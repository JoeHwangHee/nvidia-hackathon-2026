"""단위 L2 실행 결과 기록.

단위 ID: L2
도메인명: runlog_run_record
소유: 공동
입력: 실행
출력: 실행 결과 기록의 실행 쪽 키·`run_id`
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.runlog

두 가지를 한다.
1. 실행명 확보(자료 계약 §10.3 N8): reserve_run_dir가 실행 폴더를 이미 있으면 실패하는 폴더 만들기 호출 하나
   (os.mkdir, exist_ok 없음)로 만들고, 그 호출이 성공한 프로세스만 그 실행명을 쓴다. 이름의 초가 될 때까지 기다린 뒤
   만들고, 만든 뒤 다른 부모 폴더(outputs/와 outputs/sealed/)에 같은 이름이 있으면 방금 만든 빈 폴더를 지우고 다음
   초로 넘어간다. 시각은 컴퓨터 시간대와 관계없이 KST다. 개발 전용 공통 실행기(tradesentry.units)를 import하지 않고
   런타임 쪽에서 따로 구현한다(S0 결정 "두 트랙에 넘기는 것"). 부모 폴더는 부르는 쪽이 인자로 준다(S0 결정 ⑥).
2. 실행 결과 기록의 실행 쪽 키(자료 계약 §8.1에서 채점 키 세 개를 뺀 21개)를 검사해 계약 순서대로 만든다.
   채점 키(required_evidence_ok·numeric_ok·provenance_ok)는 샌드박스 밖 채점기만 채우므로 여기서는 받지 않는다.

검사 규칙(자료 계약 §3·§4·§8.1)
- 값 집합: dataset 5개, mode 4개, execution_status 5개, review_status_final·signal_status의 상태값.
- review_status_final은 실행이 COMPLETED일 때만 MAINTAIN·MONITOR·HOLD 가운데 하나이고, 아니면 null이다.
- signal_status는 COMPLETED면 신호 코드 unit_value·share를 키로 하는 객체다. COMPLETED가 아니면 null로 둔다
  (계약이 정하지 않은 빈칸의 해석 `[추론]`. 유효한 최종 판정이 없는 실행에 신호별 판정을 지어 넣지 않는다).
- 수 키(tool_attempts·model_requests·tokens_in·tokens_out·wall_ms)는 0 이상의 정수다. 한도를 넘은 실행은 실제 값을
  그대로 둔다(고치지 않는다). checklist는 모델을 쓰지 않으므로 model_requests·tokens_in·tokens_out이 0이고 Critic·수정을
  쓰지 않는다. agent는 Critic을 쓰지 않는다.
- errors는 COMPLETED면 빈 목록이다. 아니면 원인 분류 코드 항목(단위 L3) 하나 이상이고, 그중 하나의 실행 상태가
  execution_status와 같다.
"""
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from tradesentry.runlog import cause_codes
from tradesentry.runlog import trace as trace_log

# 자료 계약 §8 원문 키 순서. 채점 키 세 개는 정답 대조 채점이 더한다.
RESULT_KEYS = ("run_id", "case_id", "dataset", "mode", "policy_version", "rulebook_version", "snapshot_id",
               "grouping_version", "code_version", "review_status_final", "signal_status", "unresolved_evidence",
               "execution_status", "required_evidence_ok", "numeric_ok", "provenance_ok", "tool_attempts",
               "model_requests", "tokens_in", "tokens_out", "wall_ms", "critic_used", "revision_used", "errors")
SCORER_KEYS = ("required_evidence_ok", "numeric_ok", "provenance_ok")
RUN_KEYS = tuple(k for k in RESULT_KEYS if k not in SCORER_KEYS)

# 자료 계약 상수(§3·§4). 단위 K1이 생기면 커널에서 import한다(단위 표 §6 조립 부산물 4).
DATASETS = ("controlled_fixture_v0", "dev20", "holdout40", "real_dev", "real_sealed")
MODES = ("checklist", "agent", "full", "freeform")
REVIEW_STATUSES = ("MAINTAIN", "MONITOR", "HOLD")
SIGNAL_STATUSES = ("MAINTAIN", "MONITOR", "HOLD", "NOT_TRIGGERED")
SIGNAL_CODES = ("unit_value", "share")
COUNT_KEYS = ("tool_attempts", "model_requests", "tokens_in", "tokens_out", "wall_ms")
TEXT_KEYS = ("case_id", "policy_version", "rulebook_version", "snapshot_id", "grouping_version", "code_version")

STAMP_FORMAT = "%y%m%d%H%M%S"
RUN_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
MAX_ATTEMPTS = 10


class RunNameError(Exception):
    """실행명을 확보하지 못했다."""


def _second(moment: datetime) -> datetime:
    return moment.astimezone(trace_log.KST).replace(microsecond=0)


def reserve_run_dir(parent: Path, other_parent: Path, run_name: str, *,
                    clock: Callable[[], datetime] = trace_log.now_kst,
                    sleep: Callable[[float], None] = time.sleep,
                    max_attempts: int = MAX_ATTEMPTS) -> tuple[str, str, Path]:
    """실행명을 확보하고 (실행명, 시각, 실행 폴더)를 돌려준다(자료 계약 §10.3 N8).

    parent는 실행 폴더를 만들 부모(outputs/ 또는 outputs/sealed/), other_parent는 같은 이름이 없어야 하는 다른 부모다.
    parent 자체는 없으면 만든다. 실행 폴더는 이미 있으면 실패하는 방식으로 만든다.
    """
    if not RUN_NAME_RE.match(run_name):
        raise ValueError(f"실행 이름이 이름 규칙(N1)에 맞지 않는다: {run_name!r}")
    parent.mkdir(parents=True, exist_ok=True)
    target = _second(clock())
    for _ in range(max_attempts):
        while (remaining := (target - clock()).total_seconds()) > 0:
            sleep(remaining)
        stamp = target.strftime(STAMP_FORMAT)
        run_id = f"{run_name}-{stamp}"
        run_dir = parent / run_id
        try:
            os.mkdir(run_dir)
        except FileExistsError:
            target = max(target + timedelta(seconds=1), _second(clock()))
            continue
        if (other_parent / run_id).exists():
            os.rmdir(run_dir)
            target = max(target + timedelta(seconds=1), _second(clock()))
            continue
        return run_id, stamp, run_dir
    raise RunNameError(f"{max_attempts}번 시도해도 실행명 {run_name}-{{시각}}을 확보하지 못했다")


def _is_count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def build_record(facts: dict) -> dict:
    """실행 사실로 실행 쪽 키 21개를 계약 순서대로 만든다. 규칙에 어긋나면 ValueError를 낸다."""
    if not isinstance(facts, dict):
        raise ValueError("실행 사실은 객체다")
    extra = sorted(set(facts) - set(RUN_KEYS))
    missing = [k for k in RUN_KEYS if k not in facts]
    if extra or missing:
        raise ValueError(f"실행 쪽 키가 맞지 않는다(없음 {missing}, 더 있음 {extra}). 채점 키는 채점기가 더한다")
    problems: list[str] = []
    if not isinstance(facts["run_id"], str) or not trace_log.RUN_ID_RE.match(facts["run_id"]):
        problems.append("run_id가 실행명 형식이 아니다")
    for key in TEXT_KEYS:
        if not isinstance(facts[key], str) or not facts[key]:
            problems.append(f"{key}는 빈 문자열이 아닌 문자열이다")
    if facts["dataset"] not in DATASETS:
        problems.append("dataset이 자료 묶음 5개 밖이다")
    mode = facts["mode"]
    if mode not in MODES:
        problems.append("mode가 모드 4개 밖이다")
    status = facts["execution_status"]
    if status not in cause_codes.EXECUTION_STATUSES:
        problems.append("execution_status가 실행 상태 5개 밖이다")
    completed = status == cause_codes.COMPLETED
    final = facts["review_status_final"]
    if completed and final not in REVIEW_STATUSES:
        problems.append("COMPLETED인데 review_status_final이 사례 상태가 아니다")
    if not completed and final is not None:
        problems.append("COMPLETED가 아니면 review_status_final은 null이다")
    signals = facts["signal_status"]
    if completed:
        if not isinstance(signals, dict) or set(signals) != set(SIGNAL_CODES) \
                or any(v not in SIGNAL_STATUSES for v in signals.values()):
            problems.append("signal_status는 unit_value·share를 키로 하는 신호별 판정 객체다")
    elif signals is not None:
        problems.append("COMPLETED가 아니면 signal_status는 null로 둔다")
    if not isinstance(facts["unresolved_evidence"], bool):
        problems.append("unresolved_evidence는 참/거짓이다")
    for key in COUNT_KEYS:
        if not _is_count(facts[key]):
            problems.append(f"{key}는 0 이상의 정수다")
    for key in ("critic_used", "revision_used"):
        if not isinstance(facts[key], bool):
            problems.append(f"{key}는 참/거짓이다")
    if mode == "checklist" and (facts["model_requests"], facts["tokens_in"], facts["tokens_out"],
                                facts["critic_used"], facts["revision_used"]) != (0, 0, 0, False, False):
        problems.append("checklist는 모델 요청·토큰이 0이고 Critic·수정을 쓰지 않는다")
    if mode == "agent" and facts["critic_used"] is not False:
        problems.append("agent는 Critic을 쓰지 않는다")
    errors = facts["errors"]
    if not isinstance(errors, list):
        problems.append("errors는 목록이다")
    elif completed and errors:
        problems.append("COMPLETED 실행의 errors는 빈 목록이다")
    elif not completed:
        codes = [e.get("code") if isinstance(e, dict) else None for e in errors]
        if not errors or any(c not in cause_codes.STATUS_BY_CODE for c in codes) \
                or any(tuple(e) != cause_codes.ERROR_ENTRY_KEYS for e in errors):
            problems.append("멈춘 실행의 errors는 원인 분류 코드 항목(단위 L3) 하나 이상이다")
        elif status in cause_codes.EXECUTION_STATUSES and \
                not any(cause_codes.execution_status(c) == status for c in codes):
            problems.append("errors의 원인 분류 코드가 execution_status와 맞지 않는다")
    if problems:
        raise ValueError("; ".join(problems))
    return {key: facts[key] for key in RUN_KEYS}


def run(inp: object) -> object:
    """실행 사실(실행 쪽 키 21개)을 검사해 계약 순서의 실행 결과 기록 한 줄로 만든다."""
    return build_record(inp)  # type: ignore[arg-type]
