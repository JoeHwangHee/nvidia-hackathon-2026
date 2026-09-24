"""누적 토큰 추정 시험용 합성 봉투(시험 폴더 안에만 두는 대역). 네트워크·스냅샷 없이 만든다.

모양은 도구 5개의 봉투(자료 계약 §5.2 키 11개, 지표는 계약 §2.3.4 키)와 MT2 도구가 합성 스냅샷에서 낸 봉투의 키를 따른다.
크기는 MT2 구현 보고가 실자료 850450-JP로 잰 글자 수(비교 가능성 약 2,500, 이력 약 7,800, 비교국 약 8,200, HS10 분해 약
18,500. JSON 한 줄 기준)에 가깝게 맞췄다 `[추론: 자기 보고 값에 맞춘 합성]`. 근거 ID는 실자료 스냅샷 이름 꼴을 쓴다.
"""
import hashlib
from decimal import Decimal

SNAP = "kcs_202201_202412_v2"
HS6 = "850450"
PARTNER = "JP"
MONTH, BASE = "202401", "202301"
PEERS = ("CN", "US", "DE", "TW", "VN")
MONTHS = tuple(f"2023{m:02d}" for m in range(1, 13)) + (MONTH,)


def ev(n: int) -> str:
    return f"ev:{SNAP}:observation:{n}"


def metric(symbol: str, partner: str, period: str, baseline: str | None, value: str | None, unit: str,
           evidence: list, raw: dict, flags: tuple = ()) -> dict:
    digest = hashlib.sha256(f"{symbol}|{partner}|{period}|{baseline}".encode()).hexdigest()[:16]
    return {"metric_id": f"{symbol}-{digest}", "formula_version": "1",
            "inputs": {"metric": symbol, "hs6": HS6, "partner": partner, "period": period, "baseline_period": baseline,
                       **raw},
            "evidence_ids": list(evidence), "value": None if value is None else Decimal(value), "unit": unit,
            "comparability_flags": list(flags), "tolerance": Decimal("1.5") if symbol in (
                "within_effect", "mix_effect", "residual") else None}


def _ids(value: object) -> set:
    if isinstance(value, str):
        return {value} if value.startswith("ev:") else set()
    if isinstance(value, dict):
        return set().union(*(_ids(v) for v in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(_ids(v) for v in value)) if value else set()
    return set()


def envelope(tool: str, n: int, scope: dict, metrics: list, comparability: dict, missingness: list,
             extra_evidence: list) -> dict:
    """봉투 수준 evidence_ids는 도구가 본 행 전부다(지표·비교 가능성·빠진 자료의 근거와 따로 본 행)."""
    evidence = sorted(_ids(metrics) | _ids(comparability) | _ids(missingness) | set(extra_evidence))
    return {"query_id": f"{tool}-{n:016x}", "tool": tool,
            "scope": {"hs6": HS6, "partner": PARTNER, "month": MONTH, "baseline_month": BASE, **scope},
            "snapshot_id": SNAP, "source_kind": "snapshot", "evidence_ids": evidence, "metrics": metrics,
            "comparability": comparability, "missingness": missingness, "retryable_error": None, "elapsed_ms": 12}


def missing(n: int, partner: str, code: str, month: str, status: str = "NOT_COLLECTED") -> dict:
    return {"evidence_id": ev(n), "request_id": f"{n:016x}", "partner_code": partner, "hs_code": code, "month": month,
            "flow": "import", "observation_status": status}


def children(count: int) -> list:
    return [f"{HS6}{1000 + 1000 * i:04d}"[:10] for i in range(count)]


def check_comparability(hs10_count: int = 8) -> dict:
    codes = children(hs10_count)
    months = [{"month": m, "observation_status": "OBSERVED", "hs10_rows": hs10_count} for m in (BASE, MONTH)]
    comparability = {
        "comparable": True, "period": {"month": MONTH, "baseline_month": BASE, "yoy": True},
        "units": {"amount": "USD", "weight": "kg"}, "units_ok": True, "hs_version": "HSK",
        "parent": [{"month": m, "observation_status": "OBSERVED", "weight_zero": False} for m in (BASE, MONTH)],
        "denominator": {"partner": "ALL", "months": months}, "children": {"months": months, "same_hs10_set": True},
        "signals": {"unit_value": {"evaluable": True, "issues": []}, "share": {"evaluable": True, "issues": []}},
        "rounding": {"weight_rounding_kg": Decimal("0.5"), "threshold": 30, "r_U_low": Decimal("-40.1"),
                     "r_U_high": Decimal("-39.9"), "direction_stable": True, "threshold_stable": True,
                     "unstable": False}}
    return envelope("check_comparability", 1, {"months": [BASE, MONTH], "partners": [PARTNER, "ALL"], "hs10": codes},
                    [], comparability, [], [ev(100 + i) for i in range(4 * hs10_count + 6)])


def get_history() -> dict:
    metrics = []
    for i, month in enumerate((BASE, MONTH)):
        raw = {"V": 600000 - 240000 * i, "Q": 100000}
        metrics.append(metric("V", PARTNER, month, None, str(raw["V"]), "USD", [ev(200 + i)], raw))
        metrics.append(metric("Q", PARTNER, month, None, str(raw["Q"]), "kg", [ev(200 + i)], raw))
        metrics.append(metric("U", PARTNER, month, None, "6.00" if i == 0 else "3.60", "USD/kg", [ev(200 + i)], raw))
        metrics.append(metric("s", PARTNER, month, None, "12.5" if i == 0 else "8.5", "%",
                              [ev(200 + i), ev(300 + i), ev(302 + i)], {"V": raw["V"], "V_ALL": 4800000}))
    metrics.append(metric("r_U", PARTNER, MONTH, BASE, "-40.0", "%", [ev(200), ev(201)],
                          {"V_0": 600000, "Q_0": 100000, "V_1": 360000, "Q_1": 100000}))
    metrics.append(metric("d_s", PARTNER, MONTH, BASE, "-4.0", "pp", [ev(200), ev(201), ev(300), ev(301), ev(302),
                                                                     ev(303)],
                          {"V_0": 600000, "V_ALL_0": 4800000, "V_1": 360000, "V_ALL_1": 4235294}))
    history = [{"month": m, "observation_status": "OBSERVED" if m in (BASE, MONTH) else "UNRESOLVED_ZERO",
                "evidence_ids": [ev(400 + 2 * i), ev(401 + 2 * i)]} for i, m in enumerate(MONTHS)]
    return envelope("get_history", 2, {"months": list(MONTHS), "partners": [PARTNER, "ALL"], "hs10": []}, metrics,
                    {"history": history, "yoy": {"month": MONTH, "baseline_month": BASE}}, [], [])


def compare_partners() -> dict:
    metrics, peers, gaps = [], [], []
    for rank, peer in enumerate(PEERS, start=1):
        base = 500 + 10 * rank
        absent = rank == 5
        flags = ("NOT_COLLECTED",) if absent else ()
        metrics.append(metric("r_U", peer, MONTH, BASE, None if absent else f"-{10 * rank}.0", "%",
                              [ev(base), ev(base + 1)], {"V_0": 4000 * rank, "Q_0": 400, "V_1": 3000 * rank,
                                                         "Q_1": 400}, flags))
        metrics.append(metric("d_s", peer, MONTH, BASE, None if absent else f"{rank}.0", "pp",
                              [ev(base), ev(base + 1), ev(300), ev(301)],
                              {"V_0": 4000 * rank, "V_ALL_0": 4800000, "V_1": 3000 * rank, "V_ALL_1": 4235294}, flags))
        peers.append({"partner": peer, "peer_rank": rank,
                      "months": [{"month": m, "observation_status": "NOT_COLLECTED" if absent else "OBSERVED",
                                  "amount_zero": None if absent else False} for m in (BASE, MONTH)]})
        if absent:
            gaps += [missing(base + 2, peer, HS6, BASE), missing(base + 3, peer, HS6, MONTH)]
    comparability = {"grouping_version": "g0", "peers_allowed": list(PEERS), "peers": peers,
                     "denominator": {"partner": "ALL", "months": [{"month": m, "observation_status": "OBSERVED"}
                                                                  for m in (BASE, MONTH)]}}
    return envelope("compare_partners", 3, {"months": [BASE, MONTH], "partners": list(PEERS) + ["ALL"], "hs10": [],
                                            "grouping_version": "g0"}, metrics, comparability, gaps, [])


def decompose_hs(hs10_count: int = 8) -> dict:
    codes = children(hs10_count)
    metrics = []
    values = {code: {"V_0": 75000, "Q_0": 12500, "V_1": 45000, "Q_1": 12500} for code in codes}
    for i, code in enumerate(codes):
        rows = [ev(600 + 4 * i), ev(601 + 4 * i)]
        metrics.append(metric(f"U@{code}", PARTNER, BASE, None, "6.00", "USD/kg", rows[:1], values[code]))
        metrics.append(metric(f"U@{code}", PARTNER, MONTH, None, "3.60", "USD/kg", rows[1:], values[code]))
        metrics.append(metric(f"r_U@{code}", PARTNER, MONTH, BASE, "-40.0", "%", rows, values[code]))
        metrics.append(metric(f"w@{code}", PARTNER, BASE, None, "12.5", "%", rows[:1] + [ev(200)], values[code]))
        metrics.append(metric(f"w@{code}", PARTNER, MONTH, None, "12.5", "%", rows[1:] + [ev(201)], values[code]))
    all_rows = [ev(200), ev(201)] + [ev(600 + 4 * i + k) for i in range(hs10_count) for k in (0, 1)]
    for symbol, value in (("within_effect", "-2.40"), ("mix_effect", "0.00"), ("residual", "0.00")):
        metrics.append(metric(symbol, PARTNER, MONTH, BASE, value, "USD/kg", all_rows,
                              {"V_0": 600000, "Q_0": 100000, "V_1": 360000, "Q_1": 100000, "hs10_values": values}))
    comparability = {"parent_check": [{"period": m, "row_count": hs10_count, "V_parent": v, "V_hs10": v,
                                       "Q_parent": 100000, "Q_hs10": 100000, "tolerance": Decimal("4.5"),
                                       "V_match": True, "Q_match": True} for m, v in ((BASE, 600000), (MONTH, 360000))],
                     "hs10": [{"month": m, "observation_status": "OBSERVED", "codes": codes} for m in (BASE, MONTH)],
                     "same_hs10_set": True}
    return envelope("decompose_hs", 4, {"months": [BASE, MONTH], "partners": [PARTNER], "hs10": codes}, metrics,
                    comparability, [], [])


def verify_evidence() -> dict:
    return envelope("verify_evidence", 5, {"months": [BASE, MONTH], "partners": [PARTNER], "hs10": []}, [], {}, [],
                    [ev(200), ev(201)])


def all_envelopes(hs10_count: int = 8) -> dict:
    return {"check_comparability": check_comparability(hs10_count), "get_history": get_history(),
            "compare_partners": compare_partners(), "decompose_hs": decompose_hs(hs10_count),
            "verify_evidence": verify_evidence()}
