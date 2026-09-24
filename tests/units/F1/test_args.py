"""단위 F1(cli_args) 인자 검증 시험. 네트워크와 키 없이 돈다.

골든 쌍(test_golden.py)은 올바른 run-case 요청 하나다. 여기서는 명령별 옵션 표(공통 옵션 셋은 다섯 명령이 모두 받고,
명령이 쓰지 않는 옵션은 값 형식만 검사해 요청에 그대로 남긴다), 값 형식(스냅샷 ID·정책 버전 이름·모드·사례 인자), 경로 거부,
같은 옵션 반복 거부, 옵션 줄임 거부, 오류 문장이 받은 값을 되풀이하지 않는 것을 본다.
시험에 쓰는 절대경로 모양 값은 개발 기계에 없는 가짜 경로(/srv/probe 아래)다.
"""
import contextlib
import dataclasses
import io
import os
import unittest
from unittest import mock

from tradesentry.cli import args

SAMPLE = {"snapshot": "controlled_fixture_v0", "policy": "dev-0.1", "mode": "full", "case": "A-composition"}
FIELD = {"snapshot": "snapshot_id", "policy": "policy_version", "mode": "mode", "case": "case"}
LONG = "a" * 64


def argv_for(command: str, **values: str) -> list[str]:
    """명령이 받는 옵션을 모두 채운 인자 목록. values로 옵션 값을 바꾼다."""
    argv = [command]
    for option in args.COMMAND_OPTIONS[command]:
        argv += [f"--{option}", values.get(option, SAMPLE[option])]
    return argv


def parse_error(argv: list[str]) -> tuple[int, str]:
    """인자 오류를 기대하고 (종료 코드, 표준 오류)를 돌려준다."""
    err, out = io.StringIO(), io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
        try:
            request = args.parse(argv)
        except SystemExit as exc:
            return exc.code, err.getvalue()
    raise AssertionError(f"인자 오류가 나야 하는데 요청이 만들어졌다: {request}")


class CommandOptionTableTest(unittest.TestCase):
    def test_every_command_takes_the_three_common_options(self):
        self.assertEqual(args.COMMON_OPTIONS, ("snapshot", "policy", "mode"))  # 자료 계약 §10 CLI 행의 공통 옵션
        self.assertEqual(list(args.COMMAND_OPTIONS), list(args.COMMANDS))
        for command, options in args.COMMAND_OPTIONS.items():
            with self.subTest(command=command):
                self.assertLessEqual(set(args.COMMON_OPTIONS), set(options))
                self.assertLessEqual(set(options), set(args.OPTIONS))
                self.assertLessEqual(set(options.values()), {args.REQUIRED, args.OPTIONAL, args.UNUSED})
                self.assertEqual(options["snapshot"], args.REQUIRED)  # 모든 명령은 스냅샷 하나를 대상으로 한다
        self.assertEqual([command for command, options in args.COMMAND_OPTIONS.items() if "case" in options],
                         ["run-case"])  # --case는 공통 옵션이 아니다

    def test_roles(self):
        # snapshot-verify: 평가 스킬 ② 사전 점검·룰북 B3이 --snapshot 하나로 부른다. evaluate: 룰북 B7의 재현 명령 형식
        R, O, U = args.REQUIRED, args.OPTIONAL, args.UNUSED
        self.assertEqual(args.COMMAND_OPTIONS, {
            "snapshot-build": {"snapshot": R, "policy": O, "mode": U},
            "snapshot-verify": {"snapshot": R, "policy": U, "mode": U},
            "detect": {"snapshot": R, "policy": R, "mode": U},
            "run-case": {"snapshot": R, "policy": R, "mode": R, "case": R},
            "evaluate": {"snapshot": R, "policy": R, "mode": R},
        })

    def test_each_command_keeps_every_value_it_was_given(self):
        for command, options in args.COMMAND_OPTIONS.items():
            with self.subTest(command=command):
                request = args.parse(argv_for(command))
                self.assertIsInstance(request, args.Request)
                self.assertEqual(request.command, command)
                for option, field in FIELD.items():
                    expected = SAMPLE[option] if option in options else None
                    self.assertEqual(getattr(request, field), expected, field)

    def test_only_required_options_are_needed(self):
        for command, options in args.COMMAND_OPTIONS.items():
            argv = [command]
            for option, role in options.items():
                if role == args.REQUIRED:
                    argv += [f"--{option}", SAMPLE[option]]
            with self.subTest(command=command):
                request = args.parse(argv)
                for option, field in FIELD.items():
                    expected = SAMPLE[option] if options.get(option) == args.REQUIRED else None
                    self.assertEqual(getattr(request, field), expected, field)

    def test_optional_policy_of_snapshot_build(self):
        request = args.parse(["snapshot-build", "--snapshot", "kcs_202201_202412_v2"])
        self.assertEqual((request.snapshot_id, request.policy_version), ("kcs_202201_202412_v2", None))

    def test_required_options(self):
        for command, options in args.COMMAND_OPTIONS.items():
            for option, role in options.items():
                if role != args.REQUIRED:
                    continue
                argv = argv_for(command)
                index = argv.index(f"--{option}")
                del argv[index:index + 2]
                with self.subTest(command=command, missing=option):
                    code, err = parse_error(argv)
                    self.assertEqual(code, 2)
                    self.assertIn(f"--{option}", err)

    def test_unused_options_are_format_checked(self):
        bad = {"policy": ["policy_v1.json", "/srv/probe/policy_v1.json"], "mode": ["fast", "/srv/probe/mode"]}
        for command, options in args.COMMAND_OPTIONS.items():
            for option, role in options.items():
                if role != args.UNUSED:
                    continue
                for value in bad[option]:
                    with self.subTest(command=command, option=option, value=value):
                        code, err = parse_error(argv_for(command, **{option: value}))
                        self.assertEqual(code, 2)
                        self.assertIn(f"--{option}", err)
                        self.assertNotIn("/srv", err)

    def test_case_is_refused_outside_run_case(self):
        for command, options in args.COMMAND_OPTIONS.items():
            if "case" in options:
                continue
            with self.subTest(command=command):
                code, err = parse_error(argv_for(command) + ["--case", SAMPLE["case"]])
                self.assertEqual(code, 2)
                self.assertIn("unrecognized arguments: --case", err)

    def test_help_shows_every_option_and_marks_unused_ones(self):
        for command, options in args.COMMAND_OPTIONS.items():
            with self.subTest(command=command):
                for option, role in options.items():
                    self.assertEqual(args.option_help(command, option).endswith(args.UNUSED_NOTE), role == args.UNUSED)
                out = io.StringIO()
                with mock.patch.dict(os.environ, {"COLUMNS": "1000"}), contextlib.redirect_stdout(out), \
                        self.assertRaises(SystemExit) as caught:  # 넓은 폭: 도움말 줄바꿈이 문장을 자르지 않게
                    args.parse([command, "--help"])
                self.assertEqual(caught.exception.code, 0)
                for option in args.OPTIONS:
                    if option in options:
                        self.assertIn(f"--{option}", out.getvalue())
                    else:
                        self.assertNotIn(f"--{option}", out.getvalue())
                unused = sum(role == args.UNUSED for role in options.values())
                self.assertEqual(out.getvalue().count(args.UNUSED_NOTE), unused)


class ValueFormatTest(unittest.TestCase):
    def check(self, option: str, good: list[str], bad: list[str]) -> None:
        command = "run-case"
        for value in good:
            with self.subTest(option=option, good=value):
                self.assertEqual(getattr(args.parse(argv_for(command, **{option: value})), FIELD[option]), value)
        for value in bad:
            with self.subTest(option=option, bad=value):
                code, err = parse_error(argv_for(command, **{option: value}))
                self.assertEqual(code, 2)
                self.assertIn(f"--{option}", err)

    def test_snapshot_id(self):
        self.check("snapshot",
                   ["kcs_202201_202412_v2", "kcs_202201_202412_v1", "controlled_fixture_v0", "probe_20260923_205425",
                    "a", LONG],
                   ["", "Kcs_v2", "1kcs", "_kcs", "kcs-v2", "kcs.v2", "kcs v2", " kcs", "kcs\n", "kcs\x00",
                    "ｋcs", "kcsé", "kcs:v2", LONG + "a",
                    "data/snapshots/kcs_202201_202412_v2", "../kcs", "..", "/srv/probe/kcs", "C:\\probe\\kcs",
                    "~probe"])

    def test_policy_version(self):
        self.check("policy",
                   ["policy_v1", "dev-0.1", "dev-0.1.2", "v1.2", "dev_0.1", "dev-0.1-rc1", "a-b-c", LONG],
                   ["", "Policy_v1", "1policy", "-dev", "dev-", "dev--0.1", "dev-.1", "dev-0.", "dev-0..1", "dev.1",
                    "policy.v1", "policy_v1.json", "policy_v1.yaml", "dev 0.1", "dev-0.1\n", "dev-٠.١", "dev–0.1",
                    LONG + "a", "configs/policy_v1.json", "configs\\policy_v1.json", "../policy_v1", "..",
                    "/srv/probe/policy_v1.json", "~probe"])

    def test_case(self):
        self.check("case",
                   ["A-composition", "B-residual", "C-missing", "850450-CN-202403", "a", "x_1", "A" * 64],
                   ["", "-A", "A-", "_A", "A_", "A.B", "A..B", "..", "A/B", "A\\B", "/srv/probe/case", "~probe",
                    "A B", "A\n", "사례", "@case", "A:B", "A" * 65])

    def test_mode_accepts_only_four_values(self):
        for mode in args.MODES:
            with self.subTest(mode=mode):
                self.assertEqual(args.parse(argv_for("run-case", mode=mode)).mode, mode)
        for value in ["", "fast", "FULL", "full ", "full\n"]:
            with self.subTest(bad=value):
                code, err = parse_error(argv_for("run-case", mode=value))
                self.assertEqual(code, 2)
                self.assertIn("--mode", err)


class RepeatAndAbbreviationTest(unittest.TestCase):
    def test_same_option_twice_is_refused(self):
        cases = {
            "같은 값": ["--case", "A-composition"],
            "다른 값": ["--case", "B-residual"],
            "=꼴": ["--case=A-composition"],
        }
        for name, extra in cases.items():
            with self.subTest(name):
                code, err = parse_error(argv_for("run-case") + extra)
                self.assertEqual(code, 2)
                self.assertIn("--case 옵션을 두 번 적었다", err)
        for option in ("snapshot", "policy", "mode"):
            with self.subTest(option=option):
                code, err = parse_error(argv_for("run-case") + [f"--{option}={SAMPLE[option]}"])
                self.assertEqual(code, 2)
                self.assertIn(f"--{option} 옵션을 두 번 적었다", err)
        code, err = parse_error(["snapshot-verify", "--snapshot=kcs_202201_202412_v2", "--snapshot", "kcs_x"])
        self.assertEqual(code, 2)
        self.assertIn("--snapshot 옵션을 두 번 적었다", err)

    def test_abbreviated_options_are_refused(self):
        for abbreviation in ("--snap", "--pol", "--mo", "--ca"):
            with self.subTest(abbreviation=abbreviation):
                code, err = parse_error(argv_for("run-case") + [abbreviation, "x"])
                self.assertEqual(code, 2)
                self.assertIn(f"unrecognized arguments: {abbreviation} x", err)

    def test_file_arguments_are_not_expanded(self):
        self.assertIsNone(args.build_parser().fromfile_prefix_chars)
        code, _ = parse_error(["@probe"])
        self.assertEqual(code, 2)

    def test_command_is_required_and_known(self):
        self.assertEqual(parse_error([])[0], 2)
        self.assertEqual(parse_error(["collect"])[0], 2)
        self.assertEqual(parse_error(["--snapshot", "kcs", "detect"])[0], 2)  # 옵션은 명령 뒤에만 온다


class ErrorMessageTest(unittest.TestCase):
    PROBE = "/srv/probe/policy_v1.json"

    def test_rejected_values_are_not_repeated(self):
        for argv in (argv_for("run-case", policy=self.PROBE), argv_for("run-case", snapshot=self.PROBE),
                     argv_for("run-case", case=self.PROBE), argv_for("run-case", mode=self.PROBE),
                     argv_for("detect") + [self.PROBE], [self.PROBE]):
            with self.subTest(argv=argv):
                code, err = parse_error(argv)
                self.assertEqual(code, 2)
                self.assertNotIn("/srv", err)
                self.assertNotIn("probe", err)

    def test_path_values_get_the_path_message(self):
        for value in ("configs/policy_v1.json", "..", "~probe"):
            with self.subTest(value=value):
                _, err = parse_error(argv_for("run-case", policy=value))
                self.assertIn("정책 버전 이름에는 경로를 쓰지 않는다", err)

    def test_redact(self):
        self.assertEqual(args.redact("unrecognized arguments: /srv/probe/x y"), "unrecognized arguments: <경로 생략> y")
        self.assertEqual(args.redact("invalid choice: 'a\\b' (choose from x)"), "invalid choice: '<경로 생략>' (choose from x)")
        self.assertEqual(args.redact("--case 옵션을 두 번 적었다"), "--case 옵션을 두 번 적었다")
        for rule in (args.SNAPSHOT_RULE, args.POLICY_RULE, args.CASE_RULE):
            self.assertEqual(args.redact(rule), rule)  # 규칙 문장 자체는 가려지지 않는다


class RunTest(unittest.TestCase):
    def test_run_returns_the_request_fields(self):
        detect = ["detect", "--snapshot", "controlled_fixture_v0", "--policy", "dev-0.1"]
        self.assertEqual(args.run(detect),
                         {"command": "detect", "snapshot_id": "controlled_fixture_v0", "policy_version": "dev-0.1",
                          "mode": None, "case": None})
        self.assertEqual(args.run(detect + ["--mode", "agent"])["mode"], "agent")  # 쓰지 않는 옵션도 받은 값 그대로

    def test_run_takes_only_a_list_of_strings(self):
        for bad in (None, "detect", ("detect",), ["detect", 1], {"argv": []}):
            with self.subTest(bad=bad), self.assertRaises(TypeError):
                args.run(bad)

    def test_request_is_frozen(self):
        request = args.parse(argv_for("run-case"))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            request.snapshot_id = "kcs_202201_202412_v2"


if __name__ == "__main__":
    unittest.main()
