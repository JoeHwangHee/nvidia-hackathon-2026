# AS1 두 번째 PR: 실자료 `detect`를 `real_dev` 계열로 좁혀 잇는다

조립 작업 AS1(탐지 조립: 지표 단위와 판정 정책 단위를 이어 `tradesentry detect`를 만드는 작업)의 두 번째 PR에서 정한 것을 적는다. 이 기록은 AS1 첫 기록(`20260925-0139-model-decision-as1-detect.md`)의 ⑤("실자료 스냅샷은 이번 PR에서 탐지하지 않는다", 잠정)를 대체한다. 첫 기록의 ①~④·⑥·⑦은 그대로다. 코드와 시험은 같은 PR에 있다.

용어

- 분할 기록: 실자료 품목×상대국 계열 64개를 `real_dev`(개발용) 21개와 `real_sealed`(봉인용) 43개로 나눈 배정. 단위 V5(실자료 분할, `eval/datagen/split.py`)의 출력이다(DT4 결정 기록 `20260924-2340-dt4-real-split-and-sample-seed.md`).
- 정본 파일: 다른 단위가 이름으로 읽는 고정 위치의 입력 파일(자료 계약 §10.3 N12).
- 좁히기: 관측 값을 읽기 전에 탐지할 계열을 `real_dev` 계열로 줄이는 일.
- 감시(spy): 진짜 함수를 부르면서 호출과 인자만 기록하는 시험 도구.
- 변이 확인: 코드를 일부러 틀리게 바꿔 시험이 그 틀림을 잡는지 보는 일.

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 09:01(기록 시각). 분할 기록 파일은 같은 날 08:56:57 KST에 단위 V5를 다시 돌려 만들었다(실행명 `datagen_split-260925085657`) |
| 제목 | 분할 기록 정본 파일, 실자료 `detect`의 `real_dev` 좁히기 순서·검사·거부, P2 입력, `code_version`을 출력에 넣지 않음 |
| 결정 | 아래 "결정 내용" ①~⑤ |
| 이유와 근거 | 항목마다 적었다 |
| 검토한 대안 | 아래 "검토한 대안" |
| 결정 주체 | 소유 트랙(M). 분할 기록 위치는 사용자(결정 8), 파일을 이 PR에서 만드는 일과 묶음 고정은 오케스트레이터(작업 지시) |
| 공용 약속 여부 | 아니다. 분할 기록 위치는 2026-09-25(금) 사용자 결정 8(`20260925-0847-user-decision-morning-shared-promises.md`)이 이미 승인했다. 이 PR은 그 위치에 파일을 두고 읽기만 한다. 새 CLI 옵션, 새 계약 키, 새 상태값을 만들지 않았다. 계획 경로 표(자료 계약 §10) 반영은 문서 PR(DOCS2)이 한다 |
| 영향 | 아래 "영향과 넘길 곳" |
| 관련 PR | AS1 두 번째 PR(브랜치 `model/AS1-real-dev`) |

## 결정 내용

① **분할 기록 정본 파일** — 확정

- `data/reference/real_split_kcs_202201_202412_v2.json`은 단위 V5를 공통 실행기로 다시 돌린 출력(`env -u NVIDIA_API_KEY -u DATA_GO_KR_SERVICE_KEY -u TRADESENTRY_SEALED_DIR uv run --locked python -m tradesentry.units V5 --in tests/units/V5/input.json`, 종료 코드 0)을 복사한 것이다. 복사 전에 `cmp`로 골든 기대 출력 `tests/units/V5/expected.json`과 바이트가 같음을 확인했고(종료 코드 0), sha256은 DT4 결정 기록의 출력 값 `fe9797d2ef57f97fa2de5be6e8924b6615915d92bab0a20899f5e468407db2d0`과 같다.
- 시험 `tests/units/F2/test_real_split_file.py`가 세 가지를 고정한다.
  - 정본 파일 = 골든 기대 출력 = V5 새 실행을 공통 실행기 형식으로 쓴 바이트
  - sha256
  - 21/43 분할 모양
- 다시 만드는 일은 재분할이 아니라 복사다. 골든 파일을 다시 만드는 일이 재분할이고, 사용자 판단 대상이다(DT4 결정 기록 "영향" 행).
- 이 파일은 공개 자료다. seed·방법·배정 결과가 DT4 결정 기록에 이미 커밋돼 있다.
- `data/`는 D 소유다(병렬 개발 규칙 §1). 이 파일은 오케스트레이터 작업 지시로 M이 만들었으므로 D 검수 대상이다.

② **좁히기 순서** — 확정

- 흐름(단위 F2 `dispatch._detect`)
  1. 실행명 확보
  2. K4 정책 읽기
  3. K3 `open_snapshot`: 메타·수신 기록의 요청 목록·비교국 ID만 읽고 관측 행은 읽지 않는다(첫 기록 ⑤의 근거와 같다)
  4. 출처 종류 확인. 허용 목록은 `controlled`와 `real`이다. 그 밖의 값은 거부(1)하고 분할 기록도 열지 않는다.
  5. `real`이면 분할 기록을 읽고 검사한다(`dispatch.load_real_split`, ③).
  6. `dispatch.detect_series(snap, split)`가 수집 설정의 HS6 × 상대국 가운데 `real_dev` 계열만 남긴다.
  7. 남은 계열로만 K3 `parent_series`·`world_series`(HS6마다 한 번. 전체국가 `ALL` 분모는 두 묶음이 함께 쓴다) → X1·X2 → P1
  8. P2에 `dataset`=`real_dev`와 `series_assignment`를 넘긴다(④).
- 묶음은 `real_dev`로 고정이다(`dispatch.DETECT_DATASET`). 새 CLI 옵션은 두지 않았다(MT1 결정 ⑭, 작업 지시).
- 합성 스냅샷 경로는 그대로다. 분할 기록을 열지 않고, 첫 PR의 조립 시험 기대 출력이 한 글자도 바뀌지 않았다.
- 이유: 병렬 개발 규칙 §7.2의 5(`real_sealed` 계열로 경보를 뽑아 보지 않는다), MT1 결정 ⑭(지표·P1 앞에서 좁히고 P2 제한은 마지막 방어선).

③ **분할 기록 대응과 검사** — 확정

- 대응표 `dispatch.REAL_SPLIT_FILES`는 스냅샷 ID → 정본 파일(저장소 루트 기준 상대경로)이다. 지금은 `kcs_202201_202412_v2` → `data/reference/real_split_kcs_202201_202412_v2.json` 한 항목뿐이다.
  - `real_split_{snapshot_id}.json` 같은 이름 규칙은 만들지 않았다. 승인된 것은 경로 하나이지 규칙이 아니다.
  - 새 실자료 스냅샷이 생기면 대응표 항목과 계획 경로 표를 함께 더한다.
- 아래 경우는 관측 값을 읽기 전에 거부하고 1로 끝난다. 오류 문장은 `dispatch.DETECT_SPLIT_REFUSAL`이고, 받은 값과 로컬 절대경로를 넣지 않는다(자료 계약 §10.3 N13).
  - 대응표에 없는 실자료 스냅샷(v1 포함)
  - 파일 없음, JSON이 아님
  - 키가 V5 출력 키 여섯 개(`snapshot_id`·`seed`·`ratio`·`method`·`real_dev`·`real_sealed`)와 순서까지 같지 않음
  - `snapshot_id`가 그 스냅샷이 아님
  - 항목이 `hs6`·`partner` 객체가 아님(`ALL` 포함)
  - `real_dev`나 `real_sealed`가 비었음
  - 같은 계열이 두 번 나옴(한 묶음 안이든 두 묶음 사이든)
  - 두 묶음의 합이 스냅샷의 계열(K3 메타의 수집 설정 HS6 × 상대국)과 다름
- 이유: 배정에 없는 계열이 있으면 P2가 어차피 오류로 끝난다. 그런데 그 시점은 지표를 계산한 뒤다. 그래서 값을 읽기 전에 막는다.

④ **P2 입력** — 확정

- `series_assignment`는 분할 기록 전체(v2면 64개)를 [{`hs6`, `partner`, `dataset`}]로 바꾼 것이다(계열 순).
- `real_dev` 계열만 넘기지 않고 전체를 넘긴다. 좁히기가 빠졌을 때 P2가 `real_sealed` 계열을 버리는 마지막 방어선이 되려면 배정 전체가 필요하다.
- 변이 확인(아래 증거)에서 좁히기를 끈 판도 출력에는 `real_dev` 사례만 남았다. P2 제한이 동작한 것이다.

⑤ **`code_version`은 `detect` 출력에 넣지 않는다** — 확정(AS1 평가 방법론 검토 1회차 권고, DT7 ③ 입력에 대한 답)

- `detect` 출력은 P2 출력 그대로(`snapshot_id`·`dataset`·`policy_version`·`cases`·`data_quality`)다. 여기에 키를 더하면 DT7·단위 V6이 읽는 파일 모양이 바뀐다.
- 자료 계약 안에서 자리를 찾아봤다.
  - §8의 `code_version`은 사례 실행 결과 기록의 키다. 탐지 출력의 키가 아니다.
  - §1.3은 `code_version`을 버전 축(git 커밋 해시)으로 정할 뿐, `detect` 출력의 위치를 정하지 않는다.
  - §10.3 N6은 도메인명 하나에 파일 하나다. 커밋 해시를 담는 두 번째 파일을 두려면 새 도메인명이 필요하다.
- 그래서 계약 안의 답은 "출력에 넣지 않는다"다. 대신 로드맵 DT7 행이 이미 요구하는 대로, DT7이 결정 기록에 쓴 탐지 명령의 커밋(`git rev-parse HEAD`)을 적는다.
- 출력 파일에 넣어야 한다면 계약에 없는 자리를 만드는 일이라 사용자 승인 대상이다. 이 PR에서는 하지 않았다.

## 증거

- 시험(`tests/units/F2/test_detect_command.py`)
  - 자료: 본 합성 스냅샷(202301~202402의 14개월, 비교월 쌍 2개, 계열 10개. 값은 합성)을 `source_kind` `real`로 빌드한 것과, 임시 파일의 합성 분할 기록이다.
    - `real_dev`: CN·FI·FR·US·VN
    - `real_sealed`: DE·JP·PH·SE·TW. 합성 기대 출력에서 JP·DE·TW는 사례를, SE는 데이터 품질 행을 낸다. 그래서 "접근 0"이 공허하지 않다.
  - `RealDevNarrowingTest.test_real_sealed_rows_are_never_read`
    - K3 `_rows`의 조회 조건과 돌려받은 행, `row`가 돌려준 행 어디에도 `real_sealed` 상대국이 없다.
    - 분할 기록 읽기가 첫 관측 행 읽기보다 앞선다.
    - `parent_series`는 `real_dev` 5개 계열만, X1·X2는 각 10번(계열 5 × 비교월 2), P1 행은 `real_dev`만이다.
    - P2는 `real_dev`와 배정 10개를 받는다.
  - 출력 시험: `dataset`이 `real_dev`이고 사례·데이터 품질 행이 `real_dev` 계열뿐이다(합성 기대 출력에서 `real_dev` 계열 행만 고른 것과 같다).
  - `RealSplitRefusalTest`: 대응표 없음 1, 파일 없음·JSON 오류·목록 3, 모양·계열 불일치 11. 모두 1로 끝나고, K3 값 읽기(9개 메서드)·X1·X2·P1·P2 호출이 0이며, 빈 실행 폴더만 남는다.
  - `UnknownSourceKindRefusalTest`: 허용 목록 밖 출처 종류는 분할 기록도 열지 않고 거부한다.
- 변이 확인(시험 밖 일회 실행, 같은 합성 자료)
  - 정상 판: `real_sealed` 상대국 관측 행 0, `parent_series` 0, X1 0, 사례 3개(CN·FI·US)
  - `detect_series`가 분할 기록을 무시하게 바꾼 변이 판: `real_sealed` 상대국 관측 행 147, `parent_series` 5, X1 10. 사례는 P2 제한으로 여전히 3개(CN·FI·US)였다.
  - 변이 판에서 `test_real_sealed_rows_are_never_read`가 실패했고, 출력 시험은 통과했다. 그러므로 출력만 보는 시험으로는 좁히기 누락을 잡지 못하고, 행 접근 시험이 잡는다.
- 실제 v2 스냅샷으로는 돌리지 않았다. 정본 빌드(`data/snapshots/kcs_202201_202412_v2/snapshot_build.sqlite`)가 아직 설치 전이다(로드맵 DT7 ②).

## 검토한 대안

- 분할 기록을 `tests/units/V5/expected.json`에서 바로 읽는 안: 시험 골든 파일을 런타임 입력으로 쓰게 된다. 사용자 결정 8이 정본 위치를 따로 정했으므로 버렸다.
- 런타임이 `eval.datagen.split`으로 분할을 다시 계산하는 안: 단위 F2의 허용 import 밖이다. 또 기록된 배정이 아니라 계산한 배정을 믿게 된다. 버렸다.
- `real_dev` 계열만 `series_assignment`로 넘기는 안: P2의 마지막 방어선이 "배정에 없는 계열" 오류로만 동작한다. 좁히기가 빠지면 조용히 걸러지지 않고 실행이 실패하는 쪽이다. 전체 배정을 넘겨 P2가 묶음으로 거르게 했다(④).
- 스냅샷 ID 패턴으로 분할 기록 경로를 만드는 안: 승인받지 않은 이름 규칙을 만드는 일이라 버렸다(③).
- `detect` 출력에 `code_version`을 더하는 안: ⑤.

## 영향과 넘길 곳

- 바꾼 파일
  - `src/tradesentry/cli/dispatch.py`: 머리 설명의 "탐지 명령 detect" 절, `DETECT_SOURCE_KINDS`·`DETECT_DATASET`·`REAL_SPLIT_FILES`·`REAL_SPLIT_KEYS`·`DETECT_REFUSAL`·`DETECT_SPLIT_REFUSAL`, `SplitError`·`load_real_split`·`series_assignment`, `detect_series`·`detection_rows`의 계열 인자
  - `tests/units/F2/test_detect_command.py`: 첫 PR의 실자료 거부 시험을 좁히기·거부 시험으로 바꿨다
  - `tests/units/F2/test_real_split_file.py`: 새 파일
  - `data/reference/real_split_kcs_202201_202412_v2.json`: 새 파일
- 문서 PR(DOCS2)
  - 자료 계약 §10 계획 경로 표에 분할 기록 행을 더한다(사용자 결정 8).
  - 결정 기록 색인에서 AS1 첫 기록의 상태 칸을 "⑤는 이 기록으로 대체"로 고친다.
  - `docs/plan/UNITS.md` P2·F2 행의 설명을 필요하면 맞춘다.
- DT7
  - ①(`real_dev` 경보·사례 목록)은 실자료 정본 빌드 설치(②)를 기다린다. 설치 뒤 `detect --snapshot kcs_202201_202412_v2`로 만든다.
  - ③(`real_sealed` 사례 목록)은 `detect` CLI로 만들 수 없다. 묶음이 `real_dev`로 고정이기 때문이다. 봉인 생성 에이전트가 단위 P2를 `dataset`=`real_sealed`로 부르는 경로는 DT7·V6에서 정한다. 이 PR은 그 경로를 만들지 않았다.
  - 두 경우 모두 탐지 코드의 커밋을 결정 기록에 적는다(⑤).
- D 검수: 분할 기록 정본 파일(①)
