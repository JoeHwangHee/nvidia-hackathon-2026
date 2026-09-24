"""시험용 작은 스냅샷 원천(manifest·raw·수집기 SQLite)을 기존 수집기 코드로 만든다(단위 S2·S3·K3 시험이 함께 쓴다).

- 수집 계획과 응답은 아래 CONFIG·RESPONSES의 합성 값이다. 실제 통계가 아니다.
- 수집기(src/tradesentry/ingest.py)의 build_manifest·open_snapshot·store_result를 그대로 불러 만든다. 그래서 이 원천의
  수집기 SQLite는 실제 수집기가 같은 응답을 받았을 때의 행과 같다. 수집기가 쓰는 폴더(ingest.SNAP_DIR)와 시각
  (ingest.now_iso)은 시험 동안만 임시 폴더와 고정 시각으로 바꾼다. 네트워크(call_api)는 부르지 않는다.
- 관측 상태 다섯 가지가 모두 나온다.
  - CN: HS4 스캔 정상(부모 HS6 행 850450 두 달), HS6 조회 실패 → REQUEST_FAILED(부모는 있고 HS10은 실패: oracle C 모양)
  - JP: HS4 스캔에 850450은 202301만(202302에는 다른 HS6 850431만) → HS6 조회 202302 UNRESOLVED_ZERO(승격 후보)
  - DE: HS4 스캔 202302 빈 달 → HS4 자릿수 UNRESOLVED_ZERO, HS6 조회는 수신 기록 없음 → NOT_COLLECTED
  - ALL: 품목별 HS4·HS6 조회가 같은 HS10 월 행을 두 번 담는다(중복 제거 대상, 값 같음)
- 비교국 표 PEER_GROUP_CSV의 US는 수집 계획 밖이다(빌드가 NOT_COLLECTED 행을 만든다).
"""
import hashlib
import json
from pathlib import Path
from unittest import mock

from tradesentry import ingest

SNAPSHOT_ID = "unit_fixture_s2"
FIXED_TIME = "2026-09-25T00:00:00+09:00"
CONFIG = {
    "snapshot_id": SNAPSHOT_ID,
    "period": {"start": "202301", "end": "202302"},
    "chunk_months": 12,
    "hs6": ["850450"],
    "partners": ["CN", "JP", "DE"],
    "collect_total_denominator": True,
    "hs10": [],
    "hs4_scan": ["8504"],
}


def _item(year: str, code: str, imp: tuple[int, int], name: str, partner: str | None) -> dict:
    item = {"year": year, "impDlr": str(imp[0]), "impWgt": str(imp[1]), "expDlr": "0", "expWgt": "0", "statKor": name}
    item["hsCd" if partner else "hsCode"] = code
    if partner:
        item["statCd"] = partner
    return item


def _with_total(items: list[dict], partner: str | None) -> list[dict]:
    total = _item("총계", "-", (sum(int(i["impDlr"]) for i in items), sum(int(i["impWgt"]) for i in items)), "-",
                  partner)
    if partner:
        total["statCd"] = "-"
    return [total] + items


# (엔드포인트, hsSgn, 상대국) → 응답 행 목록 / "FAILED"(요청 실패) / None(수집하지 않음)
RESPONSES = {
    ("nitemtrade", "8504", "CN"): _with_total([
        _item("2023.01", "850450", (600, 100), "그 밖의 유도자", "CN"),
        _item("2023.01", "850431", (100, 10), "용량 1kVA 이하", "CN"),
        _item("2023.02", "850450", (360, 100), "그 밖의 유도자", "CN"),
        _item("2023.02", "850431", (50, 5), "용량 1kVA 이하", "CN")], "CN"),
    ("nitemtrade", "8504", "JP"): _with_total([
        _item("2023.01", "850450", (300, 30), "그 밖의 유도자", "JP"),
        _item("2023.01", "850431", (200, 20), "용량 1kVA 이하", "JP"),
        _item("2023.02", "850431", (80, 8), "용량 1kVA 이하", "JP")], "JP"),
    ("nitemtrade", "8504", "DE"): _with_total([
        _item("2023.01", "850450", (90, 9), "그 밖의 유도자", "DE")], "DE"),
    ("itemtrade", "8504", "ALL"): _with_total([
        _item("2023.01", "8504501000", (1500, 150), "시험 하위품목 가", None),
        _item("2023.01", "8504509000", (500, 100), "시험 하위품목 나", None),
        _item("2023.01", "8504311000", (700, 70), "시험 하위품목 다", None),
        _item("2023.02", "8504501000", (1200, 120), "시험 하위품목 가", None),
        _item("2023.02", "8504311000", (300, 30), "시험 하위품목 다", None)], None),
    ("nitemtrade", "850450", "CN"): "FAILED",
    ("nitemtrade", "850450", "JP"): _with_total([
        _item("2023.01", "8504501000", (250, 20), "시험 하위품목 가", "JP"),
        _item("2023.01", "8504509000", (50, 10), "시험 하위품목 나", "JP")], "JP"),
    ("nitemtrade", "850450", "DE"): None,
    ("itemtrade", "850450", "ALL"): _with_total([
        _item("2023.01", "8504501000", (1500, 150), "시험 하위품목 가", None),
        _item("2023.01", "8504509000", (500, 100), "시험 하위품목 나", None),
        _item("2023.02", "8504501000", (1200, 120), "시험 하위품목 가", None)], None),
}

PEER_GROUP_CSV = (
    "entity_type,entity_id,entity_namespace,baci_country_code,scope_type,scope_id,peer_rank,peer_id,similarity,"
    "community_id,method,grouping_version,params_hash,source_version,source_year,input_sha256,generated_at\n"
    "exporter_country,CN,KCS_cntyCd,156,hs6,850450,1,JP,,,import_value_topk,g0," + "a" * 64 + ","
    + SNAPSHOT_ID + ",2023," + "b" * 64 + "," + FIXED_TIME + "\n"
    "exporter_country,CN,KCS_cntyCd,156,hs6,850450,2,DE,,,import_value_topk,g0," + "a" * 64 + ","
    + SNAPSHOT_ID + ",2023," + "b" * 64 + "," + FIXED_TIME + "\n"
    "exporter_country,CN,KCS_cntyCd,156,hs6,850450,3,US,,,import_value_topk,g0," + "a" * 64 + ","
    + SNAPSHOT_ID + ",2023," + "b" * 64 + "," + FIXED_TIME + "\n"
    "exporter_country,JP,KCS_cntyCd,392,hs4,8504,1,CN,0.8300,c1,cosine_topk,g1," + "c" * 64 + ","
    + "BACI_HS22_V202601,2023," + "d" * 64 + "," + FIXED_TIME + "\n"
)


def xml_response(items: list[dict]) -> bytes:
    body = "".join("<item>" + "".join(f"<{k}>{v}</{k}>" for k, v in item.items()) + "</item>" for item in items)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><response><header><resultCode>00</resultCode>'
            f"<resultMsg>정상서비스.</resultMsg></header><body><items>{body}</items></body></response>").encode("utf-8")


def raw_combined_sha256_shasum_style(raw_dir: Path) -> str:
    """`shasum -a 256 raw/*.xml | shasum -a 256`과 같은 값(빌드 코드와 따로 적은 계산)."""
    out = []
    for path in sorted(raw_dir.glob("*.xml")):
        out.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  raw/{path.name}\n")
    return hashlib.sha256("".join(out).encode("utf-8")).hexdigest()


def make_source(root: Path, *, with_hash_file: bool = True) -> Path:
    """root 아래에 SNAPSHOT_ID 폴더(manifest.json, raw/, snapshot.sqlite, snapshot_hash.json)를 만들고 그 경로를 돌려준다."""
    requests = ingest.build_manifest(CONFIG)
    with mock.patch.object(ingest, "SNAP_DIR", Path(root)), mock.patch.object(ingest, "now_iso", return_value=FIXED_TIME):
        folder, con = ingest.open_snapshot(SNAPSHOT_ID, "real")
        (folder / "manifest.json").write_text(json.dumps({"snapshot_id": SNAPSHOT_ID, "generated_at": FIXED_TIME,
                                                          "config": CONFIG, "requests": requests},
                                                         ensure_ascii=False, indent=1), encoding="utf-8")
        for request in requests:
            params = request["params"]
            spec = RESPONSES[(request["endpoint"], params["hsSgn"], params.get("cntyCd", "ALL"))]
            if spec is None:
                continue
            if spec == "FAILED":
                result = {"ok": False, "http_status": 500, "attempts": 3, "raw": b"", "error": "HTTPError 500",
                          "attempt_errors": ["HTTPError 500"] * 3, "elapsed_ms": 30}
            else:
                result = {"ok": True, "http_status": 200, "attempts": 1, "raw": xml_response(spec), "error": None,
                          "attempt_errors": [], "elapsed_ms": 10}
            ingest.store_result(folder, con, SNAPSHOT_ID, request["endpoint"], params, result, request["months"])
        con.execute("INSERT OR REPLACE INTO snapshot_meta VALUES('last_collect_at',?)", (FIXED_TIME,))
        con.commit()
        con.close()
    if with_hash_file:
        (folder / "snapshot_hash.json").write_text(json.dumps({
            "snapshot_id": SNAPSHOT_ID, "raw_files": len(list((folder / "raw").glob("*.xml"))),
            "raw_combined_sha256": raw_combined_sha256_shasum_style(folder / "raw"),
            "method": "스냅샷 폴더에서 `shasum -a 256 raw/*.xml | shasum -a 256`"}, ensure_ascii=False), encoding="utf-8")
    return folder


def write_peer_group_csv(path: Path) -> Path:
    Path(path).write_text(PEER_GROUP_CSV, encoding="utf-8")
    return Path(path)


def collector_rows(folder: Path) -> dict:
    """수집기 SQLite의 관측 행(기본 키 → 나머지 열)."""
    import sqlite3

    con = sqlite3.connect((Path(folder) / "snapshot.sqlite").resolve().as_uri() + "?mode=ro", uri=True)
    try:
        rows = con.execute("SELECT request_id, month, partner_code, hs_code, flow, snapshot_id, partner_namespace, "
                           "hs_level, hs_version, amount_usd, net_weight_kg, observation_status, raw_file_id, "
                           "raw_row_locator, item_name FROM observation ORDER BY rowid").fetchall()
    finally:
        con.close()
    return {row[:5]: row[5:] for row in rows}


TEST_POLICY = {
    "_status": "시험용 정책(승격 규칙 있음). 실제 정책이 아니다",
    "schema_version": 1, "policy_version": "dev-9.9", "thresholds": {"unit_value": 30, "share": 10},
    "min_amount": None, "min_weight": None, "tolerance": {"amount_usd": 0, "weight_rounding_kg": 0},
    "confirmed_no_trade": {"rule": "ingest_verify_candidates"},
}
HASH_TABLES = ("collection_receipt", "observation", "peer_group", "snapshot_meta")


def dump_db(path: Path) -> dict:
    """SQLite 파일의 표 네 개를 [rowid, 열 값…] 목록으로 덤프한다(골든 비교용)."""
    import sqlite3

    con = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        out = {"journal_mode": con.execute("PRAGMA journal_mode").fetchone()[0], "tables": {}}
        for table in HASH_TABLES:
            columns = [row[1] for row in con.execute(f'PRAGMA table_info("{table}")')]
            rows = con.execute(f'SELECT rowid, {", ".join(columns)} FROM "{table}" ORDER BY rowid').fetchall()
            out["tables"][table] = {"columns": columns, "rows": [list(row) for row in rows]}
    finally:
        con.close()
    return out


def independent_normalized_sha256(path: Path) -> str:
    """normalized_sha256을 빌드 코드와 따로, 결정 기록에 적은 직렬화 규칙 그대로 계산한다."""
    dump = dump_db(path)
    lines = []
    for table in sorted(dump["tables"]):
        lines.append(json.dumps(["table", table, dump["tables"][table]["columns"]], ensure_ascii=False,
                                separators=(",", ":")))
        lines += [json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in dump["tables"][table]["rows"]]
    return hashlib.sha256("".join(line + "\n" for line in lines).encode("utf-8")).hexdigest()


def install_fixture_build(root: Path, *, policy: dict | None = None, peers: bool = True) -> Path:
    """root 아래에 원천을 만들고 단위 S2로 빌드해 정본 자리(root/SNAPSHOT_ID/snapshot_build.sqlite)로 옮긴다.

    policy가 없으면 시험용 정책(승격 규칙 있음)을 쓴다. 정본 빌드 파일 경로를 돌려준다.
    """
    from tradesentry.contract.policy_load import parse_policy
    from tradesentry.snapshot import build

    folder = make_source(root)
    csv_path = write_peer_group_csv(Path(root) / "peer_group.csv")
    out = Path(root) / "outputs" / "snapshot_build-260925000000"
    out.mkdir(parents=True)
    build.build_snapshot(SNAPSHOT_ID, out_dir=out, stamp="260925000000", source_dir=folder,
                         policy=parse_policy(TEST_POLICY if policy is None else policy),
                         peer_group_files=[csv_path] if peers else [])
    build.install_build(out / "snapshot_build-260925000000.sqlite", folder)
    return folder / build.BUILD_FILE
