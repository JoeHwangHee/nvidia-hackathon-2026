"""단위 P3 신호별 판정.

단위 ID: P3
도메인명: policy_signal_decide
소유: M
입력: 근거 상태
출력: 신호별 `HOLD`·`MONITOR`·`MAINTAIN`·`NOT_TRIGGERED`
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics, tradesentry.policy

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.4.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 P3(policy_signal_decide)의 run은 아직 구현하지 않았다")
