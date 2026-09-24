"""단위 I4(tools_decompose_hs) 보조 시험: X3에 넘기는 역할별 행과 정책 수치, 하위자료 실패·무거래 확정, 싣는 지표(U@·r_U@·w@),
C형(한 달 실패·두 구간 실패)의 빠진 HS10 코드와 진짜 X3의 실패 달 지표.

자료는 I1 폴더의 합성 스냅샷(tools_fixture.py)이고 지표는 진짜 지표 단위 X3이 계산한다(metrics_spy.py가 호출만 기록). 값은 합성이다.
"""
import unittest
from decimal import Decimal

from tradesentry.contract import envelope as k5
from tradesentry.tools import check_comparability as common
from tradesentry.tools import decompose_hs

from ..I1 import metrics_spy, tools_fixture as fx


class DecomposeTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        fx.use_fixture(self)
        self.spy = metrics_spy.spy_metrics(self)
        metrics_spy.fix_clock(self)

    def run_tool(self, partner="MX", month="202401", args=None):
        out = decompose_hs.run(fx.request(args, partner=partner, month=month, policy_version="dev-0.1"))
        self.assertEqual(k5.envelope_problems(out), [])
        return out

    def test_composition_case(self):
        out = self.run_tool()
        values = {m["inputs"]["metric"] + ":" + m["inputs"]["period"]: str(m["value"]) for m in out["metrics"]}
        self.assertEqual((values["within_effect:202401"], values["mix_effect:202401"], values["residual:202401"]),
                         ("0.00", "-2.40", "0.00"))
        self.assertEqual(values[f"r_U@{fx.C1}:202401"], "0.0")
        self.assertEqual((values[f"w@{fx.C1}:202301"], values[f"w@{fx.C1}:202401"]), ("50.0", "80.0"))
        self.assertEqual(values[f"U@{fx.C1}:202301"], "2.00")  # 계약 §2.3.4: U@·r_U@·w@를 모두 싣는다
        self.assertEqual(sorted({m["inputs"]["metric"].partition("@")[0] for m in out["metrics"]}),
                         ["U", "mix_effect", "r_U", "residual", "w", "within_effect"])
        self.assertEqual(len(out["metrics"]), 3 + 5 * 2)
        self.assertTrue(all(c["V_match"] and c["Q_match"] for c in out["comparability"]["parent_check"]))
        self.assertTrue(out["comparability"]["same_hs10_set"])

    def test_x3_input_roles_and_policy_rounding(self):
        self.run_tool()
        name, inp = self.spy.calls[0]
        self.assertEqual(name, "X3")
        self.assertEqual(inp["weight_rounding_kg"], Decimal("0.5"))  # configs/policy_dev.json tolerance
        self.assertEqual([(r["month"], r["hs_code"], r["amount_usd"], r["net_weight_kg"]) for r in inp["children"]],
                         [("202301", fx.C1, 1000, 500), ("202301", fx.C2, 5000, 500),
                          ("202401", fx.C1, 1600, 800), ("202401", fx.C2, 2000, 200)])
        self.assertEqual({r["partner_code"] for r in inp["children"] + inp["parent"]}, {"MX"})

    def test_c_type_month_names_the_missing_hs10_codes(self):
        out = self.run_tool("CN")
        entry = out["missingness"][0]
        self.assertEqual((entry["month"], entry["observation_status"], entry["hs10_codes"], entry["hs10_codes_source"]),
                         ("202401", "REQUEST_FAILED", [fx.C1, fx.C2], "other_case_month"))
        # 진짜 X3: 실패한 달의 U@·w@는 null이고 사유는 그 상태 코드, 근거는 그 상태 행이다
        failed = [m for m in out["metrics"] if m["inputs"]["period"] == "202401" and m["inputs"]["metric"][:2] in ("U@", "w@")]
        self.assertEqual(len(failed), 4)
        for metric in failed:
            self.assertIsNone(metric["value"])
            self.assertIn("REQUEST_FAILED", metric["comparability_flags"])
            self.assertEqual(metric["evidence_ids"], [entry["evidence_id"]])

    def test_both_months_failed_take_codes_from_the_reference_table(self):
        out = self.run_tool("KH")
        effects = [m for m in out["metrics"] if m["inputs"]["metric"] in ("within_effect", "mix_effect", "residual")]
        self.assertEqual({m["value"] for m in effects}, {None})
        self.assertEqual({(m["month"], m["hs10_codes_source"]) for m in out["missingness"]},
                         {("202301", "reference_table"), ("202401", "reference_table")})
        self.assertTrue(all(len(m["hs10_codes"]) == 5 and all(c.startswith(fx.HS6) for c in m["hs10_codes"])
                            for m in out["missingness"]))
        self.assertEqual(out["comparability"]["same_hs10_set"], None)

    def test_failed_hs10_request_leaves_effects_null(self):
        out = self.run_tool("CN")
        effects = [m for m in out["metrics"] if m["inputs"]["metric"] in ("within_effect", "mix_effect", "residual")]
        self.assertEqual({m["value"] for m in effects}, {None})
        self.assertTrue(all("REQUEST_FAILED" in m["comparability_flags"] for m in effects))
        self.assertEqual(out["comparability"]["hs10"][1], {"month": "202401", "observation_status": "REQUEST_FAILED",
                                                           "codes": []})
        self.assertIsNone(out["comparability"]["same_hs10_set"])
        self.assertEqual([(m["hs_code"], m["month"], m["observation_status"]) for m in out["missingness"]],
                         [("850431", "202401", "REQUEST_FAILED")])
        children = self.spy.calls[0][1]["children"]
        self.assertEqual([(r["month"], r["hs_code"], r["observation_status"]) for r in children if r["month"] == "202401"],
                         [("202401", "850431", "REQUEST_FAILED")])

    def test_confirmed_no_trade_children_row(self):
        out = self.run_tool("MY", month="202402")
        children = self.spy.calls[0][1]["children"]
        self.assertEqual([(r["month"], r["observation_status"]) for r in children if r["month"] == "202402"],
                         [("202402", "CONFIRMED_NO_TRADE")])
        parent = [r for r in self.spy.calls[0][1]["parent"] if r["month"] == "202402"][0]
        cnt_child = [r for r in children if r["month"] == "202402"][0]
        self.assertTrue(cnt_child["evidence_ids"])  # 부모의 무거래 확정 근거(같은 상태 행)를 붙인다
        self.assertEqual(cnt_child["evidence_ids"], parent["evidence_ids"])
        self.assertEqual(out["comparability"]["hs10"][1]["observation_status"], "CONFIRMED_NO_TRADE")
        self.assertNotIn("CONFIRMED_NO_TRADE", {m["observation_status"] for m in out["missingness"]})

    def test_policy_version_is_required_and_args_are_refused(self):
        with self.assertRaises(common.ToolError):
            decompose_hs.run(fx.request())
        out = self.run_tool(args={"hs10": [fx.C1]})
        self.assertEqual(out["retryable_error"]["code"], common.INVALID_ARGS)
        self.assertEqual(self.spy.calls, [])


if __name__ == "__main__":
    unittest.main()
