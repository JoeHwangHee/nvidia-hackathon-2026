"""담당자용 화면 진입 스크립트(UI2): 페이지 4개 — 담당자 홈 · 사례 검토 · 결정 기록/도움 · 관리자용 조사 기록(기존 app.py).

실행(저장소 루트에서. streamlit은 lock 밖 `--with`다, 결정 기록 20260926-0732 ①):
    uv run --locked --with "streamlit==1.64.0" streamlit run src/tradesentry/ui/ui_app.py --client.showErrorDetails=false --server.port 8502

- 관리자용 페이지는 `st.Page("../app.py")`(진입 스크립트 폴더 기준 상대 경로)로 감싼다. app.py를 고치지 않고 import로 실행시키지도
  않는다(Streamlit이 스크립트로 실행한다).
- 사이드바 맨 위: 언어 전환(한국어/English, `st.session_state["lang"]`, 기본 한국어)과 스냅샷 선택(`app.list_snapshots` 재사용.
  기본값은 정본 빌드가 있는 실자료 `kcs_202201_202412_v2`, 없으면 합성 픽스처).
- 이 스크립트는 `.env`를 읽지 않고 NIM을 직접 부르지 않는다. 예외는 이름만 보인다(N13). `outputs/sealed/`는 나열·표시하지 않는다.
- 위치: 단위 표·자료 계약 §10.3 N2가 패키지 밖 모듈을 `ingest.py`·`app.py` 둘로 고정하므로(tests/test_units_registry.py가 본다)
  진입 스크립트도 `ui/` 패키지 안에 둔다(지시서의 `src/tradesentry/ui_app.py` 대신. 결정 기록에 적음).
"""
from pathlib import Path

import streamlit as st

from tradesentry import app
from tradesentry.ui import alerts, i18n
from tradesentry.ui.i18n import t
from tradesentry.ui.screens import assist, case, common, home

ADMIN_SCRIPT = Path("..") / "app.py"  # 진입 스크립트(src/tradesentry/ui/) 기준 → src/tradesentry/app.py


def _sidebar() -> None:
    with st.sidebar:
        st.markdown(f"**{t('app.title', i18n.DEFAULT_LANG)}**")
        picked = st.radio(t("app.lang_label", i18n.DEFAULT_LANG), list(i18n.LANGS), format_func=i18n.LANG_NAMES.get,
                          horizontal=True, key="lang_pick", index=list(i18n.LANGS).index(common.lang()))
        st.session_state["lang"] = picked
        lang = picked
        snapshots = app.list_snapshots(common.SNAPSHOTS_ROOT)
        if not snapshots:
            st.warning(t("app.snapshot_none", lang))
            st.session_state["snapshot_id"] = None
        else:
            current = st.session_state.get("snapshot_id")
            default = current if current in snapshots else alerts.default_snapshot(snapshots)
            chosen = st.selectbox(t("app.snapshot_label", lang), snapshots, index=snapshots.index(default), key="snapshot_pick")
            if chosen != current:
                st.session_state["snapshot_id"] = chosen
                st.session_state.pop("home_month", None)
        st.caption(t("app.subtitle", lang))


def main() -> None:
    st.set_page_config(page_title="TradeSentry", layout="wide")
    if "lang" not in st.session_state:
        st.session_state["lang"] = i18n.DEFAULT_LANG
    _sidebar()
    lang = common.lang()
    pages = {
        "home": st.Page(home.render, title=t("nav.home", lang), url_path="home", default=True),
        "case": st.Page(case.render, title=t("nav.case", lang), url_path="case"),
        "assist": st.Page(assist.render, title=t("nav.assist", lang), url_path="assist"),
        "admin": st.Page(ADMIN_SCRIPT, title=t("nav.admin", lang), url_path="admin"),
    }
    common.PAGES.clear()
    common.PAGES.update(pages)
    navigation = st.navigation(list(pages.values()), position="sidebar")
    navigation.run()


main()
