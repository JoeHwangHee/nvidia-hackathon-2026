프롬프트·모델 설정(단위 I9, 소유 M, 로드맵 MT4). 키 값은 두지 않는다. 키가 든 환경변수의 이름만 `api_key_env`에 적는다.

- `model.json`: 모델 ID, 엔드포인트, 키 환경변수 이름, 요청 설정(temperature·top_p·max_tokens·추론 모드 `enable_thinking`, 모든 모드 같음), 5xx 명시 재전송(요청당 최대 3회, 지수 대기), 요청별 제한 시간 상한과 종료 기록 예약 시간, 사례당 한도(모델 요청 10회, 누적 토큰 32,000, wall time 300초, 도구 시도 8회와 단계별 몫, 수정 1회와 그 안의 재조회 2회). 수치는 모두 조정값이다. 소수는 Decimal로 읽는다.
- `investigator.txt`: 조사자 공통 지침(판정 뜻, 금지 문구, 도구 사용, 초안 JSON 형식).
- `claims_template.txt` / `claims_freeform.txt`: 주장(claims) 쓰는 법. `freeform`만 값을 직접 쓰고, 나머지 모드는 metric_id·근거 ID로 가리킨다(코드가 검증된 지표로 채운다).
- `critic.txt`: Critic(별도 문맥의 검수자) 지침. 도구 없음, 구조화된 지적과 재조회 요청.

읽는 코드는 단위 I7(`src/tradesentry/workflow/model_client.py`의 `load_model_config`)이다. 샌드박스에서는 설치한 패키지가 저장소 배치를 모르므로, 부르는 쪽이 이 폴더 경로를 인자로 준다.
