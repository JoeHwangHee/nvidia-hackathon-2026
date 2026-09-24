"""단위 등록부 시험: 등록부, 단위 파일, 머리 주석이 서로 맞는지 본다.

- 등록부는 저장소에 두는 앱·커널 단위 54개(앱 53, 커널 1)를 싣는다. 봉인 폴더에만 두는 단위 V3·V6과 구성 단위
  9개는 싣지 않는다. 합계 65개다(단위 표 docs/plan/UNITS.md §3, 단위 C3·C4는 PR #18 새 판).
- 도메인명은 이름 규칙(자료 계약 docs/rules/DATA_CONTRACT_V1.md §10.3 N1·N4)을 따른다.
- 단위 패키지 안에 등록부에 없는 모듈 파일이 없다(단위 하나가 파일 하나, N3).
단위 표 문서 자체와의 대조는 이 시험에 넣지 않는다(문서 판이 바뀌는 동안 깨지기 때문이다).
"""
import ast
import os
import re
import socket
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

from tradesentry.units import registry, runner

ROOT = Path(__file__).resolve().parents[1]
ID_RE = r"^[A-Z][0-9]+$"
NAME_RE = r"^[a-z][a-z0-9_]*$"
UNIT_PACKAGES = ("contract", "snapshot", "dal", "metrics", "policy", "grouping", "tools", "workflow", "reports",
                 "validator", "runlog", "evaluation", "approval", "cli")
UNITS_PACKAGE_FILES = {"__init__.py", "__main__.py", "registry.py", "runner.py"}
OWNERS = {"D", "M", "공동"}


def expected_domain(module: str) -> str:
    parts = module.split(".")
    if module in ("tradesentry.ingest", "tradesentry.app"):
        return parts[-1]  # 패키지 밖 모듈은 파일 이름(N4)
    if parts[0] == "tradesentry" and len(parts) == 3:
        return f"{parts[1]}_{parts[2]}"
    if parts[:2] == ["eval", "scorer"] and len(parts) == 3:
        return f"scorer_{parts[2]}"
    if parts[:2] == ["eval", "datagen"] and len(parts) == 3:
        return f"datagen_{parts[2]}"
    raise AssertionError(f"이름 규칙 밖의 모듈: {module}")


class RegistryTest(unittest.TestCase):
    def test_counts(self):
        units, others = registry.UNITS, registry.NOT_REGISTERED
        self.assertEqual(len(units), 54)
        self.assertEqual(sorted(u.unit_id for u in units.values() if u.entry is None), ["K1", "S1"])
        self.assertEqual(len(others), 11)
        self.assertFalse(set(units) & set(others))
        self.assertEqual(len(set(units) | set(others)), 65)
        self.assertLessEqual({"V3", "V6"}, set(others))

    def test_ids_domains_and_extensions(self):
        domains = [u.domain for u in registry.UNITS.values()]
        self.assertEqual(len(domains), len(set(domains)))
        for unit_id, unit in registry.UNITS.items():
            with self.subTest(unit_id=unit_id):
                self.assertEqual(unit.unit_id, unit_id)
                self.assertRegex(unit_id, ID_RE)
                self.assertRegex(unit.domain, NAME_RE)
                self.assertEqual(unit.domain, expected_domain(unit.module))
                self.assertIn(unit.ext, runner.OUTPUT_EXTS)
        for unit_id in registry.NOT_REGISTERED:
            self.assertRegex(unit_id, ID_RE)

    def test_files_exist_and_headers_match(self):
        for unit_id, unit in registry.UNITS.items():
            with self.subTest(unit_id=unit_id):
                path = ROOT / unit.path
                self.assertTrue(path.is_file(), unit.path)
                if unit_id == "S1":
                    continue  # 기존 수집기는 고치지 않으므로 머리 주석 형식이 없다
                fields = registry.read_header(path.read_text(encoding="utf-8"))
                self.assertEqual(set(fields), set(registry.HEADER_LABELS), unit.path)
                self.assertEqual(fields["단위 ID"], unit_id)
                self.assertEqual(fields["도메인명"], unit.domain)
                self.assertIn(fields["소유"], OWNERS)
                for label in ("입력", "출력"):
                    self.assertTrue(fields[label], label)
                self.assertIn(registry.STDLIB_TOKEN, registry.header_allowed_imports(fields))

    def test_entry_points(self):
        for unit_id, unit in registry.UNITS.items():
            with self.subTest(unit_id=unit_id):
                if unit.entry is None:
                    self.assertTrue(unit.note)
                    with self.assertRaises(LookupError):
                        registry.load_entry(unit)
                else:
                    self.assertTrue(callable(registry.load_entry(unit)))

    def test_no_unregistered_module_files(self):
        registered = {unit.path for unit in registry.UNITS.values()}
        found = [p for p in (ROOT / "src" / "tradesentry").glob("*.py")]
        for package in UNIT_PACKAGES:
            found += list((ROOT / "src" / "tradesentry" / package).glob("*.py"))
        found += list((ROOT / "eval" / "scorer").glob("*.py")) + list((ROOT / "eval" / "datagen").glob("*.py"))
        for path in found:
            rel = path.relative_to(ROOT).as_posix()
            with self.subTest(path=rel):
                self.assertTrue(rel in registered or path.name in ("__init__.py", "__main__.py"), rel)
        infra = {p.name for p in (ROOT / "src" / "tradesentry" / "units").glob("*.py")}
        self.assertLessEqual(infra, UNITS_PACKAGE_FILES)
        for package in UNIT_PACKAGES + ("units",):
            nested = [p.name for p in (ROOT / "src" / "tradesentry" / package).iterdir()
                      if p.is_dir() and p.name != "__pycache__"]
            self.assertEqual(nested, [], package)

    def test_golden_frames_match_registry(self):
        base = ROOT / "tests" / "units"
        folders = {p.name for p in base.iterdir() if p.is_dir() and p.name != "__pycache__"}
        self.assertEqual(folders, set(registry.UNITS))  # 등록부 단위마다 하나, V3·V6 등 등록부 밖 단위는 없다
        self.assertTrue((base / "__init__.py").is_file())
        for unit_id in registry.UNITS:
            with self.subTest(unit_id=unit_id):
                self.assertTrue((base / unit_id / "__init__.py").is_file())  # 없으면 discover가 내려가지 않는다
                text = (base / unit_id / "test_golden.py").read_text(encoding="utf-8")
                self.assertIn(f'UNIT_ID = "{unit_id}"', text)

    def test_sealed_only_units_are_not_in_repository(self):
        for name in ("holdout40_gen", "sealed_holdout40_gen", "real_sample", "sealed_real_sample"):
            self.assertEqual([p for p in ROOT.glob(f"src/**/{name}.py")] + [p for p in ROOT.glob(f"eval/**/{name}.py")],
                             [], name)

    def test_header_reader(self):
        source = '"""단위 Z9 시험.\n\n단위 ID: Z9\n허용 import: 표준 라이브러리, tradesentry.contract\n"""\n'
        fields = registry.read_header(source)
        self.assertEqual(fields, {"단위 ID": "Z9", "허용 import": "표준 라이브러리, tradesentry.contract"})
        self.assertEqual(registry.header_allowed_imports(fields), ["표준 라이브러리", "tradesentry.contract"])
        self.assertEqual(registry.read_header("x = 1\n"), {})


SKIP_NAMES = {"skipTest", "skip", "skipIf", "skipUnless", "expectedFailure", "SkipTest"}


def skip_uses(source: str) -> list[str]:
    """시험 소스에서 skipTest 호출, skip 장식자(skip·skipIf·skipUnless·expectedFailure), SkipTest를 찾는다."""
    found = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Attribute) and node.attr in SKIP_NAMES:
            found.add(node.attr)
        elif isinstance(node, ast.Name) and node.id in SKIP_NAMES:
            found.add(node.id)
    return sorted(found)


def run_golden(unit_id: str, entry, expected_json: str | None, input_json: str = "{}") -> unittest.TestResult:
    """임시 골든 폴더와 가짜 진입 함수로 GoldenMixin.test_golden_pair를 한 번 돌린다(run은 뼈대가 아니라고 본다)."""
    from units import golden  # discover가 tests/를 맨 위 경로로 넣으므로 tests/units는 units로 불린다

    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        (folder / golden.INPUT_NAME).write_text(input_json, encoding="utf-8")
        if expected_json is not None:
            (folder / golden.EXPECTED_NAME).write_text(expected_json, encoding="utf-8")

        class Case(golden.GoldenMixin, unittest.TestCase):
            UNIT_ID = unit_id

            def golden_dir(self):
                return folder

        result = unittest.TestResult()
        with mock.patch.object(golden, "is_skeleton", return_value=False), \
                mock.patch.object(registry, "load_entry", return_value=entry):
            Case("test_golden_pair").run(result)
    return result


class GoldenRuleTest(unittest.TestCase):
    """골든 시험 규칙(tests/units/golden.py): 건너뛰기 범위, 형식까지 보는 비교, 시험 환경, 건너뛰기 허용 목록."""

    def test_skeleton_detection(self):
        from units import golden

        skeleton = 'def run(inp):\n    """설명."""\n    raise NotImplementedError("아직")\n'
        bare = "def run(inp):\n    raise NotImplementedError\n"
        implemented = 'def run(inp):\n    """설명."""\n    return {"U": inp}\n'
        partial = 'def run(inp):\n    if inp is None:\n        raise NotImplementedError\n    return inp\n'
        self.assertTrue(golden.is_skeleton_source(skeleton, "run"))
        self.assertTrue(golden.is_skeleton_source(bare, "run"))
        self.assertFalse(golden.is_skeleton_source(implemented, "run"))
        self.assertFalse(golden.is_skeleton_source(partial, "run"))
        self.assertFalse(golden.is_skeleton_source(skeleton, "other"))
        self.assertTrue(all(golden.is_skeleton(u) for u in registry.UNITS.values() if u.entry))

    def test_not_implemented_in_non_skeleton_run_is_an_error(self):
        def calls_skeleton(inp):
            raise NotImplementedError("부른 단위가 아직 뼈대다")

        result = run_golden("X1", calls_skeleton, '{"U": 1}')
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.skipped, [])

    def test_implemented_run_without_pair_fails(self):
        result = run_golden("X1", lambda inp: {"U": 1}, None)
        self.assertEqual(len(result.failures), 1)
        self.assertEqual(result.skipped, [])

    def test_exact_values_and_formats_pass(self):
        output = {"U": Decimal("20.30"), "n": 1, "ok": True, "xs": (1, 2), "none": None, "s": "가"}
        expected = '{"xs": [1, 2], "U": 20.30, "n": 1, "ok": true, "none": null, "s": "가"}'
        result = run_golden("X1", lambda inp: output, expected)
        self.assertTrue(result.wasSuccessful(), result.failures + result.errors)
        self.assertEqual(result.skipped, [])

    def test_number_format_differences_fail(self):
        cases = [
            ("20.3 대 20.30", {"U": Decimal("20.3")}, '{"U": 20.30}'),
            ("20.30 대 20.3", {"U": Decimal("20.30")}, '{"U": 20.3}'),
            ("1 대 true", {"ok": 1}, '{"ok": true}'),
            ("true 대 1", {"n": True}, '{"n": 1}'),
            ("Decimal 대 int", {"n": Decimal("1")}, '{"n": 1}'),
            ("float 출력", {"U": 20.3}, '{"U": 20.3}'),
            ("list 순서", {"xs": [2, 1]}, '{"xs": [1, 2]}'),
        ]
        for name, output, expected in cases:
            with self.subTest(name):
                result = run_golden("X1", lambda inp, value=output: value, expected)
                self.assertEqual(len(result.failures), 1)
                self.assertEqual(result.errors, [])

    def test_golden_run_has_no_home_sealed_folder_or_network(self):
        seen = {}
        home_before = os.environ.get("HOME")
        create_connection_before = socket.create_connection

        def probe(inp):
            seen["home"] = os.environ["HOME"]
            seen["sealed"] = os.environ["TRADESENTRY_SEALED_DIR"]
            try:
                socket.create_connection(("127.0.0.1", 9), timeout=1)
                seen["create_connection"] = "연결됨"
            except OSError as exc:
                seen["create_connection"] = str(exc)
            with socket.socket() as sock:
                try:
                    sock.connect(("127.0.0.1", 9))
                    seen["connect"] = "연결됨"
                except OSError as exc:
                    seen["connect"] = str(exc)
            return {"ok": True}

        result = run_golden("X1", probe, '{"ok": true}')
        self.assertTrue(result.wasSuccessful(), result.failures + result.errors)
        self.assertFalse(Path(seen["home"]).exists())
        self.assertFalse(Path(seen["sealed"]).exists())
        self.assertIn("네트워크", seen["create_connection"])
        self.assertIn("네트워크", seen["connect"])
        self.assertEqual(os.environ.get("HOME"), home_before)  # 시험이 끝나면 되돌린다
        self.assertIs(socket.create_connection, create_connection_before)
        self.assertNotIn("connect", vars(socket.socket))

    def test_unit_folders_skip_only_with_allowance(self):
        from units import golden

        for unit_id, reason in golden.SKIP_ALLOWED.items():
            self.assertIn(unit_id, registry.UNITS)
            self.assertTrue(reason)
        base = ROOT / "tests" / "units"
        checked = 0
        for folder in sorted(p for p in base.iterdir() if p.is_dir() and p.name != "__pycache__"):
            for path in sorted(folder.glob("*.py")):
                checked += 1
                uses = skip_uses(path.read_text(encoding="utf-8"))
                if uses:
                    self.assertIn(folder.name, golden.SKIP_ALLOWED, f"{path.relative_to(ROOT)}: {uses}")
        self.assertGreaterEqual(checked, 2 * len(registry.UNITS))

    def test_skip_use_detection(self):
        self.assertEqual(skip_uses("class T:\n    def test(self):\n        self.skipTest('x')\n"), ["skipTest"])
        self.assertIn("skip", skip_uses("import unittest\n@unittest.skip('x')\ndef f():\n    pass\n"))
        self.assertIn("skipIf", skip_uses("from unittest import skipIf\n@skipIf(True, 'x')\ndef f():\n    pass\n"))
        self.assertIn("SkipTest", skip_uses("import unittest\nraise unittest.SkipTest('x')\n"))
        self.assertEqual(skip_uses((ROOT / "tests" / "units" / "X1" / "test_golden.py").read_text(encoding="utf-8")), [])


if __name__ == "__main__":
    unittest.main()
