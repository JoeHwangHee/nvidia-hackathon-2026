"""조립 작업 AS2(run-case) 시험용 자료. 값은 모두 합성이고 실제 통계가 아니다. 네트워크와 키 없이 돈다.

1. 합성 시험자료 controlled_fixture_v0(단위 S4): setUp에서 임시 폴더를 저장소 뿌리로 삼아 fixture.materialize로 한 번
   만든다(저장소의 data/·outputs/는 건드리지 않는다). 사례 A·B·C(eval/dev/oracle_ABC.json의 부모·하위 값).
2. 두 신호 스냅샷 as2_two_way(AS1 시험 도우미 detect_fixture.install로 만든다. HS6 850450, 상대국 6개, 기간 202301~202402):
   두 신호가 모두 발동한 사례 둘로 "한 계열만 문제"인 두 방향을 본다(MT1 결정 ⑦·시나리오 10, MT1 평가 검토 3회차 권고).
   - 850450-JP-202402(단가만 문제): 부모 202302 500 USD/50 kg → 202402 1500/50(r_U +200%, 점유율 5% → 25%, d_s +20pp).
     2024 구간 HS6 조회가 실패해 비교월 HS10 하위자료만 빠진다(C형, REQUEST_FAILED) → 단가 HOLD. 점유율은 비교를 모두
     마쳐 MAINTAIN → 사례 MAINTAIN, unresolved_evidence 참.
   - 850450-CN-202402(점유율만 문제): 부모 202302 500/40 → 202402 8000/420(r_U +52.4%). HS10 두 개의 단가는 그대로
     (10·20 USD/kg)이고 비중만 바뀐다(구성효과) → 단가 MONITOR. 비교월 전체국가(ALL) 분모 6000 USD가 대상국 금액
     8000 USD보다 작다(dev20 분류 7) → 점유율 HOLD(comparability_issues) → 사례 HOLD.
   - 나머지 상대국(US·VN·DE·TW)은 네 달 모두 500/50(발동 없음). 비교국 표(g0, 합성)는 CN·JP에 다섯 나라씩이다.
"""
import copy
import tempfile
from pathlib import Path

from tradesentry.snapshot import fixture

from . import detect_fixture as df

NEUTRAL = df.NEUTRAL
TWO_WAY_ID = "as2_two_way"
TWO_WAY = {
    "config": df._config(TWO_WAY_ID, ["CN", "JP", "US", "VN", "DE", "TW"]),
    "parent": {
        "CN": {"202301": NEUTRAL, "202401": NEUTRAL, "202302": (500, 40), "202402": (8000, 420)},
        "JP": {"202301": NEUTRAL, "202401": NEUTRAL, "202302": (500, 50), "202402": (1500, 50)},
        **{p: {m: NEUTRAL for m in ("202301", "202302", "202401", "202402")} for p in ("US", "VN", "DE", "TW")},
    },
    "sibling": {},
    "children": {
        "CN": {"202302": [("8504501000", 300, 30), ("8504509000", 200, 10)],
               "202402": [("8504501000", 400, 40), ("8504509000", 7600, 380)]},
        "JP": {"202302": [("8504501000", 300, 30), ("8504509000", 200, 20)]},
    },
    "world": {
        "202301": [("8504501000", 5000, 500), ("8504509000", 1000, 250)],
        "202401": [("8504501000", 4000, 400), ("8504509000", 2000, 500)],
        "202302": [("8504501000", 7000, 700), ("8504509000", 3000, 750)],
        "202402": [("8504501000", 3000, 300), ("8504509000", 3000, 150)],
    },
    "failed": {("nitemtrade", df.HS6, "JP", "202401")},
}
UNIT_ONLY_PROBLEM = "850450-JP-202402"
SHARE_ONLY_PROBLEM = "850450-CN-202402"


def peer_rows(entity: str, peers: list[str]) -> list[dict]:
    """합성 비교국 표 행(계약 §2.3.6 필드 17개, g0)."""
    rows = []
    for rank, peer in enumerate(peers, start=1):
        row = copy.deepcopy(df.OTHER_PEER_ROWS[0])
        row.update(entity_id=entity, peer_id=peer, peer_rank=str(rank), source_version=TWO_WAY_ID)
        rows.append(row)
    return rows


TWO_WAY_PEERS = peer_rows("CN", ["JP", "US", "VN", "DE", "TW"]) + peer_rows("JP", ["CN", "US", "VN", "DE", "TW"])


def install_two_way(root: Path) -> Path:
    """as2_two_way를 root 아래에 빌드해 정본 자리에 두고, 스냅샷들의 뿌리(root/snapshots)를 돌려준다."""
    return df.install(root, TWO_WAY, peer_rows=TWO_WAY_PEERS)


def materialize_fixture() -> tuple[tempfile.TemporaryDirectory, Path]:
    """controlled_fixture_v0을 임시 저장소 뿌리에 만들고 (임시 폴더, 스냅샷들의 뿌리)를 돌려준다. 만들지 못하면 예외로
    멈춘다(건너뛰지 않는다)."""
    import contextlib
    import io
    import shutil

    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    target = root / "data" / "snapshots" / fixture.SNAPSHOT_ID
    target.mkdir(parents=True)
    shutil.copyfile(fixture.spec_path(), target / fixture.SPEC_FILE)
    with contextlib.redirect_stdout(io.StringIO()):
        fixture.materialize(root)
    return tmp, root / "data" / "snapshots"
