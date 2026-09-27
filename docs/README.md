# TradeSentry 문서 색인

TradeSentry(관세청 수입통계에서 kg당 단가와 상대국 점유율이 전년 같은 달보다 크게 바뀐 경우를 경보로 잡고, Nemotron 조사자와 별도 문맥의 검수자(Critic)가 제한된 조회 도구로 반증을 시도해 담당자의 다음 업무를 제시하는 에이전트 시스템)의 계획·규칙·평가 문서 세트 입구다. 2026-09-24(목) 문서 실행에서 만들었고, 구현은 이 문서들을 근거로 다음 실행에서 한다. 부정·위법 판정 시스템이 아니다.

- 대상: 구현 실행을 맡는 에이전트(Claude 보조 에이전트, Codex headless)와 그 결과를 확인하는 사용자. 심사위원·처음 보는 사람용 안내(무엇·실행 사슬·NVIDIA 스택·키 없는 재현·평가 방법과 결과 위치)는 저장소 루트 `README.md`다(2026-09-26(토) 추가)
- 예선 마감: 2026-09-28(월) 23:59 KST. MVP 시험: 2026-09-25(금). 평가 룰북 `RB-1` 동결: 2026-09-26(토) 18:00(조정값. 2026-09-25(금) 사용자 결정 11로 12:00에서 늦췄다)
- 이 색인은 각 문서의 규칙과 값을 다시 적지 않는다. 역할과 관계만 적고 해당 문서를 가리킨다.

## 1. 문서 목록과 역할

| 문서 | 역할 | 이런 때 연다 |
|---|---|---|
| `docs/plan/DEV_PLAN.md` | 개발 플랜(NVIDIA 최소 확장판). 목적·가설, 동결 자료 범위, 실행 사슬, OpenShell 정책 요건과 대응표, NemoClaw·스킬 경로와 대체 경로, 조사·판정 규칙, 모듈 지도, 결정 기록. 앞으로의 기준 개발 플랜 | 무엇을 왜 만드는지 알아야 할 때 |
| `docs/plan/ROADMAP.md` | 두 트랙 동시 진행 로드맵. 날짜별 도착점, 구현 작업 목록(`S0`, `X1`, `DT1`~`DT8`, `MT1`~`MT7`, 조립 작업 `AS1`~`AS4`, `V1`, `F1`, `F2`, `U1`, `AP1`, `R1`, `P1`~`P3`)과 작업별 실행자·검토자·맡는 단위, 9/25 MVP 합격 체크리스트, 시간 예산, 줄이는 순서, 사용자 확인 항목, 위험과 대체 경로 | 오늘 무엇을 하고 누가 검토하는지 정할 때 |
| `docs/plan/UNITS.md` | 단위 표. 최소 단위 65개(단위: 혼자 실행하고 시험할 수 있게 파일 하나로 만든 가장 작은 구현 조각)의 ID·도메인명(단위마다 붙인 출력용 이름)·파일·소유·입출력·조립 판정 후보, 조립체와 조립 점검 절차, 조립 작업 AS1~AS4. 2026-09-24(목) 사용자 결정(도메인 재편 A안)으로 더했다 | 단위 파일을 만들거나 고칠 때, 조립하며 버릴 것과 합칠 것을 가릴 때 |
| `docs/plan/SCAFFOLD_BRIEF.md` | 앱 스캐폴딩(프로젝트 뼈대 생성) 외부 자문용 명세서. 저장소를 보지 않은 외부 자문자가 이 파일 하나로 자문하고, 열린 질문 `Q1.`~`Q21.`에 번호별로 회신한다 | 구현 첫 작업 `S0` 전에 외부 자문을 받을 때, 자문 회신을 반영할 때 |
| `docs/plan/SUBMISSION_SCENARIOS.md` | 제출 시나리오 선택 문서. MVP(최소 기능 제품) 완성 뒤 "MVP 수준 제출"과 "풀 애플리케이션 수준 제출" 가운데 고를 때 두 시나리오의 필요 작업(스모크 재현(키 없이 명령 하나로 끝까지 도는 재현)·화면(Streamlit 웹 화면)·승인 모의(코드와 시험만 있는 모의 승인) 포함)·소요 시간·심사와 자기채점 영향·위험을 모아 보여 준다. 새 규칙을 만들지 않고 로드맵·룰북·대회 조사 문서를 가리킨다. 2026-09-26(토) 사용자 요청으로 더했다 | MVP 시험 뒤 제출 범위를 정할 때 |
| `docs/rules/DATA_CONTRACT_V1.md` | 두 트랙 공용 자료 계약(현행 `schema_version=2`, 파일 이름의 V1은 처음 버전 표시). 객체·필드·상태값·ID 형식·도구 입출력 봉투·typed claim(정해진 필드에 담는 사실 주장)·결과 기록 키·단위와 표시 자릿수·봉인 해시 기록 형식, 계획 경로·명령 표와 이름·출력 규칙(실행명, 도메인 출력 `outputs/`, 증거 복사). **상태값·ID·모드 이름·경로의 정본** | 코드나 자료에 쓸 이름·값·형식을 정할 때 |
| `docs/rules/PARALLEL_DEV_RULES.md` | 병렬 개발 규칙. 모델 트랙(M)·데이터 트랙(D) 파일 소유, 합성 시험자료 먼저 넘기기, D → M 인수 조건, 공용 약속 변경 승인, 봉인 자료 규칙, 실자료 분할 절차, 브랜치와 PR 이름, 스냅샷과 키 보호 | 두 트랙이 서로의 파일·약속을 건드릴 때, 봉인 자료를 다룰 때 |
| `docs/rules/AGENT_OPS.md` | 에이전트 운용 규칙. 실행자 선택(Claude 보조 에이전트, Codex headless), 도메인 검토자 4종과 작업 성격 대응, 검토 판정과 반복, 작업 단위 PR과 병합, 외부 자문 체크포인트, 증거 규칙 | 작업을 누구에게 맡기고 어떻게 검토·병합할지 정할 때 |
| `docs/eval/RULEBOOK.md` | 평가 룰북. Part A는 팀 채점 규범(`docs/research/SCORING_GOLDEN_RULE.md`)에 따른 자기채점 규칙, Part B는 TradeSentry 성능 평가 규칙(자료 묶음, 비교 모드, 대표 지표와 채점 규칙, A등급 주장 조건, 보조 지표, 실행 규칙, 동결과 봉인, 결과 보고 양식). 부록에 `RB-1` 동결 때 사용자가 확인할 해석을 모았다 | 점수·지표를 계산하거나 판정 규칙을 확인할 때 |
| `docs/eval/RESULTS.md` | 결과표(로드맵 R1). 두 봉인 묶음(`real_sealed`·`holdout40`)의 대표·보조 지표와 Wilson 95% 구간·등급, A등급 주장 조건(룰북 B3-3) 판정, 룰북 B7 공개 값, 정직한 한계, 재현 명령. 숫자는 커밋된 채점 요약 `artifacts/eval/score-*/scorer_summary-*.md`에서만 옮긴다 | 제출서·README에 결과 숫자를 적을 때 |
| `docs/eval/SKILL_DICTIONARY.md` | 스킬 사전. NVIDIA 공식 Agent Skills와 우리 스킬의 이름·출처·설치 명령·용도·단계·채점표 항목·상태 | 어떤 스킬을 설치하고 어디에 쓰는지 볼 때 |
| `skills/tradesentry-scorecard/SKILL.md` | 평가 스킬 ①. 저장소를 룰북 Part A로 자기채점하고 근거가 붙은 점수표를 남기는 절차 | MVP 시험 뒤, `RB-1` 동결 뒤, 제출 전 자기채점할 때 |
| `skills/tradesentry-eval/SKILL.md` | 평가 스킬 ②. 룰북 Part B의 성능 평가를 사전 점검 → 실행 → 채점 → 결과 보고 순으로 수행하는 절차. 봉인 자료 취급과 멈춤 규칙 포함 | dev20·`real_dev` 평가, `RB-1` 동결 뒤 봉인 묶음 채점을 할 때 |
| `docs/tracking/journal.md` | 기획·개발 일지. 대회 이해·주제 선정부터 저장소 공개·라이선스까지 무엇을 어떤 순서로 했고 어떤 대안 가운데 무엇을 왜 골랐는지를 결정 기록·PR·대화 기록으로 시간순으로 엮은 요약. 정본은 결정 기록과 계획 문서다. 2026-09-27(일) 사용자 요청으로 더했다 | 개발 경위와 선택의 이유를 한 번에 훑을 때 |

`[사실]` 위 표에서 `docs/plan/UNITS.md`를 뺀 10개 문서와 이 색인이 이번 문서 실행의 산출물 11개다. `docs/plan/UNITS.md`는 2026-09-24(목) 사용자 결정(결정 기록 `docs/tracking/decisions/20260924-1720-user-decision-domain-restructure.md`)을 계획 문서에 반영하는 자료 계약 PR에서 더했다. 런타임 스킬 `skills/tradesentry/SKILL.md`는 구현 단계 산출물이라 아직 없다. 그 인터페이스 계약은 `docs/plan/DEV_PLAN.md`와 `docs/plan/SCAFFOLD_BRIEF.md`에 있다.

## 2. 읽는 순서

**구현 착수 전(모든 구현 에이전트)**
1. 이 색인
2. `docs/plan/DEV_PLAN.md` — 무엇을 왜 만드는지
3. `docs/plan/ROADMAP.md` — 날짜, 작업 ID, 선행 작업, 실행자·검토자, 줄이는 순서
4. `docs/plan/UNITS.md` — 맡은 단위의 파일·도메인명·입출력·소유와 조립 계획
5. `docs/rules/DATA_CONTRACT_V1.md` — 쓸 이름과 형식(값의 정본), 이름·출력 규칙
6. `docs/rules/PARALLEL_DEV_RULES.md` — 자기 트랙의 파일 소유와 인수 조건, 봉인 자료 규칙
7. `docs/rules/AGENT_OPS.md` — 검토·PR·병합 절차와 증거 규칙
8. 맡은 작업이 평가에 닿으면 `docs/eval/RULEBOOK.md`, 스킬을 설치·작성하면 `docs/eval/SKILL_DICTIONARY.md`

**앱 스캐폴딩 외부 자문 때(`S0`)**
1. `docs/plan/SCAFFOLD_BRIEF.md` 한 파일을 자문자에게 보낸다. 이 파일은 저장소를 보지 않고 읽도록 썼다.
2. 회신은 질문 번호별(동의 / 수정 제안 / 근거)로 받는다. 반영 여부와 이유는 결정 기록에 남긴다. 공용 약속(자료 형식·상태값·기준값·도구 한도·품목·국가 확정·평가 구성·제출서 주장 문구, 그리고 자료 계약의 고정값과 계획 경로·명령 표)을 바꾸는 자문은 사용자 승인을 받는다(`docs/rules/AGENT_OPS.md` 외부 자문 체크포인트).

**평가 때**
1. `docs/eval/RULEBOOK.md` — Part B(성능 평가)와 부록
2. `skills/tradesentry-eval/SKILL.md` — 사전 점검부터 결과 보고까지의 절차
3. `skills/tradesentry-scorecard/SKILL.md` — 자기채점(룰북 Part A)
4. 봉인 자료(`holdout40`, `real_sealed`)를 다루기 전에 `docs/rules/PARALLEL_DEV_RULES.md`의 봉인 자료 규칙

## 3. 문서 사이 관계와 우선순위

- **값의 정본**: `docs/rules/DATA_CONTRACT_V1.md`. 상태값·모드 이름·ID 형식·데이터셋 이름·기록 키·계획 경로·명령은 모든 문서가 이 문서와 글자까지 같게 쓴다.
- **충돌할 때의 우선순위**: `DATA_CONTRACT_V1` > `RULEBOOK` > `DEV_PLAN` > `ROADMAP` > `UNITS` > 나머지(`PARALLEL_DEV_RULES`, `AGENT_OPS`, `SKILL_DICTIONARY`, `SCAFFOLD_BRIEF`, 평가 스킬 두 개).
- **모두 설계 명세 아래다**: 이 문서 세트는 2026-09-23(수) 설계 세션에서 사용자가 승인한 설계 명세를 근거로 만들었다. 명세는 로컬 계획 폴더 `.dryforge/`(git 추적 제외)에 있고 저장소에는 없다. 문서 안의 "명세 §x" 표기는 출처 표시다. 명세의 값은 `docs/rules/DATA_CONTRACT_V1.md`에, 결정과 이유는 `docs/plan/DEV_PLAN.md` "결정 기록"과 부록 A(Codex 검토 회의 요약)에 옮겨져 있다.
- **바꾸는 방법**: 공용 약속은 버전 올림 → 영향받는 합성 시험자료·정답표 재생성이나 재검증 → 양 트랙 검토 → 사용자 승인 순으로만 바꾼다(`docs/rules/PARALLEL_DEV_RULES.md`). `RB-1` 동결 뒤의 룰북 변경은 새 버전과 사유로만 한다(`docs/eval/RULEBOOK.md`).
- **이후의 결정 기록**: 2026-09-23(수) 설계 세션의 결정은 `docs/plan/DEV_PLAN.md` §13에 있다. 2026-09-24(목) 문서 작업 중 검토에서 정한 이견·해석과 구현 실행부터의 결정은 `docs/tracking/decisions/`에 남긴다.
- **기획·개발 일지는 정본이 아니다**: `docs/tracking/journal.md`는 결정 기록과 계획 문서를 시간순으로 엮은 요약이다. 일지와 다른 문서가 다르면 결정 기록과 위 우선순위의 문서를 따른다.
- **문서끼리 서로 가리키는 곳**:
  - 로드맵의 작업별 검토자는 `docs/rules/AGENT_OPS.md`의 작업 성격 → 검토자 대응을 따른다.
  - 평가 스킬 두 개는 룰북과 자료 계약을 다시 정의하지 않고 가리킨다.
  - 스캐폴딩 명세서는 외부 자문자를 위해 자료 계약 요약을 본문에 담았다. 둘이 다르면 자료 계약이 이긴다.
  - 계획 경로·명령 표는 자료 계약 §10, 개발 플랜 §10.1, 스캐폴딩 명세서 §2.3에 글자까지 같은 사본이 있다. 단위 표는 자료 계약 §10.3의 이름·출력 규칙으로 단위마다 이름을 붙인다.

## 4. 이력 문서

`docs/research/`의 이전 기록(2026-09-27(일) 사용자 요청으로 저장소 루트에서 옮겼다)은 사실 근거이자 과거 결정의 기록이다. 고치지 않고 인용만 한다. 이번 문서 세트와 다르면 이번 문서 세트가 현행이다.

| 문서 | 성격 |
|---|---|
| `docs/research/Pasted markdown.md` | 기존 개발계획("구 개발계획"). `docs/plan/DEV_PLAN.md`가 대체했다. 바뀐 결정은 `docs/plan/DEV_PLAN.md` "기존 계획 대비 바뀐 점" 대조표에 있다 |
| `docs/research/TRADESENTRY_HANDOFF.md`, `docs/research/TRADESENTRY_FACTS_MEMO.md` | 이전 세션 인계와 실측 사실 메모 |
| `docs/research/TRADESENTRY_TEAM_SPLIT_DECISIONS.md` | 팀 분담 결정(예: "분담 D6"). 사람 2인 서명 절차는 "사용자 승인 + 검토 에이전트"로 바뀌었다 |
| `docs/research/SCORING_GOLDEN_RULE.md` | 팀 채점 규범(예: "규범 G4"). 가중치·게이트·앵커는 팀 설계 규칙이고 대회 공식 배점이 아니다 |
| `docs/research/NVIDIA-FastCampus-Korea-Agentic-AI-Hackathon-2026.md`, `docs/research/HSGATE_R3_NVIDIA_STACK_CHECK.md`, `docs/research/03-openshell-policy-yaml-구조.md` | 대회·NVIDIA 스택 조사 문서. OpenShell·NemoClaw·Agent Skills 서술의 근거 |
| `docs/research/IDEA_*`, `docs/research/HSGate*`·`docs/research/HSGATE_*`(R3 문서 말고), `docs/research/CHATGPT_*`, `docs/research/01-`·`02-` 문서, `docs/research/DATA_AND_SKILL_INVENTORY.md`, `docs/research/research_raw/` 등 | 주제 선정 과정의 탐색 기록. 현행 설계의 근거가 아니다 |

옮기기 전 경로(저장소 루트)로 적힌 곳은 고치지 않았다: 동결된 평가 룰북 `docs/eval/RULEBOOK.md`, 지난 결정 기록, `artifacts/` 증거물, `eval/`의 주석. 옛 경로와 새 경로의 대응은 `docs/research/README.md`에 있다.

## 용어 설명

- **TradeSentry**: 관세청 수입통계 경보를 Nemotron 조사자와 Critic이 반증 검수해 담당자의 다음 업무(`MAINTAIN` 검토 유지 / `MONITOR` 모니터링 / `HOLD` 자료 보류)를 제시하는 에이전트 시스템.
- **모델 트랙(M) / 데이터 트랙(D)**: 판정 정책·조사 흐름·NVIDIA 연동·그룹핑을 맡는 트랙 / 수집·지표·합성과 평가 자료·채점기를 맡는 트랙.
- **공용 약속**: 두 트랙이 함께 쓰는 자료 형식·상태값·기준값 같은 약속. 바꾸려면 사용자 승인이 필요하다.
- **정본**: 문서끼리 값이 다를 때 기준이 되는 문서.
- **설계 명세**: 이 문서 세트를 만든 2026-09-23(수) 설계 세션의 목표 명세. 로컬 계획 폴더에만 있다.
- **봉인 자료**: 평가 정답이 개발 과정에 새지 않도록 저장소 밖(`~/.tradesentry/sealed/`)에 두고 해시만 커밋하는 평가 자료(`holdout40`, `real_sealed`).
- **`RB-1`**: 평가 룰북의 첫 동결 버전. 동결 뒤 봉인 자료를 한 번만 채점한다.
- **S0 / X1**: 구현 첫 작업 단위인 앱 스캐폴딩(외부 자문 체크포인트) / 구현 첫날의 세로형 최소 통합 시험.
- **단위 / 조립**: 혼자 실행하고 시험할 수 있게 파일 하나로 만든 가장 작은 구현 조각 / 단위들을 이어 CLI 명령 하나가 도는 묶음으로 만들며 버릴 것과 합칠 것을 가리는 일. 단위 ID는 로드맵 작업 ID와 글자가 겹칠 수 있어 다른 문서에서는 "단위 V1"처럼 쓴다.
- **실행명 / 도메인 출력 / 증거 복사**: `{실행 이름}-{yymmddhhmmss}` 형식의 실행 폴더 이름(`run_id`) / 실행마다 `outputs/{실행명}/`에 쌓는 출력(커밋 안 함) / 실행 폴더와 같은 이름의 폴더를 `artifacts/{종류}/` 아래에 만들고 종류마다 정한 커밋 증거 파일만 복사해 커밋하는 일(trace는 빼고, 봉인 묶음은 금지 해제 조건(정답 대조 채점이 끝나고, `real_sealed`이면 표본 추출 seed 공개 기록까지 있는 때) 뒤에만). 그렇게 커밋한 폴더와 파일을 커밋 사본이라 한다. "승격"은 빈 응답 달을 무거래 확정 `CONFIRMED_NO_TRADE`로 바꾸는 `policy_v1` 규칙만 뜻한다.
- **Agent Skills**: `SKILL.md`(이름·설명 머리말과 절차 본문)로 에이전트에게 작업 방법을 주는 형식.
- **OpenShell / NemoClaw / NIM / NAT**: 에이전트를 격리 실행하는 NVIDIA 샌드박스 런타임 / OpenShell 샌드박스 안에서 OpenClaw 에이전트를 돌리는 NVIDIA 참조 스택 / NVIDIA 추론 API / NVIDIA NeMo Agent Toolkit(실행·추적·프로파일러·평가 도구).
- **도메인 검토자**: 작업 성격에 따라 띄우는 읽기 전용 검토 에이전트(무역통계·관세, 평가 방법론, NVIDIA 스택, 보안).
