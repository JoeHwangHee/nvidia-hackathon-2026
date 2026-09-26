# UI4 코드: 담당자 화면 v2 후속 — 독립 검토 권고 7건과 제출 절차 1단계 문구

PR #108(UI3, 결정 기록 `20260926-2031-model-decision-ui-user-pages-v2.md`)의 독립 검토 코멘트가 권고한 7건을 고쳤다. 채점 경로(`src/tradesentry/{policy,workflow,validator,tools,metrics,reports,evaluation,grouping,dal,snapshot,contract,runlog,cli}/`, `eval/`, `configs/`), `src/tradesentry/app.py`(관리자 화면), `src/tradesentry/approval/`(단위 A1), `uv.lock`·`pyproject.toml`은 바꾸지 않았다(룰북 `RB-1` 동결·관리자 화면 유지). 바꾼 곳은 `src/tradesentry/ui/`, `tests/test_ui_v2.py`, 문서뿐이다.

용어

- 진행 상태: 경보 목록의 행마다 붙는 "조사 전·조사 중·조사 완료 · 결정 대기·결정 완료·재검토 필요·조사 실패" 표시. 화면 표시 규칙이며 자료 계약의 상태값이 아니다.
- 표지 이벤트: trace(실행 추적 기록)에서 진행 단계를 알아보는 이벤트(예: `tool_call` `decompose_hs`).
- 좀비 프로세스: 끝났지만 부모가 종료 상태를 거둬 가지 않아(`wait`) 프로세스 표에 남은 자식 프로세스.
- 재생 실행: 저장해 둔 모델 응답을 다시 쓰는 시연 실행. 외부 모델을 부르지 않는다.

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-26(토) 21:39(작업 시작 KST). 바탕은 `main` 4e608f9, 브랜치 `model/UI4-v2-followups` |
| 제목 | 담당자 화면 v2 후속: 결정 뒤 새 조사 결과 표시, 실행 폴더 사례 거름, 종료 뒤 회수, 재시도 표시 조건, 건너뜀 단계, 재생/실제 안내 문구, 제출 절차 1단계 |
| 결정 | 아래 ①~⑦과 ⑧(문서) |
| 결정 주체 | 소유 트랙(M). 오케스트레이터 지시(브리프 UI4) |
| 공용 약속 여부 | 아니다. 자료 계약의 객체·필드·상태값·명령·기준값·출력 경로는 바꾸지 않았다. 새 진행 상태 `NEW_RESULT`는 `src/tradesentry/ui/listing.py` 안의 화면 표시 값이다 |
| 관련 PR | 브랜치 `model/UI4-v2-followups`(push·PR은 오케스트레이터가 한다) |

## 권고별 처리

| 권고 | 처리 | 이유 |
|---|---|---|
| ① 결정 뒤 다시 조사한 결과가 가려짐 | `listing.newer_completed_run(runs, decided_run_id)`: 결정 기록의 `run_id`보다 실행명 시각이 뒤인 같은 사례의 완료(`COMPLETED`) 실행 가운데 가장 새 것. 있으면 `listing.row_progress`가 새 상태 `NEW_RESULT`("새 조사 결과 · 결정 대기", EN "New result · awaiting your decision", 보조 줄 "{제안} 제안")를 주고, 그 행의 실행·제안은 새 실행의 것이다("결과 보기"가 새 실행을 연다). 이전 결정의 유효 상태(`VALID`·`REVIEW_REQUIRED`)와 무관하게 앞선다. `NEW_RESULT`는 `PROGRESS_STATES`(조회 조건 "전체"), 조회 조건 "조사 완료 · 결정 대기", 요약 카드 "내 결정을 기다리는 사례" 수, 정렬 순서(결정 대기와 같은 자리), 연한 파랑 행 배경에 든다. 결정 기록 화면(`screens/assist.py`)의 단계 띠 3단계 "내 결정"도 같은 함수로 새 결과가 있으면 "지금"이 된다. 이전 결정은 "이 사례의 기록"에 그대로 남는다. 이때 기록이 조사들 뒤에 결정을 몰아 적어 "19:45 조사 완료"가 "19:44 내 결정" 위에 오던 순서를 시각순으로 섞었다 | 화면 표시 규칙이다. 단위 A1 `approval.check`(결정이 가리키는 실행의 보고서와 대조)는 바꾸지 않았다. 실패·무효 실행과 실행 결과 기록이 없는(진행 중) 실행은 넣지 않는다(`alerts.run_entry`가 기록 없는 폴더를 색인에서 빼고, 상태가 `INVESTIGATED`인 것만 센다). 결정의 `run_id`가 실행명 형식이 아니면 비교하지 않는다 |
| ② 실행 폴더 대체 선택이 다른 실행을 집을 수 있음 | `progress.pick_run_dir(before, after, stdout_dirs, case_id=, case_of=)`: 전후 폴더 차이로 고를 때 `case_of(폴더 이름)`이 조사 사례와 같은 폴더만 고른다. `progress.run_dir_case(run_dir)`는 실행 결과 기록의 `case_id`, 없으면(진행 중) trace `run_start` 이벤트의 `data.case_id`, 둘 다 없으면 None(고르지 않음). `screens/jobs.py`가 두 인자를 넘긴다. 인자를 안 주면 이전 동작 그대로다 | 다른 세션·다른 사례의 실행이 같은 때 생겨도 집지 않는다. CLI 표준 출력의 폴더는 그 조사 프로세스가 직접 알린 것이라 그대로 먼저 쓴다(일찍 실패해 기록이 없는 폴더도 놓치지 않게) |
| ③ SIGKILL 뒤 회수 없음 | 끝내기 논리를 streamlit 없는 `progress.stop_process_group(proc, getpgid=, killpg=, wait_s=5)`로 옮기고 `jobs._stop`이 부른다: SIGTERM → `wait(5초)` → 살아 있으면 SIGKILL → 다시 `wait(5초)`(시간 초과·OS 오류는 무시). 프로세스가 이미 없으면(`ProcessLookupError`)도 `wait`로 거둔다 | 좀비를 남기지 않는다. `subprocess.TimeoutExpired`는 `OSError`가 아니라 따로 잡는다. 시험이 streamlit 없이 가짜 프로세스로 호출 순서를 확인할 수 있게 순수 모듈에 뒀다 |
| ④ "다시 요청 중" 표시 조건 | 마지막 모델 이벤트가 `model_error`이고 그 `data.retrying`이 `True`일 때만 켠다 | 키 이름은 조사 흐름의 모델 호출부(`src/tradesentry/workflow/model_client.py`의 `sink.emit("model_error", …, retrying=…)`)에서 확인했다(읽기만). 재전송하지 않는 오류(`retrying=False`)에 "다시 요청 중"을 보이지 않는다 |
| ⑤ 실제로 돌지 않은 단계의 ✓ | `progress.step_state`가 단계별 표지를 모아, 진행 중 단계보다 앞인데 표지가 한 번도 없고 그보다 뒤 단계 표지가 있으면 `skipped`로 둔다. 로딩 창은 회색 점 "–"와 작은 "건너뜀"(EN "Skipped") 꼬리표를 보인다(`screens/style.py` `.ts-step-skipped`·`.ts-skip`). 진행 막대와 조사 중 표시의 단계 수는 건너뛴 단계도 끝난 것으로 센다. 끝난 조사의 단계도 실제 trace로 그린다(`jobs._steps_for`, trace에 `run_end`가 없을 때만 덧붙임) | 점유율만 발동이라 `decompose_hs`를 부르지 않은 조사에 "하위품목 구성 변화 확인 ✓"가 뜨던 것을 고쳤다. 마지막 표지 뒤 단계는 건너뜀으로 보지 않는다(검수 종료 뒤 숫자 대조 차례, 표지 없이 `run_end`만 있는 경우가 모두 건너뜀이 되지 않게) |
| ⑥ 문구 두 곳 | `load.expect_replay`를 새로 두어 재생 실행에는 "저장해 둔 응답을 다시 쓰는 시연 실행이라 몇 초면 끝납니다. 끝나면 결과 화면이 바로 열립니다."(EN "This demo run reuses stored responses, so it finishes in a few seconds. The result opens automatically when done."), 실제 실행에만 기존 `load.expect`("보통 30초에서 90초가 걸립니다. …")를 쓴다. `prog.review_required_sub`는 "근거 보고서와 맞지 않습니다"(EN "No longer matches its report") | 재생은 1초 안팎에 끝난다. 재검토 필요는 보고서가 바뀐 경우와 없어진 경우 모두에 생기므로 중립 문구로 바꿨다. 재생판 뒤 문장은 실제판과 같게 두었다 |
| ⑦ 실제 NIM 실행 안내 | `load.footnote`(실제 실행판) 끝에 "모델 추론 요청은 NVIDIA 클라우드(NIM)로 갑니다."(EN "Model inference requests go to the NVIDIA cloud (NIM).")를 더했다. 재생판 `load.footnote_replay`는 그대로다 | 실제 실행은 추론 요청이 NVIDIA 클라우드로 간다(UI3 기록 ⑨ (가)와 같은 사실) |

⑧ **문서** — `docs/submission/SUBMISSION_FORM.md` "제출 절차" 1단계를 "교육 미션 확인(공식 진행 1단계)"로 고쳤다: 신청 폼 안내 원문 "참가자는 교육 미션을 확인한 후, build.nvidia.com의 Skill API를 활용하여 데모 프로젝트를 개발합니다."와 수강·수료를 증명하는 폼 칸이 없었다는 사실(대회 조사 문서 `NVIDIA-FastCampus-Korea-Agentic-AI-Hackathon-2026.md` 3-1절·4절, 2026-09-22 조사) `[사실]`, 공식 기한은 제출 마감(2026-09-28(월) 23:59)뿐이고 2026-09-27(일)은 로드맵 6.5절의 내부 목표라는 점, 제출 전에 들어 둔다는 점. 강의 주소와 참가 자격 문장은 그대로 두었다. `docs/tracking/status.md` "사용자 결정 대기"의 대회 참가 조건 줄에 같은 뜻을 적었다. README 5절과 `docs/operations.md`에는 바뀐 사실이 없어 고치지 않았다.

## 시험

- `tests/test_ui_v2.py`에 13개를 더하고 1개를 고쳤다(`model_error`에 `retrying=True`를 줌). ① 결정 뒤 새 완료 실행 → `NEW_RESULT`(이전 결정 `VALID`·`REVIEW_REQUIRED` 두 경우), 새 실행의 `run_id`·제안, 요약 카드 대기 수·조회 조건 "결정 대기" 포함·"결정 완료" 제외, 셀 문구 KO·EN과 내부 식별자 없음; 새 실행이 실패·진행 중(trace만)이면 `DECIDED` 유지, 결정한 실행보다 오래된 완료 실행·형식이 아닌 `run_id`는 제외; 여러 완료 실행 중 가장 새 것. ② 실행 결과 기록·trace `run_start` 두 경로로 사례를 알아내고 다른 사례의 더 새 폴더를 거름, 사례를 모르는 폴더 제외, 표준 출력 우선, 기록과 trace가 다르면 기록 우선. ③ 가짜 프로세스로 TERM → wait → KILL → wait(회수), TERM만으로 끝난 경우, 두 번째 wait 시간 초과·이미 없는 프로세스도 조용히 회수. ④ `retrying` 참·거짓·없음·참이 아닌 값·뒤에 요청이 온 경우. ⑤ `decompose_hs` 없이 검수 시작 → `[done, done, skipped, current, pending]`·막대 0.6, 검수 종료·끝까지·표지 없는 `run_end`. ⑥·⑦ 재생/실제 안내·각주 KO·EN, 재생 각주 불변, 재검토 필요 보조 문구.
- 전체 `env -u NVIDIA_API_KEY -u DATA_GO_KR_SERVICE_KEY -u TRADESENTRY_SEALED_DIR uv run --locked python -m unittest discover -s tests`: Ran 1670, OK(skipped=3), 종료 코드 0.
- 화면 확인(키 없이 포트 8503, 헤드리스 Chrome): 경보 목록 KO·EN(2024년 12월)에서 필리핀 "변압기·전원장치 부분품" 행이 "새 조사 결과 · 결정 대기 / 자료 보류 제안"(EN "New result · awaiting your decision / data hold suggested")이고 요약 카드 "내 결정을 기다리는 사례 2건"; 그 사례의 결정 기록 화면에서 3단계 "내 결정 (지금)", 기록이 시각순(19:41 조사 → 19:44 결정 [유효] → 19:45 조사); 합성 픽스처 재생 "다시 조사"의 로딩 창에 재생 문구와 재생 각주. 재생을 사람 눈에 보이게 늦추는 저장소 밖 하네스는 UI3와 같은 것을 썼다(앱 코드 변경 없음). 건너뜀 표시는 합성 사례 A·B·C가 모두 `decompose_hs`를 불러 화면에서는 보지 못했고 순수 시험으로만 확인했다.

## 한계

- `NEW_RESULT`는 실행명 시각(초 단위)으로 새것을 가린다. 결정한 실행과 같은 초에 만든 실행은 새것으로 보지 않는다(실행명은 초마다 하나라 같은 초에 둘이 생기지 않는다).
- 이 사례의 기록을 시각순으로 섞을 때 조사 시각은 실행명(분 단위), 결정 시각은 기록 `timestamp`(분까지 표시)라 같은 분이면 조사가 먼저 온다.
