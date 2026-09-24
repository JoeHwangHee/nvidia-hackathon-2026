"""단위 X2 점유율·변화.

단위 ID: X2
도메인명: metrics_share
소유: D
입력: 상대국 V·`ALL` V(중복 제거)
출력: `s`, `d_s`(pp)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics

공식은 자료 계약 docs/rules/DATA_CONTRACT_V1.md §11.2다. s_t = V_country,t / V_world,t를 백분율(%)로, d_s = s_t −
s_(t−12)를 퍼센트포인트(pp)로 적는다. 분자는 상대국 부모 HS6 행의 V, 분모는 그 HS6 아래 전체국가(`ALL`) HS10 월 행의
금액 합이다(원천 규칙, 행 규칙 5). 선택국 합계를 분모로 쓰지 않는다. d_s는 반올림한 s끼리 빼지 않고 정확한 s끼리
뺀 뒤 한 번 반올림한다. 머리 주석의 입력·출력 줄은 단위 표 docs/plan/UNITS.md §3.3의 문구다. 이 단위는 그 밖에
oracle 점유율 필드(V_country·V_world)를 드러내려고 V(상대국·ALL) 지표도 낸다. 구체적인 모양은 아래와 결정 기록
docs/tracking/decisions/의 DT2 기록(data-decision-dt2-metrics)에 있다.

- ALL 중복 제거(행 규칙 6)는 자료 접근층이 한다. 이 단위는 더하기 전에 달마다 (HS10, 월) 키가 한 번씩인지 세고,
  두 번 나오면 ValueError로 멈춘다(v2에서 중복을 빼지 않으면 분모가 정확히 두 배가 된다).
- null 규칙: 분자·분모 가운데 누락 상태가 있으면 s는 null이다(사유는 그 관측 상태 코드). 분모가 0이면 s는
  null이다(zero_denominator). 분자가 CONFIRMED_NO_TRADE면 0으로 본다(s = 0, 사유에 그 코드를 남긴다). 기준월
  점유율이 0이어도 d_s는 계산한다(룰북 B3-1). s가 하나라도 null이면 d_s는 null이다.

run 입력(JSON 객체)
- snapshot_id, hs6, partner, period, baseline_period: 단위 X1과 같다(snapshot_id 필수).
- parent: 상대국 부모 역할의 관측 행(단위 X1과 같다).
- world: 전체국가(partner_code `ALL`) 역할의 관측 행. 달마다 그 HS6 아래 ALL HS10 월 행(OBSERVED, hs_code는
  그 HS6로 시작하는 10자리, 중복 제거 뒤), 또는 행이 없을 때 그 달의 상태 행.
run 출력
- {"metrics": [V(상대국, t−12), V(상대국, t), V(ALL, t−12), V(ALL, t), s(t−12), s(t), d_s]}. 원소는 자료 계약
  §2.3.4 metric 객체다. V(ALL)의 inputs에는 더한 HS10 행수 row_count를, s에는 V_country·V_world를, d_s에는
  V_country_0·V_world_0·V_country_1·V_world_1(0은 t−12, 1은 t)을 적는다. 근거 ID는 분자 행 다음에 분모 행을
  HS10 코드 순으로 적는다.

반올림 전 값: metric 객체의 value는 §11.3 자릿수로 반올림한 값이다. 임계값 비교처럼 반올림 전 값이 필요하면
exact_value(metric)가 inputs의 정수로 정확한 분수를 다시 계산한다(V는 정수 그대로).
"""
from fractions import Fraction

from tradesentry.metrics import rounding as x4
from tradesentry.metrics import unit_value as x1

SCHEMA_VERSION = x4.SCHEMA_VERSION
WORLD = "ALL"


def parse_world(rows: object, target: dict[str, str]) -> dict[str, list[dict]]:
    """ALL 역할 행을 검사해 달별로 묶는다. 값 행은 그 HS6 아래 HS10 행이고 달마다 코드가 한 번씩이다."""
    hs6 = target["hs6"]
    grouped = x4.parse_rows(rows, role="world", months=(target["baseline_period"], target["period"]),
                            partner=WORLD)
    for month, found in grouped.items():
        if x4.is_value_rows(found):
            codes = [r["hs_code"] for r in found]
            for code in codes:
                if not x4.is_hs10_code(code) or not code.startswith(hs6):
                    raise ValueError(f"world: {month}의 값 행은 {hs6} 아래 HS10 행이어야 한다: {code!r}")
            if len(set(codes)) != len(codes):
                raise ValueError(f"world: {month}에 같은 HS10 행이 두 번 있다(ALL 중복 제거, 행 규칙 6)")
            found.sort(key=lambda r: r["hs_code"])
        else:
            for row in found:
                if row["hs_code"] not in (None, hs6, hs6[:4]):
                    raise ValueError(f"world: {month} 상태 행의 hs_code가 {hs6}와 맞지 않는다: {row['hs_code']!r}")
    return grouped


def country_amount(rows: list[dict]) -> tuple[int | None, list[str]]:
    """상대국 부모 역할 행의 금액과 사유(승격 행은 0)."""
    flags = x4.status_flags(rows)
    if rows[0]["observation_status"] in x4.MISSING_STATUSES:
        return None, flags
    if rows[0]["V"] is None:
        return None, flags + [x4.VALUE_MISSING]
    return rows[0]["V"], flags


def world_amount(rows: list[dict]) -> tuple[int | None, list[str], int | None]:
    """ALL 역할 행의 금액 합, 사유, 더한 HS10 행수(상태 행이면 행수는 None)."""
    flags = x4.status_flags(rows)
    if not x4.is_value_rows(rows):
        amount = 0 if rows[0]["observation_status"] == x4.CONFIRMED_NO_TRADE else None
        return amount, flags, None
    if any(r["V"] is None for r in rows):
        return None, flags + [x4.VALUE_MISSING], len(rows)
    return sum(r["V"] for r in rows), flags, len(rows)


def share_value(country: int | None, world: int | None) -> Fraction | None:
    """점유율(%) = V_country / V_world × 100(정확한 분수). 값이 없거나 분모가 0이면 None이다."""
    if country is None or world is None or world == 0:
        return None
    return Fraction(country, world) * 100


def share_of(country: tuple[int | None, list[str]],
             world: tuple[int | None, list[str], int | None]) -> tuple[Fraction | None, list[str]]:
    """점유율(%)과 사유."""
    flags = country[1] + world[1]
    if country[0] is not None and world[0] == 0:
        flags = flags + [x4.ZERO_DENOMINATOR]
    return share_value(country[0], world[0]), flags


def exact_value(metric: dict) -> Fraction | None:
    """V·s·d_s metric 객체의 반올림 전 정확한 값. value가 null이면 None이다.

    inputs의 정수(V_country·V_world, V_country_0·V_world_0·V_country_1·V_world_1)로 다시 계산한다. V는 반올림하지
    않는 정수라 value 그대로다. 다시 계산한 값을 반올림한 결과가 value와 다르면 ValueError로 멈춘다.
    """
    inputs = metric["inputs"]
    symbol = inputs["metric"]
    if symbol == "V":
        exact = None if metric["value"] is None else x4.to_fraction(metric["value"])
    elif symbol == "s":
        exact = share_value(inputs["V_country"], inputs["V_world"])
    elif symbol == "d_s":
        s0 = share_value(inputs["V_country_0"], inputs["V_world_0"])
        s1 = share_value(inputs["V_country_1"], inputs["V_world_1"])
        exact = None if s0 is None or s1 is None else s1 - s0
    else:
        raise ValueError(f"단위 X2가 다시 계산하는 기호가 아니다: {symbol!r}")
    return x4.checked_exact(metric, exact)


def run(inp: object) -> object:
    """진입 함수. 분자·분모 두 달로 V·s·d_s metric 객체를 낸다."""
    target = x4.parse_target(inp)
    if set(inp) - {"snapshot_id", "hs6", "partner", "period", "baseline_period", "parent", "world"}:
        raise ValueError("X2 입력 키는 snapshot_id·hs6·partner·period·baseline_period·parent·world다")
    snapshot_id = x4.parse_snapshot_id(inp)

    def make(symbol: str, **fields: object) -> dict[str, object]:
        return x4.metric(symbol, snapshot_id=snapshot_id, **fields)

    parent = x1.parse_parent(inp.get("parent"), target)
    world = parse_world(inp.get("world"), target)
    hs6, partner = target["hs6"], target["partner"]
    months = (target["baseline_period"], target["period"])
    amounts, totals, shares, evidence = {}, {}, {}, {}
    metrics = []
    for month in months:
        amounts[month] = country_amount(parent[month])
        metrics.append(make("V", hs6=hs6, partner=partner, period=month, baseline_period=None, values={},
                            evidence_ids=x4.evidence_of(parent[month]), value=amounts[month][0],
                            flags=amounts[month][1]))
    for month in months:
        totals[month] = world_amount(world[month])
        metrics.append(make("V", hs6=hs6, partner=WORLD, period=month, baseline_period=None,
                            values={"row_count": totals[month][2]}, evidence_ids=x4.evidence_of(world[month]),
                            value=totals[month][0], flags=totals[month][1]))
    for month in months:
        shares[month] = share_of(amounts[month], totals[month])
        evidence[month] = x4.evidence_of(parent[month]) + x4.evidence_of(world[month])
        metrics.append(make("s", hs6=hs6, partner=partner, period=month, baseline_period=None,
                            values={"V_country": amounts[month][0], "V_world": totals[month][0]},
                            evidence_ids=evidence[month], value=shares[month][0], flags=shares[month][1]))
    base, period = months
    change = None
    if shares[base][0] is not None and shares[period][0] is not None:
        change = shares[period][0] - shares[base][0]
    metrics.append(make("d_s", hs6=hs6, partner=partner, period=period, baseline_period=base,
                        values={"V_country_0": amounts[base][0], "V_world_0": totals[base][0],
                                "V_country_1": amounts[period][0], "V_world_1": totals[period][0]},
                        evidence_ids=evidence[base] + evidence[period], value=change,
                        flags=shares[base][1] + shares[period][1]))
    return {"metrics": metrics}
