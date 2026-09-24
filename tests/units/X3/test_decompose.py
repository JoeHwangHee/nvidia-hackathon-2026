"""단위 X3(metrics_decompose) 추가 시험: 분해 값, 분해 조건과 사유, HS10 하위 지표, 부모 대조, 입력 거부.

기대값의 정본은 자료 계약 §11.2(공식·분해 조건·원천 규칙)·§2.3.2 행 규칙 4와 개발 플랜 §6.1(신설·소멸 HS10,
상쇄)이다. oracle A/B/C의 수치 대조 전체는 tests/test_metrics_oracle.py가 한다.
"""
import unittest
from decimal import Decimal

from tradesentry.metrics import decompose as x3

SNAP = "ev:golden_metrics:observation:"
A, B, C = "8504501000", "8504502000", "8504509000"


def parent_row(month, v=None, q=None, status="OBSERVED", **extra):
    base = {"month": month, "observation_status": status, "amount_usd": v, "net_weight_kg": q,
            "evidence_ids": [SNAP + "p" + month]}
    base.update(extra)
    return base


def child(month, code, v, q):
    return {"month": month, "hs_code": code, "observation_status": "OBSERVED", "amount_usd": v, "net_weight_kg": q,
            "evidence_ids": [SNAP + month + code]}


def child_status(month, status):
    return {"month": month, "hs_code": "850450", "observation_status": status, "amount_usd": None,
            "net_weight_kg": None, "evidence_ids": [SNAP + "s" + month]}


def run(parent, children, rounding_kg=Decimal("0.5")):
    return x3.run({"hs6": "850450", "partner": "CN", "period": "202401", "baseline_period": "202301",
                   "parent": parent, "children": children, "weight_rounding_kg": rounding_kg})


def by_key(out):
    return {(m["inputs"]["metric"], m["inputs"]["period"]): m for m in out["metrics"]}


def shown(metric):
    return None if metric["value"] is None else str(metric["value"])


def effects(out):
    got = by_key(out)
    return tuple(shown(got[(name, "202401")]) for name in x3.EFFECTS)


ORACLE_A = ([parent_row("202301", 600, 100), parent_row("202401", 360, 100)],
            [child("202301", A, 500, 50), child("202301", B, 100, 50),
             child("202401", A, 200, 20), child("202401", B, 160, 80)])
ORACLE_B = ([parent_row("202301", 600, 100), parent_row("202401", 360, 100)],
            [child("202301", A, 500, 50), child("202301", B, 100, 50),
             child("202401", A, 300, 50), child("202401", B, 60, 50)])


class ValueTest(unittest.TestCase):
    def test_oracle_a_composition(self):
        out = run(*ORACLE_A)
        self.assertEqual(effects(out), ("0.00", "-2.40", "0.00"))
        got = by_key(out)
        self.assertEqual(got[("within_effect", "202401")]["tolerance"], Decimal("1.5"))  # 0.5 × (2 + 1)
        self.assertEqual(shown(got[(f"w@{A}", "202301")]), "50.0")
        self.assertEqual(shown(got[(f"w@{A}", "202401")]), "20.0")
        self.assertEqual(shown(got[(f"r_U@{A}", "202401")]), "0.0")
        self.assertTrue(all(c["V_match"] and c["Q_match"] for c in out["parent_check"]))

    def test_oracle_b_residual(self):
        self.assertEqual(effects(run(*ORACLE_B)), ("-2.40", "0.00", "0.00"))

    def test_offsetting_children_are_visible(self):
        # within 합계가 0이어도 하위품목의 +20%와 −20%가 상쇄된 것을 r_U@로 드러낸다(개발 플랜 §6.1)
        out = run([parent_row("202301", 2000, 200), parent_row("202401", 2000, 200)],
                  [child("202301", A, 1000, 100), child("202301", B, 1000, 100),
                   child("202401", A, 1200, 100), child("202401", B, 800, 100)])
        self.assertEqual(effects(out), ("0.00", "0.00", "0.00"))
        got = by_key(out)
        self.assertEqual(shown(got[(f"r_U@{A}", "202401")]), "20.0")
        self.assertEqual(shown(got[(f"r_U@{B}", "202401")]), "-20.0")

    def test_residual_is_parent_minus_children(self):
        # 부모 중량이 하위 합과 허용오차 안에서 다르면 잔차가 남는다(골든 쌍의 0.04와 같은 원리)
        out = run([parent_row("202301", 600, 101), parent_row("202401", 360, 100)], ORACLE_A[1])
        self.assertEqual(effects(out), ("0.00", "-2.40", "0.06"))  # 6 − 600/101 = 0.0594…


class ConditionTest(unittest.TestCase):
    def test_oracle_c_missing_hs10(self):
        # oracle C: 비교월 HS10 조회 실패 → within·mix·residual 모두 null(행 규칙 4). 기준월 하위 행은 A와 같게 둔다.
        out = run([parent_row("202301", 600, 100), parent_row("202401", 360, 100)],
                  ORACLE_A[1][:2] + [child_status("202401", "REQUEST_FAILED")])
        got = by_key(out)
        for name in x3.EFFECTS:
            self.assertIsNone(got[(name, "202401")]["value"])
            self.assertEqual(got[(name, "202401")]["comparability_flags"], ["REQUEST_FAILED"])
            self.assertIsNone(got[(name, "202401")]["tolerance"])
        self.assertIsNone(got[(f"U@{A}", "202401")]["value"])
        self.assertEqual(got[(f"U@{A}", "202401")]["evidence_ids"], [SNAP + "s202401"])
        self.assertEqual(shown(got[(f"U@{A}", "202301")]), "10.00")
        self.assertEqual(out["parent_check"][1]["V_match"], None)
        self.assertTrue(out["parent_check"][0]["V_match"])

    def test_new_and_vanished_hs10(self):
        out = run([parent_row("202301", 600, 100), parent_row("202401", 360, 100)],
                  [child("202301", A, 500, 50), child("202301", B, 100, 50),
                   child("202401", A, 200, 20), child("202401", C, 160, 80)])
        got = by_key(out)
        self.assertEqual(got[("mix_effect", "202401")]["comparability_flags"], ["hs10_set_changed"])
        self.assertIsNone(got[("mix_effect", "202401")]["tolerance"])
        self.assertEqual(got[(f"U@{C}", "202301")]["comparability_flags"], ["hs10_absent"])  # 0으로 채우지 않는다
        self.assertEqual(got[(f"U@{C}", "202301")]["evidence_ids"], [])
        self.assertEqual(got[(f"U@{B}", "202401")]["comparability_flags"], ["hs10_absent"])
        self.assertEqual(got[(f"r_U@{C}", "202401")]["comparability_flags"], ["hs10_absent"])
        self.assertEqual(shown(got[(f"w@{C}", "202401")]), "80.0")

    def test_zero_weight_child(self):
        out = run([parent_row("202301", 600, 100), parent_row("202401", 360, 100)],
                  [child("202301", A, 500, 100), child("202301", B, 100, 0),
                   child("202401", A, 200, 20), child("202401", B, 160, 80)])
        got = by_key(out)
        self.assertEqual(got[("within_effect", "202401")]["comparability_flags"], ["zero_weight"])
        self.assertEqual(got[(f"U@{B}", "202301")]["comparability_flags"], ["zero_weight"])
        self.assertEqual(shown(got[(f"w@{B}", "202301")]), "0.0")

    def test_parent_amount_mismatch(self):
        out = run([parent_row("202301", 601, 100), parent_row("202401", 360, 100)], ORACLE_A[1])
        self.assertEqual(by_key(out)[("within_effect", "202401")]["comparability_flags"], ["parent_mismatch"])
        self.assertIs(out["parent_check"][0]["V_match"], False)

    def test_weight_tolerance_comes_from_input(self):
        # 행당 반올림 kg는 정책 수치다. 0이면 1kg 차이도 불일치다(코드에 0.5를 박지 않았다).
        parent = [parent_row("202301", 600, 101), parent_row("202401", 360, 100)]
        self.assertEqual(effects(run(parent, ORACLE_A[1])), ("0.00", "-2.40", "0.06"))
        out = run(parent, ORACLE_A[1], rounding_kg=0)
        self.assertEqual(effects(out), (None, None, None))
        self.assertEqual(out["parent_check"][0]["tolerance"], Decimal("0"))
        self.assertIs(out["parent_check"][0]["Q_match"], False)

    def test_missing_parent(self):
        out = run([parent_row("202301", status="REQUEST_FAILED", hs_code="8504"), parent_row("202401", 360, 100)],
                  ORACLE_A[1])
        self.assertEqual(by_key(out)[("residual", "202401")]["comparability_flags"], ["REQUEST_FAILED"])
        self.assertEqual(out["parent_check"][0]["row_count"], 2)
        self.assertIsNone(out["parent_check"][0]["V_match"])

    def test_promoted_no_trade_month(self):
        out = run([parent_row("202301", status="CONFIRMED_NO_TRADE"), parent_row("202401", 360, 100)],
                  [child_status("202301", "CONFIRMED_NO_TRADE")] + ORACLE_A[1][2:])
        self.assertEqual(by_key(out)[("within_effect", "202401")]["comparability_flags"], ["CONFIRMED_NO_TRADE"])

    def test_residual_needs_parent_unit_value(self):
        # 부모 중량 0: 부모 대조는 허용오차 안(|0 − 1| ≤ 1.0)이라 within·mix는 계산하지만 ΔU는 정의되지 않는다
        out = run([parent_row("202301", 5, 0), parent_row("202401", 6, 2)],
                  [child("202301", A, 5, 1), child("202401", A, 6, 2)])
        got = by_key(out)
        self.assertEqual(shown(got[("within_effect", "202401")]), "-2.00")
        self.assertEqual(shown(got[("mix_effect", "202401")]), "0.00")
        self.assertIsNone(got[("residual", "202401")]["value"])
        self.assertEqual(got[("residual", "202401")]["comparability_flags"], ["zero_weight"])


class RejectTest(unittest.TestCase):
    def test_bad_inputs(self):
        parent, children = ORACLE_A
        cases = {
            "같은 코드 두 번": children + [child("202401", A, 1, 1)],
            "다른 HS6 아래 코드": children + [child("202401", "8504401000", 1, 1)],
            "HS4 상태 행": children[:2] + [{**child_status("202401", "REQUEST_FAILED"), "hs_code": "8504"}],
            "전체국가 행": children + [{**child("202401", C, 1, 1), "partner_code": "ALL"}],
        }
        for name, rows in cases.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                run(parent, rows)
        with self.assertRaises(ValueError):
            x3.run({"hs6": "850450", "partner": "CN", "period": "202401", "baseline_period": "202301",
                    "parent": parent, "children": children})
        with self.assertRaises(TypeError):
            run(parent, children, rounding_kg=0.5)
        with self.assertRaises(ValueError):
            run(parent, children, rounding_kg=Decimal("-0.5"))


if __name__ == "__main__":
    unittest.main()
