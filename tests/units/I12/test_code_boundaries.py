"""단위 I12 코드 경계 셋 시험(사용자 결정 2026-09-25(금) 22:22 ①②③, 결정 기록 *-model-decision-code-boundaries.md).

① review_status 코드 집계: 보고서를 만들 때마다 signal_status에서 자료 계약 §3.1 규칙(검증기 R3 aggregate_status와 같은
   계산)으로 review_status·unresolved_evidence를 채운다. 네 조합, checklist 불변, 네 모드, trace status_aggregated 모양,
   형식 불량 초안은 손대지 않음.
② 발동 신호 자기 계열 주장: 계열 주장(R3 signal_families 판정)이 없으면 그 신호의 변화 지표(r_U·d_s)를 받은 봉투에서 덧붙인다.
   없음→덧붙임, 있음→불변, 근거에 없음→덧붙이지 않음, 두 신호 발동, e{번호} 번호열 연속, freeform.
③ HOLD 합의 신호엔 빠진 도구 지적 없음: 초안 판정과 규칙 참고값이 둘 다 HOLD인 신호의 도구는 code_missing에서 뺀다.
   HOLD 합의→지적 없음, 단가만 합의→decompose_hs만 빼기, 참고값 None·불일치→기존, (나)로 완료되는 대본.
모델 답과 도구·검사 자리는 대역이다(harness.py, 네트워크·스냅샷 없음).
"""
import unittest

from tradesentry.cli import dispatch
from tradesentry.runlog import cause_codes
from tradesentry.runlog import trace as trace_log
from tradesentry.validator import validate
from tradesentry.workflow import model_client as mc
from tradesentry.workflow import orchestrate

from ..I7.fakes import FakeClock, ScriptedTransport
from . import harness as h
from .test_evidence_claims import (B, BOTH, ENVELOPES, HISTORY, P, PARENT_B, PARENT_T, SHARE_CASE, T, TYPED_rU,
                                   UV_CASE, envelope, filled, run_flow, targets)

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


if __name__ == "__main__":
    unittest.main()
