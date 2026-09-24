"""단위 P1(policy_trigger) 규칙 시험: 임계값 경계, null, 최소 기준, 입력 검사, 정책 객체 읽기."""
import unittest
from decimal import Decimal

from tradesentry.policy import trigger as p1

POLICY = {"policy_version": "dev-0.1", "thresholds": {"unit_value": 30, "share": 10}}


def row(**fields):
    base = {"hs6": "850450", "partner": "CN", "month": "202401", "baseline_month": "202301",
            "r_U": Decimal("-40.0"), "d_s": Decimal("-4.0")}
    base.update(fields)
    return base


def signals(policy, *rows):
    return [t["signals"] for t in p1.run({"policy": policy, "rows": list(rows)})["triggers"]]


class ThresholdTest(unittest.TestCase):
    def test_boundaries_use_unrounded_values(self):
        cases = [
            (Decimal("30"), "TRIGGERED"), (Decimal("-30.0"), "TRIGGERED"), (Decimal("29.99"), "NOT_TRIGGERED"),
            (Decimal("-29.96"), "NOT_TRIGGERED"), (Decimal("30.0000001"), "TRIGGERED"), (0, "NOT_TRIGGERED"),
        ]
        for value, expected in cases:
            with self.subTest(r_U=value):
                self.assertEqual(signals(POLICY, row(r_U=value))[0]["unit_value"], expected)
        for value, expected in [(Decimal("10.0"), "TRIGGERED"), (Decimal("-10"), "TRIGGERED"),
                                (Decimal("9.99"), "NOT_TRIGGERED")]:
            with self.subTest(d_s=value):
                self.assertEqual(signals(POLICY, row(d_s=value))[0]["share"], expected)

    def test_thresholds_come_from_policy(self):
        strict = {"policy_version": "p", "thresholds": {"unit_value": Decimal("50.5"), "share": 3}}
        self.assertEqual(signals(strict, row()), [{"unit_value": "NOT_TRIGGERED", "share": "TRIGGERED"}])

    def test_null_metric_goes_to_data_quality(self):
        out = p1.run({"policy": POLICY, "rows": [row(r_U=None)]})
        self.assertEqual(out["triggers"][0]["signals"], {"unit_value": "NOT_TRIGGERED", "share": "NOT_TRIGGERED"})
        self.assertEqual(out["data_quality"], [{"hs6": "850450", "partner": "CN", "month": "202401",
                                                "baseline_month": "202301", "signal": "unit_value",
                                                "reason": "metric_null"}])

    def test_output_sorted(self):
        out = p1.run({"policy": POLICY, "rows": [row(partner="JP"), row(month="202312", baseline_month="202212"),
                                                 row(hs6="850431")]})
        self.assertEqual([(t["hs6"], t["partner"], t["month"]) for t in out["triggers"]],
                         [("850431", "CN", "202401"), ("850450", "CN", "202312"), ("850450", "JP", "202401")])


class MinimumTest(unittest.TestCase):
    POLICY = {"policy_version": "p", "thresholds": {"unit_value": 30, "share": 10}, "min_amount": 1000,
              "min_weight": Decimal("5")}

    def mrow(self, amounts, weights, **fields):
        return row(amount_usd={"month": amounts[0], "baseline_month": amounts[1]},
                   net_weight_kg={"month": weights[0], "baseline_month": weights[1]}, d_s=Decimal("12"), **fields)

    def test_minimums_apply_to_unit_value_only(self):
        out = p1.run({"policy": self.POLICY, "rows": [self.mrow((999, 5000), (4, 100))]})
        self.assertEqual(out["triggers"][0]["signals"], {"unit_value": "NOT_TRIGGERED", "share": "TRIGGERED"})
        self.assertEqual([q["reason"] for q in out["data_quality"]], ["below_min_amount", "below_min_weight"])
        self.assertEqual({q["signal"] for q in out["data_quality"]}, {"unit_value"})

    def test_values_at_minimum_are_evaluated(self):
        out = p1.run({"policy": self.POLICY, "rows": [self.mrow((1000, 1000), (5, 5))]})
        self.assertEqual(out["triggers"][0]["signals"]["unit_value"], "TRIGGERED")
        self.assertEqual(out["data_quality"], [])

    def test_below_minimum_is_listed_even_without_large_change(self):
        out = p1.run({"policy": self.POLICY, "rows": [self.mrow((10, 5000), (100, 100), r_U=Decimal("1.0"))]})
        self.assertEqual([q["reason"] for q in out["data_quality"]], ["below_min_amount"])

    def test_minimums_need_parent_values(self):
        with self.assertRaises(ValueError):
            p1.run({"policy": self.POLICY, "rows": [row()]})
        with self.assertRaises(ValueError):
            p1.run({"policy": self.POLICY, "rows": [row(amount_usd={"month": 1, "baseline_month": 1.5},
                                                        net_weight_kg={"month": 9, "baseline_month": 9})]})

    def test_null_minimums_are_not_applied(self):
        policy = {**self.POLICY, "min_amount": None, "min_weight": None}
        self.assertEqual(signals(policy, row())[0]["unit_value"], "TRIGGERED")


class RejectTest(unittest.TestCase):
    def test_bad_rows(self):
        bad = [
            row(r_U=-40.0), row(d_s=True), row(r_U="-40"), row(r_U=Decimal("NaN")),
            row(hs6="85045"), row(hs6=850450), row(partner="ALL"), row(partner="cn"), row(partner=""),
            row(month="202413", baseline_month="202313"), row(baseline_month="202312"),
            row(month="2024-01"), {k: v for k, v in row().items() if k != "d_s"},
        ]
        for item in bad:
            with self.subTest(row=item), self.assertRaises(ValueError):
                p1.run({"policy": POLICY, "rows": [item]})

    def test_duplicate_series_month(self):
        with self.assertRaises(ValueError):
            p1.run({"policy": POLICY, "rows": [row(), row(r_U=Decimal("1"))]})

    def test_bad_policy(self):
        bad = [
            None, {}, {"thresholds": {"unit_value": 30, "share": 10}},
            {"policy_version": "", "thresholds": {"unit_value": 30, "share": 10}},
            {"policy_version": "p", "thresholds": {"unit_value": 0.3, "share": 10}},
            {"policy_version": "p", "thresholds": {"unit_value": 30}},
            {"policy_version": "p", "thresholds": {"unit_value": 0, "share": 10}},
            {"policy_version": "p", "thresholds": {"unit_value": 30, "share": -10}},
            {"policy_version": "p", "thresholds": {"unit_value": 30, "share": 10}, "min_amount": -1},
            {"policy_version": "p", "thresholds": {"unit_value": 30, "share": 10}, "min_weight": 0.5},
        ]
        for policy in bad:
            with self.subTest(policy=policy), self.assertRaises(ValueError):
                p1.run({"policy": policy, "rows": [row()]})

    def test_bad_envelope(self):
        for inp in (None, {"policy": POLICY}, {"policy": POLICY, "rows": {}}, {"policy": POLICY, "rows": [], "x": 1}):
            with self.subTest(inp=inp), self.assertRaises(ValueError):
                p1.run(inp)


class PolicyValuesTest(unittest.TestCase):
    def test_reads_only_known_keys(self):
        values = p1.policy_values({**POLICY, "promotion_rule": {"any": "thing"}, "min_amount": 100})
        self.assertEqual(values, {"policy_version": "dev-0.1", "unit_value": 30, "share": 10, "min_amount": 100,
                                  "min_weight": None})

    def test_baseline_of(self):
        self.assertEqual(p1.baseline_of("202401"), "202301")
        self.assertEqual(p1.baseline_of("202312"), "202212")


if __name__ == "__main__":
    unittest.main()
