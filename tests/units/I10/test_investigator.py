"""단위 I10(workflow_investigator) 골든 쌍 밖 규칙 시험: 도구 호출 해석, 초안 형식 검사(허용 상태 조합은 막지 않는
관찰), 잘린 응답, 도구를 주지 않는 요청, 모드 사이 메시지가 claims 지침 말고는 같음(룰북 B2)."""
import json
import unittest
from decimal import Decimal

from tradesentry.runlog import trace as trace_log
from tradesentry.workflow import investigator as inv
from tradesentry.workflow import model_client as mc

from ..I7.fakes import FakeClock, ScriptedTransport, ok_body

CASE = {"case_id": "A-composition", "hs6": "850450", "partner": "CN", "month": "202401", "baseline_month": "202301",
        "signals": {"unit_value": "TRIGGERED", "share": "NOT_TRIGGERED"}, "snapshot_id": "controlled_fixture_v0",
        "policy_version": "dev-0.1"}

SIGNALS = {"unit_value": "TRIGGERED", "share": "NOT_TRIGGERED"}


def draft(**over):
    base = {"review_status": "MAINTAIN", "signal_status": {"unit_value": "MAINTAIN", "share": "NOT_TRIGGERED"},
            "claims": [{"claim_type": "change", "metric_id": "m-rU"}], "narrative": "설명", "hypotheses": []}
    base.update(over)
    return base


def freeform_claim(**over):
    claim = {"claim_id": "c1", "claim_type": "change", "hs6": "850450", "partner": "CN", "period": "202401",
             "baseline_period": "202301", "metric": "r_U", "value": Decimal("-40.0"), "unit": "%",
             "direction": "DOWN", "evidence_ids": ["ev:controlled_fixture_v0:observation:1024"],
             "text": "단가가 전년 같은 달보다 낮다."}
    claim.update(over)
    return claim


def client_with(script):
    config = mc.load_model_config()
    clock = FakeClock()
    transport = ScriptedTransport(script, clock)
    budget = mc.Budget(config.limits, clock.now, config.settings.end_reserve_ms)
    return mc.ModelClient(config.settings, budget, transport, trace_log.NullSink(), clock.clock_ms,
                          clock.sleep_ms), transport, config


class ToolCallTest(unittest.TestCase):
    def test_only_four_model_tools_with_narrow_arguments(self):
        names = [spec["function"]["name"] for spec in inv.tool_specs()]
        self.assertEqual(names, list(inv.MODEL_TOOLS))
        self.assertNotIn("verify_evidence", names)
        with self.assertRaises(ValueError):
            inv.tool_specs(["verify_evidence"])
        calls = inv.parse_tool_calls({"tool_calls": [
            {"id": "a", "function": {"name": "compare_partners", "arguments": '{"partners": ["VN", "JP"]}'}},
            {"id": "b", "function": {"name": "run_sql", "arguments": "{}"}},
            {"id": "c", "function": {"name": "get_history", "arguments": '{"path": "/etc/passwd"}'}},
            {"id": "d", "function": {"name": "compare_partners", "arguments": '{"partners": ["vn"]}'}},
            {"id": "e", "function": {"name": "decompose_hs", "arguments": "not json"}},
        ]})
        self.assertEqual([(c["tool"], c["error"]) for c in calls],
                         [("compare_partners", None), ("run_sql", "허용 밖 도구"), ("get_history", "허용 밖 인자"),
                          ("compare_partners", "partners는 2자리 국가코드 최대 5개다"),
                          ("decompose_hs", "인자가 JSON 객체가 아니다")])
        self.assertEqual(calls[0]["args"], {"partners": ["VN", "JP"]})
        self.assertEqual(calls[2]["args"], {})  # 거부한 호출의 인자는 버린다

    def test_step_without_tools_sends_no_tools_and_reads_tool_calls_anyway(self):
        tool_calls = [{"id": "x", "type": "function", "function": {"name": "get_history", "arguments": "{}"}}]
        client, transport, config = client_with([{"body": ok_body(None, tool_calls=tool_calls)}])
        messages = inv.initial_messages(config.prompts, {"case_id": "A", "signals": SIGNALS}, "agent", [], None, {})
        result = inv.step(client, messages, stage="basic", mode="agent", signals=SIGNALS, allow_tools=False)
        self.assertNotIn("tools", transport.payloads[0])
        self.assertEqual(result["kind"], "tool_calls")  # 흐름 조정(I12)이 이 시도를 막는다

    def test_mode_picks_the_claims_instruction(self):
        config = mc.load_model_config()
        self.assertIn(config.prompts["claims_freeform"].strip(), inv.system_prompt(config.prompts, "freeform"))
        self.assertIn(config.prompts["claims_template"].strip(), inv.system_prompt(config.prompts, "full"))
        self.assertNotIn(config.prompts["claims_freeform"].strip(), inv.system_prompt(config.prompts, "agent"))


class ModeParityTest(unittest.TestCase):
    """룰북 B2: freeform은 full과 처리(틀 채우기·검증기 차단)만 다르다. 조사자 메시지의 차이는 claims 지침뿐이다."""

    def messages(self, mode):
        config = mc.load_model_config()
        envelope = {"query_id": "q-gh", "tool": "get_history", "evidence_ids": ["ev:controlled_fixture_v0:observation:1"],
                    "metrics": [], "comparability": {}, "missingness": [], "retryable_error": None, "elapsed_ms": 5}
        return config, inv.initial_messages(config.prompts, CASE, mode, [envelope], ["weight_share_decomposition"],
                                            {"comparisons": 2, "model_requests": 9})

    def test_agent_and_full_messages_are_identical(self):
        self.assertEqual(self.messages("agent")[1], self.messages("full")[1])

    def test_full_and_freeform_differ_only_in_the_claims_instruction(self):
        config, full = self.messages("full")
        _, freeform = self.messages("freeform")
        self.assertEqual([m["role"] for m in full], [m["role"] for m in freeform])
        self.assertEqual(full[1:], freeform[1:])  # 사례·근거·남은 횟수 메시지가 같다
        template, free = config.prompts["claims_template"].rstrip(), config.prompts["claims_freeform"].rstrip()
        self.assertEqual(full[0]["content"].replace(template, free), freeform[0]["content"])
        self.assertNotEqual(full[0]["content"], freeform[0]["content"])

    def test_no_mode_name_reaches_the_model(self):
        for mode in ("agent", "full", "freeform"):
            _, messages = self.messages(mode)
            user = messages[1]["content"]
            with self.subTest(mode=mode):
                self.assertNotIn("[모드]", user)
                for name in inv.MODES:
                    self.assertNotIn(name, user)


class DraftCheckTest(unittest.TestCase):
    def test_valid_template_and_freeform_drafts_pass(self):
        self.assertEqual(inv.check_draft(draft(), "full", SIGNALS), [])
        self.assertEqual(inv.check_draft(draft(claims=[freeform_claim()]), "freeform", SIGNALS), [])
        data_status = {"claim_type": "data_status", "evidence_id": "ev:controlled_fixture_v0:observation:9"}
        self.assertEqual(inv.check_draft(draft(review_status="HOLD", signal_status={"unit_value": "HOLD",
                                                                                     "share": "NOT_TRIGGERED"},
                                               claims=[data_status]), "agent", SIGNALS), [])

    def test_problems_are_listed_not_fixed(self):
        cases = {
            "상태값 밖": draft(review_status="PRE_INVESTIGATION"),
            "신호별 판정 값 밖": draft(signal_status={"unit_value": "ESCALATE", "share": "NOT_TRIGGERED"}),
            "신호 키 없음": draft(signal_status={"unit_value": "MAINTAIN"}),
            "근거 없는 주장": draft(claims=[{"claim_type": "change"}]),
            "숫자를 직접 쓴 틀 모드 주장": draft(claims=[{"claim_type": "change", "metric_id": "m", "evidence_id": "ev:a"}]),
            "freeform 필드 없음": draft(claims=[{"claim_type": "change", "metric_id": "m"}]),
            "freeform 근거 ID 형식": draft(claims=[freeform_claim(evidence_ids=["row 12"])]),
            "freeform 방향": draft(claims=[freeform_claim(direction="DOWNWARD")]),
            "가설 형식": draft(hypotheses="가설"),
        }
        for name, bad in cases.items():
            mode = "freeform" if name.startswith("freeform") else "full"
            with self.subTest(name):
                self.assertNotEqual(inv.check_draft(bad, mode, SIGNALS), [])
        original = draft(review_status="MONITOR")
        before = json.dumps(original, sort_keys=True)
        inv.check_draft(original, "full", SIGNALS)
        self.assertEqual(json.dumps(original, sort_keys=True), before)

    def test_status_combinations_are_notes_not_problems(self):
        # 허용 상태 조합은 검증기 부류(R3 STATUS_INCONSISTENT)다. 모든 모드에서 형식 문제로 막지 않고 관찰만 남긴다
        cases = {
            "미발동 신호에 판정": draft(signal_status={"unit_value": "MAINTAIN", "share": "MONITOR"}),
            "발동 신호가 NOT_TRIGGERED": draft(review_status="HOLD",
                                           signal_status={"unit_value": "NOT_TRIGGERED", "share": "NOT_TRIGGERED"}),
            "집계와 다른 사례 판정": draft(review_status="MONITOR"),
        }
        for name, odd in cases.items():
            for mode in ("full", "freeform", "agent"):
                claims = [freeform_claim()] if mode == "freeform" else odd["claims"]
                with self.subTest(name, mode=mode):
                    self.assertEqual(inv.check_draft(dict(odd, claims=claims), mode, SIGNALS), [])
                    self.assertNotEqual(inv.status_notes(odd, SIGNALS), [])
        self.assertEqual(inv.status_notes(draft(), SIGNALS), [])
        self.assertEqual(inv.status_notes(draft(review_status="PRE_INVESTIGATION"), SIGNALS), [])

    def test_truncated_answer_is_a_draft_format_problem(self):
        body = json.dumps(draft(), ensure_ascii=False)
        for content in (body, body[:40]):
            client, _, _ = client_with([{"body": ok_body(content, finish_reason="length")}])
            result = inv.step(client, [{"role": "user", "content": "x"}], stage="basic", mode="full",
                              signals=SIGNALS, allow_tools=False)
            with self.subTest(complete_json=content == body):
                self.assertEqual((result["kind"], result["truncated"], result["problems"][0]),
                                 ("draft", True, inv.TRUNCATED))
        client, _, _ = client_with([{"body": ok_body(body)}])
        result = inv.step(client, [{"role": "user", "content": "x"}], stage="basic", mode="full", signals=SIGNALS,
                          allow_tools=False)
        self.assertEqual((result["problems"], result["truncated"], result["status_notes"]), ([], False, []))

    def test_parse_reads_fenced_json_keeps_decimal_text_and_rejects_prose(self):
        text = "```json\n" + trace_log.dumps(draft(claims=[freeform_claim(value=Decimal("20.30"))])) + "\n```"
        parsed, problems = inv.parse_draft(text, "freeform", SIGNALS)
        self.assertEqual(problems, [])
        self.assertEqual(str(parsed["claims"][0]["value"]), "20.30")
        self.assertEqual(inv.parse_draft("초안입니다: 검토 유지", "full", SIGNALS), (None, ["초안이 JSON 객체 하나가 아니다"]))
        parsed, problems = inv.parse_draft(json.dumps(dict(draft(), extra=1)), "full", SIGNALS)
        self.assertEqual((problems, "extra" in parsed), ([], False))


if __name__ == "__main__":
    unittest.main()
