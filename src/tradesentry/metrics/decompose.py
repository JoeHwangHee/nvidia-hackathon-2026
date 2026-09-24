"""단위 X3 구성효과 분해.

단위 ID: X3
도메인명: metrics_decompose
소유: D
입력: HS10 두 시점(상대국 HS10 행 t−12·t, 부모 HS6 행, 행당 반올림 kg)
출력: `within_effect`·`mix_effect`·`residual`, HS10 하위 지표(`U@`·`r_U@`·`w@`), 부모 대조
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics

공식은 자료 계약 docs/rules/DATA_CONTRACT_V1.md §11.2다(모두 USD/kg).
- u_i,t = V_i,t / Q_i,t, w_i,t = Q_i,t / Σ_i Q_i,t(금액 비중이 아닌 중량 비중)
- within_effect = Σ_i ((w_i,0 + w_i,1)/2) * (u_i,1 − u_i,0)
- mix_effect = Σ_i ((u_i,0 + u_i,1)/2) * (w_i,1 − w_i,0)
- residual = ΔU − (within_effect + mix_effect), ΔU = U_t − U_(t−12)(부모 HS6 행 단가의 차, 원천 규칙)
모두 정확한 분수로 계산하고 §11.3 자릿수로 한 번 반올림한다(중간 비중이 1/3 같은 무한소수여도 틀어지지 않는다).

분해 조건(§11.2, 개발 플랜 §6.1): 같은 HS10 집합, 양 시점 중량 유효(Q > 0), 양 시점 부모 대조 통과(금액 정확 일치,
중량은 |부모 Q − HS10 Q 합| ≤ 행당 반올림 kg × (HS10 행수 + 1)). 하나라도 어긋나면 세 값 모두 null이고 사유를 남긴다.
- 사유: 부모·하위 자료의 관측 상태 코드(REQUEST_FAILED 등, oracle C), hs10_set_changed(신설·소멸 HS10),
  zero_weight, value_missing, parent_mismatch. 부모 단가를 계산할 수 없으면 residual만 null(zero_weight)이다.
- 신설·소멸 HS10은 0으로 채우지 않는다. 그 달의 U@·w@는 null(hs10_absent)로 존재를 드러낸다.
- 개별 하위변화와 상쇄는 HS10 하위 지표로 돌려준다: 코드마다 U@(t−12), U@(t), r_U@, w@(t−12), w@(t).
  계약에 없는 within_effect@ 같은 조합은 쓰지 않는다(§6.2).
- 행당 반올림 kg(출발값 0.5)는 정책 수치라 입력 weight_rounding_kg로 받는다(정책 수치 읽기 단위 K4가 주는 값).

run 입력(JSON 객체)
- hs6, partner, period, baseline_period, parent: 단위 X1과 같다.
- children: 상대국 HS10 하위 역할의 관측 행. 달마다 그 HS6 아래 HS10 행(OBSERVED, 코드는 달마다 한 번), 또는
  하위 자료가 없을 때 그 달의 상태 행(HS6 요청이 남긴 행, 행 규칙 4).
- weight_rounding_kg: 행당 반올림 kg(int나 Decimal).
run 출력
- metrics: [within_effect, mix_effect, residual, 코드 순으로 (U@(t−12), U@(t), r_U@, w@(t−12), w@(t))...].
  원소는 자료 계약 §2.3.4 metric 객체다. 분해 세 값의 inputs에는 부모 V_0·Q_0·V_1·Q_1과 HS10 코드 목록 hs10을,
  tolerance에는 중량 대조 허용오차(같은 HS10 집합일 때)를 적는다.
- parent_check: 달(t−12, t)마다 {period, row_count, V_parent, V_hs10, Q_parent, Q_hs10, tolerance, V_match,
  Q_match}. 부모 값 행과 하위 값 행이 모두 있을 때만 값이 있고, 아니면 null이다.
"""
from decimal import Decimal
from fractions import Fraction

from tradesentry.metrics import rounding as x4
from tradesentry.metrics import unit_value as x1

SCHEMA_VERSION = x4.SCHEMA_VERSION
EFFECTS = ("within_effect", "mix_effect", "residual")


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
    """한 달의 부모 대조: 금액은 정확히 같고, 중량 차는 허용오차 안인가."""
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


def decomposition(parent: dict[str, list[dict]], children: dict[str, list[dict]], checks: list[dict],
                  months: tuple[str, str]) -> tuple[list[Fraction | None], list[list[str]]]:
    """within_effect·mix_effect·residual 값과 각 사유. 분해 조건을 하나라도 못 채우면 세 값 모두 None이다."""
    base, period = months
    flags: list[str] = []
    for month in months:
        flags += x4.status_flags(parent[month]) + x4.status_flags(children[month])
        if parent[month][0]["observation_status"] == x4.OBSERVED and None in x1.values_of(parent[month]):
            flags.append(x4.VALUE_MISSING)
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
    if flags:
        return [None, None, None], [flags, flags, flags]
    old = {r["hs_code"]: r for r in children[base]}
    new = {r["hs_code"]: r for r in children[period]}
    q_old, q_new = sum(r["Q"] for r in old.values()), sum(r["Q"] for r in new.values())
    within = mix = Fraction(0)
    for code in old:
        u0, u1 = Fraction(old[code]["V"], old[code]["Q"]), Fraction(new[code]["V"], new[code]["Q"])
        w0, w1 = Fraction(old[code]["Q"], q_old), Fraction(new[code]["Q"], q_new)
        within += (w0 + w1) / 2 * (u1 - u0)
        mix += (u0 + u1) / 2 * (w1 - w0)
    u_base, u_period = x1.unit_value(*x1.values_of(parent[base])), x1.unit_value(*x1.values_of(parent[period]))
    if u_base is None or u_period is None:
        return [within, mix, None], [[], [], [x4.ZERO_WEIGHT]]
    return [within, mix, (u_period - u_base) - (within + mix)], [[], [], []]


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
    return Fraction(row["Q"], total) * 100, [], evidence, {"Q": row["Q"], "Q_total": total}


def run(inp: object) -> object:
    """진입 함수. 두 시점의 부모·하위 행으로 분해 세 값, HS10 하위 지표, 부모 대조를 낸다."""
    target = x4.parse_target(inp)
    if set(inp) - {"hs6", "partner", "period", "baseline_period", "parent", "children", "weight_rounding_kg"}:
        raise ValueError("X3 입력 키는 hs6·partner·period·baseline_period·parent·children·weight_rounding_kg다")
    if "weight_rounding_kg" not in inp:
        raise ValueError("weight_rounding_kg(행당 반올림 kg, 정책 수치)가 없다")
    rounding_kg = inp["weight_rounding_kg"]
    x4.weight_tolerance(0, rounding_kg)  # 형식 검사(int·Decimal, 0 이상)
    parent = x1.parse_parent(inp.get("parent"), target)
    children = parse_children(inp.get("children"), target)
    hs6, partner = target["hs6"], target["partner"]
    months = (target["baseline_period"], target["period"])
    base, period = months
    checks = [parent_check(m, parent[m], children[m], rounding_kg) for m in months]
    codes = sorted({r["hs_code"] for m in months if x4.is_value_rows(children[m]) for r in children[m]})
    values, flags = decomposition(parent, children, checks, months)
    v0, q0 = x1.values_of(parent[base])
    v1, q1 = x1.values_of(parent[period])
    tolerance = None
    if all(x4.is_value_rows(children[m]) for m in months) \
            and {r["hs_code"] for r in children[base]} == {r["hs_code"] for r in children[period]}:
        tolerance = x4.weight_tolerance(len(children[base]), rounding_kg)
    evidence = [ev for m in months for ev in x4.evidence_of(parent[m])] \
        + [ev for m in months for ev in x4.evidence_of(children[m])]
    metrics = [x4.metric(symbol, hs6=hs6, partner=partner, period=period, baseline_period=base,
                         values={"V_0": v0, "Q_0": q0, "V_1": v1, "Q_1": q1, "hs10": codes}, evidence_ids=evidence,
                         value=value, flags=reason, tolerance=tolerance)
               for symbol, value, reason in zip(EFFECTS, values, flags)]
    for code in codes:
        unit_values = {m: child_unit_value(children[m], code) for m in months}
        for month in months:
            value, reason, ev, used = unit_values[month]
            metrics.append(x4.metric(f"U@{code}", hs6=hs6, partner=partner, period=month, baseline_period=None,
                                     values=used, evidence_ids=ev, value=value, flags=reason))
        rate, reason = x1.change_of(unit_values[period][:2], unit_values[base][:2])
        metrics.append(x4.metric(f"r_U@{code}", hs6=hs6, partner=partner, period=period, baseline_period=base,
                                 values={"V_0": unit_values[base][3]["V"], "Q_0": unit_values[base][3]["Q"],
                                         "V_1": unit_values[period][3]["V"], "Q_1": unit_values[period][3]["Q"]},
                                 evidence_ids=unit_values[base][2] + unit_values[period][2], value=rate,
                                 flags=reason))
        for month in months:
            value, reason, ev, used = child_weight_share(children[month], code)
            metrics.append(x4.metric(f"w@{code}", hs6=hs6, partner=partner, period=month, baseline_period=None,
                                     values=used, evidence_ids=ev, value=value, flags=reason))
    return {"metrics": metrics, "parent_check": checks}
