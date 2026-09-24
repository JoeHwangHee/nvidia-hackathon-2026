"""단위 K3(dal_query) 보조 시험: 상태별 월 값, HS10 하위 상태, 비교국, 범위 밖 조회, 열기 거부, 읽기 전용, 행 규칙 6
충돌, 개발 빌드 경로. 자료는 tests/units/S2/fixture_snapshot.py의 합성 원천을 단위 S2로 빌드한 것이다.
"""
import shutil
import sqlite3
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

from tradesentry.contract import types
from tradesentry.dal import query

from ..S2 import fixture_snapshot as fx

EV = "ev:unit_fixture_s2:observation:"


class QueryTestBase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.build_file = fx.install_fixture_build(self.root)
        patcher = mock.patch.object(query, "SNAPSHOTS_ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.snap = query.open_snapshot(fx.SNAPSHOT_ID)
        self.addCleanup(self.snap.close)


class MonthValueTest(QueryTestBase):
    def test_parent_values_with_failed_children_like_oracle_c(self):
        cn = self.snap.parent_series("850450", "CN")
        self.assertEqual([(v["amount_usd"], v["net_weight_kg"], v["observation_status"]) for v in cn],
                         [(600, 100, types.OBSERVED), (360, 100, types.OBSERVED)])
        kids = self.snap.children("850450", "CN", "202302")
        self.assertEqual((kids["rows"], kids["observation_status"]), ([], types.REQUEST_FAILED))
        self.assertEqual([m["evidence_id"] for m in kids["missingness"]], [EV + "39"])
        self.assertEqual(kids["missingness"][0]["hs_code"], "850450")

    def test_missing_parent_lists_status_rows_source_request_first(self):
        de = self.snap.parent("850450", "DE", "202302")
        self.assertIsNone(de["amount_usd"])
        self.assertEqual(de["evidence_ids"], [])
        self.assertEqual([(m["hs_code"], m["observation_status"]) for m in de["missingness"]],
                         [("8504", types.UNRESOLVED_ZERO), ("850450", types.NOT_COLLECTED)])
        self.assertEqual(de["observation_status"], types.UNRESOLVED_ZERO)  # 원천 요청(HS4 스캔)의 상태
        self.assertEqual(self.snap.children("850450", "DE", "202301")["observation_status"], types.NOT_COLLECTED)

    def test_out_of_plan_peer_is_not_collected(self):
        us = self.snap.parent_series("850450", "US")
        self.assertEqual({v["observation_status"] for v in us}, {types.NOT_COLLECTED})
        self.assertEqual([m["hs_code"] for m in us[0]["missingness"]], ["8504", "850450"])
        self.assertEqual(self.snap.scope()["other_partners"], ["US"])

    def test_share_inputs(self):
        """점유율 입력(분자 부모 HS6 행, 분모 ALL HS10 합)을 DAL로 읽으면 합성 값 그대로다(계산은 지표 단위가 한다)."""
        numerator = self.snap.parent("850450", "CN", "202301")
        denominator = self.snap.world("850450", "202301")
        self.assertEqual((numerator["amount_usd"], denominator["amount_usd"]), (600, 2000))
        self.assertEqual(denominator["hs10_codes"], ["8504501000", "8504509000"])
        self.assertFalse(any(self.snap.row("observation", int(e.rsplit(":", 1)[1]))["month"].startswith("RAW:")
                             for e in denominator["evidence_ids"] + numerator["evidence_ids"]))

    def test_confirmed_no_trade_is_not_missing(self):
        jp = self.snap.parent("850450", "JP", "202302")
        self.assertEqual((jp["observation_status"], jp["missingness"]), (types.CONFIRMED_NO_TRADE, []))
        self.assertEqual(self.snap.row("observation", 47)["flow"], "import")


class PeerTest(QueryTestBase):
    def test_g0_peers_in_rank_order(self):
        peers = self.snap.peers("850450", "CN", "g0")
        self.assertEqual([(p["peer_rank"], p["peer_id"]) for p in peers], [(1, "JP"), (2, "DE"), (3, "US")])
        self.assertTrue(all(p["similarity"] is None and p["community_id"] is None for p in peers))
        self.assertEqual(self.snap.peers("850450", "DE", "g0"), [])
        g1 = self.snap.peers("850450", "JP", "g1")
        self.assertEqual(g1[0]["similarity"], Decimal("0.8300"))
        self.assertEqual(str(g1[0]["similarity"]), "0.8300")


class ScopeAndOpenTest(QueryTestBase):
    def test_scope_errors(self):
        calls = [lambda: self.snap.parent("850431", "CN", "202301"),  # 범위 밖 HS6(행은 있어도 분석 대상이 아니다)
                 lambda: self.snap.parent("850450", "TH", "202301"),
                 lambda: self.snap.parent("850450", "ALL", "202301"),
                 lambda: self.snap.parent("850450", "CN", "202303"),
                 lambda: self.snap.world("850450", "2023-01"),
                 lambda: self.snap.children("850450", "CN", "202212")]
        for index, call in enumerate(calls):
            with self.subTest(index=index), self.assertRaises(query.ScopeError):
                call()

    def test_open_refusals(self):
        with self.assertRaises(query.SnapshotError):
            query.open_snapshot("kcs_202201_202412_v2")  # 정본 빌드 파일이 없다
        with self.assertRaises(query.SnapshotError):
            query.open_snapshot("other", path=self.build_file)  # 메타의 snapshot_id가 다르다
        with self.assertRaises(query.SnapshotError):
            query.open_snapshot(fx.SNAPSHOT_ID, path=self.root / fx.SNAPSHOT_ID / "snapshot.sqlite")  # 수집기 SQLite
        with self.assertRaises(query.SnapshotError):
            query.open_snapshot("../x")

    def test_read_only(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.snap._con.execute("DELETE FROM observation")
        self.assertIsNone(self.snap.row("observation", 10 ** 6))
        with self.assertRaises(query.SnapshotError):
            self.snap.row("sqlite_master", 1)

    def test_development_build_path_and_recorded_hash(self):
        dev = self.root / "outputs" / "snapshot_build-260925000001"
        dev.mkdir(parents=True)
        shutil.copyfile(self.build_file, dev / "snapshot_build-260925000001.sqlite")
        with query.open_snapshot(fx.SNAPSHOT_ID, path=dev / "snapshot_build-260925000001.sqlite") as snap:
            self.assertIsNone(snap.snapshot_object()["normalized_sha256"])  # 옆에 빌드 기록이 없다
            self.assertEqual(snap.parent("850450", "JP", "202301")["amount_usd"], 300)
        recorded = self.snap.snapshot_object()["normalized_sha256"]
        self.assertRegex(recorded, r"^[0-9a-f]{64}$")

    def test_all_duplicate_conflict_is_an_error(self):
        broken = self.root / "broken.sqlite"
        shutil.copyfile(self.build_file, broken)
        con = sqlite3.connect(broken)
        con.execute("UPDATE observation SET amount_usd = amount_usd + 1 WHERE rowid = 55")  # HS6 조회 쪽 중복 행
        con.commit()
        con.close()
        with query.open_snapshot(fx.SNAPSHOT_ID, path=broken) as snap, self.assertRaises(query.SnapshotError):
            snap.world("850450", "202301")


if __name__ == "__main__":
    unittest.main()
