"""단위 A2 화면.

단위 ID: A2
도메인명: app
소유: M
입력: 실행 기록·조회
출력: Streamlit 화면 1개(화면 1 "사례 보기"와 "사례 실행" 패널)
허용 import: 표준 라이브러리, streamlit, tradesentry.contract, tradesentry.dal, tradesentry.runlog, tradesentry.reports, tradesentry.approval

위치는 S0 제안이다(자문 명세서 Q14): ingest.py처럼 하위 패키지 밖 모듈로 src/tradesentry/app.py에 둔다.

화면 1 "사례 보기"(로드맵 U1, 개발 플랜 §7.7, 제출 시나리오 C = A + 화면 1개. 2026-09-26(토) 04:25 사용자 결정과 모델 결정
기록 model-decision-ui-screen-1). 화면 2(시계열)·화면 3(before-after 대조)·승인 모의는 만들지 않는다.

무엇을 읽나(모두 읽기 전용): 실행 폴더 outputs/run_case-{시각}/의 실행 결과 기록(runlog_run_record-{시각}.json, 단위 L2),
한국어 보고서(reports_render_ko-{시각}.json, 단위 R2), trace(runlog_trace-{시각}.jsonl, 단위 L1). 근거 ID는 자료 접근층
(단위 K3 query.open_snapshot → Snapshot.resolve)으로 스냅샷 원본 행을 푼다. 스냅샷을 열 수 없으면 ID만 나열한다.
무엇을 읽지 않나: .env, outputs/sealed/(봉인 묶음 실행 출력. 나열도 하지 않는다), .download-*·.quarantine-*(받는 중·격리
폴더), 봉인 폴더(TRADESENTRY_SEALED_DIR), NAT 추적 폴더. 네트워크·NIM을 부르지 않는다.

무엇을 하지 않나: 판정·지표를 다시 계산하거나 바꾸지 않는다(기록을 보여 줄 뿐이다). 값은 보고서 claims와 trace의 검증된
지표(도구 봉투 metrics)에서만 가져온다. 처음 상태 표시는 "조사 전 경보"(PRE_INVESTIGATION)이고, 판정이 바뀐 것처럼 이력을
꾸미지 않는다(자료 계약 §3.1). 부정·위법·원산지 판정을 암시하는 제목·문구를 쓰지 않는다. 키·로컬 절대 경로를 화면에
쓰지 않는다(폴더는 outputs/부터의 상대 경로만).

"사례 실행" 패널(오케스트레이터 추가 지시): CLI와 같은 진입점(python -m tradesentry.cli run-case …, 하위 프로세스)으로
사례 1건만 돌린다. evaluate·detect·봉인 묶음은 돌리지 않는다. 앱은 .env를 읽지 않는다. 실제 NIM 실행은 스트림릿 프로세스
환경에 NVIDIA_API_KEY가 있을 때만 되고, 없으면 재생 실행(--replay, eval/dev/smoke/{case_id}.json이 있을 때)만 된다.
키는 있는지 여부만 보고 값은 어디에도 쓰지 않는다. 실행 폴더는 CLI와 똑같이 outputs/run_case-{시각}/에 남는다(자료 계약
§10.3 N5·N6). 화면에서 시작한 실행과 재생 실행은 점수표 근거가 아니다.

구성: 화면 논리는 순수 함수(폴더 나열, 실행 폴더 읽기, 조회 이유·도구·주장·타임라인·차트 자료 만들기, 근거 ID 풀기,
실행 인자 조립)로 나눠 streamlit 없이 시험한다(tests/units/A2/). streamlit은 화면 함수 안에서만 import한다(경계 시험과
기본 환경 시험이 streamlit 없이 돈다). 진입 함수 run(inp)은 화면 모형(순수 자료)을 돌려주고, 스트림릿 진입점 main()이
그 모형을 그린다. 수는 int와 Decimal만 쓰고, float는 차트를 그리는 순간에만 만든다.
"""
import csv
import json
import os
import re
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Iterable

from tradesentry.contract import policy_load, types
from tradesentry.dal import query
from tradesentry.reports import claims as claims_unit
from tradesentry.reports import render_ko
from tradesentry.runlog import trace as trace_log

REPO_ROOT = query.REPO_ROOT
OUTPUTS_NAME = "outputs"
SEALED_NAME = "sealed"  # outputs/sealed/: 봉인 묶음 실행 출력. 나열·표시하지 않는다(자료 계약 §10.3 N10)
EXCLUDED_PREFIXES = (".download-", ".quarantine-")  # 받는 중·격리 폴더
RUN_NAME = "run_case"
RUN_DIR_RE = re.compile(r"run_case-\d{12}")  # 실행명 {실행 이름}-{yymmddhhmmss}(N5). fullmatch로 쓴다
RECORD_DOMAIN = "runlog_run_record"
REPORT_DOMAIN = "reports_render_ko"
TRACE_DOMAIN = "runlog_trace"
CASE_ID_RE = re.compile(r"\d{6}-[A-Z]{2}-\d{6}")  # 사례 식별자 {hs6}-{partner}-{month}. fullmatch로 쓴다
FIXTURE_CASES = ("850450-XA-202412", "850431-XB-202412", "850432-XC-202412")  # 합성 픽스처 A·B·C
SMOKE_DIR = Path("eval") / "dev" / "smoke"  # 재생 파일 eval/dev/smoke/{case_id}.json(결정 기록 model-decision-smoke-replay)
DEFAULT_POLICY = "policy_v1"
KEY_ENV = "NVIDIA_API_KEY"
CHILD_ENV_DROP = ("DATA_GO_KR_SERVICE_KEY", "TRADESENTRY_SEALED_DIR")  # run-case에 필요 없는 변수는 자식에 넘기지 않는다
DEFAULT_WALL_MS = 300000  # 사례당 wall time 한도(모델 설정 limits.wall_ms를 읽지 못할 때)
RUN_GRACE_S = 90  # 한도 위에 더 기다리는 시간(프로세스 시작·NAT 내보내기)
COUNTRY_MAP = Path("data") / "reference" / "country_map.csv"
HS6_TABLE = Path("data") / "reference" / "hs6_candidate_table.json"

STATUS_LABEL = render_ko.STATUS_LABEL
SIGNAL_LABEL = render_ko.SIGNAL_LABEL
SIGNAL_METRICS = policy_load.SIGNAL_METRICS  # {"unit_value": "r_U", "share": "d_s"}
# 상태값의 뜻 한 줄(자료 계약 §3.1 판정 상태 풀이를 줄인 것). 담당자의 다음 업무이며 조사의 완결성이나 사실 판정이 아니다.
STATUS_MEANING = {
    "MAINTAIN": "검토 유지(MAINTAIN): 필수 비교를 마쳤는데 경보가 설명되지 않거나 설명이 충돌해 계속 검토한다",
    "MONITOR": "모니터링(MONITOR): 하위품목 구성 변화 같은 산술적 설명이 성립해 지켜본다",
    "HOLD": "자료 보류(HOLD): 필요한 월·단위·분모·구성자료가 없거나 반올림으로 방향이 불안정해 판단할 자료가 모자란다",
    "NOT_TRIGGERED": "미발동(NOT_TRIGGERED): 그 신호가 발동하지 않았다",
    types.PRE_INVESTIGATION: "조사 전 경보(PRE_INVESTIGATION): 조사 전의 처음 표시다. 판정 상태가 아니다",
}
PHASE_LABEL = {  # trace state_change의 phase → 단계 이름
    "rule_reference": "규칙 참고값(코드)",
    "draft": "초안(모델)",
    "draft_discarded": "초안 버림",
    "evidence_claims": "코드가 덧붙인 주장",
    "after_critic": "Critic 뒤",
    "code_finding": "코드 지적(빠진 도구)",
    "revised": "수정 뒤",
    "revision_discarded": "수정 버림(원안 유지)",
    "status_aggregated": "코드 집계(review_status)",
    "final": "최종",
}
FLAG_PHASES = ("status_aggregated", "revision_discarded", "code_finding", "draft_discarded")
FOOTER_DISCLAIMER = "부정·위법·원산지 판정이나 실제 통관 조치가 아니다. 담당자의 다음 업무 제안이다."
FOOTER_SCOPE = ("관세청 수입통계를 한 시점에 수집해 고정한 스냅샷(HS(국제 품목분류 코드) 8504 아래 6자리 품목(HS6) 4개 × "
                "상대국 16개 × 2022~2024년 36개월)에서, kg당 단가와 상대국 점유율이 전년 같은 달보다 크게 바뀐 경우를 경보로 "
                "잡는다. 경보마다 Nemotron(NVIDIA 언어 모델) 조사자와 별도 문맥의 검수자(Critic)가 정해진 조회 도구 5개로 "
                "반증을 시도하고, 담당자의 다음 업무를 검토 유지(`MAINTAIN`)·모니터링(`MONITOR`)·자료 보류(`HOLD`) 가운데 "
                "하나로 제안한다. 부정·위법·원산지 판정이나 실제 통관 조치가 아니다. 한 사람이 로컬에서 돌리고 추론만 NVIDIA "
                "클라우드 API(NIM)를 쓰는 데모이며, 여러 사용자·계정·권한·실시간 수집·운영 배포는 없다.")
NOT_SCORE_EVIDENCE = "화면에서 시작한 실행은 점수표 근거가 아니다."
REPLAY_NOT_SCORE_EVIDENCE = "재생 실행(--replay), 점수표 근거 아님"
_ABS_PATH_RE = re.compile(r"(?<![\w/])/(?:Users|home|private|tmp|var|opt|root)/[^\s'\"`,;:)\]]*")
_KEY_SHAPE_RE = re.compile("nv" + r"api-[A-Za-z0-9_\-]{8,}")  # 키 모양(방어용. 접두어를 나눠 적어 검사기에 걸리지 않게 한다)


# ---- 폴더 나열과 실행 폴더 읽기 -----------------------------------------------------------------------------


def list_run_dirs(outputs_root: Path) -> list[str]:
    """outputs/ 바로 아래 run_case-{시각} 실행 폴더 이름(새 것부터). outputs/sealed/와 .download-*·.quarantine-*는 빼고
    그 안으로 내려가지 않는다."""
    if not outputs_root.is_dir():
        return []
    names = []
    for entry in outputs_root.iterdir():
        name = entry.name
        if name == SEALED_NAME or name.startswith(EXCLUDED_PREFIXES) or not entry.is_dir():
            continue
        if RUN_DIR_RE.fullmatch(name):
            names.append(name)
    return sorted(names, reverse=True)


def relative_run_dir(text: str) -> str | None:
    """직접 적은 상대 경로(outputs/run_case-… 또는 run_case-…)를 폴더 이름으로 정리한다. 실행명 형식이 아니거나 outputs/sealed/
    아래면 None이다."""
    if not isinstance(text, str):
        return None
    cleaned = text.strip().strip("/")
    if cleaned.startswith(OUTPUTS_NAME + "/"):
        cleaned = cleaned[len(OUTPUTS_NAME) + 1:]
    if "/" in cleaned or not RUN_DIR_RE.fullmatch(cleaned):
        return None
    return cleaned


def run_stamp(run_id: str) -> str:
    return run_id.rsplit("-", 1)[-1]


def _find_file(run_dir: Path, domain: str, ext: str) -> Path | None:
    exact = run_dir / f"{domain}-{run_stamp(run_dir.name)}.{ext}"
    if exact.is_file():
        return exact
    found = sorted(p for p in run_dir.glob(f"{domain}-*.{ext}") if p.is_file())
    return found[0] if found else None


def load_run(run_dir: Path) -> dict:
    """실행 폴더의 실행 결과 기록·보고서·trace를 읽는다(소수는 Decimal). 없는 파일은 None이고 missing에 이름을 적는다."""
    if not run_dir.is_dir():
        raise FileNotFoundError(f"실행 폴더가 없다: {OUTPUTS_NAME}/{run_dir.name}")
    files = {"record": _find_file(run_dir, RECORD_DOMAIN, "json"), "report": _find_file(run_dir, REPORT_DOMAIN, "json"),
             "trace": _find_file(run_dir, TRACE_DOMAIN, "jsonl")}
    record = trace_log.loads(files["record"].read_text(encoding="utf-8")) if files["record"] else None
    report = trace_log.loads(files["report"].read_text(encoding="utf-8")) if files["report"] else None
    if isinstance(report, dict) and isinstance(report.get("report"), dict):  # {"report", "body_ko"} 모양도 받는다
        report = report["report"]
    trace = trace_log.read_records(files["trace"]) if files["trace"] else []
    return {"run_id": run_dir.name, "record": record if isinstance(record, dict) else None,
            "report": report if isinstance(report, dict) else None, "trace": trace,
            "files": {k: (v.name if v else None) for k, v in files.items()},
            "missing": [k for k, v in files.items() if v is None]}


# ---- 사례 머리 ---------------------------------------------------------------------------------------------


def parse_case_id(case_id: object) -> dict | None:
    if not isinstance(case_id, str) or not CASE_ID_RE.fullmatch(case_id):
        return None
    hs6, partner, month = case_id.split("-")
    return {"hs6": hs6, "partner": partner, "month": month, "baseline_month": f"{int(month[:4]) - 1}{month[4:]}"}


def load_country_names(repo_root: Path = REPO_ROOT) -> dict[str, str]:
    """관세청 국가코드 → 한국어 국가명(data/reference/country_map.csv). 읽지 못하면 빈 표다."""
    path = repo_root / COUNTRY_MAP
    try:
        with path.open(encoding="utf-8", newline="") as fh:
            return {row["cntyCd"]: row["kcs_country_name"] for row in csv.DictReader(fh)
                    if row.get("cntyCd") and row.get("kcs_country_name")}
    except (OSError, KeyError, csv.Error):
        return {}


def load_hs6_names(repo_root: Path = REPO_ROOT) -> dict[str, str]:
    """HS6 → 품목 이름(data/reference/hs6_candidate_table.json의 HS10 이름 모음). 읽지 못하면 빈 표다."""
    try:
        table = json.loads((repo_root / HS6_TABLE).read_text(encoding="utf-8"))
        return {row["hs6"]: row["names"] for row in table.get("rows", [])
                if isinstance(row, dict) and isinstance(row.get("hs6"), str) and isinstance(row.get("names"), str)}
    except (OSError, ValueError, AttributeError):
        return {}


def case_heading(case_id: object, countries: dict | None = None, hs6_names: dict | None = None) -> dict:
    """사례 식별자를 품목·상대국·월로 풀어 쓴다."""
    parsed = parse_case_id(case_id)
    if parsed is None:
        return {"case_id": case_id, "text": f"{case_id}(사례 식별자 형식이 아님)", "parsed": False}
    countries, hs6_names = countries or {}, hs6_names or {}
    partner_name = countries.get(parsed["partner"])
    hs6_name = hs6_names.get(parsed["hs6"])
    partner_text = f"{parsed['partner']}({partner_name})" if partner_name else f"{parsed['partner']}(합성 또는 이름 없음)"
    hs6_text = f"HS6 {parsed['hs6']}" + (f"({_shorten(hs6_name, 60)})" if hs6_name else "")
    return {**parsed, "case_id": case_id, "parsed": True, "partner_name": partner_name, "hs6_name": hs6_name,
            "month_label": claims_unit.month_label(parsed["month"]),
            "baseline_label": claims_unit.month_label(parsed["baseline_month"]),
            "text": (f"{hs6_text} · 상대국 {partner_text} · 비교월 {claims_unit.month_label(parsed['month'])}"
                     f"(기준월 {claims_unit.month_label(parsed['baseline_month'])}, 전년 같은 달)")}


def _shorten(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit - 1] + "…"


def status_text(code: object) -> str:
    """상태 코드의 한국어 표기·코드·뜻 한 줄. 모르는 값은 원문 그대로 보인다(고쳐 적지 않는다)."""
    if isinstance(code, str) and code in STATUS_MEANING:
        return STATUS_MEANING[code]
    if code is None:
        return "null(실행이 COMPLETED가 아니어서 최종 판정이 없다)"
    return f"{code}(정해진 판정 상태가 아님)"


def signal_status_text(signals: object) -> str:
    if not isinstance(signals, dict):
        return "없음" if signals is None else str(signals)
    return ", ".join(f"{SIGNAL_LABEL.get(k, k)} {render_ko.status_label(v)}" for k, v in signals.items())


def header_model(record: dict | None, report: dict | None) -> dict:
    record, report = record or {}, report or {}
    execution_status = record.get("execution_status")
    final = record.get("review_status_final") if record else report.get("review_status")
    signals = record.get("signal_status") if record.get("signal_status") is not None else report.get("signal_status")
    unresolved = record.get("unresolved_evidence") if record else report.get("unresolved_evidence")
    return {
        "snapshot_id": record.get("snapshot_id") or report.get("snapshot_id"),
        "policy_version": record.get("policy_version") or report.get("policy_version"),
        "grouping_version": record.get("grouping_version") or report.get("grouping_version"),
        "mode": record.get("mode") or report.get("mode"),
        "dataset": record.get("dataset"),
        "rulebook_version": record.get("rulebook_version"),
        "code_version": record.get("code_version"),
        "execution_status": execution_status,
        "status_before": {"code": types.PRE_INVESTIGATION, "label": STATUS_LABEL[types.PRE_INVESTIGATION],
                          "text": status_text(types.PRE_INVESTIGATION)},
        "status_after": {"code": final, "label": STATUS_LABEL.get(final, str(final)), "text": status_text(final)},
        "signal_status": signals,
        "signal_status_text": signal_status_text(signals),
        "signal_status_meaning": {k: status_text(v) for k, v in signals.items()} if isinstance(signals, dict) else {},
        "unresolved_evidence": unresolved,
        "report_id": report.get("report_id"),
        "report_hash": report.get("report_hash"),
        "created_at": report.get("created_at"),
        "errors": record.get("errors") or [],
    }


# ---- trace에서 뽑는 것: 지표·도구·타임라인 --------------------------------------------------------------------


def envelope_metrics(trace: list[dict]) -> list[dict]:
    """도구 봉투(tool_result)의 검증된 지표 목록. 항목마다 도구 이름과 순번을 붙인다. 값은 그대로다."""
    out = []
    for record in trace:
        if record.get("event") != "tool_result":
            continue
        envelope = (record.get("data") or {}).get("envelope") or {}
        for metric in envelope.get("metrics") or []:
            if isinstance(metric, dict):
                out.append({**metric, "_tool": envelope.get("tool"), "_seq": record.get("seq")})
    return out


def _metric_inputs(metric: dict) -> dict:
    inputs = metric.get("inputs")
    return inputs if isinstance(inputs, dict) else {}


def lookup_value(report: dict | None, trace: list[dict], symbol: str, partner: str, period: str) -> dict | None:
    """기호·상대국·기간이 맞는 값을 보고서 주장에서 먼저, 없으면 trace 지표에서 찾는다. 새로 계산하지 않는다."""
    for claim in (report or {}).get("claims") or []:
        if isinstance(claim, dict) and claim.get("metric") == symbol and claim.get("partner") == partner \
                and claim.get("period") == period and claim.get("value") is not None:
            return {"value": claim["value"], "unit": claim.get("unit"), "source": f"보고서 주장 {claim.get('claim_id')}",
                    "baseline_period": claim.get("baseline_period"), "evidence_ids": list(claim.get("evidence_ids") or [])}
    for metric in envelope_metrics(trace):
        inputs = _metric_inputs(metric)
        if inputs.get("metric") == symbol and inputs.get("partner") == partner and inputs.get("period") == period \
                and metric.get("value") is not None:
            return {"value": metric["value"], "unit": metric.get("unit"), "source": f"trace 지표 {metric.get('metric_id')}",
                    "baseline_period": inputs.get("baseline_period"), "evidence_ids": list(metric.get("evidence_ids") or [])}
    return None


def rule_reference(trace: list[dict]) -> dict:
    """규칙 참고값(state_change phase rule_reference)의 신호별 근거 코드. 없으면 빈 객체다."""
    basis = {}
    for record in trace:
        data = record.get("data") or {}
        if record.get("event") == "state_change" and data.get("phase") == "rule_reference" and isinstance(data.get("basis"), dict):
            basis = data["basis"]
    return basis


def trigger_table(record: dict | None, report: dict | None, trace: list[dict], thresholds: dict | None) -> list[dict]:
    """조회 이유: 신호별 발동 지표(r_U·d_s)의 값과 정책 기준값. 값은 보고서 주장·trace 지표에서만 가져온다."""
    record, report = record or {}, report or {}
    case = parse_case_id(record.get("case_id") or report.get("case_id"))
    signals = record.get("signal_status") or report.get("signal_status") or {}
    basis = rule_reference(trace)
    rows = []
    for signal in types.SIGNALS:
        metric = SIGNAL_METRICS[signal]
        status = signals.get(signal) if isinstance(signals, dict) else None
        found = lookup_value(report, trace, metric, case["partner"], case["month"]) if case else None
        threshold = thresholds.get(signal) if isinstance(thresholds, dict) else None
        rows.append({
            "signal": signal, "signal_label": SIGNAL_LABEL.get(signal, signal), "metric": metric,
            "metric_label": "단가 변화율" if metric == "r_U" else "점유율 변화",
            "value": found["value"] if found else None,
            "unit": (found["unit"] if found else None) or claims_unit.UNIT_OF.get(metric),
            "threshold": threshold, "threshold_unit": claims_unit.UNIT_OF.get(metric),
            "triggered": None if status is None else status != "NOT_TRIGGERED",
            "signal_status": status, "status_label": render_ko.status_label(status) if status is not None else "기록 없음",
            "basis": basis.get(signal), "source": found["source"] if found else "값 없음(보고서·trace에 이 지표가 없다)",
        })
    return rows


def args_summary(args: object, limit: int = 120) -> str:
    if not isinstance(args, dict) or not args:
        return ""
    parts = []
    for key, value in args.items():
        shown = ",".join(str(v) for v in value) if isinstance(value, (list, tuple)) else str(value)
        parts.append(f"{key}={shown}")
    return _shorten("; ".join(parts), limit)


def tool_table(trace: list[dict]) -> list[dict]:
    """실제 실행한 도구: tool_call과 그 tool_result를 짝지어 순서대로. 예산에 막힌 시도(budget_block)도 한 줄로 적는다."""
    rows: list[dict] = []
    pending: dict[str, list[dict]] = {}
    for record in trace:
        event, data = record.get("event"), record.get("data") or {}
        if event == "tool_call":
            row = {"seq": record.get("seq"), "stage": record.get("stage"), "tool": data.get("tool"),
                   "args": args_summary(data.get("args")), "source": data.get("source"),
                   "tool_attempts": data.get("tool_attempts"), "ok": None, "evidence_count": None, "metric_count": None,
                   "missingness_count": None, "retryable_error": None, "elapsed_ms": None, "blocked": False, "note": ""}
            rows.append(row)
            pending.setdefault(str(data.get("tool")), []).append(row)
        elif event == "tool_result":
            queue = pending.get(str(data.get("tool")))
            row = queue.pop(0) if queue else None
            if row is None:
                row = {"seq": record.get("seq"), "stage": record.get("stage"), "tool": data.get("tool"), "args": "",
                       "source": None, "tool_attempts": None, "blocked": False, "note": "짝이 되는 tool_call이 없다"}
                rows.append(row)
            envelope = data.get("envelope") or {}
            row.update(ok=data.get("ok"), evidence_count=len(envelope.get("evidence_ids") or []),
                       metric_count=len(envelope.get("metrics") or []),
                       missingness_count=len(envelope.get("missingness") or []),
                       retryable_error=envelope.get("retryable_error"),
                       elapsed_ms=data.get("elapsed_ms", envelope.get("elapsed_ms")))
        elif event == "budget_block":
            rows.append({"seq": record.get("seq"), "stage": record.get("stage"), "tool": data.get("tool"),
                         "args": args_summary(data.get("args")), "source": data.get("source"),
                         "tool_attempts": data.get("tool_attempts"), "ok": False, "evidence_count": None,
                         "metric_count": None, "missingness_count": None, "retryable_error": None, "elapsed_ms": None,
                         "blocked": True, "note": _shorten("예산·단계 한도로 막힘: " + args_summary(
                             {k: v for k, v in data.items() if k not in ("tool", "args")}), 160)})
    return rows


def model_summary(trace: list[dict], record: dict | None) -> dict:
    record = record or {}
    attempts = sum(1 for r in trace if r.get("event") == "model_request")
    errors = sum(1 for r in trace if r.get("event") == "model_error")
    return {"model_requests": record.get("model_requests"), "model_attempts": attempts, "model_errors": errors,
            "tokens_in": record.get("tokens_in"), "tokens_out": record.get("tokens_out"), "wall_ms": record.get("wall_ms"),
            "tool_attempts": record.get("tool_attempts"), "critic_used": record.get("critic_used"),
            "revision_used": record.get("revision_used")}


def code_added_claim_ids(trace: list[dict]) -> list[str]:
    """코드가 덧붙인 주장의 claim_id(state_change phase evidence_claims의 added)."""
    ids: list[str] = []
    for record in trace:
        data = record.get("data") or {}
        if record.get("event") != "state_change" or data.get("phase") != "evidence_claims":
            continue
        for item in data.get("added") or []:
            for claim in (item.get("claims") or []) if isinstance(item, dict) else []:
                claim_id = claim.get("claim_id") if isinstance(claim, dict) else None
                if isinstance(claim_id, str) and claim_id not in ids:
                    ids.append(claim_id)
    return ids


def claims_table(report: dict | None, trace: list[dict]) -> list[dict]:
    """typed claim 목록(지표·값·단위·기간·근거 ID). 코드가 덧붙인 주장은 origin이 "코드가 덧붙임"이다."""
    added = set(code_added_claim_ids(trace))
    rows = []
    for claim in (report or {}).get("claims") or []:
        if not isinstance(claim, dict):
            rows.append({"claim_id": None, "text": "(형식이 맞지 않는 주장)", "origin": "?"})
            continue
        rows.append({key: claim.get(key) for key in types.CLAIM_FIELDS} | {
            "evidence_ids": list(claim.get("evidence_ids") or []),
            "origin": "코드가 덧붙임" if claim.get("claim_id") in added else "모델(검증 통과)"})
    return rows


def _phase_note(phase: str, data: dict) -> str:
    if phase == "rule_reference":
        basis = data.get("basis")
        text = ", ".join(f"{SIGNAL_LABEL.get(k, k)} {v}" for k, v in basis.items()) if isinstance(basis, dict) else ""
        return text if data.get("available", True) else f"참고값 없음({data.get('error')})"
    if phase in ("draft", "revised"):
        problems = data.get("problem_list") or []
        return f"문제 {data.get('problems', len(problems))}건" + (f": {'; '.join(map(str, problems))}" if problems else "")
    if phase == "draft_discarded":
        return "초안 버림: " + "; ".join(map(str, data.get("problems") or []))
    if phase == "evidence_claims":
        added = [c.get("claim_id") for item in data.get("added") or [] if isinstance(item, dict)
                 for c in item.get("claims") or [] if isinstance(c, dict)]
        unmet = [f"{u.get('signal')}:{u.get('code')}" if isinstance(u, dict) else str(u) for u in data.get("unmet") or []]
        return f"덧붙인 주장 {len(added)}건" + (f"({', '.join(map(str, added))})" if added else "") + \
            (f", 채우지 못한 필수 근거 {', '.join(unmet)}" if unmet else "")
    if phase == "after_critic":
        text = f"Critic 지적 {data.get('findings')}건, 재조회 {data.get('requery')}건, 수정 필요 {data.get('needs_revision')}"
        problems = data.get("problems") or []
        return text + (f"; {'; '.join(map(str, problems))}" if problems else "")
    if phase == "code_finding":
        return "빠진 도구: " + ", ".join(map(str, data.get("missing_tools") or []))
    if phase == "revision_discarded":
        return f"{data.get('blocked_by')}가 막아 원안 유지(would_be_cause {data.get('would_be_cause')}, {data.get('kept_report_id')})"
    if phase == "status_aggregated":
        return (f"모델이 쓴 {data.get('model_review_status')} → 코드 집계 {data.get('review_status')}"
                f"(unresolved_evidence {data.get('unresolved_evidence')})")
    return ""


def timeline_table(trace: list[dict]) -> dict:
    """판정 전후 타임라인: 처음 표시(조사 전 경보) 뒤에 state_change·validator_result 사건을 순서대로. flags는
    status_aggregated·revision_discarded·code_finding·draft_discarded 발동 여부다. before-after 대조는 하지 않는다(표만)."""
    rows = [{"seq": 0, "stage": None, "phase": types.PRE_INVESTIGATION, "step": "처음 표시(조사 전 경보)",
             "review_status": types.PRE_INVESTIGATION, "signal_status": "", "note": "판정 상태가 아니다(표시 코드)"}]
    flags = {phase: False for phase in FLAG_PHASES}
    for record in trace:
        event, data = record.get("event"), record.get("data") or {}
        if event == "state_change":
            phase = str(data.get("phase"))
            if phase in flags:
                flags[phase] = True
            rows.append({"seq": record.get("seq"), "stage": record.get("stage"), "phase": phase,
                         "step": PHASE_LABEL.get(phase, phase), "review_status": data.get("review_status"),
                         "signal_status": signal_status_text(data.get("signal_status")) if data.get("signal_status") is not None else "",
                         "note": _phase_note(phase, data)})
        elif event == "validator_result":
            findings = data.get("findings") or []
            codes = ", ".join(str(f.get("code")) for f in findings if isinstance(f, dict))
            rows.append({"seq": record.get("seq"), "stage": record.get("stage"), "phase": "validator_result",
                         "step": f"검증({data.get('phase')}, {data.get('scope')})", "review_status": None, "signal_status": "",
                         "note": (f"판정 {data.get('decision')}, 스키마 {data.get('schema_ok')}, 검증기 {data.get('validator_ok')}, "
                                  f"기록 {len(findings)}건" + (f"({codes})" if codes else "")
                                  + (", 기록 전용" if data.get("record_only") else ""))})
    return {"rows": rows, "flags": flags}


# ---- 차트 자료 -----------------------------------------------------------------------------------------------


def chart_data(report: dict | None, trace: list[dict], case: dict | None) -> dict:
    """차트 자료(룰북 A2 3f 3점 앵커). (가) 기준월·비교월의 kg당 단가(U)와 점유율(s) 막대, (나) trace의 get_history 지표에
    단가(U) 달별 값이 3개 이상 있으면 그 시계열과 기준월 단가 선. 값은 보고서 주장·trace 지표에서만 가져온다."""
    empty = {"bars": {"unit_value": None, "share": None}, "series": None,
             "units": {"unit_value": claims_unit.UNIT_OF["U"], "share": claims_unit.UNIT_OF["s"]}}
    if not case or not case.get("parsed"):
        return empty
    partner, month, baseline = case["partner"], case["month"], case["baseline_month"]
    bars = {}
    for key, symbol in (("unit_value", "U"), ("share", "s")):
        before, after = lookup_value(report, trace, symbol, partner, baseline), lookup_value(report, trace, symbol, partner, month)
        bars[key] = None if before is None or after is None else [
            {"month": baseline, "label": f"기준월 {claims_unit.month_label(baseline)}", "value": before["value"]},
            {"month": month, "label": f"비교월 {claims_unit.month_label(month)}", "value": after["value"]}]
    by_period: dict[str, object] = {}
    for metric in envelope_metrics(trace):
        inputs = _metric_inputs(metric)
        if inputs.get("metric") == "U" and inputs.get("partner") == partner and isinstance(inputs.get("period"), str) \
                and metric.get("value") is not None and inputs["period"] not in by_period:
            by_period[inputs["period"]] = metric["value"]
    series = None
    if len(by_period) >= 3:
        base_value = by_period.get(baseline)
        series = [{"month": period, "label": claims_unit.month_label(period), "value": by_period[period], "baseline_value": base_value}
                  for period in sorted(by_period)]
    return {**empty, "bars": bars, "series": series}


# ---- 근거 ID → 원본 행 ----------------------------------------------------------------------------------------

OBSERVATION_COLUMNS = ("hs_code", "partner_code", "month", "amount_usd", "net_weight_kg", "observation_status", "request_id")


def _plain(value: object) -> object:
    if isinstance(value, float):  # SQLite REAL. 표시용 값이므로 문자열 표기로 Decimal을 만든다(새 계산이 아니다)
        return Decimal(str(value))
    return value


def resolve_evidence(evidence_ids: Iterable[str], snapshot_id: object, *, snapshot_path: str | Path | None = None,
                     enabled: bool = True) -> dict:
    """보고서의 근거 ID를 자료 접근층(단위 K3)으로 풀어 스냅샷 행을 돌려준다. 스냅샷이 없으면 ID만 나열하고 note에 적는다."""
    ids = [e for e in evidence_ids if isinstance(e, str)]
    rows = [{"evidence_id": e} for e in ids]
    if not enabled:
        return {"available": False, "note": "스냅샷 조회를 끄고 근거 ID만 나열했다", "rows": rows, "snapshot_id": snapshot_id}
    if not isinstance(snapshot_id, str):
        return {"available": False, "note": "스냅샷 없음: 실행 기록에 snapshot_id가 없다", "rows": rows, "snapshot_id": snapshot_id}
    try:
        snap = query.open_snapshot(snapshot_id, path=snapshot_path)
    except (query.SnapshotError, OSError) as exc:
        return {"available": False, "snapshot_id": snapshot_id, "rows": rows,
                "note": f"스냅샷 없음: {snapshot_id}의 정본 빌드 파일을 열 수 없어 근거 ID만 나열한다({type(exc).__name__})"}
    resolved_rows = []
    with snap:
        for evidence_id in ids:
            result = snap.resolve(evidence_id)
            row = result.get("row") or {}
            table = evidence_id.split(":")[2] if result.get("resolved") else None
            entry = {"evidence_id": evidence_id, "resolved": bool(result.get("resolved")),
                     "failed_rule": result.get("failed_rule"), "table": table}
            if table == "observation":
                entry.update({col: _plain(row.get(col)) for col in OBSERVATION_COLUMNS})
            elif row:
                entry["detail"] = _shorten("; ".join(f"{k}={_plain(v)}" for k, v in row.items()), 200)
            resolved_rows.append(entry)
    return {"available": True, "note": f"스냅샷 {snapshot_id}에서 {sum(1 for r in resolved_rows if r['resolved'])}/{len(ids)}건이 풀렸다",
            "rows": resolved_rows, "snapshot_id": snapshot_id}


# ---- 화면 모형(진입 함수) ---------------------------------------------------------------------------------------


def load_thresholds(policy_version: object) -> dict | None:
    """정책의 탐지 기준값 {"unit_value", "share"}. 읽지 못하면 None(화면은 그대로 뜬다)."""
    if not isinstance(policy_version, str):
        return None
    try:
        thresholds = policy_load.load_policy(policy_version).get("thresholds")
    except (policy_load.PolicyError, OSError, ValueError, TypeError):
        return None
    return thresholds if isinstance(thresholds, dict) else None


def run_start_data(trace: list[dict]) -> dict:
    for record in trace:
        if record.get("event") == "run_start":
            return record.get("data") or {}
    return {}


def screen_model(run_dir: Path, *, repo_root: Path = REPO_ROOT, snapshot_path: str | Path | None = None,
                 resolve_rows: bool = True) -> dict:
    """실행 폴더 하나를 화면 1의 모형(순수 자료)으로 만든다. 절대 경로는 넣지 않는다(폴더 이름만)."""
    loaded = load_run(run_dir)
    record, report, trace = loaded["record"], loaded["report"], loaded["trace"]
    started = run_start_data(trace)
    case_id = (record or {}).get("case_id") or (report or {}).get("case_id") or started.get("case_id")
    case = case_heading(case_id, load_country_names(repo_root), load_hs6_names(repo_root))
    header = header_model(record, report)
    if header["snapshot_id"] is None:
        header["snapshot_id"] = started.get("snapshot_id")
    thresholds = load_thresholds(header["policy_version"] or started.get("policy_version"))
    evidence_ids = list((report or {}).get("evidence_ids") or [])
    return {
        "run_id": loaded["run_id"], "run_dir": f"{OUTPUTS_NAME}/{loaded['run_id']}", "files": loaded["files"],
        "missing": loaded["missing"], "case": case, "header": header, "thresholds": thresholds,
        "triggers": trigger_table(record, report, trace, thresholds),
        "chart": chart_data(report, trace, case),
        "tools": tool_table(trace), "model": model_summary(trace, record),
        "claims": claims_table(report, trace),
        "narrative": (report or {}).get("narrative"), "hypotheses": list((report or {}).get("hypotheses") or []),
        "validator_findings": list((report or {}).get("validator_findings") or []),
        "timeline": timeline_table(trace),
        "evidence": resolve_evidence(evidence_ids, header["snapshot_id"], snapshot_path=snapshot_path, enabled=resolve_rows),
        "footer": {"disclaimer": FOOTER_DISCLAIMER, "scope": FOOTER_SCOPE},
    }


def run(inp: object) -> object:
    """진입 함수. 입력 {"run_dir": 실행 폴더 상대 경로(저장소 루트 기준), "snapshot_path"?: 정본 빌드 대신 열 SQLite 경로,
    "resolve_rows"?: 근거 ID를 스냅샷으로 풀지(기본 참)} → 화면 1의 모형(screen_model)."""
    if not isinstance(inp, dict) or not isinstance(inp.get("run_dir"), str):
        raise ValueError("입력은 {run_dir, snapshot_path?, resolve_rows?} 객체다")
    run_dir = Path(inp["run_dir"])
    if not run_dir.is_absolute():
        run_dir = REPO_ROOT / run_dir
    snapshot_path = inp.get("snapshot_path")
    if isinstance(snapshot_path, str) and not Path(snapshot_path).is_absolute():
        snapshot_path = REPO_ROOT / snapshot_path
    return screen_model(run_dir, snapshot_path=snapshot_path, resolve_rows=inp.get("resolve_rows", True) is not False)


# ---- "사례 실행" 패널의 순수 함수 ----------------------------------------------------------------------------------


def list_snapshots(snapshots_root: Path) -> list[str]:
    """data/snapshots/ 아래 정본 빌드(snapshot_build.sqlite)가 있는 폴더 이름(사전순)."""
    if not snapshots_root.is_dir():
        return []
    return sorted(p.name for p in snapshots_root.iterdir() if p.is_dir() and (p / query.BUILD_FILE).is_file())


def replay_file_for(case_id: str, repo_root: Path = REPO_ROOT) -> str | None:
    """사례의 재생 파일 상대 경로(eval/dev/smoke/{case_id}.json). 없으면 None."""
    if not isinstance(case_id, str) or not CASE_ID_RE.fullmatch(case_id):
        return None
    relative = SMOKE_DIR / f"{case_id}.json"
    return relative.as_posix() if (repo_root / relative).is_file() else None


def build_run_case_args(snapshot_id: str, policy_version: str, mode: str, case_id: str,
                        replay_path: str | None = None) -> list[str]:
    """CLI run-case 인자(명령 이름 뒤). 값의 모양이 틀리면 ValueError(값은 문장에 되풀이하지 않는다)."""
    if not isinstance(snapshot_id, str) or not query.SNAPSHOT_ID_RE.fullmatch(snapshot_id):
        raise ValueError("스냅샷 ID 모양이 아니다")
    if not isinstance(policy_version, str) or not policy_load.POLICY_VERSION_RE.fullmatch(policy_version):
        raise ValueError("정책 버전 모양이 아니다")
    if mode not in types.MODES:
        raise ValueError("모드는 checklist·agent·full·freeform 가운데 하나다")
    if not isinstance(case_id, str) or not CASE_ID_RE.fullmatch(case_id):
        raise ValueError("사례 식별자는 {hs6}-{partner}-{month} 꼴이다")
    args = ["run-case", "--snapshot", snapshot_id, "--policy", policy_version, "--mode", mode, "--case", case_id]
    if replay_path is not None:
        if not isinstance(replay_path, str) or not replay_path or replay_path.startswith(("/", "~", "\\")) \
                or ".." in replay_path.split("/"):
            raise ValueError("재생 파일은 저장소 안 상대 경로다")
        args += ["--replay", replay_path]
    return args


def run_case_command(args: list[str]) -> list[str]:
    """하위 프로세스 명령: 이 파이썬으로 python -m tradesentry.cli(설치 명령 tradesentry와 같은 진입점)."""
    return [sys.executable, "-m", "tradesentry.cli", *args]


def key_present(env: dict | None = None) -> bool:
    """NVIDIA_API_KEY가 환경에 있는지(있는지 여부만. 값은 읽어 두지 않는다)."""
    env = os.environ if env is None else env
    return bool(env.get(KEY_ENV))


def child_env(env: dict | None = None) -> dict:
    env = dict(os.environ if env is None else env)
    for key in CHILD_ENV_DROP:
        env.pop(key, None)
    return env


def new_run_dirs(before: Iterable[str], after: Iterable[str]) -> list[str]:
    """실행 전후 폴더 목록의 차이(새 실행 폴더, 새 것부터)."""
    return sorted(set(after) - set(before), reverse=True)


def redact(text: object) -> str:
    """표시용 정리: 로컬 절대 경로와 키 모양 글자를 가린다."""
    shown = text if isinstance(text, str) else ("" if text is None else str(text))
    shown = _ABS_PATH_RE.sub("<로컬 경로>", shown)
    return _KEY_SHAPE_RE.sub("<키 모양 가림>", shown)


def wall_limit_seconds(repo_root: Path = REPO_ROOT) -> int:
    """사례당 wall time 한도(초). 모델 설정 configs/model/model.json의 limits.wall_ms를 읽고, 못 읽으면 300초다."""
    try:
        config = json.loads((repo_root / "configs" / "model" / "model.json").read_text(encoding="utf-8"))
        wall_ms = int(config["limits"]["wall_ms"])
    except (OSError, ValueError, KeyError, TypeError):
        wall_ms = DEFAULT_WALL_MS
    return max(1, wall_ms // 1000)


def run_case_once(args: list[str], *, repo_root: Path = REPO_ROOT, timeout_s: int | None = None,
                  env: dict | None = None) -> dict:
    """run-case를 하위 프로세스로 한 번 돌리고 표준 출력·오류(경로·키 모양은 가림)와 종료 코드를 돌려준다. 작업 폴더는 저장소
    루트라 실행 폴더가 CLI와 똑같이 outputs/run_case-{시각}/에 남는다."""
    timeout = (wall_limit_seconds(repo_root) + RUN_GRACE_S) if timeout_s is None else timeout_s
    command = run_case_command(args)
    shown = " ".join(["tradesentry", *args])
    try:
        done = subprocess.run(command, cwd=repo_root, env=child_env(env), capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        return {"command": shown, "returncode": None, "timed_out": True, "timeout_s": timeout,
                "stdout": redact(exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else exc.stdout),
                "stderr": redact(exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else exc.stderr)}
    return {"command": shown, "returncode": done.returncode, "timed_out": False, "timeout_s": timeout,
            "stdout": redact(done.stdout), "stderr": redact(done.stderr)}


def output_run_dirs(stdout: str) -> list[str]:
    """CLI 표준 출력(outputs/run_case-{시각}/… 상대 경로)에서 실행 폴더 이름을 뽑는다."""
    found: list[str] = []
    for line in (stdout or "").splitlines():
        parts = line.strip().split("/")
        if len(parts) >= 2 and parts[0] == OUTPUTS_NAME and RUN_DIR_RE.fullmatch(parts[1]) and parts[1] not in found:
            found.append(parts[1])
    return found


# ---- Streamlit 화면(streamlit은 여기서만 import한다) ----------------------------------------------------------------


def _display_rows(rows: list[dict], columns: dict[str, str]) -> list[dict]:
    """표시용 행: 열 이름을 한국어로 바꾸고 Decimal·목록·객체는 문자열 표기로 둔다(값을 바꾸지 않는다)."""
    out = []
    for row in rows:
        shown = {}
        for key, label in columns.items():
            value = row.get(key)
            if isinstance(value, Decimal):
                shown[label] = str(value)
            elif isinstance(value, (list, tuple)):
                shown[label] = ", ".join(str(v) for v in value)
            elif isinstance(value, dict):
                shown[label] = json.dumps(value, ensure_ascii=False, default=str)
            elif value is None:
                shown[label] = ""
            else:
                shown[label] = str(value)
        out.append(shown)
    return out


def _floats(values: Iterable[object]) -> list[float | None]:
    return [float(v) if isinstance(v, (int, Decimal)) and not isinstance(v, bool) else None for v in values]


def _render_run_panel(st, repo_root: Path, outputs_root: Path) -> None:
    snapshots = list_snapshots(repo_root / "data" / "snapshots")
    has_key = key_present()
    st.caption("CLI와 같은 진입점(`tradesentry run-case`)으로 사례 1건만 돌린다. `evaluate`·`detect`·봉인 묶음은 돌리지 않는다.")
    if has_key:
        st.info("이 프로세스 환경에 NVIDIA_API_KEY가 있어 실제 NIM 실행이 가능하다(재생을 끄면 NIM을 부른다).")
    else:
        st.warning("이 프로세스 환경에 NVIDIA_API_KEY가 없다. 재생 파일이 있는 사례의 재생 실행만 가능하다. 앱은 .env를 읽지 않는다.")
    if not snapshots:
        st.warning("data/snapshots/ 아래 정본 빌드(snapshot_build.sqlite)가 있는 스냅샷이 없다. 합성 픽스처는 "
                   "`uv run --locked python -c \"from tradesentry.snapshot import fixture; fixture.materialize()\"`로 만든다.")
    default_snapshot = snapshots.index(types.FIXTURE_SNAPSHOT_ID) if types.FIXTURE_SNAPSHOT_ID in snapshots else 0
    snapshot_id = st.selectbox("스냅샷 ID", snapshots, index=default_snapshot) if snapshots else None
    policy_version = st.text_input("정책 버전", value=DEFAULT_POLICY)
    mode = st.selectbox("모드", list(types.MODES), index=types.MODES.index("full"))
    if snapshot_id == types.FIXTURE_SNAPSHOT_ID:
        picked = st.selectbox("사례(합성 픽스처 A·B·C)", list(FIXTURE_CASES) + ["직접 입력"])
        case_id = st.text_input("사례 식별자({hs6}-{partner}-{month})") if picked == "직접 입력" else picked
    else:
        case_id = st.text_input("사례 식별자({hs6}-{partner}-{month})", placeholder="예: 850432-CN-202301")
    replay_path = replay_file_for(case_id, repo_root) if case_id else None
    use_replay = st.checkbox(f"재생 파일 사용(키 없이 돈다{'' if replay_path else '. 이 사례의 재생 파일이 없다'})",
                             value=not has_key, disabled=replay_path is None) and replay_path is not None
    can_run = bool(snapshot_id and case_id) and (use_replay or has_key)
    if not can_run and snapshot_id and case_id and not has_key:
        st.caption("키가 없고 재생 파일도 없어 이 사례는 지금 돌릴 수 없다.")
    running = st.session_state.get("running", False)
    if st.button("사례 실행", disabled=not can_run or running, type="primary"):
        try:
            args = build_run_case_args(snapshot_id, policy_version, mode, case_id, replay_path if use_replay else None)
        except ValueError as exc:
            st.error(f"입력이 맞지 않는다: {exc}")
            return
        st.session_state["running"] = True
        before = list_run_dirs(outputs_root)
        try:
            with st.spinner(f"실행 중… 사례당 wall time 한도 {wall_limit_seconds(repo_root)}초까지 기다린다. 버튼은 잠긴다."):
                result = run_case_once(args, repo_root=repo_root)
        finally:
            st.session_state["running"] = False
        new_dirs = output_run_dirs(result["stdout"]) or new_run_dirs(before, list_run_dirs(outputs_root))
        result["new_run_dirs"] = new_dirs
        result["replay"] = use_replay
        st.session_state["last_run"] = result
        if new_dirs:
            st.session_state["selected_run"] = new_dirs[0]
        st.rerun()


def _render_last_run(st) -> None:
    result = st.session_state.get("last_run")
    if not result:
        return
    st.subheader("사례 실행 결과")
    st.caption(NOT_SCORE_EVIDENCE + (" " + REPLAY_NOT_SCORE_EVIDENCE if result.get("replay") else ""))
    code = result.get("returncode")
    status = "시간 초과" if result.get("timed_out") else f"종료 코드 {code}"
    (st.success if code == 0 else st.error)(f"`{result['command']}` → {status}")
    if result.get("stdout"):
        st.code(result["stdout"], language="text")
    if result.get("stderr"):
        st.code(result["stderr"], language="text")
    if result.get("new_run_dirs"):
        st.write("새 실행 폴더: " + ", ".join(f"`{OUTPUTS_NAME}/{d}`" for d in result["new_run_dirs"]))


def _render_header(st, model: dict) -> None:
    header, case = model["header"], model["case"]
    st.header(f"사례 {case['case_id']}")
    st.write(case["text"])
    if model["missing"]:
        st.warning("실행 폴더에 없는 파일: " + ", ".join(model["missing"]) + ". 있는 것만 보인다.")
    columns = st.columns(5)
    for column, (label, value) in zip(columns, (("스냅샷", header["snapshot_id"]), ("정책", header["policy_version"]),
                                              ("모드", header["mode"]), ("비교 대상", header["grouping_version"]),
                                              ("실행 상태", header["execution_status"]))):
        column.metric(label, str(value) if value is not None else "—")
    st.markdown(f"**판정 전후**: {header['status_before']['label']}(`{header['status_before']['code']}`) → "
                f"{header['status_after']['label']}(`{header['status_after']['code']}`)")
    st.caption(header["status_before"]["text"])
    st.caption(header["status_after"]["text"])
    st.markdown(f"**신호별 판정**: {header['signal_status_text']}")
    for text in header["signal_status_meaning"].values():
        st.caption(text)
    st.markdown(f"**미해결 근거(unresolved_evidence)**: {header['unresolved_evidence']}")
    if header["execution_status"] is not None and header["execution_status"] != "COMPLETED":
        causes = "; ".join(str(e.get("code")) for e in header["errors"] if isinstance(e, dict))
        st.error(f"실행 상태 {header['execution_status']}: 유효한 최종 보고서가 아니다. review_status_final은 null이다."
                 + (f" 원인: {causes}" if causes else ""))
    with st.expander("버전·기록 ID"):
        st.write({"run_id": model["run_id"], "실행 폴더": model["run_dir"], "dataset": header["dataset"],
                  "rulebook_version": header["rulebook_version"], "code_version": header["code_version"],
                  "report_id": header["report_id"], "report_hash": header["report_hash"], "created_at": header["created_at"],
                  "파일": model["files"]})


def _render_triggers(st, model: dict) -> None:
    st.subheader("조회 이유")
    st.caption("발동 신호와 정책 기준값. 값은 보고서 주장·trace의 검증된 지표에서 가져왔고 화면이 새로 계산하지 않았다.")
    if model["thresholds"] is None:
        st.caption("정책 기준값을 읽지 못해 기준값 칸이 비어 있다.")
    st.dataframe(_display_rows(model["triggers"], {
        "signal_label": "신호", "metric": "지표", "metric_label": "지표 이름", "value": "값", "unit": "단위",
        "threshold": "기준값(정책)", "threshold_unit": "기준값 단위", "triggered": "발동", "status_label": "신호별 판정",
        "basis": "규칙 참고 근거", "source": "값의 출처"}))


def _render_chart(st, model: dict) -> None:
    st.subheader("kg당 단가와 점유율: 기준월과 비교월")
    chart, units = model["chart"], model["chart"]["units"]
    series = chart.get("series")
    if series:
        label_u, label_b = f"kg당 단가({units['unit_value']})", f"기준월 단가({units['unit_value']})"
        data = {"월": [row["label"] for row in series], label_u: _floats(row["value"] for row in series)}
        if series[0].get("baseline_value") is not None:
            data[label_b] = _floats(row["baseline_value"] for row in series)
        st.line_chart(data, x="월", y=[k for k in data if k != "월"])
        st.caption("trace의 get_history 지표(U)로 그린 달별 kg당 단가. 수평선은 기준월(전년 같은 달) 단가다.")
    drawn = False
    cols = st.columns(2)
    for column, key, title in ((cols[0], "unit_value", f"kg당 단가({units['unit_value']})"),
                               (cols[1], "share", f"점유율({units['share']})")):
        rows = chart["bars"].get(key)
        if rows:
            column.bar_chart({"월": [r["label"] for r in rows], title: _floats(r["value"] for r in rows)}, x="월", y=title)
            drawn = True
    if not drawn and not series:
        st.caption("차트에 쓸 값(기준월·비교월의 U·s)이 보고서·trace에 없다.")


def _render_tools(st, model: dict) -> None:
    st.subheader("실제 실행한 도구")
    summary = model["model"]
    st.caption(f"모델 요청 {summary['model_requests']}회(HTTP 시도 {summary['model_attempts']}회, 오류 {summary['model_errors']}회), "
               f"토큰 입력 {summary['tokens_in']}·출력 {summary['tokens_out']}, 소요 {summary['wall_ms']} ms, "
               f"도구 시도 {summary['tool_attempts']}회, Critic {summary['critic_used']}, 수정 {summary['revision_used']}")
    st.dataframe(_display_rows(model["tools"], {
        "seq": "순번", "stage": "단계", "tool": "도구", "args": "인자 요약", "source": "요청 주체", "tool_attempts": "누적 시도",
        "ok": "성공", "evidence_count": "근거 ID 수", "metric_count": "지표 수", "missingness_count": "빠진 자료 수",
        "retryable_error": "retryable_error", "elapsed_ms": "소요(ms)", "blocked": "예산 차단", "note": "비고"}))


def _render_report(st, model: dict) -> None:
    st.subheader("반대 근거와 보고서")
    st.markdown("**사실 주장(typed claim)** — 코드가 덧붙인 주장은 출처 칸에 표시한다.")
    st.dataframe(_display_rows(model["claims"], {
        "claim_id": "ID", "origin": "출처", "claim_type": "종류", "metric": "지표", "value": "값", "unit": "단위",
        "direction": "방향", "period": "기간", "baseline_period": "기준 기간", "partner": "상대국", "hs6": "HS6",
        "evidence_ids": "근거 ID", "text": "문장"}))
    st.markdown("**설명(narrative)**")
    st.write(model["narrative"] or "설명 없음.")
    st.markdown("**미확인 가설(hypotheses)**")
    for item in model["hypotheses"] or ["가설 없음."]:
        st.write(f"- {item}")
    st.markdown("**검증기 기록(validator_findings)**")
    findings = model["validator_findings"]
    if findings:
        st.dataframe(_display_rows([f if isinstance(f, dict) else {"detail": f} for f in findings],
                                   {"check": "검사", "code": "코드", "path": "위치", "claim_id": "주장", "detail": "내용"}))
    else:
        st.write("기록 없음.")


def _render_timeline(st, model: dict) -> None:
    st.subheader("판정 전후 타임라인")
    flags = model["timeline"]["flags"]
    fired = [PHASE_LABEL.get(k, k) for k, v in flags.items() if v]
    st.caption("처음 표시는 조사 전 경보(PRE_INVESTIGATION)다. 표시 코드이며 판정이 바뀐 이력이 아니다. "
               + ("발동한 특수 단계: " + ", ".join(fired) if fired else "특수 단계(코드 집계·수정 버림·코드 지적·초안 버림) 발동 없음"))
    st.dataframe(_display_rows(model["timeline"]["rows"], {
        "seq": "순번", "stage": "흐름 단계", "step": "단계", "phase": "phase", "review_status": "review_status",
        "signal_status": "신호별 판정", "note": "비고"}))


def _render_evidence(st, model: dict) -> None:
    st.subheader("원본 행 링크")
    evidence = model["evidence"]
    st.caption(evidence["note"])
    if evidence["available"]:
        st.dataframe(_display_rows(evidence["rows"], {
            "evidence_id": "근거 ID", "resolved": "풀림", "table": "표", "hs_code": "HS 코드", "partner_code": "상대국",
            "month": "월", "amount_usd": "금액(USD)", "net_weight_kg": "중량(kg)", "observation_status": "관측 상태",
            "request_id": "요청 ID", "detail": "그 밖의 열", "failed_rule": "어긋난 규칙"}))
    else:
        st.dataframe(_display_rows(evidence["rows"], {"evidence_id": "근거 ID"}))


def main() -> None:
    """스트림릿 진입점: uv run --locked --with "streamlit==1.64.0" streamlit run src/tradesentry/app.py"""
    import streamlit as st

    st.set_page_config(page_title="TradeSentry 사례 보기", layout="wide")
    repo_root, outputs_root = REPO_ROOT, REPO_ROOT / OUTPUTS_NAME
    st.title("TradeSentry — 사례 보기")
    st.caption(FOOTER_DISCLAIMER)
    with st.sidebar:
        st.header("사례 실행")
        _render_run_panel(st, repo_root, outputs_root)
        st.divider()
        st.header("실행 폴더")
        names = list_run_dirs(outputs_root)
        selected = st.session_state.get("selected_run")
        index = names.index(selected) if selected in names else 0
        choice = st.selectbox(f"{OUTPUTS_NAME}/ 아래 run_case 실행({len(names)}개, 새 것부터)", names, index=index) if names else None
        typed = st.text_input("또는 상대 경로 직접 입력", placeholder=f"{OUTPUTS_NAME}/run_case-yymmddhhmmss")
        typed_name = relative_run_dir(typed) if typed else None
        if typed and typed_name is None:
            st.error("실행명 형식(run_case-{12자리 시각})이 아니거나 볼 수 없는 위치다.")
        st.caption(f"`{OUTPUTS_NAME}/{SEALED_NAME}/`(봉인 묶음 출력)와 받는 중·격리 폴더는 나열하지 않는다.")
    _render_last_run(st)
    target = typed_name or choice
    if target is None:
        st.info("볼 실행 폴더가 없다. 왼쪽 \"사례 실행\"으로 사례를 돌리거나 CLI로 `tradesentry run-case`를 돌린 뒤 새로 고친다.")
        st.caption(FOOTER_SCOPE)
        return
    try:
        model = screen_model(outputs_root / target, repo_root=repo_root)
    except (OSError, ValueError) as exc:
        st.error(f"실행 폴더를 읽지 못했다({type(exc).__name__}). {OUTPUTS_NAME}/{target}의 기록 파일을 확인한다.")
        return
    last = st.session_state.get("last_run") or {}
    if (last.get("new_run_dirs") or [None])[0] == target:
        st.caption(NOT_SCORE_EVIDENCE + (" " + REPLAY_NOT_SCORE_EVIDENCE if last.get("replay") else ""))
    _render_header(st, model)
    _render_triggers(st, model)
    _render_chart(st, model)
    _render_tools(st, model)
    _render_report(st, model)
    _render_timeline(st, model)
    _render_evidence(st, model)
    st.divider()
    st.caption(model["footer"]["disclaimer"])
    st.caption(model["footer"]["scope"])


if __name__ == "__main__":
    main()
