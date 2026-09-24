"""단위 I1(tools_check_comparability) 골든 시험. 규칙은 tests/units/golden.py에 있다.

setUp이 합성 스냅샷(tools_fixture.py, 14개월)을 임시 폴더의 정본 자리에 두고 자료 접근층의 스냅샷 뿌리를 그 폴더로
바꾼다. 도구 공통 틀의 시계를 고정해 elapsed_ms를 0으로 만든다. 입력은 MX(구성효과 사례)의 202401 대 202301이다.
"""
import unittest

from ..golden import GoldenMixin
from . import metrics_spy, tools_fixture


class GoldenTest(GoldenMixin, unittest.TestCase):
    UNIT_ID = "I1"

    def setUp(self):
        super().setUp()
        tools_fixture.use_fixture(self)
        metrics_spy.fix_clock(self)


if __name__ == "__main__":
    unittest.main()
