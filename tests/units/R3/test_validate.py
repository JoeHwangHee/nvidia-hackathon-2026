"""단위 R3(validator_validate) 규칙 시험. 골든 쌍 밖의 경우를 본다.

- 깨끗한 보고서: 단위 R1이 검증된 지표로 채운 full 보고서는 사유가 0건이다.
- 변조 시험(로드맵 §3 MVP 체크리스트 3번): 숫자·단위·근거 ID·스냅샷 변조와 뒷받침 없는 산문 숫자·증감을 잡는다.
  막을지(모드별)는 단위 R4 시험(tests/units/R4)이 R3과 함께 본다.
- 산문 규칙: 룰북 B3-2의 예시 표와 경계 사례 표, R1 문장 틀의 자기 일관성(틀 문장은 산문 사유가 0건이다).
- 값 비교: 룰북 B3-1 경계 사례. 입력을 바꾸지 않는다.
시험 값은 모두 합성이다(실제 통계가 아니다). 합성 사례 A/B/C는 실제 사건이 아니다.
"""
import copy
import hashlib
import json
import unittest
from decimal import Decimal
from pathlib import Path

from tradesentry.reports import claims as r1
from tradesentry.reports import render_ko
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
        self.assertEqual(found, [("narrative", "우회 수입"), ("hypotheses[1]", "정상 확정"), ("hypotheses[2]", "관세법 위반")])

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


def c_type_input() -> dict:
    """oracle C형 보고서: 하위품목(HS10) 자료에서 나온 주장(분해 효과·w@)을 빼고 부모 HS6 값 주장만 남긴 깨끗한 보고서."""
    inp = clean_input()
    inp["report"]["claims"] = [c for c in inp["report"]["claims"]
                               if "@" not in c["metric"] and c["metric"] not in validate.DECOMPOSITION]
    inp["report"]["narrative"] = ("단가가 kg당 6.00달러에서 3.60달러로 40.0% 낮아졌다. 하위품목 조회가 실패해 "
                                  "구성 변화 효과를 계산하지 못했다.")
    return inp


def add_status(inp: dict, claim_id: str, metric: str, value: str, rows: dict, period: str = "202401",
               partner: str = "CN") -> int:
    """자료 상태 주장 하나와 그 근거 행을 더한다. 근거 행은 봉투 missingness로 돌려준 것으로 둔다."""
    evidence = []
    for rowid, (row_partner, hs_code, month, status) in rows.items():
        evidence_id = f"{EV}{rowid}"
        inp["rows"][evidence_id] = {"partner_code": row_partner, "hs_code": hs_code, "hs_level": len(hs_code),
                                    "month": month, "flow": "import", "amount_usd": None, "net_weight_kg": None,
                                    "observation_status": status}
        inp["envelopes"][1]["missingness"].append({"evidence_ids": [evidence_id], "observation_status": status})
        evidence.append(evidence_id)
    claim = {"claim_id": claim_id, "claim_type": "data_status", "hs6": "850450", "partner": partner,
             "period": period, "baseline_period": None, "metric": metric, "value": value, "unit": None,
             "direction": "NA", "evidence_ids": evidence, "text": ""}
    claim["text"] = r1.status_text(claim, metric.partition("@")[2] or None)
    inp["report"]["claims"].append(claim)
    return len(inp["report"]["claims"]) - 1


class DataStatusTest(unittest.TestCase):
    """자료 상태 주장의 근거(무역통계 검토 지적 1). 상태 행은 요청 코드 자릿수로 기록되므로(수집기), 자료 상태 주장은
    그 키 자신의 행이나 그 키를 맡은 요청의 상태 행을 인용한다. 부모 HS6 행이 있는 키의 HS6 요청 상태 행은 HS10 하위
    자료의 상태다(자료 계약 §2.3.2 행 규칙 4). 행 202·203 등은 합성이다."""

    def test_c_type_sub_item_status_backed_by_hs6_request_row(self):
        # 확인 P2: C형은 observation_status@<HS10>이고 HS6 요청(850450)의 상태 행으로 뒷받침된다.
        inp = c_type_input()
        add_status(inp, "d1", "observation_status@8504501010", "REQUEST_FAILED",
                   {202: ("CN", "850450", "202401", "REQUEST_FAILED")})
        self.assertEqual(validate.run(inp)["findings"], [])

    def test_hs6_level_status_is_refused_when_parent_row_exists(self):
        # 확인 P5: 부모 HS6 행(201, OBSERVED)이 있는 키를 HS6 수준 REQUEST_FAILED로 적으면 막는다.
        inp = c_type_input()
        i = add_status(inp, "d1", "observation_status", "REQUEST_FAILED",
                       {202: ("CN", "850450", "202401", "REQUEST_FAILED")})
        found = codes(validate.run(inp))
        self.assertIn(("EVIDENCE_NOT_SUPPORTING", f"claims[{i}].evidence_ids"), found)
        self.assertIn(("DATA_STATUS_CONFLICT", f"claims[{i}].value"), found)  # 같은 키의 단가 주장과 어긋난다

    def test_hs6_level_status_without_parent_row(self):
        # 부모 HS6 행이 없는 달(v2 빈 응답 208개월의 꼴)은 HS6 요청 상태 행과 HS4 스캔 상태 행(확인 P1)이 모두 근거다.
        for rowid, hs_code in ((203, "850450"), (204, "8504")):
            with self.subTest(hs_code=hs_code):
                inp = c_type_input()
                add_status(inp, "d1", "observation_status", "UNRESOLVED_ZERO",
                           {rowid: ("CN", hs_code, "202402", "UNRESOLVED_ZERO")}, period="202402")
                self.assertEqual(validate.run(inp)["findings"], [])

    def test_child_row_does_not_support_parent_status(self):
        # 확인 P4: 하위 HS10 행으로 상위(HS6) 키의 상태를 뒷받침하지 못한다.
        inp = c_type_input()
        i = add_status(inp, "d1", "observation_status", "REQUEST_FAILED",
                       {205: ("CN", "8504501010", "202402", "REQUEST_FAILED")}, period="202402")
        self.assertEqual(codes(validate.run(inp)), [("EVIDENCE_NOT_SUPPORTING", f"claims[{i}].evidence_ids")])

    def test_country_sub_item_key_is_not_covered_by_hs4_scan(self):
        # 상대국 HS10 키를 맡은 요청은 HS6 요청이다(국가별 API의 HS4 스캔은 HS6 행을 준다). ALL은 HS4 요청도 맡는다.
        inp = c_type_input()
        i = add_status(inp, "d1", "observation_status@8504501010", "REQUEST_FAILED",
                       {206: ("CN", "8504", "202402", "REQUEST_FAILED")}, period="202402")
        self.assertEqual(codes(validate.run(inp)), [("EVIDENCE_NOT_SUPPORTING", f"claims[{i}].evidence_ids")])
        inp = c_type_input()
        add_status(inp, "d1", "observation_status@8504501010", "REQUEST_FAILED",
                   {207: ("ALL", "8504", "202402", "REQUEST_FAILED")}, period="202402", partner="ALL")
        self.assertEqual(validate.run(inp)["findings"], [])

    def test_observed_status_needs_the_row_of_the_same_code(self):
        inp = c_type_input()
        i = add_status(inp, "d1", "observation_status@8504501010", "OBSERVED", {})
        inp["report"]["claims"][i]["evidence_ids"] = [f"{EV}201"]  # 부모 HS6 행은 HS10 키의 관측을 보이지 않는다
        self.assertEqual(codes(validate.run(inp)), [("EVIDENCE_NOT_SUPPORTING", f"claims[{i}].evidence_ids")])
        inp["report"]["claims"][i]["evidence_ids"] = [f"{EV}211"]  # 그 HS10 행
        self.assertEqual(validate.run(inp)["findings"], [])

    def test_opposite_status_claims_do_not_pass_together(self):
        # 같은 대상의 자료 상태 주장 둘이 각자 근거를 인용해도 값이 다르면 둘 다 막는다.
        inp = c_type_input()
        add_status(inp, "d1", "observation_status@8504501010", "REQUEST_FAILED",
                   {208: ("CN", "850450", "202402", "REQUEST_FAILED")}, period="202402")
        add_status(inp, "d2", "observation_status@8504501010", "OBSERVED",
                   {209: ("CN", "8504501010", "202402", "OBSERVED")}, period="202402")
        conflicts = [f["claim_id"] for f in validate.run(inp)["findings"] if f["code"] == "DATA_STATUS_CONFLICT"]
        self.assertEqual(conflicts, ["d1", "d2"])

    def test_sub_item_status_conflicts_with_values_of_that_sub_item(self):
        # 사례 A(하위품목 자료가 있음)에 C형 상태 주장을 더하면 분해 효과·중량 비중 주장과 어긋난다.
        inp = clean_input()
        i = add_status(inp, "d1", "observation_status@8504501010", "REQUEST_FAILED",
                       {202: ("CN", "850450", "202401", "REQUEST_FAILED")})
        self.assertEqual(codes(validate.run(inp)), [("DATA_STATUS_CONFLICT", f"claims[{i}].value")])

    def test_confirmed_no_trade_allows_zero_values(self):
        status = {"claim_id": "d1", "claim_type": "data_status", "hs6": "850450", "partner": "CN", "period": "202402",
                  "baseline_period": None, "metric": "observation_status", "value": "CONFIRMED_NO_TRADE"}
        zero_v = {"claim_id": "v1", "claim_type": "value", "hs6": "850450", "partner": "CN", "period": "202402",
                  "baseline_period": None, "metric": "V", "value": 0}
        unit_value = {**zero_v, "claim_id": "u1", "metric": "U", "value": Decimal("1.00")}
        self.assertEqual(validate._data_status_conflicts([(0, status), (1, zero_v)]), [])
        found = validate._data_status_conflicts([(0, status), (1, unit_value)])
        self.assertEqual([f["code"] for f in found], ["DATA_STATUS_CONFLICT"])
        unresolved = {**status, "value": "UNRESOLVED_ZERO"}  # 빈 응답은 0이 아니므로 V 0도 어긋난다
        self.assertEqual(len(validate._data_status_conflicts([(0, unresolved), (1, zero_v)])), 1)
        sub = {**status, "metric": "observation_status@8504501010"}  # 무거래 확정 하위품목: w@ 0은 되고 U@는 안 된다
        zero_w = {**zero_v, "claim_id": "w1", "metric": "w@8504501010", "value": Decimal("0.0")}
        sub_u = {**zero_v, "claim_id": "u2", "metric": "U@8504501010", "value": Decimal("1.00")}
        self.assertEqual(validate._data_status_conflicts([(0, sub), (1, zero_w)]), [])
        self.assertEqual(len(validate._data_status_conflicts([(0, sub), (1, sub_u)])), 1)

    def test_status_claim_shape(self):
        inp = c_type_input()
        i = add_status(inp, "d1", "observation_status@8504501010", "REQUEST_FAILED",
                       {202: ("CN", "850450", "202401", "REQUEST_FAILED")})
        inp["report"]["claims"][i]["unit"] = "kg"
        inp["report"]["claims"][i]["direction"] = "DOWN"
        found = codes(validate.run(inp))
        self.assertIn(("UNIT_MISMATCH", f"claims[{i}].unit"), found)
        self.assertIn(("DIRECTION_MISMATCH", f"claims[{i}].direction"), found)
        inp["report"]["claims"][i]["value"] = "MISSING"
        self.assertIn(("SCHEMA_CLAIM", f"claims[{i}].value"), codes(validate.run(inp)))

    def test_sub_item_code_format_and_parent(self):
        # 무역통계 검토 권고 5: HS10 코드는 숫자 10자이고 주장의 hs6로 시작한다(계약 §6.2).
        for metric in ("observation_status@12345", "observation_status@8504311010"):
            with self.subTest(metric=metric):
                inp = c_type_input()
                i = add_status(inp, "d1", metric, "REQUEST_FAILED", {202: ("CN", "850450", "202401", "REQUEST_FAILED")})
                self.assertEqual(codes(validate.run(inp)), [("REFERENT_MISMATCH", f"claims[{i}].metric")])
        inp = clean_input()
        i = index_of(inp, "c7")  # w@8504501010(2023년 1월)
        inp["report"]["claims"][i]["metric"] = "w@8504311010"
        self.assertIn(("REFERENT_MISMATCH", f"claims[{i}].metric"), codes(validate.run(inp)))

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


class ReportHashTest(unittest.TestCase):
    """Codex 지적 1: report_hash가 있으면 형식과, 계약 §9.1로 다시 계산한 값과의 일치를 본다(스키마 사유)."""

    def hashed_input(self) -> dict:
        inp = clean_input()
        draft = inp["report"]
        built = render_ko.run({**{k: draft[k] for k in ("report_id", "run_id", "mode", "created_at", "policy_version",
                                                        "snapshot_id", "grouping_version", "claims", "narrative",
                                                        "hypotheses", "review_status", "signal_status",
                                                        "unresolved_evidence")},
                               "case": inp["case"], "validator_findings": []})
        inp["report"] = built["report"]
        return inp

    def hash_findings(self, inp: dict) -> list[dict]:
        return [f for f in validate.run(inp)["findings"] if f["code"] == "SCHEMA_REPORT_HASH"]

    def test_report_built_by_r2_passes(self):
        self.assertEqual(validate.run(self.hashed_input())["findings"], [])

    def test_draft_without_hash_skips_the_check(self):
        self.assertEqual(self.hash_findings(clean_input()), [])

    def test_content_changed_after_hashing_is_blocked(self):
        tampers = {
            "narrative": lambda r: r.update(narrative=r["narrative"] + " 추가 문장."),
            "claims": lambda r: r["claims"][0].update(text=r["claims"][0]["text"] + " "),
            "hypotheses": lambda r: r["hypotheses"].append("새 가설."),
            "evidence_ids": lambda r: r["evidence_ids"].reverse(),
        }
        for name, tamper in tampers.items():
            with self.subTest(tamper=name):
                inp = self.hashed_input()
                tamper(inp["report"])
                found = self.hash_findings(inp)
                self.assertEqual([(f["check"], f["path"]) for f in found], [("schema", "report_hash")])

    def test_hash_format_is_checked(self):
        for bad in ("A" * 64, "a" * 63, "g" * 64, 12, None):
            with self.subTest(bad=bad):
                inp = self.hashed_input()
                inp["report"]["report_hash"] = bad
                self.assertEqual(len(self.hash_findings(inp)), 1)

    def test_forged_hash_of_other_content_is_blocked(self):
        inp = self.hashed_input()
        inp["report"]["report_hash"] = hashlib.sha256(b"other").hexdigest()
        self.assertEqual(len(self.hash_findings(inp)), 1)

    def test_hash_without_evidence_list_uses_claim_evidence(self):
        inp = self.hashed_input()
        del inp["report"]["evidence_ids"]  # R2와 같게 주장들의 근거를 모아 다시 계산한다
        self.assertEqual(self.hash_findings(inp), [])

    def test_unhashable_content_is_blocked(self):
        inp = self.hashed_input()
        inp["report"]["claims"][0]["value"] = Decimal("NaN")
        self.assertEqual(len(self.hash_findings(inp)), 1)


class ForbiddenPhraseTest(unittest.TestCase):
    """무역통계 검토 지적 2·권고 3: 자료 계약 §6.3 범주별 표현, 통관 조치, 오탐."""

    def test_contract_categories_are_caught(self):
        cases = {  # 문장 → 잡혀야 할 문구
            "부정 가능성이 있다.": ["부정 가능성"],
            "부정 의혹이 있다.": ["부정 의혹"],
            "부정 여부는 판단하지 않는다.": ["부정 여부"],
            "부정가능성을 배제할 수 없다.": ["부정 가능성"],
            "위법 소지가 있다.": ["위법"],
            "제3국을 거쳐 원산지를 바꿔 들여왔을 수 있다.": ["원산지를 바꿔", "제3국을 거쳐"],
            "우회수입일 수 있다.": ["우회 수입"],
            "개별 거래가격이 낮아졌다.": ["개별 거래가격"],
            "관세 포탈 가능성이 있다.": ["관세 포탈"],
            "관세포탈이 의심된다.": ["관세 포탈"],
            "화물 환적이 늘었을 수 있다.": ["환적"],
            "통관 보류와 추징이 필요하다.": ["통관 보류", "추징"],
            "원산지 판정이 필요하다.": ["원산지 판정"],
            "정상 거래일 수 있다.": ["정상 거래"],
            "under-invoicing or transshipment": ["under-invoic", "transship"],
        }
        for text, want in cases.items():
            with self.subTest(text=text):
                self.assertEqual(sorted(validate.forbidden_hits(text)), sorted(want))

    def test_false_positives_are_not_caught(self):
        for text in ("반덤핑 관세 부과가 끝난 뒤 수입선이 바뀌었을 수 있다.", "덤핑방지관세 부과 기간이다.",
                     "부정적 영향이 있다.", "부정할 수 없다.", "순환적 요인일 수 있다.", "교환적 관계다.",
                     "재고 발생이 늘었다.", "정밀 수치를 확인했다.", "자료 보류를 제안한다.", "수입선 전환이 있었다.",
                     "anti-dumping duty ended"):
            with self.subTest(text=text):
                self.assertEqual(validate.forbidden_hits(text), [])

    def test_list_shape_for_prompt_sync(self):
        # MT4의 프롬프트 동기화 시험은 두 목록을 문자열로 읽는다(목록 모양을 바꾸지 않는다).
        self.assertTrue(all(isinstance(p, str) and p for p in validate.FORBIDDEN_PHRASES))
        self.assertTrue(all(isinstance(p, str) and p == p.lower() for p in validate.FORBIDDEN_LATIN))
        self.assertEqual(len(set(validate.FORBIDDEN_PHRASES)), len(validate.FORBIDDEN_PHRASES))


class ProseFalsePositiveTest(unittest.TestCase):
    """무역통계 검토 권고 4: 품목 규격·분류 자릿수·기준월 표기는 산문 숫자로 잡지 않는다(룰북 EX 표 밖의 해석)."""

    def test_specs_digit_levels_and_baseline_notation(self):
        inp = clean_input()
        inp["hs_codes"] += ["850431", "850432"]  # 스냅샷 HS 코드 집합(EX-2)
        ctx = validate._context(inp)
        for text in ("850431 변압기 1kVA 이하와 850432 변압기 1kVA 초과 16kVA 이하를 함께 봤다.",
                     "HSK 10단위 품목과 6자리 품목을 비교했다.", "기준월은 t−12, 비교월은 t다.", "기준월 t-12"):
            with self.subTest(text=text):
                self.assertEqual(validate.prose_findings([("narrative", text)], [], ctx), [])


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


class ScorerAlignmentTest(unittest.TestCase):
    """검증기 산문 규칙을 채점기(eval/scorer/prose.py, 룰북 B3-2 "둘이 어긋나면 채점기 판정이 기준")에 맞춘 항목별
    시험(결정 기록 2026-09-26(토) model-decision-validator-prose-alignment). 항목마다 빼야 하는 문장이 통과하고 막아야
    하는 문장이 PROSE_UNBACKED로 막히는 양쪽을 본다. 예문은 규칙 대조 보고서의 실측 예다. 값은 합성이다."""

    V_CLAIM = [_claim("v", "value", "V", 21876681, "USD", "NA")]
    Q_CLAIM = [_claim("q", "value", "Q", 1075490, "kg", "NA")]
    D_CLAIM = [_claim("d", "share_change", "d_s", Decimal("-4.0"), "pp", "DOWN", baseline="202301")]

    def setUp(self):
        super().setUp()
        inp = clean_input()
        inp["hs_codes"].append("8504501010")
        self.ctx = validate._context(inp)

    def kinds(self, text, claims):
        found = validate.prose_findings([("narrative", text)], claims, self.ctx)
        self.assertTrue(all(f["code"] == "PROSE_UNBACKED" for f in found))
        return [f["detail"].split(" ")[0] for f in found]

    def test_1_ordinal_je_n_is_excluded(self):
        # #1 EX-4 "제N": 제2-1안·제3국의 숫자는 순번이라 뺀다(채점기 `제\s*+\d++(-\d+)*`). 개수 "3개국"은 그대로 PT-5다.
        self.assertEqual(self.kinds("제2-1안을 택했다. 제3국을 통한 수입 여부는 보지 않는다.", []), [])
        self.assertEqual(self.kinds("제 3 국가와 비교했다.", []), [])
        self.assertEqual(self.kinds("3개국과 비교했다.", []), ["PT-5"])

    def test_2_weeks_period_is_excluded(self):
        # #2 EX-1 "N주": 기간 표현이라 뺀다. "N일"·"N주"에 "연속"이 뒤따르면 빼지 않는다(#11).
        self.assertEqual(self.kinds("2주 동안 하락했다.", rate_claims("-40.0")), [])
        self.assertEqual(self.kinds("2주 연속 하락했다.", rate_claims("-40.0")), ["PT-5"])

    def test_3_per_kg_quantity_is_excluded(self):
        # #3 "1kg당": 단위 기준 수량 1kg은 빼고, 뒤의 단가만 U claim과 비교한다(채점기 `\d+(kg|킬로그램|톤)당`).
        self.assertEqual(self.kinds("1kg당 3.6달러다.", CASE_A_CLAIMS), [])
        self.assertEqual(self.kinds("1kg당 3.7달러다.", CASE_A_CLAIMS), ["PT-3"])
        self.assertEqual(self.kinds("1 킬로그램당 3.6달러다.", CASE_A_CLAIMS), [])

    def test_4_multiple_with_inequality(self):
        # #4 배수 부등식 "2배 이상": 비율 k = 1 + r_U/100에 부등식을 적용한다(채점기 `op`). r_U +150은 비율 2.5 ≥ 2다.
        self.assertEqual(self.kinds("2배 이상 증가", rate_claims("150.0")), [])
        self.assertEqual(self.kinds("2배 이상 증가", rate_claims("80.0")), ["PT-4"])  # 비율 1.8 < 2
        self.assertEqual(self.kinds("2배 이하로 증가", rate_claims("80.0")), [])
        self.assertEqual(self.kinds("2배 증가", rate_claims("150.0")), ["PT-4"])  # 부등식이 없으면 반올림 등가(2.5 → 3)

    def test_5_space_between_number_and_multiplier(self):
        # #5 배수·금액 사이 공백 "21.9 백만 달러": 배수를 읽어 V claim과 맞춘다(채점기 `\s*+`).
        self.assertEqual(self.kinds("21.9 백만 달러였다.", self.V_CLAIM), [])
        self.assertEqual(self.kinds("21.9 백만 달러였다.", self.Q_CLAIM), ["PT-3"])
        self.assertEqual(self.kinds("2,188 만 달러였다.", self.V_CLAIM), [])

    def test_6_usd_per_ton_has_no_compatible_claim(self):
        # #6 "USD/톤"·"달러/톤"·"톤당": 관세청 지표(USD/kg)와 환산하지 않으므로 호환 claim이 없어 막는다(룰북 경계 14).
        for text in ("3.6 USD/톤이다.", "3,600달러/톤이다.", "톤당 3,600달러다.", "톤당 3.6달러다."):
            with self.subTest(text=text):
                self.assertEqual(self.kinds(text, CASE_A_CLAIMS), ["PT-3"])
        self.assertEqual(self.kinds("kg당 3.6달러다. 3.6 USD/kg이다.", CASE_A_CLAIMS), [])

    def test_9_usd_prefix_glued_to_number_is_not_an_identifier(self):
        # #9 EX-3 "USD3.7": 식별자가 아니라 금액이다(채점기 `(?!USD\d)` 가드). 다른 식별자는 그대로 뺀다.
        self.assertEqual(self.kinds("USD3.6이다.", CASE_A_CLAIMS), [])
        self.assertEqual(self.kinds("USD3.7이다.", CASE_A_CLAIMS), ["PT-3"])
        self.assertEqual(self.kinds("policy_v1과 RB-1, kcs_202201_202412_v2 기준", []), [])

    def test_10_negation_with_none_word(self):
        # #10 부정형 "(이|가|은|는)? 없": "증가가 없다"·"증가는 없었다"·"감소 없이"는 반대 방향이나 FLAT claim으로 뒷받침된다.
        for text in ("증가가 없다.", "증가는 없었다.", "증가 없이 유지됐다."):
            with self.subTest(text=text):
                self.assertEqual(self.kinds(text, rate_claims("-40.0")), [])
                self.assertEqual(self.kinds(text, rate_claims("40.0")), ["PT-6"])
        # "지는 않"은 검증기가 이미 잡던 부정형이다(채점기 쪽 보정은 사용자 확인 대기라 이 시험은 검증기 규칙만 본다).
        self.assertEqual(self.kinds("증가하지는 않았다.", rate_claims("-40.0")), [])
        # 그대로(FLAT) 어휘는 부정형을 보지 않는다(채점기와 같다).
        self.assertEqual(self.kinds("변화가 없었다.", rate_claims("0.0")), [])
        self.assertEqual(self.kinds("변화가 없었다.", rate_claims("-40.0")), ["PT-6"])

    def test_11_days_in_a_row_is_not_excluded(self):
        # #11 "N일 연속": EX-1 예외가 아니라 PT-5다(채점기 `(일|주)(?!연속)`). "N일 뒤"는 뺀다.
        self.assertEqual(self.kinds("3일 연속 하락했다.", rate_claims("-40.0")), ["PT-5"])
        self.assertEqual(self.kinds("3일 뒤 하락했다.", rate_claims("-40.0")), [])
        self.assertEqual(self.kinds("2024년 3월 5일 조회", []), [])

    def test_12_uppercase_percent_p_is_not_pp(self):
        # #12 "%P"(대문자): pp로 읽지 않는다. "%"까지가 단위라 −4.0%가 되고 d_s(pp) claim과 호환되지 않아 막는다.
        self.assertEqual(self.kinds("△4.0%P", self.D_CLAIM), ["PT-1"])
        self.assertEqual(self.kinds("△4.0%p", self.D_CLAIM), [])
        self.assertEqual(self.kinds("△4.0%P", CASE_A_CLAIMS), ["PT-1"])  # s 10.0·6.0%와도 값이 다르다


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
                     {**base, "case": {**base["case"], "signals": {"unit_value": "TRIGGERED"}}},
                     # Codex 권고 2: 발동한 신호가 없는 것은 사례가 아니다(개발 플랜 §6.4, 단위 P4·P5와 같다)
                     {**base, "case": {**base["case"], "signals": {"unit_value": "NOT_TRIGGERED",
                                                                   "share": "NOT_TRIGGERED"}}}]
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
