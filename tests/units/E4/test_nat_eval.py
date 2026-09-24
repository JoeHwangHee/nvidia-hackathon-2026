"""단위 E4(evaluation_nat_eval) 골든 쌍 밖 시험: 가짜 NAT 프로파일 폴더(실측 모양)에서 사실 뽑기, dev20 모양 묶음 요약,
봉인 묶음 거부, 요약이 실행 조건 입력 파일(nat_profile_summary)로 들어갈 수 있음, 단위 I13의 이름과 같음.
모든 파일은 임시 폴더에 쓴다. nat 패키지를 import하지 않는다.
"""
import os
import tempfile
import unittest
from pathlib import Path

import harness_fixtures as hf
from tradesentry.evaluation import batch_run, nat_eval
from tradesentry.runlog import trace as trace_log
from tradesentry.workflow import nat_wrap


class ProfileFactsTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def test_facts_from_measured_shape(self):
        nat_dir = self.root / "workflow_nat_wrap-260925100000"
        hf.write_profile(nat_dir, llm=[(1200, 2800, 80), (2400, 3000, 150)], spans=["basic", "critic", "Revision"],
                         workflow_ms=6000, tools=3)
        facts = nat_eval.profile_facts(nat_dir)
        self.assertEqual(facts, {"files": 5, "llm_calls": 2, "llm_ms": 3600, "nat_tokens": 6030, "tool_calls": 3,
                                 "workflow_ms": 6000,
                                 "stage_spans": {"basic": 1, "critic": 1, "revision": 0, "final": 0, "other": 1}})

    def test_missing_or_broken_files(self):
        self.assertIsNone(nat_eval.profile_facts(self.root / "none"))
        nat_dir = self.root / "workflow_nat_wrap-260925100000"
        hf.write_profile(nat_dir, llm=[], spans=[], workflow_ms=10, files=hf.PROFILE_FILES[1:])
        facts = nat_eval.profile_facts(nat_dir)
        self.assertEqual((facts["files"], facts["llm_calls"], facts["workflow_ms"]), (4, None, None))
        (nat_dir / "all_requests_profiler_traces.json").write_text("{not json", encoding="utf-8")
        self.assertEqual(nat_eval.profile_facts(nat_dir)["llm_calls"], None)

    def test_names_match_unit_i13(self):
        self.assertEqual(nat_eval.NAT_DIR_DOMAIN, nat_wrap.DOMAIN)
        self.assertEqual(nat_eval.PROFILE_FILES, nat_wrap.PROFILE_FILES)
        self.assertEqual(hf.PROFILE_FILES, nat_wrap.PROFILE_FILES)


class BatchSummaryTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.outputs = Path(tmp.name) / "outputs"
        clock = hf.FakeClock()
        s = batch_run.BatchSpec(dataset="dev20", cases=tuple(hf.dev20_cases()), modes=hf.DEV20_MODES,
                                order_seed="dev-order-v1", versions=dict(hf.VERSIONS))
        plan = {"850431-XA-202401": "infra", "850450-XC-202403": "raise"}
        self.result = batch_run.execute_batch(s, hf.FakeRunner(clock, plan), parent=self.outputs,
                                              other_parent=self.outputs / "sealed", clock=clock, sleep=clock.sleep)

    def test_dev20_shape_summary(self):
        summary = nat_eval.summarize_batch(self.result.run_dir)
        self.assertEqual(summary["runs"], 60)
        # 프로파일: checklist 밖 모드의 ok·infra 사례(raise 사례 2줄은 프로파일을 쓰지 않았다)
        self.assertEqual(summary["runs_with_profile"], 38)
        self.assertEqual(summary["profile_files_complete"], 38)
        self.assertEqual(list(summary["by_mode"]), ["checklist", "agent", "full"])
        full = summary["by_mode"]["full"]
        self.assertEqual((full["runs"], full["runs_with_profile"]), (20, 19))
        self.assertEqual(full["nat_llm_calls"], {"median": 2, "min": 2, "max": 2})
        self.assertEqual(full["nat_llm_ms"], {"median": 3600, "min": 3600, "max": 3600})
        self.assertEqual(full["stage_spans"], {"basic": 19, "critic": 19, "revision": 0, "final": 0, "other": 0})
        self.assertEqual(summary["by_mode"]["checklist"]["model_requests"], {"median": 0, "min": 0, "max": 0})
        self.assertEqual(summary["by_mode"]["agent"]["wall_ms"]["max"], 40000)

    def test_summary_is_safe_for_the_run_conditions_file(self):
        summary = nat_eval.summarize_batch(self.result.run_dir)
        text = trace_log.dumps(summary)
        for case in hf.dev20_cases():
            self.assertNotIn(case["case_id"], text)
        self.assertNotIn("run_case-", text)
        doc = batch_run.build_run_conditions(dataset="dev20", cases=hf.dev20_cases(), modes=list(hf.DEV20_MODES),
                                             thresholds=[30, 10], nat_profile_summary=summary)
        path = batch_run.write_run_conditions(self.result.run_dir, doc)
        self.assertEqual(trace_log.loads(path.read_text(encoding="utf-8"))["nat_profile_summary"], summary)

    def test_sealed_batch_is_not_read(self):
        sealed = self.outputs / "sealed"
        sealed.mkdir()
        moved = sealed / self.result.run_dir.name
        os.rename(self.result.run_dir, moved)  # 봉인 자리를 흉내 낸 임시 폴더
        with self.assertRaises(nat_eval.NatEvalError):
            nat_eval.summarize_batch(moved)

    def test_bad_input(self):
        for bad in ({"runs": [{"mode": "fast"}]}, {"runs": "x"}, {"lines": []}):
            with self.subTest(bad=bad), self.assertRaises(nat_eval.NatEvalError):
                nat_eval.run(bad)


if __name__ == "__main__":
    unittest.main()
