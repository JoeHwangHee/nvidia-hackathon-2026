"""단위 K2 근거 ID.

단위 ID: K2
도메인명: contract_evidence_id
소유: D
입력: (`snapshot_id`, `table`, `rowid`) 또는 `ev:` 문자열
출력: 그 반대 표현(`ev:` 문자열 ↔ (`snapshot_id`, `table`, `rowid`))과 풀림 규칙 판정
허용 import: 표준 라이브러리, tradesentry.contract

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.2.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 K2(contract_evidence_id)의 run은 아직 구현하지 않았다")
