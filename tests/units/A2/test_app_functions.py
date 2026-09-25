"""단위 A2(app) 순수 함수 시험. streamlit 없이 돈다(화면 함수는 부르지 않는다).

고정 입력은 fixture/run_case-260926071424/(키 없는 재생 실행 `tradesentry run-case --snapshot controlled_fixture_v0 --policy
policy_v1 --mode full --case 850450-XA-202412 --replay eval/dev/smoke/850450-XA-202412.json`의 실행 결과 기록·보고서·trace
세 파일. NAT 폴더는 두지 않는다)다. 근거 ID 풀기(스냅샷 있음)는 단위 F2 시험의 도우미로 합성 픽스처를 임시 폴더에 만들어 쓴다.
"""
import ast
import json
import os
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from tradesentry import app
from tradesentry.contract import types
from tradesentry.runlog import trace as trace_log

from ..F2 import run_case_fixture as rf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FIXTURE_RUN = HERE / "fixture" / "run_case-260926071424"
CASE_ID = "850450-XA-202412"
# 상태 뜻 병기 문구에 있으면 안 되는 표현(부정·위법·원산지 판정을 암시하는 말. CLAUDE.md 개요, 개발 플랜 §7.2)
FORBIDDEN_TERMS = ("부정", "위법", "불법", "원산지", "조작", "탈세", "허위", "적발", "혐의", "위반", "정상 확정")
_SHARED: dict = {}


def setUpModule():
    tmp, snapshots = rf.materialize_fixture()
    _SHARED.update(tmp=tmp, snapshots=snapshots)


def tearDownModule():
    _SHARED.pop("tmp").cleanup()
    _SHARED.clear()


def fixture_build_path() -> Path:
    return _SHARED["snapshots"] / types.FIXTURE_SNAPSHOT_ID / "snapshot_build.sqlite"


def contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(contains_float(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return any(contains_float(v) for v in value)
    return False


class ImportShapeTest(unittest.TestCase):
    def test_streamlit_is_imported_only_inside_functions(self):
        tree = ast.parse((ROOT / "src" / "tradesentry" / "app.py").read_text(encoding="utf-8"))
        top_level = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        names = [a.name for n in top_level if isinstance(n, ast.Import) for a in n.names] + \
                [n.module for n in top_level if isinstance(n, ast.ImportFrom)]
        self.assertNotIn("streamlit", names)
        self.assertTrue(any(isinstance(n, ast.Import) and any(a.name == "streamlit" for a in n.names)
                            for n in ast.walk(tree)), "화면 함수 안에서 streamlit을 import한다")

    def test_module_import_does_not_pull_streamlit(self):
        self.assertIn("tradesentry.app", sys.modules)
        self.assertNotIn("streamlit", sys.modules)


class RunDirListingTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.outputs = Path(tmp.name) / "outputs"
        for name in ("run_case-260926071424", "run_case-260926071439", "run_case-260926071437", "evaluate-260926070000",
                     "sealed", ".download-run_case-260926080000", ".quarantine-run_case-260926080001", "run_case-bad"):
            (self.outputs / name).mkdir(parents=True)
        (self.outputs / "sealed" / "run_case-260926090000").mkdir()
        (self.outputs / "run_case-260926099999.txt").write_text("", encoding="utf-8")  # 파일은 폴더가 아니다

    def test_lists_only_top_level_run_case_dirs_newest_first(self):
        self.assertEqual(app.list_run_dirs(self.outputs),
                         ["run_case-260926071439", "run_case-260926071437", "run_case-260926071424"])

    def test_missing_outputs_is_empty(self):
        self.assertEqual(app.list_run_dirs(self.outputs / "none"), [])

    def test_typed_relative_path(self):
        self.assertEqual(app.relative_run_dir("outputs/run_case-260926071424"), "run_case-260926071424")
        self.assertEqual(app.relative_run_dir(" run_case-260926071424/ "), "run_case-260926071424")
        for bad in ("outputs/sealed/run_case-260926071424", "run_case-1", "outputs/evaluate-260926071424", "", None,
                    "../outputs/run_case-260926071424"):
            with self.subTest(bad=bad):
                self.assertIsNone(app.relative_run_dir(bad))

    def test_snapshot_listing_needs_build_file(self):
        root = self.outputs.parent / "data" / "snapshots"
        (root / "a_has").mkdir(parents=True)
        (root / "a_has" / "snapshot_build.sqlite").write_bytes(b"")
        (root / "b_none").mkdir()
        (root / "c_other").mkdir()
        (root / "c_other" / "snapshot.sqlite").write_bytes(b"")
        self.assertEqual(app.list_snapshots(root), ["a_has"])
        self.assertEqual(app.list_snapshots(root / "missing"), [])


class LoadRunTest(unittest.TestCase):
    def test_reads_three_files_with_decimals(self):
        loaded = app.load_run(FIXTURE_RUN)
        self.assertEqual(loaded["run_id"], "run_case-260926071424")
        self.assertEqual(loaded["missing"], [])
        self.assertEqual(loaded["record"]["case_id"], CASE_ID)
        self.assertEqual(loaded["record"]["execution_status"], "COMPLETED")
        self.assertEqual(loaded["report"]["review_status"], "MONITOR")
        self.assertEqual(len(loaded["trace"]), 61)
        self.assertIsInstance(loaded["report"]["claims"][0]["value"], Decimal)
        self.assertFalse(contains_float(loaded["report"]))

    def test_missing_files_are_reported_not_fatal(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run_case-260926000000"
            run_dir.mkdir()
            (run_dir / "runlog_trace-260926000000.jsonl").write_text(
                (FIXTURE_RUN / "runlog_trace-260926071424.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
            loaded = app.load_run(run_dir)
            self.assertEqual(loaded["missing"], ["record", "report"])
            self.assertIsNone(loaded["record"])
            self.assertEqual(len(loaded["trace"]), 61)
            model = app.screen_model(run_dir, resolve_rows=False)  # 기록·보고서가 없어도 화면 모형은 만들어진다
            self.assertEqual(model["case"]["case_id"], CASE_ID)  # run_start에서 가져온다
            self.assertEqual(model["header"]["status_after"]["code"], None)
            self.assertIn("null", model["header"]["status_after"]["text"])
            self.assertEqual(model["claims"], [])
        with self.assertRaises(FileNotFoundError):
            app.load_run(Path(tmp) / "run_case-260926000001")


class DerivedTablesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        loaded = app.load_run(FIXTURE_RUN)
        cls.record, cls.report, cls.trace = loaded["record"], loaded["report"], loaded["trace"]

    def test_case_heading(self):
        heading = app.case_heading(CASE_ID, {"CN": "중국"}, {"850450": "기타 전원공급장치"})
        self.assertEqual((heading["hs6"], heading["partner"], heading["month"], heading["baseline_month"]),
                         ("850450", "XA", "202412", "202312"))
        self.assertIn("2024년 12월", heading["text"])
        self.assertIn("기준월 2023년 12월", heading["text"])
        self.assertIn("XA(합성 또는 이름 없음)", heading["text"])
        self.assertIn("중국", app.case_heading("850432-CN-202301", {"CN": "중국"})["text"])
        self.assertFalse(app.case_heading("nonsense")["parsed"])

    def test_header_before_after(self):
        header = app.header_model(self.record, self.report)
        self.assertEqual(header["status_before"]["code"], "PRE_INVESTIGATION")
        self.assertEqual(header["status_before"]["label"], "조사 전 경보")
        self.assertEqual(header["status_after"]["code"], "MONITOR")
        self.assertEqual(header["signal_status"], {"unit_value": "MONITOR", "share": "NOT_TRIGGERED"})
        self.assertEqual(header["signal_status_text"], "단가 모니터링(MONITOR), 점유율 미발동(NOT_TRIGGERED)")
        self.assertIs(header["unresolved_evidence"], False)

    def test_header_when_not_completed(self):
        record = {**self.record, "execution_status": "FAILED", "review_status_final": None, "signal_status": None,
                  "errors": [{"code": "CODE_ERROR"}]}
        header = app.header_model(record, None)
        self.assertIsNone(header["status_after"]["code"])
        self.assertIn("COMPLETED가 아니어서", header["status_after"]["text"])
        self.assertEqual(header["signal_status_text"], "없음")

    def test_trigger_table_uses_claims_then_trace(self):
        rows = app.trigger_table(self.record, self.report, self.trace, {"unit_value": 30, "share": 10})
        self.assertEqual([r["signal"] for r in rows], ["unit_value", "share"])
        unit, share = rows
        self.assertEqual((unit["metric"], unit["value"], unit["unit"], unit["threshold"], unit["triggered"]),
                         ("r_U", Decimal("-40.0"), "%", 30, True))
        self.assertTrue(unit["source"].startswith("보고서 주장 "))
        self.assertEqual((share["metric"], share["value"], share["unit"], share["threshold"], share["triggered"]),
                         ("d_s", Decimal("-4.0"), "pp", 10, False))
        self.assertTrue(share["source"].startswith("trace 지표 d_s-"))
        self.assertEqual(unit["basis"], "composition_explained")
        without = app.trigger_table(self.record, self.report, self.trace, None)
        self.assertEqual([r["threshold"] for r in without], [None, None])

    def test_tool_table_pairs_calls_with_results(self):
        rows = app.tool_table(self.trace)
        self.assertEqual(len(rows), 7)
        self.assertEqual([r["tool"] for r in rows], ["check_comparability", "get_history", "compare_partners", "decompose_hs",
                                                    "verify_evidence", "compare_partners", "verify_evidence"])
        self.assertEqual([r["source"] for r in rows][:4], ["code", "code", "model", "model"])
        self.assertTrue(all(r["ok"] is True for r in rows))
        self.assertEqual(rows[1]["metric_count"], 10)
        self.assertEqual(rows[0]["retryable_error"], None)
        self.assertFalse(any(r["blocked"] for r in rows))
        self.assertEqual(rows[5]["args"], "partners=XB")  # 모델이 고른 비교국 인자
        summary = app.model_summary(self.trace, self.record)
        self.assertEqual((summary["model_requests"], summary["model_attempts"], summary["model_errors"]), (5, 13, 8))
        self.assertEqual(summary["tokens_in"], 33359)

    def test_budget_block_row(self):
        trace = [{"seq": 1, "event": "budget_block", "stage": "basic",
                  "data": {"tool": "get_history", "args": {}, "reason": "tool_attempts", "limit": 8}}]
        rows = app.tool_table(trace)
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["blocked"])
        self.assertIn("reason=tool_attempts", rows[0]["note"])

    def test_claims_mark_code_added(self):
        self.assertEqual(app.code_added_claim_ids(self.trace), ["e3", "e4", "e5", "e6"])
        rows = app.claims_table(self.report, self.trace)
        self.assertEqual([(r["claim_id"], r["origin"]) for r in rows],
                         [("c1", "모델(검증 통과)"), ("c2", "모델(검증 통과)"), ("e3", "코드가 덧붙임"), ("e4", "코드가 덧붙임"),
                          ("e5", "코드가 덧붙임"), ("e6", "코드가 덧붙임")])
        self.assertEqual(set(rows[0]) - {"origin"}, set(types.CLAIM_FIELDS))
        self.assertEqual(rows[0]["value"], Decimal("-40.0"))

    def test_timeline_rows_and_flags(self):
        timeline = app.timeline_table(self.trace)
        rows = timeline["rows"]
        self.assertEqual(rows[0]["phase"], "PRE_INVESTIGATION")
        self.assertEqual(rows[0]["seq"], 0)
        self.assertEqual(len(rows), 13)  # 처음 표시 1 + state_change 9 + validator_result 3
        self.assertEqual([r["phase"] for r in rows][1:], ["rule_reference", "draft", "evidence_claims", "validator_result",
                                                          "after_critic", "code_finding", "validator_result", "rule_reference",
                                                          "revised", "evidence_claims", "validator_result", "final"])
        self.assertEqual(timeline["flags"], {"status_aggregated": False, "revision_discarded": False, "code_finding": True,
                                             "draft_discarded": False})
        self.assertIn("compare_partners", next(r for r in rows if r["phase"] == "code_finding")["note"])
        self.assertEqual(rows[-1]["review_status"], "MONITOR")

    def test_timeline_flags_for_other_phases(self):
        trace = [{"seq": 1, "event": "state_change", "stage": "basic",
                  "data": {"phase": "status_aggregated", "review_status": "MONITOR", "model_review_status": "MAINTAIN",
                           "signal_status": {"unit_value": "MONITOR", "share": "NOT_TRIGGERED"}, "unresolved_evidence": False}},
                 {"seq": 2, "event": "state_change", "stage": "revision",
                  "data": {"phase": "revision_discarded", "review_status": "MAINTAIN", "signal_status": None,
                           "blocked_by": "validator", "would_be_cause": "VALIDATOR_BLOCKED", "kept_report_id": "r1"}}]
        timeline = app.timeline_table(trace)
        self.assertTrue(timeline["flags"]["status_aggregated"] and timeline["flags"]["revision_discarded"])
        self.assertIn("MAINTAIN → 코드 집계 MONITOR", timeline["rows"][1]["note"])
        self.assertIn("validator가 막아 원안 유지", timeline["rows"][2]["note"])

    def test_chart_bars_from_verified_values(self):
        case = app.case_heading(CASE_ID)
        chart = app.chart_data(self.report, self.trace, case)
        self.assertEqual([r["value"] for r in chart["bars"]["unit_value"]], [Decimal("6.00"), Decimal("3.60")])
        self.assertEqual([r["month"] for r in chart["bars"]["unit_value"]], ["202312", "202412"])
        self.assertEqual([r["value"] for r in chart["bars"]["share"]], [Decimal("10.0"), Decimal("6.0")])
        self.assertIsNone(chart["series"])  # get_history는 기준월·비교월 두 달의 U만 준다
        self.assertEqual(chart["units"], {"unit_value": "USD/kg", "share": "%"})
        self.assertEqual(app.chart_data(self.report, self.trace, {"parsed": False})["bars"], {"unit_value": None, "share": None})

    def test_chart_series_when_trace_has_monthly_unit_values(self):
        def metric(period, value):
            return {"metric_id": f"U-{period}", "inputs": {"metric": "U", "partner": "XA", "period": period},
                    "value": Decimal(value), "unit": "USD/kg", "evidence_ids": []}
        trace = [{"seq": 1, "event": "tool_result", "stage": "basic", "data": {"tool": "get_history", "ok": True, "envelope": {
            "tool": "get_history", "metrics": [metric("202312", "6.00"), metric("202401", "5.50"), metric("202412", "3.60")]}}}]
        chart = app.chart_data(None, trace, app.case_heading(CASE_ID))
        self.assertEqual([r["month"] for r in chart["series"]], ["202312", "202401", "202412"])
        self.assertEqual([r["baseline_value"] for r in chart["series"]], [Decimal("6.00")] * 3)
        self.assertFalse(contains_float(chart))


class EvidenceResolutionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = app.load_run(FIXTURE_RUN)["report"]

    def test_disabled_lists_ids_only(self):
        result = app.resolve_evidence(self.report["evidence_ids"], "controlled_fixture_v0", enabled=False)
        self.assertFalse(result["available"])
        self.assertEqual([set(r) for r in result["rows"]], [{"evidence_id"}] * 6)

    def test_missing_snapshot_lists_ids_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = app.resolve_evidence(self.report["evidence_ids"], "controlled_fixture_v0",
                                          snapshot_path=Path(tmp) / "none.sqlite")
        self.assertFalse(result["available"])
        self.assertIn("스냅샷 없음", result["note"])
        self.assertEqual([r["evidence_id"] for r in result["rows"]], self.report["evidence_ids"])
        self.assertNotIn(tmp, result["note"])
        self.assertFalse(app.resolve_evidence(["ev:x:observation:1"], None)["available"])

    def test_resolves_rows_with_snapshot(self):
        result = app.resolve_evidence(self.report["evidence_ids"], "controlled_fixture_v0", snapshot_path=fixture_build_path())
        self.assertTrue(result["available"])
        self.assertEqual(result["note"], "스냅샷 controlled_fixture_v0에서 6/6건이 풀렸다")
        first = result["rows"][0]
        self.assertEqual((first["resolved"], first["table"], first["hs_code"], first["partner_code"], first["month"]),
                         (True, "observation", "850450", "XA", "202312"))
        self.assertEqual((first["amount_usd"], first["net_weight_kg"], first["observation_status"]), (600, 100, "OBSERVED"))
        self.assertFalse(contains_float(result))
        broken = app.resolve_evidence(["ev:controlled_fixture_v0:observation:999999999", "nonsense"], "controlled_fixture_v0",
                                      snapshot_path=fixture_build_path())
        self.assertEqual([(r["resolved"], r["failed_rule"]) for r in broken["rows"]], [(False, 4), (False, 1)])

    def test_screen_model_with_snapshot_and_without_absolute_paths(self):
        model = app.screen_model(FIXTURE_RUN, snapshot_path=fixture_build_path())
        self.assertTrue(model["evidence"]["available"])
        text = trace_log.dumps(model)  # float가 있으면 여기서 실패한다
        for forbidden in (str(ROOT), str(_SHARED["snapshots"]), os.path.expanduser("~")):
            self.assertNotIn(forbidden, text)
        self.assertEqual(model["run_dir"], "outputs/run_case-260926071424")


class WordingTest(unittest.TestCase):
    def test_status_meanings_have_label_code_and_no_forbidden_terms(self):
        for code, text in app.STATUS_MEANING.items():
            with self.subTest(code=code):
                self.assertIn(f"({code})", text)
                self.assertIn(app.STATUS_LABEL[code], text)
                for term in FORBIDDEN_TERMS:
                    self.assertNotIn(term, text)
        self.assertEqual(set(app.STATUS_MEANING), set(types.SIGNAL_STATUSES) | {types.PRE_INVESTIGATION})
        for label in list(app.PHASE_LABEL.values()) + list(app.STATUS_LABEL.values()):
            for term in FORBIDDEN_TERMS:
                self.assertNotIn(term, label)
        self.assertEqual(app.status_text("MAINTAIN"), app.STATUS_MEANING["MAINTAIN"])
        self.assertEqual(app.status_text("WEIRD"), "WEIRD(정해진 판정 상태가 아님)")

    def test_footer_keeps_disclaimer(self):
        self.assertIn("부정·위법·원산지 판정이나 실제 통관 조치가 아니다", app.FOOTER_DISCLAIMER)
        self.assertIn("담당자의 다음 업무 제안이다", app.FOOTER_DISCLAIMER)
        self.assertIn("여러 사용자·계정·권한·실시간 수집·운영 배포는 없다", app.FOOTER_SCOPE)


class RunPanelTest(unittest.TestCase):
    def test_build_args(self):
        self.assertEqual(app.build_run_case_args("controlled_fixture_v0", "policy_v1", "full", CASE_ID),
                         ["run-case", "--snapshot", "controlled_fixture_v0", "--policy", "policy_v1", "--mode", "full",
                          "--case", CASE_ID])
        self.assertEqual(app.build_run_case_args("controlled_fixture_v0", "policy_v1", "full", CASE_ID,
                                                 "eval/dev/smoke/850450-XA-202412.json")[-2:],
                         ["--replay", "eval/dev/smoke/850450-XA-202412.json"])
        bad = [("bad id!", "policy_v1", "full", CASE_ID, None), ("controlled_fixture_v0", "v1", "full", CASE_ID, None),
               ("controlled_fixture_v0", "policy_v1", "batch", CASE_ID, None),
               ("controlled_fixture_v0", "policy_v1", "full", "A-composition", None),
               ("controlled_fixture_v0", "policy_v1", "full", CASE_ID, "/abs/replay.json"),
               ("controlled_fixture_v0", "policy_v1", "full", CASE_ID, "../x.json")]
        for args in bad:
            with self.subTest(args=args), self.assertRaises(ValueError) as caught:
                app.build_run_case_args(*args)
            self.assertNotIn("bad id!", str(caught.exception))

    def test_command_uses_same_entry_point_as_cli(self):
        command = app.run_case_command(["run-case", "--snapshot", "s"])
        self.assertEqual(command[:3], [sys.executable, "-m", "tradesentry.cli"])
        self.assertEqual(command[3], "run-case")

    def test_replay_file_lookup(self):
        self.assertEqual(app.replay_file_for(CASE_ID, ROOT), "eval/dev/smoke/850450-XA-202412.json")
        self.assertIsNone(app.replay_file_for("850450-XZ-202412", ROOT))
        self.assertIsNone(app.replay_file_for("../etc", ROOT))

    def test_key_and_child_env(self):
        self.assertFalse(app.key_present({}))
        self.assertFalse(app.key_present({"NVIDIA_API_KEY": ""}))
        self.assertTrue(app.key_present({"NVIDIA_API_KEY": "x"}))
        env = app.child_env({"NVIDIA_API_KEY": "x", "DATA_GO_KR_SERVICE_KEY": "y", "TRADESENTRY_SEALED_DIR": "z", "PATH": "p"})
        self.assertEqual(env, {"NVIDIA_API_KEY": "x", "PATH": "p"})

    def test_new_dirs_and_stdout_parsing(self):
        self.assertEqual(app.new_run_dirs(["run_case-1"], ["run_case-1", "run_case-3", "run_case-2"]), ["run_case-3", "run_case-2"])
        stdout = ("outputs/run_case-260926071424/runlog_trace-260926071424.jsonl\n"
                  "outputs/run_case-260926071424/workflow_nat_wrap-260926071424\n오류: 무엇\n")
        self.assertEqual(app.output_run_dirs(stdout), ["run_case-260926071424"])
        self.assertEqual(app.output_run_dirs(""), [])

    def test_redact_hides_paths_and_key_shapes(self):
        # 경로·키 모양은 검사기(scripts/secret_scan.py)에 걸리지 않게 조각을 이어 만든다
        home_path, tmp_path = "/" + "Users/someone/x.py", "/" + "private/var" + "/folders/ab"
        text = f"File \"{home_path}\", line 1; {tmp_path}; nv" + "api-abcdefghijklmnop rest"
        shown = app.redact(text)
        self.assertNotIn("/" + "Users/", shown)
        self.assertNotIn("/" + "private/", shown)
        self.assertNotIn("abcdefghijklmnop", shown)
        self.assertIn("<로컬 경로>", shown)
        self.assertEqual(app.redact(None), "")

    def test_wall_limit_from_model_config(self):
        self.assertEqual(app.wall_limit_seconds(ROOT), 300)
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(app.wall_limit_seconds(Path(tmp)), 300)  # 설정이 없으면 기본값

    def test_run_case_once_reports_exit_code_without_network(self):
        # 실제 run-case 대신 인자 오류로 곧바로 끝나는 호출(도움말 종료 코드)로 하위 프로세스 배관만 확인한다
        result = app.run_case_once(["run-case", "--snapshot"], repo_root=ROOT, timeout_s=120,
                                   env={k: v for k, v in os.environ.items() if k != "NVIDIA_API_KEY"})
        self.assertFalse(result["timed_out"])
        self.assertNotEqual(result["returncode"], 0)
        self.assertEqual(result["command"], "tradesentry run-case --snapshot")
        self.assertNotIn(str(ROOT), result["stdout"] + result["stderr"])


class GoldenShapeTest(unittest.TestCase):
    def test_expected_json_matches_run_output_shape(self):
        expected = json.loads((HERE / "expected.json").read_text(encoding="utf-8"), parse_float=Decimal)
        self.assertEqual(set(expected), {"run_id", "run_dir", "files", "missing", "case", "header", "thresholds", "triggers",
                                         "chart", "tools", "model", "claims", "narrative", "hypotheses", "validator_findings",
                                         "timeline", "evidence", "footer"})
        self.assertFalse(expected["evidence"]["available"])


if __name__ == "__main__":
    unittest.main()
