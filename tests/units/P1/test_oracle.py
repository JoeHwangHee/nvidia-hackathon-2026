"""단위 P1(policy_trigger) oracle 대조 시험(로드맵 MT1 완료 기준, 병렬 개발 규칙 §3.2).

eval/dev/oracle_ABC.json의 `threshold_pp`·`triggered`·`signals`를 개발용 정책 `dev-0.1`의 값(단가 변화율 절댓값 30%
이상, 점유율 변화 절댓값 10pp 이상)으로 대조한다.
- 정책 객체는 단위 K4(정책 수치 읽기)가 아직 없어 이 시험 안의 대역이다. 임계값은 코드에 따로 적지 않고 oracle의
  `policy_version` 문구("|r_U|>=30%, |d_s|>=10pp")와 `threshold_pp`에서 읽는다.
- 지표 입력은 단위 X1·X2(지표)가 아직 없어 oracle 기대값을 대역으로 쓴다. oracle의 `r_U`는 비율이므로 100을 곱해
  %로 바꾼다(자료 계약 §11.5). `d_s_pp`는 이미 pp다.
- A/B/C의 품목·상대국·월은 oracle에 없어 합성 값(서로 다른 계열)을 붙인다.
"""
import json
import re
import unittest
from decimal import Decimal
from pathlib import Path

from tradesentry.policy import trigger as p1

ROOT = Path(__file__).resolve().parents[3]
ORACLE = ROOT / "eval" / "dev" / "oracle_ABC.json"
SERIES = {"A-composition": ("850450", "CN"), "B-residual": ("850450", "JP"), "C-missing-hs10": ("850450", "DE")}


def load_oracle() -> dict:
    return json.loads(ORACLE.read_text(encoding="utf-8"), parse_float=Decimal)


def dev_policy(oracle: dict) -> dict:
    """oracle 머리의 개발용 정책 문구에서 dev-0.1 정책 객체(K4 대역)를 만든다."""
    text = oracle["policy_version"]
    version = text.split(" ", 1)[0]
    unit_value = Decimal(re.search(r"\|r_U\|>=([0-9.]+)%", text).group(1))
    share = Decimal(re.search(r"\|d_s\|>=([0-9.]+)pp", text).group(1))
    return {"policy_version": version, "thresholds": {"unit_value": unit_value, "share": share},
            "min_amount": None, "min_weight": None}


class OracleTriggerTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.oracle = load_oracle()
        self.policy = dev_policy(self.oracle)

    def test_dev_policy_values(self):
        self.assertEqual(self.policy["policy_version"], "dev-0.1")
        self.assertEqual(self.policy["thresholds"], {"unit_value": 30, "share": 10})
        for case in self.oracle["cases"]:
            with self.subTest(case=case["case_id"]):
                self.assertEqual(self.policy["thresholds"]["share"], case["expected"]["share"]["threshold_pp"])

    def test_signals_and_share_triggered_match_oracle(self):
        rows = []
        for case in self.oracle["cases"]:
            hs6, partner = SERIES[case["case_id"]]
            rows.append({"hs6": hs6, "partner": partner, "month": "202401", "baseline_month": "202301",
                         "r_U": case["expected"]["unit_value"]["r_U"] * 100,
                         "d_s": case["expected"]["share"]["d_s_pp"]})
        out = p1.run({"policy": self.policy, "rows": rows})
        self.assertEqual(out["policy_version"], "dev-0.1")
        self.assertEqual(out["data_quality"], [])
        got = {(t["hs6"], t["partner"]): t["signals"] for t in out["triggers"]}
        self.assertEqual(len(got), 3)
        for case in self.oracle["cases"]:
            with self.subTest(case=case["case_id"]):
                signals = got[SERIES[case["case_id"]]]
                self.assertEqual(signals, case["expected"]["signals"])
                triggered = case["expected"]["share"]["triggered"]
                self.assertIs(type(triggered), bool)
                self.assertEqual(signals["share"], "TRIGGERED" if triggered else "NOT_TRIGGERED")


if __name__ == "__main__":
    unittest.main()
