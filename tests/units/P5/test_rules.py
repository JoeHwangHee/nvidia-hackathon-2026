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
            p5.UNIT_VALUE: {"data_insufficient": "HOLD", "rounding_unstable": "HOLD",
                            "resolved_after_correction": "MONITOR", "composition_explained": "MONITOR",
                            "unexplained": "MAINTAIN"},
            p5.SHARE: {"data_insufficient": "HOLD", "resolved_after_correction": "MONITOR", "unexplained": "MAINTAIN"},
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
