"""단위 X4 자릿수·반올림.

단위 ID: X4
도메인명: metrics_rounding
소유: D
입력: 값
출력: 표시 값(`ROUND_HALF_UP`)·중량 허용오차 판정
허용 import: 표준 라이브러리, tradesentry.contract

지표 패키지(단위 X1~X4)의 공통 유틸이다. 단위 X1~X3과 보고서·검증기 단위(R2·R3)가 쓴다. 다른 지표 단위를 부르지
않는 잎 모듈이다. 정본은 자료 계약 docs/rules/DATA_CONTRACT_V1.md §11(단위와 정밀도)이다. 머리 주석의 입력·출력
줄은 단위 표 docs/plan/UNITS.md §3.3의 문구이고, 구체적인 모양은 아래와 결정 기록
docs/tracking/decisions/의 DT2 기록(data-decision-dt2-metrics)에 있다.

- 기호표: §11.2의 단위와 §11.3의 표시 자릿수. HS10 하위 기호는 U@·r_U@·w@ 뒤에 10자리 코드만 받는다(§6.2).
- 반올림: 값을 분수(fractions.Fraction)로 정확히 바꾼 뒤 사사오입(ROUND_HALF_UP, 절댓값 기준 5 이상이면 0에서
  먼 쪽)을 한 번만 한다. Decimal 기본 문맥(28자리)의 나눗셈이나 float를 거치지 않는다. -0.0은 0.0으로 낸다.
  표시 자릿수가 0인 기호(V·Q)는 int, 나머지는 끝자리 0을 지킨 Decimal이다.
- 중량 대조: 허용오차는 §11.1의 꼴 `행당 반올림 kg × (HS10 행수 + 1)`이다. 행당 kg(출발값 0.5)는 정책 수치라
  코드에 두지 않고 인자로 받는다. 판정은 기존 수집기와 같게 |부모 Q − HS10 Q 합| ≤ 허용오차면 통과다.
- metric 객체: §2.3.4의 키 8개(metric_id, formula_version, inputs, evidence_ids, value, unit,
  comparability_flags, tolerance)를 만든다. value는 정확 계산 값을 §11.3 자릿수로 한 번 반올림한 값이다.
  반올림 전 값은 inputs의 정수로 다시 계산한다(단위 X1·X2·X3의 exact_value, 어긋남 검사는 checked_exact).
  metric_id는 스냅샷 ID와 metric_id를 뺀 나머지 내용의 sha256 앞 16자에 기호를 붙인 결정적 문자열이다(형식은
  계약이 정하지 않는다, §4.5). 스냅샷 ID를 해시에 넣으므로 근거 ID가 빈 지표도 스냅샷이 다르면 ID가 다르다. 단위
  X1~X3은 스냅샷 ID를 늘 넘기고, 근거 ID는 모두 `ev:<그 스냅샷 ID>:`로 시작해야 한다(§4.4 풀림 규칙 2).
- 입력 검사: 대상(hs6·partner·period·baseline_period)과 관측 행(observation 키 month·hs_code·amount_usd·
  net_weight_kg·observation_status와 근거 ID 목록 evidence_ids)을 본다. 계약과 다른 입력은 ValueError·TypeError로
  멈춘다. 행 규칙(부모 HS6 행 고르기, ALL 중복 제거)은 자료 접근층이 적용한 뒤 넘긴다고 보고, 여기서는 섞이면 안 되는
  것(한 달에 값 행과 상태 행)만 막는다.
- 계약이 값을 정하지 않은 것(formula_version 값, comparability_flags의 사유 문자열, 입출력 키 이름)은 이 파일의
  상수와 각 단위의 머리말에 모았다.

run 입력(JSON 객체)
- values: [{"metric": 기호, "value": 수 또는 null}, ...]
- weight_checks: [{"Q_parent": 정수, "Q_hs10": 정수(HS10 행 중량 합), "row_count": 정수(HS10 행수),
  "weight_rounding_kg": 수}, ...]
run 출력
- values: [{"metric": 기호, "unit": 단위, "value": 표시 값 또는 null}, ...]
- weight_checks: [{"difference": |Q_parent − Q_hs10|, "tolerance": 허용오차, "within_tolerance": 참/거짓}, ...]
"""
import hashlib
import json
import re
from decimal import Decimal
from fractions import Fraction

SCHEMA_VERSION = 1  # 자료 계약 버전(인수 조건 1)
FORMULA_VERSION = "1"  # 자료 계약 §11.2 공식의 첫 구현. 공식을 바꾸면 올린다(§2.3.4)

# 자료 계약 §3 관측 상태 코드. 계약 커널(단위 K1)이 생기면 그쪽 정의와 같아야 한다.
OBSERVED = "OBSERVED"
CONFIRMED_NO_TRADE = "CONFIRMED_NO_TRADE"
MISSING_STATUSES = frozenset({"NOT_COLLECTED", "REQUEST_FAILED", "UNRESOLVED_ZERO"})
OBSERVATION_STATUSES = frozenset({OBSERVED, CONFIRMED_NO_TRADE}) | MISSING_STATUSES

# comparability_flags의 사유 문자열(계약이 값 집합을 정하지 않는다, §2.3.4). 관측 상태 때문이면 그 코드를 그대로 쓴다.
ZERO_WEIGHT = "zero_weight"  # 중량(또는 중량 합)이 0이라 단가·비중을 계산하지 않는다(§11.1)
ZERO_BASELINE = "zero_baseline"  # 기준월 단가가 0이라 변화율을 계산하지 않는다(§11.1)
ZERO_DENOMINATOR = "zero_denominator"  # 전체국가(ALL) 금액이 0이라 점유율을 계산하지 않는다
VALUE_MISSING = "value_missing"  # OBSERVED 행인데 금액이나 중량 칸이 비었다
HS10_ABSENT = "hs10_absent"  # 그 달에 그 HS10 행이 없다(신설·소멸 식별, 0으로 채우지 않는다)
HS10_SET_CHANGED = "hs10_set_changed"  # 두 시점의 HS10 집합이 달라 분해하지 않는다(§11.2)
PARENT_MISMATCH = "parent_mismatch"  # 부모 대조(금액 정확 일치, 중량 허용오차)를 통과하지 못했다

# §11.2 단위와 §11.3 표시 자릿수
_SYMBOLS: dict[str, tuple[str, int]] = {
    "V": ("USD", 0),
    "Q": ("kg", 0),
    "U": ("USD/kg", 2),
    "r_U": ("%", 1),
    "s": ("%", 1),
    "d_s": ("pp", 1),
    "within_effect": ("USD/kg", 2),
    "mix_effect": ("USD/kg", 2),
    "residual": ("USD/kg", 2),
}
# HS10 하위 기호(§6.2, §11.2): U@·r_U@는 @ 앞 기호를 따르고 w@는 %, 소수 1자리다.
_HS10_SYMBOLS: dict[str, tuple[str, int]] = {"U": ("USD/kg", 2), "r_U": ("%", 1), "w": ("%", 1)}

_HS6_RE = re.compile(r"[0-9]{6}")
_HS10_RE = re.compile(r"[0-9]{10}")
_PARTNER_RE = re.compile(r"[A-Z]{2}")
_MONTH_RE = re.compile(r"[0-9]{4}(0[1-9]|1[0-2])")


def unit_and_places(symbol: str) -> tuple[str, int]:
    """지표 기호의 단위(§11.2)와 표시 자릿수(§11.3). 계약에 없는 기호는 ValueError다."""
    if not isinstance(symbol, str):
        raise TypeError("지표 기호는 문자열이다")
    base, at, code = symbol.partition("@")
    if not at and symbol in _SYMBOLS:
        return _SYMBOLS[symbol]
    if at and base in _HS10_SYMBOLS and _HS10_RE.fullmatch(code):
        return _HS10_SYMBOLS[base]
    raise ValueError(f"자료 계약 §11.2·§11.3에 없는 지표 기호다: {symbol!r}")


def is_hs10_code(code: object) -> bool:
    """10자리 숫자 HS10 코드인가."""
    return isinstance(code, str) and _HS10_RE.fullmatch(code) is not None


def to_fraction(value: object) -> Fraction:
    """int·Decimal·Fraction을 오차 없는 분수로 바꾼다. float·bool과 유한하지 않은 Decimal은 받지 않는다."""
    if isinstance(value, bool) or not isinstance(value, (int, Decimal, Fraction)):
        raise TypeError(f"수는 int나 Decimal이어야 한다(float 금지): {type(value).__name__}")
    if isinstance(value, Decimal) and not value.is_finite():
        raise ValueError("유한한 수가 아니다")
    return Fraction(value)


def round_half_up(value: object, places: int) -> Decimal:
    """값을 소수 places자리로 사사오입한다(한 번만, 정확히). 결과 Decimal은 끝자리 0을 지킨다."""
    if isinstance(places, bool) or not isinstance(places, int) or places < 0:
        raise ValueError("자릿수는 0 이상의 정수다")
    scaled = to_fraction(value) * 10 ** places
    whole, rest = divmod(abs(scaled.numerator), scaled.denominator)
    if 2 * rest >= scaled.denominator:
        whole += 1
    digits = -whole if scaled < 0 else whole  # whole이 0이면 부호가 없어진다(-0.0을 내지 않는다)
    return Decimal(f"{digits}E-{places}")  # 문자열로 만들어 문맥 반올림을 거치지 않는다


def display(symbol: str, value: object) -> int | Decimal | None:
    """기호의 표시 값(§11.3). null은 null이다. 자릿수 0(V·Q)은 int, 나머지는 Decimal이다."""
    _, places = unit_and_places(symbol)
    if value is None:
        return None
    shown = round_half_up(value, places)
    return int(shown) if places == 0 else shown


def weight_tolerance(row_count: int, weight_rounding_kg: int | Decimal) -> Decimal:
    """중량 대조 허용오차 `행당 반올림 kg × (HS10 행수 + 1)`(§11.1)."""
    require_count(row_count, "HS10 행수")
    if isinstance(weight_rounding_kg, bool) or not isinstance(weight_rounding_kg, (int, Decimal)):
        raise TypeError("행당 반올림 kg는 int나 Decimal이다(float 금지)")
    if not Decimal(weight_rounding_kg).is_finite() or weight_rounding_kg < 0:
        raise ValueError("행당 반올림 kg는 0 이상의 유한한 수다")
    return Decimal(weight_rounding_kg) * (row_count + 1)


def weight_within_tolerance(q_parent: int, q_hs10: int, row_count: int, weight_rounding_kg: int | Decimal) -> bool:
    """부모 중량과 HS10 행 중량 합의 차가 허용오차 안인가(같으면 통과)."""
    require_count(q_parent, "부모 중량")
    require_count(q_hs10, "HS10 중량 합")
    return abs(q_parent - q_hs10) <= weight_tolerance(row_count, weight_rounding_kg)


def metric(symbol: str, *, hs6: str, partner: str, period: str, baseline_period: str | None,
           values: dict[str, object], evidence_ids: list[str], value: object,
           flags: list[str] | tuple[str, ...] = (), tolerance: Decimal | None = None,
           snapshot_id: str | None = None) -> dict[str, object]:
    """자료 계약 §2.3.4 `metric` 객체를 만든다.

    value는 정확한 값(int·Fraction) 또는 None이다. 표시 자릿수로 한 번 반올림해 담는다. None이면 사유(flags)가
    있어야 한다. values는 계산에 쓴 입력값(정수나 null)이다. 근거 ID는 순서를 지키며 중복을 뺀다. snapshot_id를
    주면 근거 ID가 모두 그 스냅샷의 것인지 보고, metric_id 해시에 넣는다(단위 X1~X3은 늘 준다).
    """
    unit, _ = unit_and_places(symbol)
    if value is None and not flags:
        raise ValueError(f"{symbol}: 값이 null이면 사유를 comparability_flags에 적는다(§2.3.4)")
    if snapshot_id is not None:
        check_snapshot_id(snapshot_id)
        for ev in evidence_ids:
            if not ev.startswith(f"ev:{snapshot_id}:"):
                raise ValueError(f"{symbol}: 근거 ID가 스냅샷 {snapshot_id}의 것이 아니다(§4.4 풀림 규칙 2): {ev!r}")
    inputs: dict[str, object] = {"metric": symbol, "hs6": hs6, "partner": partner, "period": period,
                                 "baseline_period": baseline_period}
    inputs.update(values)
    body: dict[str, object] = {
        "formula_version": FORMULA_VERSION,
        "inputs": inputs,
        "evidence_ids": list(dict.fromkeys(evidence_ids)),
        "value": display(symbol, value),
        "unit": unit,
        "comparability_flags": sorted(set(flags)),
        "tolerance": tolerance,
    }
    hashed = body if snapshot_id is None else {"snapshot_id": snapshot_id, **body}
    text = json.dumps(hashed, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=_json_default)
    return {"metric_id": f"{symbol}-{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}", **body}


def check_snapshot_id(snapshot_id: object) -> str:
    """스냅샷 ID 형식: 빈 문자열이 아니고 `:`와 공백이 없다(§4.4 근거 ID 조각 규칙)."""
    if not isinstance(snapshot_id, str) or not snapshot_id or ":" in snapshot_id \
            or any(ch.isspace() for ch in snapshot_id):
        raise ValueError(f"snapshot_id 형식이 계약과 다르다: {snapshot_id!r}")
    return snapshot_id


def parse_snapshot_id(inp: dict) -> str:
    """단위 X1~X3 입력의 snapshot_id(필수)."""
    if "snapshot_id" not in inp:
        raise ValueError("snapshot_id가 없다(근거 ID와 metric_id가 가리키는 스냅샷)")
    return check_snapshot_id(inp["snapshot_id"])


def checked_exact(metric: dict, exact: Fraction | None) -> Fraction | None:
    """다시 계산한 반올림 전 값(exact)이 metric 객체의 value(표시 값)와 맞는지 보고 돌려준다.

    지표 단위의 exact_value가 쓴다. null 여부가 다르거나, exact를 표시 자릿수로 반올림한 값이 value와 다르면
    ValueError다.
    """
    recorded = metric["value"]
    if recorded is not None and (isinstance(recorded, bool) or not isinstance(recorded, (int, Decimal))):
        raise TypeError("metric 객체의 value는 int나 Decimal이다")
    if (exact is None) != (recorded is None) or \
            (exact is not None and display(metric["inputs"]["metric"], exact) != recorded):
        raise ValueError("metric 객체의 value와 inputs가 맞지 않는다")
    return exact


def parse_target(inp: object) -> dict[str, str]:
    """입력의 대상(hs6·partner·period·baseline_period)을 검사한다. 기준월은 비교월의 12개월 전이다(§11.4)."""
    if not isinstance(inp, dict):
        raise TypeError("입력은 JSON 객체다")
    target = {}
    for key, pattern in (("hs6", _HS6_RE), ("partner", _PARTNER_RE), ("period", _MONTH_RE),
                         ("baseline_period", _MONTH_RE)):
        value = inp.get(key)
        if not isinstance(value, str) or not pattern.fullmatch(value):
            raise ValueError(f"{key} 형식이 계약과 다르다: {value!r}")
        target[key] = value
    period = target["period"]
    if target["baseline_period"] != f"{int(period[:4]) - 1:04d}{period[4:]}":
        raise ValueError("baseline_period는 period의 12개월 전(전년 같은 달)이어야 한다")
    return target


def parse_rows(rows: object, *, role: str, months: tuple[str, ...], partner: str) -> dict[str, list[dict]]:
    """한 역할(부모·ALL·하위)의 관측 행 목록을 검사해 달별로 묶는다.

    행은 관측 객체의 키(month, amount_usd, net_weight_kg, observation_status, 있으면 hs_code·hs_level·
    partner_code·flow)와 evidence_ids(근거 ID 목록)를 가진다. 주어진 달 밖의 행, 수입이 아닌 흐름, 다른 상대국 행은
    입력 오류다. 달마다 행이 하나 이상 있어야 한다. 한 달의 행은 모두 값 행(OBSERVED)이거나 모두 상태 행이다.
    CONFIRMED_NO_TRADE 행은 그 달의 유일한 행이어야 하고 V·Q를 0으로 본다(§3.4). 누락 상태 행은 V·Q가 null이다.
    """
    if not isinstance(rows, list):
        raise TypeError(f"{role}: 관측 행 목록이 없다")
    by_month: dict[str, list[dict]] = {month: [] for month in months}
    for raw in rows:
        row = _parse_row(raw, role=role, partner=partner)
        if row["month"] not in by_month:
            raise ValueError(f"{role}: period·baseline_period 밖의 달이다: {row['month']}")
        by_month[row["month"]].append(row)
    for month, found in by_month.items():
        if not found:
            raise ValueError(f"{role}: {month}의 행(값 행이나 상태 행)이 없다")
        statuses = {r["observation_status"] for r in found}
        if OBSERVED in statuses and statuses != {OBSERVED}:
            raise ValueError(f"{role}: {month}에 값 행과 상태 행이 섞였다(행 규칙은 자료 접근층이 적용한다)")
        if CONFIRMED_NO_TRADE in statuses and len(found) != 1:
            raise ValueError(f"{role}: {month}의 CONFIRMED_NO_TRADE 행은 그 달의 유일한 행이어야 한다")
    return by_month


def is_value_rows(rows: list[dict]) -> bool:
    """그 달의 행이 값 행(OBSERVED)인가. 아니면 상태 행이다."""
    return rows[0]["observation_status"] == OBSERVED


def status_flags(rows: list[dict]) -> list[str]:
    """OBSERVED가 아닌 행의 관측 상태 코드(사유로 그대로 쓴다)."""
    return sorted({r["observation_status"] for r in rows if r["observation_status"] != OBSERVED})


def evidence_of(rows: list[dict]) -> list[str]:
    """행들의 근거 ID를 순서대로 모은다."""
    return [ev for r in rows for ev in r["evidence_ids"]]


def require_count(value: object, name: str) -> None:
    """0 이상의 정수(bool 제외)인지 본다."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name}는 0 이상의 정수다: {value!r}")


def run(inp: object) -> object:
    """진입 함수. values는 표시 값으로, weight_checks는 중량 허용오차 판정으로 바꾼다."""
    if not isinstance(inp, dict) or set(inp) - {"values", "weight_checks"}:
        raise ValueError("입력은 values·weight_checks 키만 가진 JSON 객체다")
    values, checks = inp.get("values", []), inp.get("weight_checks", [])
    if not isinstance(values, list) or not isinstance(checks, list):
        raise TypeError("values·weight_checks는 목록이다")
    shown = []
    for item in values:
        if not isinstance(item, dict) or set(item) != {"metric", "value"}:
            raise ValueError("values의 원소는 metric·value 키를 가진다")
        unit, _ = unit_and_places(item["metric"])
        shown.append({"metric": item["metric"], "unit": unit, "value": display(item["metric"], item["value"])})
    judged = []
    for item in checks:
        if not isinstance(item, dict) or set(item) != {"Q_parent", "Q_hs10", "row_count", "weight_rounding_kg"}:
            raise ValueError("weight_checks의 원소는 Q_parent·Q_hs10·row_count·weight_rounding_kg 키를 가진다")
        within = weight_within_tolerance(item["Q_parent"], item["Q_hs10"], item["row_count"],
                                         item["weight_rounding_kg"])
        judged.append({"difference": abs(item["Q_parent"] - item["Q_hs10"]),
                       "tolerance": weight_tolerance(item["row_count"], item["weight_rounding_kg"]),
                       "within_tolerance": within})
    return {"values": shown, "weight_checks": judged}


def _parse_row(raw: object, *, role: str, partner: str) -> dict:
    if not isinstance(raw, dict):
        raise TypeError(f"{role}: 관측 행은 JSON 객체다")
    month = raw.get("month")
    if not isinstance(month, str) or not _MONTH_RE.fullmatch(month):
        raise ValueError(f"{role}: 월 키는 YYYYMM이다(총계 행 RAW:총계는 월 지표에 쓰지 않는다): {month!r}")
    if raw.get("flow", "import") != "import":
        raise ValueError(f"{role}: 지표는 수입(import) 행만 쓴다")
    if raw.get("partner_code", partner) != partner:
        raise ValueError(f"{role}: 상대국 코드가 {partner}가 아니다: {raw.get('partner_code')!r}")
    status = raw.get("observation_status")
    if status not in OBSERVATION_STATUSES:
        raise ValueError(f"{role}: 계약에 없는 관측 상태다: {status!r}")
    hs_code = raw.get("hs_code")
    if hs_code is not None and (not isinstance(hs_code, str) or not hs_code.isascii() or not hs_code.isdigit()):
        raise ValueError(f"{role}: hs_code는 숫자 문자열이다: {hs_code!r}")
    if "hs_level" in raw and (hs_code is None or raw["hs_level"] != len(hs_code)):
        raise ValueError(f"{role}: hs_level이 hs_code 자릿수와 다르다")
    amount, weight = raw.get("amount_usd"), raw.get("net_weight_kg")
    for name, value in (("amount_usd", amount), ("net_weight_kg", weight)):
        if value is not None:
            require_count(value, name)
    if status == CONFIRMED_NO_TRADE:
        if amount not in (None, 0) or weight not in (None, 0):
            raise ValueError(f"{role}: CONFIRMED_NO_TRADE 행의 금액·중량 칸은 null이다(§3.4)")
        amount, weight = 0, 0
    elif status in MISSING_STATUSES and (amount is not None or weight is not None):
        raise ValueError(f"{role}: {status} 행의 금액·중량은 null이다(빈 응답을 0으로 채우지 않는다)")
    evidence = raw.get("evidence_ids")
    if not isinstance(evidence, list) or not all(isinstance(ev, str) for ev in evidence):
        raise TypeError(f"{role}: evidence_ids는 문자열 목록이다")
    return {"month": month, "hs_code": hs_code, "observation_status": status, "V": amount, "Q": weight,
            "evidence_ids": list(evidence)}


def _json_default(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"직렬화할 수 없는 값: {type(value).__name__}")
