# TradeSentry

## 프로젝트 개요

관세청 수입통계를 한 시점에 수집해 고정한 스냅샷(HS(국제 품목분류 코드) 8504 아래 6자리 품목(HS6) 4개 × 상대국 16개 × 2022~2024년 36개월)에서, kg당 단가와 상대국 점유율이 전년 같은 달보다 크게 바뀐 경우를 경보로 잡는다. 경보마다 Nemotron(NVIDIA 언어 모델) 조사자와 별도 문맥의 검수자(Critic)가 정해진 조회 도구 5개로 반증을 시도하고, 담당자의 다음 업무를 검토 유지(`MAINTAIN`)·모니터링(`MONITOR`)·자료 보류(`HOLD`) 가운데 하나로 제안한다. 부정·위법·원산지 판정이나 실제 통관 조치가 아니다.

2026 NVIDIA Korea Agentic AI Hackathon 예선 제출물이다(마감 2026-09-28(월) 23:59 KST). 한 사람이 로컬에서 돌리고 추론만 NVIDIA 클라우드 API(NIM)를 쓰는 데모이며, 여러 사용자·계정·권한·실시간 수집·운영 배포는 없다. NVIDIA 스택은 NemoClaw(OpenShell 위에서 에이전트를 돌리는 NVIDIA 참조 스택), OpenShell(에이전트를 격리해 돌리는 샌드박스 런타임), NAT(에이전트 실행을 추적하고 평가하는 도구 모음), NIM을 쓴다. 구현은 Claude 보조 에이전트가 모델 트랙(M: 판정 정책·조사 흐름·NVIDIA 연동)과 데이터 트랙(D: 수집·지표·평가 자료·채점기)으로 나눠 동시에 하고, 작업 성격별 도메인 검토 에이전트와 Codex(OpenAI의 코딩 에이전트 CLI)가 검토한다.

## 문서 구조

```
nvidia-hackathon-2026/
├── CLAUDE.md                          ← Claude Code가 먼저 읽는 프로젝트 안내
├── AGENTS.md                          ← Codex가 먼저 읽는 프로젝트 안내(CLAUDE.md와 내용이 같다)
├── docs/
│   ├── README.md                      ← 계획 문서 색인: 문서별 역할, 읽는 순서, 문서끼리 다를 때의 우선순위
│   ├── plan/
│   │   ├── DEV_PLAN.md                ← 개발 플랜: 실행 사슬, OpenShell 정책 요건, 조사·판정 규칙, 설계 결정 기록
│   │   ├── ROADMAP.md                 ← 작업 ID·선후 관계·날짜·완료 기준, MVP(최소 기능 제품) 합격 체크리스트, 사용자 확인 항목
│   │   ├── SCAFFOLD_BRIEF.md          ← 앱 뼈대(S0) 외부 자문용 명세서와 열린 질문 Q1~Q21
│   │   └── UNITS.md                   ← 최소 단위 65개의 정본: 단위 ID·도메인명·파일·소유·조립 판정 후보와 조립 점검 절차
│   ├── rules/
│   │   ├── DATA_CONTRACT_V1.md        ← 공용 자료 계약(값의 정본): 객체·필드·상태값·ID·단위·자릿수·경로·명령
│   │   ├── PARALLEL_DEV_RULES.md      ← 두 트랙의 파일 소유, 인수 조건, 공용 약속(두 트랙이 함께 기대는 약속) 변경, 봉인 자료(개발 중 보지 않도록 저장소 밖에 두는 평가 자료), 실자료 분할, 브랜치·PR(GitHub 변경 요청)
│   │   └── AGENT_OPS.md               ← 실행자 선택, Codex 사용, 검토자와 판정, PR 병합, 증거 규칙
│   ├── eval/
│   │   ├── RULEBOOK.md                ← 평가 룰북: Part A 자기채점, Part B 성능 평가와 채점 규칙
│   │   ├── RESULTS.md                 ← 결과표(R1): 두 봉인 묶음의 대표·보조 지표와 Wilson 95% 구간·등급, A등급 주장 조건 판정, B7 공개 값, 한계. 숫자는 커밋된 채점 요약에서만 옮긴다
│   │   └── SKILL_DICTIONARY.md        ← 쓰는 스킬(Agent Skills 형식의 에이전트용 작업 절차)과 설치·이름 확인 방법
│   ├── submission/                    ← 제출 폼 입력용 최종본 SUBMISSION_FORM.md(신청 폼 장문 칸 3개·서비스 파일 한 쪽 내용. 공개 저장소 URL은 P2 뒤 채운다)와 서비스 파일 템플릿 service_file.html
│   ├── architecture.md                ← 실행 사슬과 구성요소별 정본 위치
│   ├── business-rules.md              ← 도메인 규칙별 정본 위치
│   ├── security.md                    ← 키·샌드박스·봉인 통제별 정본 위치
│   ├── standards.md                   ← 작업 규칙별 정본 위치와 문서 작성 규칙
│   ├── engineering-notes.md           ← 이 저장소에서 겪었거나 계획 문서로 확인한 함정과 대응
│   ├── operations.md                  ← 처음 준비, 명령·환경·실행 절차별 정본 위치
│   ├── contracts.md                   ← CLI·스킬·도구·보고서·채점기 인터페이스별 정본 위치
│   └── tracking/
│       ├── status.md                  ← 지금 된 것, 남은 일, 사용자 결정 대기
│       ├── decisions/                 ← 결정 기록과 색인 index.md(2026-09-23(수) 설계 세션의 결정은 개발 플랜 §13)
│       └── findings.md                ← 지금 풀 수 없는 문제
├── skills/
│   ├── tradesentry-scorecard/SKILL.md ← 평가 스킬 ①: 룰북 Part A로 자기채점
│   ├── tradesentry-eval/SKILL.md      ← 평가 스킬 ②: 룰북 Part B 성능 평가 실행
│   └── */<이름>-card.md               ← 우리 스킬 3개(tradesentry·tradesentry-scorecard·tradesentry-eval)의 거버넌스 카드(공식 스킬 skill-card-generator의 카드 형식. 정본은 스킬 사전 docs/eval/SKILL_DICTIONARY.md §3.5)
├── pyproject.toml, uv.lock, .python-version ← Python 3.12.13 가상환경(uv)과 lock. 시험은 `uv run --locked python -m unittest discover -s tests -v`
├── src/tradesentry/                   ← 앱 패키지 15개와 단위 파일(단위 표 docs/plan/UNITS.md). ingest.py는 관세청 API 수집기와 스냅샷 검사(표준 라이브러리만 쓴다) `ui/`는 담당자용 화면(진입 스크립트 `ui/ui_app.py`, 한국어/영어)
├── tests/                             ← unittest 시험(네트워크·키 없이 돈다). 단위 골든 시험은 tests/units/{단위 ID}/
├── configs/collection_plan.json       ← 수집 설정. snapshot_id가 v2 스냅샷을 가리킨다
├── configs/openshell·nat·model/       ← OpenShell 정책, NAT 워크플로, 프롬프트·모델 설정 자리(로드맵 MT4·MT5가 채운다)
├── eval/dev/oracle_ABC.json           ← 개발용 기대 판정 사례 A·B·C
├── eval/sealed/                       ← 봉인 원본 커밋 사본(holdout40·real_sealed. 최종 채점과 seed 공개 뒤 커밋, 해시 목록과 전체 재대조)
├── eval/scorer/, eval/datagen/        ← 독립 채점기와 평가 자료 도구. 채점기는 tradesentry를 import하지 않는다
├── artifacts/                         ← 커밋 증거물(증거 복사한 커밋 사본과 X1 증거 artifacts/openshell/)
├── spikes/x1/                         ← X1 임시 시험 코드. 앱에 섞지 않는다
├── data/snapshots/                    ← 스냅샷별 manifest(수집 요청 목록)·검사 결과. 원자료와 SQLite는 커밋하지 않는다
├── data/reference/                    ← 품목표와 BACI(CEPII가 정리한 국가 간 연간 무역 자료) 참고 자료
├── outputs/                           ← 실행별 출력 폴더(커밋하지 않는다. 이름 규칙은 자료 계약 §10.3). 봉인 묶음 실행 사슬의 출력은 `outputs/sealed/`에 두고, 봉인 묶음마다 금지 해제 조건(그 묶음의 정답 대조 채점이 끝나고, `real_sealed`이면 표본 추출 seed 공개 기록까지 있는 때. 자료 계약 §10.3 N10) 전에는 그 묶음 출력을 열지 않는다
├── scripts/g4_nim_toolcall_probe.py   ← NIM tool call(모델이 도구 호출을 구조화된 형식으로 요청하는 기능) 왕복 확인
├── scripts/make_service_file.sh       ← 서비스 파일 한 쪽(pdf·docx) 생성. 인자는 공개 저장소 URL, 출력은 outputs/submission_service_file-{시각}/
├── .env.example                       ← `.env` 양식. API 키 칸은 비어 있고 모델 이름 같은 기본값만 있다
└── *.md(루트의 나머지)                ← 이전 설계·조사 기록. 사실 출처로 인용만 하고 고치지 않는다(목록은 docs/README.md §4)
```

## 절대 규칙

어기면 되돌릴 수 없거나 평가 숫자를 믿을 수 없게 되는 것만 모았다. 괄호 안이 정본이다.

1. **비밀값**: API 키(`NVIDIA_API_KEY`, `DATA_GO_KR_SERVICE_KEY`)의 원본은 `.env`에 둔다. 에이전트는 `.env`를 열거나 출력하지 않는다. 키가 필요한 프로그램은 실행 프로세스가 환경변수로 읽는다. 사본은 설계된 주입 경로(OpenShell 게이트웨이의 provider(등록한 자격 증명 묶음) 저장소, 샌드박스 안에서 root로 도는 감독 프로세스, NemoClaw 설정, 옮기면 Brev(NVIDIA 클라우드 개발 환경) 호스트)에만 생기고, 에이전트는 사본 위치도 열거나 출력하지 않는다. 키 값을 코드·문서·커밋·PR(GitHub 변경 요청)·로그·trace(실행 추적 기록)·다른 에이전트와 Codex에 주는 지시에 넣지 않고, 에이전트와 그 자식 프로세스(샌드박스 사용자 권한)가 읽을 수 있는 곳에 두지 않는다. (`docs/rules/PARALLEL_DEV_RULES.md` §10.2, 결정 기록 `20260924-2010-user-decision-key-rule-interpretation.md`)
2. **동결 스냅샷**: `data/snapshots/kcs_202201_202412_v1`과 `_v2`에 수집기의 `plan`·`collect`를 돌리지 않는다. 동결한 스냅샷은 고치지 않고, 설정이 바뀌면 새 `snapshot_id`로 새 스냅샷을 만든다. (같은 문서 §10.1)
3. **봉인 자료와 정답**: 봉인 자료(개발 중 보지 않도록 저장소 밖 봉인 폴더에 두는 holdout40·`real_sealed` 평가 자료)는 최종 정답 대조 채점이 끝날 때까지 저장소에 넣지 않고 해시만 커밋한다. 원본은 채점이 끝난 뒤 커밋한다(`docs/plan/ROADMAP.md` R1). 개발 에이전트와 Codex는 봉인 폴더를 열지 않는다. 정답표는 어떤 샌드박스에도 넣지 않고, 정답 대조 채점은 샌드박스 밖 독립 채점기만 한다. (`docs/rules/PARALLEL_DEV_RULES.md` §6, `docs/eval/RULEBOOK.md` B6)
4. **공용 약속**: 두 트랙이 함께 기대는 약속(자료 형식, 상태값, 기준값, 도구 한도, 품목·국가, 평가 구성, 제출서 주장 문구)은 사용자 승인 없이 바꾸지 않는다. 이름·상태값·키·경로·명령은 `docs/rules/DATA_CONTRACT_V1.md`와 글자까지 같게 쓴다. (`docs/rules/PARALLEL_DEV_RULES.md` §4)
5. **평가 동결**: 룰북 `RB-1`(평가 룰북의 첫 동결 버전) 동결 뒤에는 채점 규칙을 새 룰북 버전과 사유로만 바꾸고, 결과를 본 뒤 규칙·판정 정책·검증기·채점기를 유리하게 고치지 않는다. 봉인 묶음은 한 번만 채점하고, 실패·시간 초과·무효 실행도 분모에 남긴다. (`docs/eval/RULEBOOK.md` B5·B6)

`main`에는 작업 브랜치 → PR → 검사·검토 → squash 병합(PR의 여러 커밋을 하나로 합쳐 넣는 방식, 조정값)으로만 넣고 직접 push하지 않는다. 원격은 비공개 `origin`만 쓰며, 저장소 공개 전환과 설정 변경은 사용자가 정한다. (`docs/rules/PARALLEL_DEV_RULES.md` §9, `docs/rules/AGENT_OPS.md` §5)

## 작업 전에 읽을 것

- 모든 작업: `docs/README.md`, `docs/standards.md`, `docs/engineering-notes.md`, `docs/tracking/status.md`
- 객체·필드·상태값·ID·단위·자릿수·경로·명령을 쓰기 전: `docs/rules/DATA_CONTRACT_V1.md`의 해당 절. 다른 문서에 같은 값이 보여도 이 문서에서 가져온다
- 단위 파일이나 출력 경로를 만들기 전: `docs/plan/UNITS.md`와 `docs/rules/DATA_CONTRACT_V1.md` §10.3(이름·출력 규칙)
- 판정 정책·조사 흐름·도구·검증기를 건드리기 전: `docs/plan/DEV_PLAN.md` §6·§7
- 채점기·평가 묶음·산문 패턴 목록을 건드리기 전: `docs/eval/RULEBOOK.md` Part B와 `skills/tradesentry-eval/SKILL.md`
- OpenShell 정책·샌드박스·키 주입을 다루기 전: `docs/plan/DEV_PLAN.md` §4·§5.3·§5.4
- 봉인 자료나 실자료 분할(개발용 `real_dev`와 봉인용 `real_sealed`)에 닿기 전: `docs/rules/PARALLEL_DEV_RULES.md` §6·§7, `docs/rules/AGENT_OPS.md` §1.3·§1.4
- 다른 에이전트나 Codex에 일을 맡기기 전: `docs/rules/AGENT_OPS.md` §1·§2
- 앱 뼈대(S0)를 만들기 전: `docs/plan/SCAFFOLD_BRIEF.md`와 외부 자문 회신, `docs/rules/AGENT_OPS.md` §6
- 수집기를 돌리거나 스냅샷 폴더를 만지기 전: `docs/engineering-notes.md`의 스냅샷 항목

## 문제가 생기면

아래는 그 작업을 멈추고 바로 사용자에게 알린다. 전체 목록은 `docs/rules/AGENT_OPS.md` §4.5와 `docs/plan/ROADMAP.md` §6.4이고, 평가·채점 중에는 `skills/tradesentry-eval/SKILL.md`의 "멈추고 사용자에게 올리는 경우"와 `docs/eval/RULEBOOK.md` B3 채점 절차 0도 따른다.

- 키·토큰이 커밋·PR·로그·trace에 들어갔거나 들어갔을 수 있을 때
- 봉인 자료나 정답표가 개발 에이전트·Codex·채점 대상 실행 샌드박스에 드러났거나, 봉인 묶음 출력(`outputs/sealed/` 아래, 내려받기 전 샌드박스 작업 폴더의 봉인 실행 출력, 봉인 묶음을 채점한 채점기 출력 폴더)이 금지 해제 조건 전에 열렸거나, 봉인 해시가 실제 파일과 다를 때
- 동결 스냅샷의 원자료(raw 응답)나 SQLite가 바뀌었을 수 있을 때(git으로 되돌릴 수 없다), 또는 원자료 결합 해시나 `normalized_sha256`(정규화한 스냅샷 내용의 해시) 대조가 기록과 다를 때(평가 스킬 ② 사전 점검 단계 4의 3번, `docs/engineering-notes.md`의 스냅샷 항목)
- 공용 약속을 바꿔야 할 때. 승인 전에는 그 약속에 기대는 작업만 멈춘다
- X1(구현 첫날 NemoClaw부터 차단 로그까지 한 줄로 통과시키는 통합 시험)에서 키 주입 방식 두 가지가 모두 실패하거나, 공식 채점 대상 실행 전용 샌드박스의 최소 시험이 예측과 다를 때

그 밖의 문제는 풀어 보고, 지금 풀 수 없으면 `docs/tracking/findings.md`에 적는다.
