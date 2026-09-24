"""단위 P3(policy_signal_decide) 규칙 시험.

판정 순서, 필수 비교 완료 규칙, 빠진 관측의 계열 배정, 신호 독립, "기준 안" 경계, 정확값(Fraction), 입력 오류를 본다.
근거 상태는 기본값이 없으므로 시험 입력은 늘 모든 키를 채운 블록에서 한 곳씩 바꾼다. 기대값은 개발 플랜
docs/plan/DEV_PLAN.md §6.3을 옮긴 표이고 구현을 다시 부르지 않는다(P5 규칙표와의 일치는 ConsistencyTest만 본다).
"""
import copy
import unittest
from decimal import Decimal
from fractions import Fraction

from tradesentry.policy import required_evidence as p5
from tradesentry.policy import signal_decide as p3

D = Decimal
POLICY = {"policy_version": "dev-0.1", "thresholds": {"unit_value": 30, "share": 10}}
CASE = {"case_id": "850450-CN-202401", "hs6": "850450", "partner": "CN", "month": "202401",
        "baseline_month": "202301", "signals": {"unit_value": "TRIGGERED", "share": "TRIGGERED"}}
UNIT_VALUE_OK = {"comparability_issues": [], "comparisons": {"comparability": "done", "partners": "done"},
                 "U_baseline": D("6.00"),
                 "decomposition": {"within_effect": D("0.00"), "mix_effect": D("-2.40"), "residual": D("0.00"),
                                   "parent_child_match": True},
                 "children": [{"hs10": "8504501010", "r_U": D("0.0")}, {"hs10": "8504501020", "r_U": D("0.0")}],
                 "rounding_unstable": False, "resolved_after_correction": False}
SHARE_OK = {"comparability_issues": [],
            "comparisons": {"comparability": "done", "partners": "done", "country_and_world": "done"},
            "resolved_after_correction": False}
UNSTABLE_CHILD = [{"hs10": "8504501010", "r_U": D("-40.0")}, {"hs10": "8504501020", "r_U": D("-40.0")}]


def evidence(unit_value=None, share=None, missingness=None):
    return {"missingness": copy.deepcopy(missingness or []),
            "unit_value": copy.deepcopy(UNIT_VALUE_OK if unit_value is None else unit_value),
            "share": copy.deepcopy(SHARE_OK if share is None else share)}


def decide(unit_value=None, share=None, missingness=None, signals=None, policy=POLICY):
    case = dict(CASE, signals=signals or CASE["signals"])
    return p3.run({"policy": policy, "case": case, "evidence": evidence(unit_value, share, missingness)})


def replaced(block, **changes):
    """블록을 복사해 최상위 키를 통째로 바꾼다."""
    out = copy.deepcopy(block)
    out.update(changes)
    return out


def uv(decomposition=None, comparisons=None, **changes):
    """UNIT_VALUE_OK를 복사해 decomposition·comparisons는 그 안의 값만 바꾸고, 나머지 키는 통째로 바꾼다."""
    block = replaced(UNIT_VALUE_OK, **changes)
    if decomposition:
        block["decomposition"].update(decomposition)
    if comparisons:
        block["comparisons"].update(comparisons)
    return block


def sh(comparisons=None, **changes):
    block = replaced(SHARE_OK, **changes)
    if comparisons:
        block["comparisons"].update(comparisons)
    return block


def miss(partner_code, hs_code, month, status):
    return {"partner_code": partner_code, "hs_code": hs_code, "month": month, "observation_status": status}


NULL_DECOMPOSITION = replaced(UNIT_VALUE_OK, decomposition=None)


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
        self.assertEqual(self.status(unit_value=uv(children=UNSTABLE_CHILD)), ("MAINTAIN", "unexplained"))
        block = uv(children=[{"hs10": "8504501010", "r_U": D("-30")}])
        self.assertEqual(self.status(unit_value=block), ("MAINTAIN", "unexplained"))

    def test_unusable_decomposition_is_hold_not_maintain(self):
        cases = {
            "null decomposition": NULL_DECOMPOSITION,
            "null effect": uv(decomposition={"within_effect": None}),
            "parent mismatch": uv(decomposition={"parent_child_match": False}),
            "no children": uv(children=[]),
            "null child": uv(children=[{"hs10": "8504501010", "r_U": None}]),
            "no baseline U": uv(U_baseline=None),
            "zero baseline U": uv(U_baseline=0),
        }
        for name, block in cases.items():
            with self.subTest(name=name):
                self.assertEqual(self.status(unit_value=block), ("HOLD", "data_insufficient"))
        out = decide(unit_value=NULL_DECOMPOSITION)
        self.assertEqual(out["gaps"]["unit_value"], [{"reason": "decomposition_unavailable"}])

    def test_missing_child_observation_is_hold(self):
        for status in ("REQUEST_FAILED", "NOT_COLLECTED", "UNRESOLVED_ZERO"):
            for hs_code in ("850450", "8504501010"):
                with self.subTest(status=status, hs_code=hs_code):
                    out = decide(missingness=[miss("CN", hs_code, "202301", status)])
                    self.assertEqual(out["signal_status"]["unit_value"], "HOLD")
                    self.assertEqual(out["gaps"]["unit_value"][0]["observation_status"], status)
                    self.assertEqual(out["gaps"]["unit_value"][0]["partner_code"], "CN")

    def test_comparability_issue_is_hold(self):
        self.assertEqual(self.status(unit_value=uv(comparability_issues=["hs_version_changed"])),
                         ("HOLD", "data_insufficient"))

    def test_rounding_unstable_is_hold_even_if_explained(self):
        self.assertEqual(self.status(unit_value=uv(rounding_unstable=True)), ("HOLD", "rounding_unstable"))

    def test_resolved_after_correction_is_monitor(self):
        block = uv(children=UNSTABLE_CHILD, resolved_after_correction=True)
        self.assertEqual(self.status(unit_value=block), ("MONITOR", "resolved_after_correction"))

    def test_data_gap_comes_before_other_rules(self):
        block = uv(rounding_unstable=True, resolved_after_correction=True, comparisons={"partners": "incomplete"})
        out = decide(unit_value=block, missingness=[miss("CN", "8504501010", "202401", "REQUEST_FAILED")])
        self.assertEqual(out["basis"]["unit_value"], "data_insufficient")


class RequiredComparisonTest(unittest.TestCase):
    """필수 비교가 끝났다(done)는 근거가 있을 때만 MAINTAIN·MONITOR를 낸다(개발 플랜 §6.3 4행과 표 아래)."""

    def test_unit_value_maintain_needs_comparability_and_partners(self):
        self.assertEqual(decide(unit_value=uv(children=UNSTABLE_CHILD))["signal_status"]["unit_value"], "MAINTAIN")
        for key in ("comparability", "partners"):
            with self.subTest(incomplete=key):
                out = decide(unit_value=uv(children=UNSTABLE_CHILD, comparisons={key: "incomplete"}))
                self.assertEqual(out["signal_status"]["unit_value"], "HOLD")
                self.assertEqual(out["basis"]["unit_value"], "comparison_incomplete")
                self.assertEqual(out["gaps"]["unit_value"], [{"reason": "comparison_incomplete", "comparison": key}])

    def test_unit_value_monitor_needs_comparability_only(self):
        out = decide(unit_value=uv(comparisons={"partners": "incomplete"}))
        self.assertEqual((out["signal_status"]["unit_value"], out["basis"]["unit_value"]),
                         ("MONITOR", "composition_explained"))
        out = decide(unit_value=uv(comparisons={"comparability": "incomplete"}))
        self.assertEqual((out["signal_status"]["unit_value"], out["basis"]["unit_value"]),
                         ("HOLD", "comparison_incomplete"))

    def test_share_maintain_needs_all_three_comparisons(self):
        self.assertEqual(decide()["signal_status"]["share"], "MAINTAIN")
        for key in ("comparability", "partners", "country_and_world"):
            with self.subTest(incomplete=key):
                out = decide(share=sh(comparisons={key: "incomplete"}))
                self.assertEqual((out["signal_status"]["share"], out["basis"]["share"]),
                                 ("HOLD", "comparison_incomplete"))
                self.assertEqual(out["gaps"]["share"], [{"reason": "comparison_incomplete", "comparison": key}])
        out = decide(share=sh(comparisons={"partners": "incomplete", "comparability": "incomplete"}))
        self.assertEqual([g["comparison"] for g in out["gaps"]["share"]], ["comparability", "partners"])

    def test_incomplete_comparison_is_distinct_from_missing_observation(self):
        out = decide(share=sh(comparisons={"partners": "incomplete"}))
        self.assertNotEqual(out["basis"]["share"], "data_insufficient")
        out = decide(share=sh(comparisons={"partners": "incomplete"}),
                     missingness=[miss("ALL", "8504501010", "202401", "REQUEST_FAILED")])
        self.assertEqual(out["basis"]["share"], "data_insufficient")


class ShareRuleTest(unittest.TestCase):
    def test_share_hold_and_monitor(self):
        self.assertEqual(decide(missingness=[miss("ALL", "8504501010", "202401", "REQUEST_FAILED")])
                         ["signal_status"]["share"], "HOLD")
        self.assertEqual(decide(share=sh(comparability_issues=["unit_changed"]))["signal_status"]["share"], "HOLD")
        self.assertEqual(decide(share=sh(resolved_after_correction=True))["basis"]["share"],
                         "resolved_after_correction")

    def test_share_has_no_rounding_flag(self):
        with self.assertRaises(ValueError):
            decide(share=sh(rounding_unstable=True))


class AttributionTest(unittest.TestCase):
    def test_ignored_missingness(self):
        ignored = [
            miss("JP", "850450", "202401", "NOT_COLLECTED"),            # 비교국
            miss("CN", "8504501010", "202312", "REQUEST_FAILED"),       # 비교월·기준월 밖
            miss("ALL", "8504311000", "202401", "UNRESOLVED_ZERO"),     # 사례 HS6 밖
            miss("ALL", "8504", "202401", "REQUEST_FAILED"),            # HS4 요청의 상태 행(중복 제거는 HS6 요청 행을 쓴다)
            miss("CN", "8504501010", "202401", "CONFIRMED_NO_TRADE"),   # 무거래 확정
            miss("ALL", "8504501010", "202401", "OBSERVED"),
        ]
        out = decide(missingness=ignored)
        self.assertEqual(out["signal_status"], {"unit_value": "MONITOR", "share": "MAINTAIN"})
        self.assertEqual(out["gaps"], {"unit_value": [], "share": []})

    def test_k3_entry_keys_are_accepted(self):
        entry = dict(miss("ALL", "8504501010", "202301", "NOT_COLLECTED"), evidence_id="ev:s:observation:7",
                     request_id="0123456789abcdef", flow="import")
        out = decide(missingness=[entry])
        self.assertEqual(out["gaps"]["share"], [{"reason": "missing_observation", "partner_code": "ALL",
                                                 "hs_code": "8504501010", "month": "202301",
                                                 "observation_status": "NOT_COLLECTED"}])

    def test_signals_are_decided_independently(self):
        out = decide(missingness=[miss("CN", "850450", "202401", "REQUEST_FAILED")])
        self.assertEqual(out["signal_status"], {"unit_value": "HOLD", "share": "MAINTAIN"})
        out = decide(missingness=[miss("ALL", "8504501010", "202301", "NOT_COLLECTED")])
        self.assertEqual(out["signal_status"], {"unit_value": "MONITOR", "share": "HOLD"})
        out = decide(share=sh(comparisons={"partners": "incomplete"}))
        self.assertEqual(out["signal_status"], {"unit_value": "MONITOR", "share": "HOLD"})

    def test_not_triggered_signal_needs_no_block(self):
        case = dict(CASE, signals={"unit_value": "NOT_TRIGGERED", "share": "TRIGGERED"})
        out = p3.run({"policy": POLICY, "case": case,
                      "evidence": {"missingness": [miss("CN", "850450", "202401", "REQUEST_FAILED")],
                                   "share": copy.deepcopy(SHARE_OK)}})
        self.assertEqual(out["signal_status"], {"unit_value": "NOT_TRIGGERED", "share": "MAINTAIN"})
        self.assertEqual((out["basis"]["unit_value"], out["gaps"]["unit_value"]), ("not_triggered", []))
        out = decide(signals={"unit_value": "NOT_TRIGGERED", "share": "TRIGGERED"}, unit_value={})
        self.assertEqual(out["signal_status"]["unit_value"], "NOT_TRIGGERED")


class ExactValueTest(unittest.TestCase):
    """근거 수는 반올림 전 정확값(int·Decimal·Fraction)이다. 셈은 분수로 한다."""

    def test_fraction_evidence_with_decimal_threshold(self):
        policy = {"policy_version": "p", "thresholds": {"unit_value": D("30.0"), "share": 10}}
        block = uv(U_baseline=Fraction(6), decomposition={"within_effect": Fraction(-179, 100),
                                                          "mix_effect": Fraction(-61, 100), "residual": Fraction(0)},
                   children=[{"hs10": "8504501010", "r_U": Fraction(-2996, 100)}])
        self.assertEqual(decide(unit_value=block, policy=policy)["signal_status"]["unit_value"], "MONITOR")

    def test_display_rounded_child_value_would_flip(self):
        # 정확값 −29.96%는 기준 안이다. 표시 자릿수로 반올림한 −30.0을 넘기면 기준 밖이 되어 판정이 뒤집힌다
        exact_child = uv(children=[{"hs10": "8504501010", "r_U": Fraction(-2996, 100)}])
        rounded_child = uv(children=[{"hs10": "8504501010", "r_U": D("-30.0")}])
        self.assertEqual(decide(unit_value=exact_child)["signal_status"]["unit_value"], "MONITOR")
        self.assertEqual(decide(unit_value=rounded_child)["signal_status"]["unit_value"], "MAINTAIN")


class ConsistencyTest(unittest.TestCase):
    def test_status_follows_p5_rules(self):
        variants = [dict(), dict(unit_value=uv(rounding_unstable=True)), dict(unit_value=NULL_DECOMPOSITION),
                    dict(unit_value=uv(resolved_after_correction=True), share=sh(resolved_after_correction=True)),
                    dict(unit_value=uv(children=UNSTABLE_CHILD)),
                    dict(unit_value=uv(children=UNSTABLE_CHILD, comparisons={"partners": "incomplete"})),
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


class MissingKeyTest(unittest.TestCase):
    """근거 상태의 키가 빠지면 HOLD나 MAINTAIN이 아니라 입력 오류다(배선 누락이 판정으로 새지 않게)."""

    def run_with(self, evidence_value, signals=None):
        return p3.run({"policy": POLICY, "case": dict(CASE, signals=signals or CASE["signals"]),
                       "evidence": evidence_value})

    def test_missing_top_level_keys(self):
        full = evidence()
        for key in ("missingness", "unit_value", "share"):
            with self.subTest(missing=key), self.assertRaises(ValueError):
                self.run_with({k: v for k, v in full.items() if k != key})

    def test_missing_block_keys(self):
        for family, block in (("unit_value", UNIT_VALUE_OK), ("share", SHARE_OK)):
            for key in block:
                with self.subTest(family=family, missing=key), self.assertRaises(ValueError):
                    self.run_with(dict(evidence(), **{family: {k: v for k, v in block.items() if k != key}}))

    def test_missing_comparison_keys(self):
        for family, block in (("unit_value", UNIT_VALUE_OK), ("share", SHARE_OK)):
            for key in block["comparisons"]:
                bad = copy.deepcopy(block)
                del bad["comparisons"][key]
                with self.subTest(family=family, missing=key), self.assertRaises(ValueError):
                    self.run_with(dict(evidence(), **{family: bad}))

    def test_bad_comparison_values(self):
        for value in ("not_done", True, None, "DONE"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                decide(share=sh(comparisons={"partners": value}))
        with self.assertRaises(ValueError):
            decide(unit_value=uv(comparisons={"country_and_world": "done"}))  # 단가 계열에 없는 비교

    def test_missingness_entry_uses_contract_field_names(self):
        with self.assertRaises(ValueError):
            decide(missingness=[{"partner": "ALL", "hs_code": "8504501010", "month": "202401",
                                 "observation_status": "REQUEST_FAILED"}])


class RejectTest(unittest.TestCase):
    def test_bad_values(self):
        bad_blocks = [
            uv(U_baseline=6.0),
            uv(decomposition={"within_effect": 0.0}),
            uv(children=[{"hs10": "8504501010", "r_U": 0.5}]),
            uv(children=[{"hs10": "", "r_U": D("0")}]),
            uv(children=[{"code": "8504501010", "r_U": D("0")}]),
            uv(children="8504501010"),
            uv(rounding_unstable="no"),
            uv(resolved_after_correction=None),
            uv(comparability_issues="hs_version_changed"),
            uv(comparability_issues=[""]),
            uv(extra=True),
            replaced(UNIT_VALUE_OK, decomposition={"within_effect": D("0"), "mix_effect": D("0"), "residual": D("0")}),
            uv(decomposition={"parent_child_match": "yes"}),
        ]
        for block in bad_blocks:
            with self.subTest(block=block), self.assertRaises(ValueError):
                decide(unit_value=block)
        with self.assertRaises(ValueError):
            decide(missingness=[miss("CN", "850450", "202401", "MISSING")])
        with self.assertRaises(ValueError):
            decide(missingness=[{"partner_code": "CN", "month": "202401", "observation_status": "REQUEST_FAILED"}])
        with self.assertRaises(ValueError):
            p3.run({"policy": POLICY, "case": CASE, "evidence": dict(evidence(), missingness={"partner_code": "CN"})})

    def test_bad_case_and_envelope(self):
        base = {"policy": POLICY, "case": CASE, "evidence": evidence()}
        bad = [None, {k: v for k, v in base.items() if k != "evidence"}, dict(base, extra=1),
               dict(base, evidence=dict(evidence(), peers=[])), dict(base, evidence=[]),
               dict(base, case=dict(CASE, baseline_month="202312")),
               dict(base, case=dict(CASE, partner="ALL")), dict(base, case=dict(CASE, case_id="")),
               dict(base, case=dict(CASE, signals={"unit_value": "TRIGGERED"})),
               dict(base, policy={"policy_version": "p", "thresholds": {"unit_value": 0.3, "share": 10}})]
        for inp in bad:
            with self.subTest(inp=inp), self.assertRaises(ValueError):
                p3.run(inp)


if __name__ == "__main__":
    unittest.main()
