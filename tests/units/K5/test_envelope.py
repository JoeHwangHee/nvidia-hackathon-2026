"""단위 K5(contract_envelope) 보조 시험: 키 순서, 기본값, 거부 사례."""
import copy
import unittest
from decimal import Decimal

from tradesentry.contract import envelope as k5
from tradesentry.contract import types

BASE = {"query_id": "q1", "tool": "check_comparability", "scope": {"hs6": "850450"}, "snapshot_id": "s1",
        "source_kind": "real", "elapsed_ms": 0}
METRIC = {"metric_id": "m1", "formula_version": "f1", "inputs": {}, "evidence_ids": ["ev:s1:observation:1"],
          "value": Decimal("20.34"), "unit": "USD/kg", "comparability_flags": [], "tolerance": None}


class EnvelopeTest(unittest.TestCase):
    def test_minimal_envelope_has_all_keys_in_contract_order(self):
        env = k5.make_envelope(**BASE)
        self.assertEqual(tuple(env), types.ENVELOPE_KEYS)
        self.assertEqual((env["evidence_ids"], env["metrics"], env["missingness"]), ([], [], []))
        self.assertIsNone(env["comparability"])
        self.assertIsNone(env["retryable_error"])
        self.assertEqual(k5.envelope_problems(env), [])
        other = k5.make_envelope(**BASE)
        other["metrics"].append(METRIC)
        self.assertEqual(env["metrics"], [])  # 기본 목록을 봉투끼리 나눠 쓰지 않는다

    def test_rejections(self):
        cases = {
            "필수 키 없음": {k: v for k, v in BASE.items() if k != "scope"},
            "모르는 키": {**BASE, "extra": 1},
            "도구 이름": {**BASE, "tool": "get_everything"},
            "출처 종류": {**BASE, "source_kind": "synthetic"},
            "elapsed_ms 음수": {**BASE, "elapsed_ms": -1},
            "elapsed_ms bool": {**BASE, "elapsed_ms": True},
            "다른 스냅샷 근거": {**BASE, "evidence_ids": ["ev:s2:observation:1"]},
            "근거 형식": {**BASE, "evidence_ids": ["ev:s1:observation:01"]},
            "float": {**BASE, "scope": {"x": 0.5}},
            "metric 키 부족": {**BASE, "metrics": [{k: v for k, v in METRIC.items() if k != "unit"}]},
            "metric 키 초과": {**BASE, "metrics": [{**METRIC, "symbol": "U"}]},
            "metric float": {**BASE, "metrics": [{**METRIC, "value": 20.34}]},
            "null 사유 없음": {**BASE, "metrics": [{**METRIC, "value": None}]},
            "comparability 모양": {**BASE, "comparability": []},
            "retryable_error 모양": {**BASE, "retryable_error": "503"},
            "missingness에 OBSERVED": {**BASE, "missingness": [{"observation_status": "OBSERVED"}]},
            "missingness에 모르는 상태": {**BASE, "missingness": [{"observation_status": "MISSING"}]},
        }
        for name, fields in cases.items():
            with self.subTest(name), self.assertRaises(ValueError):
                k5.make_envelope(**copy.deepcopy(fields))

    def test_metric_with_null_value_and_reason_passes(self):
        metric = {**METRIC, "value": None, "comparability_flags": ["기준월 중량 0"]}
        env = k5.make_envelope(**BASE, metrics=[metric], retryable_error={"reason": "잠시 뒤 다시"})
        self.assertEqual(env["metrics"], [metric])
        self.assertEqual(k5.metric_problems(metric, "s1"), [])

    def test_missingness_statuses(self):
        for status in ("NOT_COLLECTED", "REQUEST_FAILED", "UNRESOLVED_ZERO", "CONFIRMED_NO_TRADE"):
            env = k5.make_envelope(**BASE, missingness=[{"observation_status": status, "evidence_id": "ev:s1:observation:2"}])
            self.assertEqual(env["missingness"][0]["observation_status"], status)
        free = k5.make_envelope(**BASE, missingness=[{"note": "도구가 정한 모양"}, "HS10 자료 없음"])
        self.assertEqual(len(free["missingness"]), 2)  # observation_status가 없는 항목은 도구가 정한 모양 그대로

    def test_problems_of_incomplete_envelope(self):
        self.assertIn("봉투 키가 없다", k5.envelope_problems({"query_id": "q"})[0])
        self.assertEqual(k5.envelope_problems([]), ["봉투는 객체여야 한다"])


if __name__ == "__main__":
    unittest.main()
