"""배경 조사 실행 · 전체 화면 로딩 창 · 오른쪽 아래 조사 중 표시(UI3).

- "조사 시작"/"다시 조사"는 CLI와 같은 진입점(`python -m tradesentry.cli run-case …`)을 배경 하위 프로세스로 띄운다:
  `subprocess.Popen(app.run_case_command(args), cwd=저장소 루트, env=app.child_env(), stdout/stderr=임시 파일(저장소 밖),
  start_new_session=True)`. 동기 실행(`app.run_case_once`)은 쓰지 않는다(위젯을 누르면 스크립트가 다시 돌아 끊긴다).
- 재생 파일 규칙은 UI2와 같다: 재생 파일이 있으면 재생, 없고 키가 프로세스 환경에 있으면 실제 NIM, 둘 다 없으면 시작하지 않는다.
- 세션에 조사 하나(`session_state["ts_job"]`, 프로세스 핸들은 `["ts_proc"]`). 진행 단계는 새 실행 폴더의 trace에서 읽는다
  (`tradesentry.ui.progress`). 제한 시간(모델 설정 wall time + 여유)을 넘기면 프로세스 묶음을 끝내고 실패로 표시한다.
- 로딩 창과 조사 중 표시는 진입 스크립트가 모든 페이지(관리자 페이지 포함)에서 `render_layer()`로 그린다. 도는 동안은
  `st.fragment(run_every=1초)`로 그 부분만 다시 그린다. 위치는 key를 준 컨테이너의 `.st-key-<key>` CSS로 고정한다.
- 실패로 끝난 실행은 trace `run_end`의 실행 상태로 도달한 단계까지만 완료로 그리고, 실패 창에 몇 단계까지 가고 멈췄는지 한 줄을
  보인다(UI5, `progress.step_state`·`progress.stopped_note`).
- 표준 출력·오류는 화면에 보이지 않는다(N13: 실패는 평이한 문장만). 임시 파일은 끝나면 닫는다(닫으면 지워진다).
"""
import html
import subprocess
import tempfile
import time

import streamlit as st

from tradesentry import app
from tradesentry.ui import alerts, progress
from tradesentry.ui.i18n import t
from tradesentry.ui.screens import common

JOB_KEY = "ts_job"
PROC_KEY = "ts_proc"
GOTO_KEY = "ts_goto"


def current() -> dict | None:
    job = st.session_state.get(JOB_KEY)
    return job if isinstance(job, dict) else None


def is_running() -> bool:
    job = current()
    return bool(job and job.get("status") == progress.RUNNING)


def running_case() -> str | None:
    job = current()
    return job["case_id"] if job and job.get("status") == progress.RUNNING else None


def _close_files() -> None:
    handles = st.session_state.get(PROC_KEY)
    if not handles:
        return
    for handle in handles[1:]:
        try:
            handle.close()
        except OSError:
            pass


def start(case_id: str, snapshot: str | None) -> bool:
    """배경 조사를 시작하고 로딩 창을 연다. 이미 도는 조사가 있거나 시작할 수 없으면 False."""
    if is_running() or not snapshot:
        return False
    allowed, replay = common.can_run(case_id)
    if not allowed:
        return False
    args = app.build_run_case_args(snapshot, common.policy_version(), "full", case_id, replay)
    before = app.list_run_dirs(common.OUTPUTS_ROOT)
    _close_files()
    out, err = tempfile.TemporaryFile(), tempfile.TemporaryFile()  # 저장소 밖 임시 파일. 화면에 보이지 않는다
    proc = subprocess.Popen(app.run_case_command(args), cwd=common.REPO_ROOT, env=app.child_env(), stdout=out, stderr=err,
                            stdin=subprocess.DEVNULL, start_new_session=True)
    st.session_state[PROC_KEY] = (proc, out, err)
    st.session_state[JOB_KEY] = progress.new_job(case_id, snapshot, time.time(), before, replay is not None)
    return True


def _stop(proc: subprocess.Popen) -> None:
    """제한 시간을 넘긴 프로세스 묶음을 끝낸다(SIGTERM, 5초 뒤에도 살아 있으면 SIGKILL, 그 뒤 wait로 회수. `progress.stop_process_group`)."""
    progress.stop_process_group(proc)


def _stdout_dirs(handle) -> list[str]:
    try:
        handle.seek(0)
        return app.output_run_dirs(app.redact(handle.read().decode("utf-8", "replace")))
    except (OSError, ValueError):
        return []


def poll(now: float | None = None) -> dict | None:
    """조사 상태를 새로 읽는다(실행 폴더·상태·종료 시각). 끝난 조사는 그대로 돌려준다."""
    job = current()
    if job is None or job.get("status") != progress.RUNNING:
        return job
    now = time.time() if now is None else now
    handles = st.session_state.get(PROC_KEY)
    proc = handles[0] if handles else None
    returncode = proc.poll() if proc is not None else -1
    after = app.list_run_dirs(common.OUTPUTS_ROOT)
    stdout_dirs = _stdout_dirs(handles[1]) if handles and returncode is not None else None
    run_id = progress.pick_run_dir(job["before"], after, stdout_dirs, case_id=job["case_id"],
                                   case_of=lambda name: progress.run_dir_case(common.OUTPUTS_ROOT / name)) or job.get("run_id")
    entry = alerts.run_entry(common.OUTPUTS_ROOT, run_id) if run_id else None
    limit = progress.time_limit(app.wall_limit_seconds(common.REPO_ROOT))
    status = progress.next_status(job, now=now, returncode=returncode, record_status=(entry or {}).get("execution_status"),
                                  limit_s=limit)
    if status == progress.TIMEOUT and proc is not None:
        _stop(proc)
    job = {**job, "run_id": run_id, "status": status}
    if status != progress.RUNNING:
        job["ended"] = now
        _close_files()
    st.session_state[JOB_KEY] = job
    return job


def clear() -> None:
    _close_files()
    st.session_state.pop(JOB_KEY, None)
    st.session_state.pop(PROC_KEY, None)


def _steps_for(job: dict) -> dict:
    run_dir = common.OUTPUTS_ROOT / job["run_id"] if job.get("run_id") else None
    events = progress.read_trace(run_dir)
    if job.get("status") == progress.DONE and not any(e.get("event") == "run_end" for e in events):
        events = events + [{"event": "run_end", "data": {"execution_status": "COMPLETED"}}]  # 끝났다: 건너뛴 단계는 건너뜀, 나머지는 완료
    return progress.step_state(events)


def _open_result(job: dict) -> None:
    common.select_case(job["case_id"], job.get("run_id"))
    st.session_state[GOTO_KEY] = "case"


# ---- 그리기 -----------------------------------------------------------------------------------------------------


def _steps_html(steps: dict, lang: str) -> str:
    rows = []
    for index, state in enumerate(steps["states"]):
        label = html.escape(progress.step_label(index, lang))
        mark = {"done": "✓", "skipped": "–"}.get(state, "")
        tag = f' <span class="ts-skip">{html.escape(t("load.skipped", lang))}</span>' if state == "skipped" else ""
        rows.append(f'<li class="ts-step ts-step-{state}"><span class="ts-dot">{mark}</span><span>{label}{tag}</span></li>')
    return '<ul class="ts-steps">' + "".join(rows) + "</ul>"


def _bar_html(ratio: float, cls: str = "ts-bar") -> str:
    return f'<div class="{cls}"><span style="width:{ratio * 100:.0f}%"></span></div>'


def _overlay(job: dict, lang: str, steps: dict, now: float) -> None:
    countries = common.countries()
    failed = job["status"] in (progress.FAILED, progress.TIMEOUT)
    with st.container(key="ts_overlay"):
        with st.container(key="ts_modal"):
            title = t("load.failed_title", lang) if failed else t("load.title", lang)
            spinner = '<span class="ts-fail">!</span>' if failed else '<span class="ts-spin"></span>'
            clock = html.escape(progress.clock_text(progress.elapsed_seconds(job, now)))
            st.markdown(
                f'<div class="ts-load-head">{spinner}<div class="ts-load-title"><div class="ts-h">{html.escape(title)}</div>'
                f'<div class="ts-sub">{html.escape(progress.case_title(job["case_id"], lang, countries))}</div></div>'
                f'<div class="ts-clock">{clock}</div></div>', unsafe_allow_html=True)
            st.markdown(_steps_html(steps, lang) + _bar_html(progress.progress_ratio(steps)), unsafe_allow_html=True)
            if steps.get("retrying") and not failed:
                st.markdown(f'<div class="ts-note">{html.escape(t("load.retrying", lang))}</div>', unsafe_allow_html=True)
            if failed:
                key = "load.timeout" if job["status"] == progress.TIMEOUT else "load.failed"
                where = progress.stopped_note(steps, lang)  # 실패한 실행의 run_end: 어디서 멈췄는지(UI5)
                if where:
                    st.markdown(f'<div class="ts-note">{html.escape(where)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ts-failbox">{html.escape(t(key, lang))}</div>', unsafe_allow_html=True)
                with st.container(horizontal=True, horizontal_alignment="right", key="ts_fail_actions"):
                    if st.button(t("load.close", lang), key="ts_close"):
                        clear()
                        st.rerun(scope="app")
                    if st.button(t("load.retry", lang), key="ts_retry", type="primary"):
                        case_id, snapshot = job["case_id"], job["snapshot_id"]
                        clear()
                        start(case_id, snapshot)
                        st.rerun(scope="app")
            else:
                with st.container(horizontal=True, vertical_alignment="center", key="ts_load_actions"):
                    expect = t("load.expect_replay", lang) if job.get("replay") else t("load.expect", lang)
                    st.markdown(f'<div class="ts-note">{html.escape(expect)}</div>', unsafe_allow_html=True)
                    if st.button(t("load.back", lang), key="ts_back"):  # 조사는 계속되고 경보 목록으로 간다
                        st.session_state[JOB_KEY] = {**job, "overlay": False}
                        st.session_state[GOTO_KEY] = "home"
                        st.rerun(scope="app")
                note = t("load.footnote_replay", lang) if job.get("replay") else t("load.footnote", lang)
                st.markdown(f'<div class="ts-footnote">{html.escape(note)}</div>', unsafe_allow_html=True)


def _pill(job: dict, lang: str, steps: dict, now: float) -> None:
    status = job["status"]
    label = progress.pill_text(job, lang, common.countries(), steps, now)
    state = {progress.DONE: "done", progress.FAILED: "failed", progress.TIMEOUT: "failed"}.get(status, "running")
    with st.container(key=f"ts_pill_{state}"):
        if st.button(label, key="ts_pill"):
            if status == progress.DONE:
                _open_result(job)
                clear()
            elif status in (progress.FAILED, progress.TIMEOUT):
                case_id, snapshot = job["case_id"], job["snapshot_id"]
                clear()
                start(case_id, snapshot)
            else:
                st.session_state[JOB_KEY] = {**job, "overlay": True}
            st.rerun(scope="app")
        if state == "running":
            st.markdown(_bar_html(progress.progress_ratio(steps), "ts-pillbar"), unsafe_allow_html=True)
    st.markdown('<style>[data-testid="stMainBlockContainer"]{padding-bottom:96px !important}</style>', unsafe_allow_html=True)


def _draw(job: dict) -> None:
    lang = common.lang()
    now = time.time()
    steps = _steps_for(job)
    if job.get("overlay"):
        _overlay(job, lang, steps, now)
    else:
        _pill(job, lang, steps, now)


@st.fragment(run_every=1.0)
def _live() -> None:
    job = poll()
    if job is None:
        return
    if job["status"] != progress.RUNNING:  # 방금 끝났다: 목록·사례 화면을 새 결과로 다시 그린다
        if job["status"] == progress.DONE and job.get("overlay"):
            _open_result(job)
            clear()
        st.rerun(scope="app")
    _draw(job)


def route() -> None:
    """페이지를 그리기 전에: 조사 상태를 새로 읽고, 로딩 창이 떠 있는 채로 끝났으면 사례 검토로 이동할 표시를 남긴다."""
    job = poll()
    if job is not None and job["status"] == progress.DONE and job.get("overlay"):
        _open_result(job)
        clear()


def render_layer() -> None:
    """모든 페이지 공통(페이지 본문 뒤에 그린다. 위치는 CSS로 고정): 도는 조사가 있으면 1초마다 갱신되는 로딩 창/조사 중 표시,
    끝난 조사는 결과·실패 표시."""
    job = current()
    if job is None:
        return
    if job["status"] == progress.RUNNING:
        _live()
    else:
        _draw(job)


def goto_target() -> str | None:
    """조사가 끝나 이동할 페이지 이름(한 번만)."""
    return st.session_state.pop(GOTO_KEY, None)
