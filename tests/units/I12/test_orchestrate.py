"""단위 I12(workflow_orchestrate) 흐름 쪽 예산 강제 시험(로드맵 §3 체크리스트 2번, MT4 완료 기준)과 모드 규칙 시험.

체크리스트 2번의 흐름 쪽: 두 번째 수정 단계 차단, 수정 단계의 세 번째 재조회 차단, 전체 deadline 우선 종료.
도구 8회 몫(기본 5 + 재조회 2 + 최종 검증 1)은 흐름 조정이 단계별로 강제하므로 9번째 도구 실행이 생기지 않는다.
모델 답과 다른 단위 자리는 대역이다(harness.py). 흐름 조정의 한도 판단은 대역이 아니라 실제 코드가 한다.
검토 1회차 뒤: 허용 상태 조합은 검증기 부류(freeform 기록만), 비교 불가 사례는 수정 단계에서도 도구 없음, 잘린 초안,
critic_used 기준, 기록 없이 끝나던 두 경로, 배선(unit_ports)의 P4 감싸기·I6 한도·자료 상태·P3 근거 상태.
"""
import json
import unittest
from unittest import mock

from tradesentry.runlog import cause_codes
from tradesentry.workflow import investigator
from tradesentry.workflow import model_client as mc
from tradesentry.workflow import orchestrate

from ..I7.fakes import ok_body
from . import harness as h

FREEFORM_CLAIM = {"claim_id": "c1", "claim_type": "change", "hs6": "850450", "partner": "CN", "period": "202401",
                  "baseline_period": "202301", "metric": "r_U", "value": "-40.0", "unit": "%", "direction": "DOWN",
                  "evidence_ids": [h.EV[0]], "text": "단가가 낮다."}
STATUS_FINDING = {"check": "validator", "code": "STATUS_INCONSISTENT", "path": "review_status", "claim_id": None,
                  "detail": "신호별 판정의 집계는 HOLD다"}
STATUS_BLOCK = {"schema_ok": True, "validator_ok": False, "findings": [STATUS_FINDING]}


def mismatched(**over):
    """집계가 어긋난 초안: 단가 신호 판정은 HOLD인데 사례 판정은 MONITOR(허용 상태 밖, 형식은 맞음)."""
    body = h.draft(status="MONITOR", **over)
    body["signal_status"] = {"unit_value": "HOLD", "share": "NOT_TRIGGERED"}
    return {"body": ok_body(json.dumps(body, ensure_ascii=False), prompt_tokens=1500, completion_tokens=150)}


def not_comparable(test):
    original = h.ENVELOPES["check_comparability"]
    h.ENVELOPES["check_comparability"] = h.envelope("check_comparability", "q-cc", comparable=False)
    test.addCleanup(h.ENVELOPES.__setitem__, "check_comparability", original)


def blocks(records):
    return [(r["stage"], r["data"]["kind"]) for r in h.events(records, "budget_block")]


class FlowBudgetTest(unittest.TestCase):
    """체크리스트 2번(흐름 쪽)."""

    def test_second_revision_stage_is_blocked(self):
        # Critic이 수정을 요청 → 수정 1회 → 최종 검증에서도 검증기가 막음 → 두 번째 수정 없이 INVALID
        fake = h.FakePorts(checks=[h.PASS, h.PASS, h.BLOCK])
        script = [h.draft_answer(), h.critic_answer(needs_revision=True), h.draft_answer(status="MAINTAIN")]
        result, records, fake, transport = h.run_case("full", script, fake)
        record = result["record"]
        self.assertEqual((record["execution_status"], record["errors"][0]["code"]),
                         ("INVALID", cause_codes.VALIDATOR_BLOCKED))
        self.assertIs(record["revision_used"], True)
        self.assertIsNone(result["report"])
        self.assertEqual(blocks(records), [("final", "revision_limit")])
        self.assertEqual(len([r for r in h.events(records, "stage_start") if r["stage"] == "revision"]), 1)
        self.assertEqual(record["model_requests"], 3)  # 초안, Critic, 수정 초안(두 번째 수정 요청 없음)
        self.assertEqual(transport.script, [])

    def test_third_requery_in_revision_is_blocked(self):
        # agent: 검증기가 막음 → 수정 단계에서 모델이 도구 셋을 한꺼번에 부름 → 세 번째는 막힌다
        fake = h.FakePorts(checks=[h.PASS, h.BLOCK, h.PASS])
        script = [h.draft_answer(status="MAINTAIN"),
                  h.tools_answer("decompose_hs", "compare_partners", "check_comparability"),
                  h.draft_answer(status="MAINTAIN")]
        result, records, fake, transport = h.run_case("agent", script, fake)
        record = result["record"]
        self.assertEqual(record["execution_status"], "COMPLETED")
        revision_calls = [r["data"]["tool"] for r in h.events(records, "tool_result") if r["stage"] == "revision"]
        self.assertEqual(revision_calls, ["decompose_hs", "compare_partners"])
        self.assertEqual(blocks(records), [("revision", "requery_limit")])
        self.assertEqual(record["tool_attempts"], 7)  # 기본 3 + 재조회 시도 3(1개 막힘) + 최종 검증 1
        self.assertEqual(len(fake.tool_calls), 6)
        tools_offered = [p.get("tools") is not None for p in transport.payloads]
        self.assertEqual(tools_offered, [True, True, False])  # 재조회 몫을 다 쓰면 도구를 주지 않는다

    def test_third_requery_across_turns_is_blocked_too(self):
        fake = h.FakePorts(checks=[h.PASS, h.BLOCK, h.PASS])
        script = [h.draft_answer(status="MAINTAIN"), h.tools_answer("decompose_hs", "compare_partners"),
                  h.tools_answer("get_history"), h.draft_answer(status="MAINTAIN")]
        result, records, _, _ = h.run_case("agent", script, fake)
        self.assertEqual(result["record"]["execution_status"], "COMPLETED")
        self.assertEqual(blocks(records), [("revision", "requery_limit")])

    def test_deadline_comes_first_and_ends_the_run_as_timeout(self):
        # Critic 응답이 오는 동안 300초를 넘긴다 → 다음 도구 시도 앞에서 멈춘다(모델 요청 한도보다 먼저)
        script = [h.draft_answer(), {**h.critic_answer(), "elapsed_ms": 300_000}]
        result, records, fake, _ = h.run_case("full", script)
        record = result["record"]
        self.assertEqual((record["execution_status"], record["errors"][0]["code"]), ("TIMEOUT", cause_codes.DEADLINE))
        self.assertGreaterEqual(record["wall_ms"], 300_000)
        self.assertNotIn("verify_evidence", [name for name, _ in fake.tool_calls])
        self.assertIsNone(record["review_status_final"])
        self.assertEqual(h.events(records, "run_end")[0]["data"]["cause_code"], cause_codes.DEADLINE)

    def test_deadline_before_a_model_request_is_timeout_not_budget(self):
        script = [{**h.tools_answer("decompose_hs"), "elapsed_ms": 296_000}]
        result, _, fake, transport = h.run_case("full", script)
        self.assertEqual(result["record"]["errors"][0]["code"], cause_codes.DEADLINE)
        self.assertEqual(len(transport.payloads), 1)
        self.assertNotIn("decompose_hs", [name for name, _ in fake.tool_calls])  # deadline 뒤 도구를 부르지 않는다

    def test_tool_shares_cap_executed_tools_at_eight(self):
        # 기본 단계에서 비교 셋(하나 막힘), 수정 단계에서 재조회 셋(하나 막힘): 실행은 8회, 시도는 10회
        fake = h.FakePorts(checks=[h.PASS, h.BLOCK, h.PASS])
        script = [h.tools_answer("decompose_hs", "compare_partners", "get_history"), h.draft_answer(status="MAINTAIN"),
                  h.tools_answer("get_history", "check_comparability", "decompose_hs"),
                  h.draft_answer(status="MAINTAIN")]
        result, records, fake, _ = h.run_case("agent", script, fake)
        record = result["record"]
        self.assertEqual(record["execution_status"], "COMPLETED")
        self.assertEqual(len(fake.tool_calls), 8)
        self.assertEqual(record["tool_attempts"], 10)
        self.assertEqual(blocks(records), [("basic", "comparison_limit"), ("revision", "requery_limit")])
        self.assertLessEqual(max(fake.budget_asks), 7)  # 도구 예산 자리에 8번째까지만 물었다

    def test_tool_budget_port_refusal_is_counted_and_returned_to_the_model(self):
        fake = h.FakePorts(budget_limit=2)  # 도구 예산 자리가 세 번째 실행부터 거부한다
        script = [h.tools_answer("decompose_hs"), h.draft_answer()]
        result, records, fake, transport = h.run_case("agent", script, fake)
        self.assertEqual(blocks(records)[0], ("basic", "tool_attempts_limit"))
        tool_msgs = [m for m in transport.payloads[1]["messages"] if m["role"] == "tool"]
        self.assertIn('"blocked":true', tool_msgs[0]["content"])


class ModeRuleTest(unittest.TestCase):
    def test_full_completes_after_critic_without_revision(self):
        result, records, fake, _ = h.run_case("full", [h.draft_answer(), h.critic_answer()])
        record = result["record"]
        self.assertEqual((record["execution_status"], record["review_status_final"]), ("COMPLETED", "MONITOR"))
        self.assertEqual((record["critic_used"], record["revision_used"]), (True, False))
        self.assertEqual([n for n, _ in fake.tool_calls], ["check_comparability", "get_history", "verify_evidence"])
        self.assertEqual(fake.tool_calls[-1][1], {"metric_ids": ["m-rU"], "evidence_ids": []})
        self.assertEqual((record["model_requests"], record["tokens_in"], record["tokens_out"]), (2, 2700, 240))
        self.assertEqual(record["errors"], [])
        self.assertEqual(result["report"]["validator_findings"], [])
        phases = [r["data"]["phase"] for r in h.events(records, "state_change")]
        self.assertEqual(phases, ["draft", "after_critic", "final"])

    def test_schema_failure_on_first_draft_skips_critic(self):
        result, records, fake, transport = h.run_case("full", [h.text_answer("검토 유지가 맞다"), h.draft_answer()])
        record = result["record"]
        self.assertEqual(record["execution_status"], "COMPLETED")
        self.assertEqual((record["critic_used"], record["revision_used"]), (False, True))
        self.assertEqual(record["model_requests"], 2)
        self.assertEqual([n for n, _ in fake.tool_calls][-1], "verify_evidence")
        self.assertIn("[수정 단계]", transport.payloads[1]["messages"][-1]["content"])

    def test_report_schema_failure_after_revision_is_invalid(self):
        fake = h.FakePorts(checks=[h.SCHEMA_FAIL, h.SCHEMA_FAIL])
        result, records, _, _ = h.run_case("full", [h.draft_answer(), h.draft_answer()], fake)
        record = result["record"]
        self.assertEqual((record["execution_status"], record["errors"][0]["code"]), ("INVALID", cause_codes.SCHEMA_INVALID))
        self.assertIs(record["critic_used"], False)  # 첫 스키마 검사에서 막혀 Critic을 건너뛰었다

    def test_agent_has_no_critic_and_revises_on_validator_block(self):
        fake = h.FakePorts(checks=[h.PASS, h.BLOCK, h.PASS])
        result, records, _, transport = h.run_case("agent", [h.draft_answer(status="MAINTAIN"),
                                                             h.draft_answer(status="MAINTAIN")], fake)
        record = result["record"]
        self.assertEqual((record["execution_status"], record["critic_used"], record["revision_used"]),
                         ("COMPLETED", False, True))
        self.assertFalse([r for r in records if r["stage"] == "critic"])
        self.assertIn("[검증기 지적]", transport.payloads[1]["messages"][-1]["content"])

    def test_freeform_records_validator_findings_without_blocking(self):
        claim = {"claim_id": "c1", "claim_type": "change", "hs6": "850450", "partner": "CN", "period": "202401",
                 "baseline_period": "202301", "metric": "r_U", "value": "-40.0", "unit": "%", "direction": "DOWN",
                 "evidence_ids": [h.EV[0]], "text": "단가가 낮다."}
        fake = h.FakePorts(checks=[h.PASS, h.BLOCK])
        result, _, _, _ = h.run_case("freeform", [h.draft_answer(claims=[claim]), h.critic_answer()], fake)
        self.assertEqual(result["record"]["execution_status"], "COMPLETED")
        self.assertEqual(result["report"]["validator_findings"], h.BLOCK["findings"])
        self.assertIs(result["record"]["revision_used"], False)

    def test_freeform_schema_failure_still_ends_invalid(self):
        result, _, _, _ = h.run_case("freeform", [h.text_answer("x"), h.text_answer("y")])
        self.assertEqual(result["record"]["errors"][0]["code"], cause_codes.SCHEMA_INVALID)

    def test_checklist_uses_no_model_and_is_invalid_at_once_when_blocked(self):
        fake = h.FakePorts(checks=[h.BLOCK])
        result, records, fake, transport = h.run_case("checklist", [], fake)
        record = result["record"]
        self.assertIsNone(transport)
        self.assertEqual((record["execution_status"], record["errors"][0]["code"]), ("INVALID", cause_codes.VALIDATOR_BLOCKED))
        self.assertEqual((record["model_requests"], record["tokens_in"], record["revision_used"]), (0, 0, False))
        self.assertEqual(fake.check_calls, 1)  # 수정 단계 없이 곧바로(결정 D1)

    def test_checklist_fixed_order_completes(self):
        result, _, fake, _ = h.run_case("checklist", [], h.FakePorts(checklist_status="HOLD"))
        self.assertEqual([n for n, _ in fake.tool_calls],
                         ["check_comparability", "get_history", "decompose_hs", "compare_partners", "verify_evidence"])
        record = result["record"]
        self.assertEqual((record["execution_status"], record["review_status_final"], record["tool_attempts"]),
                         ("COMPLETED", "HOLD", 5))

    def test_not_comparable_skips_history_and_offers_no_tools(self):
        original = h.ENVELOPES["check_comparability"]
        h.ENVELOPES["check_comparability"] = h.envelope("check_comparability", "q-cc", comparable=False)
        self.addCleanup(h.ENVELOPES.__setitem__, "check_comparability", original)
        result, _, fake, transport = h.run_case("agent", [h.draft_answer(status="HOLD")])
        self.assertNotIn("get_history", [n for n, _ in fake.tool_calls])
        self.assertNotIn("tools", transport.payloads[0])
        self.assertEqual(result["record"]["review_status_final"], "HOLD")

    def test_invalid_model_tool_call_is_counted_and_refused(self):
        script = [h.tools_answer("run_sql"), h.draft_answer()]
        result, records, fake, _ = h.run_case("agent", script)
        self.assertEqual(blocks(records), [("basic", "invalid_call")])
        self.assertNotIn("run_sql", [n for n, _ in fake.tool_calls])
        self.assertEqual(result["record"]["tool_attempts"], 4)

    def test_provider_5xx_after_resends_fails_with_rerun_eligible_error(self):
        script = [h.draft_answer()] + [{"status": 503}] * 4
        result, _, _, _ = h.run_case("full", script)
        record = result["record"]
        error = record["errors"][0]
        self.assertEqual((record["execution_status"], error["code"], error["stage"]),
                         ("FAILED", cause_codes.PROVIDER_HTTP_5XX, "critic"))
        self.assertEqual(error["last_good_evidence"], h.EV[:2])
        self.assertEqual(error["attempts"]["model_requests"], 5)
        self.assertTrue(cause_codes.infra_rerun_eligible(record["execution_status"], record["errors"]))

    def test_unexpected_exception_is_code_error_with_class_name_only(self):
        fake = h.FakePorts()
        fake.build_report = lambda inp: (_ for _ in ()).throw(KeyError("비밀 경로 문구"))
        result, _, _, _ = h.run_case("agent", [h.draft_answer()], fake)
        error = result["record"]["errors"][0]
        self.assertEqual((error["code"], error["detail"]), (cause_codes.CODE_ERROR, "KeyError"))



class ReviewRoundOneTest(unittest.TestCase):
    """검토 1회차의 막는 지적 1·4와 권고 6·8·10, NVIDIA 권고 3."""

    def test_freeform_status_mismatch_is_recorded_not_blocked_and_critic_runs(self):
        fake = h.FakePorts(checks=[h.PASS, STATUS_BLOCK])
        result, records, fake, _ = h.run_case("freeform", [mismatched(claims=[FREEFORM_CLAIM]), h.critic_answer()],
                                              fake)
        record = result["record"]
        self.assertEqual((record["execution_status"], record["critic_used"], record["revision_used"]),
                         ("COMPLETED", True, False))
        self.assertEqual(result["report"]["validator_findings"], [STATUS_FINDING])
        draft_state = h.events(records, "state_change")[0]["data"]
        self.assertEqual((draft_state["phase"], draft_state["problems"], draft_state["problem_list"]),
                         ("draft", 0, []))
        self.assertTrue(draft_state["status_notes"])  # 관찰은 trace에 남는다
        self.assertEqual(fake.check_calls, 2)  # 검증기 경로를 탔다(스키마 검사 + 검증)

    def test_full_status_mismatch_goes_through_critic_then_validator_block_opens_revision(self):
        fake = h.FakePorts(checks=[h.PASS, STATUS_BLOCK, h.PASS])
        script = [mismatched(), h.critic_answer(), h.draft_answer(status="HOLD")]
        result, records, _, transport = h.run_case("full", script, fake)
        record = result["record"]
        self.assertEqual((record["execution_status"], record["critic_used"], record["revision_used"]),
                         ("COMPLETED", True, True))
        self.assertEqual(record["review_status_final"], "HOLD")
        self.assertIn("[검증기 지적]", transport.payloads[2]["messages"][-1]["content"])
        self.assertIn("STATUS_INCONSISTENT", transport.payloads[2]["messages"][-1]["content"])

    def test_not_comparable_revision_offers_no_tools_and_refuses_model_calls(self):
        not_comparable(self)
        requery = [{"tool": "get_history", "args": {}, "reason": "이력"}]
        script = [h.draft_answer(status="HOLD"), h.critic_answer(needs_revision=True, requery=requery),
                  h.tools_answer("get_history", "decompose_hs"), h.draft_answer(status="HOLD")]
        result, records, fake, transport = h.run_case("full", script)
        record = result["record"]
        self.assertEqual(record["execution_status"], "COMPLETED")
        self.assertEqual([p.get("tools") for p in transport.payloads], [None] * 4)  # 어느 요청에도 도구가 없다
        self.assertEqual([n for n, _ in fake.tool_calls], ["check_comparability", "verify_evidence", "verify_evidence"])
        self.assertEqual(blocks(records), [("revision", "not_comparable"), ("revision", "not_comparable")])
        self.assertEqual(record["tool_attempts"], 5)  # 실행 3 + 막힌 시도 2
        feedback = [m["content"] for m in transport.payloads[-1]["messages"]
                    if m["role"] == "user" and m["content"].startswith("[수정 단계]")]
        self.assertEqual(len(feedback), 1)
        self.assertIn("재조회 0회", feedback[0])  # 도구를 주지 않는 차례에는 0회로 알린다

    def test_missing_comparable_key_stops_as_code_error(self):
        original = h.ENVELOPES["check_comparability"]
        h.ENVELOPES["check_comparability"] = dict(original, comparability={})
        self.addCleanup(h.ENVELOPES.__setitem__, "check_comparability", original)
        for mode in ("full", "checklist"):
            with self.subTest(mode=mode):
                result, _, fake, _ = h.run_case(mode, [])
                error = result["record"]["errors"][0]
                self.assertEqual((error["code"], result["record"]["execution_status"]), (cause_codes.CODE_ERROR, "FAILED"))
                self.assertIn("comparable", error["detail"])
                self.assertEqual([n for n, _ in fake.tool_calls], ["check_comparability"])

    def test_truncated_draft_is_a_format_problem_that_opens_revision(self):
        cut = {"body": ok_body(json.dumps(h.draft(), ensure_ascii=False), prompt_tokens=1500, completion_tokens=2048,
                               finish_reason="length")}
        result, records, _, _ = h.run_case("full", [cut, h.draft_answer()])
        record = result["record"]
        self.assertEqual((record["execution_status"], record["critic_used"], record["revision_used"]),
                         ("COMPLETED", False, True))
        draft_state = h.events(records, "state_change")[0]["data"]
        self.assertEqual(draft_state["problem_list"][0], investigator.TRUNCATED)

    def test_critic_used_is_true_once_the_critic_stage_opens(self):
        result, _, _, _ = h.run_case("full", [h.draft_answer()] + [{"status": 503}] * 4)
        record = result["record"]
        self.assertEqual((record["errors"][0]["stage"], record["critic_used"]), ("critic", True))

    def test_required_evidence_failure_is_recorded_as_code_error(self):
        fake = h.FakePorts()
        fake.required_evidence = lambda case: (_ for _ in ()).throw(KeyError("정책"))
        result, records, _, transport = h.run_case("full", [], fake)
        error = result["record"]["errors"][0]
        self.assertEqual((error["code"], error["detail"]), (cause_codes.CODE_ERROR, "KeyError"))
        self.assertEqual([r["event"] for r in records], ["run_start", "run_end"])
        self.assertEqual(transport.payloads, [])

    def test_bad_run_context_fails_before_any_request_or_tool(self):
        fake = h.FakePorts()
        transport = h.ScriptedTransport([h.draft_answer()])
        with self.assertRaises(ValueError):
            h.run_case("full", [], fake, dataset="dev21", transport=transport)
        self.assertEqual((transport.payloads, fake.tool_calls), ([], []))

    def test_template_fill_rejections_are_recorded(self):
        rejected = [{"claim_id": "c2", "reason": "없는 metric_id"}]
        result, records, _, _ = h.run_case("full", [h.draft_answer(), h.critic_answer()],
                                           h.FakePorts(rejected=rejected))
        self.assertEqual(result["record"]["execution_status"], "COMPLETED")
        self.assertEqual([r["data"]["rejected_requests"] for r in h.events(records, "validator_result")],
                         [rejected, rejected])


class UnitPortsTest(unittest.TestCase):
    """unit_ports 배선: 이 브랜치에서 뼈대인 다른 트랙 단위의 run을 대역으로 바꿔, 넘기는 입력 모양을 본다."""

    def ports(self, **kw):
        limits = mc.load_model_config().limits
        return orchestrate.unit_ports(h.CASE_A, "full", h.RUN_ID, limits, grouping_version="g0", **kw)

    def patch(self, target, stub):
        patcher = mock.patch(target, stub)
        patcher.start()
        self.addCleanup(patcher.stop)

    def render_stub(self):
        seen = {}

        def render(inp):
            seen.update(inp)
            return {"report": {"unresolved_evidence": inp["unresolved_evidence"]}, "body_ko": ""}
        self.patch("tradesentry.reports.render_ko.run", render)
        self.patch("tradesentry.reports.claims.run", lambda inp: {"claims": [], "rejected": [{"claim_id": "c1",
                                                                                            "reason": "r"}]})
        return seen

    def test_build_report_keeps_going_when_the_aggregate_rejects_the_statuses(self):
        seen = self.render_stub()

        def aggregate(inp):
            raise ValueError("발동하지 않은 신호 share의 상태는 NOT_TRIGGERED여야 한다")
        self.patch("tradesentry.policy.case_aggregate.run", aggregate)
        draft = {"review_status": "MAINTAIN", "signal_status": {"unit_value": "MAINTAIN", "share": "HOLD"},
                 "claims": [], "narrative": "", "hypotheses": []}
        built = self.ports().build_report({"draft": draft, "evidence": []})
        # 상태를 고치지 않는다. unresolved_evidence는 발동 신호만 보고 센다(share는 미발동이라 섞임 없음)
        self.assertEqual((seen["signal_status"], seen["review_status"]), (draft["signal_status"], "MAINTAIN"))
        self.assertIs(built["report"]["unresolved_evidence"], False)
        self.assertEqual(built["rejected"], [{"claim_id": "c1", "reason": "r"}])

    def test_build_report_does_not_hide_other_errors(self):
        self.render_stub()

        def skeleton(inp):
            raise NotImplementedError
        self.patch("tradesentry.policy.case_aggregate.run", skeleton)
        draft = {"review_status": "MONITOR", "signal_status": {"unit_value": "MONITOR", "share": "NOT_TRIGGERED"}}
        with self.assertRaises(NotImplementedError):
            self.ports().build_report({"draft": draft, "evidence": []})

    def test_budget_gets_every_limit_key_and_the_stage(self):
        seen = {}
        self.patch("tradesentry.tools.budget.run", lambda inp: seen.update(inp) or {"allowed": True, "reason": None})
        self.ports().budget([{"tool": "check_comparability", "args": {}, "stage": "basic"}],
                            {"tool": "get_history", "args": {}, "stage": "revision"})
        self.assertEqual(seen["limits"], {"tool_attempts": 8, "basic_tool_attempts": 5, "revision_stages": 1,
                                          "revision_requeries": 2, "final_verify": 1})
        self.assertEqual(seen["candidate"]["stage"], "revision")

    def test_statuses_read_partner_code_and_single_evidence_id(self):
        item = {"evidence_id": "ev:controlled_fixture_v0:status:7", "request_id": "r7", "partner_code": "CN",
                "hs_code": "850450", "month": "202401", "flow": "import", "observation_status": "NOT_COLLECTED"}
        child = dict(item, evidence_id="ev:controlled_fixture_v0:status:8", hs_code="8504501000")
        envelopes = [{"missingness": [item, child]}, {"missingness": [item]}]  # 같은 항목이 두 봉투에 나온다
        statuses = orchestrate._statuses_of(envelopes)
        self.assertEqual([(s["status_id"], s["partner"], s["period"], s["hs6"], s["hs10"]) for s in statuses],
                         [(item["evidence_id"], "CN", "202401", "850450", None),
                          (child["evidence_id"], "CN", "202401", "850450", "8504501000")])

    def test_checklist_evidence_state_carries_comparison_marks_or_the_assembly_hook(self):
        seen = {}

        def decide(inp):
            seen.update(inp)
            return {"signal_status": {"unit_value": "HOLD", "share": "NOT_TRIGGERED"}}
        self.patch("tradesentry.policy.signal_decide.run", decide)
        self.patch("tradesentry.policy.case_aggregate.run",
                   lambda inp: {"review_status": "HOLD", "unresolved_evidence": False})
        missing = {"evidence_id": "ev:controlled_fixture_v0:status:7", "partner_code": "CN", "hs_code": "850450",
                   "month": "202401", "observation_status": "NOT_COLLECTED"}
        envelopes = [dict(h.ENVELOPES["check_comparability"], missingness=[missing]), h.ENVELOPES["get_history"]]
        draft = self.ports(policy={"policy_version": "dev-0.1"}).checklist_draft({"evidence": envelopes})
        self.assertEqual(draft["review_status"], "HOLD")
        self.assertEqual(seen["evidence"], {"missingness": [missing], "unit_value": {"comparisons": {
            "comparability": "done", "partners": "not_performed"}}})  # 미발동 점유율 블록은 없다
        hook = lambda case, evidence: {"from": "AS2", "n": len(evidence)}  # noqa: E731
        self.ports(evidence_state=hook).checklist_draft({"evidence": envelopes})
        self.assertEqual(seen["evidence"], {"from": "AS2", "n": 2})
        failed = dict(h.ENVELOPES["compare_partners"], retryable_error={"code": "bad_args"})
        self.assertEqual(orchestrate.comparison_marks([failed])["partners"], "not_performed")


if __name__ == "__main__":
    unittest.main()
