"""단위 E2 샌드박스 밖 실행기.

단위 ID: E2
도메인명: evaluation_sealed_runner
소유: M
입력: 봉인 해시 대조
출력: 사례 식별자 한 건씩 `run-case`
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.runlog, tradesentry.evaluation.batch_run, tradesentry.evaluation.sandbox_exec

정본: docs/plan/UNITS.md E2 행, 로드맵 docs/plan/ROADMAP.md MT7(샌드박스 밖 실행기 요건), 룰북 docs/eval/RULEBOOK.md B5·B6·부록
40번, 평가 스킬 ② skills/tradesentry-eval/SKILL.md "실행"·"봉인 자료 취급"(공식 채점 순서 5·6, 해시 대조 방법), 자료 계약
docs/rules/DATA_CONTRACT_V1.md §8.2·§10.3(N5·N8·N10·N13)·§12, 결정 기록 docs/tracking/decisions/의
model-decision-mt7-sealed-runner(이 단위의 이름·명령·순서 seed).

봉인 묶음(holdout40·real_sealed)을 룰북 RB-1 동결 뒤 공식 채점 대상 실행 전용 샌드박스에서 돌리는 호스트 쪽 프로그램이다.
명령: python -m <이 모듈> --dataset {holdout40|real_sealed} --sandbox <전용 샌드박스 이름> --snapshot <스냅샷 ID>
--policy <정책 버전> [--conditions-extra <JSON 상대 경로>]. 저장소 루트에서 부른다(outputs/ 기준). CLI `tradesentry`의 하위
명령이 아니다(계획 경로·명령 표를 바꾸지 않는다. 채점기처럼 python -m 형식이다).

이 실행기는 키 변수를 뺀 환경에서 돌고 .env를 읽지 않는다. 그래서 load_env가 있는 tradesentry.ingest를 직접이든 간접이든
import하지 않는다(경계 시험이 본다). 사례는 샌드박스 안 run-case로만 돌린다. 하위 프로세스는 보조 파일
tradesentry.evaluation.sandbox_exec이 openshell로 시작하는 목록 리터럴로만 부르고, 사례를 호스트에서 돌릴 수 있는
tradesentry.workflow·tools·policy·metrics·cli·ingest와 채점기 eval.scorer는 import하지 않는다(경계 시험이 본다). 묶음 고리
(순서·실행명 확보·줄 쓰기·인프라 실패 재실행·속도 조절·실행 조건 입력 파일)는 단위 E1(tradesentry.evaluation.batch_run)을
그대로 쓴다(E1은 사례를 돌리지 않는 순수 고리다. MT7 두 번째 PR에서 경계를 이쪽으로만 열었다).

순서(run_sealed)
1. 봉인 해시 대조(자료 계약 §12.2, 스킬 "해시 대조 방법"): 봉인 폴더(환경변수 TRADESENTRY_SEALED_DIR, 비어 있으면 홈 폴더의
   .tradesentry/sealed/)의 파일 전체를 해시 목록 eval/sealed_manifest.json의 files 전체(두 묶음)와 대조한다. 목록 파일이
   모두 있고 sha256이 같고 목록 밖 파일(OS 메타데이터 파일·링크 포함)이 없어야 일치다. 불일치면 종료 코드 2로 끝나고 outputs/에
   아무것도 쓰지 않는다. 표준 출력에는 파일 수·일치 수·불일치 수·목록 밖 파일 수만 적고, 이름은 목록 안 파일만 적는다.
   진입 함수 run은 이 대조를 순수 함수(compare_manifest)로 낸다(골든 시험).
2. 봉인 사례 읽기(sealed_case_list): real_sealed는 목록에서 dataset이 real_sealed이고 file_name이 real_sealed/sample-로
   시작하는 항목 하나(둘 이상이면 오류)를 읽어 cases(case_id 문자열 목록)·snapshot_id·policy_version을 얻고 인자와 대조한다.
   case_id `{hs6}-{partner}-{month}`를 풀어 계획 사례 네 키를 만든다(판정 정책 식별자 형식, 자료 계약 §3). holdout40은
   file_name이 holdout40/input/cases.json인 항목을 읽어 cases[]의 네 키를 얻는다(정답표·answers/·gen/은 읽지 않는다). 표본 추출
   seed 파일은 읽지 않는다. 파일마다 읽기 직전에 해시를 다시 대조한다. 사례 식별자는 어디에도 출력하지 않는다(건수만).
3. 준비: 운영자 실행 조건(--conditions-extra, E1 check_operator_conditions. 봉인 묶음이면 SEALED_FORBIDDEN 거부), 정책 탐지
   임계값(단위 K4 load_policy의 thresholds.unit_value·share, int·Decimal), 모델 설정 configs/model/model.json의 limits·pacing
   (E1 limits_from_run_limits·pacing_from_config), 버전 키 5개(정책·룰북 RB-1·스냅샷·비교 대상 집합 g0·호스트 code_version),
   E1 BatchSpec(모드는 PLANNED_MODES[자료 묶음] 전부, 순서 seed SEALED_ORDER_SEED), 샌드박스 사전 점검(sandbox_exec.
   sandbox_preflight: 이미지 기록 커밋 = 호스트 code_version, dirty 거짓). 여기까지 실패하면 종료 코드 1이고 outputs/에 쓰지
   않는다.
4. 실행: 실행 폴더 outputs/sealed/sealed_evaluate-{시각}/을 N8대로 확보하고 outputs/부터의 상대경로를 표준 출력 첫 줄에 적는다.
   E1 execute_batch(sealed=True)가 (사례 × 모드)를 순서 seed로 섞어 동시성 1로 돌리고, 사례마다 outputs/sealed/run_case-{시각}/을
   확보해 sandbox_exec.SandboxCaseRunner가 전용 샌드박스 안 run-case에 --run-name으로 넘기고 내려받는다. 묶음 기록은
   evaluation_sealed_runner-{시각}.jsonl(줄 형식은 E1과 같다). 인프라 실패 재실행(룰북 B5)과 속도 조절은 E1 그대로다.
5. 실행 조건 입력 파일 run_conditions-{시각}.json(자료 계약 §8.2)을 같은 폴더에 배타 생성한다: E1 build_run_conditions에
   sandbox.name·policy_yaml_sha256, reproduce_evaluate(위 명령 그대로), prescoring_checks.final_status·seed_concurrency를 채우고
   운영자 조건을 합친다(E1 merge_operator_conditions). NAT 사후 평가(단위 E4)는 봉인 자리를 읽지 않으므로 부르지 않고
   nat_profile_summary를 넣지 않는다(자료 계약 §8.2).
6. 표준 출력 끝: 상태별 건수(COMPLETED·FAILED·TIMEOUT·INVALID·BUDGET_EXCEEDED), 재실행 대상·재실행 수, 모드별 사례 집합 일치
   여부(참·거짓)와 순서 seed·동시성, 종료 코드. 사례 식별자·값·경로(폴더 이름 제외)는 내지 않는다(N10·N13). 사례 실행이
   실패해도 묶음 기록을 끝까지 썼으면 종료 코드 0이다(E1과 같다. 실패는 줄로 분모에 남는다).

세션이 끊겨 잇는 기능(--resume)은 이 PR에 없다(결정 기록 [미확인]). 리허설(로드맵 MT7): run_sealed에 봉인 묶음이 아닌 자료
묶음(dev20)과 사례 목록·outputs/ 부모·해시 목록·봉인 폴더 자리를 인자로 주면 같은 흐름을 outputs/ 아래(봉인 아님)에서 돌린다.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Callable

from tradesentry.contract import policy_load, types
from tradesentry.evaluation import batch_run, sandbox_exec
from tradesentry.runlog import run_record
from tradesentry.runlog import trace as trace_log

DOMAIN = "evaluation_sealed_runner"
RUN_NAME = "sealed_evaluate"  # 봉인 묶음 실행의 실행 이름(N5). 폴더 outputs/sealed/sealed_evaluate-{시각}/
SEALED_ORDER_SEED = "rb1-order-v1"  # RB-1과 함께 동결한 순서 seed(룰북 B5, 조정값)
SEALED_GROUPING_VERSION = "g0"  # 봉인 묶음의 비교 대상 집합(실자료는 g0 대체, 합성은 자료 안 g0 규칙의 peer_group)
SEALED_ENV = "TRADESENTRY_SEALED_DIR"
SEALED_DEFAULT = sandbox_exec.SEALED_DIR_DEFAULT  # 홈 폴더 아래 기본값(자료 계약 §10)
MANIFEST_FILE = Path("eval") / "sealed_manifest.json"
MODEL_CONFIG_FILE = Path("configs") / "model" / "model.json"
HOLDOUT40_CASES = "holdout40/input/cases.json"
REAL_SEALED_SAMPLE_PREFIX = "real_sealed/sample-"
OUTPUTS = Path("outputs")
SEALED_NAME = "sealed"
MAX_INPUT_BYTES = 16 << 20
EXIT_OK, EXIT_FAILED, EXIT_HASH_MISMATCH = 0, 1, 2  # 2는 인자 오류와 해시 불일치(둘 다 outputs/에 쓰기 전)
CASE_ID_RE = re.compile(r"([0-9]{6})-([A-Z0-9]{2})-([0-9]{6})")  # {hs6}-{partner}-{month}(판정 정책 식별자 형식)
SHA256_RE = re.compile(r"[0-9a-f]{64}")
BAD_PATH_START_RE = re.compile(r"^(?:[\\/]|~|[A-Za-z]:[\\/])")  # 단위 F1 --conditions-extra 검사와 같다
REPO_ROOT = sandbox_exec.REPO_ROOT
PROGRAM = sandbox_exec.SEALED_RUNNER_COMMAND


class SealedRunnerError(ValueError):
    """입력이 규칙에 맞지 않는다. 문장에는 사례 식별자·값·경로를 넣지 않는다(N13)."""


# ----------------------------------------------------------------------------- 1. 봉인 해시 대조

def sealed_dir(environ: dict | None = None) -> Path:
    """봉인 폴더: TRADESENTRY_SEALED_DIR 값, 비어 있으면 홈 폴더의 .tradesentry/sealed/(자료 계약 §10). 열지 않고 경로만 만든다."""
    environ = os.environ if environ is None else environ
    value = environ.get(SEALED_ENV, "")
    if value:
        return Path(value)
    home = environ.get("HOME", "")
    if not home:
        raise SealedRunnerError("봉인 폴더 위치를 정할 수 없다(환경변수 없음)")
    return Path(home).joinpath(*SEALED_DEFAULT)


def load_manifest(path: Path) -> list[dict]:
    """해시 목록 eval/sealed_manifest.json의 files 항목(자료 계약 §12.2 형식 검사)."""
    if path.is_symlink() or not path.is_file():
        raise SealedRunnerError("봉인 해시 목록 파일이 없다")
    with open(path, "rb") as handle:
        data = handle.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES:
        raise SealedRunnerError("봉인 해시 목록이 크기 상한을 넘는다")
    try:
        doc = json.loads(data.decode("utf-8"))
    except (UnicodeError, ValueError, RecursionError):
        raise SealedRunnerError("봉인 해시 목록이 JSON이 아니다") from None
    files = doc.get("files") if isinstance(doc, dict) else None
    if not isinstance(files, list) or not files:
        raise SealedRunnerError("봉인 해시 목록에 files 목록이 없다")
    seen: set[str] = set()
    for entry in files:
        if not isinstance(entry, dict) or set(entry) != set(types.SEALED_MANIFEST_FILE_KEYS) \
                or not all(isinstance(entry[k], str) and entry[k] for k in types.SEALED_MANIFEST_FILE_KEYS):
            raise SealedRunnerError("봉인 해시 목록 항목의 모양이 틀렸다")
        name = entry["file_name"]
        if entry["dataset"] not in types.SEALED_DATASETS or SHA256_RE.fullmatch(entry["sha256"]) is None \
                or Path(name).is_absolute() or ".." in Path(name).parts or "\\" in name or name in seen:
            raise SealedRunnerError("봉인 해시 목록 항목의 값이 규칙에 맞지 않는다")
        seen.add(name)
    return files


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def list_sealed_files(root: Path) -> dict[str, str | None]:
    """봉인 폴더의 항목 전체(링크를 따라가지 않는다): 봉인 폴더 기준 상대경로 → sha256. 일반 파일이 아닌 항목(링크·특수
    파일)은 None이다(목록 밖 항목으로 센다). 폴더가 없으면 빈 사전이다."""
    if root.is_symlink() or not root.is_dir():
        return {}
    found: dict[str, str | None] = {}
    for folder, dirnames, filenames in os.walk(root, followlinks=False):
        for name in dirnames + filenames:
            path = Path(folder) / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                found[rel] = None
            elif path.is_file():
                found[rel] = _sha256_file(path)
            elif not path.is_dir():
                found[rel] = None
    return found


def compare_manifest(entries: list, actual: dict) -> dict:
    """해시 목록(files 항목)과 실제 항목(상대경로 → sha256 또는 None)을 대조한다(순수 함수, 진입 함수 run).
    출력: files(목록 파일 수), matched, mismatched(목록 안 파일 가운데 없거나 해시가 다른 file_name, 목록 순서), extra(목록
    밖 항목 수. 이름은 내지 않는다), ok."""
    listed = {e["file_name"] for e in entries}
    mismatched = [e["file_name"] for e in entries if actual.get(e["file_name"]) != e["sha256"]]
    extra = sum(1 for name in actual if name not in listed)
    return {"files": len(entries), "matched": len(entries) - len(mismatched), "mismatched": mismatched,
            "extra": extra, "ok": not mismatched and extra == 0}


def recheck(root: Path, manifest: Path) -> dict:
    """봉인 폴더 전체를 해시 목록 전체와 대조한다(스킬 "해시 대조 방법"). 봉인 폴더에 쓰지 않는다."""
    return compare_manifest(load_manifest(manifest), list_sealed_files(root))


def recheck_text(result: dict) -> str:
    """대조 결과 한 줄(파일 수·일치 수·불일치 수·목록 밖 파일 수. 이름은 목록 안 파일만)."""
    text = (f"봉인 해시 대조: 목록 파일 {result['files']}개, 일치 {result['matched']}개, 불일치 {len(result['mismatched'])}개, "
            f"목록 밖 항목 {result['extra']}개 → {'일치' if result['ok'] else '불일치'}")
    if result["mismatched"]:
        text += "(불일치한 목록 안 파일: " + ", ".join(result["mismatched"]) + ")"
    return text


# ----------------------------------------------------------------------------- 2. 봉인 사례 읽기

def read_sealed_json(root: Path, entries: list, name: str) -> object:
    """해시 목록에 한 번만 있는 봉인 파일 하나를 읽기 직전에 해시를 다시 대조한 뒤 JSON으로 읽는다(소수는 Decimal)."""
    matches = [e for e in entries if e["file_name"] == name]
    if len(matches) != 1:
        raise SealedRunnerError("봉인 파일이 해시 목록에 한 번만 있어야 한다")
    path = root / name
    if path.is_symlink() or not path.is_file():
        raise SealedRunnerError("봉인 파일이 없다")
    with open(path, "rb") as handle:
        data = handle.read(MAX_INPUT_BYTES + 1)
    if len(data) > MAX_INPUT_BYTES or hashlib.sha256(data).hexdigest() != matches[0]["sha256"]:
        raise SealedRunnerError("봉인 파일 해시가 해시 목록과 다르다")
    try:
        return json.loads(data.decode("utf-8"), parse_float=Decimal)
    except (UnicodeError, ValueError, RecursionError):
        raise SealedRunnerError("봉인 파일이 JSON이 아니다") from None


def case_from_id(case_id: object) -> dict:
    """case_id `{hs6}-{partner}-{month}`를 계획 사례 네 키로 푼다."""
    if not isinstance(case_id, str) or CASE_ID_RE.fullmatch(case_id) is None:
        raise SealedRunnerError("봉인 표본의 사례 식별자가 {hs6}-{partner}-{month} 형식이 아니다")
    hs6, partner, month = case_id.split("-")
    if types.MONTH_RE.fullmatch(month) is None or partner == types.ALL_PARTNER:
        raise SealedRunnerError("봉인 표본의 사례 식별자가 {hs6}-{partner}-{month} 형식이 아니다")
    return {"case_id": case_id, "hs6": hs6, "partner": partner, "month": month}


def _check_match(doc: dict, key: str, expected: str, what: str, err=None) -> None:
    """봉인 파일의 키가 있으면 인자와 대조하고, 없으면 대조를 생략했다고 표준 오류에 알린다(값은 적지 않는다)."""
    if key not in doc:
        print(f"알림: 봉인 {what} 파일에 {key}가 없어 인자와 대조하지 않았다", file=err or sys.stderr, flush=True)
        return
    if doc[key] != expected:
        raise SealedRunnerError(f"봉인 {what}의 {key}가 인자와 다르다")


def sealed_case_list(dataset: str, root: Path, entries: list, snapshot_id: str, policy_version: str,
                     err=None) -> list[dict]:
    """자료 묶음의 계획 사례(네 키)를 봉인 파일에서 읽는다(머리 설명 2). 정답표·표본 추출 seed 파일은 읽지 않는다."""
    if dataset == "real_sealed":
        names = [e["file_name"] for e in entries
                 if e["dataset"] == "real_sealed" and e["file_name"].startswith(REAL_SEALED_SAMPLE_PREFIX)]
        if len(names) != 1:
            raise SealedRunnerError("real_sealed 채점 표본 파일이 해시 목록에 하나여야 한다")
        doc = read_sealed_json(root, entries, names[0])
        if not isinstance(doc, dict) or not isinstance(doc.get("cases"), list) or not doc["cases"]:
            raise SealedRunnerError("real_sealed 채점 표본의 모양이 틀렸다(cases 목록)")
        _check_match(doc, "snapshot_id", snapshot_id, "표본", err)
        _check_match(doc, "policy_version", policy_version, "표본", err)
        cases = [case_from_id(item) for item in doc["cases"]]
    elif dataset == "holdout40":
        doc = read_sealed_json(root, entries, HOLDOUT40_CASES)
        if not isinstance(doc, dict) or not isinstance(doc.get("cases"), list) or not doc["cases"]:
            raise SealedRunnerError("holdout40 사례 목록의 모양이 틀렸다(cases 목록)")
        _check_match(doc, "dataset", dataset, "사례 목록", err)
        _check_match(doc, "snapshot_id", snapshot_id, "사례 목록", err)
        cases = []
        for item in doc["cases"]:
            if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item[k] for k in batch_run.CASE_KEYS):
                raise SealedRunnerError("holdout40 사례 목록 항목에 네 키가 없다")
            cases.append({k: item[k] for k in batch_run.CASE_KEYS})
    else:
        raise SealedRunnerError("봉인 묶음이 아니다")
    if len({c["case_id"] for c in cases}) != len(cases):
        raise SealedRunnerError("봉인 사례 목록에 같은 case_id가 두 번 있다")
    return cases


# ----------------------------------------------------------------------------- 3. 준비

def policy_thresholds(policy: object) -> list:
    """정책 객체(단위 K4)의 탐지 임계값 두 개(단가 %, 점유율 pp)를 수 목록으로(단위 I12 policy_thresholds와 같은 규칙. E2는
    workflow를 import할 수 없어 옮겨 적었다. 시험이 대조한다)."""
    thresholds = policy.get("thresholds") if isinstance(policy, dict) else None
    if not isinstance(thresholds, dict):
        raise SealedRunnerError("정책 객체에 thresholds가 없다")
    values = []
    for signal in types.SIGNALS:
        value = thresholds.get(signal)
        if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
            raise SealedRunnerError("정책 thresholds 값은 int나 Decimal이다")
        values.append(value)
    return values


def load_model_settings(path: Path) -> tuple[dict, batch_run.Pacing]:
    """모델 설정의 한도(요약 한도 칸으로 옮긴 것)와 속도 조절. 모델 설정 파일의 다른 값은 읽지 않는다."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise SealedRunnerError("모델 설정을 읽지 못했다") from None
    if not isinstance(raw, dict):
        raise SealedRunnerError("모델 설정이 객체가 아니다")
    return batch_run.limits_from_run_limits(raw.get("limits")), batch_run.pacing_from_config(raw.get("pacing"))


def relative_path_piece(value: str) -> bool:
    """--conditions-extra 값의 모양(단위 F1과 같다): 비어 있지 않고, 공백·제어 문자가 없고, 절대 경로·드라이브·'~'로 시작하지
    않는다."""
    return bool(value) and not any(ch.isspace() or unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp") for ch in value) \
        and BAD_PATH_START_RE.match(value) is None


def load_operator_conditions(relpath: str | None, dataset: str, base: Path) -> dict | None:
    """운영자 실행 조건 파일(JSON 객체)을 읽어 E1 check_operator_conditions로 검사한다. 없으면 None."""
    if relpath is None:
        return None
    if not relative_path_piece(relpath):
        raise SealedRunnerError("운영자 실행 조건 파일 경로는 상대 경로 한 조각이다")
    try:
        text = (base / relpath).read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        raise SealedRunnerError(f"운영자 실행 조건 파일을 읽지 못했다({type(exc).__name__})") from None
    try:
        doc = json.loads(text, parse_float=Decimal)
    except ValueError:
        raise SealedRunnerError("운영자 실행 조건 파일이 JSON이 아니다") from None
    batch_run.check_operator_conditions(doc, dataset)
    return doc


def reproduce_command(dataset: str, sandbox: str, snapshot_id: str, policy_version: str,
                      conditions_extra: str | None) -> str:
    """실행 조건 입력 파일 reproduce_evaluate(룰북 B7 재현 명령): 이 실행기의 명령을 옵션 그대로."""
    command = f"{PROGRAM} --dataset {dataset} --sandbox {sandbox} --snapshot {snapshot_id} --policy {policy_version}"
    return command + (f" --conditions-extra {conditions_extra}" if conditions_extra else "")


def final_status_text(spec: batch_run.BatchSpec, result: batch_run.BatchResult) -> str:
    """prescoring_checks.final_status(평가 스킬 ② 채점 전 확인 1): 줄 없는 조합 수와 재실행 대상·재실행 수."""
    planned = {(case["case_id"], mode) for case in spec.cases for mode in spec.modes}
    present = {(line["case_id"], line["mode"]) for line in result.lines}
    unrun = len(planned - present)
    return (f"{'참' if unrun == 0 else '거짓'}: 예정 실행 {len(planned)}건 가운데 줄 없는 조합 {unrun}건, 인프라 실패 "
            f"재실행(룰북 B5) 대상 {result.rerun_targets}건·재실행 {result.reruns}건")


def seed_concurrency_text(pacing: batch_run.Pacing, result: batch_run.BatchResult) -> str:
    """prescoring_checks.seed_concurrency(채점 전 확인 5): 순서 seed·동시성·속도 조절 값·쉰 시간."""
    return (f"참: 순서 seed {SEALED_ORDER_SEED}, 동시성 {batch_run.CONCURRENCY}, 속도 조절(모델 실행 사이 최소 "
            f"{pacing.min_gap_ms // 1000}초, 분당 토큰 {pacing.tokens_per_minute}, HTTP 429 뒤 "
            f"{pacing.after_rate_limit_ms // 1000}초), 쉰 시간 합 {result.paced_ms // 1000}초, 429 뒤 더 쉰 횟수 "
            f"{result.rate_limit_waits}")


def mode_case_sets_equal(spec: batch_run.BatchSpec, result: batch_run.BatchResult) -> bool:
    """모드별로 줄이 있는 사례 집합이 서로 같은가(채점 전 확인 5, 룰북 B3-3 조건 6의 증거. 참·거짓만)."""
    sets = [{line["case_id"] for line in result.lines if line["mode"] == mode} for mode in spec.modes]
    return all(s == sets[0] for s in sets)


def status_counts(result: batch_run.BatchResult) -> dict:
    return {status: sum(1 for line in result.lines if line["execution_status"] == status)
            for status in types.EXECUTION_STATUSES}


@dataclass(frozen=True)
class Settings:
    """run_sealed의 입력. outputs·manifest·sealed_root·model_config·repo_root를 바꾸면 리허설(임시 위치)이다."""
    dataset: str
    sandbox: str
    snapshot_id: str
    policy_version: str
    conditions_extra: str | None = None
    outputs: Path = OUTPUTS
    repo_root: Path = REPO_ROOT
    manifest: Path | None = None  # None이면 repo_root/eval/sealed_manifest.json
    sealed_root: Path | None = None  # None이면 sealed_dir(환경변수 또는 기본값)
    model_config: Path | None = None  # None이면 repo_root/configs/model/model.json


def _check_settings(settings: Settings) -> None:
    if settings.dataset not in types.DATASETS:
        raise SealedRunnerError("자료 묶음 이름이 계약의 값이 아니다")
    if not isinstance(settings.sandbox, str) or sandbox_exec.SANDBOX_NAME_RE.fullmatch(settings.sandbox) is None:
        raise SealedRunnerError("샌드박스 이름 형식이 아니다")
    if not sandbox_exec._shaped(settings.snapshot_id, sandbox_exec.SNAPSHOT_ID_RE):
        raise SealedRunnerError("스냅샷 ID 형식이 아니다")
    if not sandbox_exec._shaped(settings.policy_version, sandbox_exec.POLICY_VERSION_RE):
        raise SealedRunnerError("정책 버전 이름 형식이 아니다")


# ----------------------------------------------------------------------------- 4~6. 실행

def run_sealed(settings: Settings, *, cases: list | None = None, clock: Callable[[], datetime] | None = None,
               sleep: Callable[[float], None] | None = None, out=None, err=None) -> int:
    """봉인 묶음 하나를 돌린다(머리 설명의 순서 1~6). 종료 코드를 돌려준다.

    cases를 주면(리허설) 봉인 파일에서 사례를 읽지 않는다. 봉인 묶음이 아닌 자료 묶음은 cases가 있어야 하고 outputs/ 아래
    (봉인 아님)에 쓴다. 해시 대조는 어느 경우에나 먼저 한다.
    """
    out = out or sys.stdout
    err = err or sys.stderr
    try:
        return _run_sealed(settings, cases, clock, sleep, out, err)
    except Exception as exc:  # 예외 이름만(N13. 봉인 묶음이면 문장에 사례 식별자가 들 수 있다)
        print(f"오류: 봉인 실행기가 멈췄다({type(exc).__name__})", file=err, flush=True)
        print(f"종료 코드: {EXIT_FAILED}", file=out, flush=True)
        return EXIT_FAILED


def _run_sealed(settings: Settings, cases: list | None, clock, sleep, out, err) -> int:
    _check_settings(settings)
    sealed = settings.dataset in types.SEALED_DATASETS
    root = settings.repo_root
    sealed_root = settings.sealed_root if settings.sealed_root is not None else sealed_dir()
    manifest = settings.manifest if settings.manifest is not None else root / MANIFEST_FILE
    # 1. 봉인 해시 대조(폴더를 만들기 전. 불일치면 2)
    checked = recheck(sealed_root, manifest)
    print(recheck_text(checked), file=out, flush=True)
    if not checked["ok"]:
        print(f"종료 코드: {EXIT_HASH_MISMATCH}", file=out, flush=True)
        return EXIT_HASH_MISMATCH
    entries = load_manifest(manifest)
    # 2. 사례
    if cases is None:
        if not sealed:
            raise SealedRunnerError("봉인 묶음이 아닌 자료 묶음은 사례 목록을 인자로 받는다(리허설)")
        cases = sealed_case_list(settings.dataset, sealed_root, entries, settings.snapshot_id, settings.policy_version,
                                 err=err)
    cases = [dict(c) for c in cases]
    print(f"계획 사례 {len(cases)}건", file=out, flush=True)
    # 3. 준비
    operator = load_operator_conditions(settings.conditions_extra, settings.dataset, root)
    thresholds = policy_thresholds(policy_load.load_policy(settings.policy_version))
    limits, pacing = load_model_settings(settings.model_config if settings.model_config is not None
                                         else root / MODEL_CONFIG_FILE)
    versions = {"policy_version": settings.policy_version, "rulebook_version": types.RULEBOOK_VERSION,
                "snapshot_id": settings.snapshot_id, "grouping_version": SEALED_GROUPING_VERSION,
                "code_version": sandbox_exec.code_version(root)}
    modes = batch_run.PLANNED_MODES[settings.dataset]
    spec = batch_run.BatchSpec(dataset=settings.dataset, cases=tuple(cases), modes=tuple(modes),
                               order_seed=SEALED_ORDER_SEED, versions=versions)
    batch_run.check_spec(spec, sealed)
    problem = sandbox_exec.sandbox_preflight(settings.sandbox, versions["code_version"], program=PROGRAM)
    if problem is not None:
        print(problem, file=err, flush=True)
        print(f"종료 코드: {EXIT_FAILED}", file=out, flush=True)
        return EXIT_FAILED
    runner = sandbox_exec.SandboxCaseRunner(settings.sandbox,
                                            exec_timeout_s=limits["wall_time_s"] + sandbox_exec.SANDBOX_EXEC_MARGIN_S)
    # 4. 실행 폴더 확보(N8)와 첫 줄
    parent = settings.outputs / SEALED_NAME if sealed else settings.outputs
    other = settings.outputs if sealed else settings.outputs / SEALED_NAME
    clock = clock or trace_log.now_kst
    reserve_kw: dict = {"clock": clock}
    if sleep is not None:
        reserve_kw["sleep"] = sleep
    reserved = run_record.reserve_run_dir(parent, other, RUN_NAME, **reserve_kw)
    label = f"{OUTPUTS.name}/{SEALED_NAME}/{reserved[0]}" if sealed else f"{OUTPUTS.name}/{reserved[0]}"
    print(label, file=out, flush=True)
    result = batch_run.execute_batch(spec, runner, parent=parent, other_parent=other, clock=clock, sleep=sleep,
                                     reserved=reserved, pacing=pacing, run_name=RUN_NAME, domain=DOMAIN, sealed=sealed)
    for incident in runner.incidents:
        print(f"사건: {incident}", file=err, flush=True)
    # 5. 실행 조건 입력 파일(NAT 사후 평가는 봉인 자리를 읽지 않으므로 부르지 않는다)
    extra: dict = {"reproduce_evaluate": reproduce_command(settings.dataset, settings.sandbox, settings.snapshot_id,
                                                          settings.policy_version, settings.conditions_extra),
                   "prescoring_checks": {"final_status": final_status_text(spec, result),
                                         "seed_concurrency": seed_concurrency_text(pacing, result)}}
    sandbox = {"name": settings.sandbox}
    policy_sha = sandbox_exec.policy_file_sha256(root)
    if policy_sha is not None:
        sandbox["policy_yaml_sha256"] = policy_sha
    extra["sandbox"] = sandbox
    if operator is not None:
        merged = batch_run.merge_operator_conditions(extra, operator)
        print(f"알림: 운영자 실행 조건을 실행 조건 입력 파일에 합쳤다(키: {', '.join(merged)}).", file=err, flush=True)
    doc = batch_run.build_run_conditions(dataset=settings.dataset, cases=cases, modes=list(spec.modes),
                                         thresholds=thresholds, order_seed=SEALED_ORDER_SEED, limits=limits,
                                         run_period=(result.started, result.ended), extra=extra)
    batch_run.write_run_conditions(result.run_dir, doc)
    # 6. 끝 줄(건수와 참·거짓만)
    counts = status_counts(result)
    print("실행 상태: " + ", ".join(f"{k} {v}" for k, v in counts.items())
          + f", 재실행 대상 {result.rerun_targets}건·재실행 {result.reruns}건", file=out, flush=True)
    print(f"모드별 사례 집합 일치: {'참' if mode_case_sets_equal(spec, result) else '거짓'}, 순서 seed {SEALED_ORDER_SEED}, "
          f"동시성 {batch_run.CONCURRENCY}", file=out, flush=True)
    print(f"종료 코드: {EXIT_OK}", file=out, flush=True)
    return EXIT_OK


# ----------------------------------------------------------------------------- 명령

def _typed(pattern: re.Pattern, what: str):
    def check(value: str) -> str:
        if not sandbox_exec._shaped(value, pattern):
            raise argparse.ArgumentTypeError(f"{what} 형식이 아니다(값은 되풀이하지 않는다)")
        return value

    return check


def _conditions_extra(value: str) -> str:
    if not relative_path_piece(value):
        raise argparse.ArgumentTypeError("운영자 실행 조건 파일 경로는 공백·제어 문자 없는 상대 경로 한 조각이다")
    return value


def parse_args(argv: list[str] | None) -> Settings:
    parser = argparse.ArgumentParser(prog=PROGRAM, allow_abbrev=False,
                                     description="봉인 묶음의 샌드박스 밖 실행기(단위 E2). 저장소 루트에서 부른다.")
    parser.add_argument("--dataset", required=True, choices=list(types.SEALED_DATASETS))
    parser.add_argument("--sandbox", required=True, type=_typed(sandbox_exec.SANDBOX_NAME_RE, "샌드박스 이름"))
    parser.add_argument("--snapshot", required=True, dest="snapshot_id",
                        type=_typed(sandbox_exec.SNAPSHOT_ID_RE, "스냅샷 ID"))
    parser.add_argument("--policy", required=True, dest="policy_version",
                        type=_typed(sandbox_exec.POLICY_VERSION_RE, "정책 버전 이름"))
    parser.add_argument("--conditions-extra", dest="conditions_extra", type=_conditions_extra)
    ns = parser.parse_args(argv)
    return Settings(dataset=ns.dataset, sandbox=ns.sandbox, snapshot_id=ns.snapshot_id,
                    policy_version=ns.policy_version, conditions_extra=ns.conditions_extra)


def main(argv: list[str] | None = None) -> int:
    """종료 코드: 0 묶음 기록을 끝까지 씀(사례 실패 포함), 1 준비·실행 중 오류, 2 인자 오류·봉인 해시 불일치."""
    try:
        settings = parse_args(argv)
    except SystemExit as exc:
        return EXIT_OK if exc.code in (None, 0) else EXIT_HASH_MISMATCH
    return run_sealed(settings)


def run(inp: object) -> object:
    """봉인 해시 대조(머리 설명 1, 순수 함수).

    입력: {"manifest": [해시 목록 files 항목, ...], "actual": {봉인 폴더 기준 상대경로: sha256 또는 null}}.
    출력: compare_manifest의 결과 {files, matched, mismatched, extra, ok}.
    """
    if not isinstance(inp, dict) or set(inp) != {"manifest", "actual"} or not isinstance(inp["manifest"], list) \
            or not isinstance(inp["actual"], dict):
        raise SealedRunnerError("입력은 manifest(목록)·actual(객체) 두 키의 객체다")
    for entry in inp["manifest"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("file_name"), str) \
                or not isinstance(entry.get("sha256"), str):
            raise SealedRunnerError("manifest 항목은 file_name·sha256 문자열을 가진 객체다")
    return compare_manifest(inp["manifest"], inp["actual"])


if __name__ == "__main__":
    sys.exit(main())
