"""단위 R3(validator_validate) 규칙 시험. 골든 쌍 밖의 경우를 본다.

- 깨끗한 보고서: 단위 R1이 검증된 지표로 채운 full 보고서는 사유가 0건이다.
- 변조 시험(로드맵 §3 MVP 체크리스트 3번): 숫자·단위·근거 ID·스냅샷 변조와 뒷받침 없는 산문 숫자·증감을 잡는다.
  막을지(모드별)는 단위 R4 시험(tests/units/R4)이 R3과 함께 본다.
- 산문 규칙: 룰북 B3-2의 예시 표와 경계 사례 표, R1 문장 틀의 자기 일관성(틀 문장은 산문 사유가 0건이다).
- 값 비교: 룰북 B3-1 경계 사례. 입력을 바꾸지 않는다.
시험 값은 모두 합성이다(실제 통계가 아니다). 합성 사례 A/B/C는 실제 사건이 아니다.
"""
import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path

from tradesentry.reports import claims as r1
from tradesentry.validator import validate

HERE = Path(__file__).resolve().parent
EV = "ev:controlled_fixture_v0:observation:"
CLEAN_METRICS = ("m-U-0", "m-U-1", "m-rU", "m-within", "m-mix", "m-res", "m-w1-0", "m-w1-1", "m-s-0", "m-s-1", "m-ds")
CLEAN_NARRATIVE = ("단가가 kg당 6.00달러에서 3.60달러로 40.0% 낮아졌다. 구성 변화 효과가 kg당 -2.40달러이고 "
                   "하위품목 단가는 변화가 없다.")


def golden_input() -> dict:
    return json.loads((HERE / "input.json").read_text(encoding="utf-8"), parse_float=Decimal)


def clean_input() -> dict:
    """golden 입력의 봉투·행으로 R1이 채운 깨끗한 full 보고서를 만든다."""
    inp = golden_input()
    metrics = [m for envelope in inp["envelopes"] for m in envelope["metrics"]]
    requests = [{"claim_id": f"c{i}", "metric_id": m} for i, m in enumerate(CLEAN_METRICS, start=1)]
    filled = r1.run({"mode": "full", "case": inp["case"], "metrics": metrics, "statuses": [], "requests": requests})
    assert filled["rejected"] == [], filled["rejected"]
    inp["run"]["mode"] = "full"
    inp["report"] = {
        "report_id": "rep-A-full-1", "run_id": inp["run"]["run_id"], "case_id": "A-composition", "mode": "full",
        "claims": filled["claims"], "narrative": CLEAN_NARRATIVE,
        "hypotheses": ["하위품목 구성 변화가 이어질지는 이 자료로 확인할 수 없다."],
        "review_status": "MONITOR", "signal_status": {"unit_value": "MONITOR", "share": "NOT_TRIGGERED"},
        "unresolved_evidence": False, "created_at": "2026-09-25T10:00:30+09:00",
        "policy_version": "dev-0.1", "snapshot_id": "controlled_fixture_v0", "grouping_version": "g0"}
    return inp


def codes(out: dict) -> list[tuple[str, str]]:
    return [(f["code"], f["path"]) for f in out["findings"]]


def index_of(inp: dict, claim_id: str) -> int:
    return next(i for i, c in enumerate(inp["report"]["claims"]) if c["claim_id"] == claim_id)


class CleanReportTest(unittest.TestCase):
    def test_template_report_has_no_finding(self):
        self.assertEqual(validate.run(clean_input())["findings"], [])

    def test_input_is_not_changed(self):
        for inp in (clean_input(), golden_input()):
            before = copy.deepcopy(inp)
            validate.run(inp)
            self.assertEqual(inp, before)

    def test_equivalent_duplicate_row_is_accepted(self):
        # 룰북 B3-1 경계 18: 중복된 ALL HS10 행 둘 중 어느 쪽을 인용해도 근거 검사를 통과한다.
        inp = clean_input()
        claim = inp["report"]["claims"][index_of(inp, "c10")]
        claim["evidence_ids"] = [e.replace("observation:311", "observation:313") for e in claim["evidence_ids"]]
        self.assertEqual(validate.run(inp)["findings"], [])


class TamperTest(unittest.TestCase):
    """MVP 체크리스트 3번: 의도적으로 넣은 변조를 잡는다(변조 종류마다 하나 이상)."""

    def assert_found(self, inp: dict, code: str, path: str) -> dict:
        out = validate.run(inp)
        self.assertIn((code, path), codes(out), codes(out))
        return out

    def test_number_tamper(self):
        inp = clean_input()
        i = index_of(inp, "c2")
        inp["report"]["claims"][i]["value"] = Decimal("3.66")
        out = self.assert_found(inp, "NUMERIC_MISMATCH", f"claims[{i}].value")
        self.assertIn(("PROSE_UNBACKED", f"claims[{i}].text"), codes(out))  # 문장 속 3.60도 이제 뒷받침되지 않는다

    def test_number_written_for_not_computable_metric(self):
        inp = clean_input()
        for envelope in inp["envelopes"]:
            for metric in envelope["metrics"]:
                if metric["metric_id"] == "m-mix":
                    metric["value"] = None
        self.assert_found(inp, "NUMERIC_NOT_COMPUTABLE", f"claims[{index_of(inp, 'c5')}].value")

    def test_unit_tamper(self):
        inp = clean_input()
        i = index_of(inp, "c2")
        inp["report"]["claims"][i]["unit"] = "USD/톤"
        self.assert_found(inp, "UNIT_MISMATCH", f"claims[{i}].unit")
        inp = clean_input()
        i = index_of(inp, "c11")
        inp["report"]["claims"][i]["unit"] = "%"  # 룰북 B3-1 예시 11: 점유율 변화를 %로 적음
        self.assert_found(inp, "UNIT_MISMATCH", f"claims[{i}].unit")

    def test_evidence_id_tamper_unresolved(self):
        inp = clean_input()
        i = index_of(inp, "c3")
        inp["report"]["claims"][i]["evidence_ids"][1] = f"{EV}999999"
        out = self.assert_found(inp, "EVIDENCE_UNRESOLVED", f"claims[{i}].evidence_ids[1]")
        self.assertIn(("EVIDENCE_NOT_SUPPORTING", f"claims[{i}].evidence_ids"), codes(out))

    def test_evidence_id_tamper_to_row_not_returned(self):
        inp = clean_input()
        inp["rows"][f"{EV}555"] = {"partner_code": "CN", "hs_code": "850450", "hs_level": 6, "month": "202401",
                                   "flow": "export", "amount_usd": 999, "net_weight_kg": 9,
                                   "observation_status": "OBSERVED"}
        i = index_of(inp, "c2")
        inp["report"]["claims"][i]["evidence_ids"] = [f"{EV}555"]
        out = self.assert_found(inp, "PROVENANCE_NOT_RETURNED", f"claims[{i}].evidence_ids[0]")
        self.assertIn(("EVIDENCE_NOT_SUPPORTING", f"claims[{i}].evidence_ids"), codes(out))

    def test_evidence_id_format_and_missing(self):
        inp = clean_input()
        i = index_of(inp, "c2")
        inp["report"]["claims"][i]["evidence_ids"] = ["ev:controlled_fixture_v0:observation:0012", "row-201"]
        out = validate.run(inp)
        self.assertIn(("EVIDENCE_FORMAT", f"claims[{i}].evidence_ids[0]"), codes(out))
        self.assertIn(("EVIDENCE_FORMAT", f"claims[{i}].evidence_ids[1]"), codes(out))
        inp["report"]["claims"][i]["evidence_ids"] = []
        self.assert_found(inp, "EVIDENCE_MISSING", f"claims[{i}].evidence_ids")

    def test_change_claim_citing_only_one_month(self):
        # 룰북 B3-1 경계 17: 변화 주장에 t 행만 인용하고 t−12 행이 없다.
        inp = clean_input()
        i = index_of(inp, "c3")
        inp["report"]["claims"][i]["evidence_ids"] = [f"{EV}201"]
        self.assert_found(inp, "EVIDENCE_NOT_SUPPORTING", f"claims[{i}].evidence_ids")

    def test_total_row_evidence(self):
        inp = clean_input()
        i = index_of(inp, "c2")
        inp["report"]["claims"][i]["evidence_ids"] = [f"{EV}900"]
        out = self.assert_found(inp, "EVIDENCE_TOTAL_ROW", f"claims[{i}].evidence_ids[0]")
        self.assertIn(("EVIDENCE_NOT_SUPPORTING", f"claims[{i}].evidence_ids"), codes(out))

    def test_snapshot_tamper_in_report(self):
        inp = clean_input()
        inp["report"]["snapshot_id"] = "kcs_202201_202412_v2"
        self.assert_found(inp, "PROVENANCE_MISMATCH", "snapshot_id")

    def test_snapshot_tamper_in_evidence_id(self):
        inp = clean_input()
        i = index_of(inp, "c1")
        inp["report"]["claims"][i]["evidence_ids"] = ["ev:kcs_202201_202412_v2:observation:101"]
        out = self.assert_found(inp, "EVIDENCE_SNAPSHOT", f"claims[{i}].evidence_ids[0]")
        self.assertNotIn(("EVIDENCE_UNRESOLVED", f"claims[{i}].evidence_ids[0]"), codes(out))  # 풀림 규칙 2가 먼저다
        self.assertIn(("EVIDENCE_NOT_SUPPORTING", f"claims[{i}].evidence_ids"), codes(out))

    def test_snapshot_tamper_in_envelope_and_versions(self):
        inp = clean_input()
        inp["envelopes"][1]["snapshot_id"] = "kcs_202201_202412_v2"
        self.assert_found(inp, "PROVENANCE_ENVELOPE", "envelopes[1]")
        for key, value in (("policy_version", "policy_v1"), ("grouping_version", "g1"), ("run_id", "run_case-1"),
                           ("case_id", "B-residual"), ("mode", "freeform")):
            with self.subTest(key=key):
                inp = clean_input()
                inp["report"][key] = value
                self.assert_found(inp, "PROVENANCE_MISMATCH", key)

    def test_unbacked_prose_number(self):
        inp = clean_input()
        inp["report"]["narrative"] += " 단가는 55% 낮아졌다."
        out = validate.run(inp)
        self.assertEqual([f["detail"].split(":")[0] for f in out["findings"]], ["PT-1 표현 '55%'"])

    def test_prose_number_matching_another_claim_is_not_caught(self):
        # 룰북 B3-2 "한계": 주어를 맞추지 않으므로 다른 주장(중량 비중 50.0%)과 우연히 같은 숫자는 놓친다.
        inp = clean_input()
        inp["report"]["narrative"] += " 단가는 50% 낮아졌다."
        self.assertEqual(validate.run(inp)["findings"], [])

    def test_unbacked_prose_change(self):
        # 룰북 B3-2 예시 2(구 개발계획 G4 관문 시험에서 관찰된 오류): 점유율 10→6 감소를 "6→10 증가"로 썼다.
        inp = clean_input()
        inp["report"]["narrative"] = "점유율이 6%에서 10%로 늘었다."
        out = validate.run(inp)
        self.assertEqual([f["detail"].split(":")[0] for f in out["findings"]],
                         ["PT-8 표현 '6%에서 10%'", "PT-6 표현 '늘었'"])

    def test_direction_tamper(self):
        inp = clean_input()
        i = index_of(inp, "c3")
        inp["report"]["claims"][i]["direction"] = "UP"
        self.assertEqual(codes(validate.run(inp)), [("DIRECTION_MISMATCH", f"claims[{i}].direction")])

    def test_zero_shown_value_accepts_flat_and_real_sign(self):
        # 룰북 B3-1 경계 4: 반올림해 0이면 FLAT과 실제 부호 방향 모두 맞다.
        inp = clean_input()
        for envelope in inp["envelopes"]:
            for metric in envelope["metrics"]:
                if metric["metric_id"] == "m-res":
                    metric["value"] = Decimal("0.004")
        i = index_of(inp, "c6")
        for direction, ok in (("FLAT", True), ("UP", True), ("DOWN", False)):
            with self.subTest(direction=direction):
                inp["report"]["claims"][i]["direction"] = direction
                found = ("DIRECTION_MISMATCH", f"claims[{i}].direction") in codes(validate.run(inp))
                self.assertEqual(found, not ok)

    def test_referent_tampers(self):
        cases = [("c3", "baseline_period", "202212", "baseline_period"),
                 ("c2", "hs6", "850431", "hs6"),
                 ("c2", "claim_type", "share", "claim_type"),
                 ("c2", "baseline_period", "202301", "baseline_period"),
                 ("c3", "claim_type", "comparison", "partner"),
                 ("c2", "metric", "price", "metric")]
        for claim_id, key, value, where in cases:
            with self.subTest(key=key, value=value):
                inp = clean_input()
                i = index_of(inp, claim_id)
                inp["report"]["claims"][i][key] = value
                self.assert_found(inp, "REFERENT_MISMATCH", f"claims[{i}].{where}")

    def test_peer_value_must_be_comparison(self):
        inp = clean_input()
        i = index_of(inp, "c2")
        inp["report"]["claims"][i]["partner"] = "JP"
        out = self.assert_found(inp, "REFERENT_MISMATCH", f"claims[{i}].partner")
        self.assertIn(("NUMERIC_UNBACKED", f"claims[{i}].value"), codes(out))

    def test_status_tampers(self):
        cases = [("review_status", "MAINTAIN", "STATUS_INCONSISTENT", "review_status"),
                 ("unresolved_evidence", True, "STATUS_INCONSISTENT", "unresolved_evidence"),
                 ("review_status", "PRE_INVESTIGATION", "SCHEMA_STATUS", "review_status"),
                 ("review_status", "모니터링", "SCHEMA_STATUS", "review_status")]
        for key, value, code, where in cases:
            with self.subTest(key=key, value=value):
                inp = clean_input()
                inp["report"][key] = value
                self.assert_found(inp, code, where)
        inp = clean_input()
        inp["report"]["signal_status"]["share"] = "HOLD"  # 발동하지 않은 신호에 판정을 붙였다
        self.assert_found(inp, "STATUS_INCONSISTENT", "signal_status.share")
        inp = clean_input()
        inp["report"]["signal_status"]["unit_value"] = "NOT_TRIGGERED"
        self.assert_found(inp, "STATUS_INCONSISTENT", "signal_status.unit_value")

    def test_maintain_and_hold_need_unresolved_evidence(self):
        inp = clean_input()
        inp["case"]["signals"]["share"] = "TRIGGERED"
        inp["report"]["signal_status"] = {"unit_value": "HOLD", "share": "MAINTAIN"}
        inp["report"]["review_status"] = "MAINTAIN"
        self.assert_found(inp, "STATUS_INCONSISTENT", "unresolved_evidence")
        inp["report"]["unresolved_evidence"] = True
        self.assertNotIn("STATUS_INCONSISTENT", [c for c, _ in codes(validate.run(inp))])

    def test_forbidden_phrases(self):
        inp = clean_input()
        inp["report"]["narrative"] += " 우회수입 가능성이 있다."
        inp["report"]["hypotheses"].append("자료 교정 뒤 정상 확정으로 볼 수 있다.")
        inp["report"]["hypotheses"].append("관세법 위반이 의심된다.")
        out = validate.run(inp)
        found = [(f["path"], f["detail"].split("'")[1]) for f in out["findings"] if f["code"] == "FORBIDDEN_PHRASE"]
        self.assertEqual(found, [("narrative", "우회수입"), ("hypotheses[1]", "정상 확정"), ("hypotheses[2]", "관세법 위반")])

    def test_signal_family_requirement(self):
        inp = clean_input()
        inp["report"]["claims"] = [c for c in inp["report"]["claims"] if c["metric"] in ("s", "d_s")]
        inp["report"]["narrative"] = ""
        out = validate.run(inp)
        self.assertIn(("SCHEMA_SIGNAL_CLAIM", "claims"), codes(out))
        self.assertEqual({f["check"] for f in out["findings"] if f["code"] == "SCHEMA_SIGNAL_CLAIM"}, {"schema"})

    def test_schema_problems(self):
        inp = clean_input()
        i = index_of(inp, "c2")
        inp["report"]["claims"][i]["value"] = 3.6  # float
        self.assert_found(inp, "SCHEMA_CLAIM", f"claims[{i}].value")
        inp = clean_input()
        del inp["report"]["claims"][i]["text"]
        self.assert_found(inp, "SCHEMA_CLAIM", f"claims[{i}].fields")
        inp = clean_input()
        inp["report"]["claims"][i]["claim_id"] = "prose:narrative:1"
        self.assert_found(inp, "SCHEMA_CLAIM_ID", f"claims[{i}].claim_id")
        inp = clean_input()
        inp["report"]["confidence"] = "high"
        del inp["report"]["hypotheses"]
        out = validate.run(inp)
        self.assertEqual([c for c, _ in codes(out)].count("SCHEMA_REPORT"), 2)
        self.assertEqual(validate.run({**clean_input(), "report": []})["findings"][0]["code"], "SCHEMA_REPORT")

    def test_report_evidence_list_must_match_claims(self):
        inp = clean_input()
        used = []
        for claim in inp["report"]["claims"]:
            used += [e for e in claim["evidence_ids"] if e not in used]
        inp["report"]["evidence_ids"] = used
        self.assertEqual(validate.run(inp)["findings"], [])
        inp["report"]["evidence_ids"] = used[:-1]
        self.assert_found(inp, "PROVENANCE_REPORT_EVIDENCE", "evidence_ids")


class DataStatusTest(unittest.TestCase):
    def status_input(self, status_row: str, value: str) -> dict:
        inp = clean_input()
        inp["rows"][f"{EV}202"] = {"partner_code": "CN", "hs_code": "850450", "hs_level": 6, "month": "202401",
                                   "flow": "import", "amount_usd": None, "net_weight_kg": None,
                                   "observation_status": status_row}
        inp["envelopes"][1]["missingness"] = [{"evidence_ids": [f"{EV}202"], "observation_status": status_row}]
        claim = {"claim_id": "d1", "claim_type": "data_status", "hs6": "850450", "partner": "CN", "period": "202401",
                 "baseline_period": None, "metric": "observation_status", "value": value, "unit": None,
                 "direction": "NA", "evidence_ids": [f"{EV}202"], "text": ""}
        claim["text"] = r1.status_text(claim, None)
        inp["report"]["claims"].append(claim)
        return inp

    def test_status_claim_backed_by_its_status_row(self):
        self.assertEqual(validate.run(self.status_input("REQUEST_FAILED", "REQUEST_FAILED"))["findings"], [])

    def test_status_claim_with_wrong_status(self):
        inp = self.status_input("REQUEST_FAILED", "NOT_COLLECTED")
        i = index_of(inp, "d1")
        self.assertEqual(codes(validate.run(inp)), [("EVIDENCE_NOT_SUPPORTING", f"claims[{i}].evidence_ids")])

    def test_status_claim_shape(self):
        inp = self.status_input("REQUEST_FAILED", "REQUEST_FAILED")
        i = index_of(inp, "d1")
        inp["report"]["claims"][i]["unit"] = "kg"
        inp["report"]["claims"][i]["direction"] = "DOWN"
        found = codes(validate.run(inp))
        self.assertIn(("UNIT_MISMATCH", f"claims[{i}].unit"), found)
        self.assertIn(("DIRECTION_MISMATCH", f"claims[{i}].direction"), found)
        inp["report"]["claims"][i]["value"] = "MISSING"
        self.assertIn(("SCHEMA_CLAIM", f"claims[{i}].value"), codes(validate.run(inp)))

    def test_observed_status_does_not_fill_signal_family(self):
        case = {"hs6": "850450", "partner": "CN", "month": "202401"}
        claim = {"claim_type": "data_status", "hs6": "850450", "partner": "CN", "period": "202401",
                 "metric": "observation_status", "value": "OBSERVED"}
        self.assertEqual(validate.signal_families(claim, case), set())
        self.assertEqual(validate.signal_families({**claim, "value": "REQUEST_FAILED"}, case), {"unit_value", "share"})
        self.assertEqual(validate.signal_families({**claim, "value": "REQUEST_FAILED", "partner": "ALL"}, case), {"share"})
        self.assertEqual(validate.signal_families({**claim, "value": "REQUEST_FAILED",
                                                   "metric": "observation_status@8504501010"}, case), {"unit_value"})
        self.assertEqual(validate.signal_families({**claim, "claim_type": "value", "metric": "V", "value": 1}, case),
                         set())  # V·Q는 어느 계열 요건도 채우지 않는다(계약 §9.4)


class ValueCompareTest(unittest.TestCase):
    """룰북 B3-1 값 비교와 경계 사례 1~3."""

    def test_rulebook_boundaries(self):
        cases = [(Decimal("20.35"), Decimal("20.345"), "U", True),  # 경계 1: 딱 절반은 사사오입
                 (Decimal("20.34"), Decimal("20.345"), "U", False),
                 (-39, Decimal("-38.7"), "r_U", True),  # 경계 2: 보고값이 계약보다 거칠다
                 (Decimal("20.3412"), Decimal("20.3411"), "U", True),  # 경계 3: 계약보다 자리가 많다
                 (Decimal("20.43"), Decimal("20.3411"), "U", False),  # 예시 2
                 (21876681, 21876681, "V", True),
                 (Decimal("38.6"), Decimal("38.596"), "s", True)]  # 예시 6
        for reported, expected, base, ok in cases:
            with self.subTest(reported=reported):
                self.assertEqual(validate.value_matches(reported, expected, base), ok)


def _claim(cid, ctype, metric, value, unit, direction, period="202401", baseline=None, partner="CN"):
    return {"claim_id": cid, "claim_type": ctype, "hs6": "850450", "partner": partner, "period": period,
            "baseline_period": baseline, "metric": metric, "value": value, "unit": unit, "direction": direction,
            "evidence_ids": [], "text": ""}


CASE_A_CLAIMS = [  # 룰북 B3-2 예시 표의 전제: 합성 사례 A의 typed claim
    _claim("c1", "value", "U", Decimal("6.0"), "USD/kg", "NA", period="202301"),
    _claim("c2", "value", "U", Decimal("3.6"), "USD/kg", "NA"),
    _claim("c3", "change", "r_U", Decimal("-40.0"), "%", "DOWN", baseline="202301"),
    _claim("c4", "share", "s", Decimal("10.0"), "%", "NA", period="202301"),
    _claim("c5", "share", "s", Decimal("6.0"), "%", "NA"),
    _claim("c6", "share_change", "d_s", Decimal("-4.0"), "pp", "DOWN", baseline="202301")]


def rate_claims(*values):
    out = []
    for n, value in enumerate(values):
        v = Decimal(value)
        out.append(_claim(f"x{n}", "change", "r_U", v, "%", "UP" if v > 0 else "DOWN" if v < 0 else "FLAT",
                          baseline="202301"))
    return out


class ProseRuleTest(unittest.TestCase):
    """룰북 B3-2 예시 표 7행과 경계 사례 표를 그대로 옮긴 시험."""

    def setUp(self):
        super().setUp()
        inp = clean_input()
        inp["hs_codes"].append("8504501010")
        self.ctx = validate._context(inp)

    def kinds(self, text, claims):
        found = validate.prose_findings([("narrative", text)], claims, self.ctx)
        return [f["detail"].split(" ")[0] for f in found]

    def test_rulebook_examples(self):
        cases = [("단가가 kg당 6.0달러에서 3.6달러로 40% 떨어졌다.", []),
                 ("점유율이 6%에서 10%로 늘었다.", ["PT-8", "PT-6"]),
                 ("점유율이 4% 줄었다.", ["PT-1"]),
                 ("단가 증가율은 △40.0%였다.", []),
                 ("원자재 가격 상승이 원인일 수 있다.", ["PT-6"]),
                 ("원자재 가격 변동이 영향을 주었는지는 이 자료로 확인할 수 없다.", []),
                 ("2024년 3월 HS 850450 중국산 수입을 조사했다.", [])]
        for text, want in cases:
            with self.subTest(text=text):
                self.assertEqual(self.kinds(text, CASE_A_CLAIMS), want)

    def test_rulebook_boundaries(self):
        v_claim = [_claim("v", "value", "V", 21876681, "USD", "NA")]
        q_claim = [_claim("q", "value", "Q", 1075490, "kg", "NA")]
        d_claim = [_claim("d", "share_change", "d_s", Decimal("-4.0"), "pp", "DOWN", baseline="202301")]
        cases = [("약 40%", rate_claims("-38.7"), []), ("40%", rate_claims("-38.7"), ["PT-1"]),
                 ("30% 넘게 하락", rate_claims("-40.0"), []), ("40%대 하락", rate_claims("-43.2"), []),
                 ("2배 증가", rate_claims("100.0"), []), ("2배 증가", rate_claims("200.0"), ["PT-4"]),
                 ("2배", rate_claims("98.7"), []), ("절반으로 줄었다", rate_claims("-50.0"), []),
                 ("절반으로 줄었다", rate_claims("-47.0"), []), ("절반으로 줄었다", rate_claims("-44.0"), ["PT-4"]),
                 ("탐지 임계값 30%를 넘는 하락", rate_claims("-40.0"), []),
                 ("증가하지 않았다", rate_claims("-40.0"), []), ("증가하지 않았다", rate_claims("40.0"), ["PT-6"]),
                 ("결론을 내렸다. 판정을 내렸다. 영향을 줄 수 있다. 늘 그렇듯 줄곧 오늘 한 줄 요약, 오른쪽, 확대 해석", [], []),
                 ("단가가 내렸다", rate_claims("-40.0"), []), ("하락률 40%", rate_claims("-40.0"), []),
                 ("2,188만 달러", v_claim, []), ("USD 21.9백만", v_claim, []), ("1,075톤", q_claim, []),
                 ("비교국 5개국 중 4개국에서 하락", rate_claims("-40.0"), ["PT-5", "PT-5"]),
                 ("3개월 연속 하락", rate_claims("-40.0"), ["PT-5"]),
                 ("36개월 중 최저, 최소 금액 기준 아래 거래", [], []),
                 ("8504.50-1010 품목, 제85류, HS85, HS22 기준 BACI", [], []),
                 ("검토 유지", [], []), ("−40%", rate_claims("-40.0"), []), ("△40%", rate_claims("40.0"), ["PT-1"]),
                 ("40% 하락", rate_claims("-40.0"), []), ("△4.0%p", d_claim, []),
                 ("40%", rate_claims("-40.0", "12.0"), []),
                 ("policy_v1·RB-1·g1·kcs_202201_202412_v2 기준, 도구를 5회 불렀다, 신호 2개, 1분기", [], [])]
        for text, claims, want in cases:
            with self.subTest(text=text):
                self.assertEqual(self.kinds(text, claims), want)

    def test_list_numbers_are_excluded(self):
        self.assertEqual(self.kinds("1. 단가 확인\n2) 점유율 확인", []), [])


class TemplateConsistencyTest(unittest.TestCase):
    """R1 문장 틀은 산문 검사에서 사유가 0건이다(틀 채우기 모드의 기본 경로)."""

    def test_every_template_sentence_is_backed_by_its_claim(self):
        ctx = validate._context(clean_input())
        values = {"V": [21876681, 0], "Q": [1075490], "U": [Decimal("1234.567"), Decimal("3.6")],
                  "U@8504501010": [Decimal("20.345")], "w@8504501010": [Decimal("20")],
                  "r_U": [Decimal("12.34"), Decimal("-38.75"), Decimal("0.04")],
                  "r_U@8504501010": [Decimal("-5.55")], "s": [Decimal("38.596")],
                  "d_s": [Decimal("4.44"), Decimal("-4.0"), Decimal("-0.04")],
                  "within_effect": [Decimal("0"), Decimal("1.234")], "mix_effect": [Decimal("-2.4")],
                  "residual": [Decimal("-0.001")]}
        for symbol, samples in values.items():
            for value in samples:
                for partner in ("CN", "ALL", "JP"):
                    with self.subTest(symbol=symbol, value=value, partner=partner):
                        base = r1.base_symbol(symbol)
                        baseline = "202301" if base in r1.CHANGE_BASES else None
                        metric = {"metric_id": "m", "inputs": {"metric": symbol, "hs6": "850450", "partner": partner,
                                                               "period": "202401", "baseline_period": baseline},
                                  "evidence_ids": [f"{EV}1"], "value": value, "unit": r1.UNIT_OF[base]}
                        claim = r1.claim_from_metric("c1", metric, "CN")
                        found = validate.prose_findings([("claims[0].text", claim["text"])], [claim], ctx)
                        self.assertEqual(found, [], claim["text"])
        for code in r1.OBSERVATION_STATUSES:
            for hs10 in (None, "8504501010"):
                status = {"hs6": "850450", "partner": "ALL", "period": "202401", "hs10": hs10,
                          "observation_status": code, "evidence_ids": [f"{EV}1"]}
                claim = r1.claim_from_status("c1", status)
                self.assertEqual(validate.prose_findings([("t", claim["text"])], [claim], ctx), [], claim["text"])


class InputErrorTest(unittest.TestCase):
    def test_bad_context_raises(self):
        base = clean_input()
        bad_cases = [None, {**base, "case": {}}, {**base, "run": {**base["run"], "mode": "draft"}},
                     {**base, "envelopes": {}}, {**base, "rows": []},
                     {**base, "case": {**base["case"], "signals": {"unit_value": "TRIGGERED"}}}]
        for bad in bad_cases:
            with self.subTest(bad=type(bad).__name__):
                with self.assertRaises(ValueError):
                    validate.run(bad)


if __name__ == "__main__":
    unittest.main()


class NonFiniteTest(unittest.TestCase):
    def test_nan_in_claim_or_metric_does_not_crash(self):
        inp = clean_input()
        i = index_of(inp, "c6")
        inp["report"]["claims"][i]["value"] = Decimal("NaN")
        self.assertIn(("SCHEMA_CLAIM", f"claims[{i}].value"), codes(validate.run(inp)))
        inp = clean_input()
        for envelope in inp["envelopes"]:
            for metric in envelope["metrics"]:
                if metric["metric_id"] == "m-res":
                    metric["value"] = Decimal("NaN")
        self.assertIn(("NUMERIC_UNBACKED", f"claims[{index_of(inp, 'c6')}].value"), codes(validate.run(inp)))
