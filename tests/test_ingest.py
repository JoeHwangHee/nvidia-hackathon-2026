"""ingest.py 회귀 테스트 (표준 라이브러리 unittest, 네트워크 없음).

실행: python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import sqlite3
import tempfile
import unittest
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("ingest", ROOT / "src" / "tradesentry" / "ingest.py")
ingest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ingest)

CFG = {"snapshot_id": "t_snap", "period": {"start": "202201", "end": "202203"}, "chunk_months": 12,
       "hs4_scan": ["8504"], "hs6": ["850450"], "partners": ["CN", "KH"], "collect_total_denominator": True, "hs10": []}


def xml_response(rows: list, hs_field: str = "hsCd", total: bool = True) -> bytes:
    """관세청 정상 봉투. rows: [(year, hs, 수입금액, 수입중량, 수출금액, 수출중량)]. total 이면 실측처럼 '총계' 행을 맨 앞에 붙인다."""
    items = list(rows)
    if total and rows:
        items.insert(0, ("총계", "-", *[sum(r[i] for r in rows) for i in range(2, 6)]))
    body = "".join(f"<item><year>{y}</year><{hs_field}>{hs}</{hs_field}><impDlr>{a}</impDlr><impWgt>{w}</impWgt>"
                   f"<expDlr>{ea}</expDlr><expWgt>{ew}</expWgt></item>" for y, hs, a, w, ea, ew in items)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><response><header><resultCode>00</resultCode>'
            f"<resultMsg>정상서비스.</resultMsg></header><body><items>{body}</items></body></response>").encode()


def ok_res(raw: bytes) -> dict:
    return {"ok": True, "http_status": 200, "attempts": 1, "raw": raw, "error": None, "attempt_errors": [], "elapsed_ms": 1}


def fail_res(raw: bytes = b"<html>Internal Server Error</html>") -> dict:
    return {"ok": False, "http_status": 500, "attempts": 3, "raw": raw, "error": "HTTPError 500", "attempt_errors": ["HTTPError 500"] * 3, "elapsed_ms": 1}


# 기본 시나리오: CN 은 1·2월 부모-하위 일치, 3월은 하위(HS10)만 있음. KH 는 빈 응답. ALL 은 HS4·HS6 조회가 일치.
BASE = {
    ("hs4_partner_monthly", "8504", "CN"): xml_response([("2022.01", "850450", 300, 30, 0, 0), ("2022.02", "850450", 0, 0, 50, 5),
                                                         ("2022.01", "850410", 999, 99, 0, 0)]),
    ("hs6_partner_monthly", "850450", "CN"): xml_response([("2022.01", "8504501010", 200, 20, 0, 0), ("2022.01", "8504509010", 100, 10, 0, 0),
                                                           ("2022.02", "8504501010", 0, 0, 50, 5), ("2022.03", "8504501010", 70, 7, 0, 0)]),
    ("hs4_world_total_monthly", "8504", "ALL"): xml_response([("2022.01", "8504501010", 1000, 100, 0, 0), ("2022.02", "8504501010", 900, 90, 0, 0),
                                                              ("2022.03", "8504501010", 800, 80, 0, 0), ("2022.01", "8504100000", 5, 1, 0, 0)], "hsCode"),
    ("hs6_world_total_monthly", "850450", "ALL"): xml_response([("2022.01", "8504501010", 1000, 100, 0, 0), ("2022.02", "8504501010", 900, 90, 0, 0),
                                                                ("2022.03", "8504501010", 800, 80, 0, 0)], "hsCode"),
}


class FakeResp:
    def __init__(self, body: bytes, status: int = 200):
        self.status, self._body = status, body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def http_error(code: int) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://example.invalid", code, "err", None, io.BytesIO(b"<err/>"))


class CallApiTest(unittest.TestCase):
    def run_with(self, outcomes):
        seq = iter(outcomes)

        def fake_urlopen(req, timeout=30):
            o = next(seq)
            if isinstance(o, Exception):
                raise o
            return o

        with mock.patch.object(ingest, "service_key", return_value="K"), \
                mock.patch.object(ingest.urllib.request, "urlopen", side_effect=fake_urlopen), \
                mock.patch.object(ingest.time, "sleep") as sleep:
            res = ingest.call_api("nitemtrade", {"strtYymm": "202201", "endYymm": "202201", "hsSgn": "850450", "cntyCd": "CN"})
        return res, sleep

    def test_retry_success_after_timeout_is_ok(self):
        res, _ = self.run_with([TimeoutError("timed out"), FakeResp(b"<response/>")])
        self.assertTrue(res["ok"])
        self.assertIsNone(res["error"])
        self.assertEqual(res["attempts"], 2)
        self.assertEqual(res["attempt_errors"], ["TimeoutError: timed out"])

    def test_retry_success_after_5xx_is_ok(self):
        res, _ = self.run_with([http_error(500), FakeResp(b"<response/>")])
        self.assertTrue(res["ok"])
        self.assertEqual(res["http_status"], 200)

    def test_non_retryable_http_stops_immediately(self):
        res, sleep = self.run_with([http_error(403)])
        self.assertFalse(res["ok"])
        self.assertEqual(res["attempts"], 1)
        self.assertEqual(res["error"], "HTTPError 403")
        sleep.assert_not_called()

    def test_exhausted_retries_no_sleep_after_last(self):
        res, sleep = self.run_with([http_error(500), http_error(502), http_error(503)])
        self.assertFalse(res["ok"])
        self.assertEqual(res["attempts"], 3)
        self.assertEqual(len(res["attempt_errors"]), 3)
        self.assertEqual(sleep.call_count, 2)


class SnapshotTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self._patch = mock.patch.object(ingest, "SNAP_DIR", self.root)
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        self._tmp.cleanup()

    def make_snapshot(self, responses: dict, cfg: dict = CFG) -> Path:
        reqs = ingest.build_manifest(cfg)
        d, con = ingest.open_snapshot(cfg["snapshot_id"])
        (d / "manifest.json").write_text(json.dumps({"snapshot_id": cfg["snapshot_id"], "config": cfg, "requests": reqs}, ensure_ascii=False), encoding="utf-8")
        for r in reqs:
            key = (r["purpose"], r["params"]["hsSgn"], r["params"].get("cntyCd", "ALL"))
            ingest.store_result(d, con, cfg["snapshot_id"], r["endpoint"], r["params"], ok_res(responses.get(key, xml_response([]))), r["months"])
        con.close()
        return d

    def verify(self, snapshot_id: str = "t_snap") -> dict:
        with contextlib.redirect_stdout(io.StringIO()):
            ingest.cmd_verify(SimpleNamespace(snapshot=snapshot_id, out="data-readiness.json"))
        return json.loads((self.root / snapshot_id / "data-readiness.json").read_text(encoding="utf-8"))


class StoreResultTest(SnapshotTestCase):
    PARAMS = {"strtYymm": "202201", "endYymm": "202203", "hsSgn": "850450", "cntyCd": "CN"}
    MONTHS = ["202201", "202202", "202203"]

    def rows(self, con):
        return sorted(con.execute("SELECT month, hs_code, flow, observation_status, raw_file_id FROM observation").fetchall(), key=repr)

    def test_failed_recollect_keeps_previous_ok(self):
        d, con = ingest.open_snapshot("s")
        good = xml_response([("2022.01", "8504501010", 200, 20, 0, 0)])
        ingest.store_result(d, con, "s", "nitemtrade", self.PARAMS, ok_res(good), self.MONTHS)
        rid = ingest.request_id("nitemtrade", self.PARAMS)
        before_rows = self.rows(con)
        s = ingest.store_result(d, con, "s", "nitemtrade", self.PARAMS, fail_res(), self.MONTHS)
        self.assertEqual(s["outcome"], "FAILED_KEPT_PREVIOUS_OK")
        self.assertEqual((d / "raw" / f"{rid}.xml").read_bytes(), good)  # 정상 raw 가 오류 본문으로 덮이지 않음
        self.assertEqual(con.execute("SELECT status, response_hash FROM collection_receipt").fetchone(), ("OK", hashlib.sha256(good).hexdigest()))
        self.assertEqual(self.rows(con), before_rows)  # 옛 행 유지, REQUEST_FAILED 행이 섞이지 않음
        self.assertEqual(len(list((d / "raw" / "failed").iterdir())), 1)  # 실패 본문은 따로 보관
        self.assertEqual([r[0] for r in con.execute("SELECT outcome FROM collection_attempt ORDER BY rowid")], ["OK", "FAILED_KEPT_PREVIOUS_OK"])

    def test_success_recollect_replaces_rows_and_raw(self):
        d, con = ingest.open_snapshot("s")
        ingest.store_result(d, con, "s", "nitemtrade", self.PARAMS, ok_res(xml_response([("2022.01", "8504501010", 1, 1, 0, 0), ("2022.01", "8504509010", 2, 2, 0, 0)])), self.MONTHS)
        second = xml_response([("2022.01", "8504501010", 1, 1, 0, 0)])
        ingest.store_result(d, con, "s", "nitemtrade", self.PARAMS, ok_res(second), self.MONTHS)
        codes = {r[0] for r in con.execute("SELECT hs_code FROM observation WHERE observation_status='OBSERVED' AND month NOT LIKE 'RAW:%'")}
        self.assertEqual(codes, {"8504501010"})  # 새 응답에 없는 옛 HS10 행이 남지 않음
        rid = ingest.request_id("nitemtrade", self.PARAMS)
        self.assertEqual((d / "raw" / f"{rid}.xml").read_bytes(), second)
        self.assertEqual(list((d / "raw").glob(".*.tmp")), [])  # 임시 파일 정리

    def test_success_after_failure_clears_request_failed_rows(self):
        d, con = ingest.open_snapshot("s")
        ingest.store_result(d, con, "s", "nitemtrade", self.PARAMS, fail_res(), self.MONTHS)
        s = ingest.store_result(d, con, "s", "nitemtrade", self.PARAMS, ok_res(xml_response([("2022.01", "8504501010", 5, 1, 0, 0)])), self.MONTHS)
        self.assertEqual(s["outcome"], "OK")
        statuses = {r[3] for r in self.rows(con)}
        self.assertNotIn("REQUEST_FAILED", statuses)  # 재시도 성공 뒤 옛 실패 행이 남지 않음
        self.assertEqual(statuses, {"OBSERVED", "UNRESOLVED_ZERO"})
        self.assertEqual(con.execute("SELECT status FROM collection_receipt").fetchone()[0], "OK")

    def test_first_failure_marks_request_failed(self):
        d, con = ingest.open_snapshot("s")
        s = ingest.store_result(d, con, "s", "nitemtrade", self.PARAMS, fail_res(), self.MONTHS)
        self.assertEqual(s["outcome"], "FAILED")
        rid = ingest.request_id("nitemtrade", self.PARAMS)
        self.assertFalse((d / "raw" / f"{rid}.xml").exists())
        self.assertEqual(con.execute("SELECT status FROM collection_receipt").fetchone()[0], "FAILED")
        statuses = {r[3] for r in self.rows(con)}
        self.assertEqual(statuses, {"REQUEST_FAILED"})
        self.assertEqual(con.execute("SELECT COUNT(*) FROM observation").fetchone()[0], 6)  # 3개월 × 수입/수출
        self.assertTrue(all(r[4].startswith("failed/") for r in self.rows(con)))


class VerifyTest(SnapshotTestCase):
    def test_non_integer_detected(self):
        responses = dict(BASE)
        responses[("hs6_partner_monthly", "850450", "CN")] = xml_response([("2022.01", "8504501010", "12.5", 3, 0, 0)], total=False)
        self.make_snapshot(responses)
        self.assertEqual(self.verify()["non_integer_values"], 1)

    def test_g2_counts_expected_pairs_and_month_classes(self):
        self.make_snapshot(BASE)
        r = self.verify()
        cov = {(c["hs6"], c["partner"]): c for c in r["coverage_target_pairs"]}
        self.assertEqual(set(cov), {("850450", "CN"), ("850450", "KH"), ("850450", "ALL")})  # 관측 0개월인 KH 도 빠지지 않음
        self.assertEqual((cov["850450", "CN"]["import_pos"], cov["850450", "CN"]["import_zero_explicit"]), (2, 1))
        self.assertEqual(cov["850450", "KH"]["no_response"], 3)
        g2 = r["gates"]["G2_full_period_quality"]
        self.assertEqual(g2["pairs_expected"], {"country": 2, "ALL": 1})  # 비대상 HS6(850410, 8504100000)는 섞이지 않음
        self.assertEqual(g2["pairs_full_any_rows"], {"country": 1, "ALL": 1})
        self.assertEqual(g2["pairs_full_import_pos"], {"country": 0, "ALL": 1})
        self.assertTrue(g2["denominator_cross_check_ok"])

    def test_cross_check_reports_one_sided_and_fails_g3(self):
        self.make_snapshot(BASE)
        r = self.verify()
        c = r["cross_check"]["country"]
        self.assertEqual(c["matched"], 2)
        self.assertEqual([(x["month"], x["hs4_scan_request"]) for x in c["child_only"]], [("202203", "ok_no_row")])
        self.assertFalse(r["gates"]["G3_hs10_decomposition"])  # 이전 verify(inner join)라면 불일치 0 으로 통과했을 조합
        self.assertEqual(r["cross_check"]["ALL"]["matched"], 3)

    def test_consistent_snapshot_passes_g3(self):
        responses = dict(BASE)
        responses[("hs6_partner_monthly", "850450", "CN")] = xml_response([("2022.01", "8504501010", 200, 20, 0, 0), ("2022.01", "8504509010", 100, 10, 0, 0),
                                                                            ("2022.02", "8504501010", 0, 0, 50, 5)])
        self.make_snapshot(responses)
        r = self.verify()
        self.assertTrue(r["gates"]["G3_hs10_decomposition"])
        self.assertTrue(r["gates"]["snapshot_integrity"])

    def test_all_denominator_mismatch_detected(self):
        responses = dict(BASE)
        responses[("hs6_world_total_monthly", "850450", "ALL")] = xml_response([("2022.01", "8504501010", 1000, 100, 0, 0), ("2022.02", "8504501010", 901, 90, 0, 0)], "hsCode")
        self.make_snapshot(responses)
        a = self.verify()["cross_check"]["ALL"]
        self.assertEqual(len(a["mismatches"]), 1)
        self.assertEqual(a["only_in_hs4_query"], [{"hs10": "8504501010", "month": "202203"}])

    def test_response_without_total_row_flagged(self):
        responses = dict(BASE)
        responses[("hs6_partner_monthly", "850450", "CN")] = xml_response([("2022.01", "8504501010", 300, 30, 0, 0)], total=False)
        self.make_snapshot(responses)
        r = self.verify()
        self.assertEqual(len(r["responses_without_total_row"]), 1)
        self.assertFalse(r["gates"]["G3_hs10_decomposition"])

    def test_raw_hash_mismatch_detected(self):
        d = self.make_snapshot(BASE)
        target = sorted((d / "raw").glob("*.xml"))[0]
        target.write_bytes(target.read_bytes() + b" ")
        r = self.verify()
        self.assertEqual(len(r["raw_hash_mismatches"]), 1)
        self.assertFalse(r["gates"]["snapshot_integrity"])

    def test_verify_does_not_modify_sqlite(self):
        d = self.make_snapshot(BASE)
        before = hashlib.sha256((d / "snapshot.sqlite").read_bytes()).hexdigest()
        self.verify()
        self.assertEqual(hashlib.sha256((d / "snapshot.sqlite").read_bytes()).hexdigest(), before)

    def test_plan_rebuilt_from_receipts_without_manifest(self):
        d = self.make_snapshot(BASE)
        (d / "manifest.json").unlink()
        g2 = self.verify()["gates"]["G2_full_period_quality"]
        self.assertEqual(g2["pairs_expected"], {"country": 2, "ALL": 1})
        self.assertEqual(g2["months_required"], 3)


if __name__ == "__main__":
    unittest.main()
