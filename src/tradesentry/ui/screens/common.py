"""화면 공통: 언어·스냅샷 상태, 페이지 이동, 캐시한 경보 목록, 조사 실행(하위 프로세스), 예외 표시(N13).

streamlit은 여기와 형제 모듈에서만 import한다. 페이지 이동은 진입 스크립트가 PAGES에 넣어 준 st.Page 객체로 한다.
"""
from pathlib import Path

import streamlit as st

from tradesentry import app
from tradesentry.ui import alerts, i18n
from tradesentry.ui.i18n import t

REPO_ROOT = app.REPO_ROOT
OUTPUTS_ROOT = REPO_ROOT / app.OUTPUTS_NAME
SNAPSHOTS_ROOT = REPO_ROOT / "data" / "snapshots"
PAGES: dict[str, object] = {}  # 진입 스크립트가 채운다: home·case·assist·admin → st.Page


def lang() -> str:
    value = st.session_state.get("lang")
    return value if value in i18n.LANGS else i18n.DEFAULT_LANG


def snapshot_id() -> str | None:
    return st.session_state.get("snapshot_id")


def policy_version() -> str:
    return st.session_state.get("policy_version") or alerts.DEFAULT_POLICY


def go(name: str) -> None:
    page = PAGES.get(name)
    if page is not None:
        st.switch_page(page)


def open_admin(run_id: str | None = None) -> None:
    """관리자용 화면(app.py)으로. app.py는 session_state["selected_run"]을 실행 폴더 기본 선택으로 읽는다."""
    if run_id:
        st.session_state["selected_run"] = run_id
    go("admin")


def show_error(key: str, exc: BaseException) -> None:
    """예외는 이름만 보인다(traceback·경로 없음, N13)."""
    st.error(t(key, lang(), name=type(exc).__name__))


@st.cache_data(show_spinner=False)
def cached_case_list(snapshot: str, policy: str) -> dict:
    return alerts.case_list(snapshot, policy)


@st.cache_data(show_spinner=False)
def cached_alerts(snapshot: str, month: str, policy: str) -> list[dict]:
    return alerts.alerts_for_month(snapshot, month, policy, cases=cached_case_list(snapshot, policy))


@st.cache_data(show_spinner=False)
def cached_period(snapshot: str) -> tuple[str, str] | None:
    return alerts.snapshot_period(snapshot)


def countries() -> dict[str, str]:
    return i18n.load_country_names(REPO_ROOT, lang())


def find_alert(case_id: str) -> dict | None:
    """선택한 사례의 경보 줄(지표 포함). 현재 스냅샷의 그 달 경보에서 찾는다. 없으면 None."""
    snapshot = snapshot_id()
    parsed = app.parse_case_id(case_id)
    if not snapshot or parsed is None:
        return None
    try:
        for row in cached_alerts(snapshot, parsed["month"], policy_version()):
            if row["case_id"] == case_id:
                return row
    except Exception:  # noqa: BLE001 — 경보 목록이 안 만들어져도 사례 화면은 뜬다
        return None
    return None


def can_run(case_id: str) -> tuple[bool, str | None]:
    """조사 실행 가능 여부와 재생 파일 상대 경로. 키가 없으면 재생 파일이 있을 때만 된다(app.py와 같은 규칙)."""
    replay = app.replay_file_for(case_id, REPO_ROOT)
    return (replay is not None or app.key_present()), replay


def run_investigation(case_id: str, snapshot: str, mode: str = "full") -> dict:
    """CLI와 같은 진입점(`python -m tradesentry.cli run-case …`)을 하위 프로세스로 한 번 돌린다. 키가 없으면 재생 파일을 쓴다.
    새 실행 폴더 이름을 new_run_dirs에 돌려준다. 화면에서 시작한 실행은 점수표 근거가 아니다."""
    _, replay = can_run(case_id)
    use_replay = replay is not None  # 재생 파일이 있으면 키가 있어도 재생(app.py의 기본값과 같다). 실제 NIM은 관리자 화면에서 끈다
    args = app.build_run_case_args(snapshot, policy_version(), mode, case_id, replay if use_replay else None)
    before = app.list_run_dirs(OUTPUTS_ROOT)
    st.session_state["running"] = True
    try:
        with st.spinner(t("home.running", lang(), s=app.wall_limit_seconds(REPO_ROOT))):
            result = app.run_case_once(args, repo_root=REPO_ROOT)
    finally:
        st.session_state["running"] = False
    result["new_run_dirs"] = app.output_run_dirs(result["stdout"]) or app.new_run_dirs(before, app.list_run_dirs(OUTPUTS_ROOT))
    result["replay"] = use_replay
    st.session_state["last_run"] = result
    return result


def select_case(case_id: str, run_id: str | None) -> None:
    st.session_state["selected_case"] = case_id
    st.session_state["selected_run"] = run_id


def verdict_badge(code: object) -> str:
    return i18n.verdict_label(code, lang())


def render_footer() -> None:
    st.divider()
    st.caption(t("app.disclaimer", lang()))
