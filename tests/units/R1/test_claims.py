"""단위 R1(reports_claims) 규칙 시험. 골든 쌍 밖의 경우를 본다.

- freeform은 모델이 쓴 주장을 고치지 않고 그대로 돌려준다(개발 플랜 §7.3, 자료 계약 §6.3).
- 틀 채우기 모드 셋(checklist·agent·full)은 같은 요청에 같은 주장을 낸다.
- 입력을 바꾸지 않는다. 표시 자릿수 반올림은 Decimal ROUND_HALF_UP이다(자료 계약 §11.3, 룰북 B3-1 경계 1).
시험 값은 모두 합성이다(실제 통계가 아니다).
"""
import copy
import json
import unittest
from decimal import Decimal
from pathlib import Path

from tradesentry.reports import claims

HERE = Path(__file__).resolve().parent
CASE = {"case_id": "A-composition", "hs6": "850450", "partner": "CN", "month": "202401", "baseline_month": "202301",
        "signals": {"unit_value": "TRIGGERED", "share": "NOT_TRIGGERED"}, "snapshot_id": "controlled_fixture_v0",
        "policy_version": "dev-0.1"}
EV = "ev:controlled_fixture_v0:observation:"


def metric(metric_id, symbol, value, unit, *, partner="CN", period="202401", baseline=None, evidence=(1,)):
    inputs = {"metric": symbol, "hs6": "850450", "partner": partner, "period": period, "baseline_period": baseline}
    return {"metric_id": metric_id, "formula_version": "f1", "inputs": inputs,
            "evidence_ids": [f"{EV}{n}" for n in evidence], "value": value, "unit": unit,
            "comparability_flags": [], "tolerance": None}


def fill_one(m):
    out = claims.run({"mode": "full", "case": CASE, "metrics": [m], "statuses": [],
                      "requests": [{"claim_id": "c1", "metric_id": m["metric_id"]}]})
    return out


def golden_input():
    return json.loads((HERE / "input.json").read_text(encoding="utf-8"), parse_float=Decimal)


class FreeformTest(unittest.TestCase):
    def test_model_claims_pass_through_unchanged(self):
        wrong = {"claim_id": "c1", "claim_type": "change", "hs6": "850450", "partner": "CN", "period": "202401",
                 "baseline_period": "202301", "metric": "r_U", "value": Decimal("40.0"), "unit": "USD",
                 "direction": "UP", "evidence_ids": [], "text": "단가가 40% 올랐다."}
        inp = {"mode": "freeform", "case": CASE, "claims": [wrong]}
        out = claims.run(inp)
        self.assertEqual(out, {"claims": [wrong], "rejected": []})  # 틀린 값·단위·방향을 고치지 않는다
        self.assertIsNot(out["claims"][0], wrong)  # 돌려준 목록을 고쳐도 입력은 그대로다

    def test_freeform_ignores_requests(self):
        out = claims.run({"mode": "freeform", "case": CASE, "claims": [],
                          "metrics": [metric("m1", "U", Decimal("3.6"), "USD/kg")],
                          "requests": [{"claim_id": "c1", "metric_id": "m1"}]})
        self.assertEqual(out, {"claims": [], "rejected": []})


class TemplateTest(unittest.TestCase):
    def test_three_template_modes_fill_the_same_claims(self):
        base = golden_input()
        outputs = []
        for mode in claims.TEMPLATE_MODES:
            inp = copy.deepcopy(base)
            inp["mode"] = mode
            outputs.append(claims.run(inp))
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[0], outputs[2])

    def test_input_is_not_changed(self):
        inp = golden_input()
        before = copy.deepcopy(inp)
        out = claims.run(inp)
        self.assertEqual(inp, before)
        out["claims"][0]["evidence_ids"].append("x")  # 출력의 목록은 입력과 따로다
        self.assertEqual(inp, before)

    def test_claims_have_exactly_the_contract_fields(self):
        for claim in claims.run(golden_input())["claims"]:
            self.assertEqual(tuple(claim), claims.CLAIM_FIELDS)

    def test_half_up_rounding_reads_decimal_text(self):
        # 룰북 B3-1 경계 1: 4,069 USD / 200 kg = 20.345는 정확히 절반이다. Decimal로 읽으면 20.35다.
        self.assertEqual(str(fill_one(metric("m1", "U", Decimal("20.345"), "USD/kg"))["claims"][0]["value"]), "20.35")
        self.assertEqual(str(claims.display_value("r_U", Decimal("-38.75"))), "-38.8")
        self.assertEqual(str(claims.display_value("U", Decimal("20.3411"))), "20.34")
        self.assertEqual(claims.display_value("V", Decimal("21876681.5")), 21876682)

    def test_negative_zero_is_written_as_zero(self):
        out = fill_one(metric("m1", "r_U", Decimal("-0.04"), "%", baseline="202301"))["claims"][0]
        self.assertEqual(str(out["value"]), "0.0")
        self.assertEqual(out["direction"], "FLAT")
        self.assertIn("변화가 없다(0.0%)", out["text"])

    def test_direction_follows_the_shown_value(self):
        cases = [(Decimal("12.34"), "UP", "12.3% 높다"), (Decimal("-12.34"), "DOWN", "12.3% 낮다"),
                 (Decimal("0.04"), "FLAT", "변화가 없다(0.0%)")]
        for value, direction, phrase in cases:
            with self.subTest(value=value):
                out = fill_one(metric("m1", "r_U", value, "%", baseline="202301"))["claims"][0]
                self.assertEqual(out["direction"], direction)
                self.assertIn(phrase, out["text"])

    def test_float_is_rejected_not_converted(self):
        out = fill_one(metric("m1", "U", 3.6, "USD/kg"))
        self.assertEqual(out["claims"], [])
        self.assertIn("float", out["rejected"][0]["reason"])

    def test_undefined_symbols_are_rejected(self):
        for symbol, unit in (("within_effect@8504501010", "USD/kg"), ("w", "%"), ("price", "USD/kg"),
                             ("U@", "USD/kg"), ("U@1@2", "USD/kg")):
            with self.subTest(symbol=symbol):
                out = fill_one(metric("m1", symbol, Decimal("1.0"), unit, baseline="202301"))
                self.assertEqual(out["claims"], [])
                self.assertEqual(out["rejected"][0]["reason"], "지표 기호가 계약 §11.2에 없다")

    def test_sub_item_weight_share(self):
        out = fill_one(metric("m1", "w@8504501010", Decimal("20"), "%"))["claims"][0]
        self.assertEqual((out["claim_type"], str(out["value"]), out["unit"], out["direction"]),
                         ("value", "20.0", "%", "NA"))
        self.assertEqual(out["text"], "2024년 1월 하위품목 HS 8504501010의 중량 비중은 20.0%다.")

    def test_change_metric_needs_baseline(self):
        out = fill_one(metric("m1", "mix_effect", Decimal("-2.4"), "USD/kg"))
        self.assertEqual(out["rejected"][0]["reason"], "변화 지표에 기준월(baseline_period)이 없다")

    def test_decomposition_text_keeps_the_sign(self):
        out = fill_one(metric("m1", "mix_effect", Decimal("-2.4"), "USD/kg", baseline="202301"))["claims"][0]
        self.assertEqual((out["claim_type"], out["direction"]), ("decomposition", "DOWN"))
        self.assertEqual(out["text"], "2024년 1월 단가 변화 가운데 구성 변화 효과는 kg당 -2.40달러다.")

    def test_metric_without_evidence_is_rejected(self):
        out = fill_one(metric("m1", "U", Decimal("3.6"), "USD/kg", evidence=()))
        self.assertEqual(out["rejected"][0]["reason"], "근거 ID가 없는 지표다")

    def test_status_code_must_be_a_contract_value(self):
        status = {"status_id": "s1", "hs6": "850450", "partner": "ALL", "period": "202401", "hs10": "8504501010",
                  "observation_status": "MISSING", "evidence_ids": [f"{EV}9"]}
        out = claims.run({"mode": "full", "case": CASE, "metrics": [], "statuses": [status],
                          "requests": [{"claim_id": "c1", "status_id": "s1"}]})
        self.assertEqual(out["rejected"][0]["reason"], "관측 상태 코드가 계약 §3.4의 다섯 값이 아니다")
        status["observation_status"] = "NOT_COLLECTED"
        out = claims.run({"mode": "full", "case": CASE, "metrics": [], "statuses": [status],
                          "requests": [{"claim_id": "c1", "status_id": "s1"}]})
        claim = out["claims"][0]
        self.assertEqual((claim["metric"], claim["value"], claim["unit"]),
                         ("observation_status@8504501010", "NOT_COLLECTED", None))
        self.assertEqual(claim["text"], "2024년 1월 전체국가 하위품목 HS 8504501010 자료 상태는 NOT_COLLECTED(미수집)다.")

    def test_bad_inputs_raise(self):
        for bad in (None, [], {"mode": "draft", "case": CASE}, {"mode": "full"}, {"mode": "full", "case": {}},
                    {"mode": "freeform", "case": CASE, "claims": {}},
                    {"mode": "full", "case": CASE, "requests": {}}):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    claims.run(bad)


if __name__ == "__main__":
    unittest.main()
