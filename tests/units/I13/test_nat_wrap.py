"""단위 I13(workflow_nat_wrap) 골든 쌍 밖 규칙 시험(로드맵 MT4 완료 기준: NAT 실행 추적과 프로파일 결과, MVP 7번).

- 흐름 조정(단위 I12)을 NAT로 감싸 돌리면 NIM 요청마다 LLM 구간(토큰 포함)과 도구 시도마다 TOOL 구간이 남고,
  WORKFLOW_END까지 파일에 쓰이며(wait_for_tasks), 프로파일 파일이 N7 폴더에 NAT가 정한 이름으로 생긴다.
- NAT 추적·프로파일 파일에 로컬 절대경로가 없다(N13). 폴더가 이미 있으면 쓰지 않는다(N8).
- 흐름이 예외를 내도 NAT 추적을 끝까지 쓰고 예외를 다시 낸다. `nat` 명령 진입점을 불러오지 않는다.
"""
import ast
import os
import socket
import sys
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest import mock

from tradesentry.runlog import trace as trace_log
from tradesentry.workflow import model_client as mc
from tradesentry.workflow import nat_wrap, orchestrate

from ..I12 import harness as h
from ..I7.fakes import FakeClock, ScriptedTransport

MODEL = "nvidia/nemotron-3-super-120b-a12b"


def _refuse_network(*args, **kwargs):
    raise OSError("이 시험에서는 네트워크 연결을 쓰지 않는다")


class NatWrapTest(unittest.TestCase):
    """골든 시험과 같은 환경(HOME·봉인 폴더는 없는 경로, python-dotenv 끔, 소켓 연결 막음)에서 돈다."""

    def setUp(self):
        super().setUp()
        missing = Path(tempfile.gettempdir()) / f"tradesentry-i13-{uuid.uuid4().hex}"  # 만들지 않는 경로
        self.missing = missing
        environment = mock.patch.dict(os.environ, {"TRADESENTRY_SEALED_DIR": str(missing / "sealed"),
                                                   "HOME": str(missing / "home"), "PYTHON_DOTENV_DISABLED": "1"})
        environment.start()
        self.addCleanup(environment.stop)
        for target in ("socket.socket.connect", "socket.create_connection"):
            patcher = mock.patch(target, _refuse_network)
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_flow(self, mode, script, fake=None):
        config = mc.load_model_config()
        memory = trace_log.MemoryTrace(h.RUN_ID)

        def flow(nat_sink):
            clock = FakeClock()
            ctx = orchestrate.RunContext(run_id=h.RUN_ID, case=h.CASE_A, mode=mode, dataset="controlled_fixture_v0",
                                         rulebook_version="RB-1", grouping_version="g0", code_version="abc1234")
            return orchestrate.orchestrate(ctx, (fake or h.FakePorts()).ports(), config,
                                           transport=ScriptedTransport(script, clock),
                                           sink=trace_log.Tee(memory, nat_sink), clock_ms=clock.clock_ms,
                                           sleep_ms=clock.sleep_ms)

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        nat_dir = Path(tmp.name) / "run_case-260925143015" / "workflow_nat_wrap-260925143015"
        nat_dir.parent.mkdir()
        return nat_wrap.run_under_nat(flow, nat_dir, model=MODEL), nat_dir, memory

    def test_flow_under_nat_leaves_llm_and_tool_spans_matching_the_run_record(self):
        fake = h.FakePorts(checks=[h.PASS, h.BLOCK, h.PASS])
        script = [h.draft_answer(status="MAINTAIN"), h.tools_answer("decompose_hs", "compare_partners", "get_history"),
                  h.draft_answer(status="MAINTAIN")]
        outcome, nat_dir, memory = self.run_flow("agent", script, fake)
        record = outcome["result"]["record"]
        summary = outcome["nat"]
        self.assertEqual(record["execution_status"], "COMPLETED")
        self.assertTrue(summary["workflow_end"])
        self.assertEqual(summary["llm_spans"], record["model_requests"])
        self.assertEqual(summary["tool_spans"], record["tool_attempts"])  # 막힌 시도도 구간 하나
        self.assertEqual(summary["tokens"]["prompt_tokens"], record["tokens_in"])
        self.assertEqual(summary["tokens"]["completion_tokens"], record["tokens_out"])
        self.assertEqual(summary["nat_events"][:2], ["WORKFLOW_START", "FUNCTION_START"])
        self.assertEqual(summary["nat_events"][-2:], ["FUNCTION_END", "WORKFLOW_END"])
        self.assertEqual(sorted(p.name for p in nat_dir.iterdir()),
                         sorted((nat_wrap.NAT_TRACE_NAME,) + nat_wrap.PROFILE_FILES))
        self.assertEqual(outcome["profile_files"], sorted(nat_wrap.PROFILE_FILES))
        for path in nat_dir.iterdir():  # 로컬 절대경로가 없다(N13)
            with self.subTest(file=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn(str(nat_dir.parent), text)
                self.assertNotIn(tempfile.gettempdir(), text)
        self.assertEqual((memory.records[0]["event"], memory.records[-1]["event"]), ("run_start", "run_end"))
        self.assertFalse(self.missing.exists())  # HOME 아래에 아무것도 만들지 않았다

    def test_existing_folder_is_not_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileExistsError):
                nat_wrap.run_under_nat(lambda sink: None, Path(tmp), model=MODEL)

    def test_flow_error_is_raised_after_the_nat_trace_is_finished(self):
        def flow(nat_sink):
            nat_sink.emit("stage_start", "basic", {"stage": "basic"})
            nat_sink.emit("model_request", "basic", {"request_no": 1, "attempt": 1})
            raise KeyError("흐름 안의 오류")

        with tempfile.TemporaryDirectory() as tmp:
            nat_dir = Path(tmp) / "workflow_nat_wrap-260925143015"
            with self.assertRaises(KeyError):
                nat_wrap.run_under_nat(flow, nat_dir, model=MODEL)
            api = nat_wrap.nat_api()
            types = [s.event_type.value for s in nat_wrap.read_nat_trace(api, nat_dir)]
        self.assertEqual(types[-1], "WORKFLOW_END")
        self.assertEqual(types.count("LLM_START"), types.count("LLM_END"))  # 열린 구간을 닫았다
        self.assertEqual(types.count("SPAN_START"), types.count("SPAN_END"))

    def test_nat_is_loaded_through_the_python_api_only(self):
        nat_wrap.nat_api()
        self.assertEqual(os.environ.get("PYTHON_DOTENV_DISABLED"), "1")
        self.assertEqual(os.environ.get("NAT_TELEMETRY_ENABLED"), "false")
        self.assertNotIn("nat.cli.entrypoint", sys.modules)
        tree = ast.parse(Path(nat_wrap.__file__).read_text(encoding="utf-8"))
        top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        names = [a.name for n in top for a in n.names] + [n.module or "" for n in top if isinstance(n, ast.ImportFrom)]
        self.assertFalse([n for n in names if n == "nat" or n.startswith("nat.") or n == "yaml"])

    def test_template_values_may_not_interpolate_environment_variables(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "workflow.yml"
            bad.write_text(nat_wrap.DEFAULT_WORKFLOW_CONFIG.read_text(encoding="utf-8").replace(
                "project: tradesentry", "project: ${NVIDIA_PROJECT}"), encoding="utf-8")
            with self.assertRaises(ValueError):
                nat_wrap.load_workflow_config(Path(tmp) / "x", bad)
        config = nat_wrap.load_workflow_config(Path("outputs") / "x")
        self.assertEqual(config["workflow"], {"_type": nat_wrap.FUNCTION_TYPE})
        self.assertEqual(config["general"]["telemetry"]["tracing"][nat_wrap.EXPORTER_TYPE]["output_path"],
                         str(Path("outputs") / "x" / nat_wrap.NAT_TRACE_NAME))


if __name__ == "__main__":
    unittest.main()
