# 시스템 구성

## 실행 사슬

운영자 → NemoClaw(OpenClaw 에이전트를 OpenShell 위에서 돌리는 NVIDIA 참조 스택) → 런타임 스킬 `tradesentry` → TradeSentry CLI(OpenShell 샌드박스 안) → 조사 흐름(NAT, 곧 NVIDIA 에이전트 도구 모음으로 감싸 실행을 추적) → 조회 도구 5개 → 읽기 전용 SQLite 스냅샷.

- 모델 호출은 샌드박스 밖 OpenShell 게이트웨이를 거쳐 NIM의 Nemotron으로 나간다. 키는 샌드박스 안에 없다.
- 채점 대상 실행(점수에 들어가는 실행)은 NemoClaw를 거치지 않고 OpenShell 안 CLI를 직접 부른다. NemoClaw 경로는 시연과 스킬 호출 성공률로 따로 증명한다.
- 정답 대조 채점은 샌드박스 밖 독립 채점기(`eval/scorer/`)가 한다. 채점기는 런타임 코드를 import하지 않는다.

위 사슬에 드는 구성요소, 경로, 명령 이름의 정본은 아래 문서들이다.

| 알고 싶은 것 | 정본 |
|---|---|
| 구성요소별 역할과 연결 | `docs/plan/DEV_PLAN.md` §3.1 |
| 채점 대상 실행 경로와 시연 경로의 차이 | 같은 문서 §3.2·§5.1 |
| 검증기(실행 중 보고서 검사)와 NAT 사후 평가의 역할 구분 | 같은 문서 §3.3 |
| 넣지 않는 구성요소와 이유 | 같은 문서 §3.4 |
| 개발·실행 환경(macOS, Docker 안 OpenShell 게이트웨이, Python 3.12) | 같은 문서 §3.5 |
| 샌드박스 안에 들어가는 것과 들어가지 않는 것, 샌드박스 세 가지(채점 대상 실행용·공식 채점 전용·시연용) | 같은 문서 §4.3·§4.5·§4.8, `docs/plan/SCAFFOLD_BRIEF.md` §4.4.1 |
| NemoClaw가 안 될 때의 대체 경로(Brev, OpenShell만) | `docs/plan/DEV_PLAN.md` §5.4 |
| 모듈 역할과 소유 트랙 | 같은 문서 §10.2·§10.3, `docs/rules/PARALLEL_DEV_RULES.md` §1.2 |
| 계획된 경로·명령 표 | `docs/rules/DATA_CONTRACT_V1.md` §10 |
| 앱 폴더 구조처럼 앱 뼈대(S0)에서 정할 설계 | `docs/plan/SCAFFOLD_BRIEF.md` §2.6·§5.2·§5.3 |
| 평가 흐름(사전 점검 → 실행 → 채점 → 결과 보고) | `skills/tradesentry-eval/SKILL.md`, `docs/eval/RULEBOOK.md` Part B |
