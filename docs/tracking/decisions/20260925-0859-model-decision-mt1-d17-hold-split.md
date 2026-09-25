# MT1 판정 정책 추가 수정 D17: 자료 보류를 사유별로 나눔

판정 정책(MT1, 모델 트랙)의 추가 수정 PR(브랜치 `model/MT1-d17-hold-split`)에서, 사용자 결정 14(`20260925-0847-user-decision-morning-shared-promises.md`)를 단위 P3(신호별 판정)·P5(필수 근거 규칙)에 옮기며 정한 것을 적는다. MT1 판정 정책 결정 기록(`20260925-0025-model-decision-mt1-policy.md`)의 ⑥·⑦·⑧·⑨·⑪ 일부를 이 기록이 고친다. 그 기록은 고치지 않는다.

용어

- 자료 보류: 신호별 상태 `HOLD` 가운데 판정 순서 1번(필요한 자료가 없거나 성립하지 않음)에서 끝난 것.
- 판정 근거(basis): P3이 신호마다 어느 규칙으로 상태를 정했는지 나타내는 이름. 단위 출력 이름이고 계약 값이 아니다(MT1 기록 ⑧).
- 필수 근거: 보고서가 그 상태를 내려면 남겨야 하는 근거 코드(P5 규칙표).
- 필수 비교: 판정 근거를 내기 전에 끝나 있어야 하는 조사 단계(비교 조건 점검 `comparability`, 비교국 비교 `partners`, 해당국 금액과 전체국가 분모 변화 확인 `country_and_world`).
- `gaps`: P3 출력에서 신호마다 1번이나 5번에 걸린 항목 목록. 항목마다 사유(`reason`)가 붙는다.
- dev20: 모든 에이전트가 쓰는 공개 합성 개발 자료 20건(`eval/dev/dev20/`).
- 짝 PR: 같은 결정 14를 데이터 트랙에서 맞추는 PR(브랜치 `data/DT8-d17-evidence-table`, 시나리오 명세와 독립 채점기).

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 08:59(기록 시각). 결정은 같은 날 08:50~08:59 구현 중에 했다. 작업 중 main에 조립 AS2(PR #38)가 병합되어 이 브랜치를 그 위로 옮기고, 단위 I10의 판정 근거 한국어 이름과 "영향과 넘길 곳"을 고쳤다 |
| 제목 | 자료 보류의 사유별 판정 근거(`data_insufficient` / `data_inconsistent`), 겹칠 때의 우선순위, 새 판정 근거의 필수 근거, 필수 비교를 따지는 판정 근거의 범위, 점유율 분모 불완전의 입력 자리 |
| 결정 | 아래 "결정 내용" ①~⑥ |
| 이유와 근거 | 항목마다 적었다 |
| 검토한 대안 | 아래 "검토한 대안" |
| 결정 주체 | 소유 트랙(M). 필수 근거 목록(③)은 사용자 결정 14를 글자·순서 그대로 옮겼다 |
| 공용 약속 여부 | 필수 근거 목록(③)은 사용자 결정 14(공용 약속, 평가 구성)가 정했고 이 기록은 옮기기만 한다. 판정 근거 이름 `data_inconsistent`는 M 소유 단위의 출력 이름이라 공용 약속이 아니다. 계약 필드·상태값·ID·기준값은 바꾸지 않았다 |
| 영향 | 아래 "영향과 넘길 곳" |
| 관련 PR | 이 기록의 PR(브랜치 `model/MT1-d17-hold-split`), 짝 PR(`data/DT8-d17-evidence-table`) |

## 결정 내용

① **자료 보류를 판정 근거 둘로 나눈다** — 확정

- `data_insufficient`(빠진 관측): 그 계열에 배정된 비교월·기준월의 빠진 관측(`REQUEST_FAILED`·`NOT_COLLECTED`·`UNRESOLVED_ZERO`, `gaps` 사유 `missing_observation`)이 하나라도 있다. 계열 배정은 MT1 기록 ⑪ 그대로다(`ALL`은 점유율, 대상국 행은 단가).
- `data_inconsistent`(성립하지 않음): 빠진 관측은 없는데 1번의 다른 사유가 있다.
  - 비교 가능성 문제(`comparability_issue`): 두 달의 단위·HS 정의 차이, 점유율 분모가 대상국 금액보다 작음(④).
  - 부모·하위 대조 불일치(`parent_child_mismatch`).
  - 구성 분해 불가(`decomposition_unavailable`): 분해 null(두 달 HS10 집합이 다름 등), 분해 값 null.
  - 하위품목 단가 계산 불가(`child_unit_value_unavailable`, 하위 중량 0 등)와 기준월 단가 계산 불가(`baseline_unit_value_unavailable`).
- 신호마다 따로 정한다. 한 계열의 빠진 관측은 다른 계열의 판정 근거를 바꾸지 않는다(예: `ALL` 분모가 빠져 점유율이 `data_insufficient`여도 단가의 부모 대조 불일치는 `data_inconsistent`).
- 두 판정 근거 모두 상태는 `HOLD`다. 사례 집계(P4)는 바뀌지 않는다.
- 이유: 사용자 결정 14 (가). 빠진 관측이 없는 보류에 빠진 관측용 근거(`missingness_listed`·`failure_vs_not_collected_distinguished`)를 요구하면 보고서가 남길 수 없다(시나리오 명세의 §5.2, DT5 결정 기록 ⑤).

② **둘 다 있으면 빠진 관측 쪽(`data_insufficient`)** — 확정

- 한 계열에 빠진 관측과 다른 1번 사유가 함께 있으면 `data_insufficient`다. `gaps`에는 두 사유의 항목을 모두 싣는다(보고서·검증기가 볼 수 있게).
- 이유
  - 빠진 관측은 분해 불가·대조 불가 같은 뒤따르는 사유를 함께 부른다. oracle C(비교월 HS10 조회 실패)는 근거 상태에 빠진 관측과 부모 대조 불가·하위 단가 없음이 함께 있고, 기대 필수 근거는 빠진 관측용 셋이다(`eval/dev/oracle_ABC.json`, P5 시험). 이 우선순위라야 oracle C가 그대로 `data_insufficient`다.
  - 보고서가 남길 수 있는 근거가 빠진 관측의 목록과 상태 구분이다. 성립하지 않음의 근거(부모·하위 합계 대조, 분모 변화)는 빠진 자료 때문에 온전히 보일 수 없다.
- 시험: P3 `HoldSplitTest.test_overlap_prefers_missing_observation_and_keeps_all_gaps`, `test_oracle.py`(C는 `data_insufficient`).

③ **새 판정 근거의 필수 근거** — 확정(사용자 결정 14를 옮김)

- 단가 `data_inconsistent`: `parent_child_match_V_and_Q`, `comparability_ok`, `no_zero_fill`.
- 점유율 `data_inconsistent`: `country_and_world_change_shown`, `comparability_ok`, `no_zero_fill`.
- `data_insufficient`·`comparison_incomplete`는 지금 규칙(`missingness_listed`, `failure_vs_not_collected_distinguished`, `no_zero_fill`) 그대로다.
- P5 규칙표에서 두 계열 모두 `data_insufficient` 바로 뒤 행이다. P5 `run` 출력(조사자에게 가는 공개 필수 근거)에 이 행이 더해지고 설명 목록의 순서가 바뀐다(골든 `tests/units/P5/expected.json`).
- 새 근거 코드는 없다. 13개 어휘(MT1 기록 ⑨) 안이다. ⑨ 표의 "요구하는 판정 근거" 열에는 아래가 더해진다.
  - `parent_child_match_V_and_Q`: 단가 `data_inconsistent`
  - `comparability_ok`: 두 계열 `data_inconsistent`
  - `no_zero_fill`: 두 계열 `data_inconsistent`
  - `country_and_world_change_shown`: 점유율 `data_inconsistent`
- 이 코드들이 `data_inconsistent`에서 무엇으로 충족되는지(보고서의 어떤 typed claim·근거 ID)는 짝 PR의 판정 조건표가 정한다. 예: `comparability_ok`는 여기서 "비교 조건 점검이 통과했다"가 아니라 "점검 결과(성립하지 않음)를 보였다"로 읽혀야 한다.

④ **점유율 분모 불완전은 `comparability_issues`로 받는다** — 확정(MT1 기록 ⑪의 넣는 것에 더함)

- 점유율 계열의 `comparability_issues`에 관측된 전체국가(`ALL`) 분모가 대상국 금액보다 작은 달(분모가 전체 국가를 담지 못해 점유율이 100%를 넘음)을 넣는다. 하나라도 있으면 `HOLD`이고, 빠진 관측이 없으면 `data_inconsistent`다.
- P3에는 이 규칙이 이미 있었다(점유율 `comparability_issues`가 있으면 `HOLD`). 새 입력 키를 만들지 않았다. P3은 문자열의 글자를 읽지 않는다. 글자는 근거 상태를 만드는 조립(AS2)이 정한다. AS2(PR #38)는 `denominator_below_partner:{달}`을 쓴다(잠정, `src/tradesentry/cli/dispatch.py` `DENOMINATOR_BELOW_PARTNER`).
- 분모가 아예 빠진 달(관측 상태가 빠짐)은 지금처럼 `missingness`로 받아 `data_insufficient`다.

⑤ **필수 비교 완료는 후보 판정 근거에서만 따진다** — 확정

- P5 `required_comparisons`는 후보 판정 근거(`GATED_BASES` = `composition_explained`, `unexplained`, P3 판정 순서 4번)에만 비교를 돌려주고, 앞 단계에서 끝나는 판정 근거(`data_insufficient`, `data_inconsistent`, `comparison_incomplete`, `rounding_unstable`, `resolved_after_correction`)에는 빈 튜플을 돌려준다.
- 이유: 새 규칙의 필수 근거에 비교 코드(`comparability_ok`, `country_and_world_change_shown`)가 들어가서, 규칙표에서 기계적으로 뽑으면 `data_inconsistent`가 "판정 전에 끝나 있어야 하는 비교"를 갖게 된다. 이는 MT1 기록 ⑦ 불변식 (가)(1번 사유가 있으면 건너뛴 비교가 `not_performed`여도 `HOLD`)와 어긋난다. P3은 이 함수를 후보 판정 근거에만 부르므로 판정은 같지만, 뒤에 부를 쪽(조립 등)이 잘못 읽지 않게 함수 뜻을 좁혔다. `family_comparisons`(근거 상태가 담아야 하는 비교 키)는 그대로다.
- 시험: P5 `test_required_comparisons_follow_rule_evidence`, P3 `test_ga_stage1_reason_with_skipped_comparisons_is_hold`(비교를 모두 `not_performed`로 둔 조기 종료가 입력 오류가 아니라 `HOLD`(`data_inconsistent`)).

⑥ **도구 쪽 사유의 배정(해석)** — 확정

- 비교 가능성 조회(단위 I1)의 `signals.{계열}.issues`(`units_mismatch`, `no_trade:{달}`, `zero_weight:{달}`, `zero_baseline:{달}`, `zero_denominator:{달}`)는 빠진 관측이 아니다. AS2가 이것을 `comparability_issues`로 넘기면 `data_inconsistent`가 된다. 사용자 결정 14의 "관측은 모두 있는데 성립하지 않는 보류"에 든다고 읽었다.
- `CONFIRMED_NO_TRADE`(무거래 확정)로 한 달의 하위품목 집합이 달라져 분해가 null이면 `data_inconsistent`다(무거래 확정은 빠진 관측이 아니다, MT1 기록 ⑪).

## 검토한 대안

- 겹칠 때 `data_inconsistent`를 우선: oracle C가 `data_inconsistent`로 바뀌어 oracle의 필수 근거(빠진 관측용 셋)와 어긋나고, 빠진 자료 때문에 대조 근거를 남길 수 없는 보고서에 대조 근거를 요구하게 된다. 버렸다.
- 겹칠 때 두 규칙의 필수 근거를 합침: 한 신호에 판정 근거가 하나라는 P3 출력 모양과 규칙표(판정 근거 → 필수 근거 하나)를 깨고, 채점기 정답표 형식과도 맞지 않는다. 버렸다.
- `data_insufficient` 하나를 두고 `gaps` 사유로 필수 근거를 고름: 필수 근거가 판정 근거가 아니라 `gaps` 내용에 따라 달라져 P5의 "규칙은 신호 계열과 판정 근거마다 정해진다"를 깬다. 버렸다.
- `required_comparisons`를 규칙표에서 기계적으로 뽑는 채로 둠: P3 판정은 같지만 함수 뜻이 ⑦ (가)와 어긋난다(⑤). 버렸다.
- 점유율 분모 불완전을 새 입력 키(예: 분모 금액)로 받아 P3이 계산: 근거 상태 모양(MT1 기록 ⑪)과 AS2의 변환을 함께 바꿔야 하고, 이미 있는 `comparability_issues` 규칙으로 같은 판정이 나온다. 버렸다.

## 영향과 넘길 곳

- 시험 기대값을 바꾼 곳(P3 `tests/units/P3/test_decide.py`): 관측은 빠지지 않은 1번 사유의 기대 판정 근거를 `data_insufficient`에서 `data_inconsistent`로 바꿨다. `test_unusable_decomposition_is_hold_not_maintain`(7곳), `test_comparability_issue_is_hold`(1곳), 불변식 (가) 시험(2곳, 이름을 `test_ga_stage1_reason_with_skipped_comparisons_is_hold`로 바꿈). 상태(`HOLD`)는 모두 그대로다. oracle A/B/C 시험과 P3·P4 골든은 바뀌지 않았다. AS2 병합 뒤 조립 시험 `tests/units/F2/test_run_case_evidence.py` `test_null_decomposition_with_its_own_reason_is_hold`(1곳, 비교 가능성 조회의 `zero_weight` 사유)도 같은 까닭으로 `data_inconsistent`로 바꿨다(⑥).
- 새 시험: P3 `HoldSplitTest`(겹침, 다른 계열의 빠진 관측, 신호 독립, P5 규칙과 일치), `Dev20InconsistentHoldTest`(dev20 불일치 보류 5건의 근거 상태 모양에서 `data_inconsistent`와 정답표의 필수 근거. 사례 식별자와 필수 근거만 옮기고, 옮긴 값을 정답표와 대조한다), 불변식 (가) 시험에 조기 종료 두 경우. P5 `test_inconsistent_hold_evidence_follows_user_decision_14`.
- 짝 PR(데이터 트랙): 시나리오 명세의 §5.1 표의 `hold_inconsistent` 두 행 "단위 P5 판정 근거" 열을 `data_inconsistent`로, 점유율 행의 "없음(분모 불완전 규칙이 아직 없다)"을 `data_inconsistent`(④)로 적는다. `eval/datagen/holdout40_check.py` 88행 주석의 판정 근거 목록도 데이터 트랙이 맞춘다.
- 조립 AS2(작업 중 main에 병합됨, PR #38. 이 PR은 그 위로 옮겼다)
  - 이 PR에서 고친 것: 단위 I10 `src/tradesentry/workflow/investigator.py` `BASIS_LABELS`에 `data_inconsistent`의 한국어 이름("자료가 맞지 않아 검증 불가")을 더했다. 없으면 규칙 참고값 문구에 영문 이름이 그대로 나간다. 시험 `tests/units/I10/test_investigator.py` `BasisLabelTest`(P5 규칙표의 판정 근거마다 이름이 있음).
  - 넘길 곳(프롬프트 문구라 `config_version`을 올리고 모델 동작 검토가 필요해 이 PR에서 고치지 않는다): `configs/model/critic.txt`의 상태 뜻 "HOLD = 자료 부족·비교 미완료·반올림 불안정(U4)", `configs/model/investigator.txt`의 "HOLD(자료 보류) = 자료가 모자라 판단 불가", `investigator.py` `REFERENCE_UNAVAILABLE`의 "자료 부족(HOLD)은 조회한 자료가 비었을 때만이다"는 관측은 있는데 성립하지 않는 보류(dev20 20건 중 5건)를 모델이 `HOLD`로 내지 않게 밀 수 있다. 성립하지 않는 보류(부모·하위 합 불일치, 분해 불가, 분모가 대상국 금액보다 작음)를 넣어야 한다.
  - `src/tradesentry/cli/dispatch.py`의 근거 상태 변환은 ④의 분모 불완전 문자열을 점유율 `comparability_issues`에 넣는다(이미 그렇게 한다). 부모 대조·분해 불가는 `decomposition`으로 넘긴다(MT1 기록 ⑪ 그대로).
- 검증기(단위 R3)는 P5 규칙표를 import하지 않는다. 보고서가 판정 근거에 맞는 필수 근거를 싣는지 보는 판정 조건은 짝 PR의 판정 조건표를 따라 따로 맞춘다.
- 단위 표 `docs/plan/UNITS.md`의 P3·P5 행은 바꾸지 않았다.
- 두 번째 문서 PR(DOCS2): 개발 플랜 `docs/plan/DEV_PLAN.md` §6.3 표 1행("필요한 월·단위·HS정의·분모·구성자료가 없어 검증이 불가능", 반드시 남길 근거 "부족 항목, 실패/미수집 구분, …")은 빠진 관측 보류의 근거만 적고 있다. 관측은 있는데 성립하지 않는 보류의 근거(부모 대조, 비교조건, 0으로 채우지 않음 / 해당국·분모 변화)를 사용자 결정 14대로 반영한다. 이 PR은 고치지 않는다.
