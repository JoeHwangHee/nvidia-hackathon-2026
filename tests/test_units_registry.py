"""단위 등록부 시험: 등록부, 단위 파일, 머리 주석이 서로 맞는지 본다.

- 등록부는 저장소에 두는 앱·커널 단위 54개(앱 53, 커널 1)를 싣는다. 봉인 폴더에만 두는 단위 V3·V6과 구성 단위
  9개는 싣지 않는다. 합계 65개다(단위 표 docs/plan/UNITS.md §3, 단위 C3·C4는 PR #18 새 판).
- 도메인명은 이름 규칙(자료 계약 docs/rules/DATA_CONTRACT_V1.md §10.3 N1·N4)을 따른다.
- 단위 패키지 안에 등록부에 없는 모듈 파일이 없다(단위 하나가 파일 하나, N3).
단위 표 문서 자체와의 대조는 이 시험에 넣지 않는다(문서 판이 바뀌는 동안 깨지기 때문이다).
"""
import re
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
