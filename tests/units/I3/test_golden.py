"""단위 I3(tools_compare_partners) 골든 시험. 규칙은 tests/units/golden.py에 있다.

setUp이 합성 스냅샷(I1 폴더의 tools_fixture.py)을 두고 도구 공통 틀의 시계를 고정한다. 지표는 진짜 지표 단위(X1~X3)가
계산한다(대역 없음). 입력은 MX의 202401 대 202301, g0 비교국 전부다(US는 수집 계획 밖).
"""
import unittest

from ..golden import GoldenMixin
from ..I1 import metrics_spy, tools_fixture


class GoldenTest(GoldenMixin, unittest.TestCase):
    UNIT_ID = "I3"

    def setUp(self):
        super().setUp()
        tools_fixture.use_fixture(self)
        metrics_spy.fix_clock(self)


if __name__ == "__main__":
    unittest.main()
