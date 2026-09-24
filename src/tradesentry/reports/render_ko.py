"""단위 R2 한국어 보고서 틀.

단위 ID: R2
도메인명: reports_render_ko
소유: M
입력: claim + 설명·가설
출력: 보고서·`report_hash`
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.metrics, tradesentry.reports

정본: 자료 계약 docs/rules/DATA_CONTRACT_V1.md §9.1(보고서 객체 키와 `report_hash` 정규화 규칙), §3.1(판정 상태와
`PRE_INVESTIGATION`), 개발 플랜 docs/plan/DEV_PLAN.md §5.2(CLI가 전하는 보고서 본문)·§7.2.

입력(JSON 객체 하나)
- `report_id`, `run_id`, `mode`, `created_at`(KST ISO 8601), `policy_version`, `snapshot_id`, `grouping_version`: 문자열
- `case`: 사례 객체(자료 계약 §2.3.5). `case_id`와 본문 머리(품목·상대국·월)에 쓴다.
- `claims`: typed claim 목록(단위 R1의 출력), `narrative`: 문자열, `hypotheses`: 문자열 목록
- `review_status`, `signal_status`, `unresolved_evidence`: 조사가 낸 판정. 이 단위는 고치지 않고 옮긴다.
- `validator_findings`: 검증기 기록 목록(단위 R4의 출력). 없으면 빈 목록이다.
- `execution_status`(생략 가능): 본문 머리에 실행 상태를 알릴 때만 쓴다. 보고서 객체에는 넣지 않는다.

출력: `{"report": 보고서 객체, "body_ko": 한국어 본문}`
- 보고서 객체는 계약 키 17개를 계약 순서대로 담는다. `evidence_ids`는 주장들의 근거를 처음 나온 순서로 모은 것이다.
  `claims`·`narrative`·`hypotheses`·판정은 입력 그대로다(수의 원문 표기 보존).
- `report_hash`는 계약 §9.1 규칙이다: 네 키(`claims`·`narrative`·`hypotheses`·`evidence_ids`)만 담고, 모든 문자열을
  NFC로 바꾸고, 주장의 수 `value`를 그 `metric`의 표시 자릿수로 Decimal `ROUND_HALF_UP` 반올림해 정수 자릿수 기호는
  int, 나머지는 float로 넣는다. 키 순 정렬·공백 없는 구분자·한글 그대로의 UTF-8 바이트의 sha256(소문자 16진수 64자)이다.
  float는 계약이 정한 이 직렬화 안에서만 쓰고 출력에는 두지 않는다.
- 해석: 표시 자릿수가 정해지지 않은 기호(계약 §11.2 밖, 예: freeform 모델이 지어낸 기호)의 수는 반올림하지 않고
  그대로 넣는다(Decimal은 float, int는 int). 계약 §9.1은 이 경우를 정하지 않았다.
- 본문은 처음 표시 "조사 전 경보"(`PRE_INVESTIGATION`)를 먼저 적고, 조사 뒤 제안을 따로 적는다. 판정이 바뀐 이력처럼
  꾸미지 않는다(계약 §3.1). 숫자는 주장의 문장(`text`)으로만 적고 새로 계산하지 않는다.
- 입력을 바꾸지 않는다.
"""
import copy
import hashlib
import json
import unicodedata
from decimal import ROUND_HALF_UP, Decimal

from tradesentry.reports import claims as claims_unit

REPORT_KEYS = ("report_id", "run_id", "case_id", "mode", "claims", "narrative", "hypotheses", "review_status",
               "signal_status", "unresolved_evidence", "evidence_ids", "validator_findings", "report_hash",
               "created_at", "policy_version", "snapshot_id", "grouping_version")
TEXT_INPUTS = ("report_id", "run_id", "mode", "created_at", "policy_version", "snapshot_id", "grouping_version")
PRE_INVESTIGATION = "PRE_INVESTIGATION"
STATUS_LABEL = {"MAINTAIN": "검토 유지", "MONITOR": "모니터링", "HOLD": "자료 보류", "NOT_TRIGGERED": "미발동",
                PRE_INVESTIGATION: "조사 전 경보"}
SIGNAL_LABEL = {"unit_value": "단가", "share": "점유율"}


def run(inp: object) -> object:
    """진입 함수. 보고서 객체(계약 키 17개, report_hash 포함)와 한국어 본문을 만든다."""
    if not isinstance(inp, dict):
        raise ValueError("R2 입력은 JSON 객체여야 한다")
    for key in TEXT_INPUTS:
        if not isinstance(inp.get(key), str):
            raise ValueError(f"R2 입력의 {key}가 문자열이 아니다")
    case = inp.get("case")
    if not isinstance(case, dict) or not isinstance(case.get("case_id"), str):
        raise ValueError("R2 입력에 사례(case)와 그 case_id가 없다")
    items, narrative, hypotheses = inp.get("claims"), inp.get("narrative"), inp.get("hypotheses")
    if not isinstance(items, list) or not isinstance(narrative, str) or not isinstance(hypotheses, list):
        raise ValueError("R2 입력의 claims·hypotheses는 목록, narrative는 문자열이어야 한다")
    findings = inp.get("validator_findings", [])
    if not isinstance(findings, list):
        raise ValueError("R2 입력의 validator_findings는 목록이어야 한다")
    evidence = collect_evidence(items)
    report = {
        "report_id": inp["report_id"],
        "run_id": inp["run_id"],
        "case_id": case["case_id"],
        "mode": inp["mode"],
        "claims": copy.deepcopy(items),
        "narrative": narrative,
        "hypotheses": copy.deepcopy(hypotheses),
        "review_status": copy.deepcopy(inp.get("review_status")),
        "signal_status": copy.deepcopy(inp.get("signal_status")),
        "unresolved_evidence": copy.deepcopy(inp.get("unresolved_evidence")),
        "evidence_ids": evidence,
        "validator_findings": copy.deepcopy(findings),
        "report_hash": report_hash(items, narrative, hypotheses, evidence),
        "created_at": inp["created_at"],
        "policy_version": inp["policy_version"],
        "snapshot_id": inp["snapshot_id"],
        "grouping_version": inp["grouping_version"],
    }
    return {"report": report, "body_ko": render_body(report, case, inp.get("execution_status"))}


def collect_evidence(items: list) -> list[str]:
    """주장들의 근거 ID를 처음 나온 순서로 모은다(보고서가 쓴 근거 전체, 계약 §9.1)."""
    seen: list[str] = []
    for claim in items:
        evidence = claim.get("evidence_ids") if isinstance(claim, dict) else None
        for item in evidence if isinstance(evidence, list) else []:
            if isinstance(item, str) and item not in seen:
                seen.append(item)
    return seen


# ---- report_hash(계약 §9.1) ---------------------------------------------------------------------------------


def report_hash(items: list, narrative: str, hypotheses: list, evidence_ids: list) -> str:
    """계약 §9.1 정규화 규칙으로 계산한 report_hash."""
    payload = {"claims": [_hash_claim(c) for c in items], "narrative": _normalize(narrative),
               "hypotheses": _normalize(hypotheses), "evidence_ids": _normalize(evidence_ids)}
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _hash_claim(claim: object) -> object:
    if not isinstance(claim, dict):
        return _normalize(claim)
    out = {}
    for key, value in claim.items():
        if key == "value" and _is_number(value):
            out[key] = _hash_number(claim.get("metric"), value)
        else:
            out[key] = _normalize(value)
    return out


def _hash_number(symbol: object, value: int | Decimal) -> int | float:
    """주장 수를 그 기호의 표시 자릿수로 사사오입한다. 원문 표기를 Decimal로 바로 읽어 반올림한다."""
    base = claims_unit.base_symbol(symbol) if isinstance(symbol, str) else None
    number = Decimal(value)
    if not number.is_finite():
        raise ValueError("report_hash에는 NaN이나 무한대를 쓰지 않는다")
    if base is None:
        return value if isinstance(value, int) else float(number)
    digits = claims_unit.DIGITS_OF[base]
    shown = number.quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP)
    return int(shown) if digits == 0 else float(shown)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, Decimal)) and not isinstance(value, bool)


def _normalize(value: object) -> object:
    """문자열은 NFC로, Decimal은 float로 바꾸고 목록·객체는 안까지 따라간다."""
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, dict):
        return {unicodedata.normalize("NFC", k) if isinstance(k, str) else k: _normalize(v) for k, v in value.items()}
    return value


# ---- 한국어 본문 --------------------------------------------------------------------------------------------


def status_label(code: object) -> str:
    """판정 상태 코드의 한국어 표기와 코드. 모르는 값은 원문 그대로 보인다(고쳐 적지 않는다)."""
    if isinstance(code, str) and code in STATUS_LABEL:
        return f"{STATUS_LABEL[code]}({code})"
    return f"{code}(정해진 판정 상태가 아님)"


def render_body(report: dict, case: dict, execution_status: object = None) -> str:
    """CLI가 그대로 전할 한국어 본문(마크다운)."""
    lines = [f"# TradeSentry 조사 보고서 — {case['case_id']}", ""]
    target = [f"HS {case['hs6']}" if isinstance(case.get("hs6"), str) else None,
              f"상대국 {case['partner']}" if isinstance(case.get("partner"), str) else None,
              f"비교월 {claims_unit.month_label(case['month'])}" if isinstance(case.get("month"), str) else None,
              f"기준월 {claims_unit.month_label(case['baseline_month'])}"
              if isinstance(case.get("baseline_month"), str) else None]
    lines.append(f"- 대상: {', '.join(t for t in target if t)}")
    lines.append(f"- 처음 표시: {status_label(PRE_INVESTIGATION)}")
    lines.append(f"- 조사 뒤 제안: {status_label(report['review_status'])}")
    signals = report["signal_status"]
    if isinstance(signals, dict):
        parts = [f"{SIGNAL_LABEL.get(k, k)} {status_label(v)}" for k, v in signals.items()]
        lines.append(f"- 신호별 판정: {', '.join(parts)}")
    unresolved = report["unresolved_evidence"]
    lines.append(f"- 미해결 근거 표시: {'있음' if unresolved is True else '없음' if unresolved is False else unresolved}")
    lines.append(f"- 모드: {report['mode']}")
    if execution_status is not None and execution_status != "COMPLETED":
        lines.append(f"- 실행 상태: {execution_status}. 유효한 최종 보고서가 아니므로 공유·승인 대상이 아니다")
    lines += ["", "## 사실 주장", ""]
    items = report["claims"]
    if not items:
        lines.append("주장 없음.")
    for number, claim in enumerate(items, start=1):
        if not isinstance(claim, dict):
            lines.append(f"{number}. (형식이 맞지 않는 주장)")
            continue
        evidence = claim.get("evidence_ids")
        cited = ", ".join(e for e in evidence if isinstance(e, str)) if isinstance(evidence, list) else ""
        lines.append(f"{number}. [{claim.get('claim_id')}] {claim.get('text')} (근거: {cited or '없음'})")
    lines += ["", "## 설명", "", report["narrative"] or "설명 없음.", "", "## 미확인 가설", ""]
    lines += [f"- {h}" for h in report["hypotheses"]] or ["가설 없음."]
    lines += ["", "## 검증기 기록", ""]
    findings = report["validator_findings"]
    lines += [f"- {_finding_line(f)}" for f in findings] or ["기록 없음."]
    lines += ["", "## 버전", "",
              f"- report_id: {report['report_id']}", f"- run_id: {report['run_id']}",
              f"- snapshot_id: {report['snapshot_id']}", f"- policy_version: {report['policy_version']}",
              f"- grouping_version: {report['grouping_version']}", f"- report_hash: {report['report_hash']}",
              f"- created_at: {report['created_at']}", "",
              "이 보고서는 담당자의 다음 업무(검토 유지·모니터링·자료 보류)를 제안하는 조사 기록이다. "
              "기관의 판정이나 통관 조치가 아니다.", ""]
    return "\n".join(lines)


def _finding_line(finding: object) -> str:
    if not isinstance(finding, dict):
        return str(finding)
    head = f"[{finding.get('check', '?')}] {finding.get('code', '?')}"
    where = finding.get("path")
    detail = finding.get("detail")
    return f"{head}{f' {where}' if where else ''}: {detail}" if detail else f"{head}{f' {where}' if where else ''}"
