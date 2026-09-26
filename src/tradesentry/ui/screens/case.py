"""② 사례 검토(디자인 v2 CaseDetail2): 경로 → 제목 한 문장·칩 | 다음 업무 제안 카드 → 본문(무슨 일이 있었나 · 조사에서 확인한 것
· 다른 설명 가능성 · 결론) | 옆(제안이 뜻하는 것 · 근거로 삼은 것 · 읽을 때 유의할 점 · 작은 관리자 화면 링크).

머리 행과 본문 행은 같은 열 비율(`COLUMNS`)을 써서 "다음 업무 제안" 카드가 아래 오른쪽 열과 같은 폭·같은 끝선이 된다.
사례 ID·실행 폴더 이름·HS6 코드·스냅샷 ID·정책 이름·상태 코드는 보이지 않는다. 같은 사례의 다른 조사 결과는 "조사 시각"
선택으로만 고른다. 보고서 요약 원문은 접힌 상태다.
"""
import html

import streamlit as st

from tradesentry.ui import alerts, i18n, listing, plain
from tradesentry.ui.i18n import t
from tradesentry.ui.screens import common

COLUMNS = [2.6, 1]


def resolve_run(case_id: str | None) -> tuple[str | None, list[dict]]:
    """선택한 실행 폴더가 없으면 그 사례의 최신 실행을 찾는다. (run_id, 그 사례의 실행 목록, 새 것부터)."""
    index = alerts.investigation_index(common.OUTPUTS_ROOT)
    runs = index.get(case_id, {}).get("runs", []) if case_id else []
    run_id = st.session_state.get("selected_run")
    if run_id and (not case_id or any(r["run_id"] == run_id for r in runs)):
        return run_id, runs
    return (runs[0]["run_id"] if runs else None), runs


def pick_completed_case(lang: str, snapshot: str | None, key: str) -> None:
    """빈 상태: 현재 자료의 조사 완료 사례(새 것부터)를 골라 연다. 표시는 품목 · 국가 · 월 · 제안(사례 ID·폴더 이름 없이)."""
    runs = alerts.completed_runs(alerts.investigation_index(common.OUTPUTS_ROOT), snapshot)
    latest: dict[str, dict] = {}
    for run in runs:  # 사례마다 최신 조사 하나
        latest.setdefault(run["case_id"], run)
    if not latest:
        st.caption(t("case.pick_none", lang))
        return
    countries = common.countries()
    options = list(latest)
    col_pick, col_open = st.columns([4, 1], vertical_alignment="bottom")
    chosen = col_pick.selectbox(t("case.pick_label", lang), options, key=f"pick_case_{key}_{lang}",
                                format_func=lambda c: listing.case_option_label(c, latest[c]["review_status_final"], lang, countries))
    if col_open.button(t("case.pick_open", lang), key=f"pick_open_{key}"):
        common.select_case(chosen, latest[chosen]["run_id"])
        st.rerun()


def run_period(run: dict | None) -> tuple[str, str] | None:
    snapshot = (run or {}).get("snapshot_id")
    if not isinstance(snapshot, str):
        return None
    try:
        return common.cached_period(snapshot)
    except Exception:  # noqa: BLE001 — 기간을 못 읽으면 기간 없는 문구를 쓴다
        return None


def _run_picker(lang: str, run_id: str, runs: list[dict]) -> None:
    ids = [r["run_id"] for r in runs]
    labels = {r["run_id"]: (t("case.run_latest", lang, time=r["time"]) if i == 0 else r["time"]) for i, r in enumerate(runs)}
    col, _ = st.columns([1.2, 3])
    picked = col.selectbox(t("case.run_pick", lang), ids, index=ids.index(run_id), format_func=labels.get, key=f"case_run_pick_{lang}")
    if picked != run_id:
        st.session_state["selected_run"] = picked
        st.rerun()


def _what(model: dict, lang: str) -> None:
    what = model["what"]
    with st.container(key="case_what"):
        st.markdown(f'<div class="ts-sec">{html.escape(t("case.sec_what", lang))}</div>', unsafe_allow_html=True)
        if not what:
            st.write(t("case.found_empty", lang))
            return
        c1, c2 = st.columns(2)
        for column, part in ((c1, what["unit"]), (c2, what["share"])):
            column.markdown(f'<div class="ts-what"><div class="l">{html.escape(part["label"])}</div>'
                            f'<div class="v">{html.escape(part["value_text"])}</div><div class="s">{html.escape(part["note"])}</div></div>',
                            unsafe_allow_html=True)


def _found(model: dict, lang: str) -> None:
    with st.container(key="case_found"):
        st.markdown(f'<div class="ts-sec">{html.escape(t("case.sec_found", lang))}</div>', unsafe_allow_html=True)
        if not model["found"]:
            st.write(t("case.found_empty", lang))
            return
        items = []
        for section in model["found"]:
            body = " ".join(html.escape(line) for line in section["body"])
            items.append(f"<li><b>{html.escape(section['head'])}</b> {body}</li>")
        st.markdown(f'<ol class="ts-found">{"".join(items)}</ol>', unsafe_allow_html=True)


def _alternatives(model: dict, lang: str) -> None:
    alt = model["alternatives"]
    with st.container(key="case_alt"):
        st.markdown(f'<div class="ts-sec">{html.escape(t("case.sec_alt", lang))} <small>— {html.escape(alt["note"])}'
                    f'{" " + html.escape(alt["original_mark"]) if alt["original_mark"] and alt["items"] else ""}</small></div>',
                    unsafe_allow_html=True)
        if alt["items"]:
            st.markdown("<ul class='ts-found'>" + "".join(f"<li>{html.escape(item)}</li>" for item in alt["items"]) + "</ul>",
                        unsafe_allow_html=True)
        else:
            st.write(alt["empty"])


def _conclusion(model: dict, lang: str) -> None:
    conclusion = model["conclusion"]
    with st.container(key="case_conc"):
        st.markdown(f'<div class="ts-sec">{html.escape(conclusion["title"])}</div>', unsafe_allow_html=True)
        if conclusion["not_completed"]:
            st.write(conclusion["not_completed"])
        elif conclusion["meaning"]:
            st.write(conclusion["meaning"])
        if conclusion["narrative"]:
            with st.expander(t("case.narrative_quote", lang), expanded=False):
                st.write(conclusion["narrative"])


def _side(model: dict, lang: str, run_id: str) -> None:
    with st.container(key="case_meaning"):
        st.markdown(f'<div class="ts-sec">{html.escape(t("case.sec_meaning", lang))}</div>', unsafe_allow_html=True)
        rows = []
        for meaning in model["meanings"]:
            mark = f" {html.escape(t('case.this_case', lang))}" if meaning["current"] else ""
            cls = "ts-mean cur" if meaning["current"] else "ts-mean"
            rows.append(f'<div class="{cls}"><b class="ts-v-{meaning["code"]}">{html.escape(meaning["label"])}</b> — '
                        f'{html.escape(meaning["text"])}{mark}</div>')
        st.markdown("".join(rows), unsafe_allow_html=True)
    with st.container(key="case_basis"):
        st.markdown(f'<div class="ts-sec">{html.escape(t("case.sec_basis", lang))}</div>', unsafe_allow_html=True)
        pairs = "".join(f'<div class="k">{html.escape(k)}</div><div>{html.escape(v)}</div>' for k, v in model["basis"])
        st.markdown(f'<div class="ts-kv">{pairs}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ts-caution"><b>{html.escape(t("case.sec_caution", lang))}</b><br>{html.escape(model["caution"])}</div>',
                unsafe_allow_html=True)
    with st.container(horizontal=True, horizontal_alignment="right"):
        common.admin_link(t("case.admin_link", lang), run_id, key="case_admin")


def render() -> None:
    lang = common.lang()
    case_id = st.session_state.get("selected_case")
    run_id, runs = resolve_run(case_id)
    if run_id is None:
        st.info(t("case.none_selected", lang) if case_id is None else t("case.not_investigated", lang))
        pick_completed_case(lang, common.snapshot_id(), "case")
        common.render_footer()
        return
    run = next((r for r in runs if r["run_id"] == run_id), None)
    if run is None:
        run = alerts.run_entry(common.OUTPUTS_ROOT, run_id)
    position = (next((i for i, r in enumerate(runs) if r["run_id"] == run_id), 0), len(runs)) if runs else None
    try:
        model = plain.plain_model(common.OUTPUTS_ROOT / run_id, lang, repo_root=common.REPO_ROOT, period=run_period(run),
                                  run_position=position)
    except Exception as exc:  # noqa: BLE001 — 이름만 보인다(N13)
        common.show_error("app.error_read", exc)
        return
    case, header = model["case"], model["header"]
    if case_id is None:
        st.session_state["selected_case"] = case_id = case["case_id"]
    st.markdown(f'<div class="ts-crumb">{html.escape(t("case.crumb_home", lang))} › {html.escape(case["month_label"])} › '
                f'{html.escape(case["item"])} — {html.escape(case["partner_name"])}</div>', unsafe_allow_html=True)
    head_left, head_right = st.columns(COLUMNS, gap="medium")
    with head_left:
        st.markdown(f'<div class="ts-title">{html.escape(model["title"])}</div>', unsafe_allow_html=True)
        chips = "".join(f'<span class="ts-chip{" ok" if chip["ok"] else ""}">{html.escape(chip["text"])}</span>' for chip in model["chips"])
        st.markdown(f"<div>{chips}</div>", unsafe_allow_html=True)
        if len(runs) > 1:
            _run_picker(lang, run_id, runs)
    with head_right, st.container(key="case_next"):
        st.markdown(f'<div class="ts-flabel">{html.escape(t("case.next_step", lang))}</div>', unsafe_allow_html=True)
        verdict = header["verdict"] or ""
        st.markdown(f'<span class="ts-verdict {html.escape(verdict)}">{html.escape(header["verdict_label"])}</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="ts-cell">{html.escape(header["meaning"] or model["conclusion"]["not_completed"] or "")}</div>',
                    unsafe_allow_html=True)
        if st.button(t("case.btn_record", lang), type="primary", disabled=not header["completed"], key="to-assist", width="stretch"):
            common.select_case(case_id, run_id)
            common.go("assist")
    main, side = st.columns(COLUMNS, gap="medium")
    with main:
        _what(model, lang)
        _found(model, lang)
        _alternatives(model, lang)
        _conclusion(model, lang)
    with side:
        _side(model, lang, run_id)
