"""단위 I11(workflow_critic) 골든 쌍 밖 규칙 시험: 도구 없는 요청, 재조회 요청 거르기, 읽지 못한 답."""
import json
import unittest

from tradesentry.runlog import trace as trace_log
from tradesentry.workflow import critic
from tradesentry.workflow import model_client as mc

from ..I7.fakes import FakeClock, ScriptedTransport, ok_body

CASE = {"case_id": "B-residual", "signals": {"unit_value": "TRIGGERED", "share": "NOT_TRIGGERED"}}


def run_review(content, tool_calls=None):
    config = mc.load_model_config()
    clock = FakeClock()
    transport = ScriptedTransport([{"body": ok_body(content, tool_calls=tool_calls)}], clock)
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


if __name__ == "__main__":
    unittest.main()
