# DT2 지표 단위의 해석과 입출력 약속

DT2(지표 계산, 데이터 트랙) 구현(단위 X1~X4, PR #26)에서 자료 계약이 정하지 않았거나 데이터 트랙(D)에게 맡긴 세부와, 검토 1회차(무역통계·관세 검토, Codex(OpenAI의 코딩 에이전트 CLI) 교차 검토)가 요구한 해석을 적는다. 코드와 시험은 PR #26에 있다. 항목마다 **확정** 또는 **잠정**을 붙였다.

용어

- 지표 단위: X1 단가·변화율(`src/tradesentry/metrics/unit_value.py`), X2 점유율·변화(`share.py`), X3 구성효과 분해(`decompose.py`), X4 자릿수·반올림(`rounding.py`). 모두 `src/tradesentry/metrics/` 아래다.
- metric 객체: 자료 계약 §2.3.4의 지표 값 하나. 키는 `metric_id`, `formula_version`, `inputs`, `evidence_ids`, `value`, `unit`, `comparability_flags`, `tolerance` 여덟 개다.
- 표시 값: 자료 계약 §11.3의 표시 자릿수로 사사오입(ROUND_HALF_UP, 절댓값 기준 5 이상이면 0에서 먼 쪽)한 값.
- 정확값(반올림 전 값): 정수 USD·kg에서 `fractions.Fraction`(오차 없는 분수)으로 계산한 값.
- 역할별 입력: 지표 단위의 run 입력에서 관측 행(자료 계약 §2.3.2의 `observation`)을 쓰임에 따라 나눈 목록. `parent`(상대국 부모 HS6 행), `world`(전체국가 `ALL` HS10 행), `children`(상대국 HS10 하위 행)이다.
- 부모 대조: 부모 HS6 행과 HS10 하위 행의 합을 맞춰 보는 일. 금액은 정확 일치, 중량은 허용오차 안이어야 한다.
- K1·K3·K4: DT1의 계약 커널(여러 단위가 함께 쓰는 정의 모음), 자료 접근층(스냅샷을 읽는 `dal/` 패키지), 정책 수치 읽기 단위.
- P1·P3: MT1(판정 정책)의 신호 발동 단위와 신호별 판정 단위.

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 00:35(기록 시각). ①~⑪은 2026-09-24(목) 23:20~2026-09-25(금) 00:10 DT2 구현 중에, ⑫~⑭는 검토 1회차 뒤 수정 2회차(00:20~00:35)에 정했다 |
| 제목 | DT2 지표 단위의 입출력 모양, metric 값의 뜻과 반올림 전 값, `inputs` 키, `metric_id`, 사유 어휘, 허용오차, 행 규칙 전제, 부모 중량 0, 부모 대조 |
| 결정 | 아래 "결정 내용" ①~⑭ |
| 이유와 근거 | 아래 "결정 내용"의 항목마다 적었다 |
| 검토한 대안 | 아래 "검토한 대안" |
| 결정 주체 | 소유 트랙(D). ⑦의 행당 반올림 kg 이름은 DT1(단위 K4)의 정책 파일 키와 같다. ②는 판정 정책(MT1)이 요구한 반올림 전 비교에 맞췄다 |
| 공용 약속 여부 | ②의 metric `value` 뜻은 공용 약속인지 애매하다. 병렬 개발 규칙 §4.5는 애매하면 공용 약속으로 보라고 한다. 판정 정책 검토의 사용자 확인 항목(반올림 전 비교)에 묶을지는 오케스트레이터가 정한다(잠정). 나머지는 D 소유 단위의 입출력 약속이고, 계약 필드·상태값·ID 형식·기준값의 값을 바꾸지 않는다 |
| 영향 | 아래 "영향과 넘길 곳" |
| 관련 PR | #26 |

## 결정 내용

① **역할별 입력과 행 규칙의 전제** — 잠정(조립 작업 AS1의 어댑터가 확정한다)

- 공통 입력은 `snapshot_id`(필수), `hs6`, `partner`, `period`(비교월 t), `baseline_period`(t−12)다. X1은 `parent`, X2는 `parent`·`world`, X3은 `parent`·`children`·`weight_rounding_kg`를 더 받는다.
- 행 하나는 관측 객체의 키(`month`, `amount_usd`, `net_weight_kg`, `observation_status`, 있으면 `hs_code`·`hs_level`·`partner_code`·`flow`)와 `evidence_ids`(근거 ID 목록)를 가진다.
- 달마다 행은 모두 값 행(`OBSERVED`)이거나 모두 상태 행이다. 섞이면 ValueError다. `CONFIRMED_NO_TRADE` 행은 그 달의 유일한 행이어야 한다. 두 달 밖의 행, 수입이 아닌 흐름, 총계 행(`RAW:총계`), 다른 상대국 행, 필요한 달의 행 없음도 ValueError다.
- 자료 계약 §2.3.2의 행 규칙 4(부모 행 고르기, 같은 키의 HS6 상태 행은 하위 자료 쪽으로)와 행 규칙 6(`ALL` 중복 제거)은 자료 접근층이 적용한 뒤 넘긴다고 본다. 지표 단위는 확인만 한다. 같은 달에 같은 HS10 행이 두 번 오면 ValueError로 멈춘다(v2에서 중복을 빼지 않으면 분모가 두 배가 된다).
- 이유: 지표 단위가 행 규칙을 다시 구현하면 자료 계약 §11.2의 원천 규칙이 두 곳에서 갈린다.
- 잠정인 이유: DT1 자료 접근층(K3)의 출력이 이 모양과 그대로 맞물리지 않는다(무역통계 검토 권고 5). `ALL` 쪽은 달마다 합계·코드·근거 목록만 주고, 빠진 달의 부모는 근거가 빈 객체와 `missingness` 목록으로 준다. 옮기는 일은 AS1 어댑터가 한다(아래 "영향과 넘길 곳").

② **metric `value`는 표시 값, 반올림 전 값은 `exact_value`** — 잠정(공용 약속 여부 판단 대기)

- `value`는 정확값을 자료 계약 §11.3 자릿수로 한 번 사사오입한 값이다. V·Q는 int, 나머지는 끝자리 0을 지킨 Decimal이다. -0.0은 내지 않는다.
- 반올림 전 값은 metric 객체의 필드로 두지 않는다(자료 계약 §2.3.4에 그런 키가 없다). 세 함수가 `inputs`의 정수로 Fraction을 다시 계산한다.
  - `unit_value.exact_value`: U, r_U, U@, r_U@
  - `share.exact_value`: V, s, d_s
  - `decompose.exact_value`: within_effect, mix_effect, residual, w@. U@·r_U@는 X1 쪽으로 넘긴다.
- 임계값 비교(P1, "같으면 발동")와 분해 값의 "기준 안" 판정(P3)은 `value`가 아니라 `exact_value`로 한다. 표시 값으로 비교하면 판정이 뒤집히는 경계가 있어 시험으로 고정했다.
  - r_U: 정확 −29.96, 표시 −30.0
  - within_effect: 정확 2.9955, 표시 3.00
  - d_s: 정확 9.96, 표시 10.0(무역통계 검토 탐침)
- `exact_value`의 입력 형식: `value`가 int나 Decimal이어야 한다. 공통 실행기 출력 파일처럼 Decimal이 문자열로 적힌 객체는 TypeError다. JSON은 `parse_float=Decimal`로 읽어 넘긴다.
- 대조 범위: 다시 계산한 값을 반올림해 `value`와 같은지만 본다(`rounding.checked_exact`). `inputs` 자체가 스냅샷 원본과 같은지는 근거 ID와 도구 `verify_evidence`(단위 I5)가 본다(Codex 권고 1).
- 분해 값이 null이면 `decompose.exact_value`는 None이다. 관측 상태와 부모 대조 사유는 `inputs`만으로 다시 판정하지 않는다.
- 이유
  - 자료 계약 §11.3: "표시값과 기대값은 정수 USD·kg에서 계산해 반올림한다."
  - 자료 계약 §9.1: 틀 채우기 보고서는 수를 표시 자릿수로 쓴다.
  - 이중 반올림을 막고, 사례당 토큰 한도를 아낀다.

③ **`inputs` 키** — 확정

- 공통 키는 `metric`(기호), `hs6`, `partner`, `period`, `baseline_period`다. 수준 지표의 `baseline_period`는 null이다.
- 수준 지표
  - U·U@: `V`, `Q`
  - s: `V_country`, `V_world`
  - w@: `Q`, `Q_total`
  - V(상대국): 더 없음
  - V(`ALL`): `row_count`
- 변화 지표: 접미사 `_0`은 t−12, `_1`은 t다(oracle 관례).
  - r_U·r_U@: `V_0`, `Q_0`, `V_1`, `Q_1`
  - d_s: `V_country_0`, `V_world_0`, `V_country_1`, `V_world_1`
- 분해 세 값(무역통계 검토 막는 지적 2)
  - 부모 HS6 행의 `V_0`·`Q_0`·`V_1`·`Q_1`: 부모 대조와 ΔU에 쓴다.
  - `hs10_values` {HS10 코드: {`V_0`, `Q_0`, `V_1`, `Q_1`}}: 분해식에 쓴 하위 행이다. 그 달에 행이 없거나 하위 자료가 상태 행이면 null이다.
  - `evidence_ids`는 두 달의 부모 행과 하위 행(또는 상태 행)이라 `inputs`와 짝이 맞는다.
- V(`ALL`)는 더한 행의 금액을 `inputs`에 복제하지 않는다. 합은 `evidence_ids`의 `ALL` HS10 행으로 대조한다. 정수 합이라 반올림 문제가 없다.

④ **`metric_id` 형식과 고유 범위** — 확정(무역통계 검토 권고 7)

- 형식은 `{기호}-{sha256 앞 16자}`다. 해시하는 내용은 `snapshot_id`와, `metric_id`를 뺀 객체 나머지 전체를 키 순으로 정렬한 JSON이다.
- `snapshot_id`는 X1~X3 입력의 필수 키다. 근거 ID는 모두 `ev:<snapshot_id>:`로 시작해야 한다(자료 계약 §4.4 풀림 규칙 2). 아니면 ValueError다.
- 고유 범위: 스냅샷이 다르면 근거 ID가 빈 지표(`hs10_absent`)도 ID가 다르다. 같은 스냅샷에서 내용이 같으면 같은 ID다(결정적).
- metric 객체의 키 여덟 개는 그대로다. `snapshot_id`를 객체에 더하지 않는다.

⑤ **`formula_version`과 계약 버전 표시** — 확정

- `formula_version`은 `"1"`(자료 계약 §11.2 공식의 첫 구현)이다. 공식을 바꾸면 올린다.
- 네 모듈에 `SCHEMA_VERSION = 1`을 둔다(인수 조건 1).

⑥ **`comparability_flags` 어휘** — 확정

- 관측 상태 때문이면 자료 계약 §3.4의 코드를 그대로 쓴다: `UNRESOLVED_ZERO`, `REQUEST_FAILED`, `NOT_COLLECTED`, `CONFIRMED_NO_TRADE`.
- 계산 사유는 소문자로 적는다.
  - `zero_weight`: 중량 0. U·U@·w@, 분해의 하위·부모 중량
  - `zero_baseline`: 기준월 단가 0
  - `zero_denominator`: `ALL` 금액 0
  - `value_missing`: `OBSERVED` 행의 금액·중량 칸이 빔
  - `hs10_absent`: 그 달에 그 HS10 행이 없음
  - `hs10_set_changed`: 두 시점의 HS10 집합이 다름
  - `parent_mismatch`: 부모 대조 실패
- 값이 있어도 승격된 0이 들어갔으면 `CONFIRMED_NO_TRADE`를 비고로 남긴다(예: 점유율 분자가 승격 0이면 s 0.0과 d_s에 남는다).
- 목록은 사전순이고 중복이 없다. `value`가 null이면 사유가 하나 이상 있다.

⑦ **`tolerance`와 행당 반올림 kg** — 확정

- metric `tolerance`는 분해 세 값에만 담는다. 두 시점 HS10 집합이 같을 때 부모 대조의 중량 허용오차이고, 단위는 kg(Decimal)이다. 식은 `weight_rounding_kg × (HS10 행수 + 1)`로 자료 계약 §11.1의 꼴이다. 판정은 수집기와 같은 "≤이면 통과"다.
- 지표 단위(USD/kg)의 값 비교 허용오차가 아니다. 나머지 지표의 `tolerance`는 null이다.
- 행당 반올림 kg의 출처는 K4 정책 객체의 `tolerance.weight_rounding_kg`다(DT1 `configs/policy_dev.json`, `dev-0.1`에서 0.5). 코드에 박지 않는다. 금액 대조는 정확 일치다(정책 파일 `tolerance.amount_usd` = 0과 같다).

⑧ **상태 행의 `hs_code` 허용 범위** — 확정

- 부모 역할: 값 행은 그 HS6다. 상태 행은 그 HS6나 그 HS4다. HS4 스캔 요청이 실패하면 수집기가 상태 행을 요청 코드(HS4)에 귀속하기 때문이다.
- `ALL` 역할: 값 행은 그 HS6 아래 10자리 HS10이다. 상태 행은 HS6나 HS4다.
- 하위 역할: 값 행은 그 HS6 아래 HS10이다. 상태 행은 HS6만이다. HS10 하위 자료는 HS6 요청에서만 온다.

⑨ **단위 표 밖의 출력** — 확정

- X2는 `docs/plan/UNITS.md` §3.3의 출력("s, d_s") 말고도 V(상대국·`ALL`) metric을 낸다. oracle 점유율 필드(V_country·V_world)와 분모 축소 설명의 근거를 드러내기 위해서다.
- X3은 자료 계약 §2.3.4가 도구 `decompose_hs`에 요구하는 HS10 하위 지표(U@, r_U@, w@)를 낸다. 코드마다 U@(t−12·t), r_U@, w@(t−12·t)이다.

⑩ **대상 검사** — 확정

- `partner`는 대문자 2자리 관세청 국가코드다(`ALL`은 지표 대상이 아니다).
- `baseline_period`는 `period`의 정확히 12개월 전이어야 한다(룰북 B3-1: 전년동월 지표의 기준월은 t−12).

⑪ **관측 상태 상수의 위치** — 잠정(조립 점검 AS4에서 합친다)

- 계약 커널 K1이 생기기 전에 만들어서 X4에 따로 적었다. AS4에서 K1 정의로 합친다.

⑫ **부모 중량 0이면 분해 세 값 모두 null** — 확정(무역통계 검토 권고 4)

- 룰북 B3-1의 "양 시점 중량 유효"에 부모 HS6 행의 중량도 넣는다.
- 부모 대조가 허용오차 안이어도(예: 부모 0kg, 하위 1kg, 허용오차 1.0) within_effect·mix_effect·residual은 모두 null이고 사유는 `zero_weight`다.
- 독립 채점기(DT8)도 같은 규칙을 써야 두 쪽 기대값이 같다.

⑬ **`parent_check`의 뜻과 null 규칙** — 확정(Codex 권고 2)

- X3 출력의 `parent_check`는 달(t−12, t)마다 한 항목이다: {`period`, `row_count`, `V_parent`, `V_hs10`, `Q_parent`, `Q_hs10`, `tolerance`, `V_match`, `Q_match`}.
- 키의 뜻
  - `row_count`: 하위 HS10 값 행 수
  - `V_parent`·`Q_parent`: 부모 행 값(승격 행은 0)
  - `V_hs10`·`Q_hs10`: 하위 행 합
  - `tolerance`: 행당 반올림 kg × (`row_count` + 1)
  - `V_match`: 금액 정확 일치
  - `Q_match`: |`Q_parent` − `Q_hs10`| ≤ `tolerance`
- null 규칙
  - 하위가 상태 행이면 `period` 말고 모두 null이다.
  - 하위가 값 행이어도 부모가 누락 상태이거나 부모·하위의 V·Q 가운데 하나라도 비었으면, `period`·`row_count`만 값이 있다.
  - null은 "대조하지 못함"이지 "일치"가 아니다.
- 판정 정책 P3의 `parent_child_match`(참거짓)는 두 달 모두 `V_match`·`Q_match`가 참일 때만 참으로 옮기기를 권한다(null은 참이 아니다). 옮기는 규칙은 AS2가 정한다.

⑭ **머리 주석 문구** — 확정(무역통계 검토 권고 8)

- X1~X4 머리 주석의 입력·출력 줄을 `docs/plan/UNITS.md` §3.3의 문구와 글자까지 같게 되돌렸다.
- 구체적인 모양은 모듈 머리말과 이 기록에 둔다. 단위 표는 고치지 않는다.

## 검토한 대안

- ① 지표 단위가 원시 행을 받아 행 규칙 4·6을 직접 적용하는 안: 자료 접근층과 두 번 구현돼 원천이 갈린다. X2가 K3의 달별 합계 형식을 그대로 받는 안: 행 단위 중복 검사(분모 두 배 함정)를 할 수 없어 어댑터 쪽을 골랐다. AS1에서 다시 볼 수 있어 잠정이다.
- ② `value`에 반올림 전 값(긴 Decimal)을 담는 안은 버렸다.
  - 무한소수는 어디선가 잘려 정확하지 않다.
  - 보고서 틀이 반올림을 잊으면 긴 수가 보고서에 나간다.
  - 표시 자릿수 반올림이 두 번 일어날 수 있고, 사례당 토큰을 더 쓴다.
- ② metric 객체에 반올림 전 값 필드를 더하는 안: 자료 계약 §2.3.4의 필드를 바꾸는 일이라 공용 약속 절차가 필요하다.
- ④ 고유 범위를 "한 스냅샷 안"으로만 적는 안: 근거 ID가 빈 지표가 스냅샷을 넘어 같은 ID를 가진다. 자료 계약 §4.5의 "다른 대상에 다시 쓰지 않는다"와 어긋날 수 있다.
- ⑫ 부모 중량 0이어도 within·mix를 내고 residual만 null로 두는 안(1회차 구현): 채점기가 "중량 유효"에 부모 중량을 넣으면 런타임의 within·mix 주장이 `WRONG_VALUE`가 된다.
- ⑬ `parent_check` 없이 분해 값의 사유만 남기는 안: P3의 `parent_child_match`를 만들 근거가 도구 쪽에 없어진다.

## 영향과 넘길 곳

- MT1(판정 정책)
  - P1은 `unit_value.exact_value`·`share.exact_value`로 입력을 만든다.
  - P3는 `decompose.exact_value`·`unit_value.exact_value`와 `parent_check`로 입력을 만든다.
  - metric `value`를 넘기지 않는다.
- MT2(도구, 단위 I2~I4)
  - run 입력을 역할별로 만들고 `snapshot_id`와 `weight_rounding_kg`(K4 정책 객체)를 넘긴다.
  - 도구 봉투의 `metrics`에 metric 객체를 그대로 넣는다. 사례당 토큰 한도를 보고 X3 하위 지표를 얼마나 넣을지 정한다(HS10 6개면 33개).
- MT3(보고서 틀·검증기, 단위 R1~R3)
  - claim 값은 `value`(표시 값)를 그대로 쓴다.
  - 표시 자릿수와 반올림은 X4의 `display`·`round_half_up`을 쓴다.
- DT5(dev20 정답표)·DT8(독립 채점기)
  - 경계 근처 시나리오는 정수에서 정확히 계산하고 "같으면 발동"을 쓴다.
  - ⑫(부모 중량 0)와 ⑥(null 사유)을 같은 뜻으로 쓴다.
- AS1(탐지 조립)
  - DT1 K3 출력 → `parent`·`world` 어댑터를 만든다.
    - 값이 있는 달은 K3 객체를 행 하나로 넘긴다.
    - 빠진 달은 `missingness` 항목을 상태 행으로 펼치고 그 근거 ID를 붙인다.
    - `world`는 근거 ID를 K3로 풀어 `ALL` HS10 행으로 다시 만든다.
  - 조립 시험에 세 경계를 넣는다.
    - r_U 정확 −29.96(표시 −30.0) → 미발동
    - d_s 정확 9.96(표시 10.0) → 미발동
    - r_U 정확 −30 → 발동
  - 경계 시험(허용 import)도 같이 확인한다.
- AS2(사례 조사 조립)
  - `children` 어댑터를 만든다.
  - P3 입력(`decomposition`, `children`, `U_baseline`)을 `exact_value`로 만든다.
  - `parent_child_match`를 옮긴다(⑬).
- AS4(조립 점검): ⑪의 관측 상태 상수를 K1로 합친다.
- oracle 재현 시험(`tests/test_metrics_oracle.py`)의 대조 필드 38개 가운데 V_world_0·V_world_1(세 사례, 6개)은 합산 확인이다. oracle에 `ALL` 입력이 없어, 기대 합계로 만든 `ALL` 행을 더한 값이 맞는지만 본다. 나머지 32개는 사례 입력에서 공식으로 재현한다.
