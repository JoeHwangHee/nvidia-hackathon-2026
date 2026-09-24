"""단위 골든 시험의 공통 규칙(docs/plan/UNITS.md §2 "골든 시험 한 쌍").

단위마다 tests/units/{단위 ID}/에 고정 입력 input.json과 기대 출력 expected.json을 두고, 진입 함수 run의 출력이
기대 출력과 같은지 본다. 네트워크와 키 없이 돈다. 파일 이름이 test로 시작하지 않으므로 이 모듈 자체는 시험으로
모이지 않는다.

- 건너뛴다(skip): 진입 함수가 없는 단위(커널 K1, 기존 수집기 S1), run이 아직 뼈대인 단위(몸통이
  NotImplementedError 하나), run을 불렀더니 NotImplementedError가 난 단위. 그래서 S0 뒤 전체 시험이 종료 코드 0으로 끝난다.
- 실패한다: run을 구현했는데 골든 쌍이 없을 때, 출력이 기대 출력과 다를 때.
- 비교: 두 파일은 JSON이고 소수는 Decimal로 읽는다(빈 파일은 None). run의 출력은 튜플을 목록으로 바꾼 뒤 == 로
  비교한다. 바이트·문자열처럼 형식이 다른 출력은 자기 폴더의 test_golden.py에서 compare를 바꿔 쓴다.
"""
import ast
import json
import sys
from decimal import Decimal
from pathlib import Path

from tradesentry.units import registry

REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_NAME = "input.json"
EXPECTED_NAME = "expected.json"


def load_json(path: Path) -> object:
    text = path.read_text(encoding="utf-8")
    return json.loads(text, parse_float=Decimal) if text.strip() else None


def normalize(value: object) -> object:
    if isinstance(value, (list, tuple)):
        return [normalize(v) for v in value]
    if isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items()}
    return value


def is_skeleton(unit: registry.Unit) -> bool:
    """단위의 진입 함수가 아직 뼈대인가. 코드를 실행하지 않고 파일을 읽는다."""
    return is_skeleton_source((REPO_ROOT / unit.path).read_text(encoding="utf-8"), unit.entry or "")


def is_skeleton_source(source: str, entry: str) -> bool:
    """진입 함수의 몸통이 (설명 문자열과) raise NotImplementedError 하나뿐이면 참이다."""
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == entry:
            body = list(node.body)
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                body = body[1:]
            if len(body) != 1 or not isinstance(body[0], ast.Raise) or body[0].exc is None:
                return False
            exc = body[0].exc.func if isinstance(body[0].exc, ast.Call) else body[0].exc
            return isinstance(exc, ast.Name) and exc.id == "NotImplementedError"
    return False


class GoldenMixin:
    """단위 폴더의 test_golden.py가 unittest.TestCase와 함께 물려받는다. UNIT_ID만 적으면 된다."""

    UNIT_ID = ""

    def golden_dir(self) -> Path:
        return Path(sys.modules[type(self).__module__].__file__).resolve().parent

    def compare(self, output: object, expected: object) -> None:
        self.assertEqual(normalize(output), expected)

    def test_golden_pair(self):
        unit = registry.UNITS[self.UNIT_ID]
        if unit.entry is None:
            self.skipTest(f"단위 {self.UNIT_ID}: 진입 함수가 없다({unit.note})")
        if is_skeleton(unit):
            self.skipTest(f"단위 {self.UNIT_ID}: run이 아직 뼈대다(NotImplementedError)")
        folder = self.golden_dir()
        source, expected = folder / INPUT_NAME, folder / EXPECTED_NAME
        self.assertTrue(source.is_file() and expected.is_file(),
                        f"단위 {self.UNIT_ID}: run을 구현했으면 골든 쌍({INPUT_NAME}·{EXPECTED_NAME})을 이 폴더에 둔다")
        run = registry.load_entry(unit)
        try:
            output = run(load_json(source))
        except NotImplementedError:
            self.skipTest(f"단위 {self.UNIT_ID}: run이 이 입력에 대해 아직 구현되지 않았다")
        self.compare(output, load_json(expected))
