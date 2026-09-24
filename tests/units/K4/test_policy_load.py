"""단위 K4(contract_policy_load) 보조 시험: 실제 개발용 정책 파일, oracle 기준값 대조, 거부 사례, 버전과 파일 대응."""
import copy
import json
import re
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from tradesentry.contract import policy_load as k4

ROOT = Path(__file__).resolve().parents[3]
DEV_DOC = json.loads((ROOT / "configs" / "policy_dev.json").read_text(encoding="utf-8"), parse_float=Decimal)


class DevPolicyFileTest(unittest.TestCase):
    def test_dev_policy_file_matches_oracle_thresholds(self):
        """configs/policy_dev.json의 기준값은 oracle 최상위 policy_version 설명의 값과 같다(결정 D2)."""
        policy = k4.load_policy("dev-0.1")
        oracle = json.loads((ROOT / "eval" / "dev" / "oracle_ABC.json").read_text(encoding="utf-8"))
        text = oracle["policy_version"]
        self.assertTrue(text.startswith(policy["policy_version"] + " "))
        r_u = re.search(r"\|r_U\|>=(\d+)%", text).group(1)
        d_s = re.search(r"\|d_s\|>=(\d+)pp", text).group(1)
        self.assertEqual(policy["thresholds"], {"unit_value": int(r_u), "share": int(d_s)})
        # 판정 정책(MT1)이 읽는 키: policy_version, thresholds.unit_value(%), thresholds.share(pp), min_amount, min_weight
        self.assertEqual({k: policy[k] for k in ("policy_version", "min_amount", "min_weight")},
                         {"policy_version": "dev-0.1", "min_amount": None, "min_weight": None})
        # oracle 사례의 threshold_pp도 같은 값이다
        self.assertEqual({case["expected"]["share"]["threshold_pp"] for case in oracle["cases"]}, {int(d_s)})
        self.assertIsNone(policy["confirmed_no_trade"])
        self.assertEqual(policy["tolerance"], {"amount_usd": 0, "weight_rounding_kg": Decimal("0.5")})

    def test_policy_path(self):
        self.assertEqual(k4.policy_path("policy_v1").name, "policy_v1.json")
        self.assertEqual(k4.policy_path("dev-0.1").name, "policy_dev.json")
        self.assertEqual(k4.policy_path("dev-0.2", configs_dir=Path("x")), Path("x") / "policy_dev.json")
        for bad in ("policy_v2", "dev-1", "../policy_v1", "policy_v1.json", "", None):
            with self.subTest(bad=bad), self.assertRaises(k4.PolicyError):
                k4.policy_path(bad)

    def test_load_checks_file_version_and_presence(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            with self.assertRaises(k4.PolicyError):
                k4.load_policy("policy_v1", configs_dir=folder)  # 파일 없음
            (folder / "policy_dev.json").write_text((ROOT / "configs" / "policy_dev.json").read_text(encoding="utf-8"),
                                                    encoding="utf-8")
            self.assertEqual(k4.load_policy("dev-0.1", configs_dir=folder)["policy_version"], "dev-0.1")
            with self.assertRaises(k4.PolicyError) as cm:
                k4.load_policy("dev-0.2", configs_dir=folder)  # 파일 안 버전이 다르다
            self.assertIn("policy_version이 dev-0.2이 아니다", str(cm.exception))
            (folder / "policy_v1.json").write_text("{", encoding="utf-8")
            with self.assertRaises(k4.PolicyError):
                k4.load_policy("policy_v1", configs_dir=folder)  # JSON 아님


class ParseTest(unittest.TestCase):
    def mutated(self, change) -> dict:
        doc = copy.deepcopy(DEV_DOC)
        change(doc)
        return doc

    def test_promotion_rule(self):
        doc = self.mutated(lambda d: d.update(confirmed_no_trade={"rule": "ingest_verify_candidates"},
                                              policy_version="policy_v1", min_amount=100, min_weight=Decimal("1.5")))
        policy = k4.parse_policy(doc)
        self.assertEqual(policy["confirmed_no_trade"], {"rule": "ingest_verify_candidates"})
        self.assertEqual((policy["min_amount"], policy["min_weight"]), (100, Decimal("1.5")))
        self.assertNotIn("_status", policy)

    def test_rejections(self):
        cases = {
            "승격 규칙 이름": lambda d: d.update(confirmed_no_trade={"rule": "all_empty_months"}),
            "승격 규칙 키": lambda d: d.update(confirmed_no_trade={"rule": "ingest_verify_candidates", "months": 3}),
            "모르는 키": lambda d: d.update(extra=1),
            "빠진 키": lambda d: d.pop("min_weight"),
            "schema_version": lambda d: d.update(schema_version=2),
            "schema_version bool": lambda d: d.update(schema_version=True),
            "policy_version 형식": lambda d: d.update(policy_version="dev 0.1"),
            "기준값 float": lambda d: d["thresholds"].update(unit_value=0.3),
            "기준값 음수": lambda d: d["thresholds"].update(share=-10),
            "기준값 문자열": lambda d: d["thresholds"].update(share="10"),
            "기준값 객체": lambda d: d["thresholds"].update(share={"abs_gte": 10}),
            "기준값 빠짐": lambda d: d["thresholds"].pop("share"),
            "신호 이름": lambda d: d["thresholds"].update(price=d["thresholds"].pop("unit_value")),
            "허용오차 키": lambda d: d["tolerance"].pop("amount_usd"),
            "min_amount 문자열": lambda d: d.update(min_amount="100"),
            "무한대": lambda d: d.update(min_weight=Decimal("Infinity")),
        }
        for name, change in cases.items():
            with self.subTest(name), self.assertRaises(k4.PolicyError):
                k4.parse_policy(self.mutated(change))
        with self.assertRaises(k4.PolicyError):
            k4.parse_policy([])


if __name__ == "__main__":
    unittest.main()
