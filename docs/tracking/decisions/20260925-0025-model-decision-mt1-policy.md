# MT1 판정 정책의 해석과 입출력 약속

MT1(판정 정책, 모델 트랙) 구현(단위 P1~P5, PR #22)에서 자료 계약이 정하지 않았거나 모델 트랙(M)에 맡긴 세부와, 검토 1회차(Codex(OpenAI의 코딩 에이전트 CLI) 교차 검토, 무역통계·관세 검토, 평가 방법론 검토)가 요구한 해석을 적는다. 코드와 시험은 PR #22에 있다. 항목마다 **확정** 또는 **잠정(사용자 확인 대기)**을 붙였다. 잠정 항목은 `policy_v1`(동결 판정 정책) 승인 요청에 사용자 확인 항목 U1·U2·U4로 올린다.

용어

- 판정 정책 단위: P1 신호 발동(`src/tradesentry/policy/trigger.py`), P2 사례 만들기(`case_build.py`), P3 신호별 판정(`signal_decide.py`), P4 사례 집계(`case_aggregate.py`), P5 필수 근거 규칙(`required_evidence.py`). 모두 `src/tradesentry/policy/` 아래다.
- θ: 정책의 단가 탐지 임계값(`thresholds.unit_value`, 단위 %. 개발용 정책 `dev-0.1`에서 30).
- 근거 상태: 사례 하나를 조사해 얻은 사실(빠진 관측, 비교 가능성, 구성 분해, 필수 비교 완료 여부)을 P3 입력 모양으로 모은 것. 도구 봉투(도구 5개의 공통 출력)에서 코드가 만든다.
- 판정 근거(basis): P3이 신호마다 어느 규칙으로 상태를 정했는지 나타내는 이름.
- 필수 비교: 판정 근거를 내기 전에 끝나 있어야 하는 조사 단계. 비교 조건 점검, 비교국 비교, 해당국 금액과 전체국가 분모 변화 확인이다.
- 정확값: 표시 자릿수로 반올림하기 전의 값. 지표 단위가 `fractions.Fraction`(오차 없는 분수)으로 준다.
- oracle: 개발용 합성 정답 예시 `eval/dev/oracle_ABC.json`(A 구성변화, B 잔존변화, C 자료누락).

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 00:25(기록 시각). ①~⑥·⑧~⑭는 2026-09-24(목) 23:25부터 MT1 구현과 검토 1회차에서 정했고, ⑦은 검토 1회차의 막는 지적을 고치며 2026-09-25(금) 00시대에 정했다 |
| 제목 | MT1 판정 정책의 정책 객체 키, 정확값 비교, 판정 순서, 필수 비교 완료 규칙, 판정 근거·필수 근거 이름, 사례 식별자, 근거 상태 입력 모양과 도구 쪽 약속 |
| 결정 | 아래 "결정 내용" ①~⑭ |
| 이유와 근거 | 아래 "결정 내용"의 항목마다 적었다 |
| 검토한 대안 | 아래 "검토한 대안" |
| 결정 주체 | 소유 트랙(M). ①은 DT1(단위 K4, 정책 수치 읽기)의 정책 파일 형식과 같다. 잠정 항목 ③·④·⑤는 사용자가 확인하면 확정한다 |
| 공용 약속 여부 | ③·④·⑤는 기준값(병렬 개발 규칙 §4.1)에 닿으므로 공용 약속으로 보고 사용자 확인을 받는다(같은 문서 §4.5: 애매하면 공용 약속으로 본다). ⑨의 필수 근거 코드 어휘를 DT5 정답표·DT8 채점기와 맞추는 일을 공용 약속 절차로 올릴지는 오케스트레이터가 정한다. 나머지는 M 소유 단위의 입출력 약속이라 공용 약속이 아니다. 계약 필드·상태값·ID 형식·기준값의 값을 바꾸지 않는다 |
| 영향 | 아래 "영향과 넘길 곳" |
| 관련 PR | #22 |

## 결정 내용

① **정책 객체 키** — 확정

- 판정 정책 단위는 정책 객체(단위 K4가 정책 파일에서 읽은 것)에서 `policy_version`, `thresholds.unit_value`(단가 탐지 임계값, %), `thresholds.share`(점유율 탐지 임계값, pp), `min_amount`(USD), `min_weight`(kg)만 읽는다. 읽는 곳은 P1의 `policy_values` 하나다.
- DT1(단위 K4)의 정책 파일 형식(`configs/policy_dev.json`, 승인 뒤 `configs/policy_v1.json`)과 같은 모양이다. 그 형식의 `schema_version`, `tolerance`, `confirmed_no_trade`는 판정 정책 단위가 읽지 않는다. 모르는 키 검사는 K4가 한다.
- 단위는 자료 계약 §11.2를 따른다(30%는 `30`, 10pp는 `10`). 임계값은 0보다 커야 한다. K4는 0을 허용하므로 P1이 더 엄격하다.

② **정확값 비교** — 확정

- P1의 발동 비교와 P3의 "기준 안" 비교는 표시 자릿수(자료 계약 §11.3)로 반올림하기 전의 정확값으로 한다. 지표 단위 X1·X2·X3의 metric 객체 `value`는 반올림값이므로 넘기지 않고 `exact_value`(Fraction)를 넘긴다. P1·P3은 int·Decimal·Fraction을 받고 float는 거부한다. 셈과 비교는 분수로 한다.
- 발동은 이상이다(`|r_U| ≥ θ`, `|d_s| ≥ 점유율 임계값`). "기준 안"은 미만(`<`)이다.
- 이유: oracle 머리의 `|r_U|>=30%`와 K4 설명의 `>=`를 따른다. 표시 자릿수는 보고서·검증기·채점기용이다(자료 계약 §11.3). 반올림값을 넘기면 경계에서 판정이 뒤집힌다(정확값 −29.96%는 미발동인데 표시값 −30.0은 발동). 시험은 P1·P3의 `ExactValueTest`다.

③ **`min_amount`·`min_weight` 적용** — 잠정(사용자 확인 대기, U2)

- 정책 값이 null이 아닐 때만 **단가 신호에만** 적용한다. 비교월·기준월의 부모 HS6 행 금액이나 중량 가운데 하나라도 최소 기준보다 작으면 단가 신호를 평가하지 않는다(`NOT_TRIGGERED`). 그 행은 데이터 품질 목록에 사유 `below_min_amount`·`below_min_weight`로 남기고 사례(`HOLD` 사례)로 만들지 않는다. null이면(`dev-0.1`) 적용하지 않는다.
- 이유: 근거인 677행(금액>0, 중량 0)은 단가 계산 문제다. 다만 개발 플랜 §2.2·§6.1은 점유율 경보 수에도 "최소 금액·중량 기준 적용 전"을 붙여, 점유율에도 닿을 수 있다고 읽힌다.

④ **"개별 하위변동·잔차가 기준 안"의 기준** — 잠정(사용자 확인 대기, U1에서 (가)와 (나) 가운데 고름)

- 지금 코드는 (가)다. 새 정책 키 없이 θ를 다시 쓴다. U0(기준월 부모 HS6 단가)에 대해 아래 셋을 모두 채우면 구성효과로 설명된다(`MONITOR`)고 본다.
  - `|within_effect + residual|×100 < θ×U0`
  - `|within_effect|×100 < θ×U0`, `|residual|×100 < θ×U0`
  - 모든 HS10 하위품목의 `|r_U@HS10| < θ`
- (가)는 "구성 변화가 없었으면 경보가 아니었다"는 읽기다. 같은 크기의 단가 하락만 있는 계열은 경보조차 되지 않으므로 탐지 정책과 앞뒤가 맞는다.
- (나): 구 개발계획(`Pasted markdown.md`) 151행의 허용잔차와 189행의 개별 안정성을 정밀도 기준의 별도 값으로 두고, D가 `real_dev`로 제안한다. 고르면 정책 파일·K4·P1 `policy_values`·P3 판정식을 함께 고친다.
- 두 해석은 결과가 크게 갈린다. 무역통계 검토의 합성 탐침에서는 r_U −30.43% 가운데 within이 −28.71%여도 (가)로는 `MONITOR`였다. 사용자가 (나)를 고를 때만 코드를 고친다.

⑤ **반올림 불안정 판정** — 잠정(사용자 확인 대기, U4)

- P3은 단가 신호의 `rounding_unstable`(참거짓)을 입력으로 받고, 참이면 `HOLD`(`rounding_unstable`)다. 이 값을 만드는 쪽은 아직 없다. 조립 전까지 근거 상태 변환은 늘 거짓을 넣는다. 그래서 룰북 B1 시나리오 6(작은 기준월 값·반올림 불확실, 기대 `HOLD`)을 `checklist`(모델 없는 고정 체크리스트 비교군)가 아직 맞히지 못한다.
- 제안(무역통계 검토): 부모 HS6 행의 V·Q로 중량 ±`tolerance.weight_rounding_kg` 구간의 r_U 범위를 구한다. 그 범위가 ±θ나 0을 가로지르면 불안정으로 본다. `HOLD`를 새로 만드는 규칙이라 사용자 확인 대상이다. 계산 위치(P3 안, 또는 근거 상태 변환·단위 X4)는 오케스트레이터가 정한다.
- 점유율에는 반올림 불안정 규칙이 없다. 점유율은 정수 USD 금액만 쓰고, 행마다 반올림된 것은 중량이다(자료 계약 §11.1).

⑥ **판정 순서(발동한 신호마다, 앞에서 걸리면 멈춘다)** — 확정

1. 자료 부족 → `HOLD`(`data_insufficient`)
2. 반올림 불안정(단가만) → `HOLD`(`rounding_unstable`)
3. 자료 교정 뒤 해소 → `MONITOR`(`resolved_after_correction`)
4. 후보 판정 근거: 단가는 ④에 따라 `composition_explained`(`MONITOR`)나 `unexplained`(`MAINTAIN`), 점유율은 늘 `unexplained`
5. 후보의 필수 비교(⑦)가 다 끝나지 않았으면 `HOLD`(`comparison_incomplete`), 다 끝났으면 후보대로

- 신호마다 따로 판정한다. 비교국 비교의 내용(다른 상대국의 동반 변화)과 분모 축소는 상태를 낮추지 않는다(개발 플랜 §6.3). 필요한 자료가 없으면 "설명되지 않는다"는 이유만으로 `MAINTAIN`을 내지 않는다.
- `resolved_after_correction`은 동결 스냅샷 하나로 도는 v1 실행에서는 늘 거짓이다. 교정 전후 스냅샷이 다를 때만 쓸 값이다. 조회 범위를 고친 재조회(룰북 B1 시나리오 9)에는 쓰지 않는다.

⑦ **필수 비교 완료 규칙** — 확정(검토 1회차 막는 지적의 수정)

- 근거 상태의 계열 블록에 `comparisons`를 둔다.
  - 단가: `comparability`(비교 조건 점검), `partners`(비교국 비교)
  - 점유율: 위 둘에 `country_and_world`(해당국 금액과 전체국가 분모 변화 확인)를 더한다
- 값은 `done` 또는 `incomplete`다.
  - `done`: 수행해서 결과를 얻었다. 비교국 일부에 제외 사유가 있어도 된다.
  - `incomplete`: 수행했지만 자료가 모자라 결과를 얻지 못했다. 예: 허용된 비교국이 모두 그 달 자료가 없다.
- 어느 판정 근거가 어느 비교를 요구하는지는 P5 규칙표의 필수 근거 코드에서 나온다(`comparability_ok`, `partner_comparison_done`, `country_and_world_change_shown`).
  - 단가 `MAINTAIN`: 비교 조건 점검과 비교국 비교가 `done`이어야 한다.
  - 단가 `MONITOR`(구성효과): 비교 조건 점검이 `done`이어야 한다.
  - 점유율 `MAINTAIN`: 셋 모두 `done`이어야 한다.
  - 하나라도 `incomplete`면 `HOLD`(`comparison_incomplete`)다. 빠진 관측의 `data_insufficient`와 다른 판정 근거다.
- 키가 빠지면 입력 오류(ValueError)다. `missingness`·`comparability_issues`를 포함한 근거 상태의 모든 키에 기본값이 없다. 수행하지 않은 비교를 `done`·`incomplete`로 꾸미지 않는다. 필수 비교를 하지 않은 흐름은 P3 입력을 만들 수 없으므로 실행 실패로 드러난다.
- 이유: 개발 플랜 §6.3 4행("필수 비교를 마쳤는데 설명되지 않거나 설명이 충돌")과 표 아래 문단, 그리고 그 표가 그대로 유지한다고 밝힌 구 개발계획 229행("최종 필수근거 충족 여부로 유지/보류")이다. 키 누락을 `HOLD`로 두면 배선 실수가 그럴듯한 자료 보류로 보인다(개발 플랜 §7.5). 그러면 룰북 B4의 "모든 사례를 보류했을 때의 점수" 쪽으로 점수가 부푼다.

⑧ **판정 근거 이름과 단위가 정한 출력 이름** — 확정

- 판정 근거 7개: `not_triggered`, `data_insufficient`, `comparison_incomplete`, `rounding_unstable`, `resolved_after_correction`, `composition_explained`, `unexplained`. 판정 근거 → 상태의 대응은 P5 규칙표 하나에만 있다.
- P3 빈틈 사유(`gaps` 항목의 `reason`) 7개: `missing_observation`, `comparability_issue`, `decomposition_unavailable`, `parent_child_mismatch`, `child_unit_value_unavailable`, `baseline_unit_value_unavailable`, `comparison_incomplete`.
- P1 데이터 품질 목록(`data_quality`)의 사유 3개: `metric_null`, `below_min_amount`, `below_min_weight`.
- 모두 계약 값이 아니라 M 소유 단위의 출력 이름이다.

⑨ **필수 근거 코드 13개** — 확정(이름과 뜻. 코드별 판정 조건 표는 "영향과 넘길 곳"의 D17)

| 코드 | 뜻 | 요구하는 판정 근거 | 출처 |
|---|---|---|---|
| `parent_child_match_V_and_Q` | 부모 HS6 행과 HS10 하위 행 합계 대조(금액 정확 일치, 중량 허용오차) | 단가 `composition_explained`·`unexplained` | oracle |
| `weight_share_decomposition` | 중량 비중 구성효과 분해 수치(`within_effect`·`mix_effect`·`residual`) | 단가 `composition_explained`·`unexplained` | oracle |
| `per_child_unit_value_stable` | HS10 하위품목별 단가 변화가 기준 안(④) | 단가 `composition_explained` | oracle |
| `comparability_ok` | 비교 조건 점검. 필수 비교 `comparability` | 단가 `composition_explained`·`unexplained`, 점유율 `unexplained` | oracle |
| `partner_comparison_done` | 허용된 비교국과의 비교(검사한 대안 설명과 반대 근거). 필수 비교 `partners` | 단가·점유율 `unexplained` | oracle |
| `missingness_listed` | 부족 항목 목록 | 두 계열 `data_insufficient`·`comparison_incomplete` | oracle |
| `failure_vs_not_collected_distinguished` | 요청 실패와 미수집의 구분 | 두 계열 `data_insufficient`·`comparison_incomplete` | oracle |
| `no_zero_fill` | 빈 응답을 0으로 채우지 않음 | 두 계열 `data_insufficient`·`comparison_incomplete` | oracle |
| `precision_sensitivity_shown`(새 이름) | 정밀도·유효범위·민감도. 작은 금액 자체를 정상 근거로 쓰지 않는다 | 단가 `rounding_unstable` | 개발 플랜 §6.3 6행 |
| `correction_snapshots_before_after`(새 이름) | 교정 전후 스냅샷 | 두 계열 `resolved_after_correction` | 개발 플랜 §6.3 3행 |
| `recalculated_values`(새 이름) | 교정 뒤 동결 정책으로 재계산한 값 | 두 계열 `resolved_after_correction` | 개발 플랜 §6.3 3행 |
| `change_reason`(새 이름) | 변경 사유 | 두 계열 `resolved_after_correction` | 개발 플랜 §6.3 3행 |
| `country_and_world_change_shown`(새 이름) | 해당국 금액 변화와 전체국가(`ALL`) 분모 변화. 필수 비교 `country_and_world` | 점유율 `unexplained` | 구 개발계획 205행 |

- 단가 계열의 구성효과 설명·설명 안 됨·자료 부족 규칙은 oracle A·B·C의 `required_evidence`와 글자·순서까지 같다(P5 시험).
- 개발 플랜 §6.3의 "판단 가능한 범위"·"필요한 다음 자료"(1행), "해당 신호의 모니터링 사유"(2행), "미확인 원인"(4행)은 보고서 설명 문장(`narrative`)의 몫으로 보고 코드로 두지 않았다.

⑩ **사례 식별자 `case_id`** — 확정

- P2가 만드는 사례의 `case_id`는 `{hs6}-{partner}-{month}`(예 `850450-CN-202401`)다. 기대 상태를 담지 않는다. 식별자만으로 사례(품목·상대국·비교월·기준월)를 다시 만들 수 있다(P2 `parse_case_id`, 자문 명세서 Q18의 6).
- 고유 범위는 한 스냅샷(`snapshot_id`)과 한 자료 묶음(`dataset`) 안이다. 합성 스냅샷과 v2가 같은 코드 체계를 쓰면 같은 문자열이 나올 수 있다. 그래서 사례를 가리킬 때는 늘 `snapshot_id`와 `dataset`을 함께 적는다(실행 결과 기록도 둘을 따로 적는다, 자료 계약 §8.1). 한 스냅샷 안에서는 계열·월이 같으면 같은 사례다.
- CLI 사례 인자(단위 F1)는 이 형식과 합성 사례 이름(예 `A-composition`)을 모두 받는다(MT5 첫 PR의 CLI 결정 기록).
- P2가 내는 사례는 자료 계약 §2.3.5의 사례 객체 8필드에 `scope`({`hs6`, `partner`, `month`, `baseline_month`})를 더한 것이다(단위 표 P2 행 "사례(`case_id`·scope)"). 사례 객체를 필드 집합으로 검사하는 쪽은 `scope`를 떼고 본다. 비교국·HS10 범위는 도구가 정한다(자료 계약 §5.1).

⑪ **근거 상태 입력 모양(P3 입력)** — 확정

- `evidence.missingness`: 빠진 자료 목록. 빈 목록도 명시한다. 항목마다 자료 계약 §2.3.2의 관측 필드 `partner_code`, `hs_code`, `month`, `observation_status`가 있다. 단위 K3의 `missingness` 항목 모양이고, 다른 키(`evidence_id`, `request_id`, `flow`)는 읽지 않는다.
- `evidence.unit_value`(단가 신호가 발동했을 때): `comparability_issues`, `comparisons`, `U_baseline`, `decomposition`, `children`, `rounding_unstable`, `resolved_after_correction`.
  - `decomposition`은 null이거나 `within_effect`·`mix_effect`·`residual`·`parent_child_match`를 가진 객체다.
  - `children`은 [{`hs10`, `r_U`}] 목록이다.
- `evidence.share`(점유율 신호가 발동했을 때): `comparability_issues`, `comparisons`, `resolved_after_correction`.
- 수는 정확값이다(②). 발동하지 않은 신호의 블록은 없어도 된다.
- 빠진 관측의 계열 배정
  - 비교월·기준월, 사례 HS6 아래 코드만 본다.
  - `ALL`은 점유율, 대상국 행(HS6·HS10 자릿수 모두)은 단가에 넣는다. 발동 사례의 대상국 HS6 자릿수 상태 행은 HS10 하위 자료가 빠졌다는 뜻이다(자료 계약 §2.3.2 행 규칙 4).
  - 비교국 행과 HS4 자릿수 상태 행은 판정에 쓰지 않는다. `CONFIRMED_NO_TRADE`는 빠진 것이 아니다.
- `comparability_issues`에는 비교 가능성을 깨는 문제만 넣는다.
  - 넣는 것: 두 달의 단위가 다름, 두 달의 HS 코드 정의(코드 체계·개정판)가 다름.
  - 다른 키로 넘기는 것: 빠진 달·분모·하위자료는 `missingness`와 `decomposition`, 부모·하위 대조는 `decomposition.parent_child_match`.
  - 넣지 않는 것: 두 달의 정의가 같은데 정보만 모자란 표시. 예를 들어 개정판을 확인하지 못한 `HSK`가 두 달에 같게 쓰인 경우다(자료 계약 §2.3.1). 정보성 표시가 들어가면 실자료 사례가 모두 `HOLD`가 된다.
  - 점검 자체를 끝내지 못했으면 이 목록이 아니라 `comparisons.comparability`를 `incomplete`로 둔다.

⑫ **도구 쪽 약속(근거 상태를 만드는 쪽)** — 확정

- `ALL` 분모의 빠진 자료는 중복 제거(자료 계약 §2.3.2 행 규칙 5·6) 뒤에도 실제로 비는 경우만 `missingness`에 넣는다. 중복 제거는 HS6 요청의 행을 쓰므로, HS4 요청만 실패하고 HS6 요청 행이 있으면 빠진 것이 아니다.
- `comparability_issues`는 ⑪의 뜻만 담는다. 정보성 표시는 다른 키에 둔다.
- `comparisons`의 `done`·`incomplete`는 ⑦의 뜻을 따른다.
- 근거 상태는 도구 봉투에서 코드가 결정적으로 만들고, 모델 주장으로 채우지 않는다(⑬).

⑬ **판정과 근거 검증의 책임 경계** — 확정

- P3은 받은 근거 상태를 사실로 보고 판정만 한다.
- 근거 상태의 값이 스냅샷 원본과 맞는지는 `verify_evidence`(단위 I5)가 본다. 보고서의 주장이 판정 근거에 맞는 필수 근거(P5 규칙)를 싣는지는 검증기(단위 R3)가 본다.
- `checklist` 모드는 P3 판정을 그대로 쓴다. 다른 모드에서 P3 판정을 어떻게 쓸지(모델 상태와 나란히 적는 참고값 등)는 흐름 조정(단위 I12)과 검증기가 정한다. P3은 모델의 상태를 고쳐 쓰지 않는다(자료 계약 §3.3).

⑭ **P2 사례 만들기의 묶음 제한** — 확정

- 실자료 스냅샷은 `dataset`(`real_dev`나 `real_sealed`)을 반드시 지정한다. 기본값은 없다.
- 분할 기록은 파싱한 배정 목록 `series_assignment`([{`hs6`, `partner`, `dataset`}])로 받는다. 배정에 없는 계열은 오류다. 다른 묶음의 행은 건수도 남기지 않고 버린다. 합성 스냅샷은 묶음과 배정을 받지 않는다.
- 조립(AS1)은 지표 계산(X1·X2)과 신호 발동(P1) 앞에서 지정한 묶음의 계열로 반드시 좁힌다. 개발 중에 v2 64개 계열 전체로 P1이나 `detect`를 돌리지 않는다(병렬 개발 규칙 §7.2). P2의 제한은 마지막 방어선이다.

## 사용자 확인 항목(`policy_v1` 승인 요청에 올린다)

- U1(④): (가) θ 재사용(지금 코드)과 (나) 별도 허용잔차·하위 안정 기준(D가 `real_dev`로 제안) 가운데 고른다.
- U2(③): 적용 신호(단가만인지, 점유율도인지. 점유율이면 대상국 금액과 `ALL` 분모 가운데 어디에 거는지)를 확인한다. 비교월·기준월 모두에 적용하는지, 미달 행을 사례가 아닌 데이터 품질 목록에 두는지도 확인한다.
- U4(⑤): 중량 ±`weight_rounding_kg` 구간이 ±θ나 0을 가로지르면 `HOLD`로 볼지와 계산 위치를 정한다.
- 로드맵 §6.3의 확인 목록에는 U1·U4가 없다. 승인 요청에 항목으로 더한다.

## 검토한 대안

- ⑦ 판정과 근거 검증의 책임 경계만 문서로 두는 안(Codex 교차 검토의 둘째 안): 버렸다. P5 규칙에는 판정 조건이 없고 검증기도 필수 근거를 보지 않아 빈틈이 닫히지 않는다. 또 `checklist`에서 검증기가 막으면 `INVALID`(실행 실패)가 되어 "유지/보류" 선택과 어긋난다. 그래서 근거 상태에 완료를 명시하는 안(평가 방법론 검토의 1안)을 골랐다.
- ⑦ 키가 없으면 `HOLD`로 두는 안: 버렸다. 배선 누락이 자료 보류로 보인다(⑦의 이유).
- ⑩ `case_id`에 스냅샷 접두를 붙이는 안: 버렸다. 고유성은 늘지만 CLI 인자와 정답표를 잇는 문자열이 길어진다. 고유 범위를 기록하는 쪽을 골랐다.
- ① P1이 정책 객체의 모르는 키를 거부하는 안: 버렸다. 정책 파일에는 판정 정책이 읽지 않는 키(허용오차, 승격 규칙)가 있고, 모르는 키 검사는 K4가 한다.
- ③ `min_*`를 점유율에도 거는 안: U2로 사용자에게 올린다.

## 영향과 넘길 곳

- DT1(K3·K4): ①의 정책 객체 모양과 ⑪의 `missingness` 항목 모양이 K3·K4와 같다.
- DT2(X1·X2·X3): 조립이 ②의 정확값(`exact_value`)을 판정 정책에 넘긴다. 분해의 부모 대조(`parent_check`의 금액·중량 일치)가 ⑪의 `parent_child_match`가 된다.
- AS1(탐지 조립)
  - X1·X2의 `exact_value`를 P1에 넘기고, 경계값(정확히 30%) 조립 시험을 둔다.
  - ⑭의 계열 좁히기를 조립 시험으로 고정한다.
  - `source_kind`는 호출자가 준 값이 아니라 스냅샷 기록에서 읽는다(자료 계약 §2.3.1). 실자료 `snapshot_id`에 `controlled`를 주면 P2 제한을 우회하기 때문이다(평가 방법론 검토 지적 8).
  - `detect` CLI 경로의 묶음은 `real_dev`로 고정한다. DT4 ①의 분할 기록을 `series_assignment`로 바꾼다.
- AS2(사례 조사 조립): 도구 봉투 → 근거 상태(⑪) 변환을 맡는다. 흐름 조정(I12)의 `checklist` 배선이 P3에 `policy`·`case`·`evidence`를, P4에 `signals`·`signal_status`를 넘기도록 맞춘다.
- MT2(도구): ⑫의 약속을 지킨다. `check_comparability`·`compare_partners`는 결과에 완료 여부를 남겨 `comparisons`의 `done`·`incomplete`로 옮길 수 있게 한다.
- MT4(I9·I12)
  - 다른 모드에서 P3 판정을 쓰는 방식을 정한다(⑬).
  - `MONITOR`·`MAINTAIN` 조건 문장(④·⑥·⑦)을 모든 모드가 받는 공개 규칙(프롬프트 I9가 읽는 정책 설명이나 P5 출력)에 싣는다. 비교군 공정성 때문이다(평가 방법론 검토 지적 9).
- MT3(R3)·AS4
  - P5 `claim_families`는 `@` 뒤 코드를 검사하지 않는다. MT3 검증기에도 같은 규칙이 따로 있다. AS4(조립 점검)에서 하나로 합치며, `@` 뒤를 "10자리 숫자이고 사례 HS6로 시작"으로 좁힌다.
  - P5의 계약 상수 사본은 AS4에서 K1 import로 바꾼다(`docs/plan/UNITS.md` §6 조립 부산물 4).
- D17(DT8·MT3·MT7의 F1 전 보완 PR)
  - 필수 근거 코드마다 판정 조건 표를 공개 정본(룰북 부록이나 시나리오 명세)에 둔다. 판정 조건은 "보고서에 어떤 typed claim(정해진 필드를 가진 사실 주장)·근거 ID가 있으면 충족인가"다. 표는 R3와 채점기가 각자 구현한다.
  - `HOLD`를 사유별(빠진 관측 / 비교 조건·부모 대조 불일치)로 나눌지도 여기서 정한다. 나누면 불일치 `HOLD`에는 `parent_child_match_V_and_Q`와 `comparability_ok`가 맞는다.
  - 기한은 dev20 정답표 전, 늦어도 F1(`RB-1` 동결) 전이다.
- DT5(시나리오 명세·dev20)·DT8(채점기)
  - ⑨의 어휘를 같게 쓴다.
  - U1이 정해지기 전에는 시나리오 1 사례를 하위 단가 변화 0으로, 시나리오 2 사례를 남은 within 변화 ≥ θ로 만든다. 그러면 (가)·(나)가 같은 답을 낸다.
  - 탐지 경계 ±0.05 안의 값을 피한다.
  - 시나리오 6은 U4에 달렸다. 시나리오 9는 `resolved_after_correction`에 대응시키지 않는다(⑥).
- Q18(사례 지정 인자 형식): 채점기는 실행 기록과 정답표를 `case_id`로 잇는다. dev20·holdout40 정답표의 `case_id`와 실행 기록의 `case_id`가 같도록 정한다. 합성 사례는 정답표 이름을 그대로 쓰거나, DT5가 ⑩ 형식을 채택한다. 기한은 MVP 5번(로드맵 §3) 전이다.
