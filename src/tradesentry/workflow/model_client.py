"""단위 I7 NIM 호출.

단위 ID: I7
도메인명: workflow_model_client
소유: M
입력: 메시지
출력: 응답(5xx·429 재전송 3회, 제한 시간, 토큰)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.runlog

NIM(NVIDIA 클라우드 추론 API) chat completions를 부르는 클라이언트다. 요청 형식은 X1과 구 개발계획 G4 관문 시험에서
확인한 모양(tools·tool_choice, chat_template_kwargs의 enable_thinking)을 따른다.

규칙(개발 플랜 §3.5·§6.6, 룰북 B2·B5, 자료 계약 §3.3·§8.1)
- 자동 재시도는 없다(urllib 직접 호출). HTTP 5xx와 429(호출 한도 초과)만 코드가 명시적으로 재전송한다: 같은 고리에서
  둘을 합쳐 요청당 최대 3회(설정 retry.max_5xx_retries, 이름은 그대로 두고 429도 이 한도를 쓴다), 지수 대기
  (backoff_base_ms × backoff_factor^회차, model-1.4부터 5초·10초·20초, 조정값). 재전송도 HTTP 시도 한 번이므로 모델
  요청 수(model_requests)에 센다. 한도를 다 쓴 5xx는 PROVIDER_HTTP_5XX, 429는 PROVIDER_HTTP_4XX이고 detail은 둘 다
  "HTTP {상태}(재전송 N회 뒤)"다(마지막 응답의 상태로 가른다). 둘 다 인프라 실패 재실행 대상이다(단위 L3, 2026-09-25
  15:52 사용자 결정 기록 20260925-1552-user-decision-429-retry).
- 다른 4xx(400·401·403·404·422 등)·정책 프록시 거부·연결 실패·요청별 제한 시간 초과·읽을 수 없는 본문은 재전송하지
  않고 실행을 멈춘다(원인 분류 코드는 단위 L3).
- 한도 확인 순서: 사례 deadline이 먼저다(전체 deadline 우선). 그다음 모델 요청 10회, 그다음 누적 토큰(설정 limits.tokens, 128,000).
  재전송하기 전에도 같은 순서로 본다. 대기가 deadline을 넘으면 DEADLINE(TIMEOUT), 재전송 중 모델 요청 10회에 먼저
  닿으면 BUDGET_MODEL_REQUESTS(BUDGET_EXCEEDED)로 멈춘다. 후자는 인프라 실패 재실행 대상이 아니다.
- 요청별 제한 시간은 min(60초, deadline까지 남은 시간 − 종료 기록 예약 시간)이다. 남은 시간이 없으면 보내지 않는다.
- 토큰: 요청마다 max_tokens를 min(설정값, 남은 토큰)으로 줄여 보낸다. 응답을 받은 뒤 누적(입력 + 출력)이 한도를
  넘으면 BUDGET_TOKENS로 멈춘다. 그래서 COMPLETED 실행은 토큰 한도를 넘지 않는다(해석, 조정값).
- 키: 키 값은 전송 자리(UrllibTransport.send)가 보내는 순간 환경변수(설정의 api_key_env, 기본 NVIDIA_API_KEY.
  NemoClaw 시연 샌드박스는 NVIDIA_INFERENCE_API_KEY)에서 읽어 헤더에만 싣는다. 샌드박스 안의 그 값은 자리표시
  값이고 감독 프로세스가 실제 키로 바꾼다(결정 기록 20260924-1556-x1-key-injection). 헤더와 키 값은 trace·오류
  문장·반환값에 나오지 않는다(자료 계약 N13).
  - 값은 공백 없는 출력 가능 ASCII여야 한다(KEY_VALUE_RE). 아니면 요청을 세기 전에 변수 이름만 담은 오류로 멈춘다.
    CR·LF나 라틴-1 밖 글자가 든 값을 헤더에 넣으면 표준 라이브러리 예외의 문장·repr에 값이 실리기 때문이다. 요청을
    만들고 보내는 구간의 ValueError·UnicodeError도 원래 예외를 잇지 않은 채 같은 오류로 바꾼다.
  - Authorization은 add_unredirected_header로 싣고, 리디렉션을 따라가지 않는 opener(build_opener)로 보낸다. 3xx는
    HTTPError로 돌아와 PROVIDER_BAD_RESPONSE로 멈춘다(키가 다른 주소로 가지 않고, 세지 않는 HTTP 시도가 생기지
    않는다). 프록시 설정(HTTPS_PROXY 등, 샌드박스 정책 프록시)은 표준 처리기대로 따른다.
  - 설정은 허용 목록만 받는다: 엔드포인트 호스트 ALLOWED_ENDPOINT_HOSTS(https, 443), 키 환경변수 이름
    ALLOWED_KEY_ENVS. 샌드박스 종류(채점용·시연용)에 따라 어느 이름을 쓸지는 CLI(로드맵 MT5)가 정한다.
- 샌드박스 정책 프록시 거부(단위 L3 policy_denied, 잠정): CONNECT 403·407("Tunnel connection failed: 403")과 HTTP
  403 본문 error "policy_denied"(L7 거부)를 전송 자리가 error "policy_denied"로 가른다. 재전송하지 않고 CODE_ERROR로
  멈춘다(재실행 대상 아님). detail은 "policy_denied(connect|l7) {상태}", trace model_error에는 http_status와 denial을
  남긴다. 프록시 응답 본문(실행 파일 경로가 들어 있다)은 어디에도 싣지 않는다.
- 구조화 출력(설정 request.structured_output, "off"·"json_object", 결정 기록 ⑯): "json_object"이고, 요청에 도구가 없고,
  부르는 쪽이 json_output을 참으로 줄 때만 response_format {"type": "json_object"}를 싣는다. 도구를 싣는 요청과 "off"에는
  싣지 않는다. 도구를 뺀 요청에는 tools·tool_choice 키가 없다. nvext.guided_json은 이 모델·엔드포인트가 HTTP 400으로
  받지 않아(2026-09-25 실측) 설정 값에 두지 않는다.
- 수는 int와 Decimal만 쓴다. 설정과 응답 본문은 소수를 Decimal로 읽고, HTTP 요청 본문을 만들 때만 float로 바꾼다.

전송 자리 약속(단위 I8 기록 재생과 같은 모양): send(payload, timeout_ms) -> {http_status, body(bytes), error(None·
"connection"·"timeout"·"policy_denied"), elapsed_ms, denial(error가 policy_denied일 때만: "connect"·"l7")}.
"""
import http.client
import json
import os
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Callable

from tradesentry.runlog import cause_codes
from tradesentry.runlog import trace as trace_log

# 개발용 기본 위치(저장소 배치). 샌드박스처럼 설치한 패키지로 돌 때는 부르는 쪽이 설정 폴더를 인자로 준다.
DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[3] / "configs" / "model"
LIMIT_KEYS = ("model_requests", "tokens", "wall_ms", "tool_attempts", "basic_tool_attempts",
              "investigator_comparisons", "revision_stages", "revision_requeries", "final_verify")
PROMPT_KEYS = ("investigator", "claims_template", "claims_freeform", "critic")
MESSAGE_KEYS = ("role", "content", "tool_calls")
STRUCTURED_OUTPUT_MODES = ("off", "json_object")  # guided_json은 HTTP 400(실측)이라 받지 않는다
ALLOWED_ENDPOINT_HOSTS = frozenset({"integrate.api.nvidia.com"})
ALLOWED_KEY_ENVS = frozenset({"NVIDIA_API_KEY", "NVIDIA_INFERENCE_API_KEY"})
KEY_VALUE_RE = re.compile(r"[\x21-\x7e]+")  # 공백 없는 출력 가능 ASCII(자리표시 값 openshell:resolve:env:… 포함)
TUNNEL_DENIED_RE = re.compile(r"Tunnel connection failed: (403|407)(?!\d)")
DENIAL_KINDS = ("connect", "l7")


class ConfigError(Exception):
    """모델 설정 폴더를 읽을 수 없거나 형식이 틀렸다."""


class TransportConfigError(Exception):
    """전송 자리가 요청을 보낼 준비가 안 됐다(예: 키 환경변수가 비었다). 네트워크에 닿기 전에 난다."""


class RunStop(Exception):
    """실행을 멈추는 원인. code는 단위 L3의 원인 분류 코드다."""

    def __init__(self, code: str, stage: str | None, detail: str = ""):
        super().__init__(code)
        self.code = code
        self.stage = stage
        self.detail = detail


@dataclass(frozen=True)
class ModelSettings:
    config_version: str
    model: str
    endpoint: str
    api_key_env: str
    temperature: Decimal
    top_p: Decimal
    max_tokens: int
    enable_thinking: bool
    max_5xx_retries: int
    backoff_base_ms: int
    backoff_factor: int
    request_cap_ms: int
    end_reserve_ms: int
    structured_output: str = "off"
    tool_turn_max_tokens: int | None = None  # tool_choice required 차례의 max_tokens(없으면 max_tokens. AS2 ㉑)


@dataclass(frozen=True)
class RunLimits:
    model_requests: int
    tokens: int
    wall_ms: int
    tool_attempts: int
    basic_tool_attempts: int
    investigator_comparisons: int
    revision_stages: int
    revision_requeries: int
    final_verify: int


@dataclass(frozen=True)
class ModelConfig:
    settings: ModelSettings
    limits: RunLimits
    prompts: dict = field(default_factory=dict)


def _int(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ConfigError(f"{name}는 0 이상의 정수다")
    return value


def load_model_config(config_dir: Path | None = None, *, api_key_env: str | None = None) -> ModelConfig:
    """설정 폴더(configs/model/)의 model.json과 프롬프트 파일을 읽는다. api_key_env로 키 환경변수 이름을 바꿀 수 있다."""
    folder = Path(config_dir) if config_dir is not None else DEFAULT_CONFIG_DIR
    try:
        raw = json.loads((folder / "model.json").read_text(encoding="utf-8"), parse_float=Decimal)
        request, retry, timeouts, limits = raw["request"], raw["retry"], raw["timeouts"], raw["limits"]
        prompts = {key: (folder / raw["prompts"][key]).read_text(encoding="utf-8") for key in PROMPT_KEYS}
        env_name = api_key_env if api_key_env is not None else raw["api_key_env"]
        if env_name not in ALLOWED_KEY_ENVS:
            raise ConfigError(f"api_key_env는 {'·'.join(sorted(ALLOWED_KEY_ENVS))} 가운데 하나다")
        for key in ("temperature", "top_p"):
            if not isinstance(request[key], Decimal):
                raise ConfigError(f"request.{key}는 소수다")
        if not isinstance(request["enable_thinking"], bool):
            raise ConfigError("request.enable_thinking은 참/거짓이다")
        structured = request.get("structured_output", "off")
        if structured not in STRUCTURED_OUTPUT_MODES:
            raise ConfigError(f"request.structured_output은 {'·'.join(STRUCTURED_OUTPUT_MODES)} 가운데 하나다")
        settings = ModelSettings(
            config_version=str(raw["config_version"]), model=str(raw["model"]), endpoint=str(raw["endpoint"]),
            api_key_env=env_name, temperature=request["temperature"], top_p=request["top_p"],
            max_tokens=_int(request["max_tokens"], "request.max_tokens"), enable_thinking=request["enable_thinking"],
            max_5xx_retries=_int(retry["max_5xx_retries"], "retry.max_5xx_retries"),
            backoff_base_ms=_int(retry["backoff_base_ms"], "retry.backoff_base_ms"),
            backoff_factor=_int(retry["backoff_factor"], "retry.backoff_factor"),
            request_cap_ms=_int(timeouts["request_cap_ms"], "timeouts.request_cap_ms"),
            end_reserve_ms=_int(timeouts["end_reserve_ms"], "timeouts.end_reserve_ms"),
            structured_output=structured,
            tool_turn_max_tokens=None if request.get("tool_turn_max_tokens") is None
            else _int(request["tool_turn_max_tokens"], "request.tool_turn_max_tokens"))
        run_limits = RunLimits(**{key: _int(limits[key], f"limits.{key}") for key in LIMIT_KEYS})
    except (OSError, KeyError, TypeError, ValueError) as exc:
        if isinstance(exc, ConfigError):
            raise
        raise ConfigError(f"모델 설정을 읽지 못했다({type(exc).__name__})") from None
    _check_endpoint(settings.endpoint)
    return ModelConfig(settings=settings, limits=run_limits, prompts=prompts)


def _check_endpoint(endpoint: str) -> None:
    """엔드포인트는 허용 목록의 호스트에 https(443)로만 간다. 사용자 정보(user:pw@)가 든 주소는 받지 않는다."""
    try:
        parts = urllib.parse.urlsplit(endpoint)
        port = parts.port
    except ValueError:
        raise ConfigError("endpoint를 주소로 읽지 못했다") from None
    if parts.scheme != "https" or parts.hostname not in ALLOWED_ENDPOINT_HOSTS or port not in (None, 443) \
            or parts.username is not None or parts.password is not None:
        raise ConfigError(f"endpoint는 https://{'·'.join(sorted(ALLOWED_ENDPOINT_HOSTS))} 주소다")


def _default_clock_ms() -> int:
    return time.monotonic_ns() // 1_000_000


def _default_sleep_ms(ms: int) -> None:
    time.sleep(ms / 1000)


class Budget:
    """사례 1건의 모델 쪽 누적 값(모델 요청·토큰)과 deadline. 도구 쪽 값은 흐름 조정(단위 I12)이 센다."""

    def __init__(self, limits: RunLimits, start_ms: int, end_reserve_ms: int):
        self.limits = limits
        self.start_ms = start_ms
        self.deadline_ms = start_ms + limits.wall_ms
        self.end_reserve_ms = end_reserve_ms
        self.model_requests = 0
        self.tokens_in = 0
        self.tokens_out = 0

    @property
    def tokens_total(self) -> int:
        return self.tokens_in + self.tokens_out

    def remaining_ms(self, now_ms: int) -> int:
        """deadline까지 남은 시간에서 종료 기록 예약 시간을 뺀 값."""
        return self.deadline_ms - now_ms - self.end_reserve_ms

    def deadline_passed(self, now_ms: int) -> bool:
        return self.remaining_ms(now_ms) <= 0

    def elapsed_ms(self, now_ms: int) -> int:
        return max(0, now_ms - self.start_ms)


def _json_number(value: object) -> object:
    if isinstance(value, Decimal):
        return float(value)  # HTTP 요청 본문을 만들 때만 float로 바꾼다
    raise TypeError(f"요청 본문에 쓸 수 없는 값: {type(value).__name__}")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """3xx 리디렉션을 따라가지 않는다. 표준 처리기의 마지막 단계가 3xx를 HTTPError로 돌려준다."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ARG002 - 표준 서명
        return None


def build_opener(*handlers: urllib.request.BaseHandler) -> urllib.request.OpenerDirector:
    """리디렉션을 따라가지 않는 opener. 나머지(프록시 환경변수 등)는 표준 처리기 그대로다. handlers는 시험용 교체다."""
    return urllib.request.build_opener(_NoRedirect, *handlers)


def _policy_denied_body(data: bytes) -> bool:
    """정책 프록시의 L7 거부 본문인가(JSON 객체의 error가 policy_denied). 본문은 판정에만 쓰고 어디에도 싣지 않는다."""
    try:
        parsed = json.loads(data.decode("utf-8"), parse_float=Decimal)
    except (ValueError, UnicodeDecodeError):
        return False
    return isinstance(parsed, dict) and parsed.get("error") == "policy_denied"


def _tunnel_denied(reason: object) -> int | None:
    """정책 프록시의 CONNECT 거부(403·407)면 그 상태를, 아니면 None을 돌려준다. 다른 터널 상태는 연결 실패로 둔다."""
    if not isinstance(reason, OSError):
        return None
    match = TUNNEL_DENIED_RE.match(str(reason))
    return int(match.group(1)) if match else None


class UrllibTransport:
    """실제 전송 자리. 키는 보내는 순간 환경변수에서 읽어 헤더에만 싣는다. 자동 재시도·리디렉션 따라가기는 없다."""

    def __init__(self, endpoint: str, api_key_env: str, opener: urllib.request.OpenerDirector | None = None):
        self.endpoint = endpoint
        self.api_key_env = api_key_env
        self._opener = opener if opener is not None else build_opener()

    def _credential(self) -> str:
        value = os.environ.get(self.api_key_env, "")
        if not value:
            raise TransportConfigError(f"키 환경변수 {self.api_key_env}가 비어 있다")
        if KEY_VALUE_RE.fullmatch(value) is None:
            raise TransportConfigError(f"키 환경변수 {self.api_key_env}의 값에 헤더에 쓸 수 없는 글자(공백·제어 문자·"
                                       "ASCII 밖 글자)가 있다")
        return value

    def ready(self) -> None:
        """보낼 준비가 됐는지 본다(키 환경변수가 비었거나 값의 글자가 틀리면 TransportConfigError). 값은 돌려주지 않는다."""
        self._credential()

    def send(self, payload: dict, timeout_ms: int) -> dict:
        started = _default_clock_ms()
        error = None
        bad_request = False
        try:
            body = json.dumps(payload, default=_json_number, ensure_ascii=False).encode("utf-8")
            request = urllib.request.Request(self.endpoint, data=body, method="POST", headers={
                "Content-Type": "application/json", "Accept": "application/json"})
            request.add_unredirected_header("Authorization", "Bearer " + self._credential())
            with self._opener.open(request, timeout=timeout_ms / 1000) as response:
                return {"http_status": response.status, "body": response.read(), "error": None,
                        "elapsed_ms": _default_clock_ms() - started}
        except urllib.error.HTTPError as exc:
            try:
                data = exc.read() or b""
            except (OSError, http.client.HTTPException):
                data = b""
            elapsed = _default_clock_ms() - started
            if exc.code == 403 and _policy_denied_body(data):
                return {"http_status": 403, "body": b"", "error": "policy_denied", "denial": "l7",
                        "elapsed_ms": elapsed}
            return {"http_status": exc.code, "body": data, "error": None, "elapsed_ms": elapsed}
        except urllib.error.URLError as exc:
            denied = _tunnel_denied(exc.reason)
            if denied is not None:
                return {"http_status": denied, "body": b"", "error": "policy_denied", "denial": "connect",
                        "elapsed_ms": _default_clock_ms() - started}
            error = "timeout" if isinstance(exc.reason, (TimeoutError, socket.timeout)) else "connection"
        except (TimeoutError, socket.timeout):
            error = "timeout"
        except OSError as exc:
            denied = _tunnel_denied(exc)
            if denied is not None:
                return {"http_status": denied, "body": b"", "error": "policy_denied", "denial": "connect",
                        "elapsed_ms": _default_clock_ms() - started}
            error = "connection"
        except (ValueError, UnicodeError):
            bad_request = True  # 헤더·본문 값 검사 실패. 원래 예외(문장에 헤더 값이 실린다)를 잇지 않는다
        if bad_request:
            raise TransportConfigError("요청을 만들거나 보내지 못했다(헤더·본문 값 검사 실패)")
        return {"http_status": None, "body": b"", "error": error, "elapsed_ms": _default_clock_ms() - started}


def _message_subset(message: object) -> dict:
    if not isinstance(message, dict):
        raise ValueError("choices[0].message가 객체가 아니다")
    subset = {key: message.get(key) for key in MESSAGE_KEYS}
    if subset["content"] is not None and not isinstance(subset["content"], str):
        raise ValueError("message.content는 문자열이다")
    calls = subset["tool_calls"]
    if calls is not None:
        if not isinstance(calls, list):
            raise ValueError("message.tool_calls는 목록이다")
        subset["tool_calls"] = [{"id": c.get("id"), "type": c.get("type", "function"),
                                 "function": {"name": (c.get("function") or {}).get("name"),
                                              "arguments": (c.get("function") or {}).get("arguments")}}
                                for c in calls]
    return subset


def _parse_body(body: bytes) -> tuple[dict, str | None, dict]:
    data = json.loads(body.decode("utf-8"), parse_float=Decimal)
    choice = data["choices"][0]
    usage = data["usage"]
    counts = {key: usage.get(key) for key in ("prompt_tokens", "completion_tokens", "total_tokens")}
    if not all(isinstance(v, int) and not isinstance(v, bool) and v >= 0
               for v in (counts["prompt_tokens"], counts["completion_tokens"])):
        raise ValueError("usage의 토큰 수가 없다")
    if not isinstance(counts["total_tokens"], int) or isinstance(counts["total_tokens"], bool):
        counts["total_tokens"] = counts["prompt_tokens"] + counts["completion_tokens"]
    finish = choice.get("finish_reason")
    return _message_subset(choice.get("message")), finish if isinstance(finish, str) else None, counts


class ModelClient:
    """사례 1건 동안 쓰는 NIM 클라이언트. 조사자와 Critic이 같은 Budget을 나눠 쓴다(별도 문맥은 메시지로 나눈다)."""

    def __init__(self, settings: ModelSettings, budget: Budget, transport, sink: trace_log.Sink,
                 clock_ms: Callable[[], int] = _default_clock_ms, sleep_ms: Callable[[int], None] = _default_sleep_ms):
        self.settings = settings
        self.budget = budget
        self.transport = transport
        self.sink = sink
        self.clock_ms = clock_ms
        self.sleep_ms = sleep_ms
        self.request_no = 0

    def _precheck(self, stage: str | None) -> int:
        now = self.clock_ms()
        if self.budget.deadline_passed(now):
            raise RunStop(cause_codes.DEADLINE, stage, "사례 deadline에 닿아 모델 요청을 보내지 않았다")
        if self.budget.model_requests >= self.budget.limits.model_requests:
            raise RunStop(cause_codes.BUDGET_MODEL_REQUESTS, stage, "모델 요청 한도에 닿았다")
        if self.budget.tokens_total >= self.budget.limits.tokens:
            raise RunStop(cause_codes.BUDGET_TOKENS, stage, "누적 토큰 한도에 닿았다")
        return now

    def build_payload(self, messages: list[dict], tools: list[dict] | None, json_output: bool = False,
                      tool_choice: str = "auto") -> dict:
        """요청 본문. 도구가 없으면 tools·tool_choice 키를 싣지 않는다. 구조화 출력(response_format json_object)은 설정이
        "json_object"이고, 도구가 없고, 부르는 쪽이 json_output을 참으로 줄 때만 싣는다. tool_choice가 required인 도구 차례의
        max_tokens는 설정 tool_turn_max_tokens(있을 때)다(도구 호출 응답은 짧다. 공백 반복 실측, AS2 ㉑)."""
        s = self.settings
        cap = s.tool_turn_max_tokens if tools and tool_choice == "required" and s.tool_turn_max_tokens else s.max_tokens
        payload = {"model": s.model, "messages": messages, "temperature": s.temperature, "top_p": s.top_p,
                   "max_tokens": max(1, min(cap, self.budget.limits.tokens - self.budget.tokens_total)),
                   "stream": False, "chat_template_kwargs": {"enable_thinking": s.enable_thinking}}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice  # "auto" 또는 "required"(흐름 조정이 필수 결과가 빠진 차례에만, AS2 ⑲)
        elif json_output and s.structured_output == "json_object":
            payload["response_format"] = {"type": "json_object"}
        return payload

    def chat(self, messages: list[dict], *, stage: str | None, tools: list[dict] | None = None,
             json_output: bool = False, tool_choice: str = "auto") -> dict:
        """요청 하나를 보내고 응답(message·finish_reason·usage)을 돌려준다. 멈출 원인이 생기면 RunStop을 낸다.
        json_output은 도구 없는 요청에서 구조화 출력을 청하는 표시다(설정이 "off"면 싣지 않는다)."""
        self._precheck(stage)
        ready = getattr(self.transport, "ready", None)  # 실제 전송 자리만 있다(기록 재생에는 없다)
        if ready is not None:
            try:
                ready()
            except TransportConfigError as exc:
                raise RunStop(cause_codes.CODE_ERROR, stage, str(exc)) from None
        self.request_no += 1
        if tool_choice not in ("auto", "required"):
            raise ValueError("tool_choice는 auto나 required다(도구 이름 지정은 하지 않는다)")
        payload = self.build_payload(messages, tools, json_output, tool_choice)
        request_sha = trace_log.canonical_sha256(payload)
        base = {"request_no": self.request_no}
        retries = 0
        attempt = 0
        while True:
            now = self._precheck(stage)
            attempt += 1
            timeout_ms = min(self.settings.request_cap_ms, self.budget.remaining_ms(now))
            self.budget.model_requests += 1
            self.sink.emit("model_request", stage, dict(base, attempt=attempt,
                                                        model_requests=self.budget.model_requests,
                                                        request_sha256=request_sha, timeout_ms=timeout_ms,
                                                        messages=len(messages), tools=len(tools or []),
                                                        **({"tool_choice": tool_choice} if tools else {})))
            try:
                sent = self.transport.send(payload, timeout_ms)
            except TransportConfigError as exc:
                self.budget.model_requests -= 1  # 보내지 않은 요청은 세지 않는다
                raise RunStop(cause_codes.CODE_ERROR, stage, str(exc)) from None
            status, error, elapsed = sent.get("http_status"), sent.get("error"), int(sent.get("elapsed_ms", 0))
            failure = dict(base, attempt=attempt, http_status=status, error=error, elapsed_ms=elapsed)
            if error == "timeout":
                self.sink.emit("model_error", stage, dict(failure, retrying=False, backoff_ms=0))
                if self.budget.deadline_passed(self.clock_ms()):
                    raise RunStop(cause_codes.DEADLINE, stage, "요청 중 사례 deadline에 닿았다")
                raise RunStop(cause_codes.PROVIDER_REQUEST_TIMEOUT, stage, f"요청별 제한 시간 {timeout_ms}ms 초과")
            if error == "policy_denied":
                denial = sent.get("denial") if sent.get("denial") in DENIAL_KINDS else "unknown"
                self.sink.emit("model_error", stage, dict(failure, denial=denial, retrying=False, backoff_ms=0))
                raise RunStop(cause_codes.classify("policy_denied"), stage,
                              f"policy_denied({denial}) {status}: 샌드박스 정책 프록시가 요청을 막았다(재실행 대상 아님)")
            if error is not None or status is None:
                self.sink.emit("model_error", stage, dict(failure, error=error or "connection", retrying=False,
                                                          backoff_ms=0))
                raise RunStop(cause_codes.PROVIDER_CONNECTION, stage, "연결 실패")
            if 500 <= status <= 599 or status == 429:  # 429도 5xx와 같은 재전송 고리·같은 횟수 세기(결정 1552)
                if retries < self.settings.max_5xx_retries:
                    backoff = self.settings.backoff_base_ms * self.settings.backoff_factor ** retries
                    now = self.clock_ms()
                    stop = None
                    if self.budget.remaining_ms(now) <= backoff:
                        stop = RunStop(cause_codes.DEADLINE, stage, f"HTTP {status} 재전송 대기가 deadline을 넘는다")
                    elif self.budget.model_requests >= self.budget.limits.model_requests:
                        stop = RunStop(cause_codes.BUDGET_MODEL_REQUESTS, stage,
                                       f"HTTP {status} 재전송 전에 모델 요청 한도에 닿았다")
                    self.sink.emit("model_error", stage, dict(failure, retrying=stop is None,
                                                              backoff_ms=backoff if stop is None else 0))
                    if stop is not None:
                        raise stop
                    self.sleep_ms(backoff)
                    retries += 1
                    continue
                self.sink.emit("model_error", stage, dict(failure, retrying=False, backoff_ms=0))
                raise RunStop(cause_codes.classify("http_status", http_status=status), stage,
                              f"HTTP {status}(재전송 {retries}회 뒤)")
            if status != 200:
                self.sink.emit("model_error", stage, dict(failure, retrying=False, backoff_ms=0))
                raise RunStop(cause_codes.classify("http_status", http_status=status), stage, f"HTTP {status}")
            try:
                message, finish, usage = _parse_body(sent.get("body") or b"")
            except (ValueError, KeyError, IndexError, TypeError, UnicodeDecodeError, AttributeError):
                self.sink.emit("model_error", stage, dict(failure, error="bad_response", retrying=False, backoff_ms=0))
                raise RunStop(cause_codes.PROVIDER_BAD_RESPONSE, stage, "HTTP 200 응답 본문을 읽지 못했다") from None
            self.budget.tokens_in += usage["prompt_tokens"]
            self.budget.tokens_out += usage["completion_tokens"]
            self.sink.emit("model_response", stage, dict(base, attempt=attempt, http_status=200, elapsed_ms=elapsed,
                                                         usage=usage, tokens_total=self.budget.tokens_total,
                                                         response={"message": message, "finish_reason": finish}))
            if self.budget.tokens_total > self.budget.limits.tokens:
                raise RunStop(cause_codes.BUDGET_TOKENS, stage, "응답을 받은 뒤 누적 토큰이 한도를 넘었다")
            return {"message": message, "finish_reason": finish, "usage": usage, "request_no": self.request_no,
                    "attempts": attempt}


def budget_counters(budget: Budget, now_ms: int, tool_attempts: int = 0) -> dict:
    """원인 분류 코드 항목(단위 L3)의 누적 시도 값."""
    return {"tool_attempts": tool_attempts, "model_requests": budget.model_requests, "tokens_in": budget.tokens_in,
            "tokens_out": budget.tokens_out, "wall_ms": budget.elapsed_ms(now_ms)}


def run(inp: object) -> object:
    """메시지 하나를 NIM에 보내고 응답이나 멈춘 원인을 돌려준다(개발 전용 진입 함수).

    입력: {"messages": [...], "stage": 단계, "tools": [...](선택), "used": {"model_requests", "tokens_in",
    "tokens_out", "elapsed_ms"}(선택, 이미 쓴 값), "config_dir"(선택)}.
    출력: {"response": {message, finish_reason, usage, attempts} 또는 null, "stop": {code, execution_status, detail}
    또는 null, "budget": {model_requests, tokens_in, tokens_out}, "events": [[이벤트, 요약]]}. 키 값은 싣지 않는다.
    """
    if not isinstance(inp, dict) or not isinstance(inp.get("messages"), list):
        raise ValueError("입력은 {messages[], stage, ...}다")
    config = load_model_config(inp.get("config_dir"))
    sink = trace_log.MemoryTrace("workflow_model_client-000000000000", clock=lambda: trace_log.now_kst())
    start = _default_clock_ms()
    used = inp.get("used") or {}
    budget = Budget(config.limits, start - int(used.get("elapsed_ms", 0)), config.settings.end_reserve_ms)
    budget.model_requests = int(used.get("model_requests", 0))
    budget.tokens_in = int(used.get("tokens_in", 0))
    budget.tokens_out = int(used.get("tokens_out", 0))
    client = ModelClient(config.settings, budget,
                         UrllibTransport(config.settings.endpoint, config.settings.api_key_env), sink,
                         clock_ms=_default_clock_ms, sleep_ms=_default_sleep_ms)
    response, stop = None, None
    try:
        answer = client.chat(inp["messages"], stage=inp.get("stage"), tools=inp.get("tools"))
        response = {key: answer[key] for key in ("message", "finish_reason", "usage", "attempts")}
    except RunStop as exc:
        stop = {"code": exc.code, "execution_status": cause_codes.execution_status(exc.code), "detail": exc.detail}
    summary_keys = ("attempt", "http_status", "error", "denial", "retrying", "backoff_ms", "timeout_ms")
    events = [[r["event"], {k: r["data"][k] for k in summary_keys if k in r["data"]}] for r in sink.records]
    return {"response": response, "stop": stop, "budget": {"model_requests": budget.model_requests,
                                                           "tokens_in": budget.tokens_in,
                                                           "tokens_out": budget.tokens_out}, "events": events}
