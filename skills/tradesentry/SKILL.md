---
name: tradesentry
description: TradeSentry 런타임 스킬. 운영자가 관세청 수입통계 경보 목록을 보거나 경보 사례 1건을 조사해 달라고 하면, OpenShell 샌드박스 안 TradeSentry CLI의 `detect`(경보 목록)나 `run-case`(사례 1건 조사)만 한 번 실행하고, CLI가 낸 표준 출력·보고서·종료 코드를 고치지 않고 그대로 전한다. 부정·위법·원산지 판정이나 통관 조치가 아니다. Use this skill when the operator asks for TradeSentry alerts or a case investigation; it runs only `tradesentry detect` or `tradesentry run-case` inside the sandbox and relays the CLI output verbatim.
---

# TradeSentry 런타임 스킬 (`tradesentry`)

NemoClaw(OpenShell 위에서 에이전트를 돌리는 NVIDIA 참조 스택)의 OpenClaw 에이전트가 부르는 스킬이다. 실행 사슬은 운영자 요청 → OpenClaw 에이전트 → 이 스킬 → OpenShell(에이전트를 격리해 돌리는 샌드박스 런타임) 샌드박스 안 TradeSentry CLI(명령줄 실행 도구)다. CLI 안에서 Nemotron(NVIDIA 언어 모델) 조사자와 검수자(Critic)가 정해진 조회 도구 5개로 경보를 반증해 보고, 담당자의 다음 업무를 검토 유지(`MAINTAIN`)·모니터링(`MONITOR`)·자료 보류(`HOLD`) 가운데 하나로 제안한다. 그 결과는 부정·위법·원산지 판정이나 실제 통관 조치가 아니다.

이 스킬은 시연 경로 전용이다. 정확도 지표를 내는 채점 대상 실행(평가 스킬 ② `tradesentry-eval`이 샌드박스 밖 채점과 함께 다룬다)에는 쓰지 않는다. 인터페이스 계약의 정본은 `docs/plan/DEV_PLAN.md` §5.2다.

## 언제 쓰나

- 운영자가 경보 목록을 보여 달라고 할 때: `detect`
- 운영자가 경보 사례 1건을 조사해 달라고 할 때: `run-case`
- 그 밖의 요청(스냅샷 만들기·검증, 평가·채점, 정답 확인, 설정 변경)에는 쓰지 않는다. 할 수 없는 일이라고 답한다.

## 할 일

1. 요청에서 값 네 가지만 정한다. 운영자가 주지 않은 값은 아래 기본값을 쓰고, 기본값을 썼다고 함께 알린다.

   | 값 | 옵션 | 형식 | 기본값 |
   |---|---|---|---|
   | 스냅샷 ID(한 시점에 수집해 고정한 자료 묶음의 이름) | `--snapshot` | 영문 소문자로 시작, 영문 소문자·숫자·밑줄만(예: `controlled_fixture_v0`, `kcs_202201_202412_v2`) | `controlled_fixture_v0` |
   | 정책 버전 이름(판정 기준값 묶음의 버전. 파일 경로가 아니다) | `--policy` | 예: `policy_v1`, `dev-0.1` | `dev-0.1` |
   | 모드(실행 방식) | `--mode` | `checklist`, `agent`, `full`, `freeform` 가운데 하나. `run-case`만 쓴다 | `full` |
   | 사례(조사할 경보 1건) | `--case` | 영문자·숫자로 시작하고 끝나며 그 사이에 영문자·숫자·밑줄·하이픈만(예: `A-composition`, `850450-CN-202401`). `run-case`만 쓴다 | 없음. 운영자에게 묻는다 |

   값에 경로 구분자(`/`), `..`, `~`, 공백, 따옴표, 셸 기호(`;`, `|`, `&`, `$`, `` ` ``, `>`, `<`)가 들어 있으면 명령을 만들지 않고 운영자에게 다시 묻는다. CLI도 이런 값을 거부한다(종료 코드 2).

2. 셸 도구로 아래 두 명령 가운데 하나만 실행한다. 꺾쇠 자리에만 1단계의 값을 넣고, 다른 옵션·파일 경로·URL·SQL·셸 조각을 붙이지 않는다. 작업 폴더는 반드시 `/sandbox`다. CLI는 현재 폴더 아래 `outputs/{실행명}/`에 결과를 쓴다.

   ```bash
   cd /sandbox && /sandbox/tradesentry/bin/tradesentry detect --snapshot <스냅샷 ID> --policy <정책 버전 이름>
   ```

   ```bash
   cd /sandbox && /sandbox/tradesentry/bin/tradesentry run-case --snapshot <스냅샷 ID> --policy <정책 버전 이름> --mode <모드> --case <사례>
   ```

3. 명령의 종료 코드, 표준 출력 전부, 표준 오류 전부를 그대로 전한다. 표준 출력의 각 줄은 CLI가 쓴 결과 파일의 위치(`outputs/{실행명}/{도메인명}-{시각}.{확장자}`)다.
4. `run-case`가 종료 코드 0으로 끝났으면, 표준 출력에 적힌 파일 가운데 보고서(`.md`)와 실행 결과 기록(`.json`)만 `cat /sandbox/<표준 출력에 적힌 그 경로>`로 읽어 내용을 그대로 붙인다. 표준 출력에 없는 파일은 열지 않는다.
5. 전할 때 지킬 것
   - `case_id`, `review_status_final`(최종 검토 상태), `signal_status`(신호 상태), `unresolved_evidence`(풀리지 않은 근거), `execution_status`(실행 상태), 보고서 본문, 실행 폴더 위치를 CLI가 쓴 글자 그대로 옮긴다. 숫자를 반올림하거나 다시 계산하거나 요약하면서 바꾸지 않는다.
   - 보고서를 고쳐 쓰거나 새 결론을 덧붙이지 않는다. 설명이 필요하면 보고서 밖에 "스킬 설명"이라고 밝혀 한두 문장만 덧붙이고, 보고서의 판정과 다른 말을 하지 않는다.
   - 실행 폴더 위치는 샌드박스 안 `/sandbox/outputs/{실행명}/`이라고 적는다. 샌드박스 밖 `outputs/{실행명}/`으로는 샌드박스 밖 프로그램이 내려받는다(이 스킬이 하지 않는다).
6. 종료 코드가 0이 아니면 그 코드와 표준 오류를 그대로 전하고 멈춘다. 다른 명령으로 바꿔 다시 하거나 옵션을 바꿔 여러 번 부르지 않는다. 운영자가 값을 고쳐 다시 요청하면 그때 한 번 더 부른다.

   | 종료 코드 | 뜻(CLI 정의) |
   |---|---|
   | 0 | 끝남 |
   | 1 | 실패(처리 중 알린 실패나 예상 밖 예외) |
   | 2 | 인자 오류(값 형식이 틀림) |
   | 3 | 그 명령이 아직 연결되지 않음 |
   | 4 | 배선 계약 위반(조립체 출력이 기대한 형식이 아님 등) |
   | 130 | 중단됨 |

7. 요청마다 스킬이 CLI를 실제로 불렀는지(불렀으면 명령 이름)와, `run-case`면 그 실행의 `execution_status`를 답 끝에 한 줄로 남긴다. 스킬 호출 성공률(시연 요청 가운데 스킬이 CLI 실행까지 이어진 비율, `docs/plan/ROADMAP.md` §3 체크리스트 1번)을 세는 근거다.

## 하지 않는 것

- `snapshot-build`, `snapshot-verify`, `evaluate`를 부르지 않는다(자료 구축은 데이터 트랙, 평가는 평가 스킬 ②의 일이다).
- `curl`·`wget`·파이썬 한 줄 등 다른 프로그램으로 외부에 요청하지 않는다. NVIDIA 추론 요청은 CLI만 한다.
- `.env` 파일, 환경변수 목록, 자격 증명 파일, 하네스 설정 폴더를 읽거나 출력하지 않는다. API 키 값을 다루지 않고, 키는 변수 이름으로만 말한다.
- 정답표(평가용 기대 판정 표), 봉인 자료(개발 중 보지 않도록 저장소 밖에 둔 평가 자료), 채점기 출력을 찾거나 읽지 않는다. 봉인 자료로 실행하거나 정답 대조 채점을 하지 않는다.
- 보고서와 CLI 출력의 숫자·상태값을 바꾸지 않는다.

## 용어

- **경보**: kg당 단가나 상대국 점유율이 전년 같은 달보다 크게 바뀐 품목·상대국·달.
- **실행명**: `{실행 이름}-{yymmddhhmmss}`(예: `run_case-260925143015`). 실행 폴더 `outputs/{실행명}/`의 이름이다.
- **모드 4개**: `checklist`(고정 체크리스트. 모델을 쓰지 않는다), `agent`(Critic 없는 Nemotron), `full`(전체 TradeSentry: 조사자 + Critic + 수정 1회 + 검증기 차단), `freeform`(대표 지표의 기준선. 값을 모델이 직접 쓰고 검증기는 기록만 한다). 뜻의 정본은 `docs/rules/DATA_CONTRACT_V1.md` §4.1이다.
