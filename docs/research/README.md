# 이전 설계·조사 기록(docs/research)

이 폴더는 주제 선정과 초기 설계 때(2026-09-22(화)~2026-09-23(수)) 만든 조사·계획 문서를 모은 곳이다. 2026-09-27(일) 사용자 요청으로 저장소 루트에서 이 폴더로 옮겼다(결정 기록 `docs/tracking/decisions/20260927-1030-user-decision-readme-journal-research-move.md`). 파일 이름과 내용은 그대로이고, 사실 출처로 인용만 하며 고치지 않는다. 현행 설계의 정본은 `docs/`의 계획·규칙·평가 문서다(문서 색인 `docs/README.md` 4절).

## 묶음별 목록

| 묶음 | 파일 | 성격 |
|---|---|---|
| 대회·NVIDIA 스택 조사 | `NVIDIA-FastCampus-Korea-Agentic-AI-Hackathon-2026.md`, `HSGATE_R3_NVIDIA_STACK_CHECK.md`(R3 문서), `03-openshell-policy-yaml-구조.md`(03 문서) | 대회 요건과 OpenShell·NemoClaw·Agent Skills 서술의 근거. 현행 문서가 인용한다 |
| 팀 채점 규범 | `SCORING_GOLDEN_RULE.md` | 팀이 정한 아이디어·제출물 평가 기준(대회 공식 배점이 아니다). 평가 룰북 Part A와 평가 스킬 ①(`skills/tradesentry-scorecard/`)이 기댄다 |
| 구 개발계획·분담·인계 | `Pasted markdown.md`(구 개발계획), `TRADESENTRY_TEAM_SPLIT_DECISIONS.md`(분담 문서), `TRADESENTRY_HANDOFF.md`(인계 문서), `TRADESENTRY_FACTS_MEMO.md`(실측 메모) | 현행 개발 플랜이 대체한 계획과 이전 세션 인계. 바뀐 결정은 `docs/plan/DEV_PLAN.md` "기존 계획 대비 바뀐 점" 표 |
| 아이디어 탐색 | `IDEA_CANDIDATES.md`, `IDEA_EXPANSION_CHATGPT_REVIEW.md`, `IDEA_EXTERNAL_CANDIDATES_REVIEW.md`, `IDEA_LIFE_EMBEDDED_BRAINSTORM.md`, `IDEA_REAL_CUSTOMER_BRAINSTORM.md`, `IDEA_REAL_WORLD_USE_CASES.md`, `CHATGPT_REVIEW_TRANSCRIPT.md`, `DATA_AND_SKILL_INVENTORY.md`, `01-제안서-초안.md`, `02-에이전트-개발-규약-정책서.md` | 주제 선정 과정의 탐색 기록. 현행 설계의 근거가 아니다 |
| 이전 후보(HSGate) 조사 | `HSGate_설계서.md`, `HSGate_근거자료_및_반영사항.md`, `HSGate_도메인학습_및_구체화_체크리스트.md`, `HSGATE_DATA_VALIDITY.md`, `HSGATE_EVALUATION_DATA_REVIEW.md`, `HSGATE_R0_CHECKLIST_STATUS.md`, `HSGATE_R1_GRI_LAW.md`, `HSGATE_R2A_SECTION16_NOTES.md`, `HSGATE_R2B_CH39_CH90_NOTES.md`, `HSGATE_R4_DATAFILES_PENALTY_CASES.md`, `HSGATE_R5_COMPETITION_BENCHMARKS.md`, `HSGATE_R6_TARGET_CHAPTER_SELECTION.md`, `research_raw/`(원자료 2개) | 주제 선정 때 조사하고 채택하지 않은 후보 기록 |

## 옛 경로와 새 경로

- 모든 파일이 이름 그대로 이 폴더 아래로 옮겨졌다. 옛 경로 `<파일 이름>`(저장소 루트)은 새 경로 `docs/research/<파일 이름>`이고, 옛 `research_raw/…`는 `docs/research/research_raw/…`다. 이 폴더 안 문서끼리의 상대 참조는 그대로 맞는다.
- 옮기기 전 경로(저장소 루트)로 적힌 곳은 고치지 않았다. 읽을 때 위 규칙으로 바꿔 읽는다.
  - 동결된 평가 룰북 `docs/eval/RULEBOOK.md`(`RB-1` 동결 뒤에는 고치지 않는다)
  - 지난 결정 기록(`docs/tracking/decisions/`의 2026-09-27(일) 이전 파일)과 커밋된 증거물(`artifacts/`)
  - 평가 자료 도구의 주석과 시나리오 명세(`eval/datagen/holdout40_check.py`, `eval/scenarios/SCENARIO_SPEC.md`)
  - 평가 스킬 ① 머리말 설명과 거버넌스 카드 설명 문장의 파일 이름 표기(경로가 아닌 이름. 카드의 링크는 새 경로로 고쳤다)
  - 샌드박스 이미지 준비 스크립트의 차단 목록(`scripts/stage_sandbox_image.py`. `docs/`가 이미 차단돼 이 폴더는 이미지에 들어가지 않는다)
- 비밀값 검사(`scripts/secret_scan.py`)의 이력 문서 기준선은 이 폴더 바로 아래 파일에만 적용된다.
