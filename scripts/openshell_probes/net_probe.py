#!/usr/bin/env python3
"""위반 시험용 네트워크 탐침(단위 F7의 샌드박스 안 탐침, 소유 M). 표준 라이브러리만, Python 3.8 이상.

    python net_probe.py GET <URL>
    python net_probe.py POST <URL>                     본문 {} (키를 싣지 않는다)
    python net_probe.py NIM <URL> --key-env <변수 이름> [--model <모델 ID>]

NIM은 대조군(허용되어야 하는 추론 요청 1건)이다. 샌드박스 환경변수의 자리표시 값을 `Authorization: Bearer` 헤더에
실어 보내면 샌드박스 안 감독 프로세스의 정책 프록시가 실제 키로 바꾼다(결정 기록 1556). 헤더 값과 응답 본문은
출력하지 않는다. 리디렉션은 따라가지 않는다(키가 다른 호스트로 가지 않게).
결과는 JSON 한 줄이다. 종료 코드: 0 HTTP 2xx, 3 HTTP 오류 응답(4xx·5xx), 4 연결 실패(프록시 CONNECT 거부 포함),
5 키 변수가 없거나 헤더에 쓸 수 없는 값, 2 인자 오류. 403을 받아도 0으로 끝나지 않는다.
"""
import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _usage():
    sys.stderr.write("usage: net_probe.py GET|POST <URL> | NIM <URL> --key-env <NAME> [--model <ID>]\n")
    return 2


def main(argv):
    if len(argv) < 2:
        return _usage()
    method, url, rest = argv[0].upper(), argv[1], argv[2:]
    out = {"method": method, "url": url, "exe": sys.executable}
    headers = {"Content-Type": "application/json"}
    data = None
    if method == "NIM":
        options = dict(zip(rest[0::2], rest[1::2]))
        if len(rest) % 2 or set(options) - {"--key-env", "--model"} or "--key-env" not in options:
            return _usage()
        name = options["--key-env"]
        value = os.environ.get(name, "")
        out["key_env"] = name
        if not value or not all(33 <= ord(char) <= 126 for char in value):
            out["error"] = "key_env_missing_or_invalid"
            out["exit_code"] = 5
            print(json.dumps(out, ensure_ascii=False))
            return 5
        body = {"model": options.get("--model", DEFAULT_MODEL), "max_tokens": 8, "temperature": 0,
                "messages": [{"role": "user", "content": "Reply with exactly: OK"}]}
        data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(url, data=data, method="POST", headers=headers)
        request.add_unredirected_header("Authorization", "Bearer " + value)
        value = None
    elif method in ("GET", "POST") and not rest:
        data = b"{}" if method == "POST" else None
        request = urllib.request.Request(url, data=data, method=method, headers=headers)
    else:
        return _usage()
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(request, timeout=60) as response:
            out["http_status"] = response.status
            response.read(1)
            code = 0 if 200 <= response.status < 300 else 3
    except urllib.error.HTTPError as exc:
        out["http_status"] = exc.code
        head = exc.read()[:200].decode("utf-8", "replace")
        if method != "NIM" or "policy" in head:
            out["body_head"] = head
        code = 3
    except (urllib.error.URLError, OSError) as exc:
        out["http_status"] = None
        out["error"] = "%s: %s" % (exc.__class__.__name__, getattr(exc, "reason", exc))
        code = 4
    out["exit_code"] = code
    print(json.dumps(out, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
