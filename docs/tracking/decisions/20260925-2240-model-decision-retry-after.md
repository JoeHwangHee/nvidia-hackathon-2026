# AS3 코드 PR: Retry-After 존중과 응답 헤더·본문 요지 기록(사용자 결정 2225 ④의 코드 쪽)

2026-09-25(금) 22:22 사용자 결정(`20260925-2225-user-decision-code-boundaries.md`, 문서 PR `docs/DOCS8-code-boundaries`가 넣는다) 가운데 요청 쪽 경계 ④(Retry-After 존중과 헤더 기록)를 코드·설정·시험에 옮긴 기록이다. 명세는 그 기록의 결정 ④·⑤이고, 여기서는 코드에서 정한 세부만 적는다.

용어

- `Retry-After`: 다시 시도할 때까지 기다릴 시간을 알려 주는 HTTP 응답 헤더. 값은 초 정수(delay-seconds) 또는 HTTP-date(예: `Fri, 25 Sep 2026 13:30:00 GMT`)다.
- 재전송: 한 실행 안에서 HTTP 5xx(서버 오류)·429(호출 한도 초과)를 받은 같은 요청을 다시 보내는 것(단위 I7, 요청당 최대 3회, 지수 대기 5·10·20초).
- trace(실행 추적 기록) `model_error`: NIM(NVIDIA 클라우드 추론 API) HTTP 시도 하나가 오류로 끝났을 때 남기는 사건(단위 L1 형식).

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 22:40(기록 시각). 바탕은 `main` 3f1832a |
| 제목 | 재전송 대기 = max(지수 대기, min(`Retry-After`, 60초)), trace `model_error`에 `retry_after_ms`·허용 목록 헤더·가린 본문 요지(모델 설정 `model-1.7`) |
| 결정 | 아래 ①~⑤ |
| 결정 주체 | 규칙은 사용자(결정 2225 ④). 코드의 세부(헤더 허용 목록의 모양, HTTP-date 기준 시각, trace 값의 뜻, 재생의 옛 기록 처리)는 소유 트랙(M) |
| 공용 약속 여부 | 규칙 자체는 공용 약속(평가 구성: 재시도 규칙)이고 사용자 결정 2225가 승인이다. 재전송 횟수(3회)·지수 대기 값·요청별 제한 시간(60초)·한도(`limits`)·속도 조절(`pacing`)·원인 분류 코드 11개·실행 결과 기록 키는 바꾸지 않았다. 계획 문서(개발 플랜 §6·§7의 재전송 서술, 룰북)는 문서 PR(DOCS8)이 고친다 |
| 관련 PR | 브랜치 `model/AS3-retry-after` |

## 까닭

- 사용자 결정 2225 배경 ②: V1(MVP 시험) 3차의 실패·무효 9건 가운데 429·500 재전송 소진이 3건(dev20)이었다. 사용자는 요청 제한 시간 연장(60→120초)과 재전송 4회는 고르지 않고 "Retry-After 존중 + 헤더 기록"을 골랐다 `[사실: 결정 2225 기록]`.
- 2026-09-25 15:52 실측(결정 1552 배경 ②)에서는 429·503 응답에 `x-ratelimit-*`·`retry-after`가 없었다. 그래서 헤더가 없을 때는 지금 규칙(지수 대기) 그대로여야 하고, 헤더가 오면 그 값을 존중하되 상한(60초)으로 사례 시간(300초)을 지키게 한다.

## 결정 내용

① **응답 헤더·본문 요지 수집(단위 I7 `UrllibTransport.send`)**
- HTTP 응답을 받은 전송 결과(성공 200과 `HTTPError` 경로의 3xx·4xx·5xx)에 `headers`(dict)를 더 싣는다. 허용 목록 `RESPONSE_HEADER_ALLOWLIST`(`retry-after`, `x-ratelimit-limit-requests`, `x-ratelimit-remaining-requests`, `x-ratelimit-reset-requests`, `x-ratelimit-limit-tokens`, `x-ratelimit-remaining-tokens`, `x-ratelimit-reset-tokens`, `x-request-id`)의 헤더만 소문자 이름으로 모으고 그 밖의 헤더는 싣지 않는다. 같은 이름이 여럿이면 `", "`로 잇는다. 헤더 값에도 비밀값 가림(아래)을 적용하고 앞 200자만 둔다 `[해석: 소유 트랙. 헤더 값에 키 모양이 실릴 일은 없지만 겹 보호다]`.
- 오류 응답(400~599)에는 `body_excerpt`를 더 싣는다: 본문을 UTF-8로 풀고(못 푸는 바이트는 대체 문자 U+FFFD), NVIDIA 키 접두어(단위 I7 `KEY_PREFIX`. 글자 그대로는 적지 않는다)로 시작하는 문자열을 `KEY_PREFIX + "***"`(`SECRET_MASK`)로 가린 뒤 앞 200자다. 가린 뒤 자르므로 잘린 자리에 키 조각이 남지 않는다. 빈 본문은 `None`이다. 원본 `body`(bytes)는 그대로 둔다(200 응답 파싱 자리와 같다).
- 정책 프록시 거부(`policy_denied`)·연결 실패·timeout 결과의 모양은 바꾸지 않는다(`headers`·`body_excerpt` 키가 없다). 부르는 쪽은 `headers`가 없거나 dict가 아니면 {}로 다룬다.

② **Retry-After 존중(단위 I7 `ModelClient.chat` 재전송 고리)**
- 429·5xx 응답의 `headers["retry-after"]`를 `parse_retry_after`로 ms로 푼다. 초 정수(0 이상, 자릿수 9 이하)는 ×1000. HTTP-date는 `email.utils.parsedate_to_datetime`으로 읽어 전송 시각 기준 남은 초이고 음수면 0이다 `[해석: 결정 2225 ④]`. 시간대가 없는 날짜는 GMT로 본다(HTTP-date 규약). 그 밖(빈 값, 음수, 소수, 글자)은 `None`이다.
- 전송 시각은 `ModelClient`의 `wall_s`(기본 `time.time`, epoch 초)를 `transport.send` 직전에 읽은 값이다. 시험은 고정 값을 준다. 기존 `clock_ms`(단조 밀리초)·`sleep_ms`는 그대로다.
- 대기 = max(지수 대기 `backoff_base_ms × backoff_factor^회차`, min(`retry_after_ms`, `retry.retry_after_cap_ms` 60000)). `retry_after_ms`가 `None`이면 지수 대기 그대로다. 대기가 남은 사례 시간(deadline − 종료 기록 예약)을 넘으면 지금처럼 `DEADLINE`으로 멈추고 대기하지 않는다. 재전송 횟수(요청당 3회, 5xx·429 합산)와 한도 세기(첫 전송만 `model_requests`에 셈, 결정 1805)는 그대로다.
- 다른 4xx(400·401·403·404·422 등)·정책 거부·연결 실패·timeout은 지금처럼 재전송하지 않고, 그 `model_error`의 모양도 바꾸지 않는다.

③ **trace `model_error`(429·5xx, 재전송 여부와 무관)** — 기존 키(`request_no`·`attempt`·`http_status`·`error`·`elapsed_ms`·`retrying`·`backoff_ms`)에 세 키를 더한다: `retry_after_ms`(푼 값, 상한 적용 전. 없거나 못 풀면 null), `headers`(허용 목록만, 없으면 {}), `body_excerpt`(없으면 null). `backoff_ms`는 실제 대기(상한 적용 뒤)다. 다른 사건(`model_request`·`model_response`, 다른 4xx·연결·timeout·정책 거부의 `model_error`)의 모양은 그대로다. 단위 I13(NAT 감싸기)의 LLM 구간 끝 값은 바꾸지 않았다(`http_status`·`error`·`denial`·`retrying`).

④ **모델 설정 `model-1.7`(`configs/model/model.json`)** — `retry.retry_after_cap_ms: 60000`(조정값)을 더하고 `config_version`을 올렸다. `ModelConfig` 파싱은 기존 `retry` 키들과 같게 필수 키·0 이상 정수다(없거나 틀리면 `ConfigError`). 지침 글과 요청 본문은 바뀌지 않아 요청 해시(골든)는 그대로다. `configs/model/README.md`에 한 줄, 단위 I7 머리 주석에 재전송 서술을 더했다.

⑤ **단위 I8 기록 재생(`ReplayTransport`)** — `model_error` 기록에 `headers`(dict)가 있으면 그대로, 없으면(model-1.7 전 기록) {}를 돌려준다. `model_response` 기록에는 헤더를 남기지 않으므로 성공 응답의 재생 `headers`는 {}다. `body_excerpt`는 재생 결과에 싣지 않는다(재생은 trace 기록에서 다시 만든다). 골든(I7·I8·I10·I11·I12)은 바뀌지 않았다.

## 시험

- I7 `RetryAfterTest`(가짜 전송 `HeaderTransport`, 고정 전송 시각): 초 값이 지수 대기보다 큼(8초 → 8초)/작음(2초 → 10초), HTTP-date 미래(30초)·과거(0 → 지수 대기), 없음(헤더 키 없음·{}·다른 헤더만)·깨진 값(`soon`·`-3`·`1.5`)은 지수 대기와 `retry_after_ms` null, 상한(120초 → 대기 60초, trace는 120000), deadline 넘을 때 `DEADLINE`·대기 없음·`retrying` false, 5xx도 같은 규칙과 재전송 3회 그대로(마지막 오류에도 세 필드), trace 세 필드와 다른 사건의 모양 불변(400의 `model_error`에는 세 필드 없음), `parse_retry_after` 단위 사례, 실제 전송 자리의 허용 목록 수집·허용 목록 밖 헤더 제외(`Content-Type`·`Set-Cookie`·`Authorization`)·본문 가림(키 접두어 + `abc` → `SECRET_MASK`)·200자 자름·빈 본문 null·깨진 UTF-8 대체 문자, 성공 응답의 `headers`와 timeout·연결·터널 거부·L7 거부 결과의 모양 불변, 헤더 값 가림과 같은 이름 잇기, `retry_after_cap_ms` 필수·0 이상 정수.
- I8: `headers` 없는 옛 기록은 {}, 있는 기록은 그대로, 성공 기록은 {}.
- 모델 설정 시험: `config_version` `model-1.7`, `retry` 네 값.
- 전체 시험 `Ran 1452: OK (skipped=6)`. 건너뛴 6개는 뼈대 단위(A1·A2·E2·G2)와 진입 함수 없는 단위(K1·S1)로 이 PR과 무관하다. 골든 I7·I8·I10·I11·I12 skipped 0.

## 남은 것

- 계획 문서의 재전송 서술(개발 플랜 §6·§7, 룰북 B2)과 사용자 결정 2225 기록·색인 줄은 문서 PR(DOCS8)이 넣는다. 이 기록의 색인 줄과 DOCS8의 색인 줄이 같은 자리에 더해져 병합 때 겹칠 수 있다(두 줄 모두 남기면 된다).
- 2026-09-25 15:52 실측에서는 NIM 429·503 응답에 `Retry-After`·`x-ratelimit-*`가 없었다. 헤더가 계속 없으면 이 변경은 대기를 바꾸지 않고 기록만 더한다. V1 4차 trace의 `headers`로 실제 헤더 유무를 확인한다.
- 기록 재생에서 `headers`가 든 기록을 재생하면 재생 실행의 대기(가상 시계)가 Retry-After 규칙으로 다시 계산돼, 옛 규칙으로 기록한 `wall_ms`와 다를 수 있다. 재생은 응답·판정을 그대로 재현하므로 골든에는 영향이 없다.
- 병합 뒤 샌드박스를 다시 굽고 V1 4차(dev20·`real_dev`)를 돌린다(결정 2225 ⑥).
