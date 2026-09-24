"""단위 E1 묶음 실행.

단위 ID: E1
도메인명: evaluation_batch_run
소유: M
입력: 사례 목록 × 모드
출력: 교차 배치 실행, 실행 결과 기록의 실행 쪽 키(`evaluation_batch_run-{시각}.jsonl`)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.runlog, tradesentry.policy, tradesentry.workflow

S0 제안: 사례 실행은 묶음 폴더 안이 아니라 형제 폴더 outputs/run_case-{시각}/에 두고, 묶음 기록의 줄마다 적는 run_id로 잇는다.

호스트 전용 샌드박스 밖 실행기 E2(tradesentry.evaluation.sealed_runner)를 import하지 않는다(경계 시험이 본다).

정본: docs/plan/UNITS.md E1 행, 자료 계약 docs/rules/DATA_CONTRACT_V1.md §8·§10.3 N5·N6·N8, 룰북 docs/eval/RULEBOOK.md B2·B5.

세 가지를 한다.
1. 실행 순서(run): (사례, 모드) 목록을 고정 seed로 섞는다(룰북 B5 교차 배치). 순수 함수라 골든 시험의 대상이다.
   섞는 법(바이트 수준으로 고정. 샌드박스 밖 실행기 E2는 이 모듈을 import할 수 없으므로 같은 규칙을 따로 구현한다):
   (사례, 모드)마다 열쇠 = sha256(UTF-8 바이트 "{seed}\\n{case_id}\\n{mode}")의 16진수 소문자 64자를 만들고, 열쇠 →
   case_id → mode 순으로 오름차순 정렬한다. seed와 목록이 같으면 파이썬 판과 관계없이 같은 순서다.
2. 묶음 실행(execute_batch): 묶음 실행 폴더 outputs/evaluate-{시각}/를 확보하고, 순서대로 동시성 1로 사례마다 새
   실행명 run_case-{시각}을 확보한 뒤(N8, 단위 L2 reserve_run_dir) 주입받은 사례 실행 함수를 부른다. 사례 실행 폴더는
   묶음 폴더의 형제다(채점기는 <run_dir>의 부모에서 run_id 이름의 폴더를 연다). 사례 실행 함수는 실제로는 run-case
   처리 함수와 같은 조립(로드맵 AS2)이 준다. 여기서는 모양(CaseCall → 실행 쪽 키 21개의 객체)만 정한다.
   - 묶음 기록 evaluation_batch_run-{시각}.jsonl은 이미 있으면 실패하는 방식("x")으로 한 번 열고, 사례 실행이 끝날
     때마다 한 줄을 쓰고 비운다(flush). 도중에 멈춰도 끝난 줄은 남는다. 줄이 없는 계획 조합은 채점기가 미실행으로
     분모에 실패로 센다(자료 계약 §8.2).
   - 사례 실행 함수가 예외를 내거나, 돌려준 기록이 단위 L2 검사를 통과하지 못하거나, 실행 전에 정해지는 키(실행명·
     사례·자료 묶음·모드·버전 키 5개)가 묶음이 준 값과 다르면, 그 사례를 FAILED 줄(원인 CODE_ERROR, detail은
     "harness:" 뒤에 예외 이름이나 사유 이름만, 측정한 wall_ms)로 남긴다. 줄을 버리지 않는다(분모, 룰북 B5).
   - 모든 모드에 같은 자료·버전·사례 실행 함수를 쓴다. 묶음 안에서 인프라 실패 재실행은 하지 않는다(한 번 돈다).
     재실행 대상 목록은 단위 E3가 만들고, 재실행을 원래 실행과 잇는 방법은 로드맵 MT7의 다음 PR에서 정한다.
   - 봉인 묶음(holdout40·real_sealed)은 받지 않는다. 봉인 묶음은 샌드박스 밖 실행기 E2가 돌린다(자료 계약 §8.2).
3. 실행 조건 입력 파일(build_run_conditions·write_run_conditions): 채점기가 모르는 실행 조건을 채점기에 넘기는 파일
   run_conditions-{시각}.json을 내려받기를 끝낸 호스트 쪽 프로그램이 확보한 실행 폴더에 배타 생성한다(자료 계약 §8.2).
   형식은 MVP 전 임시 형식이다(결정 D6, 채점기 DT8 1회차 보고 §5와 같은 키. F1 전에 확정한다). 봉인 묶음이면 봉인
   출력이 있어야 하는 값(nat_profile_summary, korean_sample_review)을 넣지 않는다. 값에 로컬 절대경로 모양이나 키
   모양이 있으면 쓰지 않는다(N13, 절대 규칙 1).

이 모듈은 .env를 읽지 않고 키 변수를 쓰지 않는다. 키가 필요한 모델 호출은 사례 실행 함수 안에서만 일어난다.
"""
import hashlib
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Callable

from tradesentry.contract import types
from tradesentry.runlog import cause_codes, run_record
from tradesentry.runlog import trace as trace_log

DOMAIN = "evaluation_batch_run"
BATCH_RUN_NAME = "evaluate"  # 평가 묶음 실행의 실행 이름(자료 계약 §10.3 N5)
CASE_RUN_NAME = "run_case"  # 묶음이 부르는 사례 실행의 실행 이름(N5의 CLI 명령 run-case)
CONDITIONS_DOMAIN = "run_conditions"  # 실행 조건 입력 파일(채점기 DT8 임시 형식)
CASE_KEYS = ("case_id", "hs6", "partner", "month")  # 계획 사례 항목(채점기 planned_cases)
VERSION_KEYS = ("policy_version", "rulebook_version", "snapshot_id", "grouping_version", "code_version")
STATIC_KEYS = ("run_id", "case_id", "dataset", "mode") + VERSION_KEYS
UNSEALED_DATASETS = tuple(d for d in types.DATASETS if d not in types.SEALED_DATASETS)
CONCURRENCY = 1  # 룰북 B5: 1로 시작한다
HARNESS_DETAIL = "harness:"

# 실행 조건 입력 파일의 키(임시 형식. 채점기 DT8 1회차 보고 §5의 키 집합과 같다).
CONDITION_KEYS = ("dataset", "planned_cases", "planned_modes", "snapshot", "policy_detection_thresholds", "rulebook",
                  "grouping_reason", "scorer_commit", "prose_patterns_commit", "run_period", "concurrency",
                  "order_seed", "limits", "sandbox", "sealed_hash_recheck", "sealed_provenance_check", "precheck",
                  "prescoring_checks", "skill_call_success", "nat_profile_summary", "korean_sample_review",
                  "reproduce_evaluate", "a_grade")
CONDITION_REQUIRED = ("dataset", "planned_cases", "planned_modes", "policy_detection_thresholds")
SEALED_FORBIDDEN = ("nat_profile_summary", "korean_sample_review")  # 봉인 출력이 있어야 하는 값(자료 계약 §8.2)
LIMIT_KEYS = ("tool_attempts", "reinvestigation", "model_requests", "wall_time_s", "tokens")  # 요약 한도 칸(룰북 B7)

# 로컬 절대경로 모양(N13)과 키 모양(절대 규칙 1). 채점기 코드는 import하지 않고, 채점기가 거부하는 모양보다 넓게 잡는다:
# 값의 처음이나 공백·따옴표·구분 기호 뒤의 "/", 역슬래시 두 개(UNC), 드라이브 문자, 값의 처음이나 구분 기호 뒤의 물결표.
_PATH_START = r"(?:^|(?<=[\s\"'=(,;:<>\[{|]))"
PATH_SHAPE = re.compile(_PATH_START + r"/(?=[^\s/])|\\\\|(?<![A-Za-z0-9])[A-Za-z]:[\\/]|" + _PATH_START + r"~")
SECRET_SHAPE = re.compile("nv" + "api-|service" + r"Key\s*=", re.I)  # 패턴 글자를 나눠 적는다(이 파일이 검사에 걸리지 않게)


class BatchError(ValueError):
    """묶음 입력이나 실행 조건이 규칙에 맞지 않는다(폴더·파일을 만들기 전에 낸다)."""


# ----------------------------------------------------------------------------- 1. 실행 순서

def order_key(seed: str, case_id: str, mode: str) -> str:
    """(사례, 모드)의 섞기 열쇠(머리 설명 1)."""
    return hashlib.sha256(f"{seed}\n{case_id}\n{mode}".encode("utf-8")).hexdigest()


def _check_plan(case_ids: object, modes: object, seed: object) -> None:
    if not isinstance(seed, str) or not seed:
        raise BatchError("순서 seed는 빈 문자열이 아닌 문자열이다")
    if not isinstance(case_ids, list) or not case_ids or not all(isinstance(c, str) and c for c in case_ids):
        raise BatchError("사례 목록은 빈 문자열이 아닌 case_id의 목록이다")
    if len(set(case_ids)) != len(case_ids):
        raise BatchError("사례 목록에 같은 case_id가 두 번 있다")
    if not isinstance(modes, list) or not modes or any(m not in types.MODES for m in modes) \
            or len(set(modes)) != len(modes):
        raise BatchError(f"모드 목록은 {'·'.join(types.MODES)} 가운데 서로 다른 값의 목록이다")


def plan_order(case_ids: list, modes: list, seed: str) -> list[tuple[str, str]]:
    """(사례, 모드) 실행 순서(룰북 B5)."""
    _check_plan(case_ids, modes, seed)
    pairs = [(c, m) for c in case_ids for m in modes]
    return sorted(pairs, key=lambda p: (order_key(seed, p[0], p[1]), p[0], p[1]))


# ----------------------------------------------------------------------------- 2. 묶음 실행

@dataclass(frozen=True)
class BatchSpec:
    """묶음 하나의 입력. cases는 CASE_KEYS 네 키의 객체 목록, versions는 VERSION_KEYS 다섯 키의 객체다."""
    dataset: str
    cases: tuple
    modes: tuple
    order_seed: str
    versions: dict = field(default_factory=dict)


@dataclass(frozen=True)
class CaseCall:
    """사례 실행 함수에 넘기는 것. run_dir은 이미 확보한 빈 사례 실행 폴더이고, 출력은 그 안에 stamp로 쓴다(N6)."""
    run_id: str
    stamp: str
    run_dir: Path
    case: dict
    mode: str
    dataset: str
    versions: dict


@dataclass
class BatchResult:
    run_id: str
    stamp: str
    run_dir: Path
    lines: list
    started: datetime
    ended: datetime

    @property
    def batch_file(self) -> Path:
        return self.run_dir / f"{DOMAIN}-{self.stamp}.jsonl"


CaseRunner = Callable[[CaseCall], dict]


def check_spec(spec: BatchSpec) -> None:
    """묶음 입력 검사(폴더를 만들기 전에)."""
    if spec.dataset not in UNSEALED_DATASETS:
        raise BatchError("묶음 실행 E1은 봉인 묶음이 아닌 자료 묶음(controlled_fixture_v0·dev20·real_dev)만 돌린다")
    cases = list(spec.cases)
    for case in cases:
        if not isinstance(case, dict) or set(case) != set(CASE_KEYS) \
                or not all(isinstance(case[k], str) and case[k] for k in CASE_KEYS):
            raise BatchError("사례 항목은 case_id·hs6·partner·month 네 문자열 키의 객체다")
    _check_plan([c["case_id"] for c in cases], list(spec.modes), spec.order_seed)
    versions = spec.versions
    if not isinstance(versions, dict) or set(versions) != set(VERSION_KEYS) \
            or not all(isinstance(versions[k], str) and versions[k] for k in VERSION_KEYS):
        raise BatchError(f"버전 키는 {'·'.join(VERSION_KEYS)} 다섯 개의 빈 문자열이 아닌 문자열이다")


def _ms(start: datetime, end: datetime) -> int:
    return max(0, int((end - start).total_seconds() * 1000))


def failure_line(call: CaseCall, wall_ms: int, reason: str) -> dict:
    """하네스가 남기는 FAILED 줄(원인 CODE_ERROR). reason은 예외 이름이나 사유 이름뿐이다(값·경로를 넣지 않는다)."""
    attempts = {key: 0 for key in cause_codes.ATTEMPT_KEYS}
    attempts["wall_ms"] = wall_ms
    entry = cause_codes.error_entry(cause_codes.CODE_ERROR, None, attempts, [], HARNESS_DETAIL + reason)
    facts = {"run_id": call.run_id, "case_id": call.case["case_id"], "dataset": call.dataset, "mode": call.mode,
             **call.versions, "review_status_final": None, "signal_status": None, "unresolved_evidence": False,
             "execution_status": cause_codes.FAILED, "tool_attempts": 0, "model_requests": 0, "tokens_in": 0,
             "tokens_out": 0, "wall_ms": wall_ms, "critic_used": False, "revision_used": False, "errors": [entry]}
    return run_record.build_record(facts)


def accept_record(call: CaseCall, record: object) -> tuple[dict | None, str | None]:
    """사례 실행 함수가 돌려준 기록을 받는다. (계약 순서의 줄, None) 또는 (None, 거부 사유 이름)."""
    try:
        line = run_record.build_record(record)  # type: ignore[arg-type]
    except ValueError:
        return None, "invalid_record"
    expected = {"run_id": call.run_id, "case_id": call.case["case_id"], "dataset": call.dataset, "mode": call.mode,
                **call.versions}
    if any(line[k] != expected[k] for k in STATIC_KEYS):
        return None, "record_mismatch"
    return line, None


def execute_batch(spec: BatchSpec, runner: CaseRunner, *, parent: Path, other_parent: Path,
                  clock: Callable[[], datetime] | None = None,
                  sleep: Callable[[float], None] | None = None) -> BatchResult:
    """묶음 하나를 돌린다(머리 설명 2). parent는 outputs/, other_parent는 outputs/sealed/다(N8).

    사례 실행명을 확보하지 못하면(RunNameError) 거기서 멈춘다. 쓴 줄은 남고, 남은 계획 조합은 미실행으로 분모에 남는다.
    """
    check_spec(spec)
    if parent.name == "sealed":
        raise BatchError("묶음 실행 E1은 outputs/sealed/ 아래에 쓰지 않는다(봉인 묶음은 E2)")
    clock = clock or trace_log.now_kst
    reserve_kw: dict = {"clock": clock}
    if sleep is not None:
        reserve_kw["sleep"] = sleep
    order = plan_order([c["case_id"] for c in spec.cases], list(spec.modes), spec.order_seed)
    cases = {c["case_id"]: dict(c) for c in spec.cases}
    versions = {k: spec.versions[k] for k in VERSION_KEYS}
    batch_id, stamp, batch_dir = run_record.reserve_run_dir(parent, other_parent, BATCH_RUN_NAME, **reserve_kw)
    started = clock()
    lines: list[dict] = []
    with open(batch_dir / f"{DOMAIN}-{stamp}.jsonl", "x", encoding="utf-8", newline="\n") as out:
        for case_id, mode in order:
            run_id, case_stamp, case_dir = run_record.reserve_run_dir(parent, other_parent, CASE_RUN_NAME,
                                                                      **reserve_kw)
            call = CaseCall(run_id=run_id, stamp=case_stamp, run_dir=case_dir, case=dict(cases[case_id]), mode=mode,
                            dataset=spec.dataset, versions=dict(versions))
            begin = clock()
            try:
                record = runner(call)
            except Exception as exc:  # 사례 하나의 실패로 남긴다(예외 이름만, N13)
                line = failure_line(call, _ms(begin, clock()), type(exc).__name__)
            else:
                line, reason = accept_record(call, record)
                if line is None:
                    line = failure_line(call, _ms(begin, clock()), reason or "invalid_record")
            out.write(trace_log.dumps(line) + "\n")
            out.flush()
            lines.append(line)
    return BatchResult(run_id=batch_id, stamp=stamp, run_dir=batch_dir, lines=lines, started=started, ended=clock())


# ----------------------------------------------------------------------------- 3. 실행 조건 입력 파일

def _strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [k for k in value if isinstance(k, str)] + [s for v in value.values() for s in _strings(v)]
    if isinstance(value, (list, tuple)):
        return [s for v in value for s in _strings(v)]
    return []


def limits_from_run_limits(limits: object) -> dict:
    """모델 설정의 한도(단위 I7 RunLimits 또는 같은 키의 객체)를 요약 한도 칸(LIMIT_KEYS)으로 옮긴다.
    재조사 = 수정 단계 수(revision_stages), 사례당 wall time은 초(wall_ms ÷ 1000, 나누어떨어질 때만)."""
    def get(key: str) -> object:
        return limits.get(key) if isinstance(limits, dict) else getattr(limits, key, None)

    values = {"tool_attempts": get("tool_attempts"), "reinvestigation": get("revision_stages"),
              "model_requests": get("model_requests"), "wall_ms": get("wall_ms"), "tokens": get("tokens")}
    if not all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in values.values()) \
            or values["wall_ms"] % 1000:
        raise BatchError("한도는 0 이상의 정수이고 wall_ms는 1000의 배수다")
    return {"tool_attempts": values["tool_attempts"], "reinvestigation": values["reinvestigation"],
            "model_requests": values["model_requests"], "wall_time_s": values["wall_ms"] // 1000,
            "tokens": values["tokens"]}


def build_run_conditions(*, dataset: str, cases: list, modes: list, thresholds: list, order_seed: str | None = None,
                         concurrency: int = CONCURRENCY, limits: dict | None = None,
                         run_period: tuple[datetime, datetime] | None = None, nat_profile_summary: object = None,
                         extra: dict | None = None) -> dict:
    """실행 조건 입력 파일의 내용(임시 형식)을 만든다. 하네스가 아는 값만 채운다. 나머지(채점기 커밋, 사전 점검 결과 등)는
    extra로 받되 CONDITION_KEYS 안의 키만 받는다. 봉인 묶음이면 SEALED_FORBIDDEN을 받지 않는다."""
    doc: dict = {"dataset": dataset,
                 "planned_cases": [{k: c[k] for k in CASE_KEYS} for c in cases],
                 "planned_modes": list(modes),
                 "policy_detection_thresholds": list(thresholds)}
    if order_seed is not None:
        doc["order_seed"] = order_seed
    doc["concurrency"] = concurrency
    if limits is not None:
        doc["limits"] = {k: limits[k] for k in LIMIT_KEYS}
    if run_period is not None:
        doc["run_period"] = {"start": trace_log.iso_kst(run_period[0]), "end": trace_log.iso_kst(run_period[1])}
    if nat_profile_summary is not None:
        doc["nat_profile_summary"] = nat_profile_summary
    for key, value in (extra or {}).items():
        if key in doc:
            raise BatchError(f"실행 조건 {key}를 두 번 줬다")
        doc[key] = value
    check_run_conditions(doc)
    return doc


def check_run_conditions(doc: object) -> None:
    """임시 형식 검사. 채점기의 거부 규칙 가운데 하네스가 지킬 것을 먼저 본다(채점기가 다시 본다)."""
    if not isinstance(doc, dict):
        raise BatchError("실행 조건 입력 파일은 객체다")
    unknown = sorted(set(doc) - set(CONDITION_KEYS))
    if unknown:
        raise BatchError(f"실행 조건 입력 파일의 약속 밖 키: {', '.join(unknown)}")
    missing = [k for k in CONDITION_REQUIRED if k not in doc]
    if missing:
        raise BatchError(f"실행 조건 입력 파일의 필수 키가 없다: {', '.join(missing)}")
    if doc["dataset"] not in types.DATASETS:
        raise BatchError("dataset이 계약의 자료 묶음 이름이 아니다")
    cases = doc["planned_cases"]
    if not isinstance(cases, list) or not cases or any(
            not isinstance(c, dict) or set(c) != set(CASE_KEYS) or c.get("partner") == "ALL" for c in cases):
        raise BatchError("planned_cases는 case_id·hs6·partner(ALL 아님)·month 네 키의 객체 목록이다")
    if len({c["case_id"] for c in cases}) != len(cases):
        raise BatchError("planned_cases에 같은 case_id가 두 번 있다")
    modes = doc["planned_modes"]
    if not isinstance(modes, list) or not modes or any(m not in types.MODES for m in modes) \
            or len(set(modes)) != len(modes):
        raise BatchError("planned_modes는 서로 다른 모드의 목록이다")
    thresholds = doc["policy_detection_thresholds"]
    if not isinstance(thresholds, list) or not thresholds or any(
            isinstance(t, bool) or not isinstance(t, (int, Decimal)) for t in thresholds):
        raise BatchError("policy_detection_thresholds는 int·Decimal 수의 목록이다(float·문자열 아님)")
    if "concurrency" in doc and (not isinstance(doc["concurrency"], int) or isinstance(doc["concurrency"], bool)):
        raise BatchError("concurrency는 정수다")
    if doc["dataset"] in types.SEALED_DATASETS:
        present = [k for k in SEALED_FORBIDDEN if k in doc]
        if present:
            raise BatchError(f"봉인 묶음에는 봉인 출력이 있어야 하는 값을 넣지 않는다: {', '.join(present)}")
    strings = _strings(doc)
    if any(PATH_SHAPE.search(s) for s in strings):
        raise BatchError("실행 조건 입력 파일에 로컬 절대경로 모양의 값이 있다(N13)")
    if any(SECRET_SHAPE.search(s) for s in strings):
        raise BatchError("실행 조건 입력 파일에 키 모양의 값이 있다(절대 규칙 1)")


def conditions_path(run_dir: Path) -> Path:
    """<run_dir>/run_conditions-{그 폴더 실행명의 시각}.json(한 실행의 출력은 같은 시각, N6)."""
    name = run_dir.name
    if not trace_log.RUN_ID_RE.match(name):
        raise BatchError("실행 폴더 이름이 실행명 형식이 아니다")
    return run_dir / f"{CONDITIONS_DOMAIN}-{name.rsplit('-', 1)[1]}.json"


def write_run_conditions(run_dir: Path, doc: dict) -> Path:
    """실행 조건 입력 파일을 이미 있으면 실패하는 방식(O_EXCL)으로 쓴다. 폴더는 부르는 호스트 쪽 프로그램이 확보한
    실행 폴더다. 봉인 묶음 여부와 폴더 위치(outputs/sealed/ 아래인지)가 맞지 않으면 쓰지 않는다."""
    check_run_conditions(doc)
    sealed_place = run_dir.parent.name == "sealed"
    if (doc["dataset"] in types.SEALED_DATASETS) != sealed_place:
        raise BatchError("봉인 묶음은 outputs/sealed/ 아래, 봉인 묶음이 아니면 outputs/ 아래 실행 폴더에만 쓴다")
    path = conditions_path(run_dir)
    payload = (trace_log.dumps(doc) + "\n").encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "wb") as handle:
        handle.write(payload)
    return path


# ----------------------------------------------------------------------------- 진입 함수

def run(inp: object) -> object:
    """실행 순서를 만든다(머리 설명 1).

    입력: {"case_ids": [case_id, ...], "modes": [모드, ...], "order_seed": 문자열}.
    출력: {"order": [{"case_id", "mode"}, ...], "concurrency": 1}.
    """
    if not isinstance(inp, dict) or set(inp) != {"case_ids", "modes", "order_seed"}:
        raise BatchError("입력은 case_ids·modes·order_seed 세 키의 객체다")
    order = plan_order(inp["case_ids"], inp["modes"], inp["order_seed"])
    return {"order": [{"case_id": c, "mode": m} for c, m in order], "concurrency": CONCURRENCY}
