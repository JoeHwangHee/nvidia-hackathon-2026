"""단위 V4(datagen_holdout40_check) 동작 시험: holdout40 형식 묶음의 통과·실패와 보고의 정보 비노출, 명령 종료 코드.

- 시험 묶음은 이 파일이 분류마다 판정 근거 규칙 하나로 만드는 가짜 holdout40 형식 묶음이다(실제 holdout40이 아니다.
  봉인 폴더를 열지 않는다). 식별자는 `fx-`로 시작하고, 부모 원본 계열 ID와 가짜 dev20 목록은 글자에서 sha256으로 만든다.
- 파일은 모두 임시 폴더에 쓰고 지운다. 커밋된 dev20 묶음의 검사는 단위 V2 시험(tests/units/V2/test_dev20.py)이 한다.
"""
import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from eval.datagen import holdout40_check as v4

# 분류 → 시험 묶음에 쓰는 판정 근거 규칙(명세 §4의 기대 처리 안에서 하나씩).
CLASS_RULE = {
    1: {"unit_value": "composition_explained", "share": None},
    2: {"unit_value": "unexplained", "share": None},
    3: {"unit_value": "unexplained", "share": None},
    4: {"unit_value": "hold_missing", "share": None},
    5: {"unit_value": "hold_inconsistent", "share": None},
    6: {"unit_value": "rounding_unstable", "share": None},
    7: {"unit_value": None, "share": "hold_inconsistent"},
    8: {"unit_value": None, "share": "unexplained"},
    9: {"unit_value": "unexplained", "share": None},
    10: {"unit_value": "hold_missing", "share": "unexplained"},
}


def pid(text: str) -> str:
    return "ps_" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def fake_bundle(dataset: str = "holdout40") -> tuple[dict, dict]:
    cases, answers = [], []
    for klass, count in v4.ALLOCATION[dataset].items():
        for n in range(count):
            case_id = f"fx-{klass:02d}-{n}"
            month = f"2024{(n % 12) + 1:02d}"
            cases.append({"case_id": case_id, "hs6": "999901", "partner": "XA", "month": month})
            signals, status, review, unresolved, evidence = v4.rule_outcome(CLASS_RULE[klass])
            answers.append({"case_id": case_id, "scenario_class": klass, "parent_series_id": pid(case_id),
                            "rule": dict(CLASS_RULE[klass]),
                            "expected": {"signals": signals, "signal_status": status, "review_status": review,
                                         "unresolved_evidence": unresolved, "required_evidence": evidence}})
    head = {"schema_version": 1, "dataset": dataset, "snapshot_id": "fixture_v4", "policy_version": "dev-0.1"}
    return {**head, "cases": cases}, {**head, "cases": answers}


def fake_dev20_ids() -> dict:
    return {"schema_version": 1, "dataset": "dev20", "id_rule": "시험용",
            "parent_series_ids": sorted(pid(f"dev20-{n}") for n in range(20))}


def failed(report: dict) -> dict:
    return {c["name"]: c.get("problems") for c in report["checks"] if c["ok"] is False}


class DocumentCheckTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.cases, self.answers = fake_bundle()
        self.ids = fake_dev20_ids()

    def check(self) -> dict:
        return v4.check_documents(self.cases, self.answers, self.ids)

    def test_valid_holdout_passes(self):
        report = self.check()
        self.assertTrue(report["ok"], failed(report))
        self.assertEqual(report["overlap_with_dev20"], 0)
        self.assertEqual(report["counts"]["by_class"], {str(k): n for k, n in v4.ALLOCATION["holdout40"].items()})
        self.assertEqual(v4.TOTALS, {"dev20": 20, "holdout40": 40})

    def test_dev20_bundle_skips_overlap(self):
        cases, answers = fake_bundle("dev20")
        report = v4.check_documents(cases, answers, None)
        self.assertTrue(report["ok"], failed(report))
        self.assertIsNone(report["overlap_with_dev20"])

    def test_overlap_with_dev20_is_caught(self):
        self.answers["cases"][5]["parent_series_id"] = self.ids["parent_series_ids"][0]
        report = self.check()
        self.assertFalse(report["ok"])
        self.assertEqual(report["overlap_with_dev20"], 1)
        self.assertIn("dev20_parent_series_overlap", failed(report))

    def test_missing_or_malformed_dev20_list_fails(self):
        self.assertIn("dev20_parent_series_overlap", failed(v4.check_documents(self.cases, self.answers, None)))
        bad = dict(self.ids, parent_series_ids=["not-an-id"])
        self.assertIn("dev20_parent_series_overlap", failed(v4.check_documents(self.cases, self.answers, bad)))

    def test_class_count_mismatch_is_caught(self):
        dropped = self.cases["cases"].pop()["case_id"]
        self.answers["cases"] = [a for a in self.answers["cases"] if a["case_id"] != dropped]
        self.assertIn("class_counts", failed(self.check()))

    def test_input_list_must_not_carry_answers(self):
        self.cases["cases"][0]["scenario_class"] = 1
        self.assertIn("cases_schema", failed(self.check()))

    def test_expected_must_follow_rule(self):
        self.answers["cases"][0]["expected"]["review_status"] = "HOLD"
        problems = failed(self.check())["answers_schema"]
        self.assertTrue(any("review_status" in kind for kind in problems), problems)

    def test_class_rule_is_enforced(self):
        entry = next(a for a in self.answers["cases"] if a["scenario_class"] == 1)
        entry["rule"] = {"unit_value": "unexplained", "share": None}
        signals, status, review, unresolved, evidence = v4.rule_outcome(entry["rule"])
        entry["expected"].update(signals=signals, signal_status=status, review_status=review,
                                 unresolved_evidence=unresolved, required_evidence=evidence)
        self.assertIn("분류 1의 기대 처리와 다르다", failed(self.check())["answers_schema"])

    def test_class10_needs_different_signal_states(self):
        entry = next(a for a in self.answers["cases"] if a["scenario_class"] == 10)
        entry["rule"] = {"unit_value": "unexplained", "share": "unexplained"}
        signals, status, review, unresolved, evidence = v4.rule_outcome(entry["rule"])
        entry["expected"].update(signals=signals, signal_status=status, review_status=review,
                                 unresolved_evidence=unresolved, required_evidence=evidence)
        self.assertIn("분류 10의 기대 처리와 다르다", failed(self.check())["answers_schema"])

    def test_unknown_evidence_is_refused(self):
        self.answers["cases"][0]["expected"]["required_evidence"].append("made_up_tag")
        self.assertIn("answers_schema", failed(self.check()))

    def test_case_id_sets_must_match(self):
        self.answers["cases"][0]["case_id"] = "fx-99-0"
        self.assertIn("case_ids_match", failed(self.check()))

    def test_case_id_format_and_p2_consistency(self):
        self.cases["cases"][0]["case_id"] = "-bad-"
        self.assertIn("cases_schema", failed(self.check()))
        self.cases, self.answers = fake_bundle()
        self.cases["cases"][0]["case_id"] = "999901-XA-202402"  # 항목의 달(202401)과 다르다
        self.assertIn("cases_schema", failed(self.check()))
        self.cases, self.answers = fake_bundle()
        self.cases["cases"][0]["case_id"] = "x" * 65
        self.assertIn("cases_schema", failed(self.check()))

    def test_rule_outcome_aggregates_maintain_and_hold(self):
        signals, status, review, unresolved, evidence = v4.rule_outcome(
            {"unit_value": "hold_missing", "share": "unexplained"})
        self.assertEqual((review, unresolved), ("MAINTAIN", True))
        self.assertEqual(evidence, {"unit_value": list(v4.RULES["unit_value"]["hold_missing"][1]),
                                    "share": list(v4.RULES["share"]["unexplained"][1])})  # 두 신호가 발동하면 신호별 목록
        self.assertEqual(v4.rule_outcome({"unit_value": "unexplained", "share": None})[4],
                         list(v4.RULES["unit_value"]["unexplained"][1]))  # 한 신호만 발동하면 목록
        self.assertEqual(status, {"unit_value": "HOLD", "share": "MAINTAIN"})
        self.assertEqual(signals, {"unit_value": "TRIGGERED", "share": "TRIGGERED"})
        self.assertEqual(v4.rule_outcome({"unit_value": "composition_explained", "share": "hold_missing"})[2:4],
                         ("HOLD", False))

    def test_vocabulary_is_the_mt1_thirteen(self):
        self.assertEqual(len(v4.EVIDENCE_VOCABULARY), 13)
        used = {code for family in v4.RULES.values() for _, codes in family.values() for code in codes}
        self.assertLessEqual(used, set(v4.EVIDENCE_VOCABULARY))

    def test_report_reveals_no_case_ids(self):
        self.answers["cases"][0]["expected"]["review_status"] = "HOLD"
        self.answers["cases"][1]["parent_series_id"] = self.ids["parent_series_ids"][3]
        text = json.dumps(self.check(), ensure_ascii=False)
        for item in self.cases["cases"]:
            self.assertNotIn(item["case_id"], text)
        for value in self.ids["parent_series_ids"]:
            self.assertNotIn(value, text)


class CommandTest(unittest.TestCase):
    def run_main(self, cases: dict, answers: dict, ids: dict | None) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as tmp:
            paths = {name: Path(tmp) / f"{name}.json" for name in ("cases", "answers", "ids")}
            for name, doc in (("cases", cases), ("answers", answers), ("ids", ids)):
                if doc is not None:
                    paths[name].write_text(json.dumps(doc), encoding="utf-8")
            argv = ["--cases", str(paths["cases"]), "--answers", str(paths["answers"]), "--dev20-ids", str(paths["ids"])]
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = v4.main(argv)
            return code, out.getvalue(), tmp

    def test_exit_codes_and_quiet_output(self):
        cases, answers = fake_bundle()
        code, out, tmp = self.run_main(cases, answers, fake_dev20_ids())
        self.assertEqual(code, v4.EXIT_OK)
        self.assertTrue(json.loads(out)["ok"])
        self.assertNotIn(tmp, out)
        answers["cases"][0]["parent_series_id"] = fake_dev20_ids()["parent_series_ids"][0]
        code, out, tmp = self.run_main(cases, answers, fake_dev20_ids())
        self.assertEqual(code, v4.EXIT_FAILED)
        self.assertNotIn(tmp, out)
        code, out, tmp = self.run_main(cases, answers, None)  # dev20 목록 파일이 없다
        self.assertEqual(code, v4.EXIT_USAGE)
        self.assertNotIn(tmp, out)

    def test_usage_error(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(v4.main([]), v4.EXIT_USAGE)

    def test_run_input_keys(self):
        with self.assertRaises(ValueError):
            v4.run({"cases_file": "x", "answers_file": "y", "sealed_dir": "z"})
        with self.assertRaises(v4.CheckInputError):
            v4.run({"cases_file": "tests/units/V4/no-such-file.json", "answers_file": "tests/units/V4/input.json",
                    "dev20_parent_series_ids_file": "tests/units/V4/fixture_dev20_ids.json"})


if __name__ == "__main__":
    unittest.main()
