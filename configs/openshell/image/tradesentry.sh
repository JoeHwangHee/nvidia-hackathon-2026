#!/bin/sh
# TradeSentry CLI 실행기(단위 F5, 소유 M). 이미지 안 위치는 /opt/tradesentry/bin/tradesentry다.
#
# 이 파일이 있는 폴더의 부모(앱 뿌리)를 스스로 찾으므로 옮겨도 돈다.
#   - 채점 대상 실행 샌드박스: /opt/tradesentry(이미지에 구운 읽기 전용 배치). 가상환경 파이썬(.venv/bin/python)으로 연다.
#   - NemoClaw 시연 샌드박스: 이미지에서 꺼낸 /opt/tradesentry 묶음을 /sandbox/tradesentry로 올려 푼 사본. 가상환경은
#     옮길 수 없으므로 가상환경 파이썬이 없으면 uv 관리 Python(python/current)과 PYTHONPATH로 연다(X1 run_probe.sh 방식).
# 어느 쪽이든 실제 실행 파일은 {앱 뿌리}/python/ 아래의 Python 3.12.13이다. 채점 대상 실행 정책은 그 폴더
# (/opt/tradesentry/python/**)에만 추론 요청 한 경로를 연다. 하위 프로세스를 띄우지 않고 exec로 바꿔 탄다.
# CLI의 실행 폴더는 현재 폴더 기준 outputs/{실행명}/다. 샌드박스에서는 /sandbox에서 부른다.
# NAT 명령 진입점과 의존성의 .env 자동 로드와 사용 통계 전송을 끈다(docs/engineering-notes.md).
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)
PYTHONDONTWRITEBYTECODE=1
PYTHONNOUSERSITE=1
PYTHON_DOTENV_DISABLED=1
NAT_TELEMETRY_ENABLED=false
# 앱 코드는 늘 {앱 뿌리}/src에서 읽는다(가상환경의 editable 설치 기록은 이미지 안 경로를 가리켜 사본에서는 맞지 않는다).
PYTHONPATH="$root/src"
export PYTHONDONTWRITEBYTECODE PYTHONNOUSERSITE PYTHON_DOTENV_DISABLED NAT_TELEMETRY_ENABLED PYTHONPATH
# 키 변수 이름(결정 기록 model-decision-mt5-sandbox ⑩). CLI는 NVIDIA_API_KEY(configs/model/model.json의 api_key_env)를 읽는다.
# 채점 대상 실행 샌드박스는 provider tradesentry-nvidia가 그 이름으로 자리표시 값을 넣는다. NemoClaw 시연 샌드박스는 온보딩이
# 만든 provider nvidia-prod가 NVIDIA_INFERENCE_API_KEY로만 넣으므로, NVIDIA_API_KEY가 없고 그 값이 자리표시 값
# (openshell:resolve:env: 접두어)일 때에만 같은 값을 NVIDIA_API_KEY로도 둔다. 실제 키 모양 값은 옮기지 않고 출력하지 않는다.
# 자리표시 값은 정책 프록시가 요청 시점에 실제 키로 바꾸는 표시일 뿐 키가 아니다(결정 기록 1556, 요건 (c) 해석 A).
if [ -z "${NVIDIA_API_KEY:-}" ]; then
  case "${NVIDIA_INFERENCE_API_KEY:-}" in
    openshell:resolve:env:*) NVIDIA_API_KEY=$NVIDIA_INFERENCE_API_KEY; export NVIDIA_API_KEY ;;
  esac
fi
if [ -x "$root/.venv/bin/python" ]; then
  exec "$root/.venv/bin/python" -m tradesentry.cli "$@"
fi
PYTHONPATH="$root/src:$root/.venv/lib/python3.12/site-packages"
exec "$root/python/current/bin/python3.12" -m tradesentry.cli "$@"
