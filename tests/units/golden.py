"""단위 골든 시험의 공통 규칙(docs/plan/UNITS.md §2 "골든 시험 한 쌍").

단위마다 tests/units/{단위 ID}/에 고정 입력 input.json과 기대 출력 expected.json을 두고, 진입 함수 run의 출력이
기대 출력과 같은지 본다. 파일 이름이 test로 시작하지 않으므로 이 모듈 자체는 시험으로 모이지 않는다.

건너뛰기와 실패
- 건너뛰는(skip) 경우는 둘뿐이다: 진입 함수가 없는 단위(커널 K1, 기존 수집기 S1)와 run이 아직 뼈대인 단위(몸통이
  NotImplementedError 하나). 그래서 S0 뒤 전체 시험이 종료 코드 0으로 끝난다.
- 실패한다: run을 구현했는데 골든 쌍이 없을 때, 출력이 기대 출력과 다를 때, 뼈대가 아닌 run이 호출 중
  NotImplementedError를 낼 때(부분 구현이거나, 아직 뼈대인 다른 단위를 부를 때).
- 부르는 단위가 아직 뼈대면 그 단위 폴더의 test_golden.py에서 대역(stub: 정해진 값을 돌려주는 가짜 함수)으로
  바꾼다. 예: setUp에서 unittest.mock.patch("tradesentry.metrics.rounding.run", return_value=...)를 시작하고
  addCleanup으로 멈춘다.
- 단위 폴더의 시험 파일에서 skipTest나 skip 장식자를 쓰려면 SKIP_ALLOWED(단위 ID → 사유)에 적고 검토받는다.
  tests/test_units_registry.py가 이것을 본다. 지금 목록은 비어 있다.

비교(값과 형식을 함께 본다)
- expected.json의 소수는 JSON 숫자로 적고 Decimal로 읽는다(예: 20.30은 Decimal("20.30")). 정수는 int로 읽는다.
  공통 실행기가 쓰는 출력 파일(Decimal을 문자열로 씀)을 그대로 expected.json으로 옮기지 않는다.
- Decimal은 str() 표기(끝자리 0 포함)로 비교한다. 20.3과 20.30은 다르다. bool은 int와 따로 본다. true와 1은 다르다.
- float는 기대 출력과 실제 출력 어디에 나와도 실패다(수는 int나 Decimal로 낸다).
- dict는 키와 값을, list는 순서까지 본다. 튜플은 목록으로 본다. 빈 expected.json은 None이다.
- 정수 값의 Decimal(예: Decimal("10"))은 JSON으로 적을 수 없다(10은 int, 10.0은 Decimal("10.0")으로 읽힌다).
  그런 출력과, 바이트나 문자열 파일처럼 형식이 다른 출력은 단위 폴더의 test_golden.py에서 compare를 바꿔 쓴다.

시험 환경(GoldenMixin.setUp)
- TRADESENTRY_SEALED_DIR와 HOME을 존재하지 않는 임시 경로로 고정하고, PYTHON_DOTENV_DISABLED=1로 python-dotenv의
  .env 자동 로드를 끄며(NAT의 `nat` 명령 진입점 nat.cli.entrypoint가 import 때 load_dotenv()를 부른다. 파이썬 API는
  부르지 않는다), 소켓 연결(socket.socket.connect,
  socket.create_connection)을 예외를 내는 함수로 바꾼다. 시험이 끝나면 되돌린다.
- 단위 폴더의 시험 파일은 test_golden_pair를 새로 정의하지 않는다. setUp을 새로 쓰면 super().setUp()을 부른다.
  compare나 golden_dir를 바꾼 파일은 허용하되, tests/test_units_registry.py가 목록으로 알린다(검토자가 본다).
"""
import ast
import json
import os
import sys
import tempfile
import uuid
from decimal import Decimal
from pathlib import Path
from unittest import mock

from tradesentry.units import registry

REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_NAME = "input.json"
EXPECTED_NAME = "expected.json"

# 단위 폴더의 시험 파일에서 skipTest나 skip 장식자를 써도 되는 단위(단위 ID → 사유). 더하려면 사유를 적고 검토받는다.
SKIP_ALLOWED: dict[str, str] = {}


def load_json(path: Path) -> object:
    text = path.read_text(encoding="utf-8")
    return json.loads(text, parse_float=Decimal) if text.strip() else None


def contains_float(value: object) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, (list, tuple)):
        return any(contains_float(v) for v in value)
    if isinstance(value, dict):
        return any(contains_float(k) or contains_float(v) for k, v in value.items())
    return False


def typed(value: object) -> object:
    """값과 형식을 함께 비교하려고 값마다 형식 이름을 붙인 모양으로 바꾼다."""
    if value is None:
        return ("null",)
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, int):
        return ("int", value)
    if isinstance(value, Decimal):
        return ("decimal", str(value))
    if isinstance(value, float):
        return ("float", repr(value))
    if isinstance(value, str):
        return ("str", value)
    if isinstance(value, (list, tuple)):
        return ("list", [typed(v) for v in value])
    if isinstance(value, dict):
        return ("dict", {(type(k).__name__, repr(k)): typed(v) for k, v in value.items()})
    return ("other", type(value).__name__, repr(value))


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


def _refuse_network(*args: object, **kwargs: object) -> None:
    raise OSError("골든 시험에서는 네트워크 연결을 쓰지 않는다")


class GoldenMixin:
    """단위 폴더의 test_golden.py가 unittest.TestCase와 함께 물려받는다. UNIT_ID만 적으면 된다."""

    UNIT_ID = ""

    def setUp(self):
        super().setUp()
        missing = Path(tempfile.gettempdir()) / f"tradesentry-golden-{uuid.uuid4().hex}"  # 만들지 않는 경로
        environment = mock.patch.dict(os.environ, {"TRADESENTRY_SEALED_DIR": str(missing / "sealed"),
                                                   "HOME": str(missing / "home"),
                                                   "PYTHON_DOTENV_DISABLED": "1"})
        environment.start()
        self.addCleanup(environment.stop)
        for target in ("socket.socket.connect", "socket.create_connection"):
            patcher = mock.patch(target, _refuse_network)
            patcher.start()
            self.addCleanup(patcher.stop)

    def golden_dir(self) -> Path:
        return Path(sys.modules[type(self).__module__].__file__).resolve().parent

    def compare(self, output: object, expected: object) -> None:
        self.assertFalse(contains_float(expected), "expected.json에 float가 있다. 소수는 Decimal로 읽는다")
        self.assertFalse(contains_float(output), f"단위 {self.UNIT_ID}: 출력에 float가 있다. 수는 int나 Decimal로 낸다")
        self.assertEqual(typed(output), typed(expected))

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
        output = run(load_json(source))  # 뼈대가 아닌 run의 NotImplementedError는 건너뛰지 않고 오류로 끝난다
        self.compare(output, load_json(expected))
