"""CLI 시험(단위 F1 인자 검증·F2 명령 배선). 네트워크와 키 없이 돈다.

- 도움말은 종료 코드 0, 모드는 4개 값만, 옵션 줄임은 종료 코드 2다.
- 명령 배선은 처리 함수 표(dispatch.HANDLERS)를 가짜로 바꿔 시험한다. 그래서 실제 명령을 조립체와 이어도(구현
  상태가 바뀌어도) 이 시험들은 깨지지 않는다. "처리 함수가 NotImplementedError를 내면 분명한 오류 문장과 종료
  코드 3"은 명령마다 따로 시험해, 한 명령을 잇는 PR이 다른 명령의 시험을 건드리지 않게 한다.
"""
import argparse
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


def not_wired(namespace: argparse.Namespace) -> int:
    """아직 잇지 않은 명령을 흉내 내는 가짜 처리 함수."""
    raise NotImplementedError("가짜 처리 함수: 아직 잇지 않았다")


class FakeHandler:
    """받은 인자를 적어 두고 정해진 종료 코드를 돌려주는 가짜 처리 함수."""

    def __init__(self, code: int = 0):
        self.code = code
        self.seen: list[argparse.Namespace] = []

    def __call__(self, namespace: argparse.Namespace) -> int:
        self.seen.append(namespace)
        return self.code


class CliTest(unittest.TestCase):
    def test_commands_and_modes_match_contract(self):
        self.assertEqual(list(args.COMMANDS), COMMANDS)
        self.assertEqual(args.MODES, MODES)
        self.assertEqual(list(dispatch.ASSEMBLIES), COMMANDS)
        self.assertEqual(list(dispatch.HANDLERS), COMMANDS)

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

    def test_handler_gets_parsed_options_and_its_exit_code_is_returned(self):
        handler = FakeHandler(code=5)
        with mock.patch.dict(dispatch.HANDLERS, {"evaluate": handler}):
            code, _, err = call(["evaluate", "--snapshot", "controlled_fixture_v0", "--policy", "policy_v1",
                                 "--mode", "full"])
        self.assertEqual(code, 5)
        self.assertEqual(err, "")
        namespace = handler.seen[0]
        self.assertEqual((namespace.command, namespace.snapshot, namespace.policy, namespace.mode),
                         ("evaluate", "controlled_fixture_v0", "policy_v1", "full"))

    def test_mode_accepts_only_four_values(self):
        for mode in MODES:
            handler = FakeHandler()
            with self.subTest(mode=mode), mock.patch.dict(dispatch.HANDLERS, {"run-case": handler}):
                self.assertEqual(call(["run-case", "--mode", mode])[0], 0)
                self.assertEqual(handler.seen[0].mode, mode)
        code, _, err = call(["run-case", "--mode", "fast"])  # 처리 함수에 닿기 전 인자 오류
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
        handler = FakeHandler()
        with mock.patch.dict(dispatch.HANDLERS, {"detect": handler}):
            self.assertEqual(call(["detect", "--snapshot", "x"])[0], 0)  # 온전한 이름은 받는다
        self.assertEqual(handler.seen[0].snapshot, "x")

    def test_module_and_installed_script(self):
        result = subprocess.run([sys.executable, "-m", "tradesentry.cli", "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        script = Path(sys.executable).parent / "tradesentry"
        if not script.exists():
            self.skipTest("설치 명령 tradesentry가 없는 파이썬으로 돌렸다(uv run으로 돌리면 있다)")
        result = subprocess.run([str(script), "detect", "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run([str(script), "detect", "--snap", "x"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)  # 인자 오류는 구현 상태와 관계없다


class NotImplementedCommandTest(unittest.TestCase):
    """명령마다 따로: 처리 함수가 NotImplementedError를 내면 분명한 오류 문장과 종료 코드 3으로 끝난다."""

    def check(self, command: str) -> None:
        with mock.patch.dict(dispatch.HANDLERS, {command: not_wired}):
            code, out, err = call([command, "--snapshot", "controlled_fixture_v0", "--policy", "policy_v1",
                                   "--mode", "full"])
        self.assertEqual(code, dispatch.EXIT_NOT_IMPLEMENTED)
        self.assertEqual(out, "")
        self.assertIn(f"tradesentry {command}는 아직 구현되지 않았다", err)

    def test_snapshot_build(self):
        self.check("snapshot-build")

    def test_snapshot_verify(self):
        self.check("snapshot-verify")

    def test_detect(self):
        self.check("detect")

    def test_run_case(self):
        self.check("run-case")

    def test_evaluate(self):
        self.check("evaluate")


if __name__ == "__main__":
    unittest.main()
