"""단위 I10 조사자.

단위 ID: I10
도메인명: workflow_investigator
소유: M
입력: 상태
출력: 다음 비교·초안
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.runlog, tradesentry.workflow

허용 import에 tradesentry.runlog를 더했다(MT4): 근거를 모델에게 보낼 때 Decimal 표기를 지키는 JSON 쓰기(단위 L1
dumps)를 쓴다. S0 결정의 계층(contract → dal·runlog → … → workflow) 안이다.

조사자(Nemotron) 한 차례: 지금까지의 근거(도구 봉투)를 보고 추가 비교(도구 호출)를 고르거나 초안을 쓴다.
- 모델이 부를 수 있는 도구는 MODEL_TOOLS 넷이다. verify_evidence는 코드가 예약한 차례에만 부른다(개발 플랜 §6.7).
  도구 인자는 좁게 받는다: compare_partners의 partners(관세청 2자리 국가코드 최대 5개)만 있고 나머지는 인자가 없다.
  경로·SQL·URL·셸 명령은 받지 않는다(자료 계약 §5.1). 허용 밖 도구·인자는 호출하지 않고 오류로 돌려준다.
- 도구를 줄지(allow_tools)와 몇 번 허용할지는 흐름 조정(단위 I12)이 코드로 정한다. 프롬프트는 한도를 알릴 뿐이다.
- 초안 형식 검사(스키마 검사의 초안 쪽, 모든 모드에서 막는다): JSON 객체 하나, review_status·signal_status·claims·
  narrative·hypotheses, 상태값 집합(review_status 3값, signal_status는 unit_value·share 키와 4값), 형식과 자료형.
  claims는 freeform이면 typed claim 12필드(자료 계약 §6), 나머지 모드면 metric_id나 근거 ID로 가리키는 주장(값은
  코드가 검증된 지표로 채운다). 응답이 max_tokens에서 잘렸으면(finish_reason length) 그것도 형식 문제다. 검사는 틀린
  초안을 고치지 않고 문제 목록만 돌려준다. 보고서 쪽 스키마 요건(자료 계약 §9.4)은 검증기 자리가 본다.
- 허용 상태 조합(발동하지 않은 신호는 NOT_TRIGGERED, 발동한 신호는 판정 상태, 사례 판정은 발동 신호 판정을
  MAINTAIN > HOLD > MONITOR로 묶은 값)은 형식 문제가 아니다. 룰북 B2의 스키마 검사는 형식·자료형만 보므로, 이 조합은
  검증기(단위 R3 STATUS_INCONSISTENT, 검증기 부류)가 맡는다: full·agent에서는 막고 freeform에서는 기록만 한다.
  여기서는 status_notes로 관찰만 돌려주고(흐름 조정이 trace에 남긴다) 흐름을 바꾸지 않는다.
- 조사자 메시지에는 모드 이름을 넣지 않는다. 모드 사이 차이는 claims 지침(시스템 지침 뒤쪽)뿐이다(룰북 B2).
- 도구를 주지 않는 차례(allow_tools 거짓)에는 요청에 tools를 싣지 않고, 대화 끝에 초안 요청 메시지(DRAFT_REQUEST, 모든
  모드에서 글자까지 같다)를 붙인다. 실측에서 tools를 뺀 요청에도 모델이 구조화된 도구 호출을 돌려주었고(마지막 지시가
  "필요하면 도구로"였다), 도구 이력 뒤 tools 없는 요청에서 JSON이 아닌 글을 썼다(결정 기록 ⑯). 구조화 출력 설정(단위 I7
  request.structured_output, model-0.2부터 "json_object")이 켜져 있으면 그 차례에만 response_format json_object를
  싣는다(모든 모드 같음). 초안 형식 검사(check_draft)는 그와 별개로 그대로 돈다.
- 모델 응답의 소수는 Decimal로 읽는다(freeform 값의 끝자리 0 보존, 자료 계약 §9.1).
"""
import json
import re
from decimal import Decimal

from tradesentry.runlog import trace as trace_log
from tradesentry.workflow import model_client
from tradesentry.workflow import replay

MODEL_TOOLS = ("check_comparability", "get_history", "compare_partners", "decompose_hs")
MODES = ("checklist", "agent", "full", "freeform")
REVIEW_STATUSES = ("MAINTAIN", "MONITOR", "HOLD")
SIGNAL_STATUSES = ("MAINTAIN", "MONITOR", "HOLD", "NOT_TRIGGERED")
SIGNAL_CODES = ("unit_value", "share")
CLAIM_TYPES = ("value", "change", "share", "share_change", "decomposition", "comparison", "data_status")
DIRECTIONS = ("UP", "DOWN", "FLAT", "NA")
CLAIM_FIELDS = ("claim_id", "claim_type", "hs6", "partner", "period", "baseline_period", "metric", "value", "unit",
                "direction", "evidence_ids", "text")
DRAFT_KEYS = ("review_status", "signal_status", "claims", "narrative", "hypotheses")
# 모델용 봉투 보기(compact_envelope)가 남기는 것. 원본 봉투는 코드가 들고 검증기·틀 채우기·정책에 쓴다.
SCOPE_VIEW_KEYS = ("partners", "hs10")  # 사례 머리에 없는, 도구가 실제로 본 상대국·HS10
METRIC_TARGET_KEYS = ("metric", "partner", "period", "baseline_period")  # inputs에서 기호와 대상만
MISSING_DROP_KEYS = ("request_id", "flow")  # 빠진 자료 항목에서 빼는 것(수집 요청 ID, 늘 수입인 흐름). 나머지는 남긴다
PRIORITY = {"MAINTAIN": 3, "HOLD": 2, "MONITOR": 1}
TRUNCATED = "응답이 max_tokens에서 잘렸다(finish_reason length)"
# 도구를 주지 않는 차례에 대화 끝에 붙이는 초안 요청(모든 모드에서 글자까지 같다. 모드 이름·claims 세부는 넣지 않는다).
DRAFT_REQUEST = (
    "[초안 요청] 이 요청에는 도구가 없다. 추가 비교·재조회는 더 할 수 없고, 도구를 부르면 거부된다. 지금까지 받은 "
    "근거만으로 초안을 쓴다.\n"
    "설명·머리말·마크다운 코드 블록 없이 JSON 객체 하나만 답한다. 답의 첫 글자는 { 이고 마지막 글자는 } 이다.\n"
    '{"review_status": "MAINTAIN|MONITOR|HOLD", "signal_status": {"unit_value": "MAINTAIN|MONITOR|HOLD|NOT_TRIGGERED", '
    '"share": "MAINTAIN|MONITOR|HOLD|NOT_TRIGGERED"}, "claims": [시스템 지침의 claims 쓰는 법대로], '
    '"narrative": "한국어 설명", "hypotheses": ["확인되지 않은 가설 문장"]}')
PARTNER_RE = re.compile(r"^[A-Z]{2}$")
MONTH_RE = re.compile(r"^\d{6}$")

TOOL_DESCRIPTIONS = {
    "check_comparability": "사례의 기간·요청 완료·단위·HS 버전·분모·하위자료(HS10)의 존재 상태를 본다. 판정을 내리지 않는다.",
    "get_history": "대상 HS6·상대국의 이력과 전년동월 비교(단가·점유율 지표)를 근거 ID와 함께 본다.",
    "compare_partners": "사전에 허용된 비교국을 같은 HS6·월·기준으로 비교한다. partners를 주면 그 가운데 일부만 본다.",
    "decompose_hs": "두 시점의 HS10 하위품목으로 단가 변화를 within_effect·mix_effect·residual로 나누고 부모 대조를 본다.",
}


def draft_request_message() -> dict:
    return {"role": "user", "content": DRAFT_REQUEST}


def tool_specs(names=MODEL_TOOLS) -> list[dict]:
    """chat completions의 tools 인자(native tool call, 구 개발계획 G4에서 확인한 모양)."""
    specs = []
    for name in names:
        if name not in MODEL_TOOLS:
            raise ValueError(f"모델에게 줄 수 없는 도구: {name}")
        properties = {}
        if name == "compare_partners":
            properties["partners"] = {"type": "array", "items": {"type": "string", "pattern": "^[A-Z]{2}$"},
                                      "maxItems": 5, "description": "비교할 국가코드(허용된 비교국 가운데)"}
        specs.append({"type": "function", "function": {"name": name, "description": TOOL_DESCRIPTIONS[name],
                                                       "parameters": {"type": "object", "properties": properties,
                                                                      "required": []}}})
    return specs


def system_prompt(prompts: dict, mode: str) -> str:
    claims = prompts["claims_freeform"] if mode == "freeform" else prompts["claims_template"]
    return prompts["investigator"].rstrip() + "\n\n" + claims.rstrip() + "\n"


def compact_metric(metric: object) -> object:
    """모델에게 보여 줄 지표: metric_id, 기호와 대상(inputs의 metric·partner·period·baseline_period), 값·단위, 비교 표시
    (있을 때), 근거 ID. 계산 입력 원값(V·Q·hs10_values 등), formula_version, tolerance는 뺀다."""
    if not isinstance(metric, dict):
        return metric
    inputs = metric.get("inputs") if isinstance(metric.get("inputs"), dict) else {}
    view = {"metric_id": metric.get("metric_id")}
    view.update({key: inputs[key] for key in METRIC_TARGET_KEYS if inputs.get(key) is not None})
    view["value"] = metric.get("value")
    view["unit"] = metric.get("unit")
    if metric.get("comparability_flags"):
        view["comparability_flags"] = metric["comparability_flags"]
    view["evidence_ids"] = list(metric.get("evidence_ids") or [])
    return view


def _evidence_ids_in(value: object, found: set) -> set:
    if isinstance(value, str):
        if value.startswith("ev:"):
            found.add(value)
    elif isinstance(value, dict):
        for item in value.values():
            _evidence_ids_in(item, found)
    elif isinstance(value, list):
        for item in value:
            _evidence_ids_in(item, found)
    return found


def compact_envelope(envelope: object) -> object:
    """모델에게 보여 줄 근거(도구 봉투의 모델용 보기). 모든 모드와 Critic이 같은 보기를 받는다(룰북 B2).

    남기는 것: 도구 이름, 도구가 실제로 본 범위 가운데 사례 머리에 없는 것(partners·hs10), 지표(compact_metric),
    비교 가능성(comparability 전체), 빠진 자료(request_id·flow 밖의 키 전부. 도구가 더하는 키도 남는다), 재시도할 수 있는
    오류(있을 때).
    봉투 수준 evidence_ids는 보기의 다른 곳에 이미 나온 근거 ID를 빼고 남긴다. 그래서 봉투의 모든 근거 ID가 보기
    어딘가에 한 번 이상 나온다(freeform 주장과 자료 상태 주장이 인용할 수 있다).
    빼는 것: query_id·snapshot_id·source_kind(사례 머리와 코드가 안다), elapsed_ms, 사례 머리와 같은 범위 값, 지표의
    계산 입력 원값·formula_version·tolerance, 빠진 자료의 request_id·flow. 원본 봉투는 흐름 조정이 그대로 들고
    검증기(R3)·틀 채우기(R1)·정책(P3)에 쓴다. 도구 결과가 커서 누적 토큰 한도(32,000)를 넘지 않게 하려는 것이다
    (실자료 크기 합성 봉투에서 약 0.5~0.85배, 시험 tests/units/I12/test_token_estimate.py)."""
    if not isinstance(envelope, dict):
        return envelope
    view: dict = {"tool": envelope.get("tool")}
    scope = envelope.get("scope") if isinstance(envelope.get("scope"), dict) else {}
    seen_scope = {key: scope[key] for key in SCOPE_VIEW_KEYS if scope.get(key)}
    if seen_scope:
        view["scope"] = seen_scope
    metrics = [compact_metric(m) for m in envelope.get("metrics") or []]
    if metrics:
        view["metrics"] = metrics
    if envelope.get("comparability"):
        view["comparability"] = envelope["comparability"]
    missing = [{key: value for key, value in item.items() if key not in MISSING_DROP_KEYS} if isinstance(item, dict)
               else item for item in envelope.get("missingness") or []]
    if missing:
        view["missingness"] = missing
    shown = _evidence_ids_in(view, set())
    rest = [e for e in envelope.get("evidence_ids") or [] if e not in shown]
    if rest:
        view["evidence_ids"] = rest
    if envelope.get("retryable_error") is not None:
        view["retryable_error"] = envelope["retryable_error"]
    return view


def dumps_for_model(value: object) -> str:
    """모델에게 보내는 JSON 글. Decimal은 원문 표기의 숫자로 쓴다."""
    return trace_log.dumps(value)


def case_message(case: dict, evidence: list, required: list | None, remaining: dict) -> str:
    """조사자의 첫 사용자 메시지. 모드를 받지 않는다(모드 사이에 같은 글이어야 한다, 룰북 B2)."""
    lines = ["[사례]", dumps_for_model({k: case.get(k) for k in ("case_id", "hs6", "partner", "month", "baseline_month",
                                                               "signals", "snapshot_id")})]
    if required:
        lines += ["[필수 근거(공개 정책)]", dumps_for_model(required)]
    lines += ["[이미 받은 근거(도구 봉투)]", dumps_for_model([compact_envelope(e) for e in evidence]),
              f"[남은 횟수] 추가 비교 {remaining.get('comparisons', 0)}회, 모델 요청 {remaining.get('model_requests', 0)}회",
              "필요하면 도구로 추가 비교를 하고, 아니면 초안 JSON을 답하라."]
    return "\n".join(lines)


def initial_messages(prompts: dict, case: dict, mode: str, evidence: list, required: list | None,
                     remaining: dict) -> list[dict]:
    return [{"role": "system", "content": system_prompt(prompts, mode)},
            {"role": "user", "content": case_message(case, evidence, required, remaining)}]


def assistant_message(message: dict) -> dict:
    """모델이 도구를 부른 응답을 대화에 그대로 되돌려 넣는 메시지."""
    out = {"role": "assistant", "content": message.get("content") or ""}
    if message.get("tool_calls"):
        out["tool_calls"] = message["tool_calls"]
    return out


def tool_result_message(call_id: str | None, tool: str, result: object) -> dict:
    return {"role": "tool", "tool_call_id": call_id or "", "name": tool, "content": dumps_for_model(result)}


def feedback_message(problems: list, critic: dict | None, findings: list | None, remaining: dict) -> dict:
    """수정 단계(1회) 지시. 스키마 문제·Critic 지적·검증기 findings를 받아 한 번만 고친다."""
    lines = ["[수정 단계] 아래 지적을 반영해 초안을 한 번만 고쳐 쓴다. 이번이 마지막 수정 기회다."]
    if problems:
        lines += ["[초안 형식 문제]", dumps_for_model(problems)]
    if critic:
        lines += ["[검수자(Critic) 지적]", dumps_for_model({k: critic.get(k) for k in ("findings", "requery")})]
    if findings:
        lines += ["[검증기 지적]", dumps_for_model(findings)]
    lines += [f"[남은 횟수] 재조회 {remaining.get('requeries', 0)}회, 모델 요청 {remaining.get('model_requests', 0)}회",
              "재조회가 필요하면 도구로 하고, 아니면 고친 초안 JSON 하나만 답하라."]
    return {"role": "user", "content": "\n".join(lines)}


def parse_tool_calls(message: dict) -> list[dict]:
    """모델의 tool_calls를 [{id, tool, args, error}]로 바꾼다. error가 있으면 그 호출은 하지 않는다."""
    calls = []
    for raw in message.get("tool_calls") or []:
        function = (raw or {}).get("function") or {}
        name, error, args = function.get("name"), None, {}
        try:
            parsed = json.loads(function.get("arguments") or "{}", parse_float=Decimal)
            args = parsed if isinstance(parsed, dict) else None
        except (TypeError, ValueError):
            args = None
        if name not in MODEL_TOOLS:
            error = "허용 밖 도구"
        elif args is None:
            error = "인자가 JSON 객체가 아니다"
        else:
            allowed = {"partners"} if name == "compare_partners" else set()
            partners = args.get("partners", [])
            if set(args) - allowed:
                error = "허용 밖 인자"
            elif not isinstance(partners, list) or len(partners) > 5 or \
                    not all(isinstance(p, str) and PARTNER_RE.match(p) for p in partners):
                error = "partners는 2자리 국가코드 최대 5개다"
        calls.append({"id": (raw or {}).get("id"), "tool": name, "args": args if error is None else {},
                      "error": error})
    return calls


def _strip_fence(text: str) -> str:
    text = text.strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.S)
    return match.group(1) if match else text


def _claim_problems(claims: object, mode: str) -> list[str]:
    if not isinstance(claims, list):
        return ["claims는 목록이다"]
    problems = []
    for index, claim in enumerate(claims):
        where = f"claims[{index}]"
        if not isinstance(claim, dict):
            problems.append(f"{where}는 객체다")
            continue
        if claim.get("claim_type") not in CLAIM_TYPES:
            problems.append(f"{where}.claim_type이 값 집합 밖이다")
        if mode == "freeform":
            missing = [f for f in CLAIM_FIELDS if f not in claim]
            if missing:
                problems.append(f"{where}에 필드가 없다: {', '.join(missing)}")
                continue
            if not all(isinstance(claim[f], str) and claim[f] for f in ("claim_id", "hs6", "partner", "metric", "text")):
                problems.append(f"{where}의 claim_id·hs6·partner·metric·text는 빈 문자열이 아닌 문자열이다")
            if not isinstance(claim["period"], str) or not MONTH_RE.match(claim["period"]):
                problems.append(f"{where}.period는 YYYYMM이다")
            if claim["baseline_period"] is not None and (not isinstance(claim["baseline_period"], str)
                                                         or not MONTH_RE.match(claim["baseline_period"])):
                problems.append(f"{where}.baseline_period는 YYYYMM이거나 null이다")
            if claim["direction"] not in DIRECTIONS:
                problems.append(f"{where}.direction이 값 집합 밖이다")
            if claim["unit"] is not None and not isinstance(claim["unit"], str):
                problems.append(f"{where}.unit은 문자열이거나 null이다")
            value = claim["value"]
            if isinstance(value, bool) or not (value is None or isinstance(value, (int, Decimal, str))):
                problems.append(f"{where}.value는 수·문자열·null이다")
            if not isinstance(claim["evidence_ids"], list) or \
                    not all(isinstance(e, str) and e.startswith("ev:") for e in claim["evidence_ids"]):
                problems.append(f"{where}.evidence_ids는 ev: 근거 ID 목록이다")
        else:
            refs = [claim.get("metric_id"), claim.get("evidence_id")]
            if sum(isinstance(r, str) and bool(r) for r in refs) != 1:
                problems.append(f"{where}는 metric_id나 evidence_id 하나로 근거를 가리킨다")
            elif isinstance(claim.get("evidence_id"), str) and not claim["evidence_id"].startswith("ev:"):
                problems.append(f"{where}.evidence_id는 ev: 근거 ID다")
    return problems


def check_draft(draft: object, mode: str, signals: dict) -> list[str]:
    """초안 형식 검사. 문제 목록을 돌려준다(빈 목록이면 통과). 초안을 고치지 않는다. signals는 받기만 한다(허용 상태
    조합은 status_notes가 본다)."""
    if not isinstance(draft, dict):
        return ["초안은 JSON 객체다"]
    problems = [f"{key}가 없다" for key in DRAFT_KEYS if key not in draft]
    if problems:
        return problems
    if draft["review_status"] not in REVIEW_STATUSES:
        problems.append("review_status가 MAINTAIN·MONITOR·HOLD가 아니다")
    status = draft["signal_status"]
    if not isinstance(status, dict) or set(status) != set(SIGNAL_CODES) \
            or any(v not in SIGNAL_STATUSES for v in status.values()):
        problems.append("signal_status는 unit_value·share를 키로 하는 신호별 판정이다")
    problems += _claim_problems(draft["claims"], mode)
    if not isinstance(draft["narrative"], str):
        problems.append("narrative는 문자열이다")
    if not isinstance(draft["hypotheses"], list) or not all(isinstance(h, str) for h in draft["hypotheses"]):
        problems.append("hypotheses는 문자열 목록이다")
    return problems


def status_notes(draft: object, signals: dict) -> list[str]:
    """허용 상태 조합의 관찰(검증기 부류, 흐름을 바꾸지 않는다). 값 집합이 틀린 초안은 check_draft가 막으므로 보지 않는다."""
    if not isinstance(draft, dict):
        return []
    status = draft.get("signal_status")
    if not isinstance(status, dict) or set(status) != set(SIGNAL_CODES) \
            or any(v not in SIGNAL_STATUSES for v in status.values()):
        return []
    notes = []
    triggered = [code for code in SIGNAL_CODES if (signals or {}).get(code) == "TRIGGERED"]
    for code in SIGNAL_CODES:
        if (code in triggered) == (status[code] == "NOT_TRIGGERED"):
            notes.append(f"signal_status.{code}가 발동 여부({(signals or {}).get(code)})와 맞지 않는다")
    judged = [status[c] for c in triggered if status[c] in PRIORITY]
    if judged and draft.get("review_status") in PRIORITY \
            and draft["review_status"] != max(judged, key=PRIORITY.__getitem__):
        notes.append("review_status가 신호별 판정을 MAINTAIN > HOLD > MONITOR로 묶은 값과 다르다")
    return notes


def parse_draft(content: str, mode: str, signals: dict) -> tuple[dict | None, list[str]]:
    """모델 답을 초안으로 읽고 형식을 검사한다. 읽지 못하면 (None, 문제)다."""
    try:
        draft = json.loads(_strip_fence(content or ""), parse_float=Decimal)
    except ValueError:
        return None, ["초안이 JSON 객체 하나가 아니다"]
    problems = check_draft(draft, mode, signals)
    if isinstance(draft, dict):
        draft = {key: draft[key] for key in DRAFT_KEYS if key in draft}
    return (draft if isinstance(draft, dict) else None), problems


def step(client: model_client.ModelClient, messages: list[dict], *, stage: str, mode: str, signals: dict,
         allow_tools: bool) -> dict:
    """조사자 한 차례. 돌려주는 값: {"kind": "tool_calls", "message", "calls", "truncated"} 또는
    {"kind": "draft", "message", "draft"(없으면 None), "problems", "status_notes", "truncated"}. 도구를 주지 않았는데
    부르면 도구 호출로 돌려주고, 흐름 조정이 그 시도를 막는다. 잘린 응답(finish_reason length)의 초안은 형식 문제다.
    allow_tools가 거짓이면 messages 끝에 초안 요청 메시지(DRAFT_REQUEST)를 붙이고(대화에 남는다) tools 없이 보낸다."""
    if allow_tools:
        answer = client.chat(messages, stage=stage, tools=tool_specs())
    else:
        messages.append(draft_request_message())
        answer = client.chat(messages, stage=stage, tools=None, json_output=True)
    message = answer["message"]
    truncated = answer.get("finish_reason") == "length"
    if message.get("tool_calls"):
        return {"kind": "tool_calls", "message": message, "calls": parse_tool_calls(message), "truncated": truncated}
    draft, problems = parse_draft(message.get("content") or "", mode, signals)
    if truncated:
        problems = [TRUNCATED] + problems
    return {"kind": "draft", "message": message, "draft": draft, "problems": problems,
            "status_notes": status_notes(draft, signals), "truncated": truncated}


def run(inp: object) -> object:
    """기록 재생(단위 I8)으로 조사자 한 차례를 돈다(키·네트워크 없음).

    입력: {"case": 사례, "mode": 모드, "evidence": [도구 봉투], "required_evidence": 목록(선택),
    "remaining": {"comparisons", "model_requests"}(선택), "allow_tools": 참/거짓, "stage": 단계(선택),
    "replay": [trace 레코드], "config_dir"(선택)}.
    출력: {"kind": "tool_calls", "calls": [...]} 또는 {"kind": "draft", "draft": 초안 또는 null, "problems": [...],
    "status_notes": [...]}(status_notes는 허용 상태 조합의 관찰로, 막지 않는다).
    """
    if not isinstance(inp, dict) or inp.get("mode") not in MODES or not isinstance(inp.get("case"), dict):
        raise ValueError("입력은 {case, mode, evidence[], replay[], ...}다")
    config = model_client.load_model_config(inp.get("config_dir"))
    clock = replay.ReplayClock()
    budget = model_client.Budget(config.limits, clock.now_ms(), config.settings.end_reserve_ms)
    client = model_client.ModelClient(config.settings, budget, replay.ReplayTransport(inp.get("replay") or [], clock),
                                      trace_log.NullSink(), clock_ms=clock.now_ms,
                                      sleep_ms=clock.sleep_ms)
    case = inp["case"]
    messages = initial_messages(config.prompts, case, inp["mode"], inp.get("evidence") or [],
                                inp.get("required_evidence"), inp.get("remaining") or {})
    result = step(client, messages, stage=inp.get("stage", "basic"), mode=inp["mode"],
                  signals=case.get("signals") or {}, allow_tools=bool(inp.get("allow_tools")))
    if result["kind"] == "tool_calls":
        return {"kind": "tool_calls", "calls": result["calls"]}
    return {"kind": "draft", "draft": result["draft"], "problems": result["problems"],
            "status_notes": result["status_notes"]}
