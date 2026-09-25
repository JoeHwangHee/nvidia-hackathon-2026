"""가짜 openshell(조립 작업 AS3 샌드박스 백엔드 시험용). 파일 이름이 test로 시작하지 않으므로 시험으로 모이지 않는다.

시험이 임시 폴더에 `openshell` 실행 파일(이 스크립트를 부르는 셸 한 줄)을 만들고 PATH 앞에 둔다. 실제 openshell·샌드박스·
NIM은 쓰지 않는다. 네트워크를 쓰지 않는다. 환경변수(시험이 준다)
- FAKE_OPENSHELL_ROOT: 가짜 샌드박스 파일 시스템의 뿌리(샌드박스 안 경로 /sandbox/… 는 이 폴더 아래 sandbox/… 다)
- FAKE_OPENSHELL_SCENARIO: 시나리오 JSON 파일({"manifest": 이미지 기록 또는 null, "versions": 버전 키 5개, "dataset": 자료 묶음,
  "cases": {case_id: 동작}})
- FAKE_OPENSHELL_LOG: 부른 인자와 환경 키 이름 일부를 한 줄씩 덧붙이는 JSONL 파일

동작(사례별): ok(COMPLETED 기록·보고서, 종료 0), failed(FAILED 기록, 종료 1), crash(실행 폴더 없음, 종료 1),
exit3(실행 폴더 없음, 종료 3), link(실행 폴더에 호스트 파일을 가리키는 링크), fifo(이름 있는 파이프), layered(내려받기가 한
겹 더 싸서 준다), download_fail(내려받기 종료 1), norecord(기록 없이 trace만, 종료 1), unreadable(내려받은 뒤 링크를 든
하위 폴더의 권한이 000), hardlink(일반 파일 둘이 하드링크), misplaced(최상위에 N6·N7 밖 이름의 파일), nat_missing(NAT
프로파일 파일 없음), infra(HTTP 503으로 FAILED인 기록, 종료 1. 룰북 B5 인프라 실패 재실행 대상. 단위 E2 시험이 쓴다). 보통
사례는 NAT 폴더에 nat_trace.jsonl과 프로파일 파일 5개를 쓴다. 보고서 파일은 run_id·case_id·mode만 든 최소 객체다(채점기가 줄과
맞춰 보고 "채점할 수 없는 보고서"로 세되 묶음은 채점한다).
"""
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(os.environ["FAKE_OPENSHELL_ROOT"])
SCENARIO = json.loads(Path(os.environ["FAKE_OPENSHELL_SCENARIO"]).read_text(encoding="utf-8"))
LOG = Path(os.environ["FAKE_OPENSHELL_LOG"])
WATCHED_ENV = ("NVIDIA_API_KEY", "NVIDIA_INFERENCE_API_KEY", "DATA_GO_KR_SERVICE_KEY", "TRADESENTRY_SEALED_DIR")
CLI = "/opt/tradesentry/bin/tradesentry"
PROFILE_FILES = ("all_requests_profiler_traces.json", "inference_optimization.json", "standardized_data_all.csv",
                 "workflow_profiling_metrics.json", "workflow_profiling_report.txt")
COMPLETED_ACTIONS = ("ok", "link", "fifo", "layered", "download_fail", "unreadable", "hardlink", "misplaced", "nat_missing")
MANIFEST = "/opt/tradesentry/image_manifest.json"
STATE = ROOT / "state"


def inside(path: str) -> Path:
    return ROOT / path.lstrip("/")


def log(argv: list[str]) -> None:
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({"argv": argv, "env": sorted(k for k in WATCHED_ENV if k in os.environ)}) + "\n")


def record(run_id: str, case_id: str, mode: str, status: str, infra: bool = False) -> dict:
    completed = status == "COMPLETED"
    code, detail = ("PROVIDER_HTTP_5XX", "HTTP 503") if infra else ("PROVIDER_HTTP_4XX", "HTTP 400")
    return {"run_id": run_id, "case_id": case_id, "dataset": SCENARIO["dataset"], "mode": mode, **SCENARIO["versions"],
            "review_status_final": "HOLD" if completed else None,
            "signal_status": {"unit_value": "HOLD", "share": "NOT_TRIGGERED"} if completed else None,
            "unresolved_evidence": False, "execution_status": status, "tool_attempts": 3, "model_requests": 0,
            "tokens_in": 0, "tokens_out": 0, "wall_ms": 1200, "critic_used": False, "revision_used": False,
            "errors": [] if completed else [{"code": code, "stage": "basic", "detail": detail,
                                             "attempts": {"tool_attempts": 3, "model_requests": 0, "tokens_in": 0,
                                                          "tokens_out": 0, "wall_ms": 1200},
                                             "last_good_evidence": []}]}


def run_case(argv: list[str]) -> int:
    options = dict(zip(argv[0::2], argv[1::2]))
    run_id, case_id, mode = options["--run-name"], options["--case"], options["--mode"]
    stamp = run_id.rsplit("-", 1)[1]
    action = SCENARIO["cases"].get(case_id, "ok")
    STATE.mkdir(exist_ok=True)
    (STATE / run_id).write_text(action, encoding="utf-8")
    if action in ("crash", "exit3"):
        return 1 if action == "crash" else 3
    folder = inside("/sandbox/outputs") / run_id
    folder.mkdir(parents=True)  # 이미 있으면 실패(CLI의 --run-name 규칙과 같다)
    (folder / f"runlog_trace-{stamp}.jsonl").write_text("{}\n", encoding="utf-8")
    nat = folder / f"workflow_nat_wrap-{stamp}"
    nat.mkdir()
    (nat / "nat_trace.jsonl").write_text("{}\n", encoding="utf-8")
    if action != "nat_missing":
        for name in PROFILE_FILES:
            (nat / name).write_text("{}\n", encoding="utf-8")
    if action == "norecord":
        return 1
    status = "COMPLETED" if action in COMPLETED_ACTIONS else "FAILED"
    (folder / f"runlog_run_record-{stamp}.json").write_text(
        json.dumps(record(run_id, case_id, mode, status, infra=action == "infra")), encoding="utf-8")
    if status == "COMPLETED":
        (folder / f"reports_render_ko-{stamp}.json").write_text(
            json.dumps({"run_id": run_id, "case_id": case_id, "mode": mode}), encoding="utf-8")
    if action == "link":
        os.symlink(ROOT / "host_secret.txt", nat / "leak.txt")
    if action == "fifo":
        os.mkfifo(folder / f"pipe-{stamp}")
    if action == "hardlink":
        os.link(folder / f"runlog_trace-{stamp}.jsonl", nat / "twin.jsonl")
    if action == "misplaced":
        (folder / "notes.txt").write_text("x", encoding="utf-8")
    if action == "unreadable":
        (nat / "hidden").mkdir()
        os.symlink(ROOT / "host_secret.txt", nat / "hidden" / "leak.txt")
    return 0 if status == "COMPLETED" else 1


def sh_check(script: str) -> int:
    parts = script.split()
    # "test -d X && ! test -L X && ! test -L Y"
    target, parent = parts[2], parts[-1]
    ok = inside(target).is_dir() and not inside(target).is_symlink() and not inside(parent).is_symlink()
    return 0 if ok else 1


def download(src: str, dest: str) -> int:
    run_id = src.rsplit("/", 1)[1]
    action = (STATE / run_id).read_text(encoding="utf-8") if (STATE / run_id).exists() else "ok"
    if action == "download_fail":
        return 1
    source = inside(src)
    target = Path(dest)
    if action == "layered":
        shutil.copytree(source, target / run_id, symlinks=True)
        return 0
    for entry in source.iterdir():
        if entry.is_symlink():
            os.symlink(os.readlink(entry), target / entry.name)
        elif entry.is_dir():
            shutil.copytree(entry, target / entry.name, symlinks=True)
        elif entry.is_fifo():
            os.mkfifo(target / entry.name)
        else:
            shutil.copyfile(entry, target / entry.name)
    stamp = run_id.rsplit("-", 1)[1]
    if action == "hardlink":  # 받은 트리 안에서도 하드링크로 둔다
        nat = target / f"workflow_nat_wrap-{stamp}"
        (nat / "twin.jsonl").unlink()
        os.link(target / f"runlog_trace-{stamp}.jsonl", nat / "twin.jsonl")
    if action == "unreadable":
        os.chmod(target / f"workflow_nat_wrap-{stamp}" / "hidden", 0)
    return 0


def main(argv: list[str]) -> int:
    log(argv)
    if argv[:2] == ["sandbox", "download"]:
        return download(argv[3], argv[4])
    if argv[:2] != ["sandbox", "exec"] or "--" not in argv:
        return 2
    command = argv[argv.index("--") + 1:]
    if command == ["cat", MANIFEST]:
        if SCENARIO.get("manifest") is None:
            return 1
        sys.stdout.write(json.dumps(SCENARIO["manifest"]))
        return 0
    if command[:2] == [CLI, "run-case"]:
        return run_case(command[2:])
    if command[:2] == ["sh", "-c"]:
        return sh_check(command[2])
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
