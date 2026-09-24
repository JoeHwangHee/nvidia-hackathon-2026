# TradeSentry 공용 자료 계약 v1

| 항목 | 내용 |
|---|---|
| 문서 | `docs/rules/DATA_CONTRACT_V1.md` |
| 계약 버전 | `schema_version=1` |
| 작성 | 2026-09-24(목), 문서 실행 작업 T2를 맡은 Claude 보조 에이전트(작업 하나를 맡아 실행하는 Claude 하위 에이전트) |
| 역할 | 모델 트랙(M)과 데이터 트랙(D)의 공용 자료 계약. 상태값·ID·모드 이름의 정본 |
| 바꾸는 법 | §13 변경 절차(사용자 승인 필요) |

이 문서는 TradeSentry의 공용 자료 계약(data contract: 두 개발 트랙이 주고받는 객체·필드·값의 형식을 미리 못 박아 둔 약속)이다. TradeSentry는 관세청 수입통계에서 kg당 단가와 상대국 점유율이 전년 같은 달보다 크게 변한 경우를 경보로 잡는다. 경보가 뜨면 Nemotron(NVIDIA의 대형 언어 모델) 조사자와 검수자(Critic: 조사자가 받은 근거와 초안만 보고 누락·반대 설명을 지적하는, 별도 문맥의 같은 모델)가 제한된 도구로 반증을 시도하고, 담당자의 다음 업무를 검토 유지·모니터링·자료 보류 중 하나로 제시한다. 부정이나 위법 여부를 판정하지 않는다.

두 트랙은 모델 트랙(M: 판정 정책·조사 흐름·NVIDIA 연동·유사도 그룹핑)과 데이터 트랙(D: 수집·지표 계산·합성/평가 자료·채점기)이다. 채점기는 결과를 정답과 대조해 점수를 매기는 프로그램이다. 두 트랙은 이 계약만 보고 동시에 개발한다. D가 먼저 넘기는 합성 시험자료와 실자료 스냅샷(한 시점에 수집해 동결한 원자료 묶음)은 같은 계약을 따르므로, 실자료로 바꿀 때 코드를 고치지 않는다 [DESIGN: 분담 D6].

보고서의 모든 사실 주장은 typed claim(품목·상대국·기간·지표·값·단위·근거를 정해진 필드에 담은 주장 1건)으로 내고, 근거 ID(주장이 기대는 스냅샷 행 하나를 가리키는 문자열)로 원자료에 잇는다 [DESIGN: 명세 §3.3]. 이 계약은 그 형식과 값을 정한다.

## 0. 읽는 법

- **원문 블록**: "**명세 §4.x 원문**"으로 시작하는 부분은 문서 세트 명세(이번 문서 실행의 목표 명세. 이하 "명세") §4 "계약 고정값"을 글자 그대로 옮긴 것이다. 값·백틱·구분자(`|`, `,`)를 바꾸지 않았다. 원문 블록 안의 "§4.x"는 명세의 절 번호다.
- **원문 블록의 예외**: §10의 계획 경로·명령 표는 명세 §4.12 원문을 옮긴 블록이었으나, 2026-09-24(목) 사용자 결정(결정 기록 `docs/tracking/decisions/20260924-1720-user-decision-domain-restructure.md`)으로 고쳤다. 그래서 그 블록은 더 이상 원문 그대로가 아니고, 머리 표시도 "사용자 결정으로 고친 표"로 바꿨다. 명세 §4.12와 다른 곳의 근거는 그 결정 기록이다.
- **해설**: 원문 블록 뒤의 해설과 표는 원문의 뜻, 형식, 기존 자료와의 대응을 적는다. 해설과 원문이 어긋나 보이면 원문을 따른다.
- **절 번호**: 원문 블록 밖에서 "§n"은 이 문서의 절이고, "명세 §n"은 명세의 절이다.
- **근거 태그**: [사실] 저장소 파일에서 직접 확인, [추론] 근거 있는 판단, [DESIGN] 팀 설계 규칙(대회 공식 규칙이 아니다), [미확인] 검증하지 않음. 원문 블록의 값은 모두 [DESIGN]이다.
- **출처 약칭**
  - 구 개발계획: `Pasted markdown.md`(기존 개발계획, 이력 문서)
  - 분담: `TRADESENTRY_TEAM_SPLIT_DECISIONS.md`(2인 분담 합의안. "분담 D6"은 그 문서의 결정 D6)
  - 메모: `TRADESENTRY_FACTS_MEMO.md`(실측 사실 메모)
  - 인계: `TRADESENTRY_HANDOFF.md`(세션 인계 문서)
  - 수집기: `src/tradesentry/ingest.py`(관세청 API 수집·검증 코드)
  - oracle: `eval/dev/oracle_ABC.json`(합성 A/B/C 사례의 정답표. A는 구성변화, B는 잔존변화, C는 자료누락 사례다)
  - v2 SQLite 조회: `data/snapshots/kcs_202201_202412_v2/`의 로컬 SQLite를 2026-09-24(목)에 읽기 전용으로 조회한 결과(이 SQLite 파일은 커밋되지 않는다)
- **명세 §4와 이 문서의 위치**

| 명세 절 | 이 문서 |
|---|---|
| §4.1 판정 상태, §4.2 실행 상태, §4.3 관측 상태 | §3 |
| §4.4 모드와 출처, §4.5 이름 규칙, §4.11 스킬 형식 | §4 |
| §4.6 도구 출력 봉투 키 | §5 |
| §4.7 자료 계약 객체 | §2 |
| §4.8 typed claim 필드 | §6 |
| §4.9 주장 채점 결과 | §7 |
| §4.10 실행 결과 기록 키 | §8 |
| §4.10-1 보고서 객체 키, §4.10-2 주장 채점 기록 키 | §9 |
| §4.12 계획 경로·명령 표 | §10(2026-09-24(목) 사용자 결정으로 고친 표) |

## 1. 범위와 버전

### 1.1 담는 것과 담지 않는 것

- 담는 것: 객체와 필드(§2), 상태값(§3), 이름과 ID(§4), 도구 입출력 봉투(도구가 돌려주는 공통 출력 틀, §5), typed claim(§6), 주장 채점 결과(§7), 실행 결과 기록(§8), 보고서 객체와 주장 채점 기록(§9), 구현 단계의 예정 경로·명령과 이름·출력 규칙(§10), 단위와 정밀도(§11), 봉인(평가 자료를 저장소 밖에 격리하고 해시 목록만 커밋하는 보관 방식) 해시 기록(§12), 변경 절차(§13).
- 담지 않는 것
  - 판정 기준값(단가 변화율·점유율 변화 기준, `min_amount`·`min_weight` 등): D가 개발 묶음으로 제안하고 사용자가 승인하면 `configs/policy_v1.json`에 기록한다 [DESIGN: 명세 §3.3].
  - 채점 규칙의 세부(필드별 채점 순서, 산문 패턴 목록, 표본·신뢰구간): 평가 룰북(평가 규칙과 채점 기준을 정한 문서) `docs/eval/RULEBOOK.md`가 정한다.
  - 코드. 이 문서는 구현 전의 약속이다.
- 적용 대상: 두 트랙의 코드·자료·평가 산출물 전부와 문서 세트의 다른 문서.

### 1.2 계약 버전

- 이 계약의 버전은 `schema_version=1`이다 [DESIGN: 명세 §4.7, 분담 D5].
- 인수물(D가 M에게 넘기는 자료·코드 묶음)마다 `schema_version=1`을 표시한다 [DESIGN: 명세 §3.10]. 표시 위치는 다음과 같다 [DESIGN].
  - 스냅샷: `snapshot` 객체에 `schema_version` 값 1을 담는다.
  - 그 밖의 JSON(키와 값으로 된 텍스트 자료 형식) 인수물: 최상위 키 `schema_version`에 1을 담는다(예: §12의 `eval/sealed_manifest.json`).
  - 줄 단위 기록(채점 결과 `scorer_results-{시각}.jsonl`, 주장 채점 기록 `scorer_claims-{시각}.jsonl`. 이름 규칙은 §10.3): 명세가 정한 키 목록(§8, §9)을 늘리지 않는다. 계약 버전은 같은 채점 실행 폴더의 요약 `scorer_summary-{시각}.md`에 적는다.
- 나머지 인수 조건(자료 계약 검사 명령 통과, 자료 접근층 패키지 `dal/`(스냅샷을 읽는 함수 모음)로 읽힘, 지표 계산 패키지 `metrics/`의 oracle A/B/C 재현, 검증 명령과 종료 코드의 PR(pull request: 변경을 합치기 전에 검토받는 요청) 기록)은 병렬 개발 규칙 `docs/rules/PARALLEL_DEV_RULES.md`의 D → M 인수 조건을 따른다.

### 1.3 함께 기록하는 버전 축

| 키 | 무엇의 버전인가 | 값 |
|---|---|---|
| `schema_version` | 이 자료 계약 | 1 |
| `policy_version` | 탐지·판정 정책 | `policy_v1`(승인 전에는 개발용 정책 `dev-0.1`, `configs/policy_dev.json`) |
| `grouping_version` | 비교 대상 집합 | `g0`(2026-09-25(금) MVP 시험까지. MVP는 최소 기능 제품), `g1`(동결 뒤 기본) |
| `rulebook_version` | 평가 룰북 | `RB-1` |
| `formula_version` | 지표 공식(§11.2) | D가 정한다 |
| `code_version` | 실행한 코드 | git 커밋 해시(코드 버전을 가리키는 고유 문자열) |

- 계약은 `schema_version`, 그룹핑은 `grouping_version`, 정책은 `policy_version`을 올려서 바꾼다. 세 축을 문서와 코드가 따로 기록해야 나중에 결과를 재현할 수 있다 [DESIGN].

### 1.4 우선순위와 기존 문서

- 명세는 2026-09-23(수) 설계 세션에서 사용자가 승인한 문서 세트 목표 명세로, 저장소에는 없다. 이 문서는 명세 §4의 고정값을 원문 블록으로 글자 그대로 옮기고, 그 밖의 설계 규칙([DESIGN] 태그)을 더했다. 구현 실행부터는 이 문서가 값의 정본이다. 본문의 "명세 §x" 표기는 출처 표시다.
- 산출 문서끼리 값이 충돌하면 `DATA_CONTRACT_V1` > `RULEBOOK` > `DEV_PLAN` > `ROADMAP` > 나머지 순으로 따른다. 모두 명세 아래다 [DESIGN: 명세 §2-5].
- 기존 문서(구 개발계획, 분담, oracle 등)는 고치지 않는다. 기존 표기가 이 계약의 코드와 다르면 이 문서가 대응표를 둔다(§3.2, §11.5).
- 구 개발계획의 결정 중 이번에 바뀐 것은 옮기지 않았다. 예를 들어 기간은 "2022~2023 24개월"이 아니라 2022-01~2024-12(36개월)이고, 전년동월(비교월과 12개월 전 같은 달의 비교) 판정이 가능한 달은 2023-01~2024-12(24개월)이다 [DESIGN: 명세 §3.2].

## 2. 객체와 필드

**명세 §4.7 원문**

기존 개발계획 §3 "최소 데이터 계약" 5개 객체(`snapshot`, `observation`, `collection_receipt`, `metric`, `case`)의 필수 필드와 팀 분담 문서 §4의 `peer_group` 객체 필드를 그대로 쓴다. `schema_version=1`이다.

### 2.1 필수 필드 원문 — 구 개발계획 §3 "최소 데이터 계약"

`Pasted markdown.md` §3 "최소 데이터 계약" 표를 붙여넣기 흔적(역슬래시 이스케이프)만 걷어 내고 옮겼다. 필드를 빼거나 더하지 않았다 [사실]. 표의 raw는 API가 돌려준 응답 파일 원본이고, sha256은 파일 내용으로 계산하는 64자리 16진수 지문(내용이 조금만 바뀌어도 값이 달라진다)이다.

| 객체 | 필수 필드 |
|---|---|
| `snapshot` | snapshot_id, source_kind(real/controlled), collected_at, source_url, 요청조건(키 제외), raw_sha256, normalized_sha256, period, HS버전, importer, valuation_basis, units, precision/rounding 규칙, coverage_status |
| `observation` | snapshot_id, month, partner_code 원문/namespace, hs_code 문자열, hs_level, hs_version, amount_usd, net_weight_kg, observation_status, raw_file_id, raw_row_locator |
| `collection_receipt` | request_id, 대상 월/국가/HS, 성공·오류·미수집, response_hash, 페이지/행수, timestamp |
| `metric` | metric_id, formula_version, inputs/evidence_ids, value 또는 null, unit, comparability_flags, 허용오차 |
| `case` | case_id, HS6, partner, month, baseline_month, signals, snapshot_id, policy_version |

### 2.2 `peer_group` 객체 원문 — 분담 §4

`peer_group`은 대상국마다 비교할 상대국 집합을 적는 객체다. 아래 표와 저장 문장은 분담 §4를 그대로 옮겼다 [사실]. 여기 나오는 BACI는 CEPII(프랑스의 국제경제 연구기관)가 각국 신고를 맞춰 만든 연간 국제무역 자료, Louvain은 네트워크를 서로 가까운 무리로 나누는 알고리즘, KST ISO는 한국 표준시를 붙인 ISO 8601 시각 표기, SQLite는 파일 하나로 된 데이터베이스다.

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

### 2.3 필드 해설과 v1 키 이름

- "v1 키"는 코드와 JSON에서 쓰는 이름이다. 원문이 영문 식별자로 적은 필드는 그 이름을 그대로 쓴다.
- 원문이 한국어 설명으로 적은 필드("요청조건(키 제외)", "HS버전" 등)는 기존 수집기의 열·키 이름을 우선 따랐다 [DESIGN].
- 원문 한 칸이 두 가지를 적은 경우(예: "partner_code 원문/namespace")는 두 키로 나눴다. 원문 필드를 빼지 않았다.
- 표 아래 "기존 열"은 원문 필수 필드에는 없지만 기존 수집기에 이미 있는 열이다. v1은 이 열들을 필수로 올리지 않는다.

#### 2.3.1 `snapshot` — 한 시점에 수집해 동결한 원자료 묶음

스냅샷 폴더에는 raw 응답, manifest(수집 요청 목록과 설정을 적은 파일), SQLite 파일이 들어 있다 [사실: 수집기].

| 원문 표기 | v1 키 | 형식 | 뜻과 기존 자료 대응 |
|---|---|---|---|
| snapshot_id | `snapshot_id` | 문자열 | 스냅샷 이름. 실자료 작업 기준은 `kcs_202201_202412_v2`다 [DESIGN: 명세 §4.5]. 합성 시험자료는 폴더 이름과 같은 `controlled_fixture_v0`을 쓴다 [추론: 명세 §4.12 경로] |
| source_kind(real/controlled) | `source_kind` | 문자열 | 실자료(`real`)인지 합성(`controlled`)인지. 값 표기는 명세 §4.4를 따른다(§4) |
| collected_at | `collected_at` | KST ISO 8601 시각 | 수집(합성은 생성)을 마친 시각. 기존 수집기는 스냅샷 메타에 `created_at`(스냅샷을 처음 연 시각)과 `last_collect_at`(마지막 수집 실행 시각)을 남긴다 [사실: 수집기]. `snapshot-build`가 `last_collect_at`을 `collected_at`으로 옮긴다 [DESIGN] |
| source_url | `source_url` | 문자열 목록 | 공개 출처 안내 페이지. 실자료는 공공데이터포털 15100475(국가별)·15101609(품목별) 안내 페이지다 [사실: 수집기]. 합성 자료는 생성 규칙 문서나 생성 스크립트의 저장소 상대경로를 적는다 [DESIGN] |
| 요청조건(키 제외) | `collection_plan` | 객체 | 수집 설정 전문(기간·HS 코드·상대국·구간 길이·분모 수집 여부). HS 코드는 국제 품목분류 번호이며 앞 4자리가 HS4, 6자리가 HS6, 한국 세분류 10자리가 HS10이다. 서비스키는 넣지 않는다. 기존 `manifest.json`의 `config` 및 `configs/collection_plan.json`과 같은 내용이다 [사실: 수집기] |
| raw_sha256 | `raw_sha256` | 16진수 64자 | raw 응답 파일 전체의 결합 sha256. v2의 값과 결합 방법은 `data/snapshots/kcs_202201_202412_v2/snapshot_hash.json`의 `raw_combined_sha256`과 `method`에 있다 [사실] |
| normalized_sha256 | `normalized_sha256` | 16진수 64자 | 정규화 자료(SQLite 행)의 sha256. v2에는 아직 없다 [사실: `snapshot_hash.json`에는 raw 해시만 있다]. rowid(SQLite가 행마다 붙이는 정수 번호, §4.4)까지 넣어 계산해서 재적재로 rowid가 바뀌면 값도 바뀌게 한다. 직렬화 방법은 D가 `snapshot-build`를 구현할 때 정하고 결정 기록(결정과 이유를 남기는 문서)에 남긴다. 대조용 기준값은 SQLite 밖의 커밋된 기록에 둔다(§4.4 규칙 4) [DESIGN] |
| period | `period` | 객체 `{"start": "YYYYMM", "end": "YYYYMM"}` | 수집 기간. v2는 `202201`~`202412`다 [사실: `configs/collection_plan.json`]. 기존 스냅샷 메타는 `period_start`·`period_end` 두 키로 적는다 [사실: 수집기] |
| HS버전 | `hs_version` | 문자열 `<코드 체계>:<HS 개정판>` | 코드 체계와 HS 개정판(세계관세기구가 주기적으로 고치는 HS의 판)을 적는다(예: `HSK:HS2022`). 개정판을 확인하지 못했으면 코드 체계만 적는다(`HSK`). v2의 스냅샷 메타 값은 "HSK (응답 코드 그대로; 연도별 개정 여부는 코드 출현 연도로 판단)"이고, 관측 행 값은 모두 `HSK`다 [사실: v2 SQLite 조회]. v2 대응은 표 아래를 본다 [DESIGN] |
| importer | `importer` | 문자열 | 수입국. 기존 값은 `KR`이다 [사실: 수집기] |
| valuation_basis | `valuation_basis` | 객체 | 금액 기준. 수입은 CIF(운임·보험료를 포함한 가격) 과세가격 미화 달러, 수출은 FOB(선적항 본선 인도 가격) 신고 미화 달러다 [사실: 수집기] |
| units | `units` | 객체 | `{"amount": "USD", "weight": "kg"}` [사실: 수집기] |
| precision/rounding 규칙 | `precision_rule` | 문자열 | 정밀도·반올림 규칙(§11.1). 기존 메타 키 이름 그대로다 [사실: 수집기] |
| coverage_status | `coverage_status` | 문자열 | 수집 범위가 다 찼는지의 상태. 기존 수집기는 처음에 `IN_PROGRESS`를 적는다 [사실: 수집기]. v1은 이 필드의 값 집합을 정하지 않는다. 정하려면 §13 절차를 거친다 |

- `hs_version`의 v2 대응: 대상 HS6 4개의 HS10 코드(6·5·4·2개)는 적용시작일자가 모두 2022-01-01 이전이거나 당일이다. 이 코드 집합은 v2에서 관측된 HS10 코드 집합과 같고, 대상 HS6 4개의 HS10 코드 수는 2022·2023·2024년이 같다 [사실: `data/reference/관세청_HS부호_20260101.xlsx` 읽기 전용 확인, 메모 §2]. HSGATE_EVALUATION_DATA_REVIEW.md 표 6행은 관세·통계통합품목분류표(HSK) 개정 시행일로 2022-01-01 다음을 2025-01-01로 적는다. 그러나 같은 출처가 "10단위는 거의 매년 바뀐다"고 하고, 위 xlsx에는 그 목록에 없는 적용시작일자 2017-01-01 코드도 있어 그 목록은 완전하지 않다. 그래서 v2 기간 안의 HSK 개정이 2022-01-01뿐이라는 판단은 [추론]이다. 이 판은 HS2022(세계관세기구 HS의 2022년 개정판)를 반영한 판으로 보이지만 [추론], 한국 관세율표의 HS2022 반영 시행일은 확인하지 않았다 [미확인: HSGATE_DATA_VALIDITY.md §8]. 확인 전까지 v2의 `hs_version`은 `HSK`(개정판 미상)로 두고, 확인되면 `HSK:HS2022`로 적는다 [DESIGN].
- 동결 규칙: 스냅샷 SQLite는 `snapshot-build`가 raw 응답과 manifest에서 만드는 파생 저장소다. 승인된 `policy_version`의 승격 규칙(§3.4)까지 적용한 최종 빌드를 동결하고, 동결 뒤에는 고치지 않는다 [DESIGN]. 설정이 바뀌면 새 `snapshot_id`로 새 스냅샷을 만든다. v1·v2 스냅샷에 수집기의 `plan`·`collect`를 다시 돌리면 `manifest.json`이 덮어써지므로 하지 않는다 [사실: 인계 §6].
- 스냅샷은 모든 조회의 유일한 원천이다. 조사 중에 새로 수집하지 않고, 도구가 없는 값을 만들어 채우지 않는다 [DESIGN].

#### 2.3.2 `observation` — 수집 요청 × 월 × 상대국 × HS 코드 × 흐름 단위의 금액과 순중량

| 원문 표기 | v1 키 | 형식 | 뜻과 기존 자료 대응 |
|---|---|---|---|
| snapshot_id | `snapshot_id` | 문자열 | 이 행이 속한 스냅샷 |
| month | `month` | 문자열. 월 행은 `YYYYMM`, 총계 행(응답에 함께 오는 조회 구간 전체 합계 행)은 `RAW:총계` | 관측 월. 응답의 `2024.01` 형식을 `202401`로 바꿔 적는다. 월 형식이 아닌 행은 `RAW:` 접두어를 붙여 원문을 보존하며, v2의 총계 행은 모두 `RAW:총계`다 [사실: 수집기, v2 SQLite 조회] |
| partner_code 원문/namespace | `partner_code`, `partner_namespace` | 문자열 | 상대국 코드 원문(예: `CN`)과 코드 체계 이름(`KCS_cntyCd`: 관세청 조회코드의 2자리 국가코드). 전체국가 분모 행은 `partner_code`가 `ALL`이다 [사실: 수집기] |
| hs_code 문자열 | `hs_code` | 문자열 | HS 코드(국제 품목분류 번호). 앞자리 0을 지키도록 문자열로 둔다. 총계 행(국가별 `nitemtrade` 응답은 `hsCd='-'`, 품목별 `itemtrade`(`ALL`) 응답은 `hsCode='-'`인 행)은 요청한 코드로 귀속한다 [사실: 수집기, `data/snapshots/kcs_202201_202412_v2/raw/`의 v2 raw XML(itemtrade 총계 행 21개는 `hsCode='-'`, nitemtrade 총계 행 334개는 `hsCd='-'`, 빈 응답 2개에는 총계 행 없음)] |
| hs_level | `hs_level` | 정수 | HS 코드 자릿수(2·4·6·10) [사실: 수집기는 코드 길이를 적는다] |
| hs_version | `hs_version` | 문자열 | `snapshot`의 `hs_version`과 같은 형식(§2.3.1). v2 관측 행은 모두 `HSK`다 [사실: v2 SQLite 조회] |
| amount_usd | `amount_usd` | 정수 또는 `null` | 금액(USD 정수). 관측이 없으면 `null`이며 0으로 채우지 않는다 [사실: 수집기] |
| net_weight_kg | `net_weight_kg` | 정수 또는 `null` | 순중량(kg 정수). 관측이 없으면 `null`이다 [사실: 수집기] |
| observation_status | `observation_status` | 관측 상태 코드(§3.4) | 이 행의 관측 상태 |
| raw_file_id | `raw_file_id` | 문자열 | raw 응답 파일 이름(예: `<request_id>.xml`) [사실: 수집기] |
| raw_row_locator | `raw_row_locator` | 문자열 | raw 파일 안의 행 위치(예: `item[3]`) [사실: 수집기] |

- 기존 열: `request_id`(행을 만든 수집 요청. `collection_receipt`와 잇는 키), `flow`(`import` 또는 `export`), `item_name`(품목명 원문) [사실: 수집기]. 명세 §4.7의 "그대로 쓴다"를 지키려고 v1은 이 세 열을 필수 필드로 올리지 않는다. 대신 아래 행 규칙을 계약 규칙으로 둔다 [DESIGN].

**행 규칙**

1. 관측 단위: 기존 `observation` 테이블의 기본 키는 (`request_id`, `month`, `partner_code`, `hs_code`, `flow`)다 [사실: 수집기]. 같은 월·상대국·HS 코드라도 수집 요청이나 흐름이 다르면 행이 따로 있다.
2. 흐름: 지표는 `flow`가 `import`인 행만 쓴다 [DESIGN].
3. 총계 행: 응답의 총계 행(국가별 `nitemtrade`는 `hsCd='-'`, 품목별 `itemtrade`(`ALL`)는 `hsCode='-'`)은 `observation_status`=`OBSERVED`, `hs_code`=요청 코드(`hs_level`=요청 코드 자릿수), `month`=`RAW:총계`로 저장된다. 값은 그 요청의 조회 구간(v2는 12개월) 전체 합이다 [사실: 수집기, v2 SQLite 조회]. 총계 행은 총계·부모-하위 대조에만 쓰고, 월 지표의 입력이나 근거 ID 대상으로 쓰지 않는다 [DESIGN].
4. 상대국 월 값(부모 HS6 행): 상대국의 HS6 월 금액·중량은 그 HS6가 속한 HS4의 스캔 요청(`nitemtrade`, `hsSgn`=HS4 코드, v2는 `8504`, `cntyCd`=상대국)이 돌려준 HS6 행(`hs_level`=6)에서만 가져온다. 이 행을 부모 HS6 행이라 한다. HS6 요청이 돌려준 HS10 하위 행은 구성효과 분해와 부모 대조에만 쓴다(§11.2 원천 규칙) [DESIGN]. 부모 HS6 행이 없는 월은 값을 계산하지 않고(`null`과 사유), 그 월을 맡은 요청들이 남긴 상태 행(`UNRESOLVED_ZERO`, `REQUEST_FAILED`, `NOT_COLLECTED`)을 도구 봉투의 `missingness`로 돌려준다 [DESIGN]. 예외: 그 월의 상태 행이 `CONFIRMED_NO_TRADE`(승격된 행)이면 §3.4대로 V·Q를 0으로 본다. 점유율 분자는 0이고, 단가와 기준월 값이 0인 변화율(`r_U`)은 `null`이다 [DESIGN]. 부모 HS6 행이 있으면, 같은 월에 HS6 요청이 HS6 자릿수로 남긴 상태 행(`UNRESOLVED_ZERO`, `REQUEST_FAILED`)이나 `snapshot-build`가 만든 `NOT_COLLECTED` 행이 같은 (`partner_code`, `hs_code`, `month`, `flow`) 키로 함께 있어도 월 값은 부모 HS6 행에서 가져온다. 그 상태 행은 HS10 하위 자료가 빠졌다는 뜻이므로 구성효과 분해의 `missingness`로만 돌려준다 [DESIGN]. oracle C 사례가 이 경우다. 부모 값(V 360, Q 100)으로 `U`와 `r_U`를 계산하고, HS10 조회가 실패(`REQUEST_FAILED`)했으므로 `within_effect`·`mix_effect`는 `null`이다 [사실: oracle]. `residual`도 계산하지 않는다 [DESIGN]. v2에는 이런 키가 없다 [사실: v2 SQLite 조회].
5. 전체국가(`ALL`) 월 값: `ALL`에는 월별 HS6 행이 없고, HS6 자릿수의 `ALL` 행은 모두 총계 행이다 [사실: v2 SQLite 조회]. 그래서 HS6의 전체국가 월 금액(점유율 분모)은 `hs_code` 앞 6자리가 그 HS6인 `ALL` HS10 월 행의 금액 합이다(6의 중복 제거 뒤) [DESIGN].
6. `ALL` 중복 제거: v2에서 대상 HS6 아래 `ALL`×HS10×월 키는 `8504` 요청과 그 HS6 요청(예: `850450`) 아래 두 번 들어 있다. 수입 흐름에서 612키이고 두 값의 차이는 0이다 [사실: v2 SQLite 조회, 메모 §2 "전체국가 분모 대조 612건 일치"]. 이 규칙은 `partner_code`가 `ALL`이고 `hs_level`이 10인 월 행에만 적용한다. 같은 (`hs_code`, `month`, `flow`) 키에 이런 행이 둘 이상이면 요청 코드(`collection_receipt`의 `params_json`에 든 `hsSgn`)가 가장 긴 요청의 행 하나만 쓴다. 그래도 둘 이상이면 `request_id` 사전순으로 첫 행을 쓴다. 이 규칙으로 v2에서는 HS6 요청의 행이 쓰인다. 상대국 행에는 이 규칙을 쓰지 않고 규칙 4를 따른다 [DESIGN]. 중복된 두 행의 값이 다르면 하나를 조용히 고르지 않고 스냅샷 빌드를 오류로 멈춘다 [DESIGN]. v2에서는 불일치가 0건이다 [사실: `data/snapshots/kcs_202201_202412_v2/data-readiness.json`의 `cross_check.ALL`(matched 612, mismatches 없음)].
7. 분석 범위: 탐지·분석 대상은 HS6 4개 × 상대국 16개와 `ALL`이다(§4.2). v2에 함께 든 선정용 HS4 스캔(`8544`, `8536`)의 행과 `8504` 아래 다른 HS6(예: `850440`)의 행은 범위 밖이며, 지표와 도구가 쓰지 않는다 [DESIGN: 명세 §3.2].
8. 교체 조건: 합성 시험자료는 실스냅샷과 같은 열(`request_id`, `flow`, `item_name`을 포함한 기존 열 전체)을 갖추고 위 규칙을 따라야 코드 변경 없이 실스냅샷과 바꿔 쓸 수 있다 [DESIGN: 분담 D6].
9. `item_name` 같은 품목명·설명은 데이터로만 다루고 지시문으로 실행하지 않는다 [DESIGN: 명세 §3.3].

#### 2.3.3 `collection_receipt` — 수집 요청 1건의 결과 기록

| 원문 표기 | v1 키 | 형식 | 뜻과 기존 자료 대응 |
|---|---|---|---|
| request_id | `request_id` | 16진수 16자 | 요청 ID. 서비스키를 뺀 요청 파라미터와 엔드포인트를 키 순으로 정렬한 JSON의 sha256 앞 16자다 [사실: 수집기] |
| 대상 월/국가/HS | `endpoint`, `params_json` | 문자열 | 엔드포인트 이름(`nitemtrade` 국가별, `itemtrade` 품목별 전체국가 합계)과 요청 파라미터 JSON. 파라미터는 시작 월 `strtYymm`, 끝 월 `endYymm`, HS 코드 `hsSgn`, 국가 `cntyCd`(국가별만)이고 서비스키는 넣지 않는다 [사실: 수집기] |
| 성공·오류·미수집 | `status` | `OK` 또는 `FAILED` | 요청 결과 [사실: 수집기]. 미수집은 값이 아니라 기록이 없는 것으로 나타난다. 수집 계획(`manifest.json`)에 있는 요청에 receipt가 없으면 미수집이다 [사실: 수집기 `verify`] |
| response_hash | `response_hash` | 16진수 64자 | raw 응답 바이트의 sha256 [사실: 수집기] |
| 페이지/행수 | `row_count` | 정수 | 응답 행 수. 이 API 응답에는 페이지 필드가 없다 [사실: 메모 §1] |
| timestamp | `timestamp` | KST ISO 8601 시각 | 기록 시각 [사실: 수집기] |

- 기존 열: `http_status`, `attempts`, `result_code`, `result_msg`, `error`, `elapsed_ms`, `raw_file_id` [사실: 수집기]. 모든 시도는 `collection_attempt` 테이블에, 외부 HTTP 시도 수는 스냅샷 폴더의 `collection_http_attempts.jsonl`에 따로 남는다 [사실: 수집기].
- 외부 수집 HTTP 시도 수는 에이전트 도구 호출 예산(`tool_attempts`, §5.3)과 다른 지표다. 두 수를 섞지 않는다 [사실: 수집기 머리말].
- 재수집이 실패해도 이전 정상 자료(raw·receipt·행)를 덮어쓰지 않는다 [사실: 수집기].

#### 2.3.4 `metric` — 관측치로 계산한 지표 값 1개

| 원문 표기 | v1 키 | 형식 | 뜻과 기존 자료 대응 |
|---|---|---|---|
| metric_id | `metric_id` | 문자열 | 지표 값 하나의 고유 ID. 문자열 형식은 v1에서 정하지 않는다(§4.5) |
| formula_version | `formula_version` | 문자열 | 계산 공식(§11.2)의 버전. 공식을 바꾸면 올린다 [DESIGN] |
| inputs/evidence_ids | `inputs`, `evidence_ids` | 객체, 근거 ID 목록 | `inputs`: 지표 기호(§11.2), 대상(`hs6`·`partner`·`period`·`baseline_period`. typed claim과 같은 이름), 계산에 쓴 입력값(V·Q는 §11.2 원천 규칙의 행에서 가져온다). `evidence_ids`: 그 입력값이 나온 스냅샷 행의 근거 ID(§4.4) [DESIGN] |
| value 또는 null | `value` | 수 또는 `null` | 계산 값(단위는 §11.2). 계산하지 않는 경우(§11.1의 0·미상 규칙)는 `null`이다 |
| unit | `unit` | 문자열 | §11.2의 단위 표기 |
| comparability_flags | `comparability_flags` | 문자열 목록 | 비교 가능성 표시. `value`가 `null`이면 그 사유를 여기에 적는다 [DESIGN]. 값 집합은 v1에서 정하지 않는다 |
| 허용오차 | `tolerance` | 수 또는 `null` | 대조에 쓴 허용오차(§11.1). 주장 채점 기록(§9.2)의 `tolerance`와 같은 이름이다 [DESIGN] |

- 원문 필드에는 지표 종류(단가인지 점유율인지)와 대상(품목·상대국·기간)을 적는 칸이 따로 없다. v1은 이것을 `inputs` 안에 담는다 [DESIGN].
- 지표는 값을 돌려주거나, `null`과 사유를 돌려준다. 도구는 이 객체를 봉투의 `metrics`(§5)에 담는다 [DESIGN].
- `decompose_hs`는 `within_effect`, `mix_effect`, `residual`을 각각 `metric` 객체로 돌려주고, 개별 하위변화와 중량 비중은 HS10 하위 지표(`U@<HS10 코드>`, `r_U@<HS10 코드>`, `w@<HS10 코드>`, §6.2)로 돌려준다 [DESIGN].

#### 2.3.5 `case` — 코드가 정책으로 탐지한 경보 사례 1건

| 원문 표기 | v1 키 | 형식 | 뜻과 기존 자료 대응 |
|---|---|---|---|
| case_id | `case_id` | 문자열 | 사례 고유 ID(§4.5). oracle 예: `A-composition` [사실: oracle] |
| HS6 | `hs6` | 문자열 6자 | 대상 품목(HS6). typed claim의 `hs6`와 같은 이름·형식이다 [DESIGN] |
| partner | `partner` | 문자열 | 대상 상대국 코드(`KCS_cntyCd` 체계, 예: `CN`) |
| month | `month` | `YYYYMM` | 비교월 t |
| baseline_month | `baseline_month` | `YYYYMM` | 기준월 t−12(전년 같은 달) |
| signals | `signals` | 객체 | 신호 코드(`unit_value`, `share`)를 키로, 발동 여부(`signal_trigger`의 값 `TRIGGERED` 또는 `NOT_TRIGGERED`)를 값으로 둔다 [DESIGN]. oracle의 `signals`와 같은 모양이다 [사실: oracle] |
| snapshot_id | `snapshot_id` | 문자열 | 탐지에 쓴 스냅샷 |
| policy_version | `policy_version` | 문자열 | 탐지에 쓴 정책 버전(승인 뒤 `policy_v1`) |

- 사례는 코드가 만들고 모델은 만들지 않는다. 자료가 모자라 탐지할 수 없는 행은 숨기지 않고 데이터 품질 목록에 둔다 [DESIGN: 구 개발계획 §4.1].
- `case`의 `month`·`baseline_month`와 typed claim의 `period`·`baseline_period`는 이름만 다르고 형식(`YYYYMM`)은 같다.

#### 2.3.6 `peer_group` — 비교 대상 집합의 한 행

| 필드 | 형식 | 뜻 |
|---|---|---|
| `entity_type` | 문자열 | 대상 단위. 값은 `exporter_country`(수출국)다 |
| `entity_id`, `entity_namespace` | 문자열 | 대상국 코드와 코드 체계(`KCS_cntyCd`). BACI 국가 코드는 `baci_country_code` 열에 따로 둔다 |
| `scope_type`, `scope_id` | 문자열 | 유사도를 계산한 품목 범위. 원문 예시는 `hs2:85`(HS85 전체)와 `hs4:8504`다. 저장할 때는 두 필드로 나눠 적는다. 예: `hs2:85`는 `scope_type`=`hs2`, `scope_id`=`85`다. `g1`도 같게 저장한다 [DESIGN] |
| `peer_rank`, `peer_id`, `similarity` | 정수, 문자열, 수 | 순위(1부터 k까지), 비교국 코드, 코사인 유사도(두 벡터가 얼마나 닮았는지 나타내는 값, 1에 가까울수록 비슷) |
| `community_id` | 문자열 | Louvain 커뮤니티 라벨(국가 네트워크를 나눈 무리의 이름표). 문맥 표시용이며 판정에 쓰지 않는다 |
| `method`, `grouping_version`, `params_hash` | 문자열 | 계산 방법(`cosine_topk`), 그룹핑 버전(`g1`), 계산 매개변수의 해시 |
| `source_version`, `source_year`, `input_sha256` | 문자열, 정수, 문자열 | 입력 자료 버전(`BACI_HS22_V202601`), 기준연도(2023), 입력 파일 sha256 |
| `generated_at` | KST ISO 8601 시각 | 생성 시각 |

- 원문 예시값(`CN`, `VN`, 0.83)은 형식을 보여 주는 예일 뿐 계산 결과가 아니다 [사실: 분담 §4].
- `g1` 방법은 분담 §3 초안을 그대로 쓴다. 수출국마다 2023년 BACI HS22 전세계 대상 HS85(전기기기와 그 부분품을 담은 HS 제85류) 안 HS6 수출 바구니(금액 비중)를 벡터로 삼아 코사인 유사도를 잰다. 대상국 p마다 16개국 superset(수집한 상대국 16개 전체 집합) 안에서 상위 5개국(p 제외)을 고른다 [DESIGN: 명세 §3.4].
- 대만(`TW`)은 BACI 490(S19, "Asia n.e.s.")에 대응하며 그 주석을 남긴다 [DESIGN: 명세 §3.4].
- `g0`(고정 목록)도 같은 객체 형식으로 적는다. 필드 값은 다음과 같다 [DESIGN].
  - `scope_type`=`hs6`, `scope_id`=대상 HS6 코드(예: `850450`). 원문 예시(`hs2:85`, `hs4:8504`)처럼 소문자로 적는다.
  - `method`=`import_value_topk`: 대상국을 뺀 나머지 15개국에서, v2 부모 HS6 행(§2.3.2)의 2023년 1~12월 수입금액 합(`OBSERVED` 행)이 큰 순서로 5개국(k=5, 조정값)을 고른다. `g1`의 "상위 5개국(p 제외)"과 같게 늘 5개국이다. 합이 같으면 국가 코드 사전순으로 정한다. 명세 §3.4의 "16개국 안에서 고르고, 대상국 자신은 뺀다"를 대상국을 먼저 빼고 고르는 것으로 읽은 결과다.
  - 명세 §3.4 문장은 "상위 5개국에서 대상국을 빼는" 뜻으로도 읽히지만(그 경우 비교국 4~5개) 다른 해석은 쓰지 않는다. 비교국 확정(명세 §3.10 "품목·국가 확정")은 2026-09-24(목) 사용자 확인으로 위 해석을 정했다 [DESIGN: 2026-09-24(목) 사용자 결정, 결정 기록 `20260924-2212-user-decision-snapshot-build-and-g0.md` ②].
  - `peer_rank`는 1~5(금액 큰 순), `peer_id`는 비교국 코드다.
  - `grouping_version`=`g0`, `source_version`=`kcs_202201_202412_v2`, `source_year`=2023, `input_sha256`=v2의 `raw_sha256`(raw 응답 결합 해시)이다. `normalized_sha256`은 승격 빌드에 따라 바뀌므로 쓰지 않는다.
  - 유사도와 커뮤니티를 쓰지 않으므로 `similarity`와 `community_id`는 `null`이다. `params_hash`는 매개변수(k, 기준연도, 후보국 목록)의 해시다.
- 합성 자료(`controlled_fixture_v0`, `dev20`, `holdout40`)의 비교 대상은 자료 안의 합성 `peer_group`으로 정해지며 `g0`/`g1`과 무관하다 [DESIGN: 명세 §3.4].
- 비교 대상이 superset 밖의 국가를 가리키면 그 국가는 `NOT_COLLECTED`로 처리한다. 미수집 국가를 "변화 없음"으로 보지 않는다 [DESIGN: 분담 D8, 구 개발계획 §4.3].
- 그룹핑은 비교 대상 선택과 문맥 표시에만 쓰고 판정 신호로 쓰지 않는다. 신호는 2개(`unit_value`, `share`)로 유지한다 [DESIGN: 명세 §3.4].

### 2.4 객체 사이 관계

```text
snapshot 1 ─┬─ N observation         (snapshot_id)
            ├─ N collection_receipt  (observation.request_id → collection_receipt.request_id)
            └─ N peer_group          (스냅샷 SQLite의 peer_group 테이블)
metric.evidence_ids ──→ 스냅샷 행(주로 observation)          (§4.4 근거 ID)
case ──→ snapshot_id, policy_version
도구 봉투(§5)·보고서(§9)·실행 기록(§8) ──→ case_id로 사례를 가리킨다
```

## 3. 상태값

**명세 §4.1 원문**

| 코드 | 한국어 표기 | 쓰는 곳 |
|---|---|---|
| `MAINTAIN` | 검토 유지 | 신호별·사례별 |
| `MONITOR` | 모니터링 | 신호별·사례별 |
| `HOLD` | 자료 보류 | 신호별·사례별 |
| `NOT_TRIGGERED` | 미발동 | 신호별만 |

- 신호 코드는 `unit_value`, `share`이다.
- 신호 발동 여부 `signal_trigger`: `TRIGGERED | NOT_TRIGGERED`
- 신호별 판정 `signal_status`: `MAINTAIN | MONITOR | HOLD | NOT_TRIGGERED`
- 사례에는 `unresolved_evidence`(참/거짓)를 붙인다.
- 사례의 처음 표시 상태 코드는 `PRE_INVESTIGATION`(표기 "조사 전 경보")이다. 판정 상태가 아니다.
- 실행이 `COMPLETED`가 아니면 `review_status_final`은 `null`이다.
- 기존 `eval/dev/oracle_ABC.json`은 한국어 표기("모니터링" 등)와 `TRIGGERED`를 쓴다. 이 파일은 고치지 않고, 위 표로 코드와 대응시킨다.

**명세 §4.2 원문**

`COMPLETED | FAILED | TIMEOUT | INVALID | BUDGET_EXCEEDED`

**명세 §4.3 원문**

`OBSERVED | NOT_COLLECTED | REQUEST_FAILED | UNRESOLVED_ZERO | CONFIRMED_NO_TRADE`. 수입 0이 명시된 달은 `OBSERVED`(값 0)이다.

### 3.1 판정 상태 풀이

- 업무 판정(`review_status`)과 실행 결과(`execution_status`)는 따로 기록한다 [DESIGN: 명세 §3.3].
- 상태마다 언제 쓰는지는 신호별 판정표(구 개발계획 §5.1 유지분)를 따른다 [DESIGN: 명세 §3.3].

| 코드 | 언제 쓰나 |
|---|---|
| `HOLD` | 필요한 월·단위·HS 정의·분모·구성자료가 없어 검증할 수 없을 때. 작은 기준월 값이나 반올림 때문에 방향이나 충족 여부가 불안정할 때 |
| `MONITOR` | 완전한 하위자료에서 구성효과(하위품목 비중 변화 때문에 생긴 평균 단가 변화, `mix_effect`)로 설명되고 개별 하위변동·잔차가 기준 안일 때. 자료 교정 뒤 동결 정책으로 경보가 해소됐을 때("정상 확정" 문구는 쓰지 않는다) |
| `MAINTAIN` | 필수 비교를 마쳤는데 설명되지 않거나 설명이 충돌할 때 |
| `NOT_TRIGGERED` | 그 신호가 발동하지 않았을 때(신호별만) |

- 다른 상대국도 비슷하게 변했다는 사실만으로는 등급을 낮추지 않는다. 분모가 줄어 점유율이 오른 것은 "산술 설명"일 뿐 하향 사유가 아니다 [DESIGN].
- 사례 상태는 조사의 완결성이 아니라 담당자의 다음 업무를 뜻한다 [DESIGN].
- 사례 집계 [DESIGN: 명세 §3.3]
  - 우선순위는 `MAINTAIN > HOLD > MONITOR`다.
  - `MAINTAIN`과 `HOLD`가 섞이면 결과는 `MAINTAIN`이고 `unresolved_evidence=true`를 붙인다. 그 밖의 경우 `unresolved_evidence`는 `false`다 [추론: 명세 §3.3 집계 규칙].
  - 발동한 신호가 모두 `MONITOR`일 때만 사례가 `MONITOR`다.
- 키별 쓰임 [DESIGN]

| 키 | 붙는 곳 | 값 |
|---|---|---|
| `signal_trigger` | `case`의 `signals` 안 신호별 값 | `TRIGGERED`, `NOT_TRIGGERED` |
| `signal_status` | 실행 기록(§8), 보고서(§9) | 신호 코드를 키로 하는 객체. 값은 `MAINTAIN`, `MONITOR`, `HOLD`, `NOT_TRIGGERED` 중 하나 |
| `review_status` | 보고서(§9) | 사례 상태 `MAINTAIN`, `MONITOR`, `HOLD` 중 하나 |
| `review_status_final` | 실행 기록(§8) | 실행이 `COMPLETED`면 최종 보고서의 `review_status`, 아니면 `null` |
| `unresolved_evidence` | 실행 기록, 보고서 | `true` 또는 `false` |

- `signal_status` 형식 예시: `{"unit_value": "MONITOR", "share": "NOT_TRIGGERED"}`
- `PRE_INVESTIGATION`은 화면·보고서가 사례를 처음 보여 줄 때("조사 전 경보")만 쓰는 표시 코드다. `review_status`, `review_status_final`, `signal_status`의 값으로 쓰지 않는다 [DESIGN: 명세 §4.1]. 처음 상태가 검토 유지였다가 바뀐 것처럼 이력을 꾸미지 않는다 [DESIGN: 구 개발계획 §10].

### 3.2 oracle_ABC 대응

`eval/dev/oracle_ABC.json`은 고치지 않는다. 그 파일의 표기는 아래처럼 계약 코드와 대응시킨다 [사실: oracle].

| oracle 표기 | oracle 안 위치 | 계약 코드 | 계약 키 |
|---|---|---|---|
| `"검토 유지"` | `expected.review_status` | `MAINTAIN` | `review_status` |
| `"모니터링"` | `expected.review_status` | `MONITOR` | `review_status` |
| `"자료 보류"` | `expected.review_status` | `HOLD` | `review_status` |
| `"TRIGGERED"` | `expected.signals` | `TRIGGERED` | `signal_trigger` |
| `"NOT_TRIGGERED"` | `expected.signals` | `NOT_TRIGGERED` | `signal_trigger` |
| `"triggered": false` | `expected.share` | `NOT_TRIGGERED` | `signal_trigger` |
| `"REQUEST_FAILED"` | C 사례 `comparison.hs10` | `REQUEST_FAILED` | `observation_status` |
| `"dev-0.1 (…)"` | 최상위 `policy_version` | 개발용 임시 정책 표기이며 `policy_v1`이 아니다 | `policy_version` |

사례별 기대 판정은 다음과 같다 [사실: oracle의 `signals`·`review_status`] [추론: 발동 신호가 하나뿐이면 사례 상태가 그 신호의 상태와 같다].

| oracle `case_id` | 사례 상태 | `signal_status` |
|---|---|---|
| `A-composition` | `MONITOR` | `unit_value`=`MONITOR`, `share`=`NOT_TRIGGERED` |
| `B-residual` | `MAINTAIN` | `unit_value`=`MAINTAIN`, `share`=`NOT_TRIGGERED` |
| `C-missing-hs10` | `HOLD` | `unit_value`=`HOLD`, `share`=`NOT_TRIGGERED` |

- oracle의 숫자 키 대응은 §11.5에 있다.
- oracle은 합성 설계 예제다. 통계 실행 결과나 실제 사건이 아니다 [사실: oracle `_status`].

### 3.3 실행 상태 풀이

| 코드 | 뜻 |
|---|---|
| `COMPLETED` | 한도 안에서 유효한 최종 보고서까지 끝났다 |
| `FAILED` | 아래 셋에 들지 않는 실행 실패(예: 명시 재전송 뒤에도 남은 모델 호출 오류, 코드 오류) |
| `TIMEOUT` | 사례당 wall time(실제 경과 시간) 한도 300초(조정값: 운영하며 바꿀 수 있는 수치)에 먼저 닿아 멈췄다 |
| `INVALID` | 스키마 검사(보고서가 정해진 필드·형식을 갖췄는지 보는 검사)나 검증기(실행 중에 보고서의 숫자·근거·상태를 검사해 잘못된 보고서를 막는 코드)를 수정 1회 뒤에도 통과하지 못했다. 단 `freeform`은 검증기가 기록 전용이므로 스키마 검사 실패만 `INVALID`다. `checklist`는 모델이 없어 수정 단계가 없으므로, 검증기가 막으면 수정 없이 곧바로 `INVALID`다(새 상태값 없음) [DESIGN: 2026-09-24(목) 사용자 결정, 결정 기록 20260924-2315 D1]. 스키마 요건은 §9.4를 본다 |
| `BUDGET_EXCEEDED` | 모델 요청 10회나 누적 토큰(모델이 글을 잘게 나눠 세는 단위) 32,000(모두 조정값) 한도에 먼저 닿아 멈췄다 |

- 위 대응은 구 개발계획 §5.3의 "타임아웃/스키마 실패/코드 검증 실패/예산 소진으로 미완료인 실행은 `FAILED/TIMEOUT/INVALID/BUDGET_EXCEEDED`로 남고"를 풀어 쓴 것이다 [추론]. 구현 때 이 대응을 시험으로 고정한다.
- `COMPLETED`가 아닌 실행은 공유 승인할 수 없고 평가에서 성공으로 치지 않는다. 그래도 분모에는 남는다 [DESIGN: 명세 §3.3, §3.6].
- 한도에 닿아 멈출 때는 실패 원인, 누적 시도, 마지막 정상 근거를 `errors`(§8)에 남긴다 [DESIGN].
- 코드는 모델의 틀린 상태를 조용히 정답으로 고치지 않는다 [DESIGN: 명세 §3.3].

### 3.4 관측 상태 풀이

| 코드 | 뜻 | 기존 수집기의 처리 [사실: 수집기] | 기존 `verify` 월 분류 [사실: 수집기] |
|---|---|---|---|
| `OBSERVED` | 응답에 그 달 행이 있다. 수입 0이 명시된 달도 여기에 들고 값은 0이다 | 응답 행마다 기록한다 | `import_pos`, `import_zero_explicit` |
| `NOT_COLLECTED` | 그 달을 맡은 요청이 없거나 실행되지 않았다. v1에서는 `snapshot-build`가 값 없는 행을 만든다(표 아래) | 행을 쓰지 않는다. 수집 계획에 있는데 receipt가 없으면 미수집으로 센다 | `not_collected` |
| `REQUEST_FAILED` | 요청이 실패했다 | 처음부터 실패한 요청이 맡은 월마다 값 없는 행을 쓴다 | `failed` |
| `UNRESOLVED_ZERO` | 요청은 성공(`resultCode 00`: API의 정상 처리 결과 코드)했는데 그 달 행이 없다. 0으로 바꾸지 않는다 | 요청 범위 안에서 빠진 월마다 값 없는 행을 쓴다 | `no_response` |
| `CONFIRMED_NO_TRADE` | 승인된 규칙으로만 승격되는 무거래 확정 | 쓰지 않는다. `verify`는 후보만 나열한다 | 해당 없음 |

- v2 실측: 수입 0이 명시된 달이 68개월, `UNRESOLVED_ZERO`가 208개월(전부 무거래 후보 규칙에 해당), 금액>0인데 중량 0인 행이 677개다 [사실: 메모 §3].
- `CONFIRMED_NO_TRADE` 승격 규칙과 수입 0 명시 달의 처리는 D가 개발 묶음(`real_dev`)으로 제안하고 사용자가 승인해 `configs/policy_v1.json`에 적는다 [DESIGN: 명세 §3.3].
- `NOT_COLLECTED` 행 만들기: 기존 수집기는 미수집 행을 쓰지 않지만 [사실: 수집기], v1에서는 `snapshot-build`가 수집 계획이나 비교 대상에 필요한데 수집 기록이 없는 키(월, 상대국, HS 코드, 흐름)마다 `NOT_COLLECTED` 관측 행(값 `null`)을 만든다. `request_id`에는 그 키를 맡은 계획 요청의 ID를 적고, 계획에 없던 키는 같은 규칙(§2.3.3)으로 계산한 요청 ID를 적는다. 그래서 근거 ID가 미수집 행을 가리킬 수 있다(§4.4) [DESIGN].
- `CONFIRMED_NO_TRADE` 승격은 승인된 `policy_version`의 규칙에 따라 파생 저장소(`snapshot-build`가 raw 응답과 manifest에서 만드는 SQLite)에만 적용한다. raw 응답과 `manifest.json`은 바꾸지 않는다. 승격은 해당 행의 `observation_status`만 바꾸고 행을 더하거나 지우지 않는다. 그래서 rowid는 그대로이고 `normalized_sha256`은 달라진다(§4.4) [DESIGN].
- 승격된 `CONFIRMED_NO_TRADE` 행의 V·Q 칸(`amount_usd`, `net_weight_kg`)은 `null`로 둔다. 지표와 채점은 이 행을 무역 없음 확정으로 보아 0으로 다룬다. 점유율 분자는 0이고, 기준월 값이 0인 변화율은 `null`이며, 중량이 0이므로 단가는 계산하지 않는다(§11.1의 0·미상 규칙). 룰북 B3-1과 같은 규칙이며, 최종 확인은 `policy_v1` 승격 규칙을 승인할 때 한다 [DESIGN].
- 실패와 미수집을 구분하고 빈 응답을 0으로 채우지 않는다. 도구는 빠진 자료를 봉투의 `missingness`(§5)에 이 코드로 돌려준다 [DESIGN].

## 4. 이름과 ID 규칙

이 절은 모드·출처·이름·근거 ID·스킬 형식을 다룬다. 아래 원문의 Agent Skills는 에이전트가 불러 쓰는 작업 지침 묶음(SKILL.md)의 공개 규격이다.

**명세 §4.4 원문**

- 모드: `checklist | agent | full | freeform`
- 출처 종류 `source_kind`: `real | controlled`

**명세 §4.5 원문**

- 데이터셋: `controlled_fixture_v0`, `dev20`, `holdout40`, `real_dev`, `real_sealed`
- 스냅샷: `kcs_202201_202412_v2`
- 정책: `policy_v1`(`configs/policy_v1.json`)
- 비교 대상: `g0`(고정 목록), `g1`(BACI 유사도)
- 룰북: `RB-1`
- 승인 유효 상태: `VALID | REVIEW_REQUIRED`
- 근거 ID: `ev:<snapshot_id>:<table>:<rowid>`

**명세 §4.11 원문**

- 규격: Agent Skills 규격을 따른다.
- `name`: 디렉터리 이름과 같다. 소문자·숫자·하이픈만 쓰고 64자 이하다.
- `description`: 무엇을 하는지와 언제 쓰는지를 담고 1024자 이하다. 한국어 본문에 영어 한 문장을 덧붙인다(조정값).

### 4.1 모드와 출처 풀이

| 모드 | 뜻 |
|---|---|
| `checklist` | 고정 체크리스트. 모델을 쓰지 않는다 |
| `agent` | Critic 없는 Nemotron |
| `full` | 전체 TradeSentry(조사자 + Critic + 수정 1회 + 검증기 차단) |
| `freeform` | 대표 지표의 기준선. `full`과 처리만 다르다. typed claim의 값을 모델이 직접 쓰고, 검증기는 막지 않고 기록만 한다 |

- 모든 모드에 같은 자료·도구·정책·한도·재시도 규칙을 쓴다. CLI(명령줄 실행 도구 `tradesentry <명령>`) 공통 옵션 `--mode`의 값이 이 네 개다 [DESIGN: 명세 §3.6, §4.12].
- `source_kind`: `real`은 관세청 실자료 스냅샷이고, `controlled`는 합성 자료(`controlled_fixture_v0`, `dev20`, `holdout40`)다 [DESIGN].

### 4.2 이름 풀이

| 이름 | 뜻 |
|---|---|
| `controlled_fixture_v0` | D가 먼저 넘기는 합성 시험자료. A/B/C 사례를 포함한다. 구성은 분담 D6(3 HS6 × 10국 × 36개월 + HS10 2개월 + peer_group + 수집 기록 + A/B/C, 규모는 조정값)을 따른다 |
| `dev20` | 공개 개발 자료 20건. 모든 에이전트가 쓴다 |
| `holdout40` | 봉인 평가 자료 40건(§12) |
| `real_dev` | 실자료 개발 묶음. 기준값·최소 기준은 이 묶음만으로 조정한다. 개발 값이라 대표 숫자로 올리지 않는다. 그 밖의 용도는 MVP 시험의 대표 지표 첫 값("개발 묶음 값, 대표 숫자 아님"으로 표기), 산문 패턴 누락 사례 보강(이 묶음에서만 한다), NemoClaw(에이전트 실행 틀과 보안 런타임을 묶은 NVIDIA 참조 스택) 경로 시연이다 |
| `real_sealed` | 실자료 봉인 묶음. 동결된 `policy_v1`로 여기서 나온 경보가 대표 지표의 채점 대상이다. 표본 상한은 40건(조정값)이고, 넘으면 고정 난수로 표본을 뽑는다(§12) |
| `kcs_202201_202412_v2` | 실자료 스냅샷. 2022-01~2024-12(36개월). 분석 대상은 HS4 `8504`(변압기·정지형 변환기·인덕터) 아래 HS6 4개(`850450` 기타 인덕터, `850431` 변압기 1kVA(킬로볼트암페어, 변압기 용량 단위) 이하, `850432` 변압기 1kVA 초과 16kVA 이하, `850490` 부분품) × 상대국 16개(`CN`, `JP`, `DE`, `VN`, `US`, `PH`, `TW`, `FR`, `FI`, `SE`, `KH`, `NL`, `ID`, `IN`, `MX`, `MY`)와 전체국가 `ALL`이다. 선정용으로 함께 수집한 HS4 스캔(`8544`, `8536`)과 `8504`의 다른 HS6 행은 범위 밖이다(§2.3.2). 추가 수집 없이 그대로 동결한다 |
| `policy_v1` | 동결 판정 정책. 수치는 `configs/policy_v1.json`에 둔다 |
| `dev-0.1` | 개발용 정책. 수치는 `configs/policy_dev.json`(oracle 기준값)에 두며 승인 전 실행용이다(결정 기록 `20260924-2315-user-decision-impl-plan-approval.md` D2). 봉인 묶음 채점에는 쓰지 않는다(봉인 묶음은 동결된 `policy_v1`로 채점한다) |
| `g0` | HS6별 v2의 2023년 연간 수입금액 상위 k개국(대상국을 뺀 15개국 안, k=5는 조정값, 필드 값과 해석은 §2.3.6, 비교국 확정은 2026-09-24(목) 사용자 확인)의 고정 목록. 2026-09-25(금) MVP 시험까지 쓰고, 그 뒤에는 비교표로 남긴다. 경보 결과를 보고 바꾸지 않는다 |
| `g1` | BACI 유사도 방식의 비교 대상. 동결되면 MVP 이후 모든 채점 대상 실행(샌드박스 안에서 돌리는 실행)의 기본값이 된다. 룰북 동결 시한까지 동결되지 않으면 `g0`로 채점하고 제출서에 사실대로 적는다 |
| `RB-1` | 평가 룰북의 동결 버전. 2026-09-26(토) 12:00(조정값)에 동결한다 |
| `VALID`, `REVIEW_REQUIRED` | 승인 기록의 유효 상태(§9.3) |

[DESIGN: 명세 §3.2, §3.4, §3.6]

- `real_dev`와 `real_sealed`는 같은 스냅샷 `kcs_202201_202412_v2`를 품목×국가 시계열 64개 단위로 나눈 묶음이다. 기준값 조정 전에 고정 난수로 먼저 나누고, 같은 시계열이 양쪽에 섞이지 않게 한다. 분할 비율(1:2)과 seed(난수를 다시 똑같이 뽑기 위한 시작값)는 조정값이며 기록한다 [DESIGN: 명세 §3.6]. 두 묶음이 같은 스냅샷에 있으므로 실행 기록은 `dataset`과 `snapshot_id`를 따로 적는다.
- 분할 seed·비율·시계열 배정은 D가 `policy_v1` 수치를 제안하기 전에 결정 기록(`docs/tracking/decisions/`)으로 커밋한다. 이 커밋이 기준값 조정 전에 나눴다는 증거가 된다. 같은 결정 기록에 `real_sealed` 표본 추출 seed 파일(nonce, 즉 추측을 막으려고 섞는 한 번 쓰는 임의 값을 포함)의 sha256도 함께 커밋한다. 사례 목록을 계산할 수 있게 되기 전에 표본 seed를 골랐다는 증거다. seed 파일(nonce 포함) 자체는 채점 뒤에 공개한다(§12.3). nonce가 있어야 미리 커밋한 sha256으로 검증할 수 있기 때문이다 [DESIGN].

### 4.3 스킬 형식 풀이

- 경로 표(§10)에 있는 스킬은 런타임 스킬 `skills/tradesentry/SKILL.md`와 평가 스킬 `skills/tradesentry-scorecard/SKILL.md`, `skills/tradesentry-eval/SKILL.md`다. `name`은 디렉터리 이름과 같으므로 각각 `tradesentry`, `tradesentry-scorecard`, `tradesentry-eval`이다 [추론: 명세 §4.11 규칙].
- SKILL.md(스킬 하나의 작업 지침 파일)의 frontmatter(파일 맨 앞 `---` 두 줄 사이의 메타데이터)에 `name`과 `description`을 둔다 [DESIGN].

### 4.4 근거 ID 형식과 해석 규칙

근거 ID(evidence ID)는 주장이나 지표가 기대는 스냅샷 행 하나를 가리키는 문자열이다. 형식은 `ev:<snapshot_id>:<table>:<rowid>`다 [DESIGN: 명세 §4.5, 분담 D7].

| 조각 | 뜻 | 규칙 |
|---|---|---|
| `ev` | 근거 ID임을 나타내는 고정 접두어 | 소문자 `ev` 그대로 |
| `<snapshot_id>` | 행이 있는 스냅샷 | `snapshot` 객체의 `snapshot_id`. `:`를 넣지 않는다 |
| `<table>` | 스냅샷 SQLite(파일 하나로 된 데이터베이스)의 테이블 이름 | 예: `observation`, `collection_receipt`, `peer_group`. `:`를 넣지 않는다 |
| `<rowid>` | 그 테이블의 rowid(SQLite가 행마다 붙이는 정수 번호) | 10진수 양의 정수 |

형식 예시(합성, 실제 행 아님): `ev:controlled_fixture_v0:observation:1024`

**가리키는 대상** [DESIGN]

- 근거 ID는 동결 스냅샷의 행만 가리킨다. 계산한 지표 값에는 근거 ID를 붙이지 않는다. 대신 `metric` 객체가 입력 행의 근거 ID를 `evidence_ids`로 가진다.
- 점유율의 분자 근거는 상대국의 부모 HS6 행이고, 분모 근거는 그 HS6 아래 `ALL` HS10 월 행(중복 제거 뒤)이다(§2.3.2 행 규칙).
- 총계 행(`month`=`RAW:총계`)은 대조 전용이므로 근거 ID로 쓰지 않는다.
- `snapshot-build`가 만든 `NOT_COLLECTED` 행(§3.4)도 근거 ID로 가리킬 수 있다. 미수집을 말하는 주장은 이 행을 근거로 삼는다.
- 원본까지 추적하는 길은 `observation` 행 → `raw_file_id`·`raw_row_locator` → raw 응답 파일의 행이다.

**해석(풀림) 규칙** [DESIGN]

다음 네 가지를 모두 만족하면 근거 ID가 "풀린다"(가리키는 행을 찾았다).

1. `:`로 나눈 조각이 정확히 4개이고 첫 조각이 `ev`다.
2. `<snapshot_id>`가 그 보고서·실행 기록의 `snapshot_id`와 같다.
3. 그 스냅샷에 `<table>` 테이블이 있다.
4. 그 테이블에 rowid가 `<rowid>`인 행이 있다.

- 하나라도 어긋나면 풀리지 않는다. 근거 ID가 없거나, 풀리지 않거나, 풀린 행이 주장을 뒷받침하지 않으면 주장 채점 결과는 `UNSUPPORTED`다(§7). "뒷받침"의 판정(행의 품목·상대국·월·값이 주장과 맞는가)은 룰북 B3-1(필드별 채점 규칙)을 따른다.
- 실행 중 검증기(`validator/` 패키지)와 샌드박스(허용한 파일·네트워크만 쓰게 격리한 실행 환경) 밖 독립 채점기(`eval/scorer/`)는 같은 규칙으로 근거 ID를 푼다.

**rowid 안정성**

- 기존 `observation` 테이블은 정수 기본 키 없이 여러 열을 묶은 기본 키를 쓰므로 rowid가 따로 붙는다 [사실: 수집기 테이블 정의].
- 기존 수집기는 같은 요청을 다시 수집해 성공하면 그 요청의 행을 지우고 새로 넣는다 [사실: 수집기 `store_result`]. 이런 재적재나 VACUUM(SQLite 파일을 다시 써서 정리하는 명령) 때 rowid가 바뀔 수 있다 [추론].
- 그래서 다음 규칙을 둔다 [DESIGN].
  1. `snapshot-build`는 행 순서가 결정적이어야 한다. 같은 raw 응답·manifest·승인된 `policy_version`으로 다시 빌드하면 같은 행이 같은 순서로 들어가 같은 rowid를 받는다.
  2. raw 응답이나 manifest가 바뀌는 재수집은 새 `snapshot_id`로만 한다.
  3. 동결한 SQLite 파일에는 VACUUM을 포함해 파일을 다시 쓰는 작업을 하지 않는다.
  4. 채점 전에 스냅샷의 `normalized_sha256`을 다시 계산해 기록값과 대조한다. 기록값은 SQLite 밖의 커밋된 기록(결정 기록이나 스냅샷 폴더의 해시 파일)에 둔다. v2의 `snapshot_hash.json`에는 지금 raw 해시만 있으므로, D가 `snapshot-build`를 구현할 때 `normalized_sha256`을 그 파일이나 결정 기록에 더해 커밋한다(§2.1 표의 `normalized_sha256` 행). SQLite 안의 값과 비교하면 자기 자신과 대조하는 셈이기 때문이다. 다르면 그 스냅샷으로 채점하지 않고 사용자에게 올린다.
  5. 채점 결과 요약 `scorer_summary-{시각}.md`에 스냅샷 해시(`normalized_sha256`), 채점기 커밋 해시, 산문 패턴 목록 버전을 적는다(§8.2).

### 4.5 그 밖의 ID

| ID | 붙는 곳 | 요구 [DESIGN] |
|---|---|---|
| `case_id` | `case`, 도구 입력, 실행 기록, 보고서 | 사례마다 고유 |
| `run_id` | 실행 기록, 보고서, 주장 채점 기록 | 사례 실행(한 사례를 한 모드로 한 번 돌린 것)마다 고유. 형식은 실행명 `{실행 이름}-{yymmddhhmmss}`다(§10.3 N5) [DESIGN: 사용자 결정(이름 형식) + 오케스트레이터 정리(run_id 연결), 2026-09-24(목) 사용자 확인(PR #18)]. 실행명을 확보하는 방법은 §10.3 N8이다 |
| `report_id` | 보고서, 주장 채점 기록 | 보고서마다 고유. 내용이 바뀌면 새 보고서와 새 ID |
| `claim_id` | typed claim, 주장 채점 기록 | 한 보고서 안에서 고유 |
| `query_id` | 도구 봉투 | 도구 호출 1회마다 고유 |
| `metric_id` | `metric` | 지표 값마다 고유 |
| `request_id` | `collection_receipt`, `observation` | 기존 수집기 규칙(§2.3.3)을 그대로 쓴다 [사실: 수집기] |

- 한 번 붙인 ID는 바꾸지 않고 다른 대상에 다시 쓰지 않는다. `request_id`와 `run_id`를 뺀 ID의 문자열 형식은 v1에서 정하지 않는다 [DESIGN]. `run_id`의 형식은 2026-09-24(목) 사용자 결정의 이름 형식을 오케스트레이터가 `run_id`에 이은 것이다(§10.3 N5) [DESIGN: 사용자 결정(이름 형식) + 오케스트레이터 정리(run_id 연결), 2026-09-24(목) 사용자 확인(PR #18)].

## 5. 도구 입출력 봉투

도구 봉투(envelope)는 도구 5개가 똑같은 모양으로 돌려주는 출력 틀이다.

**명세 §4.6 원문**

`query_id, tool, scope, snapshot_id, source_kind, evidence_ids, metrics, comparability, missingness, retryable_error, elapsed_ms`

### 5.1 도구와 입력

- 도구 5개: `check_comparability`, `get_history`, `compare_partners`, `decompose_hs`, `verify_evidence` [DESIGN: 명세 §3.3]
- 공통 입력: `case_id`, `snapshot_id`, 허용된 scope(사례가 허용하는 조회 범위) [DESIGN: 명세 §3.3]
  - scope는 사례의 HS6, 대상국, 비교 대상 집합(`peer_group`), 비교월과 기준월, 필요한 HS10 하위품목 안에서만 정해진다. 범위 객체의 세부 모양은 M이 도구(`tools/` 패키지)를 구현할 때 정한다. D의 자료 접근층(`dal/` 패키지)은 그 범위의 행만 돌려준다 [DESIGN: 분담 D7].
- 모델 인자로 DB 경로·SQL·외부 URL·셸 명령을 받지 않는다. 도구가 돌려준 품목명·설명은 데이터로만 다루고 지시문으로 실행하지 않는다 [DESIGN: 명세 §3.3].

### 5.2 출력 봉투 키 풀이

| 키 | 형식 | 뜻 |
|---|---|---|
| `query_id` | 문자열 | 이 도구 호출의 고유 ID |
| `tool` | 문자열 | 도구 이름(5개 중 하나) |
| `scope` | 객체 | 실제로 조회한 범위(요청한 범위가 아니라 실제 범위) [사실: 구 개발계획 §5.2 "실제 scope"] |
| `snapshot_id` | 문자열 | 조회한 스냅샷 |
| `source_kind` | 문자열 | `real` 또는 `controlled` |
| `evidence_ids` | 근거 ID 목록 | 이 호출이 돌려준 근거(§4.4) |
| `metrics` | `metric` 객체 목록 | 이 호출이 계산한 지표(§2.3.4) |
| `comparability` | 객체 | 비교 조건 점검 결과. 기간·요청 완료·단위·HS 버전·분모·하위자료의 존재 상태를 담는다 [사실: 구 개발계획 §5.2] |
| `missingness` | 목록 | 빠진 자료와 그 관측 상태(§3.4). 실패와 미수집을 구분한다 |
| `retryable_error` | 객체 또는 `null` | 다시 시도할 수 있는 오류가 있으면 그 내용, 없으면 `null` [DESIGN] |
| `elapsed_ms` | 정수 | 도구 실행에 걸린 시간(밀리초) |

- 구 개발계획 §5.2의 출력 목록에 비해 `tool` 키가 더해졌다 [사실].
- 봉투의 키 11개는 늘 모두 있다. 해당 값이 없으면 빈 목록이나 `null`을 쓴다 [DESIGN].

### 5.3 예산 세기

- 도구 호출 시도는 `tool_attempts ≤ 8`이다. 실패·같은 도구 재호출·캐시 적중·`verify_evidence`를 모두 센다. 기본 경로 ≤5, 재조회 ≤2, 최종 검증 1이다 [DESIGN: 명세 §3.3].
- 재조사(수정 단계)는 1회이고, 그 안에서 조회는 최대 2회다. Critic은 도구를 부르지 않는다 [DESIGN: 명세 §3.3].
- 조기 종료·호출 한도·같은 인자 재호출 차단은 프롬프트가 아니라 코드가 강제한다. 구 개발계획 G4 관문 시험(NIM으로 모델의 도구 호출 왕복을 확인한 시험. NIM은 NVIDIA가 모델을 API로 제공하는 추론 서비스)에서 모델이 "추가 조회 없이 보류" 지시를 어기고 도구를 부른 적이 있다 [사실: 메모 §5].
- `verify_evidence`는 다른 도구를 다시 부르지 않고, 새 비교 근거를 만들지 않으며, 평가 정답 파일을 보지 않는다 [DESIGN: 구 개발계획 §5.2].
- 외부 수집 HTTP 시도(`collection_http_attempts`)와 모델 요청 수는 `tool_attempts`에 섞지 않는다 [사실: 구 개발계획 §5.3].

## 6. typed claim

typed claim은 정해진 필드를 가진 사실 주장 1건이다. 보고서의 모든 사실 주장은 이 형식으로 낸다 [DESIGN: 명세 §3.3].

**명세 §4.8 원문**

- 필드: `claim_id, claim_type, hs6, partner, period, baseline_period, metric, value, unit, direction, evidence_ids, text`
- `claim_type`: `value | change | share | share_change | decomposition | comparison | data_status`
- `direction`: `UP | DOWN | FLAT | NA`

### 6.1 필드 풀이

| 필드 | 형식 | 뜻 |
|---|---|---|
| `claim_id` | 문자열 | 보고서 안에서 고유한 주장 ID |
| `claim_type` | 문자열 | 주장 종류(§6.2) |
| `hs6` | 문자열 6자 | 품목(HS6). HS10 하위품목 주장에서는 부모 HS6 |
| `partner` | 문자열 | 상대국 코드(`KCS_cntyCd` 체계). 전체국가 합계를 말하면 `ALL` |
| `period` | `YYYYMM` | 값이 가리키는 월 |
| `baseline_period` | `YYYYMM` 또는 `null` | 기준월. 변화를 말하지 않는 주장은 `null` |
| `metric` | 문자열 | 지표 기호(§11.2). `data_status` 주장은 `observation_status`. HS10 하위품목을 말하면 §6.2에서 정의한 `@` 기호(`U@`, `r_U@`, `w@`, `observation_status@` 뒤에 HS10 코드) |
| `value` | 수, 문자열 또는 `null` | 주장한 값. `data_status` 주장은 관측 상태 코드(§3.4) |
| `unit` | 문자열 또는 `null` | 단위(§11.2). 단위가 없는 주장은 `null` |
| `direction` | 문자열 | `UP`(증가), `DOWN`(감소), `FLAT`(변화 없음), `NA`(방향을 말하지 않는 주장) |
| `evidence_ids` | 근거 ID 목록 | 주장을 뒷받침하는 스냅샷 행(§4.4) |
| `text` | 문자열 | 이 주장을 나타내는 한국어 문장 |

- typed claim의 `metric` 필드는 지표 기호(문자열)이며, §2의 `metric` 객체와 다르다.

### 6.2 `claim_type` 풀이 [DESIGN]

| 값 | 뜻 | `metric` 예 | `baseline_period` | `direction` |
|---|---|---|---|---|
| `value` | 한 시점의 값 | `U`, `V`, `Q`, `U@<HS10 코드>`, `w@<HS10 코드>` | `null` | `NA` |
| `change` | 전년동월 대비 변화율 | `r_U`, `r_U@<HS10 코드>` | 필요 | `UP`, `DOWN`, `FLAT` |
| `share` | 한 시점의 점유율 | `s` | `null` | `NA` |
| `share_change` | 점유율 변화 | `d_s` | 필요 | `UP`, `DOWN`, `FLAT` |
| `decomposition` | HS10 구성효과 분해 | `within_effect`, `mix_effect`, `residual` | 필요 | `UP`, `DOWN`, `FLAT` |
| `comparison` | 비교 대상 국가의 값이나 변화 | `r_U`, `d_s` 등 | 변화를 말하면 필요 | 변화를 말하면 `UP`, `DOWN`, `FLAT`, 아니면 `NA` |
| `data_status` | 자료 상태 | `observation_status`, `observation_status@<HS10 코드>` | 해당할 때만 | `NA` |

- `comparison` 주장의 `partner`에는 비교국 코드를 적는다.
- 변화 주장(`change`, `share_change`, `decomposition`, 변화를 말하는 `comparison`)의 `value`는 부호가 있는 수이고 `direction`과 맞아야 한다. `FLAT` 경계(룰북 B3-1) 밖의 음수는 `DOWN`, 양수는 `UP`이다. 필드별 채점 순서도 룰북 B3-1이 정한다 [DESIGN].
- HS10 하위품목 주장: 명세 §4.8의 필드는 바꾸지 않고 `metric` 이름으로 하위 대상을 나타낸다. 형식은 `<기호>@<HS10 코드>`이고, 정의한 것은 `U@<HS10 코드>`, `r_U@<HS10 코드>`, `w@<HS10 코드>`(중량 비중, 모니터링 근거용), `observation_status@<HS10 코드>` 넷뿐이다. `within_effect@`, `mix_effect@`, `residual@`처럼 정의하지 않은 조합은 쓰지 않는다. HS10 하위품목 주장의 `hs6`는 부모 HS6다. 채점기도 `@` 뒤 코드를 대상 HS10으로 해석한다 [DESIGN].
- 신호 계열: 주장의 `metric`으로 신호 계열(`unit_value`, `share`)이 정해진다. 대응은 §9.4에 있다.

### 6.3 모드별 채움 [DESIGN: 명세 §3.3, §3.6]

- `full`·`agent`·`checklist`: 숫자(`value`·`unit`)와 `evidence_ids`는 검증된 `metric`에서 틀로 채운다. 모델은 숫자를 직접 쓰지 않는다.
- `freeform`: typed claim의 `value`·`unit`·`evidence_ids`를 모두 모델이 쓴다(틀 채우기 없음). 검증기는 막지 않고, 막았을 사유를 `validator_findings`(§9)에 기록만 한다. 스키마 검사(§9.4)는 다른 모드와 같게 한다.
- 모델의 설명·가설 문장은 보고서의 `narrative`·`hypotheses`에 따로 둔다. 설명 문장에 typed claim으로 뒷받침되지 않는 숫자나 증감 표현이 있으면 검증기가 결정적(같은 입력이면 늘 같은 결과를 내는) 패턴 검사로 막는다(`freeform`은 기록만 한다).
- 보고서 언어는 한국어다.
- `text`·`narrative`·`hypotheses`에서 단가·점유율 변화를 부정·위법·원산지 조작(우회수입, 즉 제3국을 거쳐 원산지를 바꿔 들여오는 수입 포함)·개별 거래가격의 증거로 쓰지 않는다. 보고서는 담당자의 다음 업무(검토 유지·모니터링·자료 보류)만 제시한다 [DESIGN: 명세 §2-10].

### 6.4 형식 예시

oracle A 사례의 -40%를 빌린 합성 예시다. 실제 통계가 아니다.

```json
{
  "claim_id": "c1",
  "claim_type": "change",
  "hs6": "850450",
  "partner": "CN",
  "period": "202401",
  "baseline_period": "202301",
  "metric": "r_U",
  "value": -40.0,
  "unit": "%",
  "direction": "DOWN",
  "evidence_ids": ["ev:controlled_fixture_v0:observation:1024", "ev:controlled_fixture_v0:observation:1025"],
  "text": "2024년 1월 단가가 전년 같은 달보다 40.0% 낮다."
}
```

## 7. 주장 채점 결과

**명세 §4.9 원문**

`CORRECT | WRONG_VALUE | WRONG_DIRECTION | WRONG_UNIT | WRONG_REFERENT | UNSUPPORTED | UNBACKED_PROSE`
- 값 비교 허용오차는 표시 자릿수 반올림 기준이며 조정값이다.
- `WRONG_REFERENT`: 기간·국가·품목·지표가 가리키는 대상이 없거나 다르다.
- `UNSUPPORTED`: 근거 ID가 없거나, 풀리지 않거나, 주장을 뒷받침하지 않는다.

### 7.1 결과 풀이

| 값 | 뜻 |
|---|---|
| `CORRECT` | 주장의 모든 필드가 원본과 맞다 |
| `WRONG_VALUE` | 값이 허용오차 밖이다 |
| `WRONG_DIRECTION` | 증감 방향이 틀렸다 |
| `WRONG_UNIT` | 단위가 틀렸다 |
| `WRONG_REFERENT` | 기간·국가·품목·지표가 가리키는 대상이 없거나 다르다 |
| `UNSUPPORTED` | 근거 ID가 없거나, 풀리지 않거나(§4.4), 주장을 뒷받침하지 않는다 |
| `UNBACKED_PROSE` | 설명 문장 속에 typed claim으로 뒷받침되지 않는 숫자·증감 표현이 있다 |

- `UNBACKED_PROSE`는 산문 패턴으로 잡힌 기록(`source`가 `prose`인 기록, §9.2)에만 쓴다 [추론: 명세 §4.9·§4.10-2의 정의].
- 한 주장에 여러 오류가 겹칠 때 어느 결과를 적는지와 산문 패턴 목록은 룰북 B3-1·B3-2가 정한다.
- `WRONG_VALUE`의 허용오차는 §11.3 표시 자릿수 표를 기준으로 룰북 B3-1이 적용한다.
- 미수집을 말하는 `data_status` 주장은 `snapshot-build`가 만든 `NOT_COLLECTED` 행을 근거로 삼으므로 근거 ID로 뒷받침할 수 있다(§3.4) [DESIGN].

### 7.2 쓰는 곳과 오류율 [DESIGN: 명세 §3.6]

- 주장 채점 기록(§9.2)의 `outcome`에 적고, 채점 실행 폴더의 `scorer_claims-{시각}.jsonl`에 한 줄에 한 건씩 남긴다. 이 파일은 채점기의 다른 출력과 함께 같은 이름의 폴더 `artifacts/eval/score-{시각}/`로 복사해 커밋한다(증거 복사, §10.3 N11).
- 주장 단위 오류율 = `CORRECT`가 아닌 typed claim ÷ 전체 typed claim
- 보고서 단위 오류율 = 오류 claim이나 `UNBACKED_PROSE`가 1개 이상인 보고서 ÷ 전체 보고서
  - 분자: 오류 claim(`CORRECT`가 아닌 typed claim)이나 `UNBACKED_PROSE`가 1개 이상인 보고서, 그리고 보고서 단위 실패다. 보고서 단위 실패는 `execution_status`가 `COMPLETED`가 아닌 실행(스키마 요건 미달로 `INVALID`가 된 실행 포함, §9.4)과 실행되지 않은 사례다.
  - 분모: 그 모드에서 채점할 고정 사례 목록(`dev20`, `holdout40`, `real_dev`, `real_sealed` 봉인 표본)의 사례 수다. 결과 줄 수로 세지 않는다(§8.2).
- `UNBACKED_PROSE`는 보고서당 건수로도 따로 보고한다.
- 유효한 최종 보고서가 없는 실행은 보고서 단위 실패로 분모에 남긴다.
- 주장 단위 분모에 드는 보고서, 산문 기록을 만드는 범위, 산문 검사 필드는 채점 규칙이며 룰북 B3·B3-2가 정한다.

### 7.3 채점 원칙 [DESIGN: 명세 §3.6]

- 공식 통계 원본(스냅샷 raw 행)과 결정적으로(같은 입력이면 늘 같은 결과로) 대조한다. 사람 판정자도 AI 채점자도 두지 않는다.
- 채점 범위는 typed claim의 모든 필드와, 설명 문장 속 숫자·증감 표현이다. 산문은 `RB-1`과 함께 동결하는 결정적 패턴 목록으로 잡고, 누락 사례는 `real_dev`에서만 보강한다. 숫자·증감이 없는 정성 서술의 의미 정확성은 범위 밖이다.
- 정답 계산기(채점기, `eval/scorer/`)는 런타임 `metrics/` 패키지를 재사용하지 않는 독립 구현이다. `eval/dev/oracle_ABC.json`과 손계산 예제로 먼저 검증한다.
- 채점기는 샌드박스 밖에서 돈다. 이것이 정답 대조 채점(샌드박스 밖에서 하는 비교)이며, 채점 대상 실행(샌드박스 안에서 돌리는 실행)과 구분한다.

## 8. 실행 결과 기록

**명세 §4.10 원문**

`run_id, case_id, dataset, mode, policy_version, rulebook_version, snapshot_id, grouping_version, code_version, review_status_final, signal_status, unresolved_evidence, execution_status, required_evidence_ok, numeric_ok, provenance_ok, tool_attempts, model_requests, tokens_in, tokens_out, wall_ms, critic_used, revision_used, errors`

### 8.1 키 풀이

| 키 | 형식 | 뜻 | 기록 주체 |
|---|---|---|---|
| `run_id` | 문자열 | 사례 실행 1건의 ID | 채점 대상 실행 |
| `case_id` | 문자열 | 사례 ID | 채점 대상 실행 |
| `dataset` | 문자열 | 데이터셋 이름(§4.2의 5개 중 하나) | 채점 대상 실행 |
| `mode` | 문자열 | 모드(§4.1) | 채점 대상 실행 |
| `policy_version` | 문자열 | 정책 버전(예: `policy_v1`) | 채점 대상 실행 |
| `rulebook_version` | 문자열 | 룰북 버전(예: `RB-1`) | 채점 대상 실행 |
| `snapshot_id` | 문자열 | 스냅샷 | 채점 대상 실행 |
| `grouping_version` | 문자열 | 비교 대상 집합(`g0` 또는 `g1`). 합성 자료는 자료 안 `peer_group` 행의 `grouping_version` 값을 그대로 적는다 [DESIGN] | 채점 대상 실행 |
| `code_version` | 문자열 | 실행한 코드의 git 커밋 해시 [DESIGN] | 채점 대상 실행 |
| `review_status_final` | 문자열 또는 `null` | `MAINTAIN`, `MONITOR`, `HOLD` 중 하나. 실행이 `COMPLETED`가 아니면 `null` | 채점 대상 실행 |
| `signal_status` | 객체 | 신호별 판정(§3.1) | 채점 대상 실행 |
| `unresolved_evidence` | 참/거짓 | §3.1 | 채점 대상 실행 |
| `execution_status` | 문자열 | 실행 상태(§3.3) | 채점 대상 실행 |
| `required_evidence_ok` | 참/거짓 | 필수 근거를 충족했는가 | 정답 대조 채점 |
| `numeric_ok` | 참/거짓 | 수치·단위가 맞는가 | 정답 대조 채점 |
| `provenance_ok` | 참/거짓 | 출처·버전이 맞는가 | 정답 대조 채점 |
| `tool_attempts` | 정수 | 도구 호출 시도 수. 한도 값은 8이며, 넘은 실행은 실제 값을 적는다 | 채점 대상 실행 |
| `model_requests` | 정수 | 모델 요청 수(재전송 포함). 한도 값은 10이며, 넘은 실행은 실제 값을 적는다 | 채점 대상 실행 |
| `tokens_in`, `tokens_out` | 정수 | 입력·출력 토큰 수. 두 값의 합의 한도 값은 32,000이며, 넘은 실행은 실제 값을 적는다 | 채점 대상 실행 |
| `wall_ms` | 정수 | 사례 전체 경과 시간(밀리초). 한도 값은 300,000이며, 넘은 실행은 실제 값을 적는다 | 채점 대상 실행 |
| `critic_used` | 참/거짓 | Critic을 불렀는가(첫 초안이 스키마 검사에서 실패하면 생략한다) | 채점 대상 실행 |
| `revision_used` | 참/거짓 | 수정 단계를 썼는가 | 채점 대상 실행 |
| `errors` | 목록 | 오류 기록. 멈춘 실행은 실패 원인, 누적 시도, 마지막 정상 근거를 담는다 | 채점 대상 실행 |

기록 주체 열에서 "채점 대상 실행"은 샌드박스 안 실행이 남기는 값이고, "정답 대조 채점"은 샌드박스 밖 채점기가 채우는 값이다 [DESIGN].

- `required_evidence_ok`·`numeric_ok`·`provenance_ok`는 정답표(사례별 필수 근거·기대 수치)나 원본 대조가 있어야 정할 수 있다. 그래서 샌드박스 밖 정답 대조 채점이 채우고, 런타임 검증기의 자기 보고로 채우지 않는다 [DESIGN]. 채점 결과 `scorer_results-{시각}.jsonl`의 한 줄은 채점 대상 실행이 남긴 키(평가 하네스 단위 `evaluation_batch_run`의 출력 `evaluation_batch_run-{시각}.jsonl`)에 채점기가 이 세 키를 더한 것이다. 채점기는 하네스의 파일을 고치지 않고, 둘을 합친 파일을 자기 실행 폴더에 새로 쓴다(§8.2).
- 세 키는 구 개발계획 §8.3 처리정확도 식의 "필수근거", "수치/단위", "출처/버전"에 대응한다 [사실: 구 개발계획 §7·§8.3]. 식의 나머지 두 항은 키를 따로 두지 않는다. "예상 상태 일치"는 `review_status_final`을 정답표와 비교해 얻고, "정상 실행"은 `execution_status`가 `COMPLETED`인지로 얻는다 [추론].
- 한도 수치(모델 요청 10회, 300초, 32,000토큰, 도구 8회)는 조정값이며 모든 모드에 같게 쓴다. provider(모델 API를 호출하는 라이브러리) 자동 재시도는 끄고, 5xx(서버 오류를 뜻하는 HTTP 응답 코드) 명시 재전송만 `model_requests`에 센다 [DESIGN: 명세 §3.3].
- `checklist` 모드는 모델을 쓰지 않으므로 `model_requests`, `tokens_in`, `tokens_out`이 0이다 [사실: 구 개발계획 §8.2 "모델 없는 checklist의 토큰은 0으로 표시"].

### 8.2 기록 위치와 규칙

- 이름과 위치는 이름·출력 규칙(§10.3)을 따른다. 실행 하나가 `outputs/{실행명}/` 폴더 하나이고, 그 안의 파일 이름은 `{도메인명}-{시각}.{확장자}`다 [DESIGN: 2026-09-24(목) 사용자 결정].
- 실행 쪽 키: 평가 묶음 실행(여러 사례 실행을 한 번에 돌리는 평가 실행, `tradesentry evaluate`)이 그 실행 폴더(`outputs/evaluate-{시각}/`. 봉인 묶음이면 `outputs/sealed/` 아래의 실행 폴더)의 `evaluation_batch_run-{시각}.jsonl`에 한 줄에 실행 1건을 적는다. 이 파일에는 채점 대상 실행이 남기는 키만 있다 [DESIGN]. 봉인 묶음은 단위 E2(샌드박스 밖 실행기)가 돌리고, 단위 E2의 묶음 기록도 `outputs/sealed/` 아래 자기 실행 폴더에 둔다(§10.3 N10). 단위 E2의 묶음 기록 도메인명과 봉인 묶음 실행 폴더의 실행 이름은 로드맵 MT7에서 F1 전에 정한다 [미확인].
- 평가 결과: 채점기가 실행 쪽 키에 정답 대조 채점의 세 키를 더해 채점 실행 폴더 `outputs/score-{시각}/`의 `scorer_results-{시각}.jsonl`에 한 줄에 실행 1건(위 키 전부)을 적는다. 하네스의 `evaluation_batch_run-{시각}.jsonl`은 고치지 않는다. 채점 실행 폴더의 채점기 출력(`scorer_*` 파일)을 같은 이름의 폴더 `artifacts/eval/score-{시각}/`로 복사해 커밋한다(증거 복사, §10.3 N11). 재채점용 보고서 원문은 `artifacts/eval/score-{시각}/{run_id}/`에 증거 복사한다(§10.3 N11). 봉인 묶음의 채점 결과는 금지 해제 조건(정답 대조 채점이 끝나고, `real_sealed`이면 표본 추출 seed 공개 기록까지 있는 때. §10.3 N10)이 채워진 뒤에만 복사한다 [DESIGN: 명세 §4.12, 2026-09-24(목) 사용자 결정. 해제 조건은 오케스트레이터 결정, 2026-09-24(목) 사용자 확인(PR #18)].
- 실행 추적: trace(실행 중 호출과 응답을 순서대로 남긴 기록) JSONL(JSON 하나를 한 줄에 적는 기록 파일)과 NAT(NeMo Agent Toolkit: 에이전트 실행을 감싸 추적·프로파일·사후 평가를 하는 NVIDIA 도구 모음) 프로파일 결과는 도메인 출력이라 그 실행 폴더 `outputs/{실행명}/`에 둔다. 봉인 묶음 실행이면 `outputs/sealed/{실행명}/`이다. 커밋하지 않고 증거 복사하지도 않는다. 봉인 묶음 실행의 출력은 금지 해제 조건(§10.3 N10)이 채워지기 전에는 열지 않는다 [DESIGN: 2026-09-24(목) 사용자 결정. 해제 조건은 오케스트레이터 결정, 2026-09-24(목) 사용자 확인(PR #18)] [사실: `.gitignore`가 `outputs/`를 제외한다]. NAT가 정하는 파일 이름(예: `standardized_data_all.csv`)과 이 이름 규칙의 대응은 자문 명세서 Q1의 4다 [미확인]. 예상 해법은 §10.3 N7 폴더(`outputs/{실행명}/{도메인명}-{시각}/`)에 NAT가 정한 이름을 그대로 두고, 그 파일 이름을 단위 표의 단위 I13·E4 행에 고정하는 것이다.
- 실패·미실행·timeout·invalid도 기록하고 분모에 남긴다. 결과를 본 뒤 어려운 사례를 지우지 않는다 [DESIGN: 명세 §3.6].
- 분모는 결과 줄 수가 아니라 고정 사례 목록(`dev20`, `holdout40`, `real_dev`, `real_sealed` 봉인 표본)으로 센다. `real_dev`의 목록은 그 평가 묶음 실행 때의 정책으로 만든 경보 목록이며 채점 요약 `scorer_summary-{시각}.md`에 기록한다(MVP 대표 지표 첫 값의 분모). 실행되지 않아 결과 줄이 없는 사례도 실패로 센다. 세부는 룰북 `docs/eval/RULEBOOK.md` B5를 따른다 [DESIGN].
- NIM 오류 등으로 다시 실행하면 같은 (`dataset`, `case_id`, `mode`)에 실행 기록이 여러 건 생긴다. 모든 시도를 지우지 않고 남긴다. 채점 대상으로 고를 실행은 룰북 B5를 따른다 [DESIGN].
- 모델 원초안 → Critic 뒤 → 검증 뒤의 상태 변화는 trace의 사건으로 `outputs/{실행명}/`에 남기고 채점 요약 `scorer_summary-{시각}.md`에 집계한다 [DESIGN: 명세 §3.6].
- 채점 요약 `scorer_summary-{시각}.md`에는 계약 버전(`schema_version`), 스냅샷 해시(`normalized_sha256`), 채점기 커밋 해시, 산문 패턴 목록 버전, 채점 대상 `run_id` 목록, `real_dev`를 채점했으면 그때의 경보 목록, 상태 변화 집계를 적는다 [DESIGN].
- 요약 `scorer_summary-{시각}.md`는 채점기만 쓴다. 에이전트는 채점기 출력 파일을 고쳐 쓰지 않는다(§10.3 N8). 채점기가 모르는 값은 실행 조건 입력 파일(채점기가 모르는 실행 조건을 채점기에 넘기는 파일)로 채점기에 들어가고, 채점기는 그 값을 요약 0절·4절(룰북 B7 양식)에 그대로 옮긴다. 채점기는 실행 조건을 이 파일에서만 읽는다. 샌드박스가 쓴 파일은 믿지 않는 입력이다. 채점기 명령(`python -m eval.scorer --run <run_dir>`)은 바꾸지 않는다 [DESIGN: 오케스트레이터 결정, 결정 기록 `docs/tracking/decisions/20260924-2003-orchestrator-decision-sealed-output-scope.md`, 2026-09-24(목) 사용자 확인(PR #18)].
  - 담는 값: 사전 점검 결과, 샌드박스 이름, 라이브 정책 sha256, 시험표 폴더 이름, 봉인 해시 재대조 결과, 봉인 출처 점검 결과, 스킬 호출 성공률, 한도 값, 순서 seed, 동시성, 평가 스킬 ② 채점 전 확인 1·2·5번의 결과(참·거짓과 건수). 봉인 묶음이 아니면 NAT 프로파일 요약과 한국어 품질 표본 점검 결과도 이 파일로 요약에 들어간다.
  - 봉인 묶음이면 봉인 실행 출력을 열지 않고 얻는 값만 넣는다. 봉인 출력이 있어야 하는 값(NAT 프로파일 요약, 한국어 품질 표본 점검)은 금지 해제 조건(§10.3 N10) 뒤에 결과표(로드맵 R1)에 적고, 채점기 요약에는 넣지 않는다.
  - 만드는 주체와 방법: 내려받기를 끝낸 호스트 쪽 프로그램이 자기가 확보한 실행 폴더 안에 배타 생성(이미 있으면 실패하는 방식의 파일 만들기)한다. 샌드박스에서 받은 출력에 같은 이름이 있으면 내려받기를 거부한다. 만드는 때는 담을 값이 모두 정해진 뒤, 채점기를 부르기 전이다. 봉인 묶음이면 채점 직전의 봉인 해시 재대조 뒤다.
  - 이름·형식, `<run_dir>` 안의 위치, 누락·잘못된 입력의 처리는 로드맵 MT7·DT8에서 F1(`RB-1` 동결) 전에 정한다 [미확인]. 이 넷(이름·형식·위치·누락 처리)은 MVP 시험 전에 임시로 정해 쓰고 F1 전에 확정한다 [DESIGN: 2026-09-24(목) 사용자 결정, 결정 기록 20260924-2315 D6].

## 9. 보고서 객체와 주장 채점 기록

**명세 §4.10-1 원문**

`report_id, run_id, case_id, mode, claims, narrative, hypotheses, review_status, signal_status, unresolved_evidence, evidence_ids, validator_findings, report_hash, created_at, policy_version, snapshot_id, grouping_version`

- `claims`: typed claim 목록(§4.8)
- `narrative`: 설명 문장
- `hypotheses`: 미확인 가설
- `validator_findings`: 검증기가 막았거나(`full`), 막았을 것(`freeform` 기록 전용)의 목록
- `report_hash`: `claims`·`narrative`·`hypotheses`·`evidence_ids`를 정규화한 sha256

**명세 §4.10-2 원문**

`run_id, report_id, claim_id, source, outcome, expected_value, reported_value, unit_expected, unit_reported, tolerance, referent_resolved, evidence_ok, note`

- `source`: `claim | prose`(산문 패턴으로 잡힌 표현)
- `outcome`: §4.9 값

### 9.1 보고서 객체 키 풀이

| 키 | 형식 | 뜻 |
|---|---|---|
| `report_id` | 문자열 | 보고서 ID |
| `run_id` | 문자열 | 이 보고서를 만든 실행 |
| `case_id` | 문자열 | 사례 |
| `mode` | 문자열 | 모드(§4.1) |
| `claims` | typed claim 목록 | §6 |
| `narrative` | 문자열 | 설명 문장(한국어) |
| `hypotheses` | 문자열 목록 | 확인되지 않은 가설 |
| `review_status` | 문자열 | 사례 상태 `MAINTAIN`, `MONITOR`, `HOLD` 중 하나 |
| `signal_status` | 객체 | 신호별 판정(§3.1) |
| `unresolved_evidence` | 참/거짓 | §3.1 |
| `evidence_ids` | 근거 ID 목록 | 보고서가 쓴 근거 전체 |
| `validator_findings` | 목록 | `freeform`이 아닌 모드(`checklist`·`agent`·`full`)에서는 검증기가 막은 사유, `freeform`에서는 막았을 사유 |
| `report_hash` | 16진수 64자 | 아래 정규화 규칙으로 계산한 sha256 |
| `created_at` | KST ISO 8601 시각 | 보고서를 만든 시각 |
| `policy_version`, `snapshot_id`, `grouping_version` | 문자열 | 보고서가 기대는 정책·스냅샷·비교 대상 버전 |

- 명세 §4.10-1 원문의 괄호 `full`은 `freeform`과 대비한 예시다. 검증기는 `freeform`을 뺀 모든 모드(`checklist`·`agent`·`full`)에서 막는다 [DESIGN: 명세 §3.3].
- 보고서 객체는 도메인 출력이므로 이름·출력 규칙(§10.3)대로 그 실행 폴더 `outputs/{실행명}/`에 남는다 [DESIGN: 2026-09-24(목) 사용자 결정]. 채점기 `python -m eval.scorer --run <run_dir>`의 입력이다. 그러나 `outputs/`는 커밋하지 않으므로, 저장소만으로 다시 채점할 수 있게 재채점용 보고서 원문은 `artifacts/eval/score-{시각}/{run_id}/`(`{run_id}`는 사례 실행의 실행명)에 증거 복사한다. 조건은 다섯이다. 봉인 묶음은 그 묶음의 금지 해제 조건 뒤에만 복사한다. 허용 목록(증거 복사할 보고서 파일 이름의 목록)의 보고서 파일만 복사하고 실행 폴더를 통째로 복사하지 않는다. 원문 무결성은 `report_hash`가 아니라 파일 바이트 sha256으로 본다. 커밋 전에 비밀값·로컬 경로 검사를 거친다. 커밋 사본으로 다시 채점하는 명령을 결과 요약 "재현 명령"에 함께 적는다 [DESIGN: 2026-09-24(목) 사용자 결정, 결정 기록 `20260924-2315-user-decision-impl-plan-approval.md` D3]. 저장소만으로 다시 채점할 수 있는지는 아직 알 수 없다 [미확인]. 까닭은 다섯이다. 실자료 스냅샷의 SQLite와 raw 응답은 커밋하지 않는다. holdout40 정답표를 커밋할 위치가 정해지지 않았다. 채점기가 커밋 사본의 사례 폴더를 여는 규칙이 없다. 묶음 기록과 기준 sha256을 둘 자리가 없다. 원문이 빠졌는지는 결과 요약이 굳은 뒤에야 안다.

**`report_hash` 정규화 규칙** [DESIGN]

1. `claims`, `narrative`, `hypotheses`, `evidence_ids` 네 키만 담은 JSON 객체를 만든다.
2. 모든 문자열 값을 유니코드 NFC(같은 글자를 한 가지 코드 순서로 맞추는 정규화)로 바꾼다.
3. 수는 JSON 숫자로 적는다. `claims`의 수 `value`는 그 주장 `metric`의 표시 자릿수(§11.3)로 사사오입(ROUND_HALF_UP: 버리는 자리가 절댓값 기준 5 이상이면 올림)한다. 표시 자릿수가 정수인 기호(`V`, `Q`)는 정수로 적는다. `NaN`과 무한대는 쓰지 않는다.
4. 키 이름 순으로 정렬하고, 공백 없는 구분자(`,`와 `:`)를 쓰고, 한글을 이스케이프하지 않은 UTF-8로 직렬화한다. 목록 안의 순서는 저장된 순서 그대로 둔다.
5. 그 바이트의 sha256을 16진수 소문자 64자로 적는다.

- 파이썬으로 쓰면 2·3단계를 적용한 객체를 `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")`로 직렬화한 바이트의 sha256이다. 반올림은 `Decimal`(반올림 오차 없이 십진 소수를 다루는 파이썬 수 형식)의 `ROUND_HALF_UP`으로 하고, 결과는 정수 기호면 `int`, 나머지는 `float`로 바꿔 넣는다.
- 위 직렬화(정수·`float` 변환 포함)는 `report_hash` 계산에만 쓴다. 3단계의 반올림은 저장된 수의 원문 표기를 `Decimal`로 바로 읽어 한다. `float`를 거친 값을 `Decimal`로 바꾸지 않는다. 경계값에서 결과가 달라지기 때문이다(예: 원문 `20.345`는 `Decimal`로 읽으면 20.35, `float`를 거치면 20.34) [DESIGN].
- 보고서를 저장할 때, 채점 입력으로 쓸 때, 주장 채점 기록의 `reported_value`(§9.2)에 옮길 때는 수의 원문 표기(JSON 파일에 적힌 숫자 글자 그대로, 예: `20.30`)를 보존한다. 끝자리 0이 사라지면 룰북 B3-1의 "보인 자리수"(보고값에 적힌 소수 자리 수, 끝자리 0 포함) 판정이 바뀌기 때문이다. 틀 채우기 모드(`checklist`·`agent`·`full`)의 보고서 틀은 수를 §11.3 표시 자릿수의 십진 표기(끝자리 0 포함)로 쓴다. `freeform`의 원문은 모델 응답 문자열이므로, 응답은 문자열에서 바로 `Decimal`로 읽고 자동 `float` 해석을 거치지 않는다. 거치면 보존하기 전에 끝자리 0이 사라진다 [DESIGN].
- `report_hash`는 끝자리 0만 다른 두 보고서(`20.3`과 `20.30`)를 구분하지 못한다. 그래서 `report_hash`를 채점 입력이 같은지 확인하는 데 쓰지 않는다. 채점 입력이 같은지 확인해야 하면 저장한 보고서 파일 바이트의 sha256을 따로 쓴다 [DESIGN].
- 해시는 위 네 키만 덮는다. `review_status`·`signal_status` 같은 나머지 키는 해시에 들지 않으므로, 해시가 같아도 보고서 전체가 같다고 보장하지는 못한다 [추론: 명세 §4.10-1의 정의]. 그래서 저장한 보고서는 고치지 않고, 내용이 바뀌면 새 보고서(새 `report_id`)로 만든다 [DESIGN].
- 검증기를 통과하지 못한 보고서는 공유·승인 대상이 아니다 [DESIGN].

### 9.2 주장 채점 기록 키 풀이

| 키 | 형식 | 뜻 |
|---|---|---|
| `run_id`, `report_id` | 문자열 | 채점한 실행과 보고서 |
| `claim_id` | 문자열 | typed claim의 ID. `source`가 `prose`이면 보고서 안 필드와 출현 순번으로 만든 결정적 ID `prose:<필드>:<순번>`(예: `prose:narrative:3`) [DESIGN] |
| `source` | 문자열 | `claim`(typed claim) 또는 `prose`(설명 문장에서 산문 패턴으로 잡힌 표현) |
| `outcome` | 문자열 | 주장 채점 결과(§7) |
| `expected_value` | 수, 문자열 또는 `null` | 채점기가 스냅샷 원본 행에서 계산한 기대값 |
| `reported_value` | 수, 문자열 또는 `null` | 보고서에 적힌 값 |
| `unit_expected`, `unit_reported` | 문자열 또는 `null` | 기대 단위와 보고서의 단위(§11.2) |
| `tolerance` | 수 또는 `null` | 적용한 허용오차 |
| `referent_resolved` | 참/거짓 | 기간·국가·품목·지표가 가리키는 대상을 찾았는가 |
| `evidence_ok` | 참/거짓 | 근거 ID가 풀리고(§4.4) 주장을 뒷받침하는가 |
| `note` | 문자열 | 메모. `prose` 기록에는 잡힌 표현과 위치를 적고, 그 표현을 뒷받침한 typed claim이 있으면 그 `claim_id`를 적는다 [DESIGN] |

- `prose:<필드>:<순번>`에서 `<필드>`는 보고서 안 경로(예: `narrative`, `hypotheses[0]`, `claims[2].text`)이고, 목록 번호는 0부터 센다. `<순번>`은 그 필드 안에서 잡힌 표현의 시작 위치 순서로 1부터 센다. typed claim의 `claim_id`는 `prose:`로 시작하지 않는다. 산문 검사 대상 필드는 룰북 B3-2가 정한다 [DESIGN].

### 9.3 승인 기록(모의) [DESIGN: 명세 §3.3]

- 필드: `reviewer_label`, `timestamp`, `report_hash`, `evidence_digest`, `snapshot_id`, `policy_version`, `code_version`
- 유효 상태: `VALID` 또는 `REVIEW_REQUIRED`(명세 §4.5 원문, 이 문서 §4)
- 의존 자료·정책·수치·보고서가 바뀌면 기존 기록은 보존하고 유효 상태만 `REVIEW_REQUIRED`로 바꾼다. 승인할 때 digest를 다시 계산해 대조한다.
- `execution_status`가 `COMPLETED`가 아닌 실행의 보고서는 승인할 수 없다.
- `evidence_digest`(보고서가 기대는 근거 행 내용을 요약한 해시)의 계산 방법은 승인 패키지 `approval/`을 구현할 때 정하고 결정 기록에 남긴다.
- 화면 없이 코드와 시험으로만 구현한다. 실제 기관 승인이나 통관 조치가 아니다.

### 9.4 보고서 스키마 요건과 신호 계열 [DESIGN]

- 스키마 검사에는 다음 요건이 들어간다: `signal_trigger`가 `TRIGGERED`인 신호마다 그 신호 계열의 claim이 1개 이상 있어야 통과한다.
- 이 요건은 모든 모드에 같게 적용하고, `freeform`의 스키마 검사에도 넣는다.
- 수정 1회 뒤에도 요건을 채우지 못하면 실행은 `INVALID`로 끝난다(§3.3). `INVALID`는 명세의 "유효한 최종 보고서 없음"에 해당하므로 보고서 단위 실패로 분모에 남는다(§7.2).
- 신호 계열 대응은 아래와 같다. 룰북 `docs/eval/RULEBOOK.md` B3의 발동 신호별 주장 요건과 채점기가 같은 대응을 쓴다.

| 신호 계열 | 드는 `metric` |
|---|---|
| `unit_value` | `U`, `r_U`, `within_effect`, `mix_effect`, `residual`, `U@<HS10 코드>`, `r_U@<HS10 코드>`, `w@<HS10 코드>` |
| `share` | `s`, `d_s` |

- `data_status` 주장은 값이 `OBSERVED`가 아닐 때(자료 문제를 말할 때)만 계열 요건에 센다. 그래야 내용 없는 주장 1건으로 두 계열을 모두 채우지 못한다. 셀 때는 가리키는 관측이 속한 계열에 넣는다. HS10 하위 관측(`observation_status@<HS10 코드>`, `partner`가 상대국)은 `unit_value`, `ALL` 분모 관측(`partner`가 `ALL`)은 `share`, 상대국 HS6 관측(`observation_status`, `partner`가 상대국)은 두 계열 모두에 든다.
- 계열은 `metric`으로 정한다. 요건에 세는 claim은 사례의 `hs6`(HS10 하위 metric이면 그 부모 `hs6`)·대상국·`period`(사례의 비교월)를 가리키는 것뿐이다. `ALL` 분모 관측을 말하는 `data_status` 주장은 `partner`가 `ALL`이어도 센다. 비교국에 대한 claim(`comparison` 포함)은 요건에 세지 않는다 [DESIGN]. 룰북 `docs/eval/RULEBOOK.md` B3의 발동 신호별 주장 요건과 채점기는 이 대상 규칙을 그대로 쓴다.
- `V`·`Q` 주장은 위 표에 없으므로 어느 계열 요건도 채우지 않는다 [추론: 위 대응 표].

## 10. 계획 경로·명령 표

아래 표의 OpenShell은 에이전트를 격리 실행하는 NVIDIA 샌드박스 런타임, NAT는 §8.2의 NVIDIA 에이전트 도구 모음, S0는 구현 첫 단위인 앱 스캐폴딩(프로젝트 뼈대 생성), X1은 세로형 최소 통합 시험(설치부터 차단 로그까지 한 줄로 잇는 첫 시험)이다. 패키지는 파이썬 모듈 파일을 여럿 담는 폴더, 단위는 혼자 실행하고 시험할 수 있게 파일 하나로 만든 가장 작은 구현 조각, 도메인명은 단위마다 붙인 출력용 이름이다(§10.3, 단위 표 `docs/plan/UNITS.md`).

**2026-09-24(목) 사용자 결정(결정 기록 `20260924-1720-user-decision-domain-restructure.md`, `20260924-2315-user-decision-impl-plan-approval.md` D2·D3)으로 고친 표**

- 모든 문서는 아래 표의 경로와 명령만 쓴다. 이름은 조정값이며, S0 외부 자문으로 바뀌면 이 표와 참조 문서를 **함께** 고친다.
- 기존 파일(`src/tradesentry/ingest.py`, `eval/dev/oracle_ABC.json`, `configs/collection_plan.json`)의 위치는 바꾸지 않는다.

| 대상 | 예정 경로·명령 | 소유 |
|---|---|---|
| 앱 패키지 | `src/tradesentry/` — `ingest.py`(기존), 패키지 `contract/`, `snapshot/`, `dal/`, `metrics/`, `policy/`, `grouping/`, `tools/`, `workflow/`, `reports/`, `validator/`, `runlog/`, `evaluation/`, `approval/`, `cli/`. 단위 파일은 `{패키지}/{단위}.py` | D: ingest·contract·snapshot·dal·metrics / M: policy·grouping·tools·workflow·reports·validator·evaluation·approval·cli / 공동: runlog |
| 단위 등록부·공통 실행기(개발 전용) | `src/tradesentry/units/`, 실행 `python -m tradesentry.units <단위 ID> --in <입력 파일>` | 공동 |
| CLI | `tradesentry <명령>` — `snapshot-build`, `snapshot-verify`, `detect`, `run-case`, `evaluate`, 공통 옵션 `--snapshot`, `--policy`, `--mode`(값은 `checklist`, `agent`, `full`, `freeform`) | M |
| 화면 | `src/tradesentry/app.py`(Streamlit 화면) | M |
| 정책 수치 | `configs/policy_v1.json`(사용자 승인 뒤), 개발용 `configs/policy_dev.json`(`policy_version` `dev-0.1`, oracle 기준값, 승인 전 실행용) | D 제안·사용자 승인(개발용은 D) |
| NAT 설정 | `configs/nat/workflow.yml` | M |
| 프롬프트·모델 설정 | `configs/model/`(조사자·Critic 프롬프트, 모델 ID, 추론 모드) | M |
| OpenShell 정책 | `configs/openshell/policy.yaml` | M(보안 검토) |
| 런타임 스킬 | `skills/tradesentry/SKILL.md` | M |
| 평가 스킬 | `skills/tradesentry-scorecard/SKILL.md`, `skills/tradesentry-eval/SKILL.md` | 공동 |
| 합성 시험자료 | `data/snapshots/controlled_fixture_v0/` | D |
| 그룹핑 결과 | `data/reference/peer_group_g0.csv`(`g0`, MVP 시험용 고정 비교국 목록), `data/reference/peer_group_g1.csv` | M 계산·D 검수 |
| 시나리오 명세(공개) | `eval/scenarios/SCENARIO_SPEC.md` | D |
| dev20 | `eval/dev/dev20/`(입력 + 정답표) | D |
| 평가 자료 도구 | `eval/datagen/` — `dev20.py`(dev20 생성), `holdout40_check.py`(holdout40 결정적 검사), `split.py`(실자료 분할) | D |
| 봉인 해시 목록 | `eval/sealed_manifest.json` | D |
| 봉인 폴더 | 환경변수 `TRADESENTRY_SEALED_DIR`, 기본값 `~/.tradesentry/sealed/`(저장소 밖) | D |
| 독립 채점기 | `eval/scorer/`(런타임 모듈을 import하지 않음), 실행 `python -m eval.scorer --run <run_dir>`, 출력 `outputs/score-{시각}/` | D |
| 도메인 출력(커밋 안 함) | `outputs/{실행명}/{도메인명}-{시각}.{확장자}`(trace JSONL, NAT 프로파일 결과, 보고서, 실행 결과 기록 등 도메인 출력 전부). 봉인 묶음 실행은 `outputs/sealed/{실행명}/` | 공동 |
| 평가 결과(커밋) | `artifacts/eval/score-{시각}/`(채점 실행 폴더의 채점기 출력 복사: `scorer_results-{시각}.jsonl`, `scorer_claims-{시각}.jsonl`, `scorer_summary-{시각}.md`), 재채점용 보고서 원문 `artifacts/eval/score-{시각}/{run_id}/`(허용 목록의 보고서 파일만 복사) | 공동 |
| 자기채점 결과(커밋) | `artifacts/scorecard/scorecard-{시각}/`(자기채점 실행 폴더의 결과 파일만 복사: `scorecard-{시각}.md`) | 공동 |
| OpenShell 증거(커밋) | `artifacts/openshell/openshell_violation_tests-{시각}/`(위반 시험 실행 폴더의 결과 파일만 복사: 예측·실측 대조표 `.md`, 감사 로그 발췌 `.txt`, 라이브 정책 조회 본문 `.yaml`) | M(보안 검토) |
| X1 임시 시험 코드 | `spikes/x1/` | M |
| 시험 | `tests/`(기존 `test_ingest.py` 유지), 단위 골든 시험 `tests/units/{단위 ID}/` | 공동 |

### 10.1 읽는 법

- 이 표는 구현 단계의 예정 위치다. 이 문서를 쓴 2026-09-24(목) 현재 표의 경로 중 저장소에 있는 것은 기존 파일 셋(`src/tradesentry/ingest.py`, `eval/dev/oracle_ABC.json`, `configs/collection_plan.json`)과 `tests/test_ingest.py`뿐이다 [사실].
- 중괄호 자리 `{실행명}`, `{도메인명}`, `{시각}`, `{확장자}`, `{패키지}`, `{단위}`, `{단위 ID}`, `{run_id}`는 이름·출력 규칙(§10.3)과 단위 표로 채운다. `{run_id}`는 사례 실행의 실행명이다(§10.3 N5). `{시각}`은 `yymmddhhmmss`, 곧 그 실행이 시작한 KST(한국 표준시) 24시간 12자리 시각이다(예: `260925143015`). 꺾쇠 자리 `<run_dir>`, `<단위 ID>`, `<입력 파일>`, `<명령>`은 명령을 쓸 때 실제 값으로 바꾸는 자리표시다.
- `<run_dir>`는 채점할 실행의 폴더 `outputs/{실행명}/`이고, 봉인 묶음 실행이면 `outputs/sealed/{실행명}/`이다. 채점기는 자기 출력을 `outputs/score-{시각}/`에 쓴다. 봉인 묶음을 채점할 때도 같다. 그때 채점기는 시작 직후 자기가 확보한 실행 폴더 이름을 표준 출력 첫 줄로 알리고, 봉인 묶음을 채점한 채점기 출력은 금지 해제 조건(§10.3 N10) 전에는 에이전트가 열지 않고 커밋하지 않는다.
- `run_id`는 실행명이다(§10.3 N5). 실행 결과 기록(§8)의 `run_id`는 그 사례 실행의 실행명이며, `run-case`로 돌린 사례 실행이면 `run_case-{시각}`이다. 평가 묶음 실행(`evaluate`)은 자기 실행명 `evaluate-{시각}`을 갖고, 그 안의 사례 실행마다 새 실행명을 쓴다. 시각이 초 단위라 같은 초에 시작한 두 실행은 이름이 같아질 수 있으므로, 실행을 시작하기 전에 호스트의 실행 폴더를 폴더 만들기 호출 하나(이미 있으면 실패하는 방식. 예: 파이썬 `os.mkdir`를 `exist_ok` 없이)로 만들어 실행명을 확보하고, 그 호출이 성공한 프로세스만 그 실행명을 쓴다. 만들기 전에 그 이름의 초가 될 때까지 기다리고, 만든 뒤 다른 부모 폴더(`outputs/`와 `outputs/sealed/`)에 같은 이름이 있으면 방금 만든 빈 폴더를 지운다. 만들기에 실패하거나 폴더를 지웠으면 다음 초의 이름으로 다시 한다(N8). 사례 실행의 폴더를 묶음 실행의 폴더와 어떻게 잇는지는 S0에서 정한다 [미확인](`docs/plan/SCAFFOLD_BRIEF.md` Q9).
- 보고서 객체는 도메인 출력이라 `outputs/{실행명}/`에 남는다. 이 폴더는 커밋하지 않으므로 재채점용 보고서 원문은 `artifacts/eval/score-{시각}/{run_id}/`에 증거 복사한다(조건 다섯은 §10.3 N11).
- 소유 열의 D·M·공동은 그 파일을 고칠 수 있는 트랙이다. 소유 트랙이 아닌 에이전트는 읽기만 한다 [DESIGN: 명세 §3.10].
- S0는 구현 첫 작업 단위인 앱 스캐폴딩(프로젝트 뼈대 생성)이며, 뼈대를 만들기 전에 외부 자문을 받는 체크포인트다 [DESIGN: 명세 §3.8].

### 10.2 2026-09-24(목) 저장소 설정과 맞춰 볼 점 [사실: `.gitignore`]

- `.gitignore`는 `outputs/`를 제외한다. 표의 "도메인 출력(커밋 안 함)"과 맞다. 이 줄은 2026-09-24(목) 이름·출력 규칙(§10.3)과 같은 PR에서 더했다. 옛 실행 기록 폴더를 빼는 줄도 X1 임시 시험 기록 때문에 지우지 않고 남겨 두었다(§10.3).
- `.gitignore`는 `data/snapshots/*/raw/`와 `data/snapshots/*/snapshot.sqlite`도 제외한다. 그래서 `data/snapshots/controlled_fixture_v0/` 아래의 SQLite 파일과 raw 폴더는 이 설정으로는 커밋되지 않는다.
- 키 없이 도는 재현 시험에 합성 픽스처(시험용으로 미리 만든 고정 자료)를 커밋해야 한다면 어떤 형태로 커밋할지 D가 정해야 한다 [미확인]. 그 일을 위한 `.gitignore` 수정은 이 문서의 범위가 아니다.

### 10.3 이름·출력 규칙

2026-09-24(목) 사용자 결정(결정 기록 `docs/tracking/decisions/20260924-1720-user-decision-domain-restructure.md`)의 원문 세 가지와 확인 답 네 가지를 규칙으로 옮겼다 [DESIGN: 사용자 결정]. N5의 실행 이름 목록, N7, N11의 파일 대응, N12, 그리고 §4.5에서 `run_id`를 실행명으로 정한 것은 오케스트레이터(작업을 배분하고 PR을 병합하는 주관 에이전트)가 정리했고 2026-09-24(목) 사용자가 확인했다(PR #18). N11의 이름 "증거 복사"(커밋 증거 파일만 `artifacts/{종류}/`로 복사해 커밋하는 일)·"커밋 사본"(그렇게 커밋한 폴더와 파일)과 N10의 봉인 출력 범위·금지 해제 조건도 오케스트레이터가 정했고 같은 날 사용자가 확인했다(PR #18). 단위와 도메인명의 목록은 단위 표 `docs/plan/UNITS.md`에 있다. 이 절에서 실행은 CLI 명령, 채점기, 스킬·스크립트, 단위 하나를 한 번 돌리는 일이다.

- **N1 문자**: 패키지·단위·도메인명·실행명은 영문 소문자·숫자·밑줄(`_`)만 쓰고 영문 소문자로 시작한다. 하이픈(`-`)은 이름과 시각 사이에만, 점(`.`)은 확장자 앞에만 쓴다. 다른 규약이 정한 이름(CLI 명령 `snapshot-build`·`run-case`, 스킬 이름, 스냅샷·자료 묶음 ID)은 그대로 둔다.
- **N2 패키지**: 도메인 묶음 하나가 패키지(디렉터리) 하나다. `src/tradesentry/` 아래 15개(`contract`, `snapshot`, `dal`, `metrics`, `policy`, `grouping`, `tools`, `workflow`, `reports`, `validator`, `runlog`, `evaluation`, `approval`, `cli`, `units`)와 `eval/scorer/`·`eval/datagen/`이다. 패키지 밖 모듈 파일은 `ingest.py`(기존)와 `app.py`(`src/tradesentry/app.py`) 둘이다. 계획 모듈을 패키지로 바꿔도 import 경로(예: `tradesentry.metrics`)는 그대로다.
- **N3 단위 파일**: 단위 하나가 파일 `{패키지}/{단위}.py` 하나다. 단위 이름은 그 패키지 안에서 유일하다.
- **N4 도메인명**: `{패키지}_{단위}`다(예: `snapshot_build`). `eval/scorer`의 단위는 `scorer_`, `eval/datagen`의 단위는 `datagen_`을 앞에 붙인다. 패키지 밖 모듈은 파일 이름(`ingest`, `app`)을 도메인명으로 쓴다. 스킬·스크립트의 출력은 그 실행 이름(N5)을 도메인명으로 쓴다(`scorecard`, `openshell_violation_tests`). 단위 표에서 한 번 정한 도메인명은 조립 때 단위를 합쳐도 바꾸지 않는다.
- **N5 실행명(`run_id`)**: `{실행 이름}-{yymmddhhmmss}`다. 실행 이름은 시각이 붙지 않은 이름이다. CLI 명령은 하이픈을 밑줄로 바꾼 것(`snapshot_build`, `snapshot_verify`, `detect`, `run_case`, `evaluate`), 채점은 `score`, 단위를 혼자 돌리면 그 도메인명, 스킬·스크립트는 그 이름(`scorecard`, `openshell_violation_tests`)을 실행 이름으로 쓴다. 예: `run_case-260925143015`. 단위 E2의 묶음 기록 도메인명과 봉인 묶음 실행 폴더의 실행 이름은 로드맵 MT7에서 F1 전에 정한다 [미확인]. 묶음 실행(단위 E1·E2)이 부르는 사례 실행의 실행 이름과, 묶음 폴더와 사례 폴더를 잇는 방법은 자문 명세서 Q9 [미확인](`docs/plan/SCAFFOLD_BRIEF.md` Q9).
- **N6 출력**: 모든 도메인 출력은 `outputs/{실행명}/{도메인명}-{yymmddhhmmss}.{확장자}`에 쓴다. 실행 폴더는 곧 `outputs/{실행 이름}-{시각}/`이다. 시각은 그 실행이 시작한 KST 24시간 12자리이고, 한 실행의 모든 출력이 같은 시각을 쓴다. 예: `outputs/score-260926150000/scorer_claims-260926150000.jsonl`. 예외는 봉인 자료 생성에서 부르는 명령의 출력이다. 그 출력은 `outputs/`에 쓰지 않는다(N10). NAT가 정하는 파일 이름(예: `standardized_data_all.csv`)과 이 이름 규칙의 대응은 자문 명세서 Q1의 4다 [미확인]. 예상 해법은 N7 폴더(`outputs/{실행명}/{도메인명}-{시각}/`)에 NAT가 정한 이름을 그대로 두고, 그 파일 이름을 단위 표의 단위 I13·E4 행에 고정하는 것이다.
- **N7 같은 확장자 여러 파일**: 한 단위가 한 실행에서 같은 확장자 파일을 여럿 내면 `outputs/{실행명}/{도메인명}-{시각}/` 폴더에 넣고, 폴더 안 파일 이름은 단위 표에 고정한다.
- **N8 덮어쓰기 금지와 실행명 확보**: 쓰려는 이름이 이미 있으면 쓰지 않고 그 실행을 실패로 끝낸다. 이름 충돌 때문에 공식 실행이 실패해 `FAILED`로 분모에 남는 일은 설계로 막는다.
  - 실행명은 실행을 시작하기 전에 확보한다. 확보는 호스트의 실행 폴더 `outputs/{실행명}/`(봉인 묶음이면 `outputs/sealed/{실행명}/`)를 폴더 만들기 호출 하나로 만드는 일이다. 그 호출은 이미 있으면 실패해야 한다(예: 파이썬 `os.mkdir`를 `exist_ok` 없이 부른다). 그 호출이 성공한 프로세스만 그 실행명을 쓴다. 아직 아무것도 쓰지 않았으므로 덮어쓰기가 아니다.
  - 확보하기 전에 그 이름의 초가 될 때까지 기다린다. 그래서 `{시각}`은 실제 시작 시각보다 앞서지 않는다. 만들기에 실패하면 다음 초의 이름으로 다시 한다.
  - 한 부모 폴더(`outputs/` 또는 `outputs/sealed/`)에 만든 뒤, 다른 부모 폴더에 같은 이름이 있는지 본다. 있으면 방금 만든 빈 폴더를 지우고 다음 초로 넘어간다.
  - 확보는 실행을 시작하는 호스트 쪽 프로그램이 한다. 적용 대상은 단위 E1·E2·E3, 채점기, 스킬(스킬·스크립트 실행, N5), 봉인 기간 로그 발췌를 모으는 프로그램 모두다. 샌드박스 안에서 시작하는 실행(NemoClaw 시연 경로)은 누가 어떻게 확보하는지를 로드맵 MT5 ⑥에서 정한다 [미확인].
  - 확보와 내려받기는 같은 샌드박스 밖 프로그램이 한다. 확보가 끝나면 샌드박스 쪽 실행 폴더는 같은 `{실행명}`을 쓰고, 내려받기는 확보한 빈 폴더에 한다(아래 "그 밖의 약속"의 방식 (나), 로드맵 MT5).
  - 시각은 샌드박스 시간대와 관계없이 명시적 KST로 만든다. 샌드박스 안 시간대는 [미확인]이다.
  - 배치 실행기(평가 하네스 단위 `evaluation_batch_run`)는 사례 실행마다 새 실행명을 쓴다. dev20·`real_dev` 실행과 로드맵 MT7 확인 리허설(단위 E2로 돌리는 경우, 두 실행기가 동시에 도는 경우 포함)로 이름 충돌이 없는지 확인한다.
- **N9 커밋 안 함**: `outputs/`는 커밋하지 않는다(§10.2). `.gitignore`의 `outputs/` 줄은 이 규칙과 같은 PR로 넣으므로 `outputs/`에 처음 쓰는 코드(S0 이후)보다 먼저 `main`에 들어간다.
- **N10 봉인**: 봉인 묶음(holdout40·`real_sealed`) 실행 사슬의 출력은 `outputs/sealed/` 아래에 같은 규칙으로 두고, 금지 해제 조건(아래)이 채워지기 전에는 에이전트가 열지 않고 커밋하지 않는다. 대상과 예외는 개발 플랜 §9.8, 로드맵 F2, 평가 스킬 ②를 따른다. 두는 범위와 금지 해제 조건은 오케스트레이터가 정했고(결정 기록 `docs/tracking/decisions/20260924-2003-orchestrator-decision-sealed-output-scope.md`) 2026-09-24(목) 사용자가 확인했다(PR #18) [DESIGN: 오케스트레이터 결정, 사용자 확인].
  - `outputs/sealed/`에 두는 것: 샌드박스에서 내려받은 봉인 묶음 실행 출력에 더해, 샌드박스 밖에서 생기는 봉인 관련 출력도 여기에 둔다. 각 출력은 자기 실행 폴더 `outputs/sealed/{실행명}/`에 둔다. 샌드박스 밖 출력은 넷이다. ① 단위 E2(샌드박스 밖 실행기)의 묶음 기록 ② 실행 조건 입력 파일(§8.2) ③ 단위 E3(추출 명령)이 봉인 묶음에서 만든 인프라 실패 재실행 대상 목록 ④ 봉인 기간(봉인 묶음을 실행하는 동안)의 `openshell logs` 발췌.
  - 내려받기 전의 위치: 봉인 묶음 실행 출력은 샌드박스 작업 폴더에 있는 동안(내려받기 전, 지우기 전)에도 같은 열람·커밋 금지를 받는다. 에이전트는 그 폴더를 `openshell sandbox exec`·`connect`·`download`로 열거나 받지 않는다. 내려받기는 샌드박스 밖 실행기(프로그램)만 `outputs/sealed/{실행명}/`로 한다. 예외는 기존 셋 그대로다: 채점기 실행, 결정적 건수 추출(내용을 열지 않고 상태·원인 코드의 건수만 뽑는 명령), 한 번만 채점하기 위한 존재 확인. 공식 채점 대상 실행 전용 샌드박스를 내려받은 뒤 지우는지 남기는지를 봉인 사건(봉인 폴더에 닿거나 봉인 묶음을 움직인 일. 평가 스킬 ②가 결정 기록에 남긴다)으로 기록한다. 지우는 시점은 정답 대조 채점 뒤다.
  - 채점기 출력: 경로 표 그대로 채점 실행 폴더 `outputs/score-{시각}/`에 쓴다. 봉인 묶음을 채점할 때는 채점기가 시작 직후 자기가 확보한 실행 폴더 이름을 표준 출력 첫 줄로 알리고, 평가 스킬 ②가 그 이름을 봉인 사건 "채점 시작"에 덧붙인다. 봉인 묶음을 채점할 때 채점기의 표준 출력·오류 출력에는 첫 줄의 실행 폴더 이름과 끝 상태만 낸다. 사례 식별자와 사례별 메시지는 내지 않는다. 그 폴더는 금지 해제 조건까지 `outputs/sealed/` 아래 출력과 같은 금지를 받는다. 위 예외 가운데 채점기 실행은 에이전트가 채점기를 부르는 일까지이고, 에이전트는 그 출력 폴더를 금지 해제 조건 전에 열지 않는다. 결정적 건수 추출에서도 에이전트는 건수만 받는다. 채점기가 도중에 실패하면 부분 출력도 이 금지 아래 남기고 사용자에게 올린다.
  - 금지 해제 조건: 정답 대조 채점이 끝나고(채점기 종료 코드 0과 봉인 사건 "채점 완료" 기록), `real_sealed`이면 표본 추출 seed 공개 기록까지 있어야 한다. 이 조건은 봉인 묶음마다 따로 본다. 한 묶음의 조건이 채워지면 `outputs/sealed/` 아래의 그 묶음 출력과 그 묶음을 채점한 채점기 출력 폴더가 함께 풀린다. 어느 묶음의 것인지 봉인 사건 기록으로 알 수 없는 폴더(두 묶음 기간에 걸친 로그 발췌 포함)는 두 봉인 묶음의 조건이 모두 채워질 때까지 열지 않는다. 커밋 사본(`artifacts/eval/score-{시각}/`)도 이 조건이 채워진 뒤에만 만든다.
  - 봉인 자료 생성 중의 명령 출력: 봉인 자료 생성에서 부르는 명령(`detect` 등)의 출력은 `outputs/`에 쓰지 않는다. 봉인 폴더에 남기는 파일은 모두 해시 목록에 넣는다. 그 밖의 중간 출력은 저장소와 봉인 폴더 밖 임시 위치에 쓰고, 해시를 등록하기 전에 지운다. 출력 위치를 바꾸는 방법(함수 호출이나 CLI 인자)은 S0 결정 항목으로 둔다 [미확인].
  - 봉인 자료와의 구분: 봉인 자료(holdout40 입력·정답표, `real_sealed` 사례 목록·표본, seed)는 계속 저장소 밖 봉인 폴더(`TRADESENTRY_SEALED_DIR`, §12)에만 두고, 봉인 자료 생성(holdout40, `real_sealed` 표본)의 결과물도 봉인 폴더에만 쓴다(생성 중에 부르는 명령의 중간 출력은 바로 위 항목). 그래서 봉인 폴더를 저장소 안에 두지 않는다는 규칙(`docs/rules/PARALLEL_DEV_RULES.md` §6.1)과 부딪치지 않는다. 거꾸로 실행 출력을 봉인 폴더에 두지도 않는다. 봉인 폴더에는 격리된 생성 에이전트만 쓰고(같은 문서 §6.3), 채점 전 해시 재대조는 폴더 안 파일 전부를 해시 목록과 맞춰 보며 목록에 없는 파일도 불일치로 보기 때문이다(같은 문서 §6.2, 이 문서 §12.2). 결정 기록 `docs/tracking/decisions/20260924-1720-user-decision-domain-restructure.md`의 "경계와 순서" ①에 있는 "샌드박스에서 실행한 출력만"은 실행 출력과 봉인 자료를 가르는 말로 읽는다. 사용자가 고른 선택지 문구는 "봉인 묶음 실행 출력은 `outputs/sealed/`"였다(같은 결정 기록의 "확인 답").
- **N11 커밋 증거물(증거 복사)**: 커밋하는 증거물도 같은 이름 규칙을 쓴다. 실행 폴더와 같은 이름의 폴더를 `artifacts/{종류}/` 아래에 만들고, 종류마다 정한 커밋 증거 파일만 복사해 커밋한다. 이 일을 증거 복사라 하고, 그렇게 커밋한 폴더와 파일을 커밋 사본이라 한다. "승격"은 이 일에 쓰지 않는다. "승격"은 빈 응답 달을 무거래 확정으로 바꾸는 `policy_v1` 규칙(§3.4)만 뜻한다. 평가 결과는 채점 실행 폴더의 채점기 출력(`scorer_*` 파일)과 재채점용 보고서 원문을 `artifacts/eval/score-{시각}/`로, 자기채점은 결과 파일 `scorecard-{시각}.md`를 `artifacts/scorecard/scorecard-{시각}/`로, OpenShell 증거는 결과 파일(시험표 `.md`, 감사 로그 발췌 `.txt`, 라이브 정책 조회 본문 `.yaml`)을 `artifacts/openshell/openshell_violation_tests-{시각}/`로 복사한다. trace는 복사하지 않고, 실행 기록 원본(trace·NAT 프로파일 결과)은 커밋하지 않는다는 규칙(§8.2)을 그대로 둔다. 봉인 묶음은 금지 해제 조건(N10)이 채워진 뒤에만 복사한다. 증거 복사하는 파일도 커밋 전에 비밀값·로컬 경로 검사를 거친다(`docs/rules/PARALLEL_DEV_RULES.md` §10.3). 재채점용 보고서 원문은 `artifacts/eval/score-{시각}/{run_id}/`(`{run_id}`는 사례 실행의 실행명)에 증거 복사한다. 조건은 다섯이다. 봉인 묶음은 그 묶음의 금지 해제 조건 뒤에만 복사한다. 허용 목록(증거 복사할 보고서 파일 이름의 목록)의 보고서 파일만 복사하고 실행 폴더를 통째로 복사하지 않는다. 원문 무결성은 `report_hash`가 아니라 파일 바이트 sha256으로 본다. 커밋 전에 비밀값·로컬 경로 검사를 거친다. 커밋 사본으로 다시 채점하는 명령을 결과 요약 "재현 명령"에 함께 적는다 [DESIGN: 2026-09-24(목) 사용자 결정, 결정 기록 `20260924-2315-user-decision-impl-plan-approval.md` D3]. 저장소만으로 다시 채점할 수 있는지는 아직 알 수 없다 [미확인]. 까닭은 다섯이다. 실자료 스냅샷의 SQLite와 raw 응답은 커밋하지 않는다. holdout40 정답표를 커밋할 위치가 정해지지 않았다. 채점기가 커밋 사본의 사례 폴더를 여는 규칙이 없다. 묶음 기록과 기준 sha256을 둘 자리가 없다. 원문이 빠졌는지는 결과 요약이 굳은 뒤에야 안다.
- **N12 정본 자료**(오케스트레이터 정리, 2026-09-24(목) 사용자 확인(PR #18)): 다른 단위가 이름으로 읽는 입력은 이름이 고정이고, `outputs/`의 결과를 동결·승인 단계를 거쳐 그 자리로 옮긴다. 대상은 동결 스냅샷(`data/snapshots/{snapshot_id}/`), 정책 수치(`configs/policy_v1.json`), 비교국 표(`data/reference/peer_group_g1.csv`, `g0`는 `data/reference/peer_group_g0.csv` [DESIGN: 2026-09-24(목) 사용자 결정, 결정 기록 20260924-2315 D3]. `g0`도 `g1`과 같게 `outputs/`에서 만들고 M 계산·D 검수 뒤 옮긴다), dev20(`eval/dev/dev20/`)이다. 이미 있는 파일은 덮지 않는다(N8). `raw/`와 manifest(수집 요청 목록)는 옮기지 않는다. v1·v2 동결 스냅샷의 기존 파일을 바꿔야 하면 멈추고 사용자에게 올린다(`CLAUDE.md` 절대 규칙 2, `docs/rules/PARALLEL_DEV_RULES.md` §10.1).
- **N13 비밀값**: 키 값과 로컬 절대경로는 어떤 출력에도 쓰지 않는다(`docs/rules/PARALLEL_DEV_RULES.md` §10.2·§10.3).

**새 이름 다섯 개의 뜻과 경계**(사용자 결정의 A안)

- `contract`: 공유 커널이다. 계약 타입, 근거 ID, 정책 수치 읽기, 도구 봉투 키를 둔다.
- `snapshot`: 스냅샷 빌드·검증과 합성 스냅샷 생성을 둔다.
- `runlog`: trace, 실행 결과 기록, `errors`의 원인 분류 코드를 둔다.
- `units`: 최소 단위의 등록부(단위 ID와 진입 함수의 대응표)와 공통 실행기(단위 하나를 혼자 돌리는 개발 전용 명령)다. 물리 단위(USD·kg)나 표시 자릿수(§11)와는 관계없다.
- `eval/datagen`: 평가 자료 도구(dev20 생성, holdout40 결정적 검사, 실자료 분할)다. holdout40 생성 코드는 두지 않는다. 그 코드는 봉인 폴더에만 둔다(`docs/rules/PARALLEL_DEV_RULES.md` §1.2·§6.6).
- 경계: `src/tradesentry/` 아래 모든 패키지(`units`·`contract` 포함)는 독립 채점기(`eval/scorer/`)가 import하면 안 되는 대상이다(룰북 `docs/eval/RULEBOOK.md` B3, `docs/rules/PARALLEL_DEV_RULES.md` §1.2). 이 금지에는 간접 import(런타임 패키지를 부르는 모듈을 거쳐 부르는 경우)도 들고, 채점기는 `eval/datagen`도 import하지 않는다. 채점기, dev20 정답표, dev20 생성 도구(`eval/datagen`)는 지표 단위 구현자와 다른 실행자가 `metrics/` 아래 어느 단위도 보지 않고 만든다(`docs/plan/ROADMAP.md` DT5·DT8).

**그 밖의 약속**

- 샌드박스와 도메인 출력: 어떤 샌드박스도 허용 목록과 작업 폴더에 `outputs/` 전체나 `outputs/sealed/`를 넣지 않는다. 파일시스템 허용 목록은 경로 앞부분 일치로 판정하고 작업 폴더 안은 목록에 없어도 허용되므로, `outputs/`를 넓게 열면 다른 실행과 봉인 실행의 출력을 읽을 수 있기 때문이다. 정답 경로를 막는 조건(`docs/rules/PARALLEL_DEV_RULES.md` §6.5 ①)과 같은 구조다(`docs/plan/DEV_PLAN.md` §4.3·§4.5).
  - 문제: 파일시스템 정책은 샌드박스를 만들 때 고정된다(`docs/plan/DEV_PLAN.md` §4.2). 그런데 사례 실행마다 새 실행명을 쓰고(N8) 실행명에는 시각이 들어가므로(N5), 한 샌드박스에서 `run-case`를 여러 번 부르면(예: `real_sealed`, 같은 문서 §9.8) 샌드박스를 만들 때 그 실행 폴더들을 허용 목록에 넣을 수 없다. 상위 폴더를 열면 위 조건과 어긋난다.
  - 방식 (가): 샌드박스를 만들기 전에 묶음 단위 실행 폴더를 정하고 그 폴더 하나만 쓰기로 연다. 호스트 폴더를 샌드박스에 마운트하는 수단은 [미확인]이다.
  - 방식 (나): 샌드박스는 `outputs/`를 아예 열지 않는다. 허용 목록에도 작업 폴더에도 넣지 않는다. 샌드박스 안 작업 폴더(`/sandbox` 아래)에 쓰고, 실행이 끝나면 샌드박스 밖 실행기가 `openshell sandbox download`로 받아 `outputs/{실행명}/`에 둔다. 봉인 묶음 실행이면 받는 곳이 `outputs/sealed/{실행명}/`다(N10). 여러 사례 실행이 한 샌드박스를 쓰면 샌드박스 작업 폴더 안에서도 사례 실행별 하위 폴더를 나눈다.
    - 내려받는 시점: 실행이 끝난 때는 CLI가 NAT 파일 내보내기의 남은 쓰기를 기다린 뒤 끝난 때다. X1에서 NAT 1.9.0의 `stop()`은 남은 쓰기를 기다리지 않아 끝 이벤트가 빠졌다 [사실: X1 임시 시험 기록 "NAT 실행 추적 산출물 위치" 행].
    - 내려받기 전의 위치: 봉인 묶음 실행 출력은 샌드박스 작업 폴더에 있는 동안(내려받기 전, 지우기 전)에도 같은 열람·커밋 금지를 받고, 내려받기는 샌드박스 밖 실행기(프로그램)만 한다(N10).
    - 받기 전 확인: 받을 곳은 그 실행의 실행명을 확보할 때 만든 폴더(N8)이고, 그 폴더가 비어 있어야 한다. 비어 있지 않으면 받지 않고 실패로 끝낸다. 공식 문서는 받는 곳에 같은 이름이 이미 있을 때 거부하는지 적지 않는다. 그래서 download가 덮어쓰기 금지(N8)를 보장한다고 볼 수 없다. 확보와 내려받기는 같은 샌드박스 밖 프로그램이 한다. download가 받는 곳의 기존 파일을 덮지 않는지는 로드맵 MT5에서 검증하고, 보장이 없으면 임시 위치에 받은 뒤 확보한 빈 폴더로 옮긴다. 봉인 묶음이면 임시 위치도 `outputs/sealed/` 아래에 두고 같은 금지(N10)를 받는다.
    - 읽기 전용 입력: 읽기 전용 입력(앱 코드·설정·스냅샷·봉인 입력)은 작업 폴더와 `read_write` 경로 밖에 둔다(X1의 `/opt/x1`처럼). `include_workdir: true`이면 작업 폴더가 `read_write`에 더해지고, Landlock(리눅스 커널의 파일 접근 제한 기능)은 규칙 하나라도 허용하면 허용하므로 쓰기 가능한 부모 아래의 `read_only` 자식은 막히지 않을 수 있다 [추론: 근거는 https://docs.nvidia.com/openshell/sandboxes/policies(include_workdir가 작업 폴더를 read_write에 더한다)와 https://docs.kernel.org/userspace-api/landlock.html(한 정책 층 안에서는 규칙 하나라도 허용하면 허용한다)]. 로드맵 MT5 리허설에서 작업 폴더 아래 `read_only` 하위 경로에 탐침 파일(시험용으로 새로 만드는 빈 파일)을 써 본다. 검토 후보는 `include_workdir: false`에 `read_write: [<출력 폴더>]`만 두는 구성이다. 프록시 모드(기본값)는 `/tmp`를 기본 쓰기 경로로 더하므로, 이 구성도 출력 폴더만 쓰기 가능하게 만들지는 않는다 [사실: 공식 정책 문서 docs/sandboxes/policies.mdx(main 브랜치)]. 설치 판 0.0.116에서의 동작은 로드맵 MT5에서 확인한다 [미확인]. 이때의 CLI 동작과 download 가능 여부는 [미확인]이다.
    - 반입 목록: 이미지 빌드나 upload로 들이는 파일은 명시한 포함 목록으로 고른다. `.env`, `outputs/`, `artifacts/eval/`, 정답표(`eval/dev/oracle_ABC.json`, dev20 정답표), `eval/scorer/`는 빼도록 명시한다. 저장소 루트나 `eval/dev/`를 통째로 올리지 않는다.
    - upload 주의: 근거는 공식 문서이고 [사실: 공식 문서 manage-sandboxes "Transfer Files"], 우리 환경에서의 확정은 로드맵 MT5에서 한다 [미확인]. Git 저장소 안의 경로를 올리면 upload는 기본으로 `.gitignore`를 따른다. 추적 파일이 섞인 경로를 올리면 무시 대상(이 저장소에서는 스냅샷 SQLite와 `raw/` 등, §10.2)은 빠진다. 모든 파일이 무시 대상인 경로(예: `snapshot.sqlite` 하나)는 경고와 함께 거르지 않고 올라간다. 그래서 `.gitignore`는 제외 장치가 아니고, 제외는 명시한 반입 목록이 맡는다. `--no-git-ignore`는 `.env`가 없는 경로에만 쓰고, 이 주의는 모든 파일이 무시 대상일 때 거르지 않고 올리는 자동 전환에도 똑같이 걸린다. 목적지를 빼면 샌드박스 작업 폴더에 올라간다. upload는 심볼릭 링크를 그대로 두고, 이미 있는 폴더에는 합쳐 덮어쓴다. 원문은 "By default, uploads inside a Git repository respect `.gitignore` rules so that build artifacts, dependency caches, and other ignored files are not transferred.", "If `.gitignore` filtering excludes every file in the upload path, the CLI falls back to an unfiltered upload and prints a warning.", "Pass `--no-git-ignore` to opt into unfiltered uploads explicitly, upload a path outside the Git work tree, or force-add the intended files if they should remain Git-aware.", "When you omit the destination, OpenShell discovers the sandbox's working directory and uploads there."이다.
  - 권고는 (나)다 [DESIGN: 오케스트레이터 권고, 2026-09-24(목) 사용자 확인(PR #18)]. 1차 근거는 공식 문서다. CLI는 샌드박스의 정식 작업 폴더를 찾아 그 안으로 풀리는 샌드박스 쪽 원본만 받고, 글자 그대로(예: `/sandbox/../etc/passwd`)나 심볼릭 링크로 그 밖으로 벗어나는 경로는 전송 전에 거부한다 [사실: 공식 문서 manage-sandboxes "Transfer Files", https://docs.nvidia.com/openshell/sandboxes/manage-sandboxes]. 원문은 "The CLI discovers the sandbox's canonical working directory and only allows sandbox-side sources that resolve inside it."와 "Paths that escape lexically, such as `/etc/passwd` or `/sandbox/../etc/passwd`, and paths that escape through a symlink are refused before any data is transferred."이다. X1 임시 시험 기록(아래 X1 항목의 옛 이름 위치)의 "저장소 파일·봉인 입력 반입 방식" 행과 "NAT 실행 추적 산출물 위치" 행은 OpenShell 0.0.116에서 같은 동작을 관찰한 보강 근거다. X1은 샌드박스 안 `/sandbox/x1-runs/<run_id>/`에 쓰고 download로 호스트에 받았다. 작업 폴더 `/sandbox`는 X1 이미지에서 관찰한 값이다 [사실: X1 임시 시험 기록, X1 PR로 병합 예정]. X1은 저장소 파일을 이미지 빌드나 `openshell sandbox upload`로 들여 호스트 폴더를 열지 않았다. 최종 확정은 로드맵 MT5(샌드박스 출력 방식과 봉인 입력 반입 방식의 확정·리허설)와 MT7(샌드박스 밖 실행기)에서 한다.
  - 채점기 출력(정답표에서 온 값)은 샌드박스가 읽거나 쓸 수 있는 곳(허용 목록과 작업 폴더)에 두지 않는다. 커밋 사본 `artifacts/eval/score-{시각}/`도 같다. (나)에서는 어떤 샌드박스도 `outputs/`를 열지 않으므로 채점 실행 폴더 `outputs/score-{시각}/`가 이 조건을 채우고, 커밋 사본은 반입 목록에서 뺀다.
- X1 임시 시험 기록은 옛 이름 `artifacts/openshell/violation_tests.md`, `artifacts/openshell/logs/`(커밋)와 `artifacts/runs/`(X1이 받은 실행 추적, 커밋 안 함)를 그대로 쓰고 새 이름 폴더로 옮기지 않는다(X1 결정 기록이 이 경로를 인용하고 결정 기록은 고치지 않는다). 규범 G2(팀 채점 규범 `SCORING_GOLDEN_RULE.md`의 교육 미션 정합성 게이트, 룰북 A1)의 증거로는 이 위치도 읽지만, 평가 묶음의 실행 조건 대조(룰북 B7)는 채점 요약 `scorer_summary-{시각}.md`에 적은 새 이름 폴더만 쓴다.
- 결정 기록의 `{실행 이름}-{시각}`이 이 절의 실행명이다.
- 이 규칙은 계약 필드·키·값 집합을 바꾸지 않으므로 `schema_version`을 올리지 않는다(§13.2).

## 11. 단위와 정밀도

### 11.1 규칙

원문 근거는 구 개발계획 §3 표 다음 문단이다 [사실]: "수치 입력은 정수/Decimal로 보존합니다. 원자료의 천 USD→USD는 단위 메타데이터 확인 후 변환하고, 이미 USD인 API에 다시 ×1000하지 않습니다. BACI의 천 USD/톤과 관세청의 월별 USD/kg는 자동 혼합하지 않습니다."

| 규칙 | 내용 | 근거 |
|---|---|---|
| 금액 | `amount_usd`는 USD 정수다. 관세청 API의 수입금액(`impDlr`)을 그대로 쓴다. 수입 금액 기준은 CIF 과세가격 미화 달러다 | [사실: 메모 §1, 수집기] |
| 중량 | `net_weight_kg`는 kg 정수(순중량)다. 수입중량(`impWgt`)을 그대로 쓴다 | [사실: 메모 §1, 수집기] |
| 수치 보존 | 입력 수치는 정수 또는 Decimal(반올림 오차 없이 십진 소수를 다루는 수 형식)로 보존한다 | [사실: 구 개발계획 §3] |
| 금액 대조 | 하위 행 합과 총계·부모값은 정확히 일치해야 한다 | [사실: 메모 §1·§2, v2 국가별 부모-하위 대조 2,096건 일치] |
| 중량 대조 | 허용오차 출발값은 0.5kg×(행수+1)이다. 행마다 정수 kg로 반올림돼 있기 때문이다. 최종값은 D가 제안하고 사용자가 승인해 `configs/policy_v1.json`에 적는다 | [사실: 메모 §1, 수집기 `WEIGHT_ROUNDING_KG`] [DESIGN: 명세 §3.3] |
| 임의 허용오차 금지 | 반올림 방식을 모르면 임의의 1% 허용으로 덮지 않는다. 금액과 중량을 따로 검증한다 | [사실: 구 개발계획 §4.2] |
| 천USD 이중 변환 금지 | 이 API의 금액은 이미 USD다. ×1000을 하지 않는다. 과거 collector(옛 수집 코드)의 천 USD 값과 섞지 않는다 | [사실: 수집기 머리말, 구 개발계획 §3] |
| BACI 혼합 금지 | BACI(천 USD/톤, 연간, FOB 기준으로 수출·수입 신고를 맞춘 자료)와 관세청 자료(USD/kg, 월별, CIF)를 한 지표 안에서 섞지 않는다. BACI는 `g1` 비교 대상 선택과 문맥 표시에만 쓴다 | [DESIGN: 분담 D4, 명세 §3.4] |
| 분모 | 점유율 분모는 공식 전체국가(`ALL`) 합계다. 선택국 합계를 전체 분모로 쓰지 않는다 | [DESIGN: 명세 §3.2·§3.3] |
| 0·미상 | 기준월 값이 0이거나 미상이면 변화율을 계산하지 않는다(`null` + 사유). 중량이 0이면 단가를 계산하지 않는다. 빈 응답을 0으로 채우지 않는다 | [DESIGN: 명세 §3.3] |
| 수입 0 명시 | 수입 0이 명시된 달은 `OBSERVED`(값 0)다 | [DESIGN: 명세 §4.3] |

- 금액>0인데 중량 0인 행 677개(금액 중앙값 96 USD)가 `min_amount`·`min_weight` 기준의 근거다 [사실: 메모 §3] [DESIGN: 명세 §3.3].

### 11.2 지표 기호와 단위 [DESIGN]

기호는 명세 §3.3 공식에서 가져왔고, `residual`은 분해 잔차를 담으려고 더했다. 지표 값(`metric` 객체의 `value`)과 typed claim의 `value`는 이 표의 단위로 적는다.

| 기호 | 뜻 | 공식(명세 §3.3) | `unit` |
|---|---|---|---|
| `V` | 금액 | 관측치의 `amount_usd` | `USD` |
| `Q` | 순중량 | 관측치의 `net_weight_kg` | `kg` |
| `U` | 단가(kg당 금액) | `U_t = V_t / Q_t`(V·Q는 부모 HS6 행) | `USD/kg` |
| `r_U` | 단가의 전년동월 변화율 | `r_U = U_t / U_(t-12) - 1` | `%` |
| `s` | 점유율 | `s_t = V_country,t / V_world,t`(분자는 부모 HS6 행, 분모는 `ALL` HS10 월 행 합) | `%` |
| `d_s` | 점유율 변화 | `d_s = s_t - s_(t-12)` | `pp` |
| `within_effect` | 하위품목(HS10) 단가 변화 효과 | `Σ_i ((w_i,0 + w_i,1)/2) * (u_i,1 - u_i,0)` | `USD/kg` |
| `mix_effect` | 하위품목 구성(중량 비중) 변화 효과 | `Σ_i ((u_i,0 + u_i,1)/2) * (w_i,1 - w_i,0)` | `USD/kg` |
| `residual` | 분해 잔차 | `ΔU - (within_effect + mix_effect)`, 여기서 `ΔU = U_t - U_(t-12)`(부모 HS6 행 단가의 차) | `USD/kg` |
| `w@<HS10 코드>` | 하위품목의 중량 비중(모니터링 근거) | `w_i,t = Q_i,t / Σ_i Q_i,t` | `%` |

- `r_U`, `s`, `w@<HS10 코드>`는 비율에 100을 곱한 백분율 수치로 적는다. `d_s`는 두 점유율 백분율의 차이(pp, 퍼센트포인트)로 적는다. 예를 들어 비율 -0.4는 `r_U` -40.0(`%`)이다. 이 ×100은 비율을 백분율로 적는 표기 변환일 뿐이며, 금지한 천USD ×1000 변환과 다르다.
- 분해식은 동일 HS10 집합에서 양 시점 중량이 유효하고 부모 합계가 맞을 때만 쓴다. 비중은 금액 비중이 아닌 중량 비중 `w_i,t = Q_i,t / Σ_i Q_i,t`다. 분해 잔차·개별 하위변화·상쇄를 함께 돌려준다 [DESIGN: 명세 §3.3].
- **원천 규칙** [DESIGN]: 단가 `U_t`는 부모 HS6 행(HS4 스캔 요청이 준 상대국별 HS6 행, §2.3.2)의 `V`/`Q`다. HS10 하위 행은 구성효과 분해와 부모 대조(금액 정확 일치, 중량 0.5kg×(행수+1))에만 쓴다. 점유율 분자는 부모 HS6 행의 `V`이고, 분모는 그 HS6 아래 `ALL` HS10 월 행의 금액 합(중복 제거 뒤)이다. 부모 행과 HS10 합의 금액은 정확히 같다 [사실: 메모 §2, 국가별 부모-하위 대조 2,096건 일치].
  - 근거: oracle은 `parent`의 V·Q로 `U0`·`U1`을 정하고 `residual`을 따로 둔다 [사실: oracle]. 구 개발계획도 분해 조건으로 "부모 합계"를, 모니터링 근거로 "부모 대조"를 쓴다 [사실: 구 개발계획 §4.2·§5.1].
  - `metrics/` 패키지, 검증기, 독립 채점기는 모두 이 원천 규칙을 쓴다. 원천이 갈리면 맞는 주장이 `WRONG_VALUE`가 될 수 있기 때문이다.
  - 참고: v2에서 전년동월 비교가 가능한 품목×국가×월 조합은 부모 HS6 행 기준 1,267개(그중 단가 변화율 절댓값 30% 이상 771개), HS10 합 기준 1,265개(767개)다 [사실: v2 SQLite 조회].
- HS10 하위품목의 지표는 `U@<HS10 코드>`, `r_U@<HS10 코드>`, `w@<HS10 코드>`만 쓴다(§6.2). `U@`·`r_U@`의 단위와 표시 자릿수는 `@` 앞 기호를 따르고, `w@`는 이 표와 §11.3 표를 따른다 [DESIGN].
- `configs/policy_v1.json`의 탐지 기준값도 이 단위로 적는다. 단위 예: 개발 제안값 30%는 `30`, 10pp는 `10`으로 적는다(`0.3`·`0.1`이 아님). 확정값은 D가 제안하고 사용자가 승인한다 [DESIGN].
- 한국어 문장에서는 퍼센트포인트를 `%p`로 적고, typed claim의 `unit`은 `pp`로 적는다. 보고서 틀은 `pp` 값을 문장에서 `%p`로 적고, 산문 패턴 목록(룰북 B3-2)은 `%p`와 `pp`를 같은 단위로 본다 [DESIGN].
- 기호를 늘리거나 단위를 바꾸려면 §13 절차를 따른다.

### 11.3 표시 자릿수와 반올림 [DESIGN, 조정값]

지표별 표시 자릿수는 이 표가 정한다. 보고서 틀(M 트랙 `reports/` 패키지), 검증기, 독립 채점기가 모두 이 형식을 쓰고, 룰북은 이 표를 가리켜 허용오차를 적용한다.

| 기호 | 단위 | 표시 자릿수 |
|---|---|---|
| `V` | `USD` | 정수 |
| `Q` | `kg` | 정수 |
| `U` | `USD/kg` | 소수 2자리 |
| `r_U`, `s` | `%` | 소수 1자리 |
| `d_s` | `pp` | 소수 1자리 |
| `within_effect`, `mix_effect`, `residual` | `USD/kg` | 소수 2자리 |
| `w@<HS10 코드>` | `%` | 소수 1자리 |

- `U@<HS10 코드>`·`r_U@<HS10 코드>`는 `@` 앞 기호의 자릿수를 쓴다.
- 반올림은 사사오입(ROUND_HALF_UP)이다. 표시값과 기대값은 정수 USD·kg에서 Decimal(오차 없는 십진 연산)로 계산해 반올림한다. 부동소수 반올림을 쓰지 않는다.
- 주장 채점의 값 비교 허용오차는 이 표시 자릿수의 반올림 기준이다(§7 원문). 적용 방법은 룰북 B3-1이 정한다.
- 이 표는 `RB-1` 동결 대상이다. 동결 뒤 바꾸려면 룰북 새 버전과 사유가 필요하다.

### 11.4 시간·코드 표기 [DESIGN]

- 월 키는 `YYYYMM`(예: `202401`), 연 키는 `YYYY`다 [DESIGN: 분담 D3]. 기준월은 비교월보다 12개월 앞선 달(전년 같은 달)이다.
- 전년동월 판정이 가능한 달은 2023-01~2024-12(24개월)다 [DESIGN: 명세 §3.2].
- 시각은 KST ISO 8601 형식(한국 표준시, 예: `2026-09-24T09:00:00+09:00`, 초 단위)으로 적는다. 기존 수집기가 이 형식을 쓴다 [사실: 수집기].
- HS6는 HSK 앞 6자리 문자열이며, BACI HS22의 품목 코드처럼 앞자리 0을 지킨다 [DESIGN: 분담 D3].
- 상대국은 관세청 2자리 국가코드(`KCS_cntyCd`)로 적는다. BACI 국가 코드(예: 한국 410)는 `peer_group`의 `baci_country_code`에만 쓴다 [DESIGN: 분담 D3·§4].

### 11.5 oracle_ABC 숫자 대응

`metrics/` 패키지는 oracle A/B/C를 그대로 재현해야 한다 [사실: 인계 §3]. oracle 키와 이 계약의 기호는 다음처럼 대응한다(예시 값은 A 사례) [사실: oracle].

| oracle 키 | 계약 기호와 단위 | 예(A 사례) |
|---|---|---|
| `U0`, `U1` | `U`(`USD/kg`), 기준월·비교월. oracle은 `parent`의 V·Q로 정한다 | 6.0, 3.6 |
| `r_U` | `r_U`(`%`). oracle은 비율로 적는다 | -0.4 → -40.0 |
| `s0_pp`, `s1_pp` | `s`(`%`). oracle은 백분율 수치로 적는다 | 10.0, 6.0 |
| `d_s_pp` | `d_s`(`pp`) | -4.0 |
| `within`, `mix` | `within_effect`, `mix_effect`(`USD/kg`) | 0.0, -2.4 |
| `residual` | `residual`(`USD/kg`) | 0.0 |
| `V`, `Q` | `V`(`USD`), `Q`(`kg`) | 기준월 부모 600, 100 |
| `V_country_0`, `V_world_0` 등 | 상대국 행과 `ALL` 행의 `V`(`USD`) | 600, 6000 |
| `threshold_pp` | 정책 기준값(점유율 변화 10pp). 계약 값이 아니라 정책 값이다 | 10 |

## 12. 봉인 해시 기록

### 12.1 대상과 위치 [DESIGN: 명세 §3.6, §4.12]

- 봉인은 평가 전까지 개발 에이전트가 보지 않도록 자료를 저장소 밖에 격리하고, 해시로 변조를 드러내는 보관 방식이다.
- 봉인 대상은 `holdout40`의 입력과 정답표, `real_sealed`의 사례 목록과 채점 표본이다.
- 위치는 저장소 밖 `~/.tradesentry/sealed/`이고, 환경변수 `TRADESENTRY_SEALED_DIR`로 바꿀 수 있다. 에이전트 작업 폴더에도 두지 않는다.
- 커밋하는 것은 해시 목록 `eval/sealed_manifest.json`뿐이다. 원본 파일은 최종 채점이 끝난 뒤 커밋한다.

### 12.2 기록 형식 [DESIGN]

`eval/sealed_manifest.json`은 봉인 파일마다 파일명, sha256, 생성 시각, 생성 주체를 한 항목으로 적는다.

```json
{
  "schema_version": 1,
  "files": [
    {
      "dataset": "holdout40",
      "file_name": "<봉인 폴더 기준 상대경로>",
      "sha256": "<16진수 소문자 64자>",
      "created_at": "<KST ISO 8601 시각>",
      "created_by": "<생성 주체의 역할 이름>"
    }
  ]
}
```

| 키 | 뜻 | 규칙 |
|---|---|---|
| `dataset` | 봉인 묶음 | `holdout40` 또는 `real_sealed` |
| `file_name` | 파일명 | 봉인 폴더(`TRADESENTRY_SEALED_DIR`) 기준 상대경로. 절대경로를 쓰지 않는다. 품목·상대국·월처럼 봉인 사례를 드러내는 정보를 파일 이름에 넣지 않는다(이 목록은 커밋되어 누구나 본다) |
| `sha256` | 내용 해시 | 파일 바이트 그대로의 sha256, 16진수 소문자 64자 |
| `created_at` | 생성 시각 | 파일을 만든 시각, KST ISO 8601 |
| `created_by` | 생성 주체 | 만든 주체의 역할 이름(예: "holdout40 생성 에이전트"). 계정·경로·비밀값을 쓰지 않는다 |

- 목록에 있는 파일이 봉인 폴더에 없거나 해시가 다르면 불일치로 본다. 목록에 없는 파일이 봉인 폴더에 있어도 불일치로 본다. 채점기는 목록에 있는 파일만 읽는다 [DESIGN].

### 12.3 절차: 생성 → 봉인 → 해시 등록 → 한 번 채점 [DESIGN: 명세 §3.6]

1. 생성: `holdout40` 생성 에이전트(모델 트랙과 격리된 Claude 보조 에이전트)는 시나리오 명세와 생성 규칙만 입력으로 받는다. 결과를 봉인 폴더에 직접 기록하고 저장소에는 쓰지 않는다. 생성 에이전트는 런타임 코드를 작성하지 않고, 그 대화 기록은 모델 트랙에 넘기지 않는다.
2. 봉인: 생성 직후 파일별 sha256 목록을 만든다.
3. 해시 등록: 해시 목록(`eval/sealed_manifest.json`)만 PR로 커밋한다.
4. 한 번 채점: 룰북 `RB-1` 동결 뒤 오케스트레이터(작업을 배분·병합하는 주관 에이전트)가 평가 스킬 ②(`skills/tradesentry-eval/SKILL.md`)를 실행할 때만 봉인 입력을 샌드박스에 읽기 전용으로 넣는다. 공식 채점 대상 실행 전용 샌드박스를 새로 만들어 넣고, 개발·시연용 샌드박스에는 넣지 않는다. 넣는 방식은 X1(세로형 최소 통합 시험) 뒤에 확정한다 [미확인]. 정답표는 어떤 샌드박스에도 넣지 않고 샌드박스 밖 채점기만 읽는다.
5. 채점 전 재대조: 해시를 다시 대조한다. 일치하지 않으면 그 묶음의 채점을 무효로 하고 사용자에게 올린다.

- `real_sealed`의 사례 목록과 표본도 같은 절차를 따른다. 다만 `real_sealed`에서 4단계의 봉인 입력 전달은 룰북 B5와 부록 40번(사용자 확인 대기)을 따른다. 지금 안은 목록·표본 파일을 샌드박스에 넣지 않고, 샌드박스 밖 실행기(프로그램, 로드맵 MT7)가 해시 대조 뒤 사례 식별자를 `run-case`에 한 건씩 넘기는 것이다.
- `real_sealed` 표본 추출 seed는 표본을 뽑기 전에 nonce를 넣은 파일로 만들어 봉인 폴더 안에 두고(해시 목록 대상), 그 파일의 sha256을 분할 seed와 함께 `policy_v1` 제안 전에 결정 기록으로 커밋한다(§4.2). seed 파일(nonce 포함)은 채점이 끝난 뒤 공개한다 [DESIGN].

### 12.4 정직한 한계 [DESIGN: 명세 §3.6]

- 봉인 폴더 위치는 문서에 적혀 있으므로 비밀이 아니다.
- 개발 에이전트가 같은 OS 사용자로 돌기 때문에 열람을 기술적으로 막지는 못한다. 지시와 기록으로 관리한다.
- 기술적 차단은 런타임 샌드박스(OpenShell 정책)에만 해당한다. 해시는 변조를 드러낼 뿐 열람을 막지 않는다.
- `real_sealed` 시계열은 개발에 쓰는 같은 스냅샷(`kcs_202201_202412_v2`)에 있다. 사례 목록(표본 추출 전 경보 목록)은 결정 기록에 커밋된 분할 seed·스냅샷·승인된 `policy_v1`로 다시 계산할 수 있다. 다만 표본 추출 seed는 봉인돼 있으므로, 40건을 넘을 때 뽑힌 표본은 seed를 공개하기 전까지 다시 계산할 수 없다. 그래서 봉인은 열람 차단이 아니라 표본 고정·변조 탐지 수단이다.
- 모델 트랙 에이전트와 Codex(교차 검토와 작은 코드 구현을 맡는 별도 코딩 에이전트)의 작업 지시에 봉인 폴더를 넣지 않고, 읽지 말라고 지시한다.

## 13. 변경 절차

### 13.1 공용 약속 변경은 사용자 승인 [DESIGN: 명세 §3.10]

- 대상: 자료 형식(계약 필드), 상태값, 기준값, 도구 한도, 품목·국가 확정, 평가 구성, 제출서 주장 문구
- 절차
  1. 계약 버전(`schema_version`)을 올린다.
  2. 합성 시험자료(`controlled_fixture_v0`)를 새 계약으로 다시 만든다.
  3. 양 트랙(M·D)이 검토한다.
  4. 사용자가 승인한다.
- 승인을 기다리는 동안에는 그 약속에 의존하는 작업만 멈춘다.
- 그 밖의 세부는 에이전트가 정하고 결정 기록에 남긴다.

### 13.2 버전을 올리는 변경과 올리지 않는 변경 [DESIGN]

- 버전을 올린다: 필드·키의 추가·삭제·이름 변경, 값 집합(상태값, 모드, `claim_type`, `direction`, 주장 채점 결과, §11.2의 기호와 단위) 변경, ID 형식 변경, 단위·정밀도 규칙 변경.
- 버전을 올리지 않는다: 값을 바꾸지 않는 설명 보강과 오탈자 수정. 이런 수정도 PR과 검토를 거친다.
- 2026-09-24(목) 사용자 결정으로 고친 경로 표(§10)와 새 이름·출력 규칙(§10.3)은 `schema_version`을 올리지 않는다. 계약 필드·키·값 집합(§2~§9, §11)이 그대로이기 때문이다. `run_id`에 형식(§10.3 N5)을 준 일도 위의 "ID 형식 변경"으로 보지 않는다. v1이 형식을 정하지 않았던 ID(§4.5)에 처음 형식을 준 것이고, 그 형식으로 저장된 자료가 아직 없다 [추론]. 증거 파일 이름을 바꾼 것은 `RB-1` 동결 전 룰북 초안을 고친 것이라 룰북 버전(`rulebook_version`)도 `RB-1` 그대로다.
- §11.3 표시 자릿수 표는 `RB-1` 동결 대상이다. 동결 뒤 바꾸면 계약 버전 외에 룰북 새 버전과 사유도 필요하다 [DESIGN].
- 명세 §4와 글자 그대로 같아야 하는 값을 바꾸려면 명세도 사용자 승인을 받아 함께 고친다(명세의 오류는 사용자 승인으로만 고친다).

### 13.3 혼자 바꾸면 안 되는 것 [사실: 분담 §6]

신호 개수(2개), 임계값·허용오차, 도구 8회·재조사 1회 예산, 상태값 집합, HS4/HS6/비교국 확정, `grouping_version` 동결 후 변경, 평가 20/40 구성, 마감·적격성 주장 문구, 데이터 계약 필드 추가/삭제.

### 13.4 함께 고칠 것

- §10 경로 표의 이름이 S0 외부 자문으로 바뀌면 그 표와 참조 문서를 함께 고친다(§10 표 머리의 규칙). 표의 사본은 `docs/plan/DEV_PLAN.md` §10.1과 `docs/plan/SCAFFOLD_BRIEF.md` §2.3에 있고, 세 표는 글자까지 같게 둔다.
- 외부 자문이 공용 약속을 바꾸자고 하면 13.1 절차와 사용자 승인을 거친다 [DESIGN: 명세 §3.8, §5].
- 값이 바뀌면 문서 간 값 대조 검사를 다시 돌려 다른 문서에 철자가 다른 변형이 없는지 확인한다 [DESIGN: 명세 §6].

### 13.5 동결 뒤 변경

- 룰북 `RB-1`은 2026-09-26(토) 12:00(조정값)에 동결한다. 동결 뒤 변경은 새 버전과 사유로만 하고, 결과를 본 뒤 유리하게 고치지 않는다 [DESIGN: 명세 §3.6].
- 봉인 채점에 영향을 주는 계약 변경도 같은 규칙을 따른다 [추론: 명세 §3.6 동결 규칙].

### 13.6 기록

- 변경 이유와 승인 결과는 프로젝트 결정 기록 `docs/tracking/decisions/`에 남긴다 [DESIGN: 명세 §3.10].
- 변경 PR 본문에는 검사 명령, 종료 코드, 검토 판정 요약을 남긴다 [DESIGN: 명세 §3.10].

## 용어 설명

- **자료 계약(data contract)**: 두 트랙이 주고받는 객체·필드·값의 형식을 미리 정한 약속. 이 문서가 그 v1이다.
- **모델 트랙(M) / 데이터 트랙(D)**: 구현을 나누는 두 작업 흐름. M은 판정 정책·조사 흐름·NVIDIA 연동·그룹핑, D는 수집·지표·합성/평가 자료·채점기를 맡는다.
- **인수물**: D가 M에게 넘기는 자료·코드 묶음. 넘길 때 인수 조건을 확인한다.
- **`schema_version`**: 자료 계약의 버전 번호. 이 문서(v1)의 값은 1이다.
- **스냅샷(snapshot)**: 한 시점에 수집해 동결한 원자료 묶음(raw 응답, manifest, SQLite). 모든 조회의 유일한 원천이다.
- **raw 응답**: API가 돌려준 응답 파일을 손대지 않고 저장한 것.
- **manifest**: 스냅샷을 만들 때 보낼 수집 요청 목록과 설정을 적은 파일(`manifest.json`).
- **관측치(observation)**: 수집 요청 × 월 × 상대국 × HS 코드 × 흐름 단위의 금액과 순중량 한 행. 총계 행과 `NOT_COLLECTED` 행도 같은 테이블에 있다.
- **수집 기록(collection_receipt)**: 수집 요청 1건의 결과(성공·실패, 응답 해시, 행 수)를 적은 기록.
- **지표(metric)**: 관측치로 계산한 값(단가, 변화율, 점유율, 구성효과 등)과 그 입력 근거.
- **사례(case)**: 코드가 정책으로 탐지한 경보 1건(품목 × 상대국 × 월 + 기준월 + 신호 2종).
- **신호**: 경보를 일으키는 두 가지 변화. `unit_value`(단가)와 `share`(점유율)다.
- **비교 대상 집합(`peer_group`)**: 대상국과 비교할 상대국 목록. `g0`은 고정 목록, `g1`은 BACI 유사도 방식이다.
- **superset**: 수집한 상대국 16개 전체 집합. 비교 대상은 이 안에서만 고른다.
- **typed claim**: 정해진 필드를 가진 사실 주장 1건. 보고서의 모든 사실 주장은 이 형식이다.
- **근거 ID(evidence ID)**: 주장이나 지표가 기대는 스냅샷 행 하나를 가리키는 문자열. 형식은 `ev:<snapshot_id>:<table>:<rowid>`다.
- **rowid**: SQLite가 테이블의 행마다 붙이는 정수 번호.
- **SQLite**: 파일 하나로 된 가벼운 데이터베이스. 스냅샷 자료를 담는다.
- **도구 봉투(envelope)**: 도구 5개가 같은 모양으로 돌려주는 출력 틀.
- **검증기(validator)**: 실행 중에 보고서의 숫자·단위·근거·상태·금지 문구를 검사해 잘못된 보고서를 막는 코드. `freeform` 모드에서는 기록만 한다.
- **독립 채점기(scorer)**: 런타임 코드를 쓰지 않고 따로 만든 정답 계산·채점 프로그램(`eval/scorer/`).
- **채점 대상 실행 / 정답 대조 채점**: 샌드박스 안에서 돌리는 평가 실행 / 샌드박스 밖에서 결과를 정답과 비교하는 일.
- **조사자 / Critic(검수자)**: 도구를 골라 근거 포함 초안을 쓰는 모델 역할 / 그 초안만 보고 누락·반대 설명을 지적하는 별도 문맥의 같은 모델.
- **봉인(sealed)**: 평가 전까지 개발 에이전트가 보지 않도록 저장소 밖에 격리하고 해시로 변조를 드러내는 보관 방식.
- **sha256**: 파일 내용으로 계산하는 64자리 16진수 지문. 내용이 한 글자만 바뀌어도 값이 달라진다.
- **KST ISO 8601**: 한국 표준시(UTC+9)를 붙인 국제 표준 시각 표기(예: `2026-09-24T09:00:00+09:00`).
- **전년동월**: 비교월 t와 12개월 전 같은 달 t−12를 비교하는 방식.
- **단가(단위가치)**: 금액(USD) ÷ 순중량(kg). kg당 금액이다.
- **점유율**: 한 상대국의 금액 ÷ 전체국가(`ALL`) 금액.
- **pp(퍼센트포인트)**: 백분율끼리의 차이를 나타내는 단위. 10%에서 6%로 바뀌면 -4pp다.
- **구성효과 / 구성효과 분해**: 하위품목(HS10) 비중 변화 때문에 생긴 평균 단가 변화(`mix_effect`) / 평균 단가 변화를 하위품목 단가 변화 효과(`within_effect`)와 구성효과(`mix_effect`)로 나누고, 남는 차이를 잔차(`residual`)로 두는 계산.
- **HS 코드 / HSK / HS6 / HS10**: 국제 품목분류 번호 / 그 한국 세분류(관세청 HS 부호) / 앞 6자리 품목 / 한국이 10자리까지 나눈 하위품목.
- **`ALL`**: 전체국가 합계 행을 나타내는 상대국 코드. 점유율의 분모다.
- **CIF / FOB**: 운임·보험료를 포함한 수입 가격 / 선적항 본선 인도 기준의 수출 가격.
- **BACI**: CEPII가 각국 신고를 맞춰 만든 연간 국제무역 자료(천 USD/톤). 이 계약에서는 비교 대상 선택과 문맥 표시에만 쓴다.
- **코사인 유사도**: 두 벡터가 얼마나 닮았는지 나타내는 값. 1에 가까울수록 비슷하다.
- **Louvain**: 네트워크를 서로 가까운 무리로 나누는 알고리즘. 여기서는 문맥용 라벨만 만든다.
- **JSONL**: JSON 하나를 한 줄에 적는 기록 파일 형식.
- **frontmatter**: 파일 맨 앞 `---` 두 줄 사이에 적는 메타데이터.
- **결정적(deterministic)**: 같은 입력이면 늘 같은 결과가 나오는 성질.
- **조정값**: 운영하며 바꿀 수 있는 수치나 이름. 바꾸면 기록을 남긴다.
- **oracle**: 사례의 정답을 미리 계산해 둔 표. 여기서는 `eval/dev/oracle_ABC.json`의 합성 A/B/C 사례다.
- **NAT(NeMo Agent Toolkit)**: 에이전트 실행을 감싸 추적·프로파일·사후 평가를 하는 NVIDIA 도구 모음.
- **OpenShell**: 에이전트를 격리 실행하는 NVIDIA 샌드박스 런타임. 파일·네트워크 접근을 정책으로 제한한다.
- **Agent Skills / SKILL.md**: 에이전트가 불러 쓰는 작업 지침 묶음의 규격 / 스킬 하나의 지침 파일.
- **S0 / X1**: 구현 첫 단위인 앱 스캐폴딩(외부 자문 체크포인트) / 설치부터 차단 로그까지 한 줄로 잇는 세로형 최소 통합 시험.
- **오케스트레이터**: 작업을 배분하고 병합을 결정하는 주관 에이전트.
- **Claude 보조 에이전트**: 작업 하나를 맡아 실행하는 Claude 하위 에이전트. 두 트랙의 구현을 맡는다.
- **Nemotron**: NVIDIA의 대형 언어 모델. 조사자와 Critic이 같은 모델을 별도 문맥으로 쓴다.
- **NIM**: NVIDIA가 모델을 API로 제공하는 추론 서비스.
- **Codex**: 교차 검토와 작은 코드 구현을 맡는 별도 코딩 에이전트.
- **MVP**: 최소 기능 제품. 2026-09-25(금)에 MVP 시험을 한다.
- **CLI**: 명령줄에서 실행하는 도구. 여기서는 `tradesentry <명령>`이다.
- **PR(pull request)**: 변경을 main에 합치기 전에 검토받는 요청.
- **git 커밋 해시**: 코드의 특정 버전을 가리키는 고유 문자열.
- **룰북**: 평가 규칙과 채점 기준을 정한 문서(`docs/eval/RULEBOOK.md`).
- **자료 접근층(`dal/`)**: 스냅샷을 읽는 함수 모음 패키지. 도구는 이것을 거쳐 자료를 읽는다.
- **결정 기록**: 결정과 그 이유를 남기는 문서.
- **JSON**: 키와 값으로 된 텍스트 자료 형식.
- **trace**: 실행 중 호출과 응답을 순서대로 남긴 기록.
- **스키마 검사**: 보고서가 정해진 필드와 형식을 갖췄는지 보는 검사.
- **샌드박스**: 프로그램을 격리해 허용한 파일·네트워크만 쓰게 하는 실행 환경.
- **provider 자동 재시도**: 모델 API 호출 라이브러리가 스스로 요청을 다시 보내는 기능. 이 계약에서는 끈다.
- **5xx**: 서버 오류를 뜻하는 HTTP 응답 코드(500번대).
- **`resultCode 00`**: 관세청 API가 요청을 정상 처리했음을 알리는 결과 코드.
- **토큰**: 모델이 글을 잘게 나눠 세는 단위. 입력·출력 토큰 수로 비용과 한도를 잰다.
- **wall time**: 실행 시작부터 끝까지 실제로 흐른 시간.
- **seed**: 난수를 다시 똑같이 뽑기 위한 시작값.
- **Decimal**: 반올림 오차 없이 십진 소수를 다루는 수 형식.
- **픽스처(fixture)**: 시험용으로 미리 만든 고정 자료.
- **CEPII**: BACI를 만드는 프랑스의 국제경제 연구기관.
- **HS85 / HS4 8504**: 전기기기와 그 부분품을 담은 HS 제85류 / 그 안의 변압기·정지형 변환기·인덕터 호.
- **HS2022**: 세계관세기구 HS의 2022년 개정판.
- **kVA**: 킬로볼트암페어. 변압기 용량을 나타내는 단위.
- **부모 HS6 행**: HS4 스캔 요청이 돌려준 상대국별 HS6 월 행. 상대국 월 금액·중량의 유일한 원천이다.
- **총계 행**: 응답에 함께 오는 조회 구간 전체 합계 행. `month`가 `RAW:총계`이며 대조에만 쓴다.
- **파생 저장소**: raw 응답과 manifest에서 `snapshot-build`가 만드는 SQLite. 원자료는 바꾸지 않는다.
- **VACUUM**: SQLite 파일을 다시 써서 빈 공간을 정리하는 명령. rowid가 바뀔 수 있어 동결 파일에는 쓰지 않는다.
- **NFC**: 같은 글자를 한 가지 유니코드 코드 순서로 맞추는 정규화 방식.
- **사사오입(ROUND_HALF_UP)**: 버리는 자리가 절댓값 기준 5 이상이면 올리는 반올림.
- **`%p`**: 한국어 문장에서 퍼센트포인트를 적는 표기. typed claim의 `unit`으로는 `pp`를 쓴다.
- **신호 계열**: 주장의 `metric`이 어느 신호(`unit_value`, `share`)에 속하는지의 구분.
- **평가 묶음 실행**: 여러 사례 실행을 한 번에 돌리는 평가 실행(`tradesentry evaluate`). 실행명은 `evaluate-{시각}`이다.
- **패키지**: 파이썬 모듈 파일을 여럿 담는 폴더. `src/tradesentry/` 아래 15개와 `eval/scorer/`·`eval/datagen/`이 있다(§10.3 N2).
- **단위 / 단위 표**: 혼자 실행하고 시험할 수 있게 파일 하나로 만든 가장 작은 구현 조각 / 단위마다 ID·도메인명·파일·소유·입출력을 적은 표(`docs/plan/UNITS.md`).
- **조립**: 따로 만든 단위들을 이어 CLI 명령 하나가 도는 묶음으로 만드는 일. 이때 버릴 것과 합칠 것을 가린다.
- **도메인명**: 단위마다 붙인 출력용 이름 `{패키지}_{단위}`. 출력 파일 이름의 앞부분이 된다(§10.3 N4).
- **실행 이름 / 실행명(`run_id`)**: 시각이 붙지 않은 실행의 이름(예: `run_case`) / 실행 이름에 시작 시각을 붙인 `{실행 이름}-{yymmddhhmmss}`(예: `run_case-260925143015`). 실행 폴더 `outputs/{실행명}/`의 이름이다(§10.3 N5).
- **도메인 출력(`outputs/`)**: 실행마다 폴더 하나에 쌓는 도메인별 출력물. 커밋하지 않는다(§10.3 N6·N9).
- **증거 복사 / 커밋 사본**: 실행 폴더와 같은 이름의 폴더를 `artifacts/{종류}/` 아래에 만들고, 종류마다 정한 커밋 증거 파일만 복사해 커밋하는 일 / 그렇게 커밋한 폴더와 파일. trace는 빼고, 봉인 묶음은 금지 해제 조건이 채워진 뒤에만 한다(§10.3 N10·N11).
- **금지 해제 조건**: 봉인 묶음 실행 사슬의 출력(`outputs/sealed/` 아래)과 봉인 묶음을 채점한 채점기 출력 폴더의 열람·커밋 금지가 풀리는 조건. 봉인 묶음마다 따로 본다. 그 묶음의 정답 대조 채점이 끝나고(채점기 종료 코드 0과 봉인 사건 "채점 완료" 기록), `real_sealed`이면 표본 추출 seed 공개 기록까지 있으면 그 묶음 출력과 그 묶음을 채점한 채점기 출력 폴더가 함께 풀린다. 어느 묶음의 것인지 봉인 사건 기록으로 알 수 없는 폴더는 두 봉인 묶음의 조건이 모두 채워질 때까지 열지 않는다(§10.3 N10).
- **실행 조건 입력 파일 / 배타 생성**: 채점기가 모르는 실행 조건(사전 점검 결과, 샌드박스 이름 등)을 채점기에 넘기는 파일. 내려받기를 끝낸 호스트 쪽 프로그램이 확보한 실행 폴더 안에 만들고, 채점기는 실행 조건을 이 파일에서만 읽는다(§8.2) / 이미 있으면 실패하는 방식의 파일 만들기.
- **승격(무거래 확정)**: 승인된 `policy_v1` 규칙으로 빈 응답 달의 `UNRESOLVED_ZERO` 행을 무거래 확정 `CONFIRMED_NO_TRADE`로 바꾸는 일. 파생 저장소(SQLite)에만 적용하고 raw 응답과 manifest는 바꾸지 않는다(§3.4). 이 문서에서 "승격"은 이 뜻으로만 쓴다.
- **정본 자료**: 다른 단위가 이름으로 읽는 고정 위치의 입력(동결 스냅샷, 정책 수치, 비교국 표, dev20). `outputs/`의 결과를 동결·승인 단계를 거쳐 옮긴다(§10.3 N12).
- **NemoClaw**: 에이전트 실행 틀과 보안 런타임을 묶은 NVIDIA 참조 스택.
- **nonce**: 추측을 막으려고 섞는 한 번 쓰는 임의 값. seed 파일의 해시만 보고 seed를 역산하지 못하게 한다.
- **우회수입**: 제3국을 거쳐 원산지를 바꿔 들여오는 수입. 보고서는 단가·점유율 변화를 그 증거로 쓰지 않는다.
- **중량 비중(`w@<HS10 코드>`)**: 같은 부모 HS6의 HS10 하위 행 순중량 합(Σ_i Q_i,t) 대비 한 하위품목(HS10)의 순중량 비율(%). 분모는 부모 HS6 행의 Q가 아니다. 구성효과를 설명하는 모니터링 근거다.
