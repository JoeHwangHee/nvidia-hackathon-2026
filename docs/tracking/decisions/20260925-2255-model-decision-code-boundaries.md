# AS2 코드 PR: 코드 경계 셋(review_status 코드 집계, 발동 신호 자기 계열 주장 덧붙이기, HOLD 합의 신호엔 빠진 도구 지적 없음)

2026-09-25(금) 22:22 사용자 결정(`20260925-2225-user-decision-code-boundaries.md`, 문서 PR DOCS8이 `main`에 넣는다)의 결정 ①②③⑦ 가운데 코드 쪽 ①②③을 흐름 조정 코드와 시험에 옮긴 기록이다. 명세는 그 기록이고, 여기서는 코드에서 정한 세부만 적는다. ④(Retry-After(다시 시도할 때까지 기다릴 시간을 알려 주는 응답 헤더) 존중)는 다른 코드 PR(브랜치 `model/AS3-retry-after`)이 맡는다.

용어

- 신호별 판정(`signal_status`): 단가(`unit_value`)·점유율(`share`) 신호마다 모델이 적는 판정 상태. 사례 판정(`review_status`)은 이것의 집계다(자료 계약 §3.1).
- 규칙 참고값: 판정 정책 단위 P3(신호별 판정)을 코드가 돌린 결과(신호별 상태와 판정 근거 basis). 모델 상태를 덮어쓰지 않는 참고값이다(MT1 결정 ⑬).
- 코드 지적(`code_finding`): 초안 전에 받아야 하는 필수 도구(비교국 비교 `compare_partners`, 단가 신호의 HS10 분해 `decompose_hs`)가 빠졌다고 흐름 조정이 Critic 결과(agent는 수정 지시)에 덧붙이는 지적(AS2 결정 기록 ⑲).
- 흐름 수정 (나): Critic의 수정 요구만으로 연 수정 단계의 수정본이 최종 검사에서 막히면 수정 전 초안의 보고서로 끝내는 규칙(AS2 결정 기록 ㉔, trace `revision_discarded`).
- 계열 주장: 발동한 신호의 계열(단가: U·r_U·w·분해 셋, 점유율: s·d_s) 지표를 사례 대상(품목·상대국·비교월)에 대해 적은 주장. 없으면 검증기 R3가 `SCHEMA_SIGNAL_CLAIM`으로 모든 모드에서 막는다(자료 계약 §9.4).

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 22:55(기록 시각). 바탕은 `main` 3f1832a. 코드 커밋 345aa69 |
| 제목 | 보고서를 만들 때 코드가 `review_status`·`unresolved_evidence`를 집계값으로 채우고, 계열 주장이 없는 발동 신호에 변화 지표 주장을 덧붙이고, HOLD 합의 신호의 빠진 도구는 지적하지 않음 |
| 결정 | 아래 ①~⑤ |
| 결정 주체 | 규칙은 사용자(결정 2225). 코드의 세부는 소유 트랙(M) |
| 공용 약속 여부 | 규칙 자체는 공용 약속이고 사용자 결정 2225가 승인이다. 판정 정책·검증기·채점기의 판정 규칙, 원인 분류 코드, 실행 결과 기록 키, 보고서 필드, 도구·모델 예산은 바꾸지 않았다. 검증기 R3는 기대값 계산만 공개 함수로 빼고 판정 규칙·사유 문구는 그대로다. 계획 문서·룰북(B2·B7)은 문서 PR(DOCS8)이 고친다 |
| 관련 PR | 브랜치 `model/AS2-code-boundaries` |

## 까닭

- V1(MVP 시험) 3차에서 보고서를 못 낸 실행 9건 가운데 `review_status` 집계 불일치 1건(dev20 `850431-XP-202412`), 발동 신호 자기 계열 주장 누락 1건(dev20 `850432-XP-202408`), HOLD 초안에 `compare_partners` 빠짐 지적으로 수정이 열려 흐름 수정 (나)가 적용되지 않은 2건(`real_dev` `850432-US-202409`·`850431-MX-202305`)이 있었다 `[사실: 결정 2225 배경]`.

## 결정 내용

① **`review_status` 코드 집계(단위 I12 `src/tradesentry/workflow/orchestrate.py` `_Flow.aggregated`, 단위 R3 `src/tradesentry/validator/validate.py` `aggregate_status`)** — 보고서를 만드는 자리 `_Flow.build` 하나에서(초안·verify·final 보고서, 네 모드 모두) 초안의 `signal_status`로 자료 계약 §3.1 규칙(`MAINTAIN` > `HOLD` > `MONITOR`, `unresolved_evidence`는 `MAINTAIN`과 `HOLD`가 섞일 때만 true)을 계산해 `review_status`·`unresolved_evidence`를 채운 초안 사본을 `build_report`에 넘긴다.

- 계산은 검증기 R3가 `STATUS_INCONSISTENT`의 기대값을 세던 코드를 공개 함수 `validate.aggregate_status(signal_status, signals)`로 빼서 두 곳이 함께 쓴다(R3 `_status_consistency`는 이 함수를 부르고, 판정 규칙·사유 문구는 그대로). 발동한 신호의 판정에서 `NOT_TRIGGERED`는 세지 않고, 발동하지 않은 신호의 (틀린) 판정도 세지 않는다(R3와 같다).
- 손대지 않는 때: `signal_status`가 두 신호 키에 허용 값(`MAINTAIN`·`MONITOR`·`HOLD`·`NOT_TRIGGERED`)이 아니거나, 발동한 신호의 판정이 하나도 없을 때(초안 형식 검사·스키마 검사가 맡는다). `signal_status`·주장·설명·가설은 바꾸지 않는다.
- trace: 모델(또는 `checklist` 규칙)이 쓴 값과 달라졌을 때만 `state_change` phase `status_aggregated`(`review_status`·`signal_status`는 집계한 초안의 것, `model_review_status`, `model_unresolved_evidence`, `unresolved_evidence`)를 그 보고서의 `evidence_claims` 앞(초안이면 `draft` 사건 뒤)에 남긴다. "달라졌다"는 `review_status`가 다르거나, 모델이 `unresolved_evidence`를 참거짓으로 적었는데 집계와 다를 때다. 조사자 초안 형식(`DRAFT_KEYS`)에는 `unresolved_evidence`가 없어 모델 모드에서 `model_unresolved_evidence`는 보통 null이다 `[사실: investigator.DRAFT_KEYS]`. `draft`·`after_critic`·`revised`·`revision_discarded` 사건의 `review_status`는 모델 값 그대로다(집계 전후를 가를 수 있게).
- 결과: `checklist`는 이미 P4로 집계하므로 값이 같고 사건도 남지 않는다(시험). 모델 모드에서 검증기 R3의 `STATUS_INCONSISTENT`는 `review_status`·`unresolved_evidence` 경로에서는 더 나지 않고 `signal_status` 경로(발동하지 않은 신호에 판정을 적음, 발동한 신호에 `NOT_TRIGGERED`)만 남는다. `build_report`가 P4로 세던 `unresolved_evidence`는 같은 값이라 그대로 두었다.
- 결정 ⑦(결과 요약 공개 항목 "코드가 `review_status`를 집계 값으로 바꾼 보고서 수(모드별)")은 이 trace 사건을 세면 된다. 세는 코드는 이 PR에 없다(실행 결과 기록 키를 바꾸지 않았다. 묶음 요약 쪽 후속).

② **발동 신호 자기 계열 주장 덧붙이기(`orchestrate.signal_claims`, `_EvidenceView.signal_claim`)** — `unit_ports`의 `build_report`에서 필수 근거 덧붙이기(`evidence_claims`, 결정 기록 `20260925-1830-model-decision-evidence-claims.md`) 바로 뒤에 같은 자리에서 한다. 발동한 신호마다 보고서 주장(모델 주장 + 필수 근거로 덧붙인 주장) 가운데 형식이 맞는 것(R3 `claim_problems`가 비는 주장. R3의 `valid`와 같은 범위)에 대해 R3 `signal_families`를 그대로 불러 그 계열이 채워졌는지 보고, 없으면 그 신호의 변화 지표(`unit_value` → `r_U`, `share` → `d_s`. 사례 hs6·상대국·비교월 대 기준월) 후보를 받은 봉투의 검증된 지표에서 단위 R1 틀 채우기로 골라 덧붙인다.

- 받은 근거에 없으면(값이 null인 지표 포함. R1이 버린다) 덧붙이지 않는다. 도구를 새로 부르지 않는다. 같은 대상(같은 `metric_id`가 가리키는 기호·품목·상대국·월·기준월)의 주장이 이미 있으면 유효하지 않아도 다시 넣지 않는다(기존 덧붙임과 같은 규칙 `taken`). `freeform`도 같다(모델 주장은 그대로, 덧붙이는 주장은 R1 `fill`이 검증된 지표로 채운다).
- `claim_id`는 기존 덧붙임과 같은 `_EvidenceView.add`의 번호 규칙(`e{보고서 주장 수 + 1}`부터, 이미 있는 id는 건너뜀)이다. 필수 근거로 덧붙인 주장 뒤에 이어 붙이므로 번호열이 이어진다(덧붙이기 전·뒤 값을 세는 도구는 `e` 접두어로 가른다).
- 요청 모양의 `claim_type`은 R1이 기호로 정한 값이다: `r_U`는 `change`, `d_s`는 `share_change`(작업 지시의 "`claim_type: change`"는 두 변화 지표를 뜻하는 것으로 읽었다 `[해석]`). trace `evidence_claims`의 `added`에 `{"signal": 신호, "code": "signal_claim", "claims": [{claim_id, claim_type, metric_id}]}`로 남는다. `signal_claim`은 P5 코드가 아니라 이 덧붙임을 가르는 이름이고 `required`·`unmet`에는 들지 않는다.
- 이 덧붙임은 검증기 R3 `SCHEMA_SIGNAL_CLAIM`(모든 모드에서 막는 스키마 사유)을 받은 근거로 채울 수 있을 때 미리 채우는 것이다. 값의 참·거짓은 검증기가 그대로 본다.

③ **HOLD 합의 신호엔 빠진 도구 지적 없음(`_Flow.hold_consensus_skips`)** — `model_flow`의 `code_missing` 계산 직후, 초안의 신호별 판정과 규칙 참고값(`reference_for_codes`, P3 출력)이 둘 다 `HOLD`인 발동 신호(HOLD 합의)를 모아, 신호 전용 도구(`SIGNAL_ONLY_TOOLS`의 `decompose_hs`)는 그 신호가 HOLD 합의면, 그 밖의 필수 도구(`compare_partners`)는 발동한 모든 신호가 HOLD 합의일 때 `code_missing`에서 뺀다. 참고값이 None(배선 없음, P3 입력 검사 오류)이거나 판정이 다르면 빼지 않는다.

- 뺀 사실은 `state_change` `code_finding`에 `skipped_for_hold`(뺀 도구 이름 목록)로 함께 남긴다. 지적이 전부 빠져 지적을 내지 않을 때도 같은 사건을 `missing_tools` 빈 목록으로 남긴다(새 사건 종류 없음). 뺄 것이 없으면 `skipped_for_hold`는 빈 목록이고, 빠진 도구가 없으면 사건도 없다(전과 같다).
- `code_missing`이 비면 흐름 수정 (나)의 `kept_draft` 조건(코드 지적이 없음)은 기존 코드 그대로 성립한다. 그래서 Critic 지적만으로 연 수정이 최종 검사에서 막히면 수정 전 초안의 보고서로 `COMPLETED`한다(시험 `test_critic_only_revision_that_is_blocked_falls_back_to_the_kept_draft`).
- 바꾸지 않은 것: 수정 단계의 필수 조회 차례(AS2 ⑲ `pending_tools`)는 그대로 `missing_required_tools`를 보므로, 지적에서 뺀 도구도 수정 단계에서는 "아직 없는 필수 결과"로 세어 `tool_choice` `required` 차례를 연다(그 차례에 온 초안은 ⑱대로 버려지고 도구 없는 초안 차례로 간다). 결정 2225 ③은 "지적 시점만 바꾼다"고 했으므로 범위 밖으로 두었다. 아래 "남은 것".

④ **시험(`tests/units/I12/test_code_boundaries.py` 19개)** — ① 네 조합(MAINTAIN+HOLD→MAINTAIN·true, HOLD+HOLD→HOLD, MONITOR+MONITOR→MONITOR, 한 신호 미발동 HOLD→HOLD)과 R3 `_status_consistency` 대조, trace 네 필드와 위치(draft 뒤·validator_result 앞)와 같을 때는 없음, 세 모델 모드에서 초안·수정본 두 보고서 모두 집계, `checklist` 불변, 형식 불량·미발동 초안 불변(원본도 바꾸지 않음), 공유 함수 값. ② 두 신호 없음→e1·e2 덧붙임과 R3 계열 판정 충족, 있음(변화·수준 주장)→불변, 발동 신호만, 근거에 없음·다른 상대국→없음, 같은 대상(근거 없는·형식 틀린 모델 주장)→없음, 번호 규칙(c1+e1·e2 뒤 e4·e5, 필수 근거 덧붙임과 같은 규칙), 흐름에서 세 모델 모드(점유율 HOLD `data_insufficient`, 모델은 V만 주장)에서 d_s를 마지막에 덧붙이고 trace `signal_claim`, 있으면 흐름에서도 없음. ③ HOLD 합의→세 모델 모드에서 지적 없음·수정 없음·`skipped_for_hold` 둘, 단가만 합의→`decompose_hs`만 빼고 수정에서 `compare_partners`를 부름, 참고값 None·MONITOR 참고값·MONITOR 초안→기존 지적, 빠진 도구 없음→사건 없음, (나)로 완료되는 대본(`revision_discarded`, `budget_block` 없음).

- 갱신한 기존 시험 2개(집계가 어긋난 초안이 코드 집계로 검증기를 통과하므로 기대값이 바뀐다): `tests/units/I12/test_orchestrate.py` `MergedUnitsTest`의 `test_status_mismatch_is_recorded_in_freeform_and_revised_in_full_by_the_real_validator` → `..._is_aggregated_by_code_so_the_real_validator_passes`(freeform·full 모두 `COMPLETED`·HOLD·수정 없음·`status_aggregated` MONITOR→HOLD), `tests/units/F2/test_run_case_command.py` `test_disallowed_status_combination_is_blocked_in_full_and_recorded_in_freeform` → `..._is_aggregated_by_code_in_full_and_freeform`(두 모드 `COMPLETED`·MONITOR, `STATUS_INCONSISTENT` 없음, 종료 코드 0). 대역 `tests/units/I12/harness.py`의 가짜 `build_report`는 초안의 `unresolved_evidence`를 그대로 옮기게 한 줄 고쳤다.
- I12 골든은 바뀌지 않았다(사례 A full의 초안은 집계와 같고 필수 도구가 다 있어 새 사건이 없다). 첫 요청 해시도 그대로다(프롬프트·payload를 바꾸지 않았다).

⑤ **기록된 실행 재적용 점검(시험 밖, 읽기만)** — 메인 폴더 `outputs/`의 trace 세 건에 새 규칙을 손으로 대조했다(흐름을 다시 돈 것이 아니다. Critic·모델의 다음 답은 알 수 없다).

| 실행 | 기록 | 새 규칙이 작용했을 곳 |
|---|---|---|
| `run_case-260925202926`(dev20 `850431-XP-202412`, full) | 첫 `compare_partners`가 허용 밖 비교국으로 `invalid_args` 거부 → 규칙 참고값 계산 불가(`available` false) → 코드 지적 `compare_partners` + Critic 수정 요구 → 수정본 판정 {단가 HOLD, 점유율 MAINTAIN}인데 `review_status` HOLD → 최종 `STATUS_INCONSISTENT`·`PROSE_UNBACKED`로 `INVALID` | ③: 지적 시점의 참고값이 None이라 예외 없음(지적 그대로, `kept_draft` 없음). ①: 최종 보고서의 `review_status`를 MAINTAIN·`unresolved_evidence` true로 고쳐 `STATUS_INCONSISTENT`는 사라지지만 `PROSE_UNBACKED`가 남아 그대로 `INVALID`(산문의 '변화가 없' 문제는 `findings.md`, 문서 PR). ②: 봉투에 r_U(−50.0)·d_s(−11.9)가 있었고 필수 근거 덧붙임(`comparability_ok`)이 이미 두 계열을 채워 추가 없음 |
| `run_case-260925220701`(`real_dev` `850431-MX-202305`, full) | 참고값 {단가 HOLD `data_inconsistent`}, 초안 HOLD(합의). 첫 `compare_partners`가 `KR`로 거부 → 코드 지적 `compare_partners` + Critic 수정 요구 → 수정본이 `PROSE_UNBACKED`로 막혀 `INVALID` | ③: 단가 신호만 발동하고 HOLD 합의라 `compare_partners`를 뺌 → 지적 없음 → Critic 수정 요구만으로 연 수정 → 최종 막힘 → (나)로 수정 전 초안(verify 단계 pass)의 보고서로 `COMPLETED`(HOLD). ①: 변화 없음(HOLD/HOLD 일치). ②: 모델이 U·r_U를 주장해 추가 없음 |
| `run_case-260925204915`(dev20 `850432-XP-202408`, full) | 참고값 {단가 HOLD `data_insufficient`}, 초안 HOLD(합의). 첫 초안이 계열 주장 없이 `SCHEMA_SIGNAL_CLAIM` → Critic 생략 → 수정본도 같은 사유로 `INVALID`(`SCHEMA_INVALID`) | ②: 봉투에 사례 대상 r_U(−40.0, 값 있음)가 있어 첫 초안 보고서에 `change` r_U 주장(e1)을 덧붙여 `SCHEMA_SIGNAL_CLAIM`이 나지 않는다 → Critic으로 진행(그 뒤는 기록에 없다). ③: HOLD 합의라 첫 `compare_partners` 거부에도 지적 없음. ①: 변화 없음 |

## 남은 것

- ③은 지적만 빼고 수정 단계의 필수 조회 차례(`pending_tools`)는 그대로라, HOLD 합의로 지적을 뺀 도구가 Critic 수정 단계에서는 `required` 차례를 한 번 연다(모델 요청 1회와 버린 초안 1건이 늘 수 있다. 시험 `test_unit_value_consensus_alone_skips_only_decompose`가 이 모양을 고정한다). 수정 단계에서도 빼려면 ⑲의 차례 규칙을 고치는 결정이 필요하다.
- ②는 변화 지표(`r_U`·`d_s`)만 덧붙인다. 그 값이 null(계산 불가)이면 채울 수 없어 `SCHEMA_SIGNAL_CLAIM`이 그대로 난다(수준 주장 U·s로 대신 채우는 것은 결정 2225 ②의 문구 밖이라 넣지 않았다).
- ①은 `review_status`가 집계값으로 바뀐 보고서 수를 결과 요약에 공개해야 한다(결정 ⑦). trace `status_aggregated`를 모드별로 세는 코드는 묶음 요약 쪽 후속이다.
- 검증기 R3의 `STATUS_INCONSISTENT`(`review_status`·`unresolved_evidence` 경로)는 모델 모드에서 더 나지 않는다. 룰북·개발 플랜의 서술은 문서 PR(DOCS8)이 맞춘다.
