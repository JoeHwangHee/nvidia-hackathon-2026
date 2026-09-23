# 엔지니어링 노트

## 스냅샷과 수집기

### 수집기 명령이 커밋된 스냅샷 기록을 다시 쓴다

- 증상: `src/tradesentry/ingest.py verify --snapshot kcs_202201_202412_v2`를 돌린 뒤 `git status`에 그 스냅샷 폴더의 `data-readiness.json` 변경이 뜬다. `plan`·`collect`를 돌리면 `manifest.json`이 바뀐다.
- 원인: `verify`의 `--out` 기본값이 스냅샷 폴더 안의 `data-readiness.json`이고, v1·v2의 이 파일은 커밋된 기록이다. `plan`·`collect`는 `manifest.json`(수집 요청 목록)을 다시 쓰는데, `verify`는 그 파일로 기대 요청 쌍을 계산하므로 이후 검사 결과까지 조용히 바뀐다. `configs/collection_plan.json`의 `snapshot_id`가 v2를 가리키므로 설정을 그대로 두고 수집하면 v2가 덮인다.
- 대응: 비교용 검사는 `--out <새 파일 이름>`으로 돌린다. 그 파일은 스냅샷 폴더 안에 새로 생기니 커밋하지 않는다. v1·v2에는 `plan`·`collect`를 돌리지 않는다. 이미 덮었으면 `git checkout -- <그 파일>`로 되돌린다.
- 확인: `git status --short data/snapshots/`에 추적 중인 파일의 변경이 없다.
- 정본: `docs/rules/PARALLEL_DEV_RULES.md` §10.1

### 전체국가(`ALL`) 분모가 두 배로 잡힌다

- 증상: HS6의 전체국가 월 금액을 `ALL` HS10 월 행을 더해 만들면 v2에서 값이 정확히 두 배가 되고, 점유율이 절반으로 떨어져 점유율 경보가 틀어진다.
- 원인: v2는 품목별 API의 HS4 `8504` 요청과 HS6 요청이 같은 `ALL`×HS10×월 행(수입 612키, 값 동일)을 두 번 담는다. `ALL`에는 월별 HS6 행이 없고 HS6 자릿수의 `ALL` 행은 모두 총계 행이라, 분모는 HS10 행 합으로만 만든다.
- 대응: (HS10, 월)로 중복을 뺀 뒤 더한다. 총계 행(`month`=`RAW:총계`)은 대조에만 쓰고 근거 ID로 쓰지 않는다.
- 확인: 더하기 전에 (HS10, 월) 키가 한 번씩만 남았는지 센다. v2 대상 HS6에서는 수입 612키다.
- 정본: `docs/rules/DATA_CONTRACT_V1.md` §2.3.2 행 규칙 5·6, `docs/plan/DEV_PLAN.md` §6.1

## 실행 환경

### 시스템 파이썬으로는 앱 코드를 돌릴 수 없다

- 증상: `import pandas`나 3.10 이후 문법에서 실패한다.
- 원인: 이 개발 기계의 시스템 `python3`는 3.9.6이고 pandas·openpyxl이 없다. 앱은 Python 3.12 가상환경(uv)을 쓰기로 했고, 그 환경은 앱 뼈대(S0)에서 만든다.
- 대응: S0 전에는 표준 라이브러리 코드와 기존 시험만 시스템 `python3`로 돌린다. `ingest.py`는 계속 표준 라이브러리만 쓴다.
- 정본: `docs/plan/DEV_PLAN.md` §3.5

### macOS 기본 셸에서 검사 스크립트가 엉뚱하게 멈춘다

- 증상 1: `set -u`를 켠 bash 스크립트가 빈 배열을 `"${ARR[@]}"`로 펼칠 때 `unbound variable`로 끝난다.
- 원인 1: macOS 기본 bash는 3.2이고, 이 버전은 `set -u`에서 빈 배열 펼치기를 정의되지 않은 변수로 본다.
- 대응 1: `${ARR[@]+"${ARR[@]}"}`로 펼친다. 확인은 빈 목록을 넣고 돌려 종료 코드 0을 보는 것이다.
- 증상 2: zsh에서 `set -- $pair`처럼 따옴표 없는 변수로 인자를 나누면 한 덩어리로 들어간다.
- 원인 2: zsh는 따옴표 없는 변수를 단어로 나누지 않는다.
- 대응 2: 이런 스크립트는 `bash <파일>`이나 `bash -c`로 돌린다.

### NIM 무료 키는 간헐적으로 HTTP 500을 낸다

- 대응: 모델 호출 클라이언트의 자동 재시도는 끄고 5xx는 코드가 명시적으로 재전송한다. 요청당 재전송 상한과, 인프라 실패로 끝난 실행을 다시 돌리는 조건은 따로 정해져 있다. 재전송과 재실행을 섞지 않는다.
- 정본: `docs/plan/DEV_PLAN.md` §3.5, `docs/eval/RULEBOOK.md` B5, `docs/plan/ROADMAP.md` §4.2

## OpenShell 위반 시험

### 거부된 요청이 성공처럼 보이거나, 성공한 차단이 증거가 안 된다

- `curl`은 `--fail` 없이 쓰면 프록시가 403으로 거부해도 종료 코드 0으로 끝날 수 있다. HTTP 상태 코드를 함께 기록하고 403이면 0이 아닌 값으로 끝나게 한다.
- `No such file`(ENOENT)은 파일이 샌드박스에 들어오지 않았다는 뜻일 뿐 정책 차단 증거가 아니다. 정답 경로 차단은 허용 목록 밖에 둔 미끼 파일을 읽어 `Permission denied`(EACCES)를 받아야 증거가 된다.
- 허용된 실행 파일이 띄운 프로세스는 그 허가를 물려받는다. 네트워크 위반 시험은 `openshell sandbox exec`로 허용 실행 파일의 자손이 아닌 프로세스에서 시작한다.
- 정본: `docs/plan/DEV_PLAN.md` §4.4

## 저장소 작업

### squash 병합한 브랜치는 `main`의 조상으로 잡히지 않는다

- 증상: PR을 squash 병합한 뒤 `git merge-base --is-ancestor <브랜치> main`이 실패하고, `git branch -d <브랜치>`가 "not fully merged"로 거부한다.
- 원인: squash 병합은 `main`에 새 커밋 하나를 만들 뿐 브랜치의 커밋을 `main` 이력에 넣지 않는다. 이 저장소의 병합 방식은 squash다.
- 대응: 브랜치와 worktree(작업 복사본)를 지우기 전에 내용이 같은지 본다. `git diff --quiet origin/main <브랜치> -- <그 PR이 바꾼 파일들>`이 종료 코드 0이면 `git worktree remove <경로>`, `git branch -D <브랜치>` 순서로 지운다. 0이 아니면 지우지 않고 차이를 확인한다.

### Codex 실행이 끝나지 않거나 키를 물려받는다

- macOS에는 `timeout` 명령이 없다. Codex는 백그라운드로 돌리고 감시 프로세스로 제한 시간을 걸며, 판정은 `-o` 파일로 받는다.
- 셸에 내보낸 환경변수는 Codex에 그대로 넘어간다. `env -u NVIDIA_API_KEY -u DATA_GO_KR_SERVICE_KEY -u TRADESENTRY_SEALED_DIR`로 빼고 실행한다.
- 정본: `docs/rules/AGENT_OPS.md` §2.2·§2.4
