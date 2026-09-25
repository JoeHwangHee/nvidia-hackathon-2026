"""단위 E1 묶음 실행.

단위 ID: E1
도메인명: evaluation_batch_run
소유: M
입력: 사례 목록 × 모드
출력: 교차 배치 실행, 실행 결과 기록의 실행 쪽 키(`evaluation_batch_run-{시각}.jsonl`)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.runlog, tradesentry.policy, tradesentry.workflow

S0 제안: 사례 실행은 묶음 폴더 안이 아니라 형제 폴더 outputs/run_case-{시각}/에 두고, 묶음 기록의 줄마다 적는 run_id로 잇는다.

호스트 전용 샌드박스 밖 실행기 E2(tradesentry.evaluation.sealed_runner)를 import하지 않는다(경계 시험이 본다). E2는 이
모듈을 import해 같은 묶음 고리를 쓴다(MT7 두 번째 PR에서 경계를 한쪽으로 열었다. 이 모듈은 사례를 호스트에서 돌리지 않는다).

정본: docs/plan/UNITS.md E1 행, 자료 계약 docs/rules/DATA_CONTRACT_V1.md §8·§10.3 N5·N6·N8, 룰북 docs/eval/RULEBOOK.md B2·B5.

세 가지를 한다.
1. 실행 순서(run): (사례, 모드) 목록을 고정 seed로 섞는다(룰북 B5 교차 배치). 순수 함수라 골든 시험의 대상이다.
   섞는 법(바이트 수준으로 고정. 파이썬 판과 관계없이 같은 순서다. E2도 이 함수를 쓴다):
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
   - 모든 모드에 같은 자료·버전·사례 실행 함수를 쓴다.
   - 인프라 실패 재실행(룰북 B5, 조립 AS3 두 번째 PR): 첫 실행이 모두 끝난 뒤, 첫 실행 줄 가운데 단위 L3
     infra_rerun_eligible(FAILED이고 원인이 PROVIDER_HTTP_5XX·PROVIDER_CONNECTION·HTTP 429인 PROVIDER_HTTP_4XX뿐)인 줄을 모두, 첫 실행 순서대로 같은
     (사례, 모드)·같은 설정으로 한 번씩 다시 돌린다. 재실행마다 새 실행명을 확보하고 같은 묶음 기록에 줄을 더한다(원래 줄은
     그대로 둔다. 채점기의 재실행 모양 "FAILED 한 줄 뒤 재실행 한 줄"). 재실행 줄은 다시 재실행하지 않는다. 다른 실패
     (TIMEOUT·INVALID·BUDGET_EXCEEDED·CODE_ERROR 등)는 재실행하지 않는다. 대상 수와 재실행 수는 BatchResult에 남는다.
   - 속도 조절(Pacing, 조립 AS3 세 번째 PR): 모델 제공자의 요청 한도(HTTP 429)를 넘지 않게 모델을 쓰는 실행(checklist 밖
     모드) 사이를 띄운다. 모델을 쓰는 실행을 시작하기 전에, 직전 모델 실행의 시작 시각에서 max(최소 간격, 직전 실행 토큰
     수 ÷ 분당 토큰 예산 × 60초)가 지날 때까지 쉰다. 직전 모델 실행이 HTTP 429로 끝났으면 그 실행이 끝난 시각에서
     429 뒤 쉬는 시간도 지나야 한다. checklist는 모델을 부르지 않으므로 쉬지 않고 기준에서도 빠진다. 값은 모델 설정
     (configs/model/model.json의 pacing)에서 부르는 쪽이 읽어 넘기고, 모든 모드에 같다. 429로 끝난 실행은 인프라 실패
     재실행 대상이다(2026-09-25 15:52 사용자 결정, 사용자 결정 5 변경). 재실행도 모델 실행이라 같은 속도 조절을 받는다.
     429 줄을 가르는 곳은 단위 L3 rate_limited_entry 하나다. 쉰 시간의 합과 429 뒤 쉰 횟수는 BatchResult에 남는다.
   - 봉인 묶음(holdout40·real_sealed)은 기본값(sealed=False)으로는 받지 않는다. 봉인 묶음은 샌드박스 밖 실행기 E2가
     sealed=True로 이 함수를 불러 돌린다(로드맵 MT7 두 번째 PR): 그때는 자료 묶음이 봉인 묶음이고 부모가 outputs/sealed/
     아래여야 하며, 실행 이름(run_name)과 묶음 기록 도메인명(domain)은 E2의 값(sealed_evaluate·evaluation_sealed_runner)이다
     (자료 계약 §8.2·§10.3 N5·N10). 그 밖의 절차(순서·실행명 확보·줄 쓰기·재실행·속도 조절)는 같다.
3. 실행 조건 입력 파일(build_run_conditions·write_run_conditions): 채점기가 모르는 실행 조건을 채점기에 넘기는 파일
   run_conditions-{시각}.json을 내려받기를 끝낸 호스트 쪽 프로그램이 확보한 실행 폴더에 배타 생성한다(자료 계약 §8.2).
   형식은 MVP 전 임시 형식이다(결정 D6, 채점기 DT8 1회차 보고 §5와 같은 키. F1 전에 확정한다). 봉인 묶음이면 봉인
   출력이 있어야 하는 값(nat_profile_summary, korean_sample_review)을 넣지 않는다. 값에 로컬 절대경로 모양이나 키
   모양이 있으면 쓰지 않는다(N13, 절대 규칙 1).
   - 운영자 실행 조건(check_operator_conditions·merge_operator_conditions, 조립 AS3 `--conditions-extra`): 하네스가
     채우지 못하고 운영자만 아는 값(라이브 정책 조회 본문 sha256, 대조한 시험표 실행 폴더 이름, 스킬 호출 성공률, 채점기·
     산문 패턴 목록 커밋, 사전 점검 결과, A등급 조건 등)을 운영자가 JSON 객체로 준다. 키는 OPERATOR_CONDITION_KEYS(하네스가
     채우는 키 HARNESS_CONDITION_KEYS를 뺀 CONDITION_KEYS)만 받고, sandbox·prescoring_checks는 하네스가 채우지 않는 하위
     키(OPERATOR_SUBKEYS)만 받아 하네스 값과 합친다. 하네스가 채우는 키나 하위 키를 주면 "두 번 줬다" 오류로 멈춘다. 채점기가
     이미 읽는 키를 채우는 배관이며 채점 규칙은 바꾸지 않는다(결정 기록 model-decision-conditions-extra).

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
# 하네스(evaluate 배선과 이 모듈)가 채우는 키. 운영자 실행 조건 파일(--conditions-extra)이 주면 "두 번 줬다"다.
HARNESS_CONDITION_KEYS = ("dataset", "planned_cases", "planned_modes", "policy_detection_thresholds", "snapshot",
                          "order_seed", "concurrency", "limits", "run_period", "nat_profile_summary", "reproduce_evaluate")
# 운영자 실행 조건 파일이 줄 수 있는 최상위 키(채점기 요약 0절·4절이 읽는 키). sandbox·prescoring_checks는 하위 키를
# OPERATOR_SUBKEYS로 좁혀 하네스 값과 합친다.
OPERATOR_CONDITION_KEYS = tuple(k for k in CONDITION_KEYS if k not in HARNESS_CONDITION_KEYS)
OPERATOR_SUBKEYS = {"sandbox": ("live_policy_sha256", "violation_tests_run"),  # 하네스: name·policy_yaml_sha256
                    "prescoring_checks": ("version_keys", "mode_case_sets", "concurrency_record")}  # 하네스: final_status·seed_concurrency

# 자료 묶음 → 예정 모드(평가 스킬 ② 실행 행렬, 룰북 B2. 실자료 묶음에는 참고용 agent를 넣지 않는다). controlled_fixture_v0은
# 네 모드 모두 가능하다. 사용자 결정 12(2026-09-25 08:47): evaluate가 --mode 없이 돌 때 이 표의 모드 전부를 한 묶음으로 돈다
# (배선은 조립 AS3). 모드 하나만 준 묶음은 스모크용이고 점수표로 합치지 않는다. E2도 같은 표를 쓴다(따로 옮겨 적는다).
PLANNED_MODES = {"controlled_fixture_v0": tuple(types.MODES), "dev20": ("checklist", "agent", "full"),
                 "holdout40": ("checklist", "agent", "full"), "real_dev": ("freeform", "full"),
                 "real_sealed": ("freeform", "full")}

# 로컬 절대경로 모양(N13)과 키 모양(절대 규칙 1). 채점기 코드는 import하지 않고, 채점기가 거부하는 모양보다 넓게 잡는다:
# 값의 처음이나 영숫자·"."·"_"·"-"가 아닌 글자 뒤의 "/"(그래서 "//x", "file:///x", "`/x"도 잡는다. "USD/kg"처럼 글자 뒤의
# "/"는 잡지 않는다), 역슬래시 두 개(UNC), 드라이브 문자, 같은 자리의 물결표.
_PATH_START = r"(?:^|(?<=[^A-Za-z0-9._-]))"
PATH_SHAPE = re.compile(_PATH_START + r"/(?=\S)|\\\\|(?<![A-Za-z0-9])[A-Za-z]:[\\/]|" + _PATH_START + r"~")
SECRET_SHAPE = re.compile("nv" + "api-|service" + r"Key\s*=", re.I)  # 패턴 글자를 나눠 적는다(이 파일이 검사에 걸리지 않게)


def sealed_place(run_dir: Path) -> bool:
    """실행 폴더가 봉인 자리(outputs/sealed/ 아래)인가(자료 계약 §10.3 N10). 적힌 경로와 풀린 경로(심볼릭 링크)를 둘 다
    보고, outputs 폴더까지의 조상 이름에 sealed(대소문자 무시)가 있으면 봉인이다. 풀 수 없으면 봉인으로 본다.
    E3·E4도 같은 규칙을 쓴다(허용 import 때문에 따로 옮겨 적었다)."""
    try:
        paths = (run_dir.absolute(), run_dir.resolve())
    except (OSError, RuntimeError):
        return True
    for path in paths:
        for ancestor in path.parents:
            name = ancestor.name.lower()
            if name == "sealed":
                return True
            if name == "outputs":
                break
    return False


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
    domain: str = DOMAIN  # 묶음 기록 도메인명(E1은 evaluation_batch_run, E2는 evaluation_sealed_runner)
    rerun_targets: int = 0  # 첫 실행 줄 가운데 인프라 실패 재실행 대상 수(룰북 B5)
    reruns: int = 0  # 실제로 다시 돌린 수(사례 실행명을 확보하지 못해 멈추면 대상보다 적다)
    paced_ms: int = 0  # 속도 조절로 쉰 시간의 합(밀리초)
    rate_limit_waits: int = 0  # HTTP 429 뒤 더 쉰 횟수

    @property
    def batch_file(self) -> Path:
        return self.run_dir / f"{self.domain}-{self.stamp}.jsonl"


@dataclass(frozen=True)
class Pacing:
    """모델을 쓰는 사례 실행 사이의 속도 조절(머리 설명 2). 0이면 그 규칙을 쓰지 않는다."""
    min_gap_ms: int = 0  # 모델 실행 시작 사이 최소 간격
    tokens_per_minute: int = 0  # 분당 토큰 예산(직전 실행 토큰 수에 비례해 쉰다)
    after_rate_limit_ms: int = 0  # 직전 실행이 HTTP 429로 끝났을 때 그 끝에서 더 쉬는 시간


PACING_KEYS = ("min_gap_ms", "tokens_per_minute", "after_rate_limit_ms")


def pacing_from_config(raw: object) -> Pacing:
    """모델 설정의 pacing 객체({min_gap_ms, tokens_per_minute, after_rate_limit_ms}, 0 이상의 정수)를 읽는다."""
    if not isinstance(raw, dict) or set(raw) != set(PACING_KEYS) or not all(
            isinstance(raw[k], int) and not isinstance(raw[k], bool) and raw[k] >= 0 for k in PACING_KEYS):
        raise BatchError(f"pacing은 {'·'.join(PACING_KEYS)} 세 키의 0 이상 정수 객체다")
    return Pacing(**{k: raw[k] for k in PACING_KEYS})


def rate_limited(line: dict) -> bool:
    """실행이 모델 제공자의 요청 한도(HTTP 429)로 끝났는가(원인 PROVIDER_HTTP_4XX, detail "HTTP 429…", 단위 L3가 가른다)."""
    return any(cause_codes.rate_limited_entry(e) for e in line.get("errors") or [])


def pacing_target(pacing: Pacing, start: datetime, end: datetime, line: dict) -> datetime:
    """직전 모델 실행(시작·끝 시각, 줄) 뒤 다음 모델 실행을 시작해도 되는 가장 이른 시각."""
    from datetime import timedelta

    tokens = sum(v for v in (line.get("tokens_in"), line.get("tokens_out")) if isinstance(v, int))
    gap = pacing.min_gap_ms
    if pacing.tokens_per_minute:
        gap = max(gap, -(-tokens * 60000 // pacing.tokens_per_minute))
    target = start + timedelta(milliseconds=gap)
    if rate_limited(line):
        target = max(target, end + timedelta(milliseconds=pacing.after_rate_limit_ms))
    return target


CaseRunner = Callable[[CaseCall], dict]


def check_spec(spec: BatchSpec, sealed: bool = False) -> None:
    """묶음 입력 검사(폴더를 만들기 전에). sealed가 참이면(E2) 봉인 묶음만, 거짓이면 봉인 묶음이 아닌 것만 받는다."""
    if sealed and spec.dataset not in types.SEALED_DATASETS:
        raise BatchError("봉인 실행(sealed)은 봉인 묶음(holdout40·real_sealed)만 돌린다")
    if not sealed and spec.dataset not in UNSEALED_DATASETS:
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


def _check_reserved(reserved: object, parent: Path, run_name: str = BATCH_RUN_NAME) -> tuple[str, str, Path]:
    """이미 확보한 묶음 실행 폴더(실행명, 시각, 폴더)를 받는다. 실행명이 {run_name}-{시각}이고, 폴더가 parent 바로 아래의 그
    이름이며, 비어 있어야 한다(사용자 결정 10: 호스트가 확보한 실행명을 --run-name으로 받은 경우. E2는 첫 줄 출력을 위해
    먼저 확보한 폴더를 넘긴다)."""
    if not isinstance(reserved, tuple) or len(reserved) != 3:
        raise BatchError("확보한 묶음 실행 폴더는 (실행명, 시각, 폴더) 셋이다")
    run_id, stamp, folder = reserved
    if not isinstance(run_id, str) or not isinstance(stamp, str) or not isinstance(folder, Path) \
            or trace_log.RUN_ID_RE.fullmatch(run_id) is None or run_id != f"{run_name}-{stamp}" \
            or folder != parent / run_id:
        raise BatchError(f"확보한 묶음 실행 폴더가 {run_name}-{{시각}}/ 모양이 아니다")
    if folder.is_symlink() or not folder.is_dir() or any(folder.iterdir()):
        raise BatchError("확보한 묶음 실행 폴더가 빈 폴더가 아니다")
    return run_id, stamp, folder


def execute_batch(spec: BatchSpec, runner: CaseRunner, *, parent: Path, other_parent: Path,
                  clock: Callable[[], datetime] | None = None,
                  sleep: Callable[[float], None] | None = None,
                  reserved: tuple[str, str, Path] | None = None, pacing: Pacing | None = None,
                  run_name: str = BATCH_RUN_NAME, domain: str = DOMAIN, sealed: bool = False) -> BatchResult:
    """묶음 하나를 돌린다(머리 설명 2). parent는 outputs/, other_parent는 outputs/sealed/다(N8). 봉인 실행(sealed=True,
    E2)이면 parent가 outputs/sealed/, other_parent가 outputs/이고 run_name·domain은 E2의 값이다.

    reserved를 주면 묶음 실행 폴더를 다시 확보하지 않고 그 폴더(이미 확보한 빈 폴더, 사용자 결정 10의 --run-name)에 쓴다.
    사례 실행명을 확보하지 못하면(RunNameError) 거기서 멈춘다. 쓴 줄은 남고, 남은 계획 조합은 미실행으로 분모에 남는다.
    pacing을 주면 모델을 쓰는 실행 사이를 띄운다(머리 설명 2의 속도 조절).
    """
    import time

    check_spec(spec, sealed)
    if not sealed and sealed_place(parent / run_name):
        raise BatchError("묶음 실행 E1은 outputs/sealed/ 아래에 쓰지 않는다(봉인 묶음은 E2)")
    if sealed and not sealed_place(parent / run_name):
        raise BatchError("봉인 실행(sealed)은 outputs/sealed/ 아래에만 쓴다(자료 계약 §10.3 N10)")
    if not run_record.RUN_NAME_RE.match(run_name) or not run_record.RUN_NAME_RE.match(domain):
        raise BatchError("묶음 실행 이름과 묶음 기록 도메인명은 이름 규칙(N1)에 맞는 이름이다")
    if reserved is not None:
        reserved = _check_reserved(reserved, parent, run_name)
    clock = clock or trace_log.now_kst
    reserve_kw: dict = {"clock": clock}
    if sleep is not None:
        reserve_kw["sleep"] = sleep
    order = plan_order([c["case_id"] for c in spec.cases], list(spec.modes), spec.order_seed)
    cases = {c["case_id"]: dict(c) for c in spec.cases}
    versions = {k: spec.versions[k] for k in VERSION_KEYS}
    if reserved is None:
        batch_id, stamp, batch_dir = run_record.reserve_run_dir(parent, other_parent, run_name, **reserve_kw)
    else:
        batch_id, stamp, batch_dir = reserved
    started = clock()
    lines: list[dict] = []
    targets: list[tuple[str, str]] = []
    reruns = 0
    wait = sleep or time.sleep
    paced = {"ms": 0, "rate_limit_waits": 0, "last": None}  # last: 직전 모델 실행 (시작, 끝, 줄)
    with open(batch_dir / f"{domain}-{stamp}.jsonl", "x", encoding="utf-8", newline="\n") as out:

        def pace(mode: str) -> None:
            if pacing is None or mode == "checklist" or paced["last"] is None:
                return
            start, end, previous = paced["last"]
            target = pacing_target(pacing, start, end, previous)
            if rate_limited(previous) and pacing.after_rate_limit_ms:
                paced["rate_limit_waits"] += 1
            before = clock()
            while (remaining := (target - clock()).total_seconds()) > 0:
                wait(remaining)
            paced["ms"] += _ms(before, clock())

        def run_one(case_id: str, mode: str) -> dict:
            pace(mode)
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
            if mode != "checklist":
                paced["last"] = (begin, clock(), line)
            return line

        for case_id, mode in order:
            line = run_one(case_id, mode)
            if cause_codes.infra_rerun_eligible(line["execution_status"], line["errors"]):
                targets.append((case_id, mode))
        for case_id, mode in targets:  # 첫 실행이 모두 끝난 뒤, 첫 실행 순서대로 한 번씩(룰북 B5)
            run_one(case_id, mode)
            reruns += 1
    return BatchResult(run_id=batch_id, stamp=stamp, run_dir=batch_dir, lines=lines, started=started, ended=clock(),
                       domain=domain, rerun_targets=len(targets), reruns=reruns, paced_ms=paced["ms"],
                       rate_limit_waits=paced["rate_limit_waits"])


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


def check_operator_conditions(doc: object, dataset: str) -> None:
    """운영자 실행 조건 파일(--conditions-extra)의 내용 검사. 객체이고, 최상위 키는 OPERATOR_CONDITION_KEYS만, sandbox·
    prescoring_checks는 OPERATOR_SUBKEYS의 하위 키만 든 객체다. 하네스가 채우는 키·하위 키는 "두 번 줬다"(약속 밖 키와
    구분해 알린다). 봉인 묶음이면 SEALED_FORBIDDEN을 받지 않는다. 값의 로컬 절대경로 모양·키 모양은 합친 결과에도 다시
    보지만(check_run_conditions) 묶음을 돌리기 전에 여기서 먼저 막는다."""
    if not isinstance(doc, dict):
        raise BatchError("운영자 실행 조건 파일은 JSON 객체다")
    harness = sorted(k for k in doc if k in HARNESS_CONDITION_KEYS)
    if harness:
        raise BatchError(f"실행 조건 {', '.join(harness)}를 두 번 줬다(하네스가 채우는 키다)")
    unknown = sorted(set(doc) - set(OPERATOR_CONDITION_KEYS))
    if unknown:
        raise BatchError(f"운영자 실행 조건 파일의 약속 밖 키: {', '.join(unknown)}")
    for key, allowed in OPERATOR_SUBKEYS.items():
        if key not in doc:
            continue
        sub = doc[key]
        if not isinstance(sub, dict):
            raise BatchError(f"운영자 실행 조건 {key}는 객체다")
        bad = sorted(set(sub) - set(allowed))
        if bad:
            raise BatchError(f"실행 조건 {key}의 하위 키 {', '.join(bad)}는 하네스가 채우거나 약속 밖이다"
                             f"(받는 하위 키: {', '.join(allowed)})")
    if dataset in types.SEALED_DATASETS:
        present = [k for k in SEALED_FORBIDDEN if k in doc]
        if present:
            raise BatchError(f"봉인 묶음에는 봉인 출력이 있어야 하는 값을 넣지 않는다: {', '.join(present)}")
    strings = _strings(doc)
    if any(PATH_SHAPE.search(s) for s in strings):
        raise BatchError("운영자 실행 조건 파일에 로컬 절대경로 모양의 값이 있다(N13)")
    if any(SECRET_SHAPE.search(s) for s in strings):
        raise BatchError("운영자 실행 조건 파일에 키 모양의 값이 있다(절대 규칙 1)")


def merge_operator_conditions(extra: dict, operator: dict) -> list[str]:
    """운영자 실행 조건을 하네스의 extra(build_run_conditions에 넘길 객체)에 합친다. sandbox·prescoring_checks는 하네스
    객체가 있으면 하위 키를 더하고(같은 하위 키가 있으면 "두 번 줬다"), 없으면 운영자 객체 그대로 둔다. 다른 키는 extra에
    이미 있으면 "두 번 줬다". 합친 키 이름 목록(하위 키는 점으로 이어 씀. 값은 없다)을 돌려준다(표준 오류 알림용)."""
    merged: list[str] = []
    for key in sorted(operator):
        value = operator[key]
        if key in OPERATOR_SUBKEYS:
            target = extra.setdefault(key, {})
            if not isinstance(target, dict):
                raise BatchError(f"실행 조건 {key}의 하네스 값이 객체가 아니다")
            for sub in sorted(value):
                if sub in target:
                    raise BatchError(f"실행 조건 {key}.{sub}를 두 번 줬다")
                target[sub] = value[sub]
                merged.append(f"{key}.{sub}")
            continue
        if key in extra:
            raise BatchError(f"실행 조건 {key}를 두 번 줬다")
        extra[key] = value
        merged.append(key)
    return merged


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
    if (doc["dataset"] in types.SEALED_DATASETS) != sealed_place(run_dir):
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
