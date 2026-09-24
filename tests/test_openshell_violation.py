"""단위 F7(OpenShell 의도적 위반 시험) 시험. 네트워크·키·openshell 없이 돈다.

- scripts/openshell_violation_tests.py를 가짜 openshell(FakeOpenShell)로 돌려 시험표·라이브 정책·감사 로그 발췌 파일 이름,
  종료 코드(0 일치, 1 불일치, 2 인자 오류, 3 키 모양), MVP 체크리스트 4번 판정, 감사 로그 행 짝짓기와 경고 행 밀기,
  호스트 경로 치환을 본다. 가짜 응답의 로그 행 형식은 X1 실측(artifacts/openshell/violation_tests.md §3)을 따른다.
- 샌드박스 안 탐침(scripts/openshell_probes/)은 네트워크 없이 도는 부분(인자 오류, 쓰기 탐침, 부재 훑기, 키 조회가 값을
  내지 않는지)만 본다.
- 키 모양 문자열과 호스트 로컬 경로 모양은 비밀값·로컬 경로 검사에 이 파일이 걸리지 않게 조각을 이어 만든다.
"""
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import openshell_common as oc
from scripts import openshell_violation_tests as ovt
from scripts.openshell_probes import fs_probe, key_check, net_probe
from tradesentry.cli import dispatch

ROOT = Path(__file__).resolve().parents[1]
X1_LOGS = ROOT / "artifacts" / "openshell" / "logs"
FAKE_KEY = "nv" + "api" + "-" + "Z" * 40
SCORED, DEMO = "ts-scored", "ts-demo"
PY_IMAGE = ovt.IMAGE_PY


def x1_demo_v4() -> str:
    text = (X1_LOGS / "20260924-x1-demo-policy.txt").read_text(encoding="utf-8")
    chunk = text.split("## openshell policy get x1-demo --full (v4 dialback removed", 1)[1].split("## 8.", 1)[0]
    return "\n".join(line for line in chunk.split("\n", 1)[1].split("\n") if not line.startswith("exit="))


def policy_output(body: str, version: int = 1) -> str:
    return (f"Version:      {version}\nHash:         {'a' * 64}\nStatus:       Effective\nSource:       sandbox\n"
            f"---\n{body}")


def denied_l4(exe: str, host: str, reason: str) -> str:
    return f"NET:OPEN [MED] DENIED {exe}(7) -> {host}:443 [policy:- engine:opa] [reason:{reason}]"


class FakeOpenShell(ovt.Runner):
    """openshell 대역. 시계는 명령마다 1초씩 간다. 샌드박스 명령에는 X1 형식의 감사 로그 행을 남긴다."""

    def __init__(self, *, overrides=None, log_warning=False, inference_provider=False, extra_text=""):
        self.program = "openshell"
        self.env = {}
        self.t = 1_790_300_000.0
        self.logs: dict[str, list[str]] = {SCORED: [], DEMO: []}
        self.calls: list[list[str]] = []
        self.overrides = overrides or {}
        self.log_warning = log_warning
        self.inference_provider = inference_provider
        self.extra_text = extra_text
        demo_body = x1_demo_v4().split("---\n", 1)[1]
        self.bodies = {SCORED: (ROOT / ovt.SCORED_POLICY).read_text(encoding="utf-8"), DEMO: demo_body}

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.t += seconds

    def log(self, sandbox: str, text: str) -> None:
        self.logs[sandbox].append(f"[{self.t + 0.2:.3f}] [sandbox] [OCSF ] [ocsf] {text}")

    def run(self, args, timeout):
        self.calls.append(list(args))
        t0 = self.t
        rc, out, err = self.respond(list(args))
        self.t += 1.0
        return ovt.Result(rc, out, err, t0, self.t)

    def respond(self, args):
        if args == ["--version"]:
            return 0, "openshell 0.0.116\n", ""
        if args == ["inference", "get"]:
            provider = "  Provider: some-route\n" if self.inference_provider else ""
            return 0, (f"\x1b[1mInference:\x1b[0m\n\n  Workspace: default\n{provider}\nSystem inference:\n\n"
                       f"  Not configured\n{self.extra_text}"), ""
        if args[:2] == ["policy", "get"]:
            return 0, policy_output(self.bodies[args[2]]), ""
        if args[:3] == ["sandbox", "provider", "list"]:
            name = "tradesentry-nvidia" if args[3] == SCORED else "nvidia-prod"
            return 0, f"NAME  TYPE  CREDENTIAL_KEYS  CONFIG_KEYS\n{name}  x  1  0\n", ""
        if args[:2] == ["sandbox", "upload"]:
            return 0, "", ""
        if args[0] == "logs":
            lines = self.logs[args[1]]
            head = ["Warning: log buffer contains only the last 500 lines; --since results may be incomplete."]
            return 0, "\n".join((head if self.log_warning else []) + lines) + "\n", ""
        if args[:2] == ["sandbox", "exec"]:
            sandbox, command = args[3], args[args.index("--") + 1:]
            return self.exec(sandbox, command)
        raise AssertionError(f"모르는 명령 {args}")

    def exec(self, sandbox, command):
        joined = " ".join(command)
        for key, value in self.overrides.items():
            if key in joined:
                return value
        if command[:2] == ["mkdir", "-p"]:
            return 0, "", ""
        if command[0] == "cat":
            return 1, "", f"cat: {command[1]}: Permission denied\n"
        if "verify_snapshot" in joined:
            return 0, json.dumps({"snapshot_id": command[-1], "ok": True, "normalized_sha256": "c" * 64,
                                  "recorded": "c" * 64, "failed": []}) + "\n", ""
        if "key_check.py" in joined:
            return 0, json.dumps({"checker": "tradesentry_key_check", "verdict": "NO_REAL_KEY",
                                  "env_NVIDIA_API_KEY": "placeholder", "proc_environ_readable": 3,
                                  "proc_environ_unreadable": 0}) + "\n", ""
        if "fs_probe.py absent" in joined:
            return 0, json.dumps({"mode": "absent", "hit_count": 0, "hits": [], "entries_seen": 40,
                                  "unreadable_dirs": 0}) + "\n", ""
        if "fs_probe.py write" in joined:
            if ovt.RO_CHILD_DIR in joined:
                return 0, json.dumps({"mode": "write", "written": True}) + "\n", ""
            return 1, json.dumps({"mode": "write", "written": False, "errno": "EACCES"}) + "\n", ""
        if "fs_probe.py sha256" in joined:
            return 0, json.dumps({"mode": "sha256", "sha256": "b" * 64}) + "\n", ""
        if ovt.GITHUB_URL in joined:
            exe = ovt.CURL if ovt.CURL in joined else PY_IMAGE
            self.log(sandbox, denied_l4(exe, "api.github.com", "endpoint api.github.com:443 is not allowed by any policy"))
            if exe == ovt.CURL:
                return 56, "000", "curl: (56) CONNECT tunnel failed, response 403\n"
            return 4, json.dumps({"http_status": None, "error": "URLError: Tunnel connection failed: 403 Forbidden"}), ""
        if ovt.MODELS_URL in joined:
            self.log(sandbox, f"HTTP:GET [MED] DENIED GET http://{oc.NVIDIA_INFERENCE_HOST}:443/v1/models "
                              "[policy:x engine:l7] [reason:L7_REQUEST deny GET]")
            if ovt.CURL in joined:
                return 22, "403", "curl: (22) The requested URL returned error: 403\n"
            return 3, json.dumps({"http_status": 403, "body_head": "policy_denied"}), ""
        if ovt.INFERENCE_LOCAL_URL in joined:
            return 3, json.dumps({"http_status": 503}), ""
        if " NIM " in f" {joined} ":
            self.log(sandbox, f"NET:OPEN [INFO] ALLOWED {PY_IMAGE}(9) -> {oc.NVIDIA_INFERENCE_HOST}:443 [policy:x]")
            self.log(sandbox, f"HTTP:POST [INFO] ALLOWED POST http://{oc.NVIDIA_INFERENCE_HOST}:443{oc.CHAT_PATH}")
            return 0, json.dumps({"http_status": 200, "exit_code": 0}), ""
        if ovt.NIM_URL in joined:  # 비허용 바이너리(curl, 시스템 파이썬)
            exe = ovt.CURL if command[0] == ovt.CURL or ovt.CURL in command else "/usr/bin/python3.12"
            self.log(sandbox, denied_l4(exe, oc.NVIDIA_INFERENCE_HOST, f"binary '{exe}' not allowed in policy 'x'"))
            if exe == ovt.CURL:
                return 56, "000", "curl: (56) CONNECT tunnel failed, response 403\n"
            return 4, json.dumps({"http_status": None, "error": "URLError: Tunnel connection failed: 403 Forbidden"}), ""
        raise AssertionError(f"모르는 샌드박스 명령 {command}")


class RunHarness(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.outputs = Path(self.tmp.name) / "outputs"
        for patcher in (mock.patch.object(dispatch, "OUTPUT_PARENT", self.outputs),
                        mock.patch.object(ovt, "_at_repo_root", return_value=True)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_tool(self, runner, *extra, scored=SCORED, demo=DEMO):
        argv = ["run", "--row-gap", "0"]
        if scored:
            argv += ["--scored", scored]
        if demo:
            argv += ["--demo", demo]
        argv += list(extra)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = ovt.main(argv, runner)
        return code, out.getvalue(), err.getvalue()

    def run_dir(self) -> Path:
        dirs = sorted(self.outputs.iterdir())
        self.assertEqual(len(dirs), 1)
        self.assertRegex(dirs[0].name, r"^openshell_violation_tests-\d{12}$")
        return dirs[0]


class RunTest(RunHarness):
    def test_all_rows_match_and_files_are_fixed_names(self):
        code, out, _ = self.run_tool(FakeOpenShell())
        self.assertEqual(code, 0, out)
        run_dir = self.run_dir()
        stamp = run_dir.name.split("-", 1)[1]
        table = run_dir / f"openshell_violation_tests-{stamp}.md"
        n7 = run_dir / f"openshell_violation_tests-{stamp}"
        self.assertEqual(sorted(p.name for p in run_dir.iterdir()), sorted([table.name, n7.name]))
        self.assertEqual(sorted(p.name for p in n7.iterdir()), sorted([
            f"live_policy-{SCORED}.yaml", f"live_policy-{DEMO}.yaml", f"audit_log-{SCORED}.txt", f"audit_log-{DEMO}.txt"]))
        text = table.read_text(encoding="utf-8")
        self.assertIn("MVP 체크리스트 4번", text)
        self.assertIn("충족", text.split("MVP 체크리스트 4번", 1)[1].splitlines()[0])
        self.assertIn("불일치 행: 없음", text)
        self.assertIn("mvp4=충족 mismatch=0", out)
        # 시험표의 본문 sha256은 커밋 사본 .yaml 파일 바이트의 sha256이다
        body = (n7 / f"live_policy-{SCORED}.yaml").read_text(encoding="utf-8")
        self.assertIn(oc.sha256_text(body), text)
        self.assertEqual(oc.parse_yaml(body), oc.parse_yaml((ROOT / ovt.SCORED_POLICY).read_text(encoding="utf-8")))
        # 행마다 샌드박스 이름과 종류가 적힌다
        for rid in ("P1", "A1", "B1", "B2", "B4", "C1", "N1", "DB1", "DB3", "DB4", "DC1", "DN1"):
            self.assertRegex(text, rf"\n\| {rid} \| `ts-(scored|demo)` \|")
        self.assertIn(ovt.KIND_SCORED, text)
        self.assertIn(ovt.KIND_DEMO, text)

    def test_log_refs_point_to_denied_rows_in_excerpt(self):
        for warning in (False, True):
            with self.subTest(warning=warning), mock.patch.object(
                    dispatch, "OUTPUT_PARENT", Path(self.tmp.name) / f"outputs-{warning}"):
                self.outputs = dispatch.OUTPUT_PARENT
                code, _, _ = self.run_tool(FakeOpenShell(log_warning=warning), demo=None)
                self.assertEqual(code, 0)
                run_dir = self.run_dir()
                stamp = run_dir.name.split("-", 1)[1]
                table = (run_dir / f"openshell_violation_tests-{stamp}.md").read_text(encoding="utf-8")
                excerpt = (run_dir / f"openshell_violation_tests-{stamp}" / f"audit_log-{SCORED}.txt").read_text(
                    encoding="utf-8").splitlines()
                if warning:
                    self.assertTrue(excerpt[0].startswith("Warning"))
                for rid, needle in (("B1", "api.github.com:443"), ("B4", "HTTP:GET"), ("B2", "binary '/usr/bin/curl'"),
                            ("B3", "binary '/usr/bin/python3")):
                    row = next(line for line in table.splitlines() if line.startswith(f"| {rid} |"))
                    refs = row.split(f"audit_log-{SCORED}.txt` ", 1)[1].split("행", 1)[0].split(", ")
                    self.assertEqual(len(refs), 1, row)
                    self.assertIn(needle, excerpt[int(refs[0]) - 1])
                    self.assertIn("DENIED", excerpt[int(refs[0]) - 1])

    def test_mismatch_exits_one(self):
        allowed = (0, json.dumps({"http_status": 200}), "")
        code, out, _ = self.run_tool(FakeOpenShell(overrides={ovt.GITHUB_URL: allowed}), demo=None)
        self.assertEqual(code, 1)
        self.assertIn("mvp4=미충족", out)
        text = next(self.run_dir().glob("*.md")).read_text(encoding="utf-8")
        self.assertIn(f"{SCORED}:B1", text)

    def test_inference_route_is_a_mismatch(self):
        code, _, _ = self.run_tool(FakeOpenShell(inference_provider=True), demo=None)
        self.assertEqual(code, 1)

    def test_fs_denial_without_permission_text_is_not_a_match(self):
        missing = (1, "", "cat: /srv/x: No such file or directory\n")
        code, _, _ = self.run_tool(FakeOpenShell(overrides={"cat ": missing}), demo=None)
        self.assertEqual(code, 1)
        text = next(self.run_dir().glob("*.md")).read_text(encoding="utf-8")
        self.assertIn("ENOENT", text)

    def test_key_shape_writes_nothing(self):
        leak = (0, json.dumps({"verdict": "NO_REAL_KEY", "note": FAKE_KEY}), "")
        code, _, err = self.run_tool(FakeOpenShell(overrides={"key_check.py": leak}))
        self.assertEqual(code, 3)
        self.assertNotIn(FAKE_KEY, err)
        self.assertEqual(list(self.run_dir().iterdir()), [])

    def test_host_paths_are_substituted(self):
        local = "/" + "Users" + "/someone/elsewhere/file.txt"
        code, _, _ = self.run_tool(FakeOpenShell(extra_text=f"  note {ROOT}/configs and {local}\n"), demo=None)
        self.assertEqual(code, 0)
        text = next(self.run_dir().glob("*.md")).read_text(encoding="utf-8")
        self.assertNotIn(str(ROOT), text)
        self.assertNotIn(local, text)
        self.assertIn(oc.LOCAL_PATH_MASK, text)
        self.assertIn("configs", text)

    def test_image_manifest_sha256_is_compared_when_given(self):
        code, _, _ = self.run_tool(FakeOpenShell(), "--image-manifest-sha256", "b" * 64, demo=None)
        self.assertEqual(code, 0)
        code, _, _ = self.run_tool(FakeOpenShell(), "--image-manifest-sha256", "c" * 64, demo=None)
        self.assertEqual(code, 1)

    def test_official_kind_runs_minimum_rows_only(self):
        runner = FakeOpenShell()
        code, _, _ = self.run_tool(runner, "--scored-kind", "official", demo=None)
        self.assertEqual(code, 0)
        text = next(self.run_dir().glob("*.md")).read_text(encoding="utf-8")
        table = text.split("## 2. 시험표", 1)[1].split("## 3.", 1)[0]
        rows = [line.split("|")[1].strip() for line in table.splitlines() if line.startswith("| ") and SCORED in line]
        self.assertEqual(rows, ["P1", "P2", "P3", "P4", "P5", "A2", "A3", "B1", "C1", "M1", "S1", "D1"])
        self.assertIn(ovt.KIND_OFFICIAL, text)
        self.assertIn("봉인 입력 쓰기 거부", text)
        executed = [" ".join(call) for call in runner.calls if call[:2] == ["sandbox", "exec"]]
        self.assertFalse(any(ovt.NIM_URL in call or ovt.MODELS_URL in call for call in executed))

    def test_policy_match_ignores_duplicate_fs_entries_and_names_differences(self):
        body = (ROOT / ovt.SCORED_POLICY).read_text(encoding="utf-8")
        runner = FakeOpenShell()
        runner.bodies[SCORED] = body.replace("  - /var/log\n", "  - /var/log\n  - /var/log\n", 1)
        code, _, _ = self.run_tool(runner, demo=None)
        self.assertEqual(code, 0)
        runner = FakeOpenShell()
        runner.bodies[SCORED] = body.replace("  - /var/log\n", "", 1)
        code, _, _ = self.run_tool(runner, demo=None)
        self.assertEqual(code, 1)
        text = sorted(self.outputs.iterdir())[-1]
        table = next(text.glob("*.md")).read_text(encoding="utf-8")
        self.assertIn("커밋에만 ['/var/log']", table)

    def test_snapshot_verify_rows(self):
        runner = FakeOpenShell(overrides={"verify_snapshot": (1, json.dumps({
            "ok": False, "normalized_sha256": "c" * 64, "recorded": "d" * 64, "failed": ["normalized_sha256"]}), "")})
        code, _, _ = self.run_tool(runner, "--verify-snapshot", "controlled_fixture_v0", "--verify-snapshot", "dev20",
                                   demo=None)
        self.assertEqual(code, 1)
        table = next(self.run_dir().glob("*.md")).read_text(encoding="utf-8")
        self.assertIn("| S2 |", table)
        self.assertIn("실패 검사: normalized_sha256", table)
        verify = [call for call in runner.calls if call[:2] == ["sandbox", "exec"] and "verify_snapshot" in " ".join(call)]
        self.assertEqual([call[-1] for call in verify], ["controlled_fixture_v0", "dev20"])

    def test_argument_errors(self):
        for argv in (["run"], ["run", "--scored", "Bad_Name"], ["run", "--scored", "../x"],
                     ["run", "--scored", "same", "--demo", "same"],
                     ["run", "--scored", "ok", "--image-manifest-sha256", "xyz"],
                     ["run", "--scored", "ok", "--verify-snapshot", "../x"]):
            with self.subTest(argv=argv):
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    self.assertEqual(ovt.main(argv, FakeOpenShell()), 2)
        self.assertFalse(self.outputs.exists() and any(self.outputs.iterdir()))

    def test_runner_drops_key_variables(self):
        with mock.patch.dict(os.environ, {"NVIDIA_API_KEY": "x", "DATA_GO_KR_SERVICE_KEY": "y", "PATH": "/bin"}):
            env = ovt.Runner().env
        self.assertNotIn("NVIDIA_API_KEY", env)
        self.assertNotIn("DATA_GO_KR_SERVICE_KEY", env)
        self.assertIn("PATH", env)


class HelperTest(unittest.TestCase):
    def test_log_matches_x1_lines(self):
        lines = (X1_LOGS / "20260924-x1-os-test-openshell-logs.txt").read_text(encoding="utf-8").splitlines()
        by_number = {number: line for number, line in enumerate(lines, start=1)}
        self.assertTrue(ovt.log_matches("host", "api.github.com", by_number[106]))
        self.assertTrue(ovt.log_matches("binary", oc.NVIDIA_INFERENCE_HOST, by_number[112]))
        self.assertTrue(ovt.log_matches("binary", oc.NVIDIA_INFERENCE_HOST, by_number[118]))
        self.assertFalse(ovt.log_matches("binary", oc.NVIDIA_INFERENCE_HOST, by_number[106]))
        self.assertTrue(ovt.log_matches("binary", oc.NVIDIA_INFERENCE_HOST, by_number[112], ovt.CURL))
        self.assertFalse(ovt.log_matches("binary", oc.NVIDIA_INFERENCE_HOST, by_number[112], ovt.SYSTEM_PY))
        self.assertTrue(ovt.log_matches("binary", oc.NVIDIA_INFERENCE_HOST, by_number[118], ovt.SYSTEM_PY))
        self.assertEqual(ovt.binary_of(ovt._node_child(ovt.CURL, "x")), ovt.CURL)
        self.assertTrue(ovt.log_matches("l7", oc.NVIDIA_INFERENCE_HOST, by_number[131]))
        self.assertTrue(ovt.log_matches("nim", oc.NVIDIA_INFERENCE_HOST, by_number[81]))
        self.assertFalse(ovt.log_matches("host", "api.github.com", by_number[81]))

    def test_classify(self):
        self.assertEqual(ovt.classify(None, ""), "incomplete")
        self.assertEqual(ovt.classify(1, "cat: x: Permission denied"), "access-denial")
        self.assertEqual(ovt.classify(22, "error: 403"), "access-denial")
        self.assertEqual(ovt.classify(0, "ok"), "completed")
        self.assertEqual(ovt.classify(2, "usage"), "command failed")

    def test_forbidden_entry_is_component_based(self):
        self.assertFalse(ovt.forbidden_entry("/run/nemoclaw/managed-startup-runtime.env"))
        for entry in ("/sandbox/outputs", "/opt/x/eval/scorer", "/data/.env", "/a/.env.local", "/a/oracle_ABC.json",
                      "/x/.tradesentry/sealed", "/work/artifacts/eval"):
            with self.subTest(entry=entry):
                self.assertTrue(ovt.forbidden_entry(entry))

    def test_x1_demo_live_policy_passes_allowlist_and_b(self):
        _, body = oc.split_policy_get(x1_demo_v4())
        policy = oc.parse_yaml(body)
        self.assertEqual([entry for _, entry in oc.allowlist_entries(policy) if ovt.forbidden_entry(entry)], [])
        self.assertTrue(oc.judge_requirement_b(policy)[0])

    def test_inference_parse(self):
        self.assertFalse(ovt._inference_configured("Inference:\n\n  Workspace: default\n\nSystem inference:\n"))
        self.assertTrue(ovt._inference_configured("Inference:\n  Provider: r\n  Model: m\nSystem inference:\n"))
        self.assertIsNone(ovt._inference_configured("nothing"))

    def test_harness_report_is_found_in_agent_output(self):
        report = {"checker": "tradesentry_key_check", "verdict": "NO_REAL_KEY",
                  "ancestry": ["/usr/bin/python3.13", "/usr/local/bin/node", "/usr/bin/bash"]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "agent.json"
            path.write_text(json.dumps({"result": {"text": "done: " + json.dumps(report)}}), encoding="utf-8")
            self.assertEqual(ovt._harness_report(path), report)
        row = ovt.Row("DC2", DEMO, ovt.KIND_DEMO, "(c)", "t", "p")
        ctx = ovt.Context(args=mock.Mock(), stamp="0", scored_committed={}, harness_report=report)
        self.assertTrue(ovt.check_harness_key(row, ctx)[0])
        ctx.harness_report = None
        self.assertIsNone(ovt.check_harness_key(row, ctx)[0])


class ComposeTest(unittest.TestCase):
    def test_compose_refuses_repo_and_writes_outside(self):
        runner = FakeOpenShell()
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(ovt.main(["compose-demo-policy", "--sandbox", DEMO, "--out",
                                       str(ROOT / "outputs" / "never-written.yaml")], runner), 2)
            self.assertEqual(ovt.main(["compose-demo-policy", "--sandbox", "Bad/Name", "--out", "x"], runner), 2)
        self.assertFalse((ROOT / "outputs" / "never-written.yaml").exists())
        default = (X1_LOGS / "20260924-x1-demo-policy.txt").read_text(encoding="utf-8")
        chunk = default.split("## openshell policy get x1-demo --full (onboarding default", 1)[1]
        chunk = chunk.split("\n", 1)[1].split("## 2.", 1)[0]
        live = "\n".join(line for line in chunk.split("\n") if not line.startswith("exit="))
        runner.bodies[DEMO] = live.split("---\n", 1)[1]
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "composed.yaml"
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(ovt.main(["compose-demo-policy", "--sandbox", DEMO, "--out", str(target)], runner), 0)
            self.assertIn("requirement_b=충족", out.getvalue())
            composed = oc.parse_yaml(target.read_text(encoding="utf-8"))
            self.assertEqual(sorted(oc.network_blocks(composed)), ["nvidia"])


class ProbeTest(unittest.TestCase):
    def quiet(self, func, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = func(*args)
        return code, out.getvalue()

    def test_fs_probe_write_and_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = self.quiet(fs_probe.main, ["write", os.path.join(tmp, "probe")])
            self.assertEqual(code, 0)
            self.assertTrue(json.loads(out)["written"])
            self.assertFalse(os.path.exists(os.path.join(tmp, "probe")))
            code, out = self.quiet(fs_probe.main, ["write", os.path.join(tmp, "missing", "probe")])
            self.assertEqual(code, 3)
            self.assertEqual(json.loads(out)["errno"], "ENOENT")
            os.makedirs(os.path.join(tmp, "app", "data"))
            Path(tmp, "app", "data", "snapshot_build.sqlite").write_bytes(b"")
            code, out = self.quiet(fs_probe.main, ["absent", tmp])
            self.assertEqual((code, json.loads(out)["hit_count"]), (0, 0))
            Path(tmp, "app", "oracle_ABC.json").write_text("{}", encoding="utf-8")
            Path(tmp, "app", "answers_dev20.json").write_text("{}", encoding="utf-8")
            code, out = self.quiet(fs_probe.main, ["absent", tmp, "--name", "answers_dev20.json"])
            self.assertEqual((code, json.loads(out)["hit_count"]), (1, 2))
            code, out = self.quiet(fs_probe.main, ["absent", tmp, "--skip", os.path.join(tmp, "app")])
            self.assertEqual(code, 0)
            self.assertEqual(self.quiet(fs_probe.main, ["bogus"])[0], 2)

    def test_key_check_never_prints_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, ".env").write_text(f"NVIDIA_API_KEY={FAKE_KEY}\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"NVIDIA_API_KEY": FAKE_KEY}):
                code, out = self.quiet(key_check.main, [tmp])
            self.assertEqual(code, 1)
            self.assertNotIn(FAKE_KEY, out)
            report = json.loads(out)
            self.assertEqual(report["verdict"], "REAL_KEY_FOUND")
            self.assertEqual(report["env_NVIDIA_API_KEY"], "REAL_KEY_FORMAT")
            os.remove(os.path.join(tmp, ".env"))
            with mock.patch.dict(os.environ, {"NVIDIA_API_KEY": oc.PLACEHOLDER_PREFIX + "NVIDIA_API_KEY"}):
                code, out = self.quiet(key_check.main, [tmp])
            self.assertEqual(json.loads(out)["env_NVIDIA_API_KEY"], "placeholder")
            self.assertEqual(json.loads(out)["checker"], "tradesentry_key_check")

    def test_net_probe_argument_and_missing_key(self):
        self.assertEqual(self.quiet(net_probe.main, ["GET"])[0], 2)
        self.assertEqual(self.quiet(net_probe.main, ["NIM", "https://example.invalid/x"])[0], 2)
        with mock.patch.dict(os.environ, {}, clear=True):
            code, out = self.quiet(net_probe.main, ["NIM", "https://example.invalid/x", "--key-env", "NVIDIA_API_KEY"])
        self.assertEqual(code, 5)
        self.assertEqual(json.loads(out)["error"], "key_env_missing_or_invalid")


if __name__ == "__main__":
    unittest.main()
