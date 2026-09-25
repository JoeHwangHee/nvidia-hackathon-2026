"""독립 채점기 단위 C2(산문 채점) 시험: 룰북 docs/eval/RULEBOOK.md B3-2 예시 1~7과 경계 사례 1~22(손계산 예제).

예시의 보고서에는 합성 사례 A의 typed claim(U 기준월 6.0·비교월 3.6 USD/kg, r_U −40.0% DOWN, 점유율 기준월 10.0%·
비교월 6.0%, d_s −4.0pp DOWN)이 있다. 경계 사례는 사례마다 필요한 claim만 둔 보고서로 본다. 믿지 않는 보고서의 긴
공백·숫자열·많은 표현과 형식이 어긋난 값이 채점을 멈추거나 끝나지 않게 하지 않는지도 본다(보안 검토 1회차 반영).
"""
import time
import unittest
from decimal import Decimal
from fractions import Fraction

import scorer_fixtures as fx
from eval.scorer import claims as c1
from eval.scorer import prose as c2

C, U = c1.CORRECT, c1.UNBACKED_PROSE
HS_CODES = {"8504", "850450", "8504501010", "8504501020"}


def a_claims() -> list[dict]:
    base = {"hs6": "850450", "partner": "CN"}
    return [
        fx.claim("u0", "value", "U", Decimal("6.00"), "USD/kg", "NA", [], period="202301", **base),
        fx.claim("u1", "value", "U", Decimal("3.60"), "USD/kg", "NA", [], **base),
        fx.claim("ru", "change", "r_U", Decimal("-40.0"), "%", "DOWN", [], baseline="202301", **base),
        fx.claim("s0", "share", "s", Decimal("10.0"), "%", "NA", [], period="202301", **base),
        fx.claim("s1", "share", "s", Decimal("6.0"), "%", "NA", [], **base),
        fx.claim("ds", "share_change", "d_s", Decimal("-4.0"), "pp", "DOWN", [], baseline="202301", **base),
    ]


def one(metric: str, value: object, unit: str, direction: str = "NA", claim_type: str = "change",
        **extra) -> list[dict]:
    baseline = "202301" if claim_type in ("change", "share_change", "decomposition") else None
    return [fx.claim("k1", claim_type, metric, value, unit, direction, [], baseline=baseline, **extra)]


def prose(narrative: str = "", claims: list[dict] | None = None, hypotheses: list[str] | None = None,
          thresholds: list[int] | None = None) -> list[dict]:
    report = fx.report("run_case-260925100000", a_claims() if claims is None else claims, narrative=narrative,
                       hypotheses=hypotheses)
    for claim in report["claims"]:
        claim["text"] = ""
    return c2.score_report_prose(report, "run_case-260925100000", HS_CODES,
                                 [Fraction(t) for t in (thresholds or [])])


def outcomes(records: list[dict]) -> list[tuple[str, str]]:
    return [(r["reported_value"], r["outcome"]) for r in records]


class RulebookProseExamplesTest(unittest.TestCase):
    def test_example_1_all_backed(self):
        records = prose("단가가 kg당 6.0달러에서 3.6달러로 40% 떨어졌다.")
        self.assertEqual(outcomes(records), [("kg당 6.0달러", C), ("kg당 6.0달러에서 3.6달러로", C), ("3.6달러", C),
                                             ("40%", C), ("떨어졌", C)])
        self.assertEqual([r["claim_id"] for r in records], [f"prose:narrative:{n}" for n in range(1, 6)])
        self.assertEqual([r["unit_reported"] for r in records][:3], ["USD/kg", None, "USD"])
        self.assertEqual(records[0]["expected_value"], Decimal("6.00"))  # 뒷받침한 claim의 값
        self.assertIn("뒷받침 claim u0", records[0]["note"])

    def test_example_2_reversed_from_to(self):
        records = prose("점유율이 6%에서 10%로 늘었다.")
        self.assertEqual(outcomes(records), [("6%", C), ("6%에서 10%로", U), ("10%", C), ("늘었", U)])

    def test_example_3_percent_is_not_pp(self):
        self.assertEqual(outcomes(prose("점유율이 4% 줄었다.")), [("4%", U), ("줄었", C)])

    def test_example_4_rate_name_keeps_sign(self):
        self.assertEqual(outcomes(prose("단가 증가율은 △40.0%였다.")), [("△40.0%", C)])

    def test_examples_5_6_hypotheses(self):
        records = prose(hypotheses=["원자재 가격 상승이 원인일 수 있다.",
                                    "원자재 가격 변동이 영향을 주었는지는 이 자료로 확인할 수 없다."])
        self.assertEqual(outcomes(records), [("상승", U)])
        self.assertEqual(records[0]["claim_id"], "prose:hypotheses[0]:1")

    def test_example_7_dates_and_codes_excluded(self):
        self.assertEqual(prose("2024년 3월 HS 850450 중국산 수입을 조사했다."), [])


class RulebookProseBoundaryTest(unittest.TestCase):
    def test_1_approximate_word_ignores_trailing_zero(self):
        claims = one("r_U", Decimal("-38.7"), "%", "DOWN")
        self.assertEqual(outcomes(prose("약 40%", claims)), [("약 40%", C)])
        self.assertEqual(outcomes(prose("40%", claims)), [("40%", U)])

    def test_2_unsigned_inequality(self):
        self.assertEqual(outcomes(prose("30% 넘게 하락", one("r_U", Decimal("-40.0"), "%", "DOWN"))),
                         [("30% 넘게", C), ("하락", C)])

    def test_3_percent_range(self):
        self.assertEqual(outcomes(prose("40%대 하락", one("r_U", Decimal("-43.2"), "%", "DOWN"))),
                         [("40%대", C), ("하락", C)])
        self.assertEqual(outcomes(prose("40%대 하락", one("r_U", Decimal("-50.0"), "%", "DOWN")))[0], ("40%대", U))

    def test_4_n_times_increase_reads_ratio_n(self):
        self.assertEqual(outcomes(prose("2배 증가", one("r_U", Decimal("100.0"), "%", "UP"))),
                         [("2배", C), ("증가", C)])
        self.assertEqual(outcomes(prose("2배 증가", one("r_U", Decimal("200.0"), "%", "UP")))[0], ("2배", U))

    def test_5_ratio_rounds_at_shown_digit(self):
        self.assertEqual(outcomes(prose("2배", one("r_U", Decimal("98.7"), "%", "UP"))), [("2배", C)])
        self.assertEqual(outcomes(prose("두 배", one("r_U", Decimal("98.7"), "%", "UP"))), [("두 배", C)])

    def test_6_half(self):
        for value, outcome in (("-50.0", C), ("-47.0", C), ("-44.0", U)):
            with self.subTest(value=value):
                records = prose("절반으로 줄었다", one("r_U", Decimal(value), "%", "DOWN"))
                self.assertEqual(outcomes(records), [("절반", outcome), ("줄었", C)])

    def test_7_policy_threshold_is_excluded(self):
        records = prose("탐지 임계값 30%를 넘는 하락", one("r_U", Decimal("-40.0"), "%", "DOWN"), thresholds=[30, 10])
        self.assertEqual(outcomes(records), [("하락", C)])

    def test_8_negated_increase(self):
        self.assertEqual(outcomes(prose("증가하지 않았다", one("r_U", Decimal("-5.0"), "%", "DOWN"))), [("증가", C)])
        self.assertEqual(outcomes(prose("증가하지 않았다", one("r_U", Decimal("0.0"), "%", "FLAT"))), [("증가", C)])
        self.assertEqual(outcomes(prose("증가하지 않았다", one("r_U", Decimal("5.0"), "%", "UP"))), [("증가", U)])

    def test_9_false_positives_are_not_direction_words(self):
        text = ("결론을 내렸다. 판정을 내렸다. 영향을 줄 수 있다. 늘 같은 방식이다. 줄곧 그랬다. 오늘 확인했다. "
                "한 줄 요약이다. 오른쪽 표를 본다. 확대 해석하지 않는다.")
        self.assertEqual(prose(text), [])
        self.assertEqual(outcomes(prose("단가가 내렸다.")), [("내렸", C)])

    def test_10_decrease_rate_reverses_sign(self):
        self.assertEqual(outcomes(prose("하락률 40%", one("r_U", Decimal("-40.0"), "%", "DOWN"))), [("40%", C)])
        self.assertEqual(outcomes(prose("하락률 40%", one("r_U", Decimal("40.0"), "%", "UP"))), [("40%", U)])

    def test_11_to_13_money_and_weight_multipliers(self):
        v = one("V", 21_876_681, "USD", claim_type="value")
        q = one("Q", 1_075_490, "kg", claim_type="value")
        self.assertEqual(outcomes(prose("2,188만 달러", v)), [("2,188만 달러", C)])
        self.assertEqual(outcomes(prose("USD 21.9백만", v)), [("USD 21.9백만", C)])
        self.assertEqual(outcomes(prose("1,075톤", q)), [("1,075톤", C)])
        self.assertEqual(outcomes(prose("2,187만 달러", v)), [("2,187만 달러", U)])

    def test_14_baci_units_are_not_converted(self):
        records = prose("BACI 기준 123천USD/톤", one("U", Decimal("123.00"), "USD/kg", claim_type="value"))
        self.assertEqual(outcomes(records), [("123천USD/톤", U)])

    def test_15_counts_need_same_value_claim(self):
        records = prose("비교국 5개국 중 4개국에서 하락", one("r_U", Decimal("-40.0"), "%", "DOWN"))
        self.assertEqual(outcomes(records), [("5", U), ("4", U), ("하락", C)])
        # 한계(룰북 B3-2): 단위 없는 숫자는 값만 비교하므로 d_s −4.0 claim과 우연히 맞아 뒷받침된다
        self.assertEqual(outcomes(prose("4개국", a_claims())), [("4", C)])
        with_count = a_claims() + [fx.claim("n5", "comparison", "r_U", 5, "%", "UP", [], partner="JP",
                                            baseline="202301")]
        self.assertEqual(outcomes(prose("비교국 5개국 중", with_count)), [("5", C)])

    def test_16_consecutive_months_are_kept(self):
        self.assertEqual(outcomes(prose("3개월 연속 하락", a_claims())), [("3", U), ("하락", C)])

    def test_17_extremes_are_counted_not_scored(self):
        report = fx.report("run_case-260925100000", [], narrative="36개월 중 최저, 최소 금액 기준 아래 거래")
        self.assertEqual(prose("36개월 중 최저, 최소 금액 기준 아래 거래", []), [])
        self.assertEqual(c2.extreme_count(report), 2)

    def test_18_hs_and_chapter_notation(self):
        self.assertEqual(prose("8504.50-1010 품목, 제85류, HS85, HS22 기준 BACI", a_claims()), [])

    def test_19_status_label_is_not_direction(self):
        self.assertEqual(prose("검토 유지", a_claims()), [])

    def test_20_signed_versus_unsigned(self):
        claims = one("r_U", Decimal("-40.0"), "%", "DOWN")
        self.assertEqual(outcomes(prose("−40%", claims)), [("−40%", C)])
        self.assertEqual(outcomes(prose("△40%", claims)), [("△40%", C)])
        self.assertEqual(outcomes(prose("+40%", claims)), [("+40%", U)])
        self.assertEqual(outcomes(prose("40% 하락", claims)), [("40%", C), ("하락", C)])

    def test_21_pp_before_percent(self):
        self.assertEqual(outcomes(prose("△4.0%p", a_claims())), [("△4.0%p", C)])
        self.assertEqual(prose("△4.0%p", a_claims())[0]["unit_reported"], "pp")

    def test_dates_days_and_ordinals_are_excluded(self):
        self.assertEqual(prose("9월 25일과 3년간, 2주 동안, 제1안과 제2-1안", a_claims()), [])
        self.assertEqual(outcomes(prose("3일 연속 하락", a_claims())), [("3", U), ("하락", C)])

    def test_22_any_matching_claim_backs(self):
        claims = a_claims() + [fx.claim("dup", "comparison", "s", Decimal("6.0"), "%", "NA", [], partner="JP")]
        self.assertEqual(outcomes(prose("6.0%", claims)), [("6.0%", C)])

    # EX-2 확장(룰북 B3-2 경계 23~25, 사용자 결정 2026-09-26(토) 08:10 ②): 검증기와 같은 집합만 뺀다
    def test_23_hsk_and_digit_count_notation_excluded(self):
        self.assertEqual(prose("HSK 10단위 8504501010과 6자리 기준 850450을 대조했다", a_claims()), [])
        self.assertEqual(prose("HSK 8504.50-1010, HSK10, 10 자리 코드, 4자리 류", a_claims()), [])

    def test_24_electrical_rating_units_excluded(self):
        self.assertEqual(prose("16kVA 이하 변압기와 1kVA 초과 1.5MVA 미만 규격, 220 kV, 10kW, 500VA", a_claims()), [])
        # 규격 숫자를 빼도 같은 문장의 채점 대상은 그대로 잡는다
        self.assertEqual(outcomes(prose("16kVA 이하 변압기 단가가 40% 하락", a_claims())), [("40%", C), ("하락", C)])

    def test_25_similar_but_not_in_extension_set_are_scored(self):
        claims = one("r_U", Decimal("-40.0"), "%", "DOWN")
        # 홑 글자 전기 단위(V·A)·중량·개수·"자릿수"·단위 없는 숫자는 집합에 없어 PT-3·PT-5로 채점한다
        self.assertEqual(outcomes(prose("10 V와 5 A, 16kg, 10개국, 10자릿수, 16 이하", claims)),
                         [("10", U), ("5", U), ("16kg", U), ("10", U), ("10", U), ("16 이하", U)])
        # 단위 글자가 다른 낱말의 일부이면 빼지 않는다(kVAr·kWh)
        self.assertEqual(outcomes(prose("16kVAr, 10kWh", claims)), [("16", U), ("10", U)])


class ProseDetailsTest(unittest.TestCase):
    def test_claim_text_field_and_identifiers(self):
        report = fx.report("run_case-260925100000", a_claims(), narrative="claim ru와 policy_v1, RB-1, g0를 봤다.")
        report["claims"][2]["text"] = "단가가 40.0% 낮아졌다."
        records = c2.score_report_prose(report, "run_case-260925100000", HS_CODES, [])
        self.assertEqual([(r["claim_id"], r["reported_value"], r["outcome"]) for r in records],
                         [("prose:claims[2].text:1", "40.0%", C), ("prose:claims[2].text:2", "낮아졌", C)])
        self.assertEqual(tuple(records[0]), c1.RECORD_KEYS)
        self.assertEqual(records[0]["tolerance"], Decimal("0.1"))

    def test_korean_quality(self):
        report = fx.report("run_case-260925100000", [], narrative="모니터링 대상이다. `r_U` ev:x:observation:1 ok",
                           review_status="MONITOR", hypotheses=["위법 여부는 판정하지 않는다.", "우회수입이다."])
        quality = c2.korean_quality(report)
        self.assertEqual(quality["forbidden"], 1)  # "위법 여부"는 세지 않는다
        self.assertEqual(quality["missing"], 0)
        self.assertEqual(quality["latin"], 2)  # 백틱 안 식별자와 근거 ID는 뺀다("ok"만 센다)
        report.pop("created_at")
        report["narrative"] = "상태 표기 없음"
        self.assertEqual(c2.korean_quality(report)["missing"], 2)

    def test_pattern_list_fingerprint_is_stable(self):
        self.assertRegex(c2.pattern_list_sha256(), r"^[0-9a-f]{64}$")
        self.assertEqual(c2.pattern_list_sha256(), c2.pattern_list_sha256())


class UntrustedProseTest(unittest.TestCase):
    """믿지 않는 보고서가 산문 채점을 멈추거나 끝나지 않게 하지 않는다(보안 검토 1회차 막는 지적·권고 6)."""

    def timed(self, narrative: str, claims: list[dict] | None = None, limit: float = 3.0) -> list[dict]:
        started = time.monotonic()
        records = prose(narrative, claims)
        self.assertLess(time.monotonic() - started, limit)
        return records

    def test_long_whitespace_and_digit_runs_take_linear_time(self):
        n = c2.MAX_PROSE_CHARS
        texts = ("1" + " " * (n - 2) + "x", " " * (n - 1) + "1", "\n" * (n - 3) + "1. ", "1" * (n - 1) + "류",
                 "기준" + " " * (n - 10) + "30%", "가격이 내렸" * (n // 6), "1에서 2로 " * (n // 7),
                 "위법" * (n // 2))
        for text in texts:
            with self.subTest(text=repr(text[:8])):
                self.timed(text[:n])

    def test_many_expressions_against_many_claims(self):
        n = c2.MAX_PROSE_CHARS
        claims = [fx.claim(f"k{i}", "change", "r_U", Decimal(i) / 10, "%", "UP", [], baseline="202301")
                  for i in range(c1.MAX_CLAIMS_PER_REPORT)]
        for unit in ("1 ", "1%대 ", "1%이상 ", "두 배 ", "두 배 이상 "):
            with self.subTest(unit=unit):
                self.timed((unit * (n // len(unit)))[:n], claims)

    def test_indexed_backing_equals_claim_by_claim_check(self):
        claims = [c2._Claim(fx.claim(f"k{i}", ctype, metric, value, unit, "NA", [],
                                     baseline="202301" if ctype == "change" else None), i)
                  for i, (ctype, metric, value, unit) in enumerate([
                      ("value", "U", Decimal("6.00"), "USD/kg"), ("value", "V", 21_876_681, "USD"),
                      ("change", "r_U", Decimal("-40.0"), "%"), ("change", "r_U", Decimal("100.0"), "%"),
                      ("share", "s", Decimal("38.6"), "%"), ("value", "Q", 1_075_490, "kg"),
                      ("change", "r_U", Decimal("40.04"), "%"), ("value", "U", Decimal("6.04"), "USD/kg")])]
        backing = c2.Backing(claims)
        text = ("kg당 6.0달러, 6달러, 40%, △40.0%, 약 40%, 40%대, 30% 이상, 40% 미만, 두 배, 2배 이상, 38.6%, "
                "2,188만 달러, 1,075톤, 107만 5천kg, 0.5배")
        exprs = [e for e in c2.extract(text, set(), [], []) if e.kind in ("number", "multiple")]
        self.assertGreater(len(exprs), 10)
        for expr in exprs:
            with self.subTest(expr=expr.text):
                brute = [(c, exp) for c in backing.candidates(expr) for ok, exp in [c2._number_matches(expr, c)] if ok]
                first = backing.first(expr)
                self.assertEqual(first, brute[0] if brute else None)
                if expr.low is None and expr.op is None:
                    self.assertEqual(backing.numbers(expr), brute)

    def test_number_beyond_size_limit_is_unbacked(self):
        records = self.timed("1" * 300 + "%가 줄었다.", limit=1.0)
        self.assertEqual((records[0]["outcome"], records[1]["outcome"]), (U, C))
        self.assertIn("상한", records[0]["note"])

    def test_unhashable_claim_fields_and_status_do_not_raise(self):
        broken = dict(a_claims()[2], direction=[], metric={}, hs6=[], period=[1], unit=["%"])
        records = prose("단가가 증가했다. 6.0%에서 3.6%로 바뀌었다.", [broken])
        self.assertEqual([(r["reported_value"], r["outcome"]) for r in records],
                         [("증가", U), ("6.0%", U), ("6.0%에서 3.6%로", U), ("3.6%", U)])
        report = fx.report("run_case-260925100000", [broken], narrative="자료 보류", review_status="HOLD")
        report["review_status"] = []
        self.assertEqual(c2.korean_quality(report)["missing"], 1)

    def test_prose_and_claim_count_limits(self):
        with self.assertRaises(c1.ScorerInputError):
            prose("가" * (c2.MAX_PROSE_CHARS + 1))
        report = fx.report("run_case-260925100000", a_claims() * (c1.MAX_CLAIMS_PER_REPORT // 6 + 1))
        with self.assertRaises(c1.ScorerInputError):
            c2.score_report_prose(report, report["run_id"], HS_CODES, [])
        at_limit = fx.report("run_case-260925100000", [], hypotheses=[""] * c2.MAX_HYPOTHESES)
        self.assertEqual(c2.score_report_prose(at_limit, at_limit["run_id"], HS_CODES, []), [])
        over = fx.report("run_case-260925100000", [], hypotheses=[""] * (c2.MAX_HYPOTHESES + 1))  # 빈 항목도 센다
        with self.assertRaises(c1.ScorerInputError):
            c2.score_report_prose(over, over["run_id"], HS_CODES, [])


if __name__ == "__main__":
    unittest.main()
