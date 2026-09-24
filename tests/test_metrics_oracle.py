"""인수 조건 4: 지표 패키지(단위 X1~X3)가 eval/dev/oracle_ABC.json의 A/B/C 수치 필드를 재현한다.

정본: docs/rules/PARALLEL_DEV_RULES.md §3.2(대조 필드 목록), docs/rules/DATA_CONTRACT_V1.md §11.5(oracle 키와 계약
기호의 대응), docs/plan/ROADMAP.md DT2 행. oracle 파일은 읽기만 하고 고치지 않는다.

- 대조 필드: unit_value의 U0·U1·r_U·within·mix·residual, share의 V_country_0·V_country_1·V_world_0·V_world_1·
  s0_pp·s1_pp·d_s_pp. C처럼 분해할 수 없는 사례의 within·mix는 null 그대로 일치해야 한다(0으로 채우지 않는다).
  C에는 residual 키가 없으므로 대조하지 않는다. triggered·threshold_pp·signals는 판정 정책(MT1) 시험의 몫이다.
- 비교는 수의 크기로 한다(6.00 = 6.0). oracle의 r_U는 비율이라 100을 곱해 %로 비교한다(-0.4 → -40.0).
- oracle에 없는 입력은 시험이 정한다. 사례를 시험 입력으로 옮기면서 붙인 것은 다음과 같다.
  - 대상: hs6 850450, 상대국 CN, 비교월 202401, 기준월 202301(oracle에는 품목·국가·월이 없다).
  - 하위 코드: oracle의 X1·X2를 10자리 HS10 코드 8504501000·8504502000으로 옮긴다(코드 검사를 느슨하게 하지 않는다).
  - 분모: V_world는 사례 입력(부모·하위 행)에서 나오지 않는다. 합이 기대값(6000)인 ALL HS10 행 두 개를 합성해
    넣는다. 이 대조는 분모를 더하는 논리만 확인한다.
  - C의 기준월 HS10: oracle에 없어 A·B와 같은 기준월 하위 행(부모 600 USD·100 kg와 맞는다)을 넣는다. C의
    within·mix가 null인 것은 비교월 HS10 조회 실패(REQUEST_FAILED)로 정해진다.
"""
import json
import unittest
from decimal import Decimal
from pathlib import Path

from tradesentry.metrics import decompose, share, unit_value

ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "eval" / "dev" / "oracle_ABC.json"
HS6, PARTNER, PERIOD, BASELINE = "850450", "CN", "202401", "202301"
CODES = {"X1": "8504501000", "X2": "8504502000"}
POLICY_FIELDS = {"triggered", "threshold_pp"}  # 판정 정책(MT1) 시험에서 대조한다(병렬 개발 규칙 §3.2)
WEIGHT_ROUNDING_KG = Decimal("0.5")  # 시험 입력값(계약 §11.1의 출발값). 실행에서는 정책 수치 읽기가 준다


def load_oracle() -> dict:
    return json.loads(ORACLE.read_text(encoding="utf-8"), parse_float=Decimal)


def evidence(name: str) -> list[str]:
    return [f"ev:oracle_abc:observation:{name}"]


def parent_rows(case: dict) -> list[dict]:
    rows = []
    for month, side in ((BASELINE, "baseline"), (PERIOD, "comparison")):
        parent = case[side]["parent"]
        rows.append({"month": month, "hs_code": HS6, "observation_status": "OBSERVED", "amount_usd": parent["V"],
                     "net_weight_kg": parent["Q"], "evidence_ids": evidence(f"{case['case_id']}-parent-{month}")})
    return rows


def child_rows(case: dict, fallback_baseline: list) -> list[dict]:
    rows = []
    for month, side in ((BASELINE, "baseline"), (PERIOD, "comparison")):
        children = case[side].get("hs10", fallback_baseline if side == "baseline" else None)
        if isinstance(children, str):  # oracle C: "REQUEST_FAILED"(자료 계약 §3.2 대응표)
            rows.append({"month": month, "hs_code": HS6, "observation_status": children, "amount_usd": None,
                         "net_weight_kg": None, "evidence_ids": evidence(f"{case['case_id']}-hs10-{month}")})
            continue
        for item in children:
            rows.append({"month": month, "hs_code": CODES[item["code"]], "observation_status": "OBSERVED",
                         "amount_usd": item["V"], "net_weight_kg": item["Q"],
                         "evidence_ids": evidence(f"{case['case_id']}-{item['code']}-{month}")})
    return rows


def world_rows(case: dict) -> list[dict]:
    rows = []
    for month, key in ((BASELINE, "V_world_0"), (PERIOD, "V_world_1")):
        total = case["expected"]["share"][key]
        for code, amount in ((CODES["X1"], total - 1000), (CODES["X2"], 1000)):
            rows.append({"month": month, "hs_code": code, "partner_code": "ALL", "observation_status": "OBSERVED",
                         "amount_usd": amount, "net_weight_kg": None,
                         "evidence_ids": evidence(f"{case['case_id']}-ALL-{code}-{month}")})
    return rows


def reproduce(case: dict, fallback_baseline: list) -> dict[str, dict[str, object]]:
    """사례 하나를 X1·X2·X3에 넣어 oracle 키 이름으로 값을 모은다."""
    target = {"hs6": HS6, "partner": PARTNER, "period": PERIOD, "baseline_period": BASELINE}
    parent = parent_rows(case)
    found: dict[tuple[str, str, str], object] = {}
    outputs = [unit_value.run({**target, "parent": parent}),
               share.run({**target, "parent": parent, "world": world_rows(case)}),
               decompose.run({**target, "parent": parent, "children": child_rows(case, fallback_baseline),
                              "weight_rounding_kg": WEIGHT_ROUNDING_KG})]
    for out in outputs:
        for m in out["metrics"]:
            found[(m["inputs"]["metric"], m["inputs"]["partner"], m["inputs"]["period"])] = m["value"]
    return {
        "unit_value": {"U0": found[("U", PARTNER, BASELINE)], "U1": found[("U", PARTNER, PERIOD)],
                       "r_U": found[("r_U", PARTNER, PERIOD)], "within": found[("within_effect", PARTNER, PERIOD)],
                       "mix": found[("mix_effect", PARTNER, PERIOD)], "residual": found[("residual", PARTNER, PERIOD)]},
        "share": {"V_country_0": found[("V", PARTNER, BASELINE)], "V_country_1": found[("V", PARTNER, PERIOD)],
                  "V_world_0": found[("V", "ALL", BASELINE)], "V_world_1": found[("V", "ALL", PERIOD)],
                  "s0_pp": found[("s", PARTNER, BASELINE)], "s1_pp": found[("s", PARTNER, PERIOD)],
                  "d_s_pp": found[("d_s", PARTNER, PERIOD)]},
    }


def as_contract_unit(section: str, key: str, value: object) -> object:
    """oracle 값을 계약 단위로 바꾼다. r_U만 비율이라 ×100(계약 §11.5)."""
    if value is None or not (section == "unit_value" and key == "r_U"):
        return value
    return value * 100


class OracleReproductionTest(unittest.TestCase):
    def test_numeric_fields_match(self):
        oracle = load_oracle()
        fallback = oracle["cases"][0]["baseline"]["hs10"]  # C의 기준월 HS10(머리말 참고)
        compared = []
        for case in oracle["cases"]:
            got = reproduce(case, fallback)
            for section in ("unit_value", "share"):
                for key, expected in case["expected"][section].items():
                    if key in POLICY_FIELDS:
                        continue
                    with self.subTest(case=case["case_id"], field=f"{section}.{key}"):
                        want, have = as_contract_unit(section, key, expected), got[section][key]
                        if want is None:
                            self.assertIsNone(have)  # null 그대로(0으로 채우지 않는다)
                        else:
                            self.assertIsNotNone(have)
                            self.assertIsInstance(have, (int, Decimal))
                            self.assertEqual(Decimal(have), Decimal(want))
                    compared.append((case["case_id"], section, key))
        # 병렬 개발 규칙 §3.2의 목록이 빠짐없이 대조됐는가(C의 residual은 oracle에 키가 없다)
        unit_keys = {"U0", "U1", "r_U", "within", "mix", "residual"}
        share_keys = {"V_country_0", "V_country_1", "V_world_0", "V_world_1", "s0_pp", "s1_pp", "d_s_pp"}
        for case_id in ("A-composition", "B-residual", "C-missing-hs10"):
            expected_unit = unit_keys - ({"residual"} if case_id == "C-missing-hs10" else set())
            self.assertEqual({k for c, s, k in compared if c == case_id and s == "unit_value"}, expected_unit)
            self.assertEqual({k for c, s, k in compared if c == case_id and s == "share"}, share_keys)

    def test_c_decomposition_is_null_not_zero(self):
        oracle = load_oracle()
        case = next(c for c in oracle["cases"] if c["case_id"] == "C-missing-hs10")
        got = reproduce(case, oracle["cases"][0]["baseline"]["hs10"])
        self.assertIsNone(got["unit_value"]["within"])
        self.assertIsNone(got["unit_value"]["mix"])
        self.assertIsNone(got["unit_value"]["residual"])  # 계약 행 규칙 4: residual도 계산하지 않는다

    def test_oracle_file_shape_is_what_this_test_reads(self):
        oracle = load_oracle()
        self.assertEqual([c["case_id"] for c in oracle["cases"]], ["A-composition", "B-residual", "C-missing-hs10"])
        self.assertTrue(str(oracle["policy_version"]).startswith("dev-0.1"))


if __name__ == "__main__":
    unittest.main()
