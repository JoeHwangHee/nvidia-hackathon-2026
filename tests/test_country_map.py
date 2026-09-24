"""단위 G3(국가 코드 대응표, 구성 단위) 시험: data/reference/country_map.csv.

구성 단위라 진입 함수·골든 쌍이 없다(docs/plan/UNITS.md §3.5). 이 시험이 파일을 저장소에 커밋된 원천과 대조한다.
- 관세청 2자리 국가코드(cntyCd) ↔ BACI 국가 코드 ↔ BACI iso3 자리(대만은 S19). 결정 기록 S0 ⑤(파일 위치),
  개발 플랜 §8.2(대만 주석), 분담 D3.
- 행은 수집 설정 configs/collection_plan.json의 상대국 16개(superset)와 같다.
- 원천: data/reference/partner_superset_2023.json(cntyCd·BACI 코드·iso3), data/reference/baci_hs22_v202601_kr_imports_ch85.csv
  (BACI 수출국 코드·iso3·이름), data/reference/kcs_country_codes.json(관세청 조회코드의 국가명).
"""
import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP_FILE = ROOT / "data" / "reference" / "country_map.csv"
HEADER = ["cntyCd", "baci_country_code", "baci_country_iso3", "kcs_country_name", "baci_country_name", "note"]


def read_map() -> list[dict]:
    with open(MAP_FILE, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == HEADER, reader.fieldnames
        return list(reader)


class CountryMapTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.rows = read_map()

    def test_file_format(self):
        raw = MAP_FILE.read_bytes()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))  # BOM 없음
        self.assertNotIn(b"\r", raw)
        self.assertEqual([row["cntyCd"] for row in self.rows], sorted(row["cntyCd"] for row in self.rows))

    def test_rows_are_the_collection_superset(self):
        plan = json.loads((ROOT / "configs" / "collection_plan.json").read_text(encoding="utf-8"))
        self.assertEqual({row["cntyCd"] for row in self.rows}, set(plan["partners"]))
        self.assertEqual(len(self.rows), 16)

    def test_codes_match_committed_sources(self):
        superset = json.loads((ROOT / "data" / "reference" / "partner_superset_2023.json").read_text(encoding="utf-8"))
        expected = {}
        for entries in superset["per_hs4"].values():
            for entry in entries:
                expected.setdefault(entry["kcs"], set()).add((entry["baci_code"], entry["iso3"]))
        baci = {}
        with open(ROOT / "data" / "reference" / "baci_hs22_v202601_kr_imports_ch85.csv", encoding="utf-8") as fh:
            for record in csv.DictReader(fh):
                baci.setdefault(record["i_code"], set()).add((record["i_iso3"], record["i_name"]))
        kcs = dict(tuple(pair) for pair in json.loads(
            (ROOT / "data" / "reference" / "kcs_country_codes.json").read_text(encoding="utf-8"))[3:])
        for row in self.rows:
            with self.subTest(cntyCd=row["cntyCd"]):
                self.assertEqual(expected[row["cntyCd"]], {(row["baci_country_code"], row["baci_country_iso3"])})
                self.assertEqual(baci[row["baci_country_code"]], {(row["baci_country_iso3"], row["baci_country_name"])})
                self.assertEqual(kcs[row["cntyCd"]], row["kcs_country_name"])
        self.assertEqual(len({row["baci_country_code"] for row in self.rows}), 16)  # 코드가 겹치지 않는다

    def test_taiwan_note(self):
        taiwan = [row for row in self.rows if row["cntyCd"] == "TW"]
        self.assertEqual(len(taiwan), 1)
        self.assertEqual((taiwan[0]["baci_country_code"], taiwan[0]["baci_country_iso3"]), ("490", "S19"))
        self.assertIn("BACI 490", taiwan[0]["note"])
        self.assertIn("대만 외 기타 아시아 미상분이 섞일 수 있다", taiwan[0]["note"])
        self.assertEqual([row["cntyCd"] for row in self.rows if row["note"]], ["TW"])


if __name__ == "__main__":
    unittest.main()
