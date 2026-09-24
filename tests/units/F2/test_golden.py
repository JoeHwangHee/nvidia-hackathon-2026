"""단위 F2(cli_dispatch) 골든 시험. 규칙은 tests/units/golden.py에 있다.

골든 쌍은 snapshot-verify 한 번이다(입력 input.json, 기대 출력 {"exit_code": 0}). 부르는 단위 S3
(tradesentry.snapshot.verify.run)는 로드맵 DT1이 구현하므로 합격 보고를 돌려주는 대역으로 바꾼다. 실행 폴더의 부모
(dispatch.OUTPUT_PARENT)는 시험마다 새 임시 폴더로, 표준 출력·오류는 버리는 곳으로 바꾼다. 그래서 단위 S3의 구현 상태와
저장소의 outputs/에 관계없이 같은 결과가 나온다.
"""
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ..golden import GoldenMixin

PASSING_REPORT = {"ok": True, "snapshot_id": "controlled_fixture_v0"}


class GoldenTest(GoldenMixin, unittest.TestCase):
    UNIT_ID = "F2"

    def setUp(self):
        super().setUp()
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        stubs = {"tradesentry.snapshot.verify.run": mock.Mock(return_value=PASSING_REPORT),
                 "tradesentry.cli.dispatch.OUTPUT_PARENT": Path(folder.name) / "outputs",
                 "sys.stdout": io.StringIO(), "sys.stderr": io.StringIO()}
        for target, value in stubs.items():
            patcher = mock.patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
