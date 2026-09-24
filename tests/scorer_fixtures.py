"""독립 채점기(eval/scorer/) 시험용 합성 자료 도우미. 파일 이름이 test로 시작하지 않아 시험으로 모이지 않는다.

- 실제 스냅샷 SQLite(저장소에 커밋하지 않는다)와 봉인 폴더를 쓰지 않는다. 룰북 docs/eval/RULEBOOK.md B3-1 예시
  1~8의 v2 값(CN·850450·2024년 1월: 21,876,681 USD ÷ 1,075,490 kg, ALL HS10 합 56,680,573 USD)과 경계 사례에 필요한
  행을 합성 행으로 다시 만든다. 다른 상대국 행과 HS10 코드는 시험용 합성 값이다.
- oracle_snapshot은 eval/dev/oracle_ABC.json의 A/B/C 원자료(부모·HS10 V·Q, 전체국가 금액)를 행으로 옮긴다. oracle에는
  품목·상대국·월이 없으므로 시험용으로 hs6 850450, 상대국 A=CN·B=JP·C=DE, 기준월 202301·비교월 202401, HS10
  X1=8504501010·X2=8504501020을 붙인다.
- 스냅샷에는 단위 S2(스냅샷 빌드)가 만드는 표 넷을 둔다: observation, collection_receipt(수신 기록), snapshot_meta(수집
  계획 collection_plan·기간 등, 값은 JSON 글자), peer_group(비교국 표 17열). 수신 기록은 요청 이름 규칙에서 만든다
  (request_receipts): hs4_{국가}_{연도}=HS4 스캔, hs6_{국가}[_{HS6}]_{연도}=HS6 조회, it_hs4_{연도}·it_hs6[_{HS6}]_{연도}=
  분모 조회. 요청의 행이 NOT_COLLECTED뿐이면 수신 기록이 없고(미수집), REQUEST_FAILED 행이 있으면 FAILED, 아니면 OK다.
- write_sqlite는 스냅샷 빌드의 표 이름·열 이름으로 SQLite 파일을 만든다.
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
PEER_COLUMNS = ("entity_type", "entity_id", "entity_namespace", "baci_country_code", "scope_type", "scope_id",
                "peer_rank", "peer_id", "similarity", "community_id", "method", "grouping_version", "params_hash",
                "source_version", "source_year", "input_sha256", "generated_at")
REPO_ROOT = Path(__file__).resolve().parents[1]
V2_PARTNERS = ["CN", "JP", "DE", "VN", "US", "PH", "TW", "FR", "FI", "SE", "KH", "NL", "ID", "IN", "MX", "MY"]


def collection_plan(hs6: list[str], partners: list[str], start: str, end: str, **extra) -> dict:
    """수집 설정(configs/collection_plan.json 모양). hs4_scan은 8504, 분모 조회를 한다."""
    plan = {"period": {"start": start, "end": end}, "chunk_months": 12, "hs6": hs6, "partners": partners,
            "collect_total_denominator": True, "hs10": [], "hs4_scan": ["8504"]}
    plan.update(extra)
    return plan


RULEBOOK_PLAN = collection_plan(["850450", "850431", "850432", "850490"], V2_PARTNERS, "202201", "202412")
ORACLE_PLAN = collection_plan(["850450"], ["CN", "JP", "DE"], "202301", "202412")


def _request_source(name: str) -> tuple[str, str, str | None, str] | None:
    """요청 이름 규칙 → (엔드포인트, hsSgn, 상대국 또는 None(ALL), 연도). 규칙 밖이면 None."""
    parts = name.split("_")
    if parts[0] == "it" and len(parts) in (3, 4) and parts[1] in ("hs4", "hs6"):
        code = "8504" if parts[1] == "hs4" else (parts[2] if len(parts) == 4 else "850450")
        return "itemtrade", code, None, parts[-1]
    if parts[0] == "hs4" and len(parts) == 3:
        return "nitemtrade", "8504", parts[1].upper(), parts[2]
    if parts[0] == "hs6" and len(parts) in (3, 4):
        return "nitemtrade", parts[2] if len(parts) == 4 else "850450", parts[1].upper(), parts[-1]
    return None


def _receipt(rowid: int, request: str, endpoint: str, params: dict, status: str) -> dict:
    """수신 기록 한 줄(수집기 collection_receipt 열)."""
    return {"rowid": rowid, "request_id": request, "endpoint": endpoint,
            "params_json": json.dumps(params, sort_keys=True), "status": status,
            "http_status": 200 if status == "OK" else 500, "attempts": 1, "response_hash": "0" * 64, "row_count": 1,
            "result_code": "00", "result_msg": "OK", "error": None if status == "OK" else "HTTP 500", "elapsed_ms": 1,
            "raw_file_id": f"{request}.xml", "timestamp": "2026-09-23T21:00:00+09:00"}


class Rows:
    """합성 스냅샷 행을 쌓는다. rowid는 표마다 1부터 차례로 붙는다."""

    def __init__(self, snapshot_id: str, plan: dict | None = None):
        self.snapshot_id = snapshot_id
        self.plan = plan if plan is not None else RULEBOOK_PLAN
        self.observation: list[dict] = []
        self.receipts: list[dict] = []
        self.peers: list[dict] = []

    def obs(self, partner: str, hs: str, month: str, v: int | None, q: int | None, status: str = "OBSERVED",
            request: str = "req", flow: str = "import") -> int:
        rowid = len(self.observation) + 1
        self.observation.append({
            "rowid": rowid, "snapshot_id": self.snapshot_id, "request_id": request, "month": month,
            "partner_code": partner, "partner_namespace": "KCS_cntyCd", "hs_code": hs, "hs_level": len(hs),
            "hs_version": "HSK", "flow": flow, "amount_usd": v, "net_weight_kg": q, "observation_status": status,
            "raw_file_id": None if status == "NOT_COLLECTED" else f"{request}.xml",
            "raw_row_locator": f"item[{rowid}]", "item_name": None})
        return rowid

    def receipt(self, request: str, endpoint: str, params: dict, status: str = "OK") -> int:
        rowid = len(self.receipts) + 1
        self.receipts.append(_receipt(rowid, request, endpoint, params, status))
        return rowid

    def peer(self, entity: str, peers: list[str], version: str = "g0", scope: tuple[str, str] = ("hs6", "850450")):
        """대상국 entity의 비교국 표 행(순위는 목록 순서)."""
        for rank, peer in enumerate(peers, start=1):
            self.peers.append({
                "rowid": len(self.peers) + 1, "entity_type": "exporter_country", "entity_id": entity,
                "entity_namespace": "KCS_cntyCd", "baci_country_code": None, "scope_type": scope[0],
                "scope_id": scope[1], "peer_rank": rank, "peer_id": peer, "similarity": None, "community_id": None,
                "method": "test", "grouping_version": version, "params_hash": "0" * 64, "source_version": "test",
                "source_year": 2023, "input_sha256": "0" * 64, "generated_at": "2026-09-25T00:00:00+09:00"})

    def request_receipts(self) -> list[dict]:
        """명시한 수신 기록과, 요청 이름 규칙에서 만든 수신 기록(명시하지 않은 요청만)."""
        receipts = list(self.receipts)
        named = {r["request_id"] for r in receipts}
        statuses: dict[str, set[str]] = {}
        for row in self.observation:
            statuses.setdefault(row["request_id"], set()).add(row["observation_status"])
        for request, found in statuses.items():
            source = _request_source(request)
            if request in named or source is None or found == {"NOT_COLLECTED"}:
                continue
            endpoint, code, partner, year = source
            params = {"strtYymm": f"{year}01", "endYymm": f"{year}12", "hsSgn": code}
            if partner is not None:
                params["cntyCd"] = partner
            receipts.append(_receipt(len(receipts) + 1, request, endpoint, params,
                                     "FAILED" if "REQUEST_FAILED" in found else "OK"))
        return receipts

    def meta_rows(self) -> list[dict]:
        """snapshot_meta 행(값은 JSON 글자, 스냅샷 빌드와 같은 직렬화)."""
        values = {"schema_version": 1, "snapshot_id": self.snapshot_id, "source_kind": "controlled",
                  "collection_plan": self.plan, "period": self.plan["period"]}
        return [{"rowid": i, "key": key, "value": json.dumps(value, ensure_ascii=False, sort_keys=True,
                                                             separators=(",", ":"))}
                for i, (key, value) in enumerate(sorted(values.items()), start=1)]

    def ev(self, rowid: int, table: str = "observation") -> str:
        return f"ev:{self.snapshot_id}:{table}:{rowid}"

    def doc(self) -> dict:
        """단위 run 입력의 snapshot 객체."""
        return {"snapshot_id": self.snapshot_id,
                "tables": {"observation": list(self.observation), "collection_receipt": self.request_receipts(),
                           "snapshot_meta": self.meta_rows(), "peer_group": list(self.peers)}}


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
    """룰북 B3-1 예시 1~8·경계 사례용 합성 스냅샷 kcs_202201_202412_v2(시험 전용 행). 수집 계획은 v2 설정(HS6 4개 ×
    상대국 16개, 2022~2024년)이고, 비교국 표는 CN·JP의 g0 비교국(JP의 비교국 TR은 계획 밖)이다."""
    rows = Rows("kcs_202201_202412_v2", RULEBOOK_PLAN)
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
    # 분석 범위 밖 HS6(HS4 스캔이 함께 돌려준 850440, 자료 계약 §2.3.2 행 규칙 7)
    ids["cn_850440_2401"] = rows.obs("CN", "850440", "202401", 5000, 100, request="hs4_cn_2024")
    # 계획 밖 비교국 TR(JP의 비교국): 스냅샷 빌드가 만든 NOT_COLLECTED 행(HS4 스캔·HS6 조회 자리)
    ids["tr_hs4_2401"] = rows.obs("TR", "8504", "202401", None, None, "NOT_COLLECTED", request="hs4_tr_2024")
    ids["tr_hs6_2401"] = rows.obs("TR", "850450", "202401", None, None, "NOT_COLLECTED",
                                  request="hs6_tr_850450_2024")
    # MX: HS4 스캔 실패(부모 HS6 행 없음), HS6 조회는 성공해 HS10 하위 행이 있다
    ids["mx_hs4_2401"] = rows.obs("MX", "8504", "202401", None, None, "REQUEST_FAILED", request="hs4_mx_2024")
    ids["mx_kids_2401"] = [rows.obs("MX", code, "202401", v, q, request="hs6_mx_850450_2024")
                           for code, (v, q) in (("8504501010", (300, 30)), ("8504501020", (200, 20)))]
    rows.peer("CN", ["JP", "VN", "US", "DE", "FR"])
    rows.peer("JP", ["CN", "VN", "US", "DE", "TR"])
    return rows, ids


ORACLE_PARTNERS = {"A-composition": "CN", "B-residual": "JP", "C-missing-hs10": "DE"}
ORACLE_HS10 = {"X1": "8504501010", "X2": "8504501020"}
ORACLE_MONTHS = {"baseline": "202301", "comparison": "202401"}


def load_oracle() -> dict:
    """저장소의 eval/dev/oracle_ABC.json(고치지 않는 기존 파일)을 소수는 Decimal로 읽는다."""
    return json.loads((REPO_ROOT / "eval" / "dev" / "oracle_ABC.json").read_text(encoding="utf-8"),
                      parse_float=Decimal)


def oracle_snapshot(oracle: dict) -> tuple[Rows, dict[str, dict]]:
    """oracle A/B/C 원자료를 합성 스냅샷 controlled_fixture_v0 행으로 옮긴다. 사례마다 {이름: rowid 또는 목록}. 수집 계획은
    HS6 850450 × CN·JP·DE, 2023~2024년이다."""
    rows = Rows("controlled_fixture_v0", ORACLE_PLAN)
    for target in ORACLE_PARTNERS.values():  # 합성 비교국 표: 세 나라가 서로의 비교국(g0/g1과 무관한 합성 값)
        rows.peer(target, [p for p in ORACLE_PARTNERS.values() if p != target])
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
    """합성 스냅샷을 스냅샷 빌드의 표 이름·열 이름으로 SQLite 파일에 쓴다(rowid를 그대로 넣는다)."""
    tables = (("observation", OBSERVATION_COLUMNS, ", PRIMARY KEY(request_id, month, partner_code, hs_code, flow)"),
              ("collection_receipt", RECEIPT_COLUMNS, ""), ("snapshot_meta", ("key", "value"), ""),
              ("peer_group", PEER_COLUMNS, ""))
    con = sqlite3.connect(path)
    try:
        for name, columns, extra in tables:
            con.execute(f"CREATE TABLE {name}(" + ", ".join(columns) + extra + ")")
            for row in doc["tables"].get(name, []):
                con.execute(f"INSERT INTO {name}(rowid, {', '.join(columns)}) VALUES("
                            + ", ".join("?" * (len(columns) + 1)) + ")", [row["rowid"]] + [row[c] for c in columns])
        con.commit()
    finally:
        con.close()


def batch_line(run_id: str, case_id: str, mode: str = "full", dataset: str = "controlled_fixture_v0",
               status: str = "COMPLETED", review: str | None = "MONITOR", signal: dict | None = None,
               snapshot_id: str = "controlled_fixture_v0", **extra) -> dict:
    """하네스 묶음 기록 한 줄(자료 계약 §8의 실행 쪽 키 21개)."""
    completed = status == "COMPLETED"
    line = {"run_id": run_id, "case_id": case_id, "dataset": dataset, "mode": mode, "policy_version": "dev-0.1",
            "rulebook_version": "RB-1", "snapshot_id": snapshot_id, "grouping_version": "g0",
            "code_version": "0123456789abcdef0123456789abcdef01234567",
            "review_status_final": review if completed else None,
            "signal_status": (signal or {"unit_value": review, "share": "NOT_TRIGGERED"}) if completed else None,
            "unresolved_evidence": False if completed else None, "execution_status": status,
            "tool_attempts": 5, "model_requests": 0 if mode == "checklist" else 4,
            "tokens_in": 0 if mode == "checklist" else 3000, "tokens_out": 0 if mode == "checklist" else 500,
            "wall_ms": 12_000, "critic_used": mode == "full", "revision_used": False,
            "errors": [] if completed else [{"code": "provider_http_5xx"}]}
    line.update(extra)
    return line


def oracle_reports(rows: Rows, ids: dict, mode: str = "full", stamp: str = "260925100001") -> dict[str, dict]:
    """oracle A/B/C마다 필수 근거를 채우는 정상 보고서(합성). run_id는 run_case-{stamp를 사례마다 1씩 늘린 것}.
    분해 claim은 within_effect·mix_effect·residual 셋을 모두 적는다(필수 근거 weight_share_decomposition)."""
    ev = rows.ev
    reports = {}
    specs = {"A-composition": ("CN", "MONITOR"), "B-residual": ("JP", "MAINTAIN"), "C-missing-hs10": ("DE", "HOLD")}
    for offset, (case_id, (partner, status)) in enumerate(specs.items()):
        mine = ids[case_id]
        parents = [ev(mine["parent_comparison"]), ev(mine["parent_baseline"])]
        kids = [ev(r) for r in mine.get("kids_comparison", []) + mine.get("kids_baseline", [])]
        base = {"partner": partner, "baseline": "202301"}
        claims = [claim("c1", "change", "r_U", Decimal("-40.0"), "%", "DOWN", parents,
                        text="단가가 전년 같은 달보다 40.0% 낮다.", **base)]
        if case_id == "A-composition":
            claims += [claim("c2", "decomposition", "within_effect", Decimal("0.00"), "USD/kg", "FLAT", parents + kids,
                             **base),
                       claim("c3", "decomposition", "mix_effect", Decimal("-2.40"), "USD/kg", "DOWN", parents + kids,
                             text="구성 변화 효과는 kg당 −2.40달러다.", **base)]
            for i, code in enumerate(("8504501010", "8504501020")):
                rows_of_code = [ev(r) for r in mine["kids_comparison"] + mine["kids_baseline"]
                                if rows.observation[r - 1]["hs_code"] == code]
                claims.append(claim(f"c{4 + i}", "change", f"r_U@{code}", Decimal("0.0"), "%", "FLAT", rows_of_code,
                                    **base))
            claims.append(claim("c6", "decomposition", "residual", Decimal("0.00"), "USD/kg", "FLAT", parents + kids,
                                **base))
        elif case_id == "B-residual":
            claims += [claim("c2", "decomposition", "within_effect", Decimal("-2.40"), "USD/kg", "DOWN",
                             parents + kids, **base),
                       claim("c3", "decomposition", "mix_effect", Decimal("0.00"), "USD/kg", "FLAT", parents + kids,
                             **base),
                       claim("c4", "comparison", "r_U", Decimal("-40.0"), "%", "DOWN",
                             [ev(ids["A-composition"]["parent_comparison"]), ev(ids["A-composition"]["parent_baseline"])],
                             partner="CN", baseline="202301", text="비교국 CN도 40.0% 낮다."),
                       claim("c5", "decomposition", "residual", Decimal("0.00"), "USD/kg", "FLAT", parents + kids,
                             **base)]
        else:
            claims.append(claim("c2", "data_status", "observation_status@8504501010", "REQUEST_FAILED", None, "NA",
                                [ev(mine["hs10_status_comparison"])], partner=partner,
                                text="HS10 하위 자료 요청이 실패했다(REQUEST_FAILED)."))
        label = {"MONITOR": "모니터링", "MAINTAIN": "검토 유지", "HOLD": "자료 보류"}[status]
        run_id = f"run_case-{int(stamp) + offset:012d}"
        reports[case_id] = report(run_id, claims, case_id=case_id, mode=mode, snapshot_id=rows.snapshot_id,
                                  review_status=status, evidence_ids=parents + kids,
                                  narrative=f"단가가 전년 같은 달보다 40.0% 낮아졌다. 판정은 {label}이다.")
    return reports
