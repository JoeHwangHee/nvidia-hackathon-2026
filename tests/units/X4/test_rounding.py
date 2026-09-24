"""단위 X4(metrics_rounding) 추가 시험: 정확 반올림, 기호표, 중량 허용오차, metric 객체, 입력 검사.

골든 쌍(input.json·expected.json)은 test_golden.py가 본다. 여기서는 골든 쌍 하나로 담기 어려운 경계와 거부 규칙을
본다. 기대값의 정본은 자료 계약 §11과 룰북 B3-1의 경계 사례다. 수는 합성 값과 룰북이 가상 수치라고 밝힌 경계
사례(4,069 USD ÷ 200 kg)뿐이다(실자료 계열의 값을 쓰지 않는다).
"""
import unittest
from decimal import Decimal
from fractions import Fraction

from tradesentry.metrics import rounding as x4


def row(month, status="OBSERVED", v=None, q=None, **extra):
    base = {"month": month, "observation_status": status, "amount_usd": v, "net_weight_kg": q,
            "evidence_ids": [f"ev:golden_metrics:observation:{month}"]}
    base.update(extra)
    return base


class RoundHalfUpTest(unittest.TestCase):
    def test_exact_rounding_from_integers(self):
        # 정수 USD·kg에서 정확히 계산해 사사오입한다. 앞 둘은 합성 값(12.2749… → 12.27, 27.466…% → 27.5),
        # 뒤 둘은 룰북 B3-1 경계 사례 1의 가상 수치(4,069 USD ÷ 200 kg = 20.345, 딱 절반)다.
        self.assertEqual(str(x4.round_half_up(Fraction(4567891, 372130), 2)), "12.27")
        self.assertEqual(str(x4.round_half_up(Fraction(2345678 * 100, 8540000), 1)), "27.5")
        self.assertEqual(str(x4.round_half_up(Fraction(4069, 200), 2)), "20.35")
        self.assertEqual(str(x4.round_half_up(Fraction(-4069, 200), 2)), "-20.35")

    def test_exact_half_that_decimal_division_would_miss(self):
        # 1/3을 거쳐 딱 절반(0.125)이 되는 값. Decimal 28자리 나눗셈을 거치면 0.1249…로 잘려 0.12가 된다.
        with_thirds = Fraction(1, 3) * 3 / 8
        self.assertEqual(str(x4.round_half_up(with_thirds, 2)), "0.13")
        via_decimal = Decimal(1) / Decimal(3) * 3 / 8
        self.assertNotEqual(str(via_decimal), "0.125")  # 이 시험이 막으려는 함정이 실제로 있다

    def test_trailing_zeros_and_no_negative_zero(self):
        self.assertEqual(str(x4.round_half_up(6, 2)), "6.00")
        self.assertEqual(str(x4.round_half_up(Fraction(-4, 100), 1)), "0.0")
        self.assertEqual(str(x4.round_half_up(Decimal("-0.0"), 1)), "0.0")
        self.assertEqual(str(x4.round_half_up(Decimal("-0.05"), 1)), "-0.1")
        self.assertEqual(str(x4.round_half_up(Decimal("1234567890123456789012345678901.5"), 0)),
                         "1234567890123456789012345678902")  # 28자리 문맥에 잘리지 않는다

    def test_rejects_float_bool_and_non_finite(self):
        for bad in (0.1, True, "1.0", None):
            with self.subTest(bad=bad), self.assertRaises(TypeError):
                x4.round_half_up(bad, 2)
        for bad in (Decimal("NaN"), Decimal("Infinity")):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                x4.round_half_up(bad, 2)
        with self.assertRaises(ValueError):
            x4.round_half_up(1, -1)


class SymbolTest(unittest.TestCase):
    def test_contract_table(self):
        expected = {"V": ("USD", 0), "Q": ("kg", 0), "U": ("USD/kg", 2), "r_U": ("%", 1), "s": ("%", 1),
                    "d_s": ("pp", 1), "within_effect": ("USD/kg", 2), "mix_effect": ("USD/kg", 2),
                    "residual": ("USD/kg", 2), "U@8504501000": ("USD/kg", 2), "r_U@8504501000": ("%", 1),
                    "w@8504501000": ("%", 1)}
        for symbol, pair in expected.items():
            with self.subTest(symbol=symbol):
                self.assertEqual(x4.unit_and_places(symbol), pair)

    def test_undefined_symbols_are_rejected(self):
        for bad in ("within_effect@8504501000", "mix_effect@8504501000", "residual@8504501000", "w", "U@850450",
                    "U@85045010001", "U@８５０４５０１０００", "observation_status@8504501000", "V@8504501000",
                    "u", "r_U@", "@8504501000"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                x4.unit_and_places(bad)

    def test_display_types(self):
        self.assertIsInstance(x4.display("V", Decimal("600.5")), int)
        self.assertEqual(x4.display("V", Decimal("600.5")), 601)
        self.assertEqual(x4.display("Q", 372130), 372130)
        self.assertEqual(str(x4.display("d_s", -4)), "-4.0")
        self.assertIsNone(x4.display("U", None))


class WeightToleranceTest(unittest.TestCase):
    def test_collector_rule(self):
        # 수집기 verify와 같은 판정: |부모 − 하위 합| > 0.5×(행수+1)이면 불일치
        self.assertEqual(x4.weight_tolerance(6, Decimal("0.5")), Decimal("3.5"))
        self.assertTrue(x4.weight_within_tolerance(500000, 500002, 6, Decimal("0.5")))  # HS10 6행: 차 2 ≤ 3.5
        self.assertTrue(x4.weight_within_tolerance(100, 101, 1, Decimal("0.5")))  # 같으면 통과
        self.assertFalse(x4.weight_within_tolerance(100, 102, 2, Decimal("0.5")))
        self.assertTrue(x4.weight_within_tolerance(100, 100, 0, 0))

    def test_rejects_bad_arguments(self):
        with self.assertRaises(TypeError):
            x4.weight_tolerance(2, 0.5)
        for args in ((-1, Decimal("0.5")), (2, Decimal("-0.5")), (True, Decimal("0.5"))):
            with self.subTest(args=args), self.assertRaises(ValueError):
                x4.weight_tolerance(*args)
        with self.assertRaises(ValueError):
            x4.weight_within_tolerance(-1, 0, 0, Decimal("0.5"))


class MetricObjectTest(unittest.TestCase):
    def build(self, **changes):
        args = dict(hs6="850450", partner="CN", period="202401", baseline_period=None, values={"V": 360, "Q": 100},
                    evidence_ids=["ev:golden_metrics:observation:2", "ev:golden_metrics:observation:2"],
                    value=Fraction(36, 10))
        args.update(changes)
        return x4.metric("U", **args)

    def test_contract_keys_and_values(self):
        made = self.build()
        self.assertEqual(list(made), ["metric_id", "formula_version", "inputs", "evidence_ids", "value", "unit",
                                      "comparability_flags", "tolerance"])
        self.assertEqual(made["inputs"], {"metric": "U", "hs6": "850450", "partner": "CN", "period": "202401",
                                          "baseline_period": None, "V": 360, "Q": 100})
        self.assertEqual(made["evidence_ids"], ["ev:golden_metrics:observation:2"])
        self.assertEqual(str(made["value"]), "3.60")
        self.assertEqual(made["unit"], "USD/kg")
        self.assertEqual(made["formula_version"], x4.FORMULA_VERSION)
        self.assertRegex(made["metric_id"], r"^U-[0-9a-f]{16}$")

    def test_metric_id_is_deterministic_and_content_bound(self):
        self.assertEqual(self.build()["metric_id"], self.build()["metric_id"])
        self.assertNotEqual(self.build()["metric_id"], self.build(value=Fraction(37, 10))["metric_id"])
        self.assertNotEqual(self.build()["metric_id"], self.build(period="202301")["metric_id"])

    def test_snapshot_id_scopes_metric_id(self):
        # 근거 ID가 빈 지표(예: hs10_absent)도 스냅샷이 다르면 metric_id가 다르다(무역통계 검토 권고 7)
        empty = dict(evidence_ids=[], value=None, flags=["hs10_absent"], values={"V": None, "Q": None})
        ids = {self.build(**empty, snapshot_id=s)["metric_id"] for s in ("controlled_fixture_v0",
                                                                        "kcs_202201_202412_v2")}
        self.assertEqual(len(ids), 2)
        self.assertNotIn(self.build(**empty)["metric_id"], ids)
        same = self.build(snapshot_id="golden_metrics")
        self.assertEqual(same["metric_id"], self.build(snapshot_id="golden_metrics")["metric_id"])
        self.assertNotIn("snapshot_id", same["inputs"])  # 객체 모양(§2.3.4 키 8개)은 그대로다

    def test_evidence_must_belong_to_the_snapshot(self):
        with self.assertRaises(ValueError):
            self.build(snapshot_id="kcs_202201_202412_v2")  # 근거 ID는 golden_metrics의 것
        for bad in ("", "a:b", "a b", 5, None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                x4.check_snapshot_id(bad)
        with self.assertRaises(ValueError):
            x4.parse_snapshot_id({"hs6": "850450"})
        self.assertEqual(x4.parse_snapshot_id({"snapshot_id": "golden_metrics"}), "golden_metrics")

    def test_checked_exact(self):
        made = self.build()
        self.assertEqual(x4.checked_exact(made, Fraction(36, 10)), Fraction(36, 10))
        self.assertEqual(x4.checked_exact(made, Fraction(3601, 1000)), Fraction(3601, 1000))  # 표시 값 3.60과 같다
        for bad in (Fraction(3605, 1000), None):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                x4.checked_exact(made, bad)
        with self.assertRaises(TypeError):
            x4.checked_exact({**made, "value": 3.6}, Fraction(36, 10))

    def test_null_needs_a_reason(self):
        with self.assertRaises(ValueError):
            self.build(value=None)
        made = self.build(value=None, flags=["zero_weight", "REQUEST_FAILED", "zero_weight"])
        self.assertIsNone(made["value"])
        self.assertEqual(made["comparability_flags"], ["REQUEST_FAILED", "zero_weight"])


class InputCheckTest(unittest.TestCase):
    def test_target(self):
        good = {"hs6": "850450", "partner": "CN", "period": "202401", "baseline_period": "202301"}
        self.assertEqual(x4.parse_target(good), good)
        for key, bad in (("hs6", "85045"), ("hs6", 850450), ("partner", "ALL"), ("partner", "cn"),
                         ("period", "202413"), ("baseline_period", "202312"), ("baseline_period", "202401")):
            with self.subTest(key=key, bad=bad), self.assertRaises(ValueError):
                x4.parse_target({**good, key: bad})

    def test_rows_grouped_by_month(self):
        grouped = x4.parse_rows([row("202301", v=600, q=100), row("202401", "CONFIRMED_NO_TRADE")], role="부모",
                                months=("202301", "202401"), partner="CN")
        self.assertEqual(grouped["202301"][0]["V"], 600)
        self.assertEqual((grouped["202401"][0]["V"], grouped["202401"][0]["Q"]), (0, 0))  # 승격 행은 0으로 본다

    def test_row_rejections(self):
        months = ("202301", "202401")
        cases = {
            "달 없음": [row("202301", v=1, q=1)],
            "기간 밖": [row("202301", v=1, q=1), row("202401", v=1, q=1), row("202402", v=1, q=1)],
            "총계 행": [row("202301", v=1, q=1), row("RAW:총계", v=1, q=1)],
            "값·상태 섞임": [row("202301", v=1, q=1), row("202301", "REQUEST_FAILED"), row("202401", v=1, q=1)],
            "승격 행과 다른 행": [row("202301", "CONFIRMED_NO_TRADE"), row("202301", "NOT_COLLECTED"),
                          row("202401", v=1, q=1)],
            "상태 행에 값": [row("202301", "UNRESOLVED_ZERO", v=0, q=0), row("202401", v=1, q=1)],
            "승격 행에 값": [row("202301", "CONFIRMED_NO_TRADE", v=5, q=None), row("202401", v=1, q=1)],
            "음수": [row("202301", v=-1, q=1), row("202401", v=1, q=1)],
            "수출 행": [row("202301", v=1, q=1, flow="export"), row("202401", v=1, q=1)],
            "다른 상대국": [row("202301", v=1, q=1, partner_code="JP"), row("202401", v=1, q=1)],
            "모르는 상태": [row("202301", "MISSING", v=None, q=None), row("202401", v=1, q=1)],
            "hs_level 불일치": [row("202301", v=1, q=1, hs_code="850450", hs_level=10), row("202401", v=1, q=1)],
        }
        for name, rows in cases.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                x4.parse_rows(rows, role="부모", months=months, partner="CN")
        for name, rows in {"float 값": [row("202301", v=1.5, q=1), row("202401", v=1, q=1)],
                           "근거 ID 형식": [{**row("202301", v=1, q=1), "evidence_ids": "ev:x"},
                                        row("202401", v=1, q=1)]}.items():
            with self.subTest(name=name), self.assertRaises((TypeError, ValueError)):
                x4.parse_rows(rows, role="부모", months=months, partner="CN")

    def test_run_rejects_unknown_shapes(self):
        for bad in ({"value": []}, {"values": [{"metric": "U"}]}, {"values": [{"metric": "U", "value": 0.5}]},
                    {"weight_checks": [{"Q_parent": 1, "Q_hs10": 1, "row_count": 0}]}):
            with self.subTest(bad=bad), self.assertRaises((TypeError, ValueError)):
                x4.run(bad)


if __name__ == "__main__":
    unittest.main()
