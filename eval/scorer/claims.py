"""단위 C1 주장 채점.

단위 ID: C1
도메인명: scorer_claims
소유: D
입력: 주장·정답표·원본 행
출력: 필드별 판정(룰북 B3-1). 주장 채점 기록 `scorer_claims-{시각}.jsonl`
허용 import: 표준 라이브러리, eval.scorer

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.12.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 C1(scorer_claims)의 run은 아직 구현하지 않았다")
