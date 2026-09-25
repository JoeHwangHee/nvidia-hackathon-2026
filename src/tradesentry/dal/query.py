"""단위 K3 읽기 전용 조회.

단위 ID: K3
도메인명: dal_query
소유: D
입력: `snapshot_id` + 허용 scope
출력: 계약 객체(빠진 자료는 관측 상태 코드)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal

자료 접근층(DAL). 도구(M)·지표(D)·판정 정책(M)은 스냅샷을 이 단위로만 읽는다(병렬 개발 규칙 §2.4). 정본: 자료 계약
docs/rules/DATA_CONTRACT_V1.md §2.3.2 행 규칙, §3.4, §4.4, §5.1.

여는 법
- `open_snapshot(snapshot_id)`은 정본 빌드 `data/snapshots/{snapshot_id}/snapshot_build.sqlite`(단위 S2가 만들고 승인·동결
  뒤 옮긴 파일)를 읽기 전용 URI(`mode=ro`)로 열고 `query_only`를 켠다. `path=`를 주면 그 파일(예: 승인 전 개발 빌드
  `outputs/snapshot_build-{시각}/snapshot_build-{시각}.sqlite`)을 연다. 어느 쪽이든 파일 안 메타의 `snapshot_id`가 부른
  이름과 같고 `schema_version`이 계약 버전(`types.SCHEMA_VERSION`)이어야 연다(수집기의 `snapshot.sqlite`는 이 메타가 없어 열지 않는다).
- 파일 경로는 모델에게서 받지 않는다(§5.1). `path=`는 호출하는 코드(CLI 처리 함수·시험)만 준다.

행 규칙(§2.3.2)
- 수입 흐름(`import`)만 쓴다(규칙 2). 총계 행(`RAW:총계`)은 값과 근거에 쓰지 않는다(규칙 3).
- 상대국 월 값은 부모 HS6 행: HS4 스캔 요청(`nitemtrade`, `hsSgn`=HS6 앞 4자리)이 돌려준 HS6 행(규칙 4).
- 부모 행이 없는 달은 값이 null이고, 그 달을 맡은 요청(HS4 스캔, HS6 조회)이 남긴 상태 행을 `missingness`로 돌려준다.
  그 상태 행이 모두 `CONFIRMED_NO_TRADE`(승격된 행)면 빠진 자료가 아니라 무거래 확정이다. V·Q 칸은 null 그대로 두고
  `observation_status`로 알린다(0으로 다루는 일은 지표 단위가 한다, §3.4).
- 부모 행이 있으면 같은 달의 HS6 자릿수 상태 행은 HS10 하위 자료가 빠졌다는 뜻이라 `children()`의 `missingness`로만 준다.
- 전체국가(`ALL`) 월 값은 그 HS6 아래 `ALL` HS10 월 행의 금액 합이다(규칙 5). 같은 (HS10, 월)이 두 요청에 있으면 요청
  코드가 가장 긴 요청의 행 하나, 그래도 둘 이상이면 `request_id` 사전순 첫 행을 쓴다(규칙 6). 두 값이 다르면
  SnapshotError다(조용히 고르지 않는다).
- 분석 범위(규칙 7): 수집 설정의 HS6와 상대국(비교국 표가 가리키는 계획 밖 국가 포함), 수집 기간의 달만 조회한다.
  범위 밖이면 ScopeError다.

돌려주는 값(모두 dict·list, 수는 int, 소수는 Decimal)
- 월 값(`parent`, `world`): {"hs6", "partner", "month", "amount_usd", "net_weight_kg", "observation_status",
  "evidence_ids", "missingness"}. `world`는 "net_weight_kg" 대신 "hs10_codes"(더한 HS10 코드)를 준다.
  값이 있으면 `observation_status`는 `OBSERVED`(`world`도 같다), 무거래 확정이면 `CONFIRMED_NO_TRADE`(근거는 그 상태 행),
  빠졌으면 `missingness` 첫 항목의 상태다. `missingness` 순서는 값의 원천 요청이 먼저다(`parent`는 HS4 스캔, `world`는
  HS6 조회), 그다음 rowid 순이다.
- `missingness` 항목: {"evidence_id", "request_id", "partner_code", "hs_code", "month", "flow", "observation_status"}.
- HS10 하위(`children`): {"hs6", "partner", "month", "rows": [{"hs10", "amount_usd", "net_weight_kg", "evidence_id"}…],
  "observation_status", "missingness"}. 행은 HS6 조회(`hsSgn`=HS6)가 돌려준 HS10 행만, HS10 코드 순이다.
- 비교국(`peers`): 계약 §2.3.6 필드 17개 + "evidence_id". 가장 좁은 범위(hs6 → hs4 → hs2)에 행이 있는 것만, 순위 순.
- 근거 ID 풀기(`resolve`): 단위 K2의 풀림 규칙 판정 + "row"(풀리면 그 행의 열 값).
"""
import json
import re
import sqlite3
from decimal import Decimal
from pathlib import Path

from tradesentry.contract import types
from tradesentry.contract.evidence_id import format_evidence_id, resolve_evidence_id

REPO_ROOT = Path(__file__).resolve().parents[3]
SNAPSHOTS_ROOT = REPO_ROOT / "data" / "snapshots"
BUILD_FILE = "snapshot_build.sqlite"  # 정본 빌드 파일(결정 기록 20260924-2212 스냅샷 빌드)
SNAPSHOT_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")
_OBS = "rowid, request_id, month, partner_code, hs_code, hs_level, amount_usd, net_weight_kg, observation_status"


class SnapshotError(Exception):
    """스냅샷을 열 수 없거나 스냅샷 안의 자료가 행 규칙에 맞지 않는다."""


class ScopeError(ValueError):
    """조회가 스냅샷의 분석 범위(HS6·상대국·달) 밖이다."""


def snapshot_path(snapshot_id: str) -> Path:
    """정본 빌드 파일 경로 `data/snapshots/{snapshot_id}/snapshot_build.sqlite`."""
    if not isinstance(snapshot_id, str) or not SNAPSHOT_ID_RE.fullmatch(snapshot_id):
        raise SnapshotError("snapshot_id는 영문·숫자로 시작하고 영문·숫자·밑줄·하이픈만 쓴다")
    return SNAPSHOTS_ROOT / snapshot_id / BUILD_FILE


def open_snapshot(snapshot_id: str, *, path: str | Path | None = None) -> "Snapshot":
    """스냅샷을 읽기 전용으로 연다. path가 없으면 정본 빌드 파일을 연다."""
    return Snapshot(snapshot_id, snapshot_path(snapshot_id) if path is None else Path(path))


class Snapshot:
    """읽기 전용 스냅샷. `with open_snapshot(...) as snap:`처럼 쓰고 끝나면 닫는다."""

    def __init__(self, snapshot_id: str, path: Path) -> None:
        if not isinstance(snapshot_id, str) or not SNAPSHOT_ID_RE.fullmatch(snapshot_id):
            raise SnapshotError("snapshot_id 형식이 맞지 않다")
        if not path.is_file():
            raise SnapshotError(f"스냅샷 빌드 파일이 없다({path.name})")
        self.snapshot_id = snapshot_id
        self.path = path
        self._con = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            self._con.execute("PRAGMA query_only = ON")
            self._tables = {name for (name,) in self._con.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")}
            if not {"snapshot_meta", "observation", "collection_receipt", "peer_group"} <= self._tables:
                raise SnapshotError("스냅샷 빌드 파일이 아니다(표 snapshot_meta·observation·collection_receipt·peer_group)")
            self.meta = {key: json.loads(value) for key, value in self._con.execute("SELECT key, value FROM snapshot_meta")}
            if self.meta.get("schema_version") != types.SCHEMA_VERSION or self.meta.get("snapshot_id") != snapshot_id:
                raise SnapshotError(f"메타의 schema_version이 {types.SCHEMA_VERSION}가 아니거나 snapshot_id가 {snapshot_id}가 아니다")
            plan = self.meta.get("collection_plan") or {}
            period = self.meta["period"]
            self.hs6_codes = tuple(plan.get("hs6", []))
            self.partners = tuple(plan.get("partners", []))
            self.months = tuple(_months_between(period["start"], period["end"]))
            self._requests = {rid: (endpoint, json.loads(params)) for rid, endpoint, params in self._con.execute(
                "SELECT request_id, endpoint, params_json FROM collection_receipt")}
            self._peer_ids = {peer for (peer,) in self._con.execute("SELECT DISTINCT peer_id FROM peer_group")}
        except BaseException:
            self._con.close()
            raise

    # ------------------------------------------------------------------ 기본
    def close(self) -> None:
        self._con.close()

    def __enter__(self) -> "Snapshot":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    @property
    def source_kind(self) -> str:
        return self.meta["source_kind"]

    def evidence_id(self, table: str, rowid: int) -> str:
        return format_evidence_id(self.snapshot_id, table, rowid)

    def snapshot_object(self) -> dict:
        """계약 `snapshot` 객체(§2.3.1)와 `schema_version`. `normalized_sha256`은 빌드 파일 옆 기록(같은 이름의 .json)의
        기록값이고, 없으면 null이다. 기록값과 파일의 대조는 단위 S3(`snapshot-verify`)가 한다."""
        recorded = None
        record_path = self.path.with_suffix(".json")
        if record_path.is_file():
            recorded = json.loads(record_path.read_text(encoding="utf-8")).get("normalized_sha256")
        obj = {key: self.meta.get(key) for key in types.SNAPSHOT_KEYS}
        obj["normalized_sha256"] = recorded
        return {"schema_version": self.meta["schema_version"], **obj}

    def scope(self) -> dict:
        """분석 범위: 수집 설정의 HS6·상대국과 수집 기간의 달(규칙 7). 비교국 표의 계획 밖 국가는 `other_partners`."""
        return {"hs6": list(self.hs6_codes), "partners": list(self.partners), "months": list(self.months),
                "other_partners": sorted(self._peer_ids - set(self.partners) - {types.ALL_PARTNER})}

    # ------------------------------------------------------------------ 범위 검사
    def _check_hs6(self, hs6: str) -> str:
        if hs6 not in self.hs6_codes:
            raise ScopeError(f"분석 범위 밖 HS6다: {hs6!r}")
        return hs6

    def _check_partner(self, partner: str) -> str:
        if partner not in self.partners and partner not in self._peer_ids or partner == types.ALL_PARTNER:
            raise ScopeError(f"분석 범위 밖 상대국이다: {partner!r}")
        return partner

    def _check_months(self, months) -> list[str]:
        months = list(self.months if months is None else months)
        for month in months:
            if month not in self.months:
                raise ScopeError(f"스냅샷 기간 밖 달이다: {month!r}")
        return months

    # ------------------------------------------------------------------ 행 읽기
    def _rows(self, where: str, params: tuple) -> list[dict]:
        names = [n.strip() for n in _OBS.split(",")]
        return [dict(zip(names, row)) for row in self._con.execute(
            f"SELECT {_OBS} FROM observation WHERE flow = 'import' AND {where} ORDER BY rowid", params)]

    def _missing_entry(self, row: dict) -> dict:
        return {"evidence_id": self.evidence_id("observation", row["rowid"]), "request_id": row["request_id"],
                "partner_code": row["partner_code"], "hs_code": row["hs_code"], "month": row["month"],
                "flow": types.METRIC_FLOW, "observation_status": row["observation_status"]}

    def _request_code(self, request_id: str) -> tuple[str, str] | None:
        found = self._requests.get(request_id)
        return None if found is None else (found[0], found[1].get("hsSgn", ""))

    def _missing_value(self, base: dict, status_rows: list[dict]) -> dict:
        if not status_rows:
            raise SnapshotError(f"범위 안 키에 값 행도 상태 행도 없다({base['partner']}·{base['hs6']}·{base['month']})")
        if all(row["observation_status"] == types.CONFIRMED_NO_TRADE for row in status_rows):
            return {**base, "observation_status": types.CONFIRMED_NO_TRADE,
                    "evidence_ids": [self.evidence_id("observation", row["rowid"]) for row in status_rows],
                    "missingness": []}
        entries = [self._missing_entry(row) for row in status_rows]
        return {**base, "observation_status": entries[0]["observation_status"], "evidence_ids": [],
                "missingness": entries}

    # ------------------------------------------------------------------ 상대국 부모 HS6 값
    def parent_series(self, hs6: str, partner: str, months=None) -> list[dict]:
        """상대국 HS6의 달별 값(부모 HS6 행). months가 없으면 수집 기간 전체."""
        self._check_hs6(hs6)
        self._check_partner(partner)
        months = self._check_months(months)
        hs4 = hs6[:4]
        rows = self._rows("partner_code = ? AND hs_code IN (?, ?)", (partner, hs6, hs4))
        out = []
        for month in months:
            here = [r for r in rows if r["month"] == month]
            parents = [r for r in here if r["observation_status"] == types.OBSERVED and r["hs_code"] == hs6
                       and r["hs_level"] == 6 and self._request_code(r["request_id"]) == ("nitemtrade", hs4)]
            base = {"hs6": hs6, "partner": partner, "month": month}
            if len(parents) > 1:
                raise SnapshotError(f"부모 HS6 행이 둘 이상이다({partner}·{hs6}·{month})")
            if parents:
                row = parents[0]
                if not isinstance(row["amount_usd"], int) or not isinstance(row["net_weight_kg"], int):
                    raise SnapshotError(f"부모 HS6 행의 금액·중량이 정수가 아니다({partner}·{hs6}·{month})")
                out.append({**base, "amount_usd": row["amount_usd"], "net_weight_kg": row["net_weight_kg"],
                            "observation_status": types.OBSERVED,
                            "evidence_ids": [self.evidence_id("observation", row["rowid"])], "missingness": []})
                continue
            status = [r for r in here if r["observation_status"] != types.OBSERVED]
            status.sort(key=lambda r: (r["hs_code"] != hs4, r["rowid"]))  # 원천 요청(HS4 스캔) 먼저
            out.append(self._missing_value({**base, "amount_usd": None, "net_weight_kg": None}, status))
        return out

    def parent(self, hs6: str, partner: str, month: str) -> dict:
        """상대국 HS6의 한 달 값(부모 HS6 행)."""
        return self.parent_series(hs6, partner, [month])[0]

    # ------------------------------------------------------------------ 전체국가 분모
    def world_series(self, hs6: str, months=None) -> list[dict]:
        """전체국가(`ALL`) HS6의 달별 금액(중복 제거한 HS10 월 행의 합). months가 없으면 수집 기간 전체."""
        self._check_hs6(hs6)
        months = self._check_months(months)
        hs4 = hs6[:4]
        values = self._rows("partner_code = ? AND hs_level = 10 AND substr(hs_code, 1, 6) = ? AND observation_status = ?",
                            (types.ALL_PARTNER, hs6, types.OBSERVED))
        status_rows = self._rows("partner_code = ? AND hs_code IN (?, ?) AND observation_status != ?",
                                 (types.ALL_PARTNER, hs6, hs4, types.OBSERVED))
        out = []
        for month in months:
            chosen: dict[str, dict] = {}
            for row in (r for r in values if r["month"] == month):
                code = self._request_code(row["request_id"])
                key = (-len(code[1]) if code else 0, row["request_id"])
                current = chosen.get(row["hs_code"])
                if current is not None and (current["amount_usd"], current["net_weight_kg"]) != \
                        (row["amount_usd"], row["net_weight_kg"]):
                    raise SnapshotError(f"ALL 중복 행의 값이 다르다({row['hs_code']}·{month}). 행 규칙 6")
                if current is None or key < current["_key"]:
                    chosen[row["hs_code"]] = {**row, "_key": key}
            base = {"hs6": hs6, "partner": types.ALL_PARTNER, "month": month}
            if chosen:
                codes = sorted(chosen)
                amounts = [chosen[c]["amount_usd"] for c in codes]
                if not all(isinstance(a, int) for a in amounts):
                    raise SnapshotError(f"ALL HS10 행의 금액이 정수가 아니다({hs6}·{month})")
                out.append({**base, "amount_usd": sum(amounts), "observation_status": types.OBSERVED,
                            "evidence_ids": [self.evidence_id("observation", chosen[c]["rowid"]) for c in codes],
                            "missingness": [], "hs10_codes": codes})
                continue
            status = [r for r in status_rows if r["month"] == month]
            status.sort(key=lambda r: (r["hs_code"] != hs6, r["rowid"]))  # 원천 요청(HS6 조회, 규칙 6) 먼저
            missing = self._missing_value({**base, "amount_usd": None}, status)
            out.append({**missing, "hs10_codes": []})
        return out

    def world(self, hs6: str, month: str) -> dict:
        """전체국가(`ALL`) HS6의 한 달 금액."""
        return self.world_series(hs6, [month])[0]

    # ------------------------------------------------------------------ HS10 하위
    def children(self, hs6: str, partner: str, month: str) -> dict:
        """상대국 HS6 아래 HS10 행(HS6 조회가 돌려준 행)과 그 달 HS6 조회의 상태."""
        self._check_hs6(hs6)
        self._check_partner(partner)
        self._check_months([month])
        rows = self._rows("partner_code = ? AND month = ? AND hs_level = 10 AND substr(hs_code, 1, 6) = ? "
                          "AND observation_status = ?", (partner, month, hs6, types.OBSERVED))
        rows = [r for r in rows if self._request_code(r["request_id"]) == ("nitemtrade", hs6)]
        if len({r["hs_code"] for r in rows}) != len(rows):
            raise SnapshotError(f"HS10 하위 행이 겹친다({partner}·{hs6}·{month})")
        status = self._rows("partner_code = ? AND month = ? AND hs_code = ? AND observation_status != ?",
                            (partner, month, hs6, types.OBSERVED))
        base = {"hs6": hs6, "partner": partner, "month": month}
        if rows:
            items = [{"hs10": r["hs_code"], "amount_usd": r["amount_usd"], "net_weight_kg": r["net_weight_kg"],
                      "evidence_id": self.evidence_id("observation", r["rowid"])}
                     for r in sorted(rows, key=lambda r: r["hs_code"])]
            return {**base, "rows": items, "observation_status": types.OBSERVED,
                    "missingness": [self._missing_entry(r) for r in status]}
        if not status:
            raise SnapshotError(f"HS10 하위에 값 행도 상태 행도 없다({partner}·{hs6}·{month})")
        if all(r["observation_status"] == types.CONFIRMED_NO_TRADE for r in status):
            return {**base, "rows": [], "observation_status": types.CONFIRMED_NO_TRADE, "missingness": []}
        entries = [self._missing_entry(r) for r in status]
        return {**base, "rows": [], "observation_status": entries[0]["observation_status"], "missingness": entries}

    # ------------------------------------------------------------------ 비교국
    def peers(self, hs6: str, partner: str, grouping_version: str) -> list[dict]:
        """대상국의 비교국 행(계약 §2.3.6). 가장 좁은 범위에 행이 있는 것만, 순위 순."""
        self._check_hs6(hs6)
        self._check_partner(partner)
        columns = ", ".join(types.PEER_GROUP_KEYS)
        for scope_type, scope_id in (("hs6", hs6), ("hs4", hs6[:4]), ("hs2", hs6[:2])):
            found = self._con.execute(
                f"SELECT rowid, {columns} FROM peer_group WHERE entity_id = ? AND grouping_version = ? "
                "AND scope_type = ? AND scope_id = ? ORDER BY peer_rank, rowid",
                (partner, grouping_version, scope_type, scope_id)).fetchall()
            if found:
                out = []
                for rowid, *values in found:
                    row = dict(zip(types.PEER_GROUP_KEYS, values))
                    if row["similarity"] is not None:
                        row["similarity"] = Decimal(row["similarity"])
                    out.append({**row, "evidence_id": self.evidence_id("peer_group", rowid)})
                return out
        return []

    # ------------------------------------------------------------------ 근거 ID
    def has_table(self, table: str) -> bool:
        return table in self._tables

    def row(self, table: str, rowid: int) -> dict | None:
        """표 이름과 rowid로 행 하나(열 이름 → 값). 표가 없으면 SnapshotError, 행이 없으면 None."""
        if table not in self._tables:
            raise SnapshotError(f"스냅샷에 없는 표다: {table!r}")
        if isinstance(rowid, bool) or not isinstance(rowid, int) or not 0 < rowid <= 2 ** 63 - 1:
            return None
        cursor = self._con.execute(f'SELECT * FROM "{table}" WHERE rowid = ?', (rowid,))
        found = cursor.fetchone()
        if found is None:
            return None
        return dict(zip([d[0] for d in cursor.description], found))

    def resolve(self, evidence_id: object) -> dict:
        """근거 ID를 풀림 규칙 1~4(§4.4)로 푼다. {"evidence_id", "resolved", "failed_rule", "row"}."""
        result = resolve_evidence_id(evidence_id, self.snapshot_id, has_table=self.has_table,
                                     has_row=lambda table, rowid: self.row(table, rowid) is not None)
        row = None
        if result["resolved"]:
            _, _, table, rowid = str(evidence_id).split(":")
            row = self.row(table, int(rowid))
        return {**result, "row": row}


def _months_between(start: str, end: str) -> list[str]:
    year, month = int(start[:4]), int(start[4:])
    out = []
    while (year, month) <= (int(end[:4]), int(end[4:])):
        out.append(f"{year}{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return out


def run(inp: object) -> object:
    """진입 함수. 입력 {"snapshot_id", "hs6", "partner", "months", "grouping_version"?, "evidence_ids"?, "path"?} →
    {"snapshot", "scope", "parent", "world", "children", "peers", "resolve"}.

    path가 없으면 정본 빌드를 연다. path의 상대경로는 저장소 루트 기준이다(개발 빌드를 열 때 쓴다).
    """
    if not isinstance(inp, dict) or not {"snapshot_id", "hs6", "partner", "months"} <= set(inp):
        raise ValueError("입력은 snapshot_id, hs6, partner, months를 담은 객체다")
    path = inp.get("path")
    if path is not None:
        path = Path(path) if Path(path).is_absolute() else REPO_ROOT / path
    with open_snapshot(inp["snapshot_id"], path=path) as snap:
        months = list(inp["months"])
        return {
            "snapshot": snap.snapshot_object(),
            "scope": snap.scope(),
            "parent": snap.parent_series(inp["hs6"], inp["partner"], months),
            "world": snap.world_series(inp["hs6"], months),
            "children": [snap.children(inp["hs6"], inp["partner"], month) for month in months],
            "peers": [] if inp.get("grouping_version") is None else snap.peers(inp["hs6"], inp["partner"],
                                                                                inp["grouping_version"]),
            "resolve": [snap.resolve(e) for e in inp.get("evidence_ids", [])],
        }
