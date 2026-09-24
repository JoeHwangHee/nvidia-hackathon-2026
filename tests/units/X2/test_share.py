"""단위 X2(metrics_share) 추가 시험: 점유율·변화의 값, 분모 규칙, null 규칙, 입력 거부.

기대값의 정본은 자료 계약 §11(단위와 정밀도)·§2.3.2 행 규칙 5·6과 룰북 B3-1(예시 6의 근거 모양, 경계 사례
9·12·14)이다. 수는 모두 합성 값이다(실자료 계열의 값을 쓰지 않는다).
"""
import unittest
from fractions import Fraction

from tradesentry.metrics import share as x2

SNAP = "ev:golden_metrics:observation:"


def parent_row(month, status="OBSERVED", v=None, ev=None, **extra):
    base = {"month": month, "observation_status": status, "amount_usd": v, "net_weight_kg": None if v is None else 1,
            "evidence_ids": [SNAP + (ev or "p" + month)]}
    if status == "CONFIRMED_NO_TRADE":
        base["net_weight_kg"] = None
    base.update(extra)
    return base


def world_row(month, code, v, status="OBSERVED", **extra):
    base = {"month": month, "hs_code": code, "observation_status": status, "amount_usd": v, "net_weight_kg": None,
            "partner_code": "ALL", "evidence_ids": [SNAP + f"w{month}{code}"]}
    base.update(extra)
    return base


def run(parent, world, partner="CN"):
    out = x2.run({"hs6": "850450", "partner": partner, "period": "202401", "baseline_period": "202301",
                  "parent": parent, "world": world})
    return {(m["inputs"]["metric"], m["inputs"]["partner"], m["inputs"]["period"]): m for m in out["metrics"]}


def shown(metric):
    return None if metric["value"] is None else str(metric["value"])


def two_rows(month, total):
    return [world_row(month, "8504501000", total - 2000), world_row(month, "8504509000", 2000)]


class ValueTest(unittest.TestCase):
    def test_oracle_a_share_fields(self):
        got = run([parent_row("202301", v=600), parent_row("202401", v=360)],
                  two_rows("202301", 6000) + two_rows("202401", 6000))
        self.assertEqual(got[("V", "CN", "202301")]["value"], 600)
        self.assertEqual(got[("V", "CN", "202401")]["value"], 360)
        self.assertEqual(got[("V", "ALL", "202301")]["value"], 6000)
        self.assertEqual(got[("V", "ALL", "202401")]["value"], 6000)
        self.assertEqual(shown(got[("s", "CN", "202301")]), "10.0")
        self.assertEqual(shown(got[("s", "CN", "202401")]), "6.0")
        d_s = got[("d_s", "CN", "202401")]
        self.assertEqual((shown(d_s), d_s["unit"]), ("-4.0", "pp"))  # 룰북 예시 11: d_s의 단위는 pp다

    def test_six_all_rows_denominator(self):
        # 합성 값: 2,345,678 ÷ 8,540,000 = 27.466…% → 27.5. 분모는 ALL HS10 행 6개의 합이다(룰북 예시 6과 같은 모양).
        amounts = [3000000, 2000000, 1500000, 1000000, 700000, 340000]
        codes = ["8504501000", "8504502000", "8504503000", "8504504000", "8504505000", "8504509000"]
        world = two_rows("202301", 50000000) + [world_row("202401", c, a) for c, a in zip(codes, amounts)]
        got = run([parent_row("202301", v=20000000), parent_row("202401", v=2345678)], world)
        self.assertEqual(got[("V", "ALL", "202401")]["value"], 8540000)
        self.assertEqual(got[("V", "ALL", "202401")]["inputs"]["row_count"], 6)
        self.assertEqual(shown(got[("s", "CN", "202401")]), "27.5")
        self.assertEqual(len(got[("s", "CN", "202401")]["evidence_ids"]), 7)  # 부모 행 + ALL HS10 행 6개

    def test_duplicate_all_rows_stop_instead_of_doubling(self):
        # 행 규칙 6을 빼먹으면 v2 분모가 두 배가 된다. 이 단위는 더하기 전에 키를 세고 멈춘다.
        world = two_rows("202301", 6000) + two_rows("202401", 6000) + [world_row("202401", "8504509000", 2000)]
        with self.assertRaises(ValueError):
            run([parent_row("202301", v=600), parent_row("202401", v=360)], world)


class NullRuleTest(unittest.TestCase):
    def test_promoted_numerator_counts_as_zero(self):
        # 룰북 경계 사례 9: 승격된 달은 0으로 다룬다. 기준월이면 s0 = 0이고 d_s는 계산한다.
        got = run([parent_row("202301", "CONFIRMED_NO_TRADE"), parent_row("202401", v=360)],
                  two_rows("202301", 6000) + two_rows("202401", 6000))
        self.assertEqual(got[("V", "CN", "202301")]["value"], 0)
        self.assertEqual(got[("V", "CN", "202301")]["comparability_flags"], ["CONFIRMED_NO_TRADE"])
        self.assertEqual(shown(got[("s", "CN", "202301")]), "0.0")
        self.assertEqual(shown(got[("d_s", "CN", "202401")]), "6.0")
        self.assertEqual(got[("d_s", "CN", "202401")]["comparability_flags"], ["CONFIRMED_NO_TRADE"])

    def test_explicit_zero_numerator(self):
        got = run([parent_row("202301", v=0), parent_row("202401", v=360)],
                  two_rows("202301", 6000) + two_rows("202401", 6000))
        self.assertEqual(shown(got[("s", "CN", "202301")]), "0.0")
        self.assertEqual(shown(got[("d_s", "CN", "202401")]), "6.0")
        self.assertEqual(got[("d_s", "CN", "202401")]["comparability_flags"], [])

    def test_missing_numerator(self):
        got = run([parent_row("202301", "UNRESOLVED_ZERO"), parent_row("202401", v=360)],
                  two_rows("202301", 6000) + two_rows("202401", 6000))
        self.assertIsNone(got[("V", "CN", "202301")]["value"])
        self.assertIsNone(got[("s", "CN", "202301")]["value"])
        self.assertEqual(got[("s", "CN", "202301")]["comparability_flags"], ["UNRESOLVED_ZERO"])
        self.assertIsNone(got[("d_s", "CN", "202401")]["value"])
        self.assertEqual(got[("d_s", "CN", "202401")]["comparability_flags"], ["UNRESOLVED_ZERO"])

    def test_missing_denominator(self):
        world = two_rows("202301", 6000) + [
            {"month": "202401", "hs_code": "850450", "observation_status": "REQUEST_FAILED", "amount_usd": None,
             "net_weight_kg": None, "evidence_ids": [SNAP + "fail"]}]
        got = run([parent_row("202301", v=600), parent_row("202401", v=360)], world)
        total = got[("V", "ALL", "202401")]
        self.assertIsNone(total["value"])
        self.assertEqual((total["comparability_flags"], total["inputs"]["row_count"]), (["REQUEST_FAILED"], None))
        self.assertEqual(total["evidence_ids"], [SNAP + "fail"])
        self.assertIsNone(got[("s", "CN", "202401")]["value"])
        self.assertEqual(got[("d_s", "CN", "202401")]["comparability_flags"], ["REQUEST_FAILED"])

    def test_zero_denominator(self):
        world = two_rows("202301", 6000) + [world_row("202401", "8504501000", 0)]
        got = run([parent_row("202301", v=600), parent_row("202401", v=0)], world)
        self.assertIsNone(got[("s", "CN", "202401")]["value"])
        self.assertEqual(got[("s", "CN", "202401")]["comparability_flags"], ["zero_denominator"])
        self.assertEqual(got[("d_s", "CN", "202401")]["comparability_flags"], ["zero_denominator"])

    def test_denominator_row_with_empty_amount(self):
        world = two_rows("202301", 6000) + [world_row("202401", "8504501000", None)]
        got = run([parent_row("202301", v=600), parent_row("202401", v=360)], world)
        self.assertEqual(got[("V", "ALL", "202401")]["comparability_flags"], ["value_missing"])


class ExactValueTest(unittest.TestCase):
    """판정 정책(P1)은 반올림 전 값으로 임계값과 비교한다(같으면 발동). value는 표시 값이라 따로 다시 계산한다."""

    def test_share_change_before_rounding(self):
        world = [world_row("202301", "8504501000", 10000), world_row("202401", "8504501000", 10000)]
        got = run([parent_row("202301", v=1006), parent_row("202401", v=2014)], world)
        self.assertEqual(shown(got[("d_s", "CN", "202401")]), "10.1")
        self.assertEqual(x2.exact_value(got[("d_s", "CN", "202401")]), Fraction(1008, 100))
        self.assertEqual(x2.exact_value(got[("s", "CN", "202301")]), Fraction(1006, 100))
        self.assertEqual(x2.exact_value(got[("V", "ALL", "202401")]), 10000)

    def test_exact_threshold_is_kept(self):
        world = [world_row("202301", "8504501000", 10000), world_row("202401", "8504501000", 10000)]
        got = run([parent_row("202301", v=1000), parent_row("202401", v=2000)], world)
        self.assertEqual(x2.exact_value(got[("d_s", "CN", "202401")]), Fraction(10))  # 정확히 10pp

    def test_nulls_and_mismatch(self):
        world = two_rows("202301", 6000) + [world_row("202401", "8504501000", 0)]
        got = run([parent_row("202301", v=600), parent_row("202401", v=0)], world)
        self.assertIsNone(x2.exact_value(got[("s", "CN", "202401")]))
        self.assertIsNone(x2.exact_value(got[("d_s", "CN", "202401")]))
        tampered = {**got[("s", "CN", "202301")], "value": None}
        with self.assertRaises(ValueError):
            x2.exact_value(tampered)


class RejectTest(unittest.TestCase):
    def test_bad_inputs(self):
        parent = [parent_row("202301", v=600), parent_row("202401", v=360)]
        good = two_rows("202301", 6000) + two_rows("202401", 6000)
        cases = {
            "다른 HS6 아래 행": good + [world_row("202401", "8504401000", 5)],
            "HS6 자릿수 값 행": good + [world_row("202401", "850450", 5)],
            "값·상태 섞임": good + [{"month": "202401", "hs_code": "850450", "observation_status": "REQUEST_FAILED",
                                "amount_usd": None, "net_weight_kg": None, "evidence_ids": []}],
            "상대국 행을 분모에": good[:3] + [world_row("202401", "8504509000", 2000, partner_code="CN")],
            "분모 달 없음": two_rows("202301", 6000),
        }
        for name, world in cases.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                run(parent, world)
        with self.assertRaises(ValueError):
            run(parent, good, partner="ALL")
        with self.assertRaises(TypeError):
            x2.run({"hs6": "850450", "partner": "CN", "period": "202401", "baseline_period": "202301",
                    "parent": parent})


if __name__ == "__main__":
    unittest.main()
