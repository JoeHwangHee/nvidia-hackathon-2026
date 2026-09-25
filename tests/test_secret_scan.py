"""비밀값·로컬 경로 검사(scripts/secret_scan.py) 시험. 네트워크·키 없이 돈다.

걸려야 하는 문자열과 빼야 하는 문자열은 조각을 이어 만든다. 그래야 이 파일이 저장소 전체 검사에 걸리지 않는다.
"""
from __future__ import annotations

import contextlib
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts import secret_scan as ss

KEY = "nv" + "api" + "-" + "A1b2C3d4E5f6G7h8I9j0K1l2"
BARE_KEY_PREFIX = "`" + "nv" + "api" + "-" + "` 키"
SVC = "service" + "Key" + "=abc"
MAC_HOME = "/" + "Users" + "/someone/project/x.txt"
LINUX_HOME = "/" + "home" + "/someone/project"
MAC_TMP = "/" + "private" + "/" + "tm" + "p/x/y"
VAR_FOLDERS = "/" + "var/folders" + "/ab/cd"
TILDE = "~" + "/workspace/repo"
SEALED_DEFAULT = "~" + "/.tradesentry/sealed/"
BREW_HOME = "/" + "home" + "/linuxbrew"
SANDBOX_HOME = "/" + "home" + "/sandbox"


class ScanLineTest(unittest.TestCase):
    def kinds(self, path, line, baseline=frozenset()):
        return ss.scan_line(path, line, baseline)

    def test_each_kind_is_found(self):
        self.assertEqual(self.kinds("docs/a.md", f"키 {KEY}"), ["key"])
        self.assertEqual(self.kinds("src/a.py", f"url = '?{SVC}'"), ["svc_param"])
        self.assertEqual(self.kinds("docs/a.md", f"경로 {MAC_HOME}"), ["user_home"])
        self.assertEqual(self.kinds("docs/a.md", f"경로 {LINUX_HOME}"), ["user_home"])
        self.assertEqual(self.kinds("docs/a.md", f"경로 {MAC_TMP}"), ["tmp_dir"])
        self.assertEqual(self.kinds("docs/a.md", f"경로 {VAR_FOLDERS}"), ["tmp_dir"])
        self.assertEqual(self.kinds("docs/a.md", f"경로 `{TILDE}`"), ["tilde"])

    def test_sealed_default_is_the_only_tilde_exception(self):
        self.assertEqual(self.kinds("docs/a.md", f"봉인 폴더 `{SEALED_DEFAULT}`"), [])
        self.assertEqual(self.kinds("docs/a.md", f"`{SEALED_DEFAULT}` 와 `{TILDE}`"), ["tilde"])
        self.assertEqual(self.kinds("docs/a.md", "`" + "~" + "/.tradesentry/other/`"), ["tilde"])

    def test_bare_key_prefix_mention_is_not_a_key(self):
        # 접두어만 말하는 문장(키 문자가 뒤에 20자 이상 붙지 않음)은 키 모양이 아니다
        self.assertEqual(self.kinds("docs/a.md", BARE_KEY_PREFIX), [])

    def test_url_path_segment_is_not_a_home_path(self):
        self.assertEqual(self.kinds("docs/a.md", "https://www.example.go.kr" + "/home" + "/sub.do?x=1"), [])

    def test_container_home_excluded_only_under_container_dirs(self):
        for d in ("artifacts/openshell/", "spikes/x1/"):
            self.assertEqual(self.kinds(d + "logs/a.txt", f"  - {BREW_HOME}"), [], d)
            self.assertEqual(self.kinds(d + "a.py", f'    "{SANDBOX_HOME}",'), [], d)
        # 같은 경로라도 다른 폴더면 걸린다
        self.assertEqual(self.kinds("docs/rules/a.md", f"  - {BREW_HOME}"), ["user_home"])
        self.assertEqual(self.kinds("artifacts/eval/a.md", f"  - {BREW_HOME}"), ["user_home"])
        # 컨테이너 폴더라도 다른 홈 경로와 macOS 경로는 걸린다
        self.assertEqual(self.kinds("artifacts/openshell/a.txt", f"  - {LINUX_HOME}"), ["user_home"])
        self.assertEqual(self.kinds("artifacts/openshell/a.txt", f"  - {MAC_HOME}"), ["user_home"])
        self.assertEqual(self.kinds("artifacts/openshell/a.txt", f"  - {BREW_HOME}x/y"), ["user_home"])
        self.assertEqual(self.kinds("artifacts/openshell/a.txt", f"{BREW_HOME} {LINUX_HOME}"), ["user_home"])

    def test_historical_baseline_is_per_line_and_root_only(self):
        line = f"예전 문장 `{TILDE}`"
        baseline = frozenset({("OLD.md", ss._line_sha(line))})
        self.assertEqual(self.kinds("OLD.md", line, baseline), [])
        self.assertEqual(self.kinds("OLD.md", line + " 바뀜", baseline), ["tilde"])
        self.assertEqual(self.kinds("docs/OLD.md", line, frozenset({("docs/OLD.md", ss._line_sha(line))})),
                         ["tilde"])

    def test_committed_baseline_rows_are_root_history_docs(self):
        for path, digest in ss.HISTORICAL_BASELINE:
            self.assertNotIn("/", path)
            self.assertTrue(path.endswith(".md"))
            self.assertEqual(len(digest), 64)

    def test_script_and_this_test_do_not_flag_themselves(self):
        root = Path(__file__).resolve().parents[1]
        for rel in ("scripts/secret_scan.py", "tests/test_secret_scan.py"):
            text = (root / rel).read_text(encoding="utf-8")
            self.assertEqual(ss.scan_text(rel, text), [], rel)


class GitModesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.com")
        self.env = env
        self.git("init", "-q")
        (self.repo / "a.md").write_text("깨끗한 문장\n", encoding="utf-8")
        self.git("add", "a.md")
        self.git("commit", "-q", "-m", "base")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, env=self.env, check=True, capture_output=True)

    def run_main(self, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            code = ss.main(list(args), repo=self.repo)
        return code, buf.getvalue()

    def test_tree_mode_clean_then_dirty(self):
        self.assertEqual(self.run_main()[0], 0)
        (self.repo / "b.md").write_text(f"x\n경로 {MAC_HOME}\n", encoding="utf-8")
        self.git("add", "b.md")
        code, out = self.run_main()
        self.assertEqual(code, 1)
        self.assertIn("b.md:2 user_home", out)
        self.assertNotIn("someone", out)  # 행 내용은 내지 않는다

    def test_untracked_file_is_not_scanned(self):
        (self.repo / "c.md").write_text(f"{KEY}\n", encoding="utf-8")
        self.assertEqual(self.run_main()[0], 0)

    def test_range_mode_sees_only_added_lines(self):
        (self.repo / "a.md").write_text(f"깨끗한 문장\n키 {KEY}\n", encoding="utf-8")
        self.git("commit", "-q", "-am", "add")
        code, out = self.run_main("HEAD~1..HEAD")
        self.assertEqual(code, 1)
        self.assertIn("a.md +1 key", out)
        self.assertNotIn(KEY, out)
        # 그 행을 지우는 커밋의 범위에는 추가 행이 없다
        (self.repo / "a.md").write_text("깨끗한 문장\n", encoding="utf-8")
        self.git("commit", "-q", "-am", "remove")
        self.assertEqual(self.run_main("HEAD~1..HEAD")[0], 0)

    def test_bad_range_and_bad_args(self):
        self.assertEqual(self.run_main("no-such-ref..HEAD")[0], 2)
        self.assertEqual(self.run_main("--help")[0], 2)
        self.assertEqual(self.run_main("a", "b")[0], 2)


if __name__ == "__main__":
    unittest.main()
