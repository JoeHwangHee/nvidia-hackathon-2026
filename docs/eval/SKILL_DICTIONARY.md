# TradeSentry 스킬 사전

TradeSentry(관세청 수입통계에서 kg당 단가와 상대국 점유율이 전년 같은 달보다 크게 바뀐 경우를 경보로 잡고, 제한된 조회 도구로 반증을 시도해 담당자의 다음 업무를 제시하는 에이전트 시스템)가 개발·평가·런타임에 쓰는 스킬을 모은 사전이다. NVIDIA 공식 스킬과 우리가 직접 쓰는 스킬을 한 표로 정리하고, 스킬마다 언제·누가·무엇에 쓰는지, 쓰지 않는 스킬은 왜 빼는지, 어떻게 설치하고 확인하는지를 적는다.

- 작성: 2026-09-24(목) 문서 실행. 문서 실행은 구현에 앞서 계획·규칙·평가 문서와 평가 스킬만 만드는 단계다. 이 실행에서는 어떤 스킬도 설치하지 않는다.
- 우선순위: 문서끼리 어긋나면 `docs/rules/DATA_CONTRACT_V1.md` > `docs/eval/RULEBOOK.md` > `docs/plan/DEV_PLAN.md` > `docs/plan/ROADMAP.md` > 이 문서 순으로 따른다. 이름·경로·명령 값의 정본은 `docs/rules/DATA_CONTRACT_V1.md`다.
- 관련 문서: NVIDIA 결합 설계 전체는 `docs/plan/DEV_PLAN.md`, 날짜별 도착점은 `docs/plan/ROADMAP.md`, 채점 규칙은 `docs/eval/RULEBOOK.md`, 문서 색인은 `docs/README.md`에 있다.

## 0. 읽기 전에

**근거 태그**

- `[사실]`: 직접 확인했거나 저장소의 조사 문서로 확인된 내용. 괄호 안에 근거 문서를 적는다.
- `[추론]`: 근거가 있는 판단.
- `[DESIGN]`: 팀 설계 규칙. 대회 공식 규칙이 아니다.
- `[미확인]`: 검증하지 않은 내용. 사실로 인용하지 않는다.

**이 문서에 자주 나오는 용어**(자세한 설명은 끝의 "용어 설명")

- **Agent Skills**(AI 에이전트가 읽고 따르는 이식 가능한 작업 지침 묶음, `SKILL.md` 형식): NVIDIA가 검증한 공식 스킬을 build.nvidia.com/skills에 공개한다. REST API가 아니며 `skills` CLI(Agent Skills를 설치·갱신하는 명령줄 도구, `npx skills ...`로 부른다)로 설치한다 `[사실: NVIDIA-FastCampus-Korea-Agentic-AI-Hackathon-2026.md §7, §7-1]`.
- **공식 스킬**(NVIDIA가 `NVIDIA/skills`·`NVIDIA/OpenShell` 저장소로 공개한 스킬)과 **우리 스킬**(이 저장소의 `skills/` 아래에 팀이 쓰는 스킬)을 구분한다.
- **거버넌스 카드**(스킬이 무엇을 하고 무엇을 읽고 쓰는지 등 능력 범위를 밝히는 카드): `skill-card-generator`로 만든다.
- **OpenShell**(에이전트를 격리 실행하는 NVIDIA 샌드박스 런타임. YAML 정책으로 파일시스템·네트워크·프로세스를 통제하고 허용·차단을 감사 로그로 남긴다).
- **NemoClaw**(OpenShell 샌드박스 안에서 OpenClaw 에이전트를 돌리는 NVIDIA 참조 스택, 알파 단계): 모델·에이전트 하네스·보안 런타임을 한 번에 묶은 배포 묶음이며, 그 보안 런타임이 OpenShell이다 `[사실: HSGATE_R3_NVIDIA_STACK_CHECK.md §7, NVIDIA-FastCampus-Korea-Agentic-AI-Hackathon-2026.md §8-2 FAQ]`. 하네스는 모델을 감싸 도구 호출과 대화 흐름을 돌리는 실행 틀이고, **OpenClaw**는 NemoClaw의 기본 하네스다.
- **NIM**(NVIDIA의 OpenAI 호환 추론 API). 모델은 Nemotron(NVIDIA 언어 모델 계열)의 `nvidia/nemotron-3-super-120b-a12b`다.
- **NAT**(NVIDIA NeMo Agent Toolkit, 패키지 `nvidia-nat`. 조사 흐름을 감싸 실행·추적·프로파일·사후 평가를 맡는다).
- **X1**(세로형 최소 통합 시험): 구현 첫날인 2026-09-24(목)에 NemoClaw 에이전트 → 스킬 → 샌드박스 안 CLI 최소 명령 → NIM 호출 1회 → NAT 실행 추적 1건 → 의도적 위반 1건의 차단 로그까지, 한 줄로 이어진 최소 경로를 한 번에 통과시키는 시험.
- **MVP 시험**: 2026-09-25(금)에 최소 기능이 처음부터 끝까지 도는지 합격 체크리스트(`docs/plan/ROADMAP.md`)로 확인하는 시험.
- **룰북**(`docs/eval/RULEBOOK.md`, 평가 규칙 문서. Part A는 프로젝트 자기채점, Part B는 TradeSentry 성능 평가. 동결 버전 이름은 `RB-1`)과 **자기채점**(채점 규범과 룰북 Part A로 우리 저장소를 스스로 채점하는 일).
- **채점 대상 실행**(OpenShell 샌드박스 안에서 TradeSentry CLI로 사례를 돌리는 실행)과 **정답 대조 채점**(샌드박스 밖에서 독립 채점기가 결과를 정답·원본과 비교하는 일)은 따로 쓴다.
- **채점 규범**(`SCORING_GOLDEN_RULE.md`, 팀이 정한 자기채점 규범)의 지표 코드는 "규범 1d"처럼 출처를 붙여 쓴다. 규범의 가중치·하드 게이트·점수 앵커(점수 0/1/3/5마다 정한 판정 문구)는 `[DESIGN]`이고 대회 공식 배점이 아니다.

## 1. 스킬 사전 표

공식 스킬 7개(선택 1개 포함)와 우리 스킬 3개다. 공식 스킬의 이름과 출처 저장소는 2026-09-23(수) 설계 세션(이번 문서 실행의 목표와 결정을 정한 작업)에서 실제 저장소와 대조해 확인한 목록을 그대로 옮겼다 `[사실]`. 작성자는 외부 조회를 하지 않았고, 검토자가 2026-09-24(목)에 두 저장소의 GitHub 트리와 다시 대조해 7개 모두 적은 저장소의 `skills/<name>/SKILL.md`에 있음을 확인했다 `[사실: 2026-09-24(목) GitHub 트리 대조]`. 대조 방법은 §5.4에 있다.

**표 읽는 법**

- **상태** "2026-09-23(수) 저장소 대조 확인": 이날 스킬 이름이 실제 저장소에 있음을 확인했다는 뜻이다. 설치나 사용을 확인했다는 뜻이 아니다. 설치하거나 쓰면 §5.5 규칙대로 이 열을 고친다.
- **채점표 항목**: 채점 규범 §3의 하위 지표 코드다. 그 스킬을 쓴 결과가 해당 지표의 근거가 **될 수 있다**는 뜻이며 점수를 약속하지 않는다. 점수는 `docs/eval/RULEBOOK.md` Part A의 증거 정의로 매긴다.
  - 규범 1b OpenShell 활용 깊이, 1c NemoClaw 활용 깊이, 1d Agent Skills 활용, 3a 정량 지표 제시, 3b 평가 투명성, 3d 관측성, 3e 실패 내성, 4a NVIDIA 자산 확장 기여
- **단계**: 개발(구현·설치·시험 준비), 평가(룰북에 따른 실행과 채점), 런타임(TradeSentry 실행 사슬 안에서 동작).
- `NVIDIA/OpenShell` 저장소 스킬을 `--skill`로 하나씩 고르는 동작은 `[미확인]`이다(§5.2).
- `nemo-relay-plugin-observability`는 설계 세션 목록에 출처 저장소가 적혀 있지 않았다. 2026-09-24(목) GitHub 트리 대조에서 `NVIDIA/skills`의 `skills/nemo-relay-plugin-observability/SKILL.md`로 확인했다 `[사실: 2026-09-24(목) GitHub 트리 대조]`.

| 이름 | 출처 저장소 | 설치 명령 | TradeSentry에서의 용도 | 단계(개발·평가·런타임) | 채점표 항목 | 상태 |
|---|---|---|---|---|---|---|
| `generate-sandbox-policy` | `NVIDIA/OpenShell` | `npx skills add NVIDIA/OpenShell --skill generate-sandbox-policy` | OpenShell 샌드박스 정책 초안 생성. `configs/openshell/policy.yaml` 작성 보조(§2.2) | 개발 | 규범 1b, 1d | 2026-09-23(수) 저장소 대조 확인 |
| `openshell-cli` | `NVIDIA/OpenShell` | `npx skills add NVIDIA/OpenShell --skill openshell-cli` | OpenShell CLI 사용 안내. 샌드박스 생성·정책 적용·`openshell logs` 감사 로그 수집·의도적 위반 시험(§2.3) | 개발·평가 | 규범 1b, 1d, 3e | 2026-09-23(수) 저장소 대조 확인 |
| `debug-inference` | `NVIDIA/OpenShell` | `npx skills add NVIDIA/OpenShell --skill debug-inference` | 샌드박스의 추론 경로 점검. X1에서 NIM 호출이 안 될 때(§2.4) | 개발 | 규범 1d | 2026-09-23(수) 저장소 대조 확인 |
| `nemoclaw-user-guide` | `NVIDIA/skills` | `npx skills add NVIDIA/skills --skill nemoclaw-user-guide` | NemoClaw 설치·기동과 OpenClaw 에이전트 운용 안내(§2.5) | 개발 | 규범 1c, 1d | 2026-09-23(수) 저장소 대조 확인 |
| `skill-card-generator` | `NVIDIA/skills` | `npx skills add NVIDIA/skills --skill skill-card-generator` | 우리 스킬 3개의 거버넌스 카드 생성(§3.5) | 개발(제출 준비) | 규범 1d, 4a | 2026-09-23(수) 저장소 대조 확인 |
| `nvidia-skill-finder` | `NVIDIA/skills` | `npx skills add NVIDIA/skills --skill nvidia-skill-finder` | 필요한 공식 스킬 추가 탐색. 후보 찾기만 하고 채택은 §2.1 기준(§2.7) | 개발 | 규범 1d | 2026-09-23(수) 저장소 대조 확인 |
| `nemo-relay-plugin-observability`(선택) | `NVIDIA/skills` `[사실: 2026-09-24(목) GitHub 트리 대조]` | `npx skills add NVIDIA/skills --skill nemo-relay-plugin-observability` | 도구·모델 호출 추적 보강 후보. 기본은 넣지 않는다(§2.8) | 개발·평가(선택) | 규범 3d | 2026-09-23(수) 저장소 대조 확인. 선택 |
| `tradesentry-scorecard` | 이 저장소(비공개 원격 `JoeHwangHee/nvidia-hackathon-2026`), `skills/tradesentry-scorecard/SKILL.md` | 공개 전에는 설치하지 않고 저장소 파일을 직접 읽는다. `npx skills add JoeHwangHee/nvidia-hackathon-2026 --skill tradesentry-scorecard`는 `[미확인]`(§5.3) | 평가 스킬 ①. 저장소를 룰북 Part A로 자기채점(§3.2) | 평가 | 규범 1d, 4a | 2026-09-24(목) 문서 실행에서 작성 |
| `tradesentry-eval` | 이 저장소, `skills/tradesentry-eval/SKILL.md` | 공개 전에는 설치하지 않고 저장소 파일을 직접 읽는다. `npx skills add JoeHwangHee/nvidia-hackathon-2026 --skill tradesentry-eval`는 `[미확인]`(§5.3) | 평가 스킬 ②. 룰북 Part B 성능 평가를 사전 점검→실행→채점 순으로 수행(§3.3) | 평가 | 규범 1d, 3a, 3b, 4a | 2026-09-24(목) 문서 실행에서 작성 |
| `tradesentry` | 이 저장소, `skills/tradesentry/SKILL.md` | NemoClaw 에이전트에 넣는 방식은 X1에서 정한다. `npx skills add JoeHwangHee/nvidia-hackathon-2026 --skill tradesentry`는 `[미확인]`(§5.3) | 런타임 스킬. NemoClaw의 OpenClaw 에이전트가 부르고 OpenShell 안 TradeSentry CLI로 잇는다(§3.4) | 런타임 | 규범 1c, 1d, 4a | 구현 단계 작성 예정(2026-09-25(금)) |

## 2. 공식 스킬 사용 계획

이 절의 사용 계획(누가·언제·무엇에)은 팀 설계 `[DESIGN]`이다. 스킬 설명과 OpenShell 동작처럼 근거 문서가 있는 문장에는 `[사실]`을, 판단에는 `[추론]`을 붙였다.

### 2.1 공통 규칙 `[DESIGN]`

1. **최소 확장**: 지웠을 때 나빠지는 지표나 절차가 있는 스킬만 넣는다. 답이 없으면 개수 채우기다(채점 규범 §7 나쁜 신호 "지워도 그대로 작동한다"). 스킬마다 아래에 삭제 시험 답(지우면 무엇이 나빠지는가)을 적었다.
2. **정직한 답**: 공식 스킬은 모두 개발·평가를 돕는 도구다. 지워도 TradeSentry의 정확도 지표, 곧 대표 지표(실자료 봉인 묶음 `real_sealed`의 경보 보고서에서 잰 사실 주장 오류율)와 보조 지표(봉인 평가용 합성 자료 holdout40의 근거 충족 처리정확도)는 변하지 않는다 `[추론]`. 나빠지는 것은 작업 절차의 재현성과 규범 1d(공식 스킬 조합)의 근거다. 구성요소별 컴포넌트 삭제 시험 전체는 `docs/eval/RULEBOOK.md` Part A를 따른다.
3. **사용 근거**: 설치만 하고 쓰지 않은 스킬은 규범 1d의 근거가 아니다. 스킬을 쓴 작업의 산출물 경로를 이 사전의 상태 열에 남긴다(§5.5).
4. **초안은 증거가 아니다**: 공식 스킬이 만든 정책·명령·설명은 초안이다. 문서의 주장은 로컬 실측 결과로만 하고, 공식 문서로 확인되지 않은 기능은 `[미확인]`으로 둔다.
5. **비밀값·봉인 자료**: 스킬에 `.env` 내용과 키 값을 넘기지 않는다. 키는 변수 이름(`NVIDIA_API_KEY`, `DATA_GO_KR_SERVICE_KEY`)으로만 말한다. 봉인 폴더(개발 중 보지 않도록 평가 자료를 저장소 밖에 두는 폴더. 환경변수 `TRADESENTRY_SEALED_DIR`, 기본값 `~/.tradesentry/sealed/`)는 스킬 입력에 넣지 않는다.

### 2.2 `generate-sandbox-policy` — OpenShell 정책 초안

- 누가·언제: 모델 트랙(M, 판정 정책·조사 흐름·NVIDIA 연동·그룹핑을 맡는 구현 트랙)의 보조 에이전트. X1(2026-09-24(목))의 최소 정책부터 2026-09-25(금) 정책 YAML 완성까지 쓴다.
- 산출: `configs/openshell/policy.yaml` 초안(소유 M, 보안 검토).
- 채택 조건: 초안은 `docs/plan/DEV_PLAN.md` §4 OpenShell 정책 요건 (a)~(e)와 대조한 뒤에만 채택한다. 특히 다음을 본다.
  - 파일시스템 정책은 허용 목록 방식이다. 나열한 경로(와 작업 폴더)만 허용하고 나머지는 거부한다 `[사실: 03-openshell-policy-yaml-구조.md §3.6]`. 그래서 저장소 안 평가 정답 경로의 읽기 차단은 그 경로를 허용 목록이나 작업 폴더에 **넣지 않을 때만** 성립한다. 초안이 정답 경로가 든 폴더를 작업 폴더로 잡으면 이 조건이 깨진다 `[추론]`.
  - 외부 전송은 NVIDIA 추론 엔드포인트만 허용하고, L7 규칙(HTTP 요청 수준에서 허용·거부를 정하는 규칙. REST 규칙 기준으로 method·path·query를 본다)에 method·path를 명시한다. `rules`를 빼면 해당 host:port가 통째로 열리므로 받지 않는다. 범용 바이너리(`curl`, `python3` 등)와 `/**` 경로의 조합도 받지 않는다 `[사실: 03-openshell-policy-yaml-구조.md §3.4, §5]`.
  - API 키를 샌드박스 안에 두지 않는다. 방식은 X1에서 실제로 성공한 것만 쓴다(§2.4).
  - 정적 계층(`filesystem_policy`·`landlock`·`process`)은 샌드박스를 만들 때 고정되고, 동적 계층(`network_policies`·`network_middlewares`)은 실행 중 다시 불러올 수 있다 `[사실: 03-openshell-policy-yaml-구조.md §2.1-1]`. 파일 접근 규칙을 바꾸려면 샌드박스를 다시 만든다.
- 한계: OpenShell L7 규칙이 보는 것은 method·path·query뿐이다(REST 규칙 기준). GraphQL·MCP·JSON-RPC 규칙은 operation·도구 이름 같은 별도 필드를 쓴다 `[사실: HSGATE_R3_NVIDIA_STACK_CHECK.md §2]`. 어느 쪽이든 근거 묶음·토큰 같은 본문 값을 조건으로 거는 필드는 없으므로, 보고서 숫자와 근거의 뜻을 따지는 일은 앱 코드(검증기)가 맡는다. 정책 초안에 그런 역할을 기대하지 않는다.
- 삭제 시험 답: 정책을 처음부터 손으로 써야 한다. 정확도 지표는 변하지 않는다. 규범 1b의 근거는 정책 파일과 감사 로그 자체다.

### 2.3 `openshell-cli` — OpenShell CLI 사용 안내

- 누가·언제: M 트랙 보조 에이전트(X1부터), 그리고 봉인 자료 채점 때 오케스트레이터(작업을 배분·병합하는 주관 에이전트).
- 용도
  - 샌드박스 생성, 정책 적용, 라이브 정책 확인(`openshell policy get <agent> --full`) `[사실: 03-openshell-policy-yaml-구조.md §6.1]`.
  - 감사 로그 수집: `openshell logs`로 허용·차단 이벤트를 모은다. 모든 allow/deny를 감사 로그로 기록한다는 근거는 `NVIDIA-FastCampus-Korea-Agentic-AI-Hackathon-2026.md` §8-2에, `openshell logs`의 이벤트 예(`HTTP:* DENIED`, `CONFIG:LOADED` 등)는 `HSGATE_R3_NVIDIA_STACK_CHECK.md` §3에 있다 `[사실]`. 감사 증거는 `openshell logs`의 허용·차단 이벤트와 앱 실행 기록이다.
  - 의도적 위반 시험: 정답 경로 읽기 시도, 비허용 호스트 전송, 비허용 바이너리, 키 조회를 각각 시험한다. 예측과 실측, 종료 코드, 로그 근거를 `artifacts/openshell/violation_tests.md`(예측·실측 대조표)와 `artifacts/openshell/logs/`(감사 로그 발췌)에 남긴다.
  - 봉인 채점용 샌드박스: 정적 계층은 생성 때 고정되므로, 봉인 입력은 공식 채점 대상 실행 전용 샌드박스를 새로 만들어 넣는다. 넣는 방식은 X1 뒤에 정한다 `[미확인]`.
- 해석 규칙: 명령 실패라는 사실만으로는 어느 장치가 막았는지 알 수 없다. 종료 코드와 감사 로그 행을 함께 남긴다 `[사실: 03-openshell-policy-yaml-구조.md §6.6]`. 정책이 어떤 목적지를 열어 두었다는 것만으로 안전을 주장하지 않는다.
- 삭제 시험 답: 정확도 지표는 변하지 않는다. 위반 시험 명령과 로그 수집 절차를 매번 따로 찾아야 해서 규범 3e(정책 위반 시험 결과) 증거를 만드는 시간이 늘어난다 `[추론]`.

### 2.4 `debug-inference` — 추론 경로 점검

- 누가·언제: M 트랙. X1(2026-09-24(목))에서 샌드박스 안 NIM 호출이 되지 않을 때.
- 용도: 키 주입 방식 두 후보를 시험할 때 추론 경로를 점검한다.
  - credential placeholder rewrite: 샌드박스는 자리표시자만 갖고, 게이트웨이가 요청을 내보낼 때 실제 자격증명으로 바꿔 넣는 방식 `[사실: HSGATE_R3_NVIDIA_STACK_CHECK.md §1]`.
  - `inference.local`: 샌드박스는 `inference.local`만 보고 게이트웨이가 백엔드로 전달하는 방식. 게이트웨이당 provider(추론 제공자) 1개·모델 1개만 연결하는 단일 백엔드다 `[사실: 03-openshell-policy-yaml-구조.md §2.1-1]`. 조사자(도구를 골라 근거가 붙은 보고서 초안을 쓰는 모델 호출)와 Critic(조사자가 받은 근거와 초안을 별도 문맥에서 검토하는 검수자)이 같은 모델이라 라우팅이 필요 없다.
  - 둘 중 X1에서 실제로 성공한 방식만 채택하고 이유를 결정 기록(`docs/tracking/decisions/`)에 남긴다. 이 스킬이 두 방식을 모두 다루는지는 `[미확인]`이다.
- 범위 밖: NIM 무료 키에서 간헐적으로 나는 HTTP 500은 경로 문제가 아니라 상류 오류일 수 있다 `[추론]`. 5xx 명시 재전송 규칙은 `docs/plan/DEV_PLAN.md`를 따른다.
- 삭제 시험 답: 정확도 지표는 변하지 않는다. X1에서 추론 경로 문제를 푸는 시간이 늘 수 있다 `[추론]`.

### 2.5 `nemoclaw-user-guide` — NemoClaw 운용 안내

- 누가·언제: M 트랙. X1(2026-09-24(목))과 NemoClaw 경로 완성(2026-09-25(금)) 때 쓴다.
- 용도: NemoClaw 설치·기동과 OpenClaw 에이전트 운용 안내. 이 스킬은 NemoClaw 문서 MCP 서버(MCP: 에이전트가 외부 도구·자료 서버에 접속하는 표준 프로토콜)와 문서로 에이전트를 안내한다 `[사실: DATA_AND_SKILL_INVENTORY.md PART 2-1 설명]`.
- 연결 방식: NemoClaw에서 스킬과 TradeSentry CLI를 잇는 방식은 `docs/plan/SCAFFOLD_BRIEF.md` "고정 사항과 열린 질문"에 있는 열린 질문이며, X1 결과로 정한다.
- 대체 경로: NemoClaw 경로가 서지 않을 때의 처리는 §3.4를 따른다.
- 삭제 시험 답: 정확도 지표는 변하지 않는다. NemoClaw는 알파 단계라 안내 없이 구성하면 X1 제한 시간 3시간(조정값)을 넘길 위험이 커진다 `[추론]`.

### 2.6 `skill-card-generator` — 우리 스킬의 거버넌스 카드

- 계획은 §3.5에 있다.
- 삭제 시험 답: 정확도 지표는 변하지 않는다. 우리 스킬의 능력 범위를 밝히는 카드가 없어져 규범 4a(NVIDIA 제품에 꽂히는 산출물) 근거가 약해진다 `[추론]`.

### 2.7 `nvidia-skill-finder` — 추가 스킬 탐색

- 누가·언제: 개발 중 누구나. 새 필요가 생기면 먼저 이 스킬로 맞는 공식 스킬이 있는지 찾는다. 이 스킬은 NVIDIA 관련 요청에 맞는 스킬을 찾아 준다 `[사실: DATA_AND_SKILL_INVENTORY.md PART 2-6 설명]`.
- 규칙: 찾은 후보는 §2.1 기준으로 판단한다. 채택하면 이 사전에 행을 더하고, 이름은 §5.4 방법으로 저장소와 다시 대조한다.
- 삭제 시험 답: 정확도 지표는 변하지 않는다.

### 2.8 `nemo-relay-plugin-observability` — 선택

- 설명: 도구·모델 호출 추적을 OpenTelemetry(호출 추적 자료의 공개 표준) 등의 형식으로 남기는 관측 스킬이다 `[사실: DATA_AND_SKILL_INVENTORY.md PART 2-2 설명]`.
- 기본은 넣지 않는다 `[DESIGN]`. NAT 실행 추적과 프로파일 결과가 MVP 합격 체크리스트(`docs/plan/ROADMAP.md`)의 NAT 항목(7번)과 규범 3d(관측성)의 근거를 채우면, 이 스킬을 지워도 나빠지는 지표가 없다 `[추론]`.
- 다시 볼 조건: NAT 추적에 남지 않는 항목이 실제로 확인될 때만 검토하고, 그때 §2.1 기준으로 판단한다.

### 2.9 "Skill API" 대응과 제출서 표기

- 대회 공지의 "Skill API"는 NVIDIA 공식 제품명이 아니다 `[사실: NVIDIA-FastCampus-Korea-Agentic-AI-Hackathon-2026.md §7]`. 주최측이 뜻한 바는 `[미확인]`이다. 그래서 실체로 확인된 두 가지, 곧 build.nvidia.com Agent Skills(공식 스킬 조합 + 자체 SKILL.md 저작)와 NIM API를 **둘 다** 쓴다.
- 제출서 Tech Stack 칸(사용한 NVIDIA 기술과 전체 기술 스택을 나열하는 신청서 문항)에는 다음을 나열한다. 설치만 한 스킬은 적지 않는다 `[DESIGN]`.
  - 실제로 쓴 스킬 이름(§5.5의 사용 근거 경로가 있는 것만)
  - 모델 ID `nvidia/nemotron-3-super-120b-a12b`
  - 엔드포인트 `https://integrate.api.nvidia.com/v1/chat/completions`

### 2.10 사용 일정 `[DESIGN]`

날짜별 도착점의 정본은 `docs/plan/ROADMAP.md`다. 아래는 그 일정 안에서 스킬을 쓰는 자리다.

| 날짜 | 작업 | 쓰는 스킬 |
|---|---|---|
| 2026-09-24(목) | X1(설치·기동 포함, 3시간 제한) | `openshell-cli`, `generate-sandbox-policy`, `debug-inference`, `nemoclaw-user-guide` |
| 2026-09-25(금) | OpenShell 정책 YAML·위반 시험표, NemoClaw 경로, 런타임 `tradesentry` 스킬 작성, 오후 MVP 시험과 자기채점 | `generate-sandbox-policy`, `openshell-cli`, `nemoclaw-user-guide`, `tradesentry`, `tradesentry-eval`, `tradesentry-scorecard` |
| 2026-09-26(토) | `RB-1` 동결(12:00) 뒤 봉인 자료 채점 대상 실행 시작 | `tradesentry-eval`, `openshell-cli` |
| 2026-09-27(일) | 결과 정리, 자기채점, README·재현 묶음 준비 | `tradesentry-scorecard`, `skill-card-generator` |
| 2026-09-28(월) | 최종 자기채점, 스킬 이름 재대조, 제출서 Tech Stack 작성 | `tradesentry-scorecard` |

## 3. 우리 스킬

이 절의 규칙은 팀 설계 `[DESIGN]`이며 대회 공식 규칙이 아니다. 평가 규칙의 정본은 `docs/eval/RULEBOOK.md`, 이름·경로 값의 정본은 `docs/rules/DATA_CONTRACT_V1.md`다.

### 3.1 공통 형식

정본은 `docs/rules/DATA_CONTRACT_V1.md`이며 아래는 그 값을 옮긴 것이다.

- 규격: Agent Skills 규격을 따른다.
- `name`: 디렉터리 이름과 같다. 소문자·숫자·하이픈만 쓰고 64자 이하다.
- `description`: 무엇을 하는지와 언제 쓰는지를 담고 1024자 이하다. 한국어 본문에 영어 한 문장을 덧붙인다(조정값).
- 위치와 소유
  - 평가 스킬(공동): `skills/tradesentry-scorecard/SKILL.md`, `skills/tradesentry-eval/SKILL.md`
  - 런타임 스킬(M): `skills/tradesentry/SKILL.md`
- 비밀값: 우리 스킬은 키 값을 읽어 출력하거나 기록하지 않는다. 키는 변수 이름으로만 다루고, 주입은 X1에서 채택한 방식을 따른다.
- 봉인 자료의 한계: 봉인 폴더 위치는 문서에 적혀 있어 비밀이 아니다. 개발 에이전트가 같은 OS 사용자로 돌기 때문에 열람을 기술적으로 막지는 못하므로 지시와 기록으로 관리한다. 기술적 차단은 런타임 샌드박스(OpenShell 정책)에만 해당하고, 해시는 변조를 드러낼 뿐 열람을 막지 않는다.

### 3.2 평가 스킬 ① `tradesentry-scorecard`

- 하는 일: 저장소를 `docs/eval/RULEBOOK.md` Part A(채점 규범 기반 프로젝트 자기채점)로 채점한다. 적용 대상은 다음과 같다.
  - 규범 G1~G6(채점 규범의 하드 게이트: 하나라도 실패하면 통과하지 못하는 조건)
  - 채점 지표 20개(`1a`~`1f`, `2a`~`2d`, `3a`~`3f`, `4a`~`4d`). 점수는 0/1/3/5만 쓴다.
  - `2e`: 점수가 아니라 CAP-3(개인 편의류로 판정되면 축 2 점수의 상한을 1점으로 묶는 규칙) 발동 여부 표시다. 축 2(채점 규범의 두 번째 평가 축: 실용성·산업가치·혁신성) 평균의 분모에 넣지 않는다.
  - CAP-1~3(점수 상한 규칙), TIE 규칙(동점 처리), 판정 밴드(총점 구간별 판정), 채점 규범 §7 냄새 목록(좋은 신호·나쁜 신호를 빠르게 가리는 목록)
  - 컴포넌트 삭제 시험과 숫자 등급(정답을 누가 만들었는지와 정답이 개선 과정에 노출됐는지로 매기는 A~D 신뢰 등급). Agent Skills의 삭제 시험 답은 이 사전 §2.1·§3.4를 근거로 쓴다.
- 출력: `artifacts/scorecard/<YYYY-MM-DD>-scorecard.md`(커밋).
- 언제: 2026-09-25(금) MVP 시험 때 첫 결과를 낸다(MVP 합격 체크리스트의 "자기채점 스킬 1회 결과 파일" 항목). 2026-09-27(일)에 다시 채점하고, 2026-09-28(월) 제출 전에 최종 채점한다.
- 경계 규칙
  - 증거를 찾지 못한 지표는 앵커 정의상 낮은 점수를 준다. 추정해서 올리지 않는다.
  - 점수마다 근거 한 줄과 경로를 적는다. 근거 한 줄이 비면 그 판정은 무효로 표시한다.
  - 규범 1d(Agent Skills 활용)의 근거는 이 사전의 상태 열에 남긴 사용 근거 경로다(§5.5). 설치만 한 스킬은 근거로 치지 않는다.

### 3.3 평가 스킬 ② `tradesentry-eval`

- 하는 일: `docs/eval/RULEBOOK.md` Part B(TradeSentry 성능 평가)를 사전 점검 → 실행 → 채점 순으로 수행한다.
- 실행자: 오케스트레이터. 봉인 자료 채점은 `RB-1` 동결 뒤 오케스트레이터가 이 스킬을 실행할 때만 한다.
- 사전 점검
  - 구현 전에 부르면 사전 점검 단계에서 멈춘다. 없는 구성요소 목록(명령·파일·해시)을 보고하고 어떤 실행도 하지 않는다.
  - 동결 조건 가운데 하나라도 빠지면 봉인 자료 채점을 거부한다. 봉인 자료는 holdout40(봉인 평가용 합성 자료 40건)과 `real_sealed`(대표 지표를 재는 실자료 봉인 묶음)다.
  - 이때도 dev20(공개 개발용 합성 자료)·`real_dev`(기준값 조정에 쓰는 실자료 개발 묶음) 실행은 허용한다.
  - 동결 조건은 `policy_v1`(동결 판정 정책, `configs/policy_v1.json`) 승인, `g1`(BACI 국제 무역 자료의 수출 구성 유사도로 고른 비교 대상) 동결 또는 `g0`(고정 목록) 대체 선언, 봉인 자료 해시 커밋(`eval/sealed_manifest.json`)이다.
- 실행(채점 대상 실행)
  - OpenShell 샌드박스 안에서 같은 CLI(`tradesentry <명령>`, 예: `run-case`, `evaluate`, 공통 옵션 `--snapshot`, `--policy`, `--mode`)로 직접 돌린다.
  - NemoClaw 에이전트와 런타임 `tradesentry` 스킬을 거치지 않는다.
  - 모드는 `checklist | agent | full | freeform`이다. 모든 모드에 같은 자료·도구·정책·한도·재시도 규칙을 쓴다.
  - 정답표와 봉인 사례 목록은 샌드박스에 들이지 않는다.
  - 실행 기록은 `artifacts/runs/<run_id>/`에 남긴다(커밋하지 않음). 실패·미실행·timeout·invalid는 분모에 남긴다.
- 채점(정답 대조 채점)
  - 샌드박스 밖에서 독립 채점기 `eval/scorer/`(런타임 모듈을 import하지 않고 따로 만든 채점 프로그램)로 한다: `python -m eval.scorer --run <run_dir>`.
  - 결과는 `artifacts/eval/<run_id>/`(`results.jsonl`, `claims.jsonl`, `summary.md`)에 커밋한다.
- 봉인 자료
  - 봉인 입력은 공식 채점 대상 실행 전용 샌드박스를 새로 만들어 읽기 전용으로 넣는다. 정답표는 어떤 샌드박스에도 넣지 않고 샌드박스 밖 채점기만 읽는다.
  - 채점 전에 해시를 다시 대조한다. 봉인 해시와 실제 파일이 다르면 그 묶음의 채점을 무효로 하고 사용자에게 올린다.
  - `RB-1` 동결 뒤 holdout40과 `real_sealed`는 한 번만 채점한다.
- 등급 표기
  - 대표 지표는 `real_sealed` 사실 주장 오류율이다. 모드별(`freeform`, `full` 각각) 유효 보고서(`execution_status=COMPLETED`)가 최소 20건(조정값)이고 봉인 실행이 끝났을 때만 A등급 대표 숫자로 내세운다. 미달이거나 미완료면 A등급 대표 주장을 보류하고 참고치로만 보고한다.
  - 보조 지표인 holdout40 근거 충족 처리정확도는 C로 표기한다.
  - dev20·`real_dev` 결과는 개선 과정에 노출된 값(D)이며 대표로 올리지 않는다.
- 언제
  - 2026-09-25(금) MVP 시험: dev20 × 비교군 3개(`checklist`·`agent`·`full`) 점수표와 `real_dev`의 `freeform` vs `full` 첫 값. 이 값은 "개발 묶음 값, 대표 숫자 아님"으로 표기한다.
  - 봉인 채점: `RB-1` 동결(2026-09-26(토) 12:00, 조정값) 뒤 시작한다. 시작 목표는 2026-09-26(토) 14:00, 늦어도 2026-09-27(일) 06:00이다.

### 3.4 런타임 스킬 `tradesentry`

- 상태: 구현 단계 산출물이다(2026-09-25(금) 작성 예정, M 소유). 이번 문서 실행에서는 SKILL.md를 만들지 않는다. 인터페이스 계약은 `docs/plan/DEV_PLAN.md`(§5 NemoClaw·스킬 경로와 대체 경로)와 `docs/plan/SCAFFOLD_BRIEF.md`에 적는다.
- 실행 사슬: 운영자 요청 → NemoClaw의 OpenClaw 에이전트 → `tradesentry` 스킬 → OpenShell 샌드박스 안 TradeSentry CLI → 조사 흐름(조사자 → Critic → 수정 1회, NAT로 감쌈) → 도구 5개 → 읽기 전용 SQLite 스냅샷(한 시점에 수집해 동결한 원자료 묶음).
- 증명 방식
  - 채점 대상 실행에는 쓰지 않는다(§3.3).
  - NemoClaw 경로는 따로 증명한다. A/B/C 합성 사례(`controlled_fixture_v0`의 시험 사례로 각각 `MONITOR`/`MAINTAIN`/`HOLD`로 끝나야 한다)와 `real_dev` 경보 몇 건을 처음부터 끝까지 시연하고, 스킬 호출 성공률(시연 요청 가운데 에이전트가 스킬을 불러 CLI 실행까지 이어진 비율)을 잰다.
  - 제출서에는 "정확도 지표에는 영향을 주지 않는다"고 밝힌다.
- 삭제 시험 답: 지워도 정확도 지표는 변하지 않는다. 사라지는 것은 NemoClaw 경로 시연과 스킬 호출 성공률, 그리고 규범 1c·1d의 근거다 `[추론]`.
- **NemoClaw 대체 경로가 발동한 경우**
  1. X1의 제한 시간은 3시간(조정값)이다. 로컬 Docker로 NemoClaw 경로가 서지 않으면 Brev(NVIDIA 원클릭 클라우드 환경)로 옮긴다.
  2. Brev에서도 안 되면 OpenShell만 쓴다(사용자 결정).
  3. 제출서 표기: 어느 단계에서 멈췄는지(로컬 Docker → Brev → OpenShell만)와 이유를 사실대로 적는다. Brev에서 됐으면 시연 환경이 Brev라고 적는다. OpenShell만 쓴 경우 NemoClaw 경로 시연과 스킬 호출 성공률은 "측정하지 못함"으로 적고, 쓰지 않은 기능을 쓴 것처럼 적지 않는다 `[DESIGN]`.
  4. 채점 대상 실행은 처음부터 OpenShell 안 CLI로 돌리므로, 대표 지표와 보조 지표의 실행 경로는 바뀌지 않는다 `[추론]`.
  5. MVP 합격 체크리스트 1번(NemoClaw 경로 항목)은 대체 경로와 사실 표기로 대신한다.
  6. 자기채점(`tradesentry-scorecard`)은 규범 1c 근거가 약해진 것을 그대로 반영한다.

### 3.5 거버넌스 카드 계획(`skill-card-generator`)

- 목적: 우리 스킬 3개(`tradesentry-scorecard`, `tradesentry-eval`, `tradesentry`)마다 능력 범위를 밝히는 거버넌스 카드를 만든다. `skill-card-generator`는 기존 스킬 디렉터리에서 거버넌스 skill card를 만든다 `[사실: DATA_AND_SKILL_INVENTORY.md PART 2-6 설명]`. 카드의 정확한 항목과 형식은 `[미확인]`이다.
- 카드에서 드러나야 할 것 `[DESIGN]`
  - 읽는 입력과 쓰는 출력(`docs/rules/DATA_CONTRACT_V1.md` §10 계획 경로·명령 표의 경로)
  - 외부 전송 여부(런타임은 NVIDIA 추론 엔드포인트만)
  - 금지 사항: `.env`와 봉인 폴더를 읽지 않음, 정답표를 샌드박스에 넣지 않음
  - 생성기 형식에 이 항목이 없으면 카드는 생성기 형식대로 두고, 빠진 항목은 해당 SKILL.md 본문에 있는지 확인한다.
- 언제: 런타임 스킬까지 세 스킬이 모두 생긴 뒤, 2026-09-27(일) README·재현 묶음을 준비할 때 만든다 `[DESIGN]`.
- 저장 위치: 계획 경로·명령 표에 아직 없다. 이 문서에서 새 경로를 정하지 않는다. 위치가 정해지면 그 표와 이 사전을 함께 고친다.
- 봉인: 카드를 만들 때도 봉인 폴더의 경로·내용을 입력에 넣지 않는다. `tradesentry-eval` 카드에는 규칙과 절차만 담긴다.
- 근거로 쓰는 곳: 규범 1d·4a.

## 4. 쓰지 않는 스킬과 이유

| 이름 | 출처 저장소 | 쓰지 않는 이유(요약) | 다시 볼 조건 |
|---|---|---|---|
| `data-designer` | `NVIDIA/skills` | 합성 데이터 생성 스킬이다. holdout40을 이 스킬로 만들면 생성·채점 순환으로 등급이 떨어질 위험이 있고, 생성 주체와 절차도 이미 정해져 있다(§4.1) | 없음 |
| `nemotron-policy-generator` | `NVIDIA/skills` | Nemotron content-safety 가드레일(모델 입력·출력의 유해성을 거르는 장치)용 안전 정책을 만드는 스킬이다. 이번 설계는 NeMo Guardrails(가드레일 규칙 도구)·NemoGuard(안전성 분류 모델)를 넣지 않는다(§4.2) | 가드레일 도입이 사용자 승인으로 결정될 때 |
| `rag-eval`, `rag-perf` | `NVIDIA/skills` | TradeSentry는 RAG(검색 증강 생성) 시스템이 아니고, 대표 지표 채점에 AI 채점자를 두지 않는다(§4.3) | 없음 |

- 이 표의 출처 저장소는 2026-09-24(목) GitHub 트리 대조에서 네 스킬 모두 `NVIDIA/skills`의 `skills/<name>/SKILL.md`로 있음을 확인했다 `[사실: 2026-09-24(목) GitHub 트리 대조]`.

### 4.1 `data-designer`를 holdout40 생성에 쓰지 않는 이유

- 무엇인가: 합성 데이터 생성 파이프라인 스킬이다. 재고 문서는 "평가셋 자동 생성에 활용 가능"하다고 적었다 `[사실: DATA_AND_SKILL_INVENTORY.md PART 2-6]`.
- 이유 1 — 생성·채점 순환으로 등급 하락 위험
  - 채점 규범 §3의 숫자 등급에서 C는 "팀이 독립적으로 제작한 deterministic fixture(생성 규칙과 탐지 규칙이 분리됨)"이다. D는 "우리가 생성하고 우리가 채점한 synthetic(generator 규칙을 detector가 되찾는 구조)"이다 `[사실: SCORING_GOLDEN_RULE.md §3]`.
  - holdout40 보조 지표가 C로 남으려면 생성 규칙과 탐지·채점 규칙이 분리돼야 한다. 범용 생성 파이프라인이 사례와 정답을 함께 만들면, 정답이 생성기의 규칙에서 나오고 그 규칙을 탐지기가 되찾는 순환이 생긴다. 그러면 C가 D로 떨어질 위험이 있다 `[추론]`.
  - 채점 규범 §7도 "우리가 생성한 데이터를 우리가 채점한다"를 나쁜 신호(숫자 등급 D)로 꼽는다.
- 이유 2 — 생성 주체와 절차가 이미 정해져 있다(사용자 결정)
  - holdout40은 모델 트랙과 격리된 Claude 보조 에이전트가 시나리오 명세(`eval/scenarios/SCENARIO_SPEC.md`)와 생성 규칙만 보고 만든다. 결과는 봉인 폴더에 직접 기록한다. Codex(교차 검토와 작은 코드 구현에 쓰는 별도 코딩 에이전트)에게 생성을 맡기지 않는다.
  - 정답표는 운영 코드를 복사하지 않은 독립 구현으로 만든다.
  - 생성 → 봉인 → 해시 등록 → 한 번 채점의 권한 분리 절차는 `docs/eval/RULEBOOK.md` B6(동결과 봉인)과 `docs/rules/PARALLEL_DEV_RULES.md` §6(봉인 자료 규칙)을 따른다. 다른 생성 도구를 끼우면 이 절차의 입력 통제가 흐려진다 `[추론]`.
- 이유 3 — 확인하지 않은 경로: 이 스킬이 안에서 어떤 모델과 외부 호출을 쓰는지 이 문서에서 확인하지 않았다 `[미확인]`. 봉인 대상 내용이 확인되지 않은 경로로 나갈 수 있는 도구는 봉인 절차에 넣지 않는다 `[DESIGN]`.
- 범위: 현재 계획에는 dev20·`controlled_fixture_v0` 생성에도 이 스킬이 없다. 넣으려면 §2.1 기준을 거쳐야 하고, 평가 구성이 바뀌는 일이므로 공용 약속 변경 절차(사용자 승인)를 따른다 `[추론]`.

### 4.2 `nemotron-policy-generator`

- Nemotron content-safety 가드레일용 맞춤 안전 정책(Markdown 정책, JSON 분류 체계, 추론 프롬프트)을 만드는 스킬이다 `[사실: DATA_AND_SKILL_INVENTORY.md PART 2-1 설명]`.
- 재고 문서는 이 스킬을 교육 미션(예선 참가 조건인 NVIDIA DLI 강의 "Securing Agents with NemoClaw and OpenShell") 직결·규범 1b(OpenShell 활용 깊이) 대응으로 적었다. 그러나 설명으로 보면 대상은 content-safety 정책이지 OpenShell 샌드박스 정책이 아니다 `[추론]`. OpenShell 정책 초안은 `generate-sandbox-policy`로 만든다.
- 이번 설계는 NeMo Guardrails·NemoGuard를 넣지 않는다(이유는 `docs/plan/DEV_PLAN.md`). 그래서 이 스킬이 만든 정책을 쓸 곳이 없고, 지워도 나빠지는 지표가 없다.

### 4.3 `rag-eval`, `rag-perf`

- `rag-eval`은 RAGAS(검색 증강 생성의 품질을 재는 평가 도구) 기반 품질 점수를, `rag-perf`는 RAG Blueprint 서버의 프로파일링·부하 시험을 맡는 스킬이다 `[사실: DATA_AND_SKILL_INVENTORY.md PART 2-2 설명]`.
- TradeSentry는 문서를 찾아 답을 만드는 RAG(검색 증강 생성) 시스템이 아니다. 도구 5개가 읽기 전용 스냅샷을 조회한다.
- 대표 지표는 공식 통계 원본(스냅샷 raw 행)과 결정적으로 대조하며, 사람 판정자도 AI 채점자도 두지 않는다. faithfulness 같은 RAGAS 계열 점수는 모델 판정에 기대므로 이 규칙과 맞지 않는다 `[추론]`.

### 4.4 그 밖

- `debug-openshell-cluster`(`NVIDIA/OpenShell`): OpenShell 저장소 `skills/`에 이 사전의 세 스킬과 나란히 있다 `[사실: 2026-09-24(목) GitHub 트리 대조]`. 이름으로 보아 OpenShell 게이트웨이(클러스터) 점검용이다 `[추론]`. 설계 세션의 공식 스킬 목록 밖이므로 공식 사용 행으로는 넣지 않는다. X1에서 Docker 안 게이트웨이 문제가 생기면 §2.7 절차(§2.1 기준으로 판단하고, 채택하면 행을 더한다)로 검토할 후보다.
- 도메인이 다른 공식 스킬(최적화 `cuopt-*`, 영상 `deepstream-*` 계열 등)은 후보로 보지 않았다. 필요가 생기면 `nvidia-skill-finder`로 찾고 §2.1 기준으로 판단한다.
- 스킬은 아니지만 이번 설계에서 넣지 않는 NVIDIA 기술도 있다: Nemotron Nano/Ultra 라우팅, NeMo Guardrails·NemoGuard, NeMo Microservices(NVIDIA NeMo 서비스 제품군. 2026-10-01(목) 일몰 예정이고 후속은 NeMo Platform이라 핵심 기술로 쓰지 않는다 `[사실: NVIDIA-FastCampus-Korea-Agentic-AI-Hackathon-2026.md §9]`). 목록과 이유는 `docs/plan/DEV_PLAN.md`를 따른다.

## 5. 설치와 확인 방법

### 5.1 전제

- 이번 문서 실행에서는 설치하지 않는다. 아래 명령은 구현 단계에서 쓴다(X1을 시작하는 2026-09-24(목)부터).
- `skills` CLI v1.5.16 이상이 필요하다 `[사실: NVIDIA-FastCampus-Korea-Agentic-AI-Hackathon-2026.md §7-1]`. `npx`로 부르므로 Node.js가 있어야 한다 `[추론]`.
- 설치는 개발 환경(에이전트 작업 폴더)에서 한다 `[DESIGN]`. 커스텀 정책을 적용한 샌드박스는 외부 전송을 NVIDIA 추론 엔드포인트로만 여므로, 샌드박스 안에서 스킬을 내려받아 설치하는 방식은 막힌다고 본다 `[추론]`. 런타임 스킬을 NemoClaw 에이전트에 넣는 방식은 X1에서 정한다.
- 설치 명령에 `.env` 내용이나 봉인 폴더를 넘기지 않는다.

### 5.2 공식 스킬 설치 명령

```bash
# NVIDIA/OpenShell 저장소 스킬 (--skill 지정 동작은 [미확인])
npx skills add NVIDIA/OpenShell --skill generate-sandbox-policy
npx skills add NVIDIA/OpenShell --skill openshell-cli
npx skills add NVIDIA/OpenShell --skill debug-inference

# NVIDIA/skills 저장소 스킬
npx skills add NVIDIA/skills --skill nemoclaw-user-guide
npx skills add NVIDIA/skills --skill skill-card-generator
npx skills add NVIDIA/skills --skill nvidia-skill-finder

# 선택(기본은 설치하지 않음, 출처는 [사실: 2026-09-24(목) GitHub 트리 대조])
npx skills add NVIDIA/skills --skill nemo-relay-plugin-observability
```

- 명령 형식: `npx skills add NVIDIA/skills --skill <name>`은 조사 문서에 있는 형식이다 `[사실: NVIDIA-FastCampus-Korea-Agentic-AI-Hackathon-2026.md §7-1]`. `npx skills add NVIDIA/OpenShell --skill <name>`의 `--skill` 지정 동작은 `[미확인]`이다. 조사 문서에는 OpenShell 전용 스킬 전체를 받는 `npx skills add NVIDIA/OpenShell` 형식만 있다.
- `--skill`이 동작하지 않을 때의 대안 `[DESIGN]`: 조사 문서의 `npx skills add NVIDIA/OpenShell`로 저장소 단위로 받는다. 이때 다음을 주의한다.
  - OpenShell 저장소에는 `skills/` 말고도 `.agents/skills/` 아래에 저장소 개발용 스킬 18개(`create-github-pr`, `fix-security-issue` 등)가 있다 `[사실: 2026-09-24(목) GitHub 트리 대조]`. 저장소 단위로 설치하면 쓰지 않을 이 스킬들이 함께 들어올 수 있다 `[추론]`.
  - 설치할 때 세 스킬(`generate-sandbox-policy`, `openshell-cli`, `debug-inference`)만 고를 수 있으면 그것만 고른다(고르는 방식은 `[미확인]`). 고를 수 없으면 설치 뒤 `npx skills list`로 확인하고 세 스킬 밖의 것은 제거한다(제거 명령은 조사 문서에 없어 `[미확인]`).
  - `--skill` 지정 동작은 계속 `[미확인]`이다.
- 에이전트 지정: `--agent claude-code`, `--agent codex` 옵션이 있다 `[사실: NVIDIA-FastCampus-Korea-Agentic-AI-Hackathon-2026.md §7-1]`. 개발 보조 에이전트는 Claude Code에서 돌므로 `npx skills add NVIDIA/skills --skill <name> --agent claude-code` 형식을 쓴다 `[DESIGN]`. OpenClaw 에이전트용 지정값이 있는지는 `[미확인]`이다.
- Claude Code에서는 설치 뒤 `/reload-skills`로 스킬을 다시 읽는다 `[사실: NVIDIA-FastCampus-Korea-Agentic-AI-Hackathon-2026.md §7-1]`.

### 5.3 우리 스킬 설치

- 공개 전(원격이 비공개인 동안): `npx skills add JoeHwangHee/nvidia-hackathon-2026 --skill <name>` 설치는 `[미확인]`이다(저장소 비공개). 실행자는 설치하지 않고 저장소의 SKILL.md를 직접 읽어 따른다 `[DESIGN]`.
  - 평가 스킬: `skills/tradesentry-scorecard/SKILL.md`, `skills/tradesentry-eval/SKILL.md`
  - 런타임 스킬: `skills/tradesentry/SKILL.md`(NemoClaw 에이전트에 넣는 방식은 X1에서 정한다)
- 공개 뒤: 공개 방식(새 저장소 1커밋 / 현재 저장소 공개)은 2026-09-28(월) 오전에 사용자가 정한다. 새 저장소로 가면 위 명령의 저장소 이름이 바뀐다. 공개 뒤 실제로 설치해 보기 전까지 이 명령은 `[미확인]`으로 둔다.

### 5.4 설치·이름 확인

1. 설치 확인: `npx skills list`로 설치된 스킬을 본다. `npx skills check`, `npx skills update` 명령도 있다 `[사실: NVIDIA-FastCampus-Korea-Agentic-AI-Hackathon-2026.md §7-1]`. 각 명령의 출력 형식은 `[미확인]`이다.
2. 이름·출처 재대조(읽기 전용 GitHub 조회)

   ```bash
   gh api "repos/NVIDIA/skills/git/trees/main?recursive=1" --jq '.tree[].path'
   gh api "repos/NVIDIA/OpenShell/git/trees/main?recursive=1" --jq '.tree[].path'
   ```

   - 출력된 경로 목록에서 스킬 이름이 들어간 `SKILL.md` 경로가 있는지 본다.
   - 조회가 실패하면 2026-09-23(수) 대조 결과와 비교하는 것으로 대신하고, 그 사실을 기록한다.
   - 작성자는 조회하지 않았다(오프라인 작성). 검토자가 2026-09-24(목)에 두 명령으로 대조했다. 공식 스킬 7개가 적은 저장소의 `skills/<name>/SKILL.md`에 모두 있었고, §4 표의 4개와 §4.4의 `debug-openshell-cluster`·`cuopt-*`·`deepstream-*`도 있었다. 이름이 어긋난 것은 없었다 `[사실: 2026-09-24(목) GitHub 트리 대조]`.
   - 시점: 설치할 때, 그리고 2026-09-28(월) 제출서를 쓰기 전 `[DESIGN]`.
3. 우리 스킬 형식 확인: frontmatter(SKILL.md 맨 위 `---` 두 줄 사이의 메타데이터)가 §3.1을 지키는지 본다. `name`이 디렉터리 이름과 같은지, 소문자·숫자·하이픈만 쓰고 64자 이하인지, `description`이 1024자 이하인지 확인한다.

### 5.5 상태 열 갱신 규칙 `[DESIGN]`

- 설치하면: 상태에 "설치 확인"과 날짜를 덧붙인다(예: 설치 확인 2026-09-24(목)).
- 쓰면: 쓴 작업과 산출물 경로를 덧붙인다(예: `configs/openshell/policy.yaml` 초안). 이 경로가 규범 1d 자기채점의 근거가 된다.
- 쓰지 않기로 하면: 행을 §4로 옮기고 이유를 적는다.
- 이름이나 출처가 저장소와 다르면: 이 사전을 고치고, 그 이름을 인용한 다른 문서도 함께 고친다.
- 처음 값 "2026-09-23(수) 저장소 대조 확인"은 지우지 않고 남긴다.

## 용어 설명

- **Agent Skills**: AI 에이전트가 읽고 따르는 이식 가능한 작업 지침 묶음. NVIDIA 공식 정의는 "Agent skills are portable instruction sets that extend what an AI agent can do."다 `[사실: NVIDIA-FastCampus-Korea-Agentic-AI-Hackathon-2026.md §7-1]`. Anthropic Agent Skills 규격을 바탕으로 한다.
- **SKILL.md**: 스킬 하나의 지침 파일. 맨 위 frontmatter에 `name`과 `description`을 둔다.
- **frontmatter**: 마크다운 파일 맨 위 `---` 두 줄 사이에 두는 메타데이터 블록.
- **`skills` CLI**: Agent Skills를 설치·갱신하는 Vercel의 명령줄 도구. `npx skills add ...`로 부르며 v1.5.16 이상이 필요하다.
- **npx**: Node.js 패키지를 따로 설치하지 않고 바로 실행하는 명령.
- **공식 스킬**: NVIDIA가 `NVIDIA/skills`·`NVIDIA/OpenShell` 저장소로 공개한 스킬.
- **우리 스킬**: 이 저장소의 `skills/` 아래에 팀이 직접 쓰는 스킬(`tradesentry-scorecard`, `tradesentry-eval`, `tradesentry`).
- **거버넌스 카드(skill card)**: 스킬이 무엇을 할 수 있고 무엇을 읽고 쓰는지 등 능력 범위를 밝히는 카드. `skill-card-generator`가 만든다.
- **OpenShell**: 에이전트를 격리 실행하는 NVIDIA 샌드박스 런타임. 선언적 YAML 정책으로 파일시스템·네트워크·프로세스·추론 경로를 통제한다.
- **샌드박스**: 에이전트나 프로그램이 정해진 권한 안에서만 돌도록 가두는 실행 환경.
- **허용 목록 방식**: 나열한 경로(와 작업 폴더)만 허용하고 나머지를 거부하는 OpenShell 파일시스템 정책 방식.
- **정적 계층·동적 계층**: OpenShell 정책에서 샌드박스를 만들 때 고정되는 부분(`filesystem_policy`·`landlock`·`process`)과 실행 중 다시 불러올 수 있는 부분(`network_policies`·`network_middlewares`).
- **L7 규칙**: HTTP 요청의 method·path·query만 보고(REST 규칙 기준) 허용·거부를 정하는 네트워크 정책 규칙. GraphQL·MCP·JSON-RPC 규칙은 별도 필드(operation·도구 이름 등)를 쓴다. 어느 쪽이든 근거·토큰 같은 본문 값의 뜻을 조건으로 거는 필드는 없다.
- **credential placeholder rewrite**: 샌드박스 안에는 자리표시자만 두고, 게이트웨이가 요청을 내보낼 때 실제 자격증명으로 바꿔 넣는 OpenShell 방식. 샌드박스에 키를 두지 않기 위한 후보다.
- **`inference.local`**: 샌드박스가 보는 OpenShell 추론 주소. 게이트웨이가 연결된 단일 백엔드(provider 1개·모델 1개)로 요청을 전달한다.
- **감사 로그**: 허용·차단 사건의 기록. OpenShell 쪽 기록은 `openshell logs`로 모은다.
- **NemoClaw**: OpenShell 샌드박스 안에서 OpenClaw 에이전트를 돌리는 NVIDIA 참조 스택. 모델·에이전트 하네스·보안 런타임을 한 번에 묶은 배포 묶음이며, 그 보안 런타임이 OpenShell이다. 알파 단계다.
- **OpenClaw**: NemoClaw의 기본 에이전트 하네스.
- **하네스**: 모델을 감싸 도구 호출과 대화 흐름을 돌리는 에이전트 실행 틀.
- **NIM**: 모델과 추론 스택을 묶어 OpenAI 호환 API로 제공하는 NVIDIA 서비스. 이 프로젝트는 호스팅 API(`https://integrate.api.nvidia.com/v1/chat/completions`)를 쓴다.
- **Nemotron**: NVIDIA의 언어 모델 계열. 조사자와 Critic 모두 `nvidia/nemotron-3-super-120b-a12b`를 별도 문맥으로 쓴다.
- **NAT**: NVIDIA NeMo Agent Toolkit(`nvidia-nat`). 조사 흐름을 감싸 실행·추적·프로파일러·사후 평가를 제공한다.
- **MCP**: 에이전트가 외부 도구·자료 서버에 접속하는 표준 프로토콜(Model Context Protocol).
- **OpenTelemetry**: 호출 추적(트레이스) 자료를 남기고 주고받는 공개 표준.
- **RAG / RAGAS**: RAG(검색 증강 생성)는 문서를 찾아 그 내용으로 답을 만드는 방식이고, RAGAS는 그 품질을 재는 평가 도구다.
- **Brev**: 미리 구성된 GPU·소프트웨어 환경을 한 번에 띄우는 NVIDIA 클라우드 플랫폼. NemoClaw 대체 경로의 첫 단계다.
- **X1(세로형 최소 통합 시험)**: 구현 첫날 NemoClaw 에이전트 → 스킬 → 샌드박스 안 CLI 최소 명령 → NIM 호출 1회 → NAT 실행 추적 1건 → 의도적 위반 1건의 차단 로그까지 한 줄로 통과시키는 시험. 제한 시간은 3시간(조정값)이고, 임시 시험 코드는 `spikes/x1/`에 둔다.
- **조사자**: 도구를 골라 조회하고 근거가 붙은 보고서 초안을 쓰는 Nemotron 호출.
- **Critic(검수자)**: 조사자가 받은 근거와 초안만 보고 누락·반대 설명·비교 조건을 지적하는 별도 문맥의 모델 호출. 도구를 부르지 않는다.
- **스냅샷**: 한 시점에 수집해 동결한 원자료 묶음(raw 응답, manifest, SQLite). 모든 조회의 유일한 원천이다.
- **MVP 시험**: 2026-09-25(금)에 최소 기능이 처음부터 끝까지 도는지 합격 체크리스트로 확인하는 시험. 체크리스트는 `docs/plan/ROADMAP.md`에 있다.
- **앵커**: 채점 규범에서 점수 0/1/3/5마다 정한 판정 문구. 2점·4점은 쓰지 않는다.
- **가드레일**: 모델 입력·출력에 규칙을 걸어 유해하거나 벗어난 내용을 거르는 장치. 이번 설계는 NeMo Guardrails·NemoGuard를 넣지 않는다.
- **검증기**: 실행 중에 보고서의 숫자·단위·원본 행·출처를 확인하고 잘못된 보고서를 막는 앱 코드.
- **오케스트레이터**: 작업을 배분하고 병합하는 주관 에이전트.
- **M 트랙·D 트랙**: 구현을 나눈 두 갈래. M(모델 트랙)은 판정 정책·조사 흐름·NVIDIA 연동·그룹핑을, D(데이터 트랙)는 수집·지표·합성/평가 자료·채점기를 맡는다.
- **채점 대상 실행**: 채점에 들어갈 사례를 OpenShell 샌드박스 안에서 TradeSentry CLI로 돌리는 실행.
- **정답 대조 채점**: 채점 대상 실행의 결과를 샌드박스 밖에서 독립 채점기가 정답·원본과 비교하는 일.
- **독립 채점기**: 런타임 모듈을 가져다 쓰지 않고 따로 구현한 채점 프로그램(`eval/scorer/`).
- **룰북·`RB-1`**: 평가 규칙 문서 `docs/eval/RULEBOOK.md`와 그 동결 버전 이름. `RB-1`은 2026-09-26(토) 12:00(조정값)에 동결한다.
- **채점 규범**: 팀이 정한 자기채점 규범 `SCORING_GOLDEN_RULE.md`. 가중치·게이트·앵커는 `[DESIGN]`이다. "규범 1d"처럼 코드에 출처를 붙인다.
- **자기채점**: 채점 규범과 룰북 Part A로 우리 저장소를 스스로 채점하는 일. `tradesentry-scorecard`가 수행한다.
- **컴포넌트 삭제 시험**: 구성요소마다 "지우면 어떤 지표가 나빠지는가"를 적는 점검. 답이 없으면 개수 채우기로 본다.
- **숫자 등급 A~D**: 정답을 누가 만들었는지와 정답이 개선 과정에 노출됐는지로 매기는 숫자 신뢰 등급. 대표 지표(`real_sealed` 사실 주장 오류율)는 주장 조건(§3.3)을 채울 때 A, holdout40 처리정확도는 C, dev20·`real_dev` 결과는 D다.
- **자료 묶음**: `controlled_fixture_v0`(데이터 트랙이 먼저 넘기는 합성 시험자료, A/B/C 사례 포함), `dev20`(공개 개발 자료), `holdout40`(봉인 평가 자료), `real_dev`(기준값 조정에 쓰는 실자료 개발 묶음), `real_sealed`(대표 지표를 재는 실자료 봉인 묶음).
- **봉인 자료**: 개발 중 보지 않도록 저장소 밖(`TRADESENTRY_SEALED_DIR`, 기본값 `~/.tradesentry/sealed/`)에 두고 sha256 해시 목록(`eval/sealed_manifest.json`)만 커밋하는 평가 자료. holdout40 입력과 정답표, `real_sealed` 사례 목록과 채점 표본이 대상이다.
- **모드**: 비교 방식. `checklist`(고정 체크리스트, 모델 없음), `agent`(Critic 없는 Nemotron), `full`(전체 TradeSentry), `freeform`(대표 지표 기준선. 모델이 값을 직접 쓰고 검증기는 기록만 한다).
- **스킬 호출 성공률**: NemoClaw 경로 시연에서 에이전트가 `tradesentry` 스킬을 불러 CLI 실행까지 이어진 비율. 정확도 지표와 별개다.
- **"Skill API"**: 대회 공지에 나오는 표현. NVIDIA 공식 제품명이 아니며, 이 프로젝트는 Agent Skills와 NIM API를 둘 다 써서 대응한다.
- **조정값**: 실측이나 운영 상황에 따라 바꿀 수 있게 정한 수치·이름. 바꾸면 결정 기록에 남긴다.
