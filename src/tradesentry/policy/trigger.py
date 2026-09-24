"""단위 P1 신호 발동.

단위 ID: P1
도메인명: policy_trigger
소유: M
입력: 지표 + 정책
출력: 계열·월별 신호 발동
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics, tradesentry.policy

계열(HS6 × 상대국)·월마다 두 신호(`unit_value`, `share`)의 발동 여부(`TRIGGERED`/`NOT_TRIGGERED`)를 정한다.
탐지 공식과 임계값은 개발 플랜 docs/plan/DEV_PLAN.md §6.1·§6.2, 단위는 자료 계약 docs/rules/DATA_CONTRACT_V1.md
§11.2다. 수치는 코드에 적지 않고 입력의 정책 객체에서 읽는다.

규칙
- 단가 신호: `r_U`(%)가 null이 아니고 |r_U| ≥ 정책의 단가 임계값이면 발동한다.
- 점유율 신호: `d_s`(pp)가 null이 아니고 |d_s| ≥ 정책의 점유율 임계값이면 발동한다.
- 비교는 표시 자릿수로 반올림하기 전의 값(입력 그대로)으로 한다. 임계값과 같으면 발동한다(개발 제안 "|r_U|≥30%").
- 지표가 null이면(기준월 값이 0이거나 미상, 중량 0 등. 자료 계약 §11.1) 그 신호는 발동하지 않고, 그 행을 숨기지
  않고 데이터 품질 목록(`data_quality`)에 사유 `metric_null`로 남긴다(개발 플랜 §6.2 끝 문단).
- 정책의 `min_amount`·`min_weight`가 null이 아니면 단가 신호에만 적용한다: 비교월과 기준월의 부모 HS6 행 금액이
  하나라도 `min_amount`보다 작거나 중량이 `min_weight`보다 작으면 단가 신호를 평가하지 않고(`NOT_TRIGGERED`)
  데이터 품질 목록에 사유 `below_min_amount`·`below_min_weight`로 남긴다. 적용 방식은 `policy_v1` 승인 때 확인할
  해석이다(로드맵 §6.3). 두 값이 없거나 null이면(개발용 정책 `dev-0.1`) 적용하지 않는다.
- 기준월은 비교월보다 정확히 12개월 앞이어야 한다(자료 계약 §11.4). 같은 (hs6, partner, month) 행이 두 번 오면 오류다.

입력(JSON 객체)
- `policy`: 정책 객체(단위 K4가 정책 파일에서 읽은 것). 판정 정책 단위가 읽는 키는 policy_values 한 곳에 모았다:
  `policy_version`(문자열), `thresholds`({"unit_value": %, "share": pp}), `min_amount`(USD), `min_weight`(kg).
  나머지 키는 읽지 않는다.
- `rows`: 행 목록. 행마다 `hs6`, `partner`(대상국, `ALL` 아님), `month`, `baseline_month`, `r_U`, `d_s`. 정책에
  `min_amount`·`min_weight`가 있으면 `amount_usd`·`net_weight_kg`({"month": 정수, "baseline_month": 정수}, 부모 HS6
  행의 값)도 있어야 한다. 그 밖의 키는 읽지 않는다.

출력(JSON 객체)
- `policy_version`: 쓴 정책 버전
- `triggers`: 행마다 {`hs6`, `partner`, `month`, `baseline_month`, `signals`}. `signals`는 사례 객체와 같은 모양이다
  (자료 계약 §2.3.5). (hs6, partner, month) 순으로 정렬한다.
- `data_quality`: 신호를 평가하지 못한 행 {`hs6`, `partner`, `month`, `baseline_month`, `signal`, `reason`}. 정렬한다.
"""
import re
from decimal import Decimal

from tradesentry.policy.required_evidence import ALL_PARTNER, NOT_TRIGGERED, SHARE, SIGNAL_CODES, TRIGGERED, UNIT_VALUE

HS6_RE = re.compile(r"^[0-9]{6}$")
PARTNER_RE = re.compile(r"^[A-Z]{2}$")
MONTH_RE = re.compile(r"^[0-9]{4}(0[1-9]|1[0-2])$")
METRIC_OF = {UNIT_VALUE: "r_U", SHARE: "d_s"}
MONTH_KEYS = ("month", "baseline_month")

REASON_METRIC_NULL = "metric_null"
REASON_BELOW_MIN_AMOUNT = "below_min_amount"
REASON_BELOW_MIN_WEIGHT = "below_min_weight"


def check_number(value: object, what: str) -> int | Decimal:
    """정수나 유한한 Decimal이면 그대로 돌려준다. float·참거짓·문자열은 받지 않는다(자료 계약 §11.1)."""
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        raise ValueError(f"{what}는 정수나 Decimal이어야 한다(float·참거짓·문자열은 받지 않는다)")
    if isinstance(value, Decimal) and not value.is_finite():
        raise ValueError(f"{what}가 유한한 수가 아니다")
    return value


def policy_values(policy: object) -> dict[str, object]:
    """정책 객체에서 판정 정책 단위가 읽는 값을 꺼낸다. 정책 키 이름을 읽는 곳은 이 함수 하나다.

    돌려주는 키: `policy_version`, `unit_value`(단가 임계값 %), `share`(점유율 임계값 pp), `min_amount`, `min_weight`
    (없으면 None). 임계값은 0보다 커야 하고 최소 기준은 0 이상이어야 한다.
    """
    if not isinstance(policy, dict):
        raise ValueError("policy는 객체여야 한다")
    version = policy.get("policy_version")
    if not isinstance(version, str) or not version:
        raise ValueError("policy.policy_version은 비어 있지 않은 문자열이어야 한다")
    thresholds = policy.get("thresholds")
    if not isinstance(thresholds, dict):
        raise ValueError("policy.thresholds는 신호 코드를 키로 하는 객체여야 한다")
    values: dict[str, object] = {"policy_version": version}
    for code in SIGNAL_CODES:
        threshold = check_number(thresholds.get(code), f"policy.thresholds.{code}")
        if threshold <= 0:
            raise ValueError(f"policy.thresholds.{code}는 0보다 커야 한다")
        values[code] = threshold
    for key in ("min_amount", "min_weight"):
        raw = policy.get(key)
        if raw is not None and check_number(raw, f"policy.{key}") < 0:
            raise ValueError(f"policy.{key}는 0 이상이어야 한다")
        values[key] = raw
    return values


def baseline_of(month: str) -> str:
    """비교월 YYYYMM의 기준월(12개월 앞, 전년 같은 달)."""
    return f"{int(month[:4]) - 1:04d}{month[4:]}"


def _check_key_fields(row: dict, index: int) -> tuple[str, str, str, str]:
    hs6, partner, month, baseline = (row.get(k) for k in ("hs6", "partner", "month", "baseline_month"))
    if not isinstance(hs6, str) or not HS6_RE.match(hs6):
        raise ValueError(f"rows[{index}].hs6는 6자리 숫자 문자열이어야 한다")
    if not isinstance(partner, str) or partner == ALL_PARTNER or not PARTNER_RE.match(partner):
        raise ValueError(f"rows[{index}].partner는 대상국 2자리 코드여야 한다({ALL_PARTNER} 아님)")
    for key, value in (("month", month), ("baseline_month", baseline)):
        if not isinstance(value, str) or not MONTH_RE.match(value):
            raise ValueError(f"rows[{index}].{key}는 YYYYMM이어야 한다")
    if baseline != baseline_of(month):
        raise ValueError(f"rows[{index}].baseline_month는 month의 12개월 앞이어야 한다")
    return hs6, partner, month, baseline


def _parent_values(row: dict, key: str, index: int) -> list[int]:
    pair = row.get(key)
    if not isinstance(pair, dict) or set(pair) != set(MONTH_KEYS):
        raise ValueError(f"rows[{index}].{key}는 month·baseline_month 두 키의 객체여야 한다(최소 기준 적용에 필요)")
    values = []
    for month_key in MONTH_KEYS:
        value = pair[month_key]
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"rows[{index}].{key}.{month_key}는 정수여야 한다")
        values.append(value)
    return values


def run(inp: object) -> object:
    """계열·월 행마다 두 신호의 발동 여부를 정하고, 평가하지 못한 행을 데이터 품질 목록에 남긴다."""
    if not isinstance(inp, dict) or set(inp) != {"policy", "rows"}:
        raise ValueError("입력은 policy와 rows 두 키만 가진 객체여야 한다")
    policy = policy_values(inp["policy"])
    rows = inp["rows"]
    if not isinstance(rows, list):
        raise ValueError("rows는 목록이어야 한다")
    triggers, quality, seen = [], [], set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"rows[{index}]는 객체여야 한다")
        hs6, partner, month, baseline = _check_key_fields(row, index)
        if (hs6, partner, month) in seen:
            raise ValueError(f"rows[{index}]: 같은 (hs6, partner, month) 행이 이미 있다")
        seen.add((hs6, partner, month))
        where = {"hs6": hs6, "partner": partner, "month": month, "baseline_month": baseline}
        signals = {}
        for code in SIGNAL_CODES:
            metric = METRIC_OF[code]
            if metric not in row:
                raise ValueError(f"rows[{index}]에 {metric} 키가 없다(값이 없으면 null로 둔다)")
            value = row[metric]
            if value is None:
                signals[code] = NOT_TRIGGERED
                quality.append({**where, "signal": code, "reason": REASON_METRIC_NULL})
                continue
            check_number(value, f"rows[{index}].{metric}")
            reasons = []
            if code == UNIT_VALUE:
                if policy["min_amount"] is not None and \
                        min(_parent_values(row, "amount_usd", index)) < policy["min_amount"]:
                    reasons.append(REASON_BELOW_MIN_AMOUNT)
                if policy["min_weight"] is not None and \
                        min(_parent_values(row, "net_weight_kg", index)) < policy["min_weight"]:
                    reasons.append(REASON_BELOW_MIN_WEIGHT)
            if reasons:
                signals[code] = NOT_TRIGGERED
                quality += [{**where, "signal": code, "reason": reason} for reason in reasons]
                continue
            signals[code] = TRIGGERED if abs(value) >= policy[code] else NOT_TRIGGERED
        triggers.append({**where, "signals": signals})
    triggers.sort(key=lambda t: (t["hs6"], t["partner"], t["month"]))
    quality.sort(key=lambda q: (q["hs6"], q["partner"], q["month"], q["signal"], q["reason"]))
    return {"policy_version": policy["policy_version"], "triggers": triggers, "data_quality": quality}
