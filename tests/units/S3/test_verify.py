"""단위 S3(snapshot_verify) 보조 시험: 변조·잘못된 승격·WAL·기록 없음·raw 없음·다른 형식 파일을 잡는지, 개발 빌드 경로,
보고에 로컬 경로가 없는지. 자료는 tests/units/S2/fixture_snapshot.py의 합성 원천을 단위 S2로 빌드한 것이다.
"""
import json
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tradesentry.snapshot import build, verify

from ..S2 import fixture_snapshot as fx


def check(report: dict, name: str) -> bool | None:
    found = [c["ok"] for c in report["checks"] if c["name"] == name]
    return found[0] if found else "없음"


class VerifyTestBase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.build_file = fx.install_fixture_build(self.root)
        self.source = self.build_file.parent
        patcher = mock.patch.object(build, "SNAPSHOTS_ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)

    def dev_copy(self, name: str = "snapshot_build-260925000005", with_record: bool = True) -> Path:
        folder = self.root / "outputs" / name
        folder.mkdir(parents=True)
        target = folder / f"{name}.sqlite"
        shutil.copyfile(self.build_file, target)
        if with_record:
            shutil.copyfile(self.build_file.with_suffix(".json"), target.with_suffix(".json"))
        return target

    def edit(self, path: Path, sql: str) -> None:
        con = sqlite3.connect(path)
        con.execute(sql)
        con.commit()
        con.close()


class PassingTest(VerifyTestBase):
    def test_canonical_and_development_builds_pass(self):
        canonical = verify.verify_snapshot(fx.SNAPSHOT_ID)
        self.assertTrue(canonical["ok"], canonical["checks"])
        dev = verify.run({"snapshot_id": fx.SNAPSHOT_ID, "build_file": str(self.dev_copy(with_record=False))})
        self.assertTrue(dev["ok"])
        self.assertIsNone(check(dev, "normalized_sha256_record"))  # 개발 빌드에 기록이 없으면 건너뛴다
        self.assertEqual(dev["normalized_sha256"], canonical["normalized_sha256"])

    def test_report_has_no_local_paths(self):
        text = json.dumps(verify.verify_snapshot(fx.SNAPSHOT_ID, build_file=self.root / "missing.sqlite"),
                          ensure_ascii=False)
        text += json.dumps(verify.verify_snapshot(fx.SNAPSHOT_ID, source_dir=self.root / "nowhere"), ensure_ascii=False)
        for local in (str(self.root), str(self.root.resolve()), str(Path.home()), tempfile.gettempdir()):
            self.assertNotIn(local, text)


class FailingTest(VerifyTestBase):
    def test_value_tampering(self):
        target = self.dev_copy()
        self.edit(target, "UPDATE observation SET amount_usd = 601 WHERE rowid = 3")
        report = verify.verify_snapshot(fx.SNAPSHOT_ID, build_file=target)
        self.assertFalse(report["ok"])
        self.assertFalse(check(report, "observation_matches_raw"))
        self.assertFalse(check(report, "normalized_sha256_record"))

    def test_unapproved_promotion(self):
        target = self.dev_copy()
        self.edit(target, "UPDATE observation SET observation_status = 'CONFIRMED_NO_TRADE' WHERE rowid = 48")
        report = verify.verify_snapshot(fx.SNAPSHOT_ID, build_file=target)
        self.assertFalse(check(report, "observation_matches_raw"))

    def test_wal_mode(self):
        target = self.dev_copy(with_record=False)
        con = sqlite3.connect(target)
        con.execute("PRAGMA journal_mode = WAL")
        con.close()
        report = verify.verify_snapshot(fx.SNAPSHOT_ID, build_file=target)
        self.assertFalse(check(report, "journal_mode_not_wal"))
        self.assertFalse(report["ok"])

    def test_canonical_without_record_fails(self):
        self.build_file.with_suffix(".json").unlink()
        report = verify.verify_snapshot(fx.SNAPSHOT_ID)
        self.assertFalse(check(report, "normalized_sha256_record"))
        self.assertFalse(report["ok"])

    def test_raw_source(self):
        missing = verify.verify_snapshot(fx.SNAPSHOT_ID, source_dir=self.root / "nowhere")
        self.assertFalse(check(missing, "raw_rebuild"))
        self.assertFalse(missing["ok"])
        skipped = verify.run({"snapshot_id": fx.SNAPSHOT_ID, "source_dir": str(self.root / "nowhere"),
                              "check_raw": False})
        self.assertIsNone(check(skipped, "raw_rebuild"))
        self.assertTrue(skipped["ok"])
        raw = next(p for p in sorted((self.source / "raw").glob("*.xml")) if b"<impDlr>600<" in p.read_bytes())
        raw.write_bytes(raw.read_bytes().replace(b"<impDlr>600<", b"<impDlr>601<"))
        tampered = verify.verify_snapshot(fx.SNAPSHOT_ID)
        self.assertFalse(check(tampered, "raw_rebuild"))  # 수신 기록의 응답 sha256과 raw가 다르다

    def test_other_files(self):
        collector = verify.verify_snapshot(fx.SNAPSHOT_ID, build_file=self.source / "snapshot.sqlite")
        self.assertFalse(check(collector, "tables_and_columns"))
        self.assertFalse(collector["ok"])
        nothing = verify.verify_snapshot(fx.SNAPSHOT_ID, build_file=self.root / "missing.sqlite")
        self.assertFalse(check(nothing, "open_read_only"))
        self.assertFalse(nothing["ok"])

    def test_all_duplicate_conflict(self):
        target = self.dev_copy(with_record=False)
        self.edit(target, "UPDATE observation SET amount_usd = amount_usd + 1 WHERE rowid = 55")
        report = verify.verify_snapshot(fx.SNAPSHOT_ID, build_file=target)
        self.assertFalse(check(report, "all_duplicates_consistent"))

    def test_input_errors(self):
        for bad in ({}, {"snapshot_id": "x", "extra": 1}, {"snapshot_id": "x", "check_raw": "no"}, []):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                verify.run(bad)


if __name__ == "__main__":
    unittest.main()
