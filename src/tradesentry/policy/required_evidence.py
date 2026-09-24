"""단위 P5 필수 근거 규칙.

단위 ID: P5
도메인명: policy_required_evidence
소유: M
입력: 신호 계열
출력: 필수 주장·근거 목록
허용 import: 표준 라이브러리, tradesentry.contract

공개 정책의 "이 상태를 내려면 이 근거를 남겨야 한다"는 규칙이다(개발 플랜 docs/plan/DEV_PLAN.md §6.3 "반드시 남길
근거" 열, §6.5 끝 문단). 도구(verify_evidence)·검증기·조사자 프롬프트가 함께 쓴다. 사례별 예상 상태나 정답표는 담지
않는다. 규칙은 신호 계열과 판정 근거(basis)마다 정해지고 사례마다 달라지지 않는다.

입력(JSON 객체): {"signals": {"unit_value": "TRIGGERED" | "NOT_TRIGGERED", "share": ...}}. 사례 객체의 `signals`와
같은 모양이다(자료 계약 §2.3.5). 발동한 신호가 하나도 없으면 사례가 아니므로 오류다.

출력(JSON 객체): `families`에 발동한 신호 계열마다
- `claim_metrics`, `claim_metric_prefixes`: 그 계열의 claim 요건(자료 계약 §9.4)을 채우는 `metric` 기호와 HS10 하위
  기호 앞부분(`<기호>@` 뒤에 HS10 코드). `data_status` 주장의 계열 규칙과 대상 규칙은 함수 claim_families가 적용한다.
- `rules`: 판정 근거(basis)별 신호 상태와 필수 근거 코드 목록. basis는 신호별 판정(단위 P3)이 출력한다.
그리고 `evidence_descriptions`(쓰인 근거 코드 → 한국어 설명)를 붙인다.

필수 비교: 근거 코드 가운데 셋은 조사 중에 해야 하는 비교다. `comparability_ok`는 비교 조건 점검(`comparability`),
`partner_comparison_done`은 비교국 비교(`partners`), `country_and_world_change_shown`은 해당국 금액과 전체국가 분모의
변화 확인(`country_and_world`)이다(COMPARISON_EVIDENCE). 근거 상태는 비교마다 완료 표시 셋 가운데 하나를 적는다:
`done`(수행해서 결과를 얻음), `incomplete`(수행했지만 빠진 관측 때문에 결과를 얻지 못함), `not_performed`(수행하지
않음. 비교 불가로 조기 종료했거나 도구 호출이 실패한 경우). 단위 P3은 판정 근거를 정하기 전에 그 근거의 규칙이 요구하는
비교가 끝났는지(`done`) 확인하고, `incomplete`면 `comparison_incomplete`(`HOLD`)로 낸다. 요구하는 비교가
`not_performed`인데 자료 부족 같은 앞 단계 사유가 없으면 입력 오류다. 어느 규칙이 어느 비교를 요구하는지는 이 파일의
규칙표 하나에서 나온다.

계약 상수: 커널 K1(tradesentry.contract.types)이 아직 뼈대라, 판정 정책 단위가 쓰는 계약 값(상태값·신호 코드·관측
상태·출처·자료 묶음 이름)을 이 파일에 한 번만 적고 P1~P4가 여기서 import한다. 글자는 자료 계약과 같다. 조립 점검
(AS4)에서 K1 import로 바꾼다(단위 표 docs/plan/UNITS.md §6 조립 부산물 4).
"""

# --- 계약 상수(자료 계약 docs/rules/DATA_CONTRACT_V1.md §3·§4) ---------------------------------------------------
UNIT_VALUE = "unit_value"
SHARE = "share"
SIGNAL_CODES = (UNIT_VALUE, SHARE)

TRIGGERED = "TRIGGERED"
NOT_TRIGGERED = "NOT_TRIGGERED"
SIGNAL_TRIGGERS = (TRIGGERED, NOT_TRIGGERED)

MAINTAIN = "MAINTAIN"
MONITOR = "MONITOR"
HOLD = "HOLD"
REVIEW_STATUSES = (MAINTAIN, MONITOR, HOLD)
SIGNAL_STATUSES = (MAINTAIN, MONITOR, HOLD, NOT_TRIGGERED)

OBSERVED = "OBSERVED"
NOT_COLLECTED = "NOT_COLLECTED"
REQUEST_FAILED = "REQUEST_FAILED"
UNRESOLVED_ZERO = "UNRESOLVED_ZERO"
CONFIRMED_NO_TRADE = "CONFIRMED_NO_TRADE"
OBSERVATION_STATUSES = (OBSERVED, NOT_COLLECTED, REQUEST_FAILED, UNRESOLVED_ZERO, CONFIRMED_NO_TRADE)

ALL_PARTNER = "ALL"
SOURCE_KINDS = ("real", "controlled")
REAL_DATASETS = ("real_dev", "real_sealed")

# --- 판정 근거(basis). 이 단위가 정한 이름이고 계약 값이 아니다. 개발 플랜 §6.3 표의 행에 대응한다 ---------------
BASIS_NOT_TRIGGERED = "not_triggered"
BASIS_DATA_INSUFFICIENT = "data_insufficient"  # §6.3 1행: 필요한 월·단위·HS 정의·분모·구성자료가 없어 검증 불가
BASIS_COMPARISON_INCOMPLETE = "comparison_incomplete"  # §6.3 4행·표 아래: 필수 비교를 수행했지만 자료가 모자라 못 끝냄
BASIS_ROUNDING_UNSTABLE = "rounding_unstable"  # §6.3 6행: 작은 기준월 값이나 반올림 때문에 방향·충족 여부가 불안정
BASIS_RESOLVED_AFTER_CORRECTION = "resolved_after_correction"  # §6.3 3행: 자료 교정 뒤 동결 정책으로 경보 해소
BASIS_COMPOSITION_EXPLAINED = "composition_explained"  # §6.3 2행: 완전한 하위자료에서 구성효과로 설명(단가 신호만)
BASIS_UNEXPLAINED = "unexplained"  # §6.3 4행: 필수 비교를 마쳤는데 설명되지 않거나 설명이 충돌

# --- 근거 코드와 설명. 앞의 8개는 개발용 합성 예시(A/B/C)의 required_evidence 표기와 같은 이름이다 ---------------
EVIDENCE_DESCRIPTIONS = {
    "parent_child_match_V_and_Q": "부모 HS6 행과 HS10 하위 행 합계 대조(금액 정확 일치, 중량 허용오차)",
    "weight_share_decomposition": "중량 비중 구성효과 분해 수치(within_effect·mix_effect·residual)",
    "per_child_unit_value_stable": "HS10 하위품목별 단가 변화가 기준 안(하위 안정성)",
    "comparability_ok": "비교 조건 점검(기간·요청 완료·단위·HS 버전·분모·하위자료)",
    "partner_comparison_done": "허용된 비교국과의 비교(검사한 대안 설명과 반대 근거)",
    "missingness_listed": "부족 항목 목록",
    "failure_vs_not_collected_distinguished": "요청 실패와 미수집의 구분",
    "no_zero_fill": "빈 응답을 0으로 채우지 않음",
    "precision_sensitivity_shown": "정밀도·유효범위·민감도(작은 금액 자체를 정상 근거로 쓰지 않음)",
    "correction_snapshots_before_after": "교정 전후 스냅샷",
    "recalculated_values": "교정 뒤 동결 정책으로 재계산한 값",
    "change_reason": "변경 사유",
    "country_and_world_change_shown": "해당국 금액 변화와 전체국가(ALL) 분모 변화",
}

_HOLD_EVIDENCE = ("missingness_listed", "failure_vs_not_collected_distinguished", "no_zero_fill")
_CORRECTION_EVIDENCE = ("correction_snapshots_before_after", "recalculated_values", "change_reason")

# 계열 → ((basis, 신호 상태, 필수 근거 코드), ...). 반올림 불안정 규칙은 단가 신호에만 있다. 점유율은 정수 USD 금액만
# 쓰므로 반올림 민감도가 없다(자료 계약 §11.1: 금액은 정확 일치, 행마다 정수 kg로 반올림된 것은 중량이다).
RULES = {
    UNIT_VALUE: (
        (BASIS_DATA_INSUFFICIENT, HOLD, _HOLD_EVIDENCE),
        (BASIS_COMPARISON_INCOMPLETE, HOLD, _HOLD_EVIDENCE),
        (BASIS_ROUNDING_UNSTABLE, HOLD, ("precision_sensitivity_shown",)),
        (BASIS_RESOLVED_AFTER_CORRECTION, MONITOR, _CORRECTION_EVIDENCE),
        (BASIS_COMPOSITION_EXPLAINED, MONITOR, ("parent_child_match_V_and_Q", "weight_share_decomposition",
                                                "per_child_unit_value_stable", "comparability_ok")),
        (BASIS_UNEXPLAINED, MAINTAIN, ("parent_child_match_V_and_Q", "weight_share_decomposition",
                                       "partner_comparison_done", "comparability_ok")),
    ),
    SHARE: (
        (BASIS_DATA_INSUFFICIENT, HOLD, _HOLD_EVIDENCE),
        (BASIS_COMPARISON_INCOMPLETE, HOLD, _HOLD_EVIDENCE),
        (BASIS_RESOLVED_AFTER_CORRECTION, MONITOR, _CORRECTION_EVIDENCE),
        (BASIS_UNEXPLAINED, MAINTAIN, ("country_and_world_change_shown", "partner_comparison_done",
                                       "comparability_ok")),
    ),
}

# 필수 비교 → 그 비교가 채우는 근거 코드. 근거 상태의 비교 완료 표시는 COMPARISON_STATES 셋 중 하나다.
COMPARISON_EVIDENCE = {"comparability": "comparability_ok", "partners": "partner_comparison_done",
                       "country_and_world": "country_and_world_change_shown"}
COMPARISON_DONE = "done"
COMPARISON_INCOMPLETE = "incomplete"
COMPARISON_NOT_PERFORMED = "not_performed"
COMPARISON_STATES = (COMPARISON_DONE, COMPARISON_INCOMPLETE, COMPARISON_NOT_PERFORMED)

# 자료 계약 §9.4 신호 계열 대응. HS10 하위 기호는 `<기호>@<HS10 코드>`다(§6.2).
CLAIM_METRICS = {UNIT_VALUE: ("U", "r_U", "within_effect", "mix_effect", "residual"), SHARE: ("s", "d_s")}
CLAIM_METRIC_PREFIXES = {UNIT_VALUE: ("U@", "r_U@", "w@"), SHARE: ()}
DATA_STATUS_METRIC = "observation_status"
DATA_STATUS_PREFIX = "observation_status@"
COMPARISON_CLAIM_TYPE = "comparison"
DATA_STATUS_CLAIM_TYPE = "data_status"


def check_signals(signals: object) -> dict[str, str]:
    """사례의 `signals`(신호 코드 → TRIGGERED/NOT_TRIGGERED)를 검사해 돌려준다. 키는 신호 코드 두 개 그대로다."""
    if not isinstance(signals, dict) or set(signals) != set(SIGNAL_CODES):
        raise ValueError(f"signals는 신호 코드 {list(SIGNAL_CODES)}를 키로 하는 객체여야 한다")
    for code in SIGNAL_CODES:
        if signals[code] not in SIGNAL_TRIGGERS:
            raise ValueError(f"signals.{code}는 {list(SIGNAL_TRIGGERS)} 중 하나여야 한다")
    return {code: signals[code] for code in SIGNAL_CODES}


def _rule(family: str, basis: str) -> tuple[str, str, tuple[str, ...]]:
    for rule in RULES.get(family, ()):
        if rule[0] == basis:
            return rule
    raise ValueError(f"계열 {family}에 판정 근거 {basis} 규칙이 없다")


def rule_status(family: str, basis: str) -> str:
    """계열과 판정 근거로 신호 상태를 돌려준다. 규칙표에 없는 조합은 오류다."""
    return _rule(family, basis)[1]


def rule_evidence(family: str, basis: str) -> tuple[str, ...]:
    """계열과 판정 근거의 필수 근거 코드."""
    return _rule(family, basis)[2]


def required_comparisons(family: str, basis: str) -> tuple[str, ...]:
    """그 판정 근거를 내기 전에 끝나 있어야 하는 필수 비교(COMPARISON_EVIDENCE 순서)."""
    evidence = rule_evidence(family, basis)
    return tuple(key for key, code in COMPARISON_EVIDENCE.items() if code in evidence)


def family_comparisons(family: str) -> tuple[str, ...]:
    """그 계열의 어느 규칙이든 요구하는 필수 비교. 근거 상태가 이 비교마다 완료 표시를 담아야 한다."""
    codes = {code for _basis, _status, evidence in RULES[family] for code in evidence}
    return tuple(key for key, code in COMPARISON_EVIDENCE.items() if code in codes)


def claim_families(claim: dict, case: dict) -> frozenset[str]:
    """typed claim 하나가 자료 계약 §9.4의 신호 계열 claim 요건에서 어느 계열로 세이는지 돌려준다.

    case는 사례 객체(`hs6`, `partner`, `month`)다. 세는 claim은 사례의 `hs6`(HS10 하위 기호면 그 부모 `hs6`)·대상국·
    비교월(`period`)을 가리키는 것뿐이다. `ALL` 분모 관측을 말하는 `data_status` 주장은 `partner`가 `ALL`이어도 센다.
    `comparison` 주장과 V·Q 주장은 어느 계열도 채우지 않는다. `data_status` 주장은 값이 `OBSERVED`가 아닌 관측
    상태일 때만 세고, HS10 하위 관측(`observation_status@<HS10 코드>`)은 단가, `ALL` 분모 관측은 점유율, 대상국 HS6
    관측(`observation_status`)은 두 계열에 든다.
    """
    if claim.get("claim_type") == COMPARISON_CLAIM_TYPE:
        return frozenset()
    if claim.get("hs6") != case["hs6"] or claim.get("period") != case["month"]:
        return frozenset()
    metric = claim.get("metric")
    if not isinstance(metric, str):
        return frozenset()
    partner = claim.get("partner")
    if claim.get("claim_type") == DATA_STATUS_CLAIM_TYPE:
        if claim.get("value") == OBSERVED or claim.get("value") not in OBSERVATION_STATUSES:
            return frozenset()
        is_status_metric = metric == DATA_STATUS_METRIC or _suffixed(metric, DATA_STATUS_PREFIX)
        if partner == ALL_PARTNER and is_status_metric:
            return frozenset({SHARE})
        if partner != case["partner"]:
            return frozenset()
        if _suffixed(metric, DATA_STATUS_PREFIX):
            return frozenset({UNIT_VALUE})
        if metric == DATA_STATUS_METRIC:
            return frozenset(SIGNAL_CODES)
        return frozenset()
    if partner != case["partner"]:
        return frozenset()
    return frozenset(family for family in SIGNAL_CODES
                     if metric in CLAIM_METRICS[family]
                     or any(_suffixed(metric, prefix) for prefix in CLAIM_METRIC_PREFIXES[family]))


def _suffixed(metric: str, prefix: str) -> bool:
    """metric이 `prefix` 뒤에 HS10 코드 자리가 비지 않은 모양인가."""
    return metric.startswith(prefix) and len(metric) > len(prefix)


def run(inp: object) -> object:
    """발동한 신호 계열마다 claim 요건의 지표 기호와 판정 근거별 필수 근거 목록을 돌려준다."""
    if not isinstance(inp, dict) or set(inp) != {"signals"}:
        raise ValueError("입력은 signals 키 하나만 가진 객체여야 한다")
    signals = check_signals(inp["signals"])
    triggered = [code for code in SIGNAL_CODES if signals[code] == TRIGGERED]
    if not triggered:
        raise ValueError("발동한 신호가 없다. 사례는 신호가 하나 이상 발동해야 한다")
    families = {}
    used: list[str] = []
    for family in triggered:
        rules = []
        for basis, status, evidence in RULES[family]:
            rules.append({"basis": basis, "status": status, "required_evidence": list(evidence)})
            used += [code for code in evidence if code not in used]
        families[family] = {
            "claim_metrics": list(CLAIM_METRICS[family]),
            "claim_metric_prefixes": list(CLAIM_METRIC_PREFIXES[family]),
            "rules": rules,
        }
    return {"families": families, "evidence_descriptions": {code: EVIDENCE_DESCRIPTIONS[code] for code in used}}
