"""단위 F6(키 주입 provider 프로필) 시험. 네트워크·키·openshell 없이 돈다.

configs/openshell/provider_profile.yaml이 X1에서 채택한 헤더 자리표시 값 치환 방식의 모양을 지키고(결정 기록 1556),
목적지·rules·실행 파일이 채점 대상 실행 정책(configs/openshell/policy.yaml)의 블록과 같으며, 키 값을 담지 않는지 본다.
"""
import unittest
from pathlib import Path

from scripts import openshell_common as oc

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "configs" / "openshell" / "provider_profile.yaml"
SCORED = ROOT / "configs" / "openshell" / "policy.yaml"


class ProviderProfileTest(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.text = PROFILE.read_text(encoding="utf-8")
        self.profile = oc.parse_yaml(self.text)
        self.block = oc.network_blocks(oc.parse_yaml(SCORED.read_text(encoding="utf-8")))["tradesentry_nim_chat"]

    def test_identity(self):
        self.assertEqual(self.profile["id"], "tradesentry-nvidia-chat")
        self.assertEqual(self.profile["category"], "inference")
        self.assertIs(self.profile["inference_capable"], True)

    def test_credential_is_variable_name_only(self):
        self.assertEqual(self.profile["credentials"], [{
            "name": "api_key", "description": "NVIDIA API key", "env_vars": ["NVIDIA_API_KEY"], "required": True,
            "auth_style": "bearer", "header_name": "authorization"}])
        self.assertFalse(oc.has_key_shape(self.text))
        self.assertNotIn(oc.PLACEHOLDER_PREFIX, self.text)
        self.assertEqual(oc.LOCAL_PATH_RE.findall(self.text), [])

    def test_same_destination_rules_and_binary_as_policy(self):
        self.assertEqual(self.profile["endpoints"], self.block["endpoints"])
        self.assertEqual(self.profile["binaries"], [entry["path"] for entry in self.block["binaries"]])
        self.assertEqual(oc.judge_requirement_b({"network_policies": {"profile": {
            "endpoints": self.profile["endpoints"], "binaries": self.profile["binaries"]}}}), (True, []))


if __name__ == "__main__":
    unittest.main()
