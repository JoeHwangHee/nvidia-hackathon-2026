"""OpenShell 정책·증거 공용 도구(단위 F4·F7이 함께 쓴다, 소유 M). 표준 라이브러리만 쓴다.

OpenShell(에이전트를 격리해 돌리는 NVIDIA 샌드박스 런타임)의 정책 YAML과 `openshell policy get <이름> --full` 출력을 다룬다.
정책 해시 규칙의 정본은 MT5 샌드박스 결정 기록(docs/tracking/decisions/의 model-decision-mt5-sandbox) ⑥이다.

- parse_yaml: 정책 파일과 라이브 정책 본문이 쓰는 좁은 YAML 부분집합만 읽는다(블록 매핑·블록 시퀀스·평범한 스칼라·
  따옴표 문자열·정수·참거짓·빈 `{}`/`[]`). 모르는 문법은 조용히 넘기지 않고 YamlSubsetError로 멈춘다. 이 저장소의
  lock에는 아직 YAML 라이브러리가 없어서(로드맵 MT4가 더한다) 시험과 스크립트가 따로 읽는다.
- split_policy_get / normalize_body: 조회 출력에서 해시할 바이트를 꺼낸다(첫 `---` 줄 뒤 본문, ANSI 제어열 제거,
  줄 끝 LF, 줄 끝 공백 제거, 앞뒤 빈 줄 제거, 마지막 줄바꿈 하나).
- substitute_host_paths: 경로 치환 규칙 하나. 호스트 경로만 바꾸고 샌드박스 안 경로는 그대로 둔다.
- judge_requirement_b: 개발 플랜 §4.1 요건 (b)(외부 전송은 NVIDIA 추론 엔드포인트만, L7 method·path 명시, rules 생략과
  범용 바이너리 + `/**` 금지)를 정책 구조로 판정한다.

키 값은 이 모듈이 다루지 않는다. has_key_shape는 NVIDIA API 키 모양 문자열이 섞였는지만 본다(접두어는 조각을 이어
만든다. 비밀값 검사 규칙과 같은 방식이다).
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
KEY_PREFIX = "nv" + "api" + "-"
KEY_RE = re.compile(re.escape(KEY_PREFIX) + r"[A-Za-z0-9_\-]{20,}")
PLACEHOLDER_PREFIX = "openshell:resolve:env:"

# 요건 (b)의 허용 목적지(채점 대상 실행 샌드박스는 하나, 개발 플랜 §4.6)
NVIDIA_INFERENCE_HOST = "integrate.api.nvidia.com"
CHAT_PATH = "/v1/chat/completions"
# 시연 샌드박스에서 빼야 하는 NemoClaw 기본 블록(개발 플랜 §4.8, X1 4판)
FORBIDDEN_BLOCK_NAMES = ("clawhub", "openclaw_docs", "npm_registry", "managed_inference", "openclaw_api",
                         "openclaw_gateway_dialback")
# 가린 뒤에도 남으면 안 되는 호스트 로컬 경로 모양(macOS 사용자·임시 폴더). 비밀값·로컬 경로 검사에 이 파일 자체가
# 걸리지 않게 조각을 이어 만든다.
_LOCAL_PREFIXES = ("/" + "Users" + "/", "/" + "private" + "/", "/" + "var/folders" + "/")
LOCAL_PATH_RE = re.compile("(?:" + "|".join(re.escape(p) for p in _LOCAL_PREFIXES) + r")[^\s'\"\]\),;]*")
LOCAL_PATH_MASK = "<로컬 경로 가림>"


class YamlSubsetError(ValueError):
    """좁은 YAML 부분집합 밖의 문법이거나 모양이 틀렸다. 문장에는 줄 번호만 넣는다."""


class PolicyOutputError(ValueError):
    """`openshell policy get --full` 출력에서 본문을 꺼내지 못했다."""


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def has_key_shape(text: str) -> bool:
    """NVIDIA API 키 모양 문자열이 있는지 본다(값은 돌려주지 않는다)."""
    return bool(KEY_RE.search(text))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ---------------------------------------------------------------- 좁은 YAML 부분집합

_UNSUPPORTED_START = ("&", "*", "!", "|", ">", "%", "@", "`")


def _strip_comment(line: str) -> str:
    """따옴표 밖의 `#` 주석을 뗀다. 줄 첫 글자이거나 앞이 공백인 `#`만 주석이다."""
    quote = None
    for index, char in enumerate(line):
        if quote:
            if char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
        elif char == "#" and (index == 0 or line[index - 1] in " \t"):
            return line[:index]
    return line


def _lines(text: str) -> list[list]:
    """(줄 번호, 들여쓰기, 내용) 목록. 빈 줄과 주석 줄은 뺀다. 탭 들여쓰기와 문서 표지는 멈춘다."""
    result = []
    for number, raw in enumerate(text.replace("\r\n", "\n").replace("\r", "\n").split("\n"), start=1):
        body = _strip_comment(raw).rstrip()
        if not body.strip():
            continue
        lead = body[: len(body) - len(body.lstrip(" \t"))]
        if "\t" in lead:
            raise YamlSubsetError(f"{number}행: 탭 들여쓰기는 읽지 않는다")
        content = body.strip()
        if content in ("---", "..."):
            raise YamlSubsetError(f"{number}행: 문서 표지는 읽지 않는다")
        result.append([number, len(lead), content])
    return result


def _is_seq(content: str) -> bool:
    return content == "-" or content.startswith("- ")


def _split_key(content: str, number: int) -> tuple[str, str] | None:
    """`키: 값`이나 `키:`이면 (키, 값)을, 매핑 항목이 아니면 None을 돌려준다."""
    if content[:1] in ("'", '"'):
        quote = content[0]
        end = content.find(quote, 1)
        if end < 0:
            raise YamlSubsetError(f"{number}행: 닫히지 않은 따옴표")
        rest = content[end + 1:]
        if rest == ":" or rest.startswith(": "):
            return content[1:end], rest[1:].strip()
        return None
    if content.endswith(":") and ": " not in content:
        key, value = content[:-1], ""
    elif ": " in content:
        key, value = content.split(": ", 1)
    else:
        return None
    if not key or key[0] in _UNSUPPORTED_START or key.startswith(("- ", "{", "[")):
        return None
    return key.strip(), value.strip()


def _scalar(token: str, number: int):
    if token in ("{}",):
        return {}
    if token in ("[]",):
        return []
    if token[:1] in ("{", "["):
        raise YamlSubsetError(f"{number}행: 비어 있지 않은 흐름 표기는 읽지 않는다")
    if token[:1] in _UNSUPPORTED_START:
        raise YamlSubsetError(f"{number}행: 지원하지 않는 표기({token[0]})")
    if token[:1] in ("'", '"'):
        quote = token[0]
        if len(token) < 2 or token[-1] != quote:
            raise YamlSubsetError(f"{number}행: 따옴표 문자열 모양이 틀렸다")
        inner = token[1:-1]
        if quote == "'":
            return inner.replace("''", "'")
        if "\\" in inner.replace("\\\\", "").replace('\\"', ""):
            raise YamlSubsetError(f"{number}행: 지원하지 않는 이스케이프")
        return inner.replace('\\"', '"').replace("\\\\", "\\")
    if token in ("true", "True"):
        return True
    if token in ("false", "False"):
        return False
    if token in ("null", "~", "Null"):
        return None
    if re.fullmatch(r"-?[0-9]+", token):
        return int(token)
    return token


def _parse_node(lines: list[list], index: int, indent: int):
    if _is_seq(lines[index][2]):
        return _parse_seq(lines, index, indent)
    return _parse_map(lines, index, indent)


def _parse_seq(lines: list[list], index: int, indent: int):
    items = []
    while index < len(lines):
        number, col, content = lines[index]
        if col != indent or not _is_seq(content):
            if col > indent:
                raise YamlSubsetError(f"{number}행: 들여쓰기가 맞지 않는다")
            break
        rest = content[1:].lstrip(" ")
        if not rest:
            index += 1
            if index < len(lines) and lines[index][1] > indent:
                value, index = _parse_node(lines, index, lines[index][1])
            else:
                value = None
            items.append(value)
            continue
        item_col = col + (len(content) - len(rest))
        if _split_key(rest, number) is not None:
            lines[index] = [number, item_col, rest]
            value, index = _parse_map(lines, index, item_col)
        else:
            value = _scalar(rest, number)
            index += 1
        items.append(value)
    return items, index


def _parse_map(lines: list[list], index: int, indent: int):
    result: dict = {}
    while index < len(lines):
        number, col, content = lines[index]
        if col < indent:
            break
        if col > indent:
            raise YamlSubsetError(f"{number}행: 들여쓰기가 맞지 않는다")
        if _is_seq(content):
            break
        pair = _split_key(content, number)
        if pair is None:
            raise YamlSubsetError(f"{number}행: 매핑 항목이 아니다")
        key, rest = pair
        if key in result:
            raise YamlSubsetError(f"{number}행: 같은 키가 두 번 나온다({key})")
        index += 1
        if rest:
            value = _scalar(rest, number)
        elif index < len(lines) and lines[index][1] > indent:
            value, index = _parse_node(lines, index, lines[index][1])
        elif index < len(lines) and lines[index][1] == indent and _is_seq(lines[index][2]):
            value, index = _parse_seq(lines, index, indent)
        else:
            value = None
        result[key] = value
    return result, index


def parse_yaml(text: str):
    """좁은 YAML 부분집합을 읽어 dict·list·스칼라로 돌려준다. 빈 문서는 None이다."""
    lines = _lines(text)
    if not lines:
        return None
    if lines[0][1] != 0:
        raise YamlSubsetError(f"{lines[0][0]}행: 첫 항목은 들여쓰지 않는다")
    value, index = _parse_node(lines, 0, 0)
    if index != len(lines):
        raise YamlSubsetError(f"{lines[index][0]}행: 읽지 못한 줄이 남았다")
    return value


# ---------------------------------------------------------------- 라이브 정책 조회 본문(해시 규칙)

def normalize_body(text: str) -> str:
    """해시할 본문 바이트의 모양: ANSI 제어열 제거, 줄 끝 LF, 줄 끝 공백 제거, 앞뒤 빈 줄 제거, 마지막 줄바꿈 하나."""
    lines = [line.rstrip(" \t") for line in strip_ansi(text).replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    if not lines:
        raise PolicyOutputError("정책 본문이 비어 있다")
    return "\n".join(lines) + "\n"


def split_policy_get(stdout: str) -> tuple[dict[str, str], str]:
    """`openshell policy get <이름> --full` 출력 → (머리 항목, 정규화한 본문).

    머리는 첫 `---` 줄 앞의 `이름: 값` 줄들이다(Version·Hash·Status·Source·Config rev). 본문은 그 줄 뒤 전부다.
    """
    lines = strip_ansi(stdout).replace("\r\n", "\n").replace("\r", "\n").split("\n")
    header: dict[str, str] = {}
    for position, line in enumerate(lines):
        if line.rstrip(" \t") == "---":
            return header, normalize_body("\n".join(lines[position + 1:]))
        if ":" in line:
            name, value = line.split(":", 1)
            if name.strip():
                header[name.strip()] = value.strip()
    raise PolicyOutputError("출력에 `---` 줄이 없다")


def substitute_host_paths(text: str, *, repo_root: Path | None = None, home: Path | None = None,
                          sealed_dir: Path | None = None, tmp_dir: Path | None = None) -> tuple[str, int]:
    """경로 치환 규칙 하나(결정 기록 ⑥). 호스트 경로만 바꾸고 샌드박스 안 경로는 바꾸지 않는다.

    긴 경로부터 차례로 바꾼다: 봉인 폴더 → `$TRADESENTRY_SEALED_DIR`, 저장소 루트 → 루트 기준 상대경로(루트 자체는 `.`),
    임시 폴더 → `$TMPDIR`, 홈 폴더 → `$HOME`. 그 뒤에도 macOS 로컬 경로 모양이 남으면 `<로컬 경로 가림>`으로 바꾸고 그
    개수를 돌려준다. 같은 경로의 실제 경로(resolve)와 적힌 경로를 모두 바꾼다.
    """
    pairs: list[tuple[str, str]] = []
    for path, token in ((sealed_dir, "$TRADESENTRY_SEALED_DIR"), (repo_root, ""), (tmp_dir, "$TMPDIR"),
                        (home, "$HOME")):
        if path is None:
            continue
        for form in {str(path), str(Path(path).resolve())}:
            form = form.rstrip("/")
            if len(form) > 1:
                pairs.append((form, token))
    pairs.sort(key=lambda pair: len(pair[0]), reverse=True)
    for form, token in pairs:
        if token == "":
            text = text.replace(form + "/", "").replace(form, ".")
        else:
            text = text.replace(form, token)
    masked = len(LOCAL_PATH_RE.findall(text))
    if masked:
        text = LOCAL_PATH_RE.sub(LOCAL_PATH_MASK, text)
    return text, masked


# ---------------------------------------------------------------- 정책 구조 판정

def network_blocks(policy: dict) -> dict:
    blocks = policy.get("network_policies") or {}
    if not isinstance(blocks, dict):
        raise YamlSubsetError("network_policies가 매핑이 아니다")
    return blocks


def _glob_is_broad(path: str) -> bool:
    return "*" in path


def judge_requirement_b(policy: dict, *, allowed_hosts: tuple[str, ...] = (NVIDIA_INFERENCE_HOST,)
                        ) -> tuple[bool, list[str]]:
    """요건 (b)를 정책 구조로 판정한다. (충족 여부, 어긴 이유 목록)."""
    reasons: list[str] = []
    blocks = network_blocks(policy)
    for name in sorted(blocks):
        block = blocks[name] or {}
        if name in FORBIDDEN_BLOCK_NAMES:
            reasons.append(f"블록 {name}: 빼야 하는 기본 블록")
        endpoints = block.get("endpoints") or []
        if not endpoints:
            reasons.append(f"블록 {name}: endpoints가 없다")
        for endpoint in endpoints:
            host = str(endpoint.get("host", ""))
            if host not in allowed_hosts:
                reasons.append(f"블록 {name}: 허용하지 않은 목적지 {host or '(host 없음)'}")
            # L7 규칙이 실제로 걸리려면 protocol rest와 enforcement enforce가 있어야 한다(audit는 기록만 하고 통과시킨다)
            if endpoint.get("port") != 443:
                reasons.append(f"블록 {name}: {host} port가 443이 아니다")
            if endpoint.get("protocol") != "rest":
                reasons.append(f"블록 {name}: {host} protocol이 rest가 아니다(L7 검사 없음)")
            if endpoint.get("enforcement") != "enforce":
                reasons.append(f"블록 {name}: {host} enforcement가 enforce가 아니다")
            rules = endpoint.get("rules")
            if not rules:
                reasons.append(f"블록 {name}: {host} rules 생략(host:port 전체 개방)")
                continue
            for rule in rules:
                allow = (rule or {}).get("allow") or {}
                method, path = str(allow.get("method", "")), str(allow.get("path", ""))
                if not method or method == "*":
                    reasons.append(f"블록 {name}: method가 없거나 `*`다")
                if not path or _glob_is_broad(path):
                    reasons.append(f"블록 {name}: path가 없거나 글롭({path or '없음'})이다")
        if not block.get("binaries"):
            reasons.append(f"블록 {name}: binaries가 없다")
    return (not reasons), reasons


def allowlist_entries(policy: dict) -> list[tuple[str, str]]:
    """(종류, 경로) 목록. 종류는 read_only·read_write다."""
    fs = policy.get("filesystem_policy") or {}
    return [(kind, str(path)) for kind in ("read_only", "read_write") for path in (fs.get(kind) or [])]


def covering_entries(policy: dict, target: str) -> list[str]:
    """target 경로를 덮는(같거나 앞부분이 일치하는) 허용 목록 항목."""
    target = target.rstrip("/")
    hits = []
    for kind, entry in allowlist_entries(policy):
        base = entry.rstrip("/") or "/"
        if target == base or target.startswith(base + "/") or base == "/":
            hits.append(f"{kind}:{entry}")
    return hits


def top_level_sections(body: str) -> list[tuple[str, str]]:
    """본문을 최상위 키 단위 조각 (키, 조각 글자)로 나눈다. 주석과 빈 줄은 앞 조각에 붙는다."""
    sections: list[tuple[str, list[str]]] = []
    for line in body.replace("\r\n", "\n").split("\n"):
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):", line)
        if match:
            sections.append((match.group(1), [line]))
        elif sections:
            sections[-1][1].append(line)
        elif line.strip() and not line.lstrip().startswith("#"):
            raise YamlSubsetError("최상위 키 앞에 내용이 있다")
    return [(name, "\n".join(chunk).rstrip("\n")) for name, chunk in sections]


def compose_network(live_body: str, network_file_text: str) -> str:
    """라이브 정책 본문의 정적 계층을 그대로 두고 network_policies 조각만 바꾼 본문을 만든다(시연 샌드박스용).

    network_file_text는 `version`과 `network_policies`만 담은 파일이다. 라이브 본문의 network_middlewares는 건드리지 않는다.
    """
    ours = dict(top_level_sections("\n".join(
        line for line in network_file_text.split("\n") if not line.lstrip().startswith("#"))))
    if set(ours) != {"version", "network_policies"}:
        raise YamlSubsetError("시연 네트워크 파일은 version과 network_policies만 담는다")
    parts = [chunk for name, chunk in top_level_sections(live_body) if name != "network_policies"]
    parts.append(ours["network_policies"])
    composed = normalize_body("\n".join(parts))
    live, new = parse_yaml(live_body), parse_yaml(composed)
    for key in ("version", "filesystem_policy", "landlock", "process"):
        if live.get(key) != new.get(key):
            raise YamlSubsetError(f"합친 본문의 {key}가 라이브 정책과 다르다")
    return composed
