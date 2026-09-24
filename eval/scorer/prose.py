"""단위 C2 산문 채점.

단위 ID: C2
도메인명: scorer_prose
소유: D
입력: 보고서 산문
출력: 패턴 판정(룰북 B3-2)
허용 import: 표준 라이브러리, eval.scorer

보고서의 자유 문장 필드(narrative, hypotheses[i], claims[i].text)에서 숫자·증감 표현을 결정적 패턴으로 잡고, 같은
보고서의 typed claim으로 뒷받침되는지 판정해 주장 채점 기록(source=prose)을 만든다(룰북 docs/eval/RULEBOOK.md B3-2).

- 잡는 표현: PT-1 백분율, PT-2 퍼센트포인트(PT-1보다 먼저), PT-3 금액·중량·단가, PT-4 배수, PT-5 단위 없는 숫자와
  개수, PT-6 증감 어휘, PT-8 "X에서 Y로". PT-7 극값·순위 말은 채점하지 않고 건수만 센다(extreme_count).
- 빼는 표현: EX-1 날짜·기간("N개월 연속"은 빼지 않는다), EX-2 품목·국가 식별(점·하이픈을 뗀 숫자가 스냅샷 HS 코드
  집합에 있으면 뺀다), EX-3 식별자·버전, EX-4 목록 번호와 조사 과정의 개수, EX-5 정책 탐지 임계값, EX-6 지표 이름
  속 증감 글자(증가율·상승률은 부호 그대로, 감소율·하락률은 반대로 읽는다).
- 값 비교는 단위 C1과 같은 규칙(보인 자리수, 계약 자릿수 상한, 사사오입)이다. 뒷받침된 표현은 CORRECT, 아니면
  UNBACKED_PROSE다. 뒷받침한 claim 자체의 참·거짓은 그 claim의 기록이 맡는다(같은 사실을 두 번 세지 않는다).
- 기록의 claim_id는 prose:<필드>:<순번>(필드 안 시작 위치 순서, 1부터), reported_value는 잡힌 표현 원문, note에
  표현·위치·분류와 뒷받침한 claim_id를 적는다(자료 계약 §9.2). prose 기록의 referent_resolved·evidence_ok는
  뒷받침하는 claim을 찾았는지를 적는다(해석은 보고서 참조).
- 한국어 품질(룰북 B4, 참고 측정): korean_quality가 한글 비율, 금지 표현 건수, 필수 항목 누락 건수를 센다. 금지 표현
  목록(FORBIDDEN_EXPRESSIONS)과 산문 패턴 목록은 RB-1과 함께 동결하고, 누락·오탐 보강은 real_dev 결과로만 한다.
"""
import hashlib
import re
from decimal import Decimal
from fractions import Fraction

from eval.scorer import claims as c1

# ----------------------------------------------------------------------------- 산문 패턴 목록(RB-1과 함께 동결)

# 숫자 표현 하나: [근사어] [단위 앞말] [부호] 숫자 [배수] [단위] [대] [근사어] [부등식]
NUMBER_EXPR = re.compile(r"""
    (?P<approx_pre>(?<![가-힣])(?:약|대략|거의)\s*)?
    (?P<pre>US\$\s*|USD\s*|\$\s*|(?:kg|킬로그램)\s*당\s*|톤\s*당\s*)?
    (?P<sign>[△▼▲+\-−])?
    (?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)
    (?P<mult>\s*(?:백만|천만|억|만(?!큼)|천(?![가-힣])))?
    (?P<unit>\s*(?:퍼센트\s*포인트|%\s*포인트|%p(?![A-Za-z])|pp(?![A-Za-z])|퍼센트|%|％
               |USD/kg|USD/킬로그램|달러/kg|달러/킬로그램|USD/톤|달러/톤|USD|달러|kg|킬로그램|톤|배))?
    (?P<range>대)?
    (?P<approx_suf>\s*(?:가량|쯤|안팎|내외|정도|남짓))?
    (?P<ineq>\s*(?:을|를|이|가|은|는)?\s*(?:이상|넘게|넘는|넘어|넘었|초과|웃도는|웃돈|웃돌|미만|이하|밑도는|밑돈|밑돌))?
""", re.X)
WORD_MULTIPLE = re.compile(r"(?<![가-힣])(?P<word>두|세|네|다섯)\s*배|(?P<half>절반|반토막)")
WORD_MULTIPLE_VALUES = {"두": 2, "세": 3, "네": 4, "다섯": 5}
MULTIPLIERS = {"": 0, "천": 3, "만": 4, "백만": 6, "천만": 7, "억": 8}  # 10의 지수

# PT-6 증감 어휘(어간 기준, 룰북 B3-2 표의 활용형만). EX-6 지표 이름(증가율 등)과 피할 오탐은 뒤보기로 뺀다.
DIRECTION_WORDS = {
    "UP": re.compile(r"증가(?!율)|상승(?!률)|급증|급등|폭등|치솟|반등|확대(?!\s*해석)|늘(?:었|어|며|고)|오르|올라"
                     r"|오른(?!쪽|편)|올랐|높아(?:지|졌|진)"),
    "DOWN": re.compile(r"감소(?!율)|하락(?!률)|급감|급락|폭락|반토막|축소|줄(?:었|어|며|고)|떨어(?:지|졌|진|져)"
                       r"|낮아(?:지|졌|진)"),
    "FLAT": re.compile(r"보합|변화가\s*없|변동이\s*없|변함없|제자리"),
}
LOWERED = re.compile(r"내렸")  # 바로 앞이 단가·가격·값·금액과 조사 이·가·은·는일 때만 내림(룰북 B3-2 PT-6)
LOWERED_BEFORE = re.compile(r"(?:단가|가격|값|금액)(?:이|가|은|는)\s?$")
NEGATION_AFTER = re.compile(r"^(?:[가-힣]{0,4}?지\s*(?:않|못)|\s*(?:이|가|은|는)?\s*없)")
EXTREMES = re.compile(r"최고|최저|최대|최소")  # PT-7(채점 제외, 건수만)
RATE_NAMES = re.compile(r"(?P<rate>증가율|상승률|감소율|하락률)[^\d\n.。]{0,12}$")  # EX-6
FROM_TO_BETWEEN = re.compile(r"^\s*에서\s*$")
FROM_TO_AFTER = re.compile(r"^\s*(?:으로|로)")
THRESHOLD_BEFORE = re.compile(r"(?:기준값|기준|임계값|임계)\s*$")  # EX-5
APPROX_WORDS = ("약", "대략", "거의", "가량", "쯤", "안팎", "내외", "정도", "남짓")

EXCLUDE_PATTERNS = (
    # EX-3 식별자·버전: 근거 ID, 숫자가 든 영문 식별자(c1, policy_v1, RB-1, g0, kcs_202201_202412_v2 등)
    re.compile(r"ev:[^\s,;)\]}'\"]+"),
    re.compile(r"(?<![A-Za-z0-9_@])(?!USD\d)[A-Za-z_][A-Za-z0-9_@]*(?:[-.:/][A-Za-z0-9_@]+)*"),
    # EX-1 날짜·기간
    re.compile(r"(?:19|20)\d{2}\s*[~∼–-]\s*(?:19|20)\d{2}"),
    re.compile(r"(?:19|20)\d{2}\s*년(?:\s*\d{1,2}\s*월)?"),
    re.compile(r"(?<!\d)\d{1,2}\s*년(?:\s*\d{1,2}\s*월)?"),
    re.compile(r"(?<!\d)(?:19|20)\d{2}[./-](?:0?[1-9]|1[0-2])(?!\d)"),
    re.compile(r"(?<!\d)(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?!\d)"),
    re.compile(r"(?<!\d)\d{1,2}\s*월"),
    re.compile(r"(?<!\d)\d{1,3}\s*(?:일|주)(?!\s*연속)"),
    re.compile(r"(?<!\d)[1-4]\s*분기"),
    re.compile(r"(?<!\d)\d+\s*개월(?!\s*연속)"),
    re.compile(r"(?<![A-Za-z0-9])t\s*[−-]\s*\d+"),
    # EX-2 품목 식별: HS와 함께 쓴 숫자, 류·호 표기(HS 코드 집합 대조는 hs_code_spans)
    re.compile(r"HS\s*(?:코드\s*)?\d[\d.\-]*"),
    re.compile(r"제?\s*\d+\s*류"),
    re.compile(r"제?\s*\d{4}\s*호"),
    # EX-4 목록 번호와 조사 과정·구조의 개수, "1kg당"처럼 단위 기준을 뜻하는 숫자
    re.compile(r"(?m)^\s*\(?\d{1,2}[.)](?=\s)"),
    re.compile(r"(?<!\d)\d+\s*(?:회|번째|단계)"),
    re.compile(r"제\s*\d+(?:\s*[-.]\s*\d+)*"),
    re.compile(r"(?:신호|도구|지표)\s*(?:를|을|는|은|가|이)?\s*\d+\s*(?:개|종|가지)"),
    re.compile(r"(?<!\d)\d+\s*(?:개|종|가지)\s*(?:의\s*)?(?:신호|도구|지표)"),
    re.compile(r"(?<!\d)\d+\s*(?:kg|킬로그램|톤)\s*당"),
)
HS_TOKEN = re.compile(r"(?<![\d.,])\d[\d.\-]*\d(?!\d)")

# 한국어 품질 금지 표현(룰북 B4, 참고 측정): 부정·위법·원산지 조작·개별 거래가격을 단정하는 표현과 "정상 확정" 같은
# 문구. "…여부"(판정하지 않는다는 안내)로 이어지는 쓰임은 세지 않는다.
FORBIDDEN_EXPRESSIONS = (
    r"정상\s*확정", r"정상으로\s*확정", r"위법", r"불법", r"탈세", r"탈루", r"밀수", r"포탈",
    r"부정\s*(?:거래|행위|수입|신고)", r"우회\s*수입", r"원산지\s*(?:조작|위조|세탁|둔갑|속임|허위)",
    r"허위\s*신고", r"저가\s*신고", r"(?:거래\s*가격|가격)\s*조작", r"덤핑",
)
FORBIDDEN_RE = re.compile("|".join(f"(?:{p})" for p in FORBIDDEN_EXPRESSIONS))
NOT_A_JUDGEMENT_AFTER = re.compile(r"^\s*(?:여부|인지|가능성)")
STATUS_LABELS = {"MAINTAIN": "검토 유지", "MONITOR": "모니터링", "HOLD": "자료 보류"}
REPORT_KEYS = ("report_id", "run_id", "case_id", "mode", "claims", "narrative", "hypotheses", "review_status",
               "signal_status", "unresolved_evidence", "evidence_ids", "validator_findings", "report_hash",
               "created_at", "policy_version", "snapshot_id", "grouping_version")


def pattern_list_sha256() -> str:
    """산문 패턴 목록과 금지 표현 목록의 지문(요약의 "산문 패턴 목록 버전"). 패턴 원문을 차례로 이어 sha256을 낸다."""
    parts = [NUMBER_EXPR.pattern, WORD_MULTIPLE.pattern, LOWERED.pattern, LOWERED_BEFORE.pattern,
             NEGATION_AFTER.pattern, EXTREMES.pattern, RATE_NAMES.pattern, FROM_TO_BETWEEN.pattern,
             FROM_TO_AFTER.pattern, THRESHOLD_BEFORE.pattern, HS_TOKEN.pattern, FORBIDDEN_RE.pattern,
             NOT_A_JUDGEMENT_AFTER.pattern]
    parts += [f"{k}={v.pattern}" for k, v in sorted(DIRECTION_WORDS.items())]
    parts += [p.pattern for p in EXCLUDE_PATTERNS]
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


# ----------------------------------------------------------------------------- 표현 잡기

class Expr:
    """잡힌 표현 하나. kind: number·multiple·word·from_to. value는 claim 단위의 값(부호 없는 표현은 절댓값),
    exp는 비교 자리(10의 지수), unit은 단위 부류(%, pp, USD, USD/kg, kg, USD/톤, 배 또는 None)다."""

    def __init__(self, kind: str, pt: str, start: int, end: int, text: str, **fields: object):
        self.kind, self.pt, self.start, self.end, self.text = kind, pt, start, end, text
        self.value: Fraction | None = fields.get("value")
        self.exp: int = fields.get("exp", 0)
        self.unit: str | None = fields.get("unit")
        self.signed: bool = fields.get("signed", False)
        self.low: Fraction | None = fields.get("low")
        self.high: Fraction | None = fields.get("high")
        self.op: str | None = fields.get("op")
        self.direction: str | None = fields.get("direction")
        self.negated: bool = fields.get("negated", False)
        self.x: "Expr | None" = fields.get("x")
        self.y: "Expr | None" = fields.get("y")


def _masked_spans(text: str, hs_codes: set[str], identifiers: list[str]) -> list[tuple[int, int]]:
    spans = [(m.start(), m.end()) for pattern in EXCLUDE_PATTERNS for m in pattern.finditer(text)
             if pattern.pattern.startswith("ev:") or any(ch.isdigit() for ch in m.group())]
    for m in HS_TOKEN.finditer(text):
        if re.sub(r"[.\-]", "", m.group()) in hs_codes:
            spans.append((m.start(), m.end()))
    for ident in identifiers:
        start = text.find(ident)
        while ident and start >= 0:
            spans.append((start, start + len(ident)))
            start = text.find(ident, start + 1)
    return spans


def _overlaps(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    return any(start < b and a < end for a, b in spans)


def _last_nonzero_exp(raw: str) -> int:
    """숫자 원문에서 마지막 0 아닌 자리의 10의 지수(근사어·"N%대" 규칙). 값이 0이면 0."""
    whole, _, frac = raw.partition(".")
    frac = frac.rstrip("0")
    if frac:
        return -len(frac)
    stripped = whole.rstrip("0")
    return len(whole) - len(stripped) if stripped else 0


def _unit_class(pre: str, unit: str) -> str | None:
    pre = re.sub(r"\s+", "", pre)
    unit = re.sub(r"\s+", "", unit)
    if unit in ("퍼센트포인트", "%포인트", "%p", "pp"):
        return "pp"
    if unit in ("퍼센트", "%", "％"):
        return "%"
    if unit == "배":
        return "배"
    if unit in ("USD/kg", "USD/킬로그램", "달러/kg", "달러/킬로그램") or (pre in ("kg당", "킬로그램당")):
        return "USD/kg"
    if unit in ("USD/톤", "달러/톤") or pre == "톤당":
        return "USD/톤"
    if unit in ("USD", "달러") or pre in ("USD", "US$", "$"):
        return "USD"
    if unit in ("kg", "킬로그램", "톤"):
        return "kg"
    return None


def _rate_sign(text: str, start: int) -> str | None:
    """EX-6: 숫자 앞 같은 마디에 지표 이름이 있으면 그 이름."""
    m = RATE_NAMES.search(text[max(0, start - 16):start])
    return m.group("rate") if m else None


def _parse_number(m: re.Match, text: str, thresholds: list[Fraction]) -> Expr | None:
    raw = m.group("num").replace(",", "")
    pre = m.group("pre") or ""
    unit_token = m.group("unit") or ""
    unit = _unit_class(pre, unit_token)
    mult = re.sub(r"\s+", "", m.group("mult") or "")
    scale_exp = MULTIPLIERS[mult] + (3 if re.sub(r"\s+", "", unit_token) == "톤" else 0)
    approx = bool(m.group("approx_pre") or m.group("approx_suf"))
    frac_digits = len(raw.partition(".")[2])
    own_exp = _last_nonzero_exp(raw) if approx else -frac_digits
    number = Fraction(Decimal(raw)) * Fraction(10) ** scale_exp
    start = m.start()
    if THRESHOLD_BEFORE.search(text[:start]) and number in thresholds and not m.group("sign"):
        return None  # EX-5 정책 탐지 임계값
    sign = m.group("sign")
    signed = sign is not None
    value = -number if sign in ("△", "▼", "-", "−") else number
    rate = _rate_sign(text, start)
    if rate is not None:  # EX-6: 증가율·상승률은 부호 그대로, 감소율·하락률은 반대로. 부호가 없으면 이름으로 정한다
        down = rate in ("감소율", "하락률")
        value = (-value if down else value) if signed else (-number if down else number)
        signed = True
    kind, pt = "number", {"%": "PT-1", "pp": "PT-2", "배": "PT-4", None: "PT-5"}.get(unit, "PT-3")
    fields: dict = {"value": value, "exp": own_exp + scale_exp, "unit": unit, "signed": signed}
    if unit == "배":
        kind = "multiple"
        fields["value"] = number if not signed else value
        fields["exp"] = own_exp
    if m.group("range") and unit == "%":
        width = Fraction(10) ** _last_nonzero_exp(raw)
        fields.update(low=value, high=value + width if value >= 0 else value - width)
    ineq = m.group("ineq")
    if ineq:
        fields["op"] = "<=" if re.search(r"미만|이하|밑도는|밑돈|밑돌", ineq) else ">="
    end = m.end()
    return Expr(kind, pt, start, end, text[start:end].strip(), **fields)


def _word_multiples(text: str, spans: list) -> list[Expr]:
    found = []
    for m in WORD_MULTIPLE.finditer(text):
        if _overlaps(m.start(), m.end(), spans):
            continue
        if m.group("word"):
            value, exp = Fraction(WORD_MULTIPLE_VALUES[m.group("word")]), 0
        else:
            value, exp = Fraction(1, 2), -1
        found.append(Expr("multiple", "PT-4", m.start(), m.end(), m.group(), value=value, exp=exp, unit="배"))
    return found


def _direction_words(text: str) -> list[Expr]:
    found = []
    for direction, pattern in DIRECTION_WORDS.items():
        for m in pattern.finditer(text):
            found.append(_word(text, m, direction))
    for m in LOWERED.finditer(text):
        if LOWERED_BEFORE.search(text[:m.start()]):
            found.append(_word(text, m, "DOWN"))
    return found


def _word(text: str, m: re.Match, direction: str) -> Expr:
    negated = direction != "FLAT" and bool(NEGATION_AFTER.search(text[m.end():m.end() + 12]))
    return Expr("word", "PT-6", m.start(), m.end(), m.group(), direction=direction, negated=negated)


def extract(text: str, hs_codes: set[str], identifiers: list[str], thresholds: list[Fraction]) -> list[Expr]:
    """필드 하나에서 채점할 표현을 시작 위치 순서로 잡는다(PT-7은 넣지 않는다)."""
    spans = _masked_spans(text, hs_codes, identifiers)
    numbers: list[Expr] = []
    for m in NUMBER_EXPR.finditer(text):
        if _overlaps(m.start("num"), m.end("num"), spans):
            continue
        expr = _parse_number(m, text, thresholds)
        if expr is not None:
            numbers.append(expr)
    numbers += _word_multiples(text, spans)
    numbers.sort(key=lambda e: e.start)
    pairs = []
    for x, y in zip(numbers, numbers[1:]):
        if x.kind == "number" and y.kind == "number" and FROM_TO_BETWEEN.match(text[x.end:y.start]) \
                and FROM_TO_AFTER.match(text[y.end:]):
            direction = "UP" if y.value > x.value else ("DOWN" if y.value < x.value else "FLAT")
            end = y.end + FROM_TO_AFTER.match(text[y.end:]).end()
            pairs.append(Expr("from_to", "PT-8", x.start, end, text[x.start:end], direction=direction, x=x, y=y))
    order = {"number": 0, "multiple": 0, "from_to": 1, "word": 2}
    found = numbers + pairs + _direction_words(text)
    found.sort(key=lambda e: (e.start, order[e.kind], e.end))
    return found


def extreme_count(report: dict) -> int:
    """PT-7 극값·순위 말(최고·최저·최대·최소)의 건수(참고, 채점 제외)."""
    return sum(len(EXTREMES.findall(text)) for _, text in prose_fields(report))


# ----------------------------------------------------------------------------- 뒷받침 판정

class _Claim:
    """뒷받침에 쓰는 claim 정보."""

    def __init__(self, claim: dict):
        self.claim = claim
        self.id = claim.get("claim_id") if isinstance(claim.get("claim_id"), str) else ""
        value = claim.get("value")
        self.value = Fraction(value) if c1.is_number(value) else None
        self.raw = value
        self.unit = claim.get("unit") if isinstance(claim.get("unit"), str) else None
        parsed = c1.parse_metric(claim.get("metric"))
        self.base = parsed[0] if parsed else None
        self.metric = claim.get("metric")
        self.direction = claim.get("direction")
        self.hs6, self.partner, self.period = claim.get("hs6"), claim.get("partner"), claim.get("period")

    def contract_exp(self) -> int | None:
        digits = c1.METRIC_DIGITS.get(self.base) if self.base else None
        return None if digits is None else -digits


COMPATIBLE_UNITS = {"%": ("%",), "pp": ("pp",), "USD": ("USD", "USD/kg"), "USD/kg": ("USD/kg",), "kg": ("kg",),
                    "USD/톤": ("USD/톤",)}


def _candidates(expr: Expr, claims: list[_Claim]) -> list[_Claim]:
    numeric = [c for c in claims if c.value is not None]
    if expr.kind == "multiple":
        return [c for c in numeric if c.metric == "r_U"]
    if expr.unit is None:
        return numeric
    return [c for c in numeric if c.unit in COMPATIBLE_UNITS[expr.unit]]


def _number_matches(expr: Expr, claim: _Claim) -> tuple[bool, int]:
    """(뒷받침 여부, 비교 자리 지수)."""
    if expr.kind == "multiple":
        ratio = 1 + claim.value / 100
        if expr.op:
            return (ratio >= expr.value if expr.op == ">=" else ratio <= expr.value), expr.exp
        return c1.round_half_up(ratio, -expr.exp) == expr.value, expr.exp
    value = claim.value if expr.signed else abs(claim.value)
    if expr.low is not None:  # "N%대": N 이상 N+폭 미만(음수면 N−폭 초과 N 이하)
        inside = expr.low <= value < expr.high if expr.low <= expr.high else expr.high < value <= expr.low
        return inside, expr.exp
    if expr.op:
        return (value >= expr.value if expr.op == ">=" else value <= expr.value), expr.exp
    exp = expr.exp
    contract = claim.contract_exp()
    if contract is not None:
        exp = max(exp, contract)
    return c1.round_half_up(value, -exp) == c1.round_half_up(expr.value, -exp), exp


def backing_claims(expr: Expr, claims: list[_Claim]) -> list[tuple[_Claim, int]]:
    """숫자·배수 표현을 뒷받침하는 claim과 비교 자리 지수."""
    found = []
    for claim in _candidates(expr, claims):
        ok, exp = _number_matches(expr, claim)
        if ok:
            found.append((claim, exp))
    return found


def _direction_backers(direction: str, negated: bool, claims: list[_Claim]) -> list[_Claim]:
    if negated:
        wanted = {"UP": {"DOWN", "FLAT"}, "DOWN": {"UP", "FLAT"}, "FLAT": {"UP", "DOWN"}}[direction]
    else:
        wanted = {direction}
    return [c for c in claims if c.direction in wanted]


def _pair_problem(expr: Expr, claims: list[_Claim]) -> bool:
    """PT-8 짝 규칙: X·Y를 뒷받침하는 같은 hs6·partner·metric의 수준 claim 짝이 있는데 모두 기간이 뒤집혔으면 참."""
    xs = [c for c, _ in backing_claims(expr.x, claims) if c.base in c1.LEVEL_BASES]
    ys = [c for c, _ in backing_claims(expr.y, claims) if c.base in c1.LEVEL_BASES]
    pairs = [(a, b) for a in xs for b in ys if a is not b and (a.hs6, a.partner, a.metric) == (b.hs6, b.partner, b.metric)
             and isinstance(a.period, str) and isinstance(b.period, str)]
    return bool(pairs) and not any(a.period < b.period for a, b in pairs)


def judge(expr: Expr, claims: list[_Claim]) -> tuple[bool, _Claim | None, object, str]:
    """(뒷받침 여부, 뒷받침한 첫 claim, 허용오차 기록값, 메모)."""
    if expr.kind in ("number", "multiple"):
        backers = backing_claims(expr, claims)
        if backers:
            claim, exp = backers[0]
            exact = expr.low is None and expr.op is None
            return True, claim, c1.step_out(-exp) if exact else None, "" if exact else "구간·부등식 비교"
        return False, None, None, "같은 단위의 값이 맞는 claim이 없다"
    if expr.kind == "word":
        backers = _direction_backers(expr.direction, expr.negated, claims)
        wanted = ("부정형 " if expr.negated else "") + expr.direction
        return (True, backers[0], None, f"방향 {wanted}") if backers else \
            (False, None, None, f"방향 {wanted}인 claim이 없다")
    backers = _direction_backers(expr.direction, False, claims)
    if not backers:
        return False, None, None, f"방향 {expr.direction}인 claim이 없다"
    if _pair_problem(expr, claims):
        return False, None, None, "같은 대상의 수준 claim 짝의 기간 순서가 뒤집혔다"
    return True, backers[0], None, f"방향 {expr.direction}"


# ----------------------------------------------------------------------------- 보고서 채점

def prose_fields(report: dict) -> list[tuple[str, str]]:
    """산문 검사 필드(룰북 B3-2 적용 범위): narrative, hypotheses[i], claims[i].text. (필드 경로, 문장)."""
    fields: list[tuple[str, str]] = []
    if isinstance(report.get("narrative"), str):
        fields.append(("narrative", report["narrative"]))
    hypotheses = report.get("hypotheses")
    if isinstance(hypotheses, list):
        fields += [(f"hypotheses[{i}]", h) for i, h in enumerate(hypotheses) if isinstance(h, str)]
    claims = report.get("claims")
    if isinstance(claims, list):
        fields += [(f"claims[{i}].text", c["text"]) for i, c in enumerate(claims)
                   if isinstance(c, dict) and isinstance(c.get("text"), str)]
    return fields


def report_identifiers(report: dict) -> list[str]:
    """EX-3로 뺄 보고서의 식별자 값(case_id·run_id·report_id·claim_id)."""
    ids = [report.get(key) for key in ("case_id", "run_id", "report_id")]
    claims = report.get("claims") if isinstance(report.get("claims"), list) else []
    ids += [c.get("claim_id") for c in claims if isinstance(c, dict)]
    return sorted({i for i in ids if isinstance(i, str) and i}, key=len, reverse=True)


def score_report_prose(report: dict, run_id: str, hs_codes: set[str], thresholds: list[Fraction]) -> list[dict]:
    """보고서 하나의 산문 기록(source=prose)을 필드 순서·시작 위치 순서로 만든다."""
    report_id = report.get("report_id") if isinstance(report.get("report_id"), str) else ""
    raw_claims = report.get("claims") if isinstance(report.get("claims"), list) else []
    claims = [_Claim(c) for c in raw_claims if isinstance(c, dict)]
    identifiers = report_identifiers(report)
    records = []
    for field, text in prose_fields(report):
        for n, expr in enumerate(extract(text, hs_codes, identifiers, thresholds), start=1):
            ok, backer, tolerance, reason = judge(expr, claims)
            note = f"{expr.pt} '{expr.text}' {field} {expr.start}~{expr.end}자: " \
                + (f"뒷받침 claim {backer.id}" + (f"({reason})" if reason else "") if ok else reason)
            records.append(c1.claim_record(
                run_id, report_id, f"prose:{field}:{n}", source=c1.SOURCE_PROSE,
                outcome=c1.CORRECT if ok else c1.UNBACKED_PROSE,
                expected_value=backer.raw if ok and expr.kind in ("number", "multiple") else None,
                reported_value=expr.text, unit_expected=backer.unit if ok and backer is not None else None,
                unit_reported=expr.unit, tolerance=tolerance, referent_resolved=ok, evidence_ok=ok, note=note))
    return records


def korean_quality(report: dict) -> dict:
    """한국어 품질 참고 측정(룰북 B4): 한글 음절 수·라틴 문자 수(백틱 안 식별자와 근거 ID 제외), 금지 표현 건수,
    필수 항목 누락 건수(보고서 키, narrative의 판정 상태 한국어 표기)."""
    hangul = latin = forbidden = 0
    for _, text in prose_fields(report):
        cleaned = re.sub(r"ev:[^\s,;)\]}'\"]+", " ", re.sub(r"`[^`]*`", " ", text))
        hangul += len(re.findall(r"[가-힣]", cleaned))
        latin += len(re.findall(r"[A-Za-z]", cleaned))
        forbidden += sum(1 for m in FORBIDDEN_RE.finditer(text) if not NOT_A_JUDGEMENT_AFTER.match(text[m.end():]))
    missing = sum(1 for key in REPORT_KEYS if key not in report)
    label = STATUS_LABELS.get(report.get("review_status"))
    if label is None or label not in (report.get("narrative") if isinstance(report.get("narrative"), str) else ""):
        missing += 1
    return {"hangul": hangul, "latin": latin, "forbidden": forbidden, "missing": missing}


def run(inp: object) -> object:
    """진입 함수. 입력: {"reports": [보고서 객체], "hs_codes": [스냅샷 HS 코드], "thresholds": [정책 탐지 임계값]}.
    출력: 보고서 순서·필드 순서·시작 위치 순서의 주장 채점 기록(source=prose) 목록."""
    if not isinstance(inp, dict) or not isinstance(inp.get("reports"), list):
        raise c1.ScorerInputError("입력은 reports를 가진 객체여야 한다")
    hs_codes = {str(code) for code in inp.get("hs_codes", [])}
    thresholds = [Fraction(t) for t in inp.get("thresholds", []) if c1.is_number(t)]
    records: list[dict] = []
    for report in inp["reports"]:
        if not isinstance(report, dict) or not isinstance(report.get("run_id"), str):
            raise c1.ScorerInputError("보고서는 run_id를 가진 객체여야 한다")
        records += score_report_prose(report, report["run_id"], hs_codes, thresholds)
    return records
