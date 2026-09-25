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
- --run-name(사용자 결정 10(나), 다섯 명령): 호스트가 먼저 확보한 실행명을 받으면 CLI는 그 이름의 실행 폴더를 이미 있으면
  실패하는 방식으로 만든다(reserve_given_run_dir. 다음 초로 넘어가지 않는다). 만들지 못하면 종료 코드 1(RunNameError).
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
- 출처 종류(source_kind)는 호출자가 아니라 스냅샷 메타에서 읽는다(MT1 결정 ⑭의 AS1 항목). 허용 목록은 합성
  (controlled)과 실자료(real)다. 그 밖의 값은 지표를 계산하거나 K3로 값을 읽기 전에 거부하고 1로 끝난다.
- 실자료(real)는 분할 기록(REAL_SPLIT_FILES: 스냅샷 ID → 정본 파일. 지금은 kcs_202201_202412_v2 →
  data/reference/real_split_kcs_202201_202412_v2.json 하나, 2026-09-25 사용자 결정 8)을 읽어 real_dev 계열만 남긴 뒤에
  K3로 값을 읽고 지표(X1·X2)와 신호 발동(P1)을 부른다(병렬 개발 규칙 §7.2의 5, MT1 결정 ⑭). real_sealed 계열의 관측 값은
  읽지 않는다. 단위 P2에는 dataset=real_dev와 분할 기록 전체의 배정(series_assignment, [{hs6, partner, dataset}])을 넘긴다.
  P2의 묶음 제한은 마지막 방어선이다. 묶음은 real_dev로 고정이고 새 CLI 옵션은 두지 않는다. 대응표에 없는 실자료
  스냅샷(v1 등)이나, 분할 기록이 없거나 모양이 틀리거나 스냅샷의 계열(수집 설정의 HS6 × 상대국)과 맞지 않으면 값을 읽기
  전에 1로 끝난다(SplitError). 결정 기록 model-decision-as1-real-dev.
- 계열은 수집 설정의 HS6 × 상대국이다(비교국 표의 계획 밖 국가는 대상이 아니다). 실자료는 그 가운데 real_dev 계열이다.
  비교월 t는 기준월 t−12도 스냅샷 기간 안인 달만이다. 지표 입력은 계열마다 두 달(t−12, t)씩 넘긴다.
- 어댑터(K3 월 값 → 지표 단위의 역할별 입력 행, DT2 결정 ①): 값이 있는 달(OBSERVED)은 행 하나, 무거래 확정 달
  (CONFIRMED_NO_TRADE)은 V·Q 칸이 빈 행 하나(근거 ID는 K3가 준 상태 행 전부), 빠진 달은 K3 missingness 항목마다 상태 행
  하나(근거 ID 하나)다. 전체국가(ALL) 분모는 K3가 중복을 뺀(행 규칙 6) 뒤 고른 HS10 행의 근거 ID를 K3 resolve로 풀어 HS10
  행으로 다시 만들고, 코드 목록과 금액 합이 K3 값과 같은지 본다(다르면 4).
- P1 입력 행에는 X1의 r_U 입력(V_0·Q_0·V_1·Q_1)에서 부모 HS6 행의 금액·중량을 옮긴다(네 값이 모두 정수일 때). 정책의
  min_amount·min_weight가 있을 때 P1이 읽는다.
- 출력은 P2 출력 그대로 한 파일이다({snapshot_id, dataset, policy_version, cases, data_quality}. 합성 스냅샷은 dataset이
  null, 실자료는 real_dev). 도메인명은 그 출력을 만든 단위 P2의 policy_case_build다(N4·N6). P1 전체 발동표와 metric 객체는
  쓰지 않는다. 탐지 코드의 커밋(code_version)은 출력에 넣지 않는다(자료 계약 §8의 code_version은 사례 실행 기록의 키이고,
  N6은 도메인명 하나에 파일 하나다. 실자료 사례 목록의 code_version은 로드맵 DT7이 결정 기록에 적는다).
- 종료 코드: 0 성공(사례가 없어도), 1 정책을 읽지 못함(PolicyError, 스냅샷을 열지 않는다)·스냅샷을 열지 못했거나 행 규칙에
  맞지 않음(SnapshotError)·허용 목록 밖 출처 종류·분할 기록 오류(SplitError)·단위의 입력 오류(예상 밖 예외), 4 조립체 출력이
  기대한 모양이 아님
  (WiringError). 오류 문장에는 받은 값(스냅샷 ID·정책 이름)과 스냅샷 안의 값을 넣지 않고 예외 이름만 적는다(N13, MT5 결정 ⑧).
- 쓰지 않는 공통 옵션 --mode는 요청에 남지만 단위에 넘기지 않는다.

사례 조사 명령 run-case(조립체 3: 단위 X1~X4·P3~P5·G1·I1~I13·R1~R4·L1~L3. 배선은 조립 작업 AS2, 결정 기록
model-decision-as2-run-case)
- 순서: 실행명 확보(N8) → 단위 K4 load_policy → 모델 설정(단위 I9, configs/model/) 읽기 → 단위 K3 open_snapshot(정본 빌드,
  읽기 전용) → 출처 종류 확인(합성·실자료. 실자료는 real_case_scope가 분할 기록으로 사례 계열이 real_dev인지 관측 값을
  읽기 전에 보고, 아니면(real_sealed 포함) 1로 거부한다. 실자료의 묶음은 real_dev, 비교 대상 집합은 g0. AS3 두 번째 PR)
  → 자료 묶음(RUN_CASE_DATASETS)과 비교 대상
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

evaluate 배선(로드맵 MT7 첫 PR, 최종 연결은 조립 작업 AS3. 결정 기록 model-decision-as3-evaluate)
- 자료 묶음은 --snapshot으로 정한다 `[해석]`: dev20 → dev20, controlled_fixture_v0 → controlled_fixture_v0,
  kcs_202201_202412_v2 → real_dev. 봉인 묶음(holdout40·real_sealed)은 evaluate가 돌리지 않는다(샌드박스 밖 실행기 E2의 일,
  F1 뒤). 사례 목록은 dev20은 정본 자리 eval/dev/dev20/input/cases.json(DT5)에서 읽는다. real_dev는 실행 때
  build_case_list(detect와 같은 길, real_dev 계열로 좁힌 뒤)로 경보 목록을 만들고 DT7 결정 기록의 규칙(select_real_dev_mvp)
  으로 20건을 고른다(파일을 쓰지 않는다). 경보 목록 전체는 실행 조건 입력 파일 snapshot.real_dev_alerts에, 고른 사례는
  planned_cases에 남는다. controlled_fixture_v0의 사례 목록 자리는 없어 실행 폴더를 만들기 전에 분명한 오류로 끝난다.
- 속도 조절(AS3 세 번째 PR): 모델 설정 configs/model/model.json의 pacing(evaluate_pacing, 모든 모드 같음)을 단위 E1에
  넘긴다. 쓴 값과 쉰 시간 합·429 뒤 쉰 횟수는 실행 조건 입력 파일 prescoring_checks.seed_concurrency에 적는다.
- 인프라 실패 재실행(룰북 B5)은 단위 E1이 묶음 끝에 한다. 실행 조건 입력 파일 prescoring_checks.final_status에 줄 없는
  조합 수와 재실행 대상·재실행 수를 적는다(값이 있으면 재실행 규칙을 적용한 묶음이다).
- 모드(사용자 결정 12(가)): --mode를 주지 않으면 단위 E1 PLANNED_MODES[자료 묶음]의 모드 전부를 한 묶음(순서 seed
  DEV_ORDER_SEED로 섞음, 동시성 1)으로 돈다. 주면 그 모드 하나만 돌고, 실행 조건 입력 파일의 planned_modes가 그 모드
  하나이며 reproduce_evaluate에 --mode가 남는다(스모크 표시). 채점기는 dev20·real_dev 묶음의 계획 모드가 정해진 모드 전부가
  아니면 채점하지 않으므로 점수표로 합쳐지지 않는다. 표준 오류에 스모크 알림 한 줄을 쓴다.
- 사례 실행 백엔드(EVALUATE_BACKEND, 기본 샌드박스): 샌드박스 백엔드(SandboxCaseRunner)는 사례마다 묶음(E1)이 호스트 쪽
  outputs/run_case-{시각}/을 확보하면(N8) `openshell sandbox exec`으로 채점 대상 실행 샌드박스(SCORED_SANDBOX) 안 run-case에
  --run-name으로 그 실행명을 넘기고, MT5 결정 기록 ④·⑯ 절차로 내려받아 실행 결과 기록을 돌려준다. 받지 못하면 그 사례는
  FAILED 줄(CODE_ERROR, harness:{예외 이름})로 분모에 남는다. 호스트 백엔드(host_case_runner)는 같은 프로세스에서 run-case와
  같은 조립(run_case_in → investigate_case)을 부른다(시험·스모크용, 점수표 근거 아님). 백엔드는 CLI 옵션·환경변수로 고르지
  않는다(계약 밖 이름을 만들지 않는다).
- 샌드박스 백엔드는 실행 폴더를 만들기 전에 사전 점검한다(sandbox_preflight): openshell 명령, 이미지 기록의 코드 커밋(dirty
  거짓), 그 커밋 = 호스트 code_version. 샌드박스 안 run-case의 code_version은 이미지 기록에서 온다(code_version 참고).
- 하위 프로세스는 샌드박스 백엔드의 openshell 호출뿐이다(_openshell: "openshell"로 시작하는 목록, 셸 없음, 키 변수와 봉인
  폴더 변수를 뺀 환경). 샌드박스 안에서 evaluate를 부르면 openshell이 없어 사전 점검에서 끝난다.
- --run-name(사용자 결정 10(나))이 있으면 그 이름의 묶음 실행 폴더를 이미 있으면 실패하는 방식으로 만들고 E1에 넘긴다.
- 순서: 사전 점검 → 단위 E1 execute_batch → 단위 E4 summarize_batch(NAT 사후 평가) → 실행 조건 입력 파일
  run_conditions-{시각}.json을 묶음 실행 폴더에 배타 생성(E1 write_run_conditions. 내려받기를 끝낸 호스트 쪽 프로그램이
  쓴다, 자료 계약 §8.2). 샌드박스 백엔드는 sandbox.name·sandbox.policy_yaml_sha256을, 두 백엔드 모두 reproduce_evaluate를
  더한다. 표준 출력에는 묶음 기록과 실행 조건 입력 파일의 outputs부터의 상대경로만 적는다. 사례 실행이 실패해도 묶음
  기록을 끝까지 썼으면 0이다(실패는 줄로 분모에 남는다).
- 운영자 실행 조건(--conditions-extra <JSON 상대 경로>, 결정 기록 model-decision-conditions-extra): 하네스가 채우지
  못하는 값(라이브 정책 조회 본문 sha256, 대조한 시험표 실행 폴더 이름, 스킬 호출 성공률, 채점기·산문 패턴 목록 커밋, 사전
  점검 결과, A등급 조건 등. 단위 E1 OPERATOR_CONDITION_KEYS·OPERATOR_SUBKEYS)을 운영자가 JSON 객체로 넘기면 실행 폴더를
  만들기 전에 읽고 검사하고(load_operator_conditions: 파일 없음·JSON 아님은 오류, 하네스 키·하위 키는 "두 번 줬다", 약속 밖
  키·로컬 절대경로 모양·키 모양 값은 거부), 값이 모두 모인 뒤 실행 조건 입력 파일에 합친다(E1 merge_operator_conditions.
  sandbox·prescoring_checks는 하네스 값에 하위 키를 더한다). reproduce_evaluate에 옵션과 경로를 그대로 적고, 표준 오류에
  합친 키 이름 목록(값 없음)을 한 줄 알린다. 채점기가 이미 읽는 키를 채우는 배관이며 채점 규칙은 바꾸지 않는다.
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

# evaluate 배선(위 "evaluate 배선"). 스냅샷 ID → 자료 묶음 `[해석]`, 사례 목록 자리, 개발 묶음 순서 seed.
EVALUATE_DATASETS = {"dev20": "dev20", "controlled_fixture_v0": "controlled_fixture_v0",
                     "kcs_202201_202412_v2": "real_dev"}
# 사례 목록 자리. dev20은 DT5의 정본 입력. real_dev는 로드맵 DT7 ①의 경보 목록 자리가 정해지면 더한다(그 전에는 분명한
# 오류). controlled_fixture_v0은 커밋된 입력 사례 목록이 없다(정답 파일 eval/dev/oracle_ABC.json을 입력으로 쓰지 않는다).
EVALUATE_CASE_LISTS = {"dev20": Path("eval") / "dev" / "dev20" / "input" / "cases.json"}
DEV_ORDER_SEED = "dev-order-v1"
# real_dev MVP 사례 고르기(DT7 결정 기록 docs/tracking/decisions/20260925-0925-data-decision-dt7-real-dev-mvp-selection.md
# "고르는 방법" ①~③). 목록 파일을 두지 않고 evaluate가 실행 때 경보 목록에서 다시 고른다.
REAL_DEV_MVP_PREFIX = "real_dev-mvp-20260925"
REAL_DEV_MVP_TAKE = 20
REAL_DEV_MVP_RULE = ("sha256(\"real_dev-mvp-20260925:\" + case_id) 오름차순 앞 20건(DT7 결정 기록 "
                     "20260925-0925-data-decision-dt7-real-dev-mvp-selection.md)")
# 사례 실행 백엔드(AS3 결정 기록 ③). 기본값은 샌드박스다: 채점 대상 실행은 채점 대상 실행 샌드박스 안에서 돈다(자료 계약
# §8.2·§10.3 방식 (나)). 호스트 백엔드(같은 프로세스에서 run_case_in을 부른다)는 시험과 스모크용이고 CLI 옵션·환경변수로
# 고르지 않는다(이 값을 바꿔 끼운다). 호스트에서 돈 묶음은 점수표 근거가 아니다(MT7 결정 기록 "AS3에 넘길 것" 3).
SANDBOX_BACKEND, HOST_BACKEND = "sandbox", "host"
EVALUATE_BACKEND = SANDBOX_BACKEND
SCORED_SANDBOX = "ts-scored"  # 개발 평가용 채점 대상 실행 샌드박스 이름(MT5 위반 시험표 artifacts/openshell/의 이름)
SANDBOX_CLI = "/opt/tradesentry/bin/tradesentry"  # 이미지 안 CLI 실행기(MT5 결정 기록 ⑧, configs/openshell/image/)
SANDBOX_OUTPUTS = "/sandbox/outputs"  # 샌드박스 쪽 실행 폴더의 부모(MT5 결정 기록 ③: exec 기본 작업 폴더 /sandbox)
SANDBOX_IMAGE_MANIFEST = "/opt/tradesentry/image_manifest.json"
SANDBOX_CHECK_TIMEOUT_S = 60  # 받기 전 확인·이미지 기록 읽기·내려받기 한 번의 제한 시간
SANDBOX_EXEC_MARGIN_S = 120  # 사례 실행 exec의 제한 시간 = 모델 설정의 사례당 wall time + 이 여유
CHILD_ENV_DROP = ("NVIDIA_API_KEY", "NVIDIA_INFERENCE_API_KEY", "DATA_GO_KR_SERVICE_KEY", "TRADESENTRY_SEALED_DIR")
OPENSHELL_POLICY_FILE = Path("configs") / "openshell" / "policy.yaml"  # 채점 대상 실행 샌드박스 정책(MT5 결정 기록 ①)


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


def reserve_given_run_dir(run_name: str, given: str) -> tuple[str, str, Path]:
    """호스트가 먼저 확보해 --run-name으로 넘긴 실행명의 실행 폴더를 만든다(사용자 결정 10(나)).

    이름이 N5 형식이고 실행 이름이 run_name이어야 한다(단위 F1이 이미 봤지만 다시 본다). OUTPUT_PARENT 아래에 그 이름의 폴더를
    이미 있으면 실패하는 방식(os.mkdir)으로 만들고, 다른 부모 폴더(OUTPUT_PARENT/sealed)에 같은 이름이 있으면 방금 만든 빈
    폴더를 지우고 실패한다. 다음 초로 넘어가지 않는다(이름은 호스트가 정했다). 오류 문장에는 받은 값을 넣지 않는다(N13).
    """
    if args.RUN_NAME_RE.fullmatch(given) is None or given.rsplit("-", 1)[0] != run_name:
        raise RunNameError(f"--run-name의 실행명이 이 명령의 실행명 형식({run_name}-{{시각}})이 아니다")
    parent = OUTPUT_PARENT
    parent.mkdir(parents=True, exist_ok=True)
    run_dir = parent / given
    try:
        os.mkdir(run_dir)
    except FileExistsError:
        raise RunNameError("--run-name의 실행 폴더가 이미 있다(덮어쓰지 않는다, 자료 계약 §10.3 N8)") from None
    if os.path.lexists(parent / SEALED_NAME / given):
        os.rmdir(run_dir)
        raise RunNameError("--run-name의 실행명이 outputs/sealed/에 이미 있다(자료 계약 §10.3 N8)")
    return given, given.rsplit("-", 1)[1], run_dir


def reserve_run_dir(run_name: str, *, given: str | None = None, clock: Callable[[], datetime] = now_kst,
                    sleep: Callable[[float], None] = time.sleep) -> tuple[str, str, Path]:
    """실행명을 확보하고 (실행명, 시각, 실행 폴더)를 돌려준다(자료 계약 §10.3 N8).

    given(--run-name 값)이 있으면 reserve_given_run_dir로 그 이름의 폴더만 만든다(사용자 결정 10(나)). 없으면 아래대로 CLI가
    확보한다.

    OUTPUT_PARENT 아래에 {실행 이름}-{yymmddhhmmss} 폴더를 이미 있으면 실패하는 방식(os.mkdir)으로 만든다. 그 이름의 초가 될
    때까지 기다린 뒤 만들고, 만든 뒤 다른 부모 폴더(OUTPUT_PARENT/sealed)에 같은 이름이 있으면 방금 만든 빈 폴더를 지우고
    다음 초로 넘어간다. 만들기에 실패해도 다음 초로 넘어간다. 개발 전용 공통 실행기(tradesentry.units)의 같은 규칙을 CLI 쪽에
    다시 둔 것이다(CLI는 tradesentry.units를 import하지 않는다). 런타임의 실행명 확보(단위 L2)와는 조립 점검(AS4)에서 합칠
    후보다.
    """
    if given is not None:
        return reserve_given_run_dir(run_name, given)
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


def json_output_bytes(domain: str, value: object) -> bytes:
    """출력 값의 JSON 바이트(들여쓰기 2, 한국어 그대로, Decimal은 글자 그대로의 문자열, 끝 줄바꿈). write_output과 봉인용
    탐지 입구(detect_dataset_cases)가 같이 쓴다. JSON으로 쓸 수 없으면 배선 계약 위반(4)이다."""
    try:
        return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False, default=_json_default)
                + "\n").encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise WiringError(f"{domain} 출력을 JSON으로 쓸 수 없다({type(exc).__name__})") from None


def write_output(run_dir: Path, run_id: str, domain: str, stamp: str, ext: str, value: object) -> str:
    """출력 값을 {도메인명}-{시각}.{확장자}로 쓰고 표준 출력에 적을 상대경로를 돌려준다.

    확장자는 json 하나다(JSON 값, Decimal은 글자 그대로의 문자열). 파일은 이미 있으면 실패하는 방식("xb")으로 쓴다.
    snapshot-build의 두 파일은 단위 S2가 직접 쓴다.
    """
    if ext != "json":
        raise WiringError(f"배선이 모르는 출력 확장자다({ext})")
    payload = json_output_bytes(domain, value)
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

    run_id, stamp, run_dir = reserve_run_dir("snapshot_build", given=request.run_name)
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

    run_id, stamp, run_dir = reserve_run_dir("snapshot_verify", given=request.run_name)
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
DETECT_SOURCE_KINDS = ("controlled", "real")  # 탐지하는 출처 종류(허용 목록). real은 real_dev 계열로 좁힌다
DETECT_DATASET = "real_dev"  # 실자료 detect의 묶음(고정. CLI 옵션을 두지 않는다, MT1 결정 ⑭)
# 실자료 스냅샷 ID → 분할 기록 정본 파일(저장소 루트 기준). 2026-09-25(금) 사용자 결정 8. 단위 V5 출력과 바이트가 같다.
REAL_SPLIT_FILES = {"kcs_202201_202412_v2": "data/reference/real_split_kcs_202201_202412_v2.json"}
REAL_SPLIT_KEYS = ("snapshot_id", "seed", "ratio", "method", "real_dev", "real_sealed")  # 단위 V5 출력 키(DT4 ①)
CASE_BUILD_KEYS = frozenset({"snapshot_id", "dataset", "policy_version", "cases", "data_quality"})  # 단위 P2 출력 키
DETECT_REFUSAL = ("오류: tradesentry detect는 합성 스냅샷(source_kind가 controlled)과 실자료 스냅샷(real)만 탐지한다. 이 "
                  "스냅샷의 출처 종류는 둘 다 아니어서 지표를 계산하지 않고 끝냈다.")
DETECT_SPLIT_REFUSAL = ("오류: tradesentry detect가 이 실자료 스냅샷의 분할 기록을 읽지 못했거나, 기록이 스냅샷의 계열과 맞지 "
                        "않는다(SplitError). 실자료는 data/reference/ 아래 분할 기록 정본 파일의 real_dev 계열로만 탐지하므로 "
                        "지표를 계산하지 않고 끝냈다.")


class SplitError(Exception):
    """실자료 분할 기록을 쓸 수 없다(대응표에 없는 스냅샷, 파일 없음, 모양이 틀림, 스냅샷 계열과 다름). 문장에 값을 넣지 않는다."""


def load_real_split(snap) -> dict[tuple[str, str], str]:
    """실자료 스냅샷의 분할 기록을 읽어 계열 (HS6, 상대국) → 묶음(real_dev/real_sealed) 표를 돌려준다.

    K3로 관측 값을 읽기 전에 부른다. 읽는 것은 분할 기록 파일과, K3가 열 때 읽은 메타(수집 설정의 HS6·상대국)뿐이다.
    기록의 키는 단위 V5 출력 키 여섯 개, snapshot_id는 이 스냅샷, 두 묶음은 겹치지 않고 합이 스냅샷의 계열 전체와 같아야
    한다. 하나라도 어긋나면 SplitError다.
    """
    from tradesentry.contract import types
    from tradesentry.dal import query
    from tradesentry.policy import trigger

    relative = REAL_SPLIT_FILES.get(snap.snapshot_id)
    if relative is None:
        raise SplitError("이 실자료 스냅샷에는 분할 기록 정본 파일이 없다")
    try:
        record = json.loads((query.REPO_ROOT / relative).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SplitError(f"분할 기록 파일을 읽지 못했다({type(exc).__name__})") from None
    if not isinstance(record, dict) or tuple(record) != REAL_SPLIT_KEYS or record["snapshot_id"] != snap.snapshot_id:
        raise SplitError("분할 기록의 키가 단위 V5 출력 키가 아니거나 snapshot_id가 이 스냅샷이 아니다")
    table: dict[tuple[str, str], str] = {}
    for dataset in (DETECT_DATASET, "real_sealed"):
        items = record[dataset]
        if not isinstance(items, list) or not items:
            raise SplitError(f"분할 기록의 {dataset}가 비어 있지 않은 목록이 아니다")
        for item in items:
            if not isinstance(item, dict) or set(item) != {"hs6", "partner"} \
                    or not isinstance(item["hs6"], str) or not trigger.HS6_RE.match(item["hs6"]) \
                    or not isinstance(item["partner"], str) or not trigger.PARTNER_RE.match(item["partner"]) \
                    or item["partner"] == types.ALL_PARTNER:
                raise SplitError(f"분할 기록의 {dataset} 항목이 hs6·partner 객체가 아니다")
            key = (item["hs6"], item["partner"])
            if key in table:
                raise SplitError("분할 기록에 같은 계열이 두 번 있다")
            table[key] = dataset
    if set(table) != set(detect_series(snap)):
        raise SplitError("분할 기록의 계열이 스냅샷의 계열(수집 설정의 HS6 × 상대국)과 다르다")
    return table


def series_assignment(table: dict[tuple[str, str], str]) -> list[dict]:
    """분할 표 → 단위 P2의 series_assignment([{hs6, partner, dataset}], 계열 순)."""
    return [{"hs6": hs6, "partner": partner, "dataset": table[(hs6, partner)]} for hs6, partner in sorted(table)]


def detect_pairs(months: tuple[str, ...] | list[str]) -> list[tuple[str, str]]:
    """스냅샷 기간의 달에서 (비교월 t, 기준월 t−12) 쌍. 기준월도 기간 안인 비교월만, 달 순서대로."""
    from tradesentry.policy import trigger

    present = set(months)
    return [(month, trigger.baseline_of(month)) for month in months if trigger.baseline_of(month) in present]


def detect_series(snap, split: dict[tuple[str, str], str] | None = None,
                  dataset: str = DETECT_DATASET) -> list[tuple[str, str]]:
    """탐지할 계열 (HS6, 상대국): 수집 설정의 HS6 × 상대국. 비교국 표가 가리키는 계획 밖 국가는 넣지 않는다.

    split(load_real_split의 표)을 주면 그 가운데 묶음 dataset의 계열만 남긴다. dataset의 기본값은 real_dev이고 CLI detect는
    이 값만 쓴다. real_sealed는 봉인용 탐지 입구(detect_dataset_cases)만 넘긴다. 관측 값은 읽지 않는다(메타만 쓴다).
    """
    series = [(hs6, partner) for hs6 in snap.hs6_codes for partner in snap.partners]
    if split is None:
        return series
    return [key for key in series if split.get(key) == dataset]


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
    detect(탐지 계열 전체. 실자료는 real_dev 계열)와 run-case(사례의 계열 하나, 조립 작업 AS2)가 같이 쓴다.
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


def detection_rows(snap, series: list[tuple[str, str]] | None = None) -> list[dict]:
    """계열·비교월마다 단위 X1·X2를 불러 단위 P1의 입력 행을 만든다(행 하나는 detection_row). series가 없으면
    detect_series(snap) 전체다. 실자료는 _detect가 real_dev로 좁힌 계열을 넘긴다(관측 값을 읽기 전에 좁힌다).

    K3는 계열마다 parent_series, HS6마다 world_series를 한 번씩 부르고, ALL 행은 HS6·달마다 한 번만 다시 만든다.
    """
    pairs = detect_pairs(snap.months)
    if not pairs:
        return []
    months = sorted({month for pair in pairs for month in pair})
    worlds: dict[str, dict[str, list[dict]]] = {}
    rows: list[dict] = []
    for hs6, partner in (detect_series(snap) if series is None else series):
        if hs6 not in worlds:
            worlds[hs6] = {value["month"]: world_rows(snap, value) for value in snap.world_series(hs6, months)}
        world = worlds[hs6]
        parent = {value["month"]: parent_rows(value) for value in snap.parent_series(hs6, partner, months)}
        rows += [detection_row(snap.snapshot_id, hs6, partner, month, baseline, parent, world)
                 for month, baseline in pairs]
    return rows


def build_case_list(snap, policy: dict, dataset: str = DETECT_DATASET) -> object:
    """스냅샷 하나의 경보 사례 목록(단위 P2 출력). detect와 evaluate(real_dev 사례 목록, AS3 두 번째 PR)와 봉인용 탐지
    입구(detect_dataset_cases, AS1 세 번째 PR)가 같이 쓴다.

    실자료는 분할 기록(load_real_split)을 먼저 읽어 묶음 dataset의 계열만 남긴 뒤에 관측 값을 읽는다(병렬 개발 규칙 §7.2의
    5). dataset의 기본값은 real_dev이고 detect·evaluate는 이 값만 쓴다. real_sealed는 봉인용 탐지 입구만 넘긴다. 분할 기록을
    쓸 수 없으면 SplitError(관측 값을 읽기 전). 출처 종류 확인은 부르는 쪽이 먼저 한다.
    """
    from tradesentry.policy import case_build, trigger

    case_input: dict[str, object] = {"snapshot_id": snap.snapshot_id, "source_kind": snap.source_kind}
    split = None
    if snap.source_kind == "real":  # 값을 읽기 전에 묶음 계열로 좁힌다
        split = load_real_split(snap)
        case_input.update(dataset=dataset, series_assignment=series_assignment(split))
    rows = detection_rows(snap, detect_series(snap, split, dataset))
    detection = trigger.run({"policy": policy, "rows": rows})
    return case_build.run({**case_input, "detection": detection})


def _detect(request: args.Request) -> int:
    """detect: 조립체 2(단위 X1·X2·X4·P1·P2)를 불러 단위 P2의 출력(사례 목록·데이터 품질 목록)을 실행 폴더에 쓴다(위 "탐지
    명령 detect")."""
    # 명령을 부를 때만 import한다(도움말·인자 오류는 조립체를 불러오지 않는다). 모듈 속성으로 불러 시험 대역이 걸리게 한다.
    from tradesentry.contract import policy_load
    from tradesentry.dal import query

    run_id, stamp, run_dir = reserve_run_dir(DETECT_RUN_NAME, given=request.run_name)
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
            try:
                result = build_case_list(snap, policy)
            except SplitError:
                _report(DETECT_SPLIT_REFUSAL)
                return EXIT_FAILED
    except query.SnapshotError:
        _report("오류: tradesentry detect가 스냅샷을 열지 못했거나 스냅샷 자료가 행 규칙에 맞지 않는다(SnapshotError). "
                "--snapshot의 정본 빌드(data/snapshots/ 아래 snapshot_build.sqlite)를 확인한다.")
        return EXIT_FAILED
    if not isinstance(result, dict) or set(result) != CASE_BUILD_KEYS:
        raise WiringError("단위 P2(case_build)의 출력이 snapshot_id·dataset·policy_version·cases·data_quality 객체가 아니다")
    _emit(write_output(run_dir, run_id, DETECT_DOMAIN, stamp, "json", result))
    return EXIT_OK


# ------------------------------------------------------------------------------ 봉인용 탐지 입구(조립 작업 AS1 세 번째 PR)
# 결정 기록 docs/tracking/decisions/20260925-1250-model-decision-as1-sealed-entry.md. CLI 명령이 아니라 파이썬 함수 하나다
# (명령 표는 공용 약속이라 옵션을 더하지 않는다). 부르는 쪽은 로드맵 DT7 ③의 격리된 생성 에이전트(단위 V6)다.
ENTRY_DATASETS = ("real_dev", "real_sealed")  # 입구가 받는 묶음(자료 계약 §4.2의 실자료 두 묶음)


class DatasetEntryError(Exception):
    """봉인용 탐지 입구가 탐지하지 않고 끝내는 까닭(묶음·출력 폴더·출처 종류·출력 모양). 문장에 받은 값·경로를 넣지 않는다(N13)."""


def _git_common_dir(root: Path) -> Path | None:
    """작업 폴더 root의 git 공용 폴더(.git이 폴더면 그것, worktree의 .git 파일이면 gitdir → commondir). 없으면 None."""
    git = root / ".git"
    if git.is_dir():
        return git
    if not git.is_file():
        return None
    pointer = git.read_text(encoding="utf-8").strip()
    if not pointer.startswith("gitdir:"):
        return None
    gitdir = Path(pointer[len("gitdir:"):].strip())
    gitdir = gitdir if gitdir.is_absolute() else root / gitdir
    if (gitdir / "commondir").is_file():
        common = Path((gitdir / "commondir").read_text(encoding="utf-8").strip())
        return (common if common.is_absolute() else gitdir / common).resolve()
    return gitdir.resolve()


def _repo_roots() -> list[Path]:
    """출력 폴더로 받지 않는 저장소 뿌리: 이 코드의 작업 폴더(dal.query.REPO_ROOT), 본 작업 폴더(공용 폴더 .git의 부모), git이
    아는 모든 worktree(한 저장소에서 브랜치마다 따로 여는 작업 폴더. 공용 폴더의 worktrees/*/gitdir가 가리키는 .git 파일의
    부모). `git worktree list --porcelain`이 읽는 것과 같은 메타 파일이다. 이 모듈의 하위 프로세스는 openshell 호출뿐이라
    git을 부르지 않고 파일을 읽는다(시험이 그 명령의 목록과 같음을 확인한다). 경로를 돌려주고, 정체성 비교는 부르는 쪽이 한다.
    """
    from tradesentry.dal import query

    root = Path(query.REPO_ROOT)
    roots = [root]
    try:
        common = _git_common_dir(root)
        if common is not None:
            if common.name == ".git":
                roots.append(common.parent)
            listing = common / "worktrees"
            for entry in sorted(listing.iterdir()) if listing.is_dir() else []:
                pointer = entry / "gitdir"
                if pointer.is_file():
                    target = Path(pointer.read_text(encoding="utf-8").strip())
                    target = target if target.is_absolute() else entry / target
                    roots.append(target.parent)
    except (OSError, UnicodeError):
        pass
    unique: list[Path] = []
    for item in roots:
        if item not in unique:
            unique.append(item)
    return unique


def _repo_identities() -> set[tuple[int, int]]:
    """저장소 뿌리마다 파일 정체성 (st_dev, st_ino). 없는 뿌리(지운 worktree)는 건너뛴다. 이 코드의 작업 폴더는 반드시 있다."""
    found = set()
    for root in _repo_roots():
        try:
            info = os.stat(root)
        except OSError:
            continue
        found.add((info.st_dev, info.st_ino))
    return found


def _entry_out_dir(out_dir: object) -> tuple[Path, tuple[int, int]]:
    """부르는 쪽이 준 출력 폴더를 확인하고 (실제 위치, 그 폴더의 (st_dev, st_ino))를 돌려준다. 봉인 폴더나 저장소 밖 임시 폴더만
    받는다(병렬 개발 규칙 §7.3의 1, 자료 계약 §10.3 N10).

    이미 있는 폴더여야 하고(만들지 않는다), 그 폴더와 모든 상위 폴더 가운데 하나라도 저장소 뿌리(_repo_roots)와 파일
    정체성 (st_dev, st_ino)가 같으면 거부한다. 경로 글자로 비교하지 않으므로 대소문자를 바꾼 경로(대소문자를 구별하지 않는
    파일 시스템), macOS firmlink(/System/Volumes/Data 아래의 같은 폴더), 심볼릭 링크, 상대경로·..가 같은 폴더로 판정된다.
    """
    if not isinstance(out_dir, (str, os.PathLike)):
        raise DatasetEntryError("출력 폴더는 경로여야 한다")
    try:
        resolved = Path(out_dir).resolve(strict=True)
        if not resolved.is_dir():
            raise DatasetEntryError("출력 폴더가 폴더가 아니다")
        chain = [os.stat(folder) for folder in (resolved, *resolved.parents)]
    except (OSError, RuntimeError):
        raise DatasetEntryError("출력 폴더가 없다(입구는 폴더를 만들지 않는다)") from None
    repo = _repo_identities()
    if not repo or any((info.st_dev, info.st_ino) in repo for info in chain):
        raise DatasetEntryError("출력 폴더가 저장소 안이다(봉인 폴더나 저장소 밖 임시 폴더만 받는다)")
    return resolved, (chain[0].st_dev, chain[0].st_ino)


def _write_all(fd: int, payload: bytes) -> None:
    """파일 기술자에 바이트를 끝까지 쓴다."""
    view = memoryview(payload)
    while view:
        view = view[os.write(fd, view):]


def _write_entry_file(out_dir: object, identity: tuple[int, int], name: str, payload: bytes) -> None:
    """쓰기 직전에 출력 폴더를 다시 확인하고(_entry_out_dir), 처음 확인한 폴더와 정체성이 같을 때만 그 폴더를 열어(dir_fd)
    배타 생성(O_CREAT|O_EXCL|O_NOFOLLOW)으로 파일 하나를 쓴다. 쓰다 실패하면 그 파일을 지운다."""
    folder, again = _entry_out_dir(out_dir)
    if again != identity:
        raise DatasetEntryError("출력 폴더가 확인한 뒤 바뀌었다")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    dir_fd = os.open(folder, flags)
    try:
        opened = os.fstat(dir_fd)
        if (opened.st_dev, opened.st_ino) != identity:
            raise DatasetEntryError("출력 폴더가 확인한 뒤 바뀌었다")
        try:
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o644, dir_fd=dir_fd)
        except FileExistsError:
            raise DatasetEntryError("출력 폴더에 같은 이름의 파일이 이미 있다(덮어쓰지 않는다)") from None
        try:
            try:
                _write_all(fd, payload)
            finally:
                os.close(fd)
        except BaseException:
            os.unlink(name, dir_fd=dir_fd)  # 쓰다 만 파일을 남기지 않는다
            raise
    finally:
        os.close(dir_fd)


def detect_dataset_cases(snapshot_id: str, policy_version: str, dataset: str, out_dir) -> dict:
    """봉인용 탐지 입구: 실자료 스냅샷에서 묶음 dataset(real_dev·real_sealed)의 계열로만 경보 사례 목록을 만들어, 부르는 쪽이
    준 폴더 out_dir에 단위 P2 출력 그대로 한 파일(policy_case_build-{시각}.json)을 쓴다.

    - 경로는 CLI detect의 실자료 경로와 같다: K4 load_policy → K3 open_snapshot(정본 빌드, 읽기 전용) → 출처 종류 real 확인 →
      build_case_list(snap, policy, dataset): 분할 기록(load_real_split) → detect_series로 그 묶음 계열만 남긴다(관측 값을 읽기
      전) → detection_rows(K3 조회 → X1·X2) → P1 → P2(dataset과 분할 기록 전체의 배정). dataset이 real_dev면 출력 바이트가
      CLI detect의 출력 파일과 같다.
    - 출력은 out_dir 하나에만 쓴다. outputs/에는 아무것도 쓰지 않고 실행명도 확보하지 않는다(자료 계약 §10.3 N10 "봉인 자료
      생성 중의 명령 출력"). out_dir은 이미 있는 폴더여야 하고, 그 폴더나 상위 폴더가 저장소 뿌리(본 작업 폴더와 git이 아는
      모든 worktree)와 파일 정체성이 같으면 거부한다(_entry_out_dir). 봉인 폴더 위치(TRADESENTRY_SEALED_DIR)는 이 함수가
      읽지 않는다. 부르는 쪽이 정한다.
    - 확인을 모두 마치고 출력 바이트를 다 만든 뒤, 쓰기 직전에 출력 폴더를 다시 확인하고 처음과 같은 폴더를 열어 파일 하나를
      배타 생성(O_EXCL)으로 쓴다. 실패하면 파일을 남기지 않는다(봉인 폴더에 목록 밖 파일이 생기지 않게). 표준 출력·표준
      오류에 아무것도 쓰지 않는다.
    - 부르는 쪽 신원으로 real_sealed 호출을 막지 않는다(같은 OS 사용자 권한으로는 막을 수 없다, 병렬 개발 규칙 §6.4·§7.2 끝).
      real_sealed로는 격리된 봉인 생성 에이전트(로드맵 DT7 ③)만 부른다(결정 기록의 "한계와 운용 규칙").
    - 출력 파일에는 code_version을 넣지 않는다(P2 출력 키 다섯 개 그대로. AS1 두 번째 기록 ⑤). 돌려주는 값에 그 커밋을 담아
      부르는 쪽이 결정 기록에 적게 한다. code_version은 작업 트리의 고치지 않은 변경을 표시하지 않는다.
    - 오류는 예외로 알린다: DatasetEntryError(묶음·출력 폴더·출처 종류·출력 모양), policy_load.PolicyError, query.SnapshotError,
      SplitError, WiringError. 문장에 받은 값과 경로를 넣지 않는다(N13).

    돌려주는 값: {"file_name": 쓴 파일 이름(out_dir 기준), "code_version": 탐지 코드의 git 커밋}.
    """
    from tradesentry.contract import policy_load
    from tradesentry.dal import query

    if dataset not in ENTRY_DATASETS:  # 스냅샷·정책을 열기 전에 확인한다
        raise DatasetEntryError("묶음은 real_dev나 real_sealed여야 한다")
    _, identity = _entry_out_dir(out_dir)
    policy = policy_load.load_policy(policy_version)
    with query.open_snapshot(snapshot_id) as snap:
        if snap.source_kind != "real":  # 분할 기록이 있는 실자료만. 값을 읽기 전에 거부한다
            raise DatasetEntryError("봉인용 탐지 입구는 실자료 스냅샷(source_kind가 real)만 탐지한다")
        result = build_case_list(snap, policy, dataset)  # detect와 같은 조립. 분할 기록은 관측 값을 읽기 전(SplitError)
    if not isinstance(result, dict) or set(result) != CASE_BUILD_KEYS or result["dataset"] != dataset:
        raise WiringError("단위 P2(case_build)의 출력이 요청한 묶음의 snapshot_id·dataset·policy_version·cases·data_quality "
                          "객체가 아니다")
    payload = json_output_bytes(DETECT_DOMAIN, result)
    version = code_version()
    name = f"{DETECT_DOMAIN}-{now_kst().strftime(STAMP_FORMAT)}.json"
    _write_entry_file(out_dir, identity, name, payload)
    return {"file_name": name, "code_version": version}


# ------------------------------------------------------------------------------ run-case(조립체 3, 조립 작업 AS2)
RUN_CASE_RUN_NAME = "run_case"  # 실행 이름(N5)
RUN_CASE_SOURCE_KINDS = ("controlled", "real")  # 조사하는 출처 종류(허용 목록). real은 real_dev 계열의 사례만(AS3 두 번째 PR)
# 합성 스냅샷 → 실행 결과 기록의 dataset(자료 계약 §4.2·§8.1). 표에 없는 합성 스냅샷은 묶음을 정할 수 없어 거부한다
# (dev20 스냅샷 ID가 정해지면 이 표에 한 줄을 더한다).
RUN_CASE_DATASETS = {"controlled_fixture_v0": "controlled_fixture_v0", "dev20": "dev20"}  # dev20: DT5 스냅샷 ID(AS3)
REAL_GROUPING_VERSION = "g0"  # 실자료의 비교 대상 집합(MVP까지 g0, DT7 최종 빌드와 같다)
RUN_RECORD_DOMAIN = "runlog_run_record"  # 실행 결과 기록을 만드는 단위 L2의 도메인명(UNITS.md §3.13, N4·N6)
RUN_RECORD_MAX_BYTES = 1 << 20  # 샌드박스에서 받은 실행 결과 기록을 읽는 크기 상한
REPORT_DOMAIN = "reports_render_ko"  # 최종 보고서를 만드는 단위 R2의 도메인명(UNITS.md §3.7)
NAT_DOMAIN = "workflow_nat_wrap"  # NAT 추적·프로파일 N7 폴더(단위 I13)
UNKNOWN_CODE_VERSION = "unknown"  # git 메타와 이미지 기록을 모두 읽을 수 없을 때의 code_version
IMAGE_MANIFEST = "image_manifest.json"  # 샌드박스 이미지 기록(앱 뿌리 바로 아래, MT5 결정 기록 ⑧)
IMAGE_MANIFEST_MAX_BYTES = 1 << 20
PEER_ROW_SCAN_MAX = 100_000  # 비교국 표의 grouping_version을 읽을 때 훑는 rowid 상한
# 반올림 불안정(U4). 2026-09-25(금) 08:41 사용자 결정(policy_v1 승인, U4 → HOLD 채택)으로 켰다. 규칙은 rounding_unstable,
# 결정 기록 docs/tracking/decisions/20260925-0846-user-decision-policy-v1-approval.md. 끄는 곳도 이 한 줄이다.
ROUNDING_UNSTABLE_ENABLED = True
# 자료 교정 뒤 동결 정책으로 경보 해소(MT2 결정 ⑪). 동결 스냅샷 하나로 도는 v1 실행에서는 만드는 쪽이 없어 늘 거짓이다.
RESOLVED_AFTER_CORRECTION = False
# 점유율 comparability_issues 값(이 조립이 정했다, 잠정): 전체국가(ALL) 분모 금액이 대상국 금액보다 작은 달. "{이름}:{달}".
DENOMINATOR_BELOW_PARTNER = "denominator_below_partner"
GAP_STATUSES = ("REQUEST_FAILED", "NOT_COLLECTED", "UNRESOLVED_ZERO")  # 빠진 관측으로 보는 상태(P3와 같다)
RUN_CASE_REFUSAL = ("오류: tradesentry run-case는 합성 스냅샷(source_kind가 controlled)과 실자료 스냅샷(real)만 조사한다. "
                    "이 스냅샷의 출처 종류는 둘 다 아니어서 관측 값을 읽지 않고 끝냈다.")
RUN_CASE_SPLIT_REFUSAL = ("오류: tradesentry run-case가 이 실자료 스냅샷의 분할 기록을 읽지 못했거나 기록이 스냅샷의 계열과 맞지 "
                          "않는다(SplitError). 관측 값을 읽지 않고 끝냈다.")
RUN_CASE_SEALED_REFUSAL = ("오류: tradesentry run-case는 실자료에서 분할 기록의 real_dev 계열 사례만 조사한다. 이 사례의 계열은 "
                           "real_dev가 아니어서(real_sealed 포함) 관측 값을 읽지 않고 끝냈다(병렬 개발 규칙 §7.2의 5).")


class RunCaseError(Exception):
    """run-case가 사례를 조사하지 않고 끝내는 까닭(종료 코드 1). 문장에는 받은 값·스냅샷 안의 값을 넣지 않는다(N13)."""


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
    if isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit) and version.get("dirty") is False:
        return commit
    return UNKNOWN_CODE_VERSION


def code_version(root: Path | None = None) -> str:
    """실행한 코드의 git 커밋 해시(자료 계약 §8.1 code_version). 하위 프로세스 없이 git 메타 파일을 읽는다.

    작업 폴더(git worktree)의 .git 파일(gitdir)과 commondir, packed-refs를 따른다. git 메타를 읽을 수 없으면(샌드박스 이미지)
    이미지 기록의 커밋(image_code_version)을 쓴다. 둘 다 없거나 40자 16진수가 아니면 UNKNOWN_CODE_VERSION이다. 경로는
    돌려주지 않는다(N13). 작업 트리의 고치지 않은 변경은 표시하지 않는다.
    """
    root = Path(__file__).resolve().parents[3] if root is None else Path(root)
    found = _git_code_version(root)
    return found if found != UNKNOWN_CODE_VERSION else image_code_version(root)


def _git_code_version(root: Path) -> str:
    """git 메타 파일에서 읽은 커밋(code_version의 첫 출처)."""

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


def real_case_scope(snap, case_arg: str) -> dict:
    """실자료 사례의 묶음 확인(관측 값을 읽기 전). 분할 기록(load_real_split)으로 --case 계열 (HS6, 상대국)이 real_dev인지
    본다. 아니면(real_sealed·기록에 없음) RunCaseError. 돌려주는 값은 단위 P2에 더할 입력(dataset=real_dev,
    series_assignment)이다. 읽는 것은 분할 기록 파일과 스냅샷 메타뿐이다(병렬 개발 규칙 §7.2의 5)."""
    from tradesentry.policy import case_build

    try:
        split = load_real_split(snap)
    except SplitError:
        raise RunCaseError(RUN_CASE_SPLIT_REFUSAL) from None
    try:
        wanted = case_build.parse_case_id(case_arg)
    except ValueError:
        raise RunCaseError("오류: tradesentry run-case의 --case가 사례 식별자 형식({hs6}-{partner}-{month})이 아니다.") from None
    if split.get((wanted["hs6"], wanted["partner"])) != DETECT_DATASET:
        raise RunCaseError(RUN_CASE_SEALED_REFUSAL)
    return {"dataset": DETECT_DATASET, "series_assignment": series_assignment(split)}


def rebuild_case(snap, policy: dict, case_arg: str, case_input: dict | None = None) -> dict:
    """--case(case_id `{hs6}-{partner}-{month}`)의 사례를 스냅샷과 정책으로 다시 만든다(탐지와 같은 길: K3 → 어댑터 → X1·X2 →
    P1 → P2). 그 계열·비교월 하나만 계산한다(다른 계열의 지표를 만들지 않는다). 사례가 아니면 RunCaseError다.
    돌려주는 값은 사례 객체의 8필드(자료 계약 §2.3.5, P2의 scope는 뗀다)다. 실자료는 case_input(real_case_scope의 dataset·
    series_assignment)을 P2에 더한다."""
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
    built = case_build.run({"snapshot_id": snap.snapshot_id, "source_kind": snap.source_kind, "detection": detection,
                            **(case_input or {})})
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


def run_case_in(request: args.Request, run_id: str, stamp: str, run_dir: Path) -> tuple[dict, list[str]]:
    """확보한 빈 실행 폴더(run_dir)에서 사례 1건을 조사하고 출력 파일을 쓴다. run-case 처리 함수와 evaluate의 호스트 백엔드
    (host_case_runner)가 같이 쓴다(AS2 결정 기록 "AS3" 항목: investigate_case 배선을 그대로 써서 필수 조회·초안 차례·
    참고값 세 포트가 켜진다).

    돌려주는 값: (실행 쪽 키 21개, 표준 출력에 적을 상대경로 목록: trace·NAT 폴더·실행 결과 기록·보고서(있을 때)).
    정책(PolicyError)·모델 설정(ConfigError)·스냅샷(SnapshotError·ScopeError)을 읽지 못하거나 사례가 아니면(RunCaseError)
    예외를 낸다. 예외 문장에는 받은 값·스냅샷 안의 값을 넣지 않는다(N13).
    """
    # 명령을 부를 때만 import한다(도움말·인자 오류는 조립체를 불러오지 않는다). 모듈 속성으로 불러 시험 대역이 걸리게 한다.
    from tradesentry.contract import policy_load
    from tradesentry.dal import query
    from tradesentry.workflow import model_client

    policy = policy_load.load_policy(request.policy_version)
    model_client.load_model_config()
    with query.open_snapshot(request.snapshot_id) as snap:
        if snap.source_kind not in RUN_CASE_SOURCE_KINDS:  # 관측 값을 읽기 전에 거부한다(머리 설명)
            raise RunCaseError(RUN_CASE_REFUSAL)
        if snap.source_kind == "real":
            # 실자료: 사례 계열이 분할 기록의 real_dev인지 관측 값을 읽기 전에 본다(아니면 거부). 도구의 조회 범위(비교국·
            # 전체국가 분모)는 좁히지 않는다(병렬 개발 규칙 §7.2의 5). dataset은 real_dev, 비교 대상 집합은 g0(AS2 ⑩).
            case_input = real_case_scope(snap, request.case)
            dataset, grouping_version = DETECT_DATASET, REAL_GROUPING_VERSION
        else:
            case_input = None
            dataset = RUN_CASE_DATASETS.get(snap.snapshot_id)
            if dataset is None:
                raise RunCaseError("오류: tradesentry run-case가 이 합성 스냅샷의 자료 묶음(dataset)을 정하지 못했다"
                                   "(RUN_CASE_DATASETS에 없다).")
            grouping_version = snapshot_grouping_version(snap)
        case = rebuild_case(snap, policy, request.case, case_input)
        outcome = investigate_case(snap, policy, case, request, run_id, stamp, run_dir, dataset=dataset,
                                   grouping_version=grouping_version)
    record, report = outcome["record"], outcome["report"]
    shown = [outcome["trace"], outcome["nat"], _write_json(run_dir, run_id, RUN_RECORD_DOMAIN, stamp, record)]
    if report is not None:
        shown.append(_write_json(run_dir, run_id, REPORT_DOMAIN, stamp, report))
    return record, shown


def _run_case(request: args.Request) -> int:
    """run-case: 조립체 3으로 사례 1건을 조사해 실행 폴더에 trace·NAT 추적·실행 결과 기록·보고서를 쓴다(머리 설명 "사례
    조사 명령 run-case"). --run-name이 있으면 호스트가 확보한 그 실행명을 쓴다(사용자 결정 10(나))."""
    from tradesentry.contract import policy_load
    from tradesentry.dal import query
    from tradesentry.runlog import cause_codes
    from tradesentry.workflow import model_client

    run_id, stamp, run_dir = reserve_run_dir(RUN_CASE_RUN_NAME, given=request.run_name)
    try:
        record, shown = run_case_in(request, run_id, stamp, run_dir)
    except policy_load.PolicyError:
        _report("오류: tradesentry run-case가 --policy의 정책을 읽지 못했다(PolicyError). "
                "정책 버전 이름과 configs/의 정책 파일을 확인한다.")
        return EXIT_FAILED
    except model_client.ConfigError:
        _report("오류: tradesentry run-case가 모델 설정(configs/model/)을 읽지 못했다(ConfigError).")
        return EXIT_FAILED
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
    for line in shown:
        _emit(line)
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


def evaluate_versions(request: args.Request, dataset: str) -> dict:
    """묶음의 버전 키 5개(단위 E1 VERSION_KEYS). 정책·스냅샷은 요청, 룰북은 커널 K1, 비교 대상 집합은 스냅샷(합성은 비교국
    표 행의 값, 실자료는 REAL_GROUPING_VERSION), 코드는 code_version()이다. 샌드박스 백엔드는 code_version을 이미지 기록과
    대조한다(sandbox_preflight)."""
    from tradesentry.contract import types
    from tradesentry.dal import query

    with query.open_snapshot(request.snapshot_id) as snap:
        grouping = snapshot_grouping_version(snap) if snap.source_kind in RUN_CASE_SOURCE_KINDS \
            else REAL_GROUPING_VERSION
    return {"policy_version": request.policy_version, "rulebook_version": types.RULEBOOK_VERSION,
            "snapshot_id": request.snapshot_id, "grouping_version": grouping, "code_version": code_version()}


def host_case_runner(call) -> dict:
    """호스트 백엔드의 사례 실행 함수(단위 E1 CaseCall → 실행 쪽 키 21개). 묶음이 확보한 사례 실행 폴더에서 run_case_in을
    부른다(실행명을 다시 확보하지 않는다). 사례를 조사하지 못하면 예외를 내고, 묶음이 그 사례를 FAILED 줄로 남긴다."""
    request = args.Request(command="run-case", snapshot_id=call.versions["snapshot_id"],
                           policy_version=call.versions["policy_version"], mode=call.mode, case=call.case["case_id"],
                           run_name=call.run_id)
    record, _ = run_case_in(request, call.run_id, call.stamp, call.run_dir)
    return record


# ------------------------------------------------------------------------------ 샌드박스 백엔드(AS3 결정 기록 ③~⑥)
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


def _child_env() -> dict:
    """openshell 하위 프로세스 환경: 키 변수와 봉인 폴더 변수를 뺀다(값을 읽지 않고 이름으로만 거른다)."""
    return {key: value for key, value in os.environ.items() if key not in CHILD_ENV_DROP}


def _openshell(argv: list, timeout: float):
    """openshell 하위 프로세스를 부른다. argv는 "openshell"로 시작하는 목록이다(셸을 쓰지 않는다). 부를 수 없거나 제한
    시간을 넘으면 None, 아니면 subprocess.CompletedProcess."""
    import subprocess

    if not argv or argv[0] != "openshell":
        raise WiringError("openshell 하위 프로세스는 openshell로 시작하는 목록으로만 부른다")
    try:
        return subprocess.run(argv, capture_output=True, timeout=timeout, env=_child_env(), stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return None


def sandbox_preflight(sandbox: str, host_code_version: str) -> str | None:
    """샌드박스 백엔드의 사전 점검(실행 폴더를 만들기 전). 문제가 없으면 None, 있으면 오류 문장.

    1) openshell 명령이 있는가 2) 이미지 기록(SANDBOX_IMAGE_MANIFEST)의 code_version.git_commit이 40자 16진수이고 dirty가
    거짓인가 3) 그 커밋이 호스트 code_version과 같은가(다르면 사례 기록의 code_version이 묶음 값과 달라 모든 줄이 실패한다).
    """
    import shutil

    if shutil.which("openshell") is None:
        return ("오류: tradesentry evaluate의 샌드박스 백엔드가 openshell 명령을 찾지 못했다. evaluate는 호스트에서 "
                "부르고, 사례는 채점 대상 실행 샌드박스 안에서 돈다.")
    done = _openshell(["openshell", "sandbox", "exec", "-n", sandbox, "--timeout", str(SANDBOX_CHECK_TIMEOUT_S), "--",
                       "cat", SANDBOX_IMAGE_MANIFEST], SANDBOX_CHECK_TIMEOUT_S + 30)
    try:
        doc = json.loads(done.stdout.decode("utf-8")) if done is not None and done.returncode == 0 else None
    except (UnicodeError, ValueError, RecursionError):
        doc = None
    version = doc.get("code_version") if isinstance(doc, dict) else None
    commit = version.get("git_commit") if isinstance(version, dict) else None
    if not isinstance(commit, str) or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        return (f"오류: tradesentry evaluate가 샌드박스 {sandbox}의 이미지 기록에서 코드 커밋을 읽지 못했다"
                "(샌드박스가 없거나 이미지 기록이 없다).")
    if version.get("dirty") is not False:
        return ("오류: 샌드박스 이미지가 추적 파일을 고친 작업 트리에서 만들어졌거나(dirty) 그 여부를 모른다. 커밋한 "
                "코드로 이미지를 다시 만든다(MT5 결정 기록 ⑧).")
    if commit != host_code_version:
        return ("오류: 샌드박스 이미지의 코드 커밋이 evaluate를 부른 코드의 커밋과 다르다. 같은 커밋에서 이미지를 다시 "
                "만들거나 그 커밋에서 evaluate를 부른다.")
    return None


def _scan_download(temp: Path, run_id: str) -> dict:
    """받은 임시 폴더를 링크를 따라가지 않고(os.lstat) 훑는다(MT5 결정 기록 ④ 4단계, AS3 두 번째 PR 보강).

    돌려주는 값: links(심볼릭 링크), others(일반 파일·폴더가 아닌 항목과 링크 수가 2 이상인 일반 파일(하드링크)),
    unreadable(읽을 수 없어 훑지 못한 폴더 수. os.walk의 onerror가 모은다), layered(내용이 {실행명} 폴더 하나로 한 겹 더
    싸여 있다), misplaced(최상위 항목이 N6 `{도메인명}-{시각}.{확장자}` 파일이나 N7 `{도메인명}-{시각}/` 폴더가 아니다.
    시각은 이 실행명의 시각). 하나라도 있으면 옮기지 않는다."""
    import stat

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


class SandboxCaseRunner:
    """샌드박스 백엔드의 사례 실행 함수(단위 E1 CaseCall → 실행 쪽 키 21개, AS3 결정 기록 ④).

    1) exec: `openshell sandbox exec -n <샌드박스> --timeout <초> -- /opt/tradesentry/bin/tradesentry run-case --snapshot …
       --policy … --mode … --case … --run-name <call.run_id>`(사용자 결정 10(나): 호스트가 확보한 실행명을 넘긴다. 샌드박스 안
       CLI는 /sandbox/outputs/<실행명>/에 쓴다)
    2) 받기 전 확인(MT5 결정 기록 ⑯ T-DL4): `sh -c 'test -d …/<실행명> && ! test -L …/<실행명> && ! test -L /sandbox/outputs'`
    3) 내려받기(MT5 결정 기록 ④): 같은 부모(outputs/) 아래 새 임시 폴더 .download-*에 받고, os.lstat으로 링크·특수 파일을
       거부하고(링크만 os.unlink로 지우고 임시 폴더를 .quarantine-*로 격리), 확보한 빈 사례 실행 폴더로 os.rename한다
    4) 받은 실행 결과 기록(runlog_run_record-{시각}.json)을 읽어 돌려준다. 샌드박스 쪽 종료 코드가 1이어도(실행이 COMPLETED가
       아님) 기록이 있으면 그 기록이다(실제 원인 분류 코드). 기록을 받지 못하면 SandboxError 하위 예외를 내고, 묶음이 FAILED
       줄로 분모에 남긴다(MT5 결정 기록 ⑯)
    """

    def __init__(self, sandbox: str = SCORED_SANDBOX, *, exec_timeout_s: int):
        self.sandbox = sandbox
        self.exec_timeout_s = exec_timeout_s
        self.incidents: list[str] = []

    def __call__(self, call) -> dict:
        request = sandbox_request(call)
        remote = f"{SANDBOX_OUTPUTS}/{call.run_id}"
        done = _openshell(["openshell", "sandbox", "exec", "-n", self.sandbox, "--timeout", str(self.exec_timeout_s),
                           "--", SANDBOX_CLI, "run-case", "--snapshot", request.snapshot_id, "--policy",
                           request.policy_version, "--mode", request.mode, "--case", request.case, "--run-name",
                           request.run_name], self.exec_timeout_s + 30)
        if done is None:
            raise SandboxExecFailed("openshell sandbox exec을 부르지 못했거나 제한 시간을 넘었다")
        check = _openshell(["openshell", "sandbox", "exec", "-n", self.sandbox, "--timeout",
                            str(SANDBOX_CHECK_TIMEOUT_S), "--", "sh", "-c",
                            f"test -d {remote} && ! test -L {remote} && ! test -L {SANDBOX_OUTPUTS}"],
                           SANDBOX_CHECK_TIMEOUT_S + 30)
        if check is None or check.returncode != 0:
            if done.returncode not in (EXIT_OK, EXIT_FAILED):
                raise SandboxExecFailed("샌드박스 안 run-case가 실행 폴더 없이 끝났다")
            raise SandboxOutputMissing("받기 전 확인이 통과하지 않았다")
        self.download(call, remote)
        return self.read_record(call)

    def download(self, call, remote: str) -> None:
        """MT5 결정 기록 ④의 2~6단계. 받는 곳은 묶음이 확보한 빈 사례 실행 폴더(call.run_dir)다."""
        import tempfile

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
            found = _scan_download(temp, call.run_id)
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
        from tradesentry.workflow import nat_wrap

        nat_dir = call.run_dir / f"{NAT_DOMAIN}-{call.stamp}"
        missing = [name for name in nat_wrap.PROFILE_FILES
                   if not (nat_dir / name).is_file() or (nat_dir / name).is_symlink()]
        if missing:
            self.incidents.append(f"{call.run_id}: NAT 프로파일 파일 {len(missing)}개가 없다")

    @staticmethod
    def _discard(temp: Path) -> None:
        """실패한 받기의 임시 폴더를 지운다. 링크를 따라가지 않는다(shutil.rmtree는 링크를 지우기만 한다)."""
        import shutil

        shutil.rmtree(temp, ignore_errors=True)

    @staticmethod
    def read_record(call) -> dict:
        """받은 실행 결과 기록 runlog_run_record-{시각}.json을 읽는다(링크·크기 상한 확인)."""
        from tradesentry.runlog import trace as trace_log

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


def sandbox_request(call) -> args.Request:
    """샌드박스 안 run-case에 넘길 값을 단위 F1의 검사 함수로 다시 본다(명령 인자로 나가는 값이라). 틀리면 WiringError
    (묶음이 그 사례를 FAILED 줄로 남긴다). 문장에는 값을 넣지 않는다."""
    values = (call.versions.get("snapshot_id"), call.versions.get("policy_version"), call.mode,
              call.case.get("case_id"), call.run_id)
    if not all(isinstance(value, str) for value in values):
        raise WiringError("샌드박스에 넘길 값이 문자열이 아니다")
    snapshot_id, policy_version, mode, case_id, run_id = values
    try:
        args.check_snapshot_id(snapshot_id)
        args.check_policy_version(policy_version)
        args.check_case(case_id)
        args.check_run_name_for("run-case")(run_id)
    except Exception:  # argparse.ArgumentTypeError(값을 되풀이하지 않는 문장)
        raise WiringError("샌드박스에 넘길 값이 CLI 인자 형식이 아니다") from None
    if mode not in args.MODES or run_id != f"{RUN_CASE_RUN_NAME}-{call.stamp}":
        raise WiringError("샌드박스에 넘길 모드나 사례 실행명이 형식이 아니다")
    return args.Request(command="run-case", snapshot_id=snapshot_id, policy_version=policy_version, mode=mode,
                        case=case_id, run_name=run_id)


def _policy_file_sha256() -> str | None:
    """채점 대상 실행 샌드박스 정책 파일의 sha256(실행 조건 입력 파일 sandbox.policy_yaml_sha256). 없으면 None."""
    import hashlib

    path = Path(__file__).resolve().parents[3] / OPENSHELL_POLICY_FILE
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def reproduce_command(request: args.Request) -> str:
    """실행 조건 입력 파일 reproduce_evaluate(룰북 B7 재현 명령). --mode를 줬으면 그 값도 적고(스모크 묶음 표시),
    --conditions-extra를 줬으면 준 상대 경로 그대로 적는다(로컬 절대 경로는 F1이 받지 않고, 실행 조건 입력 파일 N13 검사도 막는다)."""
    command = f"tradesentry evaluate --snapshot {request.snapshot_id} --policy {request.policy_version}"
    command += f" --mode {request.mode}" if request.mode else ""
    return command + (f" --{args.CONDITIONS_EXTRA_OPTION} {request.conditions_extra}" if request.conditions_extra else "")


def load_operator_conditions(request: args.Request, dataset: str) -> dict | None:
    """--conditions-extra 파일(운영자 실행 조건, JSON 객체)을 읽어 단위 E1 check_operator_conditions로 검사한다. 옵션이
    없으면 None. 파일이 없거나 JSON이 아니면 RunCaseError(오류 문장에 경로·내용을 넣지 않는다, N13), 내용이 규칙에 맞지
    않으면 BatchError가 그대로 올라간다. 소수는 Decimal로 읽는다(실행 조건 입력 파일은 float를 쓰지 않는다)."""
    from decimal import Decimal

    from tradesentry.evaluation import batch_run

    if request.conditions_extra is None:
        return None
    try:
        text = Path(request.conditions_extra).read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        raise RunCaseError(f"오류: tradesentry evaluate가 --{args.CONDITIONS_EXTRA_OPTION} 파일을 읽지 못했다"
                           f"({type(exc).__name__}). 저장소 폴더 기준 상대 경로의 JSON 파일이어야 한다.") from None
    try:
        doc = json.loads(text, parse_float=Decimal)
    except ValueError:
        raise RunCaseError(f"오류: tradesentry evaluate의 --{args.CONDITIONS_EXTRA_OPTION} 파일이 JSON이 아니다.") from None
    batch_run.check_operator_conditions(doc, dataset)
    return doc


def select_real_dev_mvp(cases: list) -> list:
    """DT7 결정 기록 20260925-0925(real_dev MVP 사례 고르기)의 규칙: 사례마다 sha256("real_dev-mvp-20260925" + ":" +
    case_id)의 16진수 소문자를 순위 값으로 오름차순 앞 20건(20건 이하면 전부). 층화하지 않는다. 순위 순서로 돌려준다."""
    import hashlib

    def rank(case: dict) -> str:
        return hashlib.sha256(f"{REAL_DEV_MVP_PREFIX}:{case['case_id']}".encode("utf-8")).hexdigest()

    return sorted(cases, key=lambda case: (rank(case), case["case_id"]))[:REAL_DEV_MVP_TAKE]


def real_dev_cases(request: args.Request) -> tuple[list[dict], dict]:
    """real_dev 묶음의 사례 목록을 실행 때 만든다: detect와 같은 길(build_case_list, real_dev 계열로 좁힌 뒤 관측 값을 읽음)로
    경보 목록을 만들고 select_real_dev_mvp로 고른다. 새 파일을 쓰지 않는다(outputs/에도 쓰지 않는다).
    돌려주는 값: (계획 사례 [{case_id, hs6, partner, month}] 순위 순, 실행 조건 입력 파일 snapshot.real_dev_alerts에 남길
    경보 목록 기록). 실자료 스냅샷이 아니면 RunCaseError, 분할 기록을 쓸 수 없으면 SplitError."""
    from tradesentry.contract import policy_load
    from tradesentry.dal import query

    policy = policy_load.load_policy(request.policy_version)
    with query.open_snapshot(request.snapshot_id) as snap:
        if snap.source_kind != "real":
            raise RunCaseError("오류: tradesentry evaluate의 real_dev 묶음은 실자료 스냅샷(source_kind real)만 받는다.")
        built = build_case_list(snap, policy)
    if not isinstance(built, dict) or set(built) != CASE_BUILD_KEYS or built.get("dataset") != DETECT_DATASET:
        raise WiringError("단위 P2(case_build)의 출력이 real_dev 사례 목록 객체가 아니다")
    alerts = [{k: case[k] for k in ("case_id", "hs6", "partner", "month")} for case in built["cases"]]
    chosen = select_real_dev_mvp(alerts)
    record = {"policy_version": request.policy_version, "count": len(alerts),
              "case_ids": [case["case_id"] for case in alerts], "selected": len(chosen),
              "selection": REAL_DEV_MVP_RULE}
    return chosen, record


def evaluate_pacing():
    """모델 설정(configs/model/model.json)의 pacing(속도 조절, AS3 세 번째 PR)을 단위 E1 Pacing으로 읽는다. 모든 모드에 같다.
    CLI 옵션·환경변수로 바꾸지 않는다. 없거나 모양이 틀리면 ValueError(BatchError·ConfigError)."""
    from tradesentry.evaluation import batch_run
    from tradesentry.workflow import model_client

    try:
        raw = json.loads((model_client.DEFAULT_CONFIG_DIR / "model.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise model_client.ConfigError("모델 설정을 읽지 못했다") from None
    return batch_run.pacing_from_config(raw.get("pacing") if isinstance(raw, dict) else None)


def seed_concurrency_text(pacing, result) -> str:
    """실행 조건 입력 파일 prescoring_checks.seed_concurrency(평가 스킬 ② 채점 전 확인 5의 순서 seed·동시성 적용): 순서
    seed·동시성과 속도 조절 값, 쉰 시간의 합, HTTP 429 뒤 더 쉰 횟수."""
    return (f"참: 순서 seed {DEV_ORDER_SEED}, 동시성 1, 속도 조절(모델 실행 사이 최소 {pacing.min_gap_ms // 1000}초, "
            f"분당 토큰 {pacing.tokens_per_minute}, HTTP 429 뒤 {pacing.after_rate_limit_ms // 1000}초), 쉰 시간 합 "
            f"{result.paced_ms // 1000}초, 429 뒤 더 쉰 횟수 {result.rate_limit_waits}")


def final_status_text(spec, result) -> str:
    """실행 조건 입력 파일 prescoring_checks.final_status(평가 스킬 ② 채점 전 확인 1): 예정 실행 가운데 줄이 없는 조합 수와
    인프라 실패 재실행(룰북 B5) 대상·재실행 수. 이 값이 있으면 재실행 규칙을 적용한 묶음이다("0건"과 "미기재"가 갈린다)."""
    planned = {(case["case_id"], mode) for case in spec.cases for mode in spec.modes}
    present = {(line["case_id"], line["mode"]) for line in result.lines}
    unrun = len(planned - present)
    return (f"{'참' if unrun == 0 else '거짓'}: 예정 실행 {len(planned)}건 가운데 줄 없는 조합 {unrun}건, 인프라 실패 "
            f"재실행(룰북 B5) 대상 {result.rerun_targets}건·재실행 {result.reruns}건")


def _evaluate(request: args.Request) -> int:
    """evaluate: 단위 E1 묶음 실행 → 단위 E4 NAT 사후 평가 → 실행 조건 입력 파일(위 "evaluate 배선")."""
    # 명령을 부를 때만 import한다. 모듈 속성으로 불러 시험 대역이 걸리게 한다.
    from tradesentry.contract import policy_load
    from tradesentry.dal import query
    from tradesentry.evaluation import batch_run, nat_eval
    from tradesentry.workflow import model_client, orchestrate

    dataset = EVALUATE_DATASETS.get(request.snapshot_id)
    if dataset is None or dataset not in batch_run.UNSEALED_DATASETS:
        _report("오류: tradesentry evaluate가 --snapshot의 자료 묶음을 모른다(dev20·controlled_fixture_v0·"
                "kcs_202201_202412_v2만 받는다. 봉인 묶음은 샌드박스 밖 실행기가 돌린다).")
        return EXIT_FAILED
    extra: dict = {"reproduce_evaluate": reproduce_command(request)}
    try:  # 운영자 실행 조건(--conditions-extra)은 실행 폴더를 만들기 전에 읽고 검사한다. 합치기는 값이 모두 모인 뒤다
        operator = load_operator_conditions(request, dataset)
    except RunCaseError as exc:
        _report(str(exc))
        return EXIT_FAILED
    except ValueError as exc:  # BatchError. 파일 내용은 되풀이하지 않고 검사 문장(키 이름까지)만 적는다
        _report(f"오류: tradesentry evaluate의 --{args.CONDITIONS_EXTRA_OPTION} 파일이 규칙에 맞지 않는다: {exc}")
        return EXIT_FAILED
    try:
        if dataset == DETECT_DATASET:  # real_dev: 실행 때 경보 목록을 만들고 DT7 규칙으로 고른다(AS3 두 번째 PR)
            cases, alerts = real_dev_cases(request)
            extra["snapshot"] = {"real_dev_alerts": alerts}
        else:
            cases = evaluate_cases(dataset, request.snapshot_id)
    except LookupError:
        _report(f"오류: tradesentry evaluate가 자료 묶음 {dataset}의 사례 목록 자리를 모르거나 파일이 없다"
                "(dev20은 eval/dev/dev20/input/cases.json, real_dev는 실행 때 detect와 같은 길로 만든다).")
        return EXIT_FAILED
    except SplitError:
        _report(DETECT_SPLIT_REFUSAL)
        return EXIT_FAILED
    except RunCaseError as exc:
        _report(str(exc))
        return EXIT_FAILED
    except (ValueError, query.SnapshotError) as exc:  # PolicyError는 ValueError다. 예외 이름만 적는다(N13)
        _report(f"오류: tradesentry evaluate가 사례 목록을 읽지 못했다({type(exc).__name__}).")
        return EXIT_FAILED
    modes = (request.mode,) if request.mode else batch_run.PLANNED_MODES[dataset]  # 사용자 결정 12(가)
    try:
        thresholds = orchestrate.policy_thresholds(policy_load.load_policy(request.policy_version))
        run_limits = model_client.load_model_config().limits
        limits = batch_run.limits_from_run_limits(run_limits)
        pacing = evaluate_pacing()
        versions = evaluate_versions(request, dataset)
        spec = batch_run.BatchSpec(dataset=dataset, cases=tuple(cases), modes=tuple(modes),
                                   order_seed=DEV_ORDER_SEED, versions=versions)
        batch_run.check_spec(spec)
    except (ValueError, query.SnapshotError) as exc:  # PolicyError·ConfigError·BatchError는 ValueError다(N13)
        _report(f"오류: tradesentry evaluate의 묶음 입력이 규칙에 맞지 않는다({type(exc).__name__}).")
        return EXIT_FAILED
    if EVALUATE_BACKEND == SANDBOX_BACKEND:
        problem = sandbox_preflight(SCORED_SANDBOX, versions["code_version"])
        if problem is not None:
            _report(problem)
            return EXIT_FAILED
        runner = SandboxCaseRunner(SCORED_SANDBOX, exec_timeout_s=limits["wall_time_s"] + SANDBOX_EXEC_MARGIN_S)
        sandbox = {"name": SCORED_SANDBOX}
        policy_sha = _policy_file_sha256()
        if policy_sha is not None:
            sandbox["policy_yaml_sha256"] = policy_sha
        extra["sandbox"] = sandbox
    elif EVALUATE_BACKEND == HOST_BACKEND:
        runner = host_case_runner
    else:
        raise WiringError("evaluate의 사례 실행 백엔드가 sandbox·host가 아니다")
    reserved = None
    if request.run_name is not None:
        reserved = reserve_run_dir(batch_run.BATCH_RUN_NAME, given=request.run_name)
    result = batch_run.execute_batch(spec, runner, parent=OUTPUT_PARENT, other_parent=OUTPUT_PARENT / SEALED_NAME,
                                     reserved=reserved, pacing=pacing)
    _emit(f"{OUTPUT_LABEL}/{result.run_id}/{result.batch_file.name}")
    for incident in getattr(runner, "incidents", []):
        _report(f"사건: {incident}")
    summary = nat_eval.summarize_batch(result.run_dir)
    extra["prescoring_checks"] = {"final_status": final_status_text(spec, result),
                                  "seed_concurrency": seed_concurrency_text(pacing, result)}
    if operator is not None:
        merged = batch_run.merge_operator_conditions(extra, operator)  # 하위 키 충돌은 검사 단계가 이미 막았다
        _report(f"알림: --{args.CONDITIONS_EXTRA_OPTION}의 운영자 실행 조건을 실행 조건 입력 파일에 합쳤다(키: "
                f"{', '.join(merged)}).")
    doc = batch_run.build_run_conditions(dataset=dataset, cases=cases, modes=list(spec.modes), thresholds=thresholds,
                                         order_seed=DEV_ORDER_SEED, limits=limits,
                                         run_period=(result.started, result.ended), nat_profile_summary=summary,
                                         extra=extra)
    path = batch_run.write_run_conditions(result.run_dir, doc)
    _emit(f"{OUTPUT_LABEL}/{result.run_id}/{path.name}")
    if request.mode:
        _report(f"알림: --mode {request.mode} 하나만 돈 스모크 묶음이다. 점수표로 합치지 않는다(사용자 결정 12). 채점기는 "
                "dev20·real_dev 묶음의 계획 모드가 정해진 모드 전부가 아니면 채점하지 않는다.")
    if EVALUATE_BACKEND == HOST_BACKEND:
        _report("알림: 호스트 백엔드로 돈 묶음이다(시험·스모크용). 점수표 근거가 아니다.")
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
    except RunNameError as exc:  # 문장은 이 모듈이 만든 것뿐이다(받은 값을 넣지 않는다, N13)
        _report(f"오류: tradesentry {command}가 실행명을 확보하지 못했다. {exc}.")
        return EXIT_FAILED
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
