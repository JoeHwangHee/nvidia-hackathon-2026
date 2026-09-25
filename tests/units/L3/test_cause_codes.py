"""단위 L3(runlog_cause_codes) 골든 쌍 밖 규칙 시험: 종류별 코드·실행 상태, 재실행 대상 판정, errors 항목 형식."""
import unittest

from tradesentry.runlog import cause_codes as cc

ATTEMPTS = {"tool_attempts": 3, "model_requests": 4, "tokens_in": 900, "tokens_out": 120, "wall_ms": 5000}


class CauseCodeRuleTest(unittest.TestCase):
    def test_each_failure_kind_maps_to_one_code_and_status(self):
        cases = [
            ({"kind": "http_status", "http_status": 500}, cc.PROVIDER_HTTP_5XX, "FAILED", True),
            ({"kind": "connection"}, cc.PROVIDER_CONNECTION, "FAILED", True),
            # HTTP 429는 코드 PROVIDER_HTTP_4XX 그대로 재실행 대상이다(사용자 결정 2026-09-25 15:52)
            ({"kind": "http_status", "http_status": 429}, cc.PROVIDER_HTTP_4XX, "FAILED", True),
            ({"kind": "http_status", "http_status": 400}, cc.PROVIDER_HTTP_4XX, "FAILED", False),
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

    def test_http_429_is_a_rerun_target_but_other_4xx_are_not(self):
        """사용자 결정 2026-09-25 15:52: 재전송 한도를 다 쓴 429(PROVIDER_HTTP_4XX, detail "HTTP 429…")는 재실행 대상이다."""
        entry = lambda code, detail: cc.error_entry(code, "basic", ATTEMPTS, [], detail)  # noqa: E731
        for detail in ("HTTP 429(재전송 3회 뒤)", "HTTP 429"):
            with self.subTest(detail=detail):
                self.assertTrue(cc.rate_limited_entry(entry(cc.PROVIDER_HTTP_4XX, detail)))
                self.assertTrue(cc.infra_rerun_eligible("FAILED", [entry(cc.PROVIDER_HTTP_4XX, detail)]))
        self.assertTrue(cc.infra_rerun_eligible("FAILED", [entry(cc.PROVIDER_HTTP_4XX, "HTTP 429(재전송 3회 뒤)"),
                                                           entry(cc.PROVIDER_HTTP_5XX, "HTTP 503(재전송 3회 뒤)")]))
        for detail in ("HTTP 400", "HTTP 401", "HTTP 403", "HTTP 404", "HTTP 422", "HTTP 4290", "HTTP 42",
                       "x HTTP 429", "http 429", "", "policy_denied(l7) 403: 샌드박스 정책 프록시가 요청을 막았다"):
            with self.subTest(detail=detail):
                self.assertFalse(cc.infra_rerun_eligible("FAILED", [entry(cc.PROVIDER_HTTP_4XX, detail)]))
        for status in (400, 401, 403, 404, 422):
            with self.subTest(status=status):
                self.assertFalse(cc.run({"kind": "http_status", "http_status": status})["infra_rerun"])
        # 429 detail이어도 코드가 다르거나(정책 거부 CODE_ERROR 등) 실행 상태가 FAILED가 아니면 대상이 아니다
        self.assertFalse(cc.infra_rerun_eligible("FAILED", [entry(cc.CODE_ERROR, "HTTP 429")]))
        self.assertFalse(cc.infra_rerun_eligible("FAILED", [entry(cc.DEADLINE, "HTTP 429 재전송 대기가 deadline을 넘는다")]))
        self.assertFalse(cc.infra_rerun_eligible("BUDGET_EXCEEDED",
                                                 [entry(cc.BUDGET_MODEL_REQUESTS, "HTTP 429 재전송 전에 모델 요청 한도에 닿았다")]))
        self.assertFalse(cc.infra_rerun_eligible("FAILED", [entry(cc.PROVIDER_HTTP_4XX, "HTTP 429"),
                                                            entry(cc.CODE_ERROR, "harness:RuntimeError")]))
        self.assertFalse(cc.rate_limited_entry({"code": cc.PROVIDER_HTTP_4XX}))  # detail 없음
        # 5xx·연결 실패는 그대로 대상이다
        self.assertTrue(cc.infra_rerun_eligible("FAILED", [entry(cc.PROVIDER_HTTP_5XX, "HTTP 500(재전송 3회 뒤)")]))
        self.assertTrue(cc.infra_rerun_eligible("FAILED", [entry(cc.PROVIDER_CONNECTION, "연결 실패")]))

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
