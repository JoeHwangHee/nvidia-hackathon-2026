---
title: "NVIDIA x 패스트캠퍼스 — Korea Agentic AI Hackathon 2026 리서치 브리프"
doc_type: research_brief
audience: AI agent (context handoff)
language: ko
researched_at: 2026-09-22T21:00+09:00
revised_at: 2026-09-23T00:20+09:00  # v3 정정: OpenShell 보호 계층(§8-2)
timezone: Asia/Seoul
deadline_utc9: 2026-09-28T23:59+09:00
days_left_at_research: 6
sources: official_only
canonical_sources:
  - https://fastcampus.co.kr/NVIDIA_hackathon
  - https://docs.google.com/forms/d/e/1FAIpQLScyZ5GYYaCOycNUzXVUTenliEUmSEIdXelVdYphvMvLeLuiHA/viewform
  - https://learn.nvidia.com/courses/course-detail?course_id=course-v1:DLI+S-FX-43+V1
  - https://www.nvidia.com/ko-kr/ai-days/
  - https://build.nvidia.com/skills
---

# NVIDIA x 패스트캠퍼스 — Korea Agentic AI Hackathon 2026

> **READ THIS FIRST (for agents):**
> 이 문서는 2026-09-22 기준 1차 조사 결과다. 모든 사실은 공식 출처에서 직접 확인했으며,
> `[VERIFIED]` / `[UNVERIFIED]` / `[INFERRED]` 태그로 신뢰도를 구분했다.
> 추론이나 보강 없이 태그를 그대로 존중할 것. 태그 없는 문장은 모두 `[VERIFIED]`로 간주.
> 섹션 9의 "확인 불가 목록"을 사실로 승격시키지 말 것.

---

## 0. TL;DR — 핵심 5줄

1. 예선 마감 **2026-09-28(월) 23:59 KST**. 온라인 사전 챌린지 → 10팀 → 오프라인 1일 해커톤 → 5팀 → AI Day Seoul 쇼케이스 → 우승 1팀.
2. 예선은 자유 주제지만 **지정 교육 미션(NVIDIA DLI 무료 강의 "Securing Agents with NemoClaw and OpenShell")을 선행**하고, **build.nvidia.com의 "Skill API"를 활용한 데모 프로젝트 제출이 필수**다.
3. **파일 업로드가 필수 항목**이다. 데모 영상/배포는 불필요하지만, GitHub 링크를 적은 pdf/word 파일은 반드시 업로드해야 한다.
4. **2~5인 팀만 지원 가능**. 개인 지원 불가. 2007년 이후 출생자가 1명이라도 있으면 팀 전체 무효.
5. **"Skill API"는 NVIDIA 공식 제품명이 아니다.** 실체는 `build.nvidia.com/skills`(Agent Skills, CLI 설치)와 `integrate.api.nvidia.com/v1`(NIM 추론 API) 두 가지이며, 둘 다 쓰는 것이 안전하다.

---

## 1. 대회 개요

| 항목 | 내용 |
|---|---|
| 공식 명칭 | 2026 NVIDIA Korea Agentic AI Hackathon |
| 주최 | 패스트캠퍼스(FAST CAMPUS, 데이원컴퍼니) x NVIDIA Korea |
| 공식 페이지 | https://fastcampus.co.kr/NVIDIA_hackathon |
| 신청 폼 | https://docs.google.com/forms/d/e/1FAIpQLScyZ5GYYaCOycNUzXVUTenliEUmSEIdXelVdYphvMvLeLuiHA/viewform |
| 문의 | 패스트캠퍼스 고객센터 https://day1fastcampussupport.zendesk.com/hc/ko (평일 10:00~18:00, 점심 12:00~13:00 제외) |
| 형식 | 3주 온라인 예선 + 오프라인 One-day 해커톤 + AI Day Seoul 쇼케이스 |
| 컨셉(공식 문구) | "단순히 질문에 답하는 챗봇이 아니라, 목표를 받으면 스스로 계획을 세우고 도구를 호출하고 문제를 해결하는 에이전트" |
| 명시된 NVIDIA 스택 | DGX Spark, Nemotron, NIM, NemoClaw, OpenShell, L40S |

---

## 2. 전체 일정 (공식 폼 + 공식 페이지 교차 확인)

| # | 단계 | 일시 (KST) | 비고 |
|---|---|---|---|
| 1 | 온라인 사전 챌린지 접수 | 2026-09-11(금) ~ **2026-09-28(월) 23:59** (총 18일) | 데모 프로젝트 제출 필수 |
| 2 | 예선 심사 | 2026-09-29 ~ 10-01 | 10팀 선정 |
| 3 | 본선 진출팀 발표 | **2026-10-02(금)** | 10팀에 개별 연락 |
| 4 | 오프라인 One-day 해커톤 | **2026-10-07(수) 09:00~19:00** | 상세는 아래 |
| 5 | AI Day Seoul 쇼케이스 | **2026-11-10(화) 오후 예정** | 5팀 피칭 → 우승 1팀 |

### 2-1. 10/07 오프라인 해커톤 당일 타임라인
- **09:00~17:00** — ① 선발 10팀에게 Brev GPU 크레딧 지급(팀당 최대 $1,000, L40S 1x) ② 스페셜 미션 확인 ③ NVIDIA 도구로 프로젝트 개발
- **17:00~18:00** — Project Pitching (**팀당 최대 5분**)
- **18:00~19:00** — 시상식 (최종 심사로 AI Day Seoul 참가 5팀 선정)

> ⚠️ **본선 미션은 행사 당일 공개**되며 사전에 공개되지 않는다. 본선 진행 안내는 선발된 10팀에게만 이메일로 발송된다.

### 2-2. AI Day Seoul 2026 (NVIDIA 공식)
- 일정: **2026-11-09(월) ~ 11-10(화)**, **서울 COEX**
- 출처: https://www.nvidia.com/ko-kr/ai-days/ , https://www.nvidia.com/en-us/ai-days
- 11/9 = 세션(Talk) 중심 / 11/10 = 핸즈온 원데이 워크숍 + NVIDIA 인증 자격증 시험
- 워크숍 참가비: USD $199 (얼리버드, 2026-10-19 종료) / USD $500 (정가). 워크숍 등록자는 세션 참석 자격 포함
- 프로그램에 **"Build-a-Claw"**(OpenClaw + NemoClaw로 에이전트 구축) 포함
- `[UNVERIFIED]` 세션 카탈로그(https://www.nvidia.com/ko-kr/ai-days/session-catalog/) 현재 21개 세션 중 **해커톤 쇼케이스 세션은 미등재**. "더 많은 세션 추가 예정" 상태
- `[UNVERIFIED]` 수상 5팀의 AI Day Seoul 참가비 처리 방식은 어느 공지에도 명시 없음

---

## 3. 🔴 예선 참가 조건 — 가장 중요한 부분

### 3-1. 지정 교육 미션이 선행된다 (메모/요약본에서 자주 누락되는 항목)

공식 폼 원문:
> "참가자는 **교육 미션**을 확인한 후, **build.nvidia.com의 Skill API를 활용하여** 데모 프로젝트를 개발합니다."

**[온라인 사전 챌린지] 진행 프로세스 (공식 3단계)**
1. 교육 미션: **"Securing Agents with NemoClaw and OpenShell"** 을 확인한다.
2. **build.nvidia.com을 통해 Skill API를 활용**하여 데모 프로젝트를 직접 개발한다. (채점 항목 참고, **주제는 자유**)
3. 온라인 신청서를 통해 개발한 데모 프로젝트를 제출한다.

**교육 미션 = NVIDIA DLI 무료 자율학습 강의**
- URL: https://learn.nvidia.com/courses/course-detail?course_id=course-v1:DLI+S-FX-43+V1
- 가격: **무료** / 소요: **4시간** / 레벨: Technical - Intermediate / 주제: Generative AI/LLM / 언어: 영어
- 강의 설명: "Go from a single API call to agent coordination, grounded retrieval, deep planning, and safe execution, using NVIDIA NemoClaw as your reference stack to bootstrap the system and OpenShell as the sandbox where agents run securely."
- 학습 목표 5개 (원문):
  1. Build a basic agent loop and identify its core components.
  2. Implement reliable tool use and function calling within an agent system.
  3. Design and coordinate multi-agent systems using structured routing patterns.
  4. Utilize OpenShell to configure agent identities and ensure safe, sandboxed operations.
  5. Deploy and manage autonomous agents while building persistent skill libraries.

`[INFERRED]` 주제는 자유지만 **스택은 사실상 NemoClaw + OpenShell로 지정**되어 있다고 봐야 한다. 심사 1번(NVIDIA Agent 기술 활용 심도)이 여기서 갈린다.

### 3-2. 지원 자격
- **팀 단위 지원만 가능, 최소 2인 ~ 최대 5인**
- 만 19세 이상 대학(원)생 및 일반인 = **2006년생까지 지원 가능**
- **2007년 이후 출생자가 구성원에 포함되면 팀 전체 참가 무효 처리 + 확인 즉시 지원 사항 삭제(파기)**
- 개인 지원자 중 본선 진출자는 추후 팀 구성을 위해 별도 소통 채널에 초대될 예정 `[INFERRED]` 예선 단계 개인 지원은 불리

### 3-3. 신청 방법
- **1팀 = 1신청서가 아님. 팀원 수만큼 각자 개별 제출** (팀장 + 팀원 전원)
- **팀명은 띄어쓰기까지 전원 동일**해야 한 팀으로 묶임. 중복 방지 위해 유니크한 팀명 권장
- 팀장만 포트폴리오(Section 02) 작성. 팀원은 개인정보 입력 후 즉시 설문 종료
- 개인정보 수집·이용 동의는 전원 필수. **한 명이라도 거부하면 팀 전체 지원 불가**

### 3-4. 사전 준비물
- **NVIDIA 계정(build.nvidia.com / developer.nvidia.com) 이메일**
  - 확인 경로: https://developer.nvidia.com/ → Account → My profile → Email
- **GitHub ID** (개인정보 수집 항목에 명시됨)

---

## 4. 신청 폼 전체 구조 (실측 — 폼을 끝까지 열어 확인)

### Section 0 — 사전 확인
- `[필수/라디오]` "※ 지원서 작성 전 확인해주세요." → 선택지 1개: "해당 내용을 모두 확인하였습니다."
- 개인정보 수집·이용 동의 고지 (미동의 시 지원서 작성 즉시 종료)
  - 수집 항목: 이름, 연락처(휴대폰번호), 이메일 주소(NVIDIA 계정 로그인 ID), **Github ID**, 포트폴리오 내용
  - 보유 기간: 접수일로부터 6개월 이내 파기 / 수상자는 발표일 후 2년 보관

### Section 01 — 참여팀 개인정보 입력 (전원 작성)
| 문항 | 타입 | 필수 | 비고 |
|---|---|---|---|
| 참가 팀 이름 | 단답 | ✅ | 띄어쓰기까지 팀원 전원 동일하게 |
| 팀 구성 인원 | 라디오 | ✅ | 2명 / 3명 / 4명 / 5명 |
| 이름 | 단답 | ✅ | 오탈자 주의 (결과 안내용) |
| 연락처 (휴대폰 번호) | 단답 | ✅ | `010-0000-0000` 하이픈 포함 형식 |
| 이메일 주소 (NVIDIA 계정 아이디) | 단답 | ❌ **선택** | 폼 상 required=0. 단 NVIDIA Korea 제3자 제공 항목이므로 실질 필수 |
| 직무 정보 | 체크박스(복수) | ✅ | 프론트엔드 / 백엔드 / 디자이너 / PM·PO / 마케터 / 창업가·대표 / 기타(주관식) |
| 만 19세 이상 확인 | 라디오 | ✅ | "네, 만 19세 이상의 성인입니다." |
| **팀장 / 팀원 분기** | 라디오 | ✅ | 팀원 → 여기서 제출 종료 / 팀장 → Section 02로 이동 |

### Section 02 — 팀을 대표하는 서비스 제출 (**팀장만**)
| 문항 | 타입 | 필수 | 상세 |
|---|---|---|---|
| 서비스 명 | 단답 | ✅ | 프로젝트 이름 |
| **서비스 파일 (또는 배포 URL)** | **파일 업로드** | ✅ | **파일 1개, 최대 100MB, 양식 제한 없음.** GitHub 등 링크 제출 시 프로젝트명과 함께 **word/pdf 파일에 링크 주소를 기입하여 업로드**. 파일명 규칙: `[NVIDIA 해커톤_팀명_프로젝트명]` |
| 해결하고자 했던 문제 (Problem Definition) | 장문 | ✅ | **300자 내외.** "이 서비스를 왜 만들었나요? 어떤 사용자의 어떤 불편함을 해결하기 위해 시작된 프로젝트인지 서술" |
| 서비스 소개 및 주요 기능 (Solution) | 장문 | ✅ | **500자 내외.** "문제 해결을 위해 어떤 기능을 구현했나요? 서비스의 핵심 로직과 사용자 흐름(User Flow)을 간략히 설명" |
| **활용한 핵심 기술 및 AI 모델 (Tech Stack)** | 장문 | ✅ | "적용된 NVIDIA의 AI 기술(**모델명, 라이브러리, 프레임워크 등**)과 **전체 기술 스택을 구체적으로 나열**" |
| 추가 제출 URL | 단답 | ❌ 선택 | |

> ⚠️ **폼에 GitHub ID 전용 입력란은 없다.** 개인정보 수집 고지에만 등장하므로, GitHub 링크/ID는 업로드하는 pdf·word 문서 안에 기재한다.

### Section 03 — 동의 및 일정 확인 (전원)
| 문항 | 필수 | 내용 |
|---|---|---|
| 개인정보 제3자 제공 내역 | ✅ (동의함 / 동의하지 않음) | 제공받는 자: **NVIDIA Korea** / 목적: 온라인 등록 대상자 확인 / 항목: 성함, 연락처, NVIDIA 계정 이메일 주소 / 파기: **2026-11-30** / **거부 시 참여 불가** |
| 전체 일정 안내 확인 | ✅ | "확인하였습니다" |
| 2차 마케팅 활용 동의 | ✅ (동의함 / 동의하지 않음) | 패스트캠퍼스·NVIDIA 마케팅 채널 2차 가공 활용 / 보유 1년 / **거부해도 참여·경품 지급에 제한 없음** |

---

## 5. 심사 기준 (공식 "프로젝트 채점 항목", 순서 그대로)

1. **NVIDIA Agent 기술 활용 심도**
2. **실용성, 산업가치, 혁신성**
3. **완성도**
4. **기타 — 커스터마이징 수준, 독창성 등**

`[INFERRED]` 1번이 첫 항목이고 Tech Stack 문항이 "구체적으로 나열"을 요구하므로, 가중치 상 NVIDIA 스택 활용 깊이가 결정적이다.

---

## 6. 시상 내역 (공식 슬라이드 3종)

### 🥇 우승 1팀
- **NVIDIA DGX Spark 1대**
- NVIDIA 공식 **GitHub Recipe 등재**
- NVIDIA **글로벌 기술 블로그 피처**

### 🏅 상위 5팀 (AI Day Seoul 진출)
- **AI Day Seoul 무대 발표**
- 수료 인증서
- **NVIDIA 1:1 Tech Clinic**

### 🎟 본선 10팀
- **팀당 최대 $1,000 NVIDIA Brev 크레딧 (L40S 1x)**
- NVIDIA Korea 및 커뮤니티 리더와 네트워킹
- NVIDIA 한정판 굿즈
- **패스트캠퍼스 AI 온라인 강의 무료 수강권**

---

## 7. 🧠 "Skill API"의 정체 — 반드시 읽을 것

**결론: "Skill API"라는 이름의 NVIDIA 공식 제품/엔드포인트는 존재하지 않는다.**
build.nvidia.com 전 메뉴, docs.nvidia.com/skills, docs.api.nvidia.com, llms.txt를 전수 확인한 결과이며,
주최측(패스트캠퍼스)의 표현으로 보인다. 실체는 서로 다른 두 가지다.

| 구분 | 실체 | 성격 | URL |
|---|---|---|---|
| **Skills** | NVIDIA-Verified **Agent Skills** (SKILL.md 형태 지침 패키지, 366개) | **REST API 아님.** CLI로 설치 | https://build.nvidia.com/skills |
| **NIM API** | OpenAI 호환 추론 API | 실제 HTTP API | `https://integrate.api.nvidia.com/v1` |

### 7-1. Agent Skills
공식 정의 (https://docs.nvidia.com/skills.md):
> "Agent skills are portable instruction sets that extend what an AI agent can do."

```bash
npx skills add NVIDIA/skills
npx skills add NVIDIA/skills --skill <name>
npx skills add NVIDIA/skills --skill <name> --agent claude-code
npx skills add NVIDIA/skills --skill <name> --agent codex
npx skills add NVIDIA/OpenShell        # OpenShell 전용 스킬(별도 리포)
npx skills update | list | check
```
- Anthropic Agent Skills 스펙 기반, Vercel `skills` CLI(github.com/vercel-labs/skills)가 전달 수단
- `skills` CLI **v1.5.16 이상** 필요. Claude Code에서는 `/reload-skills`
- 카테고리: AI and Machine Learning 187 / Physical AI 66 / Infrastructure 47 / Accelerated Computing 32 / Developer Tools 30
- 주요 스킬 예시: `rag-blueprint`, `aiq-research`, `aiq-deploy`, `cuopt-install`, `cuopt-routing-api-python`, `cuopt-server-api-python`, `cuopt-numerical-optimization-api`, `nemo-retriever`, `data-designer`, `rag-eval`, `rag-perf`, `accelerated-computing-cudf`, `cudaq-guide`, `deepstream-dev`, `omniverse-*`, `skill-card-generator`, `physical-ai-neural-reconstruction`
- 출처: https://build.nvidia.com/skills , https://build.nvidia.com/skills.md , https://github.com/NVIDIA/skills , https://docs.nvidia.com/skills , https://developer.nvidia.com/blog/nvidia-verified-agent-skills-provide-capability-governance-for-ai-agents/

### 7-2. NIM Inference API
`build.nvidia.com/llms.txt` 원문:
```
- Base URL: https://integrate.api.nvidia.com/v1
- Auth: Bearer token via `Authorization: Bearer $NVIDIA_API_KEY`
- API Key: Generate one at https://build.nvidia.com/settings
```
```bash
curl https://integrate.api.nvidia.com/v1/chat/completions \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -d '{"model":"nvidia/llama-3.1-70b-instruct","messages":[{"role":"user","content":"Hello"}]}'
```
- API 레퍼런스: https://docs.api.nvidia.com/ (`https://build.nvidia.com/docs`는 404)
- 무료: "All models offer a free trial tier with no credit card required."
- `[UNVERIFIED]` 구체적 크레딧 수치는 공식 문서에 없음
- ⚠️ 계정에 따라 API 키 생성이 막혀 수동 인증이 필요한 사례 보고됨 (2026-09-07, https://forums.developer.nvidia.com/t/access-to-nim-api-on-build-nvidia-com/382635) → **키 발급을 마감 직전으로 미루지 말 것**
- 홈 노출 무료 모델 (2026-09-22): `moonshotai/kimi-k3`, `deepseek-ai/deepseek-v4-pro-0813`, `nvidia/nemotron-3.5-lightning-30b-a3b`, `nvidia/nemotron-3-ultra-550b-a55b`

### 7-3. 실무 권장
**둘 다 쓴다.** 제출서 Tech Stack 칸에 사용한 **스킬 이름을 명시적으로 나열**하고, NIM 모델명과 엔드포인트를 함께 적는다. 이것이 심사 1번에 직접 대응된다.

`[ACTION]` 정확한 의도는 패스트캠퍼스 고객센터 문의로만 확정 가능.

---

## 8. NVIDIA 에이전트 스택 레퍼런스

```
Nemotron(모델) → NIM(서빙/API) → NVIDIA Agent Toolkit(오케스트레이션)
  → OpenShell(보안 샌드박스) → NemoClaw(번들 블루프린트) → DGX Spark / L40S(Brev)(하드웨어)
```

### 8-1. NVIDIA NemoClaw
- 정의: 자율(always-on) 에이전트용 **오픈 레퍼런스 스택 / 블루프린트 번들**. 모델 + 에이전트 하네스 + 보안 런타임을 한 번에 패키징. Apache-2.0, **alpha 프로젝트**
- 설치: `curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash`
  - Hermes: `... | NEMOCLAW_AGENT=hermes bash`
  - LangChain Deep Agents: `... | NEMOCLAW_AGENT=langchain-deepagents-code bash`
- 하네스 3종: **OpenClaw(기본), Hermes(Nous Research), LangChain Deep Agents Code**
- 기능: guided onboarding, managed inference, 모델 라우팅, 네트워크 정책, managed integrations, 스냅샷, 라이프사이클 운영(NemoClaw CLI)
- 하드웨어 없이 **Brev 무료 클라우드 VM 런처블**로 즉시 실행 가능
- URL: https://www.nvidia.com/en-us/ai/nemoclaw | https://github.com/NVIDIA/NemoClaw | https://docs.nvidia.com/nemoclaw/latest/ | https://github.com/NVIDIA/nemoclaw-community | https://www.nvidia.com/en-us/ai/build-a-claw/

### 8-2. NVIDIA OpenShell
- 정의: 자율 AI 에이전트를 **커널 레벨 격리 샌드박스**에서 실행하는 오픈소스 런타임. 선언적 **YAML 정책**으로 파일시스템/네트워크/프로세스/인퍼런스를 통제하고 모든 allow/deny를 **감사 로그**로 기록
- 설치: `curl -LsSf https://raw.githubusercontent.com/NVIDIA/OpenShell/main/install.sh | sh`
- 핵심 명령:
  ```bash
  openshell sandbox create -- <agent>
  openshell policy set <name> --policy file.yaml
  openshell provider create --type [type] --from-existing
  ```
- 3 pillar: ① 에이전트별 프로그래머블 샌드박스 ② 바이너리/경로/메서드 수준 정책 엔진 ③ Gateway(호스트 도달 전 액션 평가)
- 보호 계층 (2026-09-23 공식 문서 재확인):
  - **정적** — `filesystem_policy` · `landlock` · `process`: **샌드박스 생성 시 고정**, 바꾸려면 샌드박스 재생성
  - **동적** — `network_policies` · `network_middlewares`: **실행 중 핫리로드 가능** (출처: https://docs.nvidia.com/openshell/sandboxes/policies — "static sections ... locked at sandbox creation, and dynamic `network_policies` and `network_middlewares` sections that are hot-reloadable on a running sandbox")
  - **Inference** — 샌드박스는 `inference.local`만 보고 게이트웨이가 백엔드로 전달. **게이트웨이당 provider 1개·model 1개(단일 active backend)**, 변경 전파 **약 5초** → 요청 단위 모델 라우팅 용도 아님 (출처: https://docs.nvidia.com/openshell/sandboxes/inference-routing)
  - `network_middlewares`에는 `request_body_credential_rewrite: true` / `websocket_credential_rewrite: true` 옵션이 있어 **샌드박스에 API 키를 넣지 않고 게이트웨이가 credential을 주입**하는 구성이 가능 ("Supervisor Middleware"는 공식 명칭이 아님)
- 지원 에이전트: OpenCode, Codex, GitHub Copilot CLI(기본 이미지), OpenClaw/Hermes(NemoClaw 경유), Ollama, Pi(커뮤니티)
- ⚠️ PyPI `openshell` 패키지는 **Python SDK만** 제공(CLI 미포함)
- URL: https://build.nvidia.com/openshell | https://github.com/NVIDIA/OpenShell | https://docs.nvidia.com/openshell/latest/ | https://github.com/NVIDIA/OpenShell-Community
- DGX용: https://build.nvidia.com/spark/openshell , https://build.nvidia.com/station/openshell

> **NemoClaw vs OpenShell (공식 FAQ)**: NemoClaw = 모델·하네스·툴·런타임을 포함한 **전체 배포 패키지**, OpenShell = 그 안에서 에이전트의 파일/네트워크/자격증명/툴 접근을 강제하는 **보안 런타임**.

### 8-3. NVIDIA Nemotron (모델)
현행 최신은 **Nemotron 3** (하이브리드 Mamba-Transformer MoE, **1M 토큰 컨텍스트**, 멀티 환경 RL 포스트트레이닝, reasoning budget 제어).

| 모델 | 특징 | 용도 |
|---|---|---|
| Nemotron 3 Nano 30B A3B | Nemotron 2 Nano 대비 4x 처리량 | 특화 서브에이전트, 저비용 |
| Nemotron 3 Nano Omni 30B A3B | 비디오·오디오·이미지·텍스트 단일 모델 | 멀티모달 서브에이전트, 문서지능 |
| Nemotron 3 Super 120B A12B | 단일 데이터센터 GPU 배포 | 멀티에이전트 협업, 툴콜링 |
| Nemotron 3 Ultra 550B A55B | 프런티어급 추론, NVFP4 | 오케스트레이터, 딥리서치, 코드생성 |
| Nemotron 3.5 Lightning | 30B MoE / 3B active | always-on 에이전트의 빠른 태스크 |
| Nemotron Speech | ASR/TTS/S2S/full-duplex/NMT | 음성 에이전트 |

- 무료 경로: build.nvidia.com NIM API, OpenRouter 무료 티어(`:free`), Hugging Face 가중치, Ollama(`ollama.com/library/nemotron3`) / LM Studio / llama.cpp(GGUF) / Unsloth
- ⚠️ **Ultra 550B는 L40S 48GB 단일 GPU에 셀프호스팅 불가.** Ultra는 API, Nano/Super는 L40S 셀프호스팅하는 하이브리드 설계가 합리적
- URL: https://developer.nvidia.com/nemotron | https://www.nvidia.com/en-us/ai-data-science/foundation-models/nemotron/ | https://research.nvidia.com/labs/nemotron/Nemotron-3 | https://huggingface.co/collections/nvidia/nvidia-nemotron-v3 | 배포 쿡북 https://github.com/NVIDIA-NeMo/Nemotron/tree/main/usage-cookbook

### 8-4. NVIDIA NIM
- 정의: 모델 + 전체 추론 스택(CUDA/TensorRT/Triton/vLLM)을 컨테이너 하나로 패키징하고 **OpenAI 호환 API**로 노출하는 마이크로서비스
- 가장 빠른 길 = 호스팅 NIM API (build.nvidia.com 로그인 → 모델 페이지 → View Code → Generate API Key)
  ```python
  from openai import OpenAI
  client = OpenAI(base_url="https://integrate.api.nvidia.com/v1",
                  api_key=os.environ["NVIDIA_API_KEY"])
  ```
- 셀프호스팅은 NGC API Key 필요. **NVIDIA Developer Program 멤버는 연구/테스트 용도 무료**
- 도메인별 NIM: LLM/VLM, Riva ASR·TTS·NMT, NeMo Retriever(임베딩·리랭킹·OCR), NV-CLIP, NemoGuard(ContentSafety/TopicControl/JailbreakDetect), Visual GenAI, PhysicsNeMo
- URL: https://docs.nvidia.com/nim/index.html | https://docs.nvidia.com/nim/large-language-models/latest/introduction.html | https://www.nvidia.com/en-us/ai-data-science/products/nim-microservices/

### 8-5. NVIDIA (NeMo) Agent Toolkit
- 패키지명 `nvidia-nat`. 프레임워크 무관 통합 라이브러리
- `pip install "nvidia-nat[langchain]"` → `NVIDIA_API_KEY` 설정 → `workflow.yml` → `nat run --config_file workflow.yml --input "..."`
- 심사 어필 포인트: **MCP 클라이언트/서버 완전 지원**, **A2A 프로토콜**, **프로파일러(툴/에이전트 단위 토큰·레이턴시)**, 옵저버빌리티(LangSmith/Phoenix/Weave/Langfuse/OpenTelemetry), **내장 평가 시스템**, 전용 채팅 UI
- LangChain / LlamaIndex / CrewAI / Semantic Kernel / Google ADK와 공존
- URL: https://docs.nvidia.com/nemo/agent-toolkit/latest/index.html
- ※ 용어 주의: NemoClaw FAQ에서 "NVIDIA Agent Toolkit"은 Nemotron·BioNeMo·Omniverse·PhysicsNeMo·NeMo·OpenShell·AI-Q·NemoClaw를 아우르는 **상위 브랜드**로도 쓰인다

### 8-6. NVIDIA Brev + L40S
- Brev = 드라이버/CUDA/Python/Docker/Jupyter가 미리 세팅된 GPU 인스턴스를 즉시 띄우는 플랫폼. 핵심 개념 **Launchable**(하드웨어+소프트웨어+코드 원클릭 링크)
- 본선 10팀에게 주는 **$1,000 크레딧(L40S 1x)** = Brev 인스턴스 시간으로 소모
- NemoClaw/OpenShell 런처블은 **무료 Brev 계정만으로도 체험 가능**
- **L40S**: Ada Lovelace 데이터센터 GPU, **48GB GDDR6**
- URL: https://brev.nvidia.com/ | https://docs.nvidia.com/brev/latest/index.html | https://docs.nvidia.com/brev/latest/concepts/launchables | https://www.nvidia.com/en-us/data-center/l40s/

### 8-7. NVIDIA DGX Spark (우승 상품)
- **GB10 Grace Blackwell Superchip** 기반 데스크탑 에이전트 컴퓨터
- FP4 기준 최대 **1 petaFLOP**, **128GB 통합 메모리**, 최대 **200B 추론 / 70B 파인튜닝**. ConnectX 4대 연결 시 700B
- DGX OS 업데이트로 NemoClaw 설치 간소화 + 최대 1.9x 추론 속도 향상. NIM 포함 AI 소프트웨어 스택 프리인스톨
- URL: https://www.nvidia.com/en-us/products/workstations/dgx-spark/ | https://docs.nvidia.com/dgx/dgx-spark/index.html | https://build.nvidia.com/spark/nemoclaw

### 8-8. 조합하면 좋은 보조 기술
| 기술 | 한 줄 | 해커톤 쓸모 | URL |
|---|---|---|---|
| NeMo Guardrails | LLM 프로그래머블 가드레일 OSS(Colang DSL) | "완성도" 점수. input/output/retrieval/dialog rail | https://github.com/NVIDIA-NeMo/Guardrails , https://docs.nvidia.com/nemo/guardrails/ |
| NemoGuard NIM | ContentSafety(23개 카테고리)/TopicControl/JailbreakDetect | 저지연 가드레일 | https://docs.nvidia.com/nim/index.html |
| NeMo Retriever | 텍스트 임베딩·리랭킹·이미지 OCR·객체검출 NIM | 에이전틱 RAG | https://docs.nvidia.com/nim/nemo-retriever/text-embedding/latest/overview.html |
| Riva / Speech NIM | ASR·TTS·NMT | 음성 에이전트 데모(시각 임팩트 큼) | https://docs.nvidia.com/nim/speech/latest/index.html |
| cuOpt | GPU 가속 라우팅/스케줄링 최적화 | 물류·배차 에이전트. 과거 NeMo Agent Toolkit 해커톤 1위작 조합 | https://www.nvidia.com/en-us/ai-data-science/products/cuopt/ |
| Dynamo | 멀티노드 분산 추론 서빙 OSS | KV 캐시 병목 해소 | https://www.nvidia.com/en-us/ai/dynamo/ , https://github.com/ai-dynamo/dynamo |
| AI Blueprints | Multimodal RAG, Digital Human, Video Search, Data Flywheel, AI-Q | 즉시 fork 가능한 레퍼런스 | https://github.com/NVIDIA-AI-Blueprints |
| NeMo Switchyard | 지능형 모델 라우팅 | AI Day 세션 AD1010에서 언급됨 | `[UNVERIFIED]` 전용 문서 미확인 |

---

## 9. ⚠️ 확인 불가 / 리스크 목록 (사실로 승격 금지)

1. `[UNVERIFIED]` **"Skill API"의 정확한 의미** — NVIDIA 공식 명칭이 아님. 고객센터 확인 필요
2. `[UNVERIFIED]` **build.nvidia.com 무료 크레딧 수치** — 공식 FAQ는 "신용카드 없는 free trial tier"로만 명시. 흔히 인용되는 1,000/5,000/4,000 수치는 2024~25년 개발자 포럼 답변 근거이며 2026년 현재 정책 미확인
3. ⚠️ **NemoClaw는 alpha 프로젝트** — README에 이슈/PR 대응 best-effort 명시. 공식 고지: "as-is 제공, 자율 에이전트 실행에는 시스템 접근·데이터 노출·보안 취약점 리스크 내재". 본선 당일 단독 의존은 리스크
4. ⚠️ **NeMo Microservices는 2026-10-01 일몰 예정** → 후속은 NeMo Platform(https://github.com/NVIDIA-NeMo/nemo-platform). **제출서에 핵심 기술로 적지 말 것**
5. `[UNVERIFIED]` AI Day Seoul 세션 카탈로그에 **해커톤 쇼케이스 세션 미등재** (21개 세션 기준, 추가 예정)
6. `[UNVERIFIED]` **수상 5팀의 AI Day Seoul 참가비 처리 방식** 미공지 (워크숍 $199/$500 유료)
7. `[UNVERIFIED]` Brev 학생/프로모 크레딧 공식 프로그램 존재 여부
8. `[UNVERIFIED]` DLI 코스의 "persistent skill libraries" 실제 내용 — 수강 전 확인 불가
9. ⚠️ **`nemoclaw.run`, `nemoclawai.io`, `nvidia-openshell.com` 등은 NVIDIA 공식 도메인이 아님** (서드파티/SEO 사이트). 인용 금지
10. `[UNVERIFIED]` 폼상 "이메일 주소 (NVIDIA 계정 아이디)"가 required=0으로 설정된 것이 의도적인지 실수인지 불명

---

## 10. 실행 플랜 (D-6 기준, 2026-09-22 → 09-28)

### D-6 (즉시)
- [ ] **NVIDIA 계정 생성 + API 키 발급** (https://build.nvidia.com/settings) — 계정에 따라 수동 인증 필요 사례 있음, 최우선
- [ ] 팀원 전원 GitHub ID 취합
- [ ] **팀명 문자열 확정 후 팀 채널에 고정** (띄어쓰기 포함, 복붙용)
- [ ] DLI 강의 "Securing Agents with NemoClaw and OpenShell" 수강 시작 (무료 4h)
- [ ] 팀원 생년 확인 (2006년생 이전인지)

### D-5 ~ D-3
- [ ] Brev 무료 계정으로 NemoClaw 런처블 기동 → 스택 동작 검증 (로컬 설치보다 빠름)
- [ ] 주제 확정 → OpenShell 정책 YAML 포함 최소 동작 데모 구현
- [ ] NVIDIA Agent Skills 설치/자작 (`npx skills add NVIDIA/skills --skill <name>`)
- [ ] Agent Toolkit 프로파일러로 **정량 지표 수집** (툴콜 성공률 / 레이턴시 / 토큰) → 심사 3번 "완성도" 근거

### D-2 ~ D-1
- [ ] GitHub 리포 public 전환 + README 정리 (아키텍처 다이어그램, 재현 절차)
- [ ] 제출 문서 작성 → 파일명 `[NVIDIA 해커톤_팀명_프로젝트명].pdf`
- [ ] Problem 300자 / Solution 500자 / Tech Stack 작성
- [ ] **팀장 먼저 제출 → 완료 스크린샷 공유 → 팀원 전원 제출 확인**

### Tech Stack 칸 작성 템플릿
```
모델        : Nemotron 3 Nano 30B A3B (NIM 셀프호스팅) + Nemotron 3 Ultra 550B
              (integrate.api.nvidia.com, 플래너/오케스트레이터)
오케스트레이션: NVIDIA Agent Toolkit(nvidia-nat) + MCP 서버 N개 + A2A 프로토콜
런타임 보안  : NVIDIA OpenShell 샌드박스 + 정책 YAML(파일/네트워크/인퍼런스 rail) + 감사 로그
번들        : NVIDIA NemoClaw (OpenClaw 하네스)
안전성       : NeMo Guardrails + NemoGuard ContentSafety NIM
검색        : NeMo Retriever 임베딩/리랭킹 NIM
Agent Skills: npx skills add NVIDIA/skills --skill <사용한 스킬명 나열>
인프라       : NVIDIA Brev L40S 1x → DGX Spark 로컬 배포 시나리오
측정        : Agent Toolkit 프로파일러/평가 시스템 기반 정량 지표
```

`[INFERRED]` 하드웨어 스토리 정합성: Brev L40S에서 개발 → DGX Spark 로컬 배포 시나리오를 명시하면 우승 상품(DGX Spark)과 내러티브가 맞는다.

---

## 11. 주요 링크 모음

**대회**
- 공식 페이지 https://fastcampus.co.kr/NVIDIA_hackathon
- 신청 폼 https://docs.google.com/forms/d/e/1FAIpQLScyZ5GYYaCOycNUzXVUTenliEUmSEIdXelVdYphvMvLeLuiHA/viewform
- 교육 미션(DLI, 무료) https://learn.nvidia.com/courses/course-detail?course_id=course-v1:DLI+S-FX-43+V1
- 고객센터 https://day1fastcampussupport.zendesk.com/hc/ko
- AI Day Seoul 2026 https://www.nvidia.com/ko-kr/ai-days/ | 세션 카탈로그 https://www.nvidia.com/ko-kr/ai-days/session-catalog/

**개발**
- API 카탈로그 https://build.nvidia.com/ | API 키 https://build.nvidia.com/settings | 스킬 https://build.nvidia.com/skills
- API 레퍼런스 https://docs.api.nvidia.com/
- NemoClaw https://www.nvidia.com/en-us/ai/nemoclaw | https://github.com/NVIDIA/NemoClaw | https://docs.nvidia.com/nemoclaw/latest/
- Build-a-Claw 리소스 허브 https://www.nvidia.com/en-us/ai/build-a-claw/
- OpenShell https://build.nvidia.com/openshell | https://github.com/NVIDIA/OpenShell | https://docs.nvidia.com/openshell/latest/
- Agent Toolkit https://docs.nvidia.com/nemo/agent-toolkit/latest/index.html
- Nemotron https://developer.nvidia.com/nemotron
- Brev https://brev.nvidia.com/ | https://docs.nvidia.com/brev/latest/index.html
- Agentic AI 학습 경로 https://developer.nvidia.com/topics/ai/agentic-ai-learning-path

---

*조사 방법: 공식 페이지 이미지 OCR, 구글 폼 전 섹션 직접 열람 및 `FB_PUBLIC_LOAD_DATA_` 구조 추출, NVIDIA 공식 문서/카탈로그 직접 확인. 블로그·커뮤니티 출처는 배제.*
*폼 구조 확인 과정에서 입력한 임시값은 "양식 지우기"로 전량 삭제했으며, 제출된 응답은 없음.*
