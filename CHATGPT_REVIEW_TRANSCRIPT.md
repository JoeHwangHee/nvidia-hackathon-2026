---
title: "CHATGPT REVIEW TRANSCRIPT — 아이디어 23종 교차 비평 전문"
doc_type: transcript
version: 1.0
created_at: 2026-09-23T00:10+09:00
source: "chatgpt.com 임시 채팅 (GPT-5.6 Sol, 추론 강도 '매우 높음'), 2026-09-22 23:20 ~ 2026-09-23 00:05 KST"
companion_docs:
  - IDEA_EXPANSION_CHATGPT_REVIEW.md   # 정리본 (이 전문의 요약·검증·태깅)
---

# CHATGPT REVIEW TRANSCRIPT

> **READ THIS FIRST (for agents)**
> - 이 문서는 ChatGPT 응답을 **가공 없이** 옮긴 원문이다. ChatGPT의 주장은 전부 `[CHATGPT]`이며, 검증 결과는 `IDEA_EXPANSION_CHATGPT_REVIEW.md` 섹션 9에만 있다.
> - ChatGPT는 웹 검색을 병행했고 응답 중 "NVIDIA Docs +1", "GitHub +2" 같은 표기는 ChatGPT UI의 인용 배지가 텍스트로 남은 것이다. 링크 자체는 보존되지 않았다.
> - 임시 채팅이라 사용자 ChatGPT 기록에는 존재하지 않는다. **이 파일이 유일한 사본**이다.
> - 응답 안의 예시 숫자(ASR 48%→4%, 62%→79% 등)는 ChatGPT가 든 **가상의 예시**다. 실측 아님. 제출서에 쓰지 말 것.


---

## 턴 1 — 컨텍스트 설정

### 내가 보낸 프롬프트

```text
당신은 해커톤 심사위원 겸 냉정한 기술 리뷰어 역할입니다. 앞으로 여러 턴에 걸쳐 제가 아이디어를 4개씩 보낼 테니, 각 아이디어를 아래 기준으로 비평해 주세요. 먼저 이 컨텍스트를 읽고 "준비됨"이라고만 짧게 답하세요.

[대회] NVIDIA x 패스트캠퍼스 Korea Agentic AI Hackathon 2026. 온라인 예선 마감 2026-09-28 23:59 KST (오늘 기준 D-6). 2~5인 팀. 예선 제출물 = GitHub 링크가 적힌 PDF 1개 + Problem(300자) + Solution(500자) + Tech Stack(제한 없음). 영상/배포 불필요, 코드가 유일한 증거.
[필수 조건] 지정 교육 미션 "Securing Agents with NemoClaw and OpenShell"(NVIDIA DLI) 선행 후, build.nvidia.com의 "Skill API"(실체 = NVIDIA Agent Skills(SKILL.md 지침 패키지, npx skills add NVIDIA/skills) + NIM 추론 API integrate.api.nvidia.com)를 활용한 데모 프로젝트. 주제 자유.
[공식 채점 항목 순서] 1) NVIDIA Agent 기술 활용 심도 2) 실용성·산업가치·혁신성 3) 완성도 4) 커스터마이징·독창성. 배점 미공개.
[우리 팀 내부 규범] "숫자로 증명 못 하는 아이디어는 채택하지 않는다." 하드 게이트: G1 6일 내 baseline X → ours Y 숫자 산출 가능 / G2 NemoClaw 또는 OpenShell이 아키텍처 코어 / G3 NVIDIA 기술 3종 이상 실제 호출 / G4 GitHub README만으로 재현 / G5 개인편의가 아닌 제약조건 명확한 산업·공공 문제 / G6 승인 2주 걸리는 데이터 금지. 정량 지표 없으면 총점 상한 55/100.
[NVIDIA 스택] OpenShell(커널 샌드박스: Landlock/seccomp/netns+OPA 프록시, YAML 정책, allow/deny 감사 로그), NemoClaw(OpenClaw/Hermes/LangChain 하네스 번들, alpha), Nemotron 3 Nano 30B/Super 120B/Ultra 550B + 3.5 Lightning, NIM API, NeMo Agent Toolkit(nvidia-nat: MCP/A2A/프로파일러/평가), NeMo Guardrails, NemoGuard NIM, NeMo Retriever, cuOpt, DeepStream/VSS, Nemotron Speech, nvflare, Agent Skills 363종(rag-eval, cuopt-*, deepstream-sop, nemotron-policy-generator, data-designer 등). 본선 10팀에 Brev L40S 48GB 1장 $1,000 크레딧. 우승 상품 DGX Spark + NVIDIA 공식 GitHub Recipe 등재.
[선행 대회 시그널] 직전 NVIDIA 서울 해커톤 심사평: "정성 평가뿐 아니라 정량 평가까지 보여준 팀"이 우승. 2025 NeMo Agent Toolkit 해커톤 1위는 NVIDIA 기술 3종 이상 결합한 유일한 팀. 개인 비서·여행류는 3위 이상 없음.
[사용 가능 데이터] 서울열린데이터광장(즉시, 무제한), 기상청 단기예보(자동승인 10k/일), 국토부 실거래가(자동승인), 식약처 e약은요(개발 자동승인), KOSIS, NVD CVE API(공개, 키 시 30초당 50회), Nemotron-Personas-Korea(HF, 600만건), 벤치마크 AgentDojo(MIT, 97 task/629 security case, 지표 Benign Utility/Utility Under Attack/Targeted ASR), MCPTox(AAAI26, 실제 MCP 서버 45개 기반 1,348 툴 포이즈닝 케이스), BFCL V4(Apache-2.0, 비용·지연 표준 산출), tau2-bench(MIT). 국가법령정보 API는 승인 기간 미확인. AI Hub는 2주 심의라 금지.

[비평 형식 — 아이디어마다 반드시 이 5개]
(1) 페인포인트 실재성 1~5점 + 근거 한 줄 (실제 현장에서 돈/시간/사고가 발생하는가)
(2) baseline·지표 타당성 1~5점 + 제안한 지표의 허점 + 더 나은 지표가 있으면 구체적으로
(3) NVIDIA 스택 심도 1~5점 (특히 OpenShell/NemoClaw가 장식인지 코어인지)
(4) 6일 완주 리스크 상/중/하 + 가장 먼저 터질 병목 1개
(5) 이 아이디어를 살리려면 바꿔야 할 것 1개 (한 문장)
마지막에 4개 중 순위와 "심사위원이 5분 피칭에서 가장 기억할 한 문장"을 각각 써주세요. 칭찬보다 반박을 우선하세요. 근거 없는 낙관은 금지.
```

### ChatGPT 응답

> 준비됨

---

## 턴 2 — 배치 1/5 보안·정책 계열 (I-01~I-04)

### 내가 보낸 프롬프트

```text
[배치 1/5 — 보안·정책 계열]

I-01. 에이전트 최소권한 정책 자동생성 + 레드팀 검증기
- 페인포인트: NemoClaw/OpenClaw 같은 자율 에이전트를 실무에 붙이려면 OpenShell 정책 YAML(파일/네트워크/바이너리/L7 경로)을 사람이 손으로 쓴다. 너무 빡빡하면 에이전트가 망가지고 느슨하면 유출. 정답도 검증법도 없음.
- 루프: ① Profiler Agent가 대상 에이전트를 OpenShell에서 실행해 실제 접근 패턴(감사 로그) 수집 → ② Policy Agent(Nemotron + nemotron-policy-generator 스킬)가 최소권한 YAML 초안 생성 → ③ Red-Team Agent가 자격증명 탈취/외부 유출/임의 실행 시나리오 N종 주입 → 뚫리면 ②에 피드백, 수렴까지 반복.
- 데이터: 자체 생성(감사 로그가 곧 평가 데이터). 외부 승인 의존 0.
- baseline: 기본 정책(deny-by-default 없음) / 과도 제한 정책 / 수작업 정책.
- 지표: 공격 차단율, 오탐률(정상 작업 차단), 정책 작성 시간, 수렴 라운드 수, 기능 보존율.
- 스택: OpenShell(코어), NemoClaw, Nemotron Nano/Ultra, nvidia-nat, Guardrails+NemoGuard, Agent Skills 자작.

I-02. 방어 계층별 효과 정량 비교기 — "프롬프트 방어 vs 커널 봉쇄" (AgentDojo 위에서)
- 페인포인트: 실무자들이 "가드레일만으로 충분한가, 샌드박스가 정말 필요한가"에 데이터 없이 논쟁. 벤더 주장만 있음.
- 방법: AgentDojo(MIT, 97 task/629 security case)의 workspace/slack/travel/banking 스위트에서 Nemotron 에이전트를 4조건으로 실행 — (a) 무방어 (b) NeMo Guardrails+NemoGuard만 (c) OpenShell 정책만(도구 실행을 실제 샌드박스 프로세스로 매핑) (d) 둘 다. 각 조건에서 AgentDojo 공식 3지표 산출.
- baseline: (a) 무방어 + 논문 공개 수치(GPT-4o targeted ASR 47.69%).
- 지표: Benign Utility / Utility Under Attack / Targeted ASR, 그리고 조건별 지연·비용(nvidia-nat 프로파일러). 파레토 프론티어 그림.
- 스택: OpenShell(코어), Nemotron 3종 비교, Guardrails, NemoGuard NIM, nvidia-nat 프로파일러.
- 허점 우려: AgentDojo 도구는 파이썬 함수 시뮬레이션이라 "커널 정책"이 실제로 개입할 지점이 없을 수 있음. 도구를 실제 파일/HTTP 호출로 바꾼 "AgentDojo-OpenShell 어댑터"를 만들어야 함.

I-03. MCP 서버 공급망 감사관 (MCP Supply-Chain Auditor)
- 페인포인트: MCP 서버가 폭증하는데 tools/list의 description은 검증 안 된 프롬프트 표면(Tool Poisoning). MCPTox 논문: 20개 LLM 에이전트 중 최고 거부율이 3% 미만. 기업이 MCP 서버를 승인할 근거가 없음.
- 방법: 에이전트가 후보 MCP 서버를 OpenShell 샌드박스에 설치 → (정적) Nemotron이 tool description을 분류 → (동적) 샌드박스에서 실행하며 실제 파일/네트워크 행동을 감사 로그로 관측 → 선언 능력 vs 실측 행동 diff → skill card(skill-card-generator) + 해당 서버 전용 최소권한 정책 YAML 자동 발급.
- 데이터: MCPTox 1,348 케이스(45개 실제 MCP 서버) = 골든셋. 팀이 통제.
- baseline: 무방어 에이전트의 TPA 성공률(논문 수치 재현) / 정적 스캐너(mcp-scan).
- 지표: TPA 성공률(무방어 → ours), 포이즈닝 탐지 F1, 정상 서버 오탐률, 서버당 감사 소요 시간.
- 스택: OpenShell(코어), NemoClaw(nemo-retriever-mcp 등 MCP 클라이언트), Nemotron, nvidia-nat MCP, skill-card-generator, Guardrails.

I-04. 에이전트 SOC — 감사 로그 이상탐지 메타 에이전트
- 페인포인트: 에이전트가 여러 대 돌면 OpenShell allow/deny 로그가 쏟아지는데 사람이 못 본다. "정상 작업 중 갑자기 ~/.ssh 읽기 시도 급증" 같은 신호를 놓침. 보안팀은 에이전트 플릿 모니터링 도구가 없음.
- 방법: 감사 로그 스트림을 Nemotron Nano가 실시간 요약/분류(권한상승 시도, 유출 시도, 정책 드리프트) → 임계 시 Ultra가 원인 분석 + 차단 정책 패치 제안 → 사람 승인 게이트 → 정책 핫리로드. 대시보드(경로×시간 히트맵).
- 데이터: 자체 생성 정상 트래픽 + AgentDojo/MCPTox 공격 트래픽을 주입한 인시던트 N건.
- baseline: 규칙 기반 임계값 알림(deny 건수 > k).
- 지표: 인시던트 탐지 F1, 평균 탐지 시간(MTTD), 알림 노이즈 비율, 제안 정책 패치의 차단 성공률.
- 스택: OpenShell(코어, 감사 로그+정책 핫리로드), NemoClaw, Nemotron Nano↔Ultra 라우팅, nvidia-nat, Guardrails.

위 5개 형식으로 각각 비평하고, 마지막에 4개 순위 + 기억할 한 문장.
```

### ChatGPT 응답

> 전체적으로 보면 I-03과 I-01이 제출 후보, I-02는 연구적으로 매력적이지만 6일 일정에 위험하고, I-04는 가장 만들기 쉽지만 가장 쉽게 “LLM 붙인 SOC”로 보입니다. 특히 심사위원 입장에서는 외부 골든셋 + NVIDIA 기술이 실제 방어 결과를 바꾸는 그림이 가장 강합니다.
>
> I-01. 에이전트 최소권한 정책 자동생성 + 레드팀 검증기
>
> (1) 페인포인트 실재성: 5/5
>
> 실제 문제다. 에이전트에게 shell/file/network 권한을 주는 순간 최소권한 정책 작성은 사람이 해야 하고, 정상 기능과 보안 사이의 trade-off도 명확하다.
>
> 다만 현재 설명에는 한 가지 함정이 있다. “정답 정책이 없다”는 것이 제품의 페인포인트인 동시에 평가의 약점이다. 심사위원이 “그래서 네 정책이 최소권한이라는 걸 어떻게 증명했나?”라고 물으면 현재 지표만으로는 부족하다.
>
> (2) baseline·지표 타당성: 4/5
>
> 현재 지표 중 공격 차단율 + 기능 보존율 조합은 좋다. 하지만 공격 차단율만 높이려면 아무것도 못 하게 하면 된다. 반대로 기능 보존율만 높이면 allow *가 이긴다.
>
> 특히 정책 작성 시간은 해커톤에서 약한 지표다. 자동화가 수작업보다 빠른 건 당연하기 때문이다.
>
> 더 강한 평가는 다음처럼 만들어야 한다.
>
> Benign Task Success Rate: 정상 작업 성공률
>
> Attack Success Rate: 공격 성공률
>
> Privilege Surface Reduction: baseline 대비 허용 file/path/domain/binary/action 개수 감소율
>
> Held-out Utility: 정책 생성에 사용하지 않은 정상 시나리오에서 성공률
>
> Regression after patch: 레드팀 패치 후 새롭게 깨진 정상 task 비율
>
> 예를 들어:
>
> 정상 기능 성공률 ≥95%를 유지하면서 허용 권한 표면 68% 감소, 공격 ASR 41%→3%.
>
> 이게 작성 시간 20분→30초보다 훨씬 강하다.
>
> (3) NVIDIA 스택 심도: 5/5
>
> 네 개 중 OpenShell을 가장 자연스럽게 코어로 쓰는 아이디어 중 하나다.
>
> Profiler → OpenShell audit → Nemotron policy generation → OpenShell enforcement → Red-team → policy refinement라는 폐루프에서 OpenShell을 빼면 제품 자체가 성립하지 않는다.
>
> NemoClaw 역시 단순 orchestration 장식이 아니라 여러 agent의 반복 루프를 설명할 수 있다.
>
> 주의할 것은 Guardrails/NemoGuard까지 억지로 넣는 것. 공격 입력 filtering 정도의 명확한 역할이 없다면 오히려 “NVIDIA 기술 개수 채우기”로 보인다. OpenShell + Nemotron + NAT + Agent Skill만으로도 충분히 깊다.
>
> (4) 6일 완주 리스크: 중
>
> 가장 먼저 터질 병목은 대표성 있는 정상 행동 trace 확보다.
>
> 한 번 실행한 workflow의 trace로 정책을 만들면 그 정책은 최소권한이 아니라 그냥 training trace에 overfit된 allowlist다.
>
> 그래서 다양한 workload를 하지 말고, 한 가지 agent를 깊게 해야 한다.
>
> 예:
>
> code maintenance agent
>
> repo 읽기
>
> 테스트 실행
>
> 특정 API 접근
>
> 파일 수정
>
> git diff 생성
>
> 정상 시나리오 20개 / held-out 10개 / 공격 30개 정도가 오히려 설득력이 있다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> “범용 정책 생성기”를 버리고 하나의 실제 에이전트 workload에 대해 train/held-out 정상 task와 공격 task를 분리하여 최소권한을 수치로 증명하라.
>
> I-02. 방어 계층별 효과 정량 비교기
>
> (1) 페인포인트 실재성: 4/5
>
> 질문 자체는 매우 좋다.
>
> “Prompt-level defense가 에이전트를 안전하게 만드는가, 아니면 sandbox가 필요한가?”
>
> 실무 보안 설계에서 실제로 중요한 질문이다.
>
> 다만 이것은 제품 pain보다 research question에 가깝다. 즉 산업가치는 있지만 결과물이 “벤치마크 논문 데모”처럼 보일 가능성이 있다.
>
> 우승작이 product형이어야 하는 것은 아니지만 채점 2번이 실용성·산업가치라면 설명을 잘 해야 한다.
>
> (2) baseline·지표 타당성: 4/5
>
> 2×2 ablation은 매우 좋다.
>
> 조건	Prompt defense	Kernel enforcement
> A	X	X
> B	O	X
> C	X	O
> D	O	O
>
> 이 그림 하나로 발표가 된다.
>
> 문제는 이미 본인이 정확히 짚은 AgentDojo/OpenShell semantic mismatch다.
>
> Python 함수인 tool을 억지로 sandbox 안에서 실행시키면 원래 AgentDojo benchmark와 다른 시스템이 된다. 그러면 공개 GPT-4o 수치와 직접 비교도 약해진다.
>
> 그리고 더 중요한 문제 하나가 있다.
>
> Guardrail과 OpenShell은 같은 실패를 막는 기술이 아니다.
>
> Prompt defense는:
>
> agent가 공격자의 의도를 따르지 않도록 한다.
>
> OpenShell은:
>
> agent가 이미 공격당했어도 실제 side effect를 못 일으키게 한다.
>
> 따라서 Targeted ASR 하나로 두 기술을 비교하면 개념적으로도 손실이 있다.
>
> 더 좋은 지표는 둘을 나누는 것이다.
>
> Intent Compromise Rate: 모델이 악의적 행동을 시도했는가
>
> Side-effect Completion Rate: 실제 피해 행동이 완료됐는가
>
> Benign Utility
>
> Utility Under Attack
>
> P50/P95 latency overhead
>
> cost/task
>
> 그리고 가장 강한 결과는 이런 형태다.
>
> Guardrails reduced malicious intent by X%, OpenShell reduced successful harmful side effects by Y%, and combining them reduced end-to-end attack success by Z%.
>
> (3) NVIDIA 스택 심도: 5/5 또는 2/5
>
> 구현 방식에 따라 극단적으로 갈린다.
>
> OpenShell 안에서 단순히 Python benchmark runner만 실행한다면 2/5다. 샌드박스를 “사용했다”일 뿐이다.
>
> 실제 file/network/process side effect로 tool을 mapping해 OpenShell 정책이 공격의 최종 실행을 차단한다면 5/5다.
>
> 즉 이 아이디어는 구현 결과가 스택 심도 점수를 결정한다.
>
> (4) 6일 완주 리스크: 상
>
> 가장 먼저 터질 병목:
>
> AgentDojo → real-side-effect OpenShell adapter.
>
> 97 task를 제대로 변환하려고 하면 높은 확률로 망한다.
>
> 더구나 benchmark compatibility 검증, 4가지 방어 조건, 모델 여러 종 비교, profiler까지 하면 실험 matrix가 폭발한다.
>
> 97 × 629 × 4 × 3 model 식으로 생각하기 시작하면 이미 위험하다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> AgentDojo 전체 이식을 포기하고 공격 유형 2~3개·task subset만 real side-effect adapter로 구현해 “모델 compromise와 실제 피해의 차이”를 증명하라.
>
> I-03. MCP 서버 공급망 감사관
>
> (1) 페인포인트 실재성: 5/5
>
> 네 개 중 산업 문제 설명이 가장 쉽다.
>
> 개발자에게 이렇게 말하면 끝난다.
>
> “npm package는 설치 전에 검사하는데, AI agent에게 명령을 내리는 MCP tool description은 왜 믿습니까?”
>
> Tool description이 모델의 행동을 바꿀 수 있고, MCP server가 실제 file/network 접근도 수행하므로 supply-chain이라는 framing이 자연스럽다.
>
> 기업 승인 프로세스와도 연결하기 쉽다.
>
> (2) baseline·지표 타당성: 5/5
>
> 외부 benchmark가 있는 것이 I-01 대비 결정적 장점이다.
>
> MCPTox 1,348개를 사용하면 최소한:
>
> 우리가 만든 공격을 우리가 잘 막았습니다.
>
> 라는 self-evaluation 공격에서 벗어난다.
>
> 다만 현재 서로 다른 두 문제를 섞고 있다.
>
> Tool poisoning 탐지
>
> Runtime capability auditing
>
> MCPTox label이 1번의 gold label은 줄 수 있어도 이 MCP 서버는 /etc/passwd를 읽어야 하는가? 같은 OS-level capability의 정답까지 제공하는 것은 아니다.
>
> 따라서 평가도 분리해야 한다.
>
> A. MCPTox:
>
> poisoning detection precision/recall/F1
>
> attack success rate
>
> benign utility
>
> B. 실제 runnable MCP subset:
>
> undeclared resource access detection
>
> egress blocking rate
>
> benign tool success
>
> policy generation accuracy
>
> audit time/server
>
> 그리고 F1 하나보다는 보안에서는:
>
> Recall at 1% FPR
>
> 같은 수치가 더 좋다.
>
> 정상 MCP를 다 막아버리는 detector는 쓸모없기 때문이다.
>
> (3) NVIDIA 스택 심도: 5/5
>
> 경쟁력이 매우 높다.
>
> 흐름이 자연스럽다.
>
> MCP server
> → OpenShell isolation
> → runtime audit
> → Nemotron semantic inspection
> → capability diff
> → 최소권한 OpenShell policy
> → 재실행 validation
>
> OpenShell을 제거하면 dynamic audit와 enforcement라는 핵심이 사라진다.
>
> 또한 Agent Skills를 사용해서 최종 결과물을 machine-readable security skill card로 만든다면 대회 필수 조건과도 연결하기 쉽다.
>
> NAT의 MCP integration도 매우 자연스럽다.
>
> (4) 6일 완주 리스크: 중~상
>
> 가장 먼저 터질 병목은:
>
> “45개 실제 MCP 서버를 내가 정말 실행할 수 있는가?”
>
> 실제 MCP 서버는 dependency, API key, OAuth, database, 환경변수 문제 등이 계속 나온다.
>
> 여기서 모든 시간을 잃을 가능성이 있다.
>
> 따라서 45개 동적 실행은 금지해야 한다.
>
> MCPTox 1,348개는 description-level 평가에 쓰고, dynamic audit은 로컬에서 reproducible한 5~10개 서버만 사용하는 편이 안전하다.
>
> 악성 fixture MCP도 2~3개 직접 만들면 된다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> MCPTox 1,348개는 정적 poisoning benchmark로 전량 사용하고, 동적 OpenShell 감사는 재현 가능한 MCP 5~10개로 분리하라.
>
> 이렇게 하면 범위가 갑자기 현실적으로 변한다.
>
> I-04. 에이전트 SOC
>
> (1) 페인포인트 실재성: 4/5
>
> 문제 자체는 존재한다.
>
> agent fleet이 늘어나면 file/network/process audit을 사람이 보는 것은 불가능하다.
>
> 다만 다른 세 아이디어와 비교하면 pain의 시점이 조금 미래에 있다.
>
> 현재 많은 기업이 이미 겪는 문제라기보다는 agent deployment가 확대될수록 커질 문제다.
>
> 그리고 “로그 너무 많음 → AI로 SOC”는 이미 익숙한 패턴이라 혁신성 설명이 어렵다.
>
> (2) baseline·지표 타당성: 3/5
>
> 여기가 가장 약하다.
>
> deny count > k라는 baseline은 너무 허술하다.
>
> 심사위원 입장에서는:
>
> “그렇게 약한 baseline을 이기는 게 무슨 의미죠?”
>
> 라고 할 수 있다.
>
> 적어도 다음 baseline이 필요하다.
>
> threshold rule
>
> simple statistical anomaly detection
>
> ours
>
> 또한 자체 생성 incident로 F1을 측정하면 dataset 설계에 따라 점수가 크게 바뀐다.
>
> MTTD도 replay 속도를 마음대로 정하면 의미가 약하다.
>
> 더 좋은 지표는:
>
> Precision / Recall / F1
>
> false alerts / 1,000 events
>
> attack event 발생 → 최초 detection까지 event count
>
> P95 detection latency
>
> policy patch 이후 attack block rate
>
> patch 이후 benign regression rate
>
> 특히 마지막이 중요하다.
>
> Ultra가 만든 정책이 공격은 막았지만 정상 agent도 죽여버리면 실패다.
>
> (3) NVIDIA 스택 심도: 4/5
>
> OpenShell audit stream을 실제 input으로 사용하면 코어성이 있다.
>
> Nano → Ultra escalation routing도 시연하기 좋다.
>
> 하지만 지금 구조는 자칫하면:
>
> 로그 → LLM → 요약
>
> 이라는 흔한 GenAI SI 프로젝트로 보인다.
>
> 또 모든 log event를 Nano에게 넣는 방식은 아키텍처적으로도 별로다.
>
> 실전이라면 structured filter/windowing → anomaly candidate → Nano → Ultra 순서가 합리적이다.
>
> NVIDIA 심도를 보여주려면 탐지보다 정책 remediation closed-loop를 강조해야 한다.
>
> (4) 6일 완주 리스크: 중
>
> 구현 자체는 네 개 중 오히려 쉽다.
>
> 가장 먼저 터질 병목은 신뢰할 수 있는 labeled incident dataset이다.
>
> UI와 대시보드 만드는 데 시간을 쓰기 시작하면 더 위험하다.
>
> 히트맵보다 evaluation harness가 중요하다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> 범용 “Agent SOC”를 버리고 “OpenShell policy drift 탐지 → 자동 패치 → benign regression 검증”이라는 하나의 closed-loop 문제로 좁혀라.
>
> 4개 순위
> 1위 — I-03 MCP Supply-Chain Auditor
>
> 가장 균형이 좋다.
>
> 외부 benchmark가 있고, 산업 pain도 설명하기 쉽고, OpenShell이 진짜 코어이며, 최종 산출물도 명확하다.
>
> 특히 해커톤에서 강한 그림은:
>
> 1,348개 외부 공격 데이터 → 탐지 수치 → 실제 MCP sandbox 실행 → 위험 행동 차단 → 최소권한 policy 자동 발급
>
> 이다.
>
> 유일한 위험은 scope 폭발이다.
>
> 2위 — I-01 최소권한 정책 자동생성 + 레드팀
>
> 기술적으로는 I-03보다 NVIDIA Agent 기술 활용이 더 아름답다.
>
> 그리고 “observe → generate → attack → repair” loop가 데모에서 굉장히 좋다.
>
> 하지만 외부 gold set이 없기 때문에 평가 신뢰도에서 I-03에 밀린다.
>
> 이 문제만 해결하면 1위 후보가 된다.
>
> 3위 — I-02 Prompt Defense vs Kernel Containment
>
> 가장 연구적으로 흥미롭고 그래프 한 장이 가장 강력할 아이디어다.
>
> 하지만 현재 범위 그대로면 6일 프로젝트가 아니라 benchmark engineering 프로젝트가 된다.
>
> 제대로 성공하면 1~2위급이지만, 실패 확률 때문에 3위다.
>
> 특히 이 아이디어는 “Guardrail은 compromise를 줄이고 sandbox는 consequence를 줄인다”로 framing을 바꾸면 훨씬 좋아진다.
>
> 4위 — I-04 Agent SOC
>
> 완주 가능성은 높지만 차별화가 가장 약하다.
>
> “LLM SOC”라는 기존 카테고리 안으로 빨려 들어갈 위험이 크다.
>
> 정책 drift와 remediation으로 좁히지 않으면 NVIDIA Agentic AI 해커톤보다는 일반 observability 데모처럼 보일 가능성이 있다.
>
> 심사위원이 5분 피칭에서 기억할 한 문장
>
> I-01
>
> “우리는 에이전트가 실제로 사용한 권한만 관찰하고, 공격으로 깨뜨리고, 다시 줄여서 정상 기능은 유지하면서 최소권한 정책을 자동으로 수렴시킵니다.”
>
> I-02
>
> “Guardrail은 에이전트가 공격당할 확률을 낮추고, OpenShell은 공격당한 에이전트가 실제 피해를 만들 확률을 낮춘다는 것을 같은 공격셋에서 숫자로 분리했습니다.”
>
> 이 문장은 꽤 강하다. 현재 I-02의 가장 좋은 포지셔닝이다.
>
> I-03
>
> “MCP 서버가 무엇을 할 수 있다고 말하는지가 아니라, 샌드박스에서 실제로 무엇을 하는지 보고 신뢰 여부를 결정합니다.”
>
> 네 개 중 가장 기억에 남을 가능성이 높은 문장이다.
>
> I-04
>
> “에이전트가 평소와 다른 권한을 쓰기 시작하면 탐지만 하는 것이 아니라, 원인을 찾고 최소권한 패치를 만든 뒤 정상 기능이 깨지지 않는지까지 검증합니다.”
>
> 현재 배치에서 하나만 제출 후보로 남긴다면
>
> I-03을 primary, I-01을 backup으로 잡겠다.
>
> 단, I-03에서 “45개 서버 전부 동적 실행”은 지금 즉시 버리는 게 좋다. 그 욕심 하나 때문에 6일 완주 프로젝트가 dependency-debugging 프로젝트로 바뀔 가능성이 높다.

---

## 턴 3 — 배치 2/5 산업·공공 데이터 계열 (I-05~I-08)

### 내가 보낸 프롬프트

```text
[배치 2/5 — 산업·공공 데이터 계열]

I-05. 서울 재난 대피 경로·수용 배분 최적화 에이전트
- 페인포인트: 지진·폭염·한파 시 시민이 최근접 대피소로 몰려 특정 대피소 수용 초과, 취약계층(고령·장애) 이동거리 불균형. 지자체 재난 담당자는 대피 배분을 경험칙으로 함.
- 데이터: 서울시 지진옥외대피소(OA-21063, 공공누리 1유형, 좌표·면적 포함, 매일 갱신) + 무더위쉼터/한파쉼터 + 행정동별 주민등록인구(서울열린데이터/KOSIS) + 기상청 단기예보(폭염/한파 트리거). 전부 즉시 사용 가능.
- 방법: ① 기상청 예보/지진 시나리오 입력 → Trigger Agent가 재난 유형·대상 지역 판정 → ② Constraint Agent(cuopt-numerical-optimization-formulation 스킬)가 자연어 제약(취약계층 우선, 도로 통제, 수용 한도)을 수리 모델로 변환 → ③ cuOpt로 인구 → 대피소 배정(capacitated assignment / VRP) → ④ Explainer Agent가 파레토(총 이동거리 vs 최대 이동시간 vs 초과 수용)를 설명. 전 과정 OpenShell 샌드박스, egress는 data.seoul.go.kr / apis.data.go.kr만 허용(정책 YAML 산출물).
- baseline: 최근접 대피소 greedy 배정(현행 관행 근사).
- 지표: 수용 초과 인원 수(baseline → 0), 최대 대피 이동시간(makespan) 감소%, 총 이동거리, 취약계층 평균 이동거리, cuOpt vs OR-Tools CPU solve time, 제약 추출 정확도(골든셋 30건).
- 가시화: 지도 before/after + 대피소별 점유율 히트맵.
- 스택: cuOpt(코어), Nemotron, nvidia-nat, OpenShell(정책+감사 로그), Agent Skills(cuopt-* 3종), 한국 공공데이터.

I-06. 공공 폐기물 수거·배차 제약 최적화 에이전트 (민원 텍스트 → 제약 → cuOpt)
- 페인포인트: 지자체 수거·배차는 시간창, 차량 용량, 민원 우선순위, 도로 통제가 수시로 바뀌는데 경로 조정을 사람이 손으로 함.
- 데이터: 서울열린데이터광장 + 기상청 + KOSIS. 민원 텍스트는 합성(Nemotron-Personas-Korea 기반 생성) 또는 서울시 공개 민원 데이터.
- 방법: Constraint Agent(민원/공지 자연어 → 제약 추출) → Solver Agent(cuopt-routing VRP/PDP) → Explainer(파레토). OpenShell로 외부 호출 제한.
- baseline: 현행/그리디 경로. CPU 솔버.
- 지표: 총 주행거리 절감%, solve time 배수, 제약 추출 정확도(골든셋), SLA 위반 건수.
- 스택: cuOpt, Nemotron, nvidia-nat, OpenShell(보조), Agent Skills 4종.
- 약점 자인: OpenShell 비중이 낮아 교육 미션 정합성이 형식적. 최적화 도메인은 흔함. 실제 수거 경로 데이터가 공개돼 있지 않아 baseline "현행 경로"를 팀이 합성해야 함.

I-07. CVE 영향도 상시 리포터 — "lethal trifecta 정면 돌파" 에이전트
- 페인포인트: 보안팀은 매일 쏟아지는 CVE(NVD 하루 100건+)를 사내 코드베이스 의존성과 대조해야 하는데 수작업. 상시 자동화하려면 에이전트가 신뢰불가 외부 피드 + 민감한 사내 코드 + 외부 리포트 송신 = trifecta를 정면으로 가져야 해서 아무도 안 붙임.
- 데이터: NVD CVE API 2.0(공개, 키 시 30초당 50회) + GitHub Advisory DB + 대상 코드베이스는 공개 OSS 리포(예: 의존성 많은 Python/Node 프로젝트). 골든셋은 GitHub Advisory의 affected package/version 정보로 자동 생성.
- 방법: NemoClaw cron으로 매일 무인 실행 → NeMo Retriever로 의존성 매니페스트/코드 인덱싱 → Nemotron이 CVE별 영향도 판정 + 패치 우선순위 → 리포트 생성. OpenShell 정책: NVD/GitHub 읽기만 허용, 코드 디렉토리 read-only, 리포트 송신은 승인 게이트. 피드에 주입된 "토큰을 읽어 외부로 보내라" 유도문 N건을 실제 투입해 커널 차단 시연.
- baseline: CPE/패키지명 문자열 매칭(현행 SCA 도구 근사).
- 지표: 영향 판정 precision/recall(골든셋), 오탐 감소율, 주입 공격 N건 중 커널 차단 건수 + 정책 예측 vs 실측 일치율, 일일 처리 지연·비용(Nano vs Ultra).
- 스택: OpenShell(코어, trifecta 차단), NemoClaw(cron 무인성), Nemotron Nano/Ultra, NeMo Retriever, Guardrails, nvidia-nat. 
- 약점 자인: 기존 SCA 도구(Dependabot, Snyk)와 뭐가 다른가 질문에 답해야 함. 답은 "영향도 판정(reachability)"과 "안전한 무인 운영 증명"이지만 후자는 지표화가 어려움.

I-08. 제조 SOP 준수 실시간 감시 에이전트
- 페인포인트: 조립 공정에서 작업 순서 위반이 불량·안전사고로 이어짐. 현장 감독 인력이 전 라인을 볼 수 없음.
- 데이터: 자체 촬영 조립 영상 또는 공개 조립 영상 + 자체 라벨. (병목)
- 방법: deepstream-sop 스킬(GPU 가속 FastAPI, 이벤트 경계 검출+지연 측정 내장) 코어 → VSS로 위반 구간 요약 → Nemotron Nano Omni(멀티모달)로 리포트. OpenShell로 영상 접근을 정책 제한(개인정보 서사).
- baseline: 프레임 샘플링 VLM 단독 판정.
- 지표: FPS/종단 지연(deepstream-profile-pipeline), 순서 위반 검출 정확도/오탐률, VLM 단독 대비 개선.
- 스택: DeepStream, VSS, Nemotron Nano Omni, nvidia-nat, OpenShell(보조), Agent Skills 4종.
- 약점 자인: 라벨 영상 확보가 6일 내 최대 병목. OpenShell이 장식에 가까움.

위 5개 형식으로 각각 비평하고, 마지막에 4개 순위 + 기억할 한 문장. 그리고 이 배치와 배치1을 통틀어 "산업가치 축"에서 배치1(보안)이 배치2(공공/제조)보다 불리한지 솔직히 판단해 주세요.
```

### ChatGPT 응답

> 이번 배치는 “사회적으로 중요한 문제”라는 첫인상은 배치1보다 강하지만, 실제 데이터로 숫자를 끝까지 방어하기는 더 어렵습니다. 특히 I-05는 데이터의 현재 상태, I-07은 gold label 정의, I-08은 “NVIDIA 예제를 실행한 것과 무엇이 다른가”가 핵심 공격 지점입니다.
>
> I-05. 서울 재난 대피 경로·수용 배분 최적화
> (1) 페인포인트 실재성: 5/5
>
> 재난 시 특정 대피소 쏠림, 수용능력, 취약계층 이동 부담은 실제 의사결정 문제다. 제약이 명확하고 공공성이 즉시 이해되는 것은 큰 장점이다.
>
> 문제는 현재 서술이 지진 + 폭염 + 한파를 한꺼번에 잡는다. 사실 셋은 같은 최적화 문제가 아니다.
>
> 지진 옥외대피소는 면적 중심이고, 폭염 쉼터는 운영시간·시설 특성이 중요하다. 실제로 서울시 무더위쉼터 데이터는 2026년 8월 10일 이후 시설면적·이용가능인원 필드 제공이 중단됐다. 따라서 현재 시점에 폭염까지 “실제 수용한도 기반”이라고 주장하면 위험하다. 
> data.seoul.go.kr
> +1
>
> (2) baseline·지표 타당성: 3/5
>
> 현재 가장 큰 허점은 solver가 아니라 distance matrix와 capacity의 진실성이다.
>
> 행정동 인구 → 대피소를 최적화하려면 실제로 필요한 건:
>
> 출발지 분포
>
> 도보 도로망
>
> 실제 이동시간
>
> 도로 폐쇄
>
> 시설별 수용능력
>
> 이다.
>
> 행정동 centroid와 직선거리로 계산하고 이를 최대 대피 이동시간 27% 감소라고 발표하면 숫자는 나오지만 현실적 의미가 약하다.
>
> 또한 최근접 대피소 greedy = 현행 관행은 근거가 없다. 현행을 조사하지 않았다면 “naive nearest-shelter baseline”이라고만 불러야 한다.
>
> 그리고 수용초과 0명은 너무 쉬운 metric이다. 충분히 멀리 보내면 달성 가능하다.
>
> 더 좋은 지표는:
>
> capacity violation count
>
> 95th percentile evacuation distance/time
>
> worst 10% vulnerable-population distance
>
> fairness gap: 취약계층 vs 전체
>
> rerouting stability: 도로 N% 폐쇄 시 재배정률
>
> solve latency at 10k / 100k / 1M demand units
>
> 이다.
>
> cuOpt 자체는 vehicle capacity, operating hours, time windows 등 복합 제약을 지원하므로 문제 구조와는 잘 맞는다. 
> NVIDIA Docs
> +1
>
> (3) NVIDIA 스택 심도: 4/5
>
> cuOpt는 확실히 코어다.
>
> 자연어:
>
> “A동 고령자는 800m 이상 이동시키지 말고 B도로는 통제”
>
> ↓ Nemotron formulation
>
> ↓ cuOpt constraint
>
> 라는 흐름도 Agentic AI 설명이 잘 된다.
>
> 공식 NVIDIA Agent Skills에도 수리모델 formulation 및 cuOpt API 관련 skill이 실제로 제공된다. 
> GitHub
> +1
>
> 하지만 OpenShell은 현재 장식에 가깝다.
>
> 서울 API만 접근 가능은 보안적으로 옳지만 이 문제의 본질을 해결하지 않는다. 내부 하드게이트 G2를 엄격히 적용하면 약간 위험하다.
>
> (4) 6일 완주 리스크: 중~상
>
> 가장 먼저 터질 병목:
>
> “실제 travel-time matrix를 어디서 만들지?”
>
> cuOpt는 그 matrix를 만들어주는 것이 아니다.
>
> OSRM/OSM 같은 오프라인 도로망까지 들어가면 프로젝트가 갑자기 커진다.
>
> 그리고 폭염까지 가져가면 앞서 말한 capacity 데이터 문제도 생긴다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> 폭염·한파를 버리고 “서울 지진 대피소 + 한 개 자치구 + 도로폐쇄 시나리오”로 좁힌 뒤, 직선거리가 아닌 실제 보행 네트워크 거리로 평가하라.
>
> 기억할 한 문장
>
> “가까운 대피소를 알려주는 게 아니라, 모두가 동시에 움직였을 때 아무 대피소도 넘치지 않도록 서울 전체를 재배분합니다.”
>
> 이 문장은 강하다.
>
> I-06. 공공 폐기물 수거·배차 제약 최적화
> (1) 페인포인트 실재성: 4/5
>
> 폐기물 수거 차량의 용량, 시간창, 교통·민원 변화가 실제 operational optimization 문제인 것은 맞다.
>
> 하지만 현재 제출물이 증명할 문제는 사실상:
>
> “합성된 서울 폐기물 데이터를 cuOpt로 풀었다.”
>
> 가 될 가능성이 높다.
>
> 실제 차량·수거량·기존 route가 없다면 산업 문제는 실재하지만 프로젝트의 산업 증거는 실재하지 않는다.
>
> (2) baseline·지표 타당성: 2/5
>
> 여기가 치명적이다.
>
> 총 주행거리 23% 감소 같은 숫자를 만들어도 baseline route 자체가 합성이면:
>
> “네가 나쁘게 만든 baseline을 네 optimizer가 이긴 거 아닌가?”
>
> 라는 공격에 취약하다.
>
> CPU solver vs cuOpt solve time은 유효하지만 이것은 NVIDIA solver benchmark이지, 폐기물 문제 해결 성과가 아니다.
>
> 또 하나:
>
> 민원 텍스트 → VRP constraint
>
> 라는 연결도 생각보다 부자연스럽다.
>
> “쓰레기가 아직 수거되지 않았다”는 민원은 새 pickup task이지 반드시 constraint는 아니다.
>
> 더 정직한 지표는:
>
> controlled synthetic benchmark에서 route cost
>
> SLA violations
>
> infeasible constraint detection
>
> natural language → structured constraint exact match
>
> replanning latency
>
> 정도다.
>
> 그리고 OR-Tools 비교는 반드시 동일한 time budget으로 해야 한다. GPU solver에 10초, CPU에 1초를 주고 objective만 비교하거나 반대 방식이면 의미 없다.
>
> (3) NVIDIA 스택 심도: 3/5
>
> cuOpt는 훌륭하게 들어간다. NVIDIA도 cuOpt를 물류·VRP·동적 재배차 영역으로 명시하고 있다. 
> NVIDIA Developer
> +1
>
> 그런데 내부 규범 G2를 적용하면 이 아이디어는 현재 탈락이다.
>
> OpenShell/NemoClaw를 제거해도:
>
> 민원 → Nemotron → cuOpt
>
> 시스템은 거의 그대로 작동한다.
>
> 즉 OpenShell이 architecture core가 아니다.
>
> (4) 6일 완주 리스크: 중
>
> 코드는 오히려 잘 끝날 가능성이 높다.
>
> 하지만 가장 먼저 터질 병목은 기술이 아니라:
>
> “그래서 이 데이터가 실제 지자체 운영을 얼마나 닮았습니까?”
>
> 라는 심사 질문이다.
>
> 이걸 방어하기 어렵다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> 폐기물이라는 산업 서사를 버리지 않으려면 실제 공개 운행 데이터가 있는 지역을 찾아야 하고, 없다면 이 아이디어 자체를 버려라.
>
> 6일 남았다는 조건에서는 데이터 탐색에 하루 이상 쓰지 않는 게 맞다.
>
> 기억할 한 문장
>
> “민원 한 줄이 들어오면 차량 전체를 다시 짜되, 기존 SLA와 차량 용량을 깨지 않는 배차안을 몇 초 안에 생성합니다.”
>
> 나쁘지는 않지만 다른 아이디어보다 평범하다.
>
> I-07. CVE 영향도 상시 리포터
> (1) 페인포인트 실재성: 5/5
>
> 매우 강하다.
>
> 특히 이 아이디어는 단순히 “CVE 요약 agent”가 아니라:
>
> untrusted Internet + private source + autonomous agent
>
> 라는 위험 구조를 문제 자체로 가져온다는 점이 좋다.
>
> 즉 OpenShell의 존재 이유를 설명하기 위해 별도의 억지 서사가 필요 없다.
>
> (2) baseline·지표 타당성: 2.5/5 → 수정하면 5/5
>
> 현재 가장 큰 논리적 오류가 있다.
>
> GitHub Advisory affected package/version을 gold label로 사용해 “reachability precision/recall”을 평가할 수 없다.
>
> GitHub Advisory Database의 affected versions는 그 버전의 package가 취약하다는 정보이지, 특정 repository가 vulnerable function까지 호출한다는 것을 의미하지 않는다. 
> GitHub Docs
>
> 즉:
>
> package installed
>       ≠
> vulnerable code reachable
>
> 이다.
>
> 따라서 현재 gold set으로 측정할 수 있는 것은 affected dependency detection 정도다.
>
> 그리고 package-name matching baseline도 너무 약하다.
>
> 2026년 현재 commercial SCA는 이미 function-level reachability를 제품 기능으로 제공하고 있다. 예를 들어 Endor Labs는 실제로 call-path 기반 reachability 분석을 제공한다. 따라서 “기존 SCA는 문자열 매칭뿐”이라고 발표하면 바로 반박당할 수 있다. 
> Endor Labs Documentation
> +1
>
> 이 아이디어를 살리는 evaluation은 별도로 만들어야 한다.
>
> 예를 들어 CVE 20개에 대해:
>
> Fixture A
> vulnerable dependency O
> vulnerable function 호출 O
>
> Fixture B
> vulnerable dependency O
> vulnerable function 호출 X
>
> 를 만든다.
>
> 그러면:
>
> dependency detector는 A/B 둘 다 위험
>
> ours는 A만 actionable
>
> 로 분리할 수 있다.
>
> 추천 metric:
>
> reachable vulnerability Precision / Recall / F1
>
> false positives per repo
>
> actionable CVE reduction
>
> attack exfiltration ASR
>
> benign CVE-analysis utility
>
> cost / CVE
>
> P95 runtime
>
> (3) NVIDIA 스택 심도: 5/5
>
> 배치2에서 가장 좋다.
>
> 여기서는 OpenShell이 진짜 core다.
>
> agent에게:
>
> Internet feed access
>
> private repository access
>
> autonomous execution
>
> 을 동시에 주는 것이 문제인데,
>
> OpenShell이:
>
> repo read-only
>
> domain/path 제한
>
> outbound write 차단
>
> report approval gate
>
> 를 enforcement한다.
>
> 그것을 빼면 핵심 주장인 “안전하게 무인 운영”이 성립하지 않는다.
>
> NemoClaw cron도 자연스럽다.
>
> Retriever → Nemotron → NAT → OpenShell도 억지스럽지 않다.
>
> Guardrails만 조금 과하다. 공격 payload filtering이라는 명확한 ablation을 하지 않을 거면 제거해도 된다.
>
> (4) 6일 완주 리스크: 중
>
> 가장 먼저 터질 병목:
>
> reachability gold set 구축
>
> CVE 자체 수집은 어렵지 않다.
>
> 실제 어려운 것은:
>
> “이 CVE가 이 repo에서 실제 실행 경로에 들어가는가?”
>
> 를 자동 평가할 ground truth다.
>
> 20~30개 fixture만 직접 만들어도 충분하다.
>
> 그리고 하나 더. OpenShell이 github.com 허용이라고 끝내면 안 된다.
>
> 공격받은 agent가 허용된 GitHub endpoint를 exfil channel로 악용할 수도 있기 때문에 GET/POST, endpoint/path까지 정책이 충분히 좁아야 시연이 설득력 있다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> “SCA를 대체한다”를 버리고 “SCA 결과를 안전한 autonomous triage agent가 처리한다”로 포지셔닝하고, reachable/unreachable paired fixture를 직접 만들어 gold set을 확보하라.
>
> 이 변화가 중요하다.
>
> 기억할 한 문장
>
> “인터넷의 CVE를 읽고 사내 코드를 읽는 에이전트에게, 둘을 읽을 권한은 주되 둘 사이로 데이터를 빼낼 권한은 주지 않았습니다.”
>
> 이건 이번 배치에서 가장 강하다.
>
> I-08. 제조 SOP 준수 실시간 감시
> (1) 페인포인트 실재성: 5/5
>
> 산업 pain은 명백하다.
>
> 품질 불량, 작업 누락, 안전 문제로 바로 연결된다.
>
> 그리고 시각적으로 데모하기 매우 좋다.
>
> 그런데 심사위원에게는 다른 문제가 더 크게 보일 가능성이 높다.
>
> NVIDIA가 이미 deepstream-sop이라는 Agent Skill과 SOP inference reference blueprint를 제공하고 있고, 그 기능 자체가:
>
> event boundary detection
>
> VLM action classification
>
> missing/misordered SOP detection
>
> latency measurement
>
> 이다. 즉 현재 아이디어 설명과 거의 동일하다. 
> GitHub
> +2
> GitHub
> +2
>
> 따라서:
>
> “NVIDIA 공식 SOP blueprint 실행한 것 아닌가요?”
>
> 가 가장 위험한 질문이다.
>
> (2) baseline·지표 타당성: 4/5
>
> 평가 구조 자체는 좋다.
>
> frame sampling VLM
>
> GEBD + VLM
>
> 비교는 매우 이해하기 쉽다.
>
> 특히:
>
> step classification accuracy
>
> sequence violation F1
>
> false alarm/minute
>
> detection delay after violation
>
> end-to-end P95 latency
>
> GPU FPS
>
> 등은 강한 숫자가 된다.
>
> DeepStream profiling skill도 실제로 Nsight Systems 기반 pipeline profiling을 지원한다. 
> GitHub
>
> 다만 순서 위반 검출 accuracy 하나는 부족하다.
>
> manufacturing에서는 정상 작업이 훨씬 많으므로:
>
> 100분 동안 false alarm 몇 번?
>
> 이 훨씬 현실적인 metric이다.
>
> (3) NVIDIA 스택 심도: 5/5, 독창성은 2/5
>
> NVIDIA 기술 활용만 보면 압도적이다.
>
> DeepStream → Triton → GEBD → Cosmos/VLM → VSS로 연결되므로 NVIDIA showcase로는 훌륭하다.
>
> 반대로 그것이 약점이다.
>
> 공식 repository 자체가 이미:
>
> own annotated videos → fine-tune → deploy → evaluate
>
> 라는 전체 workflow를 제공한다. 
> GitHub
>
> 즉 단순 integration은 커스터마이징 점수가 낮아질 수 있다.
>
> OpenShell 역시 제조 영상 privacy 얘기만 붙이면 장식이다.
>
> (4) 6일 완주 리스크: 상
>
> 가장 먼저 터질 병목은 video/model readiness다.
>
> 공식 SOP inference도 VLM checkpoint와 temporal action model checkpoint를 요구하며, 최적 정확도를 위해서는 retraining/fine-tuning을 권한다. 
> GitHub
>
> 직접 fine-tuning까지 들어가면 더 위험하다. NVIDIA의 training blueprint 예시는 full fine-tuning에 4×A100 80GB 환경을 전제로 한다. 
> GitHub
>
> 따라서 6일 안에는:
>
> 촬영 → 라벨 → training → DeepStream integration → evaluation
>
> 을 모두 하겠다는 계획은 버려야 한다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> 모델 학습을 포기하고 NVIDIA 제공 sample/pretrained pipeline을 고정한 뒤, “새로운 SOP를 자연어로 등록하면 자동으로 검사기·평가셋·OpenShell 영상 접근정책까지 생성”하는 customization layer를 프로젝트의 핵심으로 만들어라.
>
> 그렇게 해야 NVIDIA sample과 구별된다.
>
> 기억할 한 문장
>
> “카메라 모델을 다시 만드는 대신, 새로운 작업 절차를 자연어로 등록하면 몇 분 안에 실시간 SOP 감시 파이프라인으로 바꿉니다.”
>
> 배치2 순위
> 1위 — I-07 CVE 영향도 상시 리포터
>
> 가장 완성도가 높다.
>
> 특히 Agentic AI의 위험 자체를 OpenShell이 해결한다는 점이 좋다.
>
> 단, 현재 reachability gold set은 잘못 정의돼 있으므로 반드시 고쳐야 한다.
>
> 2위 — I-05 서울 재난 대피 최적화
>
> 5분 피칭에서 가장 직관적이고 사회적 impact가 크다.
>
> before/after 지도도 강력하다.
>
> 다만 현재 데이터 상태 그대로라면 폭염을 제거하는 것을 권한다. 무더위쉼터 capacity 정보 문제 때문이다.
>
> 3위 — I-08 제조 SOP 감시
>
> 보는 순간 NVIDIA 기술이라는 것은 알 수 있다.
>
> 하지만 역설적으로 너무 NVIDIA reference implementation과 같다.
>
> customization이 없으면 “잘 설치했습니다”가 된다.
>
> 4위 — I-06 폐기물 배차
>
> 문제는 실제지만, 현재 가지고 있는 데이터로는 숫자의 산업적 의미를 방어하기 어렵다.
>
> 더 큰 문제는 팀 내부 하드게이트 G2를 사실상 통과하지 못한다는 것.
>
> 저라면 지금 단계에서 제거한다.
>
> 기억할 한 문장 4개 요약
>
> I-05
>
> “가장 가까운 대피소가 아니라, 모든 시민이 동시에 움직여도 넘치지 않는 대피소를 계산합니다.”
>
> I-06
>
> “민원 한 줄을 새로운 배차 제약으로 바꿔 전체 차량 경로를 즉시 다시 계산합니다.”
>
> I-07
>
> “인터넷과 사내 코드를 동시에 읽는 에이전트에게 필요한 정보는 주되, 정보를 빼낼 권한은 주지 않았습니다.”
>
> I-08
>
> “새 SOP를 자연어로 등록하면 실시간 제조 공정 검사기로 바뀝니다.”
>
> 배치1 보안 vs 배치2 공공/제조 — 산업가치에서 보안이 불리한가?
>
> 아니다. 이 대회에서는 오히려 배치1 쪽이 약간 유리하다고 봅니다.
>
> “공공·제조”라는 단어 자체 때문에 산업가치 점수를 더 받는 구조는 아니다.
>
> 중요한 것은:
>
> 실제 제약이 있는 문제 + NVIDIA 기술이 왜 필수인지 + 결과를 숫자로 증명
>
> 이다.
>
> 그 관점에서 보면 차이가 명확하다.
>
> 축	배치1 보안	배치2 공공/제조
> 문제 실재성	높음	높음
> Agentic AI와 직접 연결	매우 높음	중~높음
> OpenShell 필연성	매우 높음	I-07 제외 상대적으로 약함
> 공개 benchmark	강함	약함
> 6일 내 gold set	상대적으로 쉬움	어려움
> 시각적 데모	보통	강함
> 일반인 이해도	보통	강함
> 산업 숫자 방어	강함	데이터에 따라 약함
> NVIDIA 기술 깊이	매우 강함	cuOpt/DeepStream은 강함
> “샘플 실행” 위험	낮음	I-08 높음
>
> 특히 배치1의 I-03은 MCPTox라는 외부 공격셋이 있고, I-02는 AgentDojo가 있다.
>
> 반면 I-05가:
>
> 이동거리 31% 감소
>
> 를 보여줘도 실제 이동수요·도로망·capacity가 합성되었다면 심사위원은 숫자의 의미를 의심할 수 있다.
>
> 즉 산업가치와 산업처럼 보이는 도메인은 다르다.
>
> 오히려 배치1의 가장 큰 산업가치 논리는 이것이다
>
> Agentic AI hackathon에서:
>
> “기업이 Agent를 production에 못 올리는 이유를 해결한다.”
>
> 는 것 자체가 산업 문제다.
>
> I-01 / I-03은 정확히 이 문제를 건드린다.
>
> 그리고 교육 미션도 Securing Agents with NemoClaw and OpenShell이다.
>
> 따라서 보안 문제는 대회의 주변부가 아니라 오히려 주제의 정중앙에 가깝다.
>
> 현재 8개 중 산업가치 관점에서 특히 강하게 보는 세 개
>
> 정식 종합순위가 아니라 산업가치만 놓고 보면 제 판단은 거의 동급 그룹이다.
>
> I-03 MCP Supply-Chain Auditor, I-07 Safe Autonomous CVE Triage, I-01 Least-Privilege Policy Generator.
>
> 그 다음에 I-05다.
>
> I-05가 더 “큰 문제”처럼 들릴 수는 있지만, I-03/I-07은 고객·구매자·도입 장애·측정 지표가 훨씬 명확하다.
>
> 그리고 6일짜리 예선에서는 이것이 상당히 중요하다.
>
> 한 줄로 압축하면:
>
> 배치2가 사회적 임팩트를 설명하기는 더 쉽지만, 배치1은 “왜 지금 기업이 돈을 내고 필요로 하는가”와 “정말 효과가 있었는가”를 숫자로 방어하기가 더 쉽다.
>
> 현재까지는 그래서 보안 계열을 산업가치 때문에 버릴 이유가 전혀 없습니다.

---

## 턴 4 — 배치 3/5 중간형 (I-09~I-12)

### 내가 보낸 프롬프트

```text
[배치 3/5 — 중간형: 데이터는 있으나 스택 정합성 또는 변별력이 애매한 것들]

I-09. 의약품 상호작용·복약 안전 검증 에이전트
- 페인포인트: 다제복용 고령 환자의 약물 상호작용·중복 처방 검토를 약사가 수작업. 국내 DUR 시스템은 병원 내부용이라 요양시설·재가 돌봄 현장은 접근 불가.
- 데이터: 식약처 e약은요 API(개발 자동승인, 10,000건/일, 라이선스 제한 없음) + 식약처 DUR 병용금기 공개 데이터. 골든셋: 병용금기 목록에서 자동 생성한 QA 페어 N건.
- 방법: NeMo Retriever(임베딩+리랭킹)로 약품 문서 인덱싱 → Nemotron이 처방 목록을 받아 상호작용 멀티홉 검색 → NemoGuard ContentSafety로 의료 조언 범위 제한 → 면책 문구. OpenShell로 환자 데이터 디렉토리 read-only + egress를 apis.data.go.kr만.
- baseline: 키워드 매칭 / RAG 없이 Nemotron 단독.
- 지표: 골든셋 Recall@k, faithfulness(rag-eval RAGAS), 오탐률, 응답 지연.
- 스택: NeMo Retriever(코어), Nemotron, NemoGuard, rag-eval 스킬, OpenShell(보조).
- 약점 자인: NVIDIA 스택이 RAG에 치우쳐 축1 낮음. OpenShell 장식. 의료 면책 필수.

I-10. 에이전트 비용·지연 라우터 (Nemotron Nano 셀프호스팅 ↔ Ultra API)
- 페인포인트: 에이전트 운영비의 대부분이 LLM 호출. 모든 스텝을 프런티어 모델로 돌리면 비용 폭발, 전부 소형이면 정확도 붕괴. 어떤 스텝을 어디로 보낼지 기준이 없음.
- 데이터: BFCL V4(Apache-2.0, 함수호출 정확도 + 비용·지연 표준 산출, pip install bfcl-eval 버전 고정) + tau2-bench(MIT, pass^k).
- 방법: nvidia-nat 워크플로에서 스텝별 난이도 분류기(Nano)가 라우팅 → 쉬운 스텝은 L40S 셀프호스팅 Nemotron Nano NIM, 어려운 스텝은 Ultra API. 프로파일러로 스텝 단위 토큰·지연 기록. OpenShell 인퍼런스 정책(핫리로드)으로 라우팅을 "정책"으로 표현.
- baseline: 전부 Ultra / 전부 Nano.
- 지표: 동일 BFCL 정확도(±1%p)에서 비용 절감%, p50/p95 지연, 라우팅 분류기 정확도.
- 스택: Nemotron Nano+Ultra(코어), NIM 셀프호스팅, nvidia-nat 프로파일러, OpenShell 인퍼런스 정책, Brev L40S.
- 약점 자인: "제품"이 아니라 "실험"으로 보임. OpenShell은 인퍼런스 라우팅 정책 정도.

I-11. 에이전트 회귀 게이트 (Agent CI) — 툴 description/모델/프롬프트 변경 시 라우팅 드리프트 자동 탐지
- 페인포인트: 에이전트에서 tool description 한 줄, 모델 엔드포인트 하나 바꾸면 라우팅 행동이 조용히 바뀐다. 현재 팀들은 "잘 되는 것 같다"로 배포. 테스트가 없다.
- 방법: 골든 트레이스(툴콜 시퀀스 + 인자) N건 녹화 → PR마다 OpenShell 샌드박스에서 리플레이(부작용 차단) → 트레이스 diff → 드리프트 리포트 + 자동 롤백. tau2-bench pass^k로 일관성 측정.
- 데이터: 자체 골든 트레이스 + tau2-bench.
- baseline: 테스트 없음(드리프트 탐지 0) / 단순 출력 문자열 비교.
- 지표: 주입 회귀 N건 중 탐지율, 오탐률(비의미 변경을 회귀로 판정), 리플레이 비용·시간, pass^k.
- 스택: nvidia-nat(프로파일러/평가 코어), OpenShell(부작용 격리 리플레이), Nemotron, NemoClaw.
- 약점 자인: OpenShell이 "격리 실행 환경" 역할이라 코어인지 애매. "에이전트 CI"는 GitHub Actions 위에 얹는 도구라 데모가 밋밋.

I-12. 아파트 실거래 이상거래 탐지·조사 에이전트
- 페인포인트: 자전거래·허위 신고·이상 고가 거래로 시세 왜곡. 국토부 이상거래 조사는 사후·수작업.
- 데이터: 국토부 아파트 실거래가 API(자동승인, 10,000건/일, XML) + 서울 열린데이터. 골든셋: 실제 이상거래 라벨이 공개돼 있지 않아 합성 주입(팀 통제).
- 방법: 수집 Agent → 통계 이상치 후보 → 조사 Agent가 인접 거래·해제 이력·단지 시세 멀티홉 확인 → 리포트. OpenShell egress를 apis.data.go.kr만.
- baseline: z-score 단일 규칙.
- 지표: 주입 이상거래 precision/recall, 조사 근거 인용 정확도.
- 스택: Nemotron, NeMo Retriever, nvidia-nat, OpenShell(보조), cuDF(accelerated-computing-cudf 스킬로 대량 거래 ETL).
- 약점 자인: 합성 라벨 → "자기 문제 자기 채점". 에이전트 없이도 pandas 규칙으로 풀림.

위 5개 형식으로 각각 비평하고, 마지막에 4개 순위 + 기억할 한 문장. 추가로: I-10처럼 "실험형" 아이디어를 "제품형"으로 바꾸는 가장 싼 방법이 있다면 제시해 주세요.
```

### ChatGPT 응답

> 이번 배치는 네 개 모두 “만들 수는 있다”가 문제입니다. 해커톤에서 이길 이유가 있는가로 다시 보면 I-11이 예상보다 강하고, I-10은 아이디어는 좋지만 현재 OpenShell 설계에 기술적 수정이 필요합니다. I-09와 I-12는 데이터가 있다는 사실이 오히려 함정입니다.
>
> I-09. 의약품 상호작용·복약 안전 검증 에이전트
>
> (1) 페인포인트 실재성: 5/5
>
> 다제복용과 병용금기 확인은 명백한 실무 문제다. 데이터 접근성도 실제로 좋다. 식약처 포털은 e약은요뿐 아니라 병용금기·특정연령금기·임부금기·효능군중복 등을 포함한 DUR 품목정보를 공개하고 있다. 
> 식품의약품안전처 데이터
> +1
>
> 문제는 이 문제에서 LLM agent가 정말 필요한 부분이 어디인가다.
>
> 병용금기는 기본적으로:
>
> 성분 A + 성분 B → 금기
>
> 형태의 structured lookup 문제다.
>
> 잘못 설계하면 심사위원이 바로 묻는다.
>
> “SQL JOIN이면 끝나는 걸 왜 Nemotron과 Retriever로 풀죠?”
>
> 이 질문에 현재 설계는 약하다.
>
> (2) baseline·지표 타당성: 2.5/5
>
> 병용금기 목록 → QA 자동 생성 → Recall@k는 숫자는 잘 나오지만 평가 문제가 너무 쉽다.
>
> 특히 RAGAS faithfulness가 높다고 해서:
>
> “이 복약 판단이 안전하다”
>
> 는 의미가 아니다.
>
> 또 RAG 없이 Nemotron은 너무 약한 baseline이다. 진짜 baseline은 구조화 DUR DB exact lookup이어야 한다.
>
> 오히려 이렇게 나눠야 한다.
>
> 약품명 → 표준 품목/성분 normalization accuracy
>
> contraindicated pair recall
>
> contraindicated pair precision
>
> source citation accuracy
>
> unsupported interaction claim rate
>
> 복합 처방 N개에서 pair coverage
>
> 약품 alias/상품명 변화에 대한 robustness
>
> 가장 중요한 metric은:
>
> 금기인데 놓친 비율(false negative)
>
> 이다.
>
> 그리고 “멀티홉 RAG”라는 표현도 조심해야 한다. 공개 DUR 표에서 직접 찾을 수 있는 정보를 여러 문서를 거쳐 찾았다고 해서 기술적으로 더 가치 있는 것은 아니다.
>
> (3) NVIDIA 스택 심도: 2.5/5
>
> Retriever는 코어가 될 수 있다.
>
> 그러나 OpenShell은 명백히 보조다.
>
> 환자 파일 read-only와 외부 API 제한은 좋은 security hygiene이지 의약품 상호작용 문제의 핵심 알고리즘이 아니다.
>
> 더 큰 문제는 제대로 된 시스템일수록 오히려:
>
> DUR deterministic rule engine → Retriever로 근거 검색 → Nemotron으로 설명
>
> 이 되어야 한다는 것.
>
> 그렇게 만들면 안전성은 좋아지지만 NVIDIA Agent 기술 심도는 내려간다.
>
> 즉 문제 품질과 대회 적합성이 서로 반대 방향으로 움직이는 아이디어다.
>
> (4) 6일 완주 리스크: 중
>
> API보다 먼저 터질 병목은 약품 identity normalization이다.
>
> 상품명 / 주성분 / 함량 / 복합제 등을 제대로 연결하지 못하면 gold set recall이 의미가 없다.
>
> 그리고 의료 UI나 상담 flow에 시간을 쓰기 시작하면 위험하다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> “의료 조언 에이전트”를 버리고 deterministic DUR 검증기가 판정하고 Nemotron은 근거 검색·설명만 담당하는 구조로 바꿔라—다만 그러면 대회 우승 후보로는 약해진다는 것도 감수해야 한다.
>
> 기억할 한 문장
>
> “LLM에게 약이 안전한지 묻는 것이 아니라, DUR이 판정하고 AI는 왜 위험한지를 공공 근거에서 찾아 설명합니다.”
>
> 좋은 제품 문장이지만 NVIDIA hackathon 문장으로는 약하다.
>
> I-10. 에이전트 비용·지연 라우터
>
> 여기에는 먼저 중요한 기술 수정이 하나 있다.
>
> 현재 OpenShell은 inference.local의 backend provider/model을 설정하고 실행 중 갱신할 수 있지만, gateway 단위에서 하나의 active backend를 적용하며 변경 전파도 기본 약 5초 수준이다. 즉 “에이전트의 각 step마다 OpenShell 설정을 hot reload해서 Nano↔Ultra를 선택한다”는 구조는 per-request routing 용도로 적합하지 않다. 
> NVIDIA Docs
> +1
>
> 따라서 routing decision은 애플리케이션 계층에서 해야 한다.
>
> (1) 페인포인트 실재성: 5/5
>
> 매우 현실적이다.
>
> agent는 한 요청 안에서도:
>
> 단순 추출
>
> tool selection
>
> 계획
>
> validation
>
> synthesis
>
> 등 난이도가 크게 다른 호출을 반복한다.
>
> 모든 것을 대형 모델로 처리하면 낭비라는 문제도 즉시 이해된다.
>
> 특히 enterprise agent 규모에서는 매우 명확한 돈 문제다.
>
> (2) baseline·지표 타당성: 4/5
>
> BFCL은 이 아이디어와 상당히 잘 맞는다. V4는 agentic 영역을 포함하며 공식 leaderboard가 accuracy뿐 아니라 cost와 latency도 측정한다. 현재 공개 재현 버전도 명시되어 있다. 
> Gorilla
> +1
>
> 하지만:
>
> “Ultra 정확도 ±1%p에서 비용 40% 감소”
>
> 만으로는 약간 부족하다.
>
> 왜냐하면 routing workload에 따라 숫자를 쉽게 좋게 만들 수 있기 때문이다.
>
> 반드시 Oracle router를 추가해야 한다.
>
> 각 문제에 대해 사후적으로:
>
> Nano가 성공했으면 Nano
> Nano 실패 + Ultra 성공이면 Ultra
> 둘 다 실패면 failure
>
> 를 계산한다.
>
> 그러면:
>
> All Nano
>
> All Ultra
>
> Ours
>
> Oracle
>
> 네 개가 된다.
>
> 가장 좋은 metric은 routing classifier accuracy가 아니다.
>
> Routing regret다.
>
> 예:
>
> ours cost - oracle minimum cost @ target accuracy
>
> 또는:
>
> ours quality loss vs oracle.
>
> 그리고 local GPU cost도 조심해야 한다. BFCL 역시 self-hosted 모델 비용은 GPU 시간 기반으로 추정하기 때문에 API dollar와 직접 비교할 경우 가격·utilization 가정을 명시해야 한다. 
> Gorilla
> +1
>
> 추천 지표:
>
> task success / BFCL accuracy
>
> $ / successful task
>
> P50/P95 end-to-end latency
>
> Ultra escalation rate
>
> routing regret
>
> quality-cost Pareto frontier
>
> (3) NVIDIA 스택 심도: 현재 3/5, 고치면 4.5/5
>
> Nano/Ultra + NIM + profiling은 매우 자연스럽다.
>
> 반대로 현재 OpenShell 설명은 억지다.
>
> 수정안은:
>
> Agent in OpenShell
>        ↓
> https://inference.local
>        ↓
> Secure Routing Gateway
>      ↙      ↘
> Nano NIM    Ultra NIM API
>
> 로 만드는 것.
>
> OpenShell에서는 Secure Routing Gateway 하나만 허용된 inference backend로 보이게 한다.
>
> Routing Gateway가 요청 난이도와 SLO를 보고 Nano/Ultra를 선택한다.
>
> 그러면 sandbox 안 agent는:
>
> 실제 provider URL 모름
>
> API credential 없음
>
> 임의 Ultra direct-call 불가
>
> 가 된다.
>
> OpenShell의 공식 inference routing 자체가 provider credential을 sandbox 밖에 두고 inference.local로 통제하는 구조이므로 이 framing은 맞는다. 
> NVIDIA Docs
> +1
>
> 이렇게 해야 G2를 어느 정도 방어할 수 있다.
>
> (4) 6일 완주 리스크: 중
>
> 가장 먼저 터질 병목:
>
> 난이도 classifier가 router overhead 이상의 가치를 만들 수 있느냐
>
> Nano를 먼저 한번 호출해 “이게 어려운가요?”라고 판단하고 그 뒤 Ultra를 부르면 비용·latency를 오히려 먹는다.
>
> 따라서 별도 LLM classification보다:
>
> prompt length
>
> tool count
>
> previous failure
>
> argument schema complexity
>
> confidence/logprob 가능 시 confidence
>
> 같은 cheap feature + Nano 일부를 쓰는 편이 낫다.
>
> 또 L40S self-hosting 자체를 예선 필수로 잡으면 현재 Brev 제공시점과 충돌할 수 있으니, API-only reproducible mode도 반드시 만들어야 한다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> OpenShell hot reload router를 버리고 inference.local → 단일 Secure Routing Gateway → Nano/Ultra 구조로 바꿔 비용 최적화와 provider credential/egress 통제를 하나의 제품으로 묶어라.
>
> 기억할 한 문장
>
> “모든 요청에 가장 싼 모델을 쓰는 게 아니라, 목표 정확도를 깨지 않는 한 가장 싼 모델을 자동으로 선택합니다.”
>
> 매우 좋다.
>
> I-11. Agent CI — 에이전트 회귀 게이트
>
> (1) 페인포인트 실재성: 5/5
>
> 이 배치에서 과소평가된 아이디어다.
>
> 실제 agent 개발의 큰 문제는:
>
> prompt 변경
> tool description 변경
> MCP 버전 변경
> model 변경
>
> 후에도 컴파일 오류가 발생하지 않는다는 것이다.
>
> 대신 behavior가 조용히 변한다.
>
> CI/CD 문제로 framing하면 buyer도 명확하다.
>
> AI platform team / agent engineering team.
>
> 더구나 현재 NVIDIA의 Agent Evaluation은 최종 답뿐 아니라 tool call과 trajectory 같은 evidence를 trial 단위로 평가할 수 있고, Experiments는 harness·tool·routing 변화에 따른 cost/latency/evaluator score 비교를 명시적으로 지원한다. 이 아이디어는 지금 NVIDIA 평가 스택 방향과 상당히 잘 맞는다. 
> NVIDIA Docs
> +2
> NVIDIA Docs
> +2
>
> (2) baseline·지표 타당성: 4/5
>
> 테스트 없음 baseline은 버려야 한다.
>
> 너무 쉬운 허수아비다.
>
> 진짜 baseline:
>
> final-answer exact/semantic test
>
> mocked tool unit test
>
> ours: real replay + trajectory evaluation
>
> 으로 두는 것이 낫다.
>
> 또 하나 중요한 문제가 있다.
>
> tool-call sequence가 달라졌다고 regression은 아니다.
>
> 예:
>
> search → retrieve → answer
>
> 와
>
> retrieve → search → answer
>
> 가 같은 결과와 side effect를 만들 수도 있다.
>
> 따라서 raw sequence diff를 gate로 사용하면 false positive 폭발한다.
>
> 좋은 평가셋은 mutation testing이다.
>
> 일부러:
>
> tool description 의미 변경
>
> required argument 삭제
>
> tool rename
>
> prompt instruction 충돌
>
> model swap
>
> permission reduction
>
> 등 N개 mutation을 주입하고 어떤 회귀가 발생해야 하는지 label을 만든다.
>
> 지표:
>
> regression mutation detection recall
>
> precision
>
> equivalent-change false-positive rate
>
> tool argument correctness
>
> task success delta
>
> cost/PR
>
> P95 CI runtime
>
> pass^k도 의미 있다. τ² 계열은 반복 실행에서 모두 성공할 확률을 보는 pass^k를 사용하므로 nondeterministic agent regression에 잘 맞는다. 
> GitHub
> +1
>
> (3) NVIDIA 스택 심도: 4/5 → 설계하면 5/5
>
> 현재 설명처럼 mock replay를 하면 OpenShell은 장식이다.
>
> 반대로 실제 tool/MCP를 실행하면 상황이 다르다.
>
> 예를 들어 CI가:
>
> GitHub issue 수정 agent
>
> 를 replay한다고 하자.
>
> Regression test라고 실제 GitHub에 issue를 만들고 삭제할 수는 없다.
>
> 그래서:
>
> OpenShell ephemeral sandbox
> + fixture MCP/API
> + filesystem snapshot
> + restricted network
> + actual agent execution
>
> 을 한다.
>
> 이때 OpenShell이 없으면 안전한 real side-effect replay라는 핵심 기능을 구현하기 어렵다.
>
> 더 좋은 product claim은:
>
> “Mock하지 않고 실제 agent를 재실행하지만 production side effect는 만들지 않는다.”
>
> 이다.
>
> 그리고 NVIDIA Evaluator가 trajectory/tool-use evaluation을 이미 제공하기 때문에 이것을 적극 활용해야 한다. 
> NVIDIA Docs
> +1
>
> (4) 6일 완주 리스크: 중~하
>
> 네 개 중 가장 일정이 안정적이다.
>
> 가장 먼저 터질 병목은:
>
> semantic equivalence 판정
>
> 이다.
>
> trajectory가 조금 달라졌다고 모두 fail시키면 데모는 쉽게 만들 수 있지만 제품은 쓸 수 없다.
>
> 따라서 처음부터 범용 agent를 하지 말고:
>
> 파일 수정 agent 또는
>
> 간단한 MCP support agent
>
> 하나를 골라야 한다.
>
> mutation 30개 정도만 만들어도 숫자가 나온다.
>
> UI 필요 없다.
>
> GitHub Actions의:
>
> Agent Regression Gate: FAIL
>
> Task success      97% → 71%
> Tool-call drift   4/30
> New side effects  2
> Cost/task         +38%
>
> 이 출력 자체가 데모다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> “trace diff 도구”가 아니라 “실제 side-effect를 sandbox에서 재실행하고 의미 있는 행동 회귀만 PR을 막는 Agent CI gate”로 정의하라.
>
> 기억할 한 문장
>
> “에이전트 코드는 통과했는데 행동이 깨지는 배포를, production에 가기 전에 실제 툴을 다시 실행해서 잡습니다.”
>
> 이번 배치에서 제일 좋다.
>
> I-12. 아파트 실거래 이상거래 탐지·조사
>
> (1) 페인포인트 실재성: 4/5
>
> 시세 왜곡과 이상거래 조사는 현실 문제다.
>
> 국토부 상세 실거래 API 자체는 현재 제공되고 있고 개발·운영 단계 자동승인, 개발계정 10,000건이라는 데이터 접근성도 좋다. 
> 데이터.go.kr
>
> 그런데 중요한 차이가 있다.
>
> 가격 이상치 ≠ 이상거래 ≠ 자전거래
>
> 공개된 가격·면적·층·거래 시점만으로 거래 당사자의 의도까지 판정할 수 없다.
>
> 따라서 “자전거래 탐지”라고 이름 붙이는 순간 주장이 과해진다.
>
> (2) baseline·지표 타당성: 1.5/5
>
> 네 개 중 가장 치명적이다.
>
> 합성 anomaly를 넣고:
>
> Precision 94%
>
> 라고 해도 거의 아무것도 증명하지 못한다.
>
> 왜냐하면 synthetic anomaly generator의 규칙을 detector가 다시 찾는 셈이 될 수 있기 때문이다.
>
> 더 심각한 것은 z-score baseline.
>
> 부동산은:
>
> 평형
>
> 동/층
>
> 거래량
>
> 시점
>
> 재건축 이슈
>
> 특수관계
>
> 등 heterogeneity가 매우 크므로 단순 z-score는 너무 약한 baseline이다.
>
> Isolation Forest / Local Outlier Factor / robust price index 정도까지는 baseline으로 줘야 한다.
>
> 그래도 real fraud label 부재 문제는 남는다.
>
> (3) NVIDIA 스택 심도: 2/5
>
> cuDF를 제외하면 대부분:
>
> ETL → anomaly detection → RAG 설명
>
> 이다.
>
> OpenShell은 API 제한뿐이고 NemoClaw도 필요하지 않다.
>
> 가장 치명적인 질문:
>
> “이걸 왜 agent로 만들어야 하죠?”
>
> 현재 답이 없다.
>
> 후보 추출과 근거 정리는 pandas + SQL로 충분하다.
>
> (4) 6일 완주 리스크: 기술 하 / 심사 리스크 상
>
> 코드는 잘 끝난다.
>
> 가장 먼저 터질 병목은 데이터가 아니라:
>
> “ground truth가 어디 있습니까?”
>
> 다.
>
> 여기에 답을 못 하면 숫자 중심 내부 규범 G1/G5를 동시에 흔든다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> 실거래 ‘사기 탐지’를 포기하고 계약해제·재신고 등 공개 데이터로 객관적으로 정의 가능한 거래 패턴 조사 문제로 좁히지 못하면 탈락시켜라.
>
> 기억할 한 문장
>
> “비싼 거래를 사기라고 부르는 것이 아니라, 사람이 검토해야 할 거래와 그 근거를 자동으로 묶어줍니다.”
>
> 방어적인 문장이지 강한 우승 문장은 아니다.
>
> 배치 3 순위
> 1위 — I-11 Agent CI
>
> 배치 시작 전 설명만 보면 중간급인데, 뜯어보면 꽤 강하다.
>
> 특히 현재 NVIDIA evaluation stack이 task outcome뿐 아니라 trajectory/tool evidence를 평가하는 방향이라 기술 정합성이 예상보다 높다. 
> NVIDIA Docs
> +1
>
> 게다가:
>
> 개발자 pain 명확
>
> 외부 데이터 승인 없음
>
> mutation으로 정량평가 가능
>
> 6일 scope 제어 쉬움
>
> GitHub 제출 방식 자체가 제품 데모
>
> 라는 장점이 있다.
>
> I-03과 같은 보안 아이디어보다 화려하지 않지만 완주 확률 대비 점수가 좋다.
>
> 2위 — I-10 Adaptive Inference Router
>
> 숫자가 매우 예쁘게 나올 가능성이 있다.
>
> BFCL도 적합하다. 다만 현재 OpenShell step-level hot reload 설계는 버려야 한다.
>
> Secure Routing Gateway로 바꾸면 살아난다.
>
> 3위 — I-09 복약 안전
>
> 사회적 가치는 크고 데이터도 좋다.
>
> 그러나 제대로 만들수록 deterministic DUR engine이 코어가 되어 Agentic NVIDIA hackathon이라는 대회 정합성이 내려간다.
>
> 좋은 서비스 아이디어와 좋은 대회 아이디어는 다르다.
>
> 4위 — I-12 실거래 이상거래
>
> 지금 상태에서는 제거 대상이다.
>
> 팀 규범인:
>
> 숫자로 증명 못 하면 채택하지 않는다.
>
> 를 가장 정면으로 위반한다.
>
> 숫자는 만들 수 있지만 의미 있는 숫자를 만들 수 없다.
>
> I-10을 가장 싸게 “실험형 → 제품형”으로 바꾸는 방법
>
> 있다. UI를 만드는 것이 아니다.
>
> 이름을 예를 들어:
>
> Agent Inference Governor
>
> 라고 하고 OpenAI-compatible gateway 하나만 만들면 된다.
>
> 구조는 이 정도면 충분하다.
>
>               Agent
>                 │
>         OpenShell sandbox
>                 │
>       https://inference.local
>                 │
>        ┌────────▼────────┐
>        │ Routing Gateway │
>        └───────┬─────────┘
>                │
>         ┌──────┴──────┐
>         ▼             ▼
>  Nemotron Nano     Nemotron Ultra
>  local/NIM          NVIDIA API
>
> 그리고 사용자에게 파일 하나만 주면 된다.
>
> YAML
> quality_target: 0.95
> monthly_budget_usd: 500
> latency_p95_ms: 2500
>
> routes:
>   default: nano
>
> escalation:
>   - tool_count >= 5
>   - previous_tool_error == true
>   - complexity_score >= 0.72
>
> 여기서 중요한 것은 사용자가 threshold를 직접 찾게 하지 않는 것이다.
>
> Profiler가 과거 agent trace를 읽고 정책을 자동 생성한다.
>
> nat trace
>    ↓
> offline benchmark
>    ↓
> quality / cost / latency Pareto
>    ↓
> routing-policy.yaml
>    ↓
> production gateway
>
> 그러면 제품 질문이 바뀐다.
>
> 실험형:
>
> “Nano와 Ultra를 섞으면 싸집니다.”
>
> 제품형:
>
> “현재 agent를 그대로 연결하고 품질 SLO를 지정하면, 가장 싼 routing policy를 자동 생성해서 production inference에 강제합니다.”
>
> 이 차이는 크다.
>
> 그리고 제품화 비용은 아주 작다.
>
> 필요한 것은 gateway endpoint + YAML + benchmark report뿐이다. 대시보드도 필요 없다.
>
> 더 중요한 것은 OpenShell 역할도 명확해진다는 점이다.
>
> agent가 routing decision을 우회해서 직접 Ultra endpoint에 접속하지 못하도록 network policy를 막고, 모든 inference와 credential을 inference.local을 통해 강제한다. OpenShell은 실제로 inference backend credential을 sandbox에서 분리하고 direct external inference는 network policy로 제한할 수 있다. 
> NVIDIA Docs
> +1
>
> 따라서 최종 피치가:
>
> “우리는 좋은 routing algorithm을 만들었습니다.”
>
> 가 아니라
>
> “Agent에게 월 예산과 품질 SLO를 주면 routing policy를 자동 생성하고, OpenShell이 그 정책을 우회하지 못하게 강제합니다.”
>
> 가 된다.
>
> 이 정도가 I-10을 실험에서 제품으로 바꾸는 가장 싼 변경이다. 그리고 이 형태라면 I-10과 I-11은 다음 배치들과 비교할 때도 계속 후보군에 남겨둘 가치가 있다.

---

## 턴 5 — 배치 4/5 허황형 1차 (I-13~I-16)

### 내가 보낸 프롬프트

```text
[배치 4/5 — 허황형(wild). 일부러 과감한 것들입니다. "허황되지만 6일 안에 데모 가능한 축소판이 있는가"까지 답해 주세요.]

I-13. 자기진화 스킬 라이브러리 에이전트 (Voyager-style, DLI 목표 5 "persistent skill libraries" 직결)
- 아이디어: 에이전트가 태스크 실패 경험에서 스스로 SKILL.md를 작성 → OpenShell 샌드박스에서 검증 실행 → held-out 태스크 성공률이 오를 때만 스킬 라이브러리에 승격(내려가면 폐기). NVIDIA 공식 스킬(npx skills add)과 자작 스킬이 같은 라이브러리에 공존.
- baseline: 정적 스킬셋(공식 스킬만) / 스킬 없음.
- 지표: 반복 N회에 따른 held-out 태스크 성공률 곡선, 승격된 스킬 수, 스킬 재사용률, 승격 스킬이 일으킨 회귀 수, 스킬당 토큰 절감.
- 스택: Agent Skills(코어), OpenShell(검증 격리), NemoClaw(하네스+메모리), Nemotron Nano(실행)/Ultra(스킬 저작), nvidia-nat 평가.
- 허황 포인트: 6일 안에 단조 개선 곡선이 안 나올 수 있음. "LLM이 알아서 배웁니다" 냄새.

I-14. 에이전트 면허시험소 (Agent Driver's License) — 배포 전 표준 안전 시험 → 서명된 면허(정책+스킬카드) 발급
- 아이디어: 어떤 에이전트(OpenClaw/Hermes/커스텀)든 제출하면 OpenShell 안에서 표준 시험(AgentDojo 보안 케이스 + MCPTox 툴 포이즈닝 + 자체 최소권한 시험)을 치르고, 통과 시 "면허" = 서명된 최소권한 정책 YAML + skill card + 점수표를 발급. 운영 중 정책 위반 누적 시 면허 정지. I-01+I-02+I-03을 하나의 "인증 기관" 제품으로 묶은 것.
- baseline: 무시험 배포(현재 업계 관행).
- 지표: 하네스별 면허 점수(OpenClaw vs Hermes vs LangChain — NemoClaw 하네스 교체 실증!), 시험 소요 시간, 면허 발급 후 실제 공격 시나리오 사고율(면허 有 vs 無).
- 스택: OpenShell(코어), NemoClaw 하네스 3종 교체 실증(1c=5), Nemotron, Guardrails, nvidia-nat, Agent Skills(skill-card-generator).
- 허황 포인트: 범위가 3개 아이디어 합. "인증 기관"은 제도 없이 신뢰를 못 얻음.

I-15. A2A 최소권한 협상 브로커 — 에이전트끼리 권한을 "빌리고 갚는다"
- 아이디어: 오케스트레이터가 서브에이전트에 작업 위임 시 A2A 프로토콜로 "필요 권한 명세"를 협상 → 브로커가 작업 범위에 맞는 임시 OpenShell 정책을 즉석 발급(TTL 있음) → 작업 종료 시 자동 회수. 정적 정책 대비 "권한 노출 시간×범위"를 최소화.
- baseline: 정적 광역 정책(모든 서브에이전트가 같은 정책).
- 지표: 권한 노출 면적(허용 경로·도메인·바이너리 수 × 시간) 감소%, 작업 성공률 유지, 협상 오버헤드(지연), 권한 초과 요청 거절 건수.
- 스택: nvidia-nat A2A(코어), OpenShell 정책 동적 발급/회수, NemoClaw 멀티에이전트, Nemotron.
- 허황 포인트: OpenShell 정책이 샌드박스 생성 시 고정되는 계층(파일/프로세스)과 런타임 핫리로드 계층(인퍼런스)이 달라서 "즉석 발급"이 기술적으로 제한될 수 있음. A2A 구현 성숙도 불명.

I-16. 에어갭 에이전트 — 인터넷 0바이트로 민감 문서를 처리하는 DGX Spark/L40S 로컬 완전 오프라인 에이전트
- 아이디어: 네트워크 정책 deny-all(inference.local 포함 외부 0). Nemotron Nano NIM + NeMo Retriever 임베딩 NIM을 L40S에 셀프호스팅. 공공기관·병원·방산처럼 망분리 환경에서 에이전트를 쓰려는 조직이 대상. "감사 로그에 외부 egress 시도 0건"을 증명.
- baseline: 온라인(Ultra API) 에이전트 동일 태스크.
- 지표: 오프라인 vs 온라인 태스크 성공률 격차, 지연, egress 시도 건수(0 증명 + 주입 공격 시 차단 건수), GPU 메모리 사용량, 처리량.
- 스택: OpenShell(deny-all 정책 코어), NIM 셀프호스팅(Nano+Retriever), NemoClaw, Nemotron, Brev L40S → DGX Spark 배포 시나리오(우승 상품과 서사 일치).
- 허황 포인트: 예선 단계엔 L40S 크레딧이 없음(본선 10팀만). "오프라인"은 데모로 보여주기 심심함. Nano 30B가 문서 태스크에서 Ultra 대비 얼마나 떨어지는지가 리스크.

위 5개 형식 + 각각 "6일 축소판" 한 문장. 마지막에 4개 순위 + 기억할 한 문장.
```

### ChatGPT 응답

> 이번 배치에서 “허황되지만 축소하면 오히려 강해지는” 것은 I-13과 I-15입니다. I-14는 이름보다 범위를 죽여야 살고, I-16은 아이디어가 아니라 예선 시점 GPU 접근권 때문에 막힐 가능성이 큽니다.
>
> I-13. 자기진화 스킬 라이브러리 에이전트
> (1) 페인포인트 실재성: 4/5
>
> 문제는 실재한다. Agent가 같은 종류의 실패를 반복하는데도 매번 prompt/context에서 다시 해결하고, reusable procedure로 축적하지 못하는 것은 비용·안정성 문제다.
>
> 다만 “자기진화”를 전면에 내세우면 바로 과장 냄새가 난다.
>
> 실제로 만드는 것은:
>
> 실패 trace → 후보 SKILL.md 생성 → evaluation → promotion/rejection
>
> 이다.
>
> 이건 “AI가 스스로 학습한다”가 아니라 skill artifact에 대한 automated search + CI에 가깝다. 그 표현이 훨씬 방어 가능하다.
>
> 오히려 현재 NVIDIA Skills의 방향과 절묘하게 맞는다. 공식 NVIDIA Skills는 현재 SKILL.md뿐 아니라 평가 데이터와 benchmark report, 검증용 signature까지 포함하는 구조다. 즉 skill도 평가받아야 하는 배포 artifact라는 framing 자체가 NVIDIA 방향과 잘 맞는다. 
> GitHub
>
> (2) baseline·지표 타당성: 3.5/5
>
> iteration → held-out success rate 곡선은 시각적으로 굉장히 강하다.
>
> 하지만 가장 위험한 함정은 test contamination이다.
>
> 예를 들어:
>
> 1회차 실패
> → skill 생성
> → held-out 평가
> → 실패 분석
> → 새 skill 생성
> → 같은 held-out 평가
>
> 를 반복하면 그 순간 held-out은 더 이상 held-out이 아니다.
>
> 결국 테스트셋에 적응한다.
>
> 따라서 반드시:
>
> Train tasks
>   ↓ 실패에서 skill 생성
>
> Development tasks
>   ↓ promotion 판단
>
> Frozen Test tasks
>   ↓ 마지막에 딱 한 번 평가
>
> 로 해야 한다.
>
> 현재 지표 중:
>
> 승격 skill 수 → 거의 의미 없음
>
> skill 재사용률 → 보조 지표
>
> token 절감 → 좋음
>
> 회귀 수 → 매우 중요
>
> 더 강한 지표는:
>
> Frozen test success rate
>
> skill-enabled uplift
>
> task family별 generalization
>
> regression rate
>
> average tokens / successful task
>
> tool calls / successful task
>
> promotion precision
> 승격한 skill 중 실제 frozen test에서도 도움이 된 비율
>
> 이다.
>
> 그리고 반드시 baseline에:
>
> 사람이 미리 작성한 static custom skill
>
> 하나를 넣는 것이 좋다.
>
> no skill → NVIDIA official skill → manually-authored skill → evolved skill
>
> 이라야 자동 생성 가치가 보인다.
>
> (3) NVIDIA 스택 심도: 5/5
>
> 이번 배치에서 가장 자연스럽다.
>
> 특히 Agent Skills가 부속품이 아니라 연구 대상 자체다.
>
> NemoClaw execution
>        ↓
> failure trace
>        ↓
> Ultra writes candidate SKILL.md
>        ↓
> OpenShell isolated evaluation
>        ↓
> NAT evaluator
>        ↓
> promote / reject
>
> OpenShell도 단순 보안 장식이 아니다.
>
> 새로 생성된 SKILL.md는 결국 agent에게:
>
> shell command 실행
>
> file 접근
>
> 외부 호출
>
> 등을 시킬 수 있는 untrusted executable instruction artifact다.
>
> 따라서 생성한 skill을 production library에 넣기 전에 sandbox에서 실행한다는 논리가 매우 자연스럽다.
>
> 단 하나 주의.
>
> 자작 skill을 NVIDIA Verified Skill처럼 표현하면 안 된다.
>
> 현재 NVIDIA 공식 catalog의 verified skill에는 signature/evaluation 구조가 있지만, skill-card-generator는 명시적으로 skill을 서명·승인·공개하지 않는다. 
> GitHub
> +1
>
> 즉:
>
> NVIDIA official skill + locally promoted custom skill
>
> 이라고 명확히 구분해야 한다.
>
> (4) 6일 완주 리스크: 중~상
>
> 가장 먼저 터질 병목:
>
> 재사용 가능한 실패 패턴이 있는 benchmark 설계
>
> 태스크가 전부 제각각이면 skill을 만들어도 재사용되지 않는다.
>
> 반대로 태스크가 너무 비슷하면 skill improvement가 그냥 memorization이다.
>
> 따라서 범용 computer agent를 하면 안 된다.
>
> 예를 들어 repository maintenance agent 하나로 제한해서:
>
> dependency inspection
>
> test diagnosis
>
> config editing
>
> log analysis
>
> 같은 4개 family를 만들고 각 family마다 여러 변형을 두는 것이 좋다.
>
> “5회 iteration 동안 계속 상승”까지 욕심낼 필요 없다.
>
> static 62% → promoted skills 79%
>
> 한 번만 명확하게 나와도 충분하다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> “자기진화 AI”를 버리고 “실패로부터 후보 Skill을 합성하고 unseen evaluation을 통과한 것만 배포하는 Skill CI/Compiler”로 정의하라.
>
> 6일 축소판
>
> 한 종류의 coding agent + 4개 task family만 두고, 실패에서 3~5개 후보 SKILL.md를 만든 뒤 frozen test 성공률이 실제 상승한 skill만 promotion한다.
>
> 기억할 한 문장
>
> “우리 에이전트는 실패를 기억하는 게 아니라 스킬로 컴파일하고, 처음 보는 문제에서도 효과가 있을 때만 그 스킬을 살아남깁니다.”
>
> 매우 강하다.
>
> I-14. Agent Driver's License
> (1) 페인포인트 실재성: 4.5/5
>
> 배포 전 agent validation 자체는 아주 현실적인 문제다.
>
> 하지만 “면허”라는 framing에는 제도적 권위 문제가 생긴다.
>
> 심사위원이:
>
> “누가 당신에게 면허를 발급할 권한을 줬습니까?”
>
> 라고 하면 답이 없다.
>
> 따라서 제품 가치가 있는 부분은 인증기관이 아니라:
>
> pre-deployment security attestation
>
> 이다.
>
> 즉 이름은 재미있지만 실제 제품은:
>
> Agent Deployment Safety Gate
>
> 에 가깝다.
>
> (2) baseline·지표 타당성: 2.5/5
>
> 현재 baseline인:
>
> 무시험 배포
>
> 는 너무 약하다.
>
> 그리고 더 큰 문제:
>
> AgentDojo + MCPTox + 최소권한 시험의 점수를 하나로 합쳐 “82점”처럼 만드는 건 통계적으로 근거가 없다.
>
> 서로 측정하는 것이 다르다.
>
> 또:
>
> OpenClaw 87 / Hermes 92 / LangChain 79
>
> 식으로 나오면 이것 역시 harness 자체 성능이라기보다:
>
> prompt
>
> model
>
> tool adapter
>
> test compatibility
>
> 차이일 수 있다.
>
> 따라서 단일 면허 점수보다 profile이어야 한다.
>
> 예:
>
> Benign utility       94%
> Prompt-injection ASR  7%
> Tool-poisoning ASR    4%
> Privilege violations  0/25
> Exfiltration          0/20
>
> 더 중요한 것은:
>
> 면허 발급 후 사고율
>
> 도 같은 시험 attack으로 측정하면 circular evaluation이라는 점이다.
>
> 반드시 certification set / hold-out attack set을 나눠야 한다.
>
> 즉:
>
> 시험 문제 → policy 생성
>            ↓
> 처음 보는 공격 → 실제 효과 검증
>
> 이어야 한다.
>
> (3) NVIDIA 스택 심도: 5/5
>
> 구현만 된다면 아주 높다.
>
> OpenShell이 시험장 자체다.
>
> NemoClaw의 현재 CLI는 OpenClaw 외에 Hermes와 LangChain Deep Agents 같은 설치된 agent variant도 선택할 수 있는 구조를 공식적으로 지원한다. 따라서 “같은 환경에서 agent harness 교체”라는 실험은 허황된 요소는 아니다. 
> NVIDIA Docs
>
> 하지만 scope가 문제다.
>
> 또 하나 중요한 수정:
>
> signed license = NVIDIA skill-card-generator가 서명
>
> 은 안 된다.
>
> skill-card-generator는 공식적으로 draft governance card를 생성하는 것이고 signing/approval 역할을 하지 않는다. 
> GitHub
>
> 직접 만든 key로 결과 JSON에 cryptographic signature를 붙이는 것은 가능하다.
>
> 그러나 그것은:
>
> “우리 시험 결과가 변조되지 않았다는 서명”
>
> 이지:
>
> “NVIDIA가 인증했다”
>
> 가 아니다.
>
> 이 구분은 반드시 해야 한다.
>
> (4) 6일 완주 리스크: 상
>
> 가장 먼저 터질 병목:
>
> 서로 다른 benchmark를 하나의 agent interface로 통합하는 adapter
>
> 다.
>
> I-01 + I-02 + I-03을 합쳤다는 자인 그대로다.
>
> 게다가 harness 3종까지 한다면 위험도가 더 올라간다.
>
> 이걸 그대로 시작하면 마지막 날:
>
> AgentDojo adapter 70%
>
> MCP adapter 60%
>
> policy generation 50%
>
> dashboard 30%
>
> 상태가 될 가능성이 높다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> “면허시험소” 대신 하나의 agent에 대해 security test → 최소권한 policy → unseen attack 재검증까지 수행하는 Deployment Attestation Gate로 축소하라.
>
> 6일 축소판
>
> NemoClaw agent 하나 + MCPTox subset + 자체 filesystem/network attack 20건만 시험하고, 결과표·최소권한 YAML·서명된 attestation.json을 발급한다.
>
> 기억할 한 문장
>
> “에이전트를 믿고 배포하지 않습니다. 공격 시험을 통과한 권한만 운영 환경으로 가져갑니다.”
>
> “면허”라는 말을 안 써도 더 강하다.
>
> I-15. A2A 최소권한 협상 브로커
>
> 여기는 현재 구상에 실제 기술 수정이 필수다.
>
> OpenShell 공식 schema상:
>
> filesystem: static
>
> process: static
>
> network: runtime hot-reload
>
> inference: runtime 변경
>
> 이다. filesystem/process 권한을 새로 주려면 sandbox를 다시 만들어야 한다. 
> NVIDIA Docs
> +1
>
> 따라서 현재의:
>
> 파일/네트워크/바이너리 권한을 모두 TTL로 임시 발급
>
> 은 구현할 수 없다.
>
> (1) 페인포인트 실재성: 4.5/5
>
> 문제 자체는 상당히 좋다.
>
> 멀티에이전트에서 상위 agent가 하위 agent에게 task를 넘기면 흔히 하위 agent들이 넓은 공통 credential과 network permission을 공유한다.
>
> cloud IAM에서:
>
> short-lived credential / scoped token
>
> 이 중요한 이유와 동일하다.
>
> Agent 세계에서도 자연스러운 문제다.
>
> 그리고 기존 아이디어들과 달리 멀티에이전트 특유의 문제라는 점이 좋다.
>
> (2) baseline·지표 타당성: 4/5
>
> 현재의:
>
> paths + domains + binaries × time
>
> 은 하나의 숫자로 합치면 의미가 이상해진다.
>
> 경로 하나와 domain 하나가 같은 위험 단위가 아니기 때문이다.
>
> 따라서 따로 재야 한다.
>
> 예를 들면:
>
> Network exposure
> = Σ allowed-domain-seconds
>
> Filesystem exposure
> = Σ readable-path-seconds
>
> Credential exposure
> = Σ credential-scope-seconds
>
> 그런데 filesystem은 runtime 변경이 안 되므로 첫 데모에서는 빼는 것이 맞다.
>
> 그러면 아주 깨끗해진다.
>
> allowed-domain-seconds ↓
>
> granted credential-seconds ↓
>
> benign task success
>
> over-privilege request rejection rate
>
> expired grant attack success rate
>
> delegation overhead P95
>
> 그리고 공격도 쉬운 게 있다.
>
> Agent B가:
>
> github.com 접근권한을 30초 받음
>
> task 완료
>
> TTL 종료
>
> 다시 호출 시도
>
> 했을 때:
>
> baseline 성공 / ours deny
>
> 를 보여주면 된다.
>
> (3) NVIDIA 스택 심도: 5/5 — 범위를 고친다는 전제
>
> NAT의 A2A는 현재 단순 experimental concept 수준은 아니다. 공식 최신 문서에서 A2A client/server, agent discovery, delegation을 지원하고 nvidia-nat[a2a] 패키지로 제공한다. OAuth2/JWT와 scope 검증도 지원한다. 
> NVIDIA Docs
> +1
>
> 따라서 A2A 자체의 6일 구현 가능성은 생각보다 좋다.
>
> 단 중요한 구분:
>
> A2A가 “권한 협상 프로토콜”을 제공하는 것은 아니다.
>
> A2A는:
>
> Agent Card
>
> discovery
>
> delegation
>
> communication
>
> 을 표준화한다. 
> NVIDIA Docs
>
> 즉:
>
> required_capabilities:
>   network:
>     - api.github.com
>   ttl: 30
>
> 같은 것은 당신들이 만든 broker contract다.
>
> 그걸 A2A 위에서 전달하는 것.
>
> 이렇게 설명하면 전혀 문제 없다.
>
> OpenShell의 dynamic network policy가 실제 enforcement를 담당하므로 architecture core도 매우 강하다. OpenShell은 network egress를 deny-by-default로 두고 runtime policy update/set을 지원한다. 
> NVIDIA Docs
>
> (4) 6일 완주 리스크: 현재 상 → 축소 후 중
>
> 가장 먼저 터질 병목:
>
> grant/revoke와 agent task lifecycle의 동기화
>
> 예를 들어:
>
> task가 29초에 아직 실행 중
>
> TTL은 30초
>
> 재시도 발생
>
> 두 agent가 동시에 같은 grant 요청
>
> 같은 문제다.
>
> 하지만 해커톤에서는 distributed lease manager를 완성할 필요 없다.
>
> 두 agent + 한 broker면 충분하다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> 모든 권한의 동적 협상을 포기하고, filesystem/process는 사전 정의 sandbox profile로 고정한 채 “A2A task별 network/credential lease”만 TTL로 발급하라.
>
> 이렇게 바꾸면 갑자기 구현 가능한 좋은 아이디어가 된다.
>
> 6일 축소판
>
> A2A parent 1개 + subagent 2개에서 broker가 한 task에 필요한 domain 하나를 30초만 OpenShell에 허용하고, 만료 전·후 공격을 비교한다.
>
> 기억할 한 문장
>
> “서브에이전트에게 서버 권한을 주는 게 아니라, 그 작업에 필요한 한 도메인을 30초 동안 빌려줍니다.”
>
> 이번 배치에서 가장 즉각적으로 이해되는 기술 문장이다.
>
> I-16. 에어갭 에이전트
> (1) 페인포인트 실재성: 5/5
>
> 특히 한국에서는 문제 설명이 쉽다.
>
> 공공
>
> 국방
>
> 의료
>
> 금융
>
> 제조 IP
>
> 등 외부 inference API 자체가 허용되지 않는 조직이 존재한다.
>
> 따라서 “Cloud AI를 못 쓰는 조직에서도 agent를 쓸 수 있느냐”는 명확한 industrial pain이다.
>
> 하지만 단순히:
>
> local LLM + local RAG
>
> 이면 차별성이 약하다.
>
> 진짜 차별점은:
>
> 공격당한 agent도 Internet으로 1 byte도 성공적으로 못 보내는 것을 kernel/network policy로 증명
>
> 하는 것이다.
>
> (2) baseline·지표 타당성: 3.5/5
>
> 현재:
>
> egress 시도 건수 = 0
>
> 는 좋은 metric이 아니다.
>
> 왜냐하면 아무도 egress를 시도하지 않았을 수도 있기 때문이다.
>
> 게다가 공격을 주입하면 당연히 시도 건수는 0보다 커진다.
>
> 재야 하는 것은:
>
> successful external egress bytes = 0
>
> 이다.
>
> 공격셋에서는:
>
> attempted exfiltrations
>
> blocked exfiltrations
>
> successful external connections
>
> external bytes transmitted
>
> 을 재면 된다.
>
> 그리고 offline quality trade-off:
>
> task success
>
> answer faithfulness
>
> retrieval recall
>
> P50/P95 latency
>
> tokens/sec
>
> VRAM peak
>
> 을 온라인 Ultra와 비교해야 한다.
>
> 결과가:
>
> Online Ultra   success 91%
> Offline Nano   success 85%
>
> Quality gap      -6%p
> Internet egress   0 B
>
> 라면 꽤 설득력 있다.
>
> (3) NVIDIA 스택 심도: 4.5/5
>
> 구조 자체는 매우 좋다.
>
> OpenShell은 외부 통신 불가를 약속하는 게 아니라 enforce하는 계층이 된다.
>
> Nemotron/NIM도 반드시 local이어야 하므로 핵심이다.
>
> 현재 공식 NIM support matrix를 보면 Nemotron 3 Nano 30B-A3B는 FP8 프로파일에서 단일 L40S를 지원하며 모델 파일 크기는 약 30.46GB다. 
> NVIDIA Docs
>
> 작은 Retriever를 고르면 훨씬 현실적이다. 예를 들어 300M Retriever embedding 모델은 non-optimized 구성 최소 GPU memory가 2.4GiB 수준이다. 
> NVIDIA Docs
>
> 따라서 48GB L40S에서:
>
> Nano FP8 + 작은 embedding model
>
> 이라는 구성 자체는 황당하지 않다.
>
> 다만 동시 NIM container overhead/KV cache/실제 workload까지 포함해 48GB 안에서 안정적으로 공존하는지는 실측이 필요하다. 모델 파일 크기만 더해서 “된다”고 하면 안 된다.
>
> 또 표현을 수정해야 한다.
>
> network deny-all(inference.local 포함)
>
> 은 local NIM을 sandbox 밖에서 호출하는 구조라면 모순될 수 있다.
>
> OpenShell의 inference.local은 sandbox 내부의 local endpoint이지만 gateway가 설정된 backend로 전달한다. 
> NVIDIA Docs
>
> 따라서 목표 정책은:
>
> Internet egress deny-all + approved local inference path only
>
> 가 더 정확하다.
>
> 진짜 air-gap은 이미지/model weights까지 사전 반입한 뒤 물리적으로 인터넷을 끊는 deployment mode로 설명하면 된다.
>
> (4) 6일 완주 리스크: 상
>
> 이것은 소프트웨어 병목이 아니다.
>
> 가장 먼저 터질 병목:
>
> 예선 기간에 48GB급 NVIDIA GPU를 실제 확보할 수 있는가
>
> 다.
>
> 사용자 조건대로 L40S 크레딧이 본선 10팀부터라면, 팀에 이미 적절한 GPU가 없는 이상 예선 GitHub에서:
>
> “완전 offline Nemotron Nano NIM을 실제 실행했다”
>
> 를 증명하기 어렵다.
>
> remote NIM API를 쓰면서 air-gap이라고 부를 수도 없다.
>
> 그래서 이 아이디어는 본선 아이디어로는 매우 좋고 예선 아이디어로는 나쁘다.
>
> G1을 엄격하게 적용하면 하드웨어가 없는 경우 탈락이다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> 예선에 48GB GPU가 확보되지 않았다면 이 아이디어를 채택하지 말고, 확보되어 있다면 “air-gap RAG”가 아니라 “adversarial exfiltration을 0 successful bytes로 만드는 offline agent”로 초점을 옮겨라.
>
> 6일 축소판
>
> 48GB GPU가 이미 있다면 Nano FP8 + 작은 Retriever + OpenShell로 문서 QA 20건과 exfiltration 공격 20건만 수행하고 quality gap vs successful Internet bytes=0 두 숫자만 증명한다.
>
> GPU가 없다면 정직한 6일 축소판은 없다.
>
> 이건 중요하다.
>
> 기억할 한 문장
>
> “에이전트가 유출 명령을 그대로 따르더라도 민감 문서는 인터넷으로 1바이트도 나가지 않습니다.”
>
> 피칭 문장은 강하다.
>
> 배치 4 순위
> 1위 — I-13 Skill CI / 자기진화 스킬 라이브러리
>
> 현재 이름 그대로가 아니라 Skill CI/Compiler로 수정했을 때 1위다.
>
> 대회 요구사항인 Agent Skills를 가장 깊게 사용하면서:
>
> 생성
>
> 검증
>
> benchmark
>
> promotion
>
> persistent library
>
> 까지 하나의 loop로 만든다.
>
> 무엇보다 다른 팀이 npx skills add 하고 끝낼 때:
>
> 우리는 Skill 자체를 생성·평가·운영하는 시스템을 만들었다
>
> 가 된다.
>
> 독창성에서도 강하다.
>
> 2위 — I-15 A2A Ephemeral Capability Broker
>
> wild 아이디어 중 축소판이 가장 예쁘다.
>
> filesystem까지 욕심내면 실패한다.
>
> 하지만:
>
> A2A delegation → request capability → temporary network grant → execution → revoke
>
> 만 하면 6일 안에도 명확한 demo가 가능하다.
>
> A2A + OpenShell 두 기술이 서로 존재 이유를 만들어주는 점도 좋다.
>
> I-13보다 2위인 이유는 custom permission contract 부분이 아직 팀 설계이고, evaluation standard도 직접 만들어야 하기 때문이다.
>
> 3위 — I-14 Deployment Attestation Gate
>
> 큰 아이디어로는 매우 좋다.
>
> 하지만 사실상 I-01 + I-02 + I-03의 플랫폼화라 예선 6일에 하는 순간 각각의 증거가 얕아진다.
>
> 오히려 본선 진출 뒤 I-01/I-03을 확장해서 만들 제품명으로 매우 좋다.
>
> 즉:
>
> 예선 아이디어가 아니라 본선 roadmap
>
> 으로 두고 싶다.
>
> 4위 — I-16 Air-Gapped Agent
>
> 기술·산업 가치는 높다.
>
> 순위가 낮은 이유는 오직 하나다.
>
> D-6 시점에 필요한 GPU가 없다면 핵심 주장을 실행으로 증명할 수 없다.
>
> 본선에서 L40S가 지급되는 순간 평가가 완전히 달라진다.
>
> 그때는 오히려 상위권 후보다.
>
> 네 개를 5분 피칭 문장 하나씩 다시 압축하면
>
> I-13
>
> “실패를 프롬프트에 쌓지 않고 SKILL.md로 컴파일한 뒤, 처음 보는 문제에서도 성능을 높이는 스킬만 살아남깁니다.”
>
> I-14
>
> “에이전트를 믿고 배포하지 않고, 실제 공격 시험으로 필요한 권한을 증명한 뒤 그 정책만 운영으로 가져갑니다.”
>
> I-15
>
> “서브에이전트에게 계정 권한을 주는 대신, 그 작업에 필요한 한 도메인을 30초만 빌려줍니다.”
>
> I-16
>
> “에이전트가 공격자의 유출 명령을 따르더라도 인터넷으로 성공적으로 나가는 민감 데이터는 0바이트입니다.”
>
> 현재까지 나온 아이디어 중에서도 I-13은 상당히 주의 깊게 보존할 가치가 있습니다. 처음 설명의 “self-evolving”을 그대로 쓰면 허황되지만, Skill synthesis → sandbox eval → promotion이라는 CI 시스템으로 한 단계만 현실화하면 오히려 대회의 Skill API 요구조건을 가장 공격적으로 활용하는 아이디어 중 하나가 됩니다.

---

## 턴 6 — 배치 5/5 허황형 2차 (I-17~I-20)

### 내가 보낸 프롬프트

```text
[배치 5/5 — 허황형 2차. 같은 형식 + "6일 축소판" 한 문장.]

I-17. 합성 시민 600만 명 스트레스 테스트 — Nemotron-Personas-Korea로 공공 서비스 에이전트를 세그먼트별로 깨뜨리기
- 아이디어: NVIDIA가 공개한 한국 특화 합성 페르소나 데이터셋(HF nvidia/Nemotron-Personas-Korea, 약 600만 건, KOSIS·대법원·건보공단 기반 인구통계·지역·직업 분포)에서 페르소나를 층화 샘플링 → 각 페르소나가 "민원인 시뮬레이터 에이전트"가 되어 대상 서비스 에이전트(예: 서울시 대피소 안내/복지 상담 에이전트)와 대화 → 세그먼트(연령·지역·언어 수준·장애)별 실패율·오안내율을 산출. data-designer 스킬로 페르소나별 시나리오 자동 생성, rag-eval로 채점.
- baseline: 단일 "평균 사용자" 페르소나 평가 / 사람이 쓴 테스트 20건.
- 지표: 세그먼트별 태스크 성공률 분산(형평성 갭), baseline이 놓친 실패 유형 수, 발견된 실패당 비용, 커버리지(인구 분포 대비 테스트 분포 KL).
- 스택: Nemotron-Personas-Korea(NVIDIA 자산+한국 맥락), data-designer, rag-eval, Nemotron Nano(시뮬레이터 수백 개 병렬)/Ultra(대상 에이전트), nvidia-nat, OpenShell(시뮬레이터가 실제 API를 때리지 못하게 격리).
- 허황 포인트: "시뮬레이터가 실제 시민을 대표하는가" 검증 불가. LLM이 LLM을 평가하는 순환. OpenShell 역할 약함.

I-18. 에이전트 보험 언더라이터 — 에이전트별 리스크 점수 → 보험료
- 아이디어: 에이전트의 정책 표면(허용 도메인·경로·바이너리 수), 벤치마크 점수(AgentDojo ASR, MCPTox ASR), 감사 로그 이력(deny 빈도, 이상 패턴)을 종합해 "사고 확률"을 추정하고 보험료/배포 등급을 산정. 보험사·컴플라이언스 부서 대상.
- baseline: 정성 체크리스트(현재 관행).
- 지표: 리스크 점수와 held-out 공격셋 실제 사고율의 상관(AUC), 등급별 사고율 분리도.
- 스택: OpenShell 감사 로그·정책 파싱(코어), Nemotron, nvidia-nat.
- 허황 포인트: 실제 사고 데이터가 없음(전부 시뮬레이션). 보험 상품은 존재하지 않음. 사실상 I-14의 채점표 부분.

I-19. NemoClaw 스웜 시티 — 자치구 25개 × 샌드박스 에이전트 25개가 서울 재난 대응을 분산 협업
- 아이디어: 자치구별 에이전트가 각자 OpenShell 샌드박스에서 자기 구 데이터만 접근(정책으로 타 구 데이터 차단) → A2A로 인접 구와 대피소 여유 용량 협상 → 전역 cuOpt 대신 분산 협상으로 대피 배분. I-05의 스웜 버전. "데이터 주권(구별 격리)"을 정책으로 강제한 멀티에이전트.
- baseline: 중앙집중 cuOpt 전역 최적해(상한) / 무협상 독립 배정.
- 지표: 분산 협상 해 vs 전역 최적 갭(%), 협상 라운드 수·지연, 타 구 데이터 접근 시도 차단 건수, 장애 구 1개 탈락 시 복원력.
- 스택: NemoClaw 멀티 인스턴스, OpenShell 정책 25개(자동 생성), nvidia-nat A2A, cuOpt(로컬 해), Nemotron Nano(구 에이전트)/Ultra(조정).
- 허황 포인트: 샌드박스 25개 자원. 분산 협상이 전역 최적보다 나을 이유가 없음 — 오직 "데이터 격리 하에서 얼마나 손실이 적은가"가 논점.

I-20. AI 입법 보좌관 — 법령 조문 간 충돌·중복·공백 자동 탐지 (국가법령정보 API 191종)
- 아이디어: 법령 본문·조항호목·법령용어 연계 그래프를 NeMo Retriever로 인덱싱 → 멀티홉 에이전트가 "A법 제n조와 B법 제m조가 같은 행위에 상반된 의무를 부과" 같은 충돌 후보를 탐지 → 근거 조문 인용 리포트. 국회·법제처·기업 컴플라이언스 대상.
- baseline: 키워드 공동 출현 / 단일 홉 RAG.
- 지표: 알려진 충돌 사례 골든셋(법제처 정비 사례·판례로 구성) Recall@k, 인용 정확도, 홉 수.
- 스택: NeMo Retriever, Nemotron Ultra(추론), nvidia-nat, OpenShell(법령 API 외 egress 차단).
- 허황 포인트: 국가법령정보 API 승인 기간 미확인(G6 위험). 골든셋 구축이 법률 전문성 필요. OpenShell 장식. "충돌"의 법적 정의가 모호.

각각 5개 형식 + 6일 축소판. 마지막에 4개 순위 + 기억할 한 문장.
```

### ChatGPT 응답

> 이번 배치는 아이디어가 과감한 만큼 “무엇을 증명한다고 주장하느냐”를 잘못 잡으면 바로 무너집니다. 특히 I-17은 실제 시민 대표성, I-18은 사고 확률, I-20은 법적 충돌이라는 말을 함부로 쓰면 안 됩니다. 반대로 I-19는 범위를 줄이면 생각보다 훨씬 기술적으로 선명합니다.
>
> 먼저 두 가지 데이터 정정부터 하겠습니다. 현재 Hugging Face의 Nemotron-Personas-Korea 공개 데이터셋은 1,000,000 records로 표시되고, 한 레코드 안에 여러 persona variant가 있습니다. NVIDIA collection 쪽은 현재 Korea를 7M personas라고 표기하는 반면 초기 자료에는 6M이라는 표현도 존재했습니다. 제출물에는 그냥 “600만 명”이라고 박기보다 “1M records / multi-persona variants 기반 대규모 한국 합성 페르소나”처럼 정확하게 쓰는 편이 안전합니다. 
> Hugging Face
> +1
>
> I-17. 합성 시민 스트레스 테스트
> (1) 페인포인트 실재성: 4/5
>
> 문제 자체는 좋습니다.
>
> 공공 서비스 agent를 평균적인 20개 질문으로 테스트하면:
>
> 고령자
>
> 특정 지역
>
> 낮은 디지털 문해도
>
> 다양한 직업·가구 유형
>
> 같은 subgroup failure가 묻힐 수 있습니다.
>
> 특히 NVIDIA 데이터셋 자체가 한국의 실제 인구통계·지리 분포를 바탕으로 합성되었고 age, education, occupation, district, province 등 다양한 속성을 제공하므로 한국 특화 stress test generator라는 방향은 상당히 자연스럽습니다. 
> Hugging Face
>
> 하지만 현재 표현의:
>
> “시민 600만 명을 테스트한다”
>
> 는 버려야 합니다.
>
> 600만 persona를 실제 inference할 이유도 없고, 통계적으로도 필요 없습니다.
>
> 또 장애는 현재 공개 schema에서 명시적인 대표 속성으로 확인되지 않습니다. 데이터에 없는 민감 특성을 임의로 생성해서 실제 분포처럼 말하면 위험합니다.
>
> (2) baseline·지표 타당성: 3/5
>
> 현재 가장 위험한 지표는:
>
> 형평성 gap
>
> 입니다.
>
> 합성 persona에서 65세 저학력 persona 성공률 72%가 나왔다고 해서:
>
> 실제 65세 저학력 시민 성공률이 72%
>
> 라고 말할 수 없습니다.
>
> 따라서 이 프로젝트가 측정하는 것은 fairness 자체가 아니라 behavioral robustness across synthetic strata입니다.
>
> 용어를 바꾸는 것이 중요합니다.
>
> 좋은 지표:
>
> segment task success rate
>
> worst-group success rate
>
> max-min segment gap
>
> baseline test set이 발견하지 못한 distinct failure modes
>
> failure discovery rate / 100 runs
>
> test coverage entropy
>
> cost / unique failure discovered
>
> 현재 제안한 KL divergence도 조심해야 합니다.
>
> 실제 인구분포를 그대로 복제하는 것보다 테스트에서는 오히려 희귀 subgroup을 oversample하는 것이 유리할 수 있습니다.
>
> 따라서 두 모드로 나누면 좋습니다.
>
> Population-weighted test
> → 실제 분포와 비슷한 안정성 추정
>
> Stress test
> → 희귀/취약 segment 의도적 oversampling
>
> 또 하나 결정적 약점:
>
> LLM user simulator → LLM target → LLM judge
>
> 세 단계가 모두 유사 모델이면 correlated error가 생깁니다.
>
> 그래서 gold task의 성공 여부는 가능한 한 deterministic evaluator로 만들어야 합니다.
>
> 예:
>
> “서울 강서구 대피소 중 조건 X에 맞는 위치를 정확히 반환했는가?”
>
> 는 정답 set 비교로 평가해야지 LLM judge에게 맡기지 않는 편이 낫습니다.
>
> NVIDIA rag-eval 역시 RAGAS 기반 품질 평가에 적합한 도구지만 모든 task의 ground truth를 대신해주는 일반 agent evaluator는 아닙니다. 
> GitHub
>
> (3) NVIDIA 스택 심도: 4/5
>
> OpenShell은 약합니다.
>
> 하지만 NVIDIA 자산 활용 전체로 보면 꽤 강합니다.
>
> 특히:
>
> Nemotron-Personas-Korea
> → Data Designer
> → simulation
> → evaluation
> → failure clustering
>
> 이라는 흐름은 NVIDIA 고유성이 분명합니다. Data Designer skill도 실제로 synthetic dataset/pipeline 생성에 쓰도록 제공됩니다. 
> NVIDIA
> +1
>
> 문제는 내부 G2:
>
> OpenShell/NemoClaw가 architecture core인가?
>
> 입니다.
>
> 현재 OpenShell은:
>
> simulator가 production API를 때리지 못하게 막는다.
>
> 정도라 보조입니다.
>
> G2를 살리고 싶으면 대상 agent까지 sandbox 안에 넣고 fixture API를 사용해 실제 side effect 없이 전체 conversational workflow를 replay하는 구조가 낫습니다.
>
> 그래도 I-01/I-03만큼 core는 아닙니다.
>
> (4) 6일 완주 리스크: 중
>
> 가장 먼저 터질 병목:
>
> persona가 아니라 시나리오와 evaluator
>
> 입니다.
>
> persona 10만 개 추출하는 건 쉽습니다.
>
> 어려운 것은:
>
> “이 persona에게 이 질문에서 무엇이 성공인가?”
>
> 를 정의하는 것입니다.
>
> 수백 개 병렬 simulator부터 만들면 안 됩니다.
>
> 한 가지 서비스만 고르세요.
>
> 예를 들어 I-05가 살아 있다면:
>
> 서울 대피소 안내 agent
>
> 가 훨씬 좋습니다.
>
> 그러면 persona에 따라:
>
> 출발 지역
>
> 연령
>
> 이동 제약
>
> 질문 방식
>
> 만 변화시키고 정답 대피소/조건은 deterministic하게 평가할 수 있습니다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> “합성 시민으로 공정성을 증명한다”를 버리고 “평균 사용자 테스트가 놓치는 subgroup-specific failure를 자동 발굴하는 stress-testing system”으로 바꿔라.
>
> 6일 축소판
>
> 한국 persona 500~1,000개를 8~10개 segment로 층화해 단일 공공 서비스 agent를 테스트하고, 기존 20개 hand-written test 대비 새로 발견한 failure category 수와 worst-group success rate만 증명한다.
>
> 기억할 한 문장
>
> “평균 사용자 20명에게는 통과한 에이전트를, 한국의 서로 다른 사용자 1,000명으로 바꾸자 어디서 깨지는지 드러났습니다.”
>
> 이건 꽤 좋습니다.
>
> I-18. 에이전트 보험 언더라이터
> (1) 페인포인트 실재성: 3/5
>
> Agent risk assessment라는 pain은 실재합니다.
>
> 하지만 보험료 산정이라는 pain은 현재 아이디어가 만들어낸 것에 가깝습니다.
>
> 보험이 있으려면 최소한:
>
> 사고 정의
>
> exposure
>
> historical loss
>
> loss severity
>
> claim frequency
>
> 같은 actuarial 데이터가 있어야 합니다.
>
> 지금은 없습니다.
>
> 그래서:
>
> “이 agent 보험료는 월 $37입니다.”
>
> 라고 말하는 순간 credibility가 무너집니다.
>
> 반면:
>
> “어떤 agent부터 production 승인 심사를 강화해야 하는가”
>
> 라는 risk tiering 문제는 현실적입니다.
>
> (2) baseline·지표 타당성: 2/5
>
> 이 아이디어의 가장 큰 문제입니다.
>
> held-out 공격 성공률을 prediction target으로 삼으면 측정할 수 있는 건:
>
> benchmark attack susceptibility
>
> 이지:
>
> 실제 사고 확률
>
> 이 아닙니다.
>
> AUC가 0.9가 나와도 “보험 위험도 예측 AUC 0.9”라고 말하면 안 됩니다.
>
> 올바른 target은:
>
> held-out adversarial failure probability
>
> 정도입니다.
>
> 그리고 feature도 재검토해야 합니다.
>
> 예:
>
> deny log가 많음
>
> 이 높은 위험을 의미한다고 단정할 수 없습니다.
>
> 오히려 정책이 잘 작동하고 있기 때문에 deny가 많은 것일 수도 있습니다.
>
> 따라서 feature contribution을 명확히 해야 합니다.
>
> 추천 evaluation:
>
> held-out attack failure AUROC
>
> risk tier별 held-out ASR
>
> calibration error
>
> Brier score
>
> policy surface만 사용했을 때 vs benchmark 포함했을 때 AUC
>
> unseen attack-family generalization
>
> 특히 calibration이 중요합니다.
>
> risk score 0.8인 agent들이 실제 benchmark에서 약 80% 실패해야 probability라고 말할 수 있습니다.
>
> 그렇지 않으면 그냥 ranking score입니다.
>
> (3) NVIDIA 스택 심도: 3.5/5
>
> OpenShell policy parsing/audit은 자연스럽습니다.
>
> 하지만 사실상:
>
> OpenShell features
> + AgentDojo result
> + MCPTox result
> → classifier
>
> 입니다.
>
> Nemotron이 없어도 logistic regression/XGBoost가 더 적절할 수 있습니다.
>
> 오히려 LLM을 scoring engine으로 만들면 과학성이 내려갈 가능성이 큽니다.
>
> 그리고 사용자도 짚었듯이 I-14의 scoring subsystem으로 넣으면 자연스럽지만 단독 제품으로 만들 이유가 약합니다.
>
> (4) 6일 완주 리스크: 기술 중 / 주장 리스크 상
>
> 모델 자체는 하루에도 만들 수 있습니다.
>
> 진짜 병목:
>
> training example이 몇 개의 “agent”인가?
>
> 입니다.
>
> 공격 case가 1,000개 있다고 agent가 1,000개인 게 아닙니다.
>
> risk underwriting 모델을 학습하려면:
>
> 서로 다른 policy
>
> tool configurations
>
> model
>
> harness
>
> permissions
>
> 를 가진 다양한 agent configuration이 필요합니다.
>
> 예를 들어 50개 policy variant를 자동 생성해서 attack suite를 돌릴 수는 있습니다.
>
> 하지만 그러면 결국:
>
> synthetic agents에서 synthetic risk predictor를 학습
>
> 한 것입니다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> 보험·보험료를 완전히 버리고 Agent Risk Triage Score로 바꿔, 아직 실행하지 않은 공격셋에서 실제 취약도를 예측할 수 있는지만 검증하라.
>
> 6일 축소판
>
> 권한폭·정책·모델 구성이 다른 agent variant 30~50개를 자동 생성하고 절반 공격셋에서 risk score를 만든 뒤 unseen attack family에서 risk tier별 ASR이 분리되는지만 본다.
>
> 기억할 한 문장
>
> “공격을 전부 다시 돌리기 전에, 어떤 에이전트가 다음 보안시험에서 먼저 깨질지 선별합니다.”
>
> 보험 얘기를 빼면 훨씬 낫습니다.
>
> I-19. NemoClaw Swarm City
> (1) 페인포인트 실재성: 3.5/5
>
> “25개 자치구가 agent로 협상한다” 자체는 현실 문제에서 출발했지만 25 agent가 필요한 이유는 현재 약합니다.
>
> 실제 재난 대응에서 행정구역별 데이터 접근통제가 반드시 이 형태라는 증거도 없습니다.
>
> 즉:
>
> 서울이라서 25개 agent
>
> 는 gimmick으로 보일 위험이 있습니다.
>
> 하지만 문제를 다음처럼 바꾸면 꽤 좋습니다.
>
> 데이터를 중앙으로 모을 수 없는 여러 조직이 제한된 정보만 공유하면서 resource allocation을 얼마나 잘할 수 있는가?
>
> 그러면 이것은:
>
> 병원
>
> 물류회사
>
> 지자체
>
> 계열사
>
> 등으로 일반화되는 privacy-constrained distributed optimization 문제가 됩니다.
>
> 갑자기 산업 가치가 커집니다.
>
> (2) baseline·지표 타당성: 5/5
>
> 이번 배치에서 평가 구조가 가장 좋습니다.
>
> baseline이 이미 아주 좋습니다.
>
> Upper bound:
> 중앙집중 cuOpt
>
> Lower bound:
> 각 구 독립 최적화
>
> Ours:
> 제한 정보만 공유하는 분산 협상
>
> 이 세 개면 trade-off가 명확합니다.
>
> 특히:
>
> global optimality gap
>
> 은 아주 강한 metric입니다.
>
> 예:
>
> Centralized optimum      100
> No coordination          137
> Private coordination     106
>
> Optimality gap           +6%
> Cross-domain raw access    0
>
> 5분 발표에서 매우 좋습니다.
>
> 추가 추천:
>
> global optimality gap
>
> constraint violations
>
> negotiation rounds
>
> bytes/messages exchanged
>
> raw cross-domain data accesses
>
> convergence time
>
> one-agent failure degradation
>
> recovery time
>
> 그리고 “차단 건수”보다는:
>
> unauthorized access success = 0
>
> 가 더 강합니다.
>
> (3) NVIDIA 스택 심도: 5/5
>
> 고친 I-19는 매우 강합니다.
>
> A2A는 현재 NAT에서 client/server, discovery, delegation을 실제 지원하는 기능입니다. 
> NVIDIA Docs
> +1
>
> 그리고:
>
> OpenShell → data boundary enforcement
>
> A2A → limited exchange
>
> cuOpt → local constrained optimization
>
> Nemotron → negotiation / explanation
>
> NemoClaw → multi-agent harness
>
> 각 기술의 역할이 서로 다릅니다.
>
> 이건 “NVIDIA 기술 5개 넣었습니다”가 아니라 각 layer가 구조적 이유가 있습니다.
>
> 다만 25개 sandbox를 돌릴 이유는 없습니다.
>
> 심사위원은 숫자 25 자체에 점수 주지 않습니다.
>
> (4) 6일 완주 리스크: 현재 상 / 축소 후 중
>
> 가장 먼저 터질 병목:
>
> 분산 협상 알고리즘
>
> 입니다.
>
> LLM에게:
>
> “서로 협상해서 잘 배분해봐”
>
> 라고 하면 convergence도 재현성도 없습니다.
>
> 그래서 allocation protocol은 deterministic하게 만들어야 합니다.
>
> 예:
>
> 각 지역 공개 가능 정보:
> - 남는 capacity
> - neighboring region
> - marginal travel cost
>
> 비공개:
> - individual demand
> - raw residents
>
> agent는 구조화된 offer/request만 교환.
>
> LLM은 natural-language explanation이나 constraint interpretation에만 사용합니다.
>
> 그러면 평가 가능성이 급상승합니다.
>
> 그리고 25개 대신 3개 구로 하면 충분합니다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> “서울 25개 AI가 자율 협상”이라는 쇼케이스를 버리고 “원본 데이터를 공유할 수 없는 3개 지역이 최소 정보만 교환해 중앙최적의 몇 %까지 따라갈 수 있는가”라는 constrained distributed optimization 실험으로 바꿔라.
>
> 6일 축소판
>
> 인접 3개 자치구 sandbox만 만들고 각 구의 원본 수요는 격리한 채 available capacity + marginal cost만 A2A로 교환해 중앙 cuOpt 최적해 대비 gap을 측정한다.
>
> 기억할 한 문장
>
> “데이터를 중앙에 모으지 않고도 필요한 숫자만 협상해서 전역 최적해의 94%까지 따라갔습니다.”
>
> 실제로 94%가 나왔을 때만 저 숫자를 쓰십시오.
>
> 구조적으로는 이번 배치 최고의 피치입니다.
>
> I-20. AI 입법 보좌관
>
> 먼저 G6 관련 중요한 수정이 있습니다.
>
> 현재 국가법령정보 공동활용 사이트에는 OPEN API 191건이 실제로 안내되어 있습니다. 그리고 신청 페이지에는 현재 명시적으로 “OPEN API 신청 시 자동승인 처리되며 바로 활용 가능”이라고 적혀 있습니다. 따라서 지금 확인되는 정보만 보면 승인 2주 위험은 예상보다 훨씬 낮습니다. 
> 법제처
> +1
>
> 단, 별도 이용안내에는 담당자가 신청내용 확인 후 승인한다는 일반 절차 설명도 남아 있어 페이지 간 표현이 완전히 일치하지는 않습니다. 하지만 D-6인 지금 바로 신청해서 실제 키 발급 여부를 확인할 가치가 있습니다. 
> 법제처
>
> (1) 페인포인트 실재성: 5/5
>
> 법령 사이의:
>
> 인용
>
> 위임
>
> 용어 정의
>
> 개정 영향
>
> 규정 중첩
>
> 을 사람이 추적하는 것은 명백히 어려운 문제입니다.
>
> 국가법령정보 API에도 조항호목 및 조문-법령용어 연계 API가 실제로 존재하기 때문에 knowledge graph 기반 구조도 현실성이 있습니다. 
> 법제처
> +1
>
> 그러나:
>
> “법률 충돌을 AI가 탐지한다”
>
> 는 너무 큰 주장입니다.
>
> 두 조항이 다른 의무를 규정한다고 실제 법적 충돌인 것은 아닙니다.
>
> 특별법 우선, 신법 우선, 적용대상, 요건, 예외, 위임관계 등 법해석이 필요합니다.
>
> (2) baseline·지표 타당성: 2.5/5
>
> 가장 큰 병목은 역시 gold set입니다.
>
> “알려진 충돌사례”가 있다고 해도:
>
> 정말 동일 유형인가?
>
> 법령 정비 사유가 충돌이었나?
>
> 단순 용어 정비인가?
>
> 중복 규정인가?
>
> 위임 누락인가?
>
> 를 분류해야 합니다.
>
> 법률 전문가 없이 6일 안에 제대로 된 100-case dataset을 만드는 것은 매우 어렵습니다.
>
> 또 hop 수는 좋은 metric이 아닙니다.
>
> 홉이 많다고 더 잘한 게 아닙니다.
>
> 오히려 불필요한 멀티홉은 오류를 늘립니다.
>
> 추천 metric은:
>
> candidate recall@k
>
> citation exactness
>
> article/paragraph localization accuracy
>
> false candidates / law pair
>
> evidence completeness
>
> human-review reduction
> 100개 조문 pair 중 사람이 읽어야 하는 수
>
> 입니다.
>
> 그리고 이름을 바꿔야 합니다.
>
> 충돌 탐지 → 잠재 규범 충돌 후보 검색
>
> 정도로.
>
> (3) NVIDIA 스택 심도: 2.5/5
>
> Retriever는 확실히 자연스럽습니다.
>
> Nemotron multi-hop reasoning도 맞습니다.
>
> NAT도 orchestration으로 사용 가능합니다.
>
> 하지만 OpenShell은:
>
> 법령 API만 허용
>
> 이 전부라면 장식입니다.
>
> 문제 본체는 사실:
>
> legal graph RAG
>
> 입니다.
>
> OpenShell을 빼도 거의 완전히 동일하게 동작합니다.
>
> 따라서 내부 G2를 엄격히 적용하면 현재 형태는 탈락입니다.
>
> 보안/Agent Skill 대회보다는 legal RAG hackathon에 더 잘 맞습니다.
>
> (4) 6일 완주 리스크: 상
>
> API 승인보다 제가 더 우려하는 병목은:
>
> gold set + legal semantics
>
> 입니다.
>
> API는 현재 자동승인이라고 명시되어 있으므로 의외로 빨리 해결될 수도 있습니다. 
> 법제처
>
> 하지만 API를 받은 순간부터 진짜 일이 시작됩니다.
>
> 법령 전체를 graph화하고, conflict ontology를 정의하고, 판례/정비사례까지 연결하려 하면 무조건 scope가 터집니다.
>
> (5) 살리려면 바꿔야 할 것 1개
>
> ‘법령 충돌 판단’을 포기하고 ‘개정된 한 조문이 인용·위임·용어 관계를 통해 영향을 줄 수 있는 다른 조문 후보를 찾아주는 Change Impact Analyzer’로 좁혀라.
>
> 이렇게 바꾸면 legal judgment 문제도 줄어듭니다.
>
> 예를 들어:
>
> A법 제10조의 용어 정의 변경
> → 이를 인용하는 시행령·시행규칙·다른 조문 후보 반환
>
> 은 훨씬 객관적으로 평가할 수 있습니다.
>
> 6일 축소판
>
> 하나의 법률군만 골라 조문·인용·위임·용어 graph를 만들고, 실제 과거 개정 20~30건에서 영향 조문 recall@k와 citation precision을 측정한다.
>
> 기억할 한 문장
>
> “법 하나가 바뀌었을 때 사람이 법전 전체를 다시 읽는 대신, 영향을 받을 조문 후보와 연결 근거부터 보여줍니다.”
>
> 원래 “충돌 탐지”보다 훨씬 방어 가능합니다.
>
> 배치 5 순위
> 1위 — I-19 Privacy-Constrained Swarm / Distributed Allocation
>
> 원안의 “25개 자치구 swarm”을 그대로 하면 1위가 아닙니다.
>
> 하지만 3지역 + data isolation + A2A 협상 + centralized optimum upper bound로 줄이면 매우 강합니다.
>
> 이유는 간단합니다.
>
> NVIDIA 기술 깊이 높음
>
> 숫자가 명확함
>
> baseline이 강함
>
> 문제 자체가 multi-agent여야 함
>
> OpenShell이 core
>
> 6일 축소판 존재
>
> 특히:
>
> privacy와 optimality 사이의 trade-off를 숫자로 보여준다
>
> 는 점이 훌륭합니다.
>
> 2위 — I-17 Synthetic Population Stress Tester
>
> NVIDIA 자산을 굉장히 잘 활용합니다.
>
> 그리고 Korea hackathon이라는 맥락과도 맞습니다.
>
> 하지만 절대로:
>
> “한국 시민을 대표한다”
> “형평성을 검증했다”
>
> 까지 넘어가면 안 됩니다.
>
> 포지셔닝은:
>
> diversity-aware failure discovery
>
> 입니다.
>
> 이렇게 제한하면 꽤 강합니다.
>
> 3위 — I-20 Legal Change Impact Analyzer
>
> 원래 AI 입법 보좌관 / 충돌 판정이면 4위권입니다.
>
> 그러나 Change Impact Analysis로 줄이면 꽤 좋아집니다.
>
> 또 사용자 우려와 달리 현재 국가법령정보 API 신청 페이지는 자동승인·즉시 활용이라고 명시하고 있고 API 가이드도 191건이 확인되므로 데이터 접근 G6 리스크는 상당히 낮아졌습니다. 
> 법제처
> +1
>
> 그럼에도 OpenShell/NemoClaw core성이 약해서 3위입니다.
>
> 4위 — I-18 Agent Insurance Underwriter
>
> “보험”을 붙이는 순간 근거 없는 산업 서사가 됩니다.
>
> Risk scoring subsystem 자체는 유용합니다.
>
> 하지만 독립 프로젝트로는:
>
> synthetic attacks → synthetic risk score → synthetic agent variants
>
> 라는 자기참조가 너무 많습니다.
>
> I-14에 흡수하는 편이 낫습니다.
>
> 5분 피칭에서 기억할 한 문장
>
> I-17
>
> “평균 사용자 테스트에서는 통과했지만, 한국 사용자 분포를 층화해 다시 테스트하자 특정 세그먼트에서만 반복되는 실패를 찾아냈습니다.”
>
> I-18
>
> “에이전트를 실제 공격하기 전에 어떤 구성이 가장 먼저 깨질지 risk tier로 선별합니다.”
>
> I-19
>
> “원본 데이터를 서로 공개하지 않은 세 조직이 최소 정보만 협상해 중앙집중 최적해에 얼마나 가까워질 수 있는지 숫자로 증명했습니다.”
>
> I-20
>
> “법 하나가 바뀌면 그 조문을 직접·간접으로 의존하는 다른 규정 후보와 연결 근거를 자동으로 찾아줍니다.”
>
> 이번 배치에서 하나를 살린다면 I-19를 ‘Swarm City’라는 보여주기식 이름보다 Privacy-Constrained Multi-Agent Optimization으로 재정의한 버전을 가장 높게 봅니다. 기술 4~5개를 쓰면서도 각 기술을 제거했을 때 구조가 실제로 무너지고, 무엇보다 중앙 최적해라는 강한 정답 upper bound가 있어서 숫자를 조작했다는 공격을 받기 어렵습니다.

---

## 턴 7 — 최종 종합 (TOP 8 / 하이브리드 / 팀별 / 추가 3개 / 공통 실수)

### 내가 보낸 프롬프트

```text
[최종 종합] 지금까지 I-01~I-20 전부를 놓고, 당신이 제안한 수정판 기준으로 답해 주세요.

1) 전체 종합 순위 TOP 8 (표: 순위 / ID / 수정판 한 줄 이름 / 총평 점수 100점 / 6일 리스크 / 한 줄 이유). 나머지 12개는 "폐기·본선용·흡수" 중 하나로 분류만.

2) 하이브리드 추천 2개: 서로 다른 아이디어를 결합해 "축1 NVIDIA 심도 + 축2 산업가치 + 축3 정량지표"를 동시에 최대화하는 조합. 각 조합에 대해 (a) 결합 논리 (b) 6일 스코프(하루 단위 마일스톤 6줄) (c) 반드시 뽑아야 할 숫자 3개 (d) 이 조합이 실패하는 시나리오 1개.

3) 팀 구성별 최종 추천: (a) 백엔드 2인 (b) 백엔드+데이터 3인 (c) 풀스택 4~5인. 각각 1개씩.

4) 우리가 놓친 아이디어 3개: 지금까지 나온 20개에 없고, NVIDIA가 "공식 GitHub Recipe 등재 + 글로벌 기술 블로그 피처"로 소개하고 싶어할 만한 것. 1개는 현실형, 1개는 허황형, 1개는 "NVIDIA 스택의 잘 안 알려진 기능을 파고드는 것". 각각 페인포인트 / baseline / 지표 / 스택 / 6일 축소판 포함.

5) 마지막으로, 이 20개 전체에서 발견한 공통 실수 패턴 3개(우리 팀이 아이디어를 낼 때 반복하는 버릇)를 지적해 주세요.
```

### ChatGPT 응답

> 종합하면, 예선 승률 관점에서 보안·AgentOps 계열이 여전히 상위권입니다. 이유는 산업가치가 공공/제조보다 커서가 아니라, 6일 안에 외부 benchmark 또는 frozen test로 숫자를 만들면서 OpenShell/NemoClaw를 코어로 둘 수 있기 때문입니다.
>
> 점수는 공식 배점이 공개되지 않았으므로, 공식 채점 순서와 팀의 G1~G6 하드게이트를 함께 반영한 제 종합점수입니다.
>
> 1) 전체 TOP 8
> 순위	ID	수정판 한 줄 이름	총평	6일 리스크	한 줄 이유
> 1	I-03	MCP Zero-Trust Supply-Chain Auditor	94	중	MCPTox 외부 골든셋 + 실제 OpenShell 동적 감사 + 명확한 기업 구매 이유가 동시에 있음
> 2	I-13	Skill CI/Compiler — 실패를 검증된 SKILL.md로 승격	92	중	대회 필수 Agent Skills 자체를 연구대상으로 만들며 독창성이 가장 높음
> 3	I-11	Agent CI — Real Side-Effect Replay Gate	91	중하	6일 완주성이 높고 GitHub 제출 방식 자체가 제품 데모가 됨
> 4	I-01	Least-Privilege Policy Synthesizer	90	중	observe→policy→attack→repair 폐루프가 OpenShell 존재 이유를 가장 잘 설명
> 5	I-10	Agent Inference Governor — Quality SLO 기반 Nano/Ultra 라우팅	87	중	비용이라는 강한 산업지표가 있고 BFCL로 Pareto를 숫자로 증명 가능
> 6	I-07	Safe Autonomous CVE Triage	86	중	인터넷+민감코드라는 실제 lethal-trifecta를 OpenShell이 직접 해결
> 7	I-15	A2A Ephemeral Capability Lease Broker	84	중	task별 임시 network/credential 권한이라는 multi-agent 고유 문제가 선명
> 8	I-19	Privacy-Constrained Multi-Agent Allocation	83	중	중앙 최적해라는 강한 upper bound가 있어 privacy↔optimality trade-off를 정직하게 측정 가능
> TOP 4를 다시 보면
>
> I-03은 가장 균형이 좋습니다. 제품, security, 외부 benchmark, OpenShell core가 모두 있습니다.
>
> I-13은 가장 “NVIDIA 해커톤답습니다.” 현재 NVIDIA Skills 자체도 SKILL.md 외에 skill card, 서명, 평가셋, benchmark 결과를 검증 체계로 묶고 있습니다. 여러분이 custom skill을 생성한 뒤 sandbox evaluation을 통과한 것만 promotion하는 구조는 NVIDIA가 이미 밀고 있는 “skill as governed artifact” 방향과 잘 맞습니다. 
> GitHub
> +1
>
> I-11은 가장 안전한 선택입니다. NeMo의 현재 agent evaluation도 final answer만이 아니라 tool-call accuracy와 trajectory 평가를 지원하므로 “행동 회귀를 잡는 CI”라는 방향이 기술적으로 자연스럽습니다. 
> NVIDIA Docs
> +1
>
> I-01은 가장 좋은 OpenShell 데모입니다. 단, 외부 평가셋 부족 때문에 I-03보다 한 단계 낮췄습니다.
>
> 나머지 12개
> ID	분류	이유
> I-02	흡수	독립 제품보다 I-03/I-01의 방어 ablation benchmark로 쓰는 편이 강함
> I-04	흡수	I-01의 운영 후 drift/feedback loop로 넣으면 가치가 생김
> I-05	본선용	지도·실제 도로망·데이터 정합성까지 갖출 시간이 더 필요
> I-06	폐기	실제 route baseline 부재 + G2 OpenShell core 미충족
> I-08	본선용	GPU·영상·라벨·customization 확보 후에는 매우 강한 시각적 데모
> I-09	폐기	잘 만들수록 deterministic DUR engine이 코어가 되어 대회 적합성이 떨어짐
> I-12	폐기	실제 fraud label 없이 합성 평가를 하면 핵심 숫자를 방어할 수 없음
> I-14	본선용	I-01+02+03이 완성된 다음 플랫폼으로 확장하기 좋은 형태
> I-16	본선용	L40S 확보 후에는 훨씬 강해지는 아이디어
> I-17	흡수	공공 서비스 agent의 stress-test/evaluation layer로 쓰는 것이 최선
> I-18	흡수	I-14의 risk triage subsystem이면 유용하지만 단독 제품은 약함
> I-20	폐기	별도 법률 해커톤이면 좋지만 G2와 6일 gold-set 조건에서 밀림
> 2) 하이브리드 추천 2개
> Hybrid A — MCP Zero-Trust Admission Controller
> I-03 + I-01
>
> 제가 지금 우승 확률만 놓고 하나를 선택한다면 이 조합이 1순위입니다.
>
> (a) 결합 논리
>
> I-03은:
>
> “이 MCP 서버를 믿어도 되는가?”
>
> 를 해결합니다.
>
> I-01은:
>
> “믿고 사용한다면 정확히 어떤 권한만 줘야 하는가?”
>
> 를 해결합니다.
>
> 결합하면:
>
> Candidate MCP Server
>         ↓
> Static Tool-Poisoning Inspection
>         ↓
> OpenShell Dynamic Behavior Audit
>         ↓
> Observed Capability Model
>         ↓
> Least-Privilege Policy Generation
>         ↓
> MCPTox + Runtime Red-Team
>         ↓
> Held-out Benign Validation
>         ↓
> PASS → policy.yaml + security report
> FAIL → reject
>
> 즉 단순 scanner가 아니라 MCP 서버의 production admission gate가 됩니다.
>
> 가장 좋은 부분은 OpenShell을 제거하면 이 제품의 핵심인:
>
> 실제 행동 관찰
>
> filesystem/network enforcement
>
> 최소권한 검증
>
> 이 사라진다는 것입니다.
>
> (b) 6일 스코프
>
> Day 1 — MCP client/fixture 3개 + benign/악성 서버 2~3개 + OpenShell sandbox 기본 실행을 끝냅니다.
> Day 2 — MCPTox subset benchmark와 no-defense/static-description baseline을 고정합니다.
> Day 3 — 재현 가능한 MCP 5개 이내에서 filesystem/network 실제 행동 audit과 declared-vs-observed diff를 구현합니다.
> Day 4 — Nemotron으로 최소권한 policy YAML을 생성하고 정책 적용 후 benign task 재실행까지 끝냅니다.
> Day 5 — poisoning/exfiltration/unauthorized-file 공격을 돌려 ASR와 기능 보존율을 산출합니다.
> Day 6 — evaluation script 한 방 실행, README reproducibility, 3개 그래프, PDF 제출문구만 정리합니다.
>
> (c) 반드시 뽑아야 할 숫자 3개
>
> Attack Success Rate: no defense X% → ours Y%
>
> Benign Utility: 정책 적용 전후 정상 tool task 성공률
>
> Privilege Surface Reduction: 허용 domain/path/action 수가 baseline보다 몇 % 줄었는가
>
> 가장 좋은 결과 그림:
>
> ASR 48% → 4%, benign utility 96%, privilege surface 71% 감소
>
> 숫자는 실제 실험 결과가 나오기 전에는 절대 미리 쓰면 안 됩니다.
>
> (d) 실패하는 시나리오
>
> 실제 MCP 서버 dependency와 인증 문제 때문에 dynamic audit adapter를 만드는 데 3일 이상 써버리는 경우.
>
> 그래서 원칙은 하나입니다.
>
> MCPTox 1,348개는 static benchmark, dynamic runtime은 5개 이하.
>
> Hybrid B — Verified SkillOps
> I-13 + I-11
>
> 이것은 가장 NVIDIA-native한 조합입니다.
>
> (a) 결합 논리
>
> I-13만 하면:
>
> “LLM이 알아서 skill을 만들었다.”
>
> 가 됩니다.
>
> I-11을 붙이면:
>
> “Skill이라는 production artifact를 만들고 CI로 검증해서 승격한다.”
>
> 가 됩니다.
>
> Agent task failure
>       ↓
> Failure trace
>       ↓
> Nemotron generates candidate SKILL.md
>       ↓
> OpenShell sandbox replay
>       ↓
> NeMo tool/trajectory evaluation
>       ↓
> Frozen task + regression suite
>       ↓
> improvement? ─ No → reject
>       │
>      Yes
>       ↓
> Local Skill Library Promotion
>
> 이 구조는 NVIDIA의 현재 Skills 체계가 skill에 평가셋·benchmark·governance artifact를 함께 두는 방향과도 맞습니다. 
> GitHub
> +1
>
> 단, custom skill은 NVIDIA-verified라고 부르면 안 됩니다.
>
> (b) 6일 스코프
>
> Day 1 — repository-maintenance agent 하나와 3~4개 task family, train/dev/frozen-test split을 고정합니다.
> Day 2 — no-skill / NVIDIA-skill / manual-skill baseline과 trace 저장을 구현합니다.
> Day 3 — 실패 trace → candidate SKILL.md 생성 pipeline을 만듭니다.
> Day 4 — OpenShell sandbox replay + success/tool-call/trajectory 평가 + promotion gate를 연결합니다.
> Day 5 — prompt/tool-description mutation을 20~30개 넣어 regression과 false-promotion을 측정합니다.
> Day 6 — iteration curve, frozen-test uplift, token graph와 재현 가능한 CLI를 정리합니다.
>
> (c) 반드시 뽑아야 할 숫자 3개
>
> Frozen-test success uplift: static skill 대비 몇 %p 상승했는가
>
> Promotion precision / regression rate: 승격한 skill 중 실제 unseen task에 도움이 된 비율
>
> Tokens per successful task: 성공 한 건당 토큰 소비 감소율
>
> 예쁜 그래프는:
>
> static skill → generated candidate → rejected/promoted → frozen test score
>
> 하나면 됩니다.
>
> (d) 실패하는 시나리오
>
> task family가 충분히 반복적이지 않아 생성한 skill이 다른 문제에 전혀 일반화되지 않는 경우.
>
> 즉 benchmark 설계가 이 프로젝트의 절반입니다.
>
> 3) 팀 구성별 최종 추천
> (a) 백엔드 2인 → Hybrid B: Verified SkillOps
>
> 가장 적합합니다.
>
> UI가 필요 없습니다.
>
> 한 명:
>
> agent / skill generation / OpenShell
>
> 다른 한 명:
>
> evaluation / CI / benchmark / README
>
> 로 정확히 쪼갤 수 있습니다.
>
> 외부 API adapter나 공공데이터 정제도 거의 없어서 2명 팀의 시간을 기술 본체에 쓸 수 있습니다.
>
> (b) 백엔드 + 데이터 3인 → Hybrid A: MCP Zero-Trust Admission Controller
>
> 가장 이상적인 구성입니다.
>
> Backend A: OpenShell + MCP runtime
>
> Backend B: policy generation + NemoClaw/NAT
>
> Data/Eval: MCPTox preprocessing, attack suite, metric pipeline
>
> 이렇게 나뉩니다.
>
> 특히 data 담당자가 평가 파이프라인을 전담하면 다른 두 명이 숫자를 마지막 날 만들려고 허둥거리는 상황을 방지할 수 있습니다.
>
> (c) 풀스택 4~5인 → I-19 수정판: Privacy-Constrained Multi-Agent Allocation
>
> 사람이 많을 때만 선택할 가치가 있습니다.
>
> optimization/data
>
> A2A
>
> OpenShell isolation
>
> backend orchestration
>
> 지도/협상 visualization
>
> 을 병렬로 만들 수 있기 때문입니다.
>
> 3개 지역만 사용하세요.
>
> 25개 agent는 인력 5명이어도 필요 없습니다.
>
> 최종 화면은:
>
> Central optimum / Isolated / Private coordination
>
> 세 개의 경로·capacity·optimality-gap 비교만 보여주면 됩니다.
>
> 4) 우리가 놓친 아이디어 3개
> A. 현실형 — Runaway Agent Circuit Breaker
> 페인포인트
>
> Agent가 tool error를 만나 무한 재시도하거나 plan loop에 들어가면:
>
> API 비용
>
> LLM 비용
>
> tool side effect
>
> rate-limit
>
> 가 폭발합니다.
>
> 이것은 “공격”이 없어도 production agent에서 발생할 수 있는 문제입니다.
>
> baseline
>
> max_steps=20
>
> 전체 workflow timeout 60초
>
> 같은 static safeguard.
>
> 방법
>
> NAT profiler에서:
>
> LLM calls
>
> repeated tool signature
>
> token velocity
>
> HTTP retry pattern
>
> 을 관찰합니다.
>
> Budget/loop anomaly가 발생하면 NemoClaw orchestrator가 workflow를 중단하고 OpenShell의 runtime-update 가능한 network policy에서 외부 tool endpoint를 즉시 제거합니다. OpenShell의 network policy는 filesystem/process와 달리 running sandbox에서 hot reload할 수 있습니다. 
> NVIDIA Docs
> +1
>
> 지표
>
> injected runaway에서 maximum cost exposure
>
> benign task completion rate
>
> false trip rate
>
> detection→egress-cutoff latency
>
> 스택
>
> OpenShell + NemoClaw + NAT profiler + Nemotron lightweight watchdog.
>
> 6일 축소판
>
> 정상 workflow 20개와 의도적으로 retry/loop를 만든 20개 workflow를 돌려 static max-step 대비 overspend prevented / false cutoff / cutoff latency 세 숫자만 측정합니다.
>
> 왜 NVIDIA recipe로 좋은가:
>
> “Agent security”를 prompt injection뿐 아니라 resource/cost containment까지 확장하는 아주 실무적인 패턴이기 때문입니다.
>
> B. 허황형 — Federated Agent Immune System
> 페인포인트
>
> 기업 A가 발견한 새로운 agent attack을 기업 B도 똑같이 당합니다.
>
> 그러나 각 기업은:
>
> 내부 prompt
>
> audit log
>
> customer data
>
> tool traces
>
> 를 공유할 수 없습니다.
>
> 아이디어
>
> 각 조직은 자기 OpenShell sandbox에서 공격 trace를 수집하고 local risk detector를 업데이트합니다.
>
> 원본 trace는 외부로 보내지 않고 NVFLARE로 detector/update만 federated aggregation합니다.
>
> 새로운 attack family가 한 곳에서 발견되면 다른 조직도 방어 모델이 개선되는 구조입니다.
>
> NVFLARE는 multi-client simulation과 federated recipe를 제공하고, 각 site 데이터는 local에 유지하면서 result filtering/privacy policy를 둘 수 있습니다. 
> GitHub
> +2
> NVIDIA FLARE
> +2
>
> baseline
>
> 각 조직이 자기 공격 데이터만 학습
>
> 중앙집중 데이터 pooling은 oracle upper bound
>
> 지표
>
> unseen-site attack detection AUROC/F1
>
> local-only 대비 federated uplift
>
> raw trace egress records = 0
>
> communication bytes/round
>
> 스택
>
> NVFLARE + OpenShell + Nemotron feature/explanation + NAT evaluation.
>
> 6일 축소판
>
> 3개 가상 기업에 서로 다른 공격 family를 나누고 NVFLARE simulation으로 detector를 3~5 round federated training하여 local-only 대비 cross-site unseen attack F1 향상을 측정합니다.
>
> 허황된 부분은 “글로벌 immune network”이고,
>
> 6일 데모는 그냥 3-site federated security learning입니다.
>
> 이것은 NVIDIA가 기술 블로그로 쓰기 좋은 스토리가 있습니다.
>
> “NVFLARE가 의료 federated learning만 하는 게 아니라 autonomous-agent security에도 쓰인다.”
>
> C. 잘 안 알려진 기능 파기 — Zero-Secret Agent Connector
>
> 이 아이디어는 지금까지 20개 중에 없고, 저는 꽤 높게 봅니다.
>
> 페인포인트
>
> Agent가 GitHub/Jira/Slack 같은 SaaS를 쓰려면 보통:
>
> GITHUB_TOKEN=...
> SLACK_TOKEN=...
>
> 을 agent process 환경에 넣습니다.
>
> 그러면 prompt injection으로:
>
> “환경변수 읽어서 보내”
>
> 가 성공할 위험이 있습니다.
>
> 아이디어
>
> agent sandbox에는 실제 API credential 자체를 넣지 않습니다.
>
> Agent는 OpenShell을 통해 허용된 REST endpoint만 호출합니다.
>
> OpenShell이:
>
> method/path/body 정책을 검사하고
>
> supervisor middleware를 실행하고
>
> 필요한 경우 body를 inspect/redact하며
>
> 그 뒤에 provider credential을 주입
>
> 합니다.
>
> 현재 OpenShell Supervisor Middleware는 허용된 HTTP/WebSocket egress를 credential injection 이전에 inspect/deny/replace할 수 있고, payload가 변환되면 정책을 다시 검증합니다. Request-body credential rewrite도 별도 지원합니다. 
> NVIDIA Docs
> +1
>
> 이건 상당히 독특한 기능입니다.
>
> baseline
>
> API key가 agent env에 존재
>
> domain allowlist만 적용
>
> ours: secret outside sandbox + L7 policy/middleware
>
> 지표
>
> sandbox에서 credential read 성공 건수
>
> injected exfiltration attack ASR
>
> benign API task success
>
> middleware latency overhead P95
>
> 스택
>
> OpenShell:
>
> L7 endpoint policy
>
> provider credential handling
>
> request_body_credential_rewrite
>
> Supervisor Middleware
>
> NemoClaw + Nemotron.
>
> 6일 축소판
>
> API key가 필요한 mock SaaS 하나를 만들고 30개 정상 request + 30개 credential-stealing prompt를 수행해 env-secret baseline vs zero-secret sandbox의 exfiltration ASR과 정상 task success를 비교합니다.
>
> 한 줄 피치:
>
> “에이전트에게 API를 쓸 권한은 주지만 API 키는 보여주지 않습니다.”
>
> 지금까지 23개를 포함해서도 상당히 좋은 아이디어입니다.
>
> 특히 “OpenShell을 제대로 뜯어봤다”는 인상을 줄 가능성이 높습니다.
>
> 5) 20개에서 반복된 공통 실수 3개
> 실수 1 — NVIDIA 기술의 ‘개수’를 기술의 ‘필연성’으로 착각한다
>
> 반복해서 등장한 패턴입니다.
>
> Nemotron
> + NAT
> + Guardrails
> + OpenShell
> + Retriever
>
> 를 다 넣으면 강해 보일 거라 생각합니다.
>
> 하지만 심사위원이 할 질문은 하나입니다.
>
> “OpenShell을 지우면 이 프로젝트가 여전히 작동합니까?”
>
> I-06, I-09, I-12, I-20은 거의 그대로 작동합니다.
>
> 그럼 스택 심도가 아닙니다.
>
> 앞으로 아이디어를 볼 때는 NVIDIA 기술마다 이 질문을 적용하세요.
>
> 이 component를 삭제하면 어떤 핵심 metric이 나빠지는가?
>
> 답이 없다면 제거하는 게 낫습니다.
>
> 오히려 NVIDIA 기술 3개가 구조적으로 연결된 프로젝트가 6개를 억지로 넣은 프로젝트보다 강합니다.
>
> 실수 2 — “숫자를 만들 수 있다”와 “그 숫자가 증거다”를 혼동한다
>
> 팀 규범은:
>
> 숫자로 증명 못 하면 채택하지 않는다.
>
> 인데 한 단계 더 추가해야 합니다.
>
> 외부인이 믿을 수 없는 숫자라면 숫자가 없는 것과 같다.
>
> 반복된 사례가:
>
> I-12 synthetic fraud → synthetic fraud detector 평가
>
> I-06 synthetic route → route 개선율
>
> I-01 자기 생성 공격 → 자기 방어 평가
>
> I-17 LLM simulator → LLM agent → LLM judge
>
> I-13 같은 held-out set을 반복 개선에 재사용
>
> 입니다.
>
> 앞으로 숫자는 네 등급으로 보세요.
>
> A: 외부 benchmark / 실제 label
> B: frozen held-out / oracle optimum
> C: 독립적으로 만든 deterministic fixture
> D: 우리가 생성하고 우리가 채점한 synthetic set
>
> 주요 headline metric은 A/B로 하나 이상 확보해야 합니다.
>
> D만 있는 아이디어는 자동 감점시키는 게 좋습니다.
>
> 실수 3 — 핵심 실험보다 제품 서사를 먼저 키운다
>
> 여러 번:
>
> “면허시험소”
>
> “보험 언더라이터”
>
> “600만 시민”
>
> “25개 자치구 swarm”
>
> “AI 입법 보좌관”
>
> “자기진화”
>
> 처럼 이름과 범위가 먼저 커졌습니다.
>
> 하지만 해커톤에서 기억되는 것은 시스템 크기가 아니라 보통 한 개의 반박하기 어려운 그래프입니다.
>
> 예를 들면:
>
> I-03
>
> Attack ASR vs Benign Utility
>
> I-13
>
> Iteration vs Frozen Test Success
>
> I-10
>
> Quality vs Cost Pareto
>
> I-19
>
> Privacy vs Global Optimality Gap
>
> 이게 먼저 있어야 합니다.
>
> 따라서 앞으로 아이디어를 낼 때 순서를 뒤집으세요.
>
> ① 어떤 한 문장의 가설을 증명할 것인가 → ② 어떤 그래프 하나로 증명할 것인가 → ③ 그 그래프를 만들 최소 시스템은 무엇인가 → 마지막에 제품 이름을 붙인다.
>
> 최종 결론
>
> 오늘 제가 팀의 기술 리드라면 이렇게 결정합니다.
>
> 가장 안전한 예선 승부:
> I-03 + I-01 = MCP Zero-Trust Admission Controller
>
> 가장 NVIDIA스럽고 독창적인 승부:
> I-13 + I-11 = Verified SkillOps
>
> 가장 기술적으로 야심찬 차별화:
> I-15 또는 I-19
>
> 그리고 지금부터 새 아이디어를 더 늘리지는 않겠습니다.
>
> D-6 시점에서 가장 큰 경쟁자는 다른 팀이 아니라 scope creep입니다.
>
> 특히 NVIDIA Skills가 현재 평가셋과 benchmark까지 skill artifact의 일부로 취급하고, NeMo Evaluator가 agent의 trajectory/tool-use까지 평가할 수 있는 상태라는 점을 보면, 저는 최종적으로 Hybrid A와 Hybrid B 두 개만 반나절짜리 feasibility spike를 한 뒤 하나를 즉시 고정하는 전략을 택하겠습니다. 
> github.com
> +1

---

*저장: 2026-09-23 00:10 KST. 응답 총 65,122자.*
