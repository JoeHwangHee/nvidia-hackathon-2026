"""단위 L2 실행 결과 기록.

단위 ID: L2
도메인명: runlog_run_record
소유: 공동
입력: 실행
출력: 실행 결과 기록의 실행 쪽 키·`run_id`
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.runlog

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.13.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 L2(runlog_run_record)의 run은 아직 구현하지 않았다")
