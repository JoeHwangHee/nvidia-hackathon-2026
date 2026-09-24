"""단위 I10 모델용 보기의 판정 보조 값(rule_view)과 필수 근거 보기 압축(AS2 3회차). 지표는 진짜 X3(decompose.run)로
만든다(합성 값, oracle A·B의 부모·하위 값). 네트워크·키 없이 돈다."""
import unittest
from decimal import Decimal

from tradesentry.metrics import decompose
from tradesentry.workflow import investigator, model_client

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


class StatusValueFormatTest(unittest.TestCase):
    """AS2 5회차: 초안 형식 줄과 초안 요청 메시지의 상태 값은 글자만 둔다(뜻 풀이를 붙이면 모델이 값에 옮겨 적는다)."""

    PLAIN = '"review_status": "MAINTAIN|MONITOR|HOLD"'

    def test_format_line_and_draft_request_carry_bare_values(self):
        self.assertIn(self.PLAIN, investigator.DRAFT_REQUEST)
        prompts = model_client.load_model_config().prompts
        self.assertIn(self.PLAIN, prompts["investigator"])
        for text in (investigator.DRAFT_REQUEST, prompts["investigator"].split("초안 형식", 1)[1]):
            self.assertNotIn("MAINTAIN(", text)
            self.assertNotIn("MONITOR(", text)


class ProsePatternListTest(unittest.TestCase):
    """AS2 9회차: 조사자 지침의 증감·무변동 어휘 목록이 검증기(R3) 산문 패턴 PT-6의 목록과 글자까지 같다(새로 짓지 않는다)."""

    def test_every_pt6_word_of_the_validator_is_in_the_prompt(self):
        from tradesentry.validator import validate
        prompt = model_client.load_model_config().prompts["investigator"]
        line = [ln for ln in prompt.splitlines() if "(PT-6)" in ln][0]
        missing = [w for w in validate.UP_WORDS + validate.DOWN_WORDS + validate.FLAT_WORDS if w not in line]
        self.assertEqual(missing, [])


class FeedbackAndUnavailableTextTest(unittest.TestCase):
    """AS2 10회차: 수정 지시의 막힌 산문 표현 나열, 참고값 계산 불가 안내(자료 부족 HOLD로 이끌지 않음)."""

    def test_blocked_prose_is_listed_with_path_and_text(self):
        findings = [{"check": "validator", "code": "PROSE_UNBACKED", "path": "narrative", "claim_id": None,
                     "detail": "PT-6 표현 '변동이 없': 같은 보고서의 typed claim으로 뒷받침되지 않는다(룰북 B3-2)"},
                    {"check": "validator", "code": "PROSE_UNBACKED", "path": "hypotheses[0]", "claim_id": None,
                     "detail": "PT-1 표현 '50.0%': 같은 보고서의 typed claim으로 뒷받침되지 않는다(룰북 B3-2)"},
                    {"check": "validator", "code": "NUMERIC_MISMATCH", "path": "claims[0].value", "claim_id": "c1",
                     "detail": "값이 다르다"}]
        content = investigator.feedback_message([], None, findings, {"requeries": 0, "model_requests": 3})["content"]
        self.assertIn("[검증기가 막은 산문 표현] narrative: '변동이 없'; hypotheses[0]: '50.0%'. 이 표현이 든 문장을 지우거나",
                      content)
        self.assertIsNone(investigator.prose_fix_line(findings[2:]))

    def test_unavailable_text_names_the_missing_lookup_and_is_not_a_hold_hint(self):
        text = investigator.reference_unavailable_text(["compare_partners"])
        self.assertIn("받지 못한 도구: compare_partners", text)
        self.assertIn("이것은 자료 부족이 아니다", text)
        self.assertNotIn("모자라면 HOLD", text)


if __name__ == "__main__":
    unittest.main()
