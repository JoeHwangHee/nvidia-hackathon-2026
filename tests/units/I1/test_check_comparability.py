"""단위 I1(tools_check_comparability) 보조 시험: 비교 가능성 봉투와 도구 공통 틀.

자료는 tools_fixture.py의 합성 스냅샷(14개월)이다. 값은 합성이며 실제 통계가 아니다.
- 사례별 상태: 하위자료 실패(CN), 부모 미수집(ID), 작은 기준월 값의 반올림 불안정(MY), 중량 0(PH), 무거래 확정(MY 202402)
- ALL 분모: 중복 제거 뒤에도 빈 달만 빠진 자료로 싣는다(MT1 판정 정책과의 약속)
- 인자 허용 목록(경로·SQL·URL·셸 문자열이 도구에 닿지 않음), 요청 검사, 개발 빌드(열린 스냅샷) 경로
- 반올림 민감도 경계, query_id
- C형(부모 HS6 행은 있고 HS10 하위자료만 빠진 달)의 빠진 HS10 코드 목록과 출처(사례의 다른 달, 스냅샷의 다른 달,
  참고 품목표, 없음), attempt 필수, 파일·SQLite 오류가 경로 없는 ToolError가 되는지
"""
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from decimal import Decimal
from fractions import Fraction

from tradesentry.contract import envelope as k5
from tradesentry.contract import policy_load
from tradesentry.dal import query
from tradesentry.tools import check_comparability as cc

from . import metrics_spy, tools_fixture as fx


class Base(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.build_file = fx.use_fixture(self)
        metrics_spy.fix_clock(self)

    def run_tool(self, partner="MX", month="202401", args=None, **extra):
        extra.setdefault("policy_version", "dev-0.1")
        out = cc.run(fx.request(args, partner=partner, month=month, **extra))
        self.assertEqual(k5.envelope_problems(out), [])
        return out


class StateTest(Base):
    def test_hs10_request_failed_is_missing_but_comparable(self):
        out = self.run_tool("CN")
        comp = out["comparability"]
        self.assertTrue(comp["comparable"])
        self.assertEqual([(m["hs_code"], m["month"], m["observation_status"]) for m in out["missingness"]],
                         [("850431", "202401", "REQUEST_FAILED")])
        self.assertEqual(comp["children"]["months"][1], {"month": "202401", "observation_status": "REQUEST_FAILED",
                                                         "hs10_rows": 0, "codes": []})
        self.assertEqual(comp["children"]["months"][0]["codes"], [fx.C1, fx.C2])
        self.assertIsNone(comp["children"]["same_hs10_set"])
        self.assertIn(out["missingness"][0]["evidence_id"], out["evidence_ids"])

    def test_missing_parent_month_is_not_comparable(self):
        out = self.run_tool("ID")
        comp = out["comparability"]
        self.assertFalse(comp["comparable"])
        self.assertEqual(comp["signals"], {"unit_value": {"evaluable": False, "issues": []},
                                           "share": {"evaluable": False, "issues": []}})
        self.assertIsNone(comp["rounding"])
        # 부모 달의 상태 행과 하위자료의 상태 행이 같은 행(HS6 조회의 NOT_COLLECTED)이라 한 번만 싣는다
        self.assertEqual([(m["partner_code"], m["hs_code"], m["month"], m["observation_status"])
                          for m in out["missingness"]], [("ID", "850431", "202401", "NOT_COLLECTED")])

    def test_small_baseline_is_rounding_unstable(self):
        rounding = self.run_tool("MY")["comparability"]["rounding"]
        self.assertEqual(rounding, {"weight_rounding_kg": Decimal("0.5"), "threshold": 30,
                                    "r_U_low": Decimal("-34.4"), "r_U_high": Decimal("103.4"),
                                    "direction_stable": False, "threshold_stable": False, "unstable": True})

    def test_zero_weight_blocks_unit_value_only(self):
        comp = self.run_tool("PH")["comparability"]
        self.assertEqual(comp["signals"]["unit_value"], {"evaluable": False, "issues": ["zero_weight:202401"]})
        self.assertTrue(comp["signals"]["share"]["evaluable"])
        self.assertTrue(comp["comparable"])
        self.assertEqual(comp["parent"][1], {"month": "202401", "observation_status": "OBSERVED", "weight_zero": True})

    def test_confirmed_no_trade_month_is_an_issue_not_missingness(self):
        out = self.run_tool("MY", month="202402")
        comp = out["comparability"]
        self.assertIn("no_trade:202402", comp["signals"]["unit_value"]["issues"])
        self.assertNotIn("CONFIRMED_NO_TRADE", [m["observation_status"] for m in out["missingness"]])
        self.assertEqual(comp["parent"][1]["observation_status"], "CONFIRMED_NO_TRADE")


class DenominatorTest(Base):
    def test_all_duplicates_are_not_missing(self):
        out = self.run_tool("MX")
        self.assertEqual(out["missingness"], [])
        self.assertEqual(out["comparability"]["denominator"]["months"],
                         [{"month": "202301", "observation_status": "OBSERVED", "hs10_rows": 2},
                          {"month": "202401", "observation_status": "OBSERVED", "hs10_rows": 2}])

    def test_all_months_empty_after_dedup_are_missing(self):
        out = self.run_tool("MX", month="202402")
        world = [(m["hs_code"], m["month"], m["observation_status"]) for m in out["missingness"]
                 if m["partner_code"] == "ALL"]
        self.assertEqual(sorted(world), [("8504", "202302", "UNRESOLVED_ZERO"), ("8504", "202402", "UNRESOLVED_ZERO"),
                                         ("850431", "202302", "UNRESOLVED_ZERO"), ("850431", "202402", "UNRESOLVED_ZERO")])
        self.assertFalse(out["comparability"]["signals"]["share"]["evaluable"])

    def test_world_rows_are_the_deduplicated_hs10_rows(self):
        with query.open_snapshot(fx.SNAPSHOT_ID) as snap:
            rows, _ = cc.world_rows(snap, fx.HS6, ["202301", "202302"])
        values = [(r["month"], r["hs_code"], r["amount_usd"], r["observation_status"]) for r in rows.rows]
        self.assertEqual(values[:2], [("202301", fx.C1, 30000, "OBSERVED"), ("202301", fx.C2, 30000, "OBSERVED")])
        self.assertEqual({v[3] for v in values[2:]}, {"UNRESOLVED_ZERO"})
        self.assertEqual(sum(v[2] for v in values[:2]), 60000)  # 두 요청이 같은 행을 담아도 한 번만 더한다


class ArgsTest(Base):
    def test_model_args_outside_the_allow_list_are_refused(self):
        for args in ({"path": "/etc/passwd"}, {"sql": "SELECT * FROM observation"}, {"url": "https://example.com/x"},
                     {"cmd": "rm -rf /"}, {"partners": ["CN"]}, "SELECT 1", ["x"]):
            with self.subTest(args=args):
                out = self.run_tool("MX", args=args)
                self.assertEqual(out["retryable_error"]["code"], cc.INVALID_ARGS)
                self.assertEqual((out["evidence_ids"], out["metrics"], out["comparability"]), ([], [], None))
                self.assertEqual(out["scope"]["months"], [])

    def test_request_shape_errors_are_tool_errors(self):
        good = fx.request(policy_version="dev-0.1")
        bad = [dict(good, path="outputs/x.sqlite"), {k: v for k, v in good.items() if k != "case_id"},
               dict(good, scope=dict(good["scope"], extra="x")), dict(good, scope=dict(good["scope"], partner="ALL")),
               dict(good, scope=dict(good["scope"], baseline_month="202312")),
               {k: v for k, v in good.items() if k != "policy_version"}, dict(good, policy_version="policy_v9"),
               dict(good, envelopes=[]), dict(good, attempt=0), dict(good, snapshot_id="../x"),
               dict(good, snapshot_id="no_such_snapshot"),
               dict(good, scope={"hs6": fx.HS6, "partner": "MX", "month": "202501", "baseline_month": "202401"}),
               dict(good, scope={"hs6": "850450", "partner": "MX", "month": "202401", "baseline_month": "202301"})]
        for inp in bad:
            with self.subTest(inp=inp), self.assertRaises(cc.ToolError):
                cc.run(inp)

    def test_open_snapshot_entry_for_development_builds(self):
        with query.open_snapshot(fx.SNAPSHOT_ID, path=self.build_file) as snap:
            out = cc.query(snap, fx.request(policy_version="dev-0.1", attempt=1))
        self.assertEqual(out, cc.run(fx.request(policy_version="dev-0.1", attempt=1)))
        with query.open_snapshot(fx.SNAPSHOT_ID, path=self.build_file) as snap, self.assertRaises(cc.ToolError):
            cc.query(snap, dict(fx.request(policy_version="dev-0.1"), snapshot_id="other_snapshot"))

    def test_query_id_is_deterministic_and_changes_with_attempt(self):
        first = self.run_tool("MX", attempt=1)["query_id"]
        self.assertEqual(first, self.run_tool("MX", attempt=1)["query_id"])
        self.assertNotEqual(first, self.run_tool("MX", attempt=2)["query_id"])
        self.assertTrue(first.startswith("check_comparability-"))


REFERENCE_850431 = ["8504311000", "8504312000", "8504319010", "8504319020", "8504319040"]


class CTypeTest(Base):
    def c_type_entries(self, out):
        return [(m["month"], m["observation_status"], m.get("hs10_codes"), m.get("hs10_codes_source"))
                for m in out["missingness"] if "hs10_codes" in m]

    def test_one_month_failure_takes_codes_from_the_other_case_month(self):
        out = self.run_tool("CN")
        self.assertEqual(self.c_type_entries(out),
                         [("202401", "REQUEST_FAILED", [fx.C1, fx.C2], cc.CODES_FROM_OTHER_CASE_MONTH)])
        self.assertEqual(out["missingness"][0]["hs_code"], fx.HS6)  # 상태 행 자체는 HS6 요청 코드 그대로

    def test_both_case_months_missing_take_codes_from_other_snapshot_months(self):
        out = self.run_tool("IN")
        self.assertEqual(self.c_type_entries(out),
                         [("202301", "UNRESOLVED_ZERO", [fx.C1, fx.C2], cc.CODES_FROM_OTHER_MONTHS),
                          ("202401", "REQUEST_FAILED", [fx.C1, fx.C2], cc.CODES_FROM_OTHER_MONTHS)])

    def test_no_hs10_rows_anywhere_takes_codes_from_the_reference_table(self):
        out = self.run_tool("KH")
        self.assertEqual({(m[1], tuple(m[2]), m[3]) for m in self.c_type_entries(out)},
                         {("REQUEST_FAILED", tuple(REFERENCE_850431), cc.CODES_FROM_REFERENCE)})
        self.assertEqual(len(self.c_type_entries(out)), 2)

    def test_no_reference_table_gives_an_explicit_empty_list(self):
        cc._reference_hs10.cache_clear()
        self.addCleanup(cc._reference_hs10.cache_clear)
        with mock.patch.object(cc, "REFERENCE_HS10", Path(tempfile.gettempdir()) / "no-such-reference.json"):
            out = self.run_tool("KH")
        self.assertEqual({(tuple(m[2]), m[3]) for m in self.c_type_entries(out)}, {((), cc.CODES_FROM_NONE)})

    def test_months_without_a_parent_row_are_not_c_type(self):
        self.assertEqual(self.c_type_entries(self.run_tool("ID")), [])  # 202401 부모 행도 없다
        self.assertEqual(self.c_type_entries(self.run_tool("MX", month="202402")), [])  # 202302 부모 행도 없다


class ErrorTest(Base):
    def test_attempt_is_required(self):
        inp = fx.request(policy_version="dev-0.1")
        del inp["attempt"]
        for bad in (inp, dict(inp, attempt=None), dict(inp, attempt=True), dict(inp, attempt="1")):
            with self.subTest(attempt=bad.get("attempt")), self.assertRaises(cc.ToolError):
                cc.run(bad)

    def test_policy_file_os_error_is_named_without_a_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / policy_load.POLICY_DEV_FILE).mkdir()  # 정책 자리가 폴더다(IsADirectoryError)
            with mock.patch.object(policy_load, "CONFIGS_DIR", Path(tmp)), \
                    self.assertRaises(cc.ToolError) as caught:
                cc.run(fx.request(policy_version="dev-0.1"))
        message = str(caught.exception)
        self.assertIn("IsADirectoryError", message)
        self.assertNotIn(tmp, message)
        self.assertNotIn("/", message)

    def test_broken_snapshot_file_is_named_without_a_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "broken_snapshot"
            folder.mkdir()
            (folder / "snapshot_build.sqlite").write_bytes(b"not a database" * 100)
            with mock.patch.object(query, "SNAPSHOTS_ROOT", Path(tmp)), self.assertRaises(cc.ToolError) as caught:
                cc.run(dict(fx.request(policy_version="dev-0.1"), snapshot_id="broken_snapshot"))
        self.assertIn("DatabaseError", str(caught.exception))
        self.assertNotIn(tmp, str(caught.exception))


class RoundingTest(unittest.TestCase):
    def test_bounds_follow_weight_rounding(self):
        out = cc.rounding_sensitivity(6000, 1000, 3600, 1000, Decimal("0.5"), 30)
        self.assertEqual((out["r_U_low"], out["r_U_high"], out["unstable"]), (Decimal("-40.1"), Decimal("-39.9"), False))

    def test_threshold_crossing_inside_rounding_is_unstable(self):
        # 정확값 +30.0%(발동)이지만 반올림 폭 안에 30 미만이 있다
        out = cc.rounding_sensitivity(1000, 100, 1300, 100, Decimal("0.5"), 30)
        self.assertTrue(out["direction_stable"])
        self.assertFalse(out["threshold_stable"])
        self.assertTrue(out["unstable"])

    def test_not_triggered_everywhere_is_stable(self):
        out = cc.rounding_sensitivity(1000, 1000, 1100, 1000, Decimal("0.5"), 30)
        self.assertEqual((out["threshold_stable"], out["direction_stable"], out["unstable"]), (True, True, False))

    def test_weight_within_rounding_is_unbounded(self):
        out = cc.rounding_sensitivity(100, 1, 300, 1, Decimal("1"), 30)
        self.assertEqual((out["r_U_low"], out["r_U_high"], out["unstable"]), (None, None, True))

    def test_round_half_up_is_exact(self):
        self.assertEqual(cc.round_half_up(Fraction(-4005, 100), 1), Decimal("-40.1"))
        self.assertEqual(cc.round_half_up(Fraction(1, 3), 2), Decimal("0.33"))
        self.assertEqual(cc.round_half_up(Fraction(-1, 1000), 1), Decimal("0.0"))


if __name__ == "__main__":
    unittest.main()
