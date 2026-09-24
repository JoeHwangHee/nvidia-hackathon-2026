"""공통 실행기: 등록부의 단위 하나를 혼자 돌리는 개발 전용 명령.

실행(저장소 루트에서): python -m tradesentry.units <단위 ID> --in <입력 파일>

이름·출력 규칙(자료 계약 docs/rules/DATA_CONTRACT_V1.md §10.3)
- 실행 이름은 그 단위의 도메인명이고, 실행명(run_id)은 {도메인명}-{yymmddhhmmss}다(N5).
- 출력은 outputs/{실행명}/{도메인명}-{시각}.{확장자} 하나다(N6). 시각은 실행을 시작한 KST(한국 표준시, UTC+9)
  24시간 12자리이고, 실행 폴더와 출력 파일이 같은 시각을 쓴다.
- 실행명 확보(N8): 단위를 부르기 전에 outputs/{실행명}/을 이미 있으면 실패하는 방식(os.mkdir, exist_ok 없음)으로
  만든다. 그 호출이 성공한 실행만 그 실행명을 쓴다. 이름의 초가 될 때까지 기다린 뒤 만들므로 시각이 실제 시작
  시각보다 앞서지 않는다. 만든 뒤 다른 부모 폴더(outputs/sealed/)에 같은 이름이 있으면 방금 만든 빈 폴더를 지우고
  다음 초로 넘어간다. 만들기에 실패해도 다음 초로 넘어간다. 시각은 컴퓨터 시간대와 관계없이 KST로 만든다.
- 덮어쓰기 금지: 출력 파일은 이미 있으면 실패하는 방식(open 모드 "xb")으로 쓴다.
- 로컬 절대경로를 출력하지 않는다(N13). 경로는 outputs/부터 적는다.

입력과 출력 값
- 입력 파일은 JSON 문서 하나다. 비었거나 공백뿐이면(예: 빈 파일, /dev/null) 입력 없음(None)으로 넘긴다.
  소수는 Decimal(반올림 오차 없는 십진 소수)로 읽는다.
- 출력 값은 등록부의 확장자를 따른다. json이면 JSON 값, jsonl이면 목록(원소 하나가 한 줄), md·txt·csv·yaml이면
  문자열, sqlite면 바이트다. Decimal은 글자 그대로의 문자열로 쓴다.

종료 코드
- 0: 성공. 2: 인자·입력 오류(실행명을 확보하기 전에 끝난다). 3: run이 아직 구현되지 않음(NotImplementedError).
- 4: 출력 규칙 위반(실행명을 확보하지 못함, 쓰려는 파일이 이미 있음, 확장자와 맞지 않는 값).

CLI·런타임 스킬·샌드박스 정책에서 부르지 않는다(docs/plan/UNITS.md §6의 조립 부산물 1).
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Callable, TextIO

from tradesentry.units import registry

KST = timezone(timedelta(hours=9), "KST")
STAMP_FORMAT = "%y%m%d%H%M%S"
MAX_ATTEMPTS = 10

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_NOT_IMPLEMENTED = 3
EXIT_OUTPUT = 4

TEXT_EXTS = frozenset({"md", "txt", "csv", "yaml"})
BINARY_EXTS = frozenset({"sqlite"})
OUTPUT_EXTS = TEXT_EXTS | BINARY_EXTS | {"json", "jsonl"}

REPO_ROOT = Path(__file__).resolve().parents[3]


class RunNameError(Exception):
    """실행명을 확보하지 못했다."""


class OutputRuleError(Exception):
    """출력 규칙(덮어쓰기 금지, 확장자와 값의 짝)을 어겼다."""


def now_kst() -> datetime:
    """지금 시각(KST)."""
    return datetime.now(KST)


def _second(t: datetime) -> datetime:
    return t.astimezone(KST).replace(microsecond=0)


def _wait_until(target: datetime, clock: Callable[[], datetime], sleep: Callable[[float], None]) -> None:
    while True:
        remaining = (target - clock()).total_seconds()
        if remaining <= 0:
            return
        sleep(remaining)


def reserve_run_dir(parent: Path, other_parent: Path, run_name: str, *,
                    clock: Callable[[], datetime] = now_kst,
                    sleep: Callable[[float], None] = time.sleep,
                    max_attempts: int = MAX_ATTEMPTS) -> tuple[str, str, Path]:
    """실행명을 확보하고 (실행명, 시각, 실행 폴더)를 돌려준다(자료 계약 §10.3 N8).

    parent는 실행 폴더를 만들 부모 폴더(outputs/ 또는 outputs/sealed/), other_parent는 같은 이름이 없어야 하는
    다른 부모 폴더다. parent 자체는 없으면 만든다. 실행 폴더는 이미 있으면 실패하는 방식으로 만든다.
    """
    parent.mkdir(parents=True, exist_ok=True)
    target = _second(clock())
    for _ in range(max_attempts):
        _wait_until(target, clock, sleep)
        stamp = target.strftime(STAMP_FORMAT)
        run_id = f"{run_name}-{stamp}"
        run_dir = parent / run_id
        try:
            os.mkdir(run_dir)
        except FileExistsError:
            target = max(target + timedelta(seconds=1), _second(clock()))
            continue
        if (other_parent / run_id).exists():
            os.rmdir(run_dir)
            target = max(target + timedelta(seconds=1), _second(clock()))
            continue
        return run_id, stamp, run_dir
    raise RunNameError(f"{max_attempts}번 시도해도 실행명 {run_name}-{{시각}}을 확보하지 못했다")


def load_input(path: Path) -> object:
    """입력 파일을 읽는다. 비었거나 공백뿐이면 None이다. 소수는 Decimal로 읽는다."""
    text = path.read_bytes().decode("utf-8-sig")
    if not text.strip():
        return None
    return json.loads(text, parse_float=Decimal)


def _json_default(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"JSON으로 쓸 수 없는 값: {type(value).__name__}")


def write_output(run_dir: Path, domain: str, stamp: str, ext: str, value: object) -> Path:
    """출력 값을 {도메인명}-{시각}.{확장자}로 쓴다. 이미 있으면 쓰지 않고 OutputRuleError를 낸다."""
    try:
        if ext == "json":
            payload = (json.dumps(value, ensure_ascii=False, indent=2, default=_json_default) + "\n").encode("utf-8")
        elif ext == "jsonl":
            if not isinstance(value, (list, tuple)):
                raise OutputRuleError(f"jsonl 출력 값은 목록이어야 한다: {type(value).__name__}")
            payload = "".join(json.dumps(v, ensure_ascii=False, default=_json_default) + "\n"
                              for v in value).encode("utf-8")
        elif ext in TEXT_EXTS:
            if not isinstance(value, str):
                raise OutputRuleError(f"{ext} 출력 값은 문자열이어야 한다: {type(value).__name__}")
            payload = value.encode("utf-8")
        elif ext in BINARY_EXTS:
            if not isinstance(value, (bytes, bytearray)):
                raise OutputRuleError(f"{ext} 출력 값은 바이트여야 한다: {type(value).__name__}")
            payload = bytes(value)
        else:
            raise OutputRuleError(f"등록부에 없는 출력 확장자: {ext}")
    except (TypeError, ValueError) as exc:
        raise OutputRuleError(f"출력 값을 {ext}로 쓸 수 없다: {exc}") from exc
    target = run_dir / f"{domain}-{stamp}.{ext}"
    try:
        with open(target, "xb") as fh:
            fh.write(payload)
    except FileExistsError as exc:
        raise OutputRuleError(f"{target.name}이 이미 있다. 덮어쓰지 않는다") from exc
    return target


def run_unit(unit_id: str, input_path: Path, *,
             outputs_root: Path | None = None,
             clock: Callable[[], datetime] = now_kst,
             sleep: Callable[[float], None] = time.sleep,
             out: TextIO | None = None,
             err: TextIO | None = None) -> int:
    """단위 하나를 돌리고 종료 코드를 돌려준다. outputs_root가 없으면 저장소 루트의 outputs/를 쓴다."""
    out = out or sys.stdout
    err = err or sys.stderr
    unit = registry.UNITS.get(unit_id)
    if unit is None:
        reason = registry.NOT_REGISTERED.get(unit_id, "단위 표에 없는 ID다")
        print(f"오류: 단위 {unit_id}는 등록부에 없다({reason})", file=err)
        return EXIT_USAGE
    if unit.entry is None:
        print(f"오류: 단위 {unit_id}({unit.domain})는 공통 실행기로 돌리지 않는다: {unit.note}", file=err)
        return EXIT_USAGE
    try:
        inp = load_input(input_path)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"오류: 입력 파일을 읽지 못했다({type(exc).__name__}). 입력은 JSON 문서 하나다", file=err)
        return EXIT_USAGE
    try:
        entry = registry.load_entry(unit)
    except (ImportError, AttributeError, LookupError) as exc:
        print(f"오류: 단위 {unit_id}의 진입 함수를 불러오지 못했다({type(exc).__name__}: {exc})", file=err)
        return EXIT_USAGE
    if outputs_root is None:
        if not (REPO_ROOT / "pyproject.toml").is_file():
            print("오류: 저장소 루트를 찾지 못했다. 저장소에서 설치한 가상환경으로 실행한다", file=err)
            return EXIT_USAGE
        outputs_root = REPO_ROOT / "outputs"
    try:
        run_id, stamp, run_dir = reserve_run_dir(outputs_root, outputs_root / "sealed", unit.domain,
                                                 clock=clock, sleep=sleep)
    except RunNameError as exc:
        print(f"오류: {exc}", file=err)
        return EXIT_OUTPUT
    print(f"실행명: {run_id}", file=out)
    print(f"실행 폴더: outputs/{run_id}/", file=out)
    try:
        value = entry(inp)
    except NotImplementedError:
        print(f"오류: 단위 {unit_id}({unit.domain})의 run은 아직 구현되지 않았다. "
              f"확보한 실행 폴더 outputs/{run_id}/는 비어 있다", file=err)
        return EXIT_NOT_IMPLEMENTED
    try:
        path = write_output(run_dir, unit.domain, stamp, unit.ext, value)
    except OutputRuleError as exc:
        print(f"오류: 출력 규칙 위반: {exc}", file=err)
        return EXIT_OUTPUT
    print(f"출력: outputs/{run_id}/{path.name}", file=out)
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tradesentry.units",
        description="등록부의 단위 하나를 혼자 돌린다(개발 전용). 출력은 outputs/{도메인명}-{시각}/에 쓴다.")
    parser.add_argument("unit_id", metavar="UNIT_ID", help="단위 ID(docs/plan/UNITS.md §3), 예: X1")
    parser.add_argument("--in", dest="input_file", required=True, metavar="INPUT_FILE",
                        help="입력 파일(JSON 문서 하나. 비어 있으면 입력 없음)")
    args = parser.parse_args(argv)
    return run_unit(args.unit_id, Path(args.input_file))
