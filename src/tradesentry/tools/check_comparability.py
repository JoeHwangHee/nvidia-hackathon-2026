"""단위 I1 비교 가능성 조회.

단위 ID: I1
도메인명: tools_check_comparability
소유: M
입력: scope
출력: 봉투(기간·단위·분모·하위자료 상태)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics, tradesentry.grouping, tradesentry.policy, tradesentry.tools

사례의 비교월·기준월에 대해 필요한 자료가 있는지(존재 상태)를 본다: 기간, 단위, HS 버전, 대상국 부모 HS6 행, 전체국가
(`ALL`) 분모, 대상국 HS10 하위자료. 값(내용)은 지표로 돌려주지 않고, 판정 상태(정답 상태)도 돌려주지 않는다(개발 플랜
docs/plan/DEV_PLAN.md §6.5). 정본: 자료 계약 docs/rules/DATA_CONTRACT_V1.md §5(봉투), §2.3.2 행 규칙, §3.4, §11.1.

도구 공통 틀(도구 5개가 이 모듈을 import한다. tools 패키지에는 단위 파일 밖의 모듈을 둘 수 없다)
- 요청(도구 입력, 코드가 만든다): {"case_id", "snapshot_id", "scope", "args"?, "policy_version"?, "grouping_version"?,
  "attempt"?, "envelopes"?}. 흐름 조정(단위 I12)의 지금 호출 모양 {"case_id", "snapshot_id", "scope", "args"}에 선택
  키만 더했다. 경로 같은 값은 요청에 두지 않는다.
  - scope: 사례가 정하는 부분 {"hs6", "partner", "month", "baseline_month"}만(판정 정책 단위 P2가 만든다). 비교국과 HS10
    범위는 도구가 스냅샷에서 정한다(비교국은 비교 대상 표 `peer_group`, HS10은 대상국의 하위 행).
  - args: 모델이나 흐름이 준 인자. 도구마다 허용한 키만 받고 값 모양을 검사한다(자료 계약 §5.1: 모델 인자로 DB 경로·
    SQL·외부 URL·셸 명령을 받지 않는다). 허용 밖이면 도구를 돌리지 않고 retryable_error가 있는 봉투를 돌려준다
    (모델이 고쳐 다시 부를 수 있다. 룰북 시나리오 9 "복구할 수 있는 잘못된 조회 범위").
  - policy_version: 정책 수치(K4)를 읽을 버전. 반올림 민감도·중량 허용오차를 쓰는 도구(I1·I4·I5)는 꼭 받는다.
  - grouping_version: 비교 대상 집합(`g0`·`g1`, 합성 자료는 자료 안의 값). 비교국을 쓰는 도구(I3·I5)가 받는다.
  - attempt: 사례 안 도구 시도 순번(1부터). query_id에 넣어 호출마다 고유하게 한다.
  - envelopes: 이 사례에서 앞서 받은 봉투 목록. verify_evidence(I5)만 받는다.
- 코드 오류(요청 모양, 스냅샷을 열 수 없음, 범위 밖 사례, 행 규칙 위반)는 ToolError로 멈춘다. 재시도할 수 없는 오류다.
- 스냅샷은 run이 정본 빌드(`data/snapshots/{snapshot_id}/snapshot_build.sqlite`)를 읽기 전용으로 연다. 승인 전 개발 빌드는
  부르는 코드가 자료 접근층 open_snapshot(snapshot_id, path=…)으로 열어 각 도구의 query(snap, 요청)에 넘긴다.
- 봉투는 단위 K5 make_envelope로 만든다(키 11개, float 금지, 근거 ID 형식·스냅샷 검사). query_id는
  `{도구}-{sha256(case_id·snapshot_id·도구·정규화한 args·attempt)의 앞 16자}`로 결정적이다. elapsed_ms는 이 모듈의
  clock_ms(시험에서 바꿔 끼운다)로 잰다.
- 봉투 scope(실제로 조회한 범위): 사례 scope 네 키 + "months"(읽은 달), "partners"(읽은 상대국. 분모는 `ALL`),
  "hs10"(읽은 대상국 HS10 코드). compare_partners는 "grouping_version"을 더한다.
- missingness: 자료 접근층(K3)의 빠진 자료 항목 {"evidence_id", "request_id", "partner_code", "hs_code", "month", "flow",
  "observation_status"}을 그대로 싣는다. 무거래 확정(`CONFIRMED_NO_TRADE`)은 빠진 자료가 아니라 싣지 않는다(근거 ID에는
  싣는다). `ALL` 분모는 행 규칙 5·6의 중복 제거 뒤에도 값 행이 없는 달만 빠진 자료로 싣는다(자료 접근층이 그렇게 준다).
- 지표는 지표 단위(X1 unit_value, X2 share, X3 decompose)의 run으로만 계산한다(모듈 속성으로 불러 시험에서 대역으로
  바꿀 수 있다). 자료 접근층의 행을 지표 단위의 역할별 입력(parent·world·children 관측 행)으로 옮기는 일은 이 틀이 한다.

check_comparability 봉투
- metrics: 없다(존재 상태만 본다). evidence_ids: 본 행 전부(부모 행, `ALL` HS10 행, 대상국 HS10 행, 상태 행).
- comparability(키는 이 단위가 정했다):
  - comparable: 두 신호 가운데 하나라도 계산할 수 있으면 참(흐름 조정은 거짓이면 이력·하위 조회를 건너뛴다).
  - period {month, baseline_month, yoy}, units(스냅샷 메타 그대로), units_ok(USD·kg인가), hs_version(스냅샷 메타).
  - parent: 달마다 {month, observation_status, weight_zero}. denominator: {partner: "ALL", months: [{month,
    observation_status, hs10_rows}]}. children: {months: [{month, observation_status, hs10_rows}], same_hs10_set}.
  - signals: {unit_value: {evaluable, issues}, share: {evaluable, issues}}. issues는 빠진 자료(missingness가 따로 알린다)
    밖의 문제다: units_mismatch, no_trade:{달}(무거래 확정이라 단가가 없다), zero_weight:{달}, zero_baseline:{달}(기준월
    단가 0), zero_denominator:{달}(분모 0).
  - rounding: 단가를 계산할 수 있을 때의 반올림 민감도. 중량이 행마다 정수 kg로 반올림돼 있어(자료 계약 §11.1) 참값은
    Q ± δ(δ = 정책 tolerance.weight_rounding_kg, 행 하나의 몫) 안에 있다. 그 범위에서 r_U가 움직이는 폭 [r_U_low,
    r_U_high](%, 소수 1자리 사사오입)와, 부호(direction_stable)와 탐지 임계값 충족 여부(threshold_stable, 임계값은 정책
    thresholds.unit_value)가 범위 안에서 바뀌지 않는지, 둘 중 하나라도 바뀌면 unstable=참을 준다. Q ≤ δ인 달이 있으면
    폭이 끝없어 r_U_low·r_U_high는 null이고 unstable=참이다. 판정(보류 등)은 판정 정책(P3)이 한다.
"""
import hashlib
import json
import re
import time
from decimal import Decimal
from fractions import Fraction

from tradesentry.contract import types
from tradesentry.contract.envelope import make_envelope
from tradesentry.contract.evidence_id import parse_evidence_id
from tradesentry.contract.policy_load import PolicyError, load_policy
from tradesentry.dal import query as dal

TOOL = "check_comparability"
SCOPE_KEYS = ("hs6", "partner", "month", "baseline_month")
REQUEST_KEYS = frozenset({"case_id", "snapshot_id", "scope", "args", "policy_version", "grouping_version", "attempt",
                          "envelopes"})
PARTNER_RE = re.compile(r"[A-Z]{2}")
CASE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}")
GROUPING_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,31}")
EXPECTED_UNITS = {"amount": "USD", "weight": "kg"}
INVALID_ARGS = "invalid_args"  # retryable_error.code: 인자가 허용 밖이다
MISSING_STATUSES = (types.NOT_COLLECTED, types.REQUEST_FAILED, types.UNRESOLVED_ZERO)


class ToolError(ValueError):
    """재시도할 수 없는 도구 오류(요청 모양, 스냅샷, 범위, 행 규칙). 흐름 조정이 실패한 시도로 기록한다."""


def clock_ms() -> int:
    """경과 시간을 재는 단조 시계(밀리초). 시험은 이 함수를 바꿔 끼워 elapsed_ms를 고정한다."""
    return time.monotonic_ns() // 1_000_000


def baseline_of(month: str) -> str:
    """비교월 YYYYMM의 기준월(12개월 전, 전년 같은 달)."""
    return f"{int(month[:4]) - 1:04d}{month[4:]}"


def months_between(start: str, end: str) -> list[str]:
    year, month = int(start[:4]), int(start[4:])
    out = []
    while (year, month) <= (int(end[:4]), int(end[4:])):
        out.append(f"{year:04d}{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return out


# ---------------------------------------------------------------------------------------------------- 요청
def parse_request(inp: object, tool: str, *, needs_policy: bool = False, needs_grouping: bool = False,
                  needs_envelopes: bool = False) -> dict:
    """도구 요청을 검사해 정리한다. 요청은 코드가 만들므로 모양이 틀리면 ToolError다(args의 값은 도구가 따로 본다)."""
    if not isinstance(inp, dict):
        raise ToolError("도구 요청은 객체여야 한다")
    unknown = sorted(set(inp) - REQUEST_KEYS)
    if unknown:
        raise ToolError(f"도구 요청에 모르는 키가 있다({', '.join(map(str, unknown))})")
    for key in ("case_id", "snapshot_id", "scope"):
        if key not in inp:
            raise ToolError(f"도구 요청에 {key}가 없다")
    case_id, snapshot_id = inp["case_id"], inp["snapshot_id"]
    if not isinstance(case_id, str) or not CASE_ID_RE.fullmatch(case_id):
        raise ToolError("case_id는 영문·숫자로 시작하는 128자 이하 문자열이어야 한다")
    if not isinstance(snapshot_id, str) or not dal.SNAPSHOT_ID_RE.fullmatch(snapshot_id):
        raise ToolError("snapshot_id 형식이 맞지 않다")
    scope = inp["scope"]
    if not isinstance(scope, dict) or set(scope) != set(SCOPE_KEYS):
        raise ToolError(f"scope는 {', '.join(SCOPE_KEYS)} 네 키만 가진 객체여야 한다")
    hs6, partner, month, baseline = (scope[k] for k in SCOPE_KEYS)
    if not isinstance(hs6, str) or not types.HS6_RE.fullmatch(hs6):
        raise ToolError("scope.hs6는 6자리 숫자 문자열이어야 한다")
    if not isinstance(partner, str) or not PARTNER_RE.fullmatch(partner) or partner == types.ALL_PARTNER:
        raise ToolError("scope.partner는 대상국 2자리 코드여야 한다(ALL이 아니다)")
    if not isinstance(month, str) or not types.MONTH_RE.fullmatch(month):
        raise ToolError("scope.month는 YYYYMM이어야 한다")
    if baseline != baseline_of(month):
        raise ToolError("scope.baseline_month는 month의 12개월 전이어야 한다")
    args = inp.get("args", {})
    if args is None:
        args = {}
    request = {"case_id": case_id, "snapshot_id": snapshot_id, "hs6": hs6, "partner": partner, "month": month,
               "baseline_month": baseline, "args": args, "attempt": inp.get("attempt"), "policy": None,
               "grouping_version": inp.get("grouping_version"), "envelopes": inp.get("envelopes")}
    attempt = request["attempt"]
    if attempt is not None and (isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1):
        raise ToolError("attempt는 1 이상의 정수여야 한다")
    if needs_policy or inp.get("policy_version") is not None:
        version = inp.get("policy_version")
        if not isinstance(version, str):
            raise ToolError("이 도구는 policy_version(정책 수치를 읽을 버전)을 받아야 한다")
        try:
            request["policy"] = load_policy(version)
        except PolicyError as exc:
            raise ToolError(f"정책을 읽을 수 없다: {exc}") from exc
    grouping = request["grouping_version"]
    if needs_grouping and grouping is None:
        raise ToolError("이 도구는 grouping_version(비교 대상 집합)을 받아야 한다")
    if grouping is not None and (not isinstance(grouping, str) or not GROUPING_RE.fullmatch(grouping)):
        raise ToolError("grouping_version 형식이 맞지 않다")
    if needs_envelopes and not isinstance(request["envelopes"], list):
        raise ToolError("verify_evidence는 envelopes(앞서 받은 봉투 목록)를 받아야 한다")
    if not needs_envelopes and request["envelopes"] is not None:
        raise ToolError("envelopes는 verify_evidence만 받는다")
    return request


def args_problem(args: object, allowed: dict) -> str | None:
    """args를 허용 목록(키 → 값 검사 함수, 검사 함수는 문제 문장이나 None을 돌려준다)으로 본다. 문제 문장이나 None."""
    if not isinstance(args, dict):
        return "인자는 객체여야 한다"
    unknown = sorted(str(k) for k in args if k not in allowed)
    if unknown:
        return f"이 도구가 받지 않는 인자다: {', '.join(unknown)}(받는 인자: {', '.join(sorted(allowed)) or '없음'})"
    for key, check in allowed.items():
        if key in args:
            problem = check(args[key])
            if problem:
                return f"{key}: {problem}"
    return None


def query_id(request: dict, tool: str) -> str:
    """도구 호출 1회의 결정적 ID(자료 계약 §4.5는 형식을 정하지 않는다)."""
    try:
        args = json.dumps(request["args"], sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)
    except (TypeError, ValueError):
        args = repr(request["args"])
    text = json.dumps([request["case_id"], request["snapshot_id"], tool, args, request["attempt"]], ensure_ascii=False)
    return f"{tool}-{hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}"


def case_scope(request: dict, *, months: list[str], partners: list[str], hs10: list[str], **extra: object) -> dict:
    """봉투 scope: 사례 scope 네 키 + 실제로 읽은 달·상대국·대상국 HS10 코드."""
    scope = {key: request[key] for key in SCOPE_KEYS}
    scope.update({"months": list(months), "partners": list(dict.fromkeys(partners)), "hs10": sorted(set(hs10))})
    scope.update(extra)
    return scope


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def finish(request: dict, tool: str, snap: dal.Snapshot, started: int, *, scope: dict, evidence_ids: list[str],
           metrics: list[dict] | None = None, comparability: dict | None = None, missingness: list[dict] | None = None,
           retryable_error: dict | None = None) -> dict:
    """봉투를 만든다(단위 K5). 근거 ID와 빠진 자료 항목은 순서를 지키며 중복을 뺀다."""
    missing, seen = [], set()
    for entry in missingness or []:
        if entry["evidence_id"] not in seen:
            seen.add(entry["evidence_id"])
            missing.append(entry)
    return make_envelope(query_id=query_id(request, tool), tool=tool, scope=scope, snapshot_id=snap.snapshot_id,
                         source_kind=snap.source_kind, evidence_ids=unique(evidence_ids), metrics=list(metrics or []),
                         comparability=comparability, missingness=missing, retryable_error=retryable_error,
                         elapsed_ms=max(0, clock_ms() - started))


def refuse(request: dict, tool: str, snap: dal.Snapshot, started: int, problem: str, **detail: object) -> dict:
    """인자가 허용 밖일 때의 봉투: 도구를 돌리지 않고 retryable_error만 싣는다."""
    return finish(request, tool, snap, started, scope=case_scope(request, months=[], partners=[], hs10=[]),
                  evidence_ids=[], retryable_error={"code": INVALID_ARGS, "detail": problem, **detail})


def execute(snap: dal.Snapshot, inp: object, tool: str, body, **needs: bool) -> dict:
    """요청을 검사하고 열린 스냅샷에서 도구 본체를 돌린다. 자료 접근층 오류는 ToolError로 바꾼다."""
    started = clock_ms()
    request = parse_request(inp, tool, **needs)
    if snap.snapshot_id != request["snapshot_id"]:
        raise ToolError("열린 스냅샷의 snapshot_id가 요청과 다르다")
    try:
        return body(snap, request, started)
    except (dal.ScopeError, dal.SnapshotError) as exc:
        raise ToolError(f"{type(exc).__name__}: {exc}") from exc


def run_tool(inp: object, tool: str, body, **needs: bool) -> dict:
    """run의 공통 몸통: 정본 빌드를 읽기 전용으로 열고 execute한다."""
    if not isinstance(inp, dict) or not isinstance(inp.get("snapshot_id"), str):
        raise ToolError("도구 요청에 snapshot_id가 없다")
    try:
        snap = dal.open_snapshot(inp["snapshot_id"])
    except dal.SnapshotError as exc:
        raise ToolError(f"스냅샷을 열 수 없다: {exc}") from exc
    with snap:
        return execute(snap, inp, tool, body, **needs)


# ---------------------------------------------------------------------------------------------------- 행 옮기기
def _missing_entries(value: dict) -> list[dict]:
    """빠진 자료 항목에서 무거래 확정 행을 뺀다(무거래 확정은 빠진 자료가 아니다)."""
    return [e for e in value["missingness"] if e["observation_status"] != types.CONFIRMED_NO_TRADE]


def _status_rows(entries: list[dict], partner_code: str) -> list[dict]:
    return [{"month": e["month"], "hs_code": e["hs_code"], "partner_code": partner_code, "flow": types.METRIC_FLOW,
             "amount_usd": None, "net_weight_kg": None, "observation_status": e["observation_status"],
             "evidence_ids": [e["evidence_id"]]} for e in entries]


def _value_row(month: str, hs_code: str, partner_code: str, amount: int | None, weight: int | None, status: str,
               evidence: list[str]) -> dict:
    return {"month": month, "hs_code": hs_code, "partner_code": partner_code, "flow": types.METRIC_FLOW,
            "amount_usd": amount, "net_weight_kg": weight, "observation_status": status, "evidence_ids": list(evidence)}


class Rows:
    """한 역할의 지표 단위 입력 행, 빠진 자료 항목, 근거 ID를 함께 모은다."""

    def __init__(self) -> None:
        self.rows: list[dict] = []
        self.missing: list[dict] = []
        self.evidence: list[str] = []

    def add_status(self, value: dict, partner_code: str) -> None:
        entries = _missing_entries(value)
        self.rows += _status_rows(entries, partner_code)
        self.missing += entries
        self.evidence += [e["evidence_id"] for e in value["missingness"]]


def parent_rows(snap: dal.Snapshot, hs6: str, partner: str, months: list[str]) -> tuple[Rows, list[dict]]:
    """상대국 부모 HS6 행(단위 X1·X2의 parent 역할)과 자료 접근층의 달별 값."""
    out, values = Rows(), snap.parent_series(hs6, partner, months)
    for value in values:
        status = value["observation_status"]
        if status in (types.OBSERVED, types.CONFIRMED_NO_TRADE):
            out.rows.append(_value_row(value["month"], hs6, partner, value["amount_usd"], value["net_weight_kg"],
                                       status, value["evidence_ids"]))
            out.evidence += value["evidence_ids"]
        else:
            out.add_status(value, partner)
    return out, values


def world_rows(snap: dal.Snapshot, hs6: str, months: list[str]) -> tuple[Rows, list[dict]]:
    """전체국가 분모 행(단위 X2의 world 역할). 값이 있는 달은 중복을 뺀 `ALL` HS10 행을 하나씩 되살린다."""
    out, values = Rows(), snap.world_series(hs6, months)
    for value in values:
        status = value["observation_status"]
        if status == types.OBSERVED:
            for evidence_id in value["evidence_ids"]:
                row = snap.row("observation", parse_evidence_id(evidence_id).rowid)
                if row is None:
                    raise ToolError(f"ALL 분모 행을 찾을 수 없다({evidence_id})")
                out.rows.append(_value_row(value["month"], row["hs_code"], types.ALL_PARTNER, row["amount_usd"],
                                           row["net_weight_kg"], types.OBSERVED, [evidence_id]))
            out.evidence += value["evidence_ids"]
        elif status == types.CONFIRMED_NO_TRADE:
            out.rows.append(_value_row(value["month"], hs6, types.ALL_PARTNER, None, None, status,
                                       value["evidence_ids"]))
            out.evidence += value["evidence_ids"]
        else:
            out.add_status(value, types.ALL_PARTNER)
    return out, values


def children_rows(snap: dal.Snapshot, hs6: str, partner: str, months: list[str]) -> tuple[Rows, list[dict]]:
    """상대국 HS10 하위 행(단위 X3의 children 역할). 값 행이 있는 달의 상태 행은 빠진 자료로만 싣는다."""
    out, values = Rows(), [snap.children(hs6, partner, month) for month in months]
    for value in values:
        month = value["month"]
        if value["rows"]:
            for row in value["rows"]:
                out.rows.append(_value_row(month, row["hs10"], partner, row["amount_usd"], row["net_weight_kg"],
                                           types.OBSERVED, [row["evidence_id"]]))
                out.evidence.append(row["evidence_id"])
            out.missing += _missing_entries(value)
            out.evidence += [e["evidence_id"] for e in value["missingness"]]
        elif value["observation_status"] == types.CONFIRMED_NO_TRADE:
            out.rows.append(_value_row(month, hs6, partner, None, None, types.CONFIRMED_NO_TRADE, []))
        else:
            out.add_status(value, partner)
    return out, values


def target(request: dict, partner: str | None = None) -> dict:
    """지표 단위 입력의 대상 네 키(hs6·partner·period·baseline_period)."""
    return {"hs6": request["hs6"], "partner": partner or request["partner"], "period": request["month"],
            "baseline_period": request["baseline_month"]}


def metrics_of(output: object, unit: str) -> list[dict]:
    if not isinstance(output, dict) or not isinstance(output.get("metrics"), list):
        raise ToolError(f"지표 단위 {unit}의 출력에 metrics 목록이 없다")
    return output["metrics"]


# ---------------------------------------------------------------------------------------------------- 반올림 민감도
def round_half_up(value: Fraction, places: int) -> Decimal:
    """분수를 소수 places자리로 사사오입한다(한 번만, 정확히. float·Decimal 나눗셈을 거치지 않는다)."""
    scaled = value * 10 ** places
    whole, rest = divmod(abs(scaled.numerator), scaled.denominator)
    if 2 * rest >= scaled.denominator:
        whole += 1
    digits = -whole if scaled < 0 else whole
    return Decimal(f"{digits}E-{places}")


def rounding_sensitivity(v0: int, q0: int, v1: int, q1: int, delta: Decimal | int, threshold: Decimal | int) -> dict:
    """중량 반올림 폭(±δ) 안에서 r_U(%)가 움직이는 범위와 안정성. v0·q0는 기준월, v1·q1은 비교월 부모 HS6 값이다."""
    d, theta = Fraction(delta), Fraction(threshold)
    out = {"weight_rounding_kg": delta, "threshold": threshold, "r_U_low": None, "r_U_high": None,
           "direction_stable": False, "threshold_stable": False, "unstable": True}
    if q0 - d <= 0 or q1 - d <= 0 or v0 <= 0:
        return out
    # r_U = (v1 / q1) / (v0 / q0) − 1 은 q0에 대해 늘고 q1에 대해 준다.
    low = (Fraction(v1) * (q0 - d) / (Fraction(v0) * (q1 + d)) - 1) * 100
    high = (Fraction(v1) * (q0 + d) / (Fraction(v0) * (q1 - d)) - 1) * 100
    direction = low > 0 or high < 0
    all_triggered = low >= theta or high <= -theta
    none_triggered = -theta < low and high < theta
    out.update({"r_U_low": round_half_up(low, 1), "r_U_high": round_half_up(high, 1), "direction_stable": direction,
                "threshold_stable": all_triggered or none_triggered,
                "unstable": not (direction and (all_triggered or none_triggered))})
    return out


# ---------------------------------------------------------------------------------------------------- 본체
def _month_state(values: list[dict], months: list[str]) -> dict[str, dict]:
    return {value["month"]: value for value in values if value["month"] in months}


def _body(snap: dal.Snapshot, request: dict, started: int) -> dict:
    problem = args_problem(request["args"], {})
    if problem:
        return refuse(request, TOOL, snap, started, problem)
    hs6, partner = request["hs6"], request["partner"]
    base, period = request["baseline_month"], request["month"]
    months = [base, period]
    parent, parent_values = parent_rows(snap, hs6, partner, months)
    world, world_values = world_rows(snap, hs6, months)
    children, children_values = children_rows(snap, hs6, partner, months)
    p = _month_state(parent_values, months)
    w = _month_state(world_values, months)
    units = snap.meta.get("units")
    units_ok = units == EXPECTED_UNITS

    unit_issues, share_issues = [], []
    if not units_ok:
        unit_issues.append("units_mismatch")
        share_issues.append("units_mismatch")
    parent_block = []
    for month in months:
        value = p[month]
        status = value["observation_status"]
        weight_zero = value["net_weight_kg"] == 0 if status == types.OBSERVED else None
        parent_block.append({"month": month, "observation_status": status, "weight_zero": weight_zero})
        if status == types.CONFIRMED_NO_TRADE:
            unit_issues.append(f"no_trade:{month}")
        elif weight_zero:
            unit_issues.append(f"zero_weight:{month}")
    if p[base]["observation_status"] == types.OBSERVED and p[base]["amount_usd"] == 0 \
            and p[base]["net_weight_kg"] != 0:
        unit_issues.append(f"zero_baseline:{base}")
    parent_observed = all(p[m]["observation_status"] == types.OBSERVED for m in months)
    unit_evaluable = units_ok and parent_observed and not unit_issues

    denominator = []
    for month in months:
        value = w[month]
        status = value["observation_status"]
        rows = len(value["hs10_codes"]) if status == types.OBSERVED else 0
        denominator.append({"month": month, "observation_status": status, "hs10_rows": rows})
        if status == types.CONFIRMED_NO_TRADE or (status == types.OBSERVED and value["amount_usd"] == 0):
            share_issues.append(f"zero_denominator:{month}")
    share_evaluable = (units_ok and all(p[m]["observation_status"] in (types.OBSERVED, types.CONFIRMED_NO_TRADE)
                                        for m in months)
                       and all(w[m]["observation_status"] == types.OBSERVED for m in months) and not share_issues)

    children_block, code_sets = [], []
    for value in children_values:
        codes = [row["hs10"] for row in value["rows"]]
        children_block.append({"month": value["month"], "observation_status": value["observation_status"],
                               "hs10_rows": len(codes)})
        code_sets.append(set(codes) if value["rows"] else None)
    same_set = None if None in code_sets else code_sets[0] == code_sets[1]

    rounding = None
    if unit_evaluable:
        policy = request["policy"]
        rounding = rounding_sensitivity(p[base]["amount_usd"], p[base]["net_weight_kg"], p[period]["amount_usd"],
                                        p[period]["net_weight_kg"], policy["tolerance"]["weight_rounding_kg"],
                                        policy["thresholds"]["unit_value"])

    comparability = {
        "comparable": unit_evaluable or share_evaluable,
        "period": {"month": period, "baseline_month": base, "yoy": True},
        "units": units, "units_ok": units_ok, "hs_version": snap.meta.get("hs_version"),
        "parent": parent_block,
        "denominator": {"partner": types.ALL_PARTNER, "months": denominator},
        "children": {"months": children_block, "same_hs10_set": same_set},
        "signals": {"unit_value": {"evaluable": unit_evaluable, "issues": unit_issues},
                    "share": {"evaluable": share_evaluable, "issues": share_issues}},
        "rounding": rounding,
    }
    hs10 = [row["hs10"] for value in children_values for row in value["rows"]]
    scope = case_scope(request, months=months, partners=[partner, types.ALL_PARTNER], hs10=hs10)
    evidence = parent.evidence + world.evidence + children.evidence
    missing = parent.missing + world.missing + children.missing
    return finish(request, TOOL, snap, started, scope=scope, evidence_ids=evidence, comparability=comparability,
                  missingness=missing)


def query(snap: dal.Snapshot, inp: object) -> dict:
    """열린 스냅샷(개발 빌드 포함)에서 비교 가능성을 본다. 요청 모양은 머리 설명의 도구 공통 틀이다."""
    return execute(snap, inp, TOOL, _body, needs_policy=True)


def run(inp: object) -> object:
    """진입 함수. 도구 요청 → 봉투. 스냅샷은 정본 빌드를 읽기 전용으로 연다."""
    return run_tool(inp, TOOL, _body, needs_policy=True)

