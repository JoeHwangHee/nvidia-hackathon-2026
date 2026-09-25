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
   흐름 수정 (가)(AS2 ㉔): Critic의 재조회 요청 가운데 그 사례에서 발동(TRIGGERED)하지 않은 신호에만 쓰는 도구
   (SIGNAL_ONLY_TOOLS, 지금은 단가 신호 전용 decompose_hs) 요청은 코드가 버린다. 버린 요청은 수정 지시 메시지와 수정 단계의
   필수 조회(requested)에 들지 않고, trace after_critic의 requery_dropped에 남는다. needs_revision은 바꾸지 않는다.
3. verify_evidence(기본 경로의 예약 1회) → 검증기 판정. 수정이 필요 없으면(스키마 통과, 검증기 통과 또는 freeform,
   Critic이 수정을 요청하지 않음) 여기서 COMPLETED.
4. revision(1회): 조사자가 지적을 받고 재조회(최대 2회) 뒤 고친 초안을 쓴다. Critic은 다시 부르지 않는다. 비교 불가
   사례는 수정 단계에서도 도구를 주지 않는다(조기 종료, 개발 플랜 §6.6).
5. final: verify_evidence(최종 예약 1회) → 스키마·검증기 판정. 두 번째 수정 단계는 없다: 스키마 실패는
   SCHEMA_INVALID, 검증기 차단(freeform 밖)은 VALIDATOR_BLOCKED로 INVALID다(budget_block revision_limit).
   흐름 수정 (나)(AS2 ㉔, 모든 모델 모드 같은 규칙): ① 수정 단계를 연 까닭이 Critic의 수정 요구뿐이고(초안 형식 문제·
   스키마 실패·수정 전 검증기 막음·코드 지적이 없다) ② 수정 전 초안이 verify 단계 검사(스키마, freeform 밖은 검증기까지)를
   통과했는데 ③ 수정본이 최종 단계에서 막히면(초안 형식 검사·스키마 검사 실패, freeform 밖은 검증기 막음) INVALID로 끝내지
   않고 수정 전 초안의 보고서와 그 verify 단계 판정으로 COMPLETED한다. 도구·모델 요청과 검사를 더 하지 않는다. 막힌
   validator_result는 그대로 남고, state_change revision_discarded가 수정본을 버린 사실을 남긴다(budget_block revision_limit
   은 내지 않는다). critic_used·revision_used는 그대로 참이다. agent는 Critic이 없어 ①이 성립하지 않는다. deadline·예산·
   연결 오류 같은 RunStop은 이 규칙을 거치지 않는다(예외로 곧바로 멈춘다).

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
- 필수 조회(Ports.required_tools, 조립 AS2가 넘긴다. 없으면 강제하지 않는다): 도구를 주는 조사자 차례에 필수 도구의 결과를
  받지 않고 초안을 쓰면, 그 초안을 받지 않고 차례마다 한 번 필수 조회 메시지(단위 I10 REQUIRED_TOOLS_REQUEST, 모든 모드
  같음)로 돌려보낸다. trace에는 state_change draft_refused(missing_tools)로 남는다.
- 규칙 참고값(Ports.reference_status, 조립 AS2가 근거 상태 변환을 넘길 때만): 모델 모드에서 필수 도구 결과를 받은 뒤 첫
  조사자 요청 앞에 코드가 계산한 P3 신호별 판정·판정 근거를 고정 문구로 한 번 싣고 Critic에게도 준다(MT1 결정 ⑬의
  "모델 상태와 나란히 적는 참고값"). 모델 상태를 덮어쓰지 않는다. trace state_change rule_reference. 계산할 수 없었으면
  필수 도구 결과가 갖춰진 뒤, 계산된 뒤에도 새 봉투를 받으면(수정 단계 재조회) 다시 계산해 싣는다(계산할 때마다 trace).
  계산 불가는 입력 검사 오류(ValueError)만이고, 배선 오류(WiringError 등)는 흐름의 CODE_ERROR로 올린다.
- 초안은 도구 없는 차례에서만(Ports.drafts_only_without_tools, 조립 AS2가 켠다): 도구를 준 차례에 온 초안 본문은 버리고
  (state_change draft_discarded) 곧바로 도구 없는 초안 요청(구조화 출력 json_object)으로 다시 받는다.
- 차례 규칙(조립이 위 둘을 켰을 때, AS2 ⑲): 필수 결과(필수 도구 + 수정 단계의 Critic 재조회 요청)가 빠졌고 그 차례에 예산이
  있을 때만 도구 차례다(도구 목록은 전부, tool_choice "required", 알림 한 줄 PENDING_TOOLS_REQUEST). 아니면 곧바로 도구 없는
  초안 차례다. Critic(full·freeform) 뒤에도 필수 결과가 빠졌고 재조회 예산이 있으면 코드 지적(code_finding)을 Critic
  결과(agent는 수정 지시)에 덧붙이고 수정 1회로 간다. 스키마 실패 초안이 Critic을 건너뛰는 규칙(개발 플랜 §6.6)은 그대로다.

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
  after_critic의 requery는 흐름 수정 (가)로 거르고 남은 요청 수이고, requery_dropped는 버린 요청 목록
  [{tool, args, reason "signal_not_triggered", signals}]이다. 흐름 수정 (나)로 수정본을 버리면 final 단계에
  state_change phase revision_discarded(review_status·signal_status는 둔 수정 전 초안의 것, blocked_by draft_format·
  schema·validator, would_be_cause SCHEMA_INVALID·VALIDATOR_BLOCKED, kept_report_id)가 final 앞에 나온다.
- 필수 근거 주장 덧붙이기(사용자 결정 2026-09-25(금) 18:09, 모든 모드 같은 규칙): 보고서를 만들 때마다(초안·verify·final)
  _Flow.build가 신호별 판정에 필요한 필수 근거 코드(evidence_codes: 판정이 규칙 참고값 Ports.evidence_reference와 같으면
  그 판정 근거의 P5 목록, 다르거나 참고값이 없으면 그 상태를 내는 P5 목록의 합)를 build_report에 넘기고, unit_ports의
  build_report가 코드마다 시나리오 명세 §5.3 판정 조건표를 채우는 주장이 없으면 받은 봉투의 검증된 지표·자료 상태에서 단위
  R1 틀 채우기로 채워 모델(또는 checklist 규칙) 주장 뒤에 덧붙인다(evidence_claims). 모델 주장은 바꾸지 않고, 같은 대상은
  다시 넣지 않으며, 검증기 R3의 DATA_STATUS_CONFLICT를 낼 주장은 넣지 않는다. 도구를 새로 부르지 않고 verify_evidence
  인자(초안이 가리킨 근거)도 바꾸지 않는다. trace에는 보고서를 만들 때마다 state_change phase evidence_claims
  (review_status·signal_status, required {신호: 코드}, added [{signal, code, claims: [요청 모양]}], unmet, no_action)가
  그 보고서의 validator_result 앞에 나온다.
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
# 흐름 수정 (가)(AS2 ㉔): 특정 신호에만 쓰는 도구 -> 그 신호. 사례에서 이 신호가 하나도 발동하지 않았으면 Critic의 재조회
# 요청 가운데 이 도구 요청을 버린다. 여기 없는 도구는 거르지 않는다. 신호별 필수 도구 규칙(cli.dispatch.required_tools)과
# 어긋나지 않는지는 시험이 대조한다(workflow는 cli를 import하지 않는다).
SIGNAL_ONLY_TOOLS = {"decompose_hs": ("unit_value",)}


def split_requery(requery: list, signals: dict | None) -> tuple[list, list]:
    """Critic 재조회 요청을 (남길 것, 버릴 것)으로 나눈다(흐름 수정 (가)). 버릴 것에는 까닭(reason_code
    signal_not_triggered, 그 도구가 쓰는 신호)을 붙인다. 순서는 원래 순서를 지킨다."""
    fired = {code for code, value in (signals or {}).items() if value == "TRIGGERED"}
    kept, dropped = [], []
    for item in requery or []:
        only = SIGNAL_ONLY_TOOLS.get(item.get("tool")) if isinstance(item, dict) else None
        if only is not None and not fired.intersection(only):
            dropped.append({"tool": item.get("tool"), "args": item.get("args"), "reason": "signal_not_triggered",
                            "signals": list(only)})
        else:
            kept.append(item)
    return kept, dropped


@dataclass
class Ports:
    """흐름 조정이 부르는 다른 단위 자리.

    tool(이름, 인자) -> 봉투 / budget(실행한 시도 목록, 후보) -> {"allowed", "reason"} /
    build_report({"case","mode","run_id","draft","evidence"}) -> {"report": 보고서, "rejected": 버린 요청 목록} /
    check_report({"case","mode","report","evidence","revision_used"}) -> {"schema_ok", "validator_ok", "findings"} /
    checklist_draft({"case","evidence"}) -> 초안 / required_evidence(사례) -> 필수 근거(단위 P5 출력, 없으면 None) /
    required_tools(사례) -> 조사자가 초안 전에 받아야 하는 도구 이름 목록(없으면 None: 강제하지 않음. 조립 AS2가 넘긴다) /
    reference_status(봉투 목록) -> 판정 정책 P3 출력(신호별 판정·판정 근거). 모델 모드의 규칙 참고값(없으면 None: 싣지 않음.
    unit_ports가 근거 상태 변환 evidence_state를 받았을 때만 만든다). 계산할 수 없으면 예외를 낸다 /
    drafts_only_without_tools: 참이면 초안은 도구를 주지 않는 차례(초안 요청 메시지, 구조화 출력 json_object)에서만 받는다.
    도구를 준 차례에 도구 호출 없이 온 본문은 버리고 곧바로 도구 없는 초안 요청으로 다시 받는다(조립 AS2가 켠다) /
    evidence_reference(봉투 목록) -> P3 출력. 보고서에 덧붙일 필수 근거 코드를 고를 때 쓰는 규칙 참고값(모든 모드. 없으면
    None: 판정 상태를 내는 판정 근거의 목록을 모두 합친다). unit_ports가 reference_status와 같은 계산으로 넘긴다. 모델에게
    싣는 참고값(reference_status)과 따로 두어 checklist에도 쓰고 참고값 문구의 계산 횟수를 바꾸지 않는다
    """

    tool: Callable[[str, dict], dict]
    budget: Callable[[list, dict], dict]
    build_report: Callable[[dict], dict]
    check_report: Callable[[dict], dict]
    checklist_draft: Callable[[dict], dict]
    required_evidence: Callable[[dict], object] | None = None
    required_tools: Callable[[dict], list] | None = None
    reference_status: Callable[[list], dict] | None = None
    drafts_only_without_tools: bool = False
    evidence_reference: Callable[[list], dict] | None = None


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
    evidence_ids 목록)도 읽는다. hs_code가 10자리면 hs10이다.
    C형(부모 HS6 행이 있는 달에 HS10 하위 자료만 빠짐. MT2 도구가 항목에 hs10_codes·hs10_codes_source를 붙인다)은
    hs10_codes의 코드마다 항목 하나로 펼친다(조립 AS2): hs10 = 그 코드, status_id = "{근거 ID}@{코드}"(코드마다 다르다),
    근거 ID는 그 상태 행 하나다. 그래서 R1이 코드마다 observation_status@<HS10> 주장을 만든다(MT3 결정 ⑨). 코드 목록이
    비면(출처 none) 쓸 수 있는 주장이 없어 항목을 만들지 않는다(HS6 수준 기호로 쓰면 같은 키의 값 주장과 어긋난다)."""
    statuses, seen = [], set()
    for item in _missing_items(evidence):
        code = str(item.get("hs_code") or item.get("hs6") or "")
        refs = item.get("evidence_ids") if isinstance(item.get("evidence_ids"), list) else [item.get("evidence_id")]
        codes = item.get("hs10_codes") if isinstance(item.get("hs10_codes"), list) else None
        for ev in refs:
            if not isinstance(ev, str) or ev in seen:
                continue
            seen.add(ev)
            base = {"hs6": item.get("hs6") or code[:6], "partner": item.get("partner_code") or item.get("partner"),
                    "period": item.get("month") or item.get("period"),
                    "observation_status": item.get("observation_status"), "evidence_ids": [ev],
                    "baseline_period": item.get("baseline_period")}
            if codes is None:
                statuses.append({"status_id": ev, **base,
                                 "hs10": item.get("hs10") or (code if len(code) == 10 else None)})
            else:
                statuses += [{"status_id": f"{ev}@{hs10}", **base, "hs10": hs10} for hs10 in codes
                             if isinstance(hs10, str)]
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


def _requests_of(draft: dict, statuses: list | None = None) -> list:
    """틀 채우기 모드 초안의 주장 참조(metric_id·evidence_id)를 단위 R1의 요청({claim_id, metric_id|status_id})으로.

    evidence_id가 C형 상태 행이면(자료 상태 항목이 코드마다 펼쳐져 있으면) 그 코드마다 요청 하나를 만든다(claim_id
    c{번호}-{k}). 초안은 실제 근거 ID만 가리키고, 펼친 status_id는 R1 입력 안에서만 쓴다(verify_evidence에는 근거 ID가 간다)."""
    expanded: dict[str, list[str]] = {}
    for status in statuses or []:
        ids = status.get("evidence_ids") if isinstance(status, dict) else None
        if isinstance(ids, list) and ids and isinstance(ids[0], str) and isinstance(status.get("status_id"), str):
            expanded.setdefault(ids[0], []).append(status["status_id"])
    requests = []
    for number, claim in enumerate(draft.get("claims") or [], start=1):
        if not isinstance(claim, dict):
            continue
        if isinstance(claim.get("metric_id"), str):
            requests.append({"claim_id": f"c{number}", "metric_id": claim["metric_id"]})
        elif isinstance(claim.get("evidence_id"), str):
            targets = expanded.get(claim["evidence_id"]) or [claim["evidence_id"]]
            if len(targets) == 1:
                requests.append({"claim_id": f"c{number}", "status_id": targets[0]})
            else:
                requests += [{"claim_id": f"c{number}-{k}", "status_id": target}
                             for k, target in enumerate(targets, start=1)]
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
    status_evidence = dict.fromkeys(s["evidence_ids"][0] for s in _statuses_of(evidence))  # C형은 근거 ID 하나로(펼치기는 R1 요청)
    claims += [{"claim_type": "data_status", "evidence_id": ev} for ev in status_evidence]
    return claims


# --- 필수 근거 주장 덧붙이기(사용자 결정 2026-09-25(금) 18:09, 결정 기록 *-model-decision-evidence-claims.md) ----------
# 보고서를 만들 때마다(초안·verify·final, 모든 모드) 코드가 신호별 판정에 필요한 필수 근거 코드(단위 P5)마다 시나리오 명세
# eval/scenarios/SCENARIO_SPEC.md §5.3 판정 조건표를 채우는 주장이 있는지 보고, 없으면 이미 받은 봉투의 검증된 지표·자료
# 상태로 채울 주장을 덧붙인다. 모델(또는 checklist 규칙)이 쓴 주장은 바꾸거나 지우지 않고, 같은 대상의 주장은 다시 넣지
# 않는다. 채점기(eval/scorer)는 import하지 않고 이 표를 여기서 따로 구현한다(검증기 R3에는 이 표의 구현이 없다).
EVIDENCE_CLAIM_ID = "e{n}"  # 덧붙인 주장의 claim_id(모델·틀 채우기 claim_id와 겹치면 번호를 건너뛴다)
# 덧붙일 것이 없는 코드: 부정 조건(no_zero_fill: 주장을 더해서 채울 수 없다)과 v1에서 판정하지 않는 교정 근거 셋(§5.3).
NO_ACTION_CODES = ("no_zero_fill", "correction_snapshots_before_after", "recalculated_values", "change_reason")
_MISSING_STATES = ("OBSERVED", "CONFIRMED_NO_TRADE")  # 빠진 키가 아닌 관측 상태(§5.3 "빠진 키")
# §5.3 missingness_listed의 대안(빠진 키가 없을 때): 사례 품목·두 시점 계열 지표 가운데 계산할 수 없는 것을 null로 적어
# CORRECT인 주장. 이미 있는 주장만 세고 덧붙이지는 않는다(Codex 검토 3회차: 채점기의 CORRECT를 받은 근거만으로 확실히 가늠할
# 수 없어서다). 계열마다 세는 기호(`@` 앞)다.
NULL_BASES = {"unit_value": ("V", "Q", "U", "w", "r_U", "within_effect", "mix_effect", "residual"),
              "share": ("V", "s", "d_s")}
# 값이 null인 변화 주장에 허용하는 방향. 자료 계약 §6.2는 변화 주장의 방향을 UP·DOWN·FLAT(값의 부호)로만 정하고 값 null의
# 방향을 정하지 않았다. 확신이 없는 조건은 충족으로 보지 않으므로 비어 있다(값 null의 변화 주장은 세지 않는다).
NULL_CHANGE_DIRECTIONS: tuple = ()


def evidence_codes(signals: dict | None, signal_status: object, reference: object) -> dict:
    """발동한 신호마다 보고서가 남겨야 할 필수 근거 코드(단위 P5 규칙표 순서, 겹치지 않게).

    그 신호의 판정(초안의 signal_status)이 규칙 참고값(P3 출력)의 판정과 같으면 참고값 판정 근거(basis)의 목록이고, 다르거나
    참고값이 없으면 그 판정 상태를 내는 모든 판정 근거의 목록을 합친 것이다. 판정이 값 집합 밖이면 빈 목록이다."""
    stated = signal_status if isinstance(signal_status, dict) else {}
    ref_status = reference.get("signal_status") if isinstance(reference, dict) else None
    ref_basis = reference.get("basis") if isinstance(reference, dict) else None
    out: dict = {}
    for family in policy_required_evidence.SIGNAL_CODES:
        if (signals or {}).get(family) != policy_required_evidence.TRIGGERED:
            continue
        status = stated.get(family)
        codes: list = []
        if isinstance(ref_status, dict) and isinstance(ref_basis, dict) and ref_status.get(family) == status:
            try:
                codes = list(policy_required_evidence.rule_evidence(family, ref_basis.get(family)))
            except ValueError:
                codes = []
        else:
            for _basis, rule_status, evidence in policy_required_evidence.RULES[family]:
                if rule_status == status:
                    codes += [code for code in evidence if code not in codes]
        out[family] = codes
    return out


def _target(claim: dict) -> tuple | None:
    """주장의 대상(§5.3 "유효한 claim"의 대상). 자료 상태는 기준월을 보지 않는다(채점기와 같이 상대국·품목·월·기호).
    대상 필드가 문자열·null이 아닌 주장(freeform의 형식이 틀린 주장)은 None이다."""
    if claim.get("claim_type") == "data_status":
        key = ("data_status", claim.get("metric"), claim.get("hs6"), claim.get("partner"), claim.get("period"), None)
    else:
        key = (claim.get("claim_type"), claim.get("metric"), claim.get("hs6"), claim.get("partner"),
               claim.get("period"), claim.get("baseline_period"))
    return key if all(v is None or isinstance(v, str) for v in key) else None


class _EvidenceView:
    """보고서 주장(R1 출력)과 받은 봉투로 §5.3 조건을 보고, 채울 주장을 고른다."""

    def __init__(self, case: dict, claims: list, evidence: list):
        self.hs6, self.partner = case.get("hs6"), case.get("partner")
        self.t, self.b = case.get("month"), case.get("baseline_month")
        self.evidence = [e for e in evidence if isinstance(e, dict)]
        self.claims = [c for c in claims if isinstance(c, dict)]
        self.ids = {c.get("claim_id") for c in self.claims if isinstance(c.get("claim_id"), str)}
        self.added: list = []  # (주장, 요청 모양)
        metrics = [m for m in _metrics_of(self.evidence) if isinstance(m.get("metric_id"), str)]
        statuses = _statuses_of(self.evidence)
        # 후보: 검증된 지표와 자료 상태를 단위 R1로 채운 typed claim(값이 없는 지표 등 R1이 버리는 것은 후보가 아니다)
        filled = report_claims.fill(case, metrics, [], [{"claim_id": m["metric_id"], "metric_id": m["metric_id"]}
                                                        for m in metrics])["claims"]
        status_ev = {s["status_id"]: s["evidence_ids"][0] for s in statuses}
        filled += report_claims.fill(case, [], statuses, [{"claim_id": sid, "status_id": sid}
                                                          for sid in status_ev])["claims"]
        self.candidates = [c for c in filled if c.get("hs6") == self.hs6]
        self.request_of = {}
        for claim in self.candidates:
            if claim["claim_type"] == "data_status":
                self.request_of[id(claim)] = {"claim_type": "data_status", "evidence_id": status_ev[claim["claim_id"]]}
            else:
                self.request_of[id(claim)] = {"claim_type": claim["claim_type"], "metric_id": claim["claim_id"]}
        self.by_target: dict = {}
        for claim in self.candidates:
            self.by_target.setdefault(_target(claim), []).append(claim)
        # 계산 불가(값 null) 지표 {(기호, 상대국, 월, 기준월): 근거 묶음 목록}. null 주장의 충족 판정에만 쓴다
        self.nulls: dict = {}
        for metric in metrics:
            inputs = metric.get("inputs") if isinstance(metric.get("inputs"), dict) else {}
            evidence = metric.get("evidence_ids")
            if metric.get("value") is None and inputs.get("hs6") == self.hs6 and isinstance(evidence, list) and evidence \
                    and all(isinstance(e, str) for e in evidence):
                key = (inputs.get("metric"), inputs.get("partner"), inputs.get("period"), inputs.get("baseline_period"))
                self.nulls.setdefault(key, []).append((set(evidence), metric.get("unit")))

    def null_scope(self, claim: dict, family: str) -> bool:
        """missingness_listed 대안의 범위: 사례 품목, 대상국(점유율은 대상국이나 ALL), 두 시점, 계열 기호."""
        metric = claim.get("metric")
        partners = (self.partner, "ALL") if family == "share" else (self.partner,)
        return claim.get("claim_type") != "data_status" and isinstance(metric, str) \
            and metric.partition("@")[0] in NULL_BASES[family] and claim.get("hs6") == self.hs6 \
            and claim.get("partner") in partners and claim.get("period") in (self.t, self.b)

    def null_listed(self, family: str) -> bool:
        """계산할 수 없는 계열 지표를 null로 맞게 적은 주장이 이미 있다(§5.3 missingness_listed의 대안, 자료 계약 §6.2).
        조건: 사례 품목, 대상국(점유율은 ALL도), 두 시점 가운데 하나, 값 null, claim_type이 기호·상대국에 맞음, 단위가 계약
        단위이자 받은 계산 불가 지표의 단위, 그 지표의 근거를 모두 인용. 비변화 기호는 기준월 null·방향 NA. 변화 기호는
        기준월이 비교 시점 − 12개월이고 방향이 NULL_CHANGE_DIRECTIONS 안(지금은 비어 있어 세지 않는다)."""
        for claim in self.claims:
            if claim.get("value") is not None or not self.null_scope(claim, family) or _target(claim) is None:
                continue
            symbol, partner, period = claim["metric"], claim["partner"], claim["period"]
            base = report_claims.base_symbol(symbol)
            if base is None or claim.get("claim_type") != report_claims.claim_type_of(symbol, partner, self.partner) \
                    or claim.get("unit") != report_claims.UNIT_OF[base]:
                continue
            if base in report_claims.CHANGE_BASES:
                baseline = validator_validate.month_minus_12(period)
                if claim.get("baseline_period") != baseline or claim.get("direction") not in NULL_CHANGE_DIRECTIONS:
                    continue
            else:
                baseline = None
                if claim.get("baseline_period") is not None or claim.get("direction") != "NA":
                    continue
            cited = claim.get("evidence_ids")
            cited = {e for e in cited if isinstance(e, str)} if isinstance(cited, list) else set()
            if any(evidence <= cited and unit == claim["unit"]
                   for evidence, unit in self.nulls.get((symbol, partner, period, baseline), [])):
                return True
        return False

    # 유효성과 후보 ---------------------------------------------------------------------------------------------
    def valid(self, claim: dict) -> bool:
        """대상이 같은 후보가 있고 그 근거를 모두 인용한 주장(자료 상태는 값도 같아야 한다). 값의 참·거짓은 보지 않는다."""
        cited = claim.get("evidence_ids")
        cited = {e for e in cited if isinstance(e, str)} if isinstance(cited, list) else set()
        return any(set(c["evidence_ids"]) <= cited
                   and (c["claim_type"] != "data_status" or c["value"] == claim.get("value"))
                   for c in self.by_target.get(_target(claim), []))

    def has(self, target: tuple, value: object = None) -> bool:
        return target is not None and any(_target(c) == target and (value is None or c.get("value") == value)
                                          and self.valid(c) for c in self.claims)

    def taken(self, target: tuple) -> bool:
        """같은 대상의 주장이 이미 있다(유효하지 않아도 다시 넣지 않는다)."""
        return any(_target(c) == target for c in self.claims)

    def candidate(self, target: tuple, value: object = None) -> dict | None:
        for claim in self.by_target.get(target, []):
            if value is None or claim["value"] == value:
                return claim
        return None

    def option_group(self, option: list) -> list | None:
        """선택지(대상 목록)를 채우려면 더할 후보. 이미 유효하면 빈 목록, 채울 수 없으면 None."""
        group: list = []
        for target, value in option:
            if self.has(target, value) or any(_target(c) == target for c in group):
                continue
            found = self.candidate(target, value)
            if found is None or self.taken(target):  # 받은 근거에 없거나, 같은 대상의 (유효하지 않은) 주장이 이미 있다
                return None
            group.append(found)
        return group

    def part_met(self, options: list) -> bool:
        return any(all(self.has(target, value) for target, value in option) for option in options)

    def fill_parts(self, parts: list) -> str:
        """parts = [[선택지, ...], ...]. 모든 부분을 채우면 met. 채울 수 있으면 더하고 added, 아니면 unmet."""
        if all(self.part_met(options) for options in parts):
            return "met"
        group: list = []
        for options in parts:
            if self.part_met(options):
                continue
            chosen = None
            for option in options:
                found = self.option_group(option)
                if found is not None:
                    chosen = found
                    break
            if chosen is None:
                return "unmet"
            group += [c for c in chosen if all(c is not g for g in group)]
        return "added" if self.add(group) else "unmet"

    def add(self, group: list) -> bool:
        """후보들을 덧붙인다. 같은 대상의 자료 상태·값 주장끼리 어긋나게 되면(검증기 R3 DATA_STATUS_CONFLICT) 넣지 않는다."""
        if not group:
            return False
        before = len(self.conflicts(self.claims))
        new = []
        for claim in group:
            n = len(self.ids) + len(new) + 1
            while EVIDENCE_CLAIM_ID.format(n=n) in self.ids or any(c["claim_id"] == EVIDENCE_CLAIM_ID.format(n=n)
                                                                   for c in new):
                n += 1
            new.append(dict(claim, claim_id=EVIDENCE_CLAIM_ID.format(n=n)))
        if len(self.conflicts(self.claims + new)) > before:
            return False
        for original, claim in zip(group, new):
            self.claims.append(claim)
            self.ids.add(claim["claim_id"])
            self.added.append((claim, dict(self.request_of[id(original)], claim_id=claim["claim_id"])))
        return True

    @staticmethod
    def conflicts(claims: list) -> list:
        # 검증기 R3의 규칙을 그대로 쓴다(R3처럼 형식이 맞는 주장만 넘긴다)
        typed = [(i, c) for i, c in enumerate(claims) if not validator_validate.claim_problems(c)]
        return validator_validate._data_status_conflicts(typed)

    # §5.3 조건(계열 family) ----------------------------------------------------------------------------------
    def level(self, claim_type: str, metric: str, partner: str, period: str, baseline: str | None = None) -> tuple:
        return ((claim_type, metric, self.hs6, partner, period, baseline), None)

    def change_or_levels(self, family: str, partner: str, peer: bool) -> list:
        """계열 지표의 전년동월 변화 주장 하나, 또는 두 시점 수준 주장 둘(§5.3 comparability_ok·partner_comparison_done)."""
        change, level = ("r_U", "U") if family == "unit_value" else ("d_s", "s")
        change_type, level_type = ("change", "value") if family == "unit_value" else ("share_change", "share")
        if peer:
            change_type = level_type = "comparison"
        return [[self.level(change_type, change, partner, self.t, self.b)],
                [self.level(level_type, level, partner, self.t), self.level(level_type, level, partner, self.b)]]

    def peers(self) -> list:
        """비교집합의 비교국: compare_partners 봉투(스냅샷 비교 대상 표, 실행의 grouping_version)가 돌려준 상대국."""
        found = set()
        for envelope in self.peer_envelopes():
            partners = [(m.get("inputs") or {}).get("partner") for m in envelope.get("metrics") or []
                        if isinstance(m, dict)]
            scope = envelope.get("scope") if isinstance(envelope.get("scope"), dict) else {}
            partners += scope.get("partners") if isinstance(scope.get("partners"), list) else []
            found |= {p for p in partners if isinstance(p, str) and p not in (self.partner, "ALL")}
        return sorted(found)

    def peer_envelopes(self) -> list:
        return [e for e in self.evidence if e.get("tool") == "compare_partners" and e.get("retryable_error") is None]

    def peer_statuses(self) -> list:
        """비교국의 빠진 자료 상태 후보(§5.3 missingness_listed의 빠진 키가 없을 때): compare_partners 봉투의 빠진 자료에서
        온 비교국 자신의 상태 행, 사례 품목 HS6 수준(observation_status), 두 시점, OBSERVED가 아닌 값."""
        peers = set(self.peers())
        rows = {item.get("evidence_id") for envelope in self.peer_envelopes()
                for item in envelope.get("missingness") or [] if isinstance(item, dict)}
        return [c for c in self.candidates if c["claim_type"] == "data_status" and c["partner"] in peers
                and c["metric"] == "observation_status" and c["period"] in (self.t, self.b)
                and c["value"] != "OBSERVED" and c["evidence_ids"] and set(c["evidence_ids"]) <= rows]

    def decompose(self) -> dict | None:
        found = [e for e in self.evidence if e.get("tool") == "decompose_hs" and e.get("retryable_error") is None]
        return found[-1] if found else None

    def children(self) -> list:
        """두 시점의 대상국 HS10 하위 코드(decompose_hs 봉투 comparability.hs10, 나온 순서)."""
        envelope = self.decompose()
        entries = ((envelope or {}).get("comparability") or {}).get("hs10") or []
        codes: list = []
        for entry in entries if isinstance(entries, list) else []:
            if isinstance(entry, dict) and entry.get("month") in (self.t, self.b):
                codes += [c for c in entry.get("codes") or [] if isinstance(c, str) and c not in codes]
        return codes

    def gaps(self, family: str) -> dict:
        """빠진 키(§5.3): 단가는 대상국 부모 HS6 키와 C형 HS10 하위 자료, 점유율은 대상국 부모 HS6 키와 ALL 분모.
        {(상대국, hs6|hs10, 월): [그 키의 자료 상태 후보]}."""
        found: dict = {}
        for claim in self.candidates:
            if claim["claim_type"] != "data_status" or claim["value"] in _MISSING_STATES \
                    or claim["period"] not in (self.t, self.b):
                continue
            level = "hs10" if "@" in claim["metric"] else "hs6"
            if level == "hs6" and self.observed(claim["partner"], claim["period"]):
                continue  # 관측 값이 있는 키는 빠진 키가 아니다(요청 하나의 상태 행이 있어도)
            if claim["partner"] == self.partner and (family == "unit_value" or level == "hs6"):
                found.setdefault((claim["partner"], level, claim["period"]), []).append(claim)
            elif claim["partner"] == "ALL" and family == "share":
                found.setdefault(("ALL", level, claim["period"]), []).append(claim)
        return found

    def observed(self, partner: str, period: str) -> bool:
        """그 상대국·월의 사례 품목 HS6 값이 관측됐다(OBSERVED 자료 상태 후보나 HS6 수준 수 지표가 있다)."""
        return any(c["partner"] == partner and c["period"] == period and "@" not in c["metric"]
                   and (c["value"] == "OBSERVED" if c["claim_type"] == "data_status"
                        else c["metric"] in ("V", "Q", "U")) for c in self.candidates)

    def status_options(self, claims: list) -> list:
        return [[(_target(c), c["value"])] for c in claims]

    def wrong_status(self) -> bool:
        """사례 품목·두 시점의 자료 상태 주장 가운데 값이 받은 자료 상태와 다른 것(WRONG_VALUE)이 있다."""
        for claim in self.claims:
            if claim.get("claim_type") != "data_status" or claim.get("period") not in (self.t, self.b):
                continue
            known = self.by_target.get(_target(claim), [])
            if known and all(c["value"] != claim.get("value") for c in known):
                return True
        return False

    def cited(self) -> set:
        """보고서 근거: 주장마다의 evidence_ids를 합친 것(보고서 evidence_ids도 단위 R2가 이것으로 만든다)."""
        found: set = set()
        for claim in self.claims:
            ids = claim.get("evidence_ids")
            found |= {e for e in ids if isinstance(e, str)} if isinstance(ids, list) else set()
        return found

    def parent_child(self) -> str:
        """두 시점 모두 대상국 HS10 하위 행이 있으면, 두 시점마다 대상국 부모 HS6 행과 그 시점 HS10 하위 코드마다의 행을
        보고서 근거가 인용하게 한다(§5.3). 행 묶음은 지표의 근거로 가른다: 부모는 대상국 그 월의 V(없으면 Q·U) 지표 근거,
        하위는 decompose_hs의 그 월 U@코드 지표 근거(값이 없어도 근거는 있다). 묶음마다 행 하나 이상이면 된다(같은 키의
        동등 행). 이 밖의 봉투 행은 요구하지 않는다. 대조 결과(일치·불일치)는 조건이 아니다."""
        groups = self.parent_child_groups()
        if groups is None:
            return "unmet"
        cited = self.cited()
        missing = [g for g in groups if not g & cited]
        if not missing:
            return "met"
        pool = [c for c in self.candidates if c["claim_type"] != "data_status" and c["partner"] == self.partner
                and c["period"] in (self.t, self.b) and not self.taken(_target(c))]
        group: list = []
        while missing:
            best = max(pool, key=lambda c: sum(1 for g in missing if g & set(c["evidence_ids"])), default=None)
            if best is None or not any(g & set(best["evidence_ids"]) for g in missing):
                return "unmet"
            group.append(best)
            missing = [g for g in missing if not g & set(best["evidence_ids"])]
            pool = [c for c in pool if _target(c) != _target(best)]
        return "added" if self.add(group) else "unmet"

    def parent_child_groups(self) -> list | None:
        """부모·하위 대조의 행 묶음 목록(두 시점 부모, 시점마다 하위 코드). 두 시점 모두 하위 코드가 없거나 묶음을 정할
        지표가 없으면 None."""
        envelope = self.decompose()
        entries = ((envelope or {}).get("comparability") or {}).get("hs10") or []
        codes = {e.get("month"): [c for c in e.get("codes") or [] if isinstance(c, str)]
                 for e in entries if isinstance(e, dict)} if isinstance(entries, list) else {}
        if envelope is None or not codes.get(self.t) or not codes.get(self.b):
            return None
        metrics = [m for m in _metrics_of(self.evidence) if isinstance(m.get("inputs"), dict)]

        def rows(symbols: tuple, month: str, source: list) -> frozenset | None:
            for symbol in symbols:
                for metric in source:
                    inputs = metric["inputs"]
                    ids = metric.get("evidence_ids")
                    if (inputs.get("metric"), inputs.get("hs6"), inputs.get("partner"), inputs.get("period")) \
                            == (symbol, self.hs6, self.partner, month) and isinstance(ids, list) and ids:
                        return frozenset(e for e in ids if isinstance(e, str))
            return None
        own = [m for m in (envelope.get("metrics") or []) if isinstance(m, dict) and isinstance(m.get("inputs"), dict)]
        groups = []
        for month in (self.t, self.b):
            found = [rows(("V", "Q", "U"), month, metrics)] + [rows((f"U@{code}",), month, own) for code in codes[month]]
            if any(g is None for g in found):
                return None
            groups += found
        return groups

    def code(self, family: str, code: str) -> str:
        """코드 하나: met(이미 채움) | added(덧붙여 채움) | unmet(받은 근거로 채울 수 없음) | no_action(덧붙일 것이 없음)."""
        p, t, b = self.partner, self.t, self.b
        if code in NO_ACTION_CODES:
            return "no_action"
        if code == "comparability_ok":
            return self.fill_parts([self.change_or_levels(family, p, peer=False)])
        if code == "partner_comparison_done":
            options = [option for peer in self.peers() for option in self.change_or_levels(family, peer, peer=True)]
            return self.fill_parts([options]) if options else "unmet"
        if code == "weight_share_decomposition":
            return self.fill_parts([[[self.level("decomposition", m, p, t, b) for m in report_claims.DECOMPOSITION]]])
        if code == "per_child_unit_value_stable":
            kids = self.children()
            if not kids:
                return "unmet"
            return self.fill_parts([[[self.level("change", f"r_U@{k}", p, t, b)],
                                     [self.level("value", f"U@{k}", p, t), self.level("value", f"U@{k}", p, b)]]
                                    for k in kids])
        if code == "precision_sensitivity_shown":
            return self.fill_parts([[[self.level("value", m, p, month) for m in ("V", "Q") for month in (t, b)]]])
        if code == "country_and_world_change_shown":
            return self.fill_parts([[[self.level("value", "V", who, month) for who in (p, "ALL") for month in (t, b)]]])
        if code == "parent_child_match_V_and_Q":
            return self.parent_child()
        if code in ("missingness_listed", "failure_vs_not_collected_distinguished"):
            # failure_vs_not_collected_distinguished는 빠진 키(두 시점)마다 맞는 상태 주장이 있고, 사례 품목·두 시점의
            # 자료 상태 주장에 값이 틀린 것(WRONG_VALUE)이 없어야 한다. 틀린 모델 주장은 고치지 않으므로 그때는 unmet이다.
            if code == "failure_vs_not_collected_distinguished" and self.wrong_status():
                return "unmet"
            gaps = self.gaps(family)
            if gaps:
                return self.fill_parts([self.status_options(claims) for claims in gaps.values()])
            if code == "failure_vs_not_collected_distinguished":
                return "met"  # 빠진 키가 없으면 WRONG_VALUE가 없기만 하면 채운다(§5.3)
            # 빠진 키가 없으면 둘 가운데 하나: 비교국의 빠진 자료 상태, 또는 계산할 수 없는 계열 지표를 null로 적은 주장
            peer_options = self.status_options(self.peer_statuses())
            if (peer_options and self.part_met(peer_options)) or self.null_listed(family):
                return "met"
            # 덧붙이는 것은 비교국 빠진 상태뿐이다(null 주장은 덧붙이지 않는다, NULL_BASES 주석)
            return self.fill_parts([peer_options]) if peer_options else "unmet"
        return "unmet"


def evidence_claims(case: dict, codes: dict, claims: list, evidence: list) -> dict:
    """필수 근거 코드(evidence_codes 출력)마다 §5.3 조건을 보고 채울 주장을 덧붙인다.

    돌려주는 값: {"claims": 덧붙인 typed claim(claim_id e{번호}), "log": trace state_change evidence_claims에 싣는 값
    {"required": codes, "added": [{"signal", "code", "claims": [요청 모양]}], "unmet": [{"signal", "code"}],
    "no_action": [{"signal", "code"}]}}. 요청 모양은 checklist_claims와 같은 {claim_id, claim_type, metric_id} 또는
    {claim_id, claim_type: data_status, evidence_id}다. claims(보고서의 주장)와 입력을 바꾸지 않는다."""
    view = _EvidenceView(case, list(claims or []), list(evidence or []))
    log: dict = {"required": {k: list(v) for k, v in (codes or {}).items()}, "added": [], "unmet": [], "no_action": []}
    for family in policy_required_evidence.SIGNAL_CODES:
        for code in (codes or {}).get(family) or []:
            before = len(view.added)
            outcome = view.code(family, code)
            if outcome == "added":
                log["added"].append({"signal": family, "code": code,
                                     "claims": [request for _, request in view.added[before:]]})
            elif outcome in ("unmet", "no_action"):
                log[outcome].append({"signal": family, "code": code})
    return {"claims": [claim for claim, _ in view.added], "log": log}


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
            statuses = _statuses_of(evidence)
            filled = report_claims.run({"mode": mode, "case": case, "metrics": _metrics_of(evidence),
                                        "statuses": statuses, "requests": _requests_of(draft, statuses)})
        # 필수 근거 주장 덧붙이기(모든 모드 같은 규칙). freeform도 덧붙이는 주장은 단위 R1의 틀 채우기(fill)로 검증된 지표에서
        # 채운다(모델 주장은 R1 freeform이 그대로 돌려준 것이고, R1을 두 번 부를 뿐 R1을 고치지 않는다).
        extra = evidence_claims(case, inp.get("required_codes") or {}, filled["claims"], evidence)
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
            "claims": list(filled["claims"]) + extra["claims"], "narrative": draft.get("narrative"),
            "hypotheses": draft.get("hypotheses"),
            "review_status": draft.get("review_status"), "signal_status": draft.get("signal_status"),
            "unresolved_evidence": unresolved, "validator_findings": []})
        return {"report": rendered["report"], "rejected": list(filled.get("rejected") or []),
                "evidence_claims": extra["log"]}

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

    def reference(evidence: list) -> dict:
        # 모델 모드의 규칙 참고값(MT1 결정 ⑬: 모델 상태와 나란히 적는 참고값). P3을 그대로 부르고 모델 상태를 고치지 않는다.
        state = evidence_state(case, evidence)
        return policy_signal_decide.run({"policy": policy, "case": case, "evidence": state})

    wired = evidence_state is not None and policy is not None
    return Ports(tool=tool, budget=budget, build_report=build_report, check_report=check_report,
                 checklist_draft=checklist_draft, required_evidence=required,
                 reference_status=reference if wired else None, evidence_reference=reference if wired else None)


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
        self.reference_text: str | None = None  # 모델 모드에 실은 규칙 참고값 문구(Critic에도 준다)
        self.reference_available = False  # 마지막으로 실은 참고값이 계산된 값이었나(계산 불가였으면 근거가 갖춰질 때 다시 싣는다)
        self.reference_seen = 0  # 마지막 참고값을 계산할 때의 봉투 수(수정 단계에서 새 봉투를 받으면 다시 계산한다)

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

    def directed(self) -> bool:
        """조립(AS2)이 켠 차례 규칙: 초안은 도구 없는 차례에서만, 도구 차례는 필수 결과가 빠지고 예산이 있을 때만."""
        return self.ports.drafts_only_without_tools and self.ports.required_tools is not None

    def pending_tools(self, requested: list) -> list:
        """이 차례에 아직 없는 필수 결과: 필수 도구 가운데 결과를 받지 못한 것 + Critic이 재조회를 요청했는데 이 단계에서
        아직 부르지 않은 도구(나온 순서, 중복 없음)."""
        called = {c.get("tool") for c in self.executed if c.get("stage") == self.stage}
        names = self.missing_required_tools() + [name for name in requested if name not in called]
        return list(dict.fromkeys(names))

    def investigate(self, messages: list[dict], *, allowance: str, max_tool_turns: int, tools_enabled: bool,
                    requested: list | None = None) -> dict:
        """조사자 차례를 도구 호출이 끝날 때까지 돈다.

        {"draft": 초안 또는 None, "problems": 형식 문제, "status_notes": 허용 상태 관찰, "message": 마지막 모델 메시지,
        "was_draft": 마지막 답이 초안 글이었나}를 돌려준다. tools_enabled가 거짓(비교 불가)이면 도구를 주지 않고, 모델이
        불러도 not_comparable로 막는다."""
        tool_turns, refused_turns, nudged, force_draft = 0, 0, False, False
        directed = self.directed()
        while True:
            self.check_deadline()
            can_call = tools_enabled and tool_turns < max_tool_turns and self._allowance_left(allowance) > 0
            pending = self.pending_tools(requested or []) if directed else []
            # 차례 규칙(AS2 ⑲): 필수 결과가 빠졌고 예산이 있으면 도구 차례(tool_choice required, 도구 목록은 전부),
            # 아니면 곧바로 도구 없는 초안 차례(초안 요청 메시지 + json_object). 조립이 켜지 않으면 전과 같다.
            allow = (can_call and bool(pending) if directed else can_call) and not force_draft
            if self.ports.reference_status is not None and (not allow or nudged or not self.missing_required_tools()) \
                    and (self.reference_text is None
                         or (not self.missing_required_tools()
                             and (not self.reference_available or self.lookup_count() > self.reference_seen))):
                messages.append(self.reference_message())
            if directed and allow:
                messages.append(investigator.pending_tools_message(pending))
            result = investigator.step(self.client, messages, stage=self.stage, mode=self.mode,
                                       signals=self.signals, allow_tools=allow,
                                       tool_choice="required" if directed and allow else "auto")
            missing = self.missing_required_tools() if result["kind"] == "draft" and allow and not nudged \
                and not directed else []
            if missing:
                # 공개 판정 규칙에 필요한 도구를 받지 않고 쓴 초안: 받지 않고 한 번만 돌려보낸다(차례마다 1회, 모든 모드 같음)
                nudged = True
                self.state("draft_refused", result["draft"], missing_tools=missing)
                messages.append(investigator.assistant_message({"content": result["message"].get("content") or ""}))
                messages.append(investigator.required_tools_message(missing))
                continue
            if result["kind"] == "draft" and allow and self.ports.drafts_only_without_tools:
                # 도구를 준 차례의 초안 본문은 구조화 출력이 실리지 않은 답이다. 버리고 도구 없는 초안 요청으로 다시 받는다
                force_draft = True
                self.state("draft_discarded", result["draft"], problems=result["problems"])
                continue
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

    def lookup_count(self) -> int:
        """받은 조회 봉투 수(verify_evidence 빼고). 참고값을 계산한 뒤 새 조회 결과가 왔는지 가른다."""
        return len([e for e in self.evidence if isinstance(e, dict) and e.get("tool") != "verify_evidence"])

    def reference_message(self) -> dict:
        """규칙 참고값 메시지(모든 모델 모드에 같은 문구·같은 시점): 필수 도구 결과를 받은 뒤(또는 도구를 더 줄 수 없는
        차례, 필수 조회를 한 번 돌려보낸 뒤) 첫 조사자 요청 앞에 한 번 싣는다. P3을 돌릴 수 없으면 계산 불가 문구다.
        trace에는 state_change rule_reference로 남긴다. 모델 상태를 고치지 않는다(MT1 결정 ⑬)."""
        self.reference_seen = self.lookup_count()
        try:
            decided = self.ports.reference_status(list(self.evidence))
        except ValueError as exc:  # P3·근거 상태 변환의 입력 검사 오류만 계산 불가로 둔다(배선 오류 등은 CODE_ERROR로 올린다)
            statuses, basis, reason = None, None, type(exc).__name__
            detail = str(exc)[:300]
            self.reference_text = investigator.reference_unavailable_text(self.missing_required_tools())
        else:
            statuses, basis = decided["signal_status"], decided["basis"]
            reason, detail = None, None
            self.reference_text = investigator.reference_text(self.signals, statuses, basis)
        self.reference_available = statuses is not None
        self.sink.emit("state_change", self.stage, {"phase": "rule_reference", "available": statuses is not None,
                                                    "signal_status": statuses, "basis": basis, "error": reason,
                                                    "error_detail": detail})
        return {"role": "user", "content": self.reference_text}

    def missing_required_tools(self) -> list:
        """조사자가 초안 전에 받아야 하는데 아직 결과를 받지 못한 도구(Ports.required_tools, 없으면 강제하지 않는다)."""
        if self.ports.required_tools is None:
            return []
        received = {e.get("tool") for e in self.evidence if isinstance(e, dict) and e.get("retryable_error") is None}
        return [name for name in self.ports.required_tools(self.case) or [] if name not in received]

    # 보고서와 판정 ----------------------------------------------------------------------------------------------
    def build(self, draft: dict) -> dict:
        """보고서를 만든다. 필수 근거 코드(evidence_codes)를 넘겨 build_report가 채울 주장을 덧붙이게 하고, 덧붙인 결과를
        trace state_change evidence_claims로 남긴다(build_report가 결과를 돌려줄 때)."""
        codes = evidence_codes(self.signals, draft.get("signal_status"), self.reference_for_codes())
        built = self.ports.build_report({"case": self.case, "mode": self.mode, "run_id": self.ctx.run_id,
                                         "draft": draft, "evidence": list(self.evidence), "required_codes": codes})
        self.rejected = list(built.get("rejected") or [])
        if isinstance(built.get("evidence_claims"), dict):
            self.state("evidence_claims", draft, **built["evidence_claims"])
        return built["report"]

    def reference_for_codes(self) -> dict | None:
        """필수 근거 코드를 고를 때 쓰는 규칙 참고값(P3 출력). 없거나 계산할 수 없으면(입력 검사 오류) None이다. 모델에게
        싣는 참고값 문구·trace rule_reference와 관계없다(배선 오류는 참고값처럼 CODE_ERROR로 올린다)."""
        if self.ports.evidence_reference is None:
            return None
        try:
            return self.ports.evidence_reference(list(self.evidence))
        except ValueError:
            return None

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
        kept_draft = None  # 흐름 수정 (나): 수정본이 막히면 둘 수정 전 초안(보고서, 초안, verify 단계 판정)
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
                                       self.limits.revision_requeries, reference=self.reference_text)
                # 흐름 수정 (가): 발동하지 않은 신호에만 쓰는 도구의 재조회 요청은 버린다(needs_revision은 그대로)
                kept, dropped = split_requery(review["requery"], self.signals)
                review = dict(review, requery=kept)
                self.state("after_critic", draft, needs_revision=review["needs_revision"],
                           findings=len(review["findings"]), requery=len(kept), requery_dropped=dropped,
                           problems=review["problems"])
                self.sink.emit("stage_end", "critic", {"stage": "critic"})
                self.stage = "basic"
            code_missing = self.missing_required_tools() if self.directed() and comparable \
                and self._allowance_left("requery") > 0 else []
            if code_missing:  # 코드 지적(AS2 ⑲): 빠진 필수 결과를 Critic 결과(agent는 수정 지시)에 덧붙이고 수정 1회
                finding = investigator.code_finding(code_missing)
                if review is not None:
                    review = dict(review, findings=list(review["findings"]) + [finding], needs_revision=True)
                self.state("code_finding", draft, missing_tools=code_missing)
            self.verify(draft, "verify")
            check = self.check(report, "verify")
            if review is not None and review["needs_revision"] and not code_missing and check["schema_ok"] \
                    and (self.mode == "freeform" or check["validator_ok"]):
                # 흐름 수정 (나)의 조건 ①·②: 수정을 여는 까닭이 Critic의 수정 요구뿐이고 수정 전 검사를 통과했다
                kept_draft = (report, draft, check)
            if not check["schema_ok"]:
                problems, findings = ["보고서 스키마 검사 실패"], check["findings"]
            elif self.mode != "freeform" and not check["validator_ok"]:
                findings = check["findings"]
            elif not (review and review["needs_revision"]) and not code_missing:
                self.stage = "final"
                return self.complete(report, draft, check)
            if code_missing and review is None:
                findings = list(findings) + [investigator.code_finding(code_missing)]
        # 수정 단계(1회). 비교 불가 사례는 여기서도 도구를 주지 않는다(조기 종료, 개발 플랜 §6.6).
        self.stage = "revision"
        self.revision_used = True
        self.sink.emit("stage_start", "revision", {"stage": "revision"})
        if turn["was_draft"]:
            messages.append(investigator.assistant_message({"content": turn["message"].get("content") or ""}))
        messages.append(investigator.feedback_message(problems, review, findings, self.remaining(comparable)))
        turn = self.investigate(messages, allowance="requery", max_tool_turns=self.limits.revision_requeries,
                                tools_enabled=comparable,
                                requested=[q["tool"] for q in (review or {}).get("requery") or []])
        draft, problems = turn["draft"], turn["problems"]
        self.state("revised", draft, problems=len(problems), problem_list=problems, status_notes=turn["status_notes"])
        self.sink.emit("stage_end", "revision", {"stage": "revision"})
        self.stage = "final"
        self.sink.emit("stage_start", "final", {"stage": "final"})
        if draft is None or problems:
            return self.blocked_revision(kept_draft, cause_codes.SCHEMA_INVALID, "draft_format",
                                         "수정 1회 뒤에도 초안 형식 검사에 실패했다")
        report = self.build(draft)
        self.verify(draft, "final_verify")
        check = self.check(report, "final")
        if not check["schema_ok"]:
            return self.blocked_revision(kept_draft, cause_codes.SCHEMA_INVALID, "schema",
                                         "수정 1회 뒤에도 보고서 스키마 검사에 실패했다")
        if self.mode != "freeform" and not check["validator_ok"]:
            return self.blocked_revision(kept_draft, cause_codes.VALIDATOR_BLOCKED, "validator",
                                         "수정 1회 뒤에도 검증기가 막았다")
        return self.complete(report, draft, check)

    def blocked_revision(self, kept_draft: tuple | None, code: str, blocked_by: str, detail: str) -> dict:
        """수정본이 최종 단계에서 막혔다. 흐름 수정 (나)(AS2 ㉔): 수정을 연 까닭이 Critic의 수정 요구뿐이고 수정 전 초안이
        수정 전 검사를 통과했으면(kept_draft) 수정본을 버리고 수정 전 초안의 보고서와 그 verify 단계 판정으로 끝낸다.
        도구·모델 요청을 더 쓰지 않고 검사도 다시 하지 않는다. trace state_change revision_discarded(막은 곳 blocked_by,
        그대로였다면 났을 원인 would_be_cause). 아니면 지금처럼 INVALID다(budget_block revision_limit)."""
        if kept_draft is None:
            raise self.invalid(code, detail)
        report, draft, check = kept_draft
        self.state("revision_discarded", draft, blocked_by=blocked_by, would_be_cause=code,
                   kept_report_id=report.get("report_id") if isinstance(report, dict) else None)
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
