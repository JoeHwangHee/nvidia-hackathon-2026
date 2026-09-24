"""단위 V5 실자료 분할.

단위 ID: V5
도메인명: datagen_split
소유: D
입력: 스냅샷 ID, 시계열 키 목록(hs6·partner), seed, 비율(real_dev:real_sealed)
출력: `real_dev`·`real_sealed` 시계열 키 목록(배정 기록)
허용 import: 표준 라이브러리

스냅샷의 품목(HS6)×상대국 시계열을 개발 묶음 `real_dev`와 봉인 묶음 `real_sealed`로 나눈다(정본: docs/plan/UNITS.md
§3.11, docs/rules/PARALLEL_DEV_RULES.md §7, docs/rules/DATA_CONTRACT_V1.md §4.2). 시계열 키와 seed만 쓰고 실자료 값
(원자료·SQLite)은 읽지 않는다. 그래서 허용 import를 표준 라이브러리로 좁혔다(S0 뼈대의 tradesentry.contract·
tradesentry.dal·eval.datagen을 뺐다. 자료 접근층을 import하면 경계 시험이 막는다). 같은 입력이면 늘 같은 출력이고,
입력 목록의 순서와 관계없다.

입력(JSON 객체. 키는 아래 넷뿐이다)
- snapshot_id: 스냅샷 ID. 영문 소문자로 시작하고 영문 소문자·숫자·밑줄만 쓴다.
- seed: 0 이상의 정수(bool은 받지 않는다).
- ratio: {"real_dev": 정수, "real_sealed": 정수}. 둘 다 1 이상이다.
- series: [{"hs6": 숫자 6자리 문자열, "partner": 영문 대문자 2자}, ...]. 같은 키가 두 번 나오지 않는다. 전체국가
  분모 계열(partner `ALL`)은 나누지 않으므로 받지 않는다. 두 묶음이 모두 한 개 이상이 될 만큼 있어야 한다.
  키 이름 hs6·partner는 자료 계약 case 객체(§2.3.5)의 필드 이름이다.

방법(출력의 method 값 "hs6_stratified_sha256_rank")
1. 키마다 순위 값을 만든다. 순위 값은 문자열 "{seed}:{snapshot_id}:{hs6}:{partner}"(seed는 10진수)를 UTF-8로 바꾼
   바이트의 sha256을 16진 소문자 64자로 쓴 것이다. 구분자 ":"는 형식 검사 때문에 어느 조각에도 들 수 없다. 파이썬
   random 모듈을 쓰지 않으므로 파이썬 판과 관계없이 같은 값이 나오고, 다른 도구(예: shasum -a 256)로도 다시 계산할
   수 있다.
2. 전체 개수(반올림 규칙): 키 N개 가운데 real_dev는 N × real_dev ÷ (real_dev + real_sealed)의 소수점 아래를 버린
   정수이고, 나머지는 모두 real_sealed다. 정수로만 계산한다. N = 64, 비율 1:2면 21개와 43개다.
3. HS6 층(hs6이 같은 키 무리)마다 크기에 비례해 real_dev 자리를 나눈다(최대 나머지 방식). 층 h(키 N_h개)에는 먼저
   몫 floor(n_dev × N_h ÷ N)을 주고, 남은 자리는 나머지(n_dev × N_h mod N)가 큰 층부터 한 자리씩 준다. 나머지가
   같으면 그 층에서 다음 차례(몫 + 1번째) 키의 순위 값이 작은 층이 먼저다. n_dev < N이므로 다음 차례 키는 늘 있다.
4. 층 안에서는 순위 값 오름차순(같으면 hs6, partner 순)으로 앞에서부터 자리 수만큼 real_dev, 나머지는 real_sealed다.
5. 출력 목록은 (hs6, partner) 오름차순이다.

출력: {"snapshot_id", "seed", "ratio", "method", "real_dev": [{"hs6", "partner"}, ...], "real_sealed": [...]}. 입력의
snapshot_id·seed·ratio를 그대로 옮겨 적는다. 수는 모두 정수다.

오류: 입력이 위 형식에 맞지 않으면 ValueError를 낸다. 메시지에는 입력 값을 넣지 않고 위치와 필드 이름만 적는다.

수집 설정(configs/collection_plan.json을 JSON으로 읽은 객체)에서 입력을 만드는 도우미 input_from_collection_plan도
여기 둔다. 설정의 최상위 snapshot_id와 hs6 × partners만 쓰고 _alternate·hs4_scan 같은 다른 키는 보지 않는다. 이
도우미는 입력 형식만 검사하고 분할(run)은 부르지 않는다.
"""
import hashlib
import re

METHOD = "hs6_stratified_sha256_rank"
INPUT_KEYS = frozenset({"snapshot_id", "seed", "ratio", "series"})
RATIO_KEYS = frozenset({"real_dev", "real_sealed"})
SERIES_KEYS = frozenset({"hs6", "partner"})
ALL_PARTNER = "ALL"  # 전체국가 분모 계열의 partner_code(자료 계약 §2.3.2). 나누지 않는다

SNAPSHOT_ID_RE = re.compile(r"[a-z][a-z0-9_]*")
HS6_RE = re.compile(r"[0-9]{6}")
PARTNER_RE = re.compile(r"[A-Z]{2}")


def series_digest(seed: int, snapshot_id: str, hs6: str, partner: str) -> str:
    """키 하나의 순위 값: "{seed}:{snapshot_id}:{hs6}:{partner}"의 UTF-8 바이트 sha256(16진 소문자 64자)."""
    return hashlib.sha256(f"{seed}:{snapshot_id}:{hs6}:{partner}".encode("utf-8")).hexdigest()


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _check_input(inp: object) -> tuple[str, int, int, int, list[tuple[str, str]]]:
    """입력 형식을 검사하고 (snapshot_id, seed, real_dev 몫, real_sealed 몫, 키 목록)을 돌려준다."""
    if not isinstance(inp, dict) or set(inp) != INPUT_KEYS:
        raise ValueError("입력은 snapshot_id·seed·ratio·series 네 키만 가진 JSON 객체여야 한다")
    snapshot_id = inp["snapshot_id"]
    if not isinstance(snapshot_id, str) or SNAPSHOT_ID_RE.fullmatch(snapshot_id) is None:
        raise ValueError("snapshot_id는 영문 소문자로 시작하고 영문 소문자·숫자·밑줄만 쓴 문자열이어야 한다")
    seed = inp["seed"]
    if not _is_int(seed) or seed < 0:
        raise ValueError("seed는 0 이상의 정수여야 한다(bool은 받지 않는다)")
    ratio = inp["ratio"]
    if not isinstance(ratio, dict) or set(ratio) != RATIO_KEYS:
        raise ValueError("ratio는 real_dev·real_sealed 두 키만 가진 객체여야 한다")
    dev_part, sealed_part = ratio["real_dev"], ratio["real_sealed"]
    if not (_is_int(dev_part) and _is_int(sealed_part)) or dev_part < 1 or sealed_part < 1:
        raise ValueError("ratio의 real_dev·real_sealed는 1 이상의 정수여야 한다(bool은 받지 않는다)")
    series = inp["series"]
    if not isinstance(series, list):
        raise ValueError("series는 목록이어야 한다")
    keys: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(series):
        if not isinstance(item, dict) or set(item) != SERIES_KEYS:
            raise ValueError(f"series[{index}]는 hs6·partner 두 키만 가진 객체여야 한다")
        hs6, partner = item["hs6"], item["partner"]
        if partner == ALL_PARTNER:
            raise ValueError(f"series[{index}]: 전체국가(ALL) 분모 계열은 나누지 않는다")
        if not isinstance(hs6, str) or HS6_RE.fullmatch(hs6) is None:
            raise ValueError(f"series[{index}].hs6은 숫자 6자리 문자열이어야 한다")
        if not isinstance(partner, str) or PARTNER_RE.fullmatch(partner) is None:
            raise ValueError(f"series[{index}].partner는 영문 대문자 2자 문자열이어야 한다")
        key = (hs6, partner)
        if key in seen:
            raise ValueError(f"series[{index}]: 앞에 나온 시계열 키와 같다")
        seen.add(key)
        keys.append(key)
    return snapshot_id, seed, dev_part, sealed_part, keys


def _dev_keys(snapshot_id: str, seed: int, dev_part: int, sealed_part: int,
              keys: list[tuple[str, str]]) -> set[tuple[str, str]]:
    """real_dev에 배정할 키 집합(방법 2~4)."""
    total = len(keys)
    n_dev = total * dev_part // (dev_part + sealed_part)
    if n_dev < 1 or total - n_dev < 1:
        raise ValueError("두 묶음이 모두 한 개 이상이 되려면 시계열 키가 더 있어야 한다")
    strata: dict[str, list[tuple[str, str, str]]] = {}
    for hs6, partner in keys:
        strata.setdefault(hs6, []).append((series_digest(seed, snapshot_id, hs6, partner), hs6, partner))
    for members in strata.values():
        members.sort()  # 순위 값 오름차순, 같으면 hs6·partner 순
    seats: dict[str, int] = {}
    remainders: dict[str, int] = {}
    for hs6, members in strata.items():
        seats[hs6], remainders[hs6] = divmod(n_dev * len(members), total)
    leftover = n_dev - sum(seats.values())
    # 남은 자리: 나머지가 큰 층부터. 같으면 그 층의 다음 차례 키(순위 값, hs6, partner)가 작은 층부터.
    for hs6 in sorted(strata, key=lambda h: (-remainders[h], strata[h][seats[h]]))[:leftover]:
        seats[hs6] += 1
    return {(hs6, partner) for hs6, members in strata.items() for _, _, partner in members[:seats[hs6]]}


def run(inp: object) -> object:
    """진입 함수. 입력과 출력은 머리 주석과 같다."""
    snapshot_id, seed, dev_part, sealed_part, keys = _check_input(inp)
    dev = _dev_keys(snapshot_id, seed, dev_part, sealed_part, keys)
    return {
        "snapshot_id": snapshot_id,
        "seed": seed,
        "ratio": {"real_dev": dev_part, "real_sealed": sealed_part},
        "method": METHOD,
        "real_dev": [{"hs6": hs6, "partner": partner} for hs6, partner in sorted(dev)],
        "real_sealed": [{"hs6": hs6, "partner": partner} for hs6, partner in sorted(set(keys) - dev)],
    }


def series_from_collection_plan(plan: object) -> list[dict[str, str]]:
    """수집 설정의 최상위 hs6 × partners로 시계열 키 목록을 만든다(설정에 적힌 순서, hs6 바깥 반복).

    partners에 전체국가 ALL이 있으면 오류다(분모 계열은 나누지 않는다). 키 하나하나의 형식은
    input_from_collection_plan이 검사한다.
    """
    if not isinstance(plan, dict):
        raise ValueError("수집 설정은 JSON 객체여야 한다")
    hs6_codes, partners = plan.get("hs6"), plan.get("partners")
    if not isinstance(hs6_codes, list) or not isinstance(partners, list) or not hs6_codes or not partners:
        raise ValueError("수집 설정의 hs6·partners는 비어 있지 않은 목록이어야 한다")
    if ALL_PARTNER in partners:
        raise ValueError("수집 설정의 partners에 전체국가(ALL)가 있다. 분모 계열은 나누지 않는다")
    return [{"hs6": hs6, "partner": partner} for hs6 in hs6_codes for partner in partners]


def input_from_collection_plan(plan: object, seed: int, ratio: dict[str, int]) -> dict[str, object]:
    """수집 설정에서 run의 입력을 만든다. snapshot_id와 시계열 키는 설정에서, seed와 비율은 인자에서 온다.

    입력 형식을 run과 같은 규칙으로 검사하고 돌려준다. 분할은 하지 않는다.
    """
    series = series_from_collection_plan(plan)  # plan이 JSON 객체인지 여기서 검사한다
    inp = {"snapshot_id": plan.get("snapshot_id"),
           "seed": seed,
           "ratio": dict(ratio) if isinstance(ratio, dict) else ratio,
           "series": series}
    _check_input(inp)
    return inp
