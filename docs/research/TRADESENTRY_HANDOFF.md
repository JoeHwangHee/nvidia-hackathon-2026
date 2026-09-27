---
title: TradeSentry 세션 인계 (handoff)
written: 2026-09-23 세션 종료 시점
read_order: 이 문서 → TRADESENTRY_FACTS_MEMO.md → Pasted markdown.md(개발계획)
---

# TradeSentry 세션 인계

## 0. 지금 상태

실데이터 수집·검증 기반(G1~G3 관문)은 끝났다. 사용자는 **플랜을 새로 짜는 중**이라 기존 일정표와 기한을 모두 지웠다. 남긴 날짜는 개발계획 85행의 "9/28 제출 점검을 내부 목표" 하나다. **다음 세션의 첫 일은 사용자와 새 플랜을 짜는 것**이다.

TradeSentry 요지: 관세청 수입통계에서 단위가치(금액 ÷ 순중량, USD/kg)와 상대국 점유율의 전년동월 급변을 경보로 잡고, Nemotron 조사자와 별도 문맥의 Critic(검수 역할)이 제한된 도구로 반증을 시도해 `검토 유지 / 모니터링 / 자료 보류` 중 하나로 판정한다. 부정·위법 판정이 아니다.

## 1. 먼저 읽을 파일 (현행)

| 파일 | 내용 |
|---|---|
| `TRADESENTRY_FACTS_MEMO.md` | 실측 사실 메모: API 동작, v2 스냅샷 결과, HS6 후보 표, G4 관찰. 새 플랜의 근거 자료 |
| `Pasted markdown.md` | TradeSentry 개발계획(상위 문서). 리치텍스트 붙여넣기 흔적(`\*\*`, `&#xC785;` 같은 HTML 엔티티)이 섞여 있다. §9 일자표를 지워서 절 번호가 8 → 10 으로 건너뛴다(의도: `eval/dev/oracle_ABC.json` 이 "10절"을 참조). 링크된 `research/*.md` 3개는 저장소에 없다 |
| `TRADESENTRY_TEAM_SPLIT_DECISIONS.md` | 2인 분담 합의안(M = 모델·정책·워크플로, D = 데이터·지표·평가자료). 아직 합의 전. 착수 순서 절과 기한 열은 지웠다 |
| `NVIDIA-FastCampus-Korea-Agentic-AI-Hackathon-2026.md` | 대회 사실: 참가 자격(2~5인 팀), 제출 폼, 교육 미션, "Skill API" 해석, NVIDIA 스택. G0(대회 조건) 판단 근거 |
| `SCORING_GOLDEN_RULE.md` | 팀 내부 채점 규범(공식 아님). OpenShell/NemoClaw 를 코어로 요구(G2), 숫자 신뢰 등급 A~D |

과거 기록이라 필요할 때만 여는 파일: `IDEA_*`, `CHATGPT_REVIEW_TRANSCRIPT.md`, `01~03-*.md`, `DATA_AND_SKILL_INVENTORY.md`, `HSGate_*`, `HSGATE_*`, `research_raw/`, `tmp/`, `files.zip`(= `HSGate_*.md` 3개와 바이트 동일).
아이디어 흐름: 보안·AgentOps 아이디어 23개 → 현업 브레인스토밍에서 HSGate(HS 품목분류 에이전트) → TradeSentry. HSGate 에서 TradeSentry 로 바꾼 이유는 어디에도 기록돼 있지 않다.

## 2. 데이터 상태

| 스냅샷 (`data/snapshots/`) | 상태 |
|---|---|
| `kcs_202201_202412_v2` | **작업 기준.** 357요청 전부 첫 시도 성공. HS4 스캔 8504·8544·8536 × 16개국, HS6 상세 850450·850431·850432·850490 × 16개국 + 전체국가(ALL). 아직 동결 전. 결합 해시와 계산 명령은 `snapshot_hash.json` |
| `kcs_202201_202412_v1` | v2 이전판(306요청, 850490 없음). v2 와 겹치는 306개 응답이 바이트 단위로 같다. `data-readiness.pre_fix.json` 은 수정 전 verify 결과 보존본 |
| `kcs_202201_202412_v0` | 키 없이 만든 dry-run 기록(54요청 계획) |
| `probe_20260923_205425` | 첫 실응답 probe 3건 |

v2 관문 결과(`data-readiness.json`):
- G1 신규 수집 접근: 통과
- G2 기간 품질: 국가 64쌍 중 48쌍이 36개월 완비(수입 > 0 기준 47쌍), 전체국가 4/4, 분모(전체국가 합계) 교차대조 612건 일치
- G3 HS10 구성분해: 통과. 국가별 부모-하위 대조 2,096건 일치, 한쪽만 있는 조합 0
- 스냅샷 무결성: raw 해시 불일치 0

HS6 별 완비 표와 HS4 스캔 후보 표는 메모 2절에 있다.

## 3. 코드 상태

- `src/tradesentry/ingest.py`: 관세청 API 수집기(표준 라이브러리만)
  - `call_api`: 시도마다 오류값을 초기화하고, 429·5xx·네트워크 예외만 재시도
  - `store_result`: 성공하면 raw·수집 기록·행을 한 트랜잭션으로 통째 교체. 실패는 `raw/failed/` 와 `collection_attempt` 테이블에만 남기고 이전 정상 자료는 건드리지 않음
  - `verify`: 스냅샷을 읽기 전용으로 연다. manifest(수집 요청 목록 기록)의 기대 쌍 기준으로 G2 를 월 5분류(수입>0 / 수입 0 명시 / 무응답 / 실패 / 미수집)로 세고, 부모-하위를 양방향 대조(G3)하며, 전체국가 분모는 HS10 끼리 정확 대조한다(`G2.denominator_cross_check_ok`). 총계 행 누락과 raw 해시도 검사. `--out` 으로 출력 파일명 지정
- `tests/test_ingest.py`: 회귀 테스트 17개(네트워크 없음)
- `scripts/g4_nim_toolcall_probe.py`: NIM 도구호출 왕복 확인(5xx 재시도 포함). G4 의 NIM 왕복은 통과, NAT(NeMo Agent Toolkit) 연동은 미착수
- `configs/collection_plan.json`: v2 설정(snapshot_id v2, HS6 4개, 16개국)
- `eval/dev/oracle_ABC.json`: 합성 시연 A/B/C 정답표(within/mix 산술 검산 일치). `metrics.py` 가 그대로 재현해야 한다
- 미구현: `metrics.py`, `policy.py`, `tools.py`, `workflow.py`, `validator.py`, `evaluation.py`, `reports.py`, `app.py`, NAT 설정, 합성 평가자료(개발 20 / 평가 40)

## 4. 자주 쓰는 명령

```bash
python3 -m unittest discover -s tests -v
python3 src/tradesentry/ingest.py verify --snapshot kcs_202201_202412_v2 --out data-readiness.check.json
python3 src/tradesentry/ingest.py plan    --config configs/collection_plan.json   # 설정을 바꿨으면 snapshot_id 도 새로
python3 src/tradesentry/ingest.py collect --config configs/collection_plan.json
python3 scripts/g4_nim_toolcall_probe.py
```

## 5. 새 플랜에서 정할 것

1. **HS4·HS6·비교국 선정** → 선정 사유 기록 → 스냅샷 동결. 근거는 메모 2절.
   - 850490: 완결성·코드 안정성은 가장 좋지만 HS10 이 2개뿐이라 구성효과 분해가 단순하다.
   - 850440: 완결성은 최상이나 2022-01 이후 신설 HS10 이 1개 있어 연도별 코드 집합 확인이 필요하다.
   - 850432: 16개국 중 6개국만 36개월 완비.
2. **정책 수치**: `min_amount`·`min_weight`(금액 > 0 인데 중량 0 인 행 677개), 전년동월 임계값, `CONFIRMED_NO_TRADE` 승격 규칙, 수입 0 이 명시된 달의 처리.
3. **G0 대회 적격성(미해결)**: "Skill API" 해석, OpenShell/NemoClaw 미사용(팀 규범 G2 와 교육 미션), 팀 2~5인 요건.
4. **팀 분담 합의(D0~D12)** 서명 여부.
5. **평가의 신뢰도**: 합성 평가는 팀 규범상 C~D 등급 경계. 평가 40건이면 정답률 50% 부근 95% 신뢰구간이 ±14.8pp 라 비교군 간 작은 차이는 구별이 어렵다.
6. **구현 순서 후보**: `metrics.py`(oracle_ABC 재현) → 5개 도구 → 워크플로(조사자·Critic·수정 1회·예산 강제) → validator → NAT.

## 6. 주의

- `plan`·`collect` 는 스냅샷 폴더의 `manifest.json` 을 다시 쓰고, `verify` 는 그 파일로 기대 쌍을 계산한다. 설정을 바꿨으면 반드시 새 snapshot_id 를 쓸 것(v1·v2 에 돌리지 말 것).
- `verify` 기본 출력은 `data-readiness.json` 이고 덮어쓴다. 비교할 때는 `--out` 을 쓴다.
- `open_snapshot` 은 스냅샷 정보의 기간을 202201~202412 로 고정 기록한다(`verify` 는 manifest 기간을 우선 사용하므로 현재는 무해).
- 키는 `.env` 에만 둔다(`DATA_GO_KR_SERVICE_KEY`, `NVIDIA_API_KEY`). 로그·trace·문서에 쓰지 않는다.
- 이 저장소의 `python3` 는 3.9.6 이고 pandas·openpyxl 이 없다.
- git 저장소가 아니다. 다른 세션이 같은 파일을 고친 적이 있다(`ingest.py` 는 팀 분담상 D 소유). 고치기 전에 최신 상태를 확인할 것.
- 이전 결과 보존 파일(`data-readiness.pre_fix.json`, probe 결과)에는 옛 기한 문구가 남아 있다. 기록 보존용이라 의도적으로 뒀다.
- 이번 세션의 백업(삭제한 1일차 계획서 원문, 수정 전 `ingest.py`·개발계획·팀 분담 문서·설정)은 세션 임시 폴더에만 있었다. 다음 세션에서는 없다.

## 7. G4 에서 확인된 모델 행동 (설계에 반영할 것)

- 비교 불가 시나리오에서 "추가 조회 없이 보류" 지시를 어기고 `get_history` 를 호출했다. 조기종료·도구 한도·같은 인자 재호출 차단은 프롬프트가 아니라 코드가 강제해야 한다.
- 점유율 감소(10→6)를 "증가"로 뒤집어 쓴 응답이 G4 기준(근거 ID 언급)으로는 통과로 셌다. 숫자는 검증된 metric 에서 템플릿으로만 채워 넣어야 한다(validator).
- Nemotron 3 Super 모델카드의 지원 언어에 한국어가 명시돼 있지 않다(`HSGATE_R3_NVIDIA_STACK_CHECK.md:72`). 한국어 판정문 품질을 따로 측정해야 한다.
