"""담당자 홈의 경보 목록·지표·조사 상태(순수 논리, streamlit 없음).

- 경보 목록은 CLI `detect`와 같은 길(`tradesentry.cli.dispatch.build_case_list` → 단위 P2 `policy.case_build.run`)로 만든다.
  실자료는 분할 기록의 `real_dev` 계열만 남는다(detect와 같다). 화면이 판정·지표를 새로 계산하지 않는다.
- 경보마다 이력 도구(단위 I2 `tools.get_history.run`)의 봉투에서 지표를 옮긴다: `U`(기준월·비교월), `r_U`, `s`(두 달), `d_s`.
  값은 도구가 준 Decimal(자료 계약 §11.3 표시 자릿수) 그대로이고 None이면 "비교 불가"다.
- 조사 상태는 `outputs/run_case-{시각}/`의 실행 결과 기록(`runlog_run_record-{시각}.json`)에서 그 `case_id`의 최신 실행을
  찾아 정한다. 폴더 나열은 화면 단위 `app.list_run_dirs`를 재사용한다(`outputs/sealed/`·`.download-*`·`.quarantine-*`·
  심볼릭 링크 제외).
- 키·로컬 절대 경로를 돌려주는 값에 넣지 않는다(폴더 이름만).
"""
import json
import re
from decimal import Decimal
from pathlib import Path

from tradesentry import app
from tradesentry.cli import dispatch
from tradesentry.contract import policy_load, types
from tradesentry.dal import query
from tradesentry.tools import get_history

DEFAULT_POLICY = app.DEFAULT_POLICY
NOT_INVESTIGATED = "NOT_INVESTIGATED"
INVESTIGATED = "INVESTIGATED"
FAILED = "FAILED"
STATUSES = (NOT_INVESTIGATED, INVESTIGATED, FAILED)
METRIC_KEYS = ("U_0", "U_1", "r_U", "s_0", "s_1", "d_s")
STAMP_RE = re.compile(r"\d{12}")


# ---- 경보 목록 -----------------------------------------------------------------------------------------------


def case_list(snapshot_id: str, policy_version: str = DEFAULT_POLICY) -> dict:
    """스냅샷 하나의 경보 사례 목록(단위 P2 출력 그대로). detect와 같은 함수(build_case_list)를 부른다. 스냅샷을 열 수
    없거나 분할 기록이 맞지 않으면 예외가 난다(부르는 쪽이 이름만 보인다, N13)."""
    policy = policy_load.load_policy(policy_version)
    with query.open_snapshot(snapshot_id) as snap:
        if snap.source_kind not in dispatch.DETECT_SOURCE_KINDS:
            raise ValueError("이 스냅샷의 출처 종류는 탐지 대상이 아니다")
        return dispatch.build_case_list(snap, policy)


def list_months(snapshot_id: str, policy_version: str = DEFAULT_POLICY, cases: dict | None = None) -> list[str]:
    """경보가 있는 비교월(YYYYMM), 최신 먼저."""
    cases = case_list(snapshot_id, policy_version) if cases is None else cases
    return sorted({c["month"] for c in cases["cases"]}, reverse=True)


def snapshot_period(snapshot_id: str) -> tuple[str, str] | None:
    """스냅샷 기간(첫 달, 끝 달). 열 수 없으면 None."""
    try:
        with query.open_snapshot(snapshot_id) as snap:
            return (snap.months[0], snap.months[-1]) if snap.months else None
    except (query.SnapshotError, OSError):
        return None


def _metric_map(envelope: dict, partner: str, month: str, baseline: str) -> dict:
    """봉투의 metrics에서 대상국의 U(두 달)·r_U·s(두 달)·d_s를 옮긴다. 없거나 null이면 None."""
    found = {key: None for key in METRIC_KEYS}
    for metric in envelope.get("metrics") or []:
        inputs = metric.get("inputs") if isinstance(metric, dict) else None
        if not isinstance(inputs, dict) or inputs.get("partner") != partner:
            continue
        symbol, period, value = inputs.get("metric"), inputs.get("period"), metric.get("value")
        if symbol == "U" and period == baseline:
            found["U_0"] = value
        elif symbol == "U" and period == month:
            found["U_1"] = value
        elif symbol == "r_U" and period == month:
            found["r_U"] = value
        elif symbol == "s" and period == baseline:
            found["s_0"] = value
        elif symbol == "s" and period == month:
            found["s_1"] = value
        elif symbol == "d_s" and period == month:
            found["d_s"] = value
    return found


def history_request(case: dict) -> dict:
    """사례 → 이력 도구 요청(도구 공통 틀의 요청 모양. 모델 인자는 없다)."""
    scope = {"hs6": case["hs6"], "partner": case["partner"], "month": case["month"], "baseline_month": case["baseline_month"]}
    return {"case_id": case["case_id"], "snapshot_id": case["snapshot_id"], "scope": scope, "args": {}, "attempt": 1}


def alert_row(case: dict, envelope: dict) -> dict:
    """경보 한 줄: 사례 필드 + 지표 + 신호 발동 여부(불리언). 값은 옮길 뿐 계산하지 않는다."""
    signals = case.get("signals") or {}
    metrics = _metric_map(envelope, case["partner"], case["month"], case["baseline_month"])
    return {
        "case_id": case["case_id"], "hs6": case["hs6"], "partner": case["partner"], "month": case["month"],
        "baseline_month": case["baseline_month"], "snapshot_id": case["snapshot_id"], "policy_version": case["policy_version"],
        "unit_value_triggered": signals.get("unit_value") == "TRIGGERED",
        "share_triggered": signals.get("share") == "TRIGGERED",
        "metrics": metrics,
        "missingness": len(envelope.get("missingness") or []),
    }


def alerts_for_month(snapshot_id: str, month: str, policy_version: str = DEFAULT_POLICY,
                     cases: dict | None = None, history=get_history.run) -> list[dict]:
    """그 달의 경보 목록(사례 ID 순). 경보마다 이력 도구를 한 번 불러 지표를 옮긴다. history는 시험용 대역 자리다."""
    cases = case_list(snapshot_id, policy_version) if cases is None else cases
    rows = []
    for case in cases["cases"]:
        if case["month"] != month:
            continue
        envelope = history(history_request(case))
        rows.append(alert_row(case, envelope if isinstance(envelope, dict) else {}))
    return rows


# ---- 조사 상태 -----------------------------------------------------------------------------------------------


def _record_file(run_dir: Path) -> Path | None:
    exact = run_dir / f"{app.RECORD_DOMAIN}-{app.run_stamp(run_dir.name)}.json"
    if exact.is_file():
        return exact
    found = sorted(p for p in run_dir.glob(f"{app.RECORD_DOMAIN}-*.json") if p.is_file())
    return found[0] if found else None


def run_entry(outputs_root: Path, run_id: str) -> dict | None:
    """실행 폴더 하나의 요약(사례·실행 상태·최종 판정·신호별 판정·버전). 실행 결과 기록이 없거나 깨졌으면 None."""
    path = _record_file(outputs_root / run_id)
    if path is None:
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(record, dict) or not isinstance(record.get("case_id"), str):
        return None
    execution = record.get("execution_status")
    return {
        "run_id": run_id, "case_id": record["case_id"], "execution_status": execution,
        "status": INVESTIGATED if execution == "COMPLETED" else (NOT_INVESTIGATED if execution is None else FAILED),
        "review_status_final": record.get("review_status_final"), "signal_status": record.get("signal_status"),
        "snapshot_id": record.get("snapshot_id"), "policy_version": record.get("policy_version"),
        "code_version": record.get("code_version"), "mode": record.get("mode"), "time": stamp_label(run_id),
    }


def investigation_index(outputs_root: Path) -> dict[str, dict]:
    """사례 ID → {"latest": 최신 실행 요약, "runs": [실행 요약, 새 것부터]}. outputs/sealed/ 등은 보지 않는다."""
    index: dict[str, dict] = {}
    for run_id in app.list_run_dirs(outputs_root):  # 새 것부터
        entry = run_entry(outputs_root, run_id)
        if entry is None:
            continue
        bucket = index.setdefault(entry["case_id"], {"latest": entry, "runs": []})
        bucket["runs"].append(entry)
    return index


def investigation_status(case_id: str, outputs_root: Path | None = None, index: dict | None = None) -> dict:
    """그 사례의 상태(조사 전·조사 완료·실패)와 최신 실행 폴더 이름. 실행이 없으면 조사 전이다. index(investigation_index의
    결과)를 주면 outputs_root를 다시 읽지 않는다."""
    if index is None:
        index = investigation_index(outputs_root) if outputs_root is not None else {}
    bucket = index.get(case_id)
    if bucket is None:
        return {"status": NOT_INVESTIGATED, "run_id": None, "review_status_final": None, "execution_status": None, "runs": []}
    latest = bucket["latest"]
    return {"status": latest["status"], "run_id": latest["run_id"], "review_status_final": latest["review_status_final"],
            "execution_status": latest["execution_status"], "runs": bucket["runs"]}


def summary(alerts: list[dict], all_cases: dict | None, index: dict) -> dict:
    """요약 4칸: 단가 변화 경보 수·점유율 변화 경보 수·조사 완료/전체·스냅샷 전체 경보 수(최근 24개월 합계)."""
    done = sum(1 for a in alerts if investigation_status(a["case_id"], index=index)["status"] == INVESTIGATED)
    return {"unit_value": sum(1 for a in alerts if a["unit_value_triggered"]),
            "share": sum(1 for a in alerts if a["share_triggered"]),
            "investigated": done, "total": len(alerts),
            "all_months": len(all_cases["cases"]) if all_cases else None}


# ---- 필터·표시 -------------------------------------------------------------------------------------------------


def filter_alerts(alerts: list[dict], index: dict, *, signal: str = "all", status: str = "all",
                  search: str = "", labels: dict[str, str] | None = None) -> list[dict]:
    """보기 필터: signal은 all·unit_value·share, status는 all·NOT_INVESTIGATED·INVESTIGATED·FAILED, search는 사례 ID·HS6·
    상대국 코드·이름표(labels: 코드/HS6 → 이름) 부분 일치(대소문자 무시)."""
    labels = labels or {}
    needle = (search or "").strip().lower()
    out = []
    for alert in alerts:
        if signal == "unit_value" and not alert["unit_value_triggered"]:
            continue
        if signal == "share" and not alert["share_triggered"]:
            continue
        state = investigation_status(alert["case_id"], index=index)["status"]
        if status != "all" and state != status:
            continue
        if needle:
            haystack = " ".join([alert["case_id"], alert["hs6"], alert["partner"], labels.get(alert["hs6"], ""),
                                 labels.get(alert["partner"], "")]).lower()
            if needle not in haystack:
                continue
        out.append(alert)
    return out


def number_text(value: object) -> str | None:
    """Decimal·int를 천 단위 쉼표와 끝자리 0을 지닌 십진 표기로. None은 None(새로 반올림하지 않는다)."""
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return format(value, ",")
    if isinstance(value, Decimal):
        return format(value, ",f")
    return str(value)


def signed_text(value: object) -> str | None:
    """부호를 붙인 표기(+1.5 / −42.3 / 0.0). None은 None."""
    text = number_text(value)
    if text is None:
        return None
    if text.startswith("-"):
        return "−" + text[1:]
    try:
        positive = Decimal(str(value)) > 0
    except (ArithmeticError, ValueError, TypeError):
        positive = False
    return ("+" + text) if positive else text


def history_signal(alert: dict | None) -> dict:
    """이력·진행 단계의 "경보 발생" 줄에 적을 신호와 값. 현재 스냅샷의 경보 줄(alert_row)이 있으면 발동 신호의 값을, 없으면
    (다른 스냅샷의 사례) 값 없이 kind None을 돌려준다. 값은 옮길 뿐이다."""
    if not isinstance(alert, dict):
        return {"kind": None, "value": None}
    metrics = alert.get("metrics") or {}
    if alert.get("unit_value_triggered") and metrics.get("r_U") is not None:
        return {"kind": "unit_value", "value": metrics["r_U"]}
    if alert.get("share_triggered") and metrics.get("d_s") is not None:
        return {"kind": "share", "value": metrics["d_s"]}
    return {"kind": None, "value": None}


def completed_runs(index: dict, snapshot_id: str | None = None) -> list[dict]:
    """조사 완료(COMPLETED) 실행 요약 목록(새 것부터). snapshot_id를 주면 그 스냅샷의 실행만."""
    runs = [run for bucket in index.values() for run in bucket["runs"]
            if run["status"] == INVESTIGATED and (snapshot_id is None or run.get("snapshot_id") == snapshot_id)]
    return sorted(runs, key=lambda r: r["run_id"], reverse=True)


def stamp_label(run_id: object) -> str:
    """실행명의 시각(yymmddhhmmss) → "20yy-mm-dd hh:mm". 형식이 다르면 원문."""
    if not isinstance(run_id, str):
        return str(run_id)
    stamp = run_id.rsplit("-", 1)[-1]
    if not STAMP_RE.fullmatch(stamp):
        return run_id
    return f"20{stamp[0:2]}-{stamp[2:4]}-{stamp[4:6]} {stamp[6:8]}:{stamp[8:10]}"


def fixture_snapshot_id() -> str:
    return types.FIXTURE_SNAPSHOT_ID


def default_snapshot(snapshots: list[str]) -> str | None:
    """기본 스냅샷: 정본 빌드가 있는 실자료(kcs_202201_202412_v2)가 있으면 그것, 없으면 합성 픽스처, 그것도 없으면 첫 것."""
    for candidate in (types.REAL_SNAPSHOT_ID, types.FIXTURE_SNAPSHOT_ID):
        if candidate in snapshots:
            return candidate
    return snapshots[0] if snapshots else None
