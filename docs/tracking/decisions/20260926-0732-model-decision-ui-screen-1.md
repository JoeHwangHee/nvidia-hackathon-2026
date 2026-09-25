# U1 코드 PR: 화면 1 "사례 보기"(화면 단위 `app`, `src/tradesentry/app.py`, Streamlit) — 구성·차트·의존성 그룹·"사례 실행" 패널·시험·한계

2026-09-26(토) 04:25 사용자 결정(제출 시나리오 C = A + 화면 1개. 결정 기록 `20260926-0425-user-decision-submission-scenario.md`)의 코드 쪽이다. 화면 2(시계열)·화면 3(before-after 대조)·승인 모의는 만들지 않았다. 채점 경로(탐지·조사·검증·채점·판정 정책) 코드는 한 줄도 바꾸지 않았다.

용어

- Streamlit: 파이썬 함수 호출로 웹 화면을 만드는 라이브러리. 스크립트를 위에서 아래로 다시 실행해 화면을 그린다.
- 화면 모형: 화면이 그릴 내용을 순수 자료(dict·list·int·Decimal·str)로 만든 것. streamlit 없이 시험한다.
- 재생 실행: `tradesentry run-case --replay`로 기록된 모델 응답을 재생해 키 없이 끝까지 도는 실행(결정 기록 `20260926-0230-model-decision-smoke-replay.md`). 점수표 근거가 아니다.

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-26(토) 07:32(기록 시각). 바탕은 `main` d2a9d49 |
| 제목 | 화면 1 "사례 보기"와 "사례 실행" 패널(화면 단위 `app`), streamlit은 lock 밖 `--with` 실행 |
| 결정 | 아래 ①~⑨ |
| 결정 주체 | 소유 트랙(M). 오케스트레이터 지시(브리프 UI1과 추가 지시 "사례 실행" 패널). 화면 개수는 사용자 결정 0425 |
| 공용 약속 여부 | 아니다. 자료 계약의 객체·필드·상태값·명령은 바꾸지 않았고, `src/tradesentry/app.py`는 자료 계약 §10 경로 표에 이미 있다. 판정 정책·검증기·채점기·보고서 필드·trace 모양·CLI 옵션은 불변이다 |
| 관련 PR | 브랜치 `model/U1-screen-1` |

## 결정 내용

① **의존성 — streamlit은 lock에 넣지 않는다(오케스트레이터 결정)** — 화면은 `uv run --locked --with "streamlit==1.64.0" streamlit run src/tradesentry/app.py`로 띄운다. `--with`는 uv가 그 실행에만 streamlit 1.64.0(uv가 푼 최신 안정판, 2026-09-15 배포)을 임시 환경에 더하는 방식이라 `pyproject.toml`·`uv.lock`은 바뀌지 않는다(`git diff origin/main -- pyproject.toml uv.lock`이 비어 있다). 처음에는 선택 의존성 그룹 `[project.optional-dependencies] ui = ["streamlit==1.64.0"]`으로 넣었으나 되돌렸다. 까닭: streamlit 1.64.0이 `websockets<17,>=12`를 요구해 universal lock의 `websockets`가 17.1에서 16.1.1로 내려갔고(`websockets`는 NAT 쪽 `uvicorn`의 간접 의존성), 그러면 기본 `uv sync --locked` 환경과 샌드박스 이미지의 패키지가 `RB-1` 동결 직전에 바뀐다. 오케스트레이터가 동결 직전에 기본 환경에 닿는 lock 변경을 넣지 않기로 했다. 앱은 streamlit을 화면 함수 안에서만 import하므로 경계 시험·전체 시험은 streamlit 없는 기본 환경에서 돈다. 키가 있을 때는 `python3 spikes/x1/with_nvidia_key.py --env-file .env -- uv run --locked --with "streamlit==1.64.0" streamlit run src/tradesentry/app.py`처럼 키 래퍼 아래에서 띄운다.

② **화면 구성(위에서 아래로, `src/tradesentry/app.py`)** — 사이드바: "사례 실행" 패널(⑥), 실행 폴더 선택(`outputs/` 바로 아래 `run_case-{시각}` 폴더를 새 것부터 나열. `outputs/sealed/`와 `.download-*`·`.quarantine-*`는 빼고 그 안으로 내려가지 않는다)과 상대 경로 직접 입력(`outputs/run_case-…`만 받는다). 본문: (1) 머리 — 사례 식별자를 HS6(품목 이름은 `data/reference/hs6_candidate_table.json`)·상대국(한국어 이름은 `data/reference/country_map.csv`, 합성 코드는 "합성 또는 이름 없음")·비교월·기준월로 풀어 쓰고, 스냅샷·정책·모드·비교 대상·`execution_status`를 보이고, 판정 전후를 "조사 전 경보(`PRE_INVESTIGATION`) → 최종 `review_status_final`"로 적되 상태마다 뜻 한 줄(`STATUS_MEANING`, 자료 계약 §3.1 풀이를 줄인 것)을 병기한다. 신호별 `signal_status`와 `unresolved_evidence`도 적는다. `COMPLETED`가 아니면 최종 판정이 `null`임을 알린다. (2) 조회 이유 — 신호(`unit_value`·`share`)별 발동 지표(`r_U`·`d_s`)의 값·단위, 정책 기준값(`configs/policy_v1.json` `thresholds`, 단위 K4로 읽음), 발동 여부, 신호별 판정, 규칙 참고 근거(trace `rule_reference`의 `basis`), 값의 출처. (3) 차트(③). (4) 실제 실행한 도구 — trace의 `tool_call`을 그 `tool_result`와 짝지어 순서대로(도구, 인자 요약, 요청 주체 code·model, 누적 시도, 성공, 근거 ID 수, 지표 수, 빠진 자료 수, `retryable_error`, 소요 ms), `budget_block`은 예산 차단 줄로. 모델 요청 수(HTTP 시도·오류 수 병기)·토큰·소요 시간 한 줄. (5) 반대 근거와 보고서 — typed claim 표(계약 필드 12개 + 출처. `evidence_claims` 사건의 `added`에 든 `claim_id`는 "코드가 덧붙임"), `narrative`, `hypotheses`, `validator_findings`. (6) 판정 전후 타임라인 — 첫 줄 "처음 표시(조사 전 경보)" 뒤에 `state_change`(rule_reference·draft·evidence_claims·after_critic·code_finding·revised·revision_discarded·draft_discarded·status_aggregated·final)와 `validator_result`를 순서대로 표로. `status_aggregated`·`revision_discarded`·`code_finding`·`draft_discarded` 발동 여부를 위에 한 줄로 알린다. before-after 대조는 하지 않는다(표만). (7) 원본 행 링크 — 보고서 `evidence_ids`를 단위 K3 `Snapshot.resolve`로 풀어 `observation` 행의 HS 코드·상대국·월·금액·중량·관측 상태·요청 ID를 표로. 다른 표(`peer_group`)는 열 값을 한 줄로. 스냅샷을 열 수 없으면 ID만 나열하고 "스냅샷 없음"을 적는다. (8) 바닥글 — "부정·위법·원산지 판정이나 실제 통관 조치가 아니다. 담당자의 다음 업무 제안이다."와 `CLAUDE.md` 개요의 데모 범위 문장 그대로.

③ **차트(룰북 A2 `3f` 3점 앵커 = 차트)** — 기본은 (가) `st.bar_chart` 두 개: 기준월(전년 같은 달)과 비교월의 kg당 단가 `U`(USD/kg)와 점유율 `s`(%). 값은 보고서 주장을 먼저, 없으면 trace 도구 봉투의 검증된 지표(`metrics[].inputs.metric`이 `U`·`s`인 항목)에서 가져오고 새로 계산하지 않는다. (나) trace의 `get_history` 지표에 대상국 `U`가 달별로 3개 이상 있으면 `st.line_chart`로 시계열과 기준월 단가 수평선을 더 그린다. **지금 조사 흐름의 `get_history`는 기준월·비교월 두 달의 `U`만 돌려주므로 실제로는 (가)만 그려진다**(합성·실자료 trace 모두 확인). 스냅샷에서 13개월 단가를 직접 계산하는 방식은 화면이 값을 새로 계산하게 되어 택하지 않았다(화면 2의 몫). 제목은 "kg당 단가와 점유율: 기준월과 비교월"이고 부정·위법·원산지를 암시하는 제목·문구·색을 쓰지 않는다(기본 색). Decimal은 차트를 그리는 순간에만 float로 바꾼다.

④ **진입 함수 `run(inp)`와 골든** — `run({"run_dir": 실행 폴더 상대 경로, "snapshot_path"?: SQLite 경로, "resolve_rows"?: 참/거짓})`이 화면 모형(`screen_model`)을 돌려준다. 골든 입력은 화면 단위 골든 폴더(`tests/units/` 아래 화면 단위 ID 폴더)의 `input.json`(`resolve_rows: false`로 스냅샷 유무와 무관하게 결정적), 고정 실행 폴더는 같은 폴더의 `fixture/run_case-260926071424/`(키 없는 재생 실행 A의 실행 결과 기록·보고서·trace 세 파일. NAT 폴더는 두지 않는다). 기대 출력 `expected.json`은 `run` 출력을 소수를 Decimal 원문 표기로 적어 만들었다(float 없음, 12개). 스트림릿 진입점은 `main()`이고 `streamlit run src/tradesentry/app.py`가 `__main__`으로 부른다.

⑤ **재생 실행 표시** — trace·실행 결과 기록에는 재생 표시가 없다(결정 기록 0230 ⑥: `run_start`의 `api_key_env`뿐. 원 실행과 재생 실행의 요청 해시가 같아 trace로는 가를 수 없다). 그래서 실행 폴더만으로는 "재생 실행" 표시를 하지 않는다(브리프대로 생략). 화면의 "사례 실행" 패널에서 재생으로 시작한 실행은 CLI 표준 오류의 재생 알림과 함께 "재생 실행(--replay), 점수표 근거 아님"을 그 실행 결과 위에 적는다.

⑥ **"사례 실행" 패널(오케스트레이터 추가 지시)** — 사이드바 맨 위. 입력: 스냅샷 ID(`data/snapshots/` 아래 `snapshot_build.sqlite`가 있는 폴더만, 기본 `controlled_fixture_v0`), 정책 버전(기본 `policy_v1`), 모드(`checklist`·`agent`·`full`·`freeform`, 기본 `full`), 사례 식별자(합성 픽스처면 A·B·C 선택지 + 직접 입력), 재생 파일 사용 체크(`eval/dev/smoke/{case_id}.json`이 있을 때만 켤 수 있고, 키가 없으면 기본 켬). 버튼은 CLI와 같은 진입점을 **하위 프로세스**로 부른다: `sys.executable -m tradesentry.cli run-case --snapshot … --policy … --mode … --case … [--replay eval/dev/smoke/{case_id}.json]`, 작업 폴더는 저장소 루트라 실행 폴더가 CLI와 똑같이 `outputs/run_case-{시각}/`에 남는다(자료 계약 §10.3 N5·N6). 같은 프로세스에서 `tradesentry.cli.dispatch.main`을 부르지 않은 까닭은 화면 단위(`app`)의 허용 import(`contract`·`dal`·`runlog`·`reports`·`approval`)에 `tradesentry.cli`가 없기 때문이다(경계 시험). 규칙: (a) 앱은 `.env`를 읽지 않는다. 실제 NIM 실행은 스트림릿 프로세스 환경에 `NVIDIA_API_KEY`가 있을 때만 되고(`python3 spikes/x1/with_nvidia_key.py --env-file .env -- uv run --locked --with "streamlit==1.64.0" streamlit run src/tradesentry/app.py`처럼 띄운다), 없으면 "재생 실행만 가능"을 알린다. 키는 있는지 여부만 보고 값은 읽어 두지 않는다. 자식 환경에서 `DATA_GO_KR_SERVICE_KEY`·`TRADESENTRY_SEALED_DIR`는 뺀다. (b) `evaluate`·`detect`·봉인 묶음은 돌리지 않는다(사례 1건만. 인자 조립 함수가 `run-case`만 만든다). (c) 실행 중에는 버튼을 잠그고(`session_state.running`, 그리고 하위 프로세스가 끝날 때까지 스크립트가 막힌다) 모델 설정 `limits.wall_ms`(300초)에 90초 여유를 더한 시간까지 기다린다. 시간 초과면 그렇게 표시한다. (d) 표준 출력·표준 오류(재생 알림 포함)와 종료 코드를 보이고, 표준 출력의 `outputs/run_case-{시각}/…` 줄에서 새 실행 폴더를 골라 아래 "사례 보기"에 자동으로 띄운다. 표시 전에 로컬 절대 경로 모양(사용자 홈·임시 폴더로 시작하는 절대 경로)과 키 모양 글자를 가린다. (e) 화면에서 시작한 실행 결과 위에 "화면에서 시작한 실행은 점수표 근거가 아니다"를 적는다.

⑦ **표시하지 않는 것** — 키 값, 로컬 절대 경로(폴더는 `outputs/run_case-…` 상대 경로만), `.env`, `outputs/sealed/` 아래(나열도 하지 않는다), 봉인 폴더, NAT 추적 폴더 내용. 네트워크·NIM을 화면이 직접 부르지 않는다("사례 실행" 패널의 하위 프로세스가 키가 있을 때 NIM을 부르는 것은 CLI와 같다).

⑧ **시험(화면 단위 골든 폴더)** — 골든 시험(`test_golden.py`, 기존 틀) + 순수 함수 시험 `test_app_functions.py` 34개: streamlit이 모듈 수준에 import되지 않음(ast·`sys.modules`), 폴더 나열이 `outputs/sealed/`·`.download-*`·`.quarantine-*`·다른 실행 이름·파일을 빼고 새 것부터 정렬, 상대 경로 입력 정리, 실행 폴더 읽기(세 파일, Decimal, 61 레코드)와 기록·보고서가 없을 때의 동작, 사례 머리 풀어 쓰기, 판정 전후 머리(COMPLETED가 아닐 때 `null`), 조회 이유 표(보고서 주장 → trace 지표 순서, 기준값 있음/없음), 도구 표 7행 짝짓기·모델 요약·예산 차단 줄, 코드가 덧붙인 주장 4건 표시, 타임라인 13행과 발동 표시(`code_finding` 참, `status_aggregated`·`revision_discarded` 합성 사건), 차트 자료(막대 두 쌍, 시계열 없음, 합성 3달 지표로 시계열), 근거 ID 풀기 셋(끔·스냅샷 없음·임시 합성 픽스처로 6/6 풀림과 어긋난 규칙 1·4), 화면 모형에 float·절대 경로·홈 경로 없음, 상태 뜻 문구에 금지 표현(부정·위법·불법·원산지·조작·탈세·허위·적발·혐의·위반·"정상 확정") 없음, "사례 실행" 인자 조립(정상·재생·잘못된 여섯 가지, 값 비반복), 하위 프로세스 명령이 `-m tradesentry.cli`, 재생 파일 찾기, 키 유무·자식 환경, 새 폴더·표준 출력 파싱, 경로·키 모양 가림, wall time 한도 300초, 하위 프로세스 배관(인자 오류로 곧바로 끝나는 호출). 화면 층은 streamlit `AppTest`로 한 번 돌려 예외 0, 사이드바 선택 변경, 재생 실행 버튼 → 새 실행 폴더 자동 선택까지 확인했다(시험 파일에는 넣지 않았다. streamlit이 lock 밖이라 기본 시험 환경에 없기 때문이다).

⑨ **문서** — `docs/operations.md`에 "화면 1 실행" 항목, 루트 `README.md`에 "화면(선택)" 절, `docs/plan/UNITS.md`의 화면 단위 행과 판정 집계 줄, 이 기록과 색인 한 줄.

## 한계

- 봉인 묶음 출력(`outputs/sealed/`)은 나열·표시하지 않는다(금지 해제 조건 전. 자료 계약 §10.3 N10). 해제 뒤에도 이 화면은 그 폴더를 보지 않는다(직접 입력도 `outputs/run_case-…`만 받는다).
- 실자료 스냅샷 `kcs_202201_202412_v2`의 SQLite는 커밋하지 않으므로, 그 파일이 없는 작업 폴더에서는 실자료 실행의 원본 행이 풀리지 않고 근거 ID만 나열된다("스냅샷 없음"). 합성 픽스처는 `fixture.materialize()`로 만들 수 있다.
- 실행 폴더만으로 재생 실행인지 알 수 없다(⑤). 화면에서 시작한 실행만 표시한다.
- 시계열 차트(나)는 trace에 달별 `U`가 3개 이상일 때만 그려지고, 지금 흐름에서는 그려지지 않는다(③). 화면 2가 맡을 몫이다.
- "사례 실행"은 스트림릿 프로세스가 끝날 때까지 막히는 동기 실행이다(사례 1건 300초 한도). 동시 실행·취소는 없다.
- 표의 Decimal은 문자열 표기로 보인다(pyarrow 직렬화를 피하고 끝자리 0을 보존하려는 선택).
