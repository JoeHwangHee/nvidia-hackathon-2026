#!/usr/bin/env python3
"""X1 최소 CLI(임시 시험 코드). 앱 코드가 아니며 S0 결과에 섞지 않는다.

입력 한 줄을 받아 NIM(NVIDIA 클라우드 추론 API)을 1회 호출하고,
NAT(NVIDIA NeMo Agent Toolkit)의 파일 추적 내보내기로 실행 추적 1건을 남긴다.

    python x1_probe.py --input "<한 줄>" [--mode rewrite|inference-local] [--runs-dir <경로>]

- 키는 코드·인자·파일에 없다. rewrite 방식에서는 OpenShell provider가 샌드박스 환경에 넣은
  자리표시 값(환경변수 NVIDIA_API_KEY)을 Authorization 헤더에 싣고, 샌드박스 안 감독 프로세스
  (root로 도는 openshell-sandbox)의 정책 프록시가 게이트웨이에서 받은 자격 증명으로 요청 시점에
  실제 키로 바꾼다. inference-local 방식에서는 헤더를 싣지 않고 https://inference.local/v1로 보낸다.
- 5xx는 코드가 명시적으로 다시 보낸다(요청당 최대 3회, 지수 대기). 4xx는 다시 보내지 않는다.
- 산출물: <runs-dir>/<run_id>/nat_trace.jsonl(NAT 추적), app_trace.jsonl(앱 기록, 비밀값 없음),
  nat_workflow.yml(이번 실행에 쓴 NAT 설정 사본).
- --key-check: NIM 호출 전에 이 프로세스(하네스가 띄웠다면 그 자식)에서 key_check.run_check를 돌린다.
  실제 키 형식이 하나라도 나오면 NIM을 부르지 않고 종료 코드 5로 끝난다. 값은 출력하지 않는다.
- --violation-probe <URL>: NIM 호출 뒤 허용 목록 밖으로 의도적 요청 1건(GET)을 보내 차단되는지 기록한다.
  결과는 출력 JSON의 violation_probe에 담고, 종료 코드에는 반영하지 않는다.
- 종료 코드: 0 = HTTP 200과 응답 본문 수신, 3 = HTTP 오류, 4 = 연결 실패, 5 = 실제 키 발견, 2 = 인자 오류.
"""

import argparse
import asyncio
import datetime
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
import uuid

import yaml
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig
from nat.runtime.loader import load_workflow

HERE = pathlib.Path(__file__).resolve().parent
MODES = {
    "rewrite": ("https://integrate.api.nvidia.com/v1", "NVIDIA_API_KEY"),
    "inference-local": ("https://inference.local/v1", ""),
}
DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b"


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class X1NimOnceConfig(FunctionBaseConfig, name="x1_nim_once"):
    base_url: str = MODES["rewrite"][0]
    model: str = DEFAULT_MODEL
    api_key_env: str = "NVIDIA_API_KEY"
    max_tokens: int = 64
    timeout_s: float = 90.0
    max_5xx_retries: int = 3
    app_trace_path: str = ""


def _append_app_trace(path, event):
    if not path:
        return
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")


def _post_once(url, body, headers, timeout_s):
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def _call_nim(config, prompt):
    url = config.base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": config.model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": config.max_tokens,
        "temperature": 0,
    }
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    auth_source = "none"
    if config.api_key_env:
        placeholder = os.environ.get(config.api_key_env, "")
        if placeholder:
            headers["Authorization"] = "Bearer " + placeholder
            auth_source = "env:" + config.api_key_env
    body = json.dumps(payload).encode("utf-8")
    attempts = 0
    status, raw = None, b""
    while True:
        attempts += 1
        started = time.monotonic()
        try:
            status, raw = _post_once(url, body, headers, config.timeout_s)
            error = None
        except (urllib.error.URLError, OSError) as exc:
            status, raw, error = None, b"", "%s: %s" % (exc.__class__.__name__, getattr(exc, "reason", exc))
        elapsed = round(time.monotonic() - started, 3)
        _append_app_trace(config.app_trace_path, {
            "ts": _now(), "event": "nim_request", "attempt": attempts, "url": url,
            "method": "POST", "model": config.model, "auth_header_from": auth_source,
            "http_status": status, "elapsed_s": elapsed, "error": error,
        })
        if status is not None and 500 <= status < 600 and attempts <= config.max_5xx_retries:
            time.sleep(2 ** (attempts - 1))
            continue
        break
    result = {"http_status": status, "attempts": attempts, "model": config.model}
    if status == 200:
        try:
            data = json.loads(raw.decode("utf-8"))
            choice = (data.get("choices") or [{}])[0]
            content = ((choice.get("message") or {}).get("content") or "").strip()
            result["content"] = content[:500]
            result["usage"] = data.get("usage")
        except ValueError:
            result["content"] = ""
            result["parse_error"] = True
    else:
        # 오류 본문은 앞부분만 남긴다(프록시 거부 사유 확인용). 비밀값은 본문에 없다.
        result["error_body_head"] = raw[:300].decode("utf-8", "replace") if raw else None
        if status is None:
            result["error"] = "connection_failed"
    return result


@register_function(config_type=X1NimOnceConfig)
async def x1_nim_once(config: X1NimOnceConfig, builder: Builder):
    async def _run(prompt: str) -> str:
        """입력 한 줄로 NIM을 1회 호출하고 결과를 JSON 문자열로 돌려준다."""
        result = await asyncio.to_thread(_call_nim, config, prompt)
        return json.dumps(result, ensure_ascii=False)

    yield FunctionInfo.from_fn(_run, description="X1: call NIM chat completions once")


def build_config(template_path, run_dir, mode, model, api_key_env=None):
    base_url, key_env = MODES[mode]
    if api_key_env is not None and key_env:
        key_env = api_key_env
    with open(template_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    cfg["general"]["telemetry"]["tracing"]["x1_file"]["output_path"] = str(run_dir / "nat_trace.jsonl")
    wf = cfg["workflow"]
    wf["base_url"] = base_url
    wf["api_key_env"] = key_env
    wf["model"] = model
    wf["app_trace_path"] = str(run_dir / "app_trace.jsonl")
    out = run_dir / "nat_workflow.yml"
    with open(out, "w", encoding="utf-8") as fh:
        yaml.safe_dump(cfg, fh, sort_keys=False, allow_unicode=True)
    return out


async def run_once(config_path, text):
    async with load_workflow(config_path) as session_manager:
        async with session_manager.session() as session:
            async with session.run(text) as runner:
                out = await runner.result(to_type=str)
    # NAT 내보내기의 stop()은 백그라운드 쓰기 작업을 기다리지 않는다(nat 1.9.0 base_exporter 주석).
    # 이벤트 루프가 닫히기 전에 남은 작업을 기다려 WORKFLOW_END까지 파일에 남긴다.
    pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if pending:
        await asyncio.wait(pending, timeout=5.0)
    return out


def violation_probe(url, app_trace_path):
    """허용 목록 밖 목적지로 GET 1건. 차단되면 blocked=True."""
    req = urllib.request.Request(url, method="GET")
    out = {"url": url, "method": "GET"}
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            out["http_status"] = resp.status
    except urllib.error.HTTPError as exc:
        out["http_status"] = exc.code
        out["body_head"] = exc.read()[:200].decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as exc:
        out["http_status"] = None
        out["error"] = "%s: %s" % (exc.__class__.__name__, getattr(exc, "reason", exc))
    out["blocked"] = out.get("http_status") in (None, 403, 407)
    _append_app_trace(app_trace_path, dict({"ts": _now(), "event": "violation_probe"}, **out))
    return out


def main(argv):
    ap = argparse.ArgumentParser(description="X1 probe: one line -> one NIM call -> one NAT trace")
    ap.add_argument("--input", required=True)
    ap.add_argument("--mode", choices=sorted(MODES), default="rewrite")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--runs-dir", default=os.environ.get("X1_RUNS_DIR", "/tmp/x1-runs"))
    ap.add_argument("--config-template", default=str(HERE / "nat_workflow.yml"))
    ap.add_argument("--api-key-env", default=None,
                    help="rewrite 모드에서 자리표시 값을 읽을 환경변수 이름(기본 NVIDIA_API_KEY)")
    ap.add_argument("--key-check", action="store_true")
    ap.add_argument("--violation-probe", default="")
    args = ap.parse_args(argv)
    if len(args.input) > 500 or "\n" in args.input:
        sys.stderr.write("x1_probe: --input은 500자 이하 한 줄이어야 한다\n")
        return 2

    run_id = datetime.datetime.now().strftime("%Y%m%dT%H%M%S") + "-x1-" + uuid.uuid4().hex[:6]
    run_dir = pathlib.Path(args.runs_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    if args.api_key_env is not None and not args.api_key_env.replace("_", "").isalnum():
        sys.stderr.write("x1_probe: --api-key-env는 환경변수 이름이어야 한다\n")
        return 2
    config_path = build_config(args.config_template, run_dir, args.mode, args.model, args.api_key_env)
    app_trace = str(run_dir / "app_trace.jsonl")
    _append_app_trace(app_trace, {
        "ts": _now(), "event": "run_start", "run_id": run_id, "mode": args.mode,
        "model": args.model, "pid": os.getpid(), "ppid": os.getppid(), "exe": sys.executable,
    })
    key_report = None
    if args.key_check:
        import key_check  # 같은 폴더의 모듈
        key_report = key_check.run_check(
            roots=("/sandbox", "/tmp", "/etc", "/home", "/root", "/app"),
            harness_paths=("/sandbox/.openclaw/openclaw.json", "/sandbox/.openclaw/agents",
                           "/sandbox/.nemoclaw", "/run/nemoclaw", "/etc/openshell"),
            max_files=5000)
        _append_app_trace(app_trace, {"ts": _now(), "event": "key_check", **key_report})
        if key_report["real_key_total"] != 0:
            print(json.dumps({"run_id": run_id, "run_dir": str(run_dir), "exit_code": 5,
                              "key_check": key_report}, ensure_ascii=False))
            return 5
    output = asyncio.run(run_once(str(config_path), args.input))
    try:
        result = json.loads(output)
    except ValueError:
        result = {"http_status": None, "raw_output": output[:300]}
    status = result.get("http_status")
    rc = 0 if status == 200 and "content" in result else (4 if status is None else 3)
    if key_report is not None:
        result["key_check"] = {k: key_report[k] for k in (
            "verdict", "real_key_total", "env_NVIDIA_API_KEY", "proc_environ_readable",
            "proc_environ_unreadable", "proc_environ_real_key_hits", "ppid")}
    if args.violation_probe:
        result["violation_probe"] = violation_probe(args.violation_probe, app_trace)
    _append_app_trace(str(run_dir / "app_trace.jsonl"), {
        "ts": _now(), "event": "run_end", "run_id": run_id, "http_status": status, "exit_code": rc,
    })
    print(json.dumps({"run_id": run_id, "run_dir": str(run_dir), "exit_code": rc, **result},
                     ensure_ascii=False))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
