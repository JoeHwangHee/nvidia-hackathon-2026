"""단위 K3(dal_query) 골든 시험. 규칙은 tests/units/golden.py에 있다.

setUp이 합성 원천(tests/units/S2/fixture_snapshot.py)을 단위 S2로 빌드해 임시 폴더의 정본 자리에 두고, 자료 접근층의
스냅샷 뿌리를 그 폴더로 바꾼다. 입력은 JP·850450의 두 달(부모 값 있음 / 승격된 무거래 확정), g1 비교국, 근거 ID 풀기다.
"""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tradesentry.dal import query

from ..golden import GoldenMixin
from ..S2 import fixture_snapshot as fx


class GoldenTest(GoldenMixin, unittest.TestCase):
    UNIT_ID = "K3"

    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        fx.install_fixture_build(Path(tmp.name))
        patcher = mock.patch.object(query, "SNAPSHOTS_ROOT", Path(tmp.name))
        patcher.start()
        self.addCleanup(patcher.stop)


if __name__ == "__main__":
    unittest.main()
