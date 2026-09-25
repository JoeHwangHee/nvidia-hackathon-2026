"""단위 R3 검증 규칙.

단위 ID: R3
도메인명: validator_validate
소유: M
입력: 보고서·봉투·스냅샷
출력: findings(`validator_findings`)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics, tradesentry.policy, tradesentry.validator, tradesentry.reports.render_ko

정본: 개발 플랜 docs/plan/DEV_PLAN.md §7.4(검증기), 자료 계약 docs/rules/DATA_CONTRACT_V1.md §3(상태값), §4.4(근거 ID
풀림), §6(typed claim), §9.1·§9.4(보고서와 스키마 요건), §11(단위·자릿수), 룰북 docs/eval/RULEBOOK.md B3-1(값 비교)·
B3-2(산문 패턴). 검증기는 정답표를 읽지 않고, 모델의 틀린 값·상태를 고치지 않고 사유만 적는다. 막을지(모드별)는 단위
R4가 정한다.

입력(JSON 객체 하나)
- `report`: 보고서 초안이나 보고서 객체(자료 계약 §9.1). `report_id`·`evidence_ids`·`validator_findings`·`report_hash`·
  `created_at`은 없어도 된다(검증 뒤 단위 R2가 채운다).
  - `report_hash`와 초안의 관계: 검증 전 초안에는 `report_hash`가 없고, 그러면 이 검사를 건너뛴다. 필드가 있으면
    형식(소문자 16진수 64자)과 내용 일치를 본다. 내용 일치는 `claims`·`narrative`·`hypotheses`·`evidence_ids`를 계약
    §9.1로 정규화해 다시 계산한 값(단위 R2의 `report_hash`, 해시 구현을 한 곳에 두려고 R2 모듈을 import한다)과
    같은지다. `evidence_ids`가 없으면 R2와 같게 주장들의 근거를 모아 계산한다. 어긋나면 스키마 사유
    `SCHEMA_REPORT_HASH`로 모든 모드에서 막는다. 흐름 조정(I12)은 초안을 검증한 뒤 R2로 최종 보고서를 만들거나 R2가
    만든 보고서를 검증한다. 어느 쪽이든 최종 해시는 R2가 계산한다. 저장한 보고서를 다시 검증하면(승인·화면) 이 검사가
    해시 변조와 해시 뒤 내용 변경을 잡는다.
- `case`: 사례 객체(자료 계약 §2.3.5). 코드가 만든 것이라 형식이 틀리거나 발동한 신호가 없으면(사례의 정의,
  개발 플랜 §6.4) ValueError다.
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
- 자료 상태 주장의 근거 행(`_status_row_supports`): 수집기는 상태 행(`UNRESOLVED_ZERO`·`REQUEST_FAILED`)을 요청 코드
  자릿수로 쓴다(HS4 스캔 요청은 HS4 코드, HS6 요청은 HS6 코드, 수입·수출 두 흐름). 그래서 자료 상태 주장은 그 키 자신의
  행이나 그 키를 맡은 요청의 상태 행을 인용한다.
  - 값이 `OBSERVED`인 주장은 같은 코드의 행만 받는다.
  - 그 밖의 값은 그 키 자신의 행과 그 키를 맡은 요청의 행을 받는다. 상대국 HS10 키는 HS6 요청(앞 6자리), 상대국 HS6
    키는 HS4 스캔 요청(앞 4자리)과 HS6 요청 자신, 전체국가(`ALL`) 키는 앞 6자리·앞 4자리 요청 모두다(품목별 API는 HS4·
    HS6 요청 모두 HS10 행을 준다). 하위 행으로 상위 키의 상태를 뒷받침하지 못한다.
  - 같은 상대국·HS6·월의 부모 HS6 행(`OBSERVED` 수입 행)이 `rows`에 있으면, 그 키의 HS6 요청 상태 행은 HS10 하위
    자료가 빠졌다는 뜻이다(자료 계약 §2.3.2 행 규칙 4, oracle C형). 그 행은 `observation_status@<HS10 코드>` 주장만
    뒷받침하고 HS6 수준 `observation_status` 주장은 뒷받침하지 못한다.
  - 한 보고서에서 같은 대상의 자료 상태 주장끼리 값이 다르거나, `OBSERVED`가 아닌 자료 상태와 같은 키·월의 값 주장이
    함께 있으면 `DATA_STATUS_CONFLICT`다. `CONFIRMED_NO_TRADE`는 V·Q를 0으로 보아 s·d_s·w@가 계산되므로 단가(U·r_U,
    하위품목이면 U@·r_U@)와 분해 효과만 본다(자료 계약 §3.4).
- 금지 문구 목록과 산문 패턴 정규식은 이 파일에 둔다. 룰북 B3-2가 정본이고, 채점기(eval/scorer/prose.py)와 따로
  구현했다. 둘이 어긋나면 채점기 판정이 기준이므로(룰북 B3-2 끝 문장) 검증기는 채점기의 규칙에 맞춘다(2026-09-26(토)
  결정 기록 `model-decision-validator-prose-alignment`): EX-1 `N일`·`N주`는 빼되 `연속`이 뒤따르면 빼지 않고, EX-4
  `제N`(제2-1안·제3국)과 `Nkg당`·`N톤당`의 기준 수량을 빼고, `USD/톤`·`달러/톤`·`톤당`은 호환 claim이 없는 단위로
  잡고(룰북 경계 14), `%P`(대문자)는 pp로 읽지 않고, `USD3.7`은 식별자가 아니라 금액이고, 배수 부등식("2배 이상")은
  비율 비교에 부등식을 적용하고, 배수와 금액 사이 공백("21.9 백만")을 허용하고, 부정형에 `(이|가|은|는)? 없`을 더한다.
  룰북 EX 표에 없는 빼기 셋(품목 규격 1kVA·16kVA, 분류 자릿수 HSK 10·10단위·6자리, 기준월 표기 t−12)은 무역통계
  검토 권고로 더한 해석이다. 이 가운데 t−12는 채점기도 빼고, 나머지(EX-2 확장)는 채점기가 잡으므로 룰북 EX-2·채점기에
  같게 넣을지 사용자 결정 대기다(공용 약속).
- 기호·단위·자릿수·상태값 표는 자료 계약의 사본이다(단위 표 §6 조립 부산물 4. 조립 점검에서 K1·X4로 옮긴다).
"""
import re
import unicodedata
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from tradesentry.reports import render_ko

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
HS10_RE = re.compile(r"\d{10}")
HASH_RE = re.compile(r"[0-9a-f]{64}")

CODES = {
    "SCHEMA_REPORT": "보고서 키·형식",
    "SCHEMA_CLAIM": "typed claim 필드·형식",
    "SCHEMA_CLAIM_ID": "claim_id 중복·예약어",
    "SCHEMA_STATUS": "판정 상태 값",
    "SCHEMA_SIGNAL_CLAIM": "발동 신호별 주장 요건(계약 §9.4)",
    "SCHEMA_REPORT_HASH": "report_hash 형식·내용 일치(계약 §9.1)",
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
    "DATA_STATUS_CONFLICT": "같은 대상의 자료 상태·값 주장끼리 어긋남",
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
    out += _report_hash_check(report)
    claims = report.get("claims") if isinstance(report.get("claims"), list) else []
    valid = _claim_schema(claims, out)
    statuses_ok = _status_schema(report, out)
    out += _signal_claims(valid, ctx.case)
    if statuses_ok:
        out += _status_consistency(report, ctx.case)
    out += _provenance(report, ctx)
    for index, claim in valid:
        out += _claim_checks(index, claim, ctx)
    out += _data_status_conflicts(valid)
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
    if not any(signals[s] == "TRIGGERED" for s in SIGNALS):
        raise ValueError("R3 입력의 case에 발동한 신호가 없다. 사례는 신호가 하나 이상 발동해야 한다(개발 플랜 §6.4)")
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


def _report_hash_check(report: dict) -> list[dict]:
    """report_hash가 있으면 형식과, 네 키를 계약 §9.1로 정규화해 다시 계산한 값과의 일치를 본다(초안에는 없다)."""
    if "report_hash" not in report:
        return []
    value = report["report_hash"]
    if not (isinstance(value, str) and HASH_RE.fullmatch(value)):
        return [_f("schema", "SCHEMA_REPORT_HASH", "report_hash", None,
                   "report_hash는 소문자 16진수 64자의 sha256이어야 한다(계약 §9.1)")]
    items, narrative, hypotheses = report.get("claims"), report.get("narrative"), report.get("hypotheses")
    if not (isinstance(items, list) and isinstance(narrative, str) and isinstance(hypotheses, list)):
        return []  # 네 키의 형식 사유는 SCHEMA_REPORT로 이미 적었다
    evidence = report.get("evidence_ids")
    if not isinstance(evidence, list):
        evidence = render_ko.collect_evidence(items)
    try:
        expected = render_ko.report_hash(items, narrative, hypotheses, evidence)
    except (ValueError, TypeError):
        return [_f("schema", "SCHEMA_REPORT_HASH", "report_hash", None,
                   "claims·narrative·hypotheses·evidence_ids를 계약 §9.1로 정규화할 수 없어 다시 계산하지 못했다")]
    if expected != value:
        return [_f("schema", "SCHEMA_REPORT_HASH", "report_hash", None,
                   "claims·narrative·hypotheses·evidence_ids를 계약 §9.1로 정규화해 다시 계산한 값과 다르다"
                   "(해시를 만든 뒤 내용이 바뀌었거나 해시가 틀렸다)")]
    return []


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


def aggregate_status(signal_status: dict, signals: dict) -> tuple[str, bool] | None:
    """계약 §3.1의 결정적 집계. 이 검증기의 기대값 계산과 흐름 조정(단위 I12)의 보고서 채우기가 함께 쓴다(사용자 결정
    2026-09-25(금) 22:22 ①, 두 곳의 계산이 어긋나지 않게). 발동한 신호의 판정(NOT_TRIGGERED는 빼고)에서
    review_status(MAINTAIN > HOLD > MONITOR)와 unresolved_evidence(MAINTAIN과 HOLD가 섞일 때만 true)를 돌려준다.
    발동한 신호의 판정이 하나도 없으면 None이다. signal_status는 형식 검사(_status_schema)를 지난 객체여야 한다."""
    triggered = [signal_status[signal] for signal in SIGNALS
                 if (signals or {}).get(signal) == "TRIGGERED" and signal_status[signal] != "NOT_TRIGGERED"]
    if not triggered:
        return None
    expected = "MAINTAIN" if "MAINTAIN" in triggered else "HOLD" if "HOLD" in triggered else "MONITOR"
    return expected, ("MAINTAIN" in triggered and "HOLD" in triggered)


def _status_consistency(report: dict, case: dict) -> list[dict]:
    """허용 상태: 발동하지 않은 신호는 NOT_TRIGGERED, 사례 상태는 MAINTAIN > HOLD > MONITOR 집계, unresolved_evidence는
    MAINTAIN과 HOLD가 섞일 때만 true다(계약 §3.1). 틀린 상태를 고치지 않고 사유만 적는다."""
    out = []
    signal_status = report["signal_status"]
    for signal in SIGNALS:
        stated, trigger = signal_status[signal], case["signals"][signal]
        if trigger == "NOT_TRIGGERED" and stated != "NOT_TRIGGERED":
            out.append(_f("validator", "STATUS_INCONSISTENT", f"signal_status.{signal}", None,
                          f"발동하지 않은 신호의 판정은 NOT_TRIGGERED여야 한다(적힌 값 {stated})"))
        if trigger == "TRIGGERED" and stated == "NOT_TRIGGERED":
            out.append(_f("validator", "STATUS_INCONSISTENT", f"signal_status.{signal}", None,
                          "발동한 신호의 판정이 NOT_TRIGGERED다"))
    aggregate = aggregate_status(signal_status, case["signals"])
    if aggregate is None:
        return out
    expected, unresolved = aggregate
    if report["review_status"] != expected:
        out.append(_f("validator", "STATUS_INCONSISTENT", "review_status", None,
                      f"신호별 판정의 집계(MAINTAIN > HOLD > MONITOR)는 {expected}다. 적힌 값: {report['review_status']}"))
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
    if "@" in claim["metric"] and not sub_item_ok(claim["metric"].partition("@")[2], claim["hs6"]):
        out.append(_f("validator", "REFERENT_MISMATCH", f"{path}.metric", claim_id,
                      "하위품목 코드는 부모 hs6로 시작하는 숫자 10자다(계약 §6.2)"))
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
    if at and not sub_item_ok(code, claim["hs6"]):
        out.append(_f("validator", "REFERENT_MISMATCH", f"{path}.metric", claim_id,
                      "하위품목 코드는 부모 hs6로 시작하는 숫자 10자다(계약 §6.2)"))
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
    target = code if at else claim["hs6"]
    if any(_status_row_supports(claim, target, row, ctx) for _, row in resolved):
        return
    out.append(_f("validator", "EVIDENCE_NOT_SUPPORTING", f"{path}.evidence_ids", claim_id,
                  f"인용한 행 가운데 이 대상({target})의 관측 상태가 {claim['value']}임을 보이는 행이 없다. "
                  "그 키 자신의 행이나 그 키를 맡은 요청의 상태 행을 인용한다"))


def status_row_codes(target: str, partner: str, observed: bool) -> tuple[str, ...]:
    """자료 상태 주장이 인용할 수 있는 행의 hs_code: 그 키 자신과 그 키를 맡은 요청의 코드(상태 행은 요청 코드 자릿수)."""
    if observed:
        return (target,)
    if len(target) == 10:
        return (target, target[:6], target[:4]) if partner == "ALL" else (target, target[:6])
    return (target, target[:4])


def _status_row_supports(claim: dict, target: str, row: dict, ctx: Context) -> bool:
    if (row.get("partner_code"), row.get("month"), row.get("observation_status")) != (
            claim["partner"], claim["period"], claim["value"]):
        return False
    hs_code = row.get("hs_code")
    if hs_code not in status_row_codes(target, claim["partner"], claim["value"] == "OBSERVED"):
        return False
    if claim["value"] != "OBSERVED" and len(target) == 6 and hs_code == target \
            and _parent_row_exists(claim["partner"], target, claim["period"], ctx):
        return False  # 계약 §2.3.2 행 규칙 4: 부모 HS6 행이 있는 키의 HS6 요청 상태 행은 HS10 하위 자료의 상태다
    return True


def _parent_row_exists(partner: str, hs6: str, period: str, ctx: Context) -> bool:
    """rows에 같은 상대국·HS6·월의 부모 HS6 값 행(OBSERVED 수입 행)이 있는가."""
    return any(isinstance(row, dict) and row.get("partner_code") == partner and row.get("hs_code") == hs6
               and row.get("month") == period and row.get("observation_status") == "OBSERVED"
               and row.get("flow", "import") == "import" for row in ctx.rows.values())


HS6_LEVEL_BASES = ("V", "Q", "U", "s", "r_U", "d_s")  # 부모 HS6 행에서 오는 값(계약 §11.2 원천 규칙)
NO_TRADE_BASES = ("U", "r_U")  # CONFIRMED_NO_TRADE는 V·Q를 0으로 보아 s·d_s는 계산되고 단가는 계산하지 않는다(§3.4)


def _data_status_conflicts(valid: list[tuple[int, dict]]) -> list[dict]:
    """같은 대상의 자료 상태 주장끼리 값이 다르거나, 값이 없다는 자료 상태와 같은 키·월의 값 주장이 함께 있는가."""
    out = []
    statuses = [(i, c) for i, c in valid if c["claim_type"] == "data_status"
                and (c["metric"] == "observation_status" or c["metric"].startswith("observation_status@"))]
    groups: dict[tuple, list] = {}
    for i, claim in statuses:
        groups.setdefault((claim["partner"], claim["hs6"], claim["metric"], claim["period"]), []).append((i, claim))
    for items in groups.values():
        values = sorted({claim["value"] for _, claim in items})
        if len(values) > 1:
            for i, claim in items:
                out.append(_f("validator", "DATA_STATUS_CONFLICT", f"claims[{i}].value", claim["claim_id"],
                              f"같은 대상의 자료 상태 주장이 서로 다르다({'·'.join(values)})"))
    numeric = [(i, c) for i, c in valid if c["claim_type"] != "data_status" and _is_number(c["value"])]
    for i, status in statuses:
        if status["value"] == "OBSERVED" or status["partner"] == "ALL":
            continue
        _, at, code = status["metric"].partition("@")
        month = status["period"]
        for _, claim in numeric:
            if (claim["partner"], claim["hs6"]) != (status["partner"], status["hs6"]) \
                    or month not in (claim["period"], claim["baseline_period"]):
                continue
            symbol_base, symbol_at, symbol_code = claim["metric"].partition("@")
            no_trade = status["value"] == "CONFIRMED_NO_TRADE"
            if at:  # 무거래 확정 하위품목의 중량 비중(w@)은 0으로 계산되므로 단가(U@·r_U@)와 분해 효과만 본다
                sub_bases = NO_TRADE_BASES if no_trade else SUB_ITEM_BASES
                hit = (symbol_at and symbol_code == code and symbol_base in sub_bases) \
                    or (not symbol_at and symbol_base in DECOMPOSITION)
            else:
                hit = not symbol_at and symbol_base in (NO_TRADE_BASES if no_trade else HS6_LEVEL_BASES)
            if hit:
                out.append(_f("validator", "DATA_STATUS_CONFLICT", f"claims[{i}].value", status["claim_id"],
                              f"값이 있는 같은 키·월의 주장({claim['claim_id']})과 어긋난다: 그 대상을 "
                              f"{status['value']}로 적었다"))
                break
    return out


def sub_item_ok(code: str, hs6: str) -> bool:
    """HS10 하위품목 코드는 숫자 10자이고 부모 hs6로 시작한다(계약 §6.2)."""
    return bool(HS10_RE.fullmatch(code)) and code.startswith(hs6)


# ---- 금지 문구 ----------------------------------------------------------------------------------------------
# 자료 계약 §6.3·개발 플랜 §7.6·§12.2: 단가·점유율 변화를 부정·위법·원산지 조작(우회수입, 즉 제3국을 거쳐 원산지를
# 바꿔 들여오는 수입 포함)·개별 거래가격의 증거로 쓰지 않고, 통관 조치로 표현하지 않고, 경보 해소를 "정상 확정"으로
# 쓰지 않는다. 뜻을 가리지 않고 낱말이 나오면 사유로 적는다(부정문 포함). 여러 낱말 문구는 띄어쓰기를 보지 않는다
# ("부정 가능성"과 "부정가능성"을 같게 잡는다). 목록은 문자열만 담는다(MT4 프롬프트 동기화 시험이 이 두 목록을 읽는다).
FORBIDDEN_PHRASES = (
    # 부정(不正). "부정" 단독은 "부정적 영향"·"부정할 수 없다" 같은 오탐이 있어 넣지 않는다
    "부정 거래", "부정 수입", "부정 수출", "부정 행위", "부정 가능성", "부정 의혹", "부정 여부", "부정의 증거",
    "부정 소지", "부정 신고", "부정한 방법", "사기 거래", "사기 행위",
    # 위법·불법
    "불법", "위법", "탈법", "편법", "탈세", "탈루", "밀수", "범죄", "혐의", "관세법 위반", "법 위반", "법률 위반",
    "관세 포탈", "관세 회피",
    # 원산지 조작과 우회수입(계약의 풀이 "제3국을 거쳐 원산지를 바꿔 들여오는 수입" 포함), 원산지 판정
    "원산지 조작", "원산지를 조작", "원산지 세탁", "원산지 위장", "원산지 둔갑", "원산지 속임", "원산지 우회",
    "원산지 회피", "원산지를 바꿔", "원산지를 바꾼", "원산지 판정", "원산지 판단", "우회 수입", "우회 수출",
    "우회 환적", "환적", "제3국을 거쳐", "제3국 경유", "제3국을 경유",
    # 개별 거래가격
    "저가 신고", "과소 신고", "허위 신고", "가격 조작", "개별 거래가격", "개별 거래의 가격", "덤핑",
    # 통관 조치("자료 보류"와 겹치지 않게 "보류" 단독은 넣지 않는다)
    "통관 보류", "추징", "적발", "압수", "처벌", "고발",
    # 정상 확정·정상 거래(개발 플랜 §6.3: 공통 하락은 정상 거래의 증명이 아니다)
    "정상 확정", "정상으로 확정", "정상 거래",
)
FORBIDDEN_LATIN = ("fraud", "illegal", "smuggl", "circumvent", "dumping", "evasion", "under-invoic", "transship",
                   "misdeclar")
# 금지 낱말을 품었지만 금지할 뜻이 아닌 말(무역구제 관세 이름). 대소문자와 띄어쓰기를 가리지 않고 먼저 지운다.
FORBIDDEN_EXCEPTIONS = ("반덤핑", "덤핑방지", "덤핑 방지", "anti-dumping", "antidumping")
# 앞 글자가 한글이면 세지 않는 낱말("순환적"·"교환적"·"전환적"의 "환적"). 띄어 쓴 "화물 환적"은 센다.
WORD_START_PHRASES = ("환적",)


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
        for phrase in forbidden_hits(text):
            out.append(_f("validator", "FORBIDDEN_PHRASE", path, None,
                          f"금지 문구를 썼다: '{phrase}'. 보고서는 담당자의 다음 업무만 제시한다(계약 §6.3)"))
    return out


def forbidden_hits(text: str) -> list[str]:
    """문장에 나온 금지 문구(목록 순서). 예외 낱말을 먼저 지우고, 여러 낱말 문구는 띄어쓰기를 보지 않고, 겹치면 긴 쪽만
    남긴다."""
    flat = re.sub(r"\s+", " ", unicodedata.normalize("NFC", text))
    for word in FORBIDDEN_EXCEPTIONS:
        flat = re.sub(r"\s?".join(re.escape(ch) for ch in word.replace(" ", "")), " ", flat, flags=re.IGNORECASE)
    tight, lower = flat.replace(" ", ""), flat.lower()
    hits = []
    for phrase in FORBIDDEN_PHRASES:
        if phrase in WORD_START_PHRASES:
            found = re.search(r"(?<![가-힣])" + re.escape(phrase), flat) is not None
        elif " " in phrase:  # 여러 낱말 문구는 띄어쓰기를 보지 않는다("부정가능성"도 잡는다)
            found = phrase.replace(" ", "") in tight
        else:  # 한 낱말은 띄어쓰기를 지우지 않은 문장에서 찾는다("재고 발생"을 "고발"로 잡지 않는다)
            found = phrase in flat
        if found:
            hits.append(phrase)
    hits += [word for word in FORBIDDEN_LATIN if word in lower]
    unique: dict[str, str] = {}  # 띄어쓰기를 뺀 꼴 → 처음 나온 문구(같은 꼴은 한 번만)
    for phrase in hits:
        unique.setdefault(phrase.replace(" ", "").lower(), phrase)
    return [p for key, p in unique.items() if not any(key != other and key in other for other in unique)]


# ---- 산문 패턴(룰북 B3-2) -----------------------------------------------------------------------------------

# 숫자 본체. 앞 글자가 라틴 문자·숫자·밑줄·점이면 식별자의 일부로 보고 잡지 않되, 단위 앞말 USD·US$ 바로 뒤는 잡는다
# ("USD3.7"은 금액이다. 채점기 EX-3 `(?!USD\d)` 가드와 같다)
NUMBER_RE = re.compile(r"(?:(?<=USD)|(?<=US\$)|(?<![A-Za-z0-9_.]))(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?")
SIGNS = {"-": -1, "−": -1, "△": -1, "▼": -1, "+": 1, "▲": 1}
# 금액 배수. 숫자와 배수 사이 공백을 허용한다("21.9 백만", 채점기와 같다). 긴 말(천만·백만)이 먼저다
MULTIPLIER_RE = re.compile(r"\s*(천만|백만|억|만|천)")
MULTIPLIERS = {"천만": Decimal(10) ** 7, "백만": Decimal(10) ** 6, "억": Decimal(10) ** 8, "만": Decimal(10) ** 4,
               "천": Decimal(10) ** 3}
UNIT_PATTERNS = (  # 순서가 뜻이다: %p·pp가 %보다 먼저(PT-2가 PT-1보다 먼저), 달러/kg·달러/톤이 달러보다 먼저.
    # 대문자 "%P"와 띄운 "% p"는 pp로 읽지 않는다(채점기 `%p(?![A-Za-z])`와 같다. 그때는 "%"만 단위로 읽는다)
    (re.compile(r"\s?(?:%p(?![A-Za-z])|%\s?포인트|퍼센트\s?포인트|pp(?![A-Za-z]))"), "pp"),
    (re.compile(r"\s?(?:%|퍼센트)"), "pct"),
    (re.compile(r"\s?(?:USD\s?/\s?kg|US\$\s?/\s?kg|\$\s?/\s?kg|달러\s?/\s?kg)"), "usd_per_kg"),
    (re.compile(r"\s?(?:USD\s?/\s?톤|US\$\s?/\s?톤|\$\s?/\s?톤|달러\s?/\s?톤)"), "usd_per_ton"),
    (re.compile(r"\s?(?:USD|US\$|\$|달러)(?![A-Za-z])"), "usd"),
    (re.compile(r"\s?(?:kg|킬로그램)(?![A-Za-z])"), "kg"),
    (re.compile(r"\s?톤"), "ton"),
    (re.compile(r"\s?배"), "multiple"),
)
PREFIX_USD_RE = re.compile(r"(?:US\$|USD|\$)\s?$")
PREFIX_PER_KG_RE = re.compile(r"kg당\s?$")
PREFIX_PER_TON_RE = re.compile(r"톤당\s?$")  # 톤당 단가는 관세청 지표와 환산하지 않는다(룰북 B3-2 경계 14)
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
    # "N일"·"N주" 기간(숫자와 단위 사이 공백 0개 이상, 채점기 `\s*+`와 같다). "N일 연속"은 빼지 않는다
    re.compile(r"(?<!\d)\d{1,3}\s*(?:일|주)(?!\s*연속)"),
    re.compile(r"(?<![A-Za-z])t\s?[-−+]\s?\d+"),  # 기준월 표기 t−12(해석: 무역통계 검토 권고 4. 채점기도 뺀다)
    # EX-2 품목 식별(HS와 함께 쓴 숫자, 류·호 표기). HS 코드 집합의 숫자는 아래 CODE_TOKEN_RE로 따로 본다
    re.compile(r"(?<![A-Za-z])[Hh][Ss]\s?[-:]?\s?\d+(?:[.\-]\d+)*"),
    re.compile(r"제\s?\d+\s?(?:류|호)"),
    re.compile(r"\d+\s?(?:류|호)"),
    # EX-2 확장(해석: 무역통계 검토 권고 4). 품목 규격(1kVA·16kVA)과 분류 자릿수(HSK 10, 10단위, 6자리)
    re.compile(r"\d+(?:\.\d+)?\s?(?:[kKM]?VA|[kK]V|[kK]W)(?![A-Za-z])"),
    re.compile(r"(?<![A-Za-z])[Hh][Ss][Kk]\s?\d+"),
    re.compile(r"\d+\s?(?:단위|자리)"),
    # EX-3 식별자·버전(근거 ID, 라틴 문자와 숫자가 섞인 이름: policy_v1, RB-1, g1, kcs_202201_202412_v2 등)
    re.compile(r"ev:[^\s,;)\]]+"),
    # EX-4 목록 번호와 조사 과정·구조의 개수, 순번 "제N"(제2-1안·제3국), "1kg당"처럼 단위 기준을 뜻하는 수량
    re.compile(r"(?m)^\s*\d+[.)](?=\s)"),
    re.compile(r"\d+\s?(?:회|번째|단계|차례)"),
    re.compile(r"제\s*\d+(?:\s*[-.]\s*\d+)*"),  # 공백 0개 이상(채점기 `\s*+`와 같다)
    re.compile(r"(?:신호|도구|호출)\s?\d+\s?(?:개|종|가지|회|번)"),
    re.compile(r"\d+\s?(?:개|종|가지)의?\s?(?:신호|도구)"),
    re.compile(r"(?<!\d)\d+\s*(?:kg|킬로그램|톤)\s*당"),  # 공백 0개 이상(채점기 `\s*+`와 같다)
)
# EX-3 식별자(라틴 문자로 시작하고 숫자가 든 이름). "USD3.7"처럼 단위 앞말 USD 바로 뒤의 숫자는 식별자가 아니다
IDENT_RE = re.compile(r"(?<![A-Za-z0-9_])(?!USD\d)[A-Za-z_][A-Za-z0-9_]*(?:[-.:][A-Za-z0-9_]+)*")
CODE_TOKEN_RE = re.compile(r"(?<![\d.,])\d[\d.\-]*\d(?!\d)")

UP_WORDS = ("증가", "상승", "급증", "급등", "폭등", "치솟", "반등", "확대", "늘었", "늘어", "늘며", "늘고",
            "오르", "올라", "오른", "올랐", "높아지", "높아졌", "높아진")
DOWN_WORDS = ("감소", "하락", "급감", "급락", "폭락", "반토막", "축소", "줄었", "줄어", "줄며", "줄고",
              "떨어지", "떨어졌", "떨어진", "떨어져", "내렸", "낮아지", "낮아졌", "낮아진")
FLAT_WORDS = ("보합", "변화가 없", "변동이 없", "변함없", "제자리")
CHANGE_WORD_RE = re.compile("|".join(re.escape(w) for w in sorted(UP_WORDS + DOWN_WORDS + FLAT_WORDS,
                                                                 key=len, reverse=True)))
# 부정형: "…지 않/못", "…지는 않/못"과 "증가가 없다"·"증가는 없었다"·"감소 없이" 꼴의 "(이|가|은|는)? 없"(채점기와 같다)
NEGATION_RE = re.compile(r"[가-힣]{0,3}\s?(?:지\s?않|지는\s?않|지\s?못|지는\s?못)|\s?(?:이|가|은|는)?\s?없")
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
    return {"pct": "PT-1", "pp": "PT-2", "usd": "PT-3", "usd_per_kg": "PT-3", "usd_per_ton": "PT-3", "kg": "PT-3",
            "ton": "PT-3"}.get(unit or "", "PT-5")


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
        elif PREFIX_PER_TON_RE.search(before):
            prefix, start = "per_ton", PREFIX_PER_TON_RE.search(before).start()
        before = text[:start]
        approx = bool(APPROX_BEFORE_RE.search(before))
        pos, scale = m.end(), Decimal(1)
        mult = MULTIPLIER_RE.match(text, pos)
        if mult:
            pos, scale = mult.end(), MULTIPLIERS[mult.group(1)]
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
        if prefix == "per_ton" and unit in (None, "usd"):
            unit = "usd_per_ton"
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
    """표현의 단위 부류와 호환되는 claim 단위. 톤당 단가(usd_per_ton)는 계약 단위(§11)에 없어 어느 claim과도 호환되지
    않는다(룰북 B3-2 경계 14: BACI 값을 관세청 지표와 환산하지 않는다)."""
    return {None: True, "pct": claim_unit == "%", "pp": claim_unit == "pp",
            "usd": claim_unit in ("USD", "USD/kg"), "usd_per_kg": claim_unit == "USD/kg", "usd_per_ton": False,
            "kg": claim_unit == "kg", "ton": claim_unit == "kg"}.get(unit, False)


def number_backed(expr: NumberExpr, numeric: list[dict]) -> bool:
    """숫자(PT-1~PT-5): 같은 보고서의 단위가 호환되는 typed claim 값 하나와 같으면 뒷받침된다."""
    if expr.unit == "multiple":
        return _multiple_backed(expr.magnitude, expr.places, numeric, expr.bound)
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


def _multiple_backed(value: Decimal, places: int, numeric: list[dict], bound: str | None = None) -> bool:
    """배수(PT-4): r_U 주장을 비율 k = 1 + r_U/100으로 바꿔 보인 자리에서 반올림해 같으면 뒷받침된다. 부등식이 붙으면
    ("2배 이상") 반올림하지 않고 비율이 그 값 이상(ge)·이하(le)인 주장이 있으면 뒷받침된다(룰북 B3-2 부등식, 채점기와
    같다)."""
    for claim in numeric:
        if claim["metric"] != "r_U":
            continue
        ratio = 1 + Decimal(claim["value"]) / 100
        if bound == "ge":
            ok = ratio >= value
        elif bound == "le":
            ok = ratio <= value
        else:
            ok = round_at(ratio, places) == value
        if ok:
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
    """증감 어휘(PT-6). 지표 이름(EX-6), 오탐 표현(오른쪽·확대 해석·늘어놓다), 조건 밖의 "내렸"은 빼고 부정형을 가른다.
    그대로(FLAT) 어휘("변화가 없")는 부정형을 보지 않는다(채점기와 같다)."""
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
        found.append((start, end, direction, direction != "FLAT" and bool(NEGATION_RE.match(after))))
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
