"""독립 채점기 명령(python -m eval.scorer --run <run_dir>) 시험.

임시 폴더에 저장소 뿌리를 흉내 낸 트리(oracle 정답표 사본, 합성 스냅샷 SQLite, 평가 묶음 실행 폴더와 사례 실행 폴더,
실행 조건 입력 파일)를 만들고 가짜 시계로 돌린다. 봉인 묶음 경로는 임시 폴더의 가짜 봉인 폴더(환경변수
TRADESENTRY_SEALED_DIR로 가리킨다)와 합성 자료만 쓴다. 실제 봉인 폴더와 실제 스냅샷은 쓰지 않는다.
"""
import copy
import hashlib
import io
import json
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

import scorer_fixtures as fx
from eval.scorer import __main__ as cli
from eval.scorer import claims as c1

START = datetime(2026, 9, 25, 15, 0, 0, tzinfo=cli.KST)
BATCH = "evaluate-260925140000"


class FakeClock:
    def __init__(self, start: datetime):
        self.t = start

    def now(self) -> datetime:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.t += timedelta(seconds=seconds)


def dump(value: object) -> str:
    return c1.dumps_json(value)


class ScorerCommandBase(unittest.TestCase):
    dataset = "controlled_fixture_v0"
    sealed = False

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "repo"
        (self.root / "eval" / "dev").mkdir(parents=True)
        shutil.copyfile(fx.REPO_ROOT / "eval" / "dev" / "oracle_ABC.json", self.root / "eval" / "dev" / "oracle_ABC.json")
        self.sealed_dir = Path(self._tmp.name) / "fake-sealed"
        self.environ = {"TRADESENTRY_SEALED_DIR": str(self.sealed_dir), "HOME": str(Path(self._tmp.name) / "home")}
        self.rows, self.ids = fx.oracle_snapshot(fx.load_oracle())
        snap_dir = self.root / "data" / "snapshots" / "controlled_fixture_v0"
        snap_dir.mkdir(parents=True)
        fx.write_sqlite(snap_dir / "snapshot_build.sqlite", self.rows.doc())
        parent = self.root / "outputs" / ("sealed" if self.sealed else "")
        self.batch_dir = parent / BATCH
        self.batch_dir.mkdir(parents=True)
        self.reports = fx.oracle_reports(self.rows, self.ids, mode="full")
        self.lines = []
        for case_id, report in self.reports.items():
            self.lines.append(fx.batch_line(report["run_id"], case_id, mode="full", dataset=self.dataset,
                                            review=report["review_status"]))
            case_dir = parent / report["run_id"]
            case_dir.mkdir()
            stamp = report["run_id"].rsplit("-", 1)[1]
            (case_dir / f"reports_render_ko-{stamp}.json").write_text(dump(report), encoding="utf-8")
        self.conditions = {
            "dataset": self.dataset, "planned_modes": ["full"],
            "planned_cases": [{"case_id": c, "hs6": "850450", "partner": p, "month": "202401"}
                              for c, p in fx.ORACLE_PARTNERS.items()],
            "scorer_commit": "0123456", "prose_patterns_commit": "0123456", "concurrency": 1, "order_seed": "11",
            "policy_detection_thresholds": [30, 10], "reproduce_evaluate": "tradesentry evaluate ...",
        }

    def write_inputs(self, conditions: dict | None = None, lines: list | None = None) -> None:
        (self.batch_dir / f"evaluation_batch_run-{BATCH.rsplit('-', 1)[1]}.jsonl").write_text(
            "".join(dump(line) + "\n" for line in (self.lines if lines is None else lines)), encoding="utf-8")
        if conditions is not False:
            (self.batch_dir / f"run_conditions-{BATCH.rsplit('-', 1)[1]}.json").write_text(
                dump(self.conditions if conditions is None else conditions), encoding="utf-8")

    def run_scorer(self, run_dir: Path | None = None) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        clock = FakeClock(START)
        code = cli.main(["--run", str(run_dir or self.batch_dir)], repo_root=self.root, environ=self.environ,
                        clock=clock.now, sleep=clock.sleep, out=out, err=err)
        for text in (out.getvalue(), err.getvalue()):
            self.assertNotIn(self._tmp.name, text)  # 로컬 절대경로를 출력하지 않는다(N13)
        return code, out.getvalue(), err.getvalue()

    def score_dir(self, stamp: str = "260925150000") -> Path:
        return self.root / "outputs" / f"score-{stamp}"


class DevelopmentBatchTest(ScorerCommandBase):
    def test_scores_and_writes_three_files(self):
        self.write_inputs()
        code, out, err = self.run_scorer()
        self.assertEqual((code, err), (0, ""), err)
        self.assertEqual(out.splitlines(), ["score-260925150000", "끝 상태: 완료"])
        folder = self.score_dir()
        self.assertEqual(sorted(p.name for p in folder.iterdir()),
                         ["scorer_claims-260925150000.jsonl", "scorer_results-260925150000.jsonl",
                          "scorer_summary-260925150000.md"])
        results = [c1.loads_json(line) for line in (folder / "scorer_results-260925150000.jsonl").read_text(
            encoding="utf-8").splitlines()]
        self.assertEqual([tuple(r) for r in results], [tuple(cli.c3.RESULT_KEYS)] * 3)
        self.assertTrue(all(r["required_evidence_ok"] and r["numeric_ok"] and r["provenance_ok"] for r in results))
        claims = [c1.loads_json(line) for line in (folder / "scorer_claims-260925150000.jsonl").read_text(
            encoding="utf-8").splitlines()]
        self.assertTrue(claims and all(tuple(r) == c1.RECORD_KEYS for r in claims))
        self.assertIn('"reported_value": -40.0', (folder / "scorer_claims-260925150000.jsonl").read_text(encoding="utf-8"))
        summary = (folder / "scorer_summary-260925150000.md").read_text(encoding="utf-8")
        self.assertIn("# 평가 결과 요약 — evaluate-260925140000", summary)
        self.assertIn("채점기 커밋 0123456", summary)
        self.assertIn("data/snapshots/controlled_fixture_v0/snapshot_build.sqlite", summary)
        report_bytes = next((self.root / "outputs").glob("run_case-*/reports_render_ko-*.json")).read_bytes()
        self.assertIn(hashlib.sha256(report_bytes).hexdigest(), summary)

    def test_run_name_is_secured_with_next_second_when_taken(self):
        self.write_inputs()
        self.score_dir().mkdir(parents=True)
        (self.root / "outputs" / "sealed").mkdir(exist_ok=True)
        (self.root / "outputs" / "sealed" / "score-260925150001").mkdir()  # 다른 부모 폴더에 같은 이름
        code, out, _ = self.run_scorer()
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[0], "score-260925150002")
        self.assertEqual(list(self.score_dir().iterdir()), [])
        self.assertFalse(self.score_dir("260925150001").exists())

    def test_missing_or_bad_conditions_file_is_refused(self):
        self.write_inputs(conditions=False)
        code, out, err = self.run_scorer()
        self.assertEqual(code, cli.EXIT_FAILED)
        self.assertEqual(out.splitlines(), ["score-260925150000", "끝 상태: 실패(입력 오류)"])
        self.assertIn("실행 조건 입력 파일이 없다", err)
        self.assertEqual(list(self.score_dir().iterdir()), [])
        bad_cases = {
            "unknown key": dict(self.conditions, extra=1),
            "absolute path": dict(self.conditions, precheck="결과는 /" + "Users/someone/x 에 있다"),
            "modes": dict(self.conditions, planned_modes=["full", "full"]),
            "case": dict(self.conditions, planned_cases=[{"case_id": "A-composition"}]),
            "dataset": dict(self.conditions, dataset="holdout40"),
        }
        for name, conditions in bad_cases.items():
            with self.subTest(case=name):
                shutil.rmtree(self.root / "outputs" / "score-260925150000", ignore_errors=True)
                self.write_inputs(conditions=conditions)
                code, out, _ = self.run_scorer()
                self.assertEqual((code, out.splitlines()[-1]), (cli.EXIT_FAILED, "끝 상태: 실패(입력 오류)"))

    def test_batch_line_must_match_case_folder_and_plan(self):
        report = self.reports["A-composition"]
        path = next((self.root / "outputs" / report["run_id"]).iterdir())
        path.write_text(dump(dict(report, mode="agent")), encoding="utf-8")
        self.write_inputs()
        code, _, err = self.run_scorer()
        self.assertEqual(code, cli.EXIT_FAILED)
        self.assertIn("묶음 기록 줄과 맞지 않다", err)
        shutil.rmtree(self.score_dir())
        path.write_text(dump(report), encoding="utf-8")
        self.write_inputs(lines=self.lines + [dict(self.lines[0])])
        self.assertIn("같은 run_id", self.run_scorer()[2])
        shutil.rmtree(self.score_dir())
        self.write_inputs(lines=self.lines + [fx.batch_line("run_case-260925130000", "Z-unplanned")])
        self.assertIn("계획 밖", self.run_scorer()[2])

    def test_missing_case_folder_counts_as_failure_not_error(self):
        shutil.rmtree(self.root / "outputs" / self.reports["B-residual"]["run_id"])
        self.write_inputs()
        code, _, _ = self.run_scorer()
        self.assertEqual(code, 0)
        results = [c1.loads_json(line) for line in (self.score_dir() / "scorer_results-260925150000.jsonl")
                   .read_text(encoding="utf-8").splitlines()]
        self.assertEqual([r["numeric_ok"] for r in results], [True, False, True])
        summary = (self.score_dir() / "scorer_summary-260925150000.md").read_text(encoding="utf-8")
        self.assertIn("보고서를 읽지 못한 COMPLETED 실행 1건", summary)

    def test_run_dir_must_be_an_outputs_run_folder(self):
        self.write_inputs()
        for bad in (self.root / "eval", self.root / "outputs", self.root / "outputs" / "not-a-run"):
            with self.subTest(run_dir=bad.name):
                code, out, err = self.run_scorer(bad)
                self.assertEqual((code, out), (cli.EXIT_USAGE, ""))
                self.assertTrue(err.startswith("오류:"))
        self.assertFalse(self.score_dir().exists())

    def test_snapshot_file_is_not_modified(self):
        path = self.root / "data" / "snapshots" / "controlled_fixture_v0" / "snapshot_build.sqlite"
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        self.write_inputs()
        self.assertEqual(self.run_scorer()[0], 0)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)
        self.assertEqual(sorted(p.name for p in path.parent.iterdir()), ["snapshot_build.sqlite"])


class SealedBatchTest(ScorerCommandBase):
    """봉인 묶음(holdout40) 채점: 표준 출력·오류 출력에는 실행 폴더 이름과 끝 상태만 낸다(자료 계약 §10.3 N10)."""

    dataset = "holdout40"
    sealed = True

    def setUp(self):
        super().setUp()
        answers = fx.load_oracle()
        self.sealed_dir.mkdir()
        (self.sealed_dir / "answers.json").write_text(dump(answers), encoding="utf-8")
        digest = hashlib.sha256((self.sealed_dir / "answers.json").read_bytes()).hexdigest()
        (self.root / "eval" / "sealed_manifest.json").write_text(json.dumps({"schema_version": 1, "files": [
            {"dataset": "holdout40", "file_name": "answers.json", "sha256": digest,
             "created_at": "2026-09-25T09:00:00+09:00", "created_by": "시험"}]}), encoding="utf-8")
        patcher = mock.patch.dict(cli.SEALED_FILES, {"holdout40": "answers.json"})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.conditions.update({"planned_modes": ["checklist", "agent", "full"], "sealed_hash_recheck": "일치",
                                "rulebook": {"freeze_commit": "abcdef0", "changes_after_freeze": "없음"},
                                "sealed_provenance_check": "통과", "prescoring_checks": {"final_status": "참"},
                                "precheck": "통과", "sandbox": {"name": "official"}})

    def test_success_prints_only_folder_and_end_status(self):
        self.write_inputs()
        code, out, err = self.run_scorer()
        self.assertEqual(code, 0, out)
        self.assertEqual((out.splitlines(), err), (["score-260925150000", "끝 상태: 완료"], ""))
        summary = (self.score_dir() / "scorer_summary-260925150000.md").read_text(encoding="utf-8")
        self.assertIn("## 2. 보조 지표 — holdout40 (등급 C)", summary)
        self.assertIn("미실행: checklist 3건, agent 3건, full 0건", summary)  # 계획했는데 줄이 없는 실행
        self.assertIn("금지 해제 조건 뒤 결과표(로드맵 R1)에 적음", summary)

    def test_failures_print_no_case_identifiers(self):
        cases = {
            "hash mismatch": lambda: (self.sealed_dir / "answers.json").write_text("{}", encoding="utf-8"),
            "report mismatch": lambda: next((self.root / "outputs" / "sealed" / self.reports["A-composition"]["run_id"])
                                            .iterdir()).write_text(dump(dict(self.reports["A-composition"],
                                                                             case_id="LEAK-ME")), encoding="utf-8"),
            "nat summary": lambda: self.conditions.update(nat_profile_summary="x"),
            "recheck": lambda: self.conditions.update(sealed_hash_recheck="불일치"),
        }
        for name, spoil in cases.items():
            with self.subTest(case=name):
                self.setUp()
                spoil()
                self.write_inputs()
                code, out, err = self.run_scorer()
                self.assertEqual(code, cli.EXIT_FAILED)
                self.assertEqual((out.splitlines(), err), (["score-260925150000", "끝 상태: 실패(입력 오류)"], ""))
                self.assertNotIn("LEAK-ME", out + err)
                self.assertNotIn("A-composition", out + err)

    def test_unexpected_error_is_also_quiet(self):
        self.write_inputs()
        with mock.patch.object(cli.c4, "render", side_effect=RuntimeError("A-composition 사례에서 실패")):
            code, out, err = self.run_scorer()
        self.assertEqual((code, out.splitlines(), err), (cli.EXIT_FAILED, ["score-260925150000", "끝 상태: 실패(내부 오류)"], ""))

    def test_sealed_folder_comes_only_from_environment(self):
        self.assertEqual(cli.sealed_dir({"TRADESENTRY_SEALED_DIR": str(self.sealed_dir)}), self.sealed_dir)
        self.assertEqual(cli.sealed_dir({"TRADESENTRY_SEALED_DIR": "", "HOME": "/h"}),
                         Path("/h") / ".tradesentry" / "sealed")
        with self.assertRaises(c1.ScorerInputError):
            cli.sealed_dir({})

    def test_bad_sealed_run_dir_prints_only_end_status(self):
        code, out, err = self.run_scorer(self.root / "outputs" / "sealed" / "evaluate-260925139999")
        self.assertEqual((code, out, err), (cli.EXIT_USAGE, "끝 상태: 실패(인자 오류)\n", ""))

    def test_unlisted_sealed_file_is_not_read(self):
        with mock.patch.dict(cli.SEALED_FILES, {"holdout40": "other.json"}):
            (self.sealed_dir / "other.json").write_text("{}", encoding="utf-8")
            self.write_inputs()
            code, out, err = self.run_scorer()
        self.assertEqual((code, err), (cli.EXIT_FAILED, ""))


if __name__ == "__main__":
    unittest.main()
