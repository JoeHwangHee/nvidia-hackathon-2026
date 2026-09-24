"""단위 P4 사례 집계.

단위 ID: P4
도메인명: policy_case_aggregate
소유: M
입력: 신호별 상태
출력: 최종(`MAINTAIN > HOLD > MONITOR`)·`unresolved_evidence`
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics, tradesentry.policy

사례 집계 규칙(자료 계약 docs/rules/DATA_CONTRACT_V1.md §3.1, 개발 플랜 docs/plan/DEV_PLAN.md §6.4):
- 발동한 신호의 상태 가운데 우선순위가 가장 높은 것이 사례 상태다. 우선순위는 `MAINTAIN > HOLD > MONITOR`다.
- `MAINTAIN`과 `HOLD`가 섞이면 결과는 `MAINTAIN`이고 `unresolved_evidence=true`다. 그 밖에는 `false`다.
- 발동한 신호가 모두 `MONITOR`일 때만 사례가 `MONITOR`다.

입력(JSON 객체): {"signals": 사례의 신호 발동 객체, "signal_status": 신호별 판정 객체}. 두 객체 모두 신호 코드
(`unit_value`, `share`)를 키로 한다. 발동한 신호의 상태는 `MAINTAIN`·`MONITOR`·`HOLD` 중 하나, 발동하지 않은 신호의
상태는 `NOT_TRIGGERED`여야 한다. 어긋나면 고쳐 쓰지 않고 오류로 끝낸다(모델의 틀린 상태를 조용히 고치지 않는다,
자료 계약 §3.3). 발동한 신호가 없으면 사례가 아니므로 오류다.

출력(JSON 객체): {"review_status": 사례 상태, "unresolved_evidence": 참/거짓}.
"""
from tradesentry.policy.required_evidence import (HOLD, MAINTAIN, MONITOR, NOT_TRIGGERED, REVIEW_STATUSES,
                                                  SIGNAL_CODES, TRIGGERED, check_signals)

PRIORITY = (MAINTAIN, HOLD, MONITOR)  # 앞이 우선


def check_signal_status(signal_status: object, signals: dict[str, str]) -> dict[str, str]:
    """신호별 판정 객체를 검사한다. 발동한 신호는 판정 상태, 발동하지 않은 신호는 NOT_TRIGGERED여야 한다."""
    if not isinstance(signal_status, dict) or set(signal_status) != set(SIGNAL_CODES):
        raise ValueError(f"signal_status는 신호 코드 {list(SIGNAL_CODES)}를 키로 하는 객체여야 한다")
    for code in SIGNAL_CODES:
        status = signal_status[code]
        if signals[code] == TRIGGERED and status not in REVIEW_STATUSES:
            raise ValueError(f"발동한 신호 {code}의 상태는 {list(REVIEW_STATUSES)} 중 하나여야 한다")
        if signals[code] == NOT_TRIGGERED and status != NOT_TRIGGERED:
            raise ValueError(f"발동하지 않은 신호 {code}의 상태는 {NOT_TRIGGERED}여야 한다")
    return {code: signal_status[code] for code in SIGNAL_CODES}


def run(inp: object) -> object:
    """신호별 상태를 사례 상태와 unresolved_evidence로 집계한다."""
    if not isinstance(inp, dict) or set(inp) != {"signals", "signal_status"}:
        raise ValueError("입력은 signals와 signal_status 두 키만 가진 객체여야 한다")
    signals = check_signals(inp["signals"])
    status = check_signal_status(inp["signal_status"], signals)
    triggered = [status[code] for code in SIGNAL_CODES if signals[code] == TRIGGERED]
    if not triggered:
        raise ValueError("발동한 신호가 없다. 사례는 신호가 하나 이상 발동해야 한다")
    review_status = next(level for level in PRIORITY if level in triggered)
    return {"review_status": review_status, "unresolved_evidence": MAINTAIN in triggered and HOLD in triggered}
