# 시스템 구성

## 실행 사슬

운영자 → NemoClaw(OpenClaw(에이전트 실행 틀) 에이전트를 OpenShell 위에서 돌리는 NVIDIA 참조 스택) → 런타임 스킬 `tradesentry`(에이전트가 CLI를 부르는 데 쓰는 Agent Skills 형식의 작업 절차) → TradeSentry CLI(OpenShell 샌드박스 안. OpenShell은 에이전트를 격리해 돌리는 NVIDIA 샌드박스 런타임이다) → 조사 흐름(NAT, 곧 NVIDIA 에이전트 도구 모음으로 감싸 실행을 추적) → 조회 도구 5개 → 읽기 전용 SQLite 스냅샷.

- 조사 흐름 안에서는 Nemotron(NVIDIA 언어 모델) 조사자가 도구로 근거를 모아 초안을 쓰고, 별도 문맥의 검수자(Critic)가 지적한 뒤 수정 1회를 거친다. 검증기(실행 중 보고서의 숫자·단위·근거를 검사하는 코드)가 `freeform`(모델이 사실 주장의 값을 직접 쓰는 기준선 비교 모드)을 뺀 모든 모드에서 잘못된 보고서를 막고, 통과한 한국어 보고서와 실행 기록(trace)이 남는다.
- 모델 호출은 샌드박스 밖 OpenShell 게이트웨이(정책을 적용하고 요청을 중계하는 구성요소. 키도 여기서 붙는다)를 거쳐 NIM(NVIDIA 클라우드 추론 API)의 Nemotron으로 나간다. 키는 샌드박스 안에 없다.
- 채점 대상 실행(점수에 들어가는 실행)은 NemoClaw를 거치지 않고 OpenShell 안 CLI를 직접 부른다. NemoClaw 경로는 시연과 스킬 호출 성공률로 따로 증명한다.
- 정답 대조 채점은 샌드박스 밖 독립 채점기(`eval/scorer/`)가 한다. 채점기는 런타임 코드를 import하지 않는다.
- 외부 의존은 셋이다. 관세청 수출입통계 공개 API(data.go.kr)는 수집 때만 쓰고 조사 중에는 부르지 않는다. BACI(CEPII가 정리한 국가 간 연간 무역 자료)는 비교 대상 `g1`(BACI 수출 구성이 닮은 비교국 5개국)을 고르는 데와 문맥 표시에만 쓰고, 관세청 지표와 한 지표 안에서 섞지 않는다. NIM은 모델 호출에 쓴다.

위 사슬에 드는 구성요소, 경로, 명령 이름의 정본은 아래 문서들이다.

| 알고 싶은 것 | 정본 |
|---|---|
| 구성요소별 역할과 연결 | `docs/plan/DEV_PLAN.md` §3.1 |
| 채점 대상 실행 경로와 시연 경로의 차이 | 같은 문서 §3.2·§5.1 |
| 검증기와 NAT 사후 평가의 역할 구분 | 같은 문서 §3.3 |
| 넣지 않는 구성요소와 이유 | 같은 문서 §3.4 |
| 개발·실행 환경(macOS, Docker 안 OpenShell 게이트웨이, Python 3.12) | 같은 문서 §3.5 |
| 샌드박스 종류(채점 대상 실행용·공식 채점 대상 실행 전용·시연용)와 각각에 들어가는 것 | 같은 문서 §4 머리말·§4.3·§4.5·§4.8, `docs/plan/SCAFFOLD_BRIEF.md` §4.4.1 |
| NemoClaw가 안 될 때의 대체 경로(Brev, 곧 NVIDIA 원클릭 클라우드 개발 환경으로 옮기기, 그다음 OpenShell만) | `docs/plan/DEV_PLAN.md` §5.4 |
| 모듈 역할과 소유 트랙 | 같은 문서 §10.2·§10.3, `docs/rules/PARALLEL_DEV_RULES.md` §1.2 |
| 계획된 경로·명령 표 | `docs/rules/DATA_CONTRACT_V1.md` §10 |
| 앱 폴더 구조처럼 앱 뼈대(S0)에서 정할 설계 | `docs/plan/SCAFFOLD_BRIEF.md` §2.6·§5.2·§5.3 |
| 평가 흐름(사전 점검 → 실행 → 채점 → 결과 보고)과 봉인 묶음(개발 중 보지 않도록 봉인한 평가 자료 묶음)의 샌드박스 밖 실행기(샌드박스 밖에서 봉인 해시를 대조하고 사례를 샌드박스 안 CLI에 넘기는 프로그램) | `skills/tradesentry-eval/SKILL.md`, `docs/eval/RULEBOOK.md` Part B, `docs/plan/ROADMAP.md` §2.4(MT7) |
