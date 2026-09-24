"""단위 I7 NIM 호출.

단위 ID: I7
도메인명: workflow_model_client
소유: M
입력: 메시지
출력: 응답(5xx 재전송 3회, 제한 시간, 토큰)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.runlog

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.6.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 I7(workflow_model_client)의 run은 아직 구현하지 않았다")
