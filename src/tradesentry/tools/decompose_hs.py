"""단위 I4 HS10 분해 조회.

단위 ID: I4
도메인명: tools_decompose_hs
소유: M
입력: scope
출력: 봉투(분해·부모 대조)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics, tradesentry.grouping, tradesentry.policy, tradesentry.tools

대상국 HS6의 단가 변화를 두 시점의 모든 HS10 하위품목으로 나눈다: 부모 대조, 중량 비중 분해, 개별 하위변화·상쇄·잔차·
불가 사유(개발 플랜 docs/plan/DEV_PLAN.md §6.1·§6.5, 자료 계약 docs/rules/DATA_CONTRACT_V1.md §11.2). 계산은 지표 단위
X3(decompose)이 하고, 이 도구는 자료 접근층의 행을 X3의 역할별 입력으로 옮겨 봉투에 싣는다. 요청 모양과 봉투 공통 규칙은
도구 공통 틀(check_comparability.py 머리 설명)이다. 요청에 policy_version이 꼭 있어야 한다(중량 허용오차의 행당 반올림
kg, 정책 tolerance.weight_rounding_kg). 모델 인자는 받지 않는다(하위품목을 고르지 않고 두 시점의 모든 HS10을 쓴다).

봉투
- metrics: X3의 within_effect·mix_effect·residual과 HS10 코드마다 r_U@·w@(기준월·비교월). HS10 단가 수준 U@는 싣지
  않는다: 사례당 토큰 한도 때문이고, U@의 입력(금액·중량)은 r_U@의 inputs(V_0·Q_0·V_1·Q_1)에 그대로 있다.
  분해 조건(같은 HS10 집합, 양 시점 중량 유효, 부모 대조 통과)을 못 채우면 세 값은 null과 사유다(X3이 정한다).
- comparability: {"parent_check": X3의 달별 부모 대조(행 수, 금액·중량 합, 허용오차, 일치 여부),
  "hs10": [{"month", "observation_status", "codes"}] (달별 하위자료 상태와 코드), "same_hs10_set": 참거짓 또는 null}.
- missingness: 두 달의 대상국 부모 행과 HS10 하위자료의 빠진 자료. scope: months는 두 달, partners는 대상국,
  hs10은 읽은 코드.
"""
from tradesentry.dal import query as dal
from tradesentry.metrics import decompose as metrics_decompose
from tradesentry.tools import check_comparability as common

TOOL = "decompose_hs"
DROPPED_PREFIX = "U@"  # 봉투에 싣지 않는 HS10 단가 수준 지표(머리 설명)


def _body(snap: dal.Snapshot, request: dict, started: int) -> dict:
    problem = common.args_problem(request["args"], {})
    if problem:
        return common.refuse(request, TOOL, snap, started, problem)
    hs6, partner = request["hs6"], request["partner"]
    base, period = request["baseline_month"], request["month"]
    parent, _ = common.parent_rows(snap, hs6, partner, [base, period])
    children, children_values = common.children_rows(snap, hs6, partner, [base, period])
    output = metrics_decompose.run({**common.target(request), "parent": parent.rows, "children": children.rows,
                                    "weight_rounding_kg": request["policy"]["tolerance"]["weight_rounding_kg"]})
    metrics = [m for m in common.metrics_of(output, "X3") if not m["inputs"]["metric"].startswith(DROPPED_PREFIX)]
    parent_check = output.get("parent_check")
    if not isinstance(parent_check, list):
        raise common.ToolError("지표 단위 X3의 출력에 parent_check 목록이 없다")
    hs10 = [{"month": value["month"], "observation_status": value["observation_status"],
             "codes": [row["hs10"] for row in value["rows"]]} for value in children_values]
    sets = [set(entry["codes"]) if entry["codes"] else None for entry in hs10]
    comparability = {"parent_check": parent_check, "hs10": hs10,
                     "same_hs10_set": None if None in sets else sets[0] == sets[1]}
    evidence = parent.evidence + children.evidence + [e for m in metrics for e in m["evidence_ids"]]
    scope = common.case_scope(request, months=[base, period], partners=[partner],
                              hs10=[code for entry in hs10 for code in entry["codes"]])
    return common.finish(request, TOOL, snap, started, scope=scope, evidence_ids=evidence, metrics=metrics,
                         comparability=comparability, missingness=parent.missing + children.missing)


def query(snap: dal.Snapshot, inp: object) -> dict:
    """열린 스냅샷(개발 빌드 포함)에서 HS10 분해를 조회한다."""
    return common.execute(snap, inp, TOOL, _body, needs_policy=True)


def run(inp: object) -> object:
    """진입 함수. 도구 요청 → 봉투. 스냅샷은 정본 빌드를 읽기 전용으로 연다."""
    return common.run_tool(inp, TOOL, _body, needs_policy=True)
