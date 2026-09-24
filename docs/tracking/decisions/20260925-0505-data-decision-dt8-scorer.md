# DT8 독립 채점기의 해석과 입출력 약속

DT8(독립 채점기, 데이터 트랙) 구현(단위 C1~C4와 채점기 명령, PR #30)에서 룰북·자료 계약이 정하지 않았거나 데이터 트랙(D)에게 맡긴 세부와, 검토 1회차(Codex(OpenAI의 코딩 에이전트 CLI) 교차 검토, 평가 방법론 검토, 무역통계·관세 검토, 보안 검토)와 오케스트레이터의 수정 2회차 지시가 요구한 해석을 적는다. 코드와 시험은 PR #30에 있다. 항목마다 **확정** 또는 **잠정**을 붙였다. 잠정 항목은 적힌 조건(사용자 확인, 다른 작업의 형식 확정, `RB-1` 동결)이 채워지면 새 기록으로 확정하거나 바꾼다.

용어

- 채점기 단위: C1 주장 채점(`eval/scorer/claims.py`), C2 산문 채점(`prose.py`), C3 채점 결과 기록(`results.py`), C4 보조 지표·요약(`summary.py`), 채점기 명령(`__main__.py`, `python -m eval.scorer --run <run_dir>`).
- 세 채점 키: 실행 결과 기록(자료 계약 §8)에서 샌드박스 밖 채점기만 채우는 `required_evidence_ok`(필수 근거), `numeric_ok`(수치·단위), `provenance_ok`(출처·버전).
- 정답표: 합성 묶음(`controlled_fixture_v0`·`dev20`·`holdout40`)의 사례별 기대 판정. 지금 기준은 `eval/dev/oracle_ABC.json`이다.
- 필수 근거 코드: 정답표가 발동 신호마다 요구하는 근거 조건의 이름. 판정 정책(MT1 단위 P5, `src/tradesentry/policy/required_evidence.py`)의 13개와 같다.
- 실행 조건 입력 파일: 채점기가 모르는 실행 조건을 호스트 쪽 프로그램이 넘기는 파일 `<run_dir>/run_conditions-{시각}.json`(결정 D6의 임시 형식).
- 유효한 claim: 대상이 풀리고(`referent_resolved`) 근거가 맞는(`evidence_ok`) typed claim(정해진 필드를 가진 사실 주장). 값의 참·거짓은 `numeric_ok`가 따로 본다.
- 빠진 키: 신호 계열의 대상 범위에서 관측 상태가 `OBSERVED`·`CONFIRMED_NO_TRADE`가 아닌 키(상대국·HS 코드·월).
- 계획 밖 키: 수집 설정(스냅샷 메타 `collection_plan`)의 어느 요청도 맡지 않는 키.
- C형: 부모 HS6 행은 있는데 HS10 하위 자료 요청만 실패한 경우(oracle C, 자료 계약 §2.3.2 행 규칙 4).
- F1 전 보완: 결정 D17에 따라 병합 뒤 같은 작업 ID로 내는 추가 수정 PR 목록. DT8 구현 보고(`DT8-2.md`) §9가 목록이다.

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 05:05(기록 시각). ①·⑤는 2026-09-24(목) 23:30~2026-09-25(금) 01:30 구현 1회차에, 나머지는 검토 1회차 뒤 수정 2회차(02:00~05:05)에 정했다 |
| 제목 | DT8 채점기의 세 채점 키 해석, 정답표 필드, 필수 근거 코드 판정 조건, 실행 조건 입력 파일 임시 형식, 계획 대조·비교집합·근거 행 규칙, 믿지 않는 입력의 상한 |
| 결정 | 아래 "결정 내용" ①~⑮ |
| 이유와 근거 | 아래 "결정 내용"의 항목마다 적었다 |
| 검토한 대안 | 아래 "검토한 대안" |
| 결정 주체 | 소유 트랙(D). ⑪은 DT2 결정 ⑫(오케스트레이터 확정), ⑫는 MT3 결정 ⑨에 맞췄다 |
| 공용 약속 여부 | ②(실자료의 `required_evidence_ok` 값 형식)와 ⑦(값 행도 상태 행도 없는 계획 키의 관측 상태)은 결과 기록 형식·상태값 해석에 닿으므로 공용 약속으로 보고 사용자 확인을 받는다(병렬 개발 규칙 §4.5: 애매하면 공용 약속). ③·④는 평가 구성(병렬 개발 규칙 §4.1)에 닿으므로 DT5 정답표와 MT1 결정 D17의 공개 판정 조건 표로 맞춘 뒤 확정한다. 나머지는 채점기 소유 단위의 해석이고 계약 필드·상태값·ID 형식·기준값을 바꾸지 않는다 |
| 영향 | 아래 "영향과 넘길 곳" |
| 관련 PR | #30 |

## 결정 내용

① **세 채점 키의 해석** — 확정

- `numeric_ok`: 실행이 `COMPLETED`이고 보고서를 읽었으며, typed claim 기록에 `WRONG_VALUE`·`WRONG_DIRECTION`·`WRONG_UNIT`·`WRONG_REFERENT`가 없고 산문 기록에 `UNBACKED_PROSE`가 없다.
- `provenance_ok`: 실행이 `COMPLETED`이고 보고서를 읽었으며, 모든 typed claim 기록의 `evidence_ok`가 참이고, 보고서의 `snapshot_id`·`policy_version`·`grouping_version`이 실행 기록과 같다.
- `required_evidence_ok`: 합성 묶음에서만 채운다. 실행이 `COMPLETED`이고 보고서를 읽었으며, 정답표가 발동 신호마다 정한 필수 근거 코드를 모두 채운다(④).
- 유효한 최종 보고서가 없는 실행(`COMPLETED`가 아님, 보고서 없음, 읽지 못함, ⑬의 상한 초과)은 세 키가 거짓이다. 런타임이 세 키를 적었어도 채점기 값이 우선한다(룰북 B4).
- 이유: 룰북 B3-1 판정 순서(대상 → 단위 → 방향 → 값 → 근거)에서 근거가 마지막이라 `outcome`만으로 수치 오류를 가를 수 있고, 근거는 `evidence_ok`로 따로 본다(평가 방법론 검토 초점 ①).

② **실자료 묶음(`real_dev`·`real_sealed`)의 `required_evidence_ok`는 `null`** — 잠정(사용자 확인 대기)

- 실자료에는 정답표(사례별 필수 근거)가 없어 이 값을 정할 수 없다. 거짓은 오해를 부르고 참은 공허한 참(조건이 비어 저절로 참)이다. 실자료 대표 지표(룰북 B3)는 이 키를 쓰지 않는다.
- 자료 계약 §8.1은 이 키의 형식을 참/거짓으로 정했다. 권고안은 "참/거짓. 정답표가 없는 실자료 묶음은 `null`"로 계약 문구를 고치는 것이다(평가 방법론 검토 지적 3).
- 확인을 받기 전에는 `real_dev` 채점 결과를 증거로 커밋하지 않는다.

③ **정답표 필드** — 잠정(DT5 정답표 형식과 맞춘 뒤 확정)

- 정답표는 `results.read_answer_table` 한 곳에서만 읽는다. 필드:
  - `cases`: 목록. 사례마다 서로 다른 `case_id`(문자열)와 `expected` 객체
  - `expected.signals`: `{"unit_value", "share"}` → `TRIGGERED`·`NOT_TRIGGERED`(발동 신호가 1개 이상)
  - `expected.review_status`: 한국어 표기(검토 유지·모니터링·자료 보류) 또는 코드(`MAINTAIN`·`MONITOR`·`HOLD`)
  - `expected.required_evidence`(필수): 발동 신호가 하나면 코드 목록, 둘이면 `{발동 신호: 코드 목록}`. 키가 없으면 입력 오류이고 빈 목록은 명시할 때만 받는다(공허한 참을 막는다, 평가 방법론 검토 지적 1)
  - `expected.signal_status`(선택): 신호별 판정. 두 신호가 모두 발동한 사례는 필수
  - `expected.unresolved_evidence`(선택): 없으면 사례 집계 규칙(자료 계약 §3.1)으로 정한다
- 코드는 ④의 13개 이름만 받고, 그 신호 계열의 코드여야 한다(단가: `parent_child_match_V_and_Q`, `weight_share_decomposition`, `per_child_unit_value_stable`, `comparability_ok`, `partner_comparison_done`, `missingness_listed`, `failure_vs_not_collected_distinguished`, `no_zero_fill`, `precision_sensitivity_shown` / 점유율: `country_and_world_change_shown`, `partner_comparison_done`, `comparability_ok`, `missingness_listed`, `failure_vs_not_collected_distinguished`, `no_zero_fill`). 판정 정책 P5 규칙표의 계열별 합집합이다.
- 모르는 코드, 계열에 없는 코드, 교정 전후 세 코드(`correction_snapshots_before_after`, `recalculated_values`, `change_reason`)는 입력 오류다. 교정 세 코드는 동결 스냅샷 하나로 도는 v1에 해당 사례가 없다(MT1 결정 ⑥).
- 그 밖의 키(원자료, 기대 수치)는 채점에 쓰지 않는다. 수치 기대값은 채점기가 원본 행에서 따로 계산한다.

④ **필수 근거 코드의 판정 조건** — 잠정(MT1 결정 D17의 공개 판정 조건 표가 정해지면 맞춘다. `precision_sensitivity_shown`은 사용자 확인 U4 뒤)

사례 문맥은 품목 `hs6`, 대상국 P, 비교월 t, 기준월 b(=t−12), 실행 기록의 `grouping_version`이다.

| 코드 | 채운 것으로 보는 조건 |
|---|---|
| `parent_child_match_V_and_Q` | 보고서 근거(보고서와 claim의 `evidence_ids`)가 두 시점의 부모 HS6 행과, 두 시점 모두에 있는 HS10 하위 코드마다의 행을 모두 인용한다 |
| `weight_share_decomposition` | `within_effect`·`mix_effect`·`residual`(t, b) 분해 claim이 모두 유효하다(MT1 뜻대로 residual 포함) |
| `per_child_unit_value_stable` | 두 시점의 HS10 하위 코드마다 `r_U@코드` claim(또는 두 시점 `U@코드` claim)이 유효하다 |
| `comparability_ok` | 신호 계열의 전년동월 변화 claim(단가 `r_U`, 점유율 `d_s`) 또는 두 시점 수준 claim(`U`, `s`)이 유효하다 |
| `partner_comparison_done` | 비교집합(⑧) 안 비교국의 계열 지표 comparison claim(단가 `r_U` 또는 두 시점 `U`, 점유율 `d_s` 또는 두 시점 `s`)이 유효하다 |
| `missingness_listed` | 계열 대상 범위(단가: P의 부모 HS6 키와 C형 HS10 하위, 점유율: P의 부모 HS6 키와 `ALL` 분모, 두 시점)의 빠진 키마다 그 키를 `OBSERVED`가 아닌 상태로 적은 유효한 `data_status` claim이 있다(C형은 그 HS6 아래 HS10 코드 하나로 적으면 된다). 빠진 키가 없으면(모두 `OBSERVED`인 HOLD, 비교국 누락 HOLD) 비교국의 빠진 키를 적은 유효한 `data_status` claim이나, 계산할 수 없는 계열 지표를 null로 적은 `CORRECT` claim이 하나 이상 있다 |
| `failure_vs_not_collected_distinguished` | 빠진 키마다 그 상태를 맞게 적은(`CORRECT`) `data_status` claim이 있고, 사례 품목·두 시점의 `data_status` claim에 `WRONG_VALUE`가 없다 |
| `no_zero_fill` | 대상이 풀렸고 기대값이 null인 수 claim에 수(0 포함)를 적은 것이 없다. 첫 결과가 단위·방향 오류여도 센다(무역통계 권고 5) |
| `precision_sensitivity_shown` | 대상국의 두 시점 부모 `V`·`Q` value claim 네 개가 유효하다(정밀도·민감도의 바탕. typed claim으로 적을 민감도 지표가 없어 입력값으로 대신한다) |
| `country_and_world_change_shown` | 대상국 `V`와 `ALL` `V`의 두 시점 value claim 네 개가 유효하다 |

- 이유: 1회차 조건으로는 모두 `OBSERVED`인 HOLD 사례(룰북 B1 시나리오 5·6)에서 `missingness_listed`·`failure_vs_not_collected_distinguished`를 어떤 보고서도 채울 수 없었고, 점유율만 발동한 사례의 `comparability_ok`가 단가 `r_U`를 요구했다(평가 방법론 검토 지적 4). 판정 근거(basis)를 정답표에 두지 않고도 채울 수 있게, 빠진 키가 없을 때의 대체 조건을 두었다.
- 정답표는 판정 근거에 맞는 코드를 적는다. 예를 들어 반올림 불안정(`rounding_unstable`)은 `precision_sensitivity_shown`만이고, 여기에 `missingness_listed`를 적으면 계산 불가 지표가 없어 채울 수 없다.

⑤ **실행 조건 입력 파일(결정 D6 임시 형식)** — 잠정(F1 전 MT7과 확정)

- 위치와 이름: `<run_dir>/run_conditions-{시각}.json`. `{시각}`은 `<run_dir>` 실행명의 시각이다. 글롭으로 찾지 않는다.
- 약속한 키: `dataset`, `planned_cases`, `planned_modes`, `snapshot`, `policy_detection_thresholds`, `rulebook`, `grouping_reason`, `scorer_commit`, `prose_patterns_commit`, `run_period`, `concurrency`, `order_seed`, `limits`, `sandbox`, `sealed_hash_recheck`, `sealed_provenance_check`, `precheck`, `prescoring_checks`, `skill_call_success`, `nat_profile_summary`, `korean_sample_review`, `reproduce_evaluate`, `a_grade`.
- 필수: `dataset`(계약 자료 묶음 이름, `<run_dir>`의 봉인 여부와 맞아야 한다), `planned_cases`(`[{case_id, hs6, partner, month}]`, 분모. `partner`는 국가 코드이고 `ALL`은 받지 않는다), `planned_modes`(룰북 B2의 그 묶음 모드), `policy_detection_thresholds`(비지 않은 수 목록. 룰북 B3-2 EX-5가 쓴다. 없으면 임계값 문장이 조용히 `UNBACKED_PROSE`가 된다, 평가 방법론 검토 지적 2).
- 선택: `snapshot.file`(저장소 안 `.sqlite` 상대경로, 없으면 `data/snapshots/{snapshot_id}/snapshot_build.sqlite`). 나머지 키는 요약에 옮기는 값이다.
- 거부: 약속 밖 키, 형식이 틀린 값, 로컬 절대경로, 키 모양(NVIDIA 키 접두어·서비스키 요청 파라미터), 1 MiB 초과. 봉인 묶음은 `rulebook`·`scorer_commit`·`prose_patterns_commit`·`sealed_hash_recheck`(= "일치")·`sealed_provenance_check`·`prescoring_checks`·`precheck`·`sandbox`(`real_sealed`는 `a_grade`도)가 있어야 하고, 봉인 출력이 있어야 하는 `nat_profile_summary`·`korean_sample_review`가 있으면 거부한다.
- 채점기 커밋 해시는 하위 프로세스로 얻지 않고 이 파일(`scorer_commit`)에서 받는다.

⑥ **`data_status` 주장의 계획 대조** — 확정(룰북 B3-1 "`data_status` 주장"의 구현)

- 수집 계획은 스냅샷 메타 `collection_plan`(hs6·partners·hs4_scan·period·collect_total_denominator·hs10)이다. 없으면 입력 오류다. 행에 나온 코드·달로 짐작하지 않는다(Codex 검토 막는 지적 1).
- 키(상대국, HS6 또는 HS10 코드, 월)를 맡는 계획 요청:
  - 상대국 HS6 키: HS4 스캔(부모 HS6 행의 원천)과 그 HS6 조회
  - 상대국 HS10 키: 그 HS6 조회(HS10 하위 행의 원천)와 HS10 직접 조회
  - `ALL` 키: 분모 조회(itemtrade)의 HS4·HS6 요청
- 판정 순서
  1. 맡는 요청이 없으면(계획 밖 키) 대상 판정을 하지 않고 `NOT_COLLECTED`를 기대한다. 근거는 `snapshot-build`가 비교 대상에 만든 `NOT_COLLECTED` 행(그 키 자신이나 맡았을 요청의 코드)뿐이고, 없으면 `UNSUPPORTED`다. 대상 오류가 아니다(룰북 B3-1 예시 8).
  2. 맡는 요청이 있어도 HS6가 수집 설정의 hs6 밖이면(예: HS4 스캔이 함께 준 `850440`) `WRONG_REFERENT`다(자료 계약 §2.3.2 행 규칙 7).
  3. 그 밖은 원본 행으로 기대 상태를 정한다(⑫).
- 수 주장의 대상도 같은 범위(수집 설정의 HS6, 상대국과 비교국 표의 계획 밖 비교국과 `ALL`, 수집 기간)로 본다.

⑦ **계획 안인데 값 행도 상태 행도 없는 키** — 잠정(상태값 해석, 사용자 확인 대기)

- 그 키를 맡은 요청 가운데 그 달에 성공(`OK`)한 것이 있으면, 응답에 그 키만 없는 것으로 보고 `UNRESOLVED_ZERO`를 기대한다. 수집기는 상태 행을 요청 코드 자릿수로만 쓰므로 인용할 행이 없다. 그래서 `UNRESOLVED_ZERO`로 적으면 `UNSUPPORTED`, 다른 상태로 적으면 `WRONG_VALUE`다.
- 성공한 요청도 없으면 관측 상태를 정할 수 없어 어느 상태를 적어도 `WRONG_VALUE`다(스냅샷 빌드가 만들지 않는 모양).
- 자주 닿는 곳: 성공한 HS6 조회의 응답에 어떤 HS10 코드만 빠진 달(무역통계 검토 지적 4).
- 런타임 자료 접근층(DT1 K3)은 이런 키에서 SnapshotError를 내거나 코드를 돌려주지 않으므로, 틀 채우기 모드에서는 닿지 않고 `freeform`에서만 닿는다.
- 확인 요청 문구: "성공한 요청의 응답에 그 키의 행만 없는 경우의 관측 상태를 `UNRESOLVED_ZERO`로 보되 인용할 행이 없다고 본다. 채점기·검증기(MT3)·자료 접근층(DT1)이 같게 따른다."

⑧ **comparison 주장의 비교집합** — 확정

- 기대값과 소속은 실행 기록(묶음 기록 줄)의 `grouping_version`으로 정한다. 보고서의 값이 아니다.
- 비교집합은 스냅샷 `peer_group` 표에서 대상국·그 버전·가장 좁은 범위(hs6 → hs4 → hs2)에 행이 있는 비교국이다. 자료 접근층 `peers()`와 같다. 저장소 CSV(`data/reference/peer_group_g0.csv`)로 따로 채우지 않는다. 스냅샷 빌드가 그 CSV를 적재하고 정규화 해시로 묶기 때문이다.
- 사례 문맥(대상국·품목·버전)이 없거나, 그 버전의 집합이 스냅샷에 없거나, 상대국이 집합 밖이거나(대상국 자신 포함), 품목이 사례 품목이 아니면 `WRONG_REFERENT`다(Codex 검토 막는 지적 2).
- 주의: DT1의 개발 빌드(`outputs/snapshot_build-260924235251/`, 2026-09-25(금) 읽기 전용 확인)에는 `peer_group` 행이 없다. `g0`를 적재한 빌드로 채점하지 않으면 실자료의 comparison 주장은 모두 `WRONG_REFERENT`가 된다.

⑨ **근거 ID의 rowid 해석** — 확정

- 조각 4개, `ev`, snapshot_id 일치, 테이블 있음, 그 rowid의 행 있음(자료 계약 §4.4 풀림 규칙 1~4)을 본다. rowid는 앞자리 0이 없고 19자리 이하이며 2^63−1 이하인 양의 정수(ASCII 숫자, 문자열 전체 대조)다. 끝 줄바꿈, 유니코드 숫자, 4,301자리 조각은 풀리지 않고 묶음을 멈추지 않는다(무역통계 검토 막는 지적 1).
- 모든 형식 검사(월·HS 코드·상대국·지표 기호·실행명)는 `fullmatch`와 ASCII 숫자 `[0-9]`로 한다.

⑩ **기대값이 null인 주장의 근거** — 확정

- 빠진 값은 그 키 자신과 그 키를 맡은 요청의 상태 행 묶음 가운데 하나를 인용해야 한다. 상대국 HS6는 (P, HS6)·(P, HS4), `ALL`은 HS6·HS4 요청, HS10은 그 코드와 HS6 조회(`ALL`이면 HS4 요청도)다. 다른 상대국·다른 달의 행은 뒷받침하지 않는다(자료 계약 §4.4, 무역통계 검토 막는 지적 2).
- 인용할 행이 없는 묶음은 어떤 근거로도 채울 수 없다(`UNSUPPORTED`). 분해 null은 두 시점의 부모 행과 하위 행(없으면 그 HS6 조회의 상태 행)이 모두 필요하다.

⑪ **부모 중량 0** — 확정(DT2 결정 ⑫에 맞춤)

- 부모 HS6 행의 중량이 한 시점이라도 0이면 `within_effect`·`mix_effect`·`residual` 모두 null이다. 부모 대조가 허용오차 안이어도 같다. 승격된 달(V·Q를 0으로 다룸)도 여기에 든다.

⑫ **C형 자료 상태와 근거 행** — 확정(MT3 결정 ⑨와 같은 해석)

- 값 행이 있으면 `OBSERVED` 하나다(상대국 HS6 키는 수신 기록상 HS4 스캔이 준 부모 HS6 행, `ALL` HS6 키는 그 HS6 아래 `ALL` HS10 행, HS10 키는 그 코드의 행). 부모 행이 있으면 같은 키의 HS6 조회 상태 행은 HS10 하위 자료의 상태이므로 HS6 수준 `observation_status`를 뒷받침하지 않고 `observation_status@<HS10>`만 뒷받침한다.
- 상대국 HS10 키는 HS6 조회의 상태 행만 받고 HS4 스캔 행은 받지 않는다. `ALL` HS10 키는 HS4·HS6 요청 행을 모두 받는다.
- `CONFIRMED_NO_TRADE`는 그 키의 상태 행이 모두 승격된 행일 때만 받는다(DT1 자료 접근층과 같다). 승격 규칙의 독립 구현은 `policy_v1` 승인 뒤 F1 전에 한다.
- 한 보고서의 서로 어긋나는 자료 상태 주장은 채점기가 따로 막지 않고 claim마다 같은 해석으로 판정한다. 검증기는 `DATA_STATUS_CONFLICT`로 막는다(MT3 결정 ⑩).
- 요청 전체가 실패하면 HS10 코드를 알 수 없으므로 자료 상태 주장의 HS10 코드가 스냅샷에 있는지는 보지 않는다(부모 HS6로 시작하는 숫자 10자만 본다). 무역통계 검토 가장자리 (c)의 권고에 따라 적는다.

⑬ **믿지 않는 입력의 상한** — 잠정(`RB-1` 동결 때 평가 방법론 검토와 함께 확정)

- 수 값: 유효 숫자 100자리, 10의 지수 ±100(정수는 절댓값 10^100 미만) 안만 수로 받는다. 밖의 값은 claim 단위의 해석 불가(`WRONG_REFERENT`)다. 산문의 100자리 넘는 숫자 표현은 뒷받침될 수 없다(`UNBACKED_PROSE`).
- 보고서: 파일 1 MiB, typed claim 300개, 산문 필드 글자 수 합 50,000자. 넘거나, JSON이 아니거나, 너무 깊이 중첩하면 유효한 최종 보고서가 없는 것으로 세고(보고서 단위 실패) 사유를 요약에 적는다. 한 보고서가 묶음 전체를 멈추거나 끝나지 않게 하지 않는다(보안 검토 막는 지적).
- 묶음 기록·정답표·봉인 파일은 16 MiB, 실행 조건 입력 파일은 1 MiB다. 넘으면 입력 오류다. 묶음 기록은 줄바꿈 문자(`\n`)로만 나눈다.
- 이유: 상한 크기의 최악 입력(긴 공백·숫자열, 표현 수만 개 × claim 300개)이 1초 안에 끝나는 것을 시험으로 확인했다. 실제 보고서는 모델 토큰 한도에 묶여 상한보다 훨씬 작다.

⑭ **원천 요청으로 행 가리기** — 확정

- 부모 HS6 행은 수신 기록 `params_json`의 요청이 (`nitemtrade`, HS6 앞 4자리)인 `OBSERVED` 수입 행, HS10 하위 행은 (`nitemtrade`, 그 HS6) 요청의 행이다(자료 계약 §2.3.2 행 규칙 4, DT1 자료 접근층과 같다). `ALL` HS10 행은 요청을 가리지 않고 같은 키의 중복을 동등하게 본다(행 규칙 5·6).

⑮ **산문 패턴 목록의 되돌림 제거** — 확정

- 뜻은 그대로 두고 공백 되돌림을 없앴다(소유 한정자 `\s*+`, 류 패턴의 앞 숫자 고정, 목록 번호 패턴의 줄 머리 고정, 앞뒤 문맥은 위치 인자로 본다). 패턴 원문이 바뀌어 패턴 목록 지문(`pattern_list_sha256`)이 1회차와 다르다. 지문 값을 시험에 고정하는 일은 `real_dev` 보강이 끝나는 `RB-1` 동결 전에 한다.

## 검토한 대안

- ② 실자료에 거짓이나 참을 적는 안: 거짓은 "필수 근거 실패"로 읽히고 참은 공허한 참이라 버렸다.
- ③ 정답표에 판정 근거(basis)를 신호마다 적고 그에 따라 빠진 키 범위를 고르는 안: 형식이 커지고 DT5가 따라야 할 약속이 늘어 버렸다. 빠진 키가 없을 때의 대체 조건(④)으로 같은 사례를 채울 수 있다.
- ④ 빠진 키가 없으면 `missingness_listed`를 해당 없음(참)으로 보는 안: 공허한 참이라 버렸다. 정답표가 그 코드를 적지 않게 하는 안: 판정 정책 P5가 자료 부족 판정에 늘 요구하므로 정답표와 정책이 갈려 버렸다.
- ⑥ 상대국·HS6·월이 각각 스냅샷 어딘가에 있으면 계획 안으로 보는 1회차 구현: 계획 밖 조합을 계획 안으로 보아 `WRONG_VALUE`를 내서 버렸다(Codex 검토).
- ⑦ 어느 상태를 적어도 `WRONG_VALUE`로 두는 1회차 구현: 뜻이 맞는 `UNRESOLVED_ZERO`를 수치 오류로 세고, 계획 밖 키를 `UNSUPPORTED`로 보는 룰북 B3-1과 결이 달라 버렸다.
- ⑧ 스냅샷에 그 버전의 행이 없으면 저장소 CSV로 채우는 안: 출처가 둘이 되어 자료 접근층 `peers()`와 갈릴 수 있어 버렸다.
- ⑬ 상한 밖 수를 보고서 단위 실패로 보는 안: 다른 해석 불가 값(문자열 값 등)과 달라져 claim 단위로 두었다. 보고서마다 모든 예외를 잡아 실패로 세는 안: 봉인 묶음에서 채점기 결함이 조용히 보고서 실패로 바뀌므로 버렸다(입력 오류·중첩 오류만 보고서 실패로 센다).
- ⑮ 패턴을 그대로 두고 보고서 크기 상한만 두는 안: 1 MiB 공백에서도 이차 역추적이 몇 시간 걸려 버렸다.

## 영향과 넘길 곳

- DT5(시나리오 명세·dev20)·DT6(holdout40): 정답표를 ③의 형식으로 만든다. 코드는 판정 근거에 맞게 고른다(④ 표 아래). 경로가 정해지면 오케스트레이터가 `DEV20_ANSWERS`와 봉인 파일 이름(`SEALED_FILES`)을 알린다.
- MT1(D17): 공개 판정 조건 표를 ④와 맞춘다. HOLD를 사유별로 나누면 ④의 대체 조건을 다시 본다.
- MT3(검증기): ⑦의 해석, ⑫의 `flow`(수입 행만) 확인, `ALL` HS6 `OBSERVED` 근거, 상대국 HS10 키의 HS4 행 불가를 같게 맞춘다.
- DT1(자료 접근층): 근거 ID `rowid_of`에도 19자리 상한을 둔다(⑨). ⑦이 확정되면 자료 접근층의 빠진 HS10 표시를 맞춘다. `g0`를 적재한 빌드를 정본 자리에 옮긴다(⑧의 주의).
- MT7(평가 묶음): ⑤의 형식을 F1 전에 확정한다. 봉인 묶음 요약의 룰북 B7 0절 값(한도·순서 seed·동시성·실행 기간·정규화 해시와 대조·`g0` 사유·재현 명령)을 필수로 올리는 일, 인프라 실패 재실행 줄의 룰북 B5 조건 확인, 내려받은 사례 폴더 수 대조는 F1 전 보완 목록에 있다.
- 사용자 확인(오케스트레이터가 올린다): ② 실자료 `null`, ⑦ 값 행도 상태 행도 없는 계획 키의 상태.
