#!/usr/bin/env python3
"""G4 probe: NIM hosted endpoint 에서 Nemotron 이 native tool call 을 내고, 로컬 Python 도구 결과를 받아 근거 포함 응답을 만드는지 확인한다.

표준 라이브러리만 사용. NVIDIA_API_KEY 는 .env 또는 환경변수에서 읽고 어디에도 기록하지 않는다.

  python3 scripts/g4_nim_toolcall_probe.py                 # 2개 시나리오(비교가능/비교불가) 실행, trace 저장
  python3 scripts/g4_nim_toolcall_probe.py --thinking      # reasoning ON 으로 재실행

통과 기준 (계획서 G4): 모델의 native tool call → 실제 Python 도구 실행 → tool 결과 반환 → 근거(evidence_id) 포함 응답이 trace 에 남아야 한다.
단순 채팅 성공은 불충분. 서로 다른 입력(비교가능/비교불가)에서 서로 다른 다음 도구를 고르는지도 본다.
출처: https://build.nvidia.com/nvidia/nemotron-3-super-120b-a12b , https://docs.api.nvidia.com/nim/reference/nvidia-nemotron-3-super-120b-a12b
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MODEL = os.environ.get("NIM_MODEL", "nvidia/nemotron-3-super-120b-a12b")


def load_env(path: Path = ROOT / ".env") -> None:
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


# ---- 실제 Python 도구 (스텁: 고정 snapshot 대신 시나리오 값 반환. 계획서 5.2 도구 계약의 출력 필드 형태만 맞춘다) ----
SCENARIOS = {
    "comparable": {"case_id": "C-DEMO-A", "snapshot_id": "controlled_demo_v0", "comparability": {"period_ok": True, "units_ok": True, "hs_version_ok": True, "denominator": "official_total", "hs10_available": True}, "missingness": []},
    "not_comparable": {"case_id": "C-DEMO-C", "snapshot_id": "controlled_demo_v0", "comparability": {"period_ok": True, "units_ok": True, "hs_version_ok": True, "denominator": "official_total", "hs10_available": False}, "missingness": ["HS10 응답 실패: REQUEST_FAILED (202401, CN, 850450*)"]},
}
CALLS: list[dict] = []


def check_comparability(case_id: str, snapshot_id: str, scenario: str) -> dict:
    s = SCENARIOS[scenario]
    out = {"query_id": f"q-{len(CALLS)+1}", "tool": "check_comparability", "scope": {"case_id": case_id, "snapshot_id": snapshot_id}, "snapshot_id": s["snapshot_id"], "source_kind": "controlled",
           "evidence_ids": [f"ev-cmp-{scenario}"], "metrics": {}, "comparability": s["comparability"], "missingness": s["missingness"], "retryable_error": None, "elapsed_ms": 1}
    CALLS.append(out)
    return out


def get_history(case_id: str, snapshot_id: str, scenario: str) -> dict:
    out = {"query_id": f"q-{len(CALLS)+1}", "tool": "get_history", "scope": {"case_id": case_id, "snapshot_id": snapshot_id}, "snapshot_id": snapshot_id, "source_kind": "controlled",
           "evidence_ids": ["ev-hist-1"], "metrics": {"unit_value_t": 3.6, "unit_value_t12": 6.0, "r_U": -0.4, "share_t_pp": 6.0, "share_t12_pp": 10.0, "d_s_pp": -4.0}, "comparability": {}, "missingness": [], "retryable_error": None, "elapsed_ms": 1}
    CALLS.append(out)
    return out


TOOLS = [
    {"type": "function", "function": {"name": "check_comparability", "description": "기간/단위/HS버전/분모/하위자료(HS10) 존재 상태를 반환한다. 판정을 내리지 않는다.",
                                       "parameters": {"type": "object", "properties": {"case_id": {"type": "string"}, "snapshot_id": {"type": "string"}}, "required": ["case_id", "snapshot_id"]}}},
    {"type": "function", "function": {"name": "get_history", "description": "대상 HS6/국가의 전년동월 단위가치·점유율 비교 수치를 evidence_id 와 함께 반환한다. check_comparability 가 비교 가능이라고 한 경우에만 호출한다.",
                                       "parameters": {"type": "object", "properties": {"case_id": {"type": "string"}, "snapshot_id": {"type": "string"}}, "required": ["case_id", "snapshot_id"]}}},
]
SYSTEM = ("당신은 TradeSentry 조사자다. 도구 결과만 근거로 쓴다. 먼저 check_comparability 를 호출하고, 비교 가능하면 get_history 를 호출한다. "
          "하위자료(HS10)가 없거나 missingness 가 있으면 추가 조회 없이 '자료 보류' 초안을 쓴다. 최종 답은 JSON 한 개: "
          '{"review_status": "유지|모니터링|보류", "evidence_ids": [...], "reason": "..."} 형식으로만 답한다.')


def chat(messages: list[dict], thinking: bool, max_tokens: int = 1024, timeout: int = 60) -> dict:
    load_env()
    key = os.environ.get("NVIDIA_API_KEY")
    if not key:
        sys.exit("NVIDIA_API_KEY 가 없습니다 (.env). https://build.nvidia.com 에서 발급.")
    body = {"model": MODEL, "messages": messages, "tools": TOOLS, "tool_choice": "auto", "temperature": 1.0, "top_p": 0.95, "max_tokens": max_tokens, "stream": False,
            "chat_template_kwargs": {"enable_thinking": thinking, **({"low_effort": True} if thinking else {})}}
    t0 = time.time()
    data: dict = {}
    attempts = 0
    for attempt in range(3):  # 실측(2026-09-23): 무료 엔드포인트가 간헐적 HTTP 500 을 내므로 5xx 는 최대 2회 재시도(2s/4s). 재시도는 model_request_attempts 에 포함해 기록.
        attempts += 1
        req = urllib.request.Request(BASE_URL, data=json.dumps(body).encode(), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read())
            break
        except urllib.error.HTTPError as e:
            data = {"error": f"HTTP {e.code}", "body": e.read().decode("utf-8", "replace")[:2000]}
            if e.code < 500:
                break
            time.sleep(2 * (attempt + 1))
        except Exception as e:  # noqa: BLE001
            data = {"error": f"{type(e).__name__}: {e}"}
            time.sleep(2 * (attempt + 1))
    data["_elapsed_ms"] = int((time.time() - t0) * 1000)
    data["_attempts"] = attempts
    return data


def run_scenario(name: str, thinking: bool, trace: list[dict]) -> dict:
    CALLS.clear()
    case = SCENARIOS[name]
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"case_id={case['case_id']} snapshot_id={case['snapshot_id']} 초기 경보: 단위가치 전년동월 대비 -40%. 조사 후 판정 초안을 작성하라."}]
    model_requests, tool_attempts, native_tool_call = 0, 0, False
    for step in range(4):  # 최대 4회 모델 요청 (probe 용 소형 예산)
        resp = chat(messages, thinking)
        model_requests += resp.get("_attempts", 1)
        trace.append({"scenario": name, "step": step, "request_messages": messages[-1], "response": resp})
        if "error" in resp:
            return {"scenario": name, "ok": False, "error": resp["error"], "detail": resp.get("body", "")[:300]}
        msg = resp["choices"][0]["message"]
        tcs = msg.get("tool_calls") or []
        if not tcs:
            content = (msg.get("content") or "").strip()
            return {"scenario": name, "ok": True, "native_tool_call": native_tool_call, "tool_attempts": tool_attempts, "tools_called": [c["tool"] for c in CALLS], "model_requests_incl_retries": model_requests,
                    "final": content[:600], "final_mentions_evidence": any(e in content for c in CALLS for e in c["evidence_ids"]), "usage": resp.get("usage"), "elapsed_ms": resp["_elapsed_ms"],
                    "policy_note": ("비교불가인데 get_history 호출됨 (프롬프트 지시 미준수)" if name == "not_comparable" and "get_history" in [c["tool"] for c in CALLS] else None)}
        native_tool_call = True
        messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": tcs})
        for tc in tcs:
            tool_attempts += 1
            fn = tc["function"]["name"]
            try:
                args = json.loads(tc["function"].get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {}
            if fn == "check_comparability":
                result = check_comparability(args.get("case_id", ""), args.get("snapshot_id", ""), name)
            elif fn == "get_history":
                result = get_history(args.get("case_id", ""), args.get("snapshot_id", ""), name)
            else:
                result = {"error": f"unknown tool {fn}"}
            messages.append({"role": "tool", "tool_call_id": tc.get("id"), "name": fn, "content": json.dumps(result, ensure_ascii=False)})
    return {"scenario": name, "ok": False, "error": "probe budget exhausted (4 model requests)", "tools_called": [c["tool"] for c in CALLS]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thinking", action="store_true", help="reasoning ON (low_effort). 기본은 OFF")
    args = ap.parse_args()
    out_dir = ROOT / "artifacts" / "runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    trace: list[dict] = []
    results = [run_scenario("comparable", args.thinking, trace), run_scenario("not_comparable", args.thinking, trace)]
    (out_dir / f"g4_probe_{stamp}.trace.jsonl").write_text("\n".join(json.dumps(t, ensure_ascii=False) for t in trace), encoding="utf-8")
    summary = {"model": MODEL, "thinking": args.thinking, "at": stamp, "results": results,
               "G4_pass": all(r.get("ok") and r.get("native_tool_call") and r.get("final_mentions_evidence") for r in results)
               and results[0].get("tools_called") != results[1].get("tools_called")}
    (out_dir / f"g4_probe_{stamp}.summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print("G4 판정 기준: 두 시나리오 모두 native tool_calls 발생 + 도구 결과의 evidence_id 가 최종 응답에 포함 + 비교가능/불가에서 호출된 도구 목록이 다름. 이 probe 는 NAT 연동이 아니라 NIM 왕복만 확인한다.")


if __name__ == "__main__":
    main()
