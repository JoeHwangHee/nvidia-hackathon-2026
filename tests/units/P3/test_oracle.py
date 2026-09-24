"""단위 P3(policy_signal_decide) oracle 대조 시험.

eval/dev/oracle_ABC.json의 A/B/C에서 근거 상태를 만들어 P3 → P4를 돌리면 사례 상태가 A `MONITOR`, B `MAINTAIN`,
C `HOLD`가 되는지 본다(oracle의 한국어 표기와 계약 코드의 대응은 자료 계약 §3.2).
- 정책 객체는 단위 K4가 아직 없어 이 시험 안의 대역이다. 임계값은 oracle의 `policy_version` 문구에서 읽는다.
- 분해 값(within·mix·residual)은 단위 X3·도구 decompose_hs가 아직 없어 oracle 기대값을 대역으로 쓴다. 하위품목 단가
  변화율과 기준월 부모 단가는 oracle의 V·Q에서 Decimal로 계산한다.
- C는 비교월 HS10 조회가 실패했다. 부모 HS6 행이 있는 달의 HS6 자릿수 상태 행으로 넣는다(자료 계약 §2.3.2 행 규칙 4).
- 품목·상대국·월은 oracle에 없어 합성 값을 붙인다.
"""
import json
import re
import unittest
from decimal import Decimal
from pathlib import Path

from tradesentry.policy import case_aggregate as p4
from tradesentry.policy import signal_decide as p3

ROOT = Path(__file__).resolve().parents[3]
ORACLE = ROOT / "eval" / "dev" / "oracle_ABC.json"
LABEL = {"검토 유지": "MAINTAIN", "모니터링": "MONITOR", "자료 보류": "HOLD"}
HS6, PARTNER, MONTH, BASELINE = "850450", "CN", "202401", "202301"


def dev_policy(oracle: dict) -> dict:
    text = oracle["policy_version"]
    return {"policy_version": text.split(" ", 1)[0],
            "thresholds": {"unit_value": Decimal(re.search(r"\|r_U\|>=([0-9.]+)%", text).group(1)),
                           "share": Decimal(re.search(r"\|d_s\|>=([0-9.]+)pp", text).group(1))}}


def unit_value(v: int, q: int) -> Decimal:
    return Decimal(v) / Decimal(q)


def evidence_for(case: dict) -> dict:
    base, comp = case["baseline"], case["comparison"]
    expected = case["expected"]["unit_value"]
    missingness, children = [], []
    if isinstance(comp.get("hs10"), str):
        missingness.append({"partner": PARTNER, "hs_code": HS6, "month": MONTH,
                            "observation_status": comp["hs10"]})
    else:
        before = {c["code"]: c for c in base["hs10"]}
        for child in comp["hs10"]:
            old = before[child["code"]]
            ratio = (Decimal(child["V"]) * old["Q"]) / (Decimal(child["Q"]) * old["V"])
            children.append({"hs10": child["code"], "r_U": (ratio - 1) * 100})
    decomposition = {"within_effect": expected["within"], "mix_effect": expected["mix"],
                     "residual": expected.get("residual"), "parent_child_match": not missingness}
    return {"missingness": missingness,
            "unit_value": {"U_baseline": unit_value(base["parent"]["V"], base["parent"]["Q"]),
                           "decomposition": decomposition, "children": children},
            "share": {}}


class OracleDecisionTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.oracle = json.loads(ORACLE.read_text(encoding="utf-8"), parse_float=Decimal)
        self.policy = dev_policy(self.oracle)

    def test_abc_end_in_expected_states(self):
        expected_basis = {"A-composition": "composition_explained", "B-residual": "unexplained",
                          "C-missing-hs10": "data_insufficient"}
        for case in self.oracle["cases"]:
            with self.subTest(case=case["case_id"]):
                signals = case["expected"]["signals"]
                record = {"case_id": case["case_id"], "hs6": HS6, "partner": PARTNER, "month": MONTH,
                          "baseline_month": BASELINE, "signals": signals}
                out = p3.run({"policy": self.policy, "case": record, "evidence": evidence_for(case)})
                review = LABEL[case["expected"]["review_status"]]
                self.assertEqual(out["signal_status"], {"unit_value": review, "share": "NOT_TRIGGERED"})
                self.assertEqual(out["basis"]["unit_value"], expected_basis[case["case_id"]])
                final = p4.run({"signals": signals, "signal_status": out["signal_status"]})
                self.assertEqual(final, {"review_status": review, "unresolved_evidence": False})


if __name__ == "__main__":
    unittest.main()
