"""단위 X3 구성효과 분해.

단위 ID: X3
도메인명: metrics_decompose
소유: D
입력: HS10 두 시점
출력: `within_effect`·`mix_effect`·`residual`, 부모 대조
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics

공식은 자료 계약 docs/rules/DATA_CONTRACT_V1.md §11.2다(모두 USD/kg).
- u_i,t = V_i,t / Q_i,t, w_i,t = Q_i,t / Σ_i Q_i,t(금액 비중이 아닌 중량 비중)
- within_effect = Σ_i ((w_i,0 + w_i,1)/2) * (u_i,1 − u_i,0)
- mix_effect = Σ_i ((u_i,0 + u_i,1)/2) * (w_i,1 − w_i,0)
- residual = ΔU − (within_effect + mix_effect), ΔU = U_t − U_(t−12)(부모 HS6 행 단가의 차, 원천 규칙)
모두 정확한 분수로 계산하고 §11.3 자릿수로 한 번 반올림한다(중간 비중이 1/3 같은 무한소수여도 틀어지지 않는다).
머리 주석의 입력·출력 줄은 단위 표 docs/plan/UNITS.md §3.3의 문구다. 이 단위는 그 밖에 자료 계약 §2.3.4가 도구
decompose_hs에 요구하는 HS10 하위 지표(U@·r_U@·w@)도 낸다. 구체적인 모양은 아래와 결정 기록
docs/tracking/decisions/의 DT2 기록(data-decision-dt2-metrics)에 있다.

분해 조건(§11.2, 개발 플랜 §6.1, 룰북 B3-1 "계산할 수 없는 대상"): 같은 HS10 집합, 양 시점 중량 유효(하위 HS10 행과
부모 HS6 행의 Q > 0), 양 시점 부모 대조 통과(금액 정확 일치, 중량은 |부모 Q − HS10 Q 합| ≤ 행당 반올림 kg ×
(HS10 행수 + 1)). 하나라도 어긋나면 세 값 모두 null이고 사유를 남긴다.
- 사유: 부모·하위 자료의 관측 상태 코드(REQUEST_FAILED 등, oracle C), hs10_set_changed(신설·소멸 HS10),
  zero_weight(하위나 부모의 중량 0), value_missing, parent_mismatch.
- 신설·소멸 HS10은 0으로 채우지 않는다. 그 달의 U@·w@는 null(hs10_absent)로 존재를 드러낸다.
- 개별 하위변화와 상쇄는 HS10 하위 지표로 돌려준다: 코드마다 U@(t−12), U@(t), r_U@, w@(t−12), w@(t).
  계약에 없는 within_effect@ 같은 조합은 쓰지 않는다(§6.2).
- 행당 반올림 kg(출발값 0.5)는 정책 수치라 입력 weight_rounding_kg로 받는다(정책 수치 읽기 단위 K4의
  tolerance.weight_rounding_kg).

run 입력(JSON 객체)
- snapshot_id, hs6, partner, period, baseline_period, parent: 단위 X1과 같다(snapshot_id 필수).
- children: 상대국 HS10 하위 역할의 관측 행. 달마다 그 HS6 아래 HS10 행(OBSERVED, 코드는 달마다 한 번), 또는
  하위 자료가 없을 때 그 달의 상태 행(HS6 요청이 남긴 행, 행 규칙 4).
- weight_rounding_kg: 행당 반올림 kg(int나 Decimal).
run 출력
- metrics: [within_effect, mix_effect, residual, 코드 순으로 (U@(t−12), U@(t), r_U@, w@(t−12), w@(t))...].
  원소는 자료 계약 §2.3.4 metric 객체다.
  - 분해 세 값의 inputs: 부모 HS6 행의 V_0·Q_0·V_1·Q_1(0은 t−12, 1은 t. 부모 대조와 ΔU에 쓴다)과
    hs10_values {HS10 코드: {V_0, Q_0, V_1, Q_1}}(분해식에 쓴 하위 행. 그 달에 행이 없거나 하위 자료가 상태
    행이면 null). evidence_ids는 두 달의 부모 행과 하위 행(또는 상태 행)이다.
  - 분해 세 값의 tolerance: 두 달 HS10 집합이 같을 때 중량 대조 허용오차(kg, Decimal). 아니면 null.
- parent_check: 달(t−12, t)마다 한 항목, 부모 대조의 뜻과 null 규칙은 아래와 같다.
  - period: 달(YYYYMM). row_count: 그 달 하위 HS10 값 행 수.
  - V_parent·Q_parent: 부모 HS6 행의 V·Q(승격 행은 0). V_hs10·Q_hs10: 하위 HS10 행 V·Q의 합.
  - tolerance: 행당 반올림 kg × (row_count + 1)(kg, Decimal).
  - V_match: V_parent = V_hs10(정확 일치). Q_match: |Q_parent − Q_hs10| ≤ tolerance.
  - null 규칙: 하위가 상태 행이면 period 말고 모두 null이다. 하위가 값 행이어도 부모가 누락 상태이거나 부모·하위의
    V·Q 가운데 하나라도 비었으면 period·row_count만 값이 있고 나머지는 null이다. null은 "대조하지 못함"이지
    "일치"가 아니다.

반올림 전 값: metric 객체의 value는 §11.3 자릿수로 반올림한 값이다. exact_value(metric)가 inputs의 정수로
정확한 분수를 다시 계산한다(분해 세 값과 w@. U@·r_U@는 단위 X1의 exact_value로 넘긴다). 분해 값이 null이면
None을 돌려준다(null 사유 가운데 관측 상태와 부모 대조는 inputs만으로 다시 판정하지 않는다).
"""
from decimal import Decimal
from fractions import Fraction

from tradesentry.metrics import rounding as x4
from tradesentry.metrics import unit_value as x1

SCHEMA_VERSION = x4.SCHEMA_VERSION
EFFECTS = ("within_effect", "mix_effect", "residual")
SIDES = ("V_0", "Q_0", "V_1", "Q_1")


def parse_children(rows: object, target: dict[str, str]) -> dict[str, list[dict]]:
    """하위 역할 행을 검사해 달별로 묶는다. 값 행은 그 HS6 아래 HS10 행이고 달마다 코드가 한 번씩이다."""
    hs6 = target["hs6"]
    grouped = x4.parse_rows(rows, role="children", months=(target["baseline_period"], target["period"]),
                            partner=target["partner"])
    for month, found in grouped.items():
        if x4.is_value_rows(found):
            codes = [r["hs_code"] for r in found]
            for code in codes:
                if not x4.is_hs10_code(code) or not code.startswith(hs6):
                    raise ValueError(f"children: {month}의 값 행은 {hs6} 아래 HS10 행이어야 한다: {code!r}")
            if len(set(codes)) != len(codes):
                raise ValueError(f"children: {month}에 같은 HS10 행이 두 번 있다")
            found.sort(key=lambda r: r["hs_code"])
        else:
            for row in found:
                if row["hs_code"] not in (None, hs6):
                    raise ValueError(f"children: {month} 상태 행의 hs_code가 {hs6}가 아니다: {row['hs_code']!r}")
    return grouped


def parent_check(month: str, parent_rows: list[dict], child_rows: list[dict],
                 weight_rounding_kg: int | Decimal) -> dict[str, object]:
    """한 달의 부모 대조(뜻과 null 규칙은 모듈 머리말): 금액은 정확히 같고, 중량 차는 허용오차 안인가."""
    check: dict[str, object] = {"period": month, "row_count": None, "V_parent": None, "V_hs10": None,
                                "Q_parent": None, "Q_hs10": None, "tolerance": None, "V_match": None,
                                "Q_match": None}
    if not x4.is_value_rows(child_rows):
        return check
    check["row_count"] = len(child_rows)
    v_parent, q_parent = x1.values_of(parent_rows)
    values = [v_parent, q_parent] + [r["V"] for r in child_rows] + [r["Q"] for r in child_rows]
    if any(v is None for v in values):
        return check
    v_hs10, q_hs10 = sum(r["V"] for r in child_rows), sum(r["Q"] for r in child_rows)
    check.update({"V_parent": v_parent, "V_hs10": v_hs10, "Q_parent": q_parent, "Q_hs10": q_hs10,
                  "tolerance": x4.weight_tolerance(len(child_rows), weight_rounding_kg),
                  "V_match": v_parent == v_hs10,
                  "Q_match": x4.weight_within_tolerance(q_parent, q_hs10, len(child_rows), weight_rounding_kg)})
    return check


def hs10_values_of(children: dict[str, list[dict]], months: tuple[str, str], codes: list[str]) -> dict[str, dict]:
    """분해식에 쓰는 하위 행 값 {코드: {V_0, Q_0, V_1, Q_1}}. 그 달에 행이 없거나 상태 행이면 null이다."""
    table: dict[str, dict] = {code: dict.fromkeys(SIDES) for code in codes}
    for month, (v_key, q_key) in zip(months, (("V_0", "Q_0"), ("V_1", "Q_1"))):
        if not x4.is_value_rows(children[month]):
            continue
        for row in children[month]:
            table[row["hs_code"]][v_key], table[row["hs_code"]][q_key] = row["V"], row["Q"]
    return table


def effects_of(parent_values: tuple[int | None, int | None, int | None, int | None],
               hs10_values: dict[str, dict]) -> tuple[Fraction, Fraction, Fraction] | None:
    """분해식 세 값(within_effect, mix_effect, residual)의 정확한 분수.

    parent_values는 부모 (V_0, Q_0, V_1, Q_1), hs10_values는 {코드: {V_0, Q_0, V_1, Q_1}}이다. 값이 하나라도 비었거나,
    중량(하위·부모)이 0이거나, 하위 코드가 없으면 None이다. 관측 상태와 부모 대조 조건은 run이 따로 본다.
    """
    v_p0, q_p0, v_p1, q_p1 = parent_values
    rows = list(hs10_values.values())
    if not rows or None in parent_values or q_p0 == 0 or q_p1 == 0:
        return None
    if any(row[key] is None for row in rows for key in SIDES) or any(row["Q_0"] == 0 or row["Q_1"] == 0
                                                                       for row in rows):
        return None
    q_old, q_new = sum(row["Q_0"] for row in rows), sum(row["Q_1"] for row in rows)
    within = mix = Fraction(0)
    for row in rows:
        u0, u1 = Fraction(row["V_0"], row["Q_0"]), Fraction(row["V_1"], row["Q_1"])
        w0, w1 = Fraction(row["Q_0"], q_old), Fraction(row["Q_1"], q_new)
        within += (w0 + w1) / 2 * (u1 - u0)
        mix += (u0 + u1) / 2 * (w1 - w0)
    delta = Fraction(v_p1, q_p1) - Fraction(v_p0, q_p0)
    return within, mix, delta - (within + mix)


def decomposition_flags(parent: dict[str, list[dict]], children: dict[str, list[dict]], checks: list[dict],
                        months: tuple[str, str]) -> list[str]:
    """분해 조건에 걸린 사유. 빈 목록이면 분해한다."""
    base, period = months
    flags: list[str] = []
    for month in months:
        flags += x4.status_flags(parent[month]) + x4.status_flags(children[month])
        if parent[month][0]["observation_status"] == x4.OBSERVED:
            v_parent, q_parent = x1.values_of(parent[month])
            if v_parent is None or q_parent is None:
                flags.append(x4.VALUE_MISSING)
            elif q_parent == 0:
                flags.append(x4.ZERO_WEIGHT)  # 양 시점 중량 유효(룰북 B3-1)에 부모 중량도 든다
    if all(x4.is_value_rows(children[m]) for m in months):
        if {r["hs_code"] for r in children[base]} != {r["hs_code"] for r in children[period]}:
            flags.append(x4.HS10_SET_CHANGED)
        for row in children[base] + children[period]:
            if row["V"] is None or row["Q"] is None:
                flags.append(x4.VALUE_MISSING)
            elif row["Q"] == 0:
                flags.append(x4.ZERO_WEIGHT)
    if any(c["V_match"] is False or c["Q_match"] is False for c in checks):
        flags.append(x4.PARENT_MISMATCH)
    return flags


def weight_share_value(q_child: int | None, q_total: int | None) -> Fraction | None:
    """w@(중량 비중, %) = Q_i / Σ Q × 100. 값이 없거나 합이 0이면 None이다."""
    if q_child is None or q_total is None or q_total == 0:
        return None
    return Fraction(q_child, q_total) * 100


def exact_value(metric: dict) -> Fraction | None:
    """X3 metric 객체의 반올림 전 정확한 값(분수).

    분해 세 값은 inputs의 부모 V·Q와 hs10_values로, w@는 Q·Q_total로 다시 계산한다. U@·r_U@는 단위 X1의
    exact_value로 넘긴다. 분해 값의 value가 null이면 None이다. 다시 계산한 값을 반올림한 결과가 value와 다르면
    입력과 값이 어긋난 객체라 ValueError로 멈춘다.
    """
    inputs = metric["inputs"]
    symbol = inputs["metric"]
    base, at, _ = symbol.partition("@")
    if symbol in EFFECTS:
        if metric["value"] is None:
            return x4.checked_exact(metric, None)
        effects = effects_of(tuple(inputs[key] for key in SIDES), inputs["hs10_values"])
        return x4.checked_exact(metric, None if effects is None else effects[EFFECTS.index(symbol)])
    if at and base == "w":
        return x4.checked_exact(metric, weight_share_value(inputs["Q"], inputs["Q_total"]))
    if at and base in ("U", "r_U"):
        return x1.exact_value(metric)
    raise ValueError(f"단위 X3이 다시 계산하는 기호가 아니다: {symbol!r}")


def child_rows_of(children: list[dict], code: str) -> tuple[list[dict], dict | None]:
    """한 달 하위 역할 행에서 그 코드의 행. 값 행이 아니면 (상태 행들, None)이다."""
    if not x4.is_value_rows(children):
        return children, None
    return [], next((r for r in children if r["hs_code"] == code), None)


def child_unit_value(children: list[dict], code: str) -> tuple[Fraction | None, list[str], list[str], dict]:
    """하위 품목 한 달의 U@: (값, 사유, 근거 ID, 입력값)."""
    status_rows, row = child_rows_of(children, code)
    if status_rows:
        return None, x4.status_flags(status_rows), x4.evidence_of(status_rows), {"V": None, "Q": None}
    if row is None:
        return None, [x4.HS10_ABSENT], [], {"V": None, "Q": None}
    value, flags = x1.unit_value_of([row])
    return value, flags, list(row["evidence_ids"]), {"V": row["V"], "Q": row["Q"]}


def child_weight_share(children: list[dict], code: str) -> tuple[Fraction | None, list[str], list[str], dict]:
    """하위 품목 한 달의 w@(중량 비중, %): (값, 사유, 근거 ID, 입력값)."""
    status_rows, row = child_rows_of(children, code)
    if status_rows:
        return None, x4.status_flags(status_rows), x4.evidence_of(status_rows), {"Q": None, "Q_total": None}
    if row is None:
        return None, [x4.HS10_ABSENT], [], {"Q": None, "Q_total": None}
    evidence = list(row["evidence_ids"]) + x4.evidence_of([r for r in children if r is not row])
    weights = [r["Q"] for r in children]
    if None in weights:
        return None, [x4.VALUE_MISSING], evidence, {"Q": row["Q"], "Q_total": None}
    total = sum(weights)
    if total == 0:
        return None, [x4.ZERO_WEIGHT], evidence, {"Q": row["Q"], "Q_total": total}
    return weight_share_value(row["Q"], total), [], evidence, {"Q": row["Q"], "Q_total": total}


def run(inp: object) -> object:
    """진입 함수. 두 시점의 부모·하위 행으로 분해 세 값, HS10 하위 지표, 부모 대조를 낸다."""
    target = x4.parse_target(inp)
    allowed = {"snapshot_id", "hs6", "partner", "period", "baseline_period", "parent", "children",
               "weight_rounding_kg"}
    if set(inp) - allowed:
        raise ValueError("X3 입력 키는 snapshot_id·hs6·partner·period·baseline_period·parent·children·"
                         "weight_rounding_kg다")
    snapshot_id = x4.parse_snapshot_id(inp)
    if "weight_rounding_kg" not in inp:
        raise ValueError("weight_rounding_kg(행당 반올림 kg, 정책 수치)가 없다")
    rounding_kg = inp["weight_rounding_kg"]
    x4.weight_tolerance(0, rounding_kg)  # 형식 검사(int·Decimal, 0 이상)

    def make(symbol: str, **fields: object) -> dict[str, object]:
        return x4.metric(symbol, hs6=target["hs6"], partner=target["partner"], snapshot_id=snapshot_id, **fields)

    parent = x1.parse_parent(inp.get("parent"), target)
    children = parse_children(inp.get("children"), target)
    months = (target["baseline_period"], target["period"])
    base, period = months
    checks = [parent_check(m, parent[m], children[m], rounding_kg) for m in months]
    codes = sorted({r["hs_code"] for m in months if x4.is_value_rows(children[m]) for r in children[m]})
    hs10_values = hs10_values_of(children, months, codes)
    parent_values = x1.values_of(parent[base]) + x1.values_of(parent[period])
    flags = decomposition_flags(parent, children, checks, months)
    values: tuple = (None, None, None)
    if not flags:
        values = effects_of(parent_values, hs10_values)
    tolerance = None
    if all(x4.is_value_rows(children[m]) for m in months) \
            and {r["hs_code"] for r in children[base]} == {r["hs_code"] for r in children[period]}:
        tolerance = x4.weight_tolerance(len(children[base]), rounding_kg)
    evidence = [ev for m in months for ev in x4.evidence_of(parent[m])] \
        + [ev for m in months for ev in x4.evidence_of(children[m])]
    used = dict(zip(SIDES, parent_values)) | {"hs10_values": hs10_values}
    metrics = [make(symbol, period=period, baseline_period=base, values=used, evidence_ids=evidence, value=value,
                    flags=flags, tolerance=tolerance)
               for symbol, value in zip(EFFECTS, values)]
    for code in codes:
        unit_values = {m: child_unit_value(children[m], code) for m in months}
        for month in months:
            value, reason, ev, used_values = unit_values[month]
            metrics.append(make(f"U@{code}", period=month, baseline_period=None, values=used_values,
                                evidence_ids=ev, value=value, flags=reason))
        rate, reason = x1.change_of(unit_values[period][:2], unit_values[base][:2])
        metrics.append(make(f"r_U@{code}", period=period, baseline_period=base,
                            values={"V_0": unit_values[base][3]["V"], "Q_0": unit_values[base][3]["Q"],
                                    "V_1": unit_values[period][3]["V"], "Q_1": unit_values[period][3]["Q"]},
                            evidence_ids=unit_values[base][2] + unit_values[period][2], value=rate, flags=reason))
        for month in months:
            value, reason, ev, used_values = child_weight_share(children[month], code)
            metrics.append(make(f"w@{code}", period=month, baseline_period=None, values=used_values,
                                evidence_ids=ev, value=value, flags=reason))
    return {"metrics": metrics, "parent_check": checks}
