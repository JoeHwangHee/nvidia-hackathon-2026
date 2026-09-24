# 보안 정책

인증·권한 시스템은 없다(한 사람이 로컬에서 돌리는 데모). 지키는 대상은 API 키 두 개(`NVIDIA_API_KEY`, `DATA_GO_KR_SERVICE_KEY`), 봉인 평가 자료와 정답표, 동결 스냅샷이다. 격리는 OpenShell(에이전트를 격리해 돌리는 NVIDIA 샌드박스 런타임)의 정책으로 한다. 규칙의 정본은 아래 문서들이다.

| 대상 | 정본 |
|---|---|
| API 키의 보관·전달·검사, 키가 드러났을 때의 처리 | `docs/rules/PARALLEL_DEV_RULES.md` §10.2·§10.3 |
| 샌드박스 안에 키를 두지 않는 주입 방식: credential placeholder rewrite(샌드박스 밖 게이트웨이가 요청 속 자리표시자를 실제 키로 바꿔 넣는 방식) 또는 `inference.local`(OpenShell 게이트웨이가 제공하는 관리형 추론 주소). X1(구현 첫날의 세로형 최소 통합 시험)에서 실제로 성공한 방식만 채택한다 | `docs/plan/DEV_PLAN.md` §4.6·§5.3 |
| OpenShell 정책 요건 (a)~(e), 정적·동적 계층, 파일시스템 허용 목록 방식 | 같은 문서 §4.1~§4.3 |
| 요건별 의도적 위반 시험과 증거(시험표, 감사 로그 발췌) | 같은 문서 §4.4 |
| 두 통제의 구분: 저장소 경로 차단과 저장소 밖 봉인 격리 | 같은 문서 §4.5, `docs/rules/PARALLEL_DEV_RULES.md` §6.5 |
| 시연 샌드박스의 추가 통제 | `docs/plan/DEV_PLAN.md` §4.8 |
| 봉인 자료의 위치, 해시 기록, 권한 분리, 기술적으로 막지 못하는 한계 | `docs/rules/PARALLEL_DEV_RULES.md` §6, `docs/rules/DATA_CONTRACT_V1.md` §12, `docs/plan/DEV_PLAN.md` §9.8 |
| 실행자(개발 에이전트·봉인 자료 생성 에이전트·Codex·검토자)별 권한과 lethal trifecta(민감 자료 읽기·외부 입력 수용·외부 전송이 한 실행 경로에 겹치는 위험) | `docs/rules/AGENT_OPS.md` §1.3·§1.4 |
| Codex에 넘기지 않는 것 | 같은 문서 §2.3 |
| 증거·결과 파일에 비밀값과 로컬 절대경로를 넣지 않는 법 | 같은 문서 §7.6 |
| 감사 기록: `openshell logs`의 허용·차단 이벤트 수집(요건 (d))과 시험표, 감사 저장소로 쓰지 않는 것 | `docs/plan/DEV_PLAN.md` §4.1·§4.4·§12.2 |
| 공식 채점 때 봉인 입력을 넣는 방식과 순서(`real_sealed`는 지금 안에서 샌드박스 밖 실행기가 사례 식별자만 넘긴다. 룰북 부록 40번 사용자 확인 대기) | `skills/tradesentry-eval/SKILL.md`의 "봉인 자료 취급", `docs/eval/RULEBOOK.md` B5 |
