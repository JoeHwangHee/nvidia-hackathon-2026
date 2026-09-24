"""단위 I2(tools_get_history) 보조 시험: 전년동월 지표, 이력, 지표 단위에 넘긴 역할별 행, 빠진 자료.

자료는 I1 폴더의 합성 스냅샷(tools_fixture.py)이고 지표는 진짜 지표 단위(X1~X3)가 계산한다(metrics_spy.py가 호출만 기록). 값은 합성이다.
"""
import unittest

from tradesentry.contract import envelope as k5
from tradesentry.tools import check_comparability as common
from tradesentry.tools import get_history

from ..I1 import metrics_spy, tools_fixture as fx

SYMBOLS = [("U", "MX", "202301"), ("U", "MX", "202401"), ("r_U", "MX", "202401"), ("V", "MX", "202301"),
           ("V", "MX", "202401"), ("V", "ALL", "202301"), ("V", "ALL", "202401"), ("s", "MX", "202301"),
           ("s", "MX", "202401"), ("d_s", "MX", "202401")]


class HistoryTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        fx.use_fixture(self)
        self.spy = metrics_spy.spy_metrics(self)
        metrics_spy.fix_clock(self)

    def run_tool(self, partner="MX", month="202401", args=None):
        out = get_history.run(fx.request(args, partner=partner, month=month))
        self.assertEqual(k5.envelope_problems(out), [])
        return out

    def test_yoy_metrics_come_from_x1_and_x2(self):
        out = self.run_tool()
        self.assertEqual([(m["inputs"]["metric"], m["inputs"]["partner"], m["inputs"]["period"]) for m in out["metrics"]],
                         SYMBOLS)
        values = {(m["inputs"]["metric"], m["inputs"]["period"], m["inputs"]["partner"]): m["value"]
                  for m in out["metrics"]}
        self.assertEqual(str(values[("r_U", "202401", "MX")]), "-40.0")
        self.assertEqual(str(values[("d_s", "202401", "MX")]), "-4.0")
        self.assertEqual([name for name, _ in self.spy.calls], ["X1", "X2"])

    def test_role_rows_passed_to_metrics(self):
        self.run_tool()
        x1 = self.spy.calls[0][1]
        self.assertEqual({k: x1[k] for k in ("hs6", "partner", "period", "baseline_period")},
                         {"hs6": fx.HS6, "partner": "MX", "period": "202401", "baseline_period": "202301"})
        self.assertEqual([(r["month"], r["hs_code"], r["amount_usd"], r["net_weight_kg"], r["observation_status"])
                          for r in x1["parent"]],
                         [("202301", fx.HS6, 6000, 1000, "OBSERVED"), ("202401", fx.HS6, 3600, 1000, "OBSERVED")])
        world = self.spy.calls[1][1]["world"]
        self.assertEqual([(r["month"], r["hs_code"], r["partner_code"], r["amount_usd"]) for r in world],
                         [("202301", fx.C1, "ALL", 30000), ("202301", fx.C2, "ALL", 30000),
                          ("202401", fx.C1, "ALL", 30000), ("202401", fx.C2, "ALL", 30000)])

    def test_history_lists_thirteen_months_with_pointers(self):
        out = self.run_tool()
        history = out["comparability"]["history"]
        self.assertEqual([h["month"] for h in history], common.months_between("202301", "202401"))
        self.assertEqual([h["observation_status"] for h in history if h["month"] in ("202301", "202306", "202401")],
                         ["OBSERVED"] * 3)
        self.assertEqual(history[1]["observation_status"], "UNRESOLVED_ZERO")
        for entry in history:
            self.assertTrue(entry["evidence_ids"])
            self.assertLessEqual(set(entry["evidence_ids"]), set(out["evidence_ids"]))
        self.assertEqual(out["scope"]["months"], common.months_between("202301", "202401"))
        self.assertEqual(out["missingness"], [])

    def test_confirmed_no_trade_and_missing_months(self):
        out = self.run_tool("MY", month="202402")
        x1 = self.spy.calls[0][1]
        self.assertEqual([(r["month"], r["observation_status"]) for r in x1["parent"]],
                         [("202302", "UNRESOLVED_ZERO"), ("202302", "UNRESOLVED_ZERO"), ("202402", "CONFIRMED_NO_TRADE")])
        statuses = {(m["partner_code"], m["hs_code"], m["month"], m["observation_status"]) for m in out["missingness"]}
        self.assertIn(("MY", "8504", "202302", "UNRESOLVED_ZERO"), statuses)
        self.assertIn(("ALL", "850431", "202402", "UNRESOLVED_ZERO"), statuses)
        self.assertNotIn("CONFIRMED_NO_TRADE", {s[3] for s in statuses})
        r_u = [m for m in out["metrics"] if m["inputs"]["metric"] == "r_U"][0]
        self.assertIsNone(r_u["value"])
        self.assertTrue(r_u["comparability_flags"])

    def test_not_collected_parent(self):
        out = self.run_tool("ID")
        self.assertEqual([(m["partner_code"], m["month"], m["observation_status"]) for m in out["missingness"]],
                         [("ID", "202401", "NOT_COLLECTED")])

    def test_model_args_are_refused(self):
        out = self.run_tool(args={"months": ["202201"]})
        self.assertEqual(out["retryable_error"]["code"], common.INVALID_ARGS)
        self.assertEqual(self.spy.calls, [])


if __name__ == "__main__":
    unittest.main()
