"""단위 F2 명령 배선.

단위 ID: F2
도메인명: cli_dispatch
소유: M
입력: 명령
출력: 조립체 1~4 호출
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.cli, tradesentry.snapshot, tradesentry.dal, tradesentry.metrics, tradesentry.policy, tradesentry.grouping, tradesentry.tools, tradesentry.workflow, tradesentry.reports, tradesentry.validator, tradesentry.runlog, tradesentry.evaluation.batch_run, tradesentry.evaluation.extract, tradesentry.evaluation.nat_eval

정본: docs/plan/UNITS.md §3.8. main은 설치 명령 tradesentry의 진입점이다(pyproject.toml [project.scripts]).

흐름
1. 인자를 단위 F1(args.parse)로 한 번만 검증한다. 처리 함수에는 검증을 거친, 고칠 수 없는 요청(args.Request)만 넘긴다.
2. 처리 함수 표 HANDLERS에서 명령의 처리 함수를 찾아 부르고 그 종료 코드를 돌려준다. 명령을 잇는 작업(AS1~AS3)은 자기
   명령의 항목만 바꾼다. 처리 함수는 args.Request 하나를 받아 종료 코드(정수)를 돌려준다.
3. 종료 코드 3(아직 구현되지 않음)은 항목이 아직 자리표시(_not_wired)인 명령에만 낸다. 이은 처리 함수 안에서 난 예외는
   NotImplementedError라도 3이 아니라 실패(1)다. 이은 명령의 3이 "돌리지 않은 실행"으로 읽혀 분모에서 빠지는 일을 막는다.

종료 코드
- 0 성공(도움말 포함), 1 실패(처리 함수가 알린 실패, 처리 중이나 인자 검증 중의 예상 밖 예외), 2 인자 오류(단위 F1,
  argparse), 3 아직 잇지 않은 명령, 4 배선 계약 위반, 130 중단(KeyboardInterrupt. Ctrl-C나 SIGINT 신호로 나는 예외.
  셸이 SIGINT로 끝난 프로그램에 주는 관례 값 128+2이고, 이 처리를 넣기 전에도 같은 값이었다).
- 배선 계약 위반(4): 처리 함수가 허용하는 종료 코드가 아닌 값을 돌려주거나 SystemExit로 끝난 경우, 조립체 출력이 배선이
  기대한 형식이 아닌 경우(WiringError). 허용하는 종료 코드는 0~255의 정수(bool 제외) 가운데 CLI 층이 쓰는 2·3·4·130을
  뺀 값이다. 256 이상은 프로세스 종료 코드에서 256으로 나눈 나머지가 되어 실패가 0(성공)으로 보일 수 있다. 처리 함수는
  보통 0(성공)이나 1(실패)을 돌려준다.
- 예상 밖 예외와 중단은 예외 이름만 적는다. 예외 문장과 traceback(호출 경로 기록)에는 로컬 절대경로가 들 수 있다(자료
  계약 docs/rules/DATA_CONTRACT_V1.md §10.3 N13). main이 진입점에서 모든 Exception과 KeyboardInterrupt를 받으므로 main
  밖으로 호출 경로 기록이 나가지 않는다. 오류 문장은 args.write_text로 쓴다(표준 오류가 한국어를 못 쓰는 인코딩이어도
  새 예외 없이 ASCII 역슬래시 표기로 쓰고, 정한 종료 코드를 지킨다).

출력(자료 계약 §10.3 N5·N6·N8·N13)
- 실행 폴더의 부모는 OUTPUT_PARENT 하나다. 현재 폴더 기준 outputs이며, 저장소 루트에서 부르면 저장소의 outputs/다.
  단위 안에 outputs 기본값을 따로 두지 않는다(S0 결정 ⑥). 샌드박스 안 CLI의 출력 위치는 로드맵 MT5의 두 번째 PR에서 정한다.
- 실행명 {실행 이름}-{yymmddhhmmss}는 실행을 시작하기 전에 reserve_run_dir로 확보한다(N8, 시각은 명시적 KST). 단위를
  부르기 전에 확보하므로 단위가 실패하면 빈 실행 폴더가 남는다. 그 실행명은 다시 쓰지 않는다.
- 출력 파일은 이미 있으면 실패하는 방식("xb")으로 쓴다. 표준 출력에는 outputs부터의 상대경로만 적는다.

스냅샷 명령(결정 D18: 배선은 로드맵 MT5가, 단위 S2·S3 구현은 로드맵 DT1이 맡는다)
- snapshot-build: 실행명을 확보한 뒤 --policy가 있으면 단위 K4(tradesentry.contract.policy_load.load_policy)로 정책 객체를
  읽고, 단위 S2의 build_snapshot(snapshot_id, out_dir=실행 폴더, stamp=시각, policy=정책 객체 또는 None)을 부른다. S2가
  실행 폴더에 파생 SQLite snapshot_build-{시각}.sqlite와 빌드 기록 snapshot_build-{시각}.json을 쓴다(빌드 기록은 정본
  옮기기 install_build와 출처 대조가 읽는다). 두 파일의 상대경로를 한 줄씩 적고 0으로 끝난다. 반환이 빌드 기록(dict)이
  아니거나 두 파일 가운데 하나라도 없으면 4다. 정책을 읽지 못하면(PolicyError) 1이고 S2를 부르지 않는다. 빌드가 실패하면
  (BuildError 등) 1이다. 둘 다 예외 이름만 적는다.
  - 스냅샷 원천은 S2의 기본값(data/snapshots/{snapshot_id}/의 manifest·raw·수집기 SQLite)이다.
  - 비교국 표 파일(peer_group_files)은 넘기지 않는다. 빌드의 peer_group 표와 빌드 기록의 peer_group_files는 빈다. 넘기는
    수단은 새 CLI 옵션(계획 경로·명령 표 변경)이 필요해 결정 D10(g1 동결과 최종 빌드의 순서)과 함께 정한다.
- snapshot-verify: 단위 S3 run({"snapshot_id"})의 출력(JSON 객체)을 outputs/snapshot_verify-{시각}/snapshot_verify-{시각}.json에
  쓴다. S3는 정본 빌드(data/snapshots/{snapshot_id}/snapshot_build.sqlite)와 그 옆 빌드 기록을 대조한다. 보고의 합격 표시
  ok가 참이면 0, 거짓이면 1이다. ok가 없거나 참·거짓 값이 아니면 합격으로 보지 않고 4로 끝난다. 개발 빌드(outputs 아래)를
  CLI로 검증하는 수단은 없다(S3의 build_file 입력을 잇지 않았고, 새 옵션도 만들지 않았다).
- 명령이 쓰지 않는 공통 옵션(snapshot-build의 --mode, snapshot-verify의 --policy·--mode. args.COMMAND_OPTIONS의 UNUSED)은
  요청에는 남지만 단위에는 넘기지 않는다.

평가 하네스는 모듈 단위로만 허용한다. 호스트 전용 샌드박스 밖 실행기(단위 E2, tradesentry.evaluation.sealed_runner)는
CLI가 부르지 않는다.
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Callable

from tradesentry.cli import args

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2
EXIT_NOT_IMPLEMENTED = 3
EXIT_WIRING = 4
EXIT_INTERRUPTED = 130
CLI_EXIT_CODES = frozenset({EXIT_USAGE, EXIT_NOT_IMPLEMENTED, EXIT_WIRING, EXIT_INTERRUPTED})  # 처리 함수가 돌려줄 수 없는 값

KST = timezone(timedelta(hours=9), "KST")
STAMP_FORMAT = "%y%m%d%H%M%S"
MAX_ATTEMPTS = 10
OUTPUT_PARENT = Path("outputs")
OUTPUT_LABEL = "outputs"  # 표준 출력에 적는 상대경로의 첫 이름
SEALED_NAME = "sealed"  # 봉인 묶음 실행의 부모 폴더 outputs/sealed/

# 명령 → 부를 조립체와 잇는 작업(docs/plan/UNITS.md §4 조립체 표).
ASSEMBLIES = {
    "snapshot-build": "조립체 1(스냅샷 빌드·검증)의 단위 S2. 배선은 로드맵 MT5, 단위 구현은 DT1·DT7이 맡는다",
    "snapshot-verify": "조립체 1(스냅샷 빌드·검증)의 단위 S3. 배선은 로드맵 MT5, 단위 구현은 DT1이 맡는다",
    "detect": "조립체 2(탐지). 조립 작업 AS1이 잇는다",
    "run-case": "조립체 3(사례 조사). 조립 작업 AS2가 잇는다",
    "evaluate": "조립체 4(평가 실행). 조립 작업 AS3이 잇는다",
}


class WiringError(Exception):
    """조립체 출력이 배선이 기대한 형식이 아니다(종료 코드 4). 문장에는 값이나 경로를 넣지 않는다."""


class RunNameError(Exception):
    """실행명을 확보하지 못했다."""


def _report(text: str) -> None:
    """표준 오류에 한 줄을 쓴다. 인코딩이 한국어를 못 쓰거나 흐름이 닫혀도 새 예외를 내지 않는다(args.write_text)."""
    args.write_text(sys.stderr, text + "\n")


def _emit(text: str) -> None:
    """표준 출력에 한 줄을 쓴다(outputs부터의 상대경로). 새 예외를 내지 않는다(args.write_text)."""
    args.write_text(sys.stdout, text + "\n")


def now_kst() -> datetime:
    """지금 시각(KST)."""
    return datetime.now(KST)


def _second(moment: datetime) -> datetime:
    return moment.astimezone(KST).replace(microsecond=0)


def _wait_until(target: datetime, clock: Callable[[], datetime], sleep: Callable[[float], None]) -> None:
    while True:
        remaining = (target - clock()).total_seconds()
        if remaining <= 0:
            return
        sleep(remaining)


def reserve_run_dir(run_name: str, *, clock: Callable[[], datetime] = now_kst,
                    sleep: Callable[[float], None] = time.sleep) -> tuple[str, str, Path]:
    """실행명을 확보하고 (실행명, 시각, 실행 폴더)를 돌려준다(자료 계약 §10.3 N8).

    OUTPUT_PARENT 아래에 {실행 이름}-{yymmddhhmmss} 폴더를 이미 있으면 실패하는 방식(os.mkdir)으로 만든다. 그 이름의 초가 될
    때까지 기다린 뒤 만들고, 만든 뒤 다른 부모 폴더(OUTPUT_PARENT/sealed)에 같은 이름이 있으면 방금 만든 빈 폴더를 지우고
    다음 초로 넘어간다. 만들기에 실패해도 다음 초로 넘어간다. 개발 전용 공통 실행기(tradesentry.units)의 같은 규칙을 CLI 쪽에
    다시 둔 것이다(CLI는 tradesentry.units를 import하지 않는다). 런타임의 실행명 확보(단위 L2)와는 조립 점검(AS4)에서 합칠
    후보다.
    """
    parent = OUTPUT_PARENT
    other = OUTPUT_PARENT / SEALED_NAME
    parent.mkdir(parents=True, exist_ok=True)
    target = _second(clock())
    for _ in range(MAX_ATTEMPTS):
        _wait_until(target, clock, sleep)
        stamp = target.strftime(STAMP_FORMAT)
        run_id = f"{run_name}-{stamp}"
        run_dir = parent / run_id
        try:
            os.mkdir(run_dir)
        except FileExistsError:
            target = max(target + timedelta(seconds=1), _second(clock()))
            continue
        if os.path.lexists(other / run_id):
            os.rmdir(run_dir)
            target = max(target + timedelta(seconds=1), _second(clock()))
            continue
        return run_id, stamp, run_dir
    raise RunNameError(f"{MAX_ATTEMPTS}번 시도해도 실행명 {run_name}-{{시각}}을 확보하지 못했다")


def _json_default(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"JSON으로 쓸 수 없는 값: {type(value).__name__}")


def write_output(run_dir: Path, run_id: str, domain: str, stamp: str, ext: str, value: object) -> str:
    """출력 값을 {도메인명}-{시각}.{확장자}로 쓰고 표준 출력에 적을 상대경로를 돌려준다.

    확장자는 json 하나다(JSON 값, Decimal은 글자 그대로의 문자열). 파일은 이미 있으면 실패하는 방식("xb")으로 쓴다.
    snapshot-build의 두 파일은 단위 S2가 직접 쓴다.
    """
    if ext != "json":
        raise WiringError(f"배선이 모르는 출력 확장자다({ext})")
    try:
        payload = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=_json_default)
                   + "\n").encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise WiringError(f"{domain} 출력을 JSON으로 쓸 수 없다({type(exc).__name__})") from None
    name = f"{domain}-{stamp}.{ext}"
    with open(run_dir / name, "xb") as handle:
        handle.write(payload)
    return f"{OUTPUT_LABEL}/{run_id}/{name}"


def snapshot_verify_input(request: args.Request) -> dict[str, object]:
    """단위 S3(스냅샷 검증)의 입력."""
    return {"snapshot_id": request.snapshot_id}


def _snapshot_build(request: args.Request) -> int:
    """snapshot-build: 실행명을 확보하고, 정책을 읽고(--policy가 있을 때), 단위 S2 build_snapshot으로 실행 폴더에 파생
    SQLite와 빌드 기록을 쓴다(위 "스냅샷 명령")."""
    # 명령을 부를 때만 import한다(도움말·인자 오류는 조립체를 불러오지 않는다). 모듈 속성으로 불러 시험 대역이 걸리게 한다.
    from tradesentry.contract import policy_load
    from tradesentry.snapshot import build

    run_id, stamp, run_dir = reserve_run_dir("snapshot_build")
    policy = None
    if request.policy_version is not None:
        try:
            policy = policy_load.load_policy(request.policy_version)
        except policy_load.PolicyError:
            _report("오류: tradesentry snapshot-build가 --policy의 정책을 읽지 못했다(PolicyError). "
                    "정책 버전 이름과 configs/의 정책 파일을 확인한다.")
            return EXIT_FAILED
    try:
        record = build.build_snapshot(request.snapshot_id, out_dir=run_dir, stamp=stamp, policy=policy)
    except build.BuildError:
        _report("오류: tradesentry snapshot-build가 스냅샷을 빌드하지 못했다(BuildError).")
        return EXIT_FAILED
    names = (f"snapshot_build-{stamp}.sqlite", f"snapshot_build-{stamp}.json")
    if not isinstance(record, dict) or not all((run_dir / name).is_file() for name in names):
        raise WiringError("단위 S2(build_snapshot)가 실행 폴더에 파생 SQLite와 빌드 기록을 모두 쓰지 않았다")
    for name in names:
        _emit(f"{OUTPUT_LABEL}/{run_id}/{name}")
    return EXIT_OK


def _snapshot_verify(request: args.Request) -> int:
    """snapshot-verify: 조립체 1의 단위 S3를 부르고 검증 보고를 실행 폴더에 쓴다. 합격 표시 ok로 종료 코드를 정한다."""
    from tradesentry.snapshot import verify  # 명령을 부를 때만 import한다

    run_id, stamp, run_dir = reserve_run_dir("snapshot_verify")
    report = verify.run(snapshot_verify_input(request))
    shown = write_output(run_dir, run_id, "snapshot_verify", stamp, "json", report)
    _emit(shown)
    verdict = report.get("ok") if isinstance(report, dict) else None
    if verdict is True:
        return EXIT_OK
    if verdict is False:
        _report(f"오류: 스냅샷 검증 불합격이다. 검증 보고: {shown}")
        return EXIT_FAILED
    raise WiringError("단위 S3(snapshot_verify)의 출력에 합격 표시 ok(참·거짓)가 없다")


def _not_wired(request: args.Request) -> int:
    """아직 조립체와 잇지 않은 명령의 자리표시 처리 함수. main은 이 함수를 부르지 않고 종료 코드 3으로 끝낸다."""
    raise NotImplementedError(f"tradesentry {request.command}는 아직 조립체와 잇지 않았다")


# 명령 → 처리 함수(검증된 요청을 받아 종료 코드를 돌려준다). 조립 작업이 명령마다 이 표의 자기 항목만 바꾼다.
HANDLERS: dict[str, Callable[[args.Request], int]] = {
    "snapshot-build": _snapshot_build,
    "snapshot-verify": _snapshot_verify,
    "detect": _not_wired,
    "run-case": _not_wired,
    "evaluate": _not_wired,
}


def _parse_exit_code(exc: SystemExit) -> int:
    """argparse가 낸 SystemExit의 종료 코드(도움말 0, 인자 오류 2)."""
    if exc.code is None:
        return EXIT_OK
    if type(exc.code) is int:
        return exc.code
    return EXIT_USAGE


def call_handler(request: args.Request) -> int:
    """검증된 요청을 처리 함수에 넘기고 종료 코드를 정한다(위 "종료 코드")."""
    command = request.command
    handler = HANDLERS[command]
    if handler is _not_wired:
        _report(f"오류: tradesentry {command}는 아직 구현되지 않았다. {ASSEMBLIES[command]}.")
        return EXIT_NOT_IMPLEMENTED
    try:
        code = handler(request)
    except WiringError as exc:
        _report(f"오류: tradesentry {command}의 배선 계약 위반이다. {exc}.")
        return EXIT_WIRING
    except SystemExit:
        _report(f"오류: tradesentry {command}의 처리 함수가 종료 코드를 돌려주지 않고 SystemExit로 끝났다.")
        return EXIT_WIRING
    except Exception as exc:  # 예외 이름만 적는다(N13)
        _report(f"오류: tradesentry {command} 처리 중 예상 밖 오류가 났다({type(exc).__name__}).")
        return EXIT_FAILED
    if type(code) is not int or not 0 <= code <= 255 or code in CLI_EXIT_CODES:
        shown = str(code) if type(code) is int else type(code).__name__
        _report(f"오류: tradesentry {command}의 처리 함수가 허용하지 않는 종료 코드({shown})를 돌려줬다. "
                "처리 함수는 0~255의 정수를 돌려주되 CLI 층이 쓰는 2·3·4·130은 쓰지 않는다.")
        return EXIT_WIRING
    return code


def main(argv: list[str] | None = None) -> int:
    """tradesentry <명령> 진입점. 종료 코드를 돌려준다(SystemExit를 내지 않는다).

    인자 검증과 처리 중에 난 KeyboardInterrupt(130)와 그 밖의 Exception(1)을 여기서 받아 예외 이름만 적는다. 그래서 main
    밖으로 호출 경로 기록(traceback)이 나가지 않는다(위 "종료 코드").
    """
    try:
        try:
            request = args.parse(argv)
        except SystemExit as exc:  # 도움말과 인자 오류. 알리는 문장은 argparse가 이미 썼다
            return _parse_exit_code(exc)
        return call_handler(request)
    except KeyboardInterrupt:
        _report("오류: tradesentry 실행이 중단됐다(KeyboardInterrupt).")
        return EXIT_INTERRUPTED
    except Exception as exc:  # 인자 검증·출력 중의 예상 밖 예외. 예외 이름만 적는다(N13)
        _report(f"오류: tradesentry 실행 중 예상 밖 오류가 났다({type(exc).__name__}).")
        return EXIT_FAILED


def run(inp: object) -> object:
    """진입 함수. 입력은 문자열 인자 목록(명령 이름부터), 출력은 {"exit_code": 종료 코드}다."""
    if not isinstance(inp, list) or not all(isinstance(item, str) for item in inp):
        raise TypeError("단위 F2의 입력은 문자열 인자 목록이다")
    return {"exit_code": main(list(inp))}
