"""경계 시험: 코드를 실행하지 않고 소스만 읽어(ast) 단위 사이의 경계를 확인한다.

정본: docs/plan/UNITS.md §2(경계 시험)·§5 1단계(정적 import 그래프). 확인하는 것:
1. 단위 파일이 머리 주석의 허용 import 밖을 import하지 않는다. 기존 수집기(단위 S1, src/tradesentry/ingest.py)는
   고치지 않으므로 머리 주석 대신 "표준 라이브러리만"을 적용한다(수집기는 표준 라이브러리만 쓴다는 규칙).
   허용 항목은 패키지(예: tradesentry.contract)나 모듈 하나(예: tradesentry.evaluation.batch_run)다.
2. 독립 채점기(eval/scorer/)는 허용 목록 방식이다. eval.scorer에서 import 문으로 직접이든 간접이든 닿는 이름은
   표준 라이브러리, eval(패키지 자체), eval.scorer 아래만 허용하고 나머지(tradesentry 전부, eval.datagen, tests/
   도우미, 외부 패키지)는 모두 위반이다.
3. dev20 생성 도구(단위 V2)가 tradesentry.metrics·tradesentry.policy와 그것들을 부르는 모듈에 닿지 않는다.
4. 샌드박스 밖 실행기(단위 E2)가 .env를 읽는 tradesentry.ingest(load_env)와 nat(NAT 1.9.0의 nat 명령 진입점은
   import 때 load_dotenv()를 부른다)에 닿지 않는다.
5. tradesentry·eval 아래 모듈은 tradesentry.units 밖에서 개발 전용 등록부·공통 실행기(tradesentry.units)를
   import하지 않는다(시험 파일은 예외).
6. 저장소 모듈 사이에 순환 import가 없다.
7. 채점기가 닿는 저장소 모듈 전부와 단위 V2·E2 파일에 금지 토큰이 없다: importlib·runpy·pkgutil·zipimport import,
   __import__·exec·eval·compile 호출, sys.path 쓰기, 문자열 상수 .env·NVIDIA_API_KEY·DATA_GO_KR_SERVICE_KEY,
   subprocess(와 os.system·os.exec*·os.spawn*·asyncio 하위 프로세스) 호출 인자 안의 tradesentry 문자열.
   문서 문자열(모듈·클래스·함수 첫 줄의 설명 문자열)은 보지 않는다. TRADESENTRY_SEALED_DIR는 금지하지 않는다.
   예외(단위 E2만): 하위 프로세스 인자 목록이 openshell로 시작하면(목록 리터럴이나 위치 인자의 첫 원소가 문자열
   "openshell") 그 목록 안의 tradesentry를 허용한다. 샌드박스 안에서만 CLI를 부르는 E2의 본래 일이다. 셸 문자열
   한 줄("openshell ... tradesentry ...")과 그 목록 밖의 인자(예: executable=)는 여전히 위반이다. 채점기와 V2에는
   이 예외가 없다.

따라가는 모듈은 src/ 아래(src를 뺀 이름)와 eval/·tests/·scripts/·spikes/ 아래(저장소 루트부터의 이름, 예:
tests.units.golden)다. "간접"은 저장소 안 다른 모듈을 거친 import와, 모듈을 import할 때 먼저 실행되는 상위
패키지의 __init__.py를 모두 센다. 함수 안이나 조건문 안의 import도 센다. 한계: 실행 중에 이름으로 부르는 import는
import 문으로 보이지 않는다. 그래서 7번이 채점기·V2·E2에서 그런 수단 자체를 막는다(등록부의 지연 import는
tradesentry.units에 있어 대상 밖이다). 각 검사가 실제로 위반을 잡는지는 NegativeCaseTest가 임시 폴더에 위반
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
FOLLOWED_TREES = ("eval", "tests", "scripts", "spikes")  # src/ 말고 따라가는 저장소 폴더(루트부터의 이름)

FORBIDDEN_IMPORTS = {"importlib", "runpy", "pkgutil", "zipimport"}
FORBIDDEN_CALLS = {"__import__", "exec", "eval", "compile"}
FORBIDDEN_STRINGS = ("NVIDIA_API_KEY", "DATA_GO_KR_SERVICE_KEY")
ENV_FILE_RE = re.compile(r"(?:^|[\\/])\.env(?:$|[\\/.])")
SYS_PATH_MUTATORS = {"append", "insert", "extend", "remove", "pop", "clear", "reverse", "sort", "__setitem__",
                     "__delitem__", "__iadd__"}
OS_PROCESS_CALLS = {"system", "popen", "execl", "execle", "execlp", "execlpe", "execv", "execve", "execvp", "execvpe",
                    "spawnl", "spawnle", "spawnlp", "spawnlpe", "spawnv", "spawnve", "spawnvp", "spawnvpe",
                    "posix_spawn", "posix_spawnp"}
ASYNCIO_PROCESS_CALLS = {"create_subprocess_exec", "create_subprocess_shell"}


@dataclass
class Closure:
    """rule: 보고용 규칙 번호. name: 보고용 이름. starts: 시작 모듈 이름 앞부분.
    forbidden: 닿으면 안 되는 이름 앞부분(금지 목록 방식). allowed가 있으면 허용 목록 방식이다: 표준 라이브러리,
    allowed_exact(그 이름만), allowed(그 이름과 그 아래)만 허용한다. tokens가 참이면 닿는 저장소 모듈 전부에
    금지 토큰 검사(7번)를 한다."""

    rule: str
    name: str
    starts: list[str]
    forbidden: list[str] = field(default_factory=list)
    allowed: list[str] | None = None
    allowed_exact: list[str] = field(default_factory=list)
    tokens: bool = False


@dataclass
class Rules:
    """units: 단위 ID → (모듈 이름, 고정 허용 목록 또는 None(머리 주석에서 읽음)).
    token_files: (보고용 이름, 모듈 이름, openshell 예외 여부) — 금지 토큰 검사를 하는 단위 파일."""

    units: dict[str, tuple[str, list[str] | None]]
    closures: list[Closure] = field(default_factory=list)
    token_files: list[tuple[str, str, bool]] = field(default_factory=list)


def under(name: str, prefix: str) -> bool:
    return name == prefix or name.startswith(prefix + ".")


def repo_modules(root: Path) -> dict[str, Path]:
    """따라가는 파이썬 모듈 이름 → 파일. src/ 아래는 src를 뺀 이름, 나머지 폴더는 저장소 루트부터의 이름."""
    modules: dict[str, Path] = {}
    bases = [(root / "src", root / "src")] + [(root / tree, root) for tree in FOLLOWED_TREES]
    for base, strip in bases:
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


def closure_allows(name: str, closure: Closure) -> bool:
    if name.split(".")[0] in STDLIB or name in closure.allowed_exact:
        return True
    return any(under(name, prefix) for prefix in closure.allowed or [])


def _docstring_nodes(tree: ast.AST) -> set[int]:
    found: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                    and isinstance(first.value.value, str):
                found.add(id(first.value))
    return found


def _is_sys_path(node: ast.AST) -> bool:
    return isinstance(node, ast.Attribute) and node.attr == "path" \
        and isinstance(node.value, ast.Name) and node.value.id == "sys"


def _writes_sys_path(target: ast.AST) -> bool:
    return _is_sys_path(target) or (isinstance(target, ast.Subscript) and _is_sys_path(target.value))


def forbidden_tokens(source: str, allow_openshell_cli: bool = False) -> list[str]:
    """7번 금지 토큰을 찾아 설명 목록으로 돌려준다.

    allow_openshell_cli가 참이면(단위 E2) 하위 프로세스 인자 목록이 "openshell"로 시작할 때 그 목록 안의
    tradesentry를 허용한다. 그 목록 밖의 인자는 그대로 본다."""
    tree = ast.parse(source)
    docstrings = _docstring_nodes(tree)
    subprocess_names: set[str] = set()
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "subprocess":
            subprocess_names |= {alias.asname or alias.name for alias in node.names}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found += [f"import {a.name}" for a in node.names if a.name.split(".")[0] in FORBIDDEN_IMPORTS]
        elif isinstance(node, ast.ImportFrom) and not node.level and node.module:
            if node.module.split(".")[0] in FORBIDDEN_IMPORTS:
                found.append(f"from {node.module} import")
            if node.module == "sys" and any(a.name == "path" for a in node.names):
                found.append("from sys import path")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in FORBIDDEN_CALLS:
                found.append(f"{func.id}() 호출")
            elif isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) \
                    and func.value.id == "builtins" and func.attr in FORBIDDEN_CALLS:
                found.append(f"builtins.{func.attr}() 호출")
            elif isinstance(func, ast.Attribute) and _is_sys_path(func.value) and func.attr in SYS_PATH_MUTATORS:
                found.append(f"sys.path.{func.attr}() 쓰기")
            if _is_process_call(func, subprocess_names):
                elements, holders = _command_list(node)
                exempt = holders if allow_openshell_cli and _starts_with_openshell(elements) else []
                for arg in list(node.args) + [k.value for k in node.keywords]:
                    if any(arg is holder for holder in exempt):
                        continue
                    for inner in ast.walk(arg):
                        if isinstance(inner, ast.Constant) and isinstance(inner.value, str) \
                                and "tradesentry" in inner.value:
                            found.append(f"하위 프로세스 인자 안의 tradesentry({inner.value!r})")
        elif isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Delete)):
            targets = node.targets if isinstance(node, (ast.Assign, ast.Delete)) else [node.target]
            if any(_writes_sys_path(t) for t in targets):
                found.append("sys.path 쓰기")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            if ENV_FILE_RE.search(node.value):
                found.append(f"문자열 상수 .env({node.value!r})")
            found += [f"문자열 상수 {name}" for name in FORBIDDEN_STRINGS if name in node.value]
    return found


def _command_list(call: ast.Call) -> tuple[list[ast.AST], list[ast.AST]]:
    """하위 프로세스 호출의 인자 목록 원소들과, 그 목록을 담은 인자 노드들.

    첫 위치 인자(없으면 args= 키워드)가 목록·튜플 리터럴이면 그 원소들이고(subprocess.run([...]) 모양), 아니면
    위치 인자들 자체다(asyncio.create_subprocess_exec("openshell", ...)·os.execl* 모양)."""
    first = call.args[0] if call.args else next((k.value for k in call.keywords if k.arg == "args"), None)
    if isinstance(first, (ast.List, ast.Tuple)):
        return list(first.elts), [first]
    if call.args:
        return list(call.args), list(call.args)
    return [], []


def _starts_with_openshell(elements: list[ast.AST]) -> bool:
    return bool(elements) and isinstance(elements[0], ast.Constant) and elements[0].value == "openshell"


def _is_process_call(func: ast.AST, subprocess_names: set[str]) -> bool:
    if isinstance(func, ast.Name):
        return func.id in subprocess_names
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        owner = func.value.id
        return owner == "subprocess" or (owner == "os" and func.attr in OS_PROCESS_CALLS) \
            or (owner == "asyncio" and func.attr in ASYNCIO_PROCESS_CALLS)
    return False


def check(root: Path, rules: Rules) -> tuple[list[str], dict[str, int]]:
    """위반 목록과 집계(몇 개를 봤는지)를 돌려준다."""
    modules = repo_modules(root)
    graph = {m: import_targets(m, p, modules) for m, p in modules.items()}
    problems: list[str] = []
    stats = {"modules": len(modules), "units": 0, "imports": sum(len(v) for v in graph.values()), "token_files": 0}

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

    token_modules: list[tuple[str, str, bool]] = list(rules.token_files)
    for closure in rules.closures:
        label = f"{closure.rule}) {closure.name}"
        start_modules = [m for m in modules if any(under(m, s) for s in closure.starts)]
        if not start_modules:
            problems.append(f"{label}: 시작 모듈이 없다({', '.join(closure.starts)})")
            continue
        stats[f"closure:{closure.name}"] = len(start_modules)
        reached = reach(start_modules, graph, modules)
        for hit in sorted(reached):
            if closure.allowed is not None and not closure_allows(hit, closure):
                problems.append(f"{label}: 허용 목록(표준 라이브러리, "
                                f"{', '.join(closure.allowed_exact + closure.allowed)}) 밖 이름에 닿는다({hit})")
            elif any(under(hit, prefix) for prefix in closure.forbidden):
                problems.append(f"{label}: 직접이든 간접이든 닿으면 안 되는 모듈에 닿는다({hit})")
        if closure.tokens:
            token_modules += [(closure.name, m, False) for m in sorted(reached) if m in modules]

    for name, module, openshell_ok in token_modules:
        path = modules.get(module)
        if path is None:
            problems.append(f"7) {name}: 모듈 파일이 없다({module})")
            continue
        stats["token_files"] += 1
        for token in forbidden_tokens(path.read_text(encoding="utf-8"), allow_openshell_cli=openshell_ok):
            problems.append(f"7) {name}({module}): 금지 토큰 {token}")

    for module, targets in sorted(graph.items()):
        if not (under(module, "tradesentry") or under(module, "eval")) or under(module, DEV_ONLY):
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
    v2, e2 = registry.UNITS["V2"].module, registry.UNITS["E2"].module
    closures = [
        Closure("2", "독립 채점기", ["eval.scorer"], allowed=["eval.scorer"], allowed_exact=["eval"], tokens=True),
        Closure("3", "단위 V2", [v2], forbidden=["tradesentry.metrics", "tradesentry.policy"]),
        Closure("4", "단위 E2", [e2], forbidden=["tradesentry.ingest", "nat"]),
    ]
    return Rules(units, closures, token_files=[("단위 V2", v2, False), ("단위 E2", e2, True)])


class RepositoryBoundaryTest(unittest.TestCase):
    def test_repository_has_no_boundary_violation(self):
        problems, stats = check(ROOT, repo_rules())
        self.assertEqual(problems, [], "\n".join(problems))
        self.assertEqual(stats["units"], len(registry.UNITS))  # 단위 54개의 허용 import를 모두 봤다
        self.assertGreaterEqual(stats["closure:독립 채점기"], 6)  # eval.scorer, __main__, 단위 C1~C4
        self.assertGreaterEqual(stats["token_files"], 2 + 6)  # 단위 V2·E2 파일과 채점기가 닿는 모듈
        self.assertTrue(any(name.startswith("tests.") for name in repo_modules(ROOT)))  # tests/ 아래도 따라간다

    def test_dispatch_may_not_import_host_only_sealed_runner(self):
        fields = registry.read_header((ROOT / registry.UNITS["F2"].path).read_text(encoding="utf-8"))
        tokens = registry.header_allowed_imports(fields)
        self.assertTrue(allowed("tradesentry.evaluation.batch_run", tokens))
        self.assertFalse(allowed(registry.UNITS["E2"].module, tokens))  # 호스트 전용 E2는 CLI가 부르지 않는다
        self.assertNotIn("tradesentry.evaluation", tokens)


def write_tree(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text), encoding="utf-8")


def header(unit_id: str, allowed_imports: str, note: str = "") -> str:
    return f'"""단위 {unit_id} 시험용. {note}\n\n단위 ID: {unit_id}\n허용 import: {allowed_imports}\n"""\n'


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
    "src/tradesentry/evaluation/sealed_runner.py": header("E2", "표준 라이브러리, tradesentry.evaluation",
                                                          "키 변수(NVIDIA_API_KEY)와 .env를 읽지 않는다.")
    + "import subprocess\n\n\ndef run(inp):\n    \"\"\"openshell로 run-case를 넘긴다(.env 없이).\"\"\"\n"
      "    return subprocess.run(['openshell', '--version'], check=False)\n",
    "src/tradesentry/evaluation/batch_run.py": header("E1", "표준 라이브러리"),
    "src/tradesentry/evaluation/helper.py": header("E9", "표준 라이브러리"),
    "src/tradesentry/cli/__init__.py": "",
    "src/tradesentry/cli/dispatch.py": header("F2", "표준 라이브러리, tradesentry.evaluation.batch_run")
    + "from tradesentry.evaluation import batch_run\n",
    "src/tradesentry/units/__init__.py": "",
    "src/tradesentry/units/registry.py": "import importlib\n",
    "eval/__init__.py": "",
    "eval/scorer/__init__.py": "",
    "eval/scorer/__main__.py": "import argparse\nimport sys\n",
    "eval/scorer/claims.py": header("C1", "표준 라이브러리, eval.scorer")
    + "import json\nimport os\nimport re\nimport sys\n\nSEALED = os.environ.get('TRADESENTRY_SEALED_DIR')\n"
      "PATTERN = re.compile('x')\nSEARCHED = list(sys.path)\n",
    "eval/datagen/__init__.py": "",
    "eval/datagen/split.py": header("V5", "표준 라이브러리, tradesentry.contract"),
    "eval/datagen/dev20.py": header("V2", "표준 라이브러리, tradesentry.contract, tradesentry.snapshot, eval.datagen"),
    "tests/helper.py": "import json\n",
    "scripts/tool.py": "import json\n",
}
TREE_RULES = Rules(
    units={"K1": ("tradesentry.contract.types", None), "K3": ("tradesentry.dal.query", None),
           "X4": ("tradesentry.metrics.rounding", None), "S2": ("tradesentry.snapshot.build", None),
           "E2": ("tradesentry.evaluation.sealed_runner", None), "S1": ("tradesentry.ingest", ["표준 라이브러리"]),
           "C1": ("eval.scorer.claims", None), "V2": ("eval.datagen.dev20", None),
           "F2": ("tradesentry.cli.dispatch", None)},
    closures=[Closure("2", "독립 채점기", ["eval.scorer"], allowed=["eval.scorer"], allowed_exact=["eval"], tokens=True),
              Closure("3", "단위 V2", ["eval.datagen.dev20"], forbidden=["tradesentry.metrics", "tradesentry.policy"]),
              Closure("4", "단위 E2", ["tradesentry.evaluation.sealed_runner"],
                      forbidden=["tradesentry.ingest", "nat"])],
    token_files=[("단위 V2", "eval.datagen.dev20", False), ("단위 E2", "tradesentry.evaluation.sealed_runner", True)],
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
        # 문서 문자열 속 .env·키 이름, TRADESENTRY_SEALED_DIR, re.compile, openshell 하위 프로세스는 위반이 아니다
        self.assertEqual(self.problems_with({}), [])

    def test_unit_import_outside_header(self):
        self.assert_caught({"src/tradesentry/metrics/rounding.py": header("X4", "표준 라이브러리, tradesentry.contract")
                            + "from ..dal import query\n"},
                           "1) 단위 X4", "tradesentry.dal.query")

    def test_module_level_allowance_blocks_sibling_module(self):
        self.assert_caught({"src/tradesentry/cli/dispatch.py": header("F2", "표준 라이브러리, "
                                                                      "tradesentry.evaluation.batch_run")
                            + "from tradesentry.evaluation import sealed_runner\n"},
                           "1) 단위 F2", "tradesentry.evaluation.sealed_runner")

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

    def test_scorer_reaches_runtime_through_tests_helper(self):
        self.assert_caught({"eval/scorer/__main__.py": "from tests import helper\n",
                            "tests/helper.py": "import tradesentry.contract.types\n"},
                           "2) 독립 채점기", "tests.helper", "tradesentry.contract.types")

    def test_scorer_third_party_is_outside_allowlist(self):
        self.assert_caught({"eval/scorer/claims.py": header("C1", "표준 라이브러리, eval.scorer, numpy")
                            + "import numpy\n"},
                           "2) 독립 채점기", "numpy")

    def test_v2_reaches_metrics_through_intermediate_module(self):
        self.assert_caught({"eval/datagen/dev20.py": header("V2", "표준 라이브러리, tradesentry.contract, "
                                                            "tradesentry.snapshot, eval.datagen")
                            + "from tradesentry.snapshot import build\n",
                            "src/tradesentry/snapshot/build.py": header("S2", "표준 라이브러리, tradesentry.metrics")
                            + "from tradesentry.metrics import rounding\n"},
                           "3) 단위 V2", "tradesentry.metrics")

    def test_v2_reaches_metrics_through_scripts(self):
        self.assert_caught({"eval/datagen/dev20.py": header("V2", "표준 라이브러리, eval.datagen")
                            + "from eval.datagen import util\n",
                            "eval/datagen/util.py": "import scripts.tool\n",
                            "scripts/tool.py": "from tradesentry.metrics import rounding\n"},
                           "3) 단위 V2", "tradesentry.metrics")

    def test_e2_reaches_ingest_indirectly(self):
        self.assert_caught({"src/tradesentry/evaluation/sealed_runner.py": header("E2", "표준 라이브러리, "
                                                                                  "tradesentry.evaluation")
                            + "from . import helper\n",
                            "src/tradesentry/evaluation/helper.py": "import tradesentry.ingest\n"},
                           "4) 단위 E2", "tradesentry.ingest")

    def test_e2_reaches_nat_indirectly(self):
        self.assert_caught({"src/tradesentry/evaluation/sealed_runner.py": header("E2", "표준 라이브러리, "
                                                                                  "tradesentry.evaluation")
                            + "from . import helper\n",
                            "src/tradesentry/evaluation/helper.py": "import nat.cli\n"},
                           "4) 단위 E2", "nat")

    def test_e2_reaches_ingest_through_spikes(self):
        self.assert_caught({"src/tradesentry/evaluation/sealed_runner.py": header("E2", "표준 라이브러리, "
                                                                                  "tradesentry.evaluation")
                            + "from . import helper\n",
                            "src/tradesentry/evaluation/helper.py": "import spikes.x1.run\n",
                            "spikes/x1/run.py": "from tradesentry import ingest\n"},
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

    def test_forbidden_tokens_in_scorer_closure(self):
        cases = {
            "import importlib\n": "import importlib",
            "from importlib import import_module\n": "from importlib import",
            "import runpy\n": "import runpy",
            "exec('x = 1')\n": "exec() 호출",
            "compile('x', 'f', 'exec')\n": "compile() 호출",
            "__import__('json')\n": "__import__() 호출",
            "import sys\nsys.path.insert(0, 'src')\n": "sys.path.insert() 쓰기",
            "import sys\nsys.path = ['src']\n": "sys.path 쓰기",
            "import subprocess\nsubprocess.run(['tradesentry', 'detect'])\n": "하위 프로세스 인자 안의 tradesentry",
            "from subprocess import check_output as co\nco(['python', '-m', 'tradesentry.cli'])\n":
                "하위 프로세스 인자 안의 tradesentry",
            "import os\nos.system('tradesentry run-case')\n": "하위 프로세스 인자 안의 tradesentry",
        }
        for source, fragment in cases.items():
            with self.subTest(source=source):
                self.assert_caught({"eval/scorer/__main__.py": source}, "7) 독립 채점기", fragment)

    def test_forbidden_tokens_in_v2_and_e2_files(self):
        self.assert_caught({"eval/datagen/dev20.py": header("V2", "표준 라이브러리, eval.datagen")
                            + "import os\nKEY = os.environ.get('NVIDIA_API_KEY')\n"},
                           "7) 단위 V2", "NVIDIA_API_KEY")
        self.assert_caught({"src/tradesentry/evaluation/sealed_runner.py": header("E2", "표준 라이브러리")
                            + "from pathlib import Path\nTEXT = Path('.env').read_text()\n"},
                           "7) 단위 E2", ".env")
        self.assert_caught({"src/tradesentry/evaluation/sealed_runner.py": header("E2", "표준 라이브러리")
                            + "import os\nKEY = os.environ[f'DATA_GO_KR_SERVICE_KEY']\n"},
                           "7) 단위 E2", "DATA_GO_KR_SERVICE_KEY")

    def test_e2_may_call_cli_only_through_openshell(self):
        e2 = "src/tradesentry/evaluation/sealed_runner.py"
        through_openshell = ('import subprocess\n\n\ndef run(inp):\n    return subprocess.run(["openshell", "sandbox", '
                             '"exec", "-n", "x", "--", "tradesentry", "run-case"])\n')
        self.assertEqual(self.problems_with({e2: header("E2", "표준 라이브러리") + through_openshell}), [])
        for call in ('subprocess.run(["tradesentry", "run-case"])',
                     'subprocess.run([sys.executable, "-m", "tradesentry.cli"])',
                     'subprocess.run("openshell sandbox exec -n x -- tradesentry run-case", shell=True)',
                     'subprocess.run(["openshell", "--version"], executable="tradesentry")'):
            with self.subTest(call=call):
                self.assert_caught({e2: header("E2", "표준 라이브러리") + f"import subprocess\nimport sys\n\n{call}\n"},
                                   "7) 단위 E2", "하위 프로세스 인자 안의 tradesentry")

    def test_openshell_exception_is_for_e2_only(self):
        call = 'import subprocess\nsubprocess.run(["openshell", "sandbox", "exec", "--", "tradesentry", "run-case"])\n'
        self.assert_caught({"eval/scorer/__main__.py": call}, "7) 독립 채점기", "하위 프로세스 인자 안의 tradesentry")
        self.assert_caught({"eval/datagen/dev20.py": header("V2", "표준 라이브러리, eval.datagen") + call},
                           "7) 단위 V2", "하위 프로세스 인자 안의 tradesentry")

    def test_forbidden_token_detector_ignores_harmless_code(self):
        harmless = ('"""문서: .env와 NVIDIA_API_KEY를 읽지 않는다."""\nimport os\nimport re\nimport subprocess\n'
                    "import sys\n\n\ndef f():\n    \"\"\"함수 문서: DATA_GO_KR_SERVICE_KEY도 읽지 않는다.\"\"\"\n"
                    "    subprocess.run(['openshell', '--version'])\n    return re.compile('a'), list(sys.path)\n\n\n"
                    "SEALED = os.environ.get('TRADESENTRY_SEALED_DIR')\nNAME = 'os.environ'\nFILE = '.envrc'\n")
        self.assertEqual(forbidden_tokens(harmless), [])


if __name__ == "__main__":
    unittest.main()
