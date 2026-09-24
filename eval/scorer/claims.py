"""단위 C1 주장 채점.

단위 ID: C1
도메인명: scorer_claims
소유: D
입력: 주장·정답표·원본 행
출력: 필드별 판정(룰북 B3-1). 주장 채점 기록 `scorer_claims-{시각}.jsonl`
허용 import: 표준 라이브러리, eval.scorer

보고서의 typed claim(정해진 필드에 담은 사실 주장) 하나마다 스냅샷 원본 행에서 기대값을 따로 계산해 룰북
docs/eval/RULEBOOK.md B3-1의 순서(대상 → 단위 → 방향 → 값 → 근거, data_status는 수집 계획 대조가 먼저)로 판정하고,
주장 채점 기록(자료 계약 docs/rules/DATA_CONTRACT_V1.md §9.2의 키 13개)을 만든다.

- 독립 구현이다. tradesentry 패키지(등록부·커널 포함)와 eval.datagen을 import하지 않고, 계약 상수는 이 파일에 따로
  적는다(자료 계약 §10.3, docs/plan/UNITS.md §2). 모델·네트워크를 부르지 않는 결정적 계산이다.
- 기대값은 정수 USD·kg에서 Fraction(정확한 유리수)으로 계산하고 사사오입(ROUND_HALF_UP, 딱 절반은 0에서 먼 쪽)한다.
  float를 쓰지 않는다(자료 계약 §11.3).
- 원천 규칙(자료 계약 §2.3.2 행 규칙 4~6, §11.2): 상대국 값은 부모 HS6 행(HS4 스캔이 준 상대국 HS6 월 행), 점유율
  분모는 그 HS6 아래 ALL HS10 월 행 합(같은 키의 중복 행은 동등하며 값이 다르면 계산하지 않는다), 총계 행
  (month가 RAW:로 시작)은 근거가 될 수 없다. 승격된 달(CONFIRMED_NO_TRADE)은 V·Q를 0으로 다룬다.
- 근거 ID `ev:<snapshot_id>:<table>:<rowid>`의 rowid는 앞자리 0이 없는 양의 정수로만 푼다(`013`은 풀리지 않는다).
  런타임 자료 접근층과 같은 해석이다(자료 계약 §4.4).
- 이 파일은 다른 채점기 단위가 함께 쓰는 수 비교 규칙(값 비교, 자릿수)과 JSON 도우미를 둔다. 다른 단위 파일은 이
  파일을 import하고, 이 파일은 다른 채점기 단위를 import하지 않는다(순환 import 방지).

알려진 빈칸(F1 전 보완 목록에 적는다)
- 승격 규칙(UNRESOLVED_ZERO → CONFIRMED_NO_TRADE)의 독립 구현: policy_v1 승인 전이라 규칙이 없다. 지금은 스냅샷 행의
  observation_status를 그대로 쓴다(룰북 B3-1 "data_status 주장" 3번은 승인 뒤 보완).
- 부모-하위 중량 대조 허용오차: 자료 계약 §11.1의 출발값 0.5kg×(행수+1)을 쓴다. policy_v1 승인 값으로 바꾼다.
- comparison 주장의 비교집합 소속 확인은 하지 않는다(사례 문맥과 동결 비교집합 표의 형식이 정해진 뒤 보완).
"""
import json
import math
import re
from collections import defaultdict
from decimal import Decimal
from fractions import Fraction

SOURCE_CLAIM = "claim"
SOURCE_PROSE = "prose"

CORRECT = "CORRECT"
WRONG_VALUE = "WRONG_VALUE"
WRONG_DIRECTION = "WRONG_DIRECTION"
WRONG_UNIT = "WRONG_UNIT"
WRONG_REFERENT = "WRONG_REFERENT"
UNSUPPORTED = "UNSUPPORTED"
UNBACKED_PROSE = "UNBACKED_PROSE"
OUTCOMES = (CORRECT, WRONG_VALUE, WRONG_DIRECTION, WRONG_UNIT, WRONG_REFERENT, UNSUPPORTED, UNBACKED_PROSE)

# 주장 채점 기록 키(자료 계약 §9.2, 명세 §4.10-2 원문 순서)
RECORD_KEYS = ("run_id", "report_id", "claim_id", "source", "outcome", "expected_value", "reported_value",
               "unit_expected", "unit_reported", "tolerance", "referent_resolved", "evidence_ok", "note")

# typed claim 필드(자료 계약 §6, 명세 §4.8 원문)
CLAIM_FIELDS = ("claim_id", "claim_type", "hs6", "partner", "period", "baseline_period", "metric", "value", "unit",
                "direction", "evidence_ids", "text")
CLAIM_TYPES = ("value", "change", "share", "share_change", "decomposition", "comparison", "data_status")
DIRECTIONS = ("UP", "DOWN", "FLAT", "NA")

OBSERVED = "OBSERVED"
NOT_COLLECTED = "NOT_COLLECTED"
REQUEST_FAILED = "REQUEST_FAILED"
UNRESOLVED_ZERO = "UNRESOLVED_ZERO"
CONFIRMED_NO_TRADE = "CONFIRMED_NO_TRADE"
OBS_STATUSES = (OBSERVED, NOT_COLLECTED, REQUEST_FAILED, UNRESOLVED_ZERO, CONFIRMED_NO_TRADE)
STATUS_ROW_STATUSES = frozenset({NOT_COLLECTED, REQUEST_FAILED, UNRESOLVED_ZERO, CONFIRMED_NO_TRADE})

# 지표 기호의 단위(자료 계약 §11.2)와 표시 자릿수(§11.3). w는 w@<HS10>, U@·r_U@는 앞 기호를 따른다.
METRIC_UNITS = {"V": "USD", "Q": "kg", "U": "USD/kg", "r_U": "%", "s": "%", "d_s": "pp", "within_effect": "USD/kg",
                "mix_effect": "USD/kg", "residual": "USD/kg", "w": "%"}
METRIC_DIGITS = {"V": 0, "Q": 0, "U": 2, "r_U": 1, "s": 1, "d_s": 1, "within_effect": 2, "mix_effect": 2,
                 "residual": 2, "w": 1}
STATUS_METRIC = "observation_status"
HS10_BASES = ("U", "r_U", "w", STATUS_METRIC)  # @<HS10 코드>를 붙일 수 있는 기호(자료 계약 §6.2)
PLAIN_BASES = frozenset(set(METRIC_UNITS) - {"w"} | {STATUS_METRIC})  # @ 없이 쓰는 기호

# claim_type마다 쓸 수 있는 기호(자료 계약 §6.2). comparison은 "r_U, d_s 등"을 비교국 한 나라의 값으로 읽는다.
TYPE_METRICS = {
    "value": frozenset({"V", "Q", "U", "U@", "w@"}),
    "change": frozenset({"r_U", "r_U@"}),
    "share": frozenset({"s"}),
    "share_change": frozenset({"d_s"}),
    "decomposition": frozenset({"within_effect", "mix_effect", "residual"}),
    "comparison": frozenset({"V", "Q", "U", "s", "r_U", "d_s"}),
    "data_status": frozenset({STATUS_METRIC, STATUS_METRIC + "@"}),
}
CHANGE_BASES = frozenset({"r_U", "d_s", "within_effect", "mix_effect", "residual"})  # 기준월 t−12가 필요한 기호
NO_ALL_BASES = frozenset({"s", "d_s", "within_effect", "mix_effect", "residual"})  # partner ALL로 정의하지 않는 기호
LEVEL_BASES = frozenset({"V", "Q", "U", "s", "w"})  # 수준 기호(산문 PT-8의 짝 규칙이 보는 "수준 claim")

# 룰북 B3-1 "민감도 보고": 보고값과 반올림 전 기대값의 차가 비교 자리 1단위 미만인 WRONG_VALUE. 요약(단위 C4)이 이
# 표식이 든 기록을 센다. 기록 키가 고정(자료 계약 §9.2)이라 메모에 이 글자를 그대로 넣는다.
DIGITS_ONLY_MARK = "[자릿수만 다른 WRONG_VALUE]"

MONTH_RE = re.compile(r"^(\d{4})(0[1-9]|1[0-2])$")
HS6_RE = re.compile(r"^\d{6}$")
HS10_RE = re.compile(r"^\d{10}$")
PARTNER_RE = re.compile(r"^(?:ALL|[A-Z]{2})$")
ROWID_RE = re.compile(r"^[1-9][0-9]*$")  # 앞자리 0이 없는 양의 정수만(자료 계약 §4.4)
TABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# 부모 HS6 행과 HS10 하위 행 합의 중량 대조 허용오차: 0.5kg × (하위 행 수 + 1)(자료 계약 §11.1 출발값).
WEIGHT_TOLERANCE_PER_ROW = Fraction(1, 2)


class ScorerInputError(Exception):
    """채점기 입력(실행 기록, 보고서, 정답표, 실행 조건 입력 파일, 스냅샷)이 약속한 형식이 아니다."""


# ----------------------------------------------------------------------------- 수와 자릿수

def is_number(value: object) -> bool:
    """JSON 수로 읽은 값인가(bool 제외, Decimal은 유한값만)."""
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    return isinstance(value, Decimal) and value.is_finite()


def displayed_digits(value: object) -> int:
    """보고값이 보인 소수 자리수(끝자리 0 포함, 룰북 B3-1). 정수는 0이다."""
    if isinstance(value, Decimal):
        exponent = value.as_tuple().exponent
        return max(0, -exponent) if isinstance(exponent, int) else 0
    return 0


def round_half_up(x: Fraction, digits: int) -> Fraction:
    """x를 소수 digits 자리(음수면 10의 거듭제곱 자리)에서 사사오입한다. 딱 절반은 0에서 먼 쪽으로 간다."""
    scale = Fraction(10) ** digits
    rounded = Fraction(math.floor(abs(x) * scale + Fraction(1, 2))) / scale
    return -rounded if x < 0 else rounded


def number_out(x: Fraction, digits: int) -> object:
    """x를 digits 자리에서 사사오입해 출력용 수로 바꾼다. digits가 0 이하면 int, 아니면 그 자리수의 Decimal."""
    r = round_half_up(x, digits)
    if digits <= 0:
        return int(r)
    return Decimal(int(r * 10 ** digits)).scaleb(-digits)


def step_out(digits: int) -> object:
    """비교 자리 1단위(허용오차 기록용). 소수 자리면 Decimal("0.01")처럼, 아니면 int."""
    if digits <= 0:
        return 10 ** (-digits)
    return Decimal(1).scaleb(-digits)


def compare_value(expected: Fraction, reported: object, contract_digits: int | None) -> tuple[bool, int, bool]:
    """룰북 B3-1 "값 비교". (일치 여부, 비교 자리수, 자릿수만 다른 불일치 여부)를 돌려준다.

    비교 자리수는 보고값이 보인 자리수와 계약 자릿수(§11.3) 가운데 작은 쪽이다. 두 값을 모두 그 자리에서 사사오입해
    같으면 일치다. 자릿수만 다른 불일치는 보고값과 반올림 전 기대값의 차가 비교 자리 1단위 미만인 경우다."""
    shown = displayed_digits(reported)
    digits = shown if contract_digits is None else min(shown, contract_digits)
    rep = Fraction(reported)
    match = round_half_up(expected, digits) == round_half_up(rep, digits)
    digits_only = (not match) and abs(rep - expected) < Fraction(10) ** (-digits)
    return match, digits, digits_only


def shift_month(month: str, delta: int) -> str:
    """YYYYMM에 달 수를 더한다."""
    year, mon = int(month[:4]), int(month[4:])
    index = year * 12 + (mon - 1) + delta
    return f"{index // 12:04d}{index % 12 + 1:02d}"


# ----------------------------------------------------------------------------- JSON 읽기·쓰기

def _refuse_constant(name: str) -> object:
    raise ValueError(f"JSON 상수 {name}은 쓰지 않는다")


def loads_json(text: str) -> object:
    """JSON 문서를 읽는다. 소수는 Decimal로 원문 표기(끝자리 0)를 보존하고 NaN·Infinity는 거부한다."""
    return json.loads(text, parse_float=Decimal, parse_constant=_refuse_constant)


def dumps_json(value: object) -> str:
    """한 줄 JSON으로 쓴다. Decimal은 글자 그대로의 수 토큰으로 쓰고(예: 20.30), float는 받지 않는다."""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("유한하지 않은 수는 쓰지 않는다")
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(dumps_json(v) for v in value) + "]"
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("JSON 객체의 키는 문자열이어야 한다")
            parts.append(json.dumps(key, ensure_ascii=False) + ": " + dumps_json(item))
        return "{" + ", ".join(parts) + "}"
    raise ValueError(f"JSON으로 쓸 수 없는 값: {type(value).__name__}")


def dumps_jsonl(records: list) -> str:
    """기록 목록을 JSONL(한 줄에 JSON 하나)로 쓴다."""
    return "".join(dumps_json(record) + "\n" for record in records)


# ----------------------------------------------------------------------------- 스냅샷 색인

def _int_or_none(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


class Snapshot:
    """스냅샷 행의 읽기 전용 색인. tables는 테이블 이름 → {rowid: 행(열 이름 → 값)}이다.

    지표는 flow가 import인 월 행만 쓴다(자료 계약 §2.3.2 행 규칙 2). 총계 행(month가 RAW:로 시작)은 색인에 넣지 않고
    totals에만 적는다(근거가 될 수 없다)."""

    def __init__(self, snapshot_id: str, tables: dict[str, dict[int, dict]]):
        self.snapshot_id = snapshot_id
        self.tables = tables
        self.parent: dict[tuple, list[int]] = defaultdict(list)       # (상대국, HS6, 월) → OBSERVED 부모 HS6 행
        self.children: dict[tuple, dict[str, list[int]]] = defaultdict(dict)  # (상대국, HS6, 월) → HS10 → 행들
        self.status: dict[tuple, list[int]] = defaultdict(list)       # (상대국, HS 코드, 월) → 상태 행
        self.partners: set[str] = set()
        self.months: set[str] = set()
        self.hs_codes: set[str] = set()
        self.hs6_codes: set[str] = set()
        self.hs10_codes: set[str] = set()
        self.totals: set[int] = set()
        for rowid, row in tables.get("observation", {}).items():
            hs = str(row.get("hs_code") or "")
            partner = str(row.get("partner_code") or "")
            month = str(row.get("month") or "")
            level = row.get("hs_level")
            level = level if isinstance(level, int) and not isinstance(level, bool) else len(hs)
            self.hs_codes.add(hs)
            self.partners.add(partner)
            if month.startswith("RAW:"):
                self.totals.add(rowid)
                continue
            if not MONTH_RE.match(month):
                continue
            self.months.add(month)
            if level == 6:
                self.hs6_codes.add(hs)
            elif level == 10:
                self.hs6_codes.add(hs[:6])
                self.hs10_codes.add(hs)
            if row.get("flow") != "import":
                continue
            status = row.get("observation_status")
            if status == OBSERVED:
                if level == 6 and partner != "ALL":
                    self.parent[(partner, hs, month)].append(rowid)
                elif level == 10:
                    self.children[(partner, hs[:6], month)].setdefault(hs, []).append(rowid)
            elif status in STATUS_ROW_STATUSES:
                self.status[(partner, hs, month)].append(rowid)

    @classmethod
    def from_json(cls, doc: object) -> "Snapshot":
        """단위 run 입력의 snapshot 객체({"snapshot_id", "tables": {테이블: [행(rowid 포함)]}})로 만든다."""
        if not isinstance(doc, dict) or not isinstance(doc.get("snapshot_id"), str) \
                or not isinstance(doc.get("tables"), dict):
            raise ScorerInputError("snapshot은 snapshot_id와 tables를 가진 객체여야 한다")
        tables: dict[str, dict[int, dict]] = {}
        for name, rows in doc["tables"].items():
            if not TABLE_RE.match(name) or not isinstance(rows, list):
                raise ScorerInputError("snapshot.tables의 형식이 맞지 않다")
            table: dict[int, dict] = {}
            for row in rows:
                rowid = row.get("rowid") if isinstance(row, dict) else None
                if not isinstance(rowid, int) or isinstance(rowid, bool) or rowid <= 0 or rowid in table:
                    raise ScorerInputError("snapshot 행마다 서로 다른 양의 정수 rowid가 있어야 한다")
                table[rowid] = row
            tables[name] = table
        return cls(doc["snapshot_id"], tables)

    def row(self, rowid: int) -> dict:
        return self.tables["observation"][rowid]

    def status_of(self, rowid: int) -> str:
        return str(self.row(rowid).get("observation_status"))

    def values_of(self, rowid: int) -> tuple[int | None, int | None]:
        row = self.row(rowid)
        return _int_or_none(row.get("amount_usd")), _int_or_none(row.get("net_weight_kg"))

    def status_rows(self, keys: list[tuple]) -> dict[str, set[int]]:
        """여러 (상대국, HS 코드, 월) 키의 상태 행을 상태별로 모은다."""
        grouped: dict[str, set[int]] = defaultdict(set)
        for key in keys:
            for rowid in self.status.get(key, []):
                grouped[self.status_of(rowid)].add(rowid)
        return dict(grouped)

    def in_plan(self, partner: str, hs6: str, month: str) -> bool:
        """수집 계획(또는 비교 대상)에 든 키인가. 스냅샷에 그 상대국·HS6·월의 행이 어떤 상태로든 있으면 계획 안으로
        본다(snapshot-build가 계획에 있는데 기록이 없는 키마다 NOT_COLLECTED 행을 만든다, 자료 계약 §3.4)."""
        return partner in self.partners and hs6 in self.hs6_codes and month in self.months


# ----------------------------------------------------------------------------- 기대값 계산

class Expect:
    """기대값 하나. value는 Fraction(수) 또는 None(계산하지 않는 대상)이다. required는 근거가 모두 포함해야 하는 원본 행
    묶음 목록이고, 묶음 하나는 서로 동등한 행의 rowid 집합이다(그중 어느 행을 인용해도 된다)."""

    def __init__(self, value: Fraction | None = None, required: list | None = None, note: str = ""):
        self.value = value
        self.required = required or []
        self.note = note


def _unique_values(snap: Snapshot, rowids: list[int]) -> tuple[int | None, int | None] | None:
    """동등해야 하는 행들의 (V, Q). 값이 서로 다르면 None."""
    values = {snap.values_of(rowid) for rowid in rowids}
    return values.pop() if len(values) == 1 else None


def _promoted(snap: Snapshot, keys: list[tuple]) -> set[int]:
    return snap.status_rows(keys).get(CONFIRMED_NO_TRADE, set())


def _missing_note(snap: Snapshot, keys: list[tuple], what: str) -> str:
    statuses = sorted(snap.status_rows(keys))
    return f"{what} 없음({', '.join(statuses) if statuses else '상태 행 없음'})"


def level_values(snap: Snapshot, partner: str, hs6: str, month: str) -> tuple:
    """(V, Q, 근거 묶음, 메모). 상대국은 부모 HS6 행, ALL은 HS10 행 합(중복 제거). 승격된 달은 V·Q가 0이다."""
    if partner == "ALL":
        return world_values(snap, hs6, month)
    rows = snap.parent.get((partner, hs6, month), [])
    if rows:
        pair = _unique_values(snap, rows)
        if pair is None:
            return None, None, [], "같은 키의 부모 HS6 행 값이 서로 다르다"
        return pair[0], pair[1], [frozenset(rows)], ""
    keys = [(partner, hs6, month), (partner, hs6[:4], month)]
    promoted = _promoted(snap, keys)
    if promoted:
        return 0, 0, [frozenset(promoted)], "승격된 달(CONFIRMED_NO_TRADE)은 V·Q를 0으로 다룬다"
    return None, None, [], _missing_note(snap, keys, f"{month} 부모 HS6 행")


def world_values(snap: Snapshot, hs6: str, month: str) -> tuple:
    """전체국가(ALL) HS6 월 값: 그 HS6 아래 ALL HS10 월 행 합. 같은 HS10 키의 중복 행은 동등하고 값이 다르면 계산하지
    않는다(자료 계약 §2.3.2 행 규칙 5·6)."""
    kids = snap.children.get(("ALL", hs6, month), {})
    if not kids:
        keys = [("ALL", hs6, month), ("ALL", hs6[:4], month)]
        promoted = _promoted(snap, keys)
        if promoted:
            return 0, 0, [frozenset(promoted)], "승격된 달(CONFIRMED_NO_TRADE)은 V·Q를 0으로 다룬다"
        return None, None, [], _missing_note(snap, keys, f"{month} ALL HS10 행")
    total_v: int | None = 0
    total_q: int | None = 0
    required = []
    for code in sorted(kids):
        pair = _unique_values(snap, kids[code])
        if pair is None:
            return None, None, [], f"ALL 중복 행 값이 서로 다르다({code}, {month})"
        v, q = pair
        total_v = None if (total_v is None or v is None) else total_v + v
        total_q = None if (total_q is None or q is None) else total_q + q
        required.append(frozenset(kids[code]))
    return total_v, total_q, required, ""


def _ratio(numerator: int | None, denominator: int | None) -> Fraction | None:
    if numerator is None or denominator is None or denominator == 0:
        return None
    return Fraction(numerator, denominator)


def expect_level(snap: Snapshot, base: str, partner: str, hs6: str, month: str) -> Expect:
    """V·Q·U·s의 기대값."""
    v, q, required, note = level_values(snap, partner, hs6, month)
    if base == "V":
        return Expect(None if v is None else Fraction(v), required, note)
    if base == "Q":
        return Expect(None if q is None else Fraction(q), required, note)
    if base == "U":
        if v is not None and q == 0:
            return Expect(None, required, "중량이 0이라 단가를 계산하지 않는다")
        return Expect(_ratio(v, q), required, note)
    if base == "s":
        wv, _, wrequired, wnote = world_values(snap, hs6, month)
        if v is None or wv is None:
            return Expect(None, required + wrequired, note or wnote)
        if wv == 0:
            return Expect(None, required + wrequired, "전체국가 금액이 0이라 점유율을 계산하지 않는다")
        return Expect(Fraction(v, wv) * 100, required + wrequired, "")
    raise ValueError(base)


def expect_change(snap: Snapshot, base: str, partner: str, hs6: str, month: str, baseline: str) -> Expect:
    """r_U·d_s의 기대값(전년동월)."""
    level = "U" if base == "r_U" else "s"
    now, before = expect_level(snap, level, partner, hs6, month), expect_level(snap, level, partner, hs6, baseline)
    required = now.required + before.required
    if now.value is None or before.value is None:
        return Expect(None, required, now.note or before.note or "비교할 값을 계산하지 않는다")
    if base == "r_U":
        if before.value == 0:
            return Expect(None, required, "기준월 단가가 0이라 변화율을 계산하지 않는다")
        return Expect((now.value / before.value - 1) * 100, required, "")
    return Expect(now.value - before.value, required, "")


def _child_values(snap: Snapshot, partner: str, hs6: str, month: str) -> tuple[dict | None, list, str]:
    """HS10 하위 행 값 {HS10: (V, Q)}와 근거 묶음. 같은 키의 중복 행 값이 다르면 None."""
    kids = snap.children.get((partner, hs6, month), {})
    values = {}
    required = []
    for code in sorted(kids):
        pair = _unique_values(snap, kids[code])
        if pair is None:
            return None, [], f"같은 HS10 키의 행 값이 서로 다르다({code}, {month})"
        values[code] = pair
        required.append(frozenset(kids[code]))
    return values, required, ""


def expect_decomposition(snap: Snapshot, base: str, partner: str, hs6: str, month: str, baseline: str) -> Expect:
    """HS10 구성효과 분해(within_effect·mix_effect·residual). 같은 HS10 집합, 양 시점 중량 유효(모든 하위 행의 V·Q가
    있고 Q>0), 부모 합계 일치(금액 정확 일치, 중량 0.5kg×(행수+1))일 때만 계산한다(자료 계약 §11.2)."""
    now_kids, now_req, now_note = _child_values(snap, partner, hs6, month)
    old_kids, old_req, old_note = _child_values(snap, partner, hs6, baseline)
    pv1, pq1, preq1, pnote1 = level_values(snap, partner, hs6, month)
    pv0, pq0, preq0, pnote0 = level_values(snap, partner, hs6, baseline)
    required = preq1 + preq0 + now_req + old_req
    if now_kids is None or old_kids is None:
        return Expect(None, required, now_note or old_note)
    if not now_kids or not old_kids:
        return Expect(None, required, "HS10 하위 자료가 없다(분해하지 않는다)")
    if set(now_kids) != set(old_kids):
        return Expect(None, required, "두 시점의 HS10 집합이 다르다(분해하지 않는다)")
    for kids in (now_kids, old_kids):
        if any(v is None or q is None or q <= 0 for v, q in kids.values()):
            return Expect(None, required, "HS10 하위 행의 금액·중량이 유효하지 않다(분해하지 않는다)")
    for pv, pq, kids, pnote in ((pv1, pq1, now_kids, pnote1), (pv0, pq0, old_kids, pnote0)):
        if pv is None or pq is None:
            return Expect(None, required, pnote or "부모 HS6 값이 없다(분해하지 않는다)")
        if pv != sum(v for v, _ in kids.values()):
            return Expect(None, required, "부모 금액과 HS10 합이 다르다(분해하지 않는다)")
        if abs(pq - sum(q for _, q in kids.values())) > WEIGHT_TOLERANCE_PER_ROW * (len(kids) + 1):
            return Expect(None, required, "부모 중량과 HS10 합이 허용오차 밖이다(분해하지 않는다)")
    q0 = sum(q for _, q in old_kids.values())
    q1 = sum(q for _, q in now_kids.values())
    within = Fraction(0)
    mix = Fraction(0)
    for code in sorted(now_kids):
        v0, qa = old_kids[code]
        v1, qb = now_kids[code]
        u0, u1 = Fraction(v0, qa), Fraction(v1, qb)
        w0, w1 = Fraction(qa, q0), Fraction(qb, q1)
        within += (w0 + w1) / 2 * (u1 - u0)
        mix += (u0 + u1) / 2 * (w1 - w0)
    if base == "within_effect":
        return Expect(within, required, "")
    if base == "mix_effect":
        return Expect(mix, required, "")
    if pq1 == 0 or pq0 == 0:
        return Expect(None, required, "부모 중량이 0이라 잔차를 계산하지 않는다")
    return Expect(Fraction(pv1, pq1) - Fraction(pv0, pq0) - (within + mix), required, "")


def expect_hs10(snap: Snapshot, base: str, partner: str, hs6: str, hs10: str, month: str,
                baseline: str | None) -> Expect:
    """HS10 하위 지표 U@·r_U@·w@의 기대값."""
    if base == "r_U":
        now = expect_hs10(snap, "U", partner, hs6, hs10, month, None)
        before = expect_hs10(snap, "U", partner, hs6, hs10, baseline or "", None)
        required = now.required + before.required
        if now.value is None or before.value is None:
            return Expect(None, required, now.note or before.note)
        if before.value == 0:
            return Expect(None, required, "기준월 하위 단가가 0이라 변화율을 계산하지 않는다")
        return Expect((now.value / before.value - 1) * 100, required, "")
    kids, required, note = _child_values(snap, partner, hs6, month)
    if kids is None:
        return Expect(None, [], note)
    if hs10 not in kids:
        return Expect(None, required if base == "w" else [], f"{month} {hs10} 행 없음")
    if base == "U":
        v, q = kids[hs10]
        own = [frozenset(snap.children[(partner, hs6, month)][hs10])]
        if v is not None and q == 0:
            return Expect(None, own, "중량이 0이라 단가를 계산하지 않는다")
        return Expect(_ratio(v, q), own, "")
    if base == "w":
        if any(q is None for _, q in kids.values()):
            return Expect(None, required, "하위 행 중량이 없다")
        total = sum(q for _, q in kids.values())
        if total == 0:
            return Expect(None, required, "하위 행 중량 합이 0이다")
        return Expect(Fraction(kids[hs10][1], total) * 100, required, "")
    raise ValueError(base)


def expect_status(snap: Snapshot, partner: str, hs6: str, month: str,
                  hs10: str | None) -> tuple[dict[str, set[int]], str]:
    """관측 상태별 그 키의 행({상태: rowid 집합}). 관측 행이 있으면 OBSERVED 하나다. 없으면 그 달을 맡은 요청들이 남긴
    상태 행이다(자료 계약 §2.3.2 행 규칙 4, §3.4). 상대국 HS6 키는 HS6 요청과 HS4 스캔, HS10 키는 HS6 요청의 상태 행을
    본다. ALL은 itemtrade HS6·HS4 요청의 상태 행을 본다."""
    if hs10 is None:
        if partner == "ALL":
            observed = [rowid for rows in snap.children.get(("ALL", hs6, month), {}).values() for rowid in rows]
        else:
            observed = snap.parent.get((partner, hs6, month), [])
        keys = [(partner, hs6, month), (partner, hs6[:4], month)]
    else:
        observed = snap.children.get((partner, hs6, month), {}).get(hs10, [])
        keys = [(partner, hs6, month)] + ([("ALL", hs6[:4], month)] if partner == "ALL" else [])
    if observed:
        return {OBSERVED: set(observed)}, ""
    grouped = snap.status_rows(keys)
    return grouped, ("" if grouped else "관측 행도 상태 행도 없어 관측 상태를 정할 수 없다")


# ----------------------------------------------------------------------------- 근거 ID

def resolve_evidence(evidence_ids: object, snapshot_id: str, snap: Snapshot) -> tuple[set[int] | None, str]:
    """근거 ID 목록을 푼다(자료 계약 §4.4 해석 규칙 4가지). (observation rowid 집합, 문제 메모). 목록이 없거나 비었거나
    하나라도 풀리지 않으면 None이다."""
    if not isinstance(evidence_ids, list) or not evidence_ids:
        return None, "근거 ID가 없다"
    cited: set[int] = set()
    for item in evidence_ids:
        if not isinstance(item, str):
            return None, "근거 ID가 문자열이 아니다"
        parts = item.split(":")
        if len(parts) != 4 or parts[0] != "ev":
            return None, f"근거 ID 형식이 아니다({item})"
        if parts[1] != snapshot_id:
            return None, f"근거 ID의 snapshot_id가 실행 스냅샷과 다르다({item})"
        if parts[2] not in snap.tables:
            return None, f"스냅샷에 없는 테이블이다({item})"
        if not ROWID_RE.match(parts[3]) or int(parts[3]) not in snap.tables[parts[2]]:
            return None, f"그 rowid의 행이 없다({item})"
        if parts[2] == "observation":
            cited.add(int(parts[3]))
    return cited, ""


def evidence_covers(cited: set[int], required: list, snap: Snapshot) -> tuple[bool, str]:
    """풀린 행이 기대값 계산에 필요한 행 묶음을 모두 포함하는가. 총계 행은 근거가 될 수 없다."""
    usable = cited - snap.totals
    if not usable:
        return False, "총계 행만 인용했다" if cited else "관측 행을 인용하지 않았다"
    missing = [group for group in required if not (group & usable)]
    if missing:
        return False, f"기대값 계산에 필요한 원본 행 {len(missing)}묶음을 인용하지 않았다"
    return True, ""


# ----------------------------------------------------------------------------- 주장 채점

def parse_metric(metric: object) -> tuple[str, str | None] | None:
    """지표 기호를 (앞 기호, HS10 코드 또는 None)으로 나눈다. 정의하지 않은 기호면 None."""
    if not isinstance(metric, str):
        return None
    if "@" in metric:
        base, _, code = metric.partition("@")
        return (base, code) if base in HS10_BASES and HS10_RE.match(code) else None
    return (metric, None) if metric in PLAIN_BASES else None


def _metric_key(base: str, hs10: str | None) -> str:
    return base + "@" if hs10 is not None else base


def is_directional(claim_type: str, base: str) -> bool:
    """변화 주장인가(부호 있는 value와 UP·DOWN·FLAT direction을 쓰는 주장, 자료 계약 §6.2)."""
    return claim_type in ("change", "share_change", "decomposition") \
        or (claim_type == "comparison" and base in CHANGE_BASES)


def claim_record(run_id: str, report_id: str, claim_id: str, **fields: object) -> dict:
    """주장 채점 기록 한 줄(키 순서는 자료 계약 §9.2)."""
    record = {"run_id": run_id, "report_id": report_id, "claim_id": claim_id}
    defaults = {"source": SOURCE_CLAIM, "outcome": WRONG_REFERENT, "expected_value": None, "reported_value": None,
                "unit_expected": None, "unit_reported": None, "tolerance": None, "referent_resolved": False,
                "evidence_ok": False, "note": ""}
    for key in RECORD_KEYS[3:]:
        record[key] = fields.get(key, defaults[key])
    return record


class _Findings:
    """판정 순서대로 걸린 결과와 메모를 모은다. 처음 걸린 결과가 outcome이고 나머지는 note에 적는다."""

    def __init__(self):
        self.items: list[tuple[str, str]] = []
        self.notes: list[str] = []

    def fail(self, outcome: str, note: str) -> None:
        self.items.append((outcome, note))

    def outcome(self) -> str:
        return self.items[0][0] if self.items else CORRECT

    def note(self) -> str:
        return "; ".join([f"{outcome}: {note}" for outcome, note in self.items] + [n for n in self.notes if n])


def score_claim(claim: object, index: int, snap: Snapshot, run_id: str, report_id: str, snapshot_id: str) -> dict:
    """typed claim 하나를 채점해 주장 채점 기록을 돌려준다(룰북 B3-1). 해석할 수 없는 claim은 WRONG_REFERENT다."""
    if not isinstance(claim, dict):
        return claim_record(run_id, report_id, f"claims[{index}]", note="해석 불가: claim이 객체가 아니다")
    claim_id = claim.get("claim_id")
    claim_id = claim_id if isinstance(claim_id, str) and claim_id and not claim_id.startswith("prose:") \
        else f"claims[{index}]"
    reported, unit = claim.get("value"), claim.get("unit")
    fields = {"reported_value": reported if (reported is None or isinstance(reported, str) or is_number(reported))
              else None, "unit_reported": unit if isinstance(unit, str) else None}
    missing = [name for name in CLAIM_FIELDS if name not in claim]
    if missing:
        return claim_record(run_id, report_id, claim_id, **fields, note=f"해석 불가: 필드가 없다({', '.join(missing)})")
    parsed, problem = _referent_format(claim)
    if parsed is None:
        return claim_record(run_id, report_id, claim_id, **fields, note=f"{WRONG_REFERENT}: {problem}")
    claim_type = parsed[0]
    fields["unit_expected"] = None if claim_type == "data_status" else METRIC_UNITS[parsed[1]]
    if claim_type == "data_status":
        return _score_status(claim, claim_id, snap, run_id, report_id, snapshot_id, fields, parsed)
    if not (reported is None or is_number(reported)):
        return claim_record(run_id, report_id, claim_id, **fields,
                            note=f"{WRONG_REFERENT}: 해석 불가: value가 수나 null이 아니다")
    return _score_numeric(claim, claim_id, snap, run_id, report_id, snapshot_id, fields, parsed)


def _referent_format(claim: dict) -> tuple[tuple | None, str]:
    """대상 필드의 형식(해석 가능성)을 본다. 풀리면 (claim_type, 앞 기호, HS10, hs6, partner, period, baseline)."""
    claim_type, hs6, partner = claim["claim_type"], claim["hs6"], claim["partner"]
    period, baseline = claim["period"], claim["baseline_period"]
    if claim_type not in CLAIM_TYPES:
        return None, "해석 불가: claim_type이 계약 밖이다"
    parsed = parse_metric(claim["metric"])
    if parsed is None:
        return None, "해석 불가: 정의하지 않은 지표 기호다"
    base, hs10 = parsed
    if _metric_key(base, hs10) not in TYPE_METRICS[claim_type]:
        return None, f"지표 {claim['metric']}은 claim_type {claim_type}과 맞지 않다"
    if not isinstance(hs6, str) or not HS6_RE.match(hs6):
        return None, "해석 불가: hs6가 6자리 문자열이 아니다"
    if not isinstance(partner, str) or not PARTNER_RE.match(partner):
        return None, "해석 불가: partner가 국가 코드나 ALL이 아니다"
    if not isinstance(period, str) or not MONTH_RE.match(period):
        return None, "해석 불가: period가 YYYYMM이 아니다"
    if hs10 is not None and not hs10.startswith(hs6):
        return None, "HS10 코드가 hs6 아래 코드가 아니다"
    if partner == "ALL" and (base in NO_ALL_BASES or claim_type == "comparison"):
        return None, f"partner ALL로 정의하지 않는 지표다({claim['metric']}, {claim_type})"
    if is_directional(claim_type, base):
        if not isinstance(baseline, str) or not MONTH_RE.match(baseline):
            return None, "전년동월 지표인데 baseline_period가 YYYYMM이 아니다"
        if baseline != shift_month(period, -12):
            return None, "전년동월 지표의 baseline_period가 t−12가 아니다"
    elif claim_type == "data_status":
        if baseline is not None and (not isinstance(baseline, str) or not MONTH_RE.match(baseline)):
            return None, "해석 불가: baseline_period가 YYYYMM이나 null이 아니다"
        baseline = None
    elif baseline is not None:
        return None, "변화를 말하지 않는 주장에 baseline_period가 있다"
    return (claim_type, base, hs10, hs6, partner, period, baseline), ""


def _referent_exists(snap: Snapshot, base: str, hs10: str | None, hs6: str, partner: str, period: str,
                     baseline: str | None) -> str:
    """대상이 스냅샷에 있는가. 없으면 사유 문장."""
    if hs6 not in snap.hs6_codes:
        return f"스냅샷에 없는 품목이다({hs6})"
    if partner not in snap.partners:
        return f"스냅샷에 없는 상대국이다({partner})"
    for month in (period, baseline):
        if month is not None and month not in snap.months:
            return f"스냅샷 기간 밖의 달이다({month})"
    if hs10 is not None and base != STATUS_METRIC and hs10 not in snap.hs10_codes:
        return f"스냅샷에 없는 HS10 코드다({hs10})"
    return ""


def expect_numeric(snap: Snapshot, base: str, hs10: str | None, hs6: str, partner: str, period: str,
                   baseline: str | None) -> Expect:
    """수 지표의 기대값."""
    if hs10 is not None:
        return expect_hs10(snap, base, partner, hs6, hs10, period, baseline)
    if base in ("V", "Q", "U", "s"):
        return expect_level(snap, base, partner, hs6, period)
    if base in ("r_U", "d_s"):
        return expect_change(snap, base, partner, hs6, period, baseline or "")
    return expect_decomposition(snap, base, partner, hs6, period, baseline or "")


def _score_numeric(claim: dict, claim_id: str, snap: Snapshot, run_id: str, report_id: str, snapshot_id: str,
                   fields: dict, parsed: tuple) -> dict:
    claim_type, base, hs10, hs6, partner, period, baseline = parsed
    found = _Findings()
    missing_referent = _referent_exists(snap, base, hs10, hs6, partner, period, baseline)
    if missing_referent:
        found.fail(WRONG_REFERENT, missing_referent)
    if claim["unit"] != fields["unit_expected"]:
        found.fail(WRONG_UNIT, f"단위 {claim['unit']!r}는 지표 {claim['metric']}의 단위 {fields['unit_expected']}와 다르다")
    if missing_referent:
        found.notes.append("대상을 풀지 못해 값과 근거를 대조하지 않았다")
        return claim_record(run_id, report_id, claim_id, **fields, outcome=found.outcome(), note=found.note())

    expect = expect_numeric(snap, base, hs10, hs6, partner, period, baseline)
    contract_digits = METRIC_DIGITS[base]
    reported = claim["value"]
    digits = min(displayed_digits(reported), contract_digits) if reported is not None else contract_digits
    fields["tolerance"] = step_out(digits)
    if expect.value is not None:
        fields["expected_value"] = number_out(expect.value, digits)

    direction = claim["direction"]
    if direction not in DIRECTIONS:
        found.fail(WRONG_DIRECTION, f"direction {direction!r}가 계약 밖이다")
    elif not is_directional(claim_type, base):
        if direction != "NA":
            found.fail(WRONG_DIRECTION, "변화 주장이 아닌데 direction이 NA가 아니다")
    elif expect.value is not None:
        accepted = {"UP"} if expect.value > 0 else ({"DOWN"} if expect.value < 0 else {"FLAT"})
        if expect.value != 0 and round_half_up(expect.value, digits) == 0:
            accepted.add("FLAT")
        if direction not in accepted:
            found.fail(WRONG_DIRECTION, f"기대 방향은 {'·'.join(sorted(accepted))}다")

    if expect.value is None and reported is not None:
        found.fail(WRONG_VALUE, f"계산할 수 없는 대상에 값을 적었다: {expect.note or '기대값 null'}")
    elif expect.value is not None and reported is None:
        found.fail(WRONG_VALUE, "계산할 수 있는 대상을 계산 불가(null)로 적었다")
    elif expect.value is not None:
        match, _, digits_only = compare_value(expect.value, reported, contract_digits)
        if not match:
            found.fail(WRONG_VALUE, "기대값과 다르다" + (" " + DIGITS_ONLY_MARK if digits_only else ""))
    elif expect.note:
        found.notes.append(expect.note)

    cited, problem = resolve_evidence(claim["evidence_ids"], snapshot_id, snap)
    evidence_ok = False
    if cited is not None:
        evidence_ok, problem = evidence_covers(cited, expect.required, snap)
    if not evidence_ok:
        found.fail(UNSUPPORTED, problem)
    return claim_record(run_id, report_id, claim_id, **fields, outcome=found.outcome(), referent_resolved=True,
                        evidence_ok=evidence_ok, note=found.note())


def _score_status(claim: dict, claim_id: str, snap: Snapshot, run_id: str, report_id: str, snapshot_id: str,
                  fields: dict, parsed: tuple) -> dict:
    """data_status 주장: 수집 계획과 먼저 대조한 뒤 상태 값과 근거를 본다(룰북 B3-1)."""
    _, base, hs10, hs6, partner, period, _ = parsed
    found = _Findings()
    reported = claim["value"]
    if snap.in_plan(partner, hs6, period):
        missing_referent = _referent_exists(snap, base, hs10, hs6, partner, period, None)
        if missing_referent:
            found.fail(WRONG_REFERENT, missing_referent)
            return claim_record(run_id, report_id, claim_id, **fields, outcome=found.outcome(), note=found.note())
        by_status, status_note = expect_status(snap, partner, hs6, period, hs10)
    else:
        by_status = {NOT_COLLECTED: set()}
        status_note = "수집 계획 밖 키라 대상 판정 전에 계획과 대조했다(대상 오류 아님)"
    expected = sorted(by_status)
    if isinstance(reported, str) and reported in by_status:
        fields["expected_value"] = reported
    elif expected:
        fields["expected_value"] = "|".join(expected)
    if claim["unit"] is not None:
        found.fail(WRONG_UNIT, "data_status 주장의 unit은 null이어야 한다")
    if claim["direction"] != "NA":
        found.fail(WRONG_DIRECTION, "data_status 주장의 direction은 NA여야 한다")
    if not isinstance(reported, str) or reported not in OBS_STATUSES:
        found.fail(WRONG_VALUE, "관측 상태 코드가 아니다")
    elif not by_status:
        found.fail(WRONG_VALUE, status_note)
    elif reported not in by_status:
        found.fail(WRONG_VALUE, f"기대 관측 상태는 {'|'.join(expected)}다")
    if status_note and by_status:
        found.notes.append(status_note)
    cited, problem = resolve_evidence(claim["evidence_ids"], snapshot_id, snap)
    evidence_ok = False
    if cited is not None:
        rows = by_status.get(reported, set()) if isinstance(reported, str) else set()
        if rows:
            evidence_ok, problem = evidence_covers(cited, [frozenset(rows)], snap)
            problem = "" if evidence_ok else "그 키의 상태 행을 인용하지 않았다"
        else:
            problem = "인용할 그 키의 상태 행이 없다"
    if not evidence_ok:
        found.fail(UNSUPPORTED, problem)
    return claim_record(run_id, report_id, claim_id, **fields, outcome=found.outcome(), referent_resolved=True,
                        evidence_ok=evidence_ok, note=found.note())


def score_report_claims(report: dict, snap: Snapshot, run_id: str, snapshot_id: str) -> list[dict]:
    """보고서 하나의 typed claim을 모두 채점한다. 보고서의 claims가 목록이 아니면 입력 오류다."""
    claims = report.get("claims")
    if not isinstance(claims, list):
        raise ScorerInputError("보고서의 claims가 목록이 아니다")
    report_id = report.get("report_id") if isinstance(report.get("report_id"), str) else ""
    return [score_claim(claim, i, snap, run_id, report_id, snapshot_id) for i, claim in enumerate(claims)]


def run(inp: object) -> object:
    """진입 함수. 입력: {"snapshot": {"snapshot_id", "tables": {테이블: [행(rowid 포함)]}}, "reports": [보고서 객체]}.
    출력: 보고서 순서·claim 순서대로의 주장 채점 기록(source=claim) 목록. 실행 스냅샷은 snapshot.snapshot_id다."""
    if not isinstance(inp, dict) or not isinstance(inp.get("reports"), list):
        raise ScorerInputError("입력은 snapshot과 reports를 가진 객체여야 한다")
    snap = Snapshot.from_json(inp.get("snapshot"))
    records: list[dict] = []
    for report in inp["reports"]:
        if not isinstance(report, dict) or not isinstance(report.get("run_id"), str):
            raise ScorerInputError("보고서는 run_id를 가진 객체여야 한다")
        records += score_report_claims(report, snap, report["run_id"], snap.snapshot_id)
    return records
