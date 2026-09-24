#!/bin/sh
# X1 시연 샌드박스용 CLI 실행기(임시 시험 코드).
# 호스트에서 올린 Python 3.12(독립 실행형)와 NAT 패키지를 /sandbox/x1opt에서 쓴다.
# 순서: 키 조회(하네스가 띄운 프로세스에서) -> NIM 1회 + NAT 추적 -> 허용 목록 밖으로 의도적 요청 1건.
set -eu
BASE=/sandbox/x1opt
export PYTHONPATH="$BASE/venv/lib/python3.12/site-packages"
export PYTHONDONTWRITEBYTECODE=1
exec "$BASE/python/cpython-3.12.13-linux-aarch64-gnu/bin/python3.12" "$BASE/app/x1_probe.py" \
  --input "${1:-Reply with exactly: X1 OK}" \
  --mode rewrite \
  --api-key-env NVIDIA_INFERENCE_API_KEY \
  --runs-dir /sandbox/x1-runs \
  --key-check \
  --violation-probe https://api.github.com/zen
