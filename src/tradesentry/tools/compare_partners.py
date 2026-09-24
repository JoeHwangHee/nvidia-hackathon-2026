"""단위 I3 비교국 조회.

단위 ID: I3
도메인명: tools_compare_partners
소유: M
입력: scope + 허용 비교국
출력: 봉투
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics, tradesentry.grouping, tradesentry.policy, tradesentry.tools

사전에 허용된 비교국(비교 대상 표 `peer_group`의 대상국 행)을 대상국과 같은 HS6·비교월·기준월·분모로 조회한다(개발 플랜
docs/plan/DEV_PLAN.md §6.5, 자료 계약 docs/rules/DATA_CONTRACT_V1.md §2.3.6). 요청 모양과 봉투 공통 규칙은 도구 공통 틀
(check_comparability.py 머리 설명)이다. 요청에 grouping_version(비교 대상 집합)이 꼭 있어야 한다.

허용 비교국과 모델 인자
- 허용 비교국은 스냅샷의 비교 대상 표에서 (대상국, grouping_version)의 가장 좁은 범위(hs6 → hs4 → hs2) 행이다(자료
  접근층 peers). 순위 순이다. 수집 계획 밖 비교국도 허용 목록에 있으면 조회하고 NOT_COLLECTED로 드러낸다(미수집을
  "변화 없음"으로 보지 않는다, 자료 계약 §2.3.6).
- 모델 인자는 partners 하나다: 허용 비교국 가운데 비교할 나라(관세청 2자리 국가코드 1~5개, 겹치지 않게). 없으면 허용
  비교국 전부다. 허용 목록 밖의 나라를 주면 도구를 돌리지 않고 retryable_error(invalid_args, allowed에 허용 목록)를
  돌려준다(룰북 시나리오 9 "복구할 수 있는 잘못된 조회 범위"). 다른 인자는 받지 않는다.

봉투
- metrics: 비교국마다 지표 단위 X1의 r_U와 X2의 d_s(분모는 대상국과 같은 `ALL` 합계). 사례당 토큰 한도 때문에 단가·
  점유율 수준 값(U·s·V)은 싣지 않는다(r_U·d_s의 inputs에 금액·중량이 있다).
- comparability: {"grouping_version", "comparable", "issues", "denominator": {"partner": "ALL", "months": [{month,
  observation_status}]}, "peers_allowed": [허용 비교국], "peers": [{"partner", "peer_rank", "months": [{"month",
  "observation_status", "amount_zero"}]}]}.
  comparable은 허용 비교국이 하나라도 있으면 참이다. 없으면 거짓이고 issues에 "no_allowed_peers"를 적는다(비교를 수행하지
  못했다는 명시 표시. 비교 대상 표를 적재하지 않은 빌드이거나 grouping_version이 틀린 경우다. 오류 표시 없는 빈 봉투를
  "비교 완료"로 옮기지 않게). 조회한 비교국의 자료가 모두 빠진 경우는 comparable이 참이고, peers의 관측 상태로 알린다. peers는 조회한 비교국마다 기준월·비교월의 부모 HS6 관측 상태다. amount_zero는 값이 있는 달에서
  금액이 0인가(수입 0 명시)이고, 값이 없으면 null이다. 무거래(수입 0 명시, CONFIRMED_NO_TRADE)는 비교를 마친 것으로,
  빠진 자료(NOT_COLLECTED 등)만 미완료로 볼 수 있게 남긴다(그 판단은 조립 AS2와 판정 정책이 한다).
- evidence_ids: 허용 비교국의 비교 대상 표 행, 지표의 근거, 빠진 자료. missingness: 조회한 비교국의 부모 행과 분모의
  빠진 자료(기준월·비교월).
- scope: months는 두 달, partners는 조회한 비교국과 `ALL`, hs10은 비었다. grouping_version을 더한다.
"""
from tradesentry.contract import types
from tradesentry.dal import query as dal
from tradesentry.metrics import share as metrics_share
from tradesentry.metrics import unit_value as metrics_unit_value
from tradesentry.tools import check_comparability as common

TOOL = "compare_partners"
MAX_PARTNERS = 5
NO_ALLOWED_PEERS = "no_allowed_peers"  # comparability.issues 값(이 단위가 정했다)


def _partners_problem(value: object) -> str | None:
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_PARTNERS:
        return f"관세청 2자리 국가코드 1~{MAX_PARTNERS}개의 목록이어야 한다"
    if not all(isinstance(p, str) and common.PARTNER_RE.fullmatch(p) for p in value):
        return "관세청 2자리 국가코드(영문 대문자 두 글자)만 쓴다"
    if len(set(value)) != len(value):
        return "같은 나라를 두 번 쓰지 않는다"
    return None


def _month_states(values: list[dict]) -> list[dict]:
    out = []
    for value in values:
        status = value["observation_status"]
        zero = value["amount_usd"] == 0 if status == types.OBSERVED else None
        out.append({"month": value["month"], "observation_status": status, "amount_zero": zero})
    return out


def _body(snap: dal.Snapshot, request: dict, started: int) -> dict:
    problem = common.args_problem(request["args"], {"partners": _partners_problem})
    if problem:
        return common.refuse(request, TOOL, snap, started, problem)
    hs6, partner = request["hs6"], request["partner"]
    base, period = request["baseline_month"], request["month"]
    grouping = request["grouping_version"]
    peer_rows = [row for row in snap.peers(hs6, partner, grouping) if row["peer_id"] != partner]
    allowed = list(dict.fromkeys(row["peer_id"] for row in peer_rows))
    rank = {}
    for row in peer_rows:
        rank.setdefault(row["peer_id"], row["peer_rank"])
    wanted = request["args"].get("partners")
    if wanted is not None:
        outside = [p for p in wanted if p not in allowed]
        if outside:
            return common.refuse(request, TOOL, snap, started,
                                 f"partners: 허용된 비교국이 아니다: {', '.join(outside)}", allowed=allowed)
    chosen = [p for p in allowed if wanted is None or p in wanted]

    world, world_values = common.world_rows(snap, hs6, [base, period])
    metrics, peers, evidence = [], [], [row["evidence_id"] for row in peer_rows]
    missing = list(world.missing)
    for peer in chosen:
        parent, values = common.parent_rows(snap, hs6, peer, [base, period])
        target = common.target(request, peer)
        x1 = common.metrics_of(metrics_unit_value.run({**target, "parent": parent.rows}), "X1")
        x2 = common.metrics_of(metrics_share.run({**target, "parent": parent.rows, "world": world.rows}), "X2")
        metrics += [m for m in x1 if m["inputs"]["metric"] == "r_U"] + [m for m in x2 if m["inputs"]["metric"] == "d_s"]
        peers.append({"partner": peer, "peer_rank": rank[peer], "months": _month_states(values)})
        evidence += parent.evidence
        missing += parent.missing
    comparability = {
        "grouping_version": grouping,
        "comparable": bool(allowed),
        "issues": [] if allowed else [NO_ALLOWED_PEERS],
        "denominator": {"partner": types.ALL_PARTNER,
                        "months": [{"month": v["month"], "observation_status": v["observation_status"]}
                                   for v in world_values]},
        "peers_allowed": allowed,
        "peers": peers,
    }
    evidence += world.evidence + [e for m in metrics for e in m["evidence_ids"]]
    scope = common.case_scope(request, months=[base, period], partners=chosen + [types.ALL_PARTNER], hs10=[],
                              grouping_version=grouping)
    return common.finish(request, TOOL, snap, started, scope=scope, evidence_ids=evidence, metrics=metrics,
                         comparability=comparability, missingness=missing)


def query(snap: dal.Snapshot, inp: object) -> dict:
    """열린 스냅샷(개발 빌드 포함)에서 비교국을 조회한다."""
    return common.execute(snap, inp, TOOL, _body, needs_grouping=True)


def run(inp: object) -> object:
    """진입 함수. 도구 요청 → 봉투. 스냅샷은 정본 빌드를 읽기 전용으로 연다."""
    return common.run_tool(inp, TOOL, _body, needs_grouping=True)
