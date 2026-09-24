"""단위 R2(reports_render_ko) 규칙 시험. 골든 쌍 밖의 경우를 본다.

- 보고서 객체는 계약 키 17개다(자료 계약 §9 원문).
- report_hash는 계약 §9.1 정규화 규칙이다. 손으로 쓴 정규화 문자열의 sha256과 대조한다(R2 코드를 쓰지 않는 대조).
- 본문은 처음 표시 "조사 전 경보"를 먼저 적고 조사 뒤 제안을 따로 적는다(계약 §3.1). 금지 어휘를 쓰지 않는다.
시험 값은 모두 합성이다(실제 통계가 아니다).
"""
import copy
import hashlib
import json
import unicodedata
import unittest
from decimal import Decimal
from pathlib import Path

from tradesentry.reports import render_ko

HERE = Path(__file__).resolve().parent
EV = "ev:controlled_fixture_v0:observation:"


def golden_input():
    return json.loads((HERE / "input.json").read_text(encoding="utf-8"), parse_float=Decimal)


def one_claim(value, metric="U", unit="USD/kg"):
    return {"claim_id": "c1", "claim_type": "value", "hs6": "850450", "partner": "CN", "period": "202401",
            "baseline_period": None, "metric": metric, "value": value, "unit": unit, "direction": "NA",
            "evidence_ids": [f"{EV}7"], "text": "문장"}


def hand_hash(value_text, metric="U", unit="USD/kg", narrative="설명"):
    """계약 §9.1 규칙을 손으로 적은 정규화 문자열의 sha256."""
    canon = ('{"claims":[{"baseline_period":null,"claim_id":"c1","claim_type":"value","direction":"NA",'
             f'"evidence_ids":["{EV}7"],"hs6":"850450","metric":"{metric}","partner":"CN","period":"202401",'
             f'"text":"문장","unit":"{unit}","value":{value_text}}}],"evidence_ids":["{EV}7"],"hypotheses":[],'
             f'"narrative":"{narrative}"}}')
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()


class ReportObjectTest(unittest.TestCase):
    def test_report_has_exactly_the_contract_keys_in_order(self):
        report = render_ko.run(golden_input())["report"]
        self.assertEqual(tuple(report), render_ko.REPORT_KEYS)
        self.assertEqual(len(report), 17)

    def test_input_is_not_changed_and_outputs_are_copies(self):
        inp = golden_input()
        before = copy.deepcopy(inp)
        out = render_ko.run(inp)
        self.assertEqual(inp, before)
        out["report"]["claims"][0]["evidence_ids"].append("x")
        out["report"]["hypotheses"].append("x")
        self.assertEqual(inp, before)

    def test_status_is_carried_not_corrected(self):
        inp = golden_input()
        inp["review_status"] = "모니터링"  # 계약 코드가 아닌 값도 고치지 않고 옮긴다(검사는 검증기 몫)
        out = render_ko.run(inp)
        self.assertEqual(out["report"]["review_status"], "모니터링")
        self.assertIn("조사 뒤 제안: 모니터링(정해진 판정 상태가 아님)", out["body_ko"])

    def test_evidence_ids_collect_claims_in_first_seen_order(self):
        self.assertEqual(render_ko.collect_evidence([{"evidence_ids": ["b", "a"]}, {"evidence_ids": ["a", "c"]},
                                                     {"evidence_ids": None}, "x"]), ["b", "a", "c"])


class ReportHashTest(unittest.TestCase):
    def run_hash(self, items, narrative="설명", hypotheses=()):
        return render_ko.report_hash(items, narrative, list(hypotheses), render_ko.collect_evidence(items))

    def test_half_up_from_decimal_text_not_float(self):
        # 계약 §9.1: 원문 20.345를 Decimal로 읽으면 20.35, float를 거치면 20.34다.
        got = self.run_hash([one_claim(Decimal("20.345"))])
        self.assertEqual(got, hand_hash("20.35"))
        self.assertNotEqual(got, hand_hash("20.34"))

    def test_integer_digit_symbols_are_integers(self):
        self.assertEqual(self.run_hash([one_claim(Decimal("21876681.4"), "V", "USD")]), hand_hash("21876681", "V", "USD"))
        self.assertEqual(self.run_hash([one_claim(21876681, "V", "USD")]), hand_hash("21876681", "V", "USD"))

    def test_unknown_symbol_keeps_the_number(self):
        self.assertEqual(self.run_hash([one_claim(Decimal("1.23456"), "price", "USD")]),
                         hand_hash("1.23456", "price", "USD"))

    def test_trailing_zero_is_not_distinguished(self):
        # 계약 §9.1: report_hash는 끝자리 0만 다른 두 보고서(20.3과 20.30)를 가르지 못한다.
        self.assertEqual(self.run_hash([one_claim(Decimal("20.3"))]), self.run_hash([one_claim(Decimal("20.30"))]))
        self.assertNotEqual(self.run_hash([one_claim(Decimal("20.3"))]), self.run_hash([one_claim(Decimal("20.4"))]))

    def test_nfc_normalization(self):
        composed = "단가가 낮다"
        decomposed = unicodedata.normalize("NFD", composed)
        self.assertNotEqual(composed, decomposed)
        self.assertEqual(self.run_hash([one_claim(Decimal("3.60"))], composed),
                         self.run_hash([one_claim(Decimal("3.60"))], decomposed))
        self.assertEqual(self.run_hash([one_claim(Decimal("3.60"))], decomposed),
                         hand_hash("3.6", narrative=composed))

    def test_hash_covers_only_four_keys(self):
        inp = golden_input()
        base = render_ko.run(inp)["report"]["report_hash"]
        changed = copy.deepcopy(inp)
        changed["review_status"] = "MAINTAIN"
        changed["validator_findings"] = [{"check": "validator", "code": "X"}]
        self.assertEqual(render_ko.run(changed)["report"]["report_hash"], base)
        changed["narrative"] += " "
        self.assertNotEqual(render_ko.run(changed)["report"]["report_hash"], base)

    def test_nan_is_refused(self):
        with self.assertRaises(ValueError):
            self.run_hash([one_claim(Decimal("NaN"))])


class BodyTest(unittest.TestCase):
    def test_pre_investigation_comes_first_and_is_not_a_judgment(self):
        body = render_ko.run(golden_input())["body_ko"]
        first = body.index("처음 표시: 조사 전 경보(PRE_INVESTIGATION)")
        after = body.index("조사 뒤 제안: 자료 보류(HOLD)")
        self.assertLess(first, after)
        self.assertNotIn("→", body)  # 판정이 바뀐 이력처럼 화살표로 잇지 않는다

    def test_body_has_no_forbidden_vocabulary(self):
        body = render_ko.run(golden_input())["body_ko"]
        for word in ("부정", "위법", "불법", "원산지 조작", "우회수입", "우회 수입", "정상 확정", "탈세", "밀수"):
            self.assertNotIn(word, body)

    def test_findings_and_execution_status_are_shown(self):
        inp = golden_input()
        inp["validator_findings"] = [{"check": "validator", "code": "NUMERIC_MISMATCH", "path": "claims[0].value",
                                      "claim_id": "c1", "detail": "검증된 지표 값과 다르다"}]
        inp["execution_status"] = "INVALID"
        out = render_ko.run(inp)
        self.assertNotIn("execution_status", out["report"])
        self.assertIn("- [validator] NUMERIC_MISMATCH claims[0].value: 검증된 지표 값과 다르다", out["body_ko"])
        self.assertIn("실행 상태: INVALID. 유효한 최종 보고서가 아니므로 공유·승인 대상이 아니다", out["body_ko"])

    def test_bad_inputs_raise(self):
        for key, value in (("report_id", None), ("case", {}), ("claims", {}), ("narrative", None),
                           ("validator_findings", "x")):
            with self.subTest(key=key):
                inp = golden_input()
                inp[key] = value
                with self.assertRaises(ValueError):
                    render_ko.run(inp)


if __name__ == "__main__":
    unittest.main()
