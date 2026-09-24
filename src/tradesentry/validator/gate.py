"""단위 R4 차단 판정.

단위 ID: R4
도메인명: validator_gate
소유: M
입력: findings + 모드
출력: 통과·차단·기록만·`INVALID`
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.validator

정본: 자료 계약 docs/rules/DATA_CONTRACT_V1.md §3.3(`INVALID`), §6.3·§9.1(모드별 검증기), 개발 플랜
docs/plan/DEV_PLAN.md §6.6(스키마 실패와 수정 1회)·§7.3·§7.4, 룰북 docs/eval/RULEBOOK.md B2, 결정 D1(사용자 결정
2026-09-24(목) 23:09: `checklist`에서 검증기가 막으면 수정 단계 없이 곧바로 `INVALID`, 새 상태값 없음).

입력(JSON 객체 하나)
- `mode`: `checklist` | `agent` | `full` | `freeform`
- `findings`: 단위 R3의 사유 목록. 사유마다 `check`가 `schema` 또는 `validator`다.
- `revision_used`: 이 보고서가 이미 수정 단계(1회)를 거친 것인가(true·false)

규칙
- 막는 사유: 스키마 사유는 모든 모드에서 막는다. 검증기 사유는 `freeform`이 아닌 모드(`checklist`·`agent`·`full`)에서
  막고, `freeform`에서는 막지 않고 기록만 한다.
- 막혔을 때: 수정 단계가 남았으면(`agent`·`full`·`freeform`, 아직 수정 전) 수정으로 간다. 수정을 이미 썼거나
  `checklist`(모델이 없어 수정 단계가 없다, 결정 D1)면 실행 상태는 `INVALID`다.
- 상태를 고치지 않는다. 보고서 내용과 판정은 이 단위의 출력에 들지 않는다.

출력: `{"blocked", "revise", "execution_status", "schema_failed", "record_only", "validator_findings"}`
- `blocked`: 막는 사유가 있다. `revise`: 수정 단계로 간다. `execution_status`: 막혔는데 수정이 없으면 `INVALID`,
  아니면 null(이 단위는 실행 상태를 정하지 않는다). `schema_failed`: 스키마 사유가 있다(흐름 조정(I12)이 첫 초안의
  스키마 실패면 Critic을 건너뛴다, 개발 플랜 §6.6). `record_only`: `freeform`이 막지 않고 기록만 한 검증기 사유가 있다.
- `validator_findings`: 보고서의 `validator_findings`에 넣을 목록(계약 §9.1). `freeform`이 아닌 모드에서는 막은 사유,
  `freeform`에서는 막았을 사유다. 사유는 받은 그대로 모두 담는다(`check`로 스키마 사유를 가른다).
- 판정 이름(통과·차단·기록만)은 새 상태값을 만들지 않으려고 참·거짓으로만 낸다. 상태값은 계약의 `INVALID` 하나만 쓴다.
"""
import copy

from tradesentry.validator.validate import MODES

CHECKS = ("schema", "validator")
INVALID = "INVALID"


def run(inp: object) -> object:
    """진입 함수. 사유와 모드로 막을지, 수정으로 갈지, INVALID로 끝낼지를 정한다."""
    if not isinstance(inp, dict):
        raise ValueError("R4 입력은 JSON 객체여야 한다")
    mode, findings, revision_used = inp.get("mode"), inp.get("findings"), inp.get("revision_used")
    if mode not in MODES:
        raise ValueError("R4 입력의 mode가 checklist·agent·full·freeform 가운데 하나가 아니다")
    if not isinstance(revision_used, bool):
        raise ValueError("R4 입력의 revision_used는 true·false여야 한다")
    if not isinstance(findings, list) or not all(isinstance(f, dict) and f.get("check") in CHECKS for f in findings):
        raise ValueError("R4 입력의 findings는 check가 schema·validator인 사유 객체의 목록이어야 한다")
    schema = [f for f in findings if f["check"] == "schema"]
    checked = [f for f in findings if f["check"] == "validator"]
    blocking = schema + (checked if mode != "freeform" else [])
    blocked = bool(blocking)
    revise = blocked and mode != "checklist" and not revision_used
    return {"blocked": blocked,
            "revise": revise,
            "execution_status": INVALID if blocked and not revise else None,
            "schema_failed": bool(schema),
            "record_only": mode == "freeform" and bool(checked),
            "validator_findings": copy.deepcopy(findings)}
