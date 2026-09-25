"""holdout40 봉인 입력 반입 도구(단위 F5 보조, 소유 M, 보안 검토). 표준 라이브러리 + tradesentry.ingest·snapshot·contract만 쓴다.

봉인 폴더(TRADESENTRY_SEALED_DIR, 없으면 ~/.tradesentry/sealed/)의 holdout40 **입력**만 읽어, 공식 채점 대상 실행 전용 샌드박스
이미지에 겹쳐 넣을 폴더(`--dest`, 저장소·봉인 폴더 밖의 새 폴더)를 만든다. 정답표(`holdout40/answers/`)·생성 코드(`holdout40/gen/`)·
`real_sealed/`는 해시 대조 때 바이트만 읽고(sha256 계산) 내용은 열지 않는다. 이 도구는 eval/ 아래 자료 도구(eval.datagen)를
import하지 않는다(eval/은 이미지에 들어가지 않는다). 수집기 SQLite 재현은 수집기 store_result로, 빌드는 단위 S2, 검증은 단위 S3로 한다.

    uv run --locked python -m scripts.import_sealed_holdout40 --dest <저장소·봉인 폴더 밖의 아직 없는 폴더> \\
        [--sealed-dir <봉인 폴더>] [--manifest eval/sealed_manifest.json] [--snapshot-id holdout40] [--policy policy_v1]

순서
    ① 해시 대조: 해시 목록(eval/sealed_manifest.json)의 files 전체(두 묶음)를 봉인 폴더와 대조한다. 목록 파일이 모두 있고 sha256이
       같고, 목록 밖 파일이 하나도 없어야 한다(자료 계약 §12.2, 평가 스킬 ② "해시 대조 방법"). 불일치면 아무것도 쓰지 않고 종료 코드 2.
       표준 오류에는 목록 안 파일 이름만 적고, 목록 밖 파일은 수만 적는다.
    ② 입력 읽기: `holdout40/input/cases.json`과 `holdout40/input/source/` 아래 파일(manifest.json·collection_log.json·
       snapshot_hash.json·snapshot_build.json·peer_group_<snapshot_id>.csv·raw/*.xml)만 읽는다. 모든 내용 읽기는 read_input_bytes를
       거치고, 이 함수는 `holdout40/input/` 밖 경로를 거부한다.
    ③ 임시 폴더에 수집기 형식 원천(raw/·manifest.json 등)을 놓고 수집기 store_result로 수집기 SQLite를 재현한 뒤(시각은 기록의 고정
       시각), 단위 S2 build_to로 snapshot_build.sqlite를 빌드하고 단위 S3 verify_snapshot(raw 대조 켬, 비교국 표 명시)으로 검증한다.
       빌드 기록의 normalized_sha256이 원천 snapshot_build.json의 값(그리고 cases.json의 snapshot_normalized_sha256이 있으면 그 값)과
       같아야 한다. 검증 실패나 값이 다르면 종료 코드 3(임시 폴더는 지운다).
    ④ `<dest>/`에 저장소 배치 그대로 쓴다(배타 생성). dest는 저장소 안(본 작업 폴더와 git이 아는 모든 worktree, 파일 정체성 비교)이나
       봉인 폴더 안이면 거부한다.
           data/snapshots/<snapshot_id>/snapshot_build.sqlite    단위 S2 빌드
           data/snapshots/<snapshot_id>/snapshot_build.json      빌드 기록(build_file·installed_at·installed_from 포함)
           data/reference/peer_group_<snapshot_id>.csv            원천의 합성 비교국 표(바이트 그대로)
           eval/dev/holdout40/input/cases.json                    원천의 사례 목록(바이트 그대로)
           import_manifest.json                                   쓴 파일의 sha256과 쓴 원천의 해시 목록 항목 참조
       공식 채점 대상 실행 전용 샌드박스에서는 `python -m scripts.stage_sandbox_image --overlay <dest>`가 이 폴더를 빌드 맥락에 더해
       /opt/tradesentry/data/snapshots/<snapshot_id>/와 /opt/tradesentry/eval/dev/holdout40/input/cases.json이 된다.
    ⑤ 표준 출력에는 해시 대조 건수, 빌드 normalized_sha256, 쓴 파일 수만 적는다. 사례 식별자·값·로컬 절대경로는 내지 않는다
       (자료 계약 §10.3 N13).

봉인 묶음의 snapshot_id는 holdout40이어야 하고(`--snapshot-id`), 정책은 policy_v1(`--policy`)이다. cases.json의 dataset은 holdout40,
snapshot_id·policy_version은 인자와 같아야 한다. 시험은 dev20 공개 원천으로 만든 가짜 묶음에 `--snapshot-id dev20 --policy dev-0.1`을 준다.
종료 코드: 0 성공, 2 인자·해시 대조·입력 모양·목적지 오류, 3 빌드·검증·normalized_sha256 불일치, 1 예상 밖 오류(예외 이름만 적는다).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime
from pathlib import Path, PurePosixPath

from tradesentry import ingest
from tradesentry.contract import types
from tradesentry.contract.policy_load import PolicyError, load_policy
from tradesentry.snapshot import build as s2
from tradesentry.snapshot import verify as s3

REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET = "holdout40"
DEFAULT_SEALED_DIR = "~/.tradesentry/sealed/"  # 자료 계약 §10 기본값
DEFAULT_MANIFEST = "eval/sealed_manifest.json"
DEFAULT_SNAPSHOT_ID = "holdout40"
DEFAULT_POLICY = "policy_v1"
INPUT_PREFIX = f"{DATASET}/input/"
CASES_REL = f"{INPUT_PREFIX}cases.json"
SOURCE_PREFIX = f"{INPUT_PREFIX}source/"
RAW_PREFIX = f"{SOURCE_PREFIX}raw/"
LOG_FILE = "collection_log.json"
SOURCE_TEXTS = (LOG_FILE, s2.MANIFEST_FILE, s2.HASH_FILE)  # 수집기 형식 원천의 텍스트 셋
CASES_DEST = f"eval/dev/{DATASET}/input/cases.json"
IMPORT_MANIFEST = "import_manifest.json"
INSTALLED_FROM = "scripts/import_sealed_holdout40.py"
SHA256_RE = re.compile(r"[0-9a-f]{64}")
PEER_NAME_RE = re.compile(r"peer_group_([A-Za-z0-9][A-Za-z0-9_-]*)\.csv")
EXIT_OK, EXIT_UNEXPECTED, EXIT_REFUSED, EXIT_BUILD = 0, 1, 2, 3
# 수집기 ingest.open_snapshot의 표 정의와 같다(수집기는 스냅샷 폴더 위치가 고정이라 그 함수를 부르지 않는다. eval/datagen/dev20.py와 같은 사정)
COLLECTOR_DDL = """
CREATE TABLE collection_receipt(
  request_id TEXT PRIMARY KEY, endpoint TEXT, params_json TEXT, status TEXT, http_status INTEGER,
  attempts INTEGER, response_hash TEXT, row_count INTEGER, result_code TEXT, result_msg TEXT,
  error TEXT, elapsed_ms INTEGER, raw_file_id TEXT, timestamp TEXT);
CREATE TABLE observation(
  snapshot_id TEXT, request_id TEXT, month TEXT, partner_code TEXT, partner_namespace TEXT,
  hs_code TEXT, hs_level INTEGER, hs_version TEXT, flow TEXT, amount_usd INTEGER, net_weight_kg INTEGER,
  observation_status TEXT, raw_file_id TEXT, raw_row_locator TEXT, item_name TEXT,
  PRIMARY KEY(request_id, month, partner_code, hs_code, flow));
CREATE TABLE snapshot_meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE collection_attempt(
  request_id TEXT, endpoint TEXT, params_json TEXT, outcome TEXT, http_status INTEGER, attempts INTEGER,
  result_code TEXT, error TEXT, attempt_errors TEXT, raw_file_id TEXT, response_hash TEXT, timestamp TEXT);
"""


class ImportRefused(Exception):
    """인자·해시 대조·입력 모양·목적지 오류(종료 코드 2). 문장에 로컬 절대경로와 사례 값을 넣지 않는다."""


class BuildMismatch(Exception):
    """빌드·검증 실패나 normalized_sha256 불일치(종료 코드 3)."""


# ----------------------------------------------------------------------------- 경로·정체성
def sealed_dir_from(value: str | None) -> Path:
    """봉인 폴더 위치(인자 → 환경변수 → 기본값). 값만 셈한다."""
    text = value or os.environ.get("TRADESENTRY_SEALED_DIR") or DEFAULT_SEALED_DIR
    return Path(os.path.abspath(os.path.expanduser(text)))


def _inside(path: Path, base: Path) -> bool:
    return path == base or base in path.parents


def _git_common_dir(repo_root: Path) -> Path | None:
    """저장소의 공용 git 폴더(.git 폴더, worktree면 gitdir가 가리키는 폴더의 commondir). git을 부르지 않고 파일만 읽는다."""
    dot = repo_root / ".git"
    try:
        if dot.is_dir():
            gitdir = dot
        elif dot.is_file():
            text = dot.read_text(encoding="utf-8").strip()
            if not text.startswith("gitdir:"):
                return None
            gitdir = Path(os.path.normpath(repo_root / text[len("gitdir:"):].strip()))
        else:
            return None
        common = gitdir / "commondir"
        if common.is_file():
            return Path(os.path.normpath(gitdir / common.read_text(encoding="utf-8").strip()))
        return gitdir
    except OSError:
        return None


def repo_roots(repo_root: Path) -> list[Path]:
    """목적지로 받지 않는 저장소 뿌리: 이 작업 폴더, 본 작업 폴더, git이 아는 모든 worktree(cli.dispatch._repo_roots와 같은 파일)."""
    roots = [repo_root]
    common = _git_common_dir(repo_root)
    if common is not None:
        if common.name == ".git":
            roots.append(common.parent)
        listing = common / "worktrees"
        try:
            entries = sorted(listing.iterdir()) if listing.is_dir() else []
        except OSError:
            entries = []
        for entry in entries:
            try:
                text = (entry / "gitdir").read_text(encoding="utf-8").strip()
            except OSError:
                continue
            roots.append(Path(os.path.normpath(text)).parent)
    return roots


def _identities(paths: list[Path]) -> set[tuple[int, int]]:
    found = set()
    for path in paths:
        try:
            info = os.stat(path)
        except OSError:
            continue
        found.add((info.st_dev, info.st_ino))
    return found


def check_dest(dest: Path, repo_root: Path, sealed: Path) -> Path:
    """아직 없는 폴더이고, 부모가 있고, 부모 사슬이 저장소 뿌리·봉인 폴더와 정체성이 다른지 본다. 만들 절대경로를 돌려준다."""
    target = dest.expanduser()
    if not target.is_absolute():
        target = Path.cwd() / target
    if target.exists() or target.is_symlink():
        raise ImportRefused("--dest가 이미 있다. 아직 없는 폴더 이름을 준다")
    if not target.parent.is_dir():
        raise ImportRefused("--dest의 부모 폴더가 없다")
    resolved = target.parent.resolve() / target.name
    if _inside(resolved, repo_root.resolve()) or _inside(resolved, sealed) or _inside(resolved, sealed.resolve()):
        raise ImportRefused("--dest는 저장소·봉인 폴더 밖이어야 한다")
    forbidden = _identities(repo_roots(repo_root)) | _identities([sealed])
    chain = [os.stat(folder) for folder in (resolved.parent, *resolved.parent.parents)]
    if any((info.st_dev, info.st_ino) in forbidden for info in chain):
        raise ImportRefused("--dest는 저장소·봉인 폴더 밖이어야 한다(파일 정체성)")
    return resolved


# ----------------------------------------------------------------------------- ① 해시 대조
def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(path: Path) -> list[dict]:
    """해시 목록의 files 항목(file_name·sha256 모양 검사, 이름 중복 거부)."""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ImportRefused(f"해시 목록을 읽지 못했다({type(exc).__name__})") from None
    files = doc.get("files") if isinstance(doc, dict) else None
    if not isinstance(files, list) or not files:
        raise ImportRefused("해시 목록에 files 항목이 없다")
    names = set()
    for entry in files:
        name, digest = (entry.get("file_name"), entry.get("sha256")) if isinstance(entry, dict) else (None, None)
        if not isinstance(name, str) or not name or name.startswith("/") or ".." in PurePosixPath(name).parts:
            raise ImportRefused("해시 목록의 file_name이 봉인 폴더 기준 상대경로가 아니다")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise ImportRefused(f"해시 목록의 sha256 모양이 아니다: {name}")
        if name in names:
            raise ImportRefused(f"해시 목록에 같은 file_name이 두 번 있다: {name}")
        names.add(name)
    return files


def sealed_files(sealed: Path) -> set[str]:
    """봉인 폴더의 파일 전부(상대경로, POSIX). 폴더 심볼릭 링크는 따라가지 않고, 파일 심볼릭 링크는 파일로 센다."""
    if not sealed.is_dir():
        raise ImportRefused("봉인 폴더가 없다")
    found = set()
    for current, dirs, files in os.walk(sealed, followlinks=False):
        dirs.sort()
        for name in files:
            found.add((Path(current) / name).relative_to(sealed).as_posix())
    return found


def check_manifest(sealed: Path, files: list[dict]) -> dict:
    """해시 목록 전체를 봉인 폴더와 대조한다. {"listed", "matched", "missing", "mismatched", "extra"}. 이름은 목록 안 파일만 담는다."""
    present = sealed_files(sealed)
    listed = {entry["file_name"]: entry["sha256"] for entry in files}
    missing, mismatched, matched = [], [], 0
    for name in sorted(listed):
        path = sealed / name
        if name not in present or path.is_symlink() or not path.is_file():
            missing.append(name)
        elif _sha256_file(path) != listed[name]:
            mismatched.append(name)
        else:
            matched += 1
    extra = len(present - set(listed))
    return {"listed": len(listed), "matched": matched, "missing": missing, "mismatched": mismatched, "extra": extra}


# ----------------------------------------------------------------------------- ② 입력 읽기(관문)
def read_input_bytes(sealed: Path, rel: str) -> bytes:
    """봉인 입력 파일 하나의 바이트. holdout40/input/ 밖 경로는 거부한다(정답표·생성 코드·real_sealed를 열지 않는 관문)."""
    parts = PurePosixPath(rel).parts
    if not rel.startswith(INPUT_PREFIX) or ".." in parts or rel.startswith("/"):
        raise ImportRefused(f"봉인 입력 밖 경로는 읽지 않는다: {rel}")
    path = sealed / rel
    if path.is_symlink() or not path.is_file():
        raise ImportRefused(f"봉인 입력 파일이 없다: {rel}")
    with open(path, "rb") as handle:
        return handle.read()


def _json(data: bytes, rel: str) -> dict:
    try:
        doc = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise ImportRefused(f"JSON이 아니다: {rel}") from None
    if not isinstance(doc, dict):
        raise ImportRefused(f"JSON 객체가 아니다: {rel}")
    return doc


def select_inputs(files: list[dict], snapshot_id: str) -> dict:
    """해시 목록에서 읽을 입력 항목을 고른다(이름만 본다). 사례 목록, 원천 텍스트 셋, 빌드 기록, 비교국 표 하나, raw XML들."""
    by_name = {entry["file_name"]: entry for entry in files}
    required = [CASES_REL, *(SOURCE_PREFIX + name for name in SOURCE_TEXTS), SOURCE_PREFIX + s2.BUILD_RECORD]
    missing = [name for name in required if name not in by_name]
    if missing:
        raise ImportRefused(f"해시 목록에 holdout40 입력 항목이 없다: {', '.join(missing)}")
    peers = [name for name in by_name if name.startswith(SOURCE_PREFIX) and "/" not in name[len(SOURCE_PREFIX):]
             and PEER_NAME_RE.fullmatch(name[len(SOURCE_PREFIX):])]
    if peers != [f"{SOURCE_PREFIX}peer_group_{snapshot_id}.csv"]:
        raise ImportRefused(f"해시 목록의 비교국 표가 peer_group_{snapshot_id}.csv 하나가 아니다({len(peers)}개)")
    raws = sorted(name for name in by_name if name.startswith(RAW_PREFIX) and "/" not in name[len(RAW_PREFIX):]
                  and name.endswith(".xml"))
    if not raws:
        raise ImportRefused("해시 목록에 holdout40 raw 응답이 없다")
    others = [name for name in by_name if name.startswith(INPUT_PREFIX)
              and name not in required and name not in peers and name not in raws]
    if others:
        raise ImportRefused(f"holdout40/input/ 아래에 정해진 배치 밖 파일이 {len(others)}개 있다")
    return {"cases": by_name[CASES_REL], "texts": {name: by_name[SOURCE_PREFIX + name] for name in SOURCE_TEXTS},
            "record": by_name[SOURCE_PREFIX + s2.BUILD_RECORD], "peer": by_name[peers[0]],
            "raws": [by_name[name] for name in raws]}


def read_inputs(sealed: Path, selected: dict, snapshot_id: str, policy_version: str) -> dict:
    """입력 파일을 읽고 모양을 확인한다. 값(사례 식별자)은 다루지 않는다."""
    cases_bytes = read_input_bytes(sealed, CASES_REL)
    cases = _json(cases_bytes, CASES_REL)
    if cases.get("dataset") != DATASET:
        raise ImportRefused("cases.json의 dataset이 holdout40이 아니다")
    if cases.get("snapshot_id") != snapshot_id:
        raise ImportRefused("cases.json의 snapshot_id가 --snapshot-id와 다르다")
    if cases.get("policy_version") != policy_version:
        raise ImportRefused("cases.json의 policy_version이 --policy와 다르다")
    expected_cases = cases.get("snapshot_normalized_sha256")
    if expected_cases is not None and not (isinstance(expected_cases, str) and SHA256_RE.fullmatch(expected_cases)):
        raise ImportRefused("cases.json의 snapshot_normalized_sha256 모양이 아니다")
    texts = {name: read_input_bytes(sealed, SOURCE_PREFIX + name) for name in SOURCE_TEXTS}
    manifest = _json(texts[s2.MANIFEST_FILE], s2.MANIFEST_FILE)
    if manifest.get("snapshot_id") != snapshot_id:
        raise ImportRefused("원천 manifest.json의 snapshot_id가 --snapshot-id와 다르다")
    if not isinstance(manifest.get("requests"), list) or not isinstance(manifest.get("config"), dict):
        raise ImportRefused("원천 manifest.json에 requests·config가 없다")
    log = _json(texts[LOG_FILE], LOG_FILE)
    if not isinstance(log.get("collected_at"), str) or not all(isinstance(log.get(k), list) for k in ("FAILED", "NOT_COLLECTED")):
        raise ImportRefused("원천 collection_log.json에 collected_at·FAILED·NOT_COLLECTED가 없다")
    record = _json(read_input_bytes(sealed, SOURCE_PREFIX + s2.BUILD_RECORD), s2.BUILD_RECORD)
    expected = record.get("normalized_sha256")
    if record.get("snapshot_id") != snapshot_id or not (isinstance(expected, str) and SHA256_RE.fullmatch(expected)):
        raise ImportRefused("원천 snapshot_build.json의 snapshot_id·normalized_sha256이 맞지 않다")
    if expected_cases is not None and expected_cases != expected:
        raise ImportRefused("cases.json의 snapshot_normalized_sha256이 원천 snapshot_build.json과 다르다")
    peer_name = selected["peer"]["file_name"][len(SOURCE_PREFIX):]
    raws = {entry["file_name"][len(RAW_PREFIX):]: read_input_bytes(sealed, entry["file_name"]) for entry in selected["raws"]}
    return {"cases_bytes": cases_bytes, "texts": texts, "manifest": manifest, "log": log, "expected": expected,
            "peer_name": peer_name, "peer_bytes": read_input_bytes(sealed, selected["peer"]["file_name"]), "raws": raws}


# ----------------------------------------------------------------------------- ③ 수집기 SQLite 재현 → S2 빌드 → S3 검증
def materialize_collector(inputs: dict, snapshot_id: str, target_dir: Path) -> Path:
    """수집기 형식 스냅샷 폴더를 target_dir에 새로 만든다(원천 텍스트, raw/, 수집기 store_result로 적재한 snapshot.sqlite)."""
    manifest, log = inputs["manifest"], inputs["log"]
    fixed = log["collected_at"]
    failed, not_collected = set(log["FAILED"]), set(log["NOT_COLLECTED"])
    target_dir.mkdir(parents=False, exist_ok=False)
    (target_dir / s2.RAW_DIR).mkdir()
    for name, data in inputs["texts"].items():
        (target_dir / name).write_bytes(data)
    ok_files = set()
    con = sqlite3.connect(target_dir / s2.COLLECTOR_DB)
    try:
        con.executescript(COLLECTOR_DDL)
        for request in manifest["requests"]:
            rid = request["request_id"]
            if rid in not_collected:
                continue
            if rid in failed:
                result = {"ok": False, "http_status": 500, "attempts": 3, "raw": b"", "error": "HTTPError 500",
                          "attempt_errors": ["HTTPError 500"] * 3, "elapsed_ms": 0}
            else:
                name = f"{rid}.xml"
                if name not in inputs["raws"]:
                    raise ImportRefused("OK 요청의 raw 응답이 원천에 없다")
                ok_files.add(name)
                result = {"ok": True, "http_status": 200, "attempts": 1, "error": None, "attempt_errors": [],
                          "raw": inputs["raws"][name], "elapsed_ms": 0}
            ingest.store_result(target_dir, con, snapshot_id, request["endpoint"], request["params"], result,
                                request["months"])
        con.execute("UPDATE collection_receipt SET timestamp = ?", (fixed,))
        con.execute("UPDATE collection_attempt SET timestamp = ?", (fixed,))
        config = manifest["config"]
        period = config.get("period") or {}
        meta = {"snapshot_id": snapshot_id, "source_kind": "controlled", "created_at": fixed, "last_collect_at": fixed,
                "importer": "KR", "units": json.dumps(ingest.UNITS, ensure_ascii=False),
                "valuation_basis": json.dumps(ingest.VALUATION, ensure_ascii=False),
                "units_confirmed": "합성 자료(controlled): 금액은 USD 정수, 중량은 kg 정수로 만들었다",
                "precision_rule": "amount exact integer USD; weight integer kg per row (합성 자료)",
                "hs_version": s2.COLLECTOR_HS_VERSION, "coverage_status": "IN_PROGRESS",
                "period_start": period.get("start"), "period_end": period.get("end"),
                "source_url": json.dumps(["eval/datagen/dev20.py", "eval/scenarios/SCENARIO_SPEC.md"])}
        con.executemany("INSERT INTO snapshot_meta(key, value) VALUES(?, ?)", sorted(meta.items()))
        con.commit()
    finally:
        con.close()
    if set(inputs["raws"]) != ok_files:
        raise ImportRefused(f"원천 raw 파일({len(inputs['raws'])})이 OK 요청({len(ok_files)})과 다르다")
    return target_dir


def build_and_verify(collector_dir: Path, peer_file: Path, snapshot_id: str, policy: dict, work_dir: Path) -> tuple[Path, dict]:
    """단위 S2로 work_dir/snapshot_build.sqlite를 빌드하고 기록을 옆에 쓴 뒤 단위 S3(raw 대조 켬)로 검증한다. (빌드 파일, 기록)."""
    db_path = work_dir / s2.BUILD_FILE
    record = s2.build_to(db_path, snapshot_id, source_dir=collector_dir, policy=policy, peer_group_files=[peer_file])
    record = {**record, "build_file": s2.BUILD_FILE, "installed_from": INSTALLED_FROM,
              "installed_at": datetime.now(types.KST).isoformat(timespec="seconds")}
    (work_dir / s2.BUILD_RECORD).write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    report = s3.verify_snapshot(snapshot_id, build_file=db_path, source_dir=collector_dir, peer_group_files=[peer_file])
    if not report["ok"]:
        failed = [c["name"] for c in report["checks"] if c["ok"] is False]
        raise BuildMismatch(f"단위 S3 검증 실패: {', '.join(failed)}")
    return db_path, record


# ----------------------------------------------------------------------------- ④ 쓰기
def _copy_new(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(source, "rb") as src, open(target, "xb") as dst:
        shutil.copyfileobj(src, dst, 1 << 20)


def _write_new(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "xb") as handle:
        handle.write(data)


def write_dest(dest: Path, snapshot_id: str, build_file: Path, record: dict, inputs: dict, selected: dict,
               check: dict, manifest_sha256: str, policy_version: str) -> dict:
    """목적지 폴더를 만들고 네 파일과 import_manifest.json을 배타 생성한다. 실패하면 만든 폴더를 지운다."""
    os.mkdir(dest)
    try:
        snap = f"data/snapshots/{snapshot_id}"
        plan = [(f"{snap}/{s2.BUILD_FILE}", build_file, None),
                (f"{snap}/{s2.BUILD_RECORD}", None, (json.dumps(record, ensure_ascii=False, indent=1) + "\n").encode("utf-8")),
                (f"data/reference/{inputs['peer_name']}", None, inputs["peer_bytes"]),
                (CASES_DEST, None, inputs["cases_bytes"])]
        entries = []
        for rel, source, data in plan:
            out = dest / rel
            if source is not None:
                _copy_new(source, out)
            else:
                _write_new(out, data)
            entries.append({"path": rel, "sha256": _sha256_file(out), "size": out.stat().st_size})
        used = [selected["cases"], *selected["texts"].values(), selected["record"], selected["peer"], *selected["raws"]]
        doc = {"dataset": DATASET, "snapshot_id": snapshot_id, "policy_version": policy_version,
               "normalized_sha256": record["normalized_sha256"], "sealed_manifest_sha256": manifest_sha256,
               "hash_check": {"listed": check["listed"], "matched": check["matched"], "extra": check["extra"]},
               "source_files": [{"file_name": e["file_name"], "sha256": e["sha256"]} for e in used],
               "files": entries, "installed_from": INSTALLED_FROM,
               "imported_at": datetime.now(types.KST).isoformat(timespec="seconds")}
        payload = (json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        _write_new(dest / IMPORT_MANIFEST, payload)
        return {"files": len(entries), "import_manifest_sha256": hashlib.sha256(payload).hexdigest()}
    except BaseException:
        shutil.rmtree(dest, ignore_errors=True)
        raise


# ----------------------------------------------------------------------------- 진입
def run(sealed: Path, manifest_path: Path, dest: Path, snapshot_id: str, policy_version: str, repo_root: Path = REPO_ROOT) -> dict:
    """전체 순서 ①~④. 성공하면 표준 출력에 낼 값(dict)을 돌려준다. 실패는 ImportRefused·BuildMismatch."""
    if not s2.SNAPSHOT_ID_RE.fullmatch(snapshot_id or ""):
        raise ImportRefused("--snapshot-id가 경로 조각으로 안전한 이름이 아니다")
    manifest_path = manifest_path if manifest_path.is_absolute() else repo_root / manifest_path
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ImportRefused("해시 목록 파일이 없다")
    target = check_dest(dest, repo_root, sealed)
    try:
        policy = load_policy(policy_version)
    except PolicyError as exc:
        raise ImportRefused(f"정책을 읽지 못했다({type(exc).__name__})") from None
    files = load_manifest(manifest_path)
    check = check_manifest(sealed, files)
    if check["missing"] or check["mismatched"] or check["extra"]:
        raise ImportRefused("봉인 해시 불일치 — "
                            f"목록 {check['listed']}개 중 일치 {check['matched']}개, 없음 {len(check['missing'])}개, "
                            f"해시 다름 {len(check['mismatched'])}개, 목록 밖 파일 {check['extra']}개"
                            + "".join(f"\n  없음: {name}" for name in check["missing"])
                            + "".join(f"\n  해시 다름: {name}" for name in check["mismatched"]))
    selected = select_inputs(files, snapshot_id)
    inputs = read_inputs(sealed, selected, snapshot_id, policy_version)
    with tempfile.TemporaryDirectory(prefix="tradesentry_import_") as tmp:
        work = Path(tmp)
        collector = materialize_collector(inputs, snapshot_id, work / "collector")
        peer_file = work / inputs["peer_name"]
        peer_file.write_bytes(inputs["peer_bytes"])
        try:
            build_file, record = build_and_verify(collector, peer_file, snapshot_id, policy, work)
        except (s2.BuildError, sqlite3.Error, ValueError, KeyError) as exc:
            raise BuildMismatch(f"빌드 실패({type(exc).__name__})") from None
        if record["normalized_sha256"] != inputs["expected"]:
            raise BuildMismatch("빌드 normalized_sha256이 원천 snapshot_build.json의 값과 다르다")
        if check_dest(dest, repo_root, sealed) != target:
            raise ImportRefused("--dest가 확인한 뒤 바뀌었다")
        written = write_dest(target, snapshot_id, build_file, record, inputs, selected, check,
                             _sha256_file(manifest_path), policy_version)
    return {"check": check, "snapshot_id": snapshot_id, "policy_version": policy_version,
            "normalized_sha256": record["normalized_sha256"], **written}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scripts.import_sealed_holdout40", allow_abbrev=False,
                                     description="holdout40 봉인 입력을 해시 대조 뒤 빌드·검증해 이미지 겹침 폴더로 만든다")
    parser.add_argument("--dest", required=True, help="만들 폴더(저장소·봉인 폴더 밖, 아직 없는 이름)")
    parser.add_argument("--sealed-dir", help="봉인 폴더(기본: TRADESENTRY_SEALED_DIR, 없으면 ~/.tradesentry/sealed/)")
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST, help="해시 목록(기본 eval/sealed_manifest.json)")
    parser.add_argument("--snapshot-id", default=DEFAULT_SNAPSHOT_ID, help="봉인 묶음의 snapshot_id(기본 holdout40)")
    parser.add_argument("--policy", default=DEFAULT_POLICY, help="빌드 정책 버전(기본 policy_v1)")
    args = parser.parse_args(argv)
    try:
        result = run(sealed_dir_from(args.sealed_dir), Path(args.manifest), Path(args.dest), args.snapshot_id, args.policy)
    except ImportRefused as exc:
        sys.stderr.write(f"오류: {exc}\n")
        return EXIT_REFUSED
    except BuildMismatch as exc:
        sys.stderr.write(f"오류: {exc}\n")
        return EXIT_BUILD
    except Exception as exc:  # 예외 이름만 적는다(문장에 로컬 절대경로·사례 값이 들 수 있다)
        sys.stderr.write(f"오류: 반입 중 예상 밖 오류({type(exc).__name__})\n")
        return EXIT_UNEXPECTED
    check = result["check"]
    print(f"hash_check listed={check['listed']} matched={check['matched']} extra={check['extra']}")
    print(f"build snapshot_id={result['snapshot_id']} policy_version={result['policy_version']} "
          f"normalized_sha256={result['normalized_sha256']}")
    print(f"written files={result['files']} import_manifest_sha256={result['import_manifest_sha256']}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
