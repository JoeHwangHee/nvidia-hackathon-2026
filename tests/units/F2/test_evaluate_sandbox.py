"""조립 작업 AS3: evaluate의 샌드박스 백엔드(dispatch.SandboxCaseRunner·sandbox_preflight) 시험. 가짜 openshell
(fake_openshell.py)을 PATH 앞에 두고 실제 하위 프로세스로 부른다. 실제 openshell·샌드박스·NIM은 쓰지 않는다.

- 사례마다: 묶음(E1)이 호스트 쪽 outputs/run_case-{시각}/을 확보 → exec으로 샌드박스 안 run-case에 --run-name으로 그 실행명 →
  받기 전 확인 → 같은 부모 아래 임시 폴더로 받기 → os.lstat 검사 → 빈 사례 폴더로 옮기기 → 실행 결과 기록(MT5 결정 기록 ④·⑯)
- 받지 못한 사례는 FAILED 줄(CODE_ERROR, harness:{예외 이름})로 분모에 남는다. 링크를 받으면 링크만 지우고 격리한다
- 사전 점검(실행 폴더를 만들기 전): openshell 없음, 이미지 기록 없음·dirty·커밋 불일치
- 하위 프로세스 환경에 키 변수와 봉인 폴더 변수가 없다(값이 아니라 이름이 있는지만 본다)
모든 파일은 임시 폴더에 쓴다(저장소의 outputs/와 outputs/sealed/에 닿지 않는다).
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

import harness_fixtures as hf
from tradesentry.cli import dispatch
from tradesentry.evaluation import batch_run
from tradesentry.runlog import cause_codes

FAKE = Path(__file__).resolve().parent / "fake_openshell.py"
COMMIT = "0123456789abcdef0123456789abcdef01234567"
VERSIONS = {**hf.VERSIONS, "code_version": COMMIT}
MANIFEST = {"code_version": {"git_commit": COMMIT, "dirty": False}, "files": []}
CASES = hf.dev20_cases(3)
ORIGINAL_BACKEND = dispatch.EVALUATE_BACKEND  # 시험이 바꿔 끼우기 전의 기본값


def call(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = dispatch.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class FakeOpenShell:
    """임시 폴더에 가짜 openshell과 가짜 샌드박스 뿌리를 만든다."""

    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.outputs = self.root / "outputs"
        self.sandbox_root = self.root / "fake_sandbox"
        self.sandbox_root.mkdir()
        (self.sandbox_root / "host_secret.txt").write_text("not a secret", encoding="utf-8")
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        program = bin_dir / "openshell"
        program.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{FAKE}" "$@"\n', encoding="utf-8")
        program.chmod(0o755)
        self.scenario_file = self.root / "scenario.json"
        self.log_file = self.root / "openshell_log.jsonl"
        self.set_scenario({})
        env = {"PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}", "FAKE_OPENSHELL_ROOT": str(self.sandbox_root),
               "FAKE_OPENSHELL_SCENARIO": str(self.scenario_file), "FAKE_OPENSHELL_LOG": str(self.log_file),
               # 하위 프로세스에 넘어가면 안 되는 이름(가짜 값. 실제 키가 아니다)
               "NVIDIA_API_KEY": "fake-placeholder", "TRADESENTRY_SEALED_DIR": str(self.root / "no_sealed")}
        for patcher in (mock.patch.dict(os.environ, env), mock.patch.object(dispatch, "OUTPUT_PARENT", self.outputs)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def set_scenario(self, cases: dict, manifest: dict | None = MANIFEST) -> None:
        self.scenario_file.write_text(json.dumps({"manifest": manifest, "versions": VERSIONS, "dataset": "dev20",
                                                  "cases": cases}), encoding="utf-8")

    def calls(self) -> list[dict]:
        if not self.log_file.exists():
            return []
        return [json.loads(line) for line in self.log_file.read_text(encoding="utf-8").splitlines()]

    def run_batch(self, cases: dict, modes=("checklist",)) -> tuple[batch_run.BatchResult, dispatch.SandboxCaseRunner]:
        self.set_scenario(cases)
        runner = dispatch.SandboxCaseRunner("ts-scored", exec_timeout_s=420)
        spec = batch_run.BatchSpec(dataset="dev20", cases=tuple(CASES), modes=tuple(modes), order_seed="s",
                                   versions=dict(VERSIONS))
        clock = hf.FakeClock()
        result = batch_run.execute_batch(spec, runner, parent=self.outputs, other_parent=self.outputs / "sealed",
                                         clock=clock, sleep=clock.sleep)
        return result, runner


class SandboxRunnerTest(FakeOpenShell, unittest.TestCase):
    def test_completed_and_failed_runs_come_back_with_their_own_records(self):
        result, runner = self.run_batch({CASES[1]["case_id"]: "failed"})
        lines = hf.read_jsonl(result.batch_file)
        self.assertEqual(len(lines), 3)
        by_case = {line["case_id"]: line for line in lines}
        self.assertEqual(by_case[CASES[0]["case_id"]]["execution_status"], "COMPLETED")
        failed = by_case[CASES[1]["case_id"]]
        self.assertEqual(failed["execution_status"], "FAILED")
        self.assertEqual(failed["errors"][0]["code"], cause_codes.PROVIDER_HTTP_4XX)  # 샌드박스 기록의 실제 원인
        self.assertTrue(all(hf.scorer_line_problems(line) == [] for line in lines))
        for line in lines:
            folder = self.outputs / line["run_id"]
            stamp = line["run_id"].rsplit("-", 1)[1]
            names = sorted(p.name for p in folder.iterdir())
            self.assertIn(f"runlog_run_record-{stamp}.json", names)
            self.assertIn(f"workflow_nat_wrap-{stamp}", names)
            self.assertNotIn(line["run_id"], names)  # 겹친 층이 없다
        self.assertEqual([p.name for p in self.outputs.iterdir() if p.name.startswith(".")], [])  # 임시 폴더를 지웠다
        self.assertEqual(runner.incidents, [])

    def test_command_shapes_and_child_environment(self):
        result, _ = self.run_batch({})
        calls = self.calls()
        run_ids = [line["run_id"] for line in hf.read_jsonl(result.batch_file)]
        execs = [c["argv"] for c in calls if "run-case" in c["argv"]]
        self.assertEqual(len(execs), 3)
        for argv, run_id in zip(execs, run_ids):
            self.assertEqual(argv[:7], ["sandbox", "exec", "-n", "ts-scored", "--timeout", "420", "--"])
            self.assertEqual(argv[7:9], ["/opt/tradesentry/bin/tradesentry", "run-case"])
            options = dict(zip(argv[9::2], argv[10::2]))
            self.assertEqual(options["--run-name"], run_id)  # 호스트가 확보한 실행명을 넘긴다(사용자 결정 10)
            self.assertEqual((options["--snapshot"], options["--policy"], options["--mode"]), ("dev20", "dev-0.1",
                                                                                                "checklist"))
        checks = [c["argv"] for c in calls if "sh" in c["argv"]]
        self.assertEqual(checks[0][-1], f"test -d /sandbox/outputs/{run_ids[0]} && ! test -L "
                                        f"/sandbox/outputs/{run_ids[0]} && ! test -L /sandbox/outputs")
        downloads = [c["argv"] for c in calls if c["argv"][:2] == ["sandbox", "download"]]
        self.assertEqual(len(downloads), 3)
        for argv in downloads:
            self.assertEqual(argv[2:4], ["ts-scored", f"/sandbox/outputs/{argv[3].rsplit('/', 1)[1]}"])
            self.assertTrue(Path(argv[4]).name.startswith(".download-"))
            self.assertEqual(Path(argv[4]).parent, self.outputs)  # 같은 부모 아래 임시 폴더
        self.assertTrue(all(c["env"] == [] for c in calls))  # 키 변수·봉인 폴더 변수를 넘기지 않는다

    def test_failures_to_bring_back_a_record_stay_in_the_denominator(self):
        plan = {CASES[0]["case_id"]: "crash", CASES[1]["case_id"]: "exit3", CASES[2]["case_id"]: "norecord"}
        result, _ = self.run_batch(plan)
        by_case = {line["case_id"]: line for line in hf.read_jsonl(result.batch_file)}
        details = {case: line["errors"][0]["detail"] for case, line in by_case.items()}
        self.assertEqual(details, {CASES[0]["case_id"]: "harness:SandboxOutputMissing",
                                   CASES[1]["case_id"]: "harness:SandboxExecFailed",
                                   CASES[2]["case_id"]: "harness:RunRecordMissing"})
        for line in by_case.values():
            self.assertEqual((line["execution_status"], line["errors"][0]["code"]), ("FAILED", cause_codes.CODE_ERROR))

    def test_download_problems_are_refused(self):
        plan = {CASES[0]["case_id"]: "link", CASES[1]["case_id"]: "layered", CASES[2]["case_id"]: "download_fail"}
        result, runner = self.run_batch(plan)
        by_case = {line["case_id"]: line for line in hf.read_jsonl(result.batch_file)}
        self.assertEqual({case: line["errors"][0]["detail"] for case, line in by_case.items()},
                         {CASES[0]["case_id"]: "harness:DownloadRejected",
                          CASES[1]["case_id"]: "harness:DownloadRejected",
                          CASES[2]["case_id"]: "harness:DownloadFailed"})
        for line in by_case.values():
            self.assertEqual(list((self.outputs / line["run_id"]).iterdir()), [])  # 옮기지 않았다
        self.assertEqual([p for p in self.outputs.iterdir() if p.name.startswith(".download-")], [])  # 임시 폴더를 남기지 않는다
        quarantined = [p for p in self.outputs.iterdir() if p.name.startswith(".quarantine-")]
        self.assertEqual(len(quarantined), 2)  # 링크 사례와 겹친 층 사례
        leftovers = [p for q in quarantined for p in q.rglob("*") if p.is_symlink()]
        self.assertEqual(leftovers, [])  # 링크는 지웠다(대상 파일은 그대로다)
        self.assertTrue((self.sandbox_root / "host_secret.txt").exists())
        self.assertEqual(len(runner.incidents), 2)
        link_case = by_case[CASES[0]["case_id"]]
        self.assertTrue(any(link_case["run_id"] in incident for incident in runner.incidents))
        self.assertTrue(any("겹친 층" in incident for incident in runner.incidents))
        for incident in runner.incidents:
            self.assertNotIn(str(self.root), incident)  # 사건 문장에 로컬 절대경로가 없다

    def test_special_files_are_refused(self):
        result, _ = self.run_batch({CASES[0]["case_id"]: "fifo"})
        line = [x for x in hf.read_jsonl(result.batch_file) if x["case_id"] == CASES[0]["case_id"]][0]
        self.assertEqual(line["errors"][0]["detail"], "harness:DownloadRejected")

    def test_target_must_be_the_reserved_empty_folder(self):
        self.set_scenario({})
        runner = dispatch.SandboxCaseRunner("ts-scored", exec_timeout_s=420)
        folder = self.outputs / "run_case-260925100000"
        folder.mkdir(parents=True)
        (folder / "already.txt").write_text("x", encoding="utf-8")
        call_ = batch_run.CaseCall(run_id=folder.name, stamp="260925100000", run_dir=folder, case=dict(CASES[0]),
                                   mode="checklist", dataset="dev20", versions=dict(VERSIONS))
        with self.assertRaises(dispatch.DownloadMoveConflict):
            runner(call_)

    def test_values_sent_to_the_sandbox_are_rechecked(self):
        runner = dispatch.SandboxCaseRunner("ts-scored", exec_timeout_s=420)
        folder = self.outputs / "run_case-260925100000"
        folder.mkdir(parents=True)
        for case_id, run_id in (("850431-XA-202401; rm", folder.name), (CASES[0]["case_id"], "run_case-260925100001"),
                                (CASES[0]["case_id"], "detect-260925100000")):
            call_ = batch_run.CaseCall(run_id=run_id, stamp="260925100000", run_dir=folder,
                                       case={**CASES[0], "case_id": case_id}, mode="checklist", dataset="dev20",
                                       versions=dict(VERSIONS))
            with self.subTest(case_id=case_id, run_id=run_id), self.assertRaises(dispatch.WiringError):
                runner(call_)
        self.assertEqual(self.calls(), [])  # 샌드박스를 부르기 전에 멈췄다


class PreflightTest(FakeOpenShell, unittest.TestCase):
    ARGV = ["evaluate", "--snapshot", "dev20", "--policy", "dev-0.1", "--mode", "checklist"]

    def setUp(self):
        super().setUp()
        cases_file = self.root / "cases.json"
        cases_file.write_text(json.dumps({"dataset": "dev20", "snapshot_id": "dev20", "cases": CASES}),
                              encoding="utf-8")
        for patcher in (mock.patch.dict(dispatch.EVALUATE_CASE_LISTS, {"dev20": cases_file}),
                        mock.patch.object(dispatch, "evaluate_versions", lambda request, dataset: dict(VERSIONS)),
                        mock.patch.object(dispatch, "EVALUATE_BACKEND", dispatch.SANDBOX_BACKEND)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_default_backend_is_the_sandbox(self):
        self.assertEqual(ORIGINAL_BACKEND, dispatch.SANDBOX_BACKEND)

    def test_sandbox_batch_writes_sandbox_conditions(self):
        code, out, err = call(self.ARGV)
        self.assertEqual(code, 0, err)
        batch_line, conditions_line = out.splitlines()
        doc = json.loads((self.root / conditions_line).read_text(encoding="utf-8"), parse_float=Decimal)
        self.assertEqual(doc["sandbox"]["name"], "ts-scored")
        self.assertRegex(doc["sandbox"]["policy_yaml_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(doc["reproduce_evaluate"], "tradesentry evaluate --snapshot dev20 --policy dev-0.1 --mode checklist")
        self.assertEqual(doc["planned_modes"], ["checklist"])
        self.assertEqual(len(hf.read_jsonl(self.root / batch_line)), 3)
        self.assertIn("스모크 묶음", err)

    def test_preflight_refusals_leave_no_outputs(self):
        cases = {
            "manifest 없음": (None, "코드 커밋을 읽지 못했다"),
            "dirty": ({"code_version": {"git_commit": COMMIT, "dirty": True}}, "dirty"),
            "dirty 모름": ({"code_version": {"git_commit": COMMIT, "dirty": None}}, "dirty"),
            "커밋 다름": ({"code_version": {"git_commit": "f" * 40, "dirty": False}}, "커밋과 다르다"),
            "커밋 모양": ({"code_version": {"git_commit": "HEAD", "dirty": False}}, "코드 커밋을 읽지 못했다"),
        }
        for name, (manifest, text) in cases.items():
            with self.subTest(name):
                self.set_scenario({}, manifest)
                code, out, err = call(self.ARGV)
                self.assertEqual((code, out), (1, ""))
                self.assertIn(text, err)
                self.assertFalse(self.outputs.exists())

    def test_missing_openshell_is_refused_before_outputs(self):
        with mock.patch.dict(os.environ, {"PATH": str(self.root / "empty")}):
            code, out, err = call(self.ARGV)
        self.assertEqual((code, out), (1, ""))
        self.assertIn("openshell 명령을 찾지 못했다", err)
        self.assertFalse(self.outputs.exists())


if __name__ == "__main__":
    unittest.main()
