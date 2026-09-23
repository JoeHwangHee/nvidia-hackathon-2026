#!/usr/bin/env python3
"""TradeSentry ingest: 관세청 공식 API 소범위 재수집기 (표준 라이브러리만 사용).

상태: 2026-09-23 v0.2. probe·본수집(kcs_202201_202412_v1) 실측 반영. verify 는 manifest 의 기대 요청 목록 기준으로 커버리지·교차검증을 계산한다.

엔드포인트 (공공데이터포털, 개발계정 자동승인, 일 10,000건)
  - 국가별 품목별: https://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList
        params: serviceKey, strtYymm, endYymm (조회기간 1년 이내), hsSgn(옵션, 2/4/6/10자리), cntyCd(필수, 2자리)
        fields: year, statCdCntnKor1, statCd, statKor, hsCd, expWgt, expDlr, impWgt, impDlr, balPayments
        출처: https://www.data.go.kr/data/15100475/openapi.do
  - 품목별 합계(전체 국가 분모 후보): https://apis.data.go.kr/1220000/Itemtrade/getItemtradeList
        params: serviceKey, strtYymm, endYymm, hsSgn(옵션)
        fields: year, balPayments, expDlr, expWgt, hsCode, impDlr, impWgt, statKor
        출처: https://www.data.go.kr/data/15101609/openapi.do
  단위(문서 기준): 중량 = 순중량 kg, 금액 = 수입 과세가격(CIF) 미화 달러 / 수출 신고(FOB) 미화 달러.
  ※ 과거 collector의 천 USD 단위와 다르므로 ×1000 변환을 하지 않는다. 실제 단위는 probe 응답으로 재확인한다.

명령
  python3 src/tradesentry/ingest.py plan    --config configs/collection_plan.json           # 키 불필요. manifest 생성/요청 수 산정
  python3 src/tradesentry/ingest.py probe   --hs6 854442 --country CN --month 202401        # G1: 실제 1개월 응답 3회(국가별/품목별/12개월 chunk)
  python3 src/tradesentry/ingest.py collect --config configs/collection_plan.json           # manifest 실행, raw 저장, SQLite 적재
  python3 src/tradesentry/ingest.py verify  --snapshot <snapshot_id>                        # 커버리지/중복/단위/부모합계 검사 → data-readiness.json

원칙
  - serviceKey는 .env 또는 환경변수에서만 읽고 어떤 파일/로그에도 기록하지 않는다 (manifest/receipt에는 키 제외 파라미터만).
  - 모든 응답 raw XML을 그대로 저장하고 sha256을 receipt에 남긴다. 정규화 값은 raw 행 포인터(raw_file_id, raw_row_locator)를 가진다.
  - 빈 응답을 0으로 채우지 않는다. observation_status: OBSERVED / UNRESOLVED_ZERO / REQUEST_FAILED / NOT_COLLECTED. CONFIRMED_NO_TRADE는 verify 단계의 명시 규칙으로만 승격.
  - 게이트웨이 오류 봉투(OpenAPI_ServiceResponse/cmmMsgHeader/returnReasonCode)와 정상 봉투(response/header/resultCode)를 구분한다.
  - collection_http_attempts(외부 HTTP 시도 수)는 에이전트 도구 8회 예산과 다른 지표로 별도 기록한다.
  - 재수집 실패는 이전 정상 자료(raw·receipt·행)를 덮어쓰지 않는다. 실패 본문은 raw/failed/ 에, 모든 시도는 collection_attempt 에 남긴다.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAP_DIR = ROOT / "data" / "snapshots"

ENDPOINTS = {
    "nitemtrade": {
        "url": "https://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList",
        "source_url": "https://www.data.go.kr/data/15100475/openapi.do",
        "requires_country": True,
        "hs_field": "hsCd",
    },
    "itemtrade": {
        "url": "https://apis.data.go.kr/1220000/Itemtrade/getItemtradeList",
        "source_url": "https://www.data.go.kr/data/15101609/openapi.do",
        "requires_country": False,
        "hs_field": "hsCode",
    },
}
UNITS = {"amount": "USD", "weight": "kg"}  # 문서 기준. probe에서 재확인 전까지 units_confirmed=False
VALUATION = {"import": "CIF 과세가격 미화금액", "export": "FOB 신고 미화금액"}


# ----------------------------------------------------------------------------- utils
def load_env(path: Path = ROOT / ".env") -> None:
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def service_key() -> str:
    load_env()
    key = os.environ.get("DATA_GO_KR_SERVICE_KEY", "")
    if not key:
        sys.exit("DATA_GO_KR_SERVICE_KEY 가 없습니다. .env 에 Decoding 키를 넣으세요 (채팅/로그에 붙여넣지 말 것).")
    return key


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def now_iso() -> str:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).isoformat(timespec="seconds")


def months_between(start: str, end: str) -> list[str]:
    y, m = int(start[:4]), int(start[4:])
    ye, me = int(end[:4]), int(end[4:])
    out = []
    while (y, m) <= (ye, me):
        out.append(f"{y}{m:02d}")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def year_chunks(start: str, end: str, size: int = 12) -> list[tuple[str, str]]:
    """API 제한(조회기간 1년 이내)에 맞춰 [start,end] 를 size개월 구간으로 나눈다. 연도 경계를 넘지 않는다."""
    ms = months_between(start, end)
    chunks, cur = [], []
    for m in ms:
        if cur and (len(cur) >= size or m[:4] != cur[0][:4]):
            chunks.append((cur[0], cur[-1]))
            cur = []
        cur.append(m)
    if cur:
        chunks.append((cur[0], cur[-1]))
    return chunks


def request_id(endpoint: str, params: dict) -> str:
    canon = json.dumps({"endpoint": endpoint, **{k: v for k, v in sorted(params.items()) if k != "serviceKey"}}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canon.encode()).hexdigest()[:16]


# ----------------------------------------------------------------------------- HTTP
RETRYABLE_HTTP = {429, 500, 502, 503, 504}


def call_api(endpoint: str, params: dict, timeout: int = 30, retries: int = 3, backoff: float = 2.0) -> dict:
    """1회 논리 조회. 반환: {ok, http_status, attempts, raw(bytes), error, attempt_errors, elapsed_ms}. 키는 반환/로그하지 않는다.

    시도마다 status/raw/err 를 새로 시작한다(이전 시도의 오류가 남으면 재시도 성공이 실패로 기록된다).
    재시도는 429·5xx·네트워크 예외만. 그 밖의 HTTP 오류(400·401·403·404 등)는 키/파라미터 문제라 바로 멈춘다.
    attempt_errors 는 실패한 시도의 오류 목록이다(성공했으면 복구 전 오류, 실패했으면 마지막 오류까지).
    """
    url = ENDPOINTS[endpoint]["url"] + "?" + urllib.parse.urlencode({**params, "serviceKey": service_key()})
    attempts, attempt_errors = 0, []
    status, raw, err = None, b"", None
    t0 = time.time()
    while attempts < retries:
        attempts += 1
        status, raw, err, retryable = None, b"", None, True
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/xml", "User-Agent": "TradeSentry-ingest/0.1"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                status, raw = r.status, r.read()
            break
        except urllib.error.HTTPError as e:
            status, raw = e.code, e.read() or b""
            err = f"HTTPError {e.code}"
            retryable = e.code in RETRYABLE_HTTP
        except Exception as e:  # noqa: BLE001
            err = f"{type(e).__name__}: {e}"
        attempt_errors.append(err)
        if not retryable or attempts >= retries:
            break
        time.sleep(backoff * attempts)
    return {"ok": status == 200 and err is None, "http_status": status, "attempts": attempts, "raw": raw, "error": err,
            "attempt_errors": attempt_errors, "elapsed_ms": int((time.time() - t0) * 1000)}


# ----------------------------------------------------------------------------- parsing
def parse_response(raw: bytes) -> dict:
    """정상 봉투와 게이트웨이 오류 봉투를 구분해 파싱한다. 값은 문자열 그대로 보존(정수 변환은 normalize 단계)."""
    out = {"envelope": None, "result_code": None, "result_msg": None, "items": [], "parse_error": None}
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        out["parse_error"] = str(e)
        return out
    if root.tag == "OpenAPI_ServiceResponse":
        out["envelope"] = "gateway_error"
        h = root.find("cmmMsgHeader")
        if h is not None:
            out["result_code"] = (h.findtext("returnReasonCode") or "").strip()
            out["result_msg"] = f"{(h.findtext('errMsg') or '').strip()} / {(h.findtext('returnAuthMsg') or '').strip()}"
        return out
    out["envelope"] = "response"
    out["result_code"] = (root.findtext("./header/resultCode") or "").strip()
    out["result_msg"] = (root.findtext("./header/resultMsg") or "").strip()
    for i, item in enumerate(root.iter("item")):
        out["items"].append({"_row": i, **{c.tag: (c.text or "").strip() for c in item}})
    return out


def to_int_or_none(s: str | None):
    if s is None or s == "":
        return None
    s = s.replace(",", "")
    try:
        return int(s)
    except ValueError:
        try:
            f = float(s)
            return int(f) if f.is_integer() else s  # 소수면 문자열 보존 → verify에서 precision 경고
        except ValueError:
            return s


# ----------------------------------------------------------------------------- snapshot storage
def open_snapshot(snapshot_id: str, source_kind: str = "real") -> tuple[Path, sqlite3.Connection]:
    d = SNAP_DIR / snapshot_id
    (d / "raw").mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(d / "snapshot.sqlite")
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS collection_receipt(
          request_id TEXT PRIMARY KEY, endpoint TEXT, params_json TEXT, status TEXT, http_status INTEGER,
          attempts INTEGER, response_hash TEXT, row_count INTEGER, result_code TEXT, result_msg TEXT,
          error TEXT, elapsed_ms INTEGER, raw_file_id TEXT, timestamp TEXT);
        CREATE TABLE IF NOT EXISTS observation(
          snapshot_id TEXT, request_id TEXT, month TEXT, partner_code TEXT, partner_namespace TEXT,
          hs_code TEXT, hs_level INTEGER, hs_version TEXT, flow TEXT, amount_usd INTEGER, net_weight_kg INTEGER,
          observation_status TEXT, raw_file_id TEXT, raw_row_locator TEXT, item_name TEXT,
          PRIMARY KEY(request_id, month, partner_code, hs_code, flow));
        CREATE TABLE IF NOT EXISTS snapshot_meta(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE IF NOT EXISTS collection_attempt(
          request_id TEXT, endpoint TEXT, params_json TEXT, outcome TEXT, http_status INTEGER, attempts INTEGER,
          result_code TEXT, error TEXT, attempt_errors TEXT, raw_file_id TEXT, response_hash TEXT, timestamp TEXT);
        """
    )
    meta = {
        "snapshot_id": snapshot_id, "source_kind": source_kind, "created_at": now_iso(),
        "importer": "KR", "units": json.dumps(UNITS, ensure_ascii=False), "valuation_basis": json.dumps(VALUATION, ensure_ascii=False),
        "units_confirmed": "true (probe 2026-09-23: impDlr USD 정수, impWgt kg 정수; BACI 연간값과 자릿수 일치)", "precision_rule": "amount exact integer USD; weight integer kg rounded per row (total-row diff observed 2kg over 6-73 rows)", "hs_version": "HSK (응답 코드 그대로; 연도별 개정 여부는 코드 출현 연도로 판단)",
        "coverage_status": "IN_PROGRESS", "period_start": "202201", "period_end": "202412",
    }
    for k, v in meta.items():
        con.execute("INSERT OR IGNORE INTO snapshot_meta(key,value) VALUES(?,?)", (k, v))
    con.commit()
    return d, con


def store_result(d: Path, con: sqlite3.Connection, snapshot_id: str, endpoint: str, params: dict, res: dict, months: list[str]) -> dict:
    """응답 1건을 저장한다. 모든 호출은 collection_attempt 에 남는다.

    성공: raw(임시 파일 → 교체)·receipt·이 요청의 observation 행을 한 트랜잭션으로 통째 교체한다.
    실패: 응답 본문은 raw/failed/ 에 따로 둔다. 이전에 OK 였던 요청이면 raw·receipt·행을 건드리지 않는다
          (재수집 실패가 정상 자료를 덮어쓰거나, 옛 행이 내용이 바뀐 raw 를 가리키지 않도록).
          처음부터 실패한 요청만 receipt=FAILED 와 REQUEST_FAILED 행을 남긴다.
    """
    rid = request_id(endpoint, params)
    raw_file_id = f"{rid}.xml"
    ts = now_iso()
    params_json = json.dumps({k: v for k, v in params.items() if k != "serviceKey"}, ensure_ascii=False)
    parsed = parse_response(res["raw"]) if res["raw"] else {"envelope": None, "result_code": None, "result_msg": None, "items": [], "parse_error": "empty body"}
    ok = res["ok"] and parsed["envelope"] == "response" and parsed["result_code"] in ("00", "0")
    error = res["error"] or parsed.get("parse_error")
    response_hash = sha256_bytes(res["raw"]) if res["raw"] else None
    prev = con.execute("SELECT status FROM collection_receipt WHERE request_id=?", (rid,)).fetchone()
    kept_previous = not ok and prev is not None and prev[0] == "OK"
    outcome = "OK" if ok else ("FAILED_KEPT_PREVIOUS_OK" if kept_previous else "FAILED")
    if ok:
        stored_raw = raw_file_id
        tmp = d / "raw" / f".{raw_file_id}.tmp"
        tmp.write_bytes(res["raw"])
    else:
        stored_raw = None
        if res["raw"]:
            (d / "raw" / "failed").mkdir(parents=True, exist_ok=True)
            stored_raw = f"failed/{rid}.{dt.datetime.now():%Y%m%dT%H%M%S%f}.xml"
            (d / "raw" / stored_raw).write_bytes(res["raw"])
    hs_field = ENDPOINTS[endpoint]["hs_field"]
    partner = params.get("cntyCd", "ALL")
    hs_sgn = params.get("hsSgn", "")
    try:
        with con:  # 하나의 트랜잭션: 중간에 실패하면 이전 상태 그대로
            con.execute(
                "INSERT INTO collection_attempt VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (rid, endpoint, params_json, outcome, res["http_status"], res["attempts"], parsed["result_code"], error,
                 json.dumps(res.get("attempt_errors", []), ensure_ascii=False), stored_raw, response_hash, ts),
            )
            if not kept_previous:
                con.execute("DELETE FROM observation WHERE request_id=?", (rid,))
                con.execute(
                    "INSERT OR REPLACE INTO collection_receipt VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (rid, endpoint, params_json, "OK" if ok else "FAILED", res["http_status"], res["attempts"], response_hash, len(parsed["items"]),
                     parsed["result_code"], parsed["result_msg"], error, res["elapsed_ms"], stored_raw, ts),
                )
            if ok:
                seen_months: set[str] = set()
                for it in parsed["items"]:
                    month = (it.get("year") or "").replace(".", "")  # '2024.01' -> '202401'
                    hs = (it.get(hs_field) or "").strip()
                    # 실측(2026-09-23): 요청 HS 레벨의 하위 레벨 행 + '총계' 행(hsCd='-', statCd='-').
                    if hs in ("", "-"):
                        hs = hs_sgn  # 총계 행은 요청 코드로 귀속
                    # 합계 행(연도 '총계' 등)은 별도 표시. 월 형식이 아니면 원문 보존.
                    if not (len(month) == 6 and month.isdigit()):
                        month = f"RAW:{it.get('year')}"
                    seen_months.add(month)
                    for flow, af, wf in (("import", "impDlr", "impWgt"), ("export", "expDlr", "expWgt")):
                        con.execute(
                            "INSERT OR REPLACE INTO observation VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            (snapshot_id, rid, month, partner, "KCS_cntyCd", hs, len(hs), "HSK", flow, to_int_or_none(it.get(af)), to_int_or_none(it.get(wf)),
                             "OBSERVED", raw_file_id, f"item[{it['_row']}]", it.get("statKor")),
                        )
                # 요청 범위 안에 있으나 응답에 없는 월 → UNRESOLVED_ZERO (0으로 채우지 않음)
                missing_status = [m for m in months if m not in seen_months]
                status_label = "UNRESOLVED_ZERO"
            elif not kept_previous:
                missing_status = months
                status_label = "REQUEST_FAILED"
            else:
                missing_status, status_label = [], None
            for m in missing_status:
                for flow in ("import", "export"):
                    con.execute(
                        "INSERT OR REPLACE INTO observation VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (snapshot_id, rid, m, partner, "KCS_cntyCd", hs_sgn, len(hs_sgn), "HSK", flow, None, None, status_label, stored_raw, None, None),
                    )
            if ok:
                os.replace(tmp, d / "raw" / raw_file_id)  # 커밋 직전에 raw 교체. 실패하면 트랜잭션도 롤백된다.
    finally:
        if ok and tmp.exists():
            tmp.unlink()
    return {"request_id": rid, "status": "OK" if ok else "FAILED", "outcome": outcome, "rows": len(parsed["items"]), "result_code": parsed["result_code"],
            "result_msg": parsed["result_msg"], "envelope": parsed["envelope"], "http_status": res["http_status"], "attempts": res["attempts"]}


# ----------------------------------------------------------------------------- commands
def build_manifest(cfg: dict) -> list[dict]:
    """설정에서 논리 요청 목록을 만든다.

    실측 응답 구조(2026-09-23): 요청 코드의 하위 레벨로 분해된 월별 행 + '총계' 행이 온다.
      - hs4_scan: nitemtrade HS4 요청 → 하위 HS6 월별 행 (완전성 스캔 + HS6 부모값)
      - hs6:      nitemtrade HS6 요청 → 하위 HS10 월별 행 (구성분해 자료; HS6 값 = HS10 합)
      - 분모:      itemtrade 는 HS4·HS6 요청 모두 HS10 월별 행을 돌려준다(nitemtrade 와 다름).
                  그래서 ALL(전체국가) 교차검증은 HS10 행끼리 한다(verify 참고).
    요청 수 = (HS4수 + HS6수) × 국가수 × 연도구간 + 분모((HS4수 + HS6수) × 구간) + 선택 HS10 직접조회.
    """
    start, end = cfg["period"]["start"], cfg["period"]["end"]
    chunks = year_chunks(start, end, cfg.get("chunk_months", 12))
    reqs = []
    for hs4 in cfg.get("hs4_scan", []):
        for c in cfg["partners"]:
            for s, e in chunks:
                reqs.append({"endpoint": "nitemtrade", "purpose": "hs4_partner_monthly", "params": {"strtYymm": s, "endYymm": e, "hsSgn": hs4, "cntyCd": c}})
        if cfg.get("collect_total_denominator", True):
            for s, e in chunks:
                reqs.append({"endpoint": "itemtrade", "purpose": "hs4_world_total_monthly", "params": {"strtYymm": s, "endYymm": e, "hsSgn": hs4}})
    for hs6 in cfg["hs6"]:
        for c in cfg["partners"]:
            for s, e in chunks:
                reqs.append({"endpoint": "nitemtrade", "purpose": "hs6_partner_monthly", "params": {"strtYymm": s, "endYymm": e, "hsSgn": hs6, "cntyCd": c}})
        if cfg.get("collect_total_denominator", True):
            for s, e in chunks:
                reqs.append({"endpoint": "itemtrade", "purpose": "hs6_world_total_monthly", "params": {"strtYymm": s, "endYymm": e, "hsSgn": hs6}})
    for hs10_spec in cfg.get("hs10", []):  # {"hs6": "854442", "codes": [...], "partners": ["CN"], "months": ["202301","202401"]}
        for code in hs10_spec["codes"]:
            for c in hs10_spec.get("partners", cfg["partners"]):
                for s, e in year_chunks(min(hs10_spec["months"]), max(hs10_spec["months"]), cfg.get("chunk_months", 12)):
                    reqs.append({"endpoint": "nitemtrade", "purpose": "hs10_partner_monthly", "params": {"strtYymm": s, "endYymm": e, "hsSgn": code, "cntyCd": c}})
    for r in reqs:
        r["request_id"] = request_id(r["endpoint"], r["params"])
        r["months"] = months_between(r["params"]["strtYymm"], r["params"]["endYymm"])
    return reqs


def cmd_plan(args):
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    reqs = build_manifest(cfg)
    by = {}
    for r in reqs:
        by[r["purpose"]] = by.get(r["purpose"], 0) + 1
    snapshot_id = cfg.get("snapshot_id") or f"kcs_{cfg['period']['start']}_{cfg['period']['end']}_{dt.date.today():%Y%m%d}"
    out = {"snapshot_id": snapshot_id, "generated_at": now_iso(), "config": {k: v for k, v in cfg.items()}, "logical_requests": len(reqs), "by_purpose": by,
           "max_monthly_records": len(cfg["hs6"]) * len(cfg["partners"]) * len(months_between(cfg["period"]["start"], cfg["period"]["end"])),
           "note": "collection_http_attempts(재시도 포함)는 collect 실행 후 receipts에서 집계. 에이전트 도구 8회 예산과 별개 지표.", "requests": reqs}
    d = SNAP_DIR / snapshot_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "manifest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "requests"}, ensure_ascii=False, indent=1))
    print(f"manifest -> {d / 'manifest.json'}")


def cmd_probe(args):
    """G1: HS6·국가·1개월 실제 응답 확보 + 품목별 합계 + 12개월 chunk 가능 여부. 총 3 HTTP(재시도 제외)."""
    snapshot_id = args.snapshot or f"probe_{dt.datetime.now():%Y%m%d_%H%M%S}"
    d, con = open_snapshot(snapshot_id, "real")
    y = args.month[:4]
    tests = [
        ("nitemtrade", {"strtYymm": args.month, "endYymm": args.month, "hsSgn": args.hs6, "cntyCd": args.country}, [args.month]),
        ("itemtrade", {"strtYymm": args.month, "endYymm": args.month, "hsSgn": args.hs6}, [args.month]),
        ("nitemtrade", {"strtYymm": f"{y}01", "endYymm": f"{y}12", "hsSgn": args.hs6, "cntyCd": args.country}, months_between(f"{y}01", f"{y}12")),
    ]
    report = {"snapshot_id": snapshot_id, "probe_at": now_iso(), "results": []}
    for ep, params, months in tests:
        res = call_api(ep, params)
        summary = store_result(d, con, snapshot_id, ep, params, res, months)
        parsed = parse_response(res["raw"]) if res["raw"] else {"items": []}
        summary["params"] = params
        summary["first_item"] = parsed["items"][0] if parsed["items"] else None
        summary["distinct_year_values"] = sorted({it.get("year") for it in parsed["items"]})[:14]
        report["results"].append(summary)
        print(json.dumps(summary, ensure_ascii=False, indent=1))
        time.sleep(0.5)
    (d / "probe_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"probe report -> {d / 'probe_report.json'} (raw XML: {d / 'raw'})")
    print("확인할 것: (1) 봉투/resultCode (2) year 형식('2024.01'?) (3) impDlr 자릿수로 USD vs 천USD 판단 (4) 12개월 chunk 허용 여부 (5) 합계 행 존재 여부")


def cmd_collect(args):
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    reqs = build_manifest(cfg)
    snapshot_id = args.snapshot or cfg.get("snapshot_id") or f"kcs_{cfg['period']['start']}_{cfg['period']['end']}_{dt.date.today():%Y%m%d}"
    d, con = open_snapshot(snapshot_id, "real")
    (d / "manifest.json").write_text(json.dumps({"snapshot_id": snapshot_id, "generated_at": now_iso(), "config": cfg, "requests": reqs}, ensure_ascii=False, indent=1), encoding="utf-8")
    done = {r[0] for r in con.execute("SELECT request_id FROM collection_receipt WHERE status='OK'")}
    todo = [r for r in reqs if r["request_id"] not in done or args.force]
    print(f"snapshot={snapshot_id} logical_requests={len(reqs)} already_ok={len(reqs) - len(todo)} todo={len(todo)} limit={args.limit}")
    http_attempts, n = 0, 0
    for r in todo:
        if args.limit and n >= args.limit:
            break
        res = call_api(r["endpoint"], r["params"])
        http_attempts += res["attempts"]
        s = store_result(d, con, snapshot_id, r["endpoint"], r["params"], res, r["months"])
        n += 1
        print(f"[{n}/{len(todo)}] {r['purpose']} {r['params']} -> {s['outcome']} rows={s['rows']} code={s['result_code']} http={s['http_status']} attempts={s['attempts']}")
        time.sleep(args.sleep)
    con.execute("INSERT OR REPLACE INTO snapshot_meta VALUES('last_collect_at',?)", (now_iso(),))
    con.commit()
    with (d / "collection_http_attempts.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": now_iso(), "executed": n, "http_attempts": http_attempts}) + "\n")
    print(f"executed={n} collection_http_attempts(this run)={http_attempts}")


WEIGHT_ROUNDING_KG = 0.5  # 실측: 행별 순중량이 정수 kg 로 반올림. 합계 행과의 차이 허용 = 0.5kg × (행수+1). 금액(USD)은 정확히 일치해야 한다.
IMPORT_MONTH_CLASSES = ("import_pos", "import_zero_explicit", "no_response", "failed", "not_collected")
PURPOSE_BY_ENDPOINT_LEN = {("nitemtrade", 4): "hs4_partner_monthly", ("nitemtrade", 6): "hs6_partner_monthly", ("nitemtrade", 10): "hs10_partner_monthly",
                           ("itemtrade", 4): "hs4_world_total_monthly", ("itemtrade", 6): "hs6_world_total_monthly"}


def _open_readonly(d: Path) -> sqlite3.Connection:
    """verify 는 스냅샷을 읽기 전용으로 연다(검증이 자료를 바꾸지 않도록)."""
    return sqlite3.connect((d / "snapshot.sqlite").resolve().as_uri() + "?mode=ro", uri=True)


def _load_plan(d: Path, receipt_rows: list) -> tuple[dict, list[dict]]:
    """수집 당시 설정과 기대 요청 목록. manifest 가 없으면(probe 스냅샷 등) receipt 파라미터로 복원한다."""
    p = d / "manifest.json"
    manifest = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    if manifest.get("requests"):
        return manifest.get("config", {}), manifest["requests"]
    reqs = []
    for rid, endpoint, params_json, *_ in receipt_rows:
        params = json.loads(params_json)
        reqs.append({"request_id": rid, "endpoint": endpoint, "params": params, "months": months_between(params["strtYymm"], params["endYymm"]),
                     "purpose": PURPOSE_BY_ENDPOINT_LEN.get((endpoint, len(params.get("hsSgn", ""))), "other")})
    cfg = {"hs6": sorted({r["params"]["hsSgn"] for r in reqs if r["purpose"] == "hs6_partner_monthly"}),
           "partners": sorted({r["params"]["cntyCd"] for r in reqs if "cntyCd" in r["params"]}),
           "collect_total_denominator": any(r["endpoint"] == "itemtrade" for r in reqs)}
    if reqs:
        cfg["period"] = {"start": min(r["params"]["strtYymm"] for r in reqs), "end": max(r["params"]["endYymm"] for r in reqs)}
    return cfg, reqs


def _coverage_map(reqs: list[dict]) -> dict:
    """(purpose, hsSgn, partner) → {월: request_id}. 요청이 어느 달을 맡는지의 기대값."""
    cover: dict = {}
    for r in reqs:
        key = (r["purpose"], r["params"]["hsSgn"], r["params"].get("cntyCd", "ALL"))
        for m in r["months"]:
            cover.setdefault(key, {})[m] = r["request_id"]
    return cover


def _target_coverage(cfg: dict, cover: dict, receipt_status: dict, hs10_rows: list, months_all: list[str]) -> list[dict]:
    """G2: 대상 HS6 × (국가 + ALL) 기대 쌍마다 월을 5가지로 분류한다. 관측이 0개월인 쌍도 빠지지 않는다.

    import_pos           HS10 행이 있고 수입 합 > 0
    import_zero_explicit HS10 행은 있으나 수입 합 = 0 (수출만 있는 달. API 가 명시한 0 이지 결측이 아니다 — 재분류는 정책 결정)
    no_response          요청은 정상인데 그 달 행이 없음 (UNRESOLVED_ZERO)
    failed               요청 실패
    not_collected        기대 요청이 없거나 실행되지 않음
    """
    sums: dict = {}
    for rid, month, amount in hs10_rows:
        sums[(rid, month)] = sums.get((rid, month), 0) + (amount or 0)
    partners = list(cfg.get("partners", [])) + (["ALL"] if cfg.get("collect_total_denominator", True) else [])
    out = []
    for hs6 in cfg.get("hs6", []):
        for p in partners:
            by_month = cover.get(("hs6_world_total_monthly" if p == "ALL" else "hs6_partner_monthly", hs6, p), {})
            counts = dict.fromkeys(IMPORT_MONTH_CLASSES, 0)
            for m in months_all:
                rid = by_month.get(m)
                st = receipt_status.get(rid) if rid else None
                if st is None:
                    counts["not_collected"] += 1
                elif st != "OK":
                    counts["failed"] += 1
                elif (rid, m) not in sums:
                    counts["no_response"] += 1
                elif sums[(rid, m)] > 0:
                    counts["import_pos"] += 1
                else:
                    counts["import_zero_explicit"] += 1
            out.append({"hs6": hs6, "partner": p, **counts})
    return out


def _cross_check(cfg: dict, reqs: list[dict], cover: dict, receipt_status: dict, rows: list) -> dict:
    """부모-하위 교차검증. 한쪽만 있는 조합도 보고한다(inner join 이면 조용히 빠진다).

    국가별(G3): HS4 스캔의 HS6 행(부모) vs HS6 조회의 HS10 합(하위). 금액 정확 일치, 중량은 행별 반올림 허용.
    ALL(점유율 분모, G2): itemtrade 는 HS4 요청에도 HS10 행을 돌려주므로 같은 레벨끼리,
                         즉 HS4 조회의 HS10 행 vs HS6 조회의 HS10 행을 코드·월별로 정확 대조한다.
    """
    target = set(cfg.get("hs6", []))
    by_rid = {r["request_id"]: r for r in reqs}
    parent, child, all_hs4, all_hs6 = {}, {}, {}, {}
    for rid, hs, level, month, amount, weight in rows:
        r = by_rid.get(rid)
        if r is None or hs[:6] not in target:
            continue
        partner = r["params"].get("cntyCd", "ALL")
        if r["purpose"] == "hs4_partner_monthly" and level == 6:
            parent[(hs, partner, month)] = (amount or 0, weight or 0)
        elif r["purpose"] == "hs6_partner_monthly" and level == 10:
            a, w, n = child.get((hs[:6], partner, month), (0, 0, 0))
            child[(hs[:6], partner, month)] = (a + (amount or 0), w + (weight or 0), n + 1)
        elif r["purpose"] == "hs4_world_total_monthly" and level == 10:
            all_hs4[(hs, month)] = (amount, weight)
        elif r["purpose"] == "hs6_world_total_monthly" and level == 10:
            all_hs6[(hs, month)] = (amount, weight)

    def request_state(purpose: str, hs_sgn: str, partner: str, month: str) -> str:
        rid = cover.get((purpose, hs_sgn, partner), {}).get(month)
        if rid is None:
            return "not_requested"
        st = receipt_status.get(rid)
        return "ok_no_row" if st == "OK" else ("failed" if st else "not_collected")

    country: dict = {"matched": 0, "mismatches": [], "parent_only": [], "child_only": []}
    for k in sorted(set(parent) | set(child)):
        hs6, partner, month = k
        if k in parent and k in child:
            (pa, pw), (ca, cw, n) = parent[k], child[k]
            if pa != ca or abs(pw - cw) > WEIGHT_ROUNDING_KG * (n + 1):
                country["mismatches"].append({"hs6": hs6, "partner": partner, "month": month, "parent_usd": pa, "child_sum_usd": ca,
                                              "parent_kg": pw, "child_sum_kg": cw, "n_children": n})
            else:
                country["matched"] += 1
        elif k in parent:
            country["parent_only"].append({"hs6": hs6, "partner": partner, "month": month, "parent_usd": parent[k][0],
                                           "hs6_request": request_state("hs6_partner_monthly", hs6, partner, month)})
        else:
            country["child_only"].append({"hs6": hs6, "partner": partner, "month": month, "child_sum_usd": child[k][0],
                                          "hs4_scan_request": request_state("hs4_partner_monthly", hs6[:4], partner, month)})
    all_check: dict = {"expected": bool(target) and any(r["purpose"] == "hs6_world_total_monthly" for r in reqs),
                       "matched": 0, "mismatches": [], "only_in_hs4_query": [], "only_in_hs6_query": []}
    for k in sorted(set(all_hs4) | set(all_hs6)):
        hs10, month = k
        if k in all_hs4 and k in all_hs6:
            if all_hs4[k] != all_hs6[k]:
                all_check["mismatches"].append({"hs10": hs10, "month": month, "hs4_query": list(all_hs4[k]), "hs6_query": list(all_hs6[k])})
            else:
                all_check["matched"] += 1
        elif k in all_hs4:
            all_check["only_in_hs4_query"].append({"hs10": hs10, "month": month})
        else:
            all_check["only_in_hs6_query"].append({"hs10": hs10, "month": month})
    return {"country": country, "ALL": all_check}


def _raw_hash_mismatches(d: Path, receipt_rows: list) -> list[dict]:
    """OK receipt 의 response_hash 와 raw 파일 sha256 을 대조한다(raw 교체 도중 중단·수동 편집 검출)."""
    bad = []
    for rid, _endpoint, _params, status, raw_file_id, response_hash in receipt_rows:
        if status != "OK":
            continue
        p = d / "raw" / (raw_file_id or f"{rid}.xml")
        actual = sha256_bytes(p.read_bytes()) if p.exists() else None
        if actual != response_hash:
            bad.append({"request_id": rid, "raw_file_id": raw_file_id, "receipt_sha256": response_hash, "file_sha256": actual})
    return bad


def cmd_verify(args):
    d = SNAP_DIR / args.snapshot
    con = _open_readonly(d)
    q = lambda sql, *p: con.execute(sql, p).fetchall()  # noqa: E731
    meta = dict(q("SELECT key, value FROM snapshot_meta"))
    receipt_rows = q("SELECT request_id, endpoint, params_json, status, raw_file_id, response_hash FROM collection_receipt")
    receipt_status = {r[0]: r[3] for r in receipt_rows}
    cfg, reqs = _load_plan(d, receipt_rows)
    cover = _coverage_map(reqs)
    period = cfg.get("period") or {}
    months_all = months_between(period.get("start") or meta.get("period_start", "202201"), period.get("end") or meta.get("period_end", "202412"))
    receipts = q("SELECT status, COUNT(*) FROM collection_receipt GROUP BY status")
    obs_status = q("SELECT observation_status, COUNT(*) FROM observation WHERE flow='import' GROUP BY observation_status")
    # G2: 대상 HS6 × (국가 + ALL) 기대 쌍별 월 분류 (HS6 조회의 HS10 행 기준)
    hs10_rows = q("SELECT request_id, month, amount_usd FROM observation WHERE flow='import' AND observation_status='OBSERVED' AND hs_level=10 AND month NOT LIKE 'RAW:%'")
    coverage = _target_coverage(cfg, cover, receipt_status, hs10_rows, months_all)
    # HS4 스캔 커버리지(HS4·HS6 선정 참고): 행이 있는 달 / 수입 > 0 인 달
    cov6 = q("SELECT hs_code, partner_code, COUNT(DISTINCT month), COUNT(DISTINCT CASE WHEN amount_usd>0 THEN month END) FROM observation WHERE flow='import' AND observation_status='OBSERVED' AND hs_level=6 AND month NOT LIKE 'RAW:%' GROUP BY hs_code, partner_code ORDER BY 1,2")
    # 정수가 아닌 값: 소수는 INTEGER 열 친화성 때문에 real 로 저장되므로 text 만 보면 놓친다
    nonint = q("SELECT COUNT(*) FROM observation WHERE typeof(amount_usd) NOT IN ('integer','null') OR typeof(net_weight_kg) NOT IN ('integer','null')")
    zero_w = q("SELECT COUNT(*) FROM observation WHERE flow='import' AND observation_status='OBSERVED' AND amount_usd>0 AND (net_weight_kg IS NULL OR net_weight_kg=0) AND month NOT LIKE 'RAW:%'")
    # 요청 내 총계 행 대조: 월별 행 합 vs RAW:총계 (금액 정확, 중량 반올림 허용)
    total_check = q(
        """
        SELECT t.request_id, t.partner_code, t.hs_code, t.amount_usd, s.a, t.net_weight_kg, s.k, s.n
        FROM observation t JOIN (SELECT request_id, flow, SUM(amount_usd) a, SUM(net_weight_kg) k, COUNT(*) n FROM observation
                                 WHERE observation_status='OBSERVED' AND month NOT LIKE 'RAW:%' GROUP BY request_id, flow) s
          ON s.request_id=t.request_id AND s.flow=t.flow
        WHERE t.flow='import' AND t.month LIKE 'RAW:%'
        """
    )
    total_bad = [r for r in total_check if r[3] != r[4] or abs((r[5] or 0) - (r[6] or 0)) > WEIGHT_ROUNDING_KG * (r[7] + 1)]
    # 행은 있는데 총계 행이 없는 응답 = 잘림 의심 (빈 응답은 총계 행이 없는 게 정상)
    no_total = q("SELECT request_id, row_count FROM collection_receipt r WHERE status='OK' AND row_count>0 AND NOT EXISTS (SELECT 1 FROM observation o WHERE o.request_id=r.request_id AND o.month LIKE 'RAW:%')")
    cross = _cross_check(cfg, reqs, cover, receipt_status,
                         q("SELECT request_id, hs_code, hs_level, month, amount_usd, net_weight_kg FROM observation WHERE flow='import' AND observation_status='OBSERVED' AND hs_level IN (6, 10) AND month NOT LIKE 'RAW:%'"))
    # 무거래 후보: HS6 조회가 빈 응답(UNRESOLVED_ZERO)인데 같은 partner/month 의 HS4 스캔에 해당 HS6 행이 없고 다른 HS6 행은 있음 → CONFIRMED_NO_TRADE 후보 (자동 승격 안 함)
    no_trade = q(
        """
        SELECT u.hs_code, u.partner_code, u.month FROM observation u
        WHERE u.flow='import' AND u.observation_status='UNRESOLVED_ZERO' AND u.hs_level=6
          AND NOT EXISTS (SELECT 1 FROM observation p WHERE p.flow='import' AND p.hs_level=6 AND p.observation_status='OBSERVED' AND p.hs_code=u.hs_code AND p.partner_code=u.partner_code AND p.month=u.month)
          AND EXISTS (SELECT 1 FROM observation o WHERE o.flow='import' AND o.hs_level=6 AND o.observation_status='OBSERVED' AND substr(o.hs_code,1,4)=substr(u.hs_code,1,4) AND o.partner_code=u.partner_code AND o.month=u.month)
        """
    )
    con.close()
    raw_bad = _raw_hash_mismatches(d, receipt_rows)
    n = len(months_all)
    country_pairs = [c for c in coverage if c["partner"] != "ALL"]
    all_pairs = [c for c in coverage if c["partner"] == "ALL"]
    full_rows = lambda cs: sum(1 for c in cs if c["import_pos"] + c["import_zero_explicit"] == n)  # noqa: E731
    full_pos = lambda cs: sum(1 for c in cs if c["import_pos"] == n)  # noqa: E731
    cc, ac = cross["country"], cross["ALL"]
    denominator_ok = (not ac["expected"]) or (ac["matched"] > 0 and not (ac["mismatches"] or ac["only_in_hs4_query"] or ac["only_in_hs6_query"]))
    g3 = cc["matched"] > 0 and not (cc["mismatches"] or cc["parent_only"] or cc["child_only"]) and not total_bad and not no_total
    readiness = {
        "snapshot_id": args.snapshot, "verified_at": now_iso(), "verify_logic": "v0.2 (2026-09-23): manifest 기대 요청 기준 커버리지 + 양방향 교차검증",
        "receipts_by_status": dict(receipts), "import_obs_by_status": dict(obs_status),
        "coverage_target_pairs": coverage,
        "coverage_hs6_from_hs4_scan": [{"hs6": r[0], "partner": r[1], "months": r[2], "months_import_pos": r[3]} for r in cov6],
        "non_integer_values": nonint[0][0], "positive_amount_zero_or_null_weight": zero_w[0][0],
        "total_row_checks": len(total_check),
        "total_row_mismatches": [{"request_id": r[0], "partner": r[1], "hs": r[2], "total_usd": r[3], "sum_usd": r[4], "total_kg": r[5], "sum_kg": r[6], "n_rows": r[7]} for r in total_bad],
        "responses_without_total_row": [{"request_id": r[0], "rows": r[1]} for r in no_total],
        "cross_check": cross,
        "cross_checks_hs4_vs_hs10": cc["matched"] + len(cc["mismatches"]), "cross_check_mismatches": cc["mismatches"],  # 이전 키 유지(국가별 짝지어진 대조만)
        "raw_hash_mismatches": raw_bad,
        "confirmed_no_trade_candidates": [{"hs6": r[0], "partner": r[1], "month": r[2]} for r in no_trade],
        "units_confirmed": meta.get("units_confirmed"), "precision_rule": meta.get("precision_rule"), "hs_version": meta.get("hs_version"),
        "gates": {
            "G1_new_collection_access": any(s == "OK" for s, _ in receipts),
            "G2_full_period_quality": {
                "months_required": n,
                "pairs_expected": {"country": len(country_pairs), "ALL": len(all_pairs)},
                "pairs_full_any_rows": {"country": full_rows(country_pairs), "ALL": full_rows(all_pairs)},
                "pairs_full_import_pos": {"country": full_pos(country_pairs), "ALL": full_pos(all_pairs)},
                "denominator_cross_check_ok": denominator_ok,
            },
            "G3_hs10_decomposition": g3,
            "snapshot_integrity": not raw_bad,
        },
        "notes": [
            "G2 는 대상 HS6 × (국가 + ALL) 기대 쌍 기준. any_rows = 그 달 HS10 행이 있음(수출만 있는 달 포함), import_pos = 수입 합 > 0. 이전 verify 의 쌍 집계(예: 77쌍)는 itemtrade HS4 응답에서 온 비대상 HS6 의 ALL 쌍까지 섞인 값이다.",
            "import_zero_explicit 는 결측이 아니라 API 가 명시한 0 이다. CONFIRMED_NO_TRADE 재분류는 정책 결정 사항.",
            "G3 = 국가별 HS4 스캔 HS6 행 vs HS6 조회 HS10 합의 양방향 대조(한쪽만 있어도 실패) + 총계 대조 + 잘림 의심 응답 없음.",
            "ALL(점유율 분모)은 itemtrade HS4 응답의 HS10 행 vs HS6 응답의 HS10 행을 코드·월별로 정확 대조한다(G2.denominator_cross_check_ok).",
            "금액은 정확 일치, 중량은 행별 정수 kg 반올림(허용 0.5kg×(행수+1)) - probe 2026-09-23 실측 기반.",
            "CONFIRMED_NO_TRADE 는 후보만 나열. 승격은 정책 결정 사항.",
            "G2 는 수집 기간 전체 기준. 24개월 분석창은 2023-01~2024-12.",
        ],
    }
    out = d / args.out
    out.write_text(json.dumps(readiness, ensure_ascii=False, indent=1), encoding="utf-8")
    brief = {k: v for k, v in readiness.items() if k not in ("coverage_target_pairs", "coverage_hs6_from_hs4_scan", "confirmed_no_trade_candidates", "cross_check", "notes")}
    brief["cross_check"] = {
        "country": {"matched": cc["matched"], "mismatches": len(cc["mismatches"]), "parent_only": len(cc["parent_only"]), "child_only": len(cc["child_only"])},
        "ALL": {"expected": ac["expected"], "matched": ac["matched"], "mismatches": len(ac["mismatches"]),
                "only_in_hs4_query": len(ac["only_in_hs4_query"]), "only_in_hs6_query": len(ac["only_in_hs6_query"])},
    }
    print(json.dumps(brief, ensure_ascii=False, indent=1))
    print(f"coverage: target_pairs={len(coverage)} hs4_scan_rows={len(cov6)} | no_trade_candidates={len(no_trade)} -> {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("--config", required=True); p.set_defaults(fn=cmd_plan)
    p = sub.add_parser("probe"); p.add_argument("--hs6", required=True); p.add_argument("--country", required=True); p.add_argument("--month", required=True); p.add_argument("--snapshot"); p.set_defaults(fn=cmd_probe)
    p = sub.add_parser("collect"); p.add_argument("--config", required=True); p.add_argument("--snapshot"); p.add_argument("--limit", type=int, default=0); p.add_argument("--sleep", type=float, default=0.3); p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_collect)
    p = sub.add_parser("verify"); p.add_argument("--snapshot", required=True); p.add_argument("--out", default="data-readiness.json", help="스냅샷 폴더 안 출력 파일명"); p.set_defaults(fn=cmd_verify)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
