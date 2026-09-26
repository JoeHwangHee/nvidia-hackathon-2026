"""② 사례 검토: 경로 → 제목 한 문장 → 칩 → 다음 업무 제안 카드 → 본문 4절 → 옆 3절 → 버튼 2개(보고서 전문·조사 과정)."""
import streamlit as st

from tradesentry.ui import alerts, i18n, plain
from tradesentry.ui.i18n import t
from tradesentry.ui.screens import common


def resolve_run(case_id: str | None) -> tuple[str | None, list[dict]]:
    """선택한 실행 폴더가 없으면 그 사례의 최신 실행을 찾는다. (run_id, 그 사례의 실행 목록)."""
    index = alerts.investigation_index(common.OUTPUTS_ROOT)
    runs = index.get(case_id, {}).get("runs", []) if case_id else []
    run_id = st.session_state.get("selected_run")
    if run_id and (not case_id or any(r["run_id"] == run_id for r in runs)):
        return run_id, runs
    return (runs[0]["run_id"] if runs else None), runs


def render() -> None:
    lang = common.lang()
    case_id = st.session_state.get("selected_case")
    run_id, runs = resolve_run(case_id)
    if run_id is None and case_id is None:
        st.info(t("case.none_selected", lang))
        return
    if run_id is None:
        st.info(t("case.not_investigated", lang, case_id=case_id))
        return
    try:
        model = plain.plain_model(common.OUTPUTS_ROOT / run_id, lang, repo_root=common.REPO_ROOT)
    except Exception as exc:  # noqa: BLE001 — 이름만 보인다(N13)
        common.show_error("app.error_read", exc)
        return
    case, header = model["case"], model["header"]
    if case_id is None:
        st.session_state["selected_case"] = case_id = case["case_id"]
    crumbs = f"{t('nav.home', lang)} › {t('case.crumb_month', lang, month=case['month_label'])} › {case['item']} — {case['partner_name']}"
    st.caption(crumbs)
    if len(runs) > 1:
        picked = st.selectbox(t("case.run_pick", lang, n=len(runs)), [r["run_id"] for r in runs],
                              index=[r["run_id"] for r in runs].index(run_id),
                              format_func=lambda r: f"{alerts.stamp_label(r)} · {r}")
        if picked != run_id:
            st.session_state["selected_run"] = picked
            st.rerun()
    last = st.session_state.get("last_run") or {}
    if (last.get("new_run_dirs") or [None])[0] == run_id:
        st.caption(t("reinv.not_score", lang) + (" " + t("home.replay_note", lang) if last.get("replay") else ""))
    if model["missing"]:
        st.warning(", ".join(model["missing"]))
    st.title(model["title"])
    st.write(" · ".join(f"`{chip}`" for chip in model["chips"]))
    main, side = st.columns([2, 1])
    with side:
        with st.container(border=True):
            st.markdown(f"**{t('case.next_step', lang)}**")
            st.subheader(header["verdict_label"])
            if header["meaning"]:
                st.write(header["meaning"])
            if not header["completed"]:
                st.warning(t("case.conclusion_not_completed", lang, status=header["execution_status"]))
            if st.button(t("case.btn_record", lang), type="primary", disabled=not header["completed"], key="to-assist"):
                common.select_case(case_id, run_id)
                common.go("assist")
    with main:
        st.subheader(t("case.sec_what", lang))
        what = model["what"]
        if what:
            c1, c2 = st.columns(2)
            with c1, st.container(border=True):
                st.caption(what["unit"]["label"])
                st.markdown(f"### {what['unit']['value_text']}")
                st.caption(what["unit"]["note"])
            with c2, st.container(border=True):
                st.caption(what["share"]["label"])
                st.markdown(f"### {what['share']['value_text']}")
                st.caption(what["share"]["note"])
        st.subheader(t("case.sec_found", lang))
        st.caption("— " + t("case.found_note", lang))
        if model["found"]:
            for number, section in enumerate(model["found"], start=1):
                st.markdown(f"**{number}. {section['head']}**")
                for line in section["body"]:
                    st.write(line)
        else:
            st.write(t("case.found_empty", lang))
        st.subheader(t("case.sec_alt", lang))
        alt = model["alternatives"]
        st.caption("— " + alt["note"] + (f" {alt['original_mark']}" if alt["original_mark"] else ""))
        if alt["items"]:
            for item in alt["items"]:
                st.write(f"- {item}")
        else:
            st.write(alt["empty"])
        conclusion = model["conclusion"]
        st.subheader(conclusion["title"])
        if conclusion["not_completed"]:
            st.warning(conclusion["not_completed"])
        elif conclusion["meaning"]:
            st.write(conclusion["meaning"])
        if conclusion["narrative"]:
            st.markdown(f"{t('case.narrative_quote', lang)}{' ' + conclusion['original_mark'] if conclusion['original_mark'] else ''}")
            st.markdown(f"> {conclusion['narrative']}")
        else:
            st.caption(t("case.narrative_empty", lang))
    with side:
        st.markdown(f"**{t('case.sec_meaning', lang)}**")
        for meaning in model["meanings"]:
            mark = f" {t('case.this_case', lang)}" if meaning["current"] else ""
            st.markdown(f"**{meaning['label']}**{mark}  \n{meaning['text']}")
        st.markdown(f"**{t('case.sec_basis', lang)}**")
        for label, value in model["basis"]:
            st.markdown(f"{label}: {value}")
        st.markdown(f"{t('basis.rows', lang)}: ")
        if st.button(t("basis.rows_value", lang), key="rows-admin"):
            common.open_admin(run_id)
        st.markdown(f"**{t('case.sec_caution', lang)}**")
        st.caption(model["caution"])
    b1, b2 = st.columns(2)
    if b1.button(t("case.btn_report", lang), key="full-report"):
        st.session_state["show_report"] = not st.session_state.get("show_report", False)
    if b2.button(t("case.btn_admin", lang), key="admin-process"):
        common.open_admin(run_id)
    if st.session_state.get("show_report"):
        with st.expander(t("case.report_full", lang), expanded=True):
            st.json(model["report"])
    st.caption(f"{t('case.run_label', lang)}: `{model['run_dir']}`")
    common.render_footer()
