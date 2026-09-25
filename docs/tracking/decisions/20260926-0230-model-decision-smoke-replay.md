# AS3 코드 PR: `tradesentry run-case --replay` — 키 없는 스모크 재현(기록된 모델 응답 재생)과 재생 픽스처 `eval/dev/smoke/`

사용자 결정 2026-09-26(토) 02:12 ②(`20260926-0212-user-decision-cli-options.md`)가 위임한 옵션 이름·재생 파일 형식·커밋 위치를 정한 기록이다. 판정 정책·검증기·채점기·보고서 필드·예산·`configs/model/`은 바꾸지 않았다.

용어

- 스모크 재현(smoke: 끝까지 도는지만 보는 가벼운 시험): 커밋된 합성 픽스처(`controlled_fixture_v0`, 정답을 알고 만든 가짜 자료)와 기록된 모델 응답으로 `run-case`가 키·네트워크 없이 끝까지 도는 것. 룰북 A2 `3c` 3점 앵커.
- 재생(단위 I8 `ReplayTransport`): 기록된 NIM 응답을 차례로 내주고, 보내려는 요청 본문의 `request_sha256`(정규화한 요청 본문의 해시)이 기록과 같은지 대조하는 전송 자리.

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-26(토) 02:30(기록 시각). 바탕은 `main` 69a765b |
| 제목 | `tradesentry run-case --replay <재생 파일 상대 경로>`와 재생 픽스처 `eval/dev/smoke/{case_id}.json` |
| 결정 | 아래 ①~⑦ |
| 결정 주체 | 소유 트랙(M). 오케스트레이터 지시(AS3e). 이름·형식·위치의 위임은 사용자 결정 0212 ② |
| 공용 약속 여부 | CLI 선택 옵션 하나(사용자 결정 0212로 승인. 자료 계약 §10.3에 같은 방식으로 문장을 더했다). 계획 경로 표에 없던 폴더 `eval/dev/smoke/`는 `[해석]`(eval/dev/ 아래 개발용 평가 자료 자리). 판정 정책·검증기·채점기·보고서 필드·예산·원인 분류 코드·`configs/`·trace와 실행 결과 기록의 모양은 바꾸지 않았다 |
| 관련 PR | 브랜치 `model/AS3-smoke-replay` |

## 까닭

- 자기채점 1회차 규범 G4(루트 `README.md` 없음)와 룰북 A2 `3c`의 3점 앵커 "README의 명령 하나로 키 없는 스모크 재현이 끝까지 돈다"에 CLI 쪽 수단이 없었다. 단위 I8 `ReplayTransport`는 시험에서만 썼다.
- 오케스트레이터가 현재 코드(model-1.7)로 A·C를 실제 NIM으로 돌린 실행 폴더(`run_case-260926021320` A MONITOR, `run_case-260926021540` C HOLD)가 있어 그 trace를 재생 픽스처로 쓸 수 있었다. B(`850431-XB-202412`)는 NVIDIA 쪽 오류로 시작 시점에 없었다.

## 결정 내용

① **옵션 이름(단위 F1 `src/tradesentry/cli/args.py`)** — `run-case`만 받는 선택 옵션 `--replay <REPLAY_PATH>`. `--run-name`·`--conditions-extra`처럼 옵션 역할 표 `COMMAND_OPTIONS` 밖에 둔다. 한 번만 적는다(`_Once`). 값은 `--conditions-extra`와 같은 모양 검사(`_is_relative_path_piece`: 비어 있지 않고, 공백·제어 문자가 없고, `/`·`\`·`~`·드라이브 문자로 시작하지 않는다)이며 오류 문장(`REPLAY_RULE`)은 값을 되풀이하지 않는다(N13). 다른 네 명령(`evaluate` 포함)은 받지 않는다(인자 오류 2). `Request`에 `replay`(없으면 `None`) 필드가 늘어 단위 F1 골든 `expected.json`에 `"replay": null`이 더해졌다. 상대 경로의 기준은 명령을 부른 작업 폴더(저장소 루트)다.

② **재생 파일 형식** — JSON 객체 `{"trace": [...], "requests": [], "source": {...}}`. `trace`는 원 실행 trace(단위 L1)의 `model_request`·`model_response`·`model_error` 레코드만 기록 순서대로(레코드 필드 `seq`·`ts`·`run_id`·`event`·`stage`·`data` 그대로. 도구 봉투는 넣지 않는다 — 도구 5개는 재생 때도 합성 픽스처로 실제로 돈다). `requests`는 단위 I8 골든 입력 `{"trace", "requests"}`와 모양을 맞추려 두되 비운다(CLI는 요청을 흐름이 만든다). `source`는 원 실행의 `run_id`, `case_id`, `snapshot_id`, `policy_version`, `mode`, `code_version`, `model_config`(run_start의 설정 버전), `execution_status`, `review_status_final`. 원 실행이 `COMPLETED`가 아니면 재생 파일을 만들지 않는다.

③ **커밋 위치와 이름** — `eval/dev/smoke/{case_id}.json`(합성 픽스처 A `850450-XA-202412`·B `850431-XB-202412`·C `850432-XC-202412`, 정책 `policy_v1`, 모드 `full`). 이 PR에는 A·C 둘을 넣었다. B는 오케스트레이터가 실행 폴더를 주면 같은 도구로 더한다(재생 시험은 폴더의 파일을 모두 돌리므로 파일만 더하면 된다).

④ **만드는 도구** — `scripts/make_smoke_replay.py <실행 폴더> <재생 파일 경로>`(`uv run --locked python scripts/make_smoke_replay.py outputs/run_case-{시각} eval/dev/smoke/{case_id}.json`). 만든 파일의 모든 문자열에 로컬 절대 경로 모양(단위 E1 `PATH_SHAPE`)·키 모양(`SECRET_SHAPE`)이 없어야 쓰고, 이미 있는 파일은 덮지 않는다(`xb`).

⑤ **배선(단위 F2 `src/tradesentry/cli/dispatch.py`)** — `load_replay`가 실행 폴더를 만들기 전에 파일을 읽고 검사한다: 파일 없음(예외 이름만)·JSON 아님·모양 틀림(`trace`가 모델 레코드 목록이 아님, `requests` 없음, `source` 없음)·빈 `trace`·`source`의 `case_id`·`snapshot_id`·`policy_version`·`mode`가 요청과 다름·`--mode checklist`(모델을 부르지 않으므로 재생할 것이 없다)는 종료 코드 1이고 `outputs/`에 아무것도 남기지 않는다. 통과하면 `investigate_case`가 전송 자리를 `ReplayTransport`로, 시계를 단위 I8 `ReplayClock`(가상 시계. 기록된 `elapsed_ms`와 재전송 대기만큼만 흐른다. trace 시각·보고서 시각·예산 시계에 같이 쓴다)으로 바꾼다. 그래서 429 뒤 대기(원 실행 A는 5·10·20초 등)가 실제로 잠들지 않고 실행이 결정적이다(trace 첫 시각 `2026-09-25T00:00:00+09:00`). 키는 읽지 않는다(`UrllibTransport`를 만들지 않는다). 요청 해시가 기록과 다르거나 기록이 모자라면 흐름 조정이 `ReplayMismatch`를 `CODE_ERROR`로 기록하고 1로 끝난다(단위 I8 규칙, 기존 동작). 재생이 기록을 다 쓰지 않고 끝나면(`transport.remaining` > 0) 출력 파일은 남기고 `REPLAY_LEFTOVER` 오류로 1이다(같은 실행이 아니다). 옵션이 없으면 전송 자리·시계·출력이 전과 같다(골든 불변). 호스트 백엔드(`evaluate`)는 재생을 넘기지 않는다.

⑥ **표시** — trace·실행 결과 기록에 재생 표시가 없어(`run_start`의 `api_key_env`뿐) 모양을 바꾸지 않고 표준 오류에 한 줄 `REPLAY_NOTICE`("알림: --replay로 기록된 모델 응답을 재생한 실행이다(NIM을 부르지 않았다). 점수표 근거가 아니다.")를 쓴다(스모크 묶음 알림과 같은 취지). 재생한 실행 결과 기록은 `run_id`·`code_version`·`wall_ms`만 원 실행과 다르고(A 92460 → 92354 ms, C 31320 → 31270 ms. 가상 시계는 전송 밖 처리 시간을 세지 않는다) 나머지 18개 키와 보고서(`report_id`·`run_id`·`created_at` 제외)가 같았다.

⑦ **시험** — 단위 F1 `ReplayTest` 2개(run-case만·한 번만·선택, 절대·홈·드라이브·공백·제어 문자 거부와 값 비반복), 단위 F2 `tests/units/F2/test_run_case_replay.py` 7개: 스모크(커밋된 재생 파일마다 키 환경변수를 지우고 `run_case_transport`를 부르면 실패하는 함수로 바꾼 채 끝까지 돌아 `execution_status`·`review_status_final`이 `source`와 같고 모델 레코드·해시 순서가 같음), A·B·C 기대 판정(oracle_ABC: MONITOR·MAINTAIN·HOLD), 재생 파일에 키·로컬 경로 모양 없음, 해시 불일치 → `CODE_ERROR`(detail에 `ReplayMismatch`)·1, 남은 기록 → 출력 뒤 1, 잘못된 파일 7종과 `agent`(mode 불일치)·`checklist` → 실행 폴더 없이 1, 옵션 없을 때 `run_case_transport`가 불림.

## 스모크 명령(README가 적을 것)

저장소 루트에서. 합성 픽스처는 저장소만으로 설치된다(`data/snapshots/controlled_fixture_v0/`의 커밋된 생성 규칙·manifest·빌드 기록에서 `materialize`가 SQLite를 만든다. 이 PR에서 새 작업 폴더로 확인: 새로 쓴 파일 3건, 단위 S3 검증 통과).

```
uv run --locked python -c "from tradesentry.snapshot import fixture; fixture.materialize()"
uv run --locked tradesentry run-case --snapshot controlled_fixture_v0 --policy policy_v1 --mode full --case 850450-XA-202412 --replay eval/dev/smoke/850450-XA-202412.json
```

## 남은 것

- B(`850431-XB-202412`) 재생 파일: 오케스트레이터가 실제 실행 폴더를 주면 ④의 도구로 더한다.
- 재생 파일은 지금 지침·모델 설정(`configs/model/`, model-1.7)이 만드는 요청 본문에 묶여 있다. 지침·요청 구성이 바뀌면 스모크 시험이 해시 불일치로 깨지고, 그때는 실제 NIM 실행으로 재생 파일을 다시 만든다.
- README(P1)는 별도 문서 PR이 쓴다.
