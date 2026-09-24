"""단위 X1 단가·변화율.

단위 ID: X1
도메인명: metrics_unit_value
소유: D
입력: 부모 HS6 행의 V·Q(t, t−12)
출력: `U`(t−12, t), `r_U`
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics

공식은 자료 계약 docs/rules/DATA_CONTRACT_V1.md §11.2다. U_t = V_t / Q_t(USD/kg), r_U = U_t / U_(t−12) − 1을
백분율(%)로 적는다. 원천 규칙대로 V·Q는 부모 HS6 행(HS4 스캔 요청이 준 상대국별 HS6 행)의 값이다. 정확한 분수로
계산하고 §11.3 자릿수로 한 번 반올림한다(단위 X4).

null 규칙(§11.1, §3.4, 룰북 B3-1)
- 중량이 0이면 U를 계산하지 않는다(zero_weight). 수입 0이 명시된 달(OBSERVED, 0)도 같다.
- CONFIRMED_NO_TRADE 달은 V·Q를 0으로 본다. 그래서 U는 null이다(사유 CONFIRMED_NO_TRADE, zero_weight).
- 누락 상태(UNRESOLVED_ZERO·REQUEST_FAILED·NOT_COLLECTED)는 0으로 채우지 않는다. U는 null이고 사유는 그 코드다.
- 기준월 U가 0이거나 null이면 r_U는 null이다(0이면 zero_baseline, null이면 기준월 U의 사유를 옮긴다).

run 입력(JSON 객체)
- hs6, partner(관세청 2자리 국가코드), period(비교월 t, YYYYMM), baseline_period(t−12)
- parent: 부모 역할의 관측 행 목록. 달(t−12, t)마다 부모 HS6 행 하나(OBSERVED나 CONFIRMED_NO_TRADE), 또는 부모
  행이 없을 때 그 달을 맡은 요청들의 누락 상태 행. 행은 month·amount_usd·net_weight_kg·observation_status·
  evidence_ids를 가진다. hs_code가 있으면 값 행은 그 HS6, 상태 행은 그 HS6나 그 HS4다. 같은 키의 HS10 하위 자료
  상태 행(행 규칙 4)은 여기에 넣지 않는다(단위 X3의 children에 넣는다).
run 출력
- {"metrics": [U(t−12), U(t), r_U]}. 원소는 자료 계약 §2.3.4 metric 객체다. inputs에는 V·Q(U), V_0·Q_0·V_1·Q_1
  (r_U, 0은 t−12, 1은 t)를 적는다.

반올림 전 값: metric 객체의 value는 §11.3 자릿수로 반올림한 값이다. 임계값 비교처럼 반올림 전 값이 필요하면
exact_value(metric)가 inputs의 정수로 정확한 분수를 다시 계산한다(단위 X3의 U@·r_U@도 같은 입력 키라 받는다).
"""
from fractions import Fraction

from tradesentry.metrics import rounding as x4

SCHEMA_VERSION = x4.SCHEMA_VERSION


def unit_value(amount: int | None, weight: int | None) -> Fraction | None:
    """U = V / Q(정확한 분수). 값이 없거나 중량이 0이면 None이다."""
    if amount is None or weight is None or weight == 0:
        return None
    return Fraction(amount, weight)


def change_rate(current: Fraction | None, baseline: Fraction | None) -> Fraction | None:
    """변화율(%) = (현재 / 기준 − 1) × 100. 기준이 0이거나 어느 쪽이든 없으면 None이다."""
    if current is None or baseline is None or baseline == 0:
        return None
    return (current / baseline - 1) * 100


def parse_parent(rows: object, target: dict[str, str]) -> dict[str, list[dict]]:
    """부모 역할 행을 검사해 달별로 묶는다. 값 행은 달마다 하나다."""
    hs6 = target["hs6"]
    grouped = x4.parse_rows(rows, role="parent", months=(target["baseline_period"], target["period"]),
                            partner=target["partner"])
    for month, found in grouped.items():
        value_row = found[0]["observation_status"] in (x4.OBSERVED, x4.CONFIRMED_NO_TRADE)
        if value_row and len(found) != 1:
            raise ValueError(f"parent: {month}의 부모 HS6 행이 둘 이상이다(행 규칙은 자료 접근층이 적용한다)")
        allowed = (None, hs6) if value_row else (None, hs6, hs6[:4])
        for row in found:
            if row["hs_code"] not in allowed:
                raise ValueError(f"parent: {month} 행의 hs_code가 부모 HS6 {hs6}와 맞지 않는다: {row['hs_code']!r}")
    return grouped


def unit_value_of(rows: list[dict]) -> tuple[Fraction | None, list[str]]:
    """한 달 부모 역할 행의 U와 사유."""
    flags = x4.status_flags(rows)
    if rows[0]["observation_status"] in x4.MISSING_STATUSES:
        return None, flags
    amount, weight = rows[0]["V"], rows[0]["Q"]
    if amount is None or weight is None:
        return None, flags + [x4.VALUE_MISSING]
    if weight == 0:
        return None, flags + [x4.ZERO_WEIGHT]
    return Fraction(amount, weight), flags


def change_of(current: tuple[Fraction | None, list[str]],
              baseline: tuple[Fraction | None, list[str]]) -> tuple[Fraction | None, list[str]]:
    """두 달의 (U, 사유)로 변화율과 사유를 낸다. 값이 없으면 두 달의 사유를 합친다."""
    rate = change_rate(current[0], baseline[0])
    if rate is not None:
        return rate, []
    flags = current[1] + baseline[1]
    if baseline[0] == 0:
        flags.append(x4.ZERO_BASELINE)
    return None, flags


def exact_value(metric: dict) -> Fraction | None:
    """U·r_U(과 U@·r_U@) metric 객체의 반올림 전 정확한 값. value가 null이면 None이다.

    inputs의 정수(V·Q, V_0·Q_0·V_1·Q_1)로 다시 계산한다. 그 값을 반올림한 결과가 value와 다르면 입력과 값이
    어긋난 객체라 ValueError로 멈춘다.
    """
    inputs = metric["inputs"]
    symbol = inputs["metric"]
    base = symbol.partition("@")[0]
    if base == "U":
        exact = unit_value(inputs["V"], inputs["Q"])
    elif base == "r_U":
        exact = change_rate(unit_value(inputs["V_1"], inputs["Q_1"]), unit_value(inputs["V_0"], inputs["Q_0"]))
    else:
        raise ValueError(f"단위 X1이 다시 계산하는 기호가 아니다: {symbol!r}")
    return x4.checked_exact(metric, exact)


def values_of(rows: list[dict]) -> tuple[int | None, int | None]:
    """한 달 부모 역할 행의 (V, Q). 누락 상태면 (None, None), 승격 행이면 (0, 0)이다."""
    if rows[0]["observation_status"] in x4.MISSING_STATUSES:
        return None, None
    return rows[0]["V"], rows[0]["Q"]


def run(inp: object) -> object:
    """진입 함수. 부모 HS6 행 두 달로 U(t−12)·U(t)·r_U metric 객체를 낸다."""
    target = x4.parse_target(inp)
    if set(inp) - {"hs6", "partner", "period", "baseline_period", "parent"}:
        raise ValueError("X1 입력 키는 hs6·partner·period·baseline_period·parent다")
    parent = parse_parent(inp.get("parent"), target)
    base, period = target["baseline_period"], target["period"]
    common = {"hs6": target["hs6"], "partner": target["partner"]}
    v0, q0 = values_of(parent[base])
    v1, q1 = values_of(parent[period])
    u0, u1 = unit_value_of(parent[base]), unit_value_of(parent[period])
    rate = change_of(u1, u0)
    ev0, ev1 = x4.evidence_of(parent[base]), x4.evidence_of(parent[period])
    return {"metrics": [
        x4.metric("U", **common, period=base, baseline_period=None, values={"V": v0, "Q": q0}, evidence_ids=ev0,
                  value=u0[0], flags=u0[1]),
        x4.metric("U", **common, period=period, baseline_period=None, values={"V": v1, "Q": q1}, evidence_ids=ev1,
                  value=u1[0], flags=u1[1]),
        x4.metric("r_U", **common, period=period, baseline_period=base,
                  values={"V_0": v0, "Q_0": q0, "V_1": v1, "Q_1": q1}, evidence_ids=ev0 + ev1, value=rate[0],
                  flags=rate[1]),
    ]}
