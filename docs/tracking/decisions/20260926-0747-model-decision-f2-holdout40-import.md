# F2 준비: holdout40 봉인 입력 반입 도구 `scripts/import_sealed_holdout40.py`와 스테이징 도구의 `--overlay`

룰북 `RB-1`(평가 룰북의 첫 동결 버전) 동결 뒤 F2(봉인 묶음 채점, 2026-09-26(토) 20:00 목표)에서 holdout40(봉인한 합성 평가 사례 40건)의 봉인 **입력**을 공식 채점 대상 실행 전용 샌드박스 이미지에 넣는 방식을 정한 기록이다. 결정 기록 `20260925-0530-model-decision-mt5-sandbox.md` ②가 `[잠정]`으로 남긴 "봉인 입력 반입"과 `20260926-0715-orchestrator-decision-sealed-hash-registration.md`의 `[미확인]`("holdout40 반입 방식은 F2 준비 때 정한다")을 채운다. 채점 규칙·판정 정책·검증기·채점기·`configs/openshell/policy.yaml`은 바꾸지 않았다.

용어

- 봉인 입력: 봉인 자료(개발 중 보지 않도록 저장소 밖 봉인 폴더에 두는 평가 자료) 가운데 전용 샌드박스에 읽기 전용으로 넣는 입력 파일. holdout40의 `input/` 아래(사례 목록 `cases.json`, 수집기 형식 원천 `source/`)만이다. 정답표(`answers/`)·생성 코드(`gen/`)·`real_sealed`는 넣지 않는다.
- 해시 목록: `eval/sealed_manifest.json`. 봉인 폴더 파일 202개의 sha256(파일 내용의 지문) 목록(자료 계약 §12.2).
- 겹침 폴더(overlay): 저장소 밖에 저장소 상대경로 배치로 둔 파일 묶음. 스테이징 도구가 빌드 맥락에 더한다.
- 빌드 맥락: `openshell sandbox create --from <폴더>`가 이미지를 굽는 폴더(Dockerfile, `app/`, `image/`). `app/`이 이미지의 `/opt/tradesentry/`가 된다.
- 단위 S2·S3: 스냅샷 빌드(`tradesentry.snapshot.build`)와 스냅샷 검증(`tradesentry.snapshot.verify`).

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-26(토) 07:47(기록 시각). 바탕은 `main` dc9e76b |
| 제목 | holdout40 봉인 입력 반입 도구와 스테이징 도구 `--overlay`: 해시 대조 → 입력만 읽어 빌드·검증 → 저장소 밖 겹침 폴더 → 이미지 빌드 맥락에 겹침 |
| 결정 | 아래 ①~⑦. ①~③은 `[DESIGN: 오케스트레이터 결정]`(작업 지시 H40IMPORT)이고, 세부(옵션 이름·기록 키·거부 이름·경로 파생)는 소유 트랙(M)이 정했다 |
| 이유와 근거 | 아래 "까닭" |
| 검토한 대안 | 아래 "검토한 대안" |
| 결정 주체 | 소유 트랙(M). 도구·옵션·경로·정책 확인의 틀은 오케스트레이터 지시 |
| 공용 약속 여부 | 아니다. 자료 계약의 값·키·상태값·경로 표와 `configs/openshell/policy.yaml`은 바꾸지 않았다. 새 파일 `scripts/import_sealed_holdout40.py`와 `image_manifest.json`의 새 키(`files[].source`, `overlays`)는 M 소유 도구의 세부다. 평가 스킬 ②(공용 문서)의 `[미확인]` 문구는 고치지 않고 아래 "스킬에 반영할 문장"에 적었다 |
| 영향 | 파일: `scripts/import_sealed_holdout40.py`(새), `scripts/stage_sandbox_image.py`(`--overlay`), `configs/openshell/image/include.txt`(머리 주석), `tests/test_import_sealed_holdout40.py`(새), `tests/test_sandbox_image.py`, `docs/operations.md`("F2 봉인 입력 반입" 행). 작업: F2(봉인 묶음 채점)의 공식 채점 단계 2~4, 평가 스킬 ② 문구 반영(공용 문서 PR), 로드맵 MT5 ⑤ 리허설 |
| 관련 PR | 브랜치 `model/MT5-f2-holdout40-import`(번호는 PR을 연 뒤 적는다) |

## 결정 내용

① **반입 도구** `scripts/import_sealed_holdout40.py`(단위 F5 보조, 소유 M). 명령은 저장소 루트에서
`env -u NVIDIA_API_KEY -u DATA_GO_KR_SERVICE_KEY uv run --locked python -m scripts.import_sealed_holdout40 --dest <저장소·봉인 폴더 밖의 새 폴더> [--sealed-dir <봉인 폴더>] [--manifest eval/sealed_manifest.json] [--snapshot-id holdout40] [--policy policy_v1]`.
- `--sealed-dir`의 기본은 `TRADESENTRY_SEALED_DIR`, 없으면 `~/.tradesentry/sealed/`(자료 계약 §10). `--snapshot-id`(기본 `holdout40`)·`--policy`(기본 `policy_v1`)는 봉인 묶음의 값과 같아야 한다(`cases.json`의 `dataset`은 `holdout40`, `snapshot_id`·`policy_version`은 인자와 같음. 다르면 종료 2).
- 순서: (1) 해시 목록 `files` 전체(두 묶음 202개)를 봉인 폴더와 대조 — 목록 파일 전부 존재·sha256 일치·목록 밖 파일 0개(OS 메타데이터 파일 포함). 불일치면 아무것도 쓰지 않고 종료 2. 표준 오류에는 목록 안 파일 이름(없음·해시 다름)만 적고 목록 밖 파일은 수만 적는다(평가 스킬 ② "해시 대조 방법"). (2) `holdout40/input/cases.json`과 `holdout40/input/source/`(`manifest.json`·`collection_log.json`·`snapshot_hash.json`·`snapshot_build.json`·`peer_group_<snapshot_id>.csv`·`raw/*.xml`)만 읽는다. 내용 읽기는 모두 `read_input_bytes` 한 함수를 거치고 그 함수가 `holdout40/input/` 밖 경로를 거부한다. 해시 대조 단계의 sha256 계산은 바이트만 읽고 내용을 다루지 않는다. (3) 임시 폴더에 수집기 형식 원천을 놓고 수집기 `store_result`로 수집기 SQLite를 재현(시각은 `collection_log.json`의 고정 시각, 수집기 `snapshot_meta`는 원천 빌드 기록의 `snapshot_meta` 키 또는 `--collector-meta` 파일에서. 아래 "한계") → 단위 S2 `build_to`(정책 객체는 `--policy`, 비교국 표는 원천의 CSV) → 단위 S3 `verify_snapshot`(raw 대조 켬, 비교국 표 명시). 빌드 기록의 `normalized_sha256`이 원천 `snapshot_build.json`의 값과 같아야 한다(`cases.json`에 `snapshot_normalized_sha256`이 있으면 그 값과도). 검증 실패나 값 불일치면 종료 3(임시 폴더는 지운다). (4) `<dest>/`에 저장소 배치 그대로 배타 생성: `data/snapshots/<snapshot_id>/snapshot_build.sqlite`·`snapshot_build.json`(S2 기록 + `build_file`·`installed_from`·`installed_at`), `data/reference/peer_group_<snapshot_id>.csv`(원천 바이트 그대로), `eval/dev/holdout40/input/cases.json`(원천 바이트 그대로), 그리고 `import_manifest.json`(쓴 파일별 sha256·크기, 쓴 원천의 해시 목록 항목 `file_name`·`sha256` 참조, 해시 대조 건수, 해시 목록 파일의 sha256, `normalized_sha256`). `<dest>`는 아직 없는 이름이어야 하고, 부모 사슬이 저장소 뿌리(이 작업 폴더·본 작업 폴더·git이 아는 모든 worktree)나 봉인 폴더와 파일 정체성(`st_dev`·`st_ino`)이 같으면 거부한다(`tradesentry.cli.dispatch._entry_out_dir`와 같은 방식). (5) 표준 출력은 세 줄: `hash_check listed= matched= extra=`, `build snapshot_id= policy_version= normalized_sha256=`, `written files= import_manifest_sha256=`. 사례 식별자·값·로컬 절대경로는 내지 않는다(자료 계약 §10.3 N13). 예상 밖 예외는 이름만 적고 종료 1.
- import 범위: 표준 라이브러리 + `tradesentry.ingest`·`tradesentry.snapshot`·`tradesentry.contract`. `eval.datagen`·`eval.scorer`·판정·조사 코드는 import하지 않는다. 수집기 표 정의(DDL)는 `eval/datagen/dev20.py`와 같은 사정(수집기 `open_snapshot`은 스냅샷 폴더 위치가 고정)으로 도구 안에 같은 문장을 둔다.

② **스테이징 도구 확장** `scripts/stage_sandbox_image.py --overlay <폴더>`(여러 번 가능).
- 겹침 폴더는 저장소 밖·봉인 폴더 밖 폴더여야 한다(심볼릭 링크 거부). 안의 파일을 저장소 상대경로로 보고 빌드 맥락 `app/`에 더한다. 같은 상대경로가 저장소에 있으면(대소문자만 다른 별칭 포함, 부모 폴더 목록을 casefold로 비교) 거부한다 — 봉인 입력이 저장소 파일을 덮지 않게. 겹침 폴더 사이의 같은 경로도 거부한다.
- 거부 규칙은 겹침 파일에도 그대로 적용한다(`.env`류, `outputs/`, `artifacts/`, `eval/scorer/`, `eval/datagen/`, `eval/sealed_manifest.json`, raw/·manifest·수집기 SQLite·`fixture_spec.json`, 이름에 oracle·answer). eval/ 예외만 `eval/dev/<묶음>/input/` 아래로 넓힌다(`--add`의 예외는 `eval/dev/dev20/input/` 그대로). 정답표·생성 규칙·seed 이름 `answers.json`·`parent_series_ids.json`·`generation_rules.json`·`sample_seed.json`·`fixture_spec.json`은 저장소·겹침 어디서든 거부한다(새 규칙 `BLOCKED_NAMES`. 기존 포함 목록에는 이 이름이 없어 기존 동작은 그대로다).
- 겹침 폴더 뿌리의 `import_manifest.json`(반입 도구의 기록)은 들이지 않고 sha256만 이미지 기록 `overlays[].import_manifest_sha256`에 적는다.
- 이미지 기록 `image_manifest.json`: `files[]` 항목마다 `source`(`repo`·`overlay`)를 더하고 `overlays`(폴더별 파일 수·기록 sha256) 키를 더한다. 겹침의 빌드 기록(`data/snapshots/<id>/snapshot_build.json`)도 기존과 같이 `snapshots`에 `snapshot_id`·`normalized_sha256`·비교국 표를 적고, 비교국 표는 겹침에 있으면 그것, 없으면 저장소의 것을 sha256 대조 뒤 들인다. 옵션이 없을 때의 동작은 파일 선택·거부·복사가 그대로다(기존 시험 24개가 증거. 바뀐 것은 기록의 두 키만).
- 표준 출력에 `overlay <번호> files=<수> import_manifest_sha256=<값>` 한 줄을 더한다.

③ **샌드박스 안 배치**. 겹침 폴더가 `app/`에 겹쳐지므로 봉인 입력 사본은 이미지의 `/opt/tradesentry/data/snapshots/holdout40/snapshot_build.sqlite`·`snapshot_build.json`, `/opt/tradesentry/data/reference/peer_group_holdout40.csv`, `/opt/tradesentry/eval/dev/holdout40/input/cases.json`이 된다. 정답표는 이미지에 없다. MT5 샌드박스 결정 기록 ②의 `/opt/tradesentry/sealed_input/{묶음}/`은 쓰지 않는다(아래 "검토한 대안").

④ **정책 확인 결과**. `configs/openshell/policy.yaml`은 바꿀 필요가 없다. 근거: `/opt/tradesentry`가 `read_only` 항목이고 작업 폴더(`/sandbox`)·`read_write`(`/tmp`, `/dev/null`) 밖이다. 봉인 입력 사본은 모두 `/opt/tradesentry` 아래(③)라 정책 항목을 더하지 않아도 읽기 전용으로 들어가고, 쓰기는 `read_only`가 막는다(위반 시험 쓰기 거부 행의 기대 `deny(read_only)`, EACCES). 봉인 폴더 자체는 어느 항목에도 없다(사본만 들어간다). 정답표·`outputs/`·`eval/scorer/`·`.env`는 이미지에 없고 허용 목록에도 없다(요건 (a)). 네트워크 계층(요건 (b))은 건드리지 않았다. 다만 `/opt/tradesentry` 한 항목이 앱 코드·설정·스냅샷·봉인 입력 사본을 한꺼번에 덮으므로, "봉인 폴더 아래에서는 봉인 입력 하위 경로만 `read_only`"라는 평가 스킬 ② 공식 채점 단계 4의 문장은 이 방식에서는 "봉인 입력 사본은 `/opt/tradesentry` 아래에만 있고 정답표 사본은 이미지 어디에도 없다"로 읽어야 한다(아래 "스킬에 반영할 문장").

⑤ **위반 시험 인자 확인**. `scripts/openshell_violation_tests.py run --scored <이름> --scored-kind official`은 인자 추가 없이 충분하다. `--ro-write-path /opt/tradesentry/data/snapshots/holdout40`(쓰기 거부 행이 `<경로>/probe-<시각>` 탐침 파일을 만든다. 기존 파일을 고치지 않는다), `--absent-name`(여러 번. `answers.json`·`parent_series_ids.json`·`generation_rules.json`·`sample_seed.json`. 부재 확인 행이 `/opt/tradesentry`와 `/sandbox`를 이름으로 훑는다. 기본 이름 `oracle_ABC.json`은 늘 본다), `--verify-snapshot holdout40`(S 행이 단위 S3를 raw 대조 없이 돌리고 `image_manifest.json`의 `snapshots`에서 `normalized_sha256`을 찾는다), `--image-manifest-sha256 <스테이징 출력>`(M1 행). 코드를 고치지 않았다. 실제로 돌리지는 않았다(오케스트레이터가 F2 때 돌린다).

⑥ **시험**. `tests/test_import_sealed_holdout40.py`: 임시 폴더에 dev20 공개 원천으로 가짜 봉인 묶음(배치는 봉인 폴더의 holdout40 배치, `cases.json`은 `dataset`만 `holdout40`, `answers/`·`gen/`·`real_sealed/` 자리는 가짜 내용)과 가짜 해시 목록을 만들어 `--snapshot-id dev20 --policy dev-0.1`로 돌린다. (a) 해시 다름·목록 밖 파일(`.DS_Store`)·목록 파일 없음 → 종료 2, dest 없음, 목록 밖 파일 이름은 출력하지 않음 (b) 성공 → dest 파일 4개 + `import_manifest.json`, 빌드 `normalized_sha256`이 커밋된 dev20 빌드 기록의 값(`fb802b8f…`)과 같음(도구 밖의 독립 기대값) (c) 열기 호출 추적(`builtins.open`·`io.open`)으로 해시 계산 밖에서 연 봉인 파일이 `holdout40/input/` 아래만임 (d) 표준 출력·오류에 사례 식별자 20개와 임시 폴더 절대경로가 없음. 그 밖에 `read_input_bytes` 거부, 종료 3(기록값 바꿈), 입력 모양 거부, dest 규칙(저장소 안·이미 있음·봉인 폴더 안·부모 없음), 봉인 폴더 불변, dest에 수집기 SQLite·raw 없음. `tests/test_sandbox_image.py`에 `--overlay` 7건(정상 추가와 `source`·`overlays` 기록, 옵션 없을 때 전부 `repo`, 저장소와 겹치는 경로(대소문자 별칭 포함) 거부, 거부 규칙 18개 경로, 심볼릭 링크·중복·없는 폴더·저장소 안·봉인 폴더 안 거부, 비교국 표 sha256 불일치 거부, main 출력에 로컬 경로 없음).

⑦ **경로 파생**. 도구는 스냅샷 폴더 이름과 비교국 표 이름을 `--snapshot-id`에서 파생한다(`data/snapshots/<snapshot_id>/`, `peer_group_<snapshot_id>.csv`). 실제 봉인 묶음의 값은 해시 목록의 파일 이름 `holdout40/input/source/peer_group_holdout40.csv`로 보아 `holdout40`이다(이름만 보았다). 그래서 기본값으로 돌리면 오케스트레이터 지시의 경로(`data/snapshots/holdout40/…`)가 된다. 사례 목록의 자리는 `eval/dev/holdout40/input/cases.json`으로 고정이다(`dataset`).

## 까닭

- 해시 대조를 도구 안에서 반입 직전에 하는 것: 병렬 개발 규칙 §6.6 "봉인 입력을 샌드박스에 넣기 전에도 해시를 대조한다"와 평가 스킬 ② 공식 채점 단계 3(사본을 넣으면 넣을 사본을 반입 직전에 해시 목록과 대조). 두 묶음 전체를 대조하는 것은 자료 계약 §12.2·스킬 "해시 대조 방법"이다.
- 입력만 읽고 정답표를 열지 않는 것: 병렬 개발 규칙 §6.5(입력과 정답표를 다른 하위 경로에, 허용 목록에는 입력 하위 경로만), 자료 계약 §12.3의 4(정답표는 어떤 샌드박스에도 넣지 않는다). 읽기 관문 한 함수로 좁혀 시험이 추적할 수 있게 했다.
- 봉인 폴더의 원천을 그대로 넣지 않고 샌드박스 밖에서 빌드하는 것: 스냅샷 원천(raw/·manifest·수집기 SQLite)은 스테이징 도구의 거부 대상이고(개발 플랜 §4.3 "반입 목록"), 샌드박스 안 스냅샷 검증은 raw 대조 없이 빌드 파일과 기록만 본다(MT5 결정 ⑫). dev20의 `install`과 같은 경로(수집기 형식 원천 → 수집기 SQLite → 단위 S2 → 단위 S3)를 밟아 dev20과 같은 방식으로 빌드가 재현된다. `normalized_sha256`을 원천 기록과 대조하는 것은 자료 계약 §4.4(SQLite 밖 기록과 대조)와 평가 스킬 ② 사전 점검 단계 2의 7번·단계 4의 3번과 같은 구조다.
- 저장소 안에 사본을 두지 않는 것(`--dest`·`--overlay` 모두 저장소 밖): 병렬 개발 규칙 §6.1(봉인 폴더를 저장소·작업 폴더 안에 두지 않는다), 평가 스킬 ② 공식 채점 단계 3(사본은 저장소나 에이전트 작업 폴더에 두지 않는다). 파일 정체성 비교는 대소문자·firmlink·심볼릭 링크로 저장소 안을 가리키는 경로를 잡기 위한 것으로, `tradesentry.cli.dispatch._entry_out_dir`와 같은 방식이다.
- 저장소와 겹치는 경로를 거부하는 것: 겹침 폴더가 저장소 파일을 덮으면 이미지의 코드·설정이 봉인 묶음에 따라 달라져 "같은 조건"(룰북 B2)이 깨진다. 이름만 다른 별칭도 잡아 대소문자를 구분하지 않는 파일 시스템의 우회를 막는다(MT5b 보안 검토 1과 같은 이유).
- 기록에 출처(`source`)를 남기는 것: 사전 점검·위반 시험 M1 행이 이미지 기록의 sha256을 대조하므로, 어떤 파일이 봉인 사본인지 기록에서 바로 보이게 한다. 봉인 사본의 sha256은 봉인 원천이 아닌 빌드 결과·사례 목록 바이트의 지문이라 사례 내용을 드러내지 않는다(사례 목록 바이트의 sha256은 해시 목록에도 이미 있다).

## 검토한 대안

- (가) MT5 결정 ②의 `/opt/tradesentry/sealed_input/{묶음}/`에 봉인 원천을 그대로 굽는 것: 버렸다. 원천(raw/·manifest·수집기 SQLite)은 거부 대상이고, CLI·단위 S3·자료 접근층이 스냅샷을 `data/snapshots/<id>/`와 `data/reference/`에서 찾으므로 별도 경로면 코드에 새 경로 옵션이 필요하다(공용 약속 변경 가능성). 저장소 배치로 겹치면 코드 변경 없이 `tradesentry run-case --snapshot holdout40`이 그대로 돈다.
- (나) 도구가 봉인 폴더에 빌드 결과를 쓰는 것: 버렸다. 봉인 폴더에 파일이 생기면 해시 대조에서 목록 밖 파일로 잡혀 두 묶음이 무효가 된다(스킬 "누가 닿나").
- (다) `eval/datagen/dev20.py`의 `materialize_collector`·`build_and_verify`를 import하는 것: 버렸다. `eval/` 자료 도구는 이미지에 들어가지 않고, 반입 도구가 정답표 검사 코드(`holdout40_check`)를 끌어오는 것도 피한다. 대신 같은 함수(`ingest.store_result`, `s2.build_to`, `s3.verify_snapshot`)를 직접 부른다.
- (라) 스테이징 도구의 `--add`로 저장소 밖 경로를 받는 것: 버렸다. `--add`는 저장소 상대경로만 받고 봉인 폴더 안 경로를 거부하는 규칙이 있다. 별도 옵션이 규칙을 헷갈리게 하지 않는다.
- (마) `image_manifest.json` 기록 키를 바꾸지 않고 겹침 파일을 `files`에 섞기만 하는 것: 버렸다. 봉인 사본과 저장소 파일이 구분되지 않아 사전 점검이 기록만으로 봉인 사본을 셀 수 없다.

## 스킬에 반영할 문장(공용 문서라 이 PR에서 고치지 않는다. 문서 PR이 옮긴다)

- `skills/tradesentry-eval/SKILL.md` 공식 채점 단계 3의 "넣는 방식은 로드맵 MT5에서 정한다 `[미확인]`" → "넣는 방식은 반입 도구 `python -m scripts.import_sealed_holdout40 --dest <저장소·봉인 폴더 밖의 새 폴더>`(해시 목록 전체 대조 → holdout40 입력만 읽어 단위 S2 빌드·단위 S3 검증 → `normalized_sha256` 대조 → 저장소 배치의 겹침 폴더)와 `python -m scripts.stage_sandbox_image --dest <빌드 맥락> --overlay <그 폴더>`로 이미지에 굽는 것이다(결정 기록 `docs/tracking/decisions/20260926-0747-model-decision-f2-holdout40-import.md`). 사본은 이미지의 `/opt/tradesentry/data/snapshots/holdout40/`과 `/opt/tradesentry/eval/dev/holdout40/input/cases.json`이고, 샌드박스 안 재대조는 위반 시험의 S 행(단위 S3 raw 대조 없이, `image_manifest.json`의 `normalized_sha256`과 대조)이다. 공식 실행 뒤 겹침 폴더와 빌드 맥락 폴더를 지우고 봉인 사건으로 기록한다".
- 같은 절 공식 채점 단계 4 통과 기준의 "봉인 폴더 아래에서는 봉인 입력 하위 경로만 `read_only`로 허용한다" → "봉인 폴더 경로는 정책에 없고, 봉인 입력 사본은 `read_only`인 `/opt/tradesentry` 아래(위 두 경로)에만 있으며 정답표 사본은 이미지 어디에도 없다(`--absent-name`으로 확인)".
- `docs/rules/DATA_CONTRACT_V1.md` §12.3의 4 "넣는 방식은 X1 뒤에 확정한다 [미확인]"과 `docs/rules/PARALLEL_DEV_RULES.md` §6.5 "구체 방식은 로드맵 MT5에서 확정한다 `[미확인]`"도 같은 문장으로 채울 수 있다(공용 약속의 값은 바뀌지 않는다).

## 한계

- 도구는 같은 OS 사용자 권한으로 돌아 봉인 폴더 열람을 기술적으로 막지 못한다. "입력만 읽는다"는 코드 구조(읽기 관문)와 시험(열기 호출 추적)으로 보이는 것이고 권한으로 강제한 것이 아니다(병렬 개발 규칙 §6.4).
- 해시 대조 단계는 정답표 파일의 바이트도 읽는다(sha256 계산). 내용을 해석하지 않지만 프로세스 메모리를 거친다.
- 이미지 층과 빌드 캐시에 봉인 입력 사본이 남는다(MT5 결정 ②의 "남는 위험" 그대로). 공식 채점 뒤 이미지·샌드박스·겹침 폴더·빌드 맥락을 지우는지 봉인 사건으로 기록한다.
- `--dest`가 저장소 밖인지의 정체성 비교는 이 작업 폴더의 git 메타 파일이 아는 worktree까지다. 저장소를 다른 곳에 통째로 복사한 폴더는 잡지 못한다.
- 실제 봉인 묶음으로는 돌리지 않았다(시험은 dev20 공개 원천의 가짜 묶음). 실제 묶음의 `snapshot_id`·`policy_version`이 기본값(`holdout40`·`policy_v1`)과 다르면 종료 2로 멈추고, 그때는 인자로 값을 주기 전에 오케스트레이터가 원인을 확인한다.
- 수집기 `snapshot_meta`(`source_kind`·`importer`·`valuation_basis`·`units`·`precision_rule`·`coverage_status`, 선택 `source_url`·`units_confirmed`)는 단위 S2 정규화 해시에 들어가므로 도구가 고정하지 않고 봉인 빌드 기록(`holdout40/input/source/snapshot_build.json`)의 `snapshot_meta`(또는 `collector_meta`) 키에서 읽는다(독립 검토 1회차 권고 1). 기록에 그 키가 없으면 `--collector-meta <JSON 파일>`로 채우고, 필수 키가 하나라도 없으면 종료 2(무기록)다. 파생 키(`snapshot_id`·`created_at`·`last_collect_at`·`hs_version`·`period_start`·`period_end`)는 원천에서 채우고 기록값과 다르면 종료 2다. 실제 묶음의 기록에 메타가 있는지는 이름만 본 지금은 모른다. 실제 묶음으로는 F2 직전 예행(종료 코드·건수만 확인, dest는 예행 뒤 삭제)으로 본다. 종료 3이면 메타 불일치가 첫 의심 원인이고, 생성 에이전트의 보고(메타 값)로 `--collector-meta`를 채운다.
- 봉인 폴더 안의 심볼릭 링크(파일·폴더)는 해시 목록에 없으므로 목록 밖 항목으로 세어 불일치(종료 2)다(권고 2). 원천 `manifest.json`·`collection_log.json`의 키 누락은 입력 모양 오류로 종료 2다.
- 실제 openshell·docker는 부르지 않았다. 위반 시험 인자 확인(⑤)은 코드 읽기다.
