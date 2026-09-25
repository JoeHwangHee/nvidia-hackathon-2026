"""단위 I8(workflow_replay) 골든 쌍 밖 규칙 시험: 요청 불일치·기록 부족, 도구 재생, 가상 시계."""
import unittest

from tradesentry.runlog import trace
from tradesentry.workflow import replay

RID = "run_case-260925143015"


def rec(seq, event, stage, data):
    return {"seq": seq, "ts": "2026-09-25T14:30:15+09:00", "run_id": RID, "event": event, "stage": stage,
            "data": data}


class ReplayRuleTest(unittest.TestCase):
    def test_request_hash_mismatch_and_exhaustion_raise(self):
        payload = {"model": "m", "messages": [{"role": "user", "content": "a"}]}
        records = [rec(1, "model_request", "basic", {"request_sha256": trace.canonical_sha256(payload)}),
                   rec(2, "model_response", "basic", {"http_status": 200, "elapsed_ms": 5,
                                                      "usage": {"prompt_tokens": 1, "completion_tokens": 1,
                                                                "total_tokens": 2},
                                                      "response": {"message": {"role": "assistant", "content": "x"},
                                                                   "finish_reason": "stop"}})]
        transport = replay.ReplayTransport(records)
        with self.assertRaises(replay.ReplayMismatch):
            transport.send({"model": "m", "messages": [{"role": "user", "content": "b"}]}, 1000)
        transport = replay.ReplayTransport(records)
        self.assertEqual(transport.send(payload, 1000)["http_status"], 200)
        with self.assertRaises(replay.ReplayMismatch):
            transport.send(payload, 1000)

    def test_connection_error_replays_without_status(self):
        records = [rec(1, "model_request", "basic", {}),
                   rec(2, "model_error", "basic", {"http_status": None, "error": "connection", "elapsed_ms": 30})]
        sent = replay.ReplayTransport(records).send({"any": "payload"}, 1000)
        self.assertEqual((sent["http_status"], sent["error"], sent["body"]), (None, "connection", b""))

    def test_policy_denial_replays_with_status_and_denial_kind(self):
        records = [rec(1, "model_request", "basic", {}),
                   rec(2, "model_error", "basic", {"http_status": 403, "error": "policy_denied", "denial": "connect",
                                                   "elapsed_ms": 4})]
        sent = replay.ReplayTransport(records).send({"any": "payload"}, 1000)
        self.assertEqual((sent["http_status"], sent["error"], sent["denial"], sent["body"]),
                         (403, "policy_denied", "connect", b""))
        plain = replay.ReplayTransport([rec(1, "model_error", "basic", {"http_status": None, "error": "connection"})])
        self.assertNotIn("denial", plain.send({}, 1000))  # 거부가 아닌 오류에는 denial 키가 없다

    def test_error_records_without_headers_replay_as_empty_headers_and_recorded_headers_come_back(self):
        # model-1.7 전 기록(headers 없음)은 {}로, 있는 기록은 그대로 돌려준다(Retry-After 대기는 재생 실행이 다시 계산)
        old = [rec(1, "model_request", "basic", {}),
               rec(2, "model_error", "basic", {"http_status": 503, "error": None, "elapsed_ms": 30, "retrying": True,
                                               "backoff_ms": 5000})]
        self.assertEqual(replay.ReplayTransport(old).send({}, 1000)["headers"], {})
        recorded = {"retry-after": "8", "x-request-id": "r-1"}
        new = [rec(1, "model_request", "basic", {}),
               rec(2, "model_error", "basic", {"http_status": 429, "error": None, "elapsed_ms": 30, "retrying": True,
                                               "backoff_ms": 8000, "retry_after_ms": 8000, "headers": recorded,
                                               "body_excerpt": "quota"})]
        sent = replay.ReplayTransport(new).send({}, 1000)
        self.assertEqual((sent["headers"], sent["body"]), (recorded, b""))
        self.assertNotIn("body_excerpt", sent)
        success = replay.ReplayTransport([rec(1, "model_response", "basic", {
            "http_status": 200, "elapsed_ms": 5, "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            "response": {"message": {"role": "assistant", "content": "x"}, "finish_reason": "stop"}})])
        self.assertEqual(success.send({}, 1000)["headers"], {})

    def test_tools_replay_in_order_and_check_name_and_args(self):
        envelope = {"tool": "get_history", "metrics": []}
        records = [rec(1, "tool_call", "basic", {"tool": "get_history", "args": {"period": "202401"}}),
                   rec(2, "tool_result", "basic", {"tool": "get_history", "envelope": envelope, "elapsed_ms": 7}),
                   rec(3, "budget_block", "revision", {"kind": "requery_limit", "tool": "compare_partners"})]
        clock = replay.ReplayClock()
        tools = replay.ReplayTools(records, clock)
        with self.assertRaises(replay.ReplayMismatch):
            replay.ReplayTools(records).call("get_history", {"period": "202402"})
        self.assertEqual(tools.call("get_history", {"period": "202401"}), envelope)
        self.assertEqual((tools.remaining, clock.now_ms()), (0, 7))
        with self.assertRaises(replay.ReplayMismatch):
            tools.call("compare_partners", {})

    def test_virtual_clock_moves_only_by_recorded_time_and_sleep(self):
        clock = replay.ReplayClock()
        clock.sleep_ms(1000)
        clock.advance(250)
        self.assertEqual(clock.now_ms(), 1250)
        self.assertEqual(trace.iso_kst(clock.wall()), "2026-09-25T00:00:01+09:00")
        with self.assertRaises(ValueError):
            clock.advance(-1)


if __name__ == "__main__":
    unittest.main()
