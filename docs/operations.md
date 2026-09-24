# 실행 절차

## 처음 준비

1. `.env.example`을 `.env`로 복사하고, 사용자가 API 키 두 개(`DATA_GO_KR_SERVICE_KEY`, `NVIDIA_API_KEY`)를 넣는다. 에이전트는 `.env`를 열지 않는다(`docs/rules/PARALLEL_DEV_RULES.md` §10.2).
2. git이 추적하지 않는 자료는 새 worktree(작업 복사본)에 없다. 스냅샷의 SQLite·원자료(`data/snapshots/*/raw/`, `snapshot.sqlite`)와 `.data/`의 BACI(CEPII가 정리한 국가 간 연간 무역 자료) 원본이 필요한 작업은 메인 작업 폴더에 있는 그 파일·폴더의 경로만 읽기 위치로 준다. 폴더 전체와 `.env`는 주지 않는다(`docs/rules/AGENT_OPS.md` §1.3·§2.2).
3. 앱 뼈대(S0) 전에는 표준 라이브러리 코드와 기존 시험만 시스템 `python3`로 돌린다. Python 3.12 가상환경과 uv(파이썬 패키지·가상환경 관리 도구)·lock(패키지 버전 고정 파일)은 S0에서 만든다(`docs/plan/SCAFFOLD_BRIEF.md` §4.1).
4. 시험 명령은 `docs/plan/ROADMAP.md` §2.1의 공통 완료 기준을 따른다. S0 뒤에는 S0에서 정한 가상환경의 같은 시험으로 바뀐다.

## 하려는 일별 정본

명령·경로 이름의 정본은 `docs/rules/DATA_CONTRACT_V1.md` §10이다. 앱 뼈대(S0) 외부 자문으로 이름이 바뀌면 그 표가 먼저 바뀐다.

| 하려는 일 | 정본 |
|---|---|
| 시험 실행(S0 전·후) | `docs/plan/ROADMAP.md` §2.1, `docs/rules/AGENT_OPS.md` §5.2 |
| 계획된 CLI 명령·공통 옵션·산출물 경로 | `docs/rules/DATA_CONTRACT_V1.md` §10 |
| 개발 환경(macOS, Docker 안 OpenShell(에이전트를 격리해 돌리는 NVIDIA 샌드박스 런타임) 게이트웨이(샌드박스의 정책과 provider(등록한 자격 증명 묶음) 설정을 보관하고 샌드박스에 내려보내는 OpenShell 제어면), 시스템 `python3` 3.9.6, Python 3.12·uv) | `docs/plan/DEV_PLAN.md` §3.5 |
| 환경변수(`NVIDIA_API_KEY`, `DATA_GO_KR_SERVICE_KEY`는 `.env`, 봉인 폴더 위치는 `TRADESENTRY_SEALED_DIR`) | `docs/rules/PARALLEL_DEV_RULES.md` §10.2, `docs/rules/DATA_CONTRACT_V1.md` §10 |
| 스냅샷 검사(`ingest.py verify`)를 기록을 덮지 않고 돌리는 법 | `docs/rules/PARALLEL_DEV_RULES.md` §10.1 |
| NIM(NVIDIA 클라우드 추론 API) tool call(모델이 도구 호출을 구조화된 형식으로 요청하는 기능) 왕복 확인 스크립트 | `docs/plan/DEV_PLAN.md` §3.5 |
| X1(구현 첫날의 세로형 최소 통합 시험: 설치·기동, 키 주입, NAT(NVIDIA 에이전트 실행 추적·평가 도구 모음) 추적, 차단 로그) | `docs/plan/DEV_PLAN.md` §5.3, `docs/plan/ROADMAP.md` §2.2 |
| NemoClaw(OpenShell 위에서 에이전트를 돌리는 NVIDIA 참조 스택)가 안 될 때의 대체 경로와 시한 | `docs/plan/DEV_PLAN.md` §5.4, `docs/plan/ROADMAP.md` §7.1 |
| 공식 스킬과 우리 스킬(스킬은 Agent Skills 형식의 에이전트용 작업 절차)의 설치·이름 확인 | `docs/eval/SKILL_DICTIONARY.md` §5 |
| 성능 평가(사전 점검 → 실행 → 채점 → 결과 보고) | `skills/tradesentry-eval/SKILL.md` |
| 자기채점 | `skills/tradesentry-scorecard/SKILL.md` |
| Codex(OpenAI의 코딩 에이전트 CLI) 실행(권한 모드, 환경변수 제거, 제한 시간) | `docs/rules/AGENT_OPS.md` §2.2·§2.4 |
| 날짜별 도착점, 작업 순서, 늦어질 때 줄이는 순서 | `docs/plan/ROADMAP.md` §1·§2.6·§5 |
| 재전송(요청 단위)과 재실행(실행 단위) | `docs/eval/RULEBOOK.md` B5, `docs/plan/ROADMAP.md` §4.2 |

배포는 없다. 제출용 공개 저장소 방식은 2026-09-28(월) 오전에 사용자가 정한다(`docs/plan/ROADMAP.md` §6.1).

## 키 사본 위치와 교체 때 정리할 곳

키 원본은 저장소 `.env`에 있다. 사본은 설계된 주입 경로에만 생기고, 에이전트는 사본 위치를 열거나 출력하지 않는다(`docs/rules/PARALLEL_DEV_RULES.md` §10.2). NVIDIA 키와 그 사본은 대회 마무리(2026-09-28(월) 제출 뒤)까지 두고, 마무리 때 사용자가 키를 재발급하고 오케스트레이터가 재발급과 사본 정리를 안내한다(결정 기록 `20260924-2010-user-decision-key-rule-interpretation.md` ③).

아래는 X1이 만든 사본의 위치와 지우는 방법이다. 어느 곳도 열지 않는다. `<…>` 자리표시(개발 기계 경로 대신 쓰는 이름)를 찾는 방법은 `spikes/x1/README.md`의 "자리표시" 절에 있다.

- 시연 게이트웨이(NemoClaw가 다시 구성한 OpenShell 게이트웨이, 127.0.0.1:8080)의 provider `nvidia-prod`: 자격 증명 키 이름은 `NVIDIA_INFERENCE_API_KEY`다(`artifacts/openshell/logs/20260924-x1-demo-policy.txt` 2절). DB 폴더는 `<NemoClaw 게이트웨이 상태 폴더>`다.
  - `nemoclaw credentials reset nvidia-prod`: 게이트웨이에서 provider를 지우고 그 provider를 쓰는 샌드박스에서 뗀다 `[사실: NemoClaw v0.0.124 docs/reference/commands.mdx 3605·3645~3651행]`. 또는 `openshell provider delete nvidia-prod` `[사실: OpenShell v0.0.116 docs/sandboxes/manage-providers.mdx 278행]`. NemoClaw 등록부(NemoClaw가 관리하는 샌드박스 목록)와 맞추려면 앞의 명령을 쓴다 `[추론]`.
  - 지우면 시연 샌드박스(NemoClaw 시연 경로를 돌리는 샌드박스 `x1-demo`)가 돌지 않는다.
- provider 자격 증명을 감싸는 KEK(키 암호화 키): 기본 설정의 게이트웨이는 provider 자격 증명을 DB 안에 암호화해 두고, KEK를 게이트웨이 상태 폴더(`XDG_STATE_HOME` 아래 `openshell/gateway/`)의 `credentials/` 아래에 소유자 전용 권한으로 만든다 `[사실: OpenShell v0.0.116 docs/reference/gateway-config.mdx 392행]`. 시연 게이트웨이의 KEK 위치는 설정을 열지 않아 `[미확인]`이다. 같은 OS 사용자에게는 이 암호화가 보호가 되지 않으므로, 실제 통제는 "열지 않는다" 규칙이다 `[추론]`.
- 시연 샌드박스 안 root 감독 프로세스(샌드박스 컨테이너 안에서 root로 돌며 정책을 집행하는 OpenShell 프로세스): 샌드박스가 도는 동안 게이트웨이에서 받은 자격 증명을 가진다 `[사실: OpenShell v0.0.116 docs/about/how-it-works.mdx 116행]`. 보조 근거인 `artifacts/openshell/logs/20260924-x1-demo-openshell-logs.txt` 7·13행은 감독 프로세스가 시작할 때 provider 환경을 받았다는 기록이고, 실제 키 값이 들었는지는 보이지 않는다. 샌드박스를 멈추거나(`nemoclaw x1-demo stop`) 지우면(`nemoclaw x1-demo destroy`) 그 프로세스와 함께 사라진다 `[추론]`.
- 1단계(X1에서 NemoClaw 설치 전에 OpenShell만 쓴 시험) 게이트웨이 상태 저장소(`<1단계 게이트웨이 상태 폴더>`)의 provider `x1-nvidia`·`x1-nvidia-route`(자격 증명 키 이름 `NVIDIA_API_KEY`): 지웠는지 `[미확인]`이다(정리 기록 없음, `artifacts/openshell/violation_tests.md`의 시험 환경 표 "정리" 행). 자격 증명은 그 DB 안에 암호화돼 있다 `[사실: OpenShell v0.0.116 docs/reference/gateway-config.mdx 392행]`.
  - `openshell provider delete x1-nvidia-route`(또는 `x1-nvidia`)를 지금 실행하면 활성 게이트웨이(`nemoclaw`)로 가므로 대상이 없다. 1단계 게이트웨이(`openshell`, 17670)는 NemoClaw가 서비스를 다시 구성한 뒤 뜨지 않는다(`artifacts/openshell/logs/20260924-x1-demo-transcript.txt` [N2]). CLI의 `-g`로 게이트웨이를 고를 수는 있지만(OpenShell v0.0.116 docs/sandboxes/manage-gateways.mdx 83행) 1단계 게이트웨이 프로세스가 없어 이 방법은 쓸 수 없다 `[추론]`.
  - 저장소 파일을 지울지와 그 시점은 결정 기록 `20260924-2010-user-decision-key-rule-interpretation.md` ③을 따른다. ③은 NVIDIA 키와 그 사본을 대회 마무리까지 두고, 마무리 때 사용자가 키를 재발급하고 오케스트레이터가 재발급과 사본 정리를 안내한다는 결정이다.
- NemoClaw 설정 폴더(`<NemoClaw 설정 폴더>`): 현재 판은 `credentials.json`(예전 판이 쓰던 평문 자격 증명 파일)을 만들지 않는다 `[사실: NemoClaw v0.0.124 docs/reference/host-files-and-state.mdx 37행]`. 이 폴더에 사본이 있는지는 `[미확인]`이다.
- 호스트 전달 프로세스(시연 샌드박스의 대시보드를 호스트 127.0.0.1:18789로 이어 주는 프로세스): 키 래퍼(`.env`에서 키 한 줄만 읽어 자식 프로세스에만 넘기는 `spikes/x1/with_nvidia_key.py`) 아래에서 돈 온보딩(`nemoclaw onboard` 설정 단계) 도중에 시작했다 `[추론: artifacts/openshell/logs/20260924-x1-demo-transcript.txt [N2]에는 샌드박스가 없었고, [N3] 온보딩 끝에 대시보드 점검이 통과했다]`. NemoClaw는 하위 프로세스 환경을 허용 목록으로 만들고 그 목록에 `NVIDIA_INFERENCE_API_KEY`가 없으므로, 키를 물려받았을 가능성은 낮다 `[추론: NemoClaw v0.0.124 src/lib/subprocess-env.ts 6~62행]`. 그 프로세스의 환경은 열어 보지 않았다.
