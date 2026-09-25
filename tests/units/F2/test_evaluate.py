"""evaluate 배선(로드맵 MT7 첫 PR, 조립 작업 AS3) 시험. 가짜 사례 실행 함수(tests/harness_fixtures.py FakeRunner)를 호스트
백엔드 자리(dispatch.host_case_runner)에 끼워 명령 층만 본다. 실제 조립(run_case_in)으로 도는 시험은
test_evaluate_scorer.py, 샌드박스 백엔드는 test_evaluate_sandbox.py에 있다.

- 사용자 결정 12(가): --mode를 주지 않으면 그 묶음의 정해진 모드 전부(E1 PLANNED_MODES)를 한 묶음으로, 주면 그 모드 하나만
  (스모크: 실행 조건 입력 파일의 planned_modes가 그 모드 하나, reproduce_evaluate에 --mode, 표준 오류 알림) 돈다
- 사용자 결정 10(나): --run-name이면 그 이름의 묶음 폴더를 이미 있으면 실패하는 방식으로 만든다
- 자료 묶음을 모르거나(봉인 묶음 포함) 사례 목록 자리가 없으면 실행 폴더를 만들기 전에 끝난다
모든 파일은 임시 폴더에 쓴다.
"""
import contextlib
import io
import json
import os
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

import harness_fixtures as hf
from tradesentry.cli import dispatch
from tradesentry.evaluation import batch_run

ARGV = ["evaluate", "--snapshot", "dev20", "--policy", "dev-0.1"]


def call(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = dispatch.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class EvaluateTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        cwd = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, cwd)
        self.cases_file = self.root / "cases.json"
        self.cases = hf.dev20_cases(2)
        self.cases_file.write_text(json.dumps({"schema_version": 1, "dataset": "dev20", "snapshot_id": "dev20",
                                               "cases": self.cases}), encoding="utf-8")
        self.runner = hf.FakeRunner()
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(dispatch, "EVALUATE_BACKEND", dispatch.HOST_BACKEND))
        stack.enter_context(mock.patch.object(dispatch, "host_case_runner", self.runner))
        stack.enter_context(mock.patch.object(dispatch, "evaluate_versions", lambda request, dataset: dict(hf.VERSIONS)))
        stack.enter_context(mock.patch.dict(dispatch.EVALUATE_CASE_LISTS, {"dev20": self.cases_file}))
        self.addCleanup(stack.close)

    def conditions(self, line: str) -> dict:
        return json.loads((self.root / line).read_text(encoding="utf-8"), parse_float=Decimal)

    def test_without_mode_every_planned_mode_runs_in_one_batch(self):
        code, out, err = call(ARGV)
        self.assertEqual(code, 0, err)
        self.assertNotIn("스모크 묶음", err)
        self.assertIn("호스트 백엔드", err)
        batch_line, conditions_line = out.splitlines()
        self.assertRegex(batch_line, r"^outputs/evaluate-\d{12}/evaluation_batch_run-\d{12}\.jsonl$")
        self.assertRegex(conditions_line, r"^outputs/evaluate-\d{12}/run_conditions-\d{12}\.json$")
        lines = hf.read_jsonl(self.root / batch_line)
        self.assertEqual(sorted((x["case_id"], x["mode"]) for x in lines),
                         sorted((c["case_id"], m) for c in self.cases for m in hf.DEV20_MODES))
        self.assertTrue(all(hf.scorer_line_problems(x) == [] for x in lines))
        doc = self.conditions(conditions_line)
        self.assertEqual(doc["planned_modes"], list(batch_run.PLANNED_MODES["dev20"]))  # 사용자 결정 12(가)
        self.assertEqual(doc["policy_detection_thresholds"], [30, 10])  # configs/policy_dev.json(dev-0.1)
        self.assertEqual(doc["order_seed"], dispatch.DEV_ORDER_SEED)
        self.assertEqual(doc["concurrency"], 1)
        self.assertEqual(doc["nat_profile_summary"]["runs"], 6)
        self.assertEqual(doc["limits"]["wall_time_s"], 300)
        self.assertEqual(doc["reproduce_evaluate"], "tradesentry evaluate --snapshot dev20 --policy dev-0.1")
        self.assertNotIn("sandbox", doc)  # 호스트 백엔드는 샌드박스 정보를 적지 않는다(점수표 근거가 아니다)

    def test_one_mode_is_a_smoke_batch(self):
        code, out, err = call(ARGV + ["--mode", "full"])
        self.assertEqual(code, 0, err)
        self.assertIn("스모크 묶음", err)
        batch_line, conditions_line = out.splitlines()
        self.assertEqual({x["mode"] for x in hf.read_jsonl(self.root / batch_line)}, {"full"})
        doc = self.conditions(conditions_line)
        self.assertEqual(doc["planned_modes"], ["full"])
        self.assertEqual(doc["reproduce_evaluate"], "tradesentry evaluate --snapshot dev20 --policy dev-0.1 --mode full")

    def test_run_name_is_the_batch_folder(self):
        code, out, err = call(ARGV + ["--mode", "checklist", "--run-name", "evaluate-260925100000"])
        self.assertEqual(code, 0, err)
        self.assertTrue(out.splitlines()[0].startswith("outputs/evaluate-260925100000/evaluation_batch_run-260925100000"))
        self.assertTrue((self.root / "outputs" / "evaluate-260925100000" / "run_conditions-260925100000.json").is_file())
        code, out, err = call(ARGV + ["--mode", "checklist", "--run-name", "evaluate-260925100000"])
        self.assertEqual((code, out), (1, ""))
        self.assertIn("실행명을 확보하지 못했다", err)
        self.assertEqual(len([p for p in (self.root / "outputs").iterdir() if p.name.startswith("evaluate-")]), 1)

    def test_run_name_taken_in_the_sealed_parent_is_refused(self):
        (self.root / "outputs" / "sealed" / "evaluate-260925100000").mkdir(parents=True)
        code, out, err = call(ARGV + ["--run-name", "evaluate-260925100000"])
        self.assertEqual((code, out), (1, ""))
        self.assertIn("outputs/sealed/에 이미 있다", err)
        self.assertFalse((self.root / "outputs" / "evaluate-260925100000").exists())

    def test_unknown_or_sealed_dataset_or_missing_case_list_fails_before_outputs(self):
        for argv, text in ((["evaluate", "--snapshot", "holdout40", "--policy", "dev-0.1"], "자료 묶음을 모른다"),
                           (["evaluate", "--snapshot", "real_sealed", "--policy", "dev-0.1"], "자료 묶음을 모른다"),
                           (["evaluate", "--snapshot", "controlled_fixture_v0", "--policy", "dev-0.1", "--mode", "full"],
                            "사례 목록 자리를 모르거나"),
                           (["evaluate", "--snapshot", "kcs_202201_202412_v2", "--policy", "dev-0.1"], "DT7"),
                           (["evaluate", "--snapshot", "dev20", "--policy", "policy_v9", "--mode", "full"],
                            "묶음 입력이 규칙에 맞지 않는다")):
            with self.subTest(argv=argv):
                code, out, err = call(argv)
                self.assertEqual((code, out), (1, ""))
                self.assertIn(text, err)
        with mock.patch.dict(dispatch.EVALUATE_DATASETS, {"holdout40": "holdout40"}):  # 표에 잘못 들어가도 거부한다
            code, out, err = call(["evaluate", "--snapshot", "holdout40", "--policy", "dev-0.1"])
            self.assertEqual((code, out), (1, ""))
            self.assertIn("봉인 묶음은 샌드박스 밖 실행기가 돌린다", err)
        self.cases_file.write_text(json.dumps({"dataset": "dev20", "snapshot_id": "other", "cases": self.cases}))
        code, _, err = call(ARGV)
        self.assertEqual(code, 1)
        self.assertIn("사례 목록을 읽지 못했다(ValueError)", err)
        self.assertFalse((self.root / "outputs").exists())
        self.assertEqual(self.runner.calls, [])

    def test_unknown_backend_is_a_wiring_error(self):
        with mock.patch.object(dispatch, "EVALUATE_BACKEND", "cloud"):
            code, out, err = call(ARGV)
        self.assertEqual((code, out), (4, ""))
        self.assertIn("백엔드", err)
        self.assertFalse((self.root / "outputs").exists())


if __name__ == "__main__":
    unittest.main()
