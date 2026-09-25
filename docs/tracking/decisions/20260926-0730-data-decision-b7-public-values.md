# 룰북 B7 공개 값을 세는 도구의 위치와 계산 규칙(독립 채점기 단위 C4, 실행 추적 읽기만)

룰북 `docs/eval/RULEBOOK.md` B7 결과 요약이 공개하기로 한 값(사용자 결정 1856·1809·2225 ⑦·0105 ③)을 어디서 무엇으로 세는지 정한 데이터 트랙(D) 기록이다. 채점 규칙(정답 대조·산문 패턴·오류율 정의·등급·Wilson 구간)은 바꾸지 않았다. 이미 결정된 공개 값을 채점기가 결정적으로 내게 하는 배관이다.

용어

- 실행 추적(trace): 사례 실행이 단계별로 남기는 JSONL 기록. 사례 실행 폴더 `outputs/{run_id}/runlog_trace-{시각}.jsonl`(단위 L1). 커밋하지 않고 증거 복사하지도 않는다(자료 계약 §8.2).
- 덧붙인 주장: 코드가 보고서에 더한 typed claim(정해진 필드로 나눠 쓴 구조화 주장). 필수 근거(결정 1809), 발동 신호 자기 계열(결정 2225 ②), 중량 비중 0(결정 0105 ①)의 세 갈래다. trace `state_change` 사건의 phase `evidence_claims`에 `added[].code`와 `added[].claims[].claim_id`로 남는다.

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-26(토) 07:30(기록 시각). 바탕은 `main` fe26104 |
| 제목 | 룰북 B7 공개 값(덧붙인 주장 수·`review_status` 집계로 바뀐 보고서 수·버린 초안 수·HOLD 합의로 뺀 도구 지적 수·덧붙이기 전 기준 보고서 단위 오류율·덧붙인 주장 덕분에 뒷받침된 산문 표현 수)의 도구 위치와 계산 규칙 |
| 결정 | 아래 ①~⑦ |
| 결정 주체 | 소유 트랙(D). 오케스트레이터 지시(B7 브리프). 사용자 결정 1856 ③("계산 도구의 위치와 이름은 `RB-1` 동결 전에 정한다")의 이행 |
| 공용 약속 여부 | 아니다. 자료 형식(`scorer_results-{시각}.jsonl`의 키 24개, 보고서 필드, 상태값), 채점 규칙, 채점기 명령은 그대로다. 룰북 B7의 `[미확인]` 문장 넷(실행 조건 입력 파일 항목 포함)을 확정 문장으로 바꿨고(`RB-1` 동결 전이라 새 룰북 버전은 필요 없다, 룰북 §0.1), 요약 양식에 줄을 더했다(공개 항목 자체는 위 사용자 결정으로 이미 승인됐다) |
| 관련 PR | 브랜치 `data/DT8-b7-public-values` |

## 결정 내용

① **위치** — 독립 채점기 `eval/scorer/` 안이다. 파일 읽기는 `eval/scorer/__main__.py`(`read_trace`·`trace_entry`)가, 사건 해석과 모드별 집계·요약 줄은 단위 C4 `eval/scorer/summary.py`("실행 추적 집계" 절: `parse_trace`·`attached_claim_ids`·`trace_facts`·`without_attached`·`before_after`·`trace_mode_stats`·`_trace_lines`·`_trace_b7_lines`)가 맡는다. 새 단위 파일을 두지 않았다. 까닭: 채점 요약 1~4절에 모드별로 함께 적혀야 하고, "덧붙이기 전 기준 오류율"은 채점기의 산문 뒷받침 판정(단위 C1·C2)을 그대로 다시 쓰기 때문이다. 새 단위(C5)로 두면 등록부(`src/tradesentry/units/registry.py`, 런타임)와 단위 수 65개를 적은 문서(`CLAUDE.md`·`AGENTS.md`·`docs/README.md`·로드맵)를 함께 고쳐야 해 이 작업의 범위(런타임 불변)와 맞지 않았다. 채점기는 여전히 `tradesentry`·`eval.datagen`을 import하지 않는다(경계 시험 그대로).

② **입력** — `<run_dir>`(`outputs/evaluate-{시각}/`)와 같은 부모 폴더의 사례 실행 폴더 `{run_id}/`에 있는 `runlog_trace-{시각}.jsonl`을 **읽기만** 한다. 묶음 기록의 줄마다 읽되, 집계에는 사례마다 고른 최종 행(재실행이 있으면 실행명 시각이 가장 늦은 줄, 룰북 B5)만 쓴다. 샌드박스가 쓴 믿지 않는 입력이라 심볼릭 링크·크기 상한(16 MiB)·권한·입출력 오류(`OSError`)·UTF-8 아님·한 줄이라도 JSON 객체가 아님·`event` 없음·`run_id` 불일치·사건 0건은 "trace를 읽을 수 없음"으로, 폴더·파일이 없으면 "trace 없음"으로, 사건은 읽었지만 `state_change` 사건의 필드 모양(`stage` 문자열, `data.phase` 문자열, `evidence_claims`의 `added` 목록과 항목의 `code` 문자열·`claims` 목록·`claim_id` 문자열, `code_finding`의 `skipped_for_hold` 문자열 목록, `after_critic`의 `requery_dropped` 목록. 골든 `tests/units/I12/`·`tests/units/I8/input.json`의 필드 이름)이 다르거나 완료 보고서의 `claims`가 목록이 아니면 "trace 모양 다름"으로 둔다(0건으로 세지 않는다. Codex 채점기 검토 1회차 지적 1·2·3). 어느 쪽도 채점을 멈추지 않는다. 한 모드의 최종 행 가운데 위 셋 가운데 하나라도 있으면 그 모드의 여섯 값을 모두 `집계하지 않음(사유 n/m건)`(사유가 여럿이면 `집계하지 않음(trace 없음 a·trace를 읽을 수 없음 b·trace 모양 다름 c, n/m건)`)으로 적는다. 요약 문구와 룰북 B7 문장은 같다(지적 4)(커밋 사본 `artifacts/eval/score-{시각}/{run_id}/`에는 보고서 원문만 있어 재채점할 때가 그렇다). 부분 집계는 하지 않는다(값이 표본 일부로 만들어졌다는 오해를 막는다).

③ **계산 규칙(모드별, 결정적)**

| 값 | 규칙 |
|---|---|
| 덧붙인 주장 수 | trace의 phase `evidence_claims` 사건 가운데 **마지막 사건**의 `added[].claims[].claim_id` 가운데 최종 보고서 `claims[]`에 그 `claim_id`로 남은 주장 수. 완료 보고서(COMPLETED이고 읽어 채점한 보고서)마다 세어 합계·보고서당 중앙값·범위(최소~최대)와 갈래별 내역(`signal_claim` → 자기 계열, `zero_weight_claim` → 중량 0, 나머지 code → 필수 근거)을 적는다. 마지막 사건을 쓰는 까닭: 런타임은 보고서를 만들 때마다(초안·수정본·최종) 덧붙이기를 처음부터 다시 하고 `claim_id` 번호열 `e{번호}`를 다시 매기므로 최종 보고서의 덧붙인 주장은 마지막 덧붙이기의 결과다. `main`의 실제 실행 227건(V1 4차·5차 dev20·`real_dev`)에서 완료 보고서의 `e{번호}` 주장 집합이 마지막 사건의 `claim_id` 집합과 전부 같았다(다른 사례 0건). trace에는 있는데 보고서에 없는 `claim_id`가 있으면 "trace가 덧붙였다고 적었는데 최종 보고서에 없는 주장 n건"을 따로 적는다 |
| `review_status` 집계로 바뀐 보고서 수 | 최종 보고서 기준: stage `final`의 phase `status_aggregated` 사건이 있고 실행이 COMPLETED인 실행 수. 괄호로 "어느 단계든"(stage를 가리지 않고 사건이 있는 실행 수)을 함께 적는다 |
| 버린 초안 수 | (나) 수정본 버림: phase `revision_discarded` 사건 수. (가) 재조회 버림: phase `after_critic` 사건의 `requery_dropped` 항목 수. 둘을 따로 적는다(룰북 B7 `[미확인]` 문장의 확정) |
| HOLD 합의로 뺀 도구 지적 수 | phase `code_finding` 사건의 `skipped_for_hold` 항목 수 |
| 덧붙이기 전 기준 보고서 단위 오류율 | 완료 보고서마다 덧붙인 주장(위 `claim_id`)을 뺀 사본을 같은 채점 함수(단위 C1 `score_report_claims`, C2 `score_report_prose`)로 다시 채점해, 오류 claim이나 `UNBACKED_PROSE`가 하나라도 있으면 오류다. 분모는 계획 사례 수(같은 모드 예정 실행 수)이고, COMPLETED가 아닌 실행·보고서를 읽지 못한 실행·미실행은 덧붙이기 전·뒤 모두 그대로 오류다(룰북 B3·B5). 재채점이 입력 오류를 내면 그 모드를 `집계하지 않음(덧붙이기 전 재채점 불가 n건)`으로 적는다 |
| 덧붙인 주장 덕분에 뒷받침된 산문 표현 수 | 완료 보고서마다 max(0, 덧붙이기 전 `UNBACKED_PROSE` 수 − 덧붙이기 뒤 `UNBACKED_PROSE` 수)의 합 |

④ **요약 출력** — 1절(`real_sealed`)·2절(`holdout40`)·3절(`dev20`·`real_dev`·`controlled_fixture_v0`)의 모드별 표 아래에 "덧붙이기 전·뒤 보고서 단위 오류율", "덧붙인 주장 덕분에 뒷받침된 산문 표현 수", "장치 발동 수(실행 추적 집계)" 세 줄을 더하고, 4절 참고 지표에 룰북 B7 공개 항목 줄(덧붙인 주장 수·집계로 바뀐 보고서 수·덧붙이기 전 기준 오류율(Wilson 95% 구간과 덧붙이기 뒤 값)·뒷받침된 산문 표현 수·버린 초안 수·HOLD 합의 생략 수·집계 범위)을 적는다. 값은 모드별 건수·비율만이고 사례 식별자·trace 값은 내지 않는다. 봉인 묶음도 같은 값을 낸다(건수·비율은 봉인 내용이 아니다, 자료 계약 §10.3 N10). dev20·holdout40의 "보고서 단위 오류율"은 그 묶음의 지표가 아니라 참고 값이다.

⑤ **`scorer_results-{시각}.jsonl`의 키는 늘리지 않았다** — 브리프는 사례별 덧붙인 주장 수·집계 변경 여부·버림 여부를 행의 키로 더하라고 했으나, 자료 계약 §8.2("위 키 전부")와 평가 스킬 ② `skills/tradesentry-eval/SKILL.md` "기록 키"("키를 늘리지 않는다")가 이 형식을 공용 약속으로 고정하고 있다. 공용 약속은 사용자 승인 없이 바꾸지 않으므로(`CLAUDE.md` 절대 규칙 4) 이 항목은 넣지 않고 오케스트레이터에게 올린다. 승인되면 채점기 내부 형식으로 `trace_attached_claims`(정수 또는 null)·`trace_status_aggregated_final`(참·거짓 또는 null)·`trace_revision_discarded`(정수 또는 null)·`trace_requery_dropped`·`trace_hold_skipped_findings`·`trace_available`을 제안한다(접두어 `trace_`로 trace에서 온 채점기 내부 값임을 표시). 사례별 값은 지금도 채점기 안(`trace_stats`)에 있어 요약의 모드별 값이 그것으로 계산된다.

⑥ **참고 구현과의 대조** — 오케스트레이터의 일회 분석 도구(scratchpad `attached_effect.py`, 저장소에 넣지 않는다)를 같은 실행 폴더에 돌린 값과 채점기 요약의 새 줄을 맞춰 봤다. 채점기는 작업 폴더에서 `python -m eval.scorer --run outputs/<평가 묶음>`으로 돌렸고, 입력은 메인 폴더 `outputs/`의 묶음 기록·실행 조건 입력 파일·보고서·trace를 작업 폴더 `outputs/`로 복사한 것이다(읽기만. 채점기는 `<run_dir>`가 자기 저장소의 `outputs/` 아래여야 해서 메인 폴더 절대 경로를 직접 받지 않는다).

| 묶음 | 모드 | 참고 구현(전 → 뒤, 뒷받침 수, 보고서당 중앙값(범위)) | 채점기 | 일치 |
|---|---|---|---|---|
| V1 4차 `real_dev` `evaluate-260925234445` | freeform | 7/20 → 5/20, 3, 2.5(0~7) | 전 7/20 → 뒤 5/20, 3, 2.5(0~7), 합계 58 | 예 |
| 〃 | full | 6/20 → 3/20, 3, 2(0~7) | 전 6/20 → 뒤 3/20, 3, 2(0~7), 합계 43 | 예 |
| V1 5차 `real_dev` `evaluate-260926020006` | freeform | 13/20 → 11/20, 4, 4.5(3~8) | 전 13/20 → 뒤 11/20, 4, 4.5(3~8), 합계 56(중량 0 11) | 예 |
| 〃 | full | 12/20 → 11/20, 1, 5(1~5) | 전 12/20 → 뒤 11/20, 1, 5(1~5), 합계 36(중량 0 6) | 예 |
| V1 5차 dev20 `evaluate-260926012023` | checklist | 0/20 → 0/20, 0, 0(0~4) | 전 0/20 → 뒤 0/20, 0, 0(0~4), 합계 22 | 예 |
| 〃 | agent | 3/20 → 1/20, 2, 4(0~6) | 전 3/20 → 뒤 1/20, 2, 4(0~6), 합계 54 | 예 |
| 〃 | full | 2/20 → 1/20, 1, 4(0~5) | 전 2/20 → 뒤 1/20, 1, 4(0~5), 합계 52 | 예 |

장치 발동 수도 같다: `review_status` 집계로 바뀐 최종 보고서(어느 단계든) 4차 `real_dev` freeform 1(1)·full 0(1), 5차 `real_dev` 0(0)·0(0), dev20 5차 agent 1(2)·checklist 0·full 0; (나) 수정본 버림 4차 0·0, 5차 `real_dev` freeform 1·full 0, dev20 5차 full 1; HOLD 합의로 뺀 도구 지적 4차 full 5, 5차 `real_dev` full 2, dev20 5차 agent 4·full 2. 참고 구현이 내지 않는 (가) 재조회 버림은 4차 `real_dev` freeform 1·full 2, 5차 `real_dev` freeform 1·full 2, dev20 5차 full 1이다.

**한 곳이 다르다**: 참고 구현은 "최종 보고서의 자기 계열 주장 덧붙임"을 stage `final`의 `evidence_claims` 사건에서만 세어 dev20 5차 `agent`를 0으로 냈다. 채점기는 1이다. 그 실행은 `agent` 모드(Critic·최종 단계 없음)라 `evidence_claims` 사건이 basic 단계 하나뿐이고, 거기서 덧붙인 `signal_claim` 주장(`e3`)이 최종 보고서에 그대로 남아 있다. 공개 값의 뜻("최종 보고서에 남은 덧붙인 주장", 결정 1809 ④·2225 ⑦)에는 채점기 규칙(마지막 사건 ∩ 최종 보고서)이 맞고, 참고 구현의 final 단계 제한은 최종 단계가 없는 모드를 놓친다. 참고 구현의 보고서당 중앙값·범위는 보고서의 `e{번호}` 정규식으로 세어 채점기와 같았다(같은 실행이 합계에는 들어 있었다).

⑦ **시험** — `tests/test_scorer_summary.py` `TraceAggregationTest`(골든 trace 조각: 덧붙인 주장이 산문을 뒷받침하는 보고서 1건, `review_status` 집계 변경 1건, (나) 수정본 버림 1건, trace 없는 실행 1건. ①~⑥의 기대값, 믿지 않는 trace 모양 거부, 골든 필드 이름 기준 모양 검사와 사유별 "집계하지 않음" 문구, 실패·미읽음·미실행 행이 전·뒤 모두 오류로 남음, 요약 문자열, trace 입력이 없을 때 "집계하지 않음"), `tests/test_scorer_main.py` `test_rulebook_b7_public_values_come_from_trace_files`(명령 끝까지: trace 없는 실행이 있으면 집계하지 않음·종료 코드 0, 모두 있으면 값, 깨진 줄·`run_id` 다름·권한 0 파일은 읽을 수 없음, `added`가 목록 아님·`stage` 없음은 모양 다름, `claims` 비리스트 보고서는 집계 불가, `scorer_results` 키 불변), 단위 C4 골든 `tests/units/C4/expected.json` 갱신(trace 입력이 없는 기존 입력 → 집계하지 않음 줄). 경계 시험은 바꾸지 않았다(새 import 없음).

## 한계

- trace는 샌드박스가 쓴 자기 보고다. 채점기는 모양만 검사하고 내용의 참을 보증하지 않는다. 그래서 대표 지표(정답 대조)는 trace를 쓰지 않고, 이 값들은 참고·공개 항목이다.
- 덧붙인 주장을 `claim_id`로만 가른다(`metric_id`는 대조하지 않는다). 런타임이 같은 `claim_id`를 다른 주장에 다시 쓰면 잘못 셀 수 있다. 실제 실행 227건에서는 그런 일이 없었다.
- 한 모드에 trace가 없거나 읽을 수 없거나 모양이 다른 최종 실행이 하나라도 있으면 그 모드 전체를 집계하지 않는다(부분 집계 없음). 증거 사본만으로 재채점한 요약에는 이 값들이 모두 "집계하지 않음"이다.
- `scorer_results-{시각}.jsonl`의 사례별 키(⑤)는 사용자 승인 대기다.
- 자료 계약 §8.2의 실행 조건 입력 파일 `[미확인]` 문장과 평가 스킬 ② "결과 보고"의 대응 문장은 이 PR의 소유 범위 밖이라 고치지 않았다(문서 PR 대상).
