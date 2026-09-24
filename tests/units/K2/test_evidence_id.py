"""단위 K2(contract_evidence_id) 보조 시험: 골든 쌍 밖의 경계(만들기 거부, 왕복, 확인 함수 호출 순서)."""
import unittest

from tradesentry.contract import evidence_id as k2


class FormatTest(unittest.TestCase):
    def test_round_trip(self):
        for snapshot_id, table, rowid in (("kcs_202201_202412_v2", "observation", 1), ("s", "peer_group", 2 ** 63 - 1)):
            text = k2.format_evidence_id(snapshot_id, table, rowid)
            self.assertEqual(k2.parse_evidence_id(text), k2.EvidenceRef(snapshot_id, table, rowid))
            self.assertEqual(k2.EvidenceRef(snapshot_id, table, rowid).evidence_id(), text)

    def test_format_rejects_bad_pieces(self):
        bad = [("", "observation", 1), ("a:b", "observation", 1), ("s", "", 1), ("s", "ob:s", 1), ("s", "observation", 0),
               ("s", "observation", -1), ("s", "observation", True), ("s", "observation", "1"),
               ("s", "observation", 2 ** 63), (None, "observation", 1)]
        for args in bad:
            with self.subTest(args=args), self.assertRaises(ValueError):
                k2.format_evidence_id(*args)

    def test_parse_errors_carry_rule(self):
        cases = {"ev:a:b": 1, "ev:a:b:c:1": 1, "xx:a:b:1": 1, "ev::b:1": 2, "ev:a::1": 3, "ev:a:b:": 4, "ev:a:b:+1": 4,
                 "ev:a:b: 1": 4, "ev:a:b:1.0": 4, "ev:a:b:١": 4}
        for text, rule in cases.items():
            with self.subTest(text=text), self.assertRaises(k2.EvidenceIdError) as cm:
                k2.parse_evidence_id(text)
            self.assertEqual(cm.exception.rule, rule)
        with self.assertRaises(k2.EvidenceIdError) as cm:
            k2.parse_evidence_id(None)
        self.assertEqual(cm.exception.rule, 1)


class ResolveTest(unittest.TestCase):
    def test_checks_run_in_rule_order(self):
        calls = []

        def has_table(table):
            calls.append(("table", table))
            return table == "observation"

        def has_row(table, rowid):
            calls.append(("row", table, rowid))
            return rowid == 7

        ok = k2.resolve_evidence_id("ev:s:observation:7", "s", has_table=has_table, has_row=has_row)
        self.assertEqual(ok, {"evidence_id": "ev:s:observation:7", "resolved": True, "failed_rule": None})
        self.assertEqual(calls, [("table", "observation"), ("row", "observation", 7)])
        calls.clear()
        wrong_snapshot = k2.resolve_evidence_id("ev:t:observation:7", "s", has_table=has_table, has_row=has_row)
        self.assertEqual(wrong_snapshot["failed_rule"], 2)
        self.assertEqual(calls, [])  # 스냅샷이 다르면 테이블·행을 찾지 않는다
        no_table = k2.resolve_evidence_id("ev:s:receipt:7", "s", has_table=has_table, has_row=has_row)
        self.assertEqual(no_table["failed_rule"], 3)
        self.assertNotIn(("row", "receipt", 7), calls)  # 테이블이 없으면 행을 찾지 않는다
        self.assertEqual(k2.resolve_evidence_id("ev:s:observation:8", "s", has_table=has_table,
                                                has_row=has_row)["failed_rule"], 4)

    def test_huge_rowid_does_not_reach_lookup(self):
        def has_row(table, rowid):
            raise AssertionError("2^63 이상 rowid로 행을 찾으면 SQLite 바인딩이 넘친다")

        result = k2.resolve_evidence_id("ev:s:observation:99999999999999999999", "s",
                                        has_table=lambda t: True, has_row=has_row)
        self.assertEqual(result["failed_rule"], 4)

    def test_run_rejects_unknown_input(self):
        for bad in ({"table": "observation"}, 5, None, {"evidence_id": "ev:s:o:1", "rows": [1]}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                k2.run(bad)


if __name__ == "__main__":
    unittest.main()
