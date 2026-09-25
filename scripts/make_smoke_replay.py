"""run-case 실행 폴더의 trace에서 --replay 재생 파일(키 없는 스모크 재현)을 만든다.

쓰는 법(저장소 루트): uv run --locked python scripts/make_smoke_replay.py <실행 폴더> <재생 파일 경로>
  예: uv run --locked python scripts/make_smoke_replay.py outputs/run_case-260926021320 eval/dev/smoke/850450-XA-202412.json

실행 폴더는 `tradesentry run-case`가 남긴 outputs/run_case-{시각}/(runlog_trace-{시각}.jsonl과 runlog_run_record-{시각}.json)이다.
재생 파일은 JSON 객체다(결정 기록 docs/tracking/decisions/20260926-*-model-decision-smoke-replay.md, 자료 계약 §10.3):
- "trace": trace의 model_request·model_response·model_error 레코드만 기록 순서대로(단위 I8 ReplayTransport가 읽는 레코드.
  model_request의 request_sha256과 model_response의 response·usage, model_error의 http_status·headers·backoff 등이 그대로다).
- "requests": [] (단위 I8 골든 입력 {"trace", "requests"}와 같은 모양. CLI는 요청을 흐름이 만들므로 비운다).
- "source": 원 실행의 run_id, case_id, snapshot_id, policy_version, mode, code_version, model_config, execution_status,
  review_status_final. CLI(load_replay)는 case_id·snapshot_id·policy_version·mode가 요청과 같은지 본다.
검사: 만든 파일의 문자열에 키 모양(단위 E1 SECRET_SHAPE)이나 로컬 절대 경로 모양(PATH_SHAPE)이 있으면 쓰지 않고 실패한다.
원 실행이 COMPLETED가 아니면 실패한다(스모크 재현은 끝까지 도는 실행만 재생한다). 이미 있는 파일은 덮지 않는다.
"""
import sys
from pathlib import Path

from tradesentry.evaluation.batch_run import PATH_SHAPE, SECRET_SHAPE
from tradesentry.runlog import trace as trace_log

REPLAY_EVENTS = ("model_request", "model_response", "model_error")
SOURCE_KEYS = ("run_id", "case_id", "snapshot_id", "policy_version", "mode", "code_version", "execution_status",
               "review_status_final")


def _strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def build(run_dir: Path) -> dict:
    [trace_file] = sorted(run_dir.glob("runlog_trace-*.jsonl"))
    [record_file] = sorted(run_dir.glob("runlog_run_record-*.json"))
    records = trace_log.read_records(trace_file)
    record = trace_log.loads(record_file.read_text(encoding="utf-8"))
    if record.get("execution_status") != "COMPLETED":
        raise SystemExit(f"원 실행이 COMPLETED가 아니다({record.get('execution_status')}). 스모크 재현은 끝까지 돈 실행만 재생한다")
    starts = [r["data"] for r in records if r.get("event") == "run_start"]
    source = {k: record.get(k) for k in SOURCE_KEYS}
    source["model_config"] = starts[0].get("model_config") if starts else None
    trace = [r for r in records if r.get("event") in REPLAY_EVENTS]
    if not any(r["event"] == "model_response" for r in trace):
        raise SystemExit("trace에 model_response가 없다(checklist 실행은 재생할 것이 없다)")
    doc = {"trace": trace, "requests": [], "source": source}
    bad = [s for s in _strings(doc) if PATH_SHAPE.search(s) or SECRET_SHAPE.search(s)]
    if bad:
        raise SystemExit(f"재생 파일에 로컬 절대 경로나 키 모양의 문자열이 {len(bad)}개 있어 쓰지 않는다")
    return doc


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    run_dir, out = Path(argv[0]), Path(argv[1])
    doc = build(run_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "xb") as handle:
        handle.write((trace_log.dumps(doc) + "\n").encode("utf-8"))
    print(f"{out}: 모델 레코드 {len(doc['trace'])}개, 사례 {doc['source']['case_id']}, 원 실행 {doc['source']['run_id']} "
          f"({doc['source']['review_status_final']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
