# 인터페이스 계약

TradeSentry 바깥(운영자, NemoClaw(OpenShell, 곧 에이전트를 격리해 돌리는 NVIDIA 샌드박스 런타임 위에서 에이전트를 돌리는 NVIDIA 참조 스택) 에이전트, 평가 스킬(Agent Skills 형식의 평가 작업 절차), 독립 채점기)이 기대는 약속이다. 형식의 정본은 `docs/rules/DATA_CONTRACT_V1.md`이고, 바꾸려면 공용 약속(두 트랙이 함께 기대는 약속) 변경 절차(`docs/rules/PARALLEL_DEV_RULES.md` §4)를 거친다.

| 인터페이스 | 정본 |
|---|---|
| CLI 명령과 공통 옵션, 모드 4개 | `docs/rules/DATA_CONTRACT_V1.md` §10·§4.1, `docs/plan/SCAFFOLD_BRIEF.md` §4.7 |
| `tradesentry evaluate`의 선택 옵션 `--conditions-extra <JSON 상대 경로>`(운영자가 아는 실행 조건을 실행 조건 입력 파일에 합치는 배관. 허용 키는 하네스가 채우지 않는 실행 조건 키) | `docs/tracking/decisions/20260926-0155-model-decision-conditions-extra.md`, `skills/tradesentry-eval/SKILL.md`의 "결과 보고"(실행 조건 입력 파일 항목), 코드 `src/tradesentry/evaluation/batch_run.py`의 `OPERATOR_CONDITION_KEYS`·`OPERATOR_SUBKEYS` |
| `tradesentry run-case`의 선택 옵션 `--replay <재생 파일 상대 경로>`(키 없는 스모크 재현. 재생 파일 `eval/dev/smoke/{case_id}.json`의 기록된 모델 응답을 단위 I8 `ReplayTransport`로 재생하고 요청 해시를 대조한다. 점수표 근거 아님) | `docs/rules/DATA_CONTRACT_V1.md` §10.3, `docs/tracking/decisions/20260926-0230-model-decision-smoke-replay.md`, 코드 `src/tradesentry/cli/dispatch.py`의 `load_replay`, 재생 파일 만들기 `scripts/make_smoke_replay.py` |
| 런타임 스킬 `tradesentry`(NemoClaw 에이전트가 TradeSentry CLI를 부르는 데 쓰는 Agent Skills 형식의 작업 절차)의 인터페이스(부르는 명령, 인자 검증, 돌려주는 것) | `docs/plan/DEV_PLAN.md` §5.2, `docs/plan/SCAFFOLD_BRIEF.md` §3.5 |
| 사례를 지정하는 인자 형식과 탐지 대상 시계열 제한(아직 정하지 않음) | `docs/plan/SCAFFOLD_BRIEF.md` Q18 |
| 조회 도구 5개의 입력과 공통 출력 봉투(모든 조회 도구가 같은 키로 돌려주는 응답 형식) | `docs/rules/DATA_CONTRACT_V1.md` §5 |
| 근거 ID(보고서 주장이 가리키는 스냅샷 원본 행의 식별자) 형식과 해석 | 같은 문서 §4.4 |
| typed claim(정해진 필드로 쓰는 사실 주장), 주장 채점 결과 | 같은 문서 §6·§7 |
| 실행 결과 기록 | 같은 문서 §8 |
| 보고서 객체, 주장 채점 기록, 모의 승인 기록 | 같은 문서 §9 |
| 독립 채점기(`eval/scorer/`)의 입력과 결과 파일 | `docs/eval/RULEBOOK.md` B3·B7, `skills/tradesentry-eval/SKILL.md`의 "채점"과 "결과 보고" |
| 봉인 해시 목록 `eval/sealed_manifest.json` | `docs/rules/DATA_CONTRACT_V1.md` §12 |
| 관세청 API 응답의 뜻(총계 행, 빈 응답, 금액·중량 단위) | 같은 문서 §2.3.2·§3.4·§11 |
