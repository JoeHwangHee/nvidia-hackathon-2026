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
  (`peer_group_{snapshot_id}.csv`: 합성 자료 안에서 g0 규칙으로 고른 비교국, grouping_version `g0`). 상대국은 어느 나라에도
  배정되지 않은 합성 코드다(생성 규칙이 정한다. dev20은 XL~XQ).
- 자체 검산(구 개발계획 §8.1 "생성 자료를 독립 검사"): 응답 XML을 다시 읽어 모든 계열·달의 단가 변화율과 점유율 변화를
  계산하고, 발동한 (HS6, 상대국, 달)의 집합이 사례 집합과 정확히 같은지(사례 밖 경보 0건), 사례마다 발동 여부가 기대값과
  같은지, 모든 값이 탐지 기준에서 0.05 이상 떨어졌는지, 판정 근거 규칙마다 자료 불변식(구성효과 사례는 하위 단가 변화 0,
  설명 안 됨 사례는 구성효과를 뺀 within+잔차가 기준 이상 등)이 맞는지 본다. 단가 발동 사례는 policy_v1 제안 최소 기준
  (두 달 부모 행 100 USD·10 kg 이상, U2)을 넘고, 반올림 불안정 규칙 후보(U4)로 `rounding_unstable` 사례만 불안정이며,
  그 구간 끝도 기준에서 0.05 이상 떨어져야 한다. 하나라도 어긋나면 ValueError다.
- 임시 폴더에 수집기 SQLite를 재현하고(수집기 store_result로 응답을 적재, 시각은 생성 규칙의 고정 시각) 단위 S2로 빌드해
  `normalized_sha256`을 구하고, 단위 S3로 검증한다. 사례 목록·정답표는 단위 V4의 형식·분류 규칙 검사를 통과해야 한다.

출력(`run`): {"files": {저장소 루트 기준 상대경로: 텍스트}, "build_record": {...}, "summary": {...}}. 파일 배치(결정 기록에 남긴다):
- `eval/dev/{dataset}/input/cases.json`: 사례 목록(`case_id`·`hs6`·`partner`·`month`만). 채점 대상 실행 샌드박스가 읽는
  입력 하위 경로다.
- `eval/dev/{dataset}/input/source/raw/<request_id>.xml`: 응답 XML. 스냅샷 폴더의 `raw/`는 `.gitignore`가 빼므로 여기에
  커밋하고, `install`이 스냅샷 폴더로 복사한다.
- `data/snapshots/{snapshot_id}/`: `manifest.json`·`collection_log.json`·`snapshot_hash.json`(텍스트 원천). 빌드 기록
  `snapshot_build.json`은 `install`이 처음 쓰고 커밋한다(시각 키를 뺀 기록 키가 `build_record`와 같아야 한다).
- `data/reference/peer_group_{snapshot_id}.csv`: 합성 비교국 표(단위 S3가 빌드 기록의 파일 이름을 `data/reference/`에서 찾는다).
- `eval/dev/{dataset}/answers/answers.json`: 정답표. `answers/parent_series_ids.json`: dev20 부모 원본 계열 ID 목록
  (holdout40 제외 목록). `answers/generation_rules.json`: 생성 규칙 그대로(정본 직렬화). 정답 하위 경로는 어떤 샌드박스에도
  넣지 않는다.

명령(저장소 루트에서, 키 없이)
- `uv run --locked python -m eval.datagen.dev20 generate [--rules <생성 규칙>] [--place]`: 실행 폴더
  `outputs/datagen_dev20-{시각}/`(실행명 확보 N8)의 `datagen_dev20-{시각}/` 폴더(N7)에 파일을 저장소 상대경로 그대로 쓰고
  요약을 `datagen_dev20-{시각}.json`에 쓴다. `--place`면 파일을 저장소 자리로 옮긴다(이미 있는 파일은 덮지 않는다, N12).
- `uv run --locked python -m eval.datagen.dev20 check`: 커밋된 생성 규칙으로 다시 만들어 저장소의 파일과 바이트 단위로
  대조하고(파일을 쓰지 않는다), 커밋된 빌드 기록의 시각 키를 뺀 기록 키도 대조한다. 같으면 0, 다르면 1.
- `uv run --locked python -m eval.datagen.dev20 install`: 커밋된 원천으로 수집기 SQLite를 재현하고 단위 S2로 실행 폴더에
  빌드해 단위 S3 검증과 `normalized_sha256` 대조(사례 목록의 기록값)를 한 뒤, 스냅샷 폴더 `data/snapshots/{snapshot_id}/`에
  없는 것(`raw/`, 수집기 `snapshot.sqlite`, `snapshot_build.sqlite`, 없을 때만 `snapshot_build.json`)만 만든다. 이미 있는
  것은 먼저 모두 대조하고 하나라도 다르면 아무것도 쓰지 않고 1이다(덮지 않는다). 끝에 CLI `tradesentry snapshot-verify`와
  같은 기본 경로로 단위 S3를 돌려(raw 대조 켬) `ok`가 거짓이면 1이다. 만드는 파일은 모두 `.gitignore`가 빼는 자리다.
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
REFERENCE_DIR = "data/reference"

# 묶음(eval/dev/{dataset}) 기준 상대경로
CASES_FILE = "input/cases.json"
RAW_SOURCE = "input/source/raw"  # 스냅샷 폴더의 raw/는 .gitignore가 빼므로 응답 XML은 여기에 커밋한다
ANSWERS_FILE = "answers/answers.json"
IDS_FILE = "answers/parent_series_ids.json"
RULES_OUT = "answers/generation_rules.json"
# 스냅샷 폴더(data/snapshots/{snapshot_id}) 안의 커밋하는 텍스트 원천
MANIFEST_FILE = s2.MANIFEST_FILE
LOG_FILE = "collection_log.json"
HASH_FILE = s2.HASH_FILE
SNAPSHOT_TEXTS = (LOG_FILE, MANIFEST_FILE, HASH_FILE)
RECORD_TIME_KEYS = ("build_file", "built_at", "installed_at", "installed_from")  # 빌드 기록에서 실행마다 달라지는 키

UNIT_VALUE, SHARE = types.SIGNALS
TRIGGERED, NOT_TRIGGERED = types.SIGNAL_TRIGGERS
MARGIN = Fraction(5, 100)  # 탐지 기준에서 떨어져야 하는 거리(MT1 결정 기록: 탐지 경계 ±0.05 안의 값을 피한다)
# policy_v1 제안값(사용자 승인 전, 판정 정책 결정 기록 U2): 단가 신호는 두 달 모두 부모 HS6 행이 이 금액·중량 이상일 때만
# 사례가 되고, 미달이면 데이터 품질 목록으로 간다. dev20의 단가 발동 사례는 dev-0.1과 이 제안 어느 쪽에서도 같은 결과가
# 나오게 두 달 모두 이 기준 이상으로 만든다(자체 검산이 본다).
PROPOSED_MIN_AMOUNT = 100  # USD
PROPOSED_MIN_WEIGHT = 10  # kg
# 반올림 불안정 규칙 후보(사용자 승인 전, U4): 발동한 단가 신호에만, 금액은 그대로 두고 두 달 부모 중량을 Q ± 0.5 kg로
# 움직일 때의 r_U 구간이 r_U ≥ 0이면 하한 < θ, r_U < 0이면 상한 > −θ일 때 불안정(경계와 같으면 안정).
ROUNDING_KG = Fraction(1, 2)
ROW = "ROW"  # 나머지 세계(수집하지 않은 나라들). 전체국가 분모에만 들어간다
RULES_KEYS = {"schema_version", "dataset", "snapshot_id", "policy_version", "fixed_time", "world", "cases"}
WORLD_KEYS = {"period", "hs4", "hs6", "partners", "noise", "series", "rest_of_world", "peer_k", "peer_source_year"}
CASE_KEYS = {"case_id", "hs6", "partner", "month", "scenario_class", "events", "rule", "expected", "note"}
REQUEST_STATUSES = ("FAILED", "NOT_COLLECTED")
PEER_METHOD = "import_value_topk"
PEER_GROUPING = "g0"
PEER_CSV_NULL = "null"  # 비교국 표 CSV의 빈 값. 단위 G1 to_csv·data/reference/peer_group_g0.csv와 같다
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
        raise ValueError(f"생성 규칙의 schema_version은 {types.SCHEMA_VERSION}, dataset은 dev20·holdout40이다")
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
    # params_hash: 단위 G1(g0 비교국)과 같은 규칙(자료 계약 §2.3.6 "k, 기준연도, 후보국 목록의 해시"). grouping을 import하지
    # 않고 같은 식을 따로 적었다: {"candidates": 정렬한 후보국, "k": 정수, "source_year": 정수}의 정규 JSON(키 정렬, 구분자
    # ',' ':', ensure_ascii=True)의 sha256.
    params = {"candidates": sorted(view.partners), "k": k, "source_year": int(year)}
    params_hash = hashlib.sha256(json.dumps(params, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
                                 .encode("utf-8")).hexdigest()
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
        writer.writerow([PEER_CSV_NULL if row[k] is None else row[k] for k in types.PEER_GROUP_KEYS])
    return buffer.getvalue()


def peer_file_name(snapshot_id: str) -> str:
    """합성 비교국 표 파일 이름. 단위 S3가 빌드 기록의 이 이름을 data/reference/에서 찾는다(DT3 결정 기록 ⑧과 같은 방식)."""
    return f"peer_group_{snapshot_id}.csv"


# ----------------------------------------------------------------------------- 자체 검산
def self_check(rules: dict, view: View, peers: list[dict], policy: dict) -> dict:
    """발동 집합·기대 발동·기준 거리·판정 근거 규칙별 자료 불변식을 본다. 어긋나면 ValueError."""
    theta_u, theta_s = Fraction(policy["thresholds"]["unit_value"]), Fraction(policy["thresholds"]["share"])
    weight_tol = Fraction(str(policy["tolerance"]["weight_rounding_kg"]))  # 부모·하위 중량 대조 허용오차
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
        if case["expected"]["signals"][UNIT_VALUE] == TRIGGERED:
            (v0, q0), (v1, q1) = view.parent[(h, p, b)], view.parent[(h, p, t)]
            if min(v0, v1) < PROPOSED_MIN_AMOUNT or min(q0, q1) < PROPOSED_MIN_WEIGHT:
                problems.append(f"{case['case_id']}: 단가 발동 사례인데 두 달 부모 행이 policy_v1 제안 최소 기준"
                                f"({PROPOSED_MIN_AMOUNT} USD·{PROPOSED_MIN_WEIGHT} kg)에 못 미친다")
            unstable, gap = rounding_unstable(view, h, p, t, theta_u)
            if unstable != (u_rule == "rounding_unstable"):
                problems.append(f"{case['case_id']}: 반올림 불안정 규칙 후보(U4)의 판정이 판정 근거 규칙과 다르다"
                                f"({'불안정' if unstable else '안정'})")
            if gap is not None and gap < MARGIN:
                problems.append(f"{case['case_id']}: 중량 ±{_dec(ROUNDING_KG, 1)} kg 구간의 끝이 탐지 기준에서 "
                                f"{_dec(gap)}만 떨어졌다")
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


def rounding_unstable(view: View, h: str, p: str, t: str, theta: Fraction) -> tuple[bool, Fraction | None]:
    """반올림 불안정 규칙 후보(U4, 사용자 승인 전): 금액은 그대로 두고 두 달 부모 HS6 중량을 Q ± 0.5 kg로 움직일 때의
    r_U 구간이 r_U ≥ 0이면 하한 < θ, r_U < 0이면 상한 > −θ일 때 불안정이다(경계와 같으면 안정).
    (불안정 여부, 그 구간 끝과 탐지 기준의 거리(%p))를 돌려준다. 중량이 0.5 kg 이하라 구간을 만들 수 없으면 (참, None)."""
    (v0, q0), (v1, q1) = view.parent[(h, p, _shift(t, -12))], view.parent[(h, p, t)]
    if q0 - ROUNDING_KG <= 0 or q1 - ROUNDING_KG <= 0:
        return True, None
    r_u = view.r_u(h, p, t)
    if r_u >= 0:
        low = ((Fraction(v1) / (q1 + ROUNDING_KG)) / (Fraction(v0) / (q0 - ROUNDING_KG)) - 1) * 100
        return low < theta, abs(low - theta)
    high = ((Fraction(v1) / (q1 - ROUNDING_KG)) / (Fraction(v0) / (q0 + ROUNDING_KG)) - 1) * 100
    return high > -theta, abs(high + theta)


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
def materialize_collector(text_dir: Path, raw_dir: Path, target_dir: Path) -> Path:
    """커밋된 원천(text_dir의 manifest·collection_log·snapshot_hash와 raw_dir의 응답 XML)으로 수집기 형식 스냅샷 폴더를
    target_dir에 새로 만든다.

    응답마다 수집기 store_result를 불러 수집기 SQLite(`snapshot.sqlite`)와 raw 파일을 쓰고, 시각은 기록의 고정 시각으로
    바꾼다. target_dir는 없어야 한다."""
    text_dir, raw_dir, target_dir = Path(text_dir), Path(raw_dir), Path(target_dir)
    manifest = json.loads((text_dir / MANIFEST_FILE).read_text(encoding="utf-8"))
    log = json.loads((text_dir / LOG_FILE).read_text(encoding="utf-8"))
    snapshot_id, fixed = manifest["snapshot_id"], log["collected_at"]
    failed, not_collected = set(log["FAILED"]), set(log["NOT_COLLECTED"])
    target_dir.mkdir(parents=False, exist_ok=False)
    (target_dir / s2.RAW_DIR).mkdir()
    for name in SNAPSHOT_TEXTS:
        (target_dir / name).write_bytes((text_dir / name).read_bytes())
    ok_files = set()
    con = sqlite3.connect(target_dir / s2.COLLECTOR_DB)
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
                          "raw": (raw_dir / f"{rid}.xml").read_bytes(), "elapsed_ms": 0}
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
    present = {p.name for p in raw_dir.glob("*.xml")}
    if present != ok_files:
        raise ValueError(f"원천 raw 파일({len(present)})이 OK 요청({len(ok_files)})과 다르다")
    return target_dir


def record_keys(record: dict) -> dict:
    """빌드 기록에서 실행마다 달라지는 키(시각·빌드 파일 이름)를 뺀 것. 커밋된 기록과 다시 만든 기록을 이것으로 대조한다."""
    return {k: v for k, v in record.items() if k not in RECORD_TIME_KEYS}


def build_and_verify(collector_dir: Path, peer_file: Path, snapshot_id: str, policy: dict, db_path: Path) -> dict:
    """단위 S2로 db_path에 빌드하고 단위 S3로 검증한다. 검증이 실패하면 ValueError. 빌드 기록 dict를 돌려준다."""
    record = s2.build_to(db_path, snapshot_id, source_dir=collector_dir, policy=policy, peer_group_files=[peer_file])
    report = s3.verify_snapshot(snapshot_id, build_file=db_path, source_dir=collector_dir, peer_group_files=[peer_file])
    if not report["ok"]:
        failed = [c["name"] for c in report["checks"] if c["ok"] is False]
        raise ValueError(f"단위 S3 검증 실패: {failed}")
    return {**record, "import_observation_status": report["counts"].get("import_observation_status")}


# ----------------------------------------------------------------------------- 진입 함수
def paths_for(dataset: str, snapshot_id: str) -> dict:
    """저장소 루트 기준 자리: 묶음, 스냅샷 폴더, 비교국 표."""
    return {"bundle": f"eval/dev/{dataset}", "snapshot": f"{INSTALL_DIR}/{snapshot_id}",
            "peer": f"{REFERENCE_DIR}/{peer_file_name(snapshot_id)}"}


def run(inp: object) -> object:
    """진입 함수. 입력: 생성 규칙(JSON 객체).
    출력: {"files": {저장소 루트 기준 상대경로: 텍스트}, "build_record": 시각 키를 뺀 빌드 기록, "summary": {...}}."""
    rules = _check_rules(inp)
    policy = load_policy(rules["policy_version"])
    world = rules["world"]
    for case in rules["cases"]:
        if not isinstance(case, dict) or set(case) != CASE_KEYS:
            raise ValueError(f"사례 키는 {sorted(CASE_KEYS)}다")
        if case["hs6"] not in world["hs6"] or case["partner"] not in world["partners"] \
                or case["case_id"] != f"{case['hs6']}-{case['partner']}-{case['month']}":
            raise ValueError(f"사례 {case['case_id']}: case_id는 {{hs6}}-{{partner}}-{{month}}이고 세계 안의 계열이다")
    where = paths_for(rules["dataset"], rules["snapshot_id"])
    source, status, requests = source_files(rules)
    view = View(rules, source, status, requests)
    raw_sha256 = json.loads(source[HASH_FILE])["raw_combined_sha256"]
    peers = peer_rows(rules, view, raw_sha256)
    peer_text = peer_csv(peers)
    checked = self_check(rules, view, peers, policy)
    with tempfile.TemporaryDirectory() as tmp:
        texts, raw = Path(tmp) / "texts", Path(tmp) / "raw"
        raw.mkdir()
        texts.mkdir()
        for name, text in source.items():
            target = raw / name[len("raw/"):] if name.startswith("raw/") else texts / name
            target.write_text(text, encoding="utf-8")
        peer_file = Path(tmp) / peer_file_name(rules["snapshot_id"])  # 빌드 기록에 이 파일 이름이 남는다
        peer_file.write_text(peer_text, encoding="utf-8")
        collector = materialize_collector(texts, raw, Path(tmp) / rules["snapshot_id"])
        built = build_and_verify(collector, peer_file, rules["snapshot_id"], policy, Path(tmp) / "build.sqlite")
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
    bundle = where["bundle"]
    files = {f"{bundle}/{RAW_SOURCE}/{name[len('raw/'):]}": text for name, text in source.items()
             if name.startswith("raw/")}
    files.update({f"{where['snapshot']}/{name}": source[name] for name in SNAPSHOT_TEXTS})
    files[where["peer"]] = peer_text
    files[f"{bundle}/{CASES_FILE}"] = _json_text(cases_doc)
    files[f"{bundle}/{ANSWERS_FILE}"] = _json_text(answers_doc)
    files[f"{bundle}/{IDS_FILE}"] = _json_text({"schema_version": types.SCHEMA_VERSION, "dataset": rules["dataset"],
                                                "id_rule": ID_RULE, "parent_series_ids": ids})
    files[f"{bundle}/{RULES_OUT}"] = _json_text(rules)
    by_status: dict[str, int] = {}
    for value in status.values():
        by_status[value] = by_status.get(value, 0) + 1
    summary = {"snapshot_id": rules["snapshot_id"], "dataset": rules["dataset"],
               "policy_version": rules["policy_version"], "cases": len(rules["cases"]),
               "requests": dict(sorted(by_status.items())), "raw_combined_sha256": raw_sha256,
               "normalized_sha256": built["normalized_sha256"], "row_counts": built["row_counts"],
               "import_observation_status": built["import_observation_status"], "snapshot_verify_ok": True,
               "self_check": checked, "parent_series_ids": len(ids), "files": len(files)}
    build_record = record_keys({k: v for k, v in built.items() if k != "import_observation_status"})
    return {"files": dict(sorted(files.items())), "build_record": build_record, "summary": summary}


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


def _rel(path: Path, root: Path = REPO_ROOT) -> str:
    try:
        return str(Path(path).resolve().relative_to(Path(root).resolve()))
    except ValueError:
        return Path(path).name


def write_files(files: dict, root: Path) -> None:
    """텍스트 파일을 root 아래에 쓴다. 이미 있는 파일은 덮지 않는다(N8·N12)."""
    for name, text in files.items():
        path = Path(root) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "x", encoding="utf-8", newline="") as fh:
            fh.write(text)


def compare_committed(result: dict, root: Path) -> list[str]:
    """다시 만든 결과와 저장소(root)의 파일을 대조한다. 다른 파일·없는 파일, 묶음 폴더에 남는 파일, 시각 키를 뺀 기록 키가
    다른 빌드 기록의 목록(저장소 상대경로). 스냅샷 폴더에는 install이 만든 파일(.gitignore 대상)이 있으므로 남는 파일을
    보지 않는다."""
    root, files = Path(root), result["files"]
    wrong = [name for name, text in files.items()
             if not (root / name).is_file() or (root / name).read_bytes() != text.encode("utf-8")]
    bundle = root / paths_for(result["summary"]["dataset"], result["summary"]["snapshot_id"])["bundle"]
    present = {str(p.relative_to(root)) for p in bundle.rglob("*") if p.is_file() and p.name != ".gitkeep"}
    record_path = root / paths_for(result["summary"]["dataset"], result["summary"]["snapshot_id"])["snapshot"] \
        / s2.BUILD_RECORD
    if not record_path.is_file() or record_keys(json.loads(record_path.read_text(encoding="utf-8"))) \
            != result["build_record"]:
        wrong.append(str(record_path.relative_to(root)))
    return sorted(set(wrong) | (present - set(files)))


def _load_rules(path: str) -> dict:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def cmd_generate(args: argparse.Namespace) -> int:
    result = run(_load_rules(args.rules))
    run_dir, stamp = acquire_run_dir(REPO_ROOT / "outputs")
    write_files(result["files"], run_dir / f"{DOMAIN}-{stamp}")
    with open(run_dir / f"{DOMAIN}-{stamp}.json", "x", encoding="utf-8") as fh:
        fh.write(_json_text({**result["summary"], "build_record": result["build_record"]}))
    print(_rel(run_dir))
    if args.place:
        write_files(result["files"], REPO_ROOT)
        print(f"저장소 자리로 옮겼다({len(result['files'])}개 파일). 빌드 기록은 install이 쓴다")
    print(_json_text(result["summary"]), end="")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    result = run(_load_rules(RULES_FILE))
    wrong = compare_committed(result, REPO_ROOT)
    print(json.dumps({"ok": not wrong, "files": len(result["files"]) + 1, "different": wrong}, ensure_ascii=False))
    return 0 if not wrong else 1


def _collector_rows(path: Path) -> dict:
    """수집기 SQLite의 표별 행(정렬). 이미 있는 수집기 SQLite가 다시 만든 것과 같은지 볼 때 쓴다."""
    con = s2.open_read_only(path)
    try:
        return {table: sorted(con.execute(f'SELECT * FROM "{table}"').fetchall(), key=repr)
                for table in ("collection_receipt", "collection_attempt", "observation", "snapshot_meta")}
    finally:
        con.close()


def _copy_new(source: Path, target: Path) -> None:
    with open(source, "rb") as src, open(target, "xb") as dst:
        while chunk := src.read(1 << 20):
            dst.write(chunk)


def install(root: Path = REPO_ROOT) -> dict:
    """커밋된 원천으로 스냅샷을 빌드·검증하고 스냅샷 폴더에 없는 것만 만든다(모듈 머리 설명의 install). 요약을 돌려준다.

    실패하면 {"ok": False, ...}이고 아무것도 덮지 않는다. root는 저장소 뿌리(시험은 임시 사본을 준다)."""
    root = Path(root)
    bundle = root / DEV20_DIR
    cases = json.loads((bundle / CASES_FILE).read_text(encoding="utf-8"))
    snapshot_id, expected = cases["snapshot_id"], cases["snapshot_normalized_sha256"]
    where = paths_for(cases["dataset"], snapshot_id)
    target, peer = root / where["snapshot"], root / where["peer"]
    policy = load_policy(cases["policy_version"])
    run_dir, stamp = acquire_run_dir(root / "outputs")
    collector = materialize_collector(target, bundle / RAW_SOURCE, run_dir / f"{DOMAIN}-{stamp}")
    record = s2.build_snapshot(snapshot_id, out_dir=run_dir, stamp=stamp, source_dir=collector, policy=policy,
                               peer_group_files=[peer])
    build_file = run_dir / f"{s2.DOMAIN}-{stamp}.sqlite"
    report = s3.verify_snapshot(snapshot_id, build_file=build_file, source_dir=collector, peer_group_files=[peer])
    if not report["ok"] or record["normalized_sha256"] != expected:
        return {"ok": False, "run_dir": _rel(run_dir, root), "snapshot_verify_ok": report["ok"],
                "normalized_sha256_matches": record["normalized_sha256"] == expected}
    # 1단계: 이미 있는 것을 모두 대조한다(쓰기 전에 멈출 곳을 다 찾는다)
    raws = sorted(p.name for p in (collector / s2.RAW_DIR).glob("*.xml"))
    problems = [f"raw/{name}" for name in raws if (target / s2.RAW_DIR / name).exists()
                and (target / s2.RAW_DIR / name).read_bytes() != (collector / s2.RAW_DIR / name).read_bytes()]
    if (target / s2.RAW_DIR).exists() and {p.name for p in (target / s2.RAW_DIR).glob("*.xml")} - set(raws):
        problems.append("raw/ 남는 파일")
    if (target / s2.COLLECTOR_DB).exists() and \
            _collector_rows(target / s2.COLLECTOR_DB) != _collector_rows(collector / s2.COLLECTOR_DB):
        problems.append(s2.COLLECTOR_DB)
    if (target / s2.BUILD_FILE).exists() and s2.file_normalized_sha256(target / s2.BUILD_FILE) != expected:
        problems.append(s2.BUILD_FILE)
    record_path = target / s2.BUILD_RECORD
    if record_path.exists() and record_keys(json.loads(record_path.read_text(encoding="utf-8"))) != record_keys(record):
        problems.append(s2.BUILD_RECORD)
    if problems:
        return {"ok": False, "run_dir": _rel(run_dir, root), "different_in_place": problems}
    # 2단계: 없는 것만 만든다(이미 있으면 실패하는 방식)
    created = []
    (target / s2.RAW_DIR).mkdir(exist_ok=True)
    missing = [name for name in raws if not (target / s2.RAW_DIR / name).exists()]
    for name in missing:
        _copy_new(collector / s2.RAW_DIR / name, target / s2.RAW_DIR / name)
    if missing:
        created.append(f"raw/*.xml({len(missing)})")
    for source_file, name in ((collector / s2.COLLECTOR_DB, s2.COLLECTOR_DB), (build_file, s2.BUILD_FILE)):
        if not (target / name).exists():
            _copy_new(source_file, target / name)
            created.append(name)
    if not record_path.exists():
        installed = {**record, "build_file": s2.BUILD_FILE, "installed_from": build_file.name,
                     "installed_at": datetime.now(types.KST).isoformat(timespec="seconds")}
        with open(record_path, "x", encoding="utf-8") as fh:
            fh.write(_json_text(installed))
        created.append(s2.BUILD_RECORD)
    # 3단계: CLI snapshot-verify와 같은 기본 경로로 단위 S3를 돌린다(raw 대조 켬, 비교국 표는 data/reference/에서 찾음)
    if root.resolve() == REPO_ROOT.resolve():
        final = s3.verify_snapshot(snapshot_id)  # CLI `tradesentry snapshot-verify --snapshot <id>`와 같은 입력
    else:  # 임시 사본(시험): 단위 S3의 기본 경로가 이 저장소를 가리키므로 자리를 명시한다
        final = s3.verify_snapshot(snapshot_id, build_file=target / s2.BUILD_FILE, source_dir=target, check_raw=True,
                                   peer_group_files=[peer])
    ok = bool(final["ok"]) and final["recorded_normalized_sha256"] == expected
    return {"ok": ok, "run_dir": _rel(run_dir, root), "snapshot_id": snapshot_id, "normalized_sha256": expected,
            "snapshot_verify_ok": bool(final["ok"]), "created": created,
            "failed_checks": [c["name"] for c in final["checks"] if c["ok"] is False]}


def cmd_install(args: argparse.Namespace) -> int:
    result = install(REPO_ROOT)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1


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
