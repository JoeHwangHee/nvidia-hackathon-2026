"""단위 G1 g0 고정 목록.

단위 ID: G1
도메인명: grouping_g0
소유: M
입력: HS6×상대국의 2023년 1~12월 OBSERVED 수입금액 합(v2 부모 HS6 행), 후보국 목록, 매개변수(k, 기준연도 등)
출력: peer_group 행의 CSV 문자열(g0: HS6·대상국마다 대상국을 뺀 수입금액 상위 5개국, 열 17개)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal

정본: 자료 계약 docs/rules/DATA_CONTRACT_V1.md §2.3.6의 g0 항목(필드 값), §2.3.2 행 규칙 4(부모 HS6 행), §3.4(관측
상태). 해석: 결정 기록 docs/tracking/decisions/20260924-2212-user-decision-snapshot-build-and-g0.md(대상국을 뺀 15개국
중 5개국). 결과 파일은 data/reference/peer_group_g0.csv다(구현 계획 승인 D3으로 계획 경로 표에 더함). 경보 결과를 보고
g0를 바꾸지 않는다.

재현 명령(저장소 루트에서 두 단계. 결과 파일은 이 두 단계로 만들었다. 명령 줄은 들여쓰기 없이 그대로 입력한다)
1. 입력 만들기: load_input 결과를 outputs/grouping_g0-{시각}/grouping_g0-{시각}.json에 쓰고 그 경로를 출력한다.
   실자료 금액이 들어 있으므로 outputs/(커밋 안 함)에만 둔다. 스냅샷은 읽기만 한다.
uv run --locked python - <v2 스냅샷 폴더> <<'EOF'
import sys
from tradesentry.grouping import g0
print(g0.write_input(sys.argv[1], "outputs", k=5, source_year=2023))
EOF
   generated_at은 이 단계의 시각(KST)이 된다. 커밋한 결과 파일과 바이트까지 같게 만들려면 그 파일의 generated_at
   값을 write_input에 generated_at="…"으로 더 넘긴다.
2. 공통 실행기(개발 전용): 1단계가 출력한 경로를 --in으로 준다.
uv run --locked python -m tradesentry.units G1 --in outputs/grouping_g0-{시각}/grouping_g0-{시각}.json
   run의 CSV 문자열이 outputs/grouping_g0-{시각}/grouping_g0-{시각}.csv(1단계와 다른 시각)로 써진다(등록부 확장자
   csv). 확인한 뒤 data/reference/peer_group_g0.csv로 옮긴다. 옮기기는 이미 있으면 실패하는 방식(os.link 뒤 원본
   지우기)이다(자료 계약 §10.3 N8·N12).

run(inp) — 진입 함수. peer_group_rows(inp)의 행 목록을 to_csv로 바꾼 CSV 문자열을 돌려준다(순수 함수).

peer_group_rows(inp) — 순수 함수(파일·네트워크·시계를 쓰지 않는다). 규칙 시험이 이 행 목록을 본다
- 입력은 JSON 객체 하나이고 키는 아래 여덟 개뿐이다.
  - k: 비교국 수(계약의 조정값 5). source_year: 기준연도(2023). source_version: 입력 스냅샷 ID. input_sha256: 입력
    스냅샷의 raw 응답 결합 해시(64자리 소문자 16진수). generated_at: 생성 시각(KST ISO 8601, +09:00). 시각을 입력으로
    받아 같은 입력이면 늘 같은 출력이 나온다.
  - candidates: 후보국 목록(KCS_cntyCd 2자리 대문자, 중복 없음). v2는 수집한 상대국 16개(superset)다.
  - hs6_codes: 대상 품목(HS6, 숫자 6자리, 중복 없음) 목록. 값이 하나도 없는 품목도 빠뜨리지 않으려고 따로 받는다.
  - import_value_sums: {"hs6", "partner", "amount_usd"} 기록의 목록. (HS6, 나라)마다 기준연도 1~12월 OBSERVED 부모
    HS6 행의 수입금액(USD 정수) 합이다. OBSERVED 행이 하나도 없는 (HS6, 나라)는 기록이 없다.
- 선택 규칙(계약 §2.3.6 method=import_value_topk): HS6마다, 후보국의 나라 하나하나를 대상국으로 두고, 대상국을 뺀
  나머지 후보국을 수입금액 합이 큰 순서로 k개 고른다. 기록이 없는 나라의 합은 0(빈 합)으로 본다. 합이 같으면 국가
  코드 사전순이다. 그래서 금액이 있는 나라가 k개보다 적어도 늘 k개를 고른다(후보국이 k+1개보다 적으면 ValueError).
- 출력 행은 peer_group 필드 17개를 PEER_GROUP_KEYS 순서대로 담는다. entity_type=exporter_country, entity_id=대상국,
  entity_namespace=KCS_cntyCd, baci_country_code=None(g0는 BACI를 쓰지 않는다), scope_type=hs6, scope_id=HS6,
  peer_rank=1..k(int), peer_id=비교국, similarity=None, community_id=None, method=import_value_topk,
  grouping_version=g0, params_hash, source_version, source_year(int), input_sha256, generated_at. 행 순서는
  (scope_id, entity_id, peer_rank) 오름차순이다.
- params_hash(계약: k, 기준연도, 후보국 목록의 해시): {"candidates": 사전순으로 정렬한 후보국 목록, "k": k,
  "source_year": 기준연도}를 json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=True)로 쓴 문자열의 UTF-8
  바이트 sha256(64자리 소문자 16진수)이다. 후보국을 정렬하므로 목록 순서는 해시를 바꾸지 않는다.
- 입력이 이 형식과 다르면 조용히 고치지 않고 ValueError를 낸다.

to_csv(rows) — peer_group 행 목록을 CSV 문자열로 바꾼다
- 첫 줄은 PEER_GROUP_KEYS 열 이름 17개, 줄바꿈은 LF(CR 없음), 인용은 필요할 때만(csv.QUOTE_MINIMAL)이다. 공통
  실행기는 이 문자열을 BOM 없는 UTF-8로 쓴다. 값이 None이면 따옴표 없는 null 네 글자를 쓴다(스냅샷 빌드는
  baci_country_code·similarity·community_id의 null을 NULL로 읽는다). 정수는 십진 표기다.

load_input(snapshot_dir, *, k, source_year, generated_at) — 실자료 스냅샷에서 run 입력을 만든다
- 자료 접근층(단위 K3)이 아직 없어 표준 라이브러리 sqlite3로 읽는다. K3가 들어오면 부모 행 조회를 그쪽으로 옮긴다.
- 스냅샷 폴더의 파일을 읽기만 한다: snapshot.sqlite는 읽기 전용 URI(mode=ro)로 열고, manifest.json의 config에서
  hs6(대상 HS6)와 partners(후보국), snapshot_hash.json의 raw_combined_sha256(계약 snapshot의 raw_sha256)을 읽는다.
  네 곳(snapshot_meta, manifest.json, 그 config, snapshot_hash.json)의 snapshot_id가 다르면 ValueError다.
- 부모 HS6 행(계약 §2.3.2 행 규칙 4): flow=import, hs_level=6, observation_status=OBSERVED, month=기준연도 01~12월
  (총계 행 RAW:총계 제외), hs_code가 대상 HS6, partner_code가 후보국이고, 그 행을 만든 수집 요청이 그 HS6가 속한
  HS4의 국가별 스캔(endpoint=nitemtrade, params_json의 hsSgn=HS6 앞 4자리, cntyCd=partner_code)인 행이다. HS6 요청이
  남긴 행(HS10 하위 행, 총계 행, UNRESOLVED_ZERO 상태 행)은 쓰지 않는다.
- 부모 행의 금액이 비었거나(None) 정수가 아니거나, 같은 (HS6, 나라, 월)의 부모 행이 둘 이상이거나, 행의 수집 요청
  기록이 없으면 하나를 조용히 고르지 않고 ValueError를 낸다.

write_input(snapshot_dir, outputs_dir, *, k, source_year, generated_at=None) — 재현 명령 1단계
- load_input 결과를 outputs_dir/grouping_g0-{시각}/grouping_g0-{시각}.json에 쓰고 그 경로를 돌려준다. {시각}은 지금
  KST 초(yymmddhhmmss)이고, generated_at을 주지 않으면 그 시각을 ISO 8601로 쓴다.
- 실행 폴더는 이미 있으면 실패하는 방식(os.mkdir)으로 만들고, outputs_dir/sealed/에 같은 이름이 있으면 지우고
  실패한다(자료 계약 §10.3 N8). 파일도 이미 있으면 실패하는 방식("x")으로 쓴다. 같은 초에 다시 돌리면 실패하므로
  다음 초에 다시 돌린다. 출력 위치 기본값을 두지 않는다(S0 결정 ⑥). 스냅샷 경로는 인자로만 받는다.
"""
import csv
import hashlib
import io
import json
import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

# peer_group 필드(자료 계약 §2.3.6). 순서는 계약 커널(단위 K1)의 PEER_GROUP_KEYS와 같다(조립 때 K1에서 가져온다).
# CSV 열 순서도 이것이다.
PEER_GROUP_KEYS = (
    "entity_type", "entity_id", "entity_namespace", "baci_country_code",
    "scope_type", "scope_id",
    "peer_rank", "peer_id", "similarity",
    "community_id",
    "method", "grouping_version", "params_hash",
    "source_version", "source_year", "input_sha256",
    "generated_at",
)

# g0 행의 고정값(자료 계약 §2.3.2·§2.3.6).
ENTITY_TYPE = "exporter_country"
ENTITY_NAMESPACE = "KCS_cntyCd"
SCOPE_TYPE = "hs6"
METHOD = "import_value_topk"
GROUPING_VERSION = "g0"
CSV_NULL = "null"
DOMAIN = "grouping_g0"

INPUT_KEYS = frozenset({"k", "source_year", "source_version", "input_sha256", "generated_at",
                        "candidates", "hs6_codes", "import_value_sums"})
SUM_KEYS = frozenset({"hs6", "partner", "amount_usd"})

# 부모 HS6 행(자료 계약 §2.3.2 행 규칙 2·4, §3.4).
PARENT_ENDPOINT = "nitemtrade"
IMPORT_FLOW = "import"
OBSERVED = "OBSERVED"

_HS6_RE = re.compile(r"\d{6}")
_PARTNER_RE = re.compile(r"[A-Z]{2}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_KST = timezone(timedelta(hours=9), "KST")
_KST_OFFSET = timedelta(hours=9)
_STAMP_FORMAT = "%y%m%d%H%M%S"


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def compute_params_hash(k: int, source_year: int, candidates: list[str]) -> str:
    """params_hash: k, 기준연도, 후보국 목록(정렬)의 정규 JSON의 sha256(규칙은 머리 주석)."""
    payload = {"candidates": sorted(candidates), "k": k, "source_year": source_year}
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _check_input(inp: object) -> dict:
    _require(isinstance(inp, dict), "입력은 JSON 객체여야 한다")
    keys = set(inp)
    _require(keys == INPUT_KEYS,
             f"입력 키가 다르다: 빠진 키 {sorted(INPUT_KEYS - keys)}, 모르는 키 {sorted(keys - INPUT_KEYS)}")
    k, year = inp["k"], inp["source_year"]
    _require(_is_int(k) and k >= 1, "k는 1 이상의 정수여야 한다")
    _require(_is_int(year), "source_year는 정수여야 한다")
    _require(isinstance(inp["source_version"], str) and inp["source_version"] != "",
             "source_version은 빈 문자열이 아니어야 한다")
    _require(isinstance(inp["input_sha256"], str) and _SHA256_RE.fullmatch(inp["input_sha256"]) is not None,
             "input_sha256은 64자리 소문자 16진수여야 한다")
    generated_at = inp["generated_at"]
    _require(isinstance(generated_at, str), "generated_at은 문자열(KST ISO 8601)이어야 한다")
    try:
        stamp = datetime.fromisoformat(generated_at)
    except ValueError:
        raise ValueError("generated_at은 ISO 8601 시각이어야 한다") from None
    _require(stamp.utcoffset() == _KST_OFFSET, "generated_at은 KST(+09:00) 시각이어야 한다")

    candidates = inp["candidates"]
    _require(isinstance(candidates, list) and all(isinstance(c, str) and _PARTNER_RE.fullmatch(c)
                                                  for c in candidates),
             "candidates는 2자리 대문자 국가 코드(KCS_cntyCd)의 목록이어야 한다")
    _require(len(set(candidates)) == len(candidates), "candidates에 같은 국가 코드가 두 번 있다")
    _require(len(candidates) - 1 >= k, f"대상국을 빼면 후보국이 {len(candidates) - 1}개라 {k}개를 고를 수 없다")

    hs6_codes = inp["hs6_codes"]
    _require(isinstance(hs6_codes, list) and hs6_codes != []
             and all(isinstance(h, str) and _HS6_RE.fullmatch(h) for h in hs6_codes),
             "hs6_codes는 숫자 6자리 HS6 코드의 비어 있지 않은 목록이어야 한다")
    _require(len(set(hs6_codes)) == len(hs6_codes), "hs6_codes에 같은 코드가 두 번 있다")

    records = inp["import_value_sums"]
    _require(isinstance(records, list), "import_value_sums는 목록이어야 한다")
    sums: dict[tuple[str, str], int] = {}
    for record in records:
        _require(isinstance(record, dict) and set(record) == SUM_KEYS,
                 "import_value_sums의 기록은 hs6, partner, amount_usd 세 키의 객체여야 한다")
        hs6, partner, amount = record["hs6"], record["partner"], record["amount_usd"]
        _require(hs6 in hs6_codes, f"import_value_sums의 hs6 {hs6!r}가 hs6_codes에 없다")
        _require(partner in candidates, f"import_value_sums의 partner {partner!r}가 candidates에 없다")
        _require(_is_int(amount) and amount >= 0, f"({hs6}, {partner})의 amount_usd는 0 이상의 정수여야 한다")
        _require((hs6, partner) not in sums, f"import_value_sums에 ({hs6}, {partner})가 두 번 있다")
        sums[(hs6, partner)] = amount
    return {"k": k, "source_year": year, "source_version": inp["source_version"],
            "input_sha256": inp["input_sha256"], "generated_at": generated_at,
            "candidates": list(candidates), "hs6_codes": list(hs6_codes), "sums": sums}


def peer_group_rows(inp: object) -> list[dict]:
    """g0 비교국 목록(peer_group 행 목록)을 계산한다(순수 함수). 규칙은 머리 주석."""
    checked = _check_input(inp)
    k, sums, candidates = checked["k"], checked["sums"], checked["candidates"]
    params_hash = compute_params_hash(k, checked["source_year"], candidates)
    rows: list[dict] = []
    for hs6 in sorted(checked["hs6_codes"]):
        for target in sorted(candidates):
            others = [c for c in candidates if c != target]
            ranked = sorted(others, key=lambda code: (-sums.get((hs6, code), 0), code))
            for rank, peer in enumerate(ranked[:k], start=1):
                rows.append({
                    "entity_type": ENTITY_TYPE,
                    "entity_id": target,
                    "entity_namespace": ENTITY_NAMESPACE,
                    "baci_country_code": None,
                    "scope_type": SCOPE_TYPE,
                    "scope_id": hs6,
                    "peer_rank": rank,
                    "peer_id": peer,
                    "similarity": None,
                    "community_id": None,
                    "method": METHOD,
                    "grouping_version": GROUPING_VERSION,
                    "params_hash": params_hash,
                    "source_version": checked["source_version"],
                    "source_year": checked["source_year"],
                    "input_sha256": checked["input_sha256"],
                    "generated_at": checked["generated_at"],
                })
    return rows


def to_csv(rows: list[dict]) -> str:
    """peer_group 행 목록을 CSV 문자열로 바꾼다(열 순서 PEER_GROUP_KEYS, LF, None은 null)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(PEER_GROUP_KEYS)
    for row in rows:
        _require(isinstance(row, dict) and tuple(row) == PEER_GROUP_KEYS,
                 "행의 키가 peer_group 필드와 이름·순서가 다르다")
        values = []
        for field in PEER_GROUP_KEYS:
            value = row[field]
            _require(value is None or isinstance(value, str) or _is_int(value),
                     f"{field} 값은 문자열, 정수, None 가운데 하나여야 한다")
            values.append(CSV_NULL if value is None else value)
        writer.writerow(values)
    return buffer.getvalue()


def run(inp: object) -> str:
    """진입 함수. g0 비교국 목록의 CSV 문자열(peer_group 행 17열)을 돌려준다. 규칙은 머리 주석."""
    return to_csv(peer_group_rows(inp))


def _read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(data, dict), f"{path.name}의 최상위가 객체가 아니다")
    return data


def load_input(snapshot_dir: str | Path, *, k: int, source_year: int, generated_at: str) -> dict:
    """실자료 스냅샷 폴더에서 run 입력을 만든다. 파일은 읽기만 한다. 규칙은 머리 주석."""
    folder = Path(snapshot_dir)
    manifest = _read_json(folder / "manifest.json")
    config = manifest["config"]
    hash_record = _read_json(folder / "snapshot_hash.json")
    candidates, hs6_codes = list(config["partners"]), list(config["hs6"])
    input_sha256 = hash_record["raw_combined_sha256"]
    _require(isinstance(input_sha256, str) and _SHA256_RE.fullmatch(input_sha256) is not None,
             "snapshot_hash.json의 raw_combined_sha256이 64자리 소문자 16진수가 아니다")

    months = {f"{source_year}{month:02d}" for month in range(1, 13)}
    uri = (folder / "snapshot.sqlite").resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        meta_ids = [value for (value,) in connection.execute(
            "SELECT value FROM snapshot_meta WHERE key = 'snapshot_id'")]
        _require(len(meta_ids) == 1, "snapshot_meta에 snapshot_id가 한 줄이 아니다")
        snapshot_id = meta_ids[0]
        ids = {snapshot_id, manifest.get("snapshot_id"), config.get("snapshot_id"), hash_record.get("snapshot_id")}
        _require(len(ids) == 1, "snapshot_meta, manifest.json, 그 config, snapshot_hash.json의 snapshot_id가 다르다")
        receipts = {request_id: (endpoint, json.loads(params)) for request_id, endpoint, params in connection.execute(
            "SELECT request_id, endpoint, params_json FROM collection_receipt")}
        observed = connection.execute(
            "SELECT request_id, hs_code, partner_code, month, amount_usd FROM observation"
            " WHERE snapshot_id = ? AND flow = ? AND hs_level = 6 AND observation_status = ?"
            " AND month >= ? AND month <= ?",
            (snapshot_id, IMPORT_FLOW, OBSERVED, min(months), max(months))).fetchall()
    finally:
        connection.close()

    hs6_set, candidate_set = set(hs6_codes), set(candidates)
    seen: set[tuple[str, str, str]] = set()
    sums: dict[tuple[str, str], int] = {}
    for request_id, hs_code, partner, month, amount in observed:
        if month not in months or hs_code not in hs6_set or partner not in candidate_set:
            continue
        _require(request_id in receipts, f"({hs_code}, {partner}, {month}) 행의 수집 요청 기록이 없다")
        endpoint, params = receipts[request_id]
        if not (endpoint == PARENT_ENDPOINT and params.get("hsSgn") == hs_code[:4] and params.get("cntyCd") == partner):
            continue  # 부모 HS6 행이 아니다(HS6 요청이 남긴 행 등)
        _require(_is_int(amount), f"({hs_code}, {partner}, {month}) 부모 HS6 행의 금액이 정수가 아니다")
        key = (hs_code, partner, month)
        _require(key not in seen, f"({hs_code}, {partner}, {month}) 부모 HS6 행이 둘 이상이다")
        seen.add(key)
        sums[(hs_code, partner)] = sums.get((hs_code, partner), 0) + amount

    return {
        "k": k,
        "source_year": source_year,
        "source_version": snapshot_id,
        "input_sha256": input_sha256,
        "generated_at": generated_at,
        "candidates": candidates,
        "hs6_codes": hs6_codes,
        "import_value_sums": [{"hs6": hs6, "partner": partner, "amount_usd": total}
                              for (hs6, partner), total in sorted(sums.items())],
    }


def _now_kst() -> datetime:
    return datetime.now(_KST)


def write_input(snapshot_dir: str | Path, outputs_dir: str | Path, *, k: int, source_year: int,
                generated_at: str | None = None, clock: Callable[[], datetime] = _now_kst) -> Path:
    """재현 명령 1단계: load_input 결과를 outputs_dir/grouping_g0-{시각}/grouping_g0-{시각}.json에 쓴다(머리 주석)."""
    stamp_time = clock().astimezone(_KST).replace(microsecond=0)
    run_id = f"{DOMAIN}-{stamp_time.strftime(_STAMP_FORMAT)}"
    inp = load_input(snapshot_dir, k=k, source_year=source_year,
                     generated_at=stamp_time.isoformat() if generated_at is None else generated_at)
    parent = Path(outputs_dir)
    parent.mkdir(parents=True, exist_ok=True)
    run_dir = parent / run_id
    os.mkdir(run_dir)  # 이미 있으면 FileExistsError(덮어쓰지 않는다)
    if (parent / "sealed" / run_id).exists():
        os.rmdir(run_dir)
        raise FileExistsError(f"sealed/{run_id}가 이미 있다. 다음 초에 다시 돌린다")
    path = run_dir / f"{run_id}.json"
    with open(path, "x", encoding="utf-8") as handle:
        handle.write(json.dumps(inp, ensure_ascii=False, indent=2) + "\n")
    return path
