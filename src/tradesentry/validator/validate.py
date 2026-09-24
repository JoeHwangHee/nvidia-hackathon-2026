"""단위 R3 검증 규칙.

단위 ID: R3
도메인명: validator_validate
소유: M
입력: 보고서·봉투·스냅샷
출력: findings(`validator_findings`)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics, tradesentry.policy, tradesentry.validator

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.7.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 R3(validator_validate)의 run은 아직 구현하지 않았다")
