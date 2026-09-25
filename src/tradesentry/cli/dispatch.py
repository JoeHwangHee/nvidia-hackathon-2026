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

사례 조사 명령 run-case(조립체 3: 단위 X1~X4·P3~P5·G1·I1~I13·R1~R4·L1~L3. 배선은 조립 작업 AS2, 결정 기록
model-decision-as2-run-case)
- 순서: 실행명 확보(N8) → 단위 K4 load_policy → 모델 설정(단위 I9, configs/model/) 읽기 → 단위 K3 open_snapshot(정본 빌드,
  읽기 전용) → 출처 종류 확인(합성만, 실자료는 관측 값을 읽기 전에 거부하고 1) → 자료 묶음(RUN_CASE_DATASETS)과 비교 대상
  집합(합성은 비교국 표 행의 grouping_version 그대로) → 사례 다시 만들기(rebuild_case: --case의 case_id `{hs6}-{partner}-
  {month}`를 풀고 그 계열·비교월 하나만 detect와 같은 어댑터 → X1·X2 → P1 → P2로 계산. 사례가 아니면 1) → 흐름 조정(단위
  I12)을 NAT(단위 I13)로 감싸 돌린다 → 출력.
- 배선(unit_ports에 넘기는 것): 도구 자리 ToolPort(열린 스냅샷 하나로 도구 I1~I5의 query를 부른다. 요청에 policy_version·
  grouping_version·attempt, verify_evidence에만 흐름이 받은 봉투 원본의 사본), 정책 객체(검증기 R3 thresholds는 unit_ports가
  정책의 탐지 임계값을 수 목록으로 옮긴다), 근거 행 풀기(resolve_rows, K3 resolve), 근거 상태 변환(evidence_state: 도구 봉투
  → P3 입력. checklist가 쓴다). 모델 모드의 전송 자리는 run_case_transport(단위 I7 UrllibTransport, 키는 보내는 순간
  환경변수에서 읽는다)다.
- 출력(실행 폴더 outputs/run_case-{시각}/): runlog_trace-{시각}.jsonl(단위 L1), workflow_nat_wrap-{시각}/(N7 폴더, NAT 추적
  nat_trace.jsonl과 프로파일), runlog_run_record-{시각}.json(실행 쪽 키 21개, 단위 L2), 실행이 COMPLETED면
  reports_render_ko-{시각}.json(최종 보고서, 단위 R2). 순서대로 한 줄씩 상대경로를 적는다. 기록과 보고서는 trace와 같은
  직렬화(Decimal은 원문 표기의 JSON 숫자)로 쓴다.
- 종료 코드: 0 실행이 COMPLETED, 1 실행이 다른 상태로 끝남(기록은 남긴다)·정책·모델 설정·스냅샷을 읽지 못함·실자료 거부·
  자료 묶음이나 비교 대상 집합을 정하지 못함·사례가 아님, 4 흐름 밖 조립체 출력이 기대한 모양이 아님(사례 다시 만들기의
  지표·P2 출력, 흐름 조정의 반환 모양, 출력 직렬화). 흐름 안(도구 봉투 → 근거 상태 변환 등)에서 난 WiringError는 흐름
  조정이 CODE_ERROR로 기록하므로 실행 결과 기록이 남고 1이다. 오류 문장에는 받은 값과 스냅샷 안의 값을 넣지 않는다(N13).

평가 하네스는 모듈 단위로만 허용한다. 호스트 전용 샌드박스 밖 실행기(단위 E2, tradesentry.evaluation.sealed_runner)는
CLI가 부르지 않는다.

evaluate 배선(로드맵 MT7 첫 PR. 최종 연결은 조립 작업 AS3)
- 사례 실행(run-case) 처리 함수가 아직 자리표시(_not_wired)이거나, 묶음이 부를 사례 실행 함수(EVALUATE_CASE_RUNNER)와
  묶음 버전 키 함수(EVALUATE_VERSIONS)가 아직 없으면, 실행 폴더를 만들기 전에 분명한 오류 문장과 종료 코드 1로 끝난다.
  두 자리는 run-case를 잇는 조립(AS2)과 같은 조립이 채운다(AS3). 사례 실행 함수의 모양은 단위 E1의 CaseCall → 실행 쪽 키
  21개의 객체다. 버전 키 함수는 (요청, 자료 묶음) → policy_version·rulebook_version·snapshot_id·grouping_version·
  code_version 다섯 키의 객체다.
- 자료 묶음은 --snapshot으로 정한다 `[해석]`: dev20 → dev20, controlled_fixture_v0 → controlled_fixture_v0,
  kcs_202201_202412_v2 → real_dev(봉인 묶음은 evaluate가 돌리지 않는다. 샌드박스 밖 실행기 E2의 일). 사례 목록은
  dev20만 정본 자리 eval/dev/dev20/input/cases.json(DT5)에서 읽는다. controlled_fixture_v0·real_dev의 사례 목록 자리는
  아직 없어 분명한 오류로 끝난다(AS3이 정한다. real_dev는 DT7의 경보 목록).
- 모드 목록은 지금 명령 표 그대로 --mode 한 값이다(MT5 결정 ②의 잠정). 사용자 결정 12(2026-09-25 08:47)로 AS3이 --mode를
  선택 옵션으로 바꾼다: 주지 않으면 E1 PLANNED_MODES[자료 묶음]의 모드 전부를 한 묶음으로, 주면 그 모드 하나만(스모크용,
  점수표로 합치지 않음) 돈다. 채점기는 dev20·real_dev 묶음의 계획 모드가 그 표 전부가 아니면 채점하지 않는다.
- 실행명은 사용자 결정 10(나)대로 호스트가 먼저 확보하고 샌드박스 안 CLI에 --run-name으로 넘긴다(CLI 쪽과 샌드박스
  실행기는 AS3).
- 순서: 단위 E1 execute_batch(순서 seed DEV_ORDER_SEED, 동시성 1) → 단위 E4 summarize_batch(NAT 사후 평가) → 실행 조건
  입력 파일 run_conditions-{시각}.json을 묶음 실행 폴더에 배타 생성(E1 write_run_conditions). 표준 출력에는 묶음 기록과
  실행 조건 입력 파일의 outputs부터의 상대경로만 적는다. 사례 실행이 실패해도 묶음 기록을 끝까지 썼으면 0이다(실패는
  줄로 분모에 남는다). evaluate를 샌드박스 안에서 돌릴 때는 실행 조건 입력 파일을 샌드박스가 쓰면 안 된다(자료 계약 §8.2:
  내려받기를 끝낸 호스트 쪽 프로그램이 쓴다). 그 경로의 분기는 AS3·MT5가 정한다.
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
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
    "run-case": "조립체 3(사례 조사). 배선은 조립 작업 AS2가 맡는다",
    "evaluate": "조립체 4(평가 실행). 조립 작업 AS3이 잇는다",
}

# evaluate 배선(위 "evaluate 배선"). 스냅샷 ID → 자료 묶음 `[해석]`, dev20 사례 목록 자리(DT5), 개발 묶음 순서 seed.
EVALUATE_DATASETS = {"dev20": "dev20", "controlled_fixture_v0": "controlled_fixture_v0",
                     "kcs_202201_202412_v2": "real_dev"}
EVALUATE_CASE_LISTS = {"dev20": Path("eval") / "dev" / "dev20" / "input" / "cases.json"}
DEV_ORDER_SEED = "dev-order-v1"
# AS2·AS3이 채우는 자리: 사례 실행 함수(단위 E1 CaseCall → 실행 쪽 키 21개)와 버전 키 함수((요청, 자료 묶음) → 버전 키 5개).
EVALUATE_CASE_RUNNER: Callable[[object], dict] | None = None
EVALUATE_VERSIONS: Callable[[object, str], dict] | None = None


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


def detection_row(snapshot_id: str, hs6: str, partner: str, month: str, baseline: str,
                  parent: dict[str, list[dict]], world: dict[str, list[dict]]) -> dict:
    """계열 하나·비교월 하나의 단위 P1 입력 행. parent·world는 달 → 어댑터 행(parent_rows·world_rows)이다.

    r_U·d_s는 X1·X2의 exact_value(반올림 전 정확값)다. 부모 HS6 행의 금액·중량(P1이 정책의 min_amount·min_weight에 쓴다)은
    X1 r_U 입력의 V_0·Q_0·V_1·Q_1에서 옮긴다(네 값이 모두 정수일 때만. 값이 없으면 r_U가 null이라 P1이 읽지 않는다).
    detect(모든 계열)와 run-case(사례의 계열 하나, 조립 작업 AS2)가 같이 쓴다.
    """
    from tradesentry.metrics import share, unit_value

    target = {"snapshot_id": snapshot_id, "hs6": hs6, "partner": partner, "period": month, "baseline_period": baseline}
    both = parent[baseline] + parent[month]
    r_u = _pick_metric(unit_value.run({**target, "parent": both}), "r_U", "X1")
    d_s = _pick_metric(share.run({**target, "parent": both, "world": world[baseline] + world[month]}), "d_s", "X2")
    row = {"hs6": hs6, "partner": partner, "month": month, "baseline_month": baseline,
           "r_U": unit_value.exact_value(r_u), "d_s": share.exact_value(d_s)}
    given = r_u["inputs"]
    if all(type(given.get(key)) is int for key in ("V_0", "Q_0", "V_1", "Q_1")):
        row["amount_usd"] = {"month": given["V_1"], "baseline_month": given["V_0"]}
        row["net_weight_kg"] = {"month": given["Q_1"], "baseline_month": given["Q_0"]}
    return row


def detection_rows(snap) -> list[dict]:
    """계열·비교월마다 단위 X1·X2를 불러 단위 P1의 입력 행을 만든다(행 하나는 detection_row).

    K3는 계열마다 parent_series, HS6마다 world_series를 한 번씩 부르고, ALL 행은 HS6·달마다 한 번만 다시 만든다.
    """
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
        rows += [detection_row(snap.snapshot_id, hs6, partner, month, baseline, parent, world)
                 for month, baseline in pairs]
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


# ------------------------------------------------------------------------------ run-case(조립체 3, 조립 작업 AS2)
RUN_CASE_RUN_NAME = "run_case"  # 실행 이름(N5)
RUN_CASE_SOURCE_KINDS = ("controlled",)  # 이 판에서 조사하는 출처 종류(허용 목록). 실자료는 분할 기록 정본 위치 승인 뒤 잇는다
# 합성 스냅샷 → 실행 결과 기록의 dataset(자료 계약 §4.2·§8.1). 표에 없는 합성 스냅샷은 묶음을 정할 수 없어 거부한다
# (dev20 스냅샷 ID가 정해지면 이 표에 한 줄을 더한다).
RUN_CASE_DATASETS = {"controlled_fixture_v0": "controlled_fixture_v0"}
REAL_GROUPING_VERSION = "g0"  # 실자료의 비교 대상 집합(MVP까지 g0). 실자료를 거부하는 이 판에서는 쓰이지 않는다
RUN_RECORD_DOMAIN = "runlog_run_record"  # 실행 결과 기록을 만드는 단위 L2의 도메인명(UNITS.md §3.13, N4·N6)
REPORT_DOMAIN = "reports_render_ko"  # 최종 보고서를 만드는 단위 R2의 도메인명(UNITS.md §3.7)
NAT_DOMAIN = "workflow_nat_wrap"  # NAT 추적·프로파일 N7 폴더(단위 I13)
UNKNOWN_CODE_VERSION = "unknown"  # git 메타를 읽을 수 없을 때의 code_version(샌드박스·휠 설치)
PEER_ROW_SCAN_MAX = 100_000  # 비교국 표의 grouping_version을 읽을 때 훑는 rowid 상한
# 반올림 불안정(U4). 2026-09-25(금) 08:41 사용자 결정(policy_v1 승인, U4 → HOLD 채택)으로 켰다. 규칙은 rounding_unstable,
# 결정 기록 docs/tracking/decisions/20260925-0846-user-decision-policy-v1-approval.md. 끄는 곳도 이 한 줄이다.
ROUNDING_UNSTABLE_ENABLED = True
# 자료 교정 뒤 동결 정책으로 경보 해소(MT2 결정 ⑪). 동결 스냅샷 하나로 도는 v1 실행에서는 만드는 쪽이 없어 늘 거짓이다.
RESOLVED_AFTER_CORRECTION = False
# 점유율 comparability_issues 값(이 조립이 정했다, 잠정): 전체국가(ALL) 분모 금액이 대상국 금액보다 작은 달. "{이름}:{달}".
DENOMINATOR_BELOW_PARTNER = "denominator_below_partner"
GAP_STATUSES = ("REQUEST_FAILED", "NOT_COLLECTED", "UNRESOLVED_ZERO")  # 빠진 관측으로 보는 상태(P3와 같다)
RUN_CASE_REFUSAL = ("오류: tradesentry run-case는 지금 합성 스냅샷(source_kind가 controlled)만 조사한다. 이 스냅샷은 합성 "
                    "스냅샷이 아니어서 관측 값을 읽지 않고 끝냈다. 실자료 스냅샷은 분할 기록의 정본 위치가 사용자 승인을 받은 "
                    "뒤 real_dev 사례로 좁혀 잇는다.")


class RunCaseError(Exception):
    """run-case가 사례를 조사하지 않고 끝내는 까닭(종료 코드 1). 문장에는 받은 값·스냅샷 안의 값을 넣지 않는다(N13)."""


def code_version(root: Path | None = None) -> str:
    """실행한 코드의 git 커밋 해시(자료 계약 §8.1 code_version). 하위 프로세스 없이 git 메타 파일을 읽는다.

    작업 폴더(git worktree)의 .git 파일(gitdir)과 commondir, packed-refs를 따른다. 읽을 수 없거나 40자 16진수가 아니면
    UNKNOWN_CODE_VERSION이다. 경로는 돌려주지 않는다(N13). 작업 트리의 고치지 않은 변경은 표시하지 않는다.
    """
    root = Path(__file__).resolve().parents[3] if root is None else Path(root)

    def checked(value: str) -> str:
        return value if re.fullmatch(r"[0-9a-f]{40}", value) else UNKNOWN_CODE_VERSION

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


def snapshot_grouping_version(snap) -> str:
    """합성 스냅샷의 비교 대상 집합: 비교국 표(peer_group) 행의 grouping_version 값 그대로(자료 계약 §2.3.6·§8.1, DT3 결정 ⑫).

    자료 접근층(K3)에 목록 함수가 없어 공개 함수 row로 rowid 1부터 빈 행까지 훑는다(S2 빌드의 rowid는 1부터 이어진다).
    값이 하나가 아니면(표가 비었거나 여럿이면) 정할 수 없어 RunCaseError다.
    """
    found: set[object] = set()
    for rowid in range(1, PEER_ROW_SCAN_MAX + 1):
        row = snap.row("peer_group", rowid)
        if row is None:
            break
        found.add(row.get("grouping_version"))
    if len(found) != 1 or not isinstance(next(iter(found)), str):
        raise RunCaseError("오류: tradesentry run-case가 합성 스냅샷의 비교국 표에서 grouping_version 값 하나를 얻지 못했다"
                           "(표가 비었거나 값이 여럿이다).")
    return next(iter(found))


def rebuild_case(snap, policy: dict, case_arg: str) -> dict:
    """--case(case_id `{hs6}-{partner}-{month}`)의 사례를 스냅샷과 정책으로 다시 만든다(탐지와 같은 길: K3 → 어댑터 → X1·X2 →
    P1 → P2). 그 계열·비교월 하나만 계산한다(다른 계열의 지표를 만들지 않는다). 사례가 아니면 RunCaseError다.
    돌려주는 값은 사례 객체의 8필드(자료 계약 §2.3.5, P2의 scope는 뗀다)다."""
    from tradesentry.contract import types
    from tradesentry.policy import case_build, trigger

    try:
        wanted = case_build.parse_case_id(case_arg)
    except ValueError:
        raise RunCaseError("오류: tradesentry run-case의 --case가 사례 식별자 형식({hs6}-{partner}-{month})이 아니다.") from None
    hs6, partner, month, baseline = (wanted[k] for k in ("hs6", "partner", "month", "baseline_month"))
    if hs6 not in snap.hs6_codes or partner not in snap.partners or month not in snap.months \
            or baseline not in snap.months:
        raise RunCaseError("오류: tradesentry run-case의 --case가 스냅샷의 분석 범위(수집 설정의 HS6·상대국, 기준월도 든 "
                           "수집 기간) 밖이다.")
    parent = {value["month"]: parent_rows(value) for value in snap.parent_series(hs6, partner, [baseline, month])}
    world = {value["month"]: world_rows(snap, value) for value in snap.world_series(hs6, [baseline, month])}
    row = detection_row(snap.snapshot_id, hs6, partner, month, baseline, parent, world)
    detection = trigger.run({"policy": policy, "rows": [row]})
    built = case_build.run({"snapshot_id": snap.snapshot_id, "source_kind": snap.source_kind, "detection": detection})
    found = [c for c in built["cases"] if c["case_id"] == case_arg]
    if not found:
        raise RunCaseError("오류: tradesentry run-case의 --case는 이 스냅샷과 정책으로 신호가 발동한 사례가 아니다.")
    return {key: found[0][key] for key in types.CASE_KEYS}


class ToolPort:
    """흐름 조정(단위 I12)의 도구 자리를 MT2 도구(단위 I1~I5)에 잇는다. 열린 스냅샷 하나로 모든 도구를 부른다(query).

    요청: {case_id, snapshot_id, scope(사례 네 키), args, attempt, policy_version, grouping_version} + verify_evidence만
    envelopes. attempt는 이 자리가 도구를 부른 순번(1부터)이다(query_id가 호출마다 고유하다). envelopes는 이 자리가 흐름에
    돌려준 봉투의 사본 목록이다: 흐름이 실제로 받은 봉투 원본만 넘기고, 모델 출력이나 모델에게 보인 축약본은 넘기지
    않는다(MT2 보안 권고 3). 사본으로 두어 흐름 쪽에서 봉투를 고쳐도 대조 원본이 바뀌지 않는다.
    """

    def __init__(self, snap, case: dict, policy_version: str, grouping_version: str):
        from tradesentry.workflow import orchestrate

        self.snap = snap
        self.case = case
        self.policy_version = policy_version
        self.grouping_version = grouping_version
        self.units = orchestrate.TOOL_UNITS
        self.returned: list[dict] = []
        self.requests: list[dict] = []

    def call(self, name: str, tool_args: dict) -> dict:
        from tradesentry.runlog import trace as trace_log

        request = {"case_id": self.case["case_id"], "snapshot_id": self.case["snapshot_id"],
                   "scope": {key: self.case[key] for key in ("hs6", "partner", "month", "baseline_month")},
                   "args": tool_args, "attempt": len(self.requests) + 1, "policy_version": self.policy_version,
                   "grouping_version": self.grouping_version}
        if name == "verify_evidence":
            request["envelopes"] = [trace_log.loads(trace_log.dumps(e)) for e in self.returned]
        self.requests.append({k: v for k, v in request.items() if k != "envelopes"})
        envelope = self.units[name].query(self.snap, request)
        self.returned.append(trace_log.loads(trace_log.dumps(envelope)))
        return envelope


def resolve_rows(snap, ids: list) -> dict:
    """근거 ID 목록 → {근거 ID: 스냅샷 행 또는 None}(검증기 R3 rows). 자료 접근층 resolve의 풀림 규칙 1~4를 쓴다."""
    from tradesentry.dal import query

    rows = {}
    for evidence_id in ids:
        try:
            found = snap.resolve(evidence_id)
        except query.SnapshotError:
            found = {"resolved": False, "row": None}
        rows[evidence_id] = found.get("row") if found.get("resolved") else None
    return rows


def rounding_unstable(v0: int, q0: int, v1: int, q1: int, delta, threshold) -> bool:
    """반올림 불안정(U4, 2026-09-25(금) 사용자 결정으로 채택). 발동한 단가 신호에만 쓴다.

    금액은 그대로 두고 두 달의 부모 중량을 Q ± δ(δ = 정책 tolerance.weight_rounding_kg, 0.5 kg)로 움직인 r_U(%) 구간
    [하한, 상한]을 구한다. r_U ≥ 0이면 하한 < θ, r_U < 0이면 상한 > −θ일 때 불안정이다(θ = 정책 단가 탐지 임계값).
    경계와 같으면 안정이다. 어느 달이든 Q ≤ δ이거나 기준월 금액이 0 이하면 구간이 끝없어 불안정이다. 계산은 분수로 한다.
    단위 I1의 rounding(부호와 임계값 양쪽을 보는 대칭 규칙)과 다르다.
    """
    d, theta = Fraction(delta), Fraction(threshold)
    if q0 - d <= 0 or q1 - d <= 0 or v0 <= 0:
        return True
    r_u = (Fraction(v1) * q0 / (Fraction(v0) * q1) - 1) * 100
    low = (Fraction(v1) * (q0 - d) / (Fraction(v0) * (q1 + d)) - 1) * 100
    high = (Fraction(v1) * (q0 + d) / (Fraction(v0) * (q1 - d)) - 1) * 100
    return low < theta if r_u >= 0 else high > -theta


def _received(envelopes: list, tool: str) -> list[dict]:
    """그 도구가 결과를 돌려준 봉투(retryable_error 없음). 막힌 시도·거부 봉투는 비교를 수행하지 않은 것이다."""
    return [e for e in envelopes if isinstance(e, dict) and e.get("tool") == tool and e.get("retryable_error") is None]


def _metric(envelope: dict | None, symbol: str, partner: str, period: str) -> dict | None:
    """봉투에서 (기호, 상대국, 달)의 지표 하나. 없으면 None, 둘 이상이면 배선 계약 위반(4)."""
    found = [m for m in (envelope or {}).get("metrics") or [] if isinstance(m, dict) and isinstance(m.get("inputs"), dict)
             and m["inputs"].get("metric") == symbol and m["inputs"].get("partner") == partner
             and m["inputs"].get("period") == period]
    if len(found) > 1:
        raise WiringError(f"도구 봉투에 {symbol} 지표가 둘 이상이다")
    return found[0] if found else None


def evidence_missingness(envelopes: list) -> list[dict]:
    """모든 봉투의 missingness 항목을 근거 ID로 중복을 빼 그대로 모은다(키 이름을 바꾸지 않는다). 같은 근거 ID가 두 번
    나오면 C형 코드 목록(hs10_codes)이 있는 항목을 남긴다. ALL 분모는 도구·자료 접근층이 중복 제거(행 규칙 5·6) 뒤에도
    실제로 비는 달만 싣는다(MT1 결정 ⑫)."""
    kept: dict[str, dict] = {}
    for envelope in envelopes:
        for item in (envelope.get("missingness") or []) if isinstance(envelope, dict) else []:
            key = item.get("evidence_id") if isinstance(item, dict) else None
            if not isinstance(key, str):
                continue
            if key not in kept or ("hs10_codes" in item and "hs10_codes" not in kept[key]):
                kept[key] = item
    return list(kept.values())


def _family_gap(missingness: list[dict], case: dict, family: str) -> bool:
    """그 계열에 빠진 관측(P3 1번 사유)이 있나. P3과 같은 배정: 비교월·기준월, 사례 HS6 아래, 단가는 대상국 행, 점유율은
    ALL 행."""
    wanted = case["partner"] if family == "unit_value" else "ALL"
    return any(item.get("observation_status") in GAP_STATUSES and item.get("partner_code") == wanted
               and item.get("month") in (case["month"], case["baseline_month"])
               and str(item.get("hs_code") or "").startswith(case["hs6"]) for item in missingness)


def _partners_mark(envelopes: list) -> str:
    """비교국 비교(compare_partners)의 완료 표시. 허용 비교국이 없으면(no_allowed_peers) 수행하지 않은 것이고, 조회한
    비교국 가운데 두 달 모두 결과가 있는(관측 또는 무거래 확정) 나라가 하나라도 있으면 done, 모두 빠진 관측이 있으면
    incomplete다(무거래 확정은 비교를 끝낸 것이고 결측만 미완료다)."""
    marks = []
    for envelope in _received(envelopes, "compare_partners"):
        comparability = envelope.get("comparability") or {}
        if comparability.get("comparable") is not True:
            marks.append("not_performed")
            continue
        finished = [peer for peer in comparability.get("peers") or []
                    if len(peer.get("months") or []) == 2
                    and all(m.get("observation_status") in ("OBSERVED", "CONFIRMED_NO_TRADE") for m in peer["months"])]
        marks.append("done" if finished else "incomplete")
    for mark in ("done", "incomplete"):
        if mark in marks:
            return mark
    return "not_performed"


def _country_and_world_mark(history: dict | None, case: dict) -> str:
    """해당국 금액과 전체국가 분모 변화 확인(get_history의 V 네 개: 대상국·ALL × 기준월·비교월)의 완료 표시."""
    if history is None:
        return "not_performed"
    values = [_metric(history, "V", who, month) for who in (case["partner"], "ALL")
              for month in (case["baseline_month"], case["month"])]
    return "done" if all(m is not None and m.get("value") is not None for m in values) else "incomplete"


def _denominator_issues(history: dict | None, case: dict) -> list[str]:
    """전체국가(ALL) 분모 금액이 대상국 금액보다 작은 달(dev20 분류 7). 점유율을 같은 정의로 볼 수 없는 자료다."""
    from tradesentry.metrics import share

    issues = []
    for month in (case["baseline_month"], case["month"]):
        country, world = _metric(history, "V", case["partner"], month), _metric(history, "V", "ALL", month)
        if country is None or world is None or country.get("value") is None or world.get("value") is None:
            continue
        if share.exact_value(world) < share.exact_value(country):
            issues.append(f"{DENOMINATOR_BELOW_PARTNER}:{month}")
    return issues


def evidence_state(case: dict, envelopes: list, policy: dict) -> dict:
    """도구 봉투 → 판정 정책 P3의 근거 상태(MT1 결정 ⑪ 모양). 코드가 봉투에서 결정적으로 만들고 모델 주장은 쓰지 않는다.

    - missingness: evidence_missingness. comparisons: 비교 조건 점검(check_comparability 결과를 받았으면 done), 비교국
      비교(_partners_mark), 해당국·전체국가 변화(_country_and_world_mark). 수행하지 않은 비교는 not_performed다.
    - comparability_issues: check_comparability의 signals.{계열}.issues 그대로(값이 정의되지 않는 달: 단위 불일치,
      무거래·중량 0·기준월 단가 0·분모 0). 점유율에는 ALL 분모 < 대상국 금액인 달을 더한다.
    - 단가: U_baseline(get_history U 기준월), decomposition(decompose_hs within·mix·residual, parent_child_match = 두 달
      부모 대조의 금액·중량 일치), children(r_U@HS10마다). 수는 반올림 전 정확값(Fraction, 지표 단위 exact_value)이다.
    - 조기 종료는 신호 계열별이다: 그 계열의 도구를 받지 못해 null·빈 목록을 적는 것은 그 계열에 다른 1번 사유(빠진 관측,
      비교 가능성 문제)가 있을 때뿐이고, 없으면 ValueError(흐름이 CODE_ERROR로 기록한다. 배선 누락이 HOLD로 숨지 않게).
    - rounding_unstable: ROUNDING_UNSTABLE_ENABLED가 참일 때만 rounding_unstable 규칙으로 계산하고, 아니면 거짓이다.
      resolved_after_correction: 거짓(RESOLVED_AFTER_CORRECTION).
    """
    from tradesentry.metrics import decompose, unit_value

    missingness = evidence_missingness(envelopes)
    state: dict = {"missingness": missingness}
    checked = _received(envelopes, "check_comparability")
    history = (_received(envelopes, "get_history") or [None])[-1]
    comparisons = {"comparability": "done" if checked else "not_performed", "partners": _partners_mark(envelopes),
                   "country_and_world": _country_and_world_mark(history, case)}
    signals_info = ((checked[-1].get("comparability") or {}).get("signals") or {}) if checked else {}
    partner, month, baseline = case["partner"], case["month"], case["baseline_month"]
    for family in ("unit_value", "share"):
        if case["signals"].get(family) != "TRIGGERED":
            continue
        issues = list((signals_info.get(family) or {}).get("issues") or [])
        if family == "share":
            issues += _denominator_issues(history, case)
        has_reason = bool(issues) or _family_gap(missingness, case, family)
        if family == "share":
            state["share"] = {"comparability_issues": issues,
                              "comparisons": {k: comparisons[k] for k in ("comparability", "partners",
                                                                          "country_and_world")},
                              "resolved_after_correction": RESOLVED_AFTER_CORRECTION}
            continue
        decomposed = (_received(envelopes, "decompose_hs") or [None])[-1]
        if (history is None or decomposed is None) and not has_reason:
            raise ValueError("단가 신호의 이력·분해 조회를 받지 못했는데 단가 계열에 다른 자료 부족 사유가 없다"
                             "(조기 종료는 신호 계열별이다)")
        u_baseline = None
        if history is not None:
            metric = _metric(history, "U", partner, baseline)
            if metric is None:
                raise WiringError("get_history 봉투에 기준월 대상국 U 지표가 없다")
            u_baseline = unit_value.exact_value(metric)
        decomposition, children = None, []
        if decomposed is not None:
            effects = {}
            for symbol in ("within_effect", "mix_effect", "residual"):
                metric = _metric(decomposed, symbol, partner, month)
                if metric is None:
                    raise WiringError(f"decompose_hs 봉투에 {symbol} 지표가 없다")
                effects[symbol] = decompose.exact_value(metric)
            checks = (decomposed.get("comparability") or {}).get("parent_check") or []
            match = len(checks) == 2 and all(c.get("V_match") is True and c.get("Q_match") is True for c in checks)
            decomposition = {**effects, "parent_child_match": match}
            for metric in decomposed.get("metrics") or []:
                symbol = (metric.get("inputs") or {}).get("metric") or ""
                if symbol.startswith("r_U@") and metric["inputs"].get("partner") == partner:
                    children.append({"hs10": symbol.partition("@")[2], "r_U": decompose.exact_value(metric)})
        unstable = False
        if ROUNDING_UNSTABLE_ENABLED and history is not None:
            change = _metric(history, "r_U", partner, month)
            given = (change or {}).get("inputs") or {}
            if all(type(given.get(k)) is int for k in ("V_0", "Q_0", "V_1", "Q_1")):
                unstable = rounding_unstable(given["V_0"], given["Q_0"], given["V_1"], given["Q_1"],
                                             policy["tolerance"]["weight_rounding_kg"],
                                             policy["thresholds"]["unit_value"])
        state["unit_value"] = {"comparability_issues": issues,
                               "comparisons": {k: comparisons[k] for k in ("comparability", "partners")},
                               "U_baseline": u_baseline, "decomposition": decomposition, "children": children,
                               "rounding_unstable": unstable, "resolved_after_correction": RESOLVED_AFTER_CORRECTION}
    return state


def required_tools(case: dict) -> list[str]:
    """조사자가 초안 전에 받아야 하는 도구(공개 판정 규칙이 쓰는 비교, 모든 모드 같음). 신호가 하나라도 발동했으면
    비교국 비교(compare_partners: 단가 MAINTAIN과 점유율 판정의 필수 비교), 단가 신호가 발동했으면 HS10 분해(decompose_hs:
    단가 판정 근거)다. 흐름 조정이 이 목록 없이 쓴 초안을 차례마다 한 번 돌려보낸다(AS2 결정 기록 ⑮)."""
    signals = case.get("signals") or {}
    names = ["compare_partners"] if "TRIGGERED" in signals.values() else []
    if signals.get("unit_value") == "TRIGGERED":
        names.append("decompose_hs")
    return names


def run_case_transport(config):
    """모델 모드의 NIM 전송 자리(단위 I7 UrllibTransport). 키는 보내는 순간 환경변수에서 읽는다. 시험은 이 함수를 바꿔 끼운다."""
    from tradesentry.workflow import model_client

    return model_client.UrllibTransport(config.settings.endpoint, config.settings.api_key_env)


def _write_json(run_dir: Path, run_id: str, domain: str, stamp: str, value: object) -> str:
    """값을 {도메인명}-{시각}.json으로 쓴다(이미 있으면 실패, N8). Decimal은 원문 표기의 JSON 숫자로 쓴다(trace와 같은
    직렬화. 보고서 수의 끝자리 0을 지킨다, 자료 계약 §9.1). 표준 출력에 적을 상대경로를 돌려준다."""
    from tradesentry.runlog import trace as trace_log

    try:
        payload = (trace_log.dumps(value) + "\n").encode("utf-8")
    except ValueError:
        raise WiringError(f"{domain} 출력을 JSON으로 쓸 수 없다") from None
    name = f"{domain}-{stamp}.json"
    with open(run_dir / name, "xb") as handle:
        handle.write(payload)
    return f"{OUTPUT_LABEL}/{run_id}/{name}"


def investigate_case(snap, policy: dict, case: dict, request: args.Request, run_id: str, stamp: str, run_dir: Path,
                     *, dataset: str, grouping_version: str) -> dict:
    """사례 1건을 흐름 조정(단위 I12)으로 NAT(단위 I13) 안에서 돌린다. trace(단위 L1)는 실행 폴더에 쓴다.
    돌려주는 값: {"record": 실행 쪽 키, "report": 최종 보고서 또는 None, "trace": 상대경로, "nat": 상대경로}."""
    from tradesentry.contract import types
    from tradesentry.runlog import trace as trace_log
    from tradesentry.workflow import model_client, nat_wrap, orchestrate

    config = model_client.load_model_config()
    port = ToolPort(snap, case, request.policy_version, grouping_version)
    ports = orchestrate.unit_ports(case, request.mode, run_id, config.limits, grouping_version=grouping_version,
                                   policy=policy, rows=lambda ids: resolve_rows(snap, ids),
                                   evidence_state=lambda case_obj, envelopes: evidence_state(case_obj, envelopes,
                                                                                             policy))
    ports.tool = port.call
    ports.required_tools = required_tools
    ports.drafts_only_without_tools = True  # 초안은 구조화 출력(json_object) 차례에서만 받는다(AS2 결정 기록 ⑱)
    ctx = orchestrate.RunContext(run_id=run_id, case=case, mode=request.mode, dataset=dataset,
                                 rulebook_version=types.RULEBOOK_VERSION, grouping_version=grouping_version,
                                 code_version=code_version())
    transport = None if request.mode == "checklist" else run_case_transport(config)
    trace_file = trace_log.trace_path(run_dir, stamp)
    writer = trace_log.TraceWriter(trace_file, run_id)
    nat_dir = run_dir / f"{NAT_DOMAIN}-{stamp}"

    def flow(nat_sink):
        return orchestrate.orchestrate(ctx, ports, config, transport=transport, sink=trace_log.Tee(writer, nat_sink))

    try:
        outcome = nat_wrap.run_under_nat(flow, nat_dir, model=config.settings.model)
    finally:
        writer.close()
    result = outcome["result"]
    if not isinstance(result, dict) or not isinstance(result.get("record"), dict) or "report" not in result:
        raise WiringError("단위 I12(orchestrate)의 출력이 {record, report} 객체가 아니다")
    return {"record": result["record"], "report": result["report"],
            "trace": f"{OUTPUT_LABEL}/{run_id}/{trace_file.name}", "nat": f"{OUTPUT_LABEL}/{run_id}/{nat_dir.name}"}


def _run_case(request: args.Request) -> int:
    """run-case: 조립체 3으로 사례 1건을 조사해 실행 폴더에 trace·NAT 추적·실행 결과 기록·보고서를 쓴다(머리 설명 "사례
    조사 명령 run-case")."""
    # 명령을 부를 때만 import한다(도움말·인자 오류는 조립체를 불러오지 않는다). 모듈 속성으로 불러 시험 대역이 걸리게 한다.
    from tradesentry.contract import policy_load
    from tradesentry.dal import query
    from tradesentry.runlog import cause_codes
    from tradesentry.workflow import model_client

    run_id, stamp, run_dir = reserve_run_dir(RUN_CASE_RUN_NAME)
    try:
        policy = policy_load.load_policy(request.policy_version)
    except policy_load.PolicyError:
        _report("오류: tradesentry run-case가 --policy의 정책을 읽지 못했다(PolicyError). "
                "정책 버전 이름과 configs/의 정책 파일을 확인한다.")
        return EXIT_FAILED
    try:
        model_client.load_model_config()
    except model_client.ConfigError:
        _report("오류: tradesentry run-case가 모델 설정(configs/model/)을 읽지 못했다(ConfigError).")
        return EXIT_FAILED
    try:
        with query.open_snapshot(request.snapshot_id) as snap:
            if snap.source_kind not in RUN_CASE_SOURCE_KINDS:  # 관측 값을 읽기 전에 거부한다(머리 설명)
                _report(RUN_CASE_REFUSAL)
                return EXIT_FAILED
            # 실자료를 잇는 자리(분할 기록 정본 위치 승인 뒤): 사례 계열이 real_dev에 배정된 경우만 받고 real_sealed는 관측
            # 값을 읽기 전에 거부한다. dataset은 real_dev, 비교 대상 집합은 REAL_GROUPING_VERSION(결정 기록 AS2 ⑩).
            dataset = RUN_CASE_DATASETS.get(snap.snapshot_id)
            if dataset is None:
                raise RunCaseError("오류: tradesentry run-case가 이 합성 스냅샷의 자료 묶음(dataset)을 정하지 못했다"
                                   "(RUN_CASE_DATASETS에 없다).")
            grouping_version = snapshot_grouping_version(snap)
            case = rebuild_case(snap, policy, request.case)
            outcome = investigate_case(snap, policy, case, request, run_id, stamp, run_dir, dataset=dataset,
                                       grouping_version=grouping_version)
    except RunCaseError as exc:
        _report(str(exc))
        return EXIT_FAILED
    except query.SnapshotError:
        _report("오류: tradesentry run-case가 스냅샷을 열지 못했거나 스냅샷 자료가 행 규칙에 맞지 않는다(SnapshotError). "
                "--snapshot의 정본 빌드(data/snapshots/ 아래 snapshot_build.sqlite)를 확인한다.")
        return EXIT_FAILED
    except query.ScopeError:
        _report("오류: tradesentry run-case의 조회가 스냅샷의 분석 범위 밖이다(ScopeError).")
        return EXIT_FAILED
    record, report = outcome["record"], outcome["report"]
    _emit(outcome["trace"])
    _emit(outcome["nat"])
    _emit(_write_json(run_dir, run_id, RUN_RECORD_DOMAIN, stamp, record))
    if report is not None:
        _emit(_write_json(run_dir, run_id, REPORT_DOMAIN, stamp, report))
    if record.get("execution_status") == cause_codes.COMPLETED:
        return EXIT_OK
    codes = [e.get("code") for e in record.get("errors") or [] if isinstance(e, dict)]
    _report(f"오류: 사례 실행이 {record.get('execution_status')}로 끝났다(원인 분류 코드 {', '.join(map(str, codes)) or '없음'}). "
            "실행 결과 기록과 trace를 확인한다.")
    return EXIT_FAILED


def _not_wired(request: args.Request) -> int:
    """아직 조립체와 잇지 않은 명령의 자리표시 처리 함수. main은 이 함수를 부르지 않고 종료 코드 3으로 끝낸다."""
    raise NotImplementedError(f"tradesentry {request.command}는 아직 조립체와 잇지 않았다")


def evaluate_cases(dataset: str, snapshot_id: str) -> list[dict]:
    """자료 묶음의 사례 목록(case_id·hs6·partner·month). 자리가 없으면 LookupError, 형식이 틀리면 ValueError."""
    path = EVALUATE_CASE_LISTS.get(dataset)
    if path is None or not path.is_file():
        raise LookupError(dataset)
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or doc.get("dataset") != dataset or doc.get("snapshot_id") != snapshot_id \
            or not isinstance(doc.get("cases"), list):
        raise ValueError("사례 목록 파일의 dataset·snapshot_id·cases가 요청과 맞지 않다")
    return doc["cases"]


def _evaluate(request: args.Request) -> int:
    """evaluate: 단위 E1 묶음 실행 → 단위 E4 NAT 사후 평가 → 실행 조건 입력 파일(위 "evaluate 배선")."""
    if HANDLERS["run-case"] is _not_wired or EVALUATE_CASE_RUNNER is None or EVALUATE_VERSIONS is None:
        _report("오류: tradesentry evaluate는 사례 실행(run-case)이 아직 조립되지 않아 돌 수 없다. "
                f"{ASSEMBLIES['run-case']}. evaluate의 최종 연결은 조립 작업 AS3이 한다.")
        return EXIT_FAILED
    # 명령을 부를 때만 import한다. 모듈 속성으로 불러 시험 대역이 걸리게 한다.
    from tradesentry.contract import policy_load
    from tradesentry.evaluation import batch_run, nat_eval
    from tradesentry.workflow import model_client, orchestrate

    dataset = EVALUATE_DATASETS.get(request.snapshot_id)
    if dataset is None:
        _report("오류: tradesentry evaluate가 --snapshot의 자료 묶음을 모른다(dev20·controlled_fixture_v0·"
                "kcs_202201_202412_v2만 받는다. 봉인 묶음은 샌드박스 밖 실행기가 돌린다).")
        return EXIT_FAILED
    try:
        cases = evaluate_cases(dataset, request.snapshot_id)
    except LookupError:
        _report(f"오류: tradesentry evaluate가 자료 묶음 {dataset}의 사례 목록 자리를 모르거나 파일이 없다"
                "(dev20은 eval/dev/dev20/input/cases.json. 다른 묶음의 자리는 조립 작업 AS3이 정한다).")
        return EXIT_FAILED
    except ValueError as exc:
        _report(f"오류: tradesentry evaluate가 사례 목록을 읽지 못했다({type(exc).__name__}).")
        return EXIT_FAILED
    try:
        thresholds = orchestrate.policy_thresholds(policy_load.load_policy(request.policy_version))
        limits = batch_run.limits_from_run_limits(model_client.load_model_config().limits)
        versions = EVALUATE_VERSIONS(request, dataset)
        spec = batch_run.BatchSpec(dataset=dataset, cases=tuple(cases), modes=(request.mode,),
                                   order_seed=DEV_ORDER_SEED, versions=versions)
        batch_run.check_spec(spec)
    except ValueError as exc:  # PolicyError·ConfigError·BatchError는 ValueError다. 예외 이름만 적는다(N13)
        _report(f"오류: tradesentry evaluate의 묶음 입력이 규칙에 맞지 않는다({type(exc).__name__}).")
        return EXIT_FAILED
    result = batch_run.execute_batch(spec, EVALUATE_CASE_RUNNER, parent=OUTPUT_PARENT,
                                     other_parent=OUTPUT_PARENT / SEALED_NAME)
    _emit(f"{OUTPUT_LABEL}/{result.run_id}/{result.batch_file.name}")
    summary = nat_eval.summarize_batch(result.run_dir)
    doc = batch_run.build_run_conditions(dataset=dataset, cases=cases, modes=list(spec.modes), thresholds=thresholds,
                                         order_seed=DEV_ORDER_SEED, limits=limits,
                                         run_period=(result.started, result.ended), nat_profile_summary=summary)
    path = batch_run.write_run_conditions(result.run_dir, doc)
    _emit(f"{OUTPUT_LABEL}/{result.run_id}/{path.name}")
    return EXIT_OK


# 명령 → 처리 함수(검증된 요청을 받아 종료 코드를 돌려준다). 조립 작업이 명령마다 이 표의 자기 항목만 바꾼다.
HANDLERS: dict[str, Callable[[args.Request], int]] = {
    "snapshot-build": _snapshot_build,
    "snapshot-verify": _snapshot_verify,
    "detect": _detect,
    "run-case": _run_case,
    "evaluate": _evaluate,
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
