"""단위 I6(tools_budget) 보조 시험: 예산 집행 규칙.

MVP 합격 체크리스트 2번(docs/plan/ROADMAP.md §3)의 도구 쪽 증거다. 골든 쌍(input.json·expected.json)은 예산을 쓴 시도
8건 뒤의 9번째 시도 차단이고, 이 파일은 나머지 규칙을 하나씩 본다.
- 9번째 시도 차단(실패·캐시 적중·verify_evidence·같은 도구 다른 인자 재호출도 예산을 쓴다)
- 막힌 시도는 기록(recorded)에만 들고 예산을 쓰지 않는다(예약된 최종 검증 몫을 지킨다)
- 수정 단계의 세 번째 재조회 차단, 두 번째 수정 단계 차단, Critic 차례의 도구 차단, deadline 우선
- 같은 인자 재호출 차단(인자 정규화)과 verify_evidence 예외, 기본 경로의 verify_evidence 몫, 최종 단계 규칙
- 흐름 조정(단위 I12)의 지금 호출 모양({"attempts": 실행한 시도, "candidate", "limits": {"tool_attempts"}})
"""
import unittest

from tradesentry.tools import budget

LIMITS = {"tool_attempts": 8, "basic_tool_attempts": 5, "revision_stages": 1, "revision_requeries": 2,
          "final_verify": 1}
VERIFY_ARGS = {"metric_ids": ["m-1"], "evidence_ids": ["ev:s:observation:1"]}


def attempt(tool, stage, outcome="ok", **args):
    return {"tool": tool, "args": args, "stage": stage, "outcome": outcome}


def basic_path():
    """기본 경로 5회: 비교 가능성, 이력, 비교국(실패), 비교국(다른 인자), verify_evidence."""
    return [attempt("check_comparability", "basic"), attempt("get_history", "basic"),
            attempt("compare_partners", "basic", "failed", partners=["ZZ"]),
            attempt("compare_partners", "basic", partners=["ID", "MY"]),
            {"tool": "verify_evidence", "args": VERIFY_ARGS, "stage": "basic", "outcome": "ok"}]


class NinthAttemptTest(unittest.TestCase):
    def test_ninth_attempt_is_blocked_whatever_the_stage(self):
        tb = budget.ToolBudget(LIMITS)
        steps = [("check_comparability", {}, "basic", "ok"), ("get_history", {}, "basic", "ok"),
                 ("compare_partners", {"partners": ["ZZ"]}, "basic", "failed"),
                 ("compare_partners", {"partners": ["ID"]}, "basic", "ok"),
                 ("verify_evidence", VERIFY_ARGS, "basic", "ok"),
                 ("decompose_hs", {}, "revision", "ok"), ("compare_partners", {"partners": ["MY"]}, "revision", "cache_hit"),
                 ("verify_evidence", VERIFY_ARGS, "final", "ok")]
        for tool, args, stage, outcome in steps:
            verdict = tb.gate(tool, args, stage)
            self.assertTrue(verdict["allowed"], (tool, stage, verdict["reason"]))
            tb.record(tool, args, stage, outcome)
        self.assertEqual((tb.consumed, tb.recorded), (8, 8))
        for tool, stage in (("get_history", "revision"), ("verify_evidence", "final"), ("check_comparability", "basic"),
                            ("decompose_hs", "revision")):
            verdict = tb.gate(tool, {"n": stage}, stage)
            self.assertEqual((verdict["allowed"], verdict["reason"]), (False, budget.TOOL_ATTEMPTS_LIMIT), (tool, stage))
            self.assertEqual(verdict["remaining"], 0)
        self.assertEqual((tb.consumed, tb.recorded), (8, 12))  # 막힌 시도는 기록(recorded)에만 들고 예산은 안 쓴다

    def test_failure_cache_hit_verify_and_same_tool_recall_all_consume(self):
        attempts = [attempt("check_comparability", "basic", "failed"),
                    attempt("check_comparability", "basic", "cache_hit", retry=True),
                    {"tool": "verify_evidence", "args": VERIFY_ARGS, "stage": "basic", "outcome": "ok"},
                    attempt("get_history", "basic", "blocked")]
        verdict = budget.decide(attempts, {"tool": "get_history", "args": {}, "stage": "basic"}, LIMITS)
        self.assertEqual(verdict["counts"]["consumed"], 3)
        self.assertEqual(verdict["counts"]["recorded"], 4)
        self.assertEqual(verdict["remaining"], 5)
        self.assertTrue(verdict["allowed"])

    def test_limit_value_comes_from_limits(self):
        attempts = [attempt("check_comparability", "basic"), attempt("get_history", "basic")]
        verdict = budget.decide(attempts, {"tool": "decompose_hs", "args": {}, "stage": "basic"},
                                {"tool_attempts": 2})
        self.assertEqual(verdict["reason"], budget.TOOL_ATTEMPTS_LIMIT)


class StageTest(unittest.TestCase):
    def test_third_requery_in_revision_is_blocked(self):
        attempts = basic_path() + [attempt("decompose_hs", "revision"),
                                   attempt("compare_partners", "revision", partners=["PH"])]
        verdict = budget.decide(attempts, {"tool": "get_history", "args": {"x": 1}, "stage": "revision"}, LIMITS)
        self.assertEqual((verdict["allowed"], verdict["reason"]), (False, budget.REQUERY_LIMIT))

    def test_second_revision_stage_is_blocked(self):
        attempts = basic_path() + [attempt("decompose_hs", "revision"),
                                   {"tool": "verify_evidence", "args": VERIFY_ARGS, "stage": "final", "outcome": "ok"}]
        verdict = budget.decide(attempts, {"tool": "get_history", "args": {"x": 1}, "stage": "revision"}, LIMITS)
        self.assertEqual((verdict["allowed"], verdict["reason"]), (False, budget.REVISION_LIMIT))
        self.assertEqual(verdict["counts"]["revision_stages"], 1)

    def test_revision_stage_is_counted_from_the_sequence(self):
        # 수정 단계 안에서 이어지는 조회는 같은 단계다. 막힌 기록이 끼어도 새 단계로 보지 않는다.
        attempts = basic_path() + [attempt("decompose_hs", "revision"), attempt(None, "revision", "blocked")]
        verdict = budget.decide(attempts, {"tool": "compare_partners", "args": {"partners": ["PH"]},
                                           "stage": "revision"}, LIMITS)
        self.assertTrue(verdict["allowed"], verdict["reason"])

    def test_critic_stage_calls_no_tools(self):
        verdict = budget.decide(basic_path()[:2], {"tool": "decompose_hs", "args": {}, "stage": "critic"}, LIMITS)
        self.assertEqual((verdict["allowed"], verdict["reason"]), (False, budget.CRITIC_NO_TOOLS))

    def test_basic_path_keeps_one_slot_for_verify_evidence(self):
        attempts = [attempt("check_comparability", "basic"), attempt("get_history", "basic"),
                    attempt("compare_partners", "basic", partners=["ID"]), attempt("decompose_hs", "basic")]
        blocked = budget.decide(attempts, {"tool": "compare_partners", "args": {"partners": ["PH"]}, "stage": "basic"},
                                LIMITS)
        self.assertEqual((blocked["allowed"], blocked["reason"]), (False, budget.BASIC_LIMIT))
        allowed = budget.decide(attempts, {"tool": "verify_evidence", "args": VERIFY_ARGS, "stage": "basic"}, LIMITS)
        self.assertTrue(allowed["allowed"])
        full = budget.decide(basic_path(), {"tool": "get_history", "args": {"x": 1}, "stage": "basic"}, LIMITS)
        self.assertEqual(full["reason"], budget.BASIC_LIMIT)

    def test_final_stage_is_one_verify_evidence(self):
        attempts = basic_path()
        other = budget.decide(attempts, {"tool": "get_history", "args": {"x": 1}, "stage": "final"}, LIMITS)
        self.assertEqual(other["reason"], budget.FINAL_VERIFY_ONLY)
        attempts.append({"tool": "verify_evidence", "args": {"metric_ids": ["m-2"]}, "stage": "final", "outcome": "ok"})
        again = budget.decide(attempts, {"tool": "verify_evidence", "args": {"metric_ids": ["m-3"]}, "stage": "final"},
                              LIMITS)
        self.assertEqual(again["reason"], budget.FINAL_VERIFY_LIMIT)

    def test_blocked_attempts_do_not_take_the_reserved_final_verify(self):
        """한 차례에 도구 호출 셋을 낸 모델의 세 번째 재조회가 막혀도 최종 verify_evidence 몫은 남는다."""
        tb = budget.ToolBudget(LIMITS)
        for record in basic_path():
            tb.record(record["tool"], record["args"], record["stage"], record["outcome"])
        for partners in (["PH"], ["CN"], ["MX"]):
            verdict = tb.gate("compare_partners", {"partners": partners}, "revision")
            if verdict["allowed"]:
                tb.record("compare_partners", {"partners": partners}, "revision", "ok")
        self.assertEqual((tb.consumed, tb.recorded), (7, 8))
        final = tb.gate("verify_evidence", VERIFY_ARGS, "final")
        self.assertTrue(final["allowed"], final["reason"])


class DeadlineTest(unittest.TestCase):
    def test_deadline_is_checked_first(self):
        attempts = basic_path() + [attempt("decompose_hs", "revision"), attempt("get_history", "revision", x=1),
                                   {"tool": "verify_evidence", "args": VERIFY_ARGS, "stage": "final", "outcome": "ok"}]
        verdict = budget.decide(attempts, {"tool": "decompose_hs", "args": {}, "stage": "critic"}, LIMITS,
                                now_ms=300_000, deadline_ms=300_000)
        self.assertEqual((verdict["allowed"], verdict["reason"]), (False, budget.DEADLINE))

    def test_before_deadline_is_allowed(self):
        verdict = budget.decide([], {"tool": "check_comparability", "args": {}, "stage": "basic"}, LIMITS,
                                now_ms=299_999, deadline_ms=300_000)
        self.assertTrue(verdict["allowed"])

    def test_tool_budget_uses_its_deadline(self):
        tb = budget.ToolBudget(LIMITS, deadline_ms=1_000)
        self.assertTrue(tb.gate("check_comparability", {}, "basic", now_ms=999)["allowed"])
        self.assertEqual(tb.gate("get_history", {}, "basic", now_ms=1_000)["reason"], budget.DEADLINE)
        self.assertEqual(tb.recorded, 1)

    def test_now_and_deadline_come_together(self):
        with self.assertRaises(ValueError):
            budget.decide([], {"tool": "get_history", "args": {}, "stage": "basic"}, LIMITS, now_ms=1)


class SameArgsTest(unittest.TestCase):
    def test_same_args_recall_is_blocked_after_normalizing(self):
        attempts = [attempt("check_comparability", "basic"),
                    attempt("compare_partners", "basic", partners=["MY", "ID"], note={"b": 1, "a": 2})]
        verdict = budget.decide(attempts, {"tool": "compare_partners",
                                           "args": {"note": {"a": 2, "b": 1}, "partners": ["ID", "MY", "ID"]},
                                           "stage": "basic"}, LIMITS)
        self.assertEqual((verdict["allowed"], verdict["reason"], verdict["same_as"]), (False, budget.SAME_ARGS, 1))

    def test_same_tool_with_other_args_is_allowed(self):
        attempts = [attempt("compare_partners", "basic", partners=["ID"])]
        verdict = budget.decide(attempts, {"tool": "compare_partners", "args": {"partners": ["MY"]}, "stage": "basic"},
                                LIMITS)
        self.assertTrue(verdict["allowed"])

    def test_failed_same_args_blocks_the_repeat_but_blocked_record_does_not(self):
        failed = [attempt("compare_partners", "basic", "failed", partners=["ZZ"])]
        verdict = budget.decide(failed, {"tool": "compare_partners", "args": {"partners": ["ZZ"]}, "stage": "revision"},
                                LIMITS)
        self.assertEqual(verdict["reason"], budget.SAME_ARGS)
        blocked = [attempt("get_history", "basic", "blocked")]
        self.assertTrue(budget.decide(blocked, {"tool": "get_history", "args": {}, "stage": "basic"}, LIMITS)["allowed"])

    def test_verify_evidence_is_not_blocked_as_same_args(self):
        attempts = basic_path()
        verdict = budget.decide(attempts, {"tool": "verify_evidence", "args": dict(VERIFY_ARGS), "stage": "final"},
                                LIMITS)
        self.assertTrue(verdict["allowed"], verdict["reason"])

    def test_same_args_across_stages(self):
        attempts = basic_path()
        verdict = budget.decide(attempts, {"tool": "get_history", "args": {}, "stage": "revision"}, LIMITS)
        self.assertEqual((verdict["reason"], verdict["same_as"]), (budget.SAME_ARGS, 1))


class InputTest(unittest.TestCase):
    def test_mt4_call_shape_executed_attempts_without_outcome(self):
        executed = [{"tool": "check_comparability", "args": {}, "stage": "basic"},
                    {"tool": "get_history", "args": {}, "stage": "basic"}]
        verdict = budget.run({"attempts": executed, "candidate": {"tool": "get_history", "args": {}, "stage": "basic"},
                              "limits": {"tool_attempts": 8}})
        self.assertEqual((verdict["allowed"], verdict["reason"]), (False, budget.SAME_ARGS))
        self.assertEqual(verdict["counts"]["consumed"], 2)

    def test_limits_default_to_contract_values_and_ignore_other_keys(self):
        self.assertEqual(budget.parse_limits(None), budget.CONTRACT_LIMITS)
        self.assertEqual(budget.parse_limits({"model_requests": 10, "tokens": 32000}), budget.CONTRACT_LIMITS)
        self.assertEqual(budget.CONTRACT_LIMITS, {"tool_attempts": 8, "basic_tool_attempts": 5, "revision_stages": 1,
                                                  "revision_requeries": 2, "final_verify": 1})
        for bad in ({"tool_attempts": 0}, {"tool_attempts": True}, {"final_verify": "1"}, []):
            with self.assertRaises(ValueError, msg=bad):
                budget.parse_limits(bad)

    def test_unknown_tool_is_blocked_not_run(self):
        verdict = budget.decide([], {"tool": "run_sql", "args": {"query": "SELECT 1"}, "stage": "basic"}, LIMITS)
        self.assertEqual((verdict["allowed"], verdict["reason"]), (False, budget.UNKNOWN_TOOL))

    def test_malformed_records_raise(self):
        cases = [("x", {}), ([{"tool": "get_history", "args": {}, "stage": "plan"}], {}),
                 ([{"tool": "get_history", "args": {}, "stage": "basic", "outcome": "done"}], {}),
                 ([{"tool": "shell", "args": {}, "stage": "basic", "outcome": "ok"}], {}),
                 ([{"tool": "get_history", "args": {"x": 1.5}, "stage": "basic"}], {}),
                 ([], {"tool": "get_history", "args": {}, "stage": "basic", "outcome": "ok"})]
        for attempts, extra in cases:
            candidate = extra or {"tool": "get_history", "args": {}, "stage": "basic"}
            with self.assertRaises(ValueError, msg=attempts):
                budget.decide(attempts, candidate, LIMITS)
        with self.assertRaises(ValueError):
            budget.run({"attempts": [], "candidate": {"tool": "get_history", "args": {}, "stage": "basic"}, "x": 1})

    def test_blocked_records_accept_malformed_calls(self):
        tb = budget.ToolBudget(LIMITS)
        tb.record(None, {"raw": "not json"}, "basic", "blocked")
        tb.record("drop_table", {}, "basic", "blocked")
        self.assertEqual((tb.recorded, tb.consumed), (2, 0))
        with self.assertRaises(ValueError):
            tb.record("drop_table", {}, "basic", "ok")


if __name__ == "__main__":
    unittest.main()
