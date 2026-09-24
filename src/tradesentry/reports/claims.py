"""단위 R1 typed claim 채우기.

단위 ID: R1
도메인명: reports_claims
소유: M
입력: 검증된 `metric`
출력: typed claim(모드별)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.metrics, tradesentry.reports

정본: 자료 계약 docs/rules/DATA_CONTRACT_V1.md §6(typed claim), §11.2(기호와 단위), §11.3(표시 자릿수),
§9.1(수의 원문 표기), 개발 플랜 docs/plan/DEV_PLAN.md §7.3(모드별 숫자 채우기).

입력(JSON 객체 하나)
- `mode`: `checklist` | `agent` | `full` | `freeform`
- `case`: 사례 객체(자료 계약 §2.3.5). `partner`로 비교국 주장(`comparison`)을 가른다.
- 틀 채우기 모드(`checklist`·`agent`·`full`)
  - `metrics`: 검증된 `metric` 객체 목록(자료 계약 §2.3.4). 지표 기호와 대상은 `inputs`의 `metric`·`hs6`·`partner`·
    `period`·`baseline_period`에서 읽는다(아래 "해석").
  - `statuses`: 자료 상태 항목 목록. 모양은 이 단위가 정한다:
    `{"status_id", "hs6", "partner", "period", "hs10"(없으면 null), "observation_status", "evidence_ids",
    "baseline_period"(생략 가능)}`. 도구 봉투의 `missingness` 항목을 이 모양으로 옮기는 일은 부르는 쪽이 한다.
  - `requests`: 채울 주장 목록. 원소는 `{"claim_id", "metric_id"}` 또는 `{"claim_id", "status_id"}`다. 조사자(모델)나
    `checklist` 규칙은 어떤 검증된 값을 주장할지만 고르고, 숫자·단위·근거·방향·문장은 이 단위가 채운다.
- `freeform`: `claims`(모델이 쓴 typed claim 목록)를 그대로 돌려준다. 값·단위·근거를 채우거나 고치지 않는다.

출력: `{"claims": [typed claim, ...], "rejected": [{"claim_id", "reason"}, ...]}`
- typed claim은 계약 필드 12개만 담는다. 수 `value`는 §11.3 표시 자릿수의 십진 표기(끝자리 0 포함)이고, 정수 자릿수
  기호(`V`, `Q`)는 int다. 반올림은 Decimal `ROUND_HALF_UP`이고 음수 0은 0으로 적는다. 방향은 표시 값의 부호다.
- 채울 수 없는 요청(없는 `metric_id`, 값이 null인 지표, 계약과 다른 단위, 근거 없는 지표 등)은 주장을 만들지 않고
  `rejected`에 사유를 적는다. 계산 불가는 자료 상태(`data_status`) 주장으로 쓴다(룰북 B3-1).
- 입력을 바꾸지 않는다.

해석(계약이 정하지 않아 이 단위가 정한 것. 조립(AS2)에서 확인한다)
- `metric.inputs` 안의 지표 기호 키는 typed claim과 같은 이름 `metric`으로 본다(계약 §2.3.4 "typed claim과 같은
  이름"). 이 해석은 `_metric_symbol` 한 곳에만 있다.
- 아래 기호·단위·자릿수 표는 자료 계약 §11.2·§11.3의 사본이다. 계약 커널(단위 K1)과 자릿수 단위(X4)가 생기면 조립
  점검에서 그쪽 import로 바꾼다(단위 표 docs/plan/UNITS.md §6 조립 부산물 4).
"""
import copy
from decimal import ROUND_HALF_UP, Decimal

MODES = ("checklist", "agent", "full", "freeform")
TEMPLATE_MODES = ("checklist", "agent", "full")
CLAIM_FIELDS = ("claim_id", "claim_type", "hs6", "partner", "period", "baseline_period", "metric", "value", "unit",
                "direction", "evidence_ids", "text")
OBSERVATION_STATUSES = ("OBSERVED", "NOT_COLLECTED", "REQUEST_FAILED", "UNRESOLVED_ZERO", "CONFIRMED_NO_TRADE")

# 자료 계약 §11.2(단위)·§11.3(표시 자릿수) 사본. 키는 `@` 앞 기호다(`U@<HS10>`은 `U`, `w@<HS10>`은 `w`).
UNIT_OF = {"V": "USD", "Q": "kg", "U": "USD/kg", "r_U": "%", "s": "%", "d_s": "pp",
           "within_effect": "USD/kg", "mix_effect": "USD/kg", "residual": "USD/kg", "w": "%"}
DIGITS_OF = {"V": 0, "Q": 0, "U": 2, "r_U": 1, "s": 1, "d_s": 1,
             "within_effect": 2, "mix_effect": 2, "residual": 2, "w": 1}
SUB_ITEM_BASES = ("U", "r_U", "w")  # `<기호>@<HS10 코드>`로 쓸 수 있는 기호(계약 §6.2). `w`는 `@`로만 쓴다
DECOMPOSITION = ("within_effect", "mix_effect", "residual")
CHANGE_BASES = ("r_U", "d_s") + DECOMPOSITION  # 변화를 말하는 기호(방향이 UP·DOWN·FLAT)

STATUS_LABEL = {"OBSERVED": "관측됨", "NOT_COLLECTED": "미수집", "REQUEST_FAILED": "요청 실패",
                "UNRESOLVED_ZERO": "응답에 행 없음", "CONFIRMED_NO_TRADE": "무거래 확정"}
EFFECT_LABEL = {"within_effect": "하위품목 단가 변화 효과", "mix_effect": "구성 변화 효과", "residual": "분해 잔차"}


def run(inp: object) -> object:
    """진입 함수. 모드에 따라 검증된 값으로 typed claim을 채우거나(틀 채우기) 모델의 주장을 그대로 돌려준다."""
    if not isinstance(inp, dict):
        raise ValueError("R1 입력은 JSON 객체여야 한다")
    mode = inp.get("mode")
    if mode not in MODES:
        raise ValueError("R1 입력의 mode가 checklist·agent·full·freeform 가운데 하나가 아니다")
    case = inp.get("case")
    if not isinstance(case, dict) or not isinstance(case.get("partner"), str):
        raise ValueError("R1 입력에 사례(case)와 그 partner가 없다")
    if mode == "freeform":
        claims = inp.get("claims", [])
        if not isinstance(claims, list):
            raise ValueError("freeform의 claims는 목록이어야 한다")
        return {"claims": copy.deepcopy(claims), "rejected": []}
    return fill(case, inp.get("metrics", []), inp.get("statuses", []), inp.get("requests", []))


def fill(case: dict, metrics: list, statuses: list, requests: list) -> dict:
    """틀 채우기: 요청마다 검증된 지표나 자료 상태 항목에서 typed claim 하나를 만든다."""
    for name, value in (("metrics", metrics), ("statuses", statuses), ("requests", requests)):
        if not isinstance(value, list):
            raise ValueError(f"R1 입력의 {name}는 목록이어야 한다")
    by_metric = _index(metrics, "metric_id")
    by_status = _index(statuses, "status_id")
    claims: list[dict] = []
    rejected: list[dict] = []
    seen: set[str] = set()
    for request in requests:
        claim_id = request.get("claim_id") if isinstance(request, dict) else None
        try:
            claim = _fill_one(request, claim_id, seen, by_metric, by_status, case["partner"])
        except _Reject as exc:
            rejected.append({"claim_id": claim_id if isinstance(claim_id, str) else None, "reason": str(exc)})
            continue
        seen.add(claim_id)
        claims.append(claim)
    return {"claims": claims, "rejected": rejected}


class _Reject(Exception):
    """채울 수 없는 요청. 주장을 만들지 않고 사유를 rejected에 적는다."""


def _fill_one(request: object, claim_id: object, seen: set, by_metric: dict, by_status: dict,
              case_partner: str) -> dict:
    if not isinstance(request, dict):
        raise _Reject("요청이 객체가 아니다")
    if not isinstance(claim_id, str) or not claim_id or claim_id.startswith("prose:"):
        raise _Reject("claim_id가 비었거나 prose:로 시작한다")
    if claim_id in seen:
        raise _Reject("같은 claim_id가 이미 있다")
    has_metric, has_status = "metric_id" in request, "status_id" in request
    if has_metric == has_status:
        raise _Reject("요청은 metric_id와 status_id 가운데 하나만 가리킨다")
    if has_metric:
        source = by_metric.get(request["metric_id"]) if isinstance(request["metric_id"], str) else None
        if source is None:
            raise _Reject("검증된 지표 목록에 없는 metric_id다")
        return claim_from_metric(claim_id, source, case_partner)
    source = by_status.get(request["status_id"]) if isinstance(request["status_id"], str) else None
    if source is None:
        raise _Reject("자료 상태 목록에 없는 status_id다")
    return claim_from_status(claim_id, source)


def _index(items: list, key: str) -> dict:
    found: dict = {}
    for item in items:
        if isinstance(item, dict) and isinstance(item.get(key), str) and item[key] not in found:
            found[item[key]] = item
    return found


def _metric_symbol(metric: dict) -> object:
    """지표 기호. 계약 §2.3.4는 기호를 inputs에 담으라고만 적었고, 키 이름은 typed claim과 같은 metric으로 본다."""
    inputs = metric.get("inputs")
    return inputs.get("metric") if isinstance(inputs, dict) else None


def base_symbol(symbol: str) -> str | None:
    """기호의 `@` 앞부분. 계약 §11.2 표에 없는 기호나 정의하지 않은 `@` 조합이면 None이다."""
    base, at, code = symbol.partition("@")
    if at:
        return base if base in SUB_ITEM_BASES and code and "@" not in code else None
    return base if base in UNIT_OF and base != "w" else None


def display_value(symbol: str, value: object) -> int | Decimal:
    """§11.3 표시 자릿수로 사사오입한 값. 정수 자릿수 기호는 int, 나머지는 끝자리 0을 지닌 Decimal이다."""
    base = base_symbol(symbol)
    if base is None:
        raise ValueError(f"표시 자릿수가 정해지지 않은 기호다: {symbol}")
    number = _as_decimal(value)
    digits = DIGITS_OF[base]
    shown = number.quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP)
    if shown == 0:
        shown = shown.copy_abs()  # 음수 0(-0.0)을 0.0으로 적는다
    return int(shown) if digits == 0 else shown


def _as_decimal(value: object) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        raise ValueError("수는 int나 Decimal이어야 한다(float·문자열은 받지 않는다)")
    number = Decimal(value)
    if not number.is_finite():
        raise ValueError("NaN이나 무한대는 쓰지 않는다")
    return number


def direction_of(shown: int | Decimal) -> str:
    """표시 값의 부호로 정한 방향. 반올림해 0이면 FLAT이다(룰북 B3-1 "방향의 기대값")."""
    return "UP" if shown > 0 else "DOWN" if shown < 0 else "FLAT"


def claim_type_of(symbol: str, partner: str, case_partner: str) -> str:
    """기호와 상대국으로 정한 claim_type(계약 §6.2). 대상국·전체국가(ALL)가 아닌 상대국은 comparison이다."""
    base = base_symbol(symbol)
    if partner not in (case_partner, "ALL"):
        return "comparison"
    if base == "r_U":
        return "change"
    if base == "s":
        return "share"
    if base == "d_s":
        return "share_change"
    if base in DECOMPOSITION:
        return "decomposition"
    return "value"


def claim_from_metric(claim_id: str, metric: dict, case_partner: str) -> dict:
    """검증된 metric 객체 하나로 typed claim 하나를 채운다."""
    symbol = _metric_symbol(metric)
    base = base_symbol(symbol) if isinstance(symbol, str) else None
    if base is None:
        raise _Reject("지표 기호가 계약 §11.2에 없다")
    inputs = metric["inputs"]
    hs6, partner, period = inputs.get("hs6"), inputs.get("partner"), inputs.get("period")
    if not all(isinstance(v, str) and v for v in (hs6, partner, period)):
        raise _Reject("지표의 대상(hs6·partner·period)이 없다")
    if metric.get("unit") != UNIT_OF[base]:
        raise _Reject("지표 단위가 계약 §11.2의 단위와 다르다")
    if metric.get("value") is None:
        raise _Reject("값이 없는 지표(계산 불가)다. 자료 상태 주장으로 쓴다")
    try:
        shown = display_value(symbol, metric["value"])
    except ValueError as exc:
        raise _Reject(f"지표 값을 표시할 수 없다({exc})") from None
    evidence = metric.get("evidence_ids")
    if not isinstance(evidence, list) or not evidence or not all(isinstance(e, str) and e for e in evidence):
        raise _Reject("근거 ID가 없는 지표다")
    changes = base in CHANGE_BASES
    baseline = inputs.get("baseline_period") if changes else None
    if changes and not (isinstance(baseline, str) and baseline):
        raise _Reject("변화 지표에 기준월(baseline_period)이 없다")
    claim = {"claim_id": claim_id, "claim_type": claim_type_of(symbol, partner, case_partner), "hs6": hs6,
             "partner": partner, "period": period, "baseline_period": baseline, "metric": symbol, "value": shown,
             "unit": UNIT_OF[base], "direction": direction_of(shown) if changes else "NA",
             "evidence_ids": list(evidence), "text": ""}
    claim["text"] = metric_text(claim, case_partner)
    return claim


def claim_from_status(claim_id: str, status: dict) -> dict:
    """자료 상태 항목 하나로 data_status 주장 하나를 채운다."""
    hs6, partner, period = status.get("hs6"), status.get("partner"), status.get("period")
    if not all(isinstance(v, str) and v for v in (hs6, partner, period)):
        raise _Reject("자료 상태 항목의 대상(hs6·partner·period)이 없다")
    code = status.get("observation_status")
    if code not in OBSERVATION_STATUSES:
        raise _Reject("관측 상태 코드가 계약 §3.4의 다섯 값이 아니다")
    hs10 = status.get("hs10")
    if hs10 is not None and not (isinstance(hs10, str) and hs10 and "@" not in hs10):
        raise _Reject("hs10이 문자열 코드가 아니다")
    evidence = status.get("evidence_ids")
    if not isinstance(evidence, list) or not evidence or not all(isinstance(e, str) and e for e in evidence):
        raise _Reject("근거 ID가 없는 자료 상태 항목이다")
    baseline = status.get("baseline_period")
    if baseline is not None and not (isinstance(baseline, str) and baseline):
        raise _Reject("baseline_period가 문자열이 아니다")
    claim = {"claim_id": claim_id, "claim_type": "data_status", "hs6": hs6, "partner": partner, "period": period,
             "baseline_period": baseline,
             "metric": "observation_status" if hs10 is None else f"observation_status@{hs10}",
             "value": code, "unit": None, "direction": "NA", "evidence_ids": list(evidence), "text": ""}
    claim["text"] = status_text(claim, hs10)
    return claim


# ---- 한국어 문장 틀 -------------------------------------------------------------------------------------------
# 문장 속 숫자는 그 주장의 value와 같은 자리로 적는다. 그래서 산문 검사(룰북 B3-2)에서 그 주장 자신이 뒷받침한다.
# 숫자는 value 말고는 연월(EX-1)과 "HS <코드>"(EX-2)처럼 산문 검사에서 빠지는 표기로만 쓴다.


def month_label(period: str) -> str:
    """`YYYYMM`을 "YYYY년 M월"로 적는다. 형식이 다르면 원문 그대로다."""
    if len(period) == 6 and period.isdigit() and 1 <= int(period[4:]) <= 12:
        return f"{period[:4]}년 {int(period[4:])}월"
    return period


def number_text(value: int | Decimal) -> str:
    """표시 값을 천 단위 쉼표와 끝자리 0을 지닌 십진 표기로 적는다."""
    return format(value, ",") if isinstance(value, int) else format(value, ",f")


def subject_prefix(partner: str, case_partner: str) -> str:
    if partner == "ALL":
        return "전체국가 "
    if partner != case_partner:
        return f"비교국 {partner}의 "
    return ""


def metric_text(claim: dict, case_partner: str) -> str:
    """지표 주장의 한국어 문장."""
    symbol, value, direction = claim["metric"], claim["value"], claim["direction"]
    base, _, code = symbol.partition("@")
    head = f"{month_label(claim['period'])} {subject_prefix(claim['partner'], case_partner)}"
    item = f"하위품목 HS {code}의 " if code else ""
    shown, magnitude = number_text(value), number_text(abs(value))
    if base == "V":
        return f"{head}수입금액은 {shown}달러다."
    if base == "Q":
        return f"{head}순중량은 {shown}kg이다."
    if base == "U":
        return f"{head}{item}단가는 kg당 {shown}달러다."
    if base == "w":
        return f"{head}{item}중량 비중은 {shown}%다."
    if base == "s":
        return f"{head}점유율은 {shown}%다."
    if base == "r_U":
        return _change_text(f"{head}{item}단가", ("는", "가"), direction, magnitude, shown, "%")
    if base == "d_s":
        return _change_text(f"{head}점유율", ("은", "이"), direction, magnitude, shown, "%p")
    return f"{head}단가 변화 가운데 {EFFECT_LABEL[base]}는 kg당 {shown}달러다."


def _change_text(subject: str, particles: tuple[str, str], direction: str, magnitude: str, shown: str,
                 unit: str) -> str:
    topic, nominative = particles
    if direction == "FLAT":
        return f"{subject}{topic} 전년 같은 달보다 변화가 없다({shown}{unit})."
    return f"{subject}{nominative} 전년 같은 달보다 {magnitude}{unit} {'높다' if direction == 'UP' else '낮다'}."


def status_text(claim: dict, hs10: str | None) -> str:
    """자료 상태 주장의 한국어 문장."""
    partner = "전체국가" if claim["partner"] == "ALL" else claim["partner"]
    target = f"하위품목 HS {hs10}" if hs10 is not None else f"HS {claim['hs6']}"
    code = claim["value"]
    return f"{month_label(claim['period'])} {partner} {target} 자료 상태는 {code}({STATUS_LABEL[code]})다."
