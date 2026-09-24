"""단위 I5(tools_verify_evidence) 골든 시험. 규칙은 tests/units/golden.py에 있다.

setUp이 합성 스냅샷(I1 폴더의 tools_fixture.py)을 두고, 지표 단위 X1·X2·X3의 run을 대역(I1 폴더의 fake_metrics.py)으로
바꾸고, 도구 공통 틀의 시계를 고정한다. 입력은 I2·I3 골든 출력(앞서 받은 봉투, s 지표 하나는 값을 바꿔 둠)과 초안이 가리킨 지표·근거 ID다.
"""
import unittest

from ..golden import GoldenMixin
from ..I1 import fake_metrics, tools_fixture


class GoldenTest(GoldenMixin, unittest.TestCase):
    UNIT_ID = "I5"

    def setUp(self):
        super().setUp()
        tools_fixture.use_fixture(self)
        fake_metrics.patch_metrics(self)
        fake_metrics.fix_clock(self)


if __name__ == "__main__":
    unittest.main()
