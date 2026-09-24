"""단위 R4(validator_gate) 규칙 시험과 MVP 체크리스트 3번의 변조 시험(R3 → R4).

- 모드별 차단: 스키마 사유는 모든 모드에서 막고, 검증기 사유는 freeform에서 기록만 한다(자료 계약 §6.3, 룰북 B2).
- 막혔을 때: 수정이 남았으면 수정으로, 수정을 썼거나 checklist면 INVALID(결정 D1, 새 상태값 없음).
- MVP 3번: 숫자·단위·근거 ID·스냅샷 변조와 뒷받침 없는 산문 숫자·증감을 full·agent·checklist에서 막고,
  freeform에서는 막지 않고 validator_findings에 기록만 한다.
시험 값은 모두 합성이다(실제 통계가 아니다).
"""
import copy
import unittest
from decimal import Decimal

from tradesentry.validator import gate, validate
from units.R3.test_validate import EV, clean_input, index_of

SCHEMA = {"check": "schema", "code": "SCHEMA_CLAIM", "path": "claims[0].value", "claim_id": "c1", "detail": "d"}
CHECKED = {"check": "validator", "code": "NUMERIC_MISMATCH", "path": "claims[0].value", "claim_id": "c1", "detail": "d"}


def decide(mode, findings, revision_used=False):
    return gate.run({"mode": mode, "findings": findings, "revision_used": revision_used})


class GateRuleTest(unittest.TestCase):
    def test_no_finding_passes_in_every_mode(self):
        for mode in validate.MODES:
            for used in (False, True):
                with self.subTest(mode=mode, revision_used=used):
                    self.assertEqual(decide(mode, [], used),
                                     {"blocked": False, "revise": False, "execution_status": None,
                                      "schema_failed": False, "record_only": False, "validator_findings": []})

    def test_validator_finding_by_mode(self):
        expected = {  # (blocked, revise, execution_status) — 수정 전 / 수정 뒤
            "full": ((True, True, None), (True, False, "INVALID")),
            "agent": ((True, True, None), (True, False, "INVALID")),
            "checklist": ((True, False, "INVALID"), (True, False, "INVALID")),  # 결정 D1: 수정 없이 곧바로 INVALID
            "freeform": ((False, False, None), (False, False, None)),  # 기록만 한다
        }
        for mode, outcomes in expected.items():
            for used, want in zip((False, True), outcomes):
                with self.subTest(mode=mode, revision_used=used):
                    out = decide(mode, [CHECKED], used)
                    self.assertEqual((out["blocked"], out["revise"], out["execution_status"]), want)
                    self.assertEqual(out["validator_findings"], [CHECKED])
                    self.assertEqual(out["record_only"], mode == "freeform")
                    self.assertFalse(out["schema_failed"])

    def test_schema_finding_blocks_every_mode(self):
        for mode in validate.MODES:
            with self.subTest(mode=mode):
                first = decide(mode, [SCHEMA, CHECKED])
                after = decide(mode, [SCHEMA, CHECKED], True)
                self.assertTrue(first["blocked"] and first["schema_failed"] and after["blocked"])
                self.assertEqual(first["revise"], mode != "checklist")
                self.assertEqual(first["execution_status"], "INVALID" if mode == "checklist" else None)
                self.assertEqual(after["execution_status"], "INVALID")
                self.assertEqual(first["validator_findings"], [SCHEMA, CHECKED])

    def test_only_contract_state_value_is_invalid(self):
        seen = set()
        for mode in validate.MODES:
            for findings in ([], [SCHEMA], [CHECKED]):
                for used in (False, True):
                    seen.add(decide(mode, findings, used)["execution_status"])
        self.assertEqual(seen, {None, "INVALID"})

    def test_input_is_not_changed_and_findings_are_copied(self):
        inp = {"mode": "full", "findings": [copy.deepcopy(CHECKED)], "revision_used": False}
        before = copy.deepcopy(inp)
        out = gate.run(inp)
        out["validator_findings"][0]["code"] = "X"
        self.assertEqual(inp, before)

    def test_bad_inputs_raise(self):
        for bad in (None, {"mode": "draft", "findings": [], "revision_used": False},
                    {"mode": "full", "findings": [], "revision_used": 0},
                    {"mode": "full", "findings": [{"code": "X"}], "revision_used": False},
                    {"mode": "full", "findings": {}, "revision_used": False}):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    gate.run(bad)


def tamper_number(inp):
    inp["report"]["claims"][index_of(inp, "c2")]["value"] = Decimal("3.66")


def tamper_unit(inp):
    inp["report"]["claims"][index_of(inp, "c2")]["unit"] = "USD/톤"


def tamper_evidence_id(inp):
    inp["report"]["claims"][index_of(inp, "c3")]["evidence_ids"][1] = f"{EV}999999"


def tamper_snapshot_in_report(inp):
    inp["report"]["snapshot_id"] = "kcs_202201_202412_v2"


def tamper_snapshot_in_evidence(inp):
    inp["report"]["claims"][index_of(inp, "c1")]["evidence_ids"] = ["ev:kcs_202201_202412_v2:observation:101"]


def tamper_prose_number(inp):
    inp["report"]["narrative"] += " 단가는 55% 낮아졌다."


def tamper_prose_change(inp):
    inp["report"]["narrative"] = "점유율이 6%에서 10%로 늘었다."


TAMPERS = {  # 변조 종류 → (변조 함수, 잡아야 할 사유 코드)
    "숫자": (tamper_number, "NUMERIC_MISMATCH"),
    "단위": (tamper_unit, "UNIT_MISMATCH"),
    "근거 ID": (tamper_evidence_id, "EVIDENCE_UNRESOLVED"),
    "스냅샷(보고서)": (tamper_snapshot_in_report, "PROVENANCE_MISMATCH"),
    "스냅샷(근거 ID)": (tamper_snapshot_in_evidence, "EVIDENCE_SNAPSHOT"),
    "뒷받침 없는 산문 숫자": (tamper_prose_number, "PROSE_UNBACKED"),
    "뒷받침 없는 산문 증감": (tamper_prose_change, "PROSE_UNBACKED"),
}


class MvpTamperTest(unittest.TestCase):
    """로드맵 §3 MVP 체크리스트 3번: 검증기가 의도적으로 넣은 변조를 막는다(변조 종류마다 한 개 이상)."""

    def run_mode(self, mode, tamper=None, revision_used=False):
        inp = clean_input()
        inp["run"]["mode"] = mode
        inp["report"]["mode"] = mode
        if tamper:
            tamper(inp)
        report_before = copy.deepcopy(inp["report"])
        findings = validate.run(inp)["findings"]
        decision = gate.run({"mode": mode, "findings": findings, "revision_used": revision_used})
        self.assertEqual(inp["report"], report_before)  # 검증기·차단 판정은 보고서를 고치지 않는다
        return findings, decision

    def test_clean_report_passes_every_mode(self):
        for mode in validate.MODES:
            with self.subTest(mode=mode):
                findings, decision = self.run_mode(mode)
                self.assertEqual(findings, [])
                self.assertFalse(decision["blocked"])

    def test_each_tamper_is_blocked_outside_freeform(self):
        for name, (tamper, code) in TAMPERS.items():
            for mode in ("full", "agent"):
                with self.subTest(tamper=name, mode=mode):
                    findings, decision = self.run_mode(mode, tamper)
                    self.assertIn(code, [f["code"] for f in findings])
                    self.assertTrue(decision["blocked"])
                    self.assertTrue(decision["revise"])  # 수정 1회 기회
                    _, after = self.run_mode(mode, tamper, revision_used=True)
                    self.assertEqual(after["execution_status"], "INVALID")  # 수정 뒤에도 막히면 INVALID

    def test_each_tamper_makes_checklist_invalid_at_once(self):
        for name, (tamper, code) in TAMPERS.items():
            with self.subTest(tamper=name):
                findings, decision = self.run_mode("checklist", tamper)
                self.assertIn(code, [f["code"] for f in findings])
                self.assertEqual((decision["blocked"], decision["revise"], decision["execution_status"]),
                                 (True, False, "INVALID"))

    def test_each_tamper_is_only_recorded_in_freeform(self):
        for name, (tamper, code) in TAMPERS.items():
            with self.subTest(tamper=name):
                findings, decision = self.run_mode("freeform", tamper)
                self.assertIn(code, [f["code"] for f in findings])
                self.assertEqual({f["check"] for f in findings}, {"validator"})
                self.assertEqual((decision["blocked"], decision["execution_status"], decision["record_only"]),
                                 (False, None, True))
                self.assertEqual(decision["validator_findings"], findings)  # 막았을 사유를 기록한다

    def test_schema_failure_blocks_freeform_too(self):
        def float_value(inp):
            inp["report"]["claims"][index_of(inp, "c2")]["value"] = 3.6

        findings, decision = self.run_mode("freeform", float_value)
        self.assertIn("SCHEMA_CLAIM", [f["code"] for f in findings])
        self.assertTrue(decision["blocked"] and decision["schema_failed"] and decision["revise"])
        _, after = self.run_mode("freeform", float_value, revision_used=True)
        self.assertEqual(after["execution_status"], "INVALID")


if __name__ == "__main__":
    unittest.main()
