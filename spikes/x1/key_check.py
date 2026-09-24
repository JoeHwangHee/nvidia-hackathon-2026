#!/usr/bin/env python3
"""X1 요건 (c) 키 조회 시험(샌드박스 안에서 실행, 표준 라이브러리만).

실제 키 값이 샌드박스 안 어디에 있는지 찾는다. 값은 어떤 경우에도 출력하지 않고,
있음/없음·개수·경로만 JSON 한 줄로 낸다.

- 환경변수 전체: 변수 이름과 관계없이 실제 NVIDIA API 키 형식이 있는지 본다.
- NVIDIA_API_KEY 이름의 변수: provider가 넣은 자리표시 값인지(알려진 접두어만 비교) 본다.
- DATA_GO_KR_SERVICE_KEY: 고정 접두어가 없어 변수 이름으로만 본다.
- .env 파일, 하네스 설정 경로 후보, 읽을 수 있는 /proc/<pid>/environ에서 실제 키 형식을 찾는다.

사용: python key_check.py [.env를 찾을 루트 경로 ...](기본 /)
종료 코드: 실제 키 형식 0건이면 0, 1건 이상이면 1.
키 접두어는 이 파일에 한 덩어리로 적지 않고 실행할 때 조각을 이어 만든다.
"""

import json
import os
import re
import stat
import sys

_PREFIX = "nv" + "api" + "-"
REAL_KEY_RE = re.compile(re.escape(_PREFIX) + r"[A-Za-z0-9_\-]{20,}")
PLACEHOLDER_PREFIXES = ("openshell:resolve:env:",)
HARNESS_PATHS = [
    "/sandbox/.nemoclaw",
    "/sandbox/.openclaw",
    "/sandbox/.config",
    "/sandbox/.hermes",
    "/sandbox/.deepagents",
    "/home/sandbox",
    "/root",
    "/etc/openshell",
    "/run/nemoclaw",
    "/run/openshell",
]
SKIP_TOP = {"/proc", "/sys", "/dev", "/run"}
MAX_FILE = 5 * 1024 * 1024


def scan_text(text):
    return len(REAL_KEY_RE.findall(text))


def scan_file(path):
    try:
        st = os.lstat(path)
        # 일반 파일만 연다(FIFO·소켓·장치 파일을 열면 멈출 수 있다).
        if not stat.S_ISREG(st.st_mode) or st.st_size > MAX_FILE:
            return None
        with open(path, "rb") as fh:
            return scan_text(fh.read().decode("utf-8", "replace"))
    except (OSError, ValueError):
        return None


def find_env_files(limit_depth=6, roots=("/",)):
    found = []
    for top in roots:
        for root, dirs, files in os.walk(top):
            if root in SKIP_TOP or any(root.startswith(s + "/") for s in SKIP_TOP):
                dirs[:] = []
                continue
            if root.count("/") >= limit_depth:
                dirs[:] = []
            for name in files:
                if name == ".env" or name.endswith(".env"):
                    found.append(os.path.join(root, name))
    return found


def run_check(roots=("/",), harness_paths=None, max_files=None):
    """검사 결과 dict를 돌려준다. 값은 담지 않는다."""
    report = {"checker": "x1_key_check", "pid": os.getpid(), "uid": os.getuid(),
              "ppid": os.getppid(), "dotenv_roots": list(roots)}
    real_total = 0

    # 1) 이 프로세스의 환경변수 전체
    env_hits = [k for k, v in os.environ.items() if REAL_KEY_RE.search(v or "")]
    report["env_real_key_vars"] = len(env_hits)
    real_total += len(env_hits)
    v = os.environ.get("NVIDIA_API_KEY")
    if v is None:
        report["env_NVIDIA_API_KEY"] = "absent"
    elif REAL_KEY_RE.search(v):
        report["env_NVIDIA_API_KEY"] = "REAL_KEY_FORMAT"
    elif v.startswith(PLACEHOLDER_PREFIXES):
        report["env_NVIDIA_API_KEY"] = "placeholder(openshell:resolve:env:*)"
    else:
        report["env_NVIDIA_API_KEY"] = "present_other_format(len=%d)" % len(v)
    report["env_DATA_GO_KR_SERVICE_KEY"] = "present" if "DATA_GO_KR_SERVICE_KEY" in os.environ else "absent"
    report["env_var_names_with_KEY_or_TOKEN"] = sorted(
        k for k in os.environ if ("KEY" in k.upper() or "TOKEN" in k.upper())
    )

    # 2) .env 파일
    env_files = find_env_files(roots=roots)
    env_file_hits = {}
    for p in env_files:
        n = scan_file(p)
        if n:
            env_file_hits[p] = n
            real_total += n
    report["dotenv_files_found"] = env_files[:50]
    report["dotenv_files_with_real_key"] = env_file_hits

    # 3) 하네스 설정 경로 후보
    harness = {}
    for base in (HARNESS_PATHS if harness_paths is None else harness_paths):
        if not os.path.exists(base):
            harness[base] = "absent"
            continue
        hits, scanned, unreadable = 0, 0, 0
        walk = [(os.path.dirname(base), [], [os.path.basename(base)])] if os.path.isfile(base) else os.walk(base)
        for root, dirs, files in walk:
            if max_files is not None and scanned + unreadable >= max_files:
                harness.setdefault("_truncated", []).append(base)
                break
            for name in files:
                n = scan_file(os.path.join(root, name))
                if n is None:
                    unreadable += 1
                else:
                    scanned += 1
                    hits += n
        harness[base] = {"files_scanned": scanned, "unreadable_or_large": unreadable, "real_key_hits": hits}
        real_total += hits
    report["harness_paths"] = harness

    # 4) /proc/<pid>/environ (같은 사용자 프로세스를 읽을 수 있는지)
    readable, unreadable, proc_hits, proc_hit_pids = 0, 0, 0, []
    try:
        proc_entries = os.listdir("/proc")
    except OSError:
        proc_entries = []
    for entry in proc_entries:
        if not entry.isdigit():
            continue
        path = "/proc/%s/environ" % entry
        try:
            with open(path, "rb") as fh:
                data = fh.read().decode("utf-8", "replace")
            readable += 1
            n = scan_text(data)
            if n:
                proc_hits += n
                proc_hit_pids.append(int(entry))
        except OSError:
            unreadable += 1
    report["proc_environ_readable"] = readable
    report["proc_environ_unreadable"] = unreadable
    report["proc_environ_real_key_hits"] = proc_hits
    report["proc_environ_hit_pids"] = proc_hit_pids
    real_total += proc_hits

    report["real_key_total"] = real_total
    report["verdict"] = "NO_REAL_KEY" if real_total == 0 else "REAL_KEY_FOUND"
    return report


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    roots = tuple(argv) if argv else ("/",)
    report = run_check(roots)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["real_key_total"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
