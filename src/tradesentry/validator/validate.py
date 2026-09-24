"""단위 R3 검증 규칙.

단위 ID: R3
도메인명: validator_validate
소유: M
입력: 보고서·봉투·스냅샷
출력: findings(`validator_findings`)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics, tradesentry.policy, tradesentry.validator

정본: 개발 플랜 docs/plan/DEV_PLAN.md §7.4(검증기), 자료 계약 docs/rules/DATA_CONTRACT_V1.md §3(상태값), §4.4(근거 ID
풀림), §6(typed claim), §9.1·§9.4(보고서와 스키마 요건), §11(단위·자릿수), 룰북 docs/eval/RULEBOOK.md B3-1(값 비교)·
B3-2(산문 패턴). 검증기는 정답표를 읽지 않고, 모델의 틀린 값·상태를 고치지 않고 사유만 적는다. 막을지(모드별)는 단위
R4가 정한다.

입력(JSON 객체 하나)
- `report`: 보고서 초안이나 보고서 객체(자료 계약 §9.1). `report_id`·`evidence_ids`·`validator_findings`·`report_hash`·
  `created_at`은 없어도 된다(검증 뒤 단위 R2가 채운다).
- `case`: 사례 객체(자료 계약 §2.3.5). 코드가 만든 것이라 형식이 틀리면 ValueError다.
- `run`: 이 실행의 기대 출처 `{"run_id", "mode", "snapshot_id", "policy_version", "grouping_version"}`
- `envelopes`: 이 실행에서 도구가 돌려준 봉투 목록(자료 계약 §5). 검증된 지표(`metrics`)와 돌려준 근거의 출처다.
- `rows`: 스냅샷 조회 결과 `{근거 ID: 행 객체 또는 null}`. 부르는 쪽이 자료 접근층(단위 K3)으로 보고서·봉투의 근거 ID를
  풀어 넣는다. 없거나 null이면 그 근거 ID는 풀리지 않는다(풀림 규칙 3·4).
- `hs_codes`(생략 가능): 스냅샷의 HS 코드 목록(HS4·HS6·HS10). 산문 검사의 EX-2가 쓴다. 사례·행·지표에서 보이는
  코드는 따로 넣지 않아도 더한다.
- `thresholds`(생략 가능): 정책의 탐지 임계값 목록(예: 개발 정책 dev-0.1은 30과 10). 산문 검사의 EX-5가 쓴다. 코드에
  정책 수치를 두지 않으려고 입력으로 받는다.

출력: `{"findings": [finding, ...]}`. finding은 `{"check", "code", "path", "claim_id", "detail"}`이다.
- `check`: `schema`(스키마 검사: 형식·자료형·발동 신호별 주장 요건, 모든 모드에서 막는다) 또는 `validator`(검증기 검사:
  숫자·단위·원본 행·출처·스냅샷·허용 상태·금지 문구·산문, `freeform`에서는 기록만 한다)
- `code`: 사유 코드(아래 CODES). `path`: 보고서 안 위치(예: `claims[2].value`, `narrative`). `detail`: 한국어 설명.

해석(계약이 정하지 않아 이 단위가 정한 것. 조립(AS2)에서 확인한다)
- 검증된 지표는 봉투 `metrics`의 `metric` 객체다. 지표 기호는 `inputs.metric`에서 읽는다(단위 R1과 같은 해석).
  주장과 지표는 (기호, `hs6`, `partner`, `period`)와 변화 기호면 `baseline_period`까지 같을 때 짝이 된다.
- 도구가 돌려준 근거는 봉투의 `evidence_ids`, 지표의 `evidence_ids`, `missingness` 항목의 `evidence_ids`·`evidence_id`다.
- 동등한 행(룰북 B3-1: 같은 키가 두 요청에 중복돼 값이 같은 행)은 테이블과 (`partner_code`, `hs_code`, `month`,
  `flow`, `amount_usd`, `net_weight_kg`, `observation_status`)가 모두 같은 행이다.
- 금지 문구 목록과 산문 패턴 정규식은 이 파일에 둔다. 룰북 B3-2가 정본이고, 채점기(eval/scorer)와 따로 구현했다.
- 기호·단위·자릿수·상태값 표는 자료 계약의 사본이다(단위 표 §6 조립 부산물 4. 조립 점검에서 K1·X4로 옮긴다).
"""
import re
import unicodedata
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

# ---- 자료 계약 사본 ------------------------------------------------------------------------------------------
MODES = ("checklist", "agent", "full", "freeform")
CLAIM_FIELDS = ("claim_id", "claim_type", "hs6", "partner", "period", "baseline_period", "metric", "value", "unit",
                "direction", "evidence_ids", "text")
CLAIM_TYPES = ("value", "change", "share", "share_change", "decomposition", "comparison", "data_status")
DIRECTIONS = ("UP", "DOWN", "FLAT", "NA")
REVIEW_STATUSES = ("MAINTAIN", "MONITOR", "HOLD")
SIGNAL_STATUSES = ("MAINTAIN", "MONITOR", "HOLD", "NOT_TRIGGERED")
SIGNAL_TRIGGERS = ("TRIGGERED", "NOT_TRIGGERED")
SIGNALS = ("unit_value", "share")
OBSERVATION_STATUSES = ("OBSERVED", "NOT_COLLECTED", "REQUEST_FAILED", "UNRESOLVED_ZERO", "CONFIRMED_NO_TRADE")
UNIT_OF = {"V": "USD", "Q": "kg", "U": "USD/kg", "r_U": "%", "s": "%", "d_s": "pp",
           "within_effect": "USD/kg", "mix_effect": "USD/kg", "residual": "USD/kg", "w": "%"}
DIGITS_OF = {"V": 0, "Q": 0, "U": 2, "r_U": 1, "s": 1, "d_s": 1,
             "within_effect": 2, "mix_effect": 2, "residual": 2, "w": 1}
SUB_ITEM_BASES = ("U", "r_U", "w")
DECOMPOSITION = ("within_effect", "mix_effect", "residual")
CHANGE_BASES = ("r_U", "d_s") + DECOMPOSITION
UNIT_VALUE_BASES = ("U", "r_U", "w") + DECOMPOSITION  # 계약 §9.4 신호 계열 unit_value
SHARE_BASES = ("s", "d_s")  # 계약 §9.4 신호 계열 share
TYPE_BASES = {"value": ("V", "Q", "U", "w"), "change": ("r_U",), "share": ("s",), "share_change": ("d_s",),
              "decomposition": DECOMPOSITION}
TOTAL_MONTH = "RAW:총계"
REPORT_REQUIRED = ("run_id", "case_id", "mode", "claims", "narrative", "hypotheses", "review_status", "signal_status",
                   "unresolved_evidence", "policy_version", "snapshot_id", "grouping_version")
REPORT_OPTIONAL = ("report_id", "evidence_ids", "validator_findings", "report_hash", "created_at")
EQUIVALENT_KEY = ("partner_code", "hs_code", "month", "flow", "amount_usd", "net_weight_kg", "observation_status")

PERIOD_RE = re.compile(r"\d{4}(?:0[1-9]|1[0-2])")
HS6_RE = re.compile(r"\d{6}")
PARTNER_RE = re.compile(r"[A-Z]{2}|ALL")
ROWID_RE = re.compile(r"[1-9]\d*")

CODES = {
    "SCHEMA_REPORT": "보고서 키·형식",
    "SCHEMA_CLAIM": "typed claim 필드·형식",
    "SCHEMA_CLAIM_ID": "claim_id 중복·예약어",
    "SCHEMA_STATUS": "판정 상태 값",
    "SCHEMA_SIGNAL_CLAIM": "발동 신호별 주장 요건(계약 §9.4)",
    "NUMERIC_MISMATCH": "검증된 지표 값과 다른 숫자",
    "NUMERIC_UNBACKED": "검증된 지표가 없는 숫자",
    "NUMERIC_NOT_COMPUTABLE": "계산 불가 지표에 적은 숫자",
    "UNIT_MISMATCH": "지표와 맞지 않는 단위",
    "DIRECTION_MISMATCH": "값의 부호와 맞지 않는 방향",
    "REFERENT_MISMATCH": "기간·국가·품목·지표가 가리키는 대상",
    "EVIDENCE_MISSING": "근거 ID 없음",
    "EVIDENCE_FORMAT": "근거 ID 형식(풀림 규칙 1)",
    "EVIDENCE_SNAPSHOT": "근거 ID의 스냅샷(풀림 규칙 2)",
    "EVIDENCE_UNRESOLVED": "풀리지 않는 근거 ID(풀림 규칙 3·4)",
    "EVIDENCE_TOTAL_ROW": "총계 행 근거",
    "EVIDENCE_NOT_SUPPORTING": "주장을 뒷받침하지 않는 근거",
    "PROVENANCE_MISMATCH": "보고서·사례의 출처·버전",
    "PROVENANCE_ENVELOPE": "다른 스냅샷을 조회한 봉투",
    "PROVENANCE_NOT_RETURNED": "이 실행의 도구가 돌려주지 않은 근거",
    "PROVENANCE_REPORT_EVIDENCE": "보고서 근거 목록과 주장 근거의 불일치",
    "STATUS_INCONSISTENT": "허용되지 않는 판정 상태 조합",
    "FORBIDDEN_PHRASE": "금지 문구",
    "PROSE_UNBACKED": "typed claim으로 뒷받침되지 않는 산문 숫자·증감",
}


def run(inp: object) -> object:
    """진입 함수. 보고서를 검사해 사유 목록을 돌려준다. 입력을 바꾸지 않는다."""
    ctx = _context(inp)
    report = inp.get("report")
    out: list[dict] = []
    if not isinstance(report, dict):
        out.append(_f("schema", "SCHEMA_REPORT", "report", None, "보고서가 JSON 객체가 아니다"))
        return {"findings": out}
    out += _report_schema(report)
    claims = report.get("claims") if isinstance(report.get("claims"), list) else []
    valid = _claim_schema(claims, out)
    statuses_ok = _status_schema(report, out)
    out += _signal_claims(valid, ctx.case)
    if statuses_ok:
        out += _status_consistency(report, ctx.case)
    out += _provenance(report, ctx)
    for index, claim in valid:
        out += _claim_checks(index, claim, ctx)
    out += _report_evidence(report, claims)
    fields = _prose_fields(report, claims)
    out += _forbidden(fields)
    out += prose_findings(fields, [c for _, c in valid], ctx)
    return {"findings": out}


def _f(check: str, code: str, path: str, claim_id: object, detail: str) -> dict:
    return {"check": check, "code": code, "path": path, "claim_id": claim_id if isinstance(claim_id, str) else None,
            "detail": detail}


# ---- 입력과 문맥 ---------------------------------------------------------------------------------------------


@dataclass
class Context:
    case: dict
    run: dict
    metrics: dict = field(default_factory=dict)  # (기호, hs6, partner, period) → metric 객체 목록
    returned: set = field(default_factory=set)
    rows: dict = field(default_factory=dict)
    hs_codes: set = field(default_factory=set)
    thresholds: list = field(default_factory=list)
    known_ids: list = field(default_factory=list)
    envelopes: list = field(default_factory=list)


def _context(inp: object) -> Context:
    if not isinstance(inp, dict):
        raise ValueError("R3 입력은 JSON 객체여야 한다")
    case, run_info = inp.get("case"), inp.get("run")
    if not isinstance(case, dict) or not all(isinstance(case.get(k), str) for k in
                                             ("case_id", "hs6", "partner", "month", "baseline_month")):
        raise ValueError("R3 입력의 case에 case_id·hs6·partner·month·baseline_month가 없다")
    signals = case.get("signals")
    if not isinstance(signals, dict) or any(signals.get(s) not in SIGNAL_TRIGGERS for s in SIGNALS):
        raise ValueError("R3 입력의 case.signals가 unit_value·share의 TRIGGERED·NOT_TRIGGERED가 아니다")
    if not isinstance(run_info, dict) or run_info.get("mode") not in MODES or not all(
            isinstance(run_info.get(k), str) for k in ("run_id", "snapshot_id", "policy_version", "grouping_version")):
        raise ValueError("R3 입력의 run에 run_id·mode·snapshot_id·policy_version·grouping_version이 없다")
    envelopes, rows = inp.get("envelopes", []), inp.get("rows", {})
    if not isinstance(envelopes, list) or not all(isinstance(e, dict) for e in envelopes):
        raise ValueError("R3 입력의 envelopes는 객체 목록이어야 한다")
    if not isinstance(rows, dict):
        raise ValueError("R3 입력의 rows는 객체여야 한다")
    ctx = Context(case=case, run=run_info, rows=rows, envelopes=envelopes)
    for envelope in envelopes:
        _collect_returned(envelope, ctx.returned)
        for metric in envelope.get("metrics") or []:
            if isinstance(metric, dict) and isinstance(metric.get("inputs"), dict):
                inputs = metric["inputs"]
                key = (inputs.get("metric"), inputs.get("hs6"), inputs.get("partner"), inputs.get("period"))
                ctx.metrics.setdefault(key, []).append(metric)
    codes = {case["hs6"], case["hs6"][:4]}
    for code in inp.get("hs_codes") or []:
        if isinstance(code, str):
            codes.add(code)
    for row in rows.values():
        if isinstance(row, dict) and isinstance(row.get("hs_code"), str):
            codes.add(row["hs_code"])
    for key in ctx.metrics:
        if isinstance(key[0], str) and "@" in key[0]:
            codes.add(key[0].partition("@")[2])
    ctx.hs_codes = {c for c in codes if c.isdigit() and len(c) in (4, 6, 10)}
    for value in inp.get("thresholds") or []:
        if isinstance(value, (int, Decimal)) and not isinstance(value, bool):
            ctx.thresholds.append(Decimal(value).copy_abs())
    ctx.known_ids = [v for v in (case["case_id"], run_info["run_id"], run_info["snapshot_id"],
                                 run_info["policy_version"], run_info["grouping_version"]) if v]
    return ctx


def _collect_returned(envelope: dict, returned: set) -> None:
    def add(items: object) -> None:
        for item in items if isinstance(items, list) else []:
            if isinstance(item, str):
                returned.add(item)

    add(envelope.get("evidence_ids"))
    for metric in envelope.get("metrics") or []:
        if isinstance(metric, dict):
            add(metric.get("evidence_ids"))
    for entry in envelope.get("missingness") or []:
        if isinstance(entry, dict):
            add(entry.get("evidence_ids"))
            if isinstance(entry.get("evidence_id"), str):
                returned.add(entry["evidence_id"])


# ---- 스키마 검사(모든 모드에서 막는다) --------------------------------------------------------------------------


def _report_schema(report: dict) -> list[dict]:
    out = []
    missing = [k for k in REPORT_REQUIRED if k not in report]
    extra = [k for k in report if k not in REPORT_REQUIRED + REPORT_OPTIONAL]
    if missing:
        out.append(_f("schema", "SCHEMA_REPORT", "report", None, f"필수 키가 없다: {', '.join(missing)}"))
    if extra:
        out.append(_f("schema", "SCHEMA_REPORT", "report", None,
                      f"계약 §9.1에 없는 키가 있다: {', '.join(str(k) for k in extra)}"))
    types = (("claims", list), ("narrative", str), ("hypotheses", list), ("signal_status", dict))
    for key, kind in types:
        if key in report and not isinstance(report[key], kind):
            out.append(_f("schema", "SCHEMA_REPORT", key, None, f"{key}의 형식이 계약과 다르다"))
    if isinstance(report.get("hypotheses"), list) and not all(isinstance(h, str) for h in report["hypotheses"]):
        out.append(_f("schema", "SCHEMA_REPORT", "hypotheses", None, "hypotheses는 문자열 목록이어야 한다"))
    for key in ("run_id", "case_id", "mode", "policy_version", "snapshot_id", "grouping_version"):
        if key in report and not isinstance(report[key], str):
            out.append(_f("schema", "SCHEMA_REPORT", key, None, f"{key}는 문자열이어야 한다"))
    if isinstance(report.get("mode"), str) and report["mode"] not in MODES:
        out.append(_f("schema", "SCHEMA_REPORT", "mode", None, "mode가 네 모드 가운데 하나가 아니다"))
    return out


def _claim_schema(claims: list, out: list) -> list[tuple[int, dict]]:
    """주장마다 형식을 보고 형식이 맞는 주장만 (번호, 주장)으로 돌려준다."""
    valid: list[tuple[int, dict]] = []
    seen: set[str] = set()
    for index, claim in enumerate(claims):
        path = f"claims[{index}]"
        if not isinstance(claim, dict):
            out.append(_f("schema", "SCHEMA_CLAIM", path, None, "주장이 JSON 객체가 아니다"))
            continue
        claim_id = claim.get("claim_id")
        problems = claim_problems(claim)
        for problem in problems:
            out.append(_f("schema", "SCHEMA_CLAIM", f"{path}.{problem[0]}", claim_id, problem[1]))
        if isinstance(claim_id, str):
            if claim_id.startswith("prose:"):
                out.append(_f("schema", "SCHEMA_CLAIM_ID", f"{path}.claim_id", claim_id,
                              "typed claim의 claim_id는 prose:로 시작하지 않는다(계약 §9.2)"))
                problems.append(("claim_id", ""))
            elif claim_id in seen:
                out.append(_f("schema", "SCHEMA_CLAIM_ID", f"{path}.claim_id", claim_id,
                              "claim_id가 보고서 안에서 겹친다(계약 §4.5)"))
                problems.append(("claim_id", ""))
            seen.add(claim_id)
        if not problems:
            valid.append((index, claim))
    return valid


def claim_problems(claim: dict) -> list[tuple[str, str]]:
    """typed claim 한 건의 형식 문제(필드, 설명) 목록. 값의 자릿수는 보지 않는다(룰북 B2)."""
    problems: list[tuple[str, str]] = []
    keys = set(claim)
    if keys != set(CLAIM_FIELDS):
        missing = [k for k in CLAIM_FIELDS if k not in keys]
        extra = sorted(str(k) for k in keys - set(CLAIM_FIELDS))
        detail = "; ".join(p for p in (f"없는 필드 {', '.join(missing)}" if missing else "",
                                       f"계약 밖 필드 {', '.join(extra)}" if extra else "") if p)
        return [("fields", f"typed claim 필드 12개가 아니다({detail})")]
    if not (isinstance(claim["claim_id"], str) and claim["claim_id"]):
        problems.append(("claim_id", "claim_id는 빈 문자열이 아니어야 한다"))
    if claim["claim_type"] not in CLAIM_TYPES:
        problems.append(("claim_type", "claim_type이 계약 §6의 일곱 값이 아니다"))
    if not (isinstance(claim["hs6"], str) and HS6_RE.fullmatch(claim["hs6"])):
        problems.append(("hs6", "hs6는 숫자 6자 문자열이어야 한다"))
    if not (isinstance(claim["partner"], str) and PARTNER_RE.fullmatch(claim["partner"])):
        problems.append(("partner", "partner는 2자리 국가코드나 ALL이어야 한다"))
    if not (isinstance(claim["period"], str) and PERIOD_RE.fullmatch(claim["period"])):
        problems.append(("period", "period는 YYYYMM이어야 한다"))
    baseline = claim["baseline_period"]
    if baseline is not None and not (isinstance(baseline, str) and PERIOD_RE.fullmatch(baseline)):
        problems.append(("baseline_period", "baseline_period는 YYYYMM이나 null이어야 한다"))
    if not (isinstance(claim["metric"], str) and claim["metric"]):
        problems.append(("metric", "metric은 빈 문자열이 아니어야 한다"))
    value = claim["value"]
    if claim["claim_type"] == "data_status":
        if value not in OBSERVATION_STATUSES:
            problems.append(("value", "data_status 주장의 value는 관측 상태 코드(계약 §3.4)여야 한다"))
    elif isinstance(value, float):
        problems.append(("value", "수에 float를 쓰지 않는다(Decimal·int로 적는다)"))
    elif isinstance(value, Decimal) and not value.is_finite():
        problems.append(("value", "NaN이나 무한대는 쓰지 않는다"))
    elif value is not None and not _is_number(value):
        problems.append(("value", "value는 수나 null이어야 한다"))
    if claim["unit"] is not None and not isinstance(claim["unit"], str):
        problems.append(("unit", "unit은 문자열이나 null이어야 한다"))
    if claim["direction"] not in DIRECTIONS:
        problems.append(("direction", "direction이 UP·DOWN·FLAT·NA가 아니다"))
    evidence = claim["evidence_ids"]
    if not isinstance(evidence, list) or not all(isinstance(e, str) for e in evidence):
        problems.append(("evidence_ids", "evidence_ids는 문자열 목록이어야 한다"))
    if not isinstance(claim["text"], str):
        problems.append(("text", "text는 문자열이어야 한다"))
    return problems


def _status_schema(report: dict, out: list) -> bool:
    ok = True
    if "review_status" in report and report["review_status"] not in REVIEW_STATUSES:
        out.append(_f("schema", "SCHEMA_STATUS", "review_status", None,
                      "review_status는 MAINTAIN·MONITOR·HOLD 가운데 하나다(PRE_INVESTIGATION·한국어 표기는 판정 값이 아니다)"))
        ok = False
    signal_status = report.get("signal_status")
    if isinstance(signal_status, dict):
        if set(signal_status) != set(SIGNALS) or any(v not in SIGNAL_STATUSES for v in signal_status.values()):
            out.append(_f("schema", "SCHEMA_STATUS", "signal_status", None,
                          "signal_status는 unit_value·share 두 키에 MAINTAIN·MONITOR·HOLD·NOT_TRIGGERED 값이다"))
            ok = False
    else:
        ok = False
    if "unresolved_evidence" in report and not isinstance(report["unresolved_evidence"], bool):
        out.append(_f("schema", "SCHEMA_STATUS", "unresolved_evidence", None, "unresolved_evidence는 true·false다"))
        ok = False
    return ok and all(k in report for k in ("review_status", "unresolved_evidence"))


def _signal_claims(valid: list[tuple[int, dict]], case: dict) -> list[dict]:
    """계약 §9.4: TRIGGERED인 신호마다 그 계열의 주장이 사례 대상(hs6·대상국·비교월)에 1개 이상 있어야 한다."""
    covered: set[str] = set()
    for _, claim in valid:
        covered |= signal_families(claim, case)
    return [_f("schema", "SCHEMA_SIGNAL_CLAIM", "claims", None,
               f"발동한 신호 {signal}의 계열 주장이 사례 대상에 없다")
            for signal in SIGNALS if case["signals"][signal] == "TRIGGERED" and signal not in covered]


def signal_families(claim: dict, case: dict) -> set[str]:
    """주장이 채우는 신호 계열(계약 §9.4). 비교국 주장, 다른 품목·월, V·Q, OBSERVED 자료 상태는 채우지 않는다."""
    if claim["claim_type"] == "comparison" or claim["hs6"] != case["hs6"] or claim["period"] != case["month"]:
        return set()
    metric = claim["metric"]
    if claim["claim_type"] == "data_status":
        if claim["value"] == "OBSERVED" or not metric.startswith("observation_status"):
            return set()
        if claim["partner"] == "ALL":
            return {"share"}
        if claim["partner"] == case["partner"]:
            return {"unit_value"} if "@" in metric else {"unit_value", "share"}
        return set()
    if claim["partner"] != case["partner"]:
        return set()
    base = base_symbol(metric)
    if base in UNIT_VALUE_BASES:
        return {"unit_value"}
    if base in SHARE_BASES:
        return {"share"}
    return set()


# ---- 검증기 검사(freeform에서는 기록만) ----------------------------------------------------------------------


def _status_consistency(report: dict, case: dict) -> list[dict]:
    """허용 상태: 발동하지 않은 신호는 NOT_TRIGGERED, 사례 상태는 MAINTAIN > HOLD > MONITOR 집계, unresolved_evidence는
    MAINTAIN과 HOLD가 섞일 때만 true다(계약 §3.1). 틀린 상태를 고치지 않고 사유만 적는다."""
    out = []
    signal_status = report["signal_status"]
    triggered = []
    for signal in SIGNALS:
        stated, trigger = signal_status[signal], case["signals"][signal]
        if trigger == "NOT_TRIGGERED" and stated != "NOT_TRIGGERED":
            out.append(_f("validator", "STATUS_INCONSISTENT", f"signal_status.{signal}", None,
                          f"발동하지 않은 신호의 판정은 NOT_TRIGGERED여야 한다(적힌 값 {stated})"))
        if trigger == "TRIGGERED":
            if stated == "NOT_TRIGGERED":
                out.append(_f("validator", "STATUS_INCONSISTENT", f"signal_status.{signal}", None,
                              "발동한 신호의 판정이 NOT_TRIGGERED다"))
            else:
                triggered.append(stated)
    if not triggered:
        return out
    expected = "MAINTAIN" if "MAINTAIN" in triggered else "HOLD" if "HOLD" in triggered else "MONITOR"
    if report["review_status"] != expected:
        out.append(_f("validator", "STATUS_INCONSISTENT", "review_status", None,
                      f"신호별 판정의 집계(MAINTAIN > HOLD > MONITOR)는 {expected}다. 적힌 값: {report['review_status']}"))
    unresolved = "MAINTAIN" in triggered and "HOLD" in triggered
    if report["unresolved_evidence"] is not unresolved:
        out.append(_f("validator", "STATUS_INCONSISTENT", "unresolved_evidence", None,
                      f"MAINTAIN과 HOLD가 섞일 때만 true다. 이 신호별 판정에서는 {str(unresolved).lower()}가 맞다"))
    return out


def _provenance(report: dict, ctx: Context) -> list[dict]:
    """출처: 보고서의 실행·사례·모드·스냅샷·정책·비교 대상 버전이 이 실행과 같고, 봉투가 같은 스냅샷을 조회했는가."""
    out = []
    expected = {"run_id": ctx.run["run_id"], "case_id": ctx.case["case_id"], "mode": ctx.run["mode"],
                "snapshot_id": ctx.run["snapshot_id"], "policy_version": ctx.run["policy_version"],
                "grouping_version": ctx.run["grouping_version"]}
    for key, want in expected.items():
        if key in report and report[key] != want:
            out.append(_f("validator", "PROVENANCE_MISMATCH", key, None,
                          f"보고서의 {key}가 이 실행의 값({want})과 다르다"))
    for key in ("snapshot_id", "policy_version"):
        if key in ctx.case and ctx.case[key] != ctx.run[key]:
            out.append(_f("validator", "PROVENANCE_MISMATCH", f"case.{key}", None,
                          f"사례의 {key}가 이 실행의 값({ctx.run[key]})과 다르다"))
    for number, envelope in enumerate(ctx.envelopes):
        if envelope.get("snapshot_id") != ctx.run["snapshot_id"]:
            out.append(_f("validator", "PROVENANCE_ENVELOPE", f"envelopes[{number}]", None,
                          f"도구 봉투의 snapshot_id가 이 실행의 스냅샷({ctx.run['snapshot_id']})과 다르다"))
    return out


def _report_evidence(report: dict, claims: list) -> list[dict]:
    evidence = report.get("evidence_ids")
    if evidence is None:
        return []
    used = {e for c in claims if isinstance(c, dict) and isinstance(c.get("evidence_ids"), list)
            for e in c["evidence_ids"] if isinstance(e, str)}
    if not isinstance(evidence, list) or set(e for e in evidence if isinstance(e, str)) != used:
        return [_f("validator", "PROVENANCE_REPORT_EVIDENCE", "evidence_ids", None,
                   "보고서의 evidence_ids가 주장들의 근거 전체와 같지 않다(계약 §9.1)")]
    return []


def _claim_checks(index: int, claim: dict, ctx: Context) -> list[dict]:
    path, claim_id = f"claims[{index}]", claim["claim_id"]
    out: list[dict] = []
    resolved = _evidence_checks(path, claim, ctx, out)
    if claim["claim_type"] == "data_status":
        _data_status_checks(path, claim, ctx, resolved, out)
        return out
    base = base_symbol(claim["metric"])
    if base is None:
        out.append(_f("validator", "REFERENT_MISMATCH", f"{path}.metric", claim_id,
                      f"정의하지 않은 지표 기호다({claim['metric']}). 계약 §6.2·§11.2의 기호만 쓴다"))
        return out
    _referent_checks(path, claim, base, ctx, out)
    if claim["unit"] != UNIT_OF[base]:
        out.append(_f("validator", "UNIT_MISMATCH", f"{path}.unit", claim_id,
                      f"{claim['metric']}의 단위는 {UNIT_OF[base]}다(적힌 단위 {claim['unit']})"))
    candidates = _matching_metrics(claim, base, ctx)
    matched = _numeric_checks(path, claim, base, candidates, out)
    _direction_checks(path, claim, base, matched or (candidates[0] if candidates else None), out)
    if matched is not None:
        _support_checks(path, claim, matched, ctx, resolved, out)
    return out


def _referent_checks(path: str, claim: dict, base: str, ctx: Context, out: list) -> None:
    claim_id, claim_type = claim["claim_id"], claim["claim_type"]
    if claim_type != "comparison" and base not in TYPE_BASES[claim_type]:
        out.append(_f("validator", "REFERENT_MISMATCH", f"{path}.claim_type", claim_id,
                      f"claim_type {claim_type}에 쓰지 않는 지표({claim['metric']})다(계약 §6.2)"))
    if claim["hs6"] != ctx.case["hs6"]:
        out.append(_f("validator", "REFERENT_MISMATCH", f"{path}.hs6", claim_id,
                      f"사례 품목({ctx.case['hs6']})이 아닌 품목을 가리킨다"))
    peer = claim["partner"] not in (ctx.case["partner"], "ALL")
    if claim_type == "comparison" and not peer:
        out.append(_f("validator", "REFERENT_MISMATCH", f"{path}.partner", claim_id,
                      "comparison 주장의 partner는 비교국이어야 한다(계약 §6.2)"))
    if claim_type != "comparison" and peer:
        out.append(_f("validator", "REFERENT_MISMATCH", f"{path}.partner", claim_id,
                      "비교국의 값·변화는 comparison 주장으로 쓴다(계약 §6.2)"))
    if base in CHANGE_BASES:
        want = month_minus_12(claim["period"])
        if claim["baseline_period"] != want:
            out.append(_f("validator", "REFERENT_MISMATCH", f"{path}.baseline_period", claim_id,
                          f"전년동월 지표의 기준월은 비교월의 12개월 전({want})이어야 한다"))
    elif claim["baseline_period"] is not None:
        out.append(_f("validator", "REFERENT_MISMATCH", f"{path}.baseline_period", claim_id,
                      "변화를 말하지 않는 주장의 baseline_period는 null이다(계약 §6.1)"))


def _matching_metrics(claim: dict, base: str, ctx: Context) -> list[dict]:
    found = ctx.metrics.get((claim["metric"], claim["hs6"], claim["partner"], claim["period"]), [])
    if base in CHANGE_BASES:
        found = [m for m in found if m["inputs"].get("baseline_period") == claim["baseline_period"]]
    return [m for m in found if m.get("value") is None or _is_number(m.get("value"))]


def _numeric_checks(path: str, claim: dict, base: str, candidates: list, out: list) -> dict | None:
    """숫자: 주장 값이 검증된 지표 값과 같은가(룰북 B3-1 값 비교). 짝이 된 지표를 돌려준다."""
    claim_id, value = claim["claim_id"], claim["value"]
    if not candidates:
        out.append(_f("validator", "NUMERIC_UNBACKED", f"{path}.value", claim_id,
                      "이 실행의 도구가 돌려준 검증된 지표 가운데 이 주장의 대상과 같은 지표가 없다"))
        return None
    for metric in candidates:
        expected = metric.get("value")
        if value is None and expected is None:
            return metric
        if value is not None and expected is not None and value_matches(value, expected, base):
            return metric
    if value is not None and all(m.get("value") is None for m in candidates):
        out.append(_f("validator", "NUMERIC_NOT_COMPUTABLE", f"{path}.value", claim_id,
                      "검증된 지표가 계산 불가(null)인데 숫자를 적었다. 계산 불가는 data_status 주장으로 쓴다"))
        return None
    expected = next(m["value"] for m in candidates if m.get("value") is not None)
    shown = "null" if value is None else format(value, "f") if isinstance(value, Decimal) else str(value)
    out.append(_f("validator", "NUMERIC_MISMATCH", f"{path}.value", claim_id,
                  f"검증된 지표 값과 다르다. 적힌 값: {shown}, 같은 자리의 지표 값: {_expected_text(expected, value, base)}"))
    return None


def _expected_text(expected: object, value: object, base: str) -> str:
    if not _is_number(expected):
        return "null"
    places = DIGITS_OF[base] if value is None else min(shown_places(value), DIGITS_OF[base])
    return format(round_at(Decimal(expected), places), "f")


def value_matches(reported: object, expected: object, base: str) -> bool:
    """룰북 B3-1 값 비교: 기대값을 보고값이 보인 소수 자리수로 반올림해 같으면 일치. 보고값이 계약 자릿수보다
    자리가 많으면 둘 다 계약 자릿수로 반올림해 비교한다. 반올림은 Decimal ROUND_HALF_UP이다."""
    if not (_is_number(reported) and _is_number(expected)):
        return False
    places, contract = shown_places(reported), DIGITS_OF[base]
    got, want = Decimal(reported), Decimal(expected)
    if places > contract:
        return round_at(got, contract) == round_at(want, contract)
    return round_at(want, places) == got


def _direction_checks(path: str, claim: dict, base: str, metric: dict | None, out: list) -> None:
    claim_id, direction, value = claim["claim_id"], claim["direction"], claim["value"]
    if base not in CHANGE_BASES:
        if direction != "NA":
            out.append(_f("validator", "DIRECTION_MISMATCH", f"{path}.direction", claim_id,
                          "변화를 말하지 않는 주장의 direction은 NA다(계약 §6.2)"))
        return
    if direction == "NA":
        out.append(_f("validator", "DIRECTION_MISMATCH", f"{path}.direction", claim_id,
                      "변화 주장의 direction은 UP·DOWN·FLAT 가운데 하나다"))
        return
    if not _is_number(value):
        return
    allowed = {_sign_direction(Decimal(value))}
    if Decimal(value) == 0 and metric is not None and _is_number(metric.get("value")):
        allowed.add(_sign_direction(Decimal(metric["value"])))  # 반올림해 0이면 FLAT과 실제 부호 모두 맞다(룰북 B3-1)
    if direction not in allowed:
        out.append(_f("validator", "DIRECTION_MISMATCH", f"{path}.direction", claim_id,
                      f"값의 부호로 본 방향은 {'·'.join(sorted(allowed))}다. 적힌 방향: {direction}"))


def _sign_direction(value: Decimal) -> str:
    return "UP" if value > 0 else "DOWN" if value < 0 else "FLAT"


def _evidence_checks(path: str, claim: dict, ctx: Context, out: list) -> list[tuple[str, dict]]:
    """근거 ID마다 형식(풀림 규칙 1) → 스냅샷(규칙 2) → 행(규칙 3·4) → 총계 행 → 출처 순으로 본다."""
    claim_id, evidence = claim["claim_id"], claim["evidence_ids"]
    if not evidence:
        out.append(_f("validator", "EVIDENCE_MISSING", f"{path}.evidence_ids", claim_id, "근거 ID가 없다"))
        return []
    resolved: list[tuple[str, dict]] = []
    for number, evidence_id in enumerate(evidence):
        where = f"{path}.evidence_ids[{number}]"
        parts = evidence_id.split(":")
        if len(parts) != 4 or parts[0] != "ev" or not parts[1] or not parts[2] or not ROWID_RE.fullmatch(parts[3]):
            out.append(_f("validator", "EVIDENCE_FORMAT", where, claim_id,
                          "근거 ID는 ev:<snapshot_id>:<table>:<rowid> 형식이다(풀림 규칙 1)"))
            continue
        if parts[1] != ctx.run["snapshot_id"]:
            out.append(_f("validator", "EVIDENCE_SNAPSHOT", where, claim_id,
                          f"근거 ID의 스냅샷이 이 실행의 스냅샷({ctx.run['snapshot_id']})과 다르다(풀림 규칙 2)"))
            continue
        row = ctx.rows.get(evidence_id)
        if not isinstance(row, dict):
            out.append(_f("validator", "EVIDENCE_UNRESOLVED", where, claim_id,
                          "스냅샷에서 이 근거 ID의 테이블·행을 찾지 못했다(풀림 규칙 3·4)"))
            continue
        if row.get("month") == TOTAL_MONTH:
            out.append(_f("validator", "EVIDENCE_TOTAL_ROW", where, claim_id,
                          "총계 행(RAW:총계)은 근거가 될 수 없다(계약 §4.4)"))
            continue
        if evidence_id not in ctx.returned:
            out.append(_f("validator", "PROVENANCE_NOT_RETURNED", where, claim_id,
                          "이 실행의 도구가 돌려준 근거가 아니다"))
        resolved.append((evidence_id, row))
    return resolved


def _support_checks(path: str, claim: dict, metric: dict, ctx: Context, resolved: list, out: list) -> None:
    """원본 행: 주장의 근거가 짝이 된 지표의 계산 행을 모두(동등한 행 포함) 담는가(룰북 B3-1 근거 검사)."""
    cited = {evidence_id for evidence_id, _ in resolved}
    cited_keys = {_equivalence(evidence_id, row) for evidence_id, row in resolved}
    missing = []
    for needed in metric.get("evidence_ids") or []:
        if not isinstance(needed, str) or needed in cited:
            continue
        row = ctx.rows.get(needed)
        key = _equivalence(needed, row) if isinstance(row, dict) else None
        if key is None or key not in cited_keys:
            missing.append(needed)
    if missing:
        out.append(_f("validator", "EVIDENCE_NOT_SUPPORTING", f"{path}.evidence_ids", claim["claim_id"],
                      f"검증된 지표의 계산 행을 모두 인용하지 않았다(빠진 근거 {len(missing)}개)"))


def _equivalence(evidence_id: str, row: dict) -> tuple | None:
    """동등한 행을 가르는 키. 비교 열이 하나라도 없으면 근거 ID 자체로만 같다고 본다."""
    if not all(k in row for k in EQUIVALENT_KEY):
        return ("id", evidence_id)
    table = evidence_id.split(":")[2] if evidence_id.count(":") == 3 else ""
    return (table,) + tuple(str(row[k]) for k in EQUIVALENT_KEY)


def _data_status_checks(path: str, claim: dict, ctx: Context, resolved: list, out: list) -> None:
    claim_id, metric = claim["claim_id"], claim["metric"]
    base, at, code = metric.partition("@")
    if base != "observation_status" or (at and not code):
        out.append(_f("validator", "REFERENT_MISMATCH", f"{path}.metric", claim_id,
                      "data_status 주장의 metric은 observation_status나 observation_status@<HS10 코드>다"))
        return
    if claim["unit"] is not None:
        out.append(_f("validator", "UNIT_MISMATCH", f"{path}.unit", claim_id, "data_status 주장의 unit은 null이다"))
    if claim["direction"] != "NA":
        out.append(_f("validator", "DIRECTION_MISMATCH", f"{path}.direction", claim_id,
                      "data_status 주장의 direction은 NA다"))
    if claim["hs6"] != ctx.case["hs6"]:
        out.append(_f("validator", "REFERENT_MISMATCH", f"{path}.hs6", claim_id,
                      f"사례 품목({ctx.case['hs6']})이 아닌 품목을 가리킨다"))
    if not resolved:
        return
    for _, row in resolved:
        hs_code = row.get("hs_code")
        same_item = hs_code == code if at else isinstance(hs_code, str) and hs_code.startswith(claim["hs6"])
        if (row.get("observation_status") == claim["value"] and row.get("partner_code") == claim["partner"]
                and row.get("month") == claim["period"] and same_item):
            return
    out.append(_f("validator", "EVIDENCE_NOT_SUPPORTING", f"{path}.evidence_ids", claim_id,
                  f"인용한 행 가운데 이 대상의 관측 상태가 {claim['value']}인 행이 없다"))


# ---- 금지 문구 ----------------------------------------------------------------------------------------------
# 자료 계약 §6.3·개발 플랜 §12.2: 단가·점유율 변화를 부정·위법·원산지 조작(우회수입 포함)·개별 거래가격의 증거로
# 쓰지 않고, 경보 해소를 "정상 확정"으로 쓰지 않는다. 뜻을 가리지 않고 낱말이 나오면 사유로 적는다(부정문 포함).
FORBIDDEN_PHRASES = (
    "부정 거래", "부정거래", "부정 수입", "부정수입", "부정 행위", "부정행위", "불법", "위법", "탈세", "탈루", "밀수",
    "사기 거래", "사기거래", "범죄", "혐의", "관세법 위반", "법 위반", "법률 위반",
    "원산지 조작", "원산지를 조작", "원산지 세탁", "원산지 위장", "원산지 둔갑", "원산지 속임",
    "우회수입", "우회 수입", "우회수출", "우회 수출", "저가 신고", "저가신고", "과소 신고", "과소신고", "허위 신고",
    "허위신고", "가격 조작", "개별 거래가격", "개별 거래 가격", "개별 거래의 가격", "덤핑",
    "정상 확정", "정상으로 확정", "정상 거래로 확인", "정상 거래임이 확인",
)
FORBIDDEN_LATIN = ("fraud", "illegal", "smuggl", "circumvent", "dumping", "tax evasion")


def _prose_fields(report: dict, claims: list) -> list[tuple[str, str]]:
    """산문 검사 대상 필드(룰북 B3-2 적용 범위): narrative, hypotheses[i], claims[i].text."""
    fields = []
    if isinstance(report.get("narrative"), str):
        fields.append(("narrative", report["narrative"]))
    if isinstance(report.get("hypotheses"), list):
        fields += [(f"hypotheses[{i}]", h) for i, h in enumerate(report["hypotheses"]) if isinstance(h, str)]
    for i, claim in enumerate(claims):
        if isinstance(claim, dict) and isinstance(claim.get("text"), str):
            fields.append((f"claims[{i}].text", claim["text"]))
    return [(path, unicodedata.normalize("NFC", text)) for path, text in fields]


def _forbidden(fields: list[tuple[str, str]]) -> list[dict]:
    out = []
    for path, text in fields:
        flat = re.sub(r"\s+", " ", text)
        lower = flat.lower()
        hits = [p for p in FORBIDDEN_PHRASES if p in flat] + [p for p in FORBIDDEN_LATIN if p in lower]
        hits = [p for p in hits if not any(p != q and p in q for q in hits)]  # "관세법 위반" 안의 "법 위반"은 한 번만
        for phrase in hits:
            out.append(_f("validator", "FORBIDDEN_PHRASE", path, None,
                          f"금지 문구를 썼다: '{phrase}'. 보고서는 담당자의 다음 업무만 제시한다(계약 §6.3)"))
    return out


# ---- 산문 패턴(룰북 B3-2) -----------------------------------------------------------------------------------

NUMBER_RE = re.compile(r"(?<![A-Za-z0-9_.])(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")
SIGNS = {"-": -1, "−": -1, "△": -1, "▼": -1, "+": 1, "▲": 1}
MULTIPLIERS = (("천만", Decimal(10) ** 7), ("백만", Decimal(10) ** 6), ("천", Decimal(10) ** 3),
               ("만", Decimal(10) ** 4), ("억", Decimal(10) ** 8))
UNIT_PATTERNS = (  # 순서가 뜻이다: %p·pp가 %보다 먼저(PT-2가 PT-1보다 먼저), 달러/kg가 달러보다 먼저
    (re.compile(r"\s?(?:%\s?p(?![A-Za-z])|%\s?P(?![A-Za-z])|%\s?포인트|퍼센트\s?포인트|pp(?![A-Za-z]))"), "pp"),
    (re.compile(r"\s?(?:%|퍼센트)"), "pct"),
    (re.compile(r"\s?(?:USD\s?/\s?kg|US\$\s?/\s?kg|\$\s?/\s?kg|달러\s?/\s?kg)"), "usd_per_kg"),
    (re.compile(r"\s?(?:USD|US\$|\$|달러)(?![A-Za-z])"), "usd"),
    (re.compile(r"\s?(?:kg|킬로그램)(?![A-Za-z])"), "kg"),
    (re.compile(r"\s?톤"), "ton"),
    (re.compile(r"\s?배"), "multiple"),
)
PREFIX_USD_RE = re.compile(r"(?:US\$|USD|\$)\s?$")
PREFIX_PER_KG_RE = re.compile(r"kg당\s?$")
APPROX_BEFORE_RE = re.compile(r"(?:약|대략|거의)\s?$")
APPROX_AFTER_RE = re.compile(r"\s?(?:가량|쯤|안팎|내외|정도|남짓)")
BOUND_RE = re.compile(r"\s?(?:을|를|이|가|은|는|도)?\s?(이상|넘게|초과|웃도는|미만|이하|밑도는)")
RATE_NAME_RE = re.compile(r"(증가율|상승률|감소율|하락률)\s?(?:은|는|이|가|을|를|도)?\s?(?:약|대략|거의)?\s?$")
THRESHOLD_NAME_RE = re.compile(r"(?:기준값|기준|임계값|임계)\s?(?:인|은|는|이|가|을|를|의|도)?\s?$")
WORD_MULTIPLES = (("다섯 배", Decimal(5), 0), ("다섯배", Decimal(5), 0), ("두 배", Decimal(2), 0),
                  ("두배", Decimal(2), 0), ("세 배", Decimal(3), 0), ("세배", Decimal(3), 0),
                  ("네 배", Decimal(4), 0), ("네배", Decimal(4), 0), ("절반", Decimal("0.5"), 1),
                  ("반토막", Decimal("0.5"), 1))

EXCLUDE_RES = (
    # EX-1 날짜·기간("N개월 연속"은 빼지 않는다)
    re.compile(r"\d{1,4}\s?년(?:\s?\d{1,2}\s?월)?(?:\s?\d{1,2}\s?일)?"),
    re.compile(r"\d{1,2}\s?월(?:\s?\d{1,2}\s?일)?"),
    re.compile(r"(?<!\d)(?:19|20)\d{2}\s?[-./]\s?(?:1[0-2]|0?[1-9])(?:\s?[-./]\s?\d{1,2})?(?!\d)"),
    re.compile(r"(?<!\d)(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?!\d)"),
    re.compile(r"\d\s?분기"),
    re.compile(r"\d+\s?개월(?!\s?연속)"),
    re.compile(r"\d{1,2}\s?일"),
    # EX-2 품목 식별(HS와 함께 쓴 숫자, 류·호 표기). HS 코드 집합의 숫자는 아래 CODE_TOKEN_RE로 따로 본다
    re.compile(r"(?<![A-Za-z])[Hh][Ss]\s?[-:]?\s?\d+(?:[.\-]\d+)*"),
    re.compile(r"제\s?\d+\s?(?:류|호)"),
    re.compile(r"\d+\s?(?:류|호)"),
    # EX-3 식별자·버전(근거 ID, 라틴 문자와 숫자가 섞인 이름: policy_v1, RB-1, g1, kcs_202201_202412_v2 등)
    re.compile(r"ev:[^\s,;)\]]+"),
    # EX-4 목록 번호와 조사 과정·구조의 개수
    re.compile(r"(?m)^\s*\d+[.)](?=\s)"),
    re.compile(r"\d+\s?(?:회|번째|단계|차례)"),
    re.compile(r"(?:신호|도구|호출)\s?\d+\s?(?:개|종|가지|회|번)"),
    re.compile(r"\d+\s?(?:개|종|가지)의?\s?(?:신호|도구)"),
)
IDENT_RE = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]*(?:[-.:][A-Za-z0-9_]+)*")
CODE_TOKEN_RE = re.compile(r"(?<![\d.,])\d[\d.\-]*\d(?!\d)")

UP_WORDS = ("증가", "상승", "급증", "급등", "폭등", "치솟", "반등", "확대", "늘었", "늘어", "늘며", "늘고",
            "오르", "올라", "오른", "올랐", "높아지", "높아졌", "높아진")
DOWN_WORDS = ("감소", "하락", "급감", "급락", "폭락", "반토막", "축소", "줄었", "줄어", "줄며", "줄고",
              "떨어지", "떨어졌", "떨어진", "떨어져", "내렸", "낮아지", "낮아졌", "낮아진")
FLAT_WORDS = ("보합", "변화가 없", "변동이 없", "변함없", "제자리")
CHANGE_WORD_RE = re.compile("|".join(re.escape(w) for w in sorted(UP_WORDS + DOWN_WORDS + FLAT_WORDS,
                                                                 key=len, reverse=True)))
NEGATION_RE = re.compile(r"[가-힣]{0,3}\s?(?:지\s?않|지는\s?않|지\s?못|지는\s?못)")
PRICE_SUBJECT_RE = re.compile(r"(?:단가|가격|값|금액)\s?(?:이|가|은|는)\s?$")


@dataclass
class NumberExpr:
    """산문에서 잡은 숫자 표현 하나."""
    start: int
    end: int
    magnitude: Decimal  # 부호 없는 크기(표현의 단위와 배수 그대로)
    places: int  # 보인 소수 자리(근사어면 끝자리 0을 빼고 센 자리, 음수면 십의 자리 이상)
    sign: int  # -1·+1, 부호가 없으면 0
    unit: str | None  # pct·pp·usd·usd_per_kg·kg·ton·multiple, 단위 없는 숫자는 None
    scale: Decimal = Decimal(1)  # 천·만·백만·억
    interval: bool = False  # "N%대"
    bound: str | None = None  # ge(이상·넘게·초과·웃도는) 또는 le(미만·이하·밑도는)

    @property
    def signed(self) -> Decimal:
        return self.magnitude if self.sign >= 0 else -self.magnitude


def prose_findings(fields: list[tuple[str, str]], claims: list[dict], ctx: Context) -> list[dict]:
    """룰북 B3-2: 자유 문장 필드의 숫자·증감 표현이 같은 보고서의 typed claim으로 뒷받침되는가."""
    numeric = [c for c in claims if _is_number(c["value"])]
    directions = {c["direction"] for c in claims if c["direction"] in ("UP", "DOWN", "FLAT")}
    out = []
    for path, text in fields:
        spans = excluded_spans(text, ctx)
        numbers = scan_numbers(text, spans, ctx)
        for expr in numbers:
            kind = "PT-4" if expr.unit == "multiple" else _number_kind(expr.unit)
            if not number_backed(expr, numeric):
                out.append(_prose(path, kind, text[expr.start:expr.end]))
        for start, end, value, places in _word_multiples(text, spans):
            if not _multiple_backed(value, places, numeric):
                out.append(_prose(path, "PT-4", text[start:end]))
        for first, second in _from_to_pairs(text, numbers):
            if not _from_to_backed(first, second, numeric, directions):
                out.append(_prose(path, "PT-8", text[first.start:second.end]))
        for start, end, direction, negated in change_words(text, spans):
            wanted = {direction} if not negated else {"UP", "DOWN", "FLAT"} - {direction}
            if not wanted & directions:
                out.append(_prose(path, "PT-6", text[start:end]))
    return out


def _prose(path: str, kind: str, snippet: str) -> dict:
    return _f("validator", "PROSE_UNBACKED", path, None,
              f"{kind} 표현 '{snippet}': 같은 보고서의 typed claim으로 뒷받침되지 않는다(룰북 B3-2)")


def _number_kind(unit: str | None) -> str:
    return {"pct": "PT-1", "pp": "PT-2", "usd": "PT-3", "usd_per_kg": "PT-3", "kg": "PT-3", "ton": "PT-3"}.get(
        unit or "", "PT-5")


def excluded_spans(text: str, ctx: Context) -> list[tuple[int, int]]:
    """EX-1~EX-4로 빼는 구간. EX-5(임계값)와 EX-6(지표 이름)은 숫자를 읽을 때 따로 본다."""
    spans = [m.span() for rx in EXCLUDE_RES for m in rx.finditer(text)]
    spans += [m.span() for m in IDENT_RE.finditer(text) if any(ch.isdigit() for ch in m.group())]
    spans += [m.span() for m in CODE_TOKEN_RE.finditer(text) if re.sub(r"[.\-]", "", m.group()) in ctx.hs_codes]
    for ident in ctx.known_ids:
        spans += [m.span() for m in re.finditer(re.escape(ident), text)]
    return spans


def _overlaps(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    return any(start < b and a < end for a, b in spans)


def scan_numbers(text: str, spans: list[tuple[int, int]], ctx: Context) -> list[NumberExpr]:
    """숫자 표현을 앞에서부터 읽는다(부호, 앞 단위, 배수, 뒤 단위, 근사어, %대, 부등식, 지표 이름의 부호)."""
    found = []
    for m in NUMBER_RE.finditer(text):
        if _overlaps(m.start(), m.end(), spans):
            continue
        start, sign = m.start(), 0
        if start > 0 and text[start - 1] in SIGNS:
            start, sign = start - 1, SIGNS[text[start - 1]]
        elif start > 1 and text[start - 1] == " " and text[start - 2] in "△▲▼":
            start, sign = start - 2, SIGNS[text[start - 2]]
        before = text[:start]
        prefix = None
        if PREFIX_USD_RE.search(before):
            prefix, start = "usd", PREFIX_USD_RE.search(before).start()
        elif PREFIX_PER_KG_RE.search(before):
            prefix, start = "per_kg", PREFIX_PER_KG_RE.search(before).start()
        before = text[:start]
        approx = bool(APPROX_BEFORE_RE.search(before))
        pos, scale = m.end(), Decimal(1)
        for word, factor in MULTIPLIERS:
            if text.startswith(word, pos):
                pos, scale = pos + len(word), factor
                break
        unit = None
        for rx, name in UNIT_PATTERNS:
            unit_match = rx.match(text, pos)
            if unit_match:
                unit, pos = name, unit_match.end()
                break
        if prefix == "usd" and unit is None:
            unit = "usd"
        if prefix == "per_kg" and unit in (None, "usd"):
            unit = "usd_per_kg"
        rest = text[pos:]
        interval = unit == "pct" and rest.startswith("대") and not rest.startswith("대비")
        approx = approx or bool(APPROX_AFTER_RE.match(rest))
        bound_match = BOUND_RE.match(rest)
        bound = None
        if bound_match:
            bound = "ge" if bound_match.group(1) in ("이상", "넘게", "초과", "웃도는") else "le"
        digits = m.group().replace(",", "")
        magnitude = Decimal(digits)
        rate = RATE_NAME_RE.search(before)
        if rate:
            reverse = rate.group(1) in ("감소율", "하락률")
            sign = (-sign if sign else -1) if reverse else (sign or 1)
        if ctx.thresholds and THRESHOLD_NAME_RE.search(before) and magnitude in ctx.thresholds:
            continue  # EX-5: 기준·임계값 바로 뒤의 정책 탐지 임계값
        found.append(NumberExpr(start=start, end=pos, magnitude=magnitude, places=_text_places(digits, approx),
                                sign=sign, unit=unit, scale=scale, interval=interval, bound=bound))
    return found


def _text_places(digits: str, approx: bool) -> int:
    """보인 소수 자리. 근사어가 붙으면 끝자리의 0은 자릿수로 치지 않는다("약 40"은 십의 자리 = -1)."""
    whole, _, fraction = digits.partition(".")
    places = len(fraction)
    if approx:
        joined = whole + fraction
        stripped = joined.rstrip("0")
        if stripped:
            places -= len(joined) - len(stripped)
    return places


def shown_places(value: object) -> int:
    """저장된 수의 보인 소수 자리(끝자리 0 포함). int는 0이다."""
    if isinstance(value, Decimal):
        exponent = value.as_tuple().exponent
        return -exponent if isinstance(exponent, int) else 0
    return 0


def round_at(value: Decimal, places: int) -> Decimal:
    return value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def _compatible(unit: str | None, claim_unit: object) -> bool:
    return {None: True, "pct": claim_unit == "%", "pp": claim_unit == "pp",
            "usd": claim_unit in ("USD", "USD/kg"), "usd_per_kg": claim_unit == "USD/kg",
            "kg": claim_unit == "kg", "ton": claim_unit == "kg"}.get(unit, False)


def number_backed(expr: NumberExpr, numeric: list[dict]) -> bool:
    """숫자(PT-1~PT-5): 같은 보고서의 단위가 호환되는 typed claim 값 하나와 같으면 뒷받침된다."""
    if expr.unit == "multiple":
        return _multiple_backed(expr.magnitude, expr.places, numeric)
    return any(_claim_backs(expr, c) for c in numeric if _compatible(expr.unit, c["unit"]))


def _claim_backs(expr: NumberExpr, claim: dict) -> bool:
    factor = expr.scale * (Decimal(1000) if expr.unit == "ton" else Decimal(1))
    value = Decimal(claim["value"]) / factor  # 표현의 단위(톤·만 등)로 바꾼 주장 값
    if expr.interval:
        width = Decimal(1).scaleb(-_text_places(format(expr.magnitude, "f"), True))
        return expr.magnitude <= abs(value) < expr.magnitude + width
    if expr.bound:
        got, want = (value, expr.signed) if expr.sign else (abs(value), expr.magnitude)
        return got >= want if expr.bound == "ge" else got <= want
    base = base_symbol(claim["metric"])
    contract = DIGITS_OF[base] if base else shown_places(claim["value"])
    scale_places = len(str(int(factor))) - 1  # 10의 몇 제곱인가(1000 → 3)
    if expr.places - scale_places > contract:  # 산문이 계약 자릿수보다 자리가 많으면 계약 자릿수에서 비교한다
        got = round_at(Decimal(claim["value"]), contract)
        want = round_at(expr.signed * factor, contract)
    else:
        got, want = round_at(value, expr.places), expr.signed
    if expr.sign:
        return got == want  # 부호가 있으면 부호까지 비교한다
    return abs(got) == abs(want)  # 부호가 없으면 절댓값을 비교한다


def _multiple_backed(value: Decimal, places: int, numeric: list[dict]) -> bool:
    """배수(PT-4): r_U 주장을 비율 k = 1 + r_U/100으로 바꿔 보인 자리에서 반올림해 같으면 뒷받침된다."""
    for claim in numeric:
        if claim["metric"] == "r_U" and round_at(1 + Decimal(claim["value"]) / 100, places) == value:
            return True
    return False


def _word_multiples(text: str, spans: list[tuple[int, int]]) -> list[tuple[int, int, Decimal, int]]:
    found = []
    taken: list[tuple[int, int]] = []
    for word, value, places in WORD_MULTIPLES:
        for m in re.finditer(re.escape(word), text):
            if not _overlaps(m.start(), m.end(), spans + taken):
                taken.append(m.span())
                found.append((m.start(), m.end(), value, places))
    return sorted(found)


def _from_to_pairs(text: str, numbers: list[NumberExpr]) -> list[tuple[NumberExpr, NumberExpr]]:
    """PT-8 "X에서 Y로": 이웃한 두 숫자 표현 사이가 "에서"이고 뒤 표현 다음이 "로·으로"인 꼴."""
    pairs = []
    for first, second in zip(numbers, numbers[1:]):
        if re.fullmatch(r"\s?에서\s?", text[first.end:second.start]) and re.match(r"\s?(?:으로|로)", text[second.end:]):
            pairs.append((first, second))
    return pairs


def _from_to_backed(first: NumberExpr, second: NumberExpr, numeric: list[dict], directions: set) -> bool:
    """PT-8: 방향(오름·내림·그대로)의 주장이 있고, 같은 hs6·partner·metric의 수준 주장 짝이 있으면 그중 하나는
    X 쪽 기간이 Y 쪽보다 앞서야 한다(룰북 B3-2 짝 규칙)."""
    x, y = first.signed, second.signed
    direction = "UP" if y > x else "DOWN" if y < x else "FLAT"
    if direction not in directions:
        return False
    level = [c for c in numeric if base_symbol(c["metric"]) not in CHANGE_BASES and c["claim_type"] != "data_status"]
    backs_x = [c for c in level if _compatible(first.unit, c["unit"]) and _claim_backs(first, c)]
    backs_y = [c for c in level if _compatible(second.unit, c["unit"]) and _claim_backs(second, c)]
    pairs = [(a, b) for a in backs_x for b in backs_y if a is not b
             and (a["hs6"], a["partner"], a["metric"]) == (b["hs6"], b["partner"], b["metric"])]
    return not pairs or any(a["period"] < b["period"] for a, b in pairs)


def change_words(text: str, spans: list[tuple[int, int]]) -> list[tuple[int, int, str, bool]]:
    """증감 어휘(PT-6). 지표 이름(EX-6), 오탐 표현(오른쪽·확대 해석·늘어놓다), 조건 밖의 "내렸"은 빼고 부정형을 가른다."""
    found = []
    for m in CHANGE_WORD_RE.finditer(text):
        word, start, end = m.group(), m.start(), m.end()
        after = text[end:]
        if _overlaps(start, end, spans):
            continue
        if word in ("증가", "감소", "상승", "하락") and after[:1] in ("율", "률"):
            continue  # EX-6 지표 이름
        if word == "오른" and after[:1] in ("쪽", "편", "손"):
            continue
        if word == "확대" and re.match(r"\s?해석", after):
            continue
        if word == "늘어" and after.startswith("놓"):
            continue
        if word == "내렸" and not PRICE_SUBJECT_RE.search(text[:start]):
            continue
        direction = "UP" if word in UP_WORDS else "DOWN" if word in DOWN_WORDS else "FLAT"
        found.append((start, end, direction, bool(NEGATION_RE.match(after))))
    return found


# ---- 공용 --------------------------------------------------------------------------------------------------


def base_symbol(symbol: object) -> str | None:
    """기호의 `@` 앞부분(단위 R1과 같은 규칙). 계약 §11.2 밖이면 None이다."""
    if not isinstance(symbol, str):
        return None
    base, at, code = symbol.partition("@")
    if at:
        return base if base in SUB_ITEM_BASES and code and "@" not in code else None
    return base if base in UNIT_OF and base != "w" else None


def month_minus_12(period: str) -> str:
    return f"{int(period[:4]) - 1:04d}{period[4:]}"


def _is_number(value: object) -> bool:
    """int(bool 제외)나 유한한 Decimal이면 참이다. NaN·무한대는 수로 보지 않는다."""
    if isinstance(value, Decimal):
        return value.is_finite()
    return isinstance(value, int) and not isinstance(value, bool)
