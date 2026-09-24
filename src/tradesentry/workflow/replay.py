"""단위 I8 기록 재생.

단위 ID: I8
도메인명: workflow_replay
소유: M
입력: 기록된 trace
출력: 같은 응답(키 없는 스모크 시험)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.runlog, tradesentry.workflow

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.6.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 I8(workflow_replay)의 run은 아직 구현하지 않았다")
