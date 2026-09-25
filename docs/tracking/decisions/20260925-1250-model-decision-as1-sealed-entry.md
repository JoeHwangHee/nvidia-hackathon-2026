# AS1 세 번째 PR: 봉인용 탐지 입구 `detect_dataset_cases`

조립 작업 AS1(탐지 조립: 지표 단위와 판정 정책 단위를 이어 사례 목록을 만드는 작업)의 세 번째 PR에서 정한 것을 적는다. AS1 두 번째 기록(`20260925-0901-model-decision-as1-real-dev.md`)의 "영향과 넘길 곳" DT7 항목에서 넘긴 질문에 답한다. 그 질문은 봉인 생성(로드맵 DT7 ③)이 부를 입구, 곧 출력 위치와 묶음 `real_sealed`를 받는 호출이었다. 두 번째 기록의 ①~⑤는 그대로다. 코드와 시험은 같은 PR에 있다.

용어

- 봉인용 탐지 입구: 격리된 생성 에이전트(봉인 폴더에 쓰는 유일한 역할, 병렬 개발 규칙 §6.3)가 파이썬에서 부르는 함수 `tradesentry.cli.dispatch.detect_dataset_cases`. CLI 명령이 아니다.
- 묶음: 실자료 계열 64개를 나눈 `real_dev`(개발용)와 `real_sealed`(봉인용).
- 분할 기록: 그 배정을 적은 정본 파일 `data/reference/real_split_kcs_202201_202412_v2.json`(단위 V5 출력).
- 좁히기: 관측 값을 읽기 전에 탐지할 계열을 한 묶음으로 줄이는 일.
- 저장소 뿌리: 코드가 있는 작업 폴더와, 그것이 git worktree(한 저장소에서 브랜치마다 따로 여는 작업 폴더)이면 본 작업 폴더.

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 12:50 |
| 제목 | 봉인용 탐지 입구(파이썬 함수 하나): 묶음 `real_dev`·`real_sealed` 선택, 부르는 쪽이 준 저장소 밖 폴더에만 한 파일, `outputs/` 미사용, `code_version`은 돌려주는 값으로 |
| 결정 | 아래 "결정 내용" ①~⑥ |
| 이유와 근거 | 항목마다 적었다 |
| 검토한 대안 | 아래 "검토한 대안" |
| 결정 주체 | 소유 트랙(M). 입구를 함수로 두고 CLI 옵션을 더하지 않는 것과 표본 추출 함수를 만들지 않는 것은 오케스트레이터(작업 지시) |
| 공용 약속 여부 | 아니다. 새 CLI 명령·옵션, 새 계약 키, 새 상태값, 새 파일 이름 규칙을 만들지 않았다. 출력 파일은 단위 P2 출력 그대로이고 이름은 도메인명 규칙(자료 계약 §10.3 N6의 `{도메인명}-{yymmddhhmmss}.{확장자}`)을 따른다. 자료 계약 §10.3 N10과 병렬 개발 규칙 §7.3의 1이 `[미확인]`으로 남긴 "출력 위치를 바꾸는 방법(함수 호출이나 CLI 인자)"의 답으로 함수 호출을 골랐다. 그 문장을 고치는 일은 문서 PR에 넘긴다(아래 "영향") |
| 영향 | 아래 "영향과 넘길 곳" |
| 관련 PR | AS1 세 번째 PR(브랜치 `model/AS1-sealed-entry`) |

## 결정 내용

① **입구는 파이썬 함수 하나다** — 확정

- 형태: `detect_dataset_cases(snapshot_id, policy_version, dataset, out_dir) -> {"file_name", "code_version"}`(단위 F2 `src/tradesentry/cli/dispatch.py`).
- `dataset`은 `real_dev`·`real_sealed` 가운데 하나다(`dispatch.ENTRY_DATASETS`). 그 밖의 값은 정책·스냅샷을 열기 전에 거부한다.
- CLI 명령 표와 옵션은 바꾸지 않았다. 명령 표가 공용 약속이고, CLI `detect`의 묶음은 `real_dev` 고정이다(MT1 결정 ⑭, AS1 두 번째 기록 ②).
- 부르는 예(DT7 ③ 생성 에이전트가 저장소 뿌리에서):
  `env -u NVIDIA_API_KEY -u DATA_GO_KR_SERVICE_KEY uv run --locked python -c "from tradesentry.cli.dispatch import detect_dataset_cases as d; print(d('kcs_202201_202412_v2', 'policy_v1', 'real_sealed', '<봉인 폴더 안의 폴더>'))"`
  - 돌려주는 값에는 파일 이름과 커밋만 있고 사례 내용은 없다. 그래도 생성 에이전트 밖으로는 보고하지 않는다.

② **경로는 CLI `detect`의 실자료 경로와 같다** — 확정

- 흐름
  1. 묶음·출력 폴더 확인(③)
  2. 단위 K4 `load_policy`
  3. 단위 K3 `open_snapshot`(정본 빌드, 읽기 전용)
  4. 출처 종류가 `real`인지 확인. 아니면 거부한다. 분할 기록이 없는 합성 스냅샷은 입구의 대상이 아니다.
  5. `load_real_split`(분할 기록 검사, 두 번째 기록 ③. 관측 값을 읽기 전)
  6. `detect_series(snap, split, dataset)`로 그 묶음 계열만 남긴다.
  7. `detection_rows`(K3 조회 → X1·X2) → P1 → P2. P2에는 `dataset`과 분할 기록 전체의 배정을 넘긴다(두 번째 기록 ④).
- `detect_series`에 키워드 인자 `dataset`(기본값 `real_dev`)을 더했다. CLI `detect`는 이 인자를 넘기지 않으므로 동작이 그대로다(기존 detect 조립 시험 21개 통과).
- `_detect`는 고치지 않았다. 같은 시각에 열린 AS3 두 번째 PR(#48)이 `_detect`의 본문을 `build_case_list`로 옮기므로, 충돌을 피하려고 입구는 같은 함수들(`load_real_split`·`detect_series`·`detection_rows`·`trigger.run`·`case_build.run`)을 직접 부른다. 두 경로가 같다는 것은 아래 시험의 바이트 대조가 묶는다. #48이 병합되면 `build_case_list`에 묶음 인자를 더해 입구가 그것을 부르게 합치는 것은 조립 점검(AS4) 후보다.
- 이유: 봉인 사례 목록이 개발 사례 목록과 다른 코드로 만들어지면, `real_sealed` 결과가 `real_dev`와 같은 탐지 규칙에서 나왔다고 말할 수 없다.

③ **출력 위치: 부르는 쪽이 준 저장소 밖 폴더에만 한 파일** — 확정

- `out_dir`은 이미 있는 폴더여야 한다. 입구는 폴더를 만들지 않는다.
- 심볼릭 링크를 푼 실제 위치(`resolve(strict=True)`)가 저장소 뿌리 안이면 거부한다.
  - 저장소 뿌리는 코드의 작업 폴더(`dal.query.REPO_ROOT`)와, 그것이 worktree면 `.git` 파일 → gitdir → commondir의 부모(본 작업 폴더)다. 하위 프로세스 없이 git 메타 파일만 읽는다.
  - "조상 폴더 어디에든 `.git`이 있으면 거부"하는 규칙은 쓰지 않았다. 홈 폴더가 git 저장소인 환경에서 봉인 폴더 기본값까지 거부하게 된다.
- 봉인 폴더 위치(`TRADESENTRY_SEALED_DIR`)는 입구가 읽지 않는다. 부르는 쪽이 정한다. 그래서 봉인 폴더에도, 해시 등록 전에 지울 저장소 밖 임시 폴더에도 쓸 수 있다(병렬 개발 규칙 §7.3의 1).
- `outputs/`에는 아무것도 쓰지 않고 실행명도 확보하지 않는다(자료 계약 §10.3 N10 "봉인 자료 생성 중의 명령 출력"). 표준 출력·표준 오류에도 아무것도 쓰지 않는다.
- 파일 이름은 `policy_case_build-{yymmddhhmmss}.json`(KST)이다. 사례를 드러내는 정보가 없어 해시 목록의 파일 이름 규칙(자료 계약 §12.2)과 부딪치지 않는다. 봉인 폴더 안 이름을 바꿀지는 생성 에이전트가 정한다.
- 쓰는 순서: 확인을 모두 마치고 P2 출력 모양(키 다섯 개, `dataset`이 요청한 묶음)을 확인한 뒤, 출력 바이트를 다 만들고 나서 파일 하나를 이미 있으면 실패하는 방식(`"xb"`)으로 쓴다.
  - 같은 이름이 있으면 덮지 않고 거부한다.
  - 쓰다 실패하면 그 파일을 지운다.
  - 이유: 봉인 폴더의 해시 재대조는 목록에 없는 파일도 불일치로 본다(자료 계약 §12.2). 반쯤 쓴 파일이나 여분 파일이 남으면 안 된다.
- 바이트 형식은 CLI `write_output`과 같다. 공용 도우미 `json_output_bytes`로 옮겨 둘이 같이 쓴다(`write_output`의 동작은 그대로).

④ **오류는 예외로 알린다** — 확정

- `DatasetEntryError`(묶음·출력 폴더·출처 종류·같은 이름 파일), `policy_load.PolicyError`, `query.SnapshotError`, `SplitError`, `WiringError`(P2 출력 모양·JSON 직렬화).
- 문장에 받은 값(스냅샷 ID·정책 이름·묶음 이름)과 경로를 넣지 않는다(자료 계약 §10.3 N13).
- 종료 코드가 아니라 예외인 까닭: CLI 명령이 아니므로 종료 코드 표(단위 F2)에 들지 않는다.

⑤ **`code_version`은 파일에 넣지 않고 돌려주는 값으로 준다** — 확정

- 파일은 P2 출력 키 다섯 개 그대로다. 자료 계약 안에 탐지 출력의 `code_version` 자리가 없다는 판단은 두 번째 기록 ⑤와 같다.
- 입구는 `dispatch.code_version()`(git 메타 파일에서 읽은 커밋)을 돌려준다. 생성 에이전트는 그 값을 봉인 사건 기록에 적는다(로드맵 DT7 행이 요구하는 탐지 명령의 커밋).
- 한계: `code_version`은 작업 트리의 고치지 않은 변경을 표시하지 않는다. 생성 에이전트는 부르기 전에 `git status --porcelain`이 비었는지와, 그 커밋이 사용자 결정 11의 탐지·CLI 동결 커밋과 같은지를 확인해야 한다.

⑥ **표본 추출 함수는 만들지 않았다** — 확정(작업 지시)

- 40건을 넘을 때의 표본은 생성 에이전트가 기록된 방법(`20260925-0845-user-decision-real-sealed-sampling-method.md`)대로 따로 계산한다. 런타임 코드에 표본 추출을 두면 그 코드가 봉인 seed 파일을 읽는 길이 생긴다.

## 증거

- 시험 `tests/units/F2/test_detect_dataset_entry.py`(15개). 자료는 detect 조립 시험과 같은 합성 스냅샷을 `source_kind` `real`로 만든 것과 임시 파일의 합성 분할 기록(`REAL_SPLIT_FILES`를 `clear=True`로 바꿈)이다. 실제 v1·v2와 저장소의 분할 기록은 쓰지 않는다.
  - `RealDevEntryTest`: `real_dev`로 부른 입구의 출력 바이트가 CLI `detect` 출력 파일의 바이트와 같다. 사례는 CN·FI·US다(공허하지 않음).
  - `RealSealedEntryTest`(합성): 출력이 합성 기대 출력에서 `real_sealed` 계열(DE·JP·PH·SE·TW) 행만 고른 것과 같다. 분할 기록을 먼저 읽는다. `real_dev` 상대국은 행 조회 조건·반환 행·`parent_series`·X1·X2·P1 어디에도 없다. P2는 `real_sealed`와 배정 10개를 받는다.
  - `TwoHs6SealedPairTest`(합성 HS6 두 개 × 상대국 두 개): `real_sealed` 좁히기도 (hs6, partner) 쌍 단위다.
  - 모든 입구 호출에서 표준 출력·오류가 비고, `reserve_run_dir` 호출이 0이며, outputs 자리(`dispatch.OUTPUT_PARENT`, 시험에서는 임시 경로)가 생기지 않는다.
  - `EntryRefusalTest`
    - 거부 대상: 모르는 묶음(`dev20`·`holdout40`·대문자·빈 값·None), 저장소 안 출력 폴더(뿌리, `outputs/` 아래 폴더, 문자열·상대경로, 임시 폴더에서 저장소로 가는 심볼릭 링크), 없는 폴더·파일·경로 아닌 값, 출처 종류 `controlled`, 분할 기록 오류.
    - 거부하면 K3 값 읽기 9개 메서드와 X1·X2·P1·P2 호출이 0이고, 파일이 생기지 않는다. 묶음·폴더 거부에서는 정책·스냅샷도 열지 않는다.
    - 정책·스냅샷 오류, 다른 묶음을 돌려준 P2(`WiringError`), 같은 이름 파일(덮지 않음), 쓰다 실패(반쯤 쓴 파일 지움)도 확인했다.
  - `RepoRootsTest`: worktree 모양의 가짜 git 메타에서 본 작업 폴더를 찾고, 그 안의 폴더를 거부한다.
- 변이 확인(시험 밖 일회 실행, 되돌림은 `cmp`로 확인)
  - `detect_series`가 묶음을 무시하고 두 묶음을 모두 남기게 바꾸면, 입구 시험 2개와 기존 detect 좁히기 시험 2개가 실패했다.
  - `detect_series`가 늘 `real_dev`만 남기게 바꾸면(입구의 `dataset` 무시), 입구 시험 3개가 실패했다.
- 실제 v2 대조(`real_dev`만. `real_sealed`로는 부르지 않았다)
  - 정본 빌드는 본 작업 폴더의 `data/snapshots/kcs_202201_202412_v2/snapshot_build.sqlite`(DT7 재설치본)를 읽기 전용으로 읽었다.
  - 이 브랜치 코드로 CLI `detect --snapshot kcs_202201_202412_v2 --policy policy_v1`(종료 코드 0)과 입구 `real_dev`(저장소 밖 임시 폴더)를 돌렸다.
  - 두 출력 바이트가 같다: sha256 `0a2ef10daf86451ad4a6b6ee676b2a09e812009a8ce43cdd587e9b4c1dce400b`.
  - 사례 221건, 데이터 품질 154행. DT7 재설치 기록(`20260925-1231-orchestrator-decision-dt7-reinstall-v2.md`)의 221건과 같다.

## 검토한 대안

- CLI `detect`에 `--dataset`·`--out-dir` 같은 옵션을 더하는 안: 명령 표는 공용 약속이라 사용자 승인이 필요하다. 또 개발 에이전트가 CLI로 `real_sealed`를 부를 길이 열린다. 버렸다.
- 출력 폴더를 `TRADESENTRY_SEALED_DIR`에서 입구가 직접 정하는 안: 런타임 코드가 봉인 폴더 위치를 알게 되고, 해시 등록 전에 지울 임시 위치를 쓸 수 없다. 버렸다.
- 입구가 폴더를 만들어 주는 안: 오타 난 경로에 새 폴더가 생겨 봉인 폴더 밖에 봉인 자료가 흩어질 수 있다. 버렸다.
- 파일에 `code_version` 키를 더하는 안: 두 번째 기록 ⑤와 같은 이유로 버렸다.
- `_detect`를 입구와 같이 쓰도록 이 PR에서 고치는 안: #48과 같은 자리를 고쳐 충돌한다. 바이트 대조 시험으로 같은 경로임을 묶고, 합치기는 뒤로 미뤘다(②).

## 영향과 넘길 곳

- 바꾼 파일
  - `src/tradesentry/cli/dispatch.py`
    - `json_output_bytes`(`write_output`에서 떼어 냄)
    - `detect_series`의 `dataset` 인자
    - 새 구역 "봉인용 탐지 입구": `ENTRY_DATASETS`·`DatasetEntryError`·`_repo_roots`·`_entry_out_dir`·`detect_dataset_cases`
  - `tests/units/F2/test_detect_dataset_entry.py`: 새 파일
- DT7 ③(격리된 생성 에이전트)
  - 이 입구를 `real_sealed`로 한 번 부르고, 출력 파일(과 표본)을 봉인 폴더에 둔다. 표본은 기록된 방법으로 따로 계산한다.
  - 부르기 전에 작업 트리가 깨끗한지와 커밋이 동결 커밋인지 확인한다(⑤). 돌려받은 `code_version`을 봉인 사건 기록에 적는다.
  - 출력을 저장소 밖 임시 폴더에 받았다면 해시 등록 전에 지운다.
- 문서 PR
  - 자료 계약 §10.3 N10, 병렬 개발 규칙 §7.3의 1, 단위 표 V3·V6 행의 "출력 위치를 바꾸는 방법(함수 호출이나 CLI 인자)은 S0 결정 항목으로 둔다 `[미확인]`"을 "함수 호출 `tradesentry.cli.dispatch.detect_dataset_cases`(이 기록)"로 고칠 것을 권한다. V3(holdout40)은 `detect`를 부르지 않으므로 V6만 해당할 수 있다.
- 조립 점검(AS4): #48의 `build_case_list`와 이 입구의 조립을 하나로 합치는 일(②).
