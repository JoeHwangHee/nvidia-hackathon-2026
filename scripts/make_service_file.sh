#!/bin/bash
# 서비스 파일(한 쪽) 생성: docs/submission/service_file.html의 {{REPO_URL}}을 인자로 바꾼 뒤
# pdf(Chrome headless)와 docx(macOS textutil)를 outputs/submission_service_file-{시각}/에 만든다.
# 사용(저장소 루트에서): scripts/make_service_file.sh "<공개 저장소 URL>"
# 파일 이름은 대회 안내의 [NVIDIA 해커톤_팀명_프로젝트명] 규칙을 따른다. 키·비밀값은 쓰지 않는다.
set -euo pipefail
URL="${1:?공개 저장소 URL}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TEMPLATE="$ROOT/docs/submission/service_file.html"
STAMP="$(date +%y%m%d%H%M%S)"
OUT="$ROOT/outputs/submission_service_file-$STAMP"
NAME="[NVIDIA 해커톤_TradeSentry_TradeSentry]"
CHROME="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
mkdir -p "$OUT"
HTML="$OUT/service_file-$STAMP.html"
python3 - "$TEMPLATE" "$HTML" "$URL" <<'PY'
import sys, html
src, dst, url = sys.argv[1:4]
text = open(src, encoding="utf-8").read().replace("{{REPO_URL}}", html.escape(url, quote=True))
open(dst, "w", encoding="utf-8").write(text)
PY
if [ -x "$CHROME" ]; then
  PROFILE="$OUT/.chrome-profile"; mkdir -p "$PROFILE"
  # Chrome headless는 pdf를 쓴 뒤 종료하지 않을 수 있어 배경으로 띄우고 파일이 생기면 그 프로세스만 끝낸다(별도 프로필이라 사용 중인 Chrome은 건드리지 않는다).
  "$CHROME" --headless=new --disable-gpu --no-first-run --no-default-browser-check \
    --user-data-dir="$PROFILE" --no-pdf-header-footer \
    --print-to-pdf="$OUT/$NAME.pdf" "file://$HTML" >/dev/null 2>&1 &
  CPID=$!
  for _ in $(seq 1 60); do [ -s "$OUT/$NAME.pdf" ] && { sleep 1; break; }; sleep 1; done
  kill "$CPID" 2>/dev/null || true
  pkill -f -- "--user-data-dir=$PROFILE" 2>/dev/null || true
  rm -rf "$PROFILE"
  [ -s "$OUT/$NAME.pdf" ] || echo "pdf 생성 실패(Chrome headless). html을 브라우저에서 열어 pdf로 저장한다: $HTML" >&2
else
  echo "Chrome을 찾지 못해 pdf를 만들지 않았다(CHROME_BIN으로 경로를 줄 수 있다). html: $HTML" >&2
fi
if command -v textutil >/dev/null 2>&1; then
  textutil -convert docx -output "$OUT/$NAME.docx" "$HTML" >/dev/null 2>&1 || echo "docx 변환 실패" >&2
fi
echo "출력 폴더: ${OUT#$ROOT/}"
ls -1 "$OUT"
