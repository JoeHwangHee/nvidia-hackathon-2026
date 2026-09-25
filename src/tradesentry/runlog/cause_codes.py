"""단위 L3 원인 분류 코드.

단위 ID: L3
도메인명: runlog_cause_codes
소유: 공동
입력: 실패
출력: `errors`의 원인 분류 코드
허용 import: 표준 라이브러리, tradesentry.contract

실행 결과 기록 `errors`(자료 계약 §8.1)에 적는 원인 분류 코드와, 코드마다의 실행 상태(자료 계약 §3.3)를 정한다.
룰북 B5·평가 스킬 ②는 코드 이름을 "자료 계약이나 S0에서 정한다 [미확인]"로 남겼다. 아래 이름은 로드맵 MT4의 제안이며
오케스트레이터(공용 약속이면 사용자)의 확정 전이다. 계약 상수(실행 상태)는 단위 K1이 생기면 그 커널에서 import한다
(단위 표 §6 조립 부산물 4).

코드와 실행 상태
| 코드 | 실행 상태 | 인프라 실패 재실행 대상(룰북 B5) | 언제 |
|---|---|---|---|
| PROVIDER_HTTP_5XX | FAILED | 예 | 요청당 재전송 한도(3회)를 다 쓴 뒤에도 HTTP 5xx |
| PROVIDER_CONNECTION | FAILED | 예 | 연결 실패(응답을 받지 못함). 재전송하지 않는다 |
| PROVIDER_HTTP_4XX | FAILED | 아니오 | HTTP 4xx(429 포함). 재전송하지 않는다. 재실행 여부는 결정 D12의 입력 |
| PROVIDER_REQUEST_TIMEOUT | FAILED | 아니오 | 사례 deadline 전의 요청별 제한 시간(최대 60초) 초과. 재실행 여부는 결정 D12의 입력 |
| PROVIDER_BAD_RESPONSE | FAILED | 아니오 | HTTP 200인데 본문(JSON·choices·usage)을 읽을 수 없음 |
| BUDGET_MODEL_REQUESTS | BUDGET_EXCEEDED | 아니오 | 모델 요청 한도(10회, 재전송 포함) |
| BUDGET_TOKENS | BUDGET_EXCEEDED | 아니오 | 누적 토큰 한도(설정 limits.tokens, 128,000, 입력 + 출력) |
| DEADLINE | TIMEOUT | 아니오 | 사례당 wall time 한도(300초). 다른 한도보다 먼저 본다 |
| SCHEMA_INVALID | INVALID | 아니오 | 수정 1회 뒤에도 스키마 검사 실패(모델 출력 형식 문제 포함) |
| VALIDATOR_BLOCKED | INVALID | 아니오 | 수정 1회 뒤에도 검증기 차단(checklist는 수정 없이 곧바로, 결정 D1) |
| CODE_ERROR | FAILED | 아니오 | 그 밖의 코드 오류·설정 오류(예외 이름만 적는다). 샌드박스 정책 프록시 거부도 여기 담는다(아래) |

- `errors`에는 실행을 멈춘 원인만 적는다(완료된 실행은 빈 목록). 재전송으로 흡수한 5xx나 한도로 막은 도구 시도는
  trace에만 남긴다. 그래야 "원인이 모델 제공자 쪽 오류뿐인 FAILED" 판정(룰북 B5)이 흐려지지 않는다.
- 재실행 대상 판정은 infra_rerun_eligible 하나로만 한다. 단위 E3(추출 명령)은 코드 문자열을 따로 적지 않는다.
- 한 항목의 키: code, stage, detail(예외 이름·HTTP 상태 같은 짧은 글), attempts(누적 tool_attempts·model_requests·
  tokens_in·tokens_out·wall_ms), last_good_evidence(마지막으로 정상 받은 근거 ID 목록). 자료 계약 §3.3 "실패 원인,
  누적 시도, 마지막 정상 근거"를 옮긴 것이다.

샌드박스 정책 프록시 거부(실패 종류 policy_denied, 잠정)
- OpenShell 정책 프록시가 요청을 막은 경우다. 모양은 둘이다(X1 artifacts/openshell/violation_tests.md V0a·V1·V2b·V3):
  목적지·실행 파일 거부는 CONNECT 403(urllib에서는 "Tunnel connection failed: 403"), L7(method·path) 거부는 HTTP 403에
  본문 error "policy_denied". 407(프록시 인증 요구)도 같이 본다. 다른 터널 상태(예: 502)는 상류 실패일 수 있어 연결
  실패로 둔다.
- 모델 제공자 쪽 오류가 아니라 실행 환경(정책)의 문제라 인프라 실패 재실행 대상이 아니다(룰북 B5는 "모델 제공자 쪽
  오류"만 다시 돌린다). 새 코드 이름을 짓지 않고 CODE_ERROR에 담는다. 가르는 값은 detail의 "policy_denied(connect)"·
  "policy_denied(l7)"와 프록시 상태 코드, trace model_error의 error "policy_denied"·denial(connect·l7)·http_status다
  (단위 I7). 원인 분류 코드 이름 전체는 사용자 결정(D12) 대상이라 바뀔 수 있다.
- 결정 D12에 함께 올린 분류: 429는 PROVIDER_HTTP_4XX, 요청별 제한 시간 초과(연결 단계 시간 초과 포함)는
  PROVIDER_REQUEST_TIMEOUT, 본문을 받는 도중 끊김(http.client.IncompleteRead)은 예외 이름을 적는 CODE_ERROR다. 셋 다
  지금은 재실행 대상이 아니다.
"""
PROVIDER_HTTP_5XX = "PROVIDER_HTTP_5XX"
PROVIDER_CONNECTION = "PROVIDER_CONNECTION"
PROVIDER_HTTP_4XX = "PROVIDER_HTTP_4XX"
PROVIDER_REQUEST_TIMEOUT = "PROVIDER_REQUEST_TIMEOUT"
PROVIDER_BAD_RESPONSE = "PROVIDER_BAD_RESPONSE"
BUDGET_MODEL_REQUESTS = "BUDGET_MODEL_REQUESTS"
BUDGET_TOKENS = "BUDGET_TOKENS"
DEADLINE = "DEADLINE"
SCHEMA_INVALID = "SCHEMA_INVALID"
VALIDATOR_BLOCKED = "VALIDATOR_BLOCKED"
CODE_ERROR = "CODE_ERROR"

# 자료 계약 §3.3 실행 상태(명세 §4.2 원문). 단위 K1이 생기면 커널에서 import한다.
COMPLETED, FAILED, TIMEOUT, INVALID, BUDGET_EXCEEDED = "COMPLETED", "FAILED", "TIMEOUT", "INVALID", "BUDGET_EXCEEDED"
EXECUTION_STATUSES = (COMPLETED, FAILED, TIMEOUT, INVALID, BUDGET_EXCEEDED)

STATUS_BY_CODE = {
    PROVIDER_HTTP_5XX: FAILED,
    PROVIDER_CONNECTION: FAILED,
    PROVIDER_HTTP_4XX: FAILED,
    PROVIDER_REQUEST_TIMEOUT: FAILED,
    PROVIDER_BAD_RESPONSE: FAILED,
    BUDGET_MODEL_REQUESTS: BUDGET_EXCEEDED,
    BUDGET_TOKENS: BUDGET_EXCEEDED,
    DEADLINE: TIMEOUT,
    SCHEMA_INVALID: INVALID,
    VALIDATOR_BLOCKED: INVALID,
    CODE_ERROR: FAILED,
}
CODES = tuple(STATUS_BY_CODE)
INFRA_RERUN_CODES = frozenset({PROVIDER_HTTP_5XX, PROVIDER_CONNECTION})
ERROR_ENTRY_KEYS = ("code", "stage", "detail", "attempts", "last_good_evidence")
ATTEMPT_KEYS = ("tool_attempts", "model_requests", "tokens_in", "tokens_out", "wall_ms")
DETAIL_MAX = 200


def execution_status(code: str) -> str:
    """원인 분류 코드의 실행 상태."""
    if code not in STATUS_BY_CODE:
        raise ValueError(f"알 수 없는 원인 분류 코드: {code!r}")
    return STATUS_BY_CODE[code]


def classify(kind: str, *, http_status: int | None = None, limit: str | None = None) -> str:
    """실패 종류를 원인 분류 코드로 바꾼다.

    kind: http_status(재전송 뒤 남은 HTTP 오류, http_status 필요), connection, request_timeout, bad_response,
    budget(limit이 model_requests 또는 tokens), deadline, schema, validator, exception, policy_denied(샌드박스 정책
    프록시 거부. CODE_ERROR에 담고 재실행 대상이 아니다, 잠정).
    """
    if kind == "http_status":
        if not isinstance(http_status, int) or isinstance(http_status, bool):
            raise ValueError("http_status 실패에는 정수 HTTP 상태가 필요하다")
        if 500 <= http_status <= 599:
            return PROVIDER_HTTP_5XX
        if 400 <= http_status <= 499:
            return PROVIDER_HTTP_4XX
        return PROVIDER_BAD_RESPONSE
    if kind == "budget":
        if limit == "model_requests":
            return BUDGET_MODEL_REQUESTS
        if limit == "tokens":
            return BUDGET_TOKENS
        raise ValueError(f"budget 실패의 한도 이름이 틀렸다: {limit!r}")
    simple = {"connection": PROVIDER_CONNECTION, "request_timeout": PROVIDER_REQUEST_TIMEOUT,
              "bad_response": PROVIDER_BAD_RESPONSE, "deadline": DEADLINE, "schema": SCHEMA_INVALID,
              "validator": VALIDATOR_BLOCKED, "exception": CODE_ERROR, "policy_denied": CODE_ERROR}
    if kind not in simple:
        raise ValueError(f"알 수 없는 실패 종류: {kind!r}")
    return simple[kind]


def error_entry(code: str, stage: str | None, attempts: dict, last_good_evidence: list,
                detail: str = "") -> dict:
    """errors 목록의 한 항목. 누적 시도 값은 ATTEMPT_KEYS 다섯 개를 모두 정수로 받는다."""
    execution_status(code)
    missing = [k for k in ATTEMPT_KEYS if not isinstance(attempts.get(k), int) or isinstance(attempts.get(k), bool)]
    if missing:
        raise ValueError(f"누적 시도 값이 모자라다: {missing}")
    if not isinstance(last_good_evidence, list) or not all(isinstance(e, str) for e in last_good_evidence):
        raise ValueError("last_good_evidence는 근거 ID 문자열 목록이다")
    return {"code": code, "stage": stage, "detail": str(detail)[:DETAIL_MAX],
            "attempts": {k: attempts[k] for k in ATTEMPT_KEYS}, "last_good_evidence": list(last_good_evidence)}


def infra_rerun_eligible(execution_status_value: str, errors: list) -> bool:
    """룰북 B5 인프라 실패 재실행 대상인가: FAILED이고, errors가 비지 않았고, 모든 코드가 모델 제공자 쪽 인프라 오류다."""
    if execution_status_value != FAILED or not errors:
        return False
    return all(isinstance(e, dict) and e.get("code") in INFRA_RERUN_CODES for e in errors)


def run(inp: object) -> object:
    """실패 하나를 원인 분류 코드로 바꾼다.

    입력: {"kind": 실패 종류, "http_status": 정수(선택), "limit": 한도 이름(선택)}.
    출력: {"code": 원인 분류 코드, "execution_status": 실행 상태, "infra_rerun": 인프라 실패 재실행 대상인가}.
    """
    if not isinstance(inp, dict):
        raise ValueError("입력은 {kind, ...} 객체다")
    code = classify(inp.get("kind"), http_status=inp.get("http_status"), limit=inp.get("limit"))
    status = execution_status(code)
    probe = [{"code": code}]
    return {"code": code, "execution_status": status, "infra_rerun": infra_rerun_eligible(status, probe)}
