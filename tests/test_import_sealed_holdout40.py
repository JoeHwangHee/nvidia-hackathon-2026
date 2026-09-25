"""holdout40 봉인 입력 반입 도구(scripts/import_sealed_holdout40.py) 시험. 네트워크·키·openshell·docker 없이 돈다.

실제 봉인 폴더는 열지 않는다. 임시 폴더에 dev20 **공개 원천**(eval/dev/dev20/input/cases.json, data/snapshots/dev20/의 텍스트
원천, eval/dev/dev20/input/source/raw/*.xml, data/reference/peer_group_dev20.csv)으로 가짜 봉인 묶음을 만든다. 배치는 봉인 폴더의
holdout40 배치(결정 기록 sealed-hash-registration)와 같고, cases.json은 dataset만 holdout40으로 바꾼다. snapshot_id는 dev20 그대로라
도구에 `--snapshot-id dev20 --policy dev-0.1`을 주고, 빌드 normalized_sha256이 커밋된 dev20 빌드 기록의 값과 같아야 한다(독립 기대값).
(a) 대조 실패(해시 다름·목록 밖 파일·목록 파일 없음) → 종료 2, dest 없음 (b) 성공 → dest 파일 4개·import_manifest.json·
normalized_sha256 일치 (c) answers/·gen/·real_sealed/ 파일은 해시 계산 밖에서 열리지 않음(열기 호출 추적) (d) 표준 출력·오류에 사례
식별자·로컬 절대경로 없음. 그 밖에 dest 규칙(저장소 안·이미 있음)과 normalized_sha256 불일치(종료 3)를 본다.
"""
import builtins
import contextlib
import hashlib
import io
import json
import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import import_sealed_holdout40 as tool
from tradesentry.snapshot import build as s2

ROOT = Path(__file__).resolve().parents[1]
DEV20_CASES = ROOT / "eval" / "dev" / "dev20" / "input" / "cases.json"
DEV20_RAW = ROOT / "eval" / "dev" / "dev20" / "input" / "source" / "raw"
DEV20_SNAPSHOT = ROOT / "data" / "snapshots" / "dev20"
DEV20_PEER = ROOT / "data" / "reference" / "peer_group_dev20.csv"
SNAPSHOT_ID, POLICY = "dev20", "dev-0.1"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class FakeSealed:
    """임시 폴더의 가짜 봉인 묶음과 해시 목록."""

    def __init__(self, base: Path):
        self.sealed = base / "sealed"
        self.manifest = base / "sealed_manifest.json"
        self.files: dict[str, bytes] = {}
        cases = json.loads(DEV20_CASES.read_text(encoding="utf-8"))
        self.case_ids = [case["case_id"] for case in cases["cases"]]
        cases["dataset"] = "holdout40"
        self.put("holdout40/input/cases.json", (json.dumps(cases, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
        for name in ("manifest.json", "collection_log.json", "snapshot_hash.json", "snapshot_build.json"):
            self.put(f"holdout40/input/source/{name}", (DEV20_SNAPSHOT / name).read_bytes())
        self.put("holdout40/input/source/peer_group_dev20.csv", DEV20_PEER.read_bytes())
        for path in sorted(DEV20_RAW.glob("*.xml")):
            self.put(f"holdout40/input/source/raw/{path.name}", path.read_bytes())
        # 정답표·생성 코드·real_sealed 자리(가짜 내용). 도구가 해시만 보고 내용을 열지 않아야 한다
        self.put("holdout40/answers/answers.json", b'{"fake": "answers"}\n')
        self.put("holdout40/answers/parent_series_ids.json", b'{"fake": "ids"}\n')
        self.put("holdout40/answers/generation_rules.json", b'{"fake": "rules"}\n')
        self.put("holdout40/gen/seed.json", b'{"fake": "seed"}\n')
        self.put("real_sealed/sample_seed.json", b'{"fake": "seed"}\n')
        self.write_all()

    def put(self, rel: str, data: bytes) -> None:
        self.files[rel] = data

    def write_all(self) -> None:
        for rel, data in self.files.items():
            path = self.sealed / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.write_manifest()

    def write_manifest(self) -> None:
        entries = [{"dataset": rel.split("/")[0], "file_name": rel, "sha256": sha256(data),
                    "created_at": "2026-09-25T12:31:05+09:00", "created_by": "시험용 가짜 생성 주체"}
                   for rel, data in sorted(self.files.items())]
        self.manifest.write_text(json.dumps({"schema_version": 2, "files": entries}, ensure_ascii=False, indent=1) + "\n",
                                 encoding="utf-8")


class ImportToolTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name).resolve()
        self.fake = FakeSealed(self.base)
        self.dest = self.base / "overlay"
        env = mock.patch.dict(os.environ, {"TRADESENTRY_SEALED_DIR": str(self.base / "unused_sealed")})
        env.start()
        self.addCleanup(env.stop)

    def run_tool(self, *extra: str, dest: Path | None = None) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = tool.main(["--dest", str(dest or self.dest), "--sealed-dir", str(self.fake.sealed),
                              "--manifest", str(self.fake.manifest), "--snapshot-id", SNAPSHOT_ID, "--policy", POLICY, *extra])
        return code, out.getvalue(), err.getvalue()

    def assert_clean_text(self, text: str) -> None:
        self.assertNotIn(str(self.base), text)
        for case_id in self.fake.case_ids:
            self.assertNotIn(case_id, text)

    # (a) 대조 실패
    def test_hash_mismatch_refuses_without_writing(self):
        raw = next((self.fake.sealed / "holdout40/input/source/raw").glob("*.xml"))
        raw.write_bytes(raw.read_bytes() + b"\n")
        code, out, err = self.run_tool()
        self.assertEqual(code, 2, err)
        self.assertFalse(self.dest.exists())
        self.assertIn("해시 다름 1개", err)
        self.assertIn(f"holdout40/input/source/raw/{raw.name}", err)
        self.assert_clean_text(out + err)

    def test_extra_file_refuses_and_names_only_count(self):
        (self.fake.sealed / "holdout40" / ".DS_Store").write_bytes(b"\x00")
        code, out, err = self.run_tool()
        self.assertEqual(code, 2, err)
        self.assertFalse(self.dest.exists())
        self.assertIn("목록 밖 파일 1개", err)
        self.assertNotIn(".DS_Store", err)
        self.assert_clean_text(out + err)

    def test_missing_listed_file_refuses(self):
        (self.fake.sealed / "holdout40/answers/answers.json").unlink()
        code, _, err = self.run_tool()
        self.assertEqual(code, 2, err)
        self.assertIn("없음: holdout40/answers/answers.json", err)
        self.assertFalse(self.dest.exists())

    def test_check_manifest_counts(self):
        files = tool.load_manifest(self.fake.manifest)
        check = tool.check_manifest(self.fake.sealed, files)
        self.assertEqual((check["listed"], check["matched"], check["missing"], check["mismatched"], check["extra"]),
                         (len(self.fake.files), len(self.fake.files), [], [], 0))

    # (b)(c)(d) 성공 한 번으로 본다
    def test_success_writes_dest_reads_only_input_and_prints_no_identifiers(self):
        opened: list[str] = []
        hashed: list[str] = []
        real_open = builtins.open

        def recording_open(file, *args, **kwargs):
            if isinstance(file, (str, os.PathLike)):
                opened.append(os.fspath(file))
            return real_open(file, *args, **kwargs)

        def hashing(path: Path) -> str:
            hashed.append(str(path))
            digest = hashlib.sha256()
            fd = os.open(path, os.O_RDONLY)
            try:
                while chunk := os.read(fd, 1 << 16):
                    digest.update(chunk)
            finally:
                os.close(fd)
            return digest.hexdigest()

        with mock.patch.object(tool, "_sha256_file", hashing), mock.patch.object(builtins, "open", recording_open), \
                mock.patch.object(io, "open", recording_open):
            code, out, err = self.run_tool()
        self.assertEqual(code, 0, err)
        # (b) 파일 넷 + import_manifest.json, normalized_sha256이 커밋된 dev20 빌드 기록과 같다
        written = sorted(p.relative_to(self.dest).as_posix() for p in self.dest.rglob("*") if p.is_file())
        self.assertEqual(written, ["data/reference/peer_group_dev20.csv", "data/snapshots/dev20/snapshot_build.json",
                                   "data/snapshots/dev20/snapshot_build.sqlite", "eval/dev/holdout40/input/cases.json",
                                   "import_manifest.json"])
        expected = json.loads((DEV20_SNAPSHOT / "snapshot_build.json").read_text(encoding="utf-8"))["normalized_sha256"]
        self.assertEqual(s2.file_normalized_sha256(self.dest / "data/snapshots/dev20/snapshot_build.sqlite"), expected)
        record = json.loads((self.dest / "data/snapshots/dev20/snapshot_build.json").read_text(encoding="utf-8"))
        self.assertEqual((record["snapshot_id"], record["normalized_sha256"], record["build_file"]),
                         (SNAPSHOT_ID, expected, "snapshot_build.sqlite"))
        self.assertEqual(record["peer_group_files"], [{"file_name": "peer_group_dev20.csv", "sha256": sha256(DEV20_PEER.read_bytes())}])
        self.assertEqual((self.dest / "eval/dev/holdout40/input/cases.json").read_bytes(),
                         self.fake.files["holdout40/input/cases.json"])
        self.assertEqual((self.dest / "data/reference/peer_group_dev20.csv").read_bytes(), DEV20_PEER.read_bytes())
        manifest = json.loads((self.dest / "import_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["normalized_sha256"], expected)
        self.assertEqual(manifest["hash_check"], {"listed": len(self.fake.files), "matched": len(self.fake.files), "extra": 0})
        self.assertEqual(sorted(e["path"] for e in manifest["files"]), written[:-1])
        for entry in manifest["files"]:
            self.assertEqual(entry["sha256"], sha256((self.dest / entry["path"]).read_bytes()))
        listed = {e["file_name"]: e["sha256"] for e in json.loads(self.fake.manifest.read_text(encoding="utf-8"))["files"]}
        self.assertTrue(all(name.startswith("holdout40/input/") and listed[name] == digest
                            for name, digest in ((e["file_name"], e["sha256"]) for e in manifest["source_files"])))
        self.assertEqual(len(manifest["source_files"]), sum(1 for n in listed if n.startswith("holdout40/input/")))
        self.assertEqual(manifest["sealed_manifest_sha256"], sha256(self.fake.manifest.read_bytes()))
        self.assertNotIn(str(self.base), json.dumps(manifest))
        # (c) 해시 계산 밖에서 연 봉인 파일은 holdout40/input/ 아래만이다
        sealed_opened = [p for p in opened if p.startswith(str(self.fake.sealed) + os.sep)]
        self.assertTrue(sealed_opened)
        prefix = str(self.fake.sealed / "holdout40" / "input") + os.sep
        self.assertEqual([p for p in sealed_opened if not p.startswith(prefix)], [])
        self.assertEqual(len([p for p in hashed if p.startswith(str(self.fake.sealed) + os.sep)]), len(self.fake.files))
        # (d) 표준 출력·오류에 사례 식별자·로컬 절대경로가 없다
        self.assert_clean_text(out + err)
        self.assertRegex(out, rf"hash_check listed={len(self.fake.files)} matched={len(self.fake.files)} extra=0")
        self.assertIn(f"normalized_sha256={expected}", out)
        self.assertIn("written files=4", out)
        # 만든 빌드는 읽기 전용으로 열려 단위 S3와 같은 표를 가진다
        con = s2.open_read_only(self.dest / "data/snapshots/dev20/snapshot_build.sqlite")
        try:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM observation").fetchone()[0], record["row_counts"]["observation"])
        finally:
            con.close()

    def test_read_input_bytes_refuses_outside_input(self):
        for rel in ("holdout40/answers/answers.json", "holdout40/gen/seed.json", "real_sealed/sample_seed.json",
                    "holdout40/input/../answers/answers.json", "/etc/passwd"):
            with self.subTest(rel=rel), self.assertRaises(tool.ImportRefused):
                tool.read_input_bytes(self.fake.sealed, rel)
        self.assertEqual(tool.read_input_bytes(self.fake.sealed, "holdout40/input/cases.json"),
                         self.fake.files["holdout40/input/cases.json"])

    def test_normalized_mismatch_exits_3_without_writing(self):
        rel = "holdout40/input/source/snapshot_build.json"
        record = json.loads(self.fake.files[rel].decode("utf-8"))
        record["normalized_sha256"] = "0" * 64
        self.fake.put(rel, (json.dumps(record, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
        cases = json.loads(self.fake.files["holdout40/input/cases.json"].decode("utf-8"))
        cases["snapshot_normalized_sha256"] = "0" * 64
        self.fake.put("holdout40/input/cases.json", (json.dumps(cases, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
        self.fake.write_all()
        code, out, err = self.run_tool()
        self.assertEqual(code, 3, err)
        self.assertIn("normalized_sha256", err)
        self.assertFalse(self.dest.exists())
        self.assert_clean_text(out + err)

    def test_input_shape_refusals(self):
        cases = json.loads(self.fake.files["holdout40/input/cases.json"].decode("utf-8"))
        cases["dataset"] = "dev20"
        self.fake.put("holdout40/input/cases.json", (json.dumps(cases) + "\n").encode("utf-8"))
        self.fake.write_all()
        code, _, err = self.run_tool()
        self.assertEqual(code, 2, err)
        self.assertIn("dataset", err)
        self.assertFalse(self.dest.exists())
        code, _, err = self.run_tool("--snapshot-id", "holdout40")
        self.assertEqual(code, 2, err)
        code, _, err = self.run_tool("--policy", "policy_v1")
        self.assertEqual(code, 2, err)

    def test_dest_rules(self):
        inside = ROOT / "import_sealed_holdout40_test_dest"  # 저장소 안(부모는 있다). 도구가 만들지 않아야 한다
        self.assertFalse(inside.exists())
        code, _, err = self.run_tool(dest=inside)
        self.assertEqual(code, 2, err)
        self.assertFalse(inside.exists())
        self.assertIn("저장소", err)
        self.dest.mkdir()
        code, _, err = self.run_tool()
        self.assertEqual(code, 2, err)
        shutil.rmtree(self.dest)
        code, _, err = self.run_tool(dest=self.fake.sealed / "ctx")
        self.assertEqual(code, 2, err)
        self.assertFalse((self.fake.sealed / "ctx").exists())
        code, _, err = self.run_tool(dest=self.base / "missing_parent" / "ctx")
        self.assertEqual(code, 2, err)

    def test_repo_roots_include_this_worktree(self):
        roots = tool.repo_roots(ROOT)
        self.assertIn(ROOT, roots)
        self.assertTrue(all(root.is_absolute() for root in roots))

    def test_main_never_writes_into_sealed_dir(self):
        before = tool.sealed_files(self.fake.sealed)
        code, _, err = self.run_tool()
        self.assertEqual(code, 0, err)
        self.assertEqual(tool.sealed_files(self.fake.sealed), before)
        for rel in before:
            self.assertEqual(sha256((self.fake.sealed / rel).read_bytes()), sha256(self.fake.files[rel]))

    def test_collector_db_is_not_left_in_dest(self):
        code, _, err = self.run_tool()
        self.assertEqual(code, 0, err)
        names = {p.name for p in self.dest.rglob("*")}
        self.assertNotIn(s2.COLLECTOR_DB, names)
        self.assertNotIn(s2.MANIFEST_FILE, names)
        self.assertFalse((self.dest / "data" / "snapshots" / SNAPSHOT_ID / "raw").exists())
        with self.assertRaises(sqlite3.OperationalError):
            sqlite3.connect(f"file:{self.dest / 'data/snapshots/dev20/snapshot_build.sqlite'}?mode=ro", uri=True) \
                .execute("SELECT 1 FROM collection_attempt")


if __name__ == "__main__":
    unittest.main()
