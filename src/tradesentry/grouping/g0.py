"""단위 G1 g0 고정 목록.

단위 ID: G1
도메인명: grouping_g0
소유: M
입력: v2 2023 수입액
출력: 대상국 뺀 상위 5개국
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal

S0 제안: 저장 위치는 data/reference/peer_group_g0.csv(peer_group_g1.csv와 같은 행 형식)다. 계획 경로·명령 표에 없는 위치라 사용자 승인 대상이다.

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.5.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 G1(grouping_g0)의 run은 아직 구현하지 않았다")
