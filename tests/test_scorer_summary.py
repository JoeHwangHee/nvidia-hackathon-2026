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
            "meta": {"schema_version": 2, "prose_patterns_sha256": "cd" * 32,
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

    def test_denominator_keeps_unrun_failed_and_unread_runs(self):
        # 계획 4건(full): 줄 없음·TIMEOUT·COMPLETED인데 보고서를 읽지 못함·정상 → 보고서 단위 오류 3/4, 처리 성공 1/4
        cases = self.inp["planned"]["cases"] + [dict(self.inp["planned"]["cases"][2], case_id="D-unrun")]
        answers = dict(self.answers, **{"D-unrun": self.answers["C-missing-hs10"]})
        full = {r["case_id"]: r for r in self.inp["results"] if r["mode"] == "full"}
        timeout = dict(full["A-composition"], execution_status="TIMEOUT", review_status_final=None, signal_status=None)
        from eval.scorer import results as c3
        unread_line = c3.result_line(full["B-residual"], None, [], self.answers["B-residual"], None, None)  # 보고서 없음
        results = [timeout, dict(full["B-residual"], **{k: unread_line[k] for k in
                                                        ("required_evidence_ok", "numeric_ok", "provenance_ok")}),
                   full["C-missing-hs10"]]
        plan = c4.Plan(cases, ["full"], results)
        unread = {full["B-residual"]["run_id"]}
        rep = c4.representative(plan, c4.ClaimIndex(self.inp["claims"]), unread, "full")
        self.assertEqual((rep["planned"], rep["report_errors"], rep["unrun"], rep["valid"]), (4, 3, 1, 1))
        self.assertEqual(rep["errors_by_case"], {"A-composition": True, "B-residual": True, "C-missing-hs10": False,
                                                 "D-unrun": True})
        self.assertEqual([c4.processed(plan.final(c, "full"), answers[c]) for c in plan.cases],
                         [False, False, True, False])  # 처리 성공 1/4
        stats = c4.auxiliary(plan, answers, "full")
        self.assertEqual((stats["unrun"], stats["statuses"]["TIMEOUT"]), (1, 1))

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
                "meta": {"schema_version": 2}}

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


def trace_event(seq: int, run_id: str, phase: str, stage: str = "basic", **data) -> dict:
    """런타임(단위 I12·L1)이 남기는 state_change 사건 모양(tests/units/I12/, 실제 실행 trace로 확인)."""
    return {"seq": seq, "ts": "2026-09-26T03:00:00+09:00", "run_id": run_id, "event": "state_change", "stage": stage,
            "data": {"phase": phase, "review_status": "HOLD", "signal_status": {"unit_value": "HOLD", "share": "NOT_TRIGGERED"},
                     **data}}


def evidence_claims_event(seq: int, run_id: str, stage: str, added: list[tuple[str, list[str]]]) -> dict:
    return trace_event(seq, run_id, "evidence_claims", stage, required={"unit_value": ["comparability_ok"]}, unmet=[],
                       no_action=[], added=[{"signal": "unit_value", "code": code,
                                            "claims": [{"claim_type": "value", "metric_id": f"m-{i}", "claim_id": i}
                                                       for i in ids]} for code, ids in added])


class TraceAggregationTest(unittest.TestCase):
    """룰북 B7 공개 값(실행 추적 집계): 골든 trace 조각으로 ①~⑥이 기대값과 같은지 본다. 픽스처는 덧붙인 주장이 있는 보고서
    1건, review_status 집계 변경 1건, (나) 수정본 버림 1건, trace 없는 실행 1건이다."""

    def setUp(self):
        self.rows, self.ids = fx.rulebook_snapshot()
        self.snap = c1.Snapshot.from_json(self.rows.doc())
        self.thresholds = [Fraction(30), Fraction(10)]
        self.cases = [{"case_id": f"case-{i}", "hs6": "850450", "partner": "CN", "month": "202401"} for i in range(1, 5)]
        from eval.scorer import prose as c2
        from eval.scorer import results as c3
        good = fx.claim("k", "value", "U", Decimal("20.34"), "USD/kg", "NA", [self.rows.ev(self.ids["cn_2401"])])
        attached = dict(good, claim_id="e1")  # 코드가 덧붙인 주장(trace가 가른다)과 같은 값의 산문
        self.run_ids = [f"run_case-2609260300{i:02d}" for i in range(1, 5)]
        specs = [  # (claims, narrative): 사례 1 덧붙인 주장이 산문을 뒷받침, 2 모델 주장이 뒷받침, 3 산문 없음, 4 trace 없음
            ([attached], "단가는 20.34 USD/kg다."), ([good], "단가는 20.34 USD/kg다."), ([good], ""), ([good], "")]
        self.batch, self.records, self.reports = [], [], {}
        for run_id, case, (claims, narrative) in zip(self.run_ids, self.cases, specs):
            report = fx.report(run_id, [dict(c) for c in claims], narrative=narrative, case_id=case["case_id"], mode="full")
            self.reports[run_id] = report
            self.batch.append(fx.batch_line(run_id, case["case_id"], mode="full", dataset="real_dev", review="HOLD",
                                            snapshot_id="kcs_202201_202412_v2"))
            self.records += c1.score_report_claims(report, self.snap, run_id, self.rows.snapshot_id)
            self.records += c2.score_report_prose(report, run_id, self.snap.hs_codes, self.thresholds)
        self.results = c3.run({"batch": self.batch, "reports": {}, "claims": self.records, "answers": None,
                               "cases": self.cases, "snapshot": self.rows.doc()})
        r1, r2, r3, _ = self.run_ids
        self.traces = {
            r1: [trace_event(1, r1, "draft"), evidence_claims_event(2, r1, "basic", [("comparability_ok", ["e9"])]),
                 evidence_claims_event(3, r1, "final", [("comparability_ok", ["e1"]), ("signal_claim", ["e7"])]),
                 trace_event(4, r1, "final", "final")],
            r2: [trace_event(1, r2, "status_aggregated", "basic", model_review_status="MONITOR", model_unresolved_evidence=None,
                             unresolved_evidence=False),
                 trace_event(2, r2, "code_finding", "basic", missing_tools=[], skipped_for_hold=["compare_partners"]),
                 trace_event(3, r2, "after_critic", "critic", needs_revision=True, findings=1, requery=0, problems=[],
                             requery_dropped=[{"tool": "decompose_hs", "args": {}, "reason": "signal_not_triggered",
                                               "signals": ["unit_value"]}]),
                 trace_event(4, r2, "status_aggregated", "final", model_review_status="MONITOR", model_unresolved_evidence=None,
                             unresolved_evidence=False)],
            r3: [trace_event(1, r3, "revision_discarded", "final", blocked_by="validator", would_be_cause="VALIDATOR_BLOCKED",
                             kept_report_id="report1")],
        }

    def trace_stats(self, runs: list[str] | None = None) -> dict:
        """eval/scorer/__main__.py trace_entry와 같은 계산(파일 읽기만 뺀 것)."""
        from eval.scorer import prose as c2
        out = {}
        for run_id in (runs if runs is not None else self.run_ids):
            events = self.traces.get(run_id)
            if events is None:
                out[run_id] = {"available": False, "reason": c4.TRACE_NONE}
                continue
            report = self.reports[run_id]
            facts = c4.trace_facts(events, report, True)
            before = c4.without_attached(report, facts["attached_ids"])
            mine = c1.score_report_claims(before, self.snap, run_id, self.rows.snapshot_id)
            mine += c2.score_report_prose(before, run_id, self.snap.hs_codes, self.thresholds)
            entry = {"available": True, **{k: v for k, v in facts.items() if k != "attached_ids"}}
            entry.update(c4.before_after(mine, [r for r in self.records if r["run_id"] == run_id]))
            out[run_id] = entry
        return out

    def test_parse_trace_rejects_untrusted_shapes(self):
        r1 = self.run_ids[0]
        text = "\n".join(c1.dumps_json(e) for e in self.traces[r1]) + "\n"
        self.assertEqual(len(c4.parse_trace(text, r1)), 4)
        self.assertIsNone(c4.parse_trace(text, self.run_ids[1]))  # run_id 불일치
        self.assertIsNone(c4.parse_trace(text + "{not json}\n", r1))
        self.assertIsNone(c4.parse_trace('[1, 2]\n', r1))  # 객체가 아니다
        self.assertIsNone(c4.parse_trace('{"data": {}}\n', r1))  # event 없음
        self.assertIsNone(c4.parse_trace("\n\n", r1))

    def test_trace_shape_check_follows_golden_field_names(self):
        r1 = self.run_ids[0]
        self.assertTrue(c4.trace_shape_ok(self.traces[r1]))
        self.assertTrue(c4.trace_shape_ok(self.traces[self.run_ids[1]]))
        self.assertTrue(c4.trace_shape_ok([trace_event(1, r1, "after_critic", "critic", needs_revision=False)]))  # requery_dropped 없어도 된다
        bad = [
            [{k: v for k, v in trace_event(1, r1, "draft").items() if k != "stage"}],  # stage 없음
            [dict(trace_event(1, r1, "draft"), data=[])],  # data가 객체 아님
            [dict(trace_event(1, r1, "draft"), data={"review_status": "HOLD"})],  # phase 없음
            [trace_event(1, r1, "evidence_claims", added={"code": "x"})],  # added가 목록 아님
            [trace_event(1, r1, "evidence_claims", added=[{"code": 1, "claims": []}])],  # code가 문자열 아님
            [trace_event(1, r1, "evidence_claims", added=[{"code": "comparability_ok", "claims": [{"metric_id": "m"}]}])],  # claim_id 없음
            [trace_event(1, r1, "code_finding", skipped_for_hold="compare_partners")],
            [trace_event(1, r1, "after_critic", "critic", requery_dropped={})],
        ]
        for events in bad:
            with self.subTest(events=events):
                self.assertFalse(c4.trace_shape_ok(events))
        self.assertTrue(c4.trace_shape_ok([{"event": "tool_call", "stage": "basic", "data": 3}]))  # state_change가 아닌 사건은 보지 않는다

    def test_not_aggregated_text_names_each_reason(self):
        self.assertEqual(c4.not_aggregated_text({c4.TRACE_NONE: 1}, 1, 4), "집계하지 않음(trace 없음 1/4건)")
        self.assertEqual(c4.not_aggregated_text({c4.TRACE_MALFORMED: 2}, 2, 4), "집계하지 않음(trace 모양 다름 2/4건)")
        self.assertEqual(c4.not_aggregated_text({c4.TRACE_MALFORMED: 1, c4.TRACE_NONE: 1, c4.TRACE_UNREADABLE: 1}, 3, 4),
                         "집계하지 않음(trace 없음 1·trace를 읽을 수 없음 1·trace 모양 다름 1, 3/4건)")
        self.assertEqual(c4.not_aggregated_text({}, 0, 0), "집계하지 않음(trace 없음 0/0건)")
        plan = c4.Plan(self.cases, ["full"], self.results)
        stats = self.trace_stats(self.run_ids[:2])
        stats[self.run_ids[2]] = {"available": False, "reason": c4.TRACE_MALFORMED}
        text = c4.trace_mode_stats(plan, c4.ClaimIndex(self.records), set(), stats, "full")["not_aggregated"]
        self.assertEqual(text, "집계하지 않음(trace 없음 1·trace 모양 다름 1, 2/4건)")

    def test_attached_claims_come_from_the_last_evidence_claims_event(self):
        r1 = self.run_ids[0]
        self.assertEqual(c4.attached_claim_ids(self.traces[r1]), {"e1": c4.REQUIRED_EVIDENCE, "e7": c4.SIGNAL_CLAIM})
        facts = c4.trace_facts(self.traces[r1], self.reports[r1], True)
        self.assertEqual(facts["attached_ids"], {"e1"})  # e7은 trace에만 있고 최종 보고서에 없다
        self.assertEqual((facts["attached_count"], facts["attached_missing_in_report"]), (1, 1))
        self.assertEqual(facts["attached_by_code"], {c4.REQUIRED_EVIDENCE: 1, c4.SIGNAL_CLAIM: 0, c4.ZERO_WEIGHT_CLAIM: 0})
        self.assertEqual(c4.without_attached(self.reports[r1], {"e1"})["claims"], [])
        self.assertEqual(c4.trace_facts(self.traces[r1], None, True)["attached_count"], None)  # 보고서 없음
        zero = c4.attached_claim_ids([evidence_claims_event(1, r1, "basic", [("zero_weight_claim", ["e2"])])])
        self.assertEqual(zero, {"e2": c4.ZERO_WEIGHT_CLAIM})
        self.assertEqual(c4.attached_claim_ids([trace_event(1, r1, "draft")]), {})

    def test_status_aggregation_discards_and_hold_skips(self):
        r2, r3 = self.run_ids[1], self.run_ids[2]
        facts = c4.trace_facts(self.traces[r2], self.reports[r2], True)
        self.assertEqual((facts["status_aggregated_final"], facts["status_aggregated_any"]), (True, True))
        self.assertEqual((facts["requery_dropped"], facts["hold_skipped_findings"], facts["revision_discarded"]), (1, 1, 0))
        self.assertFalse(c4.trace_facts(self.traces[r2], self.reports[r2], False)["status_aggregated_final"])  # 실패 실행
        self.assertTrue(c4.trace_facts(self.traces[r2][:1], None, True)["status_aggregated_any"])  # basic 단계만
        self.assertFalse(c4.trace_facts(self.traces[r2][:1], None, True)["status_aggregated_final"])
        self.assertEqual(c4.trace_facts(self.traces[r3], self.reports[r3], True)["revision_discarded"], 1)

    def test_mode_stats_match_expected_values(self):
        plan = c4.Plan(self.cases, ["full"], self.results)
        index = c4.ClaimIndex(self.records)
        stats = self.trace_stats(self.run_ids[:3])  # 사례 4는 trace 없음
        partial = c4.trace_mode_stats(plan, index, set(), stats, "full")
        self.assertEqual(partial["not_aggregated"], "집계하지 않음(trace 없음 1/4건)")
        self.traces[self.run_ids[3]] = [trace_event(1, self.run_ids[3], "draft")]
        full = c4.trace_mode_stats(plan, index, set(), self.trace_stats(), "full")
        self.assertIsNone(full["not_aggregated"])
        self.assertEqual((full["errors_before"], full["errors_after"]), (1, 0))  # 사례 1의 산문이 덧붙인 주장 없이는 뒷받침되지 않는다
        self.assertEqual(full["backed_by_attached"], 1)
        self.assertEqual((full["attached_total"], full["attached_per_report"]), (1, [1, 0, 0, 0]))
        self.assertEqual(full["attached_by_code"], {c4.REQUIRED_EVIDENCE: 1, c4.SIGNAL_CLAIM: 0, c4.ZERO_WEIGHT_CLAIM: 0})
        self.assertEqual((full["status_aggregated_final"], full["status_aggregated_any"]), (1, 1))
        self.assertEqual((full["revision_discarded"], full["requery_dropped"], full["hold_skipped_findings"]), (1, 1, 1))
        self.assertEqual(full["attached_missing_in_report"], 1)

    def test_failed_unread_and_unrun_rows_stay_errors_before_and_after(self):
        failed = dict(self.results[2], execution_status="FAILED", review_status_final=None, signal_status=None)
        results = [self.results[0], self.results[1], failed]  # 사례 4는 미실행
        plan = c4.Plan(self.cases, ["full"], results)
        stats = self.trace_stats(self.run_ids[:3])
        stats[self.run_ids[2]] = {"available": True, **{k: v for k, v in
                                                        c4.trace_facts(self.traces[self.run_ids[2]], None, False).items()
                                                        if k != "attached_ids"}}
        full = c4.trace_mode_stats(plan, c4.ClaimIndex(self.records), {self.run_ids[1]}, stats, "full")
        self.assertIsNone(full["not_aggregated"])  # 미실행 사례는 최종 행이 없어 trace 대상이 아니다
        self.assertEqual((full["errors_before"], full["errors_after"]), (4, 3))  # 읽지 못한 보고서·실패·미실행은 전·뒤 모두 오류
        self.assertEqual(full["attached_per_report"], [1])
        stats[self.run_ids[0]]["before_error"] = None  # 덧붙이기 전 재채점이 입력 오류를 냈다
        self.assertEqual(c4.trace_mode_stats(plan, c4.ClaimIndex(self.records), {self.run_ids[1]}, stats, "full")["not_aggregated"],
                         "집계하지 않음(덧붙이기 전 재채점 불가 1건)")

    def render(self, trace_stats: dict | None) -> str:
        inp = {"dataset": "real_dev", "batch_run": "evaluate-260926030000", "batch_dir": "outputs/evaluate-260926030000",
               "scoring_run": "score-260926040000", "planned": {"cases": self.cases, "modes": ["freeform", "full"]},
               "results": self.results, "claims": self.records, "answers": None, "report_stats": {}, "reports_unread": [],
               "conditions": {}, "meta": {"schema_version": 2}}
        if trace_stats is not None:
            inp["trace_stats"] = trace_stats
        return c4.run(inp)

    def test_summary_lines_follow_rulebook_b7(self):
        self.traces[self.run_ids[3]] = [trace_event(1, self.run_ids[3], "draft")]
        text = self.render(self.trace_stats())
        for fragment in (
                "- 덧붙이기 전·뒤 보고서 단위 오류율(덧붙인 주장을 뺀 주장 집합으로 산문 뒷받침을 다시 판정. 실패·무효·미실행은 그대로 오류. "
                "결정 기록 20260925-1856): freeform 집계하지 않음(trace 없음 0/0건), full 전 1/4 → 뒤 0/4",
                "- 덧붙인 주장 덕분에 뒷받침된 산문 표현 수: freeform 집계하지 않음(trace 없음 0/0건), full 1",
                "코드가 덧붙인 주장(최종 보고서에 남은 것) freeform 집계하지 않음(trace 없음 0/0건), full 합계 1(보고서당 0(0~1))",
                "review_status 집계로 바뀐 최종 보고서(어느 단계든) freeform 집계하지 않음(trace 없음 0/0건), full 1(1)",
                "버린 초안 (나) 수정본 버림 / (가) 재조회 버림 freeform 집계하지 않음(trace 없음 0/0건), full 1 / 1",
                "HOLD 합의로 뺀 도구 지적 freeform 집계하지 않음(trace 없음 0/0건), full 1",
                "full 보고서당 0(0~1), 합계 1(필수 근거 1·자기 계열 0·중량 0 0), 완료 보고서 4건",
                "- 덧붙이기 전 기준의 보고서 단위 오류율(덧붙인 필수 근거 주장을 빼고 같은 채점 규칙으로 다시 계산. 2026-09-25(금) 18:56 사용자 "
                "결정. 괄호는 덧붙이기 뒤): freeform 집계하지 않음(trace 없음 0/0건), full 1/4 = 25.0% (4.6%~69.9%) (뒤 0/4)",
                "- 버린 초안 수(조사 흐름 수정, B2): (나) 수정본 버림 freeform 집계하지 않음(trace 없음 0/0건), full 1; (가) 재조회 버림 "
                "freeform 집계하지 않음(trace 없음 0/0건), full 1",
                "모드별 trace 있는 최종 실행 freeform 0/0건, full 4/4건",
                "- trace가 덧붙였다고 적었는데 최종 보고서에 없는 주장: full 1건"):
            self.assertIn(fragment, text)
        for run_id in self.run_ids:  # 요약의 새 줄에는 사례 식별자가 들어가지 않는다(건수·비율만)
            self.assertNotIn(run_id, "\n".join(l for l in text.splitlines() if "trace" in l or "덧붙" in l or "버린 초안" in l))
        self.assertEqual(text.count("- 덧붙이기 전·뒤 보고서 단위 오류율"), 1)  # 3절(real_dev)에 한 번

    def test_summary_without_trace_input_says_not_aggregated(self):
        text = self.render(None)
        self.assertIn("full 집계하지 않음(trace 없음 4/4건)", text)
        self.assertIn("모드별 trace 있는 최종 실행 freeform 0/0건, full 0/4건", text)
        self.assertNotIn("최종 보고서에 없는 주장", text)


class UntrustedSummaryValueTest(unittest.TestCase):
    """실행 쪽 값(믿지 않는 입력)이 요약 마크다운에 가짜 제목·표 행을 만들지 못한다(보안 검토 1회차 권고 3)."""

    def test_version_values_and_case_ids_are_escaped(self):
        inp = oracle_summary_input()
        for result in inp["results"]:
            result["policy_version"] = "dev-0.1\n# 가짜 제목 | 가짜 칸"
        text = c4.run(inp)
        self.assertNotIn("\n# 가짜 제목", text)
        self.assertIn("dev-0.1 # 가짜 제목 ／ 가짜 칸", text)

    def test_operator_conditions_reach_the_summary_verbatim(self):
        """운영자 실행 조건(tradesentry evaluate --conditions-extra가 실행 조건 입력 파일에 합친 값)을 요약 0절·4절이 그대로
        옮긴다. 채점 규칙은 보지 않고 요약 문자열만 본다."""
        inp = oracle_summary_input()
        inp["conditions"].update({
            "rulebook": {"freeze_commit": "abc1234", "changes_after_freeze": "없음"}, "grouping_reason": "g0 고정",
            "prose_patterns_commit": "def5678", "precheck": "통과: 확인 명령 6개 종료 코드 0", "skill_call_success": "5/7",
            "korean_sample_review": "표본 3건 이상 없음",
            "sandbox": {"name": "ts-scored", "policy_yaml_sha256": "dc" * 32, "live_policy_sha256": "8a" * 32,
                        "violation_tests_run": "openshell_violation_tests-260925230336"},
            "prescoring_checks": {"final_status": "참: 예정 실행 60건 가운데 줄 없는 조합 0건", "version_keys": "참: 5개 일치",
                                  "mode_case_sets": "참", "seed_concurrency": "참: 순서 seed 7", "concurrency_record": "해당 없음"}})
        text = c4.run(inp)
        for fragment in ("동결 커밋 abc1234", "동결 뒤 변경 없음", "(사유: g0 고정)", "채점기 커밋 1234567", "산문 패턴 목록 커밋 def5678",
                         f"샌드박스 이름 ts-scored, 커밋한 라이브 정책 조회 본문(정책 YAML) sha256 {'8a' * 32}, "
                         "대조한 시험표 실행 폴더 이름 openshell_violation_tests-260925230336",
                         "2 버전 키 일치 참: 5개 일치", "5 모드별 사례 집합 일치 참(", "근거 결정 기록 해당 없음",
                         "- 사전 점검 결과 통과: 확인 명령 6개 종료 코드 0",
                         "스킬 호출 성공률(NemoClaw 경로, 정확도 지표에는 영향을 주지 않는다): 5/7",
                         "표본 점검: 표본 3건 이상 없음"):
            self.assertIn(fragment, text)
        for prefix in ("- 룰북:", "- policy_version", "- code_version", "- 샌드박스 이름", "- 사전 점검 결과", "- 스킬 호출 성공률"):
            [line] = [x for x in text.splitlines() if x.startswith(prefix)]
            self.assertNotIn(MISSING_MARK, line, line)  # 운영자가 준 줄에는 미기재가 남지 않는다

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
