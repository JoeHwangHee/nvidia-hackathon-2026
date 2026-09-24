"""단위 P3 신호별 판정.

단위 ID: P3
도메인명: policy_signal_decide
소유: M
입력: 근거 상태
출력: 신호별 `HOLD`·`MONITOR`·`MAINTAIN`·`NOT_TRIGGERED`
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics, tradesentry.policy

사례 하나의 근거 상태로 신호마다 판정 상태를 정한다. 규칙은 개발 플랜 docs/plan/DEV_PLAN.md §6.3 신호별 판정표와
자료 계약 docs/rules/DATA_CONTRACT_V1.md §3.1이다. 판정 근거(basis)와 상태의 대응은 단위 P5(필수 근거 규칙)의
규칙표 하나에서 가져온다. `checklist` 모드는 이 판정을 그대로 쓰고, 다른 모드에서는 모델이 낸 상태를 대조할 기준이다.
이 단위는 모델의 상태를 고쳐 쓰지 않는다.

발동한 신호의 판정 순서(앞에서 걸리면 멈춘다)
1. 자료 부족 → `HOLD`(`data_insufficient`): 비교월·기준월의 빠진 관측, 비교 조건 문제, 단가 신호의 구성 분해를 쓸
   수 없음(분해 없음, 분해 값 null, 부모·하위 대조 불일치, 하위품목 단가 변화 null, 기준월 단가 없음).
   필요한 자료가 없으면 "설명되지 않는다"는 이유로 `MAINTAIN`을 내지 않는다(개발 플랜 §6.3 표 아래).
2. 반올림 불안정(단가 신호만) → `HOLD`(`rounding_unstable`). 입력의 참거짓 값을 쓴다.
3. 자료 교정 뒤 동결 정책으로 경보 해소 → `MONITOR`(`resolved_after_correction`). 입력의 참거짓 값을 쓴다.
4. 구성효과로 설명(단가 신호만) → `MONITOR`(`composition_explained`). 아래 세 조건을 모두 채울 때다. θ는 정책의
   단가 탐지 임계값(%), U0는 기준월 부모 HS6 단가다.
   - |within_effect + residual| × 100 < θ × U0: 구성효과(mix_effect)를 뺀 변화는 탐지 임계값에 닿지 않는다
   - |within_effect| × 100 < θ × U0, |residual| × 100 < θ × U0: 크게 상쇄된 성분이 없다
   - 모든 HS10 하위품목의 |r_U@HS10| < θ: 하위품목 각각의 단가 변화가 기준 안이다(상쇄 검사)
   "기준 안"을 단가 탐지 임계값으로 읽은 것은 해석이다. `policy_v1` 승인 항목(로드맵 §6.3)에는 잔차·하위 안정성
   전용 기준값이 없어, 새 정책 키를 만들지 않고 이미 있는 임계값만 쓴다.
5. 그 밖 → `MAINTAIN`(`unexplained`). 다른 상대국의 동반 변화나 분모 축소(산술 설명)는 상태를 낮추지 않으므로
   비교국 결과는 입력으로 받지 않는다. 필수 비교를 마쳤는지는 단위 P5 규칙과 검증기가 본다.
발동하지 않은 신호는 `NOT_TRIGGERED`(`not_triggered`)다. 신호마다 따로 판정하므로 한 신호의 자료 부족이 다른 신호의
판정을 바꾸지 않는다.

빠진 관측의 계열 배정(비교월·기준월의 행만 보고, 사례 HS6 밖의 코드와 비교국 행은 판정에 쓰지 않는다)
- `partner`가 `ALL`이면 점유율(분모), 대상국이면 단가다. 발동한 사례에서는 비교월·기준월의 대상국 부모 HS6 값이 있으므로,
  대상국 행의 상태 표시는 HS10 하위 자료가 빠졌다는 뜻이다(자료 계약 §2.3.2 행 규칙 4, oracle C).
- 빠진 것으로 보는 상태는 `REQUEST_FAILED`, `NOT_COLLECTED`, `UNRESOLVED_ZERO`다. `CONFIRMED_NO_TRADE`(승격된 무거래
  확정)는 0으로 다루는 관측이라 그 자체로는 빠진 것이 아니다. 그 결과 하위품목 집합이 달라지면 구성 분해 값이 null로
  와서 1번에 걸린다.

입력(JSON 객체)
- `policy`: 정책 객체. 단위 P1의 policy_values로 읽는다(단가 임계값만 쓴다).
- `case`: 사례 객체. `case_id`, `hs6`, `partner`, `month`, `baseline_month`, `signals`를 읽는다.
- `evidence`: 근거 상태. 키는 셋까지다.
  - `missingness`: 도구 봉투의 빠진 자료 목록. 항목마다 `partner`, `hs_code`, `month`, `observation_status`.
  - `unit_value`: `comparability_issues`(문자열 목록), `U_baseline`(USD/kg), `decomposition`({`within_effect`,
    `mix_effect`, `residual`: USD/kg 또는 null, `parent_child_match`: 참거짓}), `children`([{`hs10`, `r_U`: % 또는
    null}]), `rounding_unstable`, `resolved_after_correction`(참거짓, 없으면 거짓).
  - `share`: `comparability_issues`, `resolved_after_correction`.
  수는 정수나 Decimal만 받는다(float 금지).

출력(JSON 객체): {`case_id`, `signal_status`(자료 계약 §3.1 모양), `basis`(신호별 판정 근거), `gaps`(신호별로 1번에
걸린 항목 목록. 항목마다 `reason`과 세부)}.
"""
from decimal import Decimal

from tradesentry.policy.required_evidence import (ALL_PARTNER, BASIS_COMPOSITION_EXPLAINED, BASIS_DATA_INSUFFICIENT,
                                                  BASIS_NOT_TRIGGERED, BASIS_RESOLVED_AFTER_CORRECTION,
                                                  BASIS_ROUNDING_UNSTABLE, BASIS_UNEXPLAINED, NOT_COLLECTED,
                                                  NOT_TRIGGERED, OBSERVATION_STATUSES, REQUEST_FAILED, SHARE,
                                                  SIGNAL_CODES, TRIGGERED, UNIT_VALUE, UNRESOLVED_ZERO,
                                                  check_signals, rule_status)
from tradesentry.policy.trigger import HS6_RE, MONTH_RE, PARTNER_RE, baseline_of, check_number, policy_values

GAP_STATUSES = (REQUEST_FAILED, NOT_COLLECTED, UNRESOLVED_ZERO)
UNIT_VALUE_KEYS = {"comparability_issues", "U_baseline", "decomposition", "children", "rounding_unstable",
                   "resolved_after_correction"}
SHARE_KEYS = {"comparability_issues", "resolved_after_correction"}
DECOMPOSITION_KEYS = {"within_effect", "mix_effect", "residual", "parent_child_match"}
EFFECTS = ("within_effect", "mix_effect", "residual")


def _check_case(case: object) -> dict:
    if not isinstance(case, dict):
        raise ValueError("case는 사례 객체여야 한다")
    case_id, hs6, partner, month, baseline = (case.get(k) for k in
                                              ("case_id", "hs6", "partner", "month", "baseline_month"))
    if not isinstance(case_id, str) or not case_id:
        raise ValueError("case.case_id는 비어 있지 않은 문자열이어야 한다")
    if not isinstance(hs6, str) or not HS6_RE.match(hs6):
        raise ValueError("case.hs6는 6자리 숫자 문자열이어야 한다")
    if not isinstance(partner, str) or partner == ALL_PARTNER or not PARTNER_RE.match(partner):
        raise ValueError("case.partner는 대상국 2자리 코드여야 한다")
    if not isinstance(month, str) or not MONTH_RE.match(month) or baseline != baseline_of(month):
        raise ValueError("case.month는 YYYYMM, case.baseline_month는 그 12개월 앞이어야 한다")
    return {"case_id": case_id, "hs6": hs6, "partner": partner, "month": month, "baseline_month": baseline,
            "signals": check_signals(case.get("signals"))}


def _flag(block: dict, key: str, where: str) -> bool:
    value = block.get(key, False)
    if not isinstance(value, bool):
        raise ValueError(f"{where}.{key}는 참거짓이어야 한다")
    return value


def _comparability_gaps(block: dict, where: str) -> list[dict]:
    issues = block.get("comparability_issues", [])
    if not isinstance(issues, list) or not all(isinstance(i, str) and i for i in issues):
        raise ValueError(f"{where}.comparability_issues는 비어 있지 않은 문자열의 목록이어야 한다")
    return [{"reason": "comparability_issue", "issue": issue} for issue in issues]


def _missing_gaps(missingness: object, case: dict) -> dict[str, list[dict]]:
    """빠진 관측을 신호 계열에 배정한다. 비교월·기준월, 사례 HS6 아래, 대상국이나 ALL 행만 본다."""
    if not isinstance(missingness, list):
        raise ValueError("evidence.missingness는 목록이어야 한다")
    gaps: dict[str, list[dict]] = {UNIT_VALUE: [], SHARE: []}
    for index, item in enumerate(missingness):
        if not isinstance(item, dict):
            raise ValueError(f"evidence.missingness[{index}]는 객체여야 한다")
        partner, hs_code, month, status = (item.get(k) for k in ("partner", "hs_code", "month", "observation_status"))
        if not all(isinstance(v, str) and v for v in (partner, hs_code, month)):
            raise ValueError(f"evidence.missingness[{index}]에 partner·hs_code·month 문자열이 있어야 한다")
        if status not in OBSERVATION_STATUSES:
            raise ValueError(f"evidence.missingness[{index}].observation_status가 관측 상태 코드가 아니다")
        if status not in GAP_STATUSES or month not in (case["month"], case["baseline_month"]) \
                or not hs_code.startswith(case["hs6"]):
            continue
        family = SHARE if partner == ALL_PARTNER else UNIT_VALUE if partner == case["partner"] else None
        if family is not None:
            gaps[family].append({"reason": "missing_observation", "partner": partner, "hs_code": hs_code,
                                 "month": month, "observation_status": status})
    return gaps


def _decomposition_gaps(block: dict, threshold: int | Decimal) -> tuple[list[dict], bool]:
    """구성 분해 근거를 검사한다. (1번에 걸린 항목, 구성효과로 설명되는가)를 돌려준다."""
    decomposition = block.get("decomposition")
    if decomposition is None:
        return [{"reason": "decomposition_absent"}], False
    if not isinstance(decomposition, dict) or set(decomposition) != DECOMPOSITION_KEYS:
        raise ValueError(f"evidence.unit_value.decomposition은 {sorted(DECOMPOSITION_KEYS)} 키의 객체여야 한다")
    effects = {}
    for key in EFFECTS:
        value = decomposition[key]
        effects[key] = None if value is None else check_number(value, f"evidence.unit_value.decomposition.{key}")
    match = decomposition["parent_child_match"]
    if not isinstance(match, bool):
        raise ValueError("evidence.unit_value.decomposition.parent_child_match는 참거짓이어야 한다")
    children = block.get("children", [])
    if not isinstance(children, list):
        raise ValueError("evidence.unit_value.children은 목록이어야 한다")
    child_changes = []
    for index, child in enumerate(children):
        if not isinstance(child, dict) or set(child) != {"hs10", "r_U"} or not isinstance(child["hs10"], str) \
                or not child["hs10"]:
            raise ValueError(f"evidence.unit_value.children[{index}]는 hs10·r_U 두 키의 객체여야 한다")
        value = child["r_U"]
        child_changes.append(None if value is None else
                             check_number(value, f"evidence.unit_value.children[{index}].r_U"))
    baseline_u = block.get("U_baseline")
    if baseline_u is not None:
        check_number(baseline_u, "evidence.unit_value.U_baseline")

    gaps = []
    if any(effects[key] is None for key in EFFECTS):
        gaps.append({"reason": "decomposition_unavailable"})
    if not match:
        gaps.append({"reason": "parent_child_mismatch"})
    if not child_changes or any(value is None for value in child_changes):
        gaps.append({"reason": "child_unit_value_unavailable"})
    if baseline_u is None or baseline_u <= 0:
        gaps.append({"reason": "baseline_unit_value_unavailable"})
    if gaps:
        return gaps, False
    limit = threshold * baseline_u
    within, residual = effects["within_effect"], effects["residual"]
    explained = (abs(within + residual) * 100 < limit and abs(within) * 100 < limit
                 and abs(residual) * 100 < limit and all(abs(value) < threshold for value in child_changes))
    return [], explained


def _decide_unit_value(block: object, missing: list[dict], threshold: int | Decimal) -> tuple[str, list[dict]]:
    if block is None:
        block = {}
    if not isinstance(block, dict) or not set(block) <= UNIT_VALUE_KEYS:
        raise ValueError(f"evidence.unit_value는 {sorted(UNIT_VALUE_KEYS)} 안의 키만 가진 객체여야 한다")
    rounding_unstable = _flag(block, "rounding_unstable", "evidence.unit_value")
    resolved = _flag(block, "resolved_after_correction", "evidence.unit_value")
    decomposition_gaps, explained = _decomposition_gaps(block, threshold)
    gaps = missing + _comparability_gaps(block, "evidence.unit_value") + decomposition_gaps
    if gaps:
        return BASIS_DATA_INSUFFICIENT, gaps
    if rounding_unstable:
        return BASIS_ROUNDING_UNSTABLE, []
    if resolved:
        return BASIS_RESOLVED_AFTER_CORRECTION, []
    return (BASIS_COMPOSITION_EXPLAINED if explained else BASIS_UNEXPLAINED), []


def _decide_share(block: object, missing: list[dict]) -> tuple[str, list[dict]]:
    if block is None:
        block = {}
    if not isinstance(block, dict) or not set(block) <= SHARE_KEYS:
        raise ValueError(f"evidence.share는 {sorted(SHARE_KEYS)} 안의 키만 가진 객체여야 한다")
    resolved = _flag(block, "resolved_after_correction", "evidence.share")
    gaps = missing + _comparability_gaps(block, "evidence.share")
    if gaps:
        return BASIS_DATA_INSUFFICIENT, gaps
    return (BASIS_RESOLVED_AFTER_CORRECTION if resolved else BASIS_UNEXPLAINED), []


def run(inp: object) -> object:
    """사례의 근거 상태로 신호별 판정 상태와 판정 근거를 정한다."""
    if not isinstance(inp, dict) or set(inp) != {"policy", "case", "evidence"}:
        raise ValueError("입력은 policy·case·evidence 세 키만 가진 객체여야 한다")
    threshold = policy_values(inp["policy"])[UNIT_VALUE]
    case = _check_case(inp["case"])
    evidence = inp["evidence"]
    if not isinstance(evidence, dict) or not set(evidence) <= {"missingness", UNIT_VALUE, SHARE}:
        raise ValueError("evidence는 missingness·unit_value·share 안의 키만 가진 객체여야 한다")
    missing = _missing_gaps(evidence.get("missingness", []), case)
    basis: dict[str, str] = {}
    gaps: dict[str, list[dict]] = {}
    for code in SIGNAL_CODES:
        if case["signals"][code] != TRIGGERED:
            basis[code], gaps[code] = BASIS_NOT_TRIGGERED, []
        elif code == UNIT_VALUE:
            basis[code], gaps[code] = _decide_unit_value(evidence.get(UNIT_VALUE), missing[UNIT_VALUE], threshold)
        else:
            basis[code], gaps[code] = _decide_share(evidence.get(SHARE), missing[SHARE])
    signal_status = {code: NOT_TRIGGERED if basis[code] == BASIS_NOT_TRIGGERED else rule_status(code, basis[code])
                     for code in SIGNAL_CODES}
    return {"case_id": case["case_id"], "signal_status": signal_status, "basis": basis, "gaps": gaps}
