# AS3 코드 PR: `tradesentry evaluate`에 운영자 실행 조건 옵션 `--conditions-extra` — 채점기가 이미 읽는 키를 채우는 배관

평가 묶음 실행(`tradesentry evaluate`)이 스스로 채우지 못하는 실행 조건을 운영자가 JSON 파일로 넘겨 실행 조건 입력 파일(채점기가 모르는 실행 조건을 채점기에 넘기는 파일, 자료 계약 §8.2)에 합치는 선택 옵션을 더한 기록이다. 채점 규칙·요약 양식·자료 계약의 키와 형식은 바꾸지 않았다.

용어

- 실행 조건 입력 파일: 평가 묶음 실행 폴더 `outputs/evaluate-{시각}/`의 `run_conditions-{시각}.json`. 채점기(`eval/scorer`)는 요약 0절·4절에 옮길 실행 조건을 이 파일에서만 읽는다(자료 계약 §8.2). 키 집합은 단위 E1(`src/tradesentry/evaluation/batch_run.py`)의 `CONDITION_KEYS`다.
- 하네스가 채우는 키(`HARNESS_CONDITION_KEYS`): 실행이 스스로 아는 값. `dataset`, `planned_cases`, `planned_modes`, `policy_detection_thresholds`, `snapshot`, `order_seed`, `concurrency`, `limits`, `run_period`, `nat_profile_summary`, `reproduce_evaluate`, 그리고 하위 키 `sandbox.name`·`sandbox.policy_yaml_sha256`(샌드박스 백엔드), `prescoring_checks.final_status`·`seed_concurrency`.
- 운영자 실행 조건(`OPERATOR_CONDITION_KEYS`·`OPERATOR_SUBKEYS`): 운영자만 아는 값. `rulebook`, `grouping_reason`, `scorer_commit`, `prose_patterns_commit`, `sealed_hash_recheck`, `sealed_provenance_check`, `precheck`, `skill_call_success`, `korean_sample_review`, `a_grade`, 하위 키 `sandbox.live_policy_sha256`·`sandbox.violation_tests_run`, `prescoring_checks.version_keys`·`mode_case_sets`·`concurrency_record`.

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-26(토) 01:55(기록 시각). 바탕은 `main` 539f306 |
| 제목 | `tradesentry evaluate --conditions-extra <JSON 상대 경로>`: 운영자 실행 조건을 실행 조건 입력 파일에 합친다 |
| 결정 | 아래 ①~⑥ |
| 결정 주체 | 소유 트랙(M). 오케스트레이터 지시(AS3d) |
| 공용 약속 여부 | 실행 조건 입력 파일의 키·형식(`CONDITION_KEYS`), 채점기의 판정·집계 규칙과 요약 양식, 검증기·판정 정책, 원인 분류 코드, 보고서 필드, 예산, `configs/`는 바꾸지 않았다. 채점기는 `tradesentry`를 import하지 않는다(그대로). CLI에 선택 옵션 하나가 늘었다. 자료 계약 §10 CLI 행에는 이 옵션이 아직 없으므로(§10 CLI 행은 `--run-name`까지 적는다) 그 행에 한 줄을 더하는 일은 문서 PR과 사용자 확인 대상으로 남긴다(아래 "남은 것") |
| 관련 PR | 브랜치 `model/AS3-conditions-extra` |

## 까닭

- 자기채점 1회차(`artifacts/scorecard/scorecard-260926013020/scorecard-260926013020.md`) 규범 G2·G6이 FAIL인 까닭의 하나는 채점 요약 0절·4절에 "미기재(실행 조건 입력 파일에 없음)"로 남은 값들이다: 라이브 정책 조회 본문 sha256, 대조한 시험표 실행 폴더 이름(G2, 스킬 2단계 4의 대조 조건), 스킬 호출 성공률(G6, 체크리스트 1번 (나)), 그리고 채점기·산문 패턴 목록 커밋, 사전 점검 결과, 룰북 동결 정보 `[사실]`.
- 채점기는 이 값들을 이미 읽는다(`eval/scorer/summary.py`의 `_conditions_lines`·`_a_grade`·4절). 값이 실행 조건 입력 파일에 없어서 미기재였다. 룰북 B7의 `[미확인]` 항목(실행 조건 입력 파일의 이름·형식·누락 처리)은 그대로다.
- 하네스는 이 값들을 알 수 없다(라이브 정책 조회는 OpenShell 증거 폴더에, 스킬 호출 성공률은 NemoClaw 경로에, 채점기 커밋은 채점 쪽에 있다). 운영자가 아는 값을 넘기는 입구가 필요했고, 실행 조건 입력 파일은 "내려받기를 끝낸 호스트 쪽 프로그램이 배타 생성"(자료 계약 §8.2)하므로 그 프로그램인 `evaluate`가 합치는 것이 계약과 맞는다.

## 결정 내용

① **옵션(단위 F1 `src/tradesentry/cli/args.py`)** — `evaluate`만 받는 선택 옵션 `--conditions-extra <JSON_PATH>`. `--run-name`처럼 옵션 역할 표 `COMMAND_OPTIONS` 밖에 둔다(공통 옵션 셋을 바꾸지 않는다). 한 번만 적는다(`_Once`). 값은 모양만 본다: 비어 있지 않고, 공백·제어 문자(유니코드 Cc·Cf·Zl·Zp)가 없고, `/`·`\`·`~`·드라이브 문자로 시작하지 않는다. 오류 문장(`CONDITIONS_EXTRA_RULE`)은 값을 되풀이하지 않는다(N13). 상대 경로만 받는 까닭은 ③이다. `Request`에 `conditions_extra`(없으면 `None`) 필드가 늘어 단위 F1 골든 `expected.json`에 `"conditions_extra": null`이 더해졌다.

② **파일과 검사(단위 E1 `check_operator_conditions`, 배선 `dispatch.load_operator_conditions`)** — 파일은 JSON 객체다(소수는 `Decimal`로 읽는다). 실행 폴더를 만들기 전(사례 목록을 읽기 전)에 읽고 검사해, 틀리면 종료 코드 1로 끝나고 `outputs/`에 아무것도 남기지 않는다. 검사 순서: 하네스가 채우는 최상위 키가 있으면 "실행 조건 {키}를 두 번 줬다(하네스가 채우는 키다)" → `CONDITION_KEYS` 밖 키는 "약속 밖 키" → `sandbox`·`prescoring_checks`는 객체이고 하위 키가 `OPERATOR_SUBKEYS`만(하네스 하위 키 `name`·`policy_yaml_sha256`·`final_status`·`seed_concurrency`나 약속 밖 하위 키는 "하네스가 채우거나 약속 밖이다") → 봉인 묶음이면 `SEALED_FORBIDDEN`(`korean_sample_review`. `nat_profile_summary`는 하네스 키라 앞 단계에서 이미 막힌다) → 값의 로컬 절대경로 모양(N13)·키 모양(절대 규칙 1)은 기존 `PATH_SHAPE`·`SECRET_SHAPE` 그대로. 파일 없음·읽기 오류는 예외 이름만, JSON 아님은 사실만 적는다(경로·내용은 되풀이하지 않는다). `evaluate`는 봉인 묶음을 돌리지 않지만 함수는 자료 묶음을 받아 봉인 규칙을 함께 검사한다(샌드박스 밖 실행기 E2가 같은 함수를 쓸 수 있게).

③ **합치기(단위 E1 `merge_operator_conditions`)** — 값이 모두 모인 뒤(NAT 사후 평가와 `prescoring_checks` 뒤, `build_run_conditions` 앞) `extra`에 합친다. `sandbox`·`prescoring_checks`는 하네스 객체가 있으면 하위 키를 더하고(같은 하위 키는 "두 번 줬다"), 없으면(호스트 백엔드는 `sandbox`를 만들지 않는다) 운영자 하위 키만 든 객체가 된다. 다른 키는 `extra`에 이미 있으면 "두 번 줬다". 합친 결과는 기존 `check_run_conditions`(약속 밖 키, 필수 키, 봉인 규칙, 경로·키 모양)를 그대로 지난다. 재현 명령 `reproduce_evaluate`(룰북 B7)에는 ` --conditions-extra <준 경로 그대로>`를 `--mode` 뒤에 적는다. 이 문자열도 N13 검사를 지나므로 로컬 절대 경로는 어차피 거부되며, 그래서 F1이 상대 경로만 받고 안내 문장에 그렇게 적는다. 상대 경로의 기준은 `evaluate`를 부른 작업 폴더(저장소 폴더)다.

④ **알림** — 합치면 표준 오류에 한 줄: "알림: --conditions-extra의 운영자 실행 조건을 실행 조건 입력 파일에 합쳤다(키: a_grade, …, sandbox.live_policy_sha256, …)". 키 이름(하위 키는 점으로)만 적고 값은 적지 않는다. 옵션이 없으면 실행 조건 입력 파일과 표준 오류가 전과 같다(골든 불변).

⑤ **시험** — 단위 F1(`ConditionsExtraTest` 2개: evaluate만 받음·한 번만·상대 경로 허용, 절대·홈·드라이브·공백·제어 문자 거부와 값 비반복), 단위 E1(`RunConditionsTest` 3개: 허용 키 = `CONDITION_KEYS` − 하네스 키와 하위 키 표, 합치기와 합친 결과의 `build_run_conditions` 통과, 거부 15종과 봉인 묶음 `korean_sample_review` 거부·합치기 충돌), 단위 F2(`test_evaluate.py` 4개: 호스트 백엔드에서 채점기 키 이름 그대로 합침·재현 명령·알림에 값 없음, `sandbox` 합치기 함수, 옵션 없을 때 키 집합 불변, 파일 없음·JSON 아님·객체 아님·하네스 키·약속 밖 키·하위 키·경로 모양·키 모양의 13종이 `outputs/` 없이 종료 1; `test_evaluate_sandbox.py` 1개: 샌드박스 백엔드의 `name`·`policy_yaml_sha256`과 운영자 하위 키가 한 객체, `name`을 주면 새 실행 폴더 없이 거부), 채점기 요약(`tests/test_scorer_summary.py` 1개: 합친 값이 요약 0절·4절 문자열에 그대로 나타나고 그 줄에 미기재가 남지 않음. 채점기 코드는 바꾸지 않았다).

⑥ **문서** — 평가 스킬 ② `skills/tradesentry-eval/SKILL.md` "결과 보고"의 실행 조건 입력 파일 항목에 이 옵션과 운영자 값의 예를 한 항목으로 더했다. `docs/contracts.md`에 인터페이스 한 줄. 자료 계약의 키·형식은 바꾸지 않았다.

## 남은 것

- 자료 계약 §10 CLI 행의 문장은 2026-09-26(토) 02:12 사용자 승인(결정 기록 `20260926-0212-user-decision-cli-options.md`)으로 같은 PR에서 §10.3에 더했다. 확인 대기는 끝났다.
- 운영자 값은 운영자의 자기 보고다. 라이브 정책 조회 본문 sha256과 시험표 실행 폴더 이름은 자기채점 스킬이 그 시험표의 `ts-scored` 행과 대조해 확인한다(스킬 2단계 4). 이 옵션은 값이 요약에 도달하게 할 뿐 값의 참을 보증하지 않는다.
- 봉인 묶음(`holdout40`·`real_sealed`)은 `evaluate`가 돌리지 않으므로 이 옵션도 봉인 묶음에 닿지 않는다. 샌드박스 밖 실행기 E2가 같은 함수(`check_operator_conditions`·`merge_operator_conditions`)를 쓰는 배선은 F1 뒤의 일이다.
- 상대 경로의 기준 폴더가 재현 명령에 적히지 않는다(저장소 폴더에서 부른다는 전제). 운영자 파일을 `outputs/` 밖 커밋되는 자리(예: `artifacts/eval/score-{시각}/`)에 증거 복사할지는 정하지 않았다.
