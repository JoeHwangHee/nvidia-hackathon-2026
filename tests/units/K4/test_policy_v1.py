"""단위 K4(contract_policy_load) 보조 시험: 승인된 동결 판정 정책 파일 configs/policy_v1.json.

정본: 결정 기록 docs/tracking/decisions/20260925-0846-user-decision-policy-v1-approval.md(2026-09-25(금) 08:41 사용자
승인), 자료 계약 docs/rules/DATA_CONTRACT_V1.md §11.2(기준값 단위), 병렬 개발 규칙 §4.2(기준값이 바뀌면 oracle A/B/C를
다시 검증한다).

- 승인값 고정: 파일을 K4로 읽은 값이 승인 기록의 값과 같다. 수치나 키를 바꾸려면 새 policy_version과 사용자 승인이
  필요하므로(병렬 개발 규칙 §4.2), 여기서 값이 달라지면 그 절차 없이 파일이 바뀐 것이다.
- oracle A/B/C: oracle의 부모 HS6 행 V·Q와 전체국가(ALL) 금액으로 지표 단위 X1·X2의 반올림 전 정확값(r_U, d_s)을
  만들고, 이 정책으로 신호 발동 단위 P1을 돌린다. 세 사례 모두 단가 신호 발동, 점유율 신호 미발동, 데이터 품질 목록
  0건이어야 한다(최소 기준 min_amount·min_weight도 oracle 규모에서 통과한다).
  - oracle에 없는 입력은 시험이 정한다(tests/test_metrics_oracle.py와 같은 꼴): 품목 850450, 기준월 202301·비교월
    202401, 사례마다 다른 상대국(한 번의 P1 호출에서 계열이 겹치지 않게), 합이 oracle 분모(6000)인 ALL HS10 행 두 개.
- 합성 시험자료: controlled_fixture_v0(DT3)의 빌드 기록과 생성 규칙이 쓴 승격 규칙이 승인된 규칙과 같다(승인 기록의
  "함께 확인한 것": 같으므로 합성 자료를 다시 만들지 않는다). 단위 S2가 아는 규칙 이름과도 같다.
"""
import json
import unittest
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

from tradesentry.contract import policy_load as k4
from tradesentry.metrics import share as x2
from tradesentry.metrics import unit_value as x1
from tradesentry.policy import trigger as p1
from tradesentry.snapshot import build as s2

ROOT = Path(__file__).resolve().parents[3]
APPROVAL_RECORD = "20260925-0846-user-decision-policy-v1-approval.md"
ORACLE = ROOT / "eval" / "dev" / "oracle_ABC.json"
FIXTURE = ROOT / "data" / "snapshots" / "controlled_fixture_v0"
APPROVED = {  # 승인 기록 "결정 1"의 값(자료 계약 §11.2 단위: 30%는 30, 10pp는 10)
    "schema_version": 1,
    "policy_version": "policy_v1",
    "thresholds": {"unit_value": 30, "share": 10},
    "min_amount": 100,
    "min_weight": 10,
    "tolerance": {"amount_usd": 0, "weight_rounding_kg": Decimal("0.5")},
    "confirmed_no_trade": {"rule": "ingest_verify_candidates"},
}
SNAPSHOT = "oracle_abc"  # 합성 사례를 담았다고 보는 시험용 스냅샷 ID(근거 ID 접두어와 같다)
HS6, PERIOD, BASELINE = "850450", "202401", "202301"
PARTNERS = {"A-composition": "CN", "B-residual": "JP", "C-missing-hs10": "DE"}
ALL_CODES = ("8504501000", "8504502000")


def evidence(name: str) -> list[str]:
    return [f"ev:{SNAPSHOT}:observation:{name}"]


def oracle_metrics(case: dict, partner: str) -> tuple[Fraction, Fraction]:
    """oracle 사례 하나의 r_U(%)·d_s(pp) 반올림 전 정확값(단위 X1·X2)."""
    parent = [{"month": month, "hs_code": HS6, "observation_status": "OBSERVED", "amount_usd": case[side]["parent"]["V"],
               "net_weight_kg": case[side]["parent"]["Q"], "evidence_ids": evidence(f"{case['case_id']}-p-{month}")}
              for month, side in ((BASELINE, "baseline"), (PERIOD, "comparison"))]
    world = []
    for month, key in ((BASELINE, "V_world_0"), (PERIOD, "V_world_1")):
        total = case["expected"]["share"][key]
        for code, amount in zip(ALL_CODES, (total - 1000, 1000)):
            world.append({"month": month, "hs_code": code, "partner_code": "ALL", "observation_status": "OBSERVED",
                          "amount_usd": amount, "net_weight_kg": None,
                          "evidence_ids": evidence(f"{case['case_id']}-all-{code}-{month}")})
    target = {"snapshot_id": SNAPSHOT, "hs6": HS6, "partner": partner, "period": PERIOD, "baseline_period": BASELINE}
    r_u = x1.exact_value(x1.run({**target, "parent": parent})["metrics"][2])
    d_s = x2.exact_value(x2.run({**target, "parent": parent, "world": world})["metrics"][6])
    return r_u, d_s


class PolicyV1FileTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.policy = k4.load_policy("policy_v1")
        self.document = json.loads((ROOT / "configs" / "policy_v1.json").read_text(encoding="utf-8"),
                                   parse_float=Decimal)

    def test_values_match_approval_record(self):
        self.assertEqual(self.policy, APPROVED)
        self.assertEqual(type(self.policy["thresholds"]["unit_value"]), int)  # 30이지 0.3(비율)이 아니다
        status = self.document["_status"]
        self.assertIn("동결 판정 정책 policy_v1의 정본", status)
        self.assertIn(APPROVAL_RECORD, status)
        self.assertTrue((ROOT / "docs" / "tracking" / "decisions" / APPROVAL_RECORD).is_file())

    def test_oracle_abc_under_policy_v1(self):
        """oracle A/B/C: 단가 신호 발동, 점유율 신호 미발동, 데이터 품질 목록 0건(병렬 개발 규칙 §4.2 재검증)."""
        oracle = json.loads(ORACLE.read_text(encoding="utf-8"), parse_float=Decimal)
        rows = []
        for case in oracle["cases"]:
            partner = PARTNERS[case["case_id"]]
            r_u, d_s = oracle_metrics(case, partner)
            with self.subTest(case=case["case_id"]):  # oracle 값: r_U −0.4(−40%), d_s −4pp
                self.assertEqual(r_u, case["expected"]["unit_value"]["r_U"] * 100)
                self.assertEqual(d_s, case["expected"]["share"]["d_s_pp"])
            parents = (case["baseline"]["parent"], case["comparison"]["parent"])
            rows.append({"hs6": HS6, "partner": partner, "month": PERIOD, "baseline_month": BASELINE,
                         "r_U": r_u, "d_s": d_s,
                         "amount_usd": {"month": parents[1]["V"], "baseline_month": parents[0]["V"]},
                         "net_weight_kg": {"month": parents[1]["Q"], "baseline_month": parents[0]["Q"]}})
        out = p1.run({"policy": self.policy, "rows": rows})
        self.assertEqual(out["policy_version"], "policy_v1")
        self.assertEqual(out["data_quality"], [])
        got = {t["partner"]: t["signals"] for t in out["triggers"]}
        self.assertEqual(len(got), 3)
        for case in oracle["cases"]:
            with self.subTest(case=case["case_id"]):
                signals = got[PARTNERS[case["case_id"]]]
                self.assertEqual(signals, {"unit_value": "TRIGGERED", "share": "NOT_TRIGGERED"})
                self.assertEqual(signals, case["expected"]["signals"])
                self.assertIs(case["expected"]["share"]["triggered"], False)

    def test_fixture_build_uses_approved_promotion_rule(self):
        """합성 시험자료 controlled_fixture_v0의 빌드 기록·생성 규칙의 승격 규칙 = 승인된 규칙 = 단위 S2가 아는 규칙."""
        rule = self.policy["confirmed_no_trade"]["rule"]
        record = json.loads((FIXTURE / "snapshot_build.json").read_text(encoding="utf-8"))
        spec = json.loads((FIXTURE / "fixture_spec.json").read_text(encoding="utf-8"))
        self.assertEqual(record["confirmed_no_trade_rule"], rule)
        self.assertEqual(spec["promotion"]["rule"], rule)
        self.assertEqual(s2.PROMOTION_RULE, rule)
        self.assertIsNone(record["policy_version"])  # 합성 빌드는 정책에서 온 값이 아니다(DT3 결정 기록 ⑦)


if __name__ == "__main__":
    unittest.main()
