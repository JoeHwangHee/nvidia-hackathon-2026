"""단위 L1 trace 기록.

단위 ID: L1
도메인명: runlog_trace
소유: 공동
입력: 이벤트
출력: trace JSONL(형식은 S0 자문 Q21)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.runlog

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.13.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 L1(runlog_trace)의 run은 아직 구현하지 않았다")
