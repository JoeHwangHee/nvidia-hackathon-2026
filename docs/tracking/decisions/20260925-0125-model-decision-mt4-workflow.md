# MT4 조사 흐름·NIM 호출·NAT 감싸기·실행 기록의 해석과 약속

MT4(조사 흐름·NIM 호출·NAT 감싸기·실행 기록, 모델 트랙) 구현(단위 L1~L3·I7~I13, PR #29)에서 자료 계약과 룰북이 정하지 않았거나 모델 트랙(M)에 맡긴 세부와, 검토 1회차(평가 방법론, NVIDIA 스택, 보안)가 요구한 해석을 적는다. 코드와 시험은 PR #29에 있다. 항목마다 **확정** 또는 **잠정**을 붙였다. 잠정 항목 가운데 ①·②·③·⑨는 2026-09-25(금) 09:00 사용자 결정 안건(원인 분류 코드 이름과 결정 D12)에 올린다.

용어

- NIM: NVIDIA 클라우드 추론 API. OpenAI 호환 chat completions 형식이다.
- NAT: NVIDIA NeMo Agent Toolkit 1.9.0. 에이전트 실행을 추적하고 프로파일(토큰·지연 측정)을 내는 도구 모음이다.
- trace: 사례 실행 1건의 호출과 응답을 순서대로 남긴 기록(단위 L1, `runlog_trace-{시각}.jsonl`).
- 원인 분류 코드: 실행 결과 기록 `errors` 항목의 `code`. 실행을 멈춘 원인 하나를 적는다(단위 L3).
- 인프라 실패 재실행: 룰북 B5가 허용하는, 모델 제공자 쪽 오류로 `FAILED`가 된 실행을 같은 설정으로 한 번 다시 돌리는 일.
- 결정 D12: 인프라 실패 재실행 규칙의 빈칸(어떤 원인을 재실행 대상으로 볼지). 2026-09-25(금) 09:00 사용자 결정 안건이다.
- 정책 프록시: OpenShell(에이전트를 격리해 돌리는 NVIDIA 샌드박스 런타임) 샌드박스 안 감독 프로세스가 바깥 요청의 목적지·실행 파일·HTTP method·path를 검사하는 부분.
- CONNECT 403: HTTPS 터널을 열어 달라는 요청을 정책 프록시가 거부한 응답. L7 거부: HTTP 요청의 method·path가 정책에 맞지 않아 정책 프록시가 준 HTTP 403.
- 조기 종료: 비교 불가가 확정되면 이력·하위 조회를 건너뛰는 흐름 규칙(개발 플랜 §6.6).
- 허용 상태 조합: 발동하지 않은 신호는 `NOT_TRIGGERED`, 발동한 신호는 판정 상태, 사례 판정은 발동 신호 판정을 `MAINTAIN > HOLD > MONITOR`로 묶은 값이라는 규칙(자료 계약 §3.1).
- 조립 AS2: 사례 조사 조립 작업(로드맵). 도구 봉투를 판정 정책·검증기 입력으로 옮기는 변환을 맡는다.
- 구조화 출력: NIM이 응답을 JSON 모양으로 묶어 내게 하는 요청 옵션. `response_format` `{"type": "json_object"}`(JSON 객체만 요구)와 `nvext.guided_json`(주어진 JSON 스키마를 따르게 디코딩을 제한)이 있다. 이 모델·엔드포인트에서는 앞의 것만 받는다(⑯).
- 스모크 하네스: 오케스트레이터가 실제 NIM으로 사례 1건을 돌려 보는 저장소 밖 시험 스크립트(`scratchpad/mt4/live_smoke.py`).

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 01:25(기록 시각). ①~⑭는 2026-09-24(목) 밤 MT4 구현과 2026-09-25(금) 새벽 검토 1회차 수정 중에 정했고, ⑮와 ③의 세는 법 한 곳 모음은 같은 날 01시대에 오케스트레이터 알림(MT2 평가 검토의 토큰 위험)을 받아 더했다. ⑯은 같은 날 05시대 실측(실제 NIM 스모크 두 모드와 탐침) 뒤 수정 3회차에 더했고, 구조화 출력 켜기는 3회차 실측 뒤 오케스트레이터 판단으로 확정했다 |
| 제목 | MT4의 원인 분류 코드·재실행 입력, 도구 시도 세기, Critic 사용 기준, 조기 종료와 비교 가능 키, 기록 없이 끝나는 경로, 초안 형식 검사 범위, 모드 사이 메시지, 정책 프록시 거부, 키 취급, 요청 설정, trace 추가 값, 배선과 조립 인계, 모델용 근거 보기와 누적 토큰, 도구를 주지 않는 초안 요청과 구조화 출력 |
| 결정 | 아래 "결정 내용" ①~⑯ |
| 이유와 근거 | 아래 "결정 내용"의 항목마다 적었다 |
| 검토한 대안 | 아래 "검토한 대안" |
| 결정 주체 | 소유 트랙(M). ①·②·⑨는 사용자 결정(09:00 안건) 뒤 확정하고, ③은 사용자 확인 뒤 확정한다. ⑮의 남은 위험(비교 뒤 수정 단계가 붙는 경로)을 어떻게 풀지는 오케스트레이터와 사용자가 정한다. ⑯의 구조화 출력 켜기(`json_object`)는 3회차 실측 뒤 오케스트레이터가 정했다 |
| 공용 약속 여부 | ①(원인 분류 코드 이름)은 평가 구성에 닿아 공용 약속으로 본다(병렬 개발 규칙 §4.5: 애매하면 공용 약속). ③은 계약 필드 `tool_attempts`의 해석이라 사용자 확인을 받는다. 나머지는 M 소유 단위의 입출력과 흐름 세부다. 자료 계약의 필드·상태값·기준값·한도 값은 바꾸지 않았다 |
| 영향 | 아래 "영향과 넘길 곳" |
| 관련 PR | #29 |

## 결정 내용

① **원인 분류 코드 11개와 실행 상태** — 잠정(2026-09-25(금) 09:00 사용자 결정 안건. 이름 전체가 D12에서 바뀔 수 있다)

- `PROVIDER_HTTP_5XX`·`PROVIDER_CONNECTION`(`FAILED`, 재실행 대상), `PROVIDER_HTTP_4XX`·`PROVIDER_REQUEST_TIMEOUT`·`PROVIDER_BAD_RESPONSE`·`CODE_ERROR`(`FAILED`, 재실행 대상 아님), `BUDGET_MODEL_REQUESTS`·`BUDGET_TOKENS`(`BUDGET_EXCEEDED`), `DEADLINE`(`TIMEOUT`), `SCHEMA_INVALID`·`VALIDATOR_BLOCKED`(`INVALID`)다. 코드와 실행 상태의 대응은 `src/tradesentry/runlog/cause_codes.py` 한 곳에 있다.
- 재실행 대상 판정은 `infra_rerun_eligible` 하나로 한다: 실행 상태가 `FAILED`이고 `errors`의 모든 코드가 `PROVIDER_HTTP_5XX`·`PROVIDER_CONNECTION`일 때만 참이다. 룰북 B5의 "모델 제공자 쪽 오류(… 연결 실패)"를 옮긴 것이다 `[사실: cause_codes.py, 시험 tests/units/L3]`.
- `errors`에는 실행을 멈춘 원인 하나만 적는다. 재전송으로 흡수한 5xx와 막힌 도구 시도는 trace에만 남긴다. 그래야 "원인이 모델 제공자 쪽 오류뿐인 `FAILED`" 판정이 흐려지지 않는다.
- 이유: 룰북 B5와 평가 스킬 ②가 코드 이름을 "자료 계약이나 S0에서 정한다 `[미확인]`"로 남겼다. 이름을 바꿔도 단위 L3 한 파일과 시험만 고치면 된다.

② **결정 D12에 올리는 분류(지금 값)** — 잠정(D12 결정 뒤 확정)

- HTTP 429: `PROVIDER_HTTP_4XX`, 재실행 대상 아님. 재전송하지 않는다.
- 요청별 제한 시간 초과(최대 60초, 사례 deadline 전): `PROVIDER_REQUEST_TIMEOUT`, 재실행 대상 아님. 연결 단계의 시간 초과(`URLError(socket.timeout)`)도 여기로 온다.
- 정책 프록시 거부: `CODE_ERROR`, 재실행 대상 아님(⑨).
- 본문을 받는 도중 끊김(`http.client.IncompleteRead`): 전송 자리에서 잡지 않아 흐름 조정이 예외 이름을 적는 `CODE_ERROR`가 된다(detail `IncompleteRead`), 재실행 대상 아님 `[사실: 검토 1회차 탐침]`.
- 평가 스킬 ②의 "중단 원인 코드"에 해당하는 코드는 단위 L3에 없다. `CODE_ERROR`로 쓸지 새 코드를 둘지 D12에서 함께 정한다.

③ **`tool_attempts`의 뜻** — 잠정(계약 필드의 해석, 사용자 확인 대상)

- 실행한 도구는 사례당 8회를 넘지 않는다. 흐름 조정(단위 I12)의 단계별 몫(기본 경로 5회: `check_comparability`·`get_history`·조사자 비교 최대 2회와 `verify_evidence` 1회 예약, 수정 단계 재조회 2회, 최종 `verify_evidence` 1회)과 도구 예산 단위 I6가 함께 막는다.
- 실행 결과 기록의 `tool_attempts`는 막힌 시도까지 센 기록 값이다(자료 계약 §8.1 "넘은 실행은 실제 값"). 그래서 `COMPLETED` 실행도 `tool_attempts`가 8을 넘을 수 있다(예: 실행 8회 + 막힌 시도 2회 = 10) `[사실: tests/units/I12/test_orchestrate.py test_tool_shares_cap_executed_tools_at_eight]`. MT2의 단위 I6도 같은 해석이다(막힌 시도는 기록에만 들고 예산을 쓰지 않는다) `[사실: MT2 브랜치 src/tradesentry/tools/budget.py 머리말]`.
- 로드맵 MVP 체크리스트 2번("9번째 도구 시도 차단")의 증거 문구는 "실행한 도구 8회까지, 막힌 시도는 `tool_attempts`에만"으로 적기를 제안한다. 룰북 B7의 "도구 시도 중앙값"도 이 기록 값을 쓴다.
- MT2 평가 검토는 반대로 (가) "도구에 닿은(ok·failed·cache_hit) 시도만 세고 막힌 시도는 trace `budget_block`으로만 남기기"를 권한다(자료 계약 §5.3의 `tool_attempts ≤ 8`이 기록 값에서도 참이 되고, 모델 모드의 비용이 부풀지 않는다). 그래서 세는 법을 흐름 조정의 `COUNT_BLOCKED_TOOL_ATTEMPTS` 한 줄에 모았다(지금 참 = 막힌 시도까지). 흐름은 도구에 닿은 시도와 막은 시도를 따로 세고, 기록·trace·원인 항목의 `tool_attempts`는 이 값으로 계산한다. 집행(실행 8회)과 `budget_block` 기록은 어느 값에서나 같다 `[사실: tests/units/I12/test_orchestrate.py test_tool_attempts_counting_rule_is_one_switch]`. 사용자가 (가)를 고르면 이 한 줄을 바꾸고 이 항목을 고친다.

④ **`critic_used`와 `revision_used`의 기준** — 확정

- `critic_used`는 Critic 단계를 연 때 참이다. Critic 요청 중에 멈춘 실행(예: 5xx 재전송 한도)도 Critic을 쓴 실행으로 센다. `revision_used`는 수정 단계를 연 때 참이다. 두 값의 기준을 "단계를 열었나"로 맞췄다.
- `agent`는 Critic이 없고 `checklist`는 Critic·수정이 없다(단위 L2가 검사한다). 첫 초안이 형식·보고서 스키마 검사에 실패하면 Critic을 건너뛴다(개발 플랜 §6.6).

⑤ **조기 종료와 비교 가능 키** — 확정(키 이름은 MT2 단위 I1 봉투 정의를 따른다)

- 비교 불가 여부는 `check_comparability` 봉투의 `comparability.comparable`(참거짓)로 본다 `[사실: MT2 브랜치 src/tradesentry/tools/check_comparability.py 머리말 "comparable: 두 신호 가운데 하나라도 계산할 수 있으면 참"]`. 키가 없거나 참거짓이 아니면 `CODE_ERROR`로 멈춘다. 1회차의 "없으면 비교 가능"은 봉투 모양이 다를 때 조기 종료를 조용히 끄므로 버렸다.
- 거짓이면 `get_history`를 건너뛰고, 기본 단계와 수정 단계 모두 조사자 요청에 도구를 주지 않는다. 모델이 그래도 도구를 부르면 부르지 않고 막는다(`budget_block` 종류 `not_comparable`, `tool_attempts`에는 센다). 남은 비교·재조회 횟수는 0회로 알린다. 조기 종료는 프롬프트가 아니라 코드가 강제한다(개발 플랜 §6.6, 룰북 B2의 checklist 행).
- `verify_evidence`(코드가 예약한 근거 대조)는 비교 불가 사례에서도 부른다. 이력·하위 조회가 아니라 초안이 가리킨 근거의 대조다.

⑥ **기록 없이 끝나는 경로** — 확정

- 실행 전에 정해지는 키 9개(`run_id`·`case_id`·`dataset`·`mode`·`policy_version`·`rulebook_version`·`snapshot_id`·`grouping_version`·`code_version`)는 흐름을 시작하기 전에 단위 L2 `check_static`으로 본다. 틀리면 모델 요청·도구를 쓰기 전에 `ValueError`로 멈춘다(모드·사례 키 검사와 같다). 1회차에는 흐름을 다 돈 뒤 끝에서 멈춰 NIM 요청과 도구를 쓰고도 기록이 없었다.
- 필수 근거(단위 P5) 계산은 흐름의 `try` 안으로 옮겼다. 실패도 `CODE_ERROR` 기록(`run_start`·`run_end` 포함)으로 남는다.
- 남는 경로는 흐름 시작 전의 입력 오류(모드·사례 키·실행 전 키)와 개발용 재생 진입 함수의 재생 불일치뿐이다. 묶음 실행(단위 E1)은 "목록에 있는데 줄이 없으면 실패"로 세므로 분모는 지켜진다 `[추론]`.

⑦ **초안 형식 검사의 범위** — 확정(검토 1회차 막는 지적 1)

- 모든 모드에서 막는 초안 형식 문제: JSON 객체 하나, 초안 키 다섯, 상태값 집합(`review_status` 3값, `signal_status`의 키 `unit_value`·`share`와 4값), 주장·설명·가설의 형식과 자료형, 응답이 `max_tokens`에서 잘림(`finish_reason` `length`).
- 허용 상태 조합은 초안 형식 문제가 아니다. 룰북 B2의 스키마 검사는 형식·자료형과 발동 신호별 주장 요건(자료 계약 §9.4)만 본다. 그래서 이 조합은 검증기 부류(단위 R3 `STATUS_INCONSISTENT`)가 맡는다: `full`·`agent`·`checklist`에서는 막고 `freeform`에서는 기록만 한다. 조사자는 관찰(`status_notes`)만 돌려주고 흐름 조정이 trace에 남긴다. 1회차에는 이 조합을 모든 모드에서 막아 기준선 `freeform`에 검증기 차단이 샜다.
- 보고서를 만들 때 단위 P4(사례 집계)가 발동 여부와 판정의 불일치로 `ValueError`를 내면, 상태를 고치지 않고 `unresolved_evidence`를 발동 신호 기준(P4·R3와 같은 기준)으로 세어 보고서를 만든다. 다른 예외는 그대로 낸다. 병합된 R1~R4·P4로 돌린 통합 시험에서 `freeform`은 사유를 기록만 하고 `COMPLETED`, `full`은 검증기 차단 뒤 수정으로 `COMPLETED`였다 `[사실: tests/units/I12/test_orchestrate.py MergedUnitsTest]`.

⑧ **모드 사이 메시지** — 확정(검토 1회차 막는 지적 3)

- 조사자 메시지에 모드 이름을 넣지 않는다. 모드 사이 차이는 시스템 지침 뒤쪽의 claims 지침(`claims_template.txt`·`claims_freeform.txt`)뿐이다. Critic 메시지도 사례·근거·초안만 싣는다. 룰북 B2 "`freeform`은 `full`과 처리만 다르고 나머지는 같다"를 따른다.
- 시험: `agent`와 `full`의 첫 메시지 목록이 글자까지 같고, `full`과 `freeform`은 claims 지침만 다르며, 사용자 메시지에 모드 이름이 없다. I12 골든 입력의 `model_request`에 `request_sha256`을 넣어, 요청 본문(프롬프트 포함)이 바뀌면 재생이 실패한다.

⑨ **정책 프록시 거부 가르기** — 잠정(코드 이름은 D12와 함께 정한다)

- 모양 둘을 전송 자리(단위 I7)가 가른다 `[사실: artifacts/openshell/violation_tests.md V0a·V1·V2b·V3, Python 3.12.13 http.client의 터널 오류 문구]`: CONNECT 403·407(파이썬에서는 `URLError(OSError("Tunnel connection failed: 403 …"))`)과 L7 거부(HTTP 403, JSON 본문의 `error`가 `policy_denied`). 다른 터널 상태(예: 502)는 상류 실패일 수 있어 연결 실패(`PROVIDER_CONNECTION`)로 둔다.
- 재전송하지 않고 `CODE_ERROR`로 멈춘다. 모델 제공자 쪽 오류가 아니므로 재실행 대상이 아니다. 새 코드 이름은 짓지 않았다.
- 가르는 값: `errors` detail `policy_denied(connect) 403`·`policy_denied(l7) 403`, trace `model_error`의 `http_status`(프록시가 준 상태)·`error` `policy_denied`·`denial`(`connect`·`l7`). 기록 재생(단위 I8)도 `denial`을 그대로 돌려준다. 프록시 응답 본문(실행 파일 경로가 들어 있다)은 어디에도 싣지 않는다.

⑩ **키 취급 보강** — 확정(보안 검토 권고 1·2·6, NVIDIA 검토 권고 4)

- 리디렉션을 따라가지 않는 opener로 보내고 `Authorization`은 리디렉션 요청에 옮겨 가지 않는 헤더(`add_unredirected_header`)로 싣는다. 3xx는 `PROVIDER_BAD_RESPONSE`로 멈춘다. 그래서 키가 다른 호스트로 가지 않고, `model_requests`에 세지 않는 HTTP 시도도 생기지 않는다. 프록시 환경변수는 표준 처리기대로 따른다.
- 키 환경변수 값이 공백 없는 출력 가능 ASCII가 아니면 요청을 세기 전에 변수 이름만 담은 오류(`CODE_ERROR`)로 멈춘다. 표준 라이브러리의 헤더 검사 예외는 문장·repr에 값을 싣기 때문이다. OpenShell 자리표시 값(`openshell:resolve:env:…`)은 이 형식에 든다 `[사실: spikes/x1/key_check.py PLACEHOLDER_PREFIXES]`.
- 설정은 허용 목록만 받는다: 엔드포인트는 `https://integrate.api.nvidia.com`(443, 사용자 정보 없음), 키 환경변수 이름은 `NVIDIA_API_KEY`·`NVIDIA_INFERENCE_API_KEY`. 샌드박스 종류(채점 대상 실행용·시연용)에 따라 어느 이름을 쓸지는 CLI(로드맵 MT5)가 정한다. 스킬이나 하네스 입력에서 받지 않는다(개발 플랜 §5.2).

⑪ **요청 설정과 `max_tokens`** — 확정(조정값)

- `temperature` 1.0·`top_p` 0.95·`enable_thinking` 끔은 구 개발계획 G4 관문 시험(`scripts/g4_nim_toolcall_probe.py`)에서 확인한 조합이다. 모든 모드가 같다.
- `max_tokens` 2048은 G4 확인값(1024)과 다른 조정값이다. 1회차 구현 보고의 "G4에서 확인한 조합(max_tokens 2048 포함)"은 틀린 문장이라 이 기록으로 바로잡는다. 한국어 `freeform` 초안(주장마다 12필드)이 1024를 넘을 수 있어 2048로 둔다 `[추론]`.
- 응답이 잘리면(`finish_reason` `length`) 조사자 초안은 형식 문제로 수정 단계나 `SCHEMA_INVALID`로 가고, Critic 답은 문제 목록 맨 앞에 적는다. trace `model_response`에 `finish_reason`이 남는다. 2048이 넉넉한지는 실측 스모크의 `finish_reason`으로 1건 확인한다.

⑫ **trace 추가 값** — 확정

- `state_change`의 `draft`·`revised`에 `problem_list`(초안 형식 문제)·`status_notes`(허용 상태 관찰), `after_critic`에 Critic `problems`, `validator_result`에 `rejected_requests`(틀 채우기가 채우지 못해 버린 요청, 단위 R1 `rejected`), `model_error`에 `denial`을 더했다. 기존 키(`problems` 개수 등)는 그대로다.
- 개발용 재생 진입 함수는 재생이 끝났는데 기록된 응답·봉투가 남으면 `ReplayMismatch`다.

⑬ **배선(`unit_ports`)과 조립 AS2 인계** — 잠정(`[미확인]` 표시한 대응은 AS2에서 확정)

- 병합된 단위의 입출력에 맞췄다: R1~R4(자료 상태의 상대국 키 `partner_code`, 근거 ID `evidence_id` 하나, 같은 항목은 한 번), P3(근거 상태에 기본값 없음), P4(`signals`·`signal_status`), 도구 예산 I6(한도 키 `tool_attempts`·`basic_tool_attempts`·`revision_stages`·`revision_requeries`·`final_verify`를 모두 넘긴다).
- 정책 객체(단위 K4)의 `thresholds.unit_value`·`share`를 검증기 R3 입력 `thresholds`(수 목록, 개발 정책 `dev-0.1`은 30과 10)로 옮겨 모든 모드에 넘긴다. R3는 형식이 틀린 값을 오류 없이 버리므로 int·Decimal만 넘기고, 다른 형식이면 실행 전에 `ValueError`다.
- `checklist`의 P3 근거 상태는 AS2 변환 훅 `evidence_state(사례, 봉투 목록)`을 받는다. 없으면 `missingness`와 발동 신호 블록의 `comparisons`만 채우고(P3가 입력 오류로 멈춰 `CODE_ERROR`가 된다), `comparisons`는 흐름이 받은 봉투로 `done`·`not_performed`를 적는다. 비교와 도구의 대응(`comparability` ← `check_comparability`, `partners` ← `compare_partners`, `country_and_world` ← `get_history`)과 `incomplete` 가리기는 `[미확인]`이다.
- AS2가 넘길 것: `policy`(K4), `rows`(근거 ID → 스냅샷 행, 단위 K3), `evidence_state`(나머지 근거 상태 키, 반올림 전 정확값). AS2에서 맞출 것: C형 자료 상태(부모 HS6 행이 있는 키에서 HS10 하위 자료만 빠짐)의 `hs10` 채우기(`observation_status@<HS10>`), 도구 요청의 선택 키(`policy_version`·`grouping_version`·`attempt`·`verify_evidence`의 `envelopes`, MT2 도구 공통 틀), R3의 선택 입력 `hs_codes`.
- MT2가 C형 사례의 빠진 HS10 코드를 봉투의 목록 필드로 싣도록 고치는 중이다(모양 미정). 모델용 보기(⑮)는 비교 가능성 전체와 빠진 자료 항목의 새 키를 그대로 남기므로 그 필드가 모델에게 간다. 자료 상태 항목의 `hs10` 채우기는 모양이 정해지면 `_statuses_of`나 AS2 변환에서 맞춘다.

⑭ **1회차 구현의 나머지 해석** — 확정(M 소유 단위의 세부)

- `COMPLETED`가 아닌 실행의 `signal_status`는 null, `review_status_final`은 null, `unresolved_evidence`는 false다. DT8 채점기도 null을 받는다 `[사실: 검토 1회차 평가 방법론 보고]`.
- 토큰 한도는 엄격하다: 요청마다 `max_tokens`를 남은 토큰으로 줄이고, 응답 뒤 누적이 32,000을 넘으면 `BUDGET_TOKENS`다. 5xx만 요청당 3회 재전송하고(1·2·4초 대기, 재전송도 `model_requests`에 센다), 연결 실패·4xx·요청별 시간 초과는 재전송하지 않는다. 종료 기록 예약 시간은 5초(조정값)다.
- `wall_ms`는 흐름 조정 시작부터 끝까지다(NAT 불러오기·프로파일 시간은 빠진다). 한도와 재전송 수치는 `configs/model/model.json` 한 곳에 있다.
- 틀 채우기 모드의 주장은 `metric_id`나 근거 ID로 가리키고 R1이 값을 채운다. `rulebook_version`·`code_version`은 빈 문자열이 아닌 문자열이면 받는다.
- NAT 출력: N7 폴더 `outputs/{실행명}/workflow_nat_wrap-{시각}/` 안에 NAT가 정한 이름(`nat_trace.jsonl`과 프로파일 파일 5개)으로 쓴다. NAT 설정 사본은 쓰지 않는다(로컬 절대경로가 들어간다). NAT를 불러오는 함수는 모두 먼저 `.env` 자동 로드와 텔레메트리를 끈다(`nat` 명령 진입점과 의존성 pymilvus가 import 때 `.env`를 읽는다).

⑮ **모델용 근거 보기와 누적 토큰** — 확정(보기 규칙). 남은 위험은 잠정(오케스트레이터·사용자 판단)

- 이유: MT2 평가 검토의 추정으로, 실자료 크기 봉투(비교 가능성 약 2,500자, 이력 약 7,800자, 비교국 약 8,200자, HS10 분해 약 18,500자)에서 1회차 보기는 봉투를 1~8%만 줄여 분해를 쓴 `full`·`freeform`과 수정 단계가 붙는 경로가 누적 토큰 한도 32,000을 넘었다 `[추론: MT2 평가 검토의 가정별 추정]`. 그러면 수정 단계를 자주 타는 `full`에 `BUDGET_EXCEEDED`가 몰려 대표 지표가 검증기의 효과가 아니라 토큰 소진을 잰다. 한도(공용 약속의 도구·모델 한도)는 바꾸지 않았다.
- 조사자 보기(단위 I10 `compact_envelope`, 모든 모드 같음): 도구 이름, 도구가 본 범위 가운데 사례 머리에 없는 것(`partners`·`hs10`), 지표의 `metric_id`·기호와 대상(`metric`·`partner`·`period`·`baseline_period`)·값·단위·비교 표시·근거 ID, 비교 가능성 전체, 빠진 자료(`request_id`·`flow` 밖의 키 전부), 재시도할 수 있는 오류만 남긴다. 계산 입력 원값(V·Q·`hs10_values`)·`formula_version`·`tolerance`·`query_id`·`snapshot_id`·`source_kind`·`elapsed_ms`는 뺀다. 봉투 수준 `evidence_ids`는 보기의 다른 곳에 나온 ID를 빼고 남겨, 봉투의 모든 근거 ID가 한 번 이상 나온다. 원본 봉투는 흐름 조정이 들고 검증기·틀 채우기·정책에 쓴다.
- Critic 보기(단위 I11 `evidence_view`, `full`·`freeform` 같음): 조사자 보기에서 지표마다의 근거 ID 목록을 걷어 봉투마다 한 목록으로 모은다. Critic은 근거의 짝을 대조하지 않으므로(검증기 R3의 일) 목록 하나로 충분하다.
- 추정 시험(`tests/units/I12/test_token_estimate.py`): 실자료 크기에 맞춘 합성 봉투(HS10 8개, 39,435자 → 조사자 보기 24,108자, Critic 보기 17,544자)로 실제 흐름을 돌리고, 요청 본문 글자로 토큰을 추정한다(ASCII 3자·그 밖 1.3자 = 토큰 1) `[추론: 토크나이저가 아닌 글자 비율]`. `full` 비교국 1회 + Critic 약 17,500, `agent` 비교 2회 약 23,100, `full` 비교 2회 + Critic 약 31,200(1회차 보기로는 약 45,900), `full` 비교 없이 Critic + 수정 약 15,800은 한도 안이다. 다만 `full` 비교 2회 + Critic은 여유가 3%가 안 된다. 근거 ID와 숫자열은 보통 글자 3자보다 짧게 토큰이 나뉘므로 실제로는 넘을 수 있어 실측으로 정한다. `tool_attempts` 세는 법(③)의 한 줄을 어느 값으로 두어도 단위 시험이 모두 통과한다 `[사실: 두 값으로 단위 시험 546개를 돌린 결과]`.
- 남은 위험: 조사자 비교 뒤 수정 단계가 붙는 경로(약 33,100~42,600)는 여전히 넘는다. 대화 전체가 요청마다 다시 가기 때문이다. 풀 방법(정하지 않음): (가) 한도를 모든 모드에 같게 올린다(공용 약속, 사용자 승인), (나) 근거 ID의 공통 앞부분(`ev:{snapshot_id}:observation:`)을 줄여 보인다(인용 형식이 바뀌어 잘못 쓴 ID가 검증기 사유가 될 수 있다), (다) 조사자 지침에 "필요한 비교는 한 차례에 함께 부른다"를 더한다(`full` 비교 2회를 한 차례로 부르면 약 24,700), (라) 실측 스모크로 실제 `prompt_tokens`를 먼저 잰다. 글자 비율이 실제보다 낙관적이면 경로 값이 더 커진다.

⑯ **도구를 주지 않는 초안 요청, 구조화 출력 설정, 빈 대조 건너뛰기** — 확정(메시지·키 규칙, 구조화 출력 `json_object` 기본, `model-0.2`)

- 실측 사실(2026-09-25(금) 04:58~05:00, 모델 `nvidia/nemotron-3-super-120b-a12b`, 사례 A 합성, trace `outputs/run_case-260925045829`·`-045848`은 커밋하지 않음)
  - `freeform`의 요청 3·4는 trace `model_request`의 `tools`가 0이었다. 곧 요청 본문에 `tools`·`tool_choice`가 없었다(`ModelClient.build_payload`는 도구가 없으면 두 키를 싣지 않는다). 그런데도 모델은 두 요청 모두 구조화된 `tool_calls`(`decompose_hs`, 이미 실행한 도구)를 돌려주었다. 흐름이 두 번 막고(`comparison_limit`) "도구 없이 초안을 쓰라는 요청에 두 번 도구를 불렀다"를 형식 문제로 적어 수정 단계로 갔다 `[사실: trace]`.
  - 그 두 요청의 마지막 사용자 지시는 첫 메시지의 "필요하면 도구로 추가 비교를 하고"와 "추가 비교 2회"(처음 값 그대로)였다. 거부 결과는 `{"blocked": true, "reason": "comparison_limit"}` 한 줄이었다 `[사실: 코드]`. 모델이 도구가 닫힌 것을 알 글이 없었다 `[추론]`.
  - 따라서 "NIM은 `tools` 없는 이력 요청에서 도구를 억지로 부르지 않는다"는 탐침 결론은 일반화되지 않는다. 이 모델·NIM 조합에서는 **`tools`를 빼도 도구 호출이 막히지 않는다**. 흐름 쪽 거부(`budget_block`)는 그래서 계속 필요하다.
  - 도구 이력 뒤 `tools` 없는 탐침 요청 2·3은 도구를 부르지 않았지만 본문이 JSON 객체가 아니었다(440자·145자) `[사실: 오케스트레이터 탐침]`. `full`의 수정 단계 응답 본문에는 `enable_thinking` 끔인데도 영어 추론 글과 `</think>`가 섞여 나왔다(그 응답은 도구 호출이라 초안 파싱과는 무관) `[사실: trace]`. 탐침의 440자가 같은 까닭인지는 확인하지 않았다.
- 도구를 주지 않는 차례의 초안 요청(단위 I10)
  - `allow_tools`가 거짓이면 요청에 `tools`·`tool_choice`를 싣지 않고, 대화 끝에 초안 요청 메시지 `DRAFT_REQUEST`를 붙인다. 내용: 이 요청에는 도구가 없고 추가 비교·재조회는 더 할 수 없으며 부르면 거부된다, 지금까지의 근거만으로 쓴다, 설명·머리말·코드 블록 없이 JSON 객체 하나(첫 글자 `{`, 마지막 글자 `}`), 윗단계 틀 한 줄(claims는 "시스템 지침의 claims 쓰는 법대로").
  - 모든 모드에서 글자까지 같다. 모드 이름·claims 세부·금지 낱말은 넣지 않는다(룰북 B2, 시험 `tests/units/I10/test_investigator.py`). 막힌 차례마다 한 번 붙고 대화에 남는다.
  - 비용: 요청 하나에 약 200토큰(추정)이다. 누적 추정은 `agent` 비교 2회 약 23,300, `full` 비교 2회 + Critic 약 31,400(여유 약 2%, 이전 31,200)이다 `[추론: 글자 비율 추정]`. ⑮의 남은 위험은 그대로다.
- 구조화 출력 설정(단위 I7·I9): `configs/model/model.json`의 `request.structured_output`(`off`·`json_object`), 기본 `json_object`, `config_version` `model-0.2`.
  - `json_object`면 도구를 주지 않는 조사자 초안 요청에만 `response_format` `{"type": "json_object"}`를 싣는다. 도구를 싣는 요청과 Critic 요청에는 싣지 않는다. 모든 모드에 같게 실리므로 모드 사이 공정성(룰북 B2)은 그대로다.
  - 3회차 실측 사실(2026-09-25(금), 오케스트레이터, X1 키 래퍼) `[사실: scratchpad/mt4/structured_probe_out.txt·live_r3_freeform_json.txt·live_r3_full_json.txt]`
    - 탐침(도구 이력 뒤 도구를 뺀 초안 요청): 초안 요청 메시지 없는 요청(2회차 모양), 메시지를 붙인 `off`, `json_object`, `tools`와 `tool_choice` `"none"`은 모두 HTTP 200·초안 파싱 성공이었다. 2회차 탐침에서는 같은 모양이 JSON이 아닌 글을 썼으므로, 온도 1.0에서 결과가 흔들린다.
    - `nvext.guided_json`은 HTTP 400(`PROVIDER_HTTP_4XX`)이었다. 이 모델·엔드포인트가 받지 않는다. 그래서 설정 값에서 뺐고, 스키마 함수도 지웠다.
    - 비교 불가 사례의 첫 차례 모양(역할 `system, user, user`)도 200·파싱 성공이었다. 사용자 메시지가 연달아 둘이어도 문제가 없다.
    - 스모크 `--structured json_object`: `freeform`은 `COMPLETED`(HOLD, 모델 요청 7, tokens_in 24,595, 최종 검증기는 기록만: `DATA_STATUS_CONFLICT`·`EVIDENCE_NOT_SUPPORTING`), `full`은 `COMPLETED`(HOLD, 모델 요청 5, tokens_in 13,402, 검증기 사유 없음). 두 모드 모두 모델 오류 0이었다.
  - 켠 까닭: 온도 1.0에서 JSON이 아닌 초안이 한 번 나왔고, `json_object`는 서버가 JSON 객체를 강제하며 두 모드 모두 통과했다.
  - 초안 형식 검사(단위 I10 `check_draft`)는 구조화 출력과 관계없이 그대로 돈다. 값을 바꾸면 요청 본문이 바뀌므로 `config_version`을 올린다.
- 파서는 느슨하게 하지 않았다: `</think>` 뒤만 읽거나 글 속 첫 JSON 객체를 뽑는 일은 룰북 B2 스키마 검사가 받는 범위를 바꾼다. 탐침(`scratchpad/mt4/structured_probe.py`의 `after_think_parses`)으로 먼저 잰 뒤, 필요하면 모든 모드에 같은 규칙으로 따로 정한다(선택지로만 둔다).
- 빈 대조 건너뛰기(단위 I12, MT2 평가 검토 2회차 권고 2): 초안에서 뽑은 `metric_id`와 근거 ID가 모두 0개면 `verify_evidence`를 부르지 않는다. 단위 I5는 그 호출을 `invalid_args`로 거부하면서 시도 1회를 쓰고, 최종 단계의 검증 몫은 1회뿐이다. 건너뛴 차례는 시도·몫을 쓰지 않고, 다음 `validator_result`에 `verify_skipped` 참을 남긴다. 기본·최종·`checklist` 차례 모두 같다. 도구 봉투의 `retryable_error`(예: `invalid_args`)는 도구 쪽 결과라 모델 제공자 원인 코드(`PROVIDER_*`)가 되지 않는다(시험 `RoundThreeTest`).
- 실측 `full`의 `VALIDATOR_BLOCKED` 원인(`EVIDENCE_UNRESOLVED` 2건, `EVIDENCE_NOT_SUPPORTING` 1건): 스모크 하네스의 근거 행 표가 대역 봉투의 근거 ID 4개 가운데 2개(`get_history`의 두 행)만 담았다. 분해 지표 `m-mix`의 근거 2개가 풀리지 않아 R3가 두 사유를 냈다. 모델·흐름 코드의 문제가 아니다 `[사실: 기록된 최종 초안과 봉투를 병합된 R1~R4에 다시 넣어, 행 2개로는 같은 사유, 근거 ID 전부로는 validator_ok 참을 확인]`. 하네스는 대역 봉투의 모든 근거 ID에 합성 행을 두도록 고쳤다(저장소 밖). 같은 실행에서 모델이 없는 `metric_id`(`m-comp`)를 한 번 지어냈고 틀 채우기(R1)가 `rejected_requests`로 버렸다(막는 사유 아님).

## 검토한 대안

- 허용 상태 조합을 초안 형식 문제로 두기(1회차): 기준선 `freeform`이 처리(검증기 차단)의 비용을 떠안아 버렸다(⑦).
- 정책 프록시 거부에 새 코드 이름(예: 샌드박스 정책 거부 전용 코드): 원인 분류 코드 이름 전체가 09:00 결정 대상이라 이름을 늘리지 않고 `CODE_ERROR`와 detail로 갈랐다(⑨).
- 비교 불가 사례의 수정 단계에 도구를 주고 도구 예산 I6에 맡기기: I6은 비교 가능 여부를 모르고, 아직 부르지 않은 인자(`get_history {}`)는 같은 인자 차단에도 걸리지 않는다. 흐름이 막는다(⑤).
- `comparable` 키가 없으면 비교 가능으로 보기(1회차): 봉투 모양이 달라지면 모든 모드에서 조기 종료가 조용히 꺼져 버렸다(⑤).
- `critic_used`를 Critic 답을 받은 뒤 참으로 두기(1회차): 요청을 보냈는데 멈춘 실행이 false로 남아 `revision_used`와 기준이 달랐다(④).
- `max_tokens` 1024(G4 확인값): 한국어 `freeform` 초안이 잘릴 위험이 있어 두지 않았다. 잘림을 형식 문제로 드러내는 것과 함께 2048을 쓴다(⑪).
- 지표의 근거 ID까지 빼는 조사자 보기(MT2 평가 검토의 예): `freeform` 주장과 자료 상태 주장이 지표별 근거 ID를 인용해야 하므로 버렸다. 근거 ID는 유지하고 계산 입력 원값과 중복만 뺐다(⑮).
- Critic도 조사자와 같은 보기: 분해를 쓴 경로가 한도에 닿아 Critic에는 근거 ID를 봉투마다 한 목록으로 모은 보기를 쓴다(⑮).
- 도구 이력이 있는 요청을 `tools` 없이 보내는 모양(NVIDIA 검토 권고 1): G4·X1이 확인하지 않은 모양이다. 실측 전이라 바꾸지 않았다. 확인이 실패하면 (i) 조사자 요청에 늘 같은 `tools`를 싣고 몫을 넘는 호출은 지금의 거부 경로로 막거나, (ii) 도구를 뺄 때 이전 도구 결과를 사용자 메시지 글로 옮긴다. 실측(⑯)에서 HTTP 200으로 받아들여졌고, `tools`를 빼도 도구 호출이 나올 수 있음이 드러났다. 모양은 유지하고 초안 요청 메시지를 더했다.
- 도구를 주지 않는 차례에 `tools`와 `tool_choice` `"none"`을 싣기: 도구 명세만큼 토큰이 늘고 이 모델에서 지켜지는지 모른다. 탐침의 측정용 변형으로만 둔다(⑯).
- 구조화 출력을 끈 채로 두기(3회차 처음 기본값): 실측에서 `json_object`가 두 모드 모두 통과했고 온도 1.0의 흔들림을 서버가 막아 주므로 켰다(⑯).
- `nvext.guided_json`(스키마로 디코딩 제한): 이 모델·엔드포인트가 HTTP 400으로 받지 않아 뺐다(⑯).
- 초안 파서가 `</think>` 뒤나 글 속 첫 JSON 객체를 읽기: 스키마 검사 범위가 바뀌어 실측 전에는 두지 않았다(⑯).

## 영향과 넘길 곳

- 사용자(09:00 안건): ①의 코드 이름, ②의 D12 입력, ③의 `tool_attempts` 뜻, ⑨의 코드 이름.
- 오케스트레이터: ⑯의 파서 선택지(`</think>` 섞임)를 정한다. ⑮의 남은 위험을 풀 방법을 정한다(한도는 공용 약속). 실측 스모크 1건과 NVIDIA 검토 권고 1의 탐침(도구 이력 뒤 `tools` 없는 요청, `finish_reason`)을 X1 키 래퍼로 돌린다. `docs/engineering-notes.md`의 `.env` 자동 로드 항목에 pymilvus와 `dotenv_values`(`PYTHON_DOTENV_DISABLED`를 보지 않는다) 예외를 더하는 일은 문서 작업이다. 로드맵 MVP 체크리스트 2번 증거 문구(③)와 단위 표 I13 행의 NAT 출력 이름(⑭)도 문서 후속이다.
- 조립 AS2: ⑬의 넘길 것과 맞출 것.
- MT5(CLI·샌드박스): 키 환경변수 이름을 샌드박스 종류로 고른다(⑩). 샌드박스 바깥 제한 시간은 사례 wall time 300초에 NAT 불러오기·프로파일 시간을 더한 값보다 길게 둔다. NAT 프로파일러 의존성(sdist 전용 패키지 셋 포함)을 이미지에 넣을지, 프로파일을 샌드박스 밖에서 만들지 정한다.
- 단위 E3(추출)·DT8(채점기): 재실행 대상은 `infra_rerun_eligible`로 가르고, 정책 프록시 거부는 detail의 `policy_denied`로 가린다(①·⑨).
