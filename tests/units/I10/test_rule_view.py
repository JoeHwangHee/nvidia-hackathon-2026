"""단위 I10 모델용 보기의 판정 보조 값(rule_view)과 필수 근거 보기 압축(AS2 3회차). 지표는 진짜 X3(decompose.run)로
만든다(합성 값, oracle A·B의 부모·하위 값). 네트워크·키 없이 돈다."""
import unittest
from decimal import Decimal

from tradesentry.metrics import decompose
from tradesentry.workflow import investigator

SNAP = "controlled_fixture_v0"


def row(month, code, amount, weight, n):
    return {"month": month, "hs_code": code, "partner_code": "XA", "flow": "import", "amount_usd": amount,
            "net_weight_kg": weight, "observation_status": "OBSERVED", "evidence_ids": [f"ev:{SNAP}:observation:{n}"]}


def envelope(children, extra_rows=()):
    parent = [row("202312", "850450", 600, 100, 1), row("202412", "850450", 360, 100, 2)]
    rows = [row(m, code, v, q, 10 + i) for i, (m, code, v, q) in enumerate(children)] + list(extra_rows)
    out = decompose.run({"snapshot_id": SNAP, "hs6": "850450", "partner": "XA", "period": "202412",
                         "baseline_period": "202312", "parent": parent, "children": rows,
                         "weight_rounding_kg": Decimal("0.5")})
    return {"tool": "decompose_hs", "metrics": out["metrics"], "comparability": {}, "missingness": [],
            "evidence_ids": [], "retryable_error": None}


A = [("202312", "8504501000", 500, 50), ("202312", "8504509000", 100, 50),
     ("202412", "8504501000", 200, 20), ("202412", "8504509000", 160, 80)]
B = [("202312", "8504501000", 500, 50), ("202312", "8504509000", 100, 50),
     ("202412", "8504501000", 300, 50), ("202412", "8504509000", 60, 50)]


class RuleViewTest(unittest.TestCase):
    def test_composition_case_shows_zero_ratios(self):
        view = investigator.compact_envelope(envelope(A))
        self.assertEqual(view["rule_view"], {"U0": Decimal("6.00"), "within_pct_of_U0": Decimal("0.00"),
                                             "residual_pct_of_U0": Decimal("0.00"),
                                             "within_plus_residual_pct_of_U0": Decimal("0.00"),
                                             "max_abs_child_r_U": Decimal("0.00")})

    def test_within_case_shows_the_ratio_to_compare_with_theta(self):
        rule = investigator.rule_view(envelope(B))
        self.assertEqual((rule["within_pct_of_U0"], rule["within_plus_residual_pct_of_U0"], rule["max_abs_child_r_U"]),
                         (Decimal("-40.00"), Decimal("-40.00"), Decimal("40.00")))

    def test_missing_children_give_nulls_and_other_tools_give_none(self):
        failed = dict(row("202412", "850450", None, None, 30), observation_status="REQUEST_FAILED")
        rule = investigator.rule_view(envelope(A[:2], [failed]))  # 비교월 하위자료 요청 실패(C형) → 분해 불가
        self.assertEqual(rule["U0"], Decimal("6.00"))
        self.assertIsNone(rule["within_pct_of_U0"])
        self.assertIsNone(rule["max_abs_child_r_U"])
        self.assertIsNone(investigator.rule_view({"tool": "get_history", "metrics": []}))
        self.assertIsNone(investigator.rule_view({"tool": "decompose_hs", "metrics": []}))


class CompactRequiredTest(unittest.TestCase):
    def test_rules_become_status_basis_to_codes(self):
        required = {"families": {"unit_value": {"claim_metrics": ["U"], "rules": [
            {"basis": "composition_explained", "status": "MONITOR", "required_evidence": ["a", "b"]},
            {"basis": "unexplained", "status": "MAINTAIN", "required_evidence": ["c"]}]}},
            "evidence_descriptions": {"a": "설명"}}
        self.assertEqual(investigator.compact_required(required),
                         {"unit_value": {"MONITOR/composition_explained": ["a", "b"], "MAINTAIN/unexplained": ["c"]}})
        other = {"families": {"unit_value": {"claim_metrics": ["U"]}}}
        self.assertIs(investigator.compact_required(other), other)


if __name__ == "__main__":
    unittest.main()
