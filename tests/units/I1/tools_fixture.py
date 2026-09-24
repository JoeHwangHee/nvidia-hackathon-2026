"""도구 시험용 합성 스냅샷(14개월, 전년동월 비교가 되는 최소 자료)을 만든다(단위 I1~I5 시험이 함께 쓴다).

- 값은 모두 합성이다. 실제 통계가 아니다(품목·국가 코드는 이름표로만 쓴다). snapshot_id는 `unit_fixture_tools`,
  출처 종류는 `controlled`다.
- 만드는 법은 단위 S2 시험 도우미(tests/units/S2/fixture_snapshot.py)와 같다: 수집기(src/tradesentry/ingest.py)의
  build_manifest·open_snapshot·store_result로 원천(manifest·raw·수집기 SQLite)을 만들고, 단위 S2로 빌드해 정본 자리
  (root/unit_fixture_tools/snapshot_build.sqlite)로 옮긴다. 네트워크는 쓰지 않는다.
- 기간 202301~202402(수집 구간은 2023년과 2024년 1~2월 두 덩어리), HS6 850431, 상대국 MX·CN·ID·MY·PH, 분모 ALL.
  사례의 비교월은 202401(기준월 202301)이 기본이고, 202402(기준월 202302)는 빠진 자료 사례다.
  - MX: 구성효과 사례. 하위품목 단가는 그대로(2.0·10.0 USD/kg)이고 중량 비중만 바뀐다. 부모 6000/1000 → 3600/1000.
    202306·202402에도 값이 있다(이력). 202302는 빈 달이다(UNRESOLVED_ZERO).
  - CN: 부모 값은 두 달 모두 있고, 2024년 HS10 조회가 실패했다(REQUEST_FAILED, 하위자료 빠짐).
  - ID: 202401 부모 HS6 행이 없다(HS4 스캔에 다른 HS6만 있고 HS6 조회는 수집하지 않음 → NOT_COLLECTED).
  - MY: 작은 기준월 값(50 USD / 1 kg). 202306·202402는 HS4 스캔에 다른 HS6만 있어 승격 규칙으로 CONFIRMED_NO_TRADE가
    된다.
  - PH: 202401 중량 0(500 USD / 0 kg).
  - ALL: 품목별 HS4(8504)·HS6(850431) 조회가 같은 HS10 월 행을 두 번 담는다(행 규칙 6 중복 제거 대상, 값 같음).
    202301·202401 분모는 60000 USD이고, 202302·202402는 두 요청 모두 빈 달이라 중복 제거 뒤에도 분모가 없다.
  - 비교 대상 표: MX의 g0 비교국 CN·ID·MY·PH·US(US는 수집 계획 밖 → 빌드가 NOT_COLLECTED 행을 만든다), MX의 g1
    비교국 CN(hs4 범위).
"""
import json
from pathlib import Path
from unittest import mock

from tradesentry import ingest
from tradesentry.contract.policy_load import parse_policy
from tradesentry.dal import query
from tradesentry.snapshot import build

from ..S2.fixture_snapshot import raw_combined_sha256_shasum_style, xml_response

SNAPSHOT_ID = "unit_fixture_tools"
FIXED_TIME = "2026-09-25T00:00:00+09:00"
HS6 = "850431"
C1, C2, OTHER = "8504311000", "8504312000", "8504321000"
CONFIG = {
    "snapshot_id": SNAPSHOT_ID,
    "period": {"start": "202301", "end": "202402"},
    "chunk_months": 12,
    "hs6": [HS6],
    "partners": ["MX", "CN", "ID", "MY", "PH"],
    "collect_total_denominator": True,
    "hs10": [],
    "hs4_scan": ["8504"],
}
# 빌드 정책: 승격 규칙이 있는 시험용 정책(실제 정책이 아니다). 도구가 읽는 정책은 configs/policy_dev.json(dev-0.1)이다.
BUILD_POLICY = {
    "schema_version": 1, "policy_version": "dev-9.9", "thresholds": {"unit_value": 30, "share": 10},
    "min_amount": None, "min_weight": None, "tolerance": {"amount_usd": 0, "weight_rounding_kg": 0},
    "confirmed_no_trade": {"rule": "ingest_verify_candidates"},
}


def _item(month: str, code: str, amount: int, weight: int, partner: str | None) -> dict:
    item = {"year": f"{month[:4]}.{month[4:]}", "impDlr": str(amount), "impWgt": str(weight), "expDlr": "0",
            "expWgt": "0", "statKor": "합성 시험 품목"}
    item["hsCd" if partner else "hsCode"] = code
    if partner:
        item["statCd"] = partner
    return item


def _response(rows: list[tuple], partner: str | None) -> list[dict]:
    items = [_item(month, code, amount, weight, partner) for month, code, amount, weight in rows]
    total = {"year": "총계", "impDlr": str(sum(int(i["impDlr"]) for i in items)),
             "impWgt": str(sum(int(i["impWgt"]) for i in items)), "expDlr": "0", "expWgt": "0", "statKor": "-"}
    total["hsCd" if partner else "hsCode"] = "-"
    if partner:
        total["statCd"] = "-"
    return [total] + items


ALL_2023 = [("202301", C1, 30000, 6000), ("202301", C2, 30000, 3000), ("202306", C1, 20000, 4000),
            ("202306", C2, 25000, 2500)]
ALL_2024 = [("202401", C1, 30000, 6000), ("202401", C2, 30000, 3000)]

# (엔드포인트, hsSgn, 상대국, 시작 월) → 응답 행 [(월, 코드, 금액, 중량)] / "FAILED" / None(수집하지 않음)
RESPONSES = {
    ("nitemtrade", "8504", "MX", "202301"): [("202301", HS6, 6000, 1000), ("202301", "850432", 500, 50),
                                            ("202306", HS6, 5000, 900)],
    ("nitemtrade", "8504", "MX", "202401"): [("202401", HS6, 3600, 1000), ("202401", "850432", 400, 40),
                                            ("202402", HS6, 3000, 800)],
    ("nitemtrade", "8504", "CN", "202301"): [("202301", HS6, 4000, 400)],
    ("nitemtrade", "8504", "CN", "202401"): [("202401", HS6, 2000, 400)],
    ("nitemtrade", "8504", "ID", "202301"): [("202301", HS6, 900, 90)],
    ("nitemtrade", "8504", "ID", "202401"): [("202401", "850432", 700, 70)],
    ("nitemtrade", "8504", "MY", "202301"): [("202301", HS6, 50, 1), ("202306", "850432", 300, 30)],
    ("nitemtrade", "8504", "MY", "202401"): [("202401", HS6, 2000, 30), ("202402", "850432", 100, 10)],
    ("nitemtrade", "8504", "PH", "202301"): [("202301", HS6, 800, 100)],
    ("nitemtrade", "8504", "PH", "202401"): [("202401", HS6, 500, 0)],
    ("itemtrade", "8504", "ALL", "202301"): ALL_2023 + [("202301", OTHER, 9000, 900)],
    ("itemtrade", "8504", "ALL", "202401"): ALL_2024 + [("202401", OTHER, 8000, 800)],
    ("nitemtrade", HS6, "MX", "202301"): [("202301", C1, 1000, 500), ("202301", C2, 5000, 500),
                                          ("202306", C1, 2000, 400), ("202306", C2, 3000, 500)],
    ("nitemtrade", HS6, "MX", "202401"): [("202401", C1, 1600, 800), ("202401", C2, 2000, 200),
                                          ("202402", C1, 1000, 500), ("202402", C2, 2000, 300)],
    ("nitemtrade", HS6, "CN", "202301"): [("202301", C1, 1000, 200), ("202301", C2, 3000, 200)],
    ("nitemtrade", HS6, "CN", "202401"): "FAILED",
    ("nitemtrade", HS6, "ID", "202301"): [("202301", C1, 900, 90)],
    ("nitemtrade", HS6, "ID", "202401"): None,
    ("nitemtrade", HS6, "MY", "202301"): [("202301", C1, 50, 1)],
    ("nitemtrade", HS6, "MY", "202401"): [("202401", C1, 2000, 30)],
    ("nitemtrade", HS6, "PH", "202301"): [("202301", C1, 800, 100)],
    ("nitemtrade", HS6, "PH", "202401"): [("202401", C1, 500, 0)],
    ("itemtrade", HS6, "ALL", "202301"): ALL_2023,
    ("itemtrade", HS6, "ALL", "202401"): ALL_2024,
}

_PEER_COLUMNS = ("entity_type,entity_id,entity_namespace,baci_country_code,scope_type,scope_id,peer_rank,peer_id,"
                 "similarity,community_id,method,grouping_version,params_hash,source_version,source_year,input_sha256,"
                 "generated_at")


def _peer(entity: str, scope_type: str, scope_id: str, rank: int, peer: str, similarity: str, community: str,
          method: str, grouping: str, source: str) -> str:
    return ",".join(["exporter_country", entity, "KCS_cntyCd", "", scope_type, scope_id, str(rank), peer, similarity,
                     community, method, grouping, "a" * 64, source, "2023", "b" * 64, FIXED_TIME])


PEER_GROUP_CSV = "\n".join(
    [_PEER_COLUMNS]
    + [_peer("MX", "hs6", HS6, rank, peer, "", "", "import_value_topk", "g0", SNAPSHOT_ID)
       for rank, peer in enumerate(("CN", "ID", "MY", "PH", "US"), start=1)]
    + [_peer("MX", "hs4", "8504", 1, "CN", "0.9000", "c1", "cosine_topk", "g1", "BACI_HS22_V202601")]) + "\n"


def make_source(root: Path) -> Path:
    """root 아래에 SNAPSHOT_ID 원천(manifest.json, raw/, snapshot.sqlite, snapshot_hash.json)을 만든다."""
    requests = ingest.build_manifest(CONFIG)
    with mock.patch.object(ingest, "SNAP_DIR", Path(root)), mock.patch.object(ingest, "now_iso", return_value=FIXED_TIME):
        folder, con = ingest.open_snapshot(SNAPSHOT_ID, "controlled")
        (folder / "manifest.json").write_text(json.dumps({"snapshot_id": SNAPSHOT_ID, "generated_at": FIXED_TIME,
                                                          "config": CONFIG, "requests": requests},
                                                         ensure_ascii=False, indent=1), encoding="utf-8")
        for request in requests:
            params = request["params"]
            key = (request["endpoint"], params["hsSgn"], params.get("cntyCd", "ALL"), params["strtYymm"])
            spec = RESPONSES[key]
            if spec is None:
                continue
            if spec == "FAILED":
                result = {"ok": False, "http_status": 500, "attempts": 3, "raw": b"", "error": "HTTPError 500",
                          "attempt_errors": ["HTTPError 500"] * 3, "elapsed_ms": 30}
            else:
                partner = params.get("cntyCd")
                result = {"ok": True, "http_status": 200, "attempts": 1, "raw": xml_response(_response(spec, partner)),
                          "error": None, "attempt_errors": [], "elapsed_ms": 10}
            ingest.store_result(folder, con, SNAPSHOT_ID, request["endpoint"], params, result, request["months"])
        con.execute("INSERT OR REPLACE INTO snapshot_meta VALUES('last_collect_at',?)", (FIXED_TIME,))
        con.commit()
        con.close()
    (folder / "snapshot_hash.json").write_text(json.dumps({
        "snapshot_id": SNAPSHOT_ID, "raw_files": len(list((folder / "raw").glob("*.xml"))),
        "raw_combined_sha256": raw_combined_sha256_shasum_style(folder / "raw"),
        "method": "스냅샷 폴더에서 `shasum -a 256 raw/*.xml | shasum -a 256`"}, ensure_ascii=False), encoding="utf-8")
    return folder


def install(root: Path) -> Path:
    """원천을 만들고 단위 S2로 빌드해 정본 자리로 옮긴다. 정본 빌드 파일 경로를 돌려준다."""
    folder = make_source(root)
    csv_path = Path(root) / "peer_group.csv"
    csv_path.write_text(PEER_GROUP_CSV, encoding="utf-8")
    out = Path(root) / "outputs" / "snapshot_build-260925000000"
    out.mkdir(parents=True)
    build.build_snapshot(SNAPSHOT_ID, out_dir=out, stamp="260925000000", source_dir=folder,
                         policy=parse_policy(BUILD_POLICY), peer_group_files=[csv_path])
    build.install_build(out / "snapshot_build-260925000000.sqlite", folder)
    return folder / build.BUILD_FILE


def use_fixture(test) -> Path:
    """시험 setUp에서 부른다: 임시 폴더에 합성 스냅샷을 두고 자료 접근층의 스냅샷 뿌리를 그 폴더로 바꾼다."""
    import tempfile

    tmp = tempfile.TemporaryDirectory()
    test.addCleanup(tmp.cleanup)
    path = install(Path(tmp.name))
    patcher = mock.patch.object(query, "SNAPSHOTS_ROOT", Path(tmp.name))
    patcher.start()
    test.addCleanup(patcher.stop)
    return path


def request(tool_args: dict | None = None, *, partner: str = "MX", month: str = "202401", **extra) -> dict:
    """도구 요청 하나(사례 scope는 P2 모양)."""
    base = f"{int(month[:4]) - 1:04d}{month[4:]}"
    out = {"case_id": f"{HS6}-{partner}-{month}", "snapshot_id": SNAPSHOT_ID,
           "scope": {"hs6": HS6, "partner": partner, "month": month, "baseline_month": base},
           "args": {} if tool_args is None else tool_args}
    out.update(extra)
    return out
