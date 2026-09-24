"""단위 G1(grouping_g0) 규칙 시험: 선택 규칙의 성질, params_hash 규칙, 입력 검사, CSV 형식.

골든 쌍(input.json·expected.json)은 합성 입력이다. 여기서도 합성 값만 쓴다. 네트워크·키·파일 없이 돈다.
"""
import copy
import csv
import hashlib
import io
import json
import unittest
from decimal import Decimal
from pathlib import Path

from tradesentry.grouping import g0

GOLDEN_INPUT = Path(__file__).resolve().parent / "input.json"


def golden_input() -> dict:
    return json.loads(GOLDEN_INPUT.read_text(encoding="utf-8"))


def peers_by_target(rows: list[dict]) -> dict[tuple[str, str], list[str]]:
    found: dict[tuple[str, str], list[str]] = {}
    for row in rows:
        found.setdefault((row["scope_id"], row["entity_id"]), []).append(row["peer_id"])
    return found


class SelectionRuleTest(unittest.TestCase):
    def test_every_target_gets_k_distinct_peers_without_itself(self):
        inp = golden_input()
        rows = g0.run(inp)
        self.assertEqual(len(rows), len(inp["hs6_codes"]) * len(inp["candidates"]) * inp["k"])
        for (hs6, target), peers in peers_by_target(rows).items():
            with self.subTest(hs6=hs6, target=target):
                self.assertEqual(len(peers), inp["k"])
                self.assertEqual(len(set(peers)), inp["k"])
                self.assertNotIn(target, peers)
                self.assertLessEqual(set(peers), set(inp["candidates"]))
        ranks = [(r["scope_id"], r["entity_id"], r["peer_rank"]) for r in rows]
        self.assertEqual(ranks, sorted(ranks))  # 행 순서: (scope_id, entity_id, peer_rank) 오름차순

    def test_item_without_any_record_uses_code_order(self):
        inp = golden_input()
        inp["hs6_codes"].append("850432")  # 기록이 하나도 없는 품목: 모두 합 0이라 사전순으로 고른다
        peers = peers_by_target(g0.run(inp))
        self.assertEqual(peers[("850432", "CN")], ["DE", "JP", "PH", "TW", "US"])
        self.assertEqual(peers[("850432", "DE")], ["CN", "JP", "PH", "TW", "US"])
        self.assertEqual(peers[("850432", "VN")], ["CN", "DE", "JP", "PH", "TW"])

    def test_missing_record_and_explicit_zero_tie_by_code(self):
        inp = golden_input()
        # 850450: PH는 기록 없음, US는 합 0(명시). 둘 다 0이라 코드 사전순으로 PH가 앞선다.
        self.assertEqual(peers_by_target(g0.run(inp))[("850450", "CN")][-1], "PH")
        inp["import_value_sums"].append({"hs6": "850450", "partner": "PH", "amount_usd": 0})
        self.assertEqual(peers_by_target(g0.run(inp))[("850450", "CN")][-1], "PH")  # 기록 없음과 명시 0은 같다
        inp["import_value_sums"][-1]["amount_usd"] = 400  # 금액이 생기면 순위가 금액을 따른다
        self.assertEqual(peers_by_target(g0.run(inp))[("850450", "CN")], ["DE", "JP", "VN", "PH", "TW"])

    def test_input_order_does_not_change_output(self):
        inp = golden_input()
        shuffled = copy.deepcopy(inp)
        shuffled["candidates"].reverse()
        shuffled["hs6_codes"].reverse()
        shuffled["import_value_sums"].reverse()
        self.assertEqual(g0.run(shuffled), g0.run(inp))

    def test_run_does_not_change_its_input(self):
        inp = golden_input()
        before = copy.deepcopy(inp)
        g0.run(inp)
        self.assertEqual(inp, before)

    def test_fixed_field_values(self):
        row = g0.run(golden_input())[0]
        self.assertEqual(tuple(row), g0.PEER_GROUP_FIELDS)
        self.assertEqual((row["entity_type"], row["entity_namespace"], row["scope_type"], row["method"],
                          row["grouping_version"]),
                         ("exporter_country", "KCS_cntyCd", "hs6", "import_value_topk", "g0"))
        self.assertIsNone(row["similarity"])
        self.assertIsNone(row["community_id"])
        self.assertIs(type(row["peer_rank"]), int)
        self.assertIs(type(row["source_year"]), int)


class ParamsHashTest(unittest.TestCase):
    def test_rule(self):
        inp = golden_input()
        text = json.dumps({"candidates": sorted(inp["candidates"]), "k": 5, "source_year": 2023},
                          sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        self.assertEqual(text, '{"candidates":["CN","DE","JP","PH","TW","US","VN"],"k":5,"source_year":2023}')
        expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
        self.assertEqual(g0.compute_params_hash(5, 2023, inp["candidates"]), expected)
        self.assertEqual({row["params_hash"] for row in g0.run(inp)}, {expected})

    def test_depends_on_k_year_and_candidate_set_only(self):
        base = g0.compute_params_hash(5, 2023, ["CN", "JP", "DE"])
        self.assertEqual(g0.compute_params_hash(5, 2023, ["DE", "CN", "JP"]), base)
        self.assertNotEqual(g0.compute_params_hash(4, 2023, ["CN", "JP", "DE"]), base)
        self.assertNotEqual(g0.compute_params_hash(5, 2022, ["CN", "JP", "DE"]), base)
        self.assertNotEqual(g0.compute_params_hash(5, 2023, ["CN", "JP", "US"]), base)


class InputCheckTest(unittest.TestCase):
    def assert_rejected(self, change) -> None:
        inp = golden_input()
        change(inp)
        with self.assertRaises(ValueError):
            g0.run(inp)

    def test_not_an_object_or_wrong_keys(self):
        with self.assertRaises(ValueError):
            g0.run([])
        self.assert_rejected(lambda inp: inp.pop("generated_at"))
        self.assert_rejected(lambda inp: inp.update(extra=1))

    def test_too_few_candidates_for_k(self):
        self.assert_rejected(lambda inp: inp.update(k=7))  # 후보국 7개면 대상국을 빼고 6개뿐이다
        inp = golden_input()
        inp["k"] = 6
        self.assertEqual(len(g0.run(inp)), 2 * 7 * 6)

    def test_bad_scalars(self):
        self.assert_rejected(lambda inp: inp.update(k=True))
        self.assert_rejected(lambda inp: inp.update(k=0))
        self.assert_rejected(lambda inp: inp.update(source_year="2023"))
        self.assert_rejected(lambda inp: inp.update(source_version=""))
        self.assert_rejected(lambda inp: inp.update(input_sha256="ABC"))
        self.assert_rejected(lambda inp: inp.update(generated_at="2026-09-25T01:00:00"))  # 시간대 없음
        self.assert_rejected(lambda inp: inp.update(generated_at="2026-09-24T16:00:00+00:00"))  # KST 아님
        self.assert_rejected(lambda inp: inp.update(generated_at="어제"))

    def test_bad_lists(self):
        self.assert_rejected(lambda inp: inp["candidates"].append("CN"))
        self.assert_rejected(lambda inp: inp["candidates"].append("ALL"))
        self.assert_rejected(lambda inp: inp["candidates"].append("kr"))
        self.assert_rejected(lambda inp: inp.update(hs6_codes=[]))
        self.assert_rejected(lambda inp: inp["hs6_codes"].append("8504"))
        self.assert_rejected(lambda inp: inp["hs6_codes"].append("850450"))

    def test_bad_sum_records(self):
        def add(record):
            return lambda inp: inp["import_value_sums"].append(record)

        self.assert_rejected(add({"hs6": "850450", "partner": "CN", "amount_usd": 1}))  # 같은 (HS6, 나라) 두 번
        self.assert_rejected(add({"hs6": "850490", "partner": "PH", "amount_usd": 1}))  # hs6_codes에 없는 품목
        self.assert_rejected(add({"hs6": "850450", "partner": "MX", "amount_usd": 1}))  # 후보국이 아닌 나라
        self.assert_rejected(add({"hs6": "850450", "partner": "PH", "amount_usd": None}))
        self.assert_rejected(add({"hs6": "850450", "partner": "PH", "amount_usd": -1}))
        self.assert_rejected(add({"hs6": "850450", "partner": "PH", "amount_usd": True}))
        self.assert_rejected(add({"hs6": "850450", "partner": "PH", "amount_usd": 1.5}))
        self.assert_rejected(add({"hs6": "850450", "partner": "PH", "amount_usd": Decimal("1")}))
        self.assert_rejected(add({"hs6": "850450", "partner": "PH"}))


class CsvTest(unittest.TestCase):
    def test_header_nulls_and_line_ends(self):
        rows = g0.run(golden_input())
        text = g0.to_csv(rows)
        lines = text.split("\n")
        self.assertEqual(lines[0], ",".join(g0.PEER_GROUP_FIELDS))
        self.assertEqual(lines[-1], "")  # 마지막 줄도 LF로 끝난다
        self.assertEqual(len(lines), len(rows) + 2)
        self.assertNotIn("\r", text)
        self.assertEqual(lines[1].split(","),
                         ["exporter_country", "CN", "KCS_cntyCd", "hs6", "850431", "1", "TW", "null", "null",
                          "import_value_topk", "g0", rows[0]["params_hash"], "kcs_202201_202412_v2", "2023",
                          "0123456789abcdef" * 4, "2026-09-25T01:00:00+09:00"])

    def test_reads_back_to_the_same_rows(self):
        rows = g0.run(golden_input())
        back = list(csv.DictReader(io.StringIO(g0.to_csv(rows))))
        as_text = [{k: ("null" if v is None else str(v)) for k, v in row.items()} for row in rows]
        self.assertEqual(back, as_text)

    def test_rejects_rows_that_are_not_peer_group_rows(self):
        row = g0.run(golden_input())[0]
        reordered = {key: row[key] for key in reversed(g0.PEER_GROUP_FIELDS)}
        with self.assertRaises(ValueError):
            g0.to_csv([reordered])
        with self.assertRaises(ValueError):
            g0.to_csv([{**row, "extra": 1}])
        with self.assertRaises(ValueError):
            g0.to_csv([{**row, "similarity": 0.5}])


if __name__ == "__main__":
    unittest.main()
