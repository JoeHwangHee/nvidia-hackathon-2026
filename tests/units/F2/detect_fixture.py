"""조립 작업 AS1(detect) 시험용 합성 스냅샷. 값은 모두 합성이고 실제 통계가 아니다.

만드는 법(단위 S2 시험 도우미 tests/units/S2/fixture_snapshot.py와 같은 길)
- 수집기 코드(src/tradesentry/ingest.py의 build_manifest·open_snapshot·store_result)로 수집기 형식 원천(manifest·raw·
  수집기 SQLite)을 만들고, 단위 S2(build_snapshot·install_build)로 빌드해 정본 자리(스냅샷 폴더의 snapshot_build.sqlite)에
  둔다. 수집기가 쓰는 폴더(ingest.SNAP_DIR)와 시각(ingest.now_iso)은 만드는 동안만 바꾼다. 네트워크는 부르지 않는다.
- 출처 종류(source_kind)는 기본이 controlled(합성)다. 실자료 거부 시험은 같은 본 스냅샷을 source_kind real로 만들어
  쓴다(값은 합성이고 수집기 메타의 출처 종류만 real이다).
- 기간이 13개월 이상이면 수집기가 요청을 연도 구간으로 나누므로 응답은 (엔드포인트, hsSgn, 상대국, 구간 시작 달)마다 정한다.
  응답에는 그 요청 구간의 달만 넣는다.

본 스냅샷 as1_detect_fixture(HS6 850450, 상대국 10개, 기간 202301~202402, 비교월 t = 202401·202402)
- ALL 분모: 품목별 API의 HS4(8504) 요청과 HS6(850450) 요청이 같은 HS10 행을 두 번 담는다(값 같음. 행 규칙 6 중복 제거
  대상). 합계는 202301·202401이 6000, 202302·202402가 10000이다. 중복을 빼지 않으면 분모가 두 배가 되어 TW·FI의 점유율
  발동이 뒤집힌다.
- 계열(부모 HS6 행 = HS4 스캔 응답의 850450 행, V USD / Q kg)
  - CN·JP·DE: oracle A·B·C(eval/dev/oracle_ABC.json)의 부모 값. 202301 600/100 → 202401 360/100(r_U −40%, d_s −4pp).
    HS10 하위 행은 CN이 oracle A, JP가 oracle B의 값이고, DE는 2024 구간 HS6 조회가 실패한다(oracle C, REQUEST_FAILED).
  - VN: 202302 1000/1751 → 202402 1000/2500. r_U 정확값 −29.96%(표시 −30.0) → 미발동
  - US: 202302 1000/7 → 202402 1000/10. r_U 정확히 −30% → 발동
  - PH: 202302 500/50 → 202402 1496/150. d_s 정확값 9.96pp(표시 10.0) → 미발동
  - TW: 202302 500/50 → 202402 1500/150. d_s 정확히 10pp → 발동
  - FR: 2024 구간 HS4 스캔 실패(REQUEST_FAILED), HS6 조회는 수집하지 않음(NOT_COLLECTED) → 202401·202402 지표 null
  - FI: 202302 1200/120, 202402에는 HS4 스캔에 850431 행만 있고 HS6 조회도 빈 달 → UNRESOLVED_ZERO가 빌드 정책의 승격
    규칙으로 CONFIRMED_NO_TRADE → r_U null, 점유율 12% → 0%(d_s −12pp) → 점유율 발동
  - SE: 기준월 202302 중량 0(300/0) → 202402 300/30. r_U null(zero_weight)
  - 그 밖의 달은 중립 값 500/50(변화 없음). 202303~202312은 응답이 없어 UNRESOLVED_ZERO 상태 행이다.
- 빌드 정책은 승격 규칙이 있는 시험용 정책(PROMOTION_POLICY)이다. 실제 정책이 아니다. 탐지는 저장소의 dev-0.1로 한다.

작은 스냅샷 as1_detect_world_gap(상대국 CN 하나): 2024 구간의 품목별 API 두 요청이 실패해 ALL 분모가 202401·202402에
빠진다(REQUEST_FAILED). 부모 값은 CN과 같다.

작은 스냅샷 as1_detect_other_partner(상대국 CN 하나): 합성 비교국 표(OTHER_PEER_ROWS)가 CN의 비교국으로 계획 밖 국가
GB를 가리킨다. 빌드가 GB의 NOT_COLLECTED 상태 행을 넣고 K3 scope의 other_partners가 ["GB"]가 된다. 탐지 계열은
수집 설정의 상대국(CN)뿐이어야 한다.
"""
import copy
import csv
import json
from decimal import Decimal
from pathlib import Path
from unittest import mock

from tradesentry import ingest
from tradesentry.contract.policy_load import parse_policy
from tradesentry.snapshot import build

from ..S2.fixture_snapshot import FIXED_TIME, raw_combined_sha256_shasum_style, xml_response

HS4 = "8504"
HS6 = "850450"
SIBLING_HS6 = "850431"  # 같은 HS4 아래 다른 HS6(승격 규칙의 "같은 HS4 아래 다른 HS6의 OBSERVED 행")
STAMP = "260925000000"
NEUTRAL = (500, 50)
ORACLE_PARENT = {"202301": (600, 100), "202401": (360, 100), "202302": NEUTRAL, "202402": NEUTRAL}
NEUTRAL_2023_01_2024_01 = {"202301": NEUTRAL, "202401": NEUTRAL}

PROMOTION_POLICY = {
    "_status": "시험용 빌드 정책(승격 규칙 있음). 실제 정책이 아니다",
    "schema_version": 2, "policy_version": "dev-9.9", "thresholds": {"unit_value": 30, "share": 10},
    "min_amount": None, "min_weight": None, "tolerance": {"amount_usd": 0, "weight_rounding_kg": Decimal("0.5")},
    "confirmed_no_trade": {"rule": "ingest_verify_candidates"},
}


def _config(snapshot_id: str, partners: list[str], hs6_codes: list[str] | None = None) -> dict:
    return {"snapshot_id": snapshot_id, "period": {"start": "202301", "end": "202402"}, "chunk_months": 12,
            "hs6": hs6_codes or [HS6], "partners": partners, "collect_total_denominator": True, "hs10": [],
            "hs4_scan": [HS4]}


MAIN = {
    "config": _config("as1_detect_fixture", ["CN", "JP", "DE", "VN", "US", "PH", "TW", "FR", "FI", "SE"]),
    "parent": {
        "CN": ORACLE_PARENT,
        "JP": ORACLE_PARENT,
        "DE": ORACLE_PARENT,
        "VN": {**NEUTRAL_2023_01_2024_01, "202302": (1000, 1751), "202402": (1000, 2500)},
        "US": {**NEUTRAL_2023_01_2024_01, "202302": (1000, 7), "202402": (1000, 10)},
        "PH": {**NEUTRAL_2023_01_2024_01, "202302": (500, 50), "202402": (1496, 150)},
        "TW": {**NEUTRAL_2023_01_2024_01, "202302": (500, 50), "202402": (1500, 150)},
        "FR": {"202301": NEUTRAL, "202302": NEUTRAL},
        "FI": {**NEUTRAL_2023_01_2024_01, "202302": (1200, 120)},
        "SE": {**NEUTRAL_2023_01_2024_01, "202302": (300, 0), "202402": (300, 30)},
    },
    "sibling": {"FI": {"202402": (100, 10)}},
    "children": {  # HS6 조회(850450)가 돌려주는 HS10 행. 여기 없는 상대국의 HS6 조회는 수집하지 않는다(NOT_COLLECTED)
        "CN": {"202301": [("8504501000", 500, 50), ("8504509000", 100, 50)],
               "202401": [("8504501000", 200, 20), ("8504509000", 160, 80)],
               "202302": [("8504501000", 500, 50)], "202402": [("8504501000", 500, 50)]},
        "JP": {"202301": [("8504501000", 500, 50), ("8504509000", 100, 50)],
               "202401": [("8504501000", 300, 50), ("8504509000", 60, 50)],
               "202302": [("8504501000", 500, 50)], "202402": [("8504501000", 500, 50)]},
        "DE": {"202301": [("8504501000", 500, 50), ("8504509000", 100, 50)], "202302": [("8504501000", 500, 50)]},
        "FI": {"202301": [("8504501000", 500, 50)], "202302": [("8504501000", 1200, 120)],
               "202401": [("8504501000", 500, 50)]},
    },
    "world": {
        "202301": [("8504501000", 5000, 500), ("8504509000", 1000, 250)],
        "202401": [("8504501000", 4000, 400), ("8504509000", 2000, 500)],
        "202302": [("8504501000", 7000, 700), ("8504509000", 3000, 750)],
        "202402": [("8504501000", 6000, 600), ("8504509000", 4000, 1000)],
    },
    "failed": {("nitemtrade", HS4, "FR", "202401"), ("nitemtrade", HS6, "DE", "202401")},
}

WORLD_GAP = {
    "config": _config("as1_detect_world_gap", ["CN"]),
    "parent": {"CN": ORACLE_PARENT},
    "sibling": {},
    "children": {},
    "world": {key: value for key, value in MAIN["world"].items() if key.startswith("2023")},
    "failed": {("itemtrade", HS4, "ALL", "202401"), ("itemtrade", HS6, "ALL", "202401")},
}


OTHER_PARTNER = {**WORLD_GAP, "config": _config("as1_detect_other_partner", ["CN"]), "world": MAIN["world"], "failed": set()}
# 작은 스냅샷 as1_detect_two_hs6(HS6 850450·850431 × 상대국 CN·JP): 계열 넷이 모두 202301 600/100 → 202401 360/100(r_U
# −40%)이라 좁히기가 없으면 네 계열 모두 202401에 단가 사례를 낸다. HS6 조회는 수집하지 않는다(NOT_COLLECTED). ALL 분모는 두
# HS6의 HS10 행을 같은 값으로 둔다. (hs6, partner) 쌍으로 좁히는지 보는 시험(AS1 두 번째 PR)이 쓴다.
TWO_HS6 = {
    "config": _config("as1_detect_two_hs6", ["CN", "JP"], [HS6, SIBLING_HS6]),
    "parent": {"CN": ORACLE_PARENT, "JP": ORACLE_PARENT},
    "sibling": {"CN": ORACLE_PARENT, "JP": ORACLE_PARENT},
    "children": {},
    "world": {month: rows + [("8504311000",) + rows[0][1:]] for month, rows in MAIN["world"].items()},
    "failed": set(),
}
OTHER_PEER = "GB"  # 수집 계획 밖 비교국(합성 비교국 표에만 있다)
OTHER_PEER_ROWS = [{  # 계약 §2.3.6 필드 17개. 값은 합성이다
    "entity_type": "exporter_country", "entity_id": "CN", "entity_namespace": "KCS_cntyCd", "baci_country_code": "null",
    "scope_type": "hs6", "scope_id": HS6, "peer_rank": "1", "peer_id": OTHER_PEER, "similarity": "null",
    "community_id": "null", "method": "import_value_topk", "grouping_version": "g0", "params_hash": "a" * 64,
    "source_version": "as1_detect_other_partner", "source_year": "2023", "input_sha256": "b" * 64,
    "generated_at": "2026-09-25T00:00:00+09:00"}]


def write_peer_group(path: Path, rows: list[dict]) -> Path:
    """합성 비교국 표 CSV(열 = 계약 §2.3.6 필드 17개)를 쓰고 그 경로를 돌려준다."""
    from tradesentry.contract import types

    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(types.PEER_GROUP_KEYS))
        writer.writeheader()
        writer.writerows(rows)
    return Path(path)

def _item(month: str, code: str, amount: int, weight: int, partner: str | None) -> dict:
    item = {"year": f"{month[:4]}.{month[4:]}", "impDlr": str(amount), "impWgt": str(weight), "expDlr": "0",
            "expWgt": "0", "statKor": "시험 품목"}
    item["hsCd" if partner else "hsCode"] = code
    if partner:
        item["statCd"] = partner
    return item


def _with_total(items: list[dict], partner: str | None) -> list[dict]:
    total = {"year": "총계", "impDlr": str(sum(int(i["impDlr"]) for i in items)),
             "impWgt": str(sum(int(i["impWgt"]) for i in items)), "expDlr": "0", "expWgt": "0", "statKor": "-"}
    total["hsCd" if partner else "hsCode"] = "-"
    if partner:
        total["statCd"] = "-"
    return [total] + items


def _response(spec: dict, key: tuple[str, str, str, str], months: list[str]) -> dict | None:
    """요청 하나의 수집 결과(수집기 store_result 입력). None이면 수집하지 않은 요청이다."""
    endpoint, hs_sgn, partner, _ = key
    if key in spec["failed"]:
        return {"ok": False, "http_status": 500, "attempts": 3, "raw": b"", "error": "HTTPError 500",
                "attempt_errors": ["HTTPError 500"] * 3, "elapsed_ms": 30}
    if endpoint == "itemtrade":  # 요청 코드(hsSgn)로 시작하는 HS10 행만 돌려준다(HS6 두 개 자료에서 뜻이 있다)
        items = [_item(m, code, v, q, None) for m in months for code, v, q in spec["world"].get(m, [])
                 if code.startswith(hs_sgn)]
        owner = None
    elif hs_sgn == HS4:
        items = []
        for m in months:
            if m in spec["parent"].get(partner, {}):
                items.append(_item(m, HS6, *spec["parent"][partner][m], partner))
            if m in spec["sibling"].get(partner, {}):
                items.append(_item(m, SIBLING_HS6, *spec["sibling"][partner][m], partner))
        owner = partner
    else:
        if partner not in spec["children"]:
            return None
        items = [_item(m, code, v, q, partner) for m in months for code, v, q in spec["children"][partner].get(m, [])
                 if code.startswith(hs_sgn)]
        owner = partner
    return {"ok": True, "http_status": 200, "attempts": 1, "raw": xml_response(_with_total(items, owner)),
            "error": None, "attempt_errors": [], "elapsed_ms": 10}


def make_source(root: Path, spec: dict, *, source_kind: str = "controlled") -> Path:
    """root 아래에 스냅샷 원천 폴더(manifest.json, raw/, snapshot.sqlite, snapshot_hash.json)를 만들고 그 경로를 돌려준다."""
    config = copy.deepcopy(spec["config"])
    snapshot_id = config["snapshot_id"]
    requests = ingest.build_manifest(config)
    with mock.patch.object(ingest, "SNAP_DIR", Path(root)), mock.patch.object(ingest, "now_iso", return_value=FIXED_TIME):
        folder, con = ingest.open_snapshot(snapshot_id, source_kind)
        (folder / "manifest.json").write_text(json.dumps({"snapshot_id": snapshot_id, "generated_at": FIXED_TIME,
                                                          "config": config, "requests": requests},
                                                         ensure_ascii=False, indent=1), encoding="utf-8")
        for request in requests:
            params = request["params"]
            key = (request["endpoint"], params["hsSgn"], params.get("cntyCd", "ALL"), params["strtYymm"])
            result = _response(spec, key, request["months"])
            if result is not None:
                ingest.store_result(folder, con, snapshot_id, request["endpoint"], params, result, request["months"])
        con.execute("INSERT OR REPLACE INTO snapshot_meta VALUES('last_collect_at',?)", (FIXED_TIME,))
        con.commit()
        con.close()
    (folder / "snapshot_hash.json").write_text(json.dumps({
        "snapshot_id": snapshot_id, "raw_files": len(list((folder / "raw").glob("*.xml"))),
        "raw_combined_sha256": raw_combined_sha256_shasum_style(folder / "raw"),
        "method": "스냅샷 폴더에서 `shasum -a 256 raw/*.xml | shasum -a 256`"}, ensure_ascii=False), encoding="utf-8")
    return folder


def install(root: Path, spec: dict, *, source_kind: str = "controlled", build_policy: dict | None = None,
            peer_rows: list[dict] | None = None) -> Path:
    """원천을 만들고 단위 S2로 빌드해 정본 자리(root/snapshots/{snapshot_id}/snapshot_build.sqlite)에 둔다.
    peer_rows가 있으면 그 합성 비교국 표를 빌드에 넣는다.

    스냅샷들의 뿌리(dal.query.SNAPSHOTS_ROOT로 쓸 폴더) root/snapshots를 돌려준다.
    """
    snapshots = Path(root) / "snapshots"
    folder = make_source(snapshots, spec, source_kind=source_kind)
    out = Path(root) / f"build-{spec['config']['snapshot_id']}"
    out.mkdir(parents=True)
    peer_files = [write_peer_group(Path(root) / "peer_group.csv", peer_rows)] if peer_rows else []
    build.build_snapshot(spec["config"]["snapshot_id"], out_dir=out, stamp=STAMP, source_dir=folder,
                         policy=None if build_policy is None else parse_policy(build_policy), peer_group_files=peer_files)
    build.install_build(out / f"snapshot_build-{STAMP}.sqlite", folder)
    return snapshots
