"""비밀값·로컬 경로 검사(공동 소유 도구 파일, 병렬 개발 규칙 §10.3, 로드맵 V1 행·MVP 체크리스트 9번).

저장소 루트에서 부른다. 표준 라이브러리만 쓰므로 시스템 python3로도 돈다.

    python3 scripts/secret_scan.py                      # 추적 파일 전체(git ls-files, 작업 폴더의 내용)
    python3 scripts/secret_scan.py origin/main..HEAD    # 그 커밋 범위의 추가 행만(병합 커밋은 first-parent)

찾는 것(패턴 문자열은 이 파일에만 둔다. 문서에는 적지 않는다):
    key        NVIDIA API 키 모양(접두어 뒤에 키 문자 20자 이상. scripts/openshell_common.py의 키 모양과 같다)
    svc_param  공공데이터포털 서비스키 요청 파라미터(파라미터 이름 뒤 `=`)
    user_home  사용자 홈 아래 절대경로(macOS 사용자 폴더, 리눅스 홈 폴더. URL 안의 같은 글자는 빼려고 앞 글자를 본다)
    tmp_dir    macOS 임시 폴더 경로(private 아래 임시 폴더, var/folders)
    tilde      홈 폴더 경로(물결표와 빗금으로 시작). 봉인 폴더 기본값(`~/.tradesentry/sealed/`) 하나만 예외다

빼는 규칙은 둘이고 좁다. 시험(tests/test_secret_scan.py)이 고정한다.
    1. 컨테이너 경로: `artifacts/openshell/`(OpenShell 증거)와 `spikes/x1/`(X1 샌드박스 안 시험 코드) 아래 파일에서,
       샌드박스 컨테이너 안 홈 폴더 두 개(시연 샌드박스의 Homebrew 폴더와 샌드박스 사용자 홈)만 뺀다. 같은 파일의 다른
       홈 경로와 다른 폴더의 같은 경로는 그대로 걸린다.
    2. 이력 문서 기준선: 저장소 루트의 이력 문서(docs/README.md §4, 고치지 않는 문서)에 이미 있는 행을 (파일, 행 sha256)
       짝으로만 뺀다. 같은 파일이라도 새 행이나 바뀐 행은 걸린다.

출력: 걸린 곳마다 `파일:줄 종류`만 낸다(행 내용은 내지 않는다). 범위 모드는 `커밋 파일 +행순번 종류`다.
종료 코드: 0 걸린 곳 없음, 1 걸린 곳 있음, 2 인자·git 오류.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

# 패턴은 조각을 이어 만든다(이 파일과 시험 파일이 스스로 걸리지 않게).
_KEY_PREFIX = "nv" + "api" + "-"
_SVC_PARAM = "service" + "Key"
PATTERNS = {
    "key": re.compile(re.escape(_KEY_PREFIX) + r"[A-Za-z0-9_\-]{20,}", re.I),
    "svc_param": re.compile(_SVC_PARAM + r"\s*=", re.I),
    "user_home": re.compile(r"(?<![\w.:/\-])/(?:" + "Us" + "ers" + "|" + "ho" + "me" + r")/[A-Za-z_]"),
    "tmp_dir": re.compile(r"(?<![\w.:/\-])/(?:" + "pri" + "vate/(?:tmp|var)" + "|" + "var/fol" + "ders" + r")/"),
    "tilde": re.compile(r"(?<![\w.~])" + "~" + "/" + r"(?!\.tradesentry/sealed/)"),
}
SECRET_KINDS = ("key", "svc_param")

# 빼는 규칙 1: 컨테이너 경로
CONTAINER_DIRS = ("artifacts/openshell/", "spikes/x1/")
CONTAINER_HOME_RE = re.compile(r"/" + "ho" + "me" + r"/(?:linuxbrew|sandbox)(?![\w\-])")

# 빼는 규칙 2: 이력 문서 기준선(파일, 행 sha256). 2026-09-25(금) main deb8128에서 이 검사로 찾은 행이다.
HISTORICAL_BASELINE = frozenset({
    ("03-openshell-policy-yaml-구조.md", "56e11940f41f220651453d2fc565b700bb6a80b900b1c251e254c5abb36909cf"),  # 34행
    ("03-openshell-policy-yaml-구조.md", "98c5d47a090bb637514279e04fa9dac29c6ec1b738e02a130c36847bd61f464c"),  # 290행
    ("CHATGPT_REVIEW_TRANSCRIPT.md", "a22552de8af2efa64f429d3e6b326e0f8fe583bc54683a6bcc82b3e888b23564"),  # 84행
    ("IDEA_LIFE_EMBEDDED_BRAINSTORM.md", "1045631d48205312d6a84e3791b7a55e7b00a7d2be3bd361ef8e0805019c3ad7"),  # 36행
    ("IDEA_REAL_WORLD_USE_CASES.md", "32c9811264aaa4fdced5b6066898838f1d0d9e520042fe432f94e0bc97ad5a1a"),  # 94행
    ("IDEA_REAL_WORLD_USE_CASES.md", "beca1e34c75cd66188d907ef31f0495539d603d939f8b85d300e5e08a7e54379"),  # 135행
})


def _line_sha(line: str) -> str:
    return hashlib.sha256(line.encode("utf-8")).hexdigest()


def is_container_home(path: str, line: str, match: "re.Match[str]") -> bool:
    """빼는 규칙 1. 걸린 자리가 컨테이너 폴더 아래 파일의 컨테이너 홈 경로면 참."""
    if not path.startswith(CONTAINER_DIRS):
        return False
    return CONTAINER_HOME_RE.match(line, match.start()) is not None


def scan_line(path: str, line: str, baseline: frozenset = HISTORICAL_BASELINE) -> List[str]:
    """한 행에서 걸린 종류 목록(겹치면 종류마다 한 번)."""
    kinds = []
    for kind, pat in PATTERNS.items():
        for m in pat.finditer(line):
            if kind == "user_home" and is_container_home(path, line, m):
                continue
            kinds.append(kind)
            break
    if kinds and "/" not in path and (path, _line_sha(line)) in baseline:
        return []
    return kinds


def scan_text(path: str, text: str, baseline: frozenset = HISTORICAL_BASELINE) -> List[Tuple[int, str]]:
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        for kind in scan_line(path, line, baseline):
            hits.append((i, kind))
    return hits


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(repo), capture_output=True)


def scan_tree(repo: Path, baseline: frozenset = HISTORICAL_BASELINE) -> Tuple[List[str], int]:
    """추적 파일 전체. UTF-8로 읽히지 않는 파일(이진 파일)은 건너뛴다. (걸린 곳, 읽은 파일 수)."""
    out = _git(repo, "ls-files", "-z")
    if out.returncode != 0:
        raise RuntimeError(out.stderr.decode("utf-8", "replace").strip())
    hits, n = [], 0
    for rel in out.stdout.decode("utf-8").split("\0"):
        if not rel:
            continue
        p = repo / rel
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        n += 1
        for lineno, kind in scan_text(rel, text, baseline):
            hits.append(f"{rel}:{lineno} {kind}")
    return hits, n


def scan_range(repo: Path, rng: str, baseline: frozenset = HISTORICAL_BASELINE) -> Tuple[List[str], int]:
    """커밋 범위의 추가 행. (걸린 곳, 추가 행 수)."""
    out = _git(repo, "-c", "core.quotePath=false", "log", "-p", "--diff-merges=first-parent", "--no-color", "--no-ext-diff",
               "--format=COMMIT %h", rng)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.decode("utf-8", "replace").strip())
    commit: Optional[str] = None
    fname = ""
    hits, added = [], 0
    for line in out.stdout.decode("utf-8", "replace").splitlines():
        if line.startswith("COMMIT "):
            commit = line[7:]
            continue
        if line.startswith("+++ "):
            fname = line[6:] if line.startswith("+++ b/") else line[4:]
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
            for kind in scan_line(fname, line[1:], baseline):
                hits.append(f"{commit} {fname} +{added} {kind}")
    return hits, added


def main(argv: Optional[Iterable[str]] = None, repo: Optional[Path] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) > 1 or (args and args[0].startswith("-")):
        print("사용: python3 scripts/secret_scan.py [커밋 범위]", file=sys.stderr)
        return 2
    root = repo or Path.cwd()
    try:
        if args:
            hits, count = scan_range(root, args[0])
            scope = f"범위 {args[0]}: 추가 행 {count}줄"
        else:
            hits, count = scan_tree(root)
            scope = f"추적 파일 {count}개"
    except RuntimeError as exc:
        print(f"git 오류: {exc}", file=sys.stderr)
        return 2
    for h in hits:
        print(h)
    print(f"{scope}, 걸린 곳 {len(hits)}")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
