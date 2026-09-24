"""CLI 뼈대 시험(단위 F1 인자 검증·F2 명령 배선): 도움말은 종료 코드 0, 모드는 4개 값만, 구현되지 않은 명령은
분명한 오류 문장과 0이 아닌 종료 코드(3)로 끝난다. 네트워크와 키 없이 돈다.
"""
import io
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

from tradesentry.cli import args, dispatch

COMMANDS = ["snapshot-build", "snapshot-verify", "detect", "run-case", "evaluate"]  # 자료 계약 §10
MODES = ("checklist", "agent", "full", "freeform")  # 자료 계약 §4.1


def call(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with mock.patch("sys.stdout", out), mock.patch("sys.stderr", err):
        try:
            code = dispatch.main(argv)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    def test_commands_and_modes_match_contract(self):
        self.assertEqual(list(args.COMMANDS), COMMANDS)
        self.assertEqual(args.MODES, MODES)
        self.assertEqual(list(dispatch.ASSEMBLIES), COMMANDS)

    def test_help_exits_zero(self):
        code, out, _ = call(["--help"])
        self.assertEqual(code, 0)
        for command in COMMANDS:
            self.assertIn(command, out)
        for command in COMMANDS:
            with self.subTest(command=command):
                code, out, _ = call([command, "--help"])
                self.assertEqual(code, 0)
                for option in ("--snapshot", "--policy", "--mode"):
                    self.assertIn(option, out)

    def test_unimplemented_commands_fail_clearly(self):
        for command in COMMANDS:
            with self.subTest(command=command):
                code, _, err = call([command, "--snapshot", "controlled_fixture_v0", "--policy", "policy_v1",
                                     "--mode", "full"])
                self.assertEqual(code, dispatch.EXIT_NOT_IMPLEMENTED)
                self.assertNotEqual(code, 0)
                self.assertIn(f"tradesentry {command}는 아직 구현되지 않았다", err)

    def test_mode_accepts_only_four_values(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                self.assertEqual(call(["run-case", "--mode", mode])[0], dispatch.EXIT_NOT_IMPLEMENTED)
        code, _, err = call(["run-case", "--mode", "fast"])
        self.assertEqual(code, 2)
        self.assertIn("--mode", err)

    def test_command_is_required(self):
        self.assertEqual(call([])[0], 2)
        self.assertEqual(call(["collect"])[0], 2)

    def test_abbreviated_options_are_refused(self):
        for argv in (["detect", "--snap", "x"], ["run-case", "--mo", "full"], ["evaluate", "--pol", "policy_v1"]):
            with self.subTest(argv=argv):
                code, _, err = call(argv)
                self.assertEqual(code, 2)
                self.assertIn(argv[1], err)
        self.assertEqual(call(["detect", "--snapshot", "x"])[0], dispatch.EXIT_NOT_IMPLEMENTED)  # 온전한 이름은 받는다

    def test_module_and_installed_script_help(self):
        result = subprocess.run([sys.executable, "-m", "tradesentry.cli", "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        script = Path(sys.executable).parent / "tradesentry"
        if not script.exists():
            self.skipTest("설치 명령 tradesentry가 없는 파이썬으로 돌렸다(uv run으로 돌리면 있다)")
        result = subprocess.run([str(script), "detect", "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([str(script), "detect"], capture_output=True, text=True)
        self.assertEqual(result.returncode, dispatch.EXIT_NOT_IMPLEMENTED)


if __name__ == "__main__":
    unittest.main()
