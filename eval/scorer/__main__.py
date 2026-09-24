"""독립 채점기 명령 자리: python -m eval.scorer --run <run_dir> (저장소 루트에서, 샌드박스 밖에서 실행).

S0 뼈대라 아직 채점하지 않고, 분명한 오류 문장과 종료 코드 3으로 끝난다. 구현은 로드맵 DT8이 한다.
구현할 때 지킬 것(자료 계약 docs/rules/DATA_CONTRACT_V1.md §10.3): 출력은 outputs/score-{시각}/에 쓰고, 그 실행명은
N8대로 이 채점기가 직접 확보한다. tradesentry 패키지 전부(등록부·커널 포함)와 eval.datagen을 직접이든 간접이든
import하지 않는다(tests/test_boundaries.py가 본다).
- 봉인 묶음 채점 때 확보한 실행 폴더 이름을 표준 출력 첫 줄로 알리고, 표준 출력·오류 출력에는 그 이름과 끝 상태만
  낸다(자료 계약 §10.3 N10).
- 종료 코드 0은 출력을 끝까지 썼을 때만 낸다.
"""
import argparse
import sys

EXIT_NOT_IMPLEMENTED = 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m eval.scorer",
                                     description="독립 채점기(샌드박스 밖 정답 대조 채점). 출력은 outputs/score-{시각}/")
    parser.add_argument("--run", dest="run_dir", required=True, metavar="RUN_DIR",
                        help="채점할 실행 폴더(outputs/{실행명}/, 봉인 묶음이면 outputs/sealed/{실행명}/)")
    parser.parse_args(argv)
    print("오류: 독립 채점기는 아직 구현되지 않았다. 로드맵 DT8이 구현한다.", file=sys.stderr)
    return EXIT_NOT_IMPLEMENTED


if __name__ == "__main__":
    raise SystemExit(main())
