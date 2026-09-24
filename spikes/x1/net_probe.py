#!/usr/bin/env python3
"""X1 위반 시험용 네트워크 탐침(표준 라이브러리만). 키를 싣지 않는다.

    python net_probe.py <METHOD> <URL>

결과를 JSON 한 줄로 낸다. 종료 코드: 0 = HTTP 2xx, 3 = HTTP 오류 응답(4xx·5xx),
4 = 연결 실패(프록시 CONNECT 거부 포함). 403을 받아도 0으로 끝나지 않는다.
"""

import json
import sys
import urllib.error
import urllib.request


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: net_probe.py <METHOD> <URL>\n")
        return 2
    method, url = argv[0].upper(), argv[1]
    data = b"{}" if method in ("POST", "PUT", "PATCH") else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    out = {"method": method, "url": url, "exe": sys.executable}
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            out["http_status"] = resp.status
            rc = 0 if 200 <= resp.status < 300 else 3
    except urllib.error.HTTPError as exc:
        out["http_status"] = exc.code
        out["body_head"] = exc.read()[:200].decode("utf-8", "replace")
        rc = 3
    except (urllib.error.URLError, OSError) as exc:
        out["http_status"] = None
        out["error"] = "%s: %s" % (exc.__class__.__name__, getattr(exc, "reason", exc))
        rc = 4
    out["exit_code"] = rc
    print(json.dumps(out, ensure_ascii=False))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
