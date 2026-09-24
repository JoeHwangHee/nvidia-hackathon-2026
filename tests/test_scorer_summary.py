"""독립 채점기 단위 C4(보조 지표·요약) 시험: Wilson·Newcombe·McNemar 계산, 룰북 B4 지표, B7 요약 양식.

통계 함수는 채점기와 다른 경로(float·math)로 따로 짠 식과 맞춰 본다. 시험 안의 float는 대조용이며 채점기 출력에는
float가 없다.
"""
import math
import unittest
from decimal import Decimal
from fractions import Fraction

import scorer_fixtures as fx
from eval.scorer import claims as c1
from eval.scorer import summary as c4


def wilson_float(x: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = x / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return center - half, center + half


def newcombe_float(a: int, b: int, c: int, d: int) -> tuple[float, float]:
    n = a + b + c + d
    l1, u1 = wilson_float(a + b, n)
    l2, u2 = wilson_float(a + c, n)
    p1, p2 = (a + b) / n, (a + c) / n
    product = (a + b) * (c + d) * (a + c) * (b + d)
    phi = 0.0 if product == 0 else (a * d - b * c) / math.sqrt(product)
    low = (p1 - p2) - math.sqrt(max(0.0, (p1 - l1) ** 2 - 2 * phi * (p1 - l1) * (u2 - p2) + (u2 - p2) ** 2))
    high = (p1 - p2) + math.sqrt(max(0.0, (u1 - p1) ** 2 - 2 * phi * (u1 - p1) * (p2 - l2) + (p2 - l2) ** 2))
    return low, high


class StatisticsTest(unittest.TestCase):
    def test_wilson_rulebook_half_widths(self):
        low, high = c4.wilson(20, 40)
        self.assertEqual(((high - low) / 2 * 100).quantize(Decimal("0.1")), Decimal("14.8"))  # 룰북 B4: 약 ±14.8pp
        low, high = c4.wilson(10, 20)
        self.assertEqual(((high - low) / 2 * 100).quantize(Decimal("1")), Decimal("20"))  # 약 ±20pp

    def test_wilson_matches_independent_formula(self):
        for x, n in ((0, 40), (1, 40), (13, 40), (40, 40), (7, 20), (3, 3)):
            with self.subTest(x=x, n=n):
                low, high = c4.wilson(x, n)
                want = wilson_float(x, n)
                self.assertAlmostEqual(float(low), max(0.0, want[0]), places=12)
                self.assertAlmostEqual(float(high), min(1.0, want[1]), places=12)
        self.assertIsNone(c4.wilson(0, 0))

    def test_newcombe_matches_independent_formula(self):
        for cells in ((12, 9, 2, 4), (5, 0, 0, 15), (0, 3, 7, 10), (10, 5, 5, 20), (0, 0, 0, 1)):
            with self.subTest(cells=cells):
                low, high = c4.newcombe_paired(*cells)
                want = newcombe_float(*cells)
                self.assertAlmostEqual(float(low), want[0], places=12)
                self.assertAlmostEqual(float(high), want[1], places=12)
                n = sum(cells)
                diff = Fraction(cells[1] - cells[2], n)
                self.assertLessEqual(float(low), float(diff))
                self.assertGreaterEqual(float(high), float(diff))

    def test_mcnemar_exact(self):
        self.assertEqual(c4.mcnemar_exact(0, 5), Fraction(1, 16))  # 2 × (1/32)
        self.assertEqual(c4.mcnemar_exact(1, 9), Fraction(22, 1024))
        self.assertEqual(c4.mcnemar_exact(2, 2), Fraction(1))
        self.assertEqual(c4.mcnemar_exact(0, 0), Fraction(1))
        self.assertEqual(c4.fmt_p(c4.mcnemar_exact(1, 9)), "0.021")
        self.assertEqual(c4.fmt_p(c4.mcnemar_exact(0, 20)), "<0.001")

    def test_median_and_format(self):
        self.assertEqual(c4.median([4, 1, 3, 2]), Fraction(5, 2))
        self.assertEqual(c4.fmt_stats([1, 2, 6]), "3/2/6")
        self.assertEqual(c4.fmt_rate(7, 20), "7/20 = 35.0% (18.1%~56.7%)")
        self.assertEqual(c4.fmt_interval((Decimal("-0.2"), Decimal("0.05"))), "-20.0pp~+5.0pp")


def oracle_summary_input(dataset: str = "dev20", modes: tuple = ("checklist", "agent", "full")) -> dict:
    """oracle A/B/C를 합성 개발 묶음처럼 돌린 결과(시험용)."""
    oracle = fx.load_oracle()
    rows, ids = fx.oracle_snapshot(oracle)
    snap = c1.Snapshot.from_json(rows.doc())
    from eval.scorer import prose as c2
    from eval.scorer import results as c3
    cases = [{"case_id": c, "hs6": "850450", "partner": p, "month": "202401"} for c, p in fx.ORACLE_PARTNERS.items()]
    batch, reports, records = [], {}, []
    stamp = 260925100001
    for mode in modes:
        for case_id, report in fx.oracle_reports(rows, ids, mode=mode, stamp=str(stamp)).items():
            stamp_used = int(report["run_id"].rsplit("-", 1)[1])
            status = "COMPLETED"
            if mode == "agent" and case_id == "B-residual":
                status = "FAILED"
            if mode == "checklist" and case_id == "A-composition":
                report["review_status"] = "HOLD"
            line = fx.batch_line(report["run_id"], case_id, mode=mode, status=status, review=report["review_status"])
            batch.append(line)
            if status == "COMPLETED":
                reports[report["run_id"]] = report
                records += c1.score_report_claims(report, snap, report["run_id"], rows.snapshot_id,
                                                  fx.oracle_context(case_id))
                records += c2.score_report_prose(report, report["run_id"], snap.hs_codes, [])
            stamp = max(stamp, stamp_used) + 1
    results = c3.run({"batch": batch, "reports": reports, "claims": records, "answers": oracle, "cases": cases,
                      "snapshot": rows.doc()})
    stats = {run_id: {"extremes": 0, "hangul": 10, "latin": 0, "forbidden": 0, "missing": 0,
                      "report_sha256": "ab" * 32} for run_id in reports}
    return {"dataset": dataset, "batch_run": "evaluate-260925100000", "batch_dir": "outputs/evaluate-260925100000",
            "scoring_run": "score-260925110000", "planned": {"cases": cases, "modes": list(modes)}, "results": results,
            "claims": records, "answers": oracle, "report_stats": stats, "reports_unread": [],
            "conditions": {"dataset": dataset, "scorer_commit": "1234567", "concurrency": 1, "order_seed": "7"},
            "meta": {"schema_version": 1, "prose_patterns_sha256": "cd" * 32,
                     "snapshot_file": "data/snapshots/controlled_fixture_v0/snapshot_build.sqlite",
                     "snapshot_file_sha256": "ef" * 32}}


class AuxiliaryMetricsTest(unittest.TestCase):
    def setUp(self):
        self.inp = oracle_summary_input()
        from eval.scorer import results as c3
        self.answers = c3.read_answer_table(self.inp["answers"])
        self.plan = c4.Plan(self.inp["planned"]["cases"], self.inp["planned"]["modes"], self.inp["results"])

    def test_processing_accuracy_and_failures(self):
        stats = {m: c4.auxiliary(self.plan, self.answers, m) for m in self.plan.modes}
        self.assertEqual({m: sum(s["success"].values()) for m, s in stats.items()},
                         {"checklist": 2, "agent": 2, "full": 3})
        self.assertEqual(stats["agent"]["statuses"]["FAILED"], 1)
        self.assertEqual(stats["checklist"]["unnecessary_hold"], (1, 2))  # A(MONITOR 기대)를 HOLD로 끝냈다
        self.assertEqual(stats["full"]["wrong_monitor"], (0, 2))
        self.assertEqual(stats["agent"]["confusion"]["MAINTAIN"]["실행 실패"], 1)
        self.assertEqual(c4.all_hold_score(self.plan, self.answers), 1)  # C만 HOLD 기대

    def test_unrun_counts_as_failure(self):
        results = [r for r in self.inp["results"] if not (r["mode"] == "full" and r["case_id"] == "C-missing-hs10")]
        plan = c4.Plan(self.inp["planned"]["cases"], self.inp["planned"]["modes"], results)
        stats = c4.auxiliary(plan, self.answers, "full")
        self.assertEqual((stats["unrun"], sum(stats["success"].values())), (1, 2))
        self.assertEqual(stats["confusion"]["HOLD"]["실행 실패"], 1)

    def test_rerun_uses_latest_row(self):
        failed = dict(self.inp["results"][0], run_id="run_case-260925090000", execution_status="FAILED",
                      review_status_final=None, signal_status=None)
        plan = c4.Plan(self.inp["planned"]["cases"], self.inp["planned"]["modes"], self.inp["results"] + [failed])
        self.assertEqual(plan.final("A-composition", "checklist")["run_id"], self.inp["results"][0]["run_id"])
        self.assertEqual(plan.first("A-composition", "checklist")["run_id"], "run_case-260925090000")
        self.assertEqual(plan.reruns("checklist"), 1)

    def test_render_dev20(self):
        text = c4.run(self.inp)
        for fragment in ("# 평가 결과 요약 — evaluate-260925100000", "## 0. 실행 조건", "## 1. 대표 지표",
                         "## 2. 보조 지표 — holdout40 (등급 C)", "## 3. 개발 묶음 값 — 대표 숫자 아님 (등급 D)",
                         "| full | 3/3 = 100.0% (43.8%~100.0%)", "등급 D", "모든 사례를 보류했을 때의 점수: 1/3",
                         "## 4. 참고 지표", "## 5. 재현 명령", "## 6. 한계", "채점기 커밋 1234567",
                         "python -m eval.scorer --run outputs/evaluate-260925100000", MISSING_MARK):
            self.assertIn(fragment, text)
        self.assertNotIn("\t", text)


MISSING_MARK = c4.MISSING


class RepresentativeMetricsTest(unittest.TestCase):
    def real_input(self, dataset: str) -> dict:
        rows, ids = fx.rulebook_snapshot()
        snap = c1.Snapshot.from_json(rows.doc())
        cases = [{"case_id": f"case-{p}", "hs6": "850450", "partner": p, "month": "202401"} for p in ("CN", "JP")]
        good = fx.claim("k", "value", "U", Decimal("20.34"), "USD/kg", "NA", [rows.ev(ids["cn_2401"])])
        bad = dict(good, value=Decimal("20.35"))
        batch, records = [], []
        plan = [("case-CN", "freeform", good, ""), ("case-JP", "freeform", bad, "단가가 50% 늘었다."),
                ("case-CN", "full", good, ""), ("case-JP", "full", good, "")]
        for i, (case_id, mode, claim, narrative) in enumerate(plan):
            run_id = f"run_case-2609251000{i:02d}"
            report = fx.report(run_id, [dict(claim)], narrative=narrative, case_id=case_id, mode=mode)
            batch.append(fx.batch_line(run_id, case_id, mode=mode, dataset=dataset, review="MAINTAIN",
                                       snapshot_id="kcs_202201_202412_v2"))
            records += c1.score_report_claims(report, snap, run_id, rows.snapshot_id)
            from eval.scorer import prose as c2
            records += c2.score_report_prose(report, run_id, snap.hs_codes, [])
        from eval.scorer import results as c3
        results = c3.run({"batch": batch, "reports": {}, "claims": records, "answers": None, "cases": cases,
                          "snapshot": rows.doc()})
        return {"dataset": dataset, "batch_run": "evaluate-260925100000", "batch_dir": "outputs/evaluate-260925100000",
                "scoring_run": "score-260925110000", "planned": {"cases": cases, "modes": ["freeform", "full"]},
                "results": results, "claims": records, "answers": None, "report_stats": {}, "reports_unread": [],
                "conditions": {"a_grade": {"rb1_frozen": True, "hash_recheck_match": True,
                                           "scorer_prevalidation": True, "scored_once": True}},
                "meta": {"schema_version": 1}}

    def test_report_level_errors(self):
        inp = self.real_input("real_dev")
        plan = c4.Plan(inp["planned"]["cases"], inp["planned"]["modes"], inp["results"])
        index = c4.ClaimIndex(inp["claims"])
        free = c4.representative(plan, index, set(), "freeform")
        full = c4.representative(plan, index, set(), "full")
        self.assertEqual((free["report_errors"], full["report_errors"]), (1, 0))
        self.assertEqual((free["claim_errors"], free["claims"]), (1, 2))
        self.assertEqual(free["digits_only"], 1)  # 20.35 대 20.3411…: 차가 0.01 미만
        self.assertEqual(free["unbacked_by_field"], {"narrative": 2, "hypotheses": 0, "claims[].text": 0})
        text = c4.run(inp)
        self.assertIn("real_dev freeform 대 full", text)
        self.assertIn("\"차이를 확인하지 못했다\"(차이가 없다는 뜻이 아님)", text)
        self.assertIn("둘 다 오류 0 / freeform만 오류 1 / full만 오류 0 / 둘 다 무오류 1", text)
        self.assertIn("등급 D(개발 묶음 값, 대표 숫자 아님)", text)
        self.assertIn("real_dev 경보 목록(분모): case-CN(850450·CN·202401), case-JP(850450·JP·202401)", text)

    def test_real_sealed_a_grade_is_withheld_below_twenty_reports(self):
        text = c4.run(self.real_input("real_sealed"))
        self.assertIn("A등급 주장 조건(B3-3): 미충족(조건 5)", text)
        self.assertIn("A등급 주장 보류(참고치)", text)
        self.assertIn("금지 해제 조건 뒤 결과표(로드맵 R1)에 적음", text)
        self.assertIn("서로 다른 시계열 2개", text)


class UntrustedSummaryValueTest(unittest.TestCase):
    """실행 쪽 값(믿지 않는 입력)이 요약 마크다운에 가짜 제목·표 행을 만들지 못한다(보안 검토 1회차 권고 3)."""

    def test_version_values_and_case_ids_are_escaped(self):
        inp = oracle_summary_input()
        for result in inp["results"]:
            result["policy_version"] = "dev-0.1\n# 가짜 제목 | 가짜 칸"
        text = c4.run(inp)
        self.assertNotIn("\n# 가짜 제목", text)
        self.assertIn("dev-0.1 # 가짜 제목 ／ 가짜 칸", text)

    def test_unread_reports_show_reasons(self):
        inp = oracle_summary_input()
        run_id = inp["results"][0]["run_id"]
        inp["reports_unread"] = [run_id]
        inp["report_stats"][run_id] = {"unreadable": "크기 상한 초과"}
        text = c4.run(inp)
        self.assertIn(f"보고서를 읽지 못한 COMPLETED 실행 1건(보고서 단위 실패로 셌다): {run_id}(사유: 크기 상한 초과 1건)",
                      text)


if __name__ == "__main__":
    unittest.main()
