"""단위 E3(evaluation_extract) 골든 쌍 밖 시험: 묶음 E1이 쓴 기록에서 건수·재실행 대상, 봉인 묶음의 출력 위치(N10),
표준 출력에 사례 식별자가 나가지 않음, 사전 점검 값 대조. 모든 파일은 임시 폴더에 쓴다(실제 outputs/sealed/에 닿지 않는다).
"""
import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path

import harness_fixtures as hf
from tradesentry.evaluation import batch_run, extract
from tradesentry.runlog import trace as trace_log

PLAN = {"850431-XA-202401": "infra", "850450-XC-202403": "raise", ("850432-XB-202402", "agent"): "budget"}


class ExtractTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.outputs = self.root / "outputs"
        self.clock = hf.FakeClock()

    def batch(self, parent: Path) -> batch_run.BatchResult:
        """E1로 묶음을 만든다. parent가 봉인 자리면 outputs/에 만든 묶음 폴더를 그 자리로 옮긴다(E1은 봉인 자리에 쓰지
        않는다. 봉인 묶음 폴더를 흉내 낸 임시 폴더일 뿐 실제 봉인 묶음이 아니다)."""
        s = batch_run.BatchSpec(dataset="dev20", cases=tuple(hf.dev20_cases(4)), modes=hf.DEV20_MODES,
                                order_seed="dev-order-v1", versions=dict(hf.VERSIONS))
        result = batch_run.execute_batch(s, hf.FakeRunner(self.clock, PLAN), parent=self.outputs,
                                         other_parent=self.outputs / "sealed", clock=self.clock, sleep=self.clock.sleep)
        if parent != self.outputs:
            parent.mkdir(parents=True, exist_ok=True)
            os.rename(result.run_dir, parent / result.run_dir.name)
            result.run_dir = parent / result.run_dir.name
        return result

    def test_counts_and_rerun_list_from_a_batch(self):
        result = self.batch(self.outputs)
        run_id, counts = extract.extract(result.run_dir, outputs=self.outputs, expected_versions=dict(hf.VERSIONS),
                                         clock=self.clock, sleep=self.clock.sleep)
        self.assertEqual(counts["lines"], 12)
        self.assertEqual(counts["execution_status"],
                         {"COMPLETED": 5, "FAILED": 6, "TIMEOUT": 0, "INVALID": 0, "BUDGET_EXCEEDED": 1})
        self.assertEqual(counts["cause_codes"]["PROVIDER_HTTP_5XX"], 3)
        self.assertEqual(counts["cause_codes"]["CODE_ERROR"], 3)
        self.assertEqual(counts["cause_codes"]["BUDGET_TOKENS"], 1)
        self.assertEqual(counts["infra_rerun"], 3)
        self.assertTrue(all(v["match"] and v["mismatch"] == 0 for v in counts["version_keys"].values()))
        run_dir = self.outputs / run_id
        self.assertTrue(run_id.startswith("evaluation_extract-"))
        stamp = run_id.rsplit("-", 1)[1]
        targets = hf.read_jsonl(run_dir / f"evaluation_extract-{stamp}.jsonl")
        infra_lines = [x for x in result.lines if x["case_id"] == "850431-XA-202401"]
        self.assertEqual(targets, [{k: x[k] for k in ("run_id", "case_id", "mode")} for x in infra_lines])  # 첫 실행 순서
        self.assertEqual(trace_log.loads((run_dir / f"evaluation_extract-{stamp}.json").read_text()), counts)
        text = trace_log.dumps(counts)
        self.assertFalse(any(c["case_id"] in text for c in hf.dev20_cases(4)))  # 건수에는 사례 식별자가 없다
        self.assertNotIn("run_case-", text)

    def test_without_precheck_values_only_checks_single_value(self):
        result = self.batch(self.outputs)
        _, counts = extract.extract(result.run_dir, outputs=self.outputs, clock=self.clock, sleep=self.clock.sleep)
        self.assertFalse(counts["versions_checked_against_precheck"])
        self.assertEqual(counts["version_keys"]["code_version"], {"distinct": 1, "match": True, "mismatch": None})
        _, counts = extract.extract(result.run_dir, outputs=self.outputs, clock=self.clock, sleep=self.clock.sleep,
                                    expected_versions={**hf.VERSIONS, "code_version": "other"})
        self.assertEqual(counts["version_keys"]["code_version"], {"distinct": 1, "match": False, "mismatch": 12})

    def test_sealed_batch_output_stays_under_sealed_and_stdout_has_counts_only(self):
        sealed_parent = self.outputs / "sealed"
        result = self.batch(sealed_parent)  # 봉인 자리를 흉내 낸 임시 폴더(실제 봉인 묶음이 아니다)
        cwd = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, cwd)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = extract.main(["--run", str(result.run_dir.relative_to(self.root))])
        self.assertEqual((code, err.getvalue()), (0, ""))
        first, second = out.getvalue().splitlines()
        self.assertTrue(first.startswith("evaluation_extract-"))
        self.assertTrue((sealed_parent / first).is_dir())
        self.assertFalse((self.outputs / first).exists())
        for case in hf.dev20_cases(4):
            self.assertNotIn(case["case_id"], out.getvalue())
        self.assertNotIn("run_case-", out.getvalue())
        self.assertEqual(trace_log.loads(second)["infra_rerun"], 3)

    def test_sealed_place_reached_through_a_symlink_counts_as_sealed(self):
        result = self.batch(self.outputs / "sealed")
        alias = self.outputs / "alias"
        alias.symlink_to(self.outputs / "sealed", target_is_directory=True)
        run_id, _ = extract.extract(alias / result.run_dir.name, outputs=self.outputs, clock=self.clock,
                                    sleep=self.clock.sleep)
        self.assertTrue((self.outputs / "sealed" / run_id).is_dir())
        self.assertFalse((self.outputs / run_id).exists())  # 재실행 대상 목록이 outputs/ 아래로 새지 않는다

    def test_errors_give_exception_names_only(self):
        cwd = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, cwd)
        missing = self.outputs / "evaluate-260925100000"
        missing.mkdir(parents=True)
        for argv in (["--run", str(missing.relative_to(self.root))], ["--run", "outputs/score-260925100000"]):
            out, err = io.StringIO(), io.StringIO()
            with self.subTest(argv=argv), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(extract.main(argv), 1)
            self.assertEqual(out.getvalue(), "")
            self.assertRegex(err.getvalue(), r"^오류: 추출하지 못했다\([A-Za-z]+\)\n$")

    def test_malformed_lines_are_counted_not_trusted(self):
        lines = [None, {"execution_status": "FAILED", "errors": "x"}, {"execution_status": "FAILED",
                 "errors": [{"code": "NEW_CODE"}], "run_id": "run_case-260925100000", "case_id": "a", "mode": "full"}]
        counts = extract.summarize(lines)
        self.assertEqual((counts["lines"], counts["malformed"], counts["cause_codes"]["unknown"]), (3, 2, 1))
        self.assertEqual(extract.rerun_targets(lines), [])
        with self.assertRaises(extract.ExtractError):
            extract.summarize(lines, {"policy_version": "x"})


if __name__ == "__main__":
    unittest.main()
