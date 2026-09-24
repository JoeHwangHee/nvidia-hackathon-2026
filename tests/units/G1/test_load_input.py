"""단위 G1(grouping_g0) 실자료 입력 준비 load_input 시험.

임시 폴더에 만든 합성 스냅샷(수집기와 같은 SQLite 스키마, manifest.json, snapshot_hash.json)만 쓴다. 실제 스냅샷
폴더는 열지 않는다. 확인하는 것: 부모 HS6 행(자료 계약 §2.3.2 행 규칙 4)만 더하는지, 읽기 전용(mode=ro)으로 열고
스냅샷 파일을 바꾸지 않는지, 빈 금액·중복·기록 불일치를 오류로 내는지.
"""
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tradesentry.grouping import g0

# 수집기(src/tradesentry/ingest.py의 open_snapshot)가 만드는 스키마와 같다.
SCHEMA = """
CREATE TABLE collection_receipt(
  request_id TEXT PRIMARY KEY, endpoint TEXT, params_json TEXT, status TEXT, http_status INTEGER,
  attempts INTEGER, response_hash TEXT, row_count INTEGER, result_code TEXT, result_msg TEXT,
  error TEXT, elapsed_ms INTEGER, raw_file_id TEXT, timestamp TEXT);
CREATE TABLE observation(
  snapshot_id TEXT, request_id TEXT, month TEXT, partner_code TEXT, partner_namespace TEXT,
  hs_code TEXT, hs_level INTEGER, hs_version TEXT, flow TEXT, amount_usd INTEGER, net_weight_kg INTEGER,
  observation_status TEXT, raw_file_id TEXT, raw_row_locator TEXT, item_name TEXT,
  PRIMARY KEY(request_id, month, partner_code, hs_code, flow));
CREATE TABLE snapshot_meta(key TEXT PRIMARY KEY, value TEXT);
"""

SNAPSHOT_ID = "synthetic_g0_fixture"
RAW_SHA = "ab" * 32
GENERATED_AT = "2026-09-25T02:00:00+09:00"
CANDIDATES = ["CN", "JP", "DE", "VN", "US", "PH"]
HS6_CODES = ["850450", "850431"]


def scan(year: str, hs: str, partner: str | None = None) -> dict:
    params = {"strtYymm": f"{year}01", "endYymm": f"{year}12", "hsSgn": hs}
    if partner is not None:
        params["cntyCd"] = partner
    return params


# (request_id, endpoint, params_json)
RECEIPTS = [
    ("a000000000000001", "nitemtrade", scan("2023", "8504", "CN")),  # HS4 국가별 스캔: 부모 HS6 행을 낸다
    ("a000000000000002", "nitemtrade", scan("2022", "8504", "CN")),
    ("a000000000000003", "nitemtrade", scan("2023", "8504", "JP")),
    ("a000000000000004", "nitemtrade", scan("2023", "850450", "CN")),  # HS6 요청: HS10 하위 행과 총계·상태 행
    ("a000000000000005", "itemtrade", scan("2023", "850450")),  # 전체국가(ALL)
    ("a000000000000006", "nitemtrade", scan("2023", "8504", "MX")),  # 후보국이 아닌 나라
]

# (request_id, month, partner_code, hs_code, flow, amount_usd, observation_status). hs_level은 hs_code 길이다.
ROWS = [
    ("a000000000000001", "202301", "CN", "850450", "import", 100, "OBSERVED"),  # 씀
    ("a000000000000001", "202302", "CN", "850450", "import", 200, "OBSERVED"),  # 씀
    ("a000000000000001", "202302", "CN", "850450", "export", 7777, "OBSERVED"),  # 수출 흐름
    ("a000000000000001", "RAW:총계", "CN", "8504", "import", 99999, "OBSERVED"),  # HS4 총계 행
    ("a000000000000001", "202303", "CN", "850440", "import", 5555, "OBSERVED"),  # 대상 밖 HS6
    ("a000000000000002", "202212", "CN", "850450", "import", 4444, "OBSERVED"),  # 기준연도 밖
    ("a000000000000004", "202301", "CN", "8504501000", "import", 60, "OBSERVED"),  # HS10 하위 행
    ("a000000000000004", "RAW:총계", "CN", "850450", "import", 300, "OBSERVED"),  # HS6 요청의 총계 행
    ("a000000000000004", "202303", "CN", "850450", "import", None, "UNRESOLVED_ZERO"),  # 상태 행
    ("a000000000000004", "202304", "CN", "850450", "import", 12345, "OBSERVED"),  # HS6 요청의 HS6 행: 부모 아님
    ("a000000000000003", "202301", "JP", "850450", "import", 0, "OBSERVED"),  # 씀(수입 0 명시)
    ("a000000000000003", "202305", "JP", "850431", "import", 30, "OBSERVED"),  # 씀
    ("a000000000000005", "202301", "ALL", "8504501000", "import", 1000, "OBSERVED"),  # 전체국가
    ("a000000000000006", "202301", "MX", "850450", "import", 8888, "OBSERVED"),  # 후보국 밖
]

EXPECTED = {
    "k": 5,
    "source_year": 2023,
    "source_version": SNAPSHOT_ID,
    "input_sha256": RAW_SHA,
    "generated_at": GENERATED_AT,
    "candidates": CANDIDATES,
    "hs6_codes": HS6_CODES,
    "import_value_sums": [
        {"hs6": "850431", "partner": "JP", "amount_usd": 30},
        {"hs6": "850450", "partner": "CN", "amount_usd": 300},
        {"hs6": "850450", "partner": "JP", "amount_usd": 0},
    ],
}


def make_snapshot(folder: Path, *, receipts=(), rows=(), hash_snapshot_id: str = SNAPSHOT_ID) -> None:
    connection = sqlite3.connect(folder / "snapshot.sqlite")
    connection.executescript(SCHEMA)
    connection.execute("INSERT INTO snapshot_meta(key, value) VALUES ('snapshot_id', ?)", (SNAPSHOT_ID,))
    for request_id, endpoint, params in RECEIPTS + list(receipts):
        connection.execute("INSERT INTO collection_receipt(request_id, endpoint, params_json, status)"
                           " VALUES (?, ?, ?, 'OK')", (request_id, endpoint, json.dumps(params)))
    for request_id, month, partner, hs_code, flow, amount, status in ROWS + list(rows):
        connection.execute(
            "INSERT INTO observation(snapshot_id, request_id, month, partner_code, partner_namespace, hs_code,"
            " hs_level, hs_version, flow, amount_usd, net_weight_kg, observation_status)"
            " VALUES (?, ?, ?, ?, 'KCS_cntyCd', ?, ?, 'HSK', ?, ?, NULL, ?)",
            (SNAPSHOT_ID, request_id, month, partner, hs_code, len(hs_code), flow, amount, status))
    connection.commit()
    connection.close()
    config = {"snapshot_id": SNAPSHOT_ID, "hs6": HS6_CODES, "partners": CANDIDATES}
    (folder / "manifest.json").write_text(json.dumps({"snapshot_id": SNAPSHOT_ID, "config": config}),
                                          encoding="utf-8")
    (folder / "snapshot_hash.json").write_text(
        json.dumps({"snapshot_id": hash_snapshot_id, "raw_combined_sha256": RAW_SHA}), encoding="utf-8")


def folder_state(folder: Path) -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.iterdir())}


class LoadInputTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def snapshot(self, name: str = "snap", **kwargs) -> Path:
        folder = self.root / name
        folder.mkdir()
        make_snapshot(folder, **kwargs)
        return folder

    def load(self, folder: Path) -> dict:
        return g0.load_input(folder, k=5, source_year=2023, generated_at=GENERATED_AT)

    def test_sums_only_parent_hs6_rows(self):
        self.assertEqual(self.load(self.snapshot()), EXPECTED)

    def test_opens_read_only_and_changes_nothing(self):
        folder = self.snapshot()
        before = folder_state(folder)
        with mock.patch.object(g0.sqlite3, "connect", wraps=sqlite3.connect) as connect:
            self.load(folder)
        self.assertEqual(connect.call_count, 1)
        (database,), options = connect.call_args
        self.assertTrue(database.startswith("file:") and database.endswith("/snapshot.sqlite?mode=ro"), database)
        self.assertIs(options.get("uri"), True)
        self.assertEqual(folder_state(folder), before)  # 파일 내용이 같고 새 파일(-journal 등)도 없다

    def test_missing_database_is_not_created(self):
        folder = self.snapshot()
        (folder / "snapshot.sqlite").unlink()
        with self.assertRaises(sqlite3.OperationalError):
            self.load(folder)
        self.assertFalse((folder / "snapshot.sqlite").exists())

    def test_empty_amount_on_parent_row_is_an_error(self):
        folder = self.snapshot(rows=[("a000000000000001", "202304", "CN", "850450", "import", None, "OBSERVED")])
        with self.assertRaises(ValueError):
            self.load(folder)

    def test_two_parent_rows_for_one_month_is_an_error(self):
        overlap = {"strtYymm": "202206", "endYymm": "202305", "hsSgn": "8504", "cntyCd": "CN"}
        folder = self.snapshot(receipts=[("a000000000000007", "nitemtrade", overlap)],
                               rows=[("a000000000000007", "202301", "CN", "850450", "import", 100, "OBSERVED")])
        with self.assertRaises(ValueError):
            self.load(folder)

    def test_row_without_receipt_is_an_error(self):
        folder = self.snapshot(rows=[("a0000000000000ff", "202306", "CN", "850450", "import", 1, "OBSERVED")])
        with self.assertRaises(ValueError):
            self.load(folder)

    def test_snapshot_id_mismatch_is_an_error(self):
        folder = self.snapshot(hash_snapshot_id="another_snapshot")
        with self.assertRaises(ValueError):
            self.load(folder)

    def test_prepared_input_runs(self):
        rows = g0.run(self.load(self.snapshot()))
        self.assertEqual(len(rows), len(HS6_CODES) * len(CANDIDATES) * 5)
        self.assertEqual({row["input_sha256"] for row in rows}, {RAW_SHA})
        self.assertEqual({row["source_version"] for row in rows}, {SNAPSHOT_ID})
        def peers(hs6, target):
            return [row["peer_id"] for row in rows if row["scope_id"] == hs6 and row["entity_id"] == target]

        self.assertEqual(peers("850450", "CN"), ["DE", "JP", "PH", "US", "VN"])  # JP의 명시 0도 기록 없음과 동점
        self.assertEqual(peers("850450", "JP"), ["CN", "DE", "PH", "US", "VN"])  # CN 합 300이 먼저
        self.assertEqual(peers("850431", "CN"), ["JP", "DE", "PH", "US", "VN"])  # JP 합 30이 먼저


if __name__ == "__main__":
    unittest.main()
