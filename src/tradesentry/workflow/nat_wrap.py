"""단위 I13 NAT 감싸기.

단위 ID: I13
도메인명: workflow_nat_wrap
소유: M
입력: 흐름
출력: NAT 추적·프로파일 파일
허용 import: 표준 라이브러리, nat, tradesentry.contract, tradesentry.runlog, tradesentry.workflow

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.6.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 I13(workflow_nat_wrap)의 run은 아직 구현하지 않았다")
