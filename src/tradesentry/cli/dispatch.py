"""단위 F2 명령 배선.

단위 ID: F2
도메인명: cli_dispatch
소유: M
입력: 명령
출력: 조립체 1~4 호출
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.cli, tradesentry.snapshot, tradesentry.dal, tradesentry.metrics, tradesentry.policy, tradesentry.grouping, tradesentry.tools, tradesentry.workflow, tradesentry.reports, tradesentry.validator, tradesentry.runlog, tradesentry.evaluation.batch_run, tradesentry.evaluation.extract, tradesentry.evaluation.nat_eval

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.8.
main은 설치 명령 tradesentry의 진입점이다(pyproject.toml [project.scripts]). 인자를 읽은 뒤 명령마다 처리 함수 표
HANDLERS의 함수를 부르고 그 종료 코드를 돌려준다. 처리 함수가 NotImplementedError를 내면 분명한 오류 문장과 종료
코드 3으로 끝난다. S0에서는 모든 명령의 처리 함수가 아직 잇지 않은 함수(_not_wired)이고, 명령마다 잇는 일은
ASSEMBLIES의 작업이 이 표의 그 명령 항목만 바꿔서 한다.
종료 코드: 0 도움말, 2 인자 오류(argparse), 3 구현되지 않은 명령, 그 밖은 처리 함수가 돌려준 값.
평가 하네스는 모듈 단위로만 허용한다. 호스트 전용 샌드박스 밖 실행기(단위 E2, tradesentry.evaluation.sealed_runner)는
CLI가 부르지 않는다.
"""
import argparse
import sys
from typing import Callable

from tradesentry.cli import args

EXIT_NOT_IMPLEMENTED = 3

# 명령 → 부를 조립체와 잇는 작업(docs/plan/UNITS.md §4 조립체 표).
ASSEMBLIES = {
    "snapshot-build": "조립체 1(스냅샷 빌드·검증). 로드맵 DT1·DT7이 잇는다",
    "snapshot-verify": "조립체 1(스냅샷 빌드·검증). 로드맵 DT1이 잇는다",
    "detect": "조립체 2(탐지). 조립 작업 AS1이 잇는다",
    "run-case": "조립체 3(사례 조사). 조립 작업 AS2가 잇는다",
    "evaluate": "조립체 4(평가 실행). 조립 작업 AS3이 잇는다",
}


def _not_wired(namespace: argparse.Namespace) -> int:
    """아직 조립체와 잇지 않은 명령의 처리 함수."""
    raise NotImplementedError(f"tradesentry {namespace.command}는 아직 조립체와 잇지 않았다")


# 명령 → 처리 함수(파싱한 인자를 받아 종료 코드를 돌려준다). 조립 작업이 명령마다 이 표의 항목을 바꾼다.
HANDLERS: dict[str, Callable[[argparse.Namespace], int]] = {name: _not_wired for name in args.COMMANDS}


def main(argv: list[str] | None = None) -> int:
    """tradesentry <명령> 진입점. 종료 코드를 돌려준다."""
    namespace = args.build_parser().parse_args(argv)
    try:
        return HANDLERS[namespace.command](namespace)
    except NotImplementedError:
        print(f"오류: tradesentry {namespace.command}는 아직 구현되지 않았다. {ASSEMBLIES[namespace.command]}.",
              file=sys.stderr)
        return EXIT_NOT_IMPLEMENTED


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 F2(cli_dispatch)의 run은 아직 구현하지 않았다")
