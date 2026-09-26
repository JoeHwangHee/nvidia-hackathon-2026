"""단위 A1 모의 승인.

단위 ID: A1
도메인명: approval_record
소유: M
입력: 보고서·근거 digest
출력: 승인 기록·`REVIEW_REQUIRED`
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.reports, tradesentry.approval

모의 승인(자료 계약 docs/rules/DATA_CONTRACT_V1.md §9.3, 개발 플랜 §7.6). 실제 기관 승인이나 통관 조치가 아니고 계정·권한은
없다. 담당자용 화면(UI2, `tradesentry.ui.records`)이 담당자 결정 기록의 핵심으로 쓴다.

- 입력(JSON 객체): `report`(보고서 객체. `report_hash`·`evidence_ids`·`snapshot_id`·`policy_version`을 읽는다),
  `execution_status`(그 실행의 실행 상태), `reviewer_label`, `timestamp`(KST ISO 8601. 부르는 쪽이 준다. 이 단위는 시계를 읽지
  않아 골든 시험이 결정적이다), `code_version`(없으면 null).
- 출력(JSON 객체): 승인 기록(자료 계약 §9.3 필드 7개 `reviewer_label, timestamp, report_hash, evidence_digest, snapshot_id,
  policy_version, code_version`)에 `status`(`VALID`)를 더한 것. `execution_status`가 `COMPLETED`가 아니면 ValueError
  (승인할 수 없다). 보고서에 `report_hash`가 없어도 ValueError다.
- `report_hash`는 보고서 객체의 `report_hash`(단위 R2가 §9.1 규칙으로 계산한 값)를 옮긴다. 다시 계산하지 않는다.
- `evidence_digest`(근거 digest)는 보고서 `evidence_ids`를 정렬·중복 제거해 줄바꿈으로 이은 UTF-8 문자열의 sha256이다
  (결정 기록 `20260926-1836-model-decision-ui-user-pages.md`). 근거 행의 내용이 아니라 근거 ID 집합의 digest다: 동결 스냅샷의
  행은 바뀌지 않으므로(CLAUDE.md 절대 규칙 2) 보고서가 기대는 근거 집합이 바뀌었는지만 본다.
- `check(record, report)`: 뒤에 보고서를 다시 읽어 기록의 `report_hash`·`evidence_digest`와 대조한다. 같으면 `VALID`, 하나라도
  다르거나 보고서가 없으면 `REVIEW_REQUIRED`. 기록 자체는 고치지 않는다(보존).
"""
import hashlib

from tradesentry.contract import types

COMPLETED = "COMPLETED"
VALID, REVIEW_REQUIRED = types.APPROVAL_STATUSES
INPUT_KEYS = ("report", "execution_status", "reviewer_label", "timestamp", "code_version")


def evidence_digest(evidence_ids: object) -> str:
    """근거 ID 집합의 digest: 정렬·중복 제거한 ID를 줄바꿈으로 이은 문자열의 sha256."""
    ids = sorted({e for e in (evidence_ids or []) if isinstance(e, str)}) if isinstance(evidence_ids, (list, tuple)) else []
    return hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()


def approve(report: object, execution_status: object, reviewer_label: object, timestamp: object,
            code_version: object = None) -> dict:
    """승인 기록을 만든다. COMPLETED가 아닌 실행의 보고서는 승인할 수 없다(ValueError)."""
    if execution_status != COMPLETED:
        raise ValueError("execution_status가 COMPLETED가 아닌 실행의 보고서는 승인할 수 없다")
    if not isinstance(report, dict) or not isinstance(report.get("report_hash"), str) or not report["report_hash"]:
        raise ValueError("보고서 객체에 report_hash가 없다")
    if not isinstance(reviewer_label, str) or not isinstance(timestamp, str) or not timestamp:
        raise ValueError("reviewer_label(문자열)과 timestamp(KST ISO 8601 문자열)가 있어야 한다")
    return {
        "reviewer_label": reviewer_label,
        "timestamp": timestamp,
        "report_hash": report["report_hash"],
        "evidence_digest": evidence_digest(report.get("evidence_ids")),
        "snapshot_id": report.get("snapshot_id"),
        "policy_version": report.get("policy_version"),
        "code_version": code_version if isinstance(code_version, str) else None,
        "status": VALID,
    }


def check(record: object, report: object) -> str:
    """기록과 지금의 보고서를 대조한 유효 상태. 보고서가 없거나 해시·digest가 하나라도 다르면 REVIEW_REQUIRED다."""
    if not isinstance(record, dict) or not isinstance(report, dict):
        return REVIEW_REQUIRED
    if record.get("report_hash") != report.get("report_hash"):
        return REVIEW_REQUIRED
    if record.get("evidence_digest") != evidence_digest(report.get("evidence_ids")):
        return REVIEW_REQUIRED
    return VALID


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    if not isinstance(inp, dict) or not {"report", "execution_status", "reviewer_label", "timestamp"} <= set(inp) \
            or not set(inp) <= set(INPUT_KEYS):
        raise ValueError("입력은 {report, execution_status, reviewer_label, timestamp, code_version?} 객체다")
    return approve(inp["report"], inp["execution_status"], inp["reviewer_label"], inp["timestamp"], inp.get("code_version"))
