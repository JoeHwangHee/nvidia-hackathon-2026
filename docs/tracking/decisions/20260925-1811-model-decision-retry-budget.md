# AS3 코드 PR: 재전송을 모델 요청 한도에서 뺌(사용자 결정 1805의 코드 쪽)

2026-09-25(금) 18:05 사용자 결정(`20260925-1805-user-decision-retry-budget.md`)을 코드·설정·시험에 옮긴 기록이다. 명세는 그 기록의 결정 ①~③이고, 여기서는 코드에서 정한 세부만 적는다.

용어

- 재전송: 한 실행 안에서 HTTP 5xx(서버 오류)·429(호출 한도 초과)를 받은 같은 요청을 다시 보내는 것(단위 I7, 요청당 최대 3회).
- 모델 요청 수(`model_requests`): 사례 1건이 NIM(NVIDIA 클라우드 추론 API)에 보낸 요청의 수. 이 기록부터 요청 하나의 첫 전송만 센다.
- 시도(`attempt`): 요청 하나 안의 HTTP 전송 차례(첫 전송 1, 재전송 2~4). trace(실행 추적 기록)의 `model_request`·`model_error`·`model_response`에 남는다.

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 18:11(기록 시각). 바탕은 `main` 690f3eb |
| 제목 | 모델 요청 수는 첫 전송만 세고, 재전송 전에는 모델 요청 한도를 보지 않음(모델 설정 `model-1.5`) |
| 결정 | 아래 ①~④ |
| 결정 주체 | 규칙은 사용자(결정 1805). 코드의 세부(세는 자리, trace 값의 뜻)는 소유 트랙(M) |
| 공용 약속 여부 | 규칙 자체는 공용 약속이고 사용자 결정 1805가 승인이다. 원인 분류 코드 11개, 오류 항목 키, 실행 결과 기록 키, 도구·모델 예산 값은 바꾸지 않았다. 계획 문서(자료 계약·룰북·개발 플랜·평가 스킬)는 문서 PR(DOCS5)이 고친다 |
| 관련 PR | 브랜치 `model/AS3-retry-budget` |

## 까닭

- 사용자 결정 1805 배경: V1(MVP 시험) dev20 묶음에서 끝까지 돌지 못한 실행 가운데 8건이 `BUDGET_MODEL_REQUESTS`("HTTP 429 재전송 전에 모델 요청 한도에 닿았다")였다. 재전송도 10회에 세는 규칙 때문에 제공자 쪽 오류가 `BUDGET_EXCEEDED`로 바뀌었고, 이 상태는 인프라 실패 재실행 대상이 아니다 `[사실: 결정 1805 기록]`.

## 결정 내용

① **단위 I7(`src/tradesentry/workflow/model_client.py`)**
- `budget.model_requests`는 요청 하나의 첫 전송(`attempt` 1)에서만 늘린다. 같은 요청의 재전송(5xx·429)은 늘리지 않는다. 첫 전송이 전송 자리의 설정 오류(`TransportConfigError`)로 나가지 못하면 지금처럼 되돌린다(재전송 차례에서 나면 되돌리지 않는다. 첫 전송은 이미 셌다).
- 한도 확인(`_precheck`)은 새 요청을 보내기 전에는 그대로 deadline → 모델 요청 10회 → 누적 토큰 순이다. 재전송 차례(`new_request` 거짓)에는 모델 요청 한도를 보지 않고 deadline과 누적 토큰만 본다(누적 토큰은 재전송 사이에 늘지 않으므로 실제로는 deadline만 걸린다).
- 재전송 대기 전의 "모델 요청 한도에 닿았다"(`BUDGET_MODEL_REQUESTS`) 검사를 지웠다. 재전송은 요청당 3회(`retry.max_5xx_retries`)와 사례 deadline으로만 묶인다. 대기가 deadline을 넘으면 지금처럼 `DEADLINE`, 3회를 다 쓰면 원래 원인 코드(`PROVIDER_HTTP_5XX` 또는 `PROVIDER_HTTP_4XX`, detail "HTTP {상태}(재전송 N회 뒤)", 재실행 대상)다.
- trace `model_request`의 `model_requests`는 그 시점까지의 모델 요청 수(재전송 뺌)라 한 요청의 시도들이 같은 값을 적는다. `attempt`는 HTTP 전송 차례 그대로(1~4), `request_no`는 요청 번호 그대로다. NAT(NVIDIA 에이전트 추적·평가 도구 모음) 감싸기(단위 I13)의 LLM 구간은 지금처럼 HTTP 시도마다 하나라, 재전송이 있으면 LLM 구간 수가 `model_requests`보다 많다(코드 변경 없음).

② **실행 결과 기록 `model_requests`** — 흐름 조정(단위 I12)이 `budget.model_requests`를 그대로 옮기므로 코드 변경 없이 재전송을 뺀 수가 된다. 오류 항목 `attempts.model_requests`도 같다.

③ **모델 설정 `model-1.5`(`configs/model/model.json`)** — `config_version`만 올렸다. 설정 값과 지침 글은 그대로다. 요청 본문은 한 곳만 달라진다: 흐름 조정(단위 I12)이 조사자 요청에 싣는 "[남은 횟수] … 모델 요청 N회"(N = 한도 − 모델 요청 수)가 재전송한 요청 뒤에는 재전송 수만큼 커진다. 재전송이 없는 실행과 기록 재생(단위 I8) 골든(요청 하나)의 요청 해시는 바뀌지 않는다. `configs/model/README.md`에 한 줄을 더했다. 단위 L3 머리 주석의 `BUDGET_MODEL_REQUESTS` 행("재전송 포함")을 "재전송은 세지 않고 새 요청을 보내기 전에만 본다"로 고쳤다(코드 변경 없음).

④ **단위 E1·E3** — 재실행 대상 판정은 단위 L3 `infra_rerun_eligible` 하나로 하므로 코드 변경이 없다. 재전송으로 `BUDGET_EXCEEDED`가 되던 실행은 이제 `PROVIDER_HTTP_5XX`·429 `PROVIDER_HTTP_4XX`(`FAILED`)로 끝나 묶음 끝 재실행 대상이 된다.

## 시험

- I7: 재전송이 모델 요청 수를 늘리지 않음(5xx 3회·429 3회·섞임·성공), 10번째 요청이 재전송 3회를 다 써도 `BUDGET_EXCEEDED`가 아니라 원래 코드·재실행 대상이고 trace의 네 시도가 모두 `model_requests` 10, 재전송이 섞인 요청 뒤 새 요청은 한도에서 보내지 않고 `BUDGET_MODEL_REQUESTS`, 429 재전송 대기의 deadline. 골든 기대값 `budget.model_requests`를 3에서 1로 고쳤다(503 두 번 뒤 200인 요청 하나).
- I12: 5xx 재전송 한도를 다 쓴 Critic 요청의 오류 항목 `attempts.model_requests`를 5에서 2로 고쳤다(초안 1 + Critic 1, 재전송 3회 뺌).
- I12: 503 뒤 재전송한 초안이 있는 `full` 실행의 `model_requests`가 3(요청 4번 전송)이고 수정 지시가 "모델 요청 8회"를 알린다(새 시험).
- 모델 설정: `config_version` `model-1.5`.
- I8 골든(기록 재생)의 입력 trace는 옛 규칙으로 적힌 기록(재전송 시도의 `model_requests` 2)이고 재생은 그 값을 읽지 않는다. 요청 해시와 기대값은 그대로다.

## 남은 것

- 이 변경 전에 기록한 trace 가운데 재전송이 든 것은, 재전송 뒤 요청의 본문("모델 요청 N회")이 달라 기록 재생에서 뒤 요청의 해시가 맞지 않을 수 있다. 새로 기록한 trace는 영향 없다.
- 계획 문서의 한도 문단·`model_requests` 뜻은 문서 PR(DOCS5)이 고친다. 이 기록의 색인 줄과 DOCS5의 1805 색인 줄이 같은 자리에 더해져 병합 때 겹칠 수 있다(두 줄 모두 남기면 된다).
- `20260925-1605-model-decision-429-retry.md` ①의 "재전송 전에 모델 요청 10회에 닿으면 `BUDGET_MODEL_REQUESTS`"는 이 기록이 대체한다.
- 병합 뒤 샌드박스를 다시 굽고 V1 두 묶음을 다시 돌린다(결정 1805 영향).
