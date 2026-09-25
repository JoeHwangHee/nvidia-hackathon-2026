# MT7 두 번째 PR: 샌드박스 밖 실행기(단위 E2)의 이름·명령·순서 seed·경계와 리허설

로드맵 MT7의 "F1 전" 항목(결정 D17과 같은 방식의 추가 수정 PR) 가운데 샌드박스 밖 실행기(단위 E2 `src/tradesentry/evaluation/sealed_runner.py`)를 구현하며 정한 것을 적는다. 앞 기록 `20260925-0600-model-decision-mt7-harness.md`의 "다음 PR" 1~4에 답한다. 채점 규칙·판정 정책·검증기·채점기(`eval/scorer/`)·`configs/`·CLI 명령 표는 바꾸지 않았다.

용어

- 샌드박스 밖 실행기(단위 E2): 봉인 묶음(holdout40·`real_sealed`. 평가 전까지 개발 과정에 노출하지 않도록 저장소 밖 봉인 폴더에 두는 평가 자료)을 룰북 `RB-1`(평가 룰북의 첫 동결 버전) 동결 뒤 공식 채점 대상 실행 전용 샌드박스(OpenShell 샌드박스)에서 돌리는 호스트 쪽 프로그램. 봉인 해시를 대조하고, 봉인 사례를 읽어 사례 식별자를 샌드박스 안 `run-case`에 한 건씩 넘기고, 내려받아 묶음 기록과 실행 조건 입력 파일을 쓴다(룰북 B5·B6·부록 40번).
- 묶음 고리(단위 E1 `batch_run`): (사례 × 모드) 순서 섞기, 실행명 확보(N8), 묶음 기록 한 줄씩 쓰기, 인프라 실패 재실행(룰북 B5), 속도 조절(HTTP 429 막기), 실행 조건 입력 파일 만들기. 사례를 호스트에서 돌리지 않는다.
- 보조 파일(`sandbox_exec.py`): 단위 표의 새 단위가 아니라 단위 E2 행에 덧붙인 파일. 샌드박스 안 `run-case` 호출·받기 전 확인·내려받기·격리와 사전 점검을 담는다.
- 실행 조건 입력 파일: 채점기가 모르는 실행 조건(순서 seed·동시성·한도·샌드박스 이름·운영자 값 등)을 내려받기를 끝낸 호스트 쪽 프로그램이 채점기에 넘기는 파일 `run_conditions-{시각}.json`(자료 계약 §8.2).
- 리허설: 봉인 배치를 흉내 내어 E2로 dev20(봉인 아님)을 돌리고 채점기가 파일 세 개를 내는지 임시 위치에서 확인하는 시험(로드맵 MT7).

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-26(토) 08:05(기록 시각). 바탕은 `main` dc9e76b(봉인 해시 등록 #79 뒤) |
| 제목 | 단위 E2의 실행 이름·묶음 기록 도메인명·명령·순서 seed·비교 대상 집합, E2 ↔ E1 import 경계, 샌드박스 백엔드의 보조 파일 분리, 봉인 파일 읽기 순서, 표준 출력 위생, 리허설 |
| 결정 | 아래 "결정 내용" ①~⑨ |
| 결정 주체 | 오케스트레이터가 정한 것(①·②·③·④·⑥)은 `[DESIGN: 오케스트레이터 결정]`, 구현 세부(⑤·⑦·⑧·⑨)는 소유 트랙(M) |
| 공용 약속 여부 | 자료 계약 §8.2·§10.3 N5의 `[미확인]` 두 자리(E2의 묶음 기록 도메인명, 봉인 묶음 실행 폴더의 실행 이름)를 채우는 값이라 **공용 약속(이름·경로) 변경이다**. 이 PR은 공용 약속 문서(`docs/rules/`)를 고치지 않았다. 아래 "채점기·문서가 맞춰야 할 이름"의 문장을 사용자 승인 뒤 문서 PR로 넣는다. CLI 명령 표(`tradesentry <명령>`)에 새 명령·옵션을 더하지 않았다(`[해석]`: 로드맵 MT7이 E2를 "프로그램"이라 했고, 자료 계약 §10 표에는 채점기처럼 `python -m` 형식이 이미 있다). 순서 seed 값은 `RB-1`과 함께 동결하는 조정값이다 |
| 관련 PR | 브랜치 `model/MT7-sealed-runner` |

## 결정 내용

① **이름과 폴더** `[DESIGN: 오케스트레이터 결정]` — 봉인 묶음 실행의 실행 이름은 `sealed_evaluate`, 폴더는 `outputs/sealed/sealed_evaluate-{시각}/`(N5·N8·N10). 사례 실행은 `outputs/sealed/run_case-{시각}/`(부모 `outputs/sealed/`, 다른 부모 `outputs/`와의 이름 충돌 확인은 E1 규칙 그대로). 묶음 기록 도메인명은 단위 E2의 도메인명 `evaluation_sealed_runner`, 파일 `evaluation_sealed_runner-{시각}.jsonl`(줄 형식은 E1 `evaluation_batch_run`과 같다). 실행 조건 입력 파일은 같은 폴더의 `run_conditions-{시각}.json`(§8.2). 단위 E3·E4의 `BATCH_DOMAINS`에 `"sealed_evaluate": "evaluation_sealed_runner"`를 더했다(E3는 E2 묶음 기록에서 재실행 대상 목록을 낼 수 있다. E4는 봉인 자리를 읽지 않으므로 이름만 안다).

② **명령** `[DESIGN: 오케스트레이터 결정]` — `python -m tradesentry.evaluation.sealed_runner --dataset {holdout40|real_sealed} --sandbox <전용 샌드박스 이름> --snapshot <스냅샷 ID> --policy <정책 버전> [--conditions-extra <JSON 상대 경로>]`. 저장소 루트에서 부른다. `--mode`는 받지 않는다(봉인 묶음은 스모크 없음. 모드는 E1 `PLANNED_MODES`: holdout40 = `checklist`·`agent`·`full`, `real_sealed` = `freeform`·`full`, 룰북 B2). 인자 형식은 단위 F1의 정규식(스냅샷 ID·정책 이름·상대 경로 조각)과 같고, 샌드박스 이름은 `scripts/openshell_violation_tests.py`의 `SANDBOX_NAME_RE`와 같다. 종료 코드: 0 묶음 기록을 끝까지 씀(사례 실패 포함, E1과 같다), 1 준비·실행 중 오류(사전 점검 실패 포함, `outputs/`에 쓰기 전), 2 인자 오류·봉인 해시 불일치(`outputs/`에 아무것도 쓰지 않는다).

③ **순서 seed** `[DESIGN: 오케스트레이터 결정, 조정값]` — 봉인용 순서 seed 상수 `SEALED_ORDER_SEED = "rb1-order-v1"`(E2). 개발용은 `dispatch.DEV_ORDER_SEED = "dev-order-v1"`(다르다). `RB-1`과 함께 동결하는 값이며(룰북 B5), 실행 조건 입력 파일 `order_seed`와 `prescoring_checks.seed_concurrency`에 적힌다. 섞는 규칙은 E1 `plan_order`(sha256 열쇠) 그대로 쓴다(앞 기록 ①의 "따로 구현"은 ④로 필요 없어졌다).

④ **E2의 import 경계** `[DESIGN: 오케스트레이터 결정]` — 단위 표 E2 행의 옛 문장("E1을 import하지 않는다")은 "사례를 호스트에서 돌릴 수 없게"가 목적이었다. E1은 사례를 돌리지 않는 순수 묶음 고리이므로 E2가 E1을 import해 `execute_batch`·`plan_order`·N8 확보·속도 조절·재실행·실행 조건 함수를 재사용한다. 대신 `tradesentry.workflow`·`tools`·`policy`·`metrics`·`cli`·`ingest`와 `eval.scorer`는 직접이든 간접이든 import하지 않는다(경계 시험 `tests/test_boundaries.py` 4번을 그렇게 고쳤다. 9번 E1 → E2 금지와 8번 CLI → E2 금지는 그대로). E1 `execute_batch`에 `sealed`·`run_name`·`domain` 인자를 더해 봉인 실행이면 봉인 묶음만·`outputs/sealed/` 아래만 받는다(반대도 막는다). E1의 골든·시험은 바뀌지 않았다.

⑤ **샌드박스 백엔드의 보조 파일 분리** — `dispatch.py`에 있던 샌드박스 백엔드(`_openshell`, `sandbox_preflight`, `_scan_download`, `SandboxCaseRunner`, `sandbox_request`, `SANDBOX_*`·`CHILD_ENV_DROP` 상수, 정책 파일 sha256, `code_version`·`image_code_version`)를 새 모듈 `src/tradesentry/evaluation/sandbox_exec.py`(허용 import: 표준 라이브러리, `tradesentry.contract`, `tradesentry.runlog`, `tradesentry.evaluation.batch_run`)로 옮겼다. dispatch는 같은 이름으로 다시 내보내고(`SandboxCaseRunner`는 시험 대역 자리 `_scan_download`를 거치는 하위 클래스) 동작이 같다(기존 F2 `evaluate` 시험 33개 불변이 증거). 단위 F1 정규식·NAT 파일 이름·I12 임계값 규칙은 옮겨 적고 시험이 원본과 대조한다. 등록부에 `AUXILIARY_FILES`(보조 파일 → 단위 ID)를 두어 단위 패키지 안의 비단위 파일을 이것만 허용한다(`tests/test_units_registry.py`). E2 파일 자체는 경계 시험 7번(문자열 상수 속 `tradesentry` 금지) 때문에 재현 명령 문자열과 봉인 폴더 기본값(`.tradesentry`)을 보조 파일의 상수로 둔다.

⑥ **봉인 파일 읽기 순서와 사례 식별자 위생** `[DESIGN: 오케스트레이터 결정]` — ⑴ `eval/sealed_manifest.json` 전체를 봉인 폴더(환경변수 `TRADESENTRY_SEALED_DIR`, 비어 있으면 홈 폴더의 `.tradesentry/sealed/`)의 파일 전체와 대조한다(목록 파일 전부 존재·해시 일치, 목록 밖 항목(링크·OS 메타데이터 파일 포함) 없음). 불일치면 종료 코드 2, `outputs/` 무변경. 표준 출력에는 파일 수·일치 수·불일치 수·목록 밖 항목 수만, 이름은 목록 안 파일만. ⑵ `real_sealed`: 목록에서 `dataset`이 `real_sealed`이고 `file_name`이 `real_sealed/sample-`로 시작하는 항목 하나(둘 이상이면 오류)를 읽어 `cases`(case_id 문자열 목록)와 `snapshot_id`·`policy_version`을 인자와 대조하고, `case_id` `{hs6}-{partner}-{month}`를 풀어 계획 사례 네 키를 만든다(`[해석]`: 표본 파일은 식별자만 담고, 판정 정책 식별자 형식이 그렇게 정해져 있다. 표본의 사례 내용 파일 `policy_case_build-*.json`은 읽지 않는다). holdout40: `holdout40/input/cases.json`의 `cases[]` 네 키(정답표·`answers/`·`gen/`은 읽지 않는다). 파일마다 읽기 직전에 해시를 다시 대조한다. 표본 추출 seed 파일은 읽지 않는다. 표본·cases.json에 `snapshot_id`·`policy_version`(holdout40은 `dataset`·`snapshot_id`)이 없으면 대조를 생략하고 표준 오류에 알림 한 줄(값 없음)을 낸다. ⑶ 사례 식별자는 표준 출력·표준 오류·예외 문장·로그 어디에도 내지 않는다(건수만. 예외는 이름만 적는다). 시험이 두 표준 흐름에 식별자가 없는지 본다. 식별자가 `openshell sandbox exec` 인자로 프로세스 목록에 보이는 것은 룰북 B6 "정직한 한계" 그대로다.

⑦ **실행 조건 입력 파일과 NAT 사후 평가** — E1 `build_run_conditions`로 만들고 `sandbox.name`·`policy_yaml_sha256`, `reproduce_evaluate`(②의 명령을 옵션 그대로), `prescoring_checks.final_status`·`seed_concurrency`를 채운다. `--conditions-extra`는 E1 `check_operator_conditions(doc, dataset)`·`merge_operator_conditions`로 합친다(봉인 묶음의 `SEALED_FORBIDDEN` 거부 그대로). 채점기가 봉인 묶음에서 요구하는 값(`rulebook`, `scorer_commit`, `prose_patterns_commit`, `sealed_hash_recheck`(반드시 `"일치"`), `sealed_provenance_check`, `precheck`, `real_sealed`이면 `a_grade`)은 운영자 실행 조건으로 준다(운영자 키라 E2가 채우지 않는다). 시험이 그렇게 만든 파일이 채점기 `read_conditions(sealed=True)`를 지나는지 본다. 단위 E4 `summarize_batch`는 봉인 자리를 읽지 않으므로(E4 규칙, 자료 계약 §8.2) E2는 E4를 부르지 않고 `nat_profile_summary`를 넣지 않는다(`[해석: 오케스트레이터 승인 2026-09-26(토) 08:25]`: `nat_eval.py` 머리 설명의 봉인 규칙 "봉인 묶음은 읽지 않는다"와 일치하는 해석). 비교 대상 집합 `grouping_version`은 `g0`(E2 상수 `SEALED_GROUPING_VERSION`. 실자료는 `g0` 대체(로드맵 §6.1), 합성은 자료 안 `g0` 규칙의 `peer_group`(시나리오 명세). E2는 스냅샷을 열 수 없어 상수로 둔다 `[해석]`). 호스트 `code_version`은 git 메타에서 읽고 사전 점검이 이미지 기록의 커밋과 대조한다.

⑧ **표준 출력 위생** — 첫 줄 해시 대조 결과(건수), 둘째 줄 계획 사례 건수, 셋째 줄 확보한 실행 폴더의 `outputs/`부터의 상대경로, 끝에 상태별 건수(COMPLETED·FAILED·TIMEOUT·INVALID·BUDGET_EXCEEDED)와 재실행 대상·재실행 수, 모드별 사례 집합 일치 여부(참·거짓)·순서 seed·동시성, 종료 코드. 표준 오류에는 사전 점검 오류 문장, 내려받기 사건(실행명·건수), 운영자 조건 합침 알림(키 이름만). 사례 식별자·값·로컬 절대경로는 없다(N10·N13). 모드별 사례 집합 일치 여부는 파일에는 넣지 않는다(`prescoring_checks.mode_case_sets`는 운영자 키(결정 기록 conditions-extra)라 E2가 채우면 "두 번 줬다"가 된다. 평가 스킬 ② 채점 전 확인 5의 "E2가 입력 파일에 넣는다" 문장과 어긋나는 점은 `[미확인]`. 지금은 표준 출력의 참·거짓을 오케스트레이터가 운영자 조건으로 옮긴다).

⑨ **리허설(로드맵 MT7)** — `tests/units/E2/test_rehearsal.py`: 임시 저장소 사본에 dev20을 설치하고, E2 `run_sealed`에 자료 묶음 dev20·사례 20건·`outputs/` 부모·가짜 해시 목록·가짜 봉인 폴더를 인자로 주어 가짜 openshell로 60회 돌린다(재대조 단계 흉내 포함). 다른 부모(`outputs/sealed/`)에 첫 초의 이름을 미리 두어 N8대로 다음 초로 넘어가는지, 사례 실행명 60개가 서로 다른지, 실행 조건 입력 파일이 배타 생성되는지 본 뒤, 채점기 `python -m eval.scorer --run <run_dir>`(`BATCH_DOMAINS`를 시험 안에서 같은 값으로 monkeypatch. PR #82로 main에 이미 들어간 값과 같다)가 종료 코드 0으로 세 파일(`scorer_results`·`scorer_claims`·`scorer_summary`)을 내고 요약에 E2 재현 명령이 적히는지 본다. 채점기 파일은 고치지 않았다.

## 채점기·문서가 맞춰야 할 이름(채점기 두 값은 PR #82(`data/DT8-sealed-wiring`)로 이미 들어감 — 값 일치 확인. 문서 문장은 문서 PR)

| 어디 | 넣을 값 |
|---|---|
| `eval/scorer/__main__.py` `BATCH_DOMAINS` | `"sealed_evaluate": "evaluation_sealed_runner"` — PR #82로 이미 들어감. `origin/main` 27403a0의 값과 같음을 확인했다 |
| `eval/scorer/__main__.py` `SEALED_FILES` | holdout40 정답표 `"holdout40/answers/answers.json"`, `real_sealed` 표본 `"real_sealed/sample-260926065820.json"`(해시 목록 `eval/sealed_manifest.json`의 `file_name`) — PR #82로 이미 들어감. `origin/main` 27403a0의 값과 같음을 확인했다 |
| 자료 계약 §8.2 두 번째 항목의 마지막 문장 | "단위 E2의 묶음 기록 도메인명은 `evaluation_sealed_runner`(파일 `evaluation_sealed_runner-{시각}.jsonl`), 봉인 묶음 실행 폴더의 실행 이름은 `sealed_evaluate`(`outputs/sealed/sealed_evaluate-{시각}/`)다(로드맵 MT7, 결정 기록 `20260926-0805-model-decision-mt7-sealed-runner.md`)." |
| 자료 계약 §10.3 N5의 "단위 E2의 묶음 기록 도메인명과 봉인 묶음 실행 폴더의 실행 이름은 로드맵 MT7에서 F1 전에 정한다 [미확인]" | "샌드박스 밖 실행기(단위 E2)의 실행 이름은 `sealed_evaluate`, 묶음 기록 도메인명은 `evaluation_sealed_runner`다(결정 기록 `20260926-0805-model-decision-mt7-sealed-runner.md`)." N5 실행 이름 목록에 `sealed_evaluate`를 더한다 |
| 자료 계약 §10 계획 경로·명령 표 | 행 추가: 봉인 묶음의 샌드박스 밖 실행기 — `src/tradesentry/evaluation/sealed_runner.py`(보조 파일 `sandbox_exec.py`), 실행 `python -m tradesentry.evaluation.sealed_runner --dataset {holdout40|real_sealed} --sandbox <전용 샌드박스 이름> --snapshot <스냅샷 ID> --policy <정책> [--conditions-extra <JSON 상대 경로>]`, 출력 `outputs/sealed/sealed_evaluate-{시각}/` — 소유 M |
| 룰북 B5 "순서" | "봉인 채점의 순서 seed는 `rb1-order-v1`이다(E2 `SEALED_ORDER_SEED`)." |
| 평가 스킬 ② 사전 점검 단계 4의 9번 "부르는 형식은 S0 뒤에 정한다 `[미확인]`" | 위 명령으로 바꾼다("명령" 절에는 이 PR이 한 줄 더했다) |

## 검토한 대안

- E2가 E1을 import하지 않고 순서·확보·재실행을 다시 구현: 같은 규칙 두 벌은 어긋날 위험이 있고, E1은 사례를 돌리지 않으므로 경계를 한쪽으로 열었다(④).
- 샌드박스 백엔드를 dispatch에 두고 E2가 dispatch를 import: CLI 닫힘이 E2에 닿고(경계 8번) `.env`를 읽는 경로가 늘어 하지 않았다(⑤).
- CLI `tradesentry sealed-evaluate` 하위 명령: 명령 표(공용 약속) 변경이라 하지 않았다(②).
- E2가 스냅샷을 열어 `grouping_version`을 읽기: `tradesentry.dal`을 E2에 허용해야 한다. 상수 `g0`으로 두고 사전 점검·채점기의 버전 키 대조에 맡겼다(⑦).

## `[미확인]`

1. 세션이 끊겼을 때 잇는 기능(`--resume <실행 폴더>`, 평가 스킬 ② 공식 채점 단계 5의 "공식 실행 재개"). 이 PR에 없다. 끊기면 새 실행이 되고, 잇기는 사용자에게 올린다.
2. 채점 전 확인 5의 "모드별 사례 집합 일치"를 E2가 파일에 넣을지(운영자 키 `prescoring_checks.mode_case_sets`와 충돌, ⑧).
3. 재대조 뒤 실행 조건 입력 파일을 만드는 호출이 E2와 같은 실행으로 남는가(로드맵 MT7): 지금은 같은 실행(같은 폴더·같은 시각)이며 채점 직전의 재대조는 평가 스킬 ②가 따로 한다. N6 예외는 필요 없다.
4. holdout40 봉인 입력의 샌드박스 반입 방식과 그 스냅샷 ID(E2는 `--snapshot` 값을 `cases.json`의 `snapshot_id`와 대조만 한다).
5. `openshell logs`에 사례 식별자가 남는지(평가 스킬 ②의 `[미확인]` 그대로).
6. 자료 계약 §8.2·§10.3·§10 표와 룰북 B5·스킬 문장의 확정(위 표. 사용자 승인 뒤 문서 PR).
