"""담당자용 화면(UI2) 순수 논리 시험. streamlit·네트워크·키 없이 돈다(화면 함수는 부르지 않는다).

대상: tradesentry.ui.i18n(문구 표), alerts(경보 지표 추출·조사 상태), plain(담당자용 모형), records(결정 기록 불변식),
approval.record(단위 A1). 고정 입력은 tests/units/A2/fixture/run_case-260926071424/(키 없는 재생 실행 A)와 이 파일 안의 합성
보고서다. 골든 시험 틀과 같이 봉인 폴더·홈을 없는 경로로 고정하고 소켓 연결을 막는다.
"""
import ast
import json
import os
import re
import shutil
import socket
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest import mock

from tradesentry import app
from tradesentry.approval import record as approval
from tradesentry.ui import alerts, i18n, plain, records

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_RUN = ROOT / "tests" / "units" / "A2" / "fixture" / "run_case-260926071424"
CASE_ID = "850450-XA-202412"
PLACEHOLDER_RE = re.compile(r"\{([a-z_0-9]+)\}")
FORBIDDEN_IN_MEANINGS = ("부정", "위법", "불법", "원산지", "조작", "탈세", "허위", "적발", "혐의", "위반", "정상 확정")
_ABS_PATH_RE = re.compile(r"/(?:Users|home|private|tmp|var)/")


def _refuse(*args, **kwargs):
    raise OSError("시험에서는 네트워크를 쓰지 않는다")


class Base(unittest.TestCase):
    def setUp(self):
        missing = Path(tempfile.gettempdir()) / "tradesentry-ui2-missing"
        env = mock.patch.dict(os.environ, {"TRADESENTRY_SEALED_DIR": str(missing / "sealed"), "HOME": str(missing / "home")})
        env.start()
        self.addCleanup(env.stop)
        for target in ("socket.socket.connect", "socket.create_connection"):
            patcher = mock.patch(target, _refuse)
            patcher.start()
            self.addCleanup(patcher.stop)


# ---- 경계: 순수 논리 모듈은 streamlit을 import하지 않는다 -------------------------------------------------------------


class ImportShapeTest(unittest.TestCase):
    def test_pure_modules_do_not_import_streamlit(self):
        for name in ("i18n", "alerts", "plain", "records", "progress", "listing"):
            tree = ast.parse((ROOT / "src" / "tradesentry" / "ui" / f"{name}.py").read_text(encoding="utf-8"))
            names = [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names] + \
                    [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module]
            self.assertFalse(any(n.split(".")[0] == "streamlit" for n in names), name)

    def test_no_local_absolute_paths_in_sources(self):
        for path in (ROOT / "src" / "tradesentry" / "ui").rglob("*.py"):
            self.assertIsNone(_ABS_PATH_RE.search(path.read_text(encoding="utf-8")), path.name)


# ---- i18n ------------------------------------------------------------------------------------------------------


class I18nTest(unittest.TestCase):
    def test_every_key_has_both_languages_non_empty_and_same_placeholders(self):
        for key, entry in i18n.STRINGS.items():
            with self.subTest(key=key):
                self.assertEqual(set(entry), set(i18n.LANGS))
                for lang in i18n.LANGS:
                    self.assertTrue(entry[lang].strip(), f"{key}.{lang}가 비었다")
                self.assertEqual(set(PLACEHOLDER_RE.findall(entry["ko"])), set(PLACEHOLDER_RE.findall(entry["en"])), key)

    def test_t_formats_and_falls_back_to_key(self):
        self.assertEqual(i18n.t("home.count", "ko", n=11), "11건")
        self.assertEqual(i18n.t("home.count", "en", n=11), "11")
        self.assertEqual(i18n.t("no.such.key", "en"), "no.such.key")

    def test_labels(self):
        self.assertEqual(i18n.verdict_label("MAINTAIN", "en"), "Keep under review")  # UI3: 상태 코드 없이
        self.assertEqual(i18n.verdict_label("MAINTAIN", "ko"), "검토 유지")
        self.assertEqual(i18n.verdict_label(None, "ko"), "—")
        self.assertEqual(i18n.verdict_label("WEIRD", "ko"), "WEIRD")  # 모르는 값은 원문 그대로
        self.assertEqual(i18n.month_label("202412", "ko"), "2024년 12월")
        self.assertEqual(i18n.month_label("202412", "en"), "Dec 2024")
        self.assertEqual(i18n.month_short("202301"), "2023-01")
        self.assertEqual(i18n.hs6_name("850432", "en"), "Transformers 1–16 kVA · voltage regulators")
        self.assertIsNone(i18n.hs6_name("999999"))
        self.assertEqual(i18n.item_label("999999"), "HS6 999999")

    def test_country_names_both_languages(self):
        ko, en = i18n.load_country_names(ROOT, "ko"), i18n.load_country_names(ROOT, "en")
        self.assertEqual(ko.get("CN"), "중국")
        self.assertEqual(en.get("CN"), "China")
        self.assertEqual(i18n.partner_label("XA", ko), "가상국 A")  # UI3: 합성 픽스처 가상 상대국 이름
        self.assertEqual(i18n.partner_label("XA", en), "Synthetic partner A")
        self.assertEqual(i18n.partner_label("ZZ", ko), "ZZ")  # 모르는 코드는 그대로

    def test_status_meanings_avoid_forbidden_terms(self):
        for key, entry in i18n.STRINGS.items():
            if key.startswith(("meaning.", "define.", "verdict.")):
                for term in FORBIDDEN_IN_MEANINGS:
                    self.assertNotIn(term, entry["ko"], key)


# ---- alerts ----------------------------------------------------------------------------------------------------


def fake_envelope(partner="XA", month="202412", baseline="202312", *, u1="3.60", r_u="-40.0", s1="6.0", d_s="-4.0"):
    def metric(symbol, period, value, base=None):
        return {"metric_id": f"{symbol}-x", "inputs": {"metric": symbol, "hs6": "850450", "partner": partner, "period": period,
                                                        "baseline_period": base}, "value": value, "unit": "x", "evidence_ids": []}
    return {"tool": "get_history", "metrics": [
        metric("U", baseline, Decimal("6.00")), metric("U", month, None if u1 is None else Decimal(u1)),
        metric("r_U", month, None if r_u is None else Decimal(r_u), baseline),
        metric("s", baseline, Decimal("10.0")), metric("s", month, Decimal(s1)),
        metric("d_s", month, Decimal(d_s), baseline),
        metric("U", month, Decimal("99.99")) | {"inputs": {"metric": "U", "partner": "ZZ", "period": month}},  # 다른 상대국은 무시
    ], "missingness": []}


def fake_case(case_id=CASE_ID, signals=None):
    hs6, partner, month = case_id.split("-")
    return {"case_id": case_id, "hs6": hs6, "partner": partner, "month": month, "baseline_month": f"{int(month[:4]) - 1}{month[4:]}",
            "signals": signals or {"unit_value": "TRIGGERED", "share": "NOT_TRIGGERED"}, "snapshot_id": "controlled_fixture_v0",
            "policy_version": "policy_v1"}


class AlertsTest(Base):
    def test_metrics_are_copied_from_envelope_without_recomputation(self):
        row = alerts.alert_row(fake_case(), fake_envelope())
        self.assertEqual({k: str(v) for k, v in row["metrics"].items()},
                         {"U_0": "6.00", "U_1": "3.60", "r_U": "-40.0", "s_0": "10.0", "s_1": "6.0", "d_s": "-4.0"})
        self.assertTrue(row["unit_value_triggered"])
        self.assertFalse(row["share_triggered"])
        self.assertIsInstance(row["metrics"]["U_1"], Decimal)

    def test_none_values_stay_none(self):
        row = alerts.alert_row(fake_case(signals={"unit_value": "NOT_TRIGGERED", "share": "TRIGGERED"}),
                               fake_envelope(u1=None, r_u=None, s1="0.0", d_s="-10.0"))
        self.assertIsNone(row["metrics"]["U_1"])
        self.assertIsNone(row["metrics"]["r_U"])
        self.assertTrue(row["share_triggered"])

    def test_alerts_for_month_uses_case_list_and_history_tool(self):
        cases = {"cases": [fake_case(), fake_case("850431-XB-202412"), fake_case("850450-XA-202411")]}
        seen = []

        def history(request):
            seen.append(request)
            return fake_envelope(partner=request["scope"]["partner"], month=request["scope"]["month"],
                                 baseline=request["scope"]["baseline_month"])
        rows = alerts.alerts_for_month("controlled_fixture_v0", "202412", cases=cases, history=history)
        self.assertEqual([r["case_id"] for r in rows], ["850450-XA-202412", "850431-XB-202412"])
        self.assertEqual(seen[0]["scope"], {"hs6": "850450", "partner": "XA", "month": "202412", "baseline_month": "202312"})
        self.assertEqual(seen[0]["attempt"], 1)
        self.assertEqual(alerts.list_months("controlled_fixture_v0", cases=cases), ["202412", "202411"])

    def test_history_request_shape(self):
        request = alerts.history_request(fake_case())
        self.assertEqual(set(request), {"case_id", "snapshot_id", "scope", "args", "attempt"})

    def test_investigation_status_from_run_records_excluding_sealed(self):
        with tempfile.TemporaryDirectory() as tmp:
            outputs = Path(tmp) / "outputs"
            shutil.copytree(FIXTURE_RUN, outputs / "run_case-260926071424")
            shutil.copytree(FIXTURE_RUN, outputs / "run_case-260926080000")  # 같은 사례의 더 새 실행
            (outputs / "sealed" / "run_case-260926090000").mkdir(parents=True)
            shutil.copy(FIXTURE_RUN / "runlog_run_record-260926071424.json",
                        outputs / "sealed" / "run_case-260926090000" / "runlog_run_record-260926090000.json")
            failed = outputs / "run_case-260926070000"
            failed.mkdir()
            (failed / "runlog_run_record-260926070000.json").write_text(json.dumps(
                {"case_id": "850431-XB-202412", "execution_status": "FAILED", "review_status_final": None}), encoding="utf-8")
            (outputs / ".download-run_case-260926095959").mkdir()
            index = alerts.investigation_index(outputs)
            self.assertEqual(set(index), {CASE_ID, "850431-XB-202412"})
            status = alerts.investigation_status(CASE_ID, outputs)
            self.assertEqual((status["status"], status["run_id"], status["review_status_final"]),
                             (alerts.INVESTIGATED, "run_case-260926080000", "MONITOR"))
            self.assertEqual([r["run_id"] for r in status["runs"]], ["run_case-260926080000", "run_case-260926071424"])
            self.assertEqual(alerts.investigation_status("850431-XB-202412", index=index)["status"], alerts.FAILED)
            self.assertEqual(alerts.investigation_status("850432-XC-202412", index=index)["status"], alerts.NOT_INVESTIGATED)
            self.assertIsNone(alerts.investigation_status("850432-XC-202412", index=index)["run_id"])
            rows = [alerts.alert_row(fake_case(), fake_envelope()), alerts.alert_row(fake_case("850431-XB-202412"), fake_envelope(partner="XB")),
                    alerts.alert_row(fake_case("850432-XC-202412", {"unit_value": "NOT_TRIGGERED", "share": "TRIGGERED"}), fake_envelope(partner="XC"))]
            summary = alerts.summary(rows, {"cases": [1, 2, 3, 4, 5]}, index)
            self.assertEqual(summary, {"unit_value": 2, "share": 1, "investigated": 1, "total": 3, "all_months": 5})
            self.assertEqual([r["case_id"] for r in alerts.filter_alerts(rows, index, status=alerts.INVESTIGATED)], [CASE_ID])
            self.assertEqual([r["case_id"] for r in alerts.filter_alerts(rows, index, signal="share")], ["850432-XC-202412"])
            self.assertEqual([r["case_id"] for r in alerts.filter_alerts(rows, index, search="xb")], ["850431-XB-202412"])
            self.assertEqual([r["case_id"] for r in alerts.filter_alerts(rows, index, search="인덕터", labels={"850450": "인덕터 (기타)"})], [CASE_ID])

    def test_history_signal_value_only_for_current_snapshot_alert(self):
        row = alerts.alert_row(fake_case(), fake_envelope())
        self.assertEqual(alerts.history_signal(row), {"kind": "unit_value", "value": Decimal("-40.0")})  # 같은 스냅샷: 값
        share = alerts.alert_row(fake_case(signals={"unit_value": "NOT_TRIGGERED", "share": "TRIGGERED"}), fake_envelope(d_s="-19.3"))
        self.assertEqual(alerts.history_signal(share), {"kind": "share", "value": Decimal("-19.3")})
        self.assertEqual(alerts.history_signal(None), {"kind": None, "value": None})  # 다른 스냅샷의 사례: 값 없음
        none_value = alerts.alert_row(fake_case(), fake_envelope(r_u=None))
        self.assertEqual(alerts.history_signal(none_value), {"kind": None, "value": None})

    def test_completed_runs_filtered_by_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            outputs = Path(tmp) / "outputs"
            shutil.copytree(FIXTURE_RUN, outputs / "run_case-260926071424")
            write_synthetic_run(outputs, "run_case-260926080000")  # 실자료 스냅샷 COMPLETED
            write_synthetic_run(outputs, "run_case-260926090000", execution="FAILED")
            index = alerts.investigation_index(outputs)
            self.assertEqual([r["run_id"] for r in alerts.completed_runs(index)], ["run_case-260926080000", "run_case-260926071424"])
            self.assertEqual([r["case_id"] for r in alerts.completed_runs(index, "controlled_fixture_v0")], [CASE_ID])
            self.assertEqual(alerts.completed_runs(index, "no_such_snapshot"), [])

    def test_text_helpers(self):
        self.assertEqual(alerts.number_text(Decimal("1410.61")), "1,410.61")
        self.assertEqual(alerts.signed_text(Decimal("663.4")), "+663.4")
        self.assertEqual(alerts.signed_text(Decimal("-42.3")), "−42.3")
        self.assertEqual(alerts.signed_text(Decimal("0.0")), "0.0")
        self.assertIsNone(alerts.signed_text(None))
        self.assertEqual(alerts.stamp_label("run_case-260926013125"), "2026-09-26 01:31")
        self.assertEqual(alerts.default_snapshot(["controlled_fixture_v0", "kcs_202201_202412_v2"]), "kcs_202201_202412_v2")
        self.assertEqual(alerts.default_snapshot(["controlled_fixture_v0"]), "controlled_fixture_v0")
        self.assertIsNone(alerts.default_snapshot([]))


# ---- plain -----------------------------------------------------------------------------------------------------


def synthetic_report(case_id="850432-CN-202301", status="MAINTAIN", execution="COMPLETED"):  # execution은 기록 쪽 인자(여기서는 무시)
    """decomposition·comparison·share claim과 가설이 있는 합성 보고서(실제 통계가 아니다)."""
    def claim(cid, ctype, metric, value, unit, direction, partner="CN", period="202301", base="202201"):
        return {"claim_id": cid, "claim_type": ctype, "hs6": "850432", "partner": partner, "period": period,
                "baseline_period": base, "metric": metric, "value": value, "unit": unit, "direction": direction,
                "evidence_ids": ["ev:controlled_fixture_v0:observation:1"], "text": "합성"}
    claims = [
        claim("c1", "change", "r_U", Decimal("-50.2"), "%", "DOWN"),
        claim("c2", "decomposition", "within_effect", Decimal("-83.65"), "USD/kg", "DOWN"),
        claim("c3", "decomposition", "mix_effect", Decimal("19.24"), "USD/kg", "UP"),
        claim("c4", "decomposition", "residual", Decimal("0.07"), "USD/kg", "UP"),
        claim("c5", "comparison", "r_U", Decimal("-59.8"), "%", "DOWN", partner="US"),
        claim("c6", "share", "s", Decimal("13.2"), "%", "NA", period="202201", base=None),
        claim("c7", "share", "s", Decimal("11.9"), "%", "NA", base=None),
        claim("c8", "share_change", "d_s", Decimal("-1.2"), "pp", "DOWN"),
    ]
    return {"report_id": "r1", "run_id": "run_case-260926013125", "case_id": case_id, "mode": "full", "claims": claims,
            "narrative": "단가 변화율 주장은 발동했으나 구성효과로 설명되지 않아 계속 검토가 필요하며, 점유율 주장은 발동하지 않았다.",
            "hypotheses": ["중국 내 수요 구조 변화가 단가 변동에 영향을 미쳤을 가능성"], "review_status": status,
            "signal_status": {"unit_value": status, "share": "NOT_TRIGGERED"}, "unresolved_evidence": False,
            "evidence_ids": ["ev:controlled_fixture_v0:observation:1"], "validator_findings": [],
            "report_hash": "a" * 64, "created_at": "2026-09-26T01:31:00+09:00", "policy_version": "policy_v1",
            "snapshot_id": "kcs_202201_202412_v2", "grouping_version": "g0"}


def synthetic_record(case_id="850432-CN-202301", status="MAINTAIN", execution="COMPLETED"):
    return {"run_id": "run_case-260926013125", "case_id": case_id, "dataset": "real_dev", "mode": "full", "policy_version": "policy_v1",
            "rulebook_version": "RB-1", "snapshot_id": "kcs_202201_202412_v2", "grouping_version": "g0", "code_version": "abc",
            "review_status_final": status if execution == "COMPLETED" else None,
            "signal_status": {"unit_value": status, "share": "NOT_TRIGGERED"}, "unresolved_evidence": False,
            "execution_status": execution, "tool_attempts": 5, "model_requests": 3, "tokens_in": 1, "tokens_out": 1,
            "wall_ms": 1, "critic_used": True, "revision_used": False, "errors": []}


def write_synthetic_run(root: Path, name="run_case-260926013125", **kwargs) -> Path:
    run_dir = root / name
    run_dir.mkdir(parents=True)
    stamp = name.rsplit("-", 1)[-1]
    (run_dir / f"reports_render_ko-{stamp}.json").write_text(json.dumps(synthetic_report(**kwargs), ensure_ascii=False, default=float), encoding="utf-8")
    (run_dir / f"runlog_run_record-{stamp}.json").write_text(json.dumps(synthetic_record(**kwargs), ensure_ascii=False), encoding="utf-8")
    (run_dir / f"runlog_trace-{stamp}.jsonl").write_text("", encoding="utf-8")
    return run_dir


class PlainTest(Base):
    def test_fixture_run_ko(self):
        model = plain.plain_model(FIXTURE_RUN, "ko", repo_root=ROOT)
        self.assertEqual(model["title"], "가상국 A산 인덕터 (기타)의 kg당 수입단가가 1년 전보다 절반 가까이 낮아졌습니다")
        self.assertEqual(model["what"]["unit"]["value"], "−40.0")  # claim c1 값 그대로
        self.assertEqual(model["what"]["unit"]["note"], "기준(30%)을 넘어 경보")
        self.assertEqual((model["what"]["share"]["s0"], model["what"]["share"]["s1"], model["what"]["share"]["value"]), ("10.0", "6.0", "−4.0"))
        self.assertEqual(model["header"]["verdict"], "MONITOR")
        kinds = [s["kind"] for s in model["found"]]
        self.assertEqual(kinds, ["decomposition", "sub_items"])  # 있는 claim만
        self.assertIn("−2.40 USD/kg", model["found"][0]["body"][0])
        self.assertEqual(model["found"][0]["head"], "하위품목 구성이 바뀐 것으로 설명됩니다.")
        self.assertEqual(model["alternatives"]["items"], [])
        self.assertIsNone(model["alternatives"]["original_mark"])
        self.assertTrue(model["conclusion"]["narrative"].startswith("단가 변화는 하위품목 구성효과로"))
        self.assertTrue(model["verified"]["ok"])
        self.assertEqual(model["verified"]["claims"], 6)
        self.assertIn(("확인", "보고서의 숫자 6개를 통계 원본과 대조해 모두 일치"), model["basis"])
        self.assertEqual([m["current"] for m in model["meanings"]], [False, True, False])
        self.assertIsNone(_ABS_PATH_RE.search(json.dumps(model, ensure_ascii=False, default=str)))

    def test_fixture_run_en_keeps_korean_original(self):
        model = plain.plain_model(FIXTURE_RUN, "en", repo_root=ROOT)
        self.assertEqual(model["title"], "The unit value (USD/kg) of Inductors, other imported from Synthetic partner A has fallen by roughly half from a year earlier")
        self.assertEqual(model["conclusion"]["original_mark"], "(Korean original)")
        self.assertTrue(model["conclusion"]["narrative"].startswith("단가 변화는"))  # 원문은 한국어 그대로
        self.assertEqual(model["header"]["verdict_label"], "Monitor")
        self.assertEqual(model["what"]["share"]["note"], "−4.0 pp, below the 10 pp threshold → no alert")

    def test_synthetic_report_sections_and_numbers(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = write_synthetic_run(Path(tmp) / "outputs")
            ko = plain.plain_model(run_dir, "ko", repo_root=ROOT)
            en = plain.plain_model(run_dir, "en", repo_root=ROOT)
        self.assertEqual(ko["title"], "중국산 계기용 변압기 (중용량) · 전압 조정기의 kg당 수입단가가 1년 전보다 절반 가까이 낮아졌습니다")
        self.assertEqual(ko["what"]["unit"]["value"], "−50.2")
        self.assertEqual([s["kind"] for s in ko["found"]], ["decomposition", "comparison", "share"])
        decomposition, comparison, share = ko["found"]
        self.assertEqual(decomposition["head"], "하위품목 구성이 바뀐 탓만으로는 설명되지 않습니다.")
        self.assertIn("−83.65 USD/kg", decomposition["body"][0])
        self.assertIn("+19.24 USD/kg", decomposition["body"][0])
        self.assertIn("+0.07 USD/kg", decomposition["body"][0])
        self.assertEqual(comparison["body"][0], "같은 품목의 미국산 kg당 단가는 같은 기간 −59.8% 내렸습니다.")
        self.assertEqual(comparison["body"][-1], "시장 전체 요인일 가능성을 열어 두어야 합니다.")
        self.assertEqual(share["head"], "점유율은 크게 움직이지 않았습니다.")
        self.assertEqual(share["body"][0], "13.2%에서 11.9%로, 기준(10%p)에 미치지 않습니다.")
        self.assertEqual(ko["alternatives"]["items"], ["중국 내 수요 구조 변화가 단가 변동에 영향을 미쳤을 가능성"])
        self.assertEqual(ko["conclusion"]["title"], "결론 — 검토 유지")
        self.assertEqual(en["found"][1]["body"][0], "Over the same period, the unit value of the same product from USA fell by −59.8%.")
        self.assertEqual(en["found"][2]["body"][0], "From 13.2% to 11.9%, below the threshold (10 pp).")
        self.assertEqual(en["alternatives"]["original_mark"], "(Korean original)")
        self.assertEqual(en["alternatives"]["items"], ko["alternatives"]["items"])  # 가설 원문은 그대로
        self.assertEqual(en["conclusion"]["title"], "Conclusion — Keep under review")

    def test_not_completed_run_has_no_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = write_synthetic_run(Path(tmp) / "outputs", execution="FAILED")
            model = plain.plain_model(run_dir, "ko", repo_root=ROOT)
        self.assertFalse(model["header"]["completed"])
        self.assertIsNone(model["header"]["verdict"])
        self.assertEqual(model["header"]["verdict_label"], "—")
        self.assertEqual(model["conclusion"]["not_completed"], "조사가 끝나지 않아 제안이 없습니다.")  # UI3: 상태 코드 없이
        self.assertNotIn("FAILED", json.dumps(model["chips"], ensure_ascii=False))
        self.assertFalse(model["verified"]["ok"])

    def test_band_and_title_rules(self):
        self.assertEqual(plain.band_key(Decimal("-32.0")), "band.notable")
        self.assertEqual(plain.band_key(Decimal("-50.2")), "band.near_half")
        self.assertEqual(plain.band_key(Decimal("80.7")), "band.large")
        self.assertEqual(plain.band_key(Decimal("663.4")), "band.double")
        self.assertIsNone(plain.band_key(None))
        unit = {"triggered": False, "value": None}
        share = {"triggered": True, "value": Decimal("-19.3")}
        self.assertEqual(plain.title_sentence("ko", "품목", "필리핀", unit, share), "필리핀의 품목 수입 점유율이 1년 전보다 크게 낮아졌습니다")
        self.assertEqual(plain.title_sentence("en", "X", "Y", {"triggered": True, "value": Decimal("103.9")}, None),
                         "The unit value (USD/kg) of X imported from Y has risen more than twofold from a year earlier")
        self.assertEqual(plain.title_sentence("ko", "X", "Y", {"triggered": True, "value": None}, None), "Y산 X의 kg당 수입단가를 1년 전과 비교할 수 없습니다")


# ---- records · A1 -----------------------------------------------------------------------------------------------


class FakeClock:
    def __init__(self, start: datetime):
        self.now = start

    def __call__(self) -> datetime:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


class RecordsTest(Base):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.outputs = Path(self.tmp.name) / "outputs"
        self.run_dir = write_synthetic_run(self.outputs)
        self.loaded = app.load_run(self.run_dir)
        self.clock = FakeClock(datetime(2026, 9, 26, 18, 30, 0, 500000, tzinfo=records.KST))

    def test_a1_run_and_check(self):
        report = self.loaded["report"]
        out = approval.run({"report": report, "execution_status": "COMPLETED", "reviewer_label": "담당자 A",
                            "timestamp": "2026-09-26T18:30:00+09:00", "code_version": "abc"})
        self.assertEqual(set(out), set(approval.INPUT_KEYS) - {"report", "execution_status"} | {"report_hash", "evidence_digest", "snapshot_id", "policy_version", "status"})
        self.assertEqual(out["report_hash"], "a" * 64)
        self.assertEqual(out["evidence_digest"], approval.evidence_digest(["ev:controlled_fixture_v0:observation:1"]))
        self.assertEqual(out["status"], "VALID")
        self.assertEqual(approval.check(out, report), "VALID")
        self.assertEqual(approval.check(out, {**report, "report_hash": "b" * 64}), "REVIEW_REQUIRED")
        self.assertEqual(approval.check(out, {**report, "evidence_ids": []}), "REVIEW_REQUIRED")
        self.assertEqual(approval.check(out, None), "REVIEW_REQUIRED")
        with self.assertRaises(ValueError):
            approval.run({"report": report, "execution_status": "FAILED", "reviewer_label": "x", "timestamp": "t"})
        with self.assertRaises(ValueError):
            approval.run({"report": {**report, "report_hash": None}, "execution_status": "COMPLETED", "reviewer_label": "x", "timestamp": "t"})
        self.assertEqual(approval.evidence_digest(["b", "a", "a"]), approval.evidence_digest(["a", "b"]))  # 순서·중복 무관

    def test_build_record_rejects_incomplete_and_bad_decision(self):
        with self.assertRaises(ValueError):
            records.build_record(self.loaded, "APPROVE", "", "x")
        with tempfile.TemporaryDirectory() as tmp:
            failed = app.load_run(write_synthetic_run(Path(tmp) / "outputs", execution="TIMEOUT"))
        with self.assertRaises(ValueError):
            records.build_record(failed, "MAINTAIN", "", "x")

    def test_save_is_append_only_with_n8_reservation_and_reread_validity(self):
        record = records.build_record(self.loaded, "MONITOR", " 메모 ", " 담당자 A ", "2026-09-26T18:30:00+09:00")
        self.assertEqual(set(record), set(records.RECORD_KEYS))
        self.assertEqual((record["decision"], record["suggested"], record["memo"], record["reviewer_label"]), ("MONITOR", "MAINTAIN", "메모", "담당자 A"))
        first = records.save_record(self.outputs, record, clock=self.clock, sleep=self.clock.sleep)
        second = records.save_record(self.outputs, record, clock=self.clock, sleep=self.clock.sleep)
        self.assertEqual(first["path"], "outputs/approval_record-260926183001/approval_record-260926183001.json")  # 다음 초까지 기다림
        self.assertEqual(second["path"], "outputs/approval_record-260926183002/approval_record-260926183002.json")  # 이미 있으면 다음 초
        self.assertEqual(first["record"]["record_id"], "approval_record-260926183001")
        self.assertTrue((self.outputs / "approval_record-260926183001" / "approval_record-260926183001.json").is_file())
        self.assertEqual(records.list_record_dirs(self.outputs), ["approval_record-260926183002", "approval_record-260926183001"])
        loaded = records.load_records(self.outputs)
        self.assertEqual([r["record_id"] for r in loaded], ["approval_record-260926183002", "approval_record-260926183001"])
        for_case = records.records_for_case(self.outputs, "850432-CN-202301")
        self.assertEqual([r["validity"] for r in for_case], ["VALID", "VALID"])
        self.assertEqual(records.records_for_case(self.outputs, "850450-XA-202412"), [])
        # 보고서가 뒤에 바뀌면 기록은 그대로 남고 유효 상태만 REVIEW_REQUIRED다
        report_path = next(self.run_dir.glob("reports_render_ko-*.json"))
        changed = json.loads(report_path.read_text(encoding="utf-8"))
        changed["report_hash"] = "c" * 64
        report_path.write_text(json.dumps(changed, ensure_ascii=False), encoding="utf-8")
        self.assertEqual([r["validity"] for r in records.records_for_case(self.outputs, "850432-CN-202301")], ["REVIEW_REQUIRED", "REVIEW_REQUIRED"])
        self.assertEqual(records.load_records(self.outputs)[0]["report_hash"], "a" * 64)  # 기록 파일은 고치지 않았다
        # 실행 폴더가 사라져도 REVIEW_REQUIRED
        shutil.rmtree(self.run_dir)
        self.assertEqual(records.records_for_case(self.outputs, "850432-CN-202301")[0]["validity"], "REVIEW_REQUIRED")

    def test_sealed_and_download_dirs_are_ignored(self):
        (self.outputs / "sealed" / "approval_record-260926183001").mkdir(parents=True)
        (self.outputs / ".download-approval_record-260926183001").mkdir()
        self.assertEqual(records.list_record_dirs(self.outputs), [])
        record = records.build_record(self.loaded, "HOLD", "", "x", "2026-09-26T18:30:00+09:00")
        saved = records.save_record(self.outputs, record, clock=self.clock, sleep=self.clock.sleep)
        self.assertEqual(saved["record"]["record_id"], "approval_record-260926183002")  # sealed에 같은 이름이 있어 다음 초
        self.assertFalse((self.outputs / "approval_record-260926183001").exists())

    def test_timestamp_is_kst_iso(self):
        text = records.timestamp_text(datetime(2026, 9, 26, 9, 0, 0, tzinfo=timezone.utc))
        self.assertEqual(text, "2026-09-26T18:00:00+09:00")


if __name__ == "__main__":
    unittest.main()
