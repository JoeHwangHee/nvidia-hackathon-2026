#!/usr/bin/env python3
"""요건 (c) 키 조회 시험(단위 F7의 샌드박스 안 탐침, 소유 M). 표준 라이브러리만, Python 3.8 이상.

샌드박스 사용자 권한으로 닿는 곳에 실제 키가 있는지 찾는다. 값은 어떤 경우에도 출력하지 않고 있음/없음·개수·경로만
JSON 한 줄로 낸다(docs/plan/DEV_PLAN.md §4.4 (c) 행). X1 key_check.py를 이어받아 MT5로 넘긴 한계를 고쳤다.

- 환경변수 전체: 변수 이름과 관계없이 실제 NVIDIA API 키 형식을 센다. NVIDIA_API_KEY·NVIDIA_INFERENCE_API_KEY는
  자리표시 값인지(openshell:resolve:env: 접두어) 본다. DATA_GO_KR_SERVICE_KEY는 고정 접두어가 없어 이름으로만 본다.
- .env 파일: 뿌리 경로들(인자, 기본 /)을 훑는다. 목록을 읽지 못한 폴더는 따로 센다(X1은 조용히 빠졌다).
- 하네스 설정 경로 후보와 정책에 적힌 파일(/run/nemoclaw의 시작 파일)은 폴더를 훑지 않고 직접 연다.
- 읽을 수 있는 /proc/<pid>/environ에서 실제 키 형식과 DATA_GO_KR_SERVICE_KEY 이름을 센다.
- 조상 프로세스의 실행 파일 목록(ancestry)을 낸다. 하네스(node)가 띄운 프로세스인지 가리는 데 쓴다.
일반 파일만 연다(FIFO·소켓에서 멈추지 않게). 키 접두어는 한 덩어리로 적지 않고 조각을 이어 만든다.

사용: python key_check.py [.env를 찾을 뿌리 경로 ...]
종료 코드: 실제 키 형식 0건이면 0, 1건 이상이면 1.
"""
import json
import os
import re
import stat
import sys

_PREFIX = "nv" + "api" + "-"
REAL_KEY_RE = re.compile(re.escape(_PREFIX) + r"[A-Za-z0-9_\-]{20,}")
PLACEHOLDER_PREFIX = "openshell:resolve:env:"
KEY_VARS = ("NVIDIA_API_KEY", "NVIDIA_INFERENCE_API_KEY")
SERVICE_KEY_NAME = "DATA_GO_KR_SERVICE_KEY"
HARNESS_PATHS = ("/sandbox/.nemoclaw", "/sandbox/.openclaw", "/sandbox/.config", "/sandbox/.hermes",
                 "/sandbox/.deepagents", "/root", "/etc/openshell", "/run/nemoclaw", "/run/openshell",
                 "/run/nemoclaw/managed-startup-runtime.env", "/run/nemoclaw/managed-startup-ca-bundle.pem")
SKIP_TOP = ("/proc", "/sys", "/dev", "/run")
MAX_FILE = 5 * 1024 * 1024
MAX_DEPTH = 6


def scan_text(text):
    return len(REAL_KEY_RE.findall(text))


def scan_file(path):
    """일반 파일의 실제 키 형식 개수. 열 수 없거나 일반 파일이 아니거나 크면 None."""
    try:
        info = os.lstat(path)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE:
            return None
        with open(path, "rb") as handle:
            return scan_text(handle.read().decode("utf-8", "replace"))
    except (OSError, ValueError):
        return None


def var_status(name):
    value = os.environ.get(name)
    if value is None:
        return "absent"
    if REAL_KEY_RE.search(value):
        return "REAL_KEY_FORMAT"
    if value.startswith(PLACEHOLDER_PREFIX):
        return "placeholder"
    return "present_other_format(len=%d)" % len(value)


def find_env_files(roots):
    found, unreadable_dirs = [], [0]

    def onerror(_error):
        unreadable_dirs[0] += 1

    for top in roots:
        for root, dirs, files in os.walk(top, onerror=onerror):
            if root in SKIP_TOP or any(root.startswith(skip + "/") for skip in SKIP_TOP):
                dirs[:] = []
                continue
            if root.count("/") >= MAX_DEPTH:
                dirs[:] = []
            for name in files:
                if name == ".env" or name.startswith(".env.") or name.endswith(".env"):
                    found.append(os.path.join(root, name))
    return found, unreadable_dirs[0]


def scan_harness():
    result, hits = {}, 0
    for base in HARNESS_PATHS:
        if not os.path.lexists(base):
            result[base] = "absent"
            continue
        if not os.path.isdir(base):
            count = scan_file(base)
            result[base] = {"file": True, "readable": count is not None, "real_key_hits": count or 0}
            hits += count or 0
            continue
        scanned = unreadable = found = 0
        unreadable_dirs = [0]

        def onerror(_error, counter=unreadable_dirs):
            counter[0] += 1

        for root, _dirs, files in os.walk(base, onerror=onerror):
            for name in files:
                count = scan_file(os.path.join(root, name))
                if count is None:
                    unreadable += 1
                else:
                    scanned += 1
                    found += count
        result[base] = {"files_scanned": scanned, "unreadable_or_large": unreadable,
                        "unreadable_dirs": unreadable_dirs[0], "real_key_hits": found}
        hits += found
    return result, hits


def scan_proc():
    readable = unreadable = hits = service_named = 0
    hit_pids = []
    try:
        entries = os.listdir("/proc")
    except OSError:
        entries = []
    for entry in entries:
        if not entry.isdigit():
            continue
        try:
            with open("/proc/%s/environ" % entry, "rb") as handle:
                data = handle.read().decode("utf-8", "replace")
        except OSError:
            unreadable += 1
            continue
        readable += 1
        count = scan_text(data)
        if count:
            hits += count
            hit_pids.append(int(entry))
        if (SERVICE_KEY_NAME + "=") in data:
            service_named += 1
    return {"proc_environ_readable": readable, "proc_environ_unreadable": unreadable,
            "proc_environ_real_key_hits": hits, "proc_environ_hit_pids": hit_pids,
            "proc_environ_with_service_key_name": service_named}, hits


def ancestry(limit=12):
    """이 프로세스부터 위로 조상의 실행 파일 경로(읽지 못하면 comm 이름)."""
    chain, pid = [], os.getpid()
    for _ in range(limit):
        try:
            exe = os.readlink("/proc/%d/exe" % pid)
        except OSError:
            try:
                with open("/proc/%d/comm" % pid) as handle:
                    exe = "comm:" + handle.read().strip()
            except OSError:
                exe = "?"
        chain.append(exe)
        try:
            with open("/proc/%d/stat" % pid) as handle:
                fields = handle.read().rsplit(")", 1)[1].split()
            pid = int(fields[1])
        except (OSError, IndexError, ValueError):
            break
        if pid <= 0:
            break
    return chain


def run_check(roots):
    report = {"checker": "tradesentry_key_check", "pid": os.getpid(), "uid": os.getuid(), "ppid": os.getppid(),
              "dotenv_roots": list(roots), "ancestry": ancestry()}
    total = 0
    env_hits = [name for name, value in os.environ.items() if REAL_KEY_RE.search(value or "")]
    report["env_real_key_vars"] = len(env_hits)
    total += len(env_hits)
    for name in KEY_VARS:
        report["env_" + name] = var_status(name)
    report["env_" + SERVICE_KEY_NAME] = "present" if SERVICE_KEY_NAME in os.environ else "absent"
    report["env_var_names_with_KEY_or_TOKEN"] = sorted(
        name for name in os.environ if "KEY" in name.upper() or "TOKEN" in name.upper())
    env_files, unreadable_dirs = find_env_files(roots)
    with_key = {}
    for path in env_files:
        count = scan_file(path)
        if count:
            with_key[path] = count
            total += count
    report["dotenv_files_found"] = env_files[:50]
    report["dotenv_files_with_real_key"] = with_key
    report["dotenv_walk_unreadable_dirs"] = unreadable_dirs
    harness, hits = scan_harness()
    report["harness_paths"] = harness
    total += hits
    proc, hits = scan_proc()
    report.update(proc)
    total += hits
    report["real_key_total"] = total
    report["verdict"] = "NO_REAL_KEY" if total == 0 else "REAL_KEY_FOUND"
    return report


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    report = run_check(tuple(argv) if argv else ("/",))
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["real_key_total"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
