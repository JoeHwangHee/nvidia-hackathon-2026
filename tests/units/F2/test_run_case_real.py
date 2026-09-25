"""조립 작업 AS3 두 번째 PR: 실자료 스냅샷의 run-case(real_dev 계열만)와 evaluate의 real_dev 사례 목록 시험.

- 자료: 두 신호 스냅샷 as2_two_way(tests/units/F2/run_case_fixture.py)를 출처 종류 real로 빌드한 것(값은 합성, 출처 종류만
  real)과 임시 파일의 합성 분할 기록(CN·US·VN = real_dev, JP·DE·TW = real_sealed). 실자료 스냅샷 v1·v2로는 돌리지 않는다.
- run-case: real_dev 계열 사례(850450-CN-202402)는 실제 조립(checklist)으로 조사하고 dataset real_dev·grouping_version g0을
  적는다. real_sealed 계열 사례(850450-JP-202402)와 분할 기록을 쓸 수 없는 경우는 관측 값을 읽기 전에 종료 코드 1로 거부한다.
  좁히기를 끈 변이(real_case_scope를 통과시키는 대역)는 같은 사례에서 JP 관측 값을 읽는다(거부 시험이 공허하지 않다).
- evaluate: real_dev는 실행 때 detect와 같은 길로 경보 목록을 만들고 DT7 규칙(sha256("real_dev-mvp-20260925:" + case_id)
  오름차순 앞 20건)으로 고른다. 모드는 freeform·full. 경보 목록 전체와 고른 수는 실행 조건 입력 파일에 남는다.
- DT7 결정 기록의 경보 목록 221건(표 ④)에 규칙을 다시 적용하면 표 ⑤의 20건·순위 값과 같다(정본 빌드 없이 규칙을 고정).
모든 파일은 임시 폴더에 쓴다.
"""
import contextlib
import hashlib
import io
import json
import re
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

import harness_fixtures as hf
from tradesentry.cli import dispatch
from tradesentry.dal import query
from tradesentry.evaluation import batch_run
from tradesentry.runlog import trace as trace_log

from ..I7.fakes import NoNetworkMixin
from . import run_case_fixture as rf

REPO = Path(__file__).resolve().parents[3]
DT7_RECORD = REPO / "docs" / "tracking" / "decisions" / "20260925-0925-data-decision-dt7-real-dev-mvp-selection.md"
DEV, SEALED = ["CN", "US", "VN"], ["DE", "JP", "TW"]
DEV_CASE, SEALED_CASE = rf.SHARE_ONLY_PROBLEM, rf.UNIT_ONLY_PROBLEM  # 850450-CN-202402, 850450-JP-202402
VALUE_READS = ("_rows", "row", "parent_series", "parent", "world_series", "world", "children", "peers", "resolve")
_SHARED: dict = {}


def setUpModule():
    tmp = tempfile.TemporaryDirectory()
    _SHARED["tmp"] = tmp
    _SHARED["snapshots"] = rf.df.install(Path(tmp.name), rf.TWO_WAY, source_kind="real", peer_rows=rf.TWO_WAY_PEERS)


def tearDownModule():
    _SHARED.pop("tmp").cleanup()


def split_record(dev=DEV, sealed=SEALED) -> dict:
    return {"snapshot_id": rf.TWO_WAY_ID, "seed": 1, "ratio": {"real_dev": 1, "real_sealed": 1},
            "method": "hs6_stratified_sha256_rank",
            "real_dev": [{"hs6": "850450", "partner": p} for p in dev],
            "real_sealed": [{"hs6": "850450", "partner": p} for p in sealed]}


def call(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = dispatch.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class RealCase(NoNetworkMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.outputs = self.root / "outputs"
        self.split_file = self.root / "real_split.json"
        self.split_file.write_text(json.dumps(split_record()), encoding="utf-8")
        for patcher in (mock.patch.object(query, "SNAPSHOTS_ROOT", _SHARED["snapshots"]),
                        mock.patch.object(dispatch, "OUTPUT_PARENT", self.outputs),
                        mock.patch.dict(dispatch.REAL_SPLIT_FILES, {rf.TWO_WAY_ID: str(self.split_file)}, clear=True)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_case(self, case_id: str, mode: str = "checklist"):
        return call(["run-case", "--snapshot", rf.TWO_WAY_ID, "--policy", "dev-0.1", "--mode", mode, "--case", case_id])

    def spied_run_case(self, case_id: str):
        spies = {name: mock.patch.object(query.Snapshot, name, autospec=True, side_effect=getattr(query.Snapshot, name))
                 for name in VALUE_READS}
        with contextlib.ExitStack() as stack:
            mocks = {name: stack.enter_context(patcher) for name, patcher in spies.items()}
            code, out, err = self.run_case(case_id)
        return code, out, err, {name: m.call_count for name, m in mocks.items()}, mocks


class RealRunCaseTest(RealCase):
    def test_real_dev_case_is_investigated(self):
        code, out, err = self.run_case(DEV_CASE)
        self.assertEqual((code, err), (0, ""), err)
        record_line = [line for line in out.splitlines() if "runlog_run_record-" in line][0]
        record = trace_log.loads((self.root / record_line).read_text(encoding="utf-8"))
        self.assertEqual((record["dataset"], record["grouping_version"], record["execution_status"], record["case_id"]),
                         ("real_dev", "g0", "COMPLETED", DEV_CASE))

    def test_real_sealed_case_is_refused_before_any_value_is_read(self):
        code, out, err, counts, _ = self.spied_run_case(SEALED_CASE)
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(err, dispatch.RUN_CASE_SEALED_REFUSAL + "\n")
        self.assertNotIn(SEALED_CASE, err)
        self.assertEqual(counts, dict.fromkeys(VALUE_READS, 0))
        [run_dir] = list(self.outputs.iterdir())
        self.assertEqual(list(run_dir.iterdir()), [])  # 확보한 빈 실행 폴더만

    def test_refusal_is_not_vacuous_without_the_scope_check(self):
        """좁히기를 끈 변이: 같은 봉인 계열 사례가 관측 값을 읽는다(JP 계열 조회). 위 거부 시험이 이 변이를 잡는다."""
        def no_check(snap, case_arg):
            return {"dataset": "real_dev", "series_assignment": dispatch.series_assignment(dispatch.load_real_split(snap))}

        with mock.patch.object(dispatch, "real_case_scope", no_check):
            code, out, err, counts, mocks = self.spied_run_case(SEALED_CASE)
        self.assertGreater(counts["parent_series"], 0)
        self.assertIn("JP", [c.args[2] for c in mocks["parent_series"].call_args_list])

    def test_unusable_split_record_is_refused(self):
        for label, raw in (("JSON 아님", "{"), ("계열 빠짐", json.dumps(split_record(dev=DEV[:-1]))),
                           ("다른 스냅샷", json.dumps({**split_record(), "snapshot_id": "kcs_202201_202412_v2"}))):
            with self.subTest(label):
                self.split_file.write_text(raw, encoding="utf-8")
                code, out, err, counts, _ = self.spied_run_case(DEV_CASE)
                self.assertEqual((code, out, err), (1, "", dispatch.RUN_CASE_SPLIT_REFUSAL + "\n"))
                self.assertEqual(counts, dict.fromkeys(VALUE_READS, 0))
        with mock.patch.dict(dispatch.REAL_SPLIT_FILES, {}, clear=True):
            code, _, err = self.run_case(DEV_CASE)
        self.assertEqual((code, err), (1, dispatch.RUN_CASE_SPLIT_REFUSAL + "\n"))


class RealDevEvaluateTest(RealCase):
    def setUp(self):
        super().setUp()
        self.runner = hf.FakeRunner()
        for patcher in (mock.patch.dict(dispatch.EVALUATE_DATASETS, {rf.TWO_WAY_ID: "real_dev"}),
                        mock.patch.object(dispatch, "EVALUATE_BACKEND", dispatch.HOST_BACKEND),
                        mock.patch.object(dispatch, "host_case_runner", self.runner),
                        mock.patch.object(dispatch, "evaluate_pacing", lambda: batch_run.Pacing())):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_real_dev_cases_are_built_at_run_time_and_recorded(self):
        with mock.patch.object(dispatch, "load_real_split", wraps=dispatch.load_real_split) as loader:
            code, out, err = call(["evaluate", "--snapshot", rf.TWO_WAY_ID, "--policy", "dev-0.1"])
        self.assertEqual(code, 0, err)
        self.assertGreaterEqual(loader.call_count, 1)
        batch_line, conditions_line = out.splitlines()
        doc = json.loads((self.root / conditions_line).read_text(encoding="utf-8"), parse_float=Decimal)
        self.assertEqual(doc["dataset"], "real_dev")
        self.assertEqual(doc["planned_modes"], ["freeform", "full"])  # 룰북 B2, 평가 스킬 ②
        alerts = doc["snapshot"]["real_dev_alerts"]
        self.assertEqual(alerts["case_ids"], [DEV_CASE])  # real_dev 계열(CN·US·VN)의 경보뿐(JP 사례는 봉인 계열)
        self.assertEqual((alerts["count"], alerts["selected"], alerts["policy_version"]), (1, 1, "dev-0.1"))
        self.assertEqual(alerts["selection"], dispatch.REAL_DEV_MVP_RULE)
        self.assertEqual(doc["planned_cases"], [{"case_id": DEV_CASE, "hs6": "850450", "partner": "CN",
                                                 "month": "202402"}])
        self.assertEqual(doc["prescoring_checks"]["final_status"],
                         "참: 예정 실행 2건 가운데 줄 없는 조합 0건, 인프라 실패 재실행(룰북 B5) 대상 0건·재실행 0건")
        lines = hf.read_jsonl(self.root / batch_line)
        self.assertEqual(sorted((x["case_id"], x["mode"]) for x in lines), [(DEV_CASE, "freeform"), (DEV_CASE, "full")])
        self.assertEqual(list(self.outputs.glob("detect-*")), [])  # detect 실행 폴더를 만들지 않는다

    def test_real_dev_needs_a_real_snapshot_and_a_split(self):
        with mock.patch.dict(dispatch.EVALUATE_DATASETS, {"dev20": "real_dev"}), \
                mock.patch.object(query, "SNAPSHOTS_ROOT", self.root / "none"):
            code, out, err = call(["evaluate", "--snapshot", "dev20", "--policy", "dev-0.1"])
        self.assertEqual((code, out), (1, ""))
        self.assertIn("사례 목록을 읽지 못했다(SnapshotError)", err)
        self.split_file.write_text("{", encoding="utf-8")
        code, out, err = call(["evaluate", "--snapshot", rf.TWO_WAY_ID, "--policy", "dev-0.1"])
        self.assertEqual((code, out, err), (1, "", dispatch.DETECT_SPLIT_REFUSAL + "\n"))
        self.assertFalse(self.outputs.exists())
        self.assertEqual(self.runner.calls, [])


def dt7_tables() -> tuple[list[str], list[tuple[str, str]]]:
    """DT7 결정 기록의 표 ④(경보 목록 전체)와 ⑤(고른 20건과 순위 값)를 읽는다."""
    text = DT7_RECORD.read_text(encoding="utf-8")
    full_part = text.split("④ **경보 목록 전체**", 1)[1].split("⑤ **MVP 실행 사례 20건**", 1)[0]
    alerts = []
    for series, months in re.findall(r"^\| `(\d{6}-[A-Z]{2})` \| \d+ \| ([0-9, ]+) \|$", full_part, re.M):
        alerts += [f"{series}-{month.strip()}" for month in months.split(",")]
    chosen_part = text.split("⑤ **MVP 실행 사례 20건**", 1)[1]
    chosen = re.findall(r"^\| \d+ \| `(\d{6}-[A-Z]{2}-\d{6})` \| `([0-9a-f]{64})` \|", chosen_part, re.M)
    return alerts, chosen


class Dt7SelectionRuleTest(unittest.TestCase):
    def test_rule_reproduces_the_dt7_table(self):
        alerts, chosen = dt7_tables()
        self.assertEqual(len(alerts), 221)
        self.assertEqual(len(set(alerts)), 221)
        self.assertEqual(len(chosen), 20)
        cases = [dict(zip(("hs6", "partner", "month"), a.split("-")), case_id=a) for a in alerts]
        picked = dispatch.select_real_dev_mvp(cases)
        self.assertEqual([c["case_id"] for c in picked], [case_id for case_id, _ in chosen])
        for case_id, rank in chosen:
            self.assertEqual(hashlib.sha256(f"real_dev-mvp-20260925:{case_id}".encode("utf-8")).hexdigest(), rank)

    def test_twenty_or_fewer_are_all_taken(self):
        cases = [{"case_id": f"850450-CN-2024{m:02d}"} for m in range(1, 13)]
        self.assertEqual(sorted(c["case_id"] for c in dispatch.select_real_dev_mvp(cases)),
                         sorted(c["case_id"] for c in cases))


if __name__ == "__main__":
    unittest.main()
