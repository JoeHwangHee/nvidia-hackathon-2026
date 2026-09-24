# DT1 스냅샷 빌드와 계약 커널의 세부 결정

DT1(자료 접근층과 계약 커널, 데이터 트랙) 구현에서 자료 계약이 데이터 트랙(D)에게 맡겼거나 정하지 않은 세부를 적는다. 코드와 시험은 DT1 PR에 있다.

용어

- 스냅샷 빌드: 단위 S2(`src/tradesentry/snapshot/build.py`)가 동결 스냅샷의 raw 응답(API가 돌려준 원본 파일)과 manifest(수집 요청 목록)에서 만드는 파생 SQLite(파일 하나로 된 데이터베이스). 정본 자리는 `data/snapshots/{snapshot_id}/snapshot_build.sqlite`다(결정 기록 `20260924-2212-user-decision-snapshot-build-and-g0.md`).
- rowid: SQLite가 행마다 붙이는 정수 번호. 근거 ID(evidence ID, 보고서 주장이 가리키는 스냅샷 행 하나의 식별자 `ev:<snapshot_id>:<table>:<rowid>`)의 마지막 조각이다.
- `normalized_sha256`: 스냅샷 SQLite 행을 rowid까지 넣어 정해진 방식으로 직렬화(값을 바이트 줄로 적는 일)해 구한 sha256(내용 지문).
- 수집기: `src/tradesentry/ingest.py`(관세청 API 수집·검증 코드, 단위 S1).
- 승격: 승인된 정책 규칙으로 빈 응답 달의 `UNRESOLVED_ZERO` 행을 무거래 확정 `CONFIRMED_NO_TRADE`로 바꾸는 일(자료 계약 §3.4).
- DAL(자료 접근층): 단위 K3(`src/tradesentry/dal/query.py`). 도구·지표·판정 정책은 스냅샷을 이것으로만 읽는다.

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 00:02(기록 시각). 결정은 2026-09-24(목) 23:30~2026-09-25(금) 00:00 DT1 구현 중에 했다 |
| 제목 | `normalized_sha256` 직렬화, 스냅샷 빌드의 행 순서·표 형식·빌드 기록, 정책 파일 형식, 근거 ID rowid 표준형, 국가 코드 대응표 열 |
| 결정 | 아래 "결정 내용" ①~⑦과 "2회차 보탬" ⑧~⑩(검토 반영, 같은 PR의 수정 커밋) |
| 이유와 근거 | 아래 "결정 내용"의 항목마다 적었다 |
| 검토한 대안 | 아래 "검토한 대안" |
| 결정 주체 | 소유 트랙(D). ⑤의 정책 객체 모양은 판정 정책 작업(MT1)이 먼저 가정한 모양을 오케스트레이터 알림으로 받아 그대로 맞췄다 |
| 공용 약속 여부 | 아니다. 계약 필드·상태값·ID 형식·기준값의 값을 바꾸지 않는다. ①은 자료 계약 §2.3.1이 D에게 맡긴 직렬화다. ④는 자료 계약 §4.4의 "10진수 양의 정수"를 한 가지 글자열로 읽은 해석이고, 독립 채점기(DT8)도 같은 해석을 써야 두 쪽 판정이 같다 |
| 영향 | 단위 K1~K5·S2·S3·G3, `configs/policy_dev.json`. 받아 쓰는 작업: DT2(지표), DT3(합성 시험자료, 같은 표 형식), DT4 ②(`policy_v1` 제안은 ⑤ 형식), DT7 ②(최종 빌드와 정본 옮기기, 기록 `snapshot_build.json`), DT8(근거 ID 풀기 ④), MT1·MT2·MT5·MT6(정책 객체, DAL, `snapshot-build`·`snapshot-verify` 배선, 비교국 표 CSV 열) |
| 관련 PR | DT1 PR(이 기록) |

## 결정 내용

① **`normalized_sha256` 직렬화** `[DESIGN]`(자료 계약 §2.3.1은 직렬화를 D가 정해 결정 기록에 남기라고 한다)

- 대상 표는 `collection_receipt`, `observation`, `peer_group`, `snapshot_meta` 넷이고 이 이름 순으로 적는다. 그 밖의 표와 색인은 넣지 않는다.
- 표마다 머리 줄 `["table", 표 이름, [열 이름…]]`(열은 표 정의 순서) 한 줄을 적고, 이어서 행마다 `[rowid, 열 값…]` 한 줄을 rowid 순서로 적는다.
- 줄은 JSON 배열이다(파이썬 `json.dumps(값, ensure_ascii=False, separators=(",", ":"))`). 줄 끝에 줄바꿈 하나(`\n`)를 붙인다.
- 값은 INTEGER → JSON 정수, TEXT → JSON 문자열(유니코드 정규화를 하지 않는다), NULL → `null`이다. REAL·BLOB 값이 있으면 계산을 거부한다(빌드는 이런 값을 넣지 않는다).
- 모든 줄을 이어 붙인 UTF-8 바이트의 sha256을 16진수 소문자 64자로 적는다.
- rowid가 줄에 들어가므로 재적재로 rowid가 바뀌면 값이 바뀐다(자료 계약 §4.4 규칙 4). 빌드 시각·경로·정책 버전 같은 출처 정보는 SQLite에 넣지 않으므로, 같은 입력으로 다시 빌드하면 같은 값이 나온다 `[사실: DT1 시험 DeterminismTest, v2 재빌드]`.
- 기록값은 SQLite 밖에 둔다: 개발 빌드는 옆의 `snapshot_build-{시각}.json`, 정본은 `data/snapshots/{snapshot_id}/snapshot_build.json`(단위 S2 `install_build`가 쓴다). 수집기의 `snapshot_hash.json`은 고치지 않는다.
- 참고값: 승인 전 v2 개발 빌드(정책 `dev-0.1`, 승격 없음, 비교국 표 없음)는 `d827b49531a8e4766a198e2c8e803e179b693ed3dc6fca9e1e1c5d389d780ee7`다 `[사실: 2026-09-24(목) 23:52 빌드, 다시 빌드해도 같음, 단위 S3 검증 통과]`. 승격 규칙을 적용하거나 비교국 표를 적재하면 값이 바뀐다. 최종 빌드의 값은 DT7 ②가 정본 기록에 남긴다.

② **행 순서(결정적 rowid)** `[DESIGN]`

- manifest의 요청 순서대로, 요청마다 응답 행 순서 × (`import`, `export`)로 넣고, 그 뒤에 그 요청의 상태 행(요청 월 순서 × (`import`, `export`))을 넣는다. 수집기의 행 만들기(`store_result`)와 같은 규칙이다.
- 수신 기록이 없는 계획 요청은 그 자리에 `NOT_COLLECTED` 행을 넣는다(자료 계약 §3.4). 비교국 표가 수집 계획 밖 국가를 가리키면 그 국가의 부모 행(HS4 스캔)과 HS10 행(HS6 조회)을 맡았을 요청의 `NOT_COLLECTED` 행을 맨 끝에 국가·코드·구간 순으로 붙인다. 계획 행의 rowid를 밀지 않기 위해서다.
- 근거: v2 수집기 SQLite의 관측 행 rowid가 이 순서와 1~50,132까지 빈틈없이 같다 `[사실: 2026-09-24(목) 읽기 전용 조회]`. 그래서 v2 개발 빌드의 관측 행과 rowid는 수집기 SQLite와 한 칸도 다르지 않고(룰북 예시의 CN·850450·2024년 1월 부모 행은 두 파일 모두 rowid 519), 승격은 상태 칸만 바꾸므로 최종 빌드도 rowid가 같다 `[사실: 2026-09-24(목) v2 개발 빌드 대조]`.

③ **빌드 입력과 표 형식** `[DESIGN]`

- 입력은 raw·manifest·비교국 표·승격 규칙에 더해 수집기 SQLite(`snapshot.sqlite`)를 읽기 전용(`mode=ro`)으로 읽는다. 수신 기록의 시각·HTTP 상태·시도 수와 스냅샷 메타(`source_kind`, `last_collect_at`, `importer` 등)는 raw로 다시 만들 수 없기 때문이다. raw로 다시 셀 수 있는 값(응답 sha256, 행 수, 결과 코드)은 대조하고 다르면 빌드를 멈춘다. raw 결합 해시는 `snapshot_hash.json`의 `method`와 같은 계산으로 구해 그 기록과 대조한다.
- `snapshot_meta` 표: 계약 `snapshot` 객체의 키(`normalized_sha256` 제외)와 `schema_version`을 키마다 한 행, 값은 키 정렬·공백 없는 JSON 글자열로 둔다. `collected_at`은 수집기 메타의 `last_collect_at`, `period`는 manifest의 수집 설정(`config.period`)에서 가져온다. 수집기 `open_snapshot`은 메타의 `period_start`·`period_end`를 설정과 관계없이 `202201`·`202412`로 적기 때문이다 `[사실: src/tradesentry/ingest.py open_snapshot]`. `hs_version`은 관측 행의 값(v2는 `HSK`)이다.
- `peer_group` 표: 비교국 표 CSV의 열은 자료 계약 §2.3.6 필드 17개(`baci_country_code` 포함)와 같아야 한다. `baci_country_code`·`similarity`·`community_id` 칸의 빈 값이나 `null`은 NULL로 읽는다. `similarity`는 원문 표기를 지키려고 TEXT로 두고, DAL이 Decimal로 돌려준다.
- 빌드 기록 JSON 키: `schema_version`, `snapshot_id`, `normalized_sha256`, `raw_sha256`, `policy_version`, `confirmed_no_trade_rule`, `confirmed_no_trade_rows`, `peer_group_files`(파일 이름과 sha256), `row_counts`, `build_file`, `built_at`. 정본 기록은 `installed_from`, `installed_at`을 더한다. 로컬 절대경로는 적지 않는다.
- SQLite는 저널 모드 DELETE(WAL 아님)로 만들고, 쓰기 전에 파일 이름을 `"xb"`로 먼저 잡는다(이미 있으면 실패).

④ **근거 ID rowid 표준형** `[DESIGN, 해석]`

- rowid 조각은 앞자리 0이 없는 10진수 양의 정수(`[1-9][0-9]*`, ASCII 숫자)이고 2^63−1 이하일 때만 행을 찾는다. `013`·`+13`·` 13`처럼 같은 행을 가리키는 두 번째 글자열은 풀림 규칙 4에서 어긋난다.
- 빈 `<snapshot_id>` 조각은 규칙 2, 빈 `<table>` 조각은 규칙 3에서 어긋난다.
- 근거: 자료 계약 §4.4는 rowid를 "10진수 양의 정수"로만 적는다. 한 행을 한 글자열로만 가리켜야 근거 ID 목록의 중복·비교가 흔들리지 않는다. 채점기는 독립 구현이므로 DT8이 같은 해석을 적용해야 한다(DT1 보고로 알린다).

⑤ **정책 파일 형식(단위 K4)** `[DESIGN]`

- 키: `schema_version`(1), `policy_version`, `thresholds`(`{"unit_value": 30, "share": 10}`. `unit_value`는 `r_U`의 %, `share`는 `d_s`의 pp. 비교는 절댓값 이상), `min_amount`(USD), `min_weight`(kg), `tolerance`(`{"amount_usd": 0, "weight_rounding_kg": 0.5}`. 중량 허용오차 = `weight_rounding_kg` × (대조한 하위 행 수 + 1)), `confirmed_no_trade`(null 또는 `{"rule": 규칙 이름}`). 밑줄로 시작하는 최상위 키는 설명용이다. 모르는 키와 float(부동소수)는 거부한다.
- 정책 버전 이름과 파일: `policy_v1` → `configs/policy_v1.json`, `dev-<수>.<수>` → `configs/policy_dev.json`(결정 D2). 파일 안 `policy_version`이 부른 이름과 같아야 한다.
- 승격 규칙 이름은 지금 `ingest_verify_candidates` 하나다. 수집기 `verify`가 `confirmed_no_trade_candidates`로 나열하는 행과 같은 규칙이다: 수입 흐름의 HS6 자릿수 `UNRESOLVED_ZERO` 행 가운데, 같은 상대국·HS6·월의 `OBSERVED` HS6 행이 없고, 같은 상대국·월에 같은 HS4 아래 다른 HS6의 `OBSERVED` 행이 있는 행을 바꾼다. 수출 흐름 행은 바꾸지 않는다. 모르는 규칙 이름은 거부한다. 실제 `policy_v1`의 규칙은 DT4 ② 제안과 사용자 승인으로 정한다(다른 규칙이면 단위 S2에 더한다).
- `configs/policy_dev.json`(`dev-0.1`): 기준값은 `eval/dev/oracle_ABC.json` 최상위 설명 `임계 |r_U|>=30%, |d_s|>=10pp`, 허용오차는 자료 계약 §11.1의 출발값, `min_amount`·`min_weight`·승격 규칙은 null이다. 허용오차를 넣은 것은 지표 단위가 수치를 코드에 박지 않게 하려는 것이며, 값은 계약에 적힌 출발값 그대로다.

⑥ **DAL이 스냅샷을 여는 법** `[DESIGN]`

- `open_snapshot(snapshot_id)`은 정본 `data/snapshots/{snapshot_id}/snapshot_build.sqlite`를 읽기 전용 URI(`mode=ro`)와 `query_only`로 연다. 메타의 `schema_version`이 1이고 `snapshot_id`가 같아야 연다(수집기 `snapshot.sqlite`는 열지 않는다).
- 승인 전 개발 빌드는 호출하는 코드가 `path=`로 준다(예: `outputs/snapshot_build-{시각}/snapshot_build-{시각}.sqlite`). 단위 S3는 같은 파일을 `build_file`로 받는다. 경로는 모델에게서 받지 않는다(자료 계약 §5.1). CLI가 개발 빌드 경로를 받는 수단은 계획 경로·명령 표에 없는 새 이름이 필요해 이 기록에서 정하지 않는다(오케스트레이터 결정 대기, DT1 보고의 제안).

⑦ **국가 코드 대응표 열(단위 G3)** `[DESIGN]`

- `data/reference/country_map.csv`의 열은 `cntyCd`(관세청 2자리), `baci_country_code`, `baci_country_iso3`, `kcs_country_name`, `baci_country_name`, `note`이고, 행은 수집 상대국 16개다. 대만(`TW`)은 BACI 490(iso3 자리 `S19`)이며 `note`에 "BACI 490에는 대만 외 기타 아시아 미상분이 섞일 수 있다"를 적었다. 값은 커밋된 참조 자료(`data/reference/partner_superset_2023.json`, BACI 한국 수입 발췌 CSV, 관세청 조회코드 국가명)에서 가져왔고 시험(`tests/test_country_map.py`)이 대조한다.

## 2회차 보탬(2026-09-25(금), 무역통계·Codex 교차 검토 반영)

⑧ **스냅샷 빌드가 멈추는 경우와 비교국 표 행 규칙** `[DESIGN]`

- `ALL` 중복 행(자료 계약 §2.3.2 행 규칙 6): 같은 (HS10, 월, 흐름)의 `ALL` HS10 월 행이 두 요청에 있고 금액·중량이 다르면 빌드를 멈춘다(조용히 고르지 않는다).
- 비교국 표 행 규칙은 함수 하나(`peer_group_problems`, 단위 S2)로 정하고 단위 S3도 같은 함수로 저장된 행을 본다. 규칙: `entity_type`=`exporter_country`, `entity_namespace`=`KCS_cntyCd`, 대상국은 수집 상대국, 비교국은 두 글자 대문자 국가코드이고 대상국 자신과 `ALL`이 아니다(자료 계약 §2.3.6의 "대상국을 뺀"·"p 제외"), `scope_type`은 소문자 `hs2`·`hs4`·`hs6`이고 `scope_id`는 그 자릿수 숫자이며 수집 HS6 가운데 하나의 앞자리, `peer_rank`는 1 이상 정수이고 묶음마다 1부터 빈틈없이 이어지며 비교국이 겹치지 않는다, `similarity`는 null이나 유한한 수, `community_id`는 null이나 비지 않은 글자, `baci_country_code`는 null이나 숫자 글자, `params_hash`·`input_sha256`은 16진수 소문자 64자, `generated_at`은 KST ISO 8601(`+09:00`, 초 단위), `source_year`는 네 자리 연도, `method`·`grouping_version`·`source_version`은 비지 않은 글자다. MT6의 `g0` 표(320행)가 이 규칙을 통과함을 확인했다 `[사실: 2026-09-25(금) 읽기 전용 확인]`.

⑨ **스냅샷 검증(단위 S3)의 범위** `[DESIGN]`

- `check_raw`는 raw 대조(raw에서 다시 만든 행과 한 칸씩 비교)만 켜고 끈다. raw 없이 볼 수 있는 계약 검사는 늘 돈다: HS 코드는 숫자이고 자릿수는 2·4·6·10, 달은 수집 기간 안(`RAW:` 원문은 `OBSERVED` 총계 행만), 상태와 수신 기록(`OBSERVED`·`UNRESOLVED_ZERO`·`CONFIRMED_NO_TRADE`는 `OK`, `REQUEST_FAILED`는 `FAILED`, `NOT_COLLECTED`는 수신 기록 없음), 행의 상대국·코드·달이 요청 조건 안, raw 위치 칸의 모양(수집기 규칙), `NOT_COLLECTED` 행 집합이 수집 계획과 비교국 표에서 다시 계산한 집합과 같음, `CONFIRMED_NO_TRADE`는 수입·HS6 자릿수 행에만 있고 승격 규칙을 다시 적용한 집합과 같음, 상대국 키마다 HS10 하위 자리(HS6 조회의 HS10 행이나 HS6 자릿수 상태 행), 비교국 표 행 규칙(⑧).
- 관측 행 규칙은 수집 계획을 메타 `collection_plan`에서 수집기 `build_manifest`로 다시 만들어 본다. 그래서 manifest가 `build_manifest(collection_plan)`과 같고 raw 위치 칸이 수집기 규칙(`{request_id}.xml`, `item[n]`)을 따르는 스냅샷을 전제로 한다. 합성 스냅샷(DT3)도 수집기 형식 원천을 만든 뒤 단위 S2로 빌드해야 이 검사를 통과한다.
- 비교국 표 원본 대조: 입력 `peer_group_files`가 있으면 그 파일로, 없으면 빌드 기록의 파일 이름을 `data/reference/`(계획 경로 표의 "그룹핑 결과" 자리)에서 찾아, sha256을 빌드 기록과 대조하고 행을 다시 읽어 저장된 행과 비교한다. 찾지 못하면 건너뛰고 보고에 적는다.

⑩ **도구 봉투와 개발용 정책** `[DESIGN]`

- 도구 봉투 `missingness` 항목의 모양은 도구(M)가 정한다. 다만 항목이 `observation_status`를 가지면 `OBSERVED`가 아닌 관측 상태 코드여야 한다(자료 계약 §5.2).
- `dev-0.1`에는 승격 규칙이 없다. `dev-0.1`로 만든 빌드는 `UNRESOLVED_ZERO`를 그대로 두고, 승격은 사용자가 승인한 `policy_v1`의 규칙으로만 한다. `configs/policy_dev.json` 설명에도 적었다(수치는 그대로라 `policy_version`을 올리지 않는다).

## 검토한 대안

- 행 순서를 관측 기본 키(`request_id`, `month`, `partner_code`, `hs_code`, `flow`) 사전순으로 두는 안: manifest와 무관하게 정해지지만, v2 수집기 SQLite의 rowid와 달라져 이미 문서에 적힌 근거 행 번호(룰북 예시)와 어긋난다. 버렸다.
- 빌드 시각·적용 정책 버전을 `snapshot_meta`에 넣는 안: 같은 입력의 두 빌드가 다른 `normalized_sha256`을 갖게 되고, 계약 `snapshot` 객체에 없는 키를 더하게 된다. 빌드 기록 JSON으로 옮겼다.
- 수신 기록을 raw만으로 다시 만드는 안: 계약 필드 `timestamp`와 기존 열(HTTP 상태, 시도 수, 걸린 시간)을 만들 수 없다. 수집기 SQLite를 읽기 전용으로 읽고 raw로 셀 수 있는 값만 대조하는 쪽을 골랐다.
- 기준값을 `{"metric", "unit", "abs_gte"}` 객체로 두는 안: 단위와 비교 방향을 파일에 드러내지만, 판정 정책(MT1)이 수 하나로 가정하고 먼저 구현했다. 단위는 자료 계약 §11.2가 이미 정하므로 수 하나로 맞췄다.
- rowid 조각을 `int()`로 너그럽게 읽는 안(`013`도 행 13): 같은 행을 가리키는 글자열이 여럿 생긴다. 버렸다.
