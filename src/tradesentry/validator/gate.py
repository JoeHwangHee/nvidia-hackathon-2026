"""단위 R4 차단 판정.

단위 ID: R4
도메인명: validator_gate
소유: M
입력: findings + 모드
출력: 통과·차단·기록만·`INVALID`
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.validator

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.7.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 R4(validator_gate)의 run은 아직 구현하지 않았다")
