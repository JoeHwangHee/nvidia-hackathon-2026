"""단위 I7(workflow_model_client) 골든 시험. 규칙은 tests/units/golden.py에 있다.

전송 자리(UrllibTransport)와 시계·대기(_default_clock_ms·_default_sleep_ms)를 가짜로 바꾼다(가짜 클라이언트 주입).
골든 입력은 HTTP 503 두 번 뒤 200을 받는 요청 하나다(재전송 2회, 대기 5초·10초. model-1.4에서 대기 기준값이 1초에서 5초로 바뀌어 기대값을 고쳤다).
model-1.5(2026-09-25 18:05 사용자 결정)부터 재전송은 모델 요청 수에 세지 않아 budget.model_requests 기대값이 3에서 1이다.
"""
import unittest
from unittest import mock

from ..golden import GoldenMixin
from .fakes import FakeClock, ScriptedTransport, ok_body

CONTENT = '{"review_status": "MONITOR"}'


class GoldenTest(GoldenMixin, unittest.TestCase):
    UNIT_ID = "I7"

    def setUp(self):
        super().setUp()
        clock = FakeClock()
        script = [{"status": 503}, {"status": 503}, {"body": ok_body(CONTENT, prompt_tokens=812, completion_tokens=96)}]
        transport = ScriptedTransport(script, clock)
        for target, value in (("UrllibTransport", lambda endpoint, env: transport),
                              ("_default_clock_ms", clock.clock_ms), ("_default_sleep_ms", clock.sleep_ms)):
            patcher = mock.patch(f"tradesentry.workflow.model_client.{target}", value)
            patcher.start()
            self.addCleanup(patcher.stop)
