"""단위 V5 실자료 분할.

단위 ID: V5
도메인명: datagen_split
소유: D
입력: 64 시계열 + seed
출력: `real_dev`·`real_sealed` 배정 기록
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, eval.datagen

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.11.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 V5(datagen_split)의 run은 아직 구현하지 않았다")
