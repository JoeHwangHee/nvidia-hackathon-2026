"""단위 I10 조사자.

단위 ID: I10
도메인명: workflow_investigator
소유: M
입력: 상태
출력: 다음 비교·초안
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.workflow

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.6.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 I10(workflow_investigator)의 run은 아직 구현하지 않았다")
