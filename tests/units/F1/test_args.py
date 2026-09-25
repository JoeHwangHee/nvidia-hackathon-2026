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
            "evaluate": {"snapshot": R, "policy": R, "mode": O},  # 사용자 결정 12(가): 모드를 주지 않으면 정해진 모드 전부
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
                self.assertIn(f"unrecognized arguments: {abbreviation} <값 생략>", err)  # 값은 되풀이하지 않는다

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
        omitted, hidden = args.VALUE_OMITTED, args.PATH_OMITTED
        cases = {
            "unrecognized arguments: /srv/probe/x y": f"unrecognized arguments: {omitted} {omitted}",
            "unrecognized arguments: --snap=v --weird-option x":
                f"unrecognized arguments: --snap={omitted} --weird-option {omitted}",
            "unrecognized arguments: --" + "a" * 31 + " --Snap --snap\nx":
                f"unrecognized arguments: {omitted} {omitted} {omitted}",  # 32자 넘는 이름, 대문자, 줄바꿈 붙은 이름
            "invalid choice: 'a\\b' (choose from x)": f"invalid choice: {omitted} (choose from x)",
            "invalid choice: \"it's\" (choose from x)": f"invalid choice: {omitted} (choose from x)",
            "invalid choice: 'S unrecognized arguments: x' (choose from x)": f"invalid choice: {omitted} (choose from x)",
            "unrecognized arguments: invalid choice: 'x'":  # 모르는 인자가 문구를 흉내 내도 조각마다 생략된다
                "unrecognized arguments: " + " ".join([omitted] * 4),
            "argument -h/--help: ignored explicit argument 'x'":
                f"argument -h/--help: ignored explicit argument {omitted}",  # 옵션 별칭은 경로로 보지 않는다
            "argument --mode: expected one argument /srv/probe/x": f"argument --mode: expected one argument {hidden}",
            "a\x1bb\u202ec\nd\u2028e": "a\\x1bb\\u202ec\\x0ad\\u2028e",
            "--case 옵션을 두 번 적었다": "--case 옵션을 두 번 적었다",
        }
        for message, expected in cases.items():
            with self.subTest(message=message):
                self.assertEqual(args.redact(message), expected)
        for rule in (args.SNAPSHOT_RULE, args.POLICY_RULE, args.CASE_RULE):
            self.assertEqual(args.redact(rule), rule)  # 규칙 문장 자체는 가려지지 않는다

    def test_values_are_never_repeated(self):
        fake = "FAKE_SECRET_TOKEN_123"  # 경로가 아닌 가짜 값
        calls = {
            "모르는 인자": argv_for("detect") + [fake],
            "모르는 옵션의 값": argv_for("detect") + [f"--snap={fake}"],
            "선택지 밖 모드": argv_for("run-case", mode=fake),
            "모르는 명령": [fake],
            "받지 않는 명시 값": argv_for("detect") + [f"--help={fake}"],
            "공백 든 경로": argv_for("detect") + ["/srv/probe dir/secret name.txt"],
            "구분자 없는 홈 모양": argv_for("detect") + ["~probe_user"],
            # 값 안의 문구가 모르는 인자 문장인 척해도 값이 새지 않는다(문장 앞에서만 판정하고 따옴표 값을 먼저 지운다)
            "모드 값 안의 문구": argv_for("run-case", mode=f"{fake} unrecognized arguments: x"),
            "명령 이름 안의 문구": [f"{fake} unrecognized arguments: x"],
            "명시 값 안의 문구": argv_for("detect") + [f"--help={fake} unrecognized arguments: x"],
        }
        for name, argv in calls.items():
            with self.subTest(name):
                code, err = parse_error(argv)
                self.assertEqual(code, 2)
                for leak in (fake, "srv", "probe", "secret", "name.txt"):
                    self.assertNotIn(leak, err)
                self.assertIn(args.VALUE_OMITTED, err)

    def test_control_characters_cannot_forge_lines(self):
        for value in ("x\nFAKE_LOG_LINE exit=0", "\x1b[31mRED", "\u202eRLO", "a\rb", "a\u2028b"):
            for argv in (argv_for("detect") + [value], argv_for("run-case", mode=value)):
                with self.subTest(value=value, argv=argv[0]):
                    code, err = parse_error(argv)
                    self.assertEqual(code, 2)
                    self.assertNotIn("FAKE_LOG_LINE", err)
                    for control in ("\x1b", "\u202e", "\r", "\u2028"):
                        self.assertNotIn(control, err)
                    self.assertTrue(err.splitlines()[-1].startswith("tradesentry"))  # 마지막 줄은 오류 문장이다


class OutputEncodingTest(unittest.TestCase):
    """표준 출력·오류가 한국어를 못 쓰는 인코딩이어도 호출 경로 기록 없이 argparse 방식으로 끝난다."""

    def ascii_stream(self) -> io.TextIOWrapper:
        return io.TextIOWrapper(io.BytesIO(), encoding="ascii")

    def test_argument_error_on_an_ascii_stream(self):
        stream = self.ascii_stream()
        with contextlib.redirect_stderr(stream), self.assertRaises(SystemExit) as caught:
            args.parse(argv_for("detect", snapshot="Bad"))
        self.assertEqual(caught.exception.code, 2)
        stream.flush()
        text = stream.buffer.getvalue().decode("ascii")
        self.assertIn("argument --snapshot:", text)
        self.assertIn("\\u", text)  # 한국어는 역슬래시 표기로 남는다

    def test_help_on_an_ascii_stream(self):
        stream = self.ascii_stream()
        with contextlib.redirect_stdout(stream), self.assertRaises(SystemExit) as caught:
            args.parse(["run-case", "--help"])
        self.assertEqual(caught.exception.code, 0)
        stream.flush()
        self.assertIn("--case CASE", stream.buffer.getvalue().decode("ascii"))

    def test_write_text(self):
        stream = self.ascii_stream()
        args.write_text(stream, "가a\n")
        stream.flush()
        self.assertEqual(stream.buffer.getvalue(), b"\\uac00a\n")
        closed = self.ascii_stream()
        closed.close()
        args.write_text(closed, "가")  # 닫힌 흐름(ValueError)은 조용히 넘어간다
        args.write_text(None, "가")  # 흐름이 없으면(AttributeError) 조용히 넘어간다


class RunNameTest(unittest.TestCase):
    """--run-name(사용자 결정 10(나)): 다섯 명령의 선택 옵션. N5 형식, 실행 이름 = 그 명령의 실행 이름, 실제 날짜·시각."""

    def test_every_command_takes_its_own_run_name(self):
        for command in args.COMMANDS:
            name = f"{command.replace('-', '_')}-260925143015"
            with self.subTest(command=command):
                self.assertEqual(args.run_name_of(command), command.replace("-", "_"))
                self.assertEqual(args.parse(argv_for(command) + ["--run-name", name]).run_name, name)
                self.assertIsNone(args.parse(argv_for(command)).run_name)  # 옵션이 없으면 CLI가 확보한다

    def test_bad_run_names_are_refused_without_echo(self):
        bad = ["", "run_case", "run_case-2609251430", "run_case-2609251430151", "run-case-260925143015",
               "detect-260925143015", "Run_case-260925143015", "run_case-260925143015\n", "run_case-260925143015\\n",
               "run_case-261325143015", "run_case-260931143015", "run_case-260925246015", "run_case-26092514301５",
               "../run_case-260925143015", "outputs/run_case-260925143015", "/srv/probe/run_case-260925143015",
               "~run_case-260925143015", "run_case-260925143015 ", "_run_case-260925143015",
               "run_case_" + "a" * 43 + "-260925143015"]
        for value in bad:
            with self.subTest(value=value):
                code, err = parse_error(argv_for("run-case") + ["--run-name", value])
                self.assertEqual(code, 2)
                self.assertIn("--run-name", err)
                self.assertNotIn("srv", err)
                if value and value not in args.RUN_NAME_RULE:
                    self.assertNotIn(value, err)  # 받은 값을 되풀이하지 않는다

    def test_run_name_prefix_must_match_the_command(self):
        code, err = parse_error(argv_for("evaluate") + ["--run-name", "run_case-260925143015"])
        self.assertEqual(code, 2)
        self.assertIn("실행 이름이 이 명령의 실행 이름과 다르다", err)

    def test_run_name_twice_is_refused(self):
        code, err = parse_error(argv_for("detect") + ["--run-name", "detect-260925143015",
                                                      "--run-name=detect-260925143016"])
        self.assertEqual(code, 2)
        self.assertIn("--run-name 옵션을 두 번 적었다", err)

    def test_evaluate_mode_is_optional(self):
        request = args.parse(["evaluate", "--snapshot", "dev20", "--policy", "dev-0.1"])
        self.assertIsNone(request.mode)
        self.assertEqual(args.parse(["evaluate", "--snapshot", "dev20", "--policy", "dev-0.1", "--mode", "full"]).mode,
                         "full")


class RunTest(unittest.TestCase):
    def test_run_returns_the_request_fields(self):
        detect = ["detect", "--snapshot", "controlled_fixture_v0", "--policy", "dev-0.1"]
        self.assertEqual(args.run(detect),
                         {"command": "detect", "snapshot_id": "controlled_fixture_v0", "policy_version": "dev-0.1",
                          "mode": None, "case": None, "run_name": None, "conditions_extra": None})
        self.assertEqual(args.run(detect + ["--mode", "agent"])["mode"], "agent")  # 쓰지 않는 옵션도 받은 값 그대로


class ConditionsExtraTest(unittest.TestCase):
    """--conditions-extra(조립 AS3): evaluate만의 선택 옵션. 값은 공백·제어 문자 없는 상대 경로 한 조각이다."""

    def test_only_evaluate_takes_it_and_it_is_optional(self):
        argv = argv_for("evaluate") + ["--conditions-extra", "outputs/conditions/extra.json"]
        self.assertEqual(args.parse(argv).conditions_extra, "outputs/conditions/extra.json")
        self.assertIsNone(args.parse(argv_for("evaluate")).conditions_extra)
        for command in args.COMMANDS:
            if command == "evaluate":
                continue
            with self.subTest(command=command):
                code, err = parse_error(argv_for(command) + ["--conditions-extra", "extra.json"])
                self.assertEqual(code, 2)
                self.assertIn("unrecognized arguments: --conditions-extra <값 생략>", err)
        code, err = parse_error(argv + ["--conditions-extra", "extra.json"])
        self.assertEqual(code, 2)
        self.assertIn("--conditions-extra 옵션을 두 번 적었다", err)

    def test_absolute_home_and_whitespace_paths_are_refused_without_echo(self):
        bad = ["", "/srv/probe/extra.json", "\\\\srv\\extra.json", "~" + "/extra.json", "~extra.json", "C:\\extra.json",
               "c:/extra.json", "extra .json", "extra.json\n", "extra\u200b.json", " extra.json"]
        for value in bad:
            with self.subTest(value=value):
                code, err = parse_error(argv_for("evaluate") + ["--conditions-extra", value])
                self.assertEqual(code, 2)
                self.assertIn("--conditions-extra", err)
                self.assertIn("상대 경로", err)
                self.assertNotIn("srv", err)
                if value.strip():
                    self.assertNotIn(value, err)  # 받은 값을 되풀이하지 않는다
        for value in ("extra.json", "./extra.json", "../shared/extra.json", "outputs/x-1/extra.json"):
            with self.subTest(value=value):
                self.assertEqual(args.parse(argv_for("evaluate") + ["--conditions-extra", value]).conditions_extra, value)

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
