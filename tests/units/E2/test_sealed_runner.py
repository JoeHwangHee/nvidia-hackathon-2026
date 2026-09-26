"""단위 E2(샌드박스 밖 실행기) 시험. 가짜 openshell(tests/units/F2/fake_openshell.py)과 임시 봉인 폴더(시험 안에서 만든 가짜
해시 목록·표본·cases.json)로 돈다. 실제 봉인 폴더·outputs/sealed/·openshell·NIM에는 닿지 않는다(모든 파일은 임시 폴더).

- (a) 해시 대조 실패 → 종료 2, outputs/ 무변경 (b) 목록 밖 파일(OS 메타데이터 파일) → 실패, 이름은 출력하지 않음
- (c) real_sealed 표본 읽기: 모드 freeform·full, 순서 seed rb1-order-v1로 고정된 순서, 사례 식별자가 표준 출력·오류에 없음,
  --conditions-extra 합치기, 채점기 read_conditions(봉인)를 지나는 실행 조건 입력 파일
- (d) holdout40 cases.json 읽기: 모드 checklist·agent·full, planned_cases가 파일의 네 키
- (e) 묶음 기록·실행 조건 입력 파일이 outputs/sealed/sealed_evaluate-{시각}/에 배타 생성되고 채점기 이름(BATCH_DOMAINS를
  monkeypatch)과 같음, N8(다른 부모에 같은 이름이 있으면 다음 초)
- (f) 인프라 실패 재실행(HTTP 503)이 같은 묶음 기록에 줄을 더하고 outputs/sealed/ 밖에는 아무것도 없음
- (g) 경계: 보조 파일 sandbox_exec의 import가 머리 주석 안, 옮겨 적은 정규식·NAT 파일 이름·임계값 규칙이 원본과 같음
- 사전 점검 실패·인자 오류·E1 봉인 보호 규칙
"""
import ast
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

import harness_fixtures as hf
from eval.scorer import __main__ as scorer
from tradesentry.cli import args
from tradesentry.contract import policy_load
from tradesentry.evaluation import batch_run, extract, nat_eval, sandbox_exec, sealed_runner
from tradesentry.runlog import cause_codes
from tradesentry.units import registry
from tradesentry.workflow import nat_wrap, orchestrate

REPO = Path(__file__).resolve().parents[3]
FAKE = REPO / "tests" / "units" / "F2" / "fake_openshell.py"
COMMIT = "0123456789abcdef0123456789abcdef01234567"
MANIFEST = {"code_version": {"git_commit": COMMIT, "dirty": False}, "files": []}
REAL_SNAPSHOT = "kcs_202201_202412_v2"
REAL_CASE_IDS = ["850431-CN-202403", "850450-JP-202411"]
HOLDOUT_CASES = hf.dev20_cases(3)
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SealedRunnerFixture:
    """임시 폴더: 가짜 openshell, 가짜 샌드박스 뿌리, 가짜 봉인 폴더와 해시 목록, outputs/ 부모."""

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
        self.sealed = self.root / "sealed_fake"
        self.manifest_file = self.root / "manifest_fake.json"
        self.write_sealed()
        env = {"PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}", "FAKE_OPENSHELL_ROOT": str(self.sandbox_root),
               "FAKE_OPENSHELL_SCENARIO": str(self.scenario_file), "FAKE_OPENSHELL_LOG": str(self.log_file),
               # 하위 프로세스에 넘어가면 안 되는 이름(가짜 값. 실제 키가 아니다). 봉인 폴더 변수는 존재하지 않는 곳
               "NVIDIA_API_KEY": "fake-placeholder", "TRADESENTRY_SEALED_DIR": str(self.root / "no_sealed")}
        for patcher in (mock.patch.dict(os.environ, env),
                        mock.patch.object(sandbox_exec, "code_version", lambda root=None: COMMIT)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def write_sealed(self) -> None:
        """가짜 봉인 폴더 네 파일과 그 해시 목록(자료 계약 §12.2 형식). 정답표는 내용을 보지 않는 자리표시다."""
        files = {
            "holdout40/input/cases.json": json.dumps({"schema_version": 2, "dataset": "holdout40", "snapshot_id": "holdout40",
                                                     "policy_version": "policy_v1", "cases": HOLDOUT_CASES}),
            "holdout40/answers/answers.json": json.dumps({"placeholder": True}),
            "real_sealed/sample-260926065820.json": json.dumps({"snapshot_id": REAL_SNAPSHOT, "policy_version": "policy_v1",
                                                               "cases": REAL_CASE_IDS}),
            "real_sealed/sample_seed.json": json.dumps({"placeholder": True}),
        }
        entries = []
        for name, text in files.items():
            path = self.sealed / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            entries.append({"dataset": name.split("/")[0], "file_name": name, "sha256": sha(text.encode("utf-8")),
                            "created_at": "2026-09-26T06:58:20+09:00", "created_by": "시험 생성 에이전트"})
        self.manifest_file.write_text(json.dumps({"schema_version": 2, "files": entries}), encoding="utf-8")

    def set_scenario(self, dataset: str, snapshot_id: str, policy_version: str, cases: dict,
                     manifest: dict | None = MANIFEST) -> None:
        versions = {"policy_version": policy_version, "rulebook_version": "RB-1", "snapshot_id": snapshot_id,
                    "grouping_version": sealed_runner.SEALED_GROUPING_VERSION, "code_version": COMMIT}
        self.scenario_file.write_text(json.dumps({"manifest": manifest, "versions": versions, "dataset": dataset,
                                                  "cases": cases}), encoding="utf-8")

    def settings(self, dataset: str, snapshot_id: str, policy_version: str = "policy_v1", **extra) -> sealed_runner.Settings:
        values = dict(dataset=dataset, sandbox="ts-official", snapshot_id=snapshot_id, policy_version=policy_version,
                      outputs=self.outputs, repo_root=REPO, manifest=self.manifest_file, sealed_root=self.sealed)
        values.update(extra)
        return sealed_runner.Settings(**values)

    def run_e2(self, settings: sealed_runner.Settings, cases: dict | None = None, **kwargs):
        self.set_scenario(settings.dataset, settings.snapshot_id, settings.policy_version, cases or {})
        clock = hf.FakeClock()
        out, err = io.StringIO(), io.StringIO()
        code = sealed_runner.run_sealed(settings, clock=clock, sleep=clock.sleep, out=out, err=err, **kwargs)
        return code, out.getvalue(), err.getvalue()

    def calls(self) -> list[dict]:
        if not self.log_file.exists():
            return []
        return [json.loads(line) for line in self.log_file.read_text(encoding="utf-8").splitlines()]

    def run_dir_from(self, out: str) -> Path:
        first = [line for line in out.splitlines() if line.startswith("outputs/")][0]
        return self.root / first

    def assert_no_case_ids(self, *texts: str) -> None:
        for text in texts:
            for case_id in REAL_CASE_IDS + [c["case_id"] for c in HOLDOUT_CASES]:
                self.assertNotIn(case_id, text)
            self.assertNotIn(str(self.root), text)  # 로컬 절대경로 없음(N13)


class HashRecheckTest(SealedRunnerFixture, unittest.TestCase):
    def test_tampered_file_exits_2_without_outputs(self):
        (self.sealed / "real_sealed/sample_seed.json").write_text("{}", encoding="utf-8")
        code, out, err = self.run_e2(self.settings("real_sealed", REAL_SNAPSHOT))
        self.assertEqual(code, 2)
        self.assertFalse(self.outputs.exists())
        self.assertIn("목록 파일 4개, 일치 3개, 불일치 1개, 목록 밖 항목 0개 → 불일치", out)
        self.assertIn("real_sealed/sample_seed.json", out)  # 목록 안 파일 이름은 적는다
        self.assertEqual(self.calls(), [])  # 샌드박스를 부르지 않았다
        self.assert_no_case_ids(out, err)

    def test_missing_listed_file_and_extra_os_file_exit_2(self):
        (self.sealed / "holdout40/answers/answers.json").unlink()
        (self.sealed / ".DS_Store").write_bytes(b"\x00\x01")
        os.symlink(self.root / "scenario.json", self.sealed / "real_sealed" / "link.json")
        code, out, err = self.run_e2(self.settings("holdout40", "holdout40"))
        self.assertEqual(code, 2)
        self.assertFalse(self.outputs.exists())
        self.assertIn("일치 3개, 불일치 1개, 목록 밖 항목 2개 → 불일치", out)
        self.assertNotIn(".DS_Store", out)  # 목록 밖 파일은 수만
        self.assertNotIn("link.json", out)

    def test_run_entry_is_the_pure_comparison(self):
        entries = json.loads(self.manifest_file.read_text(encoding="utf-8"))["files"]
        actual = sealed_runner.list_sealed_files(self.sealed)
        self.assertTrue(all(SHA_RE.match(v) for v in actual.values()))
        result = sealed_runner.run({"manifest": entries, "actual": actual})
        self.assertEqual(result, {"files": 4, "matched": 4, "mismatched": [], "extra": 0, "ok": True})
        with self.assertRaises(sealed_runner.SealedRunnerError):
            sealed_runner.run({"manifest": entries})
        with self.assertRaises(sealed_runner.SealedRunnerError):
            sealed_runner.load_manifest(self.root / "none.json")
        bad = {"schema_version": 2, "files": [dict(entries[0], file_name="../x.json")]}
        (self.root / "bad.json").write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaises(sealed_runner.SealedRunnerError):
            sealed_runner.load_manifest(self.root / "bad.json")


class RealSealedRunTest(SealedRunnerFixture, unittest.TestCase):
    OPERATOR = {"rulebook": "RB-1 동결 커밋 abc", "scorer_commit": "abc1234", "prose_patterns_commit": "abc1234",
                "sealed_hash_recheck": "일치", "sealed_provenance_check": "통과", "precheck": "통과",
                "a_grade": "조건 확인", "skill_call_success": "5/7",
                "sandbox": {"live_policy_sha256": "8a" * 32, "violation_tests_run": "openshell_violation_tests-260926011918"},
                "prescoring_checks": {"version_keys": "참", "mode_case_sets": "참", "concurrency_record": "참"}}

    def test_sample_read_modes_order_and_hygiene(self):
        # 운영자 파일 상대 경로의 기준은 저장소 폴더 → 임시 저장소 뿌리(정책 파일만 사본, 모델 설정은 실제 파일 경로)
        fake_repo = self.root / "repo"
        (fake_repo / "configs" / "openshell").mkdir(parents=True)
        shutil.copyfile(REPO / "configs" / "openshell" / "policy.yaml", fake_repo / "configs" / "openshell" / "policy.yaml")
        (fake_repo / "extra.json").write_text(json.dumps(self.OPERATOR), encoding="utf-8")
        # N8: 다른 부모(outputs/)에 첫 초의 이름이 있으면 다음 초로 넘어간다
        (self.outputs / "sealed_evaluate-260925100000").mkdir(parents=True)
        settings = self.settings("real_sealed", REAL_SNAPSHOT, conditions_extra="extra.json", repo_root=fake_repo,
                                 model_config=REPO / "configs" / "model" / "model.json")
        code, out, err = self.run_e2(settings)
        self.assertEqual(code, 0, err)
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("봉인 해시 대조: 목록 파일 4개, 일치 4개, 불일치 0개, 목록 밖 항목 0개 → 일치"))
        self.assertEqual(lines[1], "계획 사례 2건")
        self.assertRegex(lines[2], r"^outputs/sealed/sealed_evaluate-\d{12}$")
        self.assertNotEqual(lines[2], "outputs/sealed/sealed_evaluate-260925100000")
        self.assertIn("실행 상태: COMPLETED 4, FAILED 0, TIMEOUT 0, INVALID 0, BUDGET_EXCEEDED 0, 재실행 대상 0건·재실행 0건", out)
        self.assertIn("모드별 사례 집합 일치: 참, 순서 seed rb1-order-v1, 동시성 1", out)
        self.assertEqual(lines[-1], "종료 코드: 0")
        self.assert_no_case_ids(out, err)
        self.assertIn("합쳤다(키: a_grade, precheck, prescoring_checks.concurrency_record", err)
        run_dir = self.run_dir_from(out)
        stamp = run_dir.name.rsplit("-", 1)[1]
        batch = run_dir / f"evaluation_sealed_runner-{stamp}.jsonl"
        conditions = run_dir / f"run_conditions-{stamp}.json"
        self.assertEqual(sorted(p.name for p in run_dir.iterdir()), sorted([batch.name, conditions.name]))
        rows = hf.read_jsonl(batch)
        self.assertEqual(len(rows), 4)
        self.assertEqual({row["mode"] for row in rows}, {"freeform", "full"})
        self.assertEqual({row["dataset"] for row in rows}, {"real_sealed"})
        self.assertEqual([(row["case_id"], row["mode"]) for row in rows],
                         batch_run.plan_order(REAL_CASE_IDS, ["freeform", "full"], "rb1-order-v1"))
        self.assertTrue(all(hf.scorer_line_problems(row) == [] for row in rows))
        for row in rows:  # 사례 실행 폴더는 outputs/sealed/ 아래 형제이고 실행명을 --run-name으로 넘겼다
            self.assertTrue((self.outputs / "sealed" / row["run_id"] / f"runlog_run_record-{row['run_id'][-12:]}.json").is_file())
        execs = [c["argv"] for c in self.calls() if "run-case" in c["argv"]]
        self.assertEqual(len(execs), 4)
        for argv in execs:
            options = dict(zip(argv[9::2], argv[10::2]))
            self.assertEqual(argv[:4], ["sandbox", "exec", "-n", "ts-official"])
            self.assertEqual((options["--snapshot"], options["--policy"]), (REAL_SNAPSHOT, "policy_v1"))
            self.assertIn(options["--case"], REAL_CASE_IDS)
            self.assertRegex(options["--run-name"], r"^run_case-\d{12}$")
            # 봉인 묶음이면 run-case의 봉인 실행 경로 --sealed를 --run-name 뒤에 붙인다(FIX1)
            self.assertEqual(argv[-3:], ["--run-name", options["--run-name"], "--sealed"])
        self.assertTrue(all(c["env"] == [] for c in self.calls()))  # 키 변수·봉인 폴더 변수를 넘기지 않는다
        doc = json.loads(conditions.read_text(encoding="utf-8"), parse_float=Decimal)
        self.assertEqual(doc["dataset"], "real_sealed")
        self.assertEqual(doc["planned_modes"], ["freeform", "full"])
        self.assertEqual([c["case_id"] for c in doc["planned_cases"]], REAL_CASE_IDS)
        self.assertEqual(doc["planned_cases"][0], {"case_id": "850431-CN-202403", "hs6": "850431", "partner": "CN",
                                                   "month": "202403"})
        self.assertEqual(doc["order_seed"], "rb1-order-v1")
        self.assertEqual(doc["concurrency"], 1)
        self.assertEqual(doc["limits"]["wall_time_s"], 300)
        self.assertEqual(set(doc["sandbox"]), {"name", "policy_yaml_sha256", "live_policy_sha256", "violation_tests_run"})
        self.assertEqual(doc["sandbox"]["name"], "ts-official")
        self.assertEqual(doc["reproduce_evaluate"],
                         "python -m tradesentry.evaluation.sealed_runner --dataset real_sealed --sandbox ts-official "
                         f"--snapshot {REAL_SNAPSHOT} --policy policy_v1 --conditions-extra {settings.conditions_extra}")
        self.assertNotIn("nat_profile_summary", doc)
        self.assertTrue(doc["prescoring_checks"]["final_status"].startswith("참: 예정 실행 4건 가운데 줄 없는 조합 0건"))
        self.assertIn("순서 seed rb1-order-v1, 동시성 1", doc["prescoring_checks"]["seed_concurrency"])
        # 채점기가 봉인 묶음의 실행 조건 입력 파일로 받는 모양(채점기 코드는 그대로, 상수만 시험 안에서 monkeypatch)
        with mock.patch.dict(scorer.BATCH_DOMAINS, {"sealed_evaluate": "evaluation_sealed_runner"}):
            run_name = run_dir.name.rsplit("-", 1)[0]
            self.assertTrue((run_dir / f"{scorer.BATCH_DOMAINS[run_name]}-{stamp}.jsonl").is_file())
            read = scorer.read_conditions(run_dir / f"{scorer.CONDITIONS_DOMAIN}-{stamp}.json", sealed=True)
        self.assertEqual(read["dataset"], "real_sealed")
        self.assertEqual(sorted(p.name for p in self.outputs.iterdir()), ["sealed", "sealed_evaluate-260925100000"])
        for name, module in (("evaluate", None), ("sealed_evaluate", None)):
            self.assertEqual(extract.BATCH_DOMAINS[name], nat_eval.BATCH_DOMAINS[name])
        self.assertEqual(extract.BATCH_DOMAINS["sealed_evaluate"], sealed_runner.DOMAIN)
        self.assertEqual(extract.batch_file(run_dir), batch)  # 단위 E3가 E2 묶음 기록을 찾는다

    def test_sample_mismatch_with_arguments_is_refused_before_outputs(self):
        code, out, err = self.run_e2(self.settings("real_sealed", "kcs_202201_202412_v1"))
        self.assertEqual((code, self.outputs.exists()), (1, False))
        self.assertIn("SealedRunnerError", err)
        self.assert_no_case_ids(out, err)
        # 표본 파일이 둘이면 오류
        second = self.sealed / "real_sealed/sample-260926070000.json"
        second.write_text("{}", encoding="utf-8")
        entries = json.loads(self.manifest_file.read_text(encoding="utf-8"))
        entries["files"].append({"dataset": "real_sealed", "file_name": "real_sealed/sample-260926070000.json",
                                 "sha256": sha(b"{}"), "created_at": "2026-09-26T07:00:00+09:00", "created_by": "x"})
        self.manifest_file.write_text(json.dumps(entries), encoding="utf-8")
        code, out, err = self.run_e2(self.settings("real_sealed", REAL_SNAPSHOT))
        self.assertEqual((code, self.outputs.exists()), (1, False))

    def test_infra_failures_are_rerun_inside_the_sealed_folder(self):
        code, out, err = self.run_e2(self.settings("real_sealed", REAL_SNAPSHOT), cases={REAL_CASE_IDS[1]: "infra"})
        self.assertEqual(code, 0, err)
        self.assertIn("FAILED 4", out)  # 첫 실행 2 + 재실행 2(가짜는 재실행도 503)
        self.assertIn("재실행 대상 2건·재실행 2건", out)
        run_dir = self.run_dir_from(out)
        rows = hf.read_jsonl(run_dir / f"evaluation_sealed_runner-{run_dir.name[-12:]}.jsonl")
        self.assertEqual(len(rows), 6)
        infra = [r for r in rows if r["case_id"] == REAL_CASE_IDS[1]]
        self.assertEqual(len(infra), 4)
        self.assertTrue(all(cause_codes.infra_rerun_eligible(r["execution_status"], r["errors"]) for r in infra))
        self.assertEqual([p.name for p in self.outputs.iterdir()], ["sealed"])  # outputs/sealed/ 밖에는 아무것도 없다
        self.assertEqual(len([p for p in (self.outputs / "sealed").iterdir() if p.name.startswith("run_case-")]), 6)
        doc = json.loads((run_dir / f"run_conditions-{run_dir.name[-12:]}.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["prescoring_checks"]["final_status"],
                         "참: 예정 실행 4건 가운데 줄 없는 조합 0건, 인프라 실패 재실행(룰북 B5) 대상 2건·재실행 2건")
        self.assert_no_case_ids(out, err)

    def test_preflight_and_argument_failures_leave_no_outputs(self):
        settings = self.settings("real_sealed", REAL_SNAPSHOT)
        self.set_scenario("real_sealed", REAL_SNAPSHOT, "policy_v1", {},
                          manifest={"code_version": {"git_commit": "f" * 40, "dirty": False}})
        clock = hf.FakeClock()
        out, err = io.StringIO(), io.StringIO()
        code = sealed_runner.run_sealed(settings, clock=clock, sleep=clock.sleep, out=out, err=err)
        self.assertEqual((code, self.outputs.exists()), (1, False))
        self.assertIn("커밋과 다르다", err.getvalue())
        self.assertIn("python -m tradesentry.evaluation.sealed_runner", err.getvalue())
        with mock.patch.dict(os.environ, {"PATH": str(self.root / "empty")}):
            code = sealed_runner.run_sealed(settings, clock=clock, sleep=clock.sleep, out=io.StringIO(), err=io.StringIO())
        self.assertEqual((code, self.outputs.exists()), (1, False))
        for argv in (["--dataset", "dev20", "--sandbox", "x", "--snapshot", "s", "--policy", "p"],
                     ["--dataset", "holdout40", "--sandbox", "x", "--snapshot", "../s", "--policy", "p"],
                     ["--dataset", "holdout40", "--sandbox", "Bad Name", "--snapshot", "s", "--policy", "p"],
                     ["--dataset", "holdout40", "--sandbox", "x", "--snapshot", "s", "--policy", "p",
                      "--conditions-extra", "/abs/x.json"]):
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(sealed_runner.main(argv), 2)
        with self.assertRaises(sealed_runner.SealedRunnerError):  # 봉인 묶음이 아니면 사례 목록이 있어야 한다(리허설)
            sealed_runner._run_sealed(self.settings("dev20", "dev20", "dev-0.1"), None, clock, clock.sleep,
                                      io.StringIO(), io.StringIO())


class Holdout40RunTest(SealedRunnerFixture, unittest.TestCase):
    def test_cases_file_read_and_three_modes(self):
        code, out, err = self.run_e2(self.settings("holdout40", "holdout40"))
        self.assertEqual(code, 0, err)
        self.assertIn("계획 사례 3건", out)
        run_dir = self.run_dir_from(out)
        stamp = run_dir.name.rsplit("-", 1)[1]
        rows = hf.read_jsonl(run_dir / f"evaluation_sealed_runner-{stamp}.jsonl")
        self.assertEqual(len(rows), 9)
        self.assertEqual({row["mode"] for row in rows}, {"checklist", "agent", "full"})
        self.assertEqual([(r["case_id"], r["mode"]) for r in rows],
                         batch_run.plan_order([c["case_id"] for c in HOLDOUT_CASES], ["checklist", "agent", "full"],
                                              "rb1-order-v1"))
        doc = json.loads((run_dir / f"run_conditions-{stamp}.json").read_text(encoding="utf-8"), parse_float=Decimal)
        self.assertEqual(doc["planned_cases"], HOLDOUT_CASES)
        self.assertEqual(doc["planned_modes"], ["checklist", "agent", "full"])
        self.assertEqual(doc["reproduce_evaluate"], "python -m tradesentry.evaluation.sealed_runner --dataset holdout40 "
                                                    "--sandbox ts-official --snapshot holdout40 --policy policy_v1")
        self.assert_no_case_ids(out, err)
        execs = [c["argv"] for c in self.calls() if "run-case" in c["argv"]]
        self.assertEqual(len(execs), 9)
        for argv in execs:  # holdout40도 봉인 묶음이라 --sealed를 --run-name 뒤에 붙인다(FIX1)
            self.assertEqual((argv[9], argv[-3], argv[-1]), ("--snapshot", "--run-name", "--sealed"))
            self.assertRegex(argv[-2], r"^run_case-\d{12}$")
        # 정답표·gen·seed 파일은 열지 않았다(읽은 봉인 파일은 해시 대조의 전체 읽기와 cases.json뿐이라 파일로는 가릴 수 없어,
        # 사례 읽기 함수가 어느 이름을 읽는지 본다)
        with mock.patch.object(sealed_runner, "read_sealed_json", wraps=sealed_runner.read_sealed_json) as spy:
            entries = sealed_runner.load_manifest(self.manifest_file)
            sealed_runner.sealed_case_list("holdout40", self.sealed, entries, "holdout40", "policy_v1")
            sealed_runner.sealed_case_list("real_sealed", self.sealed, entries, REAL_SNAPSHOT, "policy_v1")
        self.assertEqual([call.args[2] for call in spy.call_args_list],
                         ["holdout40/input/cases.json", "real_sealed/sample-260926065820.json"])

    def test_missing_keys_skip_the_comparison_with_a_notice(self):
        """표본·cases.json에 snapshot_id·policy_version이 없으면 대조를 생략하고 표준 오류에 알림 한 줄(값 없음)."""
        sample = self.sealed / "real_sealed/sample-260926065820.json"
        sample.write_text(json.dumps({"cases": REAL_CASE_IDS}), encoding="utf-8")
        entries = json.loads(self.manifest_file.read_text(encoding="utf-8"))["files"]
        for entry in entries:
            if entry["file_name"] == "real_sealed/sample-260926065820.json":
                entry["sha256"] = sha(sample.read_bytes())
        err = io.StringIO()
        cases = sealed_runner.sealed_case_list("real_sealed", self.sealed, entries, REAL_SNAPSHOT, "policy_v1", err=err)
        self.assertEqual(len(cases), 2)
        self.assertEqual(err.getvalue().splitlines(), ["알림: 봉인 표본 파일에 snapshot_id가 없어 인자와 대조하지 않았다",
                                                        "알림: 봉인 표본 파일에 policy_version가 없어 인자와 대조하지 않았다"])
        self.assert_no_case_ids(err.getvalue())

    def test_wrong_snapshot_argument_is_refused(self):
        code, out, err = self.run_e2(self.settings("holdout40", "dev20"))
        self.assertEqual((code, self.outputs.exists()), (1, False))


class BatchRunSealedGuardTest(unittest.TestCase):
    """E1의 봉인 보호 규칙: sealed 인자와 자료 묶음·부모 자리가 맞아야 한다."""

    def test_check_spec_and_execute_batch_guards(self):
        cases = tuple(hf.dev20_cases(2))
        sealed_spec = batch_run.BatchSpec("holdout40", cases, ("checklist",), "s", dict(hf.VERSIONS))
        dev_spec = batch_run.BatchSpec("dev20", cases, ("checklist",), "s", dict(hf.VERSIONS))
        batch_run.check_spec(sealed_spec, sealed=True)
        batch_run.check_spec(dev_spec)
        with self.assertRaises(batch_run.BatchError):
            batch_run.check_spec(sealed_spec)
        with self.assertRaises(batch_run.BatchError):
            batch_run.check_spec(dev_spec, sealed=True)
        with tempfile.TemporaryDirectory() as tmp:
            outputs = Path(tmp) / "outputs"
            runner = hf.FakeRunner(hf.FakeClock())
            with self.assertRaises(batch_run.BatchError):  # 봉인 실행인데 부모가 outputs/
                batch_run.execute_batch(sealed_spec, runner, parent=outputs, other_parent=outputs / "sealed", sealed=True,
                                        run_name="sealed_evaluate", domain="evaluation_sealed_runner")
            with self.assertRaises(batch_run.BatchError):  # 이름 규칙 밖 실행 이름
                batch_run.execute_batch(sealed_spec, runner, parent=outputs / "sealed", other_parent=outputs, sealed=True,
                                        run_name="Sealed-Evaluate", domain="evaluation_sealed_runner")
            self.assertFalse(outputs.exists())


class AuxiliaryBoundaryTest(unittest.TestCase):
    """보조 파일 sandbox_exec과 E2가 옮겨 적은 값이 원본과 같다(경계 시험 (g))."""

    def test_sandbox_exec_imports_stay_inside_its_header(self):
        path = REPO / "src" / "tradesentry" / "evaluation" / "sandbox_exec.py"
        source = path.read_text(encoding="utf-8")
        allowed = registry.header_allowed_imports(registry.read_header(source))
        self.assertEqual(allowed, ["표준 라이브러리", "tradesentry.contract", "tradesentry.runlog",
                                   "tradesentry.evaluation.batch_run"])
        names = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Import):
                names |= {alias.name for alias in node.names}
            elif isinstance(node, ast.ImportFrom):
                names |= {f"{node.module}.{alias.name}" for alias in node.names}
        repo_names = {n for n in names if n.startswith(("tradesentry", "eval"))}
        for name in repo_names:
            self.assertTrue(any(name == a or name.startswith(a + ".") for a in allowed), name)
        self.assertEqual(registry.AUXILIARY_FILES, {"src/tradesentry/evaluation/sandbox_exec.py": "E2"})

    def test_copied_values_match_their_sources(self):
        self.assertEqual(sandbox_exec.PROFILE_FILES, nat_wrap.PROFILE_FILES)
        self.assertEqual(sandbox_exec.NAT_DOMAIN, nat_wrap.DOMAIN)
        for mine, theirs in ((sandbox_exec.SNAPSHOT_ID_RE, args.SNAPSHOT_ID_RE), (sandbox_exec.POLICY_VERSION_RE, args.POLICY_VERSION_RE),
                             (sandbox_exec.CASE_RE, args.CASE_RE), (sandbox_exec.RUN_NAME_RE, args.RUN_NAME_RE),
                             (sandbox_exec.PATH_HINT_RE, args.PATH_HINT_RE),
                             (sealed_runner.BAD_PATH_START_RE, args.CONDITIONS_EXTRA_BAD_START_RE)):
            self.assertEqual(mine.pattern, theirs.pattern)
        self.assertEqual(sandbox_exec.MAX_LENGTH, args.MAX_LENGTH)
        for version in ("policy_v1", "dev-0.1"):
            policy = policy_load.load_policy(version)
            self.assertEqual(sealed_runner.policy_thresholds(policy), orchestrate.policy_thresholds(policy))
        for value in ("a/b.json", "x.json"):
            self.assertTrue(sealed_runner.relative_path_piece(value))
        for value in ("", "/abs", "~" + "/x", "C:\\x", "a b", "a\tb"):
            self.assertFalse(sealed_runner.relative_path_piece(value), value)
        self.assertEqual(sealed_runner.PROGRAM, "python -m tradesentry.evaluation.sealed_runner")
        self.assertEqual((sealed_runner.RUN_NAME, sealed_runner.DOMAIN, sealed_runner.SEALED_ORDER_SEED),
                         ("sealed_evaluate", "evaluation_sealed_runner", "rb1-order-v1"))
        self.assertNotEqual(sealed_runner.SEALED_ORDER_SEED, "dev-order-v1")  # 개발용 seed와 다르다


if __name__ == "__main__":
    unittest.main()
