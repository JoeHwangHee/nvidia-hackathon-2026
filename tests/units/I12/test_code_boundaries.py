"""단위 I12 코드 경계 셋 시험(사용자 결정 2026-09-25(금) 22:22 ①②③, 결정 기록 *-model-decision-code-boundaries.md).

① review_status 코드 집계: 보고서를 만들 때마다 signal_status에서 자료 계약 §3.1 규칙(검증기 R3 aggregate_status와 같은
   계산)으로 review_status·unresolved_evidence를 채운다. 네 조합, checklist 불변, 네 모드, trace status_aggregated 모양,
   형식 불량 초안은 손대지 않음.
② 발동 신호 자기 계열 주장: 계열 주장(R3 signal_families 판정)이 없으면 그 신호의 변화 지표(r_U·d_s)를 받은 봉투에서 덧붙인다.
   없음→덧붙임, 있음→불변, 근거에 없음→덧붙이지 않음, 두 신호 발동, e{번호} 번호열 연속, freeform.
③ HOLD 합의 신호엔 빠진 도구 지적 없음: 초안 판정과 규칙 참고값이 둘 다 HOLD인 신호의 도구는 code_missing에서 뺀다.
   HOLD 합의→지적 없음, 단가만 합의→decompose_hs만 빼기, 참고값 None·불일치→기존, (나)로 완료되는 대본.
④ 중량 0 하위품목의 중량 비중 주장(사용자 결정 2026-09-26(토) 01:05 ①, 결정 기록 *-model-decision-zero-weight-claim.md):
   단가 신호 발동 + 초안 단가 판정 HOLD면 decompose_hs 봉투의 w@<HS10> = 0 지표마다 값 주장을 덧붙인다. HOLD+w=0→덧붙임
   (값·단위·자릿수는 R1 규칙), w>0만→없음, MAINTAIN·MONITOR→없음, 단가 미발동→없음, 같은 metric_id 있음→없음, 둘→둘 다,
   네 모드, trace 모양, 실제 검증기 R3에서 산문의 '0'이 뒷받침됨.
모델 답과 도구·검사 자리는 대역이다(harness.py, 네트워크·스냅샷 없음).
"""
import json
import unittest
from decimal import Decimal

from tradesentry.cli import dispatch
from tradesentry.runlog import cause_codes
from tradesentry.runlog import trace as trace_log
from tradesentry.validator import validate
from tradesentry.workflow import model_client as mc
from tradesentry.workflow import orchestrate

from ..I7.fakes import FakeClock, ScriptedTransport
from . import harness as h
from .test_evidence_claims import (B, BOTH, CHILD, CHILD_B, CHILD_T, DECOMPOSE, ENVELOPES, HISTORY, HS6, P, PARENT_B,
                                   PARENT_T, PARTNERS, SHARE_CASE, T, TYPED_rU, UV_CASE, envelope, filled, metric,
                                   run_flow, targets)

BOTH_CASE = dict(h.CASE_A, signals={"unit_value": "TRIGGERED", "share": "TRIGGERED"})
HOLD_REF = {"signal_status": {"unit_value": "HOLD", "share": "NOT_TRIGGERED"}, "basis": None}


def phases_of(records):
    return [r["data"]["phase"] for r in h.events(records, "state_change")]


def aggregated_events(records):
    return [r["data"] for r in h.events(records, "state_change") if r["data"]["phase"] == "status_aggregated"]


def code_findings(records):
    return [r["data"] for r in h.events(records, "state_change") if r["data"]["phase"] == "code_finding"]


def signal_draft(review, unit_value, share, **over):
    return h.draft_answer(status=review, signal_status={"unit_value": unit_value, "share": share}, **over)


class StatusAggregateTest(unittest.TestCase):
    """① 네 조합의 집계값과 unresolved_evidence, R3 계산과의 일치, trace 모양."""

    COMBOS = [  # (초안 review_status, 신호별 판정, 사례, 기대 review_status, 기대 unresolved_evidence)
        ("MONITOR", {"unit_value": "MAINTAIN", "share": "HOLD"}, BOTH_CASE, "MAINTAIN", True),
        ("MONITOR", {"unit_value": "HOLD", "share": "HOLD"}, BOTH_CASE, "HOLD", False),
        ("HOLD", {"unit_value": "MONITOR", "share": "MONITOR"}, BOTH_CASE, "MONITOR", False),
        ("MONITOR", {"unit_value": "HOLD", "share": "NOT_TRIGGERED"}, h.CASE_A, "HOLD", False),
    ]

    def test_four_combinations_are_filled_from_signal_status(self):
        for review, statuses, case, expected, unresolved in self.COMBOS:
            with self.subTest(statuses=statuses):
                result, records, _, _ = h.run_case("agent", [signal_draft(review, **statuses)], case=case)
                self.assertEqual(result["record"]["execution_status"], "COMPLETED")
                self.assertEqual((result["report"]["review_status"], result["report"]["unresolved_evidence"]),
                                 (expected, unresolved))
                self.assertEqual((result["record"]["review_status_final"], result["record"]["unresolved_evidence"]),
                                 (expected, unresolved))
                self.assertEqual(result["report"]["signal_status"], statuses)  # 신호별 판정은 모델 값 그대로
                # 검증기 R3와 같은 계산: 집계값을 적은 보고서에는 STATUS_INCONSISTENT가 없고 모델 값에는 있다
                report = {"review_status": expected, "unresolved_evidence": unresolved, "signal_status": statuses}
                self.assertEqual(validate._status_consistency(report, case), [])
                self.assertEqual([f["path"] for f in validate._status_consistency(dict(report, review_status=review),
                                                                                    case)], ["review_status"])

    def test_trace_only_when_the_model_value_differs_and_has_the_four_fields(self):
        result, records, _, _ = h.run_case("agent", [signal_draft("MONITOR", "MAINTAIN", "HOLD")], case=BOTH_CASE)
        events = aggregated_events(records)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], {"phase": "status_aggregated", "review_status": "MAINTAIN",
                                     "signal_status": {"unit_value": "MAINTAIN", "share": "HOLD"},
                                     "model_review_status": "MONITOR", "model_unresolved_evidence": None,
                                     "unresolved_evidence": True})
        phases = phases_of(records)
        self.assertEqual(phases[phases.index("status_aggregated") - 1], "draft")  # draft 사건은 모델 값
        kinds = [(r["event"], r["data"].get("phase")) for r in records if r["event"] in ("state_change", "validator_result")]
        self.assertLess(kinds.index(("state_change", "status_aggregated")), kinds.index(("validator_result", "draft")))
        draft = [r["data"] for r in h.events(records, "state_change") if r["data"]["phase"] == "draft"][0]
        self.assertEqual(draft["review_status"], "MONITOR")
        # 모델 값이 집계와 같으면 남기지 않는다
        _, records, _, _ = h.run_case("agent", [signal_draft("MAINTAIN", "MAINTAIN", "HOLD")], case=BOTH_CASE)
        self.assertEqual(aggregated_events(records), [])

    def test_every_model_mode_and_every_report_build(self):
        # full: 초안 보고서와 수정본 보고서 두 번 만든다 → 두 번 모두 집계하고 두 번 남긴다
        for mode in ("agent", "full", "freeform"):
            with self.subTest(mode=mode):
                claims = [dict(TYPED_rU, hs6="850450")] if mode == "freeform" else None
                script = [signal_draft("MONITOR", "HOLD", "NOT_TRIGGERED", claims=claims)]
                if mode != "agent":
                    script.append(h.critic_answer(needs_revision=True))
                    script.append(signal_draft("MONITOR", "HOLD", "NOT_TRIGGERED", claims=claims))
                else:
                    script.append(signal_draft("MONITOR", "HOLD", "NOT_TRIGGERED"))
                checks = [h.PASS, h.PASS, h.PASS] if mode != "agent" else [h.PASS, h.BLOCK, h.PASS]
                result, records, _, _ = h.run_case(mode, script, h.FakePorts(checks=checks))
                self.assertEqual((result["record"]["execution_status"], result["record"]["revision_used"]),
                                 ("COMPLETED", True))
                self.assertEqual(result["report"]["review_status"], "HOLD")
                events = aggregated_events(records)
                self.assertEqual([(e["model_review_status"], e["review_status"]) for e in events],
                                 [("MONITOR", "HOLD"), ("MONITOR", "HOLD")])
                self.assertEqual([r["stage"] for r in h.events(records, "state_change")
                                  if r["data"]["phase"] == "status_aggregated"], ["basic", "final"])

    def test_checklist_is_unchanged(self):
        result, records, _, _ = h.run_case("checklist", [], h.FakePorts(checklist_status="HOLD"))
        self.assertEqual((result["record"]["execution_status"], result["report"]["review_status"]), ("COMPLETED", "HOLD"))
        self.assertEqual(aggregated_events(records), [])
        self.assertNotIn("status_aggregated", phases_of(records))

    def flow(self, signals):
        flow = orchestrate._Flow.__new__(orchestrate._Flow)
        flow.signals, flow.stage = signals, "basic"
        flow.sink = trace_log.MemoryTrace(h.RUN_ID)
        return flow

    def test_malformed_or_untriggered_signal_status_is_left_alone(self):
        flow = self.flow(h.CASE_A["signals"])
        for statuses in ({"unit_value": "HOLD"}, {"unit_value": "PENDING", "share": "NOT_TRIGGERED"},
                         {"unit_value": "HOLD", "share": "NOT_TRIGGERED", "extra": "HOLD"}, "HOLD", None,
                         {"unit_value": "NOT_TRIGGERED", "share": "NOT_TRIGGERED"}):
            with self.subTest(statuses=statuses):
                draft = {"review_status": "MONITOR", "signal_status": statuses}
                self.assertIs(flow.aggregated(draft), draft)
                self.assertEqual(flow.sink.records, [])
        # 형식이 맞으면 사본을 돌려주고 원본은 바꾸지 않는다
        draft = {"review_status": "MONITOR", "signal_status": {"unit_value": "HOLD", "share": "NOT_TRIGGERED"}}
        out = flow.aggregated(draft)
        self.assertEqual((out["review_status"], out["unresolved_evidence"], draft["review_status"]),
                         ("HOLD", False, "MONITOR"))
        self.assertNotIn("unresolved_evidence", draft)

    def test_shared_function_matches_the_contract_rule(self):
        signals = BOTH_CASE["signals"]
        self.assertEqual(validate.aggregate_status({"unit_value": "MAINTAIN", "share": "HOLD"}, signals),
                         ("MAINTAIN", True))
        self.assertEqual(validate.aggregate_status({"unit_value": "MONITOR", "share": "HOLD"}, signals), ("HOLD", False))
        self.assertEqual(validate.aggregate_status({"unit_value": "MAINTAIN", "share": "MONITOR"}, signals),
                         ("MAINTAIN", False))
        self.assertEqual(validate.aggregate_status({"unit_value": "MONITOR", "share": "NOT_TRIGGERED"},
                                                   h.CASE_A["signals"]), ("MONITOR", False))
        # 발동하지 않은 신호의 (틀린) 판정은 세지 않고, 발동한 신호의 NOT_TRIGGERED도 세지 않는다
        self.assertEqual(validate.aggregate_status({"unit_value": "MONITOR", "share": "MAINTAIN"},
                                                   h.CASE_A["signals"]), ("MONITOR", False))
        self.assertIsNone(validate.aggregate_status({"unit_value": "NOT_TRIGGERED", "share": "NOT_TRIGGERED"},
                                                    h.CASE_A["signals"]))


class SignalClaimTest(unittest.TestCase):
    """② 계열 주장이 없으면 r_U·d_s 주장을 받은 봉투에서 덧붙인다(R3 signal_families 판정, e{번호} 번호열)."""

    def added(self, out):
        return [(a["signal"], a["code"], [(c["claim_id"], c["claim_type"], c["metric_id"]) for c in a["claims"]])
                for a in out["added"]]

    def test_missing_family_claims_are_added_for_both_signals(self):
        out = orchestrate.signal_claims(BOTH, [], ENVELOPES)
        self.assertEqual(targets(out["claims"]), [("change", "r_U", P, T, B), ("share_change", "d_s", P, T, B)])
        self.assertEqual([c["claim_id"] for c in out["claims"]], ["e1", "e2"])
        self.assertEqual(self.added(out), [("unit_value", "signal_claim", [("e1", "change", "m-rU")]),
                                           ("share", "signal_claim", [("e2", "share_change", "m-ds")])])
        # 덧붙인 뒤에는 R3의 계열 판정이 두 신호 모두 채워진다
        covered = set()
        for claim in out["claims"]:
            covered |= validate.signal_families(claim, BOTH)
        self.assertEqual(covered, {"unit_value", "share"})

    def test_existing_family_claims_leave_the_report_unchanged(self):
        claims = filled("m-rU", "m-ds")
        out = orchestrate.signal_claims(BOTH, claims, ENVELOPES)
        self.assertEqual((out["claims"], out["added"]), ([], []))
        self.assertEqual(targets(claims), [("change", "r_U", P, T, B), ("share_change", "d_s", P, T, B)])
        # 계열은 변화 지표가 아니어도 채워진다(U 수준 주장·s 수준 주장)
        out = orchestrate.signal_claims(BOTH, filled("m-U-t", "m-s-t"), ENVELOPES)
        self.assertEqual(out["claims"], [])

    def test_only_the_triggered_signal_is_filled(self):
        out = orchestrate.signal_claims(UV_CASE, [], ENVELOPES)
        self.assertEqual(targets(out["claims"]), [("change", "r_U", P, T, B)])
        out = orchestrate.signal_claims(SHARE_CASE, [], ENVELOPES)
        self.assertEqual(targets(out["claims"]), [("share_change", "d_s", P, T, B)])

    def test_nothing_is_added_when_the_change_metric_was_not_received(self):
        without_change = envelope("get_history", metrics=[m for m in HISTORY["metrics"]
                                                          if m["inputs"]["metric"] not in ("r_U", "d_s")])
        out = orchestrate.signal_claims(BOTH, [], [envelope("check_comparability"), without_change])
        self.assertEqual((out["claims"], out["added"]), ([], []))
        # 다른 품목·상대국의 변화 지표는 후보가 아니다
        peer_only = envelope("compare_partners", metrics=[ENVELOPES[3]["metrics"][0]])
        out = orchestrate.signal_claims(UV_CASE, [], [peer_only])
        self.assertEqual(out["claims"], [])

    def test_same_target_already_present_is_not_added_again(self):
        # 모델이 같은 대상(r_U)의 주장을 근거 없이 썼다: R3 판정으로는 계열이 채워지지만(형식이 맞으면) 같은 대상은 다시 넣지 않는다
        unbacked = dict(TYPED_rU, evidence_ids=[PARENT_T])
        out = orchestrate.signal_claims(UV_CASE, [unbacked], ENVELOPES)
        self.assertEqual(out["claims"], [])
        # 형식이 틀린 모델 주장(R3의 valid 밖)은 계열을 채우지 못하지만, 같은 대상이라 다시 넣지도 않는다
        broken = dict(TYPED_rU, unit=None)
        self.assertTrue(validate.claim_problems(broken))
        out = orchestrate.signal_claims(UV_CASE, [broken], ENVELOPES)
        self.assertEqual(out["claims"], [])

    def test_claim_ids_follow_the_same_e_numbering_as_the_required_evidence_claims(self):
        # 기존 덧붙임(_EvidenceView.add)의 번호 규칙 그대로: e{보고서 주장 수 + 1}부터, 이미 있는 id는 건너뛴다.
        # 모델 주장 c1(V)과 덧붙인 e1·e2 뒤에 r_U·d_s가 붙으면 e4·e5다(c1과 e1·e2를 합쳐 셋이므로 e3은 쓰지 않는다)
        claims = filled("m-V-t") + [dict(c, claim_id=f"e{i}") for i, c in enumerate(filled("m-V-b", "m-Q-t"), start=1)]
        out = orchestrate.signal_claims(BOTH, claims, ENVELOPES)
        self.assertEqual([c["claim_id"] for c in out["claims"]], ["e4", "e5"])
        self.assertEqual(len(claims), 3)  # 입력은 바꾸지 않는다
        # 같은 규칙을 evidence_claims에 적용한 결과와 같다(모델 주장 c1 하나 뒤 첫 덧붙임은 e2)
        first = orchestrate.evidence_claims(UV_CASE, {"unit_value": ["comparability_ok"]}, filled("m-V-t"), ENVELOPES)
        self.assertEqual([c["claim_id"] for c in first["claims"]], ["e2"])
        self.assertEqual([c["claim_id"] for c in orchestrate.signal_claims(UV_CASE, filled("m-V-t"), ENVELOPES)["claims"]],
                         ["e2"])

    def hold_script(self, mode, claims):
        script = [h.tools_answer("compare_partners"), h.draft_answer(status="HOLD", claims=claims,
                                                                    signal_status={"unit_value": "NOT_TRIGGERED",
                                                                                   "share": "HOLD"})]
        return script + ([h.critic_answer()] if mode in ("full", "freeform") else [])

    def test_flow_adds_d_s_after_the_required_evidence_claims_in_every_model_mode(self):
        # 점유율 HOLD(data_insufficient 합의): 필수 근거 코드는 missingness_listed 등이라 계열 주장을 만들지 않는다. 모델은 V만
        # 주장했으므로 코드가 d_s를 덧붙인다(freeform도 검증된 지표로 채운다)
        reference = {"signal_status": {"unit_value": "NOT_TRIGGERED", "share": "HOLD"},
                     "basis": {"unit_value": "not_triggered", "share": "data_insufficient"}}
        typed_v = filled("m-V-t")[0]
        for mode in ("agent", "full", "freeform"):
            with self.subTest(mode=mode):
                claims = [typed_v] if mode == "freeform" else [{"claim_type": "value", "metric_id": "m-V-t"}]
                result, records = run_flow(mode, self.hold_script(mode, claims), SHARE_CASE, reference)
                self.assertEqual(result["record"]["execution_status"], "COMPLETED")
                report_claims = result["report"]["claims"]
                self.assertEqual(targets(report_claims[:1]), [("value", "V", P, T, None)])
                self.assertEqual(targets(report_claims[-1:]), [("share_change", "d_s", P, T, B)])
                self.assertEqual(report_claims[-1]["claim_id"], f"e{len(report_claims)}")  # 기존 덧붙임과 같은 번호 규칙
                self.assertEqual(set(report_claims[-1]["evidence_ids"]), set(HISTORY["metrics"][11]["evidence_ids"]))
                logs = [r["data"] for r in h.events(records, "state_change") if r["data"]["phase"] == "evidence_claims"]
                self.assertEqual(len(logs), 1)
                self.assertEqual(logs[0]["added"][-1], {"signal": "share", "code": "signal_claim",
                                                        "claims": [{"claim_id": report_claims[-1]["claim_id"],
                                                                    "claim_type": "share_change", "metric_id": "m-ds"}]})
                if mode == "freeform":
                    self.assertEqual(report_claims[0], typed_v)  # 모델 주장 그대로
                # 덧붙인 뒤 R3의 계열 판정이 채워진다
                self.assertIn("share", set().union(*(validate.signal_families(c, SHARE_CASE) for c in report_claims)))

    def test_flow_adds_nothing_when_the_family_claim_exists(self):
        claims = [{"claim_type": "share_change", "metric_id": "m-ds"}]
        reference = {"signal_status": {"unit_value": "NOT_TRIGGERED", "share": "HOLD"},
                     "basis": {"unit_value": "not_triggered", "share": "data_insufficient"}}
        result, records = run_flow("agent", self.hold_script("agent", claims), SHARE_CASE, reference)
        self.assertEqual(targets(result["report"]["claims"]), [("share_change", "d_s", P, T, B)])
        logs = [r["data"] for r in h.events(records, "state_change") if r["data"]["phase"] == "evidence_claims"]
        self.assertEqual([a["code"] for a in logs[0]["added"]], [])


def run_hold(mode, script, *, case=None, checks=None, reference=HOLD_REF):
    """차례 규칙(directed)을 켠 흐름에 규칙 참고값(evidence_reference)을 준다. 필수 도구는 실제 조립 규칙이다."""
    fake = h.FakePorts(checks=checks)
    ports = fake.ports()
    ports.required_tools = dispatch.required_tools
    ports.drafts_only_without_tools = True
    if reference is not None:
        ports.evidence_reference = lambda evidence: reference
    clock = FakeClock()
    transport = ScriptedTransport(script, clock)
    sink = trace_log.MemoryTrace(h.RUN_ID)
    ctx = orchestrate.RunContext(run_id=h.RUN_ID, case=case or h.CASE_A, mode=mode, dataset="controlled_fixture_v0",
                                 rulebook_version="RB-1", grouping_version="g0", code_version="abc1234")
    result = orchestrate.orchestrate(ctx, ports, mc.load_model_config(), transport=transport, sink=sink,
                                     clock_ms=clock.clock_ms, sleep_ms=clock.sleep_ms)
    return result, sink.records, fake, transport


class HoldConsensusTest(unittest.TestCase):
    """③ 초안 판정과 규칙 참고값이 둘 다 HOLD인 신호에는 빠진 도구 지적을 내지 않는다."""

    HOLD_DRAFT = dict(status="HOLD")  # h.draft: signal_status unit_value HOLD, share NOT_TRIGGERED

    def test_hold_consensus_skips_every_missing_tool_and_completes_without_revision(self):
        for mode in ("agent", "full", "freeform"):
            with self.subTest(mode=mode):
                claims = [dict(TYPED_rU, hs6="850450")] if mode == "freeform" else None
                draft = h.draft_answer(status="HOLD", claims=claims)
                script = [draft, draft] + ([h.critic_answer()] if mode != "agent" else [])
                result, records, fake, transport = run_hold(mode, script)
                self.assertEqual((result["record"]["execution_status"], result["record"]["revision_used"],
                                  result["report"]["review_status"]), ("COMPLETED", False, "HOLD"))
                self.assertEqual(transport.script, [])
                self.assertEqual(code_findings(records), [{"phase": "code_finding", "review_status": "HOLD",
                                                           "signal_status": {"unit_value": "HOLD",
                                                                             "share": "NOT_TRIGGERED"},
                                                           "missing_tools": [],
                                                           "skipped_for_hold": ["compare_partners", "decompose_hs"]}])
                self.assertEqual([n for n, _ in fake.tool_calls],
                                 ["check_comparability", "get_history", "verify_evidence"])

    def test_unit_value_consensus_alone_skips_only_decompose(self):
        statuses = {"unit_value": "HOLD", "share": "MONITOR"}
        reference = {"signal_status": statuses, "basis": None}
        draft = h.draft_answer(status="HOLD", signal_status=statuses)
        # 수정 단계의 필수 조회 차례(⑲ pending_tools)는 지적에서 뺀 decompose_hs도 아직 없는 결과로 세어 required 차례를 한 번
        # 더 연다(③은 지적 시점만 바꾼다). 그 차례에 온 초안은 버려지고 도구 없는 초안 차례로 간다
        script = [draft, draft, h.critic_answer(), h.tools_answer("compare_partners"), draft, draft]
        result, records, fake, transport = run_hold("full", script, case=BOTH_CASE, reference=reference)
        self.assertEqual((result["record"]["execution_status"], result["record"]["revision_used"]), ("COMPLETED", True))
        self.assertEqual(phases_of(records).count("draft_discarded"), 2)
        self.assertEqual([(f["missing_tools"], f["skipped_for_hold"]) for f in code_findings(records)],
                         [(["compare_partners"], ["decompose_hs"])])
        self.assertIn("compare_partners", [n for n, _ in fake.tool_calls])
        self.assertNotIn("decompose_hs", [n for n, _ in fake.tool_calls])
        revision = [r["data"] for r in h.events(records, "model_request") if r["stage"] == "revision"]
        self.assertEqual(revision[0].get("tool_choice"), "required")
        self.assertEqual(transport.script, [])

    def test_without_a_reference_or_with_a_disagreeing_reference_the_finding_is_unchanged(self):
        draft = h.draft_answer(status="HOLD")
        script = [draft, draft, h.critic_answer(), h.tools_answer("compare_partners", "decompose_hs"), draft]
        monitor_ref = {"signal_status": {"unit_value": "MONITOR", "share": "NOT_TRIGGERED"}, "basis": None}
        for reference in (None, monitor_ref):
            with self.subTest(reference=reference):
                result, records, fake, _ = run_hold("full", list(script), reference=reference)
                self.assertEqual((result["record"]["execution_status"], result["record"]["revision_used"]),
                                 ("COMPLETED", True))
                self.assertEqual([(f["missing_tools"], f["skipped_for_hold"]) for f in code_findings(records)],
                                 [(["compare_partners", "decompose_hs"], [])])
        # 참고값이 HOLD인데 초안이 MONITOR면 합의가 아니다
        result, records, _, _ = run_hold("full", [h.draft_answer(), h.draft_answer(), h.critic_answer(),
                                                  h.tools_answer("compare_partners", "decompose_hs"), h.draft_answer()])
        self.assertEqual([f["skipped_for_hold"] for f in code_findings(records)], [[]])

    def test_no_event_when_nothing_is_missing(self):
        script = [h.tools_answer("compare_partners", "decompose_hs"), h.draft_answer(status="HOLD"), h.critic_answer()]
        result, records, _, _ = run_hold("full", script)
        self.assertEqual(result["record"]["execution_status"], "COMPLETED")
        self.assertEqual(code_findings(records), [])

    def test_critic_only_revision_that_is_blocked_falls_back_to_the_kept_draft(self):
        # (나): HOLD 합의로 코드 지적이 비어 Critic 수정 요구만으로 수정이 열리고, 수정본이 검증기에 막히면 수정 전 초안으로 끝난다.
        # 수정 단계의 필수 조회 차례(required)에 온 초안은 버려지고 도구 없는 초안 차례로 간다(⑲ 그대로)
        hold = h.draft_answer(status="HOLD")
        revised = h.draft_answer(status="MAINTAIN")
        script = [hold, hold, h.critic_answer(needs_revision=True), revised, revised]
        result, records, fake, transport = run_hold("full", script, checks=[h.PASS, h.PASS, h.BLOCK])
        record = result["record"]
        self.assertEqual((record["execution_status"], record["errors"], record["critic_used"], record["revision_used"]),
                         ("COMPLETED", [], True, True))
        self.assertEqual((result["report"]["review_status"], record["review_status_final"]), ("HOLD", "HOLD"))
        phases = phases_of(records)
        self.assertEqual(phases[-2:], ["revision_discarded", "final"])
        discarded = [r["data"] for r in h.events(records, "state_change") if r["data"]["phase"] == "revision_discarded"]
        self.assertEqual((discarded[0]["blocked_by"], discarded[0]["would_be_cause"]),
                         ("validator", cause_codes.VALIDATOR_BLOCKED))
        self.assertEqual([f["missing_tools"] for f in code_findings(records)], [[]])
        self.assertEqual(h.events(records, "budget_block"), [])
        self.assertEqual(fake.check_calls, 3)
        self.assertEqual(transport.script, [])


# ④ 중량 0 하위품목 봉투: CHILD(8504501000)는 비교월 T에 중량 0, 기준월 B에 60.0. CHILD2(8504502000)는 두 시점 모두 중량 0
CHILD2 = "8504502000"
W_ZERO_T = metric("m-w0-t", f"w@{CHILD}", "0.0", "%", [CHILD_T, PARENT_T])
W_POS_B = metric("m-w60-b", f"w@{CHILD}", "60.0", "%", [CHILD_B, PARENT_B], period=B)
W2_ZERO_T = metric("m-w2-t", f"w@{CHILD2}", "0", "%", [CHILD_T, PARENT_T])
W2_ZERO_B = metric("m-w2-b", f"w@{CHILD2}", "0.00", "%", [CHILD_B, PARENT_B], period=B)


def decompose_with(*weights):
    return envelope("decompose_hs", metrics=list(DECOMPOSE["metrics"]) + list(weights), evidence=DECOMPOSE["evidence_ids"],
                    comparability=DECOMPOSE["comparability"])


ZERO_ENVELOPES = [envelope("check_comparability"), HISTORY, decompose_with(W_ZERO_T, W_POS_B), PARTNERS]
TWO_ZERO_ENVELOPES = [envelope("check_comparability"), HISTORY, decompose_with(W_ZERO_T, W_POS_B, W2_ZERO_T, W2_ZERO_B),
                      PARTNERS]
HOLD_DRAFT = {"review_status": "HOLD", "signal_status": {"unit_value": "HOLD", "share": "NOT_TRIGGERED"}}
ZERO_REF = {"signal_status": {"unit_value": "HOLD", "share": "NOT_TRIGGERED"},
            "basis": {"unit_value": "data_inconsistent", "share": "not_triggered"}}
ZERO_PROSE = "중량이 0인 하위품목이 있어 자료 불일치로 본다."


def zero_ports(mode, case, envelopes, reference=ZERO_REF, checklist_status=None, real_validator=False):
    """실제 R1·R2(unit_ports의 build_report)에 중량 0 봉투를 준다. 검증기 자리는 통과로 두거나(기본) 실제 R3를 쓴다."""
    config = mc.load_model_config()
    ports = orchestrate.unit_ports(case, mode, h.RUN_ID, config.limits, grouping_version="g0",
                                   rows=lambda ids: {i: None for i in ids})
    by_tool = {e["tool"]: e for e in envelopes}
    by_tool["verify_evidence"] = envelope("verify_evidence", evidence=[PARENT_T])
    ports.tool = lambda name, args: json.loads(trace_log.dumps(by_tool[name]), parse_float=Decimal)
    ports.budget = lambda executed, candidate: {"allowed": True, "reason": None}
    if not real_validator:
        ports.check_report = lambda inp: {"schema_ok": True, "validator_ok": True, "findings": []}
    ports.evidence_reference = lambda evidence: reference
    if checklist_status is not None:
        def checklist_draft(inp):
            statuses = {k: checklist_status if v == "TRIGGERED" else "NOT_TRIGGERED" for k, v in case["signals"].items()}
            return {"review_status": checklist_status, "signal_status": statuses,
                    "claims": orchestrate.checklist_claims(case, inp["evidence"]), "narrative": "", "hypotheses": []}
        ports.checklist_draft = checklist_draft
    return ports


def run_zero_flow(mode, script, case, envelopes=ZERO_ENVELOPES, checklist_status=None):
    config = mc.load_model_config()
    clock = h.FakeClock()
    sink = trace_log.MemoryTrace(h.RUN_ID, clock=trace_log.now_kst)
    ctx = orchestrate.RunContext(run_id=h.RUN_ID, case=case, mode=mode, dataset="controlled_fixture_v0",
                                 rulebook_version="RB-1", grouping_version="g0", code_version="abc1234")
    transport = None if mode == "checklist" else h.ScriptedTransport(script, clock)
    result = orchestrate.orchestrate(ctx, zero_ports(mode, case, envelopes, checklist_status=checklist_status), config,
                                     transport=transport, sink=sink, clock_ms=clock.clock_ms, sleep_ms=clock.sleep_ms)
    return result, sink.records


def evidence_logs(records):
    return [r["data"] for r in h.events(records, "state_change") if r["data"]["phase"] == "evidence_claims"]


class ZeroWeightClaimTest(unittest.TestCase):
    """④ 단가 신호 발동 + 초안 단가 HOLD면 decompose_hs 봉투의 w@<HS10> = 0 지표마다 값 주장을 덧붙인다."""

    def zero(self, draft=HOLD_DRAFT, claims=(), envelopes=ZERO_ENVELOPES, case=UV_CASE):
        return orchestrate.zero_weight_claims(case, draft, list(claims), envelopes)

    def test_hold_with_zero_weight_adds_a_value_claim_shaped_by_r1(self):
        out = self.zero()
        self.assertEqual(len(out["claims"]), 1)
        claim = out["claims"][0]
        self.assertEqual(claim, {"claim_id": "e1", "claim_type": "value", "hs6": HS6, "partner": P, "period": T,
                                 "baseline_period": None, "metric": f"w@{CHILD}", "value": Decimal("0.0"), "unit": "%",
                                 "direction": "NA", "evidence_ids": [CHILD_T, PARENT_T], "text": claim["text"]})
        self.assertEqual(str(claim["value"]), "0.0")  # 표시 자릿수 1(계약 §11.3 w), 단위 %(§11.2)
        self.assertIn("0.0%", claim["text"])
        self.assertEqual(validate.claim_problems(claim), [])
        self.assertEqual(out["added"], [{"signal": "unit_value", "code": "zero_weight_claim", "hs10": CHILD,
                                         "claims": [{"claim_id": "e1", "claim_type": "value", "metric_id": "m-w0-t"}]}])

    def test_positive_weights_alone_add_nothing(self):
        envelopes = [envelope("check_comparability"), HISTORY, decompose_with(W_POS_B), PARTNERS]
        self.assertEqual(self.zero(envelopes=envelopes), {"claims": [], "added": []})
        # 반올림하면 0.0이 되지만 정확히 0이 아닌 값도 후보가 아니다
        near = metric("m-w-near", f"w@{CHILD}", "0.04", "%", [CHILD_T, PARENT_T])
        envelopes = [envelope("check_comparability"), HISTORY, decompose_with(near), PARTNERS]
        self.assertEqual(self.zero(envelopes=envelopes)["claims"], [])

    def test_other_unit_value_statuses_add_nothing(self):
        for status in ("MAINTAIN", "MONITOR", "NOT_TRIGGERED"):
            with self.subTest(status=status):
                draft = dict(HOLD_DRAFT, signal_status={"unit_value": status, "share": "NOT_TRIGGERED"})
                self.assertEqual(self.zero(draft=draft), {"claims": [], "added": []})
        # 초안에 signal_status가 없거나 형식이 틀리면 덧붙이지 않는다
        self.assertEqual(self.zero(draft={"review_status": "HOLD"})["claims"], [])
        self.assertEqual(self.zero(draft={"signal_status": "HOLD"})["claims"], [])

    def test_untriggered_unit_value_signal_adds_nothing_even_if_share_is_hold(self):
        draft = {"review_status": "HOLD", "signal_status": {"unit_value": "NOT_TRIGGERED", "share": "HOLD"}}
        self.assertEqual(self.zero(draft=draft, case=SHARE_CASE), {"claims": [], "added": []})
        # 단가 신호가 발동하지 않았는데 초안이 단가 HOLD를 적어도(허용 밖 초안) 덧붙이지 않는다
        self.assertEqual(self.zero(case=SHARE_CASE)["claims"], [])

    def test_same_metric_already_claimed_is_not_added_again(self):
        existing = filled("m-w0-t", envelopes=ZERO_ENVELOPES)
        self.assertEqual(targets(existing), [("value", f"w@{CHILD}", P, T, None)])
        self.assertEqual(self.zero(claims=existing), {"claims": [], "added": []})
        # 근거를 덜 인용한(유효하지 않은) 같은 대상의 주장이 있어도 다시 넣지 않는다
        unbacked = dict(existing[0], evidence_ids=[CHILD_T])
        self.assertEqual(self.zero(claims=[unbacked])["claims"], [])
        # 다른 월의 같은 하위품목 주장은 다른 대상이라 막지 않는다
        other_month = filled("m-w60-b", envelopes=ZERO_ENVELOPES)
        self.assertEqual([c["claim_id"] for c in self.zero(claims=other_month)["claims"]], ["e2"])

    def test_two_zero_weight_children_are_both_added_grouped_by_hs10(self):
        out = self.zero(envelopes=TWO_ZERO_ENVELOPES)
        self.assertEqual(targets(out["claims"]), [("value", f"w@{CHILD}", P, T, None), ("value", f"w@{CHILD2}", P, T, None),
                                                  ("value", f"w@{CHILD2}", P, B, None)])
        self.assertEqual([c["claim_id"] for c in out["claims"]], ["e1", "e2", "e3"])
        self.assertEqual([str(c["value"]) for c in out["claims"]], ["0.0", "0.0", "0.0"])  # 0·0.00도 표시 자릿수 1로
        self.assertEqual([(a["code"], a["hs10"], [c["metric_id"] for c in a["claims"]]) for a in out["added"]],
                         [("zero_weight_claim", CHILD, ["m-w0-t"]), ("zero_weight_claim", CHILD2, ["m-w2-t", "m-w2-b"])])

    def test_only_decompose_envelopes_without_error_are_sources(self):
        # 같은 지표가 get_history 봉투에 있어도 후보가 아니다
        history = envelope("get_history", metrics=list(HISTORY["metrics"]) + [W_ZERO_T], evidence=HISTORY["evidence_ids"])
        self.assertEqual(self.zero(envelopes=[envelope("check_comparability"), history, PARTNERS])["claims"], [])
        # retryable_error가 있는 decompose_hs 봉투는 받은 봉투가 아니다
        failed = dict(decompose_with(W_ZERO_T), retryable_error={"code": "timeout", "detail": "x"})
        self.assertEqual(self.zero(envelopes=[envelope("check_comparability"), HISTORY, failed])["claims"], [])

    def test_claim_ids_continue_the_e_numbering_and_inputs_are_unchanged(self):
        claims = filled("m-V-t", envelopes=ZERO_ENVELOPES) + [dict(c, claim_id=f"e{i}") for i, c in
                                                             enumerate(filled("m-V-b", envelopes=ZERO_ENVELOPES), start=1)]
        out = self.zero(claims=claims)
        self.assertEqual([c["claim_id"] for c in out["claims"]], ["e3"])
        self.assertEqual(len(claims), 2)

    # 흐름 -------------------------------------------------------------------------------------------------------
    def hold_script(self, mode):
        claims = [TYPED_rU] if mode == "freeform" else [{"claim_type": "change", "metric_id": "m-rU"}]
        script = [h.tools_answer("decompose_hs", "compare_partners"),
                  h.draft_answer(status="HOLD", claims=claims, narrative=ZERO_PROSE)]
        return script + ([h.critic_answer()] if mode in ("full", "freeform") else [])

    def test_flow_adds_the_zero_weight_claim_last_in_every_model_mode(self):
        for mode in ("agent", "full", "freeform"):
            with self.subTest(mode=mode):
                result, records = run_zero_flow(mode, self.hold_script(mode), UV_CASE)
                self.assertEqual((result["record"]["execution_status"], result["report"]["review_status"]),
                                 ("COMPLETED", "HOLD"))
                claims = result["report"]["claims"]
                self.assertEqual(targets(claims[-1:]), [("value", f"w@{CHILD}", P, T, None)])
                self.assertEqual((str(claims[-1]["value"]), claims[-1]["unit"]), ("0.0", "%"))
                self.assertEqual(claims[-1]["claim_id"], f"e{len(claims)}")  # 기존 덧붙임과 같은 번호열
                if mode == "freeform":
                    self.assertEqual(claims[0], TYPED_rU)  # 모델 주장 그대로
                logs = evidence_logs(records)
                self.assertEqual(len(logs), 1)
                self.assertEqual(logs[0]["added"][-1], {"signal": "unit_value", "code": "zero_weight_claim", "hs10": CHILD,
                                                        "claims": [{"claim_id": claims[-1]["claim_id"],
                                                                    "claim_type": "value", "metric_id": "m-w0-t"}]})
                self.assertEqual(logs[0]["signal_status"]["unit_value"], "HOLD")
                # 도구를 새로 부르지 않는다(decompose_hs는 초안 전 한 번)
                self.assertEqual([r["data"]["tool"] for r in h.events(records, "tool_call")].count("decompose_hs"), 1)

    def test_checklist_adds_only_the_zero_weight_its_rule_did_not_pick(self):
        # checklist 규칙은 발동 신호 계열의 비교월 지표를 모두 고르므로(w@ 포함) 비교월의 중량 0은 이미 있다 → 다시 넣지 않고,
        # 규칙이 고르지 않는 기준월의 중량 0(CHILD2@B)만 같은 규칙으로 덧붙인다
        result, records = run_zero_flow("checklist", [], UV_CASE, envelopes=TWO_ZERO_ENVELOPES, checklist_status="HOLD")
        self.assertEqual((result["record"]["execution_status"], result["report"]["review_status"]), ("COMPLETED", "HOLD"))
        claims = result["report"]["claims"]
        found = targets(claims)
        self.assertEqual(found.count(("value", f"w@{CHILD}", P, T, None)), 1)
        self.assertEqual(found.count(("value", f"w@{CHILD2}", P, T, None)), 1)
        self.assertEqual(found[-1:], [("value", f"w@{CHILD2}", P, B, None)])
        self.assertEqual((str(claims[-1]["value"]), claims[-1]["unit"], claims[-1]["claim_id"]),
                         ("0.0", "%", f"e{len(claims)}"))
        logs = evidence_logs(records)
        self.assertEqual(logs[0]["added"][-1], {"signal": "unit_value", "code": "zero_weight_claim", "hs10": CHILD2,
                                                "claims": [{"claim_id": claims[-1]["claim_id"], "claim_type": "value",
                                                            "metric_id": "m-w2-b"}]})
        # checklist 규칙이 MONITOR면 덧붙이지 않는다
        result, records = run_zero_flow("checklist", [], UV_CASE, envelopes=TWO_ZERO_ENVELOPES, checklist_status="MONITOR")
        self.assertNotIn(("value", f"w@{CHILD2}", P, B, None), targets(result["report"]["claims"]))
        self.assertNotIn("zero_weight_claim", [a["code"] for a in evidence_logs(records)[0]["added"]])

    def test_flow_adds_nothing_for_monitor_or_when_the_claim_exists(self):
        script = [h.tools_answer("decompose_hs", "compare_partners"), h.draft_answer(status="MONITOR")]
        result, records = run_zero_flow("agent", script, UV_CASE)
        self.assertNotIn(f"w@{CHILD}", [c["metric"] for c in result["report"]["claims"]])
        self.assertNotIn("zero_weight_claim", [a["code"] for a in evidence_logs(records)[0]["added"]])
        claims = [{"claim_type": "change", "metric_id": "m-rU"}, {"claim_type": "value", "metric_id": "m-w0-t"}]
        script = [h.tools_answer("decompose_hs", "compare_partners"), h.draft_answer(status="HOLD", claims=claims)]
        result, records = run_zero_flow("agent", script, UV_CASE)
        self.assertEqual([c["metric"] for c in result["report"]["claims"]].count(f"w@{CHILD}"), 1)
        self.assertNotIn("zero_weight_claim", [a["code"] for a in evidence_logs(records)[0]["added"]])

    def test_every_report_build_is_augmented(self):
        claims = [{"claim_type": "change", "metric_id": "m-rU"}]
        script = [h.tools_answer("decompose_hs", "compare_partners"), h.draft_answer(status="HOLD", claims=claims),
                  h.critic_answer(needs_revision=True), h.draft_answer(status="HOLD", claims=claims)]
        result, records = run_zero_flow("full", script, UV_CASE)
        self.assertEqual(result["record"]["execution_status"], "COMPLETED")
        logs = evidence_logs(records)
        self.assertEqual([r["stage"] for r in h.events(records, "state_change") if r["data"]["phase"] == "evidence_claims"],
                         ["basic", "final"])
        self.assertEqual([[a["code"] for a in log["added"]][-1] for log in logs], ["zero_weight_claim"] * 2)

    # 실제 검증기 R3 끝까지 -----------------------------------------------------------------------------------------
    def test_real_validator_no_longer_flags_the_prose_zero(self):
        ports = zero_ports("agent", UV_CASE, ZERO_ENVELOPES, real_validator=True)
        draft = dict(HOLD_DRAFT, claims=[{"claim_type": "change", "metric_id": "m-rU"}], narrative=ZERO_PROSE,
                     hypotheses=["하위품목 하나의 중량이 0이라는 가설"])
        codes = orchestrate.evidence_codes(UV_CASE["signals"], draft["signal_status"], ZERO_REF)
        built = ports.build_report({"case": UV_CASE, "mode": "agent", "run_id": h.RUN_ID, "draft": draft,
                                    "evidence": ZERO_ENVELOPES, "required_codes": codes})
        report = built["report"]
        self.assertEqual([a["code"] for a in built["evidence_claims"]["added"]][-1], "zero_weight_claim")
        checked = ports.check_report({"report": report, "evidence": ZERO_ENVELOPES, "revision_used": False})
        prose = [f for f in checked["findings"] if f.get("code") == "PROSE_UNBACKED"]
        self.assertEqual(prose, [])
        # 같은 초안에서 덧붙인 주장(w@)만 빼면 산문의 '0'이 뒷받침되지 않아 PROSE_UNBACKED가 난다
        stripped = dict(report, claims=[c for c in report["claims"] if c["metric"] != f"w@{CHILD}"])
        checked = ports.check_report({"report": stripped, "evidence": ZERO_ENVELOPES, "revision_used": False})
        prose = [(f["code"], f["path"]) for f in checked["findings"] if f.get("code") == "PROSE_UNBACKED"]
        self.assertEqual(prose, [("PROSE_UNBACKED", "narrative"), ("PROSE_UNBACKED", "hypotheses[0]")])


if __name__ == "__main__":
    unittest.main()
