"""단위 X3(metrics_decompose) 추가 시험: 분해 값, 분해 조건과 사유, HS10 하위 지표, 부모 대조, 입력 거부.

기대값의 정본은 자료 계약 §11.2(공식·분해 조건·원천 규칙)·§2.3.2 행 규칙 4와 개발 플랜 §6.1(신설·소멸 HS10,
상쇄)이다. oracle A/B/C의 수치 대조 전체는 tests/test_metrics_oracle.py가 한다.
"""
import unittest
from decimal import Decimal
from fractions import Fraction

from tradesentry.metrics import decompose as x3

SNAPSHOT = "golden_metrics"
SNAP = f"ev:{SNAPSHOT}:observation:"
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
    return x3.run({"snapshot_id": SNAPSHOT, "hs6": "850450", "partner": "CN", "period": "202401",
                   "baseline_period": "202301", "parent": parent, "children": children,
                   "weight_rounding_kg": rounding_kg})


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

    def test_zero_parent_weight_blocks_decomposition(self):
        # 부모 중량 0: 부모 대조는 허용오차 안(|0 − 1| ≤ 1.0)이지만, 룰북 B3-1 "양 시점 중량 유효"에 부모 중량도
        # 넣어 세 값 모두 null이다(무역통계 검토 권고 4). 채점기(DT8)도 같은 규칙을 쓴다.
        out = run([parent_row("202301", 5, 0), parent_row("202401", 6, 2)],
                  [child("202301", A, 5, 1), child("202401", A, 6, 2)])
        got = by_key(out)
        for name in x3.EFFECTS:
            self.assertIsNone(got[(name, "202401")]["value"])
            self.assertEqual(got[(name, "202401")]["comparability_flags"], ["zero_weight"])
        self.assertTrue(out["parent_check"][0]["Q_match"])

    def test_parent_check_null_rules(self):
        # 부모 대조의 뜻과 null 규칙(Codex 권고 2): 계산됨 / 부모 누락 / 하위 상태 행
        computed = run(*ORACLE_A)["parent_check"][0]
        self.assertEqual(computed, {"period": "202301", "row_count": 2, "V_parent": 600, "V_hs10": 600,
                                    "Q_parent": 100, "Q_hs10": 100, "tolerance": Decimal("1.5"),
                                    "V_match": True, "Q_match": True})
        rest = ("V_parent", "V_hs10", "Q_parent", "Q_hs10", "tolerance", "V_match", "Q_match")
        parent_missing = run([parent_row("202301", status="REQUEST_FAILED"), parent_row("202401", 360, 100)],
                             ORACLE_A[1])["parent_check"][0]
        self.assertEqual(parent_missing, {"period": "202301", "row_count": 2, **dict.fromkeys(rest)})
        children_missing = run([parent_row("202301", 600, 100), parent_row("202401", 360, 100)],
                               ORACLE_A[1][:2] + [child_status("202401", "REQUEST_FAILED")])["parent_check"][1]
        self.assertEqual(children_missing, {"period": "202401", "row_count": None, **dict.fromkeys(rest)})


class ExactValueTest(unittest.TestCase):
    """판정 정책(P3)은 반올림 전 분해 값으로 "기준 안"을 판정한다. value는 표시 값이라 inputs로 다시 계산한다."""

    def test_golden_scenario_fractions(self):
        out = run([parent_row("202301", 1800, 301), parent_row("202401", 1480, 259)],
                  [child("202301", A, 300, 100), child("202301", B, 600, 100), child("202301", C, 900, 100),
                   child("202401", A, 330, 110), child("202401", B, 700, 100), child("202401", C, 450, 50)])
        got = by_key(out)
        self.assertEqual(x3.exact_value(got[("within_effect", "202401")]), Fraction(14, 39))
        self.assertEqual(x3.exact_value(got[("mix_effect", "202401")]), Fraction(-2, 3))
        self.assertEqual(x3.exact_value(got[("residual", "202401")]), Fraction(164, 3913))  # −80/301 − (−4/13)
        self.assertEqual(x3.exact_value(got[(f"w@{A}", "202301")]), Fraction(100, 3))
        self.assertEqual(x3.exact_value(got[(f"r_U@{B}", "202401")]), Fraction(50, 3))  # 7/6 − 1
        self.assertEqual(x3.exact_value(got[(f"U@{C}", "202401")]), Fraction(9))

    def test_rounding_would_flip_the_within_band(self):
        # 무역통계 검토 탐침 3(합성): 비중 변화 없이 하위품목 A 단가만 10.000 → 15.991. within 정확값 2.9955, 표시 3.00.
        # P3식 "기준 안"(|within| < 0.3 × U0 = 3.0)은 정확값으로 참, 표시 값으로 거짓이다.
        out = run([parent_row("202301", 20000, 2000), parent_row("202401", 25991, 2000)],
                  [child("202301", A, 10000, 1000), child("202301", B, 10000, 1000),
                   child("202401", A, 15991, 1000), child("202401", B, 10000, 1000)])
        got = by_key(out)
        within = got[("within_effect", "202401")]
        self.assertEqual(shown(within), "3.00")
        exact = x3.exact_value(within)
        self.assertEqual(exact, Fraction(29955, 10000))
        band = Fraction(3)  # 0.3 × U0(부모 20,000 USD ÷ 2,000 kg = 10)
        self.assertTrue(abs(exact) < band)
        self.assertFalse(abs(within["value"]) < band)
        self.assertEqual(x3.exact_value(got[("mix_effect", "202401")]), 0)
        self.assertEqual(x3.exact_value(got[("residual", "202401")]), 0)

    def test_inputs_pair_with_evidence(self):
        # 자료 계약 §2.3.4: inputs(계산에 쓴 입력값)와 evidence_ids(그 입력값이 나온 행)가 짝이다
        within = by_key(run(*ORACLE_A))[("within_effect", "202401")]
        values = within["inputs"]["hs10_values"]
        self.assertEqual(values, {A: {"V_0": 500, "Q_0": 50, "V_1": 200, "Q_1": 20},
                                  B: {"V_0": 100, "Q_0": 50, "V_1": 160, "Q_1": 80}})
        self.assertEqual({k: within["inputs"][k] for k in ("V_0", "Q_0", "V_1", "Q_1")},
                         {"V_0": 600, "Q_0": 100, "V_1": 360, "Q_1": 100})
        for month in ("202301", "202401"):
            self.assertIn(SNAP + "p" + month, within["evidence_ids"])
            for code in values:
                self.assertIn(SNAP + month + code, within["evidence_ids"])

    def test_null_and_mismatched_objects(self):
        out = run([parent_row("202301", 600, 100), parent_row("202401", 360, 100)],
                  ORACLE_A[1][:2] + [child_status("202401", "REQUEST_FAILED")])
        missing = by_key(out)[("within_effect", "202401")]
        self.assertIsNone(x3.exact_value(missing))
        self.assertEqual(missing["inputs"]["hs10_values"][A], {"V_0": 500, "Q_0": 50, "V_1": None, "Q_1": None})
        good = by_key(run(*ORACLE_A))[("mix_effect", "202401")]
        with self.assertRaises(ValueError):
            x3.exact_value({**good, "value": Decimal("-2.39")})
        changed = {**good["inputs"], "hs10_values": {**good["inputs"]["hs10_values"],
                                                      A: {"V_0": 500, "Q_0": 50, "V_1": 200, "Q_1": 40}}}
        with self.assertRaises(ValueError):
            x3.exact_value({**good, "inputs": changed})
        with self.assertRaises(ValueError):
            x3.exact_value({**good, "inputs": {**good["inputs"], "metric": "s"}})

    def test_effect_objects_do_not_share_inputs(self):
        # 무역통계 검토 2회차 권고 4: 분해 세 객체는 hs10_values를 따로 가진다. 한 객체를 고쳐도 다른 객체는 그대로다.
        got = by_key(run(*ORACLE_A))
        within, mix = got[("within_effect", "202401")], got[("mix_effect", "202401")]
        self.assertIsNot(within["inputs"]["hs10_values"], mix["inputs"]["hs10_values"])
        self.assertIsNot(within["inputs"]["hs10_values"][A], mix["inputs"]["hs10_values"][A])
        within["inputs"]["hs10_values"][A]["Q_1"] = 40
        self.assertEqual(x3.exact_value(mix), Fraction(-12, 5))  # mix −2.4 그대로
        with self.assertRaises(ValueError):
            x3.exact_value(within)  # 고친 객체만 value와 어긋난다


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
        with self.assertRaises(ValueError):  # weight_rounding_kg 누락
            x3.run({"snapshot_id": SNAPSHOT, "hs6": "850450", "partner": "CN", "period": "202401",
                    "baseline_period": "202301", "parent": parent, "children": children})
        with self.assertRaises(ValueError):  # snapshot_id 누락
            x3.run({"hs6": "850450", "partner": "CN", "period": "202401", "baseline_period": "202301",
                    "parent": parent, "children": children, "weight_rounding_kg": Decimal("0.5")})
        with self.assertRaises(TypeError):
            run(parent, children, rounding_kg=0.5)
        with self.assertRaises(ValueError):
            run(parent, children, rounding_kg=Decimal("-0.5"))


if __name__ == "__main__":
    unittest.main()
