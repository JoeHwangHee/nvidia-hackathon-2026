"""단위 P5(policy_required_evidence) 규칙 시험.

- 판정 근거(basis) → 신호 상태가 개발 플랜 docs/plan/DEV_PLAN.md §6.3 표와 같다.
- 단가 계열의 세 규칙(구성효과 설명·설명 안 됨·자료 부족)의 필수 근거가 개발용 합성 예시 eval/dev/oracle_ABC.json의
  A/B/C `required_evidence`와 같다(공개 규칙의 이름을 맞춘 확인. 런타임 코드는 이 파일을 읽지 않는다).
- claim 계열 규칙(claim_families)이 자료 계약 docs/rules/DATA_CONTRACT_V1.md §9.4와 같다.
"""
import json
import unittest
from decimal import Decimal
from pathlib import Path

from tradesentry.policy import required_evidence as p5

ROOT = Path(__file__).resolve().parents[3]
ORACLE = ROOT / "eval" / "dev" / "oracle_ABC.json"
CASE = {"hs6": "850450", "partner": "CN", "month": "202401", "baseline_month": "202301"}


def claim(**fields):
    base = {"claim_id": "c1", "claim_type": "change", "hs6": "850450", "partner": "CN", "period": "202401",
            "baseline_period": "202301", "metric": "r_U", "value": Decimal("-40.0"), "unit": "%",
            "direction": "DOWN", "evidence_ids": [], "text": "합성"}
    base.update(fields)
    return base


class RuleTableTest(unittest.TestCase):
    def test_basis_status_follows_dev_plan_6_3(self):
        expected = {
            p5.UNIT_VALUE: {"data_insufficient": "HOLD", "data_inconsistent": "HOLD", "comparison_incomplete": "HOLD",
                            "rounding_unstable": "HOLD", "resolved_after_correction": "MONITOR",
                            "composition_explained": "MONITOR", "unexplained": "MAINTAIN"},
            p5.SHARE: {"data_insufficient": "HOLD", "data_inconsistent": "HOLD", "comparison_incomplete": "HOLD",
                       "resolved_after_correction": "MONITOR", "unexplained": "MAINTAIN"},
        }
        for family, table in expected.items():
            with self.subTest(family=family):
                self.assertEqual({basis: status for basis, status, _ in p5.RULES[family]}, table)
                for basis, status in table.items():
                    self.assertEqual(p5.rule_status(family, basis), status)

    def test_share_has_no_composition_or_rounding_rule(self):
        with self.assertRaises(ValueError):
            p5.rule_status(p5.SHARE, p5.BASIS_COMPOSITION_EXPLAINED)
        with self.assertRaises(ValueError):
            p5.rule_status(p5.SHARE, p5.BASIS_ROUNDING_UNSTABLE)
        with self.assertRaises(ValueError):
            p5.rule_status(p5.UNIT_VALUE, p5.BASIS_NOT_TRIGGERED)

    def test_every_code_has_description_and_statuses_are_contract_values(self):
        used = {code for rules in p5.RULES.values() for _, _, evidence in rules for code in evidence}
        self.assertEqual(used, set(p5.EVIDENCE_DESCRIPTIONS))
        for rules in p5.RULES.values():
            for _, status, evidence in rules:
                self.assertIn(status, p5.REVIEW_STATUSES)
                self.assertEqual(len(evidence), len(set(evidence)))

    def test_required_comparisons_follow_rule_evidence(self):
        # 필수 비교 → 근거 코드: comparability → comparability_ok, partners → partner_comparison_done,
        # country_and_world → country_and_world_change_shown. 규칙표의 근거 코드에서 나온다
        self.assertEqual(p5.family_comparisons(p5.UNIT_VALUE), ("comparability", "partners"))
        self.assertEqual(p5.family_comparisons(p5.SHARE), ("comparability", "partners", "country_and_world"))
        self.assertEqual(p5.required_comparisons(p5.UNIT_VALUE, "unexplained"), ("comparability", "partners"))
        self.assertEqual(p5.required_comparisons(p5.UNIT_VALUE, "composition_explained"), ("comparability",))
        self.assertEqual(p5.required_comparisons(p5.SHARE, "unexplained"),
                         ("comparability", "partners", "country_and_world"))
        for family in p5.SIGNAL_CODES:
            for basis in ("data_insufficient", "data_inconsistent", "comparison_incomplete",
                          "resolved_after_correction"):
                self.assertEqual(p5.required_comparisons(family, basis), ())
        # 앞 단계에서 끝나는 판정 근거는 필수 근거에 비교 코드가 있어도 판정 전 비교 완료를 따지지 않는다(D17)
        self.assertEqual(p5.required_comparisons(p5.UNIT_VALUE, "rounding_unstable"), ())
        self.assertIn("comparability_ok", p5.rule_evidence(p5.SHARE, "data_inconsistent"))
        self.assertEqual(p5.GATED_BASES, ("composition_explained", "unexplained"))
        self.assertLessEqual(set(p5.COMPARISON_EVIDENCE.values()), set(p5.EVIDENCE_DESCRIPTIONS))
        self.assertEqual(p5.COMPARISON_STATES, ("done", "incomplete", "not_performed"))

    def test_comparison_incomplete_is_a_hold_with_hold_evidence(self):
        for family in p5.SIGNAL_CODES:
            self.assertEqual(p5.rule_evidence(family, "comparison_incomplete"),
                             p5.rule_evidence(family, "data_insufficient"))

    def test_inconsistent_hold_evidence_follows_user_decision_14(self):
        # 사용자 결정 14(2026-09-25(금) 08:47): 관측은 모두 있는데 성립하지 않는 보류의 필수 근거(순서 그대로).
        # 빠진 관측 보류(data_insufficient)는 지금 규칙 그대로다
        self.assertEqual(p5.rule_evidence(p5.UNIT_VALUE, "data_inconsistent"),
                         ("parent_child_match_V_and_Q", "comparability_ok", "no_zero_fill"))
        self.assertEqual(p5.rule_evidence(p5.SHARE, "data_inconsistent"),
                         ("country_and_world_change_shown", "comparability_ok", "no_zero_fill"))
        for family in p5.SIGNAL_CODES:
            self.assertEqual(p5.rule_evidence(family, "data_insufficient"),
                             ("missingness_listed", "failure_vs_not_collected_distinguished", "no_zero_fill"))

    def test_unit_value_rules_match_oracle_required_evidence(self):
        oracle = json.loads(ORACLE.read_text(encoding="utf-8"), parse_float=Decimal)
        by_case = {case["case_id"]: case["expected"]["required_evidence"] for case in oracle["cases"]}
        rules = {basis: list(evidence) for basis, _, evidence in p5.RULES[p5.UNIT_VALUE]}
        self.assertEqual(rules[p5.BASIS_COMPOSITION_EXPLAINED], by_case["A-composition"])
        self.assertEqual(rules[p5.BASIS_UNEXPLAINED], by_case["B-residual"])
        self.assertEqual(rules[p5.BASIS_DATA_INSUFFICIENT], by_case["C-missing-hs10"])


class RunTest(unittest.TestCase):
    def test_only_triggered_families(self):
        out = p5.run({"signals": {"unit_value": "NOT_TRIGGERED", "share": "TRIGGERED"}})
        self.assertEqual(list(out["families"]), ["share"])
        self.assertEqual(out["families"]["share"]["claim_metrics"], ["s", "d_s"])
        self.assertEqual(set(out["evidence_descriptions"]),
                         {c for r in out["families"]["share"]["rules"] for c in r["required_evidence"]})

    def test_rejects_bad_input(self):
        bad = [
            None,
            {},
            {"signals": {"unit_value": "NOT_TRIGGERED", "share": "NOT_TRIGGERED"}},
            {"signals": {"unit_value": "TRIGGERED"}},
            {"signals": {"unit_value": "TRIGGERED", "share": "TRIGGERED", "extra": "TRIGGERED"}},
            {"signals": {"unit_value": "MAINTAIN", "share": "NOT_TRIGGERED"}},
            {"signals": {"unit_value": "TRIGGERED", "share": "NOT_TRIGGERED"}, "extra": 1},
        ]
        for inp in bad:
            with self.subTest(inp=inp), self.assertRaises(ValueError):
                p5.run(inp)


class ClaimFamiliesTest(unittest.TestCase):
    def fam(self, **fields):
        return p5.claim_families(claim(**fields), CASE)

    def test_metric_families(self):
        uv, sh = frozenset({"unit_value"}), frozenset({"share"})
        self.assertEqual(self.fam(metric="r_U"), uv)
        self.assertEqual(self.fam(metric="U", claim_type="value", baseline_period=None), uv)
        for metric in ("within_effect", "mix_effect", "residual", "U@8504501000", "r_U@8504501000", "w@8504501000"):
            self.assertEqual(self.fam(metric=metric), uv, metric)
        self.assertEqual(self.fam(metric="s", claim_type="share"), sh)
        self.assertEqual(self.fam(metric="d_s", claim_type="share_change"), sh)

    def test_claims_that_count_for_no_family(self):
        empty = frozenset()
        self.assertEqual(self.fam(metric="V", claim_type="value"), empty)
        self.assertEqual(self.fam(metric="Q", claim_type="value"), empty)
        self.assertEqual(self.fam(metric="U@"), empty)
        self.assertEqual(self.fam(metric="within_effect@8504501000"), empty)
        self.assertEqual(self.fam(claim_type="comparison", partner="JP"), empty)
        self.assertEqual(self.fam(claim_type="comparison"), empty)
        self.assertEqual(self.fam(period="202312"), empty)
        self.assertEqual(self.fam(hs6="850431"), empty)
        self.assertEqual(self.fam(partner="JP"), empty)
        self.assertEqual(self.fam(partner="ALL", metric="d_s"), empty)

    def test_data_status_claims(self):
        def ds(**fields):
            return self.fam(claim_type="data_status", baseline_period=None, unit=None, direction="NA", **fields)

        self.assertEqual(ds(metric="observation_status@8504501000", value="REQUEST_FAILED"),
                         frozenset({"unit_value"}))
        self.assertEqual(ds(metric="observation_status", value="UNRESOLVED_ZERO"),
                         frozenset({"unit_value", "share"}))
        self.assertEqual(ds(metric="observation_status@8504501000", partner="ALL", value="NOT_COLLECTED"),
                         frozenset({"share"}))
        self.assertEqual(ds(metric="observation_status", partner="ALL", value="REQUEST_FAILED"),
                         frozenset({"share"}))
        self.assertEqual(ds(metric="observation_status", value="OBSERVED"), frozenset())
        self.assertEqual(ds(metric="observation_status", value="NOT_A_STATUS"), frozenset())
        self.assertEqual(ds(metric="observation_status", partner="JP", value="REQUEST_FAILED"), frozenset())
        self.assertEqual(ds(metric="r_U", value="REQUEST_FAILED"), frozenset())


if __name__ == "__main__":
    unittest.main()
