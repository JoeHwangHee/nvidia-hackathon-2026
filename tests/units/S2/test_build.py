"""단위 S2(snapshot_build) 보조 시험: 수집기 행과의 일치, 행 규칙, 승격 불변식, 결정성, 덮어쓰기 금지, 변조 탐지,
원천 불변, 정본 옮기기. 입력 원천은 fixture_snapshot.py가 기존 수집기 코드로 만든다(합성 값).
"""
import copy
import hashlib
import json
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tradesentry.contract import types
from tradesentry.contract.policy_load import parse_policy
from tradesentry.snapshot import build

from . import fixture_snapshot as fx

PROMOTE = parse_policy(fx.TEST_POLICY)
NO_PROMOTE = parse_policy({**fx.TEST_POLICY, "confirmed_no_trade": None})


def tree_hashes(folder: Path) -> dict:
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file()}


def rows_of(path: Path) -> list[tuple]:
    con = sqlite3.connect(path)
    try:
        return con.execute("SELECT rowid, " + ", ".join(types.OBSERVATION_COLUMNS)
                           + " FROM observation ORDER BY rowid").fetchall()
    finally:
        con.close()


class BuildTestBase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.source = fx.make_source(self.root / "snapshots")
        self.csv = fx.write_peer_group_csv(self.root / "peer_group.csv")
        self.out = self.root / "out"
        self.out.mkdir()

    def build(self, stamp: str = "260925000000", policy=NO_PROMOTE, peers=True, source=None) -> dict:
        return build.build_snapshot(fx.SNAPSHOT_ID, out_dir=self.out, stamp=stamp,
                                    source_dir=self.source if source is None else source, policy=policy,
                                    peer_group_files=[self.csv] if peers else [])


class RowRuleTest(BuildTestBase):
    def test_rows_equal_collector_rows_except_not_collected(self):
        record = self.build(peers=False)
        built = rows_of(self.out / record["build_file"])
        self.assertEqual([r[0] for r in built], list(range(1, len(built) + 1)))  # rowid는 1부터 빈틈없이
        collector = fx.collector_rows(self.source)
        c = {name: i + 1 for i, name in enumerate(types.OBSERVATION_COLUMNS)}
        pk = lambda r: tuple(r[c[k]] for k in ("request_id", "month", "partner_code", "hs_code", "flow"))  # noqa: E731
        rest = lambda r: tuple(r[c[k]] for k in ("snapshot_id", "partner_namespace", "hs_level", "hs_version",  # noqa: E731
                                                 "amount_usd", "net_weight_kg", "observation_status", "raw_file_id",
                                                 "raw_row_locator", "item_name"))
        collected = {pk(r): rest(r) for r in built if r[c["observation_status"]] != types.NOT_COLLECTED}
        self.assertEqual(collected, collector)  # 같은 raw 응답을 받은 수집기와 행이 같다
        not_collected = [r for r in built if r[c["observation_status"]] == types.NOT_COLLECTED]
        self.assertEqual({(r[c["partner_code"]], r[c["hs_code"]]) for r in not_collected}, {("DE", "850450")})
        # manifest 순서: 요청마다 행이 한 덩어리로 이어지고, 덩어리 순서가 manifest 요청 순서다
        manifest = json.loads((self.source / "manifest.json").read_text(encoding="utf-8"))
        order = list(dict.fromkeys(r[c["request_id"]] for r in built))
        self.assertEqual(order, [r["request_id"] for r in manifest["requests"]])

    def test_status_rows_and_values(self):
        record = self.build(policy=PROMOTE)
        built = rows_of(self.out / record["build_file"])
        c = {name: i + 1 for i, name in enumerate(types.OBSERVATION_COLUMNS)}
        statuses = {r[c["observation_status"]] for r in built}
        self.assertEqual(statuses, set(types.OBSERVATION_STATUSES))  # 관측 상태 다섯 가지가 모두 나온다
        for r in built:
            with self.subTest(rowid=r[0]):
                if r[c["observation_status"]] == types.OBSERVED:
                    self.assertIsInstance(r[c["amount_usd"]], int)
                else:
                    self.assertIsNone(r[c["amount_usd"]])  # 빈 응답·실패·미수집·승격 행은 값을 채우지 않는다
                    self.assertIsNone(r[c["net_weight_kg"]])
        us = [r for r in built if r[c["partner_code"]] == "US"]
        self.assertEqual(len(us), 8)
        self.assertEqual(us[0][0], len(built) - 7)  # 계획 밖 비교국 행은 맨 끝
        self.assertEqual([r[c["flow"]] for r in us[:2]], ["import", "export"])

    def test_total_rows_keep_request_code(self):
        record = self.build(peers=False)
        c = {name: i + 1 for i, name in enumerate(types.OBSERVATION_COLUMNS)}
        totals = [r for r in rows_of(self.out / record["build_file"]) if r[c["month"]].startswith("RAW:")]
        self.assertTrue(totals)
        self.assertEqual({r[c["month"]] for r in totals}, {"RAW:총계"})
        self.assertTrue(all(r[c["hs_level"]] == len(r[c["hs_code"]]) for r in totals))


class PromotionTest(BuildTestBase):
    def test_promotion_changes_status_only(self):
        plain = rows_of(self.out / self.build("260925000000", NO_PROMOTE)["build_file"])
        record = self.build("260925000001", PROMOTE)
        promoted = rows_of(self.out / record["build_file"])
        self.assertEqual(len(plain), len(promoted))
        c = {name: i + 1 for i, name in enumerate(types.OBSERVATION_COLUMNS)}
        changed = [(a, b) for a, b in zip(plain, promoted) if a != b]
        self.assertEqual(len(changed), record["confirmed_no_trade_rows"])
        self.assertEqual(record["confirmed_no_trade_rows"], 1)
        before, after = changed[0]
        self.assertEqual(before[0], after[0])  # rowid 그대로
        self.assertEqual((before[c["observation_status"]], after[c["observation_status"]]),
                         (types.UNRESOLVED_ZERO, types.CONFIRMED_NO_TRADE))
        self.assertEqual((after[c["partner_code"]], after[c["hs_code"]], after[c["month"]], after[c["flow"]]),
                         ("JP", "850450", "202302", "import"))
        self.assertEqual([i for i in range(1, len(c) + 1) if before[i] != after[i]], [c["observation_status"]])

    def test_unknown_rule_is_refused(self):
        with self.assertRaises(build.BuildError):
            build.apply_promotion([], {"rule": "all_empty_months"})


class DeterminismTest(BuildTestBase):
    def test_same_inputs_give_same_normalized_hash(self):
        first = self.build("260925000000", PROMOTE)
        second = self.build("260925000001", PROMOTE)
        self.assertEqual(first["normalized_sha256"], second["normalized_sha256"])
        self.assertEqual(first["normalized_sha256"],
                         fx.independent_normalized_sha256(self.out / first["build_file"]))
        other = self.build("260925000002", NO_PROMOTE)
        self.assertNotEqual(first["normalized_sha256"], other["normalized_sha256"])  # 승격은 해시를 바꾼다

    def test_rowid_change_changes_hash(self):
        record = self.build()
        path = self.out / record["build_file"]
        copy_path = self.root / "copy.sqlite"
        shutil.copyfile(path, copy_path)
        con = sqlite3.connect(copy_path)
        con.execute("UPDATE observation SET rowid = rowid + 1000 WHERE rowid = 1")  # 값은 그대로, rowid만 바꾼다
        con.commit()
        con.close()
        self.assertNotEqual(build.file_normalized_sha256(copy_path), record["normalized_sha256"])

    def test_record_and_database_have_no_local_paths(self):
        record = self.build()
        text = (self.out / f"snapshot_build-{'260925000000'}.json").read_text(encoding="utf-8")
        blob = (self.out / record["build_file"]).read_bytes()
        for local in (str(self.root), str(self.root.resolve()), str(Path.home()), tempfile.gettempdir()):
            self.assertNotIn(local, text)
            self.assertNotIn(local.encode("utf-8"), blob)


class SafetyTest(BuildTestBase):
    def test_existing_files_are_not_overwritten(self):
        self.build()
        with self.assertRaises(FileExistsError):
            self.build()
        target = self.root / "exists.sqlite"
        target.write_bytes(b"keep")
        with self.assertRaises(FileExistsError):
            build.write_snapshot_db(target, meta={}, receipts=[], observations=[], peer_groups=[])
        self.assertEqual(target.read_bytes(), b"keep")

    def test_source_files_are_not_changed(self):
        before = tree_hashes(self.source)
        self.build(policy=PROMOTE)
        self.assertEqual(tree_hashes(self.source), before)
        self.assertFalse(any(p.name.endswith(("-journal", "-wal", "-shm")) for p in self.source.iterdir()))

    def test_tampering_is_detected(self):
        cases = {}

        def raw_byte(folder):
            path = next(p for p in sorted((folder / "raw").glob("*.xml")) if b"<impDlr>600<" in p.read_bytes())
            path.write_bytes(path.read_bytes().replace(b"<impDlr>600<", b"<impDlr>601<"))
        cases["raw 바이트"] = raw_byte

        def extra_raw(folder):
            (folder / "raw" / "0000000000000000.xml").write_bytes(b"<x/>")
        cases["raw 파일 추가"] = extra_raw

        def hash_record(folder):
            record = json.loads((folder / "snapshot_hash.json").read_text(encoding="utf-8"))
            record["raw_combined_sha256"] = "0" * 64
            (folder / "snapshot_hash.json").write_text(json.dumps(record), encoding="utf-8")
        cases["snapshot_hash.json"] = hash_record

        def extra_receipt(folder):
            con = sqlite3.connect(folder / "snapshot.sqlite")
            con.execute("INSERT INTO collection_receipt(request_id, endpoint, params_json, status) "
                        "VALUES('ffffffffffffffff', 'nitemtrade', '{}', 'OK')")
            con.commit()
            con.close()
        cases["계획 밖 수신 기록"] = extra_receipt

        def manifest_id(folder):
            manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
            manifest["requests"][0]["request_id"] = "0" * 16
            (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        cases["manifest request_id"] = manifest_id

        for index, (name, tamper) in enumerate(cases.items()):
            with self.subTest(name):
                folder = self.root / f"tampered{index}" / fx.SNAPSHOT_ID
                shutil.copytree(self.source, folder)
                tamper(folder)
                with self.assertRaises(build.BuildError):
                    self.build(stamp=f"2609250001{index:02d}", source=folder)

    def test_peer_group_csv_rules(self):
        bad = {
            "열": fx.PEER_GROUP_CSV.replace("similarity", "sim", 1),
            "scope": fx.PEER_GROUP_CSV.replace(",hs6,850450,1,", ",hs6,8504,1,", 1),
            "대상국": fx.PEER_GROUP_CSV.replace("exporter_country,CN,", "exporter_country,TH,", 1),
            "순위": fx.PEER_GROUP_CSV.replace(",850450,1,JP,", ",850450,0,JP,", 1),
            "유사도": fx.PEER_GROUP_CSV.replace("0.8300", "high", 1),
        }
        for index, (name, text) in enumerate(bad.items()):
            with self.subTest(name):
                path = self.root / f"bad{index}.csv"
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(build.BuildError):
                    build.build_snapshot(fx.SNAPSHOT_ID, out_dir=self.out, stamp=f"2609250002{index:02d}",
                                         source_dir=self.source, peer_group_files=[path])


class InstallTest(BuildTestBase):
    def test_install_moves_build_without_overwriting(self):
        record = self.build(policy=PROMOTE)
        build_file = self.out / record["build_file"]
        snapshot_dir = self.root / "frozen" / fx.SNAPSHOT_ID
        snapshot_dir.mkdir(parents=True)
        (snapshot_dir / "snapshot.sqlite").write_bytes(b"collector")  # 수집기 파일은 건드리지 않는다
        installed = build.install_build(build_file, snapshot_dir)
        target = snapshot_dir / build.BUILD_FILE
        self.assertTrue(target.is_file())
        self.assertFalse(build_file.exists())  # os.link 뒤 원본을 지웠다(옮기기)
        self.assertEqual(build.file_normalized_sha256(target), record["normalized_sha256"])
        saved = json.loads((snapshot_dir / build.BUILD_RECORD).read_text(encoding="utf-8"))
        self.assertEqual(saved["normalized_sha256"], record["normalized_sha256"])
        self.assertEqual(saved, installed)
        self.assertEqual((snapshot_dir / "snapshot.sqlite").read_bytes(), b"collector")
        second = self.build("260925000009", PROMOTE)
        with self.assertRaises(FileExistsError):
            build.install_build(self.out / second["build_file"], snapshot_dir)
        self.assertTrue((self.out / second["build_file"]).exists())

    def test_install_refuses_mismatched_record_or_folder(self):
        record = self.build(policy=PROMOTE)
        build_file = self.out / record["build_file"]
        wrong = self.root / "frozen" / "other_snapshot"
        wrong.mkdir(parents=True)
        with self.assertRaises(build.BuildError):
            build.install_build(build_file, wrong)
        record_path = build_file.with_suffix(".json")
        changed = copy.deepcopy(record)
        changed["normalized_sha256"] = "0" * 64
        record_path.chmod(0o644)
        record_path.unlink()
        record_path.write_text(json.dumps(changed), encoding="utf-8")
        right = self.root / "frozen" / fx.SNAPSHOT_ID
        right.mkdir(parents=True)
        with self.assertRaises(build.BuildError):
            build.install_build(build_file, right)
        self.assertEqual(list(right.iterdir()), [])


class RunTest(BuildTestBase):
    def test_run_with_policy_version_and_repo_relative_peer_file(self):
        with mock.patch.object(build, "SNAPSHOTS_ROOT", self.source.parent), \
                mock.patch.object(build, "REPO_ROOT", self.root):
            data = build.run({"snapshot_id": fx.SNAPSHOT_ID, "policy_version": "dev-0.1",
                              "peer_group_files": ["peer_group.csv"]})
        path = self.root / "run.sqlite"
        path.write_bytes(data)
        c = {name: i + 1 for i, name in enumerate(types.OBSERVATION_COLUMNS)}
        statuses = {r[c["observation_status"]] for r in rows_of(path)}
        self.assertNotIn(types.CONFIRMED_NO_TRADE, statuses)  # dev-0.1에는 승격 규칙이 없다
        self.assertIn(types.UNRESOLVED_ZERO, statuses)

    def test_run_input_errors(self):
        for bad in ({}, {"snapshot_id": "x", "policy": {}, "policy_version": "dev-0.1"}, {"snapshot_id": "x", "y": 1},
                    []):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                build.run(bad)
        with self.assertRaises(build.BuildError):
            build.run({"snapshot_id": "../x"})


if __name__ == "__main__":
    unittest.main()
