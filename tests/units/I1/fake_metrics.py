"""지표 단위 X1(unit_value)·X2(share)·X3(decompose)의 시험 대역(stub: 정해진 규칙으로 값을 돌려주는 가짜 함수).

이 작업 폴더의 지표 단위는 아직 뼈대라(데이터 트랙 DT2가 따로 만든다) 도구 시험은 run을 이 대역으로 바꿔 끼운다.
- 입출력 모양은 DT2 지표 단위가 보고한 모양을 따른다: 입력은 대상(hs6·partner·period·baseline_period)과 역할별 관측
  행(parent·world·children), X3는 weight_rounding_kg. 출력은 {"metrics": [metric 객체…]}(X3는 parent_check를 더한다).
  metric 객체는 자료 계약 §2.3.4의 키 8개이고 inputs에 지표 기호 "metric"과 대상 네 키를 둔다.
- 값은 정확한 분수로 계산해 표시 자릿수로 사사오입한다(대역 안의 단순 계산이다. 정본 계산은 지표 단위다).
- metric_id는 "fake-"로 시작하고 formula_version은 "fake-1"이라 진짜 지표와 섞이지 않는다. 같은 입력이면 같은 객체다.
- calls에 받은 입력을 모은다(도구가 지표 단위에 넘긴 역할별 행을 시험이 확인한다).
"""
import hashlib
import json
from decimal import Decimal
from fractions import Fraction
from unittest import mock

OBSERVED, CNT = "OBSERVED", "CONFIRMED_NO_TRADE"
PLACES = {"V": ("USD", 0), "U": ("USD/kg", 2), "r_U": ("%", 1), "s": ("%", 1), "d_s": ("pp", 1),
          "within_effect": ("USD/kg", 2), "mix_effect": ("USD/kg", 2), "residual": ("USD/kg", 2), "w": ("%", 1)}


def shown(symbol: str, value: Fraction | int | None):
    if value is None:
        return None
    places = PLACES[symbol.partition("@")[0]][1]
    scaled = Fraction(value) * 10 ** places
    whole, rest = divmod(abs(scaled.numerator), scaled.denominator)
    if 2 * rest >= scaled.denominator:
        whole += 1
    digits = -whole if scaled < 0 else whole
    return digits if places == 0 else Decimal(f"{digits}E-{places}")


def metric(symbol, inp, partner, period, baseline, values, evidence, value, flags=()):
    inputs = {"metric": symbol, "hs6": inp["hs6"], "partner": partner, "period": period, "baseline_period": baseline}
    inputs.update(values)
    flags = sorted(set(flags)) if value is None else sorted(set(flags) - {"fake_null"})
    if value is None and not flags:
        flags = ["fake_null"]
    body = {"formula_version": "fake-1", "inputs": inputs, "evidence_ids": list(dict.fromkeys(evidence)),
            "value": shown(symbol, value), "unit": PLACES[symbol.partition("@")[0]][0], "comparability_flags": flags,
            "tolerance": None}
    text = json.dumps(body, sort_keys=True, ensure_ascii=False, default=str)
    return {"metric_id": f"fake-{symbol}-{hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]}", **body}


def by_month(rows, months):
    out = {m: [r for r in rows if r["month"] == m] for m in months}
    for month, found in out.items():
        assert found, f"{month}의 행이 없다"
        statuses = {r["observation_status"] for r in found}
        assert not (OBSERVED in statuses and statuses != {OBSERVED}), "값 행과 상태 행이 섞였다"
        assert not (CNT in statuses and len(found) != 1), "무거래 확정 행은 그 달의 유일한 행이다"
    return out


def evidence(rows):
    return [e for r in rows for e in r["evidence_ids"]]


def amount_weight(rows):
    """(V, Q, 사유). 값 행이면 그 값, 무거래 확정이면 0, 빠졌으면 None과 상태."""
    status = rows[0]["observation_status"]
    if status == OBSERVED:
        return rows[0]["amount_usd"], rows[0]["net_weight_kg"], []
    if status == CNT:
        return 0, 0, [CNT]
    return None, None, sorted({r["observation_status"] for r in rows})


def unit_value(v, q, flags):
    if v is None or q is None:
        return None, flags
    if q == 0:
        return None, flags + ["zero_weight"]
    return Fraction(v, q), flags


def change(u1, u0):
    if u1[0] is None or u0[0] is None or u0[0] == 0:
        return None, u1[1] + u0[1] + (["zero_baseline"] if u0[0] == 0 else [])
    return (u1[0] / u0[0] - 1) * 100, []


class FakeMetrics:
    def __init__(self):
        self.calls = []

    def x1(self, inp):
        self.calls.append(("X1", inp))
        base, period = inp["baseline_period"], inp["period"]
        parent = by_month(inp["parent"], (base, period))
        v0, q0, f0 = amount_weight(parent[base])
        v1, q1, f1 = amount_weight(parent[period])
        u0, u1 = unit_value(v0, q0, f0), unit_value(v1, q1, f1)
        rate = change(u1, u0)
        p = inp["partner"]
        return {"metrics": [
            metric("U", inp, p, base, None, {"V": v0, "Q": q0}, evidence(parent[base]), *u0),
            metric("U", inp, p, period, None, {"V": v1, "Q": q1}, evidence(parent[period]), *u1),
            metric("r_U", inp, p, period, base, {"V_0": v0, "Q_0": q0, "V_1": v1, "Q_1": q1},
                   evidence(parent[base]) + evidence(parent[period]), *rate)]}

    def x2(self, inp):
        self.calls.append(("X2", inp))
        base, period = inp["baseline_period"], inp["period"]
        parent, world = by_month(inp["parent"], (base, period)), by_month(inp["world"], (base, period))
        p, out, country, total, shares = inp["partner"], [], {}, {}, {}
        for m in (base, period):
            v, _, flags = amount_weight(parent[m])
            country[m] = (v, flags)
            out.append(metric("V", inp, p, m, None, {}, evidence(parent[m]), v, flags))
        for m in (base, period):
            rows = world[m]
            if rows[0]["observation_status"] == OBSERVED:
                total[m] = (sum(r["amount_usd"] for r in rows), [], len(rows))
            else:
                v, _, flags = amount_weight(rows)
                total[m] = (v, flags, None)
            out.append(metric("V", inp, "ALL", m, None, {"row_count": total[m][2]}, evidence(rows), *total[m][:2]))
        for m in (base, period):
            c, w = country[m], total[m]
            value = None if c[0] is None or not w[0] else Fraction(c[0], w[0]) * 100
            flags = c[1] + w[1] + (["zero_denominator"] if w[0] == 0 and c[0] is not None else [])
            shares[m] = (value, flags)
            out.append(metric("s", inp, p, m, None, {"V_country": c[0], "V_world": w[0]},
                              evidence(parent[m]) + evidence(world[m]), value, flags))
        d = None if shares[base][0] is None or shares[period][0] is None else shares[period][0] - shares[base][0]
        out.append(metric("d_s", inp, p, period, base,
                          {"V_country_0": country[base][0], "V_world_0": total[base][0],
                           "V_country_1": country[period][0], "V_world_1": total[period][0]},
                          evidence(parent[base]) + evidence(world[base]) + evidence(parent[period])
                          + evidence(world[period]), d, shares[base][1] + shares[period][1]))
        return {"metrics": out}

    def x3(self, inp):
        self.calls.append(("X3", inp))
        base, period = inp["baseline_period"], inp["period"]
        months = (base, period)
        parent, kids = by_month(inp["parent"], months), by_month(inp["children"], months)
        delta = Fraction(inp["weight_rounding_kg"])
        checks, flags = [], []
        for m in months:
            flags += [r["observation_status"] for r in parent[m] + kids[m] if r["observation_status"] != OBSERVED]
            check = {"period": m, "row_count": None, "V_parent": None, "V_hs10": None, "Q_parent": None,
                     "Q_hs10": None, "tolerance": None, "V_match": None, "Q_match": None}
            v, q, _ = amount_weight(parent[m])
            if kids[m][0]["observation_status"] == OBSERVED and v is not None:
                n = len(kids[m])
                vk, qk = sum(r["amount_usd"] for r in kids[m]), sum(r["net_weight_kg"] for r in kids[m])
                tol = Decimal(inp["weight_rounding_kg"]) * (n + 1)
                check.update({"row_count": n, "V_parent": v, "V_hs10": vk, "Q_parent": q, "Q_hs10": qk,
                              "tolerance": tol, "V_match": v == vk, "Q_match": abs(q - qk) <= delta * (n + 1)})
                if not (check["V_match"] and check["Q_match"]):
                    flags.append("parent_mismatch")
            checks.append(check)
        values = {m: {r["hs_code"]: r for r in kids[m] if r["observation_status"] == OBSERVED} for m in months}
        codes = sorted(set(values[base]) | set(values[period]))
        if not flags and set(values[base]) != set(values[period]):
            flags.append("hs10_set_changed")
        if not flags and any(r["net_weight_kg"] == 0 for m in months for r in values[m].values()):
            flags.append("zero_weight")
        v0, q0, _ = amount_weight(parent[base])
        v1, q1, _ = amount_weight(parent[period])
        effects = [None, None, None]
        if not flags:
            qo, qn = sum(r["net_weight_kg"] for r in values[base].values()), \
                sum(r["net_weight_kg"] for r in values[period].values())
            within = mix = Fraction(0)
            for code in codes:
                o, n = values[base][code], values[period][code]
                u0, u1 = Fraction(o["amount_usd"], o["net_weight_kg"]), Fraction(n["amount_usd"], n["net_weight_kg"])
                w0, w1 = Fraction(o["net_weight_kg"], qo), Fraction(n["net_weight_kg"], qn)
                within += (w0 + w1) / 2 * (u1 - u0)
                mix += (u0 + u1) / 2 * (w1 - w0)
            effects = [within, mix, (Fraction(v1, q1) - Fraction(v0, q0)) - (within + mix)]
        p = inp["partner"]
        ev = evidence(parent[base]) + evidence(parent[period]) + evidence(kids[base]) + evidence(kids[period])
        out = [metric(symbol, inp, p, period, base, {"V_0": v0, "Q_0": q0, "V_1": v1, "Q_1": q1, "hs10": codes}, ev,
                      value, flags) for symbol, value in zip(("within_effect", "mix_effect", "residual"), effects)]
        for code in codes:
            units = {}
            for m in months:
                row = values[m].get(code)
                vq = (row["amount_usd"], row["net_weight_kg"]) if row else (None, None)
                units[m] = unit_value(*vq, [] if row else ["hs10_absent"])
                out.append(metric(f"U@{code}", inp, p, m, None, {"V": vq[0], "Q": vq[1]},
                                  row["evidence_ids"] if row else [], *units[m]))
            o, n = values[base].get(code), values[period].get(code)
            out.append(metric(f"r_U@{code}", inp, p, period, base,
                              {"V_0": o and o["amount_usd"], "Q_0": o and o["net_weight_kg"],
                               "V_1": n and n["amount_usd"], "Q_1": n and n["net_weight_kg"]},
                              (o["evidence_ids"] if o else []) + (n["evidence_ids"] if n else []),
                              *change(units[period], units[base])))
            for m in months:
                row, total = values[m].get(code), sum(r["net_weight_kg"] for r in values[m].values())
                share = Fraction(row["net_weight_kg"], total) * 100 if row and total else None
                out.append(metric(f"w@{code}", inp, p, m, None, {"Q": row and row["net_weight_kg"], "Q_total": total},
                                  evidence(list(values[m].values())), share, [] if row else ["hs10_absent"]))
        return {"metrics": out, "parent_check": checks}


def patch_metrics(test) -> FakeMetrics:
    """시험 setUp에서 부른다: 지표 단위 X1·X2·X3의 run을 대역으로 바꾸고 대역 객체를 돌려준다."""
    fake = FakeMetrics()
    for target, func in (("tradesentry.metrics.unit_value.run", fake.x1), ("tradesentry.metrics.share.run", fake.x2),
                         ("tradesentry.metrics.decompose.run", fake.x3)):
        patcher = mock.patch(target, side_effect=func)
        patcher.start()
        test.addCleanup(patcher.stop)
    return fake


def fix_clock(test, value: int = 0) -> None:
    """도구 공통 틀의 시계를 고정한다(elapsed_ms = 0)."""
    patcher = mock.patch("tradesentry.tools.check_comparability.clock_ms", return_value=value)
    patcher.start()
    test.addCleanup(patcher.stop)
