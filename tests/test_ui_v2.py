"""담당자용 화면 v2(UI3) 순수 논리 시험. streamlit·네트워크·키 없이 돈다(화면 함수는 부르지 않는다).

대상: tradesentry.ui.progress(trace → 5단계 상태, 반쯤 쓰인 줄, 배경 실행의 상태 전이·제한 시간, 사례 이름),
listing(요약 카드 수치, 변화 큰 순 정렬, 진행 상태 판정, 변화내용 문구), records.latest_decisions, i18n 월 표기, 그리고 담당자
화면에 보이는 문구(사례 이름·칩·근거·표 문구)에 내부 식별자(HS6 6자리 숫자·실행 폴더 이름·스냅샷 ID·정책 이름·상태 코드)가
없음(KO·EN). 고정 입력은 tests/units/A2/fixture/run_case-260926071424/(키 없는 재생 실행 A)와 이 파일 안의 합성 값이다.
"""
import json
import os
import re
import shutil
import socket
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

from tradesentry import app
from tradesentry.approval import record as approval
from tradesentry.ui import alerts, i18n, listing, plain, progress, records

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_RUN = ROOT / "tests" / "units" / "A2" / "fixture" / "run_case-260926071424"
CASE_ID = "850450-XA-202412"
INTERNAL_RE = re.compile(r"(?<!\d)\d{6}(?!\d)|run_case-|approval_record-|kcs_|controlled_fixture|policy_v|MAINTAIN|MONITOR|HOLD"
                         r"|COMPLETED|FAILED|NOT_TRIGGERED|[0-9a-f]{64}")


def _refuse(*args, **kwargs):
    raise OSError("시험에서는 네트워크를 쓰지 않는다")


class Base(unittest.TestCase):
    def setUp(self):
        missing = Path(tempfile.gettempdir()) / "tradesentry-ui3-missing"
        env = mock.patch.dict(os.environ, {"TRADESENTRY_SEALED_DIR": str(missing / "sealed"), "HOME": str(missing / "home")})
        env.start()
        self.addCleanup(env.stop)
        for target in ("socket.socket.connect", "socket.create_connection"):
            patcher = mock.patch(target, _refuse)
            patcher.start()
            self.addCleanup(patcher.stop)

    def assertNoInternal(self, text: str, where: str = "") -> None:
        found = INTERNAL_RE.search(text)
        self.assertIsNone(found, f"{where}: {found.group(0) if found else ''} in {text!r}")


def ev(event, where=None, **data):
    return {"event": event, "stage": where, "data": data}


# ---- progress: trace → 5단계 ------------------------------------------------------------------------------------


class ProgressStepsTest(Base):
    def test_half_written_last_line_and_bad_lines_are_ignored(self):
        text = (json.dumps({"seq": 1, "event": "run_start"}) + "\n" + "not json\n"
                + json.dumps({"seq": 2, "event": "tool_call", "data": {"tool": "check_comparability"}}) + "\n"
                + '{"seq":3,"event":"tool_call","data":{"tool":"get_hi')  # 쓰는 중
        events = progress.parse_trace_lines(text)
        self.assertEqual([e["seq"] for e in events], [1, 2])
        self.assertEqual(progress.parse_trace_lines(""), [])
        self.assertEqual(progress.parse_trace_lines('{"event":"run_start"}'), [])  # 줄바꿈이 없으면 아직 쓰는 중

    def test_expected_order_when_nothing_yet(self):
        steps = progress.step_state([])
        self.assertEqual(steps["states"], ["current", "pending", "pending", "pending", "pending"])
        self.assertEqual((steps["done"], steps["current"], steps["finished"]), (0, 0, False))
        self.assertEqual(progress.progress_ratio(steps), 0.0)

    def test_each_stage_marker(self):
        seq = [ev("run_start"), ev("stage_start", "basic", stage="basic"), ev("tool_call", "basic", tool="check_comparability")]
        self.assertEqual(progress.step_state(seq)["current"], 0)
        seq.append(ev("tool_call", "basic", tool="get_history"))
        self.assertEqual(progress.step_state(seq)["states"][:2], ["done", "current"])
        seq.append(ev("tool_call", "basic", tool="decompose_hs"))
        self.assertEqual(progress.step_state(seq)["current"], 2)
        seq.append(ev("tool_call", "basic", tool="compare_partners"))  # 순서가 바뀌어도 뒤로 가지 않는다
        self.assertEqual(progress.step_state(seq)["current"], 2)
        seq.append(ev("stage_start", "critic", stage="critic"))
        self.assertEqual(progress.step_state(seq)["current"], 3)
        seq.append(ev("stage_end", "critic", stage="critic"))  # 검수가 끝나면 숫자 대조 차례
        self.assertEqual(progress.step_state(seq)["states"], ["done", "done", "done", "done", "current"])
        seq.append(ev("tool_call", None, tool="verify_evidence"))
        seq.append(ev("validator_result", None, phase="verify"))
        steps = progress.step_state(seq)
        self.assertEqual((steps["done"], steps["current"]), (4, 4))
        self.assertEqual(progress.progress_ratio(steps), 0.8)
        seq.append(ev("run_end", None, execution_status="COMPLETED"))
        steps = progress.step_state(seq)
        self.assertEqual(steps["states"], ["done"] * 5)
        self.assertTrue(steps["finished"])
        self.assertEqual(progress.progress_ratio(steps), 1.0)

    def test_retrying_flag_follows_last_model_event(self):
        seq = [ev("tool_call", "basic", tool="get_history"), ev("model_request"), ev("model_error", retrying=True)]
        self.assertTrue(progress.step_state(seq)["retrying"])
        seq.append(ev("model_request"))
        seq.append(ev("model_response"))
        self.assertFalse(progress.step_state(seq)["retrying"])

    def test_fixture_trace_reaches_the_end(self):
        events = progress.read_trace(FIXTURE_RUN)
        self.assertTrue(events)
        steps = progress.step_state(events)
        self.assertTrue(steps["finished"])
        partial = progress.step_state(events[: len(events) // 2])
        self.assertFalse(partial["finished"])
        self.assertEqual(progress.read_trace(None), [])
        self.assertEqual(progress.read_trace(ROOT / "no-such-run"), [])


# ---- progress: 배경 실행의 순수 부분 -------------------------------------------------------------------------------


class JobStateTest(Base):
    def test_transitions(self):
        job = progress.new_job(CASE_ID, "controlled_fixture_v0", 1000.0, ["run_case-260926000000"], True)
        self.assertEqual((job["status"], job["overlay"], job["run_id"]), (progress.RUNNING, True, None))
        limit = progress.time_limit(300)
        self.assertEqual(limit, 300 + app.RUN_GRACE_S)
        self.assertEqual(progress.next_status(job, now=1010.0, returncode=None, record_status=None, limit_s=limit), progress.RUNNING)
        self.assertEqual(progress.next_status(job, now=1000.0 + limit + 1, returncode=None, record_status=None, limit_s=limit),
                         progress.TIMEOUT)
        self.assertEqual(progress.next_status(job, now=1020.0, returncode=0, record_status="COMPLETED", limit_s=limit), progress.DONE)
        self.assertEqual(progress.next_status(job, now=1020.0, returncode=0, record_status=None, limit_s=limit), progress.FAILED)
        self.assertEqual(progress.next_status(job, now=1020.0, returncode=1, record_status="FAILED", limit_s=limit), progress.FAILED)
        self.assertEqual(progress.next_status(job, now=1020.0, returncode=0, record_status="INVALID", limit_s=limit), progress.FAILED)
        done = {**job, "status": progress.DONE}
        self.assertEqual(progress.next_status(done, now=9999.0, returncode=None, record_status=None, limit_s=limit), progress.DONE)

    def test_clock_and_run_dir(self):
        self.assertEqual(progress.clock_text(0), "0:00")
        self.assertEqual(progress.clock_text(58), "0:58")
        self.assertEqual(progress.clock_text(125), "2:05")
        job = progress.new_job(CASE_ID, "s", 100.0, [], True)
        self.assertEqual(progress.elapsed_seconds(job, 142.9), 42)
        self.assertEqual(progress.elapsed_seconds({**job, "ended": 130.0}, 999.0), 30)
        before = ["run_case-260926000000"]
        after = before + ["run_case-260926000010", "run_case-260926000005"]
        self.assertEqual(progress.pick_run_dir(before, after), "run_case-260926000010")
        self.assertEqual(progress.pick_run_dir(before, after, ["run_case-260926000005"]), "run_case-260926000005")
        self.assertIsNone(progress.pick_run_dir(before, before))

    def test_case_names_and_pill_have_no_internal_identifiers(self):
        for lang in i18n.LANGS:
            countries = i18n.load_country_names(ROOT, lang)
            job = progress.new_job("850432-CN-202301", "kcs_202201_202412_v2", 100.0, [], False)
            steps = progress.step_state([ev("tool_call", None, tool="decompose_hs")])
            texts = [progress.case_title("850432-CN-202301", lang, countries), progress.case_short(CASE_ID, lang, countries),
                     progress.pill_text(job, lang, countries, steps, 158.0),
                     progress.pill_text({**job, "status": progress.DONE}, lang, countries, steps, 158.0),
                     progress.pill_text({**job, "status": progress.TIMEOUT}, lang, countries, steps, 158.0)]
            texts += [progress.step_label(i, lang) for i in range(progress.STEP_COUNT)]
            for text in texts:
                self.assertNoInternal(text, lang)
        ko = i18n.load_country_names(ROOT, "ko")
        self.assertEqual(progress.case_title("850432-CN-202301", "ko", ko), "중국산 계기용 변압기 (중용량) · 전압 조정기 · 2023년 1월 경보")
        en = i18n.load_country_names(ROOT, "en")
        self.assertEqual(progress.case_title("850490-FI-202412", "en", en),
                         "Parts of transformers & power supplies from Finland · December 2024 alert")
        job = progress.new_job("850490-FI-202412", "s", 100.0, [], False)
        steps = progress.step_state([ev("tool_call", None, tool="decompose_hs")])
        self.assertEqual(progress.pill_text(job, "ko", ko, steps, 158.0), "● 조사 중 · 핀란드산 변압기·전원장치 부분품 · 3/5단계 · 0:58 ›")
        self.assertEqual(progress.pill_text(job, "en", en, steps, 158.0),
                         "● Investigating · Parts of transformers & power supplies · Finland · step 3/5 · 0:58 ›")


# ---- listing ----------------------------------------------------------------------------------------------------


def row(case_id, *, unit=True, share=False, u0="10.00", u1="15.00", r_u="50.0", s0="10.0", s1="12.0", d_s="2.0"):
    hs6, partner, month = case_id.split("-")
    dec = lambda v: None if v is None else Decimal(v)  # noqa: E731
    return {"case_id": case_id, "hs6": hs6, "partner": partner, "month": month, "baseline_month": f"{int(month[:4]) - 1}{month[4:]}",
            "snapshot_id": "controlled_fixture_v0", "policy_version": "policy_v1", "unit_value_triggered": unit,
            "share_triggered": share, "missingness": 0,
            "metrics": {"U_0": dec(u0), "U_1": dec(u1), "r_U": dec(r_u), "s_0": dec(s0), "s_1": dec(s1), "d_s": dec(d_s)}}


def sample_rows():
    return [
        row("850490-FI-202412", r_u="496.6"),
        row("850450-JP-202412", r_u="-55.2", u0="534.20", u1="239.08"),
        row("850431-MX-202412", r_u="663.4"),
        row("850432-PH-202412", unit=False, share=True, u0="5.00", u1=None, r_u=None, s0="19.3", s1="0.0", d_s="-19.3"),
        row("850432-US-202412", unit=False, share=True, r_u="5.0", s0="10.4", s1="21.9", d_s="11.5"),
    ]


class ListingTest(Base):
    def test_sort_by_largest_change(self):
        rows = sample_rows()
        order = [r["case_id"] for r in listing.sort_rows(rows, "change", {}, {})]
        self.assertEqual(order, ["850431-MX-202412", "850490-FI-202412", "850450-JP-202412", "850432-PH-202412", "850432-US-202412"])
        names = {"850490": "b", "850450": "a", "850431": "c", "850432": "d", "FI": "z", "JP": "y", "MX": "x", "PH": "w", "US": "v"}
        self.assertEqual([r["case_id"] for r in listing.sort_rows(rows, "item", {}, names)][:2], ["850450-JP-202412", "850490-FI-202412"])
        self.assertEqual([r["case_id"] for r in listing.sort_rows(rows, "partner", {}, names)][0], "850432-US-202412")
        states = {"850432-US-202412": {"state": listing.AWAITING}, "850450-JP-202412": {"state": listing.RUNNING}}
        self.assertEqual([r["case_id"] for r in listing.sort_rows(rows, "progress", states, names)][:2],
                         ["850450-JP-202412", "850432-US-202412"])

    def test_month_summary(self):
        rows = sample_rows()
        cases = {"cases": [{"month": "202412"}] * 5 + [{"month": "202411"}] * 12 + [{"month": "202301"}] * 3}
        states = {"850431-MX-202412": {"state": listing.AWAITING, "investigated": True, "verdict": "HOLD"},
                  "850490-FI-202412": {"state": listing.RUNNING, "investigated": False, "verdict": None},
                  "850450-JP-202412": {"state": listing.DECIDED, "investigated": True, "verdict": "MAINTAIN"}}
        summary = listing.month_summary(rows, cases, "202412", states)
        self.assertEqual((summary["total"], summary["last_month"]), (5, 12))
        self.assertEqual((summary["unit"], summary["unit_up"], summary["unit_down"]), (3, 2, 1))
        self.assertEqual((summary["share"], summary["share_stopped"], summary["share_up"], summary["share_down"]), (2, 1, 1, 1))
        self.assertEqual((summary["investigated"], summary["running"], summary["awaiting"]), (2, 1, 1))
        self.assertEqual(summary["verdicts"], {"MAINTAIN": 1, "HOLD": 1})
        first = listing.month_summary(rows, cases, "202301", {})
        self.assertIsNone(first["last_month"])  # 경보가 생길 수 있는 첫 달보다 앞
        self.assertEqual(listing.prev_month("202301"), "202212")
        for lang in i18n.LANGS:
            cards = listing.summary_cards(summary, lang)
            self.assertEqual(len(cards), 5)
            self.assertTrue(cards[4]["accent"])
            for card in cards:
                self.assertNoInternal(" ".join(str(v) for v in card.values()), lang)
        ko = listing.summary_cards(summary, "ko")
        self.assertEqual(ko[0]["sub"], "지난달 12건")
        self.assertEqual(ko[1]["sub"], "오른 것 2 · 내린 것 1")
        self.assertEqual(ko[2]["sub"], "수입이 끊긴 나라 1")
        self.assertEqual(ko[3]["sub"], "검토 유지 제안 1 · 자료 보류 제안 1 · 조사 중 1")
        self.assertEqual(listing.summary_cards(listing.month_summary(rows[:3], cases, "202412", {}), "en")[2]["sub"], "0 up · 0 down")

    def test_row_progress_states(self):
        with tempfile.TemporaryDirectory() as tmp:
            outputs = Path(tmp) / "outputs"
            shutil.copytree(FIXTURE_RUN, outputs / "run_case-260926071424")
            failed = outputs / "run_case-260926070000"
            failed.mkdir()
            (failed / "runlog_run_record-260926070000.json").write_text(json.dumps(
                {"case_id": "850431-XB-202412", "execution_status": "FAILED", "review_status_final": None}), encoding="utf-8")
            index = alerts.investigation_index(outputs)
            self.assertEqual(listing.row_progress(CASE_ID, index, {})["state"], listing.AWAITING)
            self.assertEqual(listing.row_progress(CASE_ID, index, {})["verdict"], "MONITOR")
            self.assertEqual(listing.row_progress("850431-XB-202412", index, {})["state"], listing.FAILED)
            self.assertEqual(listing.row_progress("850432-XC-202412", index, {})["state"], listing.NOT_STARTED)
            self.assertEqual(listing.row_progress(CASE_ID, index, {}, running_case=CASE_ID)["state"], listing.RUNNING)
            valid = {CASE_ID: {"validity": approval.VALID, "decision": "HOLD"}}
            state = listing.row_progress(CASE_ID, index, valid)
            self.assertEqual((state["state"], state["decision"]), (listing.DECIDED, "HOLD"))
            stale = {CASE_ID: {"validity": approval.REVIEW_REQUIRED, "decision": "HOLD"}}
            self.assertEqual(listing.row_progress(CASE_ID, index, stale)["state"], listing.REVIEW_REQUIRED)
            # 저장한 기록 → latest_decisions → 결정 완료, 보고서가 바뀌면 재검토 필요
            loaded = app.load_run(outputs / "run_case-260926071424")
            record = records.build_record(loaded, "HOLD", "메모", "담당 A", "2026-09-26T19:00:00+09:00")
            records.save_record(outputs, record)
            latest = records.latest_decisions(outputs)
            self.assertEqual(latest[CASE_ID]["validity"], approval.VALID)
            self.assertEqual(listing.row_progress(CASE_ID, index, latest)["state"], listing.DECIDED)
            report_path = next((outputs / "run_case-260926071424").glob("reports_render_ko-*.json"))
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["report_hash"] = "0" * 64
            report_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
            self.assertEqual(listing.row_progress(CASE_ID, index, records.latest_decisions(outputs))["state"], listing.REVIEW_REQUIRED)
        filters = listing.filter_rows(sample_rows(), {"850431-MX-202412": {"state": listing.AWAITING}}, progress="awaiting")
        self.assertEqual([r["case_id"] for r in filters], ["850431-MX-202412"])
        self.assertEqual(len(listing.filter_rows(sample_rows(), {}, progress="not_started")), 5)
        self.assertEqual(len(listing.filter_rows(sample_rows(), {}, signal="share")), 2)
        found = listing.filter_rows(sample_rows(), {}, search="핀란드", names={"FI": "핀란드"})
        self.assertEqual([r["case_id"] for r in found], ["850490-FI-202412"])

    def test_change_and_progress_cells(self):
        rows = {r["case_id"]: r for r in sample_rows()}
        ko = listing.change_cell(rows["850450-JP-202412"], "ko")
        self.assertEqual(ko, {"main": "kg당 단가 534.20 → 239.08 USD", "sub": "점유율 10.0% → 12.0%", "badge": "▼ −55.2%", "badge_kind": "down"})
        stopped = listing.change_cell(rows["850432-PH-202412"], "ko")
        self.assertEqual(stopped["main"], "점유율 19.3% → 0.0% — 12월에 수입이 없었습니다")
        self.assertEqual((stopped["sub"], stopped["badge"], stopped["badge_kind"]), ("단가는 비교할 수 없음", "▼ −19.3%p", "sh"))
        en = listing.change_cell(rows["850432-PH-202412"], "en")
        self.assertEqual((en["main"], en["sub"], en["badge"]), ("Share 19.3% → 0.0% — no imports in December", "Unit value not comparable",
                                                                "▼ −19.3 pp"))
        share_only = listing.change_cell(rows["850432-US-202412"], "ko")
        self.assertEqual((share_only["main"], share_only["badge"]), ("점유율 10.4% → 21.9%", "▲ +11.5%p"))
        for lang in i18n.LANGS:
            for r in rows.values():
                cell = listing.change_cell(r, lang)
                self.assertNoInternal(cell["main"] + cell["sub"] + cell["badge"], lang)
            for state in ({"state": listing.NOT_STARTED}, {"state": listing.RUNNING}, {"state": listing.AWAITING, "verdict": "HOLD"},
                          {"state": listing.DECIDED, "decision": "MONITOR"}, {"state": listing.REVIEW_REQUIRED}, {"state": listing.FAILED}):
                cell = listing.progress_cell(state, lang, "0:58")
                self.assertNoInternal(cell["text"] + cell["sub"], lang)
            self.assertNoInternal(listing.case_option_label("850432-CN-202301", "MAINTAIN", lang, i18n.load_country_names(ROOT, lang)), lang)
        self.assertEqual(listing.progress_cell({"state": listing.AWAITING, "verdict": "HOLD"}, "ko"),
                         {"text": "조사 완료 · 자료 보류 제안", "sub": "내 결정 대기", "kind": "done", "action": "view"})
        self.assertEqual(listing.progress_cell({"state": listing.AWAITING, "verdict": "HOLD"}, "en")["text"], "Investigated · data hold suggested")
        self.assertEqual(listing.progress_cell({"state": listing.RUNNING}, "ko", "0:58")["text"], "조사 중 · 0:58")
        self.assertEqual(listing.progress_cell({"state": listing.RUNNING}, "ko")["action"], "running")
        self.assertEqual(listing.progress_cell({"state": listing.DECIDED, "decision": "MONITOR"}, "ko")["text"], "결정 완료 · 모니터링")
        self.assertEqual(listing.progress_cell({"state": listing.FAILED}, "ko")["action"], "start")
        self.assertEqual(listing.case_option_label("850432-CN-202301", "MAINTAIN", "ko", i18n.load_country_names(ROOT, "ko")),
                         "계기용 변압기 (중용량) · 전압 조정기 · 중국 · 2023년 1월 · 검토 유지")


# ---- 사례 검토 모형: 보이는 문구에 내부 식별자 없음 -------------------------------------------------------------------


class PlainV2Test(Base):
    def _visible(self, model: dict) -> list[str]:
        """화면 함수가 보이는 필드만(header·case의 식별자 필드와 보고서 전문은 화면에 내지 않는다)."""
        texts = [model["title"], model["caution"], model["header"]["verdict_label"], model["header"]["meaning"],
                 model["case"]["item"], model["case"]["partner_name"], model["case"]["month_label"]]
        texts += [chip["text"] for chip in model["chips"]]
        texts += [f"{k} {v}" for k, v in model["basis"]]
        texts += [section["head"] + " " + " ".join(section["body"]) for section in model["found"]]
        what = model["what"] or {}
        for part in what.values():
            texts += [part["label"], part["value_text"], part["note"]]
        texts += [m["label"] + " " + m["text"] for m in model["meanings"]]
        conclusion = model["conclusion"]
        texts += [conclusion["title"], conclusion["meaning"], conclusion["not_completed"] or ""]
        return texts

    def test_fixture_run_visible_text_has_no_internal_identifiers(self):
        for lang in i18n.LANGS:
            model = plain.plain_model(FIXTURE_RUN, lang, repo_root=ROOT, period=("202201", "202412"), run_position=(0, 13))
            for text in self._visible(model):
                self.assertNoInternal(text, lang)
        ko = plain.plain_model(FIXTURE_RUN, "ko", repo_root=ROOT, period=("202201", "202412"), run_position=(0, 13))
        self.assertEqual([c["text"] for c in ko["chips"]],
                         ["경보 2024년 12월", "비교 기준 2023년 12월", "조사 2026-09-26 07:14 (최신, 13회 중)", "숫자 확인 완료"])
        self.assertTrue(ko["chips"][3]["ok"])
        self.assertIn(("자료", "관세청 수입통계 2022년 1월 ~ 2024년 12월"), ko["basis"])
        self.assertIn(("기준", "전년 같은 달과 비교. 단가 30%, 점유율 10%p"), ko["basis"])
        self.assertEqual(ko["found"][1]["body"], ["하위품목 1: 0.0%", "하위품목 2: 0.0%"])  # HS10 코드 대신 번호
        en = plain.plain_model(FIXTURE_RUN, "en", repo_root=ROOT, run_position=(2, 3))
        self.assertEqual([c["text"] for c in en["chips"]][:3],
                         ["Alert: December 2024", "Baseline: December 2023", "Investigated 2026-09-26 07:14 (1 of 3)"])
        self.assertEqual(en["basis"][0], ("Data", "Korea Customs Service import statistics (fixed at one point in time)"))
        single = plain.plain_model(FIXTURE_RUN, "ko", repo_root=ROOT, run_position=(0, 1))
        self.assertEqual(single["chips"][2]["text"], "조사 2026-09-26 07:14")

    def test_month_labels(self):
        self.assertEqual(i18n.month_long("202412", "ko"), "2024년 12월")
        self.assertEqual(i18n.month_long("202301", "en"), "January 2023")
        self.assertEqual(i18n.month_name("202412", "ko"), "12월")
        self.assertEqual(i18n.month_name("202412", "en"), "December")
        self.assertEqual(i18n.month_long("bad", "en"), "bad")

    def test_user_facing_strings_carry_no_status_codes_or_key_names(self):
        allowed = {"app.snapshot_none"}  # 관리자 사이드바의 설치 안내(담당자 화면에는 보이지 않는다)
        for key, entry in i18n.STRINGS.items():
            if key in allowed:
                continue
            for lang in i18n.LANGS:
                self.assertNoInternal(entry[lang], key)
                self.assertNotIn("NVIDIA_API_KEY", entry[lang], key)
                self.assertNotIn("snapshot_id", entry[lang], key)


# ---- UI4: 독립 검토 권고 7건 -----------------------------------------------------------------------------------------


def write_run(outputs: Path, run_id: str, case_id: str, execution: str | None, verdict: str | None = "HOLD",
              trace_case: str | None = None) -> Path:
    """합성 실행 폴더: execution이 None이면 실행 결과 기록 없이(진행 중) trace run_start 한 줄만 쓴다."""
    run_dir = outputs / run_id
    run_dir.mkdir(parents=True)
    stamp = app.run_stamp(run_id)
    if execution is not None:
        (run_dir / f"{app.RECORD_DOMAIN}-{stamp}.json").write_text(json.dumps(
            {"case_id": case_id, "execution_status": execution, "review_status_final": verdict}), encoding="utf-8")
    start = {"seq": 1, "event": "run_start", "stage": None, "data": {"case_id": trace_case or case_id}}
    (run_dir / f"{app.TRACE_DOMAIN}-{stamp}.jsonl").write_text(json.dumps(start) + "\n", encoding="utf-8")
    return run_dir


class NewResultAfterDecisionTest(Base):
    """권고 1: 결정 뒤 같은 사례를 다시 조사해 완료된 결과가 있으면 "새 조사 결과 · 결정 대기"."""
    CASE = "850490-PH-202412"

    def _index(self, tmp: str, *extra: tuple) -> dict:
        outputs = Path(tmp) / "outputs"
        write_run(outputs, "run_case-260926194101", self.CASE, "COMPLETED", "HOLD")
        for run_id, execution, verdict in extra:
            write_run(outputs, run_id, self.CASE, execution, verdict)
        return alerts.investigation_index(outputs)

    def test_newer_completed_run_becomes_new_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = self._index(tmp, ("run_case-260926194504", "COMPLETED", "MONITOR"))
            for validity in (approval.VALID, approval.REVIEW_REQUIRED):  # 이전 결정의 유효 상태와 무관하다
                decisions = {self.CASE: {"validity": validity, "decision": "HOLD", "run_id": "run_case-260926194101"}}
                state = listing.row_progress(self.CASE, index, decisions)
                self.assertEqual(state["state"], listing.NEW_RESULT)
                self.assertEqual((state["run_id"], state["verdict"], state["investigated"]), ("run_case-260926194504", "MONITOR", True))
            rows = [row(f"{self.CASE}"), row("850431-MX-202412")]
            states = {self.CASE: state, "850431-MX-202412": {"state": listing.AWAITING, "investigated": True, "verdict": "HOLD"}}
            self.assertEqual(listing.month_summary(rows, None, "202412", states)["awaiting"], 2)  # 내 결정을 기다리는 사례에 든다
            self.assertEqual([r["case_id"] for r in listing.filter_rows(rows, states, progress="awaiting")], [self.CASE, "850431-MX-202412"])
            self.assertEqual(listing.filter_rows(rows, states, progress="decided"), [])
            self.assertIn(listing.NEW_RESULT, listing.PROGRESS_FILTERS["all"])
            self.assertEqual(listing.PROGRESS_ORDER[listing.NEW_RESULT], listing.PROGRESS_ORDER[listing.AWAITING])
            self.assertEqual(listing.progress_cell(state, "ko"),
                             {"text": "새 조사 결과 · 결정 대기", "sub": "모니터링 제안", "kind": "done", "action": "view"})
            en = listing.progress_cell(state, "en")
            self.assertEqual((en["text"], en["sub"]), ("New result · awaiting your decision", "monitoring suggested"))
            for lang in i18n.LANGS:
                cell = listing.progress_cell(state, lang)
                self.assertNoInternal(cell["text"] + cell["sub"], lang)

    def test_failed_or_running_newer_run_is_not_counted(self):
        decisions = {self.CASE: {"validity": approval.VALID, "decision": "HOLD", "run_id": "run_case-260926194101"}}
        with tempfile.TemporaryDirectory() as tmp:
            index = self._index(tmp, ("run_case-260926194504", "FAILED", None), ("run_case-260926194600", None, None))
            state = listing.row_progress(self.CASE, index, decisions)
            self.assertEqual((state["state"], state["decision"]), (listing.DECIDED, "HOLD"))
            self.assertIsNone(listing.newer_completed_run(index[self.CASE]["runs"], "run_case-260926194101"))
        with tempfile.TemporaryDirectory() as tmp:  # 결정한 실행보다 오래된 완료 실행은 새 결과가 아니다
            index = self._index(tmp, ("run_case-260926190000", "COMPLETED", "MONITOR"))
            self.assertEqual(listing.row_progress(self.CASE, index, decisions)["state"], listing.DECIDED)
            self.assertIsNone(listing.newer_completed_run(index[self.CASE]["runs"], None))
            self.assertIsNone(listing.newer_completed_run(index[self.CASE]["runs"], "approval_record-260926194428"))

    def test_newest_of_several_completed_runs(self):
        runs = [{"run_id": "run_case-260926194504", "status": alerts.INVESTIGATED, "review_status_final": "MONITOR"},
                {"run_id": "run_case-260926195000", "status": alerts.INVESTIGATED, "review_status_final": "MAINTAIN"},
                {"run_id": "run_case-260926196000", "status": alerts.FAILED, "review_status_final": None}]
        self.assertEqual(listing.newer_completed_run(runs, "run_case-260926194101")["run_id"], "run_case-260926195000")


class PickRunDirByCaseTest(Base):
    """권고 2: 전후 폴더 차이로 고를 때 같은 사례의 폴더만."""

    def test_record_and_trace_run_start(self):
        with tempfile.TemporaryDirectory() as tmp:
            outputs = Path(tmp) / "outputs"
            write_run(outputs, "run_case-260926000005", CASE_ID, "COMPLETED")  # 실행 결과 기록으로
            write_run(outputs, "run_case-260926000010", "850431-XB-202412", "COMPLETED")  # 다른 사례(더 새것)
            write_run(outputs, "run_case-260926000020", "850432-XC-202412", None)  # 다른 사례, 진행 중(trace만)
            (outputs / "run_case-260926000030").mkdir()  # 아직 아무것도 없음
            case_of = lambda name: progress.run_dir_case(outputs / name)  # noqa: E731
            self.assertEqual(case_of("run_case-260926000005"), CASE_ID)
            self.assertEqual(case_of("run_case-260926000020"), "850432-XC-202412")
            self.assertIsNone(case_of("run_case-260926000030"))
            before = ["run_case-260926000000"]
            after = before + ["run_case-260926000005", "run_case-260926000010", "run_case-260926000020", "run_case-260926000030"]
            self.assertEqual(progress.pick_run_dir(before, after), "run_case-260926000030")  # 사례를 주지 않으면 가장 새 것(이전 동작)
            self.assertEqual(progress.pick_run_dir(before, after, None, case_id=CASE_ID, case_of=case_of), "run_case-260926000005")
            self.assertEqual(progress.pick_run_dir(before, after, None, case_id="850432-XC-202412", case_of=case_of),
                             "run_case-260926000020")  # 진행 중: trace run_start의 case_id로
            self.assertIsNone(progress.pick_run_dir(before, after, None, case_id="850450-JP-202412", case_of=case_of))
            self.assertEqual(progress.pick_run_dir(before, after, ["run_case-260926000010"], case_id=CASE_ID, case_of=case_of),
                             "run_case-260926000010")  # 표준 출력(그 조사 프로세스가 알린 폴더)이 먼저다
            # 기록과 trace가 다르면 기록이 먼저
            write_run(outputs, "run_case-260926000040", CASE_ID, "FAILED", None, trace_case="850431-XB-202412")
            self.assertEqual(case_of("run_case-260926000040"), CASE_ID)


class FakeProc:
    def __init__(self, waits):
        self.pid = 4321
        self.waits = list(waits)
        self.calls = []

    def wait(self, timeout=None):
        self.calls.append(timeout)
        outcome = self.waits.pop(0) if self.waits else 0
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class StopProcessGroupTest(Base):
    """권고 3: SIGKILL 뒤에도 wait로 회수한다."""

    def _run(self, proc, getpgid=None):
        sent = []
        progress.stop_process_group(proc, getpgid=getpgid or (lambda pid: 99), killpg=lambda group, sig: sent.append((group, sig)),
                                    wait_s=0.01)
        return sent

    def test_kill_then_reap(self):
        import signal
        import subprocess
        proc = FakeProc([subprocess.TimeoutExpired("x", 0.01), -9])
        self.assertEqual(self._run(proc), [(99, signal.SIGTERM), (99, signal.SIGKILL)])
        self.assertEqual(len(proc.calls), 2)  # TERM 뒤 wait, KILL 뒤 wait(회수)

    def test_term_is_enough(self):
        import signal
        proc = FakeProc([0])
        self.assertEqual(self._run(proc), [(99, signal.SIGTERM)])
        self.assertEqual(len(proc.calls), 1)

    def test_second_wait_timeout_and_gone_process_are_quiet(self):
        import subprocess
        proc = FakeProc([subprocess.TimeoutExpired("x", 0.01), subprocess.TimeoutExpired("x", 0.01)])
        self.assertEqual(len(self._run(proc)), 2)

        def gone(pid):
            raise ProcessLookupError

        proc = FakeProc([0])
        self.assertEqual(self._run(proc, gone), [])
        self.assertEqual(len(proc.calls), 1)  # 이미 끝난 프로세스도 회수한다


class RetryAndSkipTest(Base):
    """권고 4·5."""

    def test_retrying_only_when_flag_is_true(self):
        base = [ev("tool_call", "basic", tool="get_history"), ev("model_request")]
        self.assertTrue(progress.step_state(base + [ev("model_error", retrying=True)])["retrying"])
        self.assertFalse(progress.step_state(base + [ev("model_error", retrying=False)])["retrying"])
        self.assertFalse(progress.step_state(base + [ev("model_error")])["retrying"])
        self.assertFalse(progress.step_state(base + [ev("model_error", retrying="yes")])["retrying"])
        self.assertFalse(progress.step_state(base + [ev("model_error", retrying=True), ev("model_request")])["retrying"])

    def test_step_without_marker_is_skipped(self):
        seq = [ev("tool_call", "basic", tool="check_comparability"), ev("tool_call", "basic", tool="get_history"),
               ev("stage_start", "critic", stage="critic")]  # 점유율만 발동: decompose_hs 없음
        steps = progress.step_state(seq)
        self.assertEqual(steps["states"], ["done", "done", "skipped", "current", "pending"])
        self.assertEqual((steps["done"], steps["current"]), (3, 3))
        self.assertAlmostEqual(progress.progress_ratio(steps), 0.6)  # 건너뛴 단계도 끝난 것으로 센다
        seq += [ev("stage_end", "critic", stage="critic")]
        self.assertEqual(progress.step_state(seq)["states"], ["done", "done", "skipped", "done", "current"])  # 뒤 단계는 건너뜀 아님
        seq += [ev("tool_call", None, tool="verify_evidence"), ev("run_end")]
        steps = progress.step_state(seq)
        self.assertEqual(steps["states"], ["done", "done", "skipped", "done", "done"])
        self.assertEqual(progress.progress_ratio(steps), 1.0)
        self.assertEqual(progress.step_state([ev("run_end")])["states"], ["done"] * 5)  # 표지가 없으면 건너뜀으로 보지 않는다
        self.assertEqual(progress.step_state([])["states"], ["current"] + ["pending"] * 4)

    def test_skipped_label_both_languages(self):
        self.assertEqual(i18n.t("load.skipped", "ko"), "건너뜀")
        self.assertEqual(i18n.t("load.skipped", "en"), "Skipped")


class LoadingTextTest(Base):
    """권고 6·7: 재생/실제 실행 안내와 재검토 필요 보조 문구."""

    def test_expect_by_run_kind(self):
        self.assertEqual(i18n.t("load.expect_replay", "ko"), "저장해 둔 응답을 다시 쓰는 시연 실행이라 몇 초면 끝납니다. 끝나면 결과 화면이 바로 열립니다.")
        self.assertIn("finishes in a few seconds", i18n.t("load.expect_replay", "en"))
        self.assertTrue(i18n.t("load.expect", "ko").startswith("보통 30초에서 90초가 걸립니다."))
        self.assertNotIn("30", i18n.t("load.expect_replay", "ko"))

    def test_footnote_real_mentions_nim_and_replay_unchanged(self):
        self.assertTrue(i18n.t("load.footnote", "ko").endswith(
            "조사자와 검수자는 정해진 조회 도구로 통계 원본만 조회합니다. 모델 추론 요청은 NVIDIA 클라우드(NIM)로 갑니다."))
        self.assertTrue(i18n.t("load.footnote", "en").endswith(
            "through fixed lookup tools. Model inference requests go to the NVIDIA cloud (NIM)."))
        self.assertEqual(i18n.t("load.footnote_replay", "ko"),
                         "이 조사는 저장해 둔 모델 응답을 다시 쓰는 시연 실행(재생)이라 외부 모델을 부르지 않습니다. 조사가 실패하면 여기서 "
                         "알려 주고 \"다시 시도\" 버튼이 나옵니다.")
        self.assertNotIn("NIM", i18n.t("load.footnote_replay", "en"))

    def test_review_required_sub_is_neutral(self):
        self.assertEqual(listing.progress_cell({"state": listing.REVIEW_REQUIRED}, "ko")["sub"], "근거 보고서와 맞지 않습니다")
        self.assertEqual(listing.progress_cell({"state": listing.REVIEW_REQUIRED}, "en")["sub"], "No longer matches its report")


if __name__ == "__main__":
    unittest.main()
