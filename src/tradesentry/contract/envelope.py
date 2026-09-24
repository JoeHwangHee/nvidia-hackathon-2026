"""단위 K5 공통 봉투.

단위 ID: K5
도메인명: contract_envelope
소유: D
입력: 도구 결과
출력: 키 11개 봉투
허용 import: 표준 라이브러리, tradesentry.contract

정본: 자료 계약 docs/rules/DATA_CONTRACT_V1.md §5(도구 출력 봉투), §2.3.4(`metric` 객체), §4.4(근거 ID).

- 봉투의 키 11개는 늘 모두 있다(§5.2). 값이 없으면 목록 키는 빈 목록, 객체 키(`comparability`, `retryable_error`)는
  null이다. 이 단위가 정한 기본값은 이것뿐이다.
- 꼭 받아야 하는 값: `query_id`, `tool`(도구 5개 중 하나), `scope`(실제로 조회한 범위 객체), `snapshot_id`,
  `source_kind`(`real`/`controlled`), `elapsed_ms`(0 이상 정수). `scope`의 세부 모양은 도구(M)가 정한다(§5.1).
- 근거 ID는 형식(단위 K2)과 스냅샷(봉투의 `snapshot_id`와 같음)을 본다. 행이 실제로 있는지는 자료 접근층이 본다.
- `metrics`의 원소는 `metric` 객체 키 8개를 모두, 그 키만 가진다. 수는 int나 Decimal이다. 봉투 어디에도 float를
  두지 않는다(계약 §11.1 "수치 입력은 정수 또는 Decimal로 보존").
"""
from decimal import Decimal

from tradesentry.contract import types
from tradesentry.contract.evidence_id import EvidenceIdError, parse_evidence_id

REQUIRED_KEYS = ("query_id", "tool", "scope", "snapshot_id", "source_kind", "elapsed_ms")
DEFAULTS = {"evidence_ids": [], "metrics": [], "comparability": None, "missingness": [], "retryable_error": None}


def _floats(value: object, where: str) -> list[str]:
    if isinstance(value, float):
        return [f"{where}: float는 쓰지 않는다(int나 Decimal)"]
    if isinstance(value, (list, tuple)):
        return [p for i, v in enumerate(value) for p in _floats(v, f"{where}[{i}]")]
    if isinstance(value, dict):
        return [p for k, v in value.items() for p in _floats(v, f"{where}.{k}")]
    return []


def _evidence_problems(ids: object, snapshot_id: object, where: str) -> list[str]:
    if not isinstance(ids, list):
        return [f"{where}: 근거 ID 목록이어야 한다"]
    problems = []
    for i, text in enumerate(ids):
        try:
            ref = parse_evidence_id(text)
        except EvidenceIdError as exc:
            problems.append(f"{where}[{i}]: 근거 ID 형식이 아니다(풀림 규칙 {exc.rule})")
            continue
        if ref.snapshot_id != snapshot_id:
            problems.append(f"{where}[{i}]: 봉투의 snapshot_id와 다른 스냅샷의 근거 ID다(풀림 규칙 2)")
    return problems


def _is_number(value: object) -> bool:
    return (isinstance(value, int) and not isinstance(value, bool)) or (isinstance(value, Decimal) and value.is_finite())


def metric_problems(metric: object, snapshot_id: object, where: str = "metric") -> list[str]:
    """`metric` 객체(§2.3.4) 하나의 문제 목록. 비었으면 맞다."""
    if not isinstance(metric, dict):
        return [f"{where}: 객체여야 한다"]
    problems = []
    missing = [k for k in types.METRIC_KEYS if k not in metric]
    extra = [k for k in metric if k not in types.METRIC_KEYS]
    if missing:
        problems.append(f"{where}: 키가 없다({', '.join(missing)})")
    if extra:
        problems.append(f"{where}: 계약에 없는 키다({', '.join(map(str, extra))})")
    if missing:
        return problems
    if not isinstance(metric["metric_id"], str) or not metric["metric_id"]:
        problems.append(f"{where}.metric_id: 빈 문자열이 아닌 문자열이어야 한다")
    if not isinstance(metric["formula_version"], str) or not metric["formula_version"]:
        problems.append(f"{where}.formula_version: 빈 문자열이 아닌 문자열이어야 한다")
    if not isinstance(metric["inputs"], dict):
        problems.append(f"{where}.inputs: 객체여야 한다")
    problems += _evidence_problems(metric["evidence_ids"], snapshot_id, f"{where}.evidence_ids")
    if metric["value"] is not None and not _is_number(metric["value"]):
        problems.append(f"{where}.value: 수(int·Decimal)나 null이어야 한다")
    if not isinstance(metric["unit"], str):
        problems.append(f"{where}.unit: 문자열이어야 한다(§11.2 단위)")
    flags = metric["comparability_flags"]
    if not isinstance(flags, list) or not all(isinstance(f, str) for f in flags):
        problems.append(f"{where}.comparability_flags: 문자열 목록이어야 한다")
    elif metric["value"] is None and not flags:
        problems.append(f"{where}: value가 null이면 comparability_flags에 사유를 적는다(§2.3.4)")
    if metric["tolerance"] is not None and not _is_number(metric["tolerance"]):
        problems.append(f"{where}.tolerance: 수(int·Decimal)나 null이어야 한다")
    return problems


def envelope_problems(envelope: object) -> list[str]:
    """완성된 봉투의 문제 목록. 비었으면 계약(§5)에 맞다."""
    if not isinstance(envelope, dict):
        return ["봉투는 객체여야 한다"]
    problems = []
    missing = [k for k in types.ENVELOPE_KEYS if k not in envelope]
    extra = [k for k in envelope if k not in types.ENVELOPE_KEYS]
    if missing:
        problems.append(f"봉투 키가 없다({', '.join(missing)})")
    if extra:
        problems.append(f"계약에 없는 봉투 키다({', '.join(map(str, extra))})")
    if missing:
        return problems
    e = envelope
    if not isinstance(e["query_id"], str) or not e["query_id"]:
        problems.append("query_id: 빈 문자열이 아닌 문자열이어야 한다")
    if e["tool"] not in types.TOOLS:
        problems.append(f"tool: 도구 5개({', '.join(types.TOOLS)}) 가운데 하나여야 한다")
    if not isinstance(e["scope"], dict):
        problems.append("scope: 실제로 조회한 범위 객체여야 한다")
    if not isinstance(e["snapshot_id"], str) or not e["snapshot_id"] or ":" in e["snapshot_id"]:
        problems.append("snapshot_id: `:` 없는 빈 문자열이 아닌 문자열이어야 한다")
    if e["source_kind"] not in types.SOURCE_KINDS:
        problems.append("source_kind: real 또는 controlled여야 한다")
    problems += _evidence_problems(e["evidence_ids"], e["snapshot_id"], "evidence_ids")
    if not isinstance(e["metrics"], list):
        problems.append("metrics: metric 객체 목록이어야 한다")
    else:
        for i, metric in enumerate(e["metrics"]):
            problems += metric_problems(metric, e["snapshot_id"], f"metrics[{i}]")
    if e["comparability"] is not None and not isinstance(e["comparability"], dict):
        problems.append("comparability: 객체나 null이어야 한다")
    if not isinstance(e["missingness"], list):
        problems.append("missingness: 목록이어야 한다")
    if e["retryable_error"] is not None and not isinstance(e["retryable_error"], dict):
        problems.append("retryable_error: 객체나 null이어야 한다")
    elapsed = e["elapsed_ms"]
    if isinstance(elapsed, bool) or not isinstance(elapsed, int) or elapsed < 0:
        problems.append("elapsed_ms: 0 이상 정수여야 한다")
    problems += _floats(e, "봉투")
    return problems


def make_envelope(**fields: object) -> dict:
    """도구 결과(봉투 키 일부) → 키 11개 봉투(계약 순서). 문제가 있으면 ValueError로 모두 알린다."""
    unknown = [k for k in fields if k not in types.ENVELOPE_KEYS]
    missing = [k for k in REQUIRED_KEYS if k not in fields]
    if unknown or missing:
        parts = []
        if missing:
            parts.append(f"꼭 받아야 하는 키가 없다({', '.join(missing)})")
        if unknown:
            parts.append(f"계약에 없는 봉투 키다({', '.join(unknown)})")
        raise ValueError("; ".join(parts))
    envelope = {}
    for key in types.ENVELOPE_KEYS:
        default = DEFAULTS.get(key)
        envelope[key] = fields[key] if key in fields else (list(default) if isinstance(default, list) else default)
    problems = envelope_problems(envelope)
    if problems:
        raise ValueError("; ".join(problems))
    return envelope


def run(inp: object) -> object:
    """진입 함수. 도구 결과(봉투 키 일부를 담은 객체) → 키 11개 봉투. 맞지 않으면 ValueError다."""
    if not isinstance(inp, dict):
        raise ValueError("입력은 봉투 키를 담은 객체다")
    return make_envelope(**inp)
