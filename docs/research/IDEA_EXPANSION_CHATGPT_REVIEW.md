---
title: "IDEA EXPANSION v3 — 아이디어 확장 23종 + ChatGPT 교차 비평"
doc_type: idea_review
version: 3.0
created_at: 2026-09-22T23:58+09:00
deadline: 2026-09-28T23:59+09:00
days_left: 6
reviewer: "ChatGPT (GPT-5.6 Sol, chatgpt.com 임시 채팅, 추론 강도 '매우 높음'), 총 7턴"
scoring_method: SCORING_GOLDEN_RULE.md v2.0 (하드 게이트 G1~G6) + ChatGPT 독립 점수
companion_docs:
  - IDEA_CANDIDATES.md            # v2.0 A~J (본 문서가 확장·대체)
  - SCORING_GOLDEN_RULE.md
  - DATA_AND_SKILL_INVENTORY.md
  - NVIDIA-FastCampus-Korea-Agentic-AI-Hackathon-2026.md
  - CHATGPT_REVIEW_TRANSCRIPT.md  # ChatGPT 응답 전문 (임시 채팅이라 여기에만 남음)
---

# IDEA EXPANSION v3

> **READ THIS FIRST (for agents)**
>
> - 태그 규칙: `[VERIFIED]` = 내가 공식 출처로 직접 확인 / `[CHATGPT]` = ChatGPT 주장, **미검증** / `[INFERRED]` = 추론 / `[UNVERIFIED]` = 확인 불가.
> - ChatGPT 점수(1~5, 100점)는 **ChatGPT의 독립 주관 점수**다. `SCORING_GOLDEN_RULE.md` 점수 체계와 다르며 대회 공식 평가가 아니다.
> - ChatGPT와의 대화는 **임시 채팅**으로 진행해 사용자 ChatGPT 기록에 남지 않는다. 응답 전문은 `CHATGPT_REVIEW_TRANSCRIPT.md`에만 있다.
> - 섹션 9(사실로 승격 금지)의 `[CHATGPT]` 항목을 검증 없이 제출서에 쓰지 말 것.
> - 이 문서는 **의사결정 입력**이다. 결론은 섹션 0과 5에 있지만 최종 선택은 팀 역량에 달렸다.

---

## 0. TL;DR

1. 기존 A~J(10개)를 **I-01~I-20(20개)로 확장**하고, ChatGPT가 추가 제안한 **N-A/B/C(3개)**까지 총 23개를 검토했다. 현실형 12 / 중간형 4 / 허황형 7.
2. ChatGPT 종합 TOP 4: **I-03 MCP 공급망 감사관(94) > I-13 Skill CI/Compiler(92) > I-11 Agent CI 회귀 게이트(91) > I-01 최소권한 정책 합성기(90)**. 전부 **보안·AgentOps 계열**이다. 이유는 "산업가치가 더 커서"가 아니라 **6일 안에 외부 벤치마크/frozen test로 숫자를 만들면서 OpenShell을 코어로 둘 수 있기 때문**.
3. 공공·제조 계열(I-05 대피, I-06 폐기물, I-08 SOP)은 "사회적으로 중요해 보이지만" **baseline 데이터의 진실성**(합성 경로, 직선거리, 샘플 실행)에서 공격당한다. I-06은 G2 미달로 폐기, I-05/I-08은 본선용.
4. 허황형 중 살아남은 것: **I-13(자기진화→Skill CI), I-15(A2A 권한 협상→네트워크 TTL 리스), I-19(스웜 시티→3지역 프라이버시 제약 분산 최적화)**. 공통점은 "이름을 줄이면 오히려 강해진다".
5. 추천 하이브리드: **A안 I-03+I-01 "MCP Zero-Trust Admission Controller"**(가장 안전한 예선 승부, 3인 팀), **B안 I-13+I-11 "Verified SkillOps"**(가장 NVIDIA스러운 승부, 2인 팀). 둘 다 반나절 feasibility spike 후 **하나를 즉시 고정**할 것.
6. 데이터 신규 확인 `[VERIFIED]`: AgentDojo(MIT), MCPTox(공개 GitHub), NVD API(키 없이 30초/5회), 서울시 지진옥외대피소(OA-21063, 공공누리 1유형), **국가법령정보 API 승인 1~2일**(기존 "미확인" 리스크 해소).

---

## 1. 방법론

| 단계 | 내용 |
|---|---|
| ① 정독 | 프로젝트 문서 7개(대회 브리프, 채점 규범, A~J 후보, 데이터·스킬 재고, 제안서 초안, 개발 규약, OpenShell 정책 레퍼런스) + 메모리의 인접 해커톤 우승작 분석 |
| ② 확장 | `DATA_AND_SKILL_INVENTORY.md` PART 4 조합 매트릭스 + 규약 문서에서 드러난 페인포인트(툴 description 드리프트, trifecta, 비밀 취급, MCP `tools/list` 불신)를 아이디어로 승격. 허황형은 의도적으로 7개 포함 |
| ③ 데이터 검증 | 신규 아이디어에 필요한 소스 5종을 공식 출처로 확인 (섹션 8) |
| ④ ChatGPT 교차 비평 | 임시 채팅 1개 세션. 턴1 컨텍스트(대회 규칙·G1~G6·스택·데이터·선행 대회 시그널) → 턴2~6 아이디어 4개씩 5배치 → 턴7 종합. 각 아이디어마다 고정 5항목(페인포인트 실재성 / baseline·지표 타당성 / NVIDIA 스택 심도 / 6일 리스크+첫 병목 / 살리려면 바꿀 것 1개) + 배치 순위 + "5분 피칭에서 기억할 한 문장" |
| ⑤ 사후 검증 | ChatGPT가 근거로 든 NVIDIA 문서 주장 6건을 공식 문서로 재확인 (섹션 9) |

ChatGPT에게 준 프레이밍: "심사위원 겸 냉정한 기술 리뷰어. 칭찬보다 반박 우선. 근거 없는 낙관 금지."

---

## 2. 아이디어 총람 (23개)

분류: 🟢 현실형 / 🟡 중간형 / 🔴 허황형. 최종: **추진** / **흡수**(다른 아이디어의 부품) / **본선용**(10/7 이후) / **폐기**.

| ID | 분류 | 아이디어 (수정판 이름) | 페인포인트 한 줄 | 데이터·골든셋 | 핵심 지표 (baseline → ours) | G2 OpenShell | ChatGPT 점수(1~5: 페인/지표/스택) | 최종 |
|---|---|---|---|---|---|---|---|---|
| **I-01** | 🟢 | Least-Privilege Policy Synthesizer (구 A) | OpenShell 정책 YAML을 사람이 손으로 씀 | 자체 trace (train/held-out 분리 필수) | 공격 ASR, held-out 정상 성공률, **권한 표면 감소%** | **코어** | 5 / 4 / 5 | **추진** (TOP 4) |
| **I-02** | 🟢 | 방어 계층 정량 비교기 (AgentDojo 2×2) | "가드레일만으로 충분한가" 데이터 없음 | AgentDojo 97 task/629 case `[VERIFIED]` MIT | Intent Compromise Rate vs **Side-effect Completion Rate** | 구현에 따라 5 또는 2 | 4 / 4 / 5~2 | **흡수** → I-03/I-01의 ablation |
| **I-03** | 🟢 | MCP Zero-Trust Supply-Chain Auditor | MCP tool description = 검증 안 된 프롬프트 표면. 최고 거부율 3% 미만 | MCPTox 1,348 case / 45 서버 `[VERIFIED]` | TPA ASR(무방어→ours), **Recall@1% FPR**, 정상 서버 오탐률 | **코어** | 5 / 5 / 5 | **추진** (TOP 1) |
| **I-04** | 🟢 | Agent SOC → 정책 drift 자동 패치 루프 | 감사 로그를 사람이 못 봄 | 자체 인시던트 + AgentDojo/MCPTox 트래픽 | F1, false alerts/1,000 events, **패치 후 benign regression** | 코어 | 4 / 3 / 4 | **흡수** → I-01 운영 루프 |
| **I-05** | 🟢 | 서울 지진 대피 재배분 (1개 자치구) | 최근접 쏠림·수용 초과 | 서울시 지진옥외대피소 OA-21063 `[VERIFIED]` + 행정동 인구 | capacity violation, **p95 대피시간**, 취약계층 worst-10% | 보조 | 5 / 3 / 4 | **본선용** (도로망 travel-time 필요) |
| **I-06** | 🟢 | 폐기물 수거·배차 (구 B) | 경로 조정을 사람이 함 | 실제 운행 데이터 **없음** | 주행거리 절감% (baseline이 합성) | **장식** | 4 / 2 / 3 | **폐기** (G2 미달) |
| **I-07** | 🟢 | Safe Autonomous CVE Triage | CVE 피드(신뢰불가)+사내 코드(민감)+리포트 송신 = trifecta | NVD API 2.0 `[VERIFIED]` + **reachable/unreachable 페어 픽스처 20~30개** | reachable vuln P/R/F1, exfil ASR, $/CVE | **코어** | 5 / 2.5→5 / 5 | **추진** (TOP 6) |
| **I-08** | 🟢 | 제조 SOP 감시 (구 C) → 자연어 SOP 등록 레이어 | 순서 위반→불량·사고 | 자체 라벨 영상 (병목) | 위반 F1, **false alarm/분**, FPS/p95 | 장식 | 5 / 4 / 5 (독창성 2) | **본선용** (NVIDIA 샘플 실행 위험) |
| **I-09** | 🟡 | 의약품 상호작용 (구 D) | 다제복용 검토 수작업 | 식약처 e약은요 + DUR | 금기 pair recall, **false negative율** | 장식 | 5 / 2.5 / 2.5 | **폐기** ("SQL JOIN이면 끝") |
| **I-10** | 🟡 | Agent Inference Governor (구 F) | 스텝별 모델 선택 기준 없음 → 비용 폭발 | BFCL V4 `[VERIFIED]` Apache-2.0 | 동일 정확도 비용 절감%, **routing regret vs Oracle**, p95 | 수정 후 4.5 (Secure Routing Gateway) | 5 / 4 / 3→4.5 | **추진** (TOP 5) |
| **I-11** | 🟡 | Agent CI — Real Side-Effect Replay Gate | tool description 한 줄 바꾸면 행동이 조용히 바뀜, 테스트 없음 | 자체 골든 트레이스 + **mutation 30개** + tau2 pass^k | mutation 탐지 recall/precision, **equivalent-change FP율** | 코어 (실제 툴 재실행 격리) | 5 / 4 / 4→5 | **추진** (TOP 3) |
| **I-12** | 🟡 | 실거래가 이상거래 탐지 | 자전거래·허위 신고 | 국토부 실거래가 (라벨 없음) | 합성 P/R (무의미) | 장식 | 4 / 1.5 / 2 | **폐기** |
| **I-13** | 🔴 | Skill CI/Compiler (구 "자기진화 스킬") | 같은 실패를 반복, 재사용 절차로 축적 못 함 | 자체 task family 4개 × **train/dev/frozen** split | **frozen test uplift**, promotion precision, tokens/성공 | 코어 (생성 스킬 = untrusted 실행 지침 → 샌드박스 검증) | 4 / 3.5 / 5 | **추진** (TOP 2) |
| **I-14** | 🔴 | Deployment Attestation Gate (구 "면허시험소") | 배포 전 표준 안전 시험 없음 | AgentDojo+MCPTox+자체 (인증셋/hold-out 분리) | 프로파일(단일 점수 금지) | 코어 | 4.5 / 2.5 / 5 | **본선용** (I-01+02+03 플랫폼화) |
| **I-15** | 🔴 | A2A Ephemeral Capability Lease Broker | 서브에이전트가 광역 권한 공유 | 자체 (2 subagent + 1 broker) | **allowed-domain-seconds↓**, 만료 후 공격 ASR, 위임 오버헤드 p95 | **코어** (네트워크 정책만 동적) | 4.5 / 4 / 5 | **추진** (TOP 7) |
| **I-16** | 🔴 | Air-Gapped Agent (인터넷 0바이트) | 망분리 조직은 클라우드 API 불가 | 자체 문서 QA 20 + exfil 공격 20 | **successful external egress bytes = 0**, 온/오프 품질 격차 | 코어 | 5 / 3.5 / 4.5 | **본선용** (예선에 48GB GPU 없음) |
| **I-17** | 🔴 | Diversity-aware Failure Discovery (Nemotron-Personas-Korea) | 평균 사용자 20건 테스트가 subgroup 실패를 놓침 | HF 데이터셋 (1M records × 7 variants, CC-BY-4.0 `[VERIFIED]`) + data-designer | **worst-group success**, 새로 발견한 failure category 수 | 보조 | 4 / 3 / 4 | **흡수** → 공공 서비스 에이전트 평가층 |
| **I-18** | 🔴 | Agent Risk Triage Score (구 "보험 언더라이터") | 어떤 에이전트부터 심사 강화할지 | 자체 agent variant 30~50 | unseen attack family AUROC, calibration | 코어(로그 파싱) | 3 / 2 / 3.5 | **흡수** → I-14 |
| **I-19** | 🔴 | Privacy-Constrained Multi-Agent Allocation (구 "스웜 시티") | 원본 데이터를 중앙에 못 모으는 조직 간 자원 배분 | 3 자치구 + 중앙 cuOpt 최적해 = **upper bound** | **global optimality gap%**, raw cross-domain access = 0, 협상 라운드 | **코어** (데이터 경계 강제) | 3.5 / 5 / 5 | **추진** (TOP 8, 4~5인 팀) |
| **I-20** | 🔴 | Legal Change Impact Analyzer (구 "AI 입법 보좌관") | 개정 영향 조문을 사람이 법전 전체 재독 | 국가법령정보 API 191종 (**승인 1~2일** `[VERIFIED]`) | 개정 20~30건 영향 조문 recall@k, citation precision | 장식 | 5 / 2.5 / 2.5 | **폐기** (G2, 법률 골든셋) |
| **N-A** | 🟢 | Runaway Agent Circuit Breaker (ChatGPT 제안) | 무한 재시도·plan loop로 비용·부작용 폭발 | 정상 20 + 주입 runaway 20 workflow | **max cost exposure**, false trip율, 탐지→egress 차단 지연 | 코어 (네트워크 정책 핫리로드 `[VERIFIED]`) | — | **추진 후보** |
| **N-B** | 🔴 | Federated Agent Immune System (NVFLARE) | A사가 발견한 공격을 B사도 당함, trace 공유 불가 | 3 가상 기업 × 공격 family | unseen-site attack F1 uplift, raw trace egress = 0 | 코어 | — | **본선용** |
| **N-C** | 🟢 | Zero-Secret Agent Connector | API 키가 에이전트 env에 있음 → 인젝션 한 방에 유출 | mock SaaS 1개, 정상 30 + 탈취 30 | credential read 성공 0, exfil ASR, middleware p95 | **코어** (`network_middlewares` + credential rewrite `[VERIFIED]`) | — | **추진 후보** (A안 부품) |

---

## 3. ChatGPT 종합 순위 vs 우리 규범

### 3-1. ChatGPT TOP 8 (수정판 기준, 100점)

| 순위 | ID | 수정판 이름 | 점수 | 6일 리스크 | ChatGPT 한 줄 이유 |
|---|---|---|---|---|---|
| 1 | I-03 | MCP Zero-Trust Supply-Chain Auditor | 94 | 중 | MCPTox 외부 골든셋 + 실제 OpenShell 동적 감사 + 명확한 기업 구매 이유 |
| 2 | I-13 | Skill CI/Compiler | 92 | 중 | 대회 필수 Agent Skills 자체를 연구대상으로. 독창성 최고 |
| 3 | I-11 | Agent CI — Real Side-Effect Replay Gate | 91 | 중하 | 완주성 최고, GitHub 제출 방식 자체가 데모 |
| 4 | I-01 | Least-Privilege Policy Synthesizer | 90 | 중 | observe→policy→attack→repair 폐루프가 OpenShell 존재 이유를 가장 잘 설명 |
| 5 | I-10 | Agent Inference Governor | 87 | 중 | 비용이라는 강한 산업지표 + BFCL Pareto |
| 6 | I-07 | Safe Autonomous CVE Triage | 86 | 중 | 실제 lethal trifecta를 OpenShell이 직접 해결 |
| 7 | I-15 | A2A Ephemeral Capability Lease Broker | 84 | 중 | multi-agent 고유 문제가 선명 |
| 8 | I-19 | Privacy-Constrained Multi-Agent Allocation | 83 | 중 | 중앙 최적해 upper bound로 정직한 측정 |

### 3-2. 기존 IDEA_CANDIDATES v2와 비교

| 기존 v2 순위 | 이번 ChatGPT 판정 | 변화 이유 |
|---|---|---|
| 🥇 A (87) 정책 자동생성 | I-01 → 4위(90) | 외부 골든셋 부재로 I-03에 밀림. "우리가 만든 공격을 우리가 막았다" 순환 지적 |
| 🥈 B (82) 배차 최적화 | I-06 → **폐기** | 실제 운행 데이터 없음 + OpenShell 장식(G2). **가장 큰 강등** |
| 🥉 C (79) SOP 감시 | I-08 → 본선용 | NVIDIA 공식 `deepstream-sop` 블루프린트와 동일 → "잘 설치했습니다" 위험 |
| D (74) 의약품 | I-09 → 폐기 | 잘 만들수록 deterministic DUR이 코어가 되어 대회 정합성 하락 |
| F (70) 라우터 | I-10 → 5위(87) | "제품형" 전환 방법(Governor YAML + Secure Routing Gateway)이 나와 **상승** |
| G (68) 합성 평가셋 | I-17로 재해석 → 흡수 | Nemotron-Personas-Korea로 한국 맥락 확보하되 단독 제품 아님 |
| (없었음) | I-03, I-11, I-13 신규 → TOP 3 | 규약 문서(02-*)의 페인포인트를 그대로 아이디어화한 것들이 상위 진입 |

`[INFERRED]` v2의 "A를 메인으로 B/C를 대상 에이전트로 감싼다"는 하이브리드는 이번 검토에서 **A안(I-03+I-01)으로 대체**하는 것이 합리적이다. B/C를 감싸면 대상 에이전트 데이터 문제가 그대로 딸려온다.

---

## 4. 아이디어별 상세 카드 (ChatGPT 반박 → 수정판)

형식: **원안 약점** → **ChatGPT가 바꾸라고 한 것 1개** → **뽑을 숫자** → **6일 축소판** → **기억할 한 문장**

### 4-1. 추진 후보 (TOP 8)

#### I-03 MCP Zero-Trust Supply-Chain Auditor ⭐ ChatGPT 1위
- **원안 약점**: "포이즈닝 탐지"와 "런타임 능력 감사"를 섞음. MCPTox 라벨은 전자의 정답이지 "이 서버가 /etc/passwd를 읽어야 하는가"의 정답이 아님. **45개 실제 서버를 다 돌리려다 dependency 디버깅 프로젝트가 됨**.
- **바꿀 것**: MCPTox 1,348개는 **정적 벤치마크로 전량**, 동적 OpenShell 감사는 **재현 가능한 MCP 5~10개**(+자작 악성 fixture 2~3개)로 분리.
- **뽑을 숫자**: (A) MCPTox: poisoning detection P/R/F1, **Recall@1% FPR**, ASR, benign utility. (B) 동적: undeclared resource access 탐지, egress 차단율, 정책 생성 후 benign tool 성공률, 서버당 감사 시간.
- **6일 축소판**: 위 그대로. 스택: OpenShell(코어) · NemoClaw(MCP 클라이언트) · Nemotron · nvidia-nat MCP · skill-card-generator · (Guardrails는 역할 명확할 때만).
- **한 문장**: "MCP 서버가 무엇을 할 수 있다고 *말하는지*가 아니라, 샌드박스에서 실제로 무엇을 *하는지* 보고 신뢰 여부를 결정합니다."

#### I-13 Skill CI/Compiler ⭐ ChatGPT 2위 (허황형에서 승격)
- **원안 약점**: "자기진화"는 과장 냄새. **held-out을 반복 개선에 재사용하면 더 이상 held-out이 아님**(test contamination). "승격 스킬 수"는 무의미한 지표.
- **바꿀 것**: "실패로부터 후보 Skill을 합성하고 **unseen evaluation을 통과한 것만 배포**하는 Skill CI/Compiler"로 정의. **Train(스킬 생성) / Dev(승격 판단) / Frozen Test(마지막 1회)** 분리. baseline에 **사람이 쓴 static custom skill** 추가 (no skill → NVIDIA 공식 → manual → evolved).
- **뽑을 숫자**: frozen test success uplift(예: static 62% → promoted 79%, 한 번만 명확히), promotion precision(승격 스킬 중 frozen에서 실제 도움된 비율), regression rate, tokens/successful task.
- **6일 축소판**: coding agent 1종 + task family 4개(dependency inspection / test diagnosis / config editing / log analysis), 후보 SKILL.md 3~5개.
- **주의** `[VERIFIED]`(9-1 #5): 자작 스킬을 "NVIDIA Verified"처럼 표현 금지. skill-card-generator는 초안 생성만 하고 서명·승인하지 않음("Do NOT use for: Signing, publishing, or approving"). 공식 trust pipeline 산출물(skill card · `skill.oms.sig` · `BENCHMARK.md` · `evals/`)을 **우리 promotion gate의 산출물 형식으로 그대로 차용**하면 4a(NVIDIA 자산 확장) 어필.
- **한 문장**: "우리 에이전트는 실패를 기억하는 게 아니라 스킬로 컴파일하고, 처음 보는 문제에서도 효과가 있을 때만 그 스킬을 살아남깁니다."

#### I-11 Agent CI — Real Side-Effect Replay Gate ⭐ ChatGPT 3위 (중간형에서 승격)
- **원안 약점**: "테스트 없음" baseline은 허수아비. **툴콜 시퀀스가 달라졌다고 회귀가 아님**(search→retrieve vs retrieve→search) → raw diff를 게이트로 쓰면 오탐 폭발. mock replay면 OpenShell은 장식.
- **바꿀 것**: **mutation testing** — tool description 의미 변경 / required arg 삭제 / tool rename / prompt 충돌 / model swap / permission 축소 등 20~30개 mutation에 "어떤 회귀가 발생해야 하는지" 라벨. **실제 툴/MCP를 OpenShell ephemeral sandbox + fixture API + 파일시스템 스냅샷에서 재실행** (production side effect 0).
- **뽑을 숫자**: mutation 탐지 recall / precision, **equivalent-change false-positive율**, task success delta, cost/PR, p95 CI runtime, tau2 pass^k.
- **6일 축소판**: 파일 수정 agent 1종, mutation 30개. UI 불필요 — GitHub Actions 출력 `Agent Regression Gate: FAIL / Task success 97%→71% / Tool-call drift 4/30 / New side effects 2 / Cost/task +38%`가 곧 데모.
- **한 문장**: "에이전트 코드는 통과했는데 행동이 깨지는 배포를, production에 가기 전에 실제 툴을 다시 실행해서 잡습니다."

#### I-01 Least-Privilege Policy Synthesizer (구 A) — ChatGPT 4위
- **원안 약점**: 차단율만 높이려면 아무것도 못 하게 하면 됨. "정책 작성 시간 20분→30초"는 약한 지표(자동화가 빠른 건 당연). 한 번 실행한 trace로 만든 정책은 최소권한이 아니라 **training trace에 overfit된 allowlist**.
- **바꿀 것**: 범용 생성기 포기 → **하나의 실제 workload**(예: code maintenance agent)에 대해 정상 시나리오 20(train) / 10(held-out) / 공격 30으로 분리해 최소권한을 수치로 증명.
- **뽑을 숫자**: Benign Task Success ≥95% 유지 하에 **Privilege Surface Reduction**(허용 path/domain/binary/action 개수 감소%), 공격 ASR(예: 41%→3%), held-out utility, regression after patch.
- **주의**: Guardrails/NemoGuard를 역할 없이 넣으면 "개수 채우기"로 보임. OpenShell+Nemotron+NAT+Skills만으로 충분.
- **한 문장**: "에이전트가 실제로 사용한 권한만 관찰하고, 공격으로 깨뜨리고, 다시 줄여서 정상 기능은 유지하면서 최소권한 정책을 자동으로 수렴시킵니다."

#### I-10 Agent Inference Governor (구 F) — ChatGPT 5위
- **원안 약점** `[VERIFIED]`(9-1 #3): OpenShell 인퍼런스 설정은 게이트웨이 단위 단일 백엔드 + 변경 전파 ~5초 → **스텝별 핫리로드 라우팅은 기술적으로 부적합**. 라우팅 결정은 애플리케이션 계층에서. Nano에게 "어려운가?"를 먼저 묻는 분류기는 오버헤드가 이득을 먹음.
- **바꿀 것**: `Agent(OpenShell) → inference.local → Secure Routing Gateway → Nano NIM / Ultra API`. 샌드박스 안 에이전트는 provider URL·credential을 모르고 Ultra 직접 호출 불가. 사용자에게는 YAML 하나(`quality_target: 0.95 / monthly_budget_usd / latency_p95_ms / escalation 규칙`)를 주고, **프로파일러가 과거 trace로 라우팅 정책을 자동 생성**.
- **뽑을 숫자**: All-Nano / All-Ultra / Ours / **Oracle**(사후 최적) 4조건. **routing regret**(ours cost − oracle cost @ target accuracy), $/successful task, p50/p95, Ultra escalation rate, quality-cost Pareto.
- **주의**: 셀프호스팅 GPU 비용을 API 달러와 비교할 때 가격·utilization 가정 명시. 예선엔 L40S 없으므로 **API-only 재현 모드** 필수.
- **한 문장**: "Agent에게 월 예산과 품질 SLO를 주면 routing policy를 자동 생성하고, OpenShell이 그 정책을 우회하지 못하게 강제합니다."

#### I-07 Safe Autonomous CVE Triage — ChatGPT 배치2 1위, 종합 6위
- **원안 약점**: GitHub Advisory의 affected version은 "패키지가 취약"이지 "이 repo가 취약 함수를 호출"이 아님 → **reachability recall을 그 골든셋으로 측정 불가**. 2026년 상용 SCA는 이미 함수 수준 reachability 제공 → "SCA는 문자열 매칭뿐"이라 하면 반박당함.
- **바꿀 것**: "SCA 대체" 포기 → **"SCA 결과를 안전한 autonomous triage agent가 처리"**. CVE 20개에 대해 Fixture A(취약 의존성 O + 취약 함수 호출 O) / Fixture B(O + X) **페어 픽스처 직접 제작**. OpenShell 정책은 `github.com 허용`으로 끝내지 말고 method/path까지 좁혀야 exfil 채널 악용 시연이 설득력 있음.
- **뽑을 숫자**: reachable vuln P/R/F1, false positives/repo, actionable CVE 감소율, 주입 exfil ASR, $/CVE, p95.
- **한 문장**: "인터넷의 CVE를 읽고 사내 코드를 읽는 에이전트에게, 둘을 읽을 권한은 주되 둘 사이로 데이터를 빼낼 권한은 주지 않았습니다."

#### I-15 A2A Ephemeral Capability Lease Broker — ChatGPT 7위 (허황형에서 승격)
- **원안 약점** `[VERIFIED]`(9-1 #1): OpenShell 스키마상 filesystem/process는 **정적**(샌드박스 재생성 필요), network_policies/network_middlewares만 런타임 핫리로드 → "파일/네트워크/바이너리 모두 TTL 발급"은 구현 불가. `paths+domains+binaries × time` 단일 숫자는 위험 단위가 달라 무의미. A2A는 discovery/delegation 표준이지 권한 협상 프로토콜이 아님 — `required_capabilities` 계약은 우리가 만든 것임을 명시.
- **바꿀 것**: filesystem/process는 사전 정의 프로파일로 고정, **A2A task별 network/credential lease만 TTL로 발급**.
- **뽑을 숫자**: Σ allowed-domain-seconds↓, Σ credential-scope-seconds↓, benign task success, over-privilege 요청 거절율, **만료 후 재호출 공격: baseline 성공 / ours deny**, 위임 오버헤드 p95.
- **6일 축소판**: parent 1 + subagent 2 + broker 1. 한 task에 도메인 하나를 30초만 허용, 만료 전·후 비교.
- **한 문장**: "서브에이전트에게 서버 권한을 주는 게 아니라, 그 작업에 필요한 한 도메인을 30초 동안 빌려줍니다."

#### I-19 Privacy-Constrained Multi-Agent Allocation — ChatGPT 배치5 1위, 종합 8위
- **원안 약점**: "서울이라서 25개 에이전트"는 gimmick. LLM에게 "협상해봐"는 수렴·재현성 없음.
- **바꿀 것**: **3개 지역**만. 공개 가능 정보(남는 capacity, 인접, marginal cost)와 비공개(개별 수요, 원본 주민 데이터)를 정책으로 분리. **allocation protocol은 deterministic**(구조화된 offer/request 교환), LLM은 제약 해석·설명만. 일반화: 병원·물류·계열사 등 "데이터를 중앙에 못 모으는 조직 간 자원 배분".
- **뽑을 숫자**: Centralized cuOpt(upper bound) / No coordination(lower) / Ours 3조건의 **global optimality gap%**, constraint violations, negotiation rounds, bytes exchanged, **raw cross-domain access = 0**, 1개 지역 장애 시 degradation·recovery.
- **한 문장**: "데이터를 중앙에 모으지 않고도 필요한 숫자만 협상해서 전역 최적해의 N%까지 따라갔습니다." (N은 실측 후에만)

### 4-2. 흡수 (단독 제품 아님, 부품으로 가치)

| ID | 흡수 대상 | ChatGPT 핵심 지적 |
|---|---|---|
| I-02 방어 계층 비교 | I-03/I-01의 ablation | AgentDojo 97 task 전체 이식은 벤치마크 엔지니어링 프로젝트가 됨. 공격 2~3종·subset만 real side-effect adapter로. **"Guardrail은 compromise를 줄이고 OpenShell은 consequence를 줄인다"**를 같은 공격셋에서 숫자로 분리하면 그래프 한 장이 강함 |
| I-04 Agent SOC | I-01 운영 루프 | "로그→LLM→요약"은 흔한 GenAI SI. `deny count > k` baseline은 허수아비. 정책 drift 탐지→자동 패치→benign regression 검증 closed loop로만 가치 |
| I-17 합성 시민 | 공공 서비스 에이전트 평가층 | "600만 명 테스트"·"형평성 증명" 금지 → **behavioral robustness across synthetic strata**. LLM simulator→LLM target→LLM judge 3단 순환 → 정답은 deterministic evaluator로. 장애 속성은 공개 스키마에 없음 `[CHATGPT]` |
| I-18 리스크 점수 | I-14 서브시스템 | "보험료"는 actuarial 데이터 없이 credibility 붕괴. held-out 공격 ASR은 "사고 확률"이 아님. calibration(Brier) 없으면 ranking score일 뿐 |

### 4-3. 본선용 (10/7 L40S·시간 확보 후)

| ID | 왜 예선에 부적합 | 본선 형태 |
|---|---|---|
| I-05 재난 대피 | 직선거리·행정동 centroid로 "27% 감소"는 현실 의미 약함. 실제 **보행 도로망 travel-time matrix**가 필요(OSRM/OSM). 무더위쉼터 capacity 필드 제공 중단 `[CHATGPT]` → 폭염 제외 | 지진 + 1개 자치구 + 도로폐쇄 시나리오. 지표: capacity violation, p95 대피시간, 취약계층 worst-10%, rerouting stability, 10k/100k/1M 수요 solve latency |
| I-08 SOP 감시 | 공식 `deepstream-sop` 블루프린트가 이미 동일 워크플로 제공. fine-tuning은 4×A100 전제 `[CHATGPT]` | 모델 학습 포기 → **"새 SOP를 자연어로 등록하면 검사기·평가셋·OpenShell 영상 접근정책까지 자동 생성"** 커스터마이징 레이어. 지표에 **false alarm/100분** 필수 |
| I-14 Attestation Gate | I-01+02+03 합 → 각 증거가 얕아짐. "면허"는 권위 문제. 단일 점수 합산은 통계적 근거 없음 → profile로 | 본선 로드맵. 서명은 "우리 결과 무변조 서명"이지 "NVIDIA 인증" 아님 |
| I-16 Air-Gap | 예선에 48GB GPU 없으면 핵심 주장 증명 불가. **"GPU가 없다면 정직한 6일 축소판은 없다"** | Nano FP8 + 소형 Retriever + OpenShell. 지표는 "egress 시도 0"이 아니라 **successful external egress bytes = 0** + 온/오프 품질 격차 |
| N-B Federated Immune | NVFLARE 3-site 시뮬레이션은 가능하나 스코프 큼 | 3 가상 기업 × 공격 family 분리 → federated detector 3~5 round → unseen-site F1 uplift |

### 4-4. 폐기

| ID | 탈락 사유 (ChatGPT) |
|---|---|
| I-06 폐기물 배차 | 실제 route baseline 없음("네가 나쁘게 만든 baseline을 이긴 것"). **OpenShell 제거해도 그대로 작동 → G2 FAIL**. 민원 텍스트→VRP 제약 연결도 부자연(민원은 새 pickup task이지 제약이 아님) |
| I-09 의약품 | "SQL JOIN이면 끝나는 걸 왜 Nemotron으로?" 잘 만들수록 deterministic DUR이 코어 → 대회 정합성↓. 약품 identity normalization이 먼저 터짐 |
| I-12 실거래가 | 가격 이상치 ≠ 이상거래 ≠ 자전거래. 합성 라벨 P/R은 generator 규칙을 detector가 되찾는 것. z-score baseline 허수아비. **"이걸 왜 agent로?"에 답 없음** |
| I-20 법령 | "충돌"은 법해석(특별법·신법 우선 등) 필요. 골든셋에 법률 전문가 필요. OpenShell 장식. Change Impact Analyzer로 줄이면 좋아지나 G2 미달 |

### 4-5. ChatGPT가 추가 제안한 3개

#### N-A Runaway Agent Circuit Breaker (현실형) — 추진 후보
- 페인포인트: 공격 없이도 tool error 무한 재시도·plan loop로 API/LLM 비용·부작용·rate-limit 폭발.
- baseline: `max_steps=20` / 전체 timeout 60초 같은 정적 안전장치.
- 방법: NAT 프로파일러에서 LLM 호출 수·반복 tool signature·token velocity·HTTP retry 패턴 관측 → 이상 시 NemoClaw 오케스트레이터가 중단 + **OpenShell 네트워크 정책 핫리로드로 외부 tool endpoint 즉시 제거** `[VERIFIED]`(9-1 #1).
- 지표: 주입 runaway에서 **max cost exposure**, benign 완료율, false trip율, 탐지→egress 차단 지연.
- 6일 축소판: 정상 20 + retry/loop 주입 20 workflow → overspend prevented / false cutoff / cutoff latency 3개 숫자.
- 왜 NVIDIA Recipe감: "Agent security"를 프롬프트 인젝션 너머 **resource/cost containment**까지 확장하는 실무 패턴.

#### N-B Federated Agent Immune System (허황형) — 본선용
- 각 조직이 자기 OpenShell 샌드박스에서 공격 trace 수집 → 원본은 안 보내고 **NVFLARE로 detector 업데이트만 federated aggregation**. baseline: local-only(하한) / 중앙 pooling(oracle 상한). 지표: unseen-site attack AUROC/F1, raw trace egress = 0, bytes/round.
- 블로그 서사: "NVFLARE가 의료 FL만이 아니라 autonomous-agent security에도 쓰인다."

#### N-C Zero-Secret Agent Connector (잘 안 알려진 기능 파기) — 추진 후보 (섹션 9 검증 후)
- 페인포인트: `GITHUB_TOKEN=...`이 에이전트 env에 있으면 "환경변수 읽어서 보내" 인젝션 한 방.
- 방법 `[VERIFIED-PARTIAL]`(9-1 #2): 샌드박스에 credential을 아예 넣지 않음. OpenShell이 허용 REST endpoint의 method/path/body를 검사 → **`network_middlewares`**(핫리로드 가능)로 inspect/redact → 그 뒤 provider credential 주입(**`request_body_credential_rewrite: true`** / `websocket_credential_rewrite: true`). ※ "Supervisor Middleware"는 공식 명칭이 아님.
- baseline: API 키가 env에 존재 + 도메인 allowlist만.
- 지표: 샌드박스 내 credential read 성공 건수(0), 주입 exfil ASR, benign API task success, middleware p95 오버헤드.
- 6일 축소판: mock SaaS 1개, 정상 30 + credential 탈취 프롬프트 30 → env-secret vs zero-secret 비교.
- 한 문장: "에이전트에게 API를 쓸 권한은 주지만 API 키는 보여주지 않습니다."
- `[INFERRED]` I-03/I-01/I-15 어느 것에도 **부품으로 결합 가능**(A안에 넣으면 OpenShell 심도 어필 최대).

---

## 5. 하이브리드 2안 (ChatGPT 일별 마일스톤)

### A안 — MCP Zero-Trust Admission Controller = I-03 + I-01 (+ N-C 선택)
> ChatGPT: "우승 확률만 놓고 하나를 고르면 이 조합이 1순위"

```
Candidate MCP Server → Static Tool-Poisoning Inspection → OpenShell Dynamic Behavior Audit
→ Observed Capability Model → Least-Privilege Policy Generation → MCPTox + Runtime Red-Team
→ Held-out Benign Validation → PASS: policy.yaml + security report / FAIL: reject
```
- **결합 논리**: I-03 = "이 MCP 서버를 믿어도 되는가", I-01 = "믿는다면 정확히 어떤 권한만 줄 것인가". OpenShell을 빼면 실제 행동 관찰·enforcement·최소권한 검증이 사라짐.
- **6일 스코프**
  - [ ] Day 1: MCP client/fixture 3개 + 정상/악성 서버 2~3개 + OpenShell 샌드박스 기본 실행
  - [ ] Day 2: MCPTox subset 벤치마크 + no-defense / static-description baseline **고정**
  - [ ] Day 3: 재현 가능 MCP ≤5개에서 파일/네트워크 실제 행동 audit + declared-vs-observed diff
  - [ ] Day 4: Nemotron 최소권한 YAML 생성 → 정책 적용 후 benign task 재실행
  - [ ] Day 5: poisoning/exfiltration/unauthorized-file 공격 → ASR + 기능 보존율
  - [ ] Day 6: 평가 스크립트 원커맨드, README 재현성, 그래프 3개, PDF 제출 문구
- **반드시 뽑을 숫자 3개**: ① ASR no-defense X% → ours Y% ② Benign Utility(정책 전후 정상 tool task 성공률) ③ Privilege Surface Reduction%. (숫자는 실측 전 절대 미리 쓰지 말 것)
- **실패 시나리오**: 실제 MCP 서버 dependency/인증 문제로 dynamic audit adapter에 3일 이상 소모. → 원칙: **MCPTox 1,348개는 static, dynamic runtime은 5개 이하**.

### B안 — Verified SkillOps = I-13 + I-11
> ChatGPT: "가장 NVIDIA-native한 조합"

```
Agent task failure → Failure trace → Nemotron generates candidate SKILL.md
→ OpenShell sandbox replay → NeMo tool/trajectory evaluation → Frozen task + regression suite
→ improvement? No → reject / Yes → Local Skill Library Promotion
```
- **결합 논리**: I-13만 하면 "LLM이 알아서 스킬을 만들었다", I-11을 붙이면 "Skill이라는 production artifact를 CI로 검증해 승격한다". NVIDIA Skills가 평가셋·benchmark를 skill artifact의 일부로 취급하는 방향과 정합 `[CHATGPT]`.
- **6일 스코프**
  - [ ] Day 1: repository-maintenance agent 1개 + task family 3~4개 + **train/dev/frozen-test split 고정**
  - [ ] Day 2: no-skill / NVIDIA-skill / manual-skill baseline + trace 저장
  - [ ] Day 3: 실패 trace → candidate SKILL.md 생성 파이프라인
  - [ ] Day 4: OpenShell sandbox replay + success/tool-call/trajectory 평가 + promotion gate
  - [ ] Day 5: prompt/tool-description mutation 20~30개 → regression·false-promotion 측정
  - [ ] Day 6: iteration curve, frozen-test uplift, token 그래프, 재현 CLI
- **반드시 뽑을 숫자 3개**: ① Frozen-test success uplift(static skill 대비 %p) ② Promotion precision / regression rate ③ Tokens per successful task 감소율.
- **실패 시나리오**: task family가 충분히 반복적이지 않아 생성 스킬이 다른 문제에 일반화되지 않음. → **벤치마크 설계가 프로젝트의 절반**.

### 팀 구성별 최종 추천 (ChatGPT)

| 팀 | 추천 | 분업 |
|---|---|---|
| 백엔드 2인 | **B안 Verified SkillOps** | 1: agent/skill 생성/OpenShell, 2: 평가/CI/벤치마크/README. UI·외부 API·공공데이터 정제 0 |
| 백엔드+데이터 3인 | **A안 MCP Admission Controller** | Backend A: OpenShell+MCP 런타임, Backend B: 정책 생성+NemoClaw/NAT, Data: MCPTox 전처리·공격 suite·지표 파이프라인 전담 |
| 풀스택 4~5인 | **I-19 수정판** (3지역) | optimization/data, A2A, OpenShell isolation, orchestration, 시각화 병렬. 최종 화면 = Central / Isolated / Private 3개 비교 |

`[INFERRED]` 사용자 프로필(Spring 백엔드 학습자)과 v2 "백엔드·인프라 중심 → A" 권장을 합치면, 팀이 2인이면 B안, 3인 이상이면 A안이 자연스럽다.

---

## 6. ChatGPT가 지적한 공통 실수 3개 (우리 팀 버릇)

### 실수 1 — NVIDIA 기술의 '개수'를 '필연성'으로 착각
심사위원 질문은 하나: **"OpenShell을 지우면 이 프로젝트가 여전히 작동합니까?"** I-06, I-09, I-12, I-20은 그대로 작동한다. → 앞으로 모든 NVIDIA 컴포넌트에 **"이걸 삭제하면 어떤 핵심 metric이 나빠지는가?"**를 적용. 답이 없으면 제거. 구조적으로 연결된 3개 > 억지로 넣은 6개.

### 실수 2 — "숫자를 만들 수 있다"와 "그 숫자가 증거다"를 혼동
규범에 한 줄 추가: **"외부인이 믿을 수 없는 숫자는 숫자가 없는 것과 같다."** 반복 사례: I-12(합성 fraud→합성 detector), I-06(합성 route), I-01(자기 공격→자기 방어), I-17(LLM→LLM→LLM), I-13(held-out 재사용).

**숫자 4등급** (SCORING_GOLDEN_RULE 3a 보강 제안):
| 등급 | 정의 | 예 |
|---|---|---|
| **A** | 외부 벤치마크 / 실제 라벨 | MCPTox, AgentDojo, BFCL |
| **B** | frozen held-out / oracle optimum | I-13 frozen test, I-19 중앙 최적해, I-10 Oracle router |
| **C** | 독립 제작 deterministic fixture | I-07 reachable/unreachable 페어, I-11 mutation 라벨 |
| **D** | 우리가 생성하고 우리가 채점한 synthetic | I-12, I-06 |
→ headline metric은 **A/B 중 하나 이상 필수**. D만 있는 아이디어는 자동 감점.

### 실수 3 — 핵심 실험보다 제품 서사를 먼저 키움
"면허시험소", "보험 언더라이터", "600만 시민", "25개 자치구 swarm", "AI 입법 보좌관", "자기진화"… 기억되는 건 시스템 크기가 아니라 **반박하기 어려운 그래프 한 장**. 순서를 뒤집어라: ① 증명할 한 문장 가설 → ② 그것을 증명할 그래프 하나 → ③ 그 그래프를 만들 최소 시스템 → ④ 마지막에 제품 이름.

| 아이디어 | 그 그래프 |
|---|---|
| I-03 | Attack ASR vs Benign Utility |
| I-13 | Iteration vs Frozen Test Success |
| I-10 | Quality vs Cost Pareto (+Oracle) |
| I-19 | Privacy vs Global Optimality Gap |
| I-02 | Intent Compromise vs Side-effect Completion (2×2) |

---

## 7. ChatGPT의 "산업가치: 보안 vs 공공/제조" 판단

질문: "보안 계열이 산업가치 축에서 공공/제조보다 불리한가?" → **아니다, 오히려 약간 유리.**

| 축 | 보안·AgentOps (I-01/03/07/11/13) | 공공·제조 (I-05/06/08) |
|---|---|---|
| 문제 실재성 | 높음 | 높음 |
| Agentic AI와 직접 연결 | 매우 높음 | 중~높음 |
| OpenShell 필연성 | 매우 높음 | I-07 제외 약함 |
| 공개 벤치마크 | 강함 | 약함 |
| 6일 내 골든셋 | 상대적으로 쉬움 | 어려움 |
| 시각적 데모 / 일반인 이해도 | 보통 | 강함 |
| 산업 숫자 방어 | 강함 | 데이터에 따라 약함 |
| "샘플 실행" 위험 | 낮음 | I-08 높음 |

핵심 논리: **"기업이 Agent를 production에 못 올리는 이유를 해결한다"는 것 자체가 산업 문제**이고, 교육 미션이 *Securing Agents*이므로 보안은 주변부가 아니라 **주제의 정중앙**. "산업가치"와 "산업처럼 보이는 도메인"은 다르다.

---

## 8. 이번에 새로 검증한 데이터·벤치마크 `[VERIFIED]`

| 소스 | 확인 내용 | URL |
|---|---|---|
| **AgentDojo** | MIT 라이선스. 97 user task + 629 security case. 공식 3지표 Benign Utility / Utility Under Attack / Targeted ASR. 논문 수치 GPT-4o targeted ASR 47.69%. `pip install agentdojo`, `python -m agentdojo.scripts.benchmark` | https://github.com/ethz-spylab/agentdojo · https://arxiv.org/abs/2406.13352 |
| **MCPTox** | AAAI 2026. 실제 MCP 서버 45개·툴 353개 기반 1,348개 툴 포이즈닝 케이스, 10~11개 리스크 카테고리. 20개 LLM 에이전트 최고 거부율 <3%. 데이터 GitHub 공개 (라이선스는 리포에서 직접 확인 필요) | https://github.com/zhiqiangwang4/MCPTox-Benchmark · https://arxiv.org/abs/2508.14925 |
| **NVD CVE API 2.0** | 공개. 키 없이 30초당 5회, 키 발급 시 50회. 키는 이메일 신청 후 단일 링크 활성화(7일 내). 총 395,669건(2026-09-21). 표기 의무: "This product uses data from the NVD API but is not endorsed or certified by the NVD." | https://nvd.nist.gov/developers/start-here · `https://services.nvd.nist.gov/rest/json/cves/2.0` |
| **서울시 지진옥외대피소** | OA-21063. 공공누리 1유형(상업·변경 가능). 매일 1회 갱신. 필드: 수용시설명·상세주소·시설면적·경도·위도·행정동코드. 연관: 이재민임시주거시설, 무더위쉼터, 한파쉼터 | https://data.seoul.go.kr/dataList/OA-21063/S/1/datasetView.do |
| **행안부 지진옥외대피소** (전국) | data.go.kr 개발 자동승인 / 운영 심의. 이용허락 제한 없음 | https://www.data.go.kr/data/15153506/openapi.do |
| **국가법령정보 OPEN API** | 191건. **"담당자 확인 후 승인, 신청 후 1~2일 이내 처리"** (공식 이용안내). 기존 문서의 "[UNVERIFIED] 승인 기간" → 해소 | https://open.law.go.kr/LSO/information/guide.do |

---

## 9. ⚠️ 사실로 승격 금지 — ChatGPT 주장 중 미검증 `[CHATGPT]`

ChatGPT는 웹 검색을 병행했으나 나는 아래 항목을 공식 문서로 재확인하지 못했다(또는 확인 중). **제출서·아키텍처 결정에 쓰기 전에 반드시 확인.**

| # | 주장 | 영향받는 아이디어 | 검증 상태 |
|---|---|---|---|
| 1 | OpenShell **network 정책은 실행 중 핫리로드 가능**, filesystem/process는 샌드박스 생성 시 고정 | I-15, N-A, I-04 | ✅ **VERIFIED** (9-1) |
| 2 | OpenShell **Supervisor Middleware**(credential 주입 전 egress inspect/deny/replace) + **request_body_credential_rewrite** 존재 | N-C | 🟡 **PARTIALLY** — 기능은 있으나 공식 명칭은 `network_middlewares` (9-1) |
| 3 | OpenShell 인퍼런스: 게이트웨이당 **단일 active backend**, 변경 전파 **~5초** → per-request 라우팅 부적합 | I-10 | ✅ **VERIFIED** (9-1) |
| 4 | `nvidia-nat[a2a]` 패키지: A2A client/server, Agent Card discovery, delegation, OAuth2/JWT scope 지원 | I-15, I-19 | ✅ **VERIFIED** (9-1) |
| 5 | NVIDIA Skills 검증 체계에 skill card·**서명**·평가셋·benchmark report 포함. skill-card-generator는 초안만, 서명/승인 안 함 | I-13, I-14 | ✅ **VERIFIED** (9-1) |
| 6 | Nemotron-Personas-Korea HF 카드 = **1,000,000 records**(레코드당 복수 persona variant), NVIDIA 컬렉션은 7M personas 표기 | I-17 | ✅ **VERIFIED** (1M rows, cc-by-4.0; 7M은 variant 합산으로 추정) (9-1) |
| 7 | 서울시 무더위쉼터 데이터: **2026-08-10 이후 시설면적·이용가능인원 필드 제공 중단** | I-05 | 미검증 |
| 8 | Nemotron 3 Nano 30B-A3B NIM: FP8 프로파일 단일 L40S 지원, 모델 파일 ~30.46GB. Retriever 300M 임베딩 최소 2.4GiB | I-16 | 미검증 |
| 9 | NeMo Evaluator가 tool-call/trajectory 단위 평가 + Experiments(harness·tool·routing 변화별 cost/latency 비교) 지원 | I-11, I-13 | 미검증 |
| 10 | NVIDIA SOP 학습 블루프린트 full fine-tuning 예시가 4×A100 80GB 전제 | I-08 | 미검증 |
| 11 | 2026년 상용 SCA(예: Endor Labs)가 함수 수준 call-path reachability 제공 | I-07 포지셔닝 | 미검증 (블로그성) |
| 12 | 국가법령정보 API "신청 시 자동승인·바로 활용" | I-20 | **정정됨** → 공식 페이지는 "담당자 확인 후 1~2일" `[VERIFIED]` |

> ChatGPT 점수 자체(94/92/91…)도 ChatGPT의 주관이다. 우리 규범으로 재채점하지 않았다.

### 9-1. 공식 문서 재검증 결과 `[VERIFIED]` (2026-09-23 00:05 KST, NVIDIA 공식 문서만 사용)

| # | 판정 | 출처 | 근거 |
|---|---|---|---|
| 1 | **VERIFIED** | https://docs.nvidia.com/openshell/sandboxes/policies | "A policy has static sections `filesystem_policy`, `landlock`, and `process` that are locked at sandbox creation, and dynamic `network_policies` and `network_middlewares` sections that are hot-reloadable on a running sandbox." → **I-15(네트워크 TTL 리스)·N-A(egress 즉시 차단) 설계 전제 성립.** `03-openshell-policy-yaml-구조.md` §4 표에 "network_policies / network_middlewares = 런타임 핫리로드" 추가 필요 |
| 2 | **PARTIALLY** | 동일 페이지 | 정책에 `network_middlewares` 섹션(핫리로드)과 `request_body_credential_rewrite: true` / `websocket_credential_rewrite: true` 옵션이 존재. 단 **"Supervisor Middleware"라는 고유 명칭은 없음** — supervisor는 집행 컴포넌트 명칭. → N-C는 성립하되 제출서엔 공식 용어 `network_middlewares` + `request_body_credential_rewrite`로 기재 |
| 3 | **VERIFIED** | https://docs.nvidia.com/openshell/sandboxes/inference-routing | "One provider and one model define sandbox inference for the active gateway. Every sandbox on that gateway sees the same `inference.local` backend." / "Changes propagate within about 5 seconds by default." → **I-10은 반드시 애플리케이션 계층 Secure Routing Gateway 구조** |
| 4 | **VERIFIED** | https://docs.nvidia.com/nemo/agent-toolkit/latest/build-workflows/a2a-client.html | `uv pip install "nvidia-nat[a2a]"`, Agent Card로 skill discovery, OAuth2-protected A2A agent 인증 지원 → **I-15·I-19의 A2A 구현 가능성 확인** |
| 5 | **VERIFIED** | https://docs.nvidia.com/skills/agent-skill-trust-pipeline · https://github.com/NVIDIA/skills/blob/main/skills/skill-card-generator/SKILL.md | Trust pipeline 산출물: skill card, `skill.oms.sig`, `BENCHMARK.md`, `evals/` 데이터셋. skill-card-generator SKILL.md: "Do NOT use for: Signing, publishing, or approving a skill card." → **I-13 "Skill = 평가받는 배포 artifact" 서사가 NVIDIA 공식 방향과 정합.** 자작 스킬에 NVIDIA 서명 주장 금지 |
| 6 | **VERIFIED** | https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea | HF 메타데이터 `num_examples: 1000000`, `license: cc-by-4.0`. 레코드당 persona variant 7종(professional/sports/arts/travel/culinary/family/main) → "7M"은 variant 합산으로 추정. **제출서 표기: "1M records × 7 persona variants, CC-BY-4.0"** (기존 문서의 "600만 건" 표현 정정) |

---

## 10. 기존 문서 정정·보강 — **반영 완료 (2026-09-23 00:25 KST)**

아래 8건을 사용자 승인 후 기존 파일에 직접 반영했다. 각 파일 frontmatter에 `revised_at` 또는 버전 증가(2.0→2.1, 1.0→1.1)를 기록했고, 본문 변경부는 "v2.1" / "v1.1" / "(v3 정정)" 표시로 추적 가능하다. 원문을 지우지 않고 ~~취소선~~ + 정정문을 나란히 두었다.

| 파일 | 위치 | 수정 전 | 수정 후 |
|---|---|---|---|
| `NVIDIA-FastCampus...md` | §9-1, `DATA_AND_SKILL_INVENTORY.md` PART 5-3 | `[UNVERIFIED]` 국가법령정보 승인 소요 기간 | `[VERIFIED]` 담당자 승인, 1~2일 (https://open.law.go.kr/LSO/information/guide.do) |
| `IDEA_CANDIDATES.md` | 순위 요약 | B 82점 2위, C 79점 3위 | B는 G2 FAIL 재판정 권고(OpenShell 장식 + 실제 baseline 부재), C는 본선용으로 강등 권고 |
| `SCORING_GOLDEN_RULE.md` | 3a | baseline 대비 개선률 | **숫자 4등급(A/B/C/D)** 추가, headline은 A/B 필수 (섹션 6 실수 2) |
| `SCORING_GOLDEN_RULE.md` | §7 냄새 목록 | — | 🔴 추가: "OpenShell을 지워도 그대로 작동한다" / "우리가 생성한 데이터를 우리가 채점한다" / "제품 이름이 실험보다 먼저 나왔다" |
| `DATA_AND_SKILL_INVENTORY.md` | 3-2 벤치마크 표 | BFCL/τ²/SWE/WebArena/GAIA | **AgentDojo(MIT), MCPTox(공개)** 추가. 3-1에 서울시 지진옥외대피소 OA-21063, NVD API 추가 |
| `03-openshell-policy-yaml-구조.md` | §1 스키마 / §4 | `network_policies`만 기술 | **`network_middlewares` 섹션 + `request_body_credential_rewrite` / `websocket_credential_rewrite` 옵션 추가.** "정적(filesystem/landlock/process, 생성 시 고정) vs 동적(network_policies/network_middlewares, 핫리로드)" 표 추가 (https://docs.nvidia.com/openshell/sandboxes/policies) |
| `NVIDIA-FastCampus...md` | §8-2 보호 계층 | "Filesystem·Process 고정, Inference 핫리로드" | **Network 정책도 핫리로드** 추가. 인퍼런스는 게이트웨이당 단일 backend·전파 ~5초 (https://docs.nvidia.com/openshell/sandboxes/inference-routing) |
| `DATA_AND_SKILL_INVENTORY.md` | 3-1 #8 | "약 600만 건" | "1M records × 7 persona variants, CC-BY-4.0" |

---

## 11. 다음 행동 (D-6 → D-5)

```
[x] 섹션 9 #1~#6 공식 문서 재검증 완료 (본 문서 9-1) — 5 VERIFIED / 1 PARTIALLY(용어)
[ ] 팀 인원 확정 → 2인이면 B안, 3인 이상이면 A안을 기본값으로
[ ] 반나절 feasibility spike:
    [ ] A안: MCPTox 리포 clone → 케이스 포맷 파싱 → 로컬 MCP fixture 1개를 OpenShell 샌드박스에서 실행
    [ ] B안: coding agent 1종으로 task family 1개 만들고 실패 trace → SKILL.md 후보 1개 생성까지
[ ] spike 결과로 하나 고정. 이후 새 아이디어 추가 금지 (ChatGPT: "가장 큰 경쟁자는 scope creep")
[ ] baseline 문장 팀 채널 고정: "우리 baseline은 ____, headline 지표는 ____ (등급 A/B)"
[ ] 평가 스크립트 골격 먼저 (규범 §6 역순 개발)
[ ] build.nvidia.com API 키 발급 (기존 액션, 여전히 최우선)
[ ] N-C Zero-Secret Connector(`network_middlewares` + `request_body_credential_rewrite`)를 A안 Day 4~5에 부품으로 편입 검토 — 검증 완료로 편입 가능
[ ] 미검증 잔여: 섹션 9 #7(무더위쉼터 필드 중단) #8(Nano FP8 L40S) #9(NeMo Evaluator trajectory) #10(SOP 4×A100) — 해당 아이디어(I-05/I-16/I-11·I-13/I-08) 착수 시 확인
```

---

## 12. 한계 `[UNVERIFIED]`

1. ChatGPT 1개 모델의 단일 세션 의견이다. 다른 리뷰어(Claude/Gemini/사람)와 교차하지 않았다.
2. ChatGPT가 인용한 NVIDIA 문서 주장은 섹션 9에 정리했고 재검증 전까지 `[CHATGPT]`다.
3. 점수는 아이디어 단계 예측치다. 구현 결과가 아니다.
4. 23개 아이디어의 "뽑을 숫자"는 설계상 가능하다는 주장이며 실측값이 아니다. 예시 숫자(ASR 48%→4% 등)는 **ChatGPT가 든 예시일 뿐 실측 아님** — 제출서에 절대 쓰지 말 것.
5. 본선(10/7) 미션은 당일 공개되므로 이 문서는 **예선 전용**이다.
