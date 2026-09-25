# AS4: 조립 점검 결과 — 합침 후보 판정 확정, 복사된 계약 상수 고정 시험, 조립 부산물 확인

조립 작업 AS4(조립 점검: `docs/plan/UNITS.md` §5의 여섯 단계로 버릴 것과 합칠 것을 확정하는 작업)의 결과다. MVP 시험(로드맵 V1) 직전이라 동작을 바꾸지 않는 정리만 했다. 판단이 필요한 합치기·코드 옮기기는 아래 "후보로 남긴 것"에 적었다.

용어

- 조립체: CLI(명령줄 실행 도구 `tradesentry <명령>`) 명령 하나나 진입점 하나가 도는 단위 묶음(`docs/plan/UNITS.md` §4).
- 합침 기준: 같은 입력을 받고, 같은 명령 묶음 안에서만 불리며, 소비자(그 단위를 import해 부르는 다른 단위)가 하나다(`docs/plan/UNITS.md` §6).
- 동결 경로: `RB-1`(평가 룰북의 첫 동결 버전) 전에 끝내야 하는 판정 정책(P1~P5)·검증기(R3·R4) 단위. 이 단위들의 합치기는 AS4에서만 한다.
- 실행 커버리지: MVP 명령을 실제로 돌렸을 때 단위마다 함수가 한 번이라도 불렸는지.
- 복사된 계약 상수: 상태값·키 목록 같은 자료 계약 값을 계약 커널(단위 K1, `src/tradesentry/contract/types.py`) 대신 단위 파일 안에 따로 적어 둔 것(`docs/plan/UNITS.md` §6 조립 부산물 4).
- 가짜 모델: 정해 둔 답을 차례로 돌려주는 시험용 전송 자리. 실제 NIM(NVIDIA 클라우드 추론 API)을 부르지 않는다.
- 호스트 백엔드: `evaluate`가 사례를 샌드박스 대신 같은 프로세스에서 돌리는 시험용 실행 방식(AS3 결정 기록 `20260925-0935-model-decision-as3-evaluate.md`).

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 12:40(기록 시각). 바탕은 `main` 6530b1c(DOCS2 #43·AS3 #45·DT7 #44 병합 뒤) |
| 제목 | 조립 점검 여섯 단계 결과, 합침 후보 10개의 판정 확정(유지 9, 합침 후보 유지 1), 버린 것·합친 것 없음, 복사된 계약 상수 54개의 K1 값 일치 시험, 조립 부산물 여섯 가지 확인 |
| 결정 | 아래 "결정 내용" ①~⑥ |
| 이유와 근거 | 항목마다 적었다 |
| 검토한 대안 | 아래 "검토한 대안" |
| 결정 주체 | 오케스트레이터(작업을 나누고 PR(GitHub 변경 요청)을 병합하는 주관 에이전트) 주관, 영역 공동 |
| 공용 약속 여부 | 아니다. 코드 동작, 계약 값, 이름·경로·명령을 바꾸지 않았다. 더한 것은 시험 파일 하나, 이 기록, 색인 한 줄, 단위 표 판정 열이다 |
| 영향 | 아래 "영향과 넘길 곳" |
| 관련 PR | AS4(브랜치 `common/AS4-assembly-check`) |

## 결정 내용

① **실행 커버리지 확인 방법** `[DESIGN]`

- 파이썬 `sys.setprofile`·`threading.setprofile`로 함수 호출 사건을 받아, 등록부(`src/tradesentry/units/registry.py`)의 단위 파일 안에서 모듈 본문·클래스 본문이 아닌 함수가 불렸는지 명령 단계별로 셌다. import만 된 단위(예: I8)와 실제로 불린 단위를 가른다.
- 네트워크 연결은 막았다. 실제 NIM·openshell·nemoclaw는 부르지 않았다.
- 돌린 명령(모두 in-process로 `tradesentry.cli.dispatch.main` 또는 해당 모듈의 `main`을 불렀다):

| 단계 | 명령 | 자료 | 종료 코드 |
|---|---|---|---|
| `snapshot_verify` | `tradesentry snapshot-verify --snapshot <id>` | `controlled_fixture_v0`, `dev20` | 0, 0 |
| `detect_fixture` | `tradesentry detect --snapshot controlled_fixture_v0 --policy dev-0.1` | 합성 | 0(사례 3건) |
| `detect_dev20` | `tradesentry detect --snapshot dev20 --policy dev-0.1` | 합성 | 0(사례 20건) |
| `detect_real_dev` | `tradesentry detect --snapshot kcs_202201_202412_v2 --policy policy_v1` | 실자료 `real_dev`(정본 빌드를 읽기만 함) | 0(경보 221건, DT7 ①과 같음) |
| `run_case_checklist` | `tradesentry run-case --mode checklist` 사례 A·B·C | 합성 | 0, 0, 0 |
| `run_case_model` | `tradesentry run-case --mode agent·full·freeform` 사례 A·B·C | 합성, 가짜 모델(AS2 조립 시험의 답 목록) | 9회 모두 0, 준비한 답을 모두 씀 |
| `evaluate_dev20` | `tradesentry evaluate --snapshot dev20 --policy dev-0.1` | dev20, 호스트 백엔드, 모델 모드는 HTTP 400 가짜(AS3 조립 시험과 같음) | 0(60줄: checklist 20 `COMPLETED`, agent·full 40 `FAILED`) |
| `scorer` | `python -m eval.scorer --run <evaluate 묶음 폴더>`의 `main` | 위 묶음 | 0 |
| `extract` | `python -m tradesentry.evaluation.extract --run <evaluate 묶음 폴더>`의 `main` | 위 묶음 | 0 |

- 실자료 정본 빌드(`data/snapshots/kcs_202201_202412_v2/snapshot_build.sqlite`)의 sha256은 실행 앞뒤가 같았다 `[사실]`. 실자료는 `detect`로만 읽었고 `run-case`·`evaluate`에는 쓰지 않았다. `real_sealed` 계열로 경보를 뽑지 않았다(`detect`가 `real_dev`로 좁힌다, AS1 결정 기록 `20260925-0901-model-decision-as1-real-dev.md`).
- 한계: `evaluate`의 모델 모드는 HTTP 400에서 멈추므로 I10(조사자)·I11(Critic)의 깊은 경로는 `run_case_model` 단계가 보인다. 이 방법은 불렸는지만 보고 분기별 커버리지는 보지 않는다 `[사실]`.

② **단계별 결과(커버리지 표)** `[사실]`

O는 그 단계에서 함수가 불림, -는 불리지 않음이다. 런타임 밖 단위(S1·S4·V2·V4·V5)는 이 단계에서 세지 않는다(§5 2단계). S1은 S3가 수집기 함수를 불러 O가 나왔다.

| 단위 | snapshot_verify | detect(합성 둘·real_dev) | run-case checklist | run-case 모델 모드 | evaluate | 채점기 | extract |
|---|---|---|---|---|---|---|---|
| S2·S3 | O | - | - | - | - | - | - |
| K1 | - | import만 | O | O | O | - | - |
| K2·K3·K4 | - | O | O | O | O | - | - |
| K5 | - | - | O | O | O | - | - |
| X1·X2·X4·P1·P2·P5 | - | O | O | O | O | - | - |
| X3·P3·P4·R1~R4·I1~I7·I12·I13·L1·L2 | - | - | O | O | O | - | - |
| I10 | - | - | - | O | O | - | - |
| I11 | - | - | - | O | - | - | - |
| L3 | - | - | - | - | O(실패 경로) | - | O |
| E1·E4 | - | - | - | - | O | - | - |
| E3 | - | - | - | - | - | - | O |
| C1~C4 | - | - | - | - | - | O | - |
| F1·F2 | O | O | O | O | O | - | - |
| I8 | - | - | - | - | - | - | - |
| G1·G2·E2, 승인 `approval_record`·화면 `app` | - | - | - | - | - | - | - |

- I8(기록 재생)은 I10·I11·I12가 import하고 I12가 예외 형식(`ReplayMismatch`)을 잡지만, MVP 명령에서 함수는 불리지 않는다. I10·I11·I12의 진입 함수 `run`(골든·키 없는 기록 재생 시험)이 쓴다.
- 불리지 않은 런타임 단위의 처리는 ③이다.

③ **판정 확정(3·4단계)** `[사실: 정적 import 그래프에서 시험 모듈을 뺀 소비자 수]`

| 단위 | 판정 후보 | AS4 판정 | 이유 |
|---|---|---|---|
| K2 | 합침 후보(→ K1) | 유지 | 소비자가 K3·K5·I1·I5 넷이다 |
| K4 | 합침 후보(→ K1) | 유지 | 소비자가 S2·S3·V2·I1·F2 다섯이다. 스냅샷 빌드·검증·`detect`·`run-case`·`evaluate`에서 불린다 |
| K5 | 합침 후보(→ K1) | 유지 | 소비자가 I1·I5 둘이다 |
| P2(동결 경로) | 합침 후보(→ P1) | 유지 | 입력이 P1과 다르다(P1 출력 + 출처 종류·묶음 배정). 봉인 묶음 제한의 마지막 방어선이라는 책임이 따로 있다(AS1 관찰) |
| P4(동결 경로) | 합침 후보(→ P3) | 유지 | 입력이 P3과 다르다(신호별 판정만). P4는 네 모드 모두, P3은 `checklist`에서만 불린다(AS2 관찰) |
| R4(동결 경로) | 합침 후보(→ R3) | 유지 | 입력이 R3과 다르다(findings + 모드 + 수정 사용 여부)(AS2 관찰) |
| I8 | 합침 후보(→ I7) | 유지(시험 전용) | 소비자가 I10·I11·I12 셋이고 입력(trace 레코드)이 I7(메시지)과 다르다. 버리면 I10~I12 골든이 깨진다. 기록 재생은 개발 플랜의 `workflow/` 책임에 들어 있다(`docs/plan/DEV_PLAN.md` 패키지 표) |
| L2 | 합침 후보(→ L1) | 유지 | 소비자가 I12·E1·E3 셋이다 |
| L3 | 합침 후보(→ L1) | 유지 | 소비자가 I7·I12·L2·E1·E3·F2 여섯이다. `evaluate` 실패 경로와 `extract`에서 불린다 |
| F1 | 합침 후보(→ F2) | 합침 후보 유지 | 합침 기준 세 가지를 모두 채운다(같은 입력인 문자열 인자, CLI 명령에서만 불림, 소비자 F2 하나). 합치면 단위 파일이 바뀌어 단위 표 변경(사용자 승인, `docs/plan/UNITS.md` 머리 "바꾸는 법")이고, MVP 직전 CLI 경로를 옮기는 위험이 있어 이번에는 합치지 않았다 |
| 화면 `app` | 버림 후보 | 버림 후보 그대로 | 불리지 않는다(U1 전 뼈대). 로드맵 §5 줄이는 순서가 발동하지 않았으므로 버리지 않는다 |

- 동결 경로 단위(P1~P5, R3·R4)는 합친 것이 없다. 합침 기준을 채우는 쌍이 없어서다. 그래서 MVP 뒤에 동결 경로 단위를 합칠 일도 남지 않는다.
- 불리지 않은 런타임 단위는 모두 버리지 않는다(`docs/plan/UNITS.md` §6 "버림"은 고정 규칙이 요구하지 않는 것만):
  - G1: 채점 대체 기본값 `g0` 고정 규칙(자료 계약 §4.2). 비교국은 미리 계산한 `peer_group` 행을 K3로 읽는다.
  - G2: `g1`(유사도 그룹핑)은 로드맵 §5 "끝까지 지키는 것"이고 MT6 두 번째 PR이 구현한다.
  - 모의 승인 `approval_record`: 로드맵 AP1(2026-09-26~27)이 구현할 뼈대다. 줄이는 순서 1번 대상이지만 발동하지 않았다.
  - E2: 봉인 묶음(F2)의 샌드박스 밖 실행기다. F1 뒤 구현이다.
- 새 합칠 후보(단위 표에 없던 것, 판정은 ⑥의 후보):
  - `parent`·`world` 월 값 변환이 단위 F2(AS1 어댑터)와 단위 I1(도구 공통 틀) 두 곳에 있다(AS1·AS2 관찰).
  - 실행명 확보 규칙이 공통 실행기(`tradesentry.units`), CLI(`reserve_run_dir`), 단위 L2 세 곳에 있다(MT5 CLI 결정 기록 `20260924-2356-orchestrator-decision-mt5-cli.md`).
- 고정 규칙 충돌(4단계): 판정을 바꾼 단위 가운데 동결 경로(P2·P4·R4)는 유지로 되돌렸고, `g0`(G1), 자문 명세서(`docs/plan/SCAFFOLD_BRIEF.md`) §5.1 고정 사항 5의 NAT 네 역할(I13·E4), 줄이는 순서(`approval_record`·`app`)에 걸리는 단위는 모두 유지나 기존 판정 그대로다.

④ **복사된 계약 상수: 값 일치 시험으로 고정하고, import 교체는 후보로 남김** `[사실]`

- 계약 상수 사본 54개(P5·P3·P4·R1·R3·L1·L2·L3·X4·I10·I12·G1·F2)가 K1 값과 종류·순서까지 같음을 새 시험 `tests/test_contract_copies.py`가 확인한다. 모양이 다른 사본(X4의 `frozenset`, P5의 신호 계열 목록을 둘로 나눈 것, P3·F2의 빠진 관측 셋)은 K1 값에서 같은 모양을 만들어 비교한다. 채점기 사본은 보지 않는다(채점기 독립, `docs/plan/UNITS.md` §2).
- 일부러 틀린 항목 하나를 넣으면 이 시험이 실패함을 확인했다(실패 1건).
- K1 import로 바꾸지 않은 까닭:
  - P3·P5·R3은 동결 경로라 코드를 고치면 Codex(OpenAI의 코딩 에이전트 CLI) 교차 검토 대상이다.
  - 모델 트랙 단위와 데이터 트랙 단위(X4)가 섞여 트랙별 PR로 나눠야 한다(병렬 개발 규칙 §1.3).
  - X4(`metrics/rounding.py`)·K1은 같은 시각에 계약 버전 v2 PR(`data/schema-v2`)이 고친다.
  - MVP 시험이 이 PR 병합을 기다린다.
- 값이 같으므로 지금 동작 차이는 없다. 교체 PR은 이 시험이 통과한 상태에서 바꾸고, 바꾼 뒤에도 통과해야 한다. 계약 값이 바뀌면(예: 계약 버전) 사본을 함께 고치지 않은 곳이 이 시험에서 드러난다.

⑤ **조립 부산물 버림 목록 확인(`docs/plan/UNITS.md` §6)** `[사실: 저장소 검색]`

| # | 부산물 | 결과 | 한 일 |
|---|---|---|---|
| 1 | 공통 실행기의 제품 노출 | CLI(`src/tradesentry/cli/`), 런타임 스킬(`skills/tradesentry/SKILL.md`), 샌드박스 정책·이미지(`configs/openshell/`), NAT 설정(`configs/nat/`)에서 `tradesentry.units`를 부르지 않는다. 비시험 모듈 가운데 `tradesentry.units`를 import하는 것은 0이다(경계 시험 5번). `src/tradesentry/grouping/g0.py` 머리 설명에 `g0` 결과 파일을 만드는 개발 명령으로 공통 실행기가 적혀 있다(런타임 경로가 아니다) | 없음 |
| 2 | 시험 밖 임시 대역 | `src/`·`eval/scorer/`·`eval/datagen/`·`configs/model/`·`configs/nat/`에 대역(stub)이 없다. 시험이 바꿔 끼우는 자리(`dispatch.run_case_transport`, `EVALUATE_BACKEND` 등)는 설계된 주입 자리이고 대역이 아니다 | 없음 |
| 3 | 단위 사이 중간 파일 | ①의 실행에서 생긴 출력 파일은 도메인 출력뿐이다: `policy_case_build`, `runlog_trace`, `runlog_run_record`, `reports_render_ko`, `workflow_nat_wrap`, `evaluation_batch_run`, `evaluation_extract`, `scorer_results`·`scorer_claims`·`scorer_summary`, `snapshot_verify`와 실행 조건 입력 파일 `run_conditions`(MT7 결정 기록의 임시 형식, 결정 D6) | 없음 |
| 4 | 복사된 계약 상수 | ④ | 값 일치 시험을 더함 |
| 5 | `spikes/x1/` 흔적 | `src/`에 X1 임시 코드가 없다. `configs/openshell/`의 세 파일은 출발점(provenance) 주석으로 `spikes/x1/`의 파일을 가리키고, `provider_profile.yaml`의 등록 명령 주석은 키 래퍼 `spikes/x1/with_nvidia_key.py`를 쓴다(오케스트레이터가 호스트에서 돌리는 명령) | 없음. 래퍼 위치는 ⑥의 후보 |
| 6 | `inference.local` 경로 | 앱 코드와 설정에 `inference.local`을 쓰는 경로가 없다. 위반 시험(단위 F7 `scripts/openshell_violation_tests.py`의 `inference_local` 검사 행 둘)은 `inference.local`에 닿지 않아야 한다는 차단 확인이라 남긴다 | 없음 |

⑥ **후보로 남긴 것(이 PR에서 하지 않음)**

| 후보 | 까닭 | 넘길 곳 |
|---|---|---|
| F1 → F2 합침 | 기준 충족. 단위 표 변경(사용자 승인)이고 MVP 직전 CLI 경로 변경 | MVP 뒤 사용자 승인 |
| 복사된 계약 상수 → K1 import(P3·P5·R3은 동결 경로, R1·L2·L3·I10·I12·G1·F2는 모델 트랙, X4는 데이터 트랙) | ④ | 계약 v2 PR 병합 뒤 트랙별 정리 PR. 동결 경로 셋은 `RB-1` 전 Codex 검토와 함께 |
| X4 관측 상태 상수를 K1 정의로 합치기(DT2 결정 기록 `20260925-0035-data-decision-dt2-metrics.md` ⑪) | 위와 같음. X4는 계약 v2 PR이 고치는 파일 | 데이터 트랙 정리 PR |
| P5 `claim_families`의 `@` 뒤 검사를 "10자리 숫자이고 사례 HS6로 시작"으로 좁혀 P5·R3을 하나로(MT1 결정 기록 `20260925-0025-model-decision-mt1-policy.md`) | 동작이 바뀐다(검증 규칙을 좁힘). 이 작업의 금지(판정 정책·검증기 동작 불변)에 걸린다 | `RB-1` 전 동결 경로 추가 수정 PR(판정 정책·검증기, Codex 검토) |
| P3 머리 설명에 점유율 분모 경로(`denominator_below_partner`)를 MT1 결정 ⑪의 예외로 적기(AS2 결정 기록 ⑦) | 설명 문장만이지만 동결 경로 파일이다 | 위 동결 경로 추가 수정 PR |
| `parent`·`world` 변환을 한 곳(F2 또는 I1)으로 모으기 | 단위 사이 코드 옮기기(단위 표 변경). AS2가 다섯 사례에서 두 경로의 정확값이 같음을 확인했다 | MVP 뒤 사용자 승인 |
| 실행명 확보 규칙 세 곳(공통 실행기·CLI·L2)을 하나로 | 공통 실행기는 개발 전용이고 CLI는 `tradesentry.units`를 import할 수 없다(경계 시험 5번). L2로 모으면 F2의 허용 import와 두 트랙 파일이 바뀐다 | MVP 뒤 |
| G1의 열 목록 사본 → K1, 부모 행 조회 → K3(MT6 결정 기록 `20260925-0049-model-decision-mt6-g0.md` ③) | 열 목록은 K1과 같음을 ④ 시험이 확인한다. G1은 런타임에 불리지 않고, 다시 돌리면 `g0` 결과 파일의 `generated_at`이 바뀐다 | `g1` PR(MT6 두 번째 PR) |
| 머리 주석의 쓰지 않는 허용 import 좁히기(예: P1~P4의 `tradesentry.dal`·`tradesentry.metrics`, R3의 `tradesentry.dal`·`tradesentry.policy`) | 넓은 허용은 위반이 아니다. 좁히면 동결 경로 파일을 고친다 | 각 트랙 정리 PR |
| 키 래퍼 `spikes/x1/with_nvidia_key.py`를 `scripts/`로 옮기기 | 키를 다루는 도구라 보안 검토 대상이고, 등록 명령은 오케스트레이터만 돈다 | MT5 후속(보안 검토) |
| 실행 조건 입력 파일 이름 `run_conditions`를 단위 표·자료 계약 §10.3의 이름 규칙에 올리기 | 이름·형식은 F1 전 확정 항목(MT7 결정 기록, 결정 D6) | MT7 다음 PR |

## 조립 점검 여섯 단계 결과

| 단계 | 결과 | 명령과 종료 코드 |
|---|---|---|
| 1. 정적 import 그래프 | 등록부의 단위 54개 모두 머리 주석의 허용 import 안(허용 밖 0), 저장소 모듈 순환 0, 채점기 닫힘이 `tradesentry`·`eval.datagen`에 닿는 곳 0, 비시험 모듈의 `tradesentry.units` import 0 `[사실: 경계 시험 도우미(tests/test_boundaries.py의 repo_modules·import_targets·find_cycles·reach)로 뽑은 단위별 표]` | `env -u NVIDIA_API_KEY -u DATA_GO_KR_SERVICE_KEY -u TRADESENTRY_SEALED_DIR uv run --locked python -m unittest discover -s tests -p "test_boundaries.py"` → 0(Ran 34) |
| 2. MVP 실행 커버리지 | ①·② | ①의 표: 모든 명령 종료 코드 0 |
| 3. 합칠 쌍 찾기 | ③: 합침 후보 10개 중 9개 유지로 되돌림, F1은 합침 후보 유지, 새 후보 둘 | 정적 그래프의 소비자 수 |
| 4. 고정 규칙 충돌 | ③ 끝 문단. 사용자 승인으로 올릴 것은 F1 합침과 새 후보 둘(MVP 뒤) | — |
| 5. 동작 불변 | 코드 동작을 바꾸지 않았다(더한 것은 시험 파일 하나). 모든 골든과 경계 시험, 조립 시험(F2의 `detect`·`run-case`·`evaluate`·채점기 시험)이 종료 코드 0이다. 출력 파일의 도메인명은 단위 표 그대로다(⑤의 3번, N4) | 단위별 `env -u … uv run --locked python -m unittest discover -s tests/units/<ID> -t tests` 54개 모두 0(건너뜀은 뼈대 단위 `approval_record`·`app`·E2·G2의 골든과 진입 함수가 없는 K1·S1의 골든 각 1). 전체 `env -u … uv run --locked python -m unittest discover -s tests -v` → 0 |
| 6. 결정 기록 | 이 기록, 색인 한 줄, `docs/plan/UNITS.md` §3 판정 열과 판정 집계 | — |

## 검토한 대안

- 복사된 계약 상수를 이 PR에서 K1 import로 바꾸기: 값이 같아 동작 차이는 없지만, 동결 경로 세 단위(Codex 검토), 두 트랙에 걸친 파일(트랙별 PR), 계약 v2 PR과 겹치는 파일(X4)이 한 PR에 모인다. MVP 시험이 이 PR을 기다려 값 일치 시험만 두었다.
- I8을 버림으로 판정: MVP 명령에서 불리지 않지만 I10~I12의 진입 함수와 골든이 쓰고, 키 없는 기록 재생 시험은 개발 플랜의 `workflow/` 책임이다. 버리면 시험이 깨지므로 버리지 않았다.
- 불리지 않은 뼈대 단위(`approval_record`·E2·G2)를 버림 후보로 올리기: 각각 뒤의 작업(AP1·F2·MT6 `g1`)이 구현할 자리이고, 고정 규칙(`g1` 끝까지 지키기, 봉인 묶음 실행)이나 줄이는 순서가 따로 정한다. 버림 기준("고정 규칙이 요구하지 않는다")에 맞지 않는다.
- 커버리지를 기존 시험 커버리지 도구로 재기: 저장소 lock에 커버리지 패키지가 없어 의존성을 늘려야 한다. 표준 라이브러리의 호출 감시로 대신했다.

## 영향과 넘길 곳

- 파일: `tests/test_contract_copies.py`(새 시험), 이 기록, `docs/tracking/decisions/index.md` 한 줄, `docs/plan/UNITS.md` §3 판정 열과 판정 집계 한 줄.
- 계약 v2 PR(`data/schema-v2`)·AS3 후속 PR(`model/AS3-2-real-dev`): 이 PR은 그 두 PR이 고치는 파일을 고치지 않았다. 둘이 병합되면 이 PR이 `main`을 따라가 1·2·5단계를 다시 확인한다. 계약 v2가 K1과 X4의 `SCHEMA_VERSION`을 함께 2로 올리면 ④ 시험은 그대로 통과한다.
- MVP 시험(로드맵 V1): ⑥의 후보는 V1 범위 밖이다. `evaluate`의 모델 모드는 이 점검에서 가짜 모델로만 돌렸다.
- `RB-1` 전 동결 경로 추가 수정 PR: ⑥의 P5·R3 `@` 검사 통일, P3 머리 설명, 동결 경로 셋의 상수 import 교체.
