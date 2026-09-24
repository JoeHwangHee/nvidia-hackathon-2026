"""단위 I7(workflow_model_client) 5xx 재전송 시험과 한도 규칙 시험(로드맵 MT4 완료 기준, 룰북 A2 `3e`).

- 요청당 재전송 상한(3회)과 지수 대기(1초·2초·4초)
- 재전송도 모델 요청 10회 한도에 센다(룰북 B2)
- 재전송 한도를 다 쓴 5xx는 FAILED와 모델 제공자 쪽 원인 분류 코드(인프라 실패 재실행 대상)로 남는다(룰북 B5)
- 재전송 중 모델 요청 10회에 먼저 닿으면 BUDGET_EXCEEDED로 끝나고 재실행 대상이 아니다(자료 계약 §3.3)
- 전체 deadline이 다른 한도보다 먼저다. 4xx·연결 실패·요청 제한 시간은 재전송하지 않는다
- 키는 전송 순간 환경변수에서만 읽고 trace·반환값·오류 문장에 없다
"""
import json
import os
import unittest
import urllib.error
from unittest import mock

from tradesentry.runlog import cause_codes
from tradesentry.runlog import trace as trace_log
from tradesentry.workflow import model_client as mc

from .fakes import FakeClock, ScriptedTransport, ok_body

MESSAGES = [{"role": "user", "content": "초안을 써라"}]
RID = "run_case-260925143015"


def make_client(script, *, used_requests=0, used_tokens=0, elapsed_before=0, elapsed_ms=700):
    config = mc.load_model_config()
    clock = FakeClock()
    budget = mc.Budget(config.limits, clock.now - elapsed_before, config.settings.end_reserve_ms)
    budget.model_requests = used_requests
    budget.tokens_in = used_tokens
    sink = trace_log.MemoryTrace(RID, clock=trace_log.now_kst)
    transport = ScriptedTransport(script, clock, elapsed_ms=elapsed_ms)
    client = mc.ModelClient(config.settings, budget, transport, sink, clock_ms=clock.clock_ms,
                            sleep_ms=clock.sleep_ms)
    return client, clock, transport, sink


def errors_of(stop, client, clock):
    return [cause_codes.error_entry(stop.code, stop.stage, mc.budget_counters(client.budget, clock.now), [])]


class RetransmitTest(unittest.TestCase):
    def test_5xx_is_resent_three_times_with_exponential_wait_then_fails_as_provider_error(self):
        client, clock, transport, sink = make_client([{"status": 500}, {"status": 502}, {"status": 503},
                                                      {"status": 504}])
        with self.assertRaises(mc.RunStop) as caught:
            client.chat(MESSAGES, stage="basic")
        stop = caught.exception
        self.assertEqual(stop.code, cause_codes.PROVIDER_HTTP_5XX)
        self.assertEqual(clock.sleeps, [1000, 2000, 4000])
        self.assertEqual(client.budget.model_requests, 4)  # 첫 요청 + 재전송 3회
        self.assertEqual(len(transport.payloads), 4)
        self.assertEqual(len({trace_log.canonical_sha256(p) for p in transport.payloads}), 1)  # 같은 요청 재전송
        errors = errors_of(stop, client, clock)
        self.assertEqual(cause_codes.execution_status(stop.code), "FAILED")
        self.assertTrue(cause_codes.infra_rerun_eligible("FAILED", errors))
        kinds = [(r["event"], r["data"].get("retrying")) for r in sink.records]
        self.assertEqual(kinds, [("model_request", None), ("model_error", True)] * 3
                         + [("model_request", None), ("model_error", False)])

    def test_resends_count_toward_the_model_request_limit_and_stop_as_budget_exceeded(self):
        client, clock, transport, sink = make_client([{"status": 503}, {"status": 503}], used_requests=8)
        with self.assertRaises(mc.RunStop) as caught:
            client.chat(MESSAGES, stage="revision")
        stop = caught.exception
        self.assertEqual(stop.code, cause_codes.BUDGET_MODEL_REQUESTS)
        self.assertEqual(client.budget.model_requests, 10)
        self.assertEqual(clock.sleeps, [1000])  # 10번째 뒤에는 기다리지 않고 멈춘다
        self.assertEqual(cause_codes.execution_status(stop.code), "BUDGET_EXCEEDED")
        self.assertFalse(cause_codes.infra_rerun_eligible("BUDGET_EXCEEDED", errors_of(stop, client, clock)))
        self.assertIs(sink.records[-1]["data"]["retrying"], False)

    def test_no_request_is_sent_when_the_model_request_limit_is_already_used(self):
        client, clock, transport, _ = make_client([], used_requests=10)
        with self.assertRaises(mc.RunStop) as caught:
            client.chat(MESSAGES, stage="critic")
        self.assertEqual(caught.exception.code, cause_codes.BUDGET_MODEL_REQUESTS)
        self.assertEqual(transport.payloads, [])

    def test_deadline_comes_before_other_limits(self):
        # 이미 300초를 넘겼고 모델 요청 한도도 찼다: deadline이 먼저다
        client, _, transport, _ = make_client([], used_requests=10, elapsed_before=300_000)
        with self.assertRaises(mc.RunStop) as caught:
            client.chat(MESSAGES, stage="basic")
        self.assertEqual(caught.exception.code, cause_codes.DEADLINE)
        self.assertEqual(transport.payloads, [])
        # 재전송 대기가 deadline을 넘으면 기다리지 않고 DEADLINE이다(재전송 여지가 남아 있어도)
        reserve = mc.load_model_config().settings.end_reserve_ms
        client, clock, _, _ = make_client([{"status": 503}], elapsed_before=300_000 - reserve - 900, elapsed_ms=0)
        with self.assertRaises(mc.RunStop) as caught:
            client.chat(MESSAGES, stage="basic")
        self.assertEqual((caught.exception.code, clock.sleeps), (cause_codes.DEADLINE, []))
        self.assertEqual(cause_codes.execution_status(cause_codes.DEADLINE), "TIMEOUT")

    def test_request_timeout_is_min_of_cap_and_remaining_time(self):
        config = mc.load_model_config()
        client, _, transport, _ = make_client([{"body": ok_body("{}")}], elapsed_before=270_000)
        client.chat(MESSAGES, stage="basic")
        self.assertEqual(transport.timeouts, [300_000 - 270_000 - config.settings.end_reserve_ms])
        client, _, transport, _ = make_client([{"body": ok_body("{}")}])
        client.chat(MESSAGES, stage="basic")
        self.assertEqual(transport.timeouts, [config.settings.request_cap_ms])

    def test_4xx_connection_and_timeout_are_not_resent(self):
        cases = [({"status": 429}, cause_codes.PROVIDER_HTTP_4XX),
                 ({"error": "connection"}, cause_codes.PROVIDER_CONNECTION),
                 ({"error": "timeout"}, cause_codes.PROVIDER_REQUEST_TIMEOUT),
                 ({"body": b"not json"}, cause_codes.PROVIDER_BAD_RESPONSE),
                 ({"body": json.dumps({"choices": [{"message": {"content": "x"}}]}).encode()},
                  cause_codes.PROVIDER_BAD_RESPONSE)]  # usage 없음
        for step, code in cases:
            with self.subTest(code=code, step=str(step)[:40]):
                client, clock, transport, _ = make_client([step])
                with self.assertRaises(mc.RunStop) as caught:
                    client.chat(MESSAGES, stage="basic")
                self.assertEqual(caught.exception.code, code)
                self.assertEqual((len(transport.payloads), clock.sleeps), (1, []))
        client, _, _, _ = make_client([{"error": "timeout", "elapsed_ms": 60_000}], elapsed_before=240_000)
        with self.assertRaises(mc.RunStop) as caught:
            client.chat(MESSAGES, stage="basic")
        self.assertEqual(caught.exception.code, cause_codes.DEADLINE)  # 제한 시간이 곧 deadline이었다

    def test_tokens_are_counted_and_the_limit_is_strict(self):
        client, _, transport, _ = make_client([{"body": ok_body("{}", prompt_tokens=31_000, completion_tokens=500)}],
                                              used_tokens=1_000)
        with self.assertRaises(mc.RunStop) as caught:
            client.chat(MESSAGES, stage="basic")
        self.assertEqual(caught.exception.code, cause_codes.BUDGET_TOKENS)
        self.assertEqual(transport.payloads[0]["max_tokens"], 2048)
        client, _, transport, _ = make_client([{"body": ok_body("{}")}], used_tokens=31_000)
        client.chat(MESSAGES, stage="basic")
        self.assertEqual(transport.payloads[0]["max_tokens"], 1000)  # 남은 토큰으로 줄인다
        client, _, transport, _ = make_client([], used_tokens=32_000)
        with self.assertRaises(mc.RunStop) as caught:
            client.chat(MESSAGES, stage="basic")
        self.assertEqual((caught.exception.code, transport.payloads), (cause_codes.BUDGET_TOKENS, []))

    def test_payload_shape_and_tool_calls_subset(self):
        calls = [{"id": "call_1", "type": "function", "index": 0,
                  "function": {"name": "compare_partners", "arguments": "{}"}}]
        client, _, transport, sink = make_client([{"body": ok_body(None, tool_calls=calls)}])
        tools = [{"type": "function", "function": {"name": "compare_partners", "description": "d",
                                                   "parameters": {"type": "object", "properties": {}}}}]
        answer = client.chat(MESSAGES, stage="basic", tools=tools)
        payload = transport.payloads[0]
        self.assertEqual((payload["tool_choice"], payload["stream"], payload["chat_template_kwargs"]),
                         ("auto", False, {"enable_thinking": False}))
        self.assertEqual(answer["message"]["tool_calls"],
                         [{"id": "call_1", "type": "function",
                           "function": {"name": "compare_partners", "arguments": "{}"}}])
        self.assertEqual(sink.records[-1]["data"]["response"]["message"], answer["message"])


class TransportKeyTest(unittest.TestCase):
    def test_key_is_read_at_send_time_and_never_reaches_trace(self):
        seen = {}

        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def read(self):
                return ok_body("{}")

        def fake_urlopen(request, timeout):
            seen["auth"] = request.get_header("Authorization")
            seen["timeout"] = timeout
            seen["body"] = request.data
            return Response()

        transport = mc.UrllibTransport("https://integrate.api.nvidia.com/v1/chat/completions", "TS_TEST_KEY_ENV")
        with mock.patch.dict(os.environ, {"TS_TEST_KEY_ENV": "placeholder-value-123"}), \
                mock.patch.object(mc.urllib.request, "urlopen", fake_urlopen):
            config = mc.load_model_config()
            budget = mc.Budget(config.limits, 0, config.settings.end_reserve_ms)
            sink = trace_log.MemoryTrace(RID, clock=trace_log.now_kst)
            clock = FakeClock(0)
            answer = mc.ModelClient(config.settings, budget, transport, sink, clock.clock_ms,
                                    clock.sleep_ms).chat(MESSAGES, stage="basic")
        self.assertEqual(seen["auth"], "Bearer placeholder-value-123")
        self.assertNotIn("placeholder-value-123", seen["body"].decode("utf-8"))
        self.assertEqual(seen["timeout"], 60)
        self.assertIn('"temperature": 1.0', seen["body"].decode("utf-8"))  # 요청 본문을 만들 때만 float
        everything = json.dumps([trace_log.dumps(r) for r in sink.records]) + json.dumps(str(answer))
        self.assertNotIn("placeholder-value-123", everything)
        self.assertNotIn("Bearer", everything)

    def test_missing_key_env_stops_as_code_error_without_counting_a_request(self):
        transport = mc.UrllibTransport("https://integrate.api.nvidia.com/v1/chat/completions", "TS_TEST_KEY_ENV")
        config = mc.load_model_config()
        budget = mc.Budget(config.limits, 0, config.settings.end_reserve_ms)
        clock = FakeClock(0)
        sink = trace_log.MemoryTrace(RID, clock=trace_log.now_kst)
        client = mc.ModelClient(config.settings, budget, transport, sink, clock.clock_ms, clock.sleep_ms)
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TS_TEST_KEY_ENV", None)
            with mock.patch.object(mc.urllib.request, "urlopen", side_effect=AssertionError("보내면 안 된다")):
                with self.assertRaises(mc.RunStop) as caught:
                    client.chat(MESSAGES, stage="basic")
        self.assertEqual((caught.exception.code, budget.model_requests), (cause_codes.CODE_ERROR, 0))
        self.assertEqual(sink.records, [])  # 보내지 않은 요청은 trace에도 없다(NAT LLM 구간 수 = 모델 요청 수)
        self.assertIn("TS_TEST_KEY_ENV", caught.exception.detail)

    def test_http_and_network_errors_map_to_transport_results(self):
        transport = mc.UrllibTransport("https://integrate.api.nvidia.com/v1/chat/completions", "TS_TEST_KEY_ENV")
        cases = [
            (urllib.error.HTTPError("u", 503, "busy", {}, None), (503, None)),
            (urllib.error.URLError(TimeoutError("t")), (None, "timeout")),
            (urllib.error.URLError(ConnectionRefusedError("r")), (None, "connection")),
            (TimeoutError("read"), (None, "timeout")),
            (ConnectionResetError("reset"), (None, "connection")),
        ]
        for exc, expected in cases:
            with self.subTest(exc=type(exc).__name__), mock.patch.dict(os.environ, {"TS_TEST_KEY_ENV": "p"}), \
                    mock.patch.object(mc.urllib.request, "urlopen", side_effect=exc):
                sent = transport.send({"model": "m"}, 1000)
                self.assertEqual((sent["http_status"], sent["error"]), expected)


class ConfigTest(unittest.TestCase):
    def test_load_default_config_and_override_key_env(self):
        config = mc.load_model_config(api_key_env="NVIDIA_INFERENCE_API_KEY")
        self.assertEqual(config.settings.api_key_env, "NVIDIA_INFERENCE_API_KEY")
        self.assertEqual(config.limits.model_requests, 10)
        self.assertEqual(set(config.prompts), set(mc.PROMPT_KEYS))
        with self.assertRaises(mc.ConfigError):
            mc.load_model_config(api_key_env="lower-case")
        with self.assertRaises(mc.ConfigError):
            mc.load_model_config(mc.DEFAULT_CONFIG_DIR / "없는 폴더")


if __name__ == "__main__":
    unittest.main()
