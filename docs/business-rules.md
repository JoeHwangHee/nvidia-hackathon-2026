# 도메인 규칙

TradeSentry의 도메인 규칙은 아래 정본에만 있다. 같은 규칙이 여러 문서에 보이면 `docs/README.md` §3의 우선순위(자료 계약 > 룰북 > 개발 플랜 > 로드맵 > 나머지)를 따르고, 이름·상태값·단위·자릿수는 `docs/rules/DATA_CONTRACT_V1.md`에서만 가져온다.

| 규칙 | 정본 |
|---|---|
| 용어, 객체(스냅샷·관측치·지표·사례·비교 대상 집합)와 필드, 객체 사이 관계 | `docs/rules/DATA_CONTRACT_V1.md` §2 |
| 관측치 행 규칙: 상대국 HS6 월 금액·중량의 원천(부모 HS6 행), 전체국가(`ALL`) 분모와 중복 제거, 총계 행 취급 | 같은 문서 §2.3.2 |
| 상태값 집합(판정·실행·관측·승인 유효)과 뜻 | 같은 문서 §3 |
| 지표 공식(단가 U, 단가 변화율 r_U, 점유율 s, 점유율 변화 d_s, HS10 구성효과 분해)과 0·미상 처리 | `docs/plan/DEV_PLAN.md` §6.1·§6.2 |
| 신호별 판정표와 사례 판정 집계 | 같은 문서 §6.3·§6.4 |
| 조회 도구 5개, 공통 출력 봉투, 도구·모델 예산 | 같은 문서 §6.5·§6.6, `docs/rules/DATA_CONTRACT_V1.md` §5 |
| 조사 흐름(조사자 → 검수자 → 수정 1회 → 최종 검증) | `docs/plan/DEV_PLAN.md` §6.7 |
| typed claim(정해진 필드로 쓰는 사실 주장), 보고서, 검증기, 실행 상태, 모의 승인 | 같은 문서 §7, `docs/rules/DATA_CONTRACT_V1.md` §6·§8·§9 |
| 단위, 표시 자릿수, 반올림 | `docs/rules/DATA_CONTRACT_V1.md` §11 |
| 비교 대상 집합 `g0`·`g1` | `docs/plan/DEV_PLAN.md` §8, `docs/rules/DATA_CONTRACT_V1.md` §2.3.6 |
| 탐지 임계값과 승격 규칙 같은 정책 수치(승인 뒤 `configs/policy_v1.json`) | `docs/plan/DEV_PLAN.md` §6.2, `docs/plan/ROADMAP.md` §6.3 |
| 평가 자료 묶음, 비교 모드, 대표 지표, 숫자 등급 | `docs/plan/DEV_PLAN.md` §9, `docs/eval/RULEBOOK.md` Part B |
| 쓰면 안 되는 표현(부정·위법·원산지 단정 등)과 정직한 주장 규칙 | `docs/plan/DEV_PLAN.md` §7.8·§12.2 |
