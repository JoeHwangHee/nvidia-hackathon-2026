"""단위 R2(reports_render_ko) 골든 시험. 규칙은 tests/units/golden.py에 있다."""
import unittest

from ..golden import GoldenMixin


class GoldenTest(GoldenMixin, unittest.TestCase):
    UNIT_ID = "R2"
