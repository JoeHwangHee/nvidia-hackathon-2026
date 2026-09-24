# 작업 규칙

어기면 병합이 막히거나 다른 트랙·평가가 깨지는 규칙이다. 정본은 `docs/rules/PARALLEL_DEV_RULES.md`(두 트랙이 함께 일하는 규칙)와 `docs/rules/AGENT_OPS.md`(에이전트에게 일을 맡기고 검토·병합하는 규칙)다. 코드 규약은 앱 뼈대(S0) 자문 명세서에 모여 있다.

| 규칙 | 정본 |
|---|---|
| 모델 트랙(M)·데이터 트랙(D)의 파일 소유, 공동 영역, 표에 없는 경로 | `docs/rules/PARALLEL_DEV_RULES.md` §1 |
| 합성 시험자료를 먼저 넘기는 방식, D → M 인수 조건 | 같은 문서 §2·§3 |
| 공용 약속 목록과 변경 승인 절차(처음 정하는 값도 같은 승인을 거친다) | 같은 문서 §4, `docs/rules/DATA_CONTRACT_V1.md` §13 |
| 혼자 결정하면 안 되는 것 | `docs/rules/PARALLEL_DEV_RULES.md` §5 |
| 봉인 자료, 실자료 분할 | 같은 문서 §6·§7 |
| 결정 기록의 항목과 쓰는 규칙 | 같은 문서 §8. 파일 이름 규칙은 `docs/tracking/decisions/`의 첫 기록 |
| 브랜치 이름, PR 제목, 커밋 메시지, 병합 방식 | 같은 문서 §9 |
| 스냅샷·키 보호, 비밀값·로컬 경로 검사 | 같은 문서 §10 |
| 의존성 관리: Python 3.12 가상환경과 uv(파이썬 패키지·가상환경 관리 도구), 버전 고정 파일(lock), NAT 버전 고정, 수집기는 표준 라이브러리만 | `docs/plan/DEV_PLAN.md` §3.5, `docs/plan/SCAFFOLD_BRIEF.md` §4.1 |
| 코드 규약: 정책 수치·스냅샷 경로를 코드에 박지 않기, Decimal 사사오입, 모델 입력 통제, 예산의 코드 강제, 상태 분리, 보고서 문구 | `docs/plan/SCAFFOLD_BRIEF.md` §4.10, `docs/rules/DATA_CONTRACT_V1.md` §11.3 |
| 채점기의 독립성: 런타임 모듈을 import하지 않고, `metrics.py` 구현자와 다른 실행자가 만든다 | `docs/plan/ROADMAP.md` §2.3(DT8), `docs/eval/RULEBOOK.md` B3 |
| 실행자 선택(Claude 보조 에이전트, Codex headless, 도메인 검토자) | `docs/rules/AGENT_OPS.md` §1 |
| Codex 명령 형식, 넘기지 않는 것, 제한 시간, 결과 판단 | 같은 문서 §2 |
| 작업 성격별 검토자, 판정 형식, 수정·재검토 횟수 | 같은 문서 §3·§4 |
| PR 병합 조건, 절차, 본문 양식 | 같은 문서 §5 |
| 앱 뼈대(S0) 외부 자문의 멈춤·재개 | 같은 문서 §6 |
| 증거, 종료 코드 캡처, 구현 에이전트의 보고 형식 | 같은 문서 §7 |
| 작업별 완료 기준과 공통 완료 기준(시험 명령 포함) | `docs/plan/ROADMAP.md` §2.1 |

## 문서 작성

- 문서·PR 본문·결정 기록은 한국어로 쓰고, 전문 용어와 약어는 처음 나올 때 뜻을 괄호로 함께 적는다(예: "trace(실행 추적 기록)"). 상태값·모드·키 이름 같은 값은 번역하지 않고 자료 계약의 글자 그대로 쓴다.
- 사실 주장에는 근거 태그(`[사실]`·`[추론]`·`[DESIGN]`·`[미확인]`)를 붙인다. 태그의 뜻은 `docs/rules/PARALLEL_DEV_RULES.md` 머리말에 있다.
- 경로는 저장소 루트 기준 상대경로로 쓰고, 개발 기계의 절대경로를 적지 않는다(예외: 봉인 폴더 기본값 `~/.tradesentry/sealed/`). 커밋 전 검사 방법은 `docs/rules/PARALLEL_DEV_RULES.md` §10.3이다.
