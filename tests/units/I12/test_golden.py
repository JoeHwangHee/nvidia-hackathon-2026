"""단위 I12(workflow_orchestrate) 골든 시험. 규칙은 tests/units/golden.py에 있다.

골든 입력은 사례 A(full)를 한 번 돈 trace다. 모델 응답과 도구 봉투는 기록 재생(단위 I8)으로 돌고, 다른 작업 단위(도구
예산 I6, 보고서 R1·R2, 검증기 R3·R4, 정책 P4·P5)는 아래 대역으로 바꾼다. 골든은 흐름 조정만 본다(대역의 입출력 모양은
그 단위들의 run 모양을 따르고, 흐름 조정의 unit_ports 배선을 거친다). 병합된 실제 단위와의 배선은
test_orchestrate.py의 MergedUnitsTest가 본다.
기록의 model_request에는 request_sha256이 있다. 그래서 보내는 요청 본문(프롬프트·근거 메시지 포함)이 바뀌면 재생이
ReplayMismatch로 실패한다. 재생이 끝났는데 기록이 남아도 실패한다. 프롬프트를 바꿨으면 해시를 다시 만들고 차이를 검토한다.
"""
import unittest
from unittest import mock

from ..golden import GoldenMixin


def _fill(inp):
    """단위 R1 대역: 요청의 metric_id로 검증된 지표를 찾아 typed claim을 만든다(R1의 출력 모양 {claims, rejected})."""
    case, by_id = inp["case"], {m["metric_id"]: m for m in inp.get("metrics", [])}
    claims = []
    for request in inp.get("requests", []):
        metric = by_id[request["metric_id"]]
        claims.append({"claim_id": request["claim_id"], "claim_type": "change", "hs6": case["hs6"],
                       "partner": case["partner"], "period": case["month"], "baseline_period": case["baseline_month"],
                       "metric": metric["inputs"]["metric"], "value": metric["value"], "unit": metric["unit"],
                       "direction": "DOWN", "evidence_ids": metric["evidence_ids"], "text": "단가가 전년 같은 달보다 낮다."})
    return {"claims": claims, "rejected": []}


def _render(inp):
    """단위 R2 대역: 출력 모양 {report, body_ko}."""
    evidence = sorted({e for c in inp["claims"] for e in c["evidence_ids"]})
    report = {"report_id": inp["report_id"], "run_id": inp["run_id"], "case_id": inp["case"]["case_id"],
              "mode": inp["mode"], "claims": inp["claims"], "narrative": inp["narrative"],
              "hypotheses": inp["hypotheses"], "review_status": inp["review_status"],
              "signal_status": inp["signal_status"], "unresolved_evidence": inp["unresolved_evidence"],
              "evidence_ids": evidence, "validator_findings": inp["validator_findings"], "report_hash": "0" * 64,
              "created_at": inp["created_at"], "policy_version": inp["policy_version"],
              "snapshot_id": inp["snapshot_id"], "grouping_version": inp["grouping_version"]}
    return {"report": report, "body_ko": "조사 전 경보 → 모니터링"}


STUBS = {
    "tradesentry.tools.budget.run": lambda inp: {"allowed": len(inp["attempts"]) < inp["limits"]["tool_attempts"],
                                                 "reason": "tool_attempts_limit"},
    "tradesentry.reports.claims.run": _fill,
    "tradesentry.reports.render_ko.run": _render,
    "tradesentry.validator.validate.run": lambda inp: {"findings": []},
    "tradesentry.validator.gate.run": lambda inp: {"blocked": False, "revise": False, "execution_status": None,
                                                   "schema_failed": False, "record_only": False,
                                                   "validator_findings": []},
    "tradesentry.policy.case_aggregate.run": lambda inp: {"review_status": "MONITOR", "unresolved_evidence": False},
    "tradesentry.policy.required_evidence.run": lambda inp: {"families": {"unit_value": {
        "claim_metrics": ["U", "r_U", "within_effect", "mix_effect", "residual"],
        "claim_metric_prefixes": ["U@", "r_U@", "w@"]}}},
}


class GoldenTest(GoldenMixin, unittest.TestCase):
    UNIT_ID = "I12"

    def setUp(self):
        super().setUp()
        for target, stub in STUBS.items():
            patcher = mock.patch(target, stub)
            patcher.start()
            self.addCleanup(patcher.stop)
