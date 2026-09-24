"""단위 I5 근거 대조.

단위 ID: I5
도메인명: tools_verify_evidence
소유: M
입력: 받은 근거·지표
출력: 원본 대조 결과
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics, tradesentry.grouping, tradesentry.policy, tradesentry.tools

초안이 가리킨 지표(metric_id)와 근거 ID를, 이 사례에서 앞서 받은 봉투와 읽기 전용 스냅샷 원본에 대조한다(개발 플랜
docs/plan/DEV_PLAN.md §6.5, 자료 계약 docs/rules/DATA_CONTRACT_V1.md §4.4·§5.3). 다른 도구를 부르지 않고, 새 비교 근거를
만들지 않으며, 평가 정답 파일을 보지 않는다. 요청 모양은 도구 공통 틀(check_comparability.py 머리 설명)이고, 요청에
envelopes(앞서 받은 봉투 목록, 코드가 넘긴다)와 policy_version(분해 지표를 다시 계산할 때의 중량 허용오차)이 꼭 있어야 한다.

인자(흐름 조정이 초안에서 뽑아 넘긴다): {"metric_ids": [문자열…], "evidence_ids": [문자열…]}. 둘 다 없어도 된다. 목록마다
200개, 문자열마다 256자까지다. 목록이 아니거나 문자열이 아니면 retryable_error(invalid_args)다. 지어낸 ID도 대조 대상이라
글자 모양으로 거부하지 않는다(대조 결과로 알린다).

대조(문제 코드는 이 단위가 정했다)
- 지표 metric_id마다
  - metric_not_returned: 앞서 받은 봉투의 metrics에 없다. metric_id_conflict: 같은 ID의 다른 객체가 있다.
  - metric_malformed: 자료 계약 §2.3.4 metric 객체가 아니다(단위 K5 metric_problems).
  - unit_mismatch: unit이 지표 기호의 계약 단위(§11.2)와 다르다. metric_symbol_unknown: 계약에 없는 기호다.
  - metric_out_of_scope: 품목이 사례 HS6가 아니거나, 상대국이 사례 대상국·`ALL`·앞서 조회한 비교국이 아니거나, 달이
    사례의 비교월·기준월이 아니다.
  - evidence_unresolved·evidence_out_of_scope: 지표의 근거 ID가 풀리지 않거나(풀림 규칙 1~4) 범위 밖 행이다.
  - recompute_mismatch: 같은 원본 행을 같은 지표 단위(X1·X2·X3)로 다시 계산한 지표 객체와 다르다(다른 키 이름을
    fields에 적는다). 지표 계산은 지표 단위만 하고 이 도구는 다시 부를 뿐이다.
- 초안의 근거 ID마다
  - evidence_unresolved: 풀림 규칙 1~4에 어긋난다(failed_rule에 규칙 번호).
  - evidence_not_returned: 앞서 받은 봉투(evidence_ids, 지표의 evidence_ids, missingness 항목)가 돌려준 근거가 아니다.
  - evidence_out_of_scope: 사례 범위 밖 행이다(observation 행은 수입 흐름, 기준월~비교월, 사례 HS6(와 그 HS4 스캔의
    상태 행), 사례 대상국·`ALL`·앞서 조회한 비교국. peer_group 행은 대상국의 행. 다른 표는 범위 밖).
  - evidence_total_row: 총계 행(`RAW:총계`)이다. 총계 행은 근거 ID로 쓰지 않는다(§4.4).
- 문구(금지 문구, 뒷받침 없는 산문 숫자)와 필수 근거 대조는 검증기(단위 R3)와 판정 정책(단위 P5)이 한다. 이 도구는 초안의
  글을 받지 않는다.

봉투
- evidence_ids·metrics: 비었다. 새 근거를 만들지 않고, 대조한 근거 ID를 "도구가 돌려준 근거"로 다시 싣지도 않는다(모델이
  지어낸 ID가 대조를 거쳐 돌려준 근거로 보이지 않게).
- comparability: {"ok": 모두 통과했나, "metrics": [{"metric_id", "ok", "problems", "fields"}],
  "evidence": [{"evidence_id", "ok", "problems", "failed_rule"}]}. missingness는 비었다.
- scope: months는 두 달, partners는 대조에 허용한 상대국, hs10은 비었다.
"""
import json

from tradesentry.contract import types
from tradesentry.contract.envelope import metric_problems
from tradesentry.contract.evidence_id import parse_evidence_id
from tradesentry.dal import query as dal
from tradesentry.metrics import decompose as metrics_decompose
from tradesentry.metrics import share as metrics_share
from tradesentry.metrics import unit_value as metrics_unit_value
from tradesentry.tools import check_comparability as common

TOOL = "verify_evidence"
MAX_REFS = 200
MAX_REF_LENGTH = 256
X1_SYMBOLS = ("U", "r_U")
X2_SYMBOLS = ("V", "s", "d_s")


def _canonical(value: object) -> str:
    """지표 객체 비교용 글자열. Decimal은 원문 표기(끝자리 0 포함)로, 참거짓과 정수는 따로 적는다."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)


def _refs_problem(value: object) -> str | None:
    if not isinstance(value, list) or len(value) > MAX_REFS:
        return f"문자열 {MAX_REFS}개 이하의 목록이어야 한다"
    if not all(isinstance(v, str) and 0 < len(v) <= MAX_REF_LENGTH for v in value):
        return f"{MAX_REF_LENGTH}자 이하의 비지 않은 문자열만 쓴다"
    return None


def _check_envelopes(envelopes: list, snapshot_id: str) -> None:
    for index, envelope in enumerate(envelopes):
        if not isinstance(envelope, dict) or envelope.get("tool") not in types.TOOLS \
                or envelope.get("snapshot_id") != snapshot_id or not isinstance(envelope.get("metrics"), list):
            raise common.ToolError(f"envelopes[{index}]가 같은 스냅샷의 도구 봉투가 아니다")


def _returned(envelopes: list) -> tuple[dict[str, list[dict]], set[str], set[str]]:
    """앞서 받은 봉투의 지표(metric_id → 객체들), 돌려준 근거 ID, 조회한 상대국."""
    metrics: dict[str, list[dict]] = {}
    evidence: set[str] = set()
    partners: set[str] = set()
    for envelope in envelopes:
        evidence.update(e for e in envelope.get("evidence_ids") or [] if isinstance(e, str))
        for entry in envelope.get("missingness") or []:
            if isinstance(entry, dict) and isinstance(entry.get("evidence_id"), str):
                evidence.add(entry["evidence_id"])
        for metric in envelope["metrics"]:
            if isinstance(metric, dict) and isinstance(metric.get("metric_id"), str):
                bucket = metrics.setdefault(metric["metric_id"], [])
                if metric not in bucket:
                    bucket.append(metric)
                evidence.update(e for e in metric.get("evidence_ids") or [] if isinstance(e, str))
        if envelope["tool"] == "compare_partners":
            scope = envelope.get("scope") or {}
            partners.update(p for p in scope.get("partners") or [] if isinstance(p, str))
    return metrics, evidence, partners


class _Checker:
    def __init__(self, snap: dal.Snapshot, request: dict, partners: set[str]) -> None:
        self.snap, self.request = snap, request
        self.hs6, self.partner = request["hs6"], request["partner"]
        self.base, self.period = request["baseline_month"], request["month"]
        self.window = set(common.months_between(self.base, self.period))
        self.partners = {self.partner, types.ALL_PARTNER} | partners
        self.cache: dict[tuple, dict] = {}

    def evidence_problems(self, evidence_id: str) -> tuple[list[str], int | None]:
        """근거 ID 하나의 풀림과 범위. (문제 코드, 어긋난 풀림 규칙 번호)."""
        resolved = self.snap.resolve(evidence_id)
        if not resolved["resolved"]:
            return ["evidence_unresolved"], resolved["failed_rule"]
        table, row = parse_evidence_id(evidence_id).table, resolved["row"]
        if table == "peer_group":
            return ([] if row.get("entity_id") == self.partner else ["evidence_out_of_scope"]), None
        if table != "observation":
            return ["evidence_out_of_scope"], None
        month = row.get("month") or ""
        if month.startswith(types.RAW_MONTH_PREFIX):
            return ["evidence_total_row"], None
        code = row.get("hs_code") or ""
        in_scope = (row.get("flow") == types.METRIC_FLOW and month in self.window
                    and row.get("partner_code") in self.partners and (code[:6] == self.hs6 or code == self.hs6[:4]))
        return ([] if in_scope else ["evidence_out_of_scope"]), None

    def recompute(self, symbol: str, partner: str, period: str, baseline: object) -> dict | None:
        """같은 원본 행을 같은 지표 단위로 다시 계산한 지표(없으면 None)."""
        base_symbol = symbol.partition("@")[0]
        if "@" not in symbol and base_symbol in X1_SYMBOLS:
            unit, who = "X1", partner
        elif "@" not in symbol and base_symbol in X2_SYMBOLS:
            unit, who = "X2", self.partner if partner == types.ALL_PARTNER else partner
        else:
            unit, who = "X3", partner
        if who == types.ALL_PARTNER:
            return None  # 분모(`ALL`)는 X2의 V로만 다시 계산한다
        key = (unit, who)
        if key not in self.cache:
            months = [self.base, self.period]
            parent, _ = common.parent_rows(self.snap, self.hs6, who, months)
            target = common.target(self.request, who)
            if unit == "X1":
                output = metrics_unit_value.run({**target, "parent": parent.rows})
            elif unit == "X2":
                world, _ = common.world_rows(self.snap, self.hs6, months)
                output = metrics_share.run({**target, "parent": parent.rows, "world": world.rows})
            else:
                children, _ = common.children_rows(self.snap, self.hs6, who, months)
                output = metrics_decompose.run({**target, "parent": parent.rows, "children": children.rows,
                                                "weight_rounding_kg":
                                                    self.request["policy"]["tolerance"]["weight_rounding_kg"]})
            self.cache[key] = {(m["inputs"].get("metric"), m["inputs"].get("partner"), m["inputs"].get("period"),
                                m["inputs"].get("baseline_period")): m for m in common.metrics_of(output, unit)}
        return self.cache[key].get((symbol, partner, period, baseline))

    def metric_result(self, metric_id: str, found: list[dict]) -> dict:
        result = {"metric_id": metric_id, "ok": False, "problems": [], "fields": []}
        if not found:
            result["problems"].append("metric_not_returned")
            return result
        if len(found) > 1:
            result["problems"].append("metric_id_conflict")
        metric = found[0]
        if metric_problems(metric, self.snap.snapshot_id):
            result["problems"].append("metric_malformed")
            return result
        inputs = metric["inputs"]
        symbol, partner, period = inputs.get("metric"), inputs.get("partner"), inputs.get("period")
        try:
            unit = types.metric_unit(symbol)
        except ValueError:
            result["problems"].append("metric_symbol_unknown")
            return result
        if unit != metric["unit"]:
            result["problems"].append("unit_mismatch")
        if inputs.get("hs6") != self.hs6 or partner not in self.partners or period not in (self.base, self.period):
            result["problems"].append("metric_out_of_scope")
        for evidence_id in metric["evidence_ids"]:
            result["problems"] += self.evidence_problems(evidence_id)[0]
        if "metric_out_of_scope" not in result["problems"]:
            again = self.recompute(symbol, partner, period, inputs.get("baseline_period"))
            if again is None or _canonical(again) != _canonical(metric):
                result["problems"].append("recompute_mismatch")
                result["fields"] = sorted(k for k in types.METRIC_KEYS
                                          if again is None or _canonical(again.get(k)) != _canonical(metric.get(k)))
        result["problems"] = list(dict.fromkeys(result["problems"]))
        result["ok"] = not result["problems"]
        return result

    def evidence_result(self, evidence_id: str, returned: set[str]) -> dict:
        problems, failed_rule = self.evidence_problems(evidence_id)
        if evidence_id not in returned:
            problems = problems + ["evidence_not_returned"]
        return {"evidence_id": evidence_id, "ok": not problems, "problems": problems, "failed_rule": failed_rule}


def _body(snap: dal.Snapshot, request: dict, started: int) -> dict:
    problem = common.args_problem(request["args"], {"metric_ids": _refs_problem, "evidence_ids": _refs_problem})
    if problem:
        return common.refuse(request, TOOL, snap, started, problem)
    envelopes = request["envelopes"]
    _check_envelopes(envelopes, snap.snapshot_id)
    metrics, returned, partners = _returned(envelopes)
    checker = _Checker(snap, request, partners)
    metric_results = [checker.metric_result(metric_id, metrics.get(metric_id, []))
                      for metric_id in dict.fromkeys(request["args"].get("metric_ids", []))]
    evidence_results = [checker.evidence_result(evidence_id, returned)
                        for evidence_id in dict.fromkeys(request["args"].get("evidence_ids", []))]
    comparability = {"ok": all(r["ok"] for r in metric_results + evidence_results), "metrics": metric_results,
                     "evidence": evidence_results}
    scope = common.case_scope(request, months=[request["baseline_month"], request["month"]],
                              partners=sorted(checker.partners), hs10=[])
    return common.finish(request, TOOL, snap, started, scope=scope, evidence_ids=[], comparability=comparability)


def query(snap: dal.Snapshot, inp: object) -> dict:
    """열린 스냅샷(개발 빌드 포함)에서 근거를 대조한다."""
    return common.execute(snap, inp, TOOL, _body, needs_policy=True, needs_envelopes=True)


def run(inp: object) -> object:
    """진입 함수. 도구 요청 → 봉투(대조 결과). 스냅샷은 정본 빌드를 읽기 전용으로 연다."""
    return common.run_tool(inp, TOOL, _body, needs_policy=True, needs_envelopes=True)
