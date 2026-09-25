"""조립 작업 AS3: 사용자 결정 10(나) --run-name의 실행 폴더 확보와 샌드박스 안 code_version(이미지 기록) 시험.

- --run-name이 있으면 CLI는 그 이름의 실행 폴더를 이미 있으면 실패하는 방식으로 만든다(다음 초로 넘어가지 않는다).
  outputs/sealed/에 같은 이름이 있으면 방금 만든 폴더를 지우고 실패한다(자료 계약 §10.3 N8). 실패는 종료 코드 1이고 문장에
  받은 값이 없다.
- 이미지 안에는 .git이 없으므로 code_version은 이미지 기록(image_manifest.json)의 커밋이다. dirty가 거짓일 때만 쓴다.
모든 파일은 임시 폴더에 쓴다.
"""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tradesentry.cli import dispatch
from tradesentry.snapshot import verify

HASH = "0123456789abcdef0123456789abcdef01234567"


def call(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = dispatch.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class GivenRunNameTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.outputs = Path(tmp.name) / "outputs"
        for patcher in (mock.patch.object(dispatch, "OUTPUT_PARENT", self.outputs),
                        mock.patch.object(verify, "run", lambda inp: {"ok": True, "checks": []})):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_given_name_is_the_run_folder(self):
        code, out, err = call(["snapshot-verify", "--snapshot", "controlled_fixture_v0",
                               "--run-name", "snapshot_verify-260925143015"])
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "outputs/snapshot_verify-260925143015/snapshot_verify-260925143015.json\n")

    def test_existing_or_sealed_name_fails_without_echo(self):
        (self.outputs / "snapshot_verify-260925143015").mkdir(parents=True)
        (self.outputs / "sealed" / "snapshot_verify-260925143016").mkdir(parents=True)
        for name, text in (("snapshot_verify-260925143015", "실행 폴더가 이미 있다"),
                           ("snapshot_verify-260925143016", "outputs/sealed/에 이미 있다")):
            with self.subTest(name=name):
                code, out, err = call(["snapshot-verify", "--snapshot", "controlled_fixture_v0", "--run-name", name])
                self.assertEqual((code, out), (1, ""))
                self.assertIn(text, err)
                self.assertNotIn(name, err)
        self.assertFalse((self.outputs / "snapshot_verify-260925143016").exists())  # 만든 폴더를 지웠다
        self.assertEqual(sorted(p.name for p in self.outputs.iterdir()), ["sealed", "snapshot_verify-260925143015"])

    def test_reserve_rechecks_the_name(self):
        for name in ("detect-260925143015", "snapshot_verify-26092514301", "snapshot_verify-260925143015\n"):
            with self.subTest(name=name), self.assertRaises(dispatch.RunNameError):
                dispatch.reserve_run_dir("snapshot_verify", given=name)
        self.assertFalse(self.outputs.exists() and any(self.outputs.iterdir()))

    def test_every_handler_passes_the_given_name(self):
        """다섯 처리 함수가 모두 reserve_run_dir에 --run-name 값을 넘긴다(소스에서 호출 모양을 본다)."""
        import inspect

        for handler in (dispatch._snapshot_build, dispatch._snapshot_verify, dispatch._detect, dispatch._run_case,
                        dispatch._evaluate):
            with self.subTest(handler=handler.__name__):
                self.assertIn("given=request.run_name", inspect.getsource(handler))


class ImageCodeVersionTest(unittest.TestCase):
    def write(self, root: Path, version: object) -> None:
        root.mkdir(parents=True, exist_ok=True)
        (root / "image_manifest.json").write_text(json.dumps({"code_version": version, "files": []}), encoding="utf-8")

    def test_manifest_commit_is_used_only_without_git_and_when_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root / "clean", {"git_commit": HASH, "dirty": False})
            self.assertEqual(dispatch.code_version(root / "clean"), HASH)
            for name, version in (("dirty", {"git_commit": HASH, "dirty": True}),
                                  ("unknown_dirty", {"git_commit": HASH, "dirty": None}),
                                  ("short", {"git_commit": HASH[:12], "dirty": False}),
                                  ("missing", None)):
                with self.subTest(name=name):
                    self.write(root / name, version)
                    self.assertEqual(dispatch.code_version(root / name), "unknown")
            (root / "not_json").mkdir()
            (root / "not_json" / "image_manifest.json").write_text("{", encoding="utf-8")
            self.assertEqual(dispatch.code_version(root / "not_json"), "unknown")
            # git 메타가 있으면 git이 먼저다
            (root / "both" / ".git").mkdir(parents=True)
            (root / "both" / ".git" / "HEAD").write_text("f" * 40 + "\n")
            self.write(root / "both", {"git_commit": HASH, "dirty": False})
            self.assertEqual(dispatch.code_version(root / "both"), "f" * 40)


if __name__ == "__main__":
    unittest.main()
