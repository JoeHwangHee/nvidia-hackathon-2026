# DT5 시나리오 명세·dev20·holdout40 결정적 검사의 세부 결정

DT5(시나리오 명세와 dev20 + 독립 정답표, holdout40용 결정적 검사, 데이터 트랙) 구현에서 자료 계약과 계획 문서가 데이터 트랙(D)에게 맡겼거나 정하지 않은 세부를 적는다. 코드·자료·시험은 DT5 PR에 있다. 항목마다 **확정** 또는 **잠정**을 붙였다. 잠정 항목은 사용자·오케스트레이터(작업을 나누고 병합하는 주관 에이전트) 확인이나 다른 작업의 결정(아래 D17·U1·U2·U4)을 기다린다.

용어

- dev20 / holdout40: 모든 에이전트가 쓰는 공개 합성 개발 자료 20건 / 저장소 밖 봉인 폴더에 두고 한 번만 채점하는 합성 평가 자료 40건.
- 단위 V1·V2·V4: 시나리오 명세 `eval/scenarios/SCENARIO_SPEC.md`(구성 단위), dev20 생성 `eval/datagen/dev20.py`, holdout40 결정적 검사 `eval/datagen/holdout40_check.py`.
- 판정 근거 규칙: 신호(단가 `unit_value`, 점유율 `share`)마다 어느 판정 근거로 상태를 내는지 정한 키. 신호별 상태와 필수 근거(보고서가 그 상태를 내려면 남겨야 하는 근거 이름)를 함께 정한다(시나리오 명세의 §5).
- 부모 원본 계열 ID: 사례의 대상 계열을 사건을 얹기 전의 기본 계열 값으로 만든 지문. dev20과 holdout40이 같은 기본 계열을 쓰지 않았는지 대조한다(시나리오 명세의 §6).
- 수집기 형식 원천: 실자료 수집기(`src/tradesentry/ingest.py`)가 남기는 파일 모양(수집 계획 manifest, 응답 XML, 수신 기록)으로 만든 합성 자료 원본.
- D17·U1·U2·U4: 판정 정책 결정 기록 `20260925-0025-model-decision-mt1-policy.md`가 넘긴 항목(필수 근거 판정 조건표와 보류의 사유별 근거 / "개별 하위변동·잔차가 기준 안"의 기준 / `min_amount`·`min_weight` 적용 / 반올림 불안정 규칙).

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 01:53(기록 시각). 결정은 2026-09-25(금) 01:05~01:50 DT5 구현 중에 했다 |
| 제목 | dev20 입력·정답 하위 경로 배치, 스냅샷 `dev20`과 설치 방식, 사례 식별자, 합성 비교국 표, 판정 근거 규칙과 필수 근거(잠정 포함), 분류 4~7·9의 해석, 부모 원본 계열 ID, 자체 검산, V4 보고 형식, 채점기 대응 |
| 결정 | 아래 "결정 내용" ①~⑭ |
| 이유와 근거 | 항목마다 적었다 |
| 검토한 대안 | 아래 "검토한 대안" |
| 결정 주체 | 소유 트랙(D). ⑤·⑥·⑦·⑧의 잠정 부분은 D17·U1·U2·U4 결정과 오케스트레이터 확인으로 확정한다 |
| 공용 약속 여부 | 아니다. 계약 필드·상태값·ID 형식·기준값·평가 구성(분류와 배분)의 값을 바꾸지 않았다. 새로 지은 이름(하위 경로 `input/`·`answers/`, 파일 `cases.json`·`answers.json`·`parent_series_ids.json`·`generation_rules.json`·`collection_log.json`, 판정 근거 규칙 키, 스냅샷 ID `dev20`)은 계획 경로 표의 `eval/dev/dev20/` 안이나 D 소유 자료의 내부 형식이다. ⑤의 필수 근거 어휘를 정답표·채점기와 맞추는 일을 공용 약속 절차로 올릴지는 판정 정책 결정 기록과 같이 오케스트레이터가 정한다 |
| 영향 | 아래 "영향과 넘길 곳" |
| 관련 PR | DT5 PR(이 기록) |

## 결정 내용

① **입력과 정답표의 하위 경로** — 확정

- 병렬 개발 규칙 §6.5 ①이 D에게 맡긴 배치다. `eval/dev/dev20/input/`(입력)과 `eval/dev/dev20/answers/`(정답)로 나눈다.
  - `input/cases.json`: 사례 목록. 사례마다 `case_id`·`hs6`·`partner`·`month` 넷만 있고, 식별자 순으로 적는다(순서가 분류를 드러내지 않게).
  - `input/source/`: 수집기 형식 원천(`manifest.json`, `raw/<request_id>.xml` 102개, `collection_log.json`, `snapshot_hash.json`, 합성 비교국 표 `peer_group_dev20_g0.csv`).
  - `answers/answers.json`(정답표), `answers/parent_series_ids.json`(부모 원본 계열 ID 목록, holdout40 제외 목록), `answers/generation_rules.json`(생성 규칙: 합성 세계, 사례별 사건과 손으로 정한 기대 판정).
- 샌드박스 허용 목록에는 `eval/dev/dev20/input/`(또는 그 아래 필요한 파일)만 넣고 상위 폴더 `eval/dev/dev20/`와 `answers/`는 넣지 않는다. 허용 목록은 경로 앞부분 일치라서 상위 폴더를 넣으면 정답표를 막을 수 없다 `[사실: 병렬 개발 규칙 §6.5]`. 채점 대상 실행이 쓰는 것은 사례 목록과 설치한 스냅샷(②)뿐이다.
- 생성 코드(`eval/datagen/dev20.py`)에는 사례별 기대 상태를 두지 않는다. 사례별 기대 판정은 정답 하위 경로의 생성 규칙에만 있다(시험이 코드에 사례 식별자가 없는지 본다). `eval/datagen/`도 샌드박스에 넣지 않는다(정답을 담지는 않지만 평가 자료 도구다) `[추론]`.

② **스냅샷 ID `dev20`과 설치 방식** — 확정(설치 자리의 `.gitignore` 보완은 제안)

- 스냅샷 ID는 묶음 이름·폴더 이름과 같은 `dev20`이다. 합성 시험자료가 폴더 이름과 같은 `controlled_fixture_v0`을 쓰는 규칙을 따랐다 `[사실: 자료 계약 §2.3.1 snapshot_id 행]`. 판정 정책 P2의 스냅샷 ID 형식(`^[a-z0-9][a-z0-9_]*$`)에도 맞는다.
- 빌드한 SQLite는 커밋하지 않는다. 텍스트 원천만 커밋하고, 명령 `uv run --locked python -m eval.datagen.dev20 install`이 원천으로 수집기 SQLite를 재현(수집기 `store_result`, 고정 시각 2026-09-25T00:00:00+09:00)하고 단위 S2로 빌드해 `outputs/datagen_dev20-{시각}/`에 둔 뒤, 단위 S3 검증과 `normalized_sha256` 대조를 통과하면 정본 자리 `data/snapshots/dev20/snapshot_build.sqlite`로 옮긴다(단위 S2 `install_build`). 이미 설치돼 있으면 옮기지 않고 해시만 대조한다.
- 기록값: `normalized_sha256` = `3b45fdd26400f86146a1ee764dedcd365d77249120c0aa406c7f4be379bc714f`(정책 `dev-0.1`, 승격 없음, 비교국 표 `peer_group_dev20_g0.csv`). raw 결합 sha256 = `395734be8207152ffc4331ea1918294d7df91099a6c0420a109d5493c9374599`. `input/cases.json`의 `snapshot_normalized_sha256`에도 같은 값이 있다(자료 계약 §4.4 규칙 4의 SQLite 밖 기록) `[사실: 2026-09-25(금) 01:43 설치 실행, 다시 만들어도 같음(시험 test_is_deterministic)]`.
- 설치 뒤 자료 접근층은 `open_snapshot("dev20")`으로 기본 자리에서 연다. 채점기 실행 조건 입력 파일의 `snapshot.file`을 비우면 채점기도 같은 기본 자리를 본다 `[사실: 독립 채점기 PR #30(병합 전, 커밋 1436b9b)의 eval/scorer/__main__.py snapshot.file 기본값]`.
- 설치 자리의 `snapshot_build.json`(빌드 기록)은 `.gitignore`가 빼지 않는다. 파생물이라 커밋하지 않는다. `.gitignore`에 `data/snapshots/dev20/` 한 줄을 더할지는 보안 검토 대상이라 이 PR에서 하지 않고 제안만 한다.

③ **사례 식별자** — 확정

- 판정 정책 P2의 형식 `{hs6}-{partner}-{month}`(판정 정책 결정 기록 ⑩)를 쓴다. 채점기는 실행 기록과 정답표를 `case_id`로 잇고, 런타임이 합성 스냅샷에서 탐지하면 같은 식별자가 나오므로 따로 대응표가 필요 없다. CLI 사례 인자 형식(영문·숫자로 시작하고 끝나며 영문·숫자·밑줄·하이픈, 64자 이하)에도 맞는다. 고유 범위는 (`snapshot_id`, `dataset`)이다.

④ **합성 비교국 표** — 확정(`g1` 대응은 미정)

- 합성 자료의 비교 대상은 자료 안의 합성 `peer_group`이다 `[사실: 자료 계약 §2.3.6]`. 합성 스냅샷 안에서 `g0` 규칙(대상국을 뺀 상대국 가운데 2023년 부모 HS6 수입금액 상위 5개국, 같으면 국가 코드순)으로 골라 `grouping_version`=`g0`, `method`=`import_value_topk`, `source_version`=`dev20`, `input_sha256`=raw 결합 sha256, `params_hash`=후보국·k·방법·기준연도의 sha256으로 적는다. 자료 접근층 `peers()`가 `grouping_version`으로 거르고, 비교 대상은 MVP 시험까지 `g0`이기 때문이다 `[사실: src/tradesentry/dal/query.py peers, 자료 계약 §1.3]`. 상대국이 6개라 비교국은 늘 나머지 5개국이다.
- `g1` 동결 뒤 dev20을 `g1`로 돌리면 비교국 행을 찾지 못해 설명 안 됨(`MAINTAIN`) 사례가 비교 미완료 보류로 바뀐다. 합성 자료의 `g1` 행을 어떻게 둘지는 정하지 않았다 `[미확인]`.

⑤ **판정 근거 규칙과 필수 근거** — `hold_inconsistent`만 잠정(D17), 나머지 확정

- 시나리오 명세의 §5.1의 규칙표를 단위 V4(`RULES`)에 두고, V2는 그 표로 자기 정답표를 검사한다. `composition_explained`·`unexplained`·`hold_missing`·`rounding_unstable`의 상태와 필수 근거(순서 포함)는 단위 P5 규칙표와 같다 `[사실: src/tradesentry/policy/required_evidence.py RULES]`. 두 신호가 모두 발동하면 단가 근거 뒤에 점유율 근거에서 아직 없는 것을 붙인다.
- `hold_inconsistent`(관측은 모두 `OBSERVED`인데 부모·하위 대조, 구성 분해, 전체국가 분모가 성립하지 않는 보류): 단가는 `parent_child_match_V_and_Q`, `comparability_ok`, `no_zero_fill`, 점유율은 `country_and_world_change_shown`, `comparability_ok`, `no_zero_fill`. P5는 이런 보류에도 빠진 관측용 근거(`missingness_listed`, `failure_vs_not_collected_distinguished`)를 요구하는데, 빠진 관측이 없으면 그 근거를 남길 수 없다. 판정 정책 결정 기록 D17의 제안(불일치 보류에는 `parent_child_match_V_and_Q`와 `comparability_ok`)에 `no_zero_fill`을 더했다(계산할 수 없는 값을 수로 채우지 않음: 개발 플랜 §6.1 "정의되지 않은 단위가치를 0으로 채워 분해하지 않는다", 구 개발계획 §8.1 분류 6 "계산 불가와 작은 거래의 구분").
- PR #30 커밋본(1436b9b)의 판정 정의로는 빠진 관측이 없으면 `missingness_listed`·`failure_vs_not_collected_distinguished`를 채울 수 없다. 2026-09-25(금) 02시 무렵 DT8 작업 폴더에는 빠진 관측이 없을 때의 대안 충족 조건과 새 이름의 판정 조건을 더하는 미커밋 변경이 보였다. 그 정의가 들어오면 이 이유가 약해지므로, 불일치 보류의 근거는 D17에서 채점기 정의와 함께 확정한다.
- dev20의 규칙 키 분포(신호 기준): 단가 `unexplained` 6, `composition_explained` 3, `hold_missing` 3, `hold_inconsistent` 3, `rounding_unstable` 1, 점유율 `unexplained` 3, `hold_inconsistent` 2. 사례 상태는 `MAINTAIN` 9, `HOLD` 8, `MONITOR` 3이다(모든 사례를 보류했을 때의 점수는 8/20).
- P5와 다른 필수 근거를 요구하는 사례: `hold_inconsistent` 5건(분류 5 두 건, 분류 6 중량 0 한 건, 분류 7 두 건). 채점기에 판정 조건이 아직 없는 새 이름 5개 가운데 둘을 쓰는 사례: 6건(`country_and_world_change_shown` 5건: 분류 7·8 네 건과 분류 10 한 건, `precision_sensitivity_shown` 1건: 분류 6 반올림 한 건).

⑥ **분류 4의 변형** — 잠정(D17)

- 대상국 HS10 조회(HS6 요청)의 `REQUEST_FAILED`(수신 기록 `FAILED`)나 `NOT_COLLECTED`(수신 기록 없음)만 쓴다. dev20은 비교월 연도 미수집 1건, 기준월 연도 실패 1건이고, 분류 10의 단가 보류도 비교월 연도 실패다. `UNRESOLVED_ZERO`만 있는 변형과 비교국 자료만 빠진 변형은 만들지 않는다. 독립 채점기(PR #30, 병합 전)의 `missingness_listed`는 대상국·`ALL`의 비관측 상태 주장만, `failure_vs_not_collected_distinguished`는 `REQUEST_FAILED`·`NOT_COLLECTED` 주장만 세므로 그 변형은 어느 모드도 필수 근거를 채울 수 없다 `[사실: 독립 채점기 PR #30(병합 전, 커밋 1436b9b)의 eval/scorer/results.py 태그 판정]`.

⑦ **분류 5·6·7의 해석** — 잠정(D17·U4·U2)

- 분류 5: 부모 HS6 금액 ≠ HS10 하위 금액 합(1건), 기준월·비교월 HS10 코드 집합 변경(1건: 코드 신설·소멸로 본 HS 정의 변경). 단위·HS 버전 표기가 다른 변형은 수집기 형식이 스냅샷 전체의 단위와 관측 행 `hs_version`(`HSK`)을 고정해 만들 수 없다 `[사실: src/tradesentry/snapshot/build.py COLLECTOR_HS_VERSION, 수집기 store_result]`.
- 분류 6: 반올림 불안정 1건(기준월 12 USD·1 kg, 비교월 20 USD·1 kg. 중량 ±0.5 kg 범위의 단가 변화율 −44%~+400%가 0과 ±30%를 모두 가로지른다. 판정 정책 결정 기록 ⑤의 제안 규칙을 어느 쪽으로 읽어도 불안정)과 중량 0 하위품목 1건. 반올림 사례는 사례 밖 경보를 피하려고 기준월을 2022년(비교월 2023년)에 두었다. `policy_v1`의 `min_amount`·`min_weight`(U2)가 생기면 이 사례가 경보가 아니게 될 수 있다.
- 분류 7: 전체국가 분모가 대상국 금액보다 작다(점유율 142.9%). 비교월 1건, 기준월 1건. 분모가 없으면 점유율이 계산되지 않아 신호가 발동하지 않으므로, "분모 완전성 부족"을 공식 분모가 전체 국가를 담지 못한 경우로 만들었다 `[추론: 자료 계약 §11.1 분모 규칙, 구 개발계획 §4 4]`. 대상국이 그 HS6의 약 80%를 차지하게 해 다른 나라 점유율 변화를 기준 아래로 두었다.

⑧ **분류 9의 해석** — 잠정(오케스트레이터 확인)

- "복구할 수 있는 잘못된 조회 범위"를, 필수 근거를 모두 얻을 수 있는 완전한 자료에 범위 착오를 부르는 요소를 둔 사례로 만들었다. dev20의 1건은 대상 HS6가 그 나라 HS4(8504) 수입의 약 16%라 HS4 합계로 보면 단가 변화가 약 −6%로 작아 보이지만, 사례 범위(HS6)에서는 하위 단가가 모두 −40%다(`unexplained`, `MAINTAIN`). 기대 상태는 사례 범위의 근거로 정한 상태이고, `resolved_after_correction`에는 대응시키지 않는다(판정 정책 결정 기록 ⑥). `checklist`(모델 없는 고정 체크리스트)는 범위를 틀리지 않으므로 이 사례는 모델 모드의 수정 조회를 보는 자리다.

⑨ **부모 원본 계열 ID** — 확정

- `ps_` + sha256(정규 JSON {"children": {HS10 뒤 4자리: [[금액, 중량] 36개월]}, "parent": [[금액, 중량] 36개월], "period"})의 16진수 소문자 앞 16자(시나리오 명세의 §6). 기본 계열은 사건을 얹기 전의 대상 계열(흔들림 포함)이다. 품목·국가 코드는 넣지 않아 같은 기본 계열을 다른 품목·국가에 옮겨 써도 같은 ID가 나온다. dev20의 20건은 모두 다른 계열이라 ID 20개다(`answers/parent_series_ids.json`).
- 한계: 규모만 바꾸거나 흔들림 seed만 바꾼 변형은 ID가 달라 대조에 걸리지 않는다. 그런 변형을 만들지 않는 것은 생성 규칙이 지키고(시나리오 명세의 §3), ID 대조는 기본 계열을 그대로 가져다 쓴 경우를 잡는다. 이 정의는 로드맵이 V4에 맡긴 "부모 원본 계열 ID 겹침 0"을 계산할 수 있게 하려는 것이다.

⑩ **자체 검산** — 확정

- V2는 생성한 응답 XML을 다시 읽어(생성에 쓴 표를 보지 않고) 자료 계약 §2.3.2·§11.2 규칙으로 모든 계열·달의 단가 변화율과 점유율 변화를 따로 계산한다. 지표 단위(`src/tradesentry/metrics/`)를 열거나 import하지 않았다. 검산 조건: 발동 집합 = 사례 집합(사례 밖 경보 0건), 사례별 발동 여부 = 기대 `signals`, 모든 값이 탐지 기준에서 0.05 이상 거리, 규칙 키별 자료 불변식(시나리오 명세의 §4), 수집기 SQLite 재현·단위 S2 빌드·단위 S3 검증 통과, 단위 V4 형식·분류 규칙 통과. 하나라도 어긋나면 생성이 멈춘다.
- dev20 결과: 발동 20건 = 사례 20건, 사례 밖 경보 0건, 기준에서 가장 가까운 값은 단가 3.68%p(분류 3 비교국의 동반 하락), 점유율 1.72pp `[사실: V2 요약]`.

⑪ **정책 버전과 재검증** — 확정

- dev20의 발동 여부와 기대 상태는 개발용 정책 `dev-0.1`(단가 30%, 점유율 10pp, `min_*` 없음, 승격 없음) 기준이다. `policy_v1`이 승인되면(`min_amount`·`min_weight`, 승격 규칙, U1·U4 확정 포함) dev20을 그 정책으로 다시 검증하고, 달라지면 새 생성 규칙으로 다시 만든다 `[사실: 병렬 개발 규칙 §4.2 3]`.

⑫ **V2 허용 import에 `tradesentry.ingest`를 더함** — 확정(검토 대상)

- 합성 원천을 수집기 형식(요청 ID, `build_manifest`, 응답 파서, `store_result`)으로 만들어야 단위 S2 빌드와 단위 S3 검증이 통과한다(DT1 결정 기록 ⑨). 수집기는 표준 라이브러리만 쓰고 지표·판정 정책에 닿지 않으므로 경계 시험 3(V2가 `metrics`·`policy`에 닿지 않음)은 그대로 통과한다 `[사실: tests/test_boundaries.py 종료 코드 0]`. 수집기의 `open_snapshot`은 스냅샷 폴더 위치가 고정이라 부르지 않고, 같은 표 정의를 V2 안에 적었다.

⑬ **V4 보고와 명령** — 확정

- 보고에는 건수·검사 이름·위반 종류만 적고 사례 식별자·값·경로를 적지 않는다(봉인 묶음을 검사할 때 내용이 드러나지 않게, 자료 계약 §10.3 N10·N13). 봉인 폴더를 기본 입력으로 읽지 않고, 사례 목록·정답표 경로는 부르는 쪽이 명시한다(dev20 목록만 기본 경로가 있다). 명령 `uv run --locked python -m eval.datagen.holdout40_check --cases <사례 목록> --answers <정답표> [--dev20-ids <dev20 목록>]`은 통과 0, 실패 1, 입력 오류 2를 낸다. dev20 묶음도 같은 명령으로 검사된다(겹침 검사는 건너뜀).

⑭ **정답표 형식과 채점기 대응** — 형식 확정, 채점기 수정 필요

- 정답표의 `cases[].expected`는 독립 채점기가 읽는 형식(`eval/dev/oracle_ABC.json` 사례 구조)을 그대로 따르고, 상태는 계약 코드(`MAINTAIN`·`MONITOR`·`HOLD`)로 적는다. 두 신호가 모두 발동한 사례뿐 아니라 모든 사례에 `signal_status`와 `unresolved_evidence`를 적는다. 사례 수준의 `scenario_class`·`parent_series_id`·`rule`·`note`는 검사·검토용이고 채점기는 읽지 않는다 `[사실: 독립 채점기 PR #30(병합 전, 커밋 1436b9b)의 eval/scorer/results.py read_answer_table]`. 채점기를 바꿀 필요는 없다.
- 채점기의 dev20 정답표 경로(`DEV20_ANSWERS`)는 `eval/dev/dev20/answers/answers.json`이다.
- 채점기는 모르는 필수 근거 이름이 하나라도 있으면 정답표 전체를 거부한다. dev20은 새 이름 둘(`country_and_world_change_shown`, `precision_sensitivity_shown`)을 6건에서 쓰므로, 채점기에 두 이름의 판정 조건(D17)을 더하기 전에는 dev20 채점이 멈춘다.

## 검토한 대안

- 빌드한 SQLite를 `eval/dev/dev20/input/`에 커밋하는 안: 채점기·자료 접근층에 경로를 넘기면 설치 없이 쓸 수 있지만, 런타임 CLI에는 개발 빌드 경로를 받는 수단이 아직 없고(DT1 결정 기록 ⑥) 이진 파일은 검토할 수 없다. 텍스트 원천 + 결정적 재빌드 + 기본 자리 설치를 골랐다.
- 수집기 SQLite(`snapshot.sqlite`)를 원천에 커밋하는 안: 단위 S2·S3가 원천 폴더를 바로 읽을 수 있지만 이진 파일이고 SQLite 판에 따라 바이트가 달라진다. 요청 결과 기록(`collection_log.json`)만 커밋하고 설치 때 재현한다.
- 사례마다 스냅샷을 따로 두는 안(20개): 사례끼리 간섭이 없지만 채점기 실행 조건의 스냅샷 파일이 하나이고, 런타임 탐지 식별자와 정답표를 잇기 어렵다. 스냅샷 하나에 20건을 두고 사례마다 다른 달·계열을 써서 간섭을 막았다.
- 사례 식별자를 기대 상태와 무관한 이름(예: `d20-01`)으로 짓는 안: 런타임 탐지 식별자와 이어 주는 대응표가 필요하다. P2 형식을 골랐다.
- 불일치 보류에도 P5 규칙표의 빠진 관측용 근거를 그대로 요구하는 안: 빠진 관측이 없어 어느 모드도 그 근거를 남길 수 없다(채점 불가). ⑤의 잠정 규칙을 골랐다.
- 분류 3의 비교국 변화를 탐지 기준 이상으로 두는 안: 더 뚜렷한 동반 변화지만 비교국마다 사례 밖 경보가 생겨 탐지 결과와 사례 목록이 달라진다. 기준 아래(약 −25%·−20%)로 두었다.
- 비교국 표를 `g0`가 아닌 새 이름(예: 합성 전용 그룹 버전)으로 두는 안: 자료 계약에 없는 이름이고 MVP 런타임이 `g0`로 찾으므로 비교국이 비어 보인다.

## 영향과 넘길 곳

- **DT8(독립 채점기)**: `DEV20_ANSWERS` = `eval/dev/dev20/answers/answers.json`. 새 필수 근거 이름 `country_and_world_change_shown`(5건)·`precision_sensitivity_shown`(1건)의 판정 조건을 더해야 dev20 채점이 된다(MVP 합격 체크리스트 5번 전). `hold_inconsistent` 사례 5건의 근거(⑤)와 `failure_vs_not_collected_distinguished` 정의(⑥)도 D17에서 맞춘다.
- **MT1·MT3·D17**: 필수 근거 판정 조건표와 보류의 사유별 근거. ⑤의 잠정 규칙이 바뀌면 시나리오 명세의 §5와 dev20 정답표를 함께 고친다.
- **런타임 판정 정책(현재 구현으로 기대 상태를 낼 수 없는 사례)**: 분류 6 반올림 1건(단가 `rounding_unstable`을 만드는 쪽이 없다, U4), 분류 7 두 건(분모가 대상국 금액보다 작은 경우를 잡는 규칙이 없다), `hold_inconsistent` 사례의 필수 근거(P5가 빠진 관측용 근거를 요구해 검증기가 막을 수 있다). dev20 점수를 읽을 때 이 목록을 함께 본다.
- **MT5·MT7·AS3(실행·채점 연결)**: 채점 전 `uv run --locked python -m eval.datagen.dev20 install`로 스냅샷을 설치한다(설치 명령이 raw 대조를 켠 단위 S3 검증을 이미 한다). 설치한 정본 파일을 다시 검증할 때는 비교국 표를 명시해 `uv run --locked python -m tradesentry.units S3 --in <입력 JSON>`(입력 `{"snapshot_id": "dev20", "peer_group_files": ["eval/dev/dev20/input/source/peer_group_dev20_g0.csv"], "check_raw": false}`)으로 돌린다 `[사실: 2026-09-25(금) 01:44 설치 뒤 같은 입력으로 단위 S3 실행, ok 참]`. `main`에 병합된 CLI `tradesentry snapshot-verify --snapshot dev20`(MT5 첫 PR, #23)은 단위 S3에 `snapshot_id`만 넘기므로 dev20에서는 실패한다. 비교국 표를 `data/reference/`에서 찾고(`peer_group_sources` 실패), raw 원천을 `data/snapshots/dev20/`에서 찾기 때문이다 `[사실: 같은 날 S3 기본 입력 실행에서 peer_group_sources 실패 확인]` `[추론: raw_rebuild 실패는 S3 코드로 본 것]`. 실행 조건 입력 파일의 `planned_cases`는 `input/cases.json`의 사례 항목 그대로다. 샌드박스 반입은 ①을 따른다.
- **DT3(합성 시험자료, PR #33)과의 차이**(같은 날 따로 정했다. 맞출지는 오케스트레이터가 정한다) `[사실: DT3 결정 기록 20260925-0140 ①·②·⑦·⑧·⑨]`
  - 국가 코드: DT3는 어느 나라에도 배정되지 않은 합성 코드 `XA`~`XJ`를 쓴다(실제 나라에 합성 경보가 붙어 실제 사건처럼 읽히지 않게). dev20은 실제 코드 6개(`CN`, `JP`, `DE`, `VN`, `US`, `MY`)를 쓰고 메타·품목명·`source_kind`로 합성임을 표시한다.
  - 비교국 표 자리: DT3는 `data/reference/peer_group_controlled_fixture_v0.csv`(단위 S3와 CLI `snapshot-verify`의 기본 경로가 찾는 자리), dev20은 `eval/dev/dev20/input/source/peer_group_dev20_g0.csv`(단위 S3에 명시해야 한다).
  - 원천과 재생성: DT3는 생성 규칙·manifest·raw 결합 해시·빌드 기록을 커밋하고 raw XML·수집기 SQLite·빌드를 `fixture.materialize()`로 스냅샷 폴더에 다시 만든다(CLI 검증이 raw 대조까지 통과). dev20은 raw XML과 요청 결과 기록까지 텍스트로 커밋하고, `install`은 빌드만 `data/snapshots/dev20/`에 둔다.
  - 승격: DT3는 관측 상태 5종을 위해 합성 빌드에 승격 규칙을 적용하고 빌드 기록 `policy_version`을 null로 둔다. dev20은 `dev-0.1`로 빌드해 승격하지 않는다(관측 상태는 `OBSERVED`·`REQUEST_FAILED`·`NOT_COLLECTED` 셋).
- **DT6(holdout40)**: 입력은 명세, 생성 규칙(`policy_v1`), 제외 목록 `eval/dev/dev20/answers/parent_series_ids.json`이다. 봉인 직전 `python -m eval.datagen.holdout40_check`와 자체 검산을 돌린다. ⑤의 잠정 규칙이 확정되기 전에 생성하면 동결 뒤 고칠 수 없는 채점 불가 사례가 생길 수 있으므로 D17 결정 뒤에 생성하는 것이 안전하다 `[추론]`.
- **DT4 ②(`policy_v1` 제안)**: 승인되면 dev20을 다시 검증한다(⑪).
- **`.gitignore`**: `data/snapshots/dev20/`(설치 자리, 파생물) 한 줄을 더할지 보안 검토에서 정한다(②).
