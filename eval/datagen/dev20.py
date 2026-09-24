"""단위 V2 dev20 생성.

단위 ID: V2
도메인명: datagen_dev20
소유: D
입력: 시나리오 명세
출력: dev20 입력·정답표
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.snapshot, eval.datagen

metrics/·policy/와 그것들을 부르는 모듈을 직접이든 간접이든 import하지 않는다(경계 시험이 본다).

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.11.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 V2(datagen_dev20)의 run은 아직 구현하지 않았다")
