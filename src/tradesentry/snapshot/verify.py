"""단위 S3 스냅샷 검증.

단위 ID: S3
도메인명: snapshot_verify
소유: D
입력: SQLite·raw
출력: 검증 보고·`normalized_sha256`·계약 검사
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.ingest, tradesentry.snapshot

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.1.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 S3(snapshot_verify)의 run은 아직 구현하지 않았다")
