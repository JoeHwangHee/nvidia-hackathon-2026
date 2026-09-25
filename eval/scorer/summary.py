"""단위 C4 보조 지표·요약.

단위 ID: C4
도메인명: scorer_summary
소유: D
입력: 판정·실행 결과 기록
출력: 보조 지표·Wilson 구간(비율의 신뢰구간 계산법)·요약 `scorer_summary-{시각}.md`
허용 import: 표준 라이브러리, eval.scorer

PR #18 새 판(옛 C3 scorer_summary를 C3·C4로 나눔)을 따른다.

실행 결과 기록(단위 C3)과 주장 채점 기록(단위 C1·C2)으로 룰북 docs/eval/RULEBOOK.md B3(대표 지표)·B4(보조 지표)의
값을 계산하고 B7 양식의 요약을 만든다. 채점기가 모르는 실행 조건은 실행 조건 입력 파일에서 받은 값을 그대로 옮긴다
(자료 계약 docs/rules/DATA_CONTRACT_V1.md §8.2). 요약은 채점기만 쓴다.

- 분모는 결과 줄 수가 아니라 계획 사례 × 모드다. 줄이 없는 계획 실행은 미실행으로 실패에 센다(룰북 B5, 자료 계약 §7.2).
- 같은 (사례, 모드)에 줄이 여럿이면(인프라 실패 재실행) 실행명 시각이 가장 늦은 줄이 분모의 행이고, 가장 이른 줄로
  "재실행 전 기록으로 계산한 값"을 따로 낸다(룰북 B5). 재실행을 원래 실행과 잇는 방법은 F1 전에 MT7과 확정한다.
- 비율마다 Wilson 95% 구간(z = 1.96)을 붙인다. 짝 분석은 Newcombe 짝 차이 95% 구간(1998 방법 10, 연속성 보정 없음)과
  McNemar 정확 검정(양측 이항)이다. 계산은 Decimal(정밀도 50)과 Fraction으로 하고 float를 쓰지 않는다.
- 집계하지 않는 칸(상태 변화: trace 형식 미정, 신호 요건 INVALID: 원인 분류 코드 미정)은 사유를 적는다.
"""
import math
from decimal import ROUND_HALF_UP, Decimal, localcontext
from fractions import Fraction

from eval.scorer import claims as c1
from eval.scorer import results as c3

Z95 = Decimal("1.96")
MISSING = "미기재(실행 조건 입력 파일에 없음)"
DATASET_MODES = {"dev20": ("checklist", "agent", "full"), "holdout40": ("checklist", "agent", "full"),
                 "real_dev": ("freeform", "full"), "real_sealed": ("freeform", "full"),
                 "controlled_fixture_v0": c3.MODES}
FAILURE_STATUSES = ("FAILED", "TIMEOUT", "INVALID", "BUDGET_EXCEEDED")
PROSE_FIELD_GROUPS = ("narrative", "hypotheses", "claims[].text")
MIN_VALID_REPORTS = 20  # 룰북 B3-3 조건 5(조정값)
SCHEMA_VERSION = 2  # 자료 계약 §1.2 계약 버전. 채점기는 tradesentry를 import하지 않으므로 따로 둔다(contract.types와 같게)


# ----------------------------------------------------------------------------- 통계

def _decimal(x: object) -> Decimal:
    if isinstance(x, Fraction):
        with localcontext() as ctx:
            ctx.prec = 50
            return Decimal(x.numerator) / Decimal(x.denominator)
    return Decimal(x)


def wilson(x: int, n: int, z: Decimal = Z95) -> tuple[Decimal, Decimal] | None:
    """Wilson 95% 구간(룰북 B4 식). n이 0이면 None."""
    if n <= 0:
        return None
    with localcontext() as ctx:
        ctx.prec = 50
        p = Decimal(x) / Decimal(n)
        z2 = z * z
        denom = 1 + z2 / n
        center = (p + z2 / (2 * n)) / denom
        half = z * (p * (1 - p) / n + z2 / (4 * n * n)).sqrt() / denom
        return max(Decimal(0), center - half), min(Decimal(1), center + half)


def newcombe_paired(a: int, b: int, c: int, d: int) -> tuple[Decimal, Decimal] | None:
    """짝지은 두 비율의 차 p1 − p2(p1 = (a+b)/n, p2 = (a+c)/n)의 Newcombe 95% 구간(1998 방법 10).
    a: 둘 다 사건, b: 첫째만, c: 둘째만, d: 둘 다 아님."""
    n = a + b + c + d
    if n <= 0:
        return None
    with localcontext() as ctx:
        ctx.prec = 50
        l1, u1 = wilson(a + b, n)
        l2, u2 = wilson(a + c, n)
        p1, p2 = Decimal(a + b) / n, Decimal(a + c) / n
        product = (a + b) * (c + d) * (a + c) * (b + d)
        phi = Decimal(0) if product == 0 else Decimal(a * d - b * c) / Decimal(product).sqrt()
        delta = p1 - p2
        low_sq = (p1 - l1) ** 2 - 2 * phi * (p1 - l1) * (u2 - p2) + (u2 - p2) ** 2
        high_sq = (u1 - p1) ** 2 - 2 * phi * (u1 - p1) * (p2 - l2) + (p2 - l2) ** 2
        return delta - max(Decimal(0), low_sq).sqrt(), delta + max(Decimal(0), high_sq).sqrt()


def mcnemar_exact(b: int, c: int) -> Fraction:
    """McNemar 정확 검정(엇갈린 쌍만 세는 양측 이항 검정)의 p값."""
    n = b + c
    if n == 0:
        return Fraction(1)
    tail = sum(math.comb(n, i) for i in range(min(b, c) + 1))
    return min(Fraction(1), Fraction(2 * tail, 2 ** n))


def median(values: list[int]) -> Fraction | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    return Fraction(ordered[mid]) if len(ordered) % 2 else Fraction(ordered[mid - 1] + ordered[mid], 2)


# ----------------------------------------------------------------------------- 표기

def fmt_num(x: object, digits: int = 1) -> str:
    """수를 소수 digits 자리로 사사오입해 적는다(정수면 그대로)."""
    if x is None:
        return "해당 없음"
    value = _decimal(x) if isinstance(x, Fraction) else Decimal(x)
    if value == value.to_integral_value():
        return str(int(value))
    return str(value.quantize(Decimal(1).scaleb(-digits), rounding=ROUND_HALF_UP))


def fmt_pct(p: object) -> str:
    """비율(0~1)을 백분율 소수 1자리로 적는다."""
    return f"{(_decimal(p) * 100).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}%"


def fmt_rate(x: int, n: int) -> str:
    """x/n = 백분율 (Wilson 95% 하한~상한)."""
    if n <= 0:
        return "해당 없음(분모 0)"
    low, high = wilson(x, n)
    return f"{x}/{n} = {fmt_pct(Fraction(x, n))} ({fmt_pct(low)}~{fmt_pct(high)})"


def fmt_interval(bounds: tuple[Decimal, Decimal] | None) -> str:
    if bounds is None:
        return "해당 없음"
    return f"{fmt_signed_pp(bounds[0])}~{fmt_signed_pp(bounds[1])}"


def fmt_signed_pp(x: Decimal) -> str:
    value = (x * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return f"{'+' if value > 0 else ''}{value}pp"


def fmt_p(p: Fraction) -> str:
    value = _decimal(p)
    if value < Decimal("0.0005"):
        return "<0.001"
    return str(value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))


def fmt_stats(values: list[int]) -> str:
    """평균/중앙값/최대."""
    if not values:
        return "해당 없음"
    return f"{fmt_num(Fraction(sum(values), len(values)))}/{fmt_num(median(values))}/{max(values)}"


def fmt_median_range(values: list[int]) -> str:
    if not values:
        return "해당 없음"
    return f"{fmt_num(median(values))}({min(values)}~{max(values)})"


def cell(value: object) -> str:
    """표 칸·줄에 옮길 값(줄바꿈과 | 를 바꾼다)."""
    if value is None or value == "":
        return MISSING
    if isinstance(value, bool):
        return "참" if value else "거짓"
    text = value if isinstance(value, str) else c1.dumps_json(value)
    return text.replace("\r", " ").replace("\n", " ").replace("|", "／")


def _get(conditions: dict, *path: str) -> object:
    node: object = conditions
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


# ----------------------------------------------------------------------------- 실행 행 고르기

def _stamp(run_id: str) -> str:
    return run_id.rsplit("-", 1)[-1]


class Plan:
    """계획 사례 × 모드와 사례마다 고른 결과 행."""

    def __init__(self, cases: list[dict], modes: list[str], results: list[dict]):
        self.cases = [c["case_id"] for c in cases]
        self.context = {c["case_id"]: c for c in cases}
        self.modes = list(modes)
        grouped: dict[tuple, list[dict]] = {}
        for line in results:
            grouped.setdefault((line["case_id"], line["mode"]), []).append(line)
        for rows in grouped.values():
            rows.sort(key=lambda r: (_stamp(r["run_id"]), r["run_id"]))
        self.grouped = grouped

    def final(self, case_id: str, mode: str) -> dict | None:
        rows = self.grouped.get((case_id, mode))
        return rows[-1] if rows else None

    def first(self, case_id: str, mode: str) -> dict | None:
        rows = self.grouped.get((case_id, mode))
        return rows[0] if rows else None

    def reruns(self, mode: str) -> int:
        return sum(1 for case in self.cases if len(self.grouped.get((case, mode), [])) > 1)

    def series(self) -> int | None:
        keys = {(c.get("hs6"), c.get("partner")) for c in self.context.values()}
        return None if any(None in key for key in keys) else len(keys)


# ----------------------------------------------------------------------------- 대표 지표(B3)

class ClaimIndex:
    """run_id별 주장 채점 기록."""

    def __init__(self, records: list[dict]):
        self.by_run: dict[str, list[dict]] = {}
        for record in records:
            self.by_run.setdefault(record["run_id"], []).append(record)

    def of(self, run_id: str, source: str | None = None) -> list[dict]:
        rows = self.by_run.get(run_id, [])
        return [r for r in rows if source is None or r["source"] == source]


def _field_group(claim_id: str) -> str:
    field = claim_id.split(":")[1] if claim_id.count(":") >= 2 else ""
    if field.startswith("hypotheses"):
        return "hypotheses"
    if field.startswith("claims["):
        return "claims[].text"
    return "narrative"


def report_error(line: dict | None, index: ClaimIndex, unread: set[str], skip_hypotheses: bool = False) -> bool:
    """보고서 단위 오류: 실행 실패·미실행·보고서 없음, 또는 오류 claim이나 UNBACKED_PROSE가 1개 이상(룰북 B3)."""
    if line is None or line["execution_status"] != c3.COMPLETED or line["run_id"] in unread:
        return True
    for record in index.of(line["run_id"]):
        if record["source"] == c1.SOURCE_CLAIM and record["outcome"] != c1.CORRECT:
            return True
        if record["source"] == c1.SOURCE_PROSE and record["outcome"] == c1.UNBACKED_PROSE \
                and not (skip_hypotheses and _field_group(record["claim_id"]) == "hypotheses"):
            return True
    return False


def representative(plan: Plan, index: ClaimIndex, unread: set[str], mode: str) -> dict:
    n = len(plan.cases)
    finals = [plan.final(case, mode) for case in plan.cases]
    valid = [f for f in finals if f is not None and f["execution_status"] == c3.COMPLETED and f["run_id"] not in unread]
    statuses = {s: sum(1 for f in finals if f is not None and f["execution_status"] == s) for s in FAILURE_STATUSES}
    claim_records = [r for f in valid for r in index.of(f["run_id"], c1.SOURCE_CLAIM)]
    prose_records = [r for f in valid for r in index.of(f["run_id"], c1.SOURCE_PROSE)]
    unbacked = [r for r in prose_records if r["outcome"] == c1.UNBACKED_PROSE]
    firsts = [plan.first(case, mode) for case in plan.cases]
    return {
        "planned": n, "completed": sum(1 for f in finals if f is not None and f["execution_status"] == c3.COMPLETED),
        "statuses": statuses, "unrun": sum(1 for f in finals if f is None),
        "report_errors": sum(report_error(f, index, unread) for f in finals),
        "report_errors_no_hyp": sum(report_error(f, index, unread, skip_hypotheses=True) for f in finals),
        "report_errors_first": sum(report_error(f, index, unread) for f in firsts),
        "claim_errors": sum(1 for r in claim_records if r["outcome"] != c1.CORRECT), "claims": len(claim_records),
        "claims_per_report": [len(index.of(f["run_id"], c1.SOURCE_CLAIM)) for f in valid],
        "unbacked_per_report": [sum(1 for r in index.of(f["run_id"], c1.SOURCE_PROSE)
                                    if r["outcome"] == c1.UNBACKED_PROSE) for f in valid],
        "unbacked_by_field": {g: sum(1 for r in unbacked if _field_group(r["claim_id"]) == g)
                              for g in PROSE_FIELD_GROUPS},
        "digits_only": sum(1 for r in claim_records if r["outcome"] == c1.WRONG_VALUE and c1.DIGITS_ONLY_MARK in r["note"]),
        "reruns": plan.reruns(mode), "valid": len(valid),
        "errors_by_case": {case: report_error(f, index, unread) for case, f in zip(plan.cases, finals)},
        "outcomes": {source: {o: sum(1 for f in valid for r in index.of(f["run_id"], source) if r["outcome"] == o)
                              for o in c1.OUTCOMES} for source in (c1.SOURCE_CLAIM, c1.SOURCE_PROSE)},
    }


# ----------------------------------------------------------------------------- 보조 지표(B4)

def state_match(line: dict, answer: dict) -> bool:
    """예상 상태 일치: 사례 판정·신호별 판정·unresolved_evidence가 모두 정답표와 같다(룰북 B4)."""
    return line["review_status_final"] == answer["review_status"] and line["signal_status"] == answer["signal_status"] \
        and line["unresolved_evidence"] == answer["unresolved_evidence"]


def processed(line: dict | None, answer: dict) -> bool:
    """근거 충족 처리정확도의 성공: 예상 상태 일치 AND 필수근거 AND 수치/단위 AND 출처/버전 AND 정상 실행."""
    return line is not None and line["execution_status"] == c3.COMPLETED and state_match(line, answer) \
        and line["required_evidence_ok"] is True and line["numeric_ok"] is True and line["provenance_ok"] is True


def auxiliary(plan: Plan, answers: dict, mode: str) -> dict:
    finals = {case: plan.final(case, mode) for case in plan.cases}
    ran = [f for f in finals.values() if f is not None]
    not_hold = [c for c in plan.cases if answers[c]["review_status"] != "HOLD"]
    maintain_or_hold = [c for c in plan.cases if answers[c]["review_status"] in ("MAINTAIN", "HOLD")]

    def final_status(case: str) -> str | None:
        line = finals[case]
        return line["review_status_final"] if line is not None else None

    confusion = {row: {col: 0 for col in c3.REVIEW_STATUSES + ("실행 실패",)} for row in c3.REVIEW_STATUSES}
    for case in plan.cases:
        confusion[answers[case]["review_status"]][final_status(case) or "실행 실패"] += 1
    return {
        "planned": len(plan.cases), "success": {c: processed(finals[c], answers[c]) for c in plan.cases},
        "unnecessary_hold": (sum(1 for c in not_hold if final_status(c) == "HOLD"), len(not_hold)),
        "wrong_monitor": (sum(1 for c in maintain_or_hold if final_status(c) == "MONITOR"), len(maintain_or_hold)),
        "statuses": {s: sum(1 for f in ran if f["execution_status"] == s) for s in FAILURE_STATUSES},
        "unrun": sum(1 for f in finals.values() if f is None),
        "tools": [f["tool_attempts"] for f in ran if isinstance(f["tool_attempts"], int)],
        "tokens": [f["tokens_in"] + f["tokens_out"] for f in ran
                   if isinstance(f["tokens_in"], int) and isinstance(f["tokens_out"], int)],
        "wall": [f["wall_ms"] for f in ran if isinstance(f["wall_ms"], int)],
        "confusion": confusion, "reruns": plan.reruns(mode),
    }


def all_hold_score(plan: Plan, answers: dict) -> int:
    """모든 사례를 보류했을 때의 점수: 발동 신호는 모두 HOLD, 사례 HOLD로 둔 가상 결과의 예상 상태 일치 수(룰북 B4)."""
    score = 0
    for case in plan.cases:
        answer = answers[case]
        signal = {s: "HOLD" if answer["signals"][s] == c3.TRIGGERED else c3.NOT_TRIGGERED for s in c3.SIGNALS}
        line = {"review_status_final": "HOLD", "signal_status": signal, "unresolved_evidence": False}
        score += state_match(line, answer)
    return score


def paired(first: dict[str, bool], second: dict[str, bool], cases: list[str]) -> tuple[int, int, int, int]:
    """(둘 다, 첫째만, 둘째만, 둘 다 아님) 짝 개수."""
    a = sum(1 for c in cases if first[c] and second[c])
    b = sum(1 for c in cases if first[c] and not second[c])
    c_ = sum(1 for c in cases if not first[c] and second[c])
    return a, b, c_, len(cases) - a - b - c_


# ----------------------------------------------------------------------------- 요약 쓰기

def _conditions_lines(inp: dict, plan: Plan, results: list[dict]) -> list[str]:
    cond = inp.get("conditions") or {}
    meta = inp.get("meta") or {}
    sealed = inp["dataset"] in c3.SEALED_DATASETS

    def versions(key: str) -> str:  # 실행 쪽 값(믿지 않는 입력)이라 cell()로 줄바꿈·표 문법을 바꾼다
        values = sorted({str(r[key]) for r in results})
        if not values:
            return "해당 없음(결과 줄 없음)"
        return cell(values[0]) if len(values) == 1 else f"여러 값({', '.join(cell(v) for v in values)})"

    lines = ["## 0. 실행 조건", ""]
    freeze = _get(cond, "rulebook", "freeze_commit")
    lines.append(f"- 룰북: {versions('rulebook_version')}, 동결 커밋 {cell(freeze) if freeze else '없음(RB-1 동결 전)'}, "
                 f"동결 뒤 변경 {cell(_get(cond, 'rulebook', 'changes_after_freeze'))}")
    lines.append(f"- snapshot_id {versions('snapshot_id')}, 스냅샷 정규화 해시(normalized_sha256) "
                 f"{cell(_get(cond, 'snapshot', 'normalized_sha256'))}, 대조 {cell(_get(cond, 'snapshot', 'normalized_sha256_check'))}")
    lines.append(f"- policy_version {versions('policy_version')}, grouping_version {versions('grouping_version')}"
                 f"(사유: {cell(_get(cond, 'grouping_reason'))})")
    lines.append(f"- code_version {versions('code_version')}, 채점기 커밋 {cell(_get(cond, 'scorer_commit'))}, "
                 f"산문 패턴 목록 커밋 {cell(_get(cond, 'prose_patterns_commit'))}(채점기가 계산한 패턴 목록 지문 "
                 f"sha256 {meta.get('prose_patterns_sha256', MISSING)})")
    lines.append(f"- 실행 기간(KST) {cell(_get(cond, 'run_period', 'start'))} ~ {cell(_get(cond, 'run_period', 'end'))}, "
                 f"동시성 {cell(_get(cond, 'concurrency'))}, 순서 seed {cell(_get(cond, 'order_seed'))}")
    limits = [("도구 호출 시도", "tool_attempts", ""), ("재조사", "reinvestigation", ""), ("모델 요청", "model_requests", ""),
              ("사례당 wall time", "wall_time_s", "초"), ("누적 토큰", "tokens", "")]
    lines.append("- 한도(룰북 B2와 대조한 실행 설정): " + ", ".join(
        f"{label} {cell(_get(cond, 'limits', key))}{unit if _get(cond, 'limits', key) is not None else ''}"
        for label, key, unit in limits))
    lines.append(f"- 샌드박스 이름 {cell(_get(cond, 'sandbox', 'name'))}, 커밋한 라이브 정책 조회 본문(정책 YAML) sha256 "
                 f"{cell(_get(cond, 'sandbox', 'live_policy_sha256'))}, 대조한 시험표 실행 폴더 이름 "
                 f"{cell(_get(cond, 'sandbox', 'violation_tests_run'))}, `configs/openshell/policy.yaml` sha256 "
                 f"{cell(_get(cond, 'sandbox', 'policy_yaml_sha256'))}")
    lines.append(f"- 봉인 해시 재대조 {cell(_get(cond, 'sealed_hash_recheck')) if sealed else '해당 없음(봉인 묶음 아님)'}")
    if sealed:
        lines.append(f"- 봉인 묶음의 출처 점검(평가 스킬 ② 사전 점검 단계 4의 8번) {cell(_get(cond, 'sealed_provenance_check'))}")
    checks = _get(cond, "prescoring_checks") or {}
    unrun = sum(1 for case in plan.cases for mode in plan.modes if plan.final(case, mode) is None)
    case_sets = [frozenset(c for c in plan.cases if plan.final(c, m) is not None) for m in plan.modes]
    lines.append("- 채점 전 확인(평가 스킬 ②): "
                 f"1 예정 실행의 최종 상태 확정 {cell(checks.get('final_status'))}(채점기 계산: 미실행 {unrun}건), "
                 f"2 버전 키 일치 {cell(checks.get('version_keys'))}, "
                 f"5 모드별 사례 집합 일치 {cell(checks.get('mode_case_sets'))}(채점기 계산: "
                 f"{'참' if len(set(case_sets)) <= 1 else '거짓'}), "
                 f"순서 seed·동시성 적용 {cell(checks.get('seed_concurrency'))}, "
                 f"동시성을 올렸다면 근거 결정 기록 {cell(checks.get('concurrency_record'))}")
    lines.append(f"- 사전 점검 결과 {cell(_get(cond, 'precheck'))}")
    lines.append(f"- 계약 버전 schema_version {meta.get('schema_version', SCHEMA_VERSION)}, 자료 묶음 {inp['dataset']}, "
                 f"평가 묶음 실행 {inp['batch_run']}, 채점 실행 {inp['scoring_run']}")
    lines.append(f"- 채점기가 읽은 스냅샷 파일 {cell(meta.get('snapshot_file'))}, 바이트 sha256 "
                 f"{cell(meta.get('snapshot_file_sha256'))}")
    lines.append(f"- 계획: 사례 {len(plan.cases)}건 × 모드 {', '.join(plan.modes)} = 예정 실행 "
                 f"{len(plan.cases) * len(plan.modes)}건, 결과 줄 {len(results)}줄")
    lines.append("- 채점 대상 run_id 목록: " + (", ".join(sorted(r["run_id"] for r in results)) or "없음"))
    if inp["dataset"] == "real_dev":
        lines.append("- real_dev 경보 목록(분모): " + ", ".join(
            f"{cell(c)}({plan.context[c].get('hs6')}·{plan.context[c].get('partner')}·{plan.context[c].get('month')})"
            for c in plan.cases))
    lines.append("- 상태 변화 집계(모델 원초안 → Critic 뒤 → 검증 뒤): 집계하지 않음(trace 형식 미정, 단위 L1. F1 전 보완)")
    return lines


def _rep_table(stats: dict[str, dict], grade: dict[str, str]) -> list[str]:
    head = ("| 모드 | 예정 실행 | COMPLETED | 실행 실패(상태별) | 보고서 단위 오류율(Wilson 95%) | 주장 단위 오류율(참고) | "
            "보고서당 claim 수(평균/중앙값/최대) | 보고서당 UNBACKED_PROSE(평균/중앙값/최대) | "
            "UNBACKED_PROSE 필드별(narrative / hypotheses / claims[].text) | 민감도: hypotheses를 뺀 보고서 단위 오류율 | 등급 |")
    lines = [head, "|" + "---|" * 11]
    for mode, s in stats.items():
        failures = ", ".join(f"{k} {v}" for k, v in s["statuses"].items()) + f", 미실행 {s['unrun']}"
        claim_rate = f"{s['claim_errors']}/{s['claims']} = {fmt_pct(Fraction(s['claim_errors'], s['claims']))}" \
            if s["claims"] else "해당 없음(claim 0건)"
        by_field = " / ".join(str(s["unbacked_by_field"][g]) for g in PROSE_FIELD_GROUPS)
        lines.append(f"| {mode} | {s['planned']} | {s['completed']} | {failures} | "
                     f"{fmt_rate(s['report_errors'], s['planned'])} | {claim_rate} | {fmt_stats(s['claims_per_report'])} | "
                     f"{fmt_stats(s['unbacked_per_report'])} | {by_field} | {fmt_rate(s['report_errors_no_hyp'], s['planned'])} | "
                     f"{grade[mode]} |")
    lines += ["", "| 모드 | 자릿수만 다른 WRONG_VALUE(민감도) | 발동 신호별 주장 요건 미충족으로 생긴 INVALID | "
                  "인프라 실패 재실행(건수 / 재실행 전 기록으로 계산한 보고서 단위 오류율) |", "|---|---|---|---|"]
    for mode, s in stats.items():
        lines.append(f"| {mode} | {s['digits_only']} | 집계하지 않음(원인 분류 코드 미정, 단위 L3) | "
                     f"{s['reruns']} / {fmt_rate(s['report_errors_first'], s['planned'])} |")
    return lines


def _rep_analysis(stats: dict[str, dict], plan: Plan, extremes: dict[str, int]) -> list[str]:
    modes = list(stats)
    lines = [""]
    if len(modes) == 2:
        first, second = modes
        wa = wilson(stats[first]["report_errors"], stats[first]["planned"])
        wb = wilson(stats[second]["report_errors"], stats[second]["planned"])
        if wa is None or wb is None or not (wa[1] < wb[0] or wb[1] < wa[0]):
            verdict = "구간이 겹쳐서 \"차이를 확인하지 못했다\"(차이가 없다는 뜻이 아님)"
        else:
            lower = first if wa[1] < wb[0] else second
            verdict = f"구간이 겹치지 않아 {lower}의 보고서 단위 오류율이 \"낮다\""
        lines.append(f"- 차이 판정(1차, B4 비겹침 규칙): {verdict}")
        a, b, c, d = paired(stats[first]["errors_by_case"], stats[second]["errors_by_case"], plan.cases)
        lines.append(f"- 보조 분석(사전 등록): 짝 비교 둘 다 오류 {a} / {first}만 오류 {b} / {second}만 오류 {c} / "
                     f"둘 다 무오류 {d}, Newcombe 짝 차이 95% 구간({first} − {second}) "
                     f"{fmt_interval(newcombe_paired(a, b, c, d))}, McNemar 정확 검정 p {fmt_p(mcnemar_exact(b, c))}")
    for source in (c1.SOURCE_CLAIM, c1.SOURCE_PROSE):
        allowed = [o for o in c1.OUTCOMES if o != c1.UNBACKED_PROSE] if source == c1.SOURCE_CLAIM \
            else [c1.CORRECT, c1.UNBACKED_PROSE]
        parts = "; ".join(f"{mode} " + ", ".join(f"{o} {stats[mode]['outcomes'][source][o]}" for o in allowed)
                          for mode in modes)
        lines.append(f"- 결과 집합 분포(source={source}): {parts}")
    lines.append("- 극값·순위 표현 건수(참고, 채점 제외): " + " / ".join(f"{m} {extremes.get(m, 0)}" for m in modes))
    lines.append("- 범위 밖: 숫자·증감이 없는 정성 서술과 극값·순위 말의 의미 정확성")
    return lines


def _aux_table(stats: dict[str, dict], grade: str) -> list[str]:
    lines = ["| 비교군 | 근거 충족 처리정확도 x/N(Wilson 95%) | 불필요 보류율 | 잘못된 모니터링률 | 실행 실패 x/N | "
             "도구 시도 중앙값(범위) | 토큰 중앙값(범위) | 시간(ms) 중앙값(범위) | 등급 |", "|" + "---|" * 9]
    for mode, s in stats.items():
        n = s["planned"]
        failures = sum(s["statuses"].values()) + s["unrun"]
        detail = ", ".join(f"{k} {v}" for k, v in s["statuses"].items()) + f", 미실행 {s['unrun']}"
        lines.append(f"| {mode} | {fmt_rate(sum(s['success'].values()), n)} | {fmt_rate(*s['unnecessary_hold'])} | "
                     f"{fmt_rate(*s['wrong_monitor'])} | {failures}/{n}({detail}) | {fmt_median_range(s['tools'])} | "
                     f"{fmt_median_range(s['tokens'])} | {fmt_median_range(s['wall'])} | {grade} |")
    return lines


def _aux_analysis(stats: dict[str, dict], plan: Plan, answers: dict) -> list[str]:
    modes = list(stats)
    lines = ["", f"- 모든 사례를 보류했을 때의 점수: {fmt_rate(all_hold_score(plan, answers), len(plan.cases))}",
             "- 미실행: " + ", ".join(f"{m} {stats[m]['unrun']}건" for m in modes) + f"(분모 {len(plan.cases)}에 실패로 포함)",
             "- 인프라 실패 재실행 건수: " + ", ".join(f"{m} {stats[m]['reruns']}건" for m in modes)]
    for i, first in enumerate(modes):
        for second in modes[i + 1:]:
            a, b, c, d = paired(stats[first]["success"], stats[second]["success"], plan.cases)
            better = sorted(case for case in plan.cases if stats[second]["success"][case] and not stats[first]["success"][case])
            worse = sorted(case for case in plan.cases if stats[first]["success"][case] and not stats[second]["success"][case])
            lines.append(f"- 보조 분석(사전 등록) {first} 대 {second}: 둘 다 성공 {a} / {first}만 성공 {b} / {second}만 성공 {c} / "
                         f"둘 다 실패 {d}, Newcombe 짝 차이 95% 구간({first} − {second}) "
                         f"{fmt_interval(newcombe_paired(a, b, c, d))}, McNemar 정확 검정 p {fmt_p(mcnemar_exact(b, c))}")
            lines.append(f"  - {second}에서 좋아진 사례: {', '.join(map(cell, better)) or '없음'} / "
                         f"나빠진 사례: {', '.join(map(cell, worse)) or '없음'}")
    lines += ["- 상태 변화(원초안 → Critic 뒤 → 검증 뒤): 집계하지 않음(trace 형식 미정, 단위 L1. F1 전 보완)", "",
              "혼동행렬(행: 정답 사례 상태, 열: 최종 사례 상태와 실행 실패)", ""]
    for mode in modes:
        lines += [f"- {mode}", "", "| 정답 \\ 최종 | MAINTAIN | MONITOR | HOLD | 실행 실패 |", "|---|---|---|---|---|"]
        for row, cols in stats[mode]["confusion"].items():
            lines.append(f"| {row} | " + " | ".join(str(cols[k]) for k in c3.REVIEW_STATUSES + ("실행 실패",)) + " |")
        lines.append("")
    return lines


def _a_grade(stats: dict[str, dict], plan: Plan, cond: dict) -> tuple[bool, list[int]]:
    """룰북 B3-3 A등급 주장 조건 7개. 1·2·3·7은 실행 조건 입력 파일, 4·5·6은 채점기가 계산한다."""
    flags = {1: _get(cond, "a_grade", "rb1_frozen"), 2: _get(cond, "a_grade", "hash_recheck_match"),
             3: _get(cond, "a_grade", "scorer_prevalidation"), 7: _get(cond, "a_grade", "scored_once")}
    failed = [k for k, v in flags.items() if v is not True]
    if any(s["unrun"] for s in stats.values()):
        failed.append(4)
    if any(s["valid"] < MIN_VALID_REPORTS for s in stats.values()):
        failed.append(5)
    case_sets = {frozenset(c for c in plan.cases if plan.final(c, m) is not None) for m in stats}
    if len(case_sets) > 1:
        failed.append(6)
    return not failed, sorted(failed)


def render(inp: dict) -> str:
    """요약 문서(룰북 B7 양식)."""
    dataset = inp["dataset"]
    plan = Plan(inp["planned"]["cases"], inp["planned"]["modes"], inp["results"])
    index = ClaimIndex(inp.get("claims") or [])
    unread = set(inp.get("reports_unread") or [])
    cond = inp.get("conditions") or {}
    stats_extra = inp.get("report_stats") or {}
    sealed = dataset in c3.SEALED_DATASETS
    lines = [f"# 평가 결과 요약 — {inp['batch_run']}", "",
             "채점기(eval/scorer)가 쓴 요약이다. 에이전트는 이 파일을 고쳐 쓰지 않는다(자료 계약 §10.3 N8). "
             "등급 표기는 룰북 A5·B7을 따른다.", ""]
    lines += _conditions_lines(inp, plan, inp["results"])

    extremes = {m: sum(stats_extra.get(f["run_id"], {}).get("extremes", 0)
                       for f in (plan.final(c, m) for c in plan.cases) if f is not None) for m in plan.modes}
    rep_stats = aux_stats = None
    if dataset in ("real_dev", "real_sealed"):
        rep_stats = {m: representative(plan, index, unread, m) for m in plan.modes}
    elif dataset != "controlled_fixture_v0" or inp.get("answers") is not None:
        answers = c3.read_answer_table(inp["answers"])
        aux_stats = {m: auxiliary(plan, answers, m) for m in plan.modes}
    else:
        answers = {}

    lines += ["", "## 1. 대표 지표 — 실자료 사실 주장 오류율 (real_sealed)", ""]
    if dataset == "real_sealed":
        ok, failed = _a_grade(rep_stats, plan, cond)
        grade = "등급 A" if ok else "A등급 주장 보류(참고치)"
        lines.append(f"- A등급 주장 조건(B3-3): {'충족' if ok else '미충족(조건 ' + ', '.join(map(str, failed)) + ')'}")
        series = plan.series()
        lines.append(f"- 사례 {len(plan.cases)}건, 서로 다른 시계열 {series if series is not None else '집계 못 함(사례 문맥 없음)'}개. "
                     "한 시계열에서 경보가 여러 건 뽑히면 Wilson 구간의 독립 가정이 약해진다")
        lines += [""] + _rep_table(rep_stats, {m: grade for m in rep_stats}) + _rep_analysis(rep_stats, plan, extremes)
    else:
        lines.append(f"- 해당 없음(이 채점 실행의 자료 묶음은 {dataset}다)")

    lines += ["", "## 2. 보조 지표 — holdout40 (등급 C)", ""]
    if dataset == "holdout40":
        lines += _aux_table(aux_stats, "등급 C") + _aux_analysis(aux_stats, plan, answers)
    else:
        lines.append(f"- 해당 없음(이 채점 실행의 자료 묶음은 {dataset}다)")

    lines += ["", "## 3. 개발 묶음 값 — 대표 숫자 아님 (등급 D)", ""]
    if dataset == "dev20":
        lines += ["- dev20 비교군 3개:", ""] + _aux_table(aux_stats, "등급 D") + _aux_analysis(aux_stats, plan, answers)
    elif dataset == "real_dev":
        series = plan.series()
        lines += ["- real_dev freeform 대 full — \"개발 묶음 값, 대표 숫자 아님\"",
                  f"- 사례 {len(plan.cases)}건, 서로 다른 시계열 {series if series is not None else '집계 못 함'}개", ""]
        lines += _rep_table(rep_stats, {m: "등급 D(개발 묶음 값, 대표 숫자 아님)" for m in rep_stats})
        lines += _rep_analysis(rep_stats, plan, extremes)
    elif dataset == "controlled_fixture_v0":
        lines.append("- controlled_fixture_v0은 개발용 합성 시험자료라 성능 숫자로 보고하지 않는다(룰북 B1). 아래는 참고다.")
        if aux_stats is not None:
            lines += [""] + _aux_table(aux_stats, "참고") + _aux_analysis(aux_stats, plan, answers)
    else:
        lines.append(f"- 해당 없음(이 채점 실행의 자료 묶음은 {dataset}다)")

    lines += ["", "## 4. 참고 지표", ""]
    lines.append(f"- 스킬 호출 성공률(NemoClaw 경로, 정확도 지표에는 영향을 주지 않는다): {cell(_get(cond, 'skill_call_success'))}")
    quality = []
    for mode in plan.modes:
        runs = [f["run_id"] for f in (plan.final(c, mode) for c in plan.cases)
                if f is not None and f["execution_status"] == c3.COMPLETED and f["run_id"] not in unread]
        hangul = sum(stats_extra.get(r, {}).get("hangul", 0) for r in runs)
        latin = sum(stats_extra.get(r, {}).get("latin", 0) for r in runs)
        ratio = fmt_pct(Fraction(hangul, hangul + latin)) if hangul + latin else "해당 없음"
        quality.append(f"{mode} 한글 비율 {ratio}, 금지 표현 {sum(stats_extra.get(r, {}).get('forbidden', 0) for r in runs)}건, "
                       f"필수 항목 누락 {sum(stats_extra.get(r, {}).get('missing', 0) for r in runs)}건")
    review = "금지 해제 조건 뒤 결과표(로드맵 R1)에 적음" if sealed else cell(_get(cond, "korean_sample_review"))
    lines.append("- 한국어 품질(참고, 자동 검사): " + "; ".join(quality)
                 + f". 표본 점검: {review}")
    nat = "금지 해제 조건 뒤 결과표(로드맵 R1)에 적음" if sealed else cell(_get(cond, "nat_profile_summary"))
    lines.append(f"- NAT 프로파일 요약(참고): {nat}")
    if unread:
        reasons: dict[str, int] = {}
        for run_id in unread:
            reason = stats_extra.get(run_id, {}).get("unreadable") or "보고서 파일 없음"
            reasons[reason] = reasons.get(reason, 0) + 1
        lines.append(f"- 보고서를 읽지 못한 COMPLETED 실행 {len(unread)}건(보고서 단위 실패로 셌다): {', '.join(sorted(unread))}"
                     f"(사유: {', '.join(f'{cell(k)} {v}건' for k, v in sorted(reasons.items()))})")

    lines += ["", "## 5. 재현 명령", ""]
    lines.append(f"- 채점 대상 실행: {cell(_get(cond, 'reproduce_evaluate'))}")
    lines.append(f"- 정답 대조 채점: python -m eval.scorer --run {inp['batch_dir']}")
    lines.append(f"- 스냅샷 검증: tradesentry snapshot-verify --snapshot {plan_snapshot(inp['results'])}")
    lines.append(f"- 채점기 입력(보고서 원문) 위치: artifacts/eval/{inp['scoring_run']}/{{run_id}}/(증거 복사 때 함께 복사. "
                 "봉인 묶음은 금지 해제 조건 뒤). 보고서 파일 바이트 sha256:")
    for run_id in sorted(stats_extra):
        digest = stats_extra[run_id].get("report_sha256")
        if digest:
            lines.append(f"  - {run_id}: {digest}")

    lines += ["", "## 6. 한계", ""]
    lines += ["- 봉인의 한계(룰북 B6): 봉인 폴더 위치는 비밀이 아니고, 같은 OS 사용자로 도는 에이전트의 열람을 기술적으로 "
              "막지 못하며, 해시는 변조를 드러낼 뿐 열람을 막지 않는다",
              "- 산문 패턴의 한계(룰북 B3-2): 문장 단위로 주어를 맞추지 않아 우연히 맞는 표현을 놓치고, 배수 표현은 r_U claim만 "
              "뒷받침한다",
              f"- 표본 크기와 신뢰구간 폭: 사례 {len(plan.cases)}건. 한 시계열에서 여러 경보가 뽑히면 독립 가정이 약해진다",
              "- 숫자·증감이 없는 극값·순위 표현은 채점하지 않으므로 틀려도 잡히지 않는다",
              "- 채점기 입력(보고서 원문)은 증거 복사 전까지 outputs/에만 있어 저장소만으로 재채점할 수 없다",
              "- 승격 규칙(CONFIRMED_NO_TRADE)은 policy_v1 승인 전이라 채점기가 따로 적용하지 않고 스냅샷 표시를 썼다"
              "(F1 전 보완)", ""]
    return "\n".join(lines)


def plan_snapshot(results: list[dict]) -> str:
    values = sorted({r["snapshot_id"] for r in results})
    return cell(values[0]) if len(values) == 1 else "<snapshot_id>"


def run(inp: object) -> object:
    """진입 함수. 입력: {"dataset", "batch_run", "batch_dir", "scoring_run", "planned": {"cases", "modes"},
    "results": [실행 결과 기록], "claims": [주장 채점 기록], "answers": 정답표 또는 null, "report_stats": {run_id: {...}},
    "reports_unread": [run_id], "conditions": {실행 조건}, "meta": {...}}. 출력: 요약 문서(마크다운 문자열)."""
    if not isinstance(inp, dict) or not isinstance(inp.get("planned"), dict) or not isinstance(inp.get("results"), list):
        raise c1.ScorerInputError("입력은 planned와 results를 가진 객체여야 한다")
    return render(inp)
