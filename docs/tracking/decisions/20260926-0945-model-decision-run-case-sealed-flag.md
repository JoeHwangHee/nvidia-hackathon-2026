# FIX1: `tradesentry run-case`에 봉인 묶음 실행 경로 `--sealed`를 더한다(공용 약속 변경, 사용자 승인 2026-09-26(토) 09:55)

룰북 `RB-1`(평가 룰북의 첫 동결 버전) 동결 뒤 봉인 묶음(개발 중 보지 않도록 저장소 밖 봉인 폴더에 두는 평가 자료 `holdout40`·`real_sealed`)의 첫 공식 실행이 `run-case`(사례 1건을 조사하는 CLI 명령)의 봉인 실행 경로 부재로 무효가 된 뒤, 그 경로를 명시적 선택 옵션 `--sealed`로 더하기로 한 것을 적는다. CLI 명령 형식(공용 약속, 자료 계약 §10 CLI 행)에 옵션을 더하는 변경이라 사용자 승인 대상이다. 이 기록은 브랜치 준비 단계의 기록이며, 봉인 사건 자체(중단 묶음의 처리)는 오케스트레이터가 다른 기록에 적는다.

용어

- `--sealed`: `run-case`만 받는 값 없는 선택 옵션(플래그). 봉인 묶음의 공식 채점 대상 실행 경로를 고른다. 샌드박스 밖 실행기(단위 E2, 봉인 해시를 대조하고 사례 식별자를 샌드박스 안 `run-case`에 한 건씩 넘기는 호스트 쪽 프로그램)만 붙이고, 개발 실행에는 주지 않는다.
- 자료 묶음(`dataset`): 실행 결과 기록의 키 하나로, 어느 평가 묶음의 사례인지 적는다(`controlled_fixture_v0`·`dev20`·`holdout40`·`real_dev`·`real_sealed`, 자료 계약 §4.2).
- 분할 기록: 실자료 시계열(HS6 × 상대국)을 개발용 `real_dev`와 봉인용 `real_sealed`로 나눈 정본 파일(`data/reference/real_split_*.json`, 병렬 개발 규칙 §7.2).
- 비교 대상 집합(`grouping_version`): 비교국을 고르는 규칙의 판. 봉인 묶음은 `g0`(`g0` 대체 선언, 결정 기록 `20260926-0810-user-decision-rb1-g0-substitute-and-prose-ex2.md`).

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-26(토) 09:45(기록 시각). 바탕은 `origin/main` 27d2a45(동결 커밋 c557540 + 증거 커밋 #89) |
| 제목 | `run-case`에 봉인 묶음 실행 경로 `--sealed` 추가 — `holdout40` 자료 묶음 대응·`real_sealed` 계열 허용, 단위 E2가 넘김 |
| 결정 | 아래 "설계" ①~④ |
| 이유와 근거 | 아래 "배경" |
| 검토한 대안 | 아래 "검토한 대안" |
| 결정 주체 | 설계는 오케스트레이터 `[DESIGN: 오케스트레이터 결정]`, 구현 세부는 소유 트랙(M). 공용 약속 변경은 사용자 승인 대상 |
| 공용 약속 여부 | **예**(병렬 개발 규칙 §4.1의 CLI 명령 형식, 자료 계약 §10 CLI 행). 상태: **사용자 승인 2026-09-26(토) 09:55**(채팅 "둘다 권장대로" — 이 옵션과 중단 묶음 무효 처리·새 묶음 시작을 함께 승인. 결정 기록 `20260926-0955-user-decision-f2-restart-after-run-case-defect.md`) |
| 영향 | 파일: `src/tradesentry/cli/args.py`(F1), `src/tradesentry/cli/dispatch.py`(F2), `src/tradesentry/evaluation/sandbox_exec.py`·`src/tradesentry/evaluation/sealed_runner.py`(E2), 시험 `tests/units/F1/`·`tests/units/F2/`·`tests/units/E2/`, 문서 `docs/rules/DATA_CONTRACT_V1.md` §10·`docs/plan/UNITS.md` F1·F2·E2 행·`skills/tradesentry-eval/SKILL.md` 명령 절·`docs/tracking/findings.md`. 작업 ID: 로드맵 F2(봉인 묶음 공식 실행). 일정: 승인·병합·전용 샌드박스 이미지 재스테이징 뒤 봉인 묶음을 다시 시작해야 한다 |
| 관련 PR | 브랜치 `model/F2-run-case-sealed`(PR은 승인 뒤 오케스트레이터가 연다) |

## 배경 `[사실: 오케스트레이터 실측 2026-09-26(토) 09:25~09:37, 코드는 이 브랜치 바탕 27d2a45]`

룰북 `RB-1` 동결(커밋 c557540) 뒤 공식 채점 대상 실행 전용 샌드박스 `ts-official`에서 단위 E2로 `holdout40` 봉인 묶음을 시작했더니 15건이 모두 `FAILED`·원인 코드 `CODE_ERROR`(하네스 예외 `RunRecordMissing`), 모델 호출 0회였다. 원인은 둘이다.

1. `dispatch.py`의 `RUN_CASE_DATASETS`(합성 스냅샷 → 자료 묶음 표)에 `holdout40`이 없다. `run_case_in`은 실행 폴더를 확보한 뒤 이 표를 보고 `RunCaseError`("… 자료 묶음(dataset)을 정하지 못했다(RUN_CASE_DATASETS에 없다)")로 종료 코드 1을 내므로 빈 실행 폴더만 남고, 호스트(`sandbox_exec.SandboxCaseRunner`)는 내려받은 뒤 실행 결과 기록 `runlog_run_record-{시각}.json`이 없어 `RunRecordMissing`을 낸다. 진단: 같은 샌드박스에서 `run-case --snapshot holdout40 --case … --mode checklist`가 정확히 이 메시지로 종료 1·빈 폴더였고, `--snapshot controlled_fixture_v0`는 정상 기록이었다.
2. 실자료 스냅샷에서 `run_case_in`은 `real_case_scope`로 사례 계열이 분할 기록의 `real_dev`인지 보고 아니면 `RUN_CASE_SEALED_REFUSAL`로 거부하며 `dataset`을 `real_dev`로 적는다(결정 기록 `20260925-0605-model-decision-as2-run-case.md`, `20260925-1230-model-decision-as3-real-dev.md`, 병렬 개발 규칙 §7.2의 5). 그래서 `real_sealed` 묶음도 지금 CLI로는 돌 수 없다. 단위 E1·E2는 `STATIC_KEYS`로 기록의 `dataset`이 묶음 `dataset`(`real_sealed`)과 같아야 한다(`batch_run.py`).

두 거부는 개발 중 봉인 자료를 돌리지 못하게 하는 보호(병렬 개발 규칙 §6·§7.2)로 의도된 것이라, 보호를 없애지 않고 **명시적 선택 옵션**으로 봉인 경로를 여는 쪽을 택했다.

## 설계

① **F1 `args.py`** `[DESIGN: 오케스트레이터 결정]` — `run-case`만 받는 값 없는 선택 옵션 `--sealed`(`store_true`)를 `--replay`와 같은 자리(`COMMAND_OPTIONS` 밖)에 둔다. 요청 객체 `Request`에 `sealed: bool`(기본 `False`)을 더한다. 다른 명령이 `--sealed`를 받으면 `--replay`와 같은 방식(argparse의 "unrecognized arguments", 종료 코드 2)으로 거부한다. `--sealed`와 `--replay`(키 없는 스모크 재생)를 함께 주면 인자 오류(2, 문장 `SEALED_WITH_REPLAY`)다. 도움말: "봉인 묶음(holdout40·real_sealed)의 공식 채점 대상 실행 경로. 샌드박스 밖 실행기(단위 E2)만 준다. 개발 실행에는 주지 않는다".

② **F2 `dispatch.py`** `[DESIGN: 오케스트레이터 결정]` — `SEALED_RUN_CASE_DATASETS = {"holdout40": "holdout40"}`(봉인 묶음의 합성 스냅샷 → 자료 묶음. `--sealed`일 때만 본다)와 `SEALED_REAL_DATASET = "real_sealed"`를 `RUN_CASE_DATASETS` 옆에 둔다. `run_case_in`에서
- `request.sealed`이고 출처 종류가 `real`: 새 보조 함수 `sealed_real_case_scope`가 분할 기록(`load_real_split`)으로 사례 계열이 `real_sealed`인지 관측 값을 읽기 전에 보고, 아니면 `RunCaseError`(`SEALED_REAL_REFUSAL`: "… --sealed는 실자료에서 분할 기록의 real_sealed 계열 사례만 조사한다 …"). `dataset` = `real_sealed`, `grouping_version` = `REAL_GROUPING_VERSION`(`g0`), `case_input`은 `real_case_scope`와 같은 모양(`{"dataset": "real_sealed", "series_assignment": …}`). `real_case_scope`의 동작은 바꾸지 않는다.
- `request.sealed`이고 출처 종류가 `controlled`: `dataset` = `SEALED_RUN_CASE_DATASETS.get(snapshot_id)`, 없으면 `RunCaseError`(`SEALED_SYNTHETIC_REFUSAL`: "… --sealed는 봉인 묶음의 합성 스냅샷(holdout40)만 받는다 …"). `grouping_version`은 개발 경로와 같이 `snapshot_grouping_version(snap)`(비교국 표 행의 값).
- `request.sealed`가 아니면 기존 경로를 글자 그대로 유지한다(`holdout40`은 여전히 `RUN_CASE_DATASETS`에 없어 거부, `real_sealed` 계열은 여전히 `RUN_CASE_SEALED_REFUSAL`).
- 실행 결과 기록의 키 21개 형식(자료 계약 §8)은 바꾸지 않는다. 모듈 머리 설명에 `--sealed` 항목을 더했다.

③ **E2 `sandbox_exec.py`·`sealed_runner.py`** `[DESIGN: 오케스트레이터 결정]` — `SandboxCaseRunner.__init__`에 `sealed: bool = False`를 더하고, exec 인자 목록에서 `--run-name <실행명>` 뒤에 `sealed`이면 `--sealed`를 붙인다. `sealed_runner.run_sealed`는 `sealed=sealed`(자료 묶음이 `types.SEALED_DATASETS`에 있을 때 참)를 넘긴다 `[해석: 지시서의 "sealed=True"를 리허설(dev20, 봉인 아님)까지 고려해 변수로 넘겼다. 봉인 묶음에서는 결과가 같다]`. CLI `evaluate`(개발 묶음)는 넘기지 않아 `False`다. E2 호출 형식(`python -m tradesentry.evaluation.sealed_runner …`)은 그대로다.

④ **비교 대상 집합 확인** — E2는 두 봉인 묶음의 `grouping_version`을 상수 `g0`(`SEALED_GROUPING_VERSION`)으로 두고 기록의 값과 `STATIC_KEYS`로 대조한다. `holdout40` 기록의 값은 `snapshot_grouping_version(snap)` = 비교국 표 행의 `grouping_version`이다. 공개 자료로만 확인: `holdout40` 비교국 표는 dev20과 같은 공개 생성기 `eval/datagen/dev20.py`가 만들고(생성 규칙의 `dataset`은 `dev20`·`holdout40`, 191행 근처), 그 표의 `grouping_version` 값은 상수 `PEER_GROUPING = "g0"`(117행·545행 근처) 하나다 `[사실: eval/datagen/dev20.py]`. dev20 공개 표 `data/reference/peer_group_dev20.csv`의 `grouping_version` 열도 120행 모두 `g0`이다 `[사실]`. 반입 도구 시험 `tests/test_import_sealed_holdout40.py`는 dev20 공개 표를 가짜 봉인 묶음의 비교국 표로 그대로 쓴다 `[사실]`. 봉인 폴더는 열지 않았으므로 실제 봉인 표의 값은 `[추론: 같은 생성기·같은 상수]`이다.

## 검토한 대안

- 옵션 없이 `RUN_CASE_DATASETS`에 `holdout40`을 더하고 실자료의 `real_sealed` 거부를 없애는 안: 개발 중 어떤 실행이든 봉인 자료를 돌릴 수 있게 되어 병렬 개발 규칙 §6·§7.2의 보호가 사라진다. 채택하지 않았다.
- 옵션 대신 환경변수로 봉인 경로를 켜는 안: 샌드박스 안 환경은 이미지·정책이 정하고 E2는 키·봉인 폴더 변수를 뺀 환경으로 부르므로(`CHILD_ENV_DROP`) 전달 경로가 하나 더 생긴다. 명령 인자가 실행 조건에 그대로 남아 재현이 분명하다. 채택하지 않았다.
- `tradesentry sealed-run-case` 새 하위 명령: 옵션 하나보다 큰 공용 약속 변경이고 배선을 둘로 나눈다. 채택하지 않았다.

## 바뀐 파일

- `src/tradesentry/cli/args.py`: `SEALED_OPTION`·`SEALED_HELP`·`SEALED_WITH_REPLAY`, `Request.sealed`, `build_parser`(run-case에 `--sealed`), `parse`(`--sealed`+`--replay` 인자 오류).
- `src/tradesentry/cli/dispatch.py`: `SEALED_RUN_CASE_DATASETS`, `SEALED_REAL_DATASET`, `SEALED_SYNTHETIC_REFUSAL`, `SEALED_REAL_REFUSAL`, `sealed_real_case_scope`, `run_case_in`의 분기, 머리 설명.
- `src/tradesentry/evaluation/sandbox_exec.py`: `SandboxCaseRunner(sealed=)`, exec 인자 `--sealed`, 머리 설명 2.
- `src/tradesentry/evaluation/sealed_runner.py`: `SandboxCaseRunner(..., sealed=sealed)`, 머리 설명 4.
- 시험: `tests/units/F1/test_args.py`(`SealedTest`, `RunTest` 필드), `tests/units/F1/expected.json`(`sealed: false`), `tests/units/F2/test_run_case_command.py`(`SealedFlagTest`·`SealedDatasetTableTest`), `tests/units/F2/test_run_case_real.py`(봉인 계열 4건), `tests/units/F2/test_evaluate_sandbox.py`(`--sealed` 없음), `tests/units/E2/test_sealed_runner.py`(두 봉인 묶음의 exec 인자 끝 `--sealed`).
- 문서: 자료 계약 §10 CLI 행, `docs/plan/UNITS.md` F1·F2·E2 행, `skills/tradesentry-eval/SKILL.md` 명령 절, `docs/tracking/findings.md`, 이 기록과 색인.

## 시험

- 회귀 시험 `tests/units/F2/test_run_case_command.py::SealedFlagTest`는 고치기 전 코드에서 실패한다(`AttributeError: module 'tradesentry.cli.dispatch' has no attribute 'SEALED_RUN_CASE_DATASETS'`. 같은 코드의 F1은 `--sealed`를 "unrecognized arguments: --sealed"로 종료 2). 고친 뒤 통과.
- 전체: `env -u NVIDIA_API_KEY -u DATA_GO_KR_SERVICE_KEY -u TRADESENTRY_SEALED_DIR uv run --locked python -m unittest discover -s tests` 종료 0(건수는 PR 본문에 적는다).

## 남은 것

- 사용자 승인(공용 약속 변경). 승인 뒤 PR·squash 병합, 전용 샌드박스 이미지 재스테이징(이미지 기록의 커밋 = 호스트 `code_version`이어야 사전 점검을 지난다), 봉인 묶음 재시작(중단 묶음의 처리는 봉인 사건 기록).
- `docs/tracking/status.md`는 오케스트레이터가 고친다.
- 실제 봉인 `holdout40` 비교국 표의 `grouping_version`이 `g0`인지는 봉인 폴더를 열지 않아 `[추론]`이다(④). 공식 실행에서 E2의 `STATIC_KEYS` 대조가 어긋나면 그 사례는 `FAILED`로 분모에 남는다.
