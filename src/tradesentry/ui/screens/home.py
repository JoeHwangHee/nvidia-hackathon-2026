"""① 경보 목록(디자인 v2 Main2): 요약 카드 띠 · 조회 조건 카드 · 데이터 표(6열) · 하단 용어 줄과 작은 관리자 화면 링크.

값은 경보 줄(단위 I2 이력 도구 봉투의 지표)·실행 결과 기록·결정 기록에서만 옮긴다(`tradesentry.ui.listing`). HS6 코드·
스냅샷 ID·실행 폴더 이름·상태 코드는 보이지 않는다. "조사 시작"은 배경 조사(`screens.jobs`)를 띄우고 로딩 창을 연다.
"""
import html
import time

import streamlit as st

from tradesentry.ui import alerts, i18n, listing, progress, records
from tradesentry.ui.i18n import t
from tradesentry.ui.screens import common, jobs

COLUMNS = [2.5, 1.1, 3.5, 1.1, 2.3, 1.1]


def _kpis(cards: list[dict]) -> None:
    for column, card in zip(st.columns(5), cards):
        accent = " ts-kpi-accent" if card["accent"] else ""
        of = f' <small>{html.escape(card["of"])}</small>' if card["of"] else ""
        column.markdown(f'<div class="ts-kpi{accent}"><div class="l">{html.escape(card["label"])}</div>'
                        f'<div class="v">{html.escape(card["value"])}{of}</div><div class="s">{html.escape(card["sub"])}</div></div>',
                        unsafe_allow_html=True)


def _label(column, text: str) -> None:
    column.markdown(f'<div class="ts-flabel">{html.escape(text)}</div>', unsafe_allow_html=True)


def _choice(column, name: str, options, prefix: str, lang: str) -> str:
    """조회 조건 선택 하나. 위젯 key에 언어를 넣어 언어를 바꾸면 표시 문구가 바로 바뀌고, 고른 값은 세션에 따로 둬 이어진다."""
    options = list(options)
    stored = st.session_state.get(f"home_{name}_value")
    index = options.index(stored) if stored in options else 0
    value = column.selectbox(t(prefix, lang), options, index=index, format_func=lambda k: t(f"{prefix}.{k}", lang),
                             key=f"home_{name}_{lang}", label_visibility="collapsed")
    st.session_state[f"home_{name}_value"] = value
    return value


def _filters(lang: str, months: list[str]) -> tuple[str, str, str, str, str]:
    """조회 조건 카드: 월(‹ 선택 ›) · 바뀐 것 · 진행 상태 · 정렬 · 찾기. 고른 값(month, signal, progress, sort, search)."""
    with st.container(key="ts_filters"):
        cols = st.columns([0.3, 0.32, 1.25, 0.32, 0.62, 1.0, 0.62, 1.75, 0.42, 1.2, 0.35, 0.42, 1.9], vertical_alignment="center")
        index = months.index(st.session_state["home_month"])
        _label(cols[0], t("flt.month", lang))
        if cols[1].button("‹", disabled=index >= len(months) - 1, key="month_prev"):
            st.session_state["home_month"] = months[index + 1]
            st.rerun()
        month = cols[2].selectbox(t("flt.month", lang), months, index=index, format_func=lambda m: i18n.month_label(m, lang),
                                  key=f"home_month_pick_{lang}_{st.session_state['home_month']}", label_visibility="collapsed")
        if cols[3].button("›", disabled=index <= 0, key="month_next"):
            st.session_state["home_month"] = months[index - 1]
            st.rerun()
        if month != st.session_state["home_month"]:
            st.session_state["home_month"] = month
            st.rerun()
        _label(cols[4], t("flt.signal", lang))
        signal = _choice(cols[5], "signal", listing.SIGNALS, "flt.signal", lang)
        _label(cols[6], t("flt.progress", lang))
        prog = _choice(cols[7], "progress", list(listing.PROGRESS_FILTERS), "flt.progress", lang)
        _label(cols[8], t("flt.sort", lang))
        sort = _choice(cols[9], "sort", listing.SORTS, "flt.sort", lang)
        _label(cols[11], t("flt.find", lang))
        search = cols[12].text_input(t("flt.find", lang), key="home_search", placeholder=t("flt.find_ph", lang),
                                     label_visibility="collapsed")
    return month, signal, prog, sort, search


@st.fragment(run_every=1.0)
def _running_cell(lang: str) -> None:
    """도는 조사의 행: 경과 시간을 1초마다 갱신한다(이 칸만 다시 그린다)."""
    job = jobs.current()
    clock = progress.clock_text(progress.elapsed_seconds(job, time.time())) if job else "0:00"
    st.markdown(f'<div class="ts-cell ts-prog-run"><span class="ts-minispin"></span>{html.escape(t("prog.running", lang, time=clock))}</div>',
                unsafe_allow_html=True)


def _row(row: dict, state: dict, lang: str, countries: dict, snapshot: str) -> None:
    code = state["state"]
    key = "ts_rowaw_" if code == listing.AWAITING else "ts_row_"
    with st.container(key=key + row["case_id"]):
        cells = st.columns(COLUMNS, vertical_alignment="center")
        cells[0].markdown(f'<div class="ts-cell"><b>{html.escape(i18n.item_label(row["hs6"], lang))}</b></div>', unsafe_allow_html=True)
        cells[1].markdown(f'<div class="ts-cell">{html.escape(i18n.partner_label(row["partner"], countries))}</div>', unsafe_allow_html=True)
        change = listing.change_cell(row, lang)
        cells[2].markdown(f'<div class="ts-cell">{html.escape(change["main"])}<small>{html.escape(change["sub"])}</small></div>',
                          unsafe_allow_html=True)
        cells[3].markdown(f'<span class="ts-badge {change["badge_kind"]}">{html.escape(change["badge"])}</span>', unsafe_allow_html=True)
        cell = listing.progress_cell(state, lang)
        if code == listing.RUNNING:
            with cells[4]:
                _running_cell(lang)
        else:
            kind = {"done": "ts-prog-done", "fail": "ts-prog-fail"}.get(cell["kind"], "")
            sub = f'<small>{html.escape(cell["sub"])}</small>' if cell["sub"] else ""
            cells[4].markdown(f'<div class="ts-cell {kind}">{html.escape(cell["text"])}{sub}</div>', unsafe_allow_html=True)
        with cells[5], st.container(horizontal=True, horizontal_alignment="right"):
            if cell["action"] == "running":
                st.button(t("home.btn_running", lang), key=f"running-{row['case_id']}", disabled=True)
            elif cell["action"] == "view":
                if st.button(t("home.btn_view", lang), key=f"view-{row['case_id']}"):
                    common.select_case(row["case_id"], state["run_id"])
                    common.go("case")
            else:
                allowed, _ = common.can_run(row["case_id"])
                busy = jobs.is_running()
                help_text = t("home.locked_running", lang) if busy else (None if allowed else t("home.cannot_run", lang))
                if st.button(t("home.btn_start", lang), key=f"start-{row['case_id']}", type="primary", disabled=busy or not allowed,
                             help=help_text):
                    if jobs.start(row["case_id"], snapshot):
                        st.rerun()


def render() -> None:
    lang, snapshot = common.lang(), common.snapshot_id()
    if not snapshot:
        st.warning(t("app.no_data", lang))
        return
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
    month = st.session_state["home_month"]
    try:
        rows = common.cached_alerts(snapshot, month, common.policy_version())
    except Exception as exc:  # noqa: BLE001
        common.show_error("home.error_alerts", exc)
        return
    index = alerts.investigation_index(common.OUTPUTS_ROOT)
    decisions = records.latest_decisions(common.OUTPUTS_ROOT)
    running = jobs.running_case()
    states = {row["case_id"]: listing.row_progress(row["case_id"], index, decisions, running) for row in rows}
    summary = listing.month_summary(rows, cases, month, states)
    with st.container(key="ts_summary"):
        st.markdown(f'<div class="ts-sum-title"><div class="h">{html.escape(t("sum.title", lang, month=i18n.month_long(month, lang)))}</div>'
                    f'<span>{html.escape(t("sum.desc", lang))}</span></div>', unsafe_allow_html=True)
        _kpis(listing.summary_cards(summary, lang))
    month, signal, prog, sort, search = _filters(lang, months)
    countries = common.countries()
    names = {**countries, **{code: i18n.item_label(code, lang) for code in {r["hs6"] for r in rows}}}
    shown = listing.sort_rows(listing.filter_rows(rows, states, signal=signal, progress=prog, search=search, names=names), sort,
                              states, names)
    with st.container(key="ts_table"):
        head = st.columns(COLUMNS)
        for column, key in zip(head, ("col.item", "col.partner", "col.details", "col.change", "col.progress", "col.action")):
            align = ' style="text-align:right"' if key == "col.action" else ""
            column.markdown(f'<div class="ts-th"{align}>{html.escape(t(key, lang))}</div>', unsafe_allow_html=True)
        if not shown:
            st.info(t("home.filtered_empty", lang))
        for row in shown:
            _row(row, states[row["case_id"]], lang, countries, snapshot)
    common.render_footer()
