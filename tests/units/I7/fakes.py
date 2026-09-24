"""단위 I7·I10~I12 시험용 가짜 전송 자리와 가짜 시계(시험 파일 안에만 두는 대역). 네트워크를 쓰지 않는다."""
import json


def ok_body(content=None, tool_calls=None, prompt_tokens=800, completion_tokens=100):
    message = {"role": "assistant", "content": content, "tool_calls": tool_calls}
    return json.dumps({"id": "fake", "choices": [{"index": 0, "message": message, "finish_reason": "stop"}],
                       "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
                                 "total_tokens": prompt_tokens + completion_tokens}}).encode("utf-8")


class FakeClock:
    """단조 밀리초 시계. sleep_ms와 전송 경과 시간만큼만 흐른다."""

    def __init__(self, start=1_000_000):
        self.now = start
        self.sleeps = []

    def clock_ms(self):
        return self.now

    def sleep_ms(self, ms):
        self.sleeps.append(ms)
        self.now += ms


class ScriptedTransport:
    """정해 둔 결과를 차례로 돌려준다. 결과 하나는 {"status": 503} 또는 {"body": bytes} 또는 {"error": "connection"}."""

    def __init__(self, script, clock=None, elapsed_ms=700):
        self.script = list(script)
        self.clock = clock
        self.elapsed_ms = elapsed_ms
        self.payloads = []
        self.timeouts = []

    def send(self, payload, timeout_ms):
        if not self.script:
            raise AssertionError("준비한 응답보다 더 많이 보냈다")
        self.payloads.append(payload)
        self.timeouts.append(timeout_ms)
        step = self.script.pop(0)
        elapsed = step.get("elapsed_ms", self.elapsed_ms)
        if self.clock is not None:
            self.clock.now += elapsed
        if "error" in step:
            return {"http_status": None, "body": b"", "error": step["error"], "elapsed_ms": elapsed}
        if "status" in step:
            return {"http_status": step["status"], "body": step.get("body", b""), "error": None, "elapsed_ms": elapsed}
        return {"http_status": 200, "body": step["body"], "error": None, "elapsed_ms": elapsed}
