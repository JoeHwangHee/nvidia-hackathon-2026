---
title: "IDEA REAL-WORLD USE CASES — 23개 후보의 실활용 조사 보고서"
doc_type: real_world_use_case_review
version: 1.0
created_at: 2026-09-23T09:30+09:00
deadline: 2026-09-28T23:59+09:00
scope: "공개 웹·공식 문서·공개 보고서·기업/오픈소스 1차 자료만 사용. 로그인·개인 탭 열람·게시·구매·계정 변경 없음."
method: "서브에이전트 5개 병렬 조사(클러스터별) + 결정적 사실 8건 직접 재확인(원문 fetch). ChatGPT 판단·미검증 모델 주장은 근거로 쓰지 않음."
tag_rules:
  "[사실]": "인용한 페이지가 직접 뒷받침"
  "[추론]": "조사자의 해석·유추"
  "[미확인]": "찾지 못했거나 확인 불가"
  "[커뮤니티]": "포럼·커뮤니티 보고. 신호로만 사용, 사실로 승격 금지"
  "[벤더주장]": "벤더 자체 페이지의 성과 주장. 제3자 검증 없음"
companion_docs:
  - IDEA_EXPANSION_CHATGPT_REVIEW.md   # 후보 정의의 원천. 본 문서는 이를 수정하지 않음
  - SCORING_GOLDEN_RULE.md
  - DATA_AND_SKILL_INVENTORY.md
---

# IDEA REAL-WORLD USE CASES

> **READ THIS FIRST (for agents)**
> - 이 문서는 "점수"가 아니라 **"실제로 누가, 어떤 상황에서, 무엇을 하게 되는가"와 "지금 만들 가치가 있는가"**를 다룬다.
> - 후보 ID(I-01~I-20, N-A~N-C)와 수정판 정의는 `IDEA_EXPANSION_CHATGPT_REVIEW.md` §2·§4를 따른다.
> - 섹션 5의 점수는 **조사 기반 우선순위**이며 대회 공식 점수가 아니다. 섹션 6의 미확인 항목을 사실로 승격하지 말 것.
> - 모든 외부 사실 뒤에 URL을 붙였다. URL이 없는 문장은 [추론]이다.

---

## 0. 결론 요약 (비기술자용)

**한 줄 결론**: 23개 후보 중 "오늘 실제 고객이 존재하고, 기존 제품이 아직 비워둔 자리가 있으며, 6일 안에 그 자리를 숫자로 보여줄 수 있는" 것은 **보안·개발운영(DevOps) 계열 5개**로 좁혀진다. 공공·제조 계열은 사회적 가치는 크지만 **기준 데이터(현행 배정·운행·라벨 영상)가 공개되어 있지 않아** 6일 안에 "실제 개선"을 증명할 수 없고, 데이터·도메인 계열 4개는 이미 상용 제품이 자리를 차지했거나(NeMo Switchyard, CODIT, 필톡·심평원) 정답 라벨이 없다.

### 지금 실제로 쓸 만한 TOP 5

| 순위 | 후보 | 한 문장 (누가 무엇을 하게 되는가) | 추천 팀 규모 | 가장 큰 고객/도입 리스크 |
|---|---|---|---|---|
| 1 | **A안 = I-03 MCP 공급망 감사관 (+I-01 최소권한 합성, +N-C 무비밀 커넥터)** | AppSec/플랫폼팀이 새 MCP 서버를 붙이기 전에 샌드박스에서 "실제로 무엇을 하는지" 보고, 최소권한 정책 파일을 받아 승인한다 | 3인 (백엔드 2 + 평가/데이터 1) | Snyk(Invariant mcp-scan)·Cisco·Docker MCP Gateway가 이미 정적 스캔·격리를 제공. **"동적 감사 → 정책 자동 산출"이 실제 다르다는 것을 숫자로 보여주지 못하면 기존 도구의 부속 기능으로 보임** |
| 2 | **I-11 Agent CI (실제 툴 재실행 회귀 게이트)** | 에이전트 개발팀이 PR마다 실제 툴을 격리 샌드박스에서 다시 돌려 "코드는 통과했는데 행동이 깨진" 배포를 막는다 | 2인 | Promptfoo·LangSmith가 CI 카테고리를 선점. 골든 태스크·픽스처 API 제작 비용이 도입의 실제 병목 |
| 3 | **I-07 안전한 자율 CVE 트리아지** | 보안팀이 매일 수백 건 CVE 중 "우리 코드에서 실제로 호출되는 것"만 받아본다. 에이전트는 읽기만 하고 리포트 발송은 사람이 승인 | 2~3인 (보안 경험 1인 필요) | Endor Labs·Snyk가 함수 수준 도달가능성 분석을 이미 판매. 상용 도구 대비 정밀도를 20~30개 픽스처로는 증명하기 어려움 |
| 4 | **B안 = I-13 Skill CI/Compiler (+I-11)** | 코딩 에이전트 운영팀이 반복 실패를 SKILL.md로 자동 컴파일하고, 처음 보는 테스트를 통과한 스킬만 라이브러리에 올린다 | 2인 | Agent Skills 표준이 2025-10에 나온 신생 규격. 자동 생성 스킬은 그 자체가 공급망 공격 표면(Datadog: OpenClaw 생태계 악성 스킬 230개 보고) |
| 5 | **N-A 폭주 에이전트 서킷브레이커** | 에이전트를 무인 운영하는 팀이 무한 재시도·루프 발생 시 자동으로 멈추고 외부 엔드포인트를 네트워크 수준에서 끊는다 | 1~2인 (다른 안의 부품으로 권장) | LiteLLM·OpenAI 프로젝트 예산 한도가 "멈추기"는 이미 제공. 차별점은 커널 egress 차단 하나뿐이라 단독 제품으로는 얇음 |

6위권: **I-15 A2A 임시 권한 리스 브로커**(4~5인, 멀티에이전트 조직 대상. HashiCorp Vault·Auth0가 토큰 계층에서 동일 개념을 제공하므로 "네트워크 계층 임대"만이 새로움), **I-17 다양성 실패 탐색**(AI 정부24가 3개월간 2,848만 명이 이용한 실운영 맥락이 있어 공공 에이전트 운영 조직에겐 현실적. 단독보다 평가층 부품).

### 최우선 3 / 보류 3 / 가장 중요한 리스크

| 구분 | 후보 | 이유 (요약) |
|---|---|---|
| **최우선 1** | A안 (I-03 코어) | 실제 사고(GitHub MCP 비공개 저장소 유출 시연, 2025-05) + 공개 벤치마크(MCPTox) + 구매자(AppSec) + 시장 검증(Snyk의 Invariant 인수)이 모두 존재 |
| **최우선 2** | I-11 | 개발자 페인이 가장 보편적이고, "실제 툴을 부작용 없이 재실행"은 기존 CI 도구가 비워둔 자리 |
| **최우선 3** | I-07 | CVE 폭증(NIST: 2026년 6만 건 전망) + NVD 백로그(2만 7천 건 이상)로 사람이 못 보는 상황이 구조화. 단 상용 대체재 강함 |
| **보류 1** | I-10 인퍼런스 거버너 | NVIDIA가 LLM Router 블루프린트 후속으로 **NeMo Switchyard**를 출시(실행 단계 인지 라우팅, Terminal-Bench 벤치마크 공개). 그 위의 정책 계층으로 재정의하지 않으면 재발명 |
| **보류 2** | I-12 실거래가 이상거래 | 국토부가 반기마다 수백~천 건을 적발하지만 **건별 라벨은 비공개**. 개인 거래정보·명예훼손 리스크 |
| **보류 3** | I-06 폐기물 배차 | 실제 수거 경로·차량 데이터가 공개돼 있지 않음(환경부 RFID 종량기 설치 현황만 공개). 합성 기준선으로는 개선을 증명할 수 없음 |
| **가장 중요한 리스크** | 전체 | **"애플리케이션 계층 대체재는 거의 다 있다."** 최소권한(AWS IAM Access Analyzer), 임시 자격증명(Vault·Auth0·Entra Agent ID), 예산 캡(LiteLLM), MCP 스캔(mcp-scan), 라우팅(Switchyard)이 모두 존재한다. 우리 후보들의 신규성은 대부분 **"같은 일을 OpenShell 커널 계층에서 강제한다"** 한 가지에 있다. 이 차이가 고객에게 실제 가치인지(=공격이 앱 계층 방어를 뚫었을 때만 드러남)를 데모에서 보여주지 못하면 전부 "기존 제품의 하위 기능"으로 보인다. 둘째 리스크는 도입 측: Gartner는 에이전트 프로젝트의 40% 이상이 비용·가치 불명·리스크 통제 미비로 2027년 말까지 취소될 것으로 예측한다 (https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027) |

### 이 보고서가 하지 않는 것
- 대회 채점 예측을 하지 않는다 (`SCORING_GOLDEN_RULE.md`·`IDEA_EXPANSION_CHATGPT_REVIEW.md` 담당).
- 벤더 성과 수치(불량률 67%↓ 등)를 검증하지 않는다. `[벤더주장]`으로 표시만 한다.
- 6일 안에 만들 수 있는지의 기술 판단은 ⑤에서 "MVP가 증명하는 범위"로만 다룬다.

---

## 1. 조사 방법과 표기

| 항목 | 내용 |
|---|---|
| 자료 범위 | 공식 문서(docs.nvidia.com, docs.aws.amazon.com, learn.microsoft.com 등), 정부 사이트(molit.go.kr, mois.go.kr, data.seoul.go.kr, open.law.go.kr, nist.gov), 벤더 공식 페이지·보도자료, 논문(arXiv/AAAI/Nature Medicine), 공개 GitHub 리포, 주요 언론(NVIDIA 블로그, 전자신문, 조선비즈, BusinessWire) |
| 배제 | 로그인 필요 자료, 개인 브라우저 탭, SEO 유사 도메인(nemoclaw.run 등), ChatGPT 등 모델의 미검증 주장 |
| 절차 | ① 23개 후보를 5개 클러스터로 나눠 병렬 조사 → ② 의사결정에 결정적인 사실 8건(NeMo Switchyard, Docker Sandboxes, Snyk-Invariant, MCP 규모, Gartner, OWASP Agentic Top 10, NVD 백로그, 국가법령 API 승인)은 원문을 직접 재확인 → ③ 커뮤니티·2차 블로그 근거는 `[커뮤니티]`로 격리 |
| 한계 | 벤더 페이지의 고객 성과는 검증 불가. 한국 국내 사례는 영문 자료보다 적게 확인됨. "직접 사례 미발견"은 "존재하지 않음"이 아니라 "이 조사 범위에서 찾지 못함" |

각 후보 카드의 6개 항목: ① 현실 사용자/구매자와 발생 상황 ② end-to-end 사용 시나리오(입력→에이전트 행동→사람/시스템 결과) ③ 오늘의 대체 방식과 불편 ④ 지금 유용한 이유/도입 장벽 ⑤ 6일 MVP가 증명하는 범위 ⑥ 판정(지금 추진 / 다른 후보의 부품 / 본선용 / 보류·폐기).

---

## 2. 시장 배경 신호 4가지 (모든 후보에 공통 적용)

1. **도입 리스크**: Gartner는 2025-06-25 "에이전틱 AI 프로젝트의 40% 이상이 비용 상승·불명확한 사업가치·부적절한 리스크 통제로 2027년 말까지 취소될 것"이라 예측하고, 수천 벤더 중 "진짜"는 약 130개뿐이라고 추정했다 [사실] (https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027). 같은 Gartner가 2025-08-26에는 "2026년 말까지 기업 앱의 40%가 태스크 특화 에이전트를 탑재(2025년 5% 미만)"라고 전망했다 [사실] (https://www.gartner.com/en/newsroom/press-releases/2025-08-26-gartner-predicts-40-percent-of-enterprise-apps-will-feature-task-specific-ai-agents-by-2026-up-from-less-than-5-percent-in-2025). → **"리스크 통제"가 취소 사유 3개 중 하나**라는 점이 보안 계열 후보의 존재 이유다 [추론].
2. **위협 분류 표준화**: OWASP가 2025-12-10 "Top 10 for Agentic Applications 2026"(ASI01 Agent Goal Hijack ~ ASI10 Rogue Agents)을 100명 이상의 전문가와 함께 발표했다 [사실] (https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/). ASI03 신원·권한 남용, ASI04 에이전트 공급망, ASI05 예상치 못한 코드 실행, ASI08 연쇄 장애가 각각 I-01/I-15, I-03/I-13, I-16, N-A와 대응한다 [추론].
3. **MCP 규모**: Anthropic은 2025-12-09 MCP를 Linux Foundation 산하 Agentic AI Foundation에 기부하며 "활성 공개 MCP 서버 1만 개 이상, 월 SDK 다운로드 9,700만 회 이상, ChatGPT·Cursor·Gemini·Copilot·VS Code 채택"을 공식 발표했다 [사실] (https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation , https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation). → I-03·N-C의 잠재 고객 수요 기반.
4. **격리 실행의 상품화**: Docker가 2026-01-30 코딩 에이전트용 microVM 샌드박스 "Docker Sandboxes"(네트워크 허용/차단, 파일시스템 정책, MCP 게이트웨이 포함)를 출시했고 [사실] (https://www.docker.com/products/docker-sandboxes , https://docs.docker.com/ai/sandboxes), Snyk는 2025-06-24 MCP 스캐너·에이전트 가드레일을 만든 Invariant Labs를 인수했다 [사실] (https://snyk.io/news/snyk-acquires-invariant-labs-to-accelerate-agentic-ai-security-innovation/). → "에이전트 격리·감사"는 이미 대형 벤더의 제품 영역이며, OpenShell 기반 후보는 이들과 나란히 놓고 비교당한다 [추론].

---

## 3. 23개 후보 실활용 카드

### 3-1. 보안·공급망 계열

#### I-03 MCP Zero-Trust Supply-Chain Auditor
① **사용자/구매자·상황**: 사내 AI 플랫폼팀·AppSec팀. 개발자들이 GitHub·Slack·DB용 MCP 서버를 수십 개 붙이려 하는데 "이 서버의 tool description에 숨은 지시가 없는지, 실제로 어떤 파일·네트워크를 건드리는지" 검토할 인력이 없는 상황 [추론]. 벤더(MCP 서버 배포자)도 "우리 서버는 안전하다"는 증거가 필요하다 [추론]. Docker는 이미 서명·SBOM이 붙은 "MCP Catalog"로 이 신뢰 문제를 겨냥한다 [사실] (https://docs.docker.com/ai/mcp-catalog-and-toolkit/catalog).
② **시나리오**: 개발자가 `admission request: github-mcp@1.4`를 제출 → 에이전트가 OpenShell 샌드박스에 서버를 설치하고 `tools/list`를 정적 검사(MCPTox 스타일 포이즈닝 패턴) → 픽스처 태스크를 실행하며 파일·네트워크 접근을 감사 로그로 기록 → "선언: repo 읽기 / 관측: `~/.ssh` 읽기 시도"를 diff → 최소권한 `policy.yaml` + 리스크 리포트 생성 → AppSec 담당자가 승인/거부, 승인 시 그 정책으로만 배포.
③ **오늘의 대체**: (a) Invariant/Snyk **mcp-scan**: 정적 스캔 + tool pinning(rug pull 탐지) + 크로스오리진 shadowing 탐지 [사실] (https://invariantlabs.ai/blog/introducing-mcp-scan) — 런타임 행동은 보지 않음 [추론]. (b) **Cisco mcp-scanner**: YARA + LLM 분석 + VirusTotal, PyPI 패키지는 Docker 샌드박스에서 행동 분석 [사실] (https://github.com/cisco-ai-defense/mcp-scanner) — 정책 산출 없음. (c) **Docker MCP Gateway**: 컨테이너 격리 + 로깅 + 자격증명 주입 [사실] (https://docs.docker.com/ai/mcp-catalog-and-toolkit/mcp-gateway) — 격리는 하지만 "관측→정책 자동 생성" 루프는 없음 [추론]. 불편: 세 도구 모두 "무엇을 허용할지"는 여전히 사람이 쓴다.
④ **유용/장벽**: 유용 — Invariant Labs가 2025-04-01 Cursor·OpenAI·Zapier 클라이언트의 tool poisoning 취약성을 공개하고 [사실] (https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks), 2025-05-26 GitHub MCP 서버가 공개 이슈의 인젝션으로 비공개 저장소 정보를 공개 PR로 유출하는 시연을 발표 [사실] (https://invariantlabs.ai/blog/mcp-github-vulnerability); MCPTox(AAAI 2026)는 실제 MCP 서버 45개·툴 353개 기반 1,348개 케이스에서 20개 LLM 에이전트의 최고 거부율이 3% 미만이라고 보고 [사실] (https://arxiv.org/abs/2508.14925); OWASP MCP Top 10에 "Tool Poisoning"·"Shadow MCP Servers"가 등재 [사실] (https://owasp.org/www-project-mcp-top-10). 장벽 — MCP 스펙 변동(2025-11-25 스펙에 서버 신원·비동기·무상태 추가 [사실] https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation), 실제 서버는 API 키·OAuth·DB가 필요해 동적 실행이 어려움 [추론], 오탐 시 정상 서버를 막는 비용 [추론].
⑤ **6일 MVP가 증명하는 범위**: MCPTox 정적 벤치마크에서의 탐지율(Recall@1% FPR)과, 재현 가능한 서버 5~10개에서 "선언 vs 관측 diff → 정책 생성 → 정책 적용 후 정상 태스크 유지율"까지. **증명하지 못하는 것**: 실제 기업의 수백 개 서버에 대한 오탐률, OAuth가 필요한 서버의 동적 감사, 스펙 변경 추종.
⑥ **판정: 지금 추진 (A안 코어).** 사고·벤치마크·구매자·시장 검증이 모두 있고 OpenShell 없이는 동적 감사가 성립하지 않는다. 단 "동적 감사→정책" 차별화를 mcp-scan/Docker Gateway와 나란히 놓은 비교표로 증명해야 한다.

#### N-C Zero-Secret Agent Connector
① **사용자/구매자·상황**: SaaS(GitHub·Jira·Slack)를 호출하는 에이전트를 배포하는 팀의 보안 담당자. `GITHUB_TOKEN`이 에이전트 프로세스 환경변수에 있으면 인젝션 한 번에 유출된다는 위협이 표준 패턴으로 인식됨 [사실]: agentgateway(Solo.io)는 2026-07-27 "에이전트에 실제 자격증명을 주지 않고 egress 시점에 게이트웨이가 주입"하는 CB4A 모델을 문서화하면서 "브로커 자체가 침해되면 치명적"이라는 위협모델도 명시 (https://agentgateway.dev/blog/2026-07-27-credential-injection-ai-agent-egress-cb4a/).
② **시나리오**: 에이전트가 `POST api.github.com/repos/x/issues` 호출 → OpenShell 네트워크 정책이 host·method·path를 검사 → `network_middlewares`가 요청 바디를 검사/교정 → `request_body_credential_rewrite`로 게이트웨이가 토큰 주입 [사실, 옵션 존재] (https://docs.nvidia.com/openshell/sandboxes/policies) → 샌드박스 안에는 토큰이 존재한 적 없음 → 인젝션이 "환경변수를 읽어 보내라"고 해도 읽을 것이 없음.
③ **오늘의 대체**: Arcade.dev("credentials never touch the LLM or client application") [사실] (https://www.arcade.dev/get-started/authorization/), Microsoft Entra Agent ID("에이전트 신원은 자체 자격증명을 갖지 않고 연합 자격증명으로만 인증") [사실] (https://learn.microsoft.com/en-us/entra/agent-id/agent-identities), HashiCorp Vault 네이티브 AI 에이전트 지원(2026-05-12, 요청 단위 임시 인가) [사실] (https://www.hashicorp.com/en/blog/announcing-native-ai-agent-support-in-hashicorp-vault), 1Password Agentic AI(2025-04, ".env 파일 제거") [사실] (https://1password.com/press/2025/april/agentic-ai), Okta Agent Gateway [사실] (https://www.okta.com/products/govern-ai-agent-identity). 불편: 전부 애플리케이션/IdP 계층 프록시라 **에이전트 프로세스가 프록시를 우회해 직접 외부로 나가는 것**을 OS 계층에서 막지는 않는다 [추론].
④ **유용/장벽**: 유용 — Microsoft·HashiCorp·Okta·1Password가 2025~2026년에 동일 결론("에이전트는 비밀을 가지면 안 된다")에 도달한 시장 컨센서스 [사실, 위 URL]. 장벽 — 기존 IdP와의 통합, MCP 클라이언트별 인증 흐름 차이, "정말 샌드박스에 비밀이 0인가"를 감사로 증명해야 하는 신뢰 문제 [추론]. 커널 계층 차이는 **앱 계층 프록시가 우회당했을 때만** 가치가 드러난다 [추론].
⑤ **6일 MVP**: mock SaaS 1개, 정상 요청 30 + 탈취 프롬프트 30에서 env-secret vs zero-secret의 유출 성공률·정상 성공률·미들웨어 p95 지연. 증명하지 못하는 것: 실제 OAuth 흐름, 다중 SaaS, 브로커 침해 시나리오.
⑥ **판정: 지금 추진 — 단 A안의 부품으로.** 단독 제품으로는 Arcade·Vault·Entra와 메시지가 같아 얇다. A안에 넣으면 "감사한 서버를 비밀 없이 운영한다"는 완결된 스토리가 된다.

#### I-14 Deployment Attestation Gate
① **사용자/구매자·상황**: 규제산업(금융 등) CISO·AI 거버넌스팀. NIST AI RMF [사실] (https://www.nist.gov/itl/ai-risk-management-framework)·ISO/IEC 42001(2023-12) [사실] (https://www.iso.org/standard/42001)이 배포 전 위험평가를 요구하는데 에이전트용 표준 시험이 없는 상황 [추론].
② **시나리오**: 배포 후보 에이전트 제출 → OpenShell 안에서 인젝션 스위트(AgentDojo) + 툴 포이즈닝(MCPTox) + 최소권한 시험 → 프로파일(benign utility, injection ASR, poisoning ASR, privilege violations) + 서명된 attestation.json + 최소권한 정책 → 운영 게이트웨이가 attestation 없는 배포를 거부 → 런타임 위반 누적 시 철회.
③ **오늘의 대체**: UK AISI **Inspect + Sandboxing Toolkit**(정부 평가 프레임워크, tooling/host/network 3축 격리) [사실] (https://www.aisi.gov.uk/blog/the-inspect-sandboxing-toolkit-scalable-and-secure-ai-agent-evaluations), HiddenLayer AI Attack Simulation·Agent Harness Security [사실] (https://www.hiddenlayer.com/solutions/agentic-mcp-security), Lakera AI Red Teaming(NVIDIA NeMo Agent Toolkit 레드티밍 사례 게시) [사실] (https://www.lakera.ai/ai-red-teaming-services), Promptfoo red team(OSS) [사실] (https://www.promptfoo.dev/docs/red-team), Cisco의 Robust Intelligence 인수(2024-08) [사실] (https://blogs.cisco.com/news/fortifying-the-future-of-security-for-ai-cisco-announces-intent-to-acquire-robust-intelligence). 불편: 대부분 벤더 리포트/단일 점수로 끝나고, "정책 파일 + 서명된 증명 + 런타임 철회"의 라이프사이클 연동은 공개 자료에서 확인되지 않음 [미확인].
④ **유용/장벽**: 유용 — 규제 프레임워크가 이미 배포 전 평가를 요구. 장벽 — 서명의 신뢰 루트(누가 인증기관인가), 서로 다른 벤치마크 점수를 하나로 합칠 통계적 근거 없음, 공격 패턴 진화에 따른 스위트 유지보수 [추론].
⑤ **6일 MVP**: 에이전트 1개·시험 스위트 축소판·attestation.json 발급까지. 증명하지 못하는 것: 시험 통과가 실제 사고 감소로 이어지는지(인증셋/hold-out 분리 필요), 다중 하네스 비교.
⑥ **판정: 본선용.** I-01+I-02+I-03의 플랫폼화라 예선 6일엔 각 증거가 얕아진다. A안이 완성된 뒤의 제품명으로 적합.

#### I-18 Agent Risk Triage Score
① **사용자/구매자·상황**: 수십~수백 개 에이전트 배포 후보 중 어느 것부터 보안 리뷰할지 정해야 하는 AppSec팀 [추론].
② **시나리오**: 정책 표면(허용 도메인·경로·바이너리 수)·툴 목록·모델·하네스 → 점수 → "이 5개부터 리뷰" 우선순위 → 리뷰 후 실제 실패 여부로 점수 보정.
③ **오늘의 대체**: 정성 체크리스트. 학술 프레임워크 AURA(2025-10, 에이전트 자율성 리스크 점수) [사실] (https://arxiv.org/abs/2510.15739), TrustX ARC(2026-07, 12차원 루브릭) [사실] (https://arxiv.org/html/2607.09586v1). Lakera "Agent Risk Assessment" 카테고리는 존재하나 예측 모델인지 체크리스트인지 미확인 [미확인] (https://docs.lakera.ai/docs/agent-security/risk-assessment).
④ **유용/장벽**: 유용 — 논문이 2025~2026년 연달아 나온다는 것은 미해결이면서 수요가 있다는 신호 [추론]. 장벽 — "보지 못한 공격군에 대한 취약도 예측"은 일반화 보장이 약하고 정답 라벨(실제 실패)이 없음 [추론].
⑤ **6일 MVP**: 정책 변형 30~50개 에이전트에서 절반 공격셋으로 점수를 만들고 나머지 공격군에서 티어별 실패율 분리를 확인. 증명하지 못하는 것: 실제 조직의 에이전트에 대한 예측력.
⑥ **판정: 보류·폐기 (I-14의 서브시스템으로만).** 직접 상용/운영 사례 미발견. 독립 프로젝트로는 "합성 에이전트로 합성 리스크 점수"라는 자기참조가 남는다.

### 3-2. 권한·런타임 통제 계열

#### I-01 Least-Privilege Policy Synthesizer
① **사용자/구매자·상황**: OpenShell/NemoClaw 같은 샌드박스에 에이전트를 올리는 플랫폼팀. 정책 YAML을 손으로 쓰다 보니 "무엇을 건드리는지 모른 채 넓게 허용"하게 되는 상황. 이 패턴은 클라우드 IAM에서 이미 반복됐다 [사실]: AWS IAM Access Analyzer는 CloudTrail 활동을 분석해 실제 사용된 권한만 담은 정책을 생성하되, 관찰 기간에 없던 정상 경로를 놓칠 수 있음을 공식 문서가 명시 (https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-policy-generation.html).
② **시나리오**: 대상 에이전트(예: 코드 유지보수 에이전트)를 OpenShell에서 정상 태스크 20건 실행 → 감사 로그에서 접근 패턴 수집 → LLM이 최소권한 YAML 초안 → 레드팀 공격 30건 주입 → 뚫리면 수정 → held-out 정상 태스크 10건으로 기능 보존 확인 → 플랫폼팀이 정책을 리뷰·배포.
③ **오늘의 대체**: 수작업 YAML; Docker Sandboxes(microVM, 네트워크·파일 정책은 관리자가 수동 설정) [사실] (https://www.docker.com/products/docker-sandboxes); AWS Bedrock AgentCore Policy(Cedar 정책을 자연어로 저작·검증, 로그 기반 생성은 아님) [사실] (https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html); Claude Code 샌드박스(Seatbelt/bubblewrap, 수동 설정) [사실] (https://code.claude.com/docs/en/sandboxing); K8s audit2rbac(감사 로그→RBAC 생성). 불편: 관찰 기반 자동 생성은 클라우드 IAM·K8s에는 있지만 **에이전트 샌드박스(파일+네트워크+프로세스)에는 없다** [추론].
④ **유용/장벽**: 유용 — OWASP Agentic Top 10이 권한 남용(ASI03)을 명문화 [사실] (https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/). 장벽 — 관찰 기간이 짧으면 드문 정상 경로 누락(AWS도 인정), 레드팀 커버리지의 완전성 증명 불가, OpenShell 자체의 도입 규모가 아직 작음 [추론].
⑤ **6일 MVP**: 워크로드 1종에서 권한 표면 감소%·공격 ASR·held-out 정상 성공률. 증명하지 못하는 것: 다양한 워크로드 일반화, 장기 운영 중 드리프트.
⑥ **판정: 지금 추진 — A안의 부품.** 단독으로는 "우리가 만든 공격을 우리가 막았다"는 순환에 갇히지만, I-03이 만든 관측 데이터를 입력으로 받으면 자연스럽다.

#### I-04 Agent SOC / 정책 드리프트 자동 패치
① **사용자/구매자·상황**: 에이전트 플릿을 운영하는 SOC. "평소엔 안 하던 `~/.ssh` 읽기 시도"를 사람이 로그에서 못 보는 상황 [추론]. 컨테이너 세계의 유사 통계: Sysdig 2024 보고서 인용에 따르면 K8s 사용자 중 드리프트 알림을 받는 비율은 약 25%, 자동 차단까지 하는 팀은 약 4% [사실] (https://www.sysdig.com/blog/container-drift-detection-with-falco).
② **시나리오**: OpenShell allow/deny 스트림 → 윈도우 통계로 후보 추출 → 소형 모델이 분류 → 임계 시 대형 모델이 원인 분석 + 정책 패치 제안 → 사람 승인 → `network_policies` 핫리로드 → 정상 태스크 회귀 검사.
③ **오늘의 대체**: Datadog AI Agent Monitoring(2025-06, 의사결정 경로 그래프·무한 루프 탐지) [사실] (https://investors.datadoghq.com/news-releases/news-release-details/datadog-expands-llm-observability-new-capabilities-monitor), Palo Alto Prisma AIRS Agent Security [사실] (https://www.paloaltonetworks.com/ai-security/prisma-airs), Zenity [사실] (https://zenity.io/platform), Falco + Talon(런타임 드리프트 자동 대응) [사실] (https://www.sysdig.com/blog/container-drift-detection-with-falco). 불편: 관측·알림 중심이고 "승인 후 정책만 좁히는 패치 루프"는 확인되지 않음 [미확인].
④ **유용/장벽**: 유용 — 벤더들이 2025~2026년 에이전트 런타임 이상행위 카테고리를 신설 [사실, 위 URL]. 장벽 — 오탐 관리, 기존 관측 벤더가 같은 기능을 준비 중, 라벨된 인시던트 데이터 부재 [추론].
⑤ **6일 MVP**: 주입 인시던트 N건에서 F1·1,000건당 오탐·패치 후 회귀율. 증명하지 못하는 것: 실제 플릿의 이상행위 분포.
⑥ **판정: 다른 후보의 부품 (I-01 운영 루프).** 단독으로는 "로그→LLM→요약"이라는 흔한 SI 프로젝트로 보인다.

#### I-15 A2A Ephemeral Capability Lease Broker
① **사용자/구매자·상황**: 오케스트레이터가 서브에이전트에 작업을 위임하는 멀티에이전트 플랫폼팀. 서브에이전트들이 광역 자격증명·네트워크 허용을 공유하는 상황 [추론]. A2A 스펙 자체가 "Agent Card에 정적 비밀을 넣지 말고 대역외 동적 자격증명을 선호"라고 명시 [사실] (https://a2a-protocol.org/v0.3.0/specification).
② **시나리오**: 부모 에이전트가 A2A로 "PR 코멘트 작성" 위임 → 브로커가 `api.github.com` 30초 리스를 OpenShell `network_policies`에 핫리로드 [사실, 동적 섹션] (https://docs.nvidia.com/openshell/sandboxes/policies) → 서브에이전트 실행 → 완료/만료 시 회수 → 만료 후 재호출은 deny.
③ **오늘의 대체**: HashiCorp Vault 공식 튜토리얼 "A2A 프로토콜 + Vault로 에이전트 인증"(OIDC·스코프 토큰, K8s) [사실] (https://developer.hashicorp.com/vault/tutorials/auth-methods/secure-ai-agent-communication-a2a-vault-kubernetes), Auth0 Token Vault(RFC 8693 토큰 교환, 2025-10) [사실] (https://auth0.com/blog/auth0-token-vault-secure-token-exchange-for-ai-agents/), Microsoft Entra Agent ID(JIT 스코프 토큰 로드맵) [사실] (https://techcommunity.microsoft.com/blog/microsoft-entra-blog/announcing-microsoft-entra-agent-id-secure-and-manage-your-ai-agents/3827392), AWS AgentCore Identity [사실] (https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/understanding-agent-identities.html). 불편: 전부 **토큰(앱 계층) 임대**이고, 네트워크 네임스페이스 수준에서 "특정 도메인만 N초 CONNECT 허용"하는 OS 계층 임대는 확인되지 않음 [추론].
④ **유용/장벽**: 유용 — A2A가 1년 만에 150개 이상 조직 참여, AAIF 합류 [사실] (https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year); nvidia-nat[a2a]로 구현 경로 존재 [사실] (https://docs.nvidia.com/nemo/agent-toolkit/latest/build-workflows/a2a-client.html). 장벽 — A2A의 프로덕션 배포는 아직 제한적이라는 평가 [사실] (https://galileo.ai/blog/google-agent2agent-a2a-protocol-guide), 리스 만료와 작업 수명주기 동기화(29초에 실행 중인 작업, 재시도) [추론], `required_capabilities` 계약은 표준이 아니라 팀 자작이라는 점을 명시해야 함 [추론].
⑤ **6일 MVP**: 부모 1 + 서브 2 + 브로커에서 allowed-domain-seconds 감소, 만료 후 공격 deny율, 위임 오버헤드. 증명하지 못하는 것: 파일/프로세스 권한(정적 계층이라 불가), 분산 리스 관리자의 동시성.
⑥ **판정: 지금 추진 가능하나 4~5인 팀에서.** 멀티에이전트 고유 문제이고 커널 네트워크 임대는 새롭지만, 고객이 "A2A를 이미 운영하는 조직"으로 아직 좁다.

#### N-A Runaway Agent Circuit Breaker
① **사용자/구매자·상황**: 에이전트를 무인(cron) 운영하는 스타트업·개인 개발자. 무한 재시도·계획 루프로 예상 밖 과금이 발생하는 상황. OpenAI 개발자 포럼에 "무한 루프로 인한 API 비용 폭주를 막을 방법" 질문이 2024~2026년 반복되고 "계정 한도만으로는 늦다"는 결론이 공유됨 [커뮤니티] (https://community.openai.com/t/how-to-cap-cost-to-prevent-api-cost-from-blowing-up/1029082 , https://community.openai.com/t/how-are-you-handling-runaway-agent-costs/1383593).
② **시나리오**: NAT 프로파일러가 토큰 속도·반복 툴 시그니처·HTTP 재시도 패턴 관측 → 임계 초과 시 워크플로 중단 + OpenShell 네트워크 정책 핫리로드로 외부 툴 엔드포인트 제거 → 운영자에게 원인·비용 노출 보고 → 사람이 재개.
③ **오늘의 대체**: 정적 `max_steps`/timeout; OpenAI 프로젝트 예산 한도; LiteLLM Agent Gateway의 세션별 `max_iterations`·`max_budget_per_session`(예상 비용 선예약) [사실] (https://docs.litellm.ai/docs/proxy/users). 불편: 모두 "새 LLM 호출을 거부"할 뿐 이미 발화된 외부 툴 호출(egress)을 네트워크에서 끊지는 않음 [추론]. OWASP ASI08 연쇄 장애의 1차 방어가 서킷브레이커 [사실] (https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/).
④ **유용/장벽**: 유용 — 금전 피해가 반복 보고되고 구현이 작음. 장벽 — 예산 캡 자체는 PyPI에 유사 패키지가 다수인 레드오션 [추론]; NAT 프로파일러가 토큰 속도·툴 시그니처를 실시간 노출하는지 재확인 필요 [미확인].
⑤ **6일 MVP**: 정상 20 + 주입 runaway 20 workflow에서 overspend prevented·false cutoff·차단 지연. 증명하지 못하는 것: 실제 프로덕션의 루프 유형 분포.
⑥ **판정: 지금 추진 — 다른 안의 부품으로.** A안(감사 후 운영)·B안(스킬 평가 중 폭주) 어디에나 하루면 붙는다. 단독 제품으로는 얇다.

#### I-16 Air-Gapped Agent
① **사용자/구매자·상황**: 망분리가 법제화된 공공기관·금융권·병원·국방의 보안/인프라 담당자. 한국은행은 2026-01-21 국정원 다층보안체계(MLS)를 적용해 데이터 등급 태깅·외부 AI 호출 통제·행위 로그 전면 기록으로 "논리적 망분리"를 구현했고, 금융위는 시중은행의 물리적 망분리를 전면 재검토 중 [사실] (https://www.etnews.com/20260212000082). 국정원 N2SF는 2025년 6개 공공기관 실증 후 2026년 확산 추진 [사실] (https://www.newstomato.com/readnews.aspx?no=1294190).
② **시나리오**: 인터넷 egress deny-all + 승인된 로컬 추론 경로만 허용 → Nemotron Nano NIM + 소형 Retriever를 L40S/DGX Spark에 배치 → 민감 문서 QA 수행 → 인젝션이 유출을 지시해도 "성공적으로 나간 외부 바이트 = 0"을 감사 로그로 증명 → 보안팀이 온라인 대비 품질 격차를 보고 도입 결정.
③ **오늘의 대체**: 물리적 망분리 + 망연계(CDS) 솔루션으로 파일 반출입 승인 — 실시간 API 기반 생성형 AI와 구조적으로 충돌 [사실] (https://www.boannews.com/news/articleView.html?idxno=135396); N2SF/MLS는 "완전 오프라인"이 아니라 "등급별 통제된 개방" 모델 [추론]. NIM 지원 매트릭스상 L40S 48GB가 Nemotron 3 Nano·3.5 Lightning 등의 공식 지원 GPU [사실] (https://docs.nvidia.com/nim/large-language-models/latest/reference/support-matrix.html). 해외에는 DGX Spark 기반 온프레미스 LLM을 "0 bytes egressed"로 마케팅하는 벤더가 있으나 제3자 검증 없음 [벤더주장] (https://www.iotai.com.au/services/sovereign-ai).
④ **유용/장벽**: 유용 — 한국은행 사례가 트리거가 되어 금융·공공 전환이 진행 중이라 타이밍이 좋음 [사실, 위 URL]. 장벽 — 예선 기간에 48GB급 GPU가 없으면 핵심 주장을 실행으로 증명 불가; N2SF 정책 방향은 deny-all보다 통제된 개방이라 컨셉 조정 필요 [추론]; 오프라인 vs 온라인 품질 격차의 독립 벤치마크 미발견 [미확인].
⑤ **6일 MVP**: GPU가 있을 때만 — 문서 QA 20건 + 유출 공격 20건에서 품질 격차와 successful egress bytes=0. GPU가 없으면 정직한 축소판이 없다.
⑥ **판정: 본선용.** 10/7 L40S 크레딧 지급 후 가장 크게 살아나는 후보. 예선 데모는 API 호출을 쓰는 순간 "에어갭"이 아니게 된다.

### 3-3. 평가·CI·스킬 계열

#### I-11 Agent CI — Real Side-Effect Replay Gate
① **사용자/구매자·상황**: 에이전트 저장소를 운영하는 스타트업·플랫폼팀(고객지원·코딩 에이전트 벤더). 프롬프트·툴 설명·모델을 바꿔도 컴파일 오류가 없어 행동이 조용히 바뀌는 상황 [추론]. Promptfoo는 GitHub Action으로 "PR마다 prompts/ 변경 시 전후 비교 eval 자동 실행"을 정식 제공 → 카테고리가 이미 상용화됨 [사실] (https://www.promptfoo.dev/docs/integrations/github-action).
② **시나리오**: PR 생성 → CI가 OpenShell 임시 샌드박스(파일시스템 스냅샷·픽스처 API·제한 네트워크) 기동 → 골든 태스크 30건을 **실제 툴/MCP**로 재실행 → 트래젝토리·부작용 diff → 의미 있는 회귀만 `Agent Regression Gate: FAIL` (task success 97%→71%, drift 4/30, new side effects 2, cost/task +38%) → 개발자가 PR을 고침. 프로덕션 부작용 0.
③ **오늘의 대체**: Promptfoo/LangSmith/DeepEval(주로 mock provider·응답 품질 비교) [사실] (https://github.com/promptfoo/promptfoo); NVIDIA NeMo Agent Toolkit 내장 `trajectory` evaluator(LLM judge 0~1점)·`swe_bench` evaluator [사실] (https://docs.nvidia.com/nemo/agent-toolkit/latest/workflows/evaluate.html) — 격리 실행·픽스처 명시 없음 [미확인]; Daytona/E2B(코드 실행 샌드박스 상용) [사실] (https://www.daytona.io/); τ²-bench pass^k(반복 일관성 지표) [사실] (https://arxiv.org/pdf/2506.07982). 불편: 개별 부품은 있지만 "실 툴 재실행 + 부작용 격리 + 회귀만 차단"을 묶은 CI 게이트는 확인되지 않음 [미확인].
④ **유용/장벽**: 유용 — 에이전트가 이메일·DB 등 실제 부작용을 내는 툴을 호출하는 사례가 늘며 "실행은 시키되 부작용은 격리"할 필요가 커짐 [추론] (배경: https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/). 장벽 — 골든 태스크·픽스처 API 제작 비용, 툴콜 순서 차이를 회귀로 오판하는 오탐(의미적 동치 판정), LLM judge의 비결정성 [추론].
⑤ **6일 MVP**: 파일 수정 에이전트 1종, mutation 30개(툴 설명 변경·인자 삭제·모델 교체·권한 축소)에서 탐지 recall/precision·동치 변경 오탐율·CI p95. 증명하지 못하는 것: 다양한 에이전트 유형, 실제 팀의 PR 흐름에서의 오탐 체감.
⑥ **판정: 지금 추진.** 개발자 페인이 가장 보편적이고 산출물(GitHub Actions 출력)이 곧 데모다. 단독으로도, B안의 절반으로도 성립.

#### I-13 Skill CI/Compiler
① **사용자/구매자·상황**: Agent Skills(SKILL.md) 표준을 채택한 코딩 에이전트 운영팀. Anthropic이 2025-10-16 Agent Skills를 발표 [사실] (https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills); NVIDIA는 2026-05-19 "NVIDIA-Verified Agent Skills"와 trust pipeline(스킬 카드 + OpenSSF Model Signing 서명 + evals/ + BENCHMARK.md)을 발표 [사실] (https://developer.nvidia.com/blog/nvidia-verified-agent-skills-provide-capability-governance-for-ai-agents/ , https://docs.nvidia.com/skills/agent-skill-trust-pipeline). 이 조직들은 실패 사례를 사람이 수동으로 스킬 문서화하는 병목을 겪는다 [추론].
② **시나리오**: 에이전트 실패 트레이스 누적 → 후보 SKILL.md 3~5개 자동 합성 → OpenShell 샌드박스에서 train/dev 태스크로 평가 → **frozen 테스트(마지막 1회)** 통과 + 회귀 없음일 때만 로컬 스킬 라이브러리 승격, 스킬 카드·벤치마크 리포트 첨부 → 사람이 리뷰 후 병합.
③ **오늘의 대체**: 사람이 실패 로그를 보고 SKILL.md 작성 → PR 리뷰; OpenHands 커뮤니티 스킬(수동 작성) [사실] (https://docs.openhands.dev/overview/skills); NVIDIA trust pipeline은 "이미 작성된 스킬"의 서명·평가·카드 발급이지 합성 단계는 없음 [사실] (https://docs.nvidia.com/skills/agent-skill-trust-pipeline); 학술 선행: SkillWeaver(2025-04, 웹 에이전트가 경험에서 API를 자율 합성, WebArena 31.8% 개선) [사실] (https://github.com/OSU-NLP-Group/SkillWeaver), Voyager(2023) [사실] (https://arxiv.org/abs/2305.16291). 불편: 합성→검증→승격 루프가 SKILL.md 포맷으로 묶인 사례는 미발견 [미확인].
④ **유용/장벽**: 유용 — NVIDIA가 "스킬 = 평가받는 배포 artifact" 방향을 이미 제품화해 정합성이 높음 [사실, 위 URL]. 장벽 — **자동 생성 스킬은 공급망 공격 표면**: Datadog Security Labs는 2026-05-11 Claude Code 스킬의 동적 컨텍스트(`!` 셸 명령)가 모델이 보기 전에 실행돼 인젝션 방어를 우회한다고 보고했고, OpenClaw 생태계에서 악성 스킬 230개 발견 보고를 인용 [사실] (https://securitylabs.datadoghq.com/articles/malicious-skills-supply-chain-risks-in-coding-agents-with-dynamic-context); held-out 재사용 시 test contamination; 실패 트레이스에 섞인 비밀이 스킬로 합성될 위험 [추론].
⑤ **6일 MVP**: 코딩 에이전트 1종·태스크 패밀리 4개에서 frozen test uplift·promotion precision·tokens/성공. 증명하지 못하는 것: 프로덕션 분포 변화에 대한 일반화, 승격 스킬의 장기 안전성.
⑥ **판정: 지금 추진 (B안 코어).** 대회 필수 요소인 Agent Skills를 연구 대상 자체로 만들고 NVIDIA 공식 방향과 맞는다. 단 자작 스킬을 "NVIDIA Verified"라 부르면 안 되고(skill-card-generator는 서명·승인 안 함 [사실] https://github.com/NVIDIA/skills/blob/main/skills/skill-card-generator/SKILL.md), 승격 게이트가 곧 공급망 방어라는 점을 전면에 세워야 한다.

#### I-02 방어 계층 2×2 비교 (AgentDojo)
① **사용자/구매자·상황**: 실도구 에이전트를 배포하려는 보안팀이 "가드레일이면 충분한가, 커널 정책이 필요한가"를 데이터 없이 논쟁하는 상황 [추론]. Anthropic 공식 입장: 프롬프트 인젝션은 "해결과는 거리가 먼 문제" [사실] (https://www.anthropic.com/research/prompt-injection-defenses).
② **시나리오**: AgentDojo 공격셋 subset을 (a) 무방어 (b) NeMo Guardrails (c) OpenShell 정책(툴을 실제 파일/HTTP 부작용에 매핑) (d) 둘 다로 실행 → "의도 오염율 vs 부작용 완료율" 2×2 그래프 → 보안팀이 계층 조합을 결정.
③ **오늘의 대체**: AgentDojo 결과 페이지의 모델×방어×공격 조합 [사실] (https://agentdojo.spylab.ai/results/); Google DeepMind CaMeL(무방어 84% → 방어 77% 유틸리티로 증명 가능한 보안) [사실] (https://arxiv.org/abs/2503.18813); OpenAI Instruction Hierarchy [사실] (https://arxiv.org/abs/2404.13208). 불편: OS 커널 정책을 방어층으로 넣어 실제 부작용에 매핑한 비교는 미발견 [미확인]. 주의: 정적 벤치마크의 방어 결과는 adaptive 공격 앞에서 과대평가될 수 있다는 2026-06 논문 경고 [사실] (https://arxiv.org/html/2606.26479v1).
④ **유용/장벽**: 유용 — "가드레일만으로 불충분" 컨센서스가 형성 중이라 정량 트레이드오프 수요 [추론]. 장벽 — AgentDojo 툴은 파이썬 시뮬레이션이라 실제 부작용 어댑터를 직접 만들어야 함, 97 task 전체 이식은 불가 [추론].
⑤ **6일 MVP**: 공격 2~3종·task subset에서 2×2 그래프 1장. 증명하지 못하는 것: adaptive 공격, 전체 스위트.
⑥ **판정: 다른 후보의 부품 (I-03/I-01의 ablation).** 그래프 한 장의 설득력은 크지만 제품이 아니다.

#### I-17 Diversity-aware Failure Discovery (Nemotron-Personas-Korea)
① **사용자/구매자·상황**: 대규모 공공 에이전트 운영 조직. 행정안전부의 대화형 "AI 정부24"는 2026-03-09 시범 운영 후 3개월간 누적 이용자 2,848만 명·질의 3,046만 건을 처리 [사실] (https://www.mois.go.kr/frt/bbs/type010/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000008&nttId=124243 , https://biz.chosun.com/topics/topics_social/2026/06/30/TC7LJFWMQZCTPPVFZGH6IBE3D4/). 이런 서비스는 소수의 손으로 쓴 테스트로 검증되어 고령·저문해·지역 표현 차이에서의 실패가 묻힐 위험이 있다 [추론].
② **시나리오**: Nemotron-Personas-Korea(1M records, CC-BY-4.0) [사실] (https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea)에서 연령·지역·학력·직업으로 층화 표집 → 시뮬레이터 페르소나 500~1,000개가 대상 에이전트(예: 대피소 안내)와 대화 → 결정론적 평가자(정답 대피소 집합 비교)로 채점 → "20건 수작업 테스트가 놓친 실패 유형 N개, 최악 집단 성공률 X%" 리포트 → 운영팀이 프롬프트·검색을 수정.
③ **오늘의 대체**: 수작업 테스트 수십 건; τ²-bench의 LLM 사용자 시뮬레이터(방법론 표준화) [사실] (https://arxiv.org/pdf/2506.07982); Coval(음성·채팅 에이전트 시뮬레이션 QA 상용) [사실] (https://www.coval.dev/); NIST AI RMF의 공정성 측정 요구 [사실] (https://www.nist.gov/itl/ai-risk-management-framework). 불편: 한국 인구통계 층화 + 결정론적 평가를 결합한 사례 미발견 [미확인].
④ **유용/장벽**: 유용 — 실운영 규모의 공공 에이전트가 이미 존재. 장벽 — 합성 페르소나가 실제 취약 계층의 오류 패턴(오타·방언)을 얼마나 반영하는지 미검증(synthetic-to-real gap) [미확인]; 장애 속성은 공개 스키마에 없음 [미확인]; "형평성 증명"이라 말하면 안 되고 "합성 층화 집단에 대한 강건성"으로 한정해야 함 [추론].
⑤ **6일 MVP**: 단일 서비스 에이전트에 대해 새로 발견한 실패 카테고리 수와 worst-group success. 증명하지 못하는 것: 실제 시민 대표성.
⑥ **판정: 다른 후보의 부품 (공공 서비스 에이전트 평가층).** OpenShell 필연성이 약해 단독으로는 대회 정합성이 낮지만, 실사용 맥락은 23개 중 가장 크다.

### 3-4. 공공·산업 계열

#### I-05 서울 지진 대피소 재배정 에이전트
① **사용자/구매자·상황**: 서울시·자치구 재난안전과. 지진 시 시민이 최근접 대피소로 몰려 수용 초과가 나는 상황 [추론]. 인천시는 대피소별 수용인원을 1인당 0.825㎡ 기준으로 공시하고 옥외대피장소 639곳 중 18곳의 휠체어 접근성이 낮다고 명시 → 용량·접근성 제약이 실무 지침에 이미 존재 [사실] (https://www.incheon.go.kr/safe/SAFE010201).
② **시나리오**: 지진 시나리오 + "고령자 800m 이내, B도로 통제" 입력 → 제약 추출 → cuOpt 용량 제약 배정 → 지도 before/after + 초과 수용 0·p95 대피시간 → 담당자가 훈련 계획·안내 문안에 반영.
③ **오늘의 대체**: 안전디딤돌 앱·국민재난안전포털의 "가장 가까운 대피소" 안내 [사실] (https://news.seoul.go.kr/safe/archives/512222) — 용량·통제 반영 없음 [추론]. 학술: shelter location-allocation(2024) [사실] (https://www.sciencedirect.com/science/article/pii/S0305054824002569), 일본 대피소 스케줄링(고베 데이터) [사실] (https://arxiv.org/pdf/2111.13326). cuOpt 실사용은 물류(clicOH 라스트마일 20배 가속 [사실] https://developer.nvidia.com/blog/spotlight-clicoh-accelerates-last-mile-delivery-20x-with-nvidia-cuopt/ ; AT&T 기술자 디스패치 [사실] https://blogs.nvidia.com/blog/cuopt-world-record-route)에 있고 **재난 대피소 배정 적용 사례는 직접 사례 미발견**.
④ **유용/장벽**: 유용 — 대피소·인구 데이터 무료 공개(장벽 낮음), 최근접 안내가 유일한 대체재라 빈틈이 실재 [추론]. 장벽 — 보행 도로망·실시간 도로 통제·고령자 거주 세분 데이터 비공개 [미확인]; **현행 배정 이력이 없어 기준선이 합성**; 1개 구 규모는 CPU 솔버로 충분해 GPU 필연성이 낮음 [추론].
⑤ **6일 MVP**: 직선거리 기반 배정 개선율. 증명하지 못하는 것: 실제 보행시간, 실제 대피 행동, GPU 필요성.
⑥ **판정: 본선용.** 사회적 가치와 데이터 공개성은 좋으나 6일엔 "실제 개선"을 증명할 기준선이 없다. 도로망 데이터 확보 후 본선에서.

#### I-06 지자체 폐기물 수거 경로 재계획
① **사용자/구매자·상황**: 기초자치단체 청소행정과. 민원(누락·넘침) 발생 시 당일 경로 재조정 [추론]. 대전 서구가 2025년 카메라·AI로 쓰레기를 인식해 수거 우선순위·경로를 제시하는 시스템을 시작(과기정통부 공모, 3년 7.4억 원) [사실] (https://www.ccnnews.co.kr/news/articleView.html?idxno=380423).
② **시나리오**: 민원 텍스트 → 새 pickup task/제약 → cuOpt VRP 재계획 → 배차 담당자 확인.
③ **오늘의 대체**: 고정 요일·순번 노선 + 수작업 조정; 상용 SaaS(WasteHero·Rubicon·AMCS 등) [사실, 존재] ; 환경부 공개 데이터는 RFID 종량기 설치 현황뿐 [사실] (https://www.data.go.kr/data/15061767/fileData.do) — **실제 수거 차량 경로·운행 원시데이터는 공개되어 있지 않음** [미확인/사실상 부재].
④ **유용/장벽**: 장벽이 결정적 — 기준선 부재로 개선율이 합성 대 합성이 됨 [추론]. cuOpt를 명시한 폐기물 수거 사례 미발견.
⑤ **6일 MVP**: 합성 인스턴스에서 cuOpt vs CPU 솔버 시간 비교 정도. 증명하지 못하는 것: 실제 지자체 운영 개선.
⑥ **판정: 보류·폐기.** 실제 운행 데이터가 있는 지역을 찾지 못하면 시작하지 말 것.

#### I-08 제조 SOP 준수 모니터링 (자연어 SOP 등록 레이어)
① **사용자/구매자·상황**: 전자·EMS 제조사의 품질·공정엔지니어. SOP가 자주 바뀌는 라인에서 검사기를 매번 다시 만드는 상황 [추론]. 실사용 근거는 23개 중 가장 강함: Pegatron이 NVIDIA VSS 기반 조립 가이딩으로 불량률 67%↓ 등을 보고 [벤더주장] (https://www.nvidia.com/en-eu/case-studies/pegatron-scales-factory-operations-with-visual-ai-digital-twins); Foxconn이 DeepHow "Live SOP Verification"(NVIDIA Cosmos + Metropolis VSS)을 도입 발표(2026-06-02) [사실] (https://www.businesswire.com/news/home/20260602068205/en/Foxconn-Boosts-Production-Throughput-With-DeepHow-Live-SOP-Verification-Powered-By-NVIDIA); NVIDIA Factory Operations(FOX) Blueprint 발표(2026-06-01) [사실] (https://blogs.nvidia.com/blog/factory-operations-fox-blueprint-ai-brain/).
② **시나리오**: 엔지니어가 새 SOP를 자연어로 등록 → 에이전트가 단계 정의·검사기 설정·평가셋·영상 접근 정책(OpenShell)을 생성 → 라인 영상에 적용 → 위반 시 알림·false alarm/100분 리포트.
③ **오늘의 대체**: 수동 관찰·정기 감사·말단 검사 [사실, DeepHow 발표문 인용] ; NVIDIA 공개 `sop-monitoring-blueprints` [사실] (https://github.com/NVIDIA/sop-monitoring-blueprints) 및 `deepstream-sop` 스킬; Drishti·Retrocausal·Invisible AI·Tulip 등 [사실, 존재]. 불편: 블루프린트가 이미 학습→배포→평가 전체를 제공하므로 단순 실행은 차별화가 없고, "자연어 SOP 등록 자동화"라는 정확한 기능의 실사용 사례는 미발견 [미확인].
④ **유용/장벽**: 유용 — 대형 EMS가 NVIDIA와 검증. 장벽 — 라벨된 SOP 위반 영상 비공개 [미확인]; 한국 내 채택 사례 미발견 [미확인]; GPU·VSS 인프라 비용으로 중소 제조사 진입장벽 높음 [추론].
⑤ **6일 MVP**: 사전학습 파이프라인 고정 + SOP 등록 레이어 데모. 증명하지 못하는 것: 실제 라인 정확도, 학습 없이 새 SOP를 얼마나 잡는지.
⑥ **판정: 본선용.** 실사용 근거는 최강이지만 예선 6일엔 영상·GPU·차별화 레이어를 동시에 확보하기 어렵다.

#### I-19 Privacy-Constrained Multi-Agent Allocation
① **사용자/구매자·상황**: 원시 데이터를 공유할 수 없는 병원 네트워크·물류사·계열사. 코로나19 때 지자체·병의원 간 병상 공동배정 협조체계가 실제로 운영됨 [사실] (https://www.korea.kr/briefing/pressReleaseView.do?newsId=156514448) — 단 구조화된 자동 교환은 아니었음 [미확인].
② **시나리오**: 지역 3개가 각자 OpenShell 샌드박스에서 원시 수요를 격리 → 여유 용량·한계비용만 A2A 구조화 메시지로 교환 → 결정론적 배분 프로토콜 반복 → 중앙 cuOpt 최적해 대비 gap%·원시 교차 접근 0 → 기관장이 데이터 공유 없이 배분안 수용.
③ **오늘의 대체**: 전화·이메일 협의; 중앙 데이터 풀링 + 법적 계약(수개월); Catena-X/Gaia-X 데이터 스페이스(원시 데이터 중앙집중 없이 주권 유지, BMW·Bosch·SAP·Siemens 참여) [사실] (https://internationaldataspaces.org/catena-x-with-gaia-x-will-data-space-be-the-word-of-2021). 불편: 데이터 스페이스는 교환 규격이지 최적화 프로토콜이 아님 [추론].
④ **유용/장벽**: 유용 — 데이터 주권 규제로 풀링 불가 상황 증가; A2A 150개 조직 [사실, 위 URL]. 장벽 — 분산 협상 프로토콜을 팀이 설계해야 하고, 합성 데이터 의존 [추론]; A2A 초기 채택 단계 [사실] (https://galileo.ai/blog/google-agent2agent-a2a-protocol-guide).
⑤ **6일 MVP**: 3지역 합성 인스턴스에서 optimality gap과 교차 접근 0. 증명하지 못하는 것: 실제 조직 간 데이터·인센티브.
⑥ **판정: 본선용 (4~5인 팀이면 예선 도전 가능).** 평가 구조(중앙 최적해 = 상한)는 23개 중 가장 정직하지만, 고객이 "협상 프로토콜을 신뢰"하기까지의 거리가 멀다.

#### N-B Federated Agent Immune System (NVFLARE)
① **사용자/구매자·상황**: ISAC 회원사·병원 컨소시엄의 SOC. 공격 트레이스를 외부에 내지 않고 공동 탐지기를 개선하려는 상황 [추론].
② **시나리오**: 각 조직이 로컬 OpenShell 감사 로그로 탐지기 학습 → NVFLARE로 파라미터만 집계 → 다른 조직이 처음 보는 공격군 탐지 F1 상승.
③ **오늘의 대체**: STIX/TAXII + ISAC의 수동 IOC 공유 [사실] (https://www.anomali.com/glossary/information-sharing-and-analysis-center-isac). NVFLARE 실사용은 의료에 집중: EXAM 모델(20개 병원, 원시 데이터 비공유, 로컬 대비 평균 38% 일반화 향상, Nature Medicine) [사실] (https://blogs.nvidia.com/blog/federated-learning-nature-medicine , https://pmc.ncbi.nlm.nih.gov/articles/PMC9157510/), King's College London NHS [사실] (https://nvidianews.nvidia.com/news/kings-college-london-and-nvidia-build-uks-first-ai-platform-for-nhs-hospitals). **에이전트 공격 탐지에 대한 FL 실배포 사례는 직접 사례 미발견**; 침입탐지 FL은 서베이 단계 [사실] (https://dl.acm.org/doi/full/10.1145/3731596).
④ **유용/장벽**: 유용 — NVFLARE 신뢰도 높음. 장벽 — 다기관 공격 라벨 데이터 비공개, PKI·프로비저닝 운영 오버헤드 [추론].
⑤ **6일 MVP**: 3 가상 사이트 시뮬레이션 uplift. 증명하지 못하는 것: 실제 조직 간 운영.
⑥ **판정: 본선용.** NVIDIA 블로그 소재로는 좋지만 고객 확보 거리가 가장 멀다.

### 3-5. 데이터·도메인 계열

#### I-07 Safe Autonomous CVE Triage
① **사용자/구매자·상황**: 중소~중견 보안팀·DevSecOps. SCA가 쏟아내는 CVE 중 실제 호출되는 것을 판별할 인력이 없는 상황. NIST는 2026-04 "기록적 CVE 증가"에 대응해 NVD 운영을 바꾸며 2026년 연간 6만 건 돌파를 전망하고, 2026-03-01 이전 백로그 CVE를 "Not Scheduled"로 전환 [사실] (https://www.nist.gov/news-events/news/2026/04/nist-updates-nvd-operations-address-record-cve-growth); 감사기관은 NIST가 백로그를 해소할 지속 가능한 프로세스가 없었다고 지적(2026-05) [사실] (https://www.oversight.gov/reports/evaluation-nists-management-national-vulnerability-database). Endor Labs는 고객(Cursor)의 "이전 도구가 플래그한 취약점의 97% 이상이 도달 불가능"이라는 증언을 게시 [벤더주장] (https://www.endorlabs.com/use-case/sca-with-reachability).
② **시나리오**: NemoClaw cron이 매일 NVD·GHSA를 읽기 전용으로 조회 → 사내 코드·매니페스트(read-only)에서 취약 함수 호출 경로 판정 → 우선순위 리포트 초안 → 정책 게이트에서 사람이 발송 승인 → 보안팀은 "실제 고쳐야 할 5건"만 받음. 인젝션이 유출을 지시해도 정책상 경로가 없음.
③ **오늘의 대체**: Snyk Reachability(콜그래프, REACHABLE/NO PATH 라벨) [사실] (https://docs.snyk.io/scan-fix-and-prevent/fix/prioritize-issues-for-fixing/reachability-analysis), Endor Labs 함수 수준 reachability(2025-04 Series B $93M) [사실] (https://www.endorlabs.com/learn/reachability-analysis), Google OSV-Scanner 실험 기능 [사실] (https://google.github.io/osv-scanner/experimental/), CISA KEV·FIRST EPSS 우선순위 신호 [사실] (https://www.first.org/epss , https://www.cisa.gov/known-exploited-vulnerabilities-catalog), AI SOC 벤더 Prophet Security(2025-07 Series A $30M) [사실] (https://www.prophetsecurity.ai/). 불편: 상용 reachability는 비싸고 "조직 정책(읽기 전용·발송 승인)에 맞춘 안전한 자율 에이전트" 형태로 배포된 사례는 미확인 [미확인]. 불완전한 콜그래프가 reachability의 흔한 실패 원인이라고 Endor 스스로 인정 [사실] (https://docs.endorlabs.com/scan/sca/reachability-analysis/index).
④ **유용/장벽**: 유용 — CVE 폭증 + NVD 백로그가 구조적. 장벽 — 언어·빌드별 정확도 편차, NVD 메타데이터 공백 시 입력 품질 저하, 20~30 픽스처로는 상용 대비 정밀도 비교가 통계적으로 약함 [추론].
⑤ **6일 MVP**: reachable/unreachable 페어 픽스처 20~30개에서 P/R/F1 + 주입 유출 ASR + 정책 예측 vs 실측 일치. 증명하지 못하는 것: 실제 대규모 리포 정확도, SCA 대체 가능성(대체가 아니라 후처리로 포지셔닝).
⑥ **판정: 지금 추진 (2순위 그룹).** 페인은 가장 확실하나 상용 대체재도 가장 강하다. 보안 경험자가 팀에 있을 때만.

#### I-10 Agent Inference Governor
① **사용자/구매자·상황**: 다단계 에이전트를 운영하며 스텝별 모델 비용·지연을 관리해야 하는 팀 [추론].
② **시나리오**: 품질 목표·월 예산·p95를 YAML로 선언 → 게이트웨이가 스텝별 Nano/Ultra 선택 → 비용 절감%·routing regret 리포트.
③ **오늘의 대체 (⚠️ 중복 경고)**: **NVIDIA NeMo Switchyard** — "각 LLM 호출을 그 일을 해낼 수 있는 가장 싼 모델로 라우팅", stage_router(툴 결과·에이전트 진행 상황이 라우팅을 유도), escalation, llm_classifier 알고리즘, NeMo Relay·LiteLLM 플러그인·독립 프록시, Terminal-Bench 2.1에서 Opus 단독 대비 escalation 99.6% 정확도/13.3% 절감·stage 95.7%/30.5% 절감 공개(사전 1.0) [사실] (https://github.com/NVIDIA-NeMo/Switchyard); 기존 NVIDIA LLM Router 블루프린트(v1 Rust 프록시 + Triton 복잡도 분류기, v2 실험판 NAT 기반) [사실] (https://github.com/NVIDIA-AI-Blueprints/llm-router , https://build.nvidia.com/nvidia/llm-router) — build.nvidia.com 카드의 검색 스니펫에 "2026-06-20 deprecated" 문구가 보이나 원문에서 재확인하지 못함 [미확인]; RouteLLM(LMSYS) [사실] (https://github.com/lm-sys/RouteLLM); OpenRouter Auto Router [사실] (https://openrouter.ai/docs/guides/routing/routers/auto-router). 불편: 이들 중 "월 예산 소진율을 실시간 피처로 쓰는 예산 인지형 라우팅"과 "Oracle 대비 regret 평가"는 명시되지 않음 [추론, Switchyard 로드맵 전수 확인 못함 → 미확인 여지].
④ **유용/장벽**: 유용 — 비용 페인은 확실. 장벽 — **NVIDIA가 이미 라우터를 두 세대 제공**. OpenShell inference.local은 게이트웨이당 단일 백엔드·전파 ~5초라 스텝별 라우팅은 앱 계층에서 해야 함 [사실] (https://docs.nvidia.com/openshell/sandboxes/inference-routing).
⑤ **6일 MVP**: BFCL에서 all-Nano/all-Ultra/ours/Oracle 4조건 regret. 증명하지 못하는 것: Switchyard 대비 우위(같은 벤치마크로 비교하지 않으면).
⑥ **판정: 보류.** Switchyard 위의 "예산·SLO 정책 계층 + OpenShell 자격증명 격리 + regret 평가" 플러그인으로 재정의하고 Switchyard와 같은 벤치마크로 비교할 수 있을 때만 추진.

#### I-09 약물 상호작용(DUR) 검증 에이전트
① **사용자/구매자·상황**: 요양시설·재가돌봄 종사자. 촉탁의 제도만으로는 시설 노인이 약사의 투약관리를 받기 어렵다는 지적 [사실] (https://www.dailypharm.com/user/news/91591).
② **시나리오**: 입소자 처방 목록 입력 → 결정론적 DUR 룰엔진(병용금기·노인주의) 판정 → LLM이 근거 인용 설명 → 시설 담당자가 의사·약사에게 확인 요청. 처방 변경은 하지 않음.
③ **오늘의 대체**: 심평원 "내가 먹는 약, 한눈에!"(본인 인증 후 처방 이력 통합 조회, 2025-06) [사실] (https://www.korea.kr/news/policyNewsView.do?newsId=148945126); 소비자 앱 필톡(병용금기·중복 확인) [사실] (https://play.google.com/store/apps/details?id=com.pmatch.pilltalk); 식약처 DUR 품목정보 API(병용·연령·임부·노인주의 등 무료) [사실] (https://www.data.go.kr/data/15059486/openapi.do); 한국의약품안전관리원 병용금기 파일은 **비상업 연구·교육 목적만** 허용 [사실] (https://www.data.go.kr/data/15089525/fileData.do). 불편: 시설 단위 다인 배치 처리형은 미발견 [미확인].
④ **유용/장벽**: 유용 — 데이터 무료·공개. 장벽 — 상업화 시 라이선스 승인, 비의료기관의 판단이 처방에 영향을 주면 의료법 저촉 소지 [추론], 요양시설의 DUR 접근 가능 여부는 2011년 자료 외 최신 근거 미확보 [미확인].
⑤ **6일 MVP**: 골든 pair recall·false negative. 증명하지 못하는 것: 법적 지위, 실제 시설 워크플로 적합성.
⑥ **판정: 보류·폐기.** 좋은 서비스 아이디어지만 결정론적 룰엔진이 코어라 에이전트·OpenShell 필연성이 없고 규제 리스크가 크다.

#### I-12 아파트 실거래 이상거래 조사 에이전트
① **사용자/구매자·상황**: 국토부 부동산소비자보호기획단·한국부동산원 조사 인력. 반기 기획조사로 2025 하반기 1,002건 [사실] (https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95091558&lcmspage=1), 2026-04 서울·경기 746건 적발 [사실] (https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95091935&lcmspage=1); 2025 상반기 서울 아파트 계약해제 4,240건(전년 1,155건), 해제의 92%가 동일 거래인·동일 매물·동일 가격 재신고 [사실] (https://www.arunews.com/news/articleView.html?idxno=50806).
② **시나리오**: 상시 수집 → 계약해제·재신고·가격 이상 패턴 후보 → 근거 묶음 → 조사관이 검토 대상 선정.
③ **오늘의 대체**: 반기 수동 표본조사 + 보도자료; 실거래가공개시스템 조회 [사실] (https://rt.molit.go.kr/). 불편: 실시간성 없음. 과거 조사의 위법 확정률은 22~34% 수준 [사실] (https://www.joongang.co.kr/article/25309680).
④ **유용/장벽**: 유용 — 정부가 공개한 패턴(동일인 재신고)과 정합. 장벽 — **건별 라벨 비공개**로 P/R 측정 불가 [사실 기반, 보도자료에 건별 데이터 없음]; 개인 거래정보·명예훼손("위법 의심" 표현만 허용) [추론]; 에이전트 없이 SQL로 풀림 [추론].
⑤ **6일 MVP**: 합성 라벨 P/R뿐. 증명하지 못하는 것: 실제 이상거래 탐지력.
⑥ **판정: 보류·폐기.** "정부 적발 사례와의 사후 일치율" 같은 대리 지표를 설계하고 개인정보 검토를 거치기 전엔 시작 불가.

#### I-20 Legal Change Impact Analyzer
① **사용자/구매자·상황**: 기업 컴플라이언스·법무팀. 조항 하나가 바뀔 때 인용·위임·정의어 관계 조문을 놓치는 상황 [추론]. 한국 레그테크 코딧(CODIT)이 정책·입법 모니터링을 제품화(2026-03 AI 정책 인텔리전스 특허) [사실] (https://thecodit.com/kr-ko , https://www.venturesquare.net/1042173).
② **시나리오**: 개정 조문 입력 → 법제처 "관련법령 조회"·"조문-법령용어 연계" API [사실, 191종 중 제공] (https://open.law.go.kr/LSO/openApi/guideList.do)로 그래프 탐색 → 영향 조문 후보 + 연결 근거 → 담당자가 검토.
③ **오늘의 대체**: 국가법령정보센터 수동 검색; 코딧; 슈퍼로이어(496만 건 법률정보 검색) [사실] (https://superlawyer.co.kr/). 불편: 조문 단위 영향 그래프를 recall@k로 평가하는 좁은 기능은 미확인 [미확인].
④ **유용/장벽**: 유용 — API가 자동에 가깝게 열려 있음(승인 1~2일) [사실] (https://open.law.go.kr/LSO/information/guide.do). 장벽 — 골든셋(정답 영향 조문)을 사람이 만들어야 하고 검증 방법이 없음 [추론]; OpenShell 필연성 없음.
⑤ **6일 MVP**: 과거 개정 20~30건 recall@k. 증명하지 못하는 것: 골든셋 자체의 신뢰성, 법해석.
⑥ **판정: 보류.** 법률 RAG 해커톤에 적합. 이 대회 정합성 낮음.

---

## 4. 심층 비교 — 핵심 8개 + A안/B안

각 표의 "우리 후보" 행은 조사 시점에 확인된 대체재와의 차이만 적는다. **"차별화"는 "고객이 돈을 낼 이유"가 아니라 "기존 도구가 하지 않는 일"의 의미**다. 둘은 다르다.

### 4-1. I-03 MCP 공급망 감사관 vs mcp-scan / Cisco mcp-scanner / Docker MCP Gateway

| 대체재 | 정적 검사 | 동적 행동 관측 | 정책 산출 | 격리 계층 | 근거 |
|---|---|---|---|---|---|
| mcp-scan (Invariant → Snyk) | O (포이즈닝·shadowing·tool pinning) | 제한적 | X | 없음 | https://invariantlabs.ai/blog/introducing-mcp-scan |
| Cisco AI Defense mcp-scanner | O (YARA+LLM+VirusTotal) | PyPI 패키지 한정 Docker 샌드박스 | X (리포트) | 부분 | https://github.com/cisco-ai-defense/mcp-scanner |
| Docker MCP Gateway/Catalog | 서명·SBOM 카탈로그 | 로깅·콜 트레이싱 | X (수동 프로필) | 컨테이너 | https://docs.docker.com/ai/mcp-catalog-and-toolkit/mcp-gateway |
| Snyk Evo AI-SPM (2026-03) | 코딩 에이전트 거버넌스 | [미확인] | [미확인] | [미확인] | https://www.forbes.com/sites/tonybradley/2026/03/24/snyk-launches-evo-ai-spm-to-govern-autonomous-coding-agents |
| **I-03** | O (MCPTox 기준) | **O (OpenShell 감사 로그: 파일·네트워크·바이너리)** | **O (최소권한 YAML)** | **커널 (Landlock/seccomp/netns)** | — |

- **차별화**: "선언 vs 관측 diff → 정책 자동 산출 → 정책 적용 후 재검증"의 폐루프. 대체재는 모두 "경고"에서 끝난다 [추론, 위 표 근거].
- **위험**: (1) Snyk·Cisco·Docker가 같은 방향으로 확장하면 6개월 내 기능 격차가 사라짐 [추론]. (2) 실제 서버는 OAuth·DB가 필요해 동적 감사가 어렵고, 45개 실서버가 지금도 살아 있는지 미확인 [미확인]. (3) MCPTox 리포 라이선스 미확인 [미확인].
- **고객이 실제로 하게 되는 일**: "MCP 서버 승인 요청 → 리포트·정책 확인 → 승인". 승인자는 AppSec 1명. 이 워크플로가 Docker MCP Catalog의 "서명된 서버만 허용"보다 나은 점은 **비서명·사내 자작 서버**에 적용된다는 것 [추론].

### 4-2. I-13 Skill CI/Compiler vs NVIDIA Verified Skills / SkillWeaver / OpenHands

| 대체재 | 스킬 생성 | 평가·승격 게이트 | 격리 실행 | 포맷 | 근거 |
|---|---|---|---|---|---|
| NVIDIA Verified Agent Skills + trust pipeline | X (사람 작성) | O (스킬 카드·서명·evals/·BENCHMARK.md) | [미확인] | SKILL.md | https://docs.nvidia.com/skills/agent-skill-trust-pipeline |
| SkillWeaver (OSU-NLP, 2025-04) | O (경험→Python API 자율 합성) | O (성공률 기반) | 브라우저 환경 | Python | https://github.com/OSU-NLP-Group/SkillWeaver |
| OpenHands 커뮤니티 스킬 | X (사람 작성) | PR 리뷰 | 리포 환경 | SKILL.md류 | https://docs.openhands.dev/overview/skills |
| Voyager (2023) | O (Minecraft 스킬 코드) | O | 게임 환경 | JS | https://arxiv.org/abs/2305.16291 |
| **I-13** | **O (실패 트레이스→SKILL.md)** | **O (frozen test + 회귀 0 + 카드·리포트 산출)** | **OpenShell** | SKILL.md | — |

- **차별화**: "자동 합성"과 "NVIDIA 형식의 승격 산출물"의 결합. NVIDIA 파이프라인은 합성 단계가 없고, SkillWeaver는 포맷·거버넌스가 다르다 [사실 기반 추론].
- **위험**: 자동 생성 스킬 = 공급망 공격 표면 (Datadog 2026-05: 동적 컨텍스트가 모델 검토 전 실행 [사실] https://securitylabs.datadoghq.com/articles/malicious-skills-supply-chain-risks-in-coding-agents-with-dynamic-context). **승격 게이트가 곧 방어**라는 프레임 없이는 "위험한 자동화"로 읽힌다. 표준이 신생(2025-10)이라 고객 수가 작다 [추론].
- **고객이 하게 되는 일**: 매주 승격 후보 스킬 PR을 리뷰. 사람이 SKILL.md를 처음부터 쓰는 대신 "증거가 붙은 초안"을 승인.

### 4-3. I-11 Agent CI vs Promptfoo / NeMo Evaluator / Daytona·E2B / τ²-bench

| 대체재 | 테스트 대상 | 실제 툴 실행 | 부작용 격리 | PR 게이트 | 근거 |
|---|---|---|---|---|---|
| Promptfoo GitHub Action | 프롬프트 출력 diff·레드팀 | 주로 mock | 없음 | O | https://www.promptfoo.dev/docs/integrations/github-action |
| NeMo Agent Toolkit evaluate (trajectory·swe_bench) | 워크플로 궤적 LLM judge | 워크플로 실행 | 명시 없음 | X | https://docs.nvidia.com/nemo/agent-toolkit/latest/workflows/evaluate.html |
| Daytona / E2B | 코드 실행 | O | 컨테이너/microVM | X (인프라) | https://www.daytona.io/ |
| τ²-bench pass^k | 툴 호출·정책 준수 일관성 | 벤치마크 내 DB | 벤치마크 환경 | X | https://arxiv.org/pdf/2506.07982 |
| **I-11** | **실 MCP/툴 트래젝토리 + mutation 민감도** | **O (픽스처 API)** | **OpenShell 임시 샌드박스 + 스냅샷** | **O (의미 있는 회귀만)** | — |

- **차별화**: 부품은 다 있지만 결합체가 없다. 특히 "동치 변경(툴 순서만 다름)은 통과, 의미 회귀만 차단"을 mutation 라벨로 증명하는 것이 핵심 [추론].
- **위험**: LLM judge 비결정성; 골든 태스크·픽스처 제작 비용이 도입 병목; Docker Sandboxes가 CI 통합을 내놓으면 격리 부분의 차별화가 줄어듦 [추론] (Docker Sandboxes microVM은 현재 macOS/Windows, Linux는 레거시 컨테이너 [사실] https://www.docker.com/blog/building-ai-teams-docker-sandboxes-agent).
- **고객이 하게 되는 일**: PR 화면에서 `Agent Regression Gate` 체크 하나를 더 본다. 실패 시 "어떤 툴 호출이 새로 생겼는지"를 클릭해 확인.

### 4-4. I-01 최소권한 합성기 vs AWS IAM Access Analyzer / AgentCore Policy / Docker Sandboxes / Claude Code sandbox

| 대체재 | 범위 | 관찰 기반 자동 생성 | 적대적 검증 | 런타임 강제 | 근거 |
|---|---|---|---|---|---|
| AWS IAM Access Analyzer 정책 생성 | 클라우드 API 권한 | O (CloudTrail) | X | IAM | https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-policy-generation.html |
| K8s audit2rbac | K8s RBAC | O (audit log) | X | K8s | (OSS) |
| AWS Bedrock AgentCore Policy | 툴 호출(Cedar) | 부분 (자연어→Cedar 검증) | X | Gateway | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html |
| Docker Sandboxes | 파일·네트워크·자격증명 | X (수동) | X | microVM | https://www.docker.com/products/docker-sandboxes |
| Claude Code sandbox | 파일·네트워크 | X (수동) | X | Seatbelt/bubblewrap | https://code.claude.com/docs/en/sandboxing |
| **I-01** | **파일+네트워크+바이너리+L7 경로** | **O (OpenShell 감사 로그)** | **O (레드팀 수렴)** | **커널** | — |

- **차별화**: IAM Access Analyzer 패턴을 에이전트 샌드박스에 옮기고 레드팀 수렴을 더한 것. "관찰 기간에 없던 정상 경로 누락"이라는 AWS가 인정한 약점을 held-out 정상 태스크로 측정한다는 점이 새로움 [추론].
- **위험**: 고객이 OpenShell 사용자로 한정(도입 규모 미확인) [미확인]; LLM 생성 정책의 과소제약 없음을 증명할 방법 부재 [추론].

### 4-5. I-10 인퍼런스 거버너 vs NeMo Switchyard / LLM Router / RouteLLM / OpenRouter (⚠️ 중복)

| 대체재 | 라우팅 단위 | 알고리즘 | 예산·SLO 정책 | 벤치마크 공개 | 근거 |
|---|---|---|---|---|---|
| **NVIDIA NeMo Switchyard** (사전 1.0) | LLM 호출/턴 | auto·llm_classifier·**stage_router(툴 결과·진행 상황 반영)**·escalation·composite | routes.toml (품질·예산 SLO 선언은 미확인) | Terminal-Bench 2.1: escalation 99.6%/−13.3% 비용, stage 95.7%/−30.5% | https://github.com/NVIDIA-NeMo/Switchyard |
| NVIDIA LLM Router 블루프린트 v1/v2 | 프롬프트 | 태스크/복잡도 분류(v1), intent/auto(v2) | X | 블로그 예시 | https://github.com/NVIDIA-AI-Blueprints/llm-router |
| RouteLLM (LMSYS) | 프롬프트 | 강/약 이진 + Arena 보정 | X | 논문 | https://github.com/lm-sys/RouteLLM |
| OpenRouter Auto Router | 프롬프트 | ~30 태스크 분류 + 집계 지출 데이터 | cost_tier | — | https://openrouter.ai/docs/guides/routing/routers/auto-router |
| **I-10** | 에이전트 스텝 | 저비용 피처 + 프로파일러 trace | **O (quality_target·monthly_budget·latency_p95 YAML)** | BFCL regret vs Oracle | — |

- **판정 근거**: Switchyard의 stage_router가 이미 "에이전트 실행 단계 인지 라우팅"을 제공하고 Claude Code·Codex CLI를 그대로 붙일 수 있다 [사실, 위 URL]. I-10에서 남는 것은 (1) 예산 소진율 인지 (2) 프로파일러 trace 피처 (3) regret 평가 (4) OpenShell 자격증명 격리뿐이다. **이 4가지를 Switchyard 플러그인(`switchyard-libsy` 임베드)으로 만들면 살고, 별도 게이트웨이를 새로 만들면 재발명이다** [추론].
- **미확인**: LLM Router 블루프린트의 2026-06-20 deprecation 문구(검색 스니펫에서만 확인, 원문 재확인 실패); Switchyard 로드맵에 예산 인지 기능이 있는지.

### 4-6. I-07 CVE 트리아지 vs Endor Labs / Snyk Reachability / OSV-Scanner / Prophet Security

| 대체재 | 범위 | 도달가능성 | 자율 운영·정책 게이트 | 근거 |
|---|---|---|---|---|
| Endor Labs | 코드+컨테이너 SCA | 함수 수준 콜체인 | X (스캐너) | https://www.endorlabs.com/learn/reachability-analysis |
| Snyk Reachability | SCA | 콜그래프 (REACHABLE/NO PATH) | X | https://docs.snyk.io/scan-fix-and-prevent/fix/prioritize-issues-for-fixing/reachability-analysis |
| Google OSV-Scanner | OSS SCA | 실험 기능 | X | https://google.github.io/osv-scanner/experimental/ |
| Prophet Security (AI SOC) | 알림 트리아지 전반 | X (SCA 아님) | 에이전틱 조사 | https://www.prophetsecurity.ai/ |
| **I-07** | NVD+GHSA+사내 코드, cron 상시 | 페어 픽스처로 검증 | **O (read-only 정책 + 발송 승인, 유출 경로 차단)** | — |

- **차별화**: "SCA 대체"가 아니라 "SCA 결과를 신뢰불가 인터넷 + 민감 코드 사이에서 안전하게 처리하는 무인 에이전트". 보안 가치는 트리아지 정확도가 아니라 **trifecta 상황에서의 봉쇄 증명**에 있다 [추론].
- **위험**: 상용 reachability 정밀도(벤더 주장 90%대)와의 비교에서 20~30 픽스처는 통계적으로 약함; NVD "Not Scheduled" 전환으로 신규 CVE 메타데이터 공백 [사실] (https://www.nist.gov/news-events/news/2026/04/nist-updates-nvd-operations-address-record-cve-growth); Endor도 불완전 콜그래프를 흔한 실패 원인으로 인정 [사실] (https://docs.endorlabs.com/scan/sca/reachability-analysis/index).

### 4-7. I-15 A2A 권한 리스 브로커 vs HashiCorp Vault(A2A) / Auth0 Token Vault / Entra Agent ID / AgentCore Identity

| 대체재 | 임대 대상 | TTL | 강제 계층 | 근거 |
|---|---|---|---|---|
| HashiCorp Vault × A2A 튜토리얼 | 스코프 토큰(OIDC) | O | 앱(미들웨어 검증) | https://developer.hashicorp.com/vault/tutorials/auth-methods/secure-ai-agent-communication-a2a-vault-kubernetes |
| Auth0 Token Vault | 외부 API OAuth 토큰(RFC 8693) | O | 앱 | https://auth0.com/blog/auth0-token-vault-secure-token-exchange-for-ai-agents/ |
| Microsoft Entra Agent ID | MS 리소스 스코프 | O (JIT, 로드맵) | 앱 | https://techcommunity.microsoft.com/blog/microsoft-entra-blog/announcing-microsoft-entra-agent-id-secure-and-manage-your-ai-agents/3827392 |
| AWS AgentCore Identity | 워크로드 신원+Token Vault | 부분 | Gateway | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/understanding-agent-identities.html |
| **I-15** | **네트워크 도메인 + 자격증명** | **O (초 단위)** | **커널 netns + OPA CONNECT 프록시** | — |

- **차별화**: 토큰 임대(앱 계층)와 네트워크 임대(OS 계층)의 결합. "토큰이 유출돼도 만료된 리스 밖에서는 CONNECT 자체가 거부"가 데모의 핵심 [추론].
- **위험**: A2A 프로덕션 채택 초기 [사실] (https://galileo.ai/blog/google-agent2agent-a2a-protocol-guide); 파일/프로세스 권한은 정적 계층이라 임대 불가 [사실] (https://docs.nvidia.com/openshell/sandboxes/policies); 고객이 A2A 운영 조직으로 한정.

### 4-8. I-19 프라이버시 제약 분산 배분 vs 중앙 풀링 / Catena-X / 수작업 협의

| 대체재 | 원시 데이터 이동 | 최적성 | 속도 | 근거 |
|---|---|---|---|---|
| 전화·이메일 협의(병상 배정 사례) | 없음 | 낮음 | 느림 | https://www.korea.kr/briefing/pressReleaseView.do?newsId=156514448 |
| 중앙 풀링 + 법적 계약 | 전체 | 최적(상한) | 계약 수개월 | — |
| Catena-X / Gaia-X 데이터 스페이스 | 구조화 데이터만 | 최적화 프로토콜 아님 | 표준화됨 | https://internationaldataspaces.org/catena-x-with-gaia-x-will-data-space-be-the-word-of-2021 |
| **I-19** | **구조화 오퍼만 (OpenShell로 원시 격리 강제)** | **중앙 최적 대비 gap%로 측정** | 반복 협상 | — |

- **차별화**: "프라이버시 vs 최적성"의 트레이드오프를 중앙 최적해(상한)로 정직하게 측정하는 구조 [추론].
- **위험**: 협상 프로토콜을 팀이 설계(표준 없음), 합성 데이터, 고객의 프로토콜 신뢰까지의 거리 [추론].

### 4-9. A안 vs B안

| 항목 | **A안 MCP Zero-Trust Admission Controller** (I-03 + I-01 + N-C, 선택 N-A) | **B안 Verified SkillOps** (I-13 + I-11, 선택 N-A) |
|---|---|---|
| 고객 | AppSec/플랫폼팀 (MCP 서버를 승인하는 사람) | 코딩 에이전트 운영팀 (스킬·프롬프트를 바꾸는 사람) |
| 오늘 대체재 | mcp-scan, Cisco mcp-scanner, Docker MCP Gateway/Catalog, Arcade/Vault(비밀) | Promptfoo CI, NeMo Evaluator, NVIDIA Verified Skills 파이프라인, 수작업 SKILL.md |
| 비워진 자리 | 동적 행동 관측 → 정책 자동 산출 → 무비밀 운영 | 실 툴 재실행 회귀 게이트 + 실패→스킬 자동 합성 + frozen 승격 |
| 시장 검증 강도 | **강함** (실사고 시연·AAAI 벤치마크·Snyk 인수·Docker 카탈로그) | **중간** (Anthropic 2025-10 표준·NVIDIA 2026-05 trust pipeline·Promptfoo 카테고리) |
| 6일 증명 | MCPTox 정적 전량 + 동적 5~10 서버 → ASR·benign utility·권한 표면 감소 | 태스크 패밀리 4 + mutation 30 → frozen uplift·promotion precision·회귀 탐지율 |
| 실패 시나리오 | 실서버 의존성·OAuth로 동적 감사 어댑터에 3일 이상 소모 | 태스크가 반복적이지 않아 합성 스킬이 일반화되지 않음 (벤치마크 설계가 절반) |
| OpenShell 필연성 | 매우 높음 (동적 감사·정책 강제·비밀 격리 모두 커널 계층) | 높음 (합성 스킬 = 신뢰불가 실행 지침 → 샌드박스 평가) |
| 공급망 리스크 | 감사 대상이 외부 코드 | **생성물 자체가 공급망 표면** (Datadog 보고) |
| 추천 팀 | 3인 (백엔드 2 + 평가/데이터 1) | 2인 |
| 본선 확장 | I-14 Attestation Gate, I-04 운영 루프 | I-17 평가층, N-A 폭주 차단 |

**조사자 결론** [추론]: 고객·사고·벤치마크·대체재 지형이 모두 확인되는 쪽은 A안이다. B안은 NVIDIA 방향과 가장 정합하지만 고객군이 신생 표준 채택자로 좁고, 생성물이 공급망 위험이라는 역설을 안고 간다. 2인이면 B안, 3인 이상이면 A안이 자연스럽다.

---

## 5. 의사결정 매트릭스

> **주의**: 아래 점수(1~5)는 이 조사에서 확인된 공개 근거에 기반한 **우선순위 판단**이다. 대회 공식 채점이 아니며, `SCORING_GOLDEN_RULE.md`의 0/1/3/5 앵커 점수와도 다르다. 5개 축은 사용자 요청 기준: 문제 긴급성 / 구매자 명확성 / 기존 대체재의 빈틈 / 6일 증명 가능성 / NVIDIA·OpenShell 필연성.

| ID | 후보 | 긴급성 | 구매자 | 빈틈 | 6일 | 필연성 | 합 | 근거 한 줄 |
|---|---|---|---|---|---|---|---|---|
| **I-03** | MCP 공급망 감사관 | 5 | 5 | 3 | 4 | 5 | **22** | 실사고·AAAI 벤치마크·AppSec 구매자. 빈틈은 "동적→정책"뿐이고 Snyk/Docker가 근접 |
| **I-01** | 최소권한 합성기 | 4 | 3 | 4 | 4 | 5 | **20** | IAM Access Analyzer 패턴의 에이전트 버전. 구매자가 OpenShell 사용자로 한정 |
| **N-C** | 무비밀 커넥터 | 5 | 5 | 2 | 4 | 4 | **20** | 시장 컨센서스 강하나 Arcade·Vault·Entra가 이미 앱 계층에서 제공 |
| **I-11** | Agent CI 회귀 게이트 | 4 | 4 | 4 | 4 | 3 | **19** | Promptfoo가 카테고리 선점, "실 툴 재실행 격리"만 비어 있음. 격리는 Docker Sandboxes로도 가능 |
| **I-07** | 안전한 CVE 트리아지 | 5 | 5 | 2 | 3 | 4 | **19** | CVE 6만 건 전망·NVD 백로그. Endor/Snyk reachability가 강함 |
| **I-13** | Skill CI/Compiler | 3 | 3 | 4 | 4 | 4 | **18** | NVIDIA trust pipeline과 정합, 합성 단계는 비어 있음. 표준 신생·공급망 리스크 |
| **I-15** | A2A 권한 리스 브로커 | 3 | 3 | 4 | 3 | 5 | **18** | 커널 네트워크 임대는 새롭지만 A2A 운영 조직이 아직 적음 |
| **N-A** | 폭주 서킷브레이커 | 4 | 4 | 2 | 5 | 3 | **18** | 비용 사고 반복 보고. LiteLLM 예산 캡 존재, egress 차단만 차이 |
| **I-16** | 에어갭 에이전트 | 5 | 4 | 3 | 1 | 5 | **18** | 한국은행 MLS·N2SF로 수요 확실. 예선에 GPU 없으면 증명 불가 |
| **I-14** | 배포 증명 게이트 | 4 | 3 | 3 | 2 | 5 | **17** | 규제 요구 있음. Lakera·HiddenLayer·AISI Inspect 존재, 6일엔 얕음 |
| **I-04** | Agent SOC 드리프트 패치 | 3 | 3 | 2 | 3 | 4 | **15** | Datadog·Prisma AIRS가 관측 선점. 패치 루프만 비어 있음 |
| **I-02** | 방어 계층 2×2 | 3 | 2 | 3 | 3 | 4 | **15** | 연구 질문. 제품 아님, 그래프 1장 가치 |
| **I-05** | 지진 대피소 재배정 | 3 | 3 | 4 | 2 | 2 | **14** | 최근접 안내가 유일 대체재라 빈틈은 실재. 기준선·도로망 없음, GPU 불필요 규모 |
| **I-08** | 제조 SOP 감시 | 4 | 4 | 1 | 1 | 4 | **14** | Pegatron·Foxconn·NVIDIA 블루프린트가 자리 차지. 영상·GPU 필요 |
| **I-10** | 인퍼런스 거버너 | 4 | 4 | 1 | 3 | 2 | **14** | NeMo Switchyard가 실행 단계 라우팅까지 제공. 플러그인이 아니면 재발명 |
| **I-17** | 다양성 실패 탐색 | 3 | 3 | 3 | 3 | 2 | **14** | AI 정부24 2,848만 이용이라는 맥락. OpenShell 무관, 대표성 미검증 |
| **I-19** | 프라이버시 제약 분산 배분 | 3 | 2 | 3 | 2 | 4 | **14** | 평가 구조 정직. 프로토콜 자작·합성 데이터·고객 거리 |
| **N-B** | 연합 면역 시스템 | 2 | 2 | 3 | 2 | 4 | **13** | NVFLARE 의료 사례만. 보안 전이 미검증, 라벨 없음 |
| **I-09** | DUR 검증 | 4 | 3 | 2 | 3 | 1 | **13** | 심평원·필톡·식약처 API 존재. 룰엔진이 코어, 규제 리스크 |
| **I-18** | 리스크 트리아지 점수 | 2 | 2 | 3 | 3 | 2 | **12** | 직접 사례 미발견, 논문 2편 |
| **I-20** | 법령 개정 영향 분석 | 3 | 3 | 2 | 2 | 1 | **11** | 코딧·슈퍼로이어 존재, 골든셋 검증 불가, OpenShell 무관 |
| **I-12** | 실거래 이상거래 | 3 | 2 | 3 | 1 | 1 | **10** | 건별 라벨 비공개, 개인정보·명예훼손, SQL로 충분 |
| **I-06** | 폐기물 배차 | 2 | 3 | 1 | 1 | 1 | **8** | 실제 경로 데이터 부재, 상용 SaaS 다수 |

집계 해석 [추론]: 상위 5개(I-03, I-01, N-C, I-11, I-07)가 전부 보안·DevOps이고, 그중 I-03·I-01·N-C는 **한 제품(A안)의 부품**이다. 공공·제조(I-05/I-08/I-19)는 "빈틈"과 "긴급성"은 있어도 "6일"과 "필연성"에서 깎인다. 이 축 구성 자체가 예선 규칙(6일·OpenShell)에 맞춘 것이므로, **본선(10/7, GPU 지급)에서는 I-16·I-08·I-19의 순위가 크게 오른다**는 점을 함께 적어둔다.

---

## 6. 미확인·리스크 총괄 (사실로 승격 금지)

| # | 항목 | 영향 후보 | 상태 |
|---|---|---|---|
| 1 | NVIDIA LLM Router 블루프린트의 "2026-06-20 deprecated" 문구 — 검색 스니펫에서만 확인, 원문 페이지 재확인 실패 | I-10 | [미확인] |
| 2 | NeMo Switchyard 로드맵에 예산·SLO 인지 라우팅이 있는지 | I-10 | [미확인] |
| 3 | NeMo Evaluator/NAT evaluate가 OpenShell 격리 실행과 통합된 공식 예제 | I-11, I-13 | [미확인] |
| 4 | NAT 프로파일러가 토큰 속도·툴 시그니처를 실시간 스트림으로 노출하는지 | N-A | [미확인] |
| 5 | MCPTox 리포 라이선스, 45개 실서버의 현재 가동 여부 | I-03 | [미확인] |
| 6 | Snyk Evo AI-SPM(2026-03)이 동적 감사·정책 산출까지 하는지 | I-03 | [미확인] |
| 7 | 요양시설의 심평원 DUR 접근 가능 여부(최신 근거 2011년 외 없음) | I-09 | [미확인] |
| 8 | 국토부 이상거래 건별 라벨 공개 여부(보도자료엔 집계만) | I-12 | [미확인] |
| 9 | 코딧(CODIT)의 조문 단위 영향 분석 기능 유무 | I-20 | [미확인] |
| 10 | 법제처 "관련법령 조회"·"조문-용어 연계" API의 전체 법령 커버리지 | I-20 | [미확인] |
| 11 | Nemotron-Personas-Korea 카드의 intended use에 에이전트 QA 포함 여부, 장애 속성 부재 | I-17 | [미확인] |
| 12 | 한국 제조사의 NVIDIA SOP/VSS 채택 사례 | I-08 | [미확인] (직접 사례 미발견) |
| 13 | 서울 보행 도로망·실시간 도로 통제 공개 데이터 | I-05 | [미확인] |
| 14 | 오프라인(Nano) vs 온라인(Ultra) 품질 격차의 독립 벤치마크 | I-16 | [미확인] |
| 15 | IOTAI "0 bytes egressed" 등 벤더 성과 주장, Pegatron 불량률 67%↓ | I-16, I-08 | [벤더주장] |
| 16 | 폭주 에이전트 비용 사고의 규모 — 포럼 보고만 존재 | N-A | [커뮤니티] |
| 17 | "직접 사례 미발견" 후보: I-18, N-B(보안 도메인), I-19(조합), I-05(cuOpt 재난), I-06(cuOpt 폐기물), I-11/I-13/I-02의 OpenShell 결합 사례 | — | 조사 범위 한계 |

공통 리스크 3가지 [추론]:
1. **앱 계층 대체재 포화**: 최소권한·임시 자격증명·예산 캡·MCP 스캔·라우팅이 모두 상용/OSS로 존재. 우리 신규성은 "커널 계층 강제"이며, 이는 앱 계층이 뚫렸을 때만 가치가 드러난다. 데모는 반드시 "앱 계층 방어를 통과한 공격이 커널에서 막히는 장면"을 포함해야 한다.
2. **표준 변동**: MCP(2025-11 스펙 개정), Agent Skills(2025-10 신생), A2A(v0.3, 초기 채택), OpenShell(사전 1.0, NemoClaw alpha), Switchyard(사전 1.0). 6개월 뒤 API가 바뀔 수 있다.
3. **도입 측 냉각**: Gartner의 40% 취소 예측. 구매자에게 "왜 지금"을 설명할 때 리스크 통제 미비가 취소 사유라는 점을 역이용할 수 있다.

---

## 7. Sources (중복 제거, 클러스터별)

**시장 배경**
- https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027
- https://www.gartner.com/en/newsroom/press-releases/2025-08-26-gartner-predicts-40-percent-of-enterprise-apps-will-feature-task-specific-ai-agents-by-2026-up-from-less-than-5-percent-in-2025
- https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
- https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation
- https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation
- https://www.docker.com/products/docker-sandboxes
- https://docs.docker.com/ai/sandboxes
- https://www.docker.com/blog/building-ai-teams-docker-sandboxes-agent
- https://snyk.io/news/snyk-acquires-invariant-labs-to-accelerate-agentic-ai-security-innovation/
- https://www.forbes.com/sites/tonybradley/2026/03/24/snyk-launches-evo-ai-spm-to-govern-autonomous-coding-agents

**NVIDIA 스택 (공식)**
- https://docs.nvidia.com/openshell/sandboxes/policies
- https://docs.nvidia.com/openshell/sandboxes/inference-routing
- https://docs.nvidia.com/nemoclaw/latest/
- https://docs.nvidia.com/nemo/agent-toolkit/latest/build-workflows/a2a-client.html
- https://docs.nvidia.com/nemo/agent-toolkit/latest/workflows/evaluate.html
- https://docs.nvidia.com/skills/agent-skill-trust-pipeline
- https://developer.nvidia.com/blog/nvidia-verified-agent-skills-provide-capability-governance-for-ai-agents/
- https://github.com/NVIDIA/skills/blob/main/skills/skill-card-generator/SKILL.md
- https://github.com/NVIDIA-NeMo/Switchyard
- https://github.com/NVIDIA-AI-Blueprints/llm-router
- https://build.nvidia.com/nvidia/llm-router
- https://developer.nvidia.com/blog/deploying-the-nvidia-ai-blueprint-for-cost-efficient-llm-routing/
- https://docs.nvidia.com/nim/large-language-models/latest/reference/support-matrix.html
- https://github.com/NVIDIA/sop-monitoring-blueprints
- https://blogs.nvidia.com/blog/factory-operations-fox-blueprint-ai-brain/
- https://www.nvidia.com/en-eu/case-studies/pegatron-scales-factory-operations-with-visual-ai-digital-twins
- https://developer.nvidia.com/blog/spotlight-clicoh-accelerates-last-mile-delivery-20x-with-nvidia-cuopt/
- https://blogs.nvidia.com/blog/cuopt-world-record-route
- https://blogs.nvidia.com/blog/federated-learning-nature-medicine
- https://nvidianews.nvidia.com/news/kings-college-london-and-nvidia-build-uks-first-ai-platform-for-nhs-hospitals
- https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea

**MCP 보안·비밀 관리 (I-03, N-C, I-14, I-18)**
- https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks
- https://invariantlabs.ai/blog/mcp-github-vulnerability
- https://invariantlabs.ai/blog/introducing-mcp-scan
- https://github.com/cisco-ai-defense/mcp-scanner
- https://docs.docker.com/ai/mcp-catalog-and-toolkit/catalog
- https://docs.docker.com/ai/mcp-catalog-and-toolkit/mcp-gateway
- https://arxiv.org/abs/2508.14925
- https://github.com/zhiqiangwang4/MCPTox-Benchmark
- https://owasp.org/www-project-mcp-top-10
- https://agentgateway.dev/blog/2026-07-27-credential-injection-ai-agent-egress-cb4a/
- https://www.arcade.dev/get-started/authorization/
- https://learn.microsoft.com/en-us/entra/agent-id/agent-identities
- https://www.hashicorp.com/en/blog/announcing-native-ai-agent-support-in-hashicorp-vault
- https://1password.com/press/2025/april/agentic-ai
- https://www.okta.com/products/govern-ai-agent-identity
- https://www.nist.gov/itl/ai-risk-management-framework
- https://www.iso.org/standard/42001
- https://www.aisi.gov.uk/blog/the-inspect-sandboxing-toolkit-scalable-and-secure-ai-agent-evaluations
- https://www.hiddenlayer.com/solutions/agentic-mcp-security
- https://www.lakera.ai/ai-red-teaming-services
- https://docs.lakera.ai/docs/agent-security/risk-assessment
- https://blogs.cisco.com/news/fortifying-the-future-of-security-for-ai-cisco-announces-intent-to-acquire-robust-intelligence
- https://www.promptfoo.dev/docs/red-team
- https://arxiv.org/abs/2510.15739
- https://arxiv.org/html/2607.09586v1

**권한·런타임 (I-01, I-04, I-15, N-A, I-16)**
- https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-policy-generation.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/understanding-agent-identities.html
- https://code.claude.com/docs/en/sandboxing
- https://www.sysdig.com/blog/container-drift-detection-with-falco
- https://investors.datadoghq.com/news-releases/news-release-details/datadog-expands-llm-observability-new-capabilities-monitor
- https://www.paloaltonetworks.com/ai-security/prisma-airs
- https://zenity.io/platform
- https://a2a-protocol.org/v0.3.0/specification
- https://developer.hashicorp.com/vault/tutorials/auth-methods/secure-ai-agent-communication-a2a-vault-kubernetes
- https://auth0.com/blog/auth0-token-vault-secure-token-exchange-for-ai-agents/
- https://techcommunity.microsoft.com/blog/microsoft-entra-blog/announcing-microsoft-entra-agent-id-secure-and-manage-your-ai-agents/3827392
- https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year
- https://galileo.ai/blog/google-agent2agent-a2a-protocol-guide
- https://community.openai.com/t/how-to-cap-cost-to-prevent-api-cost-from-blowing-up/1029082
- https://community.openai.com/t/how-are-you-handling-runaway-agent-costs/1383593
- https://docs.litellm.ai/docs/proxy/users
- https://www.etnews.com/20260212000082
- https://www.newstomato.com/readnews.aspx?no=1294190
- https://www.boannews.com/news/articleView.html?idxno=135396
- https://www.iotai.com.au/services/sovereign-ai

**평가·CI·스킬 (I-11, I-13, I-02, I-17)**
- https://www.promptfoo.dev/docs/integrations/github-action
- https://github.com/promptfoo/promptfoo
- https://www.daytona.io/
- https://arxiv.org/pdf/2506.07982
- https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/
- https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- https://github.com/OSU-NLP-Group/SkillWeaver
- https://arxiv.org/abs/2305.16291
- https://docs.openhands.dev/overview/skills
- https://securitylabs.datadoghq.com/articles/malicious-skills-supply-chain-risks-in-coding-agents-with-dynamic-context
- https://agentdojo.spylab.ai/results/
- https://github.com/ethz-spylab/agentdojo
- https://arxiv.org/abs/2503.18813
- https://arxiv.org/abs/2404.13208
- https://arxiv.org/html/2606.26479v1
- https://www.anthropic.com/research/prompt-injection-defenses
- https://www.mois.go.kr/frt/bbs/type010/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000008&nttId=124243
- https://biz.chosun.com/topics/topics_social/2026/06/30/TC7LJFWMQZCTPPVFZGH6IBE3D4/
- https://www.coval.dev/

**공공·산업 (I-05, I-06, I-08, I-19, N-B)**
- https://data.seoul.go.kr/dataList/OA-21063/S/1/datasetView.do
- https://www.data.go.kr/data/15153506/openapi.do
- https://news.seoul.go.kr/safe/archives/512222
- https://www.incheon.go.kr/safe/SAFE010201
- https://www.sciencedirect.com/science/article/pii/S0305054824002569
- https://arxiv.org/pdf/2111.13326
- https://www.ccnnews.co.kr/news/articleView.html?idxno=380423
- https://www.data.go.kr/data/15061767/fileData.do
- https://www.businesswire.com/news/home/20260602068205/en/Foxconn-Boosts-Production-Throughput-With-DeepHow-Live-SOP-Verification-Powered-By-NVIDIA
- https://www.korea.kr/briefing/pressReleaseView.do?newsId=156514448
- https://internationaldataspaces.org/catena-x-with-gaia-x-will-data-space-be-the-word-of-2021
- https://pmc.ncbi.nlm.nih.gov/articles/PMC9157510/
- https://dl.acm.org/doi/full/10.1145/3731596
- https://www.anomali.com/glossary/information-sharing-and-analysis-center-isac

**데이터·도메인 (I-07, I-10, I-09, I-12, I-20)**
- https://www.nist.gov/news-events/news/2026/04/nist-updates-nvd-operations-address-record-cve-growth
- https://www.oversight.gov/reports/evaluation-nists-management-national-vulnerability-database
- https://www.endorlabs.com/use-case/sca-with-reachability
- https://www.endorlabs.com/learn/reachability-analysis
- https://docs.endorlabs.com/scan/sca/reachability-analysis/index
- https://docs.snyk.io/scan-fix-and-prevent/fix/prioritize-issues-for-fixing/reachability-analysis
- https://google.github.io/osv-scanner/experimental/
- https://www.first.org/epss
- https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- https://www.prophetsecurity.ai/
- https://github.com/lm-sys/RouteLLM
- https://openrouter.ai/docs/guides/routing/routers/auto-router
- https://www.dailypharm.com/user/news/91591
- https://www.korea.kr/news/policyNewsView.do?newsId=148945126
- https://play.google.com/store/apps/details?id=com.pmatch.pilltalk
- https://www.data.go.kr/data/15059486/openapi.do
- https://www.data.go.kr/data/15089525/fileData.do
- https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95091558&lcmspage=1
- https://www.molit.go.kr/USR/NEWS/m_71/dtl.jsp?id=95091935&lcmspage=1
- https://www.arunews.com/news/articleView.html?idxno=50806
- https://www.joongang.co.kr/article/25309680
- https://rt.molit.go.kr/
- https://open.law.go.kr/LSO/openApi/guideList.do
- https://open.law.go.kr/LSO/information/guide.do
- https://thecodit.com/kr-ko
- https://www.venturesquare.net/1042173
- https://superlawyer.co.kr/

---

*작성: 2026-09-23 09:30 KST. 조사 시점 이후 벤더 기능·표준 스펙이 바뀔 수 있다. 특히 Switchyard·OpenShell·NemoClaw는 사전 1.0/alpha이므로 착수 시 재확인할 것.*
