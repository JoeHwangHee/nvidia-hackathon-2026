"""단위 L2(runlog_run_record) 골든 쌍 밖 규칙 시험: 실행명 확보(N8), 키 순서, 상태·모드별 검사."""
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from tradesentry.runlog import cause_codes, run_record
from tradesentry.runlog import trace as trace_log

BASE = datetime(2026, 9, 25, 14, 30, 15, 400000, tzinfo=trace_log.KST)


def completed(**over):
    facts = {"run_id": "run_case-260925143015", "case_id": "B-residual", "dataset": "dev20", "mode": "full",
             "policy_version": "dev-0.1", "rulebook_version": "RB-1", "snapshot_id": "controlled_fixture_v0",
             "grouping_version": "g0", "code_version": "abc1234", "review_status_final": "MAINTAIN",
             "signal_status": {"unit_value": "MAINTAIN", "share": "NOT_TRIGGERED"}, "unresolved_evidence": False,
             "execution_status": "COMPLETED", "tool_attempts": 6, "model_requests": 5, "tokens_in": 9000,
             "tokens_out": 1100, "wall_ms": 52000, "critic_used": True, "revision_used": True, "errors": []}
    facts.update(over)
    return facts


class FakeClock:
    def __init__(self, start):
        self.now = start
        self.slept = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += timedelta(seconds=seconds)


class RunRecordRuleTest(unittest.TestCase):
    def test_record_uses_contract_order_without_scorer_keys(self):
        record = run_record.run(completed())
        self.assertEqual(tuple(record), run_record.RUN_KEYS)
        self.assertEqual(len(record), 21)
        self.assertFalse(set(run_record.SCORER_KEYS) & set(record))

    def test_rejects_rule_violations(self):
        entry = cause_codes.error_entry(cause_codes.DEADLINE, "revision", {k: 1 for k in cause_codes.ATTEMPT_KEYS}, [])
        bad = {
            "채점 키": dict(completed(), numeric_ok=True),
            "COMPLETED에 errors": completed(errors=[entry]),
            "멈춘 실행에 최종 판정": completed(execution_status="TIMEOUT", errors=[entry]),
            "멈춘 실행에 신호별 판정": completed(execution_status="TIMEOUT", review_status_final=None, errors=[entry]),
            "멈춘 실행에 errors 없음": completed(execution_status="TIMEOUT", review_status_final=None,
                                            signal_status=None),
            "상태와 코드 불일치": completed(execution_status="FAILED", review_status_final=None, signal_status=None,
                                     errors=[entry]),
            "checklist 모델 사용": completed(mode="checklist", critic_used=False, revision_used=False),
            "agent Critic": completed(mode="agent"),
            "PRE_INVESTIGATION": completed(review_status_final="PRE_INVESTIGATION"),
            "음수": completed(wall_ms=-1),
            "bool 수": completed(tool_attempts=True),
            "모드 밖": completed(mode="baseline"),
            "run_id 형식": completed(run_id="run-case-1"),
        }
        for name, facts in bad.items():
            with self.subTest(name), self.assertRaises(ValueError):
                run_record.run(facts)
        ok = completed(execution_status="TIMEOUT", review_status_final=None, signal_status=None, errors=[entry])
        self.assertEqual(run_record.run(ok)["errors"], [entry])

    def test_reserve_waits_for_the_second_and_skips_taken_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            outputs, sealed = Path(tmp) / "outputs", Path(tmp) / "outputs" / "sealed"
            clock = FakeClock(BASE)
            (outputs / "run_case-260925143015").mkdir(parents=True)  # 지금 초의 이름은 이미 있다
            (sealed / "run_case-260925143016").mkdir(parents=True)  # 다음 초는 다른 부모에 있다
            run_id, stamp, run_dir = run_record.reserve_run_dir(outputs, sealed, "run_case", clock=clock,
                                                                sleep=clock.sleep)
            self.assertEqual((run_id, stamp), ("run_case-260925143017", "260925143017"))
            self.assertTrue(run_dir.is_dir())
            self.assertFalse((outputs / "run_case-260925143016").exists())  # 만들었다가 지운 빈 폴더
            self.assertGreaterEqual(clock.now, BASE.replace(second=17, microsecond=0))
            with self.assertRaises(ValueError):
                run_record.reserve_run_dir(outputs, sealed, "run-case", clock=clock, sleep=clock.sleep)

    def test_reserve_gives_up_after_max_attempts(self):
        with tempfile.TemporaryDirectory() as tmp:
            outputs = Path(tmp) / "outputs"
            clock = FakeClock(BASE)
            for second in range(15, 20):
                (outputs / f"evaluate-2609251430{second}").mkdir(parents=True)
            with self.assertRaises(run_record.RunNameError):
                run_record.reserve_run_dir(outputs, outputs / "sealed", "evaluate", clock=clock, sleep=clock.sleep,
                                           max_attempts=5)


if __name__ == "__main__":
    unittest.main()
