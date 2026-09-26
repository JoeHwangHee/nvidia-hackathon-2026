"""배경 조사의 진행 단계와 실행 관리의 순수 부분(UI3, streamlit 없음).

- 진행 단계는 새 실행 폴더의 trace(`runlog_trace-{시각}.jsonl`, 이벤트마다 한 줄씩 flush된다)에서 읽는다. 반쯤 쓰인 마지막 줄과
  깨진 줄은 건너뛴다. 단계 5개와 표지 이벤트:
  ① 자료 확인 = `tool_call` `check_comparability`
  ② 이력·상대국 비교 = `tool_call` `get_history`·`compare_partners`
  ③ 하위품목 구성 = `tool_call` `decompose_hs`
  ④ 검수·수정 = `stage_start` `critic` ~ `stage_end` `critic`
  ⑤ 숫자 대조 = `tool_call` `verify_evidence`, `validator_result` `phase`=`verify`
  끝 = `run_end`. 도달한 가장 뒤 단계가 "진행 중"이고 그 앞은 "완료"다(④는 `stage_end` `critic`이 오면 완료). 표지가 아직 없으면
  예상 순서대로 첫 단계가 진행 중이다. 마지막 모델 이벤트가 `model_error`면 "응답 지연, 다시 요청 중" 표시를 켠다.
- 실행 관리: 한 세션에 조사 하나. 상태는 `running` → `done`(실행 결과 기록이 `COMPLETED`) | `failed`(그 밖의 종료, 기록 없음)
  | `timeout`(제한 시간을 넘김. 부르는 쪽이 프로세스를 끝낸다). 시각은 부르는 쪽이 준다(시험이 결정적).
- 화면에 보일 사례 이름은 평이한 말(국가·품목 이름·월)만 쓴다. 사례 ID·실행 폴더 이름·HS6 코드를 넣지 않는다.
"""
import json
from pathlib import Path

from tradesentry import app
from tradesentry.ui import i18n
from tradesentry.ui.i18n import t

STEP_KEYS = ("check", "compare", "decompose", "critic", "verify")
STEP_COUNT = len(STEP_KEYS)
RUNNING, DONE, FAILED, TIMEOUT = "running", "done", "failed", "timeout"
JOB_STATES = (RUNNING, DONE, FAILED, TIMEOUT)
TOOL_STEP = {"check_comparability": 0, "get_history": 1, "compare_partners": 1, "decompose_hs": 2, "verify_evidence": 4}
MODEL_EVENTS = ("model_request", "model_response", "model_error")


# ---- trace 읽기 -------------------------------------------------------------------------------------------------


def parse_trace_lines(text: str) -> list[dict]:
    """trace 본문 → 이벤트 목록. 줄바꿈으로 끝나지 않은 마지막 줄(쓰는 중)과 JSON이 아닌 줄은 건너뛴다."""
    lines = text.split("\n")
    complete = lines[:-1]  # 마지막 조각은 줄바꿈 뒤의 빈 문자열이거나 반쯤 쓰인 줄이다
    events = []
    for line in complete:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict) and isinstance(record.get("event"), str):
            events.append(record)
    return events


def trace_file(run_dir: Path) -> Path | None:
    exact = run_dir / f"{app.TRACE_DOMAIN}-{app.run_stamp(run_dir.name)}.jsonl"
    if exact.is_file():
        return exact
    found = sorted(p for p in run_dir.glob(f"{app.TRACE_DOMAIN}-*.jsonl") if p.is_file())
    return found[0] if found else None


def read_trace(run_dir: Path | None) -> list[dict]:
    """실행 폴더의 trace 이벤트(없거나 읽지 못하면 빈 목록)."""
    if run_dir is None:
        return []
    path = trace_file(run_dir)
    if path is None:
        return []
    try:
        return parse_trace_lines(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return []


# ---- 단계 ------------------------------------------------------------------------------------------------------


def _stage(event: dict) -> object:
    data = event.get("data") if isinstance(event.get("data"), dict) else {}
    return event.get("stage") or data.get("stage")


def step_state(events: list[dict]) -> dict:
    """이벤트 → {"states": [done|current|pending × 5], "done": 끝난 단계 수, "current": 진행 중 단계 번호(0부터) 또는 None,
    "finished": run_end 여부, "retrying": 마지막 모델 이벤트가 model_error인지}."""
    reached = 0
    critic_closed = False
    finished = False
    last_model = None
    for event in events:
        kind = event.get("event")
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        if kind == "tool_call" and data.get("tool") in TOOL_STEP:
            reached = max(reached, TOOL_STEP[data["tool"]])
        elif kind == "stage_start" and _stage(event) == "critic":
            reached = max(reached, 3)
        elif kind == "stage_end" and _stage(event) == "critic":
            reached = max(reached, 3)
            critic_closed = True
        elif kind == "validator_result" and data.get("phase") == "verify":
            reached = max(reached, 4)
        elif kind == "run_end":
            finished = True
        if kind in MODEL_EVENTS:
            last_model = kind
    if finished:
        states = ["done"] * STEP_COUNT
        return {"states": states, "done": STEP_COUNT, "current": None, "finished": True, "retrying": False}
    if reached == 3 and critic_closed:
        reached = 4
    states = ["done"] * reached + ["current"] + ["pending"] * (STEP_COUNT - reached - 1)
    return {"states": states, "done": reached, "current": reached, "finished": False, "retrying": last_model == "model_error"}


def progress_ratio(steps: dict) -> float:
    """진행 막대: 끝난 단계 비율(0~1)."""
    return min(1.0, max(0.0, steps["done"] / STEP_COUNT))


def step_label(index: int, lang: str) -> str:
    return t(f"load.step.{STEP_KEYS[index]}", lang)


# ---- 실행 관리 -------------------------------------------------------------------------------------------------


def new_job(case_id: str, snapshot_id: str, started: float, before: list[str], replay: bool) -> dict:
    """세션에 둘 조사 정보(프로세스 핸들은 부르는 쪽이 따로 붙인다)."""
    return {"case_id": case_id, "snapshot_id": snapshot_id, "started": started, "before": list(before), "replay": replay,
            "status": RUNNING, "run_id": None, "ended": None, "overlay": True}


def time_limit(wall_limit_s: int, grace_s: int = app.RUN_GRACE_S) -> int:
    """사례당 제한 시간(초): 모델 설정의 wall time 한도 + 여유(프로세스 시작·NAT 내보내기)."""
    return int(wall_limit_s) + int(grace_s)


def next_status(job: dict, *, now: float, returncode: int | None, record_status: object, limit_s: int) -> str:
    """상태 전이. 이미 끝난 조사는 그대로 둔다. 프로세스가 돌고 있으면 제한 시간을 넘겼는지만 본다. 끝났으면 실행 결과 기록의
    execution_status가 COMPLETED일 때만 done이다(종료 코드 0이어도 기록이 없으면 failed)."""
    if job.get("status") in (DONE, FAILED, TIMEOUT):
        return job["status"]
    if returncode is None:
        return TIMEOUT if now - job["started"] > limit_s else RUNNING
    return DONE if record_status == "COMPLETED" else FAILED


def elapsed_seconds(job: dict, now: float) -> int:
    end = job.get("ended") if job.get("ended") is not None else now
    return max(0, int(end - job["started"]))


def clock_text(seconds: int) -> str:
    """경과 시간 m:ss."""
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"


def pick_run_dir(before: list[str], after: list[str], stdout_dirs: list[str] | None = None) -> str | None:
    """조사의 실행 폴더: 끝난 뒤에는 CLI 표준 출력의 폴더를 먼저, 없으면 실행 전후 폴더 차이의 가장 새 것."""
    if stdout_dirs:
        return stdout_dirs[0]
    fresh = app.new_run_dirs(before, after)
    return fresh[0] if fresh else None


# ---- 사례 이름 ---------------------------------------------------------------------------------------------------


def case_parts(case_id: object, lang: str, countries: dict[str, str]) -> dict:
    """사례 ID → 평이한 이름 조각(품목 이름·국가 이름·월). 해석할 수 없으면 빈 조각."""
    parsed = app.parse_case_id(case_id) or {}
    if not parsed:
        return {"item": "", "partner": "", "month": "", "month_long": ""}
    return {"item": i18n.item_label(parsed["hs6"], lang), "partner": i18n.partner_label(parsed["partner"], countries),
            "month": i18n.month_label(parsed["month"], lang), "month_long": i18n.month_long(parsed["month"], lang)}


def case_title(case_id: object, lang: str, countries: dict[str, str]) -> str:
    """로딩 창 제목 줄: "{국가}산 {품목} · {YYYY년 M월} 경보" / "{item} from {partner} · {Month YYYY} alert"."""
    parts = case_parts(case_id, lang, countries)
    if not parts["item"]:
        return t("load.case_unknown", lang)
    return t("load.case", lang, item=parts["item"], partner=parts["partner"], month=parts["month_long"])


def case_short(case_id: object, lang: str, countries: dict[str, str]) -> str:
    """조사 중 표시에 들어갈 짧은 이름: "{국가}산 {품목}" / "{item} · {partner}"."""
    parts = case_parts(case_id, lang, countries)
    if not parts["item"]:
        return t("load.case_unknown", lang)
    return t("pill.case", lang, item=parts["item"], partner=parts["partner"])


def pill_text(job: dict, lang: str, countries: dict[str, str], steps: dict, now: float) -> str:
    """오른쪽 아래 조사 중 표시 문구(상태별)."""
    name = case_short(job["case_id"], lang, countries)
    status = job.get("status")
    if status == DONE:
        return t("pill.done", lang, case=name)
    if status in (FAILED, TIMEOUT):
        return t("pill.failed", lang, case=name)
    step = min(STEP_COUNT, (steps["current"] if steps["current"] is not None else steps["done"]) + 1)
    return t("pill.running", lang, case=name, step=step, total=STEP_COUNT, time=clock_text(elapsed_seconds(job, now)))
