"""단위 F2 스냅샷 명령을 실제 단위로 돌리는 시험(대역 없음). 네트워크와 키 없이 돈다.

- 자료: 단위 S2 시험 도우미(tests/units/S2/fixture_snapshot.py)가 기존 수집기 코드로 만든 합성 원천(unit_fixture_s2).
  실제 통계가 아니다.
- 실제로 도는 것: CLI 인자 검증(F1) → 명령 배선(F2) → 단위 K4 load_policy(저장소의 configs/policy_dev.json) → 단위 S2
  build_snapshot → 정본 옮기기(단위 S2 install_build, 로드맵 DT7 ②의 절차를 시험이 대신한다) → 단위 S3 run.
- 바꾸는 것은 위치 셋뿐이다: 스냅샷 원천의 뿌리(build.SNAPSHOTS_ROOT), 단위 S2·S3가 저장소 루트로 보는 곳(build.REPO_ROOT),
  CLI 실행 폴더의 부모(dispatch.OUTPUT_PARENT). 모두 시험마다 새 임시 폴더다. 저장소의 data/·outputs/는 건드리지 않는다.
"""
import contextlib
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tradesentry.cli import dispatch
from tradesentry.snapshot import build

from ..S2 import fixture_snapshot as fx


def call(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = dispatch.main(argv)
    return code, out.getvalue(), err.getvalue()


class RealSnapshotCommandsTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.source = fx.make_source(self.root / "snapshots")
        self.outputs = self.root / "outputs"
        for target, name, value in ((build, "SNAPSHOTS_ROOT", self.root / "snapshots"), (build, "REPO_ROOT", self.root),
                                    (dispatch, "OUTPUT_PARENT", self.outputs)):
            patcher = mock.patch.object(target, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def local_paths(self) -> tuple[str, ...]:
        return (str(self.root), str(self.root.resolve()))

    def run_dir(self, run_name: str) -> Path:
        [folder] = [p for p in self.outputs.iterdir() if p.name.startswith(f"{run_name}-")]
        return folder

    def build_with_cli(self) -> tuple[Path, dict]:
        """snapshot-build(dev-0.1)를 CLI로 돌리고 (빌드 파일, 빌드 기록)을 돌려준다."""
        code, out, err = call(["snapshot-build", "--snapshot", fx.SNAPSHOT_ID, "--policy", "dev-0.1"])
        self.assertEqual((code, err), (0, ""))
        folder = self.run_dir("snapshot_build")
        stamp = folder.name.split("-", 1)[1]
        db, record_file = folder / f"snapshot_build-{stamp}.sqlite", folder / f"snapshot_build-{stamp}.json"
        self.assertEqual(out, f"outputs/{folder.name}/{db.name}\noutputs/{folder.name}/{record_file.name}\n")
        self.assertEqual(sorted(p.name for p in folder.iterdir()), sorted([db.name, record_file.name]))
        text = record_file.read_text(encoding="utf-8")
        for local in self.local_paths():
            self.assertNotIn(local, text)  # 빌드 기록에 로컬 절대경로가 없다(N13)
        return db, json.loads(text)

    def test_build_writes_the_build_and_its_record(self):
        db, record = self.build_with_cli()
        self.assertEqual(record["snapshot_id"], fx.SNAPSHOT_ID)
        self.assertEqual(record["policy_version"], "dev-0.1")  # --policy를 단위 K4로 읽어 넘겼다
        self.assertIsNone(record["confirmed_no_trade_rule"])  # dev-0.1은 승격하지 않는다(configs/policy_dev.json)
        self.assertEqual(record["peer_group_files"], [])  # CLI는 비교국 표 파일을 넘기지 않는다
        self.assertEqual(record["row_counts"]["peer_group"], 0)
        self.assertEqual(record["build_file"], db.name)
        self.assertEqual(record["normalized_sha256"], fx.independent_normalized_sha256(db))

    def test_verify_passes_after_install_and_fails_after_tampering(self):
        db, record = self.build_with_cli()
        canonical = build.install_build(db, self.source)  # 정본 자리로 옮긴다(로드맵 DT7 ②의 절차)
        self.assertEqual(canonical["normalized_sha256"], record["normalized_sha256"])

        code, out, err = call(["snapshot-verify", "--snapshot", fx.SNAPSHOT_ID])
        self.assertEqual((code, err), (0, ""))
        folder = self.run_dir("snapshot_verify")
        [report_file] = list(folder.iterdir())
        self.assertEqual(out, f"outputs/{folder.name}/{report_file.name}\n")
        text = report_file.read_text(encoding="utf-8")
        report = json.loads(text)
        self.assertIs(report["ok"], True)  # 단위 S3의 불리언 ok가 CLI 종료 코드 0이 됐다
        self.assertEqual(report["normalized_sha256"], record["normalized_sha256"])
        self.assertEqual(report["recorded_normalized_sha256"], record["normalized_sha256"])
        for local in self.local_paths():
            self.assertNotIn(local, text)

        con = sqlite3.connect(self.source / build.BUILD_FILE)
        con.execute("UPDATE observation SET amount_usd = amount_usd + 1 "
                    "WHERE rowid = (SELECT MIN(rowid) FROM observation WHERE amount_usd IS NOT NULL)")
        con.commit()
        con.close()
        self.outputs = self.root / "outputs_after_tampering"  # 새 부모 폴더: 같은 초의 실행명을 다투며 기다리지 않는다
        with mock.patch.object(dispatch, "OUTPUT_PARENT", self.outputs):
            code, out, err = call(["snapshot-verify", "--snapshot", fx.SNAPSHOT_ID])
        self.assertEqual(code, dispatch.EXIT_FAILED)
        self.assertIn("불합격", err)
        [report_file] = list(self.run_dir("snapshot_verify").iterdir())
        self.assertIs(json.loads(report_file.read_text(encoding="utf-8"))["ok"], False)  # 불합격 보고도 남는다

    def test_build_error_from_the_real_unit(self):
        code, out, err = call(["snapshot-build", "--snapshot", "missing_snapshot"])  # 원천 폴더가 없다
        self.assertEqual((code, out), (dispatch.EXIT_FAILED, ""))
        self.assertIn("BuildError", err)
        for local in self.local_paths():
            self.assertNotIn(local, err)
        self.assertEqual(list(self.run_dir("snapshot_build").iterdir()), [])  # 확보한 빈 실행 폴더만 남는다


if __name__ == "__main__":
    unittest.main()
