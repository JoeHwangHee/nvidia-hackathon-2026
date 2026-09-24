"""evaluate 배선(로드맵 MT7 첫 PR, 단위 F2의 evaluate 항목) 시험.

- run-case가 아직 자리표시면 evaluate는 실행 폴더를 만들기 전에 분명한 오류와 종료 코드 1로 끝난다(3이 아니다: 3은
  자리표시 항목에만 쓰고, 처리 함수가 3을 돌려주면 배선 계약 위반 4가 된다).
- run-case 자리와 사례 실행 함수·버전 키 함수를 대역으로 채우면 E1 → E4 → 실행 조건 입력 파일까지 돈다(임시 폴더에서,
  가짜 사례 실행 함수로. 실제 run-case는 로드맵 AS2가 만든다).
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

ARGV = ["evaluate", "--snapshot", "dev20", "--policy", "dev-0.1", "--mode", "full"]


def call(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = dispatch.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def wired_run_case(request):  # run-case 자리를 채운 대역(부르지 않는다)
    raise AssertionError("evaluate는 run-case 처리 함수를 직접 부르지 않는다")


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

    def wired(self):
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.dict(dispatch.HANDLERS, {"run-case": wired_run_case}))
        stack.enter_context(mock.patch.object(dispatch, "EVALUATE_CASE_RUNNER", hf.FakeRunner()))
        stack.enter_context(mock.patch.object(dispatch, "EVALUATE_VERSIONS", lambda request, dataset: dict(hf.VERSIONS)))
        stack.enter_context(mock.patch.dict(dispatch.EVALUATE_CASE_LISTS, {"dev20": self.cases_file}))
        self.addCleanup(stack.close)

    def test_unwired_run_case_gives_a_clear_failure_without_outputs(self):
        self.assertIs(dispatch.HANDLERS["evaluate"], dispatch._evaluate)
        self.assertIs(dispatch.HANDLERS["run-case"], dispatch._not_wired)
        code, out, err = call(ARGV)
        self.assertEqual((code, out), (1, ""))
        self.assertIn("tradesentry evaluate는 사례 실행(run-case)이 아직 조립되지 않아 돌 수 없다", err)
        self.assertIn("AS3", err)
        self.assertFalse((self.root / "outputs").exists())

    def test_wired_path_writes_batch_and_run_conditions(self):
        self.wired()
        code, out, err = call(ARGV)
        self.assertEqual((code, err), (0, ""), err)
        batch_line, conditions_line = out.splitlines()
        self.assertRegex(batch_line, r"^outputs/evaluate-\d{12}/evaluation_batch_run-\d{12}\.jsonl$")
        self.assertRegex(conditions_line, r"^outputs/evaluate-\d{12}/run_conditions-\d{12}\.json$")
        lines = hf.read_jsonl(self.root / batch_line)
        self.assertEqual(sorted(x["case_id"] for x in lines), sorted(c["case_id"] for c in self.cases))
        self.assertTrue(all(hf.scorer_line_problems(x) == [] for x in lines))
        doc = json.loads((self.root / conditions_line).read_text(encoding="utf-8"), parse_float=Decimal)
        self.assertEqual(doc["planned_modes"], ["full"])  # 지금 명령 표: --mode 한 값(AS3이 모드 목록 방식을 정한다)
        self.assertEqual(doc["policy_detection_thresholds"], [30, 10])  # configs/policy_dev.json(dev-0.1)
        self.assertEqual(doc["order_seed"], dispatch.DEV_ORDER_SEED)
        self.assertEqual(doc["nat_profile_summary"]["runs"], 2)
        self.assertEqual(doc["limits"]["wall_time_s"], 300)

    def test_unknown_dataset_or_missing_case_list_fails_before_outputs(self):
        self.wired()
        for argv, text in ((["evaluate", "--snapshot", "holdout40", "--policy", "dev-0.1", "--mode", "full"],
                            "자료 묶음을 모른다"),
                           (["evaluate", "--snapshot", "controlled_fixture_v0", "--policy", "dev-0.1", "--mode", "full"],
                            "사례 목록 자리를 모르거나"),
                           (["evaluate", "--snapshot", "dev20", "--policy", "policy_v9", "--mode", "full"],
                            "묶음 입력이 규칙에 맞지 않는다")):
            with self.subTest(argv=argv):
                code, out, err = call(argv)
                self.assertEqual((code, out), (1, ""))
                self.assertIn(text, err)
        self.cases_file.write_text(json.dumps({"dataset": "dev20", "snapshot_id": "other", "cases": self.cases}))
        code, _, err = call(ARGV)
        self.assertEqual(code, 1)
        self.assertIn("사례 목록을 읽지 못했다(ValueError)", err)
        self.assertFalse((self.root / "outputs").exists())


if __name__ == "__main__":
    unittest.main()
