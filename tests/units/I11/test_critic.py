"""단위 I11(workflow_critic) 골든 쌍 밖 규칙 시험: 도구 없는 요청, 재조회 요청 거르기, 읽지 못한 답."""
import json
import unittest

from tradesentry.runlog import trace as trace_log
from tradesentry.workflow import critic
from tradesentry.workflow import model_client as mc

from ..I7.fakes import FakeClock, ScriptedTransport, ok_body

CASE = {"case_id": "B-residual", "signals": {"unit_value": "TRIGGERED", "share": "NOT_TRIGGERED"}}


def run_review(content, tool_calls=None, finish_reason="stop"):
    config = mc.load_model_config()
    clock = FakeClock()
    transport = ScriptedTransport([{"body": ok_body(content, tool_calls=tool_calls, finish_reason=finish_reason)}], clock)
    budget = mc.Budget(config.limits, clock.now, config.settings.end_reserve_ms)
    client = mc.ModelClient(config.settings, budget, transport, trace_log.NullSink(), clock.clock_ms, clock.sleep_ms)
    return critic.review(client, config.prompts, CASE, {"review_status": "MAINTAIN"}, [], 2), transport


class CriticRuleTest(unittest.TestCase):
    def test_request_has_no_tools_and_tool_calls_are_not_run(self):
        calls = [{"id": "t", "type": "function", "function": {"name": "get_history", "arguments": "{}"}}]
        result, transport = run_review('{"findings": [], "requery": [], "needs_revision": false}', calls)
        payload = transport.payloads[0]
        self.assertNotIn("tools", payload)
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(len(payload["messages"]), 2)  # 조사자 대화와 섞지 않은 새 문맥
        self.assertEqual(result["requery"], [])
        self.assertIn("Critic이 도구를 부르려 했다(실행하지 않음)", result["problems"])

    def test_requery_requests_are_filtered_and_capped(self):
        answer = {"findings": [], "needs_revision": True, "requery": [
            {"tool": "verify_evidence", "args": {}, "reason": "예약된 도구"},
            {"tool": "compare_partners", "args": {"partners": ["VN"]}, "reason": "비교국"},
            {"tool": "get_history", "args": {"sql": "select 1"}, "reason": "인자 밖"},
            {"tool": "decompose_hs", "args": {}, "reason": "분해"},
            {"tool": "check_comparability", "args": {}, "reason": "세 번째"}]}
        result, _ = run_review(json.dumps(answer, ensure_ascii=False))
        self.assertEqual([(r["tool"], r["args"]) for r in result["requery"]],
                         [("compare_partners", {"partners": ["VN"]}), ("decompose_hs", {})])
        self.assertEqual(len(result["problems"]), 3)  # 버린 둘 + 개수 초과 하나

    def test_unreadable_answer_means_no_findings(self):
        result, _ = run_review("검토 결과: 문제 없음")
        self.assertEqual(result, {"findings": [], "requery": [], "needs_revision": False,
                                  "problems": ["Critic 답이 JSON 객체가 아니다"]})
        result, _ = run_review('{"findings": [{"kind": "missing_evidence", "text": "분해 없음"}]}')
        self.assertIs(result["needs_revision"], True)  # needs_revision이 없으면 지적이 있는지로 정한다

    def test_truncated_answer_is_noted_first(self):
        text = '{"findings": [], "requery": [], "needs_revision": false}'
        result, _ = run_review(text, finish_reason="length")
        self.assertEqual((result["problems"], result["needs_revision"]), ([critic.TRUNCATED], False))
        result, _ = run_review(text[:20], finish_reason="length")
        self.assertEqual(result["problems"], [critic.TRUNCATED, "Critic 답이 JSON 객체가 아니다"])

    def test_evidence_view_keeps_every_id_once_without_per_metric_lists(self):
        from tradesentry.workflow import investigator

        ids = [f"ev:controlled_fixture_v0:observation:{n}" for n in range(1, 6)]
        envelope = {"tool": "get_history", "scope": {"partners": ["CN", "ALL"]}, "evidence_ids": ids,
                    "metrics": [{"metric_id": "r_U-1", "inputs": {"metric": "r_U", "partner": "CN", "period": "202401",
                                                                  "baseline_period": "202301"},
                                 "evidence_ids": ids[:2], "value": None, "unit": "%", "comparability_flags": []},
                                {"metric_id": "d_s-1", "inputs": {"metric": "d_s", "partner": "CN", "period": "202401",
                                                                  "baseline_period": "202301"},
                                 "evidence_ids": ids[1:3], "value": None, "unit": "pp", "comparability_flags": []}],
                    "comparability": {"history": [{"month": "202401", "evidence_ids": [ids[3]]}]},
                    "missingness": [], "retryable_error": None}
        view = critic.evidence_view(envelope)
        self.assertEqual([m["metric_id"] for m in view["metrics"]], ["r_U-1", "d_s-1"])
        self.assertFalse(any("evidence_ids" in m for m in view["metrics"]))
        self.assertEqual(view["evidence_ids"], [ids[0], ids[1], ids[2], ids[4]])  # 지표 쪽 먼저, 중복 없음
        self.assertEqual(investigator._evidence_ids_in(view, set()), set(ids))  # 비교 가능성 안의 ID는 제자리에
        body = critic.messages(mc.load_model_config().prompts, CASE, {"review_status": "MAINTAIN"}, [envelope])
        self.assertIn(trace_log.dumps([view]), body[1]["content"])

    def test_messages_carry_no_mode(self):
        config = mc.load_model_config()
        case = dict(CASE, mode="full")  # 사례 객체에 모드가 섞여 와도 싣지 않는다
        body = critic.messages(config.prompts, case, {"review_status": "MAINTAIN"}, [])[1]["content"]
        for name in ("checklist", "agent", "full", "freeform"):
            self.assertNotIn(name, body)


if __name__ == "__main__":
    unittest.main()
