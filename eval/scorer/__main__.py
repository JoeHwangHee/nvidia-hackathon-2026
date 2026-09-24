"""독립 채점기 명령: python -m eval.scorer --run <run_dir> (저장소 루트에서, 샌드박스 밖에서, 키 변수를 뺀 환경에서 실행).

<run_dir>는 채점할 평가 묶음 실행 폴더 outputs/{실행명}/(봉인 묶음이면 outputs/sealed/{실행명}/)다. 채점기는 자기 출력
폴더 outputs/score-{시각}/를 이미 있으면 실패하는 폴더 만들기로 확보하고(자료 계약 docs/rules/DATA_CONTRACT_V1.md §10.3
N8), 그 이름을 표준 출력 첫 줄로 알린 뒤 scorer_claims-{시각}.jsonl, scorer_results-{시각}.jsonl, scorer_summary-{시각}.md를
이미 있으면 실패하는 방식으로 쓴다. 종료 코드 0은 세 파일을 끝까지 썼을 때만 낸다.

- 봉인 묶음(<run_dir>가 outputs/sealed/ 아래)을 채점할 때 표준 출력·오류 출력에는 첫 줄의 실행 폴더 이름과 끝 상태만
  낸다. 사례 식별자와 사례별 메시지는 내지 않는다(N10). 무엇을 읽기 전에 폴더 위치로 이 방식을 정한다.
- 봉인 폴더 위치는 환경변수 TRADESENTRY_SEALED_DIR 값, 비어 있으면 기본값(홈 폴더의 .tradesentry/sealed/)에서만 받는다.
  <run_dir> 안에 적힌 경로는 따르지 않는다. 봉인 파일은 eval/sealed_manifest.json에 있는 것만 해시를 대조한 뒤 읽는다.
- 채점기는 실행 조건을 실행 조건 입력 파일에서만 읽는다(자료 계약 §8.2). 샌드박스가 쓴 파일(묶음 기록·보고서)은 믿지
  않는 입력으로 검증한다. 채점기 커밋 해시는 하위 프로세스로 얻지 않고 그 파일에서 받는다.
- tradesentry 패키지 전부와 eval.datagen을 import하지 않는다. 모델·네트워크·하위 프로세스를 쓰지 않는다.

실행 조건 입력 파일(임시 형식, 결정 D6: MVP 전 임시로 정해 쓰고 F1 전에 MT7과 확정)
- 위치와 이름: <run_dir>/run_conditions-{시각}.json. {시각}은 <run_dir> 실행명의 시각이다. 내려받기를 끝낸 호스트 쪽
  프로그램이 채점기를 부르기 전에 배타 생성한다. 글롭으로 찾지 않는다.
- 필수 키: dataset, planned_cases([{case_id, hs6, partner(국가 코드, ALL 아님), month}], 분모), planned_modes,
  policy_detection_thresholds(정책 탐지 임계값 수 목록, 비면 안 된다. 룰북 B3-2 EX-5가 쓴다). 채점기 계산에 쓰는 선택
  키: snapshot.file(저장소 상대경로, 없으면 data/snapshots/{snapshot_id}/snapshot_build.sqlite). 나머지는 요약에 그대로
  옮기는 값이다(CONDITION_KEYS).
- 없으면 채점하지 않는다. 계약 밖 키, 형식이 틀린 값, 로컬 절대경로나 키 모양(NVIDIA 키 접두어, 서비스키 요청
  파라미터)이 든 값은 거부한다. 개발 묶음에서 옮기는 값이 없으면 요약에 "미기재"로 적는다. 봉인 묶음은
  SEALED_REQUIRED가 모두 있어야 하고 봉인 해시 재대조가 "일치"여야 하며, 봉인 출력이 있어야 하는 값
  (nat_profile_summary, korean_sample_review)이 있으면 거부한다.

믿지 않는 입력(샌드박스가 쓴 묶음 기록·보고서)의 크기와 모양
- 파일 크기 상한: 보고서 MAX_REPORT_BYTES, 묶음 기록·정답표·봉인 파일 MAX_INPUT_BYTES, 실행 조건 입력 파일
  MAX_CONDITIONS_BYTES. 상한을 넘거나 JSON이 아니거나 너무 깊이 중첩한 보고서, claim·산문이 상한을 넘는 보고서는
  "유효한 최종 보고서 없음"(보고서 단위 실패)으로 세고 사유를 요약에 적는다. 묶음 기록이 그러면 입력 오류다.
- 묶음 기록(JSONL)은 줄바꿈 문자(\n)로만 나눈다(U+2028 등에서 나누지 않는다).
- 봉인 묶음은 인자 해석 뒤 어떤 예외에서도 표준 출력에 끝 상태만 낸다(N10). 오류 문장에는 로컬 절대경로를 넣지
  않는다(N13: OSError는 형식 이름과 strerror만).

아직 정해지지 않은 것(F1 전 보완, 한 곳에 모았다): dev20 정답표 경로(DT5, DEV20_ANSWERS), 봉인 정답표·표본 파일 이름
(DT6·DT7, SEALED_FILES), 평가 묶음 실행 이름과 묶음 기록 도메인명(MT7, BATCH_DOMAINS), 사례 폴더 안 보고서 파일의
도메인명(AS3, REPORT_DOMAIN). 모르면 오류로 멈춘다.
"""
import argparse
import hashlib
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path

from eval.scorer import claims as c1
from eval.scorer import prose as c2
from eval.scorer import results as c3
from eval.scorer import summary as c4

EXIT_OK = 0
EXIT_FAILED = 1  # 실행 폴더를 확보한 뒤의 입력 오류·내부 오류
EXIT_USAGE = 2   # 인자 오류(실행 폴더를 확보하기 전)
EXIT_OUTPUT = 4  # 출력 규칙 위반(실행명을 확보하지 못함, 쓰려는 파일이 이미 있음)

REPO_ROOT = Path(__file__).resolve().parents[2]
KST = timezone(timedelta(hours=9), "KST")
STAMP_FORMAT = "%y%m%d%H%M%S"
MAX_ATTEMPTS = 10
RUN_NAME = "score"
CONDITIONS_DOMAIN = "run_conditions"
BATCH_DOMAINS = {"evaluate": "evaluation_batch_run"}  # 평가 묶음 실행 이름 → 묶음 기록 도메인명(단위 E1)
REPORT_DOMAIN = "reports_render_ko"  # 사례 실행 폴더 안 보고서 객체 파일의 도메인명(단위 R2, AS3에서 맞춘다)
SNAPSHOT_FILE = "snapshot_build.sqlite"
ORACLE_PATH = ("eval", "dev", "oracle_ABC.json")
DEV20_ANSWERS: tuple[str, ...] | None = None  # 로드맵 DT5가 정한다
SEALED_FILES: dict[str, str | None] = {"holdout40": None, "real_sealed": None}  # 봉인 폴더 기준 상대경로(DT6·DT7)
SEALED_MANIFEST = ("eval", "sealed_manifest.json")
SEALED_ENV = "TRADESENTRY_SEALED_DIR"

CONDITION_KEYS = frozenset({
    "dataset", "planned_cases", "planned_modes", "snapshot", "policy_detection_thresholds", "rulebook",
    "grouping_reason", "scorer_commit", "prose_patterns_commit", "run_period", "concurrency", "order_seed", "limits",
    "sandbox", "sealed_hash_recheck", "sealed_provenance_check", "precheck", "prescoring_checks",
    "skill_call_success", "nat_profile_summary", "korean_sample_review", "reproduce_evaluate", "a_grade"})
SEALED_REQUIRED = ("rulebook", "scorer_commit", "prose_patterns_commit", "sealed_hash_recheck",
                   "sealed_provenance_check", "prescoring_checks", "precheck", "sandbox")
SEALED_FORBIDDEN = ("nat_profile_summary", "korean_sample_review")
ABSOLUTE_PATH = re.compile(r"(?<![\w.])/(?:Users|home|private|tmp|var|root|opt|mnt|Volumes)/|(?<![\w.])~[/](?!\.tradesentry[/]sealed[/])"
                           r"|\b[A-Za-z]:\\")
# 키 모양(비밀값·로컬 경로 검사 스크립트와 같은 두 가지). 패턴 글자를 나눠 적어 이 파일이 검사에 걸리지 않게 한다.
SECRET_SHAPE = re.compile("nv" + "api-|service" + r"Key\s*=", re.I)
RUN_ID_RE = c3.RUN_ID_RE
MAX_REPORT_BYTES = 1 << 20       # 보고서 파일 1 MiB(잠정)
MAX_INPUT_BYTES = 16 << 20       # 묶음 기록·정답표·봉인 파일 16 MiB
MAX_CONDITIONS_BYTES = 1 << 20   # 실행 조건 입력 파일 1 MiB


class UsageError(Exception):
    """인자·<run_dir> 위치 오류(실행 폴더를 확보하기 전). sealed는 outputs/sealed/ 아래를 가리켰는지다."""

    def __init__(self, message: str, sealed: bool = False):
        super().__init__(message)
        self.sealed = sealed


class OutputError(Exception):
    """출력 규칙 위반."""


def _fail(message: str) -> None:
    raise c1.ScorerInputError(message)


# ----------------------------------------------------------------------------- 위치와 실행명

def sealed_hint(arg: str, repo_root: Path) -> bool:
    """<run_dir> 인자가 봉인 묶음 자리(outputs/sealed/ 아래)를 가리키는가. 마지막 조각은 따라가지 않고(심볼릭 링크여도)
    부모 폴더만 풀어 본다. 저장소 안 경로 조각에 sealed가 있어도 봉인으로 본다(outputs/sealed/../{실행명}처럼 봉인
    자리를 지나 개발 자리로 풀리는 경로를 받지 않으려고). 저장소 뿌리까지의 조각은 보지 않는다(뿌리 경로에 sealed라는
    폴더 이름이 있어도 개발 묶음을 막지 않게). 알 수 없으면 봉인으로 본다(조용한 출력이 안전한 쪽이다)."""
    try:
        candidate = Path(arg) if Path(arg).is_absolute() else Path.cwd() / arg
        parts = candidate.parts
        for root in (repo_root.parts, repo_root.resolve().parts):
            if parts[:len(root)] == root:
                parts = parts[len(root):]
                break
        return candidate.parent.resolve() == (repo_root / "outputs" / "sealed").resolve() or "sealed" in parts
    except (OSError, RuntimeError, ValueError):
        return True


def locate_run_dir(arg: str, repo_root: Path) -> tuple[Path, bool]:
    """<run_dir>를 검증하고 (실행 폴더, 봉인 묶음 여부)를 돌려준다. outputs/{실행명}/이나 outputs/sealed/{실행명}/만 받는다.
    봉인 여부는 무엇을 검사하기 전에 정한다(심볼릭 링크 오류도 봉인 묶음이면 끝 상태만 낸다)."""
    hinted = sealed_hint(arg, repo_root)
    candidate = Path(arg)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    if candidate.is_symlink():
        raise UsageError("<run_dir>가 심볼릭 링크다", hinted)
    resolved = candidate.resolve()
    outputs = (repo_root / "outputs").resolve()
    if resolved.parent == outputs and not hinted:
        sealed = False  # 봉인 자리를 지나 풀면 개발 자리가 되는 경로(예: outputs/sealed/../{실행명})는 받지 않는다
    elif resolved.parent == outputs / "sealed":
        sealed = True
    else:
        raise UsageError("<run_dir>는 outputs/{실행명}/이나 outputs/sealed/{실행명}/이어야 한다", hinted)
    if not RUN_ID_RE.fullmatch(resolved.name) or resolved.name.startswith(RUN_NAME + "-"):
        raise UsageError("<run_dir> 이름이 평가 묶음 실행명({실행 이름}-{yymmddhhmmss})이 아니다", sealed)
    if not resolved.is_dir():
        raise UsageError("<run_dir> 폴더가 없다", sealed)
    return resolved, sealed


def now_kst() -> datetime:
    return datetime.now(KST)


def reserve_run_dir(outputs: Path, clock=now_kst, sleep=time.sleep) -> tuple[str, str, Path]:
    """채점 실행명 score-{시각}을 확보한다(N8): 그 초까지 기다린 뒤 이미 있으면 실패하는 폴더 만들기, 다른 부모 폴더
    (outputs/sealed/)에 같은 이름이 있으면 지우고 다음 초로 다시 한다."""
    outputs.mkdir(exist_ok=True)
    target = clock().astimezone(KST).replace(microsecond=0)
    for _ in range(MAX_ATTEMPTS):
        while (remaining := (target - clock()).total_seconds()) > 0:
            sleep(remaining)
        stamp = target.strftime(STAMP_FORMAT)
        name = f"{RUN_NAME}-{stamp}"
        path = outputs / name
        try:
            os.mkdir(path)
        except FileExistsError:
            target = max(target + timedelta(seconds=1), clock().astimezone(KST).replace(microsecond=0))
            continue
        if (outputs / "sealed" / name).exists():
            os.rmdir(path)
            target = max(target + timedelta(seconds=1), clock().astimezone(KST).replace(microsecond=0))
            continue
        return name, stamp, path
    raise OutputError(f"{MAX_ATTEMPTS}번 시도해도 채점 실행명을 확보하지 못했다")


def _read_regular(path: Path, what: str, limit: int = MAX_INPUT_BYTES) -> bytes:
    if path.is_symlink() or not path.is_file():
        _fail(f"{what}이 없거나 일반 파일이 아니다")
    with open(path, "rb") as fh:
        data = fh.read(limit + 1)
    if len(data) > limit:
        _fail(f"{what}이 크기 상한({limit}바이트)을 넘는다")
    return data


def _loads(data: bytes, what: str) -> object:
    """믿지 않는 입력 JSON을 읽는다. 글자·JSON·중첩 깊이 오류는 입력 오류다."""
    try:
        return c1.loads_json(data.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, RecursionError):
        _fail(f"{what}이 JSON 문서가 아니다")


def _relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.name


# ----------------------------------------------------------------------------- 실행 조건 입력 파일

def _strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [s for v in value.values() for s in _strings(v)] + [k for k in value if isinstance(k, str)]
    if isinstance(value, list):
        return [s for v in value for s in _strings(v)]
    return []


def read_conditions(path: Path, sealed: bool) -> dict:
    """실행 조건 입력 파일을 읽고 검증한다(임시 형식, 머리 설명 참조)."""
    if path.is_symlink() or not path.is_file():
        _fail(f"실행 조건 입력 파일이 없다({path.name})")
    doc = _loads(_read_regular(path, "실행 조건 입력 파일", MAX_CONDITIONS_BYTES), "실행 조건 입력 파일")
    if not isinstance(doc, dict):
        _fail("실행 조건 입력 파일은 JSON 객체여야 한다")
    unknown = sorted(set(doc) - CONDITION_KEYS)
    if unknown:
        _fail(f"실행 조건 입력 파일에 약속 밖 키가 있다({', '.join(unknown)})")
    try:
        strings = _strings(doc)
    except RecursionError:
        _fail("실행 조건 입력 파일이 너무 깊이 중첩돼 있다")
    if any(ABSOLUTE_PATH.search(s) for s in strings):
        _fail("실행 조건 입력 파일에 로컬 절대경로가 들어 있다(N13)")
    if any(SECRET_SHAPE.search(s) for s in strings):
        _fail("실행 조건 입력 파일에 키 모양 값이 들어 있다(절대 규칙 1)")
    if doc.get("dataset") not in c3.DATASETS:
        _fail("실행 조건 입력 파일의 dataset이 계약의 자료 묶음 이름이 아니다")
    modes = doc.get("planned_modes")
    allowed_modes = c4.DATASET_MODES[doc["dataset"]]
    if not isinstance(modes, list) or not modes or len(set(modes)) != len(modes) \
            or any(m not in allowed_modes for m in modes) \
            or (doc["dataset"] != "controlled_fixture_v0" and sorted(modes) != sorted(allowed_modes)):
        _fail("planned_modes가 그 자료 묶음의 모드(룰북 B2)와 맞지 않다")
    cases = doc.get("planned_cases")
    if not isinstance(cases, list) or not cases:
        _fail("planned_cases가 비었다")
    seen = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"case_id", "hs6", "partner", "month"} \
                or not isinstance(case["case_id"], str) or not case["case_id"] or case["case_id"] in seen \
                or not isinstance(case["hs6"], str) or not c1.HS6_RE.fullmatch(case["hs6"]) \
                or not isinstance(case["partner"], str) or not c1.COUNTRY_RE.fullmatch(case["partner"]) \
                or not isinstance(case["month"], str) or not c1.MONTH_RE.fullmatch(case["month"]):
            _fail("planned_cases의 항목은 서로 다른 case_id와 hs6·partner(국가 코드, ALL 아님)·month를 가진 객체여야 "
                  "한다")
        seen.add(case["case_id"])
    snapshot = doc.get("snapshot", {})
    if not isinstance(snapshot, dict) or ("file" in snapshot and not isinstance(snapshot["file"], str)):
        _fail("snapshot은 객체이고 snapshot.file은 문자열이어야 한다")
    thresholds = doc.get("policy_detection_thresholds")
    if not isinstance(thresholds, list) or not thresholds or not all(c1.is_number(t) for t in thresholds):
        _fail("policy_detection_thresholds(정책 탐지 임계값 수 목록)가 없거나 비었다(룰북 B3-2 EX-5가 쓴다)")
    if "concurrency" in doc and not (isinstance(doc["concurrency"], int) and not isinstance(doc["concurrency"], bool)):
        _fail("concurrency는 정수여야 한다")
    sealed_dataset = doc["dataset"] in c3.SEALED_DATASETS
    if sealed_dataset != sealed:
        _fail("봉인 묶음은 outputs/sealed/ 아래에서만, 개발 묶음은 outputs/ 아래에서만 채점한다")
    if sealed:
        missing = [key for key in SEALED_REQUIRED + (("a_grade",) if doc["dataset"] == "real_sealed" else ())
                   if doc.get(key) in (None, "", {}, [])]
        if missing:
            _fail(f"봉인 묶음의 실행 조건 입력 파일에 필요한 값이 없다({', '.join(missing)})")
        if doc["sealed_hash_recheck"] != "일치":
            _fail("봉인 해시 재대조가 일치가 아니다")
        present = [key for key in SEALED_FORBIDDEN if key in doc]
        if present:
            _fail(f"봉인 묶음에는 봉인 출력이 있어야 하는 값을 넣지 않는다({', '.join(present)})")
    return doc


# ----------------------------------------------------------------------------- 스냅샷

def snapshot_path(conditions: dict, snapshot_id: str, repo_root: Path) -> Path:
    rel = c4._get(conditions, "snapshot", "file") or f"data/snapshots/{snapshot_id}/{SNAPSHOT_FILE}"
    parts = Path(rel).parts
    if Path(rel).is_absolute() or ".." in parts or not rel.endswith(".sqlite"):
        _fail("snapshot.file은 저장소 안 .sqlite 파일의 상대경로여야 한다")
    path = repo_root / rel
    if path.is_symlink() or not path.is_file():
        _fail(f"스냅샷 파일이 없다({rel})")
    if repo_root.resolve() not in path.resolve().parents:
        _fail("스냅샷 파일이 저장소 밖이다")
    return path


FULL_TABLES = ("observation", "collection_receipt", "snapshot_meta", "peer_group")  # 행 전체를 읽는 표(나머지는 rowid만)


def load_snapshot(path: Path, snapshot_id: str) -> tuple[c1.Snapshot, str]:
    """스냅샷 SQLite를 읽기 전용으로 열어 색인을 만든다. (색인, 파일 바이트 sha256). 스냅샷 빌드 파일의 표 넷(관측·수신
    기록·메타·비교국 표)을 읽고, 메타의 snapshot_id·schema_version을 대조한다."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    con = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        con.execute("PRAGMA query_only = ON")
        names = [row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")]
        if "observation" not in names:
            _fail("스냅샷에 observation 테이블이 없다")
        tables: dict[str, dict[int, dict]] = {}
        for name in names:
            if not c1.TABLE_RE.fullmatch(name):
                continue
            try:
                if name in FULL_TABLES:
                    cursor = con.execute(f'SELECT rowid AS "__rowid__", * FROM "{name}"')
                    columns = [d[0] for d in cursor.description]
                    tables[name] = {row[0]: dict(zip(columns[1:], row[1:])) for row in cursor}
                else:
                    tables[name] = {row[0]: {} for row in con.execute(f'SELECT rowid FROM "{name}"')}
            except sqlite3.OperationalError:
                continue  # rowid가 없는 테이블은 근거 ID가 가리킬 수 없다
    finally:
        con.close()
    ids = {row.get("snapshot_id") for row in tables["observation"].values()}
    if ids - {snapshot_id}:
        _fail("스냅샷 행의 snapshot_id가 실행 기록의 snapshot_id와 다르다")
    meta = {row.get("key"): row.get("value") for row in tables.get("snapshot_meta", {}).values()}
    if meta.get("snapshot_id") != c1.dumps_json(snapshot_id).replace(" ", "") or meta.get("schema_version") != "1":
        _fail("스냅샷 메타의 snapshot_id가 실행 기록과 다르거나 schema_version이 1이 아니다(스냅샷 빌드 파일이 아니다)")
    return c1.Snapshot(snapshot_id, tables), digest.hexdigest()


# ----------------------------------------------------------------------------- 정답표·봉인 파일

def sealed_dir(environ: dict) -> Path:
    """봉인 폴더: TRADESENTRY_SEALED_DIR 값, 비어 있으면 홈 폴더의 .tradesentry/sealed/(자료 계약 §10)."""
    value = environ.get(SEALED_ENV, "")
    if value:
        return Path(value)
    home = environ.get("HOME", "")
    if not home:
        _fail("봉인 폴더 위치를 정할 수 없다(환경변수 없음)")
    return Path(home) / ".tradesentry" / "sealed"


def read_sealed_file(repo_root: Path, environ: dict, dataset: str, name: str) -> bytes:
    """해시 목록 eval/sealed_manifest.json에 있는 봉인 파일 하나를 해시 대조 뒤 읽는다(자료 계약 §12.2)."""
    manifest = _loads(_read_regular(repo_root.joinpath(*SEALED_MANIFEST), "봉인 해시 목록"), "봉인 해시 목록")
    entries = [e for e in manifest.get("files", []) if isinstance(e, dict)
               and e.get("dataset") == dataset and e.get("file_name") == name] if isinstance(manifest, dict) else []
    if len(entries) != 1 or Path(name).is_absolute() or ".." in Path(name).parts:
        _fail("봉인 파일이 해시 목록에 한 번만 있어야 한다")
    data = _read_regular(sealed_dir(environ) / name, "봉인 파일")
    if hashlib.sha256(data).hexdigest() != entries[0].get("sha256"):
        _fail("봉인 파일 해시가 해시 목록과 다르다")
    return data


def load_answers(dataset: str, repo_root: Path, environ: dict) -> object | None:
    """자료 묶음의 정답표 원문(read_answer_table이 읽는다). 실자료 묶음은 None."""
    if dataset == "controlled_fixture_v0":
        return _loads(_read_regular(repo_root.joinpath(*ORACLE_PATH), "oracle 정답표"), "oracle 정답표")
    if dataset == "dev20":
        if DEV20_ANSWERS is None:
            _fail("dev20 정답표 경로가 아직 정해지지 않았다(로드맵 DT5)")
        return _loads(_read_regular(repo_root.joinpath(*DEV20_ANSWERS), "dev20 정답표"), "dev20 정답표")
    if dataset == "holdout40":
        if SEALED_FILES["holdout40"] is None:
            _fail("holdout40 봉인 정답표 파일 이름이 아직 정해지지 않았다(로드맵 DT6)")
        return _loads(read_sealed_file(repo_root, environ, dataset, SEALED_FILES["holdout40"]), "봉인 정답표")
    return None


def check_sealed_sample(repo_root: Path, environ: dict, planned: list[str]) -> None:
    """real_sealed 채점 표본(봉인)의 사례와 계획 사례가 같은지 본다. 표본 형식: {"cases": [{"case_id"}]} 또는 case_id 목록."""
    if SEALED_FILES["real_sealed"] is None:
        _fail("real_sealed 봉인 표본 파일 이름이 아직 정해지지 않았다(로드맵 DT7)")
    doc = _loads(read_sealed_file(repo_root, environ, "real_sealed", SEALED_FILES["real_sealed"]), "봉인 채점 표본")
    items = doc.get("cases") if isinstance(doc, dict) else doc
    ids = [i.get("case_id") if isinstance(i, dict) else i for i in items] if isinstance(items, list) else None
    if ids is None or sorted(ids) != sorted(planned):
        _fail("계획 사례가 봉인 채점 표본과 다르다")


# ----------------------------------------------------------------------------- 채점

def read_batch(path: Path) -> list[dict]:
    """묶음 기록(JSONL)을 읽는다. 줄은 줄바꿈 문자(\\n)로만 나눈다(JSON 문자열 안의 U+2028 등에서 나누지 않는다)."""
    lines = []
    for number, text in enumerate(_read_regular(path, "묶음 기록").decode("utf-8", errors="strict").split("\n")):
        if not text.strip():
            continue
        try:
            doc = c1.loads_json(text)
        except (ValueError, RecursionError):
            _fail(f"묶음 기록 {number + 1}번째 줄이 JSON이 아니다")
        lines.append(c3.validate_batch_line(doc, number))
    if not lines:
        _fail("묶음 기록이 비었다")
    return lines


def read_report(run_dir: Path, line: dict, sealed: bool) -> tuple[dict | None, str | None, str | None]:
    """사례 실행 폴더(묶음 폴더와 같은 부모의 형제 {run_id})에서 보고서 객체를 읽는다(S0 결정 ④).
    (보고서 또는 None, 파일 바이트 sha256 또는 None, 읽지 못한 사유 또는 None). 폴더·파일이 없거나, 크기 상한을 넘거나,
    JSON 객체가 아니거나 너무 깊이 중첩하면 보고서 없음으로 돌려준다(보고서 단위 실패). 보고서의 run_id·case_id·mode가
    묶음 줄과 다르면 입력 오류다."""
    case_dir = run_dir.parent / line["run_id"]
    if case_dir.is_symlink():
        _fail("사례 실행 폴더가 심볼릭 링크다")
    if not case_dir.is_dir():
        return None, None, "사례 실행 폴더 없음"
    path = case_dir / f"{REPORT_DOMAIN}-{line['run_id'].rsplit('-', 1)[1]}.json"
    if path.is_symlink() or not path.is_file():
        return None, None, "보고서 파일 없음"
    with open(path, "rb") as fh:
        data = fh.read(MAX_REPORT_BYTES + 1)
    if len(data) > MAX_REPORT_BYTES:
        return None, None, "보고서 크기 상한 초과"
    digest = hashlib.sha256(data).hexdigest()
    try:
        report = c1.loads_json(data.decode("utf-8"))
    except RecursionError:
        return None, digest, "보고서 JSON 중첩이 너무 깊다"
    except (ValueError, UnicodeDecodeError):
        return None, digest, "보고서가 JSON이 아니다"
    if not isinstance(report, dict):
        return None, digest, "보고서가 JSON 객체가 아니다"
    if (report.get("run_id"), report.get("case_id"), report.get("mode")) != (line["run_id"], line["case_id"], line["mode"]):
        _fail("사례 실행 폴더의 보고서가 묶음 기록 줄과 맞지 않다(run_id·case_id·mode)")
    return report, digest, None


def score_batch(run_dir: Path, sealed: bool, repo_root: Path, environ: dict, scoring_run: str) -> tuple[list, list, str]:
    """묶음 하나를 채점해 (주장 채점 기록, 실행 결과 기록, 요약 문서)를 돌려준다. 파일은 쓰지 않는다."""
    run_name, stamp = run_dir.name.rsplit("-", 1)
    conditions = read_conditions(run_dir / f"{CONDITIONS_DOMAIN}-{stamp}.json", sealed)
    if run_name not in BATCH_DOMAINS:
        _fail(f"평가 묶음 실행 이름 {run_name}의 묶음 기록 이름을 모른다(로드맵 MT7에서 정한다)")
    lines = read_batch(run_dir / f"{BATCH_DOMAINS[run_name]}-{stamp}.jsonl")
    dataset = conditions["dataset"]
    planned_cases = [c["case_id"] for c in conditions["planned_cases"]]
    planned = {(case, mode) for case in planned_cases for mode in conditions["planned_modes"]}
    run_ids = [line["run_id"] for line in lines]
    if len(set(run_ids)) != len(run_ids):
        _fail("묶음 기록에 같은 run_id가 두 번 나온다")
    for line in lines:
        if line["dataset"] != dataset:
            _fail("묶음 기록의 dataset이 실행 조건 입력 파일과 다르다(한 묶음은 자료 묶음 하나)")
        if (line["case_id"], line["mode"]) not in planned:
            _fail("묶음 기록에 계획 밖 (사례, 모드) 실행이 있다")
    snapshot_ids = {line["snapshot_id"] for line in lines}
    if len(snapshot_ids) != 1:
        _fail("묶음 기록의 snapshot_id가 하나가 아니다")
    snapshot_id = snapshot_ids.pop()

    answers_doc = load_answers(dataset, repo_root, environ)
    if answers_doc is not None:
        answer_ids = set(c3.read_answer_table(answers_doc))
        if not set(planned_cases) <= answer_ids or (dataset != "controlled_fixture_v0"
                                                     and set(planned_cases) != answer_ids):
            _fail("계획 사례가 정답표의 사례와 다르다")
    if dataset == "real_sealed":
        check_sealed_sample(repo_root, environ, planned_cases)
    snap_path = snapshot_path(conditions, snapshot_id, repo_root)
    snap, snap_digest = load_snapshot(snap_path, snapshot_id)

    thresholds = [Fraction(t) for t in conditions["policy_detection_thresholds"]]
    cases = {c["case_id"]: c for c in conditions["planned_cases"]}
    reports: dict[str, dict] = {}
    records: list[dict] = []
    stats: dict[str, dict] = {}
    unread: list[str] = []
    for line in lines:
        if line["execution_status"] != c3.COMPLETED:
            continue
        report, digest, reason = read_report(run_dir, line, sealed)
        if report is not None:
            try:  # 믿지 않는 보고서의 모양·크기 문제는 그 보고서 하나의 실패로 센다(묶음 전체를 멈추지 않는다)
                mine = c1.score_report_claims(report, snap, line["run_id"], snapshot_id,
                                              c3.case_context(cases.get(line["case_id"]), line))
                mine += c2.score_report_prose(report, line["run_id"], snap.hs_codes, thresholds)
                quality = dict(c2.korean_quality(report), extremes=c2.extreme_count(report), report_sha256=digest)
            except c1.ScorerInputError as exc:
                report, reason = None, f"채점할 수 없는 보고서({_reason(exc)})"
            except RecursionError:
                report, reason = None, "채점할 수 없는 보고서(중첩이 너무 깊다)"
        if report is None:
            unread.append(line["run_id"])
            stats[line["run_id"]] = {"unreadable": reason, **({"report_sha256": digest} if digest else {})}
            continue
        reports[line["run_id"]] = report
        records += mine
        stats[line["run_id"]] = quality
    answers = c3.read_answer_table(answers_doc) if answers_doc is not None else {}
    results = [c3.result_line(line, reports.get(line["run_id"]), [r for r in records if r["run_id"] == line["run_id"]],
                              answers.get(line["case_id"]), c3.case_context(cases.get(line["case_id"]), line), snap)
               for line in lines]
    summary_input = {
        "dataset": dataset, "batch_run": run_dir.name, "scoring_run": scoring_run,
        "batch_dir": ("outputs/sealed/" if sealed else "outputs/") + run_dir.name,
        "planned": {"cases": conditions["planned_cases"], "modes": conditions["planned_modes"]},
        "results": results, "claims": records, "answers": answers_doc, "report_stats": stats,
        "reports_unread": unread, "conditions": conditions,
        "meta": {"schema_version": 1, "prose_patterns_sha256": c2.pattern_list_sha256(),
                 "snapshot_file": _relative(snap_path.resolve(), repo_root), "snapshot_file_sha256": snap_digest}}
    return records, results, c4.render(summary_input)


def _reason(exc: Exception) -> str:
    """보고서 단위 실패 사유(요약에 적는다). 채점기가 만든 문장에서 괄호 안 설명만 뺀 짧은 꼴."""
    text = str(exc)
    for known in ("claims가 목록이 아니다", "claim 수가 채점기 상한", "산문 글자 수가 채점기 상한", "사례 문맥"):
        if known in text:
            return known
    return "형식 오류"


def write_outputs(folder: Path, stamp: str, records: list, results: list, summary: str) -> None:
    """세 파일을 이미 있으면 실패하는 방식("xb")으로 쓴다."""
    for name, text in ((f"scorer_claims-{stamp}.jsonl", c1.dumps_jsonl(records)),
                       (f"scorer_results-{stamp}.jsonl", c1.dumps_jsonl(results)),
                       (f"scorer_summary-{stamp}.md", summary)):
        try:
            with open(folder / name, "xb") as fh:
                fh.write(text.encode("utf-8"))
        except FileExistsError as exc:
            raise OutputError(f"{name}이 이미 있다. 덮어쓰지 않는다") from exc


def main(argv: list[str] | None = None, *, repo_root: Path | None = None, environ: dict | None = None,
         clock=now_kst, sleep=time.sleep, out=None, err=None) -> int:
    out = out or sys.stdout
    err = err or sys.stderr
    environ = dict(os.environ) if environ is None else environ
    repo_root = repo_root or REPO_ROOT
    parser = argparse.ArgumentParser(prog="python -m eval.scorer",
                                     description="독립 채점기(샌드박스 밖 정답 대조 채점). 출력은 outputs/score-{시각}/")
    parser.add_argument("--run", dest="run_dir", required=True, metavar="RUN_DIR",
                        help="채점할 실행 폴더(outputs/{실행명}/, 봉인 묶음이면 outputs/sealed/{실행명}/)")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return EXIT_USAGE if exc.code else EXIT_OK
    state = {"sealed": sealed_hint(args.run_dir, repo_root)}
    try:
        return _run(args.run_dir, repo_root, environ, clock, sleep, out, err, state)
    except Exception as exc:  # 어느 단계의 예외든 봉인 묶음이면 끝 상태만 내고, 문장에 경로를 넣지 않는다(N10·N13)
        return _finish(out, err, state["sealed"], "내부 오류", type(exc).__name__, EXIT_FAILED)


def _os_error(exc: OSError) -> str:
    """OSError를 경로 없이 적는다(str(exc)에는 로컬 절대경로가 들어 있다, N13)."""
    return f"{type(exc).__name__}: {exc.strerror or '입출력 오류'}"


def _run(arg: str, repo_root: Path, environ: dict, clock, sleep, out, err, state: dict) -> int:
    try:
        run_dir, sealed = locate_run_dir(arg, repo_root)
    except (UsageError, OSError) as exc:
        if getattr(exc, "sealed", True) or state["sealed"]:  # 봉인 묶음 자리(또는 알 수 없음)면 끝 상태만 낸다(N10)
            print("끝 상태: 실패(인자 오류)", file=out, flush=True)
        else:
            print(f"오류: {exc if isinstance(exc, UsageError) else _os_error(exc)}", file=err)
        return EXIT_USAGE
    state["sealed"] = sealed
    try:
        scoring_run, stamp, folder = reserve_run_dir(repo_root / "outputs", clock, sleep)
    except (OutputError, OSError) as exc:
        detail = str(exc) if isinstance(exc, OutputError) else _os_error(exc)
        print(("끝 상태: 실패(출력 규칙)" if sealed else f"오류: {detail}"), file=out if sealed else err, flush=True)
        return EXIT_OUTPUT
    print(scoring_run, file=out, flush=True)
    try:
        records, results, summary = score_batch(run_dir, sealed, repo_root, environ, scoring_run)
        write_outputs(folder, stamp, records, results, summary)
    except c1.ScorerInputError as exc:
        return _finish(out, err, sealed, "입력 오류", str(exc), EXIT_FAILED)
    except OutputError as exc:
        return _finish(out, err, sealed, "출력 규칙", str(exc), EXIT_OUTPUT)
    except OSError as exc:
        return _finish(out, err, sealed, "내부 오류", _os_error(exc), EXIT_FAILED)
    except Exception as exc:  # 봉인 묶음이면 예외 문장(사례 식별자가 들 수 있다)을 내지 않는다
        return _finish(out, err, sealed, "내부 오류", type(exc).__name__, EXIT_FAILED)
    print("끝 상태: 완료", file=out, flush=True)
    return EXIT_OK


def _finish(out, err, sealed: bool, kind: str, detail: str, code: int) -> int:
    if not sealed:
        print(f"오류({kind}): {detail}", file=err)
    print(f"끝 상태: 실패({kind})", file=out, flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
