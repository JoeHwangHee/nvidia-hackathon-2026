"""사례 검토 화면의 담당자용 모형(순수 논리, streamlit 없음).

실행 폴더 하나(보고서 `reports_render_ko-*.json` + 실행 결과 기록 + trace)를 화면 단위 `app.screen_model`로 읽고, 그 위에 평이한
문장을 만든다. **숫자는 typed claim과 trace의 검증된 지표(app.trigger_table·chart_data·claims_table)에서만 옮기고 다시
계산하지 않는다.** 방향·크기 구간은 claim 값의 부호와 절댓값을 비교해 고를 뿐이다.

절 구성(디자인 정본 v2 CaseDetail2): 제목 한 문장 → 칩 → 다음 업무 제안 → 무슨 일이 있었나 → 조사에서 확인한 것(있는 claim만)
→ 다른 설명 가능성(hypotheses 원문) → 결론(판정 + narrative 원문, 화면에서는 접힌 상태) → 제안 3종의 뜻 → 근거로 삼은 것 →
유의할 점. EN 모드에서는 틀 문장만 영어이고 narrative·hypotheses 원문은 한국어 그대로 두고 "(Korean original)"을 붙인다.
담당자 화면에 보이는 문구(제목·칩·절·근거)에는 HS6·HS10 코드, 스냅샷 ID, 실행 폴더 이름, 정책 이름, 해시, 상태 코드를 넣지
않는다(UI3). 그 값들은 모형의 `header`·`case`에만 두고(결정 기록 저장·관리자 화면 이동용) 화면 함수가 보이지 않는다.
"""
from decimal import Decimal
from pathlib import Path

from tradesentry import app
from tradesentry.reports import claims as claims_unit
from tradesentry.ui import alerts, i18n
from tradesentry.ui.i18n import t

REPO_ROOT = app.REPO_ROOT
DECOMP = ("within_effect", "mix_effect", "residual")


def _decimal(value: object) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, Decimal)):
        return Decimal(value)
    try:
        return Decimal(str(value))
    except (ArithmeticError, ValueError, TypeError):
        return None


def band_key(r_u: object) -> str | None:
    """r_U 절댓값의 크기 구간: 30~40 눈에 띄게, 40~60 절반 가까이, 60~100 크게, 100 이상 두 배 넘게(오를 때만 뜻이 있다)."""
    value = _decimal(r_u)
    if value is None:
        return None
    size = abs(value)
    if size >= 100:
        return "band.double" if value > 0 else "band.large"
    if size > 60:
        return "band.large"
    if size >= 40:
        return "band.near_half"
    return "band.notable"


def title_sentence(lang: str, item: str, partner: str, unit_row: dict | None, share_row: dict | None) -> str:
    """제목 한 문장. 단가 신호가 발동했으면 단가 문장, 아니면 점유율 문장. 값이 없으면 비교 불가 문장."""
    fields = {"item": item, "partner": partner}
    unit_on = bool(unit_row and unit_row.get("triggered"))
    share_on = bool(share_row and share_row.get("triggered"))
    if unit_on or not share_on:
        value = _decimal(unit_row.get("value")) if unit_row else None
        if value is None:
            return t("case.title_na", lang, **fields)
        band = band_key(value)
        if value < 0:
            return t("case.title_down", lang, band=t(band, lang), **fields)
        if value > 0:
            return t("case.title_up", lang, band=t(band, lang), **fields)
        return t("case.title_flat", lang, **fields)
    value = _decimal(share_row.get("value")) if share_row else None
    if value is None:
        return t("case.title_share_na", lang, **fields)
    return t("case.title_share_up" if value > 0 else "case.title_share_down", lang, **fields)


def _threshold_text(value: object) -> str:
    return alerts.number_text(value) or "?"


def what_happened(model: dict, lang: str, partner_name: str) -> dict:
    """무슨 일이 있었나: 단가 변화율(r_U)과 점유율(s 두 달, d_s), 정책 기준값, 발동 여부. 값은 app.trigger_table·chart_data에서."""
    rows = {row["signal"]: row for row in model["triggers"]}
    unit, share = rows.get("unit_value"), rows.get("share")
    case = model["case"]
    bars = (model["chart"]["bars"] or {}).get("share")
    s0 = alerts.number_text(bars[0]["value"]) if bars else None
    s1 = alerts.number_text(bars[1]["value"]) if bars else None
    unit_value = alerts.signed_text(unit["value"]) if unit else None
    unit_thr = _threshold_text(unit["threshold"]) if unit else "?"
    arrow = ("▲ " if unit_value.startswith("+") else ("▼ " if unit_value.startswith("−") else "")) if unit_value else ""
    if unit and unit["triggered"] is True:
        unit_note = t("case.threshold_hit", lang, thr=unit_thr)
    elif unit and unit["triggered"] is False:
        unit_note = t("case.threshold_miss", lang, thr=unit_thr)
    else:
        unit_note = t("case.threshold_unknown", lang)
    d_s = alerts.signed_text(share["value"]) if share else None
    share_thr = _threshold_text(share["threshold"]) if share else "?"
    if share and share["triggered"] is True:
        share_note = t("case.share_hit", lang, d=d_s or t("case.value_missing", lang), thr=share_thr)
    elif share and share["triggered"] is False:
        share_note = t("case.share_miss", lang, d=d_s or t("case.value_missing", lang), thr=share_thr)
    else:
        share_note = t("case.threshold_unknown", lang)
    return {
        "unit": {"label": t("case.unit_label", lang), "value": unit_value,
                 "value_text": (arrow + unit_value + "%") if unit_value else t("case.not_comparable", lang),
                 "triggered": unit["triggered"] if unit else None, "threshold": unit_thr, "note": unit_note,
                 "status": unit["signal_status"] if unit else None},
        "share": {"label": t("case.share_label", lang, partner=partner_name),
                  "s0": s0, "s1": s1, "value": d_s,
                  "value_text": (f"{s0}% → {s1}%" if s0 and s1 else t("case.value_missing", lang)),
                  "triggered": share["triggered"] if share else None, "threshold": share_thr, "note": share_note,
                  "status": share["signal_status"] if share else None},
    }


def _dir_key(direction: object, value: Decimal | None) -> str:
    if direction == "UP" or (direction is None and value is not None and value > 0):
        return "dir.up"
    if direction == "DOWN" or (direction is None and value is not None and value < 0):
        return "dir.down"
    return "dir.flat"


def findings(model: dict, lang: str, countries: dict[str, str]) -> list[dict]:
    """조사에서 확인한 것: 있는 claim만 절로 만든다(decomposition → comparison → share → HS10 하위품목 → 자료 상태)."""
    case = model["case"]
    partner = case.get("partner")
    signals = model["header"].get("signal_status") or {}
    claims = [c for c in model["claims"] if c.get("claim_id") is not None]
    sections: list[dict] = []

    decomposition = {c["metric"]: c for c in claims if c.get("claim_type") == "decomposition" and c.get("partner") == partner
                     and c.get("metric") in DECOMP}
    if decomposition:
        status = signals.get("unit_value") if isinstance(signals, dict) else None
        head_key = f"case.decomp_head.{status}" if f"case.decomp_head.{status}" in i18n.STRINGS else "case.decomp_head.other"
        values = {name: (alerts.signed_text(decomposition[name]["value"]) if name in decomposition else "—") for name in DECOMP}
        sections.append({"kind": "decomposition", "head": t(head_key, lang),
                         "body": [t("case.decomp_body", lang, within=values["within_effect"], mix=values["mix_effect"],
                                    residual=values["residual"])],
                         "claim_ids": [decomposition[n]["claim_id"] for n in DECOMP if n in decomposition]})

    comparisons = [c for c in claims if c.get("claim_type") == "comparison"]
    if comparisons:
        body, ids, any_rate = [], [], False
        for claim in comparisons:
            name = i18n.partner_label(claim.get("partner"), countries)
            value = _decimal(claim.get("value"))
            shown = alerts.signed_text(claim.get("value")) or t("case.value_missing", lang)
            if claim.get("metric") == "r_U":
                any_rate = True
                body.append(t("case.compare_item", lang, partner=name, value=shown, dir=t(_dir_key(claim.get("direction"), value), lang)))
            elif claim.get("metric") == "d_s":
                body.append(t("case.compare_share_item", lang, partner=name, value=shown))
            else:
                body.append(t("case.compare_value_item", lang, partner=name, value=shown, unit=str(claim.get("unit") or "")))
            ids.append(claim["claim_id"])
        if any_rate:
            body.append(t("case.compare_note", lang))
        sections.append({"kind": "comparison", "head": t("case.compare_head", lang), "body": body, "claim_ids": ids})

    share_claims = [c for c in claims if c.get("partner") == partner and c.get("claim_type") in ("share", "share_change")]
    if share_claims:
        status = signals.get("share") if isinstance(signals, dict) else None
        head_key = "case.share_head.NOT_TRIGGERED" if status == "NOT_TRIGGERED" else "case.share_head.other"
        by_period = {c.get("period"): c for c in share_claims if c.get("metric") == "s"}
        s0 = by_period.get(case.get("baseline_month"))
        s1 = by_period.get(case.get("month"))
        share_row = next((row for row in model["triggers"] if row["signal"] == "share"), None)
        thr = _threshold_text(share_row["threshold"]) if share_row else "?"
        rel = t("rel.at_or_above" if share_row and share_row.get("triggered") else "rel.below", lang)
        body = []
        if s0 is not None and s1 is not None:
            body.append(t("case.share_body", lang, s0=alerts.number_text(s0["value"]), s1=alerts.number_text(s1["value"]), thr=thr, rel=rel))
        for claim in share_claims:
            if claim.get("metric") == "d_s":
                body.append(t("case.compare_share_item", lang, partner=i18n.partner_label(partner, countries),
                              value=alerts.signed_text(claim.get("value")) or t("case.value_missing", lang)))
        sections.append({"kind": "share", "head": t(head_key, lang), "body": body, "claim_ids": [c["claim_id"] for c in share_claims]})

    sub_items = [c for c in claims if isinstance(c.get("metric"), str) and c["metric"].startswith("r_U@") and c.get("partner") == partner]
    if sub_items:
        sections.append({"kind": "sub_items", "head": t("case.sub_head", lang),
                         "body": [t("case.sub_item", lang, n=number,  # HS10 코드는 HS6 코드를 품어 보이지 않는다(UI3)
                                    value=alerts.signed_text(c.get("value")) or t("case.value_missing", lang))
                                  for number, c in enumerate(sub_items, start=1)],
                         "claim_ids": [c["claim_id"] for c in sub_items]})

    statuses = [c for c in claims if c.get("claim_type") == "data_status"]
    if statuses:
        body = []
        for claim in statuses:
            code = claim.get("value")
            label = t(f"dstat.{code}", lang) if code in claims_unit.STATUS_LABEL else t("dstat.other", lang)
            body.append(t("case.data_item", lang, partner=i18n.partner_label(claim.get("partner"), countries),
                          period=i18n.month_long(claim.get("period"), lang), status=label))
        sections.append({"kind": "data_status", "head": t("case.data_head", lang), "body": body,
                         "claim_ids": [c["claim_id"] for c in statuses]})
    return sections


def meanings(lang: str, current: object) -> list[dict]:
    return [{"code": code, "label": t(f"verdict.{code}", lang), "text": t(f"define.{code}", lang), "current": code == current}
            for code in ("MAINTAIN", "MONITOR", "HOLD")]


def verification(model: dict, lang: str) -> dict:
    """검증 요약: COMPLETED이고 검증기 기록이 없으면 "사실 주장 N개 검증 통과", 아니면 기록 건수를 함께 적는다."""
    n = len([c for c in model["claims"] if c.get("claim_id") is not None])
    m = len(model["validator_findings"])
    completed = model["header"].get("execution_status") == "COMPLETED"
    ok = completed and m == 0
    return {"ok": ok, "claims": n, "findings": m,
            "text": t("basis.verify_value", lang, n=n) if ok else t("basis.verify_findings", lang, n=n, m=m),
            "chip": t("chip.verified", lang) if ok else t("chip.findings", lang, n=m)}


def run_position_chip(lang: str, position: tuple[int, int] | None) -> str:
    """조사 칩의 괄호: (최신, N회 중) / (k번째, N회 중). position은 (새 것부터 0으로 센 순번, 전체 수)."""
    if not position or position[1] <= 1:
        return ""
    index, total = position
    return " " + (t("chip.pos_latest", lang, n=total) if index == 0 else t("chip.pos_older", lang, k=total - index, n=total))


def plain_model(run_dir: Path, lang: str = i18n.DEFAULT_LANG, *, repo_root: Path = REPO_ROOT,
                period: tuple[str, str] | None = None, run_position: tuple[int, int] | None = None) -> dict:
    """실행 폴더 하나 → 담당자용 모형. 근거 ID는 풀지 않는다(관리자 화면의 몫). 절대 경로는 넣지 않는다. period는 자료 기간
    (첫 달, 끝 달. 부르는 쪽이 스냅샷에서 읽어 준다), run_position은 그 사례의 조사 가운데 이 조사의 순번(칩 괄호용)이다."""
    model = app.screen_model(run_dir, repo_root=repo_root, resolve_rows=False)
    countries = i18n.load_country_names(repo_root, lang)
    case, header = model["case"], model["header"]
    parsed = bool(case.get("parsed"))
    hs6, partner, month, baseline = case.get("hs6"), case.get("partner"), case.get("month"), case.get("baseline_month")
    item = i18n.item_label(hs6, lang)
    partner_name = i18n.partner_label(partner, countries)
    rows = {row["signal"]: row for row in model["triggers"]}
    completed = header.get("execution_status") == "COMPLETED"
    verdict = header["status_after"]["code"] if completed else None
    verify = verification(model, lang)
    thresholds = model["thresholds"] or {}
    what = what_happened(model, lang, partner_name) if parsed else None
    chips = [{"text": t("chip.alert_month", lang, month=i18n.month_long(month, lang)), "ok": False},
             {"text": t("chip.baseline", lang, month=i18n.month_long(baseline, lang)), "ok": False},
             {"text": t("chip.investigated", lang, time=alerts.stamp_label(model["run_id"])) + run_position_chip(lang, run_position),
              "ok": False},
             {"text": verify["chip"] if completed else t("chip.not_completed", lang), "ok": bool(verify["ok"])}]
    narrative = model["narrative"]
    hypotheses = [h for h in model["hypotheses"] if isinstance(h, str)]
    original = t("case.korean_original", lang) if lang != "ko" else None
    data_value = (t("basis.data_value", lang, start=i18n.month_long(period[0], lang), end=i18n.month_long(period[1], lang))
                  if period else t("basis.data_value_na", lang))
    basis = [
        (t("basis.data", lang), data_value),
        (t("basis.rule", lang), t("basis.rule_value", lang, u=_threshold_text(thresholds.get("unit_value")),
                                 s=_threshold_text(thresholds.get("share")))),
        (t("basis.method", lang), t("basis.method_value", lang)),
        (t("basis.verify", lang), verify["text"]),
    ]
    return {
        "run_id": model["run_id"], "run_dir": model["run_dir"], "missing": model["missing"],
        "case": {"case_id": case.get("case_id"), "parsed": parsed, "hs6": hs6, "partner": partner, "month": month,
                 "baseline_month": baseline, "item": item, "partner_name": partner_name,
                 "month_label": i18n.month_long(month, lang), "baseline_label": i18n.month_long(baseline, lang)},
        "header": {"execution_status": header.get("execution_status"), "completed": completed, "verdict": verdict,
                   "verdict_label": i18n.verdict_label(verdict, lang),
                   "meaning": t(f"meaning.{verdict}", lang) if verdict in ("MAINTAIN", "MONITOR", "HOLD") else "",
                   "signal_status": header.get("signal_status"), "snapshot_id": header.get("snapshot_id"),
                   "policy_version": header.get("policy_version"), "code_version": header.get("code_version"),
                   "report_hash": header.get("report_hash"), "created_at": header.get("created_at"),
                   "investigated_time": alerts.stamp_label(model["run_id"]), "unresolved_evidence": header.get("unresolved_evidence")},
        "title": title_sentence(lang, item, partner_name, rows.get("unit_value"), rows.get("share")) if parsed
        else t("case.title_unknown", lang),
        "chips": chips,
        "verified": verify,
        "what": what,
        "found": findings(model, lang, countries),
        "alternatives": {"items": hypotheses, "note": t("case.alt_note", lang), "empty": t("case.alt_empty", lang),
                         "original_mark": original},
        "conclusion": {"title": t("case.sec_conclusion", lang, verdict=i18n.verdict_label(verdict, lang)) if completed
                       else t("case.sec_conclusion", lang, verdict=t("verdict.none", lang)),
                       "meaning": t(f"meaning.{verdict}", lang) if verdict in ("MAINTAIN", "MONITOR", "HOLD") else "",
                       "narrative": narrative if isinstance(narrative, str) and narrative else None,
                       "original_mark": original,
                       "not_completed": None if completed else t("case.conclusion_not_completed", lang)},
        "meanings": meanings(lang, verdict),
        "basis": basis,
        "caution": t("case.caution", lang),
        "report": model_report(model),
        "thresholds": thresholds,
    }


def model_report(model: dict) -> dict:
    """보고서 전문 보기용(한국어 원문): 주장·설명·가설·검증기 기록. 값은 문자열 표기로 둔다(Decimal 보존)."""
    def plain(value: object) -> object:
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, list):
            return [plain(v) for v in value]
        if isinstance(value, dict):
            return {k: plain(v) for k, v in value.items()}
        return value
    return {"claims": plain(model["claims"]), "narrative": model["narrative"], "hypotheses": model["hypotheses"],
            "validator_findings": plain(model["validator_findings"])}
