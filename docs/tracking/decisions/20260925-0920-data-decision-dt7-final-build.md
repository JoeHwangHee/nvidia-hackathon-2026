# DT7 ② 실자료 최종 스냅샷 빌드 설치와 `normalized_sha256`

로드맵 DT7 ②(`policy_v1` 승인 뒤 승격 규칙을 적용한 실자료 최종 스냅샷 빌드를 정본 자리에 두고 `normalized_sha256`을 커밋하는 일)의 실행 기록이다.

용어

- 최종 빌드(정본 빌드): 단위 S2(`src/tradesentry/snapshot/build.py`, 스냅샷 빌더)가 동결 스냅샷의 raw 응답(API가 돌려준 원본 파일)·manifest(수집 요청 목록)·수집기 SQLite(파일 하나로 된 데이터베이스)에서 만든 파생 SQLite. 정본 자리는 `data/snapshots/kcs_202201_202412_v2/snapshot_build.sqlite`다(결정 기록 `20260924-2212-user-decision-snapshot-build-and-g0.md` ①).
- `normalized_sha256`: 빌드 SQLite의 행을 rowid(SQLite가 행마다 붙이는 정수 번호)까지 넣어 정해진 방식으로 직렬화해 구한 sha256(내용 지문). 직렬화는 DT1 결정 기록 `20260925-0002-data-decision-dt1-snapshot-build-and-kernel.md` ①이다.
- 승격: 승인된 정책 규칙으로 빈 응답 달의 `UNRESOLVED_ZERO` 행을 무거래 확정 `CONFIRMED_NO_TRADE`로 바꾸는 일(자료 계약 §3.4).
- 비교국 표: 대상국마다 비교할 나라 목록(`peer_group` 표, 자료 계약 §2.3.6). MVP까지는 `g0`(대상국을 뺀 15개국 가운데 2023년 수입금액 상위 5개국, 결정 기록 `20260925-0049-model-decision-mt6-g0.md`)다.
- raw 대조: 단위 S3(`src/tradesentry/snapshot/verify.py`, 스냅샷 검증)가 raw에서 행을 다시 만들어 빌드의 행과 한 칸씩 비교하는 검사.

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 09:20(기록 시각). 빌드 09:16:42, 설치 09:18:02, 정본 검증 09:18:22(모두 KST) |
| 제목 | `policy_v1`의 승격 규칙과 비교국 표 `g0`를 적재한 v2 최종 빌드를 정본 자리에 설치하고 `normalized_sha256` `b439909a3c894dc773f26eb9e0f53c873cce2ceedcad9bdbdd6c849fa4af4639`를 기록한다 |
| 결정 | 아래 "결정 내용" ①~④ |
| 결정 주체 | 소유 트랙(D). `policy_v1` 수치와 승격 규칙은 사용자(`20260925-0846-user-decision-policy-v1-approval.md`), `g0`로 MVP를 가는 일정은 사용자 결정 11의 D10(`20260925-0847-user-decision-morning-shared-promises.md`) |
| 공용 약속 여부 | 아니다. 승인된 정책·비교국 표·정본 파일 이름을 그대로 썼고, 새 이름·키·경로·CLI 옵션을 만들지 않았다 |
| 영향 | DT7 ①(`real_dev` 경보 목록)과 ③(`real_sealed` 사례 목록)의 입력, `tradesentry detect`·`run-case`·`evaluate`의 실자료 실행, MT5 샌드박스 반입(빌드 기록의 `peer_group_files`로 비교국 표를 들인다), 평가 스킬 ② 사전 점검의 `snapshot-verify` |
| 관련 PR | DT7 PR(브랜치 `data/DT7-real-build`) |

## 결정 내용

① **빌드 입력과 명령** `[사실]`

- 코드: `main` `ad39e3b`(추적 파일 변경 없는 트리, 저장소 루트에서 실행). 정책 `configs/policy_v1.json`(sha256 `0aacda87eab590dbeff5b62050206866aec80f7f8f99cb5a68de182a6e3abf9e`), 비교국 표 `data/reference/peer_group_g0.csv`(sha256 `d712a189dda1cdc8452a713e30034f6cf045489f1562e140216a54cd965a534b`, MT6 기록의 값과 같다).
- `tradesentry snapshot-build`는 비교국 표 파일을 넘기지 않는다(`src/tradesentry/cli/dispatch.py` 머리 설명 "스냅샷 명령": 넘기는 수단은 새 CLI 옵션이라 D10과 함께 정한다). 그래서 그 명령으로 만든 빌드는 `peer_group`이 0행이고, 실자료에서 비교국 조회 도구(단위 I3)가 `no_allowed_peers`로 끝난다. D10은 MVP를 `g0`로 가게 했으므로, CLI 처리 함수 `_snapshot_build`와 같은 순서로 단위를 부르되 비교국 표 하나만 더 넘겼다. 새 옵션·이름·경로는 만들지 않았다.
  ```
  env -u NVIDIA_API_KEY -u DATA_GO_KR_SERVICE_KEY -u TRADESENTRY_SEALED_DIR uv run --locked python <구동 스크립트>
  # 구동 스크립트 본문(저장소 밖 일회 스크립트)
  run_id, stamp, run_dir = dispatch.reserve_run_dir("snapshot_build")      # 실행명 확보(자료 계약 §10.3 N8)
  policy = policy_load.load_policy("policy_v1")                              # 단위 K4
  build.build_snapshot("kcs_202201_202412_v2", out_dir=run_dir, stamp=stamp, policy=policy,
                       peer_group_files=[build.REPO_ROOT / "data" / "reference" / "peer_group_g0.csv"])  # 단위 S2
  ```
  종료 코드 0, 출력 `outputs/snapshot_build-260925091642/snapshot_build-260925091642.sqlite`와 같은 이름의 `.json`.
- 빌드 기록: `policy_version`=`policy_v1`, `confirmed_no_trade_rule`=`ingest_verify_candidates`, `confirmed_no_trade_rows`=208(스냅샷 64계열 전체의 행 수. 경보·지표를 계산한 값이 아니다), `peer_group_files`=`peer_group_g0.csv`(위 sha256), `raw_sha256`=`afc76401431f02b4d8d5e848b197faaa197ce3dd037d66fd7ca719d7ce7bb017`(`snapshot_hash.json`의 `raw_combined_sha256`과 같다), 행 수 `collection_receipt` 357·`observation` 50,132·`peer_group` 320·`snapshot_meta` 14. `g0` 비교국은 모두 수집 상대국이라 계획 밖 국가의 `NOT_COLLECTED` 행이 붙지 않았고, 관측 행 수가 수집기 SQLite(rowid 1~50,132)와 같다.

② **설치 전 검증과 설치** `[사실]`

- 설치 전: 단위 S3 `run({"snapshot_id": "kcs_202201_202412_v2", "build_file": <위 빌드>, "check_raw": true})` → `ok` 참, 검사 18개 모두 통과, 건너뛴 검사 0(raw 대조 `raw_sha256`·`observation_matches_raw`·`receipts_match_raw`·`meta_matches_source`, 비교국 표 원본 대조 `peer_group_sources` 포함). 다시 계산한 `normalized_sha256`이 빌드 기록과 같다.
- 설치: 단위 S2 `install_build(<위 빌드>, data/snapshots/kcs_202201_202412_v2)` → 종료 코드 0. 정본 폴더에 `snapshot_build.sqlite`(sha256 `023a1d1808546a0d39d7b445d941fe236979fcb883cf6fa5215284dc5814c3b5`)와 `snapshot_build.json`(sha256 `fd07989539fbb049261ef2d17246b0840daf6b32e76c65f541040f3331f26398`) 두 파일만 새로 생겼다. `-journal`·`-wal` 파일은 없다.
- 설치 뒤: `env -u NVIDIA_API_KEY -u DATA_GO_KR_SERVICE_KEY -u TRADESENTRY_SEALED_DIR uv run --locked tradesentry snapshot-verify --snapshot kcs_202201_202412_v2` → 종료 코드 0(`outputs/snapshot_verify-260925091822/`, `ok` 참, 검사 18개 통과, 기록값과 재계산 값이 `b439909a…4639`로 같다).
- 커밋하는 것: 정본 빌드 기록 `data/snapshots/kcs_202201_202412_v2/snapshot_build.json`(설치로 생긴 파일을 바이트 그대로 복사, sha256 위와 같다)과 이 기록. SQLite는 `.gitignore`가 뺀다.

③ **동결 파일을 바꾸지 않았다** `[사실]`

- 빌드 전·설치 전·설치 뒤 세 번 잰 sha256이 모두 같다. raw 파일은 357개다.

  | 파일 | sha256 |
  |---|---|
  | `collection_http_attempts.jsonl` | `10a86a1230f182687fadaa09da7fc1804f14f4bf33ceb3cbdffbb66222b267b1` |
  | `data-readiness.json` | `2dac28fb8658ea1c75203f053b21ffae46424b590ec204bdae3649bbc476e489` |
  | `manifest.json` | `09c8ca1c7ee668d4274e8bcefb46bb861db7bf819c74fdf4a3fa6132276d0dac` |
  | `snapshot_hash.json` | `60e6b1a9f2b4d718ecc6373264358922875f617152bd21c3b76fecea1d31682e` |
  | `snapshot.sqlite` | `253820741e577ff2cb74fd6bb90950333d0aa915aa17081c0b76d237ef2667f5`(MT6 기록의 값과 같다) |
  | raw 결합 해시(`shasum -a 256 raw/*.xml \| shasum -a 256`) | `afc76401431f02b4d8d5e848b197faaa197ce3dd037d66fd7ca719d7ce7bb017`(`snapshot_hash.json` 기록과 같다) |
- 수집기의 `plan`·`collect`·`verify`를 돌리지 않았다. `git status --short data/snapshots/`의 추적 파일 변경은 0건이다.

④ **교차 확인: 승격은 DT4 ② 통계의 빌드와 같다** `[사실]`

- 비교국 표 없이 CLI 그대로(`tradesentry snapshot-build --snapshot kcs_202201_202412_v2 --policy policy_v1`, 종료 코드 0, `outputs/snapshot_build-260925091705/`) 만든 빌드의 `normalized_sha256`은 `43829179dd3a3adae84d11b27a96738c2b61f0eb245e87118a2333fbe312470c`로, `policy_v1` 승인 기록의 승격 what-if 빌드와 같다. 그래서 최종 빌드는 그 통계 빌드에 `g0` 320행만 더한 것이고, DT7 ①의 경보 수 대조(221건)는 같은 관측·승격 위에서 한다. 이 빌드는 설치하지 않았다.

## 검토한 대안

- CLI `snapshot-build` 출력을 그대로 설치: 비교국 표가 비어 실자료 비교국 조회가 되지 않고, `install_build`는 덮어쓰기를 거부하므로 나중에 `g0`를 넣으려면 동결 폴더의 파일을 지우는 절차가 필요하다. 버렸다.
- CLI에 비교국 표 옵션을 더함: 계획 명령 표 변경(공용 약속)이라 사용자 승인이 필요하고, DT7 범위 밖이다. 버렸다.
- 공통 실행기 `python -m tradesentry.units S2`: SQLite 바이트만 쓰고 옆에 빌드 기록을 남기지 않아 `install_build`가 읽지 못한다. 버렸다.

## 남은 일

- `g1`(BACI 유사도 비교국 목록)을 정본 빌드에 넣게 되면 `normalized_sha256`이 바뀌고, 정본 두 파일을 바꾸는 절차가 필요하다(`install_build`는 덮어쓰지 않는다). 그 절차와 시점은 오케스트레이터가 정한다. `g0` 대체 선언이면 이 빌드를 그대로 쓴다.
- 설치 뒤 `data/reference/peer_group_g0.csv`를 바꾸면 `snapshot-verify`가 실패한다(DT1 결정 기록 ⑪). 바꿔야 하면 새 파일 이름과 새 빌드로 한다.
- main 폴더에 설치된 두 파일 가운데 `snapshot_build.json`은 이 PR의 커밋과 같은 바이트다. 병합 뒤 main 폴더의 추적되지 않은 사본 정리는 오케스트레이터가 한다.
