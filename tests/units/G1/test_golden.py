"""단위 G1(grouping_g0) 골든 시험. 규칙은 tests/units/golden.py에 있다.

G1의 run은 CSV 문자열(등록부 확장자 csv)을 돌려준다. golden.py의 "문자열 파일처럼 형식이 다른 출력" 규칙대로 compare를
바꿔 쓴다: expected.json은 CSV의 줄 목록(줄끝 LF를 뺀 문자열)이고, 출력은 그 줄마다 LF를 붙여 이은 문자열과 글자까지
같아야 한다(CR 없음, 마지막 줄도 LF로 끝남). 골든 입력은 손으로 푼 합성 값이다.
"""
import unittest

from ..golden import GoldenMixin


class GoldenTest(GoldenMixin, unittest.TestCase):
    UNIT_ID = "G1"

    def compare(self, output, expected):
        self.assertIsInstance(output, str, "단위 G1: run은 CSV 문자열을 돌려준다")
        self.assertIsInstance(expected, list, "expected.json은 CSV 줄 목록이다")
        self.assertTrue(all(isinstance(line, str) and "\n" not in line and "\r" not in line for line in expected))
        self.assertEqual(output, "".join(f"{line}\n" for line in expected))
