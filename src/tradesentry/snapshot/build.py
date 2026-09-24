"""단위 S2 스냅샷 빌더.

단위 ID: S2
도메인명: snapshot_build
소유: D
입력: raw·manifest·수집기 SQLite(수신 기록·메타, 읽기 전용)·비교국 표(`peer_group_g0.csv`·`peer_group_g1.csv`)·승격 규칙
출력: 파생 SQLite(결정적 rowid)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.ingest, tradesentry.snapshot

정본: 자료 계약 docs/rules/DATA_CONTRACT_V1.md §2.3(객체), §2.3.2 행 규칙, §3.4(관측 상태·`NOT_COLLECTED` 행·승격),
§4.4(rowid 안정성), 결정 기록 20260924-2212-user-decision-snapshot-build-and-g0.md(최종 빌드 파일과 옮기기 조건).

무엇을 만드나
- 스냅샷 폴더(`data/snapshots/{snapshot_id}/`)의 manifest(`manifest.json`)와 raw 응답(`raw/*.xml`)에서 `observation` 행을
  다시 만들고, 수집기 SQLite(`snapshot.sqlite`)에서 수신 기록(`collection_receipt`)과 스냅샷 메타를 읽어, 파생 SQLite를
  새 파일로 만든다. 입력 파일은 읽기만 한다(수집기 SQLite는 읽기 전용 URI `mode=ro`로 연다). raw·manifest를 다시 쓰지 않는다.
- 관측 행은 기존 수집기(`src/tradesentry/ingest.py`의 `store_result`)와 같은 규칙으로 만든다(같은 `parse_response`를 쓴다).
  수신 기록의 시각·HTTP 상태·시도 수는 raw로 다시 만들 수 없어 수집기 SQLite에서 가져오고, raw로 다시 셀 수 있는 값
  (응답 sha256, 행 수, 결과 코드)은 대조해 다르면 빌드를 멈춘다.
- 행 순서(결정적 rowid, §4.4 규칙 1): manifest의 요청 순서대로, 요청마다 응답 행 순서 × (import, export), 그다음 그 요청의
  상태 행(요청 월 순서 × (import, export))을 넣는다. 수신 기록이 없는 계획 요청은 그 자리에 `NOT_COLLECTED` 행을 넣는다.
  비교국 표가 수집 계획 밖 국가를 가리키면 그 국가의 `NOT_COLLECTED` 행을 맨 끝에 키 순서로 붙인다(계획 행의 rowid를
  밀지 않는다). 수집기가 모든 요청을 manifest 순서로 한 번에 받은 스냅샷(v2)이면 관측 rowid가 수집기 SQLite와 같다.
- 승격(§3.4): 정책의 `confirmed_no_trade` 규칙(단위 K4)이 있으면 해당 행의 `observation_status`만 `CONFIRMED_NO_TRADE`로
  바꾼다. 행을 더하거나 지우지 않으므로 rowid는 그대로다. V·Q 칸은 null로 둔다.
- `snapshot_meta` 표: 계약 `snapshot` 객체의 키(`normalized_sha256` 제외)와 `schema_version`을 키마다 한 행, 값은 JSON
  글자열로 둔다. 빌드 시각·경로·정책 버전 같은 출처 정보는 SQLite에 넣지 않고 옆의 빌드 기록 JSON에 둔다. 그래서 같은
  입력으로 다시 빌드하면 `normalized_sha256`이 같다.
- `peer_group` 표: 비교국 표 CSV(열 = 계약 §2.3.6 필드 17개)를 적재한다. `similarity`는 원문 표기를 지키려고 TEXT로 둔다.

`normalized_sha256`(§2.3.1·§4.4 규칙 4. 직렬화는 D가 정한다): 표 `collection_receipt`, `observation`, `peer_group`,
`snapshot_meta`를 이름 순으로, 표마다 머리 줄 `["table", 표 이름, [열 이름…]]`(열은 정의 순서) 한 줄과 행마다
`[rowid, 열 값…]` 한 줄(rowid 순서)을 JSON(키 없음, `ensure_ascii=False`, 구분자 `,`·`:`)으로 적어 줄 끝에 `\\n`을 붙이고,
그 UTF-8 바이트 전체의 sha256(16진수 소문자 64자)이다. 값은 INTEGER→JSON 정수, TEXT→JSON 문자열(정규화 없음),
NULL→null이다. REAL·BLOB 값이 있으면 계산을 거부한다. rowid가 들어가므로 재적재로 rowid가 바뀌면 값도 바뀐다.

만드는 파일(덮어쓰지 않는다: 이미 있으면 실패)
- `build_snapshot`: 확보한 실행 폴더(`outputs/snapshot_build-{시각}/`)에 `snapshot_build-{시각}.sqlite`와 빌드 기록
  `snapshot_build-{시각}.json`. 실행명 확보(N8)는 부르는 쪽(CLI 처리 함수)이 한다.
- `install_build`: 승인·동결 뒤(DT7 ②) 정본 자리 `data/snapshots/{snapshot_id}/snapshot_build.sqlite`와 기록
  `snapshot_build.json`으로 옮긴다. `os.link`(이미 있으면 실패) 뒤 원본을 지우고, 다른 파일 시스템이면 `"xb"` 복사한다.
  `os.rename`·`shutil.move`는 쓰지 않는다. 수집기의 `snapshot.sqlite`·`snapshot_hash.json`·`raw/`·manifest는 고치지 않는다.
- SQLite는 저널 모드 DELETE(WAL 아님)로 만들고 VACUUM을 하지 않는다.
- 로컬 절대경로는 SQLite와 빌드 기록 어디에도 적지 않는다(N13).
"""
import csv
import errno
import hashlib
import json
import os
import re
import sqlite3
import tempfile
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from tradesentry import ingest
from tradesentry.contract import types
from tradesentry.contract.policy_load import load_policy, parse_policy

REPO_ROOT = Path(__file__).resolve().parents[3]
SNAPSHOTS_ROOT = REPO_ROOT / "data" / "snapshots"
DOMAIN = "snapshot_build"
BUILD_FILE = "snapshot_build.sqlite"  # 정본 파일 이름(결정 기록 20260924-2212 스냅샷 빌드)
BUILD_RECORD = "snapshot_build.json"  # 정본 옆 빌드 기록(normalized_sha256). snapshot_hash.json은 고치지 않는다
MANIFEST_FILE = "manifest.json"
COLLECTOR_DB = "snapshot.sqlite"
HASH_FILE = "snapshot_hash.json"
RAW_DIR = "raw"
COLLECTOR_HS_VERSION = "HSK"  # 수집기 store_result가 모든 관측 행에 적는 값
HASH_TABLES = ("collection_receipt", "observation", "peer_group", "snapshot_meta")  # 이름 순
SNAPSHOT_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")  # 경로 조각으로 안전한 스냅샷 ID
STAMP_RE = re.compile(r"[0-9]{12}")
OK_RESULT_CODES = ("00", "0")  # 수집기 store_result와 같다
PROMOTION_RULE = "ingest_verify_candidates"
NULLABLE_PEER_TEXT = ("", "null")  # 비교국 표 CSV에서 null로 읽는 칸 값
NULLABLE_PEER_COLUMNS = ("baci_country_code", "similarity", "community_id")

DDL = """
CREATE TABLE snapshot_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE collection_receipt(
  request_id TEXT PRIMARY KEY, endpoint TEXT, params_json TEXT, status TEXT, http_status INTEGER,
  attempts INTEGER, response_hash TEXT, row_count INTEGER, result_code TEXT, result_msg TEXT,
  error TEXT, elapsed_ms INTEGER, raw_file_id TEXT, timestamp TEXT);
CREATE TABLE observation(
  snapshot_id TEXT, request_id TEXT, month TEXT, partner_code TEXT, partner_namespace TEXT,
  hs_code TEXT, hs_level INTEGER, hs_version TEXT, flow TEXT, amount_usd INTEGER, net_weight_kg INTEGER,
  observation_status TEXT, raw_file_id TEXT, raw_row_locator TEXT, item_name TEXT,
  PRIMARY KEY(request_id, month, partner_code, hs_code, flow));
CREATE TABLE peer_group(
  entity_type TEXT, entity_id TEXT, entity_namespace TEXT, baci_country_code TEXT, scope_type TEXT, scope_id TEXT,
  peer_rank INTEGER, peer_id TEXT, similarity TEXT, community_id TEXT, method TEXT, grouping_version TEXT,
  params_hash TEXT, source_version TEXT, source_year INTEGER, input_sha256 TEXT, generated_at TEXT,
  UNIQUE(grouping_version, entity_type, entity_id, scope_type, scope_id, peer_rank));
CREATE INDEX observation_lookup ON observation(partner_code, month, hs_level, flow);
CREATE INDEX peer_group_lookup ON peer_group(entity_id, grouping_version);
"""

# 관측 행 목록(list)의 칸 위치(types.OBSERVATION_COLUMNS 순서).
_COL = {name: i for i, name in enumerate(types.OBSERVATION_COLUMNS)}


class BuildError(Exception):
    """스냅샷을 빌드할 수 없다(입력이 서로 맞지 않거나 계약을 어긴다). 메시지에는 로컬 절대경로를 넣지 않는다."""


# ----------------------------------------------------------------------------- 입력 읽기
def open_read_only(path: Path) -> sqlite3.Connection:
    """SQLite 파일을 읽기 전용 URI(`mode=ro`)로 연다. 파일이 없으면 만들지 않고 실패한다."""
    if not Path(path).is_file():
        raise BuildError(f"SQLite 파일이 없다: {Path(path).name}")
    con = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    con.execute("PRAGMA query_only = ON")
    return con


def _check_snapshot_id(snapshot_id: object) -> str:
    if not isinstance(snapshot_id, str) or not SNAPSHOT_ID_RE.fullmatch(snapshot_id):
        raise BuildError("snapshot_id는 영문·숫자로 시작하고 영문·숫자·밑줄·하이픈만 쓴다")
    return snapshot_id


def read_source(source_dir: Path, snapshot_id: str) -> dict:
    """스냅샷 폴더의 manifest, 수집기 SQLite의 수신 기록·메타, snapshot_hash.json(있으면)을 읽는다."""
    source_dir = Path(source_dir)
    try:
        manifest = json.loads((source_dir / MANIFEST_FILE).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BuildError(f"{MANIFEST_FILE}이 없다") from exc
    if manifest.get("snapshot_id") != snapshot_id:
        raise BuildError(f"{MANIFEST_FILE}의 snapshot_id가 {snapshot_id}가 아니다")
    if not isinstance(manifest.get("config"), dict) or not isinstance(manifest.get("requests"), list):
        raise BuildError(f"{MANIFEST_FILE}에 config와 requests가 없다")
    con = open_read_only(source_dir / COLLECTOR_DB)
    try:
        con.row_factory = sqlite3.Row
        receipts = {row["request_id"]: dict(row) for row in con.execute(
            "SELECT " + ", ".join(types.COLLECTION_RECEIPT_COLUMNS) + " FROM collection_receipt ORDER BY rowid")}
        meta = {key: value for key, value in con.execute("SELECT key, value FROM snapshot_meta")}
    finally:
        con.close()
    hash_record = None
    if (source_dir / HASH_FILE).is_file():
        hash_record = json.loads((source_dir / HASH_FILE).read_text(encoding="utf-8"))
    return {"manifest": manifest, "receipts": receipts, "collector_meta": meta, "hash_record": hash_record,
            "raw_dir": source_dir / RAW_DIR}


def raw_combined_sha256(raw_dir: Path) -> tuple[str, int]:
    """raw 결합 sha256과 파일 수. snapshot_hash.json의 `method`(`shasum -a 256 raw/*.xml | shasum -a 256`)와 같은 계산:
    파일 이름 순으로 `<파일 sha256>  raw/<파일 이름>\\n` 줄을 이어 붙인 바이트의 sha256."""
    names = sorted(p.name for p in Path(raw_dir).glob("*.xml") if p.is_file())
    lines = "".join(f"{hashlib.sha256((Path(raw_dir) / name).read_bytes()).hexdigest()}  raw/{name}\n" for name in names)
    return hashlib.sha256(lines.encode("utf-8")).hexdigest(), len(names)


# ----------------------------------------------------------------------------- 관측 행 만들기
def _status_rows(snapshot_id: str, rid: str, partner: str, hs_sgn: str, months: list[str], status: str,
                 raw_file_id: str | None) -> list[list]:
    return [[snapshot_id, rid, month, partner, types.PARTNER_NAMESPACE, hs_sgn, len(hs_sgn), COLLECTOR_HS_VERSION, flow,
             None, None, status, raw_file_id, None, None]
            for month in months for flow in types.FLOWS]


def _int_value(value: object, where: str) -> int | None:
    parsed = ingest.to_int_or_none(value)
    if parsed is not None and (isinstance(parsed, bool) or not isinstance(parsed, int)):
        raise BuildError(f"{where}: 정수가 아닌 금액·중량이다(계약 §11.1: USD·kg 정수)")
    return parsed


def _response_rows(snapshot_id: str, request: dict, receipt: dict, raw_dir: Path) -> list[list]:
    rid, endpoint, params = request["request_id"], request["endpoint"], request["params"]
    raw_file_id = receipt["raw_file_id"]
    if raw_file_id != f"{rid}.xml":
        raise BuildError(f"수신 기록 {rid}: OK 응답의 raw_file_id가 {rid}.xml이 아니다")
    path = Path(raw_dir) / raw_file_id
    if not path.is_file():
        raise BuildError(f"수신 기록 {rid}: raw 파일이 없다({RAW_DIR}/{raw_file_id})")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != receipt["response_hash"]:
        raise BuildError(f"수신 기록 {rid}: raw 파일 sha256이 response_hash와 다르다")
    parsed = ingest.parse_response(raw)
    if parsed["envelope"] != "response" or parsed["result_code"] not in OK_RESULT_CODES:
        raise BuildError(f"수신 기록 {rid}: OK인데 raw 응답이 정상 봉투·결과 코드가 아니다")
    if parsed["result_code"] != receipt["result_code"] or len(parsed["items"]) != receipt["row_count"]:
        raise BuildError(f"수신 기록 {rid}: result_code 또는 row_count가 raw 응답과 다르다")
    hs_field = ingest.ENDPOINTS[endpoint]["hs_field"]
    partner = params.get("cntyCd", types.ALL_PARTNER)
    hs_sgn = params.get("hsSgn", "")
    rows, seen_months = [], set()
    for item in parsed["items"]:
        month = (item.get("year") or "").replace(".", "")
        hs = (item.get(hs_field) or "").strip()
        if hs in ("", "-"):
            hs = hs_sgn  # 총계 행은 요청 코드로 귀속(수집기와 같다)
        if not (len(month) == 6 and month.isdigit()):
            month = f"{types.RAW_MONTH_PREFIX}{item.get('year')}"
        seen_months.add(month)
        for flow, amount_field, weight_field in (("import", "impDlr", "impWgt"), ("export", "expDlr", "expWgt")):
            where = f"수신 기록 {rid} item[{item['_row']}] {flow}"
            rows.append([snapshot_id, rid, month, partner, types.PARTNER_NAMESPACE, hs, len(hs), COLLECTOR_HS_VERSION,
                         flow, _int_value(item.get(amount_field), where), _int_value(item.get(weight_field), where),
                         types.OBSERVED, raw_file_id, f"item[{item['_row']}]", item.get("statKor")])
    missing = [m for m in request["months"] if m not in seen_months]
    rows += _status_rows(snapshot_id, rid, partner, hs_sgn, missing, types.UNRESOLVED_ZERO, raw_file_id)
    return rows


def plan_rows(snapshot_id: str, requests: list, receipts: dict, raw_dir: Path) -> tuple[list[list], list[dict]]:
    """manifest 요청 순서대로 관측 행과 수신 기록 행을 만든다. 계획 밖 수신 기록이 있으면 BuildError."""
    rows: list[list] = []
    receipt_rows: list[dict] = []
    seen: set[str] = set()
    for index, request in enumerate(requests):
        endpoint, params = request.get("endpoint"), request.get("params")
        if endpoint not in ingest.ENDPOINTS or not isinstance(params, dict):
            raise BuildError(f"manifest 요청 {index}: 엔드포인트나 파라미터가 맞지 않다")
        rid = ingest.request_id(endpoint, params)
        if request.get("request_id") != rid or rid in seen:
            raise BuildError(f"manifest 요청 {index}: request_id가 파라미터와 맞지 않거나 겹친다")
        seen.add(rid)
        if request.get("months") != ingest.months_between(params["strtYymm"], params["endYymm"]):
            raise BuildError(f"manifest 요청 {rid}: months가 조회 구간과 다르다")
        partner = params.get("cntyCd", types.ALL_PARTNER)
        hs_sgn = params.get("hsSgn", "")
        receipt = receipts.get(rid)
        if receipt is None:
            rows += _status_rows(snapshot_id, rid, partner, hs_sgn, request["months"], types.NOT_COLLECTED, None)
            continue
        if receipt["endpoint"] != endpoint or json.loads(receipt["params_json"]) != params:
            raise BuildError(f"수신 기록 {rid}: 엔드포인트나 파라미터가 manifest와 다르다")
        receipt_rows.append(receipt)
        if receipt["status"] == "OK":
            rows += _response_rows(snapshot_id, request, receipt, raw_dir)
        elif receipt["status"] == "FAILED":
            rows += _status_rows(snapshot_id, rid, partner, hs_sgn, request["months"], types.REQUEST_FAILED,
                                 receipt["raw_file_id"])
        else:
            raise BuildError(f"수신 기록 {rid}: status가 OK·FAILED가 아니다")
    extra = sorted(set(receipts) - seen)
    if extra:
        raise BuildError(f"manifest에 없는 수신 기록이 {len(extra)}건 있다(첫 번째 {extra[0]})")
    return rows, receipt_rows


def apply_promotion(rows: list[list], rule: dict | None) -> int:
    """승격 규칙을 관측 행에 적용하고 바꾼 행 수를 돌려준다. 상태 칸만 바꾼다(행 수·순서·값 칸은 그대로)."""
    if rule is None:
        return 0
    if rule.get("rule") != PROMOTION_RULE:
        raise BuildError(f"모르는 승격 규칙: {rule.get('rule')!r}")
    c = _COL
    observed6: set[tuple] = set()
    sibling_months: set[tuple] = set()
    for row in rows:
        if row[c["flow"]] == "import" and row[c["observation_status"]] == types.OBSERVED \
                and row[c["hs_level"]] == 6 and types.MONTH_RE.fullmatch(row[c["month"]]):
            observed6.add((row[c["partner_code"]], row[c["hs_code"]], row[c["month"]]))
            sibling_months.add((row[c["partner_code"]], row[c["hs_code"]][:4], row[c["month"]]))
    promoted = 0
    for row in rows:
        if row[c["flow"]] == "import" and row[c["observation_status"]] == types.UNRESOLVED_ZERO and row[c["hs_level"]] == 6:
            partner, hs, month = row[c["partner_code"]], row[c["hs_code"]], row[c["month"]]
            if (partner, hs, month) not in observed6 and (partner, hs[:4], month) in sibling_months:
                row[c["observation_status"]] = types.CONFIRMED_NO_TRADE
                promoted += 1
    return promoted


# ----------------------------------------------------------------------------- 비교국 표
def _peer_value(column: str, text: str, where: str) -> object:
    if column in NULLABLE_PEER_COLUMNS and text.strip() in NULLABLE_PEER_TEXT:
        return None
    if column in ("peer_rank", "source_year"):
        if not re.fullmatch(r"[0-9]+", text) or int(text) < 1:
            raise BuildError(f"{where}.{column}: 1 이상 정수여야 한다")
        return int(text)
    if column == "similarity":
        try:
            if not Decimal(text).is_finite():
                raise InvalidOperation
        except InvalidOperation as exc:
            raise BuildError(f"{where}.similarity: 수여야 한다") from exc
        return text  # 원문 표기를 지킨다(TEXT)
    if not text:
        raise BuildError(f"{where}.{column}: 비었다")
    return text


def load_peer_groups(paths: list[Path]) -> list[list]:
    """비교국 표 CSV들을 읽어 `peer_group` 행 목록(계약 §2.3.6 필드 순서)을 정해진 순서로 돌려준다."""
    rows = []
    for path in paths:
        with open(path, encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            fields = reader.fieldnames or []
            if sorted(fields) != sorted(types.PEER_GROUP_KEYS) or len(fields) != len(set(fields)):
                raise BuildError(f"비교국 표 {Path(path).name}: 열이 계약 §2.3.6 필드 17개와 다르다")
            for number, record in enumerate(reader, start=2):
                where = f"{Path(path).name}:{number}"
                row = [_peer_value(col, record[col], where) for col in types.PEER_GROUP_KEYS]
                values = dict(zip(types.PEER_GROUP_KEYS, row))
                if values["entity_type"] != types.PEER_ENTITY_TYPE or values["entity_namespace"] != types.PARTNER_NAMESPACE:
                    raise BuildError(f"{where}: entity_type·entity_namespace가 계약 값이 아니다")
                digits = {"hs2": 2, "hs4": 4, "hs6": 6}.get(values["scope_type"])
                if digits is None or not re.fullmatch(r"[0-9]{%d}" % digits, values["scope_id"]):
                    raise BuildError(f"{where}: scope_type·scope_id가 hs2·hs4·hs6와 그 자릿수 코드가 아니다")
                rows.append(row)
    order = [types.PEER_GROUP_KEYS.index(k) for k in ("grouping_version", "entity_type", "entity_id", "scope_type",
                                                      "scope_id", "peer_rank", "peer_id")]
    return sorted(rows, key=lambda r: tuple(r[i] for i in order))


def peer_not_collected_rows(snapshot_id: str, config: dict, peer_rows: list[list]) -> list[list]:
    """비교국이 수집 계획 밖이면, 그 국가의 부모 HS6 행(HS4 스캔)과 HS10 행(HS6 조회)을 맡았을 요청의 `NOT_COLLECTED` 행."""
    partners = set(config.get("partners", []))
    period = config["period"]
    chunks = ingest.year_chunks(period["start"], period["end"], config.get("chunk_months", 12))
    at = {k: types.PEER_GROUP_KEYS.index(k) for k in ("entity_id", "peer_id", "scope_type", "scope_id")}
    needed: set[tuple] = set()  # (국가, 요청 코드, 구간 시작, 구간 끝)
    for row in peer_rows:
        entity, peer = row[at["entity_id"]], row[at["peer_id"]]
        if entity not in partners:
            raise BuildError(f"비교국 표의 대상국 {entity}가 수집 계획의 상대국이 아니다")
        if peer in partners or peer == types.ALL_PARTNER:
            continue
        digits = len(row[at["scope_id"]])
        for hs6 in config.get("hs6", []):
            if hs6[:digits] != row[at["scope_id"]]:
                continue
            for code in (hs6[:4], hs6):
                for start, end in chunks:
                    needed.add((peer, code, start, end))
    rows: list[list] = []
    for peer, code, start, end in sorted(needed):  # 국가·코드·구간 순. 요청마다 계획 행과 같은 상태 행 순서
        params = {"strtYymm": start, "endYymm": end, "hsSgn": code, "cntyCd": peer}
        rows += _status_rows(snapshot_id, ingest.request_id("nitemtrade", params), peer, code,
                             ingest.months_between(start, end), types.NOT_COLLECTED, None)
    return rows


# ----------------------------------------------------------------------------- 메타와 쓰기
def _json_text(value: object) -> str:
    def reject(obj: object) -> object:
        raise BuildError(f"메타 값에 JSON으로 적을 수 없는 형식이 있다({type(obj).__name__})")

    if _has_float(value):
        raise BuildError("메타 값에 소수(float)가 있다")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=reject)


def _has_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, (list, tuple)):
        return any(_has_float(v) for v in value)
    if isinstance(value, dict):
        return any(_has_float(v) for v in value.values())
    return False


def snapshot_object(snapshot_id: str, source: dict, rows: list[list], raw_sha256: str) -> dict:
    """계약 `snapshot` 객체(§2.3.1)에서 `normalized_sha256`을 뺀 값과 `schema_version`."""
    meta = source["collector_meta"]
    config = source["manifest"]["config"]
    required = ("source_kind", "last_collect_at", "importer", "valuation_basis", "units", "precision_rule",
                "coverage_status")
    missing = [k for k in required if not meta.get(k)]
    if missing:
        raise BuildError(f"수집기 스냅샷 메타에 값이 없다({', '.join(missing)})")
    if meta.get("snapshot_id") != snapshot_id:
        raise BuildError(f"수집기 스냅샷 메타의 snapshot_id가 {snapshot_id}가 아니다")
    if meta["source_kind"] not in types.SOURCE_KINDS:
        raise BuildError("수집기 스냅샷 메타의 source_kind가 real·controlled가 아니다")
    period = config.get("period") or {}
    if not (isinstance(period.get("start"), str) and isinstance(period.get("end"), str)):
        raise BuildError("수집 설정에 period.start·period.end가 없다")
    # 기간은 manifest의 수집 설정(config.period)을 정본으로 쓴다. 수집기 open_snapshot은 메타의 period_start·period_end를
    # 설정과 관계없이 202201·202412로 적으므로(ingest.py) 대조하지 않는다.
    hs_versions = {row[_COL["hs_version"]] for row in rows}
    if len(hs_versions) != 1:
        raise BuildError("관측 행의 hs_version이 하나가 아니다")
    try:
        valuation, units = json.loads(meta["valuation_basis"]), json.loads(meta["units"])
    except ValueError as exc:
        raise BuildError("수집기 스냅샷 메타의 valuation_basis·units가 JSON이 아니다") from exc
    if "source_url" in meta:
        source_url = json.loads(meta["source_url"])
    else:
        endpoints = {request["endpoint"] for request in source["manifest"]["requests"]}
        source_url = sorted(ingest.ENDPOINTS[e]["source_url"] for e in endpoints)
    return {
        "schema_version": types.SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "source_kind": meta["source_kind"],
        "collected_at": meta["last_collect_at"],
        "source_url": source_url,
        "collection_plan": config,
        "raw_sha256": raw_sha256,
        "period": {"start": period["start"], "end": period["end"]},
        "hs_version": hs_versions.pop(),
        "importer": meta["importer"],
        "valuation_basis": valuation,
        "units": units,
        "precision_rule": meta["precision_rule"],
        "coverage_status": meta["coverage_status"],
    }


def _cleanup(path: Path) -> None:
    for suffix in ("", "-journal", "-wal", "-shm"):
        candidate = Path(str(path) + suffix)
        if candidate.exists():
            candidate.unlink()


def write_snapshot_db(path: Path, *, meta: dict, receipts: list[dict], observations: list[list],
                      peer_groups: list[list]) -> None:
    """파생 SQLite를 새 파일로 쓴다. 파일이 이미 있으면 FileExistsError(덮어쓰지 않는다). 행은 받은 순서로 넣는다.

    합성 스냅샷 생성(단위 S4)과 시험도 이 함수로 같은 모양의 스냅샷을 만든다. meta는 `snapshot_object`의 모양이다.
    """
    path = Path(path)
    with open(path, "xb"):
        pass  # 이름을 먼저 잡는다(이미 있으면 실패). 빈 파일은 SQLite가 새 데이터베이스로 연다
    con = None
    try:
        con = sqlite3.connect(path, isolation_level=None)
        mode = con.execute("PRAGMA journal_mode = DELETE").fetchone()[0]
        if mode != "delete":
            raise BuildError(f"저널 모드를 DELETE로 두지 못했다({mode})")
        con.executescript(DDL)
        con.execute("BEGIN")
        con.executemany("INSERT INTO snapshot_meta(key, value) VALUES(?, ?)",
                        [(key, _json_text(meta[key])) for key in sorted(meta)])
        con.executemany(f"INSERT INTO collection_receipt VALUES({', '.join('?' * len(types.COLLECTION_RECEIPT_COLUMNS))})",
                        [tuple(r[c] for c in types.COLLECTION_RECEIPT_COLUMNS) for r in receipts])
        con.executemany(f"INSERT INTO observation VALUES({', '.join('?' * len(types.OBSERVATION_COLUMNS))})",
                        [tuple(row) for row in observations])
        con.executemany(f"INSERT INTO peer_group VALUES({', '.join('?' * len(types.PEER_GROUP_KEYS))})",
                        [tuple(row) for row in peer_groups])
        con.execute("COMMIT")
        con.close()
        con = None
    except sqlite3.IntegrityError as exc:
        _close_and_cleanup(con, path)
        raise BuildError(f"행 키가 겹친다({exc.__class__.__name__})") from exc
    except BaseException:
        _close_and_cleanup(con, path)
        raise
    leftovers = [s for s in ("-journal", "-wal", "-shm") if Path(str(path) + s).exists()]
    if leftovers:
        raise BuildError(f"SQLite 부속 파일이 남았다({', '.join(leftovers)})")


def _close_and_cleanup(con: sqlite3.Connection | None, path: Path) -> None:
    if con is not None:
        con.close()
    _cleanup(path)


def normalized_sha256(con: sqlite3.Connection) -> str:
    """스냅샷 SQLite의 정규화 해시(머리 설명의 직렬화). 표가 없거나 REAL·BLOB 값이 있으면 BuildError."""
    digest = hashlib.sha256()

    def line(value: list) -> bytes:
        return (json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")

    for table in HASH_TABLES:
        columns = [row[1] for row in con.execute(f'PRAGMA table_info("{table}")')]
        if not columns:
            raise BuildError(f"표가 없다: {table}")
        digest.update(line(["table", table, columns]))
        select = ", ".join(f'"{c}"' for c in columns)
        for row in con.execute(f'SELECT rowid, {select} FROM "{table}" ORDER BY rowid'):
            for value in row:
                if value is not None and not isinstance(value, (int, str)):
                    raise BuildError(f"{table} 표에 정수·문자열·NULL이 아닌 값이 있다({type(value).__name__})")
            digest.update(line(list(row)))
    return digest.hexdigest()


def file_normalized_sha256(path: Path) -> str:
    """SQLite 파일을 읽기 전용으로 열어 정규화 해시를 구한다."""
    con = open_read_only(path)
    try:
        return normalized_sha256(con)
    finally:
        con.close()


# ----------------------------------------------------------------------------- 빌드
def assemble(snapshot_id: str, source_dir: Path, policy: dict | None, peer_group_files: list[Path]) -> dict:
    """입력을 읽어 파생 SQLite에 넣을 내용을 만든다(파일은 쓰지 않는다)."""
    snapshot_id = _check_snapshot_id(snapshot_id)
    source = read_source(source_dir, snapshot_id)
    requests = source["manifest"]["requests"]
    rows, receipts = plan_rows(snapshot_id, requests, source["receipts"], source["raw_dir"])
    raw_sha256, raw_files = raw_combined_sha256(source["raw_dir"])
    ok_files = {r["raw_file_id"] for r in receipts if r["status"] == "OK"}
    present = {p.name for p in Path(source["raw_dir"]).glob("*.xml") if p.is_file()}
    if present != ok_files:
        raise BuildError(f"raw 폴더의 xml 파일({len(present)})이 OK 수신 기록의 raw 파일({len(ok_files)})과 다르다")
    record = source["hash_record"]
    if record is not None and (record.get("raw_combined_sha256") != raw_sha256
                               or record.get("raw_files", raw_files) != raw_files):
        raise BuildError(f"raw 결합 해시가 {HASH_FILE}의 기록과 다르다")
    peers = load_peer_groups(list(peer_group_files))
    rows += peer_not_collected_rows(snapshot_id, source["manifest"]["config"], peers)
    rule = None if policy is None else policy["confirmed_no_trade"]
    promoted = apply_promotion(rows, rule)
    meta = snapshot_object(snapshot_id, source, rows, raw_sha256)
    return {"meta": meta, "receipts": receipts, "observations": rows, "peer_groups": peers,
            "policy_version": None if policy is None else policy["policy_version"],
            "confirmed_no_trade_rule": None if rule is None else rule["rule"], "confirmed_no_trade_rows": promoted,
            "peer_group_files": [{"file_name": Path(p).name, "sha256": hashlib.sha256(Path(p).read_bytes()).hexdigest()}
                                 for p in peer_group_files]}


def build_to(db_path: Path, snapshot_id: str, *, source_dir: Path | None = None, policy: dict | None = None,
             peer_group_files: list[Path] | tuple = ()) -> dict:
    """파생 SQLite를 db_path에 새로 만들고 빌드 기록(dict)을 돌려준다. policy는 단위 K4의 정책 객체다."""
    source_dir = SNAPSHOTS_ROOT / _check_snapshot_id(snapshot_id) if source_dir is None else Path(source_dir)
    content = assemble(snapshot_id, source_dir, policy, list(peer_group_files))
    write_snapshot_db(db_path, meta=content["meta"], receipts=content["receipts"],
                      observations=content["observations"], peer_groups=content["peer_groups"])
    counts = {"collection_receipt": len(content["receipts"]), "observation": len(content["observations"]),
              "peer_group": len(content["peer_groups"]), "snapshot_meta": len(content["meta"])}
    return {"schema_version": types.SCHEMA_VERSION, "snapshot_id": snapshot_id,
            "normalized_sha256": file_normalized_sha256(db_path), "raw_sha256": content["meta"]["raw_sha256"],
            "policy_version": content["policy_version"], "confirmed_no_trade_rule": content["confirmed_no_trade_rule"],
            "confirmed_no_trade_rows": content["confirmed_no_trade_rows"],
            "peer_group_files": content["peer_group_files"], "row_counts": counts,
            "build_file": Path(db_path).name, "built_at": datetime.now(types.KST).isoformat(timespec="seconds")}


def _write_json_exclusive(path: Path, value: dict) -> None:
    with open(path, "x", encoding="utf-8") as fh:
        fh.write(json.dumps(value, ensure_ascii=False, indent=1) + "\n")


def build_snapshot(snapshot_id: str, *, out_dir: Path, stamp: str, source_dir: Path | None = None,
                   policy: dict | None = None, peer_group_files: list[Path] | tuple = ()) -> dict:
    """확보한 실행 폴더 out_dir에 `snapshot_build-{stamp}.sqlite`와 빌드 기록 `snapshot_build-{stamp}.json`을 쓴다.

    두 파일 중 하나라도 이미 있으면 쓰지 않는다. 빌드 기록 dict를 돌려준다. 실행명 확보(N8)는 부르는 쪽이 한다.
    """
    if not isinstance(stamp, str) or not STAMP_RE.fullmatch(stamp):
        raise BuildError("stamp는 yymmddhhmmss 12자리다")
    out_dir = Path(out_dir)
    db_path, record_path = out_dir / f"{DOMAIN}-{stamp}.sqlite", out_dir / f"{DOMAIN}-{stamp}.json"
    if record_path.exists():
        raise FileExistsError(f"{record_path.name}이 이미 있다")
    record = build_to(db_path, snapshot_id, source_dir=source_dir, policy=policy, peer_group_files=peer_group_files)
    try:
        _write_json_exclusive(record_path, record)
    except BaseException:
        _cleanup(db_path)
        raise
    return record


def install_build(build_file: Path, snapshot_dir: Path) -> dict:
    """빌드 파일을 정본 자리(`snapshot_dir/snapshot_build.sqlite`)와 기록(`snapshot_build.json`)으로 옮긴다(DT7 ②).

    옆의 빌드 기록(같은 이름 `.json`)의 normalized_sha256이 빌드 파일에서 다시 구한 값과 같아야 한다. 정본 자리에 두
    파일 중 하나라도 있으면 FileExistsError. 옮기기는 os.link 뒤 원본 삭제이고, 다른 파일 시스템이면 "xb" 복사다.
    옮기기 전에 단위 S3(`snapshot-verify`)로 빌드를 검증한다(부르는 쪽의 절차).
    """
    build_file, snapshot_dir = Path(build_file), Path(snapshot_dir)
    record = json.loads(build_file.with_suffix(".json").read_text(encoding="utf-8"))
    if record.get("snapshot_id") != snapshot_dir.name:
        raise BuildError("빌드 기록의 snapshot_id가 옮길 스냅샷 폴더 이름과 다르다")
    if file_normalized_sha256(build_file) != record.get("normalized_sha256"):
        raise BuildError("빌드 파일의 normalized_sha256이 빌드 기록과 다르다")
    target, target_record = snapshot_dir / BUILD_FILE, snapshot_dir / BUILD_RECORD
    for path in (target, target_record):
        if path.exists():
            raise FileExistsError(f"정본 자리에 {path.name}이 이미 있다. 덮어쓰지 않는다")
    linked = True
    try:
        os.link(build_file, target)
    except OSError as exc:
        if exc.errno != errno.EXDEV:
            raise
        linked = False
        with open(build_file, "rb") as src, open(target, "xb") as dst:
            while chunk := src.read(1 << 20):
                dst.write(chunk)
            dst.flush()
            os.fsync(dst.fileno())
    try:
        if file_normalized_sha256(target) != record["normalized_sha256"]:
            raise BuildError("옮긴 파일의 normalized_sha256이 빌드 기록과 다르다")
        installed = {**record, "build_file": BUILD_FILE, "installed_from": build_file.name,
                     "installed_at": datetime.now(types.KST).isoformat(timespec="seconds")}
        _write_json_exclusive(target_record, installed)
    except BaseException:
        target.unlink()
        raise
    if linked:
        build_file.unlink()
    return installed


def run(inp: object) -> object:
    """진입 함수. 입력 {"snapshot_id", "source_dir"?, "policy_version"? 또는 "policy"?, "peer_group_files"?} →
    파생 SQLite 파일의 바이트(공통 실행기가 `snapshot_build-{시각}.sqlite`로 쓴다).

    source_dir가 없으면 `data/snapshots/{snapshot_id}/`를 읽는다. peer_group_files의 상대경로는 저장소 루트 기준이다.
    policy_version(예: dev-0.1)은 단위 K4로 읽고, policy는 정책 문서 자체다. 둘 다 없으면 승격하지 않는다.
    """
    if not isinstance(inp, dict) or "snapshot_id" not in inp:
        raise ValueError("입력은 snapshot_id를 담은 객체다")
    unknown = set(inp) - {"snapshot_id", "source_dir", "policy_version", "policy", "peer_group_files"}
    if unknown or ("policy_version" in inp and "policy" in inp):
        raise ValueError("입력 키는 snapshot_id, source_dir, policy_version 또는 policy, peer_group_files다")
    policy = None
    if inp.get("policy_version") is not None:
        policy = load_policy(inp["policy_version"])
    elif inp.get("policy") is not None:
        policy = parse_policy(inp["policy"])
    source_dir = inp.get("source_dir")
    files = [path if path.is_absolute() else REPO_ROOT / path for path in map(Path, inp.get("peer_group_files") or [])]
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / f"{DOMAIN}.sqlite"
        build_to(db_path, inp["snapshot_id"], source_dir=None if source_dir is None else Path(source_dir),
                 policy=policy, peer_group_files=files)
        return db_path.read_bytes()
