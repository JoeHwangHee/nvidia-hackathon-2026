"""단위 E1(evaluation_batch_run) 골든 쌍 밖 시험: 순서 seed 결정성, dev20 모양 묶음(사례 20 × 모드 3), 실행명 충돌 없음
(두 실행기가 동시에 도는 경우 포함), 실패 실행이 분모에 남음, 묶음 기록 키와 채점기 하네스 줄 규칙, 실행 조건 입력 파일.

실제 run-case(로드맵 AS2)는 가짜 사례 실행 함수(tests/harness_fixtures.py FakeRunner)로 바꿨다. 채점기 코드는 import하지
않고 키 목록은 자료 계약 문서에서 읽는다. 모든 파일은 임시 폴더에 쓴다(outputs/·outputs/sealed/의 실제 내용에 닿지 않는다).
"""
import hashlib
import json
import tempfile
import threading
import unittest
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import harness_fixtures as hf
from tradesentry.evaluation import batch_run
from tradesentry.runlog import cause_codes


def spec(cases=None, modes=hf.DEV20_MODES, dataset="dev20", seed="dev-order-v1", versions=None):
    return batch_run.BatchSpec(dataset=dataset, cases=tuple(cases or hf.dev20_cases()), modes=tuple(modes),
                               order_seed=seed, versions=dict(versions or hf.VERSIONS))


class TempOutputs:
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.parent = Path(self.tmp.name) / "outputs"
        self.sealed = self.parent / "sealed"
        self.clock = hf.FakeClock()

    def execute(self, runner, s=None, clock=None):
        clock = clock or self.clock
        return batch_run.execute_batch(s or spec(), runner, parent=self.parent, other_parent=self.sealed,
                                       clock=clock, sleep=clock.sleep)


class OrderTest(unittest.TestCase):
    def test_same_seed_same_order_and_every_pair_once(self):
        ids = [c["case_id"] for c in hf.dev20_cases()]
        first = batch_run.plan_order(ids, list(hf.DEV20_MODES), "dev-order-v1")
        self.assertEqual(first, batch_run.plan_order(list(ids), list(hf.DEV20_MODES), "dev-order-v1"))
        self.assertEqual(sorted(first), sorted((c, m) for c in ids for m in hf.DEV20_MODES))
        self.assertNotEqual(first, batch_run.plan_order(ids, list(hf.DEV20_MODES), "dev-order-v2"))
        # 입력 순서를 바꿔도 같은 순서(열쇠가 정한다)
        self.assertEqual(first, batch_run.plan_order(ids[::-1], list(hf.DEV20_MODES)[::-1], "dev-order-v1"))

    def test_key_is_sha256_of_seed_case_mode_bytes(self):
        """E2가 따로 구현할 규칙을 바이트 수준으로 고정한다(머리 설명 1)."""
        ids = [c["case_id"] for c in hf.dev20_cases(5)]
        expected = sorted(((c, m) for c in ids for m in ("freeform", "full")),
                          key=lambda p: (hashlib.sha256(("s1\n" + p[0] + "\n" + p[1]).encode("utf-8")).hexdigest(),
                                         p[0], p[1]))
        self.assertEqual(batch_run.plan_order(ids, ["freeform", "full"], "s1"), expected)

    def test_modes_are_interleaved(self):
        order = batch_run.plan_order([c["case_id"] for c in hf.dev20_cases()], list(hf.DEV20_MODES), "dev-order-v1")
        first_third = {m for _, m in order[:20]}
        self.assertEqual(first_third, set(hf.DEV20_MODES))  # 한 모드가 앞쪽에 몰리지 않는다

    def test_bad_plan_is_refused(self):
        for case_ids, modes, seed in ((["a", "a"], ["full"], "s"), ([], ["full"], "s"), (["a"], ["fast"], "s"),
                                      (["a"], ["full", "full"], "s"), (["a"], ["full"], ""), (["a"], ["full"], 1)):
            with self.subTest(case_ids=case_ids, modes=modes, seed=seed), self.assertRaises(batch_run.BatchError):
                batch_run.plan_order(case_ids, modes, seed)


class Dev20ShapeBatchTest(TempOutputs, unittest.TestCase):
    PLAN = {"850431-XA-202401": "infra", "850450-XC-202403": "raise", "850490-XD-202404": "invalid",
            "850431-XE-202405": "mismatch", ("850432-XF-202406", "agent"): "budget"}

    def setUp(self):
        super().setUp()
        self.runner = hf.FakeRunner(self.clock, self.PLAN)
        self.result = self.execute(self.runner)
        self.lines = hf.read_jsonl(self.result.batch_file)

    def test_one_line_per_planned_pair_in_plan_order(self):
        self.assertEqual(self.result.run_id, "evaluate-260925100000")
        self.assertEqual(len(self.lines), 63)  # 계획 60 + 인프라 실패 재실행 3(룰북 B5)
        self.assertEqual(self.lines, json.loads(json.dumps(self.result.lines), parse_float=Decimal))
        order = batch_run.plan_order([c["case_id"] for c in hf.dev20_cases()], list(hf.DEV20_MODES), "dev-order-v1")
        reruns = [pair for pair in order if pair[0] == "850431-XA-202401"]  # 첫 실행 순서 그대로
        self.assertEqual([(line["case_id"], line["mode"]) for line in self.lines], order + reruns)
        self.assertEqual([(c.case["case_id"], c.mode) for c in self.runner.calls], order + reruns)
        self.assertEqual((self.result.rerun_targets, self.result.reruns), (3, 3))

    def test_run_ids_unique_and_case_dirs_are_siblings(self):
        run_ids = [line["run_id"] for line in self.lines]
        self.assertEqual(len(set(run_ids)), 63)  # 재실행도 새 실행명
        self.assertTrue(all(r.startswith("run_case-") for r in run_ids))
        self.assertTrue(all((self.parent / r).is_dir() for r in run_ids))  # 채점기가 <run_dir>.parent / run_id를 연다
        self.assertEqual(sorted(p.name for p in self.parent.iterdir()), sorted(run_ids + [self.result.run_id]))
        self.assertFalse(self.sealed.exists() and any(self.sealed.iterdir()))
        stamps = [r.rsplit("-", 1)[1] for r in [self.result.run_id] + run_ids]
        self.assertEqual(stamps, sorted(stamps))  # 시각은 앞서지 않는다

    def test_failures_stay_in_the_denominator(self):
        by_status: dict[str, int] = {}
        for line in self.lines:
            by_status[line["execution_status"]] = by_status.get(line["execution_status"], 0) + 1
        # infra 사례 3줄(FAILED 5xx)과 그 재실행 3줄(가짜는 또 5xx) + raise 3 + invalid 3 + mismatch 3 = FAILED 15, budget 1
        self.assertEqual(by_status, {"COMPLETED": 47, "FAILED": 15, "BUDGET_EXCEEDED": 1})
        harness = [line for line in self.lines if line["errors"] and line["errors"][0]["detail"].startswith("harness:")]
        self.assertEqual(sorted({line["errors"][0]["detail"] for line in harness}),
                         ["harness:RuntimeError", "harness:invalid_record", "harness:record_mismatch"])
        for line in harness:
            self.assertEqual((line["execution_status"], line["errors"][0]["code"], line["review_status_final"]),
                             ("FAILED", cause_codes.CODE_ERROR, None))
            self.assertEqual(line["wall_ms"], 250)  # 하네스가 잰 시간
            self.assertFalse(cause_codes.infra_rerun_eligible(line["execution_status"], line["errors"]))
        infra = [line for line in self.lines if line["case_id"] == "850431-XA-202401"]
        self.assertTrue(all(cause_codes.infra_rerun_eligible(x["execution_status"], x["errors"]) for x in infra))

    def test_keys_match_contract_and_scorer_line_rules(self):
        contract_keys = hf.contract_run_record_keys()
        self.assertEqual(len(contract_keys), 24)
        run_side = tuple(k for k in contract_keys if k not in hf.SCORER_KEYS)
        for line in self.lines:
            self.assertEqual(tuple(line), run_side)  # 계약 순서, 채점 키 세 개는 채점기가 더한다
            self.assertEqual(hf.scorer_line_problems(line), [])
        # 채점기가 묶음 수준에서 보는 것: 자료 묶음 하나, 스냅샷 하나, run_id 중복 없음, 계획 조합만, 조합마다 한 줄
        self.assertEqual({line["dataset"] for line in self.lines}, {"dev20"})
        self.assertEqual({line["snapshot_id"] for line in self.lines}, {"dev20"})
        pairs = [(line["case_id"], line["mode"]) for line in self.lines]
        planned = {(c["case_id"], m) for c in hf.dev20_cases() for m in hf.DEV20_MODES}
        self.assertEqual(set(pairs), planned)
        # 조합마다 한 줄, 또는 채점기 재실행 모양(실행명 시각 순으로 FAILED 한 줄 뒤 재실행 한 줄)
        for pair in planned:
            rows = sorted((line for line in self.lines if (line["case_id"], line["mode"]) == pair),
                          key=lambda line: line["run_id"])
            self.assertLessEqual(len(rows), 2)
            if len(rows) == 2:
                self.assertEqual(rows[0]["execution_status"], "FAILED")
                self.assertTrue(cause_codes.infra_rerun_eligible(rows[0]["execution_status"], rows[0]["errors"]))

    def test_batch_file_is_exclusive(self):
        with self.assertRaises(FileExistsError):
            open(self.result.batch_file, "x").close()


class InfraRerunTest(TempOutputs, unittest.TestCase):
    """룰북 B5: 원인이 PROVIDER_HTTP_5XX·PROVIDER_CONNECTION·HTTP 429인 PROVIDER_HTTP_4XX뿐인 FAILED만 첫 실행이 끝난 뒤
    한 번 다시 돈다(429는 2026-09-25 15:52 사용자 결정)."""

    def test_only_infra_failures_rerun_once_after_the_first_pass(self):
        cases = hf.dev20_cases(4)
        seen: dict = {}
        plan = {cases[0]["case_id"]: "infra", cases[1]["case_id"]: "budget", cases[2]["case_id"]: "raise"}
        base = hf.FakeRunner(self.clock, plan)

        def runner(call):
            key = (call.case["case_id"], call.mode)
            seen[key] = seen.get(key, 0) + 1
            if key == (cases[0]["case_id"], "full") and seen[key] == 2:  # 재실행은 성공한다
                return hf.completed_record(call)
            if key[0] == cases[3]["case_id"] and key[1] == "agent":  # 연결 실패도 재실행 대상이다
                return hf.failed_record(call, cause_codes.PROVIDER_CONNECTION)
            return base(call)

        result = self.execute(runner, spec(cases))
        lines = hf.read_jsonl(result.batch_file)
        self.assertEqual((result.rerun_targets, result.reruns), (4, 4))  # infra 3모드 + 연결 실패 1
        first, extra = lines[:12], lines[12:]
        self.assertEqual({(x["case_id"], x["mode"]) for x in extra},
                         {(cases[0]["case_id"], m) for m in hf.DEV20_MODES} | {(cases[3]["case_id"], "agent")})
        order = [(x["case_id"], x["mode"]) for x in first]
        self.assertEqual([(x["case_id"], x["mode"]) for x in extra],
                         [pair for pair in order if pair in {(x["case_id"], x["mode"]) for x in extra}])
        self.assertEqual(max(seen.values()), 2)  # 재실행의 실패는 다시 돌리지 않는다
        rerun_full = [x for x in extra if x["mode"] == "full" and x["case_id"] == cases[0]["case_id"]]
        self.assertEqual(rerun_full[0]["execution_status"], "COMPLETED")
        self.assertTrue(all(x["run_id"] > y["run_id"] for x in extra for y in first))  # 새 실행명, 더 늦은 시각

    def test_http_429_lines_rerun_but_other_4xx_do_not(self):
        cases = hf.dev20_cases(2)
        seen: dict = {}

        def failed_4xx(call, detail):
            record = hf.failed_record(call, cause_codes.PROVIDER_HTTP_4XX)
            return {**record, "errors": [dict(record["errors"][0], detail=detail)]}

        def runner(call):
            key = (call.case["case_id"], call.mode)
            seen[key] = seen.get(key, 0) + 1
            if key == (cases[0]["case_id"], "full"):
                return failed_4xx(call, "HTTP 429(재전송 3회 뒤)") if seen[key] == 1 else hf.completed_record(call)
            if key == (cases[1]["case_id"], "agent"):
                return failed_4xx(call, "HTTP 400")
            if key == (cases[1]["case_id"], "full"):
                return failed_4xx(call, "policy_denied(l7) 403: 샌드박스 정책 프록시가 요청을 막았다(재실행 대상 아님)")
            return hf.completed_record(call)

        result = self.execute(runner, spec(cases))
        lines = hf.read_jsonl(result.batch_file)
        self.assertEqual((result.rerun_targets, result.reruns), (1, 1))
        self.assertEqual([(x["case_id"], x["mode"], x["execution_status"]) for x in lines[6:]],
                         [(cases[0]["case_id"], "full", "COMPLETED")])
        self.assertEqual(seen[(cases[1]["case_id"], "agent")], 1)
        self.assertEqual(seen[(cases[1]["case_id"], "full")], 1)

    def test_no_targets_means_zero_reruns(self):
        result = self.execute(hf.FakeRunner(self.clock), spec(hf.dev20_cases(2)))
        self.assertEqual((result.rerun_targets, result.reruns, len(result.lines)), (0, 0, 6))


class PacingTest(TempOutputs, unittest.TestCase):
    """속도 조절(AS3 세 번째 PR): 모델 실행 사이 최소 간격, 직전 토큰 수에 비례한 쉼, HTTP 429 뒤 더 쉼. checklist는 쉬지 않는다."""

    PACING = batch_run.Pacing(min_gap_ms=60000, tokens_per_minute=50000, after_rate_limit_ms=120000)

    def runner(self, tokens: dict, rate_limited: set, run_ms: int = 20000):
        starts: list = []

        def run(call):
            starts.append((call.case["case_id"], call.mode, self.clock()))
            self.clock.advance_ms(run_ms)
            record = hf.completed_record(call, tokens_in=tokens.get(call.case["case_id"], 9000), tokens_out=0)
            if (call.case["case_id"], call.mode) in rate_limited:
                attempts = {"tool_attempts": 2, "model_requests": 1, "tokens_in": 0, "tokens_out": 0, "wall_ms": run_ms}
                record = {**record, "review_status_final": None, "signal_status": None, "execution_status": "FAILED",
                          "tool_attempts": 2, "model_requests": 1, "tokens_in": 0, "tokens_out": 0, "wall_ms": run_ms,
                          "critic_used": False,
                          "errors": [cause_codes.error_entry(cause_codes.PROVIDER_HTTP_4XX, "basic", attempts, [],
                                                             "HTTP 429")]}
            return record

        return run, starts

    def test_model_runs_are_spaced_by_gap_and_tokens(self):
        cases = hf.dev20_cases(3)
        tokens = {cases[0]["case_id"]: 150000, cases[1]["case_id"]: 9000, cases[2]["case_id"]: 9000}
        run, starts = self.runner(tokens, set())
        result = batch_run.execute_batch(spec(cases), run, parent=self.parent, other_parent=self.sealed,
                                         clock=self.clock, sleep=self.clock.sleep, pacing=self.PACING)
        model = [(c, m, t) for c, m, t in starts if m != "checklist"]
        for (case_a, _, t_a), (_, _, t_b) in zip(model, model[1:]):
            gap = max(60000, tokens[case_a] * 60000 // 50000)  # 15만 토큰 뒤에는 3분
            self.assertGreaterEqual((t_b - t_a).total_seconds() * 1000, gap)
        self.assertGreater(result.paced_ms, 0)
        self.assertEqual(result.rate_limit_waits, 0)
        # checklist는 앞 실행 바로 뒤에 시작한다(쉬지 않는다)
        checks = [i for i, (_, m, _) in enumerate(starts) if m == "checklist" and i > 0]
        for i in checks:
            self.assertLess((starts[i][2] - starts[i - 1][2]).total_seconds(), 25)

    def test_rate_limited_run_makes_the_next_model_run_wait_longer(self):
        cases = hf.dev20_cases(2)
        order = batch_run.plan_order([c["case_id"] for c in cases], ["agent", "full"], "dev-order-v1")
        run, starts = self.runner({}, {order[0]})
        result = batch_run.execute_batch(spec(cases, modes=("agent", "full")), run, parent=self.parent,
                                         other_parent=self.sealed, clock=self.clock, sleep=self.clock.sleep,
                                         pacing=self.PACING)
        first_end = starts[0][2] + timedelta(milliseconds=20000)
        self.assertGreaterEqual((starts[1][2] - first_end).total_seconds(), 120)
        self.assertEqual(result.rate_limit_waits, 1)
        # 2026-09-25 15:52 사용자 결정(사용자 결정 5 변경): 429로 끝난 줄은 묶음 끝에 한 번 다시 돈다. 이 대역은 재실행도
        # 429로 끝나게 두었다. 재실행 줄은 다시 돌리지 않고 두 줄 모두 실패로 남는다(분모, 룰북 B5)
        failed = [x for x in result.lines if x["execution_status"] == "FAILED"]
        self.assertEqual([(x["case_id"], x["mode"]) for x in failed], [order[0], order[0]])
        self.assertEqual((result.rerun_targets, result.reruns, len(result.lines)), (1, 1, 5))
        self.assertEqual((starts[-1][0], starts[-1][1]), order[0])
        self.assertGreaterEqual((starts[-1][2] - starts[-2][2]).total_seconds(), 60)  # 재실행도 속도 조절을 받는다

    def test_no_pacing_means_no_wait(self):
        run, starts = self.runner({}, set())
        result = batch_run.execute_batch(spec(hf.dev20_cases(2)), run, parent=self.parent, other_parent=self.sealed,
                                         clock=self.clock, sleep=self.clock.sleep)
        self.assertEqual(result.paced_ms, 0)

    def test_pacing_config_shape(self):
        self.assertEqual(batch_run.pacing_from_config({"min_gap_ms": 1, "tokens_per_minute": 2,
                                                       "after_rate_limit_ms": 3}), batch_run.Pacing(1, 2, 3))
        for bad in (None, {}, {"min_gap_ms": 1, "tokens_per_minute": 2}, {"min_gap_ms": -1, "tokens_per_minute": 2,
                    "after_rate_limit_ms": 3}, {"min_gap_ms": True, "tokens_per_minute": 2, "after_rate_limit_ms": 3},
                    {"min_gap_ms": 1.5, "tokens_per_minute": 2, "after_rate_limit_ms": 3},
                    {"min_gap_ms": 1, "tokens_per_minute": 2, "after_rate_limit_ms": 3, "x": 0}):
            with self.subTest(bad=bad), self.assertRaises(batch_run.BatchError):
                batch_run.pacing_from_config(bad)

    def test_only_http_429_counts_as_rate_limited(self):
        entry = cause_codes.error_entry(cause_codes.PROVIDER_HTTP_4XX, "basic",
                                        {k: 0 for k in cause_codes.ATTEMPT_KEYS}, [], "HTTP 429")
        self.assertTrue(batch_run.rate_limited({"errors": [entry]}))
        self.assertTrue(batch_run.rate_limited({"errors": [dict(entry, detail="HTTP 429(재전송 3회 뒤)")]}))
        self.assertFalse(batch_run.rate_limited({"errors": [dict(entry, detail="HTTP 4290")]}))
        self.assertFalse(batch_run.rate_limited({"errors": [dict(entry, detail="HTTP 400")]}))
        self.assertFalse(batch_run.rate_limited({"errors": [dict(entry, code=cause_codes.CODE_ERROR)]}))


class NameCollisionTest(TempOutputs, unittest.TestCase):
    def test_two_batch_runners_at_once_never_share_a_run_id(self):
        results = {}
        cases = hf.dev20_cases(6)

        def go(key):
            results[key] = self.execute(hf.FakeRunner(self.clock), spec(cases=cases, seed=f"seed-{key}"))

        threads = [threading.Thread(target=go, args=(k,)) for k in ("a", "b")]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        ids = [results[k].run_id for k in "ab"] + [line["run_id"] for k in "ab" for line in results[k].lines]
        self.assertEqual(len(ids), 2 + 2 * 18)
        self.assertEqual(len(set(ids)), len(ids))
        self.assertEqual(sorted(p.name for p in self.parent.iterdir()), sorted(ids))
        self.assertTrue(all(line["execution_status"] == "COMPLETED" for k in "ab" for line in results[k].lines))

    def test_name_taken_in_the_sealed_parent_moves_to_the_next_second(self):
        self.sealed.mkdir(parents=True)
        (self.sealed / "run_case-260925100000").mkdir()
        (self.sealed / "run_case-260925100001").mkdir()
        result = self.execute(hf.FakeRunner(self.clock), spec(cases=hf.dev20_cases(1), modes=["full"]))
        self.assertEqual(result.run_id, "evaluate-260925100000")
        self.assertEqual(result.lines[0]["run_id"], "run_case-260925100002")
        self.assertFalse((self.parent / "run_case-260925100000").exists())
        self.assertEqual(sorted(p.name for p in self.sealed.iterdir()),
                         ["run_case-260925100000", "run_case-260925100001"])  # 봉인 부모는 건드리지 않는다


class RefusalAndInterruptTest(TempOutputs, unittest.TestCase):
    def test_sealed_datasets_and_bad_specs_are_refused_before_any_folder(self):
        bad = [spec(dataset="holdout40"), spec(dataset="real_sealed"), spec(dataset="dev21"),
               spec(versions={**hf.VERSIONS, "code_version": ""}), spec(versions={"policy_version": "dev-0.1"}),
               spec(cases=[{"case_id": "a", "hs6": "850450", "partner": "CN"}]), spec(modes=["full", "fast"])]
        for s in bad:
            with self.subTest(s=s), self.assertRaises(batch_run.BatchError):
                self.execute(hf.FakeRunner(self.clock), s)
        for place in (self.sealed, self.parent / "Sealed", self.sealed / "holdout40"):
            with self.subTest(place=place), self.assertRaises(batch_run.BatchError):  # 봉인 자리에는 쓰지 않는다
                batch_run.execute_batch(spec(), hf.FakeRunner(self.clock), parent=place, other_parent=self.parent,
                                        clock=self.clock, sleep=self.clock.sleep)
        self.assertFalse(self.parent.exists())

    def test_interrupt_keeps_finished_lines(self):
        cases = hf.dev20_cases(3)
        order = batch_run.plan_order([c["case_id"] for c in cases], ["full"], "dev-order-v1")
        runner = hf.FakeRunner(self.clock, {order[2][0]: "interrupt"})
        with self.assertRaises(KeyboardInterrupt):
            self.execute(runner, spec(cases=cases, modes=["full"]))
        batch = self.parent / "evaluate-260925100000"
        lines = hf.read_jsonl(batch / "evaluation_batch_run-260925100000.jsonl")
        self.assertEqual([(x["case_id"], x["mode"]) for x in lines], order[:2])


class ReservedBatchDirTest(TempOutputs, unittest.TestCase):
    """사용자 결정 10(나): 호스트가 확보한 묶음 실행 폴더(--run-name)를 받으면 다시 확보하지 않고 그 폴더에 쓴다."""

    def reserve(self, name="evaluate-260925100000"):
        folder = self.parent / name
        folder.mkdir(parents=True)
        return name, name.rsplit("-", 1)[1], folder

    def test_reserved_folder_is_used_as_is(self):
        reserved = self.reserve()
        result = batch_run.execute_batch(spec(hf.dev20_cases(2)), hf.FakeRunner(self.clock), parent=self.parent,
                                         other_parent=self.sealed, clock=self.clock, sleep=self.clock.sleep,
                                         reserved=reserved)
        self.assertEqual((result.run_id, result.stamp, result.run_dir), reserved)
        self.assertEqual(len(hf.read_jsonl(result.batch_file)), 6)
        self.assertEqual(sorted(p.name for p in self.parent.iterdir() if p.name.startswith("evaluate-")),
                         ["evaluate-260925100000"])  # 묶음 폴더를 하나 더 만들지 않는다

    def test_bad_reserved_folders_are_refused_before_any_case(self):
        good = self.reserve()
        (self.parent / "other").mkdir()
        nonempty = self.reserve("evaluate-260925100001")
        (nonempty[2] / "x").write_text("x")
        for reserved in ((good[0], "260925100009", good[2]), ("run_case-260925100000", "260925100000", good[2]),
                         (good[0], good[1], self.parent / "other"), nonempty, (good[0], good[1]),
                         (good[0] + "\n", good[1], good[2])):
            with self.subTest(reserved=reserved), self.assertRaises(batch_run.BatchError):
                batch_run.execute_batch(spec(hf.dev20_cases(1)), hf.FakeRunner(self.clock), parent=self.parent,
                                        other_parent=self.sealed, clock=self.clock, sleep=self.clock.sleep,
                                        reserved=reserved)
        self.assertEqual(sorted(p.name for p in self.parent.iterdir()),
                         ["evaluate-260925100000", "evaluate-260925100001", "other"])  # 사례 폴더를 만들지 않았다


class RunConditionsTest(unittest.TestCase):
    """실행 조건 입력 파일이 채점기 DT8 임시 형식(1회차 보고 §5, eval/scorer/__main__.py read_conditions)과 맞는다."""

    # 채점기 임시 형식의 키 집합(DT8 1회차 보고 §5 "필수 키"·"선택 키"·"요약에 옮기는 키")을 글자 그대로 옮겼다.
    DT8_KEYS = {"dataset", "planned_cases", "planned_modes", "snapshot", "policy_detection_thresholds", "rulebook",
                "grouping_reason", "scorer_commit", "prose_patterns_commit", "run_period", "concurrency",
                "order_seed", "limits", "sandbox", "sealed_hash_recheck", "sealed_provenance_check", "precheck",
                "prescoring_checks", "skill_call_success", "nat_profile_summary", "korean_sample_review",
                "reproduce_evaluate", "a_grade"}
    DT8_LIMIT_KEYS = {"tool_attempts", "reinvestigation", "model_requests", "wall_time_s", "tokens"}

    def setUp(self):
        super().setUp()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.parent = Path(tmp.name) / "outputs"
        self.run_dir = self.parent / "evaluate-260925100000"
        self.run_dir.mkdir(parents=True)

    def doc(self, **over):
        limits = batch_run.limits_from_run_limits({"model_requests": 10, "tokens": 32000, "wall_ms": 300000,
                                                   "tool_attempts": 8, "revision_stages": 1})
        kw = dict(dataset="dev20", cases=hf.dev20_cases(), modes=list(hf.DEV20_MODES),
                  thresholds=[30, Decimal("10.5")], order_seed="dev-order-v1", limits=limits,
                  run_period=(hf.BASE, hf.BASE), nat_profile_summary={"runs": 60})
        kw.update(over)
        return batch_run.build_run_conditions(**kw)

    def test_written_file_matches_dt8_provisional_format(self):
        path = batch_run.write_run_conditions(self.run_dir, self.doc())
        self.assertEqual(path.name, "run_conditions-260925100000.json")
        doc = json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)
        self.assertTrue(set(doc) <= self.DT8_KEYS)
        self.assertEqual(set(batch_run.CONDITION_KEYS), self.DT8_KEYS)
        self.assertEqual(doc["dataset"], "dev20")
        self.assertEqual(doc["planned_modes"], ["checklist", "agent", "full"])
        self.assertTrue(all(set(c) == {"case_id", "hs6", "partner", "month"} for c in doc["planned_cases"]))
        self.assertEqual(len(doc["planned_cases"]), 20)
        self.assertEqual(doc["policy_detection_thresholds"], [30, Decimal("10.5")])  # JSON 수(문자열 아님)
        self.assertEqual(set(doc["limits"]), self.DT8_LIMIT_KEYS)
        self.assertEqual(doc["limits"], {"tool_attempts": 8, "reinvestigation": 1, "model_requests": 10,
                                         "wall_time_s": 300, "tokens": 32000})
        self.assertIs(type(doc["concurrency"]), int)
        self.assertEqual(doc["concurrency"], 1)
        self.assertEqual(doc["run_period"], {"start": "2026-09-25T10:00:00+09:00", "end": "2026-09-25T10:00:00+09:00"})
        with self.assertRaises(FileExistsError):  # 배타 생성
            batch_run.write_run_conditions(self.run_dir, self.doc())

    def test_sealed_rules(self):
        with self.assertRaises(batch_run.BatchError):  # 봉인 묶음에 봉인 출력 값
            self.doc(dataset="holdout40")
        sealed_doc = self.doc(dataset="holdout40", nat_profile_summary=None)
        with self.assertRaises(batch_run.BatchError):  # 봉인 묶음을 outputs/ 아래에
            batch_run.write_run_conditions(self.run_dir, sealed_doc)
        sealed_dir = self.parent / "sealed" / "evaluate-260925100000"
        sealed_dir.mkdir(parents=True)
        batch_run.write_run_conditions(sealed_dir, sealed_doc)
        with self.assertRaises(batch_run.BatchError):  # 개발 묶음을 outputs/sealed/ 아래에
            batch_run.write_run_conditions(self.parent / "sealed" / "evaluate-260925100001", self.doc())

    def test_sealed_place_through_symlink_or_case_variant(self):
        sealed = self.parent / "sealed"
        sealed.mkdir()
        alias = self.parent / "alias"
        alias.symlink_to(sealed, target_is_directory=True)
        (alias / "evaluate-260925100002").mkdir()
        with self.assertRaises(batch_run.BatchError):  # 개발 묶음을 심볼릭 링크로 봉인 자리에 쓰지 않는다
            batch_run.write_run_conditions(alias / "evaluate-260925100002", self.doc())
        self.assertTrue(batch_run.sealed_place(self.parent / "SEALED" / "evaluate-260925100000"))

    def test_planned_modes_table_matches_eval_skill_matrix(self):
        """평가 스킬 ② 실행 행렬(자료 묶음 × 모드)을 문서에서 읽어 E1 표와 대조한다(사용자 결정 12의 기본 모드 집합)."""
        text = (hf.ROOT / "skills" / "tradesentry-eval" / "SKILL.md").read_text(encoding="utf-8")
        table = text.split("### 실행 행렬", 1)[1].split("###", 1)[0]
        rows = {}
        for line in table.splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == 4 and cells[0].startswith("`"):
                rows[cells[0].strip("`")] = tuple(m.strip(" `") for m in cells[2].split(","))
        self.assertEqual(set(rows), {"dev20", "real_dev", "holdout40", "real_sealed"})
        for dataset, modes in rows.items():
            self.assertEqual(batch_run.PLANNED_MODES[dataset], modes)
        self.assertEqual(batch_run.PLANNED_MODES["controlled_fixture_v0"], ("checklist", "agent", "full", "freeform"))

    def test_bad_values_are_refused(self):
        home_path = "~" + "/x"
        bad = [dict(thresholds=[30.0]), dict(thresholds=["30"]), dict(thresholds=[]), dict(thresholds=[True]),
               dict(extra={"unknown_key": 1}), dict(extra={"scorer_commit": "/" + "Users/x"}),
               dict(extra={"grouping_reason": home_path}), dict(extra={"precheck": "C:\\x"}),
               dict(extra={"precheck": "nv" + "api-abc"}), dict(extra={"precheck": "//" + "srv/x"}),
               dict(extra={"precheck": "file:" + "///x"}), dict(extra={"precheck": "`" + "/x`"}), dict(concurrency=True), dict(modes=["full", "full"]),
               dict(cases=[{**hf.dev20_cases(1)[0], "partner": "ALL"}]), dict(extra={"dataset": "dev20"})]
        for over in bad:
            with self.subTest(over=over), self.assertRaises(batch_run.BatchError):
                self.doc(**over)
        self.assertEqual(self.doc(extra={"grouping_reason": "합성 peer_group", "scorer_commit": "abc1234"})
                         ["grouping_reason"], "합성 peer_group")

    def test_limits_from_model_config(self):
        from tradesentry.workflow import model_client  # 실제 설정 파일(configs/model/model.json)의 한도

        limits = batch_run.limits_from_run_limits(model_client.load_model_config().limits)
        # 누적 토큰 한도는 2026-09-25(금) 사용자 결정 4로 128,000(결정 기록 20260925-0847, AS2 #38이 설정에 반영)
        self.assertEqual(limits, {"tool_attempts": 8, "reinvestigation": 1, "model_requests": 10, "wall_time_s": 300,
                                  "tokens": 128000})


if __name__ == "__main__":
    unittest.main()
