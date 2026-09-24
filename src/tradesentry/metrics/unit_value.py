"""단위 X1 단가·변화율.

단위 ID: X1
도메인명: metrics_unit_value
소유: D
입력: V·Q(t, t−12)
출력: `U`, `r_U`
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.3.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 X1(metrics_unit_value)의 run은 아직 구현하지 않았다")
