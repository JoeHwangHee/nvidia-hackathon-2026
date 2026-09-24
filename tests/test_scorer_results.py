"""독립 채점기 단위 C3(채점 결과 기록) 시험: 하네스 줄 검증, 정답표 읽기(eval/dev/oracle_ABC.json 기준),
세 채점 키(required_evidence_ok·numeric_ok·provenance_ok)."""
import copy
import unittest
from decimal import Decimal

import scorer_fixtures as fx
from eval.scorer import claims as c1
from eval.scorer import prose as c2
from eval.scorer import results as c3


def scored(rows: fx.Rows, report: dict) -> list[dict]:
    snap = c1.Snapshot.from_json(rows.doc())
    return c1.score_report_claims(report, snap, report["run_id"], rows.snapshot_id) \
        + c2.score_report_prose(report, report["run_id"], snap.hs_codes, [])


class AnswerTableTest(unittest.TestCase):
    def test_oracle_is_read(self):
        table = c3.read_answer_table(fx.load_oracle())
        self.assertEqual({k: (v["review_status"], v["signal_status"]["unit_value"], v["signal_status"]["share"],
                              v["unresolved_evidence"]) for k, v in table.items()},
                         {"A-composition": ("MONITOR", "MONITOR", "NOT_TRIGGERED", False),
                          "B-residual": ("MAINTAIN", "MAINTAIN", "NOT_TRIGGERED", False),
                          "C-missing-hs10": ("HOLD", "HOLD", "NOT_TRIGGERED", False)})
        self.assertEqual(table["C-missing-hs10"]["required_evidence"],
                         ["missingness_listed", "failure_vs_not_collected_distinguished", "no_zero_fill"])

    def test_rejections(self):
        oracle = fx.load_oracle()

        def broken(change) -> dict:
            doc = copy.deepcopy(oracle)
            change(doc["cases"][0]["expected"])
            return doc

        cases = {
            "unknown tag": broken(lambda e: e["required_evidence"].append("new_tag")),
            "two triggers without signal_status": broken(lambda e: e["signals"].update(share="TRIGGERED")),
            "status label": broken(lambda e: e.update(review_status="정상")),
            "aggregation": broken(lambda e: e.update(signal_status={"unit_value": "HOLD", "share": "NOT_TRIGGERED"})),
            "no trigger": broken(lambda e: e["signals"].update(unit_value="NOT_TRIGGERED")),
        }
        for name, doc in cases.items():
            with self.subTest(case=name), self.assertRaises(c1.ScorerInputError):
                c3.read_answer_table(doc)
        dup = copy.deepcopy(oracle)
        dup["cases"].append(copy.deepcopy(dup["cases"][0]))
        with self.assertRaises(c1.ScorerInputError):
            c3.read_answer_table(dup)

    def test_two_signal_case_with_explicit_status(self):
        doc = {"cases": [{"case_id": "x", "expected": {
            "signals": {"unit_value": "TRIGGERED", "share": "TRIGGERED"}, "review_status": "MAINTAIN",
            "signal_status": {"unit_value": "MAINTAIN", "share": "HOLD"}, "required_evidence": []}}]}
        self.assertTrue(c3.read_answer_table(doc)["x"]["unresolved_evidence"])  # MAINTAIN과 HOLD가 섞였다

    def test_aggregate_status(self):
        self.assertEqual(c3.aggregate_status({"unit_value": "HOLD", "share": "MONITOR"}), ("HOLD", False))
        self.assertEqual(c3.aggregate_status({"unit_value": "MONITOR", "share": "NOT_TRIGGERED"}), ("MONITOR", False))
        self.assertEqual(c3.aggregate_status({"unit_value": "HOLD", "share": "MAINTAIN"}), ("MAINTAIN", True))


class BatchLineTest(unittest.TestCase):
    def test_good_lines(self):
        c3.validate_batch_line(fx.batch_line("run_case-260925100001", "A"), 0)
        c3.validate_batch_line(fx.batch_line("run_case-260925100001", "A", status="TIMEOUT"), 0)

    def test_bad_lines(self):
        good = fx.batch_line("run_case-260925100001", "A")
        cases = {
            "missing key": {k: v for k, v in good.items() if k != "errors"},
            "extra key": dict(good, note="x"),
            "run_id": dict(good, run_id="../run_case-260925100001"),
            "completed without review": dict(good, review_status_final=None),
            "failed with review": dict(good, execution_status="FAILED"),
            "bool count": dict(good, tool_attempts=True),
            "mode": dict(good, mode="critic"),
            "signal keys": dict(good, signal_status={"unit_value": "MONITOR"}),
        }
        for name, line in cases.items():
            with self.subTest(case=name), self.assertRaises(c1.ScorerInputError):
                c3.validate_batch_line(line, 0)


class ScorerKeysTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.ids = fx.oracle_snapshot(fx.load_oracle())
        cls.snap = c1.Snapshot.from_json(cls.rows.doc())
        cls.answers = c3.read_answer_table(fx.load_oracle())
        cls.reports = fx.oracle_reports(cls.rows, cls.ids)
        cls.contexts = {case: {"case_id": case, "hs6": "850450", "partner": p, "month": "202401"}
                        for case, p in fx.ORACLE_PARTNERS.items()}

    def line_for(self, report: dict, **extra) -> dict:
        return fx.batch_line(report["run_id"], report["case_id"], review=report["review_status"], **extra)

    def result(self, report: dict | None, case_id: str, line: dict | None = None) -> dict:
        records = scored(self.rows, report) if report is not None else []
        line = line or self.line_for(report)
        return c3.result_line(line, report, records, self.answers[case_id], self.contexts[case_id], self.snap)

    def test_good_reports_satisfy_every_key(self):
        for case_id, report in self.reports.items():
            with self.subTest(case=case_id):
                records = scored(self.rows, report)
                self.assertTrue(all(r["outcome"] == c1.CORRECT for r in records),
                                [(r["claim_id"], r["outcome"], r["note"]) for r in records if r["outcome"] != c1.CORRECT])
                out = self.result(report, case_id)
                self.assertEqual(tuple(out), c3.RESULT_KEYS)
                self.assertEqual((out["required_evidence_ok"], out["numeric_ok"], out["provenance_ok"]),
                                 (True, True, True))

    def test_missing_tags(self):
        a = copy.deepcopy(self.reports["A-composition"])
        a["claims"] = [c for c in a["claims"] if not c["metric"].startswith("r_U@")]
        records = scored(self.rows, a)
        ok, missing = c3.required_evidence_ok(self.answers["A-composition"]["required_evidence"], a, records,
                                              self.contexts["A-composition"], self.snap, "controlled_fixture_v0")
        self.assertEqual((ok, missing), (False, ["per_child_unit_value_stable"]))
        a["evidence_ids"] = a["evidence_ids"][:2]
        for claim in a["claims"]:
            claim["evidence_ids"] = claim["evidence_ids"][:2]
        records = scored(self.rows, a)
        missing = c3.required_evidence_ok(self.answers["A-composition"]["required_evidence"], a, records,
                                          self.contexts["A-composition"], self.snap, "controlled_fixture_v0")[1]
        self.assertIn("parent_child_match_V_and_Q", missing)
        self.assertIn("weight_share_decomposition", missing)  # 하위 행을 인용하지 않아 분해 claim이 유효하지 않다

    def test_zero_fill_and_wrong_status(self):
        c = copy.deepcopy(self.reports["C-missing-hs10"])
        c["claims"].append(fx.claim("c3", "decomposition", "mix_effect", Decimal("-2.40"), "USD/kg", "DOWN",
                                    c["claims"][0]["evidence_ids"], partner="DE", baseline="202301"))
        out = self.result(c, "C-missing-hs10")
        self.assertEqual((out["required_evidence_ok"], out["numeric_ok"], out["provenance_ok"]), (False, False, True))
        c = copy.deepcopy(self.reports["C-missing-hs10"])
        c["claims"][1]["value"] = "NOT_COLLECTED"
        records = scored(self.rows, c)
        missing = c3.required_evidence_ok(self.answers["C-missing-hs10"]["required_evidence"], c, records,
                                          self.contexts["C-missing-hs10"], self.snap, "controlled_fixture_v0")[1]
        self.assertEqual(missing, ["missingness_listed", "failure_vs_not_collected_distinguished"])

    def test_unbacked_prose_and_version_mismatch(self):
        a = copy.deepcopy(self.reports["A-composition"])
        a["narrative"] += " 점유율은 50% 늘었다."
        out = self.result(a, "A-composition")
        self.assertEqual((out["numeric_ok"], out["provenance_ok"]), (False, True))
        a = copy.deepcopy(self.reports["A-composition"])
        a["grouping_version"] = "g1"
        self.assertFalse(self.result(a, "A-composition")["provenance_ok"])

    def test_failed_run_and_runtime_values(self):
        report = self.reports["A-composition"]
        line = self.line_for(report, status="FAILED", required_evidence_ok=True, numeric_ok=True, provenance_ok=True)
        out = self.result(None, "A-composition", line)
        self.assertEqual((out["required_evidence_ok"], out["numeric_ok"], out["provenance_ok"]), (False, False, False))

    def test_real_dataset_has_null_required_evidence(self):
        report = self.reports["A-composition"]
        line = self.line_for(report, dataset="real_dev")
        out = c3.result_line(line, report, scored(self.rows, report), None, None, self.snap)
        self.assertEqual((out["required_evidence_ok"], out["numeric_ok"]), (None, True))

    def test_run_keeps_batch_order(self):
        reports = list(self.reports.values())
        batch = [self.line_for(r) for r in reversed(reports)]
        records = [r for report in reports for r in scored(self.rows, report)]
        out = c3.run({"batch": batch, "reports": {r["run_id"]: r for r in reports}, "claims": records,
                      "answers": fx.load_oracle(), "cases": list(self.contexts.values()), "snapshot": self.rows.doc()})
        self.assertEqual([o["run_id"] for o in out], [b["run_id"] for b in batch])
        self.assertTrue(all(o["required_evidence_ok"] for o in out))


if __name__ == "__main__":
    unittest.main()
