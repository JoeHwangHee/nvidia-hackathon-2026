---
title: "DATA & SKILL INVENTORY — 6일 내 사용 가능한 자원 재고"
doc_type: resource_inventory
version: 1.1
created_at: 2026-09-22
revised_at: 2026-09-23T00:20+09:00  # v3 정정: 법령 API 승인 1~2일, Personas-Korea 1M×7, AgentDojo/MCPTox/NVD/지진대피소 추가
deadline: 2026-09-28T23:59+09:00
purpose: 아이디어 도출용 원재료. 데이터 소스 × NVIDIA Agent Skills 조합 가능성 매핑
companion_docs:
  - SCORING_GOLDEN_RULE.md
  - IDEA_CANDIDATES.md
  - IDEA_EXPANSION_CHATGPT_REVIEW.md
---

# DATA & SKILL INVENTORY

> **READ THIS FIRST (for agents)**
> 이 문서는 **아이디어를 만들기 위한 재고 목록**이다. 여기 없는 자원을 가정하지 말 것.
> 모든 항목에 **6일 제약 하 사용 가능 여부**가 표시되어 있다. ❌ 표시된 것은 이번 대회에서 쓰지 않는다.
> "확인 불가"는 그대로 유지하고 추정으로 채우지 말 것.

---

## PART 1. "Skill API"의 실체 정리

대회 공지의 *"build.nvidia.com 통해 Skill API 활용"* 은 **NVIDIA 공식 제품명이 아니다.**
build.nvidia.com 전 메뉴, docs.nvidia.com/skills, docs.api.nvidia.com, llms.txt를 전수 확인한 결과 실체는 **두 가지**다.

| | 실체 | 성격 | 접근 |
|---|---|---|---|
| **Agent Skills** | SKILL.md 형태의 이식 가능한 지침 패키지 | **REST API 아님.** CLI 설치 | `npx skills add NVIDIA/skills --skill <name>` |
| **NIM Inference API** | OpenAI 호환 추론 API | 실제 HTTP API | `https://integrate.api.nvidia.com/v1` |

공식 정의:
> "Agent skills are **portable instruction sets** that extend what an AI agent can do."
> — https://docs.nvidia.com/skills.md

**→ 결론: 둘 다 쓴다.** 제출서에 사용한 스킬명을 명시 나열 + NIM 모델명/엔드포인트를 함께 적는다.

### 설치 명령
```bash
npx skills add NVIDIA/skills                                    # 전체
npx skills add NVIDIA/skills --skill <name>                     # 개별
npx skills add NVIDIA/skills --skill <name> --agent claude-code
npx skills add NVIDIA/skills --skill <name> --agent codex
npx skills add NVIDIA/OpenShell                                 # OpenShell 전용(별도 리포)
npx skills update | list | check
```
- `skills` CLI **v1.5.16 이상** 필요. Claude Code에서는 `/reload-skills`
- 리포: https://github.com/NVIDIA/skills (Apache-2.0 + CC-BY-4.0)

### ⚠️ 실측 주의
- 웹 UI는 **366 skills**라고 표시하지만, `build.nvidia.com/skills.md`는 **알파벳 e까지만 잘려 있다**(100개 중복 포함)
- GitHub 트리 실측 결과 **SKILL.md 파일 363개**가 정확한 수치
- 이 중 **120개가 DOCA(네트워킹)** 계열로 이번 대회와 무관 → **실질 후보는 약 240개**
- 전수 목록 확보 방법: `https://api.github.com/repos/NVIDIA/skills/git/trees/main?recursive=1`

---

## PART 2. 해커톤에 쓸 만한 Agent Skills (실측 363개 중 선별)

### 2-1. ⭐ 교육 미션 직결 (G2 게이트 대응)

| 스킬 | 설명 | 왜 중요한가 |
|---|---|---|
| **`nemotron-policy-generator`** | Nemotron content-safety 가드레일용 **BYO 커스텀 안전 정책 생성**. Markdown 정책 + JSON 택소노미 + 드롭인 추론 프롬프트 산출 | **정책을 산출물로 만드는 유일한 스킬.** 축1-1b(OpenShell 정책 깊이)와 축4-4a(NVIDIA 자산 확장)를 동시에 충족 |
| **`nemoclaw-user-guide`** | NemoClaw docs MCP 서버 + Fern 문서로 에이전트를 안내 | NemoClaw 운용 근거 |
| `npx skills add NVIDIA/OpenShell` | OpenShell 전용 스킬 (별도 리포) | 샌드박스/정책 |

### 2-2. ⭐ 정량 평가 내장 (G1 게이트 대응) — **가장 중요한 그룹**

| 스킬 | 설명 | 뽑을 수 있는 숫자 |
|---|---|---|
| **`rag-eval`** | 코퍼스/train.json/evaluate_rag.py 기반 **RAGAS 품질 스코어링** | 정답률, faithfulness, context recall |
| **`rag-perf`** | 배포된 RAG Blueprint 서버에 **프로파일링 + aiperf 부하 테스트** (YAML 1개로 구동) | throughput, p50/p99 latency |
| **`deepstream-profile-pipeline`** | Nsight Systems로 파이프라인 프로파일 후 설정 역산 | **FPS 측정값** |
| **`jetson-llm-benchmark`** | Jetson LLM 벤치마크 | tok/s |
| **`digital-health-clinical-asr-eval`** | NeMo manifest 채점 → **5섹션 KER 리더보드** 산출 | KER(키워드 오류율) |
| **`nemo-relay-plugin-observability`** | ATOF 이벤트 / ATIF 트래젝토리 / OpenTelemetry / OpenInference | 툴콜 트레이스 전량 |
| **`nemo-relay-instrument-calls`** | 툴/LLM 호출 지점을 Relay 스코프로 래핑 | 호출 단위 계측 |

### 2-3. 최적화 · 수치 계산 (산업가치 축 강함)

| 스킬 | 설명 |
|---|---|
| **`cuopt-routing-api-python`** | **VRP / TSP / PDP** 차량 경로 최적화 (Python) |
| `cuopt-server-api-python` | cuOpt REST 서버 + curl/Python 클라이언트 |
| `cuopt-numerical-optimization-api` | **LP / MILP / QP** |
| `cuopt-multi-objective-exploration` | **파레토 프론티어** 추적 (가중합 + ε-제약) |
| `cuopt-numerical-optimization-formulation` | 문제 텍스트 → 제약/결정변수/목적함수 파싱 |
| **`portfolio-optimization`** | Mean-CVaR, Mean-Variance/SOCP, 효율적 프론티어, 백테스트, cuOpt 연계 |

> 💡 `cuopt-numerical-optimization-formulation`은 **자연어 문제를 최적화 모델로 변환**하는 스킬이다. "에이전트가 제약조건을 스스로 추출한다"는 서사의 핵심 부품이 된다.

### 2-4. 검색 · RAG

| 스킬 | 설명 |
|---|---|
| **`nemo-retriever-mcp`** | **NeMo Retriever MCP**로 문서 검색/추가 ← MCP 요건 직결 |
| `nemo-retriever` | Retriever 26.8.1 CLI. PDF/이미지/Office/HTML/오디오/비디오, 로컬 LanceDB 인덱스 |
| `rag-blueprint` | RAG Blueprint 배포/설정/디버깅 (Agentic RAG, VLM, 가드레일, 쿼리 재작성, 옵저버빌리티) |
| `nemotron-retrieval-recipes` | Nemotron embed/rerank 레시피 튜닝·평가·배포 |
| `aiq-research` / `aiq-deploy` | AI-Q Blueprint 딥리서치 백엔드 |

### 2-5. 영상 · 비전 (가시화 임팩트 최상)

| 스킬 | 설명 |
|---|---|
| **`deepstream-sop`** | **작업자가 조립 공정을 순서대로 수행했는지** 이벤트 경계 검출하는 GPU 가속 FastAPI 서비스. 지연 측정 포함 |
| `vss-ask-video` / `vss-summarize-video` | 녹화 클립에 시각 질의 / 요약 |
| `vss-query-analytics` | VA-MCP 서버(9901)로 영상 분석 메트릭·인시던트·알림·센서 조회 |
| `vss-manage-alerts` / `vss-setup-behavior-analytics` | 알림/행동분석 |
| `deepstream-generate-pipeline` / `deepstream-dev` | 파이프라인 구축 |

> 💡 `deepstream-sop`는 **제조 현장 SOP 준수 감시**라는 산업 문제를 그대로 담고 있고, **지연 측정이 스킬에 내장**되어 있다. G1(정량 증명)과 G5(산업 문제성)를 동시에 만족시킬 수 있는 드문 조합.

### 2-6. 데이터 생성 · 기타

| 스킬 | 설명 |
|---|---|
| **`data-designer`** | **합성 데이터 생성 파이프라인** (평가셋 자동 생성에 활용 가능) |
| `accelerated-computing-cudf` | cuDF GPU DataFrame, pandas 가속, ETL |
| `nvidia-skill-finder` | NVIDIA 관련 요청에 맞는 스킬 자동 탐색 |
| `skill-card-generator` | 기존 스킬 디렉토리의 **거버넌스 skill card 생성** |
| `nemotron-customize` | 큐레이션/번역/SFT·PEFT/CPT/RL(DPO·RLVR·GRPO·RLHF)/벤치마크/ModelOpt 체이닝 |
| `nemotron-speech` | ASR/TTS/NMT NIM (구 Riva) |
| `earth2studio-*` (7개) | 기상/기후 데이터 fetch + 결정론적 예보 파이프라인 |
| `nvflare-fed-stats` / `nvflare-autofl` | **연합 통계** (원본 데이터 공유 없이 count/mean/stddev/histogram/quantile) |
| `dicom-*` (3개) / `medtech-model-evidence-export` | 의료영상 메타데이터, MLflow 증거팩 |
| `physicsnemo-discover` | SciML 모델/데이터파이프 탐색 |

---

## PART 3. 인용 가능한 데이터 소스

### 3-1. ✅ 6일 내 사용 가능 (TOP 10)

| # | 소스 | 승인 | 제한 | 라이선스 | 가시화 | 정량평가 | URL |
|---|---|---|---|---|---|---|---|
| 1 | **서울열린데이터광장** | **즉시** | **일반키 무제한** | — | ◎ | ○ | https://data.seoul.go.kr/together/guide/useGuide.do |
| 2 | **기상청 단기예보** | **자동(개발/운영 모두)** | 10,000/일 | 공공누리 1유형 | ◎ 격자지도·시계열 | ◎ 예보vs실황 | https://www.data.go.kr/data/15084084/openapi.do |
| 3 | **국토부 아파트 실거래가** | **자동(개발/운영 모두)** | 10,000/일 | **제한 없음** | ◎ 지도·시계열 | ○ MAE | https://www.data.go.kr/data/15126469/openapi.do |
| 4 | **KOSIS 공유서비스** | **자동, 즉시** | 분당 제한 有 | — | ○ | ○ | https://kosis.kr/openapi |
| 5 | **식약처 e약은요** | 개발 자동 | 10,000/일 | **제한 없음** | ○ 관계그래프 | ◎ 골든셋 | https://www.data.go.kr/data/15075057/openapi.do |
| 6 | **국가법령정보 191종 API** | **담당자 승인, 신청 후 1~2일** (공식 이용안내) | — | 출처 표기 의무 | ○ 그래프 | ◎ 멀티홉 | https://open.law.go.kr/LSO/information/guide.do |
| 7 | **AI Hub MCP** | API Key만 | 메타데이터 전용 | — | △ | — | https://github.com/aihub-git/AIHub-MCP |
| 8 | **Nemotron-Personas-Korea** | HF 즉시 | **1M records × 7 persona variants** | **CC-BY-4.0** (HF 메타데이터 실측) | ○ | ○ | https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea |
| 9 | **서울시 지진옥외대피소** (OA-21063) | **즉시** (서울열린데이터) | 일반키 무제한 | **공공누리 1유형** (상업·변경 가능) | ◎ 지도(위경도·면적) | ◎ 수용·거리 | https://data.seoul.go.kr/dataList/OA-21063/S/1/datasetView.do |
| 10 | **NVD CVE API 2.0** (NIST) | **즉시** (키 없이 가능) | 키 없이 30초/5회, 키 시 30초/50회 | 퍼블릭 도메인, 고지문 표기 의무 | ○ | ◎ 골든셋 | https://nvd.nist.gov/developers/start-here |

> ✅ 8번 라이선스는 2026-09-23 HF 메타데이터로 확인 (`num_examples: 1000000`, `license: cc-by-4.0`). 레코드당 persona variant 7종(professional/sports/arts/travel/culinary/family/main)이라 NVIDIA 컬렉션의 "7M personas"는 variant 합산으로 추정. 제출서에는 "600만 건"이 아니라 **"1M records × 7 persona variants"**로 쓸 것.
> ✅ 6번 승인 기간은 공식 이용안내 원문 "공동활용신청에 대해 담당자가 확인 후 '승인' 이후 부터 사용할 수 있습니다. 승인 처리는 신청후 1~2일 이내에 처리됩니다." → G6(2주 금지) 통과. 단 자동승인은 아니므로 오늘 신청할 것.
> ✅ 10번 NVD는 표기 의무: "This product uses data from the NVD API but is not endorsed or certified by the NVD." 키는 이메일 신청 → 단일 링크 활성화(7일 내).

**핵심 엔드포인트**
```
기상청     https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst
에어코리아  https://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMinuDustFrcstDspth
식약처     https://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList
서울시     http://openapi.seoul.go.kr:8088/(인증키)/json/{SERVICE}/{START}/{END}/
```

> 💡 **data.go.kr 핵심 요령**: 대부분 API가 **개발단계는 자동승인**이다. "운영단계 심의승인"이라고 적혀 있어도 **예선 데모는 개발계정으로 충분**하므로 즉시 사용 가능하다.
> 출처: https://www.fairdata.go.kr/ext/data/openApiGuidance.do

> ⭐ **Nemotron-Personas-Korea**: NVIDIA가 공개한 한국 특화 합성 데이터셋(1M records × 7 persona variants, CC-BY-4.0). KOSIS·대법원·건강보험공단·한국농촌경제연구원·네이버 클라우드의 공식 인구조사/노동 데이터를 기반으로 한국의 인구통계·지리·문화 다양성을 반영한다. **"NVIDIA 자산 + 한국 맥락"을 동시에 만족시키는 드문 선택지**다 (축4-4d 대응).

### 3-2. ⭐ 공개 에이전트 벤치마크 (3a 지표 직결)

| 벤치마크 | 측정 | 라이선스 | 난이도 | URL |
|---|---|---|---|---|
| **BFCL V4** | 함수/툴 호출 정확도 + **비용·지연 동시 측정** | **Apache-2.0** | **낮음** `pip install bfcl-eval` | https://gorilla.cs.berkeley.edu/leaderboard.html |
| **τ²-bench** | 툴-에이전트-사용자 상호작용, 정책 준수, **pass^k 일관성** | **MIT** | 중간 | https://github.com/sierra-research/tau2-bench |
| SWE-bench | GitHub 이슈 패치 생성 | MIT | 높음(Docker) | https://github.com/swe-bench/SWE-bench |
| WebArena-Verified | 웹 에이전트, 결정론적 평가기 | Apache-2.0 | 높음 | https://github.com/ServiceNow/webarena-verified |
| GAIA | 범용 어시스턴트 450+문항 | **확인 불가**(gated, 재배포 금지) | 중간 | https://huggingface.co/datasets/gaia-benchmark/GAIA |
| **AgentDojo** (ETH Zurich) | 프롬프트 인젝션 하의 에이전트 안전성. 97 user task + 629 security case. 공식 3지표 **Benign Utility / Utility Under Attack / Targeted ASR** | **MIT** | 중간 `pip install agentdojo` · `python -m agentdojo.scripts.benchmark` | https://github.com/ethz-spylab/agentdojo |
| **MCPTox** (AAAI 2026) | **MCP 툴 포이즈닝**. 실제 MCP 서버 45개·툴 353개 기반 1,348 케이스, 10~11 리스크 카테고리. 20개 LLM 에이전트 최고 거부율 <3% | 리포에서 직접 확인 필요 | 낮음(정적 평가) / 높음(45서버 동적 실행 — **금지**, 5~10개만) | https://github.com/zhiqiangwang4/MCPTox-Benchmark · https://arxiv.org/abs/2508.14925 |

> ⭐ **보안·AgentOps 계열 아이디어(I-01/02/03/14)엔 AgentDojo + MCPTox가 1순위다.** 둘 다 "우리가 만든 공격을 우리가 막았다"는 순환 평가를 벗어나게 해주는 외부 골든셋(숫자 등급 A)이다. 단 AgentDojo 툴은 파이썬 함수 시뮬레이션이라 OpenShell이 개입하려면 실제 파일/HTTP side-effect 어댑터가 필요하고, 97 task 전체 이식은 6일 내 불가 — 공격 2~3종·subset만.

> ⭐ **비용·지연 라우팅(I-10)엔 BFCL이 1순위다.** 유일하게 **Cost(USD)와 Latency(초)를 표준화해 산출**하므로, "Nemotron Nano 셀프호스팅 vs Ultra API" 비교를 심사위원이 검증 가능한 형태로 낼 수 있다.
> 재현성 고정: `pip install bfcl-eval==2025.12.17` 또는 커밋 `f7cf735`

### 3-3. 자체 생성 경로 (통제 가능한 ground truth)

| 방법 | 정량평가 | 비고 |
|---|---|---|
| **에이전트 실행 트레이스** | ◎ | 툴콜 성공/실패, 재시도, 토큰, 지연 자체 로깅. Agent Toolkit 프로파일러 사용 |
| **OpenShell 감사 로그** | ◎ | allow/deny 통계. 정책 위반 시나리오 주입 후 차단율 측정 |
| **합성 평가셋** | ◎ | 공공 API 응답으로 QA 페어 자동 생성 → 골든셋. **6일 내 유일하게 완전 통제 가능** |
| 공식 문서 RAG | ○ | NVIDIA docs는 `llms.txt`/`.md`/MCP 서버 제공 |

### 3-4. ❌ 쓰지 말 것

| # | 항목 | 이유 |
|---|---|---|
| 1 | **AI Hub 안심존** | 심의 최대 2주 + 환경구성 5일. **물리적으로 6일 내 불가** |
| 2 | AI Hub 대용량 데이터셋 | 수백 GB (예: 인삼 등급 603.95GB), 압축해제 추가 용량 |
| 3 | AI Hub 비상업 제한 데이터셋 | 자율주행/ADAS, 경기도 CCTV 등 "비상업적 연구개발만" → 상업화 스토리와 충돌 |
| 4 | **에어코리아** | 개발계정 **500건/일**만. 멀티홉 에이전트가 금방 소진. 게다가 **공공누리 3유형(변경금지)** → 가공 표시 시 위반 소지 |
| 5 | TourAPI | 개발계정 1,000건/일. 이미지 호출 시 부족 |
| 6 | GAIA 재배포 | gating 적용, 재배포 금지 |
| 7 | τ-bench v1.0.1 이전 | 2026-07 채점 수정으로 **이전 결과와 비교 불가**. 버전 명기 필수 |
| 8 | data.go.kr 운영계정 | 심의 대기. **예선은 개발계정으로 끝내는 게 정답** |
| 9 | AI Hub (외국인 팀원) | **내국인만 신청 가능** |

---

## PART 4. 조합 매트릭스 — 데이터 × 스킬

아이디어 생성용 격자. 가로 = 데이터, 세로 = 스킬 그룹.

| 스킬 그룹 \ 데이터 | 서울 공공데이터 | 기상청 | 실거래가 | 식약처 | 법령 API | 자체 트레이스 |
|---|---|---|---|---|---|---|
| **cuOpt 최적화** | ⭐⭐⭐ 배차·수거 경로 | ⭐⭐ 기상제약 스케줄 | ⭐ 입지 최적화 | — | — | — |
| **NeMo Retriever / RAG** | ⭐ | — | ⭐ | ⭐⭐⭐ 약물상호작용 | ⭐⭐⭐ 멀티홉 법령 | ⭐ |
| **OpenShell 정책** | — | — | — | ⭐⭐ 민감정보 차단 | ⭐⭐ | ⭐⭐⭐ 정책 검증 |
| **DeepStream/VSS** | ⭐⭐ CCTV | — | — | — | — | — |
| **rag-eval / rag-perf** | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **data-designer** | ⭐⭐ | ⭐ | ⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| **nvflare 연합통계** | ⭐⭐ | — | ⭐ | ⭐⭐ | — | — |
| **earth2studio** | — | ⭐⭐⭐ | — | — | — | — |

⭐⭐⭐ = 즉시 아이디어화 가능 / ⭐⭐ = 가능 / ⭐ = 억지 / — = 무의미

---

## PART 5. 확인 불가 목록

1. `[UNVERIFIED]` **"Skill API"의 정확한 의도** — NVIDIA 공식 명칭 아님. 패스트캠퍼스 고객센터 확인 필요 (https://day1fastcampussupport.zendesk.com/hc/ko)
2. `[UNVERIFIED]` build.nvidia.com 무료 크레딧 **구체적 수치** — 공식 FAQ는 "신용카드 없는 free trial tier"로만 명시
3. ~~`[UNVERIFIED]` 국가법령정보 OPEN API 승인 소요 기간~~ → **`[VERIFIED]` 2026-09-23: 담당자 승인, 신청 후 1~2일 이내** (https://open.law.go.kr/LSO/information/guide.do). 문의 02-2109-6446
4. `[UNVERIFIED]` AI Hub 일반 데이터 다운로드 승인 소요 기간
5. `[UNVERIFIED]` GAIA 데이터셋 SPDX 라이선스
5-1. `[UNVERIFIED]` MCPTox 리포 라이선스 — GitHub 미표기 가능성. 사용 전 LICENSE 파일 직접 확인
6. `[UNVERIFIED]` KOSIS 분당 호출 제한 구체 수치 (2026-07-09 공지 존재는 확인)
7. `[UNVERIFIED]` DLI 코스 내 "persistent skill libraries" 실제 내용 — 수강 전 확인 불가
8. ⚠️ **웹 UI 366 vs GitHub 363 불일치** — 본 문서는 GitHub 트리 실측(363)을 채택

---

## PART 6. 출처

**NVIDIA**
- https://build.nvidia.com/skills | https://build.nvidia.com/skills.md | https://github.com/NVIDIA/skills
- https://docs.nvidia.com/skills | https://docs.api.nvidia.com/
- https://build.nvidia.com/settings (API 키) | https://build.nvidia.com/openshell
- https://www.nvidia.com/en-us/ai/nemoclaw | https://github.com/NVIDIA/OpenShell
- https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea
- https://docs.nvidia.com/openshell/sandboxes/policies (정적/동적 정책 계층)

**법령·재난·보안 데이터 (v1.1 추가)**
- https://open.law.go.kr/LSO/information/guide.do (승인 1~2일)
- https://data.seoul.go.kr/dataList/OA-21063/S/1/datasetView.do (지진옥외대피소)
- https://nvd.nist.gov/developers/start-here (NVD API 2.0)
- https://github.com/ethz-spylab/agentdojo · https://github.com/zhiqiangwang4/MCPTox-Benchmark

**공공데이터**
- https://www.fairdata.go.kr/ext/data/openApiGuidance.do
- https://data.seoul.go.kr/together/guide/useGuide.do
- https://kosis.kr/openapi
- https://open.law.go.kr/LSO/openApi/guideList.do
- https://aihub.or.kr/devsport/apimcp/list.do?currMenu=527&topMenu=100

**벤치마크**
- https://gorilla.cs.berkeley.edu/leaderboard.html
- https://github.com/sierra-research/tau2-bench
- https://github.com/swe-bench/SWE-bench
- https://github.com/ServiceNow/webarena-verified
