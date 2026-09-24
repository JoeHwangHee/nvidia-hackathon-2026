"""단위 L3(runlog_cause_codes) 골든 쌍 밖 규칙 시험: 종류별 코드·실행 상태, 재실행 대상 판정, errors 항목 형식."""
import unittest

from tradesentry.runlog import cause_codes as cc

ATTEMPTS = {"tool_attempts": 3, "model_requests": 4, "tokens_in": 900, "tokens_out": 120, "wall_ms": 5000}


class CauseCodeRuleTest(unittest.TestCase):
    def test_each_failure_kind_maps_to_one_code_and_status(self):
        cases = [
            ({"kind": "http_status", "http_status": 500}, cc.PROVIDER_HTTP_5XX, "FAILED", True),
            ({"kind": "connection"}, cc.PROVIDER_CONNECTION, "FAILED", True),
            ({"kind": "http_status", "http_status": 429}, cc.PROVIDER_HTTP_4XX, "FAILED", False),
            ({"kind": "request_timeout"}, cc.PROVIDER_REQUEST_TIMEOUT, "FAILED", False),
            ({"kind": "bad_response"}, cc.PROVIDER_BAD_RESPONSE, "FAILED", False),
            ({"kind": "budget", "limit": "model_requests"}, cc.BUDGET_MODEL_REQUESTS, "BUDGET_EXCEEDED", False),
            ({"kind": "budget", "limit": "tokens"}, cc.BUDGET_TOKENS, "BUDGET_EXCEEDED", False),
            ({"kind": "deadline"}, cc.DEADLINE, "TIMEOUT", False),
            ({"kind": "schema"}, cc.SCHEMA_INVALID, "INVALID", False),
            ({"kind": "validator"}, cc.VALIDATOR_BLOCKED, "INVALID", False),
            ({"kind": "exception"}, cc.CODE_ERROR, "FAILED", False),
            # 샌드박스 정책 프록시 거부: 새 코드 없이 CODE_ERROR, 재실행 대상 아님(모델 제공자 쪽 오류가 아니다)
            ({"kind": "policy_denied"}, cc.CODE_ERROR, "FAILED", False),
        ]
        self.assertEqual({code for _, code, _, _ in cases}, set(cc.CODES))  # 코드 11개를 모두 지난다
        self.assertEqual(len(cc.CODES), 11)
        for inp, code, status, rerun in cases:
            with self.subTest(inp=inp):
                self.assertEqual(cc.run(inp), {"code": code, "execution_status": status, "infra_rerun": rerun})
        for bad in ({"kind": "budget", "limit": "tool_attempts"}, {"kind": "http_status"}, {"kind": "oops"}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                cc.run(bad)

    def test_rerun_only_when_failed_and_every_error_is_provider_infra(self):
        entry = lambda code: cc.error_entry(code, "basic", ATTEMPTS, [])  # noqa: E731
        self.assertTrue(cc.infra_rerun_eligible("FAILED", [entry(cc.PROVIDER_HTTP_5XX)]))
        self.assertTrue(cc.infra_rerun_eligible("FAILED", [entry(cc.PROVIDER_CONNECTION)]))
        self.assertFalse(cc.infra_rerun_eligible("FAILED", []))
        self.assertFalse(cc.infra_rerun_eligible("FAILED", [entry(cc.PROVIDER_HTTP_5XX), entry(cc.CODE_ERROR)]))
        self.assertFalse(cc.infra_rerun_eligible("BUDGET_EXCEEDED", [entry(cc.BUDGET_MODEL_REQUESTS)]))
        self.assertFalse(cc.infra_rerun_eligible("TIMEOUT", [entry(cc.DEADLINE)]))
        self.assertFalse(cc.infra_rerun_eligible("FAILED", [entry(cc.PROVIDER_REQUEST_TIMEOUT)]))
        denied = cc.error_entry(cc.classify("policy_denied"), "basic", ATTEMPTS, [], "policy_denied(connect) 403")
        self.assertFalse(cc.infra_rerun_eligible("FAILED", [denied]))

    def test_error_entry_keeps_attempts_and_last_good_evidence(self):
        entry = cc.error_entry(cc.DEADLINE, "revision", dict(ATTEMPTS, extra=1),
                               ["ev:controlled_fixture_v0:observation:12"], "x" * 500)
        self.assertEqual(tuple(entry), cc.ERROR_ENTRY_KEYS)
        self.assertEqual(entry["attempts"], ATTEMPTS)
        self.assertEqual(len(entry["detail"]), cc.DETAIL_MAX)
        with self.assertRaises(ValueError):
            cc.error_entry(cc.DEADLINE, "basic", {"tool_attempts": 1}, [])
        with self.assertRaises(ValueError):
            cc.error_entry("NOPE", "basic", ATTEMPTS, [])


if __name__ == "__main__":
    unittest.main()
