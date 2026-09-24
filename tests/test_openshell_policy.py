"""단위 F4(OpenShell 정책) 시험. 네트워크·키·openshell 없이 돈다.

- configs/openshell/policy.yaml(채점 대상 실행용)과 configs/openshell/policy_demo_network.yaml(시연 샌드박스의 네트워크
  부분)이 요건 (a)·(b)의 구조를 지키는지 본다(docs/plan/DEV_PLAN.md §4.1·§4.4·§4.8).
- 공용 도구 scripts/openshell_common.py의 좁은 YAML 파서, 라이브 정책 조회 본문 추출(해시 규칙), 경로 치환, 요건 (b) 판정을
  X1 실측 출력(artifacts/openshell/logs/의 조회 기록)으로 시험한다.
- 호스트 로컬 경로 모양은 비밀값·로컬 경로 검사에 이 파일이 걸리지 않게 조각을 이어 만든다.
"""
import unittest
from pathlib import Path

from scripts import openshell_common as oc

ROOT = Path(__file__).resolve().parents[1]
SCORED = ROOT / "configs" / "openshell" / "policy.yaml"
DEMO_NETWORK = ROOT / "configs" / "openshell" / "policy_demo_network.yaml"
X1_LOGS = ROOT / "artifacts" / "openshell" / "logs"
CHAT_RULES = [{"allow": {"method": "POST", "path": "/v1/chat/completions"}}]
# X1 os-test 4판 조회 출력에서 해시 규칙으로 꺼낸 본문의 sha256(규칙이 바뀌면 이 값도 바뀐다)
X1_OS_TEST_V4_BODY_SHA256 = "a0a6f2d6ecee6de4a00d734ea7d5cbd6a5f34d6947da62b48b75d8b43a3ea751"


def x1_section(file_name: str, start: str, end: str) -> str:
    """X1 조회 기록에서 한 조회의 출력만 꺼낸다(기록자가 덧붙인 `exit=` 줄은 뺀다)."""
    text = (X1_LOGS / file_name).read_text(encoding="utf-8")
    chunk = text.split(start, 1)[1].split(end, 1)[0].split("\n", 1)[1]
    return "\n".join(line for line in chunk.split("\n") if not line.startswith("exit="))


def x1_os_test_v4() -> str:
    return x1_section("20260924-x1-os-test-policy.txt", "## openshell policy get x1-os-test --full (4판",
                      "## openshell sandbox provider list")


def x1_demo(label: str, end: str) -> str:
    return x1_section("20260924-x1-demo-policy.txt", f"## openshell policy get x1-demo --full ({label}", end)


class RequirementBEndpointTest(unittest.TestCase):
    """요건 (b) 판정이 port·protocol·enforcement도 본다(MT5b NVIDIA 검토 1 권고 3)."""

    def policy(self, **endpoint_changes):
        endpoint = {"host": "integrate.api.nvidia.com", "port": 443, "protocol": "rest", "enforcement": "enforce",
                    "rules": CHAT_RULES}
        endpoint.update(endpoint_changes)
        for key in [k for k, v in endpoint.items() if v is None]:
            del endpoint[key]
        return {"network_policies": {"b": {"endpoints": [endpoint], "binaries": [{"path": "/x/python"}]}}}

    def test_fields(self):
        self.assertEqual(oc.judge_requirement_b(self.policy()), (True, []))
        for change, word in ((dict(enforcement="audit"), "enforcement"), (dict(protocol=None), "protocol"),
                             (dict(port=8443), "port")):
            with self.subTest(change=change):
                ok, reasons = oc.judge_requirement_b(self.policy(**change))
                self.assertFalse(ok)
                self.assertTrue(any(word in reason for reason in reasons), reasons)


class YamlSubsetTest(unittest.TestCase):
    def test_block_forms(self):
        text = ("# 주석\nversion: 1\nlist:\n- /usr  # 끝 주석\n- 'a # b'\nnested:\n  flag: true\n  items:\n"
                "  - path: /x/**\n    n: 3\n  - k: \"q\"\nempty: {}\nnone:\n")
        self.assertEqual(oc.parse_yaml(text), {
            "version": 1, "list": ["/usr", "a # b"],
            "nested": {"flag": True, "items": [{"path": "/x/**", "n": 3}, {"k": "q"}]},
            "empty": {}, "none": None})

    def test_unsupported_forms_stop(self):
        for text in ("a:\n\tb: 1\n", "a: {b: 1}\n", "a: [1, 2]\n", "a: &x 1\n", "a: *x\n", "a: 1\na: 2\n",
                     "---\na: 1\n", "a: |\n  b\n", "a:\n  b: 1\n   c: 2\n", "  a: 1\n", "just words\n"):
            with self.subTest(text=text), self.assertRaises(oc.YamlSubsetError):
                oc.parse_yaml(text)

    def test_x1_files_parse_like_live_output(self):
        """X1이 커밋한 정책 파일과 그 파일을 적용한 뒤의 라이브 조회 본문이 같은 구조로 읽힌다."""
        _, body = oc.split_policy_get(x1_os_test_v4())
        self.assertEqual(oc.parse_yaml(body),
                         oc.parse_yaml((ROOT / "spikes/x1/policy/x1-os-test.nim.policy.yaml").read_text("utf-8")))
        _, body = oc.split_policy_get(x1_demo("v4 dialback removed", "## 8."))
        self.assertEqual(oc.parse_yaml(body),
                         oc.parse_yaml((ROOT / "spikes/x1/policy/x1-demo-narrowed.policy.yaml").read_text("utf-8")))


class PolicyGetExtractionTest(unittest.TestCase):
    def test_header_and_body_hash(self):
        header, body = oc.split_policy_get(x1_os_test_v4())
        self.assertEqual(header["Version"], "4")
        self.assertEqual(header["Hash"], "3c8009005cf17ccd3e551590f59353f29b94fa72978d17808f50c41517d34eb2")
        self.assertEqual(header["Status"], "Effective")
        self.assertTrue(body.startswith("version: 1\n") and body.endswith("path: /opt/x1/python/**\n"))
        self.assertEqual(oc.sha256_text(body), X1_OS_TEST_V4_BODY_SHA256)

    def test_line_endings_ansi_and_trailing_space_do_not_change_hash(self):
        raw = x1_os_test_v4()
        noisy = "\x1b[1m" + raw.replace("\n", "  \r\n").replace("version: 1", "\x1b[36mversion: 1\x1b[0m") + "\r\n\r\n"
        self.assertEqual(oc.sha256_text(oc.split_policy_get(noisy)[1]), X1_OS_TEST_V4_BODY_SHA256)

    def test_missing_separator_or_empty_body(self):
        with self.assertRaises(oc.PolicyOutputError):
            oc.split_policy_get("Version: 1\nHash: x\n")
        with self.assertRaises(oc.PolicyOutputError):
            oc.split_policy_get("Version: 1\n---\n\n\n")


class HostPathSubstitutionTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.home = Path("/" + "Users" + "/someone")
        self.repo = self.home / "work" / "repo"
        self.sealed = self.home / ".tradesentry" / "sealed"
        self.tmp = Path("/" + "private" + "/var" + "/folders/xy/T")

    def test_ordered_tokens_and_mask(self):
        text = "\n".join([f"{self.sealed}/holdout40/input", f"{self.repo}/configs/x.yaml", str(self.repo),
                          f"{self.tmp}/a", f"{self.home}/.config/x", "/" + "Users" + "/other/y", "/sandbox/keep",
                          "/usr/local/bin/node"])
        out, masked = oc.substitute_host_paths(text, repo_root=self.repo, home=self.home, sealed_dir=self.sealed,
                                               tmp_dir=self.tmp)
        self.assertEqual(out.split("\n"), ["$TRADESENTRY_SEALED_DIR/holdout40/input", "configs/x.yaml", ".",
                                           "$TMPDIR/a", "$HOME/.config/x", oc.LOCAL_PATH_MASK, "/sandbox/keep",
                                           "/usr/local/bin/node"])
        self.assertEqual(masked, 1)

    def test_sandbox_paths_untouched(self):
        body = oc.split_policy_get(x1_demo("v4 dialback removed", "## 8."))[1]
        self.assertEqual(oc.substitute_host_paths(body, repo_root=self.repo, home=self.home), (body, 0))


class ScoredPolicyTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.text = SCORED.read_text(encoding="utf-8")
        self.policy = oc.parse_yaml(self.text)

    def test_static_layer(self):
        fs = self.policy["filesystem_policy"]
        self.assertEqual(self.policy["version"], 1)
        self.assertIs(fs["include_workdir"], True)
        self.assertEqual(fs["read_write"], ["/tmp", "/dev/null"])
        self.assertEqual(fs["read_only"], ["/usr", "/lib", "/proc", "/dev/urandom", "/etc", "/opt/tradesentry",
                                           "/sandbox/read_only_probe", "/var/log"])
        self.assertEqual(self.policy["landlock"], {"compatibility": "best_effort"})
        self.assertEqual(self.policy["process"], {"run_as_user": "sandbox", "run_as_group": "sandbox"})

    def test_requirement_a_decoy_and_answer_paths_not_allowed(self):
        for target in ("/srv/tradesentry_decoy/oracle_decoy.json", "/srv", "/opt/tradesentry_sealed", "/root/.env"):
            with self.subTest(target=target):
                self.assertEqual(oc.covering_entries(self.policy, target), [])
        for kind, entry in oc.allowlist_entries(self.policy):
            with self.subTest(entry=entry):
                self.assertNotIn(entry.rstrip("/"), ("", "/opt", "/srv", "/sandbox", "/opt/tradesentry/eval"))
                for word in ("outputs", "artifacts", "sealed", "scorer", "oracle", ".env"):
                    self.assertNotIn(word, entry)

    def test_requirement_b_one_destination_one_path_one_binary(self):
        blocks = oc.network_blocks(self.policy)
        self.assertEqual(list(blocks), ["tradesentry_nim_chat"])
        block = blocks["tradesentry_nim_chat"]
        self.assertEqual(block["endpoints"], [{"host": "integrate.api.nvidia.com", "port": 443, "protocol": "rest",
                                               "enforcement": "enforce", "rules": CHAT_RULES}])
        self.assertEqual(block["binaries"], [{"path": "/opt/tradesentry/python/**"}])
        self.assertEqual(oc.judge_requirement_b(self.policy), (True, []))
        self.assertNotIn("network_middlewares", self.policy)

    def test_no_key_or_local_path(self):
        self.assertFalse(oc.has_key_shape(self.text))
        self.assertEqual(oc.LOCAL_PATH_RE.findall(self.text), [])


class DemoNetworkPolicyTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.text = DEMO_NETWORK.read_text(encoding="utf-8")
        self.policy = oc.parse_yaml(self.text)

    def test_only_network_part(self):
        self.assertEqual(set(self.policy), {"version", "network_policies"})
        blocks = oc.network_blocks(self.policy)
        self.assertEqual(list(blocks), ["nvidia"])
        self.assertEqual(blocks["nvidia"]["endpoints"],
                         oc.network_blocks(oc.parse_yaml(SCORED.read_text("utf-8")))["tradesentry_nim_chat"]["endpoints"])
        self.assertEqual(blocks["nvidia"]["binaries"], [{"path": "/usr/local/bin/openclaw"},
                                                        {"path": "/usr/local/bin/node"}])
        self.assertEqual(oc.judge_requirement_b(self.policy), (True, []))
        self.assertFalse(oc.has_key_shape(self.text))
        self.assertEqual(oc.LOCAL_PATH_RE.findall(self.text), [])

    def test_compose_onto_x1_onboarding_policy(self):
        """NemoClaw 온보딩 직후 라이브 정책(요건 (b) 미충족)에 이 파일을 합치면 X1 최종 4판과 같은 구조가 되고 (b)를 채운다."""
        onboarding = oc.split_policy_get(x1_demo("onboarding default", "## 2."))[1]
        ok, reasons = oc.judge_requirement_b(oc.parse_yaml(onboarding))
        self.assertFalse(ok)
        self.assertTrue(any("clawhub" in reason for reason in reasons))
        composed = oc.compose_network(onboarding, self.text)
        final_v4 = oc.parse_yaml(oc.split_policy_get(x1_demo("v4 dialback removed", "## 8."))[1])
        self.assertEqual(oc.parse_yaml(composed), final_v4)
        self.assertEqual(oc.judge_requirement_b(oc.parse_yaml(composed)), (True, []))

    def test_compose_refuses_static_sections_in_network_file(self):
        onboarding = oc.split_policy_get(x1_demo("onboarding default", "## 2."))[1]
        with self.assertRaises(oc.YamlSubsetError):
            oc.compose_network(onboarding, self.text + "process:\n  run_as_user: root\n")


if __name__ == "__main__":
    unittest.main()
