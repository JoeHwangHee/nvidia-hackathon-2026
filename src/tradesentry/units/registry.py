"""단위 등록부: 단위 ID와 진입 함수의 대응표(개발 전용).

- 공통 실행기(runner.py)와 시험(tests/)이 쓴다. CLI·런타임 스킬·샌드박스 정책과 단위 파일은 tradesentry.units를
  import하지 않는다(경계 시험이 본다).
- 정본은 docs/plan/UNITS.md §3이다. 단위 C3·C4는 PR #18 새 판(옛 C3 scorer_summary를 C3 scorer_results와
  C4 scorer_summary로 나눔)을 따른다.
- 저장소에 두는 앱·커널 단위 54개(앱 53, 커널 1)를 싣는다. 봉인 폴더에만 두는 단위 V3·V6과 구성 단위 9개는
  싣지 않고 NOT_REGISTERED에 이유만 적는다. 합계 65개다.
- 단위 모듈은 여기서 import하지 않는다. load_entry가 필요할 때 importlib로 부른다. eval.* 단위는 설치 패키지에
  들지 않으므로 저장소 루트가 sys.path에 있어야 불린다(저장소 루트에서 python -m으로 실행한다).
- ext는 공통 실행기가 출력 파일 {도메인명}-{시각}.{ext}에 붙이는 확장자다. json이 기본이고, 단위 표가 파일 형식을
  적은 단위만 다르다(jsonl, md, csv, sqlite).
- 단위 파일의 머리 주석(모듈 docstring)은 "이름: 값" 줄로 단위 ID·도메인명·소유·입력·출력·허용 import를 적는다.
  read_header가 그 줄을 읽는다. 허용 import는 쉼표로 나눈 목록이고, 표준 라이브러리는 STDLIB_TOKEN으로 적고
  나머지는 모듈 이름 앞부분(예: tradesentry.contract는 그 아래 모든 모듈을 허용)이다.
"""
import ast
import importlib
from dataclasses import dataclass
from typing import Callable

HEADER_LABELS = ("단위 ID", "도메인명", "소유", "입력", "출력", "허용 import")
STDLIB_TOKEN = "표준 라이브러리"


@dataclass(frozen=True)
class Unit:
    """등록부 한 행.

    unit_id: 단위 표의 단위 ID. domain: 도메인명(출력 파일 이름의 앞부분이자, 혼자 돌릴 때의 실행 이름).
    module: import 경로. entry: 진입 함수 이름(없으면 None). ext: 공통 실행기의 출력 확장자.
    note: 진입 함수가 없는 이유 등 덧붙일 말.
    """

    unit_id: str
    domain: str
    module: str
    entry: str | None
    ext: str
    note: str = ""

    @property
    def path(self) -> str:
        """저장소 루트 기준 파일 경로."""
        rel = self.module.replace(".", "/") + ".py"
        return rel if self.module.startswith("eval.") else "src/" + rel


_S1_NOTE = ("기존 수집기라 run이 없다. 자체 명령(python3 src/tradesentry/ingest.py <명령>)으로 돌고, "
            "시험은 tests/test_ingest.py다")
_K1_NOTE = "커널(여러 단위가 import하는 정의 모음)이라 진입 함수가 없다"

UNITS: dict[str, Unit] = {u.unit_id: u for u in (
    Unit("S1", "ingest", "tradesentry.ingest", None, "json", _S1_NOTE),
    Unit("S2", "snapshot_build", "tradesentry.snapshot.build", "run", "sqlite"),
    Unit("S3", "snapshot_verify", "tradesentry.snapshot.verify", "run", "json"),
    Unit("S4", "snapshot_fixture", "tradesentry.snapshot.fixture", "run", "json"),
    Unit("K1", "contract_types", "tradesentry.contract.types", None, "json", _K1_NOTE),
    Unit("K2", "contract_evidence_id", "tradesentry.contract.evidence_id", "run", "json"),
    Unit("K3", "dal_query", "tradesentry.dal.query", "run", "json"),
    Unit("K4", "contract_policy_load", "tradesentry.contract.policy_load", "run", "json"),
    Unit("K5", "contract_envelope", "tradesentry.contract.envelope", "run", "json"),
    Unit("X1", "metrics_unit_value", "tradesentry.metrics.unit_value", "run", "json"),
    Unit("X2", "metrics_share", "tradesentry.metrics.share", "run", "json"),
    Unit("X3", "metrics_decompose", "tradesentry.metrics.decompose", "run", "json"),
    Unit("X4", "metrics_rounding", "tradesentry.metrics.rounding", "run", "json"),
    Unit("P1", "policy_trigger", "tradesentry.policy.trigger", "run", "json"),
    Unit("P2", "policy_case_build", "tradesentry.policy.case_build", "run", "json"),
    Unit("P3", "policy_signal_decide", "tradesentry.policy.signal_decide", "run", "json"),
    Unit("P4", "policy_case_aggregate", "tradesentry.policy.case_aggregate", "run", "json"),
    Unit("P5", "policy_required_evidence", "tradesentry.policy.required_evidence", "run", "json"),
    Unit("G1", "grouping_g0", "tradesentry.grouping.g0", "run", "csv"),
    Unit("G2", "grouping_g1", "tradesentry.grouping.g1", "run", "csv"),
    Unit("I1", "tools_check_comparability", "tradesentry.tools.check_comparability", "run", "json"),
    Unit("I2", "tools_get_history", "tradesentry.tools.get_history", "run", "json"),
    Unit("I3", "tools_compare_partners", "tradesentry.tools.compare_partners", "run", "json"),
    Unit("I4", "tools_decompose_hs", "tradesentry.tools.decompose_hs", "run", "json"),
    Unit("I5", "tools_verify_evidence", "tradesentry.tools.verify_evidence", "run", "json"),
    Unit("I6", "tools_budget", "tradesentry.tools.budget", "run", "json"),
    Unit("I7", "workflow_model_client", "tradesentry.workflow.model_client", "run", "json"),
    Unit("I8", "workflow_replay", "tradesentry.workflow.replay", "run", "json"),
    Unit("I10", "workflow_investigator", "tradesentry.workflow.investigator", "run", "json"),
    Unit("I11", "workflow_critic", "tradesentry.workflow.critic", "run", "json"),
    Unit("I12", "workflow_orchestrate", "tradesentry.workflow.orchestrate", "run", "json"),
    Unit("I13", "workflow_nat_wrap", "tradesentry.workflow.nat_wrap", "run", "json"),
    Unit("R1", "reports_claims", "tradesentry.reports.claims", "run", "json"),
    Unit("R2", "reports_render_ko", "tradesentry.reports.render_ko", "run", "json"),
    Unit("R3", "validator_validate", "tradesentry.validator.validate", "run", "json"),
    Unit("R4", "validator_gate", "tradesentry.validator.gate", "run", "json"),
    Unit("F1", "cli_args", "tradesentry.cli.args", "run", "json"),
    Unit("F2", "cli_dispatch", "tradesentry.cli.dispatch", "run", "json"),
    Unit("A1", "approval_record", "tradesentry.approval.record", "run", "json"),
    Unit("A2", "app", "tradesentry.app", "run", "json"),
    Unit("E1", "evaluation_batch_run", "tradesentry.evaluation.batch_run", "run", "jsonl"),
    Unit("E2", "evaluation_sealed_runner", "tradesentry.evaluation.sealed_runner", "run", "json"),
    Unit("E3", "evaluation_extract", "tradesentry.evaluation.extract", "run", "json"),
    Unit("E4", "evaluation_nat_eval", "tradesentry.evaluation.nat_eval", "run", "json"),
    Unit("V2", "datagen_dev20", "eval.datagen.dev20", "run", "json"),
    Unit("V4", "datagen_holdout40_check", "eval.datagen.holdout40_check", "run", "json"),
    Unit("V5", "datagen_split", "eval.datagen.split", "run", "json"),
    Unit("C1", "scorer_claims", "eval.scorer.claims", "run", "jsonl"),
    Unit("C2", "scorer_prose", "eval.scorer.prose", "run", "jsonl"),
    Unit("C3", "scorer_results", "eval.scorer.results", "run", "jsonl"),
    Unit("C4", "scorer_summary", "eval.scorer.summary", "run", "md"),
    Unit("L1", "runlog_trace", "tradesentry.runlog.trace", "run", "jsonl"),
    Unit("L2", "runlog_run_record", "tradesentry.runlog.run_record", "run", "json"),
    Unit("L3", "runlog_cause_codes", "tradesentry.runlog.cause_codes", "run", "json"),
)}

# 단위 표에 있지만 등록부에 싣지 않는 단위와 그 이유.
NOT_REGISTERED: dict[str, str] = {
    "V3": "봉인 폴더에서만 만드는 단위(holdout40 격리 생성)라 저장소와 등록부에 없다",
    "V6": "봉인 폴더에서만 만드는 단위(real_sealed 표본)라 저장소와 등록부에 없다",
    "G3": "구성 단위(국가 코드 대응표)라 진입 함수가 없다",
    "I9": "구성 단위(프롬프트·모델 설정)라 진입 함수가 없다",
    "F3": "구성 단위(런타임 스킬)라 진입 함수가 없다",
    "F4": "구성 단위(OpenShell 정책)라 진입 함수가 없다",
    "F5": "구성 단위(샌드박스 이미지 정의)라 진입 함수가 없다",
    "F6": "구성 단위(키 주입 provider 프로필)라 진입 함수가 없다",
    "F7": "구성 단위(위반 시험 스크립트)라 공통 실행기로 돌리지 않는다",
    "V1": "구성 단위(시나리오 명세)라 진입 함수가 없다",
    "V7": "구성 단위(봉인 해시 목록)라 진입 함수가 없다",
}


def read_header(source: str) -> dict[str, str]:
    """단위 파일 소스의 머리 주석에서 "이름: 값" 줄을 읽는다. 머리 주석이 없으면 빈 사전이다."""
    doc = ast.get_docstring(ast.parse(source)) or ""
    fields: dict[str, str] = {}
    for line in doc.splitlines():
        label, sep, value = line.partition(":")
        if sep and label in HEADER_LABELS and label not in fields:
            fields[label] = value.strip()
    return fields


def header_allowed_imports(fields: dict[str, str]) -> list[str]:
    """머리 주석의 허용 import 목록."""
    return [token.strip() for token in fields.get("허용 import", "").split(",") if token.strip()]


def load_entry(unit: Unit) -> Callable[[object], object]:
    """단위의 진입 함수를 불러 돌려준다. 진입 함수가 없는 단위면 LookupError를 낸다."""
    if unit.entry is None:
        raise LookupError(f"단위 {unit.unit_id}({unit.domain})는 진입 함수가 없다: {unit.note}")
    module = importlib.import_module(unit.module)
    entry = getattr(module, unit.entry)
    if not callable(entry):
        raise LookupError(f"단위 {unit.unit_id}의 {unit.module}.{unit.entry}는 함수가 아니다")
    return entry
