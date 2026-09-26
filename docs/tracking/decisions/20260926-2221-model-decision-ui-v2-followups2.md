# UI5 코드: 담당자 화면 v2 두 번째 후속 — 독립 검토 권고 4건

PR #109(UI4, 결정 기록 `20260926-2139-model-decision-ui-v2-followups.md`)의 독립 검토가 권고한 4건을 고쳤다. 채점 경로(`src/tradesentry/{policy,workflow,validator,tools,metrics,reports,evaluation,grouping,dal,snapshot,contract,runlog,cli}/`), `eval/`, `configs/`, `src/tradesentry/app.py`(관리자 화면), `src/tradesentry/approval/`(결정 기록 단위), `uv.lock`·`pyproject.toml`은 바꾸지 않았다(룰북 `RB-1` 동결·관리자 화면 유지). 바꾼 곳은 `src/tradesentry/ui/`, `tests/test_ui_v2.py`, 문서뿐이다.

용어

- 표지 단계: trace(실행 추적 기록)에 그 단계의 표지 이벤트(예: `tool_call` `compare_partners`)가 한 번이라도 나온 진행 단계.
- 실패로 끝난 실행: trace 마지막 `run_end` 이벤트의 `data.execution_status`가 `COMPLETED`가 아닌 실행(예: `FAILED`). 실패한 실행도 `run_end`를 남긴다.
- 재생 실행: 저장해 둔 모델 응답을 다시 쓰는 시연 실행. 외부 모델을 부르지 않는다.
- 옛 실행: 결정 기록 화면에서 보고 있는 실행이, 같은 사례의 결정이 가리키는 실행보다 새 완료 실행 가운데 가장 새 것보다 오래된 경우.

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-26(토) 22:21(작업 시작 KST). 바탕은 `main` 62ae882, 브랜치 `model/UI5-v2-followups2` |
| 제목 | 담당자 화면 v2 두 번째 후속: 실패 실행의 단계 표시, 결정 기록 화면의 새 결과 안내, "이 사례의 기록" 정렬 키, "다시 조사하기" 재생/실제 안내 |
| 결정 | 아래 ①~④ |
| 결정 주체 | 소유 트랙(M). 오케스트레이터 지시(브리프 UI5) |
| 공용 약속 여부 | 아니다. 자료 계약의 객체·필드·상태값·명령·기준값·출력 경로는 바꾸지 않았다. 새 값은 모두 `src/tradesentry/ui/` 안의 화면 표시 규칙과 문구다 |
| 관련 PR | 브랜치 `model/UI5-v2-followups2`(push·PR은 오케스트레이터가 한다) |

## 권고별 처리

| 권고 | 처리 | 이유 |
|---|---|---|
| ① 실패한 실행도 모든 단계가 ✓, 막대 100% | `progress.step_state`가 `run_end`의 `data.execution_status`를 읽는다. 값이 있고 `COMPLETED`가 아니면 마지막 표지 단계까지만 완료(표지 없는 앞 단계는 UI4대로 "건너뜀")이고 그 뒤 단계는 대기(`pending`)다. 결과에 `stopped`(참·거짓)를 더했고 `done`(막대가 세는 단계 수)은 도달한 단계 수다. 표지가 하나도 없으면 모두 대기·막대 0이다. 새 순수 함수 `progress.stopped_note`가 실패 창에 "5단계 가운데 2단계까지 진행하고 멈췄습니다."(EN "Stopped after step 2 of 5.", 표지가 없으면 "첫 단계에 이르기 전에 멈췄습니다." / "Stopped before reaching the first step.") 한 줄을 준다(`screens/jobs.py`가 실패 안내 상자 위에 보인다). `COMPLETED`이거나 값이 없는 `run_end`는 이전과 같이 끝까지 간 것으로 본다. 배경 실행이 완료로 끝났는데 trace에 `run_end`가 없을 때 `jobs._steps_for`가 덧붙이는 표지에는 `execution_status: COMPLETED`를 넣었다 | 키 이름은 조사 흐름 `src/tradesentry/workflow/orchestrate.py`의 `sink.emit("run_end", None, {"execution_status": status, …})`에서 확인했다(읽기만. 시험이 이 줄을 대조한다). 조사 흐름은 예외가 나면 `FAILED`로 `run_end`를 남기므로, 도달하지 못한 뒤 단계에 ✓를 두면 어디서 멈췄는지 가려진다. 값이 없는 `run_end`를 완료로 보는 것은 이전 trace·시험과의 호환이다 |
| ② 결정 기록 화면이 옛 실행을 볼 때 | 새 순수 함수 `listing.assist_view(runs, selected_run, record)`: 볼 실행은 목록 "결과 보기"·사례 검토에서 넘어온 선택(`session_state["selected_run"]`)이 이 사례의 실행이면 그것, 아니면 결정이 가리키는 실행보다 새 완료 실행(`listing.newer_completed_run`)이 있으면 그 가장 새 것, 아니면 가장 새 실행. `older`(보고 있는 실행이 그 가장 새 완료 실행보다 오래됨)이면 단계 띠 아래에 "더 새 조사 결과가 있습니다 (YYYY-MM-DD HH:MM)"(EN "A newer investigation result is available (…)") 한 줄과 "새 결과로 바꾸기"(EN "Switch to the newer result") 버튼을 보인다. 단계 띠 3단계 "내 결정 (지금)"은 결정 전이고 보고 있는 실행이 가장 새 완료 실행이거나 새 완료 실행이 없을 때만 켜고, 옛 실행을 볼 때는 강조 없는 "내 결정"이다. 결정 저장은 보고 있는 실행을 가리킨다(결정 기록 단위 그대로, 막지 않는다) | 결정 저장을 막으면 담당자가 옛 조사 결과에 대해 일부러 기록하는 경우를 막게 된다. 대신 안내가 폼 바로 위에 보이게 했다. 새 완료 실행보다 뒤의 실패 실행을 보고 있으면 "옛 실행"이 아니다(안내를 띄우지 않고, "지금"도 켜지 않는다) |
| ③ "이 사례의 기록" 정렬 키 | 새 순수 함수 `listing.history_sort_key(when, seq)`·`listing.order_history(entries)`: 시각 글자가 "YYYY-MM-DD HH:MM"(또는 ISO의 "T")로 시작하면 `(0, 분까지의 시각, 순번)`, 아니면 `(1, "", 순번)`. 결정 기록 화면이 이 함수로 조사·결정 줄을 섞는다 | 결정 기록의 `timestamp`가 ISO 형식이 아니면 `common.time_text`가 원문을 그대로 주는데, 이전 정렬은 그 글자를 사전순으로 시각 사이에 끼워 넣었다. 읽을 수 없는 줄은 끝에 넣은 순서대로 둔다. 같은 분이면 넣은 순서(조사 먼저)는 UI4와 같다 |
| ④ "다시 조사하기" 카드의 "(1~2분)" | 새 문구 `reinv.desc_replay`("같은 절차가 다시 돌고 새 결과가 이 사례에 붙습니다. 저장해 둔 응답을 다시 쓰는 시연 실행이라 몇 초면 끝납니다. 이전 결과는 그대로 남습니다.", EN 같은 뜻). 재생 파일이 있어 재생으로 돌 사례는 이 문구, 실제 실행은 기존 `reinv.desc`("…(1~2분)…")다(`listing.reinvestigate_desc_key`). 버튼이 잠긴 경우(키·재생 파일 없음)는 기존 설명과 "조사 모델 연결이 설정되지 않아 …" 문구 그대로다 | 로딩 창 안내(UI4 ⑥)와 같은 구분이다. 재생은 1초 안팎에 끝난다 |

## 시험

- `tests/test_ui_v2.py`에 11개를 더했다(28 → 39). ① 실패 `run_end`(`FAILED`) → `[done, done, pending, pending, pending]`·막대 0.4·"2단계까지" KO·EN, 건너뜀 뒤 검수 시작에서 실패(`INVALID`) → `[done, done, skipped, done, pending]`·막대 0.8, 표지 없이 실패 → 모두 대기·막대 0·"첫 단계 전" KO·EN, `COMPLETED`와 값이 없는 `run_end`는 모두 완료·막대 1.0·안내 없음, 조사 흐름의 `run_end` 키 이름 대조. ② 결정 뒤 기본 선택은 새 완료 실행("지금" 켬), 다른 사례의 선택은 무시, 옛 실행 선택 → 안내·"지금" 끔·안내 문구 KO·EN과 내부 식별자 없음, 새 실행 선택 → 안내 없음·"지금", 새 완료 실행보다 뒤의 실패 실행 → 안내 없음·"지금" 끔, 새 결과 없음 → 결정 완료, 결정 전 → 가장 새 실행·"지금", 실행 없음. ③ 비ISO 시각(글자·숫자·None)은 끝에 원래 순서, ISO "T" 형식도 시각순, 같은 분은 넣은 순서. ④ 재생/실제 문구 키와 KO·EN 문구, 잠긴 경우 문구 불변.
- 전체 `env -u NVIDIA_API_KEY -u DATA_GO_KR_SERVICE_KEY -u TRADESENTRY_SEALED_DIR uv run --locked python -m unittest discover -s tests`: Ran 1681, OK(skipped=3), 종료 코드 0.
- 화면 확인(키 없이 포트 8503, 헤드리스 Chrome): 필리핀 "변압기·전원장치 부분품" 2024년 12월 사례에서 목록 "결과 보기" → 결정 기록은 19:45 실행(자료 보류 제안)·"내 결정 (지금)"; 사례 검토에서 조사 시각 19:41을 고른 뒤 결정 기록은 19:41 실행(모니터링 제안)·강조 없는 "내 결정"·"더 새 조사 결과가 있습니다 (2026-09-26 19:45)"와 "새 결과로 바꾸기"(EN 같음); 버튼을 누르면 19:45 실행·"My decision (now)"·안내 없음. 이 사례는 재생 파일이 없고 키도 없어 "다시 조사" 버튼이 잠기고 기존 문구가 그대로다. 합성 픽스처 사례(가상국 B)의 결정 기록 화면은 재생 문구("몇 초면 끝납니다", EN "finishes in a few seconds"). 실패 창은 저장소 밖 하네스(trace 이벤트를 늦추고 `compare_partners` 도구 호출 표지 직후 한 번 예외를 내게 함. 앱 코드 변경 없음)로 재생 조사를 실패시켜 확인했다: 실행 결과 `FAILED`·`CODE_ERROR`, 창에 ✓ 두 개와 대기 세 개, 막대 40%, "5단계 가운데 2단계까지 진행하고 멈췄습니다.", "닫기"·"다시 시도". 확인 중 생긴 실패 실행 폴더는 지웠다.

## 한계

- 실패한 실행에서 마지막으로 도달한 표지 단계는 완료(✓)로 보인다(브리프 지시대로). 그 단계 안에서 멈췄는지, 그 단계를 마친 뒤 멈췄는지는 가리지 않는다.
- 제한 시간을 넘겨 프로세스를 끝낸 실행(시간 초과)은 `run_end`가 없어서 이전처럼 멈춘 단계가 "진행 중"으로 보인다.
- "옛 실행" 안내는 결정 기록이 있고 그 뒤 새 완료 실행이 있을 때만 뜬다. 결정 전에 더 오래된 실행을 골라 보는 경우는 이전과 같다(단계 띠 "지금").
- 옛 실행을 보면서 결정을 저장하면 그 결정은 옛 실행을 가리키므로, 더 새 완료 실행이 남아 있어 목록 진행 상태는 "새 조사 결과 · 결정 대기"이고 결정 기록 화면의 안내도 계속 보인다. 저장 뒤 문구 `decide.saved`와 버튼 아래 `decide.after_note`는 "결정 완료"로 바뀐다고 적고 있어 이 경우와 맞지 않는다(UI4부터 사례 검토의 조사 시각 선택으로 생길 수 있던 일이다). 문구 추가는 이번 권고 범위 밖이라 두었다.
