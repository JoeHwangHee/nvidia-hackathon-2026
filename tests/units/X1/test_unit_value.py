"""단위 X1(metrics_unit_value) 추가 시험: 단가·변화율의 값과 null 규칙, 입력 거부.

기대값의 정본은 자료 계약 §11(단위와 정밀도)·§3.4(관측 상태)와 룰북 B3-1(계산할 수 없는 대상, 승격된 달)이다.
수는 모두 합성 값이다(실자료 계열의 값을 쓰지 않는다).
"""
import unittest
from decimal import Decimal
from fractions import Fraction

from tradesentry.metrics import unit_value as x1

SNAP = "ev:golden_metrics:observation:"


def row(month, status="OBSERVED", v=None, q=None, ev=None, **extra):
    base = {"month": month, "observation_status": status, "amount_usd": v, "net_weight_kg": q,
            "evidence_ids": [SNAP + (ev or month)]}
    base.update(extra)
    return base


def run(parent, partner="CN"):
    out = x1.run({"hs6": "850450", "partner": partner, "period": "202401", "baseline_period": "202301",
                  "parent": parent})
    return {(m["inputs"]["metric"], m["inputs"]["period"]): m for m in out["metrics"]}


def shown(metric):
    return None if metric["value"] is None else str(metric["value"])


class ValueTest(unittest.TestCase):
    def test_oracle_a_parent_values(self):
        got = run([row("202301", v=600, q=100), row("202401", v=360, q=100)])
        self.assertEqual(shown(got[("U", "202301")]), "6.00")
        self.assertEqual(shown(got[("U", "202401")]), "3.60")
        self.assertEqual(shown(got[("r_U", "202401")]), "-40.0")
        self.assertEqual(got[("r_U", "202401")]["unit"], "%")
        self.assertEqual(got[("r_U", "202401")]["inputs"]["baseline_period"], "202301")
        self.assertTrue(all(not m["comparability_flags"] for m in got.values()))

    def test_change_rate_rounds_half_away_from_zero(self):
        # 정확히 −30.05%와 +30.05%: 사사오입하면 −30.1, 30.1이다(0에서 먼 쪽)
        self.assertEqual(shown(run([row("202301", v=2000, q=100), row("202401", v=1399, q=100)])
                               [("r_U", "202401")]), "-30.1")
        self.assertEqual(shown(run([row("202301", v=2000, q=100), row("202401", v=2601, q=100)])
                               [("r_U", "202401")]), "30.1")

    def test_helpers(self):
        self.assertEqual(x1.unit_value(4069, 200), Fraction(4069, 200))
        self.assertIsNone(x1.unit_value(5, 0))
        self.assertIsNone(x1.unit_value(None, 5))
        self.assertEqual(x1.change_rate(Fraction(36, 10), Fraction(6)), Fraction(-40))
        self.assertIsNone(x1.change_rate(Fraction(1), Fraction(0)))
        self.assertIsNone(x1.change_rate(None, Fraction(1)))


class NullRuleTest(unittest.TestCase):
    def test_promoted_baseline_month(self):
        # 룰북 B3-1 "승격된 달": V·Q 칸은 null이어도 0으로 다룬다. 기준월이면 r_U 기대값은 null이다.
        got = run([row("202301", "CONFIRMED_NO_TRADE"), row("202401", v=360, q=100)])
        u0, rate = got[("U", "202301")], got[("r_U", "202401")]
        self.assertIsNone(u0["value"])
        self.assertEqual(u0["comparability_flags"], ["CONFIRMED_NO_TRADE", "zero_weight"])
        self.assertEqual((u0["inputs"]["V"], u0["inputs"]["Q"]), (0, 0))
        self.assertIsNone(rate["value"])
        self.assertEqual(rate["comparability_flags"], ["CONFIRMED_NO_TRADE", "zero_weight"])

    def test_explicit_zero_import_month(self):
        got = run([row("202301", v=600, q=100), row("202401", v=0, q=0)])  # 수입 0 명시(OBSERVED, 값 0)
        self.assertIsNone(got[("U", "202401")]["value"])
        self.assertEqual(got[("U", "202401")]["comparability_flags"], ["zero_weight"])
        self.assertEqual(got[("r_U", "202401")]["comparability_flags"], ["zero_weight"])

    def test_zero_baseline_unit_value(self):
        got = run([row("202301", v=0, q=50), row("202401", v=360, q=100)])
        self.assertEqual(shown(got[("U", "202301")]), "0.00")
        self.assertIsNone(got[("r_U", "202401")]["value"])
        self.assertEqual(got[("r_U", "202401")]["comparability_flags"], ["zero_baseline"])

    def test_positive_amount_zero_weight(self):
        # 룰북 경계 사례 6(금액은 있고 중량이 0인 행)
        got = run([row("202301", v=96, q=0), row("202401", v=360, q=100)])
        self.assertIsNone(got[("U", "202301")]["value"])
        self.assertEqual(got[("U", "202301")]["comparability_flags"], ["zero_weight"])
        self.assertIsNone(got[("r_U", "202401")]["value"])

    def test_missing_month_is_not_zero_filled(self):
        # HS4 스캔 요청이 실패해 부모 HS6 행이 없는 달: 상태 행은 요청 코드(HS4)에 귀속된다
        got = run([row("202301", v=600, q=100), row("202401", "REQUEST_FAILED", hs_code="8504", ev="9")])
        u1 = got[("U", "202401")]
        self.assertIsNone(u1["value"])
        self.assertEqual(u1["comparability_flags"], ["REQUEST_FAILED"])
        self.assertEqual(u1["evidence_ids"], [SNAP + "9"])
        self.assertEqual((u1["inputs"]["V"], u1["inputs"]["Q"]), (None, None))
        self.assertEqual(got[("r_U", "202401")]["comparability_flags"], ["REQUEST_FAILED"])
        self.assertEqual(got[("r_U", "202401")]["evidence_ids"], [SNAP + "202301", SNAP + "9"])

    def test_several_status_rows_in_a_month(self):
        got = run([row("202301", "NOT_COLLECTED", hs_code="850450", ev="7"),
                   row("202301", "UNRESOLVED_ZERO", hs_code="8504", ev="8"), row("202401", v=360, q=100)])
        self.assertEqual(got[("U", "202301")]["comparability_flags"], ["NOT_COLLECTED", "UNRESOLVED_ZERO"])
        self.assertEqual(got[("U", "202301")]["evidence_ids"], [SNAP + "7", SNAP + "8"])

    def test_observed_row_with_empty_weight(self):
        got = run([row("202301", v=600, q=None), row("202401", v=360, q=100)])
        self.assertEqual(got[("U", "202301")]["comparability_flags"], ["value_missing"])


class ExactValueTest(unittest.TestCase):
    """판정 정책(P1)은 반올림 전 값으로 임계값과 비교한다(같으면 발동). value는 표시 값이라 따로 다시 계산한다."""

    def test_exact_threshold_is_kept(self):
        rate = run([row("202301", v=2000, q=100), row("202401", v=1400, q=100)])[("r_U", "202401")]
        self.assertEqual(x1.exact_value(rate), Fraction(-30))  # 정확히 −30%: |r_U| ≥ 30이 참

    def test_rounded_value_can_cross_threshold_but_exact_does_not(self):
        rate = run([row("202301", v=2000, q=100), row("202401", v=14008, q=1000)])[("r_U", "202401")]
        self.assertEqual(shown(rate), "-30.0")  # 표시 값은 −30.0
        self.assertEqual(x1.exact_value(rate), Fraction(-2996, 100))  # 반올림 전은 −29.96

    def test_unit_values_and_nulls(self):
        got = run([row("202301", "CONFIRMED_NO_TRADE"), row("202401", v=4567891, q=372130)])
        self.assertEqual(x1.exact_value(got[("U", "202401")]), Fraction(4567891, 372130))
        self.assertIsNone(x1.exact_value(got[("U", "202301")]))
        self.assertIsNone(x1.exact_value(got[("r_U", "202401")]))

    def test_mismatched_object_is_rejected(self):
        got = run([row("202301", v=600, q=100), row("202401", v=360, q=100)])
        tampered = {**got[("r_U", "202401")], "value": Decimal("-39.9")}
        with self.assertRaises(ValueError):
            x1.exact_value(tampered)
        with self.assertRaises(ValueError):
            x1.exact_value({**got[("r_U", "202401")], "inputs": {**got[("r_U", "202401")]["inputs"], "metric": "s"}})


class RejectTest(unittest.TestCase):
    def test_bad_inputs(self):
        good = [row("202301", v=600, q=100), row("202401", v=360, q=100)]
        cases = {
            "부모 행 둘": good + [row("202401", v=1, q=1)],
            "다른 HS6 값 행": [row("202301", v=600, q=100, hs_code="850431"), good[1]],
            "범위 밖 HS4 상태 행": [row("202301", "REQUEST_FAILED", hs_code="8544"), good[1]],
            "달 없음": good[:1],
            "0으로 채운 누락": [row("202301", "UNRESOLVED_ZERO", v=0, q=0), good[1]],
        }
        for name, parent in cases.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                run(parent)
        with self.assertRaises(ValueError):
            run(good, partner="ALL")
        with self.assertRaises(ValueError):
            x1.run({"hs6": "850450", "partner": "CN", "period": "202401", "baseline_period": "202301",
                    "parent": good, "world": []})
        with self.assertRaises(TypeError):
            x1.run({"hs6": "850450", "partner": "CN", "period": "202401", "baseline_period": "202301"})


if __name__ == "__main__":
    unittest.main()
