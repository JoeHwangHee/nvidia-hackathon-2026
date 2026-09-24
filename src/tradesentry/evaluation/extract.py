"""단위 E3 추출 명령.

단위 ID: E3
도메인명: evaluation_extract
소유: M
입력: 실행 기록
출력: `execution_status`·원인 분류 코드·버전 키
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.runlog

정본: docs/plan/UNITS.md E3 행, 로드맵 MT7(추출 명령), 평가 스킬 ② skills/tradesentry-eval/SKILL.md "채점 전 확인" 1·2번과
"실패와 재실행", 룰북 docs/eval/RULEBOOK.md B5(인프라 실패 재실행), 자료 계약 §10.3 N8·N10.

평가 묶음의 실행 기록(evaluation_batch_run-{시각}.jsonl)에서 execution_status, errors의 원인 분류 코드, 버전 키 5개
(policy_version·rulebook_version·snapshot_id·grouping_version·code_version)만 뽑아 건수와 참·거짓으로 낸다.
- 건수(summarize, 진입 함수 run): 실행 상태별 건수(상태 5개 모두, 0 포함), 원인 분류 코드별 건수(단위 L3의 코드 모두, 0
  포함, 모르는 코드는 unknown), 인프라 실패 재실행 대상 건수, 버전 키마다 서로 다른 값의 수·일치 여부·불일치 건수.
  사전 점검 값(expected_versions)을 주면 그 값과 대조하고, 주지 않으면 한 값뿐인지만 본다(불일치 건수는 null).
  사례 식별자·실행명·값 자체는 내지 않는다(오케스트레이터에게는 건수와 일치 여부만 준다, 로드맵 MT7).
- 인프라 실패 재실행 대상(rerun_targets): 단위 L3 infra_rerun_eligible 하나로만 가른다(원인 코드 문자열을 여기서 따로
  적지 않는다). 목록은 실행 기록 줄의 순서(= 첫 실행의 순서, 룰북 B5)대로 {run_id, case_id, mode}다.
- 추출 실행(extract): 자기 실행 폴더 evaluation_extract-{시각}/을 N8대로 확보해(봉인 묶음이면 outputs/sealed/ 아래)
  건수 evaluation_extract-{시각}.json과 재실행 대상 목록 evaluation_extract-{시각}.jsonl을 배타 생성한다. 재실행 대상
  목록은 샌드박스 밖 실행기만 읽는다. 봉인 묶음이면 에이전트는 금지 해제 조건(N10) 전에 이 폴더를 열지 않는다.
  표준 출력(main)에는 자기 실행 폴더 이름과 건수만 낸다(사례 식별자를 내지 않는다).
- 믿지 않는 입력: 실행 기록은 샌드박스가 쓴 파일이다. 객체가 아니거나 두 키(execution_status·errors)의 모양이 틀린 줄은
  malformed로 세고 건너뛴다. 오류 문장에는 예외 이름만 적는다(N13).

묶음 기록 이름: 평가 묶음 실행 evaluate-{시각}의 evaluation_batch_run-{시각}.jsonl(단위 E1)만 안다. 샌드박스 밖 실행기
E2의 묶음 기록 도메인명과 봉인 묶음 실행 이름은 로드맵 MT7의 다음 PR에서 정한다(모르는 이름이면 오류).
"""
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable

from tradesentry.contract import types
from tradesentry.runlog import cause_codes, run_record
from tradesentry.runlog import trace as trace_log

DOMAIN = "evaluation_extract"
BATCH_DOMAINS = {"evaluate": "evaluation_batch_run"}  # 묶음 실행 이름 → 묶음 기록 도메인명(E2는 다음 PR)
VERSION_KEYS = ("policy_version", "rulebook_version", "snapshot_id", "grouping_version", "code_version")
TARGET_KEYS = ("run_id", "case_id", "mode")
UNKNOWN = "unknown"
MAX_BATCH_BYTES = 16 << 20
SEALED_NAME = "sealed"


class ExtractError(ValueError):
    """추출 입력이 규칙에 맞지 않는다."""


def _well_formed(line: object) -> bool:
    return isinstance(line, dict) and line.get("execution_status") in types.EXECUTION_STATUSES \
        and isinstance(line.get("errors"), list)


def summarize(lines: list, expected_versions: dict | None = None) -> dict:
    """건수와 버전 키 일치 여부(머리 설명). 사례 식별자·값을 내지 않는다."""
    if expected_versions is not None and (not isinstance(expected_versions, dict)
                                          or set(expected_versions) != set(VERSION_KEYS)):
        raise ExtractError(f"사전 점검 버전 값은 {'·'.join(VERSION_KEYS)} 다섯 키의 객체다")
    good = [line for line in lines if _well_formed(line)]
    statuses = {status: 0 for status in types.EXECUTION_STATUSES}
    codes = {code: 0 for code in cause_codes.CODES}
    codes[UNKNOWN] = 0
    for line in good:
        statuses[line["execution_status"]] += 1
        for entry in line["errors"]:
            code = entry.get("code") if isinstance(entry, dict) else None
            key = code if isinstance(code, str) and code in cause_codes.STATUS_BY_CODE else UNKNOWN
            codes[key] += 1
    versions = {}
    for key in VERSION_KEYS:
        values = [line.get(key) for line in good]
        distinct = len({v if isinstance(v, str) else repr(v) for v in values})
        if expected_versions is None:
            versions[key] = {"distinct": distinct, "match": distinct <= 1, "mismatch": None}
        else:
            mismatch = sum(1 for v in values if v != expected_versions[key])
            versions[key] = {"distinct": distinct, "match": mismatch == 0, "mismatch": mismatch}
    return {"lines": len(lines), "malformed": len(lines) - len(good), "execution_status": statuses,
            "cause_codes": codes, "infra_rerun": len(rerun_targets(lines)),
            "version_keys": versions, "versions_checked_against_precheck": expected_versions is not None}


def rerun_targets(lines: list) -> list[dict]:
    """인프라 실패 재실행 대상(룰북 B5). 실행 기록 줄 순서 그대로."""
    targets = []
    for line in lines:
        if _well_formed(line) and cause_codes.infra_rerun_eligible(line["execution_status"], line["errors"]) \
                and all(isinstance(line.get(k), str) for k in TARGET_KEYS):
            targets.append({k: line[k] for k in TARGET_KEYS})
    return targets


def batch_file(batch_dir: Path) -> Path:
    """묶음 실행 폴더의 묶음 기록 파일. 폴더 이름은 {묶음 실행 이름}-{시각}이다."""
    name = batch_dir.name
    if not trace_log.RUN_ID_RE.match(name):
        raise ExtractError("묶음 실행 폴더 이름이 실행명 형식이 아니다")
    run_name, stamp = name.rsplit("-", 1)
    if run_name not in BATCH_DOMAINS:
        raise ExtractError("모르는 묶음 실행 이름이다(E2의 묶음 기록 이름은 로드맵 MT7 다음 PR에서 정한다)")
    return batch_dir / f"{BATCH_DOMAINS[run_name]}-{stamp}.jsonl"


def read_batch(path: Path) -> list:
    """묶음 기록을 읽는다(줄바꿈 문자로만 나눈다). JSON이 아닌 줄은 None으로 두어 malformed로 센다."""
    if path.is_symlink() or not path.is_file():
        raise ExtractError("묶음 기록 파일이 없다")
    with open(path, "rb") as handle:
        data = handle.read(MAX_BATCH_BYTES + 1)
    if len(data) > MAX_BATCH_BYTES:
        raise ExtractError("묶음 기록 파일이 크기 상한을 넘는다")
    lines = []
    for raw in data.decode("utf-8", errors="replace").split("\n"):
        if not raw.strip():
            continue
        try:
            lines.append(trace_log.loads(raw))
        except (ValueError, RecursionError):
            lines.append(None)
    return lines


def is_sealed_place(batch_dir: Path, outputs: Path) -> bool:
    """묶음 실행 폴더가 봉인 자리(outputs/sealed/ 아래)인가. 이름만이 아니라 풀린 경로로도 보고(심볼릭 링크·다른 표기),
    풀 수 없으면 봉인으로 본다(재실행 대상 목록이 outputs/ 아래로 새지 않게)."""
    if batch_dir.parent.name.lower() == SEALED_NAME:
        return True
    try:
        sealed_root = (outputs / SEALED_NAME).resolve()
        parent = batch_dir.resolve().parent
    except (OSError, RuntimeError):
        return True
    return parent == sealed_root or sealed_root in parent.parents


def extract(batch_dir: Path, *, outputs: Path, expected_versions: dict | None = None,
            clock: Callable[[], datetime] | None = None, sleep: Callable[[float], None] | None = None
            ) -> tuple[str, dict]:
    """추출 한 번(머리 설명). outputs는 outputs/ 폴더다. (자기 실행명, 건수)를 돌려준다(목록은 파일에만)."""
    sealed = is_sealed_place(batch_dir, outputs)
    home, other = (outputs / SEALED_NAME, outputs) if sealed else (outputs, outputs / SEALED_NAME)
    lines = read_batch(batch_file(batch_dir))
    counts = summarize(lines, expected_versions)
    targets = rerun_targets(lines)
    kw: dict = {"clock": clock or trace_log.now_kst}
    if sleep is not None:
        kw["sleep"] = sleep
    run_id, stamp, run_dir = run_record.reserve_run_dir(home, other, DOMAIN, **kw)
    _write_new(run_dir / f"{DOMAIN}-{stamp}.json", trace_log.dumps(counts) + "\n")
    _write_new(run_dir / f"{DOMAIN}-{stamp}.jsonl", "".join(trace_log.dumps(t) + "\n" for t in targets))
    return run_id, counts


def _write_new(path: Path, text: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "wb") as handle:
        handle.write(text.encode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    """python -m tradesentry.evaluation.extract --run <묶음 실행 폴더> [--expect <사전 점검 버전 값 JSON 파일>].
    저장소 루트에서 부른다(outputs/ 기준). 표준 출력: 첫 줄 자기 실행 폴더 이름, 둘째 줄 건수 JSON. 종료 코드 0 완료,
    1 입력 오류·실패, 2 인자 오류. 오류 문장에는 예외 이름만 적는다(N13, 봉인 묶음이면 사례 식별자가 나가지 않게)."""
    parser = argparse.ArgumentParser(prog="python -m tradesentry.evaluation.extract", allow_abbrev=False)
    parser.add_argument("--run", required=True)
    parser.add_argument("--expect")
    ns = parser.parse_args(argv)
    try:
        expected = None
        if ns.expect is not None:
            expected = trace_log.loads(Path(ns.expect).read_text(encoding="utf-8"))
        run_id, counts = extract(Path(ns.run), outputs=Path("outputs"), expected_versions=expected)
    except Exception as exc:  # 예외 이름만(N13)
        sys.stderr.write(f"오류: 추출하지 못했다({type(exc).__name__})\n")
        return 1
    sys.stdout.write(run_id + "\n" + trace_log.dumps(counts) + "\n")
    return 0


def run(inp: object) -> object:
    """건수를 낸다(머리 설명).

    입력: {"lines": [실행 기록 줄, ...], "expected_versions": 버전 키 5개 객체 또는 null}.
    출력: summarize의 건수 객체.
    """
    if not isinstance(inp, dict) or set(inp) != {"lines", "expected_versions"} or not isinstance(inp["lines"], list):
        raise ExtractError("입력은 lines(목록)·expected_versions 두 키의 객체다")
    return summarize(inp["lines"], inp["expected_versions"])


if __name__ == "__main__":
    sys.exit(main())
