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

세 키의 해석(평가 방법론 검토 대상, 결정 기록 20260925-*-data-decision-dt8-scorer.md)
- numeric_ok(수치·단위): COMPLETED이고 보고서를 읽었으며, typed claim 기록에 WRONG_VALUE·WRONG_DIRECTION·WRONG_UNIT·
  WRONG_REFERENT가 없고 산문 기록에 UNBACKED_PROSE가 없다.
- provenance_ok(출처·버전): COMPLETED이고 보고서를 읽었으며, 모든 typed claim 기록의 evidence_ok가 참이고, 보고서의
  snapshot_id·policy_version·grouping_version이 실행 기록과 같다.
- required_evidence_ok(필수 근거): 정답표가 있는 합성 묶음에서만 채운다. COMPLETED이고 보고서를 읽었으며, 정답표가 발동
  신호마다 정한 필수 근거 코드를 모두 채운다(TAG_RULES). 실자료 묶음(real_dev·real_sealed)은 정답표가 없어 null이다
  (사용자 확인 대기, 잠정).
- 유효한 최종 보고서가 없는 실행(COMPLETED가 아님, 보고서 없음)은 세 키가 거짓이다(실자료의 required_evidence_ok는 null).

정답표는 read_answer_table 한 곳에서만 읽는다. 형식은 eval/dev/oracle_ABC.json의 사례 구조를 기준으로 하고
required_evidence는 반드시 있어야 한다(빈 목록은 명시할 때만). 필수 근거 코드는 판정 정책(MT1 단위 P5,
src/tradesentry/policy/required_evidence.py)의 13개와 같은 이름이고, 신호 계열마다 쓸 수 있는 코드가 정해져 있다
(FAMILY_TAGS). 코드별 판정 조건은 잠정이다(MT1 결정 D17의 공개 판정 조건 표가 정해지면 맞춘다).
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
RUN_ID_RE = re.compile(r"[a-z][a-z0-9_]*-[0-9]{12}")  # fullmatch로 쓴다(끝 줄바꿈·유니코드 숫자를 받지 않는다)

# 필수 근거 코드 → 최종 보고서에서 확인하는 것(잠정, MT1 결정 ⑨의 뜻과 개발 플랜 §6.3 "반드시 남길 근거"). 사례 문맥
# (hs6, 대상국 P, 비교월 t, 기준월 b=t−12, grouping_version)이 필요하다. "유효한 claim"은 대상이 풀리고 근거가 맞는
# claim이다(값의 참·거짓은 numeric_ok가 본다). "빠진 키"는 신호 계열의 대상 범위(단가: P의 부모 HS6 키와 C형 HS10 하위,
# 점유율: P의 부모 HS6 키와 ALL 분모, 두 시점)에서 관측 상태가 OBSERVED·CONFIRMED_NO_TRADE가 아닌 키다.
TAG_RULES = {
    "parent_child_match_V_and_Q": "두 시점 모두 HS10 하위 행이 있고, 보고서 근거가 두 시점마다 부모 HS6 행과 그 시점의 "
                                  "HS10 하위 행(코드마다)을 모두 인용한다",
    "weight_share_decomposition": "within_effect·mix_effect·residual 분해 claim이 모두 유효하게 있다",
    "per_child_unit_value_stable": "두 시점의 HS10 하위 품목마다 r_U@ claim(또는 두 시점 U@ claim)이 유효하게 있다",
    "comparability_ok": "신호 계열의 전년동월 변화 claim(단가 r_U, 점유율 d_s) 또는 두 시점 수준 claim(U, s)이 유효하게 "
                        "있다",
    "partner_comparison_done": "비교집합 안 비교국의 계열 지표 comparison claim(단가 r_U 또는 두 시점 U, 점유율 d_s 또는 "
                               "두 시점 s)이 유효하게 있다",
    "missingness_listed": "빠진 키마다 그 키를 OBSERVED가 아닌 상태로 적은 유효한 data_status claim이 있다. 빠진 키가 "
                          "없으면 비교국의 빠진 키를 적은 유효한 data_status claim이나, 계산할 수 없는 계열 지표를 "
                          "null로 적은 CORRECT claim이 하나 이상 있다",
    "failure_vs_not_collected_distinguished": "빠진 키마다 그 상태를 맞게 적은(CORRECT, 인용할 행이 없는 키는 값만 맞은) "
                                              "data_status claim이 있고, 사례 품목·두 시점의 data_status claim에 "
                                              "WRONG_VALUE가 없다",
    "no_zero_fill": "대상이 풀렸고 기대값이 null인 수 claim에 수(0 포함)를 적은 claim이 없다",
    "precision_sensitivity_shown": "대상국의 두 시점 부모 V·Q value claim(4개)이 유효하게 있다(정밀도·민감도의 바탕, "
                                   "U4 확인 전 잠정)",
    "country_and_world_change_shown": "대상국 V와 ALL V의 두 시점 value claim(4개)이 유효하게 있다",
}
CORRECTION_TAGS = ("correction_snapshots_before_after", "recalculated_values", "change_reason")
REQUIRED_EVIDENCE_TAGS = tuple(TAG_RULES) + CORRECTION_TAGS  # 판정 정책 P5의 코드 13개와 같은 이름
FAMILY_TAGS = {  # 신호 계열마다 정답표에 쓸 수 있는 코드(판정 정책 P5 규칙표의 계열별 합집합)
    "unit_value": frozenset({"parent_child_match_V_and_Q", "weight_share_decomposition", "per_child_unit_value_stable",
                             "comparability_ok", "partner_comparison_done", "missingness_listed",
                             "failure_vs_not_collected_distinguished", "no_zero_fill", "precision_sensitivity_shown"}),
    "share": frozenset({"country_and_world_change_shown", "partner_comparison_done", "comparability_ok",
                        "missingness_listed", "failure_vs_not_collected_distinguished", "no_zero_fill"}),
}
FAMILY_NULL_BASES = {  # missingness_listed의 "계산할 수 없는 계열 지표"
    "unit_value": frozenset({"V", "Q", "U", "r_U", "w", "within_effect", "mix_effect", "residual"}),
    "share": frozenset({"V", "s", "d_s"}),
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
    if not isinstance(line["run_id"], str) or not RUN_ID_RE.fullmatch(line["run_id"]):
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


def _required_evidence(value: object, signals: dict[str, str], case_id: str) -> dict[str, list[str]]:
    """정답표 expected.required_evidence를 {발동 신호: 코드 목록}으로 읽는다. 키가 없으면 입력 오류다(빈 목록은 명시할
    때만). 목록 형식은 발동 신호가 하나일 때만 쓰고, 둘 다 발동하면 발동 신호마다 목록을 준 객체여야 한다."""
    triggered = [s for s in SIGNALS if signals[s] == TRIGGERED]
    if isinstance(value, list):
        if len(triggered) != 1:
            _fail(f"정답표 사례 {case_id}는 두 신호가 모두 발동해 required_evidence를 신호별 객체"
                  '({"unit_value": [...], "share": [...]})로 적어야 한다(합친 목록은 공통 코드의 신호를 알 수 없다)')
        by_signal = {triggered[0]: value}
    elif isinstance(value, dict) and set(value) == set(triggered):
        by_signal = {s: value[s] for s in triggered}
    else:
        _fail(f"정답표 사례 {case_id}의 required_evidence가 없거나 발동 신호와 맞지 않다(빈 목록은 명시한다)")
    for signal, tags in by_signal.items():
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags) or len(set(tags)) != len(tags):
            _fail(f"정답표 사례 {case_id}의 required_evidence({signal})가 서로 다른 코드 문자열 목록이 아니다")
        unknown = [t for t in tags if t not in REQUIRED_EVIDENCE_TAGS]
        if unknown:
            _fail(f"정답표 사례 {case_id}의 required_evidence에 채점기가 모르는 코드가 있다({', '.join(unknown)})")
        correction = [t for t in tags if t in CORRECTION_TAGS]
        if correction:
            _fail(f"정답표 사례 {case_id}의 {', '.join(correction)}는 교정 전후 스냅샷이 있어야 채점할 수 있다(동결 "
                  "스냅샷 하나로 도는 v1에는 해당 사례가 없다, MT1 결정 ⑥)")
        outside = [t for t in tags if t not in FAMILY_TAGS[signal]]
        if outside:
            _fail(f"정답표 사례 {case_id}의 {', '.join(outside)}는 {signal} 신호의 필수 근거 코드가 아니다")
    return {signal: list(tags) for signal, tags in by_signal.items()}


def read_answer_table(doc: object) -> dict[str, dict]:
    """정답표를 읽는 단 한 곳이다. 로드맵 DT5가 형식을 정하면 이 함수만 바꾼다.

    eval/dev/oracle_ABC.json의 사례 구조를 기준으로 삼는다. 필드:
    - cases: 목록. 사례마다 case_id(문자열, 고유)와 expected 객체
    - expected.signals: {"unit_value", "share"} → TRIGGERED 또는 NOT_TRIGGERED(발동 신호가 1개 이상)
    - expected.review_status: 한국어 표기(검토 유지·모니터링·자료 보류) 또는 코드(MAINTAIN·MONITOR·HOLD)
    - expected.required_evidence(필수): 발동 신호의 필수 근거 코드. 발동 신호가 하나면 목록, 둘이면 {신호: 목록}.
      빈 목록은 명시할 때만 받는다. 코드는 REQUIRED_EVIDENCE_TAGS 안이고 그 신호 계열의 코드(FAMILY_TAGS)여야 한다
    - 선택 expected.signal_status: 신호별 판정. 두 신호가 모두 발동한 사례는 반드시 있어야 한다. 없으면 발동한 신호는
      사례 상태, 발동하지 않은 신호는 NOT_TRIGGERED로 둔다(자료 계약 §3.2)
    - 선택 expected.unresolved_evidence: 참·거짓. 없으면 사례 집계 규칙으로 정한다
    그 밖의 키(baseline·comparison 원자료, 기대 수치 등)는 채점에 쓰지 않는다(수치 기대값은 채점기가 원본 행에서 따로
    계산한다). 돌려주는 값: {case_id: {"review_status", "signal_status", "unresolved_evidence",
    "required_evidence": {신호: 코드 목록}, "signals"}}."""
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
        review = expected.get("review_status")
        review = KOREAN_STATUS.get(review, review) if isinstance(review, str) else None
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
        if "required_evidence" not in expected:
            _fail(f"정답표 사례 {case_id}에 required_evidence가 없다(필수 근거가 없는 사례는 빈 목록을 명시한다)")
        table[case_id] = {"review_status": review, "signal_status": dict(signal_status),
                          "unresolved_evidence": unresolved,
                          "required_evidence": _required_evidence(expected["required_evidence"], signals, case_id),
                          "signals": dict(signals)}
    return table


# ----------------------------------------------------------------------------- 세 키

def _valid(record: dict) -> bool:
    return bool(record["referent_resolved"]) and bool(record["evidence_ok"])


class _Report:
    """필수 근거 판정에 쓰는 보고서 하나의 claim·기록 짝과 사례 문맥."""

    def __init__(self, report: dict, pairs: list[tuple[dict, dict]], context: dict, snap: c1.Snapshot,
                 snapshot_id: str):
        self.report, self.pairs, self.snap, self.snapshot_id = report, pairs, snap, snapshot_id
        self.hs6, self.partner, self.t = context["hs6"], context["partner"], context["month"]
        self.b = c1.shift_month(self.t, -12)
        self.peers = snap.comparison_set(self.partner, self.hs6, context["grouping_version"]) or frozenset()
        self._cited: set[int] | None = None

    def matches(self, claim_type: str, metric: str, partner: str, period: str, baseline: str | None) -> list:
        return [(c, r) for c, r in self.pairs if c.get("claim_type") == claim_type and c.get("metric") == metric
                and c.get("hs6") == self.hs6 and c.get("partner") == partner and c.get("period") == period
                and c.get("baseline_period") == baseline]

    def present(self, claim_type: str, metric: str, partner: str, period: str, baseline: str | None = None) -> bool:
        """그 대상의 유효한(대상이 풀리고 근거가 맞는) claim이 있는가."""
        return any(_valid(r) for _, r in self.matches(claim_type, metric, partner, period, baseline))

    def change_or_levels(self, claim_type: str, change: str, level_type: str, level: str, partner: str) -> bool:
        """전년동월 변화 claim이나 두 시점 수준 claim이 유효하게 있는가."""
        return self.present(claim_type, change, partner, self.t, self.b) \
            or (self.present(level_type, level, partner, self.t) and self.present(level_type, level, partner, self.b))

    def cited(self) -> set[int]:
        """보고서 근거(보고서 evidence_ids와 claim마다의 evidence_ids)가 가리키는 관측 행(총계 행 제외)."""
        if self._cited is None:
            ids = list(self.report.get("evidence_ids")) if isinstance(self.report.get("evidence_ids"), list) else []
            for claim, _ in self.pairs:
                if isinstance(claim.get("evidence_ids"), list):
                    ids += claim["evidence_ids"]
            rows: set[int] = set()
            for item in ids:
                found, _ = c1.resolve_evidence([item], self.snapshot_id, self.snap)
                rows |= found or set()
            self._cited = rows - self.snap.totals
        return self._cited

    def children(self) -> dict[str, list[frozenset[int]]]:
        """두 시점의 대상국 HS10 하위 행 묶음 {코드: [시점마다의 행 묶음]}."""
        kids: dict[str, list[frozenset[int]]] = {}
        for month in (self.t, self.b):
            for code, rows in self.snap.children.get((self.partner, self.hs6, month), {}).items():
                kids.setdefault(code, []).append(frozenset(rows))
        return kids

    def gaps(self, family: str) -> list[tuple[str, str, str, dict[str, set[int]]]]:
        """신호 계열 대상 범위의 빠진 키 [(상대국, "hs6"|"hs10", 월, {상태: 그 상태의 행})]. 단가는 대상국 부모 HS6 키와
        C형(부모 행이 있는데 그 HS6 조회의 상태 행), 점유율은 대상국 부모 HS6 키와 ALL 분모다. OBSERVED·
        CONFIRMED_NO_TRADE는 빠진 것이 아니다."""
        found = []
        for partner in (self.partner, c1.ALL) if family == "share" else (self.partner,):
            for month in (self.t, self.b):
                by_status, _ = c1.expect_status(self.snap, partner, self.hs6, month, None)
                missing = {k: v for k, v in by_status.items() if k not in (c1.OBSERVED, c1.CONFIRMED_NO_TRADE)}
                if c1.OBSERVED not in by_status and missing:
                    found.append((partner, "hs6", month, missing))
                elif family == "unit_value" and c1.OBSERVED in by_status:
                    hs10 = {k: v for k, v in self.snap.status_rows([(partner, self.hs6, month)]).items()
                            if k != c1.CONFIRMED_NO_TRADE}
                    if hs10:
                        found.append((partner, "hs10", month, hs10))
        return found

    def status_claims(self, partner: str, level: str, month: str) -> list[tuple[dict, dict]]:
        """그 빠진 키를 가리키는 data_status claim(HS6 키는 observation_status, C형은 observation_status@<그 HS6 아래 코드>)."""
        out = []
        for claim, record in self.pairs:
            metric = claim.get("metric")
            if claim.get("claim_type") != "data_status" or not isinstance(metric, str) \
                    or (claim.get("partner"), claim.get("hs6"), claim.get("period")) != (partner, self.hs6, month):
                continue
            base, at, code = metric.partition("@")
            if base == c1.STATUS_METRIC and ((level == "hs6" and not at) or (level == "hs10" and at
                                                                             and code.startswith(self.hs6))):
                out.append((claim, record))
        return out


def _listed(report: _Report, gap: tuple) -> bool:
    """빠진 키를 OBSERVED가 아닌 상태로 적은 유효한 data_status claim이 있는가(인용할 행이 없는 키는 대상만 풀리면 된다)."""
    partner, level, month, statuses = gap
    citable = any(statuses.values())
    return any(claim.get("value") != c1.OBSERVED and record["referent_resolved"] and (record["evidence_ok"] or not citable)
               for claim, record in report.status_claims(partner, level, month))


def _tag_ok(tag: str, family: str, report: _Report) -> bool:
    """필수 근거 코드 하나를 신호 계열 family에서 채웠는가(TAG_RULES, 잠정)."""
    p, t, b = report.partner, report.t, report.b
    if tag == "comparability_ok":
        if family == "unit_value":
            return report.change_or_levels("change", "r_U", "value", "U", p)
        return report.change_or_levels("share_change", "d_s", "share", "s", p)
    if tag == "partner_comparison_done":
        change, level = ("r_U", "U") if family == "unit_value" else ("d_s", "s")
        for peer in sorted(report.peers):
            if report.present("comparison", change, peer, t, b) \
                    or (report.present("comparison", level, peer, t) and report.present("comparison", level, peer, b)):
                return True
        return False
    if tag == "weight_share_decomposition":
        return all(report.present("decomposition", base, p, t, b) for base in c1.DECOMPOSITION_BASES)
    if tag == "parent_child_match_V_and_Q":
        months = [report.snap.children.get((p, report.hs6, m), {}) for m in (t, b)]
        groups = [frozenset(report.snap.parent.get((p, report.hs6, m), [])) for m in (t, b)]
        groups += [frozenset(rows) for kids in months for rows in kids.values()]
        return all(months) and all(group and group & report.cited() for group in groups)
    if tag == "per_child_unit_value_stable":
        kids = report.children()
        return bool(kids) and all(report.change_or_levels("change", f"r_U@{code}", "value", f"U@{code}", p)
                                  for code in kids)
    if tag == "precision_sensitivity_shown":
        return all(report.present("value", metric, p, month) for metric in ("V", "Q") for month in (t, b))
    if tag == "country_and_world_change_shown":
        return all(report.present("value", "V", partner, month) for partner in (p, c1.ALL) for month in (t, b))
    if tag == "missingness_listed":
        gaps = report.gaps(family)
        if gaps:
            return all(_listed(report, gap) for gap in gaps)
        peer_gap = any(claim.get("claim_type") == "data_status" and isinstance(claim.get("partner"), str)
                       and claim["partner"] in report.peers and claim.get("hs6") == report.hs6
                       and claim.get("period") in (t, b) and claim.get("value") != c1.OBSERVED and _valid(record)
                       for claim, record in report.pairs)
        partners = (p, c1.ALL) if family == "share" else (p,)
        null_metric = any(record["outcome"] == c1.CORRECT and claim.get("value") is None
                          and claim.get("claim_type") != "data_status" and claim.get("partner") in partners
                          and claim.get("hs6") == report.hs6 and claim.get("period") in (t, b)
                          and (c1.parse_metric(claim.get("metric")) or ("",))[0] in FAMILY_NULL_BASES[family]
                          for claim, record in report.pairs)
        return peer_gap or null_metric
    if tag == "failure_vs_not_collected_distinguished":
        for partner, level, month, statuses in report.gaps(family):
            citable = any(statuses.values())
            if not any(record["outcome"] == c1.CORRECT or (not citable and record["referent_resolved"]
                                                           and claim.get("value") == record["expected_value"])
                       for claim, record in report.status_claims(partner, level, month)):
                return False
        return not any(claim.get("claim_type") == "data_status" and claim.get("hs6") == report.hs6
                       and claim.get("period") in (t, b) and record["outcome"] == c1.WRONG_VALUE
                       for claim, record in report.pairs)
    if tag == "no_zero_fill":
        return not any(claim.get("claim_type") != "data_status" and record["referent_resolved"]
                       and record["expected_value"] is None and c1.is_number(record["reported_value"])
                       for claim, record in report.pairs)
    raise c1.ScorerInputError(f"채점기가 판정할 수 없는 필수 근거 코드다({tag})")


def required_evidence_ok(tags: dict[str, list[str]], report: dict, claim_records: list[dict], context: dict | None,
                         snap: c1.Snapshot, snapshot_id: str) -> tuple[bool, list[str]]:
    """(모두 채웠는가, 채우지 못한 "신호:코드"). tags는 {발동 신호: 코드 목록}이다. 사례 문맥(hs6·partner·month·
    grouping_version)이 없으면 입력 오류다."""
    if context is None or not all(isinstance(context.get(k), str) for k in ("hs6", "partner", "month",
                                                                            "grouping_version")):
        _fail("필수 근거를 보려면 계획 사례에 hs6·partner·month와 실행 기록의 grouping_version이 있어야 한다")
    claim_records_only = [r for r in claim_records if r["source"] == c1.SOURCE_CLAIM]
    claims = report.get("claims") if isinstance(report.get("claims"), list) else []
    if len(claims) != len(claim_records_only):
        _fail("보고서의 claim 수와 주장 채점 기록 수가 다르다")
    pairs = [(claim, record) for claim, record in zip(claims, claim_records_only) if isinstance(claim, dict)]
    view = _Report(report, pairs, context, snap, snapshot_id)
    missing = [f"{signal}:{tag}" for signal in SIGNALS for tag in tags.get(signal, [])
               if not _tag_ok(tag, signal, view)]
    return not missing, missing


def numeric_ok(claim_records: list[dict]) -> bool:
    return not any((r["source"] == c1.SOURCE_CLAIM and r["outcome"] in NUMERIC_FAILURES)
                   or (r["source"] == c1.SOURCE_PROSE and r["outcome"] == c1.UNBACKED_PROSE) for r in claim_records)


def provenance_ok(claim_records: list[dict], report: dict, line: dict) -> bool:
    versions_match = all(report.get(key) == line[key] for key in ("snapshot_id", "policy_version", "grouping_version"))
    return versions_match and all(r["evidence_ok"] for r in claim_records if r["source"] == c1.SOURCE_CLAIM)


def case_context(case: dict | None, line: dict) -> dict | None:
    """계획 사례의 문맥(hs6·대상국·비교월)에 실행 기록의 grouping_version을 더한다(비교집합과 필수 근거에 쓴다)."""
    return None if case is None else {"hs6": case["hs6"], "partner": case["partner"], "month": case["month"],
                                      "grouping_version": line["grouping_version"]}


def result_line(line: dict, report: dict | None, claim_records: list[dict], answer: dict | None,
                context: dict | None, snap: c1.Snapshot | None) -> dict:
    """실행 쪽 키에 세 채점 키를 더한 실행 결과 기록 한 줄(키 순서는 자료 계약 §8). context는 case_context의 값이다."""
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
    출력: 묶음 기록 순서의 실행 결과 기록(키 24개) 목록. 주장 채점 기록은 단위 C1에 같은 사례 문맥(대상국·품목·
    grouping_version)을 주고 만든 것이어야 한다."""
    if not isinstance(inp, dict) or not isinstance(inp.get("batch"), list):
        raise c1.ScorerInputError("입력은 batch를 가진 객체여야 한다")
    lines = [validate_batch_line(line, i) for i, line in enumerate(inp["batch"])]
    reports = inp.get("reports") or {}
    records = inp.get("claims") or []
    answers = read_answer_table(inp["answers"]) if inp.get("answers") is not None else {}
    cases = {c["case_id"]: c for c in inp.get("cases") or [] if isinstance(c, dict)}
    snap = c1.Snapshot.from_json(inp["snapshot"]) if inp.get("snapshot") is not None else None
    out = []
    for line in lines:
        mine = [r for r in records if r["run_id"] == line["run_id"]]
        out.append(result_line(line, reports.get(line["run_id"]), mine, answers.get(line["case_id"]),
                               case_context(cases.get(line["case_id"]), line), snap))
    return out
