# UI2 코드 PR: 담당자용 화면 3개(홈·사례 검토·결정 기록/재조사/도움) + 관리자 화면 통합 + 한국어/영어 전환 — 구성·재사용·기록 저장 위치·i18n·시험·한계

2026-09-26(토) 18:0x 사용자 승인 디자인("디자인은 이대로", scratchpad 정적 HTML 목업 세 장)의 코드 쪽이다. 화면 1 "사례 보기"(결정 기록 `20260926-0732-model-decision-ui-screen-1.md`)를 관리자용 네 번째 페이지로 감싸고, 그 위에 담당자용 화면 3개를 얹었다. 채점 경로(탐지·조사·검증·채점·판정 정책 코드, `eval/scorer/`, `configs/`)와 `src/tradesentry/app.py`는 한 줄도 바꾸지 않았다(룰북 `RB-1` 동결).

용어

- Streamlit: 파이썬 함수 호출로 웹 화면을 만드는 라이브러리. 스크립트를 위에서 아래로 다시 실행해 화면을 그린다.
- `st.navigation`/`st.Page`: Streamlit의 다중 페이지 구성. 페이지는 함수 하나 또는 스크립트 파일 하나다.
- 담당자용 모형: 실행 폴더의 기록을 평이한 문장(제목 한 문장, 절 4개)으로 옮긴 순수 자료(dict·list·str·Decimal). streamlit 없이 시험한다.
- 담당자 결정 기록(모의 승인): 담당자가 다음 업무 제안을 따를지 다르게 볼지 적은 기록. 단위 A1(`approval_record`)의 승인 기록 필드에 결정·사례·실행을 더한 것. 실제 기관 승인이나 통관 조치가 아니다.
- i18n(internationalization, 다국어 처리): 화면 문구를 키 → 언어별 문장 표로 두고 실행 시점에 언어를 고르는 방식.

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-26(토) 18:36(작업 시작 KST). 바탕은 `origin/main` 3712e76, 브랜치 `model/UI2-user-pages` |
| 제목 | 담당자용 화면 3개 + 관리자 화면 통합 진입 스크립트 + 순수 논리 패키지 `tradesentry.ui` + 단위 A1 구현 + 한/영 전환 |
| 결정 | 아래 ①~⑩ |
| 결정 주체 | 소유 트랙(M). 오케스트레이터 지시(브리프 UI2). 디자인은 사용자 승인 |
| 공용 약속 여부 | 아니다. 자료 계약의 객체·필드·상태값·명령·기준값은 바꾸지 않았다. 새 파일 위치(`src/tradesentry/ui/`, 결정 기록 파일 `outputs/approval_record-{시각}/`)는 자료 계약 §10 경로 표에 행을 더해야 한다(오케스트레이터가 보고를 받아 한다). 단위 A1의 `run`은 뼈대에서 구현으로 바뀌었고 입출력은 단위 표 `docs/plan/UNITS.md` §3.9의 "보고서·근거 digest → 승인 기록·`REVIEW_REQUIRED`" 안이다 |
| 관련 PR | 브랜치 `model/UI2-user-pages`(push·PR은 오케스트레이터가 한다) |

## 결정 내용

① **페이지 구성(진입 스크립트 `src/tradesentry/ui/ui_app.py`)** — `st.navigation`으로 페이지 4개: 담당자 홈(`home`, 기본), 사례 검토(`case`), 결정 기록·도움(`assist`), 관리자용 조사 기록(`admin`). 앞 셋은 `src/tradesentry/ui/screens/{home,case,assist}.py`의 `render()` 함수 페이지이고, 관리자용은 `st.Page("../app.py")`(진입 스크립트 폴더 기준 상대 경로 → `src/tradesentry/app.py`)로 기존 화면 1을 스크립트 페이지로 감쌌다. `app.py`는 고치지 않았고 import로 실행시키지도 않았다(Streamlit이 `__main__`으로 실행해 `main()`이 돈다. `st.set_page_config`를 두 번 부르는 것은 streamlit 1.64.0에서 허용됨을 AppTest로 확인했다). 사이드바 맨 위: 언어 전환(한국어/English 라디오, `st.session_state["lang"]`, 기본 한국어)과 스냅샷 선택(`app.list_snapshots` 재사용. 기본값은 정본 빌드가 있는 실자료 `kcs_202201_202412_v2`, 없으면 합성 픽스처 `controlled_fixture_v0`). 실행: `uv run --locked --with "streamlit==1.64.0" streamlit run src/tradesentry/ui/ui_app.py --client.showErrorDetails=false --server.port 8502`(8501은 기존 화면 1). streamlit은 lock 밖 `--with`다(결정 기록 0732 ①, `uv.lock` 불변).
- **위치를 지시서와 달리 정한 까닭**: 지시서는 `src/tradesentry/ui_app.py`(패키지 밖)였다. 자료 계약 §10.3 N2는 패키지 밖 모듈을 `ingest.py`·`app.py` 둘로 고정하고 `tests/test_units_registry.py`(`test_no_unregistered_module_files`)가 `src/tradesentry/*.py`를 등록부와 대조하므로, 진입 스크립트를 `ui/` 패키지 안에 두었다(저장소 규칙 우선, 브리프 "지시서와 저장소 규칙이 다르면 저장소 규칙").
- 페이지 이동: 홈 "결과 보기" → 사례 검토, "조사 시작" → 실행 뒤 새 실행 폴더로 사례 검토, 사례 검토 "내 결정 기록하기" → 결정 기록, "조사 과정 (관리자용)"·"원본 통계 행 보기" → 관리자용 페이지(`session_state["selected_run"]`을 넣어 `app.py`가 그 실행 폴더를 기본 선택한다). 선택 상태는 `session_state["selected_case"]`·`["selected_run"]`이다.

② **순수 논리 패키지 `src/tradesentry/ui/`(streamlit을 import하지 않는다. 시험 대상)**
- `i18n.py`: 문구 전부를 키 → `{"ko","en"}` 표(`STRINGS`, 약 230키)로. `t(key, lang, **자리표시)`. 판정 상태·조사 상태 이름표, 품목 이름(용어표의 HS6 4개. 합성 픽스처 코드는 `HS6 {코드}`), 국가 이름(`data/reference/country_map.csv`의 `kcs_country_name`(KO)·`baci_country_name`(EN)), 월 표기(KO "2024년 12월", EN "Dec 2024", 칩·표 머리는 언어 공통 "2024-12"). KO 문구는 디자인 목업의 문장을 그대로 옮겼고 EN은 지시서 용어표대로 번역했다. 두 언어의 키 집합·빈 값·자리표시 일치를 시험이 강제한다.
- `alerts.py`: 경보 목록은 CLI `detect`와 **같은 함수** `tradesentry.cli.dispatch.build_case_list`(→ 단위 P2 `policy.case_build.run`. 실자료는 분할 기록의 `real_dev` 계열만)로 만든다. 경보마다 단위 I2 `tools.get_history.run`의 봉투에서 `U`(기준월·비교월)·`r_U`·`s`(두 달)·`d_s`를 옮긴다(Decimal 그대로, None이면 "비교 불가"). 조사 상태(`investigation_index`·`investigation_status`)는 `outputs/run_case-*/runlog_run_record-*.json`의 `case_id`로 최신 실행을 찾아 조사 전(`NOT_INVESTIGATED`)·조사 완료(`INVESTIGATED`, `execution_status`=`COMPLETED`)·실패(`FAILED`)로 나눈다. 폴더 나열은 `app.list_run_dirs` 재사용(`outputs/sealed/`·`.download-*`·`.quarantine-*`·심볼릭 링크 제외). 요약 4칸(`summary`): 단가 변화 경보 수·점유율 변화 경보 수(사례의 `signals`가 `TRIGGERED`인 것)·조사 완료/전체·최근 24개월 합계(스냅샷 안 전체 경보 수). 화면이 지표·판정을 새로 계산하지 않는다.
- `plain.py`: `app.screen_model(resolve_rows=False)` 위에 담당자용 모형을 만든다. 제목 한 문장은 `r_U` 주장의 부호·절댓값 구간(30~40 "눈에 띄게", 40~60 "절반 가까이", 60~100 "크게", 100 이상 오름 "두 배 넘게")으로 고르고 숫자는 넣지 않는다. 단가 신호가 발동하지 않고 점유율 신호만 발동하면 점유율 문장, 값이 없으면 "비교할 수 없습니다" 문장. "무슨 일이 있었나"는 `app.trigger_table`(보고서 주장 → trace 지표 순)과 `chart_data`의 값·정책 기준값·발동 여부. "조사에서 확인한 것"은 있는 claim만 절로: `decomposition`(within/mix/residual 문장. 머리말은 기록된 `signal_status.unit_value`로 고른다 — MONITOR "구성이 바뀐 것으로 설명됩니다", MAINTAIN "구성이 바뀐 탓만으로는 설명되지 않습니다", HOLD "판정할 자료가 모자랍니다"), `comparison`(다른 상대국 문장 + "시장 전체 요인일 가능성"), `share`/`share_change`(점유율 문장. 머리말은 `signal_status.share`), HS10 하위품목 `r_U@`, `data_status`. "다른 설명 가능성"은 `hypotheses` 원문 + "조사자가 제시한 가설, 통계로 확인된 것은 아님". 결론은 판정 + `narrative` 원문 인용. 판정 3종의 뜻(자료 계약 §3.1을 평이하게), 근거로 삼은 것(스냅샷 ID, 전년 같은 달·기준값(`policy_v1`의 `thresholds`), 조사 방식 고정 문구, "사실 주장 N개 검증 통과"는 claim 수와 `validator_findings`가 비었을 때), 유의할 점(고정 문구). EN 모드는 틀 문장만 영어이고 `narrative`·`hypotheses` 원문은 한국어 그대로 두고 "(Korean original)"을 붙인다. **숫자는 claim과 기록에서만 옮긴다**(시험이 값 그대로임을 본다).
- `records.py`: 담당자 결정 기록. 필드 `{record_id, case_id, run_id, decision, suggested, memo, reviewer_label, timestamp, report_hash, evidence_digest, snapshot_id, policy_version, code_version}`. 핵심(해시·digest·거부·대조)은 단위 A1이 한다(④). 저장 위치와 이유는 ③.

③ **기록 저장 위치 — `outputs/approval_record-{yymmddhhmmss}/approval_record-{yymmddhhmmss}.json`(기록 하나가 실행 하나)** — 자료 계약 §10.3 N5(단위를 혼자 돌리면 그 도메인명이 실행 이름)·N6(출력은 `outputs/{실행명}/{도메인명}-{시각}.{확장자}`)·N8(덮어쓰기 금지. 그 초가 될 때까지 기다린 뒤 `exist_ok` 없는 `mkdir`, 실패하면 다음 초, `outputs/sealed/`에 같은 이름이 있으면 지우고 다음 초)을 그대로 따른다. 지시서 예시의 단일 JSONL(`outputs/approval_records/approval_records.jsonl`)은 한 파일에 덧붙이는 방식이라 N6(실행마다 파일)·N8(기존 파일을 다시 쓰지 않음)에 맞지 않아 쓰지 않았다. 추가 전용은 폴더가 늘어나는 방식으로 자연히 지켜진다. 읽을 때는 `outputs/` 바로 아래 `approval_record-*` 폴더(sealed·받는 중·격리·심볼릭 링크 제외)를 새 것부터 읽고, 기록의 `run_id` 실행 폴더의 지금 보고서와 대조해 `validity`(`VALID`/`REVIEW_REQUIRED`)를 붙인다. 실행 폴더가 없어졌거나 보고서 해시·근거 digest가 다르면 `REVIEW_REQUIRED`이고 기록 파일은 고치지 않는다.

④ **단위 A1행 `approval_record` 구현(`src/tradesentry/approval/record.py`)** — 입력 `{report, execution_status, reviewer_label, timestamp, code_version?}` → 승인 기록(자료 계약 §9.3 필드 7개 + `status: VALID`). `execution_status`가 `COMPLETED`가 아니거나 보고서에 `report_hash`가 없으면 ValueError(승인 불가). `report_hash`는 보고서 객체의 값(단위 R2가 §9.1 규칙으로 계산)을 옮기고 다시 계산하지 않는다. **`evidence_digest`의 계산 방법**(§9.3이 구현 때 정하라고 한 것): 보고서 `evidence_ids`를 정렬·중복 제거해 줄바꿈(`\n`)으로 이은 UTF-8 문자열의 sha256. 근거 행 내용이 아니라 근거 ID 집합의 digest다 — 동결 스냅샷의 행은 바뀌지 않으므로(CLAUDE.md 절대 규칙 2) 보고서가 기대는 근거 집합이 바뀌었는지만 본다. `check(record, report)`는 두 값을 대조해 `VALID`/`REVIEW_REQUIRED`를 돌려준다. `timestamp`는 부르는 쪽이 준다(단위는 시계를 읽지 않아 골든 시험이 결정적). 골든 쌍(`tests/units/{단위 ID}/`의 `input.json`·`expected.json`, 단위 ID 폴더는 A1행)을 두었다(중복 근거 ID가 digest에서 하나로 세어짐을 포함).

⑤ **재조사 요청** — `app.py`의 사례 실행 경로(`build_run_case_args` + `run_case_once` 하위 프로세스, `output_run_dirs`/`new_run_dirs`)를 재사용해 같은 사례를 `--mode full`로 다시 돈다. 재생 파일(`eval/dev/smoke/{case_id}.json`)이 있으면 키가 있어도 재생을 쓴다(실제 NIM 호출은 관리자용 화면에서 재생을 끌 때만). 키가 프로세스 환경에 없고 재생 파일도 없으면 버튼을 잠그고 안내 문구를 보인다(`app.py`와 같은 규칙. 앱은 `.env`를 읽지 않는다). 새 실행 폴더는 이력에 붙고 사례 검토가 그 폴더를 연다. 이유 체크 3개는 화면 표시용이며 저장하지 않는다. 홈의 "조사 시작"도 같은 경로다. 화면에서 시작한 실행과 재생 실행은 점수표 근거가 아니다.

⑥ **사후 확인 기록** — 비활성 라디오 + 설명("이 데모는 자료 갱신이 없어 사후 확인을 저장하지 않습니다"). 저장하지 않는다.

⑦ **N13** — 예외는 이름만 보이고 traceback·경로를 화면에 내지 않는다(`--client.showErrorDetails=false` + 화면 함수의 넓은 예외 처리). 화면·기록·문구에 로컬 절대 경로와 키 값이 없음을 시험이 본다(`ui/` 소스의 홈·임시 경로 패턴 부재, 모형 JSON의 경로 부재). `outputs/sealed/`는 나열·표시하지 않는다.

⑧ **디자인과 달리 한 것** — (가) 픽셀 재현이 아니라 Streamlit 기본 위젯(열·컨테이너·metric·radio)으로 정보 구조·문구·순서·강조만 옮겼다. 표는 `st.dataframe` 대신 열 레이아웃 행이다(행마다 버튼이 필요해서). (나) "조사에서 확인한 것"의 머리말은 목업의 사례별 문장("하위품목 구성이 바뀐 탓이 아닙니다", "중국만의 변화는 아닐 수 있습니다")을 그대로 쓰지 않고 기록된 `signal_status`로 고르는 중립 문장으로 바꿨다 — 목업 문장은 한 사례의 해석이라 다른 판정(MONITOR·HOLD)이나 비교국 방향이 다른 사례에 그대로 쓰면 틀릴 수 있어서다. "미국산 kg당 단가도 같은 기간 −59.8% 내렸습니다"류 비교 문장과 "시장 전체 요인일 가능성" 문장은 목업대로 두었다. (다) 결정 라디오의 첫 항목 "제안대로 {판정}"은 보고서의 판정을 맨 앞에 두고 나머지 둘을 뒤에 둔다(목업은 검토 유지 사례 하나만 그렸다). (라) 이력의 "경보 발동" 줄은 현재 스냅샷의 그 달 경보에서 지표를 찾을 때만 값(단가 −50.2%)을 적고, 다른 스냅샷의 사례면 값 없이 "경보 발동"만 적는다. (마) EN 판정 표기는 승인된 영문 목업·용어표대로 코드를 병기한다("Keep under review (MAINTAIN)", "Monitor (MONITOR)", "Data hold (HOLD)"). KO는 목업대로 코드 없이 쓴다(독립 검토 지적 반영).

⑨ **시험(`tests/test_ui_pages.py`, 25개 — 코드 커밋 때 23개, 후속 수정에서 이력 신호·완료 실행 필터 2개 추가)** — 순수 모듈이 streamlit을 import하지 않음(ast)·소스에 로컬 절대 경로 없음; i18n 키 집합·빈 값·자리표시 일치, 이름표·월 표기·국가 이름 두 언어, 판정 뜻 문구에 금지 표현 없음; alerts 지표 추출(가짜 봉투: 값 그대로 옮김·다른 상대국 무시·None 유지), `alerts_for_month`가 사례 목록과 이력 도구 요청 모양대로 부름, 조사 상태(임시 폴더의 가짜 실행 기록: 최신 실행 선택·실패·조사 전·sealed와 `.download-*` 제외·요약 4칸·필터 셋); plain(A2행 화면 단위의 재생 픽스처 KO·EN: 제목·값·절 종류·검증 문구·판정 표시, 합성 보고서(decomposition·comparison·share claim + 가설) KO·EN: 절 세 개와 숫자가 claim 값 그대로·원문 표시, COMPLETED가 아닌 실행의 판정 없음, 구간·제목 규칙); records·A1행(`approval_record`의 run·check 불변식, COMPLETED 아니면 거부, 잘못된 결정 거부, N8 이름 확보(소수 초 올림·같은 초 충돌·sealed 충돌)·추가 전용·다시 읽기·해시 변경 → `REVIEW_REQUIRED`·기록 파일 불변·실행 폴더 삭제 → `REVIEW_REQUIRED`, KST 시각). A1행 골든 시험은 뼈대에서 벗어나 실제로 돈다. 전체 시험 `env -u NVIDIA_API_KEY -u DATA_GO_KR_SERVICE_KEY -u TRADESENTRY_SEALED_DIR uv run --locked python -m unittest discover -s tests`: Ran 1642(코드 커밋 때 1640), OK(skipped=3), 종료 코드 0. 화면 층은 streamlit `AppTest`로 세 화면 × 두 언어(예외 0), 진입 스크립트(언어 전환·관리자 페이지 전환, 예외 0), 결정 기록 저장 → 이력 "[유효]" 표시까지 확인했다(시험 파일에는 넣지 않았다. streamlit이 lock 밖이라 기본 시험 환경에 없기 때문이다).

⑩ **하지 않은 것** — 사후 확인 저장, 계정·권한·인증, 채점 경로·`app.py`·`configs/`·`uv.lock` 변경, 지표·판정 재계산, 실제 NIM 호출, `outputs/sealed/` 열람, 문서(`UNITS.md`·자료 계약 §10·README·operations·status) 수정(오케스트레이터가 한다).

## 한계

- 실자료 사례의 조사는 키가 있을 때만 화면에서 시작할 수 있다(재생 파일은 합성 픽스처 A·B·C만). 키 없이 띄운 화면에서 실자료 홈의 "조사 시작"은 잠기고, 결과는 CLI나 키 래퍼 아래 화면으로 만든 실행 폴더를 새로 고쳐 본다.
- 결정 기록은 폴더 하나에 기록 하나라 기록이 늘면 `outputs/` 폴더가 늘어난다(데모 규모에서는 문제 없다). 기록 색인은 매 렌더마다 폴더를 다시 읽는다.
- `evidence_digest`는 근거 ID 집합의 digest다. 스냅샷 행 내용이 바뀌는 경우는 동결 규칙이 막으므로 감지 대상에 넣지 않았다.
- 화면의 이력 "경보 발동" 값은 현재 선택한 스냅샷의 경보 목록에서만 찾는다(⑧ (라)).
- 담당자용 문장은 판정 정책의 뜻을 평이하게 옮긴 것이며 판정을 바꾸거나 새로 해석하지 않는다. `narrative`·`hypotheses`는 한국어 원문 그대로다(EN 모드에서도).
