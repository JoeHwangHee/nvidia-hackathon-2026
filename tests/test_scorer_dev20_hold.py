"""독립 채점기 단위 C3의 필수 근거 판정 조건(시나리오 명세 eval/scenarios/SCENARIO_SPEC.md §5.3 판정 조건표)을 dev20의
불일치 보류(`hold_inconsistent`, 사용자 결정 14) 5건 모양에서 시험한다.

- 커밋된 dev20 원천으로 임시 폴더에 스냅샷을 빌드하고(설치 명령과 같은 순서, 단위 V2), 채점기 명령과 같은 읽기
  (eval.scorer.__main__.load_snapshot)로 연다. 정답표(eval/dev/dev20/answers/answers.json)의 필수 근거 코드를 그대로 쓴다.
- 사례마다 필수 근거를 모두 채우는 보고서(값은 채점기 기대값으로 적어 CORRECT)가 세 채점 키를 모두 참으로 받고, 코드
  하나만 깨뜨린 변형은 그 코드 하나만 채우지 못한 것으로 나오는지 본다. 관측은 모두 OBSERVED인데 부모·하위 대조, 구성 분해,
  전체국가 분모가 성립하지 않는 보고서에서도 채울 수 있는 조건인지 확인하는 시험이다.
- 네트워크·키 없이 돈다. 봉인 자료를 쓰지 않는다.
"""
import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

import scorer_fixtures as fx
from eval.datagen import dev20
from eval.scorer import claims as c1
from eval.scorer import prose as c2
from eval.scorer import results as c3
from eval.scorer.__main__ import load_snapshot
from tradesentry.contract.policy_load import load_policy

ROOT = Path(__file__).resolve().parents[1]
DEV20 = ROOT / "eval" / "dev" / "dev20"
UNIT_CASES = ("850431-XN-202408", "850432-XQ-202410", "850431-XO-202410")  # 부모·하위 불일치, HS10 집합 변경, 하위 중량 0
SHARE_CASES = ("850432-XL-202406", "850490-XN-202305")                     # 전체국가 분모 < 대상국 금액(비교월, 기준월)
RUN_ID = "run_case-260925100000"


class Dev20InconsistentHoldTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cases = json.loads((DEV20 / "input" / "cases.json").read_text(encoding="utf-8"))
        cls.cases = {c["case_id"]: c for c in cases["cases"]}
        answers_doc = json.loads((DEV20 / "answers" / "answers.json").read_text(encoding="utf-8"))
        cls.answers = c3.read_answer_table(answers_doc)
        cls.rules = {c["case_id"]: c["rule"] for c in answers_doc["cases"]}
        with tempfile.TemporaryDirectory() as tmp:
            collector = dev20.materialize_collector(ROOT / "data" / "snapshots" / "dev20", DEV20 / "input" / "source" / "raw",
                                                    Path(tmp) / "dev20")
            db = Path(tmp) / "build.sqlite"
            dev20.build_and_verify(collector, ROOT / "data" / "reference" / "peer_group_dev20.csv", "dev20",
                                   load_policy(cases["policy_version"]), db)
            cls.snap, _ = load_snapshot(db, "dev20")

    # ------------------------------------------------------------------ 보고서 만들기

    def context(self, case_id: str) -> dict:
        case = self.cases[case_id]
        return {"hs6": case["hs6"], "partner": case["partner"], "month": case["month"], "grouping_version": "g0"}

    def ev(self, rowids) -> list[str]:
        return [f"ev:dev20:observation:{r}" for r in sorted(rowids)]

    def claim(self, case_id: str, claim_id: str, claim_type: str, metric: str, *, partner: str | None = None,
              period: str | None = None, change: bool = False, value: object = "expected") -> dict:
        """채점기 기대값(value="expected")이나 준 값으로 typed claim 하나를 만든다. 근거는 기대값이 요구하는 묶음마다 한 행."""
        ctx = self.context(case_id)
        partner = partner or ctx["partner"]
        period = period or ctx["month"]
        baseline = c1.shift_month(ctx["month"], -12) if change else None
        base, hs10 = c1.parse_metric(metric)
        expect = c1.expect_numeric(self.snap, base, hs10, ctx["hs6"], partner, period, baseline)
        if value == "expected":
            value = None if expect.value is None else c1.number_out(expect.value, c1.METRIC_DIGITS[base])
        direction = "NA"
        if c1.is_directional(claim_type, base) and value is not None:
            direction = "UP" if value > 0 else ("DOWN" if value < 0 else "FLAT")
        evidence = self.ev({min(group) for group in expect.required if group})
        return fx.claim(claim_id, claim_type, metric, value, c1.METRIC_UNITS[base], direction, evidence, hs6=ctx["hs6"],
                        partner=partner, period=period, baseline=baseline)

    def rows_of(self, case_id: str, months: tuple[str, ...]) -> set[int]:
        """대상국의 부모 HS6 행과 HS10 하위 행(주어진 달)."""
        ctx = self.context(case_id)
        rows: set[int] = set()
        for month in months:
            rows |= set(self.snap.parent.get((ctx["partner"], ctx["hs6"], month), []))
            for kids in self.snap.children.get((ctx["partner"], ctx["hs6"], month), {}).values():
                rows |= set(kids)
        return rows

    def months(self, case_id: str) -> tuple[str, str]:
        t = self.context(case_id)["month"]
        return t, c1.shift_month(t, -12)

    def unit_claims(self, case_id: str) -> list[dict]:
        """단가 불일치 보류: 부모 단가 변화(계산됨)와 성립하지 않는 분해 셋(null)."""
        claims = [self.claim(case_id, "ru", "change", "r_U", change=True)]
        claims += [self.claim(case_id, base, "decomposition", base, change=True) for base in c1.DECOMPOSITION_BASES]
        return claims

    def share_claims(self, case_id: str) -> list[dict]:
        """점유율 분모 불완전 보류: 대상국·ALL 금액의 두 시점 값과 점유율 변화."""
        t, b = self.months(case_id)
        claims = [self.claim(case_id, f"v_{p}_{m}", "value", "V", partner=p, period=m)
                  for p in (self.context(case_id)["partner"], c1.ALL) for m in (t, b)]
        return claims + [self.claim(case_id, "ds", "share_change", "d_s", change=True)]

    def report(self, case_id: str, claims: list[dict], evidence_rows: set[int]) -> dict:
        signal = {"unit_value": "NOT_TRIGGERED", "share": "NOT_TRIGGERED"}
        signal["unit_value" if case_id in UNIT_CASES else "share"] = "HOLD"
        return fx.report(RUN_ID, claims, case_id=case_id, snapshot_id="dev20", review_status="HOLD",
                         signal_status=signal, evidence_ids=self.ev(evidence_rows))

    def good(self, case_id: str) -> dict:
        claims = self.unit_claims(case_id) if case_id in UNIT_CASES else self.share_claims(case_id)
        return self.report(case_id, claims, self.rows_of(case_id, self.months(case_id)))

    def records(self, report: dict) -> list[dict]:
        return c1.score_report_claims(report, self.snap, RUN_ID, "dev20", self.context(report["case_id"])) \
            + c2.score_report_prose(report, RUN_ID, self.snap.hs_codes, [])

    def missing(self, report: dict) -> list[str]:
        case_id = report["case_id"]
        return c3.required_evidence_ok(self.answers[case_id]["required_evidence"], report, self.records(report),
                                       self.context(case_id), self.snap, "dev20")[1]

    # ------------------------------------------------------------------ 시험

    def test_answers_use_the_inconsistent_hold_codes(self):
        expected = {"unit_value": ["parent_child_match_V_and_Q", "comparability_ok", "no_zero_fill"],
                    "share": ["country_and_world_change_shown", "comparability_ok", "no_zero_fill"]}
        found = [cid for cid, rule in self.rules.items() if "hold_inconsistent" in rule.values()]
        self.assertEqual(sorted(found), sorted(UNIT_CASES + SHARE_CASES))
        for case_id in found:
            signal = "unit_value" if case_id in UNIT_CASES else "share"
            self.assertEqual(self.answers[case_id]["required_evidence"], {signal: expected[signal]})
            self.assertEqual(self.answers[case_id]["review_status"], "HOLD")

    def test_shapes_are_all_observed_and_undecomposable(self):
        for case_id in UNIT_CASES:
            with self.subTest(case_id=case_id):
                ctx = self.context(case_id)
                for month in self.months(case_id):
                    self.assertTrue(self.snap.parent.get((ctx["partner"], ctx["hs6"], month)))
                    self.assertTrue(self.snap.children.get((ctx["partner"], ctx["hs6"], month)))
                    self.assertEqual(c3._Report({}, [], ctx, self.snap, "dev20").gaps("unit_value"), [])
                self.assertIsNone(c1.expect_numeric(self.snap, "within_effect", None, ctx["hs6"], ctx["partner"],
                                                    ctx["month"], self.months(case_id)[1]).value)
        for case_id in SHARE_CASES:  # 분모가 대상국보다 작아도 점유율은 계산된다(100% 초과)
            with self.subTest(case_id=case_id):
                ctx = self.context(case_id)
                shares = [c1.expect_numeric(self.snap, "s", None, ctx["hs6"], ctx["partner"], m, None).value
                          for m in self.months(case_id)]
                self.assertTrue(all(s is not None for s in shares))
                self.assertTrue(any(s > 100 for s in shares))

    def test_complete_reports_satisfy_every_key(self):
        for case_id in UNIT_CASES + SHARE_CASES:
            with self.subTest(case_id=case_id):
                report = self.good(case_id)
                records = self.records(report)
                self.assertTrue(all(r["outcome"] == c1.CORRECT for r in records if r["source"] == c1.SOURCE_CLAIM),
                                [r["note"] for r in records if r["outcome"] != c1.CORRECT])
                line = fx.batch_line(RUN_ID, case_id, dataset="dev20", snapshot_id="dev20", review="HOLD",
                                     signal=report["signal_status"])
                out = c3.result_line(line, report, records, self.answers[case_id],
                                     c3.case_context(self.cases[case_id], line), self.snap)
                self.assertEqual((out["required_evidence_ok"], out["numeric_ok"], out["provenance_ok"]),
                                 (True, True, True))

    def test_unit_hold_breaks_one_code_at_a_time(self):
        for case_id in UNIT_CASES:
            t, b = self.months(case_id)
            with self.subTest(case_id=case_id, broken="parent_child_match_V_and_Q"):
                # 부모 단가 변화만 남기고 근거는 비교월 부모·하위와 기준월 부모만 인용한다(기준월 하위 행 빠짐)
                ctx = self.context(case_id)
                rows = self.rows_of(case_id, (t,)) | set(self.snap.parent[(ctx["partner"], ctx["hs6"], b)])
                report = self.report(case_id, [self.claim(case_id, "ru", "change", "r_U", change=True)], rows)
                self.assertEqual(self.missing(report), ["unit_value:parent_child_match_V_and_Q"])
            with self.subTest(case_id=case_id, broken="comparability_ok"):
                good = self.good(case_id)
                report = dict(good, claims=[c for c in good["claims"] if c["metric"] != "r_U"])
                self.assertEqual(self.missing(report), ["unit_value:comparability_ok"])
            with self.subTest(case_id=case_id, broken="no_zero_fill"):
                good = self.good(case_id)
                filled = [dict(c, value=Decimal("0.00"), direction="FLAT") if c["metric"] == "within_effect" else c
                          for c in good["claims"]]
                self.assertEqual(self.missing(dict(good, claims=filled)), ["unit_value:no_zero_fill"])

    def test_zero_weight_child_unit_value_must_stay_null(self):
        case_id = "850431-XO-202410"
        good = self.good(case_id)
        code = next(code for code, rows in self.snap.children[("XO", "850431", "202410")].items()
                    if all(self.snap.values_of(r)[1] == 0 for r in rows))
        null_u = self.claim(case_id, "u0", "value", f"U@{code}")
        self.assertIsNone(null_u["value"])
        self.assertEqual(self.missing(dict(good, claims=good["claims"] + [null_u])), [])
        zero_u = self.claim(case_id, "u0", "value", f"U@{code}", value=Decimal("0.00"))
        self.assertEqual(self.missing(dict(good, claims=good["claims"] + [zero_u])), ["unit_value:no_zero_fill"])

    def test_share_hold_breaks_one_code_at_a_time(self):
        for case_id in SHARE_CASES:
            t, b = self.months(case_id)
            good = self.good(case_id)
            with self.subTest(case_id=case_id, broken="country_and_world_change_shown"):
                report = dict(good, claims=[c for c in good["claims"] if c["claim_id"] != f"v_ALL_{b}"])
                self.assertEqual(self.missing(report), ["share:country_and_world_change_shown"])
            with self.subTest(case_id=case_id, broken="comparability_ok"):  # 단가 변화는 점유율 계열의 비교 점검이 아니다
                claims = [c for c in good["claims"] if c["metric"] != "d_s"]
                claims.append(self.claim(case_id, "ru", "change", "r_U", change=True))
                self.assertEqual(self.missing(dict(good, claims=claims)), ["share:comparability_ok"])
            # 대상국에 그 달 행이 없는 HS10 코드(스냅샷의 그 HS6 아래 코드)의 단가를 0으로 채운다. 850490에는 그런 코드가
            # 없어(대상국이 모든 코드를 가진다) 850432-XL만 이 변형을 만든다
            ctx = self.context(case_id)
            mine = set(self.snap.children[(ctx["partner"], ctx["hs6"], t)])
            absent = sorted(c for c in self.snap.hs10_codes if c.startswith(ctx["hs6"]) and c not in mine)
            if absent:
                with self.subTest(case_id=case_id, broken="no_zero_fill"):
                    filled = self.claim(case_id, "u0", "value", f"U@{absent[0]}", period=t, value=Decimal("0.00"))
                    self.assertEqual(self.missing(dict(good, claims=good["claims"] + [filled])), ["share:no_zero_fill"])
        self.assertTrue(any(self.snap.hs10_codes))

    def test_empty_report_fails_all_but_the_negative_condition(self):
        # no_zero_fill은 "채우지 않았음"이라 claim이 없으면 채운다. 나머지 두 코드는 채우지 못한다
        for case_id in UNIT_CASES + SHARE_CASES:
            with self.subTest(case_id=case_id):
                signal = "unit_value" if case_id in UNIT_CASES else "share"
                codes = self.answers[case_id]["required_evidence"][signal]
                self.assertEqual(self.missing(self.report(case_id, [], set())),
                                 [f"{signal}:{code}" for code in codes if code != "no_zero_fill"])


if __name__ == "__main__":
    unittest.main()
