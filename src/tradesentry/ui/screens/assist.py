"""③ 결정 기록 · 재조사 · 도움: 진행 단계 4칸, 담당자 결정 폼, 재조사 요청 폼, 사후 확인(비활성), 옆에 이력·용어 도움·더 물어볼 곳."""
import streamlit as st

from tradesentry import app
from tradesentry.ui import alerts, i18n, records
from tradesentry.ui.i18n import t
from tradesentry.ui.screens import common
from tradesentry.ui.screens.case import pick_completed_case, resolve_run

DECISIONS = ("MAINTAIN", "MONITOR", "HOLD")
GLOSSARY = (("glossary.unit", "glossary.unit_desc"), ("glossary.share", "glossary.share_desc"), ("glossary.yoy", "glossary.yoy_desc"),
            ("glossary.mix", "glossary.mix_desc"))


def _signal_text(alert: dict | None, lang: str) -> str:
    signal = alerts.history_signal(alert)
    if signal["kind"] == "unit_value":
        return t("history.alert_unit", lang, value=alerts.signed_text(signal["value"]))
    if signal["kind"] == "share":
        return t("history.alert_share", lang, value=alerts.signed_text(signal["value"]))
    return t("history.alert_other", lang)


def _steps(lang: str, case_month: str, alert: dict | None, latest: dict | None) -> None:
    cols = st.columns(4)
    signal = _signal_text(alert, lang)
    if latest and latest["status"] == alerts.INVESTIGATED:
        verify = t("chip.verified", lang)
        step2 = t("step.2_desc", lang, time=latest["time"], verify=verify, verdict=i18n.verdict_label(latest["review_status_final"], lang))
    else:
        step2 = t("step.2_pending", lang)
    for column, number, head, desc in ((cols[0], 1, t("step.1", lang), t("step.1_desc", lang, month=i18n.month_label(case_month, lang), signal=signal)),
                                       (cols[1], 2, t("step.2", lang), step2),
                                       (cols[2], 3, t("step.3", lang), t("step.3_desc", lang)),
                                       (cols[3], 4, t("step.4", lang), t("step.4_desc", lang))):
        with column, st.container(border=True):
            st.markdown(f"**{number}. {head}**")
            st.caption(desc)


def _decision_form(lang: str, case_id: str, run_id: str, loaded: dict, suggested: object) -> None:
    st.subheader(t("decide.title", lang))
    st.write(t("decide.question", lang))
    execution = (loaded.get("record") or {}).get("execution_status")
    labels = {}
    for code in DECISIONS:
        labels[code] = t("decide.follow", lang, verdict=t(f"verdict.{code}", lang)) if code == suggested else t(f"decide.opt.{code}", lang)
    order = [c for c in DECISIONS if c == suggested] + [c for c in DECISIONS if c != suggested]
    choice = st.radio(t("decide.question", lang), order, format_func=labels.get, key="decide_choice", label_visibility="collapsed",
                      captions=[t(f"decide.desc.{c}", lang) for c in order])
    memo = st.text_area(t("decide.memo", lang), key="decide_memo", height=80)
    reviewer = st.text_input(t("decide.reviewer", lang), key="decide_reviewer")
    st.caption(t("decide.saved_with", lang))
    st.caption(t("decide.review_note", lang))
    if execution != "COMPLETED":
        st.warning(t("decide.reject_not_completed", lang, status=execution))
    if st.button(t("decide.save", lang), type="primary", disabled=execution != "COMPLETED", key="decide_save"):
        try:
            record = records.build_record(loaded, choice, memo, reviewer)
            saved = records.save_record(common.OUTPUTS_ROOT, record)
        except ValueError as exc:
            if "COMPLETED" in str(exc):
                st.error(t("decide.reject_not_completed", lang, status=execution))
            else:
                common.show_error("decide.error", exc)
            return
        except Exception as exc:  # noqa: BLE001 — 이름만 보인다(N13)
            common.show_error("decide.error", exc)
            return
        st.session_state["assist_saved"] = saved["path"]
        st.rerun()


def _reinvestigate(lang: str, case_id: str, snapshot: str | None) -> None:
    st.subheader(t("reinv.title", lang))
    st.write(t("reinv.desc", lang))
    for key in ("reinv.reason1", "reinv.reason2", "reinv.reason3"):
        st.checkbox(t(key, lang), key=key)
    allowed, replay = common.can_run(case_id) if snapshot else (False, None)
    if not app.key_present():
        st.caption(t("reinv.replay_note", lang))
    if not allowed:
        st.caption(t("reinv.cannot", lang))
    running = st.session_state.get("running", False)
    if st.button(t("reinv.button", lang), disabled=not allowed or running or not snapshot, key="reinv_button"):
        result = common.run_investigation(case_id, snapshot)
        new_dirs = result.get("new_run_dirs") or []
        if new_dirs:
            st.session_state["assist_reinv"] = new_dirs[0]
            common.select_case(case_id, new_dirs[0])
        else:
            st.session_state["assist_reinv_error"] = t("reinv.failed", lang, code=result.get("returncode"))
        st.rerun()
    if st.session_state.get("assist_reinv"):
        st.success(t("reinv.done", lang, run=f"outputs/{st.session_state.pop('assist_reinv')}"))
        st.caption(t("reinv.not_score", lang))
    if st.session_state.get("assist_reinv_error"):
        st.error(st.session_state.pop("assist_reinv_error"))


def _followup(lang: str) -> None:
    st.subheader(t("followup.title", lang))
    st.caption("— " + t("followup.locked", lang))
    st.radio(t("followup.question", lang), [t("followup.opt1", lang), t("followup.opt2", lang), t("followup.opt3", lang)],
             index=None, disabled=True, key="followup_choice")
    st.caption(t("followup.desc", lang))
    st.caption(t("followup.demo", lang))


def _history(lang: str, case_id: str, case_month: str, alert: dict | None, runs: list[dict]) -> None:
    st.markdown(f"**{t('history.title', lang)}**")
    st.markdown(f"- {t('history.alert', lang, month=i18n.month_short(case_month), signal=_signal_text(alert, lang))}")
    for run in reversed(runs):  # 오래된 것부터
        if run["status"] == alerts.INVESTIGATED:
            st.markdown(f"- {t('history.run', lang, time=run['time'], verify=t('chip.verified', lang), verdict=i18n.verdict_label(run['review_status_final'], lang), run=run['run_id'])}")
        else:
            st.markdown(f"- {t('history.run_failed', lang, time=run['time'], status=run['execution_status'], run=run['run_id'])}")
    decisions = records.records_for_case(common.OUTPUTS_ROOT, case_id)
    if decisions:
        for record in reversed(decisions):
            reviewer = t("history.by", lang, reviewer=record["reviewer_label"]) if record.get("reviewer_label") else ""
            validity = t("validity." + str(record["validity"]), lang)
            line = t("history.decision", lang, time=record["timestamp"], decision=i18n.verdict_label(record["decision"], lang),
                     reviewer=reviewer, validity=validity)
            st.markdown(f"- {line}")
    else:
        st.markdown(f"- {t('history.no_decision', lang)}")


def render() -> None:
    lang, snapshot = common.lang(), common.snapshot_id()
    case_id = st.session_state.get("selected_case")
    if not case_id:
        st.info(t("assist.none", lang))
        pick_completed_case(lang, snapshot, "assist")
        return
    run_id, runs = resolve_run(case_id)
    parsed = app.parse_case_id(case_id) or {}
    countries = common.countries()
    alert = common.find_alert(case_id)
    latest = next((r for r in runs if r["run_id"] == run_id), runs[0] if runs else None)  # 실행 요약(alerts.run_entry)
    suggested = latest["review_status_final"] if latest and latest["status"] == alerts.INVESTIGATED else None
    st.caption(f"{t('assist.case', lang)} · {i18n.item_label(parsed.get('hs6'), lang)} · {i18n.partner_label(parsed.get('partner'), countries)} · "
               f"{i18n.month_short(parsed.get('month'))} · {t('assist.suggested', lang, verdict=i18n.verdict_label(suggested, lang))}")
    _steps(lang, parsed.get("month", ""), alert, latest)
    main, side = st.columns([2, 1])
    with main:
        if st.session_state.get("assist_saved"):
            st.success(t("decide.saved", lang, path=st.session_state.pop("assist_saved")))
        if run_id:
            try:
                loaded = app.load_run(common.OUTPUTS_ROOT / run_id)
            except Exception as exc:  # noqa: BLE001
                common.show_error("app.error_read", exc)
                loaded = None
            if loaded:
                _decision_form(lang, case_id, run_id, loaded, suggested)
        else:
            st.subheader(t("decide.title", lang))
            st.info(t("decide.no_run", lang))
        st.divider()
        _reinvestigate(lang, case_id, snapshot)
        st.divider()
        _followup(lang)
    with side:
        _history(lang, case_id, parsed.get("month", ""), alert, runs)
        st.markdown(f"**{t('glossary.title', lang)}**")
        for head, desc in GLOSSARY:
            st.markdown(f"**{t(head, lang)}**  \n{t(desc, lang)}")
        st.markdown(f"**{t('glossary.hs6', lang)}**  \n{t('glossary.hs6_desc', lang, hs6=parsed.get('hs6'), item=i18n.item_label(parsed.get('hs6'), lang))}")
        st.markdown(f"**{t('ask.title', lang)}**")
        st.write(t("ask.desc", lang))
        st.code(case_id, language="text")
        if st.button(t("ask.admin_link", lang), key="ask-admin"):
            common.open_admin(run_id)
    common.render_footer()
