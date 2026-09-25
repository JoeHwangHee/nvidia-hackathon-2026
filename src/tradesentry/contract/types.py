"""단위 K1 계약 타입.

단위 ID: K1
도메인명: contract_types
소유: D
입력: 없음(입출력 없음)
출력: 정의 모음(상태값·키·typed dict·`schema_version`)
허용 import: 표준 라이브러리, tradesentry.contract

커널(여러 단위가 import하는 정의 모음)이라 진입 함수가 없다. 정본: docs/plan/UNITS.md §3.2.

- 값은 자료 계약 docs/rules/DATA_CONTRACT_V1.md에서 글자 그대로 옮겼다. 상수마다 위 주석이 출처 절이다. "명세 §4.x
  원문"은 그 계약 안의 원문 블록이다. tests/units/K1/test_types.py가 원문 블록·표와 글자까지 대조한다.
- 값 집합은 계약에 적힌 순서의 튜플이다. 포함 여부는 `in`으로 본다.
- 계약 밖 이름을 새로 짓지 않았다. 스냅샷 SQLite의 열 순서는 기존 수집기(src/tradesentry/ingest.py)의 표 정의를 그대로
  옮겼다(단위 S2가 같은 열로 파생 SQLite를 만든다).
- 채점기(eval/scorer/)는 이 모듈을 import하지 않는다(독립 구현). 필요한 상수는 채점기 안에 따로 적는다.
"""
import re
from datetime import timedelta, timezone
from decimal import Decimal
from typing import Any, TypedDict

# §1.2 계약 버전(명세 §4.7 원문 "schema_version=1"). 2026-09-25(금) 사용자 결정으로 2로 올렸다(값 집합 변경, 자료 계약
# §13.2. 결정 기록 docs/tracking/decisions/20260925-1215-data-decision-schema-v2.md).
SCHEMA_VERSION = 2

# §3 명세 §4.1 원문: 판정 상태와 신호.
REVIEW_STATUSES = ("MAINTAIN", "MONITOR", "HOLD")  # 사례별(`review_status`, `review_status_final`)
SIGNAL_STATUSES = ("MAINTAIN", "MONITOR", "HOLD", "NOT_TRIGGERED")  # 신호별(`signal_status`의 값)
SIGNALS = ("unit_value", "share")  # 신호 코드
SIGNAL_TRIGGERS = ("TRIGGERED", "NOT_TRIGGERED")  # 신호 발동 여부(`signal_trigger`)
STATUS_LABELS_KO = {"MAINTAIN": "검토 유지", "MONITOR": "모니터링", "HOLD": "자료 보류", "NOT_TRIGGERED": "미발동"}
PRE_INVESTIGATION = "PRE_INVESTIGATION"  # 사례의 처음 표시 상태 코드. 판정 상태가 아니다
PRE_INVESTIGATION_LABEL_KO = "조사 전 경보"
# §3.1 사례 집계 우선순위 `MAINTAIN > HOLD > MONITOR`(앞이 높다).
CASE_STATUS_PRIORITY = ("MAINTAIN", "HOLD", "MONITOR")

# §3.2 oracle_ABC 대응(oracle 파일은 고치지 않고 이 표로 코드와 잇는다).
ORACLE_REVIEW_STATUS = {"검토 유지": "MAINTAIN", "모니터링": "MONITOR", "자료 보류": "HOLD"}

# §3 명세 §4.2 원문: 실행 상태.
EXECUTION_STATUSES = ("COMPLETED", "FAILED", "TIMEOUT", "INVALID", "BUDGET_EXCEEDED")

# §3 명세 §4.3 원문: 관측 상태. 수입 0이 명시된 달은 `OBSERVED`(값 0)다.
OBSERVATION_STATUSES = ("OBSERVED", "NOT_COLLECTED", "REQUEST_FAILED", "UNRESOLVED_ZERO", "CONFIRMED_NO_TRADE")
OBSERVED = "OBSERVED"
NOT_COLLECTED = "NOT_COLLECTED"
REQUEST_FAILED = "REQUEST_FAILED"
UNRESOLVED_ZERO = "UNRESOLVED_ZERO"
CONFIRMED_NO_TRADE = "CONFIRMED_NO_TRADE"

# §4 명세 §4.4 원문: 모드와 출처 종류.
MODES = ("checklist", "agent", "full", "freeform")
SOURCE_KINDS = ("real", "controlled")

# §4 명세 §4.5 원문: 이름.
DATASETS = ("controlled_fixture_v0", "dev20", "holdout40", "real_dev", "real_sealed")
SEALED_DATASETS = ("holdout40", "real_sealed")  # §12.2 `dataset` 값
REAL_SNAPSHOT_ID = "kcs_202201_202412_v2"
FIXTURE_SNAPSHOT_ID = "controlled_fixture_v0"
POLICY_V1 = "policy_v1"
GROUPING_VERSIONS = ("g0", "g1")
RULEBOOK_VERSION = "RB-1"
APPROVAL_STATUSES = ("VALID", "REVIEW_REQUIRED")
EVIDENCE_ID_FORMAT = "ev:<snapshot_id>:<table>:<rowid>"
EVIDENCE_ID_PREFIX = "ev"

# §5 명세 §4.6 원문: 도구 출력 봉투 키 11개(순서 그대로). §5.1: 도구 5개.
ENVELOPE_KEYS = ("query_id", "tool", "scope", "snapshot_id", "source_kind", "evidence_ids", "metrics", "comparability",
                 "missingness", "retryable_error", "elapsed_ms")
TOOLS = ("check_comparability", "get_history", "compare_partners", "decompose_hs", "verify_evidence")

# §6 명세 §4.8 원문: typed claim.
CLAIM_FIELDS = ("claim_id", "claim_type", "hs6", "partner", "period", "baseline_period", "metric", "value", "unit",
                "direction", "evidence_ids", "text")
CLAIM_TYPES = ("value", "change", "share", "share_change", "decomposition", "comparison", "data_status")
DIRECTIONS = ("UP", "DOWN", "FLAT", "NA")

# §7 명세 §4.9 원문: 주장 채점 결과.
CLAIM_OUTCOMES = ("CORRECT", "WRONG_VALUE", "WRONG_DIRECTION", "WRONG_UNIT", "WRONG_REFERENT", "UNSUPPORTED",
                  "UNBACKED_PROSE")

# §8 명세 §4.10 원문: 실행 결과 기록 키 24개. 세 키는 샌드박스 밖 정답 대조 채점이 채운다(§8.1).
RUN_RECORD_KEYS = ("run_id", "case_id", "dataset", "mode", "policy_version", "rulebook_version", "snapshot_id",
                   "grouping_version", "code_version", "review_status_final", "signal_status", "unresolved_evidence",
                   "execution_status", "required_evidence_ok", "numeric_ok", "provenance_ok", "tool_attempts",
                   "model_requests", "tokens_in", "tokens_out", "wall_ms", "critic_used", "revision_used", "errors")
RUN_RECORD_SCORER_KEYS = ("required_evidence_ok", "numeric_ok", "provenance_ok")

# §9 명세 §4.10-1 원문: 보고서 객체 키 17개. `report_hash`가 덮는 네 키는 §9.1.
REPORT_KEYS = ("report_id", "run_id", "case_id", "mode", "claims", "narrative", "hypotheses", "review_status",
               "signal_status", "unresolved_evidence", "evidence_ids", "validator_findings", "report_hash", "created_at",
               "policy_version", "snapshot_id", "grouping_version")
REPORT_HASH_KEYS = ("claims", "narrative", "hypotheses", "evidence_ids")

# §9 명세 §4.10-2 원문: 주장 채점 기록 키 13개와 `source` 값.
CLAIM_RECORD_KEYS = ("run_id", "report_id", "claim_id", "source", "outcome", "expected_value", "reported_value",
                     "unit_expected", "unit_reported", "tolerance", "referent_resolved", "evidence_ok", "note")
CLAIM_RECORD_SOURCES = ("claim", "prose")

# §9.3 승인 기록(모의) 필드.
APPROVAL_RECORD_KEYS = ("reviewer_label", "timestamp", "report_hash", "evidence_digest", "snapshot_id", "policy_version",
                        "code_version")

# §2.1·§2.3 객체의 v1 키. `snapshot`은 v1 키 14개에 계약 버전 표시 `schema_version`(§1.2)을 더해 담는다.
SNAPSHOT_KEYS = ("snapshot_id", "source_kind", "collected_at", "source_url", "collection_plan", "raw_sha256",
                 "normalized_sha256", "period", "hs_version", "importer", "valuation_basis", "units", "precision_rule",
                 "coverage_status")
OBSERVATION_KEYS = ("snapshot_id", "month", "partner_code", "partner_namespace", "hs_code", "hs_level", "hs_version",
                    "amount_usd", "net_weight_kg", "observation_status", "raw_file_id", "raw_row_locator")
OBSERVATION_EXTRA_COLUMNS = ("request_id", "flow", "item_name")  # §2.3.2 "기존 열"(필수 필드는 아니지만 행 규칙이 쓴다)
COLLECTION_RECEIPT_KEYS = ("request_id", "endpoint", "params_json", "status", "response_hash", "row_count", "timestamp")
COLLECTION_RECEIPT_EXTRA_COLUMNS = ("http_status", "attempts", "result_code", "result_msg", "error", "elapsed_ms",
                                    "raw_file_id")
RECEIPT_STATUSES = ("OK", "FAILED")
METRIC_KEYS = ("metric_id", "formula_version", "inputs", "evidence_ids", "value", "unit", "comparability_flags",
               "tolerance")
CASE_KEYS = ("case_id", "hs6", "partner", "month", "baseline_month", "signals", "snapshot_id", "policy_version")
PEER_GROUP_KEYS = ("entity_type", "entity_id", "entity_namespace", "baci_country_code", "scope_type", "scope_id",
                   "peer_rank", "peer_id", "similarity", "community_id", "method", "grouping_version", "params_hash",
                   "source_version", "source_year", "input_sha256", "generated_at")
PEER_ENTITY_TYPE = "exporter_country"
PEER_SCOPE_TYPES = ("hs2", "hs4", "hs6")  # §2.3.6: `hs2:85`, `hs4:8504`(원문 예시)와 `g0`의 `hs6`

# 스냅샷 SQLite의 열 순서(기존 수집기 표 정의와 같다. §2.3.2 행 규칙 1의 기본 키 포함).
OBSERVATION_COLUMNS = ("snapshot_id", "request_id", "month", "partner_code", "partner_namespace", "hs_code", "hs_level",
                       "hs_version", "flow", "amount_usd", "net_weight_kg", "observation_status", "raw_file_id",
                       "raw_row_locator", "item_name")
OBSERVATION_PRIMARY_KEY = ("request_id", "month", "partner_code", "hs_code", "flow")
COLLECTION_RECEIPT_COLUMNS = ("request_id", "endpoint", "params_json", "status", "http_status", "attempts",
                              "response_hash", "row_count", "result_code", "result_msg", "error", "elapsed_ms",
                              "raw_file_id", "timestamp")
PEER_GROUP_COLUMNS = PEER_GROUP_KEYS

# §2.3.2 관측 행의 값과 행 규칙에 쓰는 고정 문자열.
PARTNER_NAMESPACE = "KCS_cntyCd"
ALL_PARTNER = "ALL"  # 전체국가 분모
FLOWS = ("import", "export")
METRIC_FLOW = "import"  # 행 규칙 2: 지표는 수입 흐름만 쓴다
RAW_MONTH_PREFIX = "RAW:"  # 월 형식이 아닌 행(총계 행은 `RAW:총계`)
TOTAL_ROW_MONTH = "RAW:총계"  # §2.3.2 `month` 형식: 월 행은 `YYYYMM`, 총계 행은 `RAW:총계`(이 둘뿐이다)
HS_LEVELS = (2, 4, 6, 10)
MONTH_RE = re.compile(r"(19|20)[0-9]{2}(0[1-9]|1[0-2])")  # `YYYYMM`(§11.4). fullmatch로 쓴다
HS6_RE = re.compile(r"[0-9]{6}")
HS10_RE = re.compile(r"[0-9]{10}")

# §11.2 지표 기호와 단위. `w`는 `w@<HS10 코드>`로만 쓴다. `observation_status`는 자료 상태 주장의 기호다(§6.1).
METRIC_SYMBOLS = ("V", "Q", "U", "r_U", "s", "d_s", "within_effect", "mix_effect", "residual")
METRIC_UNITS = {"V": "USD", "Q": "kg", "U": "USD/kg", "r_U": "%", "s": "%", "d_s": "pp", "within_effect": "USD/kg",
                "mix_effect": "USD/kg", "residual": "USD/kg", "w": "%"}
# §6.2 HS10 하위품목 주장의 `@` 기호. 정의한 것은 이 넷뿐이다.
HS10_METRIC_BASES = ("U", "r_U", "w", "observation_status")
DATA_STATUS_METRIC = "observation_status"
# §11.3 표시 자릿수(소수 자리 수. 0은 정수). `U@`·`r_U@`는 `@` 앞 기호를 따른다.
DISPLAY_DECIMALS = {"V": 0, "Q": 0, "U": 2, "r_U": 1, "s": 1, "d_s": 1, "within_effect": 2, "mix_effect": 2,
                    "residual": 2, "w": 1}
# §9.4 신호 계열 대응(`@`로 끝나는 항목은 `<기호>@<HS10 코드>`).
SIGNAL_FAMILY_METRICS = {"unit_value": ("U", "r_U", "within_effect", "mix_effect", "residual", "U@", "r_U@", "w@"),
                         "share": ("s", "d_s")}

# §12.2 봉인 해시 목록의 항목 키.
SEALED_MANIFEST_FILE_KEYS = ("dataset", "file_name", "sha256", "created_at", "created_by")

# §10.3 N5 실행명(`run_id`) 형식 `{실행 이름}-{yymmddhhmmss}`(S0 결정 기록의 검사식). fullmatch로 쓴다.
RUN_ID_RE = re.compile(r"[a-z][a-z0-9_]*-[0-9]{12}")
# §11.4 시각은 KST ISO 8601(초 단위)로 적는다.
KST = timezone(timedelta(hours=9), "KST")


def parse_metric(metric: str) -> tuple[str, str | None]:
    """지표 기호를 (기본 기호, HS10 코드 또는 None)으로 나눈다. 계약에 없는 기호면 ValueError다.

    예: "r_U" → ("r_U", None), "w@8504501000" → ("w", "8504501000"), "observation_status" → ("observation_status", None).
    `w`는 `@` 없이 쓰지 않는다(§6.2·§11.2).
    """
    if not isinstance(metric, str):
        raise ValueError("지표 기호는 문자열이어야 한다")
    base, sep, code = metric.partition("@")
    if sep:
        if base not in HS10_METRIC_BASES or not HS10_RE.fullmatch(code):
            raise ValueError(f"정의하지 않은 HS10 하위 지표 기호: {metric!r}")
        return base, code
    if metric in METRIC_SYMBOLS or metric == DATA_STATUS_METRIC:
        return metric, None
    raise ValueError(f"계약에 없는 지표 기호: {metric!r}")


def metric_unit(metric: str) -> str | None:
    """지표 기호의 단위(§11.2). 자료 상태(`observation_status`, `observation_status@…`)는 단위가 없어 None이다."""
    base, _ = parse_metric(metric)
    return METRIC_UNITS.get(base)


def metric_display_decimals(metric: str) -> int | None:
    """지표 기호의 표시 자릿수(§11.3). 자료 상태는 None이다."""
    base, _ = parse_metric(metric)
    return DISPLAY_DECIMALS.get(base)


def signal_family(metric: str) -> tuple[str, ...]:
    """지표 기호가 드는 신호 계열(§9.4). `V`·`Q`와 자료 상태는 빈 튜플이다(자료 상태 주장의 계열은 §9.4 본문 규칙)."""
    base, code = parse_metric(metric)
    key = f"{base}@" if code is not None else base
    return tuple(name for name, members in SIGNAL_FAMILY_METRICS.items() if key in members)


# 주요 객체의 모양(typed dict). 값 형식은 계약 표의 "형식" 열을 따른다. 수는 int 또는 Decimal이다(float를 쓰지 않는다).
Number = int | Decimal


class Observation(TypedDict):
    """§2.3.2 `observation` 한 행(스냅샷 SQLite 열 전부)."""

    snapshot_id: str
    request_id: str
    month: str
    partner_code: str
    partner_namespace: str
    hs_code: str
    hs_level: int
    hs_version: str
    flow: str
    amount_usd: int | None
    net_weight_kg: int | None
    observation_status: str
    raw_file_id: str | None
    raw_row_locator: str | None
    item_name: str | None


class CollectionReceipt(TypedDict):
    """§2.3.3 `collection_receipt` 한 행(스냅샷 SQLite 열 전부)."""

    request_id: str
    endpoint: str
    params_json: str
    status: str
    http_status: int | None
    attempts: int | None
    response_hash: str | None
    row_count: int | None
    result_code: str | None
    result_msg: str | None
    error: str | None
    elapsed_ms: int | None
    raw_file_id: str | None
    timestamp: str


class Metric(TypedDict):
    """§2.3.4 `metric` 지표 값 1개."""

    metric_id: str
    formula_version: str
    inputs: dict[str, Any]
    evidence_ids: list[str]
    value: Number | None
    unit: str
    comparability_flags: list[str]
    tolerance: Number | None


class Case(TypedDict):
    """§2.3.5 `case` 경보 사례 1건. `signals`는 신호 코드 → `TRIGGERED`/`NOT_TRIGGERED`."""

    case_id: str
    hs6: str
    partner: str
    month: str
    baseline_month: str
    signals: dict[str, str]
    snapshot_id: str
    policy_version: str


class PeerGroupRow(TypedDict):
    """§2.3.6 `peer_group` 한 행. `similarity`는 원문 표기를 지킨 Decimal이다(`g0`는 None)."""

    entity_type: str
    entity_id: str
    entity_namespace: str
    baci_country_code: str | None
    scope_type: str
    scope_id: str
    peer_rank: int
    peer_id: str
    similarity: Decimal | None
    community_id: str | None
    method: str
    grouping_version: str
    params_hash: str
    source_version: str
    source_year: int
    input_sha256: str
    generated_at: str


class Envelope(TypedDict):
    """§5 도구 출력 봉투. 키 11개가 늘 모두 있다."""

    query_id: str
    tool: str
    scope: dict[str, Any]
    snapshot_id: str
    source_kind: str
    evidence_ids: list[str]
    metrics: list[Metric]
    comparability: dict[str, Any] | None
    missingness: list[dict[str, Any]]
    retryable_error: dict[str, Any] | None
    elapsed_ms: int


class TypedClaim(TypedDict):
    """§6 typed claim 1건."""

    claim_id: str
    claim_type: str
    hs6: str
    partner: str
    period: str
    baseline_period: str | None
    metric: str
    value: Number | str | None
    unit: str | None
    direction: str
    evidence_ids: list[str]
    text: str


class RunRecord(TypedDict):
    """§8 실행 결과 기록 1건(키 24개)."""

    run_id: str
    case_id: str
    dataset: str
    mode: str
    policy_version: str
    rulebook_version: str
    snapshot_id: str
    grouping_version: str
    code_version: str
    review_status_final: str | None
    signal_status: dict[str, str]
    unresolved_evidence: bool
    execution_status: str
    required_evidence_ok: bool
    numeric_ok: bool
    provenance_ok: bool
    tool_attempts: int
    model_requests: int
    tokens_in: int
    tokens_out: int
    wall_ms: int
    critic_used: bool
    revision_used: bool
    errors: list[Any]


class Report(TypedDict):
    """§9.1 보고서 객체(키 17개)."""

    report_id: str
    run_id: str
    case_id: str
    mode: str
    claims: list[TypedClaim]
    narrative: str
    hypotheses: list[str]
    review_status: str
    signal_status: dict[str, str]
    unresolved_evidence: bool
    evidence_ids: list[str]
    validator_findings: list[Any]
    report_hash: str
    created_at: str
    policy_version: str
    snapshot_id: str
    grouping_version: str


class ClaimRecord(TypedDict):
    """§9.2 주장 채점 기록 1건(키 13개)."""

    run_id: str
    report_id: str
    claim_id: str
    source: str
    outcome: str
    expected_value: Number | str | None
    reported_value: Number | str | None
    unit_expected: str | None
    unit_reported: str | None
    tolerance: Number | None
    referent_resolved: bool
    evidence_ok: bool
    note: str


class ApprovalRecord(TypedDict):
    """§9.3 승인 기록(모의)."""

    reviewer_label: str
    timestamp: str
    report_hash: str
    evidence_digest: str
    snapshot_id: str
    policy_version: str
    code_version: str
