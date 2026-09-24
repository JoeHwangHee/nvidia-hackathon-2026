"""단위 V4 holdout40 결정적 검사.

단위 ID: V4
도메인명: datagen_holdout40_check
소유: D
입력: 사례 목록(`cases.json`)·정답표(`answers.json`)·dev20 부모 원본 계열 ID 목록(`parent_series_ids.json`)의 경로
출력: 스키마·분류별 건수·dev20과 부모 원본 계열 ID 겹침 0 검사 보고(건수만)
허용 import: 표준 라이브러리, tradesentry.contract, eval.datagen

합성 평가 묶음(holdout40, 그리고 같은 형식인 dev20)의 입력 사례 목록과 정답표를 결정적으로 검사한다. 정본은 공개
시나리오 명세 eval/scenarios/SCENARIO_SPEC.md(분류 10개와 배분, 판정 근거 규칙, 파일 형식, 부모 원본 계열 ID)다.
분류와 배분은 구 개발계획(`Pasted markdown.md`) §8.1과 룰북 docs/eval/RULEBOOK.md B1을 따른다.

검사(모두 결정적이다. 같은 입력이면 같은 보고)
1. 사례 목록 스키마: 키, `schema_version`, `dataset`, `snapshot_id`, `policy_version`, 사례 항목의 키 네 개
   (`case_id`, `hs6`, `partner`, `month`)만. 사례 목록에는 기대 상태·분류·생성 계열을 두지 않는다(입력 하위 경로는
   채점 대상 실행 샌드박스가 읽는다).
2. 정답표 스키마: 사례마다 `case_id`, `scenario_class`(1~10), `parent_series_id`(`ps_` + 16진수 소문자 16자),
   `rule`(신호별 판정 근거 규칙 키), `expected`(`signals`, `signal_status`, `review_status`, `unresolved_evidence`,
   `required_evidence`), 선택 `note`. 판정 근거 규칙 키가 정하는 신호별 상태·필수 근거와 사례 집계
   (`MAINTAIN > HOLD > MONITOR`, `MAINTAIN`과 `HOLD`가 섞이면 `unresolved_evidence`=true)가 맞아야 한다. 필수 근거는
   판정 정책(MT1) 결정 기록 ⑨의 어휘 13개만 쓴다.
3. 사례 식별자: CLI가 받는 형식(영문·숫자로 시작하고 끝나며 영문·숫자·밑줄·하이픈, 64자 이하), 묶음 안 고유, 사례 목록과
   정답표의 식별자 집합이 같다. 식별자가 `{hs6}-{partner}-{month}` 모양이면 사례 목록의 세 값과 같아야 한다.
4. 분류 규칙: 분류마다 명세의 기대 처리(발동 신호와 판정 근거 규칙)를 따른다.
5. 분류별 건수: 묶음의 배분(dev20 3·3·2·2·2·2·2·2·1·1, holdout40 6·6·4·4·4·4·4·4·2·2)과 전체 건수.
6. dev20과 겹침: holdout40 정답표의 부모 원본 계열 ID가 dev20 목록에 하나도 없다(dev20 묶음을 검사할 때는 건너뛴다).

보고에는 건수와 검사 이름·위반 종류만 적는다. 사례 식별자, 값, 파일 경로를 적지 않는다(봉인 묶음을 검사할 때 내용이
드러나지 않게, 자료 계약 §10.3 N10·N13). 봉인 폴더를 기본 입력으로 읽지 않는다. 사례 목록·정답표 경로는 부르는 쪽이
명시해서 준다(기본값은 dev20 목록 경로 하나뿐이다).

실행
- 단위 하나 실행(개발 전용): `uv run --locked python -m tradesentry.units V4 --in <입력 JSON>`. 입력은
  {"cases_file", "answers_file", "dev20_parent_series_ids_file"?}이고 경로는 절대경로이거나 저장소 루트 기준이다.
- 검사 명령: `uv run --locked python -m eval.datagen.holdout40_check --cases <사례 목록> --answers <정답표>
  [--dev20-ids <dev20 목록>]`. 보고(JSON)를 표준 출력에 쓰고, 모든 검사가 통과하면 종료 코드 0, 하나라도 실패하면 1,
  인자나 입력 파일을 읽지 못하면 2다.
"""
import argparse
import json
import re
import sys
from pathlib import Path

from tradesentry.contract import types

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DEV20_IDS = "eval/dev/dev20/answers/parent_series_ids.json"

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_USAGE = 2

SCHEMA_VERSION = types.SCHEMA_VERSION
UNIT_VALUE, SHARE = types.SIGNALS
TRIGGERED, NOT_TRIGGERED = types.SIGNAL_TRIGGERS
MAINTAIN, MONITOR, HOLD = types.REVIEW_STATUSES
SYNTHETIC_DATASETS = ("dev20", "holdout40")

# 분류 번호 → (통제 조건, dev20 건수, holdout40 건수). 구 개발계획 §8.1, 룰북 B1 표 그대로.
CLASSES = {
    1: ("하위 단가 고정, 구성비만 변화", 3, 6),
    2: ("구성효과를 뺀 뒤 남는 변화", 3, 6),
    3: ("비교국 동반 변화, 구성 설명 미성립", 2, 4),
    4: ("월 누락·API 실패·미수집", 2, 4),
    5: ("단위·HS 버전·하위 합계 불일치", 2, 4),
    6: ("작은 기준월 값·반올림 불확실·중량 0", 2, 4),
    7: ("분모 완전성 부족·국가 집합 변경", 2, 4),
    8: ("정상 점유율 계산에서 남는 급변", 2, 4),
    9: ("복구할 수 있는 잘못된 조회 범위", 1, 2),
    10: ("두 신호의 판정이 다름", 1, 2),
}
ALLOCATION = {"dev20": {k: v[1] for k, v in CLASSES.items()}, "holdout40": {k: v[2] for k, v in CLASSES.items()}}
TOTALS = {name: sum(counts.values()) for name, counts in ALLOCATION.items()}

# 필수 근거 어휘 13개(판정 정책 결정 기록 20260925-0025 ⑨, 단위 P5의 이름). import하지 않고 글자 그대로 옮겼다.
EVIDENCE_VOCABULARY = (
    "parent_child_match_V_and_Q", "weight_share_decomposition", "per_child_unit_value_stable", "comparability_ok",
    "partner_comparison_done", "missingness_listed", "failure_vs_not_collected_distinguished", "no_zero_fill",
    "precision_sensitivity_shown", "correction_snapshots_before_after", "recalculated_values", "change_reason",
    "country_and_world_change_shown",
)
_HOLD_MISSING = ("missingness_listed", "failure_vs_not_collected_distinguished", "no_zero_fill")

# 판정 근거 규칙: 신호 계열 → 규칙 키 → (신호 상태, 필수 근거 순서). 명세 §5가 정본 설명이다.
# composition_explained·unexplained·hold_missing·rounding_unstable은 단위 P5 규칙표(판정 근거 composition_explained,
# unexplained, data_insufficient·comparison_incomplete, rounding_unstable)와 상태·근거가 같다. hold_inconsistent(관측은
# 있으나 부모·하위 대조, 분해, 분모가 성립하지 않는 자료 보류)는 P5에 따로 없는 잠정 규칙이다(MT1 결정 기록 "영향과
# 넘길 곳"의 D17 제안을 따랐다. 사용자·오케스트레이터 확정 전).
RULES = {
    UNIT_VALUE: {
        "composition_explained": (MONITOR, ("parent_child_match_V_and_Q", "weight_share_decomposition",
                                            "per_child_unit_value_stable", "comparability_ok")),
        "unexplained": (MAINTAIN, ("parent_child_match_V_and_Q", "weight_share_decomposition",
                                   "partner_comparison_done", "comparability_ok")),
        "hold_missing": (HOLD, _HOLD_MISSING),
        "hold_inconsistent": (HOLD, ("parent_child_match_V_and_Q", "comparability_ok", "no_zero_fill")),
        "rounding_unstable": (HOLD, ("precision_sensitivity_shown",)),
    },
    SHARE: {
        "unexplained": (MAINTAIN, ("country_and_world_change_shown", "partner_comparison_done", "comparability_ok")),
        "hold_missing": (HOLD, _HOLD_MISSING),
        "hold_inconsistent": (HOLD, ("country_and_world_change_shown", "comparability_ok", "no_zero_fill")),
    },
}

# 분류별 기대 처리(명세 §4). 계열 → 허용하는 규칙 키 집합(None이면 그 신호는 발동하지 않는다). 9는 제약 없음,
# 4는 발동한 신호가 모두 hold_missing, 10은 두 신호가 모두 발동하고 신호별 상태가 달라야 한다.
CLASS_RULES = {
    1: {UNIT_VALUE: {"composition_explained"}, SHARE: None},
    2: {UNIT_VALUE: {"unexplained"}, SHARE: None},
    3: {UNIT_VALUE: {"unexplained"}, SHARE: None},
    4: "hold_missing_all",
    5: {UNIT_VALUE: {"hold_inconsistent"}, SHARE: None},
    6: {UNIT_VALUE: {"rounding_unstable", "hold_inconsistent"}, SHARE: None},
    7: {UNIT_VALUE: None, SHARE: {"hold_inconsistent", "hold_missing"}},
    8: {UNIT_VALUE: None, SHARE: {"unexplained"}},
    9: "any",
    10: "both_differ",
}

CASE_ID_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9_-]*[A-Za-z0-9])?")  # CLI 사례 인자 형식(64자 이하)
CASE_ID_MAX = 64
P2_CASE_ID_RE = re.compile(r"([0-9]{6})-([A-Z]{2})-([0-9]{6})")  # 판정 정책 P2 형식 `{hs6}-{partner}-{month}`
PARTNER_RE = re.compile(r"[A-Z]{2}")
SNAPSHOT_ID_RE = re.compile(r"[a-z0-9][a-z0-9_]*")
PARENT_ID_RE = re.compile(r"ps_[0-9a-f]{16}")
HEX64_RE = re.compile(r"[0-9a-f]{64}")

CASES_DOC_KEYS = {"schema_version", "dataset", "snapshot_id", "policy_version", "cases"}
CASES_DOC_OPTIONAL = {"snapshot_normalized_sha256"}
CASE_ITEM_KEYS = ("case_id", "hs6", "partner", "month")
ANSWERS_DOC_KEYS = {"schema_version", "dataset", "snapshot_id", "policy_version", "cases"}
ANSWERS_DOC_OPTIONAL = {"thresholds"}
ANSWER_KEYS = {"case_id", "scenario_class", "parent_series_id", "rule", "expected"}
ANSWER_OPTIONAL = {"note"}
EXPECTED_KEYS = {"signals", "signal_status", "review_status", "unresolved_evidence", "required_evidence"}
IDS_DOC_KEYS = {"schema_version", "dataset", "id_rule", "parent_series_ids"}


class CheckInputError(Exception):
    """입력 파일을 읽을 수 없다(없음, JSON 아님). 메시지에 경로를 넣지 않는다."""


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def aggregate(signal_status: dict) -> tuple[str, bool]:
    """신호별 판정 → (사례 상태, unresolved_evidence). 우선순위 `MAINTAIN > HOLD > MONITOR`(자료 계약 §3.1)."""
    values = [signal_status[s] for s in types.SIGNALS if signal_status[s] != NOT_TRIGGERED]
    for status in types.CASE_STATUS_PRIORITY:
        if status in values:
            return status, MAINTAIN in values and HOLD in values
    raise ValueError("발동한 신호가 없다")


def rule_outcome(rule: dict) -> tuple[dict, dict, str, bool, list | dict]:
    """신호별 판정 근거 규칙 키 → (signals, signal_status, review_status, unresolved_evidence, required_evidence).

    required_evidence는 발동한 신호가 하나면 그 규칙의 근거 목록이고, 두 신호가 모두 발동하면 신호별 목록 객체
    {"unit_value": [...], "share": [...]}다(두 신호에 함께 쓰이는 코드가 어느 신호의 근거인지 드러나게. 독립 채점기의
    정답표 형식과 같다)."""
    signals, status, by_signal = {}, {}, {}
    for family in types.SIGNALS:
        key = rule.get(family)
        if key is None:
            signals[family], status[family] = NOT_TRIGGERED, NOT_TRIGGERED
            continue
        signal_state, codes = RULES[family][key]
        signals[family], status[family] = TRIGGERED, signal_state
        by_signal[family] = list(codes)
    review, unresolved = aggregate(status)
    evidence = next(iter(by_signal.values())) if len(by_signal) == 1 else by_signal
    return signals, status, review, unresolved, evidence


# ----------------------------------------------------------------------------- 문서 검사
def cases_problems(doc: object) -> tuple[list[str], dict]:
    """사례 목록의 위반 종류 목록과 {case_id: (hs6, partner, month)}. 위반 종류 글자에는 사례 내용을 넣지 않는다."""
    problems: list[str] = []
    cases: dict[str, tuple] = {}
    if not isinstance(doc, dict) or not CASES_DOC_KEYS <= set(doc) or set(doc) - CASES_DOC_KEYS - CASES_DOC_OPTIONAL:
        return ["사례 목록 최상위 키가 형식과 다르다"], cases
    if not _is_int(doc["schema_version"]) or doc["schema_version"] != SCHEMA_VERSION:
        problems.append("사례 목록 schema_version이 1이 아니다")
    if doc["dataset"] not in SYNTHETIC_DATASETS:
        problems.append("사례 목록 dataset이 dev20·holdout40이 아니다")
    if not isinstance(doc["snapshot_id"], str) or not SNAPSHOT_ID_RE.fullmatch(doc["snapshot_id"]):
        problems.append("사례 목록 snapshot_id 형식이 맞지 않다")
    if not isinstance(doc["policy_version"], str) or not doc["policy_version"]:
        problems.append("사례 목록 policy_version이 비었다")
    digest = doc.get("snapshot_normalized_sha256")
    if "snapshot_normalized_sha256" in doc and not (isinstance(digest, str) and HEX64_RE.fullmatch(digest)):
        problems.append("사례 목록 snapshot_normalized_sha256이 16진수 소문자 64자가 아니다")
    items = doc["cases"]
    if not isinstance(items, list) or not items:
        return problems + ["사례 목록 cases가 비었거나 목록이 아니다"], cases
    for item in items:
        if not isinstance(item, dict) or set(item) != set(CASE_ITEM_KEYS):
            problems.append("사례 항목의 키가 case_id·hs6·partner·month 넷이 아니다")
            continue
        case_id, hs6, partner, month = (item[k] for k in CASE_ITEM_KEYS)
        if not (isinstance(case_id, str) and len(case_id) <= CASE_ID_MAX and CASE_ID_RE.fullmatch(case_id)):
            problems.append("case_id 형식이 CLI 사례 인자 형식이 아니다")
            continue
        if case_id in cases:
            problems.append("case_id가 묶음 안에서 겹친다")
            continue
        if not (isinstance(hs6, str) and types.HS6_RE.fullmatch(hs6)):
            problems.append("hs6가 숫자 6자리가 아니다")
        if not (isinstance(partner, str) and PARTNER_RE.fullmatch(partner)):
            problems.append("partner가 영문 대문자 2자가 아니다")
        if not (isinstance(month, str) and types.MONTH_RE.fullmatch(month)):
            problems.append("month가 YYYYMM이 아니다")
        match = P2_CASE_ID_RE.fullmatch(case_id)
        if match and match.groups() != (hs6, partner, month):
            problems.append("{hs6}-{partner}-{month} 모양의 case_id가 항목의 세 값과 다르다")
        cases[case_id] = (hs6, partner, month)
    return problems, cases


def _expected_problems(entry: dict) -> list[str]:
    rule = entry["rule"]
    if not isinstance(rule, dict) or set(rule) != set(types.SIGNALS):
        return ["rule이 신호 코드 두 개를 키로 가진 객체가 아니다"]
    for family in types.SIGNALS:
        if rule[family] is not None and rule[family] not in RULES[family]:
            return [f"rule.{family}가 판정 근거 규칙 키가 아니다"]
    if all(rule[f] is None for f in types.SIGNALS):
        return ["발동한 신호가 없다(rule이 모두 null)"]
    expected = entry["expected"]
    if not isinstance(expected, dict) or set(expected) != EXPECTED_KEYS:
        return ["expected의 키가 signals·signal_status·review_status·unresolved_evidence·required_evidence가 아니다"]
    problems: list[str] = []
    evidence = expected["required_evidence"]
    lists = list(evidence.values()) if isinstance(evidence, dict) else [evidence]
    if not lists or any(not isinstance(codes, list) or any(code not in EVIDENCE_VOCABULARY for code in codes)
                        or len(set(codes)) != len(codes) for codes in lists):
        problems.append("required_evidence에 어휘 13개 밖의 이름이나 겹친 이름이 있다")
    if not isinstance(expected["unresolved_evidence"], bool):
        problems.append("unresolved_evidence가 참·거짓이 아니다")
    signals, status, review, unresolved, codes = rule_outcome(rule)
    if expected["signals"] != signals:
        problems.append("signals가 rule과 맞지 않다")
    if expected["signal_status"] != status:
        problems.append("signal_status가 rule의 신호별 상태와 맞지 않다")
    if expected["review_status"] != review:
        problems.append("review_status가 신호별 판정의 집계와 다르다")
    if expected["unresolved_evidence"] is not unresolved:
        problems.append("unresolved_evidence가 집계 규칙과 다르다")
    if evidence != codes:
        problems.append("required_evidence가 판정 근거 규칙의 필수 근거와 다르다")
    return problems


def class_rule_problems(scenario_class: int, rule: dict) -> list[str]:
    """분류의 기대 처리(명세 §4)와 신호별 판정 근거 규칙이 맞는가."""
    spec = CLASS_RULES[scenario_class]
    wrong = [f"분류 {scenario_class}의 기대 처리와 다르다"]
    if spec == "any":
        return []
    if spec == "hold_missing_all":
        keys = [rule[f] for f in types.SIGNALS if rule[f] is not None]
        return [] if keys and all(k == "hold_missing" for k in keys) else wrong
    if spec == "both_differ":
        if any(rule[f] is None for f in types.SIGNALS):
            return wrong
        _, status, _, _, _ = rule_outcome(rule)
        return [] if status[UNIT_VALUE] != status[SHARE] else wrong
    for family in types.SIGNALS:
        allowed = spec[family]
        if (allowed is None) != (rule[family] is None) or (allowed is not None and rule[family] not in allowed):
            return wrong
    return []


def answers_problems(doc: object) -> tuple[list[str], dict]:
    """정답표의 위반 종류 목록과 {case_id: 정답 항목}."""
    problems: list[str] = []
    entries: dict[str, dict] = {}
    if not isinstance(doc, dict) or not ANSWERS_DOC_KEYS <= set(doc) or set(doc) - ANSWERS_DOC_KEYS - ANSWERS_DOC_OPTIONAL:
        return ["정답표 최상위 키가 형식과 다르다"], entries
    if not _is_int(doc["schema_version"]) or doc["schema_version"] != SCHEMA_VERSION:
        problems.append("정답표 schema_version이 1이 아니다")
    if doc["dataset"] not in SYNTHETIC_DATASETS:
        problems.append("정답표 dataset이 dev20·holdout40이 아니다")
    items = doc["cases"]
    if not isinstance(items, list) or not items:
        return problems + ["정답표 cases가 비었거나 목록이 아니다"], entries
    for entry in items:
        if not isinstance(entry, dict) or not ANSWER_KEYS <= set(entry) or set(entry) - ANSWER_KEYS - ANSWER_OPTIONAL:
            problems.append("정답 항목의 키가 형식과 다르다")
            continue
        case_id = entry["case_id"]
        if not (isinstance(case_id, str) and len(case_id) <= CASE_ID_MAX and CASE_ID_RE.fullmatch(case_id)):
            problems.append("정답 항목 case_id 형식이 CLI 사례 인자 형식이 아니다")
            continue
        if case_id in entries:
            problems.append("정답표 case_id가 겹친다")
            continue
        entries[case_id] = entry
        if not _is_int(entry["scenario_class"]) or entry["scenario_class"] not in CLASSES:
            problems.append("scenario_class가 1~10 정수가 아니다")
            continue
        if not (isinstance(entry["parent_series_id"], str) and PARENT_ID_RE.fullmatch(entry["parent_series_id"])):
            problems.append("parent_series_id가 ps_ + 16진수 소문자 16자가 아니다")
        if "note" in entry and not isinstance(entry["note"], str):
            problems.append("note가 글자가 아니다")
        found = _expected_problems(entry)
        problems += found
        if not found:
            problems += class_rule_problems(entry["scenario_class"], entry["rule"])
    return problems, entries


def dev20_ids(doc: object) -> tuple[list[str], set[str]]:
    """dev20 부모 원본 계열 ID 목록 문서 → (위반 종류, ID 집합)."""
    if not isinstance(doc, dict) or set(doc) != IDS_DOC_KEYS or doc.get("dataset") != "dev20" \
            or not isinstance(doc.get("parent_series_ids"), list):
        return ["dev20 부모 원본 계열 ID 목록의 형식이 맞지 않다"], set()
    ids = doc["parent_series_ids"]
    if not ids or not all(isinstance(i, str) and PARENT_ID_RE.fullmatch(i) for i in ids):
        return ["dev20 부모 원본 계열 ID가 ps_ + 16진수 소문자 16자가 아니다"], set()
    return [], set(ids)


def _kinds(problems: list[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for kind in problems:
        out[kind] = out.get(kind, 0) + 1
    return dict(sorted(out.items()))


def check_documents(cases_doc: object, answers_doc: object, ids_doc: object | None) -> dict:
    """세 문서를 검사한 보고. 건수·검사 이름·위반 종류만 담는다."""
    checks: list[dict] = []

    def add(name: str, problems: list[str] | None, **extra: object) -> None:
        entry: dict = {"name": name, "ok": None if problems is None else not problems}
        if problems:
            entry["problems"] = _kinds(problems)
        entry.update(extra)
        checks.append(entry)

    case_problems, cases = cases_problems(cases_doc)
    add("cases_schema", case_problems, cases=len(cases))
    answer_problems, entries = answers_problems(answers_doc)
    add("answers_schema", answer_problems, cases=len(entries))
    dataset = cases_doc.get("dataset") if isinstance(cases_doc, dict) else None
    header: list[str] = []
    if isinstance(cases_doc, dict) and isinstance(answers_doc, dict):
        for key in ("schema_version", "dataset", "snapshot_id", "policy_version"):
            if cases_doc.get(key) != answers_doc.get(key):
                header.append(f"사례 목록과 정답표의 {key}가 다르다")
    same = set(cases) == set(entries)
    add("case_ids_match", header + ([] if same else ["사례 목록과 정답표의 case_id 집합이 다르다"]))
    counts = {str(k): 0 for k in CLASSES}
    for entry in entries.values():
        if _is_int(entry.get("scenario_class")) and entry["scenario_class"] in CLASSES:
            counts[str(entry["scenario_class"])] += 1
    allocation = ALLOCATION.get(dataset)
    if allocation is None:
        add("class_counts", ["dataset이 dev20·holdout40이 아니라 배분을 정할 수 없다"], by_class=counts)
    else:
        wrong = [f"분류 {k}의 건수가 배분과 다르다" for k, n in allocation.items() if counts[str(k)] != n]
        if len(entries) != TOTALS[dataset] or len(cases) != TOTALS[dataset]:
            wrong.append("전체 건수가 배분 합계와 다르다")
        add("class_counts", wrong, by_class=counts, total=len(entries), expected_total=TOTALS[dataset])
    overlap = None
    if dataset == "dev20":
        add("dev20_parent_series_overlap", None, skipped="dev20 묶음 자체라 겹침 검사를 하지 않는다")
    else:
        id_problems, known = dev20_ids(ids_doc) if ids_doc is not None else (["dev20 목록이 없다"], set())
        ours = {e["parent_series_id"] for e in entries.values() if isinstance(e.get("parent_series_id"), str)}
        overlap = len(ours & known)
        add("dev20_parent_series_overlap", id_problems + (["dev20과 부모 원본 계열 ID가 겹친다"] if overlap else []),
            overlap=overlap, dev20_ids=len(known))
    return {"dataset": dataset, "ok": all(c["ok"] is not False for c in checks), "checks": checks,
            "counts": {"cases": len(cases), "answers": len(entries), "by_class": counts},
            "overlap_with_dev20": overlap}


# ----------------------------------------------------------------------------- 파일 입력과 명령
def _repo_path(value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise CheckInputError("경로가 비었다")
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def load_json(path: Path) -> object:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeDecodeError) as exc:
        raise CheckInputError(f"입력 파일을 읽지 못했다({type(exc).__name__})") from exc


def check_files(cases_file: Path, answers_file: Path, ids_file: Path | None) -> dict:
    ids_doc = None if ids_file is None else load_json(ids_file)
    return check_documents(load_json(cases_file), load_json(answers_file), ids_doc)


def run(inp: object) -> object:
    """진입 함수. 입력 {"cases_file", "answers_file", "dev20_parent_series_ids_file"?} → 검사 보고(JSON 객체).

    dev20 목록 경로를 주지 않으면 저장소의 eval/dev/dev20/answers/parent_series_ids.json을 읽는다."""
    if not isinstance(inp, dict) or not {"cases_file", "answers_file"} <= set(inp) \
            or set(inp) - {"cases_file", "answers_file", "dev20_parent_series_ids_file"}:
        raise ValueError("입력은 cases_file·answers_file(·dev20_parent_series_ids_file) 키만 가진 객체다")
    ids = _repo_path(inp.get("dev20_parent_series_ids_file") or DEFAULT_DEV20_IDS)
    return check_files(_repo_path(inp["cases_file"]), _repo_path(inp["answers_file"]), ids)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m eval.datagen.holdout40_check", allow_abbrev=False,
                                     description="합성 평가 묶음(holdout40·dev20)의 결정적 검사. 보고에는 건수만 적는다.")
    parser.add_argument("--cases", required=True, help="사례 목록 cases.json 경로")
    parser.add_argument("--answers", required=True, help="정답표 answers.json 경로")
    parser.add_argument("--dev20-ids", default=DEFAULT_DEV20_IDS, help="dev20 부모 원본 계열 ID 목록 경로")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return EXIT_USAGE if exc.code else EXIT_OK
    try:
        report = check_files(_repo_path(args.cases), _repo_path(args.answers), _repo_path(args.dev20_ids))
    except CheckInputError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return EXIT_USAGE
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=1))
    return EXIT_OK if report["ok"] else EXIT_FAILED


if __name__ == "__main__":
    sys.exit(main())
