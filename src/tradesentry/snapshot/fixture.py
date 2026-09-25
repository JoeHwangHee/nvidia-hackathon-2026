"""단위 S4 합성 스냅샷 생성.

단위 ID: S4
도메인명: snapshot_fixture
소유: D
입력: 생성 규칙
출력: `controlled_fixture_v0`
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.ingest, tradesentry.snapshot

합성 시험자료(정답을 알고 규칙대로 만든 가짜 자료) `controlled_fixture_v0`를 생성 규칙 파일
`data/snapshots/controlled_fixture_v0/fixture_spec.json`에서 만든다. 모든 금액·중량과 상대국은 합성이다. 정본: 병렬 개발
규칙 docs/rules/PARALLEL_DEV_RULES.md §2(구성·넘기기), 자료 계약 docs/rules/DATA_CONTRACT_V1.md §2.3·§3.4·§4.4, 로드맵
DT3 행. 세부 결정은 결정 기록 docs/tracking/decisions/20260925-0140-data-decision-dt3-fixture.md.

만드는 길(실스냅샷과 같은 길. 그래서 `--snapshot` 값만 바꿔 실스냅샷과 교체된다)
1. 수집기 형식 원천: 수집기(`tradesentry.ingest`)의 `build_manifest`·`open_snapshot(id, "controlled")`·`store_result`로
   manifest·raw 응답(XML)·수집기 SQLite를 만든다. 네트워크는 쓰지 않는다. 응답 XML은 이 모듈이 규칙에서 합성해
   `store_result`에 넘긴다. 수집기가 쓰는 폴더(`ingest.SNAP_DIR`)와 시각(`ingest.now_iso`)은 만드는 동안만 작업 폴더와
   규칙의 고정 시각(`generated_at`)으로 바꾸고 되돌린다. 실패 응답은 본문 없이 넘겨 시각 이름 파일(`raw/failed/`)이 생기지
   않게 한다. 그래서 같은 규칙이면 늘 같은 원천이 나온다. 수집기 메타에는 `last_collect_at`(= `generated_at`),
   `source_url`(생성 규칙과 이 모듈의 저장소 상대경로, 자료 계약 §2.3.1), 합성 자료에 맞춘 `precision_rule`을 넣는다.
   `coverage_status`는 수집기 기본값 그대로다(v1이 값 집합을 정하지 않았다).
2. 합성 비교국 표: 만든 원천의 2023년 OBSERVED 부모 HS6 행 수입금액 합으로 `g0` 규칙(자료 계약 §2.3.6
   `import_value_topk`: HS6·대상국마다 대상국을 뺀 상위 k개국, 합이 같으면 국가 코드 사전순)을 적용한 표를 만든다.
   `source_version`=`controlled_fixture_v0`, `input_sha256`=이 원천의 raw 결합 해시, `baci_country_code`·`similarity`·
   `community_id`=null이다. 합성 자료의 비교 대상은 이 합성 표로 정해지고 실자료의 `g0`·`g1`과 무관하다(§2.3.6).
3. 스냅샷 빌드: 단위 S2(`build.build_snapshot`)로 파생 SQLite와 빌드 기록을 만든다. 무거래 확정 `CONFIRMED_NO_TRADE`는
   승격으로만 생기므로 규칙의 `promotion`(단위 S2가 아는 규칙 이름)을 적용한다. 승인된 정책이 아니라 합성 생성 규칙의
   일부라서 빌드 기록의 `policy_version`은 null이다(개발용 정책 `dev-0.1`은 승격하지 않는다).
4. 검증: 단위 S3(`verify.verify_snapshot`)을 raw 대조를 켜고 돌린다.

진입 함수와 함수
- `run(inp)`: 입력 {"spec_file": 저장소 루트 기준 경로} 또는 {"spec": 규칙 객체}. null이면 정본 규칙 파일. 임시
  폴더에서 1~4를 하고 요약(JSON 객체)을 돌려준다. 시각·경로가 없는 결정적 요약이다(골든 시험).
- `materialize(repo_root=저장소 루트)`: 정본 자리를 채운다(키·네트워크 없이 도는 한 번의 호출). 1~4를
  `outputs/snapshot_fixture-{시각}/`(실행 폴더, 이미 있으면 실패)에서 한 뒤 아래 파일을 정본 자리에 둔다. 이미 있는
  파일은 덮지 않는다: 먼저 모두 대조해(텍스트 파일은 바이트, 수집기 SQLite는 빌드가 읽는 표의 행, 빌드 SQLite는
  `normalized_sha256`, 빌드 기록은 시각을 뺀 기록 키) 하나라도 다르면 아무것도 쓰지 않고 멈춘다.
  - 커밋하는 텍스트 원천: `data/snapshots/controlled_fixture_v0/`의 `fixture_spec.json`(생성 규칙), `manifest.json`,
    `snapshot_hash.json`(raw 결합 해시), `snapshot_build.json`(빌드 기록, `normalized_sha256`), 그리고
    `data/reference/peer_group_controlled_fixture_v0.csv`(합성 비교국 표. 단위 S3가 빌드 기록의 파일 이름을
    `data/reference/`에서 찾는다).
  - 커밋하지 않는 파일(`.gitignore`가 뺀다): `raw/*.xml`, `snapshot.sqlite`(수집기 SQLite), `snapshot_build.sqlite`.
  - 끝에 정본 자리를 단위 S3로 검증한다(raw 대조 켬). 새 작업 폴더에서 한 번 부르면 자료 접근층
    `open_snapshot("controlled_fixture_v0")`과 `snapshot-verify` 기본값이 그 파일을 찾는다.
  - 실행 폴더에는 원천(`snapshot_fixture-{시각}/`: `controlled_fixture_v0/`와 합성 비교국 표), 단위 S2 빌드
    (`snapshot_build-{시각}.sqlite`·`.json`), 요약(`snapshot_fixture-{시각}.json`)이 남는다(`outputs/`는 커밋하지 않는다).
- 재현 명령(저장소 루트): `uv run --locked python -c "from tradesentry.snapshot import fixture; fixture.materialize()"`
  (한 줄 요약을 찍는다. 이미 모두 있으면 새로 쓰지 않고 대조·검증만 한다).

생성 규칙(`fixture_spec.json`)의 뜻
- `collection_plan`: 수집 설정(수집기 `build_manifest` 입력). 대상 HS6 3개 × 상대국 10개 × 36개월.
- 배경 계열(사례가 아닌 HS6×상대국): HS10 두 개가 같은 중량을 나눠 갖고, HS10 단가(`unit_value_milli`, 1/1000 USD/kg)에
  상대국 단가 계수(`unit_value_permille`)를 곱한다. 기준 월 금액(`monthly_usd`)에서 HS10 중량 q = 금액 ÷ (두 단가 합)을
  구하고, 달마다 중량에 계절 계수(`seasonal_permille.weight`, 상대국·HS6마다 달을 밀어 씀)와 연 계수를, 단가에 계절·연
  계수를 곱한다. HS10 금액 = 중량 × 단가(USD 정수로 사사오입). 부모 HS6 행은 HS10 행의 합이라 금액·중량이 정확히 맞는다.
  같은 달의 계절 계수가 해마다 같아 전년동월 단가 변화율은 몇 % 안이고 점유율 변화도 작다.
- 전체국가(`ALL`): HS10마다 상대국 HS10 참값의 합 + 나머지 나라 몫(`rest_of_world`). 사례 HS6의 사례 두 달은 전체국가
  금액이 `world_usd`가 되도록 나머지 나라 몫을 맞춘다. 범위 밖 HS6(`out_of_scope_hs6`)는 HS4 조회에만 나온다(행 규칙 7).
- `cases`: 사례 계열은 모든 달이 기준월 값이고 비교월만 비교월 값이다. `hs10`이 `REQUEST_FAILED`면 그 달 HS10은
  응답이 없고(요청 실패는 `gaps`가 만든다), 전체국가에 더할 참값은 `hs10_unobserved`다.
- `gaps`: `request_failed`(그 요청 실패 → `REQUEST_FAILED`), `request_not_collected`(수신 기록 없음 → `NOT_COLLECTED`),
  `no_trade_hs6_month`(그 달 그 HS6만 거래 없음 → HS6 조회가 빈 달 `UNRESOLVED_ZERO` → 승격 → `CONFIRMED_NO_TRADE`),
  `empty_hs4_month`(그 달 그 나라 HS4 전체 거래 없음 → `UNRESOLVED_ZERO`. 같은 HS4 아래 OBSERVED 행이 없어 승격되지
  않는다), `import_zero_export_only`(수입 0·수출만 있는 달 → `OBSERVED` 값 0).
- 응답 XML의 항목 이름과 순서는 수집기 머리말의 엔드포인트 필드 목록을 따르고, 총계 행(`총계`, 코드 `-`)을 맨 앞에 둔다.
  요청 실패는 HTTP 500 세 번(본문 없음)으로 적는다.

정답과의 분리: 이 모듈과 스냅샷 폴더에는 사례의 기대 판정·시나리오 이름을 두지 않는다(`src/tradesentry/`는 샌드박스
이미지에 들어갈 수 있다). 사례는 이름표(A/B/C)와 사례 식별자 `{hs6}-{partner}-{month}`(단위 P2 형식)로만 가리킨다.
로컬 절대경로는 어떤 출력에도 적지 않는다(자료 계약 §10.3 N13).
"""
import contextlib
import csv
import hashlib
import io
import json
import os
import re
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from tradesentry import ingest
from tradesentry.contract import types
from tradesentry.snapshot import build, verify

REPO_ROOT = Path(__file__).resolve().parents[3]
DOMAIN = "snapshot_fixture"
SNAPSHOT_ID = types.FIXTURE_SNAPSHOT_ID
SNAPSHOTS_DIR = ("data", "snapshots")
REFERENCE_DIR = ("data", "reference")
SPEC_FILE = "fixture_spec.json"
PEER_GROUP_FILE = f"peer_group_{SNAPSHOT_ID}.csv"
SOURCE_URL = [f"data/snapshots/{SNAPSHOT_ID}/{SPEC_FILE}", "src/tradesentry/snapshot/fixture.py"]
PRECISION_RULE = ("amount exact integer USD; weight integer kg (controlled fixture: synthetic integers, "
                  "HS10 child rows and total rows sum exactly)")
HASH_METHOD = "스냅샷 폴더에서 `shasum -a 256 raw/*.xml | shasum -a 256`"
PARTNER_NAME = "합성국가 {code}"  # 응답의 국가명 칸(statCdCntnKor1)
ITEM_NAME = "합성 품목 {code}"  # 응답의 품목명 칸(statKor)
TOTAL_MARK = "-"  # 총계 행의 코드·이름 칸(수집기 머리말: hsCd='-', statCd='-')
TOTAL_YEAR = "총계"
OK_RESULT = {"ok": True, "http_status": 200, "attempts": 1, "error": None, "attempt_errors": [], "elapsed_ms": 0}
FAILED_RESULT = {"ok": False, "http_status": 500, "attempts": 3, "raw": b"", "error": "HTTPError 500",
                 "attempt_errors": ["HTTPError 500"] * 3, "elapsed_ms": 0}
FAILED = "request_failed"
NOT_COLLECTED = "request_not_collected"
GAP_KINDS = (FAILED, NOT_COLLECTED, "no_trade_hs6_month", "empty_hs4_month", "import_zero_export_only")
SPEC_KEYS = ("schema_version", "snapshot_id", "source_kind", "generated_at", "collection_plan", "partners", "hs6",
             "seasonal_permille", "yearly_permille", "out_of_scope_hs6", "cases", "gaps", "promotion", "peer_group")
RECORD_KEYS = ("schema_version", "snapshot_id", "normalized_sha256", "raw_sha256", "policy_version",
               "confirmed_no_trade_rule", "confirmed_no_trade_rows", "peer_group_files", "row_counts")
KST_ISO_RE = re.compile(r"(20[0-9]{2})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})\+09:00")


class FixtureError(Exception):
    """생성 규칙이 맞지 않거나 정본 자리의 파일이 다시 만든 것과 다르다. 메시지에 로컬 절대경로를 넣지 않는다."""


# ----------------------------------------------------------------------------- 규칙 읽기
def spec_path(repo_root: Path | None = None) -> Path:
    """정본 생성 규칙 파일 경로."""
    return Path(REPO_ROOT if repo_root is None else repo_root).joinpath(*SNAPSHOTS_DIR, SNAPSHOT_ID, SPEC_FILE)


def parse_spec(spec: object) -> dict:
    """생성 규칙 객체를 검사해 그대로 돌려준다(고치지 않는다). 맞지 않으면 FixtureError."""
    if not isinstance(spec, dict):
        raise FixtureError("생성 규칙은 JSON 객체다")
    missing = [key for key in SPEC_KEYS if key not in spec]
    if missing:
        raise FixtureError(f"생성 규칙에 키가 없다: {', '.join(missing)}")
    if spec["schema_version"] != types.SCHEMA_VERSION or spec["snapshot_id"] != SNAPSHOT_ID:
        raise FixtureError(f"생성 규칙의 schema_version은 {types.SCHEMA_VERSION}, snapshot_id는 {SNAPSHOT_ID}이다")
    if spec["source_kind"] != "controlled":
        raise FixtureError("합성 시험자료의 source_kind는 controlled다")
    if not isinstance(spec["generated_at"], str) or not KST_ISO_RE.fullmatch(spec["generated_at"]):
        raise FixtureError("generated_at은 KST ISO 8601(+09:00, 초 단위)이다")
    plan = spec["collection_plan"]
    if plan.get("snapshot_id") != SNAPSHOT_ID or len(plan.get("hs4_scan", [])) != 1:
        raise FixtureError("collection_plan의 snapshot_id가 다르거나 HS4 스캔이 하나가 아니다")
    hs4 = plan["hs4_scan"][0]
    partners = list(plan["partners"])
    if set(spec["partners"]) != set(partners) or len(set(partners)) != len(partners):
        raise FixtureError("partners가 수집 설정의 상대국과 다르다")
    for code in partners:
        if not re.fullmatch(r"[A-Z]{2}", code) or code == types.ALL_PARTNER:
            raise FixtureError(f"상대국 코드는 관세청 2자리 형식(대문자 두 글자)이다: {code!r}")
    if [item["code"] for item in spec["hs6"]] != list(plan["hs6"]):
        raise FixtureError("hs6 목록이 수집 설정의 HS6와 순서까지 같아야 한다")
    for item in spec["hs6"]:
        code = item["code"]
        if not types.HS6_RE.fullmatch(code) or code[:4] != hs4:
            raise FixtureError(f"HS6 {code}가 6자리가 아니거나 HS4 {hs4} 아래가 아니다")
        if len(item["hs10"]) != 2 or any(not types.HS10_RE.fullmatch(c) or c[:6] != code for c in item["hs10"]):
            raise FixtureError(f"HS6 {code}의 HS10은 그 HS6로 시작하는 10자리 코드 두 개다")
    other = spec["out_of_scope_hs6"]
    if other["code"] in plan["hs6"] or other["code"][:4] != hs4 or other["hs10"][:6] != other["code"]:
        raise FixtureError("범위 밖 HS6는 수집 설정 밖이고 같은 HS4 아래여야 한다")
    for gap in spec["gaps"]:
        if gap.get("kind") not in GAP_KINDS:
            raise FixtureError(f"모르는 gaps 종류: {gap.get('kind')!r}")
    if spec["promotion"].get("rule") != build.PROMOTION_RULE:
        raise FixtureError(f"promotion.rule은 단위 S2가 아는 {build.PROMOTION_RULE}이다")
    peer = spec["peer_group"]
    if (peer.get("grouping_version"), peer.get("method")) != ("g0", "import_value_topk"):
        raise FixtureError("합성 비교국 표는 g0 규칙(import_value_topk)으로 만든다")
    return spec


def load_spec(path: Path | None = None) -> tuple[dict, bytes]:
    """생성 규칙 파일을 읽어 (검사한 규칙, 파일 바이트)를 돌려준다."""
    data = Path(spec_path() if path is None else path).read_bytes()
    return parse_spec(json.loads(data.decode("utf-8"))), data


def _stamp(iso: str) -> str:
    """KST ISO 시각 → yymmddhhmmss."""
    year, month, day, hour, minute, second = KST_ISO_RE.fullmatch(iso).groups()
    return f"{year[2:]}{month}{day}{hour}{minute}{second}"


def _rhu(numerator: int, denominator: int) -> int:
    """음이 아닌 정수 나눗셈의 사사오입(ROUND_HALF_UP)."""
    if numerator < 0 or denominator <= 0:
        raise FixtureError("음수나 0으로 나누는 계산이 생겼다")
    return (2 * numerator + denominator) // (2 * denominator)


def _add(total: list[int] | None, values: list[int]) -> list[int]:
    return list(values) if total is None else [a + b for a, b in zip(total, values)]


# ----------------------------------------------------------------------------- 참값 표
def _case_cells(case: dict, month: str) -> dict[str, list[int]]:
    side = case["comparison"] if month == case["month"] else case["baseline"]
    rows = side["hs10"] if isinstance(side["hs10"], list) else side["hs10_unobserved"]
    cells = {row["code"]: [row["V"], row["Q"], 0, 0] for row in rows}
    if [sum(c[0] for c in cells.values()), sum(c[1] for c in cells.values())] != \
            [side["parent"]["V"], side["parent"]["Q"]]:
        raise FixtureError(f"사례 {case['label']} {month}: HS10 합이 부모 V·Q와 다르다")
    return cells


def trade_table(spec: dict) -> dict:
    """규칙의 참값 표(수집 여부와 관계없는 거래). 값은 [수입 금액, 수입 중량, 수출 금액, 수출 중량]이다.

    {"months", "children": {(HS6, 상대국, 달): {HS10: 값}}, "other": {(상대국, 달): 값}(범위 밖 HS6),
    "world": {(HS10, 달): 값}(전체국가)}. 거래가 없는 칸은 키가 없다.
    """
    plan = spec["collection_plan"]
    months = ingest.months_between(plan["period"]["start"], plan["period"]["end"])
    partners = list(plan["partners"])
    season_w, season_u = spec["seasonal_permille"]["weight"], spec["seasonal_permille"]["unit_value"]
    yearly = spec["yearly_permille"]
    cases = {(case["hs6"], case["partner"]): case for case in spec["cases"]}
    no_trade = {(g["hs6"], g["partner"], g["month"]) for g in spec["gaps"] if g["kind"] == "no_trade_hs6_month"}
    empty = {(g["partner"], g["month"]) for g in spec["gaps"] if g["kind"] == "empty_hs4_month"}
    export_only = {(g["hs6"], g["partner"], g["month"]): g for g in spec["gaps"]
                   if g["kind"] == "import_zero_export_only"}
    children: dict[tuple, dict[str, list[int]]] = {}
    for j, item in enumerate(spec["hs6"]):
        hs6, codes = item["code"], item["hs10"]
        for i, partner in enumerate(partners):
            factor = spec["partners"][partner]["unit_value_permille"]
            case = cases.get((hs6, partner))
            if case is None and partner not in item["monthly_usd"]:
                raise FixtureError(f"HS6 {hs6}·{partner}: 사례도 아니고 monthly_usd도 없다")
            for k, month in enumerate(months):
                key = (hs6, partner, month)
                if (partner, month) in empty or key in no_trade:
                    continue
                if case is not None:
                    children[key] = _case_cells(case, month)
                elif key in export_only:
                    gap = export_only[key]
                    children[key] = {gap["hs10"]: [0, 0, gap["export_usd"], gap["export_kg"]]}
                else:
                    unit = [_rhu(u * factor, 1000) for u in item["unit_value_milli"]]
                    base_q = _rhu(item["monthly_usd"][partner] * 1000, sum(unit))
                    q = _rhu(base_q * season_w[(k + i + j) % 12] * yearly["weight"][k // 12], 10 ** 6)
                    cells = {}
                    for code, u_milli in zip(codes, unit):
                        u = _rhu(u_milli * season_u[(k + 2 * i + j) % 12] * yearly["unit_value"][k // 12], 10 ** 6)
                        cells[code] = [_rhu(q * u, 1000), q, 0, 0]
                    children[key] = cells
    other_spec = spec["out_of_scope_hs6"]
    other_unit = other_spec["unit_value_milli"]
    other = {(partner, month): [_rhu(other_spec["monthly_kg"][partner] * other_unit, 1000),
                                other_spec["monthly_kg"][partner], 0, 0]
             for partner in partners for month in months if (partner, month) not in empty}
    world: dict[tuple, list[int]] = {}
    for (_, _, month), cells in children.items():
        for code, values in cells.items():
            world[(code, month)] = _add(world.get((code, month)), values)
    for (_, month), values in other.items():
        world[(other_spec["hs10"], month)] = _add(world.get((other_spec["hs10"], month)), values)
    forced = {}
    for case in spec["cases"]:
        forced[(case["hs6"], case["baseline_month"])] = case["world_usd"]["baseline"]
        forced[(case["hs6"], case["month"])] = case["world_usd"]["comparison"]
    for k, month in enumerate(months):
        row_q = other_spec["rest_of_world_monthly_kg"]
        world[(other_spec["hs10"], month)] = _add(world.get((other_spec["hs10"], month)),
                                                  [_rhu(row_q * other_unit, 1000), row_q, 0, 0])
        for item in spec["hs6"]:
            hs6, codes, row = item["code"], item["hs10"], item["rest_of_world"]
            partners_usd = sum(values[0] for (h, _, m), cells in children.items() if h == hs6 and m == month
                               for values in cells.values())
            if (hs6, month) in forced:
                total = forced[(hs6, month)] - partners_usd
                if total < 0:
                    raise FixtureError(f"{hs6} {month}: 상대국 합이 사례의 전체국가 금액보다 크다")
            else:
                total = _rhu(row["monthly_usd"] * season_w[k % 12] * yearly["rest_of_world"][k // 12], 10 ** 6)
            first = _rhu(total * row["first_hs10_permille"], 1000)
            for code, usd, u_milli in zip(codes, (first, total - first), item["unit_value_milli"]):
                world[(code, month)] = _add(world.get((code, month)), [usd, _rhu(usd * 1000, u_milli), 0, 0])
    return {"months": months, "children": children, "other": other, "world": world}


# ----------------------------------------------------------------------------- 응답 만들기
def _nitem(month: str, partner: str, code: str, values: list[int]) -> dict:
    """국가별 품목별(nitemtrade) 응답 항목. 필드 순서는 수집기 머리말과 같다."""
    imp_v, imp_q, exp_v, exp_q = values
    return {"year": f"{month[:4]}.{month[4:]}", "statCdCntnKor1": PARTNER_NAME.format(code=partner),
            "statCd": partner, "statKor": ITEM_NAME.format(code=code), "hsCd": code, "expWgt": str(exp_q),
            "expDlr": str(exp_v), "impWgt": str(imp_q), "impDlr": str(imp_v), "balPayments": str(exp_v - imp_v)}


def _item(month: str, code: str, values: list[int]) -> dict:
    """품목별(itemtrade, 전체국가) 응답 항목. 필드 순서는 수집기 머리말과 같다."""
    imp_v, imp_q, exp_v, exp_q = values
    return {"year": f"{month[:4]}.{month[4:]}", "balPayments": str(exp_v - imp_v), "expDlr": str(exp_v),
            "expWgt": str(exp_q), "hsCode": code, "impDlr": str(imp_v), "impWgt": str(imp_q),
            "statKor": ITEM_NAME.format(code=code)}


def _with_total(endpoint: str, items: list[dict]) -> list[dict]:
    """총계 행(요청 구간 전체 합)을 맨 앞에 붙인다. 행이 없으면 총계 행도 없다(빈 응답)."""
    if not items:
        return []
    values = [sum(int(item[field]) for item in items) for field in ("impDlr", "impWgt", "expDlr", "expWgt")]
    if endpoint == "nitemtrade":
        total = _nitem("000000", TOTAL_MARK, TOTAL_MARK, values)
        total.update({"statCdCntnKor1": TOTAL_MARK, "statKor": TOTAL_MARK})
    else:
        total = _item("000000", TOTAL_MARK, values)
        total["statKor"] = TOTAL_MARK
    total["year"] = TOTAL_YEAR
    return [total] + items


def _sum_cells(cells: dict[str, list[int]]) -> list[int]:
    return [sum(values[n] for values in cells.values()) for n in range(4)]


def response_items(spec: dict, table: dict, request: dict) -> list[dict]:
    """계획 요청 하나의 응답 항목(총계 행 포함). 달 순서, 달 안에서는 코드 순서다."""
    endpoint, params = request["endpoint"], request["params"]
    code, partner = params["hsSgn"], params.get("cntyCd")
    other_spec = spec["out_of_scope_hs6"]
    hs10_of = {item["code"]: item["hs10"] for item in spec["hs6"]}
    world_codes = sorted([c for codes in hs10_of.values() for c in codes] + [other_spec["hs10"]])
    items: list[dict] = []
    for month in request["months"]:
        if endpoint == "nitemtrade" and len(code) == 4:  # HS4 스캔: 상대국의 HS6 행(부모 HS6 행)
            rows = {h: _sum_cells(table["children"][(h, partner, month)]) for h in hs10_of
                    if (h, partner, month) in table["children"]}
            if (partner, month) in table["other"]:
                rows[other_spec["code"]] = table["other"][(partner, month)]
            items += [_nitem(month, partner, h, rows[h]) for h in sorted(rows)]
        elif endpoint == "nitemtrade" and len(code) == 6:  # HS6 조회: 상대국의 HS10 행
            cells = table["children"].get((code, partner, month), {})
            items += [_nitem(month, partner, c, cells[c]) for c in sorted(cells)]
        elif endpoint == "itemtrade":  # 품목별 전체국가: HS10 행(HS4 조회는 그 HS4 아래 HS10 전부)
            items += [_item(month, c, table["world"][(c, month)]) for c in world_codes
                      if c.startswith(code) and (c, month) in table["world"]]
        else:
            raise FixtureError(f"요청 {request['request_id']}: 만들 수 없는 엔드포인트·코드 자릿수다")
    return _with_total(endpoint, items)


def response_xml(items: list[dict]) -> bytes:
    """정상 봉투의 응답 XML(수집기 parse_response가 읽는 모양)."""
    body = "".join("<item>" + "".join(f"<{k}>{escape(v)}</{k}>" for k, v in item.items()) + "</item>"
                   for item in items)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><response><header><resultCode>00</resultCode>'
            f"<resultMsg>정상서비스.</resultMsg></header><body><items>{body}</items></body></response>").encode("utf-8")


def plan_answers(spec: dict) -> tuple[list[dict], dict[str, object]]:
    """(manifest 요청 목록, request_id → 응답 항목 목록 또는 FAILED·NOT_COLLECTED)."""
    requests = ingest.build_manifest(spec["collection_plan"])
    table = trade_table(spec)
    special = {}
    for gap in spec["gaps"]:
        if gap["kind"] in (FAILED, NOT_COLLECTED):
            params = {"strtYymm": gap["strtYymm"], "endYymm": gap["endYymm"], "hsSgn": gap["hsSgn"]}
            if "cntyCd" in gap:
                params["cntyCd"] = gap["cntyCd"]
            special[ingest.request_id(gap["endpoint"], params)] = gap["kind"]
    if set(special) - {request["request_id"] for request in requests}:
        raise FixtureError("gaps의 요청이 수집 계획에 없다")
    answers = {}
    for request in requests:
        rid = request["request_id"]
        answers[rid] = special[rid] if rid in special else response_items(spec, table, request)
    return requests, answers


# ----------------------------------------------------------------------------- 수집기 형식 원천
@contextlib.contextmanager
def _collector_at(root: Path, fixed_time: str):
    """수집기의 스냅샷 폴더 뿌리와 시각을 잠깐 바꾼다(만드는 동안만. 끝나면 되돌린다)."""
    saved_dir, saved_clock = ingest.SNAP_DIR, ingest.now_iso
    ingest.SNAP_DIR = Path(root)
    ingest.now_iso = lambda: fixed_time
    try:
        yield
    finally:
        ingest.SNAP_DIR, ingest.now_iso = saved_dir, saved_clock


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


def _write_new(path: Path, data: bytes) -> None:
    with open(path, "xb") as fh:
        fh.write(data)


def write_source(spec: dict, root: Path) -> Path:
    """root 아래에 수집기 형식 원천 폴더(manifest.json, raw/, snapshot.sqlite, snapshot_hash.json)를 새로 만든다."""
    requests, answers = plan_answers(spec)
    fixed = spec["generated_at"]
    root = Path(root)
    if (root / SNAPSHOT_ID).exists():
        raise FileExistsError(f"원천 폴더 {SNAPSHOT_ID}가 이미 있다")
    root.mkdir(parents=True, exist_ok=True)
    with _collector_at(root, fixed):
        folder, con = ingest.open_snapshot(SNAPSHOT_ID, spec["source_kind"])
        try:
            _write_new(folder / build.MANIFEST_FILE, _json_bytes(
                {"snapshot_id": SNAPSHOT_ID, "generated_at": fixed, "config": spec["collection_plan"],
                 "requests": requests}))
            for request in requests:
                answer = answers[request["request_id"]]
                if answer == NOT_COLLECTED:
                    continue  # 수신 기록이 없다 → 스냅샷 빌드가 NOT_COLLECTED 행을 만든다
                result = FAILED_RESULT if answer == FAILED else {**OK_RESULT, "raw": response_xml(answer)}
                ingest.store_result(folder, con, SNAPSHOT_ID, request["endpoint"], request["params"], result,
                                    request["months"])
            for key, value in (("last_collect_at", fixed), ("precision_rule", PRECISION_RULE),
                               ("source_url", json.dumps(SOURCE_URL, ensure_ascii=False))):
                con.execute("INSERT OR REPLACE INTO snapshot_meta(key, value) VALUES(?, ?)", (key, value))
            con.commit()
        finally:
            con.close()
    raw_sha256, raw_files = build.raw_combined_sha256(folder / build.RAW_DIR)
    _write_new(folder / build.HASH_FILE, _json_bytes({"snapshot_id": SNAPSHOT_ID, "raw_files": raw_files,
                                                      "raw_combined_sha256": raw_sha256, "method": HASH_METHOD}))
    return folder


# ----------------------------------------------------------------------------- 합성 비교국 표
def peer_group_rows(spec: dict, source_folder: Path) -> list[list]:
    """원천의 기준연도 OBSERVED 부모 HS6 행 수입금액 합으로 g0 규칙 비교국 표 행(계약 §2.3.6 필드 순서)을 만든다."""
    plan, peer = spec["collection_plan"], spec["peer_group"]
    year, k = str(peer["source_year"]), peer["k"]
    partners, hs4 = list(plan["partners"]), plan["hs4_scan"][0]
    con = build.open_read_only(Path(source_folder) / build.COLLECTOR_DB)
    try:
        scans = {rid for rid, endpoint, params in con.execute(
            "SELECT request_id, endpoint, params_json FROM collection_receipt")
            if endpoint == "nitemtrade" and json.loads(params).get("hsSgn") == hs4}
        sums: dict[tuple, int] = {}
        for rid, partner, hs6, month, amount in con.execute(
                "SELECT request_id, partner_code, hs_code, month, amount_usd FROM observation WHERE flow = 'import' "
                "AND hs_level = 6 AND observation_status = ?", (types.OBSERVED,)):
            if rid in scans and hs6 in plan["hs6"] and types.MONTH_RE.fullmatch(month) and month.startswith(year):
                sums[(hs6, partner)] = sums.get((hs6, partner), 0) + amount
    finally:
        con.close()
    raw_sha256, _ = build.raw_combined_sha256(Path(source_folder) / build.RAW_DIR)
    params_hash = hashlib.sha256(json.dumps({"candidates": sorted(partners), "k": k, "source_year": peer["source_year"]},
                                            sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"))
    rows = []
    for hs6 in sorted(plan["hs6"]):
        for entity in sorted(partners):
            ranked = sorted((p for p in partners if p != entity), key=lambda p: (-sums.get((hs6, p), 0), p))
            for rank, peer_id in enumerate(ranked[:k], start=1):
                values = {"entity_type": types.PEER_ENTITY_TYPE, "entity_id": entity,
                          "entity_namespace": types.PARTNER_NAMESPACE, "baci_country_code": None, "scope_type": "hs6",
                          "scope_id": hs6, "peer_rank": rank, "peer_id": peer_id, "similarity": None,
                          "community_id": None, "method": peer["method"], "grouping_version": peer["grouping_version"],
                          "params_hash": params_hash.hexdigest(), "source_version": SNAPSHOT_ID,
                          "source_year": peer["source_year"], "input_sha256": raw_sha256,
                          "generated_at": spec["generated_at"]}
                rows.append([values[key] for key in types.PEER_GROUP_KEYS])
    return rows


def peer_group_csv(rows: list[list]) -> bytes:
    """비교국 표 CSV(머리줄 = 계약 §2.3.6 필드 17개, LF, 필요할 때만 인용, null은 따옴표 없는 null)."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(types.PEER_GROUP_KEYS)
    writer.writerows(["null" if value is None else value for value in row] for row in rows)
    return buffer.getvalue().encode("utf-8")


# ----------------------------------------------------------------------------- 빌드·검증·요약
def generate(spec: dict, run_dir: Path, stamp: str) -> dict:
    """run_dir 안에 원천(`{도메인명}-{stamp}/` 폴더)·합성 비교국 표·스냅샷 빌드를 만들고 검증한다."""
    run_dir = Path(run_dir)
    work = run_dir / f"{DOMAIN}-{stamp}"
    work.mkdir()
    folder = write_source(spec, work)
    csv_path = work / PEER_GROUP_FILE
    _write_new(csv_path, peer_group_csv(peer_group_rows(spec, folder)))
    promotion = {"policy_version": None, "confirmed_no_trade": {"rule": spec["promotion"]["rule"]}}
    record = build.build_snapshot(SNAPSHOT_ID, out_dir=run_dir, stamp=stamp, source_dir=folder, policy=promotion,
                                  peer_group_files=[csv_path])
    build_file = run_dir / f"{build.DOMAIN}-{stamp}.sqlite"
    report = verify.verify_snapshot(SNAPSHOT_ID, build_file=build_file, source_dir=folder, check_raw=True,
                                    peer_group_files=[csv_path])
    return {"source": folder, "peer_group_csv": csv_path, "build_file": build_file, "record": record,
            "verify": report}


def case_list(spec: dict) -> list[dict]:
    """사례 이름표와 사례 식별자(단위 P2 형식 `{hs6}-{partner}-{month}`)."""
    return [{"label": case["label"], "case_id": f"{case['hs6']}-{case['partner']}-{case['month']}",
             "hs6": case["hs6"], "partner": case["partner"], "month": case["month"],
             "baseline_month": case["baseline_month"]} for case in spec["cases"]]


def summary(spec: dict, record: dict, report: dict) -> dict:
    """시각·경로가 없는 결정적 요약."""
    return {"snapshot_id": record["snapshot_id"], "schema_version": record["schema_version"],
            "source_kind": spec["source_kind"], "raw_sha256": record["raw_sha256"],
            "normalized_sha256": record["normalized_sha256"], "row_counts": record["row_counts"],
            "import_observation_status": report["counts"].get("import_observation_status", {}),
            "confirmed_no_trade_rule": record["confirmed_no_trade_rule"],
            "confirmed_no_trade_rows": record["confirmed_no_trade_rows"],
            "peer_group_files": record["peer_group_files"], "verify_ok": report["ok"],
            "failed_checks": [c["name"] for c in report["checks"] if c["ok"] is False], "cases": case_list(spec)}


def _spec_from_input(inp: object) -> dict:
    if inp is None:
        return load_spec()[0]
    if not isinstance(inp, dict) or set(inp) not in ({"spec_file"}, {"spec"}):
        raise ValueError('입력은 {"spec_file": 저장소 루트 기준 경로} 또는 {"spec": 생성 규칙 객체}다')
    if "spec" in inp:
        return parse_spec(inp["spec"])
    path = Path(inp["spec_file"])
    return load_spec(path if path.is_absolute() else REPO_ROOT / path)[0]


def run(inp: object) -> object:
    """진입 함수. 생성 규칙 → 임시 폴더에서 만든 `controlled_fixture_v0`의 결정적 요약(JSON 객체)."""
    spec = _spec_from_input(inp)
    with tempfile.TemporaryDirectory() as tmp:
        generated = generate(spec, Path(tmp), _stamp(spec["generated_at"]))
        return summary(spec, generated["record"], generated["verify"])


# ----------------------------------------------------------------------------- 정본 자리 채우기
def _reserve_run_dir(outputs: Path, clock=None) -> tuple[Path, str]:
    """outputs/snapshot_fixture-{시각}/을 이미 있으면 실패하는 방식으로 만든다(자료 계약 §10.3 N8)."""
    now = (clock or (lambda: datetime.now(types.KST)))()
    stamp = now.astimezone(types.KST).strftime("%y%m%d%H%M%S")
    outputs.mkdir(parents=True, exist_ok=True)
    run_dir = outputs / f"{DOMAIN}-{stamp}"
    os.mkdir(run_dir)  # 같은 초에 두 번 부르면 FileExistsError. 다음 초에 다시 부른다
    if (outputs / "sealed" / run_dir.name).exists():
        os.rmdir(run_dir)
        raise FileExistsError(f"outputs/sealed/{run_dir.name}이 있다. 다음 초에 다시 부른다")
    return run_dir, stamp


def _copy_new(source: Path, target: Path) -> None:
    with open(source, "rb") as src, open(target, "xb") as dst:
        while chunk := src.read(1 << 20):
            dst.write(chunk)
        dst.flush()
        os.fsync(dst.fileno())


def _same_build(path: Path, normalized: str) -> bool:
    try:
        return build.file_normalized_sha256(path) == normalized
    except (build.BuildError, sqlite3.Error):
        return False


def _collector_rows(path: Path) -> dict | None:
    """수집기 SQLite에서 스냅샷 빌드가 읽는 표(수신 기록·관측·메타)의 행. 읽지 못하면 None."""
    try:
        con = build.open_read_only(path)
    except (build.BuildError, sqlite3.Error):
        return None
    try:
        return {table: con.execute(f'SELECT * FROM "{table}" ORDER BY rowid').fetchall()
                for table in ("collection_receipt", "observation", "snapshot_meta")}
    except sqlite3.Error:
        return None
    finally:
        con.close()


def _record_differences(path: Path, record: dict) -> list[str]:
    """정본 빌드 기록에서 다시 만든 기록과 다른 키(시각·옮긴 파일 이름은 보지 않는다)."""
    try:
        committed = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return ["JSON이 아니다"]
    differ = [key for key in RECORD_KEYS if committed.get(key) != record[key]]
    return differ + (["build_file"] if committed.get("build_file") != build.BUILD_FILE else [])


def materialize(repo_root: Path | None = None, *, clock=None) -> dict:
    """정본 자리(`data/snapshots/controlled_fixture_v0/`와 합성 비교국 표)를 채우고 검증한 요약을 돌려준다.

    repo_root가 없으면 이 저장소다. 생성 규칙은 `{repo_root}/data/snapshots/controlled_fixture_v0/fixture_spec.json`이다.
    먼저 이미 있는 파일을 모두 대조하고(텍스트는 바이트, 수집기 SQLite는 수신 기록·관측·메타 행, 빌드 SQLite는
    normalized_sha256, 빌드 기록은 기록 키. 하나라도 다르면 아무것도 쓰지 않고 FixtureError), 그다음 없는 파일만 이미
    있으면 실패하는 방식으로 만든다(덮지 않는다).
    요약은 `outputs/snapshot_fixture-{시각}/snapshot_fixture-{시각}.json`에도 쓴다.
    """
    root = Path(REPO_ROOT if repo_root is None else repo_root)
    spec, spec_bytes = load_spec(spec_path(root))
    run_dir, stamp = _reserve_run_dir(root / "outputs", clock)
    generated = generate(spec, run_dir, stamp)
    record, report = generated["record"], generated["verify"]
    if not report["ok"]:
        failed = [c["name"] for c in report["checks"] if c["ok"] is False]
        raise FixtureError(f"다시 만든 빌드가 단위 S3 검증을 통과하지 못했다({', '.join(failed)})")
    target = root.joinpath(*SNAPSHOTS_DIR, SNAPSHOT_ID)
    reference = root.joinpath(*REFERENCE_DIR)
    source, shown = generated["source"], f"data/snapshots/{SNAPSHOT_ID}"
    raw_names = sorted(p.name for p in (source / build.RAW_DIR).glob("*.xml"))
    texts = [(target / SPEC_FILE, spec_bytes, f"{shown}/{SPEC_FILE}")]
    texts += [(target / name, (source / name).read_bytes(), f"{shown}/{name}")
              for name in (build.MANIFEST_FILE, build.HASH_FILE)]
    texts.append((reference / PEER_GROUP_FILE, generated["peer_group_csv"].read_bytes(),
                  f"data/reference/{PEER_GROUP_FILE}"))
    raws = [(target / build.RAW_DIR / name, (source / build.RAW_DIR / name).read_bytes()) for name in raw_names]
    canonical, record_path = target / build.BUILD_FILE, target / build.BUILD_RECORD
    # 1단계: 이미 있는 것을 모두 대조한다(쓰기 전에 멈출 곳을 다 찾는다)
    problems = [f"{name}이 다시 만든 것과 다르다" for path, data, name in texts
                if path.exists() and path.read_bytes() != data]
    problems += [f"{shown}/raw/{path.name}이 다시 만든 것과 다르다" for path, data in raws
                 if path.exists() and path.read_bytes() != data]
    extra = {p.name for p in (target / build.RAW_DIR).glob("*.xml")} - set(raw_names)
    if extra:
        problems.append(f"{shown}/raw/에 다시 만든 것에 없는 xml이 {len(extra)}개 있다")
    collector = target / build.COLLECTOR_DB
    if collector.exists() and _collector_rows(collector) != _collector_rows(source / build.COLLECTOR_DB):
        problems.append(f"{shown}/{build.COLLECTOR_DB}의 수신 기록·관측·메타 행이 다시 만든 것과 다르다")
    if canonical.exists() and not _same_build(canonical, record["normalized_sha256"]):
        problems.append(f"{shown}/{build.BUILD_FILE}의 normalized_sha256이 다시 만든 빌드와 다르다")
    differ = _record_differences(record_path, record) if record_path.exists() else []
    if differ:
        problems.append(f"{shown}/{build.BUILD_RECORD}이 다시 만든 빌드 기록과 다르다({', '.join(differ)})")
    if problems:
        raise FixtureError(f"정본 자리를 덮지 않고 멈춘다: {'; '.join(problems)}")
    # 2단계: 없는 것만 만든다(이미 있으면 실패하는 방식)
    created: list[str] = []
    for path, data, name in texts:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            _write_new(path, data)
            created.append(name)
    (target / build.RAW_DIR).mkdir(parents=True, exist_ok=True)
    missing_raw = [(path, data) for path, data in raws if not path.exists()]
    for path, data in missing_raw:
        _write_new(path, data)
    if missing_raw:
        created.append(f"{shown}/raw/*.xml({len(missing_raw)})")
    for source_file, path in ((source / build.COLLECTOR_DB, target / build.COLLECTOR_DB),
                              (generated["build_file"], canonical)):
        if not path.exists():
            _copy_new(source_file, path)
            created.append(f"{shown}/{path.name}")
    if not record_path.exists():
        installed = {**record, "build_file": build.BUILD_FILE, "installed_from": generated["build_file"].name,
                     "installed_at": datetime.now(types.KST).isoformat(timespec="seconds")}
        _write_new(record_path, _json_bytes(installed))
        created.append(f"{shown}/{build.BUILD_RECORD}")
    # 3단계: 정본 자리 전체를 단위 S3로 검증한다(raw 대조 켬, 빌드 기록과 normalized_sha256 대조)
    final = verify.verify_snapshot(SNAPSHOT_ID, build_file=canonical, source_dir=target, check_raw=True,
                                   peer_group_files=[reference / PEER_GROUP_FILE])
    if not final["ok"] or final["recorded_normalized_sha256"] != record["normalized_sha256"]:
        failed = [c["name"] for c in final["checks"] if c["ok"] is False]
        raise FixtureError(f"정본 자리의 스냅샷이 단위 S3 검증을 통과하지 못했다({', '.join(failed)})")
    out = {**summary(spec, record, final), "run_id": run_dir.name, "created": created}
    _write_new(run_dir / f"{DOMAIN}-{stamp}.json", _json_bytes(out))
    print(f"{SNAPSHOT_ID}: 단위 S3 검증 통과, normalized_sha256 {record['normalized_sha256'][:12]}…, "
          f"새로 쓴 파일 {len(created)}건, 실행 폴더 outputs/{run_dir.name}/")
    return out
