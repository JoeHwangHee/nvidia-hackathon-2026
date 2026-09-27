---
title: "HSGate R5 — 비교 기준(관세청 AI 80%) · 경쟁(커스텀메이트) · 빅데이터포털 유사사례 · 품목분류 경진대회 · 관세사 기출 · 학술 벤치마크 · 외국 사례 DB"
doc_type: research-validation
version: "1.0"
created_at: 2026-09-23T19:10:00+09:00
checklist_ref: "근거자료 §1.3 비교 기준·경쟁, §3.5 포지셔닝, 체크리스트 학습순서 5·6, 설계서 §10.1 B2·§11 장면 5"
scope: "읽기 전용. 출처 등급: 공식(customs.go.kr, bigdata.customs.go.kr, q-net.or.kr) / [보도] / [벤더] / [학술]"
confidence_tags: "[사실]=직접 확인 / [추론] / [미확인] / [보도]·[벤더]·[학술]"
method: "서브에이전트(읽기 전용) 조사"
related: HSGate_근거자료_및_반영사항.md §1.3·§3.5, HSGATE_EVALUATION_DATA_REVIEW.md §2.2
---

# R5 비교 기준 · 경쟁 · 추가 테스트셋

> **한 줄 결론**: (1) "관세청 AI 정확도 80%"는 **관세청 관계자 구두 발언을 택스워치가 인용**한 것으로, 단위·지표·테스트셋이 미명시이고 공식 보도자료 원출처는 못 찾았다 → "공식 발표 수치"로 쓰면 안 된다 [사실]. (2) 커스텀메이트는 이미 "관세청 사례 근거 + 세번 존재 확인 + 관세사 최종 확정 + 유니패스 전송"을 표방한다 [벤더] → HSGate 차별점은 "공개 정보상 확인되지 않음"으로 톤다운. (3) **관세청-KAIST/GIST 공동연구(2023, 결정사례 기반 검색, 925개 고난도 소호 top-3 93.9%)가 선행연구**로 존재하므로 반드시 인용해야 한다 [학술]. (4) 추가 테스트셋으로 **품목분류 경진대회 22~26회 문제·해설 PDF**와 **관세사 1차 기출(공공누리 1유형 + AI학습용 표시)**을 바로 쓸 수 있다. (5) 체크리스트 정정: "관세율표 및 상품학"은 **1차가 아니라 2차(논술)** 과목.

---

## 1. "관세청 AI 품목분류 정확도 약 80%" 원출처 판정
- 기사 실재 [사실]: 택스워치 2025-07-30 "AI 통역사가 세관에…'관세청 버전 GPT'도 가능할까?" — APEC 2차 SCCP 부대행사 "AI 관세행정 전시회" 취재. https://www.taxwatch.co.kr/article/tax/2025/07/30/0002 [보도]
- 인용 원문: "관세청 관계자는 '현재 AI 품목분류 정확도는 80% 이상이다. 80%인 것은 수입이 적은 물품은 데이터도 적기 때문에 정확도가 떨어질 수밖에 없는 것'이라고 말했다."
- 지칭 시스템: **관세청 빅데이터포털**의 AI 품목분류 추천(품목명 입력 → 과거 5년 신고데이터 기반 품명·규격·HS코드 추천 + 해설서·과거 사례 제시). 6개월마다 재학습.
- **단위(6/10)·지표(top-1/k)·테스트셋 미명시** [사실].
- 공식 보도자료 탐색: customs.go.kr "인공지능 품목분류" 검색에서 80% 수치 담긴 자료 **없음** [미확인]. 인접 자료: 관세청 새 비전 선포(2025-09-15, https://eiec.kdi.re.kr/policy/callDownload.do?dtime=20250916151428&filenum=1&num=271080), 품목분류 기준 제시 보도(2026-08-14, https://www.korea.kr/briefing/pressReleaseView.do?newsId=156774498), AI R&D 2.0(2025-09-26, https://eiec.kdi.re.kr/policy/callDownload.do?dtime=20250929154020&filenum=1&num=271701) — 모두 정확도 수치 없음.
- **발표 문구 권고**: "관세청 관계자 구두 발언(택스워치 2025-07-30 보도), 측정 기준 비공개"로 각주. "관세청 공식 80%"로 단정 금지. 우리 지표와 직접 비교 불가(측정 방법 다름)를 명시.

## 2. 커스텀메이트 (CustomMate)
- 출시 보도 [보도]: https://wowtale.net/2026/09/21/265091/ , https://www.ceoeconomy.com/news/articleView.html?idxno=20982 (2026-09-21)
- 공식 [벤더]: https://custommate.co.kr/ (주식회사 메이트플러스)

| 항목 | 내용 | 출처 |
|---|---|---|
| 대상 | **관세사무소 전용**(관세사법·관세사회 규정에 따라 사업자정보로 자격 확인, 화주 가입 불가) | custommate.co.kr/pricing |
| 파이프라인 | 인보이스/패킹리스트/B·L/운임증명서 업로드 → 추출·교차검증 → HS코드 후보(근거 포함) → 과세가격·세액·FTA·수입요건 계산 → 수입신고서 초안 → **유니패스 전송** | 보도 |
| HS 근거 | "관세청 공개 품목분류 사례 + 관세사무소 자체 신고이력" (LLM 단독 생성 아님 강조) | 보도 |
| 세번 존재 검증 | "HS코드 사전"으로 실재 확인, 동일 호 세번 비교, 기본세율 | 보도 |
| 확정 주체 | AI 자동 확정 없음, **관세사가 최종 검토·확정** | 보도 |
| 가격 | 좌석당 월 9.9만원(VAT 별도), 월 140건 포함, 초과 건당 700원, 사무소당 30건 무료. 무료 HS 조회 https://custommate.co.kr/hs-lookup | pricing |

### HSGate 차별점 3개 대조 [추론, 공개 정보 기준]
| 차별점 | 커스텀메이트 | 판정 |
|---|---|---|
| ① 실패 유형별 자기수정 루프 | 공개 자료는 선형 파이프라인(후보→검증→관세사 확정)만 기술. 반복 재검증 언급 없음 | **미확인** (없다고 단정 금지) |
| ② 사례 유효성(변경고시·동일물품) 검증 | "사례 근거 제시"만. 시행일·개정·폐지 검증 언급 없음 | **미확인** |
| ③ 인젝션 방어 전송 게이트 | 보안 게이트 언급 없음. 단 "관세사 최종 확정"이 이미 사람 게이트 역할 | **약한 차별점** — "인젝션 fixture 차단률"이라는 기술적 측정으로만 차별 가능 |
- 전략: "사례 기반 vs 생성형" 구도는 무효(커스텀메이트도 사례 기반). ①②는 "공개된 기술 설명이 없다"로만, ③은 정량 fixture 결과로만 주장.

## 3. 관세청 빅데이터포털 유사사례 서비스 [사실]
- 국내 https://bigdata.customs.go.kr/web/anaySrvc/selectSmlrPrlstClsfCaseDmstList.do / 국외 https://bigdata.customs.go.kr/web/anaySrvc/selectSmlrPrlstClsfCaseOvrsList.do — **로그인 없이 접근 가능**.
- 소개문: "사용자 질의어와 유사도가 높은 국내·외 품목분류사례를 추천하여 제공합니다."
- 출력 컬럼(국내): 결정세번 / 분류 / 시행기관 / 참조번호 / 이미지 건수 / 품명. 리스트·카드·이미지 뷰.
- 실제 검색어 입력 결과는 미확인(초기 로드 "조회된 데이터가 없습니다") [미확인]. 알고리즘 미공개.
- 판정 [추론]: 입력(질의어)→유사 사례 리스트 = **Retriever-only 베이스라인(B2)과 동형**. 비교 대상으로 적합하나, 실사용 전 검색 결과·건수·순위 재확인 필요. 대량 자동 질의는 하지 말 것(트래픽 고시).

## 4. 품목분류 경진대회 [사실]
- https://www.customs.go.kr/cvnci/cm/cntnts/cntntsView.do?mi=10583&cntntsId=5261 — 관세평가분류원 주관, **2026년 제27회**(2026-09-16 시행, 40분, 온라인). 참가: 일반인 + 관세청 직원.
- **제22회~제26회 문제·해설 PDF 공개**: https://www.customs.go.kr/common/nttFileDownload.do?fileKey=df29b7fc28b8f4466b00ad138300277d
- 판정: **추가 테스트셋 적합**(정답 + 해설=분류 근거). 라이선스 표시 없음 [미확인] → 관세평가분류원 품목분류1과(042-714-7532) 확인 권장. 사용 시 "관세청 공개 경진대회 문제, 출처 표시"로.
- 인접 선행: 2025 관세청 공공데이터 활용 경진대회 최우수 "코드헌터스" — 관세평가분류원·분석소 직원 역할의 **멀티에이전트가 HS 후보 도출·토론** [사실, 보도자료 https://www.customs.go.kr/common/nttFileDownload.do?fileKey=fdac1cbc66e36b50f3a57c39b1af6769] → 차별성 주장 시 인지 필요.

## 5. 관세사 자격시험 기출 [사실]
- 1차: 관세법개론(FTA특례법 포함) / 무역영어 / 내국소비세법 / 회계학 — 객관식 5지선다, 과목당 40문항.
- 2차: 관세법 / **관세율표 및 상품학** / 관세평가 / 무역실무 — **논술형**, 과목당 4문제. → **체크리스트 정정: 1차 아님**.
- 기출 다운로드: https://www.q-net.or.kr/cst003.do?id=cst00309 (예: 2023 제40회 1차 https://www.q-net.or.kr/cst003.do?artlSeq=5211730&boardId=Q004&gId=24&gSite=L&id=cst00302&menuType=cst00309)
- 라이선스: 1차 문제 페이지에 **공공누리 1유형 + "공공누리 인공지능 학습용"** 표시 [사실]. 2차 페이지는 미확인.
- 시험일: 제41회 2024-03-16, 제42회 2025-03-15, 제43회 2026-03-14.
- 판정: 1차 기출은 바로 사용 가능하나 품목분류 문항은 "세율 및 품목분류" 파트(관세법개론 내 약 10%)로 제한적. 2차 "관세율표 및 상품학"은 모범답안·채점기준 필요(가답안 비공개) → 자동 채점 테스트셋으로는 부적합.

## 6. 학술 벤치마크 [학술]
| 논문 | 데이터 | 지표 | 수치 | URL |
|---|---|---|---|---|
| **Explainable Product Classification for Customs** (Lee, Kim, Kim et al., KAIST/GIST, **관세청 협업**, 2023; ACM TIST) | 관세청 결정사례(precedent) 기반, 925개 고난도 소호 | top-3 (6자리) | **93.9%** | https://arxiv.org/abs/2311.10922 , https://dl.acm.org/doi/10.1145/3635158 |
| ATLAS: Benchmarking and Adapting LLMs for Global Trade via HTS Code Classification (2025) | 미국 CBP CROSS 기반, 학습 18,731건 | 10자리 완전정답 / 6자리 | GPT-5-Thinking 25.0% / 55.5%; Atlas(LLaMA-3.3-70B FT) 40.0% / 57.5% | https://arxiv.org/html/2509.18400 |
| HS code classification using supervised contrastive learning with Sentence-BERT + MNRL | 무역 거래 텍스트 | 정확도 | 본문 유료 [미확인] | https://www.emerald.com/dta/article/59/2/276/1246547 |
| A Deterministic Agentic Workflow for HS Tariff Classification (2026) | 중국 HS 실서비스 | 에이전트 워크플로우 vs 프롬프팅 | 선행연구 정리 중심 | https://arxiv.org/html/2605.14857v1 |
- **핵심**: "관세청 결정사례를 검색 근거로 쓰는 접근"은 관세청+KAIST/GIST가 2023년에 이미 수행(Sentence-BERT + 지도 대조학습 + MNRL). HSGate는 이를 **선행연구로 인용**하고 차이(자기수정 루프·사례 유효성·전송 게이트·**학습 없음**)를 명시해야 한다. "관세청 사례 RAG는 우리가 처음" 류 주장 금지.
- 수치 비교 주의 [추론]: Lee et al.의 93.9%는 top-3·6자리·925개 소호 집합·대조학습 fine-tune 결과. HSGate는 학습 없음·2026 held-out이라 **직접 비교 불가**, "다른 세팅" 명시.

## 7. 외국 사례 DB (향후 확장)
| DB | URL | 접근·라이선스 |
|---|---|---|
| 미국 CBP CROSS | https://rulings.cbp.gov/ | 무료, 1989~현재 221,854건(2026-09-22), Bulk CSV/ZIP. 미국 정부 저작물 → 자유이용 https://www.usa.gov/government-works [사실]; data.gov 등록 https://catalog.data.gov/dataset/cbp-customs-rulings-online-search-system-cross |
| EU EBTI | https://ec.europa.eu/taxation_customs/dds2/ebti/ebti_home.jsp (안내 https://taxation-customs.ec.europa.eu/customs/common-customs-tariff-cct/tariff-classification-goods/european-binding-tariff-information-ebti_en) | 공개 열람 무료. 라이선스 [미확인] |
- CLIP 외국사례 탭(미국·EU·일본·중국 등)과 자료실 일괄파일(135건)도 HSGATE_DATA_VALIDITY.md §2.1에서 확인됨.

## 8. 미확인·리스크
- [미확인] 80% 수치의 공식 원출처·측정 정의.
- [미확인] 커스텀메이트 내부 구현(①②③ 여부).
- [미확인] 빅데이터포털 실제 검색 결과·랭킹 로직.
- [미확인] 경진대회 문제 재사용 라이선스; 2차 기출 라이선스.
- [미확인] EU EBTI 라이선스.

## 9. Sources
- https://www.taxwatch.co.kr/article/tax/2025/07/30/0002 [보도]
- https://eiec.kdi.re.kr/policy/callDownload.do?dtime=20250916151428&filenum=1&num=271080
- https://www.korea.kr/briefing/pressReleaseView.do?newsId=156774498
- https://eiec.kdi.re.kr/policy/callDownload.do?dtime=20250929154020&filenum=1&num=271701
- https://wowtale.net/2026/09/21/265091/ [보도] · https://www.ceoeconomy.com/news/articleView.html?idxno=20982 [보도]
- https://custommate.co.kr/ · https://custommate.co.kr/pricing · https://custommate.co.kr/hs-lookup [벤더]
- https://bigdata.customs.go.kr/web/anaySrvc/selectSmlrPrlstClsfCaseDmstList.do · https://bigdata.customs.go.kr/web/anaySrvc/selectSmlrPrlstClsfCaseOvrsList.do
- https://www.customs.go.kr/cvnci/cm/cntnts/cntntsView.do?mi=10583&cntntsId=5261 · https://www.customs.go.kr/common/nttFileDownload.do?fileKey=df29b7fc28b8f4466b00ad138300277d · https://www.customs.go.kr/common/nttFileDownload.do?fileKey=fdac1cbc66e36b50f3a57c39b1af6769
- https://www.q-net.or.kr/site/customs · https://www.q-net.or.kr/cst003.do?id=cst00309 · https://www.q-net.or.kr/cst003.do?artlSeq=5211730&boardId=Q004&gId=24&gSite=L&id=cst00302&menuType=cst00309 · https://www.q-net.or.kr/crf005.do?id=crf00503&gSite=L&gId=24
- http://www.lec.co.kr/news/articleView.html?idxno=745159 · https://www.lec.co.kr/news/articleView.html?idxno=749040 [보도]
- https://arxiv.org/abs/2311.10922 · https://dl.acm.org/doi/10.1145/3635158 · https://arxiv.org/html/2509.18400 · https://www.emerald.com/dta/article/59/2/276/1246547 · https://arxiv.org/html/2605.14857v1 [학술]
- https://rulings.cbp.gov/ · https://catalog.data.gov/dataset/cbp-customs-rulings-online-search-system-cross · https://www.usa.gov/government-works
- https://taxation-customs.ec.europa.eu/customs/common-customs-tariff-cct/tariff-classification-goods/european-binding-tariff-information-ebti_en · https://ec.europa.eu/taxation_customs/dds2/ebti/ebti_home.jsp
