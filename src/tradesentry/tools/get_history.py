"""단위 I2 이력 조회.

단위 ID: I2
도메인명: tools_get_history
소유: M
입력: scope
출력: 봉투(이력·전년동월 비교)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics, tradesentry.grouping, tradesentry.policy, tradesentry.tools

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.6.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 I2(tools_get_history)의 run은 아직 구현하지 않았다")
