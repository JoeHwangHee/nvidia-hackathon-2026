"""키 없는 스모크 재현(tradesentry run-case --replay, 사용자 결정 2026-09-26(토) 02:12 ②, 결정 기록
model-decision-smoke-replay): 커밋된 재생 파일 eval/dev/smoke/*.json(오케스트레이터가 실제 NIM으로 돌린 A·B·C 실행의 모델
응답 기록)로 run-case가 키·네트워크 없이 끝까지 돌고 execution_status·판정이 기록과 같은지 본다. 재생 파일의 요청 해시가
지금 코드·지침(configs/model/)이 만드는 요청과 같아야 하므로, 이 시험이 깨지면 지침이나 요청 본문 구성이 바뀐 것이다(그때는
재생 파일을 다시 만든다: scripts/make_smoke_replay.py).

- 실제로 도는 것: 단위 F1 → F2 run-case → 정책 policy_v1 → 합성 픽스처(임시 폴더에 materialize) → 도구 5개(실제 조회) →
  흐름 조정 I12(모델 전송 자리만 단위 I8 ReplayTransport) → NAT I13 → trace L1·실행 결과 기록 L2 → 출력 파일.
- 바꾸는 것: 스냅샷 뿌리, 실행 폴더 부모(임시 폴더), 현재 폴더(재생 파일 상대 경로의 기준. 저장소 루트로 고정), 키
  환경변수(지운다). run_case_transport는 바꾸지 않는다(부르면 실패해야 한다).
"""
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tradesentry.cli import dispatch
from tradesentry.dal import query
from tradesentry.runlog import cause_codes
from tradesentry.runlog import trace as trace_log

from ..I7.fakes import NoNetworkMixin
from . import run_case_fixture as rf

ROOT = Path(__file__).resolve().parents[3]
SMOKE_DIR = Path("eval") / "dev" / "smoke"  # 커밋 위치(저장소 루트 기준 상대 경로. 결정 기록 model-decision-smoke-replay)
SID = "controlled_fixture_v0"
POLICY = "policy_v1"
_SHARED: dict = {}


def setUpModule():
    tmp, snapshots = rf.materialize_fixture()
    _SHARED.update(tmp=tmp, snapshots=snapshots)


def tearDownModule():
    _SHARED.pop("tmp").cleanup()
    _SHARED.clear()


def call(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = dispatch.main(argv)
    return code, out.getvalue(), err.getvalue()


def replay_files() -> list[Path]:
    return sorted((ROOT / SMOKE_DIR).glob("*.json"))


def smoke_argv(case_id: str, replay: str, mode: str = "full") -> list[str]:
    return ["run-case", "--snapshot", SID, "--policy", POLICY, "--mode", mode, "--case", case_id, "--replay", replay]


def refuse_transport(config):
    raise AssertionError("--replay 실행이 실제 전송 자리(run_case_transport)를 만들었다")


class ReplayBase(NoNetworkMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.outputs = self.tmp / "outputs"
        for target, name, value in ((query, "SNAPSHOTS_ROOT", _SHARED["snapshots"]),
                                    (dispatch, "OUTPUT_PARENT", self.outputs),
                                    (dispatch, "run_case_transport", refuse_transport)):
            patcher = mock.patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        env = {k: v for k, v in os.environ.items() if k not in dispatch.CHILD_ENV_DROP}  # 키 없이 돈다
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.cwd = os.getcwd()
        os.chdir(ROOT)  # 재생 파일의 상대 경로 기준은 명령을 부른 폴더(저장소 루트)다
        self.addCleanup(os.chdir, self.cwd)

    def files(self, out: str) -> dict:
        found = {}
        for line in out.splitlines():
            parts = line.split("/")
            self.assertEqual((parts[0], len(parts)), ("outputs", 3), line)
            found[parts[2].split("-")[0]] = self.outputs / parts[1] / parts[2]
        return found

    def read(self, path: Path) -> dict:
        return trace_log.loads(path.read_text(encoding="utf-8"))

    def write_replay(self, doc: dict, name: str = "replay.json") -> str:
        """고친 재생 파일을 임시 폴더에 쓰고 저장소 루트 기준 상대 경로를 돌려준다(절대 경로는 F1이 받지 않는다)."""
        path = self.tmp / name
        path.write_text(trace_log.dumps(doc), encoding="utf-8")
        return os.path.relpath(path, ROOT)


class SmokeReplayTest(ReplayBase):
    def test_committed_replay_files_run_end_to_end_without_a_key(self):
        """스모크 명령 하나: uv run --locked tradesentry run-case --snapshot controlled_fixture_v0 --policy policy_v1
        --mode full --case <사례> --replay eval/dev/smoke/<사례>.json. 커밋된 재생 파일마다 끝까지 돌고 판정이 기록과 같다."""
        files = replay_files()
        self.assertGreaterEqual(len(files), 2, "재생 파일이 최소 A·C 둘은 있어야 한다")
        for path in files:
            source = self.read(path)["source"]
            with self.subTest(case=source["case_id"]):
                self.assertEqual(path.stem, source["case_id"])  # 파일 이름 = 사례 식별자
                self.assertEqual((source["snapshot_id"], source["policy_version"], source["execution_status"]),
                                 (SID, POLICY, cause_codes.COMPLETED))
                self.assertNotIn("NVIDIA_API_KEY", os.environ)
                code, out, err = call(smoke_argv(source["case_id"], (SMOKE_DIR / path.name).as_posix(), source["mode"]))
                self.assertEqual(code, 0, err)
                self.assertEqual(err.strip(), dispatch.REPLAY_NOTICE)
                found = self.files(out)
                self.assertEqual(sorted(found), ["reports_render_ko", "runlog_run_record", "runlog_trace",
                                                 "workflow_nat_wrap"])
                record = self.read(found["runlog_run_record"])
                self.assertEqual((record["execution_status"], record["review_status_final"], record["case_id"],
                                  record["mode"], record["errors"]),
                                 (cause_codes.COMPLETED, source["review_status_final"], source["case_id"],
                                  source["mode"], []))
                report = self.read(found["reports_render_ko"])
                self.assertEqual(report["review_status"], source["review_status_final"])
                # 재생한 요청 해시는 기록과 같고(ReplayTransport가 대조했다), 모델 레코드 순서도 같다
                events = trace_log.read_records(found["runlog_trace"])
                mine = [(e["event"], e["data"].get("request_sha256")) for e in events
                        if e["event"] in dispatch.REPLAY_EVENTS]
                theirs = [(e["event"], e["data"].get("request_sha256")) for e in self.read(path)["trace"]]
                self.assertEqual(mine, theirs)
                self.assertEqual(events[0]["ts"], "2026-09-25T00:00:00+09:00")  # 가상 시계(단위 I8 ReplayClock)

    def test_expected_verdicts_of_a_b_c(self):
        """A MONITOR·B MAINTAIN·C HOLD(eval/dev/oracle_ABC.json). 재생 파일이 있는 사례만 본다."""
        expected = {"850450-XA-202412": "MONITOR", "850431-XB-202412": "MAINTAIN", "850432-XC-202412": "HOLD"}
        for path in replay_files():
            source = self.read(path)["source"]
            self.assertEqual(source["review_status_final"], expected[source["case_id"]], path.name)

    def test_replay_files_carry_no_secret_or_local_path_shapes(self):
        from tradesentry.evaluation.batch_run import PATH_SHAPE, SECRET_SHAPE

        for path in replay_files():
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(PATH_SHAPE.search(text), path.name)
            self.assertIsNone(SECRET_SHAPE.search(text), path.name)
            doc = json.loads(text)
            self.assertEqual(sorted(doc), ["requests", "source", "trace"])
            self.assertEqual(doc["requests"], [])
            self.assertTrue(all(r["event"] in dispatch.REPLAY_EVENTS for r in doc["trace"]))


class ReplayFailureTest(ReplayBase):
    def setUp(self):
        super().setUp()
        self.path = replay_files()[0]
        self.doc = self.read(self.path)
        self.case_id = self.doc["source"]["case_id"]

    def test_request_hash_mismatch_is_recorded_as_code_error_and_exit_1(self):
        first = next(r for r in self.doc["trace"] if r["event"] == "model_request")
        first["data"]["request_sha256"] = "0" * 64
        code, out, err = call(smoke_argv(self.case_id, self.write_replay(self.doc)))
        self.assertEqual(code, 1)
        found = self.files(out)
        record = self.read(found["runlog_run_record"])
        self.assertEqual(record["execution_status"], cause_codes.execution_status(cause_codes.CODE_ERROR))
        self.assertEqual(record["errors"][0]["code"], cause_codes.CODE_ERROR)
        self.assertIn("ReplayMismatch", record["errors"][0]["detail"])
        self.assertIn("request_sha256", record["errors"][0]["detail"])
        self.assertNotIn("reports_render_ko", found)

    def test_leftover_records_fail_after_writing_outputs(self):
        extra = dict(self.doc["trace"][-1])
        self.doc["trace"].append(extra)
        code, out, err = call(smoke_argv(self.case_id, self.write_replay(self.doc)))
        self.assertEqual(code, 1)
        self.assertIn(dispatch.REPLAY_LEFTOVER, err)
        self.assertIn("runlog_run_record", self.files(out))

    def test_bad_replay_files_fail_before_making_a_run_dir(self):
        missing = os.path.relpath(self.tmp / "none.json", ROOT)
        not_json = self.tmp / "bad.json"
        not_json.write_text("{", encoding="utf-8")
        other_case = dict(self.doc, source=dict(self.doc["source"], case_id="850431-XB-202412"))
        cases = {
            "없는 파일": (missing, "읽지 못했다"),
            "JSON 아님": (os.path.relpath(not_json, ROOT), "JSON이 아니다"),
            "객체 아님": (self.write_replay([], "r1.json"), "모양이 아니다"),
            "source 없음": (self.write_replay({"trace": self.doc["trace"], "requests": []}, "r2.json"), "모양이 아니다"),
            "trace에 다른 사건": (self.write_replay(dict(self.doc, trace=self.doc["trace"] + [{"event": "tool_call",
                                                                                         "data": {}}]), "r3.json"),
                             "모양이 아니다"),
            "빈 trace": (self.write_replay(dict(self.doc, trace=[]), "r4.json"), "기록된 모델 응답이 없다"),
            "다른 사례": (self.write_replay(other_case, "r5.json"), "이 요청의 사례가 아니다"),
        }
        for label, (replay, phrase) in cases.items():
            with self.subTest(label=label):
                code, out, err = call(smoke_argv(self.case_id, replay))
                self.assertEqual((code, out), (1, ""))
                self.assertIn(phrase, err)
                self.assertNotIn(str(self.tmp), err)
                self.assertFalse(self.outputs.exists(), "실행 폴더를 만들기 전에 끝나야 한다")
        code, out, err = call(smoke_argv(self.case_id, (SMOKE_DIR / self.path.name).as_posix(), mode="agent"))
        self.assertEqual((code, out), (1, ""))
        self.assertIn("mode", err)
        self.assertFalse(self.outputs.exists())
        code, out, err = call(smoke_argv(self.case_id, (SMOKE_DIR / self.path.name).as_posix(), mode="checklist"))
        self.assertEqual((code, out), (1, ""))
        self.assertIn("checklist", err)
        self.assertFalse(self.outputs.exists())


class NoReplayUnchangedTest(ReplayBase):
    def test_without_the_option_the_real_transport_is_used(self):
        """옵션이 없으면 전송 자리는 run_case_transport다(여기서는 부르면 실패하는 함수로 바꿔 두었으니 그 실패가 보인다)."""
        with mock.patch.object(dispatch, "run_case_transport", side_effect=RuntimeError("real transport")) as real:
            code, out, err = call(["run-case", "--snapshot", SID, "--policy", POLICY, "--mode", "agent",
                                   "--case", "850450-XA-202412"])
        self.assertEqual(real.call_count, 1)
        self.assertEqual(code, 1)
        self.assertNotIn(dispatch.REPLAY_NOTICE, err)
