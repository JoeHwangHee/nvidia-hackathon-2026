#!/usr/bin/env python3
"""위반 시험용 파일시스템 탐침(단위 F7의 샌드박스 안 탐침, 소유 M). 표준 라이브러리만, Python 3.8 이상.

    python fs_probe.py write <경로>               탐침 파일(새로 만드는 빈 파일)을 만들어 본다. 기존 파일은 고치지 않는다
    python fs_probe.py absent <뿌리> [...] [--name <파일 이름>]... [--skip <경로>]...   정답표·채점기·outputs 흔적을 훑는다
    python fs_probe.py sha256 <경로>              파일 sha256(이미지 포함 목록 기록 대조용)
    python fs_probe.py missing <경로>...          없는 경로 목록(정책 filesystem_policy 경로 가운데 이 샌드박스에 없는 것)

write는 이미 있으면 실패하는 방식(O_CREAT|O_EXCL)으로 만들고, 만들어지면 바로 지운다. 거부되면 errno 이름(EACCES:
정책 read_only 등 권한 거부, EROFS: 읽기 전용 마운트)을 적는다(docs/plan/DEV_PLAN.md §4.4 공식 채점용 최소 시험).
absent는 파일 내용을 열지 않고 이름·경로 조각만 본다. /sandbox/openshell_probes(이 탐침 폴더)와 --skip으로 준 경로
(lock에서 온 Python·가상환경처럼 저장소 자료가 아닌 폴더)는 건너뛴다.
결과는 JSON 한 줄이다. 종료 코드: write 0 만듦·1 거부(EACCES·EPERM·EROFS)·3 그 밖의 오류, absent 0 없음·1 있음,
sha256 0 읽음·3 오류, 2 인자 오류.
"""
import errno
import hashlib
import json
import os
import sys

DENIED = {errno.EACCES: "EACCES", errno.EPERM: "EPERM", errno.EROFS: "EROFS"}
SKIP = ("/sandbox/openshell_probes",)
FORBIDDEN_NAMES = ("oracle_ABC.json",)
FORBIDDEN_NAME_PARTS = ("oracle",)
FORBIDDEN_NAME_PREFIXES = ("scorer_results-", "scorer_claims-", "scorer_summary-", ".env")
# dev20 입력 하위 경로는 리허설 이미지에 있을 수 있어 경로로 막지 않는다. dev20 정답표는 D의 배치 기록에 적힌 파일
# 이름을 --name으로 준다.
FORBIDDEN_PATH_PARTS = ("/outputs/sealed", "/eval/scorer", "/artifacts/eval")


def _errno_name(exc):
    return errno.errorcode.get(exc.errno, str(exc.errno))


def probe_write(path):
    out = {"mode": "write", "path": path}
    try:
        handle = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except OSError as exc:
        out.update({"written": False, "errno": _errno_name(exc), "error": exc.strerror})
        return out, (1 if exc.errno in DENIED else 3)
    os.close(handle)
    os.unlink(path)
    out["written"] = True
    return out, 0


def probe_absent(roots, extra_names, skips=()):
    hits, unreadable, files = [], [0], 0

    def onerror(_error):
        unreadable[0] += 1

    for top in roots:
        for root, dirs, names in os.walk(top, onerror=onerror):
            if any(root == skip or root.startswith(skip + "/") for skip in SKIP + tuple(skips)):
                dirs[:] = []
                continue
            for name in dirs + names:
                path = os.path.join(root, name)
                lower = name.lower()
                if (name in FORBIDDEN_NAMES or name in extra_names or any(p in lower for p in FORBIDDEN_NAME_PARTS)
                        or name.startswith(FORBIDDEN_NAME_PREFIXES)
                        or any(part in path + "/" for part in FORBIDDEN_PATH_PARTS)):
                    hits.append(path)
            files += len(names)
    out = {"mode": "absent", "roots": list(roots), "skipped": sorted(skips), "entries_seen": files,
           "unreadable_dirs": unreadable[0],
           "hits": sorted(set(hits))[:20], "hit_count": len(set(hits))}
    return out, (1 if hits else 0)


def probe_sha256(path):
    out = {"mode": "sha256", "path": path}
    try:
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 16), b""):
                digest.update(chunk)
    except OSError as exc:
        out.update({"errno": _errno_name(exc), "error": exc.strerror})
        return out, 3
    out["sha256"] = digest.hexdigest()
    return out, 0


def probe_missing(paths):
    """os.path.lexists가 거짓인 경로 목록. 내용은 열지 않는다. 늘 종료 코드 0(정보용)."""
    missing = [path for path in paths if not os.path.lexists(path)]
    return {"mode": "missing", "checked": len(paths), "missing": missing}, 0


def main(argv):
    if len(argv) < 2:
        sys.stderr.write("usage: fs_probe.py write <path> | absent <root>... [--name <n>]... [--skip <p>]... "
                         "| sha256 <path>\n")
        return 2
    mode, rest = argv[0], argv[1:]
    if mode == "write" and len(rest) == 1:
        out, code = probe_write(rest[0])
    elif mode == "missing" and rest:
        out, code = probe_missing(rest)
    elif mode == "sha256" and len(rest) == 1:
        out, code = probe_sha256(rest[0])
    elif mode == "absent":
        roots, names, skips, index = [], [], [], 0
        while index < len(rest):
            if rest[index] in ("--name", "--skip") and index + 1 < len(rest):
                (names if rest[index] == "--name" else skips).append(rest[index + 1])
                index += 2
            else:
                roots.append(rest[index])
                index += 1
        if not roots:
            return main([])
        out, code = probe_absent(roots, set(names), skips)
    else:
        return main([])
    out["exit_code"] = code
    print(json.dumps(out, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
