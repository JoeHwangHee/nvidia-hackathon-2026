# 자료 계약 버전 2 반영: 코드 상수·정책 파일·합성 시험자료·dev20 재생성

사용자 결정(2026-09-25(금) 09:36, "v2로 올림". 원문 기록 `20260925-0936-user-decision-schema-v2.md`)을 코드와 자료에 옮긴 실행 기록이다. 결정의 까닭(사용자 결정 5·7을 자료 계약 §13.2의 "값 집합 변경"으로 봄)과 질문·선택지 원문은 그 기록에 있고 여기서 다시 쓰지 않는다.

용어

- 계약 버전(`schema_version`): 자료 계약의 버전 번호. 인수물(트랙 사이에 넘기는 자료·코드 묶음)마다 적는다(자료 계약 §1.2).
- `normalized_sha256`: 빌드 SQLite(파일 하나로 된 데이터베이스)의 행을 rowid(행 번호)까지 넣어 정해진 방식으로 직렬화해 구한 sha256(내용 지문). 빌드의 `snapshot_meta` 표에 `schema_version` 행이 있어서 버전을 올리면 이 값이 바뀐다.
- 재생성: 커밋한 생성 규칙에서 자료를 결정적으로(같은 입력이면 늘 같은 결과로) 다시 만드는 일.
- 골든 쌍: 단위마다 둔 입력(`input.json`)과 기대 출력(`expected.json`)의 짝.

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 12:15(기록 시각, KST) |
| 제목 | 계약 버전을 코드·정책 파일·시험에서 2로 올리고, `controlled_fixture_v0`와 dev20을 새 계약으로 다시 만든다. 실자료 정본 빌드와 봉인 holdout40의 재생성은 이 PR 밖에 남긴다 |
| 결정 | 아래 "결정 내용" ①~⑤ |
| 결정 주체 | 버전 올림은 사용자(`20260925-0936-user-decision-schema-v2.md`). 반영 방법은 소유 트랙(D) |
| 공용 약속 여부 | 그렇다(자료 형식의 버전 표시). 사용자 승인은 위 기록이다. 버전 표시 말고는 값·키·규칙을 바꾸지 않았다 |
| 영향 | 계약 버전을 대조하는 모든 읽기: 자료 접근층(`dal/`)의 스냅샷 열기, 단위 S3 `snapshot-verify`, 정책 읽기(단위 K4), dev20 생성기·목록 검사(단위 V2·V4), 독립 채점기의 스냅샷 메타 대조. 버전 1로 만든 자료는 이 PR 병합 뒤 모두 거부된다 |
| 관련 PR | 이 PR(브랜치 `data/schema-v2`), 문서 PR(DOCS2, PR #43: 자료 계약 §1.2·§13.2 본문과 시나리오 명세 `eval/scenarios/SCENARIO_SPEC.md` 7.2절 예시) |

## 결정 내용

① **버전을 올린 곳** `[사실: git grep -n "schema_version", git grep -n "SCHEMA_VERSION"]`

- 계약 커널 `src/tradesentry/contract/types.py` `SCHEMA_VERSION` = 2. 이 상수를 쓰는 곳(정책 읽기, 스냅샷 빌드·검증, 자료 접근층, 합성 시험자료, dev20 생성기, holdout40 목록 검사)은 따라 바뀐다. 오류 문장에 적혀 있던 글자 "1"은 상수를 쓰게 고쳤다.
- 따로 둔 상수: 지표 `src/tradesentry/metrics/rounding.py` `SCHEMA_VERSION` = 2(단위 X1~X4가 이 값을 쓴다). 독립 채점기는 `tradesentry`를 import하지 않으므로 `eval/scorer/summary.py`에 `SCHEMA_VERSION = 2`를 새로 두고, 스냅샷 메타 대조(`__main__.py`, 메타 값은 JSON 글자라 `"2"`와 비교), 요약 입력 `meta`, 요약 문장 기본값이 이 상수를 쓴다.
- 정책 파일 `configs/policy_dev.json`·`configs/policy_v1.json`의 `schema_version` = 2. 다른 키·값은 그대로다. 그래서 `configs/policy_v1.json`의 sha256이 `0aacda87…`에서 `0804508a18ca8c848b41f3a90b8cc6f362e986becd76b607380f4786ee73a981`로 바뀐다(DT7 기록 ①이 적은 입력 해시는 그때의 값이다).
- 시험 고정 자료와 골든의 버전 표시를 2로 고쳤다. 해시가 든 골든(K3·S2·S3·S4·V2)은 단위를 다시 돌린 출력과 대조해 64자리 해시만 바뀐 것을 확인하고 해시를 바꿨다.
- 버전 1 거부 시험: 정책 읽기(`tests/units/K4/test_policy_load.py`의 거부 목록에 버전 1과 3), 채점기 스냅샷 메타 대조(`tests/test_scorer_main.py` `test_snapshot_meta_of_previous_contract_version_is_refused`, 종료 코드 1). 원래 거부 목록의 "버전 2" 항목은 이제 올바른 값이라 버전 1로 바꿨다.

② **합성 시험자료 `controlled_fixture_v0` 재생성**(자료 계약 §13.1의 2) `[사실]`

- 생성 규칙 `fixture_spec.json`의 `schema_version`만 2로 고치고 `fixture.materialize()`를 불렀다. 첫 호출은 빌드 SQLite와 빌드 기록(`schema_version`, `normalized_sha256`)만 다르다며 멈췄다. manifest(수집 요청 목록), `snapshot_hash.json`, raw 응답 130개, 수집기 SQLite, 합성 비교국 표는 다시 만든 것과 같았다. 그 두 파일을 지우고 다시 불러 종료 코드 0.
- 새 `normalized_sha256` `eeb8af139a9cced7ddcb06ec8aeb53d412802dbdc77b2ae31a6e68f10e5571e9`(이전 `7453bf78…1cae`). `raw_sha256` `2f8b7f89…501a`는 그대로다.
- oracle A/B/C 재현은 그대로다(`tests/units/S4/`와 `tests/test_metrics_oracle.py` 통과).

③ **dev20 재생성** `[사실]`

- 생성 규칙 `eval/dev/dev20/answers/generation_rules.json`의 `schema_version`만 2로 고치고 `generate`(저장소에 옮기지 않음)로 110개 파일을 만들어 저장소 파일과 바이트로 대조했다. 다른 파일은 네 개였고 차이는 모두 버전 표시와 그에 딸린 해시다: `data/snapshots/dev20/collection_log.json`·`answers/answers.json`·`answers/parent_series_ids.json`은 `schema_version` 한 줄, `input/cases.json`은 `schema_version`과 `snapshot_normalized_sha256` 두 줄. 정답표의 기대 판정·필수 근거·사례, 부모 원본 계열 ID, 응답 XML, manifest, 비교국 표는 바이트까지 같다.
- 네 파일을 옮기고 빌드 두 파일(`snapshot_build.sqlite`·`snapshot_build.json`)을 지운 뒤 `install` 종료 코드 0. 수집기 SQLite와 raw는 그대로 두어도 대조를 통과했다.
- 새 `normalized_sha256` `fb802b8ffc562551583e5cfc4f5adaed70eefb84b8623c31224e43f8537e8b9d`(이전 `e10b41a9…7c16`). `raw_sha256` `297218ff…f25c`는 그대로다.

④ **이 PR에서 다시 만들지 않는 것**

- 실자료 정본 빌드 `data/snapshots/kcs_202201_202412_v2/snapshot_build.json`(커밋된 기록, 버전 1, `normalized_sha256` `b439909a…4639`). 동결 스냅샷 폴더에 닿는 일이라 병합 뒤 오케스트레이터가 main 폴더에서 DT7 기록 `20260925-0920-data-decision-dt7-final-build.md` ①~③의 절차로 다시 빌드·설치하고 기록을 따로 커밋한다. `install_build`는 덮어쓰지 않으므로 설치 전에 정본 자리의 파생 파일 두 개(`snapshot_build.sqlite`·`snapshot_build.json`)만 지운다. raw·manifest·수집기 SQLite·`snapshot_hash.json`·`data-readiness.json`·`collection_http_attempts.jsonl`은 건드리지 않고 전후 sha256을 대조한다.
- 병합부터 재설치까지는 자료 접근층이 실자료 스냅샷 열기를 거부하고(`schema_version`이 2가 아님) `snapshot-verify --snapshot kcs_202201_202412_v2`가 실패한다. 이 사이에는 실자료 `detect`·`run-case`·`evaluate`를 돌릴 수 없다. 재설치는 병합 바로 뒤, MVP 시험 전에 한다.
- 봉인 holdout40: 격리 생성 에이전트가 병합 뒤 처음 정한 seed로 다시 만들고, 봉인 해시 등록은 재생성본으로 한다(원문 기록의 영향 ⑥). 그 전까지 버전 1인 holdout40 묶음은 목록 검사(단위 V4)를 통과하지 않는다.

⑤ **문서와의 순서**

- 자료 계약 본문(§1.2·§13.2)과 시나리오 명세 `eval/scenarios/SCENARIO_SPEC.md` 7.2절의 버전 예시는 문서 PR(DOCS2)이 고친다. 이 PR은 계약 본문을 고치지 않는다.
- `tests/units/K1/test_types.py`: 이 PR은 코드 상수 단언만 2로 바꾸고, 계약 본문 글자 단언(`schema_version=…`)은 DOCS2가 2로 바꾼다. 나중에 병합되는 쪽이 main을 따라가며 두 단언이 모두 2인지 확인한다.

## 검토한 대안

- 계약 버전 상수를 채점기가 `tradesentry`에서 읽기: 채점기 독립성 규칙(`tradesentry`를 import하지 않음)에 어긋나 버렸다. 채점기에 자기 상수를 둔다.
- 버전 1 자료도 읽게 하는 호환 모드: 섞인 자료로 평가 숫자를 만들 위험이 있고, 계약 §13.1은 새 계약으로 다시 만들라고 정한다. 버렸다.

## 남은 일

- 실자료 정본 빌드 재설치와 기록 커밋(오케스트레이터, 병합 바로 뒤).
- 봉인 holdout40 재생성과 봉인 해시 등록(격리 생성 에이전트).
- 병합 뒤 새 작업 폴더는 `fixture.materialize()`와 `python -m eval.datagen.dev20 install`을 다시 부른다. 이전 버전으로 만든 파생 파일이 남은 폴더에서는 두 명령이 "덮지 않고 멈춘다"로 끝나므로, 그 폴더의 `snapshot_build.sqlite`(무시 대상)를 지우고 다시 부른다.
