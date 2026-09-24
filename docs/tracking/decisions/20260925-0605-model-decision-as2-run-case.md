# AS2: `run-case` 배선, 근거 상태 변환과 조립 점검 결과

조립 작업 AS2(사례 조사 조립: 도구·조사 흐름·보고서·검증기·실행 기록 단위를 이어 `tradesentry run-case`를 만드는 작업)에서 정한 배선·도구 자리·근거 상태 변환·출력과, 실자료 스냅샷을 이번 PR에서 조사하지 않는 잠정 결정, 조립 점검(`docs/plan/UNITS.md` §5) 1·2·5단계 결과를 적는다. 코드와 시험은 같은 PR에 있다.

용어

- 조립체 3: `run-case` 한 명령이 도는 단위 묶음. 지표 X1~X4, 판정 정책 P3~P5, 비교 대상 G1, 조사 I1~I13, 보고서·검증기 R1~R4, 실행 기록 L1~L3이다(`docs/plan/UNITS.md` §4).
- 도구 봉투(envelope): 도구 5개(단위 I1~I5)가 같은 모양(키 11개)으로 돌려주는 출력(자료 계약 §5).
- 근거 상태: 판정 정책 P3(신호별 판정)이 받는 입력. 도구 봉투에서 코드가 결정적으로 만든다(MT1 결정 기록 `20260925-0025-model-decision-mt1-policy.md` ⑪).
- 필수 비교 완료 표시: 근거 상태의 `comparisons` 값 `done`(수행해 결과를 얻음)·`incomplete`(수행했지만 빠진 관측 때문에 결과 없음)·`not_performed`(수행하지 않음).
- 1번 사유: P3 판정 순서 1번(자료 부족 → `HOLD`)에 걸리는 사유. 빠진 관측, 비교 가능성 문제(`comparability_issues`), 분해를 쓸 수 없음 등.
- 조기 종료: 비교할 수 없는 사례에서 뒤 조회를 건너뛰는 규칙(개발 플랜 §6.6).
- C형: 대상국 부모 HS6 행은 있는데 HS10 하위 자료만 상태 행인 달(자료 계약 §2.3.2 행 규칙 4, oracle C).
- 정확값: 표시 자릿수로 반올림하기 전의 값(`fractions.Fraction`, 지표 단위의 `exact_value`).
- 가짜 모델: 정해 둔 답을 차례로 돌려주는 시험용 전송 자리(`tests/units/I7/fakes.py`의 `ScriptedTransport`). 실제 NIM(NVIDIA 클라우드 추론 API)을 부르지 않는다.
- 두 신호 스냅샷: 두 신호가 모두 발동한 합성 사례 둘을 담은 시험용 스냅샷 `as2_two_way`(`tests/units/F2/run_case_fixture.py`).

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 06:05(기록 시각). 바탕은 `main` cf9d607 + MT4 브랜치 6dfc489(병합 02ebeb5)이고, 작업 중 AS1(#32)이 병합된 `main` d945792를 받았다(f9e5633). 코드 커밋은 c9085f8(단위 I12)·81b9df9(단위 F2) |
| 제목 | `run-case` 배선 순서·도구 자리·근거 상태 변환·C형 펼치기·출력 파일, 실자료 스냅샷 거부(잠정), 조립 점검 1·2·5단계 결과와 단위 표 판정 갱신 |
| 결정 | 아래 "결정 내용" ①~⑫. ⑬은 2회차(실제 NIM 실측 6회 뒤, 같은 날 06:3x)에 더했다 |
| 이유와 근거 | 항목마다 적었다 |
| 검토한 대안 | 아래 "검토한 대안" |
| 결정 주체 | 소유 트랙(M). ⑩은 AS1 결정 ⑤와 같은 오케스트레이터 결정(작업 지시)을 따른다 |
| 공용 약속 여부 | 아니다. 계약 필드·상태값·ID 형식·기준값·계획 경로·명령 표를 바꾸지 않았고 새 CLI 옵션도 없다. 출력 파일 이름은 이름·출력 규칙(자료 계약 §10.3 N4·N6)에 만든 단위의 도메인명을 넣은 것이다. ⑦의 점유율 비교 가능성 문제 이름과 ⑧의 켜는 스위치는 M 소유 단위 안의 값이다. ⑧의 규칙을 켜는 일은 2026-09-25(금) 09:00 사용자 결정(U4) 대상이다 |
| 영향 | 아래 "영향과 넘길 곳" |
| 관련 PR | AS2(브랜치 `model/AS2-run-case`) |

## 결정 내용

① **배선 순서와 종료 코드** — 확정

- 처리 함수 표의 `run-case` 항목을 `dispatch._run_case`로 잇는다(`src/tradesentry/cli/dispatch.py`, 단위 F2). 흐름은 아래 순서다. 뒤 단계가 실패하면 앞에서 확보한 실행 폴더가 남는다(MT5 결정 ⑥과 같은 방식).
  1. 실행명 `run_case-{시각}` 확보(자료 계약 §10.3 N8)
  2. K4 `load_policy(--policy)`. 실패하면 1
  3. 모델 설정(단위 I9, `configs/model/`) 읽기. 실패하면 1
  4. K3 `open_snapshot(--snapshot)`(정본 빌드, 읽기 전용)
  5. 출처 종류 확인(⑩)
  6. 자료 묶음·비교 대상 집합(⑨)
  7. 사례 다시 만들기(②). 사례가 아니면 1
  8. 흐름 조정(단위 I12)을 NAT 감싸기(단위 I13) 안에서 돌린다(③~⑥)
  9. 출력(⑪)
- 종료 코드: 0은 사례 실행이 `COMPLETED`. 1은 실행이 다른 상태로 끝남(실행 결과 기록은 남긴다), 정책·모델 설정·스냅샷을 읽지 못함, 실자료 거부, 자료 묶음이나 비교 대상 집합을 정하지 못함, 사례가 아님. 4는 흐름 밖의 조립체 출력이 기대한 모양이 아님(`WiringError`: 사례 다시 만들기의 지표·P2 출력, 흐름 조정의 반환 모양, 출력 직렬화). 흐름 안(도구 봉투 → 근거 상태 변환 등)에서 난 `WiringError`는 흐름 조정이 예외 이름만 적은 `CODE_ERROR`로 기록하므로 실행 결과 기록이 남고 1이다.
- 오류 문장에는 받은 값(스냅샷 ID·정책 이름·사례 인자)과 스냅샷 안의 값을 넣지 않는다(N13). 조립 시험이 사례 인자가 되풀이되지 않음을 본다.
- 이유: MT5 결정 기록 `20260924-2356-orchestrator-decision-mt5-cli.md`의 처리 함수 계약·종료 코드, AS1 결정 기록 `20260925-0139-model-decision-as1-detect.md` ①과 같은 모양으로 맞췄다. 실행 실패를 1로 알리되 기록은 남겨, 평가 하네스(AS3)가 종료 코드와 기록을 함께 읽을 수 있게 했다 `[DESIGN]`.

② **사례 다시 만들기** — 확정

- `--case`는 사례 식별자 `{hs6}-{partner}-{month}`다(MT1 결정 ⑩, P2 `parse_case_id`). 형식이 다르면 1이다. 합성 사례 이름(예: `A-composition`)은 CLI 형식 검사(단위 F1)는 지나지만 사례 식별자가 아니므로 1로 끝난다.
- HS6·상대국이 수집 설정 밖이거나 비교월·기준월이 수집 기간 밖이면 1이다.
- 그 계열·비교월 하나만 `detect`와 같은 길로 계산한다: AS1 어댑터(`dispatch.parent_rows`·`world_rows`) → X1·X2 → 정확값 P1 입력 행 → P1 → P2. P2가 그 `case_id`를 사례로 내지 않으면(발동 없음) 1이다. 사례 객체는 P2 출력에서 `scope`를 뗀 8필드(자료 계약 §2.3.5)다.
- AS1의 `detection_rows` 안쪽 계산을 `detection_row`(계열 하나·비교월 하나)로 뽑아 `detect`와 함께 쓴다. `detect`의 동작은 그대로다(AS1 조립 시험 통과).
- 이유: 작업 지시(K4 → K3 → X1·X2 → P1으로 발동을 다시 계산). 전체 계열을 계산하는 `detection_rows`는 부르지 않는다. 실자료를 잇게 되면 그 호출이 `real_sealed` 계열까지 계산하기 때문이다(병렬 개발 규칙 §7.2의 5).

③ **도구 자리(`ToolPort`)** — 확정

- 흐름 조정의 `Ports.tool`을 도구 I1~I5에 잇는다. 사례 실행 하나가 연 스냅샷 하나로 각 도구의 `query(snap, 요청)`을 부른다.
- 요청: {`case_id`, `snapshot_id`, `scope`(사례 네 키), `args`, `attempt`, `policy_version`, `grouping_version`}. `verify_evidence`에만 `envelopes`를 더한다(다른 도구가 받으면 도구 공통 틀이 ToolError를 낸다).
- `attempt`는 이 자리가 도구를 부른 순번(1부터)이다. 호출마다 `query_id`가 고유하다(자료 계약 §4.5). 막힌 시도는 도구에 닿지 않으므로 이 순번에 들지 않는다.
- `envelopes`는 이 자리가 흐름에 돌려준 봉투의 사본 목록이다. 흐름이 실제로 받은 봉투 원본만 넘기고, 모델 출력이나 모델에게 보인 축약본은 넘기지 않는다(MT2 보안 권고 3). 사본으로 두어 흐름 쪽에서 봉투를 고쳐도 대조 원본이 바뀌지 않는다. 조립 시험이 `verify_evidence` 요청의 `envelopes`가 trace의 앞선 봉투 넷과 같음을 본다. 마지막 봉투를 빼는 변이에서 조립 시험 넷이 실패했다 `[사실]`.
- 예산은 흐름 조정의 `unit_ports`가 이미 단위 I6에 한도 다섯 키를 모두 넘긴다(바꾸지 않았다).
- 근거 행 풀기(`resolve_rows`): 근거 ID마다 K3 `resolve`(풀림 규칙 1~4)의 행, 풀리지 않으면 null. 검증기 R3의 `rows`다.

④ **근거 상태 변환(`evidence_state`: 도구 봉투 → P3 입력)** — 확정. 봉투만 보는 순수 함수이고, 흐름 조정의 `checklist` 초안(P3 → P4)이 부른다(MT4 `unit_ports`의 `evidence_state` 훅).

- `missingness`: 모든 봉투의 항목을 근거 ID로 중복을 빼 그대로 넘긴다(키 이름을 바꾸지 않는다). 같은 근거 ID가 두 번 나오면 C형 코드 목록(`hs10_codes`)이 있는 항목을 남긴다. `ALL` 분모는 도구·K3가 중복 제거(행 규칙 5·6) 뒤에도 실제로 비는 달만 싣는다(MT1 결정 ⑫).
- `comparisons`
  - `comparability`: `check_comparability` 결과를 받았으면 `done`, 아니면 `not_performed`. 빠진 관측은 `missingness`가 1번 사유로 따로 알린다.
  - `partners`: `compare_partners` 결과마다 본다. 허용 비교국이 없으면(`no_allowed_peers`) `not_performed`. 조회한 비교국 가운데 두 달 모두 관측이나 무거래 확정(`CONFIRMED_NO_TRADE`)인 나라가 하나라도 있으면 `done`, 모두 빠진 관측이 있으면 `incomplete`다. 무거래 확정은 비교를 끝낸 것이고 결측만 미완료다(MT1 무역통계 검토 2회차 권고). 재시도할 수 있는 오류 봉투(`retryable_error`)는 받지 못한 것이다.
  - `country_and_world`: `get_history`의 V 네 개(대상국·`ALL` × 기준월·비교월)가 모두 값이 있으면 `done`, 하나라도 null이면 `incomplete`, 받지 못했으면 `not_performed`.
- `comparability_issues`: `check_comparability`의 `comparability.signals.{계열}.issues`를 그대로 옮긴다. 값은 단위 불일치와, 그 계열 값이 정의되지 않는 달(무거래·중량 0·기준월 단가 0·분모 0)이다. 점유율에는 ⑦을 더한다. MT1 결정 ⑪이 빼라고 한 "정의는 같은데 정보만 모자란 표시"(예: 개정판 미확인 `HSK`)는 이 목록에 없다. 발동한 신호는 그 값이 계산된 것이라 실자료 발동 사례에 이 문자열이 붙지 않는다 `[추론: 도구 I1 머리 설명의 issues 정의와 P1 발동 조건]`.
- 단가 블록: `U_baseline`은 `get_history`의 기준월 대상국 U, `decomposition`은 `decompose_hs`의 `within_effect`·`mix_effect`·`residual`과 `parent_child_match`(두 달 부모 대조의 금액·중량 일치가 모두 참), `children`은 `r_U@<HS10>` 지표마다 {`hs10`, `r_U`}다. 수는 모두 지표 단위의 `exact_value`(Fraction)이고 float나 표시 값을 넘기지 않는다. 분해할 수 없으면(예: C형) 세 값이 null인 객체다.
- `resolved_after_correction`: 거짓(MT2 결정 ⑪. 동결 스냅샷 하나로 도는 v1 실행에서는 만드는 쪽이 없다).
- 이유: MT2 2회차 보고 §4의 인계표, MT1 결정 ⑪·⑫·⑬.

⑤ **조기 종료는 신호 계열별** — 확정

- 단가 블록을 `get_history`·`decompose_hs` 결과 없이(null·빈 목록으로) 만드는 것은 단가 계열에 다른 1번 사유(비교월·기준월 대상국 빠진 관측, 단가 `comparability_issues`)가 있을 때뿐이다. 없으면 ValueError를 내고, 흐름 조정이 `CODE_ERROR`(실행 `FAILED`)로 기록한다. 점유율만의 사유로 단가를 null로 적지 않는다.
- 점유율 블록은 받지 못한 비교를 `not_performed`로 적는다. 점유율에 1번 사유가 없으면 P3이 입력 오류로 드러낸다(MT1 결정 ⑦).
- 시험
  - 두 신호 스냅샷의 두 사례를 `checklist`로 끝까지 돈다. 단가만 문제인 사례는 단가 `HOLD`·점유율 `MAINTAIN` → 사례 `MAINTAIN`, `unresolved_evidence` 참이다. 점유율만 문제인 사례는 단가 `MONITOR`·점유율 `HOLD` → 사례 `HOLD`다. 두 사례 모두 검증기 사유 0이다.
  - 비교 불가 봉투(점유율 사유만)를 받은 단가 사례는 흐름 조정이 `FAILED`·`CODE_ERROR`로 끝낸다(`HOLD`로 숨지 않는다).
- 이유: MT1 결정 ⑦ (나), 룰북 B1 시나리오 10, MT1 평가 검토 3회차 권고(두 방향 확인).

⑥ **C형 자료 상태 펼치기(단위 I12 수정)** — 확정

- 흐름 조정의 `_statuses_of`가 `missingness` 항목의 `hs10_codes`를 코드마다 R1 자료 상태 항목으로 펼친다: `hs10` = 코드, `status_id` = `{근거 ID}@{코드}`(코드마다 다르다), 근거 ID는 그 상태 행 하나다. 그래서 R1이 코드마다 `observation_status@<HS10>` 주장을 만든다(MT3 결정 기록 `20260925-0048-model-decision-mt3-validator.md` ⑨).
- 초안의 주장은 실제 근거 ID만 가리킨다. `_requests_of`가 C형 근거 ID를 가리킨 주장을 코드마다 요청으로 펼친다(`claim_id` `c{번호}-{k}`). `verify_evidence`에는 펼친 ID가 아니라 근거 ID가 간다(`checklist` 주장도 근거 ID 하나로 한 번 적는다).
- 코드 목록이 비면(출처 `none`) 항목을 만들지 않는다. HS6 수준 기호로 쓰면 같은 키의 값 주장과 어긋나 검증기가 막는다. 그 경우 P3의 `HOLD`는 `missingness`로 그대로 난다.
- 시험: 사례 C의 보고서에 `observation_status@8504321000`·`@8504322000` 주장 둘(`REQUEST_FAILED`)이 있고 근거는 같은 상태 행 하나다. `checklist`와 `agent` 모두 그렇다. I12 골든의 `request_sha256`은 바뀌지 않았다.

⑦ **점유율 비교 가능성: 전체국가 분모 < 대상국 금액** — 확정(이름은 잠정)

- `get_history`의 V에서 기준월·비교월 가운데 `ALL` 분모 금액이 대상국 금액보다 작은 달이 있으면 점유율 `comparability_issues`에 `denominator_below_partner:{달}`을 더한다. 같으면 문제가 아니다. 그 계열은 P3 1번으로 `HOLD`다.
- 이름 `denominator_below_partner`는 이 조립이 정했다(도구 I1의 `zero_denominator:{달}`과 같은 꼴). 계약 값이 아니다. dev20 분류 7(DT5)과 채점기(DT8)가 문자열을 보지 않고 상태(`HOLD`)만 보면 그대로 둔다.
- 이유: DT5 보고의 요청(분류 7이 `HOLD`를 기대하는데 판정 규칙에 길이 없다). 점유율이 100%를 넘는 달은 분자·분모를 같은 정의로 볼 수 없는 자료다 `[추론]`.

⑧ **반올림 불안정(`rounding_unstable`)** — 규칙 준비, 끄개 꺼짐(U4 사용자 결정 대기)

- 규칙 함수 `dispatch.rounding_unstable(v0, q0, v1, q1, δ, θ)`: 금액은 그대로, 두 달 부모 중량을 Q ± δ로 움직인 r_U 구간 [하한, 상한]을 구한다. r_U ≥ 0이면 하한 < θ, r_U < 0이면 상한 > −θ일 때 불안정이다. 경계와 같으면 안정이다. Q ≤ δ인 달이 있으면 불안정이다. δ는 정책 `tolerance.weight_rounding_kg`(`dev-0.1`은 0.5 kg), θ는 정책 단가 탐지 임계값이다. 발동한 단가 신호에만 쓰고, 값은 `get_history`의 r_U 입력(V_0·Q_0·V_1·Q_1)이다.
- 켜는 곳은 `dispatch.ROUNDING_UNSTABLE_ENABLED = False` 한 줄이다. 지금은 늘 거짓을 넘긴다.
- 도구 I1의 `comparability.rounding.unstable`(부호와 임계값 충족을 양쪽으로 보는 대칭 규칙)은 쓰지 않는다. 작업 지시의 한쪽 규칙과 다르다.
- 시험: 120 USD/12 kg → 162/12(r_U +35%, 하한 약 +24.2%)는 불안정, 사례 A(−40%, 상한 약 −39.4%)는 안정, 하한·상한이 정확히 ±θ이면 안정, 1만큼 넘으면 불안정, Q ≤ δ는 불안정. 끄개를 켜면 단가 블록이 참이 된다.

⑨ **비교 대상 집합·자료 묶음·버전 키** — 확정

- 합성 스냅샷의 `grouping_version`은 스냅샷 비교국 표(`peer_group`) 행의 값 그대로다(자료 계약 §2.3.6·§8.1, DT3 결정 ⑫). K3에 목록 함수가 없어 공개 함수 `row`로 rowid 1부터 빈 행까지 훑는다. 값이 하나가 아니면(표가 비었거나 여럿) 1이다. 실자료는 `g0`(MVP까지. 지금은 ⑩으로 쓰이지 않는다).
- 조립 시험이 사례 A·B·C마다 `compare_partners`가 `g0`로 비교국 5개를 실제로 조회함을 본다(DT3 평가 검토 권고 6: 합성 자료에서 `peers(…, "g1")`은 오류 없이 빈 목록이다).
- `dataset`: 합성 스냅샷 → 자료 묶음 표 `RUN_CASE_DATASETS`(지금 `controlled_fixture_v0` 한 줄). 표에 없는 합성 스냅샷은 1이다. dev20 스냅샷 ID가 정해지면 한 줄을 더한다.
- `rulebook_version`: 커널 K1의 `RB-1`. `code_version`: git 커밋 해시를 하위 프로세스 없이 git 메타 파일(작업 폴더의 `.git` 파일·`commondir`·`packed-refs` 포함)에서 읽는다. 읽을 수 없으면 `unknown`이다. 경로는 어디에도 쓰지 않는다(N13).

⑩ **실자료 스냅샷은 이번 PR에서 조사하지 않는다** — 잠정(AS1 결정 ⑤와 같은 이유)

- 출처 종류가 허용 목록(`controlled`)에 없으면 관측 값을 읽기 전에 거부하고 1로 끝난다(`dispatch.RUN_CASE_REFUSAL`). 조립 시험이 K3 `parent_series`·`world_series`·`children`·`peers`·`row`·`resolve` 호출 0을 본다(값은 합성이고 출처 종류만 `real`인 AS1 시험 스냅샷).
- 분할 기록 정본 위치가 사용자 승인을 받으면, 사례의 계열이 `real_dev`에 배정된 경우만 받도록 좁히는 자리가 `_run_case`의 출처 종류 확인 바로 뒤다(코드에 주석으로 표시했다. `real_sealed` 사례는 거부, 병렬 개발 규칙 §7.2의 5). 그때 비교 대상 집합은 `REAL_GROUPING_VERSION`(`g0`)이다.

⑪ **출력** — 확정

- 실행 폴더 `outputs/run_case-{시각}/` 안(자료 계약 §10.3 N5·N6·N7)
  - `runlog_trace-{시각}.jsonl`: trace(단위 L1)
  - `workflow_nat_wrap-{시각}/`: NAT 추적 `nat_trace.jsonl`과 프로파일 파일(단위 I13의 N7 폴더)
  - `runlog_run_record-{시각}.json`: 실행 결과 기록의 실행 쪽 키 21개(단위 L2)
  - `reports_render_ko-{시각}.json`: 최종 보고서(단위 R2). 실행이 `COMPLETED`일 때만(검증기를 통과하지 못한 보고서는 공유 대상이 아니다)
- 표준 출력에 위 순서로 `outputs`부터의 상대경로를 한 줄씩 적는다.
- 기록과 보고서는 trace와 같은 직렬화(`runlog.trace.dumps`)로 쓴다. Decimal을 원문 표기의 JSON 숫자로 써서 보고서 수의 끝자리 0을 지킨다(자료 계약 §9.1, 예: `3.60`). CLI 공통 `write_output`은 Decimal을 문자열로 바꾸므로 쓰지 않았다.
- 보고서 파일 이름은 작업 지시가 적은 채점기 가정 `reports_render_ko-{시각}.json`과 같다. 이 브랜치의 채점기 코드에서는 그 이름을 찾지 못해 직접 대조하지 못했다 `[미확인]`.

⑫ **`children` 어댑터(DT2 결정 ①의 남은 쪽)** — 확정

- 지표 X3의 `children` 입력은 MT2 도구 공통 틀의 `children_rows`(`src/tradesentry/tools/check_comparability.py`)가 만든다. 값이 있는 달은 HS10 행마다 행 하나, 값 행이 있는 달의 상태 행은 빠진 자료로만, 무거래 확정 달은 부모의 무거래 확정 근거를 붙인 빈 행, C형 달은 `hs10_codes`를 붙인 상태 행이다. AS2는 이 모양을 그대로 쓴다.
- 이로써 DT2 결정 ①은 `parent`·`world`(AS1 ②)와 `children`(이 항목)이 모두 확정이다. 다만 `parent`·`world` 변환이 AS1 어댑터(단위 F2)와 도구 공통 틀(단위 I1) 두 곳에 있다(AS4에 넘기는 관찰).

⑬ **실측 뒤 지침 수정(2회차, 구성 단위 I9 `model-0.3`)** — 확정(효과는 재실측으로 확인)

- 실측(오케스트레이터, 실제 NIM, `controlled_fixture_v0`·`dev-0.1`) 6회 가운데 4회가 기대와 달랐다. 원인(trace로 확인) `[사실]`
  - A `full` 첫 실행 HOLD: 조사자가 `decompose_hs`를 부르지 않고 MONITOR를 썼다. Critic이 옳게 지적했지만 재조회 인자(`hs6`·`partners`·`months`)가 도구 인자 규칙(`compare_partners`만 `partners`, 나머지 `{}`) 밖이라 버려졌다. 수정 단계의 조사자도 분해를 부르지 않고 HOLD로 바꿨다.
  - A `agent` MAINTAIN: 분해(within 0.00, mix −2.40, residual 0.00)를 받고도 MAINTAIN을 썼다. 비교국 조회는 `partners`를 문자열 `"[ALL]"`로 줘 `invalid_call`로 막혔다. 지침에 MONITOR의 수치 조건이 없었다.
  - A `freeform` INVALID(SCHEMA_INVALID): 분해를 부르지 않고 분해 값을 지어 썼다(검증기 기록만). Critic의 재조회 인자가 버려졌고, 수정 단계 답이 JSON 문법 오류(`"hs6": "850": "850450"`)로 초안 형식 검사에서 실패했다. 도구를 싣는 요청이라 `json_object` 구조화 출력이 실리지 않는 차례였다.
  - C `full` INVALID(VALIDATOR_BLOCKED): 첫 초안 HOLD는 통과했다. Critic이 HOLD 사례에 허용 밖 인자의 재조회를 요청하며 수정을 요구했고, 조사자가 Critic 문장(단가 하락)을 `hypotheses`에 옮겼다. 초안에 r_U 주장이 없어 R3 `PROSE_UNBACKED`(PT-6 '하락', `hypotheses[0]`)로 최종 차단됐다.
  - B `full`은 기대대로 MAINTAIN이었지만 첫 초안은 MONITOR였다(Critic이 바로잡음). A `full` 두 번째 실행은 분해를 부르고 MONITOR였다.
- 공통 원인: 지침에 판정 정책의 수치 조건(MT1 결정 ④·⑥·⑦을 모든 모드가 받는 공개 규칙에 싣기, MT1 결정 기록 "영향과 넘길 곳"의 MT4 항목)과 도구·재조회 인자 모양이 없었다. 판정 정책(P1~P5)과 검증기(R3·R4)의 동작은 원인이 아니다(검증기 차단은 규칙대로였다).
- 고친 것(모든 모드에 같은 글, 룰북 B2)
  - 조사자 지침: 판정 절을 P3과 같은 조건으로 바꿨다(HOLD 사유, MONITOR의 θ·U0 부등식, 비교국 비교 뒤 MAINTAIN, 비교국 자료가 모두 빠지면 HOLD). 초안 전에 `compare_partners`와(단가 발동 시) `decompose_hs`를 한 차례에 함께 부르고, 분해 없이 단가 MONITOR·MAINTAIN을 주지 않는다. 도구 인자 모양, HOLD여도 r_U·d_s 주장, 검수자 문장을 산문에 옮기지 않기를 적었다. θ는 `check_comparability`의 `comparability.rounding.threshold`(정책 단가 임계값)에서 읽게 했다(코드 변경 없음).
  - Critic 지침: 같은 판정 규칙 요약, 규칙과 근거에 맞으면 `needs_revision` 거짓, HOLD 사례에 빠진 자료 재조회를 요청하지 않기, 재조회 `args` 모양과 같은 인자 재요청 금지, 지적 문장에 숫자·증감 어휘 금지.
  - 반올림 불안정은 지침의 HOLD 사유에서 뺐다. 지금 P3에 넘기는 값이 늘 거짓(⑧)이라 `checklist`와 같은 조건으로 맞췄다. U4를 켜면 지침에도 같은 줄을 더한다.
  - `config_version` `model-0.3`. 요청 설정(temperature 1.0·top_p 0.95·`enable_thinking` 끔)은 바꾸지 않았다.
- 토큰: 지침이 길어져 비교를 두 차례로 나눠 부르는 `full` 경로의 추정이 31,402 → 31,973(한도 32,000)이 됐다. 지침이 한 차례에 부르게 하므로 그 경로는 추정 25,368이다(시험 `test_directed_single_turn_comparison_path_has_room`). 비교 뒤 수정 단계가 붙는 경로는 전처럼 한도를 넘는 남은 위험이다(MT4 결정 ⑮). 추정은 실자료 크기(HS10 8개)의 합성 봉투 기준이고, 합성 시험자료 사례는 실측 13,517~26,358이었다.
- 남은 것: 모델의 JSON 문법 오류와 판정 흔들림은 확률적이다. 효과는 사례 × 모드 반복 재실측으로 본다(보고 AS2-2 §5).

## 조립 점검 결과(조립체 3, `docs/plan/UNITS.md` §5의 1·2·5단계)

AS2는 합치거나 버린 단위가 없다. 동결 경로(판정 정책 P3~P5, 검증기 R3·R4) 단위의 코드는 고치지 않았다. 고친 단위는 F2(배선)와 I12(C형 펼치기)다. 3·4·6단계의 확정은 조립 점검 작업 AS4가 한다.

| 단계 | 결과 | 명령과 종료 코드 |
|---|---|---|
| 1. 정적 import 그래프 | `cli.dispatch` → `cli.args`, `contract.policy_load`·`types`, `dal.query`, `metrics.unit_value`·`share`·`decompose`, `policy.trigger`·`case_build`, `runlog.cause_codes`·`trace`, `workflow.model_client`·`nat_wrap`·`orchestrate`(+ 기존 `snapshot.build`·`verify`). `workflow.orchestrate` → `policy.signal_decide`·`case_aggregate`·`required_evidence`, `reports.claims`·`render_ko`, `runlog` 셋, `tools` 여섯, `validator.validate`·`gate`, `workflow.investigator`·`critic`·`model_client`·`replay`. 도구 넷 → `tools.check_comparability`(공통 틀)·`dal.query`·`metrics`. `validator.validate` → `reports.render_ko`. 모두 각 단위 머리 주석의 허용 import 안이다. `src/tradesentry` 모듈 그래프에 순환 0 `[사실: 경계 시험 도우미(tests/test_boundaries.py의 repo_modules·import_targets)로 커밋 81b9df9에서 뽑은 그래프]` | `env -u NVIDIA_API_KEY -u DATA_GO_KR_SERVICE_KEY -u TRADESENTRY_SEALED_DIR uv run --locked python -m unittest discover -s tests -p "test_boundaries.py"` → 0 |
| 2. 실행 커버리지 | `run-case`를 합성 시험자료 A·B·C × 네 모드(모델 모드는 가짜 모델)로 돌려 `sys.setprofile`로 `src/tradesentry` 함수 호출의 파일을 모았다. 네 모드 모두: X1~X4, P4, P5, I1~I7, I12, I13, R1~R4, L1, L2. `checklist`만: P3. 모델 세 모드: I10. `full`·`freeform`: I11. 불리지 않음: G1(비교국 표는 미리 계산된 `peer_group` 행을 K3로 읽는다), I8(기록 재생, 시험·골든 전용. I10~I12는 오류 형식만 import한다), L3(성공 경로에서는 상수만 쓴다. 실패 경로(키 없는 `agent` 실행 → `FAILED`·`CODE_ERROR`)에서는 불린다). I9(구성)는 모델 설정·프롬프트로 읽힌다 `[사실: scratch 스크립트, 12회 모두 종료 코드 0]` | 조립 시험 `tests/units/F2/test_run_case_command.py`(16개)·`test_run_case_evidence.py`(15개) → 0 |
| 5. 동작 불변 | 합치거나 버린 것이 없다. `detection_row` 추출 뒤 AS1 조립 시험이 그대로 통과하고, I12 골든의 `request_sha256`도 그대로다. 출력 파일 도메인명은 단위 표 글자(`runlog_trace`, `workflow_nat_wrap`, `runlog_run_record`, `reports_render_ko`)와 같다(N4, 시험이 글자로 확인) | 단위별 `env -u … uv run --locked python -m unittest discover -s tests/units/<ID> -t tests`: 조립체 3의 X1~X4·P3~P5·G1·I1~I13·R1~R4·L1~L3과 F2 모두 0, skipped 0(보고 AS2-1 §2). 전체 `env -u … uv run --locked python -m unittest discover -s tests -v` → 0(Ran 893, skipped 15. 건너뛴 것은 조립체 3 밖의 뼈대 단위 골든) |

**AS4에 넘기는 관찰**(3·4단계의 입력, 판정은 AS4)

- P4 "합침 후보(→ P3)": P4는 네 모드 모두에서 불리고(보고서 `unresolved_evidence`), P3은 `checklist`에서만 불린다. 입력도 다르다(P4는 신호별 판정만, P3은 정책·사례·근거 상태). "같은 입력" 기준을 채우지 못해 유지를 권고한다. 동결 경로라 확정은 AS4다.
- R4 "합침 후보(→ R3)": 소비자는 흐름 조정의 `unit_ports` 하나이고 늘 R3 바로 뒤에 불린다. 입력은 다르다(R3 출력 + 모드 + 수정 사용 여부). 동결 경로라 AS4가 정한다.
- I8 "합침 후보(→ I7)": `run-case`에서 불리지 않는다. 기록 재생은 골든·키 없는 시험의 전송 자리다. 버림이 아니라 시험 전용 유지나 합침을 AS4가 정한다.
- L2·L3 "합침 후보(→ L1)": L3은 실패 경로에서만 함수가 불린다. 소비자는 흐름 조정·모델 호출·실행 기록 셋이라 "소비자 하나"를 채우지 못한다.
- G1 유지: 런타임에 불리지 않지만 채점 대체 기본값 `g0` 고정 규칙이 요구한다(단위 표 비고).
- 새 합칠 후보: `parent`·`world` 변환이 AS1 어댑터(단위 F2, `resolve`로 ALL 행을 다시 만든다)와 도구 공통 틀(단위 I1, `row`로 다시 만든다) 두 곳에 있다. 사례 A·B·C와 두 신호 사례 둘, 모두 다섯 사례에서 AS1 어댑터로 만든 P1 입력의 r_U·d_s 정확값과 `get_history` 봉투 지표의 정확값이 같았다 `[사실: scratch 스크립트]`. 한 곳으로 모으는 일은 단위 변경이라 AS4·사용자 승인 대상이다.
- 실행명 확보가 세 곳(공통 실행기, CLI `reserve_run_dir`, 단위 L2 `reserve_run_dir`)에 있다. AS2는 CLI 것을 썼다.
- 계약 상수: 이 배선은 `RULEBOOK_VERSION`·`CASE_KEYS`를 커널 K1에서 가져온다. 빠진 관측 상태 셋(`GAP_STATUSES`)은 P3 머리 설명과 같은 값의 사본이다(P3 상수는 P5 모듈 안이라 조립 층에서 가져오지 않았다). AS4의 조립 부산물 4 대상이다.

## 단위 표 판정 갱신(`docs/plan/UNITS.md` §3, 조립체 3의 행)

- X1·X2·X4: AS1이 덧붙인 문구 뒤에 "AS2 점검: `run-case`에서도 불림"을 이었다.
- X3·P5·I1~I7·I9·I12·I13·R1~R3·L1: "유지"에 AS2 점검 결과(불리는 모드)를 덧붙였다.
- P3·I10·I11: 불리는 모드가 일부라는 점을 덧붙였다.
- P4·R4·I8·L2·L3: 합침 후보 판정을 그대로 두고 위 관찰(불림 여부, 기준 충족 여부, 확정은 AS4)을 덧붙였다.
- G1: "유지"에 "런타임에 불리지 않음, 고정 규칙으로 유지"를 덧붙였다.
- 판정 집계(유지 45, 합침 후보 10, 버림 후보 1, 런타임 밖 9)는 바뀌지 않는다.

## 검토한 대안

- 도구의 `run`(부를 때마다 정본 빌드를 연다)을 쓰는 안: 호출마다 스냅샷을 다시 열고, 사례 다시 만들기·검증기 행 풀기와 다른 연결을 쓰게 된다. 한 연결로 `query`를 부르는 쪽을 골랐다.
- 근거 상태 변환을 흐름 조정(단위 I12) 안에 두는 안: I12의 허용 import에 지표 단위(`metrics`)가 없다. 정확값 함수가 필요해 조립 층(F2)에 두고 훅으로 넘겼다(MT4가 만든 `evidence_state` 훅 그대로).
- `rounding_unstable`에 도구 I1의 `rounding.unstable`을 옮기는 안(MT2 인계표): 작업 지시의 한쪽 규칙과 다르고 U4 결정 전이다. 버렸다(⑧).
- 비교국 비교를 "조회한 비교국의 두 달 자료가 모두 빠졌을 때만 `incomplete`"로 읽는 안: 한 달만 빠진 비교국은 r_U·d_s가 없어 비교 결과가 아니다. 두 달 모두 결과가 있는 나라가 하나도 없으면 `incomplete`로 읽었다(④).
- 새 모듈 파일(예: `cli/run_case.py`)에 배선을 두는 안: 단위 표에 없는 파일(단위 추가, 사용자 승인)이 된다. F2 안에 두었다.
- 실행 실패를 0으로 끝내고 기록만 남기는 안: CLI를 부른 사람이 실패를 놓친다. 1로 알리고 기록은 남긴다(①).
- `code_version`을 `git rev-parse`로 얻는 안: CLI에 하위 프로세스를 들인다(MT5a 보안 권고 5). 파일로 읽었다.

## 영향과 넘길 곳

- 바꾼 파일
  - `src/tradesentry/cli/dispatch.py`: `run-case` 배선, 머리 설명의 "사례 조사 명령 run-case" 절, `detection_row` 추출
  - `src/tradesentry/workflow/orchestrate.py`: C형 펼치기(⑥)
  - `tests/units/F2/`: `run_case_fixture.py`, `test_run_case_command.py`, `test_run_case_evidence.py`
  - `tests/units/I12/test_orchestrate.py`: `CTypeStatusTest`
  - `docs/plan/UNITS.md` 판정 칸
- AS3(평가 실행·채점 연결)
  - 보고서 파일 이름은 작업 지시가 적은 채점기 가정 `reports_render_ko-{시각}.json`과 같다(이 브랜치의 채점기 코드로는 대조하지 못했다). 실행 결과 기록은 `runlog_run_record-{시각}.json`이다.
  - 실행이 `COMPLETED`가 아니면 종료 코드가 1이고 보고서 파일이 없다(기록은 있다).
  - 사례 실행 폴더를 묶음 폴더와 잇는 방법(자문 명세서 Q9)은 정하지 않았다.
- 2026-09-25(금) 09:00 사용자 결정
  - U4: 켜기로 하면 `ROUNDING_UNSTABLE_ENABLED`를 참으로 바꾼다(한 줄, 시험 있음).
  - 원인 분류 코드 이름·`tool_attempts` 뜻(MT4 ①·③): 이 배선은 이름을 쓰지 않는다. 시험은 `cause_codes` 상수로 단언하고 `tool_attempts`는 막힌 시도가 없는 경로라 두 뜻의 값이 같다.
- AS1 두 번째 PR·분할 기록 정본 위치 승인: ⑩의 좁히는 자리. `run-case`도 `real_dev` 사례만 받는다.
- DT1(K3): 비교국 표의 `grouping_version` 목록을 주는 함수가 있으면 rowid 훑기(⑨)를 바꾼다(요청 후보).
- DT5·DT8: 분류 7의 점유율 사유 문자열(⑦)은 이 조립이 정한 이름이다. 정답표·채점기가 문자열을 보면 맞춘다.
- DT5(dev20): dev20 스냅샷 ID가 정해지면 `RUN_CASE_DATASETS`에 한 줄을 더한다.
- MT5(샌드박스): 샌드박스 안의 설치에는 `.git`이 없을 수 있어 `code_version`이 `unknown`이 된다. 샌드박스 밖 실행기가 커밋 해시를 넘길 수단은 MT5·MT7이 정한다 `[미확인]`.
- 모델 모드 실측: 실제 NIM으로 `run-case`를 돌리는 명령은 AS2 보고 AS2-1의 "오케스트레이터가 돌릴 명령"에 적었다.
