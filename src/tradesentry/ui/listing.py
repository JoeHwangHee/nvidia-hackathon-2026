"""경보 목록 v2의 요약 카드·진행 상태·정렬·변화내용 문구(UI3, 순수 논리, streamlit 없음).

- 값은 경보 줄(`alerts.alert_row`)의 지표(단위 I2 이력 도구 봉투에서 옮긴 Decimal)와 실행 결과 기록·결정 기록에서만 가져온다.
  새로 계산하는 것은 개수 세기, 부호 비교, 정렬 순서뿐이다.
- 진행 상태(행마다 하나): 이 세션에서 도는 조사면 `RUNNING`. 아니면 그 사례의 최신 결정 기록이 있을 때, 결정이 가리키는 실행보다
  새로운 완료(`COMPLETED`) 실행이 같은 사례에 있으면 `NEW_RESULT`(새 조사 결과 · 결정 대기. 결정 뒤 다시 조사한 결과가 가려지지
  않게, UI4), 없으면 `approval.check`가 `VALID`면 `DECIDED`, `REVIEW_REQUIRED`면 `REVIEW_REQUIRED`. 결정이 없으면 최신 실행이
  `COMPLETED`면 `AWAITING`(조사 완료 · 내 결정 대기), 실패·무효면 `FAILED`, 실행이 없으면 `NOT_STARTED`. `NEW_RESULT`는 화면
  표시 규칙이다: 이전 결정 기록과 그 유효 상태(A1 `approval.check`는 결정이 가리키는 실행의 보고서와 대조)는 그대로다. 실패했거나
  진행 중인(실행 결과 기록이 없는) 새 실행은 이 규칙에 넣지 않는다. `NEW_RESULT`는 "내 결정을 기다리는 사례" 수와 조회 조건
  "조사 완료 · 결정 대기"에 든다.
- 화면 문구에는 품목·국가 이름과 월만 쓴다(HS6 코드·사례 ID·실행 폴더 이름·영문 상태 코드를 넣지 않는다).
"""
from decimal import Decimal

from tradesentry import app
from tradesentry.ui import alerts, i18n
from tradesentry.ui.i18n import t

NOT_STARTED, RUNNING, AWAITING, NEW_RESULT, DECIDED, REVIEW_REQUIRED, FAILED = (
    "NOT_STARTED", "RUNNING", "AWAITING", "NEW_RESULT", "DECIDED", "REVIEW_REQUIRED", "FAILED")
PROGRESS_STATES = (NOT_STARTED, RUNNING, AWAITING, NEW_RESULT, DECIDED, REVIEW_REQUIRED, FAILED)
WAITING_STATES = (AWAITING, NEW_RESULT)  # 내 결정을 기다리는 사례
PROGRESS_FILTERS = {  # 조회 조건 "진행 상태" → 포함하는 상태
    "all": PROGRESS_STATES,
    "not_started": (NOT_STARTED, FAILED),
    "running": (RUNNING,),
    "awaiting": WAITING_STATES,
    "decided": (DECIDED, REVIEW_REQUIRED),
}
SORTS = ("change", "item", "partner", "progress")
PROGRESS_ORDER = {RUNNING: 0, AWAITING: 1, NEW_RESULT: 1, REVIEW_REQUIRED: 2, FAILED: 3, NOT_STARTED: 4, DECIDED: 5}
SIGNALS = ("all", "unit_value", "share")


def _dec(value: object) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, Decimal)):
        return Decimal(value)
    try:
        return Decimal(str(value))
    except (ArithmeticError, ValueError, TypeError):
        return None


# ---- 진행 상태 ---------------------------------------------------------------------------------------------------


def newer_completed_run(runs: list[dict], decided_run_id: object) -> dict | None:
    """결정 기록이 가리키는 실행보다 새로운(실행명 시각이 더 뒤인) 완료 실행 가운데 가장 새 것(실행 요약, alerts.run_entry). runs는
    같은 사례의 실행 요약 목록이다. 실패·무효 실행과 실행 결과 기록이 없는(진행 중) 실행은 넣지 않는다. 결정의 run_id가 실행명
    형식이 아니면 None."""
    if not isinstance(decided_run_id, str) or not app.RUN_DIR_RE.fullmatch(decided_run_id):
        return None
    decided = app.run_stamp(decided_run_id)
    newer = [run for run in runs if run.get("status") == alerts.INVESTIGATED and isinstance(run.get("run_id"), str)
             and app.RUN_DIR_RE.fullmatch(run["run_id"]) and app.run_stamp(run["run_id"]) > decided]
    return max(newer, key=lambda run: app.run_stamp(run["run_id"])) if newer else None


def row_progress(case_id: str, index: dict, decisions: dict, running_case: str | None = None) -> dict:
    """사례 하나의 진행 상태. index는 alerts.investigation_index, decisions는 records.latest_decisions의 결과."""
    status = alerts.investigation_status(case_id, index=index)
    base = {"run_id": status["run_id"], "verdict": status["review_status_final"] if status["status"] == alerts.INVESTIGATED else None,
            "decision": None, "investigated": status["status"] == alerts.INVESTIGATED}
    if running_case is not None and case_id == running_case:
        return {**base, "state": RUNNING}
    record = decisions.get(case_id)
    if record is not None:
        newer = newer_completed_run(status["runs"], record.get("run_id"))
        if newer is not None:  # 결정 뒤 다시 조사한 완료 결과: 그 실행을 보이고 결정을 기다린다
            return {**base, "state": NEW_RESULT, "run_id": newer["run_id"], "verdict": newer.get("review_status_final"),
                    "investigated": True, "decision": record.get("decision")}
        state = DECIDED if record.get("validity") == "VALID" else REVIEW_REQUIRED
        return {**base, "state": state, "decision": record.get("decision")}
    if status["status"] == alerts.INVESTIGATED:
        return {**base, "state": AWAITING}
    if status["status"] == alerts.FAILED:
        return {**base, "state": FAILED}
    return {**base, "state": NOT_STARTED}


# ---- 요약 카드 ---------------------------------------------------------------------------------------------------


def prev_month(month: str) -> str:
    """YYYYMM의 앞 달."""
    year, mon = int(month[:4]), int(month[4:])
    return f"{year - 1}12" if mon == 1 else f"{year}{mon - 1:02d}"


def stopped_importing(row: dict) -> bool:
    """점유율 신호가 발동했고 비교월 수입이 없는 경우(비교월 단가가 없고 비교월 점유율이 0이거나 없음)."""
    metrics = row.get("metrics") or {}
    s1 = _dec(metrics.get("s_1"))
    return bool(row.get("share_triggered")) and metrics.get("U_1") is None and (s1 is None or s1 == 0)


def month_summary(rows: list[dict], all_cases: dict | None, month: str, progress_by_case: dict[str, dict]) -> dict:
    """요약 카드 5개의 수: 이번 달 경보·지난달 경보, 단가(오른 것·내린 것), 점유율(수입이 끊긴 나라·늘어난 것·줄어든 것),
    조사 완료(제안별)·조사 중, 내 결정 대기. 지난달 값은 그 달이 경보가 생길 수 있는 첫 달보다 앞이면 None이다."""
    months = sorted({c["month"] for c in (all_cases or {}).get("cases", [])})
    before = prev_month(month)
    last = sum(1 for c in (all_cases or {}).get("cases", []) if c["month"] == before) if months and before >= months[0] else None
    unit = [r for r in rows if r.get("unit_value_triggered")]
    share = [r for r in rows if r.get("share_triggered")]
    up = sum(1 for r in unit if (_dec(r["metrics"].get("r_U")) or 0) > 0)
    down = sum(1 for r in unit if (_dec(r["metrics"].get("r_U")) or 0) < 0)
    s_up = sum(1 for r in share if (_dec(r["metrics"].get("d_s")) or 0) > 0)
    s_down = sum(1 for r in share if (_dec(r["metrics"].get("d_s")) or 0) < 0)
    verdicts: dict[str, int] = {}
    investigated = 0
    for row in rows:
        state = progress_by_case.get(row["case_id"]) or {}
        if state.get("investigated"):
            investigated += 1
            code = state.get("verdict")
            if code:
                verdicts[code] = verdicts.get(code, 0) + 1
    return {
        "month": month, "total": len(rows), "last_month": last,
        "unit": len(unit), "unit_up": up, "unit_down": down,
        "share": len(share), "share_stopped": sum(1 for r in share if stopped_importing(r)), "share_up": s_up, "share_down": s_down,
        "investigated": investigated, "verdicts": {code: verdicts[code] for code in ("MAINTAIN", "MONITOR", "HOLD") if code in verdicts},
        "running": sum(1 for r in rows if (progress_by_case.get(r["case_id"]) or {}).get("state") == RUNNING),
        "awaiting": sum(1 for r in rows if (progress_by_case.get(r["case_id"]) or {}).get("state") in WAITING_STATES),
    }


def summary_cards(summary: dict, lang: str) -> list[dict]:
    """요약 카드 5개(라벨·값·보조 줄·강조). 문구만 만든다."""
    last = t("sum.last_month", lang, n=summary["last_month"]) if summary["last_month"] is not None else t("sum.last_month_none", lang)
    if summary["share_stopped"]:
        share_sub = t("sum.share_stopped", lang, n=summary["share_stopped"])
    else:
        share_sub = t("sum.share_updown", lang, up=summary["share_up"], down=summary["share_down"])
    parts = [t(f"sum.v.{code}", lang, n=n) for code, n in summary["verdicts"].items()]
    if summary["running"]:
        parts.append(t("sum.running", lang, n=summary["running"]))
    return [
        {"label": t("sum.total", lang), "value": t("home.count", lang, n=summary["total"]), "of": None, "sub": last, "accent": False},
        {"label": t("sum.unit", lang), "value": t("home.count", lang, n=summary["unit"]), "of": None,
         "sub": t("sum.unit_updown", lang, up=summary["unit_up"], down=summary["unit_down"]), "accent": False},
        {"label": t("sum.share", lang), "value": t("home.count", lang, n=summary["share"]), "of": None, "sub": share_sub, "accent": False},
        {"label": t("sum.investigated", lang), "value": str(summary["investigated"]), "of": f"/ {summary['total']}",
         "sub": " · ".join(parts) if parts else t("sum.none_yet", lang), "accent": False},
        {"label": t("sum.awaiting", lang), "value": t("home.count", lang, n=summary["awaiting"]), "of": None,
         "sub": t("sum.awaiting_sub", lang), "accent": True},
    ]


# ---- 정렬·필터 ---------------------------------------------------------------------------------------------------


def change_rank(row: dict) -> tuple:
    """변화 큰 순의 열쇠: 단가 발동 행(|r_U| 내림차순) → 점유율만 발동 행(|d_s| 내림차순) → 나머지."""
    metrics = row.get("metrics") or {}
    r_u, d_s = _dec(metrics.get("r_U")), _dec(metrics.get("d_s"))
    if row.get("unit_value_triggered") and r_u is not None:
        return (0, -abs(r_u), row["case_id"])
    if row.get("share_triggered") and d_s is not None:
        return (1, -abs(d_s), row["case_id"])
    return (2, Decimal(0), row["case_id"])


def sort_rows(rows: list[dict], key: str, progress_by_case: dict[str, dict], names: dict[str, str]) -> list[dict]:
    """정렬: change(변화 큰 순, 기본)·item(품목 이름)·partner(상대국 이름)·progress(진행 상태). names는 코드 → 표시 이름."""
    if key == "item":
        return sorted(rows, key=lambda r: (names.get(r["hs6"], r["hs6"]), names.get(r["partner"], r["partner"]), change_rank(r)))
    if key == "partner":
        return sorted(rows, key=lambda r: (names.get(r["partner"], r["partner"]), names.get(r["hs6"], r["hs6"]), change_rank(r)))
    if key == "progress":
        return sorted(rows, key=lambda r: (PROGRESS_ORDER.get((progress_by_case.get(r["case_id"]) or {}).get("state"), 9), change_rank(r)))
    return sorted(rows, key=change_rank)


def filter_rows(rows: list[dict], progress_by_case: dict[str, dict], *, signal: str = "all", progress: str = "all",
                search: str = "", names: dict[str, str] | None = None) -> list[dict]:
    """조회 조건: 바뀐 것(all·unit_value·share), 진행 상태(PROGRESS_FILTERS의 키), 찾기(품목·국가 이름 부분 일치)."""
    names = names or {}
    allowed = PROGRESS_FILTERS.get(progress, PROGRESS_STATES)
    needle = (search or "").strip().lower()
    out = []
    for row in rows:
        if signal == "unit_value" and not row.get("unit_value_triggered"):
            continue
        if signal == "share" and not row.get("share_triggered"):
            continue
        if (progress_by_case.get(row["case_id"]) or {}).get("state", NOT_STARTED) not in allowed:
            continue
        if needle:
            haystack = " ".join([names.get(row["hs6"], ""), names.get(row["partner"], ""), row["partner"]]).lower()
            if needle not in haystack:
                continue
        out.append(row)
    return out


# ---- 셀 문구 -----------------------------------------------------------------------------------------------------


def _arrow(signed: str) -> str:
    return "▲ " if signed.startswith("+") else ("▼ " if signed.startswith("−") else "")


def change_cell(row: dict, lang: str) -> dict:
    """변화내용(윗줄·아랫줄)과 변화 배지. 단가가 발동했으면 단가가 윗줄, 점유율만 발동했으면 점유율이 윗줄이다."""
    m = row.get("metrics") or {}
    u0, u1 = alerts.number_text(m.get("U_0")), alerts.number_text(m.get("U_1"))
    s0, s1 = alerts.number_text(m.get("s_0")), alerts.number_text(m.get("s_1"))
    r_u, d_s = alerts.signed_text(m.get("r_U")), alerts.signed_text(m.get("d_s"))
    unit_text = t("chg.unit", lang, a=u0, b=u1) if u0 is not None and u1 is not None else None
    share_text = t("chg.share", lang, a=s0, b=s1) if s0 is not None and s1 is not None else None
    share_only = bool(row.get("share_triggered")) and not row.get("unit_value_triggered")
    if share_only:
        if stopped_importing(row) and share_text:
            main = t("chg.share_stopped", lang, a=s0, b=s1, month=i18n.month_name(row["month"], lang))
        else:
            main = share_text or t("chg.share_na", lang)
        sub = unit_text or t("chg.unit_na", lang)
        badge = (_arrow(d_s) + t("chg.pp", lang, v=d_s), "sh") if d_s is not None else (t("chg.na", lang), "na")
    else:
        main = unit_text or t("chg.unit_na", lang)
        sub = share_text or t("chg.share_na", lang)
        if r_u is not None:
            badge = (_arrow(r_u) + f"{r_u}%", "up" if r_u.startswith("+") else "down")
        else:
            badge = (t("chg.na", lang), "na")
    return {"main": main, "sub": sub, "badge": badge[0], "badge_kind": badge[1]}


def progress_cell(state: dict, lang: str, clock: str | None = None) -> dict:
    """진행 상태 열(윗줄·아랫줄·종류)과 동작 버튼 종류(start·view·running)."""
    code = state.get("state", NOT_STARTED)
    if code == RUNNING:
        return {"text": t("prog.running", lang, time=clock or "0:00"), "sub": "", "kind": "run", "action": "running"}
    if code == DECIDED:
        return {"text": t("prog.decided", lang, decision=t(f"verdict_lc.{state.get('decision')}", lang)), "sub": "", "kind": "done",
                "action": "view"}
    if code == REVIEW_REQUIRED:
        return {"text": t("prog.review_required", lang), "sub": t("prog.review_required_sub", lang), "kind": "fail", "action": "view"}
    if code == NEW_RESULT:
        return {"text": t("prog.new_result", lang), "sub": t("prog.new_result_sub", lang, verdict=t(f"verdict_lc.{state.get('verdict')}", lang)),
                "kind": "done", "action": "view"}
    if code == AWAITING:
        return {"text": t("prog.awaiting", lang, verdict=t(f"verdict_lc.{state.get('verdict')}", lang)), "sub": t("prog.awaiting_sub", lang),
                "kind": "done", "action": "view"}
    if code == FAILED:
        return {"text": t("prog.failed", lang), "sub": "", "kind": "fail", "action": "start"}
    return {"text": t("prog.not_started", lang), "sub": "", "kind": "", "action": "start"}


def case_option_label(case_id: str, verdict: object, lang: str, countries: dict[str, str]) -> str:
    """조사 완료된 사례 고르기의 표시: "{품목} · {국가} · {YYYY년 M월} · {제안}"(사례 ID·폴더 이름 없이)."""
    parsed = app.parse_case_id(case_id) or {}
    if not parsed:
        return t("load.case_unknown", lang)
    return " · ".join([i18n.item_label(parsed["hs6"], lang), i18n.partner_label(parsed["partner"], countries),
                       i18n.month_label(parsed["month"], lang), t(f"verdict.{verdict}", lang) if verdict else t("verdict.none", lang)])
