"""단위 P2 사례 만들기.

단위 ID: P2
도메인명: policy_case_build
소유: M
입력: 발동·분할 기록과 묶음 선택(`real_dev`/`real_sealed`)
출력: 사례(`case_id`·scope). 지정한 묶음의 시계열로 제한(수단은 S0 자문 Q18, 고르는 방법은 병렬 개발 규칙 §7.2의 5)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics, tradesentry.policy

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.4.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 P2(policy_case_build)의 run은 아직 구현하지 않았다")
