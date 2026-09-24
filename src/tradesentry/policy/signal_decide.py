"""단위 P3 신호별 판정.

단위 ID: P3
도메인명: policy_signal_decide
소유: M
입력: 근거 상태
출력: 신호별 `HOLD`·`MONITOR`·`MAINTAIN`·`NOT_TRIGGERED`
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics, tradesentry.policy

사례 하나의 근거 상태로 신호마다 판정 상태를 정한다. 규칙은 개발 플랜 docs/plan/DEV_PLAN.md §6.3 신호별 판정표와
자료 계약 docs/rules/DATA_CONTRACT_V1.md §3.1이다. 판정 근거(basis)와 상태의 대응, 그리고 판정 근거마다 끝나 있어야
하는 필수 비교는 단위 P5(필수 근거 규칙)의 규칙표 하나에서 가져온다. 해석과 잠정 항목은 docs/tracking/decisions/의
MT1 판정 정책 결정 기록(`*-model-decision-mt1-policy.md`)에 있다.

판정과 근거 검증의 책임 경계
- 근거 상태는 도구 봉투(도구 5개의 공통 출력)에서 코드(조립 AS2의 변환)가 결정적으로 만든다. 모델의 주장으로 채우지
  않는다. 이 단위는 받은 근거 상태를 사실로 보고 판정만 한다.
- 근거 상태의 값이 스냅샷 원본과 맞는지는 `verify_evidence`(단위 I5)가, 보고서의 주장이 판정 근거에 맞는 필수 근거
  (단위 P5 규칙)를 싣는지는 검증기(단위 R3)가 본다.
- `checklist` 모드는 이 판정을 그대로 쓴다. 다른 모드에서 이 판정을 어떻게 쓸지(모델 상태와 나란히 적는 참고값 등)는
  흐름 조정(단위 I12)과 검증기가 정한다. 이 단위는 모델의 상태를 고쳐 쓰지 않는다.
- 근거 상태의 키에는 기본값이 없다. 키가 빠지면 입력 오류(ValueError)로 끝나 실행 실패로 드러난다. 배선 누락이
  그럴듯한 `HOLD`나 `MAINTAIN`으로 바뀌지 않게 하려는 것이다(개발 플랜 §7.5).

발동한 신호의 판정 순서(앞에서 걸리면 멈춘다)
1. 자료 부족 → `HOLD`(`data_insufficient`): 비교월·기준월의 빠진 관측, 비교 가능성을 깨는 문제(`comparability_issues`),
   단가 신호의 구성 분해를 쓸 수 없음(분해 null, 분해 값 null, 부모·하위 대조 불일치, 하위품목 단가 변화 null,
   기준월 단가 없음). 필요한 자료가 없으면 "설명되지 않는다"는 이유로 `MAINTAIN`을 내지 않는다(개발 플랜 §6.3 표 아래).
2. 반올림 불안정(단가 신호만) → `HOLD`(`rounding_unstable`). 입력의 참거짓 값을 쓴다. 만드는 쪽은 아직 없다(잠정).
3. 자료 교정 뒤 동결 정책으로 경보 해소 → `MONITOR`(`resolved_after_correction`). 입력의 참거짓 값을 쓴다. 동결
   스냅샷 하나로 도는 v1 실행에서는 만드는 쪽이 없어 늘 거짓이다. 조회 범위를 고친 재조회(룰북 시나리오 9)에는 쓰지 않는다.
4. 후보 판정 근거: 단가 신호는 아래 세 조건을 모두 채우면 `composition_explained`(`MONITOR`), 아니면 `unexplained`
   (`MAINTAIN`)다. 점유율 신호는 늘 `unexplained`다(분모 축소는 산술 설명일 뿐 하향 사유가 아니다). θ는 정책의 단가
   탐지 임계값(%), U0는 기준월 부모 HS6 단가다.
   - |within_effect + residual| × 100 < θ × U0: 구성효과(mix_effect)를 뺀 변화는 탐지 임계값에 닿지 않는다
   - |within_effect| × 100 < θ × U0, |residual| × 100 < θ × U0: 크게 상쇄된 성분이 없다
   - 모든 HS10 하위품목의 |r_U@HS10| < θ: 하위품목 각각의 단가 변화가 기준 안이다(상쇄 검사)
   "개별 하위변동·잔차가 기준 안"을 단가 탐지 임계값 θ로 읽은 것은 잠정 해석이다(사용자 확인 대기). 계산은 분수로 한다.
5. 필수 비교: 후보 판정 근거의 규칙이 요구하는 필수 비교(단위 P5 required_comparisons)가 모두 `done`일 때만 그 후보로
   낸다. 하나라도 `incomplete`면 `HOLD`(`comparison_incomplete`)다. 단가 `MAINTAIN`은 비교 조건 점검과 비교국 비교,
   단가 `MONITOR`는 비교 조건 점검, 점유율 `MAINTAIN`은 비교 조건 점검·비교국 비교·해당국 금액과 전체국가 분모 변화
   확인이 끝나 있어야 한다. 다른 상대국의 동반 변화는 상태를 낮추지 않으므로 비교 결과의 내용은 판정에 쓰지 않고,
   비교를 마쳤는지만 본다(개발 플랜 §6.3 5행과 표 아래).
발동하지 않은 신호는 `NOT_TRIGGERED`(`not_triggered`)다. 신호마다 따로 판정하므로 한 신호의 자료 부족이 다른 신호의
판정을 바꾸지 않는다.

빠진 관측의 계열 배정(비교월·기준월의 행만 보고, 사례 HS6 밖의 코드와 비교국 행은 판정에 쓰지 않는다)
- `partner_code`가 `ALL`이면 점유율(분모), 대상국이면 단가다. 발동한 사례에서는 비교월·기준월의 대상국 부모 HS6 값이
  있으므로, 대상국 행의 상태 표시는 HS10 하위 자료가 빠졌다는 뜻이다(자료 계약 §2.3.2 행 규칙 4, oracle C).
- 빠진 것으로 보는 상태는 `REQUEST_FAILED`, `NOT_COLLECTED`, `UNRESOLVED_ZERO`다. `CONFIRMED_NO_TRADE`(승격된 무거래
  확정)는 0으로 다루는 관측이라 그 자체로는 빠진 것이 아니다. 그 결과 하위품목 집합이 달라지면 구성 분해 값이 null로
  와서 1번에 걸린다.

`comparability_issues`에는 비교 가능성을 깨는 문제만 넣는다
- 비교월과 기준월의 값을 같은 정의로 비교할 수 없는 경우다: 두 달의 단위(USD·kg)가 다름, 두 달의 HS 코드 정의(코드
  체계·개정판)가 다름.
- 빠진 달·분모·하위자료는 `missingness`와 `decomposition`으로, 부모·하위 대조는 `decomposition.parent_child_match`로 넘긴다.
- 두 달의 정의가 같은데 정보만 모자란 표시(예: 개정판을 확인하지 못한 `HSK` 코드 체계가 두 달에 같게 쓰임)는 넣지 않는다.
- 문자열이 하나라도 있으면 그 계열은 `HOLD`다. 비교 조건 점검 자체를 끝내지 못했으면 목록이 아니라
  `comparisons.comparability`를 `incomplete`로 둔다.

입력(JSON 객체)
- `policy`: 정책 객체. 단위 P1의 policy_values로 읽는다(단가 임계값만 쓴다).
- `case`: 사례 객체. `case_id`, `hs6`, `partner`, `month`, `baseline_month`, `signals`를 읽는다.
- `evidence`: 근거 상태. 아래 키가 모두 있어야 한다(빈 목록도 명시한다).
  - `missingness`: 도구 봉투의 빠진 자료 목록. 항목마다 자료 계약 §2.3.2의 관측 필드 `partner_code`, `hs_code`,
    `month`, `observation_status`가 있다(단위 K3의 `missingness` 항목 모양. 다른 키는 읽지 않는다).
  - `unit_value`(단가 신호가 발동했을 때): `comparability_issues`(문자열 목록), `comparisons`({`comparability`,
    `partners`}), `U_baseline`(USD/kg 또는 null), `decomposition`(null이거나 {`within_effect`, `mix_effect`,
    `residual`: USD/kg 또는 null, `parent_child_match`: 참거짓}), `children`([{`hs10`, `r_U`: % 또는 null}]),
    `rounding_unstable`, `resolved_after_correction`(참거짓).
  - `share`(점유율 신호가 발동했을 때): `comparability_issues`, `comparisons`({`comparability`, `partners`,
    `country_and_world`}), `resolved_after_correction`.
  - 필수 비교의 완료 표시는 `done`(수행해서 결과를 얻었다. 비교국 일부의 제외 사유가 있어도 된다)이나
    `incomplete`(수행했지만 자료가 모자라 결과를 얻지 못했다. 예: 허용된 비교국이 모두 그 달 자료 없음)다.
    수행하지 않은 비교를 이 두 값으로 꾸미지 않는다.
  - 수는 반올림 전 정확값(int·Decimal·Fraction)이다. 표시 자릿수로 반올림한 값은 경계에서 판정을 뒤집으므로 넘기지
    않는다. float는 받지 않는다.
  발동하지 않은 신호의 블록은 없어도 되고, 있으면 읽지 않는다.

출력(JSON 객체): {`case_id`, `signal_status`(자료 계약 §3.1 모양), `basis`(신호별 판정 근거), `gaps`(신호별로 1번이나
5번에 걸린 항목 목록)}. 항목마다 `reason`은 `missing_observation`, `comparability_issue`, `decomposition_unavailable`,
`parent_child_mismatch`, `child_unit_value_unavailable`, `baseline_unit_value_unavailable`, `comparison_incomplete`
가운데 하나이고 세부 키가 붙는다.
"""
from fractions import Fraction

from tradesentry.policy.required_evidence import (ALL_PARTNER, BASIS_COMPARISON_INCOMPLETE,
                                                  BASIS_COMPOSITION_EXPLAINED, BASIS_DATA_INSUFFICIENT,
                                                  BASIS_NOT_TRIGGERED, BASIS_RESOLVED_AFTER_CORRECTION,
                                                  BASIS_ROUNDING_UNSTABLE, BASIS_UNEXPLAINED, COMPARISON_DONE,
                                                  COMPARISON_STATES, NOT_COLLECTED, NOT_TRIGGERED,
                                                  OBSERVATION_STATUSES, REQUEST_FAILED, SHARE, SIGNAL_CODES,
                                                  TRIGGERED, UNIT_VALUE, UNRESOLVED_ZERO, check_signals,
                                                  family_comparisons, required_comparisons, rule_status)
from tradesentry.policy.trigger import (HS6_RE, MONTH_RE, PARTNER_RE, baseline_of, check_number, exact,
                                        policy_values)

GAP_STATUSES = (REQUEST_FAILED, NOT_COLLECTED, UNRESOLVED_ZERO)
MISSING_FIELDS = ("partner_code", "hs_code", "month", "observation_status")
BLOCK_KEYS = {
    UNIT_VALUE: frozenset({"comparability_issues", "comparisons", "U_baseline", "decomposition", "children",
                           "rounding_unstable", "resolved_after_correction"}),
    SHARE: frozenset({"comparability_issues", "comparisons", "resolved_after_correction"}),
}
DECOMPOSITION_KEYS = frozenset({"within_effect", "mix_effect", "residual", "parent_child_match"})
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


def _block(evidence: dict, family: str) -> dict:
    """발동한 신호의 근거 블록. 블록이나 키가 빠지면 입력 오류다(기본값 없음)."""
    if family not in evidence:
        raise ValueError(f"발동한 신호의 근거 상태 evidence.{family}가 없다")
    block = evidence[family]
    if not isinstance(block, dict) or set(block) != BLOCK_KEYS[family]:
        raise ValueError(f"evidence.{family}는 {sorted(BLOCK_KEYS[family])} 키를 모두 가진 객체여야 한다")
    return block


def _flag(block: dict, key: str, where: str) -> bool:
    value = block[key]
    if not isinstance(value, bool):
        raise ValueError(f"{where}.{key}는 참거짓이어야 한다")
    return value


def _comparisons(block: dict, family: str) -> dict[str, str]:
    comparisons = block["comparisons"]
    keys = family_comparisons(family)
    if not isinstance(comparisons, dict) or set(comparisons) != set(keys):
        raise ValueError(f"evidence.{family}.comparisons는 {list(keys)} 키를 모두 가진 객체여야 한다")
    for key in keys:
        if comparisons[key] not in COMPARISON_STATES:
            raise ValueError(f"evidence.{family}.comparisons.{key}는 {list(COMPARISON_STATES)} 중 하나여야 한다")
    return comparisons


def _comparability_gaps(block: dict, family: str) -> list[dict]:
    issues = block["comparability_issues"]
    if not isinstance(issues, list) or not all(isinstance(i, str) and i for i in issues):
        raise ValueError(f"evidence.{family}.comparability_issues는 비어 있지 않은 문자열의 목록이어야 한다")
    return [{"reason": "comparability_issue", "issue": issue} for issue in issues]


def _missing_gaps(missingness: object, case: dict) -> dict[str, list[dict]]:
    """빠진 관측을 신호 계열에 배정한다. 비교월·기준월, 사례 HS6 아래, 대상국이나 ALL 행만 본다."""
    if not isinstance(missingness, list):
        raise ValueError("evidence.missingness는 목록이어야 한다(빠진 자료가 없으면 빈 목록)")
    gaps: dict[str, list[dict]] = {UNIT_VALUE: [], SHARE: []}
    for index, item in enumerate(missingness):
        if not isinstance(item, dict):
            raise ValueError(f"evidence.missingness[{index}]는 객체여야 한다")
        partner, hs_code, month, status = (item.get(k) for k in MISSING_FIELDS)
        if not all(isinstance(v, str) and v for v in (partner, hs_code, month)):
            raise ValueError(f"evidence.missingness[{index}]에 partner_code·hs_code·month 문자열이 있어야 한다")
        if status not in OBSERVATION_STATUSES:
            raise ValueError(f"evidence.missingness[{index}].observation_status가 관측 상태 코드가 아니다")
        if status not in GAP_STATUSES or month not in (case["month"], case["baseline_month"]) \
                or not hs_code.startswith(case["hs6"]):
            continue
        family = SHARE if partner == ALL_PARTNER else UNIT_VALUE if partner == case["partner"] else None
        if family is not None:
            gaps[family].append({"reason": "missing_observation", "partner_code": partner, "hs_code": hs_code,
                                 "month": month, "observation_status": status})
    return gaps


def _optional_number(value: object, where: str) -> Fraction | None:
    return None if value is None else exact(check_number(value, where))


def _decomposition_gaps(block: dict, threshold: Fraction) -> tuple[list[dict], bool]:
    """구성 분해 근거를 검사한다. (1번에 걸린 항목, 구성효과로 설명되는가)를 돌려준다."""
    children = block["children"]
    if not isinstance(children, list):
        raise ValueError("evidence.unit_value.children은 목록이어야 한다")
    child_changes = []
    for index, child in enumerate(children):
        if not isinstance(child, dict) or set(child) != {"hs10", "r_U"} or not isinstance(child["hs10"], str) \
                or not child["hs10"]:
            raise ValueError(f"evidence.unit_value.children[{index}]는 hs10·r_U 두 키의 객체여야 한다")
        child_changes.append(_optional_number(child["r_U"], f"evidence.unit_value.children[{index}].r_U"))
    baseline_u = _optional_number(block["U_baseline"], "evidence.unit_value.U_baseline")
    decomposition = block["decomposition"]
    gaps = []
    effects: dict[str, Fraction | None] = {}
    if decomposition is None:
        gaps.append({"reason": "decomposition_unavailable"})
    else:
        if not isinstance(decomposition, dict) or set(decomposition) != DECOMPOSITION_KEYS:
            raise ValueError(f"evidence.unit_value.decomposition은 null이거나 {sorted(DECOMPOSITION_KEYS)} 키의 "
                             f"객체여야 한다")
        effects = {key: _optional_number(decomposition[key], f"evidence.unit_value.decomposition.{key}")
                   for key in EFFECTS}
        if not isinstance(decomposition["parent_child_match"], bool):
            raise ValueError("evidence.unit_value.decomposition.parent_child_match는 참거짓이어야 한다")
        if any(effects[key] is None for key in EFFECTS):
            gaps.append({"reason": "decomposition_unavailable"})
        if not decomposition["parent_child_match"]:
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


def _decide(family: str, block: dict, missing: list[dict], threshold: Fraction) -> tuple[str, list[dict]]:
    """발동한 신호 하나의 판정 근거와 1번·5번에 걸린 항목."""
    comparisons = _comparisons(block, family)
    rounding_unstable = _flag(block, "rounding_unstable", f"evidence.{family}") if family == UNIT_VALUE else False
    resolved = _flag(block, "resolved_after_correction", f"evidence.{family}")
    gaps = missing + _comparability_gaps(block, family)
    explained = False
    if family == UNIT_VALUE:
        decomposition_gaps, explained = _decomposition_gaps(block, threshold)
        gaps += decomposition_gaps
    if gaps:
        return BASIS_DATA_INSUFFICIENT, gaps
    if rounding_unstable:
        return BASIS_ROUNDING_UNSTABLE, []
    if resolved:
        return BASIS_RESOLVED_AFTER_CORRECTION, []
    candidate = BASIS_COMPOSITION_EXPLAINED if explained else BASIS_UNEXPLAINED
    incomplete = [key for key in required_comparisons(family, candidate) if comparisons[key] != COMPARISON_DONE]
    if incomplete:
        return BASIS_COMPARISON_INCOMPLETE, [{"reason": "comparison_incomplete", "comparison": key}
                                             for key in incomplete]
    return candidate, []


def run(inp: object) -> object:
    """사례의 근거 상태로 신호별 판정 상태와 판정 근거를 정한다."""
    if not isinstance(inp, dict) or set(inp) != {"policy", "case", "evidence"}:
        raise ValueError("입력은 policy·case·evidence 세 키만 가진 객체여야 한다")
    threshold = exact(policy_values(inp["policy"])[UNIT_VALUE])
    case = _check_case(inp["case"])
    evidence = inp["evidence"]
    if not isinstance(evidence, dict) or "missingness" not in evidence \
            or not set(evidence) <= {"missingness", UNIT_VALUE, SHARE}:
        raise ValueError("evidence는 missingness(필수)와 발동한 신호의 블록(unit_value·share)만 가진 객체여야 한다")
    missing = _missing_gaps(evidence["missingness"], case)
    basis: dict[str, str] = {}
    gaps: dict[str, list[dict]] = {}
    for code in SIGNAL_CODES:
        if case["signals"][code] != TRIGGERED:
            basis[code], gaps[code] = BASIS_NOT_TRIGGERED, []
        else:
            basis[code], gaps[code] = _decide(code, _block(evidence, code), missing[code], threshold)
    signal_status = {code: NOT_TRIGGERED if basis[code] == BASIS_NOT_TRIGGERED else rule_status(code, basis[code])
                     for code in SIGNAL_CODES}
    return {"case_id": case["case_id"], "signal_status": signal_status, "basis": basis, "gaps": gaps}
