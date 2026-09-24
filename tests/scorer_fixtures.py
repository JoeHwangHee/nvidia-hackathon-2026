"""독립 채점기(eval/scorer/) 시험용 합성 자료 도우미. 파일 이름이 test로 시작하지 않아 시험으로 모이지 않는다.

- 실제 스냅샷 SQLite(저장소에 커밋하지 않는다)와 봉인 폴더를 쓰지 않는다. 룰북 docs/eval/RULEBOOK.md B3-1 예시
  1~8의 v2 값(CN·850450·2024년 1월: 21,876,681 USD ÷ 1,075,490 kg, ALL HS10 합 56,680,573 USD)과 경계 사례에 필요한
  행을 합성 행으로 다시 만든다. 다른 상대국 행과 HS10 코드는 시험용 합성 값이다.
- oracle_snapshot은 eval/dev/oracle_ABC.json의 A/B/C 원자료(부모·HS10 V·Q, 전체국가 금액)를 행으로 옮긴다. oracle에는
  품목·상대국·월이 없으므로 시험용으로 hs6 850450, 상대국 A=CN·B=JP·C=DE, 기준월 202301·비교월 202401, HS10
  X1=8504501010·X2=8504501020을 붙인다.
- write_sqlite는 수집기(src/tradesentry/ingest.py)의 observation·collection_receipt 열 이름으로 SQLite 파일을 만든다.
"""
import json
import sqlite3
from decimal import Decimal
from pathlib import Path

OBSERVATION_COLUMNS = ("snapshot_id", "request_id", "month", "partner_code", "partner_namespace", "hs_code", "hs_level",
                       "hs_version", "flow", "amount_usd", "net_weight_kg", "observation_status", "raw_file_id",
                       "raw_row_locator", "item_name")
RECEIPT_COLUMNS = ("request_id", "endpoint", "params_json", "status", "http_status", "attempts", "response_hash",
                   "row_count", "result_code", "result_msg", "error", "elapsed_ms", "raw_file_id", "timestamp")
REPO_ROOT = Path(__file__).resolve().parents[1]


class Rows:
    """합성 스냅샷 행을 쌓는다. rowid는 1부터 차례로 붙는다."""

    def __init__(self, snapshot_id: str):
        self.snapshot_id = snapshot_id
        self.observation: list[dict] = []
        self.receipts: list[dict] = []

    def obs(self, partner: str, hs: str, month: str, v: int | None, q: int | None, status: str = "OBSERVED",
            request: str = "req", flow: str = "import") -> int:
        rowid = len(self.observation) + 1
        self.observation.append({
            "rowid": rowid, "snapshot_id": self.snapshot_id, "request_id": request, "month": month,
            "partner_code": partner, "partner_namespace": "KCS_cntyCd", "hs_code": hs, "hs_level": len(hs),
            "hs_version": "HSK", "flow": flow, "amount_usd": v, "net_weight_kg": q, "observation_status": status,
            "raw_file_id": f"{request}.xml", "raw_row_locator": f"item[{rowid}]", "item_name": None})
        return rowid

    def receipt(self, request: str, endpoint: str, params: dict) -> int:
        rowid = len(self.receipts) + 1
        self.receipts.append({"rowid": rowid, "request_id": request, "endpoint": endpoint,
                              "params_json": json.dumps(params), "status": "OK", "http_status": 200, "attempts": 1,
                              "response_hash": "0" * 64, "row_count": 1, "result_code": "00", "result_msg": "OK",
                              "error": None, "elapsed_ms": 1, "raw_file_id": f"{request}.xml",
                              "timestamp": "2026-09-23T21:00:00+09:00"})
        return rowid

    def ev(self, rowid: int, table: str = "observation") -> str:
        return f"ev:{self.snapshot_id}:{table}:{rowid}"

    def doc(self) -> dict:
        """단위 run 입력의 snapshot 객체."""
        return {"snapshot_id": self.snapshot_id,
                "tables": {"observation": list(self.observation), "collection_receipt": list(self.receipts)}}


def claim(claim_id: str, claim_type: str, metric: str, value: object, unit: object, direction: str,
          evidence: list[str], *, hs6: str = "850450", partner: str = "CN", period: str = "202401",
          baseline: object = None, text: str = "") -> dict:
    """typed claim 하나(자료 계약 §6 필드 12개)."""
    return {"claim_id": claim_id, "claim_type": claim_type, "hs6": hs6, "partner": partner, "period": period,
            "baseline_period": baseline, "metric": metric, "value": value, "unit": unit, "direction": direction,
            "evidence_ids": evidence, "text": text}


def report(run_id: str, claims: list[dict], *, narrative: str = "", hypotheses: list | None = None,
           case_id: str = "case-1", mode: str = "full", snapshot_id: str = "kcs_202201_202412_v2",
           report_id: str | None = None, review_status: str = "MAINTAIN",
           signal_status: dict | None = None, evidence_ids: list | None = None) -> dict:
    """보고서 객체(자료 계약 §9 키 17개)."""
    return {"report_id": report_id or f"report-{run_id}", "run_id": run_id, "case_id": case_id, "mode": mode,
            "claims": claims, "narrative": narrative, "hypotheses": hypotheses or [], "review_status": review_status,
            "signal_status": signal_status or {"unit_value": review_status, "share": "NOT_TRIGGERED"},
            "unresolved_evidence": False, "evidence_ids": evidence_ids or [], "validator_findings": [],
            "report_hash": "0" * 64, "created_at": "2026-09-25T10:00:00+09:00", "policy_version": "dev-0.1",
            "snapshot_id": snapshot_id, "grouping_version": "g0"}


# ALL HS10 월 행(합성 HS10 코드). 2024년 1월 합은 룰북 예시 6의 분모 56,680,573이다.
WORLD_2401 = {"8504501010": (20_000_000, 900_000), "8504501020": (15_000_000, 700_000),
              "8504501030": (10_000_000, 500_000), "8504501040": (6_000_000, 300_000),
              "8504501090": (4_000_000, 200_000), "8504509000": (1_680_573, 90_000)}
WORLD_2301 = {"8504501010": (18_000_000, 850_000), "8504501020": (13_000_000, 650_000),
              "8504501030": (9_000_000, 450_000), "8504501040": (5_000_000, 250_000),
              "8504501090": (3_500_000, 180_000), "8504509000": (1_500_000, 80_000)}
# CN 부모 행 아래 HS10 하위 행. 금액 합은 부모와 같고 중량 합은 1,075,492kg이다(룰북 B3-1 경계 7).
CN_CHILDREN_2401 = {"8504501010": (9_000_000, 450_000), "8504501020": (6_000_000, 300_000),
                    "8504501030": (4_000_000, 200_000), "8504501040": (1_500_000, 70_000),
                    "8504501090": (1_000_000, 50_000), "8504509000": (376_681, 5_492)}


def rulebook_snapshot() -> tuple[Rows, dict[str, object]]:
    """룰북 B3-1 예시 1~8·경계 사례용 합성 스냅샷 kcs_202201_202412_v2(시험 전용 행)."""
    rows = Rows("kcs_202201_202412_v2")
    ids: dict[str, object] = {}
    ids["cn_2401"] = rows.obs("CN", "850450", "202401", 21_876_681, 1_075_490, request="hs4_cn_2024")
    ids["cn_2301"] = rows.obs("CN", "850450", "202301", 20_000_000, 800_000, request="hs4_cn_2023")
    ids["cn_total"] = rows.obs("CN", "8504", "RAW:총계", 250_000_000, 12_000_000, request="hs4_cn_2024")
    ids["cn_kids_2401"] = [rows.obs("CN", code, "202401", v, q, request="hs6_cn_850450_2024")
                           for code, (v, q) in CN_CHILDREN_2401.items()]
    for month, world in (("202401", WORLD_2401), ("202301", WORLD_2301)):
        year = month[:4]
        ids[f"all_hs4_{month}"] = [rows.obs("ALL", code, month, v, q, request=f"it_hs4_{year}")
                                   for code, (v, q) in world.items()]
        ids[f"all_hs6_{month}"] = [rows.obs("ALL", code, month, v, q, request=f"it_hs6_850450_{year}")
                                   for code, (v, q) in world.items()]
    ids["jp_2301"] = rows.obs("JP", "850450", "202301", 1000, 100, request="hs4_jp_2023")    # U 10.00
    ids["jp_2401"] = rows.obs("JP", "850450", "202401", 613, 100, request="hs4_jp_2024")     # U 6.13, r_U −38.7
    ids["vn_2301"] = rows.obs("VN", "850450", "202301", 10_000, 1000, request="hs4_vn_2023")  # U 10.000
    ids["vn_2401"] = rows.obs("VN", "850450", "202401", 10_004, 1000, request="hs4_vn_2024")  # r_U +0.04
    ids["us_2401"] = rows.obs("US", "850450", "202401", 4069, 200, request="hs4_us_2024")     # U 20.345(딱 절반)
    ids["de_2401"] = rows.obs("DE", "850450", "202401", 96, 0, request="hs4_de_2024")        # 금액>0, 중량 0
    ids["fr_2401"] = rows.obs("FR", "850450", "202401", None, None, "UNRESOLVED_ZERO", request="hs6_fr_850450_2024")
    ids["fi_2301"] = rows.obs("FI", "850450", "202301", None, None, "CONFIRMED_NO_TRADE",
                              request="hs6_fi_850450_2023")
    ids["fi_2401"] = rows.obs("FI", "850450", "202401", 1000, 10, request="hs4_fi_2024")
    ids["se_2401"] = rows.obs("SE", "850450", "202401", 0, 0, request="hs4_se_2024")         # 수입 0 명시
    ids["kh_2301"] = rows.obs("KH", "850450", "202301", 0, 50, request="hs4_kh_2023")        # 기준월 단가 0
    ids["kh_2401"] = rows.obs("KH", "850450", "202401", 100, 10, request="hs4_kh_2024")
    ids["cn_export_2401"] = rows.obs("CN", "850450", "202401", 5, 1, request="hs4_cn_2024", flow="export")
    rows.receipt("hs4_cn_2024", "nitemtrade", {"strtYymm": "202401", "endYymm": "202412", "hsSgn": "8504",
                                                "cntyCd": "CN"})
    return rows, ids


ORACLE_PARTNERS = {"A-composition": "CN", "B-residual": "JP", "C-missing-hs10": "DE"}
ORACLE_HS10 = {"X1": "8504501010", "X2": "8504501020"}
ORACLE_MONTHS = {"baseline": "202301", "comparison": "202401"}


def load_oracle() -> dict:
    """저장소의 eval/dev/oracle_ABC.json(고치지 않는 기존 파일)을 소수는 Decimal로 읽는다."""
    return json.loads((REPO_ROOT / "eval" / "dev" / "oracle_ABC.json").read_text(encoding="utf-8"),
                      parse_float=Decimal)


def oracle_snapshot(oracle: dict) -> tuple[Rows, dict[str, dict]]:
    """oracle A/B/C 원자료를 합성 스냅샷 controlled_fixture_v0 행으로 옮긴다. 사례마다 {이름: rowid 또는 목록}."""
    rows = Rows("controlled_fixture_v0")
    ids: dict[str, dict] = {}
    world_seen: dict[str, int] = {}
    for case in oracle["cases"]:
        partner = ORACLE_PARTNERS[case["case_id"]]
        share = case["expected"]["share"]
        mine: dict[str, object] = {}
        for side, month in ORACLE_MONTHS.items():
            data = case[side]
            parent = data["parent"]
            mine[f"parent_{side}"] = rows.obs(partner, "850450", month, parent["V"], parent["Q"],
                                              request=f"hs4_{partner}_{month[:4]}")
            if isinstance(data.get("hs10"), list):
                mine[f"kids_{side}"] = [rows.obs(partner, ORACLE_HS10[k["code"]], month, k["V"], k["Q"],
                                                 request=f"hs6_{partner}_{month[:4]}") for k in data["hs10"]]
            elif data.get("hs10") == "REQUEST_FAILED":
                mine[f"hs10_status_{side}"] = rows.obs(partner, "850450", month, None, None, "REQUEST_FAILED",
                                                       request=f"hs6_{partner}_{month[:4]}")
            world = share["V_world_0" if side == "baseline" else "V_world_1"]
            if world_seen.setdefault(month, world) != world:
                raise ValueError("oracle 사례들의 전체국가 금액이 달라 한 스냅샷에 담을 수 없다")
        ids[case["case_id"]] = mine
    for month, world in world_seen.items():
        half = world // 2
        for code, value in (("8504501010", half), ("8504501020", world - half)):
            for request in (f"it_hs4_{month[:4]}", f"it_hs6_{month[:4]}"):  # 같은 키의 중복 행(동등)
                ids.setdefault("world", {}).setdefault(month, []).append(
                    rows.obs("ALL", code, month, value, 100, request=request))
    return rows, ids


def write_sqlite(path: Path, doc: dict) -> None:
    """합성 스냅샷을 수집기 열 이름의 SQLite 파일로 쓴다(rowid를 그대로 넣는다)."""
    con = sqlite3.connect(path)
    try:
        con.execute("CREATE TABLE observation(" + ", ".join(OBSERVATION_COLUMNS)
                    + ", PRIMARY KEY(request_id, month, partner_code, hs_code, flow))")
        con.execute("CREATE TABLE collection_receipt(" + ", ".join(RECEIPT_COLUMNS) + ")")
        for row in doc["tables"]["observation"]:
            con.execute(f"INSERT INTO observation(rowid, {', '.join(OBSERVATION_COLUMNS)}) VALUES("
                        + ", ".join("?" * (len(OBSERVATION_COLUMNS) + 1)) + ")",
                        [row["rowid"]] + [row[c] for c in OBSERVATION_COLUMNS])
        for row in doc["tables"].get("collection_receipt", []):
            con.execute(f"INSERT INTO collection_receipt(rowid, {', '.join(RECEIPT_COLUMNS)}) VALUES("
                        + ", ".join("?" * (len(RECEIPT_COLUMNS) + 1)) + ")",
                        [row["rowid"]] + [row[c] for c in RECEIPT_COLUMNS])
        con.commit()
    finally:
        con.close()
