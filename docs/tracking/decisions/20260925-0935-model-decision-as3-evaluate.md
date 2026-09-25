# AS3: `evaluate` 배선, `--run-name`, 샌드박스 백엔드와 채점기 연결

조립 작업 AS3(평가 실행·채점 연결: 평가 하네스 출력과 독립 채점기 입력·출력의 형식을 맞추고 `tradesentry evaluate`와 채점기를 잇는 작업)에서 정한 것을 적는다. 사용자 결정 10(나)(`--run-name`)과 12(가)(`evaluate --mode` 선택)의 코드 반영, 개발 묶음의 샌드박스 실행 백엔드, 조립 점검(`docs/plan/UNITS.md` §5) 1·2·5단계 결과가 들어 있다. 코드와 시험은 같은 PR에 있다. 계획 문서(자료 계약 §10 명령 표·N8, 룰북 B7, 평가 스킬 ②)의 문구는 문서 PR(DOCS2)이 반영한다.

용어

- 조립체 4·5: `tradesentry evaluate`가 도는 평가 실행 단위 묶음(E1~E4·L1~L3)과 독립 채점기(C1~C4, `python -m eval.scorer --run <run_dir>`).
- 평가 하네스: 사례 여러 건을 모드별로 돌리고 실행 기록을 모으는 프로그램(단위 E1~E4).
- 사례 실행 백엔드: 묶음 실행(단위 E1)이 사례 1건 × 모드 하나를 돌리려고 부르는 함수를 누가 어디서 돌리는지. 샌드박스 백엔드(채점 대상 실행 샌드박스 안에서)와 호스트 백엔드(같은 프로세스에서)가 있다.
- 채점 대상 실행 샌드박스: 정확도 지표를 내는 실행용 OpenShell(에이전트를 격리해 돌리는 NVIDIA 샌드박스 런타임) 샌드박스. 개발 평가용 이름은 `ts-scored`(MT5 위반 시험표)다.
- 이미지 기록: 샌드박스 이미지 안 `/opt/tradesentry/image_manifest.json`. 스테이징 도구가 들인 파일 목록과 코드 커밋(`code_version.git_commit`, 추적 파일 변경 여부 `dirty`)을 적는다(MT5 결정 기록 ⑧).
- 스모크 묶음: 배선이 도는지만 보는 작은 묶음. 점수표 근거가 아니다.
- 세 포트: AS2가 켠 조사 흐름 자리 셋. 필수 조회(`required_tools`), 초안은 도구 없는 차례에서만(`drafts_only_without_tools`), 규칙 참고값(`reference_status`, 근거 상태 변환 훅으로 켜진다).

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 09:35(기록 시각). 바탕은 `main` d6af950(MT7 #39·AS2 #38 병합 뒤). 코드 커밋은 2c447e1(단위 F1)·5410232(단위 E1)·3627f75(단위 F2) |
| 제목 | `evaluate` 모드 기본값과 스모크 표시, `--run-name` 확보, 사례 실행 백엔드(샌드박스 기본·호스트 시험용), 샌드박스 사전 점검과 내려받기, 이미지 안 `code_version`, 하네스 ↔ 채점기 조립 시험, 조립 점검 1·2·5단계 |
| 결정 | 아래 "결정 내용" ①~⑩ |
| 이유와 근거 | 항목마다 적었다 |
| 검토한 대안 | 아래 "검토한 대안" |
| 결정 주체 | 소유 트랙(M). ①·②는 사용자 결정 10(나)·12(가)(`20260925-0847-user-decision-morning-shared-promises.md`)와 그 기록의 오케스트레이터 세부를 따른다 |
| 공용 약속 여부 | 사용자 결정 10·12가 정한 것(`--run-name` 옵션, `evaluate --mode` 선택) 밖의 이름·키를 만들지 않았다. 실행 조건 입력 파일에는 채점기 임시 형식의 키(`sandbox`, `reproduce_evaluate`)만 더 채웠다. 백엔드 선택은 CLI 옵션·환경변수가 아니라 모듈 기본값이다(③). 샌드박스 이름 `ts-scored`는 MT5 실측 이름을 기본값으로 둔 것이다 |
| 영향 | 아래 "영향과 넘길 곳" |
| 관련 PR | AS3(브랜치 `model/AS3-evaluate`) |

## 결정 내용

① **`--run-name`(사용자 결정 10(나))** — 확정

- 단위 F1: 다섯 명령에 선택 옵션 `--run-name <실행명>`을 둔다. 옵션 역할 표 `COMMAND_OPTIONS` 밖에서 다섯 명령에 똑같이 붙인다(값 검사가 명령마다 달라서). 검사: 값 전체가 N5 형식 `{실행 이름}-{yymmddhhmmss}`(fullmatch, 끝 줄바꿈 거부), 실행 이름 = 그 명령의 실행 이름(명령 이름의 하이픈을 밑줄로), 시각 12자리가 실제 날짜·시각, 64자 이하, 경로 모양 거부. 오류 문장은 받은 값을 되풀이하지 않는다(N13). 같은 옵션 두 번은 거부. 요청(`args.Request`)에 `run_name` 필드를 더했다(골든 기대값 갱신).
- 단위 F2: 옵션이 있으면 `reserve_given_run_dir`가 `outputs/{실행명}/`을 `os.mkdir`(`exist_ok` 없이)로 만들고, `outputs/sealed/`에 같은 이름이 있으면 방금 만든 빈 폴더를 지우고 실패한다. 다음 초로 넘어가지 않는다(이름은 호스트가 정했다). 실패는 종료 코드 1이고 문장에 값이 없다(`RunNameError`를 `call_handler`가 받는다). 옵션이 없으면 지금처럼 CLI가 확보한다.
- 단위 E1: `execute_batch(reserved=(실행명, 시각, 폴더))`로 이미 확보한 묶음 폴더를 받는다(`evaluate --run-name`). 모양(`evaluate-{시각}`, parent 바로 아래)과 빈 폴더가 아니면 사례 폴더를 만들기 전에 거부한다.
- NemoClaw 시연 경로는 MT5 결정 기록 ⑤ 그대로다(이 PR은 바꾸지 않았다).

② **`evaluate --mode` 선택과 스모크 표시(사용자 결정 12(가))** — 확정

- 옵션 역할 표에서 `evaluate`의 `--mode`를 OPTIONAL로 바꿨다. 주지 않으면 E1 `PLANNED_MODES[자료 묶음]`(dev20·holdout40 = `checklist`·`agent`·`full`, `real_dev`·`real_sealed` = `freeform`·`full`)을 한 묶음(순서 seed `dev-order-v1`로 섞음, 동시성 1)으로 돈다.
- 주면 그 모드 하나만 돈다. 스모크 표시는 계약 안에서 두 곳에 남는다: 실행 조건 입력 파일의 `planned_modes`가 그 모드 하나이고(`spec.modes`에서 옮긴다), `reproduce_evaluate`(룰북 B7 재현 명령)에 `--mode <모드>`가 붙는다. 묶음 기록 `evaluation_batch_run-{시각}.jsonl`의 키는 계약이 고정했으므로 더하지 않았다. 채점기는 dev20·`real_dev` 묶음의 계획 모드가 정해진 모드 전부가 아니면 채점하지 않으므로(`read_conditions`) 점수표로 합쳐지지 않는다. 표준 오류에 스모크 알림 한 줄을 쓴다.

③ **사례 실행 백엔드와 고르는 수단** — 확정(샌드박스 이름은 잠정)

- 기본값은 샌드박스 백엔드(`dispatch.EVALUATE_BACKEND = "sandbox"`)다. 채점 대상 실행은 채점 대상 실행 샌드박스 안에서 돌고(자료 계약 §8.2, §10.3 방식 (나)), 호스트에서 돈 개발 묶음은 스모크이고 점수표 근거가 아니다(MT7 결정 기록 "AS3에 넘길 것" 3).
- 호스트 백엔드(`host_case_runner`: 같은 프로세스에서 `run_case_in`)는 시험과 스모크용이다. CLI 옵션·환경변수로 고르지 않는다(계약 밖 이름을 만들지 않는다). 모듈 값을 바꿔 끼워서만 쓴다(오케스트레이터가 돌릴 명령은 AS3-1 보고). 호스트 백엔드 묶음은 실행 조건 입력 파일에 `sandbox`를 적지 않고(요약에 "미기재"), 표준 오류에 "점수표 근거가 아니다"를 쓴다.
- 샌드박스 이름은 기본값 `SCORED_SANDBOX = "ts-scored"`(MT5 위반 시험표 `artifacts/openshell/openshell_violation_tests-260925055407/`의 채점 대상 실행용 이름)다. 이름을 바꿀 수단도 옵션으로 두지 않았다(잠정: 다른 이름을 쓰려면 코드 값을 바꾼다).

④ **샌드박스 백엔드의 사례 실행 절차** — 확정(MT5 결정 기록 ③·④·⑯을 구현)

1. 묶음(E1)이 호스트 쪽 `outputs/run_case-{시각}/`을 확보한다(N8).
2. 넘길 값을 단위 F1 검사 함수로 다시 본다(`sandbox_request`). 틀리면 샌드박스를 부르기 전에 `WiringError`.
3. `openshell sandbox exec -n ts-scored --timeout <사례당 wall time + 120초> -- /opt/tradesentry/bin/tradesentry run-case --snapshot … --policy … --mode … --case … --run-name <실행명>`. 샌드박스 안 CLI는 exec 기본 작업 폴더 `/sandbox`(MT5 ⑭ 실측)에서 `/sandbox/outputs/<실행명>/`에 쓴다.
4. 받기 전 확인: `openshell sandbox exec … -- sh -c 'test -d /sandbox/outputs/<실행명> && ! test -L /sandbox/outputs/<실행명> && ! test -L /sandbox/outputs'`(MT5 ⑯ T-DL4 확인 전의 조건). 실행명은 N5 형식을 통과한 값만 들어간다.
5. 내려받기: 받는 곳이 확보한 빈 폴더인지 보고, 같은 부모(`outputs/`) 아래 `tempfile.mkdtemp(prefix=".download-")`로 받는다. `os.walk(followlinks=False)`와 `os.lstat`으로 링크·일반 파일·폴더가 아닌 항목을 찾으면 링크만 `os.unlink`로 지우고 임시 폴더를 `.quarantine-*`로 이름을 바꿔 격리하고, 사건 한 줄을 표준 오류에 쓴다(실행명과 격리 폴더 이름만). `{실행명}` 폴더 하나로 한 겹 더 싸인 모양도 같은 방식으로 거부·격리한다(임시 폴더를 `outputs/`에 그대로 남기지 않는다). 받기 자체가 실패하면 임시 폴더를 지운다(`shutil.rmtree`는 링크를 따라가지 않는다). 옮기기는 최상위 항목마다 `os.path.lexists`로 충돌을 본 뒤 `os.rename`하고 임시 폴더를 지운다.
6. 받은 `runlog_run_record-{시각}.json`을 읽어(링크 거부, 1 MiB 상한) 돌려준다. 샌드박스 쪽 종료 코드가 1(실행이 `COMPLETED`가 아님)이어도 기록이 있으면 그 기록이다(실제 원인 분류 코드가 남는다). E1이 단위 L2 검사와 실행 전 키 대조를 다시 한다.
7. 기록을 받지 못하면 예외를 내고 E1이 그 사례를 `FAILED` 줄(원인 `CODE_ERROR`, `detail` = `harness:{예외 이름}`)로 분모에 남긴다(MT5 ⑯). 예외 이름: `SandboxExecFailed`(exec을 부르지 못함·제한 시간 초과·실행 폴더 없이 종료 코드 0·1 밖), `SandboxOutputMissing`(받기 전 확인 불통과), `DownloadFailed`, `DownloadRejected`(링크·특수 항목·겹친 층), `DownloadMoveConflict`, `RunRecordMissing`. 모두 `CODE_ERROR`라 인프라 실패 재실행 대상이 아니다(단위 L3 규칙 그대로). 내려받기 실패를 인프라로 볼지는 계약에 코드가 없어 정하지 않았다.
- 받은 뒤 샌드박스 쪽 실행 폴더는 지우지 않는다(개발 묶음은 지워도 되지만 조사용으로 둔다).

⑤ **샌드박스 사전 점검과 이미지 안 `code_version`** — 확정

- 문제: 이미지 안에는 `.git`이 없어 샌드박스 안 `run-case`의 `code_version`이 `unknown`이 되고, 호스트가 준 묶음 버전 키(git 커밋)와 달라 모든 줄이 `harness:record_mismatch`로 실패한다.
- 샌드박스 쪽: `dispatch.code_version`이 git 메타를 읽지 못하면 앱 뿌리의 이미지 기록(`image_manifest.json`) `code_version.git_commit`을 쓴다. 40자 16진수이고 `dirty`가 거짓일 때만이고, 아니면 `unknown`이다(고친 코드를 커밋 해시로 적지 않는다). MT5 결정 기록 ⑧("샌드박스 안 실행 결과의 `code_version`은 이 값으로 채운다")의 구현이다.
- 호스트 쪽 사전 점검(`sandbox_preflight`, 실행 폴더를 만들기 전): ① `openshell` 명령이 있는가 ② exec으로 `cat /opt/tradesentry/image_manifest.json`을 읽어 커밋이 40자 16진수이고 `dirty`가 거짓인가(스테이징 도구의 `dirty`는 `git status --porcelain --untracked-files=no`라 추적 파일 변경만 센다) ③ 그 커밋이 호스트 `code_version`과 같은가. 하나라도 아니면 종료 코드 1과 분명한 문장으로 끝나고 `outputs/`에 아무것도 만들지 않는다. dev20 60실행을 모두 실패로 쓰는 일을 막는다.

⑥ **하위 프로세스를 CLI(단위 F2)에 둔 까닭** — 확정

- AS2 결정 기록은 `code_version`을 위해 CLI에 하위 프로세스를 들이지 않았다(MT5a 보안 권고 5). 이번에는 샌드박스 백엔드가 호스트에서 `openshell`을 불러야 하고, 경계 시험 8번(CLI는 호스트 전용 E2에 닿지 않는다)과 E2의 범위(봉인 묶음, F1 뒤) 때문에 E2에 둘 수 없다. `scripts/`는 이미지·앱 밖이라 import하지 않는다.
- 줄인 위험: 하위 프로세스는 `_openshell` 한 곳에서만 부르고, 첫 원소가 `"openshell"`인 목록만 받는다(셸 문자열 없음, `shell=False`, 표준 입력 닫음). 값은 단위 F1 검사를 통과한 것만 들어간다. 자식 환경에서 `NVIDIA_API_KEY`·`NVIDIA_INFERENCE_API_KEY`·`DATA_GO_KR_SERVICE_KEY`·`TRADESENTRY_SEALED_DIR`를 이름으로 뺀다(값을 읽거나 출력하지 않는다). 호스트 프로세스는 `.env`를 읽지 않는다(`load_env` 없음). 샌드박스 안에서 `evaluate`를 부르면 `openshell`이 없어 사전 점검에서 끝난다. `sh -c`는 샌드박스 안에서만 돈다(MT5 ⑯의 명령 그대로).

⑦ **`evaluate` 순서와 실행 조건 입력 파일** — 확정

- 순서: 자료 묶음(봉인 묶음 거부) → 사례 목록 → 정책 임계값·한도·버전 키·묶음 검사 → 샌드박스 사전 점검 → (`--run-name`이면) 묶음 폴더 확보 → E1 → E4 → 실행 조건 입력 파일 배타 생성. 실행 조건 입력 파일은 내려받기를 끝낸 호스트 쪽 프로그램(evaluate 자신)이 쓴다(자료 계약 §8.2). 샌드박스가 쓴 출력은 사례 폴더에만 옮기므로 같은 이름 충돌이 없다.
- 채우는 값(채점기 임시 형식 키 안): 기존 `dataset`·`planned_cases`·`planned_modes`·`policy_detection_thresholds`·`order_seed`·`concurrency`·`limits`·`run_period`·`nat_profile_summary`에 더해 `reproduce_evaluate`(두 백엔드)와 `sandbox.name`·`sandbox.policy_yaml_sha256`(샌드박스 백엔드. `configs/openshell/policy.yaml` 바이트 sha256)을 넣었다. `sandbox.live_policy_sha256`·`sandbox.violation_tests_run`, `scorer_commit`, 사전 점검 결과 등은 evaluate가 모르므로 채점기 요약에 "미기재"로 남는다(아래 "넘길 곳").
- 버전 키: `evaluate_versions`가 요청의 정책·스냅샷, 커널 K1의 `RB-1`, 스냅샷의 비교 대상 집합(합성은 비교국 표 행의 값), `code_version()`으로 만든다.

⑧ **사례 목록 자리** — 잠정

- dev20: `eval/dev/dev20/input/cases.json`(DT5 정본). 파일의 `dataset`·`snapshot_id`가 요청과 같아야 한다.
- `real_dev`: DT7 ①의 경보 목록 자리가 아직 없어 실행 폴더를 만들기 전에 "DT7 ①의 경보 목록 자리가 정해지면 잇는다" 오류로 끝난다(자리만). `run-case`도 실자료 스냅샷을 거부하는 판이다(AS2 ⑩).
- `controlled_fixture_v0`: 커밋된 입력 사례 목록이 없다. 정답 파일 `eval/dev/oracle_ABC.json`을 입력으로 쓰지 않으려고 자리를 두지 않았다.
- `run-case`의 자료 묶음 표 `RUN_CASE_DATASETS`에 `dev20 → dev20`을 더했다(AS2 결정 기록 "DT5(dev20)" 항목).

⑨ **`run-case` 조립 공유** — 확정

- `_run_case`의 확보 뒤 부분을 `run_case_in(request, run_id, stamp, run_dir)`로 나눴다. `run-case` 처리 함수와 호스트 백엔드가 같이 쓴다. 그래서 평가 실행도 `investigate_case` 배선(세 포트)을 그대로 쓴다(AS2 결정 기록 "AS3" 항목). 샌드박스 백엔드는 샌드박스 안 `run-case`라 같은 배선이다. 종료 코드·표준 출력·오류 문장은 전과 같다(AS2 조립 시험 22개 그대로 통과).

⑩ **하네스 ↔ 채점기 연결(조립 시험)** — 확정

- `tests/units/F2/test_evaluate_scorer.py`: 임시 저장소 사본에 dev20을 설치(`eval.datagen.dev20.install`)하고, 호스트 백엔드로 `tradesentry evaluate --snapshot dev20 --policy dev-0.1`(모드 기본값 = 세 모드)을 돌린다. `checklist` 20건은 실제 조립으로 `COMPLETED`, 모델 모드 40건은 HTTP 400을 곧바로 돌려주는 가짜 전송으로 `FAILED`(`PROVIDER_HTTP_4XX`, 재시도 없음)다. 채점기 `eval.scorer.__main__.main`(저장소 뿌리를 임시 사본으로)이 종료 코드 0으로 `scorer_claims-{시각}.jsonl`·`scorer_results-{시각}.jsonl`(60줄)·`scorer_summary-{시각}.md`를 낸다.
- 이름 대조: 보고서 파일 `reports_render_ko-{시각}.json`(채점기 `REPORT_DOMAIN`), 실행 조건 입력 파일 `run_conditions-{시각}.json`(채점기 `CONDITIONS_DOMAIN`), 묶음 기록 `evaluation_batch_run-{시각}.jsonl`(채점기 `BATCH_DOMAINS["evaluate"]`), 사례 폴더는 묶음 폴더의 형제. 채점기 코드는 고치지 않았다.
- E4 `runs_with_profile`·`runs_with_nat_trace` = 60(모든 실행에 NAT 폴더가 있다, MT7 "AS3에 넘길 것" 5). 60실행 모두에서 세 포트가 켜졌다(`required_tools is dispatch.required_tools`, `drafts_only_without_tools`가 참, `reference_status`가 있음).
- 샌드박스 백엔드는 가짜 `openshell`(`tests/units/F2/fake_openshell.py`, PATH 앞에 둔 실제 하위 프로세스)로 시험했다: 명령 모양, `--run-name` 전달, 받기 전 확인, 임시 폴더 위치, 링크·파이프·겹친 층·받기 실패·기록 없음의 분모 처리, 격리, 자식 환경에 키·봉인 변수 없음, 사전 점검 거부 다섯 가지와 `openshell` 없음.

## 조립 점검(`docs/plan/UNITS.md` §5) 1·2·5단계 결과

| 단계 | 결과 | 명령과 종료 코드 |
|---|---|---|
| 1. 정적 import 그래프 | 위반 0. CLI는 E2에 닿지 않고, 채점기는 `tradesentry`·`eval.datagen`에 닿지 않는다. 단위 파일의 허용 import는 바꾸지 않았다(F2가 쓰는 `subprocess`·`shutil`·`tempfile`·`stat`·`hashlib`은 표준 라이브러리) | `uv run --locked python -m unittest discover -s tests -p "test_boundaries.py"` → 0(34개) |
| 2. MVP 실행 커버리지(조립체 4·5) | `evaluate`가 E1·E4·L1~L3을 부르고, 채점기가 C1~C4를 부른다(조립 시험). E3(추출 명령)은 `evaluate` 밖의 별도 명령이라 이 경로에서 불리지 않지만 평가 스킬 ② 채점 전 확인이 쓴다. E2는 봉인 실행기라 F1 뒤 구현이다(골든 건너뜀) | 조립 시험 `tests/units/F2/test_evaluate_scorer.py` → 0 |
| 5. 동작 불변 | 단위 E1·E3·E4·L1~L3·C1~C4·F1 골든과 F2 시험(AS2 run-case 조립 시험 포함) 통과. 출력 파일 도메인명은 단위 표 그대로 | 단위별 `discover -s tests/units/<ID> -t tests` → 모두 0. 전체 시험 → 0 |

- 판정 열(`docs/plan/UNITS.md` §3): 이 PR은 계획 문서를 고치지 않는다(오케스트레이터 지시: 계획 문서는 DOCS2). 조립체 4·5의 판정은 바꿀 것이 없다: E1~E4·C1~C4 유지, F1은 합침 후보(→ F2) 그대로, F2 유지. 버린 것·합친 것 없음.

## 검토한 대안

- 백엔드를 CLI 옵션(`--backend`)이나 환경변수로 고르기: 계약 밖 새 이름이라 하지 않았다(작업 지시). 모듈 기본값으로 풀었다.
- 샌드박스 백엔드를 단위 E2(`sealed_runner.py`)에 두기: 경계 시험 8번이 CLI → E2를 막고, E2는 E1을 import할 수 없어 묶음 실행을 다시 만들어야 한다. E2의 봉인 범위는 F1 뒤다.
- `evaluate` 전체를 샌드박스 안에서 돌리고 E4·실행 조건 입력 파일만 호스트에서: 샌드박스 안 E1이 호스트 실행명을 확보할 수 없고(N8), 묶음 기록을 샌드박스가 쓰게 된다. 사례마다 호스트가 확보하는 지금 방식이 N8·결정 10(나)와 맞다.
- 호스트 `code_version` 대신 이미지 커밋을 묶음 버전 키로 쓰기: 호스트 코드와 이미지 코드가 다른 채로 돌 수 있다. 같을 때만 돌게 막았다.
- 스모크 표시로 묶음 기록이나 실행 조건 입력 파일에 새 키 두기: 계약 밖 키라 하지 않았다. `planned_modes`와 `reproduce_evaluate`로 충분하다.
- 조립 시험에서 채점기를 하위 프로세스로 부르기: 채점기의 저장소 뿌리가 작업 폴더로 고정돼 저장소 `outputs/`에 쓰고 gitignore 대상 dev20 SQLite에 기대게 된다. `main(repo_root=임시 사본)`으로 불렀다.

## 영향과 넘길 곳

- DOCS2(계획 문서): 자료 계약 §10 명령 표에 `--run-name`(다섯 명령 선택 옵션)과 `evaluate`의 `--mode` 선택, N8의 "호스트가 확보한 실행명을 `--run-name`으로 넘긴다", 룰북 B7 재현 명령(`tradesentry evaluate --snapshot <id> --policy <버전>`, 모드 없이), 평가 스킬 ②의 실행 명령과 "부분 모드 묶음을 합쳐 점수표를 만들지 않는다"는 문장. 단위 표 E1·F1·F2 행 비고(백엔드·`--run-name`)도 필요하면 더한다.
- 오케스트레이터(실측): 샌드박스 이미지를 이 PR 병합 뒤 커밋에서 dev20 스냅샷을 넣어 다시 만들고(`--add data/snapshots/dev20/snapshot_build.sqlite --add data/snapshots/dev20/snapshot_build.json`), 개발 평가용 샌드박스를 그 이미지로 다시 만든 뒤 스모크를 돈다(명령은 AS3-1 보고). 확인할 것: exec 기본 작업 폴더가 `/sandbox`인지(MT5 ⑭), 내려받기 내용 복사 모양(T-DL1), 이미지 안 `code_version`이 커밋과 같은지, T-DL4.
- AS4·F1 전: 실행 조건 입력 파일의 `sandbox.live_policy_sha256`·`sandbox.violation_tests_run`·`scorer_commit`·`precheck`·`prescoring_checks`는 evaluate가 모른다. 평가 스킬 ② 절차가 넣을 수단(실행 조건 입력 파일을 evaluate가 배타 생성하므로 나중에 더할 수 없다)을 MT7 다음 PR 5(형식 확정)와 함께 정한다.
- MT7 다음 PR: 내려받기 실패의 원인 코드(지금 `CODE_ERROR`)를 인프라 재실행 대상으로 볼지, 인프라 실패 재실행을 원래 묶음과 잇는 방법. 샌드박스 쪽 실행 폴더 지우기.
- E2(F1 뒤): 사례 실행 절차(④)와 사전 점검(⑤)은 E2가 같은 규칙을 따로 구현할 때의 기준이다(E2는 F2를 import하지 않는다).
