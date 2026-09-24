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
- 수집 계획과 분석 범위는 스냅샷 메타의 수집 설정(`collection_plan`: hs6·partners·hs4_scan·period 등)과 비교국 표
  (`peer_group`)의 계획 밖 비교국에서 정한다(자료 계약 §2.3.2 행 규칙 7). 행에 나온 코드·달로 범위를 짐작하지 않는다.
- 원천 규칙(자료 계약 §2.3.2 행 규칙 2~6, §11.2): 상대국 값은 부모 HS6 행(수신 기록의 요청이 HS4 스캔인 `nitemtrade`
  HS6 월 행), HS10 하위 행은 그 HS6 요청이 돌려준 행, 점유율 분모는 그 HS6 아래 ALL HS10 월 행 합(같은 키의 중복 행은
  동등하며 값이 다르면 계산하지 않는다). 총계 행(month가 RAW:로 시작)은 근거가 될 수 없다. 승격된 달(그 키를 맡은 요청의
  상태 행이 모두 CONFIRMED_NO_TRADE)은 V·Q를 0으로 다룬다.
- 기대값이 null인 대상도 근거가 필요하다. 빠진 값은 그 키 자신과 그 키를 맡은 요청의 상태 행 묶음 가운데 하나를 인용해야
  한다(다른 상대국·다른 달의 행은 뒷받침하지 않는다, 자료 계약 §4.4). 인용할 상태 행이 없으면 UNSUPPORTED다.
- 근거 ID `ev:<snapshot_id>:<table>:<rowid>`의 rowid는 앞자리 0이 없는 19자리 이하 양의 정수(2^63−1 이하)로만 푼다.
  형식 검사는 모두 문자열 전체 대조(fullmatch)와 ASCII 숫자로 한다(끝 줄바꿈·유니코드 숫자를 받지 않는다). 런타임 자료
  접근층·검증기와 같은 해석이다(자료 계약 §4.4).
- comparison 주장은 실행 기록의 grouping_version이 가리키는 스냅샷 비교국 표의 비교집합(대상국 기준, 가장 좁은 범위
  hs6 → hs4 → hs2)에 든 상대국이어야 한다(룰북 B3-1). 사례 문맥(대상국·품목·grouping_version)이 없으면 풀지 못한다.
- 믿지 않는 입력(샌드박스가 쓴 보고서)이 채점을 멈추거나 끝나지 않게 하지 않도록, 수로 받는 값의 크기(유효 숫자 100자리,
  10의 지수 ±100)와 보고서 하나의 claim 수(MAX_CLAIMS_PER_REPORT)에 상한을 둔다. 상한 밖 수는 해석할 수 없는 값이다.
- 이 파일은 다른 채점기 단위가 함께 쓰는 수 비교 규칙(값 비교, 자릿수)과 JSON 도우미를 둔다. 다른 단위 파일은 이
  파일을 import하고, 이 파일은 다른 채점기 단위를 import하지 않는다(순환 import 방지).

잠정 해석(결정 기록 20260925-*-data-decision-dt8-scorer.md)
- 계획 안 키인데 관측 행도 상태 행도 없는 경우(성공한 요청의 응답에 그 키만 없음)는 UNRESOLVED_ZERO로 보고 인용할 상태
  행이 없다고 본다(absent_key_status). 런타임 자료 접근층은 이런 키를 돌려주지 않으므로 freeform 주장에서만 닿는다.

알려진 빈칸(F1 전 보완 목록에 적는다)
- 승격 규칙(UNRESOLVED_ZERO → CONFIRMED_NO_TRADE)의 독립 구현: policy_v1 승인 전이라 규칙이 없다. 지금은 스냅샷 행의
  observation_status를 그대로 쓴다(룰북 B3-1 "data_status 주장" 3번은 승인 뒤 보완).
- 부모-하위 중량 대조 허용오차: 자료 계약 §11.1의 출발값 0.5kg×(행수+1)을 쓴다. policy_v1 승인 값으로 바꾼다.
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

ALL = "ALL"
IMPORT = "import"
NITEMTRADE = "nitemtrade"  # 국가별 품목 조회(HS4 스캔 → HS6 행, HS6 조회 → HS10 행)
ITEMTRADE = "itemtrade"    # 품목별 전체국가 조회(HS4·HS6 조회 모두 HS10 행)
RECEIPT_OK = "OK"

# 지표 기호의 단위(자료 계약 §11.2)와 표시 자릿수(§11.3). w는 w@<HS10>, U@·r_U@는 앞 기호를 따른다.
METRIC_UNITS = {"V": "USD", "Q": "kg", "U": "USD/kg", "r_U": "%", "s": "%", "d_s": "pp", "within_effect": "USD/kg",
                "mix_effect": "USD/kg", "residual": "USD/kg", "w": "%"}
METRIC_DIGITS = {"V": 0, "Q": 0, "U": 2, "r_U": 1, "s": 1, "d_s": 1, "within_effect": 2, "mix_effect": 2,
                 "residual": 2, "w": 1}
STATUS_METRIC = "observation_status"
HS10_BASES = ("U", "r_U", "w", STATUS_METRIC)  # @<HS10 코드>를 붙일 수 있는 기호(자료 계약 §6.2)
PLAIN_BASES = frozenset(set(METRIC_UNITS) - {"w"} | {STATUS_METRIC})  # @ 없이 쓰는 기호
DECOMPOSITION_BASES = ("within_effect", "mix_effect", "residual")

# claim_type마다 쓸 수 있는 기호(자료 계약 §6.2). comparison은 "r_U, d_s 등"을 비교국 한 나라의 값으로 읽는다.
TYPE_METRICS = {
    "value": frozenset({"V", "Q", "U", "U@", "w@"}),
    "change": frozenset({"r_U", "r_U@"}),
    "share": frozenset({"s"}),
    "share_change": frozenset({"d_s"}),
    "decomposition": frozenset(DECOMPOSITION_BASES),
    "comparison": frozenset({"V", "Q", "U", "s", "r_U", "d_s"}),
    "data_status": frozenset({STATUS_METRIC, STATUS_METRIC + "@"}),
}
CHANGE_BASES = frozenset({"r_U", "d_s", "within_effect", "mix_effect", "residual"})  # 기준월 t−12가 필요한 기호
NO_ALL_BASES = frozenset({"s", "d_s", "within_effect", "mix_effect", "residual"})  # partner ALL로 정의하지 않는 기호
LEVEL_BASES = frozenset({"V", "Q", "U", "s", "w"})  # 수준 기호(산문 PT-8의 짝 규칙이 보는 "수준 claim")

# 룰북 B3-1 "민감도 보고": 보고값과 반올림 전 기대값의 차가 비교 자리 1단위 미만인 WRONG_VALUE. 요약(단위 C4)이 이
# 표식이 든 기록을 센다. 기록 키가 고정(자료 계약 §9.2)이라 메모에 이 글자를 그대로 넣는다.
DIGITS_ONLY_MARK = "[자릿수만 다른 WRONG_VALUE]"

# 형식 정규식은 모두 fullmatch로 쓴다(끝 줄바꿈을 받지 않는다). 숫자는 ASCII [0-9]만 받는다.
MONTH_RE = re.compile(r"([0-9]{4})(0[1-9]|1[0-2])")
HS4_RE = re.compile(r"[0-9]{4}")
HS6_RE = re.compile(r"[0-9]{6}")
HS10_RE = re.compile(r"[0-9]{10}")
COUNTRY_RE = re.compile(r"[A-Z]{2}")
PARTNER_RE = re.compile(r"ALL|[A-Z]{2}")
ROWID_RE = re.compile(r"[1-9][0-9]{0,18}")  # 앞자리 0이 없는 19자리 이하 양의 정수(자료 계약 §4.4)
MAX_ROWID = 2 ** 63 - 1                     # SQLite rowid 상한
TABLE_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# 수로 받는 값의 상한(믿지 않는 입력의 계산 비용을 막는다): 유효 숫자 자리수, 10의 지수. 계약 값(USD·kg 정수, 백분율)보다
# 충분히 크다. 정수는 절댓값이 10^NUMBER_LIMIT_DIGITS 미만이어야 한다.
NUMBER_LIMIT_DIGITS = 100
NUMBER_LIMIT = 10 ** NUMBER_LIMIT_DIGITS
MAX_CLAIMS_PER_REPORT = 300  # 보고서 하나의 typed claim 상한(잠정). 넘으면 채점할 수 없는 보고서다
MAX_PLAN_MONTHS = 1200       # 수집 계획 기간 상한(100년)

# 부모 HS6 행과 HS10 하위 행 합의 중량 대조 허용오차: 0.5kg × (하위 행 수 + 1)(자료 계약 §11.1 출발값).
WEIGHT_TOLERANCE_PER_ROW = Fraction(1, 2)


class ScorerInputError(Exception):
    """채점기 입력(실행 기록, 보고서, 정답표, 실행 조건 입력 파일, 스냅샷)이 약속한 형식이 아니다."""


# ----------------------------------------------------------------------------- 수와 자릿수

def is_number(value: object) -> bool:
    """JSON 수로 읽은 값인가(bool 제외, Decimal은 유한값만). 크기 상한 밖의 수는 수로 받지 않는다."""
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return -NUMBER_LIMIT < value < NUMBER_LIMIT
    if not isinstance(value, Decimal) or not value.is_finite():
        return False
    _, digits, exponent = value.as_tuple()
    return len(digits) <= NUMBER_LIMIT_DIGITS and -NUMBER_LIMIT_DIGITS <= exponent \
        and value.adjusted() < NUMBER_LIMIT_DIGITS


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


def months_between(start: str, end: str) -> list[str]:
    """start부터 end까지(둘 다 포함)의 YYYYMM 목록."""
    months = []
    month = start
    while month <= end:
        months.append(month)
        if len(months) > MAX_PLAN_MONTHS:
            raise ScorerInputError("수집 계획 기간이 너무 길다")
        month = shift_month(month, 1)
    return months


def _show(value: object) -> str:
    """메모에 적을 믿지 않는 값. 짧은 글자·수·null은 그대로, 그 밖(목록·객체 등)은 형식 이름만 적는다."""
    if value is None or isinstance(value, bool):
        return repr(value)
    if isinstance(value, str):
        return repr(value[:40])
    if is_number(value):
        return str(value)
    return f"<{type(value).__name__}>"


# ----------------------------------------------------------------------------- JSON 읽기·쓰기

def _refuse_constant(name: str) -> object:
    raise ValueError(f"JSON 상수 {name}은 쓰지 않는다")


def loads_json(text: str) -> object:
    """JSON 문서를 읽는다. 소수는 Decimal로 원문 표기(끝자리 0)를 보존하고 NaN·Infinity는 거부한다. 아주 깊이 중첩한
    문서는 RecursionError를 낸다(부르는 쪽이 읽지 못한 입력으로 다룬다)."""
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


# ----------------------------------------------------------------------------- 수집 계획

def _code_list(value: object, pattern: re.Pattern, what: str, required: bool = False) -> tuple[str, ...]:
    if value is None and not required:
        return ()
    if not isinstance(value, list) or not all(isinstance(v, str) and pattern.fullmatch(v) for v in value) \
            or (required and not value):
        raise ScorerInputError(f"스냅샷 메타의 collection_plan.{what} 형식이 맞지 않다")
    return tuple(value)


class CollectionPlan:
    """스냅샷 메타의 수집 설정(collection_plan)에서 읽은 수집 계획과 분석 범위(자료 계약 §2.3.1·§2.3.2 행 규칙 7).

    요청 목록은 수집기의 계획 규칙(HS4 스캔·HS6 조회 × 상대국 × 기간, 분모 조회, HS10 직접 조회)을 따로 적은 것이다.
    기간 조각(chunk)은 기간을 나눌 뿐이라 키가 계획에 드는지에는 영향이 없다."""

    def __init__(self, config: object, period: object = None):
        if not isinstance(config, dict):
            raise ScorerInputError("스냅샷 메타의 collection_plan이 객체가 아니다")
        period = period if isinstance(period, dict) else config.get("period")
        start = period.get("start") if isinstance(period, dict) else None
        end = period.get("end") if isinstance(period, dict) else None
        if not (isinstance(start, str) and isinstance(end, str) and MONTH_RE.fullmatch(start)
                and MONTH_RE.fullmatch(end) and start <= end):
            raise ScorerInputError("스냅샷 메타의 수집 기간(period.start·end) 형식이 맞지 않다")
        self.months = tuple(months_between(start, end))
        self.month_set = frozenset(self.months)
        self.hs6 = frozenset(_code_list(config.get("hs6"), HS6_RE, "hs6", required=True))
        self.partners = frozenset(_code_list(config.get("partners"), COUNTRY_RE, "partners", required=True))
        self.hs4_scan = frozenset(_code_list(config.get("hs4_scan"), HS4_RE, "hs4_scan"))
        denominator = config.get("collect_total_denominator", True)
        if not isinstance(denominator, bool):
            raise ScorerInputError("스냅샷 메타의 collection_plan.collect_total_denominator가 참·거짓이 아니다")
        self.denominator = denominator
        self.hs10_specs: list[tuple[frozenset, frozenset, frozenset]] = []
        specs = config.get("hs10") or []
        if not isinstance(specs, list):
            raise ScorerInputError("스냅샷 메타의 collection_plan.hs10 형식이 맞지 않다")
        for spec in specs:
            months = spec.get("months") if isinstance(spec, dict) else None
            if not isinstance(months, list) or not months \
                    or not all(isinstance(m, str) and MONTH_RE.fullmatch(m) for m in months):
                raise ScorerInputError("스냅샷 메타의 collection_plan.hs10 형식이 맞지 않다")
            codes = _code_list(spec.get("codes"), HS10_RE, "hs10.codes", required=True)
            partners = _code_list(spec.get("partners"), COUNTRY_RE, "hs10.partners") if "partners" in spec \
                else tuple(self.partners)
            self.hs10_specs.append((frozenset(codes), frozenset(partners),
                                    frozenset(months_between(min(months), max(months)))))

    def covering(self, partner: str, code: str, month: str) -> list[tuple[str, str, str]]:
        """그 키(상대국, HS6 또는 HS10 코드, 월)를 맡은 계획 요청 목록 [(엔드포인트, hsSgn, 상대국)]. 비면 계획 밖 키다.

        - 상대국 HS6 키: HS4 스캔(부모 HS6 행의 원천)과 그 HS6 조회
        - 상대국 HS10 키: 그 HS6 조회(HS10 하위 행의 원천)와 HS10 직접 조회
        - ALL 키: 분모 조회(itemtrade)의 HS4·HS6 요청(둘 다 HS10 행을 준다)"""
        out: list[tuple[str, str, str]] = []
        if partner == ALL:
            if self.denominator and month in self.month_set:
                if code[:4] in self.hs4_scan:
                    out.append((ITEMTRADE, code[:4], ALL))
                if code[:6] in self.hs6:
                    out.append((ITEMTRADE, code[:6], ALL))
            return out
        if partner in self.partners and month in self.month_set:
            if len(code) == 6:
                if code[:4] in self.hs4_scan:
                    out.append((NITEMTRADE, code[:4], partner))
                if code in self.hs6:
                    out.append((NITEMTRADE, code, partner))
            elif code[:6] in self.hs6:
                out.append((NITEMTRADE, code[:6], partner))
        if len(code) == 10:
            for codes, partners, months in self.hs10_specs:
                if code in codes and partner in partners and month in months:
                    out.append((NITEMTRADE, code, partner))
        return out


# ----------------------------------------------------------------------------- 스냅샷 색인

def _int_or_none(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def status_keys(partner: str, code: str, month: str) -> list[tuple[str, str, str]]:
    """그 키의 관측 상태를 보여 주는 상태 행의 키(상대국, HS 코드, 월): 그 키 자신과 그 키를 맡은 요청의 코드.

    수집기는 상태 행을 요청 코드 자릿수로 쓴다. 상대국 HS6 키는 HS6 자신과 HS4 스캔, 상대국 HS10 키는 HS10 자신과
    HS6 조회, ALL HS10 키는 HS10 자신과 HS6·HS4 요청이다(검증기 결정 MT3 ⑨와 같은 해석). ALL HS6 키는 HS6·HS4다."""
    if len(code) == 10:
        keys = [(partner, code, month), (partner, code[:6], month)]
        if partner == ALL:
            keys.append((ALL, code[:4], month))
        return keys
    return [(partner, code, month), (partner, code[:4], month)]


class Snapshot:
    """스냅샷 행의 읽기 전용 색인. tables는 테이블 이름 → {rowid: 행(열 이름 → 값)}이다.

    - snapshot_meta(key, value=JSON 글자)에서 수집 계획(collection_plan)과 기간을 읽는다. 없으면 입력 오류다.
    - collection_receipt의 params_json으로 행마다 원천 요청(엔드포인트, hsSgn)을 가린다(자료 계약 §2.3.2 행 규칙 4).
    - peer_group에서 비교집합과 계획 밖 비교국을 읽는다(룰북 B3-1 "comparison 주장").
    - 지표는 flow가 import인 월 행만 쓴다(행 규칙 2). 총계 행(month가 RAW:로 시작)은 색인에 넣지 않고 totals에만 적는다."""

    def __init__(self, snapshot_id: str, tables: dict[str, dict[int, dict]]):
        self.snapshot_id = snapshot_id
        self.tables = tables
        self.meta = _read_meta(tables.get("snapshot_meta", {}))
        if "collection_plan" not in self.meta:
            raise ScorerInputError("스냅샷 메타에 collection_plan이 없다(스냅샷 빌드 파일이 아니다)")
        self.plan = CollectionPlan(self.meta["collection_plan"], self.meta.get("period"))
        self.request_source: dict[object, tuple[object, object]] = {}   # request_id → (엔드포인트, hsSgn)
        self.receipts: dict[tuple, list[tuple]] = defaultdict(list)     # (엔드포인트, hsSgn, 상대국) → [(시작, 끝, 상태)]
        for row in tables.get("collection_receipt", {}).values():
            try:
                params = json.loads(row.get("params_json") or "")
            except (TypeError, ValueError) as exc:
                raise ScorerInputError("수신 기록의 params_json이 JSON 객체가 아니다") from exc
            if not isinstance(params, dict):
                raise ScorerInputError("수신 기록의 params_json이 JSON 객체가 아니다")
            source = (row.get("endpoint"), params.get("hsSgn"))
            self.request_source[row.get("request_id")] = source
            self.receipts[source + (params.get("cntyCd", ALL),)].append(
                (params.get("strtYymm"), params.get("endYymm"), row.get("status")))
        self.peer_sets: dict[tuple, set[str]] = defaultdict(set)  # (대상국, grouping_version, scope_type, scope_id)
        peer_ids: set[str] = set()
        for row in tables.get("peer_group", {}).values():
            peer = row.get("peer_id")
            key = (row.get("entity_id"), row.get("grouping_version"), row.get("scope_type"), row.get("scope_id"))
            if isinstance(peer, str) and all(isinstance(k, str) for k in key):
                self.peer_sets[key].add(peer)
                peer_ids.add(peer)
        self.peer_partners = frozenset(peer_ids - self.plan.partners - {ALL})  # 비교국 표가 가리키는 계획 밖 국가
        self.scope_partners = self.plan.partners | self.peer_partners | {ALL}
        self.parent: dict[tuple, list[int]] = defaultdict(list)                # (상대국, HS6, 월) → OBSERVED 부모 HS6 행
        self.children: dict[tuple, dict[str, list[int]]] = defaultdict(dict)   # (상대국, HS6, 월) → HS10 → 행들
        self.status: dict[tuple, list[int]] = defaultdict(list)                # (상대국, HS 코드, 월) → 상태 행
        self.hs_codes: set[str] = set()
        self.hs10_codes: set[str] = set()
        self.totals: set[int] = set()
        for rowid, row in tables.get("observation", {}).items():
            hs = str(row.get("hs_code") or "")
            partner = str(row.get("partner_code") or "")
            month = str(row.get("month") or "")
            self.hs_codes.add(hs)
            if month.startswith("RAW:"):
                self.totals.add(rowid)
                continue
            if not MONTH_RE.fullmatch(month) or row.get("flow") != IMPORT:
                continue
            status = row.get("observation_status")
            if status == OBSERVED:
                source = self.request_source.get(row.get("request_id"))
                if HS6_RE.fullmatch(hs) and partner != ALL and source == (NITEMTRADE, hs[:4]):
                    self.parent[(partner, hs, month)].append(rowid)
                elif HS10_RE.fullmatch(hs) and (partner == ALL or source == (NITEMTRADE, hs[:6])):
                    self.children[(partner, hs[:6], month)].setdefault(hs, []).append(rowid)
                    self.hs10_codes.add(hs)
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
            if not TABLE_RE.fullmatch(name) or not isinstance(rows, list):
                raise ScorerInputError("snapshot.tables의 형식이 맞지 않다")
            table: dict[int, dict] = {}
            for row in rows:
                rowid = row.get("rowid") if isinstance(row, dict) else None
                if not isinstance(rowid, int) or isinstance(rowid, bool) or not 0 < rowid <= MAX_ROWID \
                        or rowid in table:
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

    def status_group(self, keys: list[tuple]) -> frozenset[int]:
        """여러 키의 상태 행 전체(빠진 값의 근거 묶음. 이 가운데 하나를 인용하면 된다)."""
        return frozenset(rowid for key in keys for rowid in self.status.get(key, []))

    def receipt_ok(self, request: tuple[str, str, str], month: str) -> bool:
        """계획 요청(엔드포인트, hsSgn, 상대국)이 그 달을 맡은 조각에서 성공(OK)했는가(수신 기록)."""
        return any(isinstance(start, str) and isinstance(end, str) and start <= month <= end and status == RECEIPT_OK
                   for start, end, status in self.receipts.get(request, []))

    def comparison_set(self, target: str, hs6: str, grouping_version: str) -> frozenset[str] | None:
        """대상국의 비교집합: 비교국 표에서 grouping_version이 같고 가장 좁은 범위(hs6 → hs4 → hs2)에 행이 있는 것."""
        for scope_type, scope_id in (("hs6", hs6), ("hs4", hs6[:4]), ("hs2", hs6[:2])):
            peers = self.peer_sets.get((target, grouping_version, scope_type, scope_id))
            if peers:
                return frozenset(peers)
        return None


def _read_meta(rows: dict[int, dict]) -> dict[str, object]:
    meta: dict[str, object] = {}
    for row in rows.values():
        key, value = row.get("key"), row.get("value")
        if not isinstance(key, str) or not isinstance(value, str):
            raise ScorerInputError("스냅샷 메타 행은 key와 JSON 글자 value를 가진다")
        try:
            meta[key] = loads_json(value)
        except (ValueError, RecursionError) as exc:
            raise ScorerInputError(f"스냅샷 메타 {key}의 값이 JSON이 아니다") from exc
    return meta


# ----------------------------------------------------------------------------- 기대값 계산

class Expect:
    """기대값 하나. value는 Fraction(수) 또는 None(계산하지 않는 대상)이다. required는 근거가 모두 포함해야 하는 원본 행
    묶음 목록이고, 묶음 하나는 서로 동등한 행(또는 같은 키의 상태 행)의 rowid 집합이다(그중 어느 행을 인용해도 된다).
    빈 묶음은 인용할 행이 없다는 뜻이라 어떤 근거로도 채우지 못한다."""

    def __init__(self, value: Fraction | None = None, required: list | None = None, note: str = ""):
        self.value = value
        self.required = required or []
        self.note = note


def _unique_values(snap: Snapshot, rowids: list[int]) -> tuple[int | None, int | None] | None:
    """동등해야 하는 행들의 (V, Q). 값이 서로 다르면 None."""
    values = {snap.values_of(rowid) for rowid in rowids}
    return values.pop() if len(values) == 1 else None


def _missing(snap: Snapshot, keys: list[tuple], what: str) -> tuple:
    """값 행이 없는 키: 그 키를 맡은 요청의 상태 행이 모두 CONFIRMED_NO_TRADE면 V·Q 0(승격된 달, 자료 계약 §3.4),
    아니면 null. 어느 쪽이든 근거 묶음은 그 상태 행들이다(없으면 빈 묶음)."""
    grouped = snap.status_rows(keys)
    group = snap.status_group(keys)
    if grouped and set(grouped) == {CONFIRMED_NO_TRADE}:
        return 0, 0, [group], "승격된 달(CONFIRMED_NO_TRADE)은 V·Q를 0으로 다룬다"
    statuses = ", ".join(sorted(grouped)) if grouped else "상태 행 없음"
    return None, None, [group], f"{what} 없음({statuses})"


def level_values(snap: Snapshot, partner: str, hs6: str, month: str) -> tuple:
    """(V, Q, 근거 묶음, 메모). 상대국은 부모 HS6 행, ALL은 HS10 행 합(중복 제거). 승격된 달은 V·Q가 0이다."""
    if partner == ALL:
        return world_values(snap, hs6, month)
    rows = snap.parent.get((partner, hs6, month), [])
    if rows:
        pair = _unique_values(snap, rows)
        if pair is None:
            return None, None, [frozenset(rows)], "같은 키의 부모 HS6 행 값이 서로 다르다"
        return pair[0], pair[1], [frozenset(rows)], ""
    return _missing(snap, status_keys(partner, hs6, month), f"{month} 부모 HS6 행")


def world_values(snap: Snapshot, hs6: str, month: str) -> tuple:
    """전체국가(ALL) HS6 월 값: 그 HS6 아래 ALL HS10 월 행 합. 같은 HS10 키의 중복 행은 동등하고 값이 다르면 계산하지
    않는다(자료 계약 §2.3.2 행 규칙 5·6)."""
    kids = snap.children.get((ALL, hs6, month), {})
    if not kids:
        return _missing(snap, status_keys(ALL, hs6, month), f"{month} ALL HS10 행")
    total_v: int | None = 0
    total_q: int | None = 0
    required = [frozenset(kids[code]) for code in sorted(kids)]
    for code in sorted(kids):
        pair = _unique_values(snap, kids[code])
        if pair is None:
            return None, None, required, f"ALL 중복 행 값이 서로 다르다({code}, {month})"
        v, q = pair
        total_v = None if (total_v is None or v is None) else total_v + v
        total_q = None if (total_q is None or q is None) else total_q + q
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
    """HS10 하위 행 값 {HS10: (V, Q)}와 근거 묶음. 하위 행이 하나도 없으면 빈 사전과 그 HS6 조회(ALL이면 HS4 요청도)의
    상태 행 묶음. 같은 키의 중복 행 값이 다르면 None."""
    kids = snap.children.get((partner, hs6, month), {})
    if not kids:
        keys = [(partner, hs6, month)] + ([(ALL, hs6[:4], month)] if partner == ALL else [])
        statuses = ", ".join(sorted(snap.status_rows(keys))) or "상태 행 없음"
        return {}, [snap.status_group(keys)], f"{month} HS10 하위 자료 없음({statuses})"
    values = {}
    required = [frozenset(kids[code]) for code in sorted(kids)]
    for code in sorted(kids):
        pair = _unique_values(snap, kids[code])
        if pair is None:
            return None, required, f"같은 HS10 키의 행 값이 서로 다르다({code}, {month})"
        values[code] = pair
    return values, required, ""


def expect_decomposition(snap: Snapshot, base: str, partner: str, hs6: str, month: str, baseline: str) -> Expect:
    """HS10 구성효과 분해(within_effect·mix_effect·residual). 양 시점 부모 중량이 0이 아니고(DT2 결정 ⑫: 한 시점이라도
    0이면 셋 모두 null), 같은 HS10 집합, 양 시점 중량 유효(모든 하위 행의 V·Q가 있고 Q>0), 부모 합계 일치(금액 정확 일치,
    중량 0.5kg×(행수+1))일 때만 계산한다(자료 계약 §11.2)."""
    now_kids, now_req, now_note = _child_values(snap, partner, hs6, month)
    old_kids, old_req, old_note = _child_values(snap, partner, hs6, baseline)
    pv1, pq1, preq1, pnote1 = level_values(snap, partner, hs6, month)
    pv0, pq0, preq0, pnote0 = level_values(snap, partner, hs6, baseline)
    required = preq1 + preq0 + now_req + old_req
    for pv, pq, pnote in ((pv1, pq1, pnote1), (pv0, pq0, pnote0)):
        if pv is None or pq is None:
            return Expect(None, required, pnote or "부모 HS6 값이 없다(분해하지 않는다)")
    if pq1 == 0 or pq0 == 0:
        return Expect(None, required, "부모 중량이 0인 시점이 있어 분해하지 않는다(DT2 결정 ⑫)")
    if now_kids is None or old_kids is None:
        return Expect(None, required, now_note or old_note)
    if not now_kids or not old_kids:
        return Expect(None, required, now_note or old_note or "HS10 하위 자료가 없다(분해하지 않는다)")
    if set(now_kids) != set(old_kids):
        return Expect(None, required, "두 시점의 HS10 집합이 다르다(분해하지 않는다)")
    for kids in (now_kids, old_kids):
        if any(v is None or q is None or q <= 0 for v, q in kids.values()):
            return Expect(None, required, "HS10 하위 행의 금액·중량이 유효하지 않다(분해하지 않는다)")
    for pv, pq, kids in ((pv1, pq1, now_kids), (pv0, pq0, old_kids)):
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
    return Expect(Fraction(pv1, pq1) - Fraction(pv0, pq0) - (within + mix), required, "")


def expect_hs10(snap: Snapshot, base: str, partner: str, hs6: str, hs10: str, month: str,
                baseline: str | None) -> Expect:
    """HS10 하위 지표 U@·r_U@·w@의 기대값. 그 코드의 행이 없는 달은 null이고, 근거는 그 코드와 그 코드를 맡은 요청의
    상태 행 묶음이다."""
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
        return Expect(None, required, note)
    if hs10 not in kids:
        missing = [snap.status_group(status_keys(partner, hs10, month))]
        return Expect(None, (required if base == "w" and kids else []) + missing, note or f"{month} {hs10} 행 없음")
    own = [frozenset(snap.children[(partner, hs6, month)][hs10])]
    if base == "U":
        v, q = kids[hs10]
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
    """계획 안 키의 관측 상태별 그 키의 행({상태: rowid 집합}). 값 행이 있으면 OBSERVED 하나다(상대국 HS6 키는 부모 HS6
    행, ALL HS6 키는 그 HS6 아래 ALL HS10 행, HS10 키는 그 코드의 행). 없으면 그 키 자신과 그 키를 맡은 요청의 상태 행
    이다(자료 계약 §2.3.2 행 규칙 4, §3.4). 부모 HS6 행이 있으면 같은 키의 HS6 조회 상태 행은 HS10 하위 자료의 상태라
    HS6 수준 상태가 아니다. CONFIRMED_NO_TRADE는 그 키의 상태 행이 모두 승격된 행일 때만 받는다."""
    code = hs10 or hs6
    if hs10 is None:
        if partner == ALL:
            observed = [rowid for rows in snap.children.get((ALL, hs6, month), {}).values() for rowid in rows]
        else:
            observed = snap.parent.get((partner, hs6, month), [])
    else:
        observed = snap.children.get((partner, hs6, month), {}).get(hs10, [])
    if observed:
        return {OBSERVED: set(observed)}, ""
    grouped = snap.status_rows(status_keys(partner, code, month))
    if CONFIRMED_NO_TRADE in grouped and len(grouped) > 1:
        grouped.pop(CONFIRMED_NO_TRADE)
    if grouped:
        return grouped, ""
    return absent_key_status(snap, partner, code, month)


def absent_key_status(snap: Snapshot, partner: str, code: str, month: str) -> tuple[dict[str, set[int]], str]:
    """[잠정] 계획 안 키인데 값 행도 상태 행도 없다. 그 키를 맡은 요청 가운데 그 달에 성공(OK)한 것이 있으면 응답에 그 키만
    없는 것이라 UNRESOLVED_ZERO로 보되, 수집기가 상태 행을 요청 코드 자릿수로만 쓰므로 인용할 상태 행은 없다(주장하면
    UNSUPPORTED). 성공한 요청도 없으면 관측 상태를 정할 수 없다(빌드가 만들지 않는 모양)."""
    if any(snap.receipt_ok(request, month) for request in snap.plan.covering(partner, code, month)):
        return {UNRESOLVED_ZERO: set()}, ("성공한 요청의 응답에 이 키의 행이 없어 UNRESOLVED_ZERO로 본다(잠정 해석). "
                                           "인용할 상태 행은 없다")
    return {}, "관측 행도 상태 행도 없어 관측 상태를 정할 수 없다"


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
            return None, f"근거 ID 형식이 아니다({_show(item)})"
        if parts[1] != snapshot_id:
            return None, f"근거 ID의 snapshot_id가 실행 스냅샷과 다르다({_show(item)})"
        if parts[2] not in snap.tables:
            return None, f"스냅샷에 없는 테이블이다({_show(item)})"
        rowid = int(parts[3]) if ROWID_RE.fullmatch(parts[3]) else 0
        if not 0 < rowid <= MAX_ROWID or rowid not in snap.tables[parts[2]]:
            return None, f"그 rowid의 행이 없다({_show(item)})"
        if parts[2] == "observation":
            cited.add(rowid)
    return cited, ""


def evidence_covers(cited: set[int], required: list, snap: Snapshot) -> tuple[bool, str]:
    """풀린 행이 기대값 계산에 필요한 행 묶음을 모두 포함하는가. 총계 행은 근거가 될 수 없고, 빈 묶음(인용할 행이 없는
    키)은 어떤 근거로도 채우지 못한다."""
    usable = cited - snap.totals
    if not usable:
        return False, "총계 행만 인용했다" if cited else "관측 행을 인용하지 않았다"
    if not required:
        return False, "기대값을 뒷받침할 원본 행을 정할 수 없다"
    if any(not group for group in required):
        return False, "인용할 그 키의 상태 행이 없다"
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
        return (base, code) if base in HS10_BASES and HS10_RE.fullmatch(code) else None
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


def check_context(context: object) -> dict | None:
    """사례 문맥 {"hs6", "partner"(대상국), "grouping_version"}을 검사한다. 없으면 None."""
    if context is None:
        return None
    if not isinstance(context, dict) or not isinstance(context.get("hs6"), str) \
            or not HS6_RE.fullmatch(context["hs6"]) or not isinstance(context.get("partner"), str) \
            or not COUNTRY_RE.fullmatch(context["partner"]) or not isinstance(context.get("grouping_version"), str):
        raise ScorerInputError("사례 문맥은 hs6·partner(국가 코드)·grouping_version을 가진 객체여야 한다")
    return context


def score_claim(claim: object, index: int, snap: Snapshot, run_id: str, report_id: str, snapshot_id: str,
                context: dict | None = None) -> dict:
    """typed claim 하나를 채점해 주장 채점 기록을 돌려준다(룰북 B3-1). 해석할 수 없는 claim은 WRONG_REFERENT다.
    context는 그 실행의 사례 문맥({"hs6", "partner", "grouping_version"})이고 comparison 주장의 비교집합을 정한다."""
    context = check_context(context)
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
                            note=f"{WRONG_REFERENT}: 해석 불가: value가 수(크기 상한 안)나 null이 아니다")
    return _score_numeric(claim, claim_id, snap, run_id, report_id, snapshot_id, fields, parsed, context)


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
    if not isinstance(hs6, str) or not HS6_RE.fullmatch(hs6):
        return None, "해석 불가: hs6가 6자리 문자열이 아니다"
    if not isinstance(partner, str) or not PARTNER_RE.fullmatch(partner):
        return None, "해석 불가: partner가 국가 코드나 ALL이 아니다"
    if not isinstance(period, str) or not MONTH_RE.fullmatch(period):
        return None, "해석 불가: period가 YYYYMM이 아니다"
    if hs10 is not None and not hs10.startswith(hs6):
        return None, "HS10 코드가 hs6 아래 코드가 아니다"
    if partner == ALL and (base in NO_ALL_BASES or claim_type == "comparison"):
        return None, f"partner ALL로 정의하지 않는 지표다({claim['metric']}, {claim_type})"
    if is_directional(claim_type, base):
        if not isinstance(baseline, str) or not MONTH_RE.fullmatch(baseline):
            return None, "전년동월 지표인데 baseline_period가 YYYYMM이 아니다"
        if baseline != shift_month(period, -12):
            return None, "전년동월 지표의 baseline_period가 t−12가 아니다"
    elif claim_type == "data_status":
        if baseline is not None and (not isinstance(baseline, str) or not MONTH_RE.fullmatch(baseline)):
            return None, "해석 불가: baseline_period가 YYYYMM이나 null이 아니다"
        baseline = None
    elif baseline is not None:
        return None, "변화를 말하지 않는 주장에 baseline_period가 있다"
    return (claim_type, base, hs10, hs6, partner, period, baseline), ""


def _referent_exists(snap: Snapshot, hs10: str | None, hs6: str, partner: str, period: str,
                     baseline: str | None) -> str:
    """수 주장의 대상이 분석 범위(수집 계획의 HS6·상대국과 비교국 표의 계획 밖 비교국·ALL, 수집 기간)에 있는가. 없으면
    사유 문장."""
    if hs6 not in snap.plan.hs6:
        return f"분석 범위 밖 품목이다({hs6}, 자료 계약 §2.3.2 행 규칙 7)"
    if partner not in snap.scope_partners:
        return f"분석 범위 밖 상대국이다({partner})"
    for month in (period, baseline):
        if month is not None and month not in snap.plan.month_set:
            return f"수집 기간 밖의 달이다({month})"
    if hs10 is not None and hs10 not in snap.hs10_codes:
        return f"스냅샷에 없는 HS10 코드다({hs10})"
    return ""


def comparison_problem(snap: Snapshot, context: dict | None, hs6: str, partner: str) -> str:
    """comparison 주장의 상대국이 실행 기록의 grouping_version 비교집합에 드는가(룰북 B3-1). 아니면 사유 문장."""
    if context is None:
        return "비교집합을 정할 사례 문맥(대상국·품목·grouping_version)이 없다"
    if hs6 != context["hs6"]:
        return f"비교 주장의 품목이 사례 품목이 아니다({hs6})"
    version = context["grouping_version"]
    peers = snap.comparison_set(context["partner"], hs6, version)
    if peers is None:
        return f"실행 기록의 grouping_version({version[:40]})으로 정한 대상국 {context['partner']}의 비교집합이 스냅샷에 없다"
    if partner not in peers:
        return f"비교집합({version[:40]}) 밖 상대국이다({partner})"
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
                   fields: dict, parsed: tuple, context: dict | None) -> dict:
    claim_type, base, hs10, hs6, partner, period, baseline = parsed
    found = _Findings()
    missing_referent = _referent_exists(snap, hs10, hs6, partner, period, baseline)
    if not missing_referent and claim_type == "comparison":
        missing_referent = comparison_problem(snap, context, hs6, partner)
    if missing_referent:
        found.fail(WRONG_REFERENT, missing_referent)
    if claim["unit"] != fields["unit_expected"]:
        found.fail(WRONG_UNIT, f"단위 {_show(claim['unit'])}는 지표 {claim['metric']}의 단위 {fields['unit_expected']}와 다르다")
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
    if not isinstance(direction, str) or direction not in DIRECTIONS:
        found.fail(WRONG_DIRECTION, f"direction {_show(direction)}가 계약 밖이다")
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
    """data_status 주장: 수집 계획과 먼저 대조한 뒤 상태 값과 근거를 본다(룰북 B3-1).

    - 그 키를 맡은 계획 요청이 없으면(계획 밖 키) 대상 판정을 하지 않고 NOT_COLLECTED를 기대한다. 근거는 snapshot-build가
      비교 대상에 만든 NOT_COLLECTED 행(그 키 자신이나 그 키를 맡았을 요청의 코드)뿐이고, 없으면 UNSUPPORTED다.
    - 계획 안 키라도 HS6가 분석 범위(수집 설정의 hs6) 밖이면 WRONG_REFERENT다(자료 계약 §2.3.2 행 규칙 7).
    - 그 밖은 expect_status가 정한 상태와 그 상태의 행을 기대한다."""
    _, base, hs10, hs6, partner, period, _ = parsed
    found = _Findings()
    reported = claim["value"]
    code = hs10 or hs6
    if not snap.plan.covering(partner, code, period):
        rows = snap.status_rows(status_keys(partner, code, period)).get(NOT_COLLECTED, set())
        by_status: dict[str, set[int]] = {NOT_COLLECTED: rows}
        status_note = "수집 계획 밖 키라 대상 판정 전에 계획과 대조했다(대상 오류 아님)"
    elif hs6 not in snap.plan.hs6:
        found.fail(WRONG_REFERENT, f"분석 범위 밖 품목이다({hs6}, 자료 계약 §2.3.2 행 규칙 7)")
        return claim_record(run_id, report_id, claim_id, **fields, outcome=found.outcome(), note=found.note())
    else:
        by_status, status_note = expect_status(snap, partner, hs6, period, hs10)
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
        elif isinstance(reported, str) and reported in by_status:
            problem = "인용할 그 키의 상태 행이 없다"
        else:
            problem = "주장한 상태를 보여 주는 그 키의 행이 없다"
    if not evidence_ok:
        found.fail(UNSUPPORTED, problem)
    return claim_record(run_id, report_id, claim_id, **fields, outcome=found.outcome(), referent_resolved=True,
                        evidence_ok=evidence_ok, note=found.note())


def report_claims(report: dict) -> list:
    """보고서의 claims 목록. 목록이 아니거나 claim 수가 상한(MAX_CLAIMS_PER_REPORT)을 넘으면 채점할 수 없는 보고서다."""
    claims = report.get("claims")
    if not isinstance(claims, list):
        raise ScorerInputError("보고서의 claims가 목록이 아니다")
    if len(claims) > MAX_CLAIMS_PER_REPORT:
        raise ScorerInputError(f"보고서의 claim 수가 채점기 상한({MAX_CLAIMS_PER_REPORT})을 넘는다")
    return claims


def score_report_claims(report: dict, snap: Snapshot, run_id: str, snapshot_id: str,
                        context: dict | None = None) -> list[dict]:
    """보고서 하나의 typed claim을 모두 채점한다. 보고서의 claims가 목록이 아니거나 상한을 넘으면 입력 오류다."""
    claims = report_claims(report)
    report_id = report.get("report_id") if isinstance(report.get("report_id"), str) else ""
    context = check_context(context)
    return [score_claim(claim, i, snap, run_id, report_id, snapshot_id, context) for i, claim in enumerate(claims)]


def run(inp: object) -> object:
    """진입 함수. 입력: {"snapshot": {"snapshot_id", "tables": {테이블: [행(rowid 포함)]}}, "reports": [보고서 객체],
    "contexts"(선택): {run_id: {"hs6", "partner"(대상국), "grouping_version"}}}. 출력: 보고서 순서·claim 순서대로의 주장
    채점 기록(source=claim) 목록. 실행 스냅샷은 snapshot.snapshot_id다. 스냅샷 tables에는 snapshot_meta(수집 계획)가
    있어야 한다."""
    if not isinstance(inp, dict) or not isinstance(inp.get("reports"), list):
        raise ScorerInputError("입력은 snapshot과 reports를 가진 객체여야 한다")
    snap = Snapshot.from_json(inp.get("snapshot"))
    contexts = inp.get("contexts") or {}
    if not isinstance(contexts, dict):
        raise ScorerInputError("contexts는 run_id → 사례 문맥 객체여야 한다")
    records: list[dict] = []
    for report in inp["reports"]:
        if not isinstance(report, dict) or not isinstance(report.get("run_id"), str):
            raise ScorerInputError("보고서는 run_id를 가진 객체여야 한다")
        records += score_report_claims(report, snap, report["run_id"], snap.snapshot_id,
                                       contexts.get(report["run_id"]))
    return records
