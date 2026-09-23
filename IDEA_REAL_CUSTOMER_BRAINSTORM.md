---
title: "현업 타깃 아이디어 브레인스토밍 — 개발팀이 아닌 '매일 업무를 수행하는 사람'이 쓰는 에이전트 게이트 15종"
doc_type: idea_brainstorm_review
version: 1.0
created_at: 2026-09-23T09:45+09:00
event: NVIDIA Korea Agentic AI Hackathon 2026
deadline: 2026-09-28T23:59+09:00
days_left_at_review: 5
scope: 예선 아이디어 후보 확장 (현업 사용자 한정) → SCORING_GOLDEN_RULE 하드게이트·등급 판정 → TOP 5 상세
constraint_from_user:
  - 타깃은 구매·물류·품질·안전·현장운영·복지·보건행정·보험심사·금융운영·제조운영·매장운영·공공민원 등 현업. 개인비서·여행·범용 챗봇 제외
  - "답변만 잘하는 에이전트" 금지. 고위험 action 전 확인·차단·승인·감사 또는 다중 시스템 업무의 안전한 완료가 코어
  - OpenShell을 빼도 그대로인 아이디어는 명시적 감점·폐기
  - 'D등급만'(우리가 합성한 데이터를 우리가 채점)인 아이디어는 TOP 5 금지
  - 규제·의료는 진단/처방이 아니라 현업 검수·워크플로 보조로 한정
rubric_applied:
  - SCORING_GOLDEN_RULE.md v2.0 본문 + v2.1 추가 규칙(숫자 4등급 A/B/C/D, D만 있으면 3a 상한 1)
  - IDEA_EXPANSION_CHATGPT_REVIEW.md의 3대 반복 실수(NVIDIA 개수≠필연성 / 우리가 만들고 우리가 채점 / 서사 먼저)
  - IDEA_EXTERNAL_CANDIDATES_REVIEW.md §1의 "OpenShell에서 코어가 성립하는 지점" 판정 규칙
  - IDEA_REAL_WORLD_USE_CASES.md의 6항목 실활용 서식·결정 매트릭스 형식
companion_docs:
  - SCORING_GOLDEN_RULE.md
  - IDEA_EXPANSION_CHATGPT_REVIEW.md
  - IDEA_REAL_WORLD_USE_CASES.md
  - IDEA_EXTERNAL_CANDIDATES_REVIEW.md
research_method: 공개 웹·공식 문서·공개 보고서만. 로그인/개인 탭/게시/구매/계정 변경 없음. 서브에이전트 4개(읽기 전용 웹 조사)로 1차 수집 후 핵심 데이터 소스 6건을 본 세션에서 직접 재열람.
tags: "[사실]=출처 페이지에서 직접 확인 / [2차]=조사 서브에이전트 확인, 본 세션 미재검증 / [추론] / [미확인] / [언론]=언론 보도의 공식 발표 인용"
---

# 현업 타깃 아이디어 브레인스토밍 (F-01 ~ F-15)

> **READ THIS FIRST (for agents)**
> - 이 문서는 기존 후보(I-01~I-20, N-A/B/C, ClaimGate 등)가 **"에이전트를 만드는 조직"(개발/AppSec/플랫폼팀)** 에 치우쳤다는 문제의식에서, **매일 현업 업무를 수행하는 사람이 직접 쓰거나 그 업무 결과가 바뀌는 아이디어만** 새로 뽑은 것이다.
> - 판정 순서는 기존 규범 그대로: §2 하드게이트(G1~G6) → 숫자 등급(A/B/C/D) → 19개 지표 채점 → CAP → 100점 환산. 점수는 **`[DESIGN]` 가중치(35/25/30/10)에 따른 팀 내부 우선순위**이며 심사위원 점수가 아니다.
> - 이 문서는 **기존 파일을 수정하지 않았다.** 워크스페이스 쓰기 권한이 없어 세션 artifacts에 저장했다(경로는 최종 메시지 참조).
> - 결론 한 줄: **TOP 5 = F-02 HSGate(관세) > F-05 PermitGate(현장 안전) > F-01 PayGate(구매/AP) > F-04 RecallExec(매장 운영) > F-03 DGGate(물류).** 다섯 개 모두 "OpenShell을 빼면 프롬프트 인젝션 한 줄로 고위험 action이 실행된다"는 구조를 갖는다. 기존 A안(I-03+I-01+N-C)을 축1(NVIDIA 심도)에서 넘는 것은 없고, 축2(산업가치·한국 맥락)에서는 다섯 개 모두 A안·B안을 이긴다. ClaimGate(65/73)와는 동급이며 **HSGate와 PermitGate가 ClaimGate의 '현업 버전' 대체 카드**다.

---

## 0. TL;DR

| 순위 | 코드 | 이름 | 타깃 현업 | 정답 등급 | 100점(6일 현실치 / 상한) | 판정 |
|---|---|---|---|---|---|---|
| 1 | **F-02** | HSGate — 수입 HS 품목분류·통관신고 게이트 | 관세사무소·수입업체 무역 담당 | **A** (관세청 품목분류 결정사례) | **64 / 72** | **추진** |
| 2 | **F-05** | PermitGate — 위험작업 허가서 발급 게이트 | 건설·플랜트 현장 안전관리자 | C(+실제 기상 A) | **67 / 73** ※3a 리스크 | **추진(조건부)** |
| 3 | **F-01** | PayGate — 거래처 계좌변경·지급 게이트 | 구매/AP(지급) 담당자 | C(+국세청 상태 A) | **62 / 70** | **추진(조건부)** |
| 4 | **F-04** | RecallExec — 회수 공표→매장 판매차단 실행 | 유통 매장 운영·품질 담당 | B/C(+식약처 회수 API A) | **58 / 65** | 추진(부품 겸용) |
| 5 | **F-03** | DGGate — 위험물 출하 부킹 게이트 | 선사/포워더 부킹·수출 물류 담당 | B (PubChem UN번호) | **58 / 66** | 추진(부품 겸용) |
| 6 | F-13 | MinwonGate — 민원 답변 발송 게이트 | 지자체 민원 담당 공무원 | D(+PII 규칙 C) | 52 | 본선용 |
| 7 | F-14 | SubsidyGate — 보조금 집행 증빙 검수 | 보조사업 담당자·지자체 | D | 50 | 본선용 |
| 8 | F-11 | ClaimDesk — 보험 청구 심사 보조·지급 게이트 | 손보사 보상 심사자 | D(미국 합성만) | 48 | 본선용 |
| 9 | F-08 | EmitReport — 배출 측정 보고·초과 대응 게이트 | 사업장 환경관리 담당 | A(CleanSYS)이나 결정론 | 47 | 부품 |
| 10 | F-07 | LotHold — HACCP CCP 이탈→출하 보류 | 식품 제조 품질관리 | D | 45 | 부품(F-04와 통합) |
| 11 | F-09 | WelfareGate — 복지급여 자격 검토·지급결정 게이트 | 읍면동 복지 담당 공무원 | D(개인정보) | 44 | 본선용 |
| 12 | F-12 | AMLDesk — 의심거래 검토·계좌조치 게이트 | 은행 AML 준법 담당 | D(합성) | 42 | 폐기 |
| 13 | F-15 | PriceGate — 매장 가격·프로모션 변경 게이트 | 매장 운영·본사 MD | D | 38 | 폐기 |
| 14 | F-06 | RecipeGate — MES 레시피 변경 승인 게이트 | 제조 공정 엔지니어/오퍼레이터 | D | 36 | 폐기 |
| 15 | F-10 | NIMSGate — 마약류 취급보고 검수 게이트 | 병원·약국 마약류관리자 | D(데이터 비공개) | 33 | 폐기 |

**공통 판정 규칙 요약**
- **G2(OpenShell 코어) 판정**: 헤드라인 흐름이 (a) L7 `deny-unless-approved` (b) Supervisor Middleware 본문 검사·`reason_code` deny (c) 자격증명 분리(샌드박스에 실제 API 키 없음) (d) Policy Advisor 승인 hot-reload 중 하나에 **구조적으로** 의존해야 PASS. "샌드박스에서 돌렸다"는 위생이지 코어가 아니다 (IDEA_EXTERNAL_CANDIDATES_REVIEW §1 규칙 계승).
- **"OpenShell 빼면?" 테스트**: 빼도 결과가 같으면 G2 FAIL → 폐기. F-06·F-15·F-08은 이 테스트에서 "게이트 규칙이 SQL/if문으로 끝나고 LLM·샌드박스 둘 다 필연성이 없다"로 감점됐다.
- **D등급만 규칙**: 헤드라인 지표가 팀 합성+팀 채점(D)뿐이면 TOP 5 금지. F-06/07/09/10/11/12/13/14/15가 여기 걸렸다.

---

## 1. 공통 근거 — OpenShell에서 "코어"가 성립하는 지점 `[사실]`

IDEA_EXTERNAL_CANDIDATES_REVIEW.md §1과 동일한 표를 그대로 적용한다(재인용). 핵심만:

| 기능 | 이 문서에서의 용도 | 출처 |
|---|---|---|
| L7 REST 규칙(method/path allow·deny, default-deny), `enforcement: enforce/audit` | "조회는 허용, 실행(POST/PUT)은 deny-unless-approved" | https://docs.nvidia.com/openshell/sandboxes/policies |
| MCP 툴 규칙(`tools/call` tool 이름 단위; 인자 매칭 미지원) | 현업 시스템을 MCP 서버로 감쌀 때 실행 툴만 차단 | 동상 |
| Supervisor Middleware(허용된 요청 본문을 자격증명 주입 전 inspect/deny/replace, `403 middleware_denied` + `reason_code`, OCSF 로그, 기본 `fail_closed`, 타임아웃 500ms~30s) | "본문 안의 세번/계좌/SKU/풍속 조건"을 검사해 차단 | https://docs.nvidia.com/openshell/extensibility/supervisor-middleware |
| Policy Advisor(에이전트가 규칙 제안 → 사람이 approve → hot reload, `CONFIG:APPROVED` 감사) | 현업 담당자의 "승인" 행위를 정책 이벤트로 남김 | https://docs.nvidia.com/openshell/sandboxes/policy-advisor |
| 자격증명 분리(`request_body_credential_rewrite`) | 에이전트는 UNI-PASS/ERP/POS 실제 키를 절대 보유하지 않음 | https://docs.nvidia.com/openshell/sandboxes/policies |
| NVIDIA 공식 예시: Shopify Admin "deny high-impact inventory/order/customer roots unless approved" | "비즈니스 액션 게이트" 패턴의 공식 선례 | https://docs.nvidia.com/openshell/sandboxes/policies |

**리스크(기존 검토와 동일)**: 미들웨어는 gRPC 서비스 + 게이트웨이 TOML 등록 + 재시작 필요, `openshell/regex` 내장은 커스텀 표현식 미지원. 6일 안에 미들웨어가 막히면 **L7 deny + 무자격증명 샌드박스 + 검수 서비스가 대신 발행** 구조로 후퇴. 후퇴안도 G2 PASS.

---

## 2. 아이디어 15종 (F-01 ~ F-15)

각 항목은 사용자가 지정한 11개 필드를 고정 순서로 쓴다: ① 한 줄 이름 ② 타깃 고객 ③ 실제 반복 업무 ④ 문제 발생 비용/안전·규제 결과 ⑤ 현행 도구와 빈틈 ⑥ 공개·즉시 사용 데이터 ⑦ 6일 MVP ⑧ baseline + headline metric(등급) ⑨ OpenShell·NemoClaw가 코어가 되는 구조 + "빼면?" ⑩ 가장 큰 도입 장벽 ⑪ 판정. 현장 사례/시장 신호 URL은 ②~⑥에 inline으로 붙였다.

---

### F-01. PayGate — 거래처 계좌변경·지급 게이트

① **한 줄**: AP 에이전트가 공급업체 마스터 변경과 지급 배치를 처리하되, "계좌 변경 후 첫 지급·한도 초과·사업자 휴폐업"은 OpenShell 경계에서 물리적으로 차단되고 담당자 승인 후에만 은행/ERP API가 호출된다.
② **타깃 고객**: 중견·대기업 구매/AP 담당자, 회계 아웃소싱(세무법인) 지급 담당. 시장 신호: 미국 FBI IC3 2024 — 전체 사이버범죄 손실 $166억 중 **BEC $27.7억(피해액 2위)** `[사실]` https://www.ic3.gov/AnnualReport/Reports/2024_IC3Report.pdf ; 국내 기업 BEC 통계는 **직접 사례 미발견**(개인 대상 기관사칭 보이스피싱은 2016년 3,384건→2025년 13,323건 `[2차]` https://www.data.go.kr/data/15063815/fileData.do).
③ **반복 업무**: 매일/매주 지급 배치(수십~수천 건), 공급업체 계좌 변경 요청 처리(이메일·팩스), 신규 거래처 등록 시 사업자 상태 확인.
④ **비용/규제**: BEC 단건 손실이 억 단위. nsKnox는 "매출 $10억 이상 기업의 83%가 결제사기 피해" 주장 `[벤더주장]` https://nsknox.net/?sa=X. 내부통제(외부감사법 내부회계관리제도) 관점의 지급 승인 분리 의무 `[추론]`.
⑤ **현행 도구·빈틈**: Trustpair(SAP·Coupa 연동 계좌 검증) `[2차]` https://www.sap.com/uk/products/financial-management/partners/trustpair-trustpair-payment-fraud-prevention.html , nsKnox Master Data Guard `[2차]` https://nsknox.net/master-data-guard . 빈틈: 이들은 "사람이 ERP에서 하는 지급"을 검증한다. **AI 에이전트가 ERP·은행 API를 직접 호출하는 시대에 에이전트 자체의 권한을 런타임에서 제한하는 층**은 없다. 한국 사업자 상태(휴폐업) 연동은 직접 사례 미발견.
⑥ **공개 데이터**: 국세청 사업자등록정보 진위확인·상태조회 API — **개발/운영 모두 자동승인, 1일 100만 건, 이용허락 제한 없음, 30분 주기 갱신** `[사실]` https://www.data.go.kr/data/15081808/openapi.do (휴폐업 상태는 A등급 외부 정답). BEC 라벨 데이터셋은 **직접 사례 미발견** → 공격 시나리오는 팀 픽스처(C).
⑦ **6일 MVP**: mock ERP/은행 API(FastAPI) + 국세청 API 실연동 + OpenShell 정책(`GET /vendors/**` allow, `PUT /vendors/*/bank` deny, `POST /payments` 미들웨어 검사) + 인젝션 이메일 20종 픽스처 + 승인 CLI. 3인 4일.
⑧ **baseline·headline**: baseline = (B0) 무방어 에이전트 (B1) 앱 내부 if문 검증. headline = **"계좌변경 후 첫 지급·폐업 사업자 지급 차단률(목표 100%) + 정상 지급 처리율(benign utility) + P95 차단 지연"** — 폐업 판정은 국세청 실데이터(A), 인젝션 차단은 결정론 픽스처(C). "사기 손실 감소액"은 D → 제출서에서 제외.
⑨ **OpenShell 코어 구조**: 에이전트 샌드박스에는 은행/ERP 키가 없다(자격증명 분리). `POST /payments` 본문을 미들웨어가 검사해 `vendor.bank_changed_within_30d && first_payment` 또는 `nts_status != 계속사업자`이면 `403 reason_code: payment_hold`. 담당자 승인은 Policy Advisor `CONFIG:APPROVED`로 남는다. **빼면?** 인젝션된 "계좌가 바뀌었으니 이 계좌로 송금" 이메일이 에이전트를 통해 그대로 지급된다 → 차단 보장률 0. **G2 PASS.**
⑩ **최대 장벽**: 기업이 에이전트에게 지급 권한을 주는 것 자체가 초기 시장. "N-C Zero-Secret Connector의 AP 스킨"으로 보일 위험(4b 독창성 1점). OrderSentry(50점) 판정 논리와 동일한 약점을 안고 있으나, **국세청 실데이터 + BEC 실피해 + 보편적 구매자**로 세 축이 더 강하다.
⑪ **판정: 추진(조건부, TOP 3).** 조건 = 헤드라인 지표에 국세청 실데이터 기반 항목을 반드시 포함하고, 인젝션 픽스처는 AgentDojo 스타일(공격 세트 고정·공개)로 만든다.

---

### F-02. HSGate — 수입 HS 품목분류·통관신고 게이트

① **한 줄**: 상품 설명·스펙·MSDS에서 HS 10단위 후보를 관세청 결정사례 근거와 함께 산출하고 신고서 초안을 만들되, UNI-PASS 신고 전송은 관세사 승인 후에만, 근거 사례와 어긋나는 세번은 OpenShell 미들웨어가 차단한다.
② **타깃 고객**: 관세사무소·관세법인(국내 수천 개소), 수입업체 무역/구매 담당. 시장 신호: 관세법인 에이원이 과기부 지원으로 'AI 품목분류 추천시스템' 개발(정확도 98%·시간 90% 단축 주장) `[2차·언론]` https://www.taxtimes.co.kr/news/article.html?no=267226 ; 더존비즈온 ONE AI HS코드 식별 시연 90% `[2차·언론]` http://www.taxwatch.co.kr/article/tax/2024/11/05/0003 . → **시장이 이미 "AI 품목분류"를 사기 시작했다**는 증거이자, 동시에 "분류 정확도만으로는 차별화가 안 된다"는 경고.
③ **반복 업무**: 수입 건마다 세번 결정(관세사 1인당 일 수십 건 `[추론]`), 사전심사 신청(처리 30일, 분석수수료 3만 원/품목) `[2차]` https://www.customs.go.kr/cvnci/cm/cntnts/cntntsView.do?cntntsId=948&mi=3217 .
④ **비용/규제**: 오분류 시 관세 추징·가산세(관세법 제42조) `[추론: 조문 직접 미열람]`; 구체 사례 수치는 **직접 사례 미발견**. FTA 협정세율 적용 오류 시 소급 추징 리스크 `[추론]`.
⑤ **현행 도구·빈틈**: UNI-PASS 사전심사(수작업 회신), 해외 Avalara/Descartes/Zonos(한국 도입 사례 미발견 `[2차]`). 빈틈: 기존 AI 분류기는 **"추천"** 에서 끝난다. 에이전트가 신고까지 실행하는 순간 필요한 **"근거 없는 세번으로는 신고 자체가 나가지 않는다"** 는 런타임 경계가 없다.
⑥ **공개 데이터** ⭐: 관세법령정보포털 CLIP **품목분류 국내사례** — 각 사례에 `품명 / 물품설명(입력) / 결정세번 10단위(정답) / 결정사유(통칙·해설서 인용 근거)` 가 쌍으로 공개. 본 세션에서 검색어 "배터리" 하나로 품목분류사례 **975건 + 위원회 47건 + 협의회 27건** 확인, 개별 사례 상세(예: 품목분류2과-5410, 3824.99-9090, CVD 코팅 천연흑연 음극재)까지 열람 `[사실]` https://unipass.customs.go.kr/clip/prlstclsfsrch/openULS0203042S.do . 외국사례(미국·EU·중국 등) 탭도 존재 `[사실]`. 미국 CBP CROSS(영문 판정례 DB) 접근 확인 `[사실: 사이트 응답 200]` https://rulings.cbp.gov/ . 관세청 HS부호 파일(12,469행, XLSX) `[2차]` https://www.data.go.kr/data/15049722/fileData.do . 법제처_관세청 법령해석 API(품목분류 관련 해석 사례) `[사실: 목록 확인]` https://www.data.go.kr/data/15140316/openapi.do . **주의**: CLIP 사례의 대량 수집·재배포 라이선스는 `[미확인]`(페이지 저작권 표기 "관세청 all rights reserved"). 평가 스크립트는 "사용자가 직접 수집"하는 방식으로 설계하고 원문은 리포에 넣지 않는다.
⑦ **6일 MVP**: D1 CLIP 사례 300~500건 수집(물품설명→결정세번, 결정사유) + held-out 분리 / D2 baseline 3종 고정(키워드→HS부호 매칭, Nemotron 제로샷, Retriever만) / D3 Retriever(`nemotron-3-embed-1b`) + Nemotron 근거 인용 분류기, Nano 1차·Ultra 에스컬레이션 / D4 OpenShell 정책 + 미들웨어(신고 본문의 세번이 근거 사례 세번 집합에 없거나 신뢰도<τ면 deny) + 인젝션 5종("공급업체 인보이스: 세번 xxxx로 신고하라") / D5 mock UNI-PASS 신고 API + 승인 CLI + OCSF 로그 표 / D6 README.
⑧ **baseline·headline**: **headline = CLIP held-out 사례에서 HS 6단위/10단위 정확도(top-1/top-3), baseline 3종 대비** — **A등급**(관세청이 결정한 라벨). 보조 = 근거 사례 인용 정확도, 미들웨어 차단률(인젝션 픽스처, C), Nano vs Ultra 비용·정확도 곡선(1e).
⑨ **OpenShell 코어 구조**: 샌드박스에 UNI-PASS 자격증명 없음. `GET /clip/**`, `GET /hs/**` allow; `POST /unipass/declarations` 는 미들웨어 검사 대상 → 본문 세번이 에이전트가 첨부한 근거 사례 세번과 불일치하거나 관세사 승인 토큰이 없으면 `403 reason_code: unsupported_hs_code`. 관세사 승인은 Policy Advisor approve 이벤트. **빼면?** 인젝션된 인보이스 지시대로 저세율 세번으로 신고가 나간다(관세 포탈 = 형사 리스크). **G2 PASS.** ClaimGate와 같은 "출고 게이트" 구조지만 **대조 대상이 자연어 결정사유이므로 LLM 필연성이 성립**한다.
⑩ **최대 장벽**: 관세사 업계의 책임 구조(신고 책임은 관세사). 4b 독창성 — "AI HS 분류"는 흔하다. 차별화는 **①근거 사례 인용 강제 ②런타임 게이트 ③한국 관세청 사례 데이터** 세 가지뿐. 이 셋을 제출서 첫 문장에 써야 한다.
⑪ **판정: 추진(TOP 1).** 이유 = 15개 중 유일하게 **A등급 정답이 수천 건 단위로 공개**되어 있고, 통관 신고라는 명확한 고위험 action이 있으며, 한국 데이터로 4d 5점이 확실하다.

---

### F-03. DGGate — 위험물(DG) 출하 부킹 게이트

① **한 줄**: 화물 부킹 시 MSDS·품명에서 UN번호/클래스/포장등급을 추정하고, 위험물로 판정된 화물의 "일반화물 부킹"은 OpenShell 경계에서 차단, DG 담당자 승인 후에만 부킹 API가 호출된다.
② **타깃 고객**: 선사·포워더 부킹 데스크, 수출업체 물류 담당. 시장 신호: HMM 운항관리팀장 — "미신고 위험물이 선박화재 최대 원인", 2020~2023년 매년 리튬배터리 화재 2~5건, 화주 고의 미신고를 걸러낼 방법이 없다고 인정 `[2차·언론]` https://www.monthlymaritimekorea.com/news/articleView.html?idxno=52314 ; 해수부·관세청 미신고 위험물컨테이너 공동대응 `[2차]` https://www.mof.go.kr/doc/ko/selectDoc.do?docSeq=35391&menuSeq=971&bbsSeq=10 .
③ **반복 업무**: 부킹 접수마다 DG 여부 확인, DG 서류(DGD) 작성·검토, 적재 위치 결정.
④ **비용/규제**: 2019년 태국 정박 중 한국 컨테이너선 미신고 위험물 추정 화재·폭발 `[2차]`(해수부, 동상). HMM 추정 대형선 화재 시 선가 1,500억+화물 3,000억 `[벤더주장]`. 선박안전법·위험물 선박운송 및 저장규칙 `[추론: 조문 미열람]`.
⑤ **현행 도구·빈틈**: HMM 수작업 승인 절차(부킹→모니터링→선적신청→DG서류) `[2차]`. Labelmaster DGIS 등 해외 소프트웨어 국내 도입 미발견. 빈틈: **화주 신고에 의존**하며, 품명 텍스트("파워뱅크", "향수", "에어로졸")에서 DG 가능성을 추론해 부킹을 막는 층이 없다.
⑥ **공개 데이터**: PubChem PUG-View `Transport Information` 에 화학물질별 UN번호 제공(본 세션 확인: 아세톤 CID 180 → "UN 1090") `[사실]` https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/180/JSON?heading=Transport+Information ; PubChem GHS 분류 요약 `[2차]` https://pubchem.ncbi.nlm.nih.gov/ghs . UNECE GHS Rev.11 공식 PDF `[2차]` https://unece.org/transport/dangerous-goods/ghs-rev11-2025 . **IATA DGR·IMDG Code 본문은 유료** `[2차]` https://www.iata.org/en/publications/dgr/ . 일반 공산품(배터리 내장 기기 등)→UN번호 라벨셋은 **직접 사례 미발견**.
⑦ **6일 MVP**: PubChem에서 화학물질 500종 UN번호 골든셋 + 팀 작성 공산품 50종(약한 라벨) + MSDS PDF 파싱(섹션 14) + Nemotron 판정 + mock 부킹 API + OpenShell 미들웨어(선언 클래스 ≠ 추정 클래스 또는 미신고 시 deny). 3인 4~5일. **첫 병목**: MSDS 섹션 14가 있으면 문제가 사소해지고, 없으면 라벨이 없다 — "품명만으로 DG 의심" 구간을 헤드라인으로 잡아야 하는데 그 구간의 라벨이 약하다.
⑧ **baseline·headline**: headline = **PubChem 화학물질 골든셋에서 UN 클래스/번호 정확도(키워드 baseline 대비)** — **B등급**(외부 라벨이지만 화학물질 한정, 실무 분포와 다름). 보조 = 미신고 부킹 차단률(C).
⑨ **OpenShell 코어**: `POST /bookings` 미들웨어가 본문의 `dg_declared`와 에이전트 추정 클래스를 대조 → 불일치 시 `403 reason_code: undeclared_dg_suspected`. 승인은 DG 담당자. **빼면?** 화주 지시("일반화물로 부킹")를 그대로 실행 → 선박 화재 리스크. **G2 PASS.**
⑩ **최대 장벽**: 실무 헤드라인(공산품)이 B가 아니라 C~D. 선사 시스템 연동 장벽.
⑪ **판정: 추진(TOP 5, 부품 겸용).** HSGate와 데이터·구조가 유사하므로 **HSGate의 두 번째 도메인 시나리오("이 품목은 HS 3824이고 UN 1090이다")로 흡수**하는 것이 6일 안에서는 더 효율적이다.

---

### F-04. RecallExec — 회수 공표→매장 판매차단·격리 실행

① **한 줄**: 식약처 회수·판매중지 공표를 받아 매장 POS 판매차단·진열 철거·재고 격리 작업지시를 다중 시스템에 실행하되, 차단 대상 SKU는 반드시 공표 바코드와 일치해야 하고 범위 초과 차단·해제는 OpenShell이 막는다.
② **타깃 고객**: 대형마트·편의점·온라인몰 매장 운영/품질(QA) 담당, 식품 도매. 시장 신호: 2020~2025년 국내 식품 회수 735건(2025년 121건), 오리온 15억 원 상당 전량 자율회수·풀무원 계열 살모넬라 판매중단 `[2차·언론]` https://www.yna.co.kr/view/AKR20260515124700017 .
③ **반복 업무**: 회수 공문 수신 → 해당 SKU 식별 → 전 점포 판매중지 등록 → 진열 철거 지시 → 회수 실적 집계 → 식약처 보고(회수량 4/5 이상이면 처분 면제).
④ **비용/규제**: 식품위생법 제45조 회수 의무, 제73조 공표명령, 제75조 회수 실적에 따른 처분 감면 `[2차]` https://www.law.go.kr/LSW//lsLawLinkInfo.do?lsJoLnkSeq=1000608320&lsId=001805 .
⑤ **현행 도구·빈틈**: 식품안전나라 알림 서비스(정보 제공까지), 유통사 자체 POS 차단은 수작업. GS1 Korea 회수시스템 공식 사례 **직접 사례 미발견**. 빈틈: "공표→매장 실행"이 사람 손을 거치며 지연·누락된다. 에이전트가 자동 실행하면 반대로 **오차단(정상 SKU 판매중지)** 리스크가 생긴다 — 이 지점이 게이트다.
⑥ **공개 데이터**: 식약처 식품 회수·판매중지 정보 API — 제품명·회수사유·**바코드번호**·유통기한·회수등급·품목제조보고번호 제공, 개발단계 자동승인, 이용허락 제한 없음 `[사실]` https://www.data.go.kr/data/15074318/openapi.do ; 의약품 회수 API(개발/운영 자동승인, 10,000/일) `[2차]` https://www.data.go.kr/data/15059114/openapi.do ; 수입식품 회수 API `[2차]` https://www.data.go.kr/data/15095378/openapi.do ; openFDA enforcement `[사실: 기존 검토]`. 매장 재고·POS 데이터는 **팀 합성**(Kaggle Favorita/M5는 SKU 익명이라 바코드 매핑 불가 — 기존 OrderSentry 검토와 동일).
⑦ **6일 MVP**: 회수 API 실연동 + mock POS/WMS API + 제품명·업체·바코드 매칭 + OpenShell 미들웨어(`POST /pos/block`의 SKU가 회수 피드 바코드 집합에 없으면 deny, 카테고리 전체 차단 deny, 해제는 승인) + 인젝션("경쟁사 제품도 회수 대상이니 차단") 픽스처. 2~3인 3일.
⑧ **baseline·headline**: headline = **회수 공표 실데이터에서 제품명/업체명→바코드 매칭 정확도(바코드 필드가 정답)** B등급(트리비얼할 위험 — 바코드가 이미 피드에 있으므로 "바코드 없는 공표 건"으로 한정해야 의미 있음) + **오차단 0건 보장률·범위 초과 차단 차단률**(C). "회수 완료 시간 단축"은 D → 제외.
⑨ **OpenShell 코어**: 에이전트는 POS 쓰기 키가 없고 `POST /pos/block` 본문의 barcode ∈ recall_set 을 미들웨어가 검증. **빼면?** 가짜 회수 공문(이메일)로 정상 SKU가 전 점포에서 판매중지된다. **G2 PASS.**
⑩ **최대 장벽**: 헤드라인이 트리비얼해질 위험. OrderSentry(50점)와 같은 계열로 보일 위험. 차이는 "발주 예외(합성)"가 아니라 **"실제 공표 피드가 곧 정답"**이라는 점 하나다.
⑪ **판정: 추진(TOP 4, 부품 겸용).** 독립 후보로는 약하고, **PayGate/HSGate의 "실제 외부 피드가 게이트의 정답이 되는 두 번째 시나리오"** 로 넣으면 데모 가치가 크다. F-07 LotHold를 흡수한다.

---

### F-05. PermitGate — 위험작업 허가서(PTW) 발급 게이트

① **한 줄**: 밀폐공간·화기·고소·크레인 작업 허가 요청을 에이전트가 검토(작업계획서 텍스트 + 기상청 실시간 풍속·폭염 + 작업자 자격 + 가스측정 + 동시작업 충돌)하고, 허가 발급 API는 법정 조건 충족 + 안전관리자 승인 시에만 열리며, 발급 후 풍속이 기준을 넘으면 정책 hot-reload로 허가가 정지된다.
② **타깃 고객**: 건설·플랜트·조선 현장 안전관리자, 협력사 공사 담당. 시장 신호: 고용노동부 '중대재해 사이렌'이 사망사고를 사실상 매일 공개(누적 543건) `[2차]` https://labor.moel.go.kr/sasttc/cmmt/bbs_srn_list.do?seCdVal=B1 ; 2026-05-27 재해조사보고서 51건 최초 공개 `[2차]` https://www.moel.go.kr/news/enews/report/enewsView.do?news_seq=19436 .
③ **반복 업무**: 매일 아침 작업허가서 수십 건 검토·서명, TBM, 기상 확인, 동시작업 조정.
④ **비용/규제**: 중대재해처벌법 공표 44개소 중 경영책임자 실형 2년·법인 벌금 최고 20억 원, 위반 최다 조항은 "유해·위험요인 확인·개선 점검 미이행"(41건, 24%) `[2차]` https://www.moel.go.kr/news/enews/report/enewsView.do?news_seq=19155 . 산업안전보건기준에 관한 규칙 제37조: 순간풍속 10m/s 초과 시 타워크레인 설치·수리·해체 중지, 15m/s 초과 시 운전 중지; 제383조 철골작업 풍속 10m/s 이상 중지 `[2차]` https://www.law.go.kr/LSW//lsSideInfoP.do?lsiSeq=273603&joNo=0037&joBrNo=00&docCls=jo&urlMode=lsScJoRltInfoR .
⑤ **현행 도구·빈틈**: 종이/엑셀 PTW, 해외 EHS SaaS(Enablon·Intelex, 국내 도입 공식 사례 `[미확인]`). 빈틈: 법정 기준이 텍스트로만 존재하고 **실시간 기상·자격·가스측정과 연동된 자동 게이트가 없다** `[2차·추론]`.
⑥ **공개 데이터**: 기상청 단기예보 API — 개발/운영 자동승인, 10,000/일, 공공누리 제1유형 `[사실: 프로젝트 인벤토리 기확인]` https://www.data.go.kr/data/15084084/openapi.do ; KOSHA 재해사례·재해조사보고서(사고 상황·기상 조건 텍스트 포함, 구조화 라벨 아님) `[2차]`; 산안규칙 조문(law.go.kr) `[2차]`. 작업허가서 실데이터·"허가했어야/막았어야" 라벨은 **직접 사례 미발견** → 재해조사보고서 51건에서 팀이 "이 허가 요청이 들어왔다면 차단 사유는 무엇인가"를 역구성(C등급, 실사고 기반).
⑦ **6일 MVP**: 허가 요청 스키마(작업 유형·높이·장비·인원·자격·가스측정값·위치) + 기상청 실연동 + 법정 조건 룰(결정론) + Nemotron이 작업계획서 자유 텍스트에서 위험요인·동시작업 충돌 추출 + OpenShell 미들웨어(`POST /permits/issue` 본문 조건 미충족 시 deny; 풍속 상승 시 `network_policies` hot-reload로 `POST /permits/*/activate` 차단) + 재해조사 기반 픽스처 30건. 3인 4~5일.
⑧ **baseline·headline**: baseline = (B0) 체크리스트 룰만 (B1) 제로샷 LLM. headline = **재해조사보고서 역구성 픽스처에서 "차단됐어야 할 허가" 검출률 + 정상 허가 통과율** — **C등급**(실사고 기반이나 라벨은 팀이 구성). 보조 = 기상청 실데이터 기반 풍속 초과 시 정지 지연(P95, 결정론 A).
⑨ **OpenShell 코어**: 에이전트는 허가 시스템 쓰기 키가 없다. 미들웨어가 본문의 `wind_speed`, `o2_pct`, `qualification_ids`를 법정 기준과 대조. 풍속 이벤트로 hot-reload(동적 정책 계층 활용 = 1b 5점 후보). **빼면?** 현장 관리자의 "오늘 바쁘니 그냥 허가 내라" 지시나 인젝션이 그대로 허가로 이어진다. **G2 PASS.** 다만 **"왜 LLM이냐"** 에 답이 필요하다: 답은 "작업계획서·동시작업·재해사례는 자유 텍스트이고, 결정론 룰은 정책 YAML로 내리며 LLM은 룰 입력값 추출과 위험요인 추론만 맡는다"(ChatGPT가 I-09에 권한 구조와 동일).
⑩ **최대 장벽**: 헤드라인이 C등급. 안전 도메인 특유의 "AI가 허가했다"는 책임 논란 → 반드시 "안전관리자 승인 보조"로 포지셔닝.
⑪ **판정: 추진(조건부, TOP 2).** 조건 = 헤드라인 픽스처를 재해조사보고서 원문 기반으로 만들고 리포에 출처 링크를 남긴다(D로 떨어지지 않게). 한국 맥락(중대재해처벌법)과 동적 정책 데모가 강력하다.

---

### F-06. RecipeGate — 제조 공정 파라미터/레시피 변경 승인 게이트

① **한 줄**: MES 레시피 변경 요청을 에이전트가 검토(허용 범위·과거 불량 연관·MOC 절차)하고 MES 쓰기는 승인 후에만.
② **타깃**: 제조 공정 엔지니어/오퍼레이터. 시장 신호: CSB "Management of Change" 안전 회보 `[2차]` https://www.csb.gov/management-of-change/ , AB Specialty Silicones 2019 사고 보고서 `[2차]` https://www.csb.gov/file.aspx?DocumentId=6220 .
③ **반복 업무**: 교대별 파라미터 조정·레시피 배포. ④ **비용**: 폭발·불량 로트; 금액 `[미확인]`. ⑤ **현행**: MES 변경관리 기능(Siemens Opcenter 등, 공식 확인 `[미확인]`). 빈틈은 "에이전트가 MES를 직접 쓴다"는 가정 자체가 아직 현장에 없다.
⑥ **데이터**: SECOM(1,567샘플·591피처, pass/fail) `[2차]` http://archive.ics.uci.edu/ml/datasets/secom , NASA C-MAPSS `[2차]` — **레시피 변경↔결과 라벨이 아니다.** 변경 요청·승인 데이터 **직접 사례 미발견**.
⑦ **MVP**: mock MES + 범위 룰 + OpenShell deny. 2일. ⑧ **headline**: 범위 밖 변경 차단률 — **D(팀 합성·팀 채점)**, SECOM은 관련성 없음.
⑨ **OpenShell**: `PUT /mes/recipes/*` deny-unless-approved. **빼면?** 앱 if문으로 동일 → 필연성 약함. 룰이 숫자 범위 비교라 LLM도 불필요. **G1 FAIL(D만), G2 약함.**
⑩ **장벽**: 데이터 부재. ⑪ **판정: 폐기.** 본선에서 NVIDIA FOX/Pegatron 사례(기존 I-08)와 결합할 때만 재검토.

---

### F-07. LotHold — HACCP CCP 이탈→출하 보류 게이트

① **한 줄**: CCP 모니터링(온도·금속검출·pH) 이탈 시 해당 로트 출하 API를 차단, 개선조치 기록 + QA 승인 후 해제.
② **타깃**: 식품 제조 품질관리(HACCP 팀장). 시장 신호: HACCP 의무적용 단계 확대(축산물 2029년까지) `[2차·언론]` https://www.foodtoday.or.kr/news/article.html?no=202149 ; 식품안전나라 부적합 식품 공표 게시판(RSS) `[2차]` https://www.foodsafetykorea.go.kr/portal/fooddanger/testUnfitDom.do?menu_no=4409&menu_grp=MENU_NEW02 .
③ **반복 업무**: 매 로트 CCP 기록·검증, 이탈 시 개선조치서. ④ **비용**: 회수·영업정지(F-04 참조). ⑤ **현행**: 스마트HACCP(인증원, 상세 `[미확인]`). ⑥ **데이터**: CCP 이탈 라벨 데이터 **직접 사례 미발견** → 합성.
⑦ **MVP**: 2일. ⑧ **headline**: 이탈 로트 출하 차단률 — **D**. ⑨ **OpenShell**: `POST /shipments` deny when lot.hold — 결정론, LLM 불필요. **G1 FAIL(D만).**
⑩ **장벽**: 데이터. ⑪ **판정: 부품.** F-04 RecallExec의 "출하 보류" 시나리오로 흡수(실제 회수 공표 데이터를 트리거로 쓰면 D→B).

---

### F-08. EmitReport — 대기·수질 배출 측정결과 보고·초과 대응 게이트

① **한 줄**: 자가측정·TMS 결과를 에이전트가 정리해 환경부 보고 초안을 만들고, 배출허용기준 초과 시 개선명령 대응 초안과 보고 전송은 담당자 승인 후에만.
② **타깃**: 사업장 환경관리 담당(대기 1~3종 사업장). 시장 신호: CleanSYS 굴뚝 TMS 실시간 공개 `[2차]` https://cleansys.or.kr/index.do .
④ **비용/규제**: 대기환경보전법 제32조(측정기기 조작 금지)·제33조(개선명령)·제89조(7년 이하 징역/1억 이하 벌금) `[2차]` https://www.law.go.kr/LSW/lsInfoP.do?lsId=001773&ancYnChk=0 .
⑥ **데이터**: CleanSYS TMS 2015~2023 사업장별 측정값 공개 `[2차]` https://data.kei.re.kr/data/d4e31251-9186-4d5b-bae8-a46046fa59f8 → 초과 여부는 A등급 정답이지만 **비교 연산이 결정론**이라 LLM·에이전트 필연성이 없다.
⑧ **headline**: 초과 탐지 정확도(A, 그러나 트리비얼) / 보고서 초안 품질(D). ⑨ **OpenShell**: 보고 전송 deny-unless-approved. **빼면?** 결과 동일에 가깝다(허위보고 인젝션 시나리오는 억지). **G2 약함.**
⑪ **판정: 부품.** 실제 공개 시계열이 있다는 점만 가치. 본선 미션이 환경이면 재검토.

---

### F-09. WelfareGate — 복지급여 신청 자격 사전검토·지급결정 게이트

① **한 줄**: 신청서·소득재산 자료를 에이전트가 급여 기준과 대조해 검토 초안을 만들고, 지급 결정 입력은 담당 공무원 승인 후에만.
② **타깃**: 읍면동 복지 담당 공무원. 시장 신호: 사회복지공무원 1인당 568명 담당(2024 국감) `[2차·언론]` https://www.newspim.com/news/view/20241008000572 ; 2024년 부정수급 신고 3,140건, 환수 결정 15.7억 원 `[2차]` https://www.mohw.go.kr/board.es?mid=a10503010100&bid=0027&act=view&list_no=1484062 ; 2022년 차세대 사회보장정보시스템 개통 오류(감사원) `[2차·언론]` https://www.etnews.com/20240730000374 .
⑤ **현행**: 행복이음(ssis.or.kr) — 자격·소득 조회는 되나 검토 초안 자동화 없음 `[2차]`. ⑥ **데이터**: 지자체복지서비스 API(자동승인, 1,000/일) `[2차]` https://www.data.go.kr/data/15108347/openapi.do 는 서비스 목록뿐. 개인 자격 판정 라벨은 개인정보로 **비공개**.
⑧ **headline**: 자격 판정 정확도 — Nemotron-Personas-Korea로 가상 신청자를 만들고 팀이 채점 → **D**. ⑨ **OpenShell**: 지급 결정 API deny-unless-approved + 개인정보 외부 유출 차단(자격증명 분리). **G2 PASS**이나 **G1 FAIL(D만)**.
⑩ **장벽**: 개인정보·공공 조달. ⑪ **판정: 본선용.** 공공 미션이 나올 때 Personas-Korea(기존 I-17)와 결합.

---

### F-10. NIMSGate — 마약류 취급보고(NIMS) 검수 게이트

① **한 줄**: 병원·약국의 마약류 취급 보고를 재고·처방 기록과 대조해 초안 생성, 수량 불일치·미보고를 사전 차단, 전송은 관리자 승인 후에만.
② **타깃**: 마약류관리자(병원 약제부·약국). 시장 신호: 마약류관리법 제11조 매 거래 보고 의무(2018-05 전면 시행) `[2차]` https://www.mfds.go.kr/wpge/m_738/de010114l002.do ; 2024-08 미보고 등 55개소 조치 `[2차]` https://nodrugzone.mfds.go.kr/fileView.do?uniqueKey=cb00d1a0008a85e71a41b8741facbffed5653d4f091c471e51f1937b33860386 .
④ **규제**: 경고~업무정지 2개월~허가취소(4차) `[2차·언론]` https://www.newsthevoice.com/news/articleView.html?idxno=26964 . ⑥ **데이터**: 거래 단위 데이터 **비공개 원칙**, 라벨 **직접 사례 미발견**.
⑧ **headline**: D. ⑨ **OpenShell**: 전송 게이트는 성립하나 데이터가 전부 합성. **G1 FAIL.** ⑩ **장벽**: 마약류 데이터 취급 자체가 규제. ⑪ **판정: 폐기.** (의료 행정으로 범위를 좁혀도 데이터가 없다.)

---

### F-11. ClaimDesk — 보험 청구 심사 보조·지급 게이트

① **한 줄**: 청구 서류를 약관·지급기준과 대조해 심사 초안 작성, 소액·정형 건만 자동지급 허용, 나머지 지급 API는 심사자 승인 후에만. (진단·의학 판단 없음, 서류 정합성·약관 대조만.)
② **타깃**: 손보사 실손/자동차 보상 심사자. 시장 신호: 실손24 청구전산화 — 2025-10-25 의원·약국까지 확대(10.5만 기관), 2026-04-15 기준 연계율 28.4%, 청구 180만 건 누적 `[2차]` https://www.fsc.go.kr/no010101/86709 ; 2025년 보험사기 적발 1조 1,571억 원, 사고내용 조작(진단서 위변조 등) 54.9% `[2차·언론]` https://intn.co.kr/news/articleView.html?idxno=2049887 .
⑤ **현행**: 실손24는 전송만. 손보사 AI 심사 공식 사례 **직접 사례 미발견**. ⑥ **데이터**: CMS DE-SynPUF(미국 합성) `[2차]` https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf , Kaggle 자동차보험 사기(합성, MIT) `[2차]`. 국내 약관·청구 라벨 **없음**.
⑧ **headline**: D(국내) / 미국 합성(관련성 낮음). ⑨ **OpenShell**: 지급 API 한도·승인 게이트 — 성립. **G1 FAIL(D만).** ⑩ **장벽**: 금융규제·개인의료정보. ⑪ **판정: 본선용.** 실손24라는 강한 한국 신호는 있으나 예선 6일 안에 숫자가 없다.

---

### F-12. AMLDesk — 의심거래 검토·계좌 조치 게이트

① **한 줄**: AML 알림 검토·STR 초안을 에이전트가 만들고, 계좌 지급정지·STR 제출은 담당자 승인 후에만.
② **타깃**: 은행/핀테크 AML 준법 담당. 시장 신호: 가상자산사업자 STR 2024년 19,658건→2025년 62,055건 `[2차·언론]` https://v.daum.net/v/20260917091759996 ; 보이스피싱 정보공유 AI 플랫폼(ASAP) 46만 건 공유·663.6억 원 사전차단 `[2차]` https://www.fsc.go.kr/no010101/85959 .
④ **규제**: 통신사기피해환급법 제4조 지급정지 `[2차]`. ⑤ **현행**: NICE Actimize 등 성숙한 벤더 시장(국내 도입 공식 확인 `[미확인]`). ⑥ **데이터**: IBM AMLSim(Apache-2.0, 합성), IBM AML(CDLA), SAML-D(합성), Elliptic(BTC, CC BY-NC-ND) `[2차]` — 모두 합성 또는 암호화폐.
⑧ **headline**: 합성 데이터 탐지율 → **D 성격**(외부 합성이라 C로 볼 여지 있으나 국내 STR과 무관). ⑨ **OpenShell**: 지급정지 API 게이트 성립. ⑩ **장벽**: 성숙 벤더·금융보안 규제. ⑪ **판정: 폐기.** 대체재가 너무 강하고 숫자가 실무와 무관.

---

### F-13. MinwonGate — 공공 민원 배정·답변 발송 게이트

① **한 줄**: 국민신문고 민원을 분류·부서 배정·답변 초안 작성하고, 발송은 담당자 승인 후에만; 답변에 타인 개인정보·미확정 법령 해석이 포함되면 전송 차단.
② **타깃**: 지자체/공공기관 민원 담당 공무원. 시장 신호: AI정부24 시범운영 누적 2,848만 명·질의 3,046만 건, 프롬프트 공격 악용 사례 확인 후 가드레일·개인정보 자동마스킹 도입 `[2차·언론]` https://www.mt.co.kr/policy/2026/06/30/2026063011082018363 .
④ **비용/규제**: 정부24 오류로 1,233명 개인정보 노출 → 개보위 과징금 2억 7,300만 원+과태료 750만 원 `[2차·언론]` https://www.newsis.com/view/NISX20260527_0003646514 ; 공무원 개인정보 고의 유출 원스트라이크아웃(파면·해임) `[2차]` https://www.mpm.go.kr/board/file/bbs_0000000000000029/3553/FILE_000000100022453/996DF015A8344c87A86B77E94005119A .
⑥ **데이터**: 국민권익위 민원빅데이터 분석정보 API — 개발 자동승인, 100건/일, **공공누리 2유형(상업적 이용 금지)**, 키워드 통계만 `[2차]` https://www.data.go.kr/data/15143948/openapi.do . 민원 텍스트→부서 라벨 **직접 사례 미발견**(AI Hub 민원 데이터는 내국인 승인·비상업 제약 — 프로젝트 메모리 기확인).
⑧ **headline**: 부서 배정 정확도(D) / 개인정보 포함 답변 차단률(주민번호·전화번호 정규식 → 결정론 C). ⑨ **OpenShell**: `POST /answers/send` 미들웨어 PII 검사 + 승인. **G2 PASS**이나 헤드라인이 결정론 또는 D. ⑩ **장벽**: 공공 조달·데이터. ⑪ **판정: 본선용.** 공공 미션 시 Personas-Korea로 민원 생성 + PII 게이트 조합.

---

### F-14. SubsidyGate — 국고보조금 집행 증빙 검수 게이트

① **한 줄**: e나라도움 집행 등록 전 증빙(세금계산서·카드내역)을 사업계획·집행기준과 대조하고, 부적정 항목 등록 차단, 집행 등록·이체는 담당자 승인 후에만.
② **타깃**: 보조사업 수행기관 담당자, 지자체 보조금 담당. 시장 신호: 최근 3년 부정수급 1,383건·1,290.9억 원 `[2차·언론]` https://taxtimes.co.kr/news/article.html?no=271833 ; 2026-02-25 정부 보도자료 "역대 최다" + 차세대 e나라도움 재구축 필요 `[2차]` https://www.korea.kr/common/download.do?fileId=198369947&tblKey=GMN .
④ **규제**: 보조금관리법 제재부가금 최대 5배·명단 공표 `[2차]` https://law.go.kr/lsInfoP.do?lsId=000729 . ⑥ **데이터**: 국고보조금 정보 API(자동승인, 10,000/일) `[2차]` https://www.data.go.kr/data/15097584/openapi.do 는 거시 통계. 증빙 적정/부적정 라벨 **없음**.
⑧ **headline**: D. ⑨ **OpenShell**: 집행 등록 API 게이트 성립. **G1 FAIL(D만).** ⑪ **판정: 본선용/부품.** PayGate의 "공공 지급 버전"으로 흡수 가능.

---

### F-15. PriceGate — 매장 가격·프로모션 변경 실행 게이트

① **한 줄**: 프로모션 가격 변경을 POS/ESL에 반영하되, 원가 이하·단위가격 표시 위반·기간 오류·전 매장 일괄 변경은 차단·승인 필요.
② **타깃**: 매장 운영·본사 MD. 시장 신호: 롯데면세점 ESL 도입 `[2차·언론]` https://www.munhwa.com/article/11194937 (규모 통계 `[미확인]`).
④ **규제**: 가격표시제 실시요령 제17조 과태료 1,000만/3,000만 원 `[2차]` https://www.law.go.kr/LSW/admRulInfoP.do?admRulSeq=70305 ; 2025-04 단위가격 표시 확대 `[2차]` .
⑥ **데이터**: 참가격 API(승인유형 `[미확인]`), 오표시 라벨 **없음**. ⑧ **headline**: D. ⑨ **OpenShell**: 게이트 성립하나 룰이 SQL(원가<가격, 기간 유효) → LLM 불필요, 앱 if문과 동일. **G1 FAIL, G2 약함.** ⑪ **판정: 폐기.**

---

## 3. 하드게이트 판정표 (TOP 5)

| 게이트 | F-02 HSGate | F-05 PermitGate | F-01 PayGate | F-04 RecallExec | F-03 DGGate |
|---|---|---|---|---|---|
| G1 정량 증명 | **PASS** — baseline=키워드/제로샷, 지표=CLIP held-out HS 정확도(A) | PASS(조건부) — baseline=체크리스트 룰, 지표=재해조사 역구성 픽스처 검출률(C)+기상 실데이터 정지 지연(A) | PASS(조건부) — baseline=무방어/앱 if문, 지표=폐업·계좌변경 지급 차단률(A+C)+benign utility | PASS(조건부) — 지표=바코드 없는 공표건 매칭(B)+오차단 0 보장(C) | PASS — 지표=PubChem UN 클래스 정확도(B) |
| G2 OpenShell 코어 | PASS — 신고 전송 미들웨어/L7 deny + 무자격증명 | PASS — 허가 발급 미들웨어 + 풍속 hot-reload | **PASS(최상)** — 자격증명 분리 + 지급 본문 검사 | PASS — POS 차단 본문 검사 | PASS — 부킹 본문 검사 |
| G3 NVIDIA 3종 | PASS — OpenShell·NemoClaw·Nemotron×2·Retriever·NAT | PASS — OpenShell·NemoClaw·Nemotron·NAT | PASS — OpenShell·NemoClaw·Nemotron·NAT | PASS | PASS — +Retriever |
| G4 재현성 | PASS — 사례는 사용자가 수집(라이선스 미확인), 캐시 픽스처로 스모크 | PASS — 기상청 응답 캐시 | PASS — 국세청 응답 캐시 | PASS — 회수 API 캐시 | PASS — PubChem 캐시 |
| G5 산업 문제 | PASS — 통관/관세 | PASS — 중대재해 | PASS — 지급 사기 | PASS — 식품 안전 | PASS — 해상 안전 |
| G6 6일 완주 | PASS(중) — 사례 수집 스크래핑이 병목 | PASS(중) — 픽스처 라벨링 | PASS(하) | PASS(하) | PASS(중) — MSDS 파싱 |

## 4. 채점 (TOP 5, 0/1/3/5 앵커, 6일 현실치 → 상한)

| 코드 | 축1(35%) | 축2(25%) | 축3(30%) | 축4(10%) | 총점 | 100점 | 상한 조건 |
|---|---|---|---|---|---|---|---|
| F-02 | 3.00 (1a3·1b3·1c3·1d3·1e3·1f3) | 4.00 (2a5·2b3·2c5·2d3) | 2.67 (3a3·3b3·3c3·3d3·3e3·3f1) | 3.00 (4a3·4b1·4c3·4d5) | 3.22 | **64** | 1b5·3a5(골든셋 버전 고정+재현 커맨드)·3b5·3e5 → **72** |
| F-05 | 3.00 (1a3·1b5·1c3·1d1·1e3·1f3) | 4.50 (2a5·2b5·2c5·2d3) | 3.00 (3a3·3b3·3c3·3d3·3e3·3f3) | 3.50 (4a3·4b3·4c3·4d5) | 3.43 | **67** | 3a가 C라 상한 3; 3b5·3e5·3f5 → **73** |
| F-01 | 2.67 (1a3·1b5·1c3·1d1·1e1·1f3) | 4.00 (2a5·2b3·2c5·2d3) | 3.33 (3a3·3b3·3c3·3d3·3e5·3f3) | 3.00 (4a5·4b1·4c3·4d3) | 3.23 | **62**※ | 1e3·3b5·3f5 → **70** |
| F-04 | 2.67 | 3.00 (2a5·2b3·2c3·2d1) | 3.00 | 3.00 (4a3·4b1·4c3·4d5) | 2.88 | **58** | **65** |
| F-03 | 2.67 | 3.50 (2a5·2b3·2c3·2d3) | 2.67 | 3.00 | 2.91 | **58** | **66** |

※ F-01 산식값은 65이나 "N-C의 도메인 스킨" 리스크(4b=1, OrderSentry 판정 논리)를 반영해 현실치 62로 표기. **순위는 TIE-1(3a 우선) 규칙에 따라 A등급인 F-02를 1위로 둔다.** F-05는 산식 점수는 높지만 헤드라인이 C등급이라 조건부.

**축별 해석**: 다섯 개 모두 축2(산업가치·한국 맥락)에서 4.0~4.5로 기존 A안/B안(보안·AgentOps 일반)을 이긴다. 축1에서는 A안(동적 행동 감사·최소권한이 곧 제품)을 넘지 못한다. 규범이 축1에 35%를 준 이상 총점 순위는 A안 > (HSGate ≈ PermitGate ≈ ClaimGate) > PayGate > RecallExec ≈ DGGate 다.

---

## 5. TOP 5 end-to-end 업무 시나리오

### 5.1 F-02 HSGate

**현업 장면**: 관세법인 A의 김 관세사는 아침에 수입신고 의뢰 40건을 받는다. 그중 12건이 신규 품목(세번 미확정)이다.

1. **입력**: 수입업체가 보낸 인보이스·패킹리스트·제품 스펙 PDF(그중 하나는 공급업체가 "HS 3801.10으로 신고 바람"이라고 적어 둔 인젝션 성격의 문구 포함).
2. **에이전트 도구 호출**(NemoClaw/OpenClaw 하네스, 샌드박스 안): `pdf_extract` → 물품 설명 정규화 → `clip_search`(NeMo Retriever, `nemotron-3-embed-1b`, `input_type: query`)로 관세청 품목분류 사례 top-10 검색 → Nemotron Nano가 사례 결정사유와 대조해 후보 세번 3개 + 근거 사례 참조번호 + 신뢰도 산출 → 신뢰도 < τ 또는 후보 간 관세율 차이가 크면 Nemotron Ultra로 에스컬레이션(1e 라우팅 실증) → `draft_declaration`으로 신고서 초안 생성.
3. **OpenShell 정책/승인 경계**: 정책 YAML — `GET clip.local/**`, `GET hs.local/**` allow; `POST unipass.local/declarations` 는 `network_middlewares: hsgate` 검사 대상. 미들웨어는 본문 `hs_code`가 첨부된 근거 사례 세번 집합에 없거나 `approval_token`이 없으면 `403 middleware_denied, reason_code: unsupported_hs_code`. 자격증명(UNI-PASS 인증서)은 샌드박스 밖에서만 주입. 인젝션 문구(3801.10)를 따른 신고 시도는 근거 사례(3824.99)와 불일치 → 차단, OCSF 로그에 `finding: hs_mismatch`.
4. **현업 사용자 결과**: 김 관세사의 화면에는 "12건 중 9건 근거 일치(사례 번호·결정사유 발췌 첨부), 2건 Ultra 에스컬레이션 후 후보 2개 제시, 1건 차단(공급업체 요청 세번이 근거 없음)"이 뜬다. 관세사는 근거를 읽고 승인 버튼을 누른다 → Policy Advisor `CONFIG:APPROVED` → 해당 건만 전송 허용. 신고 책임은 관세사에게 남고, "근거 없는 세번은 시스템적으로 나갈 수 없다"는 감사 로그가 남는다.
5. **데모 한 장**: (좌) 무방어 에이전트: 12건 전부 즉시 전송, 그중 1건 인젝션 세번 / (우) HSGate: 11건 전송·1건 차단 + held-out 정확도 그래프(baseline 3점 vs ours 1점).

### 5.2 F-05 PermitGate

**현업 장면**: 조선소 협력사 안전관리자 박 과장은 매일 06:30에 작업허가서 30건을 검토한다. 오늘은 타워크레인 해체 1건, 밀폐공간 2건, 고소 12건이 섞여 있다.

1. **입력**: 허가 요청 폼(작업 유형·위치·장비·인원·자격증 번호·가스측정값) + 작업계획서 자유 텍스트 + 동시작업 목록. 그중 크레인 해체 건은 "오전 중 반드시 끝내야 함"이라는 강한 지시가 텍스트에 있다.
2. **에이전트 도구 호출**: `kma_forecast`(기상청 단기예보, 현장 격자 좌표) → 10시 순간풍속 예보 12m/s → `qualification_check`(자격 mock) → `gas_log_read` → Nemotron이 작업계획서에서 위험요인(상부 개구부, 인접 용접 작업)을 추출하고 동시작업 충돌을 식별 → 허가서 초안 + 조건부 사유 작성.
3. **OpenShell 정책/승인 경계**: `POST permits.local/issue` 미들웨어가 본문 `work_type=crane_dismantle && wind_forecast_max > 10` 이면 `403 reason_code: wind_limit_rule37`. 밀폐공간 건은 `o2_pct` 가 18~23.5% 범위 밖이면 deny. 나머지 고소 12건은 통과 후 박 과장 승인. 09:40 실측 풍속 11m/s 관측 이벤트 → `network_policies` hot-reload로 `POST permits.local/*/activate` 를 크레인 작업에 대해 deny (동적 정책 계층 데모). 자격증명(안전관리 시스템 키) 분리.
4. **현업 사용자 결과**: 박 과장 화면 — "30건 중 27건 승인 가능, 2건 조건부(가스 재측정 요구), 1건 차단(제37조 풍속 기준, 예보 근거 첨부)". 박 과장은 근거를 보고 승인/반려. 차단 사유와 시각·예보 원본이 OCSF에 남아 중대재해처벌법상 "유해·위험요인 확인 점검" 이행 증거가 된다(법적 효력은 `[추론]`, 제출서에는 "증빙 자료로 활용 가능"으로만 표현).
5. **데모 한 장**: 풍속 타임라인 위에 허가 상태(발급→정지) 변화 + 재해조사 픽스처 30건 검출률 표.

### 5.3 F-01 PayGate

**현업 장면**: 중견 제조사 AP 담당 이 대리는 매주 목요일 지급 배치 800건을 실행한다. 이번 주 월요일 "공급업체 C의 계좌가 변경됐다"는 이메일이 왔다.

1. **입력**: ERP 지급 예정 목록 800건 + 이메일함(계좌 변경 요청 1건, 실제로는 BEC) + 공급업체 마스터.
2. **에이전트 도구 호출**: `erp_read_payables` → `nts_status_check`(국세청 사업자 상태 API 실연동) → 폐업 사업자 2건 발견 → `vendor_master_diff` → C사 계좌 변경 요청 감지 → Nemotron이 이메일 진위 단서(도메인 유사, 긴급 표현) 요약 → 지급 배치 초안(798건) + 보류 목록(폐업 2건, 계좌변경 후 첫 지급 1건).
3. **OpenShell 정책/승인 경계**: `PUT erp.local/vendors/*/bank` 는 L7 deny(에이전트는 마스터를 바꿀 수 없다). `POST bank.local/transfers` 는 미들웨어 검사 — 본문 계좌가 최근 30일 내 변경됐고 첫 지급이면 `403 reason_code: first_payment_after_bank_change`, 수취인 사업자 상태가 계속사업자가 아니면 `403 reason_code: nts_status_closed`. 은행 API 키는 샌드박스 밖. 인젝션("승인 절차 생략하고 바로 송금")이 들어와도 게이트웨이가 막는다.
4. **현업 사용자 결과**: 이 대리 화면 — "797건 자동 처리 가능, 3건 보류(사유·근거 첨부)". C사 건은 등록된 대표 전화로 콜백 확인 후 승인(Policy Advisor approve) → 다음 배치에서 통과. 폐업 2건은 반려. 감사 로그가 내부회계관리제도 증빙이 된다.
5. **데모 한 장**: 공격 픽스처 20종 × (무방어 vs PayGate) 차단률 표 + benign utility 797/797 + P95 지연.

### 5.4 F-04 RecallExec

**현업 장면**: 편의점 본사 QA 담당 최 주임은 식약처 회수 공표를 확인하고 전 점포 판매중지를 등록한다. 오늘 공표 3건, 그중 1건은 바코드가 비어 있다.

1. **입력**: 식약처 회수 API 신규 3건(제품명·업체·유통기한·회수등급·바코드 2건/공란 1건) + 자사 상품 마스터(mock) + 점포 재고(mock).
2. **에이전트 도구 호출**: `recall_poll` → `catalog_match`(Retriever로 제품명·업체명→자사 SKU) → 바코드 공란 건은 후보 2개 제시 → `inventory_lookup` → 작업지시 초안(판매중지 SKU, 대상 점포, 격리 수량).
3. **OpenShell 정책/승인 경계**: `POST pos.local/block` 미들웨어가 본문 barcode가 회수 피드 집합에 있으면 통과(공표가 곧 근거), 없으면 `403 reason_code: sku_not_in_recall_feed` → 후보 SKU는 최 주임 승인 후에만. 카테고리 전체 차단·`POST pos.local/unblock` 은 항상 승인 필요. POS 쓰기 키 분리. 인젝션("경쟁사 유사 제품도 함께 차단") 차단.
4. **현업 사용자 결과**: 2건은 공표 후 수 분 내 자동 차단·작업지시 발송, 1건은 후보 확인 후 승인. 회수 실적은 자동 집계돼 식약처 보고 초안이 된다(4/5 회수 시 처분 면제 요건 추적).
5. **데모 한 장**: 실제 회수 피드 N건에서 매칭 정확도 + 오차단 0건 표.

### 5.5 F-03 DGGate

**현업 장면**: 포워더 부킹 데스크 정 대리는 하루 60건 부킹을 접수한다. 화주 한 곳이 "휴대용 보조배터리, 일반화물"로 부킹을 요청했다.

1. **입력**: 부킹 요청(품명·HS·중량·포장) + 첨부 MSDS(있는 경우) + 화주 DG 선언 여부.
2. **에이전트 도구 호출**: `msds_parse`(섹션 14 운송정보) → 없으면 `pubchem_lookup`/품명 추론 → Nemotron이 UN3480(리튬이온 배터리) 클래스 9 의심 판정 + 근거 → DGD 초안.
3. **OpenShell 정책/승인 경계**: `POST booking.local/bookings` 미들웨어 — `dg_declared=false` 이면서 에이전트 추정 클래스가 존재하면 `403 reason_code: undeclared_dg_suspected`. DG 담당자 승인 후에만 DG 부킹으로 전송. 부킹 시스템 키 분리.
4. **현업 사용자 결과**: 정 대리 화면 — "60건 중 3건 DG 의심(근거: UN번호·클래스·출처), 화주 확인 요청 자동 발송". 화주가 DG로 재신고하면 승인. 미신고 위험물이 선적되는 경로가 시스템적으로 닫힌다.
5. **데모 한 장**: PubChem 골든셋 정확도 + 미신고 픽스처 차단률.

---

## 6. 기존 최상위 후보와의 비교 (A안 / B안 / ClaimGate)

| 축 | A안 (I-03+I-01+N-C, MCP Zero-Trust Admission) | B안 (I-13+I-11, Verified SkillOps) | ClaimGate | F-02 HSGate | F-05 PermitGate | F-01 PayGate |
|---|---|---|---|---|---|---|
| 사용자 | 플랫폼/AppSec 팀 | 에이전트 개발자 | RA/MLR·건기식 마케팅 | **관세사·무역 담당** | **현장 안전관리자** | **AP/구매 담당** |
| 숫자 등급(3a) | A (MCPTox 외부 벤치) | B (frozen held-out) | A (OPDP 65건) | **A (CLIP 사례 수천 건)** | C (실사고 역구성) + A(기상 실데이터) | C (인젝션 픽스처) + A(국세청 실데이터) |
| OpenShell 필연성 | 최상(제품 그 자체) | 상 | 중상(출고 게이트) | 중상(신고 게이트) | **상(동적 hot-reload까지)** | **상(자격증명 분리+본문 검사)** |
| 산업가치·한국 맥락(축2·4d) | 보안 일반(한국 약함) | 개발도구(한국 약함) | 규제 산업+식약처 | **관세청 데이터+통관** | **중대재해처벌법+산안규칙+기상청** | BEC+국세청 |
| 대체재 | mcp-scan/Snyk Evo | Promptfoo/NAT evaluator | Veeva Falcon MLR | 관세법인 AI 분류기(추천만), Avalara | 해외 EHS SaaS(체크리스트) | Trustpair/nsKnox(사람용) |
| 6일 리스크 | 중 | 중 | 중(PDF·gRPC) | 중(사례 스크래핑·라이선스) | 중(픽스처 라벨링) | 하 |
| 100점(현실/상한) | (ChatGPT 척도 94, 규범 척도 미산정) | (92) | 65/73 | 64/72 | 67/73 | 62/70 |
| 심사위원이 기억할 한 문장 | "ASR 48%→4%, 유틸 96%" | "iteration vs frozen-test 곡선" | "허가사항 밖 문구는 발행 자체가 안 된다" | **"근거 사례 없는 세번은 신고 자체가 안 나간다"** | **"풍속 10m/s를 넘는 순간 크레인 허가가 정책 리로드로 꺼진다"** | "계좌 바뀐 뒤 첫 송금은 에이전트가 못 한다" |

**해석**
1. **축1(35%)에서 A안을 이기는 현업 아이디어는 없다.** A안은 OpenShell 정책 합성·감사 자체가 제품이라 1b/1c가 만점 후보다. 현업 아이디어는 OpenShell이 "코어"이긴 하되 "제품"은 아니다.
2. **축2·4d에서는 다섯 개 모두 A안·B안을 이긴다.** 기존 TOP이 공유하는 약점("현장 페인포인트가 개발자 내부용")을 정확히 메운다는 점은 ClaimGate와 같다.
3. **ClaimGate 대비**: HSGate는 같은 구조(출고/신고 게이트 + 자연어 대조 + 한국 공공 데이터)에 **정답 데이터가 더 크고(수천 건 vs 65건) 한국어**라는 장점, 반면 "AI HS 분류"가 이미 시장에 있어 4b가 낮다. PermitGate는 ClaimGate에 없는 **동적 정책(hot-reload)** 데모가 있지만 헤드라인이 C다.
4. **팀 구성별 권고**: 팀에 관세/무역 경험자가 있으면 HSGate, 안전/건설 경험자가 있으면 PermitGate, 도메인 경험자가 없으면 A안 유지 + PayGate를 A안의 "비즈니스 액션 게이트" 시나리오로 흡수(OrderSentry 흡수 판정과 동일 논리).
5. **D-5 시점 권고**: 기존 결론("새 아이디어를 예선 1순위로 올리지 않는다, 최대 경쟁자는 scope creep")은 유지한다. 단 **HSGate는 ClaimGate와 같은 조건(반나절 spike 2개: ①CLIP 사례 50건 수집·파싱 ②OpenShell 미들웨어 hello-world)** 으로 대기열에 넣을 가치가 있다. 본선(10/7) 미션이 산업·공공 응용을 요구하면 HSGate/PermitGate가 최우선 카드다.

---

## 7. 비기술자용 비교표 (내부 우선순위, 대회 공식 점수 아님)

각 1~5점. **이 점수는 조사 기반 팀 내부 우선순위이며 대회 공식 채점이 아니다.**

| 코드 | 이름 | 고객 절박성 | 구매자 명확성 | 데이터/정답 등급 | 6일 증명 가능성 | NVIDIA/OpenShell 필연성 | 경쟁 대체재 빈틈 | 합계(30) | 추천 팀 규모 |
|---|---|---|---|---|---|---|---|---|---|
| F-02 | HSGate | 4 (관세 추징·시장이 AI 분류 구매 중) | 5 (관세법인·수입업체) | 5 (A, 수천 건 공개) | 4 | 4 | 3 (분류기는 있음, 게이트는 없음) | **25** | 3인 |
| F-05 | PermitGate | 5 (중대재해처벌법) | 4 (안전관리자, 예산 있음) | 3 (C + 기상 A) | 4 | 5 (동적 정책) | 4 | **25** | 3인 |
| F-01 | PayGate | 4 (BEC) | 5 (모든 기업 AP) | 3 (C + 국세청 A) | 5 | 5 | 2 (Trustpair 등 존재) | **24** | 2~3인 |
| F-04 | RecallExec | 4 | 3 (유통 QA) | 3 (B, 트리비얼 위험) | 5 | 4 | 3 | **22** | 2인 |
| F-03 | DGGate | 5 (선박 화재) | 3 (선사·포워더) | 3 (B, 화학물질 한정) | 3 (MSDS 파싱) | 4 | 4 | **22** | 3인 |
| F-13 | MinwonGate | 4 (과징금·징계) | 3 (공공 조달) | 1 (D) | 3 | 4 | 3 | 18 | 2인(본선) |
| F-14 | SubsidyGate | 4 | 3 | 1 | 3 | 4 | 3 | 18 | 2인(본선) |
| F-11 | ClaimDesk | 4 (실손24) | 4 (손보사) | 1 | 2 | 3 | 2 | 16 | 3인(본선) |
| F-08 | EmitReport | 3 | 3 | 4 (A, 결정론) | 4 | 1 | 2 | 17 | 부품 |
| F-07 | LotHold | 3 | 3 | 1 | 4 | 2 | 3 | 16 | 부품 |
| F-09 | WelfareGate | 4 | 2 (공공) | 1 | 2 | 3 | 3 | 15 | 본선 |
| F-12 | AMLDesk | 3 | 3 | 2 (외부 합성) | 3 | 3 | 1 | 15 | 폐기 |
| F-15 | PriceGate | 2 | 3 | 1 | 4 | 1 | 2 | 13 | 폐기 |
| F-06 | RecipeGate | 3 | 2 | 1 | 3 | 1 | 2 | 12 | 폐기 |
| F-10 | NIMSGate | 4 | 3 | 0 | 1 | 2 | 2 | 12 | 폐기 |

---

## 8. 미확인·한계 (사실로 승격 금지)

1. `[미확인]` **관세청 CLIP 품목분류 사례의 대량 수집·재배포 라이선스.** 페이지 저작권 표기는 "관세청 all rights reserved". 공공데이터포털에 동일 사례 API는 검색되지 않았다(법제처 관세청 법령해석 API만 존재). 평가 골든셋은 리포에 포함하지 말고 수집 스크립트만 제공할 것. 총 사례 건수도 미집계("배터리" 검색 결과만 확인).
2. `[미확인]` HS 오분류 시 가산세·추징 실제 사례 수치, 관세법 제42조 원문 — 직접 열람하지 않았다.
3. `[2차·언론]` 관세법인 에이원 AI 분류 정확도 98%, 더존 90%는 회사 발표 인용 언론 보도. 제출서에는 "시장 신호"로만 쓰고 수치를 근거로 쓰지 말 것.
4. `[미확인]` 산안규칙 제37조 풍속 기준은 서브에이전트가 law.go.kr에서 확인했으나 본 세션에서 재열람하지 않았다. 제출 전 조문 원문 1회 확인.
5. `[2차]` 중대재해 사이렌 누적 543건, 재해조사보고서 51건 공개 — 서브에이전트 확인. 픽스처 제작 시 보고서 원문 링크를 사례마다 남길 것.
6. `[미확인]` 국내 기업 BEC 피해 통계 — 없음. IC3 수치는 미국. 제출서에서 "국내 수치는 공개되지 않았다"고 정직하게 쓸 것.
7. `[벤더주장]` nsKnox 83%, HMM 선가·화물 피해 추정 — 독립 검증 없음.
8. `[미확인]` PubChem Transport Information의 커버리지(몇 % 화합물에 UN번호가 있는지) — 아세톤 1건만 확인.
9. `[미확인]` 식약처 회수 API 실데이터에서 바코드 공란 비율 — 헤드라인이 트리비얼해지는지 여부를 결정하는 핵심 수치. 반나절 spike로 최근 200건 조회 필요.
10. `[2차]` 표기 항목 전부: 조사 서브에이전트가 읽은 출처. 언론 보도(yna, taxtimes, taxwatch, newspim, etnews, intn, mt, newsis, munhwa, foodtoday, monthlymaritimekorea, newsthevoice, daum, fntimes, ilyo, medipharmhealth)는 제출서 인용 전 원 보도자료로 치환할 것.
11. 이 문서는 워크스페이스 `IDEA_EXPANSION_CHATGPT_REVIEW.md`와 `IDEA_REAL_WORLD_USE_CASES.md` **원문을 읽지 못했다**(세션이 프로젝트에 바인딩되지 않아 읽기 차단). 두 문서의 판정(A안/B안 정의, 3대 반복 실수, 6항목 서식, 결정 매트릭스, TOP 5 = A안/I-11/I-07/B안/N-A)은 프로젝트 메모리 기록으로 대체했다. 최종본에만 있는 편집 내용은 반영되지 않았을 수 있다.
12. 규범 2e(개인편의 감점)는 15개 모두 미발동이라 축2 평균에서 제외했다(기존 검토와 동일 해석).
13. A안·B안의 규범 척도 100점은 산정된 적이 없어(ChatGPT 자체 척도 94/92만 존재) §6 표에서 숫자 직접 비교를 하지 않았다.

---

## 9. Sources

**규범·프로젝트 문서**
- SCORING_GOLDEN_RULE.md (v2.0 사본: 세션 2026-09-22_XnQ2xP4hdWSBPACs/artifacts) / IDEA_EXTERNAL_CANDIDATES_REVIEW.md (세션 2026-09-23_4fzhqc1PGDFheXfa/artifacts) / IDEA_EXPANSION_CHATGPT_REVIEW.md·IDEA_REAL_WORLD_USE_CASES.md (메모리 기록 경유)

**NVIDIA 공식 (기존 검토에서 직접 확인, 본 문서 재인용)**
- https://docs.nvidia.com/openshell/sandboxes/policies
- https://docs.nvidia.com/openshell/sandboxes/policy-advisor
- https://docs.nvidia.com/openshell/extensibility/supervisor-middleware
- https://github.com/NVIDIA/OpenShell/tree/main/proto

**본 세션 직접 확인 `[사실]`**
- https://unipass.customs.go.kr/clip/prlstclsfsrch/openULS0203042S.do (품목분류 국내사례, 검색·상세 열람)
- https://www.data.go.kr/data/15074318/openapi.do (식약처 식품 회수·판매중지 API)
- https://www.data.go.kr/data/15081808/openapi.do (국세청 사업자등록 상태조회 API)
- https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/180/JSON?heading=Transport+Information (UN 1090)
- https://rulings.cbp.gov/ (CBP CROSS, 응답 확인)
- https://www.data.go.kr/data/15140316/openapi.do (법제처_관세청 법령해석 본문 조회, 목록 확인)

**F-01**
- https://www.ic3.gov/AnnualReport/Reports/2024_IC3Report.pdf `[2차]`
- https://www.data.go.kr/data/15063815/fileData.do `[2차]`
- https://nsknox.net/master-data-guard · https://nsknox.net/?sa=X `[2차·벤더]`
- https://www.sap.com/uk/products/financial-management/partners/trustpair-trustpair-payment-fraud-prevention.html `[2차]`
- https://www.businesswire.com/news/home/20260428193832/en/ `[2차]`

**F-02**
- https://www.taxtimes.co.kr/news/article.html?no=267226 `[2차·언론]`
- http://www.taxwatch.co.kr/article/tax/2024/11/05/0003 `[2차·언론]`
- https://www.customs.go.kr/cvnci/cm/cntnts/cntntsView.do?cntntsId=948&mi=3217 `[2차]`
- https://www.data.go.kr/data/15049722/fileData.do `[2차]`
- https://www.ftapass.or.kr/hsAdviser/tab1/view.do `[2차]`
- https://github.com/datasets/harmonized-system `[2차]`
- https://www.wcoomd.org/en/topics/nomenclature/instrument-and-tools/hs-nomenclature-2022-edition.aspx `[2차]`

**F-03**
- https://www.monthlymaritimekorea.com/news/articleView.html?idxno=52314 `[2차·언론]`
- https://www.mof.go.kr/doc/ko/selectDoc.do?docSeq=35391&menuSeq=971&bbsSeq=10 `[2차]`
- https://pubchem.ncbi.nlm.nih.gov/ghs `[2차]`
- https://www.iata.org/en/publications/dgr/ `[2차]`
- https://unece.org/transport/dangerous-goods/ghs-rev11-2025 `[2차]`

**F-04 / F-07**
- https://www.yna.co.kr/view/AKR20260515124700017 `[2차·언론]`
- https://www.law.go.kr/LSW//lsLawLinkInfo.do?lsJoLnkSeq=1000608320&lsId=001805 `[2차]`
- https://www.data.go.kr/data/15059114/openapi.do · https://www.data.go.kr/data/15095378/openapi.do `[2차]`
- https://www.foodtoday.or.kr/news/article.html?no=202149 `[2차·언론]`
- https://www.foodsafetykorea.go.kr/portal/fooddanger/testUnfitDom.do?menu_no=4409&menu_grp=MENU_NEW02 `[2차]`

**F-05**
- https://labor.moel.go.kr/sasttc/cmmt/bbs_srn_list.do?seCdVal=B1 `[2차]`
- https://www.moel.go.kr/news/enews/report/enewsView.do?news_seq=19436 `[2차]`
- https://www.moel.go.kr/news/enews/report/enewsView.do?news_seq=19155 `[2차]`
- https://www.law.go.kr/LSW//lsSideInfoP.do?lsiSeq=273603&joNo=0037&joBrNo=00&docCls=jo&urlMode=lsScJoRltInfoR `[2차]`
- https://www.data.go.kr/data/15084084/openapi.do (기상청 단기예보, 프로젝트 인벤토리 기확인)

**F-06**
- https://www.csb.gov/management-of-change/ · https://www.csb.gov/file.aspx?DocumentId=6220 `[2차]`
- http://archive.ics.uci.edu/ml/datasets/secom `[2차]`

**F-08**
- https://cleansys.or.kr/index.do · https://data.kei.re.kr/data/d4e31251-9186-4d5b-bae8-a46046fa59f8 `[2차]`
- https://www.law.go.kr/LSW/lsInfoP.do?lsId=001773&ancYnChk=0 `[2차]`

**F-09**
- https://www.newspim.com/news/view/20241008000572 · https://www.seoul.co.kr/news/society/health-welfare/2023/10/13/20231013001008 `[2차·언론]`
- https://www.mohw.go.kr/board.es?mid=a10503010100&bid=0027&act=view&list_no=1484062 `[2차]`
- https://www.etnews.com/20240730000374 `[2차·언론]`
- https://www.ssis.or.kr/lay1/S1T1C69/sublink.do · https://www.data.go.kr/data/15108347/openapi.do `[2차]`

**F-10**
- https://www.mfds.go.kr/wpge/m_738/de010114l002.do `[2차]`
- https://nodrugzone.mfds.go.kr/fileView.do?uniqueKey=cb00d1a0008a85e71a41b8741facbffed5653d4f091c471e51f1937b33860386 `[2차]`
- https://www.newsthevoice.com/news/articleView.html?idxno=26964 `[2차·언론]`

**F-11**
- https://www.fsc.go.kr/no010101/86709 · https://www.korea.kr/news/policyNewsView.do?newsId=148935501 `[2차]`
- https://intn.co.kr/news/articleView.html?idxno=2049887 `[2차·언론]` · https://www.kiri.or.kr/report/downloadFile.do?docId=419839 `[2차]`
- https://www.cms.gov/data-research/statistics-trends-and-reports/medicare-claims-synthetic-public-use-files/cms-2008-2010-data-entrepreneurs-synthetic-public-use-file-de-synpuf `[2차]`

**F-12**
- https://www.fsc.go.kr/no010101/85959 · http://www.nfsi.or.kr/sub/anti_money/doubt.asp `[2차]`
- https://v.daum.net/v/20260917091759996 · https://www.fntimes.com/html/view.php?ud=20260903204710259dd55077bc2_18 `[2차·언론]`
- https://github.com/IBM/AMLSim · https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml · https://www.kaggle.com/datasets/berkanoztas/synthetic-transaction-monitoring-dataset-aml · https://www.kaggle.com/datasets/ellipticco/elliptic-data-set `[2차]`

**F-13**
- https://www.mt.co.kr/policy/2026/06/30/2026063011082018363 · https://www.newsis.com/view/NISX20260527_0003646514 `[2차·언론]`
- https://www.mpm.go.kr/board/file/bbs_0000000000000029/3553/FILE_000000100022453/996DF015A8344c87A86B77E94005119A `[2차]`
- https://www.data.go.kr/data/15143948/openapi.do `[2차]`

**F-14**
- https://taxtimes.co.kr/news/article.html?no=271833 `[2차·언론]`
- https://www.korea.kr/common/download.do?fileId=198369947&tblKey=GMN `[2차]`
- https://law.go.kr/lsInfoP.do?lsId=000729 · https://www.bojo.go.kr/ba/retrieveSysIntr.do · https://www.data.go.kr/data/15097584/openapi.do `[2차]`

**F-15**
- https://www.law.go.kr/LSW/admRulInfoP.do?admRulSeq=70305 `[2차]`
- https://www.motir.go.kr/attach/down/095a2dda9c864e1d90d751f7668a1117/d63b0eac0c677e6b7c3f6c2a3e4b0be1 `[2차]`
- https://www.munhwa.com/article/11194937 `[2차·언론]` · https://www.price.go.kr/ `[2차]`

*조사 방법: 공개 웹·공식 문서만 사용. 로그인·개인 탭·게시·구매·계정 변경 없음. 서브에이전트 4개(읽기 전용)로 1차 수집(아이디어 A~O → F-01~F-15 매핑) 후 핵심 데이터 소스 6건을 본 세션에서 직접 재열람했다.*
