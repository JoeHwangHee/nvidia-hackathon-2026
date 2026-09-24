"""샌드박스 이미지 빌드 맥락 스테이징 도구(단위 F5, 소유 M, 보안 검토). 표준 라이브러리만 쓴다.

포함 목록(configs/openshell/image/include.txt)과 --add로 명시한 저장소 경로만 저장소 밖 빈 폴더에 복사해, OpenShell이
`openshell sandbox create --from <그 폴더>`로 빌드할 맥락을 만든다. 저장소 루트나 eval/dev/를 통째로 올리지 않는다(개발
플랜 §4.3 "반입 목록"). .gitignore는 제외 장치가 아니므로 쓰지 않고, 들이면 안 되는 경로는 이 도구의 거부 규칙이 막는다.

    uv run --locked python -m scripts.stage_sandbox_image --dest <저장소 밖의 아직 없는 폴더> [--add <저장소 상대경로>]...

빌드 기록(data/snapshots/<id>/snapshot_build.json)을 들이면 그 기록의 peer_group_files가 가리키는 비교국 표
(data/reference/peer_group_*.csv)를 sha256 대조 뒤 자동으로 함께 들이고, 이미지 기록의 snapshots에 snapshot_id·
normalized_sha256·비교국 표를 적는다(결정 기록 model-decision-mt5-sandbox ⑫).

만드는 것(--dest 아래)
    Dockerfile                  configs/openshell/image/Dockerfile 사본
    image/tradesentry.sh        CLI 실행기 사본
    app/<저장소 상대경로>        들이는 파일(저장소와 같은 배치. 이미지의 /opt/tradesentry/가 된다)
    app/image_manifest.json     들인 파일 목록과 sha256(이미지 안 /opt/tradesentry/image_manifest.json)

거부 규칙(하나라도 걸리면 아무것도 남기지 않고 종료 코드 2)
    - .env와 .env.* 등 이름이 .env로 시작하거나 끝나는 파일, .git·.venv·.dryforge·node_modules 아래
    - outputs/, artifacts/, spikes/, tests/, docs/, scripts/, research_raw/, .claude/ 아래
    - eval/ 아래 전부. 예외는 --add로 준 eval/dev/dev20/input/과 그 아래다(dev20 입력 하위 경로. 로드맵 DT5의 배치는
      입력 eval/dev/dev20/input/cases.json, 정답표 eval/dev/dev20/answers/). dev20 폴더 전체, answers/, 그 밖의 하위
      경로는 거부한다. 이름에 oracle·answer가 든 파일은 어디서든 거부한다
    - data/snapshots/ 아래는 snapshot_build.sqlite·snapshot_build.json만(raw/·manifest·수집기 SQLite·fixture_spec.json 거부).
      dev20 스냅샷(`uv run --locked python -m eval.datagen.dev20 install`이 만드는 data/snapshots/dev20/snapshot_build.sqlite)은
      --add로 준다
    - 비교는 경로 조각을 casefold해서 한다(대소문자를 구분하지 않는 파일 시스템에서 `.ENV`·`Eval/` 같은 별칭 우회를
      막는다). 적힌 철자가 디스크의 철자(os.listdir)와 다르면 거부한다. 하드 링크(링크 수 > 1)와 일반 파일이 아닌 것도 거부한다
    - 심볼릭 링크(파일·폴더), 봉인 폴더(TRADESENTRY_SEALED_DIR, 없으면 기본값) 안의 경로, 저장소 밖으로 풀리는 경로
    - 없는 필수 항목(`?`가 없는 줄과 --add). `?` 줄이 없으면 빼고 알린다
    __pycache__ 폴더와 .pyc 파일은 캐시라 알리지 않고 건너뛴다.

표준 출력에는 저장소 상대경로와 개수·sha256만 쓰고 로컬 절대경로는 쓰지 않는다(자료 계약 §10.3 N13).
종료 코드: 0 성공, 2 인자·거부 규칙·목적지 오류, 1 예상 밖 오류(예외 이름만 적는다).
봉인 입력 반입(공식 채점 대상 실행 전용 이미지)은 이 도구에 아직 없다. 방식과 조건은 MT5 샌드박스 결정 기록 ②에 있다.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = Path("configs") / "openshell" / "image"
INCLUDE_FILE = IMAGE_DIR / "include.txt"
MANIFEST_NAME = "image_manifest.json"
DEFAULT_SEALED_DIR = "~/.tradesentry/sealed/"  # 자료 계약 §10 기본값(끝 / 포함)
BLOCKED_PARTS = frozenset({".git", ".venv", ".dryforge", "node_modules"})
BLOCKED_TOP = ("outputs", "artifacts", "spikes", "tests", "docs", "scripts", "research_raw", ".claude")
CACHE_PARTS = frozenset({"__pycache__"})
SNAPSHOT_FILES = frozenset({"snapshot_build.sqlite", "snapshot_build.json"})
DEV20_INPUT_PREFIX = ("eval", "dev", "dev20", "input")
BUILD_RECORD = "snapshot_build.json"
PEER_GROUP_NAME_RE = re.compile(r"peer_group_[a-z0-9_]+\.csv")
SHA256_RE = re.compile(r"[0-9a-f]{64}")


class StageError(Exception):
    """거부 규칙·목적지·목록 오류. 문장에는 저장소 상대경로만 넣는다."""


def sealed_dir() -> Path:
    """봉인 폴더 위치(값만 셈한다. 그 폴더를 열거나 stat하지 않는다)."""
    return Path(os.path.abspath(os.path.expanduser(os.environ.get("TRADESENTRY_SEALED_DIR") or DEFAULT_SEALED_DIR)))


def _inside(path: Path, base: Path) -> bool:
    return path == base or base in path.parents


def blocked_reason(rel: str, *, from_add: bool) -> str | None:
    """저장소 상대경로(POSIX)가 거부 규칙에 걸리면 이유를, 아니면 None을 돌려준다."""
    raw_parts = PurePosixPath(rel).parts
    if not raw_parts or rel.startswith("/") or ".." in raw_parts:
        return "저장소 상대경로가 아니다"
    # 비교는 casefold한 조각으로 한다. macOS APFS 같은 대소문자를 구분하지 않는 파일 시스템에서는 `.ENV`·`Eval/`·
    # `Outputs/`가 같은 파일·폴더를 가리키므로, 글자 그대로 비교하면 거부 규칙을 우회한다(MT5b 보안 검토 1).
    parts = tuple(part.casefold() for part in raw_parts)
    name = parts[-1]
    if name.startswith(".env") or name.endswith(".env"):
        return ".env 파일"
    if BLOCKED_PARTS.intersection(parts):
        return "저장소 관리·가상환경 폴더"
    if parts[0] in BLOCKED_TOP:
        return f"{parts[0]}/ 아래"
    if "oracle" in name or "answer" in name:
        return "정답표 이름(oracle·answer)"
    if parts[0] == "eval":
        if not (from_add and parts[:4] == DEV20_INPUT_PREFIX):
            return "eval/ 아래(예외는 --add로 준 eval/dev/dev20/input/ 아래)"
    if parts[:2] == ("data", "snapshots"):
        if len(parts) != 4 or name not in SNAPSHOT_FILES:
            return "스냅샷은 snapshot_build.sqlite·snapshot_build.json만"
    return None


def read_include(path: Path) -> list[tuple[str, bool]]:
    """(저장소 상대경로, 선택 항목 여부) 목록."""
    entries = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        optional = line.startswith("?")
        entries.append((line[1:].strip() if optional else line, optional))
    return entries


def check_spelling(repo_root: Path, rel: str) -> None:
    """적힌 경로의 조각마다 부모 폴더 목록(os.listdir)에 글자 그대로 있는지 본다. 대소문자만 다른 별칭 경로를 막는다."""
    current = repo_root
    for part in PurePosixPath(rel).parts:
        try:
            names = os.listdir(current)
        except OSError:
            return  # 없는 경로는 부르는 쪽이 "없음"으로 처리한다
        if part not in names:
            if any(name.casefold() == part.casefold() for name in names):
                raise StageError(f"적힌 철자가 디스크의 철자와 다르다(대소문자): {rel}")
            return
        current = current / part


def _check_regular(path: Path, rel: str) -> None:
    """일반 파일이고 하드 링크가 아닌지 본다(링크 수 > 1이면 다른 이름의 같은 파일일 수 있다)."""
    info = os.lstat(path)
    if not stat.S_ISREG(info.st_mode):
        raise StageError(f"일반 파일이 아니다: {rel}")
    if info.st_nlink > 1:
        raise StageError(f"하드 링크(링크 수 {info.st_nlink})는 들이지 않는다: {rel}")


def _files_under(repo_root: Path, rel: str, *, from_add: bool) -> list[str]:
    """항목 하나를 파일 목록(저장소 상대경로)으로 펼친다. 거부 규칙·심볼릭 링크·하드 링크·저장소 밖·철자 불일치면
    StageError."""
    check_spelling(repo_root, rel)
    source = repo_root / rel
    for parent in [source, *source.parents]:
        if parent == repo_root:
            break
        if parent.is_symlink():
            raise StageError(f"심볼릭 링크는 들이지 않는다: {rel}")
    if not _inside(source.resolve(), repo_root.resolve()):
        raise StageError(f"저장소 밖으로 풀리는 경로다: {rel}")
    if _inside(source.resolve(), sealed_dir()) or _inside(Path(os.path.abspath(source)), sealed_dir()):
        raise StageError(f"봉인 폴더 안의 경로다: {rel}")
    if source.is_file():
        found = [rel]
    else:
        found = []
        for current, dirs, files in os.walk(source, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in CACHE_PARTS)
            for name in list(dirs):
                if (Path(current) / name).is_symlink():
                    raise StageError(f"심볼릭 링크는 들이지 않는다: {Path(current, name).relative_to(repo_root).as_posix()}")
            for name in sorted(files):
                path = Path(current) / name
                if name.endswith(".pyc"):
                    continue
                if path.is_symlink():
                    raise StageError(f"심볼릭 링크는 들이지 않는다: {path.relative_to(repo_root).as_posix()}")
                found.append(path.relative_to(repo_root).as_posix())
    for item in found:
        reason = blocked_reason(item, from_add=from_add)
        if reason:
            raise StageError(f"들이지 않는 경로다({reason}): {item}")
        _check_regular(repo_root / item, item)
    return found


def collect(repo_root: Path, include: list[tuple[str, bool]], added: list[str]) -> tuple[list[str], list[str]]:
    """(들일 파일 목록, 없어서 뺀 선택 항목)."""
    files: dict[str, None] = {}
    missing_optional: list[str] = []
    for rel, optional, from_add in [(r, o, False) for r, o in include] + [(r, False, True) for r in added]:
        rel = PurePosixPath(rel).as_posix().rstrip("/")
        reason = blocked_reason(rel, from_add=from_add)
        if reason:
            raise StageError(f"들이지 않는 경로다({reason}): {rel}")
        if not (repo_root / rel).exists() and not (repo_root / rel).is_symlink():
            if optional:
                missing_optional.append(rel)
                continue
            raise StageError(f"필수 항목이 없다: {rel}")
        for item in _files_under(repo_root, rel, from_add=from_add):
            files[item] = None
    return sorted(files), missing_optional


def snapshot_companions(repo_root: Path, files: list[str]) -> tuple[list[str], list[dict]]:
    """들이는 빌드 기록(data/snapshots/<id>/snapshot_build.json)이 가리키는 비교국 표를 함께 들인다.

    빌드 기록의 peer_group_files[].file_name을 data/reference/에서 찾아 sha256을 기록값과 대조한다. 이름이 정해진 모양
    (peer_group_<소문자·숫자·밑줄>.csv)이 아니거나, 파일이 없거나, sha256이 다르면 StageError다. 샌드박스 안 스냅샷 검증
    (단위 S3의 peer_group_sources)이 이 표를 찾기 때문이다(결정 기록 model-decision-mt5-sandbox ⑫).
    돌려주는 것: (더 들일 파일, 이미지 기록의 snapshots 항목 목록).
    """
    extra: list[str] = []
    snapshots: list[dict] = []
    for rel in files:
        parts = PurePosixPath(rel).parts
        if not (len(parts) == 4 and parts[:2] == ("data", "snapshots") and parts[3] == BUILD_RECORD):
            continue
        try:
            record = json.loads((repo_root / rel).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise StageError(f"빌드 기록을 읽지 못했다({type(exc).__name__}): {rel}") from None
        if not isinstance(record, dict) or record.get("snapshot_id") != parts[2]:
            raise StageError(f"빌드 기록의 snapshot_id가 폴더 이름과 다르다: {rel}")
        peers = []
        for entry in record.get("peer_group_files") or []:
            name = entry.get("file_name") if isinstance(entry, dict) else None
            expected = entry.get("sha256") if isinstance(entry, dict) else None
            if not isinstance(name, str) or not PEER_GROUP_NAME_RE.fullmatch(name):
                raise StageError(f"빌드 기록의 비교국 표 이름이 정해진 모양이 아니다: {rel}")
            peer = f"data/reference/{name}"
            if not (repo_root / peer).is_file() or (repo_root / peer).is_symlink():
                raise StageError(f"빌드 기록이 가리키는 비교국 표가 없다: {peer}")
            check_spelling(repo_root, peer)
            _check_regular(repo_root / peer, peer)
            if not isinstance(expected, str) or _sha256(repo_root / peer) != expected:
                raise StageError(f"비교국 표 sha256이 빌드 기록과 다르다: {peer}")
            extra.append(peer)
            peers.append({"file_name": name, "sha256": expected})
        normalized = record.get("normalized_sha256")
        snapshots.append({"snapshot_id": parts[2],
                          "normalized_sha256": normalized if isinstance(normalized, str) and SHA256_RE.fullmatch(normalized)
                          else None,
                          "build_record": rel, "peer_group_files": peers})
    return extra, snapshots


def code_version(repo_root: Path) -> dict:
    """스테이징한 작업 트리의 git 커밋과 추적 파일 변경 여부. git이 없거나 저장소가 아니면 값이 None이다.

    이미지 안에는 .git이 없으므로, 샌드박스 안 실행 결과의 code_version(자료 계약의 git 커밋 해시)을 이미지 내용과 잇는
    근거가 이 기록이다(결정 기록 model-decision-mt5-sandbox ⑧). dirty가 참인 이미지는 공식 실행에 쓰지 않는다.
    """
    def git(*args: str) -> str | None:
        try:
            done = subprocess.run(["git", "-C", str(repo_root), *args], capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError):
            return None
        return done.stdout if done.returncode == 0 else None

    head = git("rev-parse", "HEAD")
    status = git("status", "--porcelain", "--untracked-files=no")
    return {"git_commit": head.strip() if head else None,
            "dirty": None if status is None or head is None else bool(status.strip())}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stage(repo_root: Path, dest: Path, added: list[str]) -> dict:
    """빌드 맥락을 만들고 이미지 기록(dict)을 돌려준다. 실패하면 만든 폴더를 지운다."""
    repo_root = repo_root.resolve()
    target = dest.expanduser()
    if not target.is_absolute():
        target = Path.cwd() / target
    if target.exists() or target.is_symlink():
        raise StageError("--dest가 이미 있다. 아직 없는 폴더 이름을 준다")
    if not target.parent.is_dir():
        raise StageError("--dest의 부모 폴더가 없다")
    resolved = target.parent.resolve() / target.name
    if _inside(resolved, repo_root):
        raise StageError("--dest는 저장소 밖이어야 한다")
    if _inside(resolved, sealed_dir()):
        raise StageError("--dest는 봉인 폴더 밖이어야 한다")
    files, missing = collect(repo_root, read_include(repo_root / INCLUDE_FILE), added)
    extra, snapshots = snapshot_companions(repo_root, files)
    files = sorted(set(files) | set(extra))
    os.mkdir(resolved)
    try:
        app = resolved / "app"
        entries = []
        for rel in files:
            out = app / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(repo_root / rel, out)
            entries.append({"path": rel, "sha256": _sha256(out), "size": out.stat().st_size})
        (resolved / "image").mkdir()
        shutil.copyfile(repo_root / IMAGE_DIR / "Dockerfile", resolved / "Dockerfile")
        shutil.copyfile(repo_root / IMAGE_DIR / "tradesentry.sh", resolved / "image" / "tradesentry.sh")
        record = {
            "files": entries,
            "optional_missing": missing,
            "snapshots": snapshots,
            "code_version": code_version(repo_root),
            "dockerfile_sha256": _sha256(resolved / "Dockerfile"),
            "launcher_sha256": _sha256(resolved / "image" / "tradesentry.sh"),
            "include_sha256": _sha256(repo_root / INCLUDE_FILE),
        }
        payload = (json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        with open(app / MANIFEST_NAME, "xb") as handle:
            handle.write(payload)
        record["manifest_sha256"] = hashlib.sha256(payload).hexdigest()
        return record
    except BaseException:
        shutil.rmtree(resolved, ignore_errors=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scripts.stage_sandbox_image", allow_abbrev=False,
                                     description="샌드박스 이미지 빌드 맥락을 포함 목록대로 저장소 밖 빈 폴더에 만든다")
    parser.add_argument("--dest", required=True, help="만들 폴더(저장소·봉인 폴더 밖, 아직 없는 이름)")
    parser.add_argument("--add", action="append", default=[], help="더 들일 저장소 상대경로(여러 번)")
    args = parser.parse_args(argv)
    try:
        record = stage(REPO_ROOT, Path(args.dest), args.add)
    except StageError as exc:
        sys.stderr.write(f"오류: {exc}\n")
        return 2
    except Exception as exc:  # 예외 이름만 적는다(로컬 절대경로가 문장에 들 수 있다)
        sys.stderr.write(f"오류: 스테이징 중 예상 밖 오류({type(exc).__name__})\n")
        return 1
    total = sum(entry["size"] for entry in record["files"])
    print(f"staged files={len(record['files'])} bytes={total} optional_missing={len(record['optional_missing'])}")
    for rel in record["optional_missing"]:
        print(f"optional_missing {rel}")
    for snap in record["snapshots"]:
        peers = ",".join(entry["file_name"] for entry in snap["peer_group_files"]) or "-"
        print(f"snapshot {snap['snapshot_id']} normalized_sha256={snap['normalized_sha256']} peer_group_files={peers}")
    version = record["code_version"]
    print(f"git_commit={version['git_commit']} dirty={version['dirty']}")
    print(f"manifest_sha256={record['manifest_sha256']}")
    print(f"dockerfile_sha256={record['dockerfile_sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
