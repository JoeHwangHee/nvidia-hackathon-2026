"""단위 S3(snapshot_verify) 골든 시험. 규칙은 tests/units/golden.py에 있다.

setUp이 합성 원천(tests/units/S2/fixture_snapshot.py)을 단위 S2로 빌드해 임시 폴더의 정본 자리(옆에 빌드 기록
snapshot_build.json)에 두고, 스냅샷 뿌리를 그 폴더로 바꾼다. 입력은 snapshot_id 하나(정본 빌드와 raw 대조)다.
"""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tradesentry.snapshot import build

from ..golden import GoldenMixin
from ..S2 import fixture_snapshot as fx


class GoldenTest(GoldenMixin, unittest.TestCase):
    UNIT_ID = "S3"

    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        fx.install_fixture_build(Path(tmp.name))
        patcher = mock.patch.object(build, "SNAPSHOTS_ROOT", Path(tmp.name))
        patcher.start()
        self.addCleanup(patcher.stop)


if __name__ == "__main__":
    unittest.main()
