"""단위 S2(snapshot_build) 골든 시험. 규칙은 tests/units/golden.py에 있다.

run의 출력은 SQLite 파일 바이트라 compare를 바꿔 쓴다: 바이트를 파일로 쓰고 열어, 표 네 개의 [rowid, 열 값…] 덤프와
저널 모드, 따로 계산한 normalized_sha256을 기대 출력과 비교한다(SQLite 파일 바이트 자체는 판본에 따라 달라 비교하지
않는다). 입력 원천은 setUp이 수집기 코드로 임시 폴더에 만든다(fixture_snapshot.py).
"""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tradesentry.snapshot import build

from ..golden import GoldenMixin
from . import fixture_snapshot as fx


class GoldenTest(GoldenMixin, unittest.TestCase):
    UNIT_ID = "S2"

    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        fx.make_source(self.root)
        fx.write_peer_group_csv(self.root / "peer_group.csv")
        for name in ("SNAPSHOTS_ROOT", "REPO_ROOT"):  # 스냅샷 폴더와 비교국 표 상대경로를 임시 폴더로
            patcher = mock.patch.object(build, name, self.root)
            patcher.start()
            self.addCleanup(patcher.stop)

    def compare(self, output, expected):
        self.assertIsInstance(output, bytes)
        path = self.root / "output.sqlite"
        path.write_bytes(output)
        actual = {**fx.dump_db(path), "normalized_sha256": fx.independent_normalized_sha256(path)}
        super().compare(actual, expected)


if __name__ == "__main__":
    unittest.main()
