"""단위 I6 예산 집행.

단위 ID: I6
도메인명: tools_budget
소유: M
입력: 시도 기록
출력: 허용·거부(8회, 재조사 1회·그 안의 조회 2회, 같은 인자, deadline)
허용 import: 표준 라이브러리, tradesentry.contract

사례 하나의 도구 시도 기록과 새 시도(후보)를 받아, 후보를 도구에 넘겨도 되는지 코드로 정한다. 한도는 프롬프트가
아니라 이 코드가 강제한다(자료 계약 docs/rules/DATA_CONTRACT_V1.md §5.3, 개발 플랜 docs/plan/DEV_PLAN.md §6.6).
이 단위는 도구를 부르지 않는다. 도구를 부르고 결과를 기록하는 일은 흐름 조정(단위 I12)이 한다.

시도 기록 한 건: {"tool": 도구 이름, "args": 인자 객체, "stage": 단계, "outcome": 결과}
- 단계(stage): basic(기본 경로), critic(Critic 차례), revision(수정 단계), final(최종 검증). 흐름 조정의 단계 이름이다.
- 결과(outcome): ok(도구가 봉투를 돌려줌), failed(도구가 실패하거나 retryable_error를 돌려줌), cache_hit(도구를 다시
  부르지 않고 저장해 둔 결과로 답함), blocked(이 단위나 흐름이 막아 도구에 닿지 않음). 없으면 ok로 본다.

예산을 쓰는 결과(해석. 보고서에 적는다)
- ok·failed·cache_hit는 예산을 쓴다. 같은 도구를 다른 인자로 다시 부른 시도와 verify_evidence도 똑같이 쓴다
  (§5.3 "실패·같은 도구 재호출·캐시 적중·verify_evidence를 모두 센다").
- blocked는 예산을 쓰지 않는다. 단계별 몫(기본 5, 재조회 2, 최종 검증 1)의 합이 한도 8과 같으므로, 막힌 시도가 예산을
  쓰면 한 차례에 도구 호출을 여럿 낸 모델이 예약된 최종 검증 몫을 빼앗을 수 있기 때문이다.
- 그래서 "9번째 시도 차단"은 예산을 쓴 시도가 8건이면 그 뒤의 모든 시도를 막는다는 뜻으로 구현했다.
- 실행 결과 기록의 tool_attempts(§8.1)에 예산을 쓴 시도 수(consumed)를 적을지, 막힌 시도까지 센 기록 수(recorded)를
  적을지는 이 단위가 정하지 않는다(열린 결정, 보고서). 이 단위는 두 수를 모두 돌려준다.

판정 순서(앞에서 걸리면 멈춘다. 사유 이름은 흐름 조정의 budget_block 종류와 맞췄다)
1. deadline: now_ms와 deadline_ms를 받았고 now_ms ≥ deadline_ms면 막는다(전체 deadline이 먼저다).
2. unknown_tool: 도구 5개 밖의 이름이다.
3. critic_no_tools: Critic 차례에는 도구를 부르지 않는다(§5.3).
4. tool_attempts_limit: 예산을 쓴 시도가 한도(8)에 닿았다. 9번째 시도는 단계와 관계없이 여기서 막힌다.
5. revision_limit: 수정 단계는 1회다. 예산을 쓴 시도의 순서에서 revision이 이어진 한 덩어리를 수정 단계 하나로
   보고, 새 덩어리를 여는 후보를 막는다(흐름 조정은 수정 단계 번호를 넘기지 않으므로 순서로 판단한다).
6. 단계별 몫: basic_limit(기본 경로 5회, 그 가운데 1회는 verify_evidence 몫으로 남긴다), requery_limit(수정 단계의
   조회 2회. 세 번째 재조회를 막는다), final_verify_only·final_verify_limit(최종 단계는 verify_evidence 1회만).
7. same_args: 같은 도구를 같은 인자(정규화한 인자: 객체 키 순서, 목록의 순서·중복은 따지지 않는다)로 예산을 쓴
   시도가 이미 있으면 막는다. 동결 스냅샷이라 결과가 같고, 영구적 자료 부재를 같은 인자로 반복 조회하지 않기
   때문이다(개발 플랜 §6.6). verify_evidence는 뺀다: 흐름 조정이 예약한 차례에만 부르고, 같은 근거 목록이라도 그사이
   받은 봉투가 늘면 대조 결과가 달라질 수 있다. verify_evidence의 횟수는 5·6의 몫이 막는다.

한도 값(limits): 흐름 조정 설정(configs/model/model.json의 limits)과 같은 키 tool_attempts, basic_tool_attempts,
revision_stages, revision_requeries, final_verify를 읽는다. 빠진 키는 자료 계약 §5.3 값(8, 5, 1, 2, 1)이다. 다른
키(model_requests 등)는 다른 단위의 한도라 읽지 않는다. 값은 1 이상의 정수다.

run 입력: {"attempts": [시도 기록…], "candidate": {"tool", "args", "stage"}, "limits"?, "now_ms"?, "deadline_ms"?}
run 출력: {"allowed": 참거짓, "reason": 사유 또는 null, "same_as": 같은 인자 시도의 순번(0부터) 또는 null,
          "counts": {"recorded", "consumed", "basic", "revision", "final", "revision_stages"}, "remaining": 남은 예산}
counts는 후보를 더하기 전의 값이다. recorded는 막힌 시도까지 센 기록 수, consumed는 예산을 쓴 시도 수다.
"""
import json

from tradesentry.contract import types

STAGES = ("basic", "critic", "revision", "final")
OUTCOMES = ("ok", "failed", "cache_hit", "blocked")
CONSUMING_OUTCOMES = frozenset({"ok", "failed", "cache_hit"})  # 예산을 쓰는 결과
VERIFY_TOOL = "verify_evidence"
# 자료 계약 §5.3의 한도(조정값). 흐름 조정 설정의 키 이름을 쓴다.
CONTRACT_LIMITS = {"tool_attempts": 8, "basic_tool_attempts": 5, "revision_stages": 1, "revision_requeries": 2,
                   "final_verify": 1}

DEADLINE = "deadline"
UNKNOWN_TOOL = "unknown_tool"
CRITIC_NO_TOOLS = "critic_no_tools"
TOOL_ATTEMPTS_LIMIT = "tool_attempts_limit"
REVISION_LIMIT = "revision_limit"
BASIC_LIMIT = "basic_limit"
REQUERY_LIMIT = "requery_limit"
FINAL_VERIFY_ONLY = "final_verify_only"
FINAL_VERIFY_LIMIT = "final_verify_limit"
SAME_ARGS = "same_args"


def parse_limits(limits: object = None) -> dict[str, int]:
    """한도 객체를 읽는다. 빠진 키는 자료 계약 §5.3 값이고, 한도 밖의 키는 읽지 않는다."""
    if limits is None:
        return dict(CONTRACT_LIMITS)
    if not isinstance(limits, dict):
        raise ValueError("limits는 객체여야 한다")
    out = dict(CONTRACT_LIMITS)
    for key in CONTRACT_LIMITS:
        if key in limits:
            value = limits[key]
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"limits.{key}는 1 이상의 정수여야 한다")
            out[key] = value
    return out


def _normalize(value: object, where: str) -> object:
    if isinstance(value, dict):
        if not all(isinstance(k, str) for k in value):
            raise ValueError(f"{where}: 인자 객체의 키는 문자열이어야 한다")
        return {k: _normalize(v, f"{where}.{k}") for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        items = [_normalize(v, f"{where}[]") for v in value]
        unique = {json.dumps(v, sort_keys=True, ensure_ascii=False): v for v in items}
        return [unique[k] for k in sorted(unique)]
    if value is None or isinstance(value, (str, bool, int)):
        return value
    raise ValueError(f"{where}: 인자 값은 문자열·정수·참거짓·null·목록·객체만 쓴다({type(value).__name__})")


def canonical_args(args: object) -> str:
    """같은 인자인지 비교할 정규화 문자열. 객체 키 순서와 목록의 순서·중복은 따지지 않는다."""
    if not isinstance(args, dict):
        raise ValueError("args는 객체여야 한다")
    return json.dumps(_normalize(args, "args"), sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _check_record(record: object, where: str, *, candidate: bool) -> dict:
    """시도 기록(또는 후보) 한 건을 검사한다. 막힌 기록(blocked)은 형식이 틀린 모델 호출일 수 있어 도구 이름(null 가능)과
    인자를 따지지 않는다. 막힌 기록은 예산도 쓰지 않고 같은 인자 비교에도 쓰지 않는다."""
    if not isinstance(record, dict):
        raise ValueError(f"{where}는 객체여야 한다")
    keys = {"tool", "args", "stage"} if candidate else {"tool", "args", "stage", "outcome"}
    if not {"tool", "args", "stage"} <= set(record) or not set(record) <= keys:
        raise ValueError(f"{where}의 키는 {', '.join(sorted(keys))}다")
    if record["stage"] not in STAGES:
        raise ValueError(f"{where}.stage는 {', '.join(STAGES)} 가운데 하나여야 한다")
    outcome = "ok" if candidate else record.get("outcome", "ok")
    if outcome not in OUTCOMES:
        raise ValueError(f"{where}.outcome은 {', '.join(OUTCOMES)} 가운데 하나여야 한다")
    tool = record["tool"]
    if outcome == "blocked":
        if tool is not None and not isinstance(tool, str):
            raise ValueError(f"{where}.tool은 문자열이나 null이어야 한다")
        return {"tool": tool, "key": None, "stage": record["stage"], "outcome": outcome}
    if not isinstance(tool, str) or not tool:
        raise ValueError(f"{where}.tool은 빈 문자열이 아닌 문자열이어야 한다")
    if not candidate and tool not in types.TOOLS:
        raise ValueError(f"{where}.tool이 도구 5개 가운데 하나가 아니다(도구 밖 이름은 blocked로만 기록한다)")
    return {"tool": tool, "key": canonical_args(record["args"]), "stage": record["stage"], "outcome": outcome}


def _clock(now_ms: object, deadline_ms: object) -> tuple[int, int] | None:
    if now_ms is None and deadline_ms is None:
        return None
    for name, value in (("now_ms", now_ms), ("deadline_ms", deadline_ms)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name}는 정수여야 한다(now_ms와 deadline_ms는 함께 준다)")
    return now_ms, deadline_ms


def _counts(records: list[dict]) -> dict[str, int]:
    consumed = [r for r in records if r["outcome"] in CONSUMING_OUTCOMES]
    runs, previous = 0, None
    for record in consumed:
        if record["stage"] == "revision" and previous != "revision":
            runs += 1
        previous = record["stage"]
    return {"recorded": len(records), "consumed": len(consumed),
            "basic": sum(r["stage"] == "basic" for r in consumed),
            "revision": sum(r["stage"] == "revision" for r in consumed),
            "final": sum(r["stage"] == "final" for r in consumed), "revision_stages": runs}


def _verdict(allowed: bool, reason: str | None, counts: dict, limits: dict, same_as: int | None = None) -> dict:
    return {"allowed": allowed, "reason": reason, "same_as": same_as, "counts": counts,
            "remaining": max(0, limits["tool_attempts"] - counts["consumed"])}


def decide(attempts: object, candidate: object, limits: object = None, *, now_ms: object = None,
           deadline_ms: object = None) -> dict:
    """시도 기록과 후보로 허용·거부를 정한다(머리 설명의 판정 순서)."""
    if not isinstance(attempts, list):
        raise ValueError("attempts는 시도 기록의 목록이어야 한다")
    records = [_check_record(a, f"attempts[{i}]", candidate=False) for i, a in enumerate(attempts)]
    cand = _check_record(candidate, "candidate", candidate=True)
    lim = parse_limits(limits)
    clock = _clock(now_ms, deadline_ms)
    counts = _counts(records)

    if clock is not None and clock[0] >= clock[1]:
        return _verdict(False, DEADLINE, counts, lim)
    if cand["tool"] not in types.TOOLS:
        return _verdict(False, UNKNOWN_TOOL, counts, lim)
    stage, tool = cand["stage"], cand["tool"]
    if stage == "critic":
        return _verdict(False, CRITIC_NO_TOOLS, counts, lim)
    if counts["consumed"] >= lim["tool_attempts"]:
        return _verdict(False, TOOL_ATTEMPTS_LIMIT, counts, lim)
    consumed = [r for r in records if r["outcome"] in CONSUMING_OUTCOMES]
    if stage == "revision":
        opens_stage = not consumed or consumed[-1]["stage"] != "revision"
        if opens_stage and counts["revision_stages"] >= lim["revision_stages"]:
            return _verdict(False, REVISION_LIMIT, counts, lim)
        if counts["revision"] >= lim["revision_requeries"]:
            return _verdict(False, REQUERY_LIMIT, counts, lim)
    elif stage == "basic":
        verified = any(r["stage"] == "basic" and r["tool"] == VERIFY_TOOL for r in consumed)
        reserve = 0 if tool == VERIFY_TOOL or verified else 1
        if counts["basic"] + reserve >= lim["basic_tool_attempts"]:
            return _verdict(False, BASIC_LIMIT, counts, lim)
    elif stage == "final":
        if tool != VERIFY_TOOL:
            return _verdict(False, FINAL_VERIFY_ONLY, counts, lim)
        if counts["final"] >= lim["final_verify"]:
            return _verdict(False, FINAL_VERIFY_LIMIT, counts, lim)
    if tool != VERIFY_TOOL:
        for index, record in enumerate(records):
            if record["outcome"] in CONSUMING_OUTCOMES and record["tool"] == tool and record["key"] == cand["key"]:
                return _verdict(False, SAME_ARGS, counts, lim, same_as=index)
    return _verdict(True, None, counts, lim)


class ToolBudget:
    """사례 하나의 시도 기록을 가진 얇은 감싸개. 흐름 조정이 시도마다 gate → (도구 호출) → record 순으로 쓴다.

    - gate: 판정하고, 막히면 그 시도를 blocked로 기록한다. 허용이면 기록하지 않는다(부른 뒤 결과로 기록한다).
    - record: 도구를 부른 결과(ok·failed·cache_hit)나 흐름이 막은 시도(blocked)를 기록한다.
    - recorded: 막힌 시도까지 센 기록 수. consumed: 예산을 쓴 시도 수. 실행 결과 기록의 tool_attempts에 어느 쪽을
      적을지는 열린 결정이다(머리 설명).
    - deadline_ms를 주면 check·gate에 now_ms를 함께 줘야 deadline을 본다.
    """

    def __init__(self, limits: object = None, *, deadline_ms: int | None = None) -> None:
        self.limits = parse_limits(limits)
        self.deadline_ms = deadline_ms
        self.attempts: list[dict] = []

    def check(self, tool: str, args: dict, stage: str, *, now_ms: int | None = None) -> dict:
        deadline = self.deadline_ms if now_ms is not None else None
        return decide(self.attempts, {"tool": tool, "args": args, "stage": stage}, self.limits,
                      now_ms=now_ms if deadline is not None else None, deadline_ms=deadline)

    def gate(self, tool: str, args: dict, stage: str, *, now_ms: int | None = None) -> dict:
        verdict = self.check(tool, args, stage, now_ms=now_ms)
        if not verdict["allowed"]:
            self.record(tool, args, stage, "blocked")
        return verdict

    def record(self, tool: str, args: dict, stage: str, outcome: str) -> None:
        entry = {"tool": tool, "args": args, "stage": stage, "outcome": outcome}
        _check_record(entry, "record", candidate=False)
        self.attempts.append(entry)

    @property
    def recorded(self) -> int:
        return len(self.attempts)

    @property
    def consumed(self) -> int:
        return sum(a["outcome"] in CONSUMING_OUTCOMES for a in self.attempts)


def run(inp: object) -> object:
    """진입 함수. 시도 기록과 후보 → 허용·거부 판정(머리 설명의 run 입출력)."""
    if not isinstance(inp, dict) or not {"attempts", "candidate"} <= set(inp) \
            or not set(inp) <= {"attempts", "candidate", "limits", "now_ms", "deadline_ms"}:
        raise ValueError("입력은 attempts·candidate(와 limits·now_ms·deadline_ms)를 가진 객체다")
    return decide(inp["attempts"], inp["candidate"], inp.get("limits"), now_ms=inp.get("now_ms"),
                  deadline_ms=inp.get("deadline_ms"))
