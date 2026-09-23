---
title: "HSGate R3 — 설계서의 NVIDIA 스택 주장 vs 공식 문서 대조 (OpenShell · Policy Advisor · Nemotron · NeMo Retriever · NemoGuard · NemoClaw)"
doc_type: research-validation
version: "1.0"
created_at: 2026-09-23T19:06:00+09:00
checklist_ref: "체크리스트 2부 '가장 먼저 풀어야 할 세 가지' 2번(NVIDIA 툴 실제 스펙), 남은 과제 '에이전트·게이트', 설계서 §4.1·§8"
scope: "읽기 전용. docs.nvidia.com / build.nvidia.com / github.com/NVIDIA 공식만. API 키 발급·로그인 없음"
confidence_tags: "[사실]=직접 확인 / [추론] / [미확인] / [커뮤니티]=비공식"
method: "서브에이전트(읽기 전용) 조사. 기존 03-openshell-policy-yaml-구조.md·DLI 코스 정리와 교차"
related: HSGate_설계서.md §4·§8, 03-openshell-policy-yaml-구조.md, 02-에이전트-개발-규약-정책서.md
---

# R3 NVIDIA 스택 대조

> **한 줄 결론**: 설계서의 NVIDIA 구성요소 역할 6개 중 **2개는 공식 문서상 틀렸고(e: Policy Advisor≠감사기록, f: OpenShell은 승인 토큰을 검증하지 못함)**, 1개는 부분적으로만 맞으며(d: 자격증명 격리는 맞지만 "근거 묶음+토큰 정책 검사"는 OpenShell 기능이 아님), 3개는 모델명만 정확히 쓰면 된다(a·b·c). 심사 1번 "NVIDIA 기술 활용 심도"에서 **틀린 역할 부여는 감점 요인**이므로 설계서 §4.1·§8을 아래 수정안대로 고쳐야 한다.

---

## 0. 판정 요약표

| # | 설계서 주장 | 판정 | 수정 제안 | 근거 URL |
|---|---|---|---|---|
| (a) | 입력 정제: "규칙 + Nemotron Nano 분류"로 인젝션 탐지 | **조건부** | 범용 Nemotron을 분류기로 쓰는 건 공식 권장 경로가 아님. **"규칙(휴리스틱) + `nvidia/nemoguard-jailbreak-detect` NIM + NeMo Guardrails 오케스트레이션"**으로 교체하면 NVIDIA 활용 심도가 더 정확하고 강함 | https://build.nvidia.com/nvidia/nemoguard-jailbreak-detect |
| (b) | 속성 추출·후보 생성·검증기: Nemotron, NeMo Retriever + Nemotron | **가능** | 한국어 CLIP 검색이면 영어 전용 `nv-embedqa-e5-v5` 대신 다국어 `llama-3.2-nv-embedqa-1b-v2`로 모델명 특정. 한국어 성능은 [미확인]이라 "검증됨"이라 쓰지 말 것 | https://build.nvidia.com/nvidia/nv-embedqa-e5-v5 |
| (c) | 라우팅: Nano 단독 → Ultra 승격 | **가능 (명칭 특정 필요)** | Nemotron 3는 Nano/Super/Ultra 3티어 실재. 실제 ID `nemotron-3-nano-30b-a3b` / `nemotron-3-super-120b-a12b` / `nemotron-3-ultra-550b-a55b`로 표기. **Ultra 모델카드만 한국어 지원 명시** | https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b |
| (d) | 외부 게이트: "OpenShell 정책 검사(근거 묶음+승인 토큰) → 자격증명 주입(N-C 방식) → UNI-PASS Mock" | **부분 불가 / 조건부** | 자격증명 격리는 `request_body_credential_rewrite`(placeholder 치환)로 **공식 지원** [사실]. 그러나 L7 규칙은 method/path/query만 매칭하므로 **"근거 묶음+토큰" 의미 검사는 OpenShell이 못 함** → 앱 계층 게이트웨이가 검사하고, OpenShell은 (1) 목적지 allowlist (2) 자격증명 주입만 담당하도록 재기술. "N-C 방식"은 공식 용어 아님 → "OpenShell provider credential placeholder rewrite"로 | https://docs.nvidia.com/openshell/reference/policy-schema |
| (e) | 감사 기록: "Policy Advisor가 승인·반려·차단·보안 플래그·에스컬레이션 보존" | **불가 (오용)** | Policy Advisor는 **에이전트가 네트워크 정책 예외를 제안하고 사람이 승인하는 워크플로우**. 비즈니스 감사 DB가 아님. 감사 로그는 `openshell logs <sandbox> --since …`의 `HTTP:* DENIED`, `CONFIG:PROPOSED/APPROVED/REJECTED` 이벤트 + **앱 계층 감사 DB**로 분리 재기술 | https://docs.nvidia.com/openshell/sandboxes/policy-advisor |
| (f) | 승인 토큰(case_id·세번·트레이스 해시 바인딩·만료)을 OpenShell이 검증 | **불가** | 정책 스키마에 토큰·해시 검증 필드 없음. 토큰 검증은 앱 계층(백엔드/프록시). OpenShell에는 "허용된 엔드포인트+메서드+경로"만 연다 | https://docs.nvidia.com/openshell/reference/policy-schema |

---

## 1. OpenShell 미들웨어·자격증명 주입 [사실]
- `network_middlewares`: 정책의 **dynamic** 섹션. 목적지 호스트별 최대 10개 미들웨어를 `order` 순으로 실행. 각 항목은 `middleware`(내장명 또는 operator 등록명), `endpoints.include/exclude`, `on_error`(fail_closed/fail_open). https://docs.nvidia.com/openshell/reference/policy-schema
- 자격증명 주입: 엔드포인트 필드 `request_body_credential_rewrite: true`(REST) / `websocket_credential_rewrite: true`. UTF-8 `application/json` · `x-www-form-urlencoded` · `text/*` 바디의 **placeholder**(`openshell:resolve:env:KEY` 또는 provider alias)만 실제 값으로 치환. 최대 256KiB 버퍼, `Content-Length` 갱신.
- 실행 순서: 정책/L7 허용 판정 → 미들웨어 체인 → **provider credential injection** ("Every matching config runs once by ascending order before provider credential injection").
- 보장 서술: rewrite가 꺼진 상태에서 placeholder 마커는 upstream 도달 전 거부됨("a reserved credential placeholder is rejected before its marker reaches upstream") → **샌드박스 내부 에이전트는 실제 자격증명 값을 보유하지 않고 placeholder만 다룬다**는 설계서 주장과 부합.
- Providers v2 개요: "Credential delivery uses environment placeholders and proxy rewrite" https://docs.nvidia.com/openshell/sandboxes/providers-v2 [추론]
- 기존 문서(03-openshell §4 v1.1)와 일치.

## 2. OpenShell L7 정책 범위 [사실]
- REST `rules[].allow` / `deny_rules` 매칭 필드: **`method`, `path`(glob), `query`(glob)** 뿐. GraphQL은 `operation_type/operation_name/fields`, MCP는 `method/tool/params.name`, JSON-RPC는 `method`.
- **요청·응답 바디 값(근거 묶음, 토큰, case_id, 세번)을 조건으로 하는 필드는 스키마에 없다.**
- `request_body_credential_rewrite`는 검사기가 아니라 단순 치환기.
- GitHub 이슈 #689도 바디 rewrite를 "webhook APIs put credentials in JSON bodies" 용도로 설명 https://github.com/NVIDIA/OpenShell/issues/689 [사실, 공식 리포 이슈].
- 확장 지점: `middleware: "<operator-owned registration name>"`으로 커스텀 미들웨어 등록 가능(Supervisor Middleware, https://docs.nvidia.com/openshell/extensibility/supervisor-middleware — 제목만 확인 [미확인]). 이는 "OpenShell 기본 기능"이 아니라 **별도 개발 코드**이므로 설계서에 "OpenShell이 정책 검사를 한다"고 쓰면 과장.

### 게이트 아키텍처 수정안 [추론·설계]
```
에이전트(샌드박스) ──HTTP──▶ OpenShell 프록시
   │ (placeholder만 보유)         ├─ network_policies: mock-unipass 호스트 + POST /declarations 만 허용
   │                              ├─ network_middlewares: (선택) 커스텀 미들웨어
   │                              └─ credential rewrite: placeholder → 실제 자격증명
   ▼
앱 계층 게이트웨이(HSGate Gateway, 팀 코드) ── 근거 묶음 존재·resolved 상태·승인 토큰(case_id/세번/해시/만료)·보안 플래그 검사 → 403/200
   ▼
UNI-PASS Mock
```
- 데모 서사: "OpenShell = 목적지·자격증명 강제(에이전트가 오염돼도 다른 호스트로 못 보내고 자격증명을 못 봄)", "HSGate Gateway = 의미 검사(근거 없는 세번·토큰 없는 전송 403)". 두 층을 **구분해서** 말해야 심사위원에게 정확하다.

## 3. Policy Advisor 실제 목적 + 감사 로그 [사실]
- 목적: "Let sandboxed agents propose narrow policy changes through policy.local while keeping developer approval in the loop". 기본 비활성(`agent_policy_proposals_enabled: false`). https://docs.nvidia.com/openshell/sandboxes/policy-advisor
- Agent API 4개: `GET /v1/policy/current`, `POST /v1/proposals`, `GET /v1/proposals/{chunk_id}`, `GET /v1/proposals/{chunk_id}/wait`.
- 승인·반려: `openshell rule approve/reject <sandbox> --chunk-id <id>`. auto 모드는 policy prover delta가 비고 보안 노트가 없을 때만.
- 감사 이벤트: `openshell logs <sandbox-name> --since 10m` → `HTTP:* DENIED`, `CONFIG:PROPOSED`, `CONFIG:APPROVED/REJECTED`, `CONFIG:LOADED` ("Policy advisor emits audit events into the sandbox log").
- **`GET /v1/denials`**: 기존 메모리(2026-09-23 09:25 세션)에는 있었으나 이번 공식 문서 재확인에서는 **없음** → 문서 버전 차이 가능. 설계서에 `/v1/denials`를 인용하지 말 것 [미확인].
- 설계서 (e) 수정: "Policy Advisor"를 감사 저장소로 쓰지 말고, (1) OpenShell 샌드박스 로그(네트워크 거부·정책 변경 이벤트) (2) 앱 계층 감사 DB(관세사 승인·반려·에스컬레이션·보안 플래그)로 분리. Policy Advisor를 쓰고 싶다면 "에이전트가 새 조회 엔드포인트(예: 법령해석 API) 접근을 제안하면 사람이 승인"하는 **보조 데모 장면**으로만.

## 4. Nemotron 모델 실명표 [사실]
| 모델 ID | 파라미터(총/활성) | 컨텍스트 | 라이선스 | build.nvidia.com | 한국어 |
|---|---|---|---|---|---|
| `nemotron-3-nano-30b-a3b` | 30B/3B | [미확인] | [미확인] | Omni-Reasoning 변형은 확인 https://build.nvidia.com/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning ; 순수 텍스트 Nano 독립 엔드포인트 URL [미확인] | [미확인] |
| `nemotron-3-super-120b-a12b` | 120B/12B | 1,048,576 | NVIDIA Nemotron Open Model License | https://build.nvidia.com/nvidia/nemotron-3-super-120b-a12b | 모델카드 언어 목록: EN/FR/DE/IT/JA/ES/ZH — **한국어 없음** |
| `nemotron-3-ultra-550b-a55b` | 550B/55B | 1,048,576 | OpenMDW License v1.1 | https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b (2026-06-04 출시) | **Korean 명시** |
- 제품군 개요: https://developer.nvidia.com/topics/ai/nemotron
- 설계서 (c) 수정: "Nano/Ultra" → 실제 ID. Super를 건너뛰는 이유(비용/지연 2단계 단순화)를 한 줄 명기. 한국어 처리 품질은 Nano/Super가 [미확인]이므로 **dev 100건으로 실측 후 라우팅 임계값 θ 보정**(설계서 §7과 일치).

## 5. NeMo Retriever [부분 사실]
| 모델 | 종류 | 언어 | 차원 | 태그 |
|---|---|---|---|---|
| `nvidia/nv-embedqa-e5-v5` | 임베딩 | **영어 전용** | 1024 | [사실] https://build.nvidia.com/nvidia/nv-embedqa-e5-v5 |
| `nvidia/llama-3.2-nv-embedqa-1b-v2` | 임베딩 | 다국어 (한국어 포함 여부 모델카드 직접 미확인) | 최대 2048 (Matryoshka 384/512/768/1024) | [추론] 존재 확인, 상세 페이지 미열람 [미확인] |
| 리랭커 (`nv-rerankqa` 계열) | 리랭커 | [미확인] | — | [미확인] |
- [커뮤니티] Spheron 블로그 "non-English → llama-3.2-nv-embedqa-1b-v2" (https://www.spheron.network/blog/nvidia-nemo-retriever-gpu-cloud-enterprise-rag-deployment-guide/) — 근거로 쓰지 말 것.
- 함의: 한국어 CLIP 검색은 `llama-3.2-nv-embedqa-1b-v2`가 방향은 맞으나 **한국어 recall을 dev 세트에서 실측**해야 함. BM25(형태소) 하이브리드를 B3 baseline에 병행하면 안전.

## 6. NemoGuard / NeMo Guardrails [사실]
- `NemoGuard-JailbreakDetect-v1.0`: Snowflake-arctic-embed-m 기반 전용 탈옥 탐지, NeMo Guardrails 통합, 상업 사용 가능(NVIDIA Open Model License), JailbreakHub F1 0.9601. https://build.nvidia.com/nvidia/nemoguard-jailbreak-detect
- `llama-3.1-nemoguard-8b-content-safety`(Llama Nemotron Safety Guard V2): 프롬프트/응답 safe·unsafe 분류. NIM 컨테이너(A100/H100/L40S/A6000). https://build.nvidia.com/nvidia/llama-3_1-nemoguard-8b-content-safety , https://docs.nvidia.com/nim/llama-3-1-nemoguard-8b-contentsafety/latest/index.html
- NeMo Guardrails 문서 "Jailbreak Protection" 4계층(LLM self-check, 휴리스틱, NemoGuard NIM, 서드파티), **"prompt injections" 명시**. https://github.com/NVIDIA-NeMo/Guardrails , https://docs.nvidia.com/nemo/guardrails/.md
- 주의 [추론]: 이들은 "탈옥/유해성" 탐지기다. HSGate의 인젝션은 **문서 내 지시문(분류 유도·검토 생략·권한 사칭)**이라 데이터셋 분포가 다름 → NemoGuard를 1차 필터로 쓰되, 설계서 §10.5 fixture 3유형에 대한 탐지율을 **직접 측정해 보고**해야 함. 규칙(정규식: "분류됨", "즉시 신고", "승인 완료, 토큰") + NemoGuard + (필요시) Nemotron 판정의 3중 구조가 정직한 표현.

## 7. NemoClaw · OpenShell 실행 요건 [사실]
- OpenShell: Linux / macOS(Apple Silicon) / Windows(WSL2, experimental). Docker/Podman 또는 MicroVM 필요. 설치 `curl -LsSf https://raw.githubusercontent.com/NVIDIA/OpenShell/main/install.sh | sh`. https://github.com/NVIDIA/openshell
- `openshell-gateway`: Linux glibc 2.28+ (Ubuntu 20.04+, RHEL 8+ 등). https://docs.nvidia.com/openshell/reference/support-matrix
- NemoClaw: OpenShell 샌드박스 안에서 OpenClaw(기본)/Hermes/LangChain Deep Agents를 실행하는 참조 스택 CLI. Express install은 DGX/WSL 프리셋. https://github.com/NVIDIA/NemoClaw , https://docs.nvidia.com/nemoclaw/latest/get-started/prerequisites.html
- GPU: OpenShell 자체는 GPU 불필요로 보이나 공식 문구 [미확인]. NIM 로컬 호스팅은 GPU 필요 → 해커톤은 **build.nvidia.com NIM API(클라우드)** 사용이 재현성 높음 [추론].

## 8. NeMo Agent Toolkit 프로파일러 [사실]
- Profiler: tool/agent 단위 프로파일링, 입출력 토큰·타이밍 추적, 병목 식별. https://docs.nvidia.com/nemo/agent-toolkit/latest/index.html
- 산출물: `standardized_data_all.csv`(요청별 latency/토큰/모델/에러), `workflow_profiling_metrics.json`(평균·백분위·병목 점수), `workflow_profiling_report.txt`. 90/95/99% CI. https://docs.nvidia.com/nemo/agent-toolkit/latest/improve-workflows/evaluate.html , https://docs.nvidia.com/nemo/agent-toolkit/1.6/workflows/profiler.html
- "루프 반복 횟수" 전용 필드는 미확인이나 콜 단위 집계로 도출 가능 [추론]. 설계서 §10.3·§10.6 지표(평균 반복, 토큰, 지연)를 이 툴킷 산출물로 만들면 심사 3번 "완성도" 근거가 됨.

---

## 9. 설계서 반영 체크리스트 (편집 시 적용)
- [ ] §4.1 표 "외부 게이트 | OpenShell, N-C 방식" → "OpenShell(목적지 allowlist + credential placeholder rewrite) + HSGate Gateway(앱 계층 의미 검사)"
- [ ] §4.1 표 "감사 기록 | Policy Advisor" → "OpenShell 샌드박스 로그(`openshell logs`) + 앱 감사 DB"
- [ ] §4.1 표 "입력 정제 | 규칙 + Nemotron Nano 분류" → "규칙 + NemoGuard Jailbreak Detect NIM (+ NeMo Guardrails)"
- [ ] §4.1 "후보 생성 | NeMo Retriever + Nemotron" → 모델 ID 명시(`llama-3.2-nv-embedqa-1b-v2`, `nemotron-3-nano-30b-a3b`)
- [ ] §7 라우팅 표 "Nano/Ultra" → 실제 ID + Super 생략 사유
- [ ] §8.2 "외부 게이트(OpenShell)" 표의 UNI-PASS 전송 조건 1~4 → "HSGate Gateway가 검사, OpenShell은 목적지·자격증명 강제"로 주체 수정
- [ ] §8.3 "N-C 방식" 용어 삭제 → "provider credential placeholder rewrite (`request_body_credential_rewrite`)"
- [ ] §8.4 "감사 기록 (Policy Advisor)" 제목 수정
- [ ] mermaid 다이어그램 GW 서브그래프: POL(정책 검사) 노드를 "OpenShell allowlist"와 "HSGate Gateway 의미 검사" 두 노드로 분리

## 10. 미확인·리스크
- [미확인] `/v1/denials` 엔드포인트 존재 여부(문서 버전 차이 가능).
- [미확인] 리랭커 모델 ID·한국어 지원; `llama-3.2-nv-embedqa-1b-v2` 모델카드의 한국어 명시 여부.
- [미확인] Nano 텍스트 모델의 정확한 build.nvidia.com URL·컨텍스트·라이선스.
- [미확인] Supervisor Middleware로 앱 수준 검사를 구현할 수 있는지(가능해도 6일 내 난이도 높음).
- [미확인] OpenShell 로컬 실행 GPU 요건 공식 문구.

## 11. Sources
- https://docs.nvidia.com/openshell/about/overview
- https://docs.nvidia.com/openshell/sandboxes/policies
- https://docs.nvidia.com/openshell/sandboxes/providers-v2
- https://docs.nvidia.com/openshell/sandboxes/policy-advisor
- https://docs.nvidia.com/openshell/reference/policy-schema
- https://docs.nvidia.com/openshell/reference/default-policy
- https://docs.nvidia.com/openshell/reference/support-matrix
- https://docs.nvidia.com/openshell/extensibility/supervisor-middleware
- https://github.com/NVIDIA/OpenShell/issues/689
- https://github.com/NVIDIA/OpenShell/blob/main/architecture/policy-advisor.md
- https://github.com/NVIDIA/openshell
- https://github.com/NVIDIA/NemoClaw
- https://docs.nvidia.com/nemoclaw/latest/get-started/prerequisites.html
- https://developer.nvidia.com/topics/ai/nemotron
- https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b
- https://build.nvidia.com/nvidia/nemotron-3-super-120b-a12b
- https://build.nvidia.com/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning
- https://build.nvidia.com/nvidia/nv-embedqa-e5-v5
- https://build.nvidia.com/nvidia/nemoguard-jailbreak-detect
- https://build.nvidia.com/nvidia/llama-3_1-nemoguard-8b-content-safety
- https://docs.nvidia.com/nim/llama-3-1-nemoguard-8b-contentsafety/latest/index.html
- https://github.com/NVIDIA-NeMo/Guardrails
- https://docs.nvidia.com/nemo/guardrails/.md
- https://docs.nvidia.com/nemo/agent-toolkit/latest/index.html
- https://docs.nvidia.com/nemo/agent-toolkit/latest/improve-workflows/evaluate.html
- https://docs.nvidia.com/nemo/agent-toolkit/1.6/workflows/profiler.html
- [커뮤니티] https://www.spheron.network/blog/nvidia-nemo-retriever-gpu-cloud-enterprise-rag-deployment-guide/
