# DT8 독립 채점기의 해석과 입출력 약속

DT8(독립 채점기, 데이터 트랙) 구현(단위 C1~C4와 채점기 명령, PR #30)에서 룰북·자료 계약이 정하지 않았거나 데이터 트랙(D)에게 맡긴 세부와, 검토 1회차(Codex(OpenAI의 코딩 에이전트 CLI) 교차 검토, 평가 방법론 검토, 무역통계·관세 검토, 보안 검토)와 오케스트레이터의 수정 2회차 지시가 요구한 해석, 검토 2회차 뒤 수정 3회차에서 정한 것(⑯·⑰, ⑤·⑩·⑫·⑬의 보충)을 적는다. 코드와 시험은 PR #30에 있다. 항목마다 **확정** 또는 **잠정**을 붙였다. 잠정 항목은 적힌 조건(사용자 확인, 다른 작업의 형식 확정, `RB-1` 동결)이 채워지면 새 기록으로 확정하거나 바꾼다.

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
- F1 전 보완: 결정 D17에 따라 병합 뒤 같은 작업 ID로 내는 추가 수정 PR 목록. 이 기록 끝의 "F1 전 보완 목록"이 목록이다.

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 05:05(기록 시각). ①·⑤는 2026-09-24(목) 23:30~2026-09-25(금) 01:30 구현 1회차에, 나머지는 검토 1회차 뒤 수정 2회차(02:00~05:05)에 정했다. ⑯·⑰과 ⑤·⑩·⑫·⑬의 보충은 검토 2회차 뒤 수정 3회차(같은 날 오전)에 더했다 |
| 제목 | DT8 채점기의 세 채점 키 해석, 정답표 필드, 필수 근거 코드 판정 조건, 실행 조건 입력 파일 임시 형식, 계획 대조·비교집합·근거 행 규칙, 믿지 않는 입력의 상한, 묶음 기록 조합과 봉인 자리 판정 |
| 결정 | 아래 "결정 내용" ①~⑰ |
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
- dev20 정답표 경로 `DEV20_ANSWERS`는 `eval/dev/dev20/answers/answers.json`이다(DT5 결정 기록 ⑭). DT5 브랜치의 정답표를 이 함수로 읽어 보면(읽기만) 20건 가운데 19건이 통과하고 새 이름 둘(`country_and_world_change_shown`, `precision_sensitivity_shown`)도 받는다. 두 신호가 모두 발동한 1건은 필수 근거를 합친 목록으로 적어 입력 오류다. 합친 목록에서는 두 계열에 모두 있는 코드(`comparability_ok` 등 다섯)가 어느 신호의 근거인지 알 수 없어 채점기가 나누지 않는다. DT5가 그 사례를 신호별 객체로 적어야 dev20 채점이 된다. 평가 방법론 검토 2회차가 본 DT5 작업 폴더의 2회차판(커밋 전)은 신호별 객체로 바뀌어 20건이 모두 읽힌다.

④ **필수 근거 코드의 판정 조건** — 잠정(MT1 결정 D17의 공개 판정 조건 표가 정해지면 맞춘다. `precision_sensitivity_shown`은 사용자 확인 U4 뒤)

사례 문맥은 품목 `hs6`, 대상국 P, 비교월 t, 기준월 b(=t−12), 실행 기록의 `grouping_version`이다.

| 코드 | 채운 것으로 보는 조건 |
|---|---|
| `parent_child_match_V_and_Q` | 두 시점 모두 HS10 하위 행이 있고, 보고서 근거(보고서와 claim의 `evidence_ids`)가 두 시점마다 부모 HS6 행과 그 시점의 HS10 하위 코드마다의 행을 모두 인용한다(한 시점에만 있는 코드도 그 시점에서 인용한다) |
| `weight_share_decomposition` | `within_effect`·`mix_effect`·`residual`(t, b) 분해 claim이 모두 유효하다(MT1 뜻대로 residual 포함) |
| `per_child_unit_value_stable` | 두 시점의 HS10 하위 코드마다 `r_U@코드` claim(또는 두 시점 `U@코드` claim)이 유효하다 |
| `comparability_ok` | 신호 계열의 전년동월 변화 claim(단가 `r_U`, 점유율 `d_s`) 또는 두 시점 수준 claim(`U`, `s`)이 유효하다 |
| `partner_comparison_done` | 비교집합(⑧) 안 비교국의 계열 지표 comparison claim(단가 `r_U` 또는 두 시점 `U`, 점유율 `d_s` 또는 두 시점 `s`)이 유효하다 |
| `missingness_listed` | 계열 대상 범위(단가: P의 부모 HS6 키와 C형 HS10 하위, 점유율: P의 부모 HS6 키와 `ALL` 분모, 두 시점)의 빠진 키마다 그 키를 `OBSERVED`가 아닌 상태로 적은 유효한 `data_status` claim이 있다(C형은 그 HS6 아래 HS10 코드 하나로 적으면 된다). 빠진 키가 없으면(모두 `OBSERVED`인 HOLD, 비교국 누락 HOLD) 비교국의 빠진 키를 적은 유효한 `data_status` claim이나, 계산할 수 없는 계열 지표를 null로 적은 `CORRECT` claim이 하나 이상 있다 |
| `failure_vs_not_collected_distinguished` | 빠진 키마다 그 상태를 맞게 적은(`CORRECT`. 인용할 행이 없는 키(⑦)는 대상이 풀리고 값이 기대 상태와 같으면 된다) `data_status` claim이 있고, 사례 품목·두 시점의 `data_status` claim에 `WRONG_VALUE`가 없다. 빠진 키가 없으면 앞 조건이 비어 `WRONG_VALUE`가 없기만 하면 채운다(공허한 참). 판정 정책 P5는 이 코드를 늘 `missingness_listed`와 함께 요구하고 그 코드에는 대체 조건이 있으므로 둘을 함께 보면 공허하지 않다는 전제다(평가 방법론 검토 2회차 권고 5). 정답표가 이 코드만 따로 적는 사례가 생기면 다시 본다 |
| `no_zero_fill` | 대상이 풀렸고 기대값이 null인 수 claim에 수(0 포함)를 적은 것이 없다. 첫 결과가 단위·방향 오류여도 센다(무역통계 권고 5) |
| `precision_sensitivity_shown` | 대상국의 두 시점 부모 `V`·`Q` value claim 네 개가 유효하다(정밀도·민감도의 바탕. typed claim으로 적을 민감도 지표가 없어 입력값으로 대신한다) |
| `country_and_world_change_shown` | 대상국 `V`와 `ALL` `V`의 두 시점 value claim 네 개가 유효하다 |

- 이유: 1회차 조건으로는 모두 `OBSERVED`인 HOLD 사례(룰북 B1 시나리오 5·6)에서 `missingness_listed`·`failure_vs_not_collected_distinguished`를 어떤 보고서도 채울 수 없었고, 점유율만 발동한 사례의 `comparability_ok`가 단가 `r_U`를 요구했다(평가 방법론 검토 지적 4). 판정 근거(basis)를 정답표에 두지 않고도 채울 수 있게, 빠진 키가 없을 때의 대체 조건을 두었다.
- 정답표는 판정 근거에 맞는 코드를 적는다. 예를 들어 반올림 불안정(`rounding_unstable`)은 `precision_sensitivity_shown`만이고, 여기에 `missingness_listed`를 적으면 계산 불가 지표가 없어 채울 수 없다.
- 넘길 것(평가 방법론 검토 2회차 권고 6): DT5 dev20 정답표의 불일치·비교 조건 HOLD 사례(단가 3건 `parent_child_match_V_and_Q`·`comparability_ok`·`no_zero_fill`, 점유율 2건 `country_and_world_change_shown`·`comparability_ok`·`no_zero_fill`)의 코드 조합이 P5 규칙표(HOLD는 자료 부족·비교 불완전의 세 코드 또는 반올림 불안정의 `precision_sensitivity_shown`)에 없다. 채점기는 계열별 합집합만 보므로 받지만, 조사자·검증기가 P5대로 근거를 남기면 처리정확도가 모든 모드에서 깎인다. MT1 D17(공개 판정 조건 표)과 DT5가 MVP 합격 체크리스트 5번 전에 맞춘다.

⑤ **실행 조건 입력 파일(결정 D6 임시 형식)** — 잠정(F1 전 MT7과 확정)

- 위치와 이름: `<run_dir>/run_conditions-{시각}.json`. `{시각}`은 `<run_dir>` 실행명의 시각이다. 글롭으로 찾지 않는다.
- 약속한 키: `dataset`, `planned_cases`, `planned_modes`, `snapshot`, `policy_detection_thresholds`, `rulebook`, `grouping_reason`, `scorer_commit`, `prose_patterns_commit`, `run_period`, `concurrency`, `order_seed`, `limits`, `sandbox`, `sealed_hash_recheck`, `sealed_provenance_check`, `precheck`, `prescoring_checks`, `skill_call_success`, `nat_profile_summary`, `korean_sample_review`, `reproduce_evaluate`, `a_grade`.
- 필수: `dataset`(계약 자료 묶음 이름, `<run_dir>`의 봉인 여부와 맞아야 한다), `planned_cases`(`[{case_id, hs6, partner, month}]`, 분모. `partner`는 국가 코드이고 `ALL`은 받지 않는다), `planned_modes`(룰북 B2의 그 묶음 모드), `policy_detection_thresholds`(비지 않은 수 목록. 룰북 B3-2 EX-5가 쓴다. 없으면 임계값 문장이 조용히 `UNBACKED_PROSE`가 된다, 평가 방법론 검토 지적 2).
- 선택: `snapshot.file`(저장소 안 `.sqlite` 상대경로, 없으면 `data/snapshots/{snapshot_id}/snapshot_build.sqlite`). 나머지 키는 요약에 옮기는 값이다.
- 거부: 약속 밖 키, 형식이 틀린 값, 로컬 절대경로 모양(3회차부터 거부 목록이 아니라 모양으로 본다: 값의 처음이나 공백·따옴표·구분 기호 뒤의 `/`, UNC `\\이름`, 드라이브 문자 `C:\`·`C:/`, 홈 폴더 표기(물결표 뒤 빗금). 봉인 폴더 기본값(홈 폴더의 `.tradesentry/sealed/`)만 뺀다. `USD/kg`처럼 글자 뒤의 `/`와 URL은 걸리지 않는다, 보안 검토 2회차 권고 5), 키 모양(NVIDIA 키 접두어·서비스키 요청 파라미터), 1 MiB 초과. 봉인 묶음은 `rulebook`·`scorer_commit`·`prose_patterns_commit`·`sealed_hash_recheck`(= "일치")·`sealed_provenance_check`·`prescoring_checks`·`precheck`·`sandbox`(`real_sealed`는 `a_grade`도)가 있어야 하고, 봉인 출력이 있어야 하는 `nat_profile_summary`·`korean_sample_review`가 있으면 거부한다.
- 채점기 커밋 해시는 하위 프로세스로 얻지 않고 이 파일(`scorer_commit`)에서 받는다.
- 봉인 필수 값은 지금 있는지만 본다(`sealed_hash_recheck`만 값이 "일치"인지 본다). `precheck: "실패"`처럼 값이 실패를 뜻해도 채점하고 요약에 그대로 적는다. 값의 내용 검사(사전 점검·출처 확인이 통과인지)는 이 파일의 형식을 확정할 때(결정 D6, F1 전) 함께 정한다(보안 검토 2회차 권고 3, F1 전 보완 목록).

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
- 여러 원천을 쓰는 지표(`s`, `r_U`, `d_s`, 분해)가 null이면 빠진 쪽의 상태 행 묶음과 나머지 원천 행을 모두 인용해야 한다. 예: null인 `s`는 대상국 상태 행 묶음과 분모 `ALL` HS10 행, null인 `r_U`·`d_s`는 다른 시점의 행도 요구한다(룰북 B3-1 "기대값 계산에 필요한 원본 행 집합", 경계 17, 예시 6과 같은 결. 무역통계 검토 2회차 권고 2로 코드 범위에 맞춰 문구를 넓혔다).

⑪ **부모 중량 0** — 확정(DT2 결정 ⑫에 맞춤)

- 부모 HS6 행의 중량이 한 시점이라도 0이면 `within_effect`·`mix_effect`·`residual` 모두 null이다. 부모 대조가 허용오차 안이어도 같다. 승격된 달(V·Q를 0으로 다룸)도 여기에 든다.

⑫ **C형 자료 상태와 근거 행** — 확정(MT3 결정 ⑨와 같은 해석)

- 값 행이 있으면 `OBSERVED` 하나다(상대국 HS6 키는 수신 기록상 HS4 스캔이 준 부모 HS6 행, `ALL` HS6 키는 그 HS6 아래 `ALL` HS10 행, HS10 키는 그 코드의 행). 부모 행이 있으면 같은 키의 HS6 조회 상태 행은 HS10 하위 자료의 상태이므로 HS6 수준 `observation_status`를 뒷받침하지 않고 `observation_status@<HS10>`만 뒷받침한다.
- 상대국 HS10 키는 HS6 조회의 상태 행만 받고 HS4 스캔 행은 받지 않는다. `ALL` HS10 키는 HS4·HS6 요청 행을 모두 받는다.
- `CONFIRMED_NO_TRADE`는 그 키의 상태 행이 모두 승격된 행일 때만 받는다(DT1 자료 접근층과 같다). 승격 규칙의 독립 구현은 `policy_v1` 승인 뒤 F1 전에 한다.
- 한 보고서의 서로 어긋나는 자료 상태 주장은 채점기가 따로 막지 않고 claim마다 같은 해석으로 판정한다. 검증기는 `DATA_STATUS_CONFLICT`로 막는다(MT3 결정 ⑩).
- 부모 행이 없는 상대국 HS6 키에 상태가 섞이면(HS4 스캔 `REQUEST_FAILED`와 HS6 조회 `UNRESOLVED_ZERO`) 두 상태를 모두 기대 상태로 보아 어느 쪽을 그 행과 함께 적어도 `CORRECT`다. 자료 계약 §2.3.2 행 규칙 4가 "그 월을 맡은 요청들이 남긴 상태 행"을 모두 빠진 자료로 돌려주기 때문이다. 부모 값의 원천(HS4 스캔)을 먼저 기대하는 해석(DT1 자료 접근층은 HS4 스캔 상태를 첫 상태로 돌려준다)과 다르므로 MT3 검증기(`DATA_STATUS_CONFLICT`)·DT1과 F1 전에 맞춘다. DT1 개발 빌드에는 이 모양이 없다(수신 기록 모두 `OK`, 무역통계 검토 2회차 권고 1).
- 요청 전체가 실패하면 HS10 코드를 알 수 없으므로 자료 상태 주장의 HS10 코드가 스냅샷에 있는지는 보지 않는다(부모 HS6로 시작하는 숫자 10자만 본다). 무역통계 검토 가장자리 (c)의 권고에 따라 적는다.

⑬ **믿지 않는 입력의 상한** — 잠정(`RB-1` 동결 때 평가 방법론 검토와 함께 확정)

- 수 값: 유효 숫자 100자리, 10의 지수 ±100(정수는 절댓값 10^100 미만) 안만 수로 받는다. 밖의 값은 claim 단위의 해석 불가(`WRONG_REFERENT`)다. 산문의 100자리 넘는 숫자 표현은 뒷받침될 수 없다(`UNBACKED_PROSE`).
- 보고서: 파일 1 MiB, typed claim 300개, `hypotheses` 항목 100개(빈 항목도 센다. 3회차에 더함: 1 MiB 안의 빈 항목 수십만 개가 보고서마다 수 초를 썼다, 보안 검토 2회차 권고 4), 산문 필드 글자 수 합 50,000자. 넘거나, JSON이 아니거나, 너무 깊이 중첩하면 유효한 최종 보고서가 없는 것으로 세고(보고서 단위 실패) 사유를 요약에 적는다. 한 보고서가 묶음 전체를 멈추거나 끝나지 않게 하지 않는다(보안 검토 막는 지적).
- 묶음 기록·정답표·봉인 파일은 16 MiB, 실행 조건 입력 파일은 1 MiB다. 넘으면 입력 오류다. 묶음 기록은 줄바꿈 문자(`\n`)로만 나눈다.
- 이유: 상한 크기의 최악 입력(긴 공백·숫자열, 표현 수만 개 × claim 300개)이 1초 안에 끝나는 것을 시험으로 확인했다. 실제 보고서는 모델 토큰 한도에 묶여 상한보다 훨씬 작다.

⑭ **원천 요청으로 행 가리기** — 확정

- 부모 HS6 행은 수신 기록 `params_json`의 요청이 (`nitemtrade`, HS6 앞 4자리)인 `OBSERVED` 수입 행, HS10 하위 행은 (`nitemtrade`, 그 HS6) 요청의 행이다(자료 계약 §2.3.2 행 규칙 4, DT1 자료 접근층과 같다). `ALL` HS10 행은 요청을 가리지 않고 같은 키의 중복을 동등하게 본다(행 규칙 5·6).

⑮ **산문 패턴 목록의 되돌림 제거** — 확정

- 뜻은 그대로 두고 공백 되돌림을 없앴다(소유 한정자 `\s*+`, 류 패턴의 앞 숫자 고정, 목록 번호 패턴의 줄 머리 고정, 앞뒤 문맥은 위치 인자로 본다). 패턴 원문이 바뀌어 패턴 목록 지문(`pattern_list_sha256`)이 1회차와 다르다. 지문 값을 시험에 고정하는 일은 `real_dev` 보강이 끝나는 `RB-1` 동결 전에 한다.

⑯ **묶음 기록의 (사례, 모드) 조합** — 확정(룰북 B5)

- 계획(`planned_cases` × `planned_modes`) 밖 조합의 줄은 입력 오류다(2회차부터).
- 계획됐는데 줄이 없는 조합은 거부하지 않는다. 그 조합은 미실행으로 대표·보조 지표의 분모에 실패로 남는다(룰북 B5 "실패·시간 초과·무효 실행도 분모에 남김", 자료 계약 §8.2의 분모는 고정 사례 목록). 거부하면 미실행을 분모에 남길 수 없고, 봉인 묶음에서는 빠진 사례만 골라 다시 돌리는 일(B5가 금지)로 이어진다. 분모는 요약(`scorer_summary`)이 센다. 결과 기록 `scorer_results`는 실행 1건에 한 줄이라 미실행 조합의 줄이 없다. 내려받기 누락처럼 파이프라인 결함으로 빠진 줄은 실행 조건 입력 파일의 기대 줄 수·사례 폴더 수 대조로 막는다(F1 전 보완 목록).
- 같은 조합의 줄이 둘 이상이면 B5의 재실행 모양만 받는다: 실행명 시각 순으로 `FAILED` 한 줄 뒤 재실행 한 줄. 줄이 셋 이상이거나 앞 줄이 `FAILED`가 아니면(`COMPLETED`·`TIMEOUT` 뒤의 줄, `COMPLETED` 뒤의 `FAILED`) 입력 오류다. 결과를 보고 고른 재실행이 점수에 들어가지 않게 한다(Codex 검토 2회차 막는 지적 1 가운데 중복 부분, 평가 방법론 검토 2회차 권고 2). 원인이 인프라 오류뿐인지는 원인 분류(단위 L3)가 정해진 뒤 본다(F1 전).
- 보고서의 `run_id`·`case_id`·`mode`가 묶음 줄과 다르면 보고서 단위 실패가 아니라 묶음 전체가 입력 오류로 멈춘다(1회차부터). 실행 폴더가 뒤섞였으면 어느 보고서가 어느 실행의 것인지 믿을 수 없으므로 채점하지 않는 쪽(확인할 수 없으면 멈추는 방식)을 골랐다. 봉인 묶음이 이 이유로 멈춘 뒤의 처리(다시 채점할 수 있는지)는 룰북 B6과 평가 스킬 ②를 따른다(보안 검토 2회차 권고 2).

⑰ **봉인 자리 판정** — 확정(자료 계약 §10.3 N10)

- `<run_dir>`가 봉인 묶음 자리인지는 이름이 아니라 파일 시스템의 같음(`os.path.samefile`, 장치·inode)으로 본다. 부모 폴더가 `outputs/sealed`이거나(대소문자 변형·링크 포함), 인자가 심볼릭 링크이고 그 대상의 부모가 `outputs/sealed`이거나, 저장소 뿌리 뒤 경로 조각에 `sealed`(대소문자 무시)가 있으면 봉인으로 보고, 인자 오류도 끝 상태만 낸다(고정 문구도 오류 출력에 내지 않는다, 보안 검토 2회차 권고 1). 알 수 없으면 봉인으로 본다.
- 받는 자리는 그대로 `outputs/{실행명}/`과 `outputs/sealed/{실행명}/`이다. `outputs/sealed/../{실행명}`처럼 봉인 자리를 지나 개발 자리로 풀리는 경로는 받지 않는다.

## 검토한 대안

- ② 실자료에 거짓이나 참을 적는 안: 거짓은 "필수 근거 실패"로 읽히고 참은 공허한 참이라 버렸다.
- ③ 정답표에 판정 근거(basis)를 신호마다 적고 그에 따라 빠진 키 범위를 고르는 안: 형식이 커지고 DT5가 따라야 할 약속이 늘어 버렸다. 빠진 키가 없을 때의 대체 조건(④)으로 같은 사례를 채울 수 있다.
- ④ 빠진 키가 없으면 `missingness_listed`를 해당 없음(참)으로 보는 안: 공허한 참이라 버렸다. 정답표가 그 코드를 적지 않게 하는 안: 판정 정책 P5가 자료 부족 판정에 늘 요구하므로 정답표와 정책이 갈려 버렸다.
- ⑥ 상대국·HS6·월이 각각 스냅샷 어딘가에 있으면 계획 안으로 보는 1회차 구현: 계획 밖 조합을 계획 안으로 보아 `WRONG_VALUE`를 내서 버렸다(Codex 검토).
- ⑦ 어느 상태를 적어도 `WRONG_VALUE`로 두는 1회차 구현: 뜻이 맞는 `UNRESOLVED_ZERO`를 수치 오류로 세고, 계획 밖 키를 `UNSUPPORTED`로 보는 룰북 B3-1과 결이 달라 버렸다.
- ⑧ 스냅샷에 그 버전의 행이 없으면 저장소 CSV로 채우는 안: 출처가 둘이 되어 자료 접근층 `peers()`와 갈릴 수 있어 버렸다.
- ⑬ 상한 밖 수를 보고서 단위 실패로 보는 안: 다른 해석 불가 값(문자열 값 등)과 달라져 claim 단위로 두었다. 보고서마다 모든 예외를 잡아 실패로 세는 안: 봉인 묶음에서 채점기 결함이 조용히 보고서 실패로 바뀌므로 버렸다(입력 오류·중첩 오류만 보고서 실패로 센다).
- ⑮ 패턴을 그대로 두고 보고서 크기 상한만 두는 안: 1 MiB 공백에서도 이차 역추적이 몇 시간 걸려 버렸다.
- ⑯ 계획된 조합이 묶음 기록에 모두 있어야 받는 안(Codex 검토 2회차): 미실행을 분모에 실패로 남기라는 룰북 B5와 충돌해 버렸다. 중복 거부만 받았다.
- ⑯ 보고서의 식별자가 묶음 줄과 다르면 그 보고서만 실패로 세는 안: 뒤섞인 폴더에서 다른 실행의 보고서가 점수에 들어갈 수 있어 버렸다.

## 영향과 넘길 곳

- DT5(시나리오 명세·dev20)·DT6(holdout40): 정답표를 ③의 형식으로 만든다. 코드는 판정 근거에 맞게 고른다(④ 표 아래). `DEV20_ANSWERS`는 정해졌다(③). 두 신호가 모두 발동한 dev20 사례의 `required_evidence`는 신호별 객체로 적는다(③). 봉인 파일 이름(`SEALED_FILES`)은 정해지면 오케스트레이터가 알린다.
- MT1(D17): 공개 판정 조건 표를 ④와 맞춘다. HOLD를 사유별로 나누면 ④의 대체 조건을 다시 본다.
- MT3(검증기): ⑦의 해석, ⑫의 `flow`(수입 행만) 확인, `ALL` HS6 `OBSERVED` 근거, 상대국 HS10 키의 HS4 행 불가를 같게 맞춘다.
- DT1(자료 접근층): 근거 ID `rowid_of`에도 19자리 상한을 둔다(⑨). ⑦이 확정되면 자료 접근층의 빠진 HS10 표시를 맞춘다. `g0`를 적재한 빌드를 정본 자리에 옮긴다(⑧의 주의).
- MT7(평가 묶음): ⑤의 형식을 F1 전에 확정한다. 봉인 묶음 요약의 룰북 B7 0절 값(한도·순서 seed·동시성·실행 기간·정규화 해시와 대조·`g0` 사유·재현 명령)을 필수로 올리는 일, 인프라 실패 재실행 줄의 룰북 B5 조건 확인, 내려받은 사례 폴더 수 대조는 F1 전 보완 목록에 있다.
- 사용자 확인(오케스트레이터가 올린다): ② 실자료 `null`, ⑦ 값 행도 상태 행도 없는 계획 키의 상태.
- 평가 스킬 ②·결과표(로드맵 R1): 분모는 요약에서만 읽는다(⑯, `scorer_results`에는 미실행 조합의 줄이 없다).

## F1 전 보완 목록(수정 3회차 기준, 결정 D17)

1. 산문 패턴 누락·오탐 보강(`real_dev` 결과로만): 억·만 복합 금액, 톤당 단가를 환산하지 않는다는 해석, MT3 결정 ⑰의 EX 보강 셋.
2. 승격 규칙 독립 구현(`policy_v1` 승인 뒤).
3. 부모-하위 중량 허용오차를 `policy_v1` 값(`tolerance.weight_rounding_kg`)으로.
4. 상태 변화 집계(단위 L1 trace 형식 뒤), 발동 신호별 주장 요건 미충족 `INVALID` 건수(단위 L3 뒤).
5. 실행 조건 입력 파일 형식 확정(MT7, ⑤). 봉인 필수 값의 내용 검사(사전 점검·출처 확인 값이 통과인지, ⑤)를 함께 정한다.
6. `SEALED_FILES`(DT6·DT7), `BATCH_DOMAINS`(MT7), `REPORT_DOMAIN`(AS3).
7. 실자료 `required_evidence_ok`(②, 사용자 확인).
8. 재실행 줄의 원인이 인프라 오류뿐인지 확인(⑯, 단위 L3 뒤). 줄 모양 검사는 3회차에 했다.
9. 봉인 묶음 필수 값에 룰북 B7 0절 값(한도·순서 seed·동시성·실행 기간·정규화 해시와 대조·`g0` 사유·재현 명령) 추가.
10. `normalized_sha256_check` 강제: 값이 있는데 "일치"가 아니면 멈추고, 실자료·봉인 묶음은 "일치" 필수. 봉인 묶음을 채점하기 전에 닫는다.
11. 내려받은 사례 폴더 수(와 기대 줄 수)를 실행 조건 입력 파일에 넣고 실제 수와 대조(⑯).
12. `COMPLETED` 묶음 줄의 `review_status_final`·`signal_status`·`unresolved_evidence`를 보고서 값과 대조.
13. 요약 빈칸: 보조 지표의 Wilson 비겹침 판정 줄, 모델 요청 중앙값·범위, "LLM 추가 가치 미확인" 문장, 짝 분석 순서 고정.
14. Newcombe 공개 참조값 시험, 패턴 목록 지문 값 고정(⑮).
15. 실자료 사례 `case_id`(`{hs6}-{partner}-{month}`)를 풀어 `planned_cases`와 대조.
16. 결과 기록 `errors` 필드의 로컬 절대경로 검사.
17. 봉인 묶음은 실행 조건 입력 파일에 `snapshot.file`이나 기대 `snapshot_id`를 필수로 하고 묶음 줄과 대조.
18. 경계 시험의 금지 토큰 우회 여섯 모양을 채점기 닫힘에서 위반으로.
19. 봉인 폴더 값이 절대경로가 아니거나 저장소 안이면 거부.
20. EX-3 claim_id 빼기의 악용(claim_id를 숫자 표현과 같게 적기): 식별자 모양 제한을 룰북에 넣을지.
21. MT3와 맞출 것: 자료 상태 근거 행의 `flow`(수입) 확인, `ALL` HS6 `OBSERVED` 근거, ⑦의 해석, ⑫의 섞인 상태 해석.
22. DT1 `rowid_of` 19자리 상한(⑨).
23. HS10 직접 조회(`collection_plan.hs10`)가 준 행을 하위 행 색인에 넣을지(지금은 넣지 않지만 계획 대조는 그 요청을 센다. v2는 `hs10: []`라 영향 없음).
