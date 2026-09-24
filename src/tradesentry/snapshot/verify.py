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

입력(`run`): {"snapshot_id", "build_file"?, "source_dir"?, "check_raw"?}
- build_file이 없으면 정본 빌드 `data/snapshots/{snapshot_id}/snapshot_build.sqlite`를 보고, 그 옆 기록
  `snapshot_build.json`의 `normalized_sha256`과 반드시 대조한다(기록이 없으면 실패).
- 승인 전 개발 빌드는 build_file(저장소 루트 기준 상대경로 또는 절대경로, 예:
  `outputs/snapshot_build-{시각}/snapshot_build-{시각}.sqlite`)로 준다. 옆에 같은 이름의 기록 `.json`이 있으면 대조하고,
  없으면 대조를 건너뛰었다고 적는다(실패가 아니다).
- raw 대조의 원천은 source_dir(없으면 `data/snapshots/{snapshot_id}/`: manifest.json, raw/, 수집기 snapshot.sqlite)다.
  check_raw가 참(기본)인데 원천이 없으면 그 검사는 실패다. 거짓이면 raw 대조를 건너뛰고 보고에 적는다.

출력: {"snapshot_id", "schema_version", "build_file"(파일 이름만), "ok", "normalized_sha256",
"recorded_normalized_sha256", "checks": [{"name", "ok", "detail"}…], "counts"}. `ok`는 건너뛰지 않은 검사가 모두 통과했는지다.
로컬 절대경로는 보고에 적지 않는다(N13).
"""
import json
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
        problems.append("schema_version이 1이 아니다")
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
        if not (types.MONTH_RE.fullmatch(month or "") or (month or "").startswith(types.RAW_MONTH_PREFIX)):
            problems.append(f"{where}: month가 YYYYMM이나 RAW: 원문이 아니다")
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


def _check_coverage(con: sqlite3.Connection, meta: dict, report: _Report) -> bool:
    """분석 범위의 키마다 값 행(부모 HS6 행·ALL HS10 행)이나 상태 행이 있다."""
    plan = meta.get("collection_plan") or {}
    period = meta.get("period") or {}
    months = ingest.months_between(period["start"], period["end"])
    rows = con.execute("SELECT partner_code, hs_code, hs_level, month, observation_status FROM observation "
                       "WHERE flow = 'import' AND month NOT LIKE 'RAW:%'").fetchall()
    value_keys, status_keys = set(), set()
    for partner, hs, level, month, status in rows:
        if status == types.OBSERVED:
            if level == 6 and partner != types.ALL_PARTNER:
                value_keys.add((partner, hs, month))
            elif level == 10 and partner == types.ALL_PARTNER:
                value_keys.add((partner, hs[:6], month))
        else:
            status_keys.add((partner, hs, month))
    missing = []
    for hs6 in plan.get("hs6", []):
        for partner in list(plan.get("partners", [])) + [types.ALL_PARTNER]:
            for month in months:
                if (partner, hs6, month) in value_keys:
                    continue
                if (partner, hs6, month) in status_keys or (partner, hs6[:4], month) in status_keys:
                    continue
                missing.append(f"{partner}·{hs6}·{month}")
    return report.add("coverage", not missing, {"keys": len(plan.get("hs6", [])) * (len(plan.get("partners", [])) + 1)
                                                * len(months), **_problems_detail(missing)})


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
                    check_raw: bool = True) -> dict:
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
        meta_ok = _check_meta(meta, snapshot_id, report)
        _check_observation_values(con, meta, report)
        _check_all_duplicates(con, report)
        if meta_ok:
            _check_coverage(con, meta, report)
        _check_receipts(con, report)
        record_path = build_file.with_suffix(".json")
        record = json.loads(record_path.read_text(encoding="utf-8")) if record_path.is_file() else None
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
    unknown = set(inp) - {"snapshot_id", "build_file", "source_dir", "check_raw"}
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

    return verify_snapshot(inp["snapshot_id"], build_file=repo_path(inp.get("build_file")),
                           source_dir=repo_path(inp.get("source_dir")), check_raw=check_raw)
