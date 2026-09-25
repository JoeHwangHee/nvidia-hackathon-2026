"""단위 S3 스냅샷 검증.

단위 ID: S3
도메인명: snapshot_verify
소유: D
입력: SQLite·raw
출력: 검증 보고·`normalized_sha256`·계약 검사
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.ingest, tradesentry.snapshot

단위 S2가 만든 파생 SQLite를 읽기 전용으로 열어 계약·행 규칙 검사, raw 대조(raw에서 다시 만든 행과 한 칸씩 비교),
`normalized_sha256` 재계산과 기록값 대조를 하고 보고(dict)를 돌려준다. 파일을 고치지 않는다. `tradesentry snapshot-verify`의
자료 쪽 구현이고, 스냅샷 인수물의 자료 계약 검사(인수 조건 2)로도 쓴다. 정본: 자료 계약 §2.3·§3.4·§4.4 규칙 4.

입력(`run`): {"snapshot_id", "build_file"?, "source_dir"?, "check_raw"?, "peer_group_files"?}
- build_file이 없으면 정본 빌드 `data/snapshots/{snapshot_id}/snapshot_build.sqlite`를 보고, 그 옆 기록
  `snapshot_build.json`의 `normalized_sha256`과 반드시 대조한다(기록이 없으면 실패).
- 승인 전 개발 빌드는 build_file(저장소 루트 기준 상대경로 또는 절대경로, 예:
  `outputs/snapshot_build-{시각}/snapshot_build-{시각}.sqlite`)로 준다. 옆에 같은 이름의 기록 `.json`이 있으면 대조하고,
  없으면 대조를 건너뛰었다고 적는다(실패가 아니다).
- raw 대조의 원천은 source_dir(없으면 `data/snapshots/{snapshot_id}/`: manifest.json, raw/, 수집기 snapshot.sqlite)다.
  check_raw가 참(기본)인데 원천이 없으면 그 검사는 실패다. 거짓이면 raw 대조만 건너뛰고 보고에 적는다.
- raw 없이 도는 계약 검사는 check_raw와 관계없이 늘 돈다: 표·열, 메타, 관측 값, rowid 연속, `ALL` 중복 값, 분석 범위와
  HS10 하위 자리, 관측 행 규칙(HS 코드·월·수신 기록과 상태·raw 위치 칸·`NOT_COLLECTED` 집합·승격 집합), 비교국 표 행 규칙
  (단위 S2와 같은 `peer_group_problems`), 비교국 표 원본 대조.
- 비교국 표 원본 대조: peer_group_files(경로 목록)를 주면 그 파일로, 없으면 빌드 기록의 `peer_group_files` 이름을
  `data/reference/`에서 찾아 sha256을 빌드 기록과 대조하고 행을 다시 읽어 저장된 행과 비교한다. 빌드 기록에 적힌 파일을
  찾지 못하거나 기록에 파일이 없는데 행이 있으면 실패다. 빌드 기록이 없는 개발 빌드만 건너뛴다.

출력: {"snapshot_id", "schema_version", "build_file"(파일 이름만), "ok", "normalized_sha256",
"recorded_normalized_sha256", "checks": [{"name", "ok", "detail"}…], "counts"}. `ok`는 건너뛰지 않은 검사가 모두 통과했는지다.
로컬 절대경로는 보고에 적지 않는다(N13).
"""
import hashlib
import json
import re
import sqlite3
from pathlib import Path

from tradesentry import ingest
from tradesentry.contract import types
from tradesentry.contract.policy_load import PROMOTION_RULES
from tradesentry.snapshot import build

META_COLUMNS = ("key", "value")
TABLE_COLUMNS = {"collection_receipt": types.COLLECTION_RECEIPT_COLUMNS, "observation": types.OBSERVATION_COLUMNS,
                 "peer_group": types.PEER_GROUP_COLUMNS, "snapshot_meta": META_COLUMNS}
EXAMPLES = 5  # 문제 예시는 몇 건만 적는다
RAW_LOCATOR_RE = re.compile(r"item\[[0-9]+\]")  # raw 파일 안 행 위치(수집기 store_result)
HS_CODE_RE = re.compile(r"[0-9]+")
REFERENCE_DIR = ("data", "reference")  # 비교국 표의 정본 자리(계획 경로 표 "그룹핑 결과")


class _Report:
    def __init__(self) -> None:
        self.checks: list[dict] = []

    def add(self, name: str, ok: bool | None, detail: object = None) -> bool:
        """ok가 None이면 건너뛴 검사다."""
        self.checks.append({"name": name, "ok": ok, "detail": detail})
        return bool(ok)


def _error_detail(exc: BaseException) -> dict:
    """예외를 보고에 적는다. 빌드 오류 문장은 경로를 담지 않지만 OS·SQLite 오류 원문은 로컬 경로를 담을 수 있어 이름만 적는다."""
    return {"error": str(exc) if isinstance(exc, build.BuildError) else type(exc).__name__}


def _problems_detail(problems: list[str]) -> dict:
    return {"problems": len(problems), "examples": problems[:EXAMPLES]}


def _check_tables(con: sqlite3.Connection, report: _Report) -> bool:
    problems = []
    for table, columns in TABLE_COLUMNS.items():
        found = tuple(row[1] for row in con.execute(f'PRAGMA table_info("{table}")'))
        if found != tuple(columns):
            problems.append(f"{table}: 열이 계약 순서와 다르다" if found else f"{table}: 표가 없다")
    return report.add("tables_and_columns", not problems, _problems_detail(problems))


def _check_meta(meta: dict, snapshot_id: str, report: _Report) -> bool:
    problems = []
    if meta.get("schema_version") != types.SCHEMA_VERSION:
        problems.append(f"schema_version이 {types.SCHEMA_VERSION}가 아니다")
    if meta.get("snapshot_id") != snapshot_id:
        problems.append("snapshot_id가 부른 이름과 다르다")
    expected = {"schema_version", *types.SNAPSHOT_KEYS} - {"normalized_sha256"}
    if set(meta) != expected:
        problems.append(f"메타 키가 계약 snapshot 키와 다르다(없음 {sorted(expected - set(meta))}, "
                        f"남음 {sorted(set(meta) - expected)})")
    if meta.get("source_kind") not in types.SOURCE_KINDS:
        problems.append("source_kind가 real·controlled가 아니다")
    period = meta.get("period") or {}
    if not all(types.MONTH_RE.fullmatch(str(period.get(k, ""))) for k in ("start", "end")):
        problems.append("period가 {start, end} YYYYMM이 아니다")
    if not isinstance(meta.get("hs_version"), str) or not meta.get("hs_version"):
        problems.append("hs_version이 문자열이 아니다")
    return report.add("snapshot_meta", not problems, _problems_detail(problems))


def _check_observation_values(con: sqlite3.Connection, meta: dict, report: _Report) -> bool:
    problems = []
    columns = ", ".join(types.OBSERVATION_COLUMNS)
    query = f"SELECT rowid, {columns}, typeof(amount_usd), typeof(net_weight_kg) FROM observation ORDER BY rowid"
    at = {name: i + 1 for i, name in enumerate(types.OBSERVATION_COLUMNS)}
    for row in con.execute(query):
        rowid, status, month = row[0], row[at["observation_status"]], row[at["month"]]
        kinds = (row[-2], row[-1])
        where = f"observation rowid {rowid}"
        if row[at["snapshot_id"]] != meta.get("snapshot_id"):
            problems.append(f"{where}: snapshot_id가 메타와 다르다")
        if status not in types.OBSERVATION_STATUSES:
            problems.append(f"{where}: 관측 상태가 다섯 값이 아니다")
        if row[at["flow"]] not in types.FLOWS:
            problems.append(f"{where}: flow가 import·export가 아니다")
        if row[at["partner_namespace"]] != types.PARTNER_NAMESPACE:
            problems.append(f"{where}: partner_namespace가 {types.PARTNER_NAMESPACE}가 아니다")
        if row[at["hs_level"]] != len(row[at["hs_code"]] or ""):
            problems.append(f"{where}: hs_level이 hs_code 자릿수와 다르다")
        if row[at["hs_version"]] != meta.get("hs_version"):
            problems.append(f"{where}: hs_version이 메타와 다르다")
        if not (types.MONTH_RE.fullmatch(month or "") or month == types.TOTAL_ROW_MONTH):
            problems.append(f"{where}: month가 YYYYMM이나 총계 행 {types.TOTAL_ROW_MONTH}가 아니다(§2.3.2)")
        if status == types.OBSERVED and kinds != ("integer", "integer"):
            problems.append(f"{where}: OBSERVED 행의 금액·중량이 정수가 아니다")
        if status != types.OBSERVED and kinds != ("null", "null"):
            problems.append(f"{where}: {status} 행의 금액·중량이 null이 아니다")
    rowids = [r[0] for r in con.execute("SELECT rowid FROM observation ORDER BY rowid")]
    contiguous = rowids == list(range(1, len(rowids) + 1))
    report.add("observation_values", not problems, _problems_detail(problems))
    report.add("observation_rowids_contiguous", contiguous, {"rows": len(rowids)})
    return not problems and contiguous


def _check_all_duplicates(con: sqlite3.Connection, report: _Report) -> bool:
    groups = con.execute(
        "SELECT hs_code, month, flow, COUNT(*), COUNT(DISTINCT amount_usd), COUNT(DISTINCT net_weight_kg) "
        "FROM observation WHERE partner_code = ? AND hs_level = 10 AND observation_status = ? "
        "AND month NOT LIKE 'RAW:%' GROUP BY hs_code, month, flow HAVING COUNT(*) > 1",
        (types.ALL_PARTNER, types.OBSERVED)).fetchall()
    conflicts = [f"{hs}·{month}·{flow}" for hs, month, flow, _, amounts, weights in groups if amounts > 1 or weights > 1]
    return report.add("all_duplicates_consistent", not conflicts,
                      {"duplicated_keys": len(groups), **_problems_detail(conflicts)})


def _receipt_map(con: sqlite3.Connection) -> dict:
    """수신 기록 request_id → {"endpoint", "params", "status", "raw_file_id"}."""
    out = {}
    for rid, endpoint, params_json, status, raw_file_id in con.execute(
            "SELECT request_id, endpoint, params_json, status, raw_file_id FROM collection_receipt"):
        try:
            params = json.loads(params_json)
        except (TypeError, ValueError):
            params = None
        out[rid] = {"endpoint": endpoint, "params": params if isinstance(params, dict) else {}, "status": status,
                    "raw_file_id": raw_file_id}
    return out


def _check_coverage(con: sqlite3.Connection, meta: dict, receipts: dict, report: _Report) -> bool:
    """분석 범위의 키마다 값 행(부모 HS6 행·ALL HS10 행)이나 상태 행이 있고, 상대국 키마다 HS10 하위 자리(HS6 조회의
    HS10 행이나 HS6 자릿수 상태 행)가 있다(DAL `children()`이 멈추지 않게)."""
    plan = meta.get("collection_plan") or {}
    period = meta.get("period") or {}
    months = ingest.months_between(period["start"], period["end"])
    rows = con.execute("SELECT request_id, partner_code, hs_code, hs_level, month, observation_status FROM observation "
                       "WHERE flow = 'import' AND month NOT LIKE 'RAW:%'").fetchall()
    value_keys, status_keys, child_keys = set(), set(), set()
    for rid, partner, hs, level, month, status in rows:
        if status == types.OBSERVED:
            if level == 6 and partner != types.ALL_PARTNER:
                value_keys.add((partner, hs, month))
            elif level == 10 and partner == types.ALL_PARTNER:
                value_keys.add((partner, hs[:6], month))
            elif level == 10:
                request = receipts.get(rid) or {}
                if request.get("endpoint") == "nitemtrade" and request["params"].get("hsSgn") == hs[:6]:
                    child_keys.add((partner, hs[:6], month))
        else:
            status_keys.add((partner, hs, month))
    missing, missing_children = [], []
    for hs6 in plan.get("hs6", []):
        for partner in list(plan.get("partners", [])) + [types.ALL_PARTNER]:
            for month in months:
                key = (partner, hs6, month)
                if key not in value_keys and key not in status_keys and (partner, hs6[:4], month) not in status_keys:
                    missing.append(f"{partner}·{hs6}·{month}")
                if partner != types.ALL_PARTNER and key not in child_keys and key not in status_keys:
                    missing_children.append(f"{partner}·{hs6}·{month}")
    keys = len(plan.get("hs6", [])) * (len(plan.get("partners", [])) + 1) * len(months)
    ok = report.add("coverage", not missing, {"keys": keys, **_problems_detail(missing)})
    child_total = len(plan.get("hs6", [])) * len(plan.get("partners", [])) * len(months)
    return report.add("coverage_hs10_children", not missing_children,
                      {"keys": child_total, **_problems_detail(missing_children)}) and ok


def _expected_status(row_status: str) -> str | None:
    """관측 상태 → 그 행을 만든 요청의 수신 기록 상태(`None`이면 수신 기록이 없어야 한다)."""
    return {types.OBSERVED: "OK", types.UNRESOLVED_ZERO: "OK", types.CONFIRMED_NO_TRADE: "OK",
            types.REQUEST_FAILED: "FAILED", types.NOT_COLLECTED: None}.get(row_status, "?")


def _check_observation_rules(con: sqlite3.Connection, meta: dict, snapshot_id: str, receipts: dict,
                             record: dict | None, report: _Report) -> bool:
    """raw 없이 볼 수 있는 관측 행 규칙(`check_raw`와 관계없이 늘 돈다, 자료 계약 §2.3.2·§3.4).

    HS 코드는 숫자이고 자릿수는 2·4·6·10, 월은 수집 기간 안이거나 총계 행 `RAW:총계`(`OBSERVED`이고 HS 코드가 요청 코드인
    행만. 그 밖의 `RAW:` 글자는 자료 계약 §2.3.2 형식이 아니라 거부), 행의 요청과 수신
    기록·상태가 맞는다(`OBSERVED`·`UNRESOLVED_ZERO`·`CONFIRMED_NO_TRADE`는 OK, `REQUEST_FAILED`는 FAILED, `NOT_COLLECTED`는
    수신 기록 없음), 행의 상대국·코드·월이 그 요청의 조회 조건 안, raw 위치 칸의 모양, `NOT_COLLECTED` 행 집합이 수집 계획과
    비교국 표에서 다시 계산한 집합과 같다, `CONFIRMED_NO_TRADE`는 수입·HS6 자릿수 행에만 있고 승격 규칙을 다시 적용한
    집합과 같다, 수신 기록은 모두 수집 계획의 요청이다.
    """
    plan = meta.get("collection_plan") or {}
    period = meta.get("period") or {}
    problems: list[str] = []
    try:
        planned = {r["request_id"]: r for r in ingest.build_manifest(plan)}
        months = set(ingest.months_between(period["start"], period["end"]))
    except (KeyError, TypeError, ValueError) as exc:
        return report.add("observation_rules", False, {"error": f"수집 설정으로 계획을 다시 만들지 못했다({type(exc).__name__})"})
    for rid in sorted(set(receipts) - set(planned)):
        problems.append(f"수신 기록 {rid}: 수집 계획에 없는 요청이다")
    columns = ", ".join(types.OBSERVATION_COLUMNS)
    rows = [list(row) for row in con.execute(f"SELECT rowid, {columns} FROM observation ORDER BY rowid")]
    at = {name: i + 1 for i, name in enumerate(types.OBSERVATION_COLUMNS)}
    for row in rows:
        rowid, rid, status = row[0], row[at["request_id"]], row[at["observation_status"]]
        hs, level, month = row[at["hs_code"]] or "", row[at["hs_level"]], row[at["month"]] or ""
        partner, locator, raw_file = row[at["partner_code"]], row[at["raw_row_locator"]], row[at["raw_file_id"]]
        where = f"observation rowid {rowid}"
        if not HS_CODE_RE.fullmatch(hs) or level not in types.HS_LEVELS:
            problems.append(f"{where}: hs_code가 숫자가 아니거나 자릿수가 2·4·6·10이 아니다")
        if types.MONTH_RE.fullmatch(month):
            if month not in months:
                problems.append(f"{where}: month가 수집 기간 밖이다")
        elif month == types.TOTAL_ROW_MONTH:
            if status != types.OBSERVED:
                problems.append(f"{where}: 총계 행 {types.TOTAL_ROW_MONTH}는 OBSERVED(응답의 총계 행)만 있다")
        else:
            problems.append(f"{where}: month가 YYYYMM이나 총계 행 {types.TOTAL_ROW_MONTH}가 아니다(§2.3.2)")
        receipt = receipts.get(rid)
        expected = _expected_status(status)
        if expected is None and receipt is not None:
            problems.append(f"{where}: NOT_COLLECTED인데 요청의 수신 기록이 있다")
        elif expected not in (None, "?") and (receipt is None or receipt["status"] != expected):
            problems.append(f"{where}: {status} 행의 요청에 {expected} 수신 기록이 없다")
        if receipt is not None:
            params = receipt["params"]
            request_partner = params.get("cntyCd", types.ALL_PARTNER)
            code = params.get("hsSgn", "")
            request_months = set(ingest.months_between(params["strtYymm"], params["endYymm"])) \
                if {"strtYymm", "endYymm"} <= set(params) else set()
            if partner != request_partner:
                problems.append(f"{where}: 상대국이 요청 조건과 다르다")
            exact = status != types.OBSERVED or month == types.TOTAL_ROW_MONTH  # 상태 행·총계 행은 요청 코드 그대로
            if (exact and hs != code) or (not exact and not hs.startswith(code)):
                problems.append(f"{where}: HS 코드가 요청 코드와 맞지 않다")
            if types.MONTH_RE.fullmatch(month) and month not in request_months:
                problems.append(f"{where}: 달이 요청 조회 구간 밖이다")
        if status == types.OBSERVED:
            if raw_file != f"{rid}.xml" or not isinstance(locator, str) or not RAW_LOCATOR_RE.fullmatch(locator):
                problems.append(f"{where}: OBSERVED 행의 raw_file_id·raw_row_locator 모양이 수집기와 다르다")
        else:
            wanted = {types.UNRESOLVED_ZERO: f"{rid}.xml", types.CONFIRMED_NO_TRADE: f"{rid}.xml",
                      types.REQUEST_FAILED: None if receipt is None else receipt["raw_file_id"]}.get(status)
            if locator is not None or row[at["item_name"]] is not None or raw_file != wanted:
                problems.append(f"{where}: {status} 행의 raw 위치 칸이 수집기 규칙과 다르다")
        if status == types.CONFIRMED_NO_TRADE and (row[at["flow"]] != types.METRIC_FLOW or level != 6):
            problems.append(f"{where}: CONFIRMED_NO_TRADE가 수입·HS6 자릿수 행이 아니다")
    # NOT_COLLECTED 행 집합: 수신 기록 없는 계획 요청의 상태 행 + 계획 밖 비교국 행(단위 S2 규칙)
    expected_nc: set[tuple] = set()
    for rid, request in planned.items():
        if rid not in receipts:
            params = request["params"]
            for status_row in build._status_rows(snapshot_id, rid, params.get("cntyCd", types.ALL_PARTNER),
                                                 params.get("hsSgn", ""), request["months"], types.NOT_COLLECTED, None):
                expected_nc.add(tuple(status_row))
    try:
        for status_row in build.peer_not_collected_rows(snapshot_id, plan, _peer_rows(con)):
            expected_nc.add(tuple(status_row))
    except build.BuildError as exc:
        problems.append(f"비교국 표로 NOT_COLLECTED 행을 다시 만들지 못했다({exc})")
    stored_nc = {tuple(row[1:]) for row in rows if row[at["observation_status"]] == types.NOT_COLLECTED}
    if stored_nc != expected_nc:
        problems.append(f"NOT_COLLECTED 행이 계획·비교국 표에서 다시 만든 집합과 다르다(스냅샷 {len(stored_nc)}, "
                        f"다시 만든 행 {len(expected_nc)})")
    # 승격: CONFIRMED_NO_TRADE를 되돌려 규칙을 다시 적용한 집합과 같아야 한다
    promoted = {row[0] for row in rows if row[at["observation_status"]] == types.CONFIRMED_NO_TRADE}
    rule = record.get("confirmed_no_trade_rule") if record else (PROMOTION_RULES[0] if promoted else None)
    reverted = [row[1:] for row in rows]
    for values in reverted:
        if values[at["observation_status"] - 1] == types.CONFIRMED_NO_TRADE:
            values[at["observation_status"] - 1] = types.UNRESOLVED_ZERO
    try:
        build.apply_promotion(reverted, None if rule is None else {"rule": rule})
        again = {rows[i][0] for i, values in enumerate(reverted)
                 if values[at["observation_status"] - 1] == types.CONFIRMED_NO_TRADE}
        if again != promoted:
            problems.append(f"CONFIRMED_NO_TRADE 행이 승격 규칙({rule})을 다시 적용한 집합과 다르다"
                            f"(스냅샷 {len(promoted)}, 다시 적용 {len(again)})")
    except build.BuildError as exc:
        problems.append(f"승격 규칙을 다시 적용하지 못했다({exc})")
    return report.add("observation_rules", not problems,
                      {"rows": len(rows), "confirmed_no_trade_rule": rule, **_problems_detail(problems)})


def _check_peer_groups(con: sqlite3.Connection, meta: dict, record: dict | None, peer_files: list[Path] | None,
                       report: _Report) -> bool:
    """비교국 표 행 규칙(단위 S2와 같은 함수)과 적재 순서, 그리고 입력 CSV와의 대조(빌드 기록의 sha256·행 값)."""
    stored = _peer_rows(con)
    problems = build.peer_group_problems([dict(zip(types.PEER_GROUP_KEYS, row)) for row in stored],
                                         meta.get("collection_plan") or {})
    if not problems and stored != build.order_peer_rows(stored):
        problems.append("peer_group 행이 정해진 적재 순서가 아니다")
    ok = report.add("peer_group_rows", not problems, {"rows": len(stored), **_problems_detail(problems)})
    entries = list((record or {}).get("peer_group_files") or [])
    if peer_files is None:
        candidates = [build.REPO_ROOT.joinpath(*REFERENCE_DIR, entry.get("file_name", "")) for entry in entries]
        if not entries:
            if stored and record is not None:
                return report.add("peer_group_sources", False,
                                  {"error": "빌드 기록에 비교국 표 파일이 없는데 peer_group 행이 있다"}) and ok
            if stored:  # 빌드 기록이 없는 개발 빌드: 원본을 알 수 없어 건너뛴다(행 규칙은 peer_group_rows가 봤다)
                return report.add("peer_group_sources", None,
                                  {"skipped": "빌드 기록이 없어 원본 비교국 표와 대조하지 못했다"}) or ok
            return report.add("peer_group_sources", True, {"files": 0}) and ok
        missing = [path.name for path in candidates if not path.is_file()]
        if missing:  # 원본 대조가 필요한 빌드인데 원본을 찾지 못했다(Codex 권고: 건너뛰지 않고 실패)
            return report.add("peer_group_sources", False,
                              {"error": "빌드 기록의 비교국 표 파일을 data/reference/에서 찾지 못했다",
                               "missing": missing}) and ok
        peer_files = candidates
    source_problems = []
    names = sorted(Path(path).name for path in peer_files)
    if record is not None:
        recorded = {entry.get("file_name"): entry.get("sha256") for entry in entries}
        if sorted(recorded) != names:
            source_problems.append("비교국 표 파일 이름이 빌드 기록과 다르다")
        for path in peer_files:
            digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
            if recorded.get(Path(path).name) != digest:
                source_problems.append(f"{Path(path).name}: sha256이 빌드 기록과 다르다")
    try:
        loaded = build.order_peer_rows(build.load_peer_groups(list(peer_files)))
        if loaded != stored:
            source_problems.append("peer_group 행이 비교국 표 CSV를 다시 읽은 행과 다르다")
    except (build.BuildError, OSError, TypeError) as exc:
        source_problems.append(f"비교국 표 CSV를 다시 읽지 못했다({_error_detail(exc)['error']})")
    return report.add("peer_group_sources", not source_problems,
                      {"files": names, **_problems_detail(source_problems)}) and ok


def _check_receipts(con: sqlite3.Connection, report: _Report) -> bool:
    problems = []
    for rid, status, response_hash in con.execute("SELECT request_id, status, response_hash FROM collection_receipt"):
        if status not in types.RECEIPT_STATUSES:
            problems.append(f"{rid}: status가 OK·FAILED가 아니다")
        if status == "OK" and not (isinstance(response_hash, str) and len(response_hash) == 64):
            problems.append(f"{rid}: OK 수신 기록의 response_hash가 sha256이 아니다")
    return report.add("collection_receipts", not problems, _problems_detail(problems))


def _peer_rows(con: sqlite3.Connection) -> list[list]:
    return [list(row) for row in con.execute(
        f"SELECT {', '.join(types.PEER_GROUP_KEYS)} FROM peer_group ORDER BY rowid")]


def _check_against_raw(con: sqlite3.Connection, meta: dict, snapshot_id: str, source_dir: Path, record: dict | None,
                       report: _Report) -> bool:
    """raw·manifest·수집기 수신 기록에서 단위 S2 규칙으로 다시 만든 행·메타와 한 칸씩 비교한다."""
    try:
        source = build.read_source(source_dir, snapshot_id)
        rows, receipts = build.plan_rows(snapshot_id, source["manifest"]["requests"], source["receipts"],
                                         source["raw_dir"])
        raw_sha256, _ = build.raw_combined_sha256(source["raw_dir"])
    except (build.BuildError, OSError, ValueError, KeyError) as exc:
        return report.add("raw_rebuild", False, _error_detail(exc))
    ok = report.add("raw_sha256", raw_sha256 == meta.get("raw_sha256"),
                    {"recomputed_matches_meta": raw_sha256 == meta.get("raw_sha256")})
    rows += build.peer_not_collected_rows(snapshot_id, source["manifest"]["config"], _peer_rows(con))
    has_promoted = con.execute("SELECT COUNT(*) FROM observation WHERE observation_status = ?",
                               (types.CONFIRMED_NO_TRADE,)).fetchone()[0]
    rule = record.get("confirmed_no_trade_rule") if record else (PROMOTION_RULES[0] if has_promoted else None)
    promoted = build.apply_promotion(rows, None if rule is None else {"rule": rule})
    stored = [list(row[1:]) for row in con.execute(
        f"SELECT rowid, {', '.join(types.OBSERVATION_COLUMNS)} FROM observation ORDER BY rowid")]
    differ = [f"observation rowid {i + 1}" for i, (a, b) in enumerate(zip(stored, rows)) if a != b]
    if len(stored) != len(rows):
        differ.append(f"행 수가 다르다(스냅샷 {len(stored)}, raw에서 다시 만든 행 {len(rows)})")
    ok &= report.add("observation_matches_raw", not differ,
                     {"rows": len(rows), "confirmed_no_trade_rule": rule, "confirmed_no_trade_rows": promoted,
                      **_problems_detail(differ)})
    stored_receipts = [list(row) for row in con.execute(
        f"SELECT {', '.join(types.COLLECTION_RECEIPT_COLUMNS)} FROM collection_receipt ORDER BY rowid")]
    rebuilt_receipts = [[r[c] for c in types.COLLECTION_RECEIPT_COLUMNS] for r in receipts]
    ok &= report.add("receipts_match_raw", stored_receipts == rebuilt_receipts, {"receipts": len(rebuilt_receipts)})
    try:
        rebuilt_meta = build.snapshot_object(snapshot_id, source, rows, raw_sha256)
    except build.BuildError as exc:
        report.add("meta_matches_source", False, _error_detail(exc))
        return False
    ok &= report.add("meta_matches_source", rebuilt_meta == meta, None)
    return ok


def verify_snapshot(snapshot_id: str, *, build_file: Path | None = None, source_dir: Path | None = None,
                    check_raw: bool = True, peer_group_files: list[Path] | None = None) -> dict:
    """스냅샷 빌드 파일을 검증한 보고. 머리 설명의 출력 모양이다."""
    canonical = build_file is None
    if canonical:
        build_file = build.SNAPSHOTS_ROOT / build._check_snapshot_id(snapshot_id) / build.BUILD_FILE
    build_file = Path(build_file)
    source_dir = build.SNAPSHOTS_ROOT / build._check_snapshot_id(snapshot_id) if source_dir is None else Path(source_dir)
    report = _Report()
    out = {"snapshot_id": snapshot_id, "schema_version": types.SCHEMA_VERSION, "build_file": build_file.name,
           "ok": False, "normalized_sha256": None, "recorded_normalized_sha256": None, "checks": report.checks,
           "counts": {}}
    try:
        con = build.open_read_only(build_file)
    except (build.BuildError, sqlite3.Error) as exc:
        report.add("open_read_only", False, _error_detail(exc))
        return out
    try:
        report.add("open_read_only", True)
        mode = con.execute("PRAGMA journal_mode").fetchone()[0]
        report.add("journal_mode_not_wal", mode != "wal", {"journal_mode": mode})
        if not _check_tables(con, report):
            return out
        meta = {key: json.loads(value) for key, value in con.execute("SELECT key, value FROM snapshot_meta")}
        record_path = build_file.with_suffix(".json")
        record = json.loads(record_path.read_text(encoding="utf-8")) if record_path.is_file() else None
        receipts = _receipt_map(con)
        meta_ok = _check_meta(meta, snapshot_id, report)
        _check_observation_values(con, meta, report)
        _check_all_duplicates(con, report)
        _check_receipts(con, report)
        if meta_ok:  # 아래 셋은 raw 없이 도는 계약 검사다(check_raw와 관계없이 늘 돈다)
            _check_coverage(con, meta, receipts, report)
            _check_observation_rules(con, meta, snapshot_id, receipts, record, report)
            _check_peer_groups(con, meta, record, peer_group_files, report)
        if check_raw:
            if (source_dir / build.MANIFEST_FILE).is_file() and (source_dir / build.RAW_DIR).is_dir():
                _check_against_raw(con, meta, snapshot_id, source_dir, record, report)
            else:
                report.add("raw_rebuild", False, {"error": "raw 대조 원천(manifest.json, raw/)이 없다"})
        else:
            report.add("raw_rebuild", None, {"skipped": "check_raw가 거짓이라 raw 대조를 건너뛰었다"})
        try:
            computed = build.normalized_sha256(con)
        except build.BuildError as exc:
            report.add("normalized_sha256", False, _error_detail(exc))
            computed = None
        out["normalized_sha256"] = computed
        recorded = None if record is None else record.get("normalized_sha256")
        out["recorded_normalized_sha256"] = recorded
        if record is None:
            report.add("normalized_sha256_record", False if canonical else None,
                       {"error" if canonical else "skipped": f"기록 {record_path.name}이 없다"})
        else:
            report.add("normalized_sha256_record", computed is not None and computed == recorded,
                       {"matches": computed == recorded})
        status_counts = dict(con.execute("SELECT observation_status, COUNT(*) FROM observation WHERE flow = 'import' "
                                          "GROUP BY observation_status ORDER BY observation_status").fetchall())
        out["counts"] = {table: con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] for table in TABLE_COLUMNS}
        out["counts"]["import_observation_status"] = status_counts
    finally:
        con.close()
    out["ok"] = all(check["ok"] for check in report.checks if check["ok"] is not None)
    return out


def run(inp: object) -> object:
    """진입 함수. 입력 {"snapshot_id", "build_file"?, "source_dir"?, "check_raw"?} → 검증 보고(JSON 객체, `ok`는 합격 여부)."""
    if not isinstance(inp, dict) or "snapshot_id" not in inp:
        raise ValueError("입력은 snapshot_id를 담은 객체다")
    unknown = set(inp) - {"snapshot_id", "build_file", "source_dir", "check_raw", "peer_group_files"}
    if unknown:
        raise ValueError(f"모르는 입력 키: {', '.join(sorted(unknown))}")
    check_raw = inp.get("check_raw", True)
    if not isinstance(check_raw, bool):
        raise ValueError("check_raw는 참·거짓이다")

    def repo_path(value: object) -> Path | None:
        if value is None:
            return None
        path = Path(value)
        return path if path.is_absolute() else build.REPO_ROOT / path

    files = inp.get("peer_group_files")
    if files is not None and (not isinstance(files, list) or not all(isinstance(f, str) for f in files)):
        raise ValueError("peer_group_files는 경로 글자의 목록이다")
    return verify_snapshot(inp["snapshot_id"], build_file=repo_path(inp.get("build_file")),
                           source_dir=repo_path(inp.get("source_dir")), check_raw=check_raw,
                           peer_group_files=None if files is None else [repo_path(f) for f in files])
