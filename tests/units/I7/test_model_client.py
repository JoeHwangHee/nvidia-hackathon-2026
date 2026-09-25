"""단위 I7(workflow_model_client) 5xx 재전송 시험과 한도 규칙 시험(로드맵 MT4 완료 기준, 룰북 A2 `3e`).

- 요청당 재전송 상한(3회)과 지수 대기(5초·10초·20초, model-1.4). HTTP 429도 5xx와 같은 고리·같은 횟수로 재전송하고,
  한도를 다 쓴 429는 PROVIDER_HTTP_4XX(재실행 대상, 2026-09-25 15:52 사용자 결정)
- 모델 요청 10회 한도는 재전송을 빼고 센다(요청 하나의 첫 전송만, model-1.5, 2026-09-25 18:05 사용자 결정). 재전송이
  많아도 BUDGET_EXCEEDED가 되지 않고, 새 요청은 한도에서 멈춘다
- 재전송 한도를 다 쓴 5xx는 FAILED와 모델 제공자 쪽 원인 분류 코드(인프라 실패 재실행 대상)로 남는다(룰북 B5)
- 전체 deadline이 다른 한도보다 먼저다. 429 밖 4xx·연결 실패·요청 제한 시간은 재전송하지 않는다
- 키는 전송 순간 환경변수에서만 읽고 trace·반환값·오류 문장에 없다. 값의 글자가 틀리면 요청을 세기 전에 멈추고,
  리디렉션은 따라가지 않으며 Authorization은 리디렉션 요청에 옮겨 가지 않는다
- 정책 프록시 거부(CONNECT 403·407, L7 403 policy_denied)는 CODE_ERROR로 멈추고 재실행 대상이 아니다
- 설정은 엔드포인트 호스트와 키 환경변수 이름을 허용 목록으로만 받는다
- Retry-After 존중(model-1.7): 재전송 대기 = max(지수 대기, min(Retry-After, 60초)). 초 정수·HTTP-date·없음·깨진 값·상한·
  deadline·5xx 같은 규칙. trace model_error에 retry_after_ms·허용 목록 headers·가린 body_excerpt(2026-09-25 22:22 사용자 결정 ④)
- 도구 없는 요청에는 tools·tool_choice 키가 없다. 구조화 출력(response_format json_object)은 설정이 json_object이고,
  도구가 없고, 부르는 쪽이 청할 때만 실린다. guided_json은 설정 값으로 받지 않는다(결정 기록 ⑯)

전송 시험은 가짜 opener(연결 처리기 묶음)나 가짜 HTTPS 처리기를 넣어 돈다. 겹 보호로 소켓 연결도 막는다
(NoNetworkMixin).
"""
import dataclasses
import email.message
import email.utils
import io
import json
import os
import shutil
import tempfile
import unittest
import urllib.error
import urllib.request
import urllib.response
from pathlib import Path
from unittest import mock

from tradesentry.runlog import cause_codes
from tradesentry.runlog import trace as trace_log
from tradesentry.workflow import model_client as mc

from .fakes import FakeClock, NoNetworkMixin, ScriptedTransport, ok_body

ENDPOINT = "https://integrate.api.nvidia.com/v1/chat/completions"
PLACEHOLDER = "placeholder-value-123"

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


class RetransmitTest(NoNetworkMixin, unittest.TestCase):
    def test_5xx_is_resent_three_times_with_exponential_wait_then_fails_as_provider_error(self):
        client, clock, transport, sink = make_client([{"status": 500}, {"status": 502}, {"status": 503},
                                                      {"status": 504}])
        with self.assertRaises(mc.RunStop) as caught:
            client.chat(MESSAGES, stage="basic")
        stop = caught.exception
        self.assertEqual(stop.code, cause_codes.PROVIDER_HTTP_5XX)
        self.assertEqual(clock.sleeps, [5000, 10000, 20000])
        self.assertEqual(client.budget.model_requests, 1)  # 요청 하나(재전송 3회는 세지 않는다, 결정 1805)
        self.assertEqual(len(transport.payloads), 4)
        self.assertEqual(len({trace_log.canonical_sha256(p) for p in transport.payloads}), 1)  # 같은 요청 재전송
        errors = errors_of(stop, client, clock)
        self.assertEqual(cause_codes.execution_status(stop.code), "FAILED")
        self.assertTrue(cause_codes.infra_rerun_eligible("FAILED", errors))
        kinds = [(r["event"], r["data"].get("retrying")) for r in sink.records]
        self.assertEqual(kinds, [("model_request", None), ("model_error", True)] * 3
                         + [("model_request", None), ("model_error", False)])

    def test_429_is_resent_like_5xx_then_succeeds(self):
        client, clock, transport, sink = make_client([{"status": 429}, {"body": ok_body("{}")}])
        client.chat(MESSAGES, stage="basic")
        self.assertEqual((clock.sleeps, client.budget.model_requests, len(transport.payloads)), ([5000], 1, 2))
        errors = [r["data"] for r in sink.records if r["event"] == "model_error"]
        self.assertEqual([(e["http_status"], e["retrying"], e["backoff_ms"]) for e in errors], [(429, True, 5000)])

    def test_429_after_three_resends_stops_as_4xx_with_retry_count_and_is_a_rerun_target(self):
        client, clock, transport, sink = make_client([{"status": 429}] * 4)
        with self.assertRaises(mc.RunStop) as caught:
            client.chat(MESSAGES, stage="critic")
        stop = caught.exception
        self.assertEqual((stop.code, stop.stage, stop.detail), (cause_codes.PROVIDER_HTTP_4XX, "critic",
                                                                "HTTP 429(재전송 3회 뒤)"))
        self.assertEqual((clock.sleeps, client.budget.model_requests), ([5000, 10000, 20000], 1))
        errors = [cause_codes.error_entry(stop.code, stop.stage, mc.budget_counters(client.budget, clock.now), [],
                                          stop.detail)]
        self.assertEqual(cause_codes.execution_status(stop.code), "FAILED")
        self.assertTrue(cause_codes.infra_rerun_eligible("FAILED", errors))
        traced = [(r["data"]["retrying"], r["data"]["backoff_ms"]) for r in sink.records if r["event"] == "model_error"]
        self.assertEqual(traced, [(True, 5000), (True, 10000), (True, 20000), (False, 0)])

    def test_5xx_and_429_share_one_resend_count_and_the_last_status_names_the_code(self):
        for script, code, detail in (
                ([{"status": 500}, {"status": 429}, {"status": 503}, {"status": 429}], cause_codes.PROVIDER_HTTP_4XX,
                 "HTTP 429(재전송 3회 뒤)"),
                ([{"status": 429}, {"status": 502}, {"status": 429}, {"status": 500}], cause_codes.PROVIDER_HTTP_5XX,
                 "HTTP 500(재전송 3회 뒤)")):
            with self.subTest(last=script[-1]["status"]):
                client, clock, transport, _ = make_client(script)
                with self.assertRaises(mc.RunStop) as caught:
                    client.chat(MESSAGES, stage="basic")
                self.assertEqual((caught.exception.code, caught.exception.detail), (code, detail))
                self.assertEqual((clock.sleeps, len(transport.payloads)), ([5000, 10000, 20000], 4))
        client, clock, _, _ = make_client([{"status": 503}, {"status": 429}, {"body": ok_body("{}")}])
        client.chat(MESSAGES, stage="basic")
        self.assertEqual((clock.sleeps, client.budget.model_requests), ([5000, 10000], 1))

    def test_429_resend_respects_deadline_but_not_the_model_request_limit(self):
        reserve = mc.load_model_config().settings.end_reserve_ms
        client, clock, _, _ = make_client([{"status": 429}], elapsed_before=300_000 - reserve - 4_000, elapsed_ms=0)
        with self.assertRaises(mc.RunStop) as caught:
            client.chat(MESSAGES, stage="basic")
        self.assertEqual((caught.exception.code, clock.sleeps), (cause_codes.DEADLINE, []))
        # 한도의 마지막(10번째) 요청이어도 429 재전송은 한도에 막히지 않는다(결정 1805)
        client, clock, transport, _ = make_client([{"status": 429}, {"status": 429}, {"body": ok_body("{}")}],
                                                  used_requests=9)
        client.chat(MESSAGES, stage="revision")
        self.assertEqual((clock.sleeps, client.budget.model_requests, len(transport.payloads)),
                         ([5000, 10000], 10, 3))

    def test_resends_do_not_count_toward_the_model_request_limit(self):
        # 10번째 요청이 재전송 3회를 다 써도 BUDGET_EXCEEDED가 아니라 원래 원인 코드(재실행 대상)로 멈춘다
        for status, code in ((503, cause_codes.PROVIDER_HTTP_5XX), (429, cause_codes.PROVIDER_HTTP_4XX)):
            with self.subTest(status=status):
                client, clock, transport, sink = make_client([{"status": status}] * 4, used_requests=9)
                with self.assertRaises(mc.RunStop) as caught:
                    client.chat(MESSAGES, stage="revision")
                stop = caught.exception
                self.assertEqual((stop.code, stop.detail), (code, f"HTTP {status}(재전송 3회 뒤)"))
                self.assertEqual((client.budget.model_requests, len(transport.payloads)), (10, 4))
                self.assertEqual(clock.sleeps, [5000, 10000, 20000])
                self.assertEqual(cause_codes.execution_status(stop.code), "FAILED")
                errors = [cause_codes.error_entry(stop.code, stop.stage, mc.budget_counters(client.budget, clock.now),
                                                  [], stop.detail)]
                self.assertTrue(cause_codes.infra_rerun_eligible("FAILED", errors))
                # trace: 시도(attempt)는 1~4, 모델 요청 수는 네 시도 모두 10(재전송은 늘리지 않는다)
                sent = [r["data"] for r in sink.records if r["event"] == "model_request"]
                self.assertEqual([(d["attempt"], d["model_requests"], d["request_no"]) for d in sent],
                                 [(1, 10, 1), (2, 10, 1), (3, 10, 1), (4, 10, 1)])

    def test_resent_requests_leave_room_and_new_requests_still_stop_at_the_limit(self):
        # 재전송이 섞인 요청 뒤에도 모델 요청 수는 요청 수만큼이고, 새 요청은 한도(10회)에서 보내지 않고 멈춘다
        client, clock, transport, sink = make_client([{"status": 503}, {"body": ok_body("{}")},
                                                      {"status": 429}, {"status": 429}, {"body": ok_body("{}")}],
                                                     used_requests=8)
        client.chat(MESSAGES, stage="basic")
        client.chat(MESSAGES, stage="critic")
        self.assertEqual((client.budget.model_requests, len(transport.payloads)), (10, 5))
        with self.assertRaises(mc.RunStop) as caught:
            client.chat(MESSAGES, stage="revision")
        stop = caught.exception
        self.assertEqual((stop.code, len(transport.payloads)), (cause_codes.BUDGET_MODEL_REQUESTS, 5))
        self.assertEqual(cause_codes.execution_status(stop.code), "BUDGET_EXCEEDED")
        self.assertFalse(cause_codes.infra_rerun_eligible("BUDGET_EXCEEDED", errors_of(stop, client, clock)))
        sent = [(r["data"]["request_no"], r["data"]["attempt"], r["data"]["model_requests"])
                for r in sink.records if r["event"] == "model_request"]
        self.assertEqual(sent, [(1, 1, 9), (1, 2, 9), (2, 1, 10), (2, 2, 10), (2, 3, 10)])

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
        cases = [({"status": 400}, cause_codes.PROVIDER_HTTP_4XX),
                 ({"status": 403}, cause_codes.PROVIDER_HTTP_4XX),
                 ({"status": 404}, cause_codes.PROVIDER_HTTP_4XX),
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
        limit = mc.load_model_config().limits.tokens  # 설정 값(model-1.2부터 128,000, 사용자 결정 4)
        client, _, transport, _ = make_client([{"body": ok_body("{}", prompt_tokens=limit - 1_000,
                                                                 completion_tokens=500)}], used_tokens=1_000)
        with self.assertRaises(mc.RunStop) as caught:
            client.chat(MESSAGES, stage="basic")
        self.assertEqual(caught.exception.code, cause_codes.BUDGET_TOKENS)
        self.assertEqual(transport.payloads[0]["max_tokens"], mc.load_model_config().settings.max_tokens)  # 설정 값
        client, _, transport, _ = make_client([{"body": ok_body("{}")}], used_tokens=limit - 1_000)
        client.chat(MESSAGES, stage="basic")
        self.assertEqual(transport.payloads[0]["max_tokens"], 1000)  # 남은 토큰으로 줄인다
        client, _, transport, _ = make_client([], used_tokens=limit)
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


class FakeResponse:
    status = 200

    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self.body


class FakeOpener:
    """opener 대역: open(request, timeout)마다 정해 둔 결과(응답 본문 bytes 또는 낼 예외)를 차례로 쓴다."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.requests = []

    def open(self, request, timeout):
        self.requests.append({"auth": request.get_header("Authorization"), "timeout": timeout, "body": request.data,
                              "redirectable": dict(request.headers), "method": request.get_method()})
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return FakeResponse(outcome)


class FakeHTTPS(urllib.request.HTTPSHandler):
    """HTTPS 처리기 대역: 표준 opener 안에서 네트워크 없이 정해 둔 (상태, 헤더, 본문)을 돌려준다."""

    def __init__(self, *responses):
        super().__init__()
        self.responses = list(responses)
        self.seen = []

    def https_open(self, req):
        self.seen.append({"url": req.full_url, "authorization": req.get_header("Authorization")})
        status, headers, body = self.responses.pop(0)
        message = email.message.Message()
        for key, value in headers.items():
            message[key] = value
        response = urllib.response.addinfourl(io.BytesIO(body), message, req.full_url, status)
        response.msg = "Found" if 300 <= status < 400 else "OK"
        return response


def http_error(code, body=b""):
    return urllib.error.HTTPError(ENDPOINT, code, "err", email.message.Message(), io.BytesIO(body))


def client_for(transport):
    config = mc.load_model_config()
    budget = mc.Budget(config.limits, 0, config.settings.end_reserve_ms)
    sink = trace_log.MemoryTrace(RID, clock=trace_log.now_kst)
    clock = FakeClock(0)
    return mc.ModelClient(config.settings, budget, transport, sink, clock.clock_ms, clock.sleep_ms), budget, sink


class TransportKeyTest(NoNetworkMixin, unittest.TestCase):
    def test_key_is_read_at_send_time_and_never_reaches_trace(self):
        opener = FakeOpener(ok_body("{}"))
        transport = mc.UrllibTransport(ENDPOINT, "TS_TEST_KEY_ENV", opener=opener)
        with mock.patch.dict(os.environ, {"TS_TEST_KEY_ENV": PLACEHOLDER}):
            client, _, sink = client_for(transport)
            answer = client.chat(MESSAGES, stage="basic")
        seen = opener.requests[0]
        self.assertEqual((seen["auth"], seen["method"]), ("Bearer " + PLACEHOLDER, "POST"))
        self.assertNotIn("Authorization", seen["redirectable"])  # 리디렉션 요청에 옮겨 가지 않는 헤더로 실었다
        self.assertNotIn(PLACEHOLDER, seen["body"].decode("utf-8"))
        self.assertEqual(seen["timeout"], 60)
        self.assertIn('"temperature": 1.0', seen["body"].decode("utf-8"))  # 요청 본문을 만들 때만 float
        everything = json.dumps([trace_log.dumps(r) for r in sink.records]) + json.dumps(str(answer))
        self.assertNotIn(PLACEHOLDER, everything)
        self.assertNotIn("Bearer", everything)

    def test_missing_key_env_stops_as_code_error_without_counting_a_request(self):
        opener = FakeOpener()
        transport = mc.UrllibTransport(ENDPOINT, "TS_TEST_KEY_ENV", opener=opener)
        client, budget, sink = client_for(transport)
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TS_TEST_KEY_ENV", None)
            with self.assertRaises(mc.RunStop) as caught:
                client.chat(MESSAGES, stage="basic")
        self.assertEqual((caught.exception.code, budget.model_requests), (cause_codes.CODE_ERROR, 0))
        self.assertEqual((sink.records, opener.requests), ([], []))  # 보내지 않은 요청은 trace에도 없다
        self.assertIn("TS_TEST_KEY_ENV", caught.exception.detail)

    def test_key_value_with_header_breaking_characters_stops_before_counting_without_the_value(self):
        for bad in (PLACEHOLDER + "\r", PLACEHOLDER + "\u2019", "two words", PLACEHOLDER + "\n" + "X-Other: 1"):
            opener = FakeOpener()
            transport = mc.UrllibTransport(ENDPOINT, "TS_TEST_KEY_ENV", opener=opener)
            client, budget, sink = client_for(transport)
            with self.subTest(bad=repr(bad)), mock.patch.dict(os.environ, {"TS_TEST_KEY_ENV": bad}):
                with self.assertRaises(mc.RunStop) as caught:
                    client.chat(MESSAGES, stage="basic")
                stop = caught.exception
                self.assertEqual((stop.code, budget.model_requests, opener.requests, sink.records),
                                 (cause_codes.CODE_ERROR, 0, [], []))
                for text in (stop.detail, str(stop), repr(stop)):
                    self.assertNotIn(PLACEHOLDER, text)
                    self.assertNotIn("two words", text)
                self.assertIn("TS_TEST_KEY_ENV", stop.detail)
                self.assertIsNone(stop.__cause__)
                self.assertTrue(stop.__suppress_context__)
                with self.assertRaises(mc.TransportConfigError):
                    transport.send({"model": "m"}, 1000)  # 전송 자리를 바로 불러도 같다

    def test_value_errors_while_sending_are_replaced_without_the_original_message(self):
        leaked = ValueError("Invalid header value b'Bearer " + PLACEHOLDER + "'")
        for raised in (leaked, UnicodeEncodeError("latin-1", "Bearer " + PLACEHOLDER, 0, 1, "x")):
            transport = mc.UrllibTransport(ENDPOINT, "TS_TEST_KEY_ENV", opener=FakeOpener(raised))
            with self.subTest(type(raised).__name__), mock.patch.dict(os.environ, {"TS_TEST_KEY_ENV": PLACEHOLDER}):
                with self.assertRaises(mc.TransportConfigError) as caught:
                    transport.send({"model": "m"}, 1000)
                error = caught.exception
                self.assertNotIn(PLACEHOLDER, str(error) + repr(error))
                self.assertIsNone(error.__context__)  # 원래 예외(문장에 헤더 값)를 잇지 않는다
                self.assertIsNone(error.__cause__)

    def test_http_and_network_errors_map_to_transport_results(self):
        cases = [
            (http_error(503), (503, None)),
            (urllib.error.URLError(TimeoutError("t")), (None, "timeout")),
            (urllib.error.URLError(ConnectionRefusedError("r")), (None, "connection")),
            (urllib.error.URLError(OSError("Tunnel connection failed: 502 Bad Gateway")), (None, "connection")),
            (TimeoutError("read"), (None, "timeout")),
            (ConnectionResetError("reset"), (None, "connection")),
        ]
        for exc, expected in cases:
            transport = mc.UrllibTransport(ENDPOINT, "TS_TEST_KEY_ENV", opener=FakeOpener(exc))
            with self.subTest(exc=repr(exc)[:60]), mock.patch.dict(os.environ, {"TS_TEST_KEY_ENV": "p"}):
                sent = transport.send({"model": "m"}, 1000)
                self.assertEqual((sent["http_status"], sent["error"]), expected)
                self.assertNotIn("denial", sent)


class RedirectTest(NoNetworkMixin, unittest.TestCase):
    """리디렉션: 표준 urllib 처리 순서(오류 처리기 포함)를 가짜 HTTPS 처리기로 돈다. 프록시 환경변수는 쓰지 않는다."""

    LOCATION = {"Location": "https://collector.example.org/steal"}

    def test_redirect_is_not_followed_and_stops_as_bad_response(self):
        https = FakeHTTPS((302, self.LOCATION, b""), (200, {}, ok_body("{}")))
        opener = mc.build_opener(urllib.request.ProxyHandler({}), https)
        transport = mc.UrllibTransport(ENDPOINT, "TS_TEST_KEY_ENV", opener=opener)
        with mock.patch.dict(os.environ, {"TS_TEST_KEY_ENV": PLACEHOLDER}):
            sent = transport.send({"model": "m"}, 1000)
            self.assertEqual((sent["http_status"], sent["error"], len(https.seen)), (302, None, 1))
            self.assertEqual(https.seen[0]["url"], ENDPOINT)
            client, budget, sink = client_for(mc.UrllibTransport(ENDPOINT, "TS_TEST_KEY_ENV", opener=mc.build_opener(
                urllib.request.ProxyHandler({}), FakeHTTPS((307, self.LOCATION, b"")))))
            with self.assertRaises(mc.RunStop) as caught:
                client.chat(MESSAGES, stage="basic")
        self.assertEqual((caught.exception.code, budget.model_requests), (cause_codes.PROVIDER_BAD_RESPONSE, 1))
        self.assertEqual([r["event"] for r in sink.records], ["model_request", "model_error"])

    def test_authorization_does_not_move_to_a_redirected_request_even_with_a_following_opener(self):
        # 대조: 표준 opener(리디렉션을 따라감)로 바꿔 끼워도 두 번째 요청에는 Authorization이 없다(겹 보호)
        https = FakeHTTPS((302, self.LOCATION, b""), (200, {}, ok_body("{}")))
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), https)
        transport = mc.UrllibTransport(ENDPOINT, "TS_TEST_KEY_ENV", opener=opener)
        with mock.patch.dict(os.environ, {"TS_TEST_KEY_ENV": PLACEHOLDER}):
            sent = transport.send({"model": "m"}, 1000)
        self.assertEqual(sent["http_status"], 200)
        self.assertEqual([s["url"] for s in https.seen], [ENDPOINT, self.LOCATION["Location"]])
        self.assertEqual([s["authorization"] for s in https.seen], ["Bearer " + PLACEHOLDER, None])


class PolicyDenialTest(NoNetworkMixin, unittest.TestCase):
    """샌드박스 정책 프록시 거부(X1 artifacts/openshell/violation_tests.md V0a·V1·V2b의 CONNECT 403, V3의 L7 403)."""

    L7_BODY = json.dumps({"error": "policy_denied", "layer": "l7", "detail": "GET /v1/models not permitted by policy",
                          "binary": "/opt/app/bin/python3.12"}).encode("utf-8")

    def test_transport_marks_connect_and_l7_denials(self):
        cases = [
            (urllib.error.URLError(OSError("Tunnel connection failed: 403 Forbidden")), (403, "connect")),
            (urllib.error.URLError(OSError("Tunnel connection failed: 407 Proxy Authentication Required")),
             (407, "connect")),
            (http_error(403, self.L7_BODY), (403, "l7")),
        ]
        for exc, (status, denial) in cases:
            transport = mc.UrllibTransport(ENDPOINT, "TS_TEST_KEY_ENV", opener=FakeOpener(exc))
            with self.subTest(denial=denial, status=status), mock.patch.dict(os.environ, {"TS_TEST_KEY_ENV": "p"}):
                sent = transport.send({"model": "m"}, 1000)
                self.assertEqual((sent["http_status"], sent["error"], sent["denial"], sent["body"]),
                                 (status, "policy_denied", denial, b""))  # 프록시 본문(실행 파일 경로)은 싣지 않는다
        transport = mc.UrllibTransport(ENDPOINT, "TS_TEST_KEY_ENV", opener=FakeOpener(http_error(403, b'{"x": 1}')))
        with mock.patch.dict(os.environ, {"TS_TEST_KEY_ENV": "p"}):
            sent = transport.send({"model": "m"}, 1000)
        self.assertEqual((sent["http_status"], sent["error"]), (403, None))  # 제공자 쪽 403은 그대로 4xx

    def test_denial_stops_as_code_error_that_is_not_rerun_eligible(self):
        for denial in ("connect", "l7"):
            with self.subTest(denial=denial):
                client, clock, transport, sink = make_client([{"error": "policy_denied", "status": 403,
                                                               "denial": denial}])
                with self.assertRaises(mc.RunStop) as caught:
                    client.chat(MESSAGES, stage="basic")
                stop = caught.exception
                self.assertEqual((stop.code, len(transport.payloads), clock.sleeps), (cause_codes.CODE_ERROR, 1, []))
                self.assertIn(f"policy_denied({denial}) 403", stop.detail)
                errors = errors_of(stop, client, clock)
                self.assertFalse(cause_codes.infra_rerun_eligible(cause_codes.execution_status(stop.code), errors))
                last = sink.records[-1]
                self.assertEqual((last["event"], last["data"]["http_status"], last["data"]["error"],
                                  last["data"]["denial"], last["data"]["retrying"]),
                                 ("model_error", 403, "policy_denied", denial, False))
        # 비교: 제공자 쪽 연결 실패는 재실행 대상이다(원인 분류가 섞이지 않는다)
        client, clock, _, _ = make_client([{"error": "connection"}])
        with self.assertRaises(mc.RunStop) as caught:
            client.chat(MESSAGES, stage="basic")
        self.assertTrue(cause_codes.infra_rerun_eligible("FAILED", errors_of(caught.exception, client, clock)))


class ConfigTest(NoNetworkMixin, unittest.TestCase):
    def test_load_default_config_and_override_key_env(self):
        config = mc.load_model_config(api_key_env="NVIDIA_INFERENCE_API_KEY")
        self.assertEqual(config.settings.api_key_env, "NVIDIA_INFERENCE_API_KEY")
        self.assertEqual(config.limits.model_requests, 10)
        self.assertEqual(set(config.prompts), set(mc.PROMPT_KEYS))
        with self.assertRaises(mc.ConfigError):
            mc.load_model_config(api_key_env="lower-case")
        with self.assertRaises(mc.ConfigError):
            mc.load_model_config(mc.DEFAULT_CONFIG_DIR / "없는 폴더")

    def test_key_env_name_is_limited_to_the_allowlist(self):
        self.assertEqual(mc.ALLOWED_KEY_ENVS, {"NVIDIA_API_KEY", "NVIDIA_INFERENCE_API_KEY"})
        for name in ("DATA_GO_KR_SERVICE_KEY", "OPENCLAW_GATEWAY_TOKEN", "TS_TEST_KEY_ENV", "PATH"):
            with self.subTest(name=name), self.assertRaises(mc.ConfigError) as caught:
                mc.load_model_config(api_key_env=name)
            self.assertNotIn(name, str(caught.exception))  # 오류 문장에는 허용 이름만 적는다

    def test_endpoint_host_is_limited_to_the_allowlist(self):
        bad = ["https://collector.example.org/v1/chat/completions",
               "http://integrate.api.nvidia.com/v1/chat/completions",
               "https://integrate.api.nvidia.com.example.org/v1/chat/completions",
               "https://user:pw@integrate.api.nvidia.com/v1/chat/completions",
               "https://integrate.api.nvidia.com:8443/v1/chat/completions",
               "https://integrate.api.nvidia.com:bad/v1/chat/completions"]
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "model"
            shutil.copytree(mc.DEFAULT_CONFIG_DIR, folder)
            raw = json.loads((folder / "model.json").read_text(encoding="utf-8"))
            for endpoint in bad + ["https://integrate.api.nvidia.com:443/v1/chat/completions"]:
                (folder / "model.json").write_text(json.dumps(dict(raw, endpoint=endpoint)), encoding="utf-8")
                with self.subTest(endpoint=endpoint):
                    if endpoint in bad:
                        with self.assertRaises(mc.ConfigError):
                            mc.load_model_config(folder)
                    else:
                        self.assertEqual(mc.load_model_config(folder).settings.endpoint, endpoint)


class StructuredOutputTest(NoNetworkMixin, unittest.TestCase):
    TOOLS = [{"type": "function", "function": {"name": "get_history", "description": "d",
                                               "parameters": {"type": "object", "properties": {}}}}]
    EXTRA_KEYS = ("tools", "tool_choice", "response_format", "nvext")

    def payload(self, structured, *, tools=None, json_output=False):
        client, _, transport, _ = make_client([{"body": ok_body("{}")}])
        client.settings = dataclasses.replace(client.settings, structured_output=structured)
        client.chat(MESSAGES, stage="basic", tools=tools, json_output=json_output)
        return transport.payloads[0]

    def keys(self, payload):
        return [k for k in self.EXTRA_KEYS if k in payload]

    def test_off_sends_no_extra_keys_without_tools(self):
        for json_output in (False, True):
            with self.subTest(json_output=json_output):
                self.assertEqual(self.keys(self.payload("off", json_output=json_output)), [])

    def test_json_object_rides_only_on_requests_without_tools_that_ask_for_it(self):
        payload = self.payload("json_object", json_output=True)
        self.assertEqual((self.keys(payload), payload["response_format"]), (["response_format"], {"type": "json_object"}))
        with_tools = self.payload("json_object", tools=self.TOOLS, json_output=True)
        self.assertEqual(self.keys(with_tools), ["tools", "tool_choice"])
        not_asked = self.payload("json_object")  # 부르는 쪽이 청하지 않으면(예: Critic) 싣지 않는다
        self.assertEqual(self.keys(not_asked), [])

    def test_config_value_is_off_or_json_object_only(self):
        self.assertEqual(mc.STRUCTURED_OUTPUT_MODES, ("off", "json_object"))
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "model"
            shutil.copytree(mc.DEFAULT_CONFIG_DIR, folder)
            raw = json.loads((folder / "model.json").read_text(encoding="utf-8"))
            for value in mc.STRUCTURED_OUTPUT_MODES + ("guided_json", "json_schema", True, None):
                request = dict(raw["request"], structured_output=value)
                (folder / "model.json").write_text(json.dumps(dict(raw, request=request)), encoding="utf-8")
                with self.subTest(value=value):
                    if value in mc.STRUCTURED_OUTPUT_MODES:
                        self.assertEqual(mc.load_model_config(folder).settings.structured_output, value)
                    else:
                        with self.assertRaises(mc.ConfigError):
                            mc.load_model_config(folder)


class HeaderTransport(ScriptedTransport):
    """ScriptedTransport에 응답 헤더·본문 요지를 더한 대역. 결과 하나에 "headers"(dict)·"body_excerpt"가 있으면 그대로 싣는다.
    실제 전송 자리(UrllibTransport)가 HTTP 응답에서 허용 목록 헤더만 모아 주는 모양을 흉내 낸다."""

    def send(self, payload, timeout_ms):
        step = self.script[0]
        sent = super().send(payload, timeout_ms)
        if "headers" in step:
            sent["headers"] = step["headers"]
        if "body_excerpt" in step:
            sent["body_excerpt"] = step["body_excerpt"]
        return sent


SENT_EPOCH = 1_790_000_000  # 고정한 전송 시각(epoch 초). HTTP-date Retry-After는 이 시각 기준 남은 초로 푼다
RA_FIELDS = ("retry_after_ms", "headers", "body_excerpt")
KEY = mc.KEY_PREFIX + "abc"  # 짧은 가짜 키 표시(실제 키 모양의 긴 문자열은 쓰지 않는다). 가림만 확인한다
MASKED = mc.SECRET_MASK


def make_header_client(script, *, elapsed_before=0, elapsed_ms=700):
    config = mc.load_model_config()
    clock = FakeClock()
    budget = mc.Budget(config.limits, clock.now - elapsed_before, config.settings.end_reserve_ms)
    sink = trace_log.MemoryTrace(RID, clock=trace_log.now_kst)
    transport = HeaderTransport(script, clock, elapsed_ms=elapsed_ms)
    client = mc.ModelClient(config.settings, budget, transport, sink, clock_ms=clock.clock_ms,
                            sleep_ms=clock.sleep_ms, wall_s=lambda: SENT_EPOCH)
    return client, clock, transport, sink


def http_date(epoch_s):
    return email.utils.formatdate(epoch_s, usegmt=True)


def model_errors(sink):
    return [r["data"] for r in sink.records if r["event"] == "model_error"]


def transport_send(transport):
    with mock.patch.dict(os.environ, {"TS_TEST_KEY_ENV": "p"}):
        return transport.send({"model": "m"}, 1000)


class RetryAfterTest(NoNetworkMixin, unittest.TestCase):
    """Retry-After 존중과 헤더·본문 요지 기록(model-1.7, 2026-09-25 22:22 사용자 결정 ④). 대기 = max(지수 대기,
    min(Retry-After, 60초)). 재전송 횟수(3회)·한도 세기(첫 전송만)·deadline 규칙은 그대로다."""

    def test_seconds_larger_than_backoff_wins_and_smaller_keeps_backoff(self):
        client, clock, _, sink = make_header_client([{"status": 429, "headers": {"retry-after": "8"}},
                                                     {"status": 429, "headers": {"retry-after": "2"}},
                                                     {"body": ok_body("{}")}])
        client.chat(MESSAGES, stage="basic")
        self.assertEqual(clock.sleeps, [8000, 10000])  # 8초 > 5초 → 8초. 2초 < 10초 → 지수 대기 10초
        self.assertEqual([(e["retry_after_ms"], e["backoff_ms"], e["retrying"]) for e in model_errors(sink)],
                         [(8000, 8000, True), (2000, 10000, True)])
        self.assertEqual(client.budget.model_requests, 1)

    def test_http_date_is_resolved_against_the_send_time_and_past_dates_count_as_zero(self):
        future, past = http_date(SENT_EPOCH + 30), http_date(SENT_EPOCH - 90)
        client, clock, _, sink = make_header_client([{"status": 429, "headers": {"retry-after": future}},
                                                     {"status": 429, "headers": {"retry-after": past}},
                                                     {"body": ok_body("{}")}])
        client.chat(MESSAGES, stage="basic")
        self.assertEqual(clock.sleeps, [30000, 10000])
        self.assertEqual([e["retry_after_ms"] for e in model_errors(sink)], [30000, 0])

    def test_missing_or_broken_value_keeps_the_exponential_wait(self):
        scripts = ([{"status": 429}, {"body": ok_body("{}")}],  # 헤더 키 자체가 없는 전송 결과
                   [{"status": 429, "headers": {}}, {"body": ok_body("{}")}],
                   [{"status": 429, "headers": {"x-request-id": "req-1"}}, {"body": ok_body("{}")}],
                   [{"status": 429, "headers": {"retry-after": "soon"}}, {"body": ok_body("{}")}],
                   [{"status": 429, "headers": {"retry-after": "-3"}}, {"body": ok_body("{}")}],
                   [{"status": 429, "headers": {"retry-after": "1.5"}}, {"body": ok_body("{}")}])
        for script in scripts:
            with self.subTest(headers=script[0].get("headers")):
                client, clock, _, sink = make_header_client(script)
                client.chat(MESSAGES, stage="basic")
                error = model_errors(sink)[0]
                self.assertEqual((clock.sleeps, error["retry_after_ms"], error["backoff_ms"]), ([5000], None, 5000))
                self.assertEqual(error["headers"], script[0].get("headers") or {})
                self.assertIsNone(error["body_excerpt"])

    def test_cap_limits_the_wait_to_sixty_seconds_but_the_trace_keeps_the_parsed_value(self):
        self.assertEqual(mc.load_model_config().settings.retry_after_cap_ms, 60000)
        client, clock, _, sink = make_header_client([{"status": 429, "headers": {"retry-after": "120"}},
                                                     {"body": ok_body("{}")}])
        client.chat(MESSAGES, stage="basic")
        self.assertEqual(clock.sleeps, [60000])
        self.assertEqual([(e["retry_after_ms"], e["backoff_ms"]) for e in model_errors(sink)], [(120000, 60000)])

    def test_wait_beyond_the_deadline_stops_as_deadline_without_sleeping(self):
        reserve = mc.load_model_config().settings.end_reserve_ms
        # 남은 시간 50초: 지수 대기 5초는 들어가지만 Retry-After 55초(상한 60초 안)는 넘는다
        client, clock, _, sink = make_header_client([{"status": 429, "headers": {"retry-after": "55"}}],
                                                    elapsed_before=300_000 - reserve - 50_000, elapsed_ms=0)
        with self.assertRaises(mc.RunStop) as caught:
            client.chat(MESSAGES, stage="basic")
        self.assertEqual((caught.exception.code, clock.sleeps), (cause_codes.DEADLINE, []))
        self.assertEqual([(e["retrying"], e["backoff_ms"], e["retry_after_ms"]) for e in model_errors(sink)],
                         [(False, 0, 55000)])

    def test_5xx_follows_the_same_rule_and_the_resend_count_is_unchanged(self):
        client, clock, transport, sink = make_header_client([{"status": 503, "headers": {"retry-after": "7"}},
                                                             {"status": 500, "headers": {"retry-after": "1"}},
                                                             {"status": 502},
                                                             {"status": 503, "headers": {"retry-after": "9"}}])
        with self.assertRaises(mc.RunStop) as caught:
            client.chat(MESSAGES, stage="basic")
        self.assertEqual((caught.exception.code, caught.exception.detail),
                         (cause_codes.PROVIDER_HTTP_5XX, "HTTP 503(재전송 3회 뒤)"))
        self.assertEqual((clock.sleeps, len(transport.payloads), client.budget.model_requests),
                         ([7000, 10000, 20000], 4, 1))
        # 마지막(재전송하지 않는) 오류에도 세 필드가 남는다
        self.assertEqual([(e["retrying"], e["retry_after_ms"]) for e in model_errors(sink)],
                         [(True, 7000), (True, 1000), (True, None), (False, 9000)])

    def test_trace_carries_the_three_fields_with_the_masked_excerpt_and_other_events_keep_their_shape(self):
        headers = {"retry-after": "6", "x-ratelimit-remaining-requests": "0", "x-request-id": "req-9"}
        client, _, _, sink = make_header_client([{"status": 429, "headers": headers,
                                                  "body_excerpt": '{"error": "quota", "hint": "' + MASKED + '"}'},
                                                 {"body": ok_body("{}")}])
        client.chat(MESSAGES, stage="basic")
        error = model_errors(sink)[0]
        self.assertEqual({k: error[k] for k in RA_FIELDS},
                         {"retry_after_ms": 6000, "headers": headers,
                          "body_excerpt": '{"error": "quota", "hint": "' + MASKED + '"}'})
        for record in sink.records:
            if record["event"] != "model_error":
                self.assertFalse(set(RA_FIELDS) & set(record["data"]))
        # 재전송 고리 밖 오류(다른 4xx)의 model_error 모양은 바뀌지 않는다
        client, _, _, sink = make_header_client([{"status": 400, "headers": headers, "body_excerpt": "bad"}])
        with self.assertRaises(mc.RunStop):
            client.chat(MESSAGES, stage="basic")
        self.assertFalse(set(RA_FIELDS) & set(model_errors(sink)[0]))

    def test_parse_retry_after_handles_seconds_dates_and_garbage(self):
        cases = {"12": 12000, " 0 ": 0, "": None, None: None, "abc": None, "1.5": None, "-1": None,
                 http_date(SENT_EPOCH + 45): 45000, http_date(SENT_EPOCH - 1): 0}
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(mc.parse_retry_after(value, SENT_EPOCH), expected)
        bare = http_date(SENT_EPOCH + 20).replace(" GMT", "")  # 시간대 없는 날짜는 GMT로 본다
        self.assertEqual(mc.parse_retry_after(bare, SENT_EPOCH), 20000)

    def test_transport_collects_allowlisted_headers_and_masks_the_error_body(self):
        message = email.message.Message()
        for key, value in (("Retry-After", "30"), ("X-RateLimit-Remaining-Requests", "0"), ("X-Request-Id", "r-1"),
                           ("Content-Type", "application/json"), ("Set-Cookie", "session=nope"),
                           ("Authorization", "Bearer " + KEY)):
            message[key] = value
        body = ('{"error": "rate limited", "key": "' + KEY + '", "pad": "').encode("utf-8") + b"x" * 300 + b'"}'
        error = urllib.error.HTTPError(ENDPOINT, 429, "err", message, io.BytesIO(body))
        sent = transport_send(mc.UrllibTransport(ENDPOINT, "TS_TEST_KEY_ENV", opener=FakeOpener(error)))
        self.assertEqual((sent["http_status"], sent["error"]), (429, None))
        self.assertEqual(sent["headers"], {"retry-after": "30", "x-ratelimit-remaining-requests": "0",
                                           "x-request-id": "r-1"})  # 허용 목록 밖 헤더는 없다
        self.assertEqual(len(sent["body_excerpt"]), 200)
        self.assertIn(MASKED, sent["body_excerpt"])
        self.assertNotIn(KEY, sent["body_excerpt"])
        self.assertEqual(sent["body"], body)  # 원본 본문은 그대로다
        # 본문이 없는 오류 응답은 body_excerpt가 None, 헤더가 없으면 {}
        empty = transport_send(mc.UrllibTransport(ENDPOINT, "TS_TEST_KEY_ENV", opener=FakeOpener(http_error(503))))
        self.assertEqual((empty["headers"], empty["body_excerpt"]), ({}, None))
        # 깨진 UTF-8은 대체 문자로 푼다
        broken = transport_send(mc.UrllibTransport(ENDPOINT, "TS_TEST_KEY_ENV",
                                                   opener=FakeOpener(http_error(500, b"\xff\xfe oops"))))
        self.assertEqual(broken["body_excerpt"], "�� oops")

    def test_success_response_carries_headers_and_other_transport_results_keep_their_shape(self):
        handler = FakeHTTPS((200, {"X-Request-Id": "ok-1", "Content-Length": "5", "retry-after": "1"}, ok_body("{}")))
        sent = transport_send(mc.UrllibTransport(ENDPOINT, "TS_TEST_KEY_ENV", opener=mc.build_opener(handler)))
        self.assertEqual((sent["http_status"], sent["headers"]), (200, {"x-request-id": "ok-1", "retry-after": "1"}))
        self.assertNotIn("body_excerpt", sent)
        for exc in (urllib.error.URLError(TimeoutError("t")), ConnectionResetError("reset"),
                    urllib.error.URLError(OSError("Tunnel connection failed: 403 Forbidden"))):
            with self.subTest(exc=repr(exc)[:40]):
                sent = transport_send(mc.UrllibTransport(ENDPOINT, "TS_TEST_KEY_ENV", opener=FakeOpener(exc)))
                self.assertFalse({"headers", "body_excerpt"} & set(sent))
        denied = transport_send(mc.UrllibTransport(ENDPOINT, "TS_TEST_KEY_ENV",
                                                   opener=FakeOpener(http_error(403, b'{"error": "policy_denied"}'))))
        self.assertEqual(denied["error"], "policy_denied")
        self.assertFalse({"headers", "body_excerpt"} & set(denied))

    def test_header_values_are_masked_and_repeated_names_are_joined(self):
        message = email.message.Message()
        message["X-Request-Id"] = KEY
        message["Retry-After"] = "3"
        message["retry-after"] = "4"
        self.assertEqual(mc.collect_headers(message), {"x-request-id": MASKED, "retry-after": "3, 4"})
        self.assertEqual(mc.collect_headers(None), {})
        self.assertIsNone(mc.body_excerpt(b""))
        self.assertEqual(mc.body_excerpt((KEY + " " + mc.KEY_PREFIX + "def_9-x tail").encode("utf-8")),
                         MASKED + " " + MASKED + " tail")

    def test_retry_after_cap_is_a_required_non_negative_integer(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "model"
            shutil.copytree(mc.DEFAULT_CONFIG_DIR, folder)
            raw = json.loads((folder / "model.json").read_text(encoding="utf-8"))
            for value in (0, 60000, -1, "60000", 1.5, None, "missing"):
                retry = dict(raw["retry"])
                if value == "missing":
                    retry.pop("retry_after_cap_ms")
                else:
                    retry["retry_after_cap_ms"] = value
                (folder / "model.json").write_text(json.dumps(dict(raw, retry=retry)), encoding="utf-8")
                with self.subTest(value=value):
                    if value in (0, 60000):
                        self.assertEqual(mc.load_model_config(folder).settings.retry_after_cap_ms, value)
                    else:
                        with self.assertRaises(mc.ConfigError):
                            mc.load_model_config(folder)


if __name__ == "__main__":
    unittest.main()
