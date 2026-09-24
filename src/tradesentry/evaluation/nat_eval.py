"""단위 E4 NAT 사후 평가.

단위 ID: E4
도메인명: evaluation_nat_eval
소유: M
입력: 실행 기록
출력: 정답 없는 지표
허용 import: 표준 라이브러리, nat, yaml, tradesentry.contract, tradesentry.runlog

정본: docs/plan/UNITS.md E4 행, 로드맵 MT7(NAT 사후 평가), 자료 계약 §8.2(NAT 프로파일 요약은 실행 조건 입력 파일로 채점
요약에 들어간다. 봉인 묶음은 넣지 않는다), 로드맵 §3 MVP 체크리스트 7번.

평가 묶음 하나의 사례 실행 폴더에 남은 NAT 프로파일 결과와 실행 기록에서, 정답 없이 계산할 수 있는 지표만 묶음 요약으로
낸다. 정답 대조(채점기와 겹치는 항목)는 하지 않는다. 이 요약이 실행 조건 입력 파일의 nat_profile_summary로 간다.
- 실행 기록에서: 실행 수, 모드별 모델 요청 수·토큰(입력 + 출력)·경과 시간(wall_ms)의 중앙값과 범위.
- NAT 프로파일에서(사례 실행 폴더 안 workflow_nat_wrap-{시각}/, 단위 I13이 NAT가 정한 이름 그대로 쓴 파일 5개):
  모델 요청 구간 수(LLM_END)와 그 시간 합, NAT가 센 토큰, 도구 구간 수(TOOL_END), 흐름 전체 시간(WORKFLOW_START →
  WORKFLOW_END), 단계별 구간 수(SPAN_START의 이름: basic·critic·revision·final, 그 밖은 other). 이 값들은
  all_requests_profiler_traces.json의 intermediate_steps payload에서 event_type·name·event_timestamp·
  span_event_timestamp·usage_info.token_usage만 읽는다(data·metadata는 읽지 않는다). 나머지 네 파일은 있는지만 센다.
- 수는 int나 Decimal이다(float 없음). 시각 차는 Decimal로 계산해 밀리초 정수로 반올림(0.5는 올림)한다. 중앙값은 두 값의
  평균이면 Decimal일 수 있다.
- 출력에는 사례 식별자·실행명·경로·모델 이름을 넣지 않는다(건수와 수만).
- 봉인 묶음(outputs/sealed/ 아래)은 읽지 않는다. 봉인 묶음의 NAT 프로파일 요약은 금지 해제 조건 뒤 결과표(로드맵 R1)에
  적는다(자료 계약 §8.2·§10.3 N10).
- nat 패키지는 import하지 않는다(파일을 표준 라이브러리 json으로 읽는다). NAT 폴더 이름과 파일 이름은 단위 I13
  (tradesentry.workflow.nat_wrap의 DOMAIN·PROFILE_FILES)과 같은 값이다. 이 단위는 workflow를 import할 수 없어 값을
  옮겨 적었다(시험이 둘을 대조한다).
"""
import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from tradesentry.contract import types
from tradesentry.runlog import trace as trace_log

DOMAIN = "evaluation_nat_eval"
NAT_DIR_DOMAIN = "workflow_nat_wrap"  # 단위 I13의 도메인명(N7 폴더)
PROFILE_FILES = ("all_requests_profiler_traces.json", "inference_optimization.json", "standardized_data_all.csv",
                 "workflow_profiling_metrics.json", "workflow_profiling_report.txt")  # 단위 I13 PROFILE_FILES
TRACES_FILE = PROFILE_FILES[0]
BATCH_DOMAINS = {"evaluate": "evaluation_batch_run"}
STAGES = ("basic", "critic", "revision", "final")  # 단위 L1 단계 이름
OTHER_STAGE = "other"
MAX_FILE_BYTES = 16 << 20
RUN_KEYS = ("mode", "execution_status", "model_requests", "tokens_in", "tokens_out", "wall_ms", "profile")
FACT_KEYS = ("llm_calls", "llm_ms", "nat_tokens", "tool_calls", "workflow_ms")


class NatEvalError(ValueError):
    """입력이 규칙에 맞지 않는다."""


# ----------------------------------------------------------------------------- 사례 하나의 NAT 프로파일

def _ms(start: object, end: object) -> int | None:
    if not all(isinstance(v, (int, Decimal)) and not isinstance(v, bool) for v in (start, end)):
        return None
    return int(((Decimal(end) - Decimal(start)) * 1000).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _load(path: Path) -> object:
    if path.is_symlink() or not path.is_file():
        return None
    with open(path, "rb") as handle:
        data = handle.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        return None
    try:
        return json.loads(data.decode("utf-8"), parse_float=Decimal)
    except (ValueError, RecursionError):
        return None


def _count(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


def profile_facts(nat_dir: Path) -> dict | None:
    """NAT 프로파일 폴더 하나의 사실. 폴더가 없으면 None. 추적 파일을 읽지 못하면 수 칸은 None이다."""
    if nat_dir.is_symlink() or not nat_dir.is_dir():
        return None
    files = sum(1 for name in PROFILE_FILES if (nat_dir / name).is_file() and not (nat_dir / name).is_symlink())
    facts: dict = {"files": files, **{k: None for k in FACT_KEYS}, "stage_spans": {s: 0 for s in STAGES + (OTHER_STAGE,)}}
    doc = _load(nat_dir / TRACES_FILE)
    if not isinstance(doc, list):
        return facts
    llm_calls = llm_ms = tokens = tools = 0
    start = end = None
    for request in doc:
        steps = request.get("intermediate_steps") if isinstance(request, dict) else None
        for step in steps if isinstance(steps, list) else []:
            payload = step.get("payload") if isinstance(step, dict) else None
            if not isinstance(payload, dict):
                continue
            kind, stamp = payload.get("event_type"), payload.get("event_timestamp")
            if kind == "LLM_END":
                llm_calls += 1
                llm_ms += _ms(payload.get("span_event_timestamp"), stamp) or 0
                usage = payload.get("usage_info")
                usage = usage.get("token_usage") if isinstance(usage, dict) else None
                if isinstance(usage, dict):
                    tokens += _count(usage.get("prompt_tokens")) + _count(usage.get("completion_tokens"))
            elif kind == "TOOL_END":
                tools += 1
            elif kind == "SPAN_START":
                name = payload.get("name")
                facts["stage_spans"][name if name in STAGES else OTHER_STAGE] += 1
            elif kind == "WORKFLOW_START" and start is None:
                start = stamp
            elif kind == "WORKFLOW_END":
                end = stamp
    facts.update(llm_calls=llm_calls, llm_ms=llm_ms, nat_tokens=tokens, tool_calls=tools,
                 workflow_ms=_ms(start, end) if start is not None and end is not None else None)
    return facts


# ----------------------------------------------------------------------------- 묶음 요약

def _median(values: list[int]) -> int | Decimal:
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    total = ordered[mid - 1] + ordered[mid]
    return total // 2 if total % 2 == 0 else Decimal(total) / 2


def _stat(values: list) -> dict | None:
    values = [v for v in values if isinstance(v, int) and not isinstance(v, bool)]
    if not values:
        return None
    return {"median": _median(values), "min": min(values), "max": max(values)}


def summarize(runs: list) -> dict:
    """사례 실행마다의 사실 목록을 묶음 요약으로 모은다(모드별, 계약의 모드 순서)."""
    if not isinstance(runs, list):
        raise NatEvalError("runs는 목록이다")
    for item in runs:
        if not isinstance(item, dict) or set(item) != set(RUN_KEYS) or item["mode"] not in types.MODES:
            raise NatEvalError(f"사례 실행 사실은 {'·'.join(RUN_KEYS)} 키의 객체이고 mode는 계약의 모드다")
    by_mode = {}
    for mode in types.MODES:
        mine = [r for r in runs if r["mode"] == mode]
        if not mine:
            continue
        profiled = [r["profile"] for r in mine if isinstance(r["profile"], dict)]
        spans = {s: sum(_count(p.get("stage_spans", {}).get(s)) for p in profiled) for s in STAGES + (OTHER_STAGE,)}
        tokens = [r["tokens_in"] + r["tokens_out"] if all(isinstance(r[k], int) and not isinstance(r[k], bool)
                                                         for k in ("tokens_in", "tokens_out")) else None
                  for r in mine]
        by_mode[mode] = {
            "runs": len(mine),
            "runs_with_profile": len(profiled),
            "model_requests": _stat([r["model_requests"] for r in mine]),
            "tokens": _stat(tokens),
            "wall_ms": _stat([r["wall_ms"] for r in mine]),
            "nat_llm_calls": _stat([p.get("llm_calls") for p in profiled]),
            "nat_llm_ms": _stat([p.get("llm_ms") for p in profiled]),
            "nat_tokens": _stat([p.get("nat_tokens") for p in profiled]),
            "nat_tool_calls": _stat([p.get("tool_calls") for p in profiled]),
            "nat_workflow_ms": _stat([p.get("workflow_ms") for p in profiled]),
            "stage_spans": spans,
        }
    profiled_all = [r["profile"] for r in runs if isinstance(r["profile"], dict)]
    return {"runs": len(runs), "runs_with_profile": len(profiled_all),
            "profile_files_complete": sum(1 for p in profiled_all if p.get("files") == len(PROFILE_FILES)),
            "by_mode": by_mode}


def _batch_lines(batch_dir: Path) -> list:
    name = batch_dir.name
    if not trace_log.RUN_ID_RE.match(name) or name.rsplit("-", 1)[0] not in BATCH_DOMAINS:
        raise NatEvalError("평가 묶음 실행 폴더 이름이 아니다")
    run_name, stamp = name.rsplit("-", 1)
    path = batch_dir / f"{BATCH_DOMAINS[run_name]}-{stamp}.jsonl"
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
        raise NatEvalError("묶음 기록 파일이 없거나 크기 상한을 넘는다")
    lines = []
    for raw in path.read_text(encoding="utf-8").split("\n"):
        if raw.strip():
            lines.append(trace_log.loads(raw))
    return lines


def summarize_batch(batch_dir: Path) -> dict:
    """평가 묶음 실행 폴더 하나의 NAT 사후 평가 요약. 사례 실행 폴더는 묶음 폴더의 형제(run_id 이름)다."""
    if batch_dir.parent.name == "sealed":
        raise NatEvalError("봉인 묶음의 NAT 프로파일은 금지 해제 조건 전에 읽지 않는다(자료 계약 §10.3 N10)")
    runs = []
    for line in _batch_lines(batch_dir):
        if not isinstance(line, dict) or not isinstance(line.get("run_id"), str) \
                or not trace_log.RUN_ID_RE.match(line["run_id"]) or line.get("mode") not in types.MODES:
            raise NatEvalError("묶음 기록 줄의 모양이 틀렸다")
        case_dir = batch_dir.parent / line["run_id"]
        nat_dir = case_dir / f"{NAT_DIR_DOMAIN}-{line['run_id'].rsplit('-', 1)[1]}"
        profile = None if case_dir.is_symlink() else profile_facts(nat_dir)
        runs.append({"mode": line["mode"], "execution_status": line.get("execution_status"),
                     "model_requests": line.get("model_requests"), "tokens_in": line.get("tokens_in"),
                     "tokens_out": line.get("tokens_out"), "wall_ms": line.get("wall_ms"), "profile": profile})
    return summarize(runs)


def run(inp: object) -> object:
    """묶음 요약을 낸다.

    입력: {"runs": [{"mode", "execution_status", "model_requests", "tokens_in", "tokens_out", "wall_ms",
    "profile": profile_facts의 출력 또는 null}, ...]}. 출력: summarize의 요약.
    """
    if not isinstance(inp, dict) or set(inp) != {"runs"}:
        raise NatEvalError("입력은 runs 한 키의 객체다")
    return summarize(inp["runs"])
