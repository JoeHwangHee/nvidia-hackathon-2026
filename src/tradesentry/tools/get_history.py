"""단위 I2 이력 조회.

단위 ID: I2
도메인명: tools_get_history
소유: M
입력: scope
출력: 봉투(이력·전년동월 비교)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics, tradesentry.grouping, tradesentry.policy, tradesentry.tools

대상 HS6·대상국의 전년동월 비교와 이력을 정해진 작은 구조와 원본 행 포인터로 돌려준다(개발 플랜 docs/plan/DEV_PLAN.md
§6.5). 요청 모양과 봉투 공통 규칙은 도구 공통 틀(check_comparability.py 머리 설명)이다. 모델 인자는 받지 않는다.

봉투
- metrics: 지표 단위 X1(unit_value)과 X2(share)의 출력 그대로다. X1은 U(기준월)·U(비교월)·r_U, X2는 V(대상국 두 달)·
  V(`ALL` 두 달)·s(두 달)·d_s다. 단가·점유율 분자는 부모 HS6 행, 분모는 중복을 뺀 `ALL` HS10 행의 합이다(자료 계약
  §11.2 원천 규칙). 값·null 사유는 지표 단위가 정한다.
- comparability: {"history": [{"month", "observation_status", "evidence_ids"}…], "denominator": {"partner": "ALL"}}.
  history는 기준월부터 비교월까지 13개월의 대상국 부모 HS6 관측 상태와 그 행(빠진 달은 상태 행)의 근거 ID다. 값은
  싣지 않는다(값은 metrics만 싣는다. 사례당 토큰 한도 때문에 이력 달의 지표는 만들지 않는다).
- missingness: 비교월·기준월의 빠진 자료(대상국 부모 행, `ALL` 분모). 이력의 다른 달은 history의 상태로만 알린다.
- scope: months는 읽은 13개월, partners는 대상국과 `ALL`, hs10은 비었다(대상국 HS10은 읽지 않는다).
"""
from tradesentry.contract import types
from tradesentry.dal import query as dal
from tradesentry.metrics import share as metrics_share
from tradesentry.metrics import unit_value as metrics_unit_value
from tradesentry.tools import check_comparability as common

TOOL = "get_history"


def _body(snap: dal.Snapshot, request: dict, started: int) -> dict:
    problem = common.args_problem(request["args"], {})
    if problem:
        return common.refuse(request, TOOL, snap, started, problem)
    hs6, partner = request["hs6"], request["partner"]
    base, period = request["baseline_month"], request["month"]
    parent, _ = common.parent_rows(snap, hs6, partner, [base, period])
    world, _ = common.world_rows(snap, hs6, [base, period])
    target = common.target(request)
    metrics = common.metrics_of(metrics_unit_value.run({**target, "parent": parent.rows}), "X1")
    metrics += common.metrics_of(metrics_share.run({**target, "parent": parent.rows, "world": world.rows}), "X2")

    window = common.months_between(base, period)
    history, history_evidence = [], []
    for value in snap.parent_series(hs6, partner, window):
        ids = list(value["evidence_ids"]) or [entry["evidence_id"] for entry in value["missingness"]]
        history.append({"month": value["month"], "observation_status": value["observation_status"], "evidence_ids": ids})
        history_evidence += ids
    comparability = {"history": history, "denominator": {"partner": types.ALL_PARTNER}}
    evidence = parent.evidence + world.evidence + [e for m in metrics for e in m["evidence_ids"]] + history_evidence
    scope = common.case_scope(request, months=window, partners=[partner, types.ALL_PARTNER], hs10=[])
    return common.finish(request, TOOL, snap, started, scope=scope, evidence_ids=evidence, metrics=metrics,
                         comparability=comparability, missingness=parent.missing + world.missing)


def query(snap: dal.Snapshot, inp: object) -> dict:
    """열린 스냅샷(개발 빌드 포함)에서 이력을 조회한다."""
    return common.execute(snap, inp, TOOL, _body)


def run(inp: object) -> object:
    """진입 함수. 도구 요청 → 봉투. 스냅샷은 정본 빌드를 읽기 전용으로 연다."""
    return common.run_tool(inp, TOOL, _body)
