"""단위 I11 Critic.

단위 ID: I11
도메인명: workflow_critic
소유: M
입력: 초안 + 근거
출력: 구조화된 지적·재조회 요청
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.runlog, tradesentry.workflow

Critic은 도구를 부르지 않으므로 허용 import에 tradesentry.tools를 넣지 않는다.
허용 import에 tradesentry.runlog를 더했다(MT4): Decimal 표기를 지키는 JSON 쓰기(단위 L1 dumps)를 쓴다(S0 계층 안).

Critic(별도 문맥의 검수자)은 조사자가 받은 근거와 초안만 보고 누락·반대 설명·비교조건을 지적한다(개발 플랜 §6.7).
- 같은 모델을 새 대화(시스템 지침 critic.txt + 사례·초안·근거 한 메시지)로 부른다. 요청에 tools를 넣지 않는다.
  그래도 답에 도구 호출이 오면 실행하지 않고 문제로만 적는다.
- 재조회 요청은 조사자가 수정 단계에서 실행한다. 여기서는 형식만 거른다: 모델이 부를 수 있는 도구 넷과 좁은 인자
  (단위 I10 규칙), 최대 개수(설정의 revision_requeries, 조정값 2).
- 답을 읽지 못하면 지적 없음(needs_revision=false)으로 돌리고 문제를 적는다. Critic의 답은 판정을 바꾸지 않고, 수정
  단계를 열지 정하는 입력일 뿐이다. 실행 상태(자료 계약 §3.3)를 새로 만들지 않는다.
- 답이 max_tokens에서 잘렸으면(finish_reason length) 문제 목록 맨 앞에 적는다(흐름 조정이 trace에 남긴다). 잘린 답도
  읽을 수 있는 만큼은 위 규칙대로 읽는다.
- Critic 메시지에는 모드 이름이 없다(사례·근거·초안만). 모드 사이 차이를 만들지 않는다(룰북 B2).
- Critic이 보는 근거는 조사자의 모델용 보기(단위 I10 compact_envelope)에서 지표마다의 근거 ID 목록을 걷어 봉투마다 한
  목록(중복 없음)으로 모은 것이다(evidence_view). 근거 ID와 metric_id는 하나도 잃지 않는다. Critic은 근거의 짝을
  대조하지 않고(그 일은 검증기 R3), 누락·반대 설명·비교조건·근거에 없는 ID를 지적하므로 목록 하나로 충분하다. 조사자의
  대화보다 짧아 사례 누적 토큰(32,000)을 덜 쓴다. full·freeform이 같은 보기를 받는다.
"""
import json
import re
from decimal import Decimal

from tradesentry.runlog import trace as trace_log
from tradesentry.workflow import investigator
from tradesentry.workflow import model_client
from tradesentry.workflow import replay

FINDING_KINDS = ("missing_evidence", "alternative_explanation", "comparison_condition", "unsupported_claim",
                 "status_conflict")
REVIEW_KEYS = ("findings", "requery", "needs_revision", "problems")
TRUNCATED = "Critic 답이 max_tokens에서 잘렸다(finish_reason length)"


def evidence_view(envelope: object) -> object:
    """Critic용 근거 보기: 조사자 보기에서 지표의 근거 ID 목록을 걷어 봉투마다 한 목록(나온 순서, 중복 없음)으로 모은다."""
    view = investigator.compact_envelope(envelope)
    if not isinstance(view, dict):
        return view
    metrics = view.get("metrics") or []
    ids = [e for m in metrics if isinstance(m, dict) for e in m.get("evidence_ids") or []]
    ids += view.get("evidence_ids") or []
    out = {key: value for key, value in view.items() if key not in ("metrics", "evidence_ids", "retryable_error")}
    if metrics:
        out["metrics"] = [{k: v for k, v in m.items() if k != "evidence_ids"} if isinstance(m, dict) else m
                          for m in metrics]
    unique = list(dict.fromkeys(ids))
    if unique:
        out["evidence_ids"] = unique
    if "retryable_error" in view:
        out["retryable_error"] = view["retryable_error"]
    return out


def messages(prompts: dict, case: dict, draft: dict | None, evidence: list, reference: str | None = None) -> list[dict]:
    lines = [
        "[사례]", trace_log.dumps({k: case.get(k) for k in ("case_id", "hs6", "partner", "month", "baseline_month",
                                                           "signals")}),
        "[조사자가 받은 근거]", trace_log.dumps([evidence_view(e) for e in evidence])]
    if reference:
        lines.append(reference)  # 조사자가 받은 규칙 참고값과 같은 글(AS2 6회차)
    lines += ["[조사자의 초안]", trace_log.dumps(draft), "지적과 재조회 요청을 JSON 객체 하나로 답하라."]
    body = "\n".join(lines)
    return [{"role": "system", "content": prompts["critic"]}, {"role": "user", "content": body}]


def _strip_fence(text: str) -> str:
    text = (text or "").strip()
    match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.S)
    return match.group(1) if match else text


def parse_review(content: str, max_requery: int) -> dict:
    """Critic 답을 {findings, requery, needs_revision, problems}로 읽는다. 형식이 틀린 항목은 버리고 문제로 적는다."""
    try:
        raw = json.loads(_strip_fence(content), parse_float=Decimal)
    except ValueError:
        raw = None
    if not isinstance(raw, dict):
        return {"findings": [], "requery": [], "needs_revision": False, "problems": ["Critic 답이 JSON 객체가 아니다"]}
    problems: list[str] = []
    findings = []
    for index, item in enumerate(raw.get("findings") or []):
        if not isinstance(item, dict) or item.get("kind") not in FINDING_KINDS or not isinstance(item.get("text"), str):
            problems.append(f"findings[{index}]의 kind·text 형식이 틀려 버렸다")
            continue
        refs = item.get("claim_refs") or []
        findings.append({"kind": item["kind"], "text": item["text"],
                         "claim_refs": [r for r in refs if isinstance(r, str)] if isinstance(refs, list) else []})
    requery = []
    for index, item in enumerate(raw.get("requery") or []):
        if not isinstance(item, dict):
            problems.append(f"requery[{index}]가 객체가 아니다")
            continue
        args = item.get("args") if isinstance(item.get("args"), dict) else {}
        call = investigator.parse_tool_calls({"tool_calls": [
            {"id": None, "function": {"name": item.get("tool"), "arguments": trace_log.dumps(args)}}]})[0]
        if call["error"] is not None:
            problems.append(f"requery[{index}]를 버렸다({call['error']})")
            continue
        requery.append({"tool": call["tool"], "args": call["args"],
                        "reason": item["reason"] if isinstance(item.get("reason"), str) else ""})
    if len(requery) > max_requery:
        problems.append(f"재조회 요청 {len(requery)}개 가운데 앞의 {max_requery}개만 남겼다")
        requery = requery[:max_requery]
    needs = raw.get("needs_revision")
    if not isinstance(needs, bool):
        problems.append("needs_revision이 참/거짓이 아니어서 지적·재조회 요청이 있는지로 정했다")
        needs = bool(findings or requery)
    return {"findings": findings, "requery": requery, "needs_revision": needs, "problems": problems}


def review(client: model_client.ModelClient, prompts: dict, case: dict, draft: dict | None, evidence: list,
           max_requery: int, reference: str | None = None) -> dict:
    """Critic 한 차례(모델 요청 1회, 도구 없음). reference는 조사자에게 실은 규칙 참고값 문구(있을 때)."""
    answer = client.chat(messages(prompts, case, draft, evidence, reference), stage="critic", tools=None)
    message = answer["message"]
    result = parse_review(message.get("content") or "", max_requery)
    if answer.get("finish_reason") == "length":
        result["problems"].insert(0, TRUNCATED)
    if message.get("tool_calls"):
        result["problems"].append("Critic이 도구를 부르려 했다(실행하지 않음)")
    return result


def run(inp: object) -> object:
    """기록 재생(단위 I8)으로 Critic 한 차례를 돈다(키·네트워크 없음).

    입력: {"case": 사례, "draft": 초안, "evidence": [도구 봉투], "replay": [trace 레코드], "config_dir"(선택)}.
    출력: {"findings": [...], "requery": [...], "needs_revision": 참/거짓, "problems": [...]}.
    """
    if not isinstance(inp, dict) or not isinstance(inp.get("case"), dict):
        raise ValueError("입력은 {case, draft, evidence[], replay[]}다")
    config = model_client.load_model_config(inp.get("config_dir"))
    clock = replay.ReplayClock()
    budget = model_client.Budget(config.limits, clock.now_ms(), config.settings.end_reserve_ms)
    client = model_client.ModelClient(config.settings, budget, replay.ReplayTransport(inp.get("replay") or [], clock),
                                      trace_log.NullSink(), clock_ms=clock.now_ms, sleep_ms=clock.sleep_ms)
    return review(client, config.prompts, inp["case"], inp.get("draft"), inp.get("evidence") or [],
                  config.limits.revision_requeries)
