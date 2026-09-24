"""샌드박스 이미지 빌드 맥락 스테이징 도구(단위 F5, 소유 M, 보안 검토). 표준 라이브러리만 쓴다.

포함 목록(configs/openshell/image/include.txt)과 --add로 명시한 저장소 경로만 저장소 밖 빈 폴더에 복사해, OpenShell이
`openshell sandbox create --from <그 폴더>`로 빌드할 맥락을 만든다. 저장소 루트나 eval/dev/를 통째로 올리지 않는다(개발
플랜 §4.3 "반입 목록"). .gitignore는 제외 장치가 아니므로 쓰지 않고, 들이면 안 되는 경로는 이 도구의 거부 규칙이 막는다.

    uv run --locked python -m scripts.stage_sandbox_image --dest <저장소 밖의 아직 없는 폴더> [--add <저장소 상대경로>]...

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
import shutil
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


class StageError(Exception):
    """거부 규칙·목적지·목록 오류. 문장에는 저장소 상대경로만 넣는다."""


def sealed_dir() -> Path:
    """봉인 폴더 위치(값만 셈한다. 그 폴더를 열거나 stat하지 않는다)."""
    return Path(os.path.abspath(os.path.expanduser(os.environ.get("TRADESENTRY_SEALED_DIR") or DEFAULT_SEALED_DIR)))


def _inside(path: Path, base: Path) -> bool:
    return path == base or base in path.parents


def blocked_reason(rel: str, *, from_add: bool) -> str | None:
    """저장소 상대경로(POSIX)가 거부 규칙에 걸리면 이유를, 아니면 None을 돌려준다."""
    parts = PurePosixPath(rel).parts
    if not parts or rel.startswith("/") or ".." in parts:
        return "저장소 상대경로가 아니다"
    name = parts[-1]
    if name.startswith(".env") or name.endswith(".env"):
        return ".env 파일"
    if BLOCKED_PARTS.intersection(parts):
        return "저장소 관리·가상환경 폴더"
    if parts[0] in BLOCKED_TOP:
        return f"{parts[0]}/ 아래"
    if "oracle" in name.lower() or "answer" in name.lower():
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


def _files_under(repo_root: Path, rel: str, *, from_add: bool) -> list[str]:
    """항목 하나를 파일 목록(저장소 상대경로)으로 펼친다. 거부 규칙·심볼릭 링크·저장소 밖이면 StageError."""
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
    print(f"manifest_sha256={record['manifest_sha256']}")
    print(f"dockerfile_sha256={record['dockerfile_sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
