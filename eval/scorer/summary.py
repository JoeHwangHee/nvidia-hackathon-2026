"""단위 C4 보조 지표·요약.

단위 ID: C4
도메인명: scorer_summary
소유: D
입력: 판정·실행 결과 기록
출력: 보조 지표·Wilson 구간(비율의 신뢰구간 계산법)·요약 `scorer_summary-{시각}.md`
허용 import: 표준 라이브러리, eval.scorer

PR #18 새 판(옛 C3 scorer_summary를 C3·C4로 나눔)을 따른다.

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.12.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 C4(scorer_summary)의 run은 아직 구현하지 않았다")
