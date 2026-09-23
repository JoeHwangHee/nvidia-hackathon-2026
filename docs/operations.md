# 실행 절차

명령·경로 이름의 정본은 `docs/rules/DATA_CONTRACT_V1.md` §10이다. 앱 뼈대(S0) 외부 자문으로 이름이 바뀌면 그 표가 먼저 바뀐다.

| 하려는 일 | 정본 |
|---|---|
| 시험 실행(S0 전에는 시스템 `python3`의 기존 명령, S0 뒤에는 S0에서 정한 가상환경의 같은 시험) | `docs/plan/ROADMAP.md` §2.1, `docs/rules/AGENT_OPS.md` §5.2 |
| 계획된 CLI 명령·공통 옵션·산출물 경로 | `docs/rules/DATA_CONTRACT_V1.md` §10 |
| 개발 환경(macOS, Docker 안 OpenShell 게이트웨이, 시스템 `python3` 3.9.6, Python 3.12·uv) | `docs/plan/DEV_PLAN.md` §3.5 |
| 환경변수(`NVIDIA_API_KEY`, `DATA_GO_KR_SERVICE_KEY`는 `.env`, 봉인 폴더 위치는 `TRADESENTRY_SEALED_DIR`) | `docs/rules/PARALLEL_DEV_RULES.md` §10.2, `docs/rules/DATA_CONTRACT_V1.md` §10 |
| 스냅샷 검사(`ingest.py verify`)를 기록을 덮지 않고 돌리는 법 | `docs/rules/PARALLEL_DEV_RULES.md` §10.1 |
| NIM tool call 왕복 확인 스크립트 | `docs/plan/DEV_PLAN.md` §3.5 |
| X1 세로형 최소 통합 시험(설치·기동, 키 주입, NAT 추적, 차단 로그) | `docs/plan/DEV_PLAN.md` §5.3, `docs/plan/ROADMAP.md` §2.2 |
| NemoClaw가 안 될 때의 대체 경로와 시한 | `docs/plan/DEV_PLAN.md` §5.4, `docs/plan/ROADMAP.md` §7.1 |
| 공식 스킬과 우리 스킬의 설치·이름 확인 | `docs/eval/SKILL_DICTIONARY.md` §5 |
| 성능 평가(사전 점검 → 실행 → 채점 → 결과 보고) | `skills/tradesentry-eval/SKILL.md` |
| 자기채점 | `skills/tradesentry-scorecard/SKILL.md` |
| Codex 실행(권한 모드, 환경변수 제거, 제한 시간) | `docs/rules/AGENT_OPS.md` §2.2·§2.4 |
| 날짜별 도착점, 작업 순서, 늦어질 때 줄이는 순서 | `docs/plan/ROADMAP.md` §1·§2.6·§5 |
| 재전송(요청 단위)과 재실행(실행 단위) | `docs/eval/RULEBOOK.md` B5, `docs/plan/ROADMAP.md` §4.2 |

배포는 없다. 제출용 공개 저장소 방식은 2026-09-28(월) 오전에 사용자가 정한다(`docs/plan/ROADMAP.md` §6.1).
