"""단위 V2 dev20 생성.

단위 ID: V2
도메인명: datagen_dev20
소유: D
입력: dev20 생성 규칙(합성 세계, 사례별 자료 사건, 손으로 정한 기대 판정. 정본 eval/dev/dev20/answers/generation_rules.json)
출력: dev20 입력(사례 목록, 수집기 형식 원천)·정답표·부모 원본 계열 ID 목록의 텍스트 파일과 자체 검산 요약
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.ingest, tradesentry.snapshot, eval.datagen

metrics/·policy/와 그것들을 부르는 모듈을 직접이든 간접이든 import하지 않는다(경계 시험이 본다). 지표는 이 파일 안에서
자료 계약 docs/rules/DATA_CONTRACT_V1.md §2.3.2 행 규칙과 §11.2 공식으로 따로 계산한다(지표 단위 구현을 보지 않았다).
tradesentry.ingest를 허용 import에 더했다: 합성 원천을 수집기 형식(요청 ID, manifest, 응답 XML, 수집기 SQLite)으로 만들고
단위 S2(tradesentry.snapshot.build)로 빌드해야 단위 S3 검사를 통과하기 때문이다(DT1 결정 기록 20260925-0002 ⑨).

무엇을 하나(정본: 공개 명세 eval/scenarios/SCENARIO_SPEC.md, 결정 기록 docs/tracking/decisions/의 DT5 기록)
- 생성 규칙의 합성 세계(HS4 하나, HS6·상대국 목록, 계열마다 HS10 하위품목의 기본 월 값, 나머지 세계 값, 작은 결정적
  흔들림)에 사례별 사건(그 달 하위 값 지정, 부모 행 덮어쓰기, 비교국 규모·단가 배율, 전체국가 분모 덮어쓰기, 요청 실패·
  미수집)을 얹어 36개월 자료를 만든다. 사례 판정의 기대값(signals, signal_status, review_status, unresolved_evidence,
  required_evidence)은 생성 규칙에 손으로 적은 값이고, 이 코드는 사례별 기대 상태를 담지 않는다.
- 자료를 수집기 형식 원천으로 쓴다: `manifest.json`(수집기 build_manifest의 요청 목록), 응답 XML(`raw/<request_id>.xml`),
  요청 결과 기록(`collection_log.json`: 실패·미수집 요청 ID), raw 결합 해시(`snapshot_hash.json`), 합성 비교국 표
  (`peer_group_dev20_g0.csv`: 합성 자료 안에서 g0 규칙으로 고른 비교국, grouping_version `g0`).
- 자체 검산(구 개발계획 §8.1 "생성 자료를 독립 검사"): 응답 XML을 다시 읽어 모든 계열·달의 단가 변화율과 점유율 변화를
  계산하고, 발동한 (HS6, 상대국, 달)의 집합이 사례 집합과 정확히 같은지(사례 밖 경보 0건), 사례마다 발동 여부가 기대값과
  같은지, 모든 값이 탐지 기준에서 0.05 이상 떨어졌는지, 판정 근거 규칙마다 자료 불변식(구성효과 사례는 하위 단가 변화 0,
  설명 안 됨 사례는 구성효과를 뺀 within+잔차가 기준 이상 등)이 맞는지 본다. 하나라도 어긋나면 ValueError다.
- 임시 폴더에 수집기 SQLite를 재현하고(수집기 store_result로 응답을 적재, 시각은 생성 규칙의 고정 시각) 단위 S2로 빌드해
  `normalized_sha256`을 구하고, 단위 S3로 검증한다. 사례 목록·정답표는 단위 V4의 형식·분류 규칙 검사를 통과해야 한다.

출력(`run`): {"files": {묶음 기준 상대경로: 텍스트}, "summary": {...}}. 묶음의 파일 배치(결정 기록에 남긴다):
- `input/cases.json`: 사례 목록(`case_id`·`hs6`·`partner`·`month`만). 채점 대상 실행 샌드박스가 읽는 입력 하위 경로다.
- `input/source/`: 수집기 형식 원천(위 다섯 종류). 빌드한 SQLite는 커밋하지 않고 명령 `install`이 다시 만든다.
- `answers/answers.json`: 정답표. `answers/parent_series_ids.json`: dev20 부모 원본 계열 ID 목록(holdout40 제외 목록).
  `answers/generation_rules.json`: 생성 규칙 그대로(정본 직렬화). 정답 하위 경로는 어떤 샌드박스에도 넣지 않는다.

명령(저장소 루트에서, 키 없이)
- `uv run --locked python -m eval.datagen.dev20 generate [--rules <생성 규칙>] [--place]`: 실행 폴더
  `outputs/datagen_dev20-{시각}/`(실행명 확보 N8)의 `datagen_dev20-{시각}/` 폴더(N7)에 묶음을 쓰고 요약을
  `datagen_dev20-{시각}.json`에 쓴다. `--place`면 묶음을 `eval/dev/dev20/`로 옮긴다(이미 있는 파일은 덮지 않는다, N12).
- `uv run --locked python -m eval.datagen.dev20 check`: 커밋된 생성 규칙으로 다시 만들어 `eval/dev/dev20/`의 파일과 바이트
  단위로 대조한다(파일을 쓰지 않는다). 같으면 0, 다르면 1.
- `uv run --locked python -m eval.datagen.dev20 install`: 커밋된 원천으로 수집기 SQLite를 재현하고 단위 S2로 빌드해 실행
  폴더에 두고, 단위 S3 검증과 `normalized_sha256` 대조(사례 목록의 기록값)를 통과하면 정본 자리
  `data/snapshots/dev20/snapshot_build.sqlite`(git이 추적하지 않는 자리)로 옮긴다(S2 install_build). 이미 설치돼 있으면
  옮기지 않고 해시만 대조한다.
"""
import argparse
import csv
import hashlib
import io
import json
import os
import sqlite3
import sys
import tempfile
import time
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from pathlib import Path
from xml.sax.saxutils import escape

from eval.datagen import holdout40_check as v4
from tradesentry import ingest
from tradesentry.contract import types
from tradesentry.contract.policy_load import load_policy
from tradesentry.snapshot import build as s2
from tradesentry.snapshot import verify as s3

REPO_ROOT = Path(__file__).resolve().parents[2]
DOMAIN = "datagen_dev20"
DEV20_DIR = "eval/dev/dev20"
RULES_FILE = DEV20_DIR + "/answers/generation_rules.json"
INSTALL_DIR = "data/snapshots"

CASES_FILE = "input/cases.json"
SOURCE = "input/source"
MANIFEST_FILE = "manifest.json"
LOG_FILE = "collection_log.json"
HASH_FILE = "snapshot_hash.json"
ANSWERS_FILE = "answers/answers.json"
IDS_FILE = "answers/parent_series_ids.json"
RULES_OUT = "answers/generation_rules.json"

UNIT_VALUE, SHARE = types.SIGNALS
TRIGGERED, NOT_TRIGGERED = types.SIGNAL_TRIGGERS
MARGIN = Fraction(5, 100)  # 탐지 기준에서 떨어져야 하는 거리(MT1 결정 기록: 탐지 경계 ±0.05 안의 값을 피한다)
ROW = "ROW"  # 나머지 세계(수집하지 않은 나라들). 전체국가 분모에만 들어간다
RULES_KEYS = {"schema_version", "dataset", "snapshot_id", "policy_version", "fixed_time", "world", "cases"}
WORLD_KEYS = {"period", "hs4", "hs6", "partners", "noise", "series", "rest_of_world", "peer_k", "peer_source_year"}
CASE_KEYS = {"case_id", "hs6", "partner", "month", "scenario_class", "events", "rule", "expected", "note"}
REQUEST_STATUSES = ("FAILED", "NOT_COLLECTED")
PEER_METHOD = "import_value_topk"
PEER_GROUPING = "g0"
ID_RULE = ("ps_ + sha256(정규 JSON {\"children\": {HS10 뒤 4자리: [[V, Q] 월별]}, \"parent\": [[V, Q] 월별], "
           "\"period\": {\"start\", \"end\"}})의 16진수 소문자 앞 16자. 정규 JSON은 키 정렬, 구분자 ',' ':', "
           "ensure_ascii=False. 기본 계열은 사례 사건을 얹기 전의 대상 계열(부모 HS6와 HS10 하위품목의 월별 금액·중량)")
COLLECTOR_DDL = """
CREATE TABLE collection_receipt(
  request_id TEXT PRIMARY KEY, endpoint TEXT, params_json TEXT, status TEXT, http_status INTEGER,
  attempts INTEGER, response_hash TEXT, row_count INTEGER, result_code TEXT, result_msg TEXT,
  error TEXT, elapsed_ms INTEGER, raw_file_id TEXT, timestamp TEXT);
CREATE TABLE observation(
  snapshot_id TEXT, request_id TEXT, month TEXT, partner_code TEXT, partner_namespace TEXT,
  hs_code TEXT, hs_level INTEGER, hs_version TEXT, flow TEXT, amount_usd INTEGER, net_weight_kg INTEGER,
  observation_status TEXT, raw_file_id TEXT, raw_row_locator TEXT, item_name TEXT,
  PRIMARY KEY(request_id, month, partner_code, hs_code, flow));
CREATE TABLE snapshot_meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE collection_attempt(
  request_id TEXT, endpoint TEXT, params_json TEXT, outcome TEXT, http_status INTEGER, attempts INTEGER,
  result_code TEXT, error TEXT, attempt_errors TEXT, raw_file_id TEXT, response_hash TEXT, timestamp TEXT);
"""  # 수집기 ingest.open_snapshot의 표 정의와 같다(수집기는 스냅샷 폴더 위치가 고정이라 그 함수를 부르지 않는다)


# ----------------------------------------------------------------------------- 작은 도우미
def _round(value: Fraction) -> int:
    """0 이상의 수를 사사오입(ROUND_HALF_UP)으로 정수로 만든다."""
    if value < 0:
        raise ValueError("음수 금액·중량을 만들 수 없다")
    return int(value + Fraction(1, 2))


def _digest(*parts: object) -> int:
    return int(hashlib.sha256(":".join(str(p) for p in parts).encode("utf-8")).hexdigest(), 16)


def _pair(value: object, where: str) -> tuple[int, int]:
    if not (isinstance(value, list) and len(value) == 2 and all(isinstance(v, int) and not isinstance(v, bool)
                                                                   and v >= 0 for v in value)):
        raise ValueError(f"{where}: [금액 USD, 중량 kg] 두 정수(0 이상)여야 한다")
    if value == [0, 0]:
        raise ValueError(f"{where}: [0, 0]은 쓰지 않는다(없는 하위품목은 적지 않는다)")
    return value[0], value[1]


def _factor(text: object, where: str) -> Fraction:
    if not isinstance(text, str):
        raise ValueError(f"{where}: 배율은 소수 글자(예 \"0.75\")로 적는다(float를 쓰지 않는다)")
    value = Fraction(Decimal(text))
    if value <= 0:
        raise ValueError(f"{where}: 배율은 0보다 커야 한다")
    return value


def _shift(month: str, delta: int) -> str:
    index = int(month[:4]) * 12 + int(month[4:]) - 1 + delta
    return f"{index // 12}{index % 12 + 1:02d}"


def _dec(value: Fraction | None, places: int = 2) -> str | None:
    """요약에 적는 수(Decimal 글자, 사사오입)."""
    if value is None:
        return None
    return str((Decimal(value.numerator) / Decimal(value.denominator)).quantize(Decimal(1).scaleb(-places),
                                                                                  rounding=ROUND_HALF_UP))


def _json_text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=1) + "\n"


# ----------------------------------------------------------------------------- 생성 규칙 읽기
def _check_rules(rules: object) -> dict:
    if not isinstance(rules, dict) or set(rules) != RULES_KEYS:
        raise ValueError(f"생성 규칙의 최상위 키는 {sorted(RULES_KEYS)}다")
    if rules["schema_version"] != types.SCHEMA_VERSION or rules["dataset"] not in v4.SYNTHETIC_DATASETS:
        raise ValueError("생성 규칙의 schema_version은 1, dataset은 dev20·holdout40이다")
    if not isinstance(rules["snapshot_id"], str) or not v4.SNAPSHOT_ID_RE.fullmatch(rules["snapshot_id"]):
        raise ValueError("snapshot_id는 영문 소문자·숫자로 시작하고 영문 소문자·숫자·밑줄만 쓴다")
    if not s2.KST_ISO_RE.fullmatch(str(rules["fixed_time"])):
        raise ValueError("fixed_time은 KST ISO 8601(+09:00, 초 단위)이다")
    world = rules["world"]
    if not isinstance(world, dict) or set(world) != WORLD_KEYS:
        raise ValueError(f"world의 키는 {sorted(WORLD_KEYS)}다")
    hs4, hs6s, partners = world["hs4"], world["hs6"], world["partners"]
    if not (isinstance(hs4, str) and len(hs4) == 4 and hs4.isdigit()):
        raise ValueError("world.hs4는 숫자 4자리다")
    if not hs6s or any(not (isinstance(h, str) and types.HS6_RE.fullmatch(h) and h.startswith(hs4)) for h in hs6s):
        raise ValueError("world.hs6는 hs4로 시작하는 숫자 6자리 목록이다")
    if not partners or len(set(partners)) != len(partners) \
            or any(not (isinstance(p, str) and v4.PARTNER_RE.fullmatch(p)) or p == types.ALL_PARTNER for p in partners):
        raise ValueError("world.partners는 겹치지 않는 영문 대문자 2자 목록이다(ALL 제외)")
    if not isinstance(world["series"], dict) or not isinstance(world["rest_of_world"], dict):
        raise ValueError("world.series·rest_of_world는 HS6를 키로 하는 객체다")
    for h in hs6s:
        if not isinstance(world["series"].get(h), dict) or set(world["series"][h]) != set(partners) \
                or not isinstance(world["rest_of_world"].get(h), dict):
            raise ValueError(f"world.series·rest_of_world에 {h}의 모든 상대국 기본 값이 있어야 한다")
        for who, levels in list(world["series"][h].items()) + [(ROW, world["rest_of_world"][h])]:
            if not isinstance(levels, dict) or not levels:
                raise ValueError(f"기본 값 {h}·{who}: 하위품목이 없다")
            for suffix, level in levels.items():
                if not (isinstance(suffix, str) and len(suffix) == 4 and suffix.isdigit()):
                    raise ValueError(f"기본 값 {h}·{who}: 하위품목 키는 HS10 뒤 4자리 숫자다")
                _pair(level, f"기본 값 {h}·{who}·{suffix}")
    noise = world["noise"]
    if not (isinstance(noise, dict) and set(noise) == {"seed", "quantity_permille", "price_permille"}
            and all(isinstance(v, int) and not isinstance(v, bool) and v >= 0 for v in noise.values())):
        raise ValueError("world.noise는 seed·quantity_permille·price_permille 정수다")
    if not isinstance(rules["cases"], list) or not rules["cases"]:
        raise ValueError("cases가 비었다")
    return rules


def collection_plan(rules: dict) -> dict:
    """수집기 설정(`configs/collection_plan.json`과 같은 모양). manifest의 config이자 스냅샷 메타의 collection_plan."""
    world = rules["world"]
    return {"snapshot_id": rules["snapshot_id"], "period": dict(world["period"]), "chunk_months": 12,
            "hs4_scan": [world["hs4"]], "hs6": list(world["hs6"]), "partners": list(world["partners"]),
            "collect_total_denominator": True, "hs10": []}


# ----------------------------------------------------------------------------- 합성 세계
def _noisy(level: tuple[int, int], noise: dict, *key: str) -> tuple[int, int]:
    """기본 월 값에 결정적 흔들림(중량 ±quantity_permille‰, 단가 ±price_permille‰)을 얹는다."""
    value, weight = level
    qp, pp = noise["quantity_permille"], noise["price_permille"]
    qf = 1 + Fraction(_digest(noise["seed"], "q", *key) % (2 * qp + 1) - qp, 1000)
    pf = 1 + Fraction(_digest(noise["seed"], "p", *key) % (2 * pp + 1) - pp, 1000)
    if weight == 0:
        return _round(value * pf), 0
    q = _round(weight * qf)
    return _round(Fraction(value, weight) * pf * q), q


def base_children(rules: dict) -> dict:
    """(hs6, 상대국 또는 ROW, 달) → {HS10 뒤 4자리: (금액, 중량)}. 사건을 얹기 전의 값."""
    world = rules["world"]
    months = ingest.months_between(world["period"]["start"], world["period"]["end"])
    out = {}
    for h in world["hs6"]:
        owners = [(p, world["series"][h][p]) for p in world["partners"]] + [(ROW, world["rest_of_world"][h])]
        for who, levels in owners:
            for m in months:
                out[(h, who, m)] = {s: _noisy(tuple(levels[s]), world["noise"], h, who, s, m) for s in sorted(levels)}
    return out


EVENT_KEYS = {"exact": {"type", "month"}, "children": {"type", "month", "values"},
              "parent": {"type", "month", "value"}, "scale": {"type", "month", "who", "volume", "price"},
              "world": {"type", "month", "values"},
              "request": {"type", "endpoint", "hsSgn", "cntyCd", "strtYymm", "status"}}


def apply_events(rules: dict, children: dict) -> tuple[dict, dict, dict, dict]:
    """사례 사건을 얹는다. (하위 값, 부모 덮어쓰기, 분모 덮어쓰기, 요청 상태) 네 가지를 돌려준다.

    사건은 사례의 대상 계열(hs6·partner)이나 그 hs6에만 닿는다. 한 (hs6, 나라, 달)의 하위 값에는 사건이 하나뿐이고
    (exact·children·scale 가운데 하나), 부모 덮어쓰기·분모 덮어쓰기·요청 상태도 대상마다 하나다."""
    world = rules["world"]
    months = set(ingest.months_between(world["period"]["start"], world["period"]["end"]))
    children = {k: dict(v) for k, v in children.items()}
    parents, worlds, requests = {}, {}, {}
    overridden: dict[tuple, str] = {}

    def claim(table: dict, key: tuple, where: str) -> None:
        if key in table:
            raise ValueError(f"{where}: 같은 대상({'·'.join(key)})에 사건이 이미 있다")
        table[key] = where

    claimed_parent: dict[tuple, str] = {}
    claimed_world: dict[tuple, str] = {}
    for case in rules["cases"]:
        h, p = case["hs6"], case["partner"]
        if not isinstance(case["events"], list):
            raise ValueError(f"사례 {case['case_id']}: events는 목록이다")
        for index, event in enumerate(case["events"]):
            where = f"사례 {case['case_id']} 사건 {index}"
            kind = event.get("type") if isinstance(event, dict) else None
            if kind not in EVENT_KEYS or set(event) != EVENT_KEYS[kind]:
                raise ValueError(f"{where}: 사건 종류와 키가 맞지 않다({sorted(EVENT_KEYS)})")
            if kind == "request":
                if event["status"] not in REQUEST_STATUSES:
                    raise ValueError(f"{where}: request 사건 status는 {REQUEST_STATUSES} 중 하나다")
                key = (event["endpoint"], event["hsSgn"], event["cntyCd"], event["strtYymm"])
                if key in requests:
                    raise ValueError(f"{where}: 같은 요청에 사건이 둘이다")
                requests[key] = event["status"]
                continue
            month = event["month"]
            if month not in months:
                raise ValueError(f"{where}: month가 기간 밖이다")
            if kind == "scale":
                volume, price = _factor(event["volume"], where), _factor(event["price"], where)
                for who in event["who"]:
                    if who != ROW and (who not in world["partners"] or who == p):
                        raise ValueError(f"{where}: scale 대상은 대상국이 아닌 상대국이나 ROW다")
                    claim(overridden, (h, who, month), where)
                    children[(h, who, month)] = {s: (_round(v * volume * price), _round(q * volume))
                                                 for s, (v, q) in children[(h, who, month)].items()}
            elif kind == "world":
                claim(claimed_world, (h, month), where)
                worlds[(h, month)] = {s: _pair(v, where) for s, v in sorted(event["values"].items())}
            elif kind == "parent":
                claim(claimed_parent, (h, p, month), where)
                parents[(h, p, month)] = _pair(event["value"], where)
            else:  # exact·children: 대상 계열의 그 달 하위 값을 정확히 정한다(흔들림 없음)
                claim(overridden, (h, p, month), where)
                levels = world["series"][h][p] if kind == "exact" else event["values"]
                children[(h, p, month)] = {s: _pair(v, where) for s, v in sorted(levels.items())}
    return children, parents, worlds, requests


def world_tables(rules: dict) -> tuple[dict, dict, dict, dict]:
    """(상대국 하위 값, 부모 HS6 값, 전체국가 HS10 값, 요청 상태)."""
    world = rules["world"]
    months = ingest.months_between(world["period"]["start"], world["period"]["end"])
    children, parent_over, world_over, requests = apply_events(rules, base_children(rules))
    parents, totals = {}, {}
    for h in world["hs6"]:
        for m in months:
            for p in world["partners"]:
                kids = children[(h, p, m)]
                parents[(h, p, m)] = parent_over.get((h, p, m)) or (sum(v for v, _ in kids.values()),
                                                                      sum(q for _, q in kids.values()))
            if (h, m) in world_over:
                totals[(h, m)] = world_over[(h, m)]
                continue
            codes: dict[str, list[int]] = {}
            for who in list(world["partners"]) + [ROW]:
                for s, (v, q) in children[(h, who, m)].items():
                    acc = codes.setdefault(s, [0, 0])
                    acc[0] += v
                    acc[1] += q
            totals[(h, m)] = {s: tuple(codes[s]) for s in sorted(codes)}
    return children, parents, totals, requests


# ----------------------------------------------------------------------------- 수집기 형식 원천
def _item(fields: list[tuple[str, object]]) -> str:
    return "<item>" + "".join(f"<{k}>{escape(str(v))}</{k}>" for k, v in fields) + "</item>"


def _xml(lines: list[str]) -> str:
    head = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<response><header><resultCode>00</resultCode>'
            "<resultMsg>정상서비스.</resultMsg></header><body><items>")
    return "\n".join([head] + lines + ["</items></body></response>"]) + "\n"


def _rows_xml(endpoint: str, partner: str | None, rows: list[tuple[str, str, int, int]]) -> str:
    """응답 행 [(달, HS 코드, 수입금액, 수입중량)] → 관세청 정상 봉투 XML. 첫 줄은 총계 행(실측 응답 모양)."""
    code_key = ingest.ENDPOINTS[endpoint]["hs_field"]

    def fields(year: str, code: str, name: str, value: int, weight: int, total: bool = False) -> list:
        out = [("year", year)]
        if partner is not None:
            out.append(("statCd", "-" if total else partner))
        return out + [("statKor", name), (code_key, code), ("impDlr", value), ("impWgt", weight),
                      ("expDlr", 0), ("expWgt", 0)]

    lines = []
    if rows:
        lines.append(_item(fields("총계", "-", "-", sum(r[2] for r in rows), sum(r[3] for r in rows), total=True)))
    for month, code, value, weight in rows:
        name = f"합성 품목 {code}" if len(code) == 6 else f"합성 하위품목 {code}"
        lines.append(_item(fields(f"{month[:4]}.{month[4:]}", code, name, value, weight)))
    return _xml(lines)


def source_files(rules: dict) -> tuple[dict, dict, list]:
    """수집기 형식 원천 텍스트 {파일 이름: 글자}, 요청별 상태 {request_id: OK|FAILED|NOT_COLLECTED}, manifest 요청 목록."""
    world = rules["world"]
    config = collection_plan(rules)
    requests = ingest.build_manifest(config)
    children, parents, totals, events = world_tables(rules)
    files, status = {}, {}
    for request in requests:
        params, endpoint, rid = request["params"], request["endpoint"], request["request_id"]
        partner, code = params.get("cntyCd"), params["hsSgn"]
        key = (endpoint, code, partner or types.ALL_PARTNER, params["strtYymm"])
        status[rid] = {"FAILED": "FAILED", "NOT_COLLECTED": "NOT_COLLECTED"}.get(events.pop(key, None), "OK")
        rows = []
        for m in request["months"]:
            if request["purpose"] == "hs4_partner_monthly":
                rows += [(m, h, *parents[(h, partner, m)]) for h in world["hs6"] if h.startswith(code)
                         and parents[(h, partner, m)] != (0, 0)]
            elif request["purpose"] == "hs6_partner_monthly":
                rows += [(m, code + s, v, q) for s, (v, q) in sorted(children[(code, partner, m)].items())]
            else:  # 품목별 전체국가 합계(HS4·HS6 요청 모두 HS10 행을 준다)
                rows += [(m, h + s, v, q) for h in world["hs6"] if h.startswith(code)
                         for s, (v, q) in sorted(totals[(h, m)].items())]
        if status[rid] == "OK":
            files[f"raw/{rid}.xml"] = _rows_xml(endpoint, partner, rows)
    if events:
        raise ValueError(f"request 사건이 수집 계획에 없는 요청을 가리킨다({len(events)}건)")
    names = sorted(name for name in files if name.startswith("raw/"))
    lines = "".join(f"{hashlib.sha256(files[n].encode('utf-8')).hexdigest()}  {n}\n" for n in names)
    raw_sha256 = hashlib.sha256(lines.encode("utf-8")).hexdigest()
    files[MANIFEST_FILE] = _json_text({"snapshot_id": rules["snapshot_id"], "generated_at": rules["fixed_time"],
                                       "config": config, "requests": requests})
    files[LOG_FILE] = _json_text({
        "schema_version": types.SCHEMA_VERSION, "snapshot_id": rules["snapshot_id"], "collected_at": rules["fixed_time"],
        "_rule": "manifest 요청 가운데 raw/<request_id>.xml이 있는 요청은 OK(HTTP 200, 시도 1회)다. FAILED는 HTTP 500으로 "
                 "세 번 실패한 요청(응답 본문 없음), NOT_COLLECTED는 수신 기록이 없는 요청이다",
        "FAILED": sorted(r for r, s in status.items() if s == "FAILED"),
        "NOT_COLLECTED": sorted(r for r, s in status.items() if s == "NOT_COLLECTED")})
    files[HASH_FILE] = _json_text({"snapshot_id": rules["snapshot_id"], "raw_files": len(names),
                                   "raw_combined_sha256": raw_sha256,
                                   "method": "스냅샷 원천 폴더에서 `shasum -a 256 raw/*.xml | shasum -a 256`"})
    return files, status, requests


# ----------------------------------------------------------------------------- 응답을 다시 읽어 만든 자료(검산용)
class View:
    """응답 XML과 요청 상태만으로 다시 읽은 자료(자료 계약 §2.3.2 행 규칙 4~6). 생성에 쓴 표를 보지 않는다."""

    def __init__(self, rules: dict, files: dict, status: dict, requests: list) -> None:
        world = rules["world"]
        self.hs6, self.partners = list(world["hs6"]), list(world["partners"])
        self.months = ingest.months_between(world["period"]["start"], world["period"]["end"])
        self.parent: dict[tuple, tuple[int, int]] = {}
        self.children: dict[tuple, dict] = {}
        self.child_missing: dict[tuple, str] = {}
        self.world: dict[tuple, dict] = {}
        world_rank: dict[tuple, int] = {}
        for request in requests:
            rid, params, purpose = request["request_id"], request["params"], request["purpose"]
            partner, code = params.get("cntyCd", types.ALL_PARTNER), params["hsSgn"]
            items = [] if status[rid] != "OK" else ingest.parse_response(files[f"raw/{rid}.xml"].encode("utf-8"))["items"]
            seen = set()
            for item in items:
                month = item["year"].replace(".", "")
                if not types.MONTH_RE.fullmatch(month):
                    continue  # 총계 행
                seen.add(month)
                hs = item[ingest.ENDPOINTS[request["endpoint"]]["hs_field"]]
                pair = (int(item["impDlr"]), int(item["impWgt"]))
                if purpose == "hs4_partner_monthly":
                    self.parent[(hs, partner, month)] = pair
                elif purpose == "hs6_partner_monthly":
                    self.children.setdefault((code, partner, month), {})[hs] = pair
                else:
                    key = (hs[:6], month)
                    rank = len(code)  # 행 규칙 6: 요청 코드가 긴 요청의 행
                    held = self.world.setdefault(key, {})
                    if hs in held and held[hs] != pair:
                        raise ValueError(f"ALL {hs}·{month}: 두 요청의 값이 다르다(행 규칙 6)")
                    if world_rank.get((hs, month), -1) <= rank:
                        held[hs] = pair
                        world_rank[(hs, month)] = rank
            if purpose == "hs6_partner_monthly":
                for month in request["months"]:
                    if status[rid] != "OK":
                        self.child_missing[(code, partner, month)] = \
                            types.REQUEST_FAILED if status[rid] == "FAILED" else types.NOT_COLLECTED
                    elif month not in seen:
                        self.child_missing[(code, partner, month)] = types.UNRESOLVED_ZERO

    def unit_value(self, h: str, p: str, m: str) -> Fraction | None:
        pair = self.parent.get((h, p, m))
        return None if pair is None or pair[1] == 0 else Fraction(pair[0], pair[1])

    def world_value(self, h: str, m: str) -> int | None:
        rows = self.world.get((h, m))
        return None if not rows else sum(v for v, _ in rows.values())

    def share(self, h: str, p: str, m: str) -> Fraction | None:
        pair, total = self.parent.get((h, p, m)), self.world_value(h, m)
        return None if pair is None or not total else Fraction(pair[0], total)

    def r_u(self, h: str, p: str, t: str) -> Fraction | None:
        """단가 전년동월 변화율(%). 기준월 값이 없거나 0이면 None."""
        u0, u1 = self.unit_value(h, p, _shift(t, -12)), self.unit_value(h, p, t)
        return None if u0 is None or u1 is None or u0 == 0 else (u1 / u0 - 1) * 100

    def d_s(self, h: str, p: str, t: str) -> Fraction | None:
        """점유율 변화(pp)."""
        s0, s1 = self.share(h, p, _shift(t, -12)), self.share(h, p, t)
        return None if s0 is None or s1 is None else (s1 - s0) * 100

    def decompose(self, h: str, p: str, t: str, weight_tol: Fraction) -> dict:
        """HS10 구성효과 분해(자료 계약 §11.2). 쓸 수 없으면 {"ok": False, "reason"}."""
        b = _shift(t, -12)
        for m in (b, t):
            if (h, p, m) in self.child_missing:
                return {"ok": False, "reason": "child_missing"}
        kids0, kids1 = self.children.get((h, p, b), {}), self.children.get((h, p, t), {})
        if set(kids0) != set(kids1) or not kids0:
            return {"ok": False, "reason": "code_set_changed"}
        for m, kids in ((b, kids0), (t, kids1)):
            parent = self.parent[(h, p, m)]
            if sum(v for v, _ in kids.values()) != parent[0]:
                return {"ok": False, "reason": "parent_amount_mismatch"}
            if abs(sum(q for _, q in kids.values()) - parent[1]) > weight_tol * (len(kids) + 1):
                return {"ok": False, "reason": "parent_weight_mismatch"}
            if any(q == 0 for _, q in kids.values()):
                return {"ok": False, "reason": "zero_weight_child"}
        q0, q1 = sum(q for _, q in kids0.values()), sum(q for _, q in kids1.values())
        u0 = {c: Fraction(v, q) for c, (v, q) in kids0.items()}
        u1 = {c: Fraction(v, q) for c, (v, q) in kids1.items()}
        w0 = {c: Fraction(q, q0) for c, (_, q) in kids0.items()}
        w1 = {c: Fraction(q, q1) for c, (_, q) in kids1.items()}
        within = sum(((w0[c] + w1[c]) / 2) * (u1[c] - u0[c]) for c in u0)
        mix = sum(((u0[c] + u1[c]) / 2) * (w1[c] - w0[c]) for c in u0)
        delta = self.unit_value(h, p, t) - self.unit_value(h, p, b)
        return {"ok": True, "within": within, "mix": mix, "residual": delta - within - mix,
                "u0": self.unit_value(h, p, b), "child_r": {c: u1[c] / u0[c] - 1 for c in u0}}


# ----------------------------------------------------------------------------- 비교국 표(합성 g0)
def peer_rows(rules: dict, view: View, raw_sha256: str) -> list[dict]:
    """합성 자료 안에서 g0 규칙(대상국을 뺀 상대국 가운데 기준연도 부모 HS6 수입금액 상위 k개국, 같으면 코드순)."""
    world = rules["world"]
    year, k = str(world["peer_source_year"]), world["peer_k"]
    params = {"candidates": sorted(view.partners), "k": k, "method": PEER_METHOD, "source_year": year}
    params_hash = hashlib.sha256(json.dumps(params, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    rows = []
    for h in view.hs6:
        for p in view.partners:
            sums = {q: sum(view.parent.get((h, q, m), (0, 0))[0] for m in view.months if m.startswith(year))
                    for q in view.partners if q != p}
            ranked = sorted(sums, key=lambda q: (-sums[q], q))[:k]
            for rank, q in enumerate(ranked, start=1):
                rows.append({"entity_type": types.PEER_ENTITY_TYPE, "entity_id": p,
                             "entity_namespace": types.PARTNER_NAMESPACE, "baci_country_code": None,
                             "scope_type": "hs6", "scope_id": h, "peer_rank": rank, "peer_id": q, "similarity": None,
                             "community_id": None, "method": PEER_METHOD, "grouping_version": PEER_GROUPING,
                             "params_hash": params_hash, "source_version": rules["snapshot_id"],
                             "source_year": int(year), "input_sha256": raw_sha256,
                             "generated_at": rules["fixed_time"]})
    return rows


def peer_csv(rows: list[dict]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(types.PEER_GROUP_KEYS)
    for row in rows:
        writer.writerow(["" if row[k] is None else row[k] for k in types.PEER_GROUP_KEYS])
    return buffer.getvalue()


def peer_file_name(rules: dict) -> str:
    return f"peer_group_{rules['dataset']}_{PEER_GROUPING}.csv"


# ----------------------------------------------------------------------------- 자체 검산
def self_check(rules: dict, view: View, peers: list[dict], policy: dict) -> dict:
    """발동 집합·기대 발동·기준 거리·판정 근거 규칙별 자료 불변식을 본다. 어긋나면 ValueError."""
    theta_u, theta_s = Fraction(policy["thresholds"]["unit_value"]), Fraction(policy["thresholds"]["share"])
    weight_tol = Fraction(str(policy["tolerance"]["weight_rounding_kg"]))
    cases = {(c["hs6"], c["partner"], c["month"]): c for c in rules["cases"]}
    problems: list[str] = []
    triggered: dict[tuple, dict] = {}
    nearest = {UNIT_VALUE: None, SHARE: None}
    for h in view.hs6:
        for p in view.partners:
            for t in view.months:
                if _shift(t, -12) not in view.months:
                    continue
                for family, value, theta in ((UNIT_VALUE, view.r_u(h, p, t), theta_u),
                                             (SHARE, view.d_s(h, p, t), theta_s)):
                    if value is None:
                        continue
                    gap = abs(abs(value) - theta)
                    if gap < MARGIN:
                        problems.append(f"{h}-{p}-{t} {family}: 탐지 기준에서 {_dec(gap)}만 떨어졌다")
                    nearest[family] = gap if nearest[family] is None else min(nearest[family], gap)
                    if abs(value) >= theta:
                        triggered.setdefault((h, p, t), {})[family] = value
    extra = sorted(set(triggered) - set(cases))
    problems += [f"사례 밖 경보: {'-'.join(k)}" for k in extra]
    peer_of = {}
    for row in peers:
        peer_of.setdefault((row["scope_id"], row["entity_id"]), []).append(row["peer_id"])
    for key, case in cases.items():
        h, p, t = key
        b = _shift(t, -12)
        got = {f: (TRIGGERED if f in triggered.get(key, {}) else NOT_TRIGGERED) for f in types.SIGNALS}
        if got != case["expected"]["signals"]:
            problems.append(f"{case['case_id']}: 자료에서 다시 계산한 발동 여부가 기대 signals와 다르다({got})")
            continue
        rule = case["rule"]
        u_rule, s_rule = rule[UNIT_VALUE], rule[SHARE]
        peers_ok = all(view.parent.get((h, q, m)) for q in peer_of.get((h, p), []) for m in (b, t))
        if u_rule is not None:
            dec = view.decompose(h, p, t, weight_tol)
            if u_rule == "composition_explained" and not (dec["ok"] and dec["within"] == 0 and dec["residual"] == 0
                                                          and all(r == 0 for r in dec["child_r"].values())):
                problems.append(f"{case['case_id']}: 구성효과 사례인데 하위 단가 변화·within·잔차가 0이 아니다")
            if u_rule == "unexplained" and not (dec["ok"] and abs(dec["within"] + dec["residual"]) * 100
                                                >= (theta_u + MARGIN) * dec["u0"] and peers_ok):
                problems.append(f"{case['case_id']}: 설명 안 됨 사례인데 within+잔차가 기준 미만이거나 비교국 자료가 없다")
            if u_rule == "hold_missing" and not any(view.child_missing.get((h, p, m)) in
                                                    (types.REQUEST_FAILED, types.NOT_COLLECTED) for m in (b, t)):
                problems.append(f"{case['case_id']}: 관측 누락 보류 사례인데 대상국 HS10 요청 실패·미수집이 없다")
            if u_rule == "hold_inconsistent" and not (not dec["ok"] and dec["reason"] in
                                                      ("code_set_changed", "parent_amount_mismatch",
                                                       "parent_weight_mismatch", "zero_weight_child")):
                problems.append(f"{case['case_id']}: 불일치 보류 사례인데 부모·하위 대조나 분해가 성립한다")
            if u_rule == "rounding_unstable" and not _rounding_unstable(view, h, p, t, theta_u, weight_tol):
                problems.append(f"{case['case_id']}: 반올림 불안정 사례인데 중량 반올림 범위가 0과 ±기준을 모두 넘지 않는다")
        if s_rule is not None:
            totals = [view.world_value(h, m) for m in (b, t)]
            covered = [sum(view.parent.get((h, q, m), (0, 0))[0] for q in view.partners) for m in (b, t)]
            complete = all(w is not None and w >= c for w, c in zip(totals, covered))
            if s_rule == "unexplained" and not (complete and peers_ok):
                problems.append(f"{case['case_id']}: 점유율 설명 안 됨 사례인데 분모가 상대국 합보다 작거나 비교국 자료가 없다")
            if s_rule == "hold_inconsistent" and not any(
                    w is not None and w < view.parent[(h, p, m)][0] for w, m in zip(totals, (b, t))):
                problems.append(f"{case['case_id']}: 분모 불완전 보류 사례인데 분모가 대상국 금액보다 작은 달이 없다")
        if case["scenario_class"] == 3:
            target = view.r_u(h, p, t)
            moves = [view.r_u(h, q, t) for q in peer_of.get((h, p), [])]
            if not moves or any(r is None or r * target <= 0 or abs(r) * 2 < theta_u for r in moves):
                problems.append(f"{case['case_id']}: 비교국 동반 변화(같은 방향, 기준의 절반 이상)가 아니다")
        if case["scenario_class"] == 9:
            sums = [tuple(sum(view.parent.get((g, p, m), (0, 0))[i] for g in view.hs6) for i in (0, 1)) for m in (b, t)]
            ratio = Fraction(sums[1][0], sums[1][1]) / Fraction(sums[0][0], sums[0][1]) - 1
            if abs(ratio) * 100 * 2 >= theta_u:
                problems.append(f"{case['case_id']}: HS4 합계 단가 변화가 기준의 절반 이상이라 범위 함정이 아니다")
    if problems:
        raise ValueError("dev20 자체 검산 실패: " + " / ".join(problems[:10]) + (f" 외 {len(problems) - 10}건"
                                                                          if len(problems) > 10 else ""))
    return {"cases": len(cases), "triggered_series_months": len(triggered), "extra_triggers": len(extra),
            "nearest_to_threshold": {UNIT_VALUE: _dec(nearest[UNIT_VALUE]), SHARE: _dec(nearest[SHARE])}}


def _rounding_unstable(view: View, h: str, p: str, t: str, theta: Fraction, tol: Fraction) -> bool:
    """부모 HS6 중량을 ±tol 안에서 움직였을 때 단가 변화율 범위가 0과 +θ·−θ를 모두 가로지르는가(MT1 결정 기록 ⑤ 제안)."""
    (v0, q0), (v1, q1) = view.parent[(h, p, _shift(t, -12))], view.parent[(h, p, t)]
    if q0 - tol <= 0 or q1 - tol <= 0:
        return True
    low = (Fraction(v1) / (q1 + tol)) / (Fraction(v0) / (q0 - tol)) - 1
    high = (Fraction(v1) / (q1 - tol)) / (Fraction(v0) / (q0 + tol)) - 1
    bound = theta / 100
    return low < 0 < high and low < bound < high and low < -bound < high


# ----------------------------------------------------------------------------- 부모 원본 계열 ID
def parent_series_id(rules: dict, base: dict, h: str, p: str) -> str:
    """사례 사건을 얹기 전의 대상 계열(부모 HS6와 HS10 하위품목의 월별 금액·중량)의 지문(명세 §6)."""
    world = rules["world"]
    months = ingest.months_between(world["period"]["start"], world["period"]["end"])
    suffixes = sorted(world["series"][h][p])
    doc = {"children": {s: [list(base[(h, p, m)][s]) for m in months] for s in suffixes},
           "parent": [[sum(base[(h, p, m)][s][i] for s in suffixes) for i in (0, 1)] for m in months],
           "period": {"start": world["period"]["start"], "end": world["period"]["end"]}}
    text = json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "ps_" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# ----------------------------------------------------------------------------- 수집기 SQLite 재현과 빌드
def materialize_collector(source_dir: Path, target_dir: Path) -> Path:
    """커밋된 원천(manifest·raw·collection_log·snapshot_hash)으로 수집기 형식 스냅샷 폴더를 target_dir에 새로 만든다.

    응답마다 수집기 store_result를 불러 수집기 SQLite(`snapshot.sqlite`)와 raw 파일을 쓰고, 시각은 기록의 고정 시각으로
    바꾼다. target_dir는 없어야 한다."""
    source_dir, target_dir = Path(source_dir), Path(target_dir)
    manifest = json.loads((source_dir / MANIFEST_FILE).read_text(encoding="utf-8"))
    log = json.loads((source_dir / LOG_FILE).read_text(encoding="utf-8"))
    snapshot_id, fixed = manifest["snapshot_id"], log["collected_at"]
    failed, not_collected = set(log["FAILED"]), set(log["NOT_COLLECTED"])
    target_dir.mkdir(parents=False, exist_ok=False)
    (target_dir / "raw").mkdir()
    for name in (MANIFEST_FILE, HASH_FILE):
        (target_dir / name).write_bytes((source_dir / name).read_bytes())
    ok_files = set()
    con = sqlite3.connect(target_dir / "snapshot.sqlite")
    try:
        con.executescript(COLLECTOR_DDL)
        for request in manifest["requests"]:
            rid = request["request_id"]
            if rid in not_collected:
                continue
            if rid in failed:
                result = {"ok": False, "http_status": 500, "attempts": 3, "raw": b"", "error": "HTTPError 500",
                          "attempt_errors": ["HTTPError 500"] * 3, "elapsed_ms": 0}
            else:
                ok_files.add(f"{rid}.xml")
                result = {"ok": True, "http_status": 200, "attempts": 1, "error": None, "attempt_errors": [],
                          "raw": (source_dir / "raw" / f"{rid}.xml").read_bytes(), "elapsed_ms": 0}
            ingest.store_result(target_dir, con, snapshot_id, request["endpoint"], request["params"], result,
                                request["months"])
        con.execute("UPDATE collection_receipt SET timestamp = ?", (fixed,))
        con.execute("UPDATE collection_attempt SET timestamp = ?", (fixed,))
        config = manifest["config"]
        meta = {"snapshot_id": snapshot_id, "source_kind": "controlled", "created_at": fixed, "last_collect_at": fixed,
                "importer": "KR", "units": json.dumps(ingest.UNITS, ensure_ascii=False),
                "valuation_basis": json.dumps(ingest.VALUATION, ensure_ascii=False),
                "units_confirmed": "합성 자료(controlled): 금액은 USD 정수, 중량은 kg 정수로 만들었다",
                "precision_rule": "amount exact integer USD; weight integer kg per row (합성 자료)",
                "hs_version": s2.COLLECTOR_HS_VERSION, "coverage_status": "IN_PROGRESS",
                "period_start": config["period"]["start"], "period_end": config["period"]["end"],
                "source_url": json.dumps(["eval/datagen/dev20.py", "eval/scenarios/SCENARIO_SPEC.md"])}
        con.executemany("INSERT INTO snapshot_meta(key, value) VALUES(?, ?)", sorted(meta.items()))
        con.commit()
    finally:
        con.close()
    present = {p.name for p in (source_dir / "raw").glob("*.xml")}
    if present != ok_files:
        raise ValueError(f"원천 raw 파일({len(present)})이 OK 요청({len(ok_files)})과 다르다")
    return target_dir


def build_and_verify(collector_dir: Path, peer_file: Path, snapshot_id: str, policy: dict, db_path: Path) -> dict:
    """단위 S2로 db_path에 빌드하고 단위 S3로 검증한다. 검증이 실패하면 ValueError."""
    record = s2.build_to(db_path, snapshot_id, source_dir=collector_dir, policy=policy, peer_group_files=[peer_file])
    report = s3.verify_snapshot(snapshot_id, build_file=db_path, source_dir=collector_dir, peer_group_files=[peer_file])
    if not report["ok"]:
        failed = [c["name"] for c in report["checks"] if c["ok"] is False]
        raise ValueError(f"단위 S3 검증 실패: {failed}")
    return {"normalized_sha256": record["normalized_sha256"], "row_counts": record["row_counts"],
            "verify_ok": True, "import_observation_status": report["counts"].get("import_observation_status")}


# ----------------------------------------------------------------------------- 진입 함수
def run(inp: object) -> object:
    """진입 함수. 입력: 생성 규칙(JSON 객체). 출력: {"files": {묶음 기준 상대경로: 텍스트}, "summary": {...}}."""
    rules = _check_rules(inp)
    policy = load_policy(rules["policy_version"])
    world = rules["world"]
    for case in rules["cases"]:
        if not isinstance(case, dict) or set(case) != CASE_KEYS:
            raise ValueError(f"사례 키는 {sorted(CASE_KEYS)}다")
        if case["hs6"] not in world["hs6"] or case["partner"] not in world["partners"] \
                or case["case_id"] != f"{case['hs6']}-{case['partner']}-{case['month']}":
            raise ValueError(f"사례 {case['case_id']}: case_id는 {{hs6}}-{{partner}}-{{month}}이고 세계 안의 계열이다")
    source, status, requests = source_files(rules)
    view = View(rules, source, status, requests)
    raw_sha256 = json.loads(source[HASH_FILE])["raw_combined_sha256"]
    peers = peer_rows(rules, view, raw_sha256)
    peer_name = peer_file_name(rules)
    source[peer_name] = peer_csv(peers)
    checked = self_check(rules, view, peers, policy)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "source"
        (src / "raw").mkdir(parents=True)
        for name, text in source.items():
            (src / name).write_text(text, encoding="utf-8")
        collector = materialize_collector(src, Path(tmp) / rules["snapshot_id"])
        built = build_and_verify(collector, src / peer_name, rules["snapshot_id"], policy, Path(tmp) / "build.sqlite")
    base = base_children(rules)
    ordered = sorted(rules["cases"], key=lambda c: c["case_id"])  # 순서가 분류를 드러내지 않게 식별자 순으로 적는다
    cases_doc = {"schema_version": types.SCHEMA_VERSION, "dataset": rules["dataset"],
                 "snapshot_id": rules["snapshot_id"], "policy_version": rules["policy_version"],
                 "snapshot_normalized_sha256": built["normalized_sha256"],
                 "cases": [{k: c[k] for k in v4.CASE_ITEM_KEYS} for c in ordered]}
    answers_doc = {"schema_version": types.SCHEMA_VERSION, "dataset": rules["dataset"],
                   "snapshot_id": rules["snapshot_id"], "policy_version": rules["policy_version"],
                   "thresholds": {"unit_value": policy["thresholds"]["unit_value"],
                                  "share": policy["thresholds"]["share"]},
                   "cases": [{"case_id": c["case_id"], "scenario_class": c["scenario_class"],
                              "parent_series_id": parent_series_id(rules, base, c["hs6"], c["partner"]),
                              "rule": c["rule"], "expected": c["expected"], "note": c["note"]}
                             for c in ordered]}
    report = v4.check_documents(cases_doc, answers_doc, None)  # 분류별 건수는 묶음 대조 시험이 본다(작은 규칙도 받게)
    failed = [c for c in report["checks"] if c["name"] in ("cases_schema", "answers_schema", "case_ids_match")
              and c["ok"] is False]
    if failed:
        raise ValueError(f"사례 목록·정답표가 단위 V4 검사를 통과하지 못했다: {failed}")
    ids = sorted({c["parent_series_id"] for c in answers_doc["cases"]})
    files = {f"{SOURCE}/{name}": text for name, text in sorted(source.items())}
    files[CASES_FILE] = _json_text(cases_doc)
    files[ANSWERS_FILE] = _json_text(answers_doc)
    files[IDS_FILE] = _json_text({"schema_version": types.SCHEMA_VERSION, "dataset": rules["dataset"],
                                  "id_rule": ID_RULE, "parent_series_ids": ids})
    files[RULES_OUT] = _json_text(rules)
    by_status: dict[str, int] = {}
    for value in status.values():
        by_status[value] = by_status.get(value, 0) + 1
    summary = {"snapshot_id": rules["snapshot_id"], "dataset": rules["dataset"],
               "policy_version": rules["policy_version"], "cases": len(rules["cases"]),
               "requests": dict(sorted(by_status.items())), "raw_combined_sha256": raw_sha256,
               "normalized_sha256": built["normalized_sha256"], "row_counts": built["row_counts"],
               "import_observation_status": built["import_observation_status"], "snapshot_verify_ok": True,
               "self_check": checked, "parent_series_ids": len(ids), "files": len(files)}
    return {"files": dict(sorted(files.items())), "summary": summary}


# ----------------------------------------------------------------------------- 명령
def _stamp() -> str:
    return datetime.now(types.KST).strftime("%y%m%d%H%M%S")


def acquire_run_dir(parent: Path) -> tuple[Path, str]:
    """실행명 확보(자료 계약 §10.3 N8): 그 초가 될 때까지 기다리고, 이미 있으면 실패하는 폴더 만들기 하나로 만든다.
    다른 부모 폴더(outputs/sealed/)에 같은 이름이 있으면 방금 만든 빈 폴더를 지우고 다음 초로 넘어간다."""
    parent.mkdir(exist_ok=True)
    for _ in range(10):
        stamp = _stamp()  # 지금 초의 이름이라 시각이 실제 시작보다 앞서지 않는다
        run_dir = parent / f"{DOMAIN}-{stamp}"
        try:
            os.mkdir(run_dir)
        except FileExistsError:
            run_dir = None
        if run_dir is not None and (parent / "sealed" / run_dir.name).exists():
            os.rmdir(run_dir)
            run_dir = None
        if run_dir is not None:
            return run_dir, stamp
        while _stamp() == stamp:  # 다음 초로 넘어간다
            time.sleep(0.05)
    raise RuntimeError("실행명을 확보하지 못했다")


def _rel(path: Path) -> str:
    try:
        return str(Path(path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return Path(path).name


def write_files(files: dict, root: Path) -> None:
    """묶음 텍스트 파일을 root 아래에 쓴다. 이미 있는 파일은 덮지 않는다(N8·N12)."""
    for name, text in files.items():
        path = Path(root) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "x", encoding="utf-8", newline="") as fh:
            fh.write(text)


def compare_committed(files: dict, root: Path) -> list[str]:
    """다시 만든 파일과 커밋된 파일을 바이트로 대조한다. 다른 파일·없는 파일·남는 파일 목록(상대경로)."""
    root = Path(root)
    wrong = [name for name, text in files.items()
             if not (root / name).is_file() or (root / name).read_bytes() != text.encode("utf-8")]
    present = {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file() and p.name != ".gitkeep"}
    return sorted(set(wrong) | (present - set(files)))


def _load_rules(path: str) -> dict:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def cmd_generate(args: argparse.Namespace) -> int:
    result = run(_load_rules(args.rules))
    run_dir, stamp = acquire_run_dir(REPO_ROOT / "outputs")
    write_files(result["files"], run_dir / f"{DOMAIN}-{stamp}")
    with open(run_dir / f"{DOMAIN}-{stamp}.json", "x", encoding="utf-8") as fh:
        fh.write(_json_text(result["summary"]))
    print(_rel(run_dir))
    if args.place:
        write_files(result["files"], REPO_ROOT / DEV20_DIR)
        print(f"{DEV20_DIR}로 옮겼다({len(result['files'])}개 파일)")
    print(_json_text(result["summary"]), end="")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    result = run(_load_rules(RULES_FILE))
    wrong = compare_committed(result["files"], REPO_ROOT / DEV20_DIR)
    print(json.dumps({"ok": not wrong, "files": len(result["files"]), "different": wrong}, ensure_ascii=False))
    return 0 if not wrong else 1


def cmd_install(args: argparse.Namespace) -> int:
    cases = json.loads((REPO_ROOT / DEV20_DIR / CASES_FILE).read_text(encoding="utf-8"))
    snapshot_id, expected = cases["snapshot_id"], cases["snapshot_normalized_sha256"]
    policy = load_policy(cases["policy_version"])
    source = REPO_ROOT / DEV20_DIR / SOURCE
    peer = source / f"peer_group_{cases['dataset']}_{PEER_GROUPING}.csv"
    target = REPO_ROOT / INSTALL_DIR / snapshot_id
    installed = target / s2.BUILD_FILE
    if installed.exists():
        same = s2.file_normalized_sha256(installed) == expected
        print(json.dumps({"installed": _rel(installed), "already_installed": True, "normalized_sha256_matches": same},
                         ensure_ascii=False))
        return 0 if same else 1
    run_dir, stamp = acquire_run_dir(REPO_ROOT / "outputs")
    collector = materialize_collector(source, run_dir / f"{DOMAIN}-{stamp}")
    record = s2.build_snapshot(snapshot_id, out_dir=run_dir, stamp=stamp, source_dir=collector, policy=policy,
                               peer_group_files=[peer])
    build_file = run_dir / f"{s2.DOMAIN}-{stamp}.sqlite"
    report = s3.verify_snapshot(snapshot_id, build_file=build_file, source_dir=collector, peer_group_files=[peer])
    if not report["ok"] or record["normalized_sha256"] != expected:
        print(json.dumps({"ok": False, "snapshot_verify_ok": report["ok"],
                          "normalized_sha256_matches": record["normalized_sha256"] == expected}, ensure_ascii=False))
        return 1
    target.mkdir(parents=True, exist_ok=True)
    s2.install_build(build_file, target)
    print(json.dumps({"ok": True, "run_dir": _rel(run_dir), "installed": _rel(installed),
                      "normalized_sha256": expected, "snapshot_verify_ok": True}, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m eval.datagen.dev20", allow_abbrev=False,
                                     description="dev20 합성 개발 자료 생성·대조·설치(개발 전용, 네트워크·키 없음)")
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate", allow_abbrev=False, help="생성 규칙으로 묶음을 만들어 outputs/에 쓴다")
    gen.add_argument("--rules", default=RULES_FILE, help="생성 규칙 경로(저장소 루트 기준)")
    gen.add_argument("--place", action="store_true", help="eval/dev/dev20/로 옮긴다(이미 있는 파일은 덮지 않는다)")
    sub.add_parser("check", allow_abbrev=False, help="커밋된 규칙으로 다시 만들어 커밋된 파일과 대조한다")
    sub.add_parser("install", allow_abbrev=False, help="커밋된 원천을 빌드·검증해 data/snapshots/<snapshot_id>/에 설치한다")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    return {"generate": cmd_generate, "check": cmd_check, "install": cmd_install}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
