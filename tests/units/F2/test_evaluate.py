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
from tradesentry.dal import query
from tradesentry.evaluation import batch_run

ARGV = ["evaluate", "--snapshot", "dev20", "--policy", "dev-0.1"]
ORIGINAL_PACING = dispatch.evaluate_pacing
REPO = Path(__file__).resolve().parents[3]


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
        self.cases_file.write_text(json.dumps({"schema_version": 2, "dataset": "dev20", "snapshot_id": "dev20",
                                               "cases": self.cases}), encoding="utf-8")
        self.runner = hf.FakeRunner()
        stack = contextlib.ExitStack()
        stack.enter_context(mock.patch.object(dispatch, "EVALUATE_BACKEND", dispatch.HOST_BACKEND))
        stack.enter_context(mock.patch.object(dispatch, "host_case_runner", self.runner))
        stack.enter_context(mock.patch.object(dispatch, "evaluate_versions", lambda request, dataset: dict(hf.VERSIONS)))
        stack.enter_context(mock.patch.dict(dispatch.EVALUATE_CASE_LISTS, {"dev20": self.cases_file}))
        self.pacing = batch_run.Pacing()  # 시험은 쉬지 않는다(속도 조절 규칙은 E1 시험과 test_pacing_values_reach_e1)
        stack.enter_context(mock.patch.object(dispatch, "evaluate_pacing", lambda: self.pacing))
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
                           (["evaluate", "--snapshot", "kcs_202201_202412_v2", "--policy", "dev-0.1"],
                            "사례 목록을 읽지 못했다(SnapshotError)"),  # 정본 빌드가 없는 자리(아래 SNAPSHOTS_ROOT)
                           (["evaluate", "--snapshot", "dev20", "--policy", "policy_v9", "--mode", "full"],
                            "묶음 입력이 규칙에 맞지 않는다")):
            with self.subTest(argv=argv), mock.patch.object(query, "SNAPSHOTS_ROOT", self.root / "no_snapshots"):
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

    def test_pacing_values_reach_e1_and_the_conditions_file(self):
        """모델 설정의 pacing을 E1에 넘기고, 실행 조건 입력 파일 prescoring_checks.seed_concurrency에 적는다."""
        seen = {}
        real = batch_run.execute_batch

        def spy(*a, **k):
            seen["pacing"] = k.get("pacing")
            return real(*a, **{**k, "pacing": batch_run.Pacing()})

        with mock.patch.object(dispatch, "evaluate_pacing", ORIGINAL_PACING), \
                mock.patch.object(batch_run, "execute_batch", spy):
            code, out, err = call(ARGV + ["--mode", "full"])
        self.assertEqual(code, 0, err)
        config = json.loads((REPO / "configs" / "model" / "model.json").read_text(encoding="utf-8"))["pacing"]
        self.assertEqual(seen["pacing"], batch_run.Pacing(**config))
        self.assertGreater(seen["pacing"].min_gap_ms, 0)
        doc = self.conditions(out.splitlines()[1])
        self.assertTrue(doc["prescoring_checks"]["seed_concurrency"].startswith(
            f"참: 순서 seed dev-order-v1, 동시성 1, 속도 조절(모델 실행 사이 최소 {config['min_gap_ms'] // 1000}초"))

    def test_bad_pacing_config_fails_before_outputs(self):
        with mock.patch.object(dispatch, "evaluate_pacing", ORIGINAL_PACING), \
                mock.patch.object(batch_run, "pacing_from_config", side_effect=batch_run.BatchError("x")):
            code, out, err = call(ARGV)
        self.assertEqual((code, out), (1, ""))
        self.assertIn("묶음 입력이 규칙에 맞지 않는다(BatchError)", err)
        self.assertFalse((self.root / "outputs").exists())

    OPERATOR = {"rulebook": {"freeze_commit": "abc1234", "changes_after_freeze": "없음"}, "grouping_reason": "g0 고정",
                "scorer_commit": "abc1234", "prose_patterns_commit": "abc1234", "precheck": "통과: 확인 명령 6개 종료 코드 0",
                "skill_call_success": "5/7", "korean_sample_review": "표본 3건 이상 없음",
                "a_grade": {"rb1_frozen": False, "hash_recheck_match": True, "scorer_prevalidation": True, "scored_once": True},
                "sandbox": {"live_policy_sha256": "8a" * 32, "violation_tests_run": "openshell_violation_tests-260925230336"},
                "prescoring_checks": {"version_keys": "참: 5개 일치", "mode_case_sets": "참", "concurrency_record": "해당 없음"}}

    def write_operator(self, doc, name="extra.json") -> str:
        (self.root / "conditions").mkdir(exist_ok=True)
        (self.root / "conditions" / name).write_text(json.dumps(doc, ensure_ascii=False) if not isinstance(doc, str) else doc,
                                                     encoding="utf-8")
        return f"conditions/{name}"

    def test_conditions_extra_is_merged_into_the_conditions_file(self):
        """--conditions-extra(운영자 실행 조건): 채점기 요약이 읽는 키 이름 그대로 합치고, 재현 명령에 옵션을 적고, 표준 오류에
        키 이름만 알린다. 호스트 백엔드에는 하네스 sandbox 객체가 없어 운영자 하위 키만 든 sandbox가 된다."""
        path = self.write_operator(self.OPERATOR)
        code, out, err = call(ARGV + ["--mode", "full", "--conditions-extra", path])
        self.assertEqual(code, 0, err)
        doc = self.conditions(out.splitlines()[1])
        self.assertEqual(doc["reproduce_evaluate"],
                         "tradesentry evaluate --snapshot dev20 --policy dev-0.1 --mode full --conditions-extra conditions/extra.json")
        for key in ("rulebook", "grouping_reason", "scorer_commit", "prose_patterns_commit", "precheck", "skill_call_success",
                    "korean_sample_review", "a_grade"):
            self.assertEqual(doc[key], self.OPERATOR[key], key)
        self.assertEqual(doc["sandbox"], self.OPERATOR["sandbox"])
        self.assertEqual(doc["prescoring_checks"]["version_keys"], "참: 5개 일치")
        self.assertTrue(doc["prescoring_checks"]["final_status"].startswith("참: 예정 실행"))  # 하네스 값은 그대로
        self.assertIn("seed_concurrency", doc["prescoring_checks"])
        notice = [line for line in err.splitlines() if "운영자 실행 조건을 실행 조건 입력 파일에 합쳤다" in line]
        self.assertEqual(len(notice), 1)
        self.assertIn("sandbox.live_policy_sha256, sandbox.violation_tests_run, scorer_commit, skill_call_success", notice[0])
        self.assertNotIn("8a8a", notice[0])  # 값은 적지 않는다
        self.assertNotIn("abc1234", err)

    def test_conditions_extra_sandbox_keys_join_the_sandbox_backend_values(self):
        """샌드박스 백엔드가 채운 sandbox.name·policy_yaml_sha256과 운영자 하위 키를 한 객체로 합친다(merge 함수 수준. 샌드박스
        백엔드 전체 흐름은 test_evaluate_sandbox.py)."""
        extra = {"reproduce_evaluate": "x", "sandbox": {"name": "ts-scored", "policy_yaml_sha256": "dc" * 32}}
        batch_run.merge_operator_conditions(extra, {"sandbox": dict(self.OPERATOR["sandbox"])})
        self.assertEqual(set(extra["sandbox"]), {"name", "policy_yaml_sha256", "live_policy_sha256", "violation_tests_run"})

    def test_without_conditions_extra_the_conditions_file_is_unchanged(self):
        code, out, err = call(ARGV + ["--mode", "full"])
        self.assertEqual(code, 0, err)
        doc = self.conditions(out.splitlines()[1])
        self.assertEqual(set(doc), {"dataset", "planned_cases", "planned_modes", "policy_detection_thresholds", "order_seed",
                                    "concurrency", "limits", "run_period", "nat_profile_summary", "reproduce_evaluate",
                                    "prescoring_checks"})
        self.assertEqual(set(doc["prescoring_checks"]), {"final_status", "seed_concurrency"})
        self.assertEqual(doc["reproduce_evaluate"], "tradesentry evaluate --snapshot dev20 --policy dev-0.1 --mode full")
        self.assertNotIn("운영자 실행 조건", err)

    def test_bad_conditions_extra_fails_before_outputs(self):
        home_path = "~" + "/x"
        bad = [("파일을 읽지 못했다(FileNotFoundError)", None),
               ("JSON이 아니다", "{not json"),
               ("규칙에 맞지 않는다: 운영자 실행 조건 파일은 JSON 객체다", [1]),
               ("두 번 줬다(하네스가 채우는 키다)", {"dataset": "dev20"}),
               ("두 번 줬다(하네스가 채우는 키다)", {"reproduce_evaluate": "x"}),
               ("두 번 줬다(하네스가 채우는 키다)", {"snapshot": {"normalized_sha256": "ab"}}),
               ("약속 밖 키: unknown_key", {"unknown_key": 1}),
               ("sandbox의 하위 키 name는 하네스가 채우거나 약속 밖이다", {"sandbox": {"name": "ts-scored"}}),
               ("sandbox의 하위 키 policy_yaml_sha256는", {"sandbox": {"policy_yaml_sha256": "dc" * 32}}),
               ("prescoring_checks의 하위 키 final_status는", {"prescoring_checks": {"final_status": "참"}}),
               ("로컬 절대경로 모양의 값이 있다(N13)", {"precheck": "/" + "Users/x"}),
               ("로컬 절대경로 모양의 값이 있다(N13)", {"sandbox": {"violation_tests_run": home_path}}),
               ("키 모양의 값이 있다(절대 규칙 1)", {"precheck": "nv" + "api-abc"})]
        for text, doc in bad:
            with self.subTest(text=text):
                path = "conditions/missing.json" if doc is None else self.write_operator(doc)
                code, out, err = call(ARGV + ["--mode", "full", "--conditions-extra", path])
                self.assertEqual((code, out), (1, ""), err)
                self.assertIn("--conditions-extra", err)
                self.assertIn(text, err)
                self.assertNotIn("Users", err)
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
