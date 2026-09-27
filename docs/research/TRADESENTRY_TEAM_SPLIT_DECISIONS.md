---
title: TradeSentry 2인 분담 착수 전 합의 사항 (모델 구상 ↔ 데이터 정형화)
version: 0.1
created_at: 2026-09-23T20:05+09:00
status: 합의 대기 (권장 기본값 포함). 킥오프 30분에서 D0~D7, D10 서명 → 각자 착수
depends_on: TradeSentry 개발계획(2026-09-23)
confidence_tags: "[사실]=직접 확인, [추론]=근거 있는 판단, [DESIGN]=제안, [미확인]=검증 안 됨"
---

# 착수 전 합의 사항

**요지.** 두 사람이 따로 시작해도 나중에 붙는 조건은 세 가지다. (1) **유사도 그룹핑의 용도**를 "비교집합 선택"으로 못 박고 판정 신호로 쓰지 않는다. (2) **데이터 계약 v1**(스키마·ID·단위·상태값·peer_group 객체)을 먼저 동결하고, 실자료 대신 **합성 픽스처**를 먼저 넘겨 모델 쪽이 그것으로 개발한다. (3) 수집 범위는 peer 선택 결과에 의존하므로 **상대국 superset**을 먼저 정한다. 나머지는 파일 소유권과 "혼자 바꾸면 안 되는 것" 목록이다.

역할 표기: **M** = 모델 구상(유사도 그룹핑 + 판정 정책 + NIM/NAT 워크플로), **D** = 데이터 정형화(관세청·BACI 수집/정규화 + 지표 계산 + 픽스처·평가자료 생성). "모델"이 그룹핑 모델만 뜻한다면 워크플로 소유자를 D0에서 따로 정한다.

## 1. 반드시 먼저 정할 것 (D0~D12)

| # | 결정 항목 | 권장 기본값 [DESIGN] | 소유 | 안 정하면 생기는 일 |
|---|---|---|---|---|
| **D0** | 역할 경계와 파일 소유권 | 아래 2절 표. "모델" = 그룹핑 + 정책 + 워크플로 모두 M. 지표 계산은 D(자료와 붙어 있고 oracle 로 시험 가능) | 둘 | 같은 파일을 둘이 고침, 지표 정의가 두 벌 생김 |
| **D1** | **유사도 그룹핑의 용도** | (a) `compare_partners` 의 비교집합 = 대상국의 peer 집합, (b) UI/Critic 문맥 표시. **판정 신호로 쓰지 않음**(두 신호 유지). 품목 peer 기준선(3번째 신호)은 이번 범위 밖 | 둘 | 평가 20/40 설계·정책·도구 계약이 전부 바뀜 |
| **D2** | 그룹핑 대상·특징·방법·버전 | 3절 spec v0. exporter 국가 × HS85 내 HS6 수출바구니(전세계 대상, 2023) → 코사인 유사도 → top-k peer + Louvain 커뮤니티 라벨. `grouping_version=g1` 로 동결 | M 제안, D 검토 | 동결 없이 평가하면 비교군 간 조건이 달라짐 |
| **D3** | 코드·키 매핑(조인 키) | `data/reference/country_map.csv`: KCS `cntyCd`(2자리) ↔ BACI `country_code`(410 등) ↔ ISO3. **TW ↔ BACI 490 'Asia n.e.s.'(S19)** 명시. HS6 = HSK 앞 6자리 = BACI HS22 `k`(문자열, 선행 0). 연도 키 `YYYY`, 월 키 `YYYYMM` | D | peer 결과를 관세청 자료에 못 붙임 |
| **D4** | 단위·기준 분리 규칙 | KCS = USD/kg(CIF 월별), BACI = 천USD/톤(FOB 화해 연간). **한 지표 안에 두 출처를 섞지 않는다.** BACI 는 선택·문맥 전용. 모든 수치 행에 `source`, `unit`, `basis` 필드 | D 정의, M 준수 | 화면/보고서에 출처 다른 숫자 비교가 섞임 |
| **D5** | 데이터 계약 v1 동결 | 개발계획 3절 5객체 + **`peer_group` 객체**(4절). `schema_version=1`. 변경 = 버전 올림 + 둘 다 서명 + 픽스처 재생성 | D 작성, M 서명 | 모델 쪽 코드가 실자료 도착 시 깨짐 |
| **D6** | **픽스처 우선 handshake** | D 가 `controlled_fixture_v0` 스냅샷(합성) 제공: 3 HS6 × 10 국 × 36개월 + HS10 2개월 + peer_group + receipts + oracle A/B/C 케이스. M 은 이것으로 도구·워크플로 개발. 실스냅샷은 코드 변경 없이 교체 | D | M 이 실자료(키·수집·검증)까지 대기 → 하루 손실 |
| **D7** | 도구 경계 | D = 데이터 접근층(`dal.py`: SQLite 읽기 함수, typed dict 반환). M = 도구 래퍼·NAT 등록·프롬프트·워크플로·Critic·validator 연결. 공통 출력 봉투는 개발계획 5.2. evidence_id 형식 `ev:<snapshot_id>:<table>:<rowid>` | 둘 | 도구가 DB 경로/SQL 을 모델 인자로 받는 사고 |
| **D8** | 상대국 superset 과 peer 선택 위치 | D 는 HS6별 **2023 규모 상위 10개국** 을 수집(superset). M 의 peer 선택은 superset 안에서만. 밖이면 `NOT_COLLECTED` 로 comparability 가 처리 | 둘 | peer 가 미수집국 → 비교 불가 남발 |
| **D9** | 지표·정책 소유와 임계값 동결 | `metrics.py`(D, oracle_ABC 통과 필수), `policy.py`(M). 임계값·허용오차·min_amount 는 probe 정밀도 확인 후 **둘이 함께** `configs/policy_v1.json` 에 기록. 코드에 하드코딩 금지 | 둘 | 반올림 규칙 모른 채 1% 허용오차 같은 임의값 사용 |
| **D10** | 평가자료 분리·생성 책임 | D 가 scenario spec(개발계획 8.1)으로 dev20/holdout40 생성 + 독립 oracle. **M 은 holdout 을 열지 않는다.** 통제자료의 peer_group 도 합성. `grouping_version` 동결 후 3 비교군 동일 사용 | D 생성, M 미접근 | 모델 만든 사람이 정답을 알게 됨 |
| **D11** | 환경·저장소 규약 | Python **3.12** 단일 venv(`trade-baci` 3.12, NAT `>=3.11,<3.14` [사실]) + `requirements.lock`. `git init` 즉시, 브랜치 `data/*`·`model/*` → main PR. Neo4j/GDS 는 **오프라인 계산 전용**(결과를 CSV/SQLite 로 내보냄), 런타임 의존 없음. 비밀값 `.env` 만 | 둘 | 각자 다른 파이썬/패키지로 통합 실패 |
| **D12** | 동기화 리듬·완료 정의 | 하루 2회(정오 결정, 저녁 픽스처 통합 테스트). 결정은 `DECISIONS.md` 에 날짜·버전으로 기록. 완료 = 산출물 + hash + 테스트 통과 | 둘 | 결정이 채팅에 흩어짐 |

## 2. 파일 소유권 (D0)

| 경로 | 소유 | 비고 |
|---|---|---|
| `src/tradesentry/ingest.py`, `metrics.py`, `dal.py`, `data/`, `configs/collection_plan.json`, `eval/` 생성 스크립트·oracle | **D** | M 은 읽기만 |
| `src/tradesentry/tools.py`(래퍼), `workflow.py`, `policy.py`, `validator.py`(실행 중 검증), `configs/model*.yml`, NAT 설정, 프롬프트 | **M** | D 는 읽기만 |
| `src/tradesentry/grouping.py`(BACI 유사도 계산) | **M** 설계·구현, **D** 입력 파일 제공·출력 검수 | 출력은 D5 `peer_group` 계약 |
| `evaluation.py`(NAT 사후 evaluator), `app.py` | M | 평가 정답 파일은 D 소유 |
| `docs/contracts/*.md`, `DECISIONS.md`, `tests/` | 공동 | 계약 변경은 둘 다 서명 |

## 3. 유사도 그룹핑 spec v0 (D2) [DESIGN]

- **대상**: exporter 국가 `i`. **입력**: BACI HS22 V202601, `t=2023`(기준연도; 2024 는 잠정치 [사실: CEPII FAQ]), 전세계 수입국 `j` 합산. 한국만 대상(`j=410`)으로 만든 바구니는 부속 변형으로 두되 기본은 전세계.
- **품목 범위**: 두 해상도. (1) HS85 내 HS6 바구니(296차원, 안정) (2) 선택 HS4 내 HS6 바구니(예: 8504 → 11차원, 특이). 기본은 (1), (2)는 감도 확인용.
- **벡터**: `x_i[k] = v(i→world, k, 2023) / Σ_k v(i→world, ·, 2023)` (금액 비중, 천USD 그대로 사용 — 비중이라 단위 무관).
- **유사도**: 코사인(가중치 반영). trade-baci `gds.ipynb` 의 Node Similarity 는 기본 Jaccard(존재 여부)라 정보가 적음 [추론]; Aura Graph Analytics 세션이 없으면 파이썬(numpy)으로 같은 값을 계산 — **결과 계약이 같으면 어느 쪽이든 허용**. Aura GA 가용성 [미확인].
- **peer 집합**: 대상국 p 에 대해 코사인 상위 k=5, 단 **D8 superset 에 있는 국가만**. 최소 규모 조건(2023 BACI 한국수입 해당 HS6 ≥ 임계) 은 D 가 superset 으로 이미 보장.
- **커뮤니티 라벨**: Louvain(가중 국가 네트워크, seed 고정, resolution 기본) → `community_id` 는 문맥 표시용. 판정에 사용 금지.
- **버전**: `grouping_version=g1`, `params_hash`, 입력 파일 sha256 을 `peer_group` 행에 기록. 평가 동결 전 변경 시 `g2` 로 올리고 dev20 에만 반영.
- **BACI 국가코드 주의**: 대만은 490 'Asia n.e.s.'(iso3 자리 'S19') [사실]. KCS `TW` 와 매핑하되 "대만 이외 아시아 미상 포함" 주석을 country_map 에 남긴다.

## 4. `peer_group` 객체 (D5 추가분)

| 필드 | 값 |
|---|---|
| `entity_type` | `exporter_country` |
| `entity_id`, `entity_namespace` | `CN`, `KCS_cntyCd` (BACI 코드는 `baci_country_code` 별도 컬럼) |
| `scope_type`, `scope_id` | `hs2:85` 또는 `hs4:8504` |
| `peer_rank`, `peer_id`, `similarity` | 1..k, `VN`, 0.83 |
| `community_id` | Louvain 라벨(문맥용) |
| `method`, `grouping_version`, `params_hash` | `cosine_topk`, `g1`, sha |
| `source_version`, `source_year`, `input_sha256` | `BACI_HS22_V202601`, 2023, … |
| `generated_at` | KST ISO |

저장: 스냅샷 SQLite 의 `peer_group` 테이블(읽기 전용) 또는 `data/reference/peer_group_g1.csv` → `snapshot-build` 가 적재. 도구는 파일 경로를 모델에서 받지 않는다.

## 5. 첫 동기화(킥오프 30분)에서 답을 정해야 하는 질문

1. "모델 구상"에 NIM/NAT 워크플로·정책이 포함되는가? (기본: 포함, 모두 M)
2. 유사도 그룹핑은 비교집합 선택 + 문맥 표시까지만인가? (기본: 예. 신호 추가 없음)
3. 바구니 기준: 전세계 수출 vs 한국행 수출? (기본: 전세계, 한국행은 변형)
4. 품목 범위에 HS84 를 넣는가? (기본: 아니오, HS85 만)
5. Aura Graph Analytics 를 쓸 수 있는가? 없으면 파이썬 코사인으로 간다 (결과 계약 동일)
6. superset 크기 10개국이 수집 예산에 맞는가? (54 → 99 논리 요청, 개발계정 1%)
7. 평가에서 peer 비교집합을 "고정 5개국"과 병행 비교할 것인가, 대체할 것인가? (기본: 대체하되 고정 5개국 결과를 부속 표로 남김)
8. 킥오프 시점의 Python venv 를 누가 만들고 lock 을 관리하는가? (기본: D 가 생성, 둘 다 사용)

## 6. 혼자 결정하면 안 되는 것 (D12 부속)

신호 개수(2개), 임계값·허용오차, 도구 8회·재조사 1회 예산, 상태값 집합, HS4/HS6/비교국 확정, `grouping_version` 동결 후 변경, 평가 20/40 구성, 마감·적격성 주장 문구, 데이터 계약 필드 추가/삭제.
