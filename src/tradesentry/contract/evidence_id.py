"""단위 K2 근거 ID.

단위 ID: K2
도메인명: contract_evidence_id
소유: D
입력: (`snapshot_id`, `table`, `rowid`) 또는 `ev:` 문자열
출력: 그 반대 표현(`ev:` 문자열 ↔ (`snapshot_id`, `table`, `rowid`))과 풀림 규칙 판정
허용 import: 표준 라이브러리, tradesentry.contract

정본: 자료 계약 docs/rules/DATA_CONTRACT_V1.md §4.4(형식 `ev:<snapshot_id>:<table>:<rowid>`와 해석(풀림) 규칙 네 가지).

풀림 규칙(§4.4). 넷을 모두 채우면 풀린다. 앞에서부터 보고, 처음 어긋난 규칙 번호를 `failed_rule`로 돌려준다.
1. `:`로 나눈 조각이 정확히 4개이고 첫 조각이 `ev`다.
2. `<snapshot_id>`가 그 보고서·실행 기록의 `snapshot_id`와 같다.
3. 그 스냅샷에 `<table>` 테이블이 있다.
4. 그 테이블에 rowid가 `<rowid>`인 행이 있다.

계약이 정하지 않아 이 단위가 정한 것(보고서에 해석으로 적는다)
- rowid 조각은 앞자리 0 없는 10진수 양의 정수(`[1-9][0-9]*`, ASCII 숫자)만 표준형으로 본다. 부호·공백·앞자리 0(`01`)은
  같은 행을 가리키는 두 번째 글자열을 만들므로 받지 않는다. 그런 조각은 "rowid가 그 값인 행"이 없다고 보고 규칙 4에서
  어긋난다. SQLite rowid 최댓값(2^63-1)을 넘는 수도 규칙 4에서 어긋난다.
- 빈 `<snapshot_id>` 조각은 규칙 2, 빈 `<table>` 조각은 규칙 3에서 어긋난다(그런 스냅샷·테이블은 없다).
- 만들기(format)는 조각에 `:`나 빈 값이 있으면 거부한다(§4.4 "`:`를 넣지 않는다").
실제 테이블·행의 존재는 이 단위가 모른다. 호출하는 쪽(자료 접근층 단위 K3 등)이 확인 함수를 넘긴다.
독립 채점기(eval/scorer/)는 같은 규칙을 따로 구현한다(이 모듈을 import하지 않는다).
"""
import re
from dataclasses import dataclass
from typing import Callable

from tradesentry.contract import types

SEPARATOR = ":"
ROWID_RE = re.compile(r"[1-9][0-9]*")  # fullmatch로 쓴다. [0-9]는 ASCII 숫자만이다
ROWID_MAX = 2 ** 63 - 1  # SQLite rowid의 최댓값


class EvidenceIdError(ValueError):
    """근거 ID 문자열이 형식에 맞지 않는다. `rule`은 처음 어긋난 풀림 규칙 번호(1~4)다."""

    def __init__(self, message: str, rule: int) -> None:
        super().__init__(message)
        self.rule = rule


@dataclass(frozen=True)
class EvidenceRef:
    """근거 ID가 가리키는 스냅샷 행."""

    snapshot_id: str
    table: str
    rowid: int

    def evidence_id(self) -> str:
        return format_evidence_id(self.snapshot_id, self.table, self.rowid)


def _check_piece(name: str, value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"근거 ID의 {name}는 빈 문자열이 아닌 문자열이어야 한다")
    if SEPARATOR in value:
        raise ValueError(f"근거 ID의 {name}에 `:`를 넣지 않는다")
    return value


def format_evidence_id(snapshot_id: str, table: str, rowid: int) -> str:
    """(`snapshot_id`, `table`, `rowid`) → `ev:<snapshot_id>:<table>:<rowid>`. 조각이 맞지 않으면 ValueError다."""
    _check_piece("snapshot_id", snapshot_id)
    _check_piece("table", table)
    if isinstance(rowid, bool) or not isinstance(rowid, int) or not 0 < rowid <= ROWID_MAX:
        raise ValueError("근거 ID의 rowid는 1 이상 2^63-1 이하의 정수여야 한다")
    return SEPARATOR.join((types.EVIDENCE_ID_PREFIX, snapshot_id, table, str(rowid)))


def split_evidence_id(evidence_id: object) -> list[str]:
    """규칙 1(조각 4개, 첫 조각 `ev`)을 보고 조각 네 개를 돌려준다. 어긋나면 EvidenceIdError(rule=1)."""
    if not isinstance(evidence_id, str):
        raise EvidenceIdError("근거 ID는 문자열이어야 한다", 1)
    parts = evidence_id.split(SEPARATOR)
    if len(parts) != 4 or parts[0] != types.EVIDENCE_ID_PREFIX:
        raise EvidenceIdError("근거 ID는 `:`로 나눈 조각이 4개이고 첫 조각이 `ev`여야 한다", 1)
    return parts


def rowid_of(piece: str) -> int | None:
    """rowid 조각의 값. 표준형(앞자리 0 없는 양의 정수, 2^63-1 이하)이 아니면 None이다."""
    if not ROWID_RE.fullmatch(piece):
        return None
    value = int(piece)
    return value if value <= ROWID_MAX else None


def parse_evidence_id(evidence_id: object) -> EvidenceRef:
    """`ev:` 문자열 → EvidenceRef. 스냅샷과 무관하게 형식만 본다. 어긋나면 EvidenceIdError(처음 어긋난 규칙 번호)."""
    _, snapshot_id, table, piece = split_evidence_id(evidence_id)
    if not snapshot_id:
        raise EvidenceIdError("근거 ID의 snapshot_id 조각이 비었다", 2)
    if not table:
        raise EvidenceIdError("근거 ID의 table 조각이 비었다", 3)
    rowid = rowid_of(piece)
    if rowid is None:
        raise EvidenceIdError("근거 ID의 rowid 조각이 앞자리 0 없는 양의 정수가 아니다", 4)
    return EvidenceRef(snapshot_id, table, rowid)


def resolve_evidence_id(evidence_id: object, snapshot_id: str, *,
                        has_table: Callable[[str], bool],
                        has_row: Callable[[str, int], bool]) -> dict:
    """풀림 규칙 1~4를 차례로 본다. 돌려주는 값: {"evidence_id", "resolved", "failed_rule"}.

    snapshot_id는 그 보고서·실행 기록의 `snapshot_id`다. has_table(table)은 스냅샷에 그 테이블이 있는지,
    has_row(table, rowid)는 그 테이블에 그 rowid 행이 있는지 돌려준다(has_table이 참일 때만 부른다).
    """
    result = {"evidence_id": evidence_id, "resolved": False, "failed_rule": None}
    try:
        _, piece_snapshot, table, piece_rowid = split_evidence_id(evidence_id)
    except EvidenceIdError as exc:
        return {**result, "failed_rule": exc.rule}
    if not piece_snapshot or piece_snapshot != snapshot_id:
        return {**result, "failed_rule": 2}
    if not table or not has_table(table):
        return {**result, "failed_rule": 3}
    rowid = rowid_of(piece_rowid)
    if rowid is None or not has_row(table, rowid):
        return {**result, "failed_rule": 4}
    return {**result, "resolved": True}


def _run_one(item: object) -> object:
    if isinstance(item, str):
        try:
            ref = parse_evidence_id(item)
        except EvidenceIdError as exc:
            return {"evidence_id": item, "failed_rule": exc.rule}
        return {"evidence_id": item, "snapshot_id": ref.snapshot_id, "table": ref.table, "rowid": ref.rowid,
                "failed_rule": None}
    if isinstance(item, dict) and "evidence_id" in item:
        rows = item.get("rows") or {}
        if not isinstance(rows, dict):
            raise ValueError("풀림 판정 입력의 rows는 {테이블: [rowid, …]} 모양이어야 한다")
        present = {table: set(rowids) for table, rowids in rows.items()}
        return resolve_evidence_id(item["evidence_id"], item.get("snapshot_id"),
                                   has_table=lambda table: table in present,
                                   has_row=lambda table, rowid: rowid in present[table])
    if isinstance(item, dict) and set(item) == {"snapshot_id", "table", "rowid"}:
        return {"evidence_id": format_evidence_id(item["snapshot_id"], item["table"], item["rowid"])}
    raise ValueError("입력은 `ev:` 문자열, {snapshot_id, table, rowid}, {evidence_id, snapshot_id, rows} 가운데 하나다")


def run(inp: object) -> object:
    """진입 함수. 입력 하나 또는 그 목록을 받아 같은 모양으로 돌려준다.

    - `ev:` 문자열 → {"evidence_id", "snapshot_id", "table", "rowid", "failed_rule": None} 또는
      {"evidence_id", "failed_rule": 규칙 번호}(형식만 본 결과)
    - {"snapshot_id", "table", "rowid"} → {"evidence_id": `ev:` 문자열}(조각이 맞지 않으면 ValueError)
    - {"evidence_id", "snapshot_id", "rows": {테이블: [rowid, …]}} → 풀림 판정 {"evidence_id", "resolved", "failed_rule"}
    """
    if isinstance(inp, list):
        return [_run_one(item) for item in inp]
    return _run_one(inp)
