"""독립 채점기 명령(python -m eval.scorer --run <run_dir>) 시험.

임시 폴더에 저장소 뿌리를 흉내 낸 트리(oracle 정답표 사본, 합성 스냅샷 SQLite, 평가 묶음 실행 폴더와 사례 실행 폴더,
실행 조건 입력 파일)를 만들고 가짜 시계로 돌린다. 봉인 묶음 경로는 임시 폴더의 가짜 봉인 폴더(환경변수
TRADESENTRY_SEALED_DIR로 가리킨다)와 합성 자료만 쓴다. 실제 봉인 폴더와 실제 스냅샷은 쓰지 않는다.
믿지 않는 보고서·묶음 기록(아주 큰 지수, 목록 direction, 깊은 중첩, U+2028, 크기 상한)이 묶음 채점을 멈추거나
끝나지 않게 하지 않는지, 예외 경로(폴더 확보 OSError, 심볼릭 링크 봉인 <run_dir>)에서도 봉인 출력 규칙을 지키는지 본다.
"""
import copy
import os
import time
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

    def rerun(self, stamp: str, status: str, index: int = 0) -> dict:
        base = self.lines[index]
        return fx.batch_line(f"run_case-{stamp}", base["case_id"], mode=base["mode"], dataset=self.dataset,
                             status=status, review=base["review_status_final"])

    def test_missing_planned_run_is_scored_as_failure_not_rejected(self):
        self.write_inputs(lines=self.lines[1:])  # 룰북 B5: 미실행도 분모에 실패로 남는다(거부하면 남길 수 없다)
        code, out, err = self.run_scorer()
        self.assertEqual((code, err), (0, ""), err)
        summary = (self.score_dir() / "scorer_summary-260925150000.md").read_text(encoding="utf-8")
        self.assertIn("미실행 1건", summary)

    def write_trace(self, report: dict, events: list[dict] | None, text: str | None = None) -> Path:
        """사례 실행 폴더에 실행 추적 runlog_trace-{시각}.jsonl을 둔다(events가 None이면 text를 그대로 쓴다)."""
        stamp = report["run_id"].rsplit("-", 1)[1]
        path = self.root / "outputs" / report["run_id"] / f"runlog_trace-{stamp}.jsonl"
        body = text if events is None else "".join(dump(e) + "\n" for e in events)
        path.write_text(body, encoding="utf-8")
        return path

    def trace_state(self, run_id: str, seq: int, phase: str, stage: str, **data) -> dict:
        return {"seq": seq, "ts": "2026-09-25T14:00:00+09:00", "run_id": run_id, "event": "state_change", "stage": stage,
                "data": {"phase": phase, "review_status": "MONITOR", "signal_status": {"unit_value": "MONITOR", "share": "NOT_TRIGGERED"},
                         **data}}

    def test_rulebook_b7_public_values_come_from_trace_files(self):
        """룰북 B7 공개 값: 사례 실행 폴더의 trace를 읽기만 해서 모드별 건수·비율을 요약에 적는다. trace가 없는 실행이 있으면
        "집계하지 않음(trace 없음)"이고 채점은 실패하지 않는다(증거 사본만으로 다시 채점할 때)."""
        a, b, c = (self.reports[k] for k in ("A-composition", "B-residual", "C-missing-hs10"))
        # A: c1(r_U −40.0%)이 코드가 덧붙인 주장이라고 trace가 적는다 → 덧붙이기 전에는 산문 "40.0% 낮아졌다"가 뒷받침되지 않는다
        self.write_trace(a, [self.trace_state(a["run_id"], 1, "draft", "basic"),
                             self.trace_state(a["run_id"], 2, "evidence_claims", "final", required={}, unmet=[], no_action=[],
                                              added=[{"signal": "unit_value", "code": "comparability_ok",
                                                      "claims": [{"claim_type": "change", "metric_id": "r_U-1", "claim_id": "c1"}]},
                                                     {"signal": "unit_value", "code": "zero_weight_claim",
                                                      "claims": [{"claim_type": "value", "metric_id": "w@1", "claim_id": "c6"}]}])])
        # B: review_status 집계로 바뀜(final), HOLD 합의로 뺀 도구 지적 1, (가) 재조회 버림 1
        self.write_trace(b, [self.trace_state(b["run_id"], 1, "status_aggregated", "final", model_review_status="HOLD",
                                              model_unresolved_evidence=None, unresolved_evidence=False),
                             self.trace_state(b["run_id"], 2, "code_finding", "basic", missing_tools=[], skipped_for_hold=["compare_partners"]),
                             self.trace_state(b["run_id"], 3, "after_critic", "critic", needs_revision=False, findings=0, requery=0,
                                              problems=[], requery_dropped=[{"tool": "decompose_hs", "args": {}, "reason": "x", "signals": ["unit_value"]}])])
        self.write_inputs()
        code, out, err = self.run_scorer()  # C는 trace 없음
        self.assertEqual((code, err), (0, ""), err)
        summary = (self.score_dir() / "scorer_summary-260925150000.md").read_text(encoding="utf-8")
        self.assertIn("full 집계하지 않음(trace 없음 1/3건)", summary)
        self.assertIn("모드별 trace 있는 최종 실행 full 2/3건", summary)
        # C: (나) 수정본 버림 1 → 세 실행 모두 trace가 있어 집계한다
        self.write_trace(c, [self.trace_state(c["run_id"], 1, "revision_discarded", "final", blocked_by="validator",
                                              would_be_cause="VALIDATOR_BLOCKED", kept_report_id="r1")])
        clock_shift = FakeClock(START + timedelta(seconds=5))
        out, err = io.StringIO(), io.StringIO()
        code = cli.main(["--run", str(self.batch_dir)], repo_root=self.root, environ=self.environ, clock=clock_shift.now,
                        sleep=clock_shift.sleep, out=out, err=err)
        self.assertEqual((code, err.getvalue()), (0, ""), err.getvalue())
        summary = (self.score_dir("260925150005") / "scorer_summary-260925150005.md").read_text(encoding="utf-8")
        self.assertIn("full 전 1/3 → 뒤 0/3", summary)
        self.assertIn("- 덧붙인 주장 덕분에 뒷받침된 산문 표현 수: full 1", summary)
        self.assertIn("full 보고서당 0(0~2), 합계 2(필수 근거 1·자기 계열 0·중량 0 1), 완료 보고서 3건", summary)
        self.assertIn("괄호는 어느 단계든 바뀐 보고서 수): full 1(1)", summary)
        self.assertIn("(나) 수정본 버림 full 1; (가) 재조회 버림 full 1", summary)
        self.assertIn("HOLD 합의 신호에 내지 않은 도구 지적 수(2026-09-25(금) 22:22 사용자 결정 ③): full 1", summary)
        self.assertIn("덧붙이기 전 기준의 보고서 단위 오류율(덧붙인 필수 근거 주장을 빼고 같은 채점 규칙으로 다시 계산. 2026-09-25(금) 18:56 사용자 "
                      "결정. 괄호는 덧붙이기 뒤): full 1/3 = 33.3% (6.1%~79.2%) (뒤 0/3)", summary)
        results = [c1.loads_json(line) for line in (self.score_dir("260925150005") / "scorer_results-260925150005.jsonl")
                   .read_text(encoding="utf-8").splitlines()]
        self.assertEqual([tuple(r) for r in results], [tuple(cli.c3.RESULT_KEYS)] * 3)  # 결과 기록의 키는 늘리지 않는다
        cases = {  # (trace 본문 또는 None(권한 0 파일), 기대 사유). 채점은 모두 종료 코드 0으로 끝난다
            "깨진 줄": ("{not json}\n", "trace를 읽을 수 없음"),
            "run_id 다름": (dump(self.trace_state("run_case-000000000000", 1, "draft", "basic")) + "\n", "trace를 읽을 수 없음"),
            "모양 다른 사건(added가 목록 아님)": (dump(self.trace_state(c["run_id"], 1, "evidence_claims", "final", added={"code": "x"})) + "\n",
                                           "trace 모양 다름"),
            "모양 다른 사건(stage 없음)": (dump({k: v for k, v in self.trace_state(c["run_id"], 1, "draft", "basic").items() if k != "stage"}) + "\n",
                                       "trace 모양 다름"),
            "읽기 실패(권한 0)": (None, "trace를 읽을 수 없음"),
        }
        for offset, (name, (body, reason)) in enumerate(cases.items(), start=2):
            with self.subTest(name=name):
                path = self.write_trace(c, None, body or "")
                if body is None:
                    if os.geteuid() == 0:
                        self.skipTest("root는 권한 0 파일도 읽는다")
                    path.chmod(0)
                    self.addCleanup(path.chmod, 0o600)
                clock = FakeClock(START + timedelta(seconds=5 * offset))
                out, err = io.StringIO(), io.StringIO()
                code = cli.main(["--run", str(self.batch_dir)], repo_root=self.root, environ=self.environ, clock=clock.now,
                                sleep=clock.sleep, out=out, err=err)
                self.assertEqual((code, err.getvalue()), (0, ""))
                stamp = (START + timedelta(seconds=5 * offset)).strftime(cli.STAMP_FORMAT)
                summary = (self.score_dir(stamp) / f"scorer_summary-{stamp}.md").read_text(encoding="utf-8")
                self.assertIn(f"full 집계하지 않음({reason} 1/3건)", summary)
                if body is None:
                    path.chmod(0o600)

    def test_report_without_claim_list_is_not_counted_as_zero_attached(self):
        """완료 보고서의 claims가 목록이 아니면 덧붙인 주장 0으로 세지 않고 그 실행을 집계 불가(모양 오류)로 둔다."""
        a = self.reports["A-composition"]
        self.write_trace(a, [self.trace_state(a["run_id"], 1, "draft", "basic")])
        line = fx.batch_line(a["run_id"], "A-composition", mode="full", dataset=self.dataset, review=a["review_status"])
        snap = c1.Snapshot.from_json(self.rows.doc())
        entry = cli.trace_entry(self.batch_dir, line, dict(a, claims={"c1": 1}), [], snap, self.rows.snapshot_id,
                                fx.oracle_context("A-composition"), [])
        self.assertEqual(entry, {"available": False, "reason": "trace 모양 다름"})
        self.assertEqual(cli.c4.trace_facts([], dict(a, claims="x"), True)["report_shape_ok"], False)
        self.assertIsNone(cli.c4.trace_facts([], dict(a, claims="x"), True)["attached_count"])

    def test_rerun_shape_of_rulebook_b5(self):
        self.write_inputs(lines=[self.rerun("260925090000", "FAILED")] + self.lines)
        self.assertEqual(self.run_scorer()[0], 0)  # FAILED 한 줄 뒤 재실행 한 줄만 받는다
        bad = {"completed then completed": [self.rerun("260925090000", "COMPLETED")],
               "timeout then completed": [self.rerun("260925090000", "TIMEOUT")],
               "three lines": [self.rerun("260925080000", "FAILED"), self.rerun("260925090000", "FAILED")],
               "failed after completed": [self.rerun("260925110000", "FAILED")]}
        for name, extra in bad.items():
            with self.subTest(case=name):
                with self.assertRaises(c1.ScorerInputError):
                    cli.check_rerun_shape(extra + self.lines)
        self.write_inputs(lines=bad["timeout then completed"] + self.lines)
        code, out, err = self.run_scorer()
        self.assertEqual(code, cli.EXIT_FAILED)
        self.assertIn("B5", err)

    def test_absolute_path_shapes_in_conditions_are_rejected(self):
        for value in ("/etc/x", "tradesentry evaluate --run /workspace/x", "\\\\srv\\share", "D:/x", "C:\\x",
                      "~" + "/x", '{"f": "/srv/a"}'):
            with self.subTest(value=value):
                self.write_inputs(dict(self.conditions, reproduce_evaluate=value))
                code, out, err = self.run_scorer()
                self.assertEqual(code, cli.EXIT_FAILED)
                self.assertIn("N13", err)
                shutil.rmtree(self.score_dir())
        for value in ("USD/kg", "https://example.org/a", "a / b", "tradesentry evaluate outputs/x", "2026/09/25",
                      "~/.tradesentry/sealed/"):
            self.assertIsNone(cli.ABSOLUTE_PATH.search(value), value)

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
        (self.root / "eval" / "sealed_manifest.json").write_text(json.dumps({"schema_version": 2, "files": [
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

    def test_path_through_sealed_to_dev_folder_is_rejected_quietly(self):
        (self.root / "outputs" / "evaluate-260925140002").mkdir()
        code, out, err = self.run_scorer(self.root / "outputs" / "sealed" / ".." / "evaluate-260925140002")
        self.assertEqual((code, out, err), (cli.EXIT_USAGE, "끝 상태: 실패(인자 오류)\n", ""))

    def test_sealed_folder_name_in_repo_root_does_not_hint_sealed(self):
        root = Path(self._tmp.name) / "sealed" / "repo"
        self.assertFalse(cli.sealed_hint(str(root / "outputs" / "evaluate-260925140002"), root))
        self.assertTrue(cli.sealed_hint(str(root / "outputs" / "sealed" / "evaluate-260925140002"), root))

    def test_case_variant_and_dev_symlink_to_sealed_are_quiet(self):
        self.write_inputs()
        code, out, err = self.run_scorer(self.root / "outputs" / "SEALED" / BATCH)
        self.assertEqual((code, out, err), (cli.EXIT_USAGE, "끝 상태: 실패(인자 오류)\n", ""))
        link = self.root / "outputs" / "evaluate-260925140003"
        os.symlink(self.batch_dir, link)
        code, out, err = self.run_scorer(link)
        self.assertEqual((code, out, err), (cli.EXIT_USAGE, "끝 상태: 실패(인자 오류)\n", ""))
        self.assertTrue(cli.sealed_hint(str(link), self.root))

    def test_every_sealed_required_value_is_required(self):
        for key in cli.SEALED_REQUIRED:
            with self.subTest(key=key):
                self.setUp()
                self.conditions.pop(key)
                self.write_inputs()
                code, out, err = self.run_scorer()
                self.assertEqual((code, out.splitlines(), err),
                                 (cli.EXIT_FAILED, ["score-260925150000", "끝 상태: 실패(입력 오류)"], ""))

    def test_bad_sealed_run_dir_prints_only_end_status(self):
        code, out, err = self.run_scorer(self.root / "outputs" / "sealed" / "evaluate-260925139999")
        self.assertEqual((code, out, err), (cli.EXIT_USAGE, "끝 상태: 실패(인자 오류)\n", ""))

    def test_unlisted_sealed_file_is_not_read(self):
        with mock.patch.dict(cli.SEALED_FILES, {"holdout40": "other.json"}):
            (self.sealed_dir / "other.json").write_text("{}", encoding="utf-8")
            self.write_inputs()
            code, out, err = self.run_scorer()
        self.assertEqual((code, err), (cli.EXIT_FAILED, ""))


class Dev20AnswersTest(unittest.TestCase):
    """dev20 정답표는 저장소 안 eval/dev/dev20/answers/answers.json(DT5 결정 기록 ⑭)에서 읽는다. 합성 정답표만 쓴다."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / "repo"

    def test_path_is_fixed(self):
        self.assertEqual(cli.DEV20_ANSWERS, ("eval", "dev", "dev20", "answers", "answers.json"))

    def test_reads_answer_table_from_dev20_path(self):
        with self.assertRaises(c1.ScorerInputError):  # 파일이 없으면 입력 오류
            cli.load_answers("dev20", self.root, {})
        path = self.root.joinpath(*cli.DEV20_ANSWERS)
        path.parent.mkdir(parents=True)
        answers = fx.load_oracle()
        answers["cases"][0]["expected"]["required_evidence"] = ["country_and_world_change_shown"]
        answers["cases"][0]["expected"]["signals"] = {"unit_value": "NOT_TRIGGERED", "share": "TRIGGERED"}
        answers["cases"][1]["expected"]["required_evidence"] = ["precision_sensitivity_shown"]
        path.write_text(dump(answers), encoding="utf-8")
        table = cli.c3.read_answer_table(cli.load_answers("dev20", self.root, {}))
        self.assertEqual(len(table), len(answers["cases"]))
        both = copy.deepcopy(answers)  # 두 신호가 모두 발동하면 합친 목록은 받지 않는다(신호별 객체)
        both["cases"][0]["expected"].update(
            signals={"unit_value": "TRIGGERED", "share": "TRIGGERED"},
            signal_status={"unit_value": "MONITOR", "share": "MONITOR"},
            required_evidence=["comparability_ok", "country_and_world_change_shown"])
        with self.assertRaises(c1.ScorerInputError):
            cli.c3.read_answer_table(both)
        both["cases"][0]["expected"]["required_evidence"] = {"unit_value": ["comparability_ok"],
                                                             "share": ["country_and_world_change_shown"]}
        self.assertEqual(cli.c3.read_answer_table(both)[answers["cases"][0]["case_id"]]["required_evidence"],
                         {"unit_value": ["comparability_ok"], "share": ["country_and_world_change_shown"]})


class UntrustedInputTest(ScorerCommandBase):
    """믿지 않는 보고서·묶음 기록은 그 보고서 하나의 결과로 끝나고 묶음 채점을 멈추지 않는다(보안 검토 1회차 막는 지적)."""

    def report_path(self, case_id: str) -> Path:
        return next((self.root / "outputs" / self.reports[case_id]["run_id"]).iterdir())

    def results(self) -> list[dict]:
        return [c1.loads_json(line) for line in (self.score_dir() / "scorer_results-260925150000.jsonl")
                .read_text(encoding="utf-8").splitlines()]

    def test_poisoned_reports_are_contained(self):
        a = copy.deepcopy(self.reports["A-composition"])
        a["claims"][0]["value"] = c1.loads_json("1e999999999")  # 아주 큰 지수: 해석 불가 claim
        self.report_path("A-composition").write_text(dump(a), encoding="utf-8")
        b = copy.deepcopy(self.reports["B-residual"])
        b["claims"][0]["direction"] = []
        b["review_status"] = []
        b["narrative"] = "단가가 증가했다."
        self.report_path("B-residual").write_text(dump(b), encoding="utf-8")
        c = self.reports["C-missing-hs10"]
        nested = "[" * 10000 + "]" * 10000
        self.report_path("C-missing-hs10").write_text(dump(c)[:-1] + f', "extra": {nested}}}', encoding="utf-8")
        self.write_inputs()
        started = time.monotonic()
        code, out, err = self.run_scorer()
        self.assertLess(time.monotonic() - started, 30)
        self.assertEqual((code, err), (0, ""), err)
        # A: 큰 지수 claim은 해석 불가(근거도 대조하지 않음), B: 방향 오류이나 근거는 맞음, C: 읽지 못한 보고서
        self.assertEqual([(r["numeric_ok"], r["provenance_ok"]) for r in self.results()],
                         [(False, False), (False, True), (False, False)])
        summary = (self.score_dir() / "scorer_summary-260925150000.md").read_text(encoding="utf-8")
        self.assertIn("보고서를 읽지 못한 COMPLETED 실행 1건", summary)
        self.assertIn("보고서 JSON 중첩이 너무 깊다 1건", summary)

    def test_oversized_report_counts_as_failure(self):
        report = dict(self.reports["A-composition"], narrative="가" * (cli.MAX_REPORT_BYTES // 3 + 10))
        self.report_path("A-composition").write_text(dump(report), encoding="utf-8")
        self.write_inputs()
        self.assertEqual(self.run_scorer()[0], 0)
        self.assertFalse(self.results()[0]["numeric_ok"])
        summary = (self.score_dir() / "scorer_summary-260925150000.md").read_text(encoding="utf-8")
        self.assertIn("보고서 크기 상한 초과 1건", summary)

    def test_too_much_prose_counts_as_failure(self):
        report = dict(self.reports["A-composition"], narrative="가" * (cli.c2.MAX_PROSE_CHARS + 1))
        self.report_path("A-composition").write_text(dump(report), encoding="utf-8")
        self.write_inputs()
        self.assertEqual(self.run_scorer()[0], 0)
        self.assertEqual([r["numeric_ok"] for r in self.results()], [False, True, True])

    def test_batch_line_is_split_only_at_newline(self):
        lines = copy.deepcopy(self.lines)
        lines[0]["errors"] = [{"message": "줄\u2028나눔\u2029문자\u0085포함"}]
        text = "".join(json.dumps(line, ensure_ascii=False) + "\n" for line in lines)
        self.assertIn("\u2028", text)
        self.write_inputs(lines=[])
        (self.batch_dir / f"evaluation_batch_run-{BATCH.rsplit('-', 1)[1]}.jsonl").write_text(text, encoding="utf-8")
        code, _, err = self.run_scorer()
        self.assertEqual((code, err), (0, ""))

    def test_conditions_are_checked_more_strictly(self):
        base = dict(self.conditions)
        bad_cases = {
            "thresholds missing": {k: v for k, v in base.items() if k != "policy_detection_thresholds"},
            "thresholds empty": dict(base, policy_detection_thresholds=[]),
            "thresholds huge": dict(base, policy_detection_thresholds=[c1.loads_json("1e999999999")]),
            "partner ALL": dict(base, planned_cases=[dict(base["planned_cases"][0], partner="ALL")]),
            "month newline": dict(base, planned_cases=[dict(base["planned_cases"][0], month="202401\n")]),
            "key shape": dict(base, precheck="nv" + "api-" + "x" * 10),
            "service key shape": dict(base, precheck="service" + "Key=abc"),
            "too large": dict(base, precheck="가" * cli.MAX_CONDITIONS_BYTES),
        }
        for name, conditions in bad_cases.items():
            with self.subTest(case=name):
                shutil.rmtree(self.score_dir(), ignore_errors=True)
                self.write_inputs(conditions=conditions)
                code, out, err = self.run_scorer()
                self.assertEqual((code, out.splitlines()[-1]), (cli.EXIT_FAILED, "끝 상태: 실패(입력 오류)"))
                self.assertNotIn("api-", err)

    def test_snapshot_without_build_meta_is_refused(self):
        path = self.root / "data" / "snapshots" / "controlled_fixture_v0" / "snapshot_build.sqlite"
        path.unlink()
        doc = self.rows.doc()
        doc["tables"]["snapshot_meta"] = []
        fx.write_sqlite(path, doc)
        self.write_inputs()
        code, _, err = self.run_scorer()
        self.assertEqual(code, cli.EXIT_FAILED)
        self.assertIn("스냅샷 메타", err)

    def test_snapshot_meta_of_previous_contract_version_is_refused(self):
        """계약 버전 1(이전 계약)로 빌드한 스냅샷은 채점하지 않는다(자료 계약 §1.2, 버전 2로 올림)."""
        path = self.root / "data" / "snapshots" / "controlled_fixture_v0" / "snapshot_build.sqlite"
        path.unlink()
        doc = self.rows.doc()
        doc["tables"]["snapshot_meta"] = [dict(row, value="1") if row["key"] == "schema_version" else row
                                          for row in doc["tables"]["snapshot_meta"]]
        fx.write_sqlite(path, doc)
        self.write_inputs()
        code, _, err = self.run_scorer()
        self.assertEqual(code, cli.EXIT_FAILED)
        self.assertIn("schema_version이 2가 아니다", err)

    def test_folder_os_error_prints_no_path(self):
        self.write_inputs()
        with mock.patch.object(cli.os, "mkdir", side_effect=PermissionError(13, "Permission denied",
                                                                           str(self.score_dir()))):
            code, out, err = self.run_scorer()
        self.assertEqual((code, out), (cli.EXIT_OUTPUT, ""))
        self.assertIn("PermissionError: Permission denied", err)


class SealedExceptionPathTest(SealedBatchTest):
    """봉인 묶음의 예외 경로에서도 표준 출력에는 끝 상태만, 오류 출력은 비어 있다(보안 검토 1회차 권고 2)."""

    def test_symlink_sealed_run_dir_is_quiet(self):
        self.write_inputs()
        link = self.root / "outputs" / "sealed" / "evaluate-260925140001"
        os.symlink(self.batch_dir, link)
        code, out, err = self.run_scorer(link)
        self.assertEqual((code, out, err), (cli.EXIT_USAGE, "끝 상태: 실패(인자 오류)\n", ""))

    def test_folder_os_error_is_quiet(self):
        self.write_inputs()
        with mock.patch.object(cli.os, "mkdir", side_effect=PermissionError(13, "Permission denied", "x")):
            code, out, err = self.run_scorer()
        self.assertEqual((code, out, err), (cli.EXIT_OUTPUT, "끝 상태: 실패(출력 규칙)\n", ""))

    def test_unhashable_claim_fields_do_not_stop_sealed_batch(self):
        answers = fx.load_oracle()  # A는 빠진 키가 없는 사례: missingness_listed의 대체 조건 가지까지 돈다
        answers["cases"][0]["expected"]["required_evidence"] = sorted(cli.c3.FAMILY_TAGS["unit_value"])
        (self.sealed_dir / "answers.json").write_text(dump(answers), encoding="utf-8")
        digest = hashlib.sha256((self.sealed_dir / "answers.json").read_bytes()).hexdigest()
        (self.root / "eval" / "sealed_manifest.json").write_text(json.dumps({"schema_version": 2, "files": [
            {"dataset": "holdout40", "file_name": "answers.json", "sha256": digest,
             "created_at": "2026-09-25T09:00:00+09:00", "created_by": "시험"}]}), encoding="utf-8")
        a = copy.deepcopy(self.reports["A-composition"])
        a["claims"] += [dict({field: empty() for field in c1.CLAIM_FIELDS}, claim_type=kind)
                        for empty in (list, dict) for kind in c1.CLAIM_TYPES]
        next((self.root / "outputs" / "sealed" / a["run_id"]).iterdir()).write_text(dump(a), encoding="utf-8")
        self.write_inputs()
        code, out, err = self.run_scorer()
        self.assertEqual((code, out.splitlines(), err), (0, ["score-260925150000", "끝 상태: 완료"], ""))

    def test_huge_exponent_in_sealed_batch_finishes(self):
        a = copy.deepcopy(self.reports["A-composition"])
        a["claims"][0]["value"] = c1.loads_json("1e999999999")
        next((self.root / "outputs" / "sealed" / a["run_id"]).iterdir()).write_text(dump(a), encoding="utf-8")
        self.write_inputs()
        started = time.monotonic()
        code, out, err = self.run_scorer()
        self.assertLess(time.monotonic() - started, 30)
        self.assertEqual((code, out.splitlines(), err), (0, ["score-260925150000", "끝 상태: 완료"], ""))


if __name__ == "__main__":
    unittest.main()
