# 현재 위치

2026-09-24(목) 기준이다. 2026-09-25(금) 사용자 결정(아래 "된 것"의 마지막 항목)만 더했다.

## 된 것

- **계획 문서 11종**: 개발 플랜, 로드맵, 앱 뼈대 자문 명세서, 공용 자료 계약, 병렬 개발 규칙, 에이전트 운용 규칙, 평가 룰북, 스킬(Agent Skills 형식의 에이전트용 작업 절차) 사전, 평가 스킬 두 개, 계획 문서 색인이 PR(GitHub 변경 요청) #2~#12로 `main`에 병합됐다. 문서마다 작업 성격별 도메인 검토를 거쳤고(색인은 기계 검사만), 고위험 4종(개발 플랜·자료 계약·룰북·평가 스킬 ②)은 Codex(OpenAI의 코딩 에이전트 CLI) 교차 검토도 받았다. 병합 뒤 전체 최종 검토에서 나온 문서 간 어긋남은 PR #14에서 맞췄다.
- **수집기와 시험**: `src/tradesentry/ingest.py`와 `tests/test_ingest.py`의 시험 17개가 네트워크·키 없이 통과한다(2026-09-24(목) `python3 -m unittest discover -s tests` 종료 코드 0).
- **자료**: 스냅샷 `kcs_202201_202412_v2`의 수집과 검사 기록(`data-readiness.json`, `snapshot_hash.json`)이 있다. 상태 표시는 아직 `COLLECTED_NOT_FROZEN`이다. 동결 표시는 데이터 트랙이 결정 기록과 함께 바꾸고(`docs/rules/PARALLEL_DEV_RULES.md` §10.1), 최종 스냅샷 빌드의 동결은 로드맵 DT7에서 한다.
- **사용자 승인**(2026-09-24(목)): 결정 기록은 `docs/tracking/decisions/`의 `20260924-1504-user-approval-contract-design.md`와 `20260924-1504-user-approval-x1-exception.md`다.
  - 자료 계약 v1(`docs/rules/DATA_CONTRACT_V1.md`)의 `[DESIGN]`(팀 설계 규칙) 항목. `g0`(비교국 고정 목록) 해석, `policy_v1`(동결 판정 정책) 승인 때 확인할 로드맵 §6.3의 항목 전체(수치, 빈 응답 달을 무거래 확정 `CONFIRMED_NO_TRADE`로 바꾸는 승격과 그 달의 0 처리, 수입 0이 명시된 달의 처리, 허용오차), 룰북 부록 항목은 이 승인에 들지 않는다.
  - X1(구현 첫날의 세로형 최소 통합 시험) 대체 경로 규칙의 두 예외: 키 주입(샌드박스 안에 API 키를 두지 않고 추론 요청에 키를 붙이는 일) 두 방식(credential placeholder rewrite, 곧 샌드박스 안 감독 프로세스(root로 돌며 정책을 집행하는 OpenShell 프로세스)의 정책 프록시가 게이트웨이(정책·provider 설정을 보관하고 내려보내는 OpenShell 제어면)에서 받은 자격 증명으로 자리표시 문자열을 실제 키로 바꾸는 방식과, 샌드박스가 보는 추론 주소 `inference.local`)이 모두 실패하거나, 기본 블록(NemoClaw 기본 정책에 딸려 올 수 있는 네트워크 허용 블록. 예: `clawhub`·`npm_registry`)을 빼거나 좁힌 정책으로도 시연 샌드박스(시연용으로 따로 두는 샌드박스)가 요건 (b)를 채우지 못하면 Brev(NVIDIA 원클릭 클라우드 개발 환경)로 옮기지 않고 바로 사용자 결정을 받는다. 요건 (b)는 외부 전송을 NVIDIA 추론 엔드포인트로만 허용하고 L7(HTTP 요청 수준) method·path를 명시하며, `rules`(요청 허용 규칙) 생략과 범용 바이너리(`curl`·`python3`·`node`처럼 어떤 요청이든 보낼 수 있는 실행 파일) + `/**`(모든 경로) 조합을 쓰지 않는 정책 요건이다(`docs/plan/DEV_PLAN.md` §4.1).
- **사용자 결정**(2026-09-24(목) 17시 무렵): 결정 기록 `20260924-1720-user-decision-domain-restructure.md`, `20260924-1720-user-decision-x1-option-ga.md`. 오케스트레이터가 정한 X1 재시도의 마감과 시험 방식은 `20260924-1741-orchestrator-decision-x1-retry.md`다.
  - 도메인 재편 A안: 도메인(책임 하나와 소유자 하나를 가진 기능 묶음)을 최소 단위로 다시 나눠 단위별 앱(혼자 실행하고 시험할 수 있는 단위)으로 따로 구현한 뒤 조립한다. 계획 모듈 이름은 패키지로 바꾸고 새 이름 다섯 개를 둔다. 도메인별 출력물은 `outputs/{실행 이름}-{시각}/` 폴더에 `{도메인명}-{yymmddhhmmss}.{확장자}` 이름으로 쌓는다(KST, 덮어쓰기 금지, 커밋 안 함). 실행 이름은 시각이 붙지 않은 실행의 이름(예: `run_case`)이다. 커밋 증거물도 같은 이름 규칙을 쓰고, 봉인 묶음(개발 중 보지 않도록 봉인한 평가 자료 묶음) 실행 출력은 `outputs/sealed/`에 둔다. 정답 대조 채점이 끝나기 전에는 열람 금지다(세부 조건은 `docs/rules/DATA_CONTRACT_V1.md` §10.3 N10의 금지 해제 조건, 곧 정답 대조 채점이 끝나고 `real_sealed`이면 표본 추출 seed 공개 기록까지 있는 때). 봉인 자료 자체는 계속 저장소 밖 봉인 폴더에 둔다.
  - X1 (가)안(사용자 결정): NemoClaw 제3자 소프트웨어 고지를 수락하고 NemoClaw 시연 경로를 다시 시도한다. 마감(같은 날 19:30)과 시험 방식은 오케스트레이터가 정했다.
- **사용자 결정**(2026-09-24(목) 19:35 무렵): 결정 기록 `20260924-2010-user-decision-key-rule-interpretation.md`. 절대 규칙 1·요건 (c)의 "샌드박스 안"을 에이전트와 그 자식 프로세스가 읽을 수 있는 곳으로 읽고(해석 A) 규칙 문구를 고쳤다. NVIDIA 키는 대회 마무리(2026-09-28(월) 제출 뒤)에 사용자가 재발급하고, 오케스트레이터가 그때 재발급과 사본 정리를 안내한다. NemoClaw 설치기 고지 전문에 이의가 없다.
- **X1 세로형 최소 통합 시험**(2026-09-24(목), 조건부 통과, X1 PR #19로 병합): NemoClaw v0.0.124 시연 샌드박스에서 OpenClaw(NemoClaw의 기본 에이전트) 요청 → `x1-probe` 스킬 → 샌드박스 안 CLI → NIM 1회(HTTP 200) → NAT 실행 추적(이벤트 4개) → 의도적 위반 1건 차단의 한 줄 경로가 통과했다.
  - 요건 (b)(외부 전송은 NVIDIA 추론 엔드포인트만, L7 method·path 명시, `rules` 생략과 범용 바이너리 + `/**` 금지) 판정과 통과 증거는 최종 4판 정책(17:55 뒤, `nvidia` 블록 하나) 실행만 쓴다. 2판·3판에는 규칙 없는 `openclaw_gateway_dialback` 블록이 남아 있었다.
  - 4판 턴은 SKILL.md를 다시 읽지 않고 exec(셸 명령 실행 도구)만 두 번 불렀다(CLI 두 번, 각각 NIM 1회). 스킬을 읽고 CLI를 부른 기록은 3판 턴(17:46)이다. 같은 세션의 앞 턴 문맥을 썼다는 설명은 `[추론]`이고, 새 세션으로 4판에서 다시 돌리는 일은 MT5에서 한다.
  - 요건 (c)(API 키를 샌드박스 안에 두지 않는다)는 해석 A(2026-09-24(목) 사용자 결정, 결정 기록 `20260924-2010-user-decision-key-rule-interpretation.md`)에 따라 충족. 키 조회는 샌드박스 사용자(UID 998) 권한으로 닿는 곳 기준으로 실제 키 0건이었고, 실제 키는 샌드박스 컨테이너 안에서 root로 도는 감독 프로세스(supervisor)가 게이트웨이에서 받아 가진다(`artifacts/openshell/violation_tests.md` 머리말 "키 조회 범위").
  - 조건: NemoClaw `agent` 래퍼가 OpenClaw 결과의 `replayInvalid` 표식(OpenClaw 결과는 성공, NemoClaw 기준으로는 미완료 표식) 때문에 종료 코드 1을 냈다. 원인은 미확인이고 조사는 MT5에서 한다(`docs/tracking/findings.md`). 스킬 호출 성공률의 증거를 세는 규칙은 결정 기록 `20260924-2315-user-decision-impl-plan-approval.md` D5로 정했다(로드맵 V1 행).
  - 키 주입 방식은 credential placeholder rewrite(헤더 자리표시 값 치환. 샌드박스 안 감독 프로세스의 정책 프록시가, 게이트웨이에서 받은 자격 증명으로 요청 시점에 자리표시 값을 실제 키로 바꾼다)로 정했다(`docs/tracking/decisions/20260924-1556-x1-key-injection.md`). 추론 블록에 node를 넣는 예외는 `docs/plan/DEV_PLAN.md` §4.8에 적었다.
  - 증거는 `artifacts/openshell/violation_tests.md`와 `artifacts/openshell/logs/`, 재현 절차는 `spikes/x1/README.md`다.
- **PR #18 확인**(2026-09-24(목) 20:19): 사용자가 PR #18의 확인 항목 여덟 가지(N5·N7·N11·N12와 `run_id`=실행명, "증거 복사"·"커밋 사본", 출력 방식 (나), 봉인 관련 출력 범위, 작성 중 더한 `[DESIGN]` 항목, 룰북 부록 41, 설계 명세 경로 표 맞추기, 앱 뼈대(S0) 외부 자문 "반영 없음"에 따른 따로 병합)를 모두 승인했다. 실행 결과 기록 파일 이름은 `scorer_results-{시각}.jsonl`로 바꾸기로 골랐고, 그에 따라 단위 C3을 C3·C4로 나눈 것(65단위)도 21:51에 승인했다. 결정 기록은 `20260924-2055-user-decision-pr18-confirmation.md`다. 봉인 관련 출력 범위는 `20260924-2003-orchestrator-decision-sealed-output-scope.md`, S0 외부 자문 "반영 없음"(같은 날 20:15)은 `20260924-2035-user-decision-s0-no-advisory.md`에 있다.
- **사용자 결정**(2026-09-24(목) 21:51): 구현 계획은 S0 병합 뒤 따로 세우고 사용자가 오늘 밤 보고 승인한 뒤 두 트랙을 시작한다. 최종 스냅샷 빌드 파일은 `data/snapshots/{snapshot_id}/snapshot_build.sqlite`(동결 폴더에 새 이름, 기존 파일 불변)다. `g0`는 대상국을 뺀 15개국 중 2023년 수입금액 상위 5개국이다. 결정 기록 `20260924-2212-user-decision-impl-plan-after-s0.md`, `20260924-2212-user-decision-snapshot-build-and-g0.md`.
- **앱 뼈대 S0**(2026-09-24(목), S0 PR): 패키지 15개와 `eval/scorer/`·`eval/datagen/`, 단위 표대로 단위 파일 뼈대(저장소에 두는 앱·커널 54개, 기존 S1 포함), 단위 등록부와 공통 실행기(실행명 확보 N8), 골든 시험 틀, 경계 시험, CLI 진입점 `tradesentry`, Python 3.12.13·uv lock. 시험 `uv run --locked python -m unittest discover -s tests -v`는 종료 코드 0이다(Ran 139: ok 85, skipped 54). 외부 자문은 반영 없음이고(결정 기록 `20260924-2035-user-decision-s0-no-advisory.md`), S0가 정한 위치와 약속은 결정 기록 `20260924-2212-orchestrator-decision-s0-scaffold.md`에 있다.
- **구현 계획 승인**(2026-09-24(목) 23:09): 자료 계약 PR #18과 S0 PR이 병합된 뒤, 사용자가 두 트랙 구현 계획과 결정 열한 가지(D1~D8, D16~D18)를 승인했고 두 트랙 구현을 시작했다. 결정 기록 `20260924-2315-user-decision-impl-plan-approval.md`.
- **NIM 연결**: NIM(NVIDIA 클라우드 추론 API)의 Nemotron(NVIDIA 언어 모델)에서 native tool call(모델이 도구 호출을 구조화된 형식으로 요청하는 기능) 왕복은 구 개발계획의 G4 관문 시험(NIM으로 모델의 도구 호출 왕복을 확인한 이전 계획의 시험)에서 확인한 기록이 있다(`docs/plan/DEV_PLAN.md` §3.1). NAT(NVIDIA 에이전트 실행 추적·평가 도구 모음) 연동은 아직 시작하지 않았다(같은 문서 §3.3). 확인 스크립트는 `scripts/g4_nim_toolcall_probe.py`이고, 이번 문서 작업에서는 다시 돌리지 않았다.
- **사용자 결정**(2026-09-25(금) 08:41): `policy_v1` 수치와 판정 해석 U1~U4 승인, 실자료 판정 분포 수용(결정 기록 `20260925-0846-user-decision-policy-v1-approval.md`), `real_sealed` 표본 추출 방법(`20260925-0845-user-decision-real-sealed-sampling-method.md`), 공용 약속 결정 11개(토큰 한도 128,000, 원인 분류 코드 11개, `tool_attempts`의 뜻, 실자료 `required_evidence_ok` null, 분할 기록 위치, 필수 근거 코드 13개, 실행명 `--run-name`, `RB-1` 동결 2026-09-26(토) 18:00, `evaluate --mode`, 규칙 참고값과 도구 호출 요구, 보류 사유별 필수 근거)와 진행 방식(`20260925-0847-user-decision-morning-shared-promises.md`). 계획 문서 반영은 두 번째 문서 PR(DOCS2)에서 했고, 비밀값·로컬 경로 검사 `scripts/secret_scan.py`도 그 PR에서 만들었다. 같은 날 12:05 무렵에 사용자가 자료 계약 버전을 `schema_version=2`로 올리기로 정했다(결정 기록 `20260925-1205-user-decision-schema-v2.md`). 코드·자료의 버전 올림과 재생성은 `data/schema-v2` PR이 한다.
- **사용자 결정**(2026-09-25(금) 14:17 무렵): `real_dev`(실자료 개발 묶음) MVP 사례 두 건의 `INVALID`(검증을 통과하지 못해 무효로 끝난 실행)를 보고, `real_dev`의 용도에 조사 지침(모델 프롬프트)·조사 흐름 조정을 더하고, 모델 설정 `model-1.3`과 조사 흐름 수정 두 가지((가) 발동하지 않은 신호에만 쓰는 재조회 요청은 코드가 버림 (나) 검수자 요구로 고친 초안이 막히고 수정 전 초안이 통과했으면 수정 전 초안을 최종으로)를 쓰기로 했다. 결과 요약과 제출서에 "`real_dev`에서 본 실패 유형으로 조사 지침과 흐름을 조정했다"를 밝힌다. 결정 기록 `20260925-1417-user-decision-real-dev-tuning.md`. 계획 문서 반영은 세 번째 문서 PR(DOCS3)이 한다. 남은 일: 코드 PR(브랜치 `model/AS2-prompt-numbers`: `model-1.3`, 흐름 수정 (가)·(나), 시험) 병합, 채점 대상 실행 샌드박스와 시연 샌드박스 다시 굽기(재스테이징), `real_dev` 몇 건으로 확인, 그 뒤 V1(MVP 시험).
- **사용자 결정**(2026-09-25(금) 15:52 무렵): `real_dev` 사례 5건을 `full` 모드로 돌려 3건이 `PROVIDER_HTTP_4XX`(HTTP 429, 호출 한도 초과)로 실패한 것을 보고, HTTP 429도 5xx(서버 오류)처럼 다루기로 했다(사용자 결정 5 변경). 한 실행 안에서 요청당 최대 3회 재전송하고 대기는 5xx·429 모두 5·10·20초(지수 대기, 조정값)이며 모델 요청 횟수에 센다. 재전송 한도를 다 쓴 429는 원인 분류 코드 `PROVIDER_HTTP_4XX` 그대로 룰북 B5의 인프라 실패 재실행 대상에 넣는다(다른 4xx는 그대로 대상 아님, 모든 모드 같은 규칙). 결정 기록 `20260925-1552-user-decision-429-retry.md`. 계획 문서 반영은 네 번째 문서 PR(DOCS4)이 한다. 남은 일: 코드 PR(브랜치 `model/AS3-429-retry`: 단위 I7 재전송, 단위 L3 재실행 대상 판정, 모델 설정 대기값과 `config_version`, 시험) 병합, 샌드박스 다시 굽기, 그 뒤 V1.

## 남은 일

앱 뼈대(S0)가 있고 단위 구현은 아직 없다. 순서·날짜·완료 기준의 정본은 `docs/plan/ROADMAP.md` §1·§2다.

1. 앱 뼈대 S0는 S0 PR로 들어갔다(위 "된 것"). X1 세로형 최소 통합 시험(NemoClaw(OpenShell, 곧 에이전트를 격리해 돌리는 NVIDIA 샌드박스 런타임 위에서 에이전트를 돌리는 NVIDIA 참조 스택) → 스킬 → 샌드박스 안 CLI → NIM → NAT 추적 → 차단 로그)은 조건부 통과했다(위 "된 것"). `replayInvalid` 원인 조사는 MT5에서 한다
2. 두 트랙 구현(계획 승인됨, 결정 기록 `20260924-2315-user-decision-impl-plan-approval.md`): 데이터 트랙 DT1~DT8, 모델 트랙 MT1~MT7(단위별 구현 뒤 조립 작업 AS1~AS4)
3. 2026-09-25(금) MVP(최소 기능 제품) 시험(로드맵 §3 합격 체크리스트)
4. 룰북 `RB-1`(평가 룰북의 첫 동결 버전) 동결, holdout40(봉인한 합성 평가 사례 40건)·`real_sealed`(봉인한 실자료 평가 묶음) 채점 대상 실행과 정답 대조 채점, 결과·재현 묶음, 제출(마감 2026-09-28(월) 23:59 KST)
5. 대회 마무리(제출 뒤): NVIDIA 키 재발급 안내와 사본 정리(결정 기록 `20260924-2010-user-decision-key-rule-interpretation.md` ③). 재발급은 사용자가 하고 오케스트레이터가 안내한다. 사본 위치와 정리할 곳은 `docs/operations.md`의 "키 사본 위치와 교체 때 정리할 곳" 절이다

## 사용자 결정 대기

로드맵 §6(`docs/plan/ROADMAP.md`)의 사용자 확인 항목과 그 밖에 지금 걸려 있는 것이다.

- `g1` 동결과 최종 스냅샷 빌드의 순서: 로드맵 §6.1, DT7 ② 전
- 룰북 `RB-1` 동결 때 확인할 부록 13개 항목: 로드맵 §6.2
- 대회 참가 조건 확인(교육 미션 DLI(NVIDIA 교육 과정) 강의는 늦어도 2026-09-27(일)까지): 로드맵 §6.5
- 공개 저장소 방식 결정: 2026-09-28(월) 오전, 로드맵 §6.1
- 계획 문서 작업 중 오케스트레이터(작업을 나누고 PR을 병합하는 주관 에이전트)가 정해 둔 해석 가운데 사용자 확인이 남은 것: `docs/tracking/decisions/20260924-0810-docs-run-review-decisions.md`의 4·6·9·10·11·12·18·19행. 행마다 "사용자 확인" 칸에 확인 시점이 있다. 1·5·13행은 2026-09-24(목)에 승인했고, 2행(`g0` 해석)은 같은 날 21:51 사용자 결정으로 확정했다(결정 기록 `20260924-2212-user-decision-snapshot-build-and-g0.md` ②)
- X1 뒤 개발 기계 정리(선택): 사용자 zsh 시작 설정 파일(`.zshrc`)에 NemoClaw가 더한 PATH 블록을 둘지. 되돌리는 방법은 `spikes/x1/README.md`의 "개발 기계 되돌리기" 절에 있다. 명령은 공개 문서(판을 고정한 OpenShell·NemoClaw 문서, Homebrew 공식 manpage(명령 설명서), Docker 공식 문서)로 확인한 것만 적었고, LaunchAgent(로그인할 때 프로그램을 띄우는 macOS 설정) 파일 삭제 등은 `[미확인]`으로 남았다. 1단계 게이트웨이 상태 저장소에 키가 남았는지는 `[미확인]`이고, 키 사본 정리는 대회 마무리 때 한다(위 "남은 일" 5). X1 PR의 병합 조건은 아니다
- 아직 어느 문서에도 규칙이 없어 정해야 하는 것: `docs/tracking/findings.md`의 해당 항목(재실행 규칙의 빈칸(결정 D12), 시험표 행의 작성 주체, 저장소 공개 때의 PR 참조 검사)
