"""단위 S2 스냅샷 빌더.

단위 ID: S2
도메인명: snapshot_build
소유: D
입력: raw·manifest·`peer_group_g1.csv`·승격 규칙
출력: 파생 SQLite(결정적 rowid)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.ingest, tradesentry.snapshot

S0 제안: 최종 빌드(DT7 ②)는 outputs/snapshot_build-{시각}/에서 만들어 data/snapshots/{snapshot_id}/snapshot_build.sqlite로 옮긴다. 수집기의 snapshot.sqlite와 snapshot_hash.json은 고치지 않는다.

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.1.
"""


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 S2(snapshot_build)의 run은 아직 구현하지 않았다")
