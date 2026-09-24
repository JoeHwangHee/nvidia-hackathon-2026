"""조립 작업 AS2: run-case 배선의 부품 시험(도구 봉투 → 판정 정책 P3 근거 상태 변환, 반올림 불안정 규칙, code_version,
비교 대상 집합 읽기, 계열별 조기 종료). 봉투는 시험 안에서 만든 모양이고 값은 합성이다. 네트워크와 키 없이 돈다.

- 근거 상태 변환(dispatch.evidence_state)은 봉투만 보는 순수 함수라 병합된 P3(policy.signal_decide)에 그대로 넣어 판정을
  확인한다(P3 코드는 고치지 않는다).
- 계열별 조기 종료(MT1 결정 ⑦): 한 계열의 도구를 받지 못해 null을 적는 것은 그 계열에 다른 자료 부족 사유가 있을 때뿐이고,
  없으면 ValueError다. 흐름 조정(I12)은 그 ValueError를 CODE_ERROR(FAILED)로 기록한다(HOLD로 숨지 않는다).
"""
import copy
import tempfile
import unittest
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from unittest import mock

from tradesentry.cli import dispatch
from tradesentry.contract.policy_load import load_policy
from tradesentry.dal import query
from tradesentry.policy import signal_decide
from tradesentry.runlog import cause_codes
from tradesentry.workflow import model_client, orchestrate

from . import detect_fixture as df
from . import run_case_fixture as rf

SNAP = "controlled_fixture_v0"
T, N = "TRIGGERED", "NOT_TRIGGERED"
POLICY = load_policy("dev-0.1")
CASE = {"case_id": "850450-XA-202412", "hs6": "850450", "partner": "XA", "month": "202412", "baseline_month": "202312",
        "signals": {"unit_value": T, "share": T}, "snapshot_id": SNAP, "policy_version": "dev-0.1"}


def ev(n: int) -> str:
    return f"ev:{SNAP}:observation:{n}"


def envelope(tool: str, *, metrics=(), comparability=None, missingness=(), retryable_error=None) -> dict:
    return {"query_id": f"{tool}-0", "tool": tool, "scope": {}, "snapshot_id": SNAP, "source_kind": "controlled",
            "evidence_ids": [], "metrics": list(metrics), "comparability": comparability,
            "missingness": list(missingness), "retryable_error": retryable_error, "elapsed_ms": 1}


def metric(symbol: str, partner: str, period: str, value, inputs=None, baseline=None) -> dict:
    return {"metric_id": f"{symbol}-{partner}-{period}", "formula_version": "t",
            "inputs": {"metric": symbol, "hs6": "850450", "partner": partner, "period": period,
                       "baseline_period": baseline, **(inputs or {})},
            "evidence_ids": [ev(1)], "value": value, "unit": "USD", "comparability_flags": [], "tolerance": None}


def checked(unit_issues=(), share_issues=(), comparable=True) -> dict:
    return envelope("check_comparability", comparability={
        "comparable": comparable,
        "signals": {"unit_value": {"evaluable": not unit_issues, "issues": list(unit_issues)},
                    "share": {"evaluable": not share_issues, "issues": list(share_issues)}}})


def history(country=(600, 360), world=(6000, 6000), q=(100, 100)) -> dict:
    """get_history 봉투: V(대상국·ALL, 두 달), U(두 달), r_U. 값은 정수 입력으로 다시 계산되는 모양이다."""
    (v0, v1), (w0, w1), (q0, q1) = country, world, q
    out = [metric("V", "XA", "202312", v0), metric("V", "XA", "202412", v1),
           metric("V", "ALL", "202312", w0), metric("V", "ALL", "202412", w1)]
    out += [metric("U", "XA", "202312", (Decimal(v0) / q0).quantize(Decimal("0.01")), {"V": v0, "Q": q0}),
            metric("U", "XA", "202412", (Decimal(v1) / q1).quantize(Decimal("0.01")), {"V": v1, "Q": q1})]
    r_u = ((Decimal(v1) * q0) / (Decimal(v0) * q1) - 1) * 100
    out.append(metric("r_U", "XA", "202412", r_u.quantize(Decimal("0.1")), {"V_0": v0, "Q_0": q0, "V_1": v1, "Q_1": q1},
                      baseline="202312"))
    return envelope("get_history", metrics=out)


def peers(*months_per_peer) -> dict:
    return envelope("compare_partners", comparability={
        "grouping_version": "g0", "comparable": True, "issues": [],
        "peers": [{"partner": f"P{i}", "peer_rank": i + 1,
                   "months": [{"month": m, "observation_status": s, "amount_zero": None}
                              for m, s in zip(("202312", "202412"), statuses)]}
                  for i, statuses in enumerate(months_per_peer)]})


def missing(partner: str, hs_code: str, month: str, status: str = "REQUEST_FAILED", n: int = 9, **extra) -> dict:
    return {"evidence_id": ev(n), "request_id": "r", "partner_code": partner, "hs_code": hs_code, "month": month,
            "flow": "import", "observation_status": status, **extra}


def share_case() -> dict:
    return dict(CASE, signals={"unit_value": N, "share": T})


def unit_case() -> dict:
    return dict(CASE, signals={"unit_value": T, "share": N})


class ComparisonMarksTest(unittest.TestCase):
    def state(self, *envelopes, case=None):
        return dispatch.evidence_state(case or share_case(), list(envelopes), POLICY)

    def test_partners_no_trade_is_done_and_only_missing_peers_are_incomplete(self):
        base = [checked(), history()]
        done = self.state(*base, peers(("CONFIRMED_NO_TRADE", "CONFIRMED_NO_TRADE"), ("NOT_COLLECTED", "OBSERVED")))
        self.assertEqual(done["share"]["comparisons"]["partners"], "done")
        incomplete = self.state(*base, peers(("NOT_COLLECTED", "OBSERVED"), ("OBSERVED", "REQUEST_FAILED")))
        self.assertEqual(incomplete["share"]["comparisons"]["partners"], "incomplete")
        no_peers = envelope("compare_partners", comparability={"grouping_version": "g0", "comparable": False,
                                                               "issues": ["no_allowed_peers"], "peers": []})
        self.assertEqual(self.state(*base, no_peers)["share"]["comparisons"]["partners"], "not_performed")
        refused = envelope("compare_partners", retryable_error={"code": "invalid_args", "detail": "x"})
        self.assertEqual(self.state(*base, refused)["share"]["comparisons"]["partners"], "not_performed")
        self.assertEqual(self.state(*base)["share"]["comparisons"], {
            "comparability": "done", "partners": "not_performed", "country_and_world": "done"})

    def test_incomplete_partners_become_comparison_incomplete_hold_in_p3(self):
        state = self.state(checked(), history(), peers(("NOT_COLLECTED", "NOT_COLLECTED")))
        out = signal_decide.run({"policy": POLICY, "case": share_case(), "evidence": state})
        self.assertEqual((out["signal_status"]["share"], out["basis"]["share"]), ("HOLD", "comparison_incomplete"))

    def test_country_and_world_missing_value_is_incomplete(self):
        gap = history()
        gap["metrics"][2]["value"] = None  # ALL 기준월 V 없음
        self.assertEqual(self.state(checked(), gap)["share"]["comparisons"]["country_and_world"], "incomplete")
        self.assertEqual(self.state(checked())["share"]["comparisons"]["country_and_world"], "not_performed")


class ComparabilityIssuesTest(unittest.TestCase):
    def test_check_comparability_issues_pass_through_per_family(self):
        state = dispatch.evidence_state(CASE, [checked(unit_issues=["zero_weight:202312"],
                                                       share_issues=["zero_denominator:202412"]),
                                               history()], POLICY)  # 단가 사유가 있어 분해 없이 null
        self.assertEqual(state["unit_value"]["comparability_issues"], ["zero_weight:202312"])
        self.assertEqual(state["share"]["comparability_issues"], ["zero_denominator:202412"])

    def test_world_below_country_amount_is_a_share_issue(self):
        """dev20 분류 7: 전체국가(ALL) 분모 금액이 대상국 금액보다 작은 달은 점유율 비교 가능성 문제다 → 점유율 HOLD."""
        state = dispatch.evidence_state(share_case(), [checked(), history(country=(600, 8000), world=(10000, 6000)),
                                                       peers(("OBSERVED", "OBSERVED"))], POLICY)
        self.assertEqual(state["share"]["comparability_issues"], ["denominator_below_partner:202412"])
        out = signal_decide.run({"policy": POLICY, "case": share_case(), "evidence": state})
        self.assertEqual(out["signal_status"]["share"], "HOLD")
        equal = dispatch.evidence_state(share_case(), [checked(), history(country=(600, 6000), world=(10000, 6000))],
                                        POLICY)
        self.assertEqual(equal["share"]["comparability_issues"], [])  # 같으면 문제가 아니다


class MissingnessTest(unittest.TestCase):
    def test_dedupe_by_evidence_id_keeps_the_c_type_codes(self):
        plain = missing("XA", "850450", "202412")
        c_type = dict(plain, hs10_codes=["8504501000"], hs10_codes_source="other_case_month")
        other = missing("ALL", "850450", "202312", "NOT_COLLECTED", n=10)
        got = dispatch.evidence_missingness([envelope("get_history", missingness=[plain, other]),
                                             envelope("check_comparability", missingness=[c_type])])
        self.assertEqual(got, [c_type, other])


class EarlyStopByFamilyTest(unittest.TestCase):
    """분해·이력을 받지 못한 단가 블록은 그 계열에 다른 자료 부족 사유가 있을 때만 null로 만든다."""

    def test_null_decomposition_needs_a_unit_value_reason(self):
        with self.assertRaises(ValueError):
            dispatch.evidence_state(unit_case(), [checked(comparable=False, share_issues=["zero_denominator:202412"])],
                                    POLICY)  # 점유율만의 사유로는 단가를 null로 적지 않는다

    def test_null_decomposition_with_its_own_reason_is_hold(self):
        state = dispatch.evidence_state(unit_case(), [checked(comparable=False, unit_issues=["zero_weight:202412"])],
                                        POLICY)
        self.assertEqual({k: state["unit_value"][k] for k in ("U_baseline", "decomposition", "children")},
                         {"U_baseline": None, "decomposition": None, "children": []})
        out = signal_decide.run({"policy": POLICY, "case": unit_case(), "evidence": state})
        self.assertEqual((out["signal_status"]["unit_value"], out["basis"]["unit_value"]), ("HOLD", "data_insufficient"))
        gap = dispatch.evidence_state(unit_case(), [envelope("check_comparability", comparability=checked()[
            "comparability"], missingness=[missing("XA", "850450", "202412")])], POLICY)
        self.assertIsNone(gap["unit_value"]["decomposition"])  # 대상국 빠진 관측도 사유다

    def test_decomposition_envelope_without_effect_metrics_is_a_wiring_error(self):
        decomposed = envelope("decompose_hs", metrics=[], comparability={"parent_check": []})
        with self.assertRaises(dispatch.WiringError):
            dispatch.evidence_state(unit_case(), [checked(), history(), decomposed], POLICY)

    def test_flow_records_code_error_not_hold(self):
        """흐름 조정(checklist)에 그 변환을 걸면 조기 종료 누락은 FAILED·CODE_ERROR로 남는다."""
        case = dict(CASE)
        first = checked(comparable=False, share_issues=["zero_denominator:202412"])
        config = model_client.load_model_config()
        ports = orchestrate.unit_ports(case, "checklist", "run_case-260925000000", config.limits, grouping_version="g0",
                                       policy=POLICY, rows=lambda ids: {},
                                       evidence_state=lambda c, e: dispatch.evidence_state(c, e, POLICY))
        ports.tool = lambda name, args: copy.deepcopy(first)
        ctx = orchestrate.RunContext(run_id="run_case-260925000000", case=case, mode="checklist", dataset=SNAP,
                                     rulebook_version="RB-1", grouping_version="g0", code_version="unknown")
        record = orchestrate.orchestrate(ctx, ports, config)["record"]
        self.assertEqual((record["execution_status"], [e["code"] for e in record["errors"]]),
                         (cause_codes.execution_status(cause_codes.CODE_ERROR), [cause_codes.CODE_ERROR]))
        self.assertIsNone(record["review_status_final"])


class RoundingUnstableTest(unittest.TestCase):
    """U4 후보 규칙(사용자 결정 대기): 금액 그대로, 두 달 중량 Q ± 0.5 kg의 r_U 구간."""

    def test_rule_cases(self):
        rule = dispatch.rounding_unstable
        self.assertTrue(rule(120, 12, 162, 12, Decimal("0.5"), 30))  # r_U +35%, 하한 약 +24.2% < 30(DT5 분류 6)
        self.assertFalse(rule(600, 100, 360, 100, Decimal("0.5"), 30))  # 사례 A: −40%, 상한 약 −39.4% ≤ −30
        self.assertTrue(rule(600, 1, 360, 1, Decimal("0.5"), 30) and rule(600, 100, 360, Fraction(1, 2), 1, 30))  # Q ≤ δ
        # 경계와 같으면 안정: 하한이 정확히 θ(= 30%)가 되게 만든다. v1·(q0−δ) / (v0·(q1+δ)) = 1.3
        self.assertFalse(rule(100, Fraction(21, 2), 130, Fraction(19, 2), Decimal("0.5"), 30))
        self.assertTrue(rule(100, Fraction(21, 2), 129, Fraction(19, 2), Decimal("0.5"), 30))
        # r_U < 0 쪽 경계: 상한이 정확히 −θ
        self.assertFalse(rule(100, Fraction(19, 2), 70, Fraction(21, 2), Decimal("0.5"), 30))
        self.assertTrue(rule(100, Fraction(19, 2), 71, Fraction(21, 2), Decimal("0.5"), 30))

    def test_switch_is_off_and_turning_it_on_holds_the_unit_value_signal(self):
        self.assertIs(dispatch.ROUNDING_UNSTABLE_ENABLED, False)
        # 분해 봉투 없이 단가 블록을 만들 수 있게 단가 계열 사유 하나(시험용 문자열)를 둔다. 규칙만 보는 시험이다.
        envs = [checked(unit_issues=["test_reason"]), history(country=(120, 162), world=(100000, 100000), q=(12, 12))]
        self.assertFalse(dispatch.evidence_state(unit_case(), envs, POLICY)["unit_value"]["rounding_unstable"])
        with mock.patch.object(dispatch, "ROUNDING_UNSTABLE_ENABLED", True):
            self.assertTrue(dispatch.evidence_state(unit_case(), envs, POLICY)["unit_value"]["rounding_unstable"])
            stable = [envs[0], history()]  # 사례 A 값(−40%, 상한 약 −39.4%)
            self.assertFalse(dispatch.evidence_state(unit_case(), stable, POLICY)["unit_value"]["rounding_unstable"])


class CodeVersionTest(unittest.TestCase):
    HASH = "0123456789abcdef0123456789abcdef01234567"

    def test_git_layouts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "plain" / ".git" / "refs" / "heads").mkdir(parents=True)
            (root / "plain" / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
            (root / "plain" / ".git" / "refs" / "heads" / "main").write_text(self.HASH + "\n")
            self.assertEqual(dispatch.code_version(root / "plain"), self.HASH)
            # 작업 폴더(worktree): .git 파일 → gitdir, commondir의 packed-refs
            common = root / "common"
            (common / "worktrees" / "w").mkdir(parents=True)
            (common / "packed-refs").write_text(f"# pack-refs\n{self.HASH} refs/heads/topic\n")
            (common / "worktrees" / "w" / "HEAD").write_text("ref: refs/heads/topic\n")
            (common / "worktrees" / "w" / "commondir").write_text("../..\n")
            (root / "wt").mkdir()
            (root / "wt" / ".git").write_text(f"gitdir: {common / 'worktrees' / 'w'}\n")
            self.assertEqual(dispatch.code_version(root / "wt"), self.HASH)
            (root / "detached" / ".git").mkdir(parents=True)
            (root / "detached" / ".git" / "HEAD").write_text(self.HASH + "\n")
            self.assertEqual(dispatch.code_version(root / "detached"), self.HASH)
            self.assertEqual(dispatch.code_version(root / "none"), "unknown")
            (root / "bad" / ".git").mkdir(parents=True)
            (root / "bad" / ".git" / "HEAD").write_text("not-a-hash\n")
            self.assertEqual(dispatch.code_version(root / "bad"), "unknown")

    def test_this_checkout(self):
        self.assertRegex(dispatch.code_version(), r"^([0-9a-f]{40}|unknown)$")


class GroupingVersionTest(unittest.TestCase):
    def test_read_from_the_peer_table_or_refuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            with_peers = rf.install_two_way(Path(tmp) / "a")
            without = df.install(Path(tmp) / "b", df.WORLD_GAP)
            with mock.patch.object(query, "SNAPSHOTS_ROOT", with_peers), query.open_snapshot(rf.TWO_WAY_ID) as snap:
                self.assertEqual(dispatch.snapshot_grouping_version(snap), "g0")
            with mock.patch.object(query, "SNAPSHOTS_ROOT", without), \
                    query.open_snapshot("as1_detect_world_gap") as snap:
                with self.assertRaises(dispatch.RunCaseError):
                    dispatch.snapshot_grouping_version(snap)


if __name__ == "__main__":
    unittest.main()
