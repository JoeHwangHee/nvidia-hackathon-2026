"""단위 X3 구성효과 분해.

단위 ID: X3
도메인명: metrics_decompose
소유: D
입력: HS10 두 시점
출력: `within_effect`·`mix_effect`·`residual`, 부모 대조
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.3.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 X3(metrics_decompose)의 run은 아직 구현하지 않았다")
