"""단위 I12(workflow_orchestrate) 누적 토큰 추정 시험: 모델용 봉투 보기가 실자료 크기의 봉투에서 사례 누적 토큰(32,000,
공용 약속 한도라 바꾸지 않는다)을 얼마나 쓰는지 합성 봉투로 잰다.

- 봉투: sized_envelopes.py(실자료 850450-JP 크기에 맞춘 합성, HS10 하위품목 8개).
- 토큰: 요청 본문(메시지 + 도구 명세)의 글자로 추정한다. ASCII는 3자, 그 밖(한국어)은 1.3자를 토큰 하나로 본다
  (MT2 평가 검토의 가운데 가정). 실제 토크나이저가 아니므로 정확한 값이 아니다 `[추론]`. 실측 스모크가 정답이다.
- 흐름: 실제 흐름 조정 코드(단위 I12)를 돌리고, 모델 답만 대본이다(도구 호출 60·초안 1,200·Critic 답 400 출력 토큰).
- 모델용 보기(단위 I10 compact_envelope)는 모든 모드가 같고, Critic 보기(단위 I11 evidence_view)는 full·freeform이 같다.
  봉투의 근거 ID와 metric_id는 하나도 잃지 않는다.
- 2026-09-25(금) 새벽 잰 값(봉투 39,435자 → 조사자 보기 24,108자, Critic 보기 17,544자): full 비교국 1회 + Critic 약
  17,500, agent 비교 2회 약 23,100, full 비교 2회 + Critic 약 31,200(1회차 보기로는 약 45,900으로 넘음), full 비교 없이
  Critic + 수정 약 15,800은 한도 안이다. 비교 뒤 수정 단계가 붙는 경로(약 33,100~42,600)는 넘는다. 이 남은 위험은
  결정 기록(MT4 조사 흐름 기록 ⑮)에 적었고, 한도(공용 약속)를 바꾸지 않는 한 모든 모드에 같게 걸린다.
- 3회차(도구를 주지 않는 조사자 요청에 초안 요청 메시지를 붙인 뒤) 다시 잰 값: agent 비교 2회 약 23,300, full 비교
  2회 + Critic 약 31,400(여유 약 2%). 비교 1회 경로(약 17,500)는 도구를 주지 않는 요청이 없어 같다(결정 기록 ⑯).
"""
import json
import math
import unittest

from tradesentry.runlog import trace as trace_log
from tradesentry.workflow import critic, investigator
from tradesentry.workflow import model_client as mc
from tradesentry.workflow import orchestrate

from ..I7.fakes import FakeClock, ok_body
from . import harness as h
from . import sized_envelopes as se

ASCII_PER_TOKEN, OTHER_PER_TOKEN = 3, 1.3
LIMIT = 32_000


def estimate(payload: dict) -> int:
    text = trace_log.dumps({"messages": payload["messages"], "tools": payload.get("tools")})
    ascii_chars = sum(1 for ch in text if ord(ch) < 128)
    return math.ceil(ascii_chars / ASCII_PER_TOKEN + (len(text) - ascii_chars) / OTHER_PER_TOKEN)


class EstimatingTransport:
    """대본 답을 돌려주되 prompt_tokens는 보낸 요청 본문으로 추정한다(대본 답 = (content, tool_calls, 출력 토큰))."""

    def __init__(self, answers, clock):
        self.answers = list(answers)
        self.clock = clock
        self.prompts = []

    def send(self, payload, timeout_ms):
        content, calls, completion = self.answers.pop(0)
        prompt = estimate(payload)
        self.prompts.append(prompt)
        self.clock.now += 1000
        return {"http_status": 200, "body": ok_body(content, tool_calls=calls, prompt_tokens=prompt,
                                                    completion_tokens=completion), "error": None, "elapsed_ms": 1000}


def calls(*names):
    return [{"id": f"c{i}", "type": "function", "function": {"name": n, "arguments": "{}"}} for i, n in enumerate(names)]


DRAFT = json.dumps(h.draft(), ensure_ascii=False)
CRITIC_OK = '{"findings": [], "requery": [], "needs_revision": false}'


def run_path(mode, answers, checks):
    envelopes = se.all_envelopes()
    fake = h.FakePorts(checks=checks)
    fake.tool = lambda name, args: envelopes[name]
    clock = FakeClock()
    transport = EstimatingTransport(answers, clock)
    ctx = orchestrate.RunContext(run_id=h.RUN_ID, case=h.CASE_A, mode=mode, dataset="controlled_fixture_v0",
                                 rulebook_version="RB-1", grouping_version="g0", code_version="abc1234")
    result = orchestrate.orchestrate(ctx, fake.ports(), mc.load_model_config(), transport=transport,
                                     sink=trace_log.NullSink(), clock_ms=clock.clock_ms, sleep_ms=clock.sleep_ms)
    record = result["record"]
    return record, record["tokens_in"] + record["tokens_out"]


class ModelViewTest(unittest.TestCase):
    def test_view_keeps_every_evidence_id_and_metric_id(self):
        for name, envelope in se.all_envelopes().items():
            view = investigator.compact_envelope(envelope)
            with self.subTest(tool=name):
                ids = investigator._evidence_ids_in(view, set())
                self.assertEqual(ids, investigator._evidence_ids_in(envelope, set()))
                self.assertEqual(investigator._evidence_ids_in(critic.evidence_view(envelope), set()), ids)
                self.assertEqual([m["metric_id"] for m in view.get("metrics", [])],
                                 [m["metric_id"] for m in envelope["metrics"]])
                for kept, original in zip(view.get("metrics", []), envelope["metrics"]):
                    self.assertEqual((kept["metric"], kept["value"], kept["unit"], kept["evidence_ids"]),
                                     (original["inputs"]["metric"], original["value"], original["unit"],
                                      original["evidence_ids"]))
                self.assertEqual(view["tool"], envelope["tool"])
                self.assertEqual(view.get("comparability", {}), envelope["comparability"])

    def test_view_is_much_smaller_than_the_envelope(self):
        envelopes = se.all_envelopes()
        full = sum(len(trace_log.dumps(e)) for e in envelopes.values())
        view = sum(len(trace_log.dumps(investigator.compact_envelope(e))) for e in envelopes.values())
        self.assertGreater(full, 35_000)  # 실자료 크기(기본 경로 약 38,000자)에 가까운 합성이다
        self.assertLess(view / full, 0.65)
        decompose = se.decompose_hs()
        self.assertLess(len(trace_log.dumps(investigator.compact_envelope(decompose))) / len(trace_log.dumps(decompose)),
                        0.6)


class CumulativeTokenTest(unittest.TestCase):
    """경로별 누적 토큰 추정. 한도 안에 드는 경로는 단언하고, 넘는 경로는 넘는다는 것을 고정한다(남은 위험이 바뀌면 이
    시험과 결정 기록을 함께 고친다)."""

    def test_paths_without_the_large_decomposition_fit_under_the_limit(self):
        # 추가 비교 1(비교국), Critic, 수정 없음: full·freeform
        record, total = run_path("full", [(None, calls("compare_partners"), 60), (DRAFT, None, 1200),
                                          (CRITIC_OK, None, 400)], [h.PASS, h.PASS])
        self.assertEqual(record["execution_status"], "COMPLETED")
        self.assertLess(total, LIMIT)
        # agent: 추가 비교 2(비교국·분해), 수정 없음(Critic 없음)
        record, total = run_path("agent", [(None, calls("compare_partners"), 60), (None, calls("decompose_hs"), 60),
                                           (DRAFT, None, 1200)], [h.PASS, h.PASS])
        self.assertEqual(record["execution_status"], "COMPLETED")
        self.assertLess(total, LIMIT)

    def test_directed_single_turn_comparison_path_has_room(self):
        """AS2 2회차(model-0.3): 지침이 비교국·분해를 한 차례에 함께 부르게 한다. 그 경로(full, Critic, 수정 없음)는 두
        차례로 나눠 부르는 경로보다 조사자 요청이 하나 적어 한도 아래 여유가 크다(나눠 부르는 경로는 한도에 거의 닿는다)."""
        record, one_turn = run_path("full", [(None, calls("compare_partners", "decompose_hs"), 60), (DRAFT, None, 1200),
                                             (CRITIC_OK, None, 400)], [h.PASS, h.PASS])
        self.assertEqual(record["execution_status"], "COMPLETED")
        self.assertLess(one_turn, LIMIT * 85 // 100)
        _, two_turns = run_path("full", [(None, calls("compare_partners"), 60), (None, calls("decompose_hs"), 60),
                                         (DRAFT, None, 1200), (CRITIC_OK, None, 400)], [h.PASS, h.PASS])
        self.assertLess(one_turn, two_turns)

    def test_decomposition_path_with_critic_fits_but_a_revision_after_it_does_not(self):
        # full: 추가 비교 2(비교국·분해), Critic, 수정 없음 → 한도 안
        record, total = run_path("full", [(None, calls("compare_partners"), 60), (None, calls("decompose_hs"), 60),
                                          (DRAFT, None, 1200), (CRITIC_OK, None, 400)], [h.PASS, h.PASS])
        self.assertEqual(record["execution_status"], "COMPLETED")
        self.assertLess(total, LIMIT)
        # 같은 경로에 검증기 차단으로 수정 단계(재조회 1)가 붙으면 한도를 넘는다(모든 모드에 같은 한도, 남은 위험)
        record, total = run_path("full", [(None, calls("compare_partners"), 60), (None, calls("decompose_hs"), 60),
                                          (DRAFT, None, 1200), (CRITIC_OK, None, 400),
                                          (None, calls("check_comparability"), 60), (DRAFT, None, 1200)],
                                 [h.PASS, h.BLOCK, h.PASS])
        self.assertEqual((record["execution_status"], record["errors"][0]["code"]), ("BUDGET_EXCEEDED", "BUDGET_TOKENS"))


if __name__ == "__main__":
    unittest.main()
