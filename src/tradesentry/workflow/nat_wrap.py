"""단위 I13 NAT 감싸기.

단위 ID: I13
도메인명: workflow_nat_wrap
소유: M
입력: 흐름
출력: NAT 추적·프로파일 파일
허용 import: 표준 라이브러리, nat, yaml, tradesentry.contract, tradesentry.runlog, tradesentry.workflow

허용 import에 yaml을 더했다(S0 인계: NAT 워크플로 설정 configs/nat/workflow.yml을 PyYAML로 읽는다).

NAT(NVIDIA NeMo Agent Toolkit 1.9.0)로 사례 조사 흐름 1건을 감싼다(자문 명세서 Q1의 (가): 흐름을 NAT 함수로 등록해
NAT 실행기로 돌리고, 예산·조기 종료는 우리 코드가 강제한다).
- 실행: 흐름을 NAT 함수 tradesentry_case로 등록하고 NAT 워크플로 실행기(WorkflowBuilder·SessionManager)로 돌린다.
- 추적: 우리 trace 이벤트(단위 L1)를 NAT 중간 단계로 옮긴다(NatSink). NIM 요청 시도마다 LLM_START·LLM_END(토큰 수
  포함. X1 인계: LLM 구간 기록), 도구 시도마다 TOOL_START·TOOL_END, 흐름 단계마다 SPAN_START·SPAN_END. NIM 호출 자체는
  우리 클라이언트(단위 I7)가 하므로 provider 자동 재시도가 끼지 않는다(Q1의 2).
- 내보내기: NAT 파일 내보내기(FileExporter)를 쓰되, 멈추기 전에 wait_for_tasks()로 남은 쓰기를 기다리는 하위 클래스
  (tradesentry_file)로 WORKFLOW_END까지 파일에 남긴다(X1 인계: NAT 1.9.0의 stop()은 기다리지 않는다). 외부 관측
  서비스로 보내지 않는다(Q1의 7).
- 프로파일: 끝난 뒤 NAT 추적 파일을 다시 읽어 NAT 프로파일러(nvidia-nat-profiler ProfilerRunner)로 결과를 쓴다.

출력 위치와 이름(자료 계약 §10.3 N6·N7): 부르는 쪽이 실행 폴더 안의 N7 폴더 outputs/{실행명}/workflow_nat_wrap-{시각}/을
경로 인자로 준다(S0 결정 ⑥). 이 단위가 그 폴더를 이미 있으면 실패하는 방식으로 만들고, 안에 NAT가 정한 이름 그대로
쓴다: NAT_TRACE_NAME(NAT 추적), PROFILE_FILES(프로파일). 이 이름들은 단위 표 I13 행에 고정할 값의 제안이다.

지키는 것
- `nat` 명령(nat.cli.entrypoint)은 쓰지 않는다. 그 진입점은 import 때 load_dotenv()로 .env를 읽는다. 의존성
  pymilvus도 import 때 load_dotenv()를 부른다(NAT Milvus 검색기를 설정할 때만 불러온다. 이 단위의 경로는 부르지
  않는다). NAT를 불러오는 함수(nat_api·read_nat_trace·write_profile)는 모두 첫 줄에서 이 프로세스에
  PYTHON_DOTENV_DISABLED=1(python-dotenv 1.2.0 이상)과 NAT_TELEMETRY_ENABLED=false를 둔다(S0 인계). 그래서
  write_profile을 따로 불러도(예: 샌드박스 밖 결과 정리) 같다.
- import nat은 함수 안에서만 한다(단위를 import해도 nat이 올라오지 않는다. 기본 시험 환경 보호).
- NAT 설정은 파일로 쓰지 않고 메모리에서 만든다. NAT의 설정 파일 읽기는 ${변수}를 환경변수 값으로 바꾸고, 실행마다 쓰는
  설정 사본에는 로컬 절대경로가 들어가기 때문이다(자료 계약 N13).
"""
import asyncio
import logging
import os
import warnings
from pathlib import Path
from types import SimpleNamespace
from typing import Callable

from tradesentry.runlog import trace as trace_log
from tradesentry.workflow import model_client

DOMAIN = "workflow_nat_wrap"
DEFAULT_WORKFLOW_CONFIG = Path(__file__).resolve().parents[3] / "configs" / "nat" / "workflow.yml"
EXPORTER_TYPE = "tradesentry_file"
FUNCTION_TYPE = "tradesentry_case"
NAT_TRACE_NAME = "nat_trace.jsonl"
PROFILE_FILES = ("all_requests_profiler_traces.json", "inference_optimization.json", "standardized_data_all.csv",
                 "workflow_profiling_metrics.json", "workflow_profiling_report.txt")
EXPORT_WAIT_S = 30.0
OUTPUT_TEXT_MAX = 2000

_STATE: dict = {"api": None}
_ACTIVE: dict = {}


def _prepare_env() -> None:
    os.environ["PYTHON_DOTENV_DISABLED"] = "1"
    os.environ["NAT_TELEMETRY_ENABLED"] = "false"


def nat_api() -> SimpleNamespace:
    """NAT 모듈을 불러오고 우리 내보내기·함수 형식을 한 번만 등록한다. 부를 때마다 환경변수 두 개를 다시 둔다."""
    _prepare_env()
    if _STATE["api"] is not None:
        return _STATE["api"]
    with _Quiet("nat"):
        from nat.builder.builder import Builder
        from nat.builder.context import Context
        from nat.builder.function_info import FunctionInfo
        from nat.builder.workflow_builder import WorkflowBuilder
        from nat.cli.register_workflow import register_function, register_telemetry_exporter
        from nat.data_models.config import Config
        from nat.data_models.function import FunctionBaseConfig
        from nat.data_models.intermediate_step import (IntermediateStep, IntermediateStepPayload,
                                                       IntermediateStepType, StreamEventData, UsageInfo)
        from nat.data_models.telemetry_exporter import TelemetryExporterBaseConfig
        from nat.data_models.token_usage import TokenUsageBaseModel
        from nat.observability.exporter.file_exporter import FileExporter
        from nat.runtime.loader import PluginTypes, discover_and_register_plugins
        from nat.runtime.session import SessionManager

    class WaitingFileExporter(FileExporter):
        """멈추기 전에 남은 내보내기 쓰기를 wait_for_tasks()로 기다리는 파일 내보내기(WORKFLOW_END까지 남긴다)."""

        async def stop(self):
            await self.wait_for_tasks(timeout=EXPORT_WAIT_S)
            await super().stop()

    class TradeSentryFileConfig(TelemetryExporterBaseConfig, name=EXPORTER_TYPE):
        output_path: str
        project: str

    @register_telemetry_exporter(config_type=TradeSentryFileConfig)
    async def tradesentry_file_exporter(config: TradeSentryFileConfig, builder: Builder):
        yield WaitingFileExporter(output_path=config.output_path, project=config.project)

    class TradeSentryCaseConfig(FunctionBaseConfig, name=FUNCTION_TYPE):
        pass

    @register_function(config_type=TradeSentryCaseConfig)
    async def tradesentry_case(config: TradeSentryCaseConfig, builder: Builder):
        async def _run(text: str) -> str:
            """TradeSentry 사례 조사 흐름 1건을 돈다(흐름은 run_under_nat가 넘긴다)."""
            sink = NatSink(_STATE["api"], Context.get().intermediate_step_manager, _ACTIVE["model"])
            _ACTIVE["sink"] = sink
            try:
                _ACTIVE["result"] = _ACTIVE["flow"](sink)
            except Exception as exc:  # noqa: BLE001 - 흐름의 예외는 NAT 추적을 마저 쓴 뒤 다시 낸다
                _ACTIVE["error"] = exc
            finally:
                sink.close_all()
            return "error" if _ACTIVE.get("error") is not None else "done"

        yield FunctionInfo.from_fn(_run, description="TradeSentry case investigation flow")

    _STATE["api"] = SimpleNamespace(
        Config=Config, IntermediateStep=IntermediateStep, IntermediateStepPayload=IntermediateStepPayload,
        IntermediateStepType=IntermediateStepType, StreamEventData=StreamEventData, UsageInfo=UsageInfo,
        TokenUsageBaseModel=TokenUsageBaseModel, WorkflowBuilder=WorkflowBuilder, SessionManager=SessionManager,
        PluginTypes=PluginTypes, discover_and_register_plugins=discover_and_register_plugins)
    return _STATE["api"]


def _short(value: object) -> str:
    text = value if isinstance(value, str) else trace_log.dumps(value)
    return text[:OUTPUT_TEXT_MAX]


class NatSink:
    """trace 이벤트(단위 L1)를 NAT 중간 단계로 옮긴다. 이벤트에 키 값·헤더가 없으므로 NAT 추적에도 없다."""

    def __init__(self, api: SimpleNamespace, manager, model: str):
        self.api = api
        self.manager = manager
        self.model = model
        self.llm: tuple[str, float] | None = None
        self.tool: tuple[str, float, str] | None = None
        self.spans: dict[str, tuple[str, float]] = {}
        self.counts = {"llm": 0, "tool": 0, "span": 0}

    def _push(self, event_type: str, uuid: str | None = None, **fields) -> object:
        extra = {"UUID": uuid} if uuid else {}
        payload = self.api.IntermediateStepPayload(event_type=getattr(self.api.IntermediateStepType, event_type),
                                                   **extra, **fields)
        self.manager.push_intermediate_step(payload)
        return payload

    def _open(self, event_type: str, name: str, data: object) -> tuple[str, float]:
        payload = self._push(event_type, name=name, data=self.api.StreamEventData(input=data))
        return payload.UUID, payload.event_timestamp

    def _close_llm(self, output: object, usage: dict | None = None) -> None:
        if self.llm is None:
            return
        uuid, started = self.llm
        fields = {"name": self.model, "span_event_timestamp": started, "data": self.api.StreamEventData(output=output)}
        if usage is not None:
            fields["usage_info"] = self.api.UsageInfo(
                token_usage=self.api.TokenUsageBaseModel(prompt_tokens=int(usage.get("prompt_tokens") or 0),
                                                         completion_tokens=int(usage.get("completion_tokens") or 0),
                                                         total_tokens=int(usage.get("total_tokens") or 0)),
                num_llm_calls=1)
        self._push("LLM_END", uuid, **fields)
        self.llm = None

    def _close_tool(self, output: object) -> None:
        if self.tool is None:
            return
        uuid, started, name = self.tool
        self._push("TOOL_END", uuid, name=name, span_event_timestamp=started,
                   data=self.api.StreamEventData(output=output))
        self.tool = None

    def _close_children(self) -> None:
        self._close_llm({"error": "unfinished"})
        self._close_tool({"blocked": "unfinished"})

    def emit(self, event: str, stage: str | None, data: dict) -> None:
        if event == "stage_start" and stage and stage not in self.spans:
            self.spans[stage] = self._open("SPAN_START", stage, {"stage": stage})
            self.counts["span"] += 1
        elif event == "stage_end" and stage in self.spans:
            self._close_children()
            uuid, started = self.spans.pop(stage)
            self._push("SPAN_END", uuid, name=stage, span_event_timestamp=started)
        elif event == "model_request":
            self._close_llm({"error": "unfinished"})
            self.llm = self._open("LLM_START", self.model, {"stage": stage, "request_no": data.get("request_no"),
                                                            "attempt": data.get("attempt")})
            self.counts["llm"] += 1
        elif event == "model_response":
            message = (data.get("response") or {}).get("message") or {}
            self._close_llm(_short(message.get("content") or message.get("tool_calls") or ""), data.get("usage") or {})
        elif event == "model_error":
            self._close_llm({"http_status": data.get("http_status"), "error": data.get("error"),
                             "denial": data.get("denial"), "retrying": data.get("retrying")})
        elif event == "tool_call":
            self._close_tool({"blocked": "unfinished"})
            tool = data.get("tool") or "invalid_call"
            uuid, started = self._open("TOOL_START", tool, data.get("args") or {})
            self.tool = (uuid, started, tool)
            self.counts["tool"] += 1
        elif event == "tool_result":
            envelope = data.get("envelope") or {}
            self._close_tool({"evidence_ids": len(envelope.get("evidence_ids") or []),
                              "metrics": len(envelope.get("metrics") or []),
                              "missingness": len(envelope.get("missingness") or [])})
        elif event == "budget_block":
            self._close_tool({"blocked": data.get("kind")})
        elif event == "run_end":
            self.close_all()

    def close_all(self) -> None:
        """멈춘 흐름이 남긴 열린 구간을 닫는다(NAT 구간 쌓기가 어긋나지 않게)."""
        self._close_children()
        for stage in list(self.spans)[::-1]:
            uuid, started = self.spans.pop(stage)
            self._push("SPAN_END", uuid, name=stage, span_event_timestamp=started)


class _Quiet:
    """NAT를 불러오거나 돌리는 동안 의존 패키지의 경고와 한 로거의 기록을 화면에 내지 않는다.

    쓰지 않는 선택 플러그인(예: langchain 도구)의 import 실패 기록, authlib 폐기 예정 경고(패키지 파일의 로컬 절대경로가
    찍힌다, N13), 프로파일러의 표본 1건 안내 같은 것이다. 경고는 catch_warnings(record=True)로 모으고 버린다(authlib은
    import 때 자기 경고를 "always"로 걸어 두므로 무시 필터로는 막히지 않는다).
    """

    def __init__(self, logger_name: str):
        self.logger = logging.getLogger(logger_name)

    def __enter__(self):
        self.level = self.logger.level
        self.logger.setLevel(logging.CRITICAL)
        self.catcher = warnings.catch_warnings(record=True)
        self.catcher.__enter__()
        return self

    def __exit__(self, *exc):
        self.catcher.__exit__(*exc)
        self.logger.setLevel(self.level)
        return False


def _strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _strings(key)
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def load_workflow_config(nat_dir: Path, workflow_config: Path | None = None) -> dict:
    """configs/nat/workflow.yml(틀)을 PyYAML로 읽고 이번 실행의 NAT 추적 파일 경로를 채운 설정(메모리)을 만든다."""
    import yaml

    source = Path(workflow_config) if workflow_config is not None else DEFAULT_WORKFLOW_CONFIG
    config = yaml.safe_load(source.read_text(encoding="utf-8"))
    if any("${" in value for value in _strings(config)):
        raise ValueError("NAT 설정 틀의 값에 ${변수}를 두지 않는다(환경변수 끼워 넣기 금지)")
    exporter = config["general"]["telemetry"]["tracing"][EXPORTER_TYPE]
    if exporter.get("_type") != EXPORTER_TYPE or config["workflow"].get("_type") != FUNCTION_TYPE:
        raise ValueError("NAT 설정 틀의 내보내기·워크플로 형식이 이 단위와 다르다")
    exporter["output_path"] = str(Path(nat_dir) / NAT_TRACE_NAME)
    return config


async def _run_workflow(api: SimpleNamespace, config: dict) -> None:
    with _Quiet("nat"):
        api.discover_and_register_plugins(api.PluginTypes.CONFIG_OBJECT)
    nat_config = api.Config(**config)
    async with api.WorkflowBuilder.from_config(config=nat_config) as builder:
        manager = await api.SessionManager.create(config=nat_config, shared_builder=builder, max_concurrency=1)
        try:
            async with manager.session() as session:
                async with session.run("tradesentry case") as runner:
                    await runner.result(to_type=str)
        finally:
            await manager.shutdown()


def read_nat_trace(api: SimpleNamespace, nat_dir: Path) -> list:
    _prepare_env()
    path = Path(nat_dir) / NAT_TRACE_NAME
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    return [api.IntermediateStep.model_validate_json(line) for line in lines if line.strip()]


def write_profile(steps: list, nat_dir: Path) -> list[str]:
    """NAT 프로파일러로 결과 파일을 nat_dir에 쓴다(이미 있으면 쓰지 않는다, N8). 쓴 파일 이름 목록을 돌려준다."""
    _prepare_env()
    with _Quiet("nat"):
        from nat.data_models.profiler import ProfilerConfig
        from nat.plugins.profiler.profile_runner import ProfilerRunner
    folder = Path(nat_dir)
    before = {p.name for p in folder.iterdir()}
    clash = before & set(PROFILE_FILES)
    if clash:
        raise FileExistsError(f"프로파일 파일이 이미 있다: {sorted(clash)}")
    config = ProfilerConfig(base_metrics=True, compute_llm_metrics=True, csv_exclude_io_text=True,
                            bottleneck_analysis={"enable_simple_stack": True})
    with _Quiet("nat.plugins.profiler"):
        asyncio.run(ProfilerRunner(config, folder, write_output=True).run([steps]))
    return sorted(p.name for p in folder.iterdir() if p.name not in before)


def summarize(steps: list) -> dict:
    """NAT 추적 요약(시각·UUID·경로 없음)."""
    types = [str(step.event_type.value) for step in steps]
    tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    for step in steps:
        usage = step.usage_info
        if str(step.event_type.value) == "LLM_END" and usage is not None:
            for key in tokens:
                tokens[key] += int(getattr(usage.token_usage, key) or 0)
    return {"nat_events": types, "workflow_end": bool(types) and types[-1] == "WORKFLOW_END",
            "llm_spans": types.count("LLM_END"), "tool_spans": types.count("TOOL_END"),
            "stage_spans": types.count("SPAN_END"), "tokens": tokens}


def run_under_nat(flow: Callable[[NatSink], object], nat_dir: Path, *, model: str,
                  workflow_config: Path | None = None, profile: bool = True) -> dict:
    """흐름 1건을 NAT로 감싸 돌린다. flow(nat_sink)는 우리 trace sink와 nat_sink를 함께 쓰도록 부르는 쪽이 짠다
    (예: trace.Tee(trace_writer, nat_sink)를 흐름 조정의 sink로 준다).

    nat_dir(N7 폴더)은 아직 없어야 하고 여기서 만든다. 돌려주는 값: {"result": flow의 반환값, "nat": 요약,
    "profile_files": 쓴 프로파일 파일 이름}. 흐름이 예외를 냈으면 NAT 추적·프로파일을 마저 쓴 뒤 그 예외를 다시 낸다.
    """
    if _ACTIVE:
        raise RuntimeError("NAT 감싸기는 한 프로세스에서 한 번에 한 흐름만 돈다")
    api = nat_api()
    config = load_workflow_config(Path(nat_dir), workflow_config)
    os.mkdir(nat_dir)  # 이미 있으면 FileExistsError(N8)
    _ACTIVE.update(flow=flow, model=model, result=None, error=None, sink=None)
    try:
        asyncio.run(_run_workflow(api, config))
        slot = dict(_ACTIVE)
    finally:
        _ACTIVE.clear()
    steps = read_nat_trace(api, Path(nat_dir))
    summary = summarize(steps)
    files = write_profile(steps, Path(nat_dir)) if profile and steps else []
    if slot["error"] is not None:
        raise slot["error"]
    return {"result": slot["result"], "nat": summary, "profile_files": files}


def run(inp: object) -> object:
    """기록된 trace(단위 L1 레코드)를 NAT로 감싼 흐름에 다시 흘려 NAT 추적·프로파일을 만든다(키·네트워크 없음).

    입력: {"trace": [trace 레코드], "model": 모델 ID(선택, 없으면 configs/model 설정)}.
    출력: {"nat": 요약(NAT 이벤트 순서, 구간 수, 토큰 합. 시각·UUID·경로 없음), "profile_files": 파일 이름}.
    임시 폴더에 쓰고 지운다(개발 전용 진입 함수).
    """
    import tempfile

    if not isinstance(inp, dict) or not isinstance(inp.get("trace"), list):
        raise ValueError("입력은 {trace[]}다")
    model = inp.get("model") or model_client.load_model_config().settings.model

    def flow(nat_sink: NatSink) -> str:
        for record in inp["trace"]:
            nat_sink.emit(record["event"], record.get("stage"), record.get("data") or {})
        return "replayed"

    with tempfile.TemporaryDirectory() as tmp:
        outcome = run_under_nat(flow, Path(tmp) / f"{DOMAIN}-000000000000", model=model)
    return {"nat": outcome["nat"], "profile_files": outcome["profile_files"]}
