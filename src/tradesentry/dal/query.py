"""단위 K3 읽기 전용 조회.

단위 ID: K3
도메인명: dal_query
소유: D
입력: `snapshot_id` + 허용 scope
출력: 계약 객체(빠진 자료는 관측 상태 코드)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.2.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 K3(dal_query)의 run은 아직 구현하지 않았다")
