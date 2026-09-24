"""단위 I11 Critic.

단위 ID: I11
도메인명: workflow_critic
소유: M
입력: 초안 + 근거
출력: 구조화된 지적·재조회 요청
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.workflow

Critic은 도구를 부르지 않으므로 허용 import에 tradesentry.tools를 넣지 않는다.

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.6.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 I11(workflow_critic)의 run은 아직 구현하지 않았다")
