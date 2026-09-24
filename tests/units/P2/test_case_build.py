"""단위 P2(policy_case_build) 규칙 시험: 묶음 제한, 흔적 없는 버림, 사례 식별자, 입력 검사, P1 → P2 연결.

계열 코드는 모두 합성이다(999901 같은 품목, XA 같은 상대국). 실제 분할 기록의 배정을 흉내 내지 않는다.
"""
import copy
import json
import unittest
from decimal import Decimal

from tradesentry.policy import case_build as p2
from tradesentry.policy import trigger as p1

CONTRACT_CASE_FIELDS = {"case_id", "hs6", "partner", "month", "baseline_month", "signals", "snapshot_id",
                        "policy_version"}
UV = {"unit_value": "TRIGGERED", "share": "NOT_TRIGGERED"}
NONE = {"unit_value": "NOT_TRIGGERED", "share": "NOT_TRIGGERED"}


def trig(hs6, partner, month, signals):
    return {"hs6": hs6, "partner": partner, "month": month, "baseline_month": p1.baseline_of(month),
            "signals": dict(signals)}


def dq(hs6, partner, month):
    return {"hs6": hs6, "partner": partner, "month": month, "baseline_month": p1.baseline_of(month),
            "signal": "unit_value", "reason": "metric_null"}


DETECTION = {"policy_version": "dev-0.1",
             "triggers": [trig("999901", "XA", "202401", UV), trig("999901", "XB", "202401", UV),
                          trig("999901", "XA", "202402", NONE)],
             "data_quality": [dq("999901", "XB", "202403"), dq("999901", "XA", "202404")]}
ASSIGN = [{"hs6": "999901", "partner": "XA", "dataset": "real_dev"},
          {"hs6": "999901", "partner": "XB", "dataset": "real_sealed"}]


def real(dataset, assignment=ASSIGN, detection=DETECTION):
    return p2.run({"snapshot_id": "synthetic_real_v0", "source_kind": "real", "dataset": dataset,
                   "series_assignment": copy.deepcopy(assignment), "detection": copy.deepcopy(detection)})


class DatasetTest(unittest.TestCase):
    def test_dev_selection_leaves_no_trace_of_other_dataset(self):
        out = real("real_dev")
        self.assertEqual([c["case_id"] for c in out["cases"]], ["999901-XA-202401"])
        self.assertEqual(out["data_quality"], [dq("999901", "XA", "202404")])
        self.assertNotIn("XB", json.dumps(out))
        self.assertEqual(set(out), {"snapshot_id", "dataset", "policy_version", "cases", "data_quality"})

    def test_sealed_selection_is_the_complement(self):
        out = real("real_sealed")
        self.assertEqual([c["case_id"] for c in out["cases"]], ["999901-XB-202401"])
        self.assertEqual(out["data_quality"], [dq("999901", "XB", "202403")])
        self.assertNotIn("XA", json.dumps(out))

    def test_real_snapshot_needs_explicit_dataset_and_full_assignment(self):
        with self.assertRaises(ValueError):
            real(None)
        with self.assertRaises(ValueError):
            real("dev20")
        with self.assertRaises(ValueError):
            real("real_dev", assignment=None)
        with self.assertRaises(ValueError):
            real("real_dev", assignment=ASSIGN[:1])  # XB 계열이 배정에 없다
        with self.assertRaises(ValueError):
            real("real_dev", assignment=ASSIGN + [dict(ASSIGN[0])])
        with self.assertRaises(ValueError):
            real("real_dev", assignment=[dict(ASSIGN[0], dataset="holdout40"), ASSIGN[1]])

    def test_controlled_snapshot_takes_every_series(self):
        out = p2.run({"snapshot_id": "controlled_fixture_v0", "source_kind": "controlled",
                      "detection": copy.deepcopy(DETECTION)})
        self.assertIsNone(out["dataset"])
        self.assertEqual([c["case_id"] for c in out["cases"]], ["999901-XA-202401", "999901-XB-202401"])
        self.assertEqual(len(out["data_quality"]), 2)
        for extra in ({"dataset": "real_dev"}, {"series_assignment": ASSIGN}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                p2.run({"snapshot_id": "controlled_fixture_v0", "source_kind": "controlled",
                        "detection": copy.deepcopy(DETECTION), **extra})


class CaseTest(unittest.TestCase):
    def test_case_object_fields(self):
        case = real("real_dev")["cases"][0]
        self.assertEqual(set(case), CONTRACT_CASE_FIELDS | {"scope"})
        self.assertEqual(case["scope"], {"hs6": "999901", "partner": "XA", "month": "202401",
                                         "baseline_month": "202301"})
        self.assertEqual(case["snapshot_id"], "synthetic_real_v0")
        self.assertEqual(case["policy_version"], "dev-0.1")
        self.assertEqual(case["signals"], UV)

    def test_case_id_round_trip(self):
        case_id = p2.case_id_for("850450", "CN", "202401")
        self.assertEqual(case_id, "850450-CN-202401")
        self.assertEqual(p2.parse_case_id(case_id), {"hs6": "850450", "partner": "CN", "month": "202401",
                                                     "baseline_month": "202301"})
        for bad in ("A-composition", "850450-CN-202413", "850450-ALL-202401", "85045-CN-202401",
                    "850450-cn-202401", "850450-CN-202401-x", "", None, 850450):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                p2.parse_case_id(bad)
        with self.assertRaises(ValueError):
            p2.case_id_for("850450", "ALL", "202401")


class RejectTest(unittest.TestCase):
    def test_bad_detection_rows(self):
        bad_rows = [
            trig("999901", "XA", "202401", {"unit_value": "TRIGGERED"}),
            dict(trig("999901", "XA", "202401", UV), baseline_month="202312"),
            trig("99990", "XA", "202401", UV),
            trig("999901", "ALL", "202401", UV),
        ]
        for row in bad_rows:
            detection = dict(DETECTION, triggers=[row])
            with self.subTest(row=row), self.assertRaises(ValueError):
                p2.run({"snapshot_id": "controlled_fixture_v0", "source_kind": "controlled", "detection": detection})
        duplicate = dict(DETECTION, triggers=[DETECTION["triggers"][0], trig("999901", "XA", "202401", NONE)])
        with self.assertRaises(ValueError):
            p2.run({"snapshot_id": "controlled_fixture_v0", "source_kind": "controlled", "detection": duplicate})

    def test_bad_envelope(self):
        base = {"snapshot_id": "controlled_fixture_v0", "source_kind": "controlled", "detection": DETECTION}
        bad = [None, dict(base, snapshot_id="../x"), dict(base, snapshot_id="kcs:1"), dict(base, snapshot_id=""),
               dict(base, source_kind="synthetic"), dict(base, detection={"triggers": [], "data_quality": []}),
               dict(base, detection=dict(DETECTION, extra=[])), dict(base, detection=dict(DETECTION, policy_version="")),
               dict(base, extra=1), {k: v for k, v in base.items() if k != "detection"}]
        for inp in bad:
            with self.subTest(inp=inp), self.assertRaises(ValueError):
                p2.run(inp)


class PipelineTest(unittest.TestCase):
    def test_p1_output_feeds_p2(self):
        policy = {"policy_version": "dev-0.1", "thresholds": {"unit_value": 30, "share": 10}}
        rows = [{"hs6": "999901", "partner": "XA", "month": "202401", "baseline_month": "202301",
                 "r_U": Decimal("-40.0"), "d_s": Decimal("-4.0")},
                {"hs6": "999901", "partner": "XA", "month": "202402", "baseline_month": "202302",
                 "r_U": None, "d_s": Decimal("1.0")}]
        detection = p1.run({"policy": policy, "rows": rows})
        out = p2.run({"snapshot_id": "controlled_fixture_v0", "source_kind": "controlled", "detection": detection})
        self.assertEqual([c["case_id"] for c in out["cases"]], ["999901-XA-202401"])
        self.assertEqual(out["cases"][0]["signals"], UV)
        self.assertEqual([q["month"] for q in out["data_quality"]], ["202402"])


if __name__ == "__main__":
    unittest.main()
