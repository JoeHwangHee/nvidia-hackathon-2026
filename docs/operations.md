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
| 개발 환경(macOS, Docker 안 OpenShell(에이전트를 격리해 돌리는 NVIDIA 샌드박스 런타임) 게이트웨이(샌드박스 밖에서 정책을 적용하고 요청을 중계하는 구성요소), 시스템 `python3` 3.9.6, Python 3.12·uv) | `docs/plan/DEV_PLAN.md` §3.5 |
| 환경변수(`NVIDIA_API_KEY`, `DATA_GO_KR_SERVICE_KEY`는 `.env`, 봉인 폴더 위치는 `TRADESENTRY_SEALED_DIR`) | `docs/rules/PARALLEL_DEV_RULES.md` §10.2, `docs/rules/DATA_CONTRACT_V1.md` §10 |
| 스냅샷 검사(`ingest.py verify`)를 기록을 덮지 않고 돌리는 법 | `docs/rules/PARALLEL_DEV_RULES.md` §10.1 |
| NIM(NVIDIA 클라우드 추론 API) tool call(모델이 도구 호출을 구조화된 형식으로 요청하는 기능) 왕복 확인 스크립트 | `docs/plan/DEV_PLAN.md` §3.5 |
| X1(구현 첫날의 세로형 최소 통합 시험: 설치·기동, 키 주입, NAT(NVIDIA 에이전트 실행 추적·평가 도구 모음) 추적, 차단 로그) | `docs/plan/DEV_PLAN.md` §5.3, `docs/plan/ROADMAP.md` §2.2 |
| NemoClaw(OpenShell 위에서 에이전트를 돌리는 NVIDIA 참조 스택)가 안 될 때의 대체 경로와 시한 | `docs/plan/DEV_PLAN.md` §5.4, `docs/plan/ROADMAP.md` §7.1 |
| 공식 스킬과 우리 스킬의 설치·이름 확인 | `docs/eval/SKILL_DICTIONARY.md` §5 |
| 성능 평가(사전 점검 → 실행 → 채점 → 결과 보고) | `skills/tradesentry-eval/SKILL.md` |
| 자기채점 | `skills/tradesentry-scorecard/SKILL.md` |
| Codex(OpenAI의 코딩 에이전트 CLI) 실행(권한 모드, 환경변수 제거, 제한 시간) | `docs/rules/AGENT_OPS.md` §2.2·§2.4 |
| 날짜별 도착점, 작업 순서, 늦어질 때 줄이는 순서 | `docs/plan/ROADMAP.md` §1·§2.6·§5 |
| 재전송(요청 단위)과 재실행(실행 단위) | `docs/eval/RULEBOOK.md` B5, `docs/plan/ROADMAP.md` §4.2 |

배포는 없다. 제출용 공개 저장소 방식은 2026-09-28(월) 오전에 사용자가 정한다(`docs/plan/ROADMAP.md` §6.1).
