"""단위 P4(policy_case_aggregate) 집계 규칙 시험.

신호 두 개의 상태 조합 15가지(둘 다 미발동인 조합은 사례가 아니다)를 모두 돌려, 우선순위 `MAINTAIN > HOLD > MONITOR`와
`MAINTAIN`·`HOLD` 혼합일 때만 `unresolved_evidence=true`가 되는지 본다(자료 계약 §3.1, 로드맵 MT1 행).
기대값은 규칙을 표로 적은 것이고 구현을 다시 부르지 않는다.
"""
import unittest

from tradesentry.policy import case_aggregate as p4

TRIG = {"unit_value": "TRIGGERED", "share": "TRIGGERED"}

# (단가 상태, 점유율 상태) → (사례 상태, unresolved_evidence). NT는 미발동.
TABLE = {
    ("MAINTAIN", "NT"): ("MAINTAIN", False),
    ("MONITOR", "NT"): ("MONITOR", False),
    ("HOLD", "NT"): ("HOLD", False),
    ("NT", "MAINTAIN"): ("MAINTAIN", False),
    ("NT", "MONITOR"): ("MONITOR", False),
    ("NT", "HOLD"): ("HOLD", False),
    ("MAINTAIN", "MAINTAIN"): ("MAINTAIN", False),
    ("MAINTAIN", "MONITOR"): ("MAINTAIN", False),
    ("MAINTAIN", "HOLD"): ("MAINTAIN", True),
    ("MONITOR", "MAINTAIN"): ("MAINTAIN", False),
    ("MONITOR", "MONITOR"): ("MONITOR", False),
    ("MONITOR", "HOLD"): ("HOLD", False),
    ("HOLD", "MAINTAIN"): ("MAINTAIN", True),
    ("HOLD", "MONITOR"): ("HOLD", False),
    ("HOLD", "HOLD"): ("HOLD", False),
}


def make_input(unit_value: str, share: str) -> dict:
    signals = {code: ("NOT_TRIGGERED" if state == "NT" else "TRIGGERED")
               for code, state in (("unit_value", unit_value), ("share", share))}
    status = {code: ("NOT_TRIGGERED" if state == "NT" else state)
              for code, state in (("unit_value", unit_value), ("share", share))}
    return {"signals": signals, "signal_status": status}


class AggregateTableTest(unittest.TestCase):
    def test_all_fifteen_combinations(self):
        self.assertEqual(len(TABLE), 15)
        for (uv, sh), (review, unresolved) in TABLE.items():
            with self.subTest(unit_value=uv, share=sh):
                out = p4.run(make_input(uv, sh))
                self.assertEqual(out, {"review_status": review, "unresolved_evidence": unresolved})
                self.assertIs(type(out["unresolved_evidence"]), bool)


class RejectTest(unittest.TestCase):
    def test_no_triggered_signal(self):
        with self.assertRaises(ValueError):
            p4.run(make_input("NT", "NT"))

    def test_status_disagrees_with_trigger(self):
        bad = [
            {"signals": TRIG, "signal_status": {"unit_value": "NOT_TRIGGERED", "share": "HOLD"}},
            {"signals": {"unit_value": "TRIGGERED", "share": "NOT_TRIGGERED"},
             "signal_status": {"unit_value": "MONITOR", "share": "MONITOR"}},
            {"signals": TRIG, "signal_status": {"unit_value": "PRE_INVESTIGATION", "share": "HOLD"}},
        ]
        for inp in bad:
            with self.subTest(inp=inp), self.assertRaises(ValueError):
                p4.run(inp)

    def test_malformed_input(self):
        bad = [
            None,
            {"signals": TRIG},
            {"signals": TRIG, "signal_status": {"unit_value": "HOLD"}},
            {"signals": TRIG, "signal_status": {"unit_value": "HOLD", "share": "HOLD", "x": "HOLD"}},
            {"signals": {"unit_value": "YES", "share": "TRIGGERED"}, "signal_status": {"unit_value": "HOLD",
                                                                                      "share": "HOLD"}},
            {"signals": TRIG, "signal_status": {"unit_value": "HOLD", "share": "HOLD"}, "extra": True},
        ]
        for inp in bad:
            with self.subTest(inp=inp), self.assertRaises(ValueError):
                p4.run(inp)


if __name__ == "__main__":
    unittest.main()
