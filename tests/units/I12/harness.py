"""단위 I12 시험용 대역(시험 파일 안에만 두는 가짜 도구·보고서·검증기 자리와 모델 답). 네트워크·스냅샷을 쓰지 않는다."""
import json
from decimal import Decimal

from tradesentry.runlog import trace as trace_log
from tradesentry.workflow import model_client as mc
from tradesentry.workflow import orchestrate

from ..I7.fakes import FakeClock, ScriptedTransport, ok_body

SNAP = "controlled_fixture_v0"
EV = [f"ev:{SNAP}:observation:{n}" for n in (1024, 1025, 2048, 2049)]
CASE_A = {"case_id": "A-composition", "hs6": "850450", "partner": "CN", "month": "202401", "baseline_month": "202301",
          "signals": {"unit_value": "TRIGGERED", "share": "NOT_TRIGGERED"}, "snapshot_id": SNAP,
          "policy_version": "dev-0.1"}
RUN_ID = "run_case-260925143015"


def envelope(tool, query_id, *, comparable=True, metrics=(), evidence=()):
    return {"query_id": query_id, "tool": tool, "scope": {"hs6": "850450", "partner": "CN"}, "snapshot_id": SNAP,
            "source_kind": "controlled", "evidence_ids": list(evidence), "metrics": list(metrics),
            "comparability": {"comparable": comparable} if tool == "check_comparability" else {},
            "missingness": [], "retryable_error": None, "elapsed_ms": 5}


def metric(metric_id, symbol, value, unit, evidence):
    return {"metric_id": metric_id, "formula_version": "f1",
            "inputs": {"metric": symbol, "hs6": "850450", "partner": "CN", "period": "202401",
                       "baseline_period": "202301"},
            "evidence_ids": list(evidence), "value": Decimal(value), "unit": unit, "comparability_flags": [],
            "tolerance": None}


ENVELOPES = {
    "check_comparability": envelope("check_comparability", "q-cc"),
    "get_history": envelope("get_history", "q-gh", metrics=[metric("m-rU", "r_U", "-40.0", "%", EV[:2])],
                            evidence=EV[:2]),
    "decompose_hs": envelope("decompose_hs", "q-dh", metrics=[metric("m-mix", "mix_effect", "-2.40", "USD/kg",
                                                                     EV[2:])], evidence=EV[2:]),
    "compare_partners": envelope("compare_partners", "q-cp"),
    "verify_evidence": envelope("verify_evidence", "q-ve", evidence=EV[:2]),
}


def draft(status="MONITOR", claims=None, **over):
    body = {"review_status": status, "signal_status": {"unit_value": status, "share": "NOT_TRIGGERED"},
            "claims": claims if claims is not None else [{"claim_type": "change", "metric_id": "m-rU"}],
            "narrative": "단가 신호는 하위품목 구성 변화로 설명될 가능성이 있다.", "hypotheses": ["구성 변화 가설"]}
    body.update(over)
    return body


def draft_answer(**kw):
    return {"body": ok_body(json.dumps(draft(**kw), ensure_ascii=False), prompt_tokens=1500, completion_tokens=150)}


def text_answer(text):
    return {"body": ok_body(text, prompt_tokens=1500, completion_tokens=40)}


def critic_answer(needs_revision=False, requery=()):
    findings = [{"kind": "missing_evidence", "text": "하위품목 분해가 없다.", "claim_refs": []}] if needs_revision else []
    body = {"findings": findings, "requery": list(requery), "needs_revision": needs_revision}
    return {"body": ok_body(json.dumps(body, ensure_ascii=False), prompt_tokens=1200, completion_tokens=90)}


def tools_answer(*names, args=None):
    calls = [{"id": f"call_{i}", "type": "function",
              "function": {"name": n, "arguments": json.dumps((args or {}).get(n, {}))}} for i, n in enumerate(names)]
    return {"body": ok_body(None, tool_calls=calls, prompt_tokens=1400, completion_tokens=30)}


class FakePorts:
    """Ports에 넣는 가짜 자리. 부른 순서를 남기고, 검사 결과는 정해 둔 차례대로 돌려준다."""

    def __init__(self, checks=None, checklist_status="HOLD", budget_limit=8, rejected=()):
        self.tool_calls = []
        self.budget_asks = []
        self.checks = list(checks or [])
        self.check_calls = 0
        self.checklist_status = checklist_status
        self.budget_limit = budget_limit
        self.rejected = list(rejected)

    def tool(self, name, args):
        self.tool_calls.append((name, args))
        return json.loads(trace_log.dumps(ENVELOPES[name]), parse_float=Decimal)

    def budget(self, executed, candidate):
        self.budget_asks.append(len(executed))
        if len(executed) >= self.budget_limit:
            return {"allowed": False, "reason": "tool_attempts_limit"}
        return {"allowed": True, "reason": None}

    def build_report(self, inp):
        d = inp["draft"]
        report = {"report_id": f"r-{inp['run_id']}", "run_id": inp["run_id"], "case_id": inp["case"]["case_id"],
                  "mode": inp["mode"], "claims": d["claims"], "narrative": d["narrative"], "hypotheses": d["hypotheses"],
                  "review_status": d["review_status"], "signal_status": d["signal_status"],
                  "unresolved_evidence": d.get("unresolved_evidence", False), "evidence_ids": EV[:2],
                  "validator_findings": [],
                  "report_hash": "0" * 64, "created_at": "2026-09-25T14:30:15+09:00",
                  "policy_version": inp["case"]["policy_version"], "snapshot_id": SNAP, "grouping_version": "g0"}
        return {"report": report, "rejected": list(self.rejected)}

    def check_report(self, inp):
        self.check_calls += 1
        if self.checks:
            return self.checks.pop(0)
        return {"schema_ok": True, "validator_ok": True, "findings": []}

    def checklist_draft(self, inp):
        s = self.checklist_status
        return {"review_status": s, "signal_status": {"unit_value": s, "share": "NOT_TRIGGERED"},
                "claims": [{"claim_type": "change", "metric_id": "m-rU"}], "narrative": "", "hypotheses": []}

    def required_evidence(self, case):
        return ["parent_child_match_V_and_Q", "weight_share_decomposition"]

    def ports(self):
        return orchestrate.Ports(tool=self.tool, budget=self.budget, build_report=self.build_report,
                                 check_report=self.check_report, checklist_draft=self.checklist_draft,
                                 required_evidence=self.required_evidence)


PASS = {"schema_ok": True, "validator_ok": True, "findings": []}
BLOCK = {"schema_ok": True, "validator_ok": False, "findings": [{"rule": "unbacked_prose", "where": "narrative"}]}
SCHEMA_FAIL = {"schema_ok": False, "validator_ok": False, "findings": [{"rule": "series_claim_missing"}]}


def run_case(mode, script, fake=None, *, case=None, elapsed_ms=700, clock=None, dataset="controlled_fixture_v0",
             transport=None):
    """모델 답 목록(script)과 가짜 자리로 사례 1건을 돌린다. (결과, trace 레코드, 가짜 자리, 전송)을 돌려준다."""
    config = mc.load_model_config()
    clock = clock or FakeClock()
    fake = fake or FakePorts()
    if transport is None and mode != "checklist":
        transport = ScriptedTransport(script, clock, elapsed_ms=elapsed_ms)
    sink = trace_log.MemoryTrace(RUN_ID, clock=trace_log.now_kst)
    ctx = orchestrate.RunContext(run_id=RUN_ID, case=case or CASE_A, mode=mode, dataset=dataset,
                                 rulebook_version="RB-1", grouping_version="g0", code_version="abc1234")
    result = orchestrate.orchestrate(ctx, fake.ports(), config, transport=transport, sink=sink,
                                     clock_ms=clock.clock_ms, sleep_ms=clock.sleep_ms)
    return result, sink.records, fake, transport


def events(records, name):
    return [r for r in records if r["event"] == name]
