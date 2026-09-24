"""단위 F2 명령 배선.

단위 ID: F2
도메인명: cli_dispatch
소유: M
입력: 명령
출력: 조립체 1~4 호출
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.cli, tradesentry.snapshot, tradesentry.dal, tradesentry.metrics, tradesentry.policy, tradesentry.grouping, tradesentry.tools, tradesentry.workflow, tradesentry.reports, tradesentry.validator, tradesentry.runlog, tradesentry.evaluation

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.8.
main은 설치 명령 tradesentry의 진입점이다(pyproject.toml [project.scripts]). S0에서는 인자를 읽은 뒤 어느 명령도
조립체를 부르지 않고, 분명한 오류 문장과 종료 코드 3으로 끝난다. 명령마다 잇는 일은 ASSEMBLIES의 작업이 한다.
종료 코드: 0 도움말, 2 인자 오류(argparse), 3 구현되지 않은 명령.
"""
import sys

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


def main(argv: list[str] | None = None) -> int:
    """tradesentry <명령> 진입점. 종료 코드를 돌려준다."""
    namespace = args.build_parser().parse_args(argv)
    print(f"오류: tradesentry {namespace.command}는 아직 구현되지 않았다. {ASSEMBLIES[namespace.command]}.",
          file=sys.stderr)
    return EXIT_NOT_IMPLEMENTED


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 F2(cli_dispatch)의 run은 아직 구현하지 않았다")
