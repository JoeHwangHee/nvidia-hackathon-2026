"""단위 I8 기록 재생.

단위 ID: I8
도메인명: workflow_replay
소유: M
입력: 기록된 trace
출력: 같은 응답(키 없는 스모크 시험)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.runlog, tradesentry.workflow

기록된 trace(단위 L1 형식)로 NIM(NVIDIA 클라우드 추론 API) 응답과 도구 봉투를 기록 순서대로 다시 내준다. 네트워크와
키, 스냅샷 없이 흐름(단위 I10~I12)을 다시 돌리는 스모크 시험과 골든 쌍에 쓴다. 재생은 기록을 고치지 않는다.

전송 자리(transport) 약속. 단위 I7(모델 호출)의 실제 전송과 ReplayTransport가 같은 모양이다.
- send(payload: dict, timeout_ms: int) -> dict. payload는 chat completions 요청 본문(Decimal 허용)이다.
- 돌려주는 키: http_status(int 또는 None), body(bytes, 응답 본문), error(None, "connection", "timeout",
  "policy_denied"), elapsed_ms(int). 연결 실패·제한 시간 초과는 http_status가 None이고 error가 채워진다.
- error가 "policy_denied"(샌드박스 정책 프록시 거부)면 http_status는 프록시가 준 상태(403·407)이고, 키 denial이
  거부 자리("connect": CONNECT 터널 거부, "l7": HTTP 요청 거부)를 알린다. 재생은 trace model_error의 denial을 그대로
  돌려준다(그래야 재생한 실행의 원인 분류 detail이 기록과 같다).

재생 규칙
- 응답: model_response·model_error 레코드를 차례로 하나씩 내준다. 바로 앞 model_request에 request_sha256이 있으면
  보내려는 요청의 canonical_sha256(단위 L1)과 같아야 하고, 다르면 ReplayMismatch다(흐름이 기록에서 벗어났다).
- 도구: tool_call과 짝인 tool_result를 차례로 내준다. 도구 이름과 인자가 기록과 다르면 ReplayMismatch다.
  budget_block으로 막힌 시도는 도구를 부르지 않았으므로 재생 대상이 아니다.
- 시각: ReplayClock은 가상 시계다. 재생한 응답·봉투의 elapsed_ms와 대기(sleep)만큼만 흐른다. 그래서 재생 실행의
  wall_ms와 trace 시각이 결정적이다.
"""
from datetime import datetime, timedelta

from tradesentry.runlog import trace as trace_log

REPLAY_BASE = datetime(2026, 9, 25, 0, 0, 0, tzinfo=trace_log.KST)


class ReplayMismatch(Exception):
    """재생하려는 호출이 기록과 다르거나 기록이 모자라다."""


class ReplayClock:
    """가상 시계. now_ms는 단조 증가 밀리초, wall은 KST 시각이다."""

    def __init__(self, base: datetime = REPLAY_BASE):
        self._ms = 0
        self._base = base

    def now_ms(self) -> int:
        return self._ms

    def advance(self, ms: int) -> None:
        if not isinstance(ms, int) or isinstance(ms, bool) or ms < 0:
            raise ValueError("advance는 0 이상의 정수 밀리초다")
        self._ms += ms

    def sleep_ms(self, ms: int) -> None:
        self.advance(ms)

    def wall(self) -> datetime:
        return self._base + timedelta(milliseconds=self._ms)


def _records(source: object) -> list[dict]:
    if not isinstance(source, list) or not all(isinstance(r, dict) for r in source):
        raise ValueError("재생 입력은 trace 레코드 목록이다")
    return source


def response_items(records: list[dict]) -> list[dict]:
    """trace에서 HTTP 시도마다 재생할 응답을 뽑는다."""
    items: list[dict] = []
    pending_sha: str | None = None
    for record in _records(records):
        event, data = record.get("event"), record.get("data") or {}
        if event == "model_request":
            pending_sha = data.get("request_sha256")
        elif event == "model_response":
            body = {"choices": [{"message": data.get("response", {}).get("message"),
                                 "finish_reason": data.get("response", {}).get("finish_reason")}],
                    "usage": data.get("usage")}
            items.append({"request_sha256": pending_sha, "http_status": data.get("http_status", 200),
                          "body": trace_log.dumps(body).encode("utf-8"), "error": None,
                          "elapsed_ms": int(data.get("elapsed_ms", 0))})
            pending_sha = None
        elif event == "model_error":
            item = {"request_sha256": pending_sha, "http_status": data.get("http_status"), "body": b"",
                    "error": data.get("error"), "elapsed_ms": int(data.get("elapsed_ms", 0))}
            if data.get("denial") is not None:
                item["denial"] = data["denial"]
            items.append(item)
            pending_sha = None
    return items


def tool_items(records: list[dict]) -> list[dict]:
    """trace에서 실제로 부른 도구 호출(tool_call → tool_result)을 차례로 뽑는다."""
    items: list[dict] = []
    open_call: dict | None = None
    for record in _records(records):
        event, data = record.get("event"), record.get("data") or {}
        if event == "tool_call":
            open_call = data
        elif event == "tool_result":
            if open_call is None or open_call.get("tool") != data.get("tool"):
                raise ValueError("tool_result 앞에 짝이 되는 tool_call이 없다")
            items.append({"tool": data.get("tool"), "args": open_call.get("args", {}),
                          "envelope": data.get("envelope"), "elapsed_ms": int(data.get("elapsed_ms", 0))})
            open_call = None
    return items


class ReplayTransport:
    """기록된 응답을 차례로 내주는 전송 자리."""

    def __init__(self, records: list[dict], clock: ReplayClock | None = None):
        self._items = response_items(records)
        self._pos = 0
        self._clock = clock

    @property
    def remaining(self) -> int:
        return len(self._items) - self._pos

    def send(self, payload: dict, timeout_ms: int) -> dict:
        if self._pos >= len(self._items):
            raise ReplayMismatch(f"기록된 모델 응답이 {len(self._items)}개뿐인데 더 요청했다")
        item = self._items[self._pos]
        expected = item["request_sha256"]
        if expected is not None and expected != trace_log.canonical_sha256(payload):
            raise ReplayMismatch(f"{self._pos + 1}번째 모델 요청이 기록과 다르다(request_sha256 불일치)")
        self._pos += 1
        if self._clock is not None:
            self._clock.advance(item["elapsed_ms"])
        sent = {"http_status": item["http_status"], "body": item["body"], "error": item["error"],
                "elapsed_ms": item["elapsed_ms"]}
        if "denial" in item:
            sent["denial"] = item["denial"]
        return sent


class ReplayTools:
    """기록된 도구 봉투를 차례로 내주는 도구 자리. call(도구 이름, 인자) -> 봉투."""

    def __init__(self, records: list[dict], clock: ReplayClock | None = None):
        self._items = tool_items(records)
        self._pos = 0
        self._clock = clock

    @property
    def remaining(self) -> int:
        return len(self._items) - self._pos

    def call(self, tool: str, args: dict) -> dict:
        if self._pos >= len(self._items):
            raise ReplayMismatch(f"기록된 도구 봉투가 {len(self._items)}개뿐인데 더 불렀다")
        item = self._items[self._pos]
        if item["tool"] != tool or trace_log.canonical_sha256(item["args"]) != trace_log.canonical_sha256(args):
            raise ReplayMismatch(f"{self._pos + 1}번째 도구 호출이 기록과 다르다({tool})")
        self._pos += 1
        if self._clock is not None:
            self._clock.advance(item["elapsed_ms"])
        return item["envelope"]


def run(inp: object) -> object:
    """기록된 trace와 보낼 요청 목록으로 응답을 차례로 재생한다.

    입력: {"trace": [trace 레코드], "requests": [chat completions 요청 본문, ...]}.
    출력: {"responses": [{"http_status", "body"(JSON 객체 또는 null), "error", "elapsed_ms"}], "remaining": 남은 기록 수}.
    요청이 기록과 다르거나 기록이 모자라면 ReplayMismatch다.
    """
    if not isinstance(inp, dict) or not isinstance(inp.get("requests"), list):
        raise ValueError("입력은 {trace[], requests[]}다")
    transport = ReplayTransport(_records(inp.get("trace")))
    responses = []
    for payload in inp["requests"]:
        sent = transport.send(payload, timeout_ms=60000)
        body = trace_log.loads(sent["body"].decode("utf-8")) if sent["body"] else None
        responses.append({"http_status": sent["http_status"], "body": body, "error": sent["error"],
                          "elapsed_ms": sent["elapsed_ms"]})
    return {"responses": responses, "remaining": transport.remaining}
