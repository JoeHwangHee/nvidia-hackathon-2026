"""단위 E3 추출 명령.

단위 ID: E3
도메인명: evaluation_extract
소유: M
입력: 실행 기록
출력: `execution_status`·원인 분류 코드·버전 키
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.runlog

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.10.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 E3(evaluation_extract)의 run은 아직 구현하지 않았다")
