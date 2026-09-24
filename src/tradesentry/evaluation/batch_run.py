"""단위 E1 묶음 실행.

단위 ID: E1
도메인명: evaluation_batch_run
소유: M
입력: 사례 목록 × 모드
출력: 교차 배치 실행, 실행 결과 기록의 실행 쪽 키(`evaluation_batch_run-{시각}.jsonl`)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.runlog, tradesentry.policy, tradesentry.workflow

S0 제안: 사례 실행은 묶음 폴더 안이 아니라 형제 폴더 outputs/run_case-{시각}/에 두고, 묶음 기록의 줄마다 적는 run_id로 잇는다.

호스트 전용 샌드박스 밖 실행기 E2(tradesentry.evaluation.sealed_runner)를 import하지 않는다(경계 시험이 본다).

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.10.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 E1(evaluation_batch_run)의 run은 아직 구현하지 않았다")
