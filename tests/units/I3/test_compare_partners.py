"""단위 I3(tools_compare_partners) 보조 시험: 허용 비교국, 모델 인자 partners, 비교국별 관측 상태, 비교 대상 집합.

자료는 I1 폴더의 합성 스냅샷(tools_fixture.py)이고 지표는 진짜 지표 단위(X1~X3)가 계산한다(metrics_spy.py가 호출만 기록). 값은 합성이다.
"""
import unittest

from tradesentry.contract import envelope as k5
from tradesentry.tools import check_comparability as common
from tradesentry.tools import compare_partners

from ..I1 import metrics_spy, tools_fixture as fx


class ComparePartnersTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        fx.use_fixture(self)
        self.spy = metrics_spy.spy_metrics(self)
        metrics_spy.fix_clock(self)

    def run_tool(self, args=None, partner="MX", month="202401", grouping="g0"):
        out = compare_partners.run(fx.request(args, partner=partner, month=month, grouping_version=grouping))
        self.assertEqual(k5.envelope_problems(out), [])
        return out

    def test_all_allowed_peers_in_rank_order(self):
        out = self.run_tool()
        comp = out["comparability"]
        self.assertEqual(comp["peers_allowed"], ["CN", "ID", "MY", "PH", "US"])
        self.assertEqual([(p["partner"], p["peer_rank"]) for p in comp["peers"]],
                         [("CN", 1), ("ID", 2), ("MY", 3), ("PH", 4), ("US", 5)])
        self.assertEqual([(m["inputs"]["metric"], m["inputs"]["partner"]) for m in out["metrics"]],
                         [(s, p) for p in ("CN", "ID", "MY", "PH", "US") for s in ("r_U", "d_s")])
        self.assertEqual(out["scope"]["partners"], ["CN", "ID", "MY", "PH", "US", "ALL"])
        self.assertEqual(out["scope"]["grouping_version"], "g0")
        for rowid in range(1, 6):
            self.assertIn(f"ev:unit_fixture_tools:peer_group:{rowid}", out["evidence_ids"])

    def test_out_of_plan_peer_is_not_collected_not_unchanged(self):
        out = self.run_tool()
        us = [p for p in out["comparability"]["peers"] if p["partner"] == "US"][0]
        self.assertEqual([m["observation_status"] for m in us["months"]], ["NOT_COLLECTED", "NOT_COLLECTED"])
        us_metrics = [m for m in out["metrics"] if m["inputs"]["partner"] == "US"]
        self.assertEqual({m["value"] for m in us_metrics}, {None})
        self.assertIn(("US", "202401", "NOT_COLLECTED"),
                      {(m["partner_code"], m["month"], m["observation_status"]) for m in out["missingness"]})

    def test_same_denominator_for_every_peer(self):
        self.run_tool()
        worlds = [call[1]["world"] for call in self.spy.calls if call[0] == "X2"]
        self.assertEqual(len(worlds), 5)
        self.assertTrue(all(w == worlds[0] for w in worlds))
        self.assertEqual({r["partner_code"] for r in worlds[0]}, {"ALL"})

    def test_partners_subset_keeps_rank_order(self):
        out = self.run_tool({"partners": ["PH", "CN"]})
        self.assertEqual([p["partner"] for p in out["comparability"]["peers"]], ["CN", "PH"])
        self.assertEqual(out["scope"]["partners"], ["CN", "PH", "ALL"])
        self.assertEqual(out["comparability"]["peers_allowed"], ["CN", "ID", "MY", "PH", "US"])

    def test_partner_outside_the_peer_group_is_retryable(self):
        out = self.run_tool({"partners": ["CN", "JP"]})
        self.assertEqual(out["retryable_error"]["code"], common.INVALID_ARGS)
        self.assertEqual(out["retryable_error"]["allowed"], ["CN", "ID", "MY", "PH", "US"])
        self.assertIn("JP", out["retryable_error"]["detail"])
        self.assertEqual((out["metrics"], out["evidence_ids"]), ([], []))
        self.assertEqual(self.spy.calls, [])

    def test_malformed_partners_are_refused(self):
        for args in ({"partners": "CN"}, {"partners": []}, {"partners": ["cn"]}, {"partners": ["CN", "CN"]},
                     {"partners": ["CN", "ID", "MY", "PH", "US", "JP"]}, {"partners": ["CN'; DROP TABLE observation;--"]},
                     {"partners": ["CN"], "grouping_version": "g1"}, {"partner": "CN"}):
            with self.subTest(args=args):
                out = self.run_tool(args)
                self.assertEqual(out["retryable_error"]["code"], common.INVALID_ARGS)
        self.assertEqual(self.spy.calls, [])

    def test_confirmed_no_trade_peer_is_a_state_not_missingness(self):
        out = self.run_tool({"partners": ["MY"]}, month="202402")
        months = out["comparability"]["peers"][0]["months"]
        self.assertEqual([(m["month"], m["observation_status"], m["amount_zero"]) for m in months],
                         [("202302", "UNRESOLVED_ZERO", None), ("202402", "CONFIRMED_NO_TRADE", None)])
        self.assertNotIn("CONFIRMED_NO_TRADE", {m["observation_status"] for m in out["missingness"]})

    def test_explicit_zero_import_is_marked(self):
        values = [{"month": "202301", "observation_status": "OBSERVED", "amount_usd": 0},
                  {"month": "202401", "observation_status": "OBSERVED", "amount_usd": 10},
                  {"month": "202402", "observation_status": "REQUEST_FAILED", "amount_usd": None}]
        self.assertEqual([m["amount_zero"] for m in compare_partners._month_states(values)], [True, False, None])

    def test_grouping_version_selects_the_peer_table(self):
        g1 = self.run_tool(grouping="g1")
        self.assertEqual(g1["comparability"]["peers_allowed"], ["CN"])
        none = self.run_tool(grouping="g9")
        self.assertEqual((none["comparability"]["peers_allowed"], none["metrics"]), ([], []))
        other = self.run_tool(partner="CN")
        self.assertEqual(other["comparability"]["peers"], [])

    def test_grouping_version_is_required(self):
        with self.assertRaises(common.ToolError):
            compare_partners.run(fx.request())


if __name__ == "__main__":
    unittest.main()
