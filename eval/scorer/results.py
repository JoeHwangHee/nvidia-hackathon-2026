"""단위 C3 채점 결과 기록.

단위 ID: C3
도메인명: scorer_results
소유: D
입력: 하네스의 실행 쪽 키 기록(`evaluation_batch_run-{시각}.jsonl`)·필드별 판정
출력: 실행 쪽 키에 채점 키를 더한 사례 × 모드 실행 결과 기록 `scorer_results-{시각}.jsonl`
허용 import: 표준 라이브러리, eval.scorer

PR #18 새 판(옛 C3 scorer_summary를 C3·C4로 나눔)을 따른다.

하네스(단위 E1)의 실행 쪽 키 21개를 검증하고, 샌드박스 밖 채점기가 채우는 세 키(required_evidence_ok·numeric_ok·
provenance_ok)를 더해 실행 결과 기록(자료 계약 docs/rules/DATA_CONTRACT_V1.md §8의 키 24개)을 만든다. 런타임이 세 키를
적었으면 채점기 값이 우선한다(룰북 docs/eval/RULEBOOK.md B4). 하네스 파일은 고치지 않고 새 파일을 쓴다.

세 키의 해석(평가 방법론 검토 대상, 보고서에 적는다)
- numeric_ok(수치·단위): COMPLETED이고 보고서를 읽었으며, typed claim 기록에 WRONG_VALUE·WRONG_DIRECTION·WRONG_UNIT·
  WRONG_REFERENT가 없고 산문 기록에 UNBACKED_PROSE가 없다.
- provenance_ok(출처·버전): COMPLETED이고 보고서를 읽었으며, 모든 typed claim 기록의 evidence_ok가 참이고, 보고서의
  snapshot_id·policy_version·grouping_version이 실행 기록과 같다.
- required_evidence_ok(필수 근거): 정답표가 있는 합성 묶음에서만 채운다. COMPLETED이고 보고서를 읽었으며, 정답표의
  필수 근거 태그를 모두 채운다(REQUIRED_EVIDENCE_TAGS). 실자료 묶음(real_dev·real_sealed)은 정답표가 없어 null이다.
- 유효한 최종 보고서가 없는 실행(COMPLETED가 아님, 보고서 없음)은 세 키가 거짓이다(실자료의 required_evidence_ok는 null).

정답표는 read_answer_table 한 곳에서만 읽는다. 지금 형식은 eval/dev/oracle_ABC.json의 사례 구조를 기준으로 삼았고,
로드맵 DT5가 정답표 형식을 정하면 이 함수(와 태그 표)만 바꾼다.
"""
import re

from eval.scorer import claims as c1

# 실행 결과 기록 키(자료 계약 §8, 명세 §4.10 원문 순서)
RESULT_KEYS = ("run_id", "case_id", "dataset", "mode", "policy_version", "rulebook_version", "snapshot_id",
               "grouping_version", "code_version", "review_status_final", "signal_status", "unresolved_evidence",
               "execution_status", "required_evidence_ok", "numeric_ok", "provenance_ok", "tool_attempts",
               "model_requests", "tokens_in", "tokens_out", "wall_ms", "critic_used", "revision_used", "errors")
SCORER_KEYS = ("required_evidence_ok", "numeric_ok", "provenance_ok")
RUN_SIDE_KEYS = tuple(k for k in RESULT_KEYS if k not in SCORER_KEYS)
COUNT_KEYS = ("tool_attempts", "model_requests", "tokens_in", "tokens_out", "wall_ms")
VERSION_KEYS = ("policy_version", "rulebook_version", "snapshot_id", "grouping_version", "code_version")

DATASETS = ("controlled_fixture_v0", "dev20", "holdout40", "real_dev", "real_sealed")
SYNTHETIC_DATASETS = ("controlled_fixture_v0", "dev20", "holdout40")
SEALED_DATASETS = ("holdout40", "real_sealed")
MODES = ("checklist", "agent", "full", "freeform")
COMPLETED = "COMPLETED"
EXECUTION_STATUSES = (COMPLETED, "FAILED", "TIMEOUT", "INVALID", "BUDGET_EXCEEDED")
REVIEW_STATUSES = ("MAINTAIN", "MONITOR", "HOLD")
NOT_TRIGGERED = "NOT_TRIGGERED"
SIGNAL_STATUSES = REVIEW_STATUSES + (NOT_TRIGGERED,)
SIGNALS = ("unit_value", "share")
TRIGGERED = "TRIGGERED"
KOREAN_STATUS = {"검토 유지": "MAINTAIN", "모니터링": "MONITOR", "자료 보류": "HOLD"}  # 자료 계약 §3.2
RUN_ID_RE = re.compile(r"^[a-z][a-z0-9_]*-\d{12}$")

# 필수 근거 태그 → 최종 보고서에서 확인하는 것(잠정. 정답표 형식과 함께 DT5·평가 방법론 검토로 정한다). 사례 문맥
# (hs6, 대상국, 비교월 t, 기준월 t−12)이 필요하다. "유효하게 있는 claim"은 대상이 풀리고 근거가 맞는 claim이다.
REQUIRED_EVIDENCE_TAGS = {
    "comparability_ok": "사례의 전년동월 단가 변화 r_U claim이 유효하게 있다",
    "parent_child_match_V_and_Q": "보고서 근거가 두 시점의 부모 HS6 행과 HS10 하위 행을 모두 인용한다",
    "weight_share_decomposition": "사례의 within_effect·mix_effect 분해 claim이 모두 유효하게 있다",
    "per_child_unit_value_stable": "두 시점의 HS10 하위 품목마다 r_U@ claim(또는 두 시점 U@ claim)이 유효하게 있다",
    "partner_comparison_done": "사례 기간의 비교국 comparison claim이 1개 이상 유효하게 있다",
    "missingness_listed": "사례 품목·두 시점의 OBSERVED가 아닌 data_status claim이 1개 이상 유효하게 있다",
    "failure_vs_not_collected_distinguished": "REQUEST_FAILED나 NOT_COLLECTED를 맞게 적은 data_status claim이 있고 "
                                              "틀린 data_status claim이 없다",
    "no_zero_fill": "계산할 수 없는 대상에 값(0 포함)을 적은 claim이 없다",
}
NUMERIC_FAILURES = frozenset({c1.WRONG_VALUE, c1.WRONG_DIRECTION, c1.WRONG_UNIT, c1.WRONG_REFERENT})


def _fail(message: str) -> None:
    raise c1.ScorerInputError(message)


# ----------------------------------------------------------------------------- 하네스 줄 검증

def _is_count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_batch_line(line: object, index: int) -> dict:
    """하네스 묶음 기록 한 줄을 검증한다(자료 계약 §3·§8). 채점 키 세 개는 있어도 되고 채점기 값으로 덮는다."""
    where = f"묶음 기록 {index + 1}번째 줄"
    if not isinstance(line, dict):
        _fail(f"{where}이 객체가 아니다")
    extra = sorted(set(line) - set(RESULT_KEYS))
    missing = [key for key in RUN_SIDE_KEYS if key not in line]
    if extra or missing:
        _fail(f"{where}의 키가 계약(§8)과 다르다(없는 키 {missing}, 계약 밖 키 {extra})")
    if not isinstance(line["run_id"], str) or not RUN_ID_RE.match(line["run_id"]):
        _fail(f"{where}의 run_id가 실행명 형식이 아니다")
    if not isinstance(line["case_id"], str) or not line["case_id"]:
        _fail(f"{where}의 case_id가 비었다")
    for key, allowed in (("dataset", DATASETS), ("mode", MODES), ("execution_status", EXECUTION_STATUSES)):
        if line[key] not in allowed:
            _fail(f"{where}의 {key} 값이 계약 밖이다")
    for key in VERSION_KEYS:
        if not isinstance(line[key], str) or not line[key]:
            _fail(f"{where}의 {key}가 문자열이 아니다")
    completed = line["execution_status"] == COMPLETED
    review = line["review_status_final"]
    if completed and review not in REVIEW_STATUSES or not completed and review is not None:
        _fail(f"{where}의 review_status_final이 execution_status와 맞지 않다(COMPLETED가 아니면 null)")
    signal = line["signal_status"]
    signal_ok = isinstance(signal, dict) and set(signal) == set(SIGNALS) \
        and all(v in SIGNAL_STATUSES for v in signal.values())
    if not signal_ok and (completed or signal is not None):
        _fail(f"{where}의 signal_status 형식이 맞지 않다")
    for key in ("unresolved_evidence", "critic_used", "revision_used"):
        if not isinstance(line[key], bool) and (completed or line[key] is not None):
            _fail(f"{where}의 {key}가 참·거짓이 아니다")
    for key in COUNT_KEYS:
        if not _is_count(line[key]) and (completed or line[key] is not None):
            _fail(f"{where}의 {key}가 0 이상의 정수가 아니다")
    if not isinstance(line["errors"], list):
        _fail(f"{where}의 errors가 목록이 아니다")
    return line


# ----------------------------------------------------------------------------- 정답표

def aggregate_status(signal_status: dict[str, str]) -> tuple[str | None, bool]:
    """사례 집계(자료 계약 §3.1): MAINTAIN > HOLD > MONITOR, MAINTAIN과 HOLD가 섞이면 unresolved_evidence=true."""
    statuses = {v for v in signal_status.values() if v != NOT_TRIGGERED}
    for status in ("MAINTAIN", "HOLD", "MONITOR"):
        if status in statuses:
            return status, {"MAINTAIN", "HOLD"} <= statuses
    return None, False


def read_answer_table(doc: object) -> dict[str, dict]:
    """정답표를 읽는 단 한 곳이다. 로드맵 DT5가 형식을 정하면 이 함수만 바꾼다.

    지금은 eval/dev/oracle_ABC.json의 사례 구조를 기준으로 삼는다. 가정한 필드:
    - cases: 목록. 사례마다 case_id(문자열, 고유)와 expected 객체
    - expected.signals: {"unit_value", "share"} → TRIGGERED 또는 NOT_TRIGGERED(발동 신호가 1개 이상)
    - expected.review_status: 한국어 표기(검토 유지·모니터링·자료 보류) 또는 코드(MAINTAIN·MONITOR·HOLD)
    - expected.required_evidence: 필수 근거 태그 목록(REQUIRED_EVIDENCE_TAGS 안의 이름)
    - 선택 expected.signal_status: 신호별 판정. 두 신호가 모두 발동한 사례는 반드시 있어야 한다. 없으면 발동한 신호는
      사례 상태, 발동하지 않은 신호는 NOT_TRIGGERED로 둔다(자료 계약 §3.2)
    - 선택 expected.unresolved_evidence: 참·거짓. 없으면 사례 집계 규칙으로 정한다
    그 밖의 키(baseline·comparison 원자료, 기대 수치 등)는 채점에 쓰지 않는다(수치 기대값은 채점기가 원본 행에서 따로
    계산한다). 돌려주는 값: {case_id: {"review_status", "signal_status", "unresolved_evidence", "required_evidence",
    "signals"}}."""
    if not isinstance(doc, dict) or not isinstance(doc.get("cases"), list) or not doc["cases"]:
        _fail("정답표에 사례 목록(cases)이 없다")
    table: dict[str, dict] = {}
    for case in doc["cases"]:
        case_id = case.get("case_id") if isinstance(case, dict) else None
        expected = case.get("expected") if isinstance(case, dict) else None
        if not isinstance(case_id, str) or not case_id or case_id in table or not isinstance(expected, dict):
            _fail("정답표 사례마다 서로 다른 case_id와 expected 객체가 있어야 한다")
        signals = expected.get("signals")
        if not isinstance(signals, dict) or set(signals) != set(SIGNALS) \
                or any(v not in (TRIGGERED, NOT_TRIGGERED) for v in signals.values()) or TRIGGERED not in signals.values():
            _fail(f"정답표 사례 {case_id}의 signals가 맞지 않다")
        review = KOREAN_STATUS.get(expected.get("review_status"), expected.get("review_status"))
        if review not in REVIEW_STATUSES:
            _fail(f"정답표 사례 {case_id}의 review_status가 맞지 않다")
        signal_status = expected.get("signal_status")
        if signal_status is None:
            if list(signals.values()).count(TRIGGERED) != 1:
                _fail(f"정답표 사례 {case_id}는 두 신호가 모두 발동해 signal_status가 필요하다")
            signal_status = {s: review if signals[s] == TRIGGERED else NOT_TRIGGERED for s in SIGNALS}
        elif not isinstance(signal_status, dict) or set(signal_status) != set(SIGNALS) \
                or any((v == NOT_TRIGGERED) != (signals[s] == NOT_TRIGGERED) or v not in SIGNAL_STATUSES
                       for s, v in signal_status.items()):
            _fail(f"정답표 사례 {case_id}의 signal_status가 signals와 맞지 않다")
        aggregated, unresolved = aggregate_status(signal_status)
        if aggregated != review:
            _fail(f"정답표 사례 {case_id}의 review_status가 신호별 판정의 집계와 다르다")
        if "unresolved_evidence" in expected:
            if not isinstance(expected["unresolved_evidence"], bool):
                _fail(f"정답표 사례 {case_id}의 unresolved_evidence가 참·거짓이 아니다")
            unresolved = expected["unresolved_evidence"]
        tags = expected.get("required_evidence", [])
        if not isinstance(tags, list) or any(t not in REQUIRED_EVIDENCE_TAGS for t in tags):
            _fail(f"정답표 사례 {case_id}의 required_evidence에 채점기가 모르는 태그가 있다(DT5와 맞춘다)")
        table[case_id] = {"review_status": review, "signal_status": dict(signal_status),
                          "unresolved_evidence": unresolved, "required_evidence": list(tags),
                          "signals": dict(signals)}
    return table


# ----------------------------------------------------------------------------- 세 키

def _valid(record: dict) -> bool:
    return bool(record["referent_resolved"]) and bool(record["evidence_ok"])


def _cited_rows(report: dict, snap: c1.Snapshot, snapshot_id: str) -> set[int]:
    rows: set[int] = set()
    ids = list(report.get("evidence_ids") or []) if isinstance(report.get("evidence_ids"), list) else []
    for claim in report.get("claims") or []:
        if isinstance(claim, dict) and isinstance(claim.get("evidence_ids"), list):
            ids += claim["evidence_ids"]
    for item in ids:
        cited, _ = c1.resolve_evidence([item], snapshot_id, snap)
        rows |= cited or set()
    return rows - snap.totals


def _tag_ok(tag: str, pairs: list[tuple[dict, dict]], report: dict, context: dict, snap: c1.Snapshot,
            snapshot_id: str) -> bool:
    hs6, partner, t = context["hs6"], context["partner"], context["month"]
    b = c1.shift_month(t, -12)

    def present(claim_type: str, metric: str, period: str = t, baseline: str | None = b, partner_is=partner) -> bool:
        return any(c.get("claim_type") == claim_type and c.get("metric") == metric and c.get("hs6") == hs6
                   and c.get("period") == period and c.get("baseline_period") == baseline
                   and c.get("partner") == partner_is and _valid(r) for c, r in pairs)

    if tag == "comparability_ok":
        return present("change", "r_U")
    if tag == "weight_share_decomposition":
        return present("decomposition", "within_effect") and present("decomposition", "mix_effect")
    kids = {code for month in (t, b) for code in snap.children.get((partner, hs6, month), {})}
    if tag == "parent_child_match_V_and_Q":
        groups = [set(snap.parent.get((partner, hs6, m), [])) for m in (t, b)]
        groups += [set(rows) for m in (t, b) for rows in snap.children.get((partner, hs6, m), {}).values()]
        cited = _cited_rows(report, snap, snapshot_id)
        return bool(kids) and all(g and g & cited for g in groups)
    if tag == "per_child_unit_value_stable":
        return bool(kids) and all(present("change", f"r_U@{code}")
                                  or (present("value", f"U@{code}", t, None) and present("value", f"U@{code}", b, None))
                                  for code in kids)
    if tag == "partner_comparison_done":
        return any(c.get("claim_type") == "comparison" and c.get("hs6") == hs6 and c.get("period") == t
                   and c.get("partner") != partner and _valid(r) for c, r in pairs)
    statuses = [(c, r) for c, r in pairs if c.get("claim_type") == "data_status"]
    if tag == "missingness_listed":
        return any(c.get("hs6") == hs6 and c.get("partner") in (partner, "ALL") and c.get("period") in (t, b)
                   and c.get("value") != c1.OBSERVED and _valid(r) for c, r in statuses)
    if tag == "failure_vs_not_collected_distinguished":
        return any(c.get("value") in (c1.REQUEST_FAILED, c1.NOT_COLLECTED) and r["outcome"] == c1.CORRECT
                   for c, r in statuses) and not any(r["outcome"] == c1.WRONG_VALUE for _, r in statuses)
    if tag == "no_zero_fill":
        return not any(r["outcome"] == c1.WRONG_VALUE and r["expected_value"] is None and c1.is_number(r["reported_value"])
                       for _, r in pairs)
    raise c1.ScorerInputError(f"채점기가 모르는 필수 근거 태그다({tag})")


def required_evidence_ok(tags: list[str], report: dict, claim_records: list[dict], context: dict | None,
                         snap: c1.Snapshot, snapshot_id: str) -> tuple[bool, list[str]]:
    """(모두 채웠는가, 채우지 못한 태그). 사례 문맥(hs6·partner·month)이 없으면 입력 오류다."""
    if context is None:
        _fail("필수 근거를 보려면 계획 사례에 hs6·partner·month가 있어야 한다")
    claim_records_only = [r for r in claim_records if r["source"] == c1.SOURCE_CLAIM]
    claims = report.get("claims") if isinstance(report.get("claims"), list) else []
    if len(claims) != len(claim_records_only):
        _fail("보고서의 claim 수와 주장 채점 기록 수가 다르다")
    pairs = [(claim, record) for claim, record in zip(claims, claim_records_only) if isinstance(claim, dict)]
    missing = [tag for tag in tags if not _tag_ok(tag, pairs, report, context, snap, snapshot_id)]
    return not missing, missing


def numeric_ok(claim_records: list[dict]) -> bool:
    return not any((r["source"] == c1.SOURCE_CLAIM and r["outcome"] in NUMERIC_FAILURES)
                   or (r["source"] == c1.SOURCE_PROSE and r["outcome"] == c1.UNBACKED_PROSE) for r in claim_records)


def provenance_ok(claim_records: list[dict], report: dict, line: dict) -> bool:
    versions_match = all(report.get(key) == line[key] for key in ("snapshot_id", "policy_version", "grouping_version"))
    return versions_match and all(r["evidence_ok"] for r in claim_records if r["source"] == c1.SOURCE_CLAIM)


def result_line(line: dict, report: dict | None, claim_records: list[dict], answer: dict | None,
                context: dict | None, snap: c1.Snapshot | None) -> dict:
    """실행 쪽 키에 세 채점 키를 더한 실행 결과 기록 한 줄(키 순서는 자료 계약 §8)."""
    scored = line["execution_status"] == COMPLETED and report is not None
    values = {"numeric_ok": scored and numeric_ok(claim_records),
              "provenance_ok": scored and provenance_ok(claim_records, report or {}, line),
              "required_evidence_ok": None}
    if line["dataset"] in SYNTHETIC_DATASETS:
        if answer is None:
            _fail(f"정답표에 사례 {line['case_id']}가 없다")
        values["required_evidence_ok"] = scored and snap is not None and required_evidence_ok(
            answer["required_evidence"], report, claim_records, context, snap, line["snapshot_id"])[0]
    return {key: values[key] if key in SCORER_KEYS else line[key] for key in RESULT_KEYS}


def run(inp: object) -> object:
    """진입 함수. 입력: {"batch": [하네스 줄], "reports": {run_id: 보고서 또는 null}, "claims": [주장 채점 기록(claim·prose)],
    "answers": 정답표 또는 null, "cases": [{"case_id", "hs6", "partner", "month"}], "snapshot": 스냅샷 객체}.
    출력: 묶음 기록 순서의 실행 결과 기록(키 24개) 목록."""
    if not isinstance(inp, dict) or not isinstance(inp.get("batch"), list):
        raise c1.ScorerInputError("입력은 batch를 가진 객체여야 한다")
    lines = [validate_batch_line(line, i) for i, line in enumerate(inp["batch"])]
    reports = inp.get("reports") or {}
    records = inp.get("claims") or []
    answers = read_answer_table(inp["answers"]) if inp.get("answers") is not None else {}
    contexts = {c["case_id"]: c for c in inp.get("cases") or [] if isinstance(c, dict)}
    snap = c1.Snapshot.from_json(inp["snapshot"]) if inp.get("snapshot") is not None else None
    out = []
    for line in lines:
        mine = [r for r in records if r["run_id"] == line["run_id"]]
        out.append(result_line(line, reports.get(line["run_id"]), mine, answers.get(line["case_id"]),
                               contexts.get(line["case_id"]), snap))
    return out
