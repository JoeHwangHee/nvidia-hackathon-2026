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
| 결정 | 아래 "결정 내용" ①~⑫. ⑬은 2회차(실제 NIM 실측 6회 뒤, 같은 날 06:3x), ⑭는 3회차(실측 27회 뒤, 07:0x), ⑮는 4회차(실측 20회 뒤, 07:2x), ⑯은 5회차(07:4x), ⑰은 6회차(08:0x, 오케스트레이터 판단), ⑱은 7회차(08:3x), ⑲는 8회차(09:0x), ⑳은 9회차(검토 반영, 09:3x), ㉑은 10회차(마지막 조정, 10:0x), ㉒는 병합 준비(사용자 결정 반영)에, ㉓은 12회차(실자료 `real_dev` 실측 뒤, 오케스트레이터 판단, 브랜치 `model/AS2-prompt-numbers`)에, ㉔는 13회차(2026-09-25(금) 14:17 사용자 결정 반영, 같은 브랜치)에 더했다 |
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

⑭ **분해 보기의 판정 보조 값과 필수 근거 보기 압축(3회차, 단위 I10·구성 I9 `model-0.4`)** — 확정(효과는 재실측으로 확인)

- 실측 27회(`model-0.3`)에서 B는 완료 때마다 MAINTAIN, C는 HOLD였다. A는 완료 6회가 모두 MAINTAIN이었다(기대 MONITOR).
- A 완료 6회의 trace 봉투를 `evidence_state` → P3에 넣어 보았다 `[사실: scratch]`.
  - 분해·비교국을 받은 4회: P3은 MONITOR(`composition_explained`)다. 모델은 설명문에 "구성효과로 설명"이라 쓰고도 MAINTAIN을 냈다.
  - 분해를 부르지 않은 2회: 근거 상태를 만들 수 없다(분해 없이 결론).
- 원인
  - 분해 값은 USD/kg이고 기준 θ는 %라, 모델이 지침의 θ×U0/100 부등식을 적용하지 못했다 `[추론: 네 번 모두 같은 근거에서 같은 오판]`.
  - U0는 `get_history` 봉투에만 있었다.
- 고친 것(모든 모드와 Critic에 같은 보기·글, 룰북 B2)
  - 조사자 보기(`compact_envelope`)의 `decompose_hs` 봉투에 `rule_view`를 더한다. 값은 U0, within_effect·residual·그 합의 U0 대비 %, 하위품목 |r_U@|의 최대(%)다. 모두 X3 정확값에서 계산해 소수 2자리로 사사오입하고, 값이 없으면 null이다. 단위 I10의 허용 import에 `tradesentry.metrics`를 더했다.
  - 지침의 규칙을 "rule_view 네 값의 절댓값이 모두 θ보다 작으면 비교국 결과와 관계없이 MONITOR"로 바꾸고 수치 예를 더했다. θ는 `comparability.rounding.threshold`다. P3의 부등식과 같은 조건이다(|x|×100 < θ×U0 ⇔ |x/U0×100| < θ).
  - 경계에서 표시 값(소수 2자리)이 판정을 뒤집을 수 있다(예: 정확값 29.996%가 30.00으로 보임). 최종 판정은 모델 몫이라 이 차이는 모델 모드의 남은 위험으로 둔다.
  - 필수 근거 보기(`case_message`)를 계열별 {"판정/판정 근거": [코드]}로 줄였다. 코드 설명과 주장 기호 목록을 뺐고, 실측 사례에서 약 1,700자가 670자가 됐다. 조사자 요청마다 줄어든다.
- 토큰(실자료 크기 합성 봉투 추정)
  - 지침대로 비교를 한 차례에 부르는 경로는 25,627이다.
  - 모델이 두 차례로 나눠 부르는 경로는 32,301로 한도(32,000)를 넘는다. 실측 27회에서 모델은 대부분 나눠 불렀다. 합성 시험자료 사례의 실측은 한도에 닿은 8회가 모두 수정 단계가 붙은 경로였다.
  - 한도는 2026-09-25(금) 09:00 사용자 결정 대상이라 바꾸지 않았다.
- 판단 대상(바꾸지 않음)
  - 모델 모드에서도 코드가 기본 경로에 `decompose_hs`·`compare_partners`를 부르는 흐름 변경(개발 플랜 §6.6 변경). 모델이 분해를 건너뛰는 일(27회 가운데 A에서 2회)과 나눠 부르는 토큰 비용을 함께 없애지만, 조사자의 추가 비교가 0회가 된다.

⑮ **상태 뜻 표와 필수 조회(4회차, 단위 I10·I12·F2·구성 I9 `model-0.5`)** — 확정(효과는 재실측으로 확인)

- 실측(오케스트레이터)
  - `model-0.4` 11회: A는 MAINTAIN 5, MONITOR 1, SCHEMA_INVALID 3이었다. B는 MAINTAIN, C는 HOLD로 맞았다.
  - temperature 0.3 실험(설정은 되돌림) 9회: 완료 7회가 모두 MAINTAIN이었다.
  - 무작위가 아니다. 결정적 단서는 A full의 narrative "구성효과로 설명 가능한 범위 내 변화여서 검토 유지가 적절하다"다. 모델이 MAINTAIN(검토 유지)을 "설명되니 현상 유지"로, 곧 MONITOR와 뒤바꿔 읽는다.
- SCHEMA_INVALID 3회의 원인 `[사실: trace]`
  - A full(`run_case-260925064619`)
    - 조사자가 도구를 부르지 않았고, 첫 초안에서 필수 근거 코드 `missingness_listed`를 근거 ID로 썼다(초안 형식 문제).
    - 수정 초안은 HOLD였다. 주장이 부모 행의 `OBSERVED` 자료 상태 하나뿐이라, 최종 검사에서 R3 `SCHEMA_SIGNAL_CLAIM`(발동 신호 계열 주장 없음)과 `PROSE_UNBACKED`에 막혔다.
    - 두 요청 모두 도구를 싣는 차례라 `json_object`가 실리지 않았다.
  - A freeform 1회차(`…064535`): 수정 단계 답에 JSON 문법 오류(`"signal_status", "signal_status": …`)가 있었다. 도구를 싣는 요청이었다.
  - A freeform 3회차(`…064712`)
    - 조사자가 `compare_partners`만 두 번 부르고 분해는 부르지 않았다.
    - 도구 없는 초안 요청(`json_object` 켬)의 답이 `max_tokens` 2048에서 잘렸다(글 5,245자, 12필드 주장 다수). 수정 단계도 같았다.
- 도구 없이 결론: A agent(`…065128`, 온도 0.3)는 요청 1회로 도구 없이 MAINTAIN을 냈다.
- 고친 것(모든 모드에 같은 글·동작, 룰북 B2)
  - 조사자·Critic 지침
    - 세 상태의 뜻 표를 넣었다: MONITOR = 설명됨·지켜봄, MAINTAIN = 필수 비교 뒤 설명 안 됨·충돌·계속 검토, HOLD = 자료 부족.
    - "MAINTAIN은 설명되니 유지가 아니다"와 narrative·상태 일치 규칙을 넣었다.
    - 초안 형식 줄과 초안 요청 메시지(단위 I10 `DRAFT_REQUEST`)에도 상태 값의 뜻을 적었다.
    - Critic의 첫 점검을 "상태와 narrative·근거가 뒤바뀌었는지(status_conflict)"로 했다.
  - 필수 근거 보기(단위 I10) 머리에 "판정별로 보여야 할 근거의 종류이지 주장·근거 ID가 아니다"를 적었다.
  - `freeform` 주장은 8개 이하로 했다(잘림 방지. `max_tokens`는 모델 설정이라 바꾸지 않았다).
  - 필수 조회(단위 I12 `Ports.required_tools`, 조립이 넘긴다. 없으면 강제하지 않는다. MT4 단위 시험과 I12 골든은 그대로다)
    - 도구를 주는 조사자 차례에 필수 도구의 결과 없이 쓴 초안은 받지 않고, 차례마다 한 번 필수 조회 메시지(`REQUIRED_TOOLS_REQUEST`)로 돌려보낸다.
    - 두 번째 초안은 받는다(모델 요청 한도와 흐름을 넘지 않게). trace에는 `state_change` `draft_refused`(`missing_tools`)로 남는다.
    - 조립(F2 `required_tools`)은 발동 신호가 있으면 `compare_partners`, 단가 발동이면 `decompose_hs`를 넘긴다(공개 판정 규칙이 쓰는 비교).
    - 흐름 설계(개발 플랜 §6.6: 조사자가 비교를 고른다)는 그대로다. 코드는 결론 전에 필요한 조회를 했는지만 강제한다(예산·조기 종료를 코드가 강제하는 것과 같은 방식).
- 남은 것
  - 도구를 싣는 요청의 JSON 문법 오류는 구조화 출력으로 막을 수 없다(MT4 결정 ⑯의 설계).
  - 돌려보내기는 요청 1회를 더 쓴다. 토큰 한도는 09:00 결정 대상이다.

⑯ **상태 값 뜻 풀이 제거와 지침 압축(5회차, 구성 I9·단위 I10 `model-0.6`)** — 확정. ⑮의 초안 형식·초안 요청 메시지 부분을 대체한다

- ⑮의 퇴행(오케스트레이터 실측): 한도를 128,000으로 올린 실험 11회 가운데 9회가 SCHEMA_INVALID였다.
  - 원인은 모델이 `review_status`에 `"MAINTAIN(설명 안 됨·계속 검토)"`처럼, ⑮가 초안 형식 줄에 넣은 뜻 풀이까지 값으로 적은 것이다.
  - 한도 32,000으로는 BUDGET_TOKENS가 11회 가운데 8회였다.
- 완료된 A 2회도 MAINTAIN이었다 `[사실: trace]`. 두 번 모두 받은 분해는 within 0.00·residual 0.00이었다.
  - `run_case-260925070427`(agent): narrative가 "구성 변화로 설명되지 않으며, 비교국 대비 특이하게 크게 변동"이다.
  - `…070517`(full): 돌려보내기 뒤 분해를 받았다. narrative는 "하위 품목 간 무게 이동으로 설명되나 비교국과의 차이는 설명되지 않는다"다.
  - 뜻 표를 읽고도 비교국과 다른 변화를 "설명되지 않음"으로 읽었다.
- 고친 것(모든 모드 같은 글)
  - 초안 형식 줄과 초안 요청 메시지(단위 I10 `DRAFT_REQUEST`)의 상태 값을 `MAINTAIN|MONITOR|HOLD` 글자만으로 되돌렸다. 시험이 이를 고정한다.
  - 뜻 표는 지침 본문에만 두고 한 문단으로 줄였다.
  - "대상국 변화가 비교국과 달라도 구성효과로 설명되면 MONITOR, 비교국과의 차이는 설명되지 않음의 근거가 아니다"를 조사자·Critic 지침에 넣었다(P3도 비교국 결과의 내용을 판정에 쓰지 않는다).
  - 필수 조회(⑮)는 그대로 둔다. 초안 파서는 느슨하게 하지 않았다.

⑰ **모델 모드의 규칙 참고값(6회차, 단위 I10·I11·I12·구성 I9 `model-0.7`)** — 오케스트레이터 판단, 확정

- 배경: 5회차(`model-0.6`)를 한도 128,000으로 실측했다(오케스트레이터).
  - A MONITOR는 9회 가운데 2회였다.
  - B는 MONITOR로 떨어졌다(퇴행, 기대 MAINTAIN).
  - 지침 문장 조정만으로는 한 사례를 올리면 다른 사례가 흔들렸다.
- 판단 근거: MT1 결정 기록 `20260925-0025-model-decision-mt1-policy.md` ⑬(확정)은 "다른 모드에서 P3 판정을 어떻게 쓸지(모델 상태와 나란히 적는 참고값 등)는 흐름 조정(I12)과 검증기가 정한다. P3은 모델의 상태를 고쳐 쓰지 않는다"고 적었다. 그 범위 안에서 모델 모드(agent·full·freeform)의 조사자와 Critic에게 코드가 계산한 P3 신호별 판정을 참고값으로 보인다.
- 동작
  - 계산: `Ports.reference_status`(봉투 목록 → P3 출력)는 `unit_ports`가 근거 상태 변환(`evidence_state`, ④)과 정책을 받을 때만 만든다. 그래서 `run-case` 배선(AS2)에서만 켜지고, MT4 단위 시험과 I12 골든은 그대로다.
  - 시점: 필수 도구(⑮) 결과를 모두 받은 뒤의 첫 조사자 요청 앞에 한 번 싣는다. 도구를 더 줄 수 없는 차례(비교 불가·몫 소진)나 필수 조회를 한 번 돌려보낸 뒤라면 그 요청 앞에 싣는다. 모든 모델 모드에 같은 시점·같은 문구다(룰북 B2).
  - 문구(단위 I10): "[규칙 계산 결과(참고값)] 공개 판정 규칙을 지금까지 받은 근거에 코드로 적용한 결과다: 단가 신호(unit_value) = MONITOR(구성효과로 설명됨). 이 값과 다르게 판정하려면 narrative에 그 반대 근거를 적는다."
  - P3을 돌릴 수 없으면(필수 근거 없음) "규칙 계산 불가: 판정에 필요한 근거가 없다(받지 못한 도구: …). 받은 근거로 판정하고, 모자라면 HOLD다"를 싣는다.
  - Critic: 같은 문구를 Critic 요청의 근거 뒤에 싣고, 지침은 "초안 상태가 참고값과 다른데 반대 근거가 없으면 status_conflict"로 점검하게 했다.
  - 기록: trace `state_change` 이벤트, `phase` = `rule_reference`, 데이터는 {`available`, `signal_status`, `basis`, `error`(예외 이름)}다. 새 이벤트 종류는 만들지 않았다(단위 L1 이벤트 표 그대로).
  - 보고서 스키마와 실행 결과 기록 키는 바꾸지 않았다(자료 계약 §3.3·§6·§8). 코드는 모델의 상태를 덮어쓰지 않는다. 최종 상태는 여전히 모델 초안이고, 검증기 R3가 허용 상태 조합을 본다.
- 지침: 판정 절을 참고값 설명과 규칙 요약 한 줄로 줄였다(`rule_view` 부등식 풀이·수치 예·분해 없이 판정 금지 문장을 뺐다). 상태 뜻과 일치 규칙은 짧게 남겼다. 조사자 지침은 5,917 → 5,418바이트다.
- **평가 해석상의 의미**(결과 요약에 적어야 한다)
  - `model-0.7`부터 모델 모드의 판정은 모델이 규칙 참고값(코드가 계산한 P3 판정)을 보고 정한다. 모델 모드와 `checklist`의 판정 일치는 "모델이 규칙을 스스로 적용한 정도"가 아니라 "참고값을 따르거나 반대 근거로 벗어난 정도"로 읽어야 한다.
  - 모델 모드의 몫은 도구 선택, 주장·설명문 작성, 반대 근거 판단이다. 이 점을 평가 결과 요약(로드맵 R1, 룰북 B7 요약)과 제출서 주장 문구에 적는다. 공용 약속(제출서 주장 문구)과 닿으므로 오케스트레이터가 사용자에게 알린다.
- 시험
  - I12 `RuleReferenceTest` 4개: 세 모델 모드에 같은 문구가 분해를 받은 뒤 두 번째 조사자 요청 앞에 한 번 실린다. P3은 한 번 계산하고, Critic 요청에도 같은 글이 가며, 모델 상태는 그대로다. 계산 불가 문구와 받지 못한 도구를 확인하고, checklist에는 참고값이 없음을 확인한다.
  - F2 조립 시험: 사례 A·B·C `full`의 참고값이 checklist 판정과 같다.

⑱ **계산 불가 참고값 재계산, 초안은 도구 없는 차례에서만, `max_tokens` 4096(7회차, 단위 I12·F2·구성 I9 `model-0.8`)** — 확정. 뒤의 둘은 오케스트레이터 허락

- 실측(오케스트레이터, 한도 128K 조건 18회, `model-0.7`): 맞은 사례는 A 1/6, B 1/6, C 5/6이다.
- B 참고값이 계산 불가였던 원인 `[사실: trace run_case-260925072735·-072811]`
  - 조사자가 비교 몫 2회를 `compare_partners`에 썼다. 한 번은 잘못된 인자(빈 목록·허용 밖 국가)였고, 한 번은 같은 차례 중복 호출이었다.
  - 그래서 도구를 더 줄 수 없는 차례에 분해 없이 참고값을 계산했다. 근거 상태 변환이 계열별 조기 종료 규칙(⑤)대로 ValueError를 냈고, "계산 불가"를 한 번 싣고 끝났다.
  - 분해는 수정 단계 재조회에서 받았지만 참고값을 다시 싣지 않았다.
  - 조립 시험(가짜 모델)은 분해·비교국을 한 차례에 받으므로 이 경로를 타지 않았다.
- 고친 것
  - 참고값이 계산 불가였으면, 필수 도구 결과가 갖춰진 뒤(수정 단계 재조회 포함) 다시 계산해 싣는다. trace `rule_reference`에 `error_detail`(예외 문장. 근거 상태·P3의 문장은 키 이름만 담고 값은 없다, 300자까지)을 더했다.
  - 초안은 도구 없는 차례에서만 받는다(`Ports.drafts_only_without_tools`, F2가 켠다. MT4 단위 시험과 I12 골든은 그대로다).
    - 도구를 준 차례에 도구 호출 없이 온 초안 본문은 버린다. trace에는 `state_change` `draft_discarded`로 남는다.
    - 곧바로 도구 없는 초안 요청(초안 요청 메시지, 구조화 출력 `json_object`)으로 다시 받는다. 모든 모드 같다.
    - SCHEMA_INVALID 6/18 가운데 대부분이 도구를 준 차례(`json_object`가 실리지 않는 차례)의 본문이었다.
  - `max_tokens` 2048 → 4096(모델 설정의 조정값. MT4 결정 기록 `20260925-0125-model-decision-mt4-workflow.md` ⑪의 값을 이 기록이 대체한다). 수정 단계 초안이 2048에서 잘린 실측(`run_case-260925073047`)에 따른 것이다. 모든 모드 같다. temperature·top_p는 그대로다.
- 비용: 버린 초안만큼 모델 요청이 1회 늘 수 있다. 토큰 한도는 사용자 결정 대상이다.

⑲ **필수 결과가 빠진 도구 차례만 `tool_choice` required, 코드 지적 뒤 수정 1회(8회차, 단위 I7·I10·I12·구성 I9 `model-0.9`)** — 오케스트레이터 지시, 확정

- 실측(오케스트레이터, 한도 128K 조건 18회, `model-0.8`): 기대 일치는 11/18이었다. SCHEMA_INVALID와 잘림은 0이다.
  - 참고값이 끝내 있던 13회 가운데 완료 11회는 10회가 참고값과 같았다.
  - 참고값이 없던 5회는 1회만 맞았다. 남은 실패 대부분은 필수 도구 결과 누락이다.
  - 누락 경로: 도구 차례에 초안만 냄(모델 요청 10회 소진 포함), `compare_partners` `{"partners": []}`(`invalid_args`)로 비교 몫 소진, Critic 재조회 요청을 수정 단계에서 부르지 않음.
- 탐침 사실(커밋하지 않은 오케스트레이터 탐침, 결과 파일 `scratchpad/mt4/toolchoice_probe_out.txt`. 조건: 2026-09-25(금), 모델 `nvidia/nemotron-3-super-120b-a12b`, 엔드포인트 `https://integrate.api.nvidia.com/v1/chat/completions`, 도구 2개(`compare_partners`·`decompose_hs`)를 싣고 `max_tokens` 400, `tool_choice` 값마다 2회) `[사실]`
  - NIM(이 모델·엔드포인트)은 `tool_choice` `"auto"`·`"required"`·이름 지정 함수·`"none"`을 모두 HTTP 200으로 받았다.
  - `"required"`는 두 번 모두 도구 호출(`finish_reason` `tool_calls`, 본문 없음)을 냈다.
- 고친 것(모든 모드 같음. 조립이 `drafts_only_without_tools`·`required_tools`를 켠 run-case에서만 작동하고, MT4 단위 시험과 I12 골든의 흐름은 그대로다)
  1. **차례 규칙**(단위 I12)
     - 흐름이 도구 호출을 기대하는 차례(기본 단계 비교, 수정 단계 재조회)에서, 필수 결과가 빠졌고 그 차례에 예산이 있을 때만 도구 차례다. 필수 결과는 필수 도구의 결과와, 수정 단계라면 Critic이 재조회를 요청했는데 그 단계에서 아직 부르지 않은 도구다.
     - 도구 차례에는 도구 목록을 전부 주고 `tool_choice` `"required"`를 싣는다. 이름 지정은 하지 않는다(코드가 도구를 고르면 checklist 방식이 된다, 룰북 B2). 알림 한 줄 "[필수 조회] 아직 없는 필수 결과: …. 이 차례에는 도구를 부른다."를 붙인다.
     - 둘 가운데 하나라도 아니면 곧바로 도구 없는 초안 차례다(초안 요청 메시지 + `json_object`).
     - trace `model_request`에 `tool_choice`를 남긴다(도구를 실은 요청만). 도구 차례에 온 초안 본문은 ⑱대로 버린다(`draft_discarded`). ⑮의 필수 조회 돌려보내기는 이 규칙이 켜지면 쓰지 않는다.
  2. **코드 지적**: `full`·`freeform`은 Critic 뒤, `agent`는 첫 검증 뒤에 판단한다.
     - 필수 결과가 빠졌고 재조회 예산이 있으면, 빠진 도구 목록을 코드 지적(`code_finding`, Critic 지적과 같은 모양)으로 Critic 결과나 수정 지시에 덧붙이고 수정 1회로 간다. trace는 `state_change` `code_finding`이다.
     - 필수 결과가 빠진 초안도 Critic을 거친다(시험으로 확인).
     - 최초 초안이 스키마 검사에서 실패하면 Critic을 건너뛰는 규칙(개발 플랜 §6.6 한도 표)은 그대로다. 오케스트레이터가 예로 든 `run_case-260925074402`의 Critic 생략은 필수 결과 누락 때문이 아니다. 첫 초안의 `SCHEMA_SIGNAL_CLAIM`(보고서 스키마 실패) 때문이었다 `[사실: trace]`.
  3. `invalid_args` 거부가 비교 몫을 쓰는 규칙은 바꾸지 않았다(2026-09-25(금) 09:00 사용자 결정 6과 맞닿음). 대신 모델에게 주는 `compare_partners` 설명과 인자 스키마를 바꿨다: "partners는 허용 비교국 1~5개, 생략하면 전부, 빈 목록 금지", `minItems` 1.
  4. 지침: 증감 어휘는 인용한 지표 주장(direction, 주장 text)에만 두고 narrative·가설에는 쓰지 않는다. 검증기는 바꾸지 않았다.
- `config_version` `model-0.9`. 단위 I7의 `chat`·`build_payload`에 `tool_choice`(`auto`|`required`)를 더했다.
- 시험
  - I12 3개
    - required는 결과가 없고 예산이 있을 때만 실린다. 결과를 받은 뒤는 도구 없는 초안 차례이고, 요청은 2회다.
    - 비교 몫이 0이면 곧바로 초안 차례로 간다. 수정 단계는 required다.
    - 세 모드에서 required 차례의 초안을 버리고, Critic을 거쳐 코드 지적 뒤 수정한다.
  - F2 조립 2개
    - A agent에서 required → 초안 차례로 모델 요청 2회이고, 버린 초안이 없다.
    - A full에서 필수 결과가 없는 초안이 Critic을 거쳐 수정 단계에서 도구를 부르고 MONITOR가 된다.

⑳ **검토 반영(9회차, 단위 I10·I12·F1·F3·구성 I9 `model-1.0`)** — 확정. 무역통계 검토 막음 1, 평가 방법론·NVIDIA+보안 권고와 8회차 실측(한도 128K, 참고값 18/18, 일치 12/18, INVALID 3: A agent·full의 narrative "변동이 없"·"늘어"(PT-6)·구성 비중 "50.0%"·"80.0%"(PT-1) 뒷받침 없음, A freeform 수정 초안 `max_tokens` 4096 잘림)

1. **지침이 판정 정책을 틀리게 설명하던 곳**(무역 막음 1). ⑰에서 규칙을 줄이며 빠졌다(조사자·Critic, 모든 모드 같은 글).
   - MONITOR의 뜻을 "단가 변화가 하위품목 구성효과로 설명됨(단가 신호만)"으로 적었다. "등"을 뺐다.
   - "다른 상대국의 동반 변화, 분모 축소, 비교국과의 차이는 상태를 바꾸는 근거가 아니다(반대 근거로 쓰지 않는다). 자료가 모자라면 MAINTAIN을 주지 않는다"를 되살렸다(개발 플랜 §6.3).
   - 참고값에서 벗어나는 조건을 "도구 결과에 있는 사실 가운데 규칙이 보지 않는 것"으로 좁혔다. 위 셋은 반대 근거가 될 수 없다.
   - 규칙 요약에 두 HOLD 사유를 더했다: 비교 미완료, 점유율 분모(ALL)가 대상국 금액보다 작은 달. θ 경계 근처는 참고값을 따른다(`rule_view` 소수 2자리 표시의 경계 문제, 무 권고 5·6).
   - Critic 대안 설명 줄에 "분모 변화와 여러 상대국에 공통인 변화, 이 둘은 상태를 낮추는 근거가 아니다"를 덧붙였다.
2. **산문 금지 표현**: 검증기(단위 R3) 산문 패턴(룰북 B3-2)의 원천 목록을 지침에 옮겼다.
   - PT-6 증감·무변동 어휘는 `validator/validate.py`의 `UP_WORDS`·`DOWN_WORDS`·`FLAT_WORDS` 글자 그대로 옮겼다. 시험 `ProsePatternListTest`가 대조한다.
   - PT-1~PT-5 숫자와 PT-8 "X에서 Y로"도 적었다.
   - narrative·가설에는 쓰지 않는다. 구성 비중 변화는 %로 쓰지 말고 `mix_effect`·`w@` 지표 주장을 인용한다. 검증기는 바꾸지 않았다.
3. **`max_tokens` 8192**(모든 모드 같음. ⑱의 4096을 대체): `freeform` 수정 초안이 4096에서 잘렸다. 누적 토큰 한도(`limits.tokens`)는 사용자 결정 4를 기다리며 32,000 그대로다.
4. **참고값 재계산과 예외 범위**
   - 수정 단계에서 새 조회 봉투(`verify_evidence` 제외)를 받은 뒤 참고값을 다시 계산해 싣는다(평 권고 9, 세 모드 공통). 계산할 때마다 trace `rule_reference`를 남긴다.
   - 참고값 계산은 P3·근거 상태 변환의 입력 검사 오류(`ValueError`)만 "계산 불가"로 두고, 배선 오류(`WiringError`·`KeyError` 등)는 흐름의 `CODE_ERROR`로 올린다(보 권고 2).
5. **런타임 스킬 맞춤**(보 권고 1, 무 권고 8). `skills/tradesentry/SKILL.md`(단위 F3, MT5 소유)를 조립 작업의 맞춤으로 고쳤다.
   - run-case 표준 출력의 네 줄(trace, NAT 폴더, 실행 결과 기록, `COMPLETED`일 때 보고서 `reports_render_ko-{시각}.json`) 가운데 실행 결과 기록과 보고서만 읽는다.
   - 운영자에게 보일 값을 정했다.
   - 종료 코드 1일 때는 실행 결과 기록의 `execution_status`와 `errors` 코드를 전한다.
   - 사례 예시를 `850450-XA-202412`로 바꿨다. 합성 사례도 `{hs6}-{partner}-{month}` 꼴이다. CLI `--case` 도움말(단위 F1)에도 같은 안내를 적었다.
6. **시험**
   - F2
     - 가짜 모델이 참고값과 다른 상태를 내는 경우(agent·full·freeform): 최종 기록이 모델 상태 그대로다(허용 상태 조합이라 검증기가 막지 않는다).
     - 버린 초안·required 차례가 모델 요청 수(보낸 요청 수)와 토큰 합에 드는지 단언한다.
     - C형 `hs10_codes`가 비었을 때 checklist HOLD 보고서가 검증기에 막히지 않는다.
   - I12
     - directed 흐름에서 full·freeform의 "첫 초안 스키마 실패 + 필수 결과 없음"은 Critic 요청 0, 수정 첫 요청 required다.
     - `drafts_only`를 켠 세 모드의 이벤트 순서가 같다.
     - 수정 뒤 참고값을 다시 계산한다.
     - 참고값 배선 오류는 `CODE_ERROR`다.
   - I10 `ProsePatternListTest`.
- 조립을 위해 `origin/main`(acd4240, MT5 두 번째 PR #35)을 병합했다(런타임 스킬 파일이 main에만 있었다).
- 기록 한 줄씩(무 권고 2·3·4)
  - 분모 경로: 점유율 `denominator_below_partner`는 MT1 결정 ⑪("빠진 달·분모·하위자료는 missingness·decomposition으로")의 예외다. 결측이 아니라 `missingness`로 표현할 수 없어 `comparability_issues`에 넣는다. P3 머리 설명은 AS4에서 맞춘다. dev20 분류 7의 "국가 집합 변경" 절반은 이 검사로 잡히지 않는다(DT5 확인 요청).
  - `parent_child_match`: 부모 대조의 `V_match`·`Q_match`가 null(대조 불가, 예: C형)이면 거짓으로 옮긴다. 그래서 P3 gaps에 "불일치"가 함께 적히지만 판정(HOLD)은 같다.
  - 도구 I1의 `no_trade`·`zero_weight`·`zero_baseline`·`zero_denominator`를 `comparability_issues`로 넘기는 것은 발동한 계열에서는 생기지 않는다(그 계열의 값이 계산돼 발동했으므로).

㉑ **계산 불가 안내, 도구 차례 `max_tokens`, 막힌 산문 수정 지시(10회차, 마지막 조정. 단위 I7·I10·F1·구성 I9 `model-1.1`)** — 확정. 이 뒤로는 실측 결과를 보고 지침을 더 조정하지 않는다(오케스트레이터)

- 9회차 실측(한도 128K, 18회) `[사실: trace]`
  - 기대 일치 8/18이었다.
  - 실패 내역
    - VALIDATOR_BLOCKED 4회: PROSE_UNBACKED `0.0%`·`0.9%`·`증가`·`하락`. 수정 초안에도 같은 표현이 남았다.
    - SCHEMA_INVALID 2회
    - PROVIDER_REQUEST_TIMEOUT 1회
  - `run_case-260925082849`(B agent)
    - 조사자가 허용 목록 밖 국가로 `compare_partners`를 불러 거부됐다.
    - 수정 단계의 `required` 차례 응답이 공백 반복 8,192토큰으로 잘렸다(`finish_reason` `length`, 도구 호출 없음).
    - 참고값이 끝까지 계산 불가였고, 모델이 "모자라면 HOLD다" 안내대로 HOLD를 내 `COMPLETED`/HOLD로 끝났다(기대 MAINTAIN).
1. **계산 불가 안내**(무역 재검토 막음)
   - 필수 조회 결과가 없어서 참고값을 계산하지 못한 경우, 이제 HOLD로 이끌지 않고 빠진 필수 조회를 알린다. 문구: "필수 조회 결과를 아직 받지 않았다(받지 못한 도구: …). 이것은 자료 부족이 아니다. 허용된 인자로 그 도구를 부른다(compare_partners는 인자 없이 부르면 허용 비교국 전부). 자료 부족(HOLD)은 조회한 자료가 비었을 때만이다."
   - 개발 플랜 §6.3의 HOLD는 "필요한 자료가 없어 검증이 불가능"할 때이고, 결정 ⑦과 P3은 흐름의 누락이 그럴듯한 HOLD로 숨지 않게 정했다.
   - 오케스트레이터 판단: 끝까지 필수 조회를 하지 못한 모델 모드 실행은 모델의 최종 상태를 그대로 기록한다. 새 상태·키·원인 코드를 만들지 않는다. trace `rule_reference`의 `available`(마지막 값 거짓)로 드러낸다.
     - 까닭: 채점에서는 기대 상태 불일치와 필수 근거 미충족으로 이미 실패로 세어진다.
     - 결과 요약에 모드별 "참고값 없이 끝난 실행 수"를 공개 항목으로 넘긴다(아래 "영향과 넘길 곳").
2. **도구 차례 `max_tokens`**(보 권고 1)
   - 설정 `request.tool_turn_max_tokens` 1024를 더했다(단위 I7 `ModelSettings.tool_turn_max_tokens`). `tool_choice` `"required"` 차례에만 쓰고, 초안 차례는 `max_tokens` 8192 그대로다. 모든 모드 같다.
   - 도구 호출 응답은 실측에서 수십 토큰이다.
   - ⑲의 "`required`는 도구 호출을 냈다"(탐침 2회, 8회차 24/24)의 **반례**: `run_case-260925082849` 수정 단계의 `required` 응답이 도구 호출 없이 공백 반복으로 8,192토큰을 채웠다 `[사실: trace]`. `required`도 도구 호출을 보장하지 않는다. 그런 응답은 초안이 아니므로 ⑱대로 버려지고 다음 차례로 간다.
3. **막힌 산문 수정 지시**
   - 수정 차례 요청(단위 I10 `feedback_message`)에 검증기가 막은 산문 표현(`PROSE_UNBACKED`)을 경로와 글자 그대로 나열한다. 예: `narrative: '변동이 없'; hypotheses[0]: '50.0%'`.
   - 함께 싣는 지시: "이 표현이 든 문장을 지우거나, 같은 값·같은 방향의 지표 주장을 인용하는 문장으로 바꾼다. 같은 표현을 다른 곳에 다시 쓰지 않는다." 모든 모드 같다.
   - 원래 "[검증기 지적]"은 사유 목록 JSON만 실었다.
4. **지침 보탬**(무 권고)
   - 비교 미완료 HOLD는 MAINTAIN 후보일 때만이다. 단가 MONITOR는 비교국 비교가 필요 없다.
   - "ALL 분모 < 대상국 금액"은 분자가 분모보다 커 점유율을 정의할 수 없는 자료라는 뜻이다. 시간에 따른 분모 축소와 다르다.
   - narrative 숫자 안내를 검증기와 같게 맞췄다. 연월·기간, HS 코드, 국가 코드, 근거 ID·버전 이름, 조사 횟수는 검증기가 빼므로(룰북 B3-2 EX-1~EX-4) 써도 된다.
5. CLI 단위 F1의 머리 설명과 `CASE_RULE` 예시를 `850450-XA-202412`로 바꿨다(보 권고 2).
6. **시험**
   - F2
     - 허용되지 않는 상태 조합(단가 MONITOR인데 사례 MAINTAIN): full은 수정 1회 뒤에도 차단돼 INVALID(VALIDATOR_BLOCKED)이고, freeform은 COMPLETED이며 `validator_findings`에 STATUS_INCONSISTENT를 기록한다(평 권고 C).
     - 도구 차례 1024, 초안 차례 8192.
   - I10: 막힌 산문 나열, 계산 불가 안내에 "모자라면 HOLD"가 없음.

㉒ **사용자 결정 반영과 조정 종료(병합 준비, `model-1.2`)** — 확정

- 반영한 사용자 결정(2026-09-25(금) 08:41, "전부 권장안대로, 단 10은 나")
  - 결정 1(`policy_v1` 승인·U1~U4, 결정 기록 `20260925-0846-user-decision-policy-v1-approval.md`)
    - U4 반올림 불안정 → HOLD를 채택했다. `dispatch.ROUNDING_UNSTABLE_ENABLED`를 참으로 켰다(⑧의 규칙 그대로). 조사자 지침 규칙 요약과 Critic의 상태 뜻에 반올림 불안정 → HOLD를 더했다.
    - δ는 정책의 `tolerance.weight_rounding_kg`(0.5 kg)에서 읽는다.
  - 결정 4(누적 토큰 한도 128,000, 결정 기록 `20260925-0847-user-decision-morning-shared-promises.md`): `configs/model/model.json` `limits.tokens` 128000이다. 토큰 추정 시험과 I7 한도 시험은 설정 값을 읽는다.
  - 결정 6(`tool_attempts`는 도구에 닿은 시도만): MT4(#29)가 `COUNT_BLOCKED_TOOL_ATTEMPTS`를 거짓으로 바꿨다. `origin/main` 병합 결과도 거짓이다(병합 커밋 2a60a52).
  - 결정 13(규칙 참고값·도구 호출 요구 유지) 승인으로 ⑰~㉑을 확정한다. 모델 모드의 판정이 규칙 참고값을 보고 정해진다는 공개 문구 초안은 "영향과 넘길 곳"에 있다.
- `config_version` `model-1.2`.
- 10회차 출하본(`model-1.1`) 실측(오케스트레이터, 한도 128K 조건 18회, 합성 A·B·C × agent·full·freeform × 2회, `scratchpad/as2_live_matrix_r10_128k.tsv`, 커밋하지 않은 실측) `[사실]`
  - 기대 일치 16/18: agent 5/6(A 1회 VALIDATOR_BLOCKED), full 5/6(B 1회 SCHEMA_INVALID. 수정 초안이 `max_tokens`에서 잘림), freeform 6/6.
  - 규칙 참고값은 18/18 끝내 계산됐다(3회는 처음 계산 불가 뒤 다시 계산). 키 접두어 0이다.
  - 누적 토큰은 중앙값 29,956, 최대 43,026이었다. 옛 한도 32,000을 넘은 실행은 7/18이다.
- **조정 종료**: 오케스트레이터 지시로 이 뒤로는 실측 결과를 보고 지침·흐름을 더 조정하지 않는다. 설정 조정은 합성 A·B·C 3건으로 했다(`model-0.2`~`1.2`, 결과 요약 공개 항목).
- 단위 표(`docs/plan/UNITS.md`) 판정 칸은 1회차의 AS2 점검 문구 28행 그대로다. 이후 회차는 판정(유지·합침 후보)을 바꾸지 않았다. 단위 I10의 허용 import에 `tradesentry.metrics`를 더한 것(⑭)은 머리 주석과 경계 시험으로 확인한다.

㉓ **산문 숫자 금지와 신호 계열 주장 규칙을 맨 앞으로(12회차, `model-1.3`, 오케스트레이터 판단)** — 잠정(재실측 전)

- 까닭: `main` 1ea3c90 뒤 실자료 개발 묶음(`real_dev`, 개발용 실자료) 실측(오케스트레이터, full 모드, 실제 NIM, 호스트, 5건 + 시연 경로 1건. 실행 폴더는 `outputs/run_case-260925125318`·`-125351`·`-125409`와 STAGE 작업 폴더 `outputs/run_case-260925125001`, 커밋하지 않음) 분류 `[사실, 오케스트레이터 보고]`
  - PH-202302: 두 번 모두 INVALID(VALIDATOR_BLOCKED). narrative의 '1.2%'·'15.9%'·'+4.0 pp'·'-11.8 pp' 같은 숫자가 막혔다. 검증기(R3) 오탐이 아니다. 모델이 비교국 d_s(점유율 변화, pp) 값을 문장에 적으면서 그 비교 주장을 claims에 넣지 않았고, 지표 번호(metric_id)도 r_U 번호에 d_s를 붙여 잘못 적었다.
  - MY-202401: INVALID(SCHEMA_SIGNAL_CLAIM: 발동한 단가 신호의 계열 주장이 없음)와 산문 숫자.
  - MX-202404: COMPLETED.
  - 나머지 2건: HTTP 429(요청 한도 초과)로 실패. 지침과 무관해 따로 처리한다.
- 바꾼 것(`configs/model/*.txt`만, 세 모델 모드에 같은 글자)
  - 조사자 초안 규칙의 맨 앞에 "발동한(TRIGGERED) 신호마다 그 계열의 지표 주장(단가 신호는 r_U, 점유율 신호는 d_s)을 claims에 반드시 하나 이상 넣는다"를 두었다(이전에는 산문 규칙 뒤).
  - 숫자 금지: narrative·hypotheses에는 숫자 표현(%, pp, 금액·중량·단가, 배수, "X에서 Y로")을 쓰지 않는다. 값은 claims로만 내고 문장은 "단가 변화율 주장(claims의 r_U)"처럼 주장을 가리킨다. 이전의 "같은 값의 지표 주장이 있으면 써도 된다"는 허용을 뺐다. 검증기 규칙(PT-1~PT-8)은 그대로이고, 지침의 PT-6 어휘 목록 대조 시험도 그대로다.
  - Critic 지적 문장에도 같은 숫자 금지를 두었다(값은 claim_refs로 가리킨다). Critic에게 초안 산문의 숫자를 따로 지적하게 하지는 않았다. freeform 기준선에 두 번째 산문 검사를 더해 대표 지표 비교를 바꾸지 않으려는 것이다.
  - freeform 주장 쓰는 법에 "narrative·hypotheses에는 숫자와 증감 어휘를 쓰지 않는다"를 맞췄다.
- 승인 근거: 2026-09-25(금) 14:17 사용자 결정 `20260925-1417-user-decision-real-dev-tuning.md`("1.3 + 흐름 수정")가 `real_dev`로 조사 지침·흐름을 조정하는 것을 승인했다(결정 ①·②). 아래 "룰북과 어긋나는 점"은 그 결정에 따라 문서 PR(DOCS3)이 푼다.
- 이 조정은 `real_dev` 사례로 한 조정이다. 결과 요약 공개 항목을 "모델 설정은 합성 A·B·C와 real_dev 사례로 조정"으로 바꿨다(아래 "영향과 넘길 곳"). ㉒의 "조정 종료" 뒤 오케스트레이터 판단으로 한 번 더 조정한 것이다.
- 대표 지표에 미치는 영향: 대표 지표(룰북 B3 실자료 사실 주장 오류율, `freeform` 대 `full`)는 typed claim(`source` `claim`)과 산문 패턴으로 잡힌 표현(`source` `prose`)을 함께 센다. freeform(모델이 값을 직접 쓰는 기준선 모드)도 같은 지침으로 산문에 숫자를 쓰지 않게 돼 산문 주장(`prose`)의 기여가 줄고, 대표 지표는 주로 typed claim 값 오류를 재게 된다. 결과 요약에 이 점을 적는다.
- 룰북과 어긋나는 점(결정 필요): 룰북 Part B 묶음 표(`docs/eval/RULEBOOK.md`의 `real_dev` 행 둘)는 `real_dev`를 "탐지 임계값·최소 기준 조정과 산문 패턴 보강에만 쓴다"고 적는다. 모델 지침 조정은 이 용도 목록에 없다. 룰북은 아직 `RB-1`(동결 전 초안, 동결 예정 2026-09-26(토) 18:00)이라 동결 전에 고칠 수 있지만, 평가 구성은 공용 약속이라 사용자 승인이 필요하다. 동결 뒤라면 새 룰북 버전과 사유가 필요하다(B5). 재실측 수치를 결과 요약에 싣기 전에 오케스트레이터·사용자가 정한다. 이 PR은 룰북을 고치지 않는다.
- 코드 쪽 남은 불일치(이 PR 범위 밖, `configs/model/*.txt`만 고침): 수정 지시 문구 `investigator.PROSE_FIX`는 "이 표현이 든 문장을 지우거나, 같은 값·같은 방향의 지표 주장(claims)을 인용하는 문장으로 바꾼다"라서, 수정 차례에 숫자를 남긴 채 주장으로 뒷받침하라는 뜻으로 읽힐 수 있다. 새 지침과 맞추려면 "숫자 없이 주장을 가리키는 문장으로 바꾼다"로 고쳐야 한다(다음 PR 후보).
- 보고서 한국어 렌더러 확인(단위 R4 `reports/render_ko.py`, 동결 경로라 고치지 않음) `[사실]`: `render_body`는 주장마다 `[claim_id] text (근거: …)` 줄을 쓰고 `value`·`unit`을 따로 찍지 않는다. 그래서 한국어 본문에 값이 보이는 것은 주장 text에 값을 적었을 때뿐이다. `run-case`는 보고서 객체(JSON, claims의 `value`·`unit` 포함)만 쓰고 한국어 본문(`body_ko`)은 쓰지 않는다. 산문에서 숫자를 빼면 사람이 읽는 본문의 값은 주장 text에 기댄다.
- `config_version` `model-1.3`. I12 골든 `request_sha256`을 다시 만들었다(요청 본문의 지침 글자가 바뀜).
- 시험: I10 `NoNumbersInProseTest` — 숫자 금지 문장이 agent·full·freeform 지침(`investigator.system_prompt`)에 글자까지 같게 한 번씩 있고, 신호 계열 규칙이 초안 규칙의 첫 줄이며, Critic 지침에 숫자 금지가 있다.

㉔ **흐름 수정 두 가지: Critic 재조회 거르기와 수정 전 초안 두기(13회차, 단위 I12, `model-1.3`)** — 확정(사용자 결정)

- 날짜·결정: 2026-09-25(금) 14:17 사용자 결정 `20260925-1417-user-decision-real-dev-tuning.md`의 ③ (가)·(나)를 코드로 옮겼다. 모든 모델 모드에 같은 규칙이다.
- 근거(원인 실험, 오케스트레이터, 2026-09-25(금) 13:40~14:10, `scratchpad/ab/RESULTS.md`, 커밋하지 않은 실측) `[사실, 오케스트레이터 보고]`
  - `real_dev` 두 사례(`850432-PH-202302`, `850450-MY-202401`)의 모델 요청 13건을 앱의 기록 재생(단위 I8)으로 다시 만들었고 요청 해시가 모두 같았다. 같은 요청도 temperature 1.0에서 결과가 갈렸다(PH 3번 중 2번, MY 4번 중 3번 `INVALID`).
  - 점유율 신호만 발동한 PH 사례에서 검수자(Critic)는 네 번 모두 하위품목 분해(`decompose_hs`) 재조회를 요청했다. 지침에 "분해는 단가 신호일 때만"을 넣어도 네 번 중 두 번 요청했다. 그래서 코드로 거른다.
  - PH의 첫 초안은 검증기를 통과했고 규칙 참고값과도 맞았는데, 검수자 요구로 고친 초안이 `INVALID`가 됐다. 수정 단계 지침만 바꾸면 효과가 작았다.
- (가) 검수자 재조회 요청 거르기: `orchestrate.SIGNAL_ONLY_TOOLS`(`{"decompose_hs": ("unit_value",)}`, workflow 안의 상수 하나)에 있는 도구의 요청은, 그 사례에서 대응 신호가 하나도 발동(TRIGGERED)하지 않았으면 버린다(`split_requery`). 버린 요청은 수정 지시 메시지(`investigator.feedback_message`의 Critic 지적 칸)와 수정 단계의 필수 조회 목록(`requested`)에 들지 않는다. `needs_revision`은 바꾸지 않는다. workflow는 cli를 import하지 않으므로, 상수와 신호별 필수 도구 규칙(`dispatch.required_tools`)이 어긋나지 않는지는 시험이 네 신호 조합으로 대조한다.
- (나) 수정본을 버리고 수정 전 초안 두기: ① 수정 단계를 연 까닭이 Critic의 수정 요구뿐이고(초안 형식 문제·스키마 실패·수정 전 검증기 막음·코드 지적이 없다) ② 수정 전 초안이 verify 단계 검사(스키마, `freeform`이 아니면 검증기까지)를 통과했고 ③ 수정본이 최종 단계에서 막히면(초안 형식 검사 실패, 스키마 검사 실패, `freeform`이 아니면 검증기 막음), `INVALID`로 끝내지 않고 수정 전 초안의 보고서와 그 verify 단계 판정으로 `complete`한다(`_Flow.blocked_revision`). 도구·모델 요청과 검사를 더 하지 않는다. `critic_used`·`revision_used`는 그대로 참이다. `agent`는 Critic이 없어 ①이 성립하지 않는다. deadline·예산·연결 오류 같은 `RunStop`은 예외로 곧바로 멈추므로 이 규칙을 거치지 않는다.
- trace 모양(새 사건 종류 없음, 단위 L1 `EVENT_TYPES` 그대로)
  - `state_change` `after_critic`: `requery`는 거르고 남은 요청 수, 새 필드 `requery_dropped`는 버린 요청 목록 `[{tool, args, reason: "signal_not_triggered", signals}]`(버린 것이 없으면 빈 목록).
  - 새 `phase` 값 `revision_discarded`(`final` 단계, `final` 바로 앞): `review_status`·`signal_status`는 둔 수정 전 초안의 것, `blocked_by`(`draft_format`·`schema`·`validator`), `would_be_cause`(규칙이 없었다면 났을 원인 `SCHEMA_INVALID`·`VALIDATOR_BLOCKED`), `kept_report_id`. 수정본의 막힌 `validator_result`(phase `final`, decision `block`)는 그대로 남는다. `COMPLETED` 실행이므로 `budget_block` `revision_limit`은 내지 않는다.
  - trace를 읽는 코드(`src`·`eval`에서 `state_change`·`phase`를 찾음): 채점기·추출기·NAT 감싸기(단위 I13) 가운데 phase 값을 읽는 곳은 없다(`eval/scorer/summary.py`는 상태 변화를 "trace 형식 미정"이라며 집계하지 않는다). 룰북 결과 요약의 공개 항목 "버린 초안 수"를 세는 코드도 아직 없다. 이 이름(`revision_discarded`)은 조사자 차례의 `draft_discarded`와 달라서, 나중에 `draft_discarded`로 세는 코드를 만들면 (나)는 그 수에 들지 않는다. 결과 요약에 따로 셀지는 AS3·R1이 정한다.
- 시험(`tests/units/I12/test_orchestrate.py`)
  - `RequeryFilterTest`: 상수와 `dispatch.required_tools` 대조(네 신호 조합, 상수 밖 필수 도구는 어느 신호에도 필수), `split_requery` 순서·까닭, 점유율 신호만 발동한 사례(full·freeform, 차례 규칙을 켠 흐름)에서 `decompose_hs` 재조회를 버리고 trace에 남기며 수정 지시에 없고 수정 단계에 필수 조회 요구(`tool_choice` `required`)가 없음, 단가 신호가 발동한 사례에서는 그대로 남아 수정 단계에서 부름.
  - `RevisionFallbackTest`: 검증기 막음·수정본 형식 실패(full)와 수정본 스키마 실패(freeform)에서 `COMPLETED`이고 최종 보고서가 수정 전 초안의 것(검사·도구·모델 요청 수 그대로), 수정 전 검증기 막음·코드 지적으로 연 수정·첫 초안 스키마 실패·`agent`·`checklist`는 지금처럼 `INVALID`, 수정본 응답 중 deadline은 `TIMEOUT`.
  - 달라진 기존 시험: `FlowBudgetTest.test_second_revision_stage_is_blocked`(로드맵 체크리스트 2번 "두 번째 수정 단계 차단"). 대본 `[PASS, PASS, BLOCK]`(Critic 수정 요구만으로 연 수정)은 이제 수정 전 초안을 두어 `COMPLETED`다. 체크리스트 2번을 계속 보도록 수정 전 검증기도 막는 대본 `[PASS, BLOCK, BLOCK]`으로 바꿨다(기대값 `INVALID`·`VALIDATOR_BLOCKED`·`revision_limit` 그대로). 이전 대본은 `RevisionFallbackTest`가 본다. I12 골든(수정 없이 끝나는 사례 A full)은 바뀌지 않았다.
- 공개 문구: ㉒ "조정 종료"에 적은 "설정 조정은 합성 A·B·C 3건으로 했다"(결과 요약 공개 항목)는, 위 사용자 결정에 따라 문서 PR(DOCS3)이 룰북 B7에서 "합성 A·B·C 3건과 `real_dev` 두 사례의 실패 유형으로 조정"으로 고쳐 적었다. 이 기록의 ㉑·㉒ 본문은 고치지 않는다.
- 검토 반영(오케스트레이터, 같은 날 15시 무렵, 도메인 검토 권고 ②·③과 Codex 1회차 막음): ① 수정 지시 문구 `investigator.PROSE_FIX`를 "이 표현이 든 문장을 지우거나, 숫자·증감 어휘 없이 지표 주장(claims)을 가리키는 문장으로 바꾼다(값과 방향은 claims에만 둔다)"로 고쳤다(㉓의 "코드 쪽 남은 불일치"를 닫음). ② 지침의 식별 표기 예외를 검증기 빼기 규칙(EX-1~EX-3)에 맞게 좁혔다: 연월·분기, 자릿수 전체로 쓴 HS 코드, 근거 ID·버전 이름만 빼고, HS 코드의 일부·"N개월 연속"·개수와 0은 숫자 표현으로 잡힌다고 적었다(원인 실험의 '1010' 조각). ③ 지침의 주장 text 숫자 규칙이 narrative·가설 숫자 금지를 풀지 않음을 밝혔다. 지침이 바뀌어 I12 골든 입력의 첫 요청 해시를 다시 만들었다(흐름·기대 출력은 그대로).
- 남은 점: Critic 답의 재조회 요청은 `critic.parse_review`가 최대 개수(2)로 먼저 자른 뒤 (가)가 거른다. 그래서 버려질 `decompose_hs` 요청이 앞에 있으면 세 번째 유효한 요청이 이미 잘려 있을 수 있다.

## 조립 점검 결과(조립체 3, `docs/plan/UNITS.md` §5의 1·2·5단계)

AS2는 합치거나 버린 단위가 없다. 동결 경로(판정 정책 P3~P5, 검증기 R3·R4) 단위의 코드는 고치지 않았다. 고친 단위는 F2(배선)와 I12(C형 펼치기)다. 3·4·6단계의 확정은 조립 점검 작업 AS4가 한다.

| 단계 | 결과 | 명령과 종료 코드 |
|---|---|---|
| 1. 정적 import 그래프 | `cli.dispatch` → `cli.args`, `contract.policy_load`·`types`, `dal.query`, `metrics.unit_value`·`share`·`decompose`, `policy.trigger`·`case_build`, `runlog.cause_codes`·`trace`, `workflow.model_client`·`nat_wrap`·`orchestrate`(+ 기존 `snapshot.build`·`verify`). `workflow.orchestrate` → `policy.signal_decide`·`case_aggregate`·`required_evidence`, `reports.claims`·`render_ko`, `runlog` 셋, `tools` 여섯, `validator.validate`·`gate`, `workflow.investigator`·`critic`·`model_client`·`replay`. 도구 넷 → `tools.check_comparability`(공통 틀)·`dal.query`·`metrics`. `validator.validate` → `reports.render_ko`. 모두 각 단위 머리 주석의 허용 import 안이다. `src/tradesentry` 모듈 그래프에 순환 0 `[사실: 경계 시험 도우미(tests/test_boundaries.py의 repo_modules·import_targets)로 커밋 81b9df9에서 뽑은 그래프]` | `env -u NVIDIA_API_KEY -u DATA_GO_KR_SERVICE_KEY -u TRADESENTRY_SEALED_DIR uv run --locked python -m unittest discover -s tests -p "test_boundaries.py"` → 0 |
| 2. 실행 커버리지 | `run-case`를 합성 시험자료 A·B·C × 네 모드(모델 모드는 가짜 모델)로 돌려 `sys.setprofile`로 `src/tradesentry` 함수 호출의 파일을 모았다. 네 모드 모두: X1~X4, P4, P5, I1~I7, I12, I13, R1~R4, L1, L2. `checklist`만: P3. 모델 세 모드: I10. `full`·`freeform`: I11. 불리지 않음: G1(비교국 표는 미리 계산된 `peer_group` 행을 K3로 읽는다), I8(기록 재생, 시험·골든 전용. I10~I12는 오류 형식만 import한다), L3(성공 경로에서는 상수만 쓴다. 실패 경로(키 없는 `agent` 실행 → `FAILED`·`CODE_ERROR`)에서는 불린다). I9(구성)는 모델 설정·프롬프트로 읽힌다 `[사실: scratch 스크립트, 12회 모두 종료 코드 0]` | 조립 시험 `tests/units/F2/test_run_case_command.py`(16개)·`test_run_case_evidence.py`(15개) → 0 |
| 5. 동작 불변 | 합치거나 버린 것이 없다. `detection_row` 추출 뒤 AS1 조립 시험이 그대로 통과하고, I12 골든의 `request_sha256`도 그대로다. 출력 파일 도메인명은 단위 표 글자(`runlog_trace`, `workflow_nat_wrap`, `runlog_run_record`, `reports_render_ko`)와 같다(N4, 시험이 글자로 확인) | 단위별 `env -u … uv run --locked python -m unittest discover -s tests/units/<ID> -t tests`: 조립체 3의 X1~X4·P3~P5·G1·I1~I13·R1~R4·L1~L3과 F2 모두 0, skipped 0(보고 AS2-1 §2). 전체 `env -u … uv run --locked python -m unittest discover -s tests -v` → 0. 1회차 머리 81b9df9에서 Ran 893, 9회차 머리(⑳ 커밋, `origin/main` acd4240 병합 뒤)에서 Ran 997, 10회차 머리(㉑ 커밋)에서 Ran 1000, 병합 준비 머리(㉒ 커밋, `origin/main` deb8128 병합 뒤)에서 Ran 1228(skipped 9), 모두 skipped 15(조립체 3 밖의 뼈대 단위 골든) |

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
  - `src/tradesentry/cli/dispatch.py`: `run-case` 배선, 머리 설명의 "사례 조사 명령 run-case" 절, `detection_row` 추출, `required_tools`·`drafts_only_without_tools` 켜기(⑮·⑱)
  - `src/tradesentry/cli/args.py`: `--case` 도움말·머리 설명·`CASE_RULE` 예시(⑳·㉑)
  - `src/tradesentry/workflow/orchestrate.py`: C형 펼치기(⑥), 필수 조회·규칙 참고값·도구 없는 차례의 초안·차례 규칙·코드 지적·참고값 재계산(⑮·⑰~⑳), Critic 재조회 거르기·수정 전 초안 두기(㉔)
  - `src/tradesentry/workflow/investigator.py`: 분해 보기 `rule_view`, 필수 근거 보기 압축, 참고값·필수 조회·코드 지적 문구, `tool_choice`, `compare_partners` 설명(⑭~⑲)
  - `src/tradesentry/workflow/critic.py`: 참고값 문구 전달(⑰)
  - `src/tradesentry/workflow/model_client.py`: `tool_choice`(⑲), `tool_turn_max_tokens`(㉑)
  - `configs/model/*`: 지침(`investigator.txt`·`critic.txt`·`claims_freeform.txt`), `model.json`(`max_tokens` 8192, `tool_turn_max_tokens` 1024, `config_version` `model-1.1`), README(⑬~㉑)
  - `skills/tradesentry/SKILL.md`: run-case 출력·사례 식별자 맞춤(⑳)
  - `tests/units/F2/`: `run_case_fixture.py`, `test_run_case_command.py`, `test_run_case_evidence.py`
  - `tests/units/I10/test_rule_view.py`, `tests/units/I12/test_orchestrate.py`·`test_token_estimate.py`·`input.json`, `tests/units/I13/input.json`, `tests/units/I7/test_model_client.py`, `tests/test_model_config.py`
  - `docs/plan/UNITS.md` 판정 칸
- AS3(평가 실행·채점 연결)
  - 보고서 파일 이름은 작업 지시가 적은 채점기 가정 `reports_render_ko-{시각}.json`과 같다(이 브랜치의 채점기 코드로는 대조하지 못했다). 실행 결과 기록은 `runlog_run_record-{시각}.json`이다.
  - 실행이 `COMPLETED`가 아니면 종료 코드가 1이고 보고서 파일이 없다(기록은 있다).
  - 사례 실행 폴더를 묶음 폴더와 잇는 방법(자문 명세서 Q9)은 정하지 않았다.
  - `tradesentry evaluate`는 `dispatch.investigate_case` 배선을 그대로 써야 한다. 그래야 세 포트(`required_tools`, `drafts_only_without_tools`, 근거 상태 변환 훅으로 켜지는 `reference_status`)가 켜진다. `orchestrate.unit_ports`를 직접 부르면 개발 실측과 채점 대상 실행의 흐름이 달라진다. 평가 실행에서 세 포트가 켜졌는지 보는 시험을 AS3에 둔다(평 권고 4).
- 결과 요약(로드맵 R1)·룰북 B2·B4 공개 항목(평 권고 1·A, 사용자 결정 13 승인 뒤, 룰북은 이 PR에서 고치지 않는다)
  - 공개할 수치
    - 모델 모드가 규칙 참고값과 필수 조회를 받는다는 점
    - 모드별 참고값 가용률, "최종 = 참고값" 비율, 참고값 없이 끝난 실행 수(㉑)
    - `required` 차례 수, `draft_discarded`·`code_finding` 건수, Critic 생략률
    - 한도 값(누적 토큰, `max_tokens` 8192, 도구 차례 1024)
    - 모델 설정은 합성 A·B·C와 real_dev 사례로 조정한 사실(`model-0.2`~`1.2`는 합성 A·B·C, `model-1.3`은 `real_dev` 사례, ㉓)
  - B2 "모든 모드에 같은 조건"에 더할 문구(초안): "규칙 참고값과 필수 조회: 모델 모드(`agent`·`full`·`freeform`)의 조사자와 Critic은, 코드가 공개 판정 규칙(판정 정책 P3)을 그 초안을 쓸 때까지 받은 근거에 적용한 신호별 판정을 규칙 참고값으로 받는다(수정 단계에서 새 조회 결과를 받으면 다시 계산한다). 지침은 참고값을 따르게 하고, 규칙이 보지 않는 도구 결과 속 사실이 있을 때만 narrative에 반대 근거를 적고 벗어나게 한다. 코드는 모델의 판정을 덮어쓰지 않는다. 필수 도구(발동 신호가 있으면 `compare_partners`, 단가 신호가 발동했으면 `decompose_hs`)의 결과가 없고 그 단계의 도구 몫이 남은 차례에는 `tool_choice: "required"`와 빠진 도구 이름을 적은 알림을 싣는다(부를 도구를 API로 지정하지는 않는다). Critic 뒤(agent는 첫 검증 뒤)에도 필수 결과가 없으면 코드 지적을 붙여 같은 수정 1회로 보낸다. 문구·시점은 세 모델 모드에 글자까지 같다."
  - B4(또는 결과 요약 2절)에 더할 문구(초안): "holdout40에서 `agent`·`full`과 `checklist`의 판정 일치는 모델이 규칙을 스스로 적용한 정도가 아니라, 규칙 참고값을 따르거나 반대 근거로 벗어난 정도다. 두 모드가 `checklist`보다 나을 수 있는 길은 정책 규칙과 독립 정답표가 다른 사례에서 반대 근거로 옳게 벗어나는 경우와, 필수 조회·주장 작성·검증 통과의 차이뿐이다. 개선이 없으면 "이 범위에서 LLM 추가 가치 미확인"으로 보고한다."
- dev20 개발 점수표(평 권고 3): `RB-1` 전에 이 설정(`model-1.2`)으로 dev20을 한 번 돌린다. 결과로 설정을 바꾸면 그 사실과 회차를 기록한다. 지금 `RUN_CASE_DATASETS`에 dev20이 없어 먼저 한 줄을 더해야 한다.
- 2026-09-25(금) 08:41 사용자 결정(반영은 ㉒)
  - U4: 채택돼 `ROUNDING_UNSTABLE_ENABLED`를 참으로 켰다.
  - 원인 분류 코드 이름(결정 5)·`tool_attempts` 뜻(결정 6, 도구에 닿은 시도만): 이 배선은 코드 이름을 쓰지 않는다. 시험은 `cause_codes` 상수로 단언한다. `COUNT_BLOCKED_TOOL_ATTEMPTS`는 거짓이다.
- AS1 두 번째 PR·분할 기록 정본 위치 승인: ⑩의 좁히는 자리. `run-case`도 `real_dev` 사례만 받는다.
- DT1(K3): 비교국 표의 `grouping_version` 목록을 주는 함수가 있으면 rowid 훑기(⑨)를 바꾼다(요청 후보).
- DT5·DT8: 분류 7의 점유율 사유 문자열(⑦)은 이 조립이 정한 이름이다. 정답표·채점기가 문자열을 보면 맞춘다.
- DT5(dev20): dev20 스냅샷 ID가 정해지면 `RUN_CASE_DATASETS`에 한 줄을 더한다.
- MT5(샌드박스): 샌드박스 안의 설치에는 `.git`이 없을 수 있어 `code_version`이 `unknown`이 된다. 샌드박스 밖 실행기가 커밋 해시를 넘길 수단은 MT5·MT7이 정한다 `[미확인]`.
- 모델 모드 실측: 실제 NIM으로 `run-case`를 돌리는 명령은 AS2 보고 AS2-1의 "오케스트레이터가 돌릴 명령"에 적었다.
