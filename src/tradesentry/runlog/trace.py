"""단위 L1 trace 기록.

단위 ID: L1
도메인명: runlog_trace
소유: 공동
입력: 이벤트
출력: trace JSONL(형식은 S0 자문 Q21)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.runlog

trace(실행 중 호출과 응답을 순서대로 남긴 기록)는 사례 실행 1건에 파일 1개다. 파일 이름은 이름·출력 규칙(자료 계약
§10.3 N6)대로 {실행 폴더}/runlog_trace-{yymmddhhmmss}.jsonl이고, 실행 폴더는 부르는 쪽이 인자로 준다(S0 결정 ⑥:
단위 안에 outputs/ 기본값을 두지 않는다). 파일은 이미 있으면 실패하는 방식(open 모드 "x")으로 만든다(N8).

한 줄(레코드)의 키
- seq: 1부터 세는 순번. ts: KST ISO 8601 시각(초 단위, 자료 계약 §11.4). run_id: 실행명 {실행 이름}-{yymmddhhmmss}(N5).
- event: EVENT_TYPES 가운데 하나. stage: STAGES 가운데 하나이거나 null. data: 이벤트별 값(객체).
- 수는 int와 Decimal만 쓴다. Decimal은 원문 표기 그대로 JSON 숫자로 쓴다(끝자리 0 보존). float·NaN은 거부한다.
- 키 값(인증 헤더·API 키)은 싣지 않는다. 헤더는 전송 단계에서만 만들어지고 여기로 오지 않는다. 방어로, 이름이
  FORBIDDEN_DATA_KEYS에 드는 키가 data 안에 있으면 쓰지 않고 ValueError를 낸다(자료 계약 N13).

이벤트(Q21 제안)
- run_start·run_end: 실행의 시작과 끝(끝에는 execution_status·원인 분류 코드·누적 값).
- stage_start·stage_end: 흐름 단계(basic 기본 조사, critic 검수, revision 수정 1회, final 최종 검증).
- model_request·model_response·model_error: NIM(NVIDIA 클라우드 추론 API) HTTP 시도 1회마다. 재전송도 한 번씩 적는다.
  model_response에는 기록 재생(단위 I8)에 쓰는 응답 본문(message·finish_reason·usage)을 싣는다.
- tool_call·tool_result: 도구 시도와 봉투. budget_block: 예산·단계 한도로 막은 시도.
- state_change: 모델 원초안(draft) → Critic 뒤(after_critic) → 수정 뒤(revised) → 확정(final)의 판정 상태.
- validator_result: 스키마 검사와 검증기 판정(findings).
"""
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Callable, Protocol

KST = timezone(timedelta(hours=9), "KST")
DOMAIN = "runlog_trace"
RUN_ID_RE = re.compile(r"^[a-z][a-z0-9_]*-\d{12}$")
TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+09:00$")
EVENT_TYPES = frozenset({
    "run_start", "run_end", "stage_start", "stage_end",
    "model_request", "model_response", "model_error",
    "tool_call", "tool_result", "budget_block", "state_change", "validator_result",
})
STAGES = frozenset({"basic", "critic", "revision", "final"})
RECORD_KEYS = ("seq", "ts", "run_id", "event", "stage", "data")
FORBIDDEN_DATA_KEYS = frozenset({"authorization", "api_key", "apikey", "x-api-key", "bearer", "password", "secret"})


class Sink(Protocol):
    """이벤트를 받는 쪽. trace 파일, 메모리, NAT 추적(단위 I13)이 같은 모양으로 받는다."""

    def emit(self, event: str, stage: str | None, data: dict) -> None:
        ...


def now_kst() -> datetime:
    return datetime.now(KST)


def iso_kst(moment: datetime) -> str:
    return moment.astimezone(KST).isoformat(timespec="seconds")


def dumps(value: object, sort_keys: bool = False) -> str:
    """JSON 한 줄로 쓴다. Decimal은 원문 표기의 JSON 숫자, float·NaN·무한대·문자열 아닌 키는 거부한다."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("trace에 NaN·무한대 Decimal을 쓰지 않는다")
        return str(value)
    if isinstance(value, float):
        raise ValueError("trace에 float를 쓰지 않는다(수는 int나 Decimal)")
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (list, tuple)):
        return "[" + ",".join(dumps(v, sort_keys) for v in value) + "]"
    if isinstance(value, dict):
        parts = []
        for key in (sorted(value) if sort_keys else value):
            if not isinstance(key, str):
                raise ValueError(f"trace 객체의 키는 문자열이어야 한다: {type(key).__name__}")
            parts.append(json.dumps(key, ensure_ascii=False) + ":" + dumps(value[key], sort_keys))
        return "{" + ",".join(parts) + "}"
    raise ValueError(f"trace에 쓸 수 없는 값: {type(value).__name__}")


def loads(text: str) -> object:
    """dumps의 반대. 소수는 Decimal로 읽는다."""
    return json.loads(text, parse_float=Decimal)


def canonical_sha256(value: object) -> str:
    """키를 정렬한 dumps 바이트의 sha256(16진수 소문자 64자). 모델 요청(I7)과 기록 재생(I8)이 같은 요청인지 맞춰 본다."""
    return hashlib.sha256(dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def _check_data(value: object, path: str = "data") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str) and key.lower() in FORBIDDEN_DATA_KEYS:
                raise ValueError(f"{path}에 싣지 않는 키가 있다: {key}")
            _check_data(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _check_data(item, f"{path}[{index}]")


def make_record(seq: int, ts: str, run_id: str, event: str, stage: str | None, data: dict | None) -> dict:
    """레코드 하나를 검사해 만든다. 규칙에 어긋나면 ValueError를 낸다."""
    if not isinstance(seq, int) or isinstance(seq, bool) or seq < 1:
        raise ValueError(f"seq는 1 이상의 정수다: {seq!r}")
    if not isinstance(ts, str) or not TS_RE.match(ts):
        raise ValueError("ts는 초 단위 KST ISO 8601 문자열(예: 2026-09-25T14:30:15+09:00)이다")
    if not isinstance(run_id, str) or not RUN_ID_RE.match(run_id):
        raise ValueError(f"run_id가 실행명 형식이 아니다: {run_id!r}")
    if event not in EVENT_TYPES:
        raise ValueError(f"알 수 없는 trace 이벤트: {event!r}")
    if stage is not None and stage not in STAGES:
        raise ValueError(f"알 수 없는 단계: {stage!r}")
    data = {} if data is None else data
    if not isinstance(data, dict):
        raise ValueError("data는 객체다")
    _check_data(data)
    record = {"seq": seq, "ts": ts, "run_id": run_id, "event": event, "stage": stage, "data": data}
    dumps(record)  # float 등 쓸 수 없는 값을 여기서 거른다
    return record


class MemoryTrace:
    """레코드를 메모리 목록에 모은다(시험과 기록 재생용)."""

    def __init__(self, run_id: str, clock: Callable[[], datetime] = now_kst):
        self.run_id = run_id
        self.records: list[dict] = []
        self._clock = clock

    def emit(self, event: str, stage: str | None, data: dict) -> None:
        self.records.append(make_record(len(self.records) + 1, iso_kst(self._clock()), self.run_id, event, stage, data))


class TraceWriter(MemoryTrace):
    """레코드를 파일에 한 줄씩 쓴다. 파일은 새로 만들고(이미 있으면 FileExistsError) 줄마다 flush한다."""

    def __init__(self, path: Path, run_id: str, clock: Callable[[], datetime] = now_kst):
        super().__init__(run_id, clock)
        self._fh = open(path, "x", encoding="utf-8")

    def emit(self, event: str, stage: str | None, data: dict) -> None:
        super().emit(event, stage, data)
        self._fh.write(dumps(self.records[-1]) + "\n")
        self._fh.flush()

    def close(self) -> None:
        if not self._fh.closed:
            self._fh.close()


class Tee:
    """여러 sink에 같은 이벤트를 차례로 넘긴다."""

    def __init__(self, *sinks: Sink):
        self.sinks = [s for s in sinks if s is not None]

    def emit(self, event: str, stage: str | None, data: dict) -> None:
        for sink in self.sinks:
            sink.emit(event, stage, data)


class NullSink:
    def emit(self, event: str, stage: str | None, data: dict) -> None:
        return None


def trace_path(run_dir: Path, stamp: str) -> Path:
    """실행 폴더 안 trace 파일 경로(N6). stamp는 실행명의 yymmddhhmmss."""
    if not re.fullmatch(r"\d{12}", stamp):
        raise ValueError("stamp는 yymmddhhmmss 12자리다")
    return run_dir / f"{DOMAIN}-{stamp}.jsonl"


def read_records(path: Path) -> list[dict]:
    """trace 파일을 레코드 목록으로 읽는다."""
    return [loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run(inp: object) -> object:
    """이벤트 목록을 검사한 trace 레코드 목록(JSONL 한 줄씩)으로 바꾼다.

    입력: {"run_id": 실행명, "events": [{"ts": KST ISO 시각, "event": 이벤트, "stage": 단계 또는 null,
    "data": 객체}, ...]}. 출력: 순번(seq)을 붙인 레코드 목록. 규칙에 어긋나는 이벤트가 있으면 ValueError다.
    """
    if not isinstance(inp, dict) or not isinstance(inp.get("events"), list):
        raise ValueError("입력은 {run_id, events[]}다")
    run_id = inp.get("run_id")
    return [make_record(index, event.get("ts"), run_id, event.get("event"), event.get("stage"), event.get("data"))
            for index, event in enumerate(inp["events"], start=1)]
