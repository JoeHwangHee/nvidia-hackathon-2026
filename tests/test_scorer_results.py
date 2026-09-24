"""독립 채점기 단위 C3(채점 결과 기록) 시험: 하네스 줄 검증, 정답표 읽기(eval/dev/oracle_ABC.json 기준, required_evidence
필수·신호별 형식·판정 정책 P5의 코드 13개), 세 채점 키(required_evidence_ok·numeric_ok·provenance_ok)와 필수 근거 코드의
판정 조건(신호 계열별, 모두 OBSERVED인 HOLD와 비교국 누락 HOLD에서도 채울 수 있는지)."""
import copy
import unittest
from decimal import Decimal

import scorer_fixtures as fx
from eval.scorer import claims as c1
from eval.scorer import prose as c2
from eval.scorer import results as c3


def scored(rows: fx.Rows, report: dict, context: dict | None = None) -> list[dict]:
    snap = c1.Snapshot.from_json(rows.doc())
    if context is None and report["case_id"] in fx.ORACLE_PARTNERS:
        context = fx.oracle_context(report["case_id"])
    return c1.score_report_claims(report, snap, report["run_id"], rows.snapshot_id, context) \
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
                         {"unit_value": ["missingness_listed", "failure_vs_not_collected_distinguished", "no_zero_fill"]})
        self.assertEqual(len(c3.REQUIRED_EVIDENCE_TAGS), 13)  # 판정 정책 P5의 코드 13개

    def test_rejections(self):
        oracle = fx.load_oracle()

        def broken(change) -> dict:
            doc = copy.deepcopy(oracle)
            change(doc["cases"][0]["expected"])
            return doc

        cases = {
            "unknown tag": broken(lambda e: e["required_evidence"].append("new_tag")),
            "missing required_evidence": broken(lambda e: e.pop("required_evidence")),
            "null required_evidence": broken(lambda e: e.update(required_evidence=None)),
            "correction code": broken(lambda e: e["required_evidence"].append("recalculated_values")),
            "code of the other family": broken(lambda e: e["required_evidence"].append("country_and_world_change_shown")),
            "duplicate code": broken(lambda e: e["required_evidence"].append(e["required_evidence"][0])),
            "signal object with wrong keys": broken(lambda e: e.update(required_evidence={"share": []})),
            "two triggers without signal_status": broken(lambda e: e["signals"].update(share="TRIGGERED")),
            "two triggers with a list": broken(lambda e: (e["signals"].update(share="TRIGGERED"), e.update(
                signal_status={"unit_value": "MONITOR", "share": "MONITOR"}))),
            "status label": broken(lambda e: e.update(review_status="정상")),
            "status list": broken(lambda e: e.update(review_status=["모니터링"])),
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
            "signal_status": {"unit_value": "MAINTAIN", "share": "HOLD"},
            "required_evidence": {"unit_value": ["comparability_ok"], "share": []}}}]}
        table = c3.read_answer_table(doc)
        self.assertTrue(table["x"]["unresolved_evidence"])  # MAINTAIN과 HOLD가 섞였다
        self.assertEqual(table["x"]["required_evidence"], {"unit_value": ["comparability_ok"], "share": []})

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
            "run_id with newline": dict(good, run_id="run_case-260925100001\n"),
            "run_id with unicode digits": dict(good, run_id="run_case-\uff12" + "0" * 11),
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
        cls.tag_contexts = {case: fx.oracle_context(case) for case in fx.ORACLE_PARTNERS}

    def line_for(self, report: dict, **extra) -> dict:
        return fx.batch_line(report["run_id"], report["case_id"], review=report["review_status"], **extra)

    def result(self, report: dict | None, case_id: str, line: dict | None = None) -> dict:
        records = scored(self.rows, report) if report is not None else []
        line = line or self.line_for(report)
        return c3.result_line(line, report, records, self.answers[case_id],
                              c3.case_context(self.contexts[case_id], line), self.snap)

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
                                              self.tag_contexts["A-composition"], self.snap, "controlled_fixture_v0")
        self.assertEqual((ok, missing), (False, ["unit_value:per_child_unit_value_stable"]))
        a["evidence_ids"] = a["evidence_ids"][:2]
        for claim in a["claims"]:
            claim["evidence_ids"] = claim["evidence_ids"][:2]
        records = scored(self.rows, a)
        missing = c3.required_evidence_ok(self.answers["A-composition"]["required_evidence"], a, records,
                                          self.tag_contexts["A-composition"], self.snap, "controlled_fixture_v0")[1]
        self.assertIn("unit_value:parent_child_match_V_and_Q", missing)
        self.assertIn("unit_value:weight_share_decomposition", missing)  # 하위 행을 인용하지 않아 분해 claim이 유효하지 않다

    def test_zero_fill_and_wrong_status(self):
        c = copy.deepcopy(self.reports["C-missing-hs10"])
        c["claims"].append(fx.claim("c3", "decomposition", "mix_effect", Decimal("-2.40"), "USD/kg", "DOWN",
                                    c["claims"][0]["evidence_ids"], partner="DE", baseline="202301"))
        out = self.result(c, "C-missing-hs10")  # HS10 상태 행을 인용하지 않아 근거도 모자란다
        self.assertEqual((out["required_evidence_ok"], out["numeric_ok"], out["provenance_ok"]), (False, False, False))
        c = copy.deepcopy(self.reports["C-missing-hs10"])
        c["claims"][1]["value"] = "NOT_COLLECTED"
        records = scored(self.rows, c)
        missing = c3.required_evidence_ok(self.answers["C-missing-hs10"]["required_evidence"], c, records,
                                          self.tag_contexts["C-missing-hs10"], self.snap, "controlled_fixture_v0")[1]
        self.assertEqual(missing, ["unit_value:missingness_listed",
                                   "unit_value:failure_vs_not_collected_distinguished"])

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
        out = c3.result_line(line, report, scored(self.rows, report), None, c3.case_context(None, line), self.snap)
        self.assertEqual((out["required_evidence_ok"], out["numeric_ok"]), (None, True))

    def test_run_keeps_batch_order(self):
        reports = list(self.reports.values())
        batch = [self.line_for(r) for r in reversed(reports)]
        records = [r for report in reports for r in scored(self.rows, report)]
        out = c3.run({"batch": batch, "reports": {r["run_id"]: r for r in reports}, "claims": records,
                      "answers": fx.load_oracle(), "cases": list(self.contexts.values()), "snapshot": self.rows.doc()})
        self.assertEqual([o["run_id"] for o in out], [b["run_id"] for b in batch])
        self.assertTrue(all(o["required_evidence_ok"] for o in out))


class TagRuleTest(unittest.TestCase):
    """필수 근거 코드의 판정 조건(잠정): 신호 계열별 지표, 비교집합, 모두 OBSERVED인 HOLD, 비교국 누락, 0 채우기."""

    CN = {"hs6": "850450", "partner": "CN", "month": "202401", "grouping_version": "g0"}

    @classmethod
    def setUpClass(cls):
        cls.rows, cls.ids = fx.rulebook_snapshot()
        cls.snap = c1.Snapshot.from_json(cls.rows.doc())

    def ev(self, *names: str) -> list[str]:
        out = []
        for name in names:
            value = self.ids[name]
            out += [self.rows.ev(r) for r in value] if isinstance(value, list) else [self.rows.ev(value)]
        return out

    def missing(self, tags: dict, claims: list[dict], context: dict | None = None, rows: fx.Rows | None = None,
                snap: c1.Snapshot | None = None) -> list[str]:
        rows, snap, context = rows or self.rows, snap or self.snap, context or self.CN
        report = fx.report("run_case-260925100000", claims, snapshot_id=rows.snapshot_id)
        records = c1.score_report_claims(report, snap, report["run_id"], rows.snapshot_id, context)
        return c3.required_evidence_ok(tags, report, records, context, snap, rows.snapshot_id)[1]

    def test_share_signal_takes_share_metrics(self):
        world = self.ev("all_hs6_202401", "all_hs6_202301")
        d_s = fx.claim("ds", "share_change", "d_s", Decimal("-1.4"), "pp", "DOWN", self.ev("cn_2401", "cn_2301") + world,
                       baseline="202301")
        r_u = fx.claim("ru", "change", "r_U", Decimal("-8.5"), "%", "DOWN", self.ev("cn_2401", "cn_2301"),
                       baseline="202301")
        tags = {"share": ["comparability_ok"]}
        self.assertEqual(self.missing(tags, [d_s]), [])
        self.assertEqual(self.missing(tags, [r_u]), ["share:comparability_ok"])  # 점유율 신호에 단가 변화는 안 된다
        self.assertEqual(self.missing({"unit_value": ["comparability_ok"]}, [r_u]), [])

    def test_country_and_world_change_needs_four_value_claims(self):
        claims = [fx.claim(f"v{i}", "value", "V", None, "USD", "NA", self.ev(name), partner=partner, period=month)
                  for i, (partner, month, name) in enumerate((("CN", "202401", "cn_2401"), ("CN", "202301", "cn_2301"),
                                                              ("ALL", "202401", "all_hs4_202401"),
                                                              ("ALL", "202301", "all_hs4_202301")))]
        for claim, value in zip(claims, (21_876_681, 20_000_000, 56_680_573, 50_000_000)):
            claim["value"] = value
        tags = {"share": ["country_and_world_change_shown"]}
        self.assertEqual(self.missing(tags, claims), [])
        self.assertEqual(self.missing(tags, claims[:3]), ["share:country_and_world_change_shown"])

    def test_partner_comparison_needs_set_member_and_family_metric(self):
        world = self.ev("all_hs6_202401", "all_hs6_202301")
        jp_ds = fx.claim("cj", "comparison", "d_s", Decimal("-0.7"), "pp", "DOWN", self.ev("jp_2401", "jp_2301") + world,
                         partner="JP", baseline="202301")
        jp_ru = fx.claim("cr", "comparison", "r_U", Decimal("-38.7"), "%", "DOWN", self.ev("jp_2401", "jp_2301"),
                         partner="JP", baseline="202301")
        kh_ru = fx.claim("ck", "comparison", "r_U", None, "%", "NA", self.ev("kh_2401", "kh_2301"), partner="KH",
                         baseline="202301")
        self.assertEqual(self.missing({"share": ["partner_comparison_done"]}, [jp_ds]), [])
        self.assertEqual(self.missing({"share": ["partner_comparison_done"]}, [jp_ru]), ["share:partner_comparison_done"])
        self.assertEqual(self.missing({"unit_value": ["partner_comparison_done"]}, [jp_ru]), [])
        self.assertEqual(self.missing({"unit_value": ["partner_comparison_done"]}, [kh_ru]),  # KH는 CN의 비교집합 밖
                         ["unit_value:partner_comparison_done"])

    def test_precision_needs_two_time_parent_value_and_weight(self):
        claims = [fx.claim("v1", "value", "V", 21_876_681, "USD", "NA", self.ev("cn_2401")),
                  fx.claim("q1", "value", "Q", 1_075_490, "kg", "NA", self.ev("cn_2401")),
                  fx.claim("v0", "value", "V", 20_000_000, "USD", "NA", self.ev("cn_2301"), period="202301"),
                  fx.claim("q0", "value", "Q", 800_000, "kg", "NA", self.ev("cn_2301"), period="202301")]
        tags = {"unit_value": ["precision_sensitivity_shown"]}
        self.assertEqual(self.missing(tags, claims), [])
        self.assertEqual(self.missing(tags, claims[:3]), ["unit_value:precision_sensitivity_shown"])

    def test_all_observed_hold_is_satisfiable(self):
        # 시나리오 6 모양: 두 시점 부모 행이 모두 OBSERVED인데 기준월 중량 0이라 단가·변화율을 계산하지 않는다
        rows = fx.Rows("controlled_fixture_v0", fx.ORACLE_PLAN)
        before = rows.obs("CN", "850450", "202301", 100, 0, request="hs4_CN_2023")
        now = rows.obs("CN", "850450", "202401", 200, 10, request="hs4_CN_2024")
        snap = c1.Snapshot.from_json(rows.doc())
        evidence = [rows.ev(now), rows.ev(before)]
        tags = {"unit_value": ["missingness_listed", "failure_vs_not_collected_distinguished", "no_zero_fill"]}
        null_claim = fx.claim("ru", "change", "r_U", None, "%", "NA", evidence, baseline="202301")
        filled = fx.claim("ru", "change", "r_U", Decimal("100.0"), "%", "UP", evidence, baseline="202301")
        self.assertEqual(self.missing(tags, [null_claim], rows=rows, snap=snap), [])
        self.assertEqual(self.missing(tags, [filled], rows=rows, snap=snap),
                         ["unit_value:missingness_listed", "unit_value:no_zero_fill"])
        self.assertEqual(self.missing(tags, [], rows=rows, snap=snap), ["unit_value:missingness_listed"])

    def test_comparison_incomplete_lists_a_peer_gap(self):
        jp = dict(self.CN, partner="JP")  # JP의 비교국 TR(계획 밖)은 NOT_COLLECTED
        tr = fx.claim("tr", "data_status", "observation_status", "NOT_COLLECTED", None, "NA", self.ev("tr_hs6_2401"),
                      partner="TR")
        tags = {"unit_value": ["missingness_listed", "failure_vs_not_collected_distinguished"]}
        self.assertEqual(self.missing(tags, [tr], jp), [])
        wrong = dict(tr, value="REQUEST_FAILED")
        self.assertEqual(self.missing(tags, [wrong], jp),
                         ["unit_value:missingness_listed", "unit_value:failure_vs_not_collected_distinguished"])

    def test_target_gaps_must_each_be_listed_correctly(self):
        fr = dict(self.CN, partner="FR")  # FR 202401은 UNRESOLVED_ZERO, 202301은 성공한 요청이 없어 상태를 정할 수 없다
        listed = fx.claim("s", "data_status", "observation_status", "UNRESOLVED_ZERO", None, "NA", self.ev("fr_2401"),
                          partner="FR")
        tags = {"unit_value": ["missingness_listed", "failure_vs_not_collected_distinguished"]}
        self.assertEqual(self.missing(tags, [listed], fr), [])
        self.assertEqual(self.missing(tags, [dict(listed, value="NOT_COLLECTED")], fr),
                         ["unit_value:missingness_listed", "unit_value:failure_vs_not_collected_distinguished"])

    def test_zero_fill_counts_even_when_first_outcome_is_unit(self):
        de = fx.claim("u", "value", "U", 0, "USD/톤", "NA", self.ev("de_2401"), partner="DE")
        record = c1.score_claim(de, 0, self.snap, "run_case-260925100000", "report-1", self.rows.snapshot_id)
        self.assertEqual((record["outcome"], record["expected_value"]), (c1.WRONG_UNIT, None))
        self.assertEqual(self.missing({"unit_value": ["no_zero_fill"]}, [de], dict(self.CN, partner="DE")),
                         ["unit_value:no_zero_fill"])

    def test_two_signal_case_reports_missing_codes_per_signal(self):
        d_s = fx.claim("ds", "share_change", "d_s", Decimal("-1.4"), "pp", "DOWN",
                       self.ev("cn_2401", "cn_2301", "all_hs6_202401", "all_hs6_202301"), baseline="202301")
        tags = {"unit_value": ["comparability_ok"], "share": ["comparability_ok"]}
        self.assertEqual(self.missing(tags, [d_s]), ["unit_value:comparability_ok"])


if __name__ == "__main__":
    unittest.main()
