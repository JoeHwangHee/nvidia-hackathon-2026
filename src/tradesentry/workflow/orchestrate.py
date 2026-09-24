"""단위 I12 흐름 조정.

단위 ID: I12
도메인명: workflow_orchestrate
소유: M
입력: 사례·모드
출력: 조사자 → Critic → 수정 1회 상태 기계
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.runlog, tradesentry.policy, tradesentry.tools, tradesentry.validator, tradesentry.reports, tradesentry.workflow

사례 1건을 모드대로 끝까지 돌리는 상태 기계다(개발 플랜 §6.6·§6.7, 룰북 B2, 자료 계약 §3.3·§8.1).

흐름(checklist 밖 모드)
1. basic: check_comparability → (비교 가능하면) get_history → 조사자 추가 비교(모델 도구 호출, 최대 2회) → 초안.
   초안 형식 검사(단위 I10: 값 집합·형식·자료형, 잘린 응답)와 보고서 쪽 스키마 검사(검증기 자리)에 실패하면 Critic을
   건너뛰고 수정 단계로 간다. 허용 상태 조합(발동 여부·집계)은 형식 문제가 아니다: 조사자가 관찰(status_notes)로
   돌려주면 trace에 남기고, 판정은 검증기(R3 STATUS_INCONSISTENT)가 모드 규칙대로 한다(full·agent 차단, freeform 기록).
2. critic(full·freeform만): Critic 한 차례(도구 없음). agent는 Critic이 없다. critic_used는 Critic 단계를 연 때 참이다.
3. verify_evidence(기본 경로의 예약 1회) → 검증기 판정. 수정이 필요 없으면(스키마 통과, 검증기 통과 또는 freeform,
   Critic이 수정을 요청하지 않음) 여기서 COMPLETED.
4. revision(1회): 조사자가 지적을 받고 재조회(최대 2회) 뒤 고친 초안을 쓴다. Critic은 다시 부르지 않는다. 비교 불가
   사례는 수정 단계에서도 도구를 주지 않는다(조기 종료, 개발 플랜 §6.6).
5. final: verify_evidence(최종 예약 1회) → 스키마·검증기 판정. 두 번째 수정 단계는 없다: 스키마 실패는
   SCHEMA_INVALID, 검증기 차단(freeform 밖)은 VALIDATOR_BLOCKED로 INVALID다(budget_block revision_limit).

checklist: 모델 없이 check_comparability → get_history → decompose_hs(단가 신호 발동) → compare_partners(신호 발동)
→ 정책으로 초안 → verify_evidence → 스키마·검증기. 막히면 수정 없이 곧바로 INVALID다(결정 D1). 비교 불가면 조회를
건너뛴다.

코드가 강제하는 것(프롬프트가 아니다)
- 한도 확인 순서: 전체 deadline이 먼저다. 모든 도구 시도·모델 요청 앞에서 deadline을 보고, 닿으면 TIMEOUT
  (원인 DEADLINE)으로 멈춘다. 완료 직전에도 한 번 더 본다. 모델 요청·토큰 한도는 단위 I7이 본다.
- 도구 시도의 단계별 몫(설정 limits, 조정값): 기본 경로 5회(verify_evidence 1회 예약 포함, 그 가운데 조사자 추가
  비교 최대 2회), 수정 단계 재조회 2회, 최종 verify_evidence 1회. 합이 도구 8회다. 몫을 넘는 시도와 형식이 틀린
  모델 도구 호출은 도구를 부르지 않고 거부 결과를 모델에게 돌려준다(budget_block).
- 비교 불가 조기 종료: check_comparability 봉투의 comparability.comparable(참거짓)이 거짓이면 get_history를 건너뛰고,
  기본·수정 단계 모두 조사자 요청에 도구를 주지 않는다. 그래도 모델이 도구를 부르면 부르지 않고 막는다(budget_block
  not_comparable). 이 키가 없거나 참거짓이 아니면 CODE_ERROR로 멈춘다(조기 종료가 조용히 꺼지지 않게).
- budget_block 종류: {몫}_limit(comparison·requery·basic·verify·final_verify), not_comparable, invalid_call,
  revision_limit(두 번째 수정 단계), 그리고 도구 예산 자리(단위 I6)가 준 거부 사유.
- tool_attempts 세는 법은 COUNT_BLOCKED_TOOL_ATTEMPTS 한 곳이 정한다(결정 기록 ③). 2026-09-25(금) 사용자 결정 6
  (가)대로 거짓: 도구에 닿아 예산을 쓴 시도만 센다(항상 8 이하). 막힌 시도는 trace의 budget_block에만 남는다(결정 기록
  docs/tracking/decisions/20260925-0847-user-decision-morning-shared-promises.md). 흐름의 몫·도구 예산 판정은 이 값과 관계없다. 몫을 통과한 시도는 도구 예산 자리(단위 I6)에 한 번 더
  묻는다(도구 8회, 같은 인자 재호출 등은 I6 규칙). 실행한 도구는 8회를 넘지 않는다.
- 대조할 것이 없으면 verify_evidence를 부르지 않는다: 초안에서 뽑은 metric_id와 근거 ID가 모두 0개면(단위 I5가
  invalid_args로 거부하면서 시도 1회를 쓰는 호출) 시도로 세지 않고 건너뛰며, 다음 validator_result에 verify_skipped
  참을 남긴다. 몫(특히 최종 verify_evidence 1회)을 쓰지 않는다. 도구 봉투의 retryable_error는 도구 쪽 결과라 모델
  제공자 원인 코드(PROVIDER_*)가 되지 않는다(결정 기록 ⑯).
- 코드는 모델의 틀린 상태를 고치지 않는다. 형식·검증기 문제는 수정 단계로 보내거나 INVALID로 끝낸다.

다른 작업 단위를 부르는 자리(Ports). unit_ports가 그 단위들의 run을 부르는 얇은 배선을 한곳에 모았다. 보고서·
검증기(MT3 R1~R4)와 정책(MT1 P3~P5)은 각 작업 브랜치에 커밋된 입출력에 맞췄고(병합 전 대조), 도구 5개·도구 예산(MT2)은
아직 없어 제안 모양이다 `[미확인]`. 정책 객체(K4)와 근거 행 풀기(K3)는 사례 조사 조립(로드맵 AS2)이 인자로 넘긴다.
흐름 조정 자체는 Ports만 본다.

기록: 사례 1건의 trace 이벤트(단위 L1)를 sink로 내고, 끝에 실행 결과 기록의 실행 쪽 키(단위 L2)를 만든다. 멈춘 실행의
errors는 원인 분류 코드 항목 하나다(단위 L3: 원인, 누적 시도, 마지막 정상 근거). COMPLETED가 아니면 보고서를 돌려주지
않는다(검증기를 통과하지 못한 보고서는 공유 대상이 아니다).
- 실행 전에 정해지는 키(단위 L2 check_static)는 흐름을 시작하기 전에 검사한다. 틀리면 모델 요청·도구를 쓰기 전에
  ValueError로 멈춘다(모드·사례 키 검사와 같다). 필수 근거(단위 P5) 계산은 흐름 안에서 해 실패도 CODE_ERROR로 남긴다.
- trace 추가 값: state_change의 draft·revised에 problem_list(형식 문제)·status_notes(허용 상태 관찰), after_critic에
  Critic problems, validator_result에 rejected_requests(틀 채우기가 채우지 못해 버린 요청, 단위 R1 rejected).
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable

from tradesentry.policy import case_aggregate as policy_case_aggregate
from tradesentry.policy import required_evidence as policy_required_evidence
from tradesentry.policy import signal_decide as policy_signal_decide
from tradesentry.reports import claims as report_claims
from tradesentry.reports import render_ko as report_render
from tradesentry.runlog import cause_codes, run_record
from tradesentry.runlog import trace as trace_log
from tradesentry.tools import budget as tool_budget
from tradesentry.tools import check_comparability, compare_partners, decompose_hs, get_history, verify_evidence
from tradesentry.validator import gate as validator_gate
from tradesentry.validator import validate as validator_validate
from tradesentry.workflow import critic, investigator, model_client, replay

MODES = ("checklist", "agent", "full", "freeform")
CRITIC_MODES = ("full", "freeform")
TOOL_UNITS = {"check_comparability": check_comparability, "get_history": get_history,
              "compare_partners": compare_partners, "decompose_hs": decompose_hs, "verify_evidence": verify_evidence}
CASE_KEYS = ("case_id", "hs6", "partner", "month", "baseline_month", "signals", "snapshot_id", "policy_version")
PRIORITY = investigator.PRIORITY
BUDGET_LIMIT_KEYS = ("tool_attempts", "basic_tool_attempts", "revision_stages", "revision_requeries", "final_verify")
# 실행 결과 기록 tool_attempts에 막힌 시도(budget_block)를 셀지(결정 기록 ③). 2026-09-25(금) 사용자 결정 6 (가):
# 거짓 = 도구에 닿아 예산을 쓴 시도만 센다. 참이면 막힌 시도까지 센다. 바꾸는 곳은 이 한 줄이다(시험이 두 값을 다 돈다).
COUNT_BLOCKED_TOOL_ATTEMPTS = False
# 판정 정책 P3 근거 상태의 필수 비교(comparisons)와 그 비교를 하는 도구 `[미확인]`: 조립(AS2)에서 확정한다.
COMPARISON_TOOLS = {"comparability": "check_comparability", "partners": "compare_partners",
                    "country_and_world": "get_history"}
FAMILY_COMPARISONS = {"unit_value": ("comparability", "partners"),
                      "share": ("comparability", "partners", "country_and_world")}


@dataclass
class Ports:
    """흐름 조정이 부르는 다른 단위 자리.

    tool(이름, 인자) -> 봉투 / budget(실행한 시도 목록, 후보) -> {"allowed", "reason"} /
    build_report({"case","mode","run_id","draft","evidence"}) -> {"report": 보고서, "rejected": 버린 요청 목록} /
    check_report({"case","mode","report","evidence","revision_used"}) -> {"schema_ok", "validator_ok", "findings"} /
    checklist_draft({"case","evidence"}) -> 초안 / required_evidence(사례) -> 필수 근거(단위 P5 출력, 없으면 None)
    """

    tool: Callable[[str, dict], dict]
    budget: Callable[[list, dict], dict]
    build_report: Callable[[dict], dict]
    check_report: Callable[[dict], dict]
    checklist_draft: Callable[[dict], dict]
    required_evidence: Callable[[dict], object] | None = None


@dataclass(frozen=True)
class RunContext:
    """사례 실행 1건의 입력. run_id는 부르는 쪽이 확보한 실행명(단위 L2 reserve_run_dir)이다."""

    run_id: str
    case: dict
    mode: str
    dataset: str
    rulebook_version: str
    grouping_version: str
    code_version: str


def _scope(case: dict) -> dict:
    return {k: case.get(k) for k in ("hs6", "partner", "month", "baseline_month")}


# 신호 계열별 주장 metric 기호(자료 계약 §9.4 표). checklist 틀 채우기에서 어떤 검증된 값을 주장할지 고를 때 쓴다.
FAMILY_METRICS = {"unit_value": ("U", "r_U", "within_effect", "mix_effect", "residual"), "share": ("s", "d_s")}
FAMILY_PREFIXES = {"unit_value": ("U@", "r_U@", "w@"), "share": ()}


def _metrics_of(evidence: list) -> list:
    return [m for e in evidence if isinstance(e, dict) for m in (e.get("metrics") or []) if isinstance(m, dict)]


def _missing_items(evidence: list) -> list:
    """봉투들의 missingness 항목(단위 K3 모양: evidence_id·request_id·partner_code·hs_code·month·flow·
    observation_status). 여러 봉투에 같은 항목이 나오면 한 번만 둔다."""
    items, seen = [], set()
    for envelope in evidence:
        for item in (envelope.get("missingness") or []) if isinstance(envelope, dict) else []:
            if not isinstance(item, dict):
                continue
            key = trace_log.canonical_sha256(item)
            if key not in seen:
                seen.add(key)
                items.append(item)
    return items


def _statuses_of(evidence: list) -> list:
    """봉투의 missingness 항목을 단위 R1의 자료 상태 항목으로 옮긴다(근거 ID 하나에 항목 하나, status_id = 근거 ID).

    항목의 상대국 키는 partner_code, 근거 ID는 evidence_id(하나)다(단위 K3·MT2 도구 공통 틀). 옛 모양(partner·
    evidence_ids 목록)도 읽는다. hs_code가 10자리면 hs10이다. 부모 HS6 행이 있는 키에서 HS10 하위 자료만 빠진 경우
    (C형, 빠진 HS10 코드마다 observation_status@<HS10>)를 가려 hs10을 채우는 일은 조립(AS2)의 몫이다 `[미확인]`."""
    statuses, seen = [], set()
    for item in _missing_items(evidence):
        code = str(item.get("hs_code") or item.get("hs6") or "")
        refs = item.get("evidence_ids") if isinstance(item.get("evidence_ids"), list) else [item.get("evidence_id")]
        for ev in refs:
            if isinstance(ev, str) and ev not in seen:
                seen.add(ev)
                statuses.append({"status_id": ev, "hs6": item.get("hs6") or code[:6],
                                 "partner": item.get("partner_code") or item.get("partner"),
                                 "period": item.get("month") or item.get("period"),
                                 "hs10": item.get("hs10") or (code if len(code) == 10 else None),
                                 "observation_status": item.get("observation_status"), "evidence_ids": [ev],
                                 "baseline_period": item.get("baseline_period")})
    return statuses


def comparison_marks(evidence: list) -> dict:
    """P3 근거 상태 comparisons의 흐름 쪽 표시. 필수 비교마다 그 도구의 봉투를 받았으면(retryable_error 없음) done,
    받지 못했으면(비교 불가 조기 종료, 막힌 시도, 부르지 않음, 도구 실패) not_performed다. 빠진 관측 때문에 결과를 얻지
    못한 incomplete는 봉투 내용을 읽는 조립(AS2)의 변환이 가린다 `[미확인]`."""
    marks = {}
    for comparison, tool in COMPARISON_TOOLS.items():
        received = [e for e in evidence if isinstance(e, dict) and e.get("tool") == tool]
        marks[comparison] = "done" if any(e.get("retryable_error") is None for e in received) else "not_performed"
    return marks


def default_evidence_state(case: dict, evidence: list) -> dict:
    """조립(AS2)의 근거 상태 변환이 없을 때 P3에 넘기는 모양: missingness와 발동 신호 블록의 comparisons만 채운다.

    나머지 키(comparability_issues, 단가의 U_baseline·decomposition·children·rounding_unstable, resolved_after_correction.
    수는 반올림 전 정확값)는 봉투를 읽는 AS2 변환의 몫이라 비워 둔다. P3에는 기본값이 없어 그 키가 없으면 ValueError로
    멈추고, 흐름은 CODE_ERROR로 기록한다(배선 누락이 그럴듯한 판정으로 바뀌지 않게)."""
    marks = comparison_marks(evidence)
    state: dict = {"missingness": _missing_items(evidence)}
    for family, needed in FAMILY_COMPARISONS.items():
        if (case.get("signals") or {}).get(family) == "TRIGGERED":
            state[family] = {"comparisons": {c: marks[c] for c in needed}}
    return state


def policy_thresholds(policy: object) -> list:
    """정책 객체(단위 K4)의 탐지 임계값을 검증기 R3 입력 thresholds 모양(수 목록: 단가 %, 점유율 pp)으로 옮긴다.

    R3는 형식이 틀린 값(float·문자열)을 오류 없이 버려 산문 검사 EX-5(정책 기준값 언급 빼기)가 조용히 꺼지므로, int와
    Decimal만 넘기고 다른 형식이면 ValueError로 드러낸다."""
    thresholds = policy.get("thresholds") if isinstance(policy, dict) else None
    if not isinstance(thresholds, dict):
        raise ValueError("정책 객체에 thresholds가 없다")
    values = []
    for signal in ("unit_value", "share"):
        value = thresholds.get(signal)
        if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
            raise ValueError(f"정책 thresholds.{signal}는 int나 Decimal이다(float·문자열을 넘기지 않는다)")
        values.append(value)
    return values


def _unresolved_triggered(signals: dict | None, signal_status: object) -> bool:
    """발동한 신호의 판정에 MAINTAIN과 HOLD가 섞였나(P4·R3와 같은 기준). 판정 객체가 틀리면 거짓."""
    if not isinstance(signal_status, dict):
        return False
    judged = {signal_status.get(code) for code, fired in (signals or {}).items() if fired == "TRIGGERED"}
    return "MAINTAIN" in judged and "HOLD" in judged


def _requests_of(draft: dict) -> list:
    """틀 채우기 모드 초안의 주장 참조(metric_id·evidence_id)를 단위 R1의 요청({claim_id, metric_id|status_id})으로."""
    requests = []
    for number, claim in enumerate(draft.get("claims") or [], start=1):
        if not isinstance(claim, dict):
            continue
        if isinstance(claim.get("metric_id"), str):
            requests.append({"claim_id": f"c{number}", "metric_id": claim["metric_id"]})
        elif isinstance(claim.get("evidence_id"), str):
            requests.append({"claim_id": f"c{number}", "status_id": claim["evidence_id"]})
    return requests


def checklist_claims(case: dict, evidence: list) -> list:
    """checklist 규칙의 주장 고르기(제안): 발동 신호 계열의 검증된 지표 가운데 사례 품목·상대국·비교월을 가리키는 것,
    그리고 빠진 자료의 자료 상태. 값·단위·근거는 단위 R1이 채운다."""
    triggered = [s for s in FAMILY_METRICS if (case.get("signals") or {}).get(s) == "TRIGGERED"]
    claims = []
    for metric in _metrics_of(evidence):
        inputs = metric.get("inputs") if isinstance(metric.get("inputs"), dict) else {}
        symbol = inputs.get("metric")
        family_hit = any(symbol in FAMILY_METRICS[s] or (isinstance(symbol, str) and symbol.startswith(FAMILY_PREFIXES[s]))
                         for s in triggered)
        if family_hit and inputs.get("period") == case.get("month") and isinstance(metric.get("metric_id"), str):
            claims.append({"claim_type": "value", "metric_id": metric["metric_id"]})
    claims += [{"claim_type": "data_status", "evidence_id": s["status_id"]} for s in _statuses_of(evidence)]
    return claims


def unit_ports(case: dict, mode: str, run_id: str, limits: model_client.RunLimits, *, grouping_version: str,
               policy: object = None, rows: Callable[[list], dict] | None = None,
               evidence_state: Callable[[dict, list], dict] | None = None,
               clock: Callable[[], object] = trace_log.now_kst) -> Ports:
    """다른 트랙·작업 단위의 run을 부르는 배선. 보고서·검증기(MT3 R1~R4, 커밋 b5948c3)와 정책(MT1 P3~P5, 커밋 30931d9),
    도구 예산(MT2 I6, 커밋 be32f6b)은 그 작업 브랜치에 커밋된 입출력에 맞췄다. 도구 5개의 요청 모양은 지금
    {case_id, snapshot_id, scope, args}이고, MT2 공통 틀의 선택 키(policy_version·grouping_version·attempt·envelopes)는
    조립(AS2)에서 맞춘다 `[미확인]`.

    AS2(사례 조사 조립)가 넘겨야 하는 것: policy(단위 K4 정책 객체. checklist의 P3가 쓰고, 탐지 임계값은 검증기 R3
    입력 thresholds로 옮겨 모든 모드에 넘긴다), rows(근거 ID 목록 -> {근거 ID: 스냅샷 행 또는 None}, 단위 K3 자료
    접근층으로 푼다. 검증기 R3의 원본 대조에 쓴다), evidence_state(사례, 봉투 목록 -> P3 근거 상태. 없으면
    default_evidence_state로 missingness·comparisons만 채워 P3가 입력 오류로 멈춘다).
    """
    made = {"reports": 0}
    thresholds = policy_thresholds(policy) if policy is not None else None  # 형식이 틀리면 실행 전에 ValueError

    def tool(name: str, args: dict) -> dict:
        return TOOL_UNITS[name].run({"case_id": case.get("case_id"), "snapshot_id": case.get("snapshot_id"),
                                     "scope": _scope(case), "args": args})

    def budget(executed: list, candidate: dict) -> dict:
        # 한도 키 다섯을 모두 넘긴다(설정 한 곳과 I6가 어긋나지 않게). candidate에는 단계(stage)가 들어 있다.
        return tool_budget.run({"attempts": executed, "candidate": candidate,
                                "limits": {key: getattr(limits, key) for key in BUDGET_LIMIT_KEYS}})

    def build_report(inp: dict) -> dict:
        draft, evidence = inp["draft"], inp["evidence"]
        if mode == "freeform":
            filled = report_claims.run({"mode": mode, "case": case, "claims": draft.get("claims") or []})
        else:
            filled = report_claims.run({"mode": mode, "case": case, "metrics": _metrics_of(evidence),
                                        "statuses": _statuses_of(evidence), "requests": _requests_of(draft)})
        try:
            unresolved = policy_case_aggregate.run({"signals": case.get("signals"),
                                                    "signal_status": draft.get("signal_status")})["unresolved_evidence"]
        except ValueError:
            # 발동 여부와 신호별 판정이 어긋난 초안(허용 상태 밖). 상태를 고쳐 쓰지 않고 보고서를 그대로 만들어 검증기
            # R3가 STATUS_INCONSISTENT로 적게 둔다(full·agent 차단, freeform 기록). 값은 P4·R3와 같은 기준으로 센다.
            unresolved = _unresolved_triggered(case.get("signals"), draft.get("signal_status"))
        made["reports"] += 1
        rendered = report_render.run({
            "report_id": f"{run_id}-report{made['reports']}", "run_id": run_id, "mode": mode,
            "created_at": trace_log.iso_kst(clock()), "policy_version": case.get("policy_version"),
            "snapshot_id": case.get("snapshot_id"), "grouping_version": grouping_version, "case": case,
            "claims": filled["claims"], "narrative": draft.get("narrative"), "hypotheses": draft.get("hypotheses"),
            "review_status": draft.get("review_status"), "signal_status": draft.get("signal_status"),
            "unresolved_evidence": unresolved, "validator_findings": []})
        return {"report": rendered["report"], "rejected": list(filled.get("rejected") or [])}

    def check_report(inp: dict) -> dict:
        report, evidence = inp["report"], inp["evidence"]
        ids = sorted({e for e in (report.get("evidence_ids") or []) if isinstance(e, str)}
                     | {e for env in evidence if isinstance(env, dict) for e in (env.get("evidence_ids") or [])
                        if isinstance(e, str)})
        request = {"case": case, "report": report, "envelopes": evidence, "rows": rows(ids) if rows else {},
                   "run": {"run_id": run_id, "mode": mode, "snapshot_id": case.get("snapshot_id"),
                           "policy_version": case.get("policy_version"), "grouping_version": grouping_version}}
        if thresholds is not None:
            request["thresholds"] = list(thresholds)
        out = validator_validate.run(request)
        findings = out["findings"]
        decision = validator_gate.run({"mode": mode, "findings": findings, "revision_used": inp["revision_used"]})
        return {"schema_ok": not decision["schema_failed"],
                "validator_ok": not [f for f in findings if isinstance(f, dict) and f.get("check") == "validator"],
                "findings": findings}

    def checklist_draft(inp: dict) -> dict:
        evidence = inp["evidence"]
        state = evidence_state(case, evidence) if evidence_state else default_evidence_state(case, evidence)
        decided = policy_signal_decide.run({"policy": policy, "case": case, "evidence": state})
        aggregate = policy_case_aggregate.run({"signals": case.get("signals"),
                                               "signal_status": decided["signal_status"]})
        return {"review_status": aggregate["review_status"], "signal_status": decided["signal_status"],
                "claims": checklist_claims(case, evidence), "narrative": "", "hypotheses": []}

    def required(case_obj: dict) -> object:
        return policy_required_evidence.run({"signals": case_obj.get("signals")})

    return Ports(tool=tool, budget=budget, build_report=build_report, check_report=check_report,
                 checklist_draft=checklist_draft, required_evidence=required)


def _unresolved(signal_status: dict, signals: dict | None = None) -> bool:
    if signals is not None:
        return _unresolved_triggered(signals, signal_status)
    values = set((signal_status or {}).values())
    return "MAINTAIN" in values and "HOLD" in values


def _draft_refs(draft: dict | None) -> dict:
    """verify_evidence에 넘길 근거: 초안이 가리킨 metric_id와 근거 ID(나온 순서, 중복 없음)."""
    metric_ids: list[str] = []
    evidence_ids: list[str] = []
    for claim in (draft or {}).get("claims") or []:
        if not isinstance(claim, dict):
            continue
        if isinstance(claim.get("metric_id"), str) and claim["metric_id"] not in metric_ids:
            metric_ids.append(claim["metric_id"])
        for ref in [claim.get("evidence_id")] + list(claim.get("evidence_ids") or []):
            if isinstance(ref, str) and ref not in evidence_ids:
                evidence_ids.append(ref)
    return {"metric_ids": metric_ids, "evidence_ids": evidence_ids}


class _Flow:
    def __init__(self, ctx: RunContext, ports: Ports, config: model_client.ModelConfig, client, budget, sink, clock_ms):
        self.ctx = ctx
        self.case = ctx.case
        self.signals = ctx.case.get("signals") or {}
        self.mode = ctx.mode
        self.ports = ports
        self.config = config
        self.limits = config.limits
        self.client = client
        self.budget = budget
        self.sink = sink
        self.clock_ms = clock_ms
        self.stage = "basic"
        self.evidence: list = []
        self.executed: list = []
        self.attempts = {"executed": 0, "blocked": 0}  # 도구에 닿은 시도, 막은 시도(tool_attempts는 이 둘로 센다)
        self.used = {"basic": 0, "comparison": 0, "requery": 0, "final_verify": 0}
        self.critic_used = False
        self.revision_used = False
        self.last_good_evidence: list[str] = []
        self.required = None  # 필수 근거(P5)는 orchestrate의 try 안에서 채운다(실패도 기록으로 남게)
        self.rejected: list = []
        self.verify_skipped = False  # 바로 앞 verify_evidence를 대조할 것이 없어 건너뛰었나(다음 validator_result에 남긴다)

    # 한도와 도구 시도 ---------------------------------------------------------------------------------------------
    @property
    def tool_attempts(self) -> int:
        """실행 결과 기록의 tool_attempts(COUNT_BLOCKED_TOOL_ATTEMPTS가 셀 범위를 정한다)."""
        blocked = self.attempts["blocked"] if COUNT_BLOCKED_TOOL_ATTEMPTS else 0
        return self.attempts["executed"] + blocked

    def check_deadline(self) -> None:
        if self.budget.deadline_passed(self.clock_ms()):
            raise model_client.RunStop(cause_codes.DEADLINE, self.stage, "사례 deadline에 닿았다")

    def _allowance_left(self, allowance: str) -> int:
        lim, used = self.limits, self.used
        basic_left = lim.basic_tool_attempts - used["basic"]
        if allowance == "basic":
            return basic_left - 1  # verify_evidence 1회 예약
        if allowance == "comparison":
            return min(lim.investigator_comparisons - used["comparison"], basic_left - 1)
        if allowance == "verify":
            return basic_left
        if allowance == "requery":
            return lim.revision_requeries - used["requery"]
        if allowance == "final_verify":
            return lim.final_verify - used["final_verify"]
        raise ValueError(f"알 수 없는 몫: {allowance}")

    def _consume(self, allowance: str) -> None:
        if allowance in ("basic", "verify"):
            self.used["basic"] += 1
        elif allowance == "comparison":
            self.used["comparison"] += 1
            self.used["basic"] += 1
        else:
            self.used[allowance] += 1

    def refuse(self, tool: str | None, args: dict, source: str, kind: str) -> dict:
        """도구를 부르지 않고 막는다. 시도로는 센다. deadline이 먼저다."""
        self.check_deadline()
        self.attempts["blocked"] += 1
        self.sink.emit("tool_call", self.stage, {"tool": tool, "args": args, "source": source,
                                                 "tool_attempts": self.tool_attempts})
        self.sink.emit("budget_block", self.stage, {"kind": kind, "tool": tool, "tool_attempts": self.tool_attempts})
        return {"blocked": True, "reason": kind}

    def attempt(self, tool: str, args: dict, *, source: str, allowance: str) -> dict:
        """도구 시도 하나. 막히면 {"blocked": True, "reason"}를, 부르면 봉투를 돌려준다."""
        self.check_deadline()
        if self._allowance_left(allowance) <= 0:
            return self.refuse(tool, args, source, f"{allowance}_limit")
        candidate = {"tool": tool, "args": args, "stage": self.stage}
        decision = self.ports.budget(list(self.executed), candidate)
        if not decision.get("allowed"):
            return self.refuse(tool, args, source, str(decision.get("reason") or "tool_budget"))
        self.attempts["executed"] += 1
        self._consume(allowance)
        self.sink.emit("tool_call", self.stage, {"tool": tool, "args": args, "source": source,
                                                 "tool_attempts": self.tool_attempts})
        envelope = self.ports.tool(tool, args)
        self.executed.append(candidate)
        self.evidence.append(envelope)
        ids = envelope.get("evidence_ids") if isinstance(envelope, dict) else None
        if isinstance(ids, list) and ids:
            self.last_good_evidence = [e for e in ids if isinstance(e, str)]
        elapsed = envelope.get("elapsed_ms", 0) if isinstance(envelope, dict) else 0
        self.sink.emit("tool_result", self.stage, {"tool": tool, "ok": True,
                                                   "elapsed_ms": elapsed if isinstance(elapsed, int) else 0,
                                                   "envelope": envelope})
        return envelope

    def verify(self, draft: dict | None, allowance: str) -> None:
        """verify_evidence 예약 차례. 초안이 가리킨 metric_id·근거 ID가 모두 없으면 부르지 않는다(시도·몫을 쓰지 않는다)."""
        refs = _draft_refs(draft)
        self.verify_skipped = not refs["metric_ids"] and not refs["evidence_ids"]
        if self.verify_skipped:
            self.check_deadline()
            return
        self.attempt("verify_evidence", refs, source="code", allowance=allowance)

    # 조사자 ------------------------------------------------------------------------------------------------------
    def remaining(self, tools_enabled: bool = True) -> dict:
        """모델에게 알리는 남은 횟수. 도구를 주지 않는 차례(비교 불가)에는 비교·재조회 0회로 알린다."""
        return {"comparisons": max(0, self._allowance_left("comparison")) if tools_enabled else 0,
                "requeries": max(0, self._allowance_left("requery")) if tools_enabled else 0,
                "model_requests": max(0, self.limits.model_requests - self.budget.model_requests)}

    def investigate(self, messages: list[dict], *, allowance: str, max_tool_turns: int, tools_enabled: bool) -> dict:
        """조사자 차례를 도구 호출이 끝날 때까지 돈다.

        {"draft": 초안 또는 None, "problems": 형식 문제, "status_notes": 허용 상태 관찰, "message": 마지막 모델 메시지,
        "was_draft": 마지막 답이 초안 글이었나}를 돌려준다. tools_enabled가 거짓(비교 불가)이면 도구를 주지 않고, 모델이
        불러도 not_comparable로 막는다."""
        tool_turns, refused_turns = 0, 0
        while True:
            self.check_deadline()
            allow = tools_enabled and tool_turns < max_tool_turns and self._allowance_left(allowance) > 0
            result = investigator.step(self.client, messages, stage=self.stage, mode=self.mode,
                                       signals=self.signals, allow_tools=allow)
            if result["kind"] == "draft":
                return {"draft": result["draft"], "problems": result["problems"],
                        "status_notes": result["status_notes"], "message": result["message"], "was_draft": True}
            messages.append(investigator.assistant_message(result["message"]))
            if allow:
                tool_turns += 1
            else:
                refused_turns += 1
            for call in result["calls"]:
                if call["error"] is not None:
                    outcome = self.refuse(call["tool"], call["args"], "model", "invalid_call")
                elif not allow:
                    kind = f"{allowance}_limit" if tools_enabled else "not_comparable"
                    outcome = self.refuse(call["tool"], call["args"], "model", kind)
                else:
                    outcome = self.attempt(call["tool"], call["args"], source="model", allowance=allowance)
                result_view = outcome if outcome.get("blocked") else investigator.compact_envelope(outcome)
                messages.append(investigator.tool_result_message(call["id"], call["tool"] or "", result_view))
            if refused_turns >= 2:
                return {"draft": None, "problems": ["도구 없이 초안을 쓰라는 요청에 두 번 도구를 불렀다"],
                        "status_notes": [], "message": result["message"], "was_draft": False}

    # 보고서와 판정 ----------------------------------------------------------------------------------------------
    def build(self, draft: dict) -> dict:
        built = self.ports.build_report({"case": self.case, "mode": self.mode, "run_id": self.ctx.run_id,
                                         "draft": draft, "evidence": list(self.evidence)})
        self.rejected = list(built.get("rejected") or [])
        return built["report"]

    def check(self, report: dict, phase: str, schema_only: bool = False) -> dict:
        """스키마 검사와 검증기 판정. schema_only면(Critic 앞의 첫 검사) 스키마 결과만 판정에 쓴다."""
        result = self.ports.check_report({"case": self.case, "mode": self.mode, "report": report,
                                          "evidence": list(self.evidence), "revision_used": self.revision_used})
        blocked = (not result["schema_ok"]) or (not schema_only and self.mode != "freeform"
                                                and not result["validator_ok"])
        self.sink.emit("validator_result", self.stage, {"phase": phase, "scope": "schema" if schema_only else "all",
                                                        "schema_ok": result["schema_ok"],
                                                        "validator_ok": result["validator_ok"],
                                                        "record_only": self.mode == "freeform",
                                                        "decision": "block" if blocked else "pass",
                                                        "findings": result["findings"],
                                                        "rejected_requests": self.rejected,
                                                        **({"verify_skipped": True} if self.verify_skipped else {})})
        self.verify_skipped = False
        return result

    def state(self, phase: str, draft: dict | None, **extra) -> None:
        data = {"phase": phase, "review_status": (draft or {}).get("review_status"),
                "signal_status": (draft or {}).get("signal_status")}
        data.update(extra)
        self.sink.emit("state_change", self.stage, data)

    def invalid(self, code: str, detail: str) -> model_client.RunStop:
        self.sink.emit("budget_block", self.stage, {"kind": "revision_limit", "tool": None,
                                                    "tool_attempts": self.tool_attempts})
        return model_client.RunStop(code, self.stage, detail)

    def complete(self, report: dict, draft: dict, check: dict) -> dict:
        if self.clock_ms() >= self.budget.deadline_ms:  # 완료 직전에도 deadline이 먼저다
            raise model_client.RunStop(cause_codes.DEADLINE, self.stage, "완료 직전 사례 deadline을 넘었다")
        final = dict(report, validator_findings=check["findings"])
        final.setdefault("review_status", draft.get("review_status"))
        final.setdefault("signal_status", draft.get("signal_status"))
        final.setdefault("unresolved_evidence", _unresolved(final["signal_status"], self.signals))
        statuses = final["signal_status"]
        if final["review_status"] not in investigator.REVIEW_STATUSES or not isinstance(statuses, dict) \
                or set(statuses) != set(investigator.SIGNAL_CODES) \
                or any(v not in investigator.SIGNAL_STATUSES for v in statuses.values()):
            raise model_client.RunStop(cause_codes.SCHEMA_INVALID, self.stage, "최종 보고서의 판정 상태가 값 집합 밖이다")
        self.state("final", final)
        return final

    # 모드별 흐름 -------------------------------------------------------------------------------------------------
    def comparable(self, envelope: object) -> bool:
        """check_comparability 봉투의 comparability.comparable(참거짓, MT2 커밋 777adb6의 단위 I1 봉투 키). 키가 없거나
        참거짓이 아니면 CODE_ERROR로 멈춘다(비교 불가 조기 종료가 조용히 꺼지지 않게)."""
        comparability = envelope.get("comparability") if isinstance(envelope, dict) else None
        value = comparability.get("comparable") if isinstance(comparability, dict) else None
        if not isinstance(value, bool):
            raise model_client.RunStop(cause_codes.CODE_ERROR, self.stage,
                                       "check_comparability 봉투에 comparability.comparable(참거짓)이 없다")
        return value

    def checklist(self) -> dict:
        self.stage = "basic"
        self.sink.emit("stage_start", "basic", {"stage": "basic"})
        first = self.attempt("check_comparability", {}, source="code", allowance="basic")
        if self.comparable(first):
            self.attempt("get_history", {}, source="code", allowance="basic")
            if self.signals.get("unit_value") == "TRIGGERED":
                self.attempt("decompose_hs", {}, source="code", allowance="basic")
            if "TRIGGERED" in self.signals.values():
                self.attempt("compare_partners", {}, source="code", allowance="basic")
        draft = self.ports.checklist_draft({"case": self.case, "evidence": list(self.evidence)})
        self.state("draft", draft)
        self.sink.emit("stage_end", "basic", {"stage": "basic"})
        self.stage = "final"
        self.sink.emit("stage_start", "final", {"stage": "final"})
        report = self.build(draft)
        self.verify(draft, "verify")
        result = self.check(report, "final")
        if not result["schema_ok"]:
            raise model_client.RunStop(cause_codes.SCHEMA_INVALID, "final", "checklist 보고서가 스키마 검사에서 막혔다")
        if not result["validator_ok"]:
            raise model_client.RunStop(cause_codes.VALIDATOR_BLOCKED, "final", "checklist는 수정 없이 INVALID(결정 D1)")
        return self.complete(report, draft, result)

    def model_flow(self) -> dict:
        prompts = self.config.prompts
        self.stage = "basic"
        self.sink.emit("stage_start", "basic", {"stage": "basic"})
        first = self.attempt("check_comparability", {}, source="code", allowance="basic")
        comparable = self.comparable(first)
        if comparable:
            self.attempt("get_history", {}, source="code", allowance="basic")
        messages = investigator.initial_messages(prompts, self.case, self.mode, self.evidence, self.required,
                                                 self.remaining(comparable))
        turn = self.investigate(messages, allowance="comparison", max_tool_turns=self.limits.investigator_comparisons,
                                tools_enabled=comparable)
        draft, problems = turn["draft"], turn["problems"]
        self.state("draft", draft, problems=len(problems), problem_list=problems, status_notes=turn["status_notes"])
        report, check, findings = None, None, []
        if draft is not None and not problems:
            report = self.build(draft)
            check = self.check(report, "draft", schema_only=True)
            if not check["schema_ok"]:
                problems, findings = ["보고서 스키마 검사 실패"], check["findings"]
        self.sink.emit("stage_end", "basic", {"stage": "basic"})
        review = None
        if not problems:
            if self.mode in CRITIC_MODES:
                self.stage = "critic"
                self.sink.emit("stage_start", "critic", {"stage": "critic"})
                self.critic_used = True  # Critic 단계를 연 때 참(요청 중에 멈춰도 Critic을 쓴 실행으로 센다)
                review = critic.review(self.client, prompts, self.case, draft, self.evidence,
                                       self.limits.revision_requeries)
                self.state("after_critic", draft, needs_revision=review["needs_revision"],
                           findings=len(review["findings"]), requery=len(review["requery"]),
                           problems=review["problems"])
                self.sink.emit("stage_end", "critic", {"stage": "critic"})
                self.stage = "basic"
            self.verify(draft, "verify")
            check = self.check(report, "verify")
            if not check["schema_ok"]:
                problems, findings = ["보고서 스키마 검사 실패"], check["findings"]
            elif self.mode != "freeform" and not check["validator_ok"]:
                findings = check["findings"]
            elif not (review and review["needs_revision"]):
                self.stage = "final"
                return self.complete(report, draft, check)
        # 수정 단계(1회). 비교 불가 사례는 여기서도 도구를 주지 않는다(조기 종료, 개발 플랜 §6.6).
        self.stage = "revision"
        self.revision_used = True
        self.sink.emit("stage_start", "revision", {"stage": "revision"})
        if turn["was_draft"]:
            messages.append(investigator.assistant_message({"content": turn["message"].get("content") or ""}))
        messages.append(investigator.feedback_message(problems, review, findings, self.remaining(comparable)))
        turn = self.investigate(messages, allowance="requery", max_tool_turns=self.limits.revision_requeries,
                                tools_enabled=comparable)
        draft, problems = turn["draft"], turn["problems"]
        self.state("revised", draft, problems=len(problems), problem_list=problems, status_notes=turn["status_notes"])
        self.sink.emit("stage_end", "revision", {"stage": "revision"})
        self.stage = "final"
        self.sink.emit("stage_start", "final", {"stage": "final"})
        if draft is None or problems:
            raise self.invalid(cause_codes.SCHEMA_INVALID, "수정 1회 뒤에도 초안 형식 검사에 실패했다")
        report = self.build(draft)
        self.verify(draft, "final_verify")
        check = self.check(report, "final")
        if not check["schema_ok"]:
            raise self.invalid(cause_codes.SCHEMA_INVALID, "수정 1회 뒤에도 보고서 스키마 검사에 실패했다")
        if self.mode != "freeform" and not check["validator_ok"]:
            raise self.invalid(cause_codes.VALIDATOR_BLOCKED, "수정 1회 뒤에도 검증기가 막았다")
        return self.complete(report, draft, check)


def orchestrate(ctx: RunContext, ports: Ports, config: model_client.ModelConfig, *, transport=None,
                sink: trace_log.Sink | None = None, clock_ms: Callable[[], int] | None = None,
                sleep_ms: Callable[[int], None] | None = None) -> dict:
    """사례 1건을 끝까지 돌린다. 돌려주는 값: {"record": 실행 쪽 키 21개, "report": 최종 보고서 또는 None}.

    transport는 NIM 전송 자리(단위 I7 UrllibTransport나 단위 I8 ReplayTransport). checklist는 모델을 부르지 않는다.
    sink는 trace 이벤트를 받는 쪽(단위 L1)이다. 실행 폴더·파일은 부르는 쪽이 정한다(S0 결정 ⑥).
    """
    if ctx.mode not in MODES:
        raise ValueError(f"모드가 4개 밖이다: {ctx.mode!r}")
    missing = [k for k in CASE_KEYS if k not in ctx.case]
    if missing:
        raise ValueError(f"사례에 키가 없다: {missing}")
    # 실행 전에 정해지는 키는 모델 요청·도구를 쓰기 전에 본다(끝의 build_record와 같은 규칙, 단위 L2)
    run_record.check_static({"run_id": ctx.run_id, "case_id": ctx.case["case_id"], "dataset": ctx.dataset,
                             "mode": ctx.mode, "policy_version": ctx.case["policy_version"],
                             "rulebook_version": ctx.rulebook_version, "snapshot_id": ctx.case["snapshot_id"],
                             "grouping_version": ctx.grouping_version, "code_version": ctx.code_version})
    sink = sink or trace_log.NullSink()
    clock_ms = clock_ms or model_client._default_clock_ms
    sleep_ms = sleep_ms or model_client._default_sleep_ms
    budget = model_client.Budget(config.limits, clock_ms(), config.settings.end_reserve_ms)
    client = None
    if ctx.mode != "checklist":
        if transport is None:
            raise ValueError("모델 모드에는 전송 자리가 필요하다")
        client = model_client.ModelClient(config.settings, budget, transport, sink, clock_ms=clock_ms,
                                          sleep_ms=sleep_ms)
    flow = _Flow(ctx, ports, config, client, budget, sink, clock_ms)
    sink.emit("run_start", None, {"case_id": ctx.case["case_id"], "mode": ctx.mode, "dataset": ctx.dataset,
                                  "snapshot_id": ctx.case["snapshot_id"], "policy_version": ctx.case["policy_version"],
                                  "grouping_version": ctx.grouping_version, "model_config": config.settings.config_version,
                                  "api_key_env": config.settings.api_key_env,
                                  "limits": {k: getattr(config.limits, k) for k in model_client.LIMIT_KEYS}})
    report, stop = None, None
    try:
        if ports.required_evidence is not None:
            flow.required = ports.required_evidence(ctx.case)
        report = flow.checklist() if ctx.mode == "checklist" else flow.model_flow()
    except model_client.RunStop as exc:
        stop = exc
    except replay.ReplayMismatch as exc:
        stop = model_client.RunStop(cause_codes.CODE_ERROR, flow.stage, f"ReplayMismatch: {exc}")
    except Exception as exc:  # noqa: BLE001 - 예외 이름만 적는다(자료 계약 N13)
        stop = model_client.RunStop(cause_codes.CODE_ERROR, flow.stage, type(exc).__name__)
    now = clock_ms()
    counters = model_client.budget_counters(budget, now, flow.tool_attempts)
    if stop is None:
        status, errors = cause_codes.COMPLETED, []
    else:
        status = cause_codes.execution_status(stop.code)
        errors = [cause_codes.error_entry(stop.code, stop.stage, counters, flow.last_good_evidence, stop.detail)]
    completed = status == cause_codes.COMPLETED
    record = run_record.build_record({
        "run_id": ctx.run_id, "case_id": ctx.case["case_id"], "dataset": ctx.dataset, "mode": ctx.mode,
        "policy_version": ctx.case["policy_version"], "rulebook_version": ctx.rulebook_version,
        "snapshot_id": ctx.case["snapshot_id"], "grouping_version": ctx.grouping_version,
        "code_version": ctx.code_version,
        "review_status_final": report["review_status"] if completed else None,
        "signal_status": report["signal_status"] if completed else None,
        "unresolved_evidence": bool(report["unresolved_evidence"]) if completed else False,
        "execution_status": status, "tool_attempts": flow.tool_attempts,
        "model_requests": budget.model_requests, "tokens_in": budget.tokens_in, "tokens_out": budget.tokens_out,
        "wall_ms": counters["wall_ms"], "critic_used": flow.critic_used, "revision_used": flow.revision_used,
        "errors": errors})
    sink.emit("run_end", None, {"execution_status": status, "cause_code": stop.code if stop else None,
                                "review_status_final": record["review_status_final"],
                                **{k: record[k] for k in ("tool_attempts", "model_requests", "tokens_in", "tokens_out",
                                                          "wall_ms", "critic_used", "revision_used")}})
    return {"record": record, "report": report if completed else None}


def run(inp: object) -> object:
    """기록된 trace로 사례 실행 1건을 다시 돈다(키·네트워크·스냅샷 없음, 단위 I8 재생).

    입력: {"run_id", "case": 사례(CASE_KEYS), "mode", "dataset", "rulebook_version", "grouping_version",
    "code_version", "replay": [trace 레코드], "config_dir"(선택)}. 모델 응답과 도구 봉투는 기록에서 재생하고(기록의
    model_request에 request_sha256이 있으면 보내는 요청 본문이 같아야 한다), 보고서·검증기·정책·도구 예산은
    unit_ports로 그 단위들을 부른다. 재생이 끝났는데 기록이 남으면 ReplayMismatch다.
    출력: {"record": 실행 쪽 키 21개, "report": 최종 보고서 또는 null, "events": [[이벤트, 단계, 요지]]}.
    """
    if not isinstance(inp, dict) or not isinstance(inp.get("case"), dict):
        raise ValueError("입력은 {run_id, case, mode, dataset, ..., replay[]}다")
    config = model_client.load_model_config(inp.get("config_dir"))
    records = inp.get("replay") or []
    clock = replay.ReplayClock()
    ctx = RunContext(run_id=inp["run_id"], case=inp["case"], mode=inp["mode"], dataset=inp["dataset"],
                     rulebook_version=inp["rulebook_version"], grouping_version=inp["grouping_version"],
                     code_version=inp["code_version"])
    ports = unit_ports(ctx.case, ctx.mode, ctx.run_id, config.limits, grouping_version=ctx.grouping_version,
                       clock=clock.wall)
    tools = replay.ReplayTools(records, clock)
    transport = replay.ReplayTransport(records, clock)
    ports.tool = tools.call
    sink = trace_log.MemoryTrace(ctx.run_id, clock=clock.wall)
    result = orchestrate(ctx, ports, config, transport=transport, sink=sink, clock_ms=clock.now_ms,
                         sleep_ms=clock.sleep_ms)
    if transport.remaining or tools.remaining:  # 기록보다 일찍 끝난 재생은 같은 실행이 아니다
        raise replay.ReplayMismatch(f"재생이 기록보다 일찍 끝났다(남은 모델 응답 {transport.remaining}개, "
                                    f"도구 봉투 {tools.remaining}개)")
    events = []
    for record in sink.records:
        data = record["data"]
        gist = data.get("kind") or data.get("phase") or data.get("tool") or data.get("execution_status")
        if record["event"] == "model_error":
            gist = f"HTTP {data.get('http_status')}" if data.get("http_status") is not None else data.get("error")
        events.append([record["event"], record["stage"], gist])
    return {"record": result["record"], "report": result["report"], "events": events}
