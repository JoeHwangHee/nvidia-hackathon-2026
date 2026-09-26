"""단위 E2의 보조 파일: 채점 대상 실행 샌드박스 안 run-case 호출과 내려받기(호스트 쪽).

단위 ID: E2(보조 파일. 새 단위가 아니다. 단위 표 docs/plan/UNITS.md E2 행의 파일 칸)
도메인명: evaluation_sealed_runner(단위 E2와 같다. 이 파일은 도메인 출력을 만들지 않는다)
소유: M
입력: 단위 E1 CaseCall(확보한 사례 실행명·빈 사례 실행 폴더·사례·모드·버전 키)
출력: 샌드박스에서 내려받은 실행 결과 기록(실행 쪽 키 21개)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.runlog, tradesentry.evaluation.batch_run

조립 작업 AS3이 CLI 배선(tradesentry.cli.dispatch)에 두었던 샌드박스 백엔드를 로드맵 MT7 두 번째 PR에서 이 파일로 옮겼다.
샌드박스 밖 실행기 E2(tradesentry.evaluation.sealed_runner)는 CLI를 import할 수 없고(경계 시험 8번), 평가 묶음 실행
tradesentry evaluate(dispatch)와 같은 절차로 사례를 샌드박스 안에서 돌려야 하기 때문이다. dispatch는 이 모듈을 import해
같은 이름을 그대로 쓴다(기존 시험 불변). 결정 기록 docs/tracking/decisions/의 AS3 기록(model-decision-as3-evaluate ③~⑥,
model-decision-as3-real-dev ⑤~⑥)이 절차의 정본이다.

하는 일
1. 사전 점검(sandbox_preflight): openshell 명령이 있는가, 샌드박스 이미지 기록(SANDBOX_IMAGE_MANIFEST)의 코드 커밋이 40자
   16진수이고 dirty가 거짓인가, 그 커밋이 호스트 code_version과 같은가. 실행 폴더를 만들기 전에 부른다.
2. 사례 실행 함수(SandboxCaseRunner, 단위 E1 CaseCall → 실행 쪽 키 21개): `openshell sandbox exec -n <샌드박스> --timeout <초>
   -- /opt/tradesentry/bin/tradesentry run-case --snapshot … --policy … --mode … --case … --run-name <call.run_id> [--sealed]`
   (사용자 결정 10(나). `--sealed`는 봉인 묶음 실행(sealed=True, 단위 E2)일 때만 붙는다. evaluate는 붙이지 않는다) → 받기 전 확인(`sh -c 'test -d …/<실행명> && ! test -L …/<실행명> && ! test -L /sandbox/outputs'`, MT5 결정 기록 ⑯
   T-DL4) → 같은 부모 아래 임시 폴더 .download-*로 `openshell sandbox download` → os.lstat으로 링크·특수 파일·하드링크·읽을 수
   없는 폴더·겹친 층·N6·N7 배치 밖 항목을 거부하고(링크만 os.unlink로 지우고 .quarantine-*로 격리) → 확보한 빈 사례 실행 폴더로
   os.rename → 실행 결과 기록(runlog_run_record-{시각}.json)을 읽어 돌려준다. 받지 못하면 SandboxError 하위 예외를 내고, 묶음
   (E1)이 그 사례를 FAILED 줄(CODE_ERROR, harness:{예외 이름})로 분모에 남긴다(MT5 결정 기록 ⑯).
3. 샌드박스에 넘길 값의 재검사(sandbox_request): 명령 인자로 나가는 값이라 단위 F1의 형식(스냅샷 ID·정책 이름·사례 인자·
   실행명의 좁은 문자 집합, 경로 모양 거부)을 여기서 다시 본다. 이 모듈은 tradesentry.cli를 import할 수 없어 같은 정규식을
   옮겨 적었다(시험 tests/units/E2가 단위 F1의 값과 대조한다).
4. 호스트 code_version(git 메타 파일에서 읽는 커밋 해시. 하위 프로세스 없음)과 이미지 기록의 커밋(image_code_version), 채점
   대상 실행 샌드박스 정책 파일의 sha256(policy_file_sha256). dispatch가 같은 이름으로 쓴다.

하위 프로세스는 openshell로 시작하는 목록 리터럴로만 부르고(셸 없음), 환경에서 키 변수와 봉인 폴더 변수를 뺀다(CHILD_ENV_DROP.
이름으로만 거르고 값은 읽지 않는다). 이 모듈은 .env를 읽지 않는다. 오류 문장에는 받은 값·경로를 넣지 않는다(자료 계약 §10.3 N13).
NAT 프로파일 파일 이름은 단위 I13(tradesentry.workflow.nat_wrap)의 값을 옮겨 적었다(workflow를 import할 수 없다. 시험이 대조한다).
"""
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from tradesentry.contract import types
from tradesentry.evaluation import batch_run
from tradesentry.runlog import trace as trace_log

SCORED_SANDBOX = "ts-scored"  # 개발 평가용 채점 대상 실행 샌드박스 이름(MT5 위반 시험표 artifacts/openshell/의 이름)
SANDBOX_CLI = "/opt/tradesentry/bin/tradesentry"  # 이미지 안 CLI 실행기(MT5 결정 기록 ⑧, configs/openshell/image/)
SANDBOX_OUTPUTS = "/sandbox/outputs"  # 샌드박스 쪽 실행 폴더의 부모(MT5 결정 기록 ③: exec 기본 작업 폴더 /sandbox)
SANDBOX_IMAGE_MANIFEST = "/opt/tradesentry/image_manifest.json"
SANDBOX_CHECK_TIMEOUT_S = 60  # 받기 전 확인·이미지 기록 읽기·내려받기 한 번의 제한 시간
SANDBOX_EXEC_MARGIN_S = 120  # 사례 실행 exec의 제한 시간 = 모델 설정의 사례당 wall time + 이 여유
SANDBOX_NAME_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,62}")  # 샌드박스 이름(scripts/openshell_violation_tests.py와 같다)
CHILD_ENV_DROP = ("NVIDIA_API_KEY", "NVIDIA_INFERENCE_API_KEY", "DATA_GO_KR_SERVICE_KEY", "TRADESENTRY_SEALED_DIR")
OPENSHELL_POLICY_FILE = Path("configs") / "openshell" / "policy.yaml"  # 채점 대상 실행 샌드박스 정책(MT5 결정 기록 ①)
RUN_CASE_RUN_NAME = batch_run.CASE_RUN_NAME  # 사례 실행의 실행 이름 run_case(N5)
RUN_RECORD_DOMAIN = "runlog_run_record"  # 실행 결과 기록을 만드는 단위 L2의 도메인명(UNITS.md §3.13, N4·N6)
RUN_RECORD_MAX_BYTES = 1 << 20  # 샌드박스에서 받은 실행 결과 기록을 읽는 크기 상한
NAT_DOMAIN = "workflow_nat_wrap"  # NAT 추적·프로파일 N7 폴더(단위 I13 DOMAIN)
PROFILE_FILES = ("all_requests_profiler_traces.json", "inference_optimization.json", "standardized_data_all.csv",
                 "workflow_profiling_metrics.json", "workflow_profiling_report.txt")  # 단위 I13 PROFILE_FILES
UNKNOWN_CODE_VERSION = "unknown"  # git 메타와 이미지 기록을 모두 읽을 수 없을 때의 code_version
IMAGE_MANIFEST = "image_manifest.json"  # 샌드박스 이미지 기록(앱 뿌리 바로 아래, MT5 결정 기록 ⑧)
IMAGE_MANIFEST_MAX_BYTES = 1 << 20
REPO_ROOT = Path(__file__).resolve().parents[3]
# 샌드박스 밖 실행기 E2의 명령(로드맵 MT7, 결정 기록 model-decision-mt7-sealed-runner). E2 파일 자체는 경계 시험 7번(문자열
# 상수 속 tradesentry 금지) 때문에 이 이름을 적을 수 없어 여기에 둔다. 재현 명령(reproduce_evaluate)에 쓴다.
SEALED_RUNNER_COMMAND = "python -m tradesentry.evaluation.sealed_runner"
SEALED_DIR_DEFAULT = (".tradesentry", "sealed")  # 봉인 폴더 기본값(홈 폴더 아래, 자료 계약 §10). 같은 까닭으로 여기에 둔다

# 단위 F1(tradesentry.cli.args)의 인자 형식(옮겨 적음. 시험이 대조한다). 값 전체가 맞아야 한다(fullmatch).
MAX_LENGTH = 64
SNAPSHOT_ID_RE = re.compile(r"[a-z][a-z0-9_]*")
POLICY_VERSION_RE = re.compile(r"[a-z][a-z0-9_]*(?:-[a-z0-9_]+|(?<=[0-9])\.[0-9]+)*")
CASE_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9_-]*[A-Za-z0-9])?")
RUN_NAME_RE = re.compile(r"[a-z][a-z0-9_]*-[0-9]{12}")
PATH_HINT_RE = re.compile(r"[\\/]|\.\.|^~")  # 경로 구분자, '..', '~'로 시작
COMMIT_RE = re.compile(r"[0-9a-f]{40}")


class WiringError(Exception):
    """배선이 기대한 형식이 아니다(CLI 종료 코드 4). 문장에는 값이나 경로를 넣지 않는다."""


class SandboxError(Exception):
    """샌드박스 백엔드가 사례 실행 기록을 받지 못했다. 묶음은 하위 클래스 이름을 사유로 FAILED 줄(원인 CODE_ERROR,
    detail harness:{이름})을 남긴다(MT5 결정 기록 ⑯: 분모에 남는 실패). 문장에는 값·경로를 넣지 않는다."""


class SandboxExecFailed(SandboxError):
    """openshell sandbox exec을 부르지 못했거나(openshell 없음·제한 시간 초과) 실행 폴더 없이 끝났다."""


class SandboxOutputMissing(SandboxError):
    """받기 전 확인(샌드박스 쪽 실행 폴더가 링크가 아닌 폴더인가)이 통과하지 않았다."""


class DownloadFailed(SandboxError):
    """openshell sandbox download가 0이 아닌 종료 코드로 끝났다."""


class DownloadRejected(SandboxError):
    """받은 내용에 심볼릭 링크나 일반 파일·폴더가 아닌 항목이 있거나, 한 겹 더 싸인 모양이다. 옮기지 않았다."""


class DownloadMoveConflict(SandboxError):
    """받는 곳(확보한 사례 실행 폴더)이 비어 있지 않거나, 옮길 이름이 이미 있다."""


class RunRecordMissing(SandboxError):
    """받은 실행 폴더에 실행 결과 기록 파일이 없거나 읽을 수 없다."""


# ----------------------------------------------------------------------------- openshell 하위 프로세스

def _child_env() -> dict:
    """openshell 하위 프로세스 환경: 키 변수와 봉인 폴더 변수를 뺀다(값을 읽지 않고 이름으로만 거른다)."""
    return {key: value for key, value in os.environ.items() if key not in CHILD_ENV_DROP}


def _openshell(argv: list, timeout: float):
    """openshell 하위 프로세스를 부른다. argv는 "openshell"로 시작하는 목록이다(셸을 쓰지 않는다). 부를 수 없거나 제한
    시간을 넘으면 None, 아니면 subprocess.CompletedProcess."""
    if not argv or argv[0] != "openshell":
        raise WiringError("openshell 하위 프로세스는 openshell로 시작하는 목록으로만 부른다")
    try:
        return subprocess.run(argv, capture_output=True, timeout=timeout, env=_child_env(), stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return None


def sandbox_preflight(sandbox: str, host_code_version: str, program: str = "tradesentry evaluate") -> str | None:
    """샌드박스 백엔드의 사전 점검(실행 폴더를 만들기 전). 문제가 없으면 None, 있으면 오류 문장. program은 문장에 적는
    부른 프로그램 이름이다.

    1) openshell 명령이 있는가 2) 이미지 기록(SANDBOX_IMAGE_MANIFEST)의 code_version.git_commit이 40자 16진수이고 dirty가
    거짓인가 3) 그 커밋이 호스트 code_version과 같은가(다르면 사례 기록의 code_version이 묶음 값과 달라 모든 줄이 실패한다).
    """
    if shutil.which("openshell") is None:
        return (f"오류: {program}의 샌드박스 백엔드가 openshell 명령을 찾지 못했다. {program}는 호스트에서 "
                "부르고, 사례는 채점 대상 실행 샌드박스 안에서 돈다.")
    done = _openshell(["openshell", "sandbox", "exec", "-n", sandbox, "--timeout", str(SANDBOX_CHECK_TIMEOUT_S), "--",
                       "cat", SANDBOX_IMAGE_MANIFEST], SANDBOX_CHECK_TIMEOUT_S + 30)
    try:
        doc = json.loads(done.stdout.decode("utf-8")) if done is not None and done.returncode == 0 else None
    except (UnicodeError, ValueError, RecursionError):
        doc = None
    version = doc.get("code_version") if isinstance(doc, dict) else None
    commit = version.get("git_commit") if isinstance(version, dict) else None
    if not isinstance(commit, str) or COMMIT_RE.fullmatch(commit) is None:
        return (f"오류: {program}가 샌드박스 {sandbox}의 이미지 기록에서 코드 커밋을 읽지 못했다"
                "(샌드박스가 없거나 이미지 기록이 없다).")
    if version.get("dirty") is not False:
        return ("오류: 샌드박스 이미지가 추적 파일을 고친 작업 트리에서 만들어졌거나(dirty) 그 여부를 모른다. 커밋한 "
                "코드로 이미지를 다시 만든다(MT5 결정 기록 ⑧).")
    if commit != host_code_version:
        return (f"오류: 샌드박스 이미지의 코드 커밋이 {program}를 부른 코드의 커밋과 다르다. 같은 커밋에서 이미지를 다시 "
                f"만들거나 그 커밋에서 {program}를 부른다.")
    return None


# ----------------------------------------------------------------------------- 내려받기 검사

def _scan_download(temp: Path, run_id: str) -> dict:
    """받은 임시 폴더를 링크를 따라가지 않고(os.lstat) 훑는다(MT5 결정 기록 ④ 4단계, AS3 두 번째 PR 보강).

    돌려주는 값: links(심볼릭 링크), others(일반 파일·폴더가 아닌 항목과 링크 수가 2 이상인 일반 파일(하드링크)),
    unreadable(읽을 수 없어 훑지 못한 폴더 수. os.walk의 onerror가 모은다), layered(내용이 {실행명} 폴더 하나로 한 겹 더
    싸여 있다), misplaced(최상위 항목이 N6 `{도메인명}-{시각}.{확장자}` 파일이나 N7 `{도메인명}-{시각}/` 폴더가 아니다.
    시각은 이 실행명의 시각). 하나라도 있으면 옮기지 않는다."""
    stamp = run_id.rsplit("-", 1)[1]
    file_name = re.compile(r"[a-z][a-z0-9_]*-" + stamp + r"\.[a-z0-9]+")
    folder_name = re.compile(r"[a-z][a-z0-9_]*-" + stamp)
    errors: list[OSError] = []
    found = {"links": [], "others": [], "unreadable": 0, "layered": False, "misplaced": 0}
    top = list(os.scandir(temp))
    found["layered"] = len(top) == 1 and top[0].name == run_id and top[0].is_dir(follow_symlinks=False)
    for entry in top:
        mode = os.lstat(entry.path).st_mode
        pattern = folder_name if stat.S_ISDIR(mode) else file_name
        if pattern.fullmatch(entry.name) is None or entry.name == run_id:
            found["misplaced"] += 1
    for folder, dirnames, filenames in os.walk(temp, followlinks=False, onerror=errors.append):
        for name in dirnames + filenames:
            path = Path(folder) / name
            info = os.lstat(path)
            if stat.S_ISLNK(info.st_mode):
                found["links"].append(path)
            elif stat.S_ISREG(info.st_mode):
                if info.st_nlink > 1:
                    found["others"].append(path)
            elif not stat.S_ISDIR(info.st_mode):
                found["others"].append(path)
    found["unreadable"] = len(errors)
    return found


# ----------------------------------------------------------------------------- 샌드박스에 넘길 값

@dataclass(frozen=True)
class SandboxRequest:
    """샌드박스 안 run-case에 명령 인자로 넘길 값(재검사를 지난 것)."""
    snapshot_id: str
    policy_version: str
    mode: str
    case: str
    run_name: str


def _shaped(value: str, pattern: re.Pattern) -> bool:
    return not PATH_HINT_RE.search(value) and len(value) <= MAX_LENGTH and pattern.fullmatch(value) is not None


def sandbox_request(call) -> SandboxRequest:
    """샌드박스 안 run-case에 넘길 값을 단위 F1과 같은 형식으로 다시 본다(명령 인자로 나가는 값이라). 틀리면 WiringError
    (묶음이 그 사례를 FAILED 줄로 남긴다). 문장에는 값을 넣지 않는다."""
    values = (call.versions.get("snapshot_id"), call.versions.get("policy_version"), call.mode,
              call.case.get("case_id"), call.run_id)
    if not all(isinstance(value, str) for value in values):
        raise WiringError("샌드박스에 넘길 값이 문자열이 아니다")
    snapshot_id, policy_version, mode, case_id, run_id = values
    if not (_shaped(snapshot_id, SNAPSHOT_ID_RE) and _shaped(policy_version, POLICY_VERSION_RE)
            and _shaped(case_id, CASE_RE) and _shaped(run_id, RUN_NAME_RE)):
        raise WiringError("샌드박스에 넘길 값이 CLI 인자 형식이 아니다")
    if mode not in types.MODES or run_id != f"{RUN_CASE_RUN_NAME}-{call.stamp}":
        raise WiringError("샌드박스에 넘길 모드나 사례 실행명이 형식이 아니다")
    return SandboxRequest(snapshot_id=snapshot_id, policy_version=policy_version, mode=mode, case=case_id,
                          run_name=run_id)


# ----------------------------------------------------------------------------- 사례 실행 함수

class SandboxCaseRunner:
    """샌드박스 백엔드의 사례 실행 함수(단위 E1 CaseCall → 실행 쪽 키 21개, AS3 결정 기록 ④). 절차는 머리 설명 2."""

    def __init__(self, sandbox: str = SCORED_SANDBOX, *, exec_timeout_s: int, sealed: bool = False):
        self.sandbox = sandbox
        self.exec_timeout_s = exec_timeout_s
        self.sealed = sealed  # 봉인 묶음 실행이면 샌드박스 안 run-case에 --sealed를 붙인다(단위 E2만 True. evaluate는 False)
        self.incidents: list[str] = []

    def __call__(self, call) -> dict:
        request = sandbox_request(call)
        remote = f"{SANDBOX_OUTPUTS}/{call.run_id}"
        argv = ["openshell", "sandbox", "exec", "-n", self.sandbox, "--timeout", str(self.exec_timeout_s),
                "--", SANDBOX_CLI, "run-case", "--snapshot", request.snapshot_id, "--policy",
                request.policy_version, "--mode", request.mode, "--case", request.case, "--run-name",
                request.run_name]
        if self.sealed:
            argv.append("--sealed")
        done = _openshell(argv, self.exec_timeout_s + 30)
        if done is None:
            raise SandboxExecFailed("openshell sandbox exec을 부르지 못했거나 제한 시간을 넘었다")
        check = _openshell(["openshell", "sandbox", "exec", "-n", self.sandbox, "--timeout",
                            str(SANDBOX_CHECK_TIMEOUT_S), "--", "sh", "-c",
                            f"test -d {remote} && ! test -L {remote} && ! test -L {SANDBOX_OUTPUTS}"],
                           SANDBOX_CHECK_TIMEOUT_S + 30)
        if check is None or check.returncode != 0:
            if done.returncode not in (0, 1):  # CLI 종료 코드 0(COMPLETED)·1(다른 상태)이면 실행 폴더는 있어야 한다
                raise SandboxExecFailed("샌드박스 안 run-case가 실행 폴더 없이 끝났다")
            raise SandboxOutputMissing("받기 전 확인이 통과하지 않았다")
        self.download(call, remote)
        return self.read_record(call)

    def scan_download(self, temp: Path, run_id: str) -> dict:
        """받은 임시 폴더 검사(_scan_download). 부르는 쪽(dispatch)이 시험 대역을 끼울 수 있게 메서드로 둔다."""
        return _scan_download(temp, run_id)

    def download(self, call, remote: str) -> None:
        """MT5 결정 기록 ④의 2~6단계. 받는 곳은 묶음이 확보한 빈 사례 실행 폴더(call.run_dir)다."""
        target = call.run_dir
        if target.is_symlink() or not target.is_dir() or any(target.iterdir()):
            raise DownloadMoveConflict("받는 곳이 확보한 빈 폴더가 아니다")
        temp = Path(tempfile.mkdtemp(prefix=".download-", dir=target.parent))
        got = _openshell(["openshell", "sandbox", "download", self.sandbox, remote, str(temp)],
                         SANDBOX_CHECK_TIMEOUT_S + 30)
        if got is None or got.returncode != 0:
            self._discard(temp)
            raise DownloadFailed("openshell sandbox download가 실패했다")
        try:
            found = self.scan_download(temp, call.run_id)
        except OSError:
            self._quarantine(temp, call.run_id, "훑는 중 입출력 오류")
            raise DownloadRejected("받은 내용을 훑지 못했다") from None
        if found["links"] or found["others"] or found["unreadable"] or found["layered"] or found["misplaced"]:
            for link in found["links"]:
                os.unlink(link)  # 링크 자체만 지운다(대상을 따라가지 않는다)
            self._quarantine(temp, call.run_id,
                             f"링크 {len(found['links'])}개·특수 항목(하드링크 포함) {len(found['others'])}개·읽을 수 "
                             f"없는 폴더 {found['unreadable']}개·겹친 층 {int(found['layered'])}·배치 밖 항목 "
                             f"{found['misplaced']}개")
            raise DownloadRejected("받은 내용에 링크·특수 항목·읽을 수 없는 폴더가 있거나 배치가 N6·N7이 아니다")
        for entry in sorted(os.listdir(temp)):
            if os.path.lexists(target / entry):
                self._quarantine(temp, call.run_id, "옮길 이름이 받는 곳에 이미 있다")
                raise DownloadMoveConflict("옮길 이름이 받는 곳에 이미 있다")
            os.rename(temp / entry, target / entry)
        os.rmdir(temp)
        self.check_nat_files(call)

    def _quarantine(self, temp: Path, run_id: str, what: str) -> None:
        """임시 폴더를 .quarantine-*로 이름을 바꿔 격리하고 사건 한 줄을 남긴다(outputs/에 .download-*를 남기지 않는다).
        문장에는 실행명·격리 폴더 이름·건수만 넣는다(로컬 절대경로 없음, N13)."""
        quarantine = temp.with_name(".quarantine-" + temp.name.lstrip(".").split("-", 1)[-1])
        try:
            os.rename(temp, quarantine)
        except OSError:
            self.incidents.append(f"{run_id}: {what}. 임시 폴더를 격리하지 못했다({temp.name})")
            return
        self.incidents.append(f"{run_id}: {what}. 거부하고 {quarantine.name}로 격리했다")

    def check_nat_files(self, call) -> None:
        """받은 뒤 확인(MT5 결정 기록 ③): NAT 폴더 workflow_nat_wrap-{시각}/에 프로파일 파일 5개가 모두 있는가. 없으면 사건
        한 줄을 남긴다(실행 기록은 그대로 쓴다. E4 profile_files_complete에도 드러난다)."""
        nat_dir = call.run_dir / f"{NAT_DOMAIN}-{call.stamp}"
        missing = [name for name in PROFILE_FILES
                   if not (nat_dir / name).is_file() or (nat_dir / name).is_symlink()]
        if missing:
            self.incidents.append(f"{call.run_id}: NAT 프로파일 파일 {len(missing)}개가 없다")

    @staticmethod
    def _discard(temp: Path) -> None:
        """실패한 받기의 임시 폴더를 지운다. 링크를 따라가지 않는다(shutil.rmtree는 링크를 지우기만 한다)."""
        shutil.rmtree(temp, ignore_errors=True)

    @staticmethod
    def read_record(call) -> dict:
        """받은 실행 결과 기록 runlog_run_record-{시각}.json을 읽는다(링크·크기 상한 확인)."""
        path = call.run_dir / f"{RUN_RECORD_DOMAIN}-{call.stamp}.json"
        if path.is_symlink() or not path.is_file():
            raise RunRecordMissing("받은 실행 폴더에 실행 결과 기록이 없다")
        with open(path, "rb") as handle:
            data = handle.read(RUN_RECORD_MAX_BYTES + 1)
        if len(data) > RUN_RECORD_MAX_BYTES:
            raise RunRecordMissing("실행 결과 기록이 크기 상한을 넘는다")
        try:
            record = trace_log.loads(data.decode("utf-8"))
        except (UnicodeError, ValueError, RecursionError):
            raise RunRecordMissing("실행 결과 기록이 JSON이 아니다") from None
        if not isinstance(record, dict):
            raise RunRecordMissing("실행 결과 기록이 객체가 아니다")
        return record


# ----------------------------------------------------------------------------- 코드 커밋과 정책 파일 해시

def policy_file_sha256(root: Path | None = None) -> str | None:
    """채점 대상 실행 샌드박스 정책 파일의 sha256(실행 조건 입력 파일 sandbox.policy_yaml_sha256). 없으면 None."""
    path = (REPO_ROOT if root is None else Path(root)) / OPENSHELL_POLICY_FILE
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def image_code_version(root: Path) -> str:
    """샌드박스 이미지 기록(<앱 뿌리>/image_manifest.json, 스테이징 도구 scripts/stage_sandbox_image.py가 쓴다)의 git 커밋.

    이미지 안에는 .git이 없으므로 샌드박스 안 실행의 code_version은 이 값으로 채운다(MT5 결정 기록 ⑧). 커밋이 40자 16진수이고
    추적 파일 변경 없음(dirty가 거짓)일 때만 그 커밋이고, 아니면 UNKNOWN_CODE_VERSION이다(고친 코드를 커밋 해시로 적지 않는다).
    """
    try:
        path = root / IMAGE_MANIFEST
        if path.is_symlink() or not path.is_file():
            return UNKNOWN_CODE_VERSION
        with open(path, "rb") as handle:
            data = handle.read(IMAGE_MANIFEST_MAX_BYTES + 1)
        doc = json.loads(data.decode("utf-8")) if len(data) <= IMAGE_MANIFEST_MAX_BYTES else None
    except (OSError, UnicodeError, ValueError, RecursionError):
        return UNKNOWN_CODE_VERSION
    version = doc.get("code_version") if isinstance(doc, dict) else None
    commit = version.get("git_commit") if isinstance(version, dict) else None
    if isinstance(commit, str) and COMMIT_RE.fullmatch(commit) and version.get("dirty") is False:
        return commit
    return UNKNOWN_CODE_VERSION


def code_version(root: Path | None = None) -> str:
    """실행한 코드의 git 커밋 해시(자료 계약 §8.1 code_version). 하위 프로세스 없이 git 메타 파일을 읽는다.

    작업 폴더(git worktree)의 .git 파일(gitdir)과 commondir, packed-refs를 따른다. git 메타를 읽을 수 없으면(샌드박스 이미지)
    이미지 기록의 커밋(image_code_version)을 쓴다. 둘 다 없거나 40자 16진수가 아니면 UNKNOWN_CODE_VERSION이다. 경로는
    돌려주지 않는다(N13). 작업 트리의 고치지 않은 변경은 표시하지 않는다.
    """
    root = REPO_ROOT if root is None else Path(root)
    found = _git_code_version(root)
    return found if found != UNKNOWN_CODE_VERSION else image_code_version(root)


def _git_code_version(root: Path) -> str:
    """git 메타 파일에서 읽은 커밋(code_version의 첫 출처)."""

    def checked(value: str) -> str:
        return value if COMMIT_RE.fullmatch(value) else UNKNOWN_CODE_VERSION

    try:
        git = root / ".git"
        gitdir = git
        if git.is_file():
            pointer = git.read_text(encoding="utf-8").strip()
            if not pointer.startswith("gitdir:"):
                return UNKNOWN_CODE_VERSION
            gitdir = Path(pointer[len("gitdir:"):].strip())
            gitdir = gitdir if gitdir.is_absolute() else (root / gitdir)
        head = (gitdir / "HEAD").read_text(encoding="utf-8").strip()
        if not head.startswith("ref: "):
            return checked(head)
        ref = head[len("ref: "):]
        common = gitdir
        if (gitdir / "commondir").is_file():
            pointer = Path((gitdir / "commondir").read_text(encoding="utf-8").strip())
            common = pointer if pointer.is_absolute() else gitdir / pointer
        for base in (gitdir, common):
            if (base / ref).is_file():
                return checked((base / ref).read_text(encoding="utf-8").strip())
        packed = common / "packed-refs"
        if packed.is_file():
            for line in packed.read_text(encoding="utf-8").splitlines():
                parts = line.split()
                if len(parts) == 2 and parts[1] == ref:
                    return checked(parts[0])
    except (OSError, UnicodeError):
        pass
    return UNKNOWN_CODE_VERSION
