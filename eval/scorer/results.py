"""단위 C3 채점 결과 기록.

단위 ID: C3
도메인명: scorer_results
소유: D
입력: 하네스의 실행 쪽 키 기록(`evaluation_batch_run-{시각}.jsonl`)·필드별 판정
출력: 실행 쪽 키에 채점 키를 더한 사례 × 모드 실행 결과 기록 `scorer_results-{시각}.jsonl`
허용 import: 표준 라이브러리, eval.scorer

PR #18 새 판(옛 C3 scorer_summary를 C3·C4로 나눔)을 따른다.

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.12.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 C3(scorer_results)의 run은 아직 구현하지 않았다")
