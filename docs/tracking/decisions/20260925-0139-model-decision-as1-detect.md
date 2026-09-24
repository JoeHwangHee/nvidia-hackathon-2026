# AS1 첫 PR: `detect` 배선과 조립 점검 결과

조립 작업 AS1(탐지 조립: 지표 단위와 판정 정책 단위를 이어 `tradesentry detect`를 만드는 작업)의 첫 PR에서 정한 배선·어댑터·출력과, 실자료 스냅샷을 이번 PR에서 탐지하지 않기로 한 오케스트레이터 결정, 조립 점검(`docs/plan/UNITS.md` §5) 1·2·5단계 결과를 적는다. 코드와 시험은 같은 PR에 있다.

용어

- 조립체 2: `detect` 한 명령이 도는 단위 묶음. 단위 X1(단가·변화율), X2(점유율·변화), X4(자릿수·반올림), P1(신호 발동), P2(사례 만들기)다(`docs/plan/UNITS.md` §4).
- K3·K4: 자료 접근층(스냅샷을 읽기 전용으로 조회하는 단위, `dal/query.py`)과 정책 수치 읽기 단위(`contract/policy_load.py`).
- 어댑터: K3가 돌려주는 월 값 객체를 지표 단위 X1·X2의 역할별 입력 행(`parent`: 상대국 부모 HS6 행, `world`: 전체국가 `ALL` HS10 행)으로 옮기는 배선 코드.
- 정확값: 표시 자릿수로 반올림하기 전의 값. X1·X2의 `exact_value`가 `fractions.Fraction`(오차 없는 분수)으로 준다.
- 출처 종류(`source_kind`): 스냅샷이 실자료(`real`)인지 합성(`controlled`)인지 적은 스냅샷 메타 값(자료 계약 §2.3.1).
- 분할 기록: 실자료 64개 계열을 `real_dev`(개발용)와 `real_sealed`(봉인용)로 나눈 배정(로드맵 DT4 ①).

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 01:39(기록 시각). 배선과 시험은 같은 날 CLI 첫 PR(#23)을 병합해 받은 뒤(01:31) 만들어 01:38에 커밋했다(`4fe3a35`). ⑤는 작업 지시(오케스트레이터)로 받았다 |
| 제목 | `detect` 배선 순서·어댑터·P1 입력·출력 파일, 실자료 스냅샷 거부(`real_dev` 좁히기는 두 번째 PR), 조립 점검 1·2·5단계 결과와 단위 표 판정 갱신 |
| 결정 | 아래 "결정 내용" ①~⑦ |
| 이유와 근거 | 항목마다 적었다 |
| 검토한 대안 | 아래 "검토한 대안" |
| 결정 주체 | 소유 트랙(M). ⑤는 오케스트레이터(작업 지시) |
| 공용 약속 여부 | 아니다. 계약 필드·상태값·ID 형식·기준값·계획 경로·명령 표를 바꾸지 않는다. 새 CLI 옵션을 두지 않았고 `detect`의 옵션 역할(`args.COMMAND_OPTIONS`)도 그대로다. 출력 파일 이름은 이름·출력 규칙(자료 계약 §10.3 N4·N6)에 단위 P2의 도메인명을 넣은 것이다. 두 번째 PR이 기다리는 분할 기록의 정본 위치는 계획 경로 표(공용 약속) 변경이라 사용자 승인 대상이다(⑤) |
| 영향 | 아래 "영향과 넘길 곳" |
| 관련 PR | AS1 첫 PR(브랜치 `model/AS1-detect`) |

## 결정 내용

① **배선 순서와 종료 코드** — 확정

- 처리 함수 표의 `detect` 항목을 `dispatch._detect`로 잇는다(`src/tradesentry/cli/dispatch.py`, 단위 F2).
- 흐름은 아래 순서다. 뒤 단계가 실패하면 앞 단계에서 확보한 빈 실행 폴더가 남는다(MT5 결정 기록 `20260924-2356-orchestrator-decision-mt5-cli.md` ⑥과 같은 방식).
  1. 실행명 `detect-{시각}` 확보(자료 계약 §10.3 N8)
  2. K4 `load_policy(--policy)`. 실패하면(`PolicyError`) 스냅샷을 열지 않고 1로 끝낸다.
  3. K3 `open_snapshot(--snapshot)`로 정본 빌드(`data/snapshots/{snapshot_id}/snapshot_build.sqlite`)를 읽기 전용으로 연다.
  4. 출처 종류 확인(⑤)
  5. 계열·비교월마다 어댑터(②) → X1·X2 → 정확값으로 P1 입력 행(③)
  6. P1 → P2(출처 종류는 스냅샷 메타에서 읽는다)
  7. 출력(④)
- 종료 코드
  - 0: 성공. 사례가 없어도 0이다.
  - 1: 정책을 읽지 못함, 스냅샷을 열지 못했거나 행 규칙에 맞지 않음(`SnapshotError`), 실자료 스냅샷 거부, 단위의 입력 오류(예상 밖 예외)
  - 4: P2 출력이 `snapshot_id`·`dataset`·`policy_version`·`cases`·`data_quality` 객체가 아님, K3 `world` 값을 풀어 다시 만든 ALL 행이 K3 값과 다름, 지표 출력에 필요한 기호가 하나가 아님. 세 경우 모두 조립 시험이 있다(`test_case_build_output_shape_is_checked`, `test_world_rebuild_mismatch_is_a_wiring_error`, `test_metric_symbol_must_appear_exactly_once`: 종료 코드 4, 빈 실행 폴더. 뒤의 둘은 P1 호출 0도 본다)
- 오류 문장에는 받은 값(스냅샷 ID·정책 이름)과 스냅샷 안의 값을 넣지 않고 예외 이름만 적는다(N13, MT5 결정 ⑧).
- 쓰지 않는 공통 옵션 `--mode`는 요청에 남지만 단위에 넘기지 않는다.
- 이유: MT1 결정 기록 `20260925-0025-model-decision-mt1-policy.md` ⑭의 AS1 항목(출처 종류는 호출자가 아니라 스냅샷 기록에서 읽는다), MT5 결정 ④~⑧(처리 함수 계약·종료 코드·출력 규칙).

② **어댑터(K3 → X1·X2 역할별 입력)** — 확정. DT2 결정 기록 `20260925-0035-data-decision-dt2-metrics.md` ①의 `parent`·`world` 쪽을 이 모양으로 확정한다. `children`(단위 X3 입력)은 AS2가 정한다.

- `parent`(K3 `parent_series`의 월 값 하나)
  - 값이 있는 달(`OBSERVED`): 행 하나. `hs_code`는 그 HS6, 근거 ID는 K3의 부모 행 하나다.
  - 무거래 확정 달(`CONFIRMED_NO_TRADE`): V·Q 칸이 빈 행 하나. 근거 ID는 K3가 준 상태 행 전부이고, 지표 단위가 V·Q를 0으로 본다(자료 계약 §3.4). K3 값이 코드를 주지 않아 `hs_code`는 비운다(지표 단위가 허용한다).
  - 빠진 달(`REQUEST_FAILED`·`NOT_COLLECTED`·`UNRESOLVED_ZERO`): K3 `missingness` 항목마다 상태 행 하나(근거 ID 하나). 항목이 없으면 4다.
- `world`(K3 `world_series`의 월 값 하나)
  - 값이 있는 달: K3가 중복을 빼고(자료 계약 §2.3.2 행 규칙 6) 고른 ALL HS10 행의 근거 ID를 K3 `resolve`로 풀어 HS10 행으로 다시 만든다. 다시 만든 코드 목록과 금액 합이 K3 값(`hs10_codes`, `amount_usd`)과 같아야 한다(다르면 4).
  - 무거래 확정 달과 빠진 달은 `parent`와 같다.
- K3 호출은 계열마다 `parent_series` 한 번, HS6마다 `world_series` 한 번이다. ALL 행은 HS6·달마다 한 번만 다시 만든다.
- 이유: 행 규칙 4·6은 K3가 적용하고 지표 단위는 확인만 한다(DT2 결정 ①). ALL을 K3의 달별 합계 형식 그대로 넘기면 X2의 행 단위 중복 검사(분모 두 배 함정)를 할 수 없다(DT2 "검토한 대안").

③ **P1 입력** — 확정

- 행마다 `hs6`, `partner`, `month`, `baseline_month`, `r_U`, `d_s`를 넘긴다. `r_U`·`d_s`는 X1·X2 `exact_value`의 정확값(Fraction이나 null)이다. metric 객체의 `value`(표시 자릿수로 반올림한 값)는 넘기지 않는다.
- 부모 HS6 행의 금액·중량 `amount_usd`·`net_weight_kg`({`month`, `baseline_month`})는 X1 `r_U` 입력의 `V_0`·`Q_0`·`V_1`·`Q_1`에서 옮긴다. 네 값이 모두 정수일 때만 옮기고, 아니면 `r_U`가 null이라 P1이 읽지 않는다. P1은 정책의 `min_amount`·`min_weight`가 null이 아닐 때 이 값을 쓴다(MT1 결정 ③, 사용자 확인 U2 잠정).
- 이유: DT2 결정 ②·MT1 결정 ②. 표시 값으로 비교하면 경계에서 발동이 뒤집힌다. 정확값 −29.96%는 미발동인데 표시 값 −30.0은 발동이 되고, d_s 9.96pp와 표시 10.0도 같은 관계다. 조립 시험이 두 경우와 정확히 −30%·10pp(발동)를 고정했다.

④ **출력** — 확정

- `outputs/detect-{시각}/policy_case_build-{시각}.json` 한 파일에 P2 출력을 그대로 쓴다: {`snapshot_id`, `dataset`, `policy_version`, `cases`, `data_quality`}. 합성 스냅샷은 `dataset`이 null이다. 파일은 이미 있으면 실패하는 방식으로 쓴다.
- 도메인명은 그 출력을 만든 단위 P2의 `policy_case_build`다(자료 계약 §10.3 N4·N6, 단위 표 §3.4). 실행 이름은 `detect`다(N5). 조립 시험은 파일 이름을 코드 상수가 아니라 글자 `policy_case_build`로 확인한다.
- 표준 출력에는 `outputs`부터의 상대경로 한 줄만 적는다.
- 쓰지 않는 것
  - P1 전체 발동표(`policy_trigger`): 발동하지 않은 계열·월까지 담는다. 스냅샷과 정책으로 다시 계산할 수 있다. 사례 목록과 데이터 품질 목록은 P2 출력에 이미 있다.
  - metric 객체(`metrics_unit_value`·`metrics_share`): 사례를 조사할 때 `run-case`의 도구가 다시 계산한다.
- 이유: 작업 지시("경보·사례 목록, 데이터 품질 목록"), 개발 플랜 §6.2("자료 미달로 탐지할 수 없는 행은 숨기지 않고 데이터 품질 목록에 둔다"). 개발 플랜 §6.4에 따라 경보 = 사례다.

⑤ **실자료 스냅샷은 이번 PR에서 탐지하지 않는다** — 오케스트레이터 결정(작업 지시), 두 번째 PR에서 대체할 잠정 결정

- 출처 종류가 허용 목록(`controlled`)에 없으면 거부한다. 거부는 K3로 값을 읽거나 지표를 계산하기 전이다. 분명한 오류 문장을 내고 1로 끝난다(`dispatch.DETECT_REFUSAL`). 그때까지 읽은 것은 K3 `open_snapshot`이 열면서 읽는 메타·수신 기록의 요청 목록·비교국 ID뿐이고, 관측 행의 값(금액·중량)은 읽지 않는다 `[사실: dal/query.py Snapshot.__init__. 조립 시험의 거부 시험(RealSnapshotRefusalTest)은 비교월 쌍 2개·계열 10개가 있는 14개월(202301~202402) 스냅샷(값은 합성, 출처 종류만 real)을 쓰고, 거부가 없었다면 탐지할 쌍·계열이 있음을 먼저 단언한 뒤, 진짜를 부르는 감시(spy)로 K3 _rows·row·parent_series·parent·world_series·world·children·peers·resolve와 X1·X2·P1·P2의 호출 0을 확인한다. 거부를 지표 계산 뒤로 옮긴 변이에서 이 시험이 실패했다(K3 _rows 12·row 16·parent_series 10·world_series 1·resolve 8, X1·X2 각 20번 호출)]`.
- 이유
  - 개발 실행의 `detect`는 지표 계산(X1·X2)과 신호 발동(P1) 앞에서 `real_dev` 계열로 좁혀야 한다(병렬 개발 규칙 §7.2의 5, MT1 결정 ⑭). P2의 묶음 제한은 마지막 방어선이다.
  - 좁히려면 분할 기록을 읽어야 한다. 그런데 기계가 읽는 분할 기록은 지금 `tests/units/V5/expected.json`이 커밋된 유일한 사본이다. 탐지의 묶음 선택(단위 P2)이나 DT7이 다른 위치를 쓰려면 그 작업에서 계획 경로 표 절차로 정한다 `[사실: DT4 결정 기록 20260924-2340-dt4-real-split-and-sample-seed.md "영향" 행]`.
  - 계획 경로 표는 공용 약속이다. 그래서 정본 위치가 사용자 승인을 받기 전에는 실자료 탐지를 잇지 않는다. 바뀔 약속을 미리 가정한 코드는 병합하지 않는다(병렬 개발 규칙 §4.3).
- 두 번째 PR이 할 일
  - 승인된 정본 위치의 분할 기록(DT4 ① 출력 키 `snapshot_id`·`seed`·`ratio`·`method`·`real_dev`·`real_sealed`)을 P2의 `series_assignment`([{`hs6`, `partner`, `dataset`}])로 바꾼다.
  - 지표·P1 앞에서 `real_dev` 계열만 남기고(`dispatch.detect_series`를 좁힌다), P2에 `dataset`=`real_dev`를 넘긴다.
  - 새 CLI 옵션은 두지 않는다. `detect` CLI 경로의 묶음은 `real_dev`로 고정한다(MT1 결정 ⑭).
- 이 PR의 시험은 실자료 스냅샷 v1·v2로 `detect`를 돌리지 않았다. 거부 시험은 합성 본 스냅샷 `as1_detect_fixture`를 출처 종류 `real`로 빌드한 것을 쓴다. 값은 합성이지만 메타가 `real`이다. 처음 판(단위 S2 시험 도우미의 2개월 원천)은 비교월 쌍이 없어 거부 순서와 관계없이 호출이 0이었다(평가 방법론 검토 1회차 지적). 그래서 자료를 바꿨다.

⑥ **계열과 비교월** — 확정

- 계열은 스냅샷 메타 수집 설정의 HS6 × 상대국이다. 비교국 표가 가리키는 계획 밖 국가(K3 `scope()["other_partners"]`)는 대상이 아니다. 경보 대상은 수집 상대국이다(개발 플랜 §6.4). 조립 시험 `test_out_of_plan_peer_is_not_a_detection_series`가 이를 고정한다. 합성 비교국 표가 CN의 비교국으로 계획 밖 국가 GB를 가리키는 작은 스냅샷에서 `other_partners`가 [GB]이고, P1 입력 행과 출력에는 CN만 있다.
- 비교월 t는 기준월 t−12(전년 같은 달, 자료 계약 §11.4)도 스냅샷 기간 안인 달만 쓴다. v2(202201~202412)라면 202301~202412의 24개월이다 `[추론: 기간 계산]`.

⑦ **시험 자료** — 확정

- 합성 스냅샷을 만들어 쓴다. 도우미는 `tests/units/F2/detect_fixture.py`다. 수집기 코드로 수집기 형식 원천을 만들고, 단위 S2로 빌드한 뒤 정본 자리에 둔다. 출처 종류는 `controlled`다. 다만 거부 시험은 본 스냅샷을 `real`로 빌드한다(⑤). 값은 모두 합성이다.
- 본 스냅샷 `as1_detect_fixture`의 계열
  - oracle A·B·C(`eval/dev/oracle_ABC.json`)의 부모 값을 가진 CN·JP·DE
  - 경계 계열: VN(r_U −29.96%), US(r_U −30%), PH(d_s 9.96pp), TW(d_s 10pp)
  - 자료 문제 계열: FR(2024 구간 HS4 스캔 실패), FI(무거래 확정 승격 달의 점유율 0%), SE(기준월 중량 0)
- ALL 분모는 품목별 API의 두 요청(HS4·HS6)이 같은 HS10 행을 담는다(중복 제거 대상). 중복을 빼지 않으면 TW·FI의 점유율 발동이 뒤집힌다.
- 작은 스냅샷 `as1_detect_world_gap`은 2024 구간의 ALL 분모 요청 두 개가 실패하는 경우다.
- 작은 스냅샷 `as1_detect_other_partner`는 합성 비교국 표(계약 §2.3.6 필드 17개)가 계획 밖 국가 GB를 가리키는 경우다(⑥).
- 단위 S2 시험 도우미(`tests/units/S2/fixture_snapshot.py`, D 소유)는 고치지 않고 가져다 쓴다(XML 응답·raw 해시 도우미).

## 조립 점검 결과(조립체 2, `docs/plan/UNITS.md` §5의 1·2·5단계)

AS1은 합치거나 버린 단위가 없다. 동결 경로(판정 정책 P1·P2) 단위의 코드는 고치지 않았다. 3·4·6단계의 확정은 조립 점검 작업 AS4가 한다. 아래 "AS4에 넘기는 관찰"은 그 입력이다.

| 단계 | 결과 | 명령과 종료 코드 |
|---|---|---|
| 1. 정적 import 그래프 | `cli.dispatch` → `cli.args`, `contract.policy_load`, `contract.types`, `dal.query`, `metrics.unit_value`, `metrics.share`, `policy.trigger`, `policy.case_build`(+ 기존 `snapshot.build`·`snapshot.verify`). `metrics.unit_value` → `metrics.rounding`, `metrics.share` → `metrics.rounding`·`metrics.unit_value`, `policy.trigger` → `policy.required_evidence`, `policy.case_build` → `policy.required_evidence`·`policy.trigger`, `dal.query` → `contract.evidence_id`·`contract.types`, `contract.policy_load` → `contract.types`. 모두 각 단위 머리 주석의 허용 import 안이다(F2는 contract·dal·metrics·policy 허용). 순환 없음, CLI 닫힘은 단위 E2에 닿지 않음 `[사실: 경계 시험 도우미(tests/test_boundaries.py의 repo_modules·import_targets)로 커밋 4fe3a35에서 뽑은 그래프]` | `env -u NVIDIA_API_KEY -u DATA_GO_KR_SERVICE_KEY -u TRADESENTRY_SEALED_DIR uv run --locked python -m unittest discover -s tests -p "test_boundaries.py"` → 0(Ran 33) |
| 2. 실행 커버리지 | `detect` 한 번(합성 본 스냅샷, `dev-0.1`)에 불린 횟수: K4 `load_policy` 1, K3 `open_snapshot` 1·`parent_series` 10·`world_series` 1·`resolve` 8, X1 `run` 20·`exact_value` 20, X2 `run` 20·`exact_value` 20, X4 `metric` 200(X1이 3개, X2가 7개씩), P1 `run` 1, P2 `run` 1. 조립체 2의 다섯 단위가 모두 불린다. K3 `children`·`peers`와 X3은 `detect`가 부르지 않는다(조립체 3의 몫) | `tests/units/F2/test_detect_command.py`의 `test_assembly_units_are_called`(아래 단위 시험 명령에 든다) → 0 |
| 5. 동작 불변 | 합치거나 버린 것이 없어 단위 X1·X2·X4·P1·P2의 입출력은 그대로다. 조립 시험(`detect` 하나를 처음부터 끝까지 돌려 기대 출력과 비교)이 통과한다. 출력 파일의 도메인명은 단위 표의 `policy_case_build`와 같다(N4) | 단위별 `env -u … uv run --locked python -m unittest discover -s tests/units/<ID> -t tests`: F1 0(29), F2 0(49), K3 0(12), K4 0(8), X1 0(17), X2 0(14), X4 0(20), P1 0(21), P2 0(10), 모두 skipped 0. 전체 `env -u … uv run --locked python -m unittest discover -s tests -v` → 0(Ran 627, skipped 31). 수정 2회차(`origin/main` cf9d607 병합, 시험 보강) 뒤 F2 0(52, skipped 0), 전체 0(Ran 741, skipped 24) |

**AS4에 넘기는 관찰**(3·4단계의 입력, 판정은 AS4)

- P2 "합침 후보(→ P1)"
  - 합침 기준 세 가지 가운데 "같은 명령 묶음 안에서만 불림"(`detect`)과 "소비자 하나"(단위 F2의 `detect`. 단위 V6 봉인 표본도 `detect` 명령으로 부른다)는 채운다.
  - "같은 입력"은 채우지 못한다. P2 입력은 P1 출력에 스냅샷 출처 종류와 두 번째 PR의 묶음·계열 배정이 더해진 것이다.
  - 봉인 묶음 제한의 마지막 방어선이라는 책임도 따로 있다.
  - AS1은 유지를 권고한다. 동결 경로라 확정은 AS4에서만 한다(§5 4단계).
- 새 합칠 후보: 어댑터(K3 월 값 → X1·X2 역할별 입력)가 지금은 단위 F2 안에만 있다. 사례 조사 도구(MT2의 단위 I2~I4)가 같은 변환을 따로 만들면, 같은 입력·같은 규칙이 두 곳에 생긴다. AS2·AS4가 한 곳으로 모을지 본다. 단위를 새로 두거나 옮기면 단위 표 변경(사용자 승인)이다.
- 계약 상수: 이 배선은 관측 상태·흐름 상수를 커널 K1(`contract.types`)에서 가져온다. 새 사본을 만들지 않았다.
- MT5 결정 기록이 적은 실행명 확보 중복(공통 실행기·CLI·단위 L2)은 이 PR에서 바꾸지 않았다.

## 단위 표 판정 갱신(`docs/plan/UNITS.md` §3, 조립체 2의 다섯 행)

- X1·X2·P1: "유지"에 AS1 점검 결과(`detect`에서 불림)를 덧붙였다.
- X4: "유지"에 "X1·X2를 거쳐 불림"을 덧붙였다.
- P2: "합침 후보(→ P1)"를 그대로 두고, AS1 점검 결과(불림, 입력이 달라 합침 기준 미충족, 유지 권고, 확정은 AS4)를 덧붙였다.
- 판정 집계(유지 45, 합침 후보 10, 버림 후보 1, 런타임 밖 9)는 바뀌지 않는다.

## 검토한 대안

- 실자료도 이 PR에서 `real_dev`로 좁혀 잇는 안. 분할 기록을 지금 유일한 사본(`tests/units/V5/expected.json`)에서 읽게 된다. 시험 골든 파일을 런타임 입력으로 쓰는 일이고, 계획 경로 표에 없는 위치를 정하는 일이라(공용 약속) 버렸다(⑤).
- 실자료를 막지 않고 P2의 묶음 제한에만 맡기는 안. `real_sealed` 계열로 지표와 신호 발동을 계산하게 된다(병렬 개발 규칙 §7.2의 5 위반). 버렸다.
- 출처 종류를 금지 목록(`real`만 거부)으로 보는 안. 모르는 값이 들어오면 탐지로 넘어간다. 허용 목록(`controlled`만 통과)을 골랐다.
- ALL을 K3의 달별 합계로 넘기는 안. X2가 행 단위 중복 검사를 할 수 없다(DT2 결정 ①의 대안과 같은 이유). 버렸다.
- P1 전체 발동표와 metric 객체도 출력하는 안. 작업 지시 범위 밖이고, 실자료 두 번째 PR에서 좁히기 전 계열이 파일에 남을 수 있는 출력을 늘린다. 버렸다(④).
- 데이터 품질 목록에 지표 null의 사유(`comparability_flags`)를 덧붙이는 안. P1 출력 모양(동결 경로)을 바꾸거나 새 출력 키를 더해야 한다. 이 PR에서는 하지 않았다("영향과 넘길 곳").
- 조립 시험을 `controlled_fixture_v0`(DT3)로 하는 안. DT3가 아직 `main`에 없다. 수집기 형식 원천을 시험 안에서 만드는 쪽을 골랐다. DT3 병합 뒤 같은 명령을 그 스냅샷으로 돌려 볼 수 있다.

## 영향과 넘길 곳

- 바꾼 파일
  - `src/tradesentry/cli/dispatch.py`: `detect` 배선, 머리 설명의 "탐지 명령 detect" 절
  - `tests/units/F2/test_detect_command.py`: 조립 시험(수정 2회차에 거부 시험 자료 교체, 종료 코드 4 두 경로·계획 밖 비교국 시험 추가)
  - `tests/units/F2/detect_fixture.py`: 합성 스냅샷(수정 2회차에 합성 비교국 표를 넣는 인자 추가)
  - `tests/units/F2/test_dispatch.py`: ASCII 흐름 시험. `detect`가 이어졌으므로 종료 코드 3은 하위 프로세스 안에서 자리표시를 넣어 본다. 없는 스냅샷의 1을 더했고, 하위 프로세스 현재 폴더는 임시 폴더다.
  - `docs/plan/UNITS.md` 판정 칸 다섯 개
- AS1 두 번째 PR: ⑤. 분할 기록 정본 위치의 사용자 승인을 기다린다.
- DT7 ①(`real_dev` 경보·사례 목록)과 V1(채점 요약의 `real_dev` 경보 목록)은 두 번째 PR과 실자료 정본 빌드 설치(DT7 ②)를 기다린다.
- AS2
  - `children` 어댑터는 AS2가 정한다(DT2 결정 ①).
  - 이 PR의 `parent`·`world` 어댑터(`dispatch.parent_rows`·`world_rows`)를 다시 쓸지, 도구 쪽 변환과 한 곳으로 모을지 정한다.
- AS4
  - P2 판정 확정
  - 어댑터 합칠 후보
- `policy_v1` 승인 요청(U2)
  - 최소 기준을 단가 신호에만 거는 지금 해석(MT1 결정 ③)을 조립 시험이 고정했다.
  - 점유율에도 걸기로 바뀌면 P1과 이 시험을 함께 고친다.
  - 그때 무거래 확정 달을 최소 기준에서 뺄지도 함께 정한다. 어댑터는 무거래 확정 달의 부모 금액·중량을 0으로 옮기므로(③), 최소 기준을 점유율에도 걸면 점유율이 0으로 떨어진 사례(합성 FI처럼 d_s −12pp 발동)가 금액 0 < `min_amount`로 조용히 걸러질 수 있다(무역통계 검토 1회차 권고). 2026-09-25(금) 09:00 사용자 확인 항목과 함께 올린다.
- 데이터 품질 목록의 사유 부족: `metric_null` 행은 null이 된 사유(예: `REQUEST_FAILED`, `zero_weight`)를 담지 않는다. 담으려면 P1 출력 모양(동결 경로)을 바꾸거나 `detect` 출력에 새 키를 더해야 한다. 오케스트레이터 판단 후보다(AS4 또는 `RB-1` 전).
- `detect` 출력의 코드 버전: 출력 파일에는 `snapshot_id`·`policy_version`만 있고 탐지 코드의 커밋(`code_version`)이 없다. DT7 ③은 커밋된 탐지 명령과 그 `code_version`을 입력으로 요구하므로, 실행 폴더에 커밋 해시를 남길지 DT7·두 번째 PR에서 정한다(평가 방법론 검토 1회차 권고).
