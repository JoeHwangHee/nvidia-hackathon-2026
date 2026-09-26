"""담당자 결정 기록(모의 승인)의 저장·읽기·대조(순수 논리, streamlit 없음).

기록 필드(단위 A1·A2 결정 기록): `record_id, case_id, run_id, decision(MAINTAIN|MONITOR|HOLD), suggested(보고서의 판정), memo,
reviewer_label, timestamp, report_hash, evidence_digest, snapshot_id, policy_version, code_version`. 핵심(해시·digest·유효 상태)은
단위 A1 `approval.record`가 만든다.

규칙
- `execution_status`가 `COMPLETED`인 실행만 기록할 수 있다(A1이 거부한다).
- 저장은 추가 전용이다. 기록 하나가 실행 하나다: 실행 이름은 단위 A1의 도메인명 `approval_record`, 실행 폴더는
  `outputs/approval_record-{yymmddhhmmss}/`, 파일은 `approval_record-{yymmddhhmmss}.json`(자료 계약 §10.3 N4·N5·N6). 이미 있는
  이름은 쓰지 않고 다음 초로 넘어간다(N8: 그 초가 될 때까지 기다린 뒤 exist_ok 없는 mkdir). 한 파일에 덧붙이는 JSONL은 N6
  (실행마다 파일 하나)·N8(덮어쓰기 금지)에 맞지 않아 쓰지 않는다.
- 읽을 때 실행 폴더의 지금 보고서와 기록의 `report_hash`·`evidence_digest`를 대조해 `VALID`/`REVIEW_REQUIRED`를 붙인다. 기록
  파일은 고치지 않는다.
- 계정·권한·인증은 없다. `outputs/sealed/`는 보지 않는다.
"""
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from tradesentry import app
from tradesentry.approval import record as approval
from tradesentry.contract import types

RUN_NAME = "approval_record"  # 단위 A1 도메인명 = 혼자 돌릴 때의 실행 이름(N5)
RECORD_DIR_RE = re.compile(r"approval_record-\d{12}")
STAMP_FORMAT = "%y%m%d%H%M%S"
KST = timezone(timedelta(hours=9))
DECISIONS = types.REVIEW_STATUSES  # MAINTAIN·MONITOR·HOLD
RECORD_KEYS = ("record_id", "case_id", "run_id", "decision", "suggested", "memo", "reviewer_label", "timestamp",
               "report_hash", "evidence_digest", "snapshot_id", "policy_version", "code_version")
MAX_ATTEMPTS = 60


def now_kst() -> datetime:
    return datetime.now(KST)


def timestamp_text(moment: datetime | None = None) -> str:
    """KST ISO 8601(초 단위, 자료 계약 §11.4)."""
    moment = now_kst() if moment is None else moment
    return moment.astimezone(KST).replace(microsecond=0).isoformat()


def build_record(loaded: dict, decision: str, memo: str, reviewer_label: str, timestamp: str | None = None) -> dict:
    """실행 폴더 읽기 결과(app.load_run)와 담당자 입력으로 기록 객체(record_id 없이)를 만든다. COMPLETED가 아니면 ValueError."""
    if decision not in DECISIONS:
        raise ValueError("decision은 MAINTAIN·MONITOR·HOLD 가운데 하나다")
    record, report = loaded.get("record") or {}, loaded.get("report")
    core = approval.approve(report, record.get("execution_status"), reviewer_label.strip(), timestamp or timestamp_text(),
                            record.get("code_version"))
    return {
        "record_id": None, "case_id": record.get("case_id") or report.get("case_id"), "run_id": loaded["run_id"],
        "decision": decision, "suggested": record.get("review_status_final"), "memo": (memo or "").strip(),
        "reviewer_label": core["reviewer_label"], "timestamp": core["timestamp"], "report_hash": core["report_hash"],
        "evidence_digest": core["evidence_digest"], "snapshot_id": core["snapshot_id"],
        "policy_version": core["policy_version"], "code_version": core["code_version"],
    }


def _second(moment: datetime) -> datetime:
    """이름에 쓸 초: 시작 시각보다 앞서지 않게, 소수 초가 있으면 다음 초로 올린다(N8)."""
    whole = moment.replace(microsecond=0)
    return whole + timedelta(seconds=1) if moment.microsecond else whole


def reserve_record_dir(outputs_root: Path, clock: Callable[[], datetime] = now_kst,
                       sleep: Callable[[float], None] = time.sleep) -> tuple[str, str, Path]:
    """기록 실행명을 확보한다(N8): 그 초가 될 때까지 기다린 뒤 exist_ok 없는 mkdir. 실패하면 다음 초. outputs/sealed/ 아래에
    같은 이름이 있으면 방금 만든 빈 폴더를 지우고 다음 초로 넘어간다."""
    outputs_root.mkdir(parents=True, exist_ok=True)
    target = _second(clock())
    for _ in range(MAX_ATTEMPTS):
        remaining = (target - clock()).total_seconds()
        if remaining > 0:
            sleep(remaining)
        stamp = target.strftime(STAMP_FORMAT)
        run_id = f"{RUN_NAME}-{stamp}"
        run_dir = outputs_root / run_id
        try:
            os.mkdir(run_dir)
        except FileExistsError:
            target += timedelta(seconds=1)
            continue
        if (outputs_root / app.SEALED_NAME / run_id).exists():
            os.rmdir(run_dir)
            target += timedelta(seconds=1)
            continue
        return run_id, stamp, run_dir
    raise RuntimeError("기록 실행명을 확보하지 못했다")


def save_record(outputs_root: Path, record: dict, clock: Callable[[], datetime] = now_kst,
                sleep: Callable[[float], None] = time.sleep) -> dict:
    """기록을 새 실행 폴더에 쓴다(추가 전용). 돌려주는 값은 record_id가 채워진 기록과 상대 경로(outputs/부터)다."""
    run_id, stamp, run_dir = reserve_record_dir(outputs_root, clock, sleep)
    saved = {**record, "record_id": run_id}
    path = run_dir / f"{RUN_NAME}-{stamp}.json"
    with path.open("x", encoding="utf-8") as fh:  # 'x': 이미 있으면 실패(덮어쓰기 금지)
        json.dump({key: saved.get(key) for key in RECORD_KEYS}, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    return {"record": saved, "path": f"{app.OUTPUTS_NAME}/{run_id}/{path.name}"}


def list_record_dirs(outputs_root: Path) -> list[str]:
    """outputs/ 바로 아래 approval_record-{시각} 폴더 이름(새 것부터). sealed·받는 중·격리·심볼릭 링크는 뺀다."""
    if not outputs_root.is_dir():
        return []
    names = []
    for entry in outputs_root.iterdir():
        name = entry.name
        if name == app.SEALED_NAME or name.startswith(app.EXCLUDED_PREFIXES) or entry.is_symlink() or not entry.is_dir():
            continue
        if RECORD_DIR_RE.fullmatch(name):
            names.append(name)
    return sorted(names, reverse=True)


def load_records(outputs_root: Path) -> list[dict]:
    """저장된 기록 전부(새 것부터). 깨진 파일은 건너뛴다."""
    out = []
    for name in list_record_dirs(outputs_root):
        path = outputs_root / name / f"{RUN_NAME}-{name.rsplit('-', 1)[-1]}.json"
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(record, dict) and isinstance(record.get("case_id"), str):
            out.append({key: record.get(key) for key in RECORD_KEYS})
    return out


def current_report(outputs_root: Path, run_id: object) -> dict | None:
    """기록이 가리키는 실행 폴더의 지금 보고서. 없거나 읽지 못하면 None."""
    if not isinstance(run_id, str) or not app.RUN_DIR_RE.fullmatch(run_id):
        return None
    try:
        return app.load_run(outputs_root / run_id).get("report")
    except (OSError, ValueError, KeyError):
        return None


def records_for_case(outputs_root: Path, case_id: str) -> list[dict]:
    """그 사례의 기록(새 것부터)에 유효 상태 `validity`(VALID·REVIEW_REQUIRED)를 붙인다. 기록은 고치지 않는다."""
    reports: dict[str, dict | None] = {}
    out = []
    for record in load_records(outputs_root):
        if record["case_id"] != case_id:
            continue
        run_id = record.get("run_id")
        if run_id not in reports:
            reports[run_id] = current_report(outputs_root, run_id)
        out.append({**record, "validity": approval.check(record, reports[run_id])})
    return out
