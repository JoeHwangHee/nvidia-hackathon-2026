"""단위 A2 화면.

단위 ID: A2
도메인명: app
소유: M
입력: 실행 기록·조회
출력: Streamlit 화면 3개
허용 import: 표준 라이브러리, streamlit, tradesentry.contract, tradesentry.dal, tradesentry.runlog, tradesentry.reports, tradesentry.approval

위치는 S0 제안이다(자문 명세서 Q14): ingest.py처럼 하위 패키지 밖 모듈로 src/tradesentry/app.py에 둔다.

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.9.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 A2(app)의 run은 아직 구현하지 않았다")
