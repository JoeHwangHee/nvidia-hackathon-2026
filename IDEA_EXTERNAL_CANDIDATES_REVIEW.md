---
title: "외부 아이디어 3종 냉정 검토 — SourcingCritic / OrderSentry / ClaimGate"
doc_type: idea_review
version: 1.0
created_at: 2026-09-23T10:30+09:00
event: NVIDIA Korea Agentic AI Hackathon 2026
deadline: 2026-09-28T23:59+09:00
days_left_at_review: 5
scope: 예선 아이디어 선정 (SCORING_GOLDEN_RULE §2 하드게이트 → §3 채점 → §4 밴드)
rubric_applied:
  - SCORING_GOLDEN_RULE.md v2.0 본문 + v2.1 추가 규칙("숫자 4등급 A/B/C/D", D등급만 있으면 3a 상한 1)
  - IDEA_EXPANSION_CHATGPT_REVIEW.md의 3대 반복 실수 (NVIDIA 개수≠필연성 / 우리가 만들고 우리가 채점 / 서사 먼저)
companion_docs:
  - SCORING_GOLDEN_RULE.md
  - IDEA_EXPANSION_CHATGPT_REVIEW.md
  - NVIDIA-FastCampus-Korea-Agentic-AI-Hackathon-2026.md
research_method: 공개 웹·공식 문서·공개 보고서만. 로그인/개인 탭/게시/계정 변경 없음.
tags: "[사실]=출처 페이지에서 직접 확인 / [2차]=조사 서브에이전트 확인, 본 세션 미재검증 / [추론] / [미확인]"
---

# 외부 아이디어 3종 냉정 검토

> **READ THIS FIRST (for agents)**
> - 이 문서는 **버리기 위한 검토**다. 세 아이디어 모두 "만들 수는 있다". 질문은 "이 대회에서 이길 이유가 있는가"다.
> - 판정 순서: §2 하드게이트(G1~G6) → 게이트 통과분만 §3 19개 지표 채점 → CAP → 100점 환산. 게이트 탈락 아이디어의 점수는 **참고용**으로만 표기했다(규범상 채점 무효).
> - 100점 점수는 `[DESIGN]` 가중치(35/25/30/10)에 따른 **팀 내부 우선순위 점수**다. 심사위원 점수가 아니다.
> - 모든 외부 수치에는 inline URL을 달았다. `[2차]` 태그는 조사 서브에이전트가 읽은 출처로, 본 세션에서 재열람하지 않았다 → 제출서에 인용하기 전 1회 직접 확인할 것.
> - 결론 한 줄: **ClaimGate(조건부 예선 후보) > OrderSentry(부품으로 흡수) > SourcingCritic(폐기).** 세 개 모두 기존 TOP(I-03/I-13/I-11/I-01)을 넘지 못한다.

---

## 0. TL;DR

| 순위 | 아이디어 | 게이트 | 참고 점수(100) | 밴드 | 결론 |
|---|---|---|---|---|---|
| 1 | **ClaimGate** | G1~G6 PASS (G2·G6 조건부) | **65** (상한 73) | 경쟁권 | **조건부 예선 후보 / 본선용.** OpenShell 미들웨어(출고 게이트) 구조로 재설계 + FDA OPDP 실제 라벨셋 확보 시에만 |
| 2 | **OrderSentry** | G1 조건부, G2 조건부 | **50** | 약함 | **부품으로 흡수.** Hybrid A / N-C의 "비즈니스 액션 게이트" 데모 시나리오로만 가치 있음 |
| 3 | **SourcingCritic** | **G1 FAIL, G2 FAIL** | (참고) 33 | 폐기 | **폐기.** 정답 라벨이 국가 대외비, LLM이 LLM을 채점, OpenShell은 장식 |

가장 큰 공통 결함: 세 아이디어 모두 원안 그대로는 **"OpenShell을 지우면 그대로 작동한다"**(ChatGPT 리뷰 실수 1). ClaimGate와 OrderSentry는 "LLM 판단"을 코어에서 빼고 **OpenShell 이그레스 경계에서의 강제(enforcement)** 를 코어로 옮겨야만 G2를 통과한다.

---

## 1. 공통 판단 근거 — OpenShell에서 "코어"가 성립하는 지점 `[사실]`

세 아이디어의 G2 판정에 공통으로 쓰이므로 먼저 고정한다. 모두 NVIDIA 공식 문서에서 직접 확인했다.

| 기능 | 내용 | 출처 |
|---|---|---|
| L7 REST 규칙 | `protocol: rest` 엔드포인트에 method/path allow·deny 규칙. 미매칭 연결은 거부(default-deny). `enforcement: enforce/audit` | https://docs.nvidia.com/openshell/sandboxes/policies |
| MCP 툴 규칙 | `protocol: mcp`로 `tools/call`의 tool 이름 단위 allow/deny. 인자 매칭은 미지원 | 동상 |
| GraphQL 뮤테이션 차단 예시 | NVIDIA 문서 자체가 Shopify Admin에 대해 "deny high-impact **inventory/order**/customer roots unless approved"를 권장 정책으로 제시 | 동상 |
| Policy Advisor | 샌드박스 안 에이전트가 `policy.local`로 규칙 제안 → 사람이 밖에서 approve/reject → 승인 시 hot reload. `CONFIG:PROPOSED/APPROVED/REJECTED` 감사 이벤트 | https://docs.nvidia.com/openshell/sandboxes/policy-advisor |
| Supervisor Middleware | 허용된 HTTP 요청 본문을 **자격증명 주입 전**에 inspect/deny/replace. 운영자 자체 gRPC 서비스 등록 가능(`HttpRequest/pre_credentials`), 기본 `fail_closed`, 타임아웃 기본 500ms·최대 30s, 본문 ≤4MiB, 결과는 OCSF 로그 | https://docs.nvidia.com/openshell/extensibility/supervisor-middleware |
| 자격증명 분리 | 샌드박스에 실제 API 키를 두지 않고 OpenShell이 주입. `request_body_credential_rewrite`는 REST 본문 내 플레이스홀더 치환 | https://docs.nvidia.com/openshell/sandboxes/policies |
| 정책 계층 | filesystem/process는 생성 시 고정, network/inference는 hot-reload | https://docs.nvidia.com/openshell/latest/ |

**판정 규칙(이 문서용)**: 아이디어의 헤드라인 지표가 위 기능 중 하나에 *구조적으로* 의존해야 G2 PASS. "에이전트를 샌드박스에서 돌렸다"는 보안 위생이지 코어가 아니다(ChatGPT가 I-09에 내린 판정과 동일).

**리스크 `[사실]`**: 운영자 미들웨어는 gRPC 서비스 구현 + 게이트웨이 TOML 등록 + 재시작이 필요하고, `openshell/regex` 내장 미들웨어는 커스텀 표현식을 아직 지원하지 않는다(https://docs.nvidia.com/openshell/extensibility/supervisor-middleware). 프로토 정의는 리포 `proto/`에 있고 Python 바인딩 재생성을 전제한다(https://github.com/NVIDIA/OpenShell/tree/main/proto). **6일 안에 미들웨어 경로가 막히면 L7 deny + "자격증명 없는 샌드박스 + 검수 서비스가 대신 발행" 구조로 후퇴**해야 한다. 후퇴 경로도 G2를 통과한다.

---

## 2. 아이디어별 검토

### 2.1 SourcingCritic — 수입 공급망 취약 품목의 "심층조사 가치" 판정 에이전트

#### (a) 페인포인트 실재성과 공개 근거
- `[사실]` 정부는 2024-06-27 공급망안정화법 시행과 함께 경제안보품목을 200여 개 → **300여 개**로 확대하고 최대 **5조 원** 공급망안정화기금을 가동. 1년마다 전 품목 재검토, 3단계 등급제. https://www.korea.kr/news/policyNewsView.do?newsId=148930850 · https://www.kita.net/board/totalTradeNews/totalTradeNewsDetail.do?no=84662
- `[사실]` **"구체적인 품목은 공개되지 않았다. 국가 안보 차원에서 '대외비'"** (KITA 게재 기사 원문). 요소·리튬·흑연 포함은 *추정*으로만 보도. https://www.kita.net/board/totalTradeNews/totalTradeNewsDetail.do?no=84662
- `[2차]` 산업부 "공급망 3050 전략"(2023-12): 185개 공급망 안정품목, 특정국 의존도 70%(2022) → 50%(2030) 목표. https://www.motir.go.kr/kor/article/ATCL3f49a5a8c/168317/view
- `[2차]` 글로벌 정의: EU CRMA(Reg. 2024/1252)는 Supply Risk × Economic Importance 2축, HHI 기반 집중도. https://single-market-economy.ec.europa.eu/sectors/raw-materials/areas-specific-interest/critical-raw-materials/critical-raw-materials-act_en · 공개 대시보드 https://rmis.jrc.ec.europa.eu/eu-critical-raw-materials · 미국 EO 14017 https://www.cisa.gov/executive-order-14017-securing-americas-supply-chains
- **실제 사용자·업무 흐름** `[추론]`: 산업부 공급망분석센터·공급망안정화위원회(정부), KOTRA 공급망 컨설팅(https://www.kotra.or.kr/subList/20000020753), 대기업 구매·SCM팀. 흐름은 (무역통계 집계 → HHI/의존도 산출 → 전문가 정성 평가 → 품목 지정 → 대체처 조사). **"심층조사를 할지 말지"를 결정하는 주체가 정부 위원회이고 그 결과가 대외비**라는 점이 이 아이디어의 구조적 문제다. 구매자를 특정할 수 없다.

#### (b) end-to-end 시나리오
구매 전략 담당자가 HS 6단위 품목 리스트를 넣는다 → 에이전트가 관세청/Comtrade에서 5년치 수입액·국가별 점유율을 받아 HHI·특정국 의존도·대체국 수를 계산 → 후보 품목마다 "조사 찬성 에이전트 vs 반박 에이전트"가 근거를 교환 → 판정("조사 가치 있음/없음/보류")과 근거 리포트 출력 → 담당자가 조사 대상을 확정.
→ 이 흐름에서 **LLM이 필요한 유일한 구간은 "찬반 토론"** 이고, 그 결과를 채점할 사람·데이터가 없다.

#### (c) 데이터 소스와 6일 내 즉시 사용 가능성
| 소스 | 승인 | 라이선스 | 개인/민감정보 | 비고 |
|---|---|---|---|---|
| 관세청 품목별 국가별 수출입실적 API `[사실]` | 개발단계 **자동승인**, 10,000/일 | 이용허락 제한 없음 | 없음 | HS 2/4/6/10단위, 월 갱신 https://www.data.go.kr/data/15100475/openapi.do |
| 관세청 국가별 수출입 API `[2차]` | 자동승인 | 제한 없음 | 없음 | https://www.data.go.kr/data/15101612/openapi.do |
| 관세청 수출입무역통계 포털 `[2차]` | 불필요 | 공개 | 없음 | https://tradedata.go.kr/cts/index.do |
| UN Comtrade `[사실: 포털 존재]` | 개발자 포털 가입·키 필요 | 무료 프리뷰 티어 | 없음 | https://comtradedeveloper.un.org/ (레이트리밋 수치는 `[미확인]`) |
| EU RMIS CRM 점수 `[2차]` | 불필요 | 공개 | 없음 | https://rmis.jrc.ec.europa.eu/eu-critical-raw-materials |
| 경제안보품목 300개 목록 | — | **비공개(대외비)** | — | 라벨로 사용 불가 `[사실]` |

데이터 접근성은 세 아이디어 중 가장 좋다. 문제는 데이터가 아니라 **정답**이다.

#### (d) baseline과 headline metric
- 후보 baseline: (1) HHI>임계값 단순 규칙 (2) EU CRM 리스트와의 일치율 (3) 사후 라벨 — 2023~24 중국 수출통제 품목(갈륨·게르마늄·흑연·안티몬 등)을 "2022년 데이터만 보고 맞혔는가".
- 판정: (1)은 결정론적이라 "왜 LLM이냐"에 답이 없다. (2)는 한국 맥락이 아니고 EU 점수 자체가 HHI 기반이라 순환 논리. (3)은 양성 사례가 한 자릿수라 통계적으로 무의미하고 발표 일자·품목 매핑을 팀이 정해야 한다(C등급 이하).
- KPI "불필요한 심층조사 감소·판단 시간 감소"는 **실제 조사 담당자가 없으면 측정 불가** → 팀이 시나리오를 만들고 LLM-judge로 채점 = **D등급**. v2.1 규칙에 따라 3a 상한 1, 사실상 CAP-1 근접.
- **G1 FAIL.** "baseline이 무엇인지 한 문장"이 지금 성립하지 않는다.

#### (e) NVIDIA/NemoClaw/OpenShell이 코어가 되려면
- 원안: 공개 API를 읽는 리서치 에이전트. OpenShell은 "이그레스를 관세청·Comtrade로만 제한"하는 보안 위생 → **장식**. G2 FAIL.
- 살릴 유일한 구조: "외부 웹까지 크롤링하는 딥리서치 에이전트가 **기업 내부 BOM/구매단가(민감)** 를 읽으면서도 외부로 유출하지 못하게 OpenShell이 강제"하는 프레임. 그러나 이 순간 아이디어는 I-07(Safe CVE Triage)·N-C(Zero-Secret)의 도메인 스킨이 되고, 공급망 특유의 가치는 사라진다.

#### (f) 대체재와 차별화
`[2차]` Resilinc(https://resilinc.ai/), Everstream, Interos, Prewave, Sayari 등 글로벌 공급망 리스크 플랫폼이 이미 점수화·모니터링 제공. 국내는 KOTRA 컨설팅(수동), LG CNS SCM(https://www.lgcns.com/kr/service/biz-process-intelligence/scm). "조사하지 말라고 반박하는 critic"은 문헌에서 미발견(`[미확인]`)이지만, 미발견인 이유가 **검증 불가능해서**일 가능성이 높다.

#### (g) 6일 MVP·첫 병목·데모
- MVP: 관세청 API → HHI 대시보드 → 2-에이전트 토론 → 판정 리포트. 3일이면 만든다.
- 첫 병목: HS 코드 ↔ "품목" 개념 매핑(같은 소재가 HS 여러 개에 걸침)과 "조사 가치"의 정의.
- 데모: 지도/차트는 예쁘지만 §7 🔴 "데이터가 있다는 사실이 함정"(ChatGPT I-09/I-12 판정)에 정확히 해당.

#### (h) 게이트·점수
| 게이트 | 판정 | 근거 한 줄 |
|---|---|---|
| G1 | **FAIL** | 정답 라벨(경제안보품목)이 대외비, 대안 라벨은 N<10, KPI는 LLM-judge 자기채점(D등급) |
| G2 | **FAIL** | OpenShell을 제거해도 HHI·토론·리포트 모두 동일하게 동작 |
| G3 | PASS(가능) | Nemotron·NAT·Retriever·OpenShell 나열은 가능하나 필연성 없음 |
| G4 | PASS | 공개 API, 키 없이 캐시 픽스처로 스모크 가능 |
| G5 | PASS | 산업·공공 문제 맞음 |
| G6 | PASS | 3일 완주 |

참고 점수(게이트 무시 시): 축1 1.67 (1a3·1b1·1c1·1d1·1e3·1f1) / 축2 1.5 (2a3·2b1·2c1·2d1) / 축3 1.67 (3a1·3b1·3c3·3d1·3e1·3f3) / 축4 2.0 (4a1·4b3·4c1·4d3) → 총점 1.66 → **33/100 → 폐기**.

---

### 2.2 OrderSentry — "발주하면 안 되는" 예외를 설명·차단하는 발주 에이전트

#### (a) 페인포인트 실재성과 공개 근거
- `[2차]` IHL Group 2025: 글로벌 소매 재고 왜곡(결품+과잉) 비용 **연 $1.77조**(결품 $1.16조, 과잉 $5,720억). 인포그래픽 https://www.board.com/wp-content/uploads/2025/10/Board-Infographic_IHL-Distortion-Study.pdf · 원보고서 페이지는 본 세션에서 403(봇 차단)으로 직접 열람 실패 https://www.ihlservices.com/product/fixing-inventory-distortion-whos-winning-whos-failing-whats-working `[미확인 직접열람]`
- `[사실]` ERP에는 이미 **구조화된 발주 예외 체계**가 있다: SAP MRP Exception Messages/Exception Monitor(https://help.sap.com/docs/SCMCSERM/d85738bd9bad40eaa2aec9680cde13b6/d7940c257a011014a71ac2a8a2918037.html), Oracle Retail SRP의 Overstock alerts/Exceptions `[2차]`(https://docs.oracle.com/cd/B28094_01/aip/pdf/srp/1142/aip-srp-1142-ug.doc). 즉 "예외 감지" 자체는 신규가 아니다. 신규인 부분은 **리콜·시즌종료·프로모션 종료를 외부 피드와 연결해 자동 차단**하는 것뿐이다.
- `[2차·언론]` GS리테일 "AI 편의점 파트너"(2024-07) 자동발주·진열 도입 https://www.mk.co.kr/news/business/11009485 — 리콜 차단 언급 없음.
- **실제 사용자·업무 흐름** `[추론]`: 점포 발주 담당·MD/바이어·SCM. 자동발주 시스템이 제안 → 사람이 승인/수정(이지어드민 문서상 "자동발주/수동 발주서" 병존 https://help.ezadmin.co.kr/index.php?title=%EB%B0%9C%EC%A3%BC `[2차]`). 오발주는 결품(매출 손실)보다 눈에 덜 띄어 관리 사각지대라는 점은 그럴듯하지만, **"오발주율" 산업 통계는 어디에도 없다** `[미확인]`.

#### (b) end-to-end 시나리오
자동발주 배치가 내일자 발주안 3,000라인을 생성 → OrderSentry가 각 라인을 (재고/판매속도) + (식약처 회수·판매중지 피드, 시즌 캘린더, 프로모션 종료일, 공급사 납품중단 공지, 장기체화 플래그)와 대조 → 차단 라인에 사유 카드("SKU 4711: 8/27 식약처 회수 대상, 회수등급 2") 첨부 → 담당자가 승인 → **승인된 라인만 ERP 발주 API로 전송**.
→ 마지막 화살표가 핵심이다. "승인 없이는 발주 API를 호출할 수 없다"를 **앱 코드가 아니라 OpenShell 정책이 보장**해야 이 대회의 아이디어가 된다.

#### (c) 데이터 소스와 6일 내 즉시 사용 가능성
| 소스 | 승인 | 라이선스 | 개인/민감정보 | 비고 |
|---|---|---|---|---|
| 식약처 식품의 회수 및 판매중지 정보 API `[사실]` | 개발단계 **자동승인** | 이용허락 제한 없음 | 없음(업체 전화번호 필드 있음 — 사업자 정보, 개인정보 아님) | 제품명·회수사유·바코드·유통기한·회수등급·품목코드 https://www.data.go.kr/data/15074318/openapi.do |
| openFDA Drug Enforcement(리콜) API `[사실]` | 불필요 | 공개 | 없음 | 2004~현재, 주간 갱신 https://open.fda.gov/apis/drug/enforcement/ |
| Kaggle Favorita `[사실: 페이지 존재]` | 계정 필요, 즉시 | 대회 규칙 `[미확인]` | 없음 | `onpromotion` 필드 있음 https://www.kaggle.com/competitions/favorita-grocery-sales-forecasting/data |
| Kaggle M5 (Walmart) `[2차]` | 즉시 | 대회 규칙 | 없음 | 이벤트/가격 필드 https://www.kaggle.com/competitions/m5-forecasting-accuracy |
| UCI Online Retail II `[2차]` | 즉시 | CC BY 4.0 | 고객ID(익명 정수) | 거래 데이터일 뿐 발주 아님 https://archive.ics.uci.edu/dataset/502/online+retail+ii |
| 실제 발주(PO) 데이터·공급불가 통지·시즌 종료 라벨 | — | — | — | **공개 데이터 없음** `[사실: 조사 범위 내 미발견]` |

결론: **리콜만 실제 데이터**, 나머지 4개 예외(시즌종료·장기체화·공급불가·프로모션종료)는 팀이 만든다.

#### (d) baseline과 headline metric
- 후보 baseline: 규칙 기반 min/max 재주문점 + SAP식 예외 규칙. 타당하다.
- 헤드라인 "오발주율 감소": 예외를 팀이 주입하고 팀이 채점 → **D등급** → 3a 상한 1. 리콜 예외만 실제 피드(A)이나 "리콜 SKU를 발주 목록에 심는 행위" 자체가 합성.
- 살릴 수 있는 지표(B/C등급): **"주입된 프롬프트/도구 오염 하에서 미승인 발주 API 호출 차단률"** + **"정상 발주 처리율(benign utility)"** + **"차단 지연(P95)"**. 이건 OpenShell 정책·감사로그가 정답을 주는 결정론적 픽스처다. 그러나 이 순간 아이디어는 I-03/I-01/N-C와 같은 실험이 된다.
- G1: **조건부 PASS**(위 재설계 시) / 원안은 FAIL.

#### (e) NVIDIA/NemoClaw/OpenShell이 코어가 되려면
- 구조: 발주 에이전트(OpenClaw/NemoClaw)는 OpenShell 안. 정책은 `GET /inventory/**`·`GET /recalls/**` allow, **`POST /purchase_orders` deny**. 차단 사유 카드가 사람에게 가고, 승인 시 Policy Advisor 흐름(`CONFIG:APPROVED`)으로 해당 발주에 한해 규칙 hot-reload, 또는 OrderSentry가 운영자 미들웨어로 `POST /purchase_orders` 본문을 검사해 리콜 SKU 포함 시 `reason_code: recalled_sku`로 deny. NVIDIA 문서의 Shopify 예시("deny inventory/order roots unless approved")가 이 구조의 공식 근거다(https://docs.nvidia.com/openshell/sandboxes/policies).
- "OpenShell을 지우면?": LLM 에이전트가 프롬프트 인젝션으로 검수를 건너뛰고 발주 API를 직접 호출할 수 있게 된다 → 차단 보장률이 무너진다. **G2 PASS(재설계 시)**.
- 장식 위험: 원안처럼 "OrderSentry가 LLM으로 예외를 설명"하는 것을 코어에 두면 OpenShell은 컨테이너에 불과. 또한 리콜/시즌 규칙 자체는 SQL로 끝나 "왜 에이전트냐"(ChatGPT I-09 판정)가 그대로 적용된다.

#### (f) 대체재와 차별화
`[2차]` RELEX, Blue Yonder, o9, Kinaxis, SAP IBP(예외 관리 https://support.sap.com/en/alm/sap-focused-run/expert-portal/focused-run-advanced-integration-monitoring-cloud-services/sap-integrated-business-planning.html), Oracle Retail, Netstock(예외 알림 https://www.netstock.com/blog/what-is-demand-planning). 이들은 "예외 알림"까지는 한다. 차별화 여지는 **"AI 에이전트가 발주를 자동화하는 시대에 잘못된 자동 발주를 런타임에서 물리적으로 막는 층"** 뿐이며, 이건 도메인이 아니라 보안 패턴이다.

#### (g) 6일 MVP·첫 병목·데모
- MVP: mock 커머스 API(FastAPI) + Favorita 서브셋 + 식약처 회수 피드 + OpenShell 정책 + 승인 UI 없음(CLI). 4일.
- 첫 병목: 회수 정보의 "제품명/바코드" ↔ 판매 데이터 SKU 매핑(Favorita는 SKU가 익명 정수라 **실제 매핑 불가** → 결국 합성).
- 데모: 회수 SKU가 포함된 발주안이 `POST` 시점에 403 + 감사 로그 + 사유 카드. 시각적으로는 좋다. 숫자는 약하다.

#### (h) 게이트·점수
| 게이트 | 판정 | 근거 한 줄 |
|---|---|---|
| G1 | 조건부 PASS | baseline=규칙 기반 예외 + 무방어 에이전트; 지표=미승인 발주 차단률/정상 처리율(픽스처 C등급). 원안 "오발주율"은 D등급 |
| G2 | 조건부 PASS | `POST /purchase_orders` deny + 승인 hot-reload/미들웨어가 코어일 때만 |
| G3 | PASS | OpenShell·NemoClaw·Nemotron·MCP(ERP 툴)·NAT |
| G4 | PASS | mock API + 공개 데이터, 키 없이 재현 가능 |
| G5 | PASS | 유통 산업 문제 |
| G6 | PASS | 3인 4일 |

점수: 축1 2.33 (1a3·1b3·1c3·1d1·1e1·1f3) / 축2 2.5 (2a3·2b3·2c3·2d1) / 축3 2.67 (3a1·3b3·3c3·3d3·3e3·3f3) / 축4 2.5 (4a3·4b1·4c3·4d3) → 총점 2.49 → **50/100 → 약함(재설계)**. 재설계해도 I-03/N-C의 하위 사례이므로 **독립 후보로는 폐기, 부품으로 흡수**.

---

### 2.3 ClaimGate — 의약품·건기식 AI 콘텐츠의 출고 전 위험 문구 검수·차단

#### (a) 페인포인트 실재성과 공개 근거
- `[사실]` 식약처 공식 보도자료(2026): 식품 온라인 부당광고 **165건** 적발(2026-06-05, https://mfds.go.kr/brd/m_99/view.do?seq=50051), 마약류 성분 표방 식품 부당광고 **60건**(2026-07-07, https://www.korea.kr/common/download.do?fileId=198503546&tblKey=GMN), 알부민 식품 부당광고 업체 9개소(2026-04-13, https://www.mfds.go.kr/brd/m_99/view.do?seq=49860), 온라인 식품 부당광고 업체 16개소(2025-12-15, https://www.foodsafetykorea.go.kr/portal/board/boardDetail.do?bbs_no=bbs080&menu_no=2857&ntctxt_no=49557).
- `[사실·언론(식약처 발표 인용)]` 키성장 식품·의약품 부당광고 166건: 위반 유형 분포 = 건기식 오인 86.2% / 미인정 기능성 5.8% / 질병 예방·치료 표방 3.6% / 의약품 오인 2.9% / 소비자 기만 1.5% (2026-03-20, https://www.foodtoday.or.kr/news/article.html?no=203313). 온라인 의약품 불법 판매·광고 **432건**(약사법, 2026-08-13, https://www.yna.co.kr/view/AKR20260813024000017). 추석 대비 부당광고·불법유통 **308건**(2026-09-17, https://www.hankyung.com/article/202609170174g).
  → 식약처 발표는 **위반 유형 분류(taxonomy)** 를 매번 같은 틀로 제공한다. 이것이 ClaimGate의 라벨 스키마가 된다.
- `[사실]` 미국 FDA OPDP Untitled Letters 목록(https://www.fda.gov/drugs/warning-letters-and-notice-violation-letters-pharmaceutical-companies/untitled-letters, 2026-09-17 갱신): 본 세션에서 목록을 집계한 결과 **총 103건, 2025년 61건, 2026년 23건(YTD)**, 2020~2024년은 연 1~2건. 그중 **65건은 위반 판촉물 PDF가 함께 공개**되어 있다. 즉 "위반 문구 원문 + FDA의 위반 사유"가 쌍으로 있는 **실제 라벨 데이터(A등급)** 가 존재한다. (집계는 목록 페이지 텍스트 기준이며 중복·누락 가능 `[추론]`.)
- `[2차]` 글로벌 MLR(Medical-Legal-Regulatory) 검토 병목: Veeva PromoMats가 tier 기반 리뷰로 승인시간 50~75% 단축을 주장 https://www.veeva.com/products/veeva-promomats/mlr-review ; Veeva의 Copli 인수·Falcon MLR https://www.veeva.com/resources/veeva-acquires-copli-launches-veeva-falcon-mlr-to-accelerate-content-review — **시장이 이미 "AI MLR"을 사고 있다는 증거**.
- **실제 사용자·업무 흐름** `[추론]`: (1) 제약사 RA/의학부의 MLR 검토(판촉물·상담 스크립트) (2) 건기식 업체 마케팅 → 한국건강기능식품협회 표시·광고 심의(https://ad.khff.or.kr/, 사전 심의 절차 존재 `[사실: 사이트 확인]`, 처리 기간은 `[미확인]`) (3) 광고대행사·커머스 셀러. AI가 상담·상세페이지를 대량 생성하기 시작하면서 "출고 전 검수"가 병목이 되는 흐름은 자연스럽다.

#### (b) end-to-end 시나리오
마케팅 에이전트(OpenClaw)가 제품 A의 상세페이지·상담 답변 초안 200건을 생성 → CMS `POST /contents/publish`를 호출 → OpenShell L7 정책이 이 엔드포인트를 **미들웨어 검사 대상**으로 지정 → ClaimGate 미들웨어가 본문에서 클레임 문장을 추출, 식약처 허가사항(효능효과·용법용량·주의사항) / 건기식 인정 기능성 / openFDA label과 대조(NeMo Retriever 임베딩 → Nemotron NLI: 지지/모순/근거없음) → 모순·근거없음 클레임이 있으면 **`403 middleware_denied, reason_code: unsupported_efficacy_claim`** → 에이전트는 사유를 보고 수정 후 재시도 → 통과분만 발행, 전 과정이 OCSF 감사 로그에 남음 → RA 담당자는 차단 큐만 검토.
→ "LLM에게 약이 안전하냐고 묻지 않는다. 허가사항이 판정하고, AI는 어떤 문장이 왜 허가사항을 벗어났는지 찾는다"(ChatGPT가 I-09에 권한 구조). 단 I-09와 달리 **마케팅 문장 ↔ 허가 문언의 대조는 SQL JOIN이 아니라 자연어 함의 판단**이므로 LLM 사용의 필연성이 성립한다.

#### (c) 데이터 소스와 6일 내 즉시 사용 가능성
| 소스 | 승인 | 라이선스 | 개인/민감정보 | 비고 |
|---|---|---|---|---|
| 식약처 의약품 제품 허가정보 API `[사실]` | 개발단계 **자동승인**, 10,000/일 | 제한 없음 | 없음 | 2026-09-18 갱신 https://www.data.go.kr/data/15095677/openapi.do |
| 식약처 e약은요 API `[사실: 인벤토리 기확인]` | 자동승인 | 제한 없음 | 없음 | 효능·사용법·주의사항 https://www.data.go.kr/data/15075057/openapi.do |
| 식약처 건강기능식품 기능성 원료인정 현황 `[사실: 페이지 존재]` | 자동승인 `[2차]` | 제한 없음 `[2차]` | 없음 | https://www.data.go.kr/data/15058359/openapi.do |
| openFDA Drug Label API `[2차]` | 불필요 | 공개 | 없음 | indications/contraindications/drug_interactions/warnings https://open.fda.gov/apis/drug/label |
| DailyMed API `[2차]` | 불필요 | 공개 | 없음 | https://dailymed.nlm.nih.gov/dailymed/services/v2/ |
| **FDA OPDP Untitled Letters + 판촉물 PDF** `[사실]` | 불필요 | 미국 정부 공개물 | 없음 | 65건 판촉물 원문 = 실제 위반 라벨 |
| 식약처 부당광고 보도자료 PDF `[사실]` | 불필요 | 공공누리 `[미확인 유형]` | 없음 | 예시 문구·유형 분포만 있고 **코퍼스는 아님** |
| 벤치마크 `[사실: arXiv 존재]` | 즉시 | 각 논문 라이선스 `[미확인]` | 없음 | MedHallu 10k QA https://arxiv.org/abs/2502.14302 · FDARxBench(FDA 제네릭 평가 추론) https://arxiv.org/abs/2603.19539 · SciFact https://github.com/allenai/scifact `[2차]` |

- **개인/민감정보 리스크**: 실제 상담 로그·환자 데이터를 쓰지 않는 한 없음. 데모 입력은 팀이 생성한 마케팅 문장 + 공개 위반 판촉물로 충분. **실제 환자 질의 로그를 쓰는 순간 의료정보 리스크가 생기므로 금지.**
- **규제 리스크** `[사실: 법령 존재]`: 약사법 제68조(과장광고 등의 금지 https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EC%95%BD%EC%82%AC%EB%B2%95/%EC%A0%9C68%EC%A1%B0), 식품 등의 표시·광고에 관한 법률 제8조(부당한 표시·광고 금지 https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EC%8B%9D%ED%92%88%EB%93%B1%EC%9D%98%ED%91%9C%EC%8B%9C%E3%86%8D%EA%B4%91%EA%B3%A0%EC%97%90%EA%B4%80%ED%95%9C%EB%B2%95%EB%A5%A0/%EC%A0%9C8%EC%A1%B0). **"AI 복약상담 서비스"로 포지셔닝하면 약사법·의료법 이슈가 생긴다** → 반드시 **B2B 내부 출고 전 검수(RA/MLR 보조)** 로 한정. 이 한정이 오히려 산업가치 서사를 명확하게 만든다.

#### (d) baseline과 headline metric
- baseline 3종: (B0) 키워드 블랙리스트("치료", "예방", "100%") — 협회 체크리스트 수준 (B1) Nemotron 제로샷 "이 문장 괜찮은가?" (B2) NemoGuard ContentSafety만 적용(효능 과장은 못 잡는다는 것을 보여주는 대조군).
- ours: 허가사항 grounded NLI(Retriever + Nemotron) + 정책 게이트.
- **headline metric(A등급)**: FDA OPDP 위반 판촉물 65건에서 FDA가 지적한 클레임 문장의 **검출 재현율**, 그리고 **비위반 문장 오탐률**(음성 세트 = 같은 제품의 FDA 승인 라벨 문장·Patient Information 문장 — 분포 차이가 있으므로 정직하게 "약한 음성"으로 표기). 보조: MedHallu/FDARxBench 서브셋 정확도(공개 벤치마크 + 재현 커맨드 → 3a=5 요건 충족 가능).
- **한국어 셋**: 식약처 유형 분류에 맞춰 팀이 작성 → C/D등급. 헤드라인로 쓰지 말고 "한국 적용 가능성" 보조 지표로만.
- "검수시간 감소" KPI는 실제 검수자가 없으므로 **D등급 → 제출서에서 빼거나 "추정"으로만**.
- G1 **PASS**: "baseline은 키워드 블랙리스트/제로샷이고, OPDP 65건 재현율에서 X→Y".

#### (e) NVIDIA/NemoClaw/OpenShell이 코어가 되려면
- 코어 구조 = **출고 게이트를 앱이 아니라 OpenShell 경계에 둔다.** (1순위) 운영자 미들웨어로 `POST /contents/**` 본문 검사·deny·findings. (후퇴안) `POST /contents/publish` L7 deny + CMS 자격증명을 샌드박스에 두지 않고 ClaimGate 검수 서비스만 보유(N-C 패턴) → 에이전트는 `POST /claimgate/review`만 허용.
- "OpenShell을 지우면?": 프롬프트 인젝션("검수 건너뛰고 바로 올려")으로 미검수 콘텐츠가 나간다. **G2 PASS.** 데모에서 이 공격을 일부러 넣어 막히는 장면(§7 🟢 신호)을 찍을 수 있다.
- 필연성 있는 NVIDIA 스택: OpenShell(게이트) / NemoClaw·OpenClaw(생성 에이전트 하네스) / Nemotron Nano(1차 판정)·Ultra(경계 사례 에스컬레이션 = 1e 라우팅 실증) / NeMo Retriever `nemotron-3-embed-1b`(허가사항 검색) / NeMo Guardrails(샌드박스 안 output rail, 미들웨어 이전 빠른 경로) / NAT(평가·프로파일러). 6개가 **한 요청 경로 위에 직렬로** 놓인다.
- 장식 위험: (i) 미들웨어 타임아웃 최대 30s — LLM 판정을 그 안에 못 넣으면 `fail_closed`로 전부 막힌다 → Nano 1차 + 캐시로 설계, Ultra는 비동기 큐. (ii) 미들웨어 구현이 3일을 넘기면 즉시 후퇴안으로. (iii) "AI 상담 챗봇 UI"에 시간을 쓰면 §7 🔴 "채팅창 하나".

#### (f) 대체재와 차별화
`[2차]` Veeva PromoMats/Falcon MLR, Indegene, IQVIA, Sorcero, Writer 등 AI MLR. 국내 건기식은 협회 사전심의(수동). NVIDIA 쪽은 NeMo Guardrails가 범용 콘텐츠 안전(https://developer.nvidia.com/blog/content-moderation-and-safety-checks-with-nvidia-nemo-guardrails)이지 허가사항 대조는 아님.
차별화 3가지: ① 검수 대상이 **사람이 쓴 판촉물이 아니라 에이전트가 생성·발행하는 콘텐츠**이고 ② 검수 결과가 **런타임 경계에서 강제**되며 ③ **한국 식약처 허가·기능성 데이터**를 근거로 쓴다. ①②는 Veeva에 없고, ③은 글로벌 벤더에 없다.

#### (g) 6일 MVP·첫 병목·데모
- D1: OPDP 65건 PDF → 클레임 문장 추출 + FDA 지적 문장 라벨링(수작업 병행), openFDA label 매칭. 식약처 API 키 발급.
- D2: 평가 스크립트 + baseline 3종 고정(**기능보다 먼저**, 규범 §6 경고).
- D3: Retriever + Nemotron NLI 검증기, Nano/Ultra 라우팅.
- D4: OpenShell 정책 YAML + 미들웨어(또는 후퇴안) + 공격 시나리오 5개.
- D5: 한국 건기식 20문장 보조 셋, OCSF 로그 → before/after 표, 프로파일러 수치.
- D6: README·재현 커맨드·제출서.
- **첫 병목**: OPDP 판촉물 PDF 파싱과 "FDA가 지적한 문장" 경계 확정(라벨 노이즈). 반나절 spike로 5건 해보고 안 되면 MedHallu/FDARxBench로 헤드라인을 바꾼다.
- 데모: 같은 초안 200건 → (좌) 무방어: 위반 문장 그대로 발행 / (우) ClaimGate: 차단 N건 + 사유 + 감사 로그. 그래프 1장: 재현율 vs 오탐률(baseline 3점 + ours 1점).

#### (h) 게이트·점수
| 게이트 | 판정 | 근거 한 줄 |
|---|---|---|
| G1 | **PASS** | baseline=키워드/제로샷, 지표=OPDP 65건 위반 클레임 재현율(A등급) + 공개 벤치마크 서브셋 |
| G2 | PASS(조건부) | 출고 게이트가 OpenShell 미들웨어/L7 deny + 무자격증명 샌드박스일 때만. 앱 내부 체크로 만들면 FAIL |
| G3 | PASS | OpenShell·NemoClaw·Nemotron(2종)·Retriever·Guardrails·NAT — 한 경로 위 직렬 |
| G4 | PASS | 공개 데이터, 캐시 픽스처로 키 없이 스모크 가능 |
| G5 | PASS | 규제 산업 문제 + 식약처 적발 수치 + FDA 집행 급증 |
| G6 | PASS(중 리스크) | PDF 파싱·미들웨어 gRPC가 병목. 3인 기준 가능, 2인이면 후퇴안 고정 |

점수(6일 현실치): 축1 3.0 (1a3·1b3·1c3·1d3·1e3·1f3) / 축2 4.0 (2a5·2b3·2c5·2d3; 2e 미발동으로 평균 제외) / 축3 2.67 (3a3·3b3·3c3·3d3·3e3·3f1) / 축4 4.0 (4a5·4b3·4c3·4d5) → 총점 3.25 → **65/100 → 경쟁권(최저 축 보강 후 착수)**.
상한(1b5·3a5·3b5·3e5 달성 시): 축1 3.33 / 축3 3.67 → 3.67 → **73/100**.
최저 축 = 축3 완성도. 올리는 방법은 명확하다(공개 벤치마크 + 골든셋 버전 고정 + 정책 위반 테스트 결과). 6일 안에 가능하다.

---

## 3. 3개 비교표

| 항목 | SourcingCritic | OrderSentry | ClaimGate |
|---|---|---|---|
| 페인포인트 근거 | 정부 정책 수치(공식) 있으나 구매자 특정 불가 | 글로벌 재고 비용(2차), ERP 예외 체계 존재 | 식약처 적발 수치(공식, 2026 다수) + FDA OPDP 급증(직접 집계) |
| 실제 사용자 | 정부 위원회(대외비) | 발주 담당/MD | RA/MLR, 건기식 마케팅, 협회 심의 |
| 데이터 즉시성 | ◎ (관세청 API 자동승인) | ○ (리콜만 실제) | ◎ (식약처·openFDA 자동/무승인) |
| 정답 라벨 등급 | D (LLM-judge) | D (합성 예외) / C (게이트 픽스처) | **A** (OPDP 65건) + 공개 벤치마크 |
| 승인·라이선스·PII | 없음 | Kaggle 규칙 확인 필요 | 없음(환자 로그 금지 조건) |
| OpenShell 필연성 | 없음(장식) | 재설계 시 있음(액션 게이트) | 재설계 시 있음(출고 게이트·미들웨어) |
| NVIDIA 스택 직렬성 | 낮음 | 중 | 높음(6개가 한 요청 경로) |
| 대체재 대비 차별화 | 약함(검증 불가한 critic) | 약함(보안 패턴이 전부) | 중~강(에이전트 생성물 + 런타임 강제 + 한국 데이터) |
| 6일 첫 병목 | HS↔품목 매핑, 정의 | 회수↔SKU 매핑(불가→합성) | PDF 파싱·미들웨어 gRPC |
| 게이트 | G1·G2 FAIL | G1·G2 조건부 | 전부 PASS(G2·G6 조건부) |
| 100점 | (참고)33 | 50 | 65 (상한 73) |
| 결론 | 폐기 | 부품으로 흡수 | 조건부 예선 후보 / 본선용 |

---

## 4. 기존 TOP 후보(I-03 / I-13 / I-11 / I-01)와의 상대 비교

주의: IDEA_EXPANSION_CHATGPT_REVIEW.md의 94/92/91/90은 ChatGPT의 자체 척도이고, 위 65/50/33은 본 문서가 규범 §3으로 매긴 점수다. **같은 척도가 아니므로 숫자 직접 비교는 하지 않고, 규범이 정한 결정 축으로 비교한다.**

| 축 | I-03 (+I-01 = Hybrid A) | I-13 (+I-11 = Hybrid B) | ClaimGate | OrderSentry | SourcingCritic |
|---|---|---|---|---|---|
| 숫자 등급(3a) | A (MCPTox 외부 벤치마크) | B (frozen held-out) | **A** (OPDP 실제 위반) + 공개 벤치 | D→C | D |
| OpenShell 필연성 | 최상(동적 행동 감사·최소권한이 곧 제품) | 상(샌드박스 리플레이) | 중상(출고 게이트; 후퇴안도 성립) | 중(액션 게이트 = I-03 하위) | 없음 |
| NVIDIA 생태계 편입(4a) | 정책 YAML·감사 리포트 | SKILL.md 승격 파이프라인 | **미들웨어/정책 = OpenShell에 꽂히는 산출물** | 정책 예시 1개 | 없음 |
| 산업가치·한국 맥락(축2·4d) | 보안 일반(한국 특화 약함) | 개발도구(한국 특화 약함) | **규제 산업 + 식약처 데이터 + 2026 적발 수치** | 유통 일반 | 공공 정책(구매자 없음) |
| 6일 리스크 | 중(MCP 어댑터) | 중(벤치 설계) | 중(PDF·gRPC) | 중하 | 하 |
| 심사위원이 기억할 한 문장 | "ASR 48%→4%, 유틸 96%" | "iteration vs frozen-test 곡선" | "에이전트가 쓴 효능 문구, 허가사항 밖이면 발행 자체가 안 된다" | (I-03 문장의 유통 버전) | 없음 |

**해석**
- ClaimGate는 **축2(산업가치·한국 맥락)에서 TOP 4를 이기고, 축1(OpenShell 필연성)에서 진다.** 심사 1번 항목이 "NVIDIA Agent 기술 활용 심도"이고 규범이 축1에 35%를 준 이상, 순서는 바뀌지 않는다.
- 다만 ClaimGate는 TOP 4가 공유하는 약점("보안·AgentOps 계열이라 현장 페인포인트가 개발자 내부용")을 정확히 메운다. **팀에 제약/건기식 도메인 지식이 있거나, 본선(10/7) 미션이 산업 응용을 요구할 때 최우선 카드**다.
- OrderSentry는 Hybrid A의 데모 시나리오(MCP 서버 = ERP 툴, 최소권한 정책이 `POST /purchase_orders`를 deny)로 흡수하면 "왜 기업이 사는가"를 설명하는 데 쓸모 있다. 독립 후보로는 I-03보다 약한 같은 실험이다.
- SourcingCritic은 규범 §7 🔴 세 개("LLM이 알아서", "채팅창/리포트 하나", "사람이 보기에 좋아 보인다")에 동시에 걸린다.

---

## 5. 결론 판정

| 아이디어 | 판정 | 조건·행동 |
|---|---|---|
| **ClaimGate** | **조건부 예선 후보(2순위 대안) / 본선용** | ① 반나절 spike: OPDP 판촉물 5건 PDF→클레임 추출·라벨링이 되는가 ② 반나절 spike: OpenShell 운영자 미들웨어 hello-world(deny + reason_code)가 등록·동작하는가. **둘 다 성공하면** Hybrid A/B와 나란히 최종 후보로 올린다. 하나라도 실패하면 본선용으로 보관하고 예선은 Hybrid A/B 유지. 포지셔닝은 반드시 "B2B 출고 전 검수", "AI 상담"이라는 단어 금지 |
| **OrderSentry** | **부품으로 흡수** | Hybrid A(I-03+I-01) 또는 N-C의 시나리오 중 하나로: "ERP 발주 MCP 서버 + 회수 피드 + `POST /purchase_orders` deny-unless-approved". 식약처 회수 API(자동승인)는 실제 외부 피드로 재사용 가치 있음. 독립 개발 금지 |
| **SourcingCritic** | **폐기** | 본선 미션이 "공급망/통상" 주제로 나올 때만 재검토. 그때도 baseline·라벨 문제는 그대로이므로 시각화 부품(관세청 API → 의존도 지도)만 재활용 |

D-5 시점의 최종 권고: **새 아이디어를 예선 1순위로 올리지 않는다.** ChatGPT 최종 리뷰의 결론("지금부터 새 아이디어를 늘리지 않는다. 최대 경쟁자는 scope creep")이 이 검토로도 유지된다. ClaimGate만 반일짜리 spike 2개를 조건으로 대기열에 넣는다.

---

## 6. 미확인·한계 (사실로 승격 금지)

1. `[미확인]` IHL $1.77조 원보고서 페이지는 본 세션에서 403(봇 차단)으로 직접 열람 실패. 인포그래픽(board.com) 경유 수치.
2. `[미확인]` UN Comtrade 무료 티어 레이트리밋 수치(서브에이전트 보고 "100 req/hour")는 개발자 포털 로그인 뒤에서만 확인 가능 → 미검증.
3. `[미확인]` 한국건강기능식품협회 광고심의 처리 기간(서브에이전트 보고 "10일")은 사이트 본문에서 직접 확인하지 못함.
4. `[미확인]` Kaggle Favorita/M5 데이터의 해커톤 제출용 재배포 허용 여부(대회 규칙 원문 미열람). 재현 스크립트는 "사용자가 Kaggle에서 직접 받는다" 방식으로 설계할 것.
5. `[미확인]` MedHallu·FDARxBench·SciFact의 라이선스 문구.
6. `[추론]` FDA OPDP 건수(2025년 61, 2026년 23, 판촉물 PDF 65)는 목록 페이지 텍스트 정규식 집계. 제출서에 쓰기 전 목록을 다시 세어 확정할 것.
7. `[미확인]` 식약처 부당광고 보도자료 첨부 PDF의 저작권 유형(공공누리 1유형 여부) 및 예시 문구 재게시 가능 범위.
8. `[2차]` 표기 항목 전부: 조사 서브에이전트가 읽은 출처. 제출서 인용 전 1회 직접 확인 필요. 특히 언론 보도(mk.co.kr, foodtoday, hankyung, yna)는 식약처 원 보도자료로 치환할 것.
9. 이 검토는 `SCORING_GOLDEN_RULE.md` **v2.0 사본 + v2.1 추가 규칙(메모리 기록)** 을 적용했다. 워크스페이스 v2.1 원문과 문구 차이가 있을 수 있다. 워크스페이스 `IDEA_EXPANSION_CHATGPT_REVIEW.md` 최종본 대신 ChatGPT 리뷰 **원문 배치 6개**를 읽었다. 판정 논리는 동일하나 최종본에만 있는 편집 내용은 반영되지 않았다.
10. 규범 §3의 2e(개인편의 감점)는 세 아이디어 모두 미발동이라 축2 평균에서 제외했다. 포함하는 해석을 쓰면 축2 점수가 달라진다(규범이 명시하지 않은 부분).
11. 점수는 "6일 현실치"다. 상한치는 조건을 명시했다. 상한을 기본값으로 인용하지 말 것.

---

## 7. Sources

**규범·프로젝트 문서**
- SCORING_GOLDEN_RULE.md / IDEA_EXPANSION_CHATGPT_REVIEW.md(원문 배치) / NVIDIA-FastCampus-Korea-Agentic-AI-Hackathon-2026.md (워크스페이스)

**NVIDIA 공식 (직접 확인)**
- https://docs.nvidia.com/openshell/latest/
- https://docs.nvidia.com/openshell/sandboxes/policies
- https://docs.nvidia.com/openshell/sandboxes/policy-advisor
- https://docs.nvidia.com/openshell/extensibility/supervisor-middleware
- https://github.com/NVIDIA/OpenShell/tree/main/proto
- https://github.com/NVIDIA/OpenShell/tree/main/crates
- https://docs.nvidia.com/nemo/agent-toolkit/latest/workflows/evaluate.html
- https://developer.nvidia.com/blog/content-moderation-and-safety-checks-with-nvidia-nemo-guardrails `[2차]`

**SourcingCritic**
- https://www.korea.kr/news/policyNewsView.do?newsId=148930850 (직접)
- https://www.kita.net/board/totalTradeNews/totalTradeNewsDetail.do?no=84662 (직접)
- https://www.data.go.kr/data/15100475/openapi.do (직접)
- https://www.data.go.kr/data/15101612/openapi.do `[2차]`
- https://tradedata.go.kr/cts/index.do `[2차]`
- https://unipass.customs.go.kr/ `[2차]`
- https://stat.kita.net/ `[2차]`
- https://comtradedeveloper.un.org/ (직접, 포털 존재만)
- https://www.motir.go.kr/kor/article/ATCL3f49a5a8c/168317/view `[2차]`
- https://www.korea.kr/news/policyNewsView.do?newsId=148897259 `[2차]`
- https://www.cisa.gov/executive-order-14017-securing-americas-supply-chains `[2차]`
- https://single-market-economy.ec.europa.eu/sectors/raw-materials/areas-specific-interest/critical-raw-materials/critical-raw-materials-act_en `[2차]`
- https://rmis.jrc.ec.europa.eu/eu-critical-raw-materials `[2차]`
- https://resilinc.ai/ · https://www.kotra.or.kr/subList/20000020753 · https://www.lgcns.com/kr/service/biz-process-intelligence/scm `[2차]`
- https://arxiv.org/abs/2509.03811 · https://arxiv.org/abs/2602.05524 · https://arxiv.org/abs/2411.10184 · https://arxiv.org/abs/2605.17036 · https://pmc.ncbi.nlm.nih.gov/articles/PMC13316148/ `[2차]`

**OrderSentry**
- https://www.data.go.kr/data/15074318/openapi.do (직접)
- https://open.fda.gov/apis/drug/enforcement/ (직접)
- https://help.sap.com/docs/SCMCSERM/d85738bd9bad40eaa2aec9680cde13b6/d7940c257a011014a71ac2a8a2918037.html (직접, 페이지 존재)
- https://docs.oracle.com/cd/B28094_01/aip/pdf/srp/1142/aip-srp-1142-ug.doc `[2차]`
- https://support.sap.com/en/alm/sap-focused-run/expert-portal/focused-run-advanced-integration-monitoring-cloud-services/sap-integrated-business-planning.html `[2차]`
- https://www.board.com/wp-content/uploads/2025/10/Board-Infographic_IHL-Distortion-Study.pdf `[2차]`
- https://www.ihlservices.com/product/fixing-inventory-distortion-whos-winning-whos-failing-whats-working `[미확인: 403]`
- https://www.kaggle.com/competitions/favorita-grocery-sales-forecasting/data (직접, 페이지 존재)
- https://www.kaggle.com/competitions/m5-forecasting-accuracy `[2차]`
- https://archive.ics.uci.edu/dataset/502/online+retail+ii `[2차]`
- https://help.ezadmin.co.kr/index.php?title=%EB%B0%9C%EC%A3%BC `[2차]`
- https://www.mk.co.kr/news/business/11009485 `[2차·언론]`
- https://www.netstock.com/blog/what-is-demand-planning `[2차]`
- https://arxiv.org/abs/2511.23366 · https://arxiv.org/abs/2405.14754 · https://www.tandfonline.com/doi/full/10.1080/16258312.2024.2399501 `[2차]`

**ClaimGate**
- https://www.fda.gov/drugs/warning-letters-and-notice-violation-letters-pharmaceutical-companies/untitled-letters (직접, 집계)
- https://mfds.go.kr/brd/m_99/view.do?seq=50051 (식약처 보도자료 2026-06-05)
- https://www.korea.kr/common/download.do?fileId=198503546&tblKey=GMN (식약처 보도자료 2026-07-07)
- https://www.mfds.go.kr/brd/m_99/view.do?seq=49860 (식약처 보도자료 2026-04-13)
- https://www.foodsafetykorea.go.kr/portal/board/boardDetail.do?bbs_no=bbs080&menu_no=2857&ntctxt_no=49557 (2025-12-15)
- https://www.foodtoday.or.kr/news/article.html?no=203313 `[언론, 식약처 발표 인용]`
- https://www.yna.co.kr/view/AKR20260813024000017 `[언론, 식약처 발표 인용]`
- https://www.hankyung.com/article/202609170174g `[언론, 식약처 발표 인용]`
- https://www.data.go.kr/data/15095677/openapi.do (직접)
- https://www.data.go.kr/data/15075057/openapi.do (프로젝트 데이터 인벤토리 기확인)
- https://www.data.go.kr/data/15058359/openapi.do (직접, 페이지 존재)
- https://open.fda.gov/apis/drug/label `[2차]`
- https://dailymed.nlm.nih.gov/dailymed/services/v2/ `[2차]`
- https://arxiv.org/abs/2502.14302 (직접) · https://arxiv.org/abs/2603.19539 (직접) · https://github.com/allenai/scifact `[2차]` · https://ojs.aaai.org/index.php/AAAI/article/view/35384 `[2차]` · https://aclanthology.org/2024.lrec-main.868 `[2차]`
- https://www.veeva.com/products/veeva-promomats/mlr-review · https://www.veeva.com/resources/veeva-acquires-copli-launches-veeva-falcon-mlr-to-accelerate-content-review `[2차]`
- https://ad.khff.or.kr/ (직접, 사이트 존재)
- https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EC%95%BD%EC%82%AC%EB%B2%95/%EC%A0%9C68%EC%A1%B0 (직접)
- https://www.law.go.kr/%EB%B2%95%EB%A0%B9/%EC%8B%9D%ED%92%88%EB%93%B1%EC%9D%98%ED%91%9C%EC%8B%9C%E3%86%8D%EA%B4%91%EA%B3%A0%EC%97%90%EA%B4%80%ED%95%9C%EB%B2%95%EB%A5%A0/%EC%A0%9C8%EC%A1%B0 (직접)

*조사 방법: 공개 웹·공식 문서만 사용. 로그인·개인 탭·게시·계정 변경 없음. 서브에이전트 3개(읽기 전용 웹 조사)로 1차 수집 후 핵심 출처 15건을 본 세션에서 직접 재열람했다.*
