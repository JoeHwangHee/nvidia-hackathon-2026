"""단위 F2(cli_dispatch) 배선 시험. 네트워크와 키 없이 돈다.

- main은 단위 F1을 한 번만 부르고, 검증된 고칠 수 없는 요청(args.Request)만 처리 함수에 넘긴다.
- 종료 코드: 아직 잇지 않은 명령(자리표시)만 3, 이은 처리 함수의 예외는 1(예외 이름만 적는다), 허용하지 않는 반환값·
  SystemExit·배선 계약 위반은 4, 중단(KeyboardInterrupt)은 130. main 밖으로 호출 경로 기록이 나가지 않는다(표준 출력·
  오류가 한국어를 못 쓰는 인코딩일 때 포함).
- snapshot-build·snapshot-verify 배선: 단위 S2·S3은 대역으로 바꾼다(로드맵 DT1이 구현한다). 실행 폴더의 부모는 시험마다
  새 임시 폴더다. 대역은 불리는 순간 실행 폴더가 이미 하나 있고 비어 있는지 본다(실행명은 단위보다 먼저 확보한다, N8).
- 실행명 확보(자료 계약 §10.3 N8): 가짜 시계로 이름 형식(KST), 충돌 때 다음 초, 다른 부모 폴더의 같은 이름, 기다리기,
  포기를 본다.
시험에 쓰는 절대경로 모양 값은 개발 기계에 없는 가짜 경로(/srv/probe 아래)다.
"""
import contextlib
import dataclasses
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest import mock

from tradesentry.cli import args, dispatch

ARGV = {
    "snapshot-build": ["snapshot-build", "--snapshot", "controlled_fixture_v0"],
    "snapshot-verify": ["snapshot-verify", "--snapshot", "controlled_fixture_v0"],
    "detect": ["detect", "--snapshot", "controlled_fixture_v0", "--policy", "dev-0.1"],
    "run-case": ["run-case", "--snapshot", "controlled_fixture_v0", "--policy", "dev-0.1", "--mode", "full",
                 "--case", "A-composition"],
    "evaluate": ["evaluate", "--snapshot", "controlled_fixture_v0", "--policy", "dev-0.1", "--mode", "full"],
}


def call(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = dispatch.main(argv)
    return code, out.getvalue(), err.getvalue()


class Recorder:
    """받은 요청을 적어 두고 정해진 값을 돌려주는 가짜 처리 함수."""

    def __init__(self, result: object = 0):
        self.result = result
        self.seen: list[args.Request] = []

    def __call__(self, request: args.Request) -> object:
        self.seen.append(request)
        return self.result


def raising(exc: BaseException):
    def handler(request: args.Request) -> int:
        raise exc

    return handler


class MainTest(unittest.TestCase):
    def test_parse_runs_once_and_the_handler_gets_the_validated_request(self):
        recorder = Recorder()
        with mock.patch.object(args, "parse", wraps=args.parse) as parse, \
                mock.patch.dict(dispatch.HANDLERS, {"run-case": recorder}):
            code, out, err = call(ARGV["run-case"])
        self.assertEqual((code, out, err), (0, "", ""))
        self.assertEqual(parse.call_count, 1)
        self.assertEqual(recorder.seen, [args.Request("run-case", "controlled_fixture_v0", "dev-0.1", "full",
                                                      "A-composition")])
        self.assertIs(type(recorder.seen[0]), args.Request)

    def test_invalid_arguments_never_reach_the_handler(self):
        recorder = Recorder()
        bad_calls = (["detect", "--snapshot", "controlled_fixture_v0", "--policy", "policy_v1.json"],
                     ["detect", "--snapshot", "Controlled", "--policy", "dev-0.1"],
                     ["detect", "--snapshot", "controlled_fixture_v0"],
                     ARGV["detect"] + ["--policy", "dev-0.1"],
                     ARGV["detect"] + ["--mode", "fast"],  # 쓰지 않는 공통 옵션도 값 형식은 검사한다
                     ARGV["detect"] + ["--case", "A-composition"])  # --case는 run-case만 받는다
        with mock.patch.dict(dispatch.HANDLERS, {"detect": recorder}):
            for argv in bad_calls:
                with self.subTest(argv=argv):
                    self.assertEqual(call(argv)[0], 2)
        self.assertEqual(recorder.seen, [])

    def test_help_returns_zero_without_system_exit(self):
        code, out, _ = call(["--help"])
        self.assertEqual(code, 0)
        self.assertIn("snapshot-verify", out)
        self.assertEqual(call(["detect", "--help"])[0], 0)

    def test_the_request_cannot_be_changed_by_a_handler(self):
        def mutate(request: args.Request) -> int:
            request.snapshot_id = "kcs_202201_202412_v2"
            return 0

        with mock.patch.dict(dispatch.HANDLERS, {"detect": mutate}):
            code, _, err = call(ARGV["detect"])
        self.assertEqual(code, dispatch.EXIT_FAILED)
        self.assertIn(dataclasses.FrozenInstanceError.__name__, err)

    def test_run_returns_only_the_exit_code(self):
        with mock.patch.dict(dispatch.HANDLERS, {"detect": dispatch._not_wired}), \
                contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(dispatch.run(ARGV["detect"]), {"exit_code": 3})
            self.assertEqual(dispatch.run(["--help"]), {"exit_code": 0})
            self.assertEqual(dispatch.run(["detect"]), {"exit_code": 2})
        for bad in (None, "detect", ("detect",), ["detect", 1]):
            with self.subTest(bad=bad), self.assertRaises(TypeError):
                dispatch.run(bad)

    def test_help_and_argument_errors_do_not_import_assemblies(self):
        probe = ("import contextlib, io, sys\n"
                 "from tradesentry.cli import dispatch\n"
                 "with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):\n"
                 "    codes = [dispatch.main(['--help']), dispatch.main(['snapshot-build', '--snapshot', 'X'])]\n"
                 "print(codes, sorted(m for m in sys.modules if m.split('.')[:2] == ['tradesentry', 'snapshot']))\n")
        result = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "[0, 2] []")


class ExitCodeTest(unittest.TestCase):
    def test_placeholder_gives_3_without_being_called(self):
        for command in ARGV:
            with self.subTest(command=command), mock.patch.dict(dispatch.HANDLERS, {command: dispatch._not_wired}):
                code, out, err = call(ARGV[command])
                self.assertEqual(code, dispatch.EXIT_NOT_IMPLEMENTED)
                self.assertEqual(out, "")
                self.assertIn(f"tradesentry {command}는 아직 구현되지 않았다", err)
                self.assertIn(dispatch.ASSEMBLIES[command], err)

    def test_not_implemented_inside_a_wired_handler_is_a_failure(self):
        with mock.patch.dict(dispatch.HANDLERS, {"detect": raising(NotImplementedError("부른 단위가 아직 뼈대다"))}):
            code, _, err = call(ARGV["detect"])
        self.assertEqual(code, dispatch.EXIT_FAILED)
        self.assertIn("NotImplementedError", err)
        self.assertNotIn("아직 구현되지 않았다", err)

    def test_unexpected_exception_prints_only_its_name(self):
        with mock.patch.dict(dispatch.HANDLERS, {"detect": raising(KeyError("/srv/probe/secret.txt"))}):
            code, out, err = call(ARGV["detect"])
        self.assertEqual(code, dispatch.EXIT_FAILED)
        self.assertEqual(out, "")
        self.assertIn("KeyError", err)
        for leak in ("/srv", "probe", "secret", "Traceback"):
            self.assertNotIn(leak, err)

    def test_allowed_handler_results_pass_through(self):
        for result in (0, 1, 5, 255):
            with self.subTest(result=result), mock.patch.dict(dispatch.HANDLERS, {"evaluate": Recorder(result)}):
                self.assertEqual(call(ARGV["evaluate"])[0], result)

    def test_other_handler_results_are_wiring_errors(self):
        for result in (None, "0", 0.0, True, False, 256, -1, 2, 3, 4, 130, Decimal("0"), Path("x")):
            with self.subTest(result=result), mock.patch.dict(dispatch.HANDLERS, {"evaluate": Recorder(result)}):
                code, _, err = call(ARGV["evaluate"])
                self.assertEqual(code, dispatch.EXIT_WIRING)
                self.assertIn("허용하지 않는 종료 코드", err)

    def test_system_exit_in_a_handler_is_a_wiring_error(self):
        for exc in (SystemExit(0), SystemExit(None), SystemExit("끝")):
            with self.subTest(exc=exc), mock.patch.dict(dispatch.HANDLERS, {"detect": raising(exc)}):
                code, _, err = call(ARGV["detect"])
                self.assertEqual(code, dispatch.EXIT_WIRING)
                self.assertIn("SystemExit", err)

    def test_wiring_error_gives_4_with_its_message(self):
        with mock.patch.dict(dispatch.HANDLERS, {"detect": raising(dispatch.WiringError("출력 모양이 다르다"))}):
            code, _, err = call(ARGV["detect"])
        self.assertEqual(code, dispatch.EXIT_WIRING)
        self.assertIn("출력 모양이 다르다", err)

    def test_exit_code_table(self):
        self.assertEqual((dispatch.EXIT_OK, dispatch.EXIT_FAILED, dispatch.EXIT_USAGE, dispatch.EXIT_NOT_IMPLEMENTED,
                          dispatch.EXIT_WIRING, dispatch.EXIT_INTERRUPTED), (0, 1, 2, 3, 4, 130))
        self.assertEqual(dispatch.CLI_EXIT_CODES, {2, 3, 4, 130})


class EntryPointTest(unittest.TestCase):
    """main 밖으로 호출 경로 기록(traceback)이 나가지 않는다(결정 기록 20260924-2356 ⑤, 보안 검토 1회차 권고 2)."""

    def assert_name_only(self, err: str, name: str) -> None:
        self.assertIn(name, err)
        for leak in ("Traceback", 'File "', "/srv", "probe", "secret"):
            self.assertNotIn(leak, err)

    def test_interrupt_in_a_handler(self):
        with mock.patch.dict(dispatch.HANDLERS, {"detect": raising(KeyboardInterrupt())}):
            code, out, err = call(ARGV["detect"])
        self.assertEqual((code, out), (dispatch.EXIT_INTERRUPTED, ""))
        self.assert_name_only(err, "KeyboardInterrupt")

    def test_interrupt_while_parsing(self):
        with mock.patch.object(args, "parse", side_effect=KeyboardInterrupt()):
            code, _, err = call(ARGV["detect"])
        self.assertEqual(code, dispatch.EXIT_INTERRUPTED)
        self.assert_name_only(err, "KeyboardInterrupt")

    def test_unexpected_exception_while_parsing(self):
        with mock.patch.object(args, "parse", side_effect=RuntimeError("/srv/probe/secret.txt")):
            code, _, err = call(ARGV["detect"])
        self.assertEqual(code, dispatch.EXIT_FAILED)
        self.assert_name_only(err, "RuntimeError")

    def test_ascii_only_standard_streams_keep_the_exit_codes(self):
        env = dict(os.environ, PYTHONIOENCODING="ascii", PYTHONUTF8="0")
        cases = ((["--help"], 0), (["detect", "--snapshot", "Bad", "--policy", "dev-0.1"], 2),
                 (ARGV["detect"], 3))  # 3은 한국어 오류 문장을 쓰고도 1로 바뀌지 않는다
        for argv, expected in cases:
            with self.subTest(argv=argv):
                result = subprocess.run([sys.executable, "-m", "tradesentry.cli", *argv], capture_output=True, env=env)
                self.assertEqual(result.returncode, expected, result.stderr[-400:])
                for leak in (b"Traceback", b'File "'):
                    self.assertNotIn(leak, result.stderr)


class TempOutputs(unittest.TestCase):
    """실행 폴더의 부모(dispatch.OUTPUT_PARENT)를 시험마다 새 임시 폴더로 바꾼다."""

    def setUp(self):
        super().setUp()
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.count = 0
        self.outputs = self.root / "outputs"
        patcher = mock.patch.object(dispatch, "OUTPUT_PARENT", self.outputs)
        patcher.start()
        self.addCleanup(patcher.stop)

    def fresh_outputs(self) -> Path:
        """호출마다 새 부모 폴더. 같은 초에 같은 실행명을 다투며 다음 초까지 기다리는 일을 없앤다."""
        self.count += 1
        self.outputs = self.root / f"outputs{self.count}"
        return self.outputs

    def run_dirs(self, run_name: str) -> list[Path]:
        return sorted(p for p in self.outputs.iterdir() if re.fullmatch(rf"{run_name}-\d{{12}}", p.name))


class SnapshotWiringTest(TempOutputs):
    SQLITE = b"SQLite format 3\x00probe"

    def call_unit(self, target: str, run_name: str, argv: list[str], result: object,
                  error: BaseException | None) -> tuple[int, str, str, mock.Mock]:
        """단위를 대역으로 바꿔 명령을 부른다. 대역은 불리는 순간의 실행 폴더를 적어 두고, 부른 뒤 그 폴더가 정확히 하나이고
        비어 있었는지 본다. 실행명은 단위를 부르기 전에 확보한다(자료 계약 §10.3 N8, 평가 검토 1회차 권고 4)."""
        seen: list[list[tuple[str, list[str]]]] = []

        def unit(inp: object) -> object:
            dirs = self.run_dirs(run_name) if self.outputs.exists() else []
            seen.append([(p.name, sorted(q.name for q in p.iterdir())) for p in dirs])
            if error is not None:
                raise error
            return result

        stub = mock.Mock(side_effect=unit)
        with mock.patch(target, stub), mock.patch.object(dispatch, "OUTPUT_PARENT", self.fresh_outputs()):
            code, out, err = call(argv)
        self.assertEqual(len(seen), 1, "단위를 한 번 불렀다")
        self.assertEqual(len(seen[0]), 1, f"단위를 부를 때 {run_name} 실행 폴더가 정확히 하나 있다")
        name, contents = seen[0][0]
        self.assertRegex(name, rf"^{run_name}-\d{{12}}$")
        self.assertEqual(contents, [], "단위를 부를 때 실행 폴더는 비어 있다")
        return code, out, err, stub

    def build(self, value: object, argv: list[str] | None = None,
              error: BaseException | None = None) -> tuple[int, str, str, mock.Mock]:
        return self.call_unit("tradesentry.snapshot.build.run", "snapshot_build", argv or ARGV["snapshot-build"],
                              value, error)

    def verify(self, value: object, argv: list[str] | None = None,
               error: BaseException | None = None) -> tuple[int, str, str, mock.Mock]:
        return self.call_unit("tradesentry.snapshot.verify.run", "snapshot_verify", argv or ARGV["snapshot-verify"],
                              value, error)

    def test_snapshot_build_writes_the_sqlite_bytes(self):
        code, out, err, stub = self.build(self.SQLITE, ARGV["snapshot-build"] + ["--policy", "dev-0.1"])
        self.assertEqual((code, err), (0, ""))
        stub.assert_called_once_with({"snapshot_id": "controlled_fixture_v0", "policy_version": "dev-0.1"})
        [run_dir] = self.run_dirs("snapshot_build")
        stamp = run_dir.name.split("-")[1]
        output = run_dir / f"snapshot_build-{stamp}.sqlite"
        self.assertEqual([p.name for p in run_dir.iterdir()], [output.name])
        self.assertEqual(output.read_bytes(), self.SQLITE)
        self.assertEqual(out, f"outputs/{run_dir.name}/{output.name}\n")  # 상대경로만 적는다(N13)

    def test_snapshot_build_without_policy(self):
        code, _, _, stub = self.build(bytearray(self.SQLITE), ARGV["snapshot-build"])
        self.assertEqual(code, 0)
        stub.assert_called_once_with({"snapshot_id": "controlled_fixture_v0", "policy_version": None})

    def test_snapshot_build_output_must_be_bytes(self):
        code, out, err, _ = self.build({"rows": 1}, ARGV["snapshot-build"])
        self.assertEqual(code, dispatch.EXIT_WIRING)
        self.assertEqual(out, "")
        self.assertIn("바이트가 아니다", err)
        self.assertEqual(list(self.outputs.rglob("*.sqlite")), [])

    def test_snapshot_verify_pass(self):
        report = {"ok": True, "snapshot_id": "controlled_fixture_v0", "share": Decimal("20.30")}
        code, out, err, stub = self.verify(report)
        self.assertEqual((code, err), (0, ""))
        stub.assert_called_once_with({"snapshot_id": "controlled_fixture_v0"})
        [run_dir] = self.run_dirs("snapshot_verify")
        [output] = list(run_dir.iterdir())
        self.assertEqual(output.name, f"snapshot_verify-{run_dir.name.split('-')[1]}.json")
        self.assertEqual(json.loads(output.read_text(encoding="utf-8")),
                         {"ok": True, "snapshot_id": "controlled_fixture_v0", "share": "20.30"})
        self.assertEqual(out, f"outputs/{run_dir.name}/{output.name}\n")

    def test_snapshot_verify_fail_still_writes_the_report(self):
        code, out, err, _ = self.verify({"ok": False, "problems": ["행 수가 다르다"]})
        self.assertEqual(code, dispatch.EXIT_FAILED)
        self.assertIn("불합격", err)
        [run_dir] = self.run_dirs("snapshot_verify")
        self.assertEqual(len(list(run_dir.iterdir())), 1)
        self.assertTrue(out.startswith("outputs/snapshot_verify-"))

    def test_snapshot_verify_without_a_true_or_false_verdict_is_not_a_pass(self):
        for report in ({"snapshot_id": "controlled_fixture_v0"}, {"ok": "true"}, {"ok": 1}, {"ok": None},
                       [True], "ok"):
            with self.subTest(report=report):
                code, _, err, _ = self.verify(report)
                self.assertEqual(code, dispatch.EXIT_WIRING)
                self.assertIn("합격 표시 ok", err)

    def test_snapshot_verify_report_must_be_json(self):
        code, _, err, _ = self.verify({"ok": True, "value": object()})
        self.assertEqual(code, dispatch.EXIT_WIRING)
        self.assertIn("JSON으로 쓸 수 없다", err)
        self.assertEqual(list(self.outputs.rglob("*.json")), [])

    def test_unit_errors_are_failures_not_3_and_leave_the_reserved_folder(self):
        for helper, run_name in ((self.build, "snapshot_build"), (self.verify, "snapshot_verify")):
            with self.subTest(run_name=run_name):
                code, out, err, _ = helper(None, error=NotImplementedError("뼈대"))
                self.assertEqual((code, out), (dispatch.EXIT_FAILED, ""))
                self.assertIn("NotImplementedError", err)
                [run_dir] = self.run_dirs(run_name)
                self.assertEqual(list(run_dir.iterdir()), [])  # 단위보다 먼저 확보한 빈 실행 폴더가 남는다(N8)

    def test_unit_inputs(self):
        request = args.parse(ARGV["snapshot-build"] + ["--policy", "policy_v1"])
        self.assertEqual(dispatch.snapshot_build_input(request),
                         {"snapshot_id": "controlled_fixture_v0", "policy_version": "policy_v1"})
        self.assertEqual(dispatch.snapshot_verify_input(args.parse(ARGV["snapshot-verify"])),
                         {"snapshot_id": "controlled_fixture_v0"})

    def test_unused_common_options_are_not_passed_to_the_units(self):
        code, _, _, stub = self.build(self.SQLITE, ARGV["snapshot-build"] + ["--mode", "agent"])
        self.assertEqual(code, 0)
        stub.assert_called_once_with({"snapshot_id": "controlled_fixture_v0", "policy_version": None})
        code, _, _, stub = self.verify({"ok": True}, ARGV["snapshot-verify"] + ["--policy", "dev-0.1", "--mode", "full"])
        self.assertEqual(code, 0)
        stub.assert_called_once_with({"snapshot_id": "controlled_fixture_v0"})


class FakeClock:
    """정해진 시각에서 시작하고 sleep만큼 흐르는 시계. sleep 호출 값을 적어 둔다."""

    def __init__(self, start: datetime):
        self.now = start
        self.sleeps: list[float] = []

    def __call__(self) -> datetime:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += timedelta(seconds=seconds)


class ReserveRunDirTest(TempOutputs):
    START = datetime(2026, 9, 24, 16, 2, 3, 500000, tzinfo=timezone.utc)  # KST 2026-09-25 01:02:03.5

    def reserve(self, clock: FakeClock) -> tuple[str, str, Path]:
        return dispatch.reserve_run_dir("snapshot_build", clock=clock, sleep=clock.sleep)

    def test_name_uses_kst_whatever_the_clock_zone(self):
        clock = FakeClock(self.START)
        run_id, stamp, run_dir = self.reserve(clock)
        self.assertEqual((run_id, stamp), ("snapshot_build-260925010203", "260925010203"))
        self.assertEqual(run_dir, self.outputs / run_id)
        self.assertTrue(run_dir.is_dir())
        self.assertEqual(clock.sleeps, [])

    def test_taken_name_moves_to_the_next_second_after_waiting(self):
        self.outputs.mkdir(parents=True)
        (self.outputs / "snapshot_build-260925010203").mkdir()
        clock = FakeClock(self.START)
        run_id, _, _ = self.reserve(clock)
        self.assertEqual(run_id, "snapshot_build-260925010204")
        self.assertEqual(clock.sleeps, [0.5])  # 그 초가 될 때까지 기다린다

    def test_same_name_under_the_sealed_parent_is_given_up(self):
        (self.outputs / "sealed" / "snapshot_build-260925010203").mkdir(parents=True)
        run_id, _, _ = self.reserve(FakeClock(self.START))
        self.assertEqual(run_id, "snapshot_build-260925010204")
        self.assertFalse((self.outputs / "snapshot_build-260925010203").exists())  # 방금 만든 빈 폴더를 지웠다

    def test_gives_up_after_the_attempt_limit(self):
        self.outputs.mkdir(parents=True)
        base = datetime(2026, 9, 25, 1, 2, 3, tzinfo=dispatch.KST)
        for offset in range(dispatch.MAX_ATTEMPTS):
            (self.outputs / f"snapshot_build-{(base + timedelta(seconds=offset)).strftime('%y%m%d%H%M%S')}").mkdir()
        with self.assertRaises(dispatch.RunNameError):
            self.reserve(FakeClock(self.START))

    def test_output_file_is_never_overwritten(self):
        run_id, stamp, run_dir = self.reserve(FakeClock(self.START))
        dispatch.write_output(run_dir, run_id, "snapshot_verify", stamp, "json", {"ok": True})
        with self.assertRaises(FileExistsError):
            dispatch.write_output(run_dir, run_id, "snapshot_verify", stamp, "json", {"ok": False})
        with self.assertRaises(dispatch.WiringError):
            dispatch.write_output(run_dir, run_id, "snapshot_verify", stamp, "csv", "a,b\n")


if __name__ == "__main__":
    unittest.main()
