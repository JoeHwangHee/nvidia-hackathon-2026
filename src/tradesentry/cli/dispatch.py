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

탐지 명령 detect(조립체 2: 단위 X1·X2·X4·P1·P2. 배선은 조립 작업 AS1, 결정 기록 model-decision-as1-detect)
- 순서: 실행명 확보(N8) → 단위 K4 load_policy(--policy의 정책 객체) → 단위 K3 open_snapshot(정본 빌드
  data/snapshots/{snapshot_id}/snapshot_build.sqlite, 읽기 전용) → 출처 종류 확인 → 계열·월마다 K3 조회를 지표 입력으로
  옮기고(아래 "어댑터") 단위 X1·X2를 부른다 → X1·X2의 exact_value(반올림 전 정확값, fractions.Fraction)로 단위 P1 입력 행을
  만든다 → P1 → 단위 P2 → P2 출력을 outputs/detect-{시각}/policy_case_build-{시각}.json에 쓰고 그 상대경로를 한 줄 적는다.
  metric 객체의 value(표시 자릿수로 반올림한 값)는 P1에 넘기지 않는다. 경계에서 발동 여부가 뒤집히기 때문이다(DT2 결정 ②,
  MT1 결정 ②).
- 출처 종류(source_kind)는 호출자가 아니라 스냅샷 메타에서 읽는다(MT1 결정 ⑭의 AS1 항목). 이 판은 합성 스냅샷
  (controlled)만 탐지한다. 그 밖(실자료 real)은 지표를 계산하거나 K3로 값을 읽기 전에 거부하고 1로 끝난다. 실자료는 분할
  기록의 정본 위치가 계획 경로 표에 올라 사용자 승인을 받은 뒤, AS1의 두 번째 PR이 지표·P1 앞에서 real_dev 계열로 좁혀
  잇는다(병렬 개발 규칙 §7.2의 5). 새 CLI 옵션은 두지 않는다.
- 계열은 수집 설정의 HS6 × 상대국이다(비교국 표의 계획 밖 국가는 대상이 아니다). 비교월 t는 기준월 t−12도 스냅샷 기간
  안인 달만이다. 지표 입력은 계열마다 두 달(t−12, t)씩 넘긴다.
- 어댑터(K3 월 값 → 지표 단위의 역할별 입력 행, DT2 결정 ①): 값이 있는 달(OBSERVED)은 행 하나, 무거래 확정 달
  (CONFIRMED_NO_TRADE)은 V·Q 칸이 빈 행 하나(근거 ID는 K3가 준 상태 행 전부), 빠진 달은 K3 missingness 항목마다 상태 행
  하나(근거 ID 하나)다. 전체국가(ALL) 분모는 K3가 중복을 뺀(행 규칙 6) 뒤 고른 HS10 행의 근거 ID를 K3 resolve로 풀어 HS10
  행으로 다시 만들고, 코드 목록과 금액 합이 K3 값과 같은지 본다(다르면 4).
- P1 입력 행에는 X1의 r_U 입력(V_0·Q_0·V_1·Q_1)에서 부모 HS6 행의 금액·중량을 옮긴다(네 값이 모두 정수일 때). 정책의
  min_amount·min_weight가 있을 때 P1이 읽는다.
- 출력은 P2 출력 그대로 한 파일이다({snapshot_id, dataset, policy_version, cases, data_quality}. 합성 스냅샷은 dataset이
  null). 도메인명은 그 출력을 만든 단위 P2의 policy_case_build다(N4·N6). P1 전체 발동표와 metric 객체는 쓰지 않는다.
- 종료 코드: 0 성공(사례가 없어도), 1 정책을 읽지 못함(PolicyError, 스냅샷을 열지 않는다)·스냅샷을 열지 못했거나 행 규칙에
  맞지 않음(SnapshotError)·실자료 스냅샷 거부·단위의 입력 오류(예상 밖 예외), 4 조립체 출력이 기대한 모양이 아님
  (WiringError). 오류 문장에는 받은 값(스냅샷 ID·정책 이름)과 스냅샷 안의 값을 넣지 않고 예외 이름만 적는다(N13, MT5 결정 ⑧).
- 쓰지 않는 공통 옵션 --mode는 요청에 남지만 단위에 넘기지 않는다.

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
    "detect": "조립체 2(탐지)의 단위 X1·X2·X4·P1·P2. 배선은 조립 작업 AS1이 맡는다",
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


# ------------------------------------------------------------------------------ detect(조립체 2, 조립 작업 AS1)
DETECT_RUN_NAME = "detect"  # 실행 이름(N5: 명령 이름의 하이픈을 밑줄로 바꾼 것)
DETECT_DOMAIN = "policy_case_build"  # 출력을 만드는 단위 P2의 도메인명(docs/plan/UNITS.md §3.4, N4·N6)
DETECT_SOURCE_KINDS = ("controlled",)  # 이 판에서 탐지하는 출처 종류(허용 목록). 실자료는 AS1의 두 번째 PR에서 잇는다
CASE_BUILD_KEYS = frozenset({"snapshot_id", "dataset", "policy_version", "cases", "data_quality"})  # 단위 P2 출력 키
DETECT_REFUSAL = ("오류: tradesentry detect는 지금 합성 스냅샷(source_kind가 controlled)만 탐지한다. 이 스냅샷은 합성 "
                  "스냅샷이 아니어서 지표를 계산하지 않고 끝냈다. 실자료 스냅샷은 분할 기록의 정본 위치가 사용자 승인을 받은 "
                  "뒤, 조립 작업 AS1의 두 번째 PR이 real_dev 계열로 좁혀 잇는다.")


def detect_pairs(months: tuple[str, ...] | list[str]) -> list[tuple[str, str]]:
    """스냅샷 기간의 달에서 (비교월 t, 기준월 t−12) 쌍. 기준월도 기간 안인 비교월만, 달 순서대로."""
    from tradesentry.policy import trigger

    present = set(months)
    return [(month, trigger.baseline_of(month)) for month in months if trigger.baseline_of(month) in present]


def detect_series(snap) -> list[tuple[str, str]]:
    """탐지할 계열 (HS6, 상대국): 수집 설정의 HS6 × 상대국. 비교국 표가 가리키는 계획 밖 국가는 넣지 않는다."""
    return [(hs6, partner) for hs6 in snap.hs6_codes for partner in snap.partners]


def _status_rows(value: dict) -> list[dict]:
    """빠진 달: K3 missingness 항목마다 상태 행 하나(V·Q 칸은 비고, 근거 ID는 그 상태 행 하나)."""
    entries = value["missingness"]
    if not entries:
        raise WiringError("단위 K3의 빠진 달 값에 missingness 항목이 없다")
    return [{"month": entry["month"], "hs_code": entry["hs_code"], "partner_code": entry["partner_code"],
             "flow": entry["flow"], "amount_usd": None, "net_weight_kg": None,
             "observation_status": entry["observation_status"], "evidence_ids": [entry["evidence_id"]]}
            for entry in entries]


def _no_trade_rows(value: dict) -> list[dict]:
    """무거래 확정 달: V·Q 칸이 빈 행 하나. 근거 ID는 K3가 준 상태 행 전부다(지표 단위가 V·Q를 0으로 본다, 자료 계약 §3.4)."""
    from tradesentry.contract import types

    return [{"month": value["month"], "partner_code": value["partner"], "flow": types.METRIC_FLOW, "amount_usd": None,
             "net_weight_kg": None, "observation_status": types.CONFIRMED_NO_TRADE,
             "evidence_ids": list(value["evidence_ids"])}]


def parent_rows(value: dict) -> list[dict]:
    """단위 K3 parent 월 값 하나 → 지표 단위 X1·X2의 parent 역할 행(DT2 결정 ①)."""
    from tradesentry.contract import types

    status = value["observation_status"]
    if status == types.OBSERVED:
        return [{"month": value["month"], "hs_code": value["hs6"], "partner_code": value["partner"],
                 "flow": types.METRIC_FLOW, "amount_usd": value["amount_usd"], "net_weight_kg": value["net_weight_kg"],
                 "observation_status": status, "evidence_ids": list(value["evidence_ids"])}]
    if status == types.CONFIRMED_NO_TRADE:
        return _no_trade_rows(value)
    return _status_rows(value)


def world_rows(snap, value: dict) -> list[dict]:
    """단위 K3 world 월 값 하나 → 지표 단위 X2의 world 역할 행(DT2 결정 ①).

    값이 있는 달은 K3가 중복을 빼고(행 규칙 6) 고른 ALL HS10 행의 근거 ID를 K3 resolve로 풀어 HS10 행으로 다시 만든다.
    다시 만든 행의 코드 목록과 금액 합이 K3 값과 다르면 배선 계약 위반(4)이다.
    """
    from tradesentry.contract import types

    status = value["observation_status"]
    if status == types.CONFIRMED_NO_TRADE:
        return _no_trade_rows(value)
    if status != types.OBSERVED:
        return _status_rows(value)
    rows = []
    for evidence_id in value["evidence_ids"]:
        found = snap.resolve(evidence_id)
        row = found.get("row")
        if found.get("resolved") is not True or not isinstance(row, dict):
            raise WiringError("단위 K3 world의 근거 ID가 스냅샷 행으로 풀리지 않는다")
        rows.append({"month": row["month"], "hs_code": row["hs_code"], "partner_code": row["partner_code"],
                     "flow": row["flow"], "amount_usd": row["amount_usd"], "net_weight_kg": row["net_weight_kg"],
                     "observation_status": row["observation_status"], "evidence_ids": [evidence_id]})
    amounts = [row["amount_usd"] for row in rows]
    if sorted(row["hs_code"] for row in rows) != list(value["hs10_codes"]) \
            or not all(type(amount) is int for amount in amounts) or sum(amounts) != value["amount_usd"]:
        raise WiringError("단위 K3 world의 근거 행으로 다시 만든 HS10 행이 K3의 코드 목록·금액 합과 다르다")
    return rows


def _pick_metric(output: object, symbol: str, unit: str) -> dict:
    """지표 단위 출력({"metrics": [...]})에서 기호가 symbol인 metric 객체 하나. 하나가 아니면 배선 계약 위반(4)이다."""
    metrics = output.get("metrics") if isinstance(output, dict) else None
    found = [m for m in metrics if isinstance(m, dict) and isinstance(m.get("inputs"), dict)
             and m["inputs"].get("metric") == symbol] if isinstance(metrics, list) else []
    if len(found) != 1:
        raise WiringError(f"단위 {unit}의 출력에 {symbol} 지표가 하나가 아니다")
    return found[0]


def detection_rows(snap) -> list[dict]:
    """계열·비교월마다 단위 X1·X2를 불러 단위 P1의 입력 행을 만든다.

    r_U·d_s는 X1·X2의 exact_value(반올림 전 정확값)다. 부모 HS6 행의 금액·중량(P1이 정책의 min_amount·min_weight에 쓴다)은
    X1 r_U 입력의 V_0·Q_0·V_1·Q_1에서 옮긴다(네 값이 모두 정수일 때만. 값이 없으면 r_U가 null이라 P1이 읽지 않는다).
    K3는 계열마다 parent_series, HS6마다 world_series를 한 번씩 부르고, ALL 행은 HS6·달마다 한 번만 다시 만든다.
    """
    from tradesentry.metrics import share, unit_value

    pairs = detect_pairs(snap.months)
    if not pairs:
        return []
    months = sorted({month for pair in pairs for month in pair})
    worlds: dict[str, dict[str, list[dict]]] = {}
    rows: list[dict] = []
    for hs6, partner in detect_series(snap):
        if hs6 not in worlds:
            worlds[hs6] = {value["month"]: world_rows(snap, value) for value in snap.world_series(hs6, months)}
        world = worlds[hs6]
        parent = {value["month"]: parent_rows(value) for value in snap.parent_series(hs6, partner, months)}
        for month, baseline in pairs:
            target = {"snapshot_id": snap.snapshot_id, "hs6": hs6, "partner": partner, "period": month,
                      "baseline_period": baseline}
            both = parent[baseline] + parent[month]
            r_u = _pick_metric(unit_value.run({**target, "parent": both}), "r_U", "X1")
            d_s = _pick_metric(share.run({**target, "parent": both, "world": world[baseline] + world[month]}), "d_s", "X2")
            row = {"hs6": hs6, "partner": partner, "month": month, "baseline_month": baseline,
                   "r_U": unit_value.exact_value(r_u), "d_s": share.exact_value(d_s)}
            given = r_u["inputs"]
            if all(type(given.get(key)) is int for key in ("V_0", "Q_0", "V_1", "Q_1")):
                row["amount_usd"] = {"month": given["V_1"], "baseline_month": given["V_0"]}
                row["net_weight_kg"] = {"month": given["Q_1"], "baseline_month": given["Q_0"]}
            rows.append(row)
    return rows


def _detect(request: args.Request) -> int:
    """detect: 조립체 2(단위 X1·X2·X4·P1·P2)를 불러 단위 P2의 출력(사례 목록·데이터 품질 목록)을 실행 폴더에 쓴다(위 "탐지
    명령 detect")."""
    # 명령을 부를 때만 import한다(도움말·인자 오류는 조립체를 불러오지 않는다). 모듈 속성으로 불러 시험 대역이 걸리게 한다.
    from tradesentry.contract import policy_load
    from tradesentry.dal import query
    from tradesentry.policy import case_build, trigger

    run_id, stamp, run_dir = reserve_run_dir(DETECT_RUN_NAME)
    try:
        policy = policy_load.load_policy(request.policy_version)
    except policy_load.PolicyError:
        _report("오류: tradesentry detect가 --policy의 정책을 읽지 못했다(PolicyError). "
                "정책 버전 이름과 configs/의 정책 파일을 확인한다.")
        return EXIT_FAILED
    try:
        with query.open_snapshot(request.snapshot_id) as snap:
            if snap.source_kind not in DETECT_SOURCE_KINDS:  # 값을 읽기 전에 거부한다(위 "탐지 명령 detect")
                _report(DETECT_REFUSAL)
                return EXIT_FAILED
            detection = trigger.run({"policy": policy, "rows": detection_rows(snap)})
            result = case_build.run({"snapshot_id": snap.snapshot_id, "source_kind": snap.source_kind,
                                     "detection": detection})
    except query.SnapshotError:
        _report("오류: tradesentry detect가 스냅샷을 열지 못했거나 스냅샷 자료가 행 규칙에 맞지 않는다(SnapshotError). "
                "--snapshot의 정본 빌드(data/snapshots/ 아래 snapshot_build.sqlite)를 확인한다.")
        return EXIT_FAILED
    if not isinstance(result, dict) or set(result) != CASE_BUILD_KEYS:
        raise WiringError("단위 P2(case_build)의 출력이 snapshot_id·dataset·policy_version·cases·data_quality 객체가 아니다")
    _emit(write_output(run_dir, run_id, DETECT_DOMAIN, stamp, "json", result))
    return EXIT_OK


def _not_wired(request: args.Request) -> int:
    """아직 조립체와 잇지 않은 명령의 자리표시 처리 함수. main은 이 함수를 부르지 않고 종료 코드 3으로 끝낸다."""
    raise NotImplementedError(f"tradesentry {request.command}는 아직 조립체와 잇지 않았다")


# 명령 → 처리 함수(검증된 요청을 받아 종료 코드를 돌려준다). 조립 작업이 명령마다 이 표의 자기 항목만 바꾼다.
HANDLERS: dict[str, Callable[[args.Request], int]] = {
    "snapshot-build": _snapshot_build,
    "snapshot-verify": _snapshot_verify,
    "detect": _detect,
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
