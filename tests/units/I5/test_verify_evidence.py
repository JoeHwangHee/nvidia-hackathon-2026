"""단위 I5(tools_verify_evidence) 보조 시험: 원본 대조, 다른 도구를 부르지 않음, 근거 세탁 없음, 인자·요청 검사.

앞서 받은 봉투는 합성 스냅샷(I1 폴더의 tools_fixture.py)에서 도구 I2·I3·I4를 실제로 돌려 만든다(지표 단위는 대역).
"""
import copy
import unittest
from decimal import Decimal
from unittest import mock

from tradesentry.contract import envelope as k5
from tradesentry.tools import check_comparability as common
from tradesentry.tools import compare_partners, decompose_hs, get_history, verify_evidence

from ..I1 import fake_metrics, tools_fixture as fx

EV = "ev:unit_fixture_tools:"


class VerifyTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        fx.use_fixture(self)
        self.fake = fake_metrics.patch_metrics(self)
        fake_metrics.fix_clock(self)
        self.history = get_history.run(fx.request(attempt=1))
        self.peers = compare_partners.run(fx.request(grouping_version="g0", attempt=2))
        self.decomposition = decompose_hs.run(fx.request(policy_version="dev-0.1", attempt=3))
        self.envelopes = [self.history, self.peers, self.decomposition]

    def verify(self, metric_ids=(), evidence_ids=(), envelopes=None, **extra):
        args = {"metric_ids": list(metric_ids), "evidence_ids": list(evidence_ids)}
        inp = fx.request(args, policy_version="dev-0.1", envelopes=self.envelopes if envelopes is None else envelopes,
                         **extra)
        out = verify_evidence.run(inp)
        self.assertEqual(k5.envelope_problems(out), [])
        self.assertEqual((out["evidence_ids"], out["metrics"], out["missingness"]), ([], [], []))
        return out

    def metric(self, envelope, symbol, partner="MX"):
        return [m for m in envelope["metrics"] if m["inputs"]["metric"] == symbol and m["inputs"]["partner"] == partner][0]

    def test_honest_refs_pass(self):
        ids = [m["metric_id"] for env in self.envelopes for m in env["metrics"]]
        evidence = self.history["evidence_ids"][:3] + self.peers["evidence_ids"][:2] \
            + [m["evidence_id"] for m in self.peers["missingness"]]
        out = self.verify(ids, evidence)
        self.assertTrue(out["comparability"]["ok"], out["comparability"])
        self.assertEqual(len(out["comparability"]["metrics"]), len(set(ids)))
        self.assertIn(EV + "peer_group:1", evidence)

    def test_other_tools_are_not_called(self):
        with mock.patch.object(get_history, "run", side_effect=AssertionError), \
                mock.patch.object(compare_partners, "run", side_effect=AssertionError), \
                mock.patch.object(decompose_hs, "run", side_effect=AssertionError), \
                mock.patch.object(common, "run_tool", wraps=common.run_tool) as wrapped:
            self.verify([self.metric(self.history, "r_U")["metric_id"]])
        self.assertEqual(wrapped.call_count, 1)  # verify_evidence 자신뿐

    def test_tampered_metric_is_caught_by_recompute(self):
        envelopes = copy.deepcopy(self.envelopes)
        target = self.metric(envelopes[0], "r_U")
        target["inputs"]["V_1"] = 3700
        out = self.verify([target["metric_id"]], envelopes=envelopes)
        result = out["comparability"]["metrics"][0]
        self.assertEqual((result["problems"], result["fields"]), (["recompute_mismatch"], ["inputs"]))

    def test_trailing_zero_change_is_a_mismatch(self):
        envelopes = copy.deepcopy(self.envelopes)
        target = self.metric(envelopes[0], "U")
        target["value"] = Decimal(str(target["value"]) + "0")  # 6.00 → 6.000: 수는 같고 표기만 다르다
        out = self.verify([target["metric_id"]], envelopes=envelopes)
        self.assertEqual(out["comparability"]["metrics"][0]["fields"], ["value"])

    def test_unit_scope_symbol_and_shape_problems(self):
        envelopes = copy.deepcopy(self.envelopes)
        wrong_unit = self.metric(envelopes[0], "d_s")
        wrong_unit["unit"] = "%"
        foreign = copy.deepcopy(self.metric(envelopes[0], "r_U"))
        foreign.update(metric_id="x-foreign", inputs=dict(foreign["inputs"], partner="JP"))
        unknown = copy.deepcopy(foreign)
        unknown.update(metric_id="x-unknown", inputs=dict(foreign["inputs"], metric="Z"))
        broken = {"metric_id": "x-broken", "value": 1}
        twin = copy.deepcopy(self.metric(envelopes[0], "U"))
        twin["value"] = None
        twin["comparability_flags"] = ["x"]
        envelopes[0]["metrics"] += [foreign, unknown, broken, twin]
        ids = [wrong_unit["metric_id"], "x-foreign", "x-unknown", "x-broken", twin["metric_id"]]
        results = {r["metric_id"]: r["problems"] for r in self.verify(ids, envelopes=envelopes)["comparability"]["metrics"]}
        self.assertIn("unit_mismatch", results[wrong_unit["metric_id"]])
        self.assertEqual(results["x-foreign"], ["metric_out_of_scope"])
        self.assertEqual(results["x-unknown"], ["metric_symbol_unknown"])
        self.assertEqual(results["x-broken"], ["metric_malformed"])
        self.assertIn("metric_id_conflict", results[twin["metric_id"]])

    def test_decomposition_metric_is_recomputed_with_x3(self):
        within = self.metric(self.decomposition, "within_effect")
        out = self.verify([within["metric_id"]])
        self.assertTrue(out["comparability"]["ok"])
        self.assertIn("X3", [name for name, _ in self.fake.calls[-1:]])

    def test_evidence_checks(self):
        out = self.verify(evidence_ids=[EV + "observation:31", EV + "observation:239", EV + "observation:32",
                                        EV + "observation:1", EV + "observation:999999", "ev:other:observation:31",
                                        "not an id", EV + "collection_receipt:1", EV + "peer_group:6"])
        rows = {r["evidence_id"]: (r["problems"], r["failed_rule"]) for r in out["comparability"]["evidence"]}
        self.assertEqual(rows[EV + "observation:31"], ([], None))
        self.assertEqual(rows[EV + "observation:239"], ([], None))  # decompose_hs가 돌려준 하위 행
        self.assertEqual(rows[EV + "observation:32"], (["evidence_out_of_scope", "evidence_not_returned"], None))
        self.assertEqual(rows[EV + "observation:1"], (["evidence_total_row", "evidence_not_returned"], None))
        self.assertEqual(rows[EV + "observation:999999"][1], 4)
        self.assertEqual(rows["ev:other:observation:31"][1], 2)
        self.assertEqual(rows["not an id"][1], 1)
        self.assertEqual(rows[EV + "collection_receipt:1"][0], ["evidence_out_of_scope", "evidence_not_returned"])
        self.assertEqual(rows[EV + "peer_group:6"][0], ["evidence_not_returned"])  # g1 행(대상국 MX)은 범위 안

    def test_args_and_request_checks(self):
        for args in ({"metric_ids": "x"}, {"metric_ids": [1]}, {"evidence_ids": ["x"] * 201}, {"text": "부정"},
                     {"metric_ids": [""]}):
            with self.subTest(args=args):
                out = verify_evidence.run(fx.request(args, policy_version="dev-0.1", envelopes=self.envelopes))
                self.assertEqual(out["retryable_error"]["code"], common.INVALID_ARGS)
        other = copy.deepcopy(self.history)
        other["snapshot_id"] = "kcs_202201_202412_v2"
        for inp in (fx.request({}, policy_version="dev-0.1"), fx.request({}, envelopes=[]),
                    fx.request({}, policy_version="dev-0.1", envelopes=[other]),
                    fx.request({}, policy_version="dev-0.1", envelopes=[{"tool": "shell"}])):
            with self.subTest(inp=sorted(inp)), self.assertRaises(common.ToolError):
                verify_evidence.run(inp)

    def test_envelopes_are_only_for_verify_evidence(self):
        with self.assertRaises(common.ToolError):
            get_history.run(fx.request(envelopes=[]))


if __name__ == "__main__":
    unittest.main()
