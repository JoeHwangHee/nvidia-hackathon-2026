"""단위 I10(workflow_investigator) 골든 쌍 밖 규칙 시험: 도구 호출 해석, 초안 형식 검사(허용 상태 조합은 막지 않는
관찰), 잘린 응답, 도구를 주지 않는 요청(tools 없음, 초안 요청 메시지, 구조화 출력은 설정을 켰을 때만), 모드 사이
메시지가 claims 지침 말고는 같음(룰북 B2). off일 때의 동작은 설정을 주입해 본다."""
import dataclasses
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
        client.settings = dataclasses.replace(client.settings, structured_output="off")  # off일 때의 동작
        messages = inv.initial_messages(config.prompts, {"case_id": "A", "signals": SIGNALS}, "agent", [], None, {})
        result = inv.step(client, messages, stage="basic", mode="agent", signals=SIGNALS, allow_tools=False)
        payload = transport.payloads[0]
        self.assertEqual([k for k in ("tools", "tool_choice", "response_format", "nvext") if k in payload], [])
        self.assertEqual(result["kind"], "tool_calls")  # 흐름 조정(I12)이 이 시도를 막는다
        self.assertEqual(payload["messages"][-1], {"role": "user", "content": inv.DRAFT_REQUEST})
        self.assertEqual(messages[-1]["content"], inv.DRAFT_REQUEST)  # 대화에 남는다

    def test_draft_request_is_added_only_when_tools_are_withheld(self):
        client, transport, config = client_with([{"body": ok_body(json.dumps(draft()))}])
        messages = inv.initial_messages(config.prompts, CASE, "full", [], None, {"comparisons": 2})
        inv.step(client, messages, stage="basic", mode="full", signals=SIGNALS, allow_tools=True)
        payload = transport.payloads[0]
        self.assertEqual((payload["tool_choice"], len(payload["messages"])), ("auto", 2))
        self.assertNotIn(inv.DRAFT_REQUEST, [m["content"] for m in payload["messages"]])

    def test_structured_output_rides_only_on_the_draft_request_when_enabled(self):
        for structured in ("off", "json_object"):
            for allow in (True, False):
                client, transport, config = client_with([{"body": ok_body(json.dumps(draft()))}])
                client.settings = dataclasses.replace(client.settings, structured_output=structured)
                messages = inv.initial_messages(config.prompts, CASE, "full", [], None, {})
                inv.step(client, messages, stage="basic", mode="full", signals=SIGNALS, allow_tools=allow)
                payload = transport.payloads[0]
                with self.subTest(structured=structured, allow_tools=allow):
                    self.assertEqual("response_format" in payload, structured == "json_object" and not allow)
                    self.assertNotIn("nvext", payload)
                    if "response_format" in payload:
                        self.assertEqual(payload["response_format"], {"type": "json_object"})

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
                    self.assertNotIn(name, inv.DRAFT_REQUEST)

    def test_draft_request_and_response_format_are_the_same_in_every_mode(self):
        sent = {}
        for mode in ("agent", "full", "freeform"):
            claims = [freeform_claim()] if mode == "freeform" else None
            body = json.dumps(draft(**({"claims": claims} if claims else {})), default=str)
            client, transport, config = client_with([{"body": ok_body(body)}])
            client.settings = dataclasses.replace(client.settings, structured_output="json_object")
            _, messages = self.messages(mode)
            inv.step(client, messages, stage="basic", mode=mode, signals=SIGNALS, allow_tools=False)
            payload = transport.payloads[0]
            sent[mode] = (payload["messages"][-1], payload["response_format"], payload["messages"][1:])
        self.assertEqual(sent["agent"], sent["full"])
        self.assertEqual(sent["full"], sent["freeform"])  # 초안 요청·response_format·사용자 메시지 모두 같다(차이는 시스템 지침)
        self.assertEqual(sent["full"][:2], ({"role": "user", "content": inv.DRAFT_REQUEST}, {"type": "json_object"}))


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


class ModelViewTest(unittest.TestCase):
    """모델용 봉투 보기(모든 모드·Critic 공통): 필요한 필드만 남기고 근거 ID·metric_id는 하나도 잃지 않는다."""

    ENVELOPE = {
        "query_id": "decompose_hs-00000000000000aa", "tool": "decompose_hs",
        "scope": {"hs6": "850450", "partner": "CN", "month": "202401", "baseline_month": "202301",
                  "months": ["202301", "202401"], "partners": ["CN"], "hs10": ["8504501000"]},
        "snapshot_id": "controlled_fixture_v0", "source_kind": "controlled",
        "evidence_ids": ["ev:controlled_fixture_v0:observation:1", "ev:controlled_fixture_v0:observation:2",
                         "ev:controlled_fixture_v0:observation:3", "ev:controlled_fixture_v0:observation:9"],
        "metrics": [{"metric_id": "r_U@8504501000-01", "formula_version": "1",
                     "inputs": {"metric": "r_U@8504501000", "hs6": "850450", "partner": "CN", "period": "202401",
                                "baseline_period": "202301", "V_0": 100, "Q_0": 10, "V_1": 60, "Q_1": 10},
                     "evidence_ids": ["ev:controlled_fixture_v0:observation:1", "ev:controlled_fixture_v0:observation:2"],
                     "value": Decimal("-40.0"), "unit": "%", "comparability_flags": [], "tolerance": Decimal("1.5")}],
        "comparability": {"hs10": [{"month": "202401", "observation_status": "OBSERVED", "codes": ["8504501000"]}]},
        "missingness": [{"evidence_id": "ev:controlled_fixture_v0:observation:3", "request_id": "r3",
                         "partner_code": "CN", "hs_code": "8504502000", "month": "202301", "flow": "import",
                         "observation_status": "NOT_COLLECTED", "missing_hs10": ["8504502000"]}],
        "retryable_error": None, "elapsed_ms": 7}

    def test_view_keeps_what_the_model_needs_and_every_evidence_id(self):
        view = inv.compact_envelope(self.ENVELOPE)
        self.assertEqual(list(view), ["tool", "scope", "metrics", "comparability", "missingness", "evidence_ids"])
        self.assertEqual(view["scope"], {"partners": ["CN"], "hs10": ["8504501000"]})
        self.assertEqual(view["metrics"], [{"metric_id": "r_U@8504501000-01", "metric": "r_U@8504501000",
                                            "partner": "CN", "period": "202401", "baseline_period": "202301",
                                            "value": Decimal("-40.0"), "unit": "%",
                                            "evidence_ids": ["ev:controlled_fixture_v0:observation:1",
                                                             "ev:controlled_fixture_v0:observation:2"]}])
        missing = view["missingness"][0]
        self.assertNotIn("request_id", missing)
        self.assertNotIn("flow", missing)
        self.assertEqual(missing["missing_hs10"], ["8504502000"])  # 도구가 더한 키는 남는다
        self.assertEqual(view["evidence_ids"], ["ev:controlled_fixture_v0:observation:9"])  # 다른 곳에 없는 ID만
        self.assertEqual(inv._evidence_ids_in(view, set()), set(self.ENVELOPE["evidence_ids"]))
        failed = inv.compact_envelope(dict(self.ENVELOPE, retryable_error={"code": "invalid_args"}))
        self.assertEqual(failed["retryable_error"], {"code": "invalid_args"})


if __name__ == "__main__":
    unittest.main()
