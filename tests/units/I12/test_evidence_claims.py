"""단위 I12 필수 근거 주장 덧붙이기 시험(사용자 결정 2026-09-25(금) 18:09, 결정 기록 *-model-decision-evidence-claims.md).

보고서를 만들 때 코드가 필수 근거 코드(단위 P5)마다 시나리오 명세 §5.3 판정 조건표를 채우는 주장이 있는지 보고, 없으면
받은 봉투의 검증된 지표·자료 상태에서 채울 주장을 덧붙인다. 시험 봉투는 이 파일의 합성 값이다(스냅샷·네트워크 없음).
코드마다: 덧붙이면 조건을 채우는가(덧붙인 뒤 다시 보면 met), 받은 근거에 없으면 덧붙이지 않는가, 모델 주장은 그대로인가,
같은 대상을 두 번 넣지 않는가. 그리고 네 모드 모두 흐름에서 덧붙이고 trace state_change evidence_claims에 남기는가.
"""
import copy
import json
import unittest
from decimal import Decimal

from tradesentry.policy import required_evidence as p5
from tradesentry.reports import claims as report_claims
from tradesentry.runlog import trace as trace_log
from tradesentry.workflow import model_client as mc
from tradesentry.workflow import orchestrate

from . import harness as h

SNAP = h.SNAP
HS6, P, T, B = "850450", "CN", "202401", "202301"
PEER, CHILD = "JP", "8504501000"


def ev(n):
    return f"ev:{SNAP}:observation:{n}"


PARENT_T, PARENT_B, CHILD_T, CHILD_B, ALL_T, ALL_B, PEER_T, PEER_B = (ev(n) for n in (101, 102, 111, 112, 201, 202,
                                                                                         301, 302))


def metric(metric_id, symbol, value, unit, evidence, *, partner=P, period=T, baseline=None):
    return {"metric_id": metric_id, "formula_version": "f1",
            "inputs": {"metric": symbol, "hs6": HS6, "partner": partner, "period": period, "baseline_period": baseline},
            "evidence_ids": list(evidence), "value": value if value is None else Decimal(value), "unit": unit,
            "comparability_flags": [], "tolerance": None}


def envelope(tool, metrics=(), evidence=(), missingness=(), comparability=None):
    return {"query_id": f"q-{tool}", "tool": tool, "scope": {"hs6": HS6, "partner": P}, "snapshot_id": SNAP,
            "source_kind": "controlled", "evidence_ids": list(evidence), "metrics": list(metrics),
            "comparability": comparability if comparability is not None else
            ({"comparable": True} if tool == "check_comparability" else {}),
            "missingness": list(missingness), "retryable_error": None, "elapsed_ms": 5}


HISTORY = envelope("get_history", metrics=[
    metric("m-U-t", "U", "6.00", "USD/kg", [PARENT_T]),
    metric("m-U-b", "U", "10.00", "USD/kg", [PARENT_B], period=B),
    metric("m-rU", "r_U", "-40.0", "%", [PARENT_B, PARENT_T], baseline=B),
    metric("m-V-t", "V", "600", "USD", [PARENT_T]),
    metric("m-V-b", "V", "1000", "USD", [PARENT_B], period=B),
    metric("m-Q-t", "Q", "100", "kg", [PARENT_T]),
    metric("m-Q-b", "Q", "100", "kg", [PARENT_B], period=B),
    metric("m-VA-t", "V", "3000", "USD", [ALL_T], partner="ALL"),
    metric("m-VA-b", "V", "4000", "USD", [ALL_B], partner="ALL", period=B),
    metric("m-s-t", "s", "20.0", "%", [PARENT_T, ALL_T]),
    metric("m-s-b", "s", "25.0", "%", [PARENT_B, ALL_B], period=B),
    metric("m-ds", "d_s", "-5.0", "pp", [PARENT_B, PARENT_T, ALL_B, ALL_T], baseline=B),
], evidence=[PARENT_T, PARENT_B, ALL_T, ALL_B])
DECOMPOSE = envelope("decompose_hs", metrics=[
    metric("m-within", "within_effect", "-3.00", "USD/kg", [PARENT_B, PARENT_T, CHILD_B, CHILD_T], baseline=B),
    metric("m-mix", "mix_effect", "-1.00", "USD/kg", [PARENT_B, PARENT_T, CHILD_B, CHILD_T], baseline=B),
    metric("m-residual", "residual", "0.00", "USD/kg", [PARENT_B, PARENT_T, CHILD_B, CHILD_T], baseline=B),
    metric("m-Uc-t", f"U@{CHILD}", "6.00", "USD/kg", [CHILD_T]),
    metric("m-Uc-b", f"U@{CHILD}", "10.00", "USD/kg", [CHILD_B], period=B),
    metric("m-rUc", f"r_U@{CHILD}", "-40.0", "%", [CHILD_B, CHILD_T], baseline=B),
], evidence=[PARENT_B, PARENT_T, CHILD_B, CHILD_T],
    comparability={"hs10": [{"month": B, "observation_status": "OBSERVED", "codes": [CHILD]},
                            {"month": T, "observation_status": "OBSERVED", "codes": [CHILD]}],
                   "same_hs10_set": True, "parent_check": []})
PARTNERS = envelope("compare_partners", metrics=[
    metric("m-rU-JP", "r_U", "1.5", "%", [PEER_B, PEER_T], partner=PEER, baseline=B),
    metric("m-ds-JP", "d_s", "0.4", "pp", [PEER_B, PEER_T, ALL_B, ALL_T], partner=PEER, baseline=B),
], evidence=[PEER_B, PEER_T, ALL_B, ALL_T])
ENVELOPES = [envelope("check_comparability"), HISTORY, DECOMPOSE, PARTNERS]
BOTH = {"case_id": f"{HS6}-{P}-{T}", "hs6": HS6, "partner": P, "month": T, "baseline_month": B,
        "signals": {"unit_value": "TRIGGERED", "share": "TRIGGERED"}, "snapshot_id": SNAP, "policy_version": "dev-0.1"}


def targets(claims):
    return [(c["claim_type"], c["metric"], c["partner"], c["period"], c["baseline_period"]) for c in claims]


def filled(*metric_ids, envelopes=ENVELOPES):
    """R1 틀 채우기로 만든 보고서 주장(모델·checklist가 metric_id로 고른 주장과 같은 모양)."""
    metrics = orchestrate._metrics_of(envelopes)
    return report_claims.fill(BOTH, metrics, [], [{"claim_id": f"c{i}", "metric_id": m}
                                                  for i, m in enumerate(metric_ids, start=1)])["claims"]


def augment(codes, claims=(), envelopes=ENVELOPES, case=BOTH):
    return orchestrate.evidence_claims(case, codes, list(claims), envelopes)


class EvidenceCodesTest(unittest.TestCase):
    """필수 근거 코드 고르기: 판정이 규칙 참고값과 같으면 참고값 판정 근거의 목록, 다르면 그 상태 규칙 목록의 합."""

    REF = {"signal_status": {"unit_value": "MONITOR", "share": "MAINTAIN"},
           "basis": {"unit_value": "composition_explained", "share": "unexplained"}}

    def test_same_as_reference_uses_the_reference_basis(self):
        codes = orchestrate.evidence_codes(BOTH["signals"], {"unit_value": "MONITOR", "share": "MAINTAIN"}, self.REF)
        self.assertEqual(codes, {"unit_value": list(p5.rule_evidence("unit_value", "composition_explained")),
                                 "share": list(p5.rule_evidence("share", "unexplained"))})

    def test_different_from_reference_unions_every_rule_of_that_status(self):
        codes = orchestrate.evidence_codes(BOTH["signals"], {"unit_value": "HOLD", "share": "MAINTAIN"}, self.REF)
        self.assertEqual(codes["unit_value"], ["missingness_listed", "failure_vs_not_collected_distinguished",
                                               "no_zero_fill", "parent_child_match_V_and_Q", "comparability_ok",
                                               "precision_sensitivity_shown"])
        self.assertEqual(codes["share"], list(p5.rule_evidence("share", "unexplained")))

    def test_union_for_share_hold_and_untriggered_signal_is_absent(self):
        signals = {"unit_value": "NOT_TRIGGERED", "share": "TRIGGERED"}
        codes = orchestrate.evidence_codes(signals, {"unit_value": "NOT_TRIGGERED", "share": "HOLD"}, None)
        self.assertEqual(codes, {"share": ["missingness_listed", "failure_vs_not_collected_distinguished",
                                           "no_zero_fill", "country_and_world_change_shown", "comparability_ok"]})
        ref = {"signal_status": {"unit_value": "NOT_TRIGGERED", "share": "HOLD"},
               "basis": {"unit_value": "not_triggered", "share": "data_inconsistent"}}
        self.assertEqual(orchestrate.evidence_codes(signals, {"share": "HOLD"}, ref),
                         {"share": list(p5.rule_evidence("share", "data_inconsistent"))})

    def test_without_reference_unions_and_untriggered_or_unknown_statuses_get_nothing(self):
        signals = {"unit_value": "TRIGGERED", "share": "NOT_TRIGGERED"}
        self.assertEqual(orchestrate.evidence_codes(signals, {"unit_value": "MAINTAIN"}, None),
                         {"unit_value": list(p5.rule_evidence("unit_value", "unexplained"))})
        self.assertEqual(orchestrate.evidence_codes(signals, {"unit_value": "LOW"}, None), {"unit_value": []})
        self.assertEqual(orchestrate.evidence_codes(signals, None, None), {"unit_value": []})


class PerCodeTest(unittest.TestCase):
    """코드마다 덧붙이면 §5.3 조건을 채우고(덧붙인 뒤 다시 보면 met), 받은 근거에 없으면 덧붙이지 않는다."""

    CASES = [  # (계열, 코드, 덧붙일 주장의 대상)
        ("unit_value", "comparability_ok", [("change", "r_U", P, T, B)]),
        ("share", "comparability_ok", [("share_change", "d_s", P, T, B)]),
        ("unit_value", "partner_comparison_done", [("comparison", "r_U", PEER, T, B)]),
        ("share", "partner_comparison_done", [("comparison", "d_s", PEER, T, B)]),
        ("unit_value", "weight_share_decomposition", [("decomposition", m, P, T, B)
                                                      for m in ("within_effect", "mix_effect", "residual")]),
        ("unit_value", "per_child_unit_value_stable", [("change", f"r_U@{CHILD}", P, T, B)]),
        ("unit_value", "parent_child_match_V_and_Q", [("decomposition", "within_effect", P, T, B)]),
        ("unit_value", "precision_sensitivity_shown", [("value", "V", P, T, None), ("value", "V", P, B, None),
                                                       ("value", "Q", P, T, None), ("value", "Q", P, B, None)]),
        ("share", "country_and_world_change_shown", [("value", "V", P, T, None), ("value", "V", P, B, None),
                                                     ("value", "V", "ALL", T, None), ("value", "V", "ALL", B, None)]),
    ]

    def test_each_code_is_filled_from_received_evidence_and_is_then_met(self):
        for family, code, expected in self.CASES:
            with self.subTest(family=family, code=code):
                out = augment({family: [code]})
                self.assertEqual(sorted(targets(out["claims"])), sorted(expected))
                self.assertEqual([(a["signal"], a["code"]) for a in out["log"]["added"]], [(family, code)])
                self.assertEqual(out["log"]["unmet"], [])
                again = augment({family: [code]}, claims=out["claims"])
                self.assertEqual((again["claims"], again["log"]["added"], again["log"]["unmet"]), ([], [], []))

    def test_added_claims_are_r1_claims_of_verified_metrics(self):
        out = augment({"share": ["country_and_world_change_shown"]})
        for claim in out["claims"]:
            self.assertRegex(claim["claim_id"], r"^e\d+$")
            self.assertEqual(sorted(claim), sorted(report_claims.CLAIM_FIELDS))
        self.assertEqual([c["value"] for c in out["claims"]], [600, 1000, 3000, 4000])
        requests = out["log"]["added"][0]["claims"]
        self.assertEqual([(r["claim_type"], r["metric_id"]) for r in requests],
                         [("value", "m-V-t"), ("value", "m-V-b"), ("value", "m-VA-t"), ("value", "m-VA-b")])

    def test_nothing_is_added_when_the_evidence_was_not_received(self):
        lookups_only = [envelope("check_comparability"), HISTORY]  # decompose_hs·compare_partners 결과가 없다
        codes = {"unit_value": ["parent_child_match_V_and_Q", "weight_share_decomposition",
                                "per_child_unit_value_stable", "partner_comparison_done"]}
        out = augment(codes, envelopes=lookups_only)
        self.assertEqual((out["claims"], out["log"]["added"]), ([], []))
        self.assertEqual([u["code"] for u in out["log"]["unmet"]], codes["unit_value"])
        # 값이 없는(계산 불가) 지표로는 채우지 않는다
        null_history = envelope("get_history", metrics=[metric("m-V-t", "V", None, "USD", [PARENT_T]),
                                                        metric("m-V-b", "V", "1000", "USD", [PARENT_B], period=B),
                                                        metric("m-VA-t", "V", "3000", "USD", [ALL_T], partner="ALL"),
                                                        metric("m-VA-b", "V", "4000", "USD", [ALL_B], partner="ALL",
                                                               period=B)])
        out = augment({"share": ["country_and_world_change_shown"]}, envelopes=[null_history])
        self.assertEqual((out["claims"], out["log"]["unmet"]), ([], [{"signal": "share",
                                                                       "code": "country_and_world_change_shown"}]))

    def test_no_action_codes_add_nothing(self):
        out = augment({"unit_value": ["no_zero_fill", "correction_snapshots_before_after"]})
        self.assertEqual(out["claims"], [])
        self.assertEqual([n["code"] for n in out["log"]["no_action"]], ["no_zero_fill",
                                                                        "correction_snapshots_before_after"])


class ModelClaimsTest(unittest.TestCase):
    """모델 주장은 바꾸지 않고, 같은 대상은 다시 넣지 않는다."""

    def test_existing_claims_count_and_are_not_changed(self):
        mine = filled("m-rU", "m-within")
        before = copy.deepcopy(mine)
        out = augment({"unit_value": ["comparability_ok", "parent_child_match_V_and_Q", "weight_share_decomposition"]},
                      claims=mine)
        self.assertEqual(mine, before)
        self.assertEqual(sorted(targets(out["claims"])), [("decomposition", "mix_effect", P, T, B),
                                                          ("decomposition", "residual", P, T, B)])
        self.assertEqual([a["code"] for a in out["log"]["added"]], ["weight_share_decomposition"])
        self.assertTrue(all(c["claim_id"] not in ("c1", "c2") for c in out["claims"]))

    def test_one_target_is_added_once_across_codes_and_signals(self):
        out = augment({"unit_value": ["precision_sensitivity_shown"], "share": ["country_and_world_change_shown"]})
        self.assertEqual(len(targets(out["claims"])), len(set(targets(out["claims"]))))
        self.assertEqual(targets(out["claims"]).count(("value", "V", P, T, None)), 1)
        self.assertEqual(len(out["claims"]), 6)  # V·Q 두 시점 넷 + ALL V 두 시점 둘
        self.assertEqual(len({c["claim_id"] for c in out["claims"]}), 6)

    def test_claim_ids_skip_ids_already_in_the_report(self):
        mine = [dict(c, claim_id="e1") for c in filled("m-U-t")]
        out = augment({"unit_value": ["comparability_ok"]}, claims=mine)
        self.assertEqual([c["claim_id"] for c in out["claims"]], ["e2"])

    def test_freeform_model_claim_blocks_only_its_own_target(self):
        wrong = dict(filled("m-rU")[0], claim_id="mine-1", evidence_ids=[PARENT_T])
        out = augment({"unit_value": ["comparability_ok"]}, claims=[wrong])
        # r_U 대상은 모델 주장이 차지해 다시 넣지 않고, 두 시점 U 수준 주장으로 채운다
        self.assertEqual(sorted(targets(out["claims"])), [("value", "U", P, B, None), ("value", "U", P, T, None)])
        self.assertEqual(out["log"]["unmet"], [])


class DataStatusTest(unittest.TestCase):
    """빠진 키의 자료 상태(missingness_listed·failure_vs_not_collected_distinguished)와 검증기 R3의 어긋남 규칙."""

    GAP = {"evidence_id": ev(900), "request_id": "req-1", "partner_code": P, "hs_code": HS6, "month": B,
           "flow": "import", "observation_status": "REQUEST_FAILED"}
    PEER_GAP = dict(GAP, evidence_id=ev(901), partner_code=PEER, observation_status="NOT_COLLECTED")

    def test_missing_key_gets_its_data_status(self):
        gap_history = envelope("get_history", metrics=[metric("m-U-t", "U", "6.00", "USD/kg", [PARENT_T])],
                               missingness=[self.GAP])
        out = augment({"unit_value": ["missingness_listed", "failure_vs_not_collected_distinguished"]},
                      envelopes=[gap_history])
        self.assertEqual([(c["claim_type"], c["metric"], c["partner"], c["period"], c["value"]) for c in out["claims"]],
                         [("data_status", "observation_status", P, B, "REQUEST_FAILED")])
        self.assertEqual([a["code"] for a in out["log"]["added"]], ["missingness_listed"])
        self.assertEqual(out["log"]["added"][0]["claims"],
                         [{"claim_type": "data_status", "evidence_id": ev(900), "claim_id": "e1"}])
        self.assertEqual(out["log"]["unmet"], [])

    def test_without_gaps_a_peer_status_lists_missingness(self):
        peer = envelope("compare_partners", metrics=[metric("m-rU-JP", "r_U", "1.5", "%", [PEER_B, PEER_T],
                                                            partner=PEER, baseline=B)], missingness=[self.PEER_GAP])
        out = augment({"unit_value": ["missingness_listed", "failure_vs_not_collected_distinguished"]},
                      envelopes=[peer])
        self.assertEqual([(c["partner"], c["value"]) for c in out["claims"]], [(PEER, "NOT_COLLECTED")])
        self.assertEqual(out["log"]["unmet"], [])

    def test_status_that_would_conflict_with_a_value_claim_is_not_added(self):
        # 모델(freeform)이 빠진 키에 값 주장을 적었다: 자료 상태를 더하면 R3 DATA_STATUS_CONFLICT라 넣지 않는다
        gap_history = envelope("get_history", metrics=[metric("m-U-t", "U", "6.00", "USD/kg", [PARENT_T])],
                               missingness=[self.GAP])
        mine = [dict(filled("m-V-b")[0], claim_id="mine-1")]
        out = augment({"unit_value": ["missingness_listed"]}, claims=mine, envelopes=[gap_history])
        self.assertEqual(out["claims"], [])
        self.assertEqual(out["log"]["unmet"], [{"signal": "unit_value", "code": "missingness_listed"}])

    def test_every_missing_key_of_both_months_is_required(self):
        gap_t = dict(self.GAP, evidence_id=ev(902), month=T, observation_status="NOT_COLLECTED")
        both = envelope("get_history", missingness=[self.GAP, gap_t])
        out = augment({"unit_value": ["failure_vs_not_collected_distinguished"]}, envelopes=[both])
        self.assertEqual(sorted((c["period"], c["value"]) for c in out["claims"]),
                         [(B, "REQUEST_FAILED"), (T, "NOT_COLLECTED")])
        # 한 시점만 적은 보고서는 채우지 못한 것이고, 빠진 다른 시점을 덧붙인다
        first = augment({"unit_value": ["failure_vs_not_collected_distinguished"]}, envelopes=[both])["claims"][:1]
        again = augment({"unit_value": ["failure_vs_not_collected_distinguished"]}, claims=first, envelopes=[both])
        self.assertEqual(len(again["claims"]), 1)
        self.assertNotEqual(again["claims"][0]["period"], first[0]["period"])

    def test_wrong_status_claim_leaves_failure_vs_not_collected_unmet(self):
        gap_history = envelope("get_history", missingness=[self.GAP])
        wrong = dict(augment({"unit_value": ["missingness_listed"]}, envelopes=[gap_history])["claims"][0],
                     claim_id="mine-1", value="NOT_COLLECTED")  # 받은 상태는 REQUEST_FAILED
        out = augment({"unit_value": ["failure_vs_not_collected_distinguished"]}, claims=[wrong],
                      envelopes=[gap_history])
        self.assertEqual((out["claims"], out["log"]["unmet"]),
                         ([], [{"signal": "unit_value", "code": "failure_vs_not_collected_distinguished"}]))

    def test_request_status_row_of_an_observed_key_is_not_a_missing_key(self):
        # 대상국 HS6 값이 관측된 월의 요청 상태 행은 빠진 키가 아니다(비교국 상태도 없으면 채울 수 없다)
        observed = envelope("get_history", metrics=[metric("m-V-b", "V", "1000", "USD", [PARENT_B], period=B)],
                            missingness=[self.GAP])
        out = augment({"unit_value": ["missingness_listed"]}, envelopes=[observed])
        self.assertEqual(out["claims"], [])

    def test_peer_status_must_be_a_peer_hs6_status_from_compare_partners(self):
        other = dict(self.PEER_GAP, evidence_id=ev(903), partner_code="KR")  # 비교국 밖
        hs10 = dict(self.PEER_GAP, evidence_id=ev(904), hs_code=CHILD)  # 비교국이지만 HS10 수준
        peer = envelope("compare_partners", metrics=[metric("m-rU-JP", "r_U", "1.5", "%", [PEER_B, PEER_T],
                                                            partner=PEER, baseline=B)], missingness=[other, hs10])
        elsewhere = envelope("get_history", missingness=[dict(self.PEER_GAP, evidence_id=ev(905))])  # 다른 도구
        out = augment({"unit_value": ["missingness_listed"]}, envelopes=[peer, elsewhere])
        self.assertEqual(out["claims"], [])
        self.assertEqual(out["log"]["unmet"], [{"signal": "unit_value", "code": "missingness_listed"}])


class PeerAndParentTest(unittest.TestCase):
    """비교국 여럿 가운데 첫 유효 후보, 부모·하위 대조의 행 범위."""

    def test_first_peer_with_a_usable_metric_is_used(self):
        peers = envelope("compare_partners", metrics=[
            metric("m-rU-KR", "r_U", None, "%", [ev(401), ev(402)], partner="KR", baseline=B),  # 값 없음
            metric("m-rU-JP", "r_U", "1.5", "%", [PEER_B, PEER_T], partner=PEER, baseline=B)])
        peers["scope"]["partners"] = ["AU", "KR", PEER, "ALL"]  # AU는 지표가 없다
        out = augment({"unit_value": ["partner_comparison_done"]}, envelopes=[peers])
        self.assertEqual(targets(out["claims"]), [("comparison", "r_U", PEER, T, B)])

    def test_parent_child_needs_only_parent_and_child_rows(self):
        extra = dict(DECOMPOSE, evidence_ids=list(DECOMPOSE["evidence_ids"]) + [ev(999)])  # 대조에 쓰지 않는 행
        envelopes = [HISTORY, extra]
        mine = filled("m-V-t", "m-V-b", "m-Uc-t", "m-Uc-b", envelopes=envelopes)
        out = augment({"unit_value": ["parent_child_match_V_and_Q"]}, claims=mine, envelopes=envelopes)
        self.assertEqual((out["claims"], out["log"]["unmet"], out["log"]["added"]), ([], [], []))
        # 하위 행 하나(기준월)를 인용하지 않으면 그것만 채운다
        partial = filled("m-V-t", "m-V-b", "m-Uc-t", envelopes=envelopes)
        out = augment({"unit_value": ["parent_child_match_V_and_Q"]}, claims=partial, envelopes=envelopes)
        self.assertEqual(len(out["claims"]), 1)
        self.assertIn(CHILD_B, out["claims"][0]["evidence_ids"])

    def test_parent_child_is_unmet_without_children_in_both_months(self):
        one_month = dict(DECOMPOSE, comparability={"hs10": [{"month": T, "observation_status": "OBSERVED",
                                                             "codes": [CHILD]},
                                                            {"month": B, "observation_status": "REQUEST_FAILED",
                                                             "codes": []}]})
        out = augment({"unit_value": ["parent_child_match_V_and_Q"]}, envelopes=[HISTORY, one_month])
        self.assertEqual((out["claims"], [u["code"] for u in out["log"]["unmet"]]),
                         ([], ["parent_child_match_V_and_Q"]))

def ports_for(mode, case, reference, checklist_status=None):
    """실제 R1·R2(unit_ports의 build_report)에 이 파일의 봉투를 주고, 검증기 자리는 통과로 둔다."""
    config = mc.load_model_config()
    ports = orchestrate.unit_ports(case, mode, h.RUN_ID, config.limits, grouping_version="g0")
    by_tool = {e["tool"]: e for e in ENVELOPES}
    by_tool["verify_evidence"] = envelope("verify_evidence", evidence=[PARENT_T])
    ports.tool = lambda name, args: json.loads(trace_log.dumps(by_tool[name]), parse_float=Decimal)
    ports.budget = lambda executed, candidate: {"allowed": True, "reason": None}
    ports.check_report = lambda inp: {"schema_ok": True, "validator_ok": True, "findings": []}
    ports.evidence_reference = lambda evidence: reference
    if checklist_status is not None:
        def checklist_draft(inp):
            statuses = {k: checklist_status if v == "TRIGGERED" else "NOT_TRIGGERED" for k, v in case["signals"].items()}
            return {"review_status": checklist_status, "signal_status": statuses,
                    "claims": orchestrate.checklist_claims(case, inp["evidence"]), "narrative": "", "hypotheses": []}
        ports.checklist_draft = checklist_draft
    return ports


def run_flow(mode, script, case, reference, checklist_status=None):
    config = mc.load_model_config()
    clock = h.FakeClock()
    sink = trace_log.MemoryTrace(h.RUN_ID, clock=trace_log.now_kst)
    ctx = orchestrate.RunContext(run_id=h.RUN_ID, case=case, mode=mode, dataset="controlled_fixture_v0",
                                 rulebook_version="RB-1", grouping_version="g0", code_version="abc1234")
    transport = None if mode == "checklist" else h.ScriptedTransport(script, clock)
    result = orchestrate.orchestrate(ctx, ports_for(mode, case, reference, checklist_status), config,
                                     transport=transport, sink=sink, clock_ms=clock.clock_ms, sleep_ms=clock.sleep_ms)
    return result, sink.records


UV_CASE = dict(BOTH, signals={"unit_value": "TRIGGERED", "share": "NOT_TRIGGERED"})
SHARE_CASE = dict(BOTH, signals={"unit_value": "NOT_TRIGGERED", "share": "TRIGGERED"})
UV_REF = {"signal_status": {"unit_value": "MONITOR", "share": "NOT_TRIGGERED"},
          "basis": {"unit_value": "composition_explained", "share": "not_triggered"}}
SHARE_REF = {"signal_status": {"unit_value": "NOT_TRIGGERED", "share": "MAINTAIN"},
             "basis": {"unit_value": "not_triggered", "share": "unexplained"}}
TYPED_rU = {"claim_id": "c1", "claim_type": "change", "hs6": HS6, "partner": P, "period": T, "baseline_period": B,
            "metric": "r_U", "value": "-40.0", "unit": "%", "direction": "DOWN", "evidence_ids": [PARENT_B, PARENT_T],
            "text": "단가가 전년 같은 달보다 40.0% 낮다."}


class FlowModesTest(unittest.TestCase):
    """네 모드 모두 보고서를 만들 때 덧붙이고(모델 주장은 앞에 그대로), trace state_change evidence_claims에 남긴다."""

    EXPECTED_UV = [("decomposition", "within_effect", P, T, B), ("decomposition", "mix_effect", P, T, B),
                   ("decomposition", "residual", P, T, B), ("change", f"r_U@{CHILD}", P, T, B)]

    def model_script(self, mode):
        tools = h.tools_answer("decompose_hs", "compare_partners")
        claims = [TYPED_rU] if mode == "freeform" else [{"claim_type": "change", "metric_id": "m-rU"}]
        script = [tools, h.draft_answer(claims=claims)]
        return script + ([h.critic_answer()] if mode in ("full", "freeform") else [])

    def test_model_modes_append_after_the_model_claims(self):
        for mode in ("agent", "full", "freeform"):
            with self.subTest(mode=mode):
                result, records = run_flow(mode, self.model_script(mode), UV_CASE, UV_REF)
                self.assertEqual(result["record"]["execution_status"], "COMPLETED")
                claims = result["report"]["claims"]
                self.assertEqual(targets(claims[:1]), [("change", "r_U", P, T, B)])
                if mode == "freeform":
                    self.assertEqual(claims[0], TYPED_rU)  # 모델이 쓴 주장 그대로(값 표기도)
                self.assertEqual(targets(claims[1:]), self.EXPECTED_UV)
                logs = [r["data"] for r in h.events(records, "state_change") if r["data"]["phase"] == "evidence_claims"]
                self.assertEqual(len(logs), 1)
                self.assertEqual(logs[0]["required"],
                                 {"unit_value": list(p5.rule_evidence("unit_value", "composition_explained"))})
                self.assertEqual([a["code"] for a in logs[0]["added"]],
                                 ["parent_child_match_V_and_Q", "weight_share_decomposition",
                                  "per_child_unit_value_stable"])
                self.assertEqual((logs[0]["unmet"], logs[0]["no_action"]), ([], []))
                self.assertEqual(logs[0]["signal_status"], {"unit_value": "MONITOR", "share": "NOT_TRIGGERED"})
                # verify_evidence에는 모델이 가리킨 근거만 간다(덧붙인 주장은 이미 검증된 봉투의 지표다)
                verify = [r["data"]["args"] for r in h.events(records, "tool_call")
                          if r["data"]["tool"] == "verify_evidence"]
                self.assertEqual(len(verify), 1)
                self.assertNotIn("m-within", json.dumps(verify))

    def test_checklist_adds_country_and_world_change(self):
        result, records = run_flow("checklist", [], SHARE_CASE, SHARE_REF, checklist_status="MAINTAIN")
        self.assertEqual(result["record"]["execution_status"], "COMPLETED")
        claims = result["report"]["claims"]
        self.assertIn(("value", "V", "ALL", B, None), targets(claims))
        logs = [r["data"] for r in h.events(records, "state_change") if r["data"]["phase"] == "evidence_claims"]
        self.assertEqual([(a["signal"], a["code"]) for a in logs[0]["added"]],
                         [("share", "country_and_world_change_shown")])
        added = logs[0]["added"][0]["claims"]
        self.assertEqual([(c["claim_type"], c["metric_id"]) for c in added],
                         [("value", "m-V-t"), ("value", "m-V-b"), ("value", "m-VA-t"), ("value", "m-VA-b")])
        self.assertEqual(targets(claims[-4:]), [("value", "V", P, T, None), ("value", "V", P, B, None),
                                                ("value", "V", "ALL", T, None), ("value", "V", "ALL", B, None)])
        # checklist 규칙의 주장(비교월 지표)은 앞에 그대로다
        self.assertEqual(targets(claims[:-4]), [("share", "s", P, T, None), ("share_change", "d_s", P, T, B),
                                                ("comparison", "d_s", PEER, T, B)])

    def test_every_report_build_is_augmented_and_logged(self):
        # full에서 Critic이 수정을 요청하면 초안 보고서와 수정본 보고서 두 번 만든다: 두 번 모두 덧붙인다
        claims = [{"claim_type": "change", "metric_id": "m-rU"}]
        script = [h.tools_answer("decompose_hs", "compare_partners"), h.draft_answer(claims=claims),
                  h.critic_answer(needs_revision=True), h.draft_answer(claims=claims)]
        result, records = run_flow("full", script, UV_CASE, UV_REF)
        self.assertEqual(result["record"]["execution_status"], "COMPLETED")
        stages = [r["stage"] for r in h.events(records, "state_change") if r["data"]["phase"] == "evidence_claims"]
        self.assertEqual(stages, ["basic", "final"])
        self.assertEqual(targets(result["report"]["claims"][1:]), self.EXPECTED_UV)


if __name__ == "__main__":
    unittest.main()
