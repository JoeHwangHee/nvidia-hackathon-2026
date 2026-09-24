"""단위 E2 샌드박스 밖 실행기.

단위 ID: E2
도메인명: evaluation_sealed_runner
소유: M
입력: 봉인 해시 대조
출력: 사례 식별자 한 건씩 `run-case`
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.runlog

이 실행기는 키 변수를 뺀 환경에서 돌고 .env를 읽지 않는다. 그래서 load_env가 있는 tradesentry.ingest를 직접이든 간접이든 import하지 않는다(경계 시험이 본다).

사례는 샌드박스 안 run-case로만 돌린다. 하위 프로세스는 openshell로 시작하는 목록 리터럴로만 부르고, 묶음 실행 E1(tradesentry.evaluation.batch_run)과 사례를 호스트에서 돌릴 수 있는 tradesentry.workflow·tools·policy·metrics를 import하지 않는다(경계 시험이 본다).

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.10.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 E2(evaluation_sealed_runner)의 run은 아직 구현하지 않았다")
