# MT7 평가 하네스 첫 PR의 해석과 약속

MT7(평가 하네스, 모델 트랙) 첫 PR(단위 E1·E3·E4와 `tradesentry evaluate` 배선)에서 자료 계약·룰북·평가 스킬 ②가 정하지 않았거나 모델 트랙(M)에 맡긴 세부를 적는다. 샌드박스 밖 실행기(단위 E2)와 봉인 흉내 리허설은 다음 PR이다(아래 "다음 PR"). 항목마다 **확정** 또는 **잠정**을 붙였다.

용어

- 평가 하네스: 사례 여러 건을 모드별로 돌리고 실행 기록을 모으는 프로그램(단위 E1~E4).
- 묶음 실행: 여러 사례 실행을 한 번에 돌리는 평가 실행(`tradesentry evaluate`, 실행명 `evaluate-{시각}`).
- 사례 실행 함수: 묶음이 사례 1건 × 모드 하나를 돌리려고 부르는 함수. 실제로는 `run-case` 처리 함수와 같은 조립(로드맵 AS2)이 준다.
- 교차 배치: (사례 × 모드) 실행 목록을 고정 난수로 섞어 한 모드가 특정 시간대에 몰리지 않게 하는 순서(룰북 B5).
- 순서 seed: 교차 배치 순서를 다시 똑같이 만들기 위한 시작값.
- 실행 조건 입력 파일: 채점기가 모르는 실행 조건(순서 seed, 동시성, 한도, NAT 프로파일 요약 등)을 호스트 쪽 프로그램이 채점기에 넘기는 파일(자료 계약 §8.2).
- 인프라 실패 재실행: 모델 제공자 쪽 오류로 `FAILED`가 된 실행을 같은 설정으로 한 번 다시 돌리는 일(룰북 B5).
- NAT 프로파일: NAT(NVIDIA NeMo Agent Toolkit)가 사례 실행마다 남기는 토큰·지연 측정 파일(단위 I13이 쓴다).
- 조립 AS2·AS3: 사례 조사 조립(`run-case`), 평가 실행·채점 연결(`evaluate`와 채점기).

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 06:00(기록 시각) |
| 제목 | MT7 첫 PR: 교차 배치 순서 규칙, 묶음 실행과 사례 실행 함수의 모양, 하네스 실패 줄, 실행 조건 입력 파일 임시 형식, 추출 명령 출력, NAT 사후 평가 지표, `evaluate` 배선 |
| 결정 | 아래 "결정 내용" ①~⑩ |
| 이유와 근거 | 아래 "결정 내용"의 항목마다 적었다 |
| 검토한 대안 | 아래 "검토한 대안" |
| 결정 주체 | 소유 트랙(M). ⑤의 형식 확정은 로드맵 MT7·DT8이 F1 전에 함께 한다(결정 D6). ⑩의 모드 목록 방식과 사례 목록 자리는 조립 AS3이 새 결정으로 정한다 |
| 공용 약속 여부 | 계약 필드·상태값·키·기준값·한도 값과 명령 표(`args.COMMAND_OPTIONS`)를 바꾸지 않았다. ⑤는 채점기 DT8의 임시 형식을 그대로 썼다. ①의 개발 묶음 seed 값과 ⑩의 스냅샷 → 자료 묶음 대응은 M 소유 배선의 해석이다. 봉인 묶음 seed는 `RB-1`과 함께 동결하는 값이라 여기서 정하지 않았다 |
| 영향 | 아래 "영향과 넘길 곳" |
| 관련 PR | 로드맵 MT7 첫 PR(브랜치 `model/MT7-harness`) |

## 결정 내용

① **교차 배치 순서 규칙** — 확정

- (사례, 모드)마다 열쇠 = `sha256(UTF-8 바이트 "{seed}\n{case_id}\n{mode}")`의 16진수 소문자 64자이고, 열쇠 → `case_id` → `mode` 순으로 오름차순 정렬한다(`batch_run.order_key`·`plan_order`).
- 이유: 샌드박스 밖 실행기 E2는 경계 시험 규칙상 E1을 import할 수 없으므로 같은 순서를 따로 만들어야 한다. 파이썬 `random`의 섞기 알고리즘에 기대지 않고 바이트 수준으로 고정했다. 시험(`tests/units/E1/test_batch_run.py` `test_key_is_sha256_of_seed_case_mode_bytes`)이 이 식을 직접 다시 계산해 대조한다.
- 개발 묶음(`evaluate`)의 seed는 `dev-order-v1`(`dispatch.DEV_ORDER_SEED`)이다. 실행 조건 입력 파일 `order_seed`로 요약에 들어간다. 봉인 묶음 seed는 `RB-1`과 함께 동결한다(룰북 B5). 이 PR은 정하지 않는다.
- 동시성은 1이다(룰북 B5). 올리는 방법은 두지 않았다.

② **묶음 실행과 사례 실행 함수의 모양** — 확정(사례 실행 함수의 실제 구현은 AS2)

- 진입 함수 `run`은 순서 계획만 낸다(입력 `case_ids`·`modes`·`order_seed`, 출력 `order`·`concurrency`). 순수 함수라 골든 쌍의 대상이다.
- `execute_batch(spec, runner, parent, other_parent)`: 묶음 폴더 `outputs/evaluate-{시각}/`를 확보한 뒤, 순서대로 사례마다 새 실행명 `run_case-{시각}`을 확보하고(자료 계약 §10.3 N8, 단위 L2 `reserve_run_dir`) 사례 실행 함수를 부른다.
- 사례 실행 함수는 `CaseCall`(실행명, 시각, 확보한 빈 사례 실행 폴더, 사례 네 키, 모드, 자료 묶음, 버전 키 5개)을 받아 실행 쪽 키 21개의 객체를 돌려준다. 출력 파일은 그 폴더 안에 받은 시각으로 쓴다(N6).
- 사례 실행 폴더는 묶음 폴더의 형제(`outputs/run_case-{시각}/`)다. S0 제안과 같고, 채점기가 `<run_dir>`의 부모에서 `run_id` 이름의 폴더를 여는 방식(DT8 결정 ④)과 맞다. 사례 실행의 실행 이름은 CLI 명령 이름 규칙(N5)대로 `run_case`다.
- 묶음 기록 `evaluation_batch_run-{시각}.jsonl`은 이미 있으면 실패하는 방식(`"x"`)으로 한 번 열고, 사례마다 한 줄을 쓰고 비운다(flush). 도중에 멈추면 끝난 줄만 남고, 줄이 없는 계획 조합은 채점기가 미실행으로 분모에 실패로 센다(자료 계약 §8.2).
- 사례 실행명을 10번 시도해도 확보하지 못하면 거기서 멈춘다(남은 조합은 미실행으로 분모에 남는다).

③ **하네스가 남기는 실패 줄** — 잠정(F1 전 확정)

- 사례 실행 함수가 예외를 내거나, 돌려준 기록이 단위 L2 `build_record` 검사를 통과하지 못하거나, 실행 전에 정해지는 키(실행명·사례·자료 묶음·모드·버전 키 5개)가 묶음이 준 값과 다르면 그 사례를 `FAILED` 줄로 남긴다. 원인은 단위 L3 `CODE_ERROR` 한 항목이고, `detail`은 `harness:` 뒤에 예외 이름(`harness:RuntimeError`)이나 사유 이름(`harness:invalid_record`, `harness:record_mismatch`)뿐이다(N13).
- 수 키는 하네스가 모르므로 0이고, `wall_ms`만 하네스가 잰 값이다. `CODE_ERROR`라 인프라 실패 재실행 대상이 아니다.
- 잠정인 까닭: 모르는 수를 0으로 적으면 비용 중앙값이 낮게 보일 수 있다. 채점기는 `COMPLETED`가 아닌 줄의 수 키가 `null`이어도 받지만, 단위 L2 `build_record`가 정수만 받아 0으로 두었다. F1 전에 `null`로 바꿀지 평가 방법론 검토와 정한다.

④ **묶음 안에서는 한 번만 돈다** — 확정(이 PR)

- 인프라 실패 재실행은 E1이 묶음 안에서 하지 않는다. 재실행 대상 목록은 단위 E3이 만들고(⑥), 재실행을 원래 실행과 잇는 방법(같은 묶음 기록에 줄을 더할지, 새 묶음으로 돌릴지)은 다음 PR에서 정한다. 채점기(DT8 3회차)는 같은 (사례, 모드)에 "`FAILED` 한 줄 뒤 재실행 한 줄"만 받는다. 잇는 방법은 이 모양에 맞춘다.

⑤ **실행 조건 입력 파일 — 임시 형식** — 잠정(결정 D6: MVP 전 임시로 정해 쓰고 F1 전에 확정)

| 항목 | 임시로 정한 것 |
|---|---|
| 이름·위치 | `<run_dir>/run_conditions-{시각}.json`. `{시각}`은 `<run_dir>` 실행명의 시각(N6). 채점기 DT8 1회차 보고 §5와 같다 |
| 만드는 주체 | 내려받기를 끝낸 호스트 쪽 프로그램. 개발 묶음을 호스트에서 돌리는 `evaluate`는 스스로 쓴다(⑩). 샌드박스 안에서 돌리는 경로는 샌드박스가 쓰지 않고 내려받은 프로그램이 쓴다(자료 계약 §8.2) |
| 쓰는 방법 | `batch_run.write_run_conditions`. 이미 있으면 실패(`O_EXCL`). 봉인 묶음은 `outputs/sealed/` 아래, 개발 묶음은 `outputs/` 아래 실행 폴더에만 쓴다 |
| 형식 | JSON 객체 한 줄. 수는 JSON 수(Decimal은 원문 표기)다 |
| 키 | 채점기 임시 형식의 키 23개(`batch_run.CONDITION_KEYS`) 안에서만. 필수 `dataset`·`planned_cases`(네 키 `case_id`·`hs6`·`partner`·`month`, `ALL` 아님)·`planned_modes`·`policy_detection_thresholds`(int·Decimal 수 목록) |
| 하네스가 채우는 값 | `order_seed`, `concurrency`(정수 1), `limits`, `run_period`(`start`·`end`, KST ISO 초 단위), `nat_profile_summary`(개발 묶음만, ⑦) |
| `limits` 대응 | 모델 설정(단위 I7 `RunLimits`)에서 `tool_attempts` → `tool_attempts`, `revision_stages` → `reinvestigation`, `model_requests` → `model_requests`, `wall_ms` ÷ 1000 → `wall_time_s`, `tokens` → `tokens`. 채점기 요약의 한도 칸 이름에 맞췄다 |
| 그 밖의 값 | 채점기 커밋, 사전 점검 결과, 샌드박스 정보, 봉인 해시 재대조 등은 `extra`로 받는다. 하네스는 모른다 |
| 거부 | 약속 밖 키, 필수 키 없음, float·문자열 임계값, 중복 사례·모드, `concurrency`가 bool, 봉인 묶음의 `nat_profile_summary`·`korean_sample_review`, 문자열(키 이름 포함)에 로컬 절대경로 모양이나 키 모양 |
| 누락 처리 | 하네스 쪽은 필수 키가 없으면 쓰지 않는다. 옮기는 값이 없을 때 요약에 "미기재"로 적는 것은 채점기 몫이다 |

- 대조 증거: 이 브랜치 커밋으로 만든 dev20 모양 묶음(가짜 사례 실행 함수, 60줄)과 실행 조건 입력 파일을 채점기 커밋 `46f85ac`와 `26d2fd2`의 `read_conditions`·`read_batch`·`validate_batch_line`(뒤 커밋은 `check_rerun_shape`까지)에 저장소 밖에서 넣어 모두 통과했다. 저장소 시험은 채점기를 import하지 않고, 키 목록을 계약 문서에서 읽어 대조한다.
- F1 전에 확정할 것: 이 넷(이름·형식·위치·누락 처리)을 DT8과 함께 확정, 봉인 묶음 필수 값(DT8 F1 전 목록 9)을 누가 채우는지, 재대조 뒤 이 파일을 만드는 호출이 E2와 같은 실행으로 남는지와 N6 예외 여부(로드맵 MT7 `[미확인]`).

⑥ **추출 명령의 출력** — 확정(명령 형식은 잠정)

- 건수 객체: 실행 상태 5개별 건수(0 포함), 원인 분류 코드별 건수(단위 L3의 11개 모두, 0 포함, 모르는 코드는 `unknown`), 인프라 실패 재실행 대상 건수, 버전 키 5개마다 서로 다른 값의 수·일치 여부·불일치 건수, 모양이 틀린 줄 수(`malformed`). 사전 점검 값을 주면 그 값과 대조하고, 주지 않으면 한 값뿐인지만 본다(불일치 건수 `null`). 사례 식별자·실행명·값 자체는 넣지 않는다.
- 재실행 대상은 단위 L3 `infra_rerun_eligible` 하나로만 가른다. 목록은 묶음 기록 줄 순서(= 첫 실행의 순서)의 `{run_id, case_id, mode}`다.
- 추출 한 번이 자기 실행 폴더 `evaluation_extract-{시각}/`(N5: 단위를 혼자 돌리면 그 도메인명)을 N8대로 확보한다. 봉인 묶음이면 `outputs/sealed/` 아래다(N10). 건수는 `evaluation_extract-{시각}.json`, 재실행 대상 목록은 `evaluation_extract-{시각}.jsonl`로 배타 생성한다.
- 명령: `python -m tradesentry.evaluation.extract --run <묶음 실행 폴더> [--expect <사전 점검 버전 값 JSON 파일>]`(저장소 루트에서). 표준 출력은 첫 줄 자기 실행 폴더 이름, 둘째 줄 건수 JSON뿐이고, 오류는 예외 이름만 적는다. 잠정인 까닭: 계획 경로·명령 표에 없는 모듈 실행 형식이다. `tradesentry` CLI 명령으로 올리려면 명령 표를 바꿔야 하므로 F1 전에 평가 스킬 ②와 함께 정한다.

⑦ **NAT 사후 평가 지표** — 확정

- 실행 기록에서: 모드별 실행 수, 모델 요청 수·토큰(입력 + 출력)·`wall_ms`의 중앙값과 범위.
- NAT 프로파일에서(사례 실행 폴더 안 `workflow_nat_wrap-{시각}/`의 `all_requests_profiler_traces.json`): 모델 요청 구간 수(`LLM_END`)와 그 시간 합, NAT가 센 토큰, 도구 구간 수(`TOOL_END`), 흐름 전체 시간(`WORKFLOW_START` → `WORKFLOW_END`), 단계별 구간 수(`SPAN_START` 이름 `basic`·`critic`·`revision`·`final`, 그 밖은 `other`). payload의 `event_type`·`name`·`event_timestamp`·`span_event_timestamp`·`usage_info.token_usage`만 읽고 `data`·`metadata`는 읽지 않는다. 나머지 네 파일(`inference_optimization.json`, `standardized_data_all.csv`, `workflow_profiling_metrics.json`, `workflow_profiling_report.txt`)은 있는지만 센다(`profile_files_complete`).
- 단계 이름이 `standardized_data_all.csv`에는 없다(`SPAN` 행의 `function_name`이 모두 `<workflow>`). 그래서 추적 JSON을 읽는다 `[사실: MT4 실측 출력 controlled_fixture_v0 사례 한 건을 구조만 확인]`. 같은 실측 폴더에서 값이 CSV·`workflow_profiling_metrics.json`과 맞았다(모델 구간 5개, 토큰 합 14,031, 흐름 12,726ms).
- 수는 int와 Decimal뿐이다(시각 차는 Decimal로 계산해 밀리초 정수로 반올림, 중앙값은 두 값 평균이면 Decimal). 정답 대조는 하지 않는다. 봉인 묶음(`outputs/sealed/` 아래)은 읽지 않는다.
- NAT 폴더 이름과 파일 이름은 단위 I13의 값을 옮겨 적었다(E4는 `workflow`를 import할 수 없다). 시험이 둘을 대조한다.

⑧ **E1은 봉인 묶음과 봉인 자리를 받지 않는다** — 확정

- 자료 묶음 `holdout40`·`real_sealed`, 부모 폴더 `outputs/sealed/`는 폴더를 만들기 전에 거부한다. 봉인 묶음은 샌드박스 밖 실행기 E2가 돌린다(자료 계약 §8.2).

⑨ **모든 모드에 같은 조건** — 확정

- 한 묶음은 자료 묶음 하나, 버전 키 5개 하나, 사례 실행 함수 하나를 모든 모드에 쓴다. 모드별로 다른 것은 사례 실행 함수 안의 처리뿐이다(룰북 B2).

⑩ **`tradesentry evaluate` 배선** — 잠정(최종 연결은 AS3)

- 명령 표는 그대로다(`--snapshot`, `--policy`, `--mode` 필수. `--mode` 한 값, 반복 거부).
- `run-case`가 자리표시이거나, 사례 실행 함수(`dispatch.EVALUATE_CASE_RUNNER`)와 버전 키 함수(`dispatch.EVALUATE_VERSIONS`)가 비어 있으면 실행 폴더를 만들기 전에 분명한 오류 문장과 종료 코드 1로 끝난다. 3은 자리표시 항목에만 쓰고, 처리 함수가 3을 돌려주면 배선 계약 위반 4가 되기 때문이다.
- 자료 묶음은 `--snapshot`으로 정한다 `[해석]`: `dev20` → `dev20`, `controlled_fixture_v0` → `controlled_fixture_v0`, `kcs_202201_202412_v2` → `real_dev`. 사례 목록은 `dev20`만 정본 자리 `eval/dev/dev20/input/cases.json`(DT5 결정 기록)에서 읽고, 파일의 `dataset`·`snapshot_id`가 요청과 같아야 한다. 다른 묶음은 자리가 없어 분명한 오류로 끝난다.
- 모드 목록은 `(--mode 값,)` 하나다. 채점기는 `dev20`·`real_dev` 묶음의 계획 모드가 룰북 B2의 모드 전부가 아니면 채점하지 않는다. 그래서 지금 배선으로는 MVP 체크리스트 5·6번의 묶음을 만들 수 없다. 모드 목록을 받는 방식은 MT5 결정 ②대로 AS3이 룰북 B5·B7 재현 명령과 함께 새 결정으로 정한다.
- 순서: E1 `execute_batch` → E4 `summarize_batch` → 실행 조건 입력 파일 배타 생성. 정책 탐지 임계값은 단위 K4 `load_policy`와 I12 `policy_thresholds`, 한도는 I7 `load_model_config`에서 얻는다. 표준 출력에는 묶음 기록과 실행 조건 입력 파일의 `outputs/`부터의 상대경로만 적는다. 사례가 실패해도 묶음 기록을 끝까지 썼으면 0이다.

## 검토한 대안

- 순서에 `random.Random(seed).shuffle`: 짧지만 E2가 같은 결과를 내려면 같은 파이썬 알고리즘에 기대야 한다. 바이트 수준 식을 골랐다.
- 묶음 안 인프라 실패 재실행(첫 실행이 끝난 뒤 대상만 한 번 더): 룰북 B5와 채점기 재실행 모양에 맞지만, 재실행을 원래 실행과 잇는 방법이 다음 PR 항목이라 이번에는 넣지 않았다(④).
- 하네스 실패 줄의 수 키를 `null`로: 채점기는 받지만 단위 L2 검사와 어긋난다. 0으로 두고 잠정으로 적었다(③).
- `evaluate`에 `--dataset`·모드 목록 옵션 더하기: 명령 표(공용 약속) 변경이라 하지 않았다(⑩).
- E4가 `standardized_data_all.csv`만 읽기: 단계 이름이 없어 단계별 구간 수를 낼 수 없다(⑦).

## 다음 PR(로드맵 MT7 "F1 전" 항목, 결정 D17과 같은 방식)

1. 단위 E2 샌드박스 밖 실행기(`sealed_runner.py`): 봉인 해시 대조 → ①의 순서 규칙을 따로 구현해 예정 실행 목록 고정 → 사례 식별자를 샌드박스 안 `run-case`에 한 건씩 → 받기 전 확인과 내려받기 → 실행 조건 입력 파일(⑤). 모드별 사례 집합 일치·seed·동시성 적용을 참·거짓과 건수로 낸다.
2. E2의 묶음 기록 도메인명과 봉인 묶음 실행 폴더의 실행 이름(자료 계약 §10.3 N5 `[미확인]`). 정하면 E3·E4·채점기 `BATCH_DOMAINS`에 한 줄씩 더한다.
3. 봉인 흉내 리허설(실제 `outputs/sealed/`에 닿지 않는 임시 위치): E2로 `dev20` 돌리기 → 내려받기 → 실행 조건 입력 파일 → 채점기 파일 세 개. 재대조 단계 흉내와 두 실행기 동시 실행 포함.
4. 인프라 실패 재실행을 원래 실행과 잇는 방법(④)과 E1·E2의 재실행 흐름.
5. 실행 조건 입력 파일 형식 확정(⑤, DT8과 함께)과 하네스 실패 줄의 수 키(③).
6. 추출 명령의 명령 형식(⑥)과 오케스트레이터가 받는 출력 모양 확정.

## 영향과 넘길 곳

- 조립 AS2: 사례 실행 함수는 `batch_run.CaseCall`을 받아 받은 폴더(`call.run_dir`)에 받은 시각(`call.stamp`)으로 trace·NAT 프로파일·보고서를 쓰고, 실행 쪽 키 21개를 돌려준다. 실행명은 묶음이 확보했으므로 사례 실행 함수가 다시 확보하지 않는다. `run-case` CLI 처리 함수는 자기 실행명을 확보한 뒤 같은 함수를 부르면 된다.
- 조립 AS3: `dispatch.EVALUATE_CASE_RUNNER`·`EVALUATE_VERSIONS`를 채운다(버전 키 5개: `rulebook_version`, `grouping_version`, `code_version`의 출처 포함). ⑩의 모드 목록 방식과 `controlled_fixture_v0`·`real_dev` 사례 목록 자리를 정한다. 샌드박스 안 `evaluate`이면 실행 조건 입력 파일을 샌드박스가 쓰지 않게 가른다. 채점기 `REPORT_DOMAIN`(보고서 파일 도메인명)과 AS2 보고서 파일 이름을 맞춘다.
- 채점기 DT8: `BATCH_DOMAINS`는 지금 `evaluate` 하나로 맞다. E2 이름이 정해지면 한 줄 더한다(다음 PR 2).
- 평가 스킬 ②: 채점 전 확인 1·2번은 ⑥의 명령 출력(건수와 일치 여부)으로 한다. 재실행 대상 목록 파일은 오케스트레이터가 열지 않는다.
