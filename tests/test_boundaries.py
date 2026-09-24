"""경계 시험: 코드를 실행하지 않고 import 문만 읽어(ast) 단위 사이의 경계를 확인한다.

정본: docs/plan/UNITS.md §2(경계 시험)·§5 1단계(정적 import 그래프). 확인하는 것:
1. 단위 파일이 머리 주석의 허용 import 밖을 import하지 않는다. 기존 수집기(단위 S1, src/tradesentry/ingest.py)는
   고치지 않으므로 머리 주석 대신 "표준 라이브러리만"을 적용한다(수집기는 표준 라이브러리만 쓴다는 규칙).
2. 독립 채점기(eval/scorer/)가 tradesentry 패키지 전부(등록부·커널 포함)와 eval.datagen을 직접이든 간접이든
   import하지 않는다.
3. dev20 생성 도구(단위 V2)가 tradesentry.metrics·tradesentry.policy와 그것들을 부르는 모듈을 직접이든 간접이든
   import하지 않는다.
4. 샌드박스 밖 실행기(단위 E2)가 .env를 읽는 load_env가 있는 tradesentry.ingest에 닿지 않는다.
5. tradesentry.units 밖의 어떤 모듈도 개발 전용 등록부·공통 실행기(tradesentry.units)를 import하지 않는다.
6. 저장소 모듈(src/·eval/ 아래) 사이에 순환 import가 없다.

"간접"은 저장소 안 다른 모듈을 거친 import와, 모듈을 import할 때 먼저 실행되는 상위 패키지의 __init__.py를 모두 센다.
함수 안이나 조건문 안의 import도 센다. 한계: importlib·__import__처럼 실행 중에 이름으로 부르는 import는 보지
않는다(등록부의 지연 import가 그렇다). 각 검사가 실제로 위반을 잡는지는 NegativeCaseTest가 임시 폴더에 위반
사례를 만들어 확인한다.
"""
import ast
import re
import sys
import tempfile
import textwrap
import unittest
from dataclasses import dataclass, field
from pathlib import Path

from tradesentry.units import registry

ROOT = Path(__file__).resolve().parents[1]
STDLIB = frozenset(sys.stdlib_module_names) | {"__future__"}
TOKEN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$")
DEV_ONLY = "tradesentry.units"


@dataclass
class Rules:
    """units: 단위 ID → (모듈 이름, 고정 허용 목록 또는 None(머리 주석에서 읽음)).
    closures: (이름, 시작 모듈 이름 앞부분 목록, 닿으면 안 되는 모듈 이름 앞부분 목록)."""

    units: dict[str, tuple[str, list[str] | None]]
    closures: list[tuple[str, list[str], list[str]]] = field(default_factory=list)


def under(name: str, prefix: str) -> bool:
    return name == prefix or name.startswith(prefix + ".")


def repo_modules(root: Path) -> dict[str, Path]:
    """src/ 아래(src를 뺀 이름)와 eval/ 아래(eval부터의 이름) 파이썬 모듈 이름 → 파일."""
    modules: dict[str, Path] = {}
    for base, strip in ((root / "src", root / "src"), (root / "eval", root)):
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            parts = list(path.relative_to(strip).with_suffix("").parts)
            if parts[-1] == "__init__":
                parts = parts[:-1]
            modules[".".join(parts)] = path
    return modules


def import_targets(module: str, path: Path, modules: dict[str, Path]) -> list[str]:
    """모듈이 import하는 이름들. from X import n은 X.n이 저장소 모듈이면 X.n, 아니면 X로 센다."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
    package = module if path.name == "__init__.py" else module.rpartition(".")[0]
    targets: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parts = package.split(".") if package else []
                parts = parts[:len(parts) - (node.level - 1)]
                base = ".".join(parts + ([node.module] if node.module else []))
            else:
                base = node.module or ""
            for alias in node.names:
                candidate = f"{base}.{alias.name}" if base else alias.name
                targets.append(candidate if candidate in modules else base)
    return targets


def reach(starts: list[str], graph: dict[str, list[str]], modules: dict[str, Path]) -> set[str]:
    """starts를 import하면 실행되거나 import되는 이름 전부(상위 패키지 포함, 저장소 모듈은 따라 들어간다)."""
    seen: set[str] = set()
    stack = list(starts)
    while stack:
        name = stack.pop()
        parts = name.split(".")
        for i in range(1, len(parts) + 1):
            prefix = ".".join(parts[:i])
            if prefix in seen:
                continue
            seen.add(prefix)
            if prefix in modules:
                stack.extend(graph[prefix])
    return seen


def find_cycles(graph: dict[str, list[str]], modules: dict[str, Path]) -> list[list[str]]:
    """저장소 모듈 사이 명시적 import의 강한 연결 요소(Tarjan) 가운데 크기 2 이상."""
    edges = {m: sorted({t for t in graph[m] if t in modules and t != m}) for m in modules}
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: set[str] = set()
    stack: list[str] = []
    found: list[list[str]] = []

    def visit(node: str) -> None:
        index[node] = low[node] = len(index)
        stack.append(node)
        on_stack.add(node)
        for nxt in edges[node]:
            if nxt not in index:
                visit(nxt)
                low[node] = min(low[node], low[nxt])
            elif nxt in on_stack:
                low[node] = min(low[node], index[nxt])
        if low[node] == index[node]:
            component = []
            while True:
                top = stack.pop()
                on_stack.discard(top)
                component.append(top)
                if top == node:
                    break
            if len(component) > 1:
                found.append(sorted(component))

    for node in sorted(edges):
        if node not in index:
            visit(node)
    return found


def allowed(target: str, tokens: list[str]) -> bool:
    if target.split(".")[0] in STDLIB:
        return registry.STDLIB_TOKEN in tokens
    return any(under(target, token) for token in tokens if token != registry.STDLIB_TOKEN)


def check(root: Path, rules: Rules) -> tuple[list[str], dict[str, int]]:
    """위반 목록과 집계(몇 개를 봤는지)를 돌려준다."""
    modules = repo_modules(root)
    graph = {m: import_targets(m, p, modules) for m, p in modules.items()}
    problems: list[str] = []
    stats = {"modules": len(modules), "units": 0, "imports": sum(len(v) for v in graph.values())}

    for unit_id, (module, fixed) in sorted(rules.units.items()):
        path = modules.get(module)
        if path is None:
            problems.append(f"1) 단위 {unit_id}: 모듈 파일이 없다({module})")
            continue
        tokens = fixed if fixed is not None else registry.header_allowed_imports(
            registry.read_header(path.read_text(encoding="utf-8")))
        if not tokens:
            problems.append(f"1) 단위 {unit_id}: 머리 주석에 허용 import가 없다")
            continue
        stats["units"] += 1
        for token in tokens:
            if token != registry.STDLIB_TOKEN and not TOKEN_RE.match(token):
                problems.append(f"1) 단위 {unit_id}: 허용 import 항목을 읽을 수 없다({token!r})")
        for target in graph[module]:
            if not allowed(target, tokens):
                problems.append(f"1) 단위 {unit_id}({module}): 허용 import 밖을 import한다({target})")

    for name, starts, forbidden in rules.closures:
        start_modules = [m for m in modules if any(under(m, s) for s in starts)]
        if not start_modules:
            problems.append(f"{name}: 시작 모듈이 없다({', '.join(starts)})")
            continue
        stats[f"closure:{name}"] = len(start_modules)
        for hit in sorted(n for n in reach(start_modules, graph, modules) if any(under(n, f) for f in forbidden)):
            problems.append(f"{name}: 직접이든 간접이든 닿으면 안 되는 모듈에 닿는다({hit})")

    for module, targets in sorted(graph.items()):
        if under(module, DEV_ONLY):
            continue
        for target in targets:
            if under(target, DEV_ONLY):
                problems.append(f"5) {module}: 개발 전용 {DEV_ONLY}를 import한다({target})")

    for cycle in find_cycles(graph, modules):
        problems.append(f"6) 순환 import: {' ↔ '.join(cycle)}")
    return problems, stats


def repo_rules() -> Rules:
    units = {uid: (unit.module, [registry.STDLIB_TOKEN] if uid == "S1" else None)
             for uid, unit in registry.UNITS.items()}
    closures = [
        ("2) 독립 채점기", ["eval.scorer"], ["tradesentry", "eval.datagen"]),
        ("3) 단위 V2", [registry.UNITS["V2"].module], ["tradesentry.metrics", "tradesentry.policy"]),
        ("4) 단위 E2", [registry.UNITS["E2"].module], ["tradesentry.ingest"]),
    ]
    return Rules(units, closures)


class RepositoryBoundaryTest(unittest.TestCase):
    def test_repository_has_no_boundary_violation(self):
        problems, stats = check(ROOT, repo_rules())
        self.assertEqual(problems, [], "\n".join(problems))
        self.assertEqual(stats["units"], len(registry.UNITS))  # 단위 54개의 허용 import를 모두 봤다
        self.assertGreaterEqual(stats["closure:2) 독립 채점기"], 5)  # eval.scorer와 단위 C1~C4


def write_tree(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text), encoding="utf-8")


def header(unit_id: str, allowed_imports: str) -> str:
    return f'"""단위 {unit_id} 시험용.\n\n단위 ID: {unit_id}\n허용 import: {allowed_imports}\n"""\n'


BASE_TREE = {
    "src/tradesentry/__init__.py": "",
    "src/tradesentry/contract/__init__.py": "",
    "src/tradesentry/contract/types.py": header("K1", "표준 라이브러리, tradesentry.contract"),
    "src/tradesentry/dal/__init__.py": "",
    "src/tradesentry/dal/query.py": header("K3", "표준 라이브러리, tradesentry.contract, tradesentry.dal")
    + "import sqlite3\nfrom tradesentry.contract import types\n",
    "src/tradesentry/metrics/__init__.py": "",
    "src/tradesentry/metrics/rounding.py": header("X4", "표준 라이브러리, tradesentry.contract")
    + "from decimal import Decimal, ROUND_HALF_UP\n",
    "src/tradesentry/snapshot/__init__.py": "",
    "src/tradesentry/snapshot/build.py": header("S2", "표준 라이브러리, tradesentry.contract, tradesentry.dal"),
    "src/tradesentry/ingest.py": "import os\n",
    "src/tradesentry/evaluation/__init__.py": "",
    "src/tradesentry/evaluation/sealed_runner.py": header("E2", "표준 라이브러리, tradesentry.evaluation"),
    "src/tradesentry/evaluation/helper.py": header("E9", "표준 라이브러리"),
    "src/tradesentry/units/__init__.py": "",
    "src/tradesentry/units/registry.py": "import importlib\n",
    "eval/__init__.py": "",
    "eval/scorer/__init__.py": "",
    "eval/scorer/claims.py": header("C1", "표준 라이브러리, eval.scorer") + "import json\n",
    "eval/datagen/__init__.py": "",
    "eval/datagen/split.py": header("V5", "표준 라이브러리, tradesentry.contract"),
    "eval/datagen/dev20.py": header("V2", "표준 라이브러리, tradesentry.contract, tradesentry.snapshot, eval.datagen"),
}
TREE_RULES = Rules(
    units={"K1": ("tradesentry.contract.types", None), "K3": ("tradesentry.dal.query", None),
           "X4": ("tradesentry.metrics.rounding", None), "S2": ("tradesentry.snapshot.build", None),
           "E2": ("tradesentry.evaluation.sealed_runner", None), "S1": ("tradesentry.ingest", ["표준 라이브러리"]),
           "C1": ("eval.scorer.claims", None), "V2": ("eval.datagen.dev20", None)},
    closures=[("2) 독립 채점기", ["eval.scorer"], ["tradesentry", "eval.datagen"]),
              ("3) 단위 V2", ["eval.datagen.dev20"], ["tradesentry.metrics", "tradesentry.policy"]),
              ("4) 단위 E2", ["tradesentry.evaluation.sealed_runner"], ["tradesentry.ingest"])],
)


class NegativeCaseTest(unittest.TestCase):
    """위반을 하나씩 심은 임시 저장소에서 검사가 그 위반을 잡는지 본다."""

    def problems_with(self, changes: dict[str, str]) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_tree(root, {**BASE_TREE, **changes})
            problems, _ = check(root, TREE_RULES)
        return problems

    def assert_caught(self, changes: dict[str, str], *fragments: str) -> None:
        problems = self.problems_with(changes)
        joined = "\n".join(problems)
        self.assertTrue(problems, "위반을 잡지 못했다")
        for fragment in fragments:
            self.assertIn(fragment, joined)

    def test_clean_tree_passes(self):
        self.assertEqual(self.problems_with({}), [])

    def test_unit_import_outside_header(self):
        self.assert_caught({"src/tradesentry/metrics/rounding.py": header("X4", "표준 라이브러리, tradesentry.contract")
                            + "from ..dal import query\n"},
                           "1) 단위 X4", "tradesentry.dal.query")

    def test_third_party_import_needs_header(self):
        self.assert_caught({"src/tradesentry/metrics/rounding.py": header("X4", "표준 라이브러리") + "import numpy\n"},
                           "1) 단위 X4", "numpy")

    def test_collector_stays_standard_library_only(self):
        self.assert_caught({"src/tradesentry/ingest.py": "import requests\n"}, "1) 단위 S1", "requests")

    def test_scorer_direct_import_of_runtime(self):
        self.assert_caught({"eval/scorer/claims.py": header("C1", "표준 라이브러리, eval.scorer, tradesentry.contract")
                            + "from tradesentry.contract import types\n"},
                           "2) 독립 채점기", "tradesentry.contract.types")

    def test_scorer_reaches_runtime_through_parent_package_init(self):
        self.assert_caught({"eval/__init__.py": "import tradesentry.contract.types\n"},
                           "2) 독립 채점기", "tradesentry")

    def test_scorer_reaches_datagen_through_helper(self):
        self.assert_caught({"eval/scorer/claims.py": header("C1", "표준 라이브러리, eval.scorer")
                            + "from eval.scorer import helper\n",
                            "eval/scorer/helper.py": "import eval.datagen.split\n"},
                           "2) 독립 채점기", "eval.datagen")

    def test_v2_reaches_metrics_through_intermediate_module(self):
        self.assert_caught({"eval/datagen/dev20.py": header("V2", "표준 라이브러리, tradesentry.contract, "
                                                            "tradesentry.snapshot, eval.datagen")
                            + "from tradesentry.snapshot import build\n",
                            "src/tradesentry/snapshot/build.py": header("S2", "표준 라이브러리, tradesentry.metrics")
                            + "from tradesentry.metrics import rounding\n"},
                           "3) 단위 V2", "tradesentry.metrics")

    def test_e2_reaches_ingest_indirectly(self):
        self.assert_caught({"src/tradesentry/evaluation/sealed_runner.py": header("E2", "표준 라이브러리, "
                                                                                  "tradesentry.evaluation")
                            + "from . import helper\n",
                            "src/tradesentry/evaluation/helper.py": "import tradesentry.ingest\n"},
                           "4) 단위 E2", "tradesentry.ingest")

    def test_runtime_module_importing_dev_only_registry(self):
        self.assert_caught({"src/tradesentry/dal/query.py": header("K3", "표준 라이브러리, tradesentry")
                            + "from tradesentry import units\n"},
                           "5) tradesentry.dal.query", DEV_ONLY)

    def test_cycle(self):
        self.assert_caught({"src/tradesentry/contract/types.py": header("K1", "표준 라이브러리, tradesentry.contract")
                            + "from tradesentry.contract import envelope\n",
                            "src/tradesentry/contract/envelope.py": "from tradesentry.contract import types\n"},
                           "6) 순환 import", "tradesentry.contract.envelope", "tradesentry.contract.types")

    def test_missing_header_is_reported(self):
        self.assert_caught({"src/tradesentry/snapshot/build.py": "import os\n"}, "1) 단위 S2", "허용 import가 없다")


if __name__ == "__main__":
    unittest.main()
