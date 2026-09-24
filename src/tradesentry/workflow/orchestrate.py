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
   초안 형식 검사(단위 I10)와 보고서 쪽 스키마 검사(검증기 자리)에 실패하면 Critic을 건너뛰고 수정 단계로 간다.
2. critic(full·freeform만): Critic 한 차례(도구 없음). agent는 Critic이 없다.
3. verify_evidence(기본 경로의 예약 1회) → 검증기 판정. 수정이 필요 없으면(스키마 통과, 검증기 통과 또는 freeform,
   Critic이 수정을 요청하지 않음) 여기서 COMPLETED.
4. revision(1회): 조사자가 지적을 받고 재조회(최대 2회) 뒤 고친 초안을 쓴다. Critic은 다시 부르지 않는다.
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
- tool_attempts는 막힌 시도까지 모든 시도를 센다(자료 계약 §8.1 "넘은 실행은 실제 값"). 몫을 통과한 시도는 도구
  예산 자리(단위 I6)에 한 번 더 묻는다(도구 8회, 같은 인자 재호출 등은 I6 규칙).
- 코드는 모델의 틀린 상태를 고치지 않는다. 형식·검증기 문제는 수정 단계로 보내거나 INVALID로 끝낸다.

다른 작업 단위를 부르는 자리(Ports). unit_ports가 그 단위들의 run을 부르는 얇은 배선을 한곳에 모았다. 보고서·
검증기(MT3 R1~R4)와 정책(MT1 P3~P5)은 각 작업 브랜치에 커밋된 입출력에 맞췄고(병합 전 대조), 도구 5개·도구 예산(MT2)은
아직 없어 제안 모양이다 `[미확인]`. 정책 객체(K4)와 근거 행 풀기(K3)는 사례 조사 조립(로드맵 AS2)이 인자로 넘긴다.
흐름 조정 자체는 Ports만 본다.

기록: 사례 1건의 trace 이벤트(단위 L1)를 sink로 내고, 끝에 실행 결과 기록의 실행 쪽 키(단위 L2)를 만든다. 멈춘 실행의
errors는 원인 분류 코드 항목 하나다(단위 L3: 원인, 누적 시도, 마지막 정상 근거). COMPLETED가 아니면 보고서를 돌려주지
않는다(검증기를 통과하지 못한 보고서는 공유 대상이 아니다).
"""
from dataclasses import dataclass
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


@dataclass
class Ports:
    """흐름 조정이 부르는 다른 단위 자리.

    tool(이름, 인자) -> 봉투 / budget(실행한 시도 목록, 후보) -> {"allowed", "reason"} /
    build_report({"case","mode","run_id","draft","evidence"}) -> 보고서 /
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


def _statuses_of(evidence: list) -> list:
    """봉투의 missingness 항목을 단위 R1의 자료 상태 항목으로 옮긴다(근거 ID 하나에 항목 하나, status_id = 근거 ID).

    missingness 항목의 키(partner·hs_code·month·observation_status·evidence_ids)는 단위 P3(MT1)이 가정한 모양이다.
    도구(MT2)가 다른 모양을 내면 AS2가 여기를 맞춘다 `[미확인]`."""
    statuses = []
    for envelope in evidence:
        for item in (envelope.get("missingness") or []) if isinstance(envelope, dict) else []:
            if not isinstance(item, dict):
                continue
            code = str(item.get("hs_code") or item.get("hs6") or "")
            for ev in item.get("evidence_ids") or []:
                if isinstance(ev, str):
                    statuses.append({"status_id": ev, "hs6": item.get("hs6") or code[:6],
                                     "partner": item.get("partner"), "period": item.get("period") or item.get("month"),
                                     "hs10": item.get("hs10") or (code if len(code) == 10 else None),
                                     "observation_status": item.get("observation_status"), "evidence_ids": [ev],
                                     "baseline_period": item.get("baseline_period")})
    return statuses


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
               clock: Callable[[], object] = trace_log.now_kst) -> Ports:
    """다른 트랙·작업 단위의 run을 부르는 배선. 보고서·검증기(MT3 R1~R4)와 정책(MT1 P3~P5)은 그 작업 브랜치에 커밋된
    입출력(2026-09-25 새벽 기준)에 맞췄고, 도구 5개·도구 예산(MT2)은 아직 없어 제안 모양이다 `[미확인]`.

    AS2(사례 조사 조립)가 넘겨야 하는 것: policy(단위 K4 정책 객체, checklist의 P3가 쓴다), rows(근거 ID 목록 ->
    {근거 ID: 스냅샷 행 또는 None}, 단위 K3 자료 접근층으로 푼다. 검증기 R3의 원본 대조에 쓴다).
    """
    made = {"reports": 0}

    def tool(name: str, args: dict) -> dict:
        return TOOL_UNITS[name].run({"case_id": case.get("case_id"), "snapshot_id": case.get("snapshot_id"),
                                     "scope": _scope(case), "args": args})

    def budget(executed: list, candidate: dict) -> dict:
        return tool_budget.run({"attempts": executed, "candidate": candidate,
                                "limits": {"tool_attempts": limits.tool_attempts}})

    def build_report(inp: dict) -> dict:
        draft, evidence = inp["draft"], inp["evidence"]
        if mode == "freeform":
            filled = report_claims.run({"mode": mode, "case": case, "claims": draft.get("claims") or []})
        else:
            filled = report_claims.run({"mode": mode, "case": case, "metrics": _metrics_of(evidence),
                                        "statuses": _statuses_of(evidence), "requests": _requests_of(draft)})
        aggregate = policy_case_aggregate.run({"signals": case.get("signals"),
                                               "signal_status": draft.get("signal_status")})
        made["reports"] += 1
        rendered = report_render.run({
            "report_id": f"{run_id}-report{made['reports']}", "run_id": run_id, "mode": mode,
            "created_at": trace_log.iso_kst(clock()), "policy_version": case.get("policy_version"),
            "snapshot_id": case.get("snapshot_id"), "grouping_version": grouping_version, "case": case,
            "claims": filled["claims"], "narrative": draft.get("narrative"), "hypotheses": draft.get("hypotheses"),
            "review_status": draft.get("review_status"), "signal_status": draft.get("signal_status"),
            "unresolved_evidence": aggregate["unresolved_evidence"], "validator_findings": []})
        return rendered["report"]

    def check_report(inp: dict) -> dict:
        report, evidence = inp["report"], inp["evidence"]
        ids = sorted({e for e in (report.get("evidence_ids") or []) if isinstance(e, str)}
                     | {e for env in evidence if isinstance(env, dict) for e in (env.get("evidence_ids") or [])
                        if isinstance(e, str)})
        out = validator_validate.run({
            "case": case, "report": report, "envelopes": evidence, "rows": rows(ids) if rows else {},
            "run": {"run_id": run_id, "mode": mode, "snapshot_id": case.get("snapshot_id"),
                    "policy_version": case.get("policy_version"), "grouping_version": grouping_version}})
        findings = out["findings"]
        decision = validator_gate.run({"mode": mode, "findings": findings, "revision_used": inp["revision_used"]})
        return {"schema_ok": not decision["schema_failed"],
                "validator_ok": not [f for f in findings if isinstance(f, dict) and f.get("check") == "validator"],
                "findings": findings}

    def checklist_draft(inp: dict) -> dict:
        evidence = inp["evidence"]
        missing = [m for e in evidence if isinstance(e, dict) for m in (e.get("missingness") or [])]
        decided = policy_signal_decide.run({"policy": policy, "case": case, "evidence": {"missingness": missing}})
        aggregate = policy_case_aggregate.run({"signals": case.get("signals"),
                                               "signal_status": decided["signal_status"]})
        return {"review_status": aggregate["review_status"], "signal_status": decided["signal_status"],
                "claims": checklist_claims(case, evidence), "narrative": "", "hypotheses": []}

    def required(case_obj: dict) -> object:
        return policy_required_evidence.run({"signals": case_obj.get("signals")})

    return Ports(tool=tool, budget=budget, build_report=build_report, check_report=check_report,
                 checklist_draft=checklist_draft, required_evidence=required)


def _unresolved(signal_status: dict) -> bool:
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
        self.tool_attempts = 0
        self.used = {"basic": 0, "comparison": 0, "requery": 0, "final_verify": 0}
        self.critic_used = False
        self.revision_used = False
        self.last_good_evidence: list[str] = []
        self.required = ports.required_evidence(ctx.case) if ports.required_evidence else None

    # 한도와 도구 시도 ---------------------------------------------------------------------------------------------
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
        self.tool_attempts += 1
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
        self.tool_attempts += 1
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

    # 조사자 ------------------------------------------------------------------------------------------------------
    def remaining(self) -> dict:
        return {"comparisons": max(0, self._allowance_left("comparison")),
                "requeries": max(0, self._allowance_left("requery")),
                "model_requests": max(0, self.limits.model_requests - self.budget.model_requests)}

    def investigate(self, messages: list[dict], *, allowance: str, max_tool_turns: int, tools_enabled: bool):
        """조사자 차례를 도구 호출이 끝날 때까지 돈다.

        (초안 또는 None, 문제 목록, 마지막 모델 메시지, 마지막 답이 초안 글이었나)를 돌려준다."""
        tool_turns, refused_turns = 0, 0
        while True:
            self.check_deadline()
            allow = tools_enabled and tool_turns < max_tool_turns and self._allowance_left(allowance) > 0
            result = investigator.step(self.client, messages, stage=self.stage, mode=self.mode,
                                       signals=self.signals, allow_tools=allow)
            if result["kind"] == "draft":
                return result["draft"], result["problems"], result["message"], True
            messages.append(investigator.assistant_message(result["message"]))
            if allow:
                tool_turns += 1
            else:
                refused_turns += 1
            for call in result["calls"]:
                if call["error"] is not None:
                    outcome = self.refuse(call["tool"], call["args"], "model", "invalid_call")
                elif not allow:
                    outcome = self.refuse(call["tool"], call["args"], "model", f"{allowance}_limit")
                else:
                    outcome = self.attempt(call["tool"], call["args"], source="model", allowance=allowance)
                result_view = outcome if outcome.get("blocked") else investigator.compact_envelope(outcome)
                messages.append(investigator.tool_result_message(call["id"], call["tool"] or "", result_view))
            if refused_turns >= 2:
                return None, ["도구 없이 초안을 쓰라는 요청에 두 번 도구를 불렀다"], result["message"], False

    # 보고서와 판정 ----------------------------------------------------------------------------------------------
    def build(self, draft: dict) -> dict:
        return self.ports.build_report({"case": self.case, "mode": self.mode, "run_id": self.ctx.run_id,
                                        "draft": draft, "evidence": list(self.evidence)})

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
                                                        "findings": result["findings"]})
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
        final.setdefault("unresolved_evidence", _unresolved(final["signal_status"]))
        statuses = final["signal_status"]
        if final["review_status"] not in investigator.REVIEW_STATUSES or not isinstance(statuses, dict) \
                or set(statuses) != set(investigator.SIGNAL_CODES) \
                or any(v not in investigator.SIGNAL_STATUSES for v in statuses.values()):
            raise model_client.RunStop(cause_codes.SCHEMA_INVALID, self.stage, "최종 보고서의 판정 상태가 값 집합 밖이다")
        self.state("final", final)
        return final

    # 모드별 흐름 -------------------------------------------------------------------------------------------------
    def comparable(self, envelope: dict) -> bool:
        """check_comparability 봉투의 comparability.comparable이 false면 비교 불가다(없으면 비교 가능으로 본다) `[미확인]`."""
        comparability = envelope.get("comparability") if isinstance(envelope, dict) else None
        return not (isinstance(comparability, dict) and comparability.get("comparable") is False)

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
        self.attempt("verify_evidence", _draft_refs(draft), source="code", allowance="verify")
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
                                                 self.remaining())
        draft, problems, message, was_draft = self.investigate(messages, allowance="comparison",
                                                               max_tool_turns=self.limits.investigator_comparisons,
                                                               tools_enabled=comparable)
        self.state("draft", draft, problems=len(problems))
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
                review = critic.review(self.client, prompts, self.case, draft, self.evidence,
                                       self.limits.revision_requeries)
                self.critic_used = True
                self.state("after_critic", draft, needs_revision=review["needs_revision"],
                           findings=len(review["findings"]), requery=len(review["requery"]))
                self.sink.emit("stage_end", "critic", {"stage": "critic"})
                self.stage = "basic"
            self.attempt("verify_evidence", _draft_refs(draft), source="code", allowance="verify")
            check = self.check(report, "verify")
            if not check["schema_ok"]:
                problems, findings = ["보고서 스키마 검사 실패"], check["findings"]
            elif self.mode != "freeform" and not check["validator_ok"]:
                findings = check["findings"]
            elif not (review and review["needs_revision"]):
                self.stage = "final"
                return self.complete(report, draft, check)
        # 수정 단계(1회)
        self.stage = "revision"
        self.revision_used = True
        self.sink.emit("stage_start", "revision", {"stage": "revision"})
        if was_draft:
            messages.append(investigator.assistant_message({"content": message.get("content") or ""}))
        messages.append(investigator.feedback_message(problems, review, findings, self.remaining()))
        draft, problems, message, was_draft = self.investigate(messages, allowance="requery",
                                                               max_tool_turns=self.limits.revision_requeries,
                                                               tools_enabled=True)
        self.state("revised", draft, problems=len(problems))
        self.sink.emit("stage_end", "revision", {"stage": "revision"})
        self.stage = "final"
        self.sink.emit("stage_start", "final", {"stage": "final"})
        if draft is None or problems:
            raise self.invalid(cause_codes.SCHEMA_INVALID, "수정 1회 뒤에도 초안 형식 검사에 실패했다")
        report = self.build(draft)
        self.attempt("verify_evidence", _draft_refs(draft), source="code", allowance="final_verify")
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
    "code_version", "replay": [trace 레코드], "config_dir"(선택)}. 모델 응답과 도구 봉투는 기록에서 재생하고, 보고서·
    검증기·정책·도구 예산은 unit_ports로 그 단위들을 부른다.
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
    ports.tool = replay.ReplayTools(records, clock).call
    sink = trace_log.MemoryTrace(ctx.run_id, clock=clock.wall)
    result = orchestrate(ctx, ports, config, transport=replay.ReplayTransport(records, clock), sink=sink,
                         clock_ms=clock.now_ms, sleep_ms=clock.sleep_ms)
    events = []
    for record in sink.records:
        data = record["data"]
        gist = data.get("kind") or data.get("phase") or data.get("tool") or data.get("execution_status")
        if record["event"] == "model_error":
            gist = f"HTTP {data.get('http_status')}" if data.get("http_status") is not None else data.get("error")
        events.append([record["event"], record["stage"], gist])
    return {"record": result["record"], "report": result["report"], "events": events}
