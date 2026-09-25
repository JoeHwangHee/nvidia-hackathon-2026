"""평가 하네스(단위 E1·E3·E4) 시험의 공통 도우미. 파일 이름이 test로 시작하지 않으므로 시험으로 모이지 않는다.

- 가짜 시계(FakeClock): sleep이 시각을 앞으로 민다. 여러 스레드가 함께 써도 된다(자물쇠).
- 가짜 사례 실행 함수(FakeRunner): 사례 실행 폴더에 가짜 NAT 프로파일 파일을 쓰고 실행 쪽 키 21개를 돌려준다. 사례별로
  완료·인프라 실패·예외·잘못된 기록·키 불일치를 고를 수 있다. 실제 run-case(로드맵 AS2)의 대역이다.
- 계약 키 목록(contract_run_record_keys): 자료 계약 §8의 "명세 §4.10 원문" 키 줄을 문서에서 읽는다(채점기 코드를
  import하지 않고 계약에서 가져와 대조한다).
- 채점기 하네스 줄 검증의 독립 재구현(scorer_line_problems): 채점기 eval/scorer/results.py validate_batch_line이 거부하는
  모양을 계약(§3·§8)에서 다시 적었다. 채점기를 import하지 않는다.
"""
import json
import re
import threading
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from tradesentry.evaluation import batch_run
from tradesentry.runlog import cause_codes
from tradesentry.runlog import trace as trace_log

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "rules" / "DATA_CONTRACT_V1.md"
BASE = datetime(2026, 9, 25, 10, 0, 0, 250000, tzinfo=trace_log.KST)
VERSIONS = {"policy_version": "dev-0.1", "rulebook_version": "RB-1", "snapshot_id": "dev20",
            "grouping_version": "g0", "code_version": "abc1234"}
DEV20_MODES = ("checklist", "agent", "full")
PROFILE_FILES = ("all_requests_profiler_traces.json", "inference_optimization.json", "standardized_data_all.csv",
                 "workflow_profiling_metrics.json", "workflow_profiling_report.txt")  # 단위 I13 PROFILE_FILES


class FakeClock:
    """KST 가짜 시계. sleep만 시각을 민다. 여러 스레드가 함께 써도 된다."""

    def __init__(self, start: datetime = BASE):
        self.now = start
        self.lock = threading.Lock()

    def __call__(self) -> datetime:
        with self.lock:
            return self.now

    def sleep(self, seconds: float) -> None:
        with self.lock:
            self.now += timedelta(seconds=max(seconds, 0.001))

    def advance_ms(self, ms: int) -> None:
        with self.lock:
            self.now += timedelta(milliseconds=ms)


def dev20_cases(n: int = 20) -> list[dict]:
    """dev20 모양(사례 20건)의 합성 사례 목록. 식별자는 판정 정책 형식 {hs6}-{partner}-{month}다."""
    hs6s = ("850431", "850432", "850450", "850490")
    return [{"case_id": f"{hs6s[i % 4]}-X{chr(65 + i)}-2024{(i % 12) + 1:02d}", "hs6": hs6s[i % 4],
             "partner": f"X{chr(65 + i)}", "month": f"2024{(i % 12) + 1:02d}"} for i in range(n)]


def contract_run_record_keys() -> tuple[str, ...]:
    """자료 계약 §8 "명세 §4.10 원문"의 키 줄(백틱 안 쉼표 목록)을 읽는다."""
    text = CONTRACT.read_text(encoding="utf-8")
    section = text.split("## 8. 실행 결과 기록", 1)[1]
    match = re.search(r"`(run_id,[^`]+)`", section)
    return tuple(k.strip() for k in match.group(1).split(","))


SCORER_KEYS = ("required_evidence_ok", "numeric_ok", "provenance_ok")  # 자료 계약 §8.1 기록 주체 "정답 대조 채점"


def scorer_line_problems(line: object) -> list[str]:
    """채점기가 묶음 기록 한 줄에서 거부하는 모양(자료 계약 §3·§8, 채점기 C3 validate_batch_line과 같은 규칙)."""
    keys = contract_run_record_keys()
    run_side = [k for k in keys if k not in SCORER_KEYS]
    if not isinstance(line, dict):
        return ["객체가 아니다"]
    problems = []
    if set(line) - set(keys) or [k for k in run_side if k not in line]:
        return ["키가 계약과 다르다"]
    if not isinstance(line["run_id"], str) or not re.fullmatch(r"[a-z][a-z0-9_]*-[0-9]{12}", line["run_id"]):
        problems.append("run_id")
    if not isinstance(line["case_id"], str) or not line["case_id"]:
        problems.append("case_id")
    for key, allowed in (("dataset", ("controlled_fixture_v0", "dev20", "holdout40", "real_dev", "real_sealed")),
                         ("mode", ("checklist", "agent", "full", "freeform")),
                         ("execution_status", ("COMPLETED", "FAILED", "TIMEOUT", "INVALID", "BUDGET_EXCEEDED"))):
        if line[key] not in allowed:
            problems.append(key)
    for key in batch_run.VERSION_KEYS:
        if not isinstance(line[key], str) or not line[key]:
            problems.append(key)
    completed = line["execution_status"] == "COMPLETED"
    review = line["review_status_final"]
    if completed and review not in ("MAINTAIN", "MONITOR", "HOLD") or not completed and review is not None:
        problems.append("review_status_final")
    signal = line["signal_status"]
    signal_ok = isinstance(signal, dict) and set(signal) == {"unit_value", "share"} \
        and all(v in ("MAINTAIN", "MONITOR", "HOLD", "NOT_TRIGGERED") for v in signal.values())
    if not signal_ok and (completed or signal is not None):
        problems.append("signal_status")
    for key in ("unresolved_evidence", "critic_used", "revision_used"):
        if not isinstance(line[key], bool) and (completed or line[key] is not None):
            problems.append(key)
    for key in ("tool_attempts", "model_requests", "tokens_in", "tokens_out", "wall_ms"):
        value = line[key]
        if not (isinstance(value, int) and not isinstance(value, bool) and value >= 0) and (completed
                                                                                           or value is not None):
            problems.append(key)
    if not isinstance(line["errors"], list):
        problems.append("errors")
    return problems


def completed_record(call: batch_run.CaseCall, *, model_requests: int = 4, tokens_in: int = 9000,
                     tokens_out: int = 900, wall_ms: int = 40000) -> dict:
    checklist = call.mode == "checklist"
    return {"run_id": call.run_id, "case_id": call.case["case_id"], "dataset": call.dataset, "mode": call.mode,
            **call.versions, "review_status_final": "MONITOR",
            "signal_status": {"unit_value": "MONITOR", "share": "NOT_TRIGGERED"}, "unresolved_evidence": False,
            "execution_status": "COMPLETED", "tool_attempts": 5,
            "model_requests": 0 if checklist else model_requests, "tokens_in": 0 if checklist else tokens_in,
            "tokens_out": 0 if checklist else tokens_out, "wall_ms": wall_ms,
            "critic_used": call.mode in ("full", "freeform"), "revision_used": False, "errors": []}


def failed_record(call: batch_run.CaseCall, code: str = cause_codes.PROVIDER_HTTP_5XX) -> dict:
    model = (0, 0, 0) if call.mode == "checklist" else (4, 3000, 100)  # checklist는 모델 요청·토큰 0
    attempts = {"tool_attempts": 2, "model_requests": model[0], "tokens_in": model[1], "tokens_out": model[2],
                "wall_ms": 9000}
    return {**completed_record(call), "review_status_final": None, "signal_status": None,
            "execution_status": cause_codes.execution_status(code), "tool_attempts": 2, "model_requests": model[0],
            "tokens_in": model[1], "tokens_out": model[2], "wall_ms": 9000, "critic_used": False,
            "errors": [cause_codes.error_entry(code, "basic", attempts, [], "HTTP 503")]}


def write_profile(nat_dir: Path, *, llm: list[tuple[int, int, int]], spans: list[str], workflow_ms: int,
                  tools: int = 1, files: tuple[str, ...] = PROFILE_FILES, nat_trace: bool = True,
                  workflow_end: bool = True) -> None:
    """NAT 프로파일 폴더를 흉내 낸다(실측 모양: all_requests_profiler_traces.json의 intermediate_steps payload).
    llm은 (지속 ms, 입력 토큰, 출력 토큰) 목록, spans는 단계 이름 목록이다. data·metadata는 넣지 않는다."""
    nat_dir.mkdir()
    t0 = Decimal("1790281845.000000")
    steps = [{"payload": {"event_type": "WORKFLOW_START", "event_timestamp": t0, "name": "tradesentry_case"}}]
    t = t0
    for stage in spans:
        steps.append({"payload": {"event_type": "SPAN_START", "event_timestamp": t, "name": stage}})
        steps.append({"payload": {"event_type": "SPAN_END", "event_timestamp": t + Decimal("0.001"),
                                  "span_event_timestamp": t, "name": stage}})
    for duration, prompt, completion in llm:
        start = t
        t = t + Decimal(duration) / 1000
        steps.append({"payload": {"event_type": "LLM_START", "event_timestamp": start, "name": "model"}})
        steps.append({"payload": {"event_type": "LLM_END", "event_timestamp": t, "span_event_timestamp": start,
                                  "name": "model", "usage_info": {"token_usage": {
                                      "prompt_tokens": prompt, "completion_tokens": completion,
                                      "total_tokens": prompt + completion}}}})
    for _ in range(tools):
        steps.append({"payload": {"event_type": "TOOL_START", "event_timestamp": t, "name": "get_history"}})
        steps.append({"payload": {"event_type": "TOOL_END", "event_timestamp": t, "span_event_timestamp": t,
                                  "name": "get_history"}})
    if workflow_end:
        steps.append({"payload": {"event_type": "WORKFLOW_END", "event_timestamp": t0 + Decimal(workflow_ms) / 1000,
                                  "name": "tradesentry_case"}})
    if nat_trace:
        (nat_dir / "nat_trace.jsonl").write_text("{}\n", encoding="utf-8")
    for name in files:
        path = nat_dir / name
        if name == "all_requests_profiler_traces.json":
            path.write_text(trace_log.dumps([{"request_number": 0, "intermediate_steps": steps}]), encoding="utf-8")
        else:
            path.write_text("{}" if name.endswith(".json") else "x\n", encoding="utf-8")


class FakeRunner:
    """가짜 사례 실행 함수. plan: case_id → 동작(완료가 기본). 동작: "ok", "infra"(5xx FAILED), "budget", "raise",
    "invalid"(키가 빠진 기록), "mismatch"(다른 run_id), "interrupt"(KeyboardInterrupt). 부를 때마다 시계를 민다."""

    def __init__(self, clock: FakeClock | None = None, plan: dict | None = None, profile: bool = True):
        self.clock = clock
        self.plan = plan or {}
        self.profile = profile
        self.calls: list[batch_run.CaseCall] = []

    def __call__(self, call: batch_run.CaseCall) -> dict:
        self.calls.append(call)
        assert call.run_dir.is_dir() and not any(call.run_dir.iterdir()), "사례 실행 폴더는 확보한 빈 폴더다"
        if self.clock is not None:
            self.clock.advance_ms(250)
        action = self.plan.get((call.case["case_id"], call.mode), self.plan.get(call.case["case_id"], "ok"))
        if self.profile and action in ("ok", "infra", "budget") and call.mode != "checklist":
            write_profile(call.run_dir / f"workflow_nat_wrap-{call.stamp}", llm=[(1200, 2800, 80), (2400, 3000, 150)],
                          spans=["basic", "critic"] if call.mode == "full" else ["basic"], workflow_ms=6000)
        (call.run_dir / f"runlog_trace-{call.stamp}.jsonl").write_text("", encoding="utf-8")
        if action == "ok":
            return completed_record(call)
        if action == "infra":
            return failed_record(call)
        if action == "budget":
            return failed_record(call, cause_codes.BUDGET_TOKENS)
        if action == "raise":
            raise RuntimeError("사례 실행 실패(가짜)")
        if action == "invalid":
            record = completed_record(call)
            del record["errors"]
            return record
        if action == "mismatch":
            return {**completed_record(call), "run_id": "run_case-000000000000"}
        if action == "interrupt":
            raise KeyboardInterrupt
        raise AssertionError(action)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line, parse_float=Decimal) for line in path.read_text(encoding="utf-8").split("\n") if line]
