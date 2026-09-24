"""독립 채점기 단위 C1(주장 채점) 시험: 룰북 B3 사전 조건(채점기 검증).

- eval/dev/oracle_ABC.json의 합성 사례 A/B/C 기대값(U0·U1·r_U·within·mix·residual·점유율·d_s)을 채점기가 원본 행에서
  따로 계산해 재현하는지 본다.
- 룰북 docs/eval/RULEBOOK.md B3-1의 예시 1~14와 경계 사례 1~19(손계산 예제)의 판정을 재현하는지 본다. 예시 1~8의
  v2 값은 tests/scorer_fixtures.py가 합성 행으로 다시 만든다(실제 스냅샷 파일은 쓰지 않는다).
- 네트워크·키·봉인 폴더 없이 돈다.
"""
import unittest
from decimal import Decimal
from fractions import Fraction

import scorer_fixtures as fx
from eval.scorer import claims as c1

C = c1.CORRECT


def score(rows: fx.Rows, claim: dict) -> dict:
    snap = c1.Snapshot.from_json(rows.doc())
    return c1.score_claim(claim, 0, snap, "run_case-260925100000", "report-1", rows.snapshot_id)


class OracleReproductionTest(unittest.TestCase):
    """oracle A/B/C의 설계값을 원본 행에서 따로 계산해 재현한다(룰북 B3 채점 절차 0, 자료 계약 §11.5)."""

    @classmethod
    def setUpClass(cls):
        cls.oracle = fx.load_oracle()
        cls.rows, cls.ids = fx.oracle_snapshot(cls.oracle)
        cls.snap = c1.Snapshot.from_json(cls.rows.doc())

    def expected(self, case_id: str) -> dict:
        return next(case["expected"] for case in self.oracle["cases"] if case["case_id"] == case_id)

    def value(self, base: str, partner: str, month: str = "202401", baseline: str = "202301") -> Fraction | None:
        if base in ("V", "Q", "U", "s"):
            return c1.expect_level(self.snap, base, partner, "850450", month).value
        if base in ("r_U", "d_s"):
            return c1.expect_change(self.snap, base, partner, "850450", month, baseline).value
        return c1.expect_decomposition(self.snap, base, partner, "850450", month, baseline).value

    def test_all_three_cases(self):
        self.assertEqual(len(self.oracle["cases"]), 3)
        for case_id, partner in fx.ORACLE_PARTNERS.items():
            with self.subTest(case=case_id):
                unit, share = self.expected(case_id)["unit_value"], self.expected(case_id)["share"]
                self.assertEqual(self.value("U", partner, "202301"), Fraction(unit["U0"]))
                self.assertEqual(self.value("U", partner), Fraction(unit["U1"]))
                self.assertEqual(self.value("r_U", partner), Fraction(unit["r_U"]) * 100)  # 비율 → 백분율(§11.5)
                for key in ("within", "mix"):
                    base = "within_effect" if key == "within" else "mix_effect"
                    want = unit[key]
                    self.assertEqual(self.value(base, partner), None if want is None else Fraction(want))
                if "residual" in unit:
                    self.assertEqual(self.value("residual", partner), Fraction(unit["residual"]))
                else:  # C: HS10 조회가 실패해 residual도 계산하지 않는다(자료 계약 §2.3.2 행 규칙 4)
                    self.assertIsNone(self.value("residual", partner))
                self.assertEqual(self.value("V", partner, "202301"), share["V_country_0"])
                self.assertEqual(self.value("V", partner), share["V_country_1"])
                self.assertEqual(self.value("V", "ALL", "202301"), share["V_world_0"])
                self.assertEqual(self.value("V", "ALL"), share["V_world_1"])
                self.assertEqual(self.value("s", partner, "202301"), Fraction(share["s0_pp"]))
                self.assertEqual(self.value("s", partner), Fraction(share["s1_pp"]))
                self.assertEqual(self.value("d_s", partner), Fraction(share["d_s_pp"]))

    def test_rulebook_examples_9_to_14(self):
        a, cc = self.ids["A-composition"], self.ids["C-missing-hs10"]
        ev = self.rows.ev
        a_parents = [ev(a["parent_comparison"]), ev(a["parent_baseline"])]
        a_all = a_parents + [ev(r) for r in a["kids_comparison"] + a["kids_baseline"]]
        cases = [
            ("9", fx.claim("c9", "change", "r_U", Decimal("-40.0"), "%", "DOWN", a_parents, baseline="202301"), C),
            ("10", fx.claim("c10", "change", "r_U", Decimal("-40.0"), "%", "UP", a_parents, baseline="202301"),
             c1.WRONG_DIRECTION),
            ("11", fx.claim("c11", "share_change", "d_s", Decimal("-4.0"), "%", "DOWN",
                            a_parents + [ev(r) for r in self.ids["world"]["202401"] + self.ids["world"]["202301"]],
                            baseline="202301"), c1.WRONG_UNIT),
            ("12a", fx.claim("c12a", "decomposition", "within_effect", Decimal("0.00"), "USD/kg", "FLAT", a_all,
                             baseline="202301"), C),
            ("12b", fx.claim("c12b", "decomposition", "mix_effect", Decimal("-2.40"), "USD/kg", "DOWN", a_all,
                             baseline="202301"), C),
            ("13", fx.claim("c13", "decomposition", "mix_effect", Decimal("-2.40"), "USD/kg", "DOWN",
                            [ev(cc["parent_comparison"]), ev(cc["parent_baseline"])], partner="DE",
                            baseline="202301"), c1.WRONG_VALUE),
            ("14", fx.claim("c14", "data_status", "observation_status@8504501010", "REQUEST_FAILED", None, "NA",
                            [ev(cc["hs10_status_comparison"])], partner="DE"), C),
        ]
        for number, claim, outcome in cases:
            with self.subTest(example=number):
                record = score(self.rows, claim)
                self.assertEqual(record["outcome"], outcome, record["note"])
        self.assertEqual(score(self.rows, cases[0][1])["expected_value"], Decimal("-40.0"))


class RulebookFieldExamplesTest(unittest.TestCase):
    """룰북 B3-1 예시 1~8(v2 값을 합성 행으로 재현)."""

    @classmethod
    def setUpClass(cls):
        cls.rows, cls.ids = fx.rulebook_snapshot()

    def unit_value_claim(self, **overrides) -> dict:
        fields = {"value": Decimal("20.34"), "unit": "USD/kg", "evidence": [self.rows.ev(self.ids["cn_2401"])]}
        fields.update(overrides)
        return fx.claim("c1", "value", "U", fields.pop("value"), fields.pop("unit"), "NA", fields.pop("evidence"),
                        **fields)

    def share_evidence(self, duplicates: str = "all_hs4_202401") -> list[str]:
        return [self.rows.ev(self.ids["cn_2401"])] + [self.rows.ev(r) for r in self.ids[duplicates]]

    def test_examples_1_to_8(self):
        ev = self.rows.ev
        cases = [
            ("1", self.unit_value_claim(), C),
            ("2", self.unit_value_claim(value=Decimal("20.43")), c1.WRONG_VALUE),
            ("3", self.unit_value_claim(unit="USD/톤"), c1.WRONG_UNIT),
            ("4", self.unit_value_claim(evidence=[]), c1.UNSUPPORTED),
            ("5", self.unit_value_claim(evidence=[ev(self.ids["cn_total"])]), c1.UNSUPPORTED),
            ("6", fx.claim("c6", "share", "s", Decimal("38.6"), "%", "NA", self.share_evidence()), C),
            ("7", self.unit_value_claim(partner="TH"), c1.WRONG_REFERENT),
            ("8", fx.claim("c8", "data_status", "observation_status", "NOT_COLLECTED", None, "NA", [],
                           partner="TH"), c1.UNSUPPORTED),
        ]
        for number, claim, outcome in cases:
            with self.subTest(example=number):
                record = score(self.rows, claim)
                self.assertEqual(record["outcome"], outcome, record["note"])
        first = score(self.rows, cases[0][1])
        self.assertEqual((first["expected_value"], first["tolerance"], first["evidence_ok"]),
                         (Decimal("20.34"), Decimal("0.01"), True))
        self.assertEqual(score(self.rows, cases[5][1])["expected_value"], Decimal("38.6"))
        eight = score(self.rows, cases[7][1])
        self.assertTrue(eight["referent_resolved"])  # 대상 오류가 아니다(계획과 먼저 대조했다)
        self.assertEqual(eight["expected_value"], "NOT_COLLECTED")

    def test_record_has_contract_keys_and_preserves_reported_token(self):
        record = score(self.rows, self.unit_value_claim(value=Decimal("20.30")))
        self.assertEqual(tuple(record), c1.RECORD_KEYS)
        self.assertEqual(record["source"], "claim")
        self.assertEqual(str(record["reported_value"]), "20.30")  # 끝자리 0을 보존한다
        self.assertIn('"reported_value": 20.30', c1.dumps_json(record))


class RulebookFieldBoundaryTest(unittest.TestCase):
    """룰북 B3-1 경계 사례 1~19."""

    @classmethod
    def setUpClass(cls):
        cls.rows, cls.ids = fx.rulebook_snapshot()

    def ev(self, *names: str) -> list[str]:
        out = []
        for name in names:
            value = self.ids[name]
            out += [self.rows.ev(r) for r in value] if isinstance(value, list) else [self.rows.ev(value)]
        return out

    def check(self, claim: dict, outcome: str) -> dict:
        record = score(self.rows, claim)
        self.assertEqual(record["outcome"], outcome, record["note"])
        return record

    def test_1_exact_half_rounds_half_up(self):
        base = {"partner": "US"}
        self.check(fx.claim("c", "value", "U", Decimal("20.35"), "USD/kg", "NA", self.ev("us_2401"), **base), C)
        wrong = self.check(fx.claim("c", "value", "U", Decimal("20.34"), "USD/kg", "NA", self.ev("us_2401"), **base),
                           c1.WRONG_VALUE)
        self.assertIn(c1.DIGITS_ONLY_MARK, wrong["note"])
        far = self.check(fx.claim("c", "value", "U", Decimal("20.33"), "USD/kg", "NA", self.ev("us_2401"), **base),
                         c1.WRONG_VALUE)
        self.assertNotIn(c1.DIGITS_ONLY_MARK, far["note"])

    def test_2_coarser_than_contract_compares_at_shown_digits(self):
        record = self.check(fx.claim("c", "change", "r_U", -39, "%", "DOWN", self.ev("jp_2401", "jp_2301"),
                                     partner="JP", baseline="202301"), C)
        self.assertEqual((record["expected_value"], record["tolerance"]), (-39, 1))

    def test_3_finer_than_contract_compares_at_contract_digits(self):
        self.check(fx.claim("c", "value", "U", Decimal("20.3412"), "USD/kg", "NA", self.ev("cn_2401")), C)

    def test_4_near_zero_accepts_flat_and_sign(self):
        for direction in ("FLAT", "UP"):
            self.check(fx.claim("c", "change", "r_U", Decimal("0.0"), "%", direction, self.ev("vn_2401", "vn_2301"),
                                partner="VN", baseline="202301"), C)
        self.check(fx.claim("c", "change", "r_U", Decimal("0.0"), "%", "DOWN", self.ev("vn_2401", "vn_2301"),
                            partner="VN", baseline="202301"), c1.WRONG_DIRECTION)

    def test_5_zero_baseline_has_no_change_rate_but_share_change_exists(self):
        self.check(fx.claim("c", "change", "r_U", Decimal("100.0"), "%", "UP", self.ev("kh_2401", "kh_2301"),
                            partner="KH", baseline="202301"), c1.WRONG_VALUE)
        self.check(fx.claim("c", "change", "r_U", None, "%", "NA", self.ev("kh_2401", "kh_2301"),
                            partner="KH", baseline="202301"), C)
        want = c1.expect_change(c1.Snapshot.from_json(self.rows.doc()), "d_s", "KH", "850450", "202401", "202301")
        self.assertEqual(want.value, Fraction(100, 56_680_573) * 100)  # 기준월 점유율 0에서 계산된다

    def test_6_zero_weight_unit_value_is_null(self):
        self.check(fx.claim("c", "value", "U", 96, "USD/kg", "NA", self.ev("de_2401"), partner="DE"), c1.WRONG_VALUE)
        self.check(fx.claim("c", "value", "U", None, "USD/kg", "NA", self.ev("de_2401"), partner="DE"), C)

    def test_7_child_sum_weight_differs_but_rounded_unit_value_matches(self):
        self.check(fx.claim("c", "value", "Q", 1_075_492, "kg", "NA", self.ev("cn_2401")), c1.WRONG_VALUE)
        self.check(fx.claim("c", "value", "Q", 1_075_490, "kg", "NA", self.ev("cn_2401")), C)
        self.check(fx.claim("c", "value", "U", Decimal("20.34"), "USD/kg", "NA", self.ev("cn_2401")), C)

    def test_8_unresolved_zero_month_is_not_zero(self):
        self.check(fx.claim("c", "value", "V", 0, "USD", "NA", self.ev("fr_2401"), partner="FR"), c1.WRONG_VALUE)

    def test_9_promoted_month_is_zero(self):
        self.check(fx.claim("c", "value", "V", 0, "USD", "NA", self.ev("fi_2301"), partner="FI", period="202301"), C)
        self.check(fx.claim("c", "change", "r_U", None, "%", "NA", self.ev("fi_2401", "fi_2301"), partner="FI",
                            baseline="202301"), C)
        record = self.check(fx.claim("c", "share_change", "d_s", Decimal("0.0"), "pp", "UP",
                                     self.ev("fi_2401", "fi_2301", "all_hs6_202401", "all_hs6_202301"),
                                     partner="FI", baseline="202301"), C)
        self.assertEqual(record["expected_value"], Decimal("0.0"))  # 1000/56,680,573 → 0.0018pp

    def test_10_explicit_zero_month(self):
        self.check(fx.claim("c", "value", "V", 0, "USD", "NA", self.ev("se_2401"), partner="SE"), C)

    def test_11_promotion_status_must_match(self):
        self.check(fx.claim("c", "data_status", "observation_status", "CONFIRMED_NO_TRADE", None, "NA",
                            self.ev("fr_2401"), partner="FR"), c1.WRONG_VALUE)
        self.check(fx.claim("c", "data_status", "observation_status", "UNRESOLVED_ZERO", None, "NA",
                            self.ev("fi_2301"), partner="FI", period="202301"), c1.WRONG_VALUE)
        self.check(fx.claim("c", "data_status", "observation_status", "UNRESOLVED_ZERO", None, "NA",
                            self.ev("fr_2401"), partner="FR"), C)

    def test_12_share_level_in_percent_but_change_in_pp(self):
        self.check(fx.claim("c", "share", "s", Decimal("38.6"), "%", "NA", self.ev("cn_2401", "all_hs4_202401")), C)
        evidence = self.ev("cn_2401", "cn_2301", "all_hs4_202401", "all_hs4_202301")
        self.check(fx.claim("c", "share_change", "d_s", Decimal("-1.4"), "%", "DOWN", evidence,
                            baseline="202301"), c1.WRONG_UNIT)

    def test_13_yoy_baseline_must_be_t_minus_12(self):
        self.check(fx.claim("c", "change", "r_U", Decimal("-38.7"), "%", "DOWN", self.ev("jp_2401", "jp_2301"),
                            partner="JP", baseline="202302"), c1.WRONG_REFERENT)
        self.check(fx.claim("c", "value", "U", Decimal("20.34"), "USD/kg", "NA", self.ev("cn_2401"),
                            baseline="202301"), c1.WRONG_REFERENT)

    def test_14_selected_country_denominator(self):
        selected = Decimal("99.9")  # CN ÷ (CN + JP)
        self.check(fx.claim("c", "share", "s", selected, "%", "NA", self.ev("cn_2401", "all_hs4_202401")),
                   c1.WRONG_VALUE)

    def test_15_baci_unit(self):
        self.check(fx.claim("c", "value", "U", Decimal("20.34"), "천USD/톤", "NA", self.ev("cn_2401")), c1.WRONG_UNIT)

    def test_16_evidence_from_other_snapshot(self):
        other = [f"ev:kcs_202201_202412_v1:observation:{self.ids['cn_2401']}"]
        self.check(fx.claim("c", "value", "U", Decimal("20.34"), "USD/kg", "NA", other), c1.UNSUPPORTED)

    def test_17_change_without_baseline_row(self):
        self.check(fx.claim("c", "change", "r_U", Decimal("-38.7"), "%", "DOWN", self.ev("jp_2401"),
                            partner="JP", baseline="202301"), c1.UNSUPPORTED)

    def test_18_either_duplicate_all_row_is_enough(self):
        for duplicates in ("all_hs4_202401", "all_hs6_202401"):
            self.check(fx.claim("c", "share", "s", Decimal("38.6"), "%", "NA", self.ev("cn_2401", duplicates)), C)
        mixed = self.ev("cn_2401") + self.ev("all_hs4_202401")[:3] + self.ev("all_hs6_202401")[3:]
        self.check(fx.claim("c", "share", "s", Decimal("38.6"), "%", "NA", mixed), C)
        missing_one = self.ev("cn_2401") + self.ev("all_hs4_202401")[:5]
        self.check(fx.claim("c", "share", "s", Decimal("38.6"), "%", "NA", missing_one), c1.UNSUPPORTED)

    def test_19_first_failure_wins_and_rest_go_to_note(self):
        record = self.check(fx.claim("c", "value", "U", Decimal("20.43"), "USD/톤", "NA", []), c1.WRONG_UNIT)
        self.assertIn("WRONG_VALUE", record["note"])
        self.assertIn("UNSUPPORTED", record["note"])
        self.assertFalse(record["evidence_ok"])


class EvidenceAndInterpretationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.ids = fx.rulebook_snapshot()
        cls.snap = c1.Snapshot.from_json(cls.rows.doc())

    def test_rowid_must_be_positive_integer_without_leading_zero(self):
        rowid = self.ids["cn_2401"]
        good, _ = c1.resolve_evidence([f"ev:kcs_202201_202412_v2:observation:{rowid}"], "kcs_202201_202412_v2",
                                      self.snap)
        self.assertEqual(good, {rowid})
        for bad in (f"0{rowid}", "0", "-1", "+1", "1.0", " 1", "999999"):
            with self.subTest(rowid=bad):
                cited, _ = c1.resolve_evidence([f"ev:kcs_202201_202412_v2:observation:{bad}"],
                                               "kcs_202201_202412_v2", self.snap)
                self.assertIsNone(cited)

    def test_one_unresolvable_id_fails_the_evidence(self):
        ids = [self.rows.ev(self.ids["cn_2401"]), "ev:kcs_202201_202412_v2:observation"]
        record = score(self.rows, fx.claim("c", "value", "U", Decimal("20.34"), "USD/kg", "NA", ids))
        self.assertEqual(record["outcome"], c1.UNSUPPORTED)

    def test_export_row_does_not_support_import_claim(self):
        record = score(self.rows, fx.claim("c", "value", "V", 21_876_681, "USD", "NA",
                                           [self.rows.ev(self.ids["cn_export_2401"])]))
        self.assertEqual(record["outcome"], c1.UNSUPPORTED)

    def test_uninterpretable_claims_are_wrong_referent(self):
        good = fx.claim("c", "value", "U", Decimal("20.34"), "USD/kg", "NA", [self.rows.ev(self.ids["cn_2401"])])
        broken = [dict(good, claim_type="level"), dict(good, metric="unit_price"), dict(good, hs6="8504"),
                  dict(good, period="2024-01"), dict(good, value="20.34"), dict(good, value=True),
                  {k: v for k, v in good.items() if k != "text"}, "claim"]
        for claim in broken:
            with self.subTest(claim=str(claim)[:60]):
                record = c1.score_claim(claim, 3, self.snap, "run_case-260925100000", "report-1",
                                        "kcs_202201_202412_v2")
                self.assertEqual(record["outcome"], c1.WRONG_REFERENT)
                self.assertIn("해석 불가" if claim is not broken[0] else "해석 불가", record["note"])

    def test_level_claim_with_direction_is_wrong_direction(self):
        record = score(self.rows, fx.claim("c", "value", "U", Decimal("20.34"), "USD/kg", "UP",
                                           [self.rows.ev(self.ids["cn_2401"])]))
        self.assertEqual(record["outcome"], c1.WRONG_DIRECTION)

    def test_world_values_and_all_partner(self):
        self.assertEqual(c1.expect_level(self.snap, "V", "ALL", "850450", "202401").value, 56_680_573)
        record = score(self.rows, fx.claim("c", "share", "s", Decimal("100.0"), "%", "NA", [], partner="ALL"))
        self.assertEqual(record["outcome"], c1.WRONG_REFERENT)  # ALL의 점유율은 정의하지 않는다

    def test_dumps_json_keeps_decimal_tokens_and_refuses_float(self):
        self.assertEqual(c1.dumps_json({"a": Decimal("20.30"), "b": [1, None, True], "c": "한글"}),
                         '{"a": 20.30, "b": [1, null, true], "c": "한글"}')
        with self.assertRaises(ValueError):
            c1.dumps_json({"a": 0.5})
        with self.assertRaises(ValueError):
            c1.loads_json('{"a": NaN}')

    def test_run_scores_reports_in_order(self):
        report = fx.report("run_case-260925100000", [
            fx.claim("c1", "value", "U", Decimal("20.34"), "USD/kg", "NA", [self.rows.ev(self.ids["cn_2401"])]),
            fx.claim("c2", "value", "U", Decimal("20.43"), "USD/kg", "NA", [self.rows.ev(self.ids["cn_2401"])])])
        records = c1.run({"snapshot": self.rows.doc(), "reports": [report]})
        self.assertEqual([(r["claim_id"], r["outcome"]) for r in records], [("c1", C), ("c2", c1.WRONG_VALUE)])


if __name__ == "__main__":
    unittest.main()
