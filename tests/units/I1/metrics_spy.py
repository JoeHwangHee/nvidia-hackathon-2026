"""지표 단위 X1(unit_value)·X2(share)·X3(decompose)의 run을 감싸 호출만 기록한다(시험 도우미).

계산은 진짜 지표 단위가 한다(unittest.mock.patch.object(…, wraps=진짜 run)). 도구 시험은 대역(가짜 계산)을 쓰지 않는다.
지표 단위가 main에 병합돼 있기 때문이다(구현 공통 규칙: 대역은 아직 없는 단위에만 쓴다).
- spy_metrics(test)는 세 단위의 run을 감싼 Spy를 돌려준다. Spy.calls는 부른 순서대로 (단위 이름, 입력)의 목록이다.
- fix_clock(test)는 도구 공통 틀의 시계를 고정한다(elapsed_ms = 0, 골든 비교가 결정적이게).
"""
from unittest import mock

from tradesentry.metrics import decompose, share, unit_value

UNITS = (("X1", unit_value), ("X2", share), ("X3", decompose))


class Spy:
    def __init__(self, manager: mock.MagicMock) -> None:
        self._manager = manager

    @property
    def calls(self) -> list[tuple[str, dict]]:
        return [(call[0], call[1][0]) for call in self._manager.mock_calls]


def spy_metrics(test) -> Spy:
    """시험 setUp에서 부른다: 지표 단위 X1·X2·X3의 run을 진짜 run으로 감싸(wraps) 호출을 기록한다."""
    manager = mock.MagicMock()
    for name, module in UNITS:
        patcher = mock.patch.object(module, "run", wraps=module.run)
        manager.attach_mock(patcher.start(), name)
        test.addCleanup(patcher.stop)
    return Spy(manager)


def fix_clock(test, value: int = 0) -> None:
    """도구 공통 틀의 시계를 고정한다(elapsed_ms = 0)."""
    patcher = mock.patch("tradesentry.tools.check_comparability.clock_ms", return_value=value)
    patcher.start()
    test.addCleanup(patcher.stop)
