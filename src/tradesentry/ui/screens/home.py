"""① 담당자 홈: 월 선택, 요약 4칸, 필터, 경보 표(품목·상대국·단가·점유율·상태·다음 업무 제안·동작), 하단 설명."""
import streamlit as st

from tradesentry.ui import alerts, i18n
from tradesentry.ui.i18n import t
from tradesentry.ui.screens import common

COLUMNS = [2.6, 1.3, 2.4, 2.0, 1.1, 1.6, 1.4]


def _kpi(column, label: str, value: str) -> None:
    column.metric(label, value)


def _unit_cell(row: dict, lang: str) -> tuple[str, str]:
    m = row["metrics"]
    u0, u1, r = alerts.number_text(m["U_0"]), alerts.number_text(m["U_1"]), alerts.signed_text(m["r_U"])
    if u0 is not None and u1 is not None:
        main = f"{u0} → {u1} USD"
    elif u0 is not None:
        main = f"{u0} USD → {t('home.no_import', lang, month=i18n.month_short(row['month']))}"
    elif u1 is not None:
        main = f"{t('home.no_import', lang, month=i18n.month_short(row['baseline_month']))} → {u1} USD"
    else:
        main = t("case.value_missing", lang)
    if r is None:
        badge = t("home.not_comparable", lang)
    else:
        badge = ("▲ " if r.startswith("+") else ("▼ " if r.startswith("−") else "")) + r + "%"
    return main, badge


def _share_cell(row: dict, lang: str) -> tuple[str, str]:
    m = row["metrics"]
    s0, s1, d = alerts.number_text(m["s_0"]), alerts.number_text(m["s_1"]), alerts.signed_text(m["d_s"])
    main = f"{s0}% → {s1}%" if s0 is not None and s1 is not None else t("case.value_missing", lang)
    if d is None:
        badge = t("home.not_comparable", lang)
    elif row["share_triggered"]:
        badge = ("▲ " if d.startswith("+") else ("▼ " if d.startswith("−") else "")) + d + "%p"
    else:
        badge = f"({d}%p)"
    return main, badge


def _start(case_id: str, snapshot: str) -> None:
    result = common.run_investigation(case_id, snapshot)
    new_dirs = result.get("new_run_dirs") or []
    if new_dirs:
        common.select_case(case_id, new_dirs[0])
        common.go("case")
    else:
        st.session_state["home_error"] = t("home.run_failed", common.lang(), code=result.get("returncode"))


def render() -> None:
    lang, snapshot = common.lang(), common.snapshot_id()
    st.title(t("app.title", lang))
    st.caption(t("app.subtitle", lang))
    if not snapshot:
        st.warning(t("app.snapshot_none", lang))
        return
    period = common.cached_period(snapshot)
    if period:
        st.caption(t("app.data_line", lang, start=i18n.month_short(period[0]), end=i18n.month_short(period[1]), snapshot_id=snapshot))
    try:
        cases = common.cached_case_list(snapshot, common.policy_version())
    except Exception as exc:  # noqa: BLE001 — 이름만 보인다(N13)
        common.show_error("home.error_alerts", exc)
        return
    months = alerts.list_months(snapshot, cases=cases)
    if not months:
        st.info(t("home.no_alerts", lang))
        return
    if st.session_state.get("home_month") not in months:
        st.session_state["home_month"] = months[0]
    nav_prev, nav_mid, nav_next = st.columns([1, 6, 1])
    index = months.index(st.session_state["home_month"])
    if nav_prev.button("‹", disabled=index >= len(months) - 1, key="month_prev"):
        st.session_state["home_month"] = months[index + 1]
        st.rerun()
    if nav_next.button("›", disabled=index <= 0, key="month_next"):
        st.session_state["home_month"] = months[index - 1]
        st.rerun()
    month = nav_mid.selectbox(t("home.month_label", lang), months, index=index, format_func=lambda m: i18n.month_label(m, lang),
                              key="home_month_pick", label_visibility="collapsed")
    if month != st.session_state["home_month"]:
        st.session_state["home_month"] = month
        st.rerun()
    try:
        rows = common.cached_alerts(snapshot, month, common.policy_version())
    except Exception as exc:  # noqa: BLE001
        common.show_error("home.error_alerts", exc)
        return
    index_by_case = alerts.investigation_index(common.OUTPUTS_ROOT)
    baseline = rows[0]["baseline_month"] if rows else f"{int(month[:4]) - 1}{month[4:]}"
    thresholds = {}
    try:
        from tradesentry.contract import policy_load
        thresholds = policy_load.load_policy(common.policy_version()).get("thresholds") or {}
    except Exception:  # noqa: BLE001
        thresholds = {}
    st.header(f"{t('home.month_alerts', lang, month=i18n.month_label(month, lang))} · {t('home.count', lang, n=len(rows))}")
    st.write(t("home.intro", lang, baseline=i18n.month_label(baseline, lang), u=alerts.number_text(thresholds.get("unit_value")) or "?",
               s=alerts.number_text(thresholds.get("share")) or "?"))
    summary = alerts.summary(rows, cases, index_by_case)
    k1, k2, k3, k4 = st.columns(4)
    _kpi(k1, t("home.kpi_unit", lang), t("home.count", lang, n=summary["unit_value"]))
    _kpi(k2, t("home.kpi_share", lang), t("home.count", lang, n=summary["share"]))
    _kpi(k3, t("home.kpi_done", lang), f"{summary['investigated']} / {summary['total']}")
    _kpi(k4, t("home.kpi_total", lang), t("home.count", lang, n=summary["all_months"]))
    if st.session_state.get("home_error"):
        st.error(st.session_state.pop("home_error"))
    f1, f2, f3 = st.columns([2, 2, 3])
    signal_options = {"all": t("home.filter_all", lang), "unit_value": t("home.filter_unit", lang), "share": t("home.filter_share", lang)}
    status_options = {"all": t("home.filter_all", lang), alerts.NOT_INVESTIGATED: t("status.NOT_INVESTIGATED", lang),
                      alerts.INVESTIGATED: t("status.INVESTIGATED", lang), alerts.FAILED: t("status.FAILED", lang)}
    signal = f1.radio(t("home.filter_label", lang), list(signal_options), format_func=signal_options.get, horizontal=True, key="home_signal")
    status = f2.radio(t("home.filter_status", lang), list(status_options), format_func=status_options.get, horizontal=True, key="home_status")
    search = f3.text_input(t("home.search", lang), key="home_search")
    countries = common.countries()
    labels = {**countries, **{code: i18n.item_label(code, lang) for code in i18n.HS6_NAMES}}
    shown = alerts.filter_alerts(rows, index_by_case, signal=signal, status=status, search=search, labels=labels)
    header = st.columns(COLUMNS)
    for column, text in zip(header, (t("home.col_item", lang), t("home.col_partner", lang),
                                     t("home.col_unit", lang, baseline=i18n.month_short(baseline), month=i18n.month_short(month)),
                                     t("home.col_share", lang, baseline=i18n.month_short(baseline), month=i18n.month_short(month)),
                                     t("home.col_status", lang), t("home.col_next", lang), t("home.col_action", lang))):
        column.markdown(f"**{text}**")
    if not shown:
        st.info(t("home.filtered_empty", lang))
    running = st.session_state.get("running", False)
    for row in shown:
        state = alerts.investigation_status(row["case_id"], index=index_by_case)
        cells = st.columns(COLUMNS)
        cells[0].markdown(f"{i18n.item_label(row['hs6'], lang)}  \n`{row['hs6']}`")
        cells[1].write(i18n.partner_label(row["partner"], countries))
        u_main, u_badge = _unit_cell(row, lang)
        cells[2].markdown(f"{u_main}  \n**{u_badge}**" if row["unit_value_triggered"] else f"{u_main}  \n{u_badge}")
        s_main, s_badge = _share_cell(row, lang)
        cells[3].markdown(f"{s_main}  \n**{s_badge}**" if row["share_triggered"] else f"{s_main}  \n{s_badge}")
        cells[4].write(t(f"status.{state['status']}", lang))
        cells[5].write(common.verdict_badge(state["review_status_final"]) if state["status"] == alerts.INVESTIGATED else t("verdict.none", lang))
        if state["status"] == alerts.NOT_INVESTIGATED:
            allowed, replay = common.can_run(row["case_id"])
            if cells[6].button(t("home.btn_start", lang), key=f"start-{row['case_id']}", disabled=running or not allowed,
                               help=None if allowed else t("home.cannot_run", lang)):
                _start(row["case_id"], snapshot)
        else:
            if cells[6].button(t("home.btn_view", lang), key=f"view-{row['case_id']}", type="primary"):
                common.select_case(row["case_id"], state["run_id"])
                common.go("case")
            if state["status"] == alerts.FAILED and cells[6].button(t("home.btn_start", lang), key=f"restart-{row['case_id']}",
                                                                    disabled=running or not common.can_run(row["case_id"])[0]):
                _start(row["case_id"], snapshot)
    st.divider()
    st.caption(t("home.footer1", lang))
    st.caption(t("app.disclaimer", lang))
