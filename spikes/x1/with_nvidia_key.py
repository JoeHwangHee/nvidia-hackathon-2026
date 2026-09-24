#!/usr/bin/env python3
"""X1 임시 키 래퍼(표준 라이브러리만 쓴다).

env 파일에서 NVIDIA_API_KEY 한 줄만 읽어 자식 프로세스 환경에만 넣고 명령을 실행한다.
자식의 stdout·stderr는 줄 단위로 읽어, 키 값과 똑같은 문자열을 ***REDACTED***로 바꿔 내보낸다.
키를 디스크에 쓰지 않고, 자식의 종료 코드를 그대로 돌려준다.

사용법:
    python3 spikes/x1/with_nvidia_key.py --env-file <경로> [--export-as <변수 이름>] -- <명령 ...>

- --env-file: 키가 든 env 파일 경로. 코드에 경로를 적지 않고 인자로만 받는다.
- --export-as: 자식 환경에 넣을 변수 이름(기본 NVIDIA_API_KEY). 값은 같은 키이고, 이름만 바꾼다.
  예: NemoClaw 온보딩은 NVIDIA_INFERENCE_API_KEY 이름을 읽는다.
- 다른 변수(DATA_GO_KR_SERVICE_KEY 등)는 읽지 않는다. 자식 환경에서 그 변수와 봉인 폴더 변수는 뺀다.
- 키의 앞부분·끝부분 조각이 출력에 보이면 그 조각도 가리고 stderr에 경고 한 줄을 남긴다
  (조각 출력도 키 노출로 보고 사람이 판단한다).
"""

import argparse
import os
import re
import subprocess
import sys
import threading

KEY_NAME = "NVIDIA_API_KEY"
REDACTED = b"***REDACTED***"
DROP_FROM_CHILD = ("DATA_GO_KR_SERVICE_KEY", "TRADESENTRY_SEALED_DIR")
LINE_RE = re.compile(r"^\s*(?:export\s+)?" + KEY_NAME + r"\s*=\s*(.*?)\s*$")
VAR_NAME_RE = re.compile(r"^[A-Z_][A-Z0-9_]*$")


def read_key(env_file):
    """env 파일에서 NVIDIA_API_KEY 줄만 골라 값을 돌려준다. 없으면 None."""
    with open(env_file, "r", encoding="utf-8") as fh:
        for raw in fh:
            if KEY_NAME not in raw:
                continue
            m = LINE_RE.match(raw.rstrip("\n"))
            if not m:
                continue
            value = m.group(1)
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            return value or None
    return None


class Redactor:
    def __init__(self, key):
        self.key = key.encode("utf-8")
        # 조각: 앞 10글자(접두어+4글자), 끝 6글자. 키가 짧으면 조각 검사를 하지 않는다.
        self.fragments = []
        if len(self.key) >= 24:
            self.fragments = [self.key[:10], self.key[-6:]]
        self.fragment_seen = False
        self.lock = threading.Lock()

    def redact(self, line):
        out = line.replace(self.key, REDACTED)
        for frag in self.fragments:
            if frag in out:
                out = out.replace(frag, REDACTED)
                with self.lock:
                    self.fragment_seen = True
        return out


def pump(src, dst, redactor):
    """자식 출력 한 줄씩 가려서 내보낸다. readline()은 줄 끝까지 모으므로 키가 조각 경계에 걸리지 않는다."""
    try:
        for line in iter(src.readline, b""):
            dst.write(redactor.redact(line))
            dst.flush()
    finally:
        src.close()


def main(argv):
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--export-as", default=KEY_NAME)
    parser.add_argument("cmd", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)

    cmd = args.cmd
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        sys.stderr.write("with_nvidia_key: 실행할 명령이 없다(-- 뒤에 명령을 준다)\n")
        return 2
    if not VAR_NAME_RE.match(args.export_as):
        sys.stderr.write("with_nvidia_key: --export-as 값이 변수 이름 형식이 아니다\n")
        return 2

    try:
        key = read_key(args.env_file)
    except OSError as exc:
        sys.stderr.write("with_nvidia_key: env 파일을 읽지 못했다: %s\n" % exc.__class__.__name__)
        return 2
    if not key:
        sys.stderr.write("with_nvidia_key: env 파일에 %s 줄이 없다\n" % KEY_NAME)
        return 2

    child_env = dict(os.environ)
    for name in DROP_FROM_CHILD:
        child_env.pop(name, None)
    child_env[args.export_as] = key

    redactor = Redactor(key)
    try:
        proc = subprocess.Popen(
            cmd,
            env=child_env,
            stdin=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        sys.stderr.write("with_nvidia_key: 명령을 시작하지 못했다: %s\n" % exc.__class__.__name__)
        return 127
    finally:
        key = None
        child_env = None

    threads = [
        threading.Thread(target=pump, args=(proc.stdout, sys.stdout.buffer, redactor)),
        threading.Thread(target=pump, args=(proc.stderr, sys.stderr.buffer, redactor)),
    ]
    for t in threads:
        t.start()
    rc = proc.wait()
    for t in threads:
        t.join()
    if redactor.fragment_seen:
        sys.stderr.write(
            "with_nvidia_key: WARNING 자식 출력에서 키 조각을 발견해 가렸다. 키 노출 의심으로 다룬다\n"
        )
        sys.stderr.flush()
    if rc < 0:
        return 128 + (-rc)
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
