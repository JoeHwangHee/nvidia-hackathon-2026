"""③ 결정 기록(디자인 v2 Assist2): 사례 칩 + 제안 → 진행 단계 띠 4칸 → 세 열(결정 폼 | 다시 조사하기 · 사후 확인 | 이 사례의 기록 ·
용어 · 문의할 때 사례 번호).

- "결정 저장" 버튼은 위 입력칸과 같은 폭(`width="stretch"`)이고 안내 문구는 버튼 아래 작게 둔다.
- "다시 조사" 버튼은 오른쪽 정렬이고 배경 조사(`screens.jobs`)를 띄워 로딩 창을 연다. 이유 체크 3개는 표시용이며 저장하지 않는다.
- 사후 확인은 설명만 있고 열리지 않는다(자료 갱신이 없는 데모).
- 진행 단계 띠의 "내 결정"은 결정 기록이 있어도, 결정이 가리키는 실행보다 새로운 완료 실행이 같은 사례에 있으면 다시 "지금"이다
  (`listing.newer_completed_run`, 화면 표시 규칙. 결정 기록의 유효 상태 대조는 바꾸지 않는다).
- 결정 뒤 새 완료 실행이 있으면 기본으로 그 실행을 본다(목록·사례 검토에서 넘어온 선택이 있으면 그것). 더 오래된 실행을 보고
  있으면 "더 새 조사 결과가 있습니다 (시각)" 한 줄과 새 결과로 바꾸는 버튼을 보이고, "내 결정 (지금)"은 가장 새 완료 실행을 볼
  때만 켠다. 결정 저장은 보고 있는 실행을 가리킨다(A1 그대로, 막지 않는다. UI5 `listing.assist_view`).
- "이 사례의 기록"의 정렬은 `listing.order_history`(시각을 읽을 수 없는 줄은 끝에 원래 순서대로)이고, "다시 조사하기" 설명은
  재생 실행이면 "몇 초", 실제 실행이면 "1~2분"이다(UI5).
- 담당자 화면에서 유일하게 사례 ID가 보이는 곳은 "문의할 때 사례 번호" 한 줄이다(디자인대로).
"""
import html

import streamlit as st

from tradesentry import app
from tradesentry.ui import alerts, i18n, listing, records
from tradesentry.ui.i18n import t
from tradesentry.ui.screens import common, jobs
from tradesentry.ui.screens.case import pick_completed_case, resolve_run

DECISIONS = ("MAINTAIN", "MONITOR", "HOLD")
GLOSSARY = (("glossary.unit", "glossary.unit_desc"), ("glossary.share", "glossary.share_desc"), ("glossary.mix", "glossary.mix_desc"))
ASSIST_COLUMNS = [1.25, 1.1, 0.8]


def _signal_text(alert: dict | None, lang: str) -> str | None:
    signal = alerts.history_signal(alert)
    if signal["kind"] == "unit_value":
        return t("signal.unit_change", lang, value=alerts.signed_text(signal["value"]))
    if signal["kind"] == "share":
        return t("signal.share_change", lang, value=alerts.signed_text(signal["value"]))
    return None


def _steps(lang: str, case_month: str, alert: dict | None, latest: dict | None, decided: bool, now: bool) -> None:
    signal = _signal_text(alert, lang)
    month = i18n.month_long(case_month, lang)
    step1 = t("step.1_desc", lang, month=month, signal=signal) if signal else t("step.1_desc_plain", lang, month=month)
    investigated = bool(latest and latest["status"] == alerts.INVESTIGATED)
    step2 = (t("step.2_desc", lang, time=latest["time"], verdict=t(f"verdict_lc.{latest['review_status_final']}", lang))
             if investigated else t("step.2_pending", lang))
    items = ((1, t("step.1", lang), step1, "done"), (2, t("step.2", lang), step2, "done" if investigated else ""),
             (3, t("step.3" if now and not decided else "step.3_done", lang), t("step.3_desc", lang),
              "done" if decided else ("now" if now else "")),
             (4, t("step.4", lang), t("step.4_desc", lang), ""))
    with st.container(key="as_steps"):
        for column, (number, head, desc, state) in zip(st.columns(4), items):
            mark = "✓" if state == "done" else str(number)
            bold = ' class="now"' if state == "now" else ""
            column.markdown(f'<div class="ts-stepbox"><span class="n {state}">{mark}</span><div><b{bold}>{html.escape(head)}</b>'
                            f'<small>{html.escape(desc)}</small></div></div>', unsafe_allow_html=True)


def _decision_form(lang: str, loaded: dict | None, suggested: object) -> None:
    with st.container(key="as_form"):
        st.markdown(f'<div class="ts-sec">{html.escape(t("decide.question", lang))}</div>', unsafe_allow_html=True)
        if st.session_state.pop("assist_saved", None):
            st.success(t("decide.saved", lang))
        if loaded is None:
            st.info(t("decide.no_run", lang))
            return
        execution = (loaded.get("record") or {}).get("execution_status")
        labels = {code: (t("decide.follow", lang, verdict=t(f"verdict_lc.{code}", lang)) if code == suggested else t(f"decide.opt.{code}", lang))
                  for code in DECISIONS}
        order = [c for c in DECISIONS if c == suggested] + [c for c in DECISIONS if c != suggested]
        choice = st.radio(t("decide.question", lang), order, format_func=labels.get, key=f"decide_choice_{lang}",
                          label_visibility="collapsed", captions=[t(f"decide.desc.{c}", lang) for c in order])
        memo = st.text_area(t("decide.memo", lang), key="decide_memo", height=84, placeholder=t("decide.memo_ph", lang))
        reviewer = st.text_input(t("decide.reviewer", lang), key="decide_reviewer", placeholder=t("decide.reviewer_ph", lang))
        completed = execution == "COMPLETED"
        if not completed:
            st.warning(t("decide.reject_not_completed", lang))
        if st.button(t("decide.save", lang), type="primary", disabled=not completed, key="decide_save", width="stretch"):
            try:
                record = records.build_record(loaded, choice, memo, reviewer)
                records.save_record(common.OUTPUTS_ROOT, record)
            except ValueError as exc:
                if "COMPLETED" in str(exc):
                    st.error(t("decide.reject_not_completed", lang))
                else:
                    common.show_error("decide.error", exc)
                return
            except Exception as exc:  # noqa: BLE001 — 이름만 보인다(N13)
                common.show_error("decide.error", exc)
                return
            st.session_state["assist_saved"] = True
            st.rerun()
        st.caption(t("decide.after_note", lang))


def _reinvestigate(lang: str, case_id: str, snapshot: str | None) -> None:
    with st.container(key="as_reinv"):
        st.markdown(f'<div class="ts-sec">{html.escape(t("reinv.title", lang))}</div>', unsafe_allow_html=True)
        allowed, replay = common.can_run(case_id) if snapshot else (False, None)
        st.caption(t(listing.reinvestigate_desc_key(allowed and replay is not None), lang))  # 재생은 몇 초, 실제는 1~2분
        for key in ("reinv.reason1", "reinv.reason2", "reinv.reason3"):
            st.checkbox(t(key, lang), key=key)
        busy = jobs.is_running()
        help_text = t("home.locked_running", lang) if busy else (None if allowed else t("reinv.cannot", lang))
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button(t("reinv.button", lang), disabled=busy or not allowed, key="reinv_button", help=help_text):
                if jobs.start(case_id, snapshot):
                    st.rerun()
        if not allowed and not busy:
            st.caption(t("reinv.cannot", lang))
    with st.container(key="as_follow"):
        st.markdown(f'<div class="ts-sec">{html.escape(t("followup.title", lang))}</div>', unsafe_allow_html=True)
        st.caption(t("followup.desc", lang))


def _history(lang: str, case_id: str, case_month: str, alert: dict | None, runs: list[dict], run_id: str | None) -> None:
    lines = []
    signal = _signal_text(alert, lang)
    month = i18n.month_long(case_month, lang)
    lines.append(t("history.alert", lang, month=month, signal=signal) if signal else t("history.alert_plain", lang, month=month))
    events: list[tuple[str, str]] = []  # (시각 글자, 줄): 조사와 결정을 시각순으로 섞는다(결정 뒤 다시 조사한 결과가 결정 아래에 온다)
    for run in reversed(runs):  # 오래된 것부터
        if run["status"] == alerts.INVESTIGATED:
            line = t("history.run", lang, time=run["time"], verdict=t(f"verdict_lc.{run['review_status_final']}", lang))
        else:
            line = t("history.run_failed", lang, time=run["time"])
        events.append((str(run["time"]), line))
    decisions = records.records_for_case(common.OUTPUTS_ROOT, case_id)
    muted = None
    for record in reversed(decisions):
        reviewer = t("history.by", lang, reviewer=record["reviewer_label"]) if record.get("reviewer_label") else ""
        when = common.time_text(record["timestamp"])
        events.append((str(when), t("history.decision", lang, time=when, decision=t(f"verdict_lc.{record['decision']}", lang),
                                    reviewer=reviewer, validity=t("validity." + str(record["validity"]), lang))))
    lines += listing.order_history(events)  # 시각을 읽을 수 없는 줄은 끝에 원래 순서대로(UI5)
    if not decisions:
        muted = t("history.no_decision", lang)
    with st.container(key="as_hist"):
        st.markdown(f'<div class="ts-sec">{html.escape(t("history.title", lang))}</div>', unsafe_allow_html=True)
        items = "".join(f"<li>{html.escape(line)}</li>" for line in lines)
        if muted:
            items += f'<li class="muted">{html.escape(muted)}</li>'
        st.markdown(f'<ol class="ts-hist">{items}</ol>', unsafe_allow_html=True)
    with st.container(key="as_terms"):
        st.markdown(f'<div class="ts-sec">{html.escape(t("glossary.title", lang))}</div>', unsafe_allow_html=True)
        pairs = "".join(f'<div class="k"><b>{html.escape(t(head, lang))}</b></div><div>{html.escape(t(desc, lang))}</div>'
                        for head, desc in GLOSSARY)
        st.markdown(f'<div class="ts-kv ts-kv-wide">{pairs}</div>', unsafe_allow_html=True)
    with st.container(horizontal=True, vertical_alignment="center", gap="small", key="as_ask"):
        st.markdown(f'<div class="ts-foot">{html.escape(t("ask.line", lang, case_id=case_id))} ·</div>', unsafe_allow_html=True)
        common.admin_link(t("foot.admin", lang), run_id, key="assist_admin")


def render() -> None:
    lang, snapshot = common.lang(), common.snapshot_id()
    case_id = st.session_state.get("selected_case")
    if not case_id:
        st.info(t("assist.none", lang))
        pick_completed_case(lang, snapshot, "assist")
        common.render_footer()
        return
    _, runs = resolve_run(case_id)
    record = records.latest_decisions(common.OUTPUTS_ROOT).get(case_id)
    # 결정 뒤 같은 사례를 다시 조사해 완료된 결과가 있으면 "내 결정"은 다시 지금 할 일이다(이전 결정은 "이 사례의 기록"에 남는다. UI4).
    # 기본 선택은 그 새 결과이고, "지금"은 가장 새 완료 실행을 볼 때만 켠다(UI5)
    view = listing.assist_view(runs, st.session_state.get("selected_run"), record)
    run_id = view["run_id"]
    parsed = app.parse_case_id(case_id) or {}
    countries = common.countries()
    alert = common.find_alert(case_id)
    latest = next((r for r in runs if r["run_id"] == run_id), runs[0] if runs else None)  # 실행 요약(alerts.run_entry)
    suggested = latest["review_status_final"] if latest and latest["status"] == alerts.INVESTIGATED else None
    chip = " · ".join([i18n.item_label(parsed.get("hs6"), lang), i18n.partner_label(parsed.get("partner"), countries),
                       i18n.month_long(parsed.get("month"), lang)])
    verdict = t(f"verdict_lc.{suggested}", lang) if suggested else t("verdict.none", lang)
    with st.container(horizontal=True, horizontal_alignment="right", key="as_chips"):
        st.markdown(f'<span class="ts-chip">{html.escape(chip)}</span><span class="ts-chip ok"><b>'
                    f'{html.escape(t("assist.suggested", lang, verdict=verdict))}</b></span>', unsafe_allow_html=True)
    _steps(lang, parsed.get("month", ""), alert, latest, view["decided"], view["now"])
    if view["older"]:  # 옛 실행을 보고 있다: 새 결과 안내와 바꾸는 버튼(저장은 막지 않는다)
        with st.container(horizontal=True, vertical_alignment="center", key="as_newer"):
            st.markdown(f'<div class="ts-note">{html.escape(t("assist.newer", lang, time=view["newer"]["time"]))}</div>',
                        unsafe_allow_html=True)
            if st.button(t("assist.newer_open", lang), key="assist_newer_open"):
                st.session_state["selected_run"] = view["newer"]["run_id"]
                st.rerun()
    loaded = None
    if run_id:
        try:
            loaded = app.load_run(common.OUTPUTS_ROOT / run_id)
        except Exception as exc:  # noqa: BLE001 — 이름만 보인다(N13)
            common.show_error("app.error_read", exc)
    left, middle, right = st.columns(ASSIST_COLUMNS, gap="medium")
    with left:
        _decision_form(lang, loaded, suggested)
    with middle:
        _reinvestigate(lang, case_id, (latest or {}).get("snapshot_id") or snapshot)  # 그 사례를 조사한 자료로 다시 돈다
    with right:
        _history(lang, case_id, parsed.get("month", ""), alert, runs, run_id)
