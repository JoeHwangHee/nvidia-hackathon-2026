"""단위 F5(샌드박스 이미지 정의) 시험. 네트워크·키·docker·openshell 없이 돈다.

- configs/openshell/image/include.txt(명시한 포함 목록)가 거부 규칙을 지키는지 본다.
- scripts/stage_sandbox_image.py가 임시 폴더의 가짜 저장소에서 포함 목록 파일만 복사하고, .env·outputs/·정답표·채점기·
  스냅샷 원자료·심볼릭 링크·저장소 안 목적지를 거부하는지 본다. 봉인 폴더 변수는 시험마다 임시 경로로 둔다.
- Dockerfile이 관리 Python만 쓰고 정책(configs/openshell/policy.yaml)의 실행 파일·읽기 전용 경로와 맞는지 본다.
- CLI 실행기(configs/openshell/image/tradesentry.sh)가 옮긴 자리에서도 앱 뿌리를 찾는지 가짜 파이썬으로 본다.
"""
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import openshell_common as oc
from scripts import stage_sandbox_image as stage

ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "configs" / "openshell" / "image"
# 합성 시험자료 빌드: .sqlite는 fixture.materialize()가 만들고(커밋 안 함), .json은 로드맵 DT3(PR #33)이 커밋한다.
# 이 브랜치의 기준 커밋에는 아직 없으므로 저장소 안 존재 확인에서 뺀다(스테이징 도구는 없으면 멈춘다).
GENERATED = {"data/snapshots/controlled_fixture_v0/snapshot_build.sqlite",
             "data/snapshots/controlled_fixture_v0/snapshot_build.json"}


class IncludeListTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.entries = stage.read_include(ROOT / stage.INCLUDE_FILE)

    def test_entries_pass_block_rules(self):
        for rel, _ in self.entries:
            with self.subTest(rel=rel):
                self.assertIsNone(stage.blocked_reason(rel, from_add=False))

    def test_required_entries_exist_except_generated(self):
        for rel, optional in self.entries:
            if not optional and rel not in GENERATED:
                with self.subTest(rel=rel):
                    self.assertTrue((ROOT / rel).exists())

    def test_fixture_build_only_and_required(self):
        fixture = [(rel, opt) for rel, opt in self.entries if "controlled_fixture_v0" in rel]
        self.assertEqual(fixture, [("data/snapshots/controlled_fixture_v0/snapshot_build.sqlite", False),
                                   ("data/snapshots/controlled_fixture_v0/snapshot_build.json", False)])
        self.assertFalse(any("fixture_spec" in rel or rel.startswith("eval") for rel, _ in self.entries))


class BlockedReasonTest(unittest.TestCase):
    def test_table(self):
        cases = {
            ".env": True, ".env.example": True, "configs/x.env": True, "outputs/run/x.json": True,
            "outputs/sealed/x": True, "artifacts/eval/score-1/x": True, "eval/dev/oracle_ABC.json": True,
            "eval/scorer/core.py": True, "eval/datagen/dev20.py": True, "eval/sealed_manifest.json": True,
            "eval/dev/dev20": True, "src/.venv/x": True, ".git/config": True, "tests/test_cli.py": True,
            "spikes/x1/x1_probe.py": True, "docs/README.md": True, "scripts/tool.py": True,
            "data/snapshots/controlled_fixture_v0/fixture_spec.json": True,
            "data/snapshots/kcs_202201_202412_v2/raw/a.xml": True,
            "data/snapshots/kcs_202201_202412_v2/snapshot.sqlite": True,
            "data/snapshots/kcs_202201_202412_v2/manifest.json": True, "../outside": True, "/abs/path": True,
            "src/tradesentry/cli/args.py": False, "configs/model/model.json": False,
            "data/reference/country_map.csv": False,
            "data/snapshots/controlled_fixture_v0/snapshot_build.sqlite": False,
        }
        for rel, blocked in cases.items():
            with self.subTest(rel=rel):
                self.assertEqual(stage.blocked_reason(rel, from_add=False) is not None, blocked)

    def test_dev20_input_subpath_only_by_add(self):
        self.assertIsNone(stage.blocked_reason("eval/dev/dev20/input", from_add=True))
        self.assertIsNone(stage.blocked_reason("eval/dev/dev20/input/case_01.json", from_add=True))
        self.assertIsNotNone(stage.blocked_reason("eval/dev/dev20/input", from_add=False))
        self.assertIsNotNone(stage.blocked_reason("eval/dev/dev20", from_add=True))
        self.assertIsNotNone(stage.blocked_reason("eval/dev/dev20/input/oracle_x.json", from_add=True))
        self.assertIsNotNone(stage.blocked_reason("eval/dev/dev20/answers", from_add=True))
        self.assertIsNotNone(stage.blocked_reason("eval/dev/dev20/answers/answers.json", from_add=True))
        self.assertIsNotNone(stage.blocked_reason("eval/dev/dev20/cases.json", from_add=True))
        self.assertIsNotNone(stage.blocked_reason("eval/dev/dev20/input/answer_key.json", from_add=True))
        self.assertIsNone(stage.blocked_reason("data/snapshots/dev20/snapshot_build.sqlite", from_add=True))


class StageToolTest(unittest.TestCase):
    """가짜 저장소(임시 폴더)에서 스테이징한다. 저장소의 실제 파일은 읽기만 하고 고치지 않는다."""

    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name).resolve()
        self.repo = self.base / "repo"
        self.dest = self.base / "context"
        env = mock.patch.dict(os.environ, {"TRADESENTRY_SEALED_DIR": str(self.base / "sealed")})
        env.start()
        self.addCleanup(env.stop)
        for rel, optional in stage.read_include(ROOT / stage.INCLUDE_FILE):
            if optional:
                continue
            self.write(rel if Path(rel).suffix else f"{rel}/placeholder.txt", f"{rel}\n")
        for name in ("Dockerfile", "tradesentry.sh"):
            self.write(f"configs/openshell/image/{name}", (IMAGE / name).read_text(encoding="utf-8"))
        self.write("configs/openshell/image/include.txt", (IMAGE / "include.txt").read_text(encoding="utf-8"))
        self.write(".env", "NOT_A_KEY=1\n")
        self.write("src/tradesentry/__pycache__/x.cpython-312.pyc", "cache")
        self.write("eval/dev/oracle_ABC.json", "{}\n")
        self.write("eval/dev/dev20/input/case_01.json", "{}\n")
        self.write("data/snapshots/controlled_fixture_v0/fixture_spec.json", "{}\n")
        self.build_record("controlled_fixture_v0")

    def build_record(self, snapshot_id: str, peer_text: str = "peer\n", *, sha: str | None = None,
                     name: str | None = None) -> None:
        name = name or f"peer_group_{snapshot_id}.csv"
        peer = self.write(f"data/reference/{name}", peer_text) if "/" not in name else None
        digest = sha or (hashlib.sha256(peer.read_bytes()).hexdigest() if peer else "0" * 64)
        self.write(f"data/snapshots/{snapshot_id}/snapshot_build.json", json.dumps({
            "snapshot_id": snapshot_id, "normalized_sha256": "a" * 64,
            "peer_group_files": [{"file_name": name, "sha256": digest}]}))
        self.write(f"data/snapshots/{snapshot_id}/snapshot_build.sqlite", "db")

    def write(self, rel: str, text: str) -> Path:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_build_record_peer_groups_come_along(self):
        self.build_record("dev20")
        record = stage.stage(self.repo, self.dest, ["data/snapshots/dev20/snapshot_build.sqlite",
                                                    "data/snapshots/dev20/snapshot_build.json"])
        paths = [entry["path"] for entry in record["files"]]
        self.assertIn("data/reference/peer_group_controlled_fixture_v0.csv", paths)
        self.assertIn("data/reference/peer_group_dev20.csv", paths)
        self.assertEqual(sorted(snap["snapshot_id"] for snap in record["snapshots"]), ["controlled_fixture_v0", "dev20"])
        manifest = json.loads((self.dest / "app" / stage.MANIFEST_NAME).read_text(encoding="utf-8"))
        self.assertEqual(manifest["snapshots"][0]["normalized_sha256"], "a" * 64)

    def test_build_record_peer_group_problems_refuse(self):
        cases = {"sha": dict(sha="b" * 64), "name": dict(name="../outputs/x.csv"), "other": dict(name="oracle.csv")}
        for label, kwargs in cases.items():
            with self.subTest(label=label):
                self.build_record("controlled_fixture_v0", **kwargs)
                with self.assertRaises(stage.StageError):
                    stage.stage(self.repo, self.dest, [])
                self.assertFalse(self.dest.exists())
        self.build_record("controlled_fixture_v0")
        (self.repo / "data/reference/peer_group_controlled_fixture_v0.csv").unlink()
        with self.assertRaises(stage.StageError):
            stage.stage(self.repo, self.dest, [])

    def test_stages_only_listed_files(self):
        record = stage.stage(self.repo, self.dest, ["eval/dev/dev20/input"])
        staged = sorted(p.relative_to(self.dest / "app").as_posix()
                        for p in (self.dest / "app").rglob("*") if p.is_file())
        paths = [entry["path"] for entry in record["files"]]
        self.assertEqual(staged, sorted(paths + [stage.MANIFEST_NAME]))
        self.assertIn("eval/dev/dev20/input/case_01.json", paths)
        for rel in paths:
            self.assertIsNone(stage.blocked_reason(rel, from_add=rel.startswith("eval/")))
        for forbidden in (".env", "eval/dev/oracle_ABC.json", "data/snapshots/controlled_fixture_v0/fixture_spec.json"):
            self.assertNotIn(forbidden, paths)
        self.assertFalse(any("__pycache__" in rel or rel.endswith(".pyc") for rel in paths))
        self.assertTrue((self.dest / "Dockerfile").is_file() and (self.dest / "image" / "tradesentry.sh").is_file())
        manifest = (self.dest / "app" / stage.MANIFEST_NAME).read_bytes()
        self.assertEqual(hashlib.sha256(manifest).hexdigest(), record["manifest_sha256"])
        written = json.loads(manifest)
        self.assertEqual(written["files"], record["files"])
        self.assertEqual(written["optional_missing"], [rel for rel, opt in stage.read_include(ROOT / stage.INCLUDE_FILE)
                                                       if opt])
        self.assertNotIn(str(self.base), manifest.decode("utf-8"))

    def test_refusals_leave_nothing(self):
        refusals = {
            "listed .env": lambda: self.write("configs/openshell/image/include.txt", ".env\n"),
            "add oracle": None, "add dev20 whole": None, "add outputs": None, "add fixture spec": None,
        }
        adds = {"add oracle": ["eval/dev/oracle_ABC.json"], "add dev20 whole": ["eval/dev/dev20"],
                "add outputs": ["outputs"], "add fixture spec": ["data/snapshots/controlled_fixture_v0/fixture_spec.json"]}
        original = (IMAGE / "include.txt").read_text(encoding="utf-8")
        for label, prepare in refusals.items():
            with self.subTest(label=label):
                self.write("configs/openshell/image/include.txt", original)
                if prepare:
                    prepare()
                with self.assertRaises(stage.StageError):
                    stage.stage(self.repo, self.dest, adds.get(label, []))
                self.assertFalse(self.dest.exists())

    def test_symlink_refused(self):
        os.symlink(self.repo / ".env", self.repo / "src" / "tradesentry" / "linked.env.txt")
        with self.assertRaises(stage.StageError):
            stage.stage(self.repo, self.dest, [])
        self.assertFalse(self.dest.exists())

    def test_destination_rules(self):
        self.dest.mkdir()
        with self.assertRaises(stage.StageError):
            stage.stage(self.repo, self.dest, [])
        with self.assertRaises(stage.StageError):
            stage.stage(self.repo, self.repo / "build_context", [])
        (self.base / "sealed").mkdir()
        with self.assertRaises(stage.StageError):
            stage.stage(self.repo, self.base / "sealed" / "ctx", [])
        with self.assertRaises(stage.StageError):
            stage.stage(self.repo, self.base / "missing_parent" / "ctx", [])

    def test_missing_required_entry(self):
        (self.repo / "data/snapshots/controlled_fixture_v0/snapshot_build.sqlite").unlink()
        with self.assertRaises(stage.StageError):
            stage.stage(self.repo, self.dest, [])

    def test_main_prints_no_local_path(self):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(stage, "REPO_ROOT", self.repo), contextlib.redirect_stdout(out), \
                contextlib.redirect_stderr(err):
            code = stage.main(["--dest", str(self.dest)])
        self.assertEqual(code, 0, err.getvalue())
        self.assertNotIn(str(self.base), out.getvalue() + err.getvalue())
        self.assertRegex(out.getvalue(), r"manifest_sha256=[0-9a-f]{64}")
        with mock.patch.object(stage, "REPO_ROOT", self.repo), contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(err):
            self.assertEqual(stage.main(["--dest", str(self.dest)]), 2)
        self.assertNotIn(str(self.base), err.getvalue())


class DockerfileTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.text = (IMAGE / "Dockerfile").read_text(encoding="utf-8")
        self.policy = oc.parse_yaml((ROOT / "configs" / "openshell" / "policy.yaml").read_text(encoding="utf-8"))

    def test_managed_python_matches_policy_binary(self):
        version = (ROOT / ".python-version").read_text(encoding="utf-8").strip()
        self.assertIn(f"uv python install {version}", self.text)
        self.assertIn("UV_PYTHON_PREFERENCE=only-managed", self.text)
        install_dir = re.search(r"UV_PYTHON_INSTALL_DIR=(\S+)", self.text).group(1)
        [binary] = oc.network_blocks(self.policy)["tradesentry_nim_chat"]["binaries"]
        self.assertEqual(binary["path"], f"{install_dir}/**")
        self.assertIn("uv sync --locked --no-dev", self.text)

    def test_copies_only_staged_context(self):
        sources = re.findall(r"^COPY\s+(?:--from=\S+\s+)?(\S+)\s", self.text, re.M)
        self.assertEqual(sources, ["/uv", "app/", "image/tradesentry.sh"])
        self.assertIn("COPY app/ /opt/tradesentry/", self.text)

    def test_layout_matches_policy(self):
        self.assertEqual(oc.covering_entries(self.policy, "/opt/tradesentry/write_probe/x"),
                         ["read_only:/opt/tradesentry"])
        self.assertEqual(oc.covering_entries(self.policy, "/srv/tradesentry_decoy/oracle_decoy.json"), [])
        self.assertIn("/srv/tradesentry_decoy/oracle_decoy.json", self.text)
        self.assertIn("chmod 0644 /srv/tradesentry_decoy/oracle_decoy.json", self.text)
        self.assertIn("install -d -m 0777 /opt/tradesentry/write_probe", self.text)
        self.assertIn("/sandbox/read_only_probe", self.policy["filesystem_policy"]["read_only"])
        self.assertTrue(self.text.rstrip().endswith("USER sandbox\nWORKDIR /sandbox"))
        self.assertFalse(oc.has_key_shape(self.text))
        self.assertEqual(oc.LOCAL_PATH_RE.findall(self.text), [])


class LauncherTest(unittest.TestCase):
    """실행기를 옮긴 자리에서 가짜 파이썬(인자와 PYTHONPATH를 찍는 셸 스크립트)으로 돌려 본다."""

    FAKE = ("#!/bin/sh\necho \"exe=$0\"\necho \"pp=$PYTHONPATH\"\necho \"dotenv=$PYTHON_DOTENV_DISABLED\"\necho \"args=$*\"\n"
            "echo \"key=${NVIDIA_API_KEY-unset}\"\n")

    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve() / "tradesentry"
        (self.root / "bin").mkdir(parents=True)
        shutil.copyfile(IMAGE / "tradesentry.sh", self.root / "bin" / "tradesentry")
        os.chmod(self.root / "bin" / "tradesentry", 0o755)
        self.fake(self.root / "python" / "cpython-3.12.13-linux-test-gnu" / "bin" / "python3.12")
        os.symlink("cpython-3.12.13-linux-test-gnu", self.root / "python" / "current")

    def fake(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.FAKE, encoding="utf-8")
        os.chmod(path, 0o755)

    def run_launcher(self, **env: str) -> dict:
        done = subprocess.run([str(self.root / "bin" / "tradesentry"), "detect", "--snapshot", "x"],
                              capture_output=True, text=True, check=True, env={"PATH": "/usr/bin:/bin", **env})
        return dict(line.split("=", 1) for line in done.stdout.splitlines())

    def test_syntax(self):
        subprocess.run(["sh", "-n", str(IMAGE / "tradesentry.sh")], check=True)

    def test_copy_without_venv_uses_managed_python_and_pythonpath(self):
        out = self.run_launcher()
        self.assertEqual(out["exe"], str(self.root / "python" / "current" / "bin" / "python3.12"))
        self.assertEqual(out["pp"], f"{self.root}/src:{self.root}/.venv/lib/python3.12/site-packages")
        self.assertEqual((out["dotenv"], out["args"]), ("1", "-m tradesentry.cli detect --snapshot x"))

    def test_image_with_venv_uses_venv_python(self):
        self.fake(self.root / ".venv" / "bin" / "python")
        out = self.run_launcher()
        self.assertEqual((out["exe"], out["pp"]), (str(self.root / ".venv" / "bin" / "python"), f"{self.root}/src"))

    def test_demo_placeholder_is_aliased_only_when_placeholder(self):
        placeholder = "openshell:resolve:env:" + "NVIDIA_INFERENCE_API_KEY"
        self.assertEqual(self.run_launcher()["key"], "unset")
        self.assertEqual(self.run_launcher(NVIDIA_INFERENCE_API_KEY=placeholder)["key"], placeholder)
        not_placeholder = "nv" + "api" + "-" + "Q" * 30
        self.assertEqual(self.run_launcher(NVIDIA_INFERENCE_API_KEY=not_placeholder)["key"], "unset")
        mine = "openshell:resolve:env:" + "NVIDIA_API_KEY"
        self.assertEqual(self.run_launcher(NVIDIA_API_KEY=mine, NVIDIA_INFERENCE_API_KEY=placeholder)["key"], mine)


if __name__ == "__main__":
    unittest.main()
