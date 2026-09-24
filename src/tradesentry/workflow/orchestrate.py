"""단위 I12 흐름 조정.

단위 ID: I12
도메인명: workflow_orchestrate
소유: M
입력: 사례·모드
출력: 조사자 → Critic → 수정 1회 상태 기계
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.runlog, tradesentry.policy, tradesentry.tools, tradesentry.validator, tradesentry.reports, tradesentry.workflow

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.6.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 I12(workflow_orchestrate)의 run은 아직 구현하지 않았다")
