프롬프트·모델 설정(단위 I9, 소유 M, 로드맵 MT4). 키 값은 두지 않는다. 키가 든 환경변수의 이름만 `api_key_env`에 적는다.

- `model.json`: 모델 ID, 엔드포인트, 키 환경변수 이름, 요청 설정(temperature·top_p·max_tokens·추론 모드 `enable_thinking`, 모든 모드 같음), 5xx 명시 재전송(요청당 최대 3회, 지수 대기), 요청별 제한 시간 상한과 종료 기록 예약 시간, 사례당 한도(모델 요청 10회, 누적 토큰 32,000, wall time 300초, 도구 시도 8회와 단계별 몫, 수정 1회와 그 안의 재조회 2회). 수치는 모두 조정값이다. 소수는 Decimal로 읽는다.
  - 요청 설정: temperature 1.0·top_p 0.95·`enable_thinking` 끔은 구 개발계획 G4 관문 시험(`scripts/g4_nim_toolcall_probe.py`)에서 확인한 조합이다. `max_tokens` 2048은 G4 확인값(1024)과 다른 조정값이다. 한국어 `freeform` 초안(주장마다 12필드)이 1024를 넘을 수 있어 2048로 둔다. 응답이 잘리면(`finish_reason` `length`) 조사자 초안은 형식 실패로 수정 단계나 `INVALID`로 가고(단위 I10), trace `model_response`에 `finish_reason`이 남는다. 2048이 넉넉한지는 실측 스모크의 `finish_reason`으로 확인한다.
  - `structured_output`: NIM 구조화 출력. `json_object`(기본, `model-0.2`부터)·`off` 가운데 하나다. `json_object`면 도구 없는 조사자 초안 요청에만 `response_format` `{"type": "json_object"}`를 싣고(모든 모드 같음), 도구를 싣는 요청과 Critic 요청에는 싣지 않는다. 2026-09-25 실측에서 `json_object`는 HTTP 200·초안 파싱 성공이었고, `nvext.guided_json`은 이 모델·엔드포인트가 HTTP 400으로 받지 않아 설정 값에 두지 않는다. 값을 바꾸면 요청 본문이 바뀌므로 `config_version`을 올린다(결정 기록 ⑯).
- `config_version` `model-0.3`: 조사자·Critic 지침에 신호별 판정 규칙(판정 정책 P3과 같은 조건), 도구 인자와 재조회 인자 모양, 단가 신호의 분해·비교국 조회를 한 차례에 부르라는 지시를 더했다(AS2 2회차 실측 원인, 결정 기록 `docs/tracking/decisions/20260925-0605-model-decision-as2-run-case.md` ⑬). 요청 설정은 바꾸지 않았다.
- `investigator.txt`: 조사자 공통 지침(판정 뜻과 신호별 판정 규칙, 금지 문구, 도구 사용과 인자, 초안 JSON 형식). 금지 낱말 목록은 검증기(단위 R3)의 금지 문구 목록(한국어 62개, 영문 앞부분 9개)과 같아야 한다(시험 `tests/test_model_config.py`).
- `claims_template.txt` / `claims_freeform.txt`: 주장(claims) 쓰는 법. `freeform`만 값을 직접 쓰고, 나머지 모드는 metric_id·근거 ID로 가리킨다(코드가 검증된 지표로 채운다).
- `critic.txt`: Critic(별도 문맥의 검수자) 지침. 도구 없음, 구조화된 지적과 재조회 요청.

읽는 코드는 단위 I7(`src/tradesentry/workflow/model_client.py`의 `load_model_config`)이다. 샌드박스에서는 설치한 패키지가 저장소 배치를 모르므로, 부르는 쪽이 이 폴더 경로를 인자로 준다.
