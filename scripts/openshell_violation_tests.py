"""OpenShell 의도적 위반 시험(단위 F7, 도메인명·실행 이름 openshell_violation_tests, 소유 M, 보안 검토).

샌드박스 밖(호스트)에서 openshell 명령으로 채점 대상 실행 샌드박스와 NemoClaw 시연 샌드박스를 시험하고, 예측과 실측을
나란히 적은 시험표를 만든다(docs/plan/DEV_PLAN.md §4.4 요건 (a)~(e), 로드맵 MT5 행, MVP 체크리스트 4번).
저장소 루트에서 키 변수를 뺀 환경으로 부른다. 이 프로그램은 키를 쓰지 않는다.

    env -u NVIDIA_API_KEY -u DATA_GO_KR_SERVICE_KEY -u TRADESENTRY_SEALED_DIR \\
      uv run --locked python -m scripts.openshell_violation_tests run --scored <이름> [--demo <이름>] [...]
    uv run --locked python -m scripts.openshell_violation_tests compose-demo-policy --sandbox <시연 이름> --out <저장소 밖 파일>

run의 출력(자료 계약 §10.3 N5~N8, 이름은 단위 표 F7 행에 적을 값)
    outputs/openshell_violation_tests-{시각}/openshell_violation_tests-{시각}.md            시험표(예측·실측 대조)
    outputs/openshell_violation_tests-{시각}/openshell_violation_tests-{시각}/live_policy-{샌드박스}.yaml   라이브 정책
    outputs/openshell_violation_tests-{시각}/openshell_violation_tests-{시각}/audit_log-{샌드박스}.txt      감사 로그 발췌
  세 종류만 같은 이름의 폴더 artifacts/openshell/openshell_violation_tests-{시각}/로 증거 복사한다(오케스트레이터).
  실행명은 시작 전에 확보하고(N8), 파일은 이미 있으면 실패하는 방식으로 쓴다.

시험 행은 샌드박스마다 정해져 있다(ROWS_*). 네트워크 행은 허용 바이너리의 자손이 아닌 `openshell sandbox exec` 세션에서
시작한다(시연 샌드박스의 상속 행은 node가 띄운 자식). 행 사이에 간격을 두어 감사 로그 행을 시간 창으로 짝짓는다.
분류는 03 문서 §6.4(incomplete·access-denial·completed·command failed), 해석 규율은 §6.6을 따른다.
캡처한 출력 어디에든 NVIDIA API 키 모양 문자열이 있으면 파일을 하나도 쓰지 않고 종료 코드 3으로 끝낸다.
호스트 로컬 경로는 정책 해시 규칙과 같은 치환 규칙(scripts/openshell_common.py substitute_host_paths)으로 바꾼 뒤 쓴다.
종료 코드: 0 모든 판정 행 일치, 1 불일치 행이 있다(시험표는 씀), 2 인자·위치 오류, 3 키 모양 발견(확보한 실행 폴더는
빈 채로 남고 기록은 쓰지 않는다). 종료 코드 0은 불일치가 없다는 뜻일 뿐 MVP 체크리스트 4번 충족이 아니다. 충족은 표준 출력의
`mvp4=충족`(시험표 3절)으로 본다. 공식 채점용 종류(--scored-kind official)는 NIM 허용·L7 행이 없어 4번 판정이 "해당 없음"이다.
키 모양 검사는 NVIDIA API 키 접두어만 찾는다. DATA_GO_KR_SERVICE_KEY는 고정 모양이 없어 값으로 찾을 수 없다. 대신 탐침은 그
값을 내지 않는다(key_check는 변수 이름과 있음/없음·길이만 낸다).
샌드박스 이름은 파일 이름에 들어가므로 영문 소문자·숫자로 시작하고 영문 소문자·숫자·하이픈만 쓴 63자 이하만 받는다.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from scripts import openshell_common as oc
from scripts.stage_sandbox_image import code_version
from tradesentry.cli import dispatch

RUN_NAME = "openshell_violation_tests"
REPO_ROOT = Path(__file__).resolve().parents[1]
SCORED_POLICY = Path("configs") / "openshell" / "policy.yaml"
DEMO_NETWORK = Path("configs") / "openshell" / "policy_demo_network.yaml"
PROBE_LOCAL = Path("scripts") / "openshell_probes"
PROBE_DIR = "/sandbox/openshell_probes"
PROBES = ("key_check.py", "net_probe.py", "fs_probe.py")
KIND_SCORED, KIND_OFFICIAL, KIND_DEMO = "채점 대상 실행용", "공식 채점 대상 실행 전용", "시연용"

IMAGE_ROOT = "/opt/tradesentry"
IMAGE_PY = f"{IMAGE_ROOT}/python/current/bin/python3.12"
SYSTEM_PY = "/usr/bin/python3"
CURL = "/usr/bin/curl"
NODE = "/usr/local/bin/node"
NIM_URL = "https://" + oc.NVIDIA_INFERENCE_HOST + oc.CHAT_PATH
MODELS_URL = "https://" + oc.NVIDIA_INFERENCE_HOST + "/v1/models"
GITHUB_URL = "https://api.github.com/zen"
INFERENCE_LOCAL_URL = "https://inference.local/v1/models"
DECOY = "/srv/tradesentry_decoy/oracle_decoy.json"
WRITE_PROBE_DIR = f"{IMAGE_ROOT}/write_probe"
RO_CHILD_DIR = "/sandbox/read_only_probe"
IMAGE_MANIFEST = f"{IMAGE_ROOT}/image_manifest.json"
CURL_POST_NIM = [CURL, "--fail", "-sS", "-o", "/dev/null", "-w", "%{http_code}", "-X", "POST",
                 "-H", "Content-Type: application/json", "-d", "{}", NIM_URL]
# node가 띄운 자식으로 명령을 돌린다(조상 프로세스 상속 행). `--` 뒤 인자가 자식 명령이다.
NODE_SPAWN = ('const a=process.argv.slice(1);if(a[0]==="--")a.shift();'
              'const r=require("child_process").spawnSync(a[0],a.slice(1),{stdio:"inherit"});'
              'process.exit(r.status===null?1:r.status)')
DENIAL_TEXT = ("permission denied", "operation not permitted", "eacces", "eperm", "forbidden", "policy_denied",
               "tunnel connection failed", "connect tunnel failed")
# 허용 목록 항목의 경로 조각 가운데 하나라도 이 이름이면 정답·채점기·출력·봉인·저장소 .env 경로로 본다. 조각 단위로
# 본다. 글자 포함으로 보면 NemoClaw 정적 계층의 /run/nemoclaw/managed-startup-runtime.env가 저장소 .env로 잘못 걸린다
# (X1 시연 라이브 정책. 그 파일에 실제 키가 없는지는 키 조회 행이 직접 연다).
FORBIDDEN_ENTRY_PARTS = ("outputs", "artifacts", "sealed", "scorer", ".tradesentry")
LOG_TS_RE = re.compile(r"^\[(\d+(?:\.\d+)?)\]")
KEY_ENV_NAMES = ("NVIDIA_API_KEY", "NVIDIA_INFERENCE_API_KEY", "DATA_GO_KR_SERVICE_KEY", "TRADESENTRY_SEALED_DIR")
# 샌드박스 이름은 파일 이름(live_policy-{이름}.yaml, audit_log-{이름}.txt)이 되므로 좁은 형식만 받는다.
SANDBOX_NAME_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,62}")
SHA256_RE = re.compile(r"[0-9a-f]{64}")


# ---------------------------------------------------------------- openshell 호출

@dataclass
class Result:
    rc: int | None
    out: str
    err: str
    t0: float
    t1: float


class Runner:
    """openshell을 부른다. 키 변수와 봉인 폴더 변수는 자식 환경에서 뺀다. 시험은 이 클래스를 대역으로 바꾼다."""

    def __init__(self, program: str = "openshell"):
        self.program = program
        self.env = {k: v for k, v in os.environ.items() if k not in KEY_ENV_NAMES}

    def now(self) -> float:
        return time.time()

    def sleep(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)

    def run(self, args: list[str], timeout: float) -> Result:
        t0 = self.now()
        try:
            done = subprocess.run([self.program, *args], capture_output=True, text=True, timeout=timeout,
                                  env=self.env, errors="replace")
            return Result(done.returncode, done.stdout, done.stderr, t0, self.now())
        except subprocess.TimeoutExpired as exc:
            out = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            return Result(None, out, "host timeout", t0, self.now())
        except OSError as exc:
            return Result(127, "", f"{type(exc).__name__}", t0, self.now())


# ---------------------------------------------------------------- 시험 행

@dataclass
class Row:
    rid: str
    sandbox: str
    kind: str
    requirement: str
    title: str
    predict: str
    command: list[str] | None = None
    check: Callable[["Row", "Context"], tuple[bool | None, str]] | None = None
    log_kind: str | None = None
    log_host: str = ""
    denial_type: str | None = None
    info: bool = False
    rc: int | None = None
    http: str = "—"
    classification: str = "—"
    matched: bool | None = None
    note: str = ""
    log_refs: list[int] = field(default_factory=list)
    log_texts: list[str] = field(default_factory=list)
    t0: float = 0.0
    t1: float = 0.0
    out: str = ""
    err: str = ""
    data: dict = field(default_factory=dict)


@dataclass
class SandboxState:
    name: str
    kind: str
    header: dict = field(default_factory=dict)
    body: str = ""
    policy: dict | None = None
    policy_error: str = ""
    providers: list[str] = field(default_factory=list)
    provider_text: str = ""
    log_lines: list[str] = field(default_factory=list)
    log_warning: str = ""
    log_rc: int | None = None
    upload_failures: list[str] = field(default_factory=list)


@dataclass
class Context:
    args: argparse.Namespace
    stamp: str
    scored_committed: dict
    inference_text: str = ""
    inference_configured: bool | None = None
    version_text: str = ""
    harness_report: dict | None = None
    code: dict = field(default_factory=lambda: {"git_commit": None, "dirty": None})
    sandboxes: dict[str, SandboxState] = field(default_factory=dict)


def classify(rc: int | None, text: str) -> str:
    """03 문서 §6.4 분류."""
    if rc is None:
        return "incomplete"
    lower = text.lower()
    if any(word in lower for word in DENIAL_TEXT) or re.search(r"\b40[37]\b", lower):
        return "access-denial"
    return "completed" if rc == 0 else "command failed"


def probe_json(text: str) -> dict:
    for line in reversed(text.strip().splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                value = json.loads(line)
            except ValueError:
                continue
            if isinstance(value, dict):
                return value
    return {}


def http_of(row: Row) -> str:
    status = row.data.get("http_status")
    if isinstance(status, int):
        return str(status)
    token = row.out.strip()
    if re.fullmatch(r"\d{3}", token):
        return token
    return "—"


def _failed(row: Row) -> bool:
    return row.rc not in (0, None)


def check_deny_network(row: Row, ctx: Context) -> tuple[bool, str]:
    return _failed(row) and row.classification == "access-denial", ""


def check_deny_l7(row: Row, ctx: Context) -> tuple[bool, str]:
    return _failed(row) and row.http == "403" and row.classification == "access-denial", ""


def check_allow_nim(row: Row, ctx: Context) -> tuple[bool, str]:
    return row.rc == 0 and row.http == "200", ""


def check_not_success(row: Row, ctx: Context) -> tuple[bool, str]:
    ok = _failed(row) and not row.http.startswith("2")
    if not ok:
        return False, "inference.local에 닿았다: 작업 공간 추론 경로가 정책 밖에서 열려 요건 (b) 증거가 서지 않는다"
    if any("ALLOWED" in line for line in row.log_texts):
        return True, ("정책은 inference.local 연결을 허용했다(감사 로그 ALLOWED). 막은 것은 정책이 아니라 게이트웨이 추론 경로 "
                      "부재다(결정 기록 ⑮)")
    return True, "추론 경로 부재 또는 거부(감사 로그 행 없음)"


def check_deny_read(row: Row, ctx: Context) -> tuple[bool, str]:
    text = (row.out + row.err).lower()
    if "no such file" in text:
        return False, "파일 없음(ENOENT): 반입되지 않았다는 뜻일 뿐 정책 차단 증거가 아니다"
    return _failed(row) and "permission denied" in text, "EACCES" if "permission denied" in text else ""


def check_deny_write(row: Row, ctx: Context) -> tuple[bool, str]:
    code = row.data.get("errno", "")
    device = {"EACCES": "권한 거부(정책 read_only 또는 파일 권한)", "EPERM": "권한 거부(EPERM)",
              "EROFS": "읽기 전용 마운트"}.get(code, "")
    if row.data.get("written") is True:
        return False, "탐침 파일을 만들었다(쓰기 허용)"
    if code == "EACCES" and row.command and row.command[-1].startswith(WRITE_PROBE_DIR + "/"):
        device = "정책 read_only(탐침 폴더 권한은 0777이라 파일 권한은 거부하지 않는다)"
    return row.rc == 1 and code in ("EACCES", "EPERM", "EROFS"), f"{code} {device}".strip()


def check_info_write(row: Row, ctx: Context) -> tuple[None, str]:
    if row.data.get("written") is True:
        return None, "쓰기 허용(작업 폴더 read_write와 합쳐진 것으로 본다)"
    if row.data.get("errno"):
        return None, f"쓰기 거부({row.data['errno']})"
    return None, "판정 불가(탐침 출력 없음)"


def check_absent(row: Row, ctx: Context) -> tuple[bool, str]:
    count = row.data.get("hit_count")
    note = f"훑은 항목 {row.data.get('entries_seen', '?')}, 못 읽은 폴더 {row.data.get('unreadable_dirs', '?')}"
    if count:
        note += f", 걸린 경로 {count}: " + ", ".join(row.data.get("hits", []))
    return row.rc == 0 and count == 0, note


def check_key(row: Row, ctx: Context) -> tuple[bool, str]:
    data = row.data
    note = ", ".join(f"{name}={data.get('env_' + name, '?')}" for name in ("NVIDIA_API_KEY", "NVIDIA_INFERENCE_API_KEY",
                                                                            "DATA_GO_KR_SERVICE_KEY"))
    note += f", /proc environ 읽음 {data.get('proc_environ_readable', '?')}·못 읽음 {data.get('proc_environ_unreadable', '?')}"
    return row.rc == 0 and data.get("verdict") == "NO_REAL_KEY", note + " (UID 샌드박스 사용자 범위)"


def check_snapshot_verify(row: Row, ctx: Context) -> tuple[bool, str]:
    """샌드박스 안 스냅샷 검증(raw 대조 제외, 결정 기록 ⑫). raw 없이 도는 검사가 모두 통과하고 다시 계산한
    normalized_sha256이 빌드 기록값, 그리고 이미지 기록(image_manifest.json의 snapshots, 이미지 기록 대조 행이 스테이징 출력과
    이어 준 값)과 같아야 한다."""
    data = row.data
    failed = data.get("failed") or []
    value = data.get("normalized_sha256")
    same = bool(value) and value == data.get("recorded") and value == data.get("manifest")
    ok = row.rc == 0 and data.get("ok") is True and same and not failed
    note = f"normalized_sha256 {value or '?'}" + (
        "(빌드 기록값·이미지 기록값과 같다)" if same else
        f"(빌드 기록 {data.get('recorded') or '없음'}, 이미지 기록 {data.get('manifest') or '없음'})")
    if failed:
        note += ", 실패 검사: " + ", ".join(map(str, failed))
    return ok, note


def check_sha_info(row: Row, ctx: Context) -> tuple[bool | None, str]:
    """이미지 포함 목록 기록의 sha256. --image-manifest-sha256(스테이징 출력)을 주면 대조하고, 없으면 정보 행이다."""
    got = row.data.get("sha256")
    expected = getattr(ctx.args, "image_manifest_sha256", None)
    if not got:
        return (False if expected else None), "읽지 못했다"
    if expected:
        return got == expected, f"sha256 {got}" + ("" if got == expected else f", 스테이징 출력 {expected}")
    return None, f"sha256 {got}(대조값 없음)"


# ---- 호스트 점검(샌드박스 명령 없음)

def check_policy_match(row: Row, ctx: Context) -> tuple[bool, str]:
    state = ctx.sandboxes[row.sandbox]
    if state.policy is None:
        return False, f"라이브 정책을 읽지 못했다({state.policy_error})"
    live, committed = dedupe_fs(state.policy), dedupe_fs(ctx.scored_committed)
    if live == committed:
        return True, "커밋한 configs/openshell/policy.yaml과 구조가 같다(파일시스템 목록의 겹친 항목은 하나로 본다)"
    keys = sorted(k for k in set(live) | set(committed) if live.get(k) != committed.get(k))
    notes = []
    for kind in ("read_only", "read_write"):
        got = (live.get("filesystem_policy") or {}).get(kind) or []
        want = (committed.get("filesystem_policy") or {}).get(kind) or []
        extra, missing = [e for e in got if e not in want], [e for e in want if e not in got]
        if extra or missing:
            notes.append(f"{kind} 라이브에만 {extra or '없음'}, 커밋에만 {missing or '없음'}")
    return False, "다른 최상위 키: " + ", ".join(keys) + ("; " + "; ".join(notes) if notes else "")


def dedupe_fs(policy: dict) -> dict:
    """파일시스템 허용 목록의 똑같은 항목을 처음 것 하나로 줄인 사본(결정 기록 ⑬). 순서와 다른 키는 그대로다.

    커밋 정책이 OpenShell이 스스로 더하는 /var/log를 이미 적었는데 OpenShell이 또 더하면 같은 항목이 두 번 나올 수 있다
    [미확인]. 겹친 항목은 허용 범위를 바꾸지 않으므로 구조 비교에서만 하나로 본다. 해시(라이브 본문 바이트)는 줄이지 않는다.
    """
    out = dict(policy)
    fs = policy.get("filesystem_policy")
    if isinstance(fs, dict):
        fs = dict(fs)
        for kind in ("read_only", "read_write"):
            if isinstance(fs.get(kind), list):
                fs[kind] = list(dict.fromkeys(fs[kind]))
        out["filesystem_policy"] = fs
    return out


def check_requirement_b(row: Row, ctx: Context) -> tuple[bool, str]:
    state = ctx.sandboxes[row.sandbox]
    if state.policy is None:
        return False, f"라이브 정책을 읽지 못했다({state.policy_error})"
    ok, reasons = oc.judge_requirement_b(state.policy)
    blocks = ", ".join(sorted(oc.network_blocks(state.policy))) or "없음"
    return ok, f"남은 블록: {blocks}" + ("" if ok else "; 어긴 곳: " + "; ".join(reasons))


def check_allowlist(row: Row, ctx: Context) -> tuple[bool, str]:
    state = ctx.sandboxes[row.sandbox]
    if state.policy is None:
        return False, f"라이브 정책을 읽지 못했다({state.policy_error})"
    problems = [f"{kind}:{entry}" for kind, entry in oc.allowlist_entries(state.policy) if forbidden_entry(entry)]
    if row.kind != KIND_DEMO:
        problems += [f"미끼 파일을 덮는 항목 {hit}" for hit in oc.covering_entries(state.policy, DECOY)]
    return not problems, "; ".join(problems) or "정답·채점기·outputs·봉인·.env 경로 항목 없음"


def forbidden_entry(entry: str) -> bool:
    """허용 목록 항목이 정답·채점기·outputs·봉인 폴더·저장소 .env 경로 모양인가(경로 조각 단위)."""
    parts = [part.lower() for part in entry.split("/") if part]
    return any(part in FORBIDDEN_ENTRY_PARTS or "oracle" in part or part == ".env" or part.startswith(".env.")
               for part in parts)


def check_provider(row: Row, ctx: Context) -> tuple[bool, str]:
    state = ctx.sandboxes[row.sandbox]
    expected = ctx.args.scored_provider if row.kind != KIND_DEMO else ctx.args.demo_provider
    names = state.providers
    ok = names == [expected] if row.kind != KIND_DEMO else expected in names
    return ok, "붙은 provider: " + (", ".join(names) or "없음")


def check_inference_route(row: Row, ctx: Context) -> tuple[bool, str]:
    if ctx.inference_configured is None:
        return False, "조회 실패"
    return (not ctx.inference_configured,
            "작업 공간 추론 경로 없음" if not ctx.inference_configured else "추론 경로가 있다(inference.local이 정책 밖에서 열린다)")


def check_logs(row: Row, ctx: Context) -> tuple[bool, str]:
    state = ctx.sandboxes[row.sandbox]
    note = f"발췌 {len(state.log_lines)}행"
    if state.log_warning:
        note += f"; 수집 한계 경고: {state.log_warning}"
    loaded = sum("CONFIG:LOADED" in line for line in state.log_lines)
    # landlock compatibility best_effort는 커널이 지원하지 않으면 파일시스템 통제를 알리지 않고 뺀다. 그래서 시험 기간의
    # Landlock 적용 행(rules_applied·skipped)이 있고 skipped가 모두 0이어야 한다(MT5b 보안 검토 권고 6).
    skipped = [int(m.group(1)) for line in state.log_lines if "rules_applied" in line
               for m in [re.search(r"skipped:(\d+)", line)] if m]
    landlock_ok = bool(skipped) and not any(skipped)
    note += f"; 시험 기간 CONFIG:LOADED {loaded}행; Landlock 적용 행 {len(skipped)}개" + (
        ", 모두 skipped:0" if landlock_ok else (", skipped가 0이 아닌 행이 있다" if skipped else ", 없음"))
    return state.log_rc == 0 and landlock_ok, note


def check_harness_key(row: Row, ctx: Context) -> tuple[bool | None, str]:
    report = ctx.harness_report
    if report is None:
        return None, "미실시: 오케스트레이터가 하네스로 돌린 결과 파일을 --harness-key-check로 주면 채운다"
    chain = report.get("ancestry") or []
    spawned = any(str(exe).endswith("/node") for exe in chain[1:])
    ok = report.get("verdict") == "NO_REAL_KEY" and spawned
    return ok, (f"verdict {report.get('verdict')}, 조상 실행 파일 {' < '.join(map(str, chain[:5]))}"
                + ("" if spawned else " (조상에 node가 없다: 하네스가 띄운 프로세스인지 확인 못 함)"))


# ---------------------------------------------------------------- 행 정의

def _py(path: str, *args: str) -> list[str]:
    return [path, *args]


def _probe(python: str, probe: str, *args: str) -> list[str]:
    return [python, f"{PROBE_DIR}/{probe}", *args]


def _node_child(*command: str) -> list[str]:
    return [NODE, "-e", NODE_SPAWN, "--", *command]


# 샌드박스 안 스냅샷 검증 탐침. 단위 S3 verify_snapshot을 check_raw=False로 부른다(raw는 반입하지 않는다). CLI 명령
# snapshot-verify는 raw 대조를 늘 켜므로 샌드박스 안에서는 종료 1이 설계대로다(결정 기록 ⑫).
VERIFY_CODE = ("import json,sys\n"
               "from tradesentry.snapshot import verify\n"
               "r=verify.verify_snapshot(sys.argv[1],check_raw=False)\n"
               "m=json.load(open('/opt/tradesentry/image_manifest.json'))\n"
               "mv=[x.get('normalized_sha256') for x in m.get('snapshots',[]) if x.get('snapshot_id')==sys.argv[1]]\n"
               "bad=[c.get('name') for c in r.get('checks',[]) if c.get('ok') is False]\n"
               "print(json.dumps({'snapshot_id':sys.argv[1],'ok':r.get('ok'),'normalized_sha256':r.get('normalized_sha256'),"
               "'recorded':r.get('recorded_normalized_sha256'),'manifest':mv[0] if mv else None,'failed':bad}))\n"
               "sys.exit(0 if r.get('ok') and not bad else 1)\n")


def _verify(snapshot_id: str) -> list[str]:
    return ["env", f"PYTHONPATH={IMAGE_ROOT}/src", f"{IMAGE_ROOT}/.venv/bin/python", "-c", VERIFY_CODE, snapshot_id]


def scored_rows(name: str, kind: str, stamp: str, args: argparse.Namespace) -> list[Row]:
    absent_args = ["absent", IMAGE_ROOT, "/sandbox", "--skip", f"{IMAGE_ROOT}/python", "--skip", f"{IMAGE_ROOT}/.venv"]
    for extra in args.absent_name:
        absent_args += ["--name", extra]
    ro_write = args.ro_write_path or WRITE_PROBE_DIR
    rows = [
        Row("P1", name, kind, "(a)(b) 정책", "라이브 정책 = 커밋 정책(configs/openshell/policy.yaml)", "같다",
            check=check_policy_match),
        Row("P2", name, kind, "(b)", "요건 (b) 구조 판정(목적지·rules·method·path)", "충족", check=check_requirement_b),
        Row("P3", name, kind, "(a)", "허용 목록에 정답·채점기·outputs·봉인·.env 경로와 미끼 파일이 없다", "없음",
            check=check_allowlist),
        Row("P4", name, kind, "(c)", "붙은 provider(openshell sandbox provider list)", f"{args.scored_provider} 하나",
            check=check_provider),
        Row("P5", name, kind, "(b)", "게이트웨이 작업 공간 추론 경로(openshell inference get)", "없음",
            check=check_inference_route),
        Row("A2", name, kind, "(a)", "정답표·채점기 출력·outputs/sealed·.env 부재(샌드박스 안 이름 훑기)",
            "없음(종료 코드 0)", _probe(IMAGE_PY, "fs_probe.py", *absent_args), check_absent),
        Row("A3", name, kind, "(a)", ("봉인 입력 쓰기 거부" if kind == KIND_OFFICIAL else "읽기 전용 입력 쓰기 거부")
            + f"(탐침 파일, {ro_write})", "deny(read_only)",
            _probe(IMAGE_PY, "fs_probe.py", "write", f"{ro_write}/probe-{stamp}"), check_deny_write),
        Row("B1", name, kind, "(b) 비허용 호스트", "CLI 파이썬 → api.github.com:443 GET /zen", "deny(endpoint-miss)",
            _probe(IMAGE_PY, "net_probe.py", "GET", GITHUB_URL), check_deny_network, "host", "api.github.com", "host"),
        Row("C1", name, kind, "(c) 키 조회", "샌드박스 밖 실행기와 같은 exec 경로에서 키 조회(값 출력 없음)",
            "실제 키 0건(종료 코드 0)", _probe(IMAGE_PY, "key_check.py", "/"), check_key),
        Row("M1", name, kind, "기록", "이미지 포함 목록 기록(image_manifest.json) sha256", "스테이징 출력과 같다",
            _probe(IMAGE_PY, "fs_probe.py", "sha256", IMAGE_MANIFEST), check_sha_info,
            info=not args.image_manifest_sha256),
    ]
    for number, snapshot_id in enumerate(args.verify_snapshot or ["controlled_fixture_v0"], start=1):
        rows.append(Row(f"S{number}", name, kind, "(a) 입력 무결성",
                        f"스냅샷 {snapshot_id} 검증(raw 대조 제외, 단위 S3 check_raw=False)",
                        "통과, normalized_sha256 = 빌드 기록값", _verify(snapshot_id), check_snapshot_verify))
    if kind == KIND_OFFICIAL:
        return rows
    rows[6:6] = [
        Row("A1", name, kind, "(a) 정답 경로 읽기", f"미끼 파일 읽기(cat {DECOY}, 허용 목록·작업 폴더 밖, 파일 권한 0644)",
            "deny(허용 목록 밖, EACCES)", ["cat", DECOY], check_deny_read),
    ]
    rows += [
        Row("A4", name, kind, "(a) 리허설", f"작업 폴더 아래 read_only 자식 쓰기({RO_CHILD_DIR}, 탐침 파일)",
            "deny(모형) / allow 가능(Landlock 합집합, 추론)",
            _probe(IMAGE_PY, "fs_probe.py", "write", f"{RO_CHILD_DIR}/probe-{stamp}"), check_info_write, info=True),
        Row("B2", name, kind, "(b) 비허용 바이너리", "curl --fail → POST /v1/chat/completions", "deny(binary-miss)",
            list(CURL_POST_NIM), check_deny_network, "binary", oc.NVIDIA_INFERENCE_HOST, "binary"),
        Row("B3", name, kind, "(b) 비허용 바이너리", "시스템 파이썬 → POST /v1/chat/completions", "deny(binary-miss)",
            _probe(SYSTEM_PY, "net_probe.py", "POST", NIM_URL), check_deny_network, "binary",
            oc.NVIDIA_INFERENCE_HOST, "binary"),
        Row("B4", name, kind, "(b) L7 위반", "CLI 파이썬 → GET /v1/models(허용 목적지의 허용하지 않은 method·path)",
            "deny(L7 불일치, HTTP 403)", _probe(IMAGE_PY, "net_probe.py", "GET", MODELS_URL), check_deny_l7, "l7",
            oc.NVIDIA_INFERENCE_HOST, "l7"),
        Row("B5", name, kind, "(b) 차단 조건", "CLI 파이썬 → inference.local GET /v1/models(작업 공간 추론 경로)",
            "2xx 아님(경로 없음 503 또는 거부)", _probe(IMAGE_PY, "net_probe.py", "GET", INFERENCE_LOCAL_URL),
            check_not_success, "inference_local", "inference.local"),
        Row("N1", name, kind, "대조군(c)(d)", "CLI 파이썬 → POST /v1/chat/completions, 헤더에 자리표시 값(NVIDIA_API_KEY)",
            "allow(HTTP 200)", _probe(IMAGE_PY, "net_probe.py", "NIM", NIM_URL, "--key-env", "NVIDIA_API_KEY"),
            check_allow_nim, "nim", oc.NVIDIA_INFERENCE_HOST),
    ]
    return rows


def demo_rows(name: str, args: argparse.Namespace) -> list[Row]:
    kind = KIND_DEMO
    return [
        Row("DP1", name, kind, "(b)", "요건 (b) 구조 판정과 남은 블록(clawhub·openclaw_docs·npm_registry 등 없음)", "충족",
            check=check_requirement_b),
        Row("DP2", name, kind, "(a)", "허용 목록에 정답·채점기·outputs·봉인·.env 경로가 없다", "없음", check=check_allowlist),
        Row("DP3", name, kind, "(c)", "붙은 provider(openshell sandbox provider list)", f"{args.demo_provider} 포함",
            check=check_provider),
        Row("DA2", name, kind, "(a)", "정답표·채점기 출력·outputs/sealed·.env 부재(샌드박스 안 이름 훑기)",
            "없음(종료 코드 0)", _probe(SYSTEM_PY, "fs_probe.py", "absent", "/sandbox", "--skip",
                                      f"{args.demo_root}/python", "--skip", f"{args.demo_root}/.venv",
                                      *[item for extra in args.absent_name for item in ("--name", extra)]),
            check_absent),
        Row("DB1", name, kind, "(b) 비허용 바이너리", "node 자손이 아닌 curl --fail → POST /v1/chat/completions",
            "deny(binary-miss)", list(CURL_POST_NIM), check_deny_network, "binary", oc.NVIDIA_INFERENCE_HOST, "binary"),
        Row("DB2", name, kind, "(b) 비허용 바이너리", "node 자손이 아닌 시스템 파이썬 → POST /v1/chat/completions",
            "deny(binary-miss)", _probe(SYSTEM_PY, "net_probe.py", "POST", NIM_URL), check_deny_network, "binary",
            oc.NVIDIA_INFERENCE_HOST, "binary"),
        Row("DB3", name, kind, "(b) 비허용 호스트", "node가 띄운 curl → api.github.com:443(조상 상속으로도 목적지 밖)",
            "deny(endpoint-miss)", _node_child(CURL, "--fail", "-sS", "-o", "/dev/null", "-w", "%{http_code}", GITHUB_URL),
            check_deny_network, "host", "api.github.com", "host"),
        Row("DB4", name, kind, "(b) L7 위반", "node가 띄운 curl → GET /v1/models(L4는 상속으로 허용, L7 거부)",
            "deny(L7 불일치, HTTP 403)",
            _node_child(CURL, "--fail", "-sS", "-o", "/dev/null", "-w", "%{http_code}", MODELS_URL), check_deny_l7, "l7",
            oc.NVIDIA_INFERENCE_HOST, "l7"),
        Row("DP4", name, kind, "(b)", "게이트웨이 작업 공간 추론 경로(openshell inference get)", "없음",
            check=check_inference_route),
        Row("DB5", name, kind, "(b) 차단 조건", "node가 띄운 시스템 파이썬 → inference.local GET /v1/models(작업 공간 추론 경로)",
            "2xx 아님(경로 없음 503 또는 거부)", _node_child(SYSTEM_PY, f"{PROBE_DIR}/net_probe.py", "GET", INFERENCE_LOCAL_URL),
            check_not_success, "inference_local", "inference.local"),
        Row("DC1", name, kind, "(c) 키 조회", "exec 세션에서 키 조회(값 출력 없음)", "실제 키 0건(종료 코드 0)",
            _probe(SYSTEM_PY, "key_check.py", "/"), check_key),
        Row("DC2", name, kind, "(c) 키 조회", "하네스(OpenClaw)가 띄운 프로세스에서 키 조회(오케스트레이터 명령 결과)",
            "실제 키 0건, 조상에 node", check=check_harness_key),
        Row("DN1", name, kind, "대조군(c)(d)", "node가 띄운 시스템 파이썬 → POST /v1/chat/completions, 자리표시 값"
            "(NVIDIA_INFERENCE_API_KEY)", "allow(HTTP 200, 조상 상속)",
            _node_child(SYSTEM_PY, f"{PROBE_DIR}/net_probe.py", "NIM", NIM_URL, "--key-env", "NVIDIA_INFERENCE_API_KEY"),
            check_allow_nim, "nim", oc.NVIDIA_INFERENCE_HOST),
    ]


def log_row(name: str, kind: str, rid: str) -> Row:
    return Row(rid, name, kind, "(d)", "감사 로그 수집(openshell logs --since)", "종료 코드 0", check=check_logs)


# ---------------------------------------------------------------- 감사 로그 짝짓기

def binary_of(command: list[str] | None) -> str:
    """거부 행에 찍힐 실행 파일 경로의 앞부분. node가 띄운 자식이면 그 자식의 실행 파일이다."""
    if not command:
        return ""
    if command[:2] == [NODE, "-e"] and "--" in command:
        command = command[command.index("--") + 1:]
    return command[0]


def log_matches(kind: str, host: str, line: str, exe: str = "") -> bool:
    """감사 로그 행이 그 시험 행의 사건인가(X1 실측 행 형식, artifacts/openshell/violation_tests.md §3).

    비허용 바이너리 행은 실행 파일까지 맞춘다(시간 창이 겹치는 curl 행과 시스템 파이썬 행을 가른다). 시스템 파이썬은
    커널이 푼 실제 경로(/usr/bin/python3.12 등)로 찍히므로 앞부분으로 맞춘다.
    """
    if kind == "host":
        return "DENIED" in line and f"-> {host}:443" in line
    if kind == "binary":
        return ("DENIED" in line and f"-> {host}:443" in line and "binary '" in line
                and (not exe or f"binary '{exe}" in line))
    if kind == "l7":
        return "HTTP:GET" in line and "DENIED" in line and "/v1/models" in line
    if kind == "nim":
        # L7 채팅 경로 허용 행만 받는다. L4 `NET:OPEN ALLOWED -> host:443` 행은 바로 앞 L7 위반 행(GET /v1/models)도 남기므로
        # 시간 창이 겹치면 다른 행의 로그가 허용 증거로 붙는다(MT5b 평가 검토 1).
        return "HTTP:POST" in line and "ALLOWED" in line and f"{host}:443{oc.CHAT_PATH}" in line
    if kind == "inference_local":
        return "inference.local" in line
    return False


def attach_log_refs(rows: list[Row], lines: list[str], *, before: float = 2.0, after: float = 5.0) -> None:
    stamped = []
    for number, line in enumerate(lines, start=1):
        match = LOG_TS_RE.match(line)
        if match:
            stamped.append((number, float(match.group(1)), line))
    for row in rows:
        if not row.log_kind or row.command is None:
            continue
        hits = [(number, line) for number, ts, line in stamped
                if row.t0 - before <= ts <= row.t1 + after and log_matches(row.log_kind, row.log_host, line,
                                                                     binary_of(row.command))]
        row.log_refs = [number for number, _ in hits]
        row.log_texts = [line for _, line in hits]


# ---------------------------------------------------------------- 실행

def _texts(ctx: Context, rows: list[Row]) -> list[str]:
    texts = [ctx.inference_text, ctx.version_text]
    for state in ctx.sandboxes.values():
        texts += [state.body, state.provider_text, *state.log_lines, state.log_warning]
    for row in rows:
        texts += [row.out, row.err]
    return texts


def _parse_providers(text: str) -> list[str]:
    names = []
    for line in oc.strip_ansi(text).splitlines():
        cells = line.split()
        if cells and cells[0] not in ("NAME", "No", "no") and not line.startswith(" "):
            names.append(cells[0])
    return names


def _inference_configured(text: str) -> bool | None:
    plain = oc.strip_ansi(text)
    section = plain.split("System inference:", 1)[0]
    if "Inference:" not in section:
        return None
    return bool(re.search(r"^\s*Provider:\s*\S+", section, re.M))


def _harness_report(path: Path) -> dict | None:
    """하네스 결과 파일에서 key_check JSON(checker tradesentry_key_check)을 찾는다."""
    text = path.read_text(encoding="utf-8", errors="replace")
    found: list[dict] = []

    def visit(value) -> None:
        if isinstance(value, dict):
            if value.get("checker") == "tradesentry_key_check":
                found.append(value)
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, str) and "tradesentry_key_check" in value:
            start, end = value.find("{"), value.rfind("}")
            if 0 <= start < end:
                try:
                    visit(json.loads(value[start:end + 1]))
                except ValueError:
                    pass

    for chunk in [text, *text.splitlines()]:
        try:
            visit(json.loads(chunk))
        except ValueError:
            visit(chunk)
        if found:
            return found[0]
    return None


def collect_sandbox(runner: Runner, ctx: Context, state: SandboxState, rows: list[Row], timeout: float,
                    gap: float) -> None:
    got = runner.run(["policy", "get", state.name, "--full"], timeout)
    try:
        state.header, state.body = oc.split_policy_get(got.out)
        state.policy = oc.parse_yaml(state.body)
    except (oc.PolicyOutputError, oc.YamlSubsetError) as exc:
        state.policy_error = f"{type(exc).__name__}: {exc}" if got.rc == 0 else f"종료 코드 {got.rc}"
    got = runner.run(["sandbox", "provider", "list", state.name], timeout)
    state.provider_text = oc.strip_ansi(got.out)
    state.providers = _parse_providers(got.out) if got.rc == 0 else []
    got = runner.run(["sandbox", "exec", "-n", state.name, "--timeout", "60", "--", "mkdir", "-p", PROBE_DIR], timeout)
    if got.rc != 0:
        state.upload_failures.append("mkdir")
    for probe in PROBES:
        got = runner.run(["sandbox", "upload", state.name, (PROBE_LOCAL / probe).as_posix(), PROBE_DIR + "/"], timeout)
        if got.rc != 0:
            state.upload_failures.append(probe)
    first = runner.now()
    for row in rows:
        if row.command is None:
            continue
        got = runner.run(["sandbox", "exec", "-n", state.name, "--timeout", str(int(timeout)), "--", *row.command],
                         timeout + 30)
        row.rc, row.out, row.err, row.t0, row.t1 = got.rc, got.out, got.err, got.t0, got.t1
        row.data = probe_json(got.out)
        row.http = http_of(row)
        row.classification = classify(got.rc, got.out + "\n" + got.err)
        runner.sleep(gap)
    minutes = max(1, math.ceil((runner.now() - first) / 60) + 2)
    got = runner.run(["logs", state.name, "--since", f"{minutes}m", "-n", "5000"], timeout)
    state.log_rc = got.rc
    lines = oc.strip_ansi(got.out).splitlines()
    if lines and lines[0].lower().startswith("warning"):
        state.log_warning = lines.pop(0).strip()
    ran = [row for row in rows if row.command is not None and row.t0]
    start = min((row.t0 for row in ran), default=first) - 5
    end = max((row.t1 for row in ran), default=runner.now()) + 15
    state.log_lines = [line for line in lines
                       if (m := LOG_TS_RE.match(line)) and start <= float(m.group(1)) <= end]
    attach_log_refs(rows, state.log_lines)


def evaluate(ctx: Context, rows: list[Row]) -> dict:
    for row in rows:
        if row.check is not None:
            row.matched, row.note = row.check(row, ctx)
            if row.info:
                row.matched = None
    judged = [row for row in rows if row.kind != KIND_OFFICIAL]
    official = [row for row in rows if row.kind == KIND_OFFICIAL]
    nim = [row for row in judged if row.log_kind == "nim" and row.matched]
    blocked = {kind: [row.rid for row in judged if row.denial_type == kind and row.matched and row.log_refs]
               for kind in ("host", "binary", "l7")}
    nim_ids = [f"{row.sandbox}:{row.rid}" for row in nim]
    nim_source = ("openshell logs 허용 행" if any(row.log_refs for row in nim)
                  else "앱 기록(openshell logs 행 없음)" if nim else "없음")
    return {"nim": nim_ids, "nim_source": nim_source, "blocked": blocked,
            "mvp4": (bool(nim) and all(blocked.values())) if judged else None,
            "official": ([f"{row.sandbox}:{row.rid}" for row in official if row.matched is False] if official else None),
            "mismatch": [f"{row.sandbox}:{row.rid}" for row in rows if row.matched is False]}


def mvp4_word(verdict: dict) -> str:
    return {True: "충족", False: "미충족", None: "해당 없음"}[verdict["mvp4"]]


def _cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip() or "—"


def render(ctx: Context, rows: list[Row], verdict: dict, run_id: str, started: datetime, n7: str) -> str:
    args = ctx.args
    lines = [
        f"# OpenShell 위반 시험표 — {run_id}", "",
        f"- 실행명 `{run_id}`, 시작 {started.strftime('%Y-%m-%d %H:%M:%S')} KST. 만든 프로그램: "
        "`python -m scripts.openshell_violation_tests run`(단위 F7)",
        f"- OpenShell: `{_cell(ctx.version_text.splitlines()[0] if ctx.version_text else '조회 실패')}`",
        f"- 이 도구의 코드 판: git 커밋 `{ctx.code['git_commit']}`, 추적 파일 변경 {ctx.code['dirty']}",
        f"- 커밋 정책 파일 sha256: `{SCORED_POLICY.as_posix()}` `{oc.sha256_file(REPO_ROOT / SCORED_POLICY)}`, "
        f"`{DEMO_NETWORK.as_posix()}` `{oc.sha256_file(REPO_ROOT / DEMO_NETWORK)}`",
        f"- 이 실행 폴더의 파일: 시험표 `{run_id}.md`(이 파일), `{n7}/live_policy-{{샌드박스}}.yaml`(라이브 정책 조회 본문. "
        "첫 `---` 줄 뒤 본문을 줄 끝 LF·마지막 줄바꿈 하나로 맞추고 호스트 경로를 치환한 바이트이며 본문 sha256은 이 바이트의 "
        f"값), `{n7}/audit_log-{{샌드박스}}.txt`(시험 기간 감사 로그 발췌. 로그 근거 열의 행 번호는 이 파일의 행 번호)",
        "- 분류(03 문서 §6.4): 종료 상태가 정수가 아니면 incomplete, 거부 문구(Permission denied·EACCES·프록시 403·407 등)가 "
        "있으면 access-denial, 종료 코드 0이면 completed, 그 밖은 command failed. 이 분류는 시험표 전용이며 실행 상태와 다르다",
        "- 해석 규율(03 문서 §6.6): 일치는 시험한 그 행동의 예측만 지지한다. 명령 실패만으로는 거부한 장치를 알 수 없어 "
        "정책 조회와 감사 로그를 함께 둔다. 감사 로그는 크기가 정해진 버퍼에서 읽어 행이 빠질 수 있다",
        "- 키 값은 어디에도 적지 않았다. 키 조회 행은 있음/없음과 자리표시 여부만 적는다", "",
        "## 1. 샌드박스", "",
        "| 샌드박스 | 종류 | 라이브 정책 본문 파일 | 본문 sha256 | Version | Hash(OpenShell 보고) | Status | 요건 (b) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for state in ctx.sandboxes.values():
        judged = "—"
        if state.policy is not None:
            ok, _ = oc.judge_requirement_b(state.policy)
            judged = "충족" if ok else "미충족"
        body_hash = oc.sha256_text(state.body) if state.body else "—"
        file_name = f"live_policy-{state.name}.yaml" if state.body else f"없음({_cell(state.policy_error)})"
        lines.append(f"| `{state.name}` | {state.kind} | `{file_name}` | `{body_hash}` | {_cell(state.header.get('Version', '—'))} "
                     f"| `{_cell(state.header.get('Hash', '—'))}` | {_cell(state.header.get('Status', '—'))} | {judged} |")
    lines += ["", "### provider·추론 경로 조회", ""]
    for state in ctx.sandboxes.values():
        failed = f" 탐침 올리기 실패: {', '.join(state.upload_failures)}." if state.upload_failures else ""
        lines.append(f"- `{state.name}` `openshell sandbox provider list`: {', '.join(state.providers) or '없음'}.{failed}")
    configured = {None: "조회 실패", True: "있음", False: "없음"}[ctx.inference_configured]
    lines += [f"- 게이트웨이 작업 공간 추론 경로(`openshell inference get`): {configured}", "", "```text",
              *(ctx.inference_text.strip().splitlines() or ["(출력 없음)"]), "```", "",
              "## 2. 시험표", "",
              "| # | 샌드박스 | 요건 | 입력 | 예측 | 종료 코드 | HTTP | 분류 | 로그 근거 | 일치 | 비고 |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    for row in rows:
        command = " ".join(row.command) if row.command else "호스트 점검"
        if row.command and row.command[:2] == [NODE, "-e"]:
            command = "node가 띄운 자식: " + " ".join(row.command[4:])
        refs = ", ".join(map(str, row.log_refs)) if row.log_refs else ("로그 행 없음" if row.log_kind else "해당 없음")
        if row.log_refs:
            refs = f"`audit_log-{row.sandbox}.txt` {refs}행"
        mark = {True: "O", False: "X", None: "정보" if row.info else "—"}[row.matched]
        rc = "—" if row.command is None else ("정수 아님" if row.rc is None else str(row.rc))
        lines.append(f"| {row.rid} | `{row.sandbox}` | {_cell(row.requirement)} | {_cell(row.title)}: `{_cell(command)}` "
                     f"| {_cell(row.predict)} | {rc} | {_cell(row.http)} | {_cell(row.classification if row.command else '—')} "
                     f"| {_cell(refs)} | {mark} | {_cell(row.note)} |")
    blocked = verdict["blocked"]
    lines += ["", "## 3. 판정", "",
              f"- MVP 체크리스트 4번(NIM 허용 1건 + 네트워크 차단 3종, 종료 코드 + 감사 로그 행): {mvp4_word(verdict)}"
              + (" (공식 채점용 샌드박스만 시험했다. 공식 최소 행에는 NIM 허용·L7 행이 없다)" if verdict["mvp4"] is None else ""),
              f"  - NIM 허용: {', '.join(verdict['nim']) or '없음'}. 허용 증거 출처: {verdict['nim_source']}",
              f"  - 비허용 호스트: {', '.join(blocked['host']) or '없음'} / 비허용 바이너리: "
              f"{', '.join(blocked['binary']) or '없음'} / L7 위반: {', '.join(blocked['l7']) or '없음'}",
              f"- 불일치 행: {', '.join(verdict['mismatch']) or '없음'}",
              *([f"- 공식 채점용 최소 행(비허용 호스트·부재 확인·키 조회·봉인 입력 쓰기 거부와 정책·기록 점검): "
                 f"{'모두 일치' if not verdict['official'] else '불일치 ' + ', '.join(verdict['official'])}"]
                if verdict["official"] is not None else []),
              "- 정답 경로 읽기(A1)와 키 조회(C1·DC1·DC2)는 차단 3종에 세지 않지만 실행·기록한다. 파일시스템 거부는 감사 로그에 "
              "남지 않을 수 있어(X1) 허용 목록 점검(P3·DP2)과 함께 본다",
              f"- 이 시험표의 정책 본문 sha256은 조회한 때의 정책을 가리킬 뿐 실행 기간 내내 같은 정책이었다는 증거가 아니다. "
              "실행 중 재적용은 결정 기록(model-decision-mt5-sandbox ⑥)의 방법으로 따로 본다", ""]
    return "\n".join(lines)


def _at_repo_root() -> bool:
    return Path.cwd().resolve() == REPO_ROOT


def run(args: argparse.Namespace, runner: Runner) -> int:
    if not _at_repo_root():
        sys.stderr.write("오류: 저장소 루트에서 부른다(실행 폴더 outputs/는 현재 폴더 기준이다)\n")
        return 2
    if not args.scored and not args.demo:
        sys.stderr.write("오류: --scored나 --demo 가운데 하나는 준다\n")
        return 2
    for option, value in (("--scored", args.scored), ("--demo", args.demo)):
        if value is not None and not SANDBOX_NAME_RE.fullmatch(value):
            sys.stderr.write(f"오류: {option} 샌드박스 이름은 영문 소문자·숫자로 시작하고 영문 소문자·숫자·하이픈만 쓴다"
                             "(63자 이하)\n")
            return 2
    if args.scored and args.scored == args.demo:
        sys.stderr.write("오류: --scored와 --demo는 다른 샌드박스다\n")
        return 2
    if any(not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", value) for value in args.verify_snapshot):
        sys.stderr.write("오류: --verify-snapshot은 스냅샷 ID 형식이다\n")
        return 2
    if args.image_manifest_sha256 and not SHA256_RE.fullmatch(args.image_manifest_sha256):
        sys.stderr.write("오류: --image-manifest-sha256은 16진수 소문자 64자다\n")
        return 2
    harness = None
    if args.harness_key_check:
        path = Path(args.harness_key_check)
        if not path.is_file():
            sys.stderr.write("오류: --harness-key-check 파일이 없다\n")
            return 2
        harness = _harness_report(path)
    run_id, stamp, run_dir = dispatch.reserve_run_dir(RUN_NAME)
    started = datetime.strptime(stamp, dispatch.STAMP_FORMAT)
    committed = oc.parse_yaml((REPO_ROOT / SCORED_POLICY).read_text(encoding="utf-8"))
    ctx = Context(args=args, stamp=stamp, scored_committed=committed, harness_report=harness,
                  code=code_version(REPO_ROOT))
    version = runner.run(["--version"], args.exec_timeout)
    ctx.version_text = oc.strip_ansi(version.out).strip() if version.rc == 0 else ""
    got = runner.run(["inference", "get"], args.exec_timeout)
    ctx.inference_text = oc.strip_ansi(got.out)
    ctx.inference_configured = _inference_configured(got.out) if got.rc == 0 else None
    rows: list[Row] = []
    plan = []
    if args.scored:
        kind = KIND_OFFICIAL if args.scored_kind == "official" else KIND_SCORED
        plan.append((SandboxState(args.scored, kind), scored_rows(args.scored, kind, stamp, args) + [
            log_row(args.scored, kind, "D1")]))
    if args.demo:
        plan.append((SandboxState(args.demo, KIND_DEMO), demo_rows(args.demo, args) + [
            log_row(args.demo, KIND_DEMO, "DD1")]))
    for state, sandbox_rows in plan:
        ctx.sandboxes[state.name] = state
        collect_sandbox(runner, ctx, state, sandbox_rows, args.exec_timeout, args.row_gap)
        rows += sandbox_rows
    if any(oc.has_key_shape(text) for text in _texts(ctx, rows)) or (
            harness is not None and oc.has_key_shape(json.dumps(harness))):
        sys.stderr.write("오류: 캡처한 출력에 키 모양 문자열이 있다. 기록을 쓰지 않는다(파일 없음). 사용자에게 올린다\n")
        return 3
    verdict = evaluate(ctx, rows)
    sub = {"repo_root": REPO_ROOT, "home": Path.home(), "tmp_dir": Path(tempfile.gettempdir()),
           "sealed_dir": Path(os.path.abspath(os.path.expanduser(
               os.environ.get("TRADESENTRY_SEALED_DIR") or "~/.tradesentry/sealed/")))}
    n7_name = f"{RUN_NAME}-{stamp}"
    n7 = run_dir / n7_name
    os.mkdir(n7)
    masked = 0
    for state in ctx.sandboxes.values():
        if state.body:
            body, count = oc.substitute_host_paths(state.body, **sub)
            state.body = body
            masked += count
            _write(n7 / f"live_policy-{state.name}.yaml", body)
        log_text, count = oc.substitute_host_paths(
            "\n".join(([state.log_warning] if state.log_warning else []) + state.log_lines) + "\n", **sub)
        masked += count
        _write(n7 / f"audit_log-{state.name}.txt", log_text)
        if state.log_warning:  # 발췌 파일 첫 행이 경고이므로 행 번호를 한 칸 민다
            for row in rows:
                if row.sandbox == state.name:
                    row.log_refs = [number + 1 for number in row.log_refs]
    text, count = oc.substitute_host_paths(render(ctx, rows, verdict, run_id, started, n7_name), **sub)
    masked += count
    if masked:
        text += f"\n- 호스트 로컬 경로 모양 {masked}곳을 `{oc.LOCAL_PATH_MASK}`로 가렸다(경로 치환 규칙)\n"
    _write(run_dir / f"{RUN_NAME}-{stamp}.md", text)
    print(f"outputs/{run_id}/{RUN_NAME}-{stamp}.md")
    print(f"mvp4={mvp4_word(verdict)} mismatch={len(verdict['mismatch'])}")
    return 0 if not verdict["mismatch"] else 1


def _write(path: Path, text: str) -> None:
    with open(path, "xb") as handle:
        handle.write(text.encode("utf-8"))


def compose(args: argparse.Namespace, runner: Runner) -> int:
    """시연 샌드박스의 라이브 정책 정적 계층 + policy_demo_network.yaml의 network_policies → 저장소 밖 새 파일."""
    if not SANDBOX_NAME_RE.fullmatch(args.sandbox):
        sys.stderr.write("오류: --sandbox 샌드박스 이름 형식이 아니다(영문 소문자·숫자·하이픈, 63자 이하)\n")
        return 2
    out = Path(args.out).expanduser()
    out = (Path.cwd() / out) if not out.is_absolute() else out
    if out.exists() or not out.parent.is_dir():
        sys.stderr.write("오류: --out은 아직 없는 파일이고 부모 폴더가 있어야 한다\n")
        return 2
    target = out.parent.resolve() / out.name
    if target == REPO_ROOT or REPO_ROOT in target.parents:
        sys.stderr.write("오류: --out은 저장소 밖이어야 한다(라이브 정적 계층을 커밋하지 않는다)\n")
        return 2
    got = runner.run(["policy", "get", args.sandbox, "--full"], args.exec_timeout)
    if got.rc != 0:
        sys.stderr.write(f"오류: openshell policy get이 종료 코드 {got.rc}로 끝났다\n")
        return 1
    if oc.has_key_shape(got.out):
        sys.stderr.write("오류: 조회 출력에 키 모양 문자열이 있다. 파일을 쓰지 않는다. 사용자에게 올린다\n")
        return 3
    try:
        header, body = oc.split_policy_get(got.out)
        composed = oc.compose_network(body, (REPO_ROOT / DEMO_NETWORK).read_text(encoding="utf-8"))
        ok, reasons = oc.judge_requirement_b(oc.parse_yaml(composed))
    except (oc.PolicyOutputError, oc.YamlSubsetError) as exc:
        sys.stderr.write(f"오류: 합치지 못했다({type(exc).__name__}: {exc})\n")
        return 1
    _write(target, composed)
    print(f"live_version={header.get('Version', '?')} live_hash={header.get('Hash', '?')}")
    print(f"composed_sha256={oc.sha256_text(composed)} requirement_b={'충족' if ok else '미충족'}")
    for reason in reasons:
        print(f"violation {reason}")
    return 0 if ok else 1


def main(argv: list[str] | None = None, runner: Runner | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scripts.openshell_violation_tests", allow_abbrev=False)
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run", allow_abbrev=False, help="위반 시험을 돌리고 시험표를 쓴다")
    run_parser.add_argument("--scored", help="채점 대상 실행 샌드박스 이름")
    run_parser.add_argument("--scored-kind", choices=("dev", "official"), default="dev",
                            help="dev: 개발 평가용 전체 행, official: 공식 채점 대상 실행 전용 최소 행")
    run_parser.add_argument("--scored-provider", default="tradesentry-nvidia", help="채점 샌드박스에 붙은 provider 이름")
    run_parser.add_argument("--ro-write-path", help="쓰기 거부를 볼 샌드박스 안 폴더(기본: 이미지의 쓰기 탐침 폴더)")
    run_parser.add_argument("--absent-name", action="append", default=[], help="부재를 확인할 파일 이름(여러 번)")
    run_parser.add_argument("--verify-snapshot", action="append", default=[],
                            help="샌드박스 안에서 raw 대조 없이 검증할 스냅샷 ID(여러 번, 기본 controlled_fixture_v0)")
    run_parser.add_argument("--image-manifest-sha256",
                            help="스테이징 도구가 출력한 manifest_sha256(주면 M1 행을 대조 행으로 판정한다)")
    run_parser.add_argument("--demo", help="NemoClaw 시연 샌드박스 이름")
    run_parser.add_argument("--demo-provider", default="nvidia-prod", help="시연 샌드박스에 붙은 provider 이름")
    run_parser.add_argument("--demo-root", default="/sandbox/tradesentry", help="시연 샌드박스 안 CLI 묶음 위치")
    run_parser.add_argument("--harness-key-check", help="하네스가 띄운 키 조회 결과를 담은 파일(nemoclaw agent 출력)")
    run_parser.add_argument("--exec-timeout", type=float, default=120.0, help="명령 하나의 제한 시간(초)")
    run_parser.add_argument("--row-gap", type=float, default=1.0, help="시험 행 사이 간격(초, 로그 짝짓기용)")
    run_parser.add_argument("--openshell", default="openshell", help="openshell 실행 파일")
    compose_parser = sub.add_parser("compose-demo-policy", allow_abbrev=False,
                                    help="시연 샌드박스에 적용할 정책 본문을 저장소 밖 파일로 만든다")
    compose_parser.add_argument("--sandbox", required=True)
    compose_parser.add_argument("--out", required=True)
    compose_parser.add_argument("--exec-timeout", type=float, default=120.0)
    compose_parser.add_argument("--openshell", default="openshell")
    args = parser.parse_args(argv)
    runner = runner or Runner(args.openshell)
    if args.command == "run":
        return run(args, runner)
    return compose(args, runner)


if __name__ == "__main__":
    sys.exit(main())
