# AS2 코드 PR: 필수 근거 주장을 코드가 덧붙임(사용자 결정 1809의 코드 쪽)

2026-09-25(금) 18:09 사용자 결정(`20260925-1809-user-decision-evidence-claims.md`, 문서 PR DOCS6이 `main`에 넣는다)을 흐름 조정 코드와 시험에 옮긴 기록이다. 명세는 그 기록의 결정 ①~④이고, 여기서는 코드에서 정한 세부만 적는다.

용어

- 필수 근거: 보고서가 어떤 판정 상태를 내려면 남겨야 하는 근거. 이름 13개는 판정 정책 단위 P5(`policy_required_evidence`)의 어휘이고, "남겼다"고 보는 조건은 시나리오 명세 `eval/scenarios/SCENARIO_SPEC.md` §5.3 판정 조건표다.
- typed claim: 보고서의 정해진 필드(`claim_type`·`hs6`·`partner`·`period`·`baseline_period`·`metric`·`value`·`unit`·`evidence_ids` 등)를 가진 사실 주장(자료 계약 §6).
- 규칙 참고값: 판정 정책 단위 P3(신호별 판정)을 코드가 돌린 결과(신호별 상태와 판정 근거 basis). 모델 상태를 덮어쓰지 않는 참고값이다(MT1 결정 ⑬).
- 봉투: 도구 5개가 돌려주는 조회 결과 객체(자료 계약 §5). 검증된 지표(`metrics`)와 빠진 자료(`missingness`)를 담는다.

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 18:30(기록 시각). 바탕은 `main` 690f3eb. Codex 교차 검토 1회차 막음 세 가지(부모·하위 대조의 행 범위, 빠진 자료 상태의 두 시점·WRONG_VALUE, 비교국 상태 범위)를 같은 날 고쳤고, 고친 뒤 dev20 기록 재적용 결과는 아래와 같다 |
| 제목 | 보고서를 만들 때 필수 근거 코드마다 §5.3 조건을 보고, 없으면 받은 봉투의 검증된 지표·자료 상태로 주장을 덧붙임 |
| 결정 | 아래 ①~⑥ |
| 결정 주체 | 규칙은 사용자(결정 1809). 코드의 세부는 소유 트랙(M) |
| 공용 약속 여부 | 규칙 자체는 공용 약속이고 사용자 결정 1809가 승인이다. 판정 정책·검증기·지표·채점기의 판정 규칙, 원인 분류 코드, 실행 결과 기록 키, 보고서 필드, 도구·모델 예산은 바꾸지 않았다. 계획 문서는 문서 PR(DOCS6)이 고친다 |
| 관련 PR | 브랜치 `model/AS2-evidence-claims` |

## 까닭

- V1(MVP 시험) dev20 묶음(`evaluate-260925163949`)에서 판정 상태는 거의 맞았는데 채점기의 필수 근거 검사가 많이 떨어졌다. 모델은 주장을 한두 개만 넣고, `checklist` 규칙은 비교월 지표만 골라 기준월 금액(`country_and_world_change_shown`)을 빠뜨렸다 `[사실: 결정 1809 배경]`.

## 결정 내용

① **어디서(단위 I12 `src/tradesentry/workflow/orchestrate.py`)** — 보고서를 만드는 자리 `_Flow.build` 하나에서 한다. 초안 보고서(Critic 앞 스키마 검사와 verify 단계가 같은 보고서를 쓴다), 수정본 보고서(final), `checklist` 보고서가 모두 이 자리를 지나므로 모든 모드·모든 단계에 같은 규칙이다. 덧붙이기는 `unit_ports`의 `build_report` 안에서 단위 R1이 만든 주장 뒤에 붙인다. 모델(또는 `checklist` 규칙)의 판정·주장·설명·가설은 그대로다.

② **어느 코드를(`evidence_codes`)** — 발동한 신호마다 초안의 신호별 판정이 규칙 참고값의 판정과 같으면 그 판정 근거(basis)의 P5 목록, 다르거나 참고값이 없으면 그 판정 상태를 내는 P5 규칙 목록을 모두 합친 것(규칙표 순서, 겹치지 않게)이다. 판정이 값 집합 밖이면 빈 목록이다. 참고값은 새 자리 `Ports.evidence_reference`로 받는다. `unit_ports`가 근거 상태 변환과 정책을 받았을 때(조립 `run-case`·`evaluate`) 모델에게 싣는 참고값(`reference_status`)과 같은 계산을 넘긴다. 자리를 나눈 까닭: `checklist`에도 써야 하고, 모델에게 싣는 참고값 문구의 계산 횟수·시점을 바꾸지 않으려고 `[추론: 기존 참고값 시험이 계산 횟수를 본다]`. 참고값 계산이 입력 검사 오류(ValueError)면 참고값 없음으로 두고, 배선 오류는 참고값 규칙처럼 `CODE_ERROR`로 올린다.

③ **채울지의 판정(§5.3을 런타임 안에서 따로 구현, `_EvidenceView`)** — 채점기(`eval/scorer`)는 import하지 않는다(경계 시험). 검증기 R3에는 이 표의 구현이 없어(R3는 필수 근거를 보지 않는다) 흐름 조정에 두었다. 받은 봉투의 검증된 지표와 자료 상태를 단위 R1 틀 채우기(`fill`)로 typed claim 후보로 만들고, 보고서 주장이 "유효"한지는 대상(`claim_type`·`metric`·`hs6`·`partner`·`period`·`baseline_period`, 자료 상태는 월까지)이 같은 후보가 있고 그 후보의 근거를 모두 인용했는지로 본다(값의 참·거짓은 보지 않는다. §5.3 "유효한 claim"). 코드별 규칙:

| 코드 | 채우는 선택지(앞의 것부터) |
|---|---|
| `comparability_ok` | 단가: 대상국 `r_U` 변화 주장, 없으면 두 시점 `U`. 점유율: `d_s`, 없으면 두 시점 `s` |
| `partner_comparison_done` | `compare_partners` 봉투가 돌려준 비교국(스냅샷 비교 대상 표, 실행의 `grouping_version`. 채점기의 비교집합과 같은 표) 가운데 가나다순 첫 나라의 `comparison` 주장: 단가 `r_U`나 두 시점 `U`, 점유율 `d_s`나 두 시점 `s` |
| `weight_share_decomposition` | 분해 셋(`within_effect`·`mix_effect`·`residual`) 모두 |
| `per_child_unit_value_stable` | `decompose_hs` 봉투 `comparability.hs10`의 두 시점 하위 코드마다 `r_U@코드`나 두 시점 `U@코드`. 코드 하나라도 채울 수 없으면 덧붙이지 않는다 |
| `parent_child_match_V_and_Q` | 두 시점 모두 하위 코드가 있을 때, 시점마다 대상국 부모 HS6 행 묶음(그 월 대상국 `V` 지표의 근거, 없으면 `Q`·`U`)과 그 시점 하위 코드마다의 행 묶음(`decompose_hs`의 그 월 `U@코드` 지표 근거. 값이 없어도 근거는 있다)을 묶음마다 하나 이상 보고서 근거가 인용하도록, 새로 덮는 묶음이 가장 많은 후보부터 고른다(대상국·두 시점 지표). 봉투의 다른 행은 요구하지 않는다. 다 덮지 못하면 덧붙이지 않는다(Codex 검토 1회차로 고침: 처음에는 봉투의 상태 행 밖 모든 행을 요구했다) |
| `precision_sensitivity_shown` | 대상국 두 시점 `V`·`Q` 값 주장 넷 |
| `country_and_world_change_shown` | 대상국과 `ALL`의 두 시점 `V` 값 주장 넷 |
| `missingness_listed`, `failure_vs_not_collected_distinguished` | 빠진 키(단가: 대상국 부모 HS6 키와 C형 HS10 하위 자료, 점유율: 대상국 부모 HS6 키와 `ALL`, 두 시점 각각. HS6 키는 그 월 관측 값 지표나 `OBSERVED` 상태가 있으면 빠진 키가 아니다)마다 받은 자료 상태 주장 하나. `failure_vs_not_collected_distinguished`는 여기에 더해 사례 품목·두 시점의 자료 상태 주장 가운데 받은 상태와 값이 다른 것(WRONG_VALUE)이 없어야 한다(있으면 모델 주장을 고치지 않으므로 unmet). 빠진 키가 없으면 `missingness_listed`는 비교국 자료 상태 하나(`compare_partners` 봉투의 빠진 자료에서 온 비교국 자신의 상태 행, 사례 품목 HS6 수준, 두 시점, `OBSERVED` 아님) 또는 계산할 수 없는 계열 지표(단가 V·Q·U·r_U·w·분해 셋, 점유율 V·s·d_s. 대상국, 점유율은 `ALL`도, 두 시점 가운데 하나)를 null로 맞게 적은 주장(값 null, 대상이 같은 계산 불가 지표의 근거를 모두 인용, 계약 단위, 변화가 아닌 기호는 방향 NA)이 있으면 채운 것으로 본다. 덧붙일 때는 비교국 상태를 먼저 쓰고, 없으면 받은 계산 불가 지표 가운데 변화가 아닌 기호의 첫 것을 값 null 주장으로 덧붙인다(R1은 계산 불가 지표를 주장으로 만들지 않으므로 흐름 조정이 대상·단위·근거를 옮기고 숫자 없는 문장을 쓴다. 변화 기호는 null 값에 방향을 정할 수 없어 덧붙이지 않는다. Codex 검토 2회차로 더함), `failure_vs_not_collected_distinguished`는 WRONG_VALUE가 없으면 채운다(Codex 검토 1회차로 고침: 처음에는 빠진 키가 있을 때 WRONG_VALUE를 보지 않았고, 비교국 상태의 출처·수준을 좁히지 않았다) |
| `no_zero_fill`, 교정 근거 셋 | 덧붙일 것이 없다(부정 조건, v1에서 판정하지 않는 코드). trace에 `no_action`으로 남긴다 |

- 여러 대상이 필요한 선택지는 모두 채울 수 있을 때만 덧붙인다(일부만 넣으면 조건을 채우지 못한다).
- 받은 근거에 없는 대상(값이 없는 지표 포함. R1이 버린다)은 덧붙이지 않는다. 도구를 새로 부르지 않는다.
- 같은 대상의 주장이 이미 있으면(유효하지 않아도, 예: freeform 주장이 근거를 덜 인용함) 다시 넣지 않고 다른 선택지를 본다. 코드·신호 사이에서도 같은 대상은 한 번만 넣는다(예: 대상국 `V`는 `precision_sensitivity_shown`과 `country_and_world_change_shown`에 함께 쓰인다).
- 덧붙인 뒤 검증기 R3의 자료 상태 어긋남 규칙(`DATA_STATUS_CONFLICT`, R3의 `_data_status_conflicts`를 그대로 부른다)이 늘어나면 그 묶음은 넣지 않는다. 덧붙인 주장이 검증기 차단을 새로 만들지 않게 하려는 것이다. R3의 비공개 함수를 다른 단위에서 부르는 것은 같은 규칙을 두 곳에 두지 않으려는 것이다. 공개 이름으로 바꾸려면 R3 머리 주석·시험을 함께 고쳐야 해서 이 PR에서는 그대로 두었다(조립 점검 때 공개 이름으로 옮길 후보).

④ **주장 모양** — 덧붙인 주장은 단위 R1 틀 채우기가 검증된 지표·자료 상태에서 만든 typed claim이다(값·단위·방향·문장을 R1이 채운다). `freeform`에서도 같다: 모델 주장은 R1 freeform이 그대로 돌려주고, 덧붙일 주장은 R1의 `fill`을 한 번 더 불러 채운다. R1은 고치지 않았다(두 형식을 한 호출에 받지는 않지만, 두 번 불러 합치면 된다 `[추론]`). `claim_id`는 `e1`, `e2` …이고 보고서에 이미 있는 id는 건너뛴다. 주장 개수 상한은 스키마·검증기에 없다 `[사실: validate.py·investigator.py 검색]`.

⑤ **verify_evidence 인자** — 초안이 가리킨 근거(`_draft_refs`)만 넘기고 덧붙인 주장은 넣지 않는다. 덧붙인 주장은 이미 받은 봉투의 검증된 지표이고, 검증기 R3가 봉투 전체의 지표·근거로 숫자와 출처를 본다 `[사실: validate.py _context·_collect_returned]`. 인자를 바꾸면 기록 재생(단위 I8)이 인자 해시로 도구 호출을 대조해 기존 기록과 어긋난다 `[추론]`.

⑥ **trace** — 새 사건 종류 없이 `state_change`의 새 phase `evidence_claims`를 보고서를 만들 때마다 그 보고서의 `validator_result` 앞에 남긴다: `review_status`·`signal_status`(그 초안의 것), `required`({신호: 코드}), `added`([{`signal`, `code`, `claims`: 요청 모양 목록}]), `unmet`([{`signal`, `code`}]: 받은 근거로 채울 수 없음), `no_action`. 요청 모양은 `checklist_claims`와 같은 `{"claim_id", "claim_type", "metric_id"}` 또는 `{"claim_id", "claim_type": "data_status", "evidence_id"}`다. `phase`로 가르는 소비자(NAT 감싸기·추출·요약)는 없다 `[사실: grep]`.

## 시험

- `tests/units/I12/test_evidence_claims.py`(31개. Codex 검토 2회차 뒤 6개 더함: 비교국 상태 없이 null 주장만으로 충족, null 주장이 맞지 않으면(근거·단위·방향·월) 세지 않음, 둘 다 없으면 unmet, 받은 계산 불가 지표를 null 주장으로 덧붙임, 비교국 상태가 있으면 그것을 먼저, 점유율의 ALL null 주장(단가 계열은 세지 않음). 그 전 25개: Codex 검토 1회차 뒤 8개 더함: 두 시점 빠진 키 모두 요구, 틀린 모델 상태면 unmet, 관측된 키의 요청 상태 행은 빠진 키 아님, 비교국 상태의 범위(비교국 밖·HS10 수준·다른 도구 거부), 여러 비교국 가운데 첫 유효 후보, 부모·하위 대조에 쓰지 않는 행 요구 안 함·한 시점만 하위가 있으면 unmet, 판정 코드 고르기의 합집합·비발동 신호): 코드 고르기(참고값과 같음·다름·없음), 코드마다 덧붙인 대상과 덧붙인 뒤 다시 보면 채워짐(단가·점유율 `comparability_ok`·`partner_comparison_done`, 분해, 하위 안정, 부모·하위 대조, 정밀도, 해당국·전체국가), 받은 근거에 없거나 값이 없으면 덧붙이지 않음, 덧붙일 것이 없는 코드, 모델 주장 불변, 같은 대상 한 번, `claim_id` 건너뛰기, freeform 주장이 차지한 대상, 자료 상태(빠진 키·비교국·값 주장과 어긋나면 넣지 않음), 흐름에서 네 모드(`agent`·`full`·`freeform`·`checklist`, 실제 R1·R2) 모두 덧붙이고 trace에 남김, `checklist`의 `country_and_world_change_shown`, 수정 단계가 있으면 두 보고서 모두.
- 골든 I12: trace 사건 목록에 `state_change` `evidence_claims` 한 줄이 초안 보고서의 `validator_result` 앞에 생겼다(골든 봉투에는 덧붙일 지표가 없어 보고서는 그대로). 기대값을 그 한 줄만 고쳤다.

## 시험 밖 점검(dev20 기록 재적용)

V1 dev20 묶음(`outputs/evaluate-260925163949`)의 `COMPLETED` 실행 45건의 최종 보고서에 기록된 봉투로 덧붙이기를 적용하고, 채점기(`eval/scorer`)의 필수 근거 판정과 검증기 R3로 본 결과다(실행 기록은 읽기만 했다. 끝까지 돌지 못한 실행은 다시 보지 않았다. 흐름을 다시 돈 것이 아니라 최종 보고서에 규칙을 적용한 것이다).

| 모드 | 적용 전 `required_evidence_ok` | 적용 뒤 |
|---|---|---|
| `checklist` | 12/20 | 19/20 |
| `agent` | 2/17 | 16/17 |
| `full` | 0/8 | 6/8 |

- 검증기 R3 findings는 45건 모두 늘지 않았다.
- 남은 4건: 3건은 `precision_sensitivity_shown`(사례 `850490-XP-202309`, 세 모드). 도구가 부모 `Q`(중량) 지표를 돌려주지 않아 받은 근거로 채울 수 없다(`get_history` 지표에 `Q`가 없다). 1건(`full` `850431-XQ-202401`)은 모델 판정이 참고값과 달라 그 판정(`MONITOR`)의 코드 목록에 `partner_comparison_done`이 없다(규칙 ②대로).

- 채점기 `numeric_ok`·`provenance_ok`는 45건 모두 적용 전과 같았다(모두 참). 기록된 `real_dev` `run_case` 6건(`full` 3, `freeform` 3)에서도 떨어진 실행은 없었다. 다만 `freeform` 1건(`850490-FI-202402`)은 덧붙인 주장이 모델 산문의 숫자를 뒷받침해 `numeric_ok`가 거짓에서 참으로 바뀌고 검증기 `PROSE_UNBACKED` 2건이 사라졌다.

## 남은 것

- 덧붙인 주장은 산문 검사(룰북 B3-2)에서 산문 숫자를 뒷받침할 수 있다. 그래서 대표 지표(실자료 보고서 단위 오류율)가 "더한 주장이 맞는 한 그대로"가 아니라 오를 수 있고, `full`·`agent`에서는 검증기 차단이 풀려 수정 단계가 줄 수 있다(위 `real_dev` 1건). 사용자에게 알릴지는 오케스트레이터가 정한다.
- Critic은 덧붙이기 전 초안을 본다. 코드가 덧붙일 근거를 이유로 수정을 요청해 모델 요청이 늘 수 있다(재지 않았다).
- 결정 1809 ④의 "결과 요약에 모드별로 공개"(덧붙인 주장 수 등)는 이 PR에 없다. 실행 결과 기록 키를 바꾸지 않으므로 trace `evidence_claims`에서 모아 요약에 싣는 일이 남는다(묶음 요약·제출서 쪽, 오케스트레이터가 맡길 곳을 정한다).
- `precision_sensitivity_shown`을 채우려면 도구가 부모 `Q`를 지표로 돌려줘야 한다(도구 봉투 변경은 이 PR 범위 밖).
- 병합 뒤 샌드박스를 다시 굽고 dev20·`real_dev`를 다시 돈다(결정 1809 ⑤).
