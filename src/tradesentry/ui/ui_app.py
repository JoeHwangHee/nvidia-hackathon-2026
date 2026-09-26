"""담당자용 화면 진입 스크립트(UI2 → UI3 v2): 페이지 4개 — 경보 목록 · 사례 검토 · 결정 기록 · 관리자 화면(기존 app.py).

실행(저장소 루트에서. streamlit은 lock 밖 `--with`다, 결정 기록 20260926-0732 ①):
    uv run --locked --with "streamlit==1.64.0" streamlit run src/tradesentry/ui/ui_app.py --client.showErrorDetails=false --server.port 8502

- 사이드바 메뉴는 쓰지 않는다(`st.navigation(..., position="hidden")`). 모든 페이지 위에 머리 띠(브랜드 · 부제 · 페이지 링크 3개 ·
  자료 기간 한 줄 · 언어 전환)를 그린다. 관리자 화면은 담당자 페이지 하단의 작은 링크로만 들어간다.
- 스냅샷 선택은 담당자 화면에 없다. 기본값은 정본 빌드가 있는 실자료(`alerts.default_snapshot`). 관리자 페이지일 때만 사이드바에
  "담당자 화면 자료(스냅샷)" 선택을 둔다. 확인용 URL 질의 `?snapshot=<id>`는 `app.list_snapshots`에 있는 값만 받는다.
- 배경 조사: 페이지를 그리기 전에 상태를 읽어(`screens.jobs.route`) 로딩 창이 떠 있는 채로 끝났으면 사례 검토로 옮기고, 페이지
  본문 뒤에 로딩 창·조사 중 표시(`screens.jobs.render_layer`)를 그린다(위치는 CSS로 고정, 어느 페이지에서도 뜬다).
- 관리자용 페이지는 `st.Page("../app.py")`(진입 스크립트 폴더 기준 상대 경로)로 감싼다. app.py를 고치지 않는다.
- 이 스크립트는 `.env`를 읽지 않고 NIM을 직접 부르지 않는다. 예외는 이름만 보인다(N13). `outputs/sealed/`는 나열·표시하지 않는다.
- 위치: 자료 계약 §10.3 N2가 패키지 밖 모듈을 `ingest.py`·`app.py` 둘로 고정하므로 진입 스크립트도 `ui/` 패키지 안에 둔다.
"""
import html
from pathlib import Path

import streamlit as st

from tradesentry import app
from tradesentry.ui import alerts, i18n
from tradesentry.ui.i18n import t
from tradesentry.ui.screens import assist, case, common, home, jobs, style

ADMIN_SCRIPT = Path("..") / "app.py"  # 진입 스크립트(src/tradesentry/ui/) 기준 → src/tradesentry/app.py


def _snapshot_state() -> list[str]:
    """스냅샷 기본값과 URL 질의(?snapshot=)를 세션에 반영한다. 목록에 없는 값은 무시한다."""
    snapshots = app.list_snapshots(common.SNAPSHOTS_ROOT)
    asked = st.query_params.get("snapshot")
    if isinstance(asked, str) and asked in snapshots and st.session_state.get("snapshot_query") != asked:
        st.session_state["snapshot_query"] = asked
        st.session_state["snapshot_id"] = asked
        st.session_state.pop("home_month", None)
    if st.session_state.get("snapshot_id") not in snapshots:
        st.session_state["snapshot_id"] = alerts.default_snapshot(snapshots)
    return snapshots


def _admin_sidebar(snapshots: list[str], lang: str) -> None:
    """관리자 페이지에서만: 담당자 화면이 쓸 자료(스냅샷) 선택(시험·시연용)."""
    with st.sidebar:
        if not snapshots:
            st.warning(t("app.snapshot_none", lang))
            return
        current = st.session_state.get("snapshot_id")
        chosen = st.selectbox(t("admin.snapshot_label", lang), snapshots, index=snapshots.index(current) if current in snapshots else 0,
                              key="admin_snapshot_pick")
        if chosen != current:
            st.session_state["snapshot_id"] = chosen
            st.session_state.pop("home_month", None)
        st.caption(t("admin.snapshot_note", lang))
        st.divider()


def _set_lang() -> None:
    picked = st.session_state.get("lang_seg")
    if picked in i18n.LANGS:
        st.session_state["lang"] = picked


def _header(pages: dict, lang: str) -> None:
    snapshot = common.snapshot_id()
    period = common.cached_period(snapshot) if snapshot else None
    with st.container(key="ts_header"):
        brand, nav, data, switch = st.columns([2.9, 3.0, 3.9, 1.5], vertical_alignment="center")
        brand.markdown(f'<div class="ts-brand"><b>TradeSentry</b><span>{html.escape(t("app.subtitle", lang))}</span></div>',
                       unsafe_allow_html=True)
        with nav, st.container(horizontal=True, gap="small", key="ts_nav"):
            for name in ("home", "case", "assist"):
                st.page_link(pages[name], label=t(f"nav.{name}", lang))
        if period:
            line = t("app.data_line", lang, start=i18n.month_label(period[0], lang), end=i18n.month_label(period[1], lang))
            data.markdown(f'<div class="ts-dataline">{html.escape(line)}</div>', unsafe_allow_html=True)
        if st.session_state.get("lang_seg") != lang:
            st.session_state["lang_seg"] = lang
        switch.segmented_control(t("app.lang_label", lang), list(i18n.LANGS), format_func=i18n.LANG_SHORT.get, key="lang_seg",
                                 on_change=_set_lang, label_visibility="collapsed", required=True)


def main() -> None:
    st.set_page_config(page_title="TradeSentry", layout="wide")
    if st.session_state.get("lang") not in i18n.LANGS:
        st.session_state["lang"] = i18n.DEFAULT_LANG
    st.markdown(style.CSS, unsafe_allow_html=True)
    snapshots = _snapshot_state()
    lang = common.lang()
    pages = {
        "home": st.Page(home.render, title=t("nav.home", lang), url_path="home", default=True),
        "case": st.Page(case.render, title=t("nav.case", lang), url_path="case"),
        "assist": st.Page(assist.render, title=t("nav.assist", lang), url_path="assist"),
        "admin": st.Page(ADMIN_SCRIPT, title=t("nav.admin", lang), url_path="admin"),
    }
    common.PAGES.clear()
    common.PAGES.update(pages)
    navigation = st.navigation(list(pages.values()), position="hidden")
    jobs.route()
    target = jobs.goto_target()
    if target in pages and navigation is not pages[target]:
        st.switch_page(pages[target])
    _header(pages, lang)
    if navigation is pages["admin"]:
        _admin_sidebar(snapshots, lang)
    navigation.run()
    jobs.render_layer()  # 모든 페이지(관리자 페이지 포함) 공통. 화면 위치는 CSS(position:fixed)로 고정한다


main()
