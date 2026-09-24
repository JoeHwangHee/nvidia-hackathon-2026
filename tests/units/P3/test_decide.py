"""단위 P3(policy_signal_decide) 규칙 시험: 판정 순서, 계열 배정, 신호 독립, "기준 안" 경계, 입력 검사."""
import copy
import unittest
from decimal import Decimal

from tradesentry.policy import required_evidence as p5
from tradesentry.policy import signal_decide as p3

D = Decimal
POLICY = {"policy_version": "dev-0.1", "thresholds": {"unit_value": 30, "share": 10}}
CASE = {"case_id": "850450-CN-202401", "hs6": "850450", "partner": "CN", "month": "202401",
        "baseline_month": "202301", "signals": {"unit_value": "TRIGGERED", "share": "TRIGGERED"}}
EXPLAINED = {"U_baseline": D("6.00"),
             "decomposition": {"within_effect": D("0.00"), "mix_effect": D("-2.40"), "residual": D("0.00"),
                               "parent_child_match": True},
             "children": [{"hs10": "8504501010", "r_U": D("0.0")}, {"hs10": "8504501020", "r_U": D("0.0")}]}


def decide(unit_value=None, share=None, missingness=None, signals=None, policy=POLICY):
    case = dict(CASE, signals=signals or CASE["signals"])
    evidence = {"missingness": missingness or [], "unit_value": copy.deepcopy(EXPLAINED if unit_value is None
                                                                               else unit_value),
                "share": share or {}}
    return p3.run({"policy": policy, "case": case, "evidence": evidence})


def uv(**changes):
    block = copy.deepcopy(EXPLAINED)
    decomposition = changes.pop("decomposition", None)
    if decomposition:
        block["decomposition"].update(decomposition)
    block.update(changes)
    return block


def miss(partner, hs_code, month, status):
    return {"partner": partner, "hs_code": hs_code, "month": month, "observation_status": status}


class UnitValueRuleTest(unittest.TestCase):
    def status(self, **kwargs):
        out = decide(**kwargs)
        return out["signal_status"]["unit_value"], out["basis"]["unit_value"]

    def test_composition_explained_is_monitor(self):
        self.assertEqual(self.status(), ("MONITOR", "composition_explained"))

    def test_within_effect_at_threshold_is_not_explained(self):
        # |within| × 100 = 1.80 × 100 = 180 = 30 × 6.00 → "기준 안"(<)이 아니다
        block = uv(decomposition={"within_effect": D("-1.80"), "mix_effect": D("-0.60")})
        self.assertEqual(self.status(unit_value=block), ("MAINTAIN", "unexplained"))
        block = uv(decomposition={"within_effect": D("-1.79"), "mix_effect": D("-0.61")})
        self.assertEqual(self.status(unit_value=block), ("MONITOR", "composition_explained"))

    def test_large_offsetting_components_are_not_explained(self):
        block = uv(decomposition={"within_effect": D("-2.00"), "residual": D("2.00"), "mix_effect": D("-2.40")})
        self.assertEqual(self.status(unit_value=block), ("MAINTAIN", "unexplained"))
        block = uv(decomposition={"residual": D("-1.80"), "mix_effect": D("-0.60")})
        self.assertEqual(self.status(unit_value=block), ("MAINTAIN", "unexplained"))

    def test_unstable_child_is_not_explained(self):
        block = uv(children=[{"hs10": "8504501010", "r_U": D("45.0")}, {"hs10": "8504501020", "r_U": D("-40.0")}])
        self.assertEqual(self.status(unit_value=block), ("MAINTAIN", "unexplained"))
        block = uv(children=[{"hs10": "8504501010", "r_U": D("-30")}])
        self.assertEqual(self.status(unit_value=block), ("MAINTAIN", "unexplained"))

    def test_missing_decomposition_is_hold_not_maintain(self):
        cases = {
            "absent": {k: v for k, v in EXPLAINED.items() if k != "decomposition"},
            "null effect": uv(decomposition={"within_effect": None}),
            "parent mismatch": uv(decomposition={"parent_child_match": False}),
            "no children": uv(children=[]),
            "null child": uv(children=[{"hs10": "8504501010", "r_U": None}]),
            "no baseline U": {k: v for k, v in EXPLAINED.items() if k != "U_baseline"},
            "zero baseline U": uv(U_baseline=0),
        }
        for name, block in cases.items():
            with self.subTest(name=name):
                self.assertEqual(self.status(unit_value=block), ("HOLD", "data_insufficient"))
        out = decide(unit_value={})
        self.assertEqual(out["gaps"]["unit_value"], [{"reason": "decomposition_absent"}])

    def test_missing_child_observation_is_hold(self):
        for status in ("REQUEST_FAILED", "NOT_COLLECTED", "UNRESOLVED_ZERO"):
            for hs_code in ("850450", "8504501010"):
                with self.subTest(status=status, hs_code=hs_code):
                    out = decide(missingness=[miss("CN", hs_code, "202301", status)])
                    self.assertEqual(out["signal_status"]["unit_value"], "HOLD")
                    self.assertEqual(out["gaps"]["unit_value"][0]["observation_status"], status)

    def test_comparability_issue_is_hold(self):
        self.assertEqual(self.status(unit_value=uv(comparability_issues=["hs_version_changed"])),
                         ("HOLD", "data_insufficient"))

    def test_rounding_unstable_is_hold_even_if_explained(self):
        self.assertEqual(self.status(unit_value=uv(rounding_unstable=True)), ("HOLD", "rounding_unstable"))

    def test_resolved_after_correction_is_monitor(self):
        block = uv(children=[{"hs10": "8504501010", "r_U": D("-40")}], resolved_after_correction=True)
        self.assertEqual(self.status(unit_value=block), ("MONITOR", "resolved_after_correction"))

    def test_data_gap_comes_before_other_rules(self):
        block = uv(rounding_unstable=True, resolved_after_correction=True)
        out = decide(unit_value=block, missingness=[miss("CN", "8504501010", "202401", "REQUEST_FAILED")])
        self.assertEqual(out["basis"]["unit_value"], "data_insufficient")


class ShareRuleTest(unittest.TestCase):
    def test_share_maintain_hold_monitor(self):
        self.assertEqual(decide()["signal_status"]["share"], "MAINTAIN")
        self.assertEqual(decide(missingness=[miss("ALL", "8504501010", "202401", "REQUEST_FAILED")])
                         ["signal_status"]["share"], "HOLD")
        self.assertEqual(decide(share={"comparability_issues": ["denominator_incomplete"]})
                         ["signal_status"]["share"], "HOLD")
        self.assertEqual(decide(share={"resolved_after_correction": True})["basis"]["share"],
                         "resolved_after_correction")

    def test_share_has_no_rounding_flag(self):
        with self.assertRaises(ValueError):
            decide(share={"rounding_unstable": True})


class AttributionTest(unittest.TestCase):
    def test_ignored_missingness(self):
        ignored = [
            miss("JP", "850450", "202401", "NOT_COLLECTED"),            # 비교국
            miss("CN", "8504501010", "202312", "REQUEST_FAILED"),       # 비교월·기준월 밖
            miss("ALL", "8504311000", "202401", "UNRESOLVED_ZERO"),     # 사례 HS6 밖
            miss("CN", "8504501010", "202401", "CONFIRMED_NO_TRADE"),   # 무거래 확정
            miss("ALL", "8504501010", "202401", "OBSERVED"),
        ]
        out = decide(missingness=ignored)
        self.assertEqual(out["signal_status"], {"unit_value": "MONITOR", "share": "MAINTAIN"})
        self.assertEqual(out["gaps"], {"unit_value": [], "share": []})

    def test_signals_are_decided_independently(self):
        out = decide(missingness=[miss("CN", "850450", "202401", "REQUEST_FAILED")])
        self.assertEqual(out["signal_status"], {"unit_value": "HOLD", "share": "MAINTAIN"})
        out = decide(missingness=[miss("ALL", "8504501010", "202301", "NOT_COLLECTED")])
        self.assertEqual(out["signal_status"], {"unit_value": "MONITOR", "share": "HOLD"})

    def test_not_triggered_signal_ignores_evidence(self):
        out = decide(signals={"unit_value": "NOT_TRIGGERED", "share": "TRIGGERED"}, unit_value={},
                     missingness=[miss("CN", "850450", "202401", "REQUEST_FAILED")])
        self.assertEqual(out["signal_status"], {"unit_value": "NOT_TRIGGERED", "share": "MAINTAIN"})
        self.assertEqual(out["basis"]["unit_value"], "not_triggered")
        self.assertEqual(out["gaps"]["unit_value"], [])


class ConsistencyTest(unittest.TestCase):
    def test_status_follows_p5_rules(self):
        variants = [dict(), dict(unit_value=uv(rounding_unstable=True)), dict(unit_value={}),
                    dict(unit_value=uv(resolved_after_correction=True), share={"resolved_after_correction": True}),
                    dict(unit_value=uv(children=[{"hs10": "8504501010", "r_U": D("50")}])),
                    dict(missingness=[miss("ALL", "8504501010", "202401", "REQUEST_FAILED")])]
        for kwargs in variants:
            out = decide(**kwargs)
            for code in ("unit_value", "share"):
                with self.subTest(kwargs=kwargs, code=code):
                    self.assertEqual(out["signal_status"][code], p5.rule_status(code, out["basis"][code]))

    def test_threshold_comes_from_policy(self):
        strict = {"policy_version": "p", "thresholds": {"unit_value": D("50"), "share": 10}}
        block = uv(children=[{"hs10": "8504501010", "r_U": D("45.0")}])
        self.assertEqual(decide(unit_value=block)["signal_status"]["unit_value"], "MAINTAIN")
        self.assertEqual(decide(unit_value=block, policy=strict)["signal_status"]["unit_value"], "MONITOR")


class RejectTest(unittest.TestCase):
    def test_bad_input(self):
        bad_blocks = [
            uv(U_baseline=6.0),
            uv(decomposition={"within_effect": 0.0}),
            uv(children=[{"hs10": "8504501010", "r_U": 0.5}]),
            uv(children=[{"hs10": "", "r_U": D("0")}]),
            uv(children=[{"code": "8504501010", "r_U": D("0")}]),
            uv(rounding_unstable="no"),
            uv(comparability_issues="hs_version_changed"),
            uv(extra=True),
            dict(EXPLAINED, decomposition={"within_effect": D("0"), "mix_effect": D("0"), "residual": D("0")}),
            dict(EXPLAINED, decomposition={"within_effect": D("0"), "mix_effect": D("0"), "residual": D("0"),
                                           "parent_child_match": "yes"}),
        ]
        for block in bad_blocks:
            with self.subTest(block=block), self.assertRaises(ValueError):
                decide(unit_value=block)
        with self.assertRaises(ValueError):
            decide(missingness=[miss("CN", "850450", "202401", "MISSING")])
        with self.assertRaises(ValueError):
            decide(missingness=[{"partner": "CN", "month": "202401", "observation_status": "REQUEST_FAILED"}])

    def test_bad_case_and_envelope(self):
        base = {"policy": POLICY, "case": CASE, "evidence": {}}
        bad = [None, {k: v for k, v in base.items() if k != "evidence"}, dict(base, extra=1),
               dict(base, evidence={"peers": []}), dict(base, case=dict(CASE, baseline_month="202312")),
               dict(base, case=dict(CASE, partner="ALL")), dict(base, case=dict(CASE, case_id="")),
               dict(base, case=dict(CASE, signals={"unit_value": "TRIGGERED"})),
               dict(base, policy={"policy_version": "p", "thresholds": {"unit_value": 0.3, "share": 10}})]
        for inp in bad:
            with self.subTest(inp=inp), self.assertRaises(ValueError):
                p3.run(inp)


if __name__ == "__main__":
    unittest.main()
