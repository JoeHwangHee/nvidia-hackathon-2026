"""단위 E2(evaluation_sealed_runner) 골든 시험. 규칙은 tests/units/golden.py에 있다."""
import unittest

from ..golden import GoldenMixin


class GoldenTest(GoldenMixin, unittest.TestCase):
    UNIT_ID = "E2"
