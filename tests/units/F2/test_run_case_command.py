"""조립 작업 AS2: tradesentry run-case 조립 시험(명령 하나를 처음부터 끝까지 돌려 기대 출력과 비교한다). 네트워크와 키 없이
돈다. 실제 NIM은 부르지 않는다: 모델 모드(agent·full·freeform)는 모델 전송 자리(dispatch.run_case_transport)만 정해 둔
답을 차례로 돌려주는 가짜(tests/units/I7/fakes.py ScriptedTransport)로 바꾼다. 나머지는 모두 실제 단위다.

- 실제로 도는 것: 단위 F1 → 단위 F2 run-case → K4 load_policy(저장소 configs/policy_dev.json, dev-0.1) → K3(정본 빌드를
  읽기 전용으로 연다) → 사례 다시 만들기(AS1 어댑터 → X1·X2 → P1 → P2) → 흐름 조정 I12(도구 I1~I5·예산 I6, 조사자 I10·
  Critic I11·모델 호출 I7, 정책 P3~P5, 보고서 R1·R2, 검증기 R3·R4) → NAT 감싸기 I13 → trace L1·실행 결과 기록 L2·L3 → 출력 파일.
- 자료: 합성 시험자료 controlled_fixture_v0(사례 A·B·C)와 두 신호 스냅샷 as2_two_way(run_case_fixture.py). 실자료
  스냅샷 v1·v2로는 돌리지 않는다. 실자료 거부 시험은 AS1 시험 도우미의 작은 스냅샷을 source_kind real로 만든 것을 쓴다.
- 바꾸는 것: 스냅샷들의 뿌리(dal.query.SNAPSHOTS_ROOT), CLI 실행 폴더의 부모(dispatch.OUTPUT_PARENT, 시험마다 새 임시
  폴더), 모델 전송 자리. 저장소의 data/·outputs/는 건드리지 않는다. 두 신호 스냅샷은 자료 묶음 표(RUN_CASE_DATASETS)에
  없어 그 시험 안에서만 한 줄을 더한다.
- 출력 파일 이름의 도메인명은 docs/plan/UNITS.md §3.6·§3.7·§3.13 행 글자 그대로 적는다(코드 상수를 쓰지 않는다).
"""
import contextlib
import io
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

from tradesentry.cli import dispatch
from tradesentry.dal import query
from tradesentry.reports import claims as report_claims
from tradesentry.runlog import cause_codes
from tradesentry.runlog import trace as trace_log
from tradesentry.tools import check_comparability, compare_partners, decompose_hs, get_history, verify_evidence
from tradesentry.validator import validate
from tradesentry.workflow import orchestrate

from ..I7.fakes import NoNetworkMixin, ScriptedTransport, ok_body
from ..I12.harness import critic_answer, tools_answer
from . import detect_fixture as df
from . import run_case_fixture as rf

SID = "controlled_fixture_v0"
T, N = "TRIGGERED", "NOT_TRIGGERED"
# 사례 A·B·C(단위 S4 이름표 → case_id)와 기대 판정(eval/dev/oracle_ABC.json: 모니터링·검토 유지·자료 보류)
CASES = {"A": "850450-XA-202412", "B": "850431-XB-202412", "C": "850432-XC-202412"}
EXPECTED = {"A": ("MONITOR", {"unit_value": "MONITOR", "share": N}),
            "B": ("MAINTAIN", {"unit_value": "MAINTAIN", "share": N}),
            "C": ("HOLD", {"unit_value": "HOLD", "share": N})}
# 실행 결과 기록의 실행 쪽 키(자료 계약 §8.1에서 정답 대조 채점의 세 키를 뺀 21개, 글자 그대로)
RUN_RECORD_KEYS = ["run_id", "case_id", "dataset", "mode", "policy_version", "rulebook_version", "snapshot_id",
                   "grouping_version", "code_version", "review_status_final", "signal_status", "unresolved_evidence",
                   "execution_status", "tool_attempts", "model_requests", "tokens_in", "tokens_out", "wall_ms",
                   "critic_used", "revision_used", "errors"]
NARRATIVE = "단가 신호를 하위품목 구성과 허용된 비교국 자료로 점검했다."
_SHARED: dict = {}


def setUpModule():
    """합성 시험자료와 두 신호 스냅샷을 한 번만 만든다(임시 폴더). 만들지 못하면 모듈 시험이 모두 실패한다."""
    tmp, snapshots = rf.materialize_fixture()
    rf.install_two_way(snapshots.parent)  # snapshots.parent/snapshots = 같은 뿌리에 as2_two_way를 둔다
    _SHARED.update(tmp=tmp, snapshots=snapshots)


def tearDownModule():
    _SHARED.pop("tmp").cleanup()
    _SHARED.clear()


def call(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = dispatch.main(argv)
    return code, out.getvalue(), err.getvalue()


def argv(case_id: str, mode: str, snapshot_id: str = SID) -> list[str]:
    return ["run-case", "--snapshot", snapshot_id, "--policy", "dev-0.1", "--mode", mode, "--case", case_id]


class RunCaseBase(NoNetworkMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.outputs = Path(tmp.name) / "outputs"
        for target, name, value in ((query, "SNAPSHOTS_ROOT", _SHARED["snapshots"]),
                                    (dispatch, "OUTPUT_PARENT", self.outputs)):
            patcher = mock.patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def files(self, out: str) -> dict:
        """표준 출력의 상대경로(outputs/부터) → {도메인명: 경로}. 실행 폴더는 하나다."""
        found = {}
        for line in out.splitlines():
            parts = line.split("/")
            self.assertEqual(parts[0], "outputs")
            self.assertEqual(len(parts), 3)
            run_id, name = parts[1], parts[2]
            self.assertRegex(run_id, r"^run_case-\d{12}$")
            stamp = run_id.split("-")[1]
            domain = name.split("-")[0]
            self.assertTrue(name.startswith(f"{domain}-{stamp}"), name)
            found[domain] = self.outputs / run_id / name
        return found

    def read_json(self, path: Path) -> dict:
        return trace_log.loads(path.read_text(encoding="utf-8"))

    def trace(self, files: dict) -> list[dict]:
        return trace_log.read_records(files["runlog_trace"])

    def run_ok(self, case_id: str, mode: str, script: list | None = None, snapshot_id: str = SID) -> tuple:
        transport = ScriptedTransport(script or [])
        with mock.patch.object(dispatch, "run_case_transport", lambda config: transport):
            code, out, err = call(argv(case_id, mode, snapshot_id))
        self.assertEqual((code, err), (0, ""), err)
        self.assertEqual(transport.script, [], "준비한 모델 답을 모두 써야 한다")
        files = self.files(out)
        return files, self.read_json(files["runlog_run_record"]), self.read_json(files["reports_render_ko"]), transport


def envelopes_of(case_id: str) -> tuple[dict, list]:
    """사례의 도구 봉투(I1·I2·I4·I3 순서)를 시험이 직접 조회한다. metric_id와 근거 ID는 조회 순번과 관계없다."""
    parsed = dict(zip(("hs6", "partner", "month"), case_id.split("-")))
    parsed["baseline_month"] = f"{int(parsed['month'][:4]) - 1}{parsed['month'][4:]}"
    signals = {"unit_value": T, "share": N}
    case = {"case_id": case_id, **parsed, "signals": signals, "snapshot_id": SID, "policy_version": "dev-0.1"}
    base = {"case_id": case_id, "snapshot_id": SID, "scope": {k: parsed[k] for k in ("hs6", "partner", "month",
                                                                                      "baseline_month")},
            "policy_version": "dev-0.1", "grouping_version": "g0"}
    with query.open_snapshot(SID) as snap:
        envs = [unit.query(snap, dict(base, attempt=n)) for n, unit in
                enumerate((check_comparability, get_history, decompose_hs, compare_partners), start=1)]
    return case, envs


def draft_for(label: str, mode: str) -> dict:
    """사례의 모델 초안(가짜 모델의 답). 판정은 oracle, 주장은 실제 봉투의 metric_id·근거 ID(틀 채우기) 또는 틀 채우기가
    만든 typed claim(freeform)이다. 설명 문장에는 숫자를 쓰지 않는다."""
    case, envs = envelopes_of(CASES[label])
    claims = orchestrate.checklist_claims(case, envs)
    if mode == "freeform":
        statuses = orchestrate._statuses_of(envs)
        claims = report_claims.fill(case, orchestrate._metrics_of(envs), statuses,
                                    orchestrate._requests_of({"claims": claims}, statuses))["claims"]
    review, signal_status = EXPECTED[label]
    return {"review_status": review, "signal_status": signal_status, "claims": claims, "narrative": NARRATIVE,
            "hypotheses": []}


def draft_answer(draft: dict) -> dict:
    return {"body": ok_body(trace_log.dumps(draft), prompt_tokens=1500, completion_tokens=150)}


def script_for(label: str, mode: str) -> list:
    """모델 답 순서: 조사자가 도구 두 개(decompose_hs·compare_partners)를 한 차례에 부르고, 초안을 쓰고, Critic(full·
    freeform)은 수정을 요청하지 않는다."""
    steps = [tools_answer("decompose_hs", "compare_partners"), draft_answer(draft_for(label, mode))]
    if mode in ("full", "freeform"):
        steps.append(critic_answer(needs_revision=False))
    return steps


class ChecklistTest(RunCaseBase):
    def test_cases_a_b_c_end_to_end(self):
        for label in ("A", "B", "C"):
            with self.subTest(case=label):
                files, record, report, _ = self.run_ok(CASES[label], "checklist")
                self.assertEqual(sorted(files), ["reports_render_ko", "runlog_run_record", "runlog_trace",
                                                 "workflow_nat_wrap"])
                self.assertEqual(list(record), RUN_RECORD_KEYS)
                review, signal_status = EXPECTED[label]
                self.assertEqual((record["review_status_final"], record["signal_status"]), (review, signal_status))
                self.assertEqual(record["execution_status"], cause_codes.COMPLETED)
                self.assertEqual({k: record[k] for k in ("case_id", "dataset", "mode", "policy_version",
                                                         "rulebook_version", "snapshot_id", "grouping_version")},
                                 {"case_id": CASES[label], "dataset": SID, "mode": "checklist",
                                  "policy_version": "dev-0.1", "rulebook_version": "RB-1", "snapshot_id": SID,
                                  "grouping_version": "g0"})
                self.assertEqual((record["tool_attempts"], record["model_requests"], record["tokens_in"],
                                  record["tokens_out"], record["critic_used"], record["revision_used"], record["errors"]),
                                 (5, 0, 0, 0, False, False, []))
                self.assertRegex(record["code_version"], r"^([0-9a-f]{40}|unknown)$")
                self.assertEqual((report["review_status"], report["signal_status"], report["validator_findings"]),
                                 (review, signal_status, []))
                self.assertEqual(report["run_id"], record["run_id"])
                events = self.trace(files)
                tools = [e["data"]["tool"] for e in events if e["event"] == "tool_call"]
                self.assertEqual(tools, ["check_comparability", "get_history", "decompose_hs", "compare_partners",
                                         "verify_evidence"])
                verified = [e["data"]["envelope"] for e in events
                            if e["event"] == "tool_result" and e["data"]["tool"] == "verify_evidence"]
                self.assertTrue(verified[0]["comparability"]["ok"])
                self.assertTrue((files["workflow_nat_wrap"] / "nat_trace.jsonl").is_file())

    def test_synthetic_cases_query_five_peers_with_the_data_grouping_version(self):
        """합성 자료의 grouping_version은 자료 안 값(g0)이고, 사례마다 비교국 5개가 실제로 조회된다(DT3 평가 검토 권고 6:
        peers(…, "g1")은 오류 없이 빈 목록이라 조용히 비교가 빠질 수 있다)."""
        for label in ("A", "B", "C"):
            with self.subTest(case=label):
                files, record, _, _ = self.run_ok(CASES[label], "checklist")
                [peers] = [e["data"]["envelope"]["comparability"] for e in self.trace(files)
                           if e["event"] == "tool_result" and e["data"]["tool"] == "compare_partners"]
                self.assertEqual((peers["grouping_version"], peers["comparable"], len(peers["peers"])), ("g0", True, 5))
                self.assertEqual(record["grouping_version"], "g0")

    def test_c_type_status_becomes_one_claim_per_missing_hs10(self):
        files, _, report, _ = self.run_ok(CASES["C"], "checklist")
        status_claims = [c for c in report["claims"] if c["claim_type"] == "data_status"]
        self.assertEqual([(c["metric"], c["value"]) for c in status_claims],
                         [("observation_status@8504321000", "REQUEST_FAILED"),
                          ("observation_status@8504322000", "REQUEST_FAILED")])
        self.assertEqual(len({c["claim_id"] for c in status_claims}), 2)
        self.assertEqual(status_claims[0]["evidence_ids"], status_claims[1]["evidence_ids"])  # 상태 행 하나
        [verify_call] = [e["data"]["args"] for e in self.trace(files)
                         if e["event"] == "tool_call" and e["data"]["tool"] == "verify_evidence"]
        self.assertEqual(verify_call["evidence_ids"], status_claims[0]["evidence_ids"])  # 펼친 ID가 아니라 근거 ID

    def test_report_numbers_keep_their_display_digits(self):
        files, _, _, _ = self.run_ok(CASES["A"], "checklist")
        text = files["reports_render_ko"].read_text(encoding="utf-8")
        self.assertIn('"value":3.60', text)  # 끝자리 0(자료 계약 §9.1). 문자열 "3.60"이 아니다
        self.assertNotIn('"value":"', text.replace('"value":"REQUEST', ""))

    def test_validator_receives_policy_thresholds_as_numbers(self):
        seen = []

        def spy(inp):
            seen.append(inp.get("thresholds"))
            return real(inp)
        real = validate.run
        with mock.patch.object(validate, "run", spy):
            self.run_ok(CASES["B"], "checklist")
        self.assertEqual(seen, [[30, 10]])

    def test_tool_requests_carry_versions_attempt_and_only_received_envelopes(self):
        seen: list[tuple[str, dict]] = []
        patchers = []
        for unit in (check_comparability, get_history, decompose_hs, compare_partners, verify_evidence):
            def spy(snap, inp, _unit=unit, _real=unit.query):
                seen.append((_unit.__name__.rsplit(".", 1)[-1], json.loads(trace_log.dumps(inp))))
                return _real(snap, inp)
            patchers.append(mock.patch.object(unit, "query", spy))
        with contextlib.ExitStack() as stack:
            for patcher in patchers:
                stack.enter_context(patcher)
            files, _, _, _ = self.run_ok(CASES["A"], "checklist")
        self.assertEqual([name for name, _ in seen], ["check_comparability", "get_history", "decompose_hs",
                                                      "compare_partners", "verify_evidence"])
        self.assertEqual([inp["attempt"] for _, inp in seen], [1, 2, 3, 4, 5])
        for name, inp in seen:
            self.assertEqual((inp["policy_version"], inp["grouping_version"]), ("dev-0.1", "g0"))
            self.assertEqual("envelopes" in inp, name == "verify_evidence")
        received = [json.loads(trace_log.dumps(e["data"]["envelope"])) for e in self.trace(files)
                    if e["event"] == "tool_result"][:4]
        self.assertEqual(seen[-1][1]["envelopes"], received)  # 흐름이 받은 봉투 원본 넷 그대로


class ModelModesTest(RunCaseBase):
    def test_modes_a_b_c_with_a_fake_model(self):
        for mode in ("agent", "full", "freeform"):
            for label in ("A", "B", "C"):
                with self.subTest(mode=mode, case=label):
                    files, record, report, transport = self.run_ok(CASES[label], mode, script_for(label, mode))
                    review, signal_status = EXPECTED[label]
                    self.assertEqual(list(record), RUN_RECORD_KEYS)
                    self.assertEqual((record["execution_status"], record["review_status_final"],
                                      record["signal_status"]), (cause_codes.COMPLETED, review, signal_status))
                    self.assertEqual((record["critic_used"], record["revision_used"]), (mode != "agent", False))
                    self.assertEqual(record["model_requests"], 2 if mode == "agent" else 3)
                    self.assertEqual(record["tool_attempts"], 5)  # I1·I2(코드) + 모델 비교 2 + verify_evidence
                    final = [e["data"] for e in self.trace(files) if e["event"] == "validator_result"][-1]
                    self.assertEqual((final["decision"], final["record_only"], final["schema_ok"]),
                                     ("pass", mode == "freeform", True))
                    self.assertEqual(report["validator_findings"], [])  # freeform도 틀 채우기가 만든 주장이라 사유 0
                    tools = [e["data"] for e in self.trace(files) if e["event"] == "tool_call"]
                    self.assertEqual([(t["tool"], t["source"]) for t in tools],
                                     [("check_comparability", "code"), ("get_history", "code"),
                                      ("decompose_hs", "model"), ("compare_partners", "model"),
                                      ("verify_evidence", "code")])
                    self.assertTrue(all("tools" in p for p in transport.payloads[:1]))

    def test_model_mode_keeps_c_type_expansion(self):
        _, _, report, _ = self.run_ok(CASES["C"], "agent", script_for("C", "agent"))
        self.assertEqual([c["metric"] for c in report["claims"] if c["claim_type"] == "data_status"],
                         ["observation_status@8504321000", "observation_status@8504322000"])


class TwoDirectionTest(RunCaseBase):
    """두 신호가 모두 발동한 사례에서 한 계열만의 문제가 다른 계열의 판정을 바꾸지 않는다(시나리오 10, MT1 결정 ⑦)."""

    def setUp(self):
        super().setUp()
        patcher = mock.patch.dict(dispatch.RUN_CASE_DATASETS, {rf.TWO_WAY_ID: SID})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_detect_finds_both_signals_in_the_two_cases(self):
        code, out, err = call(["detect", "--snapshot", rf.TWO_WAY_ID, "--policy", "dev-0.1"])
        self.assertEqual((code, err), (0, ""))
        detected = trace_log.loads((self.outputs / out.strip().split("/", 1)[1]).read_text(encoding="utf-8"))
        self.assertEqual([(c["case_id"], c["signals"]) for c in detected["cases"]],
                         [(rf.SHARE_ONLY_PROBLEM, {"unit_value": T, "share": T}),
                          (rf.UNIT_ONLY_PROBLEM, {"unit_value": T, "share": T})])

    def test_unit_value_only_problem(self):
        files, record, report, _ = self.run_ok(rf.UNIT_ONLY_PROBLEM, "checklist", snapshot_id=rf.TWO_WAY_ID)
        self.assertEqual((record["review_status_final"], record["signal_status"], record["unresolved_evidence"]),
                         ("MAINTAIN", {"unit_value": "HOLD", "share": "MAINTAIN"}, True))
        self.assertEqual(report["validator_findings"], [])

    def test_share_only_problem(self):
        files, record, report, _ = self.run_ok(rf.SHARE_ONLY_PROBLEM, "checklist", snapshot_id=rf.TWO_WAY_ID)
        self.assertEqual((record["review_status_final"], record["signal_status"], record["unresolved_evidence"]),
                         ("HOLD", {"unit_value": "MONITOR", "share": "HOLD"}, False))
        self.assertEqual(report["validator_findings"], [])


class RefusalTest(RunCaseBase):
    def test_not_a_case_out_of_scope_and_bad_format_end_with_1_and_no_record(self):
        for case_id, phrase in (("850450-XA-202312", "신호가 발동한 사례가 아니다"),
                                ("850450-XA-202201", "분석 범위"), ("850450-XZ-202412", "분석 범위"),
                                ("A-composition", "사례 식별자 형식")):
            with self.subTest(case=case_id):
                code, out, err = call(argv(case_id, "checklist"))
                self.assertEqual((code, out), (1, ""))
                self.assertIn(phrase, err)
                self.assertNotIn(case_id, err)  # 받은 값을 되풀이하지 않는다(N13)
        self.assertEqual([list(p.iterdir()) for p in self.outputs.iterdir()], [[]] * 4)  # 빈 실행 폴더만 남는다

    def test_unknown_policy_and_missing_snapshot(self):
        code, _, err = call(["run-case", "--snapshot", SID, "--policy", "dev-9.7", "--mode", "checklist", "--case",
                             CASES["A"]])
        self.assertEqual(code, 1)
        self.assertIn("PolicyError", err)
        code, _, err = call(argv(CASES["A"], "checklist", snapshot_id="no_such_snapshot"))
        self.assertEqual(code, 1)
        self.assertIn("SnapshotError", err)

    def test_real_snapshot_is_refused_before_reading_values(self):
        """실자료 스냅샷(source_kind real)은 관측 값을 읽기 전에 거부한다(병렬 개발 규칙 §7.2의 5, AS1과 같은 자리)."""
        with tempfile.TemporaryDirectory() as tmp:
            real_root = df.install(Path(tmp), df.WORLD_GAP, source_kind="real")
            reads = []
            spies = [mock.patch.object(query.Snapshot, name, lambda self, *a, _n=name, **k: reads.append(_n))
                     for name in ("parent_series", "world_series", "children", "peers", "row", "resolve")]
            with mock.patch.object(query, "SNAPSHOTS_ROOT", real_root), contextlib.ExitStack() as stack:
                for spy in spies:
                    stack.enter_context(spy)
                code, out, err = call(argv("850450-CN-202401", "checklist", snapshot_id="as1_detect_world_gap"))
        self.assertEqual((code, out, reads), (1, "", []))
        self.assertIn("합성 스냅샷(source_kind가 controlled)만 조사한다", err)

    def test_unlisted_synthetic_snapshot_has_no_dataset(self):
        code, _, err = call(argv(rf.UNIT_ONLY_PROBLEM, "checklist", snapshot_id=rf.TWO_WAY_ID))
        self.assertEqual(code, 1)
        self.assertIn("자료 묶음(dataset)을 정하지 못했다", err)

    def test_model_mode_without_a_key_is_recorded_not_raised(self):
        """모델 모드에서 키가 없으면 실행 기록을 남기고 1로 끝난다(FAILED, 키 값·경로는 쓰지 않는다)."""
        with mock.patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("NVIDIA_API_KEY", None)
            code, out, err = call(argv(CASES["A"], "agent"))
        self.assertEqual(code, 1)
        files = self.files(out)
        record = self.read_json(files["runlog_run_record"])
        self.assertNotEqual(record["execution_status"], cause_codes.COMPLETED)
        self.assertNotIn("reports_render_ko", files)
        self.assertIn(record["execution_status"], err)


if __name__ == "__main__":
    unittest.main()
