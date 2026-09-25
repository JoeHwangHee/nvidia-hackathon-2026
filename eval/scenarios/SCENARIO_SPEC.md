# TradeSentry 합성 시나리오 명세(공개)

| 항목 | 내용 |
|---|---|
| 문서 | `eval/scenarios/SCENARIO_SPEC.md`(단위 V1, 구성 단위) |
| 작성 | 2026-09-25(금), 로드맵 DT5(데이터 트랙) |
| 역할 | 합성 평가 자료 `dev20`(공개 개발 자료 20건)와 `holdout40`(봉인 평가 자료 40건)의 **분류 수준** 생성 규칙과 파일 형식. holdout40 생성 에이전트(로드맵 DT6)가 받는 입력이다 |
| 적지 않는 것 | 사례별 기대 상태와 생성 계열(사례마다 어떤 기본 계열·사건으로 만들었는지). 구 개발계획(`Pasted markdown.md`) §5.2가 숨길 대상으로 정한 것이다 `[사실: 병렬 개발 규칙 docs/rules/PARALLEL_DEV_RULES.md §6.8]` |
| 값의 정본 | 상태값·필드·ID·경로는 자료 계약 `docs/rules/DATA_CONTRACT_V1.md`, 분류와 배분은 룰북 `docs/eval/RULEBOOK.md` B1(구 개발계획 §8.1 유지). 이 문서는 그 값을 글자 그대로 옮겨 쓴다 |
| 검사 명령 | `uv run --locked python -m eval.datagen.holdout40_check --cases <사례 목록> --answers <정답표>`(단위 V4, §8) |
| 사용자 결정 반영 | 2026-09-25(금) 08:41 사용자 결정을 본문에 반영했다(D17 PR): U1·U2·U4 승인(`docs/tracking/decisions/20260925-0846-user-decision-policy-v1-approval.md`)은 §2.1과 분류 1·2·6, 새 필수 근거 이름 승인(결정 9)과 보류 사유별 필수 근거(결정 14, `docs/tracking/decisions/20260925-0847-user-decision-morning-shared-promises.md`)는 §5.1~§5.3과 분류 5·7 |

TradeSentry는 관세청 수입통계에서 kg당 단가와 상대국 점유율이 전년 같은 달보다 크게 바뀐 경우를 경보로 잡고, 조사자와 검수자(Critic)가 제한된 조회 도구로 반증을 시도해 담당자의 다음 업무를 검토 유지(`MAINTAIN`)·모니터링(`MONITOR`)·자료 보류(`HOLD`) 가운데 하나로 제안하는 에이전트 시스템이다. 부정·위법 판정이 아니다. 이 문서의 합성 자료는 정답을 알고 규칙대로 만든 가짜 자료이고 실제 거래가 아니다.

**근거 태그.** `[사실]` 저장소 파일에서 직접 확인, `[추론]` 근거 있는 판단, `[DESIGN]` 팀 설계 규칙(대회 공식 규칙이 아니다), `[미확인]` 검증하지 않음. 따로 적지 않은 규칙은 `[DESIGN]`이다. 오케스트레이터는 작업을 나누고 병합하는 주관 에이전트다.

## 1. 한눈에 보기

1. 합성 사례는 10개 분류로 나눈다. dev20은 20건, holdout40은 40건을 아래 배분대로 만든다(§3).
2. 사례 하나는 HS6(6자리 품목 코드) × 상대국 × 비교월(전년 같은 달이 기준월)이다. 사례는 코드가 탐지하는 경보와 같다. 합성 스냅샷에서 탐지 기준을 넘는 (HS6, 상대국, 달)은 사례 목록과 정확히 같아야 한다(§2.4).
3. 사례마다 신호 두 개(단가 `unit_value`, 점유율 `share`)의 발동 여부와 **판정 근거 규칙**을 생성 전에 손으로 정한다. 규칙이 신호별 상태와 필수 근거를 정하고, 사례 상태는 집계 규칙으로 나온다(§5).
4. 자료는 수집기 형식 원천(수집 계획 manifest, 응답 XML, 요청 결과 기록, 합성 비교국 표)으로 만들고 단위 S2로 빌드해 단위 S3 검증을 통과시킨다(§7).
5. 입력(사례 목록과 원천)과 정답표는 서로 다른 하위 경로에 둔다. 채점 대상 실행 샌드박스는 입력만 읽는다(§7.1).
6. 사례마다 부모 원본 계열 ID(사건을 얹기 전 기본 계열의 지문)를 붙이고, holdout40은 dev20 목록과 겹치지 않아야 한다(§6).
7. 결정적 검사 명령(단위 V4)이 스키마, 분류별 건수, dev20과 겹침 0을 본다(§8).

## 2. 공통 규칙

### 2.1 자료 묶음과 정책 버전

| 묶음 | 건수 | 위치 | 정책 버전 | 숫자 등급 |
|---|---|---|---|---|
| `dev20` | 20 | `eval/dev/dev20/`(입력 `input/`, 정답 `answers/`) | `dev-0.1`(개발용 정책 `configs/policy_dev.json`: 단가 변화율 절댓값 30% 이상, 점유율 변화 절댓값 10pp 이상) | D(개선 과정에 노출됨) |
| `holdout40` | 40 | 봉인 폴더(환경변수 `TRADESENTRY_SEALED_DIR`, 기본값 `~/.tradesentry/sealed/`, 저장소 밖) | `policy_v1`(2026-09-25(금) 사용자 승인. 생성 규칙에 `policy_version`을 적는다) | C(보조 지표) |

- 두 묶음 모두 `source_kind`=`controlled`(합성)이다 `[사실: 자료 계약 §4.1]`.
- 발동 여부와 기대 상태는 그 묶음의 정책 버전 기준값으로 정한다. 기준값이 바뀌면(예: `policy_v1` 승인, `min_amount`·`min_weight` 도입) 발동 여부와 기대 상태가 달라질 수 있으므로 dev20은 다시 검증하고, holdout40은 다시 만든다 `[사실: 병렬 개발 규칙 §4.2 3, §6.7]`.
- `policy_v1`(2026-09-25(금) 승인, 결정 기록 `docs/tracking/decisions/20260925-0846-user-decision-policy-v1-approval.md`)과도 같은 결과가 나오게 만든다. `policy_v1`은 단가 신호에 최소 기준 `min_amount` 100 USD·`min_weight` 10 kg을 두 달 모두의 부모 HS6 행에 걸고, 미달이면 사례가 아니라 데이터 품질 목록으로 보낸다(U2). 그래서 단가 신호를 발동시키는 사례는 두 달 모두 부모 행 금액 100 USD 이상·중량 10 kg 이상으로 만든다. 반올림 불안정 규칙(U4, 승인, §4 분류 6)도 모든 단가 발동 사례에 적용해, `rounding_unstable` 사례만 불안정이고 나머지는 안정이게 만든다. 생성 도구의 자체 검산이 둘을 본다.

### 2.2 합성 세계

- 품목과 상대국: HS4(4자리 품목 묶음 코드) 하나 아래 HS6 코드들과 상대국 여러 개(관세청 2자리 국가코드 `KCS_cntyCd` 형식), 그리고 전체국가 분모 `ALL`. HS4·HS6는 실자료와 같은 품목분류 번호를 쓴다. HS10은 10자리 모양의 합성 세번(예: `{HS6}1000`)이라 실제 HSK 10단위 번호와 다를 수 있고, 품목명 칸은 "합성 하위품목"으로 표시한다. 상대국은 어느 나라에도 배정되지 않은 합성 코드(ISO 3166-1(국가 코드 국제 표준)의 사용자 지정 범위 `XA`~`XZ` 가운데, 널리 코소보로 쓰이는 `XK`를 뺀 것)만 쓴다. 실제 나라 코드에 합성 수치가 붙으면 커밋되는 보고서 사본에서 실제 무역에 대한 주장으로 읽힐 수 있기 때문이다. 합성 코드는 관세청 국가코드 목록(`data/reference/kcs_country_codes.json`)과 국가 코드 대응표(`data/reference/country_map.csv`)에 없어야 한다. dev20은 `XL`~`XQ` 여섯 개, 합성 시험자료(DT3)는 `XA`~`XJ`를 쓴다. 사례는 늘 `snapshot_id`와 `dataset`을 함께 적어 가리킨다(판정 정책 결정 기록 `docs/tracking/decisions/20260925-0025-model-decision-mt1-policy.md` ⑩).
- 기간: 실자료 스냅샷과 같게 36개월(2022-01~2024-12)을 쓴다. 비교월은 기준월(12개월 전)이 기간 안에 있는 달이다.
- 하위품목: HS6마다 HS10(10자리 세부 코드) 하위품목이 있다. 상대국 월 값은 HS10 하위 값의 합과 같은 부모 HS6 행이다(분류 5의 불일치 사례만 예외).
- 나머지 세계: 수집하지 않은 나라들의 HS10 값. 전체국가(`ALL`) 분모에만 들어간다. 그래서 분모는 수집한 상대국 금액의 합보다 크다(분류 7만 예외).
- 비교 대상: 자료 안의 합성 비교국 표(`peer_group`)로 정한다. 실자료의 `g0`/`g1` 결과 파일과 무관하다 `[사실: 자료 계약 §2.3.6]`. 합성 자료 안에서 `g0` 규칙(대상국을 뺀 상대국 가운데 기준연도 2023년 부모 HS6 수입금액 상위 k개국, 같으면 국가 코드순)으로 고르고 `grouping_version`=`g0`, `method`=`import_value_topk`, `source_version`=합성 `snapshot_id`, `params_hash`=단위 G1과 같은 규칙(k·기준연도·후보국 목록의 정규 JSON sha256, 자료 계약 §2.3.6)으로 적고 빈 값은 `null`로 쓴다(비교 대상은 MVP 시험까지 `g0`다 `[사실: 자료 계약 §1.3]`). `g1` 동결 뒤 합성 묶음을 `g1`로 돌릴 때의 처리는 정하지 않았다 `[미확인]`.
- 흔들림: 사건이 없는 달의 값은 작은 결정적 흔들림(예: 중량 ±2%, 단가 ±1%)만 둔다. 그래서 사례가 아닌 (계열, 달)은 탐지 기준을 넘지 않는다.

### 2.3 사례와 식별자

- 사례 식별자 `case_id`는 판정 정책 단위 P2의 형식 `{hs6}-{partner}-{month}`(예: `999901-XA-202401`. dev20에 없는 형식 예시)를 쓴다. CLI가 받는 형식(영문·숫자로 시작하고 끝나며 영문·숫자·밑줄·하이픈, 64자 이하)이고, 묶음 안에서 고유하다. 기대 상태·분류를 식별자에 넣지 않는다.
- 사례 목록은 식별자 순으로 적는다(순서가 분류를 드러내지 않게).
- 파일 이름에도 기대 상태·분류를 넣지 않는다(봉인 해시 목록이 커밋되어 누구나 본다) `[사실: 자료 계약 §12.2]`.

### 2.4 탐지 경계와 사례 밖 경보

- 탐지 공식과 원천 규칙은 자료 계약 §2.3.2 행 규칙과 §11.2를 따른다. 단가는 부모 HS6 행의 금액÷중량, 점유율 분모는 `ALL` HS10 월 행의 합(같은 (HS10, 달)이 두 요청에 있으면 한 번만)이다.
- 발동은 정확값(표시 자릿수로 반올림하기 전)으로 기준 **이상**이다(판정 정책 결정 기록 ②). 생성 자료의 모든 단가 변화율(%)과 점유율 변화(pp)는 기준에서 0.05 이상 떨어져야 한다(같은 기록 "영향과 넘길 곳": 탐지 경계 ±0.05 안의 값을 피한다).
- 합성 스냅샷 전체에서 기준을 넘는 (HS6, 상대국, 달)의 집합은 사례 목록과 정확히 같다. 사례 밖 경보를 만들지 않는다. 사건이 한 달 e에 닿으면 e와 e+12 두 비교에 영향을 주고, `ALL` 분모를 바꾸면 그 HS6의 모든 나라 점유율이 바뀐다는 점을 고려한다.
- 한 사례의 사건이 다른 사례의 비교월·기준월 값(비교국 값 포함)을 건드리지 않게 한다(같은 HS6 안에서는 사례마다 다른 달을 쓰면 쉽다).

### 2.5 신호 두 개

- 사례는 두 신호 각각의 발동 여부(`TRIGGERED`/`NOT_TRIGGERED`)를 가진다. 단일 신호 사례의 다른 신호는 `NOT_TRIGGERED`로 둔다 `[사실: 룰북 B1]`.
- 발동하지 않은 신호의 판정 근거 규칙은 `null`이고 신호별 상태는 `NOT_TRIGGERED`다.

## 3. 분류와 배분

구 개발계획 §8.1과 룰북 B1의 표를 그대로 쓴다 `[사실: 룰북 B1]`.

| # | 통제 조건 | dev20 | holdout40 | 사전 기대 처리·검사 |
|---|---|---:|---:|---|
| 1 | 하위 단가 고정, 구성비만 변화 | 3 | 6 | `MONITOR`. 합계 일치·중량 비중·상쇄 검사 |
| 2 | 구성효과를 뺀 뒤 남는 변화 | 3 | 6 | `MAINTAIN`. 하위·비교국·잔차 증거 |
| 3 | 비교국 동반 변화, 구성 설명 미성립 | 2 | 4 | `MAINTAIN`. 단순 동반 하락으로 성급히 낮추지 않음 |
| 4 | 월 누락·API 실패·미수집 | 2 | 4 | `HOLD`. 빈 행을 0으로 바꾸지 않음 |
| 5 | 단위·HS 버전·하위 합계 불일치 | 2 | 4 | `HOLD`. 불일치 식별, 임의 허용오차 금지 |
| 6 | 작은 기준월 값·반올림 불확실·중량 0 | 2 | 4 | `HOLD`. 계산 불가와 작은 거래의 구분 |
| 7 | 분모 완전성 부족·국가 집합 변경 | 2 | 4 | `HOLD`. 전체 점유율 표기 금지 |
| 8 | 정상 점유율 계산에서 남는 급변 | 2 | 4 | `MAINTAIN`. 분모 산술 설명만으로 낮추지 않음 |
| 9 | 복구할 수 있는 잘못된 조회 범위 | 1 | 2 | 수정 조회 뒤 원래 근거에 따른 상태. 재조사 1회 |
| 10 | 두 신호의 판정이 다름 | 1 | 2 | 신호별 판정과 사례 집계 우선순위 검증 |
| | 합계 | 20 | 40 | |

- 같은 기본 계열의 규모·seed만 바꾼 변형을 dev20과 holdout40 양쪽에 두지 않는다. 기초 시계열·하위품목 구조·결측 방식·부모 원본 계열 ID 단위로 나눈다 `[사실: 룰북 B1, 병렬 개발 규칙 §6.8]`.
- 60건을 서로 구별되게 만들지 못하면 그 사실과 실제로 만든 건수를 적는다. 평가 뒤 어려운 사례를 지우지 않는다 `[사실: 룰북 B1]`.

## 4. 분류별 규칙

분류마다 **자료 구성**(생성 자료가 만족해야 하는 조건)과 **기대 처리**(허용하는 판정 근거 규칙, §5)를 적는다. 사례마다 어떤 변형을 골랐는지는 적지 않는다. 판정 근거 규칙의 뜻과 상태·필수 근거는 §5 표다.

### 분류 1 — 하위 단가 고정, 구성비만 변화

- 자료 구성: 단가 신호만 발동. 기준월과 비교월의 대상국 HS10 하위품목 집합이 같고, 모든 하위품목의 단가(금액÷중량)가 **정확히 같다**(하위 단가 변화 0). 중량 비중만 바뀌어 부모 단가가 기준 이상 변한다. 부모 금액 = 하위 금액 합(정확히), 부모 중량 = 하위 중량 합(허용오차 0.5 kg×(행수+1) 안). 그래서 `within_effect`(하위 단가 변화 효과) = 0, `residual`(분해 잔차) = 0이다.
- 이유: 승인된 U1은 "개별 하위변동·잔차가 기준 안"의 기준을 단가 탐지 임계값 θ로 정했다(판정 정책 결정 기록 ④, `policy_v1` 승인 기록). 하위 변화 0·잔차 0이면 이 기준을 넉넉히 만족한다. 승인 전에 검토한 두 해석도 같은 답(`MONITOR`)을 내게 만들었다.
- 기대 처리: 단가 `composition_explained` → `MONITOR`.

### 분류 2 — 구성효과를 뺀 뒤 남는 변화

- 자료 구성: 단가 신호만 발동. 하위 자료가 완전하고(같은 HS10 집합, 부모 대조 일치, 모든 중량 > 0) 구성효과를 뺀 변화 |`within_effect` + `residual`|이 기준월 단가 U0의 θ 이상(θ는 단가 탐지 기준, `dev-0.1`에서 30%)이다. 비교국의 비교월·기준월 부모 값이 모두 관측돼 비교국 비교를 마칠 수 있다.
- 이유: 승인된 U1(기준 θ)에서 `MAINTAIN`이다. 승인 전에 검토한 두 해석도 같은 답을 내게 만들었다(판정 정책 결정 기록 "영향과 넘길 곳").
- 기대 처리: 단가 `unexplained` → `MAINTAIN`.

### 분류 3 — 비교국 동반 변화, 구성 설명 미성립

- 자료 구성: 분류 2의 조건에 더해, 같은 달 비교국(합성 비교국 표의 나라들)의 단가가 대상국과 **같은 방향**으로 기준의 절반 이상 변한다. 비교국 변화는 탐지 기준 아래로 둔다(사례 밖 경보 금지, §2.4).
- 뜻: 다른 상대국도 비슷하게 변했다는 사실만으로는 등급을 낮추지 않는다 `[사실: 개발 플랜 docs/plan/DEV_PLAN.md §6.3]`.
- 기대 처리: 단가 `unexplained` → `MAINTAIN`.

### 분류 4 — 월 누락·API 실패·미수집

- 자료 구성: 대상국의 부모 HS6 행은 비교월·기준월 모두 있어 신호는 발동한다. 판정에 필요한 대상국 HS10 하위 자료를 맡은 요청(HS6 조회)이 실패(`REQUEST_FAILED`: 수신 기록 `FAILED`)했거나 수집되지 않았다(`NOT_COLLECTED`: 수신 기록 없음). 비교월 연도나 기준월 연도 구간 어느 쪽이든 된다.
- 만들지 않는 변형: 요청은 성공했는데 그 달 행만 없는 변형(`UNRESOLVED_ZERO`만 있는 경우)과 비교국 자료만 빠진 변형. 두 변형의 필수 근거도 §5.3 판정 조건표로 판정할 수는 있다(인용할 행이 없는 키는 값으로 구분하고, 비교국 누락은 `missingness_listed`의 대체 조건으로 채운다) `[사실: eval/scorer/results.py _tag_ok, tests/test_scorer_results.py]`. 다만 두 변형 모두 dev20에 확인 사례가 없고 이 판은 생성 규칙을 바꾸지 않으므로 만들지 않는다. holdout40에서 열지는 holdout40 생성(로드맵 DT6) 전에 오케스트레이터가 정한다.
- 기대 처리: 발동한 모든 신호가 `hold_missing` → `HOLD`.

### 분류 5 — 단위·HS 버전·하위 합계 불일치

- 자료 구성(단가 신호만 발동, 관측은 모두 `OBSERVED`): 다음 가운데 하나.
  - 부모 HS6 행과 HS10 하위 합이 맞지 않다: 금액이 정확히 같지 않거나, 중량 차이가 허용오차 0.5 kg×(행수+1)을 넘는다.
  - 기준월과 비교월의 HS10 코드 집합이 다르다. 분해식은 같은 HS10 집합에서만 쓰므로 분해가 성립하지 않는다 `[사실: 자료 계약 §11.2]`. 신설·소멸 코드의 단가를 0으로 채워 분해하지 않는다 `[사실: 개발 플랜 §6.1]`. HSK 10단위 개정 흔적으로 만들려면 실제 개정처럼 구 코드 소멸·신 코드 신설이 그해 1월부터 이어지게 한다(한 달짜리 교체는 개정이 아니라 "그 달 그 세번 거래 없음 + 다른 세번 거래"로 읽힌다).
- 만들 수 없는 변형: 단위나 HS 버전 표기가 다른 변형. 수집기 형식은 스냅샷 전체의 단위(`USD`·`kg`)와 관측 행의 `hs_version`(`HSK`)을 하나로 고정한다 `[사실: 단위 S2 build.py, 수집기 store_result]`.
- 기대 처리: 단가 `hold_inconsistent` → `HOLD`(불일치 보류, §5.2).

### 분류 6 — 작은 기준월 값·반올림 불확실·중량 0

- 자료 구성(단가 신호만 발동): 다음 가운데 하나.
  - 반올림 불안정: 두 달 부모 HS6 행이 최소 기준(100 USD·10 kg, §2.1) 이상이면서 중량이 작아 반올림에 민감하다. 규칙(U4, 2026-09-25(금) 승인): 발동한 단가 신호에만, 금액은 그대로 두고 두 달 부모 중량을 Q ± 0.5 kg로 움직일 때의 단가 변화율 r_U 구간이 r_U ≥ 0이면 하한 < θ, r_U < 0이면 상한 > −θ일 때 불안정이다(구간 끝이 기준과 같으면 안정). 구간 끝도 기준에서 0.05 이상 떨어지게 한다. 사건 달의 앞뒤 비교(e, e+12)가 사례 밖 경보를 만들지 않게 기준월을 기간 첫해에 둘 수 있다.
  - 중량 0: 하위품목 하나가 금액 > 0, 중량 0이라 그 품목 단가를 계산할 수 없어 분해가 성립하지 않는다(부모 대조는 맞다).
- 기대 처리: 반올림 불안정은 단가 `rounding_unstable` → `HOLD`, 중량 0은 단가 `hold_inconsistent` → `HOLD`.
- 승인 뒤: 반올림 불안정 규칙(U4)과 최소 기준(U2)은 이 분류가 전제한 제안대로 승인됐다(`policy_v1` 승인 기록 결정 1). dev20의 `policy_v1` 재검증은 DT5 결정 기록 ⑪대로 한다. 뒤에 기준값이 바뀌면(새 정책 버전) 이 분류의 사례를 다시 검증하고 필요하면 다시 만든다.

### 분류 7 — 분모 완전성 부족·국가 집합 변경

- 자료 구성(점유율 신호만 발동): 비교월이나 기준월의 전체국가(`ALL`) 분모가 **대상국 금액보다 작다**(점유율 100% 초과). 공식 분모가 전체 국가를 담지 못해(국가 범위가 줄어) 전체 점유율을 확인할 수 없다. 대상국 단가는 기준 아래로 둔다. 분모를 줄이면 그 HS6의 다른 나라 점유율도 바뀌므로, 대상국이 그 HS6의 대부분을 차지하게 만들어 다른 나라 점유율 변화가 기준 아래에 머물게 한다.
- 주의: 실제 관세청 API에서 전체국가(`itemtrade`) 값은 같은 통관 자료의 합이라 한 나라 값보다 작게 나오지 않는다. 이 변형은 분모가 전체 국가를 담지 못한(부분집합이 된) 경우를 흉내 낸 **주입된 불일치**다. 보고서나 발표에서 관세청 자료의 실제 현상으로 쓰지 않는다.
- 근거: 점유율 분모는 공식 전체국가 합계다. 선택국 합계를 전체 분모로 쓰지 않는다 `[사실: 자료 계약 §11.1]`. 공식 분모가 없으면 전체 점유율 경보의 결론은 보류한다 `[사실: 구 개발계획 §4 4]`. 필요한 분모가 없어 검증할 수 없으면 `HOLD` `[사실: 개발 플랜 §6.3 1행]`.
- 기대 처리: 점유율 `hold_inconsistent` → `HOLD`(분모 불완전 보류, §5.2). 분모 관측이 빠진 변형(`hold_missing`)도 규칙상 허용하지만, 분모가 없으면 점유율이 계산되지 않아 신호가 발동하지 않는다는 점에 주의한다.

### 분류 8 — 정상 점유율 계산에서 남는 급변

- 자료 구성(점유율 신호만 발동): 기준월·비교월 분모가 완전하고(분모 ≥ 수집한 상대국 금액의 합), 비교국 자료가 관측된다. 대상국 단가는 기준 아래다. 변형: 대상국 금액은 그대로인데 다른 나라 물량이 줄어 분모가 작아진 경우(분모 축소의 "산술 설명"), 대상국 물량이 크게 줄어든 경우 등.
- 뜻: 분모 축소로 점유율이 오른 것은 산술 설명일 뿐 하향 사유가 아니다 `[사실: 개발 플랜 §6.3]`.
- 기대 처리: 점유율 `unexplained` → `MAINTAIN`.

### 분류 9 — 복구할 수 있는 잘못된 조회 범위

- 자료 구성: 필수 근거를 모두 얻을 수 있는 완전한 자료다. 다만 조사 범위를 사례 범위(사례 HS6·대상국·비교월과 기준월, 허용된 비교국) 밖으로 잡기 쉬운 요소를 둔다. 예: 대상 HS6가 그 나라 HS4 수입의 작은 부분이라 HS4 합계로 보면 단가 변화가 기준의 절반에도 못 미친다. 올바른 범위로 다시 조회하면(재조사 1회, 그 안의 조회 2회 이하) 필요한 근거가 모두 나온다.
- 기대 처리: 사례 범위의 근거로 정한 상태(규칙 제약 없음). `resolved_after_correction`(교정 전후 스냅샷)에는 대응시키지 않는다(판정 정책 결정 기록 ⑥).

### 분류 10 — 두 신호의 판정이 다름

- 자료 구성: 두 신호가 모두 발동하고 신호별 상태가 다르다. 예: 단가는 HS10 조회 실패로 `HOLD`, 점유율은 분모가 완전하고 설명되지 않아 `MAINTAIN`.
- 기대 처리: 두 신호 규칙의 상태가 다르다. 사례 상태는 집계 규칙(`MAINTAIN > HOLD > MONITOR`)으로 나오고, `MAINTAIN`과 `HOLD`가 섞이면 `unresolved_evidence`=true다 `[사실: 자료 계약 §3.1]`.

## 5. 판정 근거 규칙

### 5.1 규칙표

신호 계열마다 판정 근거 규칙 키를 하나 고른다. 키가 신호별 상태와 필수 근거(보고서가 그 상태를 내려면 남겨야 하는 근거)를 정한다. 필수 근거 이름은 판정 정책 단위 P5의 어휘 13개만 쓴다(판정 정책 결정 기록 ⑨) `[사실: src/tradesentry/policy/required_evidence.py]`.

| 계열 | 규칙 키 | 신호별 상태 | 필수 근거(순서대로) | 단위 P5 판정 근거 |
|---|---|---|---|---|
| 단가 | `composition_explained` | `MONITOR` | `parent_child_match_V_and_Q`, `weight_share_decomposition`, `per_child_unit_value_stable`, `comparability_ok` | `composition_explained` |
| 단가 | `unexplained` | `MAINTAIN` | `parent_child_match_V_and_Q`, `weight_share_decomposition`, `partner_comparison_done`, `comparability_ok` | `unexplained` |
| 단가 | `hold_missing` | `HOLD` | `missingness_listed`, `failure_vs_not_collected_distinguished`, `no_zero_fill` | `data_insufficient`(빠진 관측)·`comparison_incomplete` |
| 단가 | `hold_inconsistent` | `HOLD` | `parent_child_match_V_and_Q`, `comparability_ok`, `no_zero_fill` | `data_inconsistent`(관측은 모두 있는데 비교 조건·부모·하위 대조·구성 분해가 성립하지 않음, PR #42) |
| 단가 | `rounding_unstable` | `HOLD` | `precision_sensitivity_shown` | `rounding_unstable` |
| 점유율 | `unexplained` | `MAINTAIN` | `country_and_world_change_shown`, `partner_comparison_done`, `comparability_ok` | `unexplained` |
| 점유율 | `hold_missing` | `HOLD` | `missingness_listed`, `failure_vs_not_collected_distinguished`, `no_zero_fill` | `data_insufficient`·`comparison_incomplete` |
| 점유율 | `hold_inconsistent` | `HOLD` | `country_and_world_change_shown`, `comparability_ok`, `no_zero_fill` | `data_inconsistent`(점유율 비교 가능성 문제: 분모가 대상국 금액보다 작음 등, PR #42) |

- 필수 근거의 모양: 발동한 신호가 하나면 그 규칙의 근거 목록이다. 두 신호가 모두 발동하면 신호별 목록 객체 `{"unit_value": [...], "share": [...]}`다(두 신호에 함께 쓰이는 코드, 예: `comparability_ok`가 어느 신호의 근거인지 드러나게. 독립 채점기의 정답표 형식과 같다 `[사실: eval/scorer/results.py _required_evidence]`).
- "단위 P5 판정 근거" 열은 참고다. 채점기는 정답표의 필수 근거 목록만 읽고 판정 근거 이름을 읽지 않는다 `[사실: eval/scorer/results.py read_answer_table]`. 불일치 보류의 판정 근거 이름은 판정 정책 P3·P5를 고치는 짝 PR(모델 트랙 `model/MT1-d17-hold-split`)이 정하고, 병합 뒤 이 열을 그 이름으로 맞춘다.
- 사례 상태 `review_status`는 신호별 상태의 집계다: 우선순위 `MAINTAIN > HOLD > MONITOR`, 발동한 신호가 모두 `MONITOR`일 때만 `MONITOR`, `MAINTAIN`과 `HOLD`가 섞이면 `MAINTAIN`에 `unresolved_evidence`=true, 그 밖에는 false `[사실: 자료 계약 §3.1]`.
- `resolved_after_correction`(교정 전후 스냅샷, `MONITOR`)은 스냅샷 하나로 도는 합성 묶음에서 쓰지 않는다.

### 5.2 불일치 보류 `hold_inconsistent`

- 뜻: 필요한 관측은 모두 `OBSERVED`인데 부모·하위 대조, 구성 분해(같은 HS10 집합이 아니거나 하위 중량 0), 전체국가 분모가 성립하지 않아 검증할 수 없는 자료 보류. 분류 5, 분류 6의 중량 0 변형, 분류 7이 쓴다.
- 확정: 사용자 결정 14(`docs/tracking/decisions/20260925-0847-user-decision-morning-shared-promises.md`)가 자료 보류(`HOLD`)를 사유별로 나눴다. 빠진 관측이 있는 보류는 `hold_missing`의 근거(`missingness_listed`, `failure_vs_not_collected_distinguished`, `no_zero_fill`) 그대로이고, 불일치 보류는 단가 `parent_child_match_V_and_Q`·`comparability_ok`·`no_zero_fill`, 점유율 `country_and_world_change_shown`·`comparability_ok`·`no_zero_fill`이다. holdout40도 이 규칙으로 만든다.
- 나눈 이유: 나누기 전 판정 정책 P5 규칙표는 이런 보류에도 빠진 관측용 근거를 요구했는데, 빠진 관측이 없으면 그 근거는 비교국 누락이나 계산 불가 값의 null 표기 같은 대체 조건으로만 채워져 보류 사유를 보이지 못한다. 불일치 보류에는 대조한 양쪽 행(`parent_child_match_V_and_Q`), 계열 지표의 비교 점검(`comparability_ok`), 계산할 수 없는 값을 0이나 수로 채우지 않음(`no_zero_fill`: 신설·소멸 코드와 중량 0 하위품목의 단가, 성립하지 않는 분해 값)이 맞다. 점유율 분모 불완전에는 해당국 금액과 `ALL` 분모의 두 시점 값(`country_and_world_change_shown`)을 대조 근거로 쓴다.
- 판정 조건과 채울 수 있는지의 확인은 §5.3이다.

### 5.3 필수 근거의 뜻과 판정 조건표

필수 근거 이름 13개는 판정 정책 단위 P5의 어휘이고, 새 이름 다섯(`precision_sensitivity_shown`, `correction_snapshots_before_after`, `recalculated_values`, `change_reason`, `country_and_world_change_shown`)은 평가 구성(공용 약속)으로 승인됐다(사용자 결정 9, `docs/tracking/decisions/20260925-0847-user-decision-morning-shared-promises.md`). 뜻은 단위 P5의 설명을 옮겼다.

| 이름 | 뜻 |
|---|---|
| `parent_child_match_V_and_Q` | 부모 HS6 행과 HS10 하위 행 합계 대조(금액 정확 일치, 중량 허용오차) |
| `weight_share_decomposition` | 중량 비중 구성효과 분해 수치(`within_effect`·`mix_effect`·`residual`) |
| `per_child_unit_value_stable` | HS10 하위품목별 단가 변화가 기준 안(하위 안정성) |
| `comparability_ok` | 비교 조건 점검(기간·요청 완료·단위·HS 버전·분모·하위자료) |
| `partner_comparison_done` | 허용된 비교국과의 비교(검사한 대안 설명과 반대 근거) |
| `missingness_listed` | 부족 항목 목록 |
| `failure_vs_not_collected_distinguished` | 요청 실패와 미수집의 구분 |
| `no_zero_fill` | 빈 응답을 0으로 채우지 않음 |
| `precision_sensitivity_shown` | 정밀도·유효범위·민감도(작은 금액 자체를 정상 근거로 쓰지 않음) |
| `correction_snapshots_before_after` | 교정 전후 스냅샷 |
| `recalculated_values` | 교정 뒤 동결 정책으로 재계산한 값 |
| `change_reason` | 변경 사유 |
| `country_and_world_change_shown` | 해당국 금액 변화와 전체국가(`ALL`) 분모 변화 |

**판정 조건표(판정 정책 결정 기록 D17의 공개 정본).** 보고서가 필수 근거 하나를 "남겼다"고 보는 조건이다. 독립 채점기(`eval/scorer/results.py`의 `TAG_RULES`·`_tag_ok`)와 판정 정책의 검증기(단위 R3)가 이 표를 각자 구현한다. 채점기 구현이 이 표와 다르면 채점기의 결함이다. 룰북 `RB-1` 동결 뒤에는 이 표도 채점 규칙이라 새 룰북 버전과 사유로만 바꾼다 `[사실: 룰북 B5]`.

표에서 쓰는 말:

- 사례 문맥: 사례 HS6 h, 대상국 P, 비교월 t, 기준월 b(= t−12, 전년 같은 달), 실행 기록의 `grouping_version`.
- typed claim: 보고서의 정해진 필드(자료 계약 §6의 `claim_type`·`hs6`·`partner`·`period`·`baseline_period`·`metric`·`value`·`unit`·`direction`·`evidence_ids` 등)를 가진 사실 주장. 표의 claim은 모두 사례 품목 h의 것이다.
- 유효한 claim: 대상(`claim_type`·`metric`·`partner`·`period`·`baseline_period`)이 풀리고, 근거 ID가 채점기가 그 값을 계산하는 데 쓰는 원본 행 묶음을 모두 인용한 claim. 값이 맞는지는 보지 않는다(값은 채점 키 `numeric_ok`가 본다). 변화 claim은 `period` t·`baseline_period` b이고, "두 시점 수준 claim"은 `period`가 t인 것과 b인 것 둘이다.
- 보고서 근거: 보고서의 `evidence_ids`와 claim마다의 `evidence_ids`를 합친 근거 ID(`ev:<snapshot_id>:<table>:<rowid>`, 자료 계약 §4.4)가 가리키는 관측 행. 총계 행(`month`가 `RAW:`로 시작)은 뺀다.
- 빠진 키: 신호 계열의 대상 범위에서 관측 상태가 `OBSERVED`·`CONFIRMED_NO_TRADE`가 아닌 키. 단가는 P의 부모 HS6 키와, 부모 행이 있는데 그 HS6 조회가 상태 행을 남긴 HS10 하위 자료(C형)이고, 점유율은 P의 부모 HS6 키와 `ALL` 분모다. 두 시점을 모두 본다.
- 비교집합: 실행 기록의 `grouping_version`으로 고른 스냅샷 비교국 표의 P 비교국(가장 좁은 범위 hs6 → hs4 → hs2).
- 기대값이 null인 claim: 채점기가 원본 행에서 계산하지 않는 대상(값 행이 없는 달, 중량 0의 단가, 자료 계약 §11.2 조건이 성립하지 않는 분해 등).

| 코드 | 충족 조건(보고서에 이것이 있으면 남긴 것으로 본다) |
|---|---|
| `parent_child_match_V_and_Q` | 두 시점 모두 P의 HS10 하위 행이 있고, 보고서 근거가 두 시점마다 P의 부모 HS6 행과 그 시점 HS10 하위 코드마다의 행을 모두 인용한다(한 시점에만 있는 코드도 그 시점에서 인용한다). 대조 결과(일치·불일치)를 담는 typed claim 종류가 없으므로, 대조를 보였다는 것은 대조한 양쪽 행을 모두 근거로 남긴 것으로 판정한다. 대조 결과가 일치인지 불일치인지는 조건이 아니다 |
| `weight_share_decomposition` | `decomposition` claim `within_effect`·`mix_effect`·`residual` 셋(P, t, b)이 모두 유효하다 |
| `per_child_unit_value_stable` | 두 시점에 나오는 P의 HS10 하위 코드마다 `change` claim `r_U@코드`나 두 시점 `value` claim `U@코드`가 유효하다 |
| `comparability_ok` | 단가 계열은 P의 `change` claim `r_U`나 두 시점 `value` claim `U`, 점유율 계열은 P의 `share_change` claim `d_s`나 두 시점 `share` claim `s`가 유효하다. 다른 계열의 지표는 세지 않는다 |
| `partner_comparison_done` | 비교집합 안 비교국 하나 이상의 `comparison` claim이 유효하다: 단가 계열은 `r_U`나 두 시점 `U`, 점유율 계열은 `d_s`나 두 시점 `s` |
| `missingness_listed` | 빠진 키마다 그 키를 `OBSERVED`가 아닌 값으로 적은 `data_status` claim이 대상이 풀리고 근거가 맞다(HS6 키는 `metric` `observation_status`, C형은 `observation_status@<그 HS6 아래 HS10 코드>` 하나. 인용할 행이 없는 키는 대상만 풀리면 된다). 빠진 키가 없으면 둘 중 하나: 비교집합 비교국의 h·두 시점 키를 `OBSERVED`가 아닌 값으로 적은 유효한 `data_status` claim, 또는 P(점유율은 P나 `ALL`)의 두 시점 계열 지표(단가 V·Q·U·r_U·w·분해 셋, 점유율 V·s·d_s) 가운데 계산할 수 없는 것을 null로 적어 `CORRECT`를 받은 claim |
| `failure_vs_not_collected_distinguished` | 빠진 키마다 그 상태를 맞게 적은 `data_status` claim이 있고(`CORRECT`. 인용할 행이 없는 키는 대상이 풀리고 값이 기대 상태와 같으면 된다), h·두 시점의 `data_status` claim에 `WRONG_VALUE`가 없다. 빠진 키가 없으면 `WRONG_VALUE`가 없기만 하면 채운다(빈 조건). 이 코드는 늘 `missingness_listed`와 함께 요구되므로 둘을 함께 보면 빈 조건이 아니다 |
| `no_zero_fill` | 대상이 풀렸고 기대값이 null인 수 claim(`data_status` 제외)에 수(0 포함)를 적은 claim이 하나도 없다. 첫 판정이 단위·방향 오류여도 센다. "채우지 않았음"을 보는 부정 조건이라 해당 claim이 없는 보고서도 채운다 |
| `precision_sensitivity_shown` | P의 두 시점 부모 `V`·`Q` `value` claim 네 개가 유효하다. 반올림 민감도를 적는 typed claim 지표가 없어 그 계산의 입력값으로 대신한다 |
| `country_and_world_change_shown` | P의 `V`와 `ALL`의 `V`(그 HS6 아래 `ALL` HS10 행 합)의 두 시점 `value` claim 네 개가 유효하다 |
| `correction_snapshots_before_after`, `recalculated_values`, `change_reason` | v1에서는 판정하지 않는다. 교정 전후 스냅샷이 있어야 하는데 v1은 동결 스냅샷 하나로 돌아 해당 사례가 없다. 정답표에 적으면 채점기 입력 오류다 |

- 계열별로 쓸 수 있는 코드: 단가는 `parent_child_match_V_and_Q`, `weight_share_decomposition`, `per_child_unit_value_stable`, `comparability_ok`, `partner_comparison_done`, `missingness_listed`, `failure_vs_not_collected_distinguished`, `no_zero_fill`, `precision_sensitivity_shown`이고, 점유율은 `country_and_world_change_shown`, `partner_comparison_done`, `comparability_ok`, `missingness_listed`, `failure_vs_not_collected_distinguished`, `no_zero_fill`이다. 계열 밖 코드를 적은 정답표는 채점기 입력 오류다 `[사실: eval/scorer/results.py FAMILY_TAGS]`.
- 사례의 `required_evidence_ok`는 발동한 신호마다 정답표가 정한 코드를 모두 채웠을 때 참이다. 실자료 묶음(`real_dev`·`real_sealed`)은 정답표가 없어 null이다(사용자 결정 7).

**불일치 보류에서 채울 수 있는지(확인).** 관측은 모두 있는데 대조·분해·분모가 성립하지 않는 보고서도 각 코드를 채울 수 있다. dev20의 불일치 보류 5건 모양으로 채우는 보고서와 코드 하나씩 깨뜨린 보고서를 시험한다 `[사실: tests/test_scorer_dev20_hold.py]`.

- 단가(분류 5, 분류 6의 중량 0): 두 시점 모두 P의 HS10 하위 행이 있으므로, `parent_child_match_V_and_Q`는 금액이 맞지 않거나 HS10 집합이 달라도 부모·하위 행을 모두 인용하면 채운다. 부모 행 중량이 0보다 크므로 부모 단가 변화 `r_U`가 계산돼 `comparability_ok`를 채운다. `no_zero_fill`은 성립하지 않는 분해 셋, 중량 0 하위품목의 `U@`·`r_U@`, 한 시점에만 있는 코드의 없는 달 값을 null로 두면 채운다.
- 점유율(분류 7): 분모가 대상국 금액보다 작아도 `ALL` 금액과 점유율(100% 초과)은 계산되므로, `country_and_world_change_shown`은 네 `value` claim으로, `comparability_ok`는 `d_s` claim으로 채운다. 이 값들은 기대값이 null이 아니어서 수로 적어도 `no_zero_fill`을 어기지 않는다. 런타임 지표 계산도 분모가 0이 아니면 점유율을 계산한다 `[사실: src/tradesentry/metrics/share.py share_value]`.

## 6. 부모 원본 계열 ID

- 부모 원본 계열은 사례의 대상 계열(대상국 × HS6)을 사건을 얹기 **전**의 기본 계열이다. 부모 HS6와 HS10 하위품목의 36개월 금액·중량(흔들림 포함)으로 이뤄진다.
- ID는 `ps_` 뒤에 아래 정규 JSON을 UTF-8로 바꾼 바이트의 sha256 16진수 소문자 앞 16자를 붙인 것이다. 정규 JSON은 키 정렬, 구분자 `,`·`:`, `ensure_ascii=False`로 적는다.

```json
{"children": {"<HS10 뒤 4자리>": [[금액, 중량], "... 월 순서대로 36개"]},
 "parent": [[금액, 중량], "... 월 순서대로 36개"],
 "period": {"start": "YYYYMM", "end": "YYYYMM"}}
```

- dev20의 ID 목록은 `eval/dev/dev20/answers/parent_series_ids.json`에 있다. holdout40 생성 규칙은 이 목록을 제외 목록으로 받고, holdout40 정답표의 ID는 이 목록과 하나도 겹치지 않아야 한다(§8).
- 한계: ID는 값이 한 칸만 달라도 달라지므로, 규모만 바꾸거나 흔들림 seed만 바꾼 변형은 ID 대조로 잡히지 않는다. 그런 변형을 만들지 않는 것은 생성 규칙(§3 첫 항목)이 지키고, ID 대조는 기본 계열을 그대로 가져다 쓴 경우를 잡는다.

## 7. 파일 형식

### 7.1 배치

| 경로(묶음 기준) | 내용 | 샌드박스 |
|---|---|---|
| `input/cases.json` | 사례 목록 | 읽는다(입력 하위 경로) |
| `input/source/raw/` | 응답 XML(§7.3). 스냅샷 폴더의 `raw/`는 `.gitignore`가 빼므로 여기에 둔다 | 넣지 않는다(빌드한 스냅샷만 넣는다) |
| `answers/answers.json` | 정답표 | 넣지 않는다 |
| `answers/parent_series_ids.json` | 부모 원본 계열 ID 목록 | 넣지 않는다 |
| `answers/generation_rules.json` | 생성 규칙(dev20만 공개) | 넣지 않는다 |

묶음 밖(dev20. 단위 S3와 CLI `tradesentry snapshot-verify`가 기본 경로로 찾는 자리):

| 경로(저장소 기준) | 내용 |
|---|---|
| `data/snapshots/dev20/manifest.json`, `collection_log.json`, `snapshot_hash.json` | 수집기 형식 원천의 텍스트(§7.3) |
| `data/snapshots/dev20/snapshot_build.json` | 빌드 기록(`normalized_sha256` 등). 설치 명령이 처음 쓰고 커밋한다 |
| `data/reference/peer_group_dev20.csv` | 합성 비교국 표. 단위 S3가 빌드 기록의 파일 이름을 `data/reference/`에서 찾는다 |

- 샌드박스 허용 목록에는 `input/cases.json` 파일만 넣는다. `input/`을 넣으면 앞부분 일치라 응답 XML도 들어간다(정답은 아니지만 실행에 필요 없다).
- 입력과 정답표를 서로 다른 하위 경로에 두는 이유: 샌드박스 파일시스템 허용 목록은 경로 앞부분 일치라서, 입력 하위 경로만 허용 목록에 넣고 상위 폴더를 넣지 않아야 정답표를 막을 수 있다 `[사실: 병렬 개발 규칙 §6.5 ①]`.
- dev20은 `eval/dev/dev20/`에 이 배치 그대로 둔다. holdout40은 봉인 폴더에 두고, 파일 이름에 기대 상태·분류를 넣지 않는다. 봉인 폴더의 모든 파일(생성 코드·seed·제외 목록 포함)은 해시 목록 `eval/sealed_manifest.json`에 올린다 `[사실: 병렬 개발 규칙 §6.2]`.

### 7.2 사례 목록과 정답표

사례 목록(`cases.json`):

```json
{"schema_version": 2, "dataset": "dev20", "snapshot_id": "<합성 스냅샷 ID>", "policy_version": "dev-0.1",
 "snapshot_normalized_sha256": "<빌드한 스냅샷의 normalized_sha256>",
 "cases": [{"case_id": "<hs6>-<partner>-<YYYYMM>", "hs6": "<6자리>", "partner": "<2자리>", "month": "<YYYYMM>"}]}
```

- 사례 항목은 키 네 개만 가진다. 기대 상태·분류·생성 계열·부모 원본 계열 ID를 넣지 않는다. `snapshot_normalized_sha256`은 선택이며, 있으면 빌드 결과와 대조한다(자료 계약 §4.4 규칙 4의 SQLite 밖 기록).

정답표(`answers.json`):

```json
{"schema_version": 2, "dataset": "dev20", "snapshot_id": "<같은 ID>", "policy_version": "dev-0.1",
 "thresholds": {"unit_value": 30, "share": 10},
 "cases": [{"case_id": "<같은 식별자>", "scenario_class": 1, "parent_series_id": "ps_<16자>",
            "rule": {"unit_value": "<규칙 키 또는 null>", "share": "<규칙 키 또는 null>"},
            "expected": {"signals": {"unit_value": "TRIGGERED", "share": "NOT_TRIGGERED"},
                         "signal_status": {"unit_value": "MONITOR", "share": "NOT_TRIGGERED"},
                         "review_status": "MONITOR", "unresolved_evidence": false,
                         "required_evidence": ["<§5.1 순서>"]},
            "note": "<선택: 검토용 한 줄>"}]}
```

- `expected`의 키와 값은 독립 채점기가 읽는 형식(`eval/dev/oracle_ABC.json`의 사례 구조, 상태는 계약 코드)과 같다. `rule`·`scenario_class`·`parent_series_id`·`note`는 검사와 검토용이고 채점기는 쓰지 않는다 `[사실: eval/scorer/results.py read_answer_table]`.
- `thresholds`는 선택이며 그 묶음 정책 버전의 탐지 기준을 옮겨 적는다.
- `required_evidence`는 발동한 신호가 하나면 목록, 두 신호가 모두 발동하면 `{"unit_value": [...], "share": [...]}`다(§5.1).

부모 원본 계열 ID 목록(`parent_series_ids.json`): `{"schema_version": 2, "dataset": "dev20", "id_rule": "<§6의 설명>", "parent_series_ids": ["ps_…", …]}`(정렬, 중복 없음).

### 7.3 수집기 형식 원천과 스냅샷 빌드

- 원천은 실자료 수집기(`src/tradesentry/ingest.py`)가 만드는 모양을 따른다. 그래야 단위 S2가 빌드하고 단위 S3가 검증한다(DT1 결정 기록 `docs/tracking/decisions/20260925-0002-data-decision-dt1-snapshot-build-and-kernel.md` ⑨).
  - `manifest.json`: `{"snapshot_id", "generated_at", "config", "requests"}`. `requests`는 수집기 `build_manifest(config)`의 결과 그대로다.
  - `raw/<request_id>.xml`: 요청마다 관세청 정상 봉투(`resultCode` `00`) 응답. 국가별(`nitemtrade`) 응답의 품목 코드는 `hsCd`, 품목별 전체국가(`itemtrade`) 응답은 `hsCode`, 달은 `YYYY.MM`, 총계 행(`총계`, 코드 `-`)이 하나 있다(합성 원천은 두 종류 모두 첫 행에 둔다. 실응답은 국가별이 첫 행, 전체국가가 마지막 행이다. 수집기는 위치와 무관하게 읽는다). 수입금액 `impDlr`(USD 정수), 수입중량 `impWgt`(kg 정수).
  - `collection_log.json`: 요청 결과. `raw/`에 파일이 있는 요청은 OK, `FAILED` 목록은 실패(HTTP 500, 응답 본문 없음), `NOT_COLLECTED` 목록은 수신 기록 없음.
  - `snapshot_hash.json`: raw 결합 sha256(`shasum -a 256 raw/*.xml | shasum -a 256`과 같은 계산).
  - 합성 비교국 표 CSV(`peer_group_<snapshot_id>.csv`, `data/reference/`): 열은 자료 계약 §2.3.6 필드 17개.
- 빌드: 원천으로 수집기 SQLite를 재현하고(수집기 `store_result`, 시각은 기록의 고정 시각) 단위 S2 `build_to`(정책 객체는 그 묶음의 정책 버전)로 파생 SQLite를 만든 뒤, 단위 S3 `verify_snapshot`(비교국 표 파일을 명시)이 통과해야 한다. 스냅샷 메타의 `source_kind`는 `controlled`, `source_url`은 생성 규칙 문서와 생성 코드의 저장소 상대경로다 `[사실: 자료 계약 §2.3.1]`.
- dev20은 명령 `uv run --locked python -m eval.datagen.dev20 install`로 `data/snapshots/dev20/`에 `raw/`, 수집기 `snapshot.sqlite`, `snapshot_build.sqlite`(모두 `.gitignore`가 빼는 자리)를 만든다. 이미 있는 것은 대조만 하고 덮지 않는다. 그 뒤 `uv run --locked tradesentry snapshot-verify --snapshot dev20`이 raw 대조까지 통과하고(종료 코드 0, 보고 `ok` 참), `git status`에 바뀐 파일·추적 안 된 파일이 생기지 않는다. 자료 접근층은 `open_snapshot("dev20")`으로 연다.

### 7.4 생성 규칙 형식(dev20의 생성 도구)

`eval/datagen/dev20.py`의 `run`은 생성 규칙 JSON을 받아 §7.1의 파일을 만들고 §8의 검사와 자체 검산(발동 집합 = 사례 집합, 기준 거리 0.05 이상, 규칙별 자료 불변식)을 한다. 규칙의 최상위 키는 `schema_version`, `dataset`, `snapshot_id`, `policy_version`, `fixed_time`, `world`(기간·HS4·HS6·상대국·흔들림·계열별 기본 월 값·나머지 세계 값·비교국 k·기준연도), `cases`(사례마다 식별자·분류·사건 목록·판정 근거 규칙·기대 판정·메모)다. 사건 종류는 `exact`(그 달 기본 값 그대로), `children`(그 달 하위 값 지정), `parent`(부모 행만 덮어쓰기), `scale`(같은 HS6의 다른 나라·나머지 세계의 물량·단가 배율), `world`(그 달 전체국가 분모 덮어쓰기), `request`(요청 실패·미수집)다. holdout40 생성에 이 도구를 쓸지는 로드맵 DT6가 정한다. 쓰더라도 생성 규칙과 결과는 봉인 폴더에만 두고, `generate` 명령(저장소 `outputs/`에 쓴다)은 쓰지 않는다. 이 도구의 자체 검산은 생성 코드 안에 있으므로, 도구를 다시 써도 생성 코드·런타임 모듈과 따로 된 검산(병렬 개발 규칙 §6.6의 1)이 따로 필요하다. 생성 에이전트는 부모 원본 계열 ID도 생성 자료에서 다시 계산해 정답표 값과 대조한다(단위 V4는 정답표에 적힌 ID를 믿는다).

## 8. 결정적 검사(단위 V4)

- 명령: `uv run --locked python -m eval.datagen.holdout40_check --cases <사례 목록> --answers <정답표> [--dev20-ids <dev20 목록>]`. 모든 검사가 통과하면 종료 코드 0, 실패 1, 입력을 읽지 못하면 2.
- 검사: 사례 목록 스키마, 정답표 스키마(규칙 키와 기대 판정·필수 근거의 일치, 집계, 어휘 13개), 식별자(형식·고유·두 파일 집합 같음·`{hs6}-{partner}-{month}` 모양이면 세 값 일치), 분류 규칙(§4의 기대 처리), 분류별 건수(§3 배분), dev20과 부모 원본 계열 ID 겹침(holdout40만).
- 보고에는 건수·검사 이름·위반 종류만 적는다. 사례 식별자·값·경로를 적지 않아 봉인 묶음을 검사할 때도 내용이 드러나지 않는다. 봉인 폴더를 기본 입력으로 읽지 않는다.
- holdout40 생성 에이전트는 봉인 직전에 이 명령과 자체 검산(발동 여부를 정답표 표시가 아니라 생성 자료에서 다시 계산)을 돌리고, 오케스트레이터에게 통과 여부와 건수만 보고한다 `[사실: 병렬 개발 규칙 §6.6 1]`. 평가 스킬 ②의 사전 점검도 이 명령을 다시 돌린다.

## 9. 한계와 열린 항목

- 합성 자료는 같은 정책 안의 제한된 구조 변화 시험이며 현실 분포를 대표하지 않는다 `[사실: 구 개발계획 §8.1]`. dev20 숫자는 등급 D다.
- dev20 점수는 방향 확인용이다. 20건에서는 모든 사례를 보류한 기준 점수와 Wilson 95% 구간(룰북 B4)이 겹치지 않게 이기기 어렵고, 현재 런타임이 낼 수 없는 기대 상태(예: 판정 정책 짝 PR이 보류 사유를 나누기 전의 불일치 보류) 때문에 도달 가능한 점수에 상한이 있을 수 있다. 수치(상태 정확도·근거 충족의 상한, 모든 사례 보류 점수와 필요한 점수)는 DT5 결정 기록 "영향과 넘길 곳"에 적었다.
- 열린 항목(확정되면 이 문서·dev20·검사를 함께 고친다)
  - 분류 4에서 만들지 않은 두 변형(`UNRESOLVED_ZERO`만 있는 경우, 비교국 자료만 빠진 경우)을 holdout40에서 열지(오케스트레이터, holdout40 생성 전).
  - 합성 묶음의 비교 대상을 `g1` 동결 뒤 어떻게 둘지(§2.2).
- 닫힌 항목: U1·U2·U4는 `policy_v1` 승인(2026-09-25(금))으로, D17(필수 근거 판정 조건표와 보류의 사유별 근거)은 사용자 결정 14와 §5.2·§5.3으로 닫았다.

## 용어 설명

- **dev20 / holdout40**: 모든 에이전트가 쓰는 공개 합성 개발 자료 20건 / 저장소 밖에 봉인해 한 번만 채점하는 합성 평가 자료 40건.
- **분류(시나리오 분류)**: 합성 사례를 만드는 통제 조건 10가지(구 개발계획 §8.1).
- **판정 근거 규칙**: 신호마다 어느 판정 근거로 상태를 내는지 정한 키. 신호별 상태와 필수 근거를 함께 정한다.
- **필수 근거**: 보고서가 그 상태를 내려면 남겨야 하는 근거의 이름(판정 정책 단위 P5 어휘).
- **부모 HS6 행 / HS10 하위 행**: 국가별 조회에서 HS4로 요청해 받은 HS6 월 값 / HS6로 요청해 받은 10자리 세부 코드 월 값.
- **구성효과 분해**: 부모 단가 변화를 하위품목 단가 변화 효과(`within_effect`)와 중량 비중 변화 효과(`mix_effect`), 잔차(`residual`)로 나누는 계산(자료 계약 §11.2).
- **부모 원본 계열 ID**: 사례의 기본 계열 값으로 만든 지문. dev20과 holdout40이 같은 기본 계열을 쓰지 않았는지 확인하는 데 쓴다.
- **수집기 형식 원천**: 실자료 수집기가 남기는 파일 모양(수집 계획, 응답 XML, 수신 기록)으로 만든 합성 자료의 원본.
- **θ**: 단가 탐지 기준(단가 변화율 절댓값, %). `dev-0.1`에서 30.
- **U1·U2·U4·D17**: 판정 정책 결정 기록이 사용자·오케스트레이터 확인으로 넘긴 항목(기준 해석, 최소 금액·중량, 반올림 불안정, 필수 근거 판정 조건). 모두 닫혔다(§9).
- **판정 조건표**: 필수 근거 코드마다 보고서에 어떤 typed claim·근거 ID가 있으면 그 근거를 남긴 것으로 보는지 정한 표(§5.3). 채점기와 검증기가 각자 구현한다.
- **불일치 보류**: 관측은 모두 있는데 부모·하위 대조, 구성 분해, 전체국가 분모가 성립하지 않아 내리는 자료 보류(`hold_inconsistent`, §5.2).
