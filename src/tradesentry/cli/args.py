"""단위 F1 인자 검증.

단위 ID: F1
도메인명: cli_args
소유: M
입력: 문자열 인자
출력: 검증된 요청(모드 4개·스냅샷 ID·사례·정책 버전)
허용 import: 표준 라이브러리, tradesentry.contract

S0 뼈대다. 진입 함수 run의 몸통은 아직 NotImplementedError다. 정본: docs/plan/UNITS.md §3.8.
S0는 명령 5개와 공통 옵션(--snapshot, --policy, --mode)의 틀만 만든다(build_parser). 모드는 4개 값만 받는다.
스냅샷 ID·정책 버전 이름·사례 인자의 형식 검증과, 명령마다 어떤 옵션이 꼭 있어야 하는지는 run이 맡고 로드맵
MT5가 정한다(사례 인자 형식은 자문 명세서 Q18). --policy는 파일 경로가 아니라 버전 이름(예: policy_v1)이다.
"""
import argparse

# 계약 상수 사본: 자료 계약 docs/rules/DATA_CONTRACT_V1.md §4.1의 모드 4개.
# 조립 때 단위 K1(tradesentry.contract.types)에서 import하게 바꾼다(docs/plan/UNITS.md §6 조립 부산물 4).
MODES = ("checklist", "agent", "full", "freeform")

# 명령과 도움말(자료 계약 §10 계획 경로·명령 표). 명령의 실행 이름은 하이픈을 밑줄로 바꾼 것이다(§10.3 N5).
COMMANDS = {
    "snapshot-build": "raw 응답·manifest에서 파생 SQLite 스냅샷을 만든다(조립체 1)",
    "snapshot-verify": "스냅샷을 검증한다(조립체 1)",
    "detect": "동결 정책으로 경보 사례 목록을 만든다(조립체 2)",
    "run-case": "사례 1건을 조사한다(조립체 3)",
    "evaluate": "자료 묶음의 사례를 모드별로 실행하고 실행 쪽 키를 기록한다(조립체 4)",
}


def build_parser() -> argparse.ArgumentParser:
    """tradesentry 명령의 인자 틀. 도움말(-h, --help)은 종료 코드 0으로 끝난다.

    옵션 줄임(예: --snap)은 받지 않는다(allow_abbrev=False). 시연 경로에서는 하네스 모델이 명령을 조립하므로 적힌
    그대로의 옵션 이름만 받는다. 같은 옵션을 되풀이해 적은 경우의 거부와 값 형식 검증은 run(MT5)이 맡는다.
    """
    parser = argparse.ArgumentParser(
        prog="tradesentry",
        description="TradeSentry CLI(명령줄 실행 도구). 관세청 수입통계 경보를 조사해 담당자의 다음 업무를 제안한다. "
                    "부정·위법·원산지 판정이나 통관 조치가 아니다.",
        allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", metavar="<명령>", required=True)
    common = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    common.add_argument("--snapshot", metavar="SNAPSHOT_ID", help="스냅샷 ID(예: kcs_202201_202412_v2)")
    common.add_argument("--policy", metavar="POLICY_VERSION", help="정책 버전 이름(예: policy_v1). 파일 경로가 아니다")
    common.add_argument("--mode", choices=MODES, help="실행 모드. " + ", ".join(MODES) + " 가운데 하나")
    for name, help_text in COMMANDS.items():
        commands.add_parser(name, parents=[common], help=help_text, description=help_text, allow_abbrev=False)
    return parser


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    raise NotImplementedError("단위 F1(cli_args)의 run은 아직 구현하지 않았다")
