"""단위 P2 사례 만들기.

단위 ID: P2
도메인명: policy_case_build
소유: M
입력: 발동·분할 기록과 묶음 선택(`real_dev`/`real_sealed`)
출력: 사례(`case_id`·scope). 지정한 묶음의 시계열로 제한(수단은 S0 자문 Q18, 고르는 방법은 병렬 개발 규칙 §7.2의 5)
허용 import: 표준 라이브러리, tradesentry.contract, tradesentry.dal, tradesentry.metrics, tradesentry.policy

신호 발동(단위 P1) 결과에서 신호가 하나 이상 발동한 계열·월마다 사례 객체(자료 계약 docs/rules/DATA_CONTRACT_V1.md
§2.3.5)를 만든다. 사례는 코드가 만들고 모델은 만들지 않는다.

묶음 제한(실자료 스냅샷, `source_kind`=`real`)
- 묶음(`dataset`)을 `real_dev`나 `real_sealed` 중 하나로 반드시 지정한다. 기본값을 두지 않는다.
- 분할 기록은 파싱한 계열 배정 목록(`series_assignment`)으로 받는다. 분할 기록 파일의 형식은 로드맵 DT4 ①이 정한다.
- 지정한 묶음의 계열만 사례와 데이터 품질 목록에 남긴다. 다른 묶음의 행은 건수도 남기지 않고 버린다(다른 묶음의
  경보 규모가 출력에 드러나지 않게). 배정에 없는 계열이 오면 추측하지 않고 오류로 끝낸다.
- 합성 스냅샷(`controlled`)은 분할이 없으므로 묶음과 배정을 받지 않는다.
- 개발 실행에서는 `real_sealed` 계열로 경보를 뽑아 보지 않는다(병렬 개발 규칙 §7.2의 5). 그래서 조립(AS1)은
  지표 계산(X1·X2)과 신호 발동(P1) 앞에서 지정한 묶음의 계열로 반드시 좁혀야 한다. 개발 중에 v2 64개 계열 전체로
  P1이나 `detect`를 돌리지 않는다(공통 실행기로 단위만 돌릴 때도 같다). 이 단위의 제한은 마지막 방어선이다.

사례 식별자(`case_id`): `{hs6}-{partner}-{month}`(예: `850450-CN-202401`). 자료 계약 §4.5는 `case_id` 문자열 형식을
정하지 않았다. 품목·상대국·비교월만 담아 기대 상태를 넣지 않고, 식별자만으로 사례를 다시 만들 수 있다(자문 명세서
Q18의 6). CLI 사례 인자 형식(단위 F1)과 맞추는 일은 Q18 결정으로 남아 있다.

입력(JSON 객체): `snapshot_id`, `source_kind`(`real`/`controlled`), `detection`(단위 P1 출력 그대로), 실자료면
`dataset`과 `series_assignment`([{`hs6`, `partner`, `dataset`}]).

출력(JSON 객체): `snapshot_id`, `dataset`(합성은 null), `policy_version`, `cases`(사례 객체에 `scope`를 더한 것.
`scope`는 사례가 정하는 조회 범위의 바탕인 {`hs6`, `partner`, `month`, `baseline_month`}이고, 비교국·HS10 하위품목
범위는 도구 단위가 정한다), `data_quality`(P1의 데이터 품질 목록 가운데 지정한 묶음의 행).
"""
import re

from tradesentry.policy.required_evidence import REAL_DATASETS, SIGNAL_CODES, SOURCE_KINDS, TRIGGERED, check_signals
from tradesentry.policy.trigger import HS6_RE, MONTH_RE, PARTNER_RE, baseline_of

SNAPSHOT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_]*$")
CASE_ID_RE = re.compile(r"^([0-9]{6})-([A-Z]{2})-([0-9]{4}(?:0[1-9]|1[0-2]))$")
DETECTION_KEYS = {"policy_version", "triggers", "data_quality"}
INPUT_KEYS = {"snapshot_id", "source_kind", "detection", "dataset", "series_assignment"}


def case_id_for(hs6: str, partner: str, month: str) -> str:
    """사례 식별자 `{hs6}-{partner}-{month}`를 만든다."""
    case_id = f"{hs6}-{partner}-{month}"
    if not CASE_ID_RE.match(case_id):
        raise ValueError("사례 식별자의 재료(hs6 6자리, 상대국 2자리, 비교월 YYYYMM)가 형식에 맞지 않는다")
    return case_id


def parse_case_id(case_id: object) -> dict[str, str]:
    """사례 식별자를 {hs6, partner, month, baseline_month}로 되돌린다. 형식이 다르면 오류다."""
    match = CASE_ID_RE.match(case_id) if isinstance(case_id, str) else None
    if match is None:
        raise ValueError("사례 식별자는 {hs6}-{partner}-{month} 형식이어야 한다")
    hs6, partner, month = match.groups()
    return {"hs6": hs6, "partner": partner, "month": month, "baseline_month": baseline_of(month)}


def _series_key(item: object, where: str) -> tuple[str, str]:
    if not isinstance(item, dict):
        raise ValueError(f"{where}는 객체여야 한다")
    hs6, partner = item.get("hs6"), item.get("partner")
    if not isinstance(hs6, str) or not HS6_RE.match(hs6) or not isinstance(partner, str) \
            or not PARTNER_RE.match(partner):
        raise ValueError(f"{where}의 hs6·partner 형식이 맞지 않는다")
    return hs6, partner


def _assignment(raw: object) -> dict[tuple[str, str], str]:
    if not isinstance(raw, list) or not raw:
        raise ValueError("실자료 스냅샷은 series_assignment(계열 배정 목록)가 있어야 한다")
    table: dict[tuple[str, str], str] = {}
    for index, item in enumerate(raw):
        key = _series_key(item, f"series_assignment[{index}]")
        if set(item) != {"hs6", "partner", "dataset"} or item["dataset"] not in REAL_DATASETS:
            raise ValueError(f"series_assignment[{index}]는 hs6·partner·dataset({list(REAL_DATASETS)}) 객체여야 한다")
        if key in table:
            raise ValueError(f"series_assignment[{index}]: 같은 계열이 두 번 배정됐다")
        table[key] = item["dataset"]
    return table


def _selected(key: tuple[str, str], table: dict | None, dataset: str | None, where: str) -> bool:
    """이 계열을 남기는가. 합성 스냅샷(table이 None)은 모두 남긴다."""
    if table is None:
        return True
    if key not in table:
        raise ValueError(f"{where}의 계열이 series_assignment에 없다")
    return table[key] == dataset


def run(inp: object) -> object:
    """발동한 계열·월로 사례를 만들고, 실자료면 지정한 묶음의 계열로 제한한다."""
    if not isinstance(inp, dict) or not {"snapshot_id", "source_kind", "detection"} <= set(inp) <= INPUT_KEYS:
        raise ValueError("입력은 snapshot_id·source_kind·detection(실자료면 dataset·series_assignment도) 객체여야 한다")
    snapshot_id, source_kind = inp["snapshot_id"], inp["source_kind"]
    if not isinstance(snapshot_id, str) or not SNAPSHOT_ID_RE.match(snapshot_id):
        raise ValueError("snapshot_id는 영문 소문자·숫자·밑줄로 된 스냅샷 ID여야 한다")
    if source_kind not in SOURCE_KINDS:
        raise ValueError(f"source_kind는 {list(SOURCE_KINDS)} 중 하나여야 한다")
    dataset, raw_assignment = inp.get("dataset"), inp.get("series_assignment")
    if source_kind == "real":
        if dataset not in REAL_DATASETS:
            raise ValueError(f"실자료 스냅샷은 dataset을 {list(REAL_DATASETS)} 중 하나로 지정해야 한다")
        table = _assignment(raw_assignment)
    else:
        if dataset is not None or raw_assignment is not None:
            raise ValueError("합성 스냅샷에는 dataset·series_assignment를 주지 않는다")
        table = None
    detection = inp["detection"]
    if not isinstance(detection, dict) or set(detection) != DETECTION_KEYS:
        raise ValueError("detection은 신호 발동(단위 P1)의 출력 그대로여야 한다")
    policy_version = detection["policy_version"]
    if not isinstance(policy_version, str) or not policy_version:
        raise ValueError("detection.policy_version은 비어 있지 않은 문자열이어야 한다")
    if not isinstance(detection["triggers"], list) or not isinstance(detection["data_quality"], list):
        raise ValueError("detection.triggers와 detection.data_quality는 목록이어야 한다")

    cases, seen = [], set()
    for index, row in enumerate(detection["triggers"]):
        where = f"detection.triggers[{index}]"
        hs6, partner = _series_key(row, where)
        month, baseline = row.get("month"), row.get("baseline_month")
        if not isinstance(month, str) or not MONTH_RE.match(month) or baseline != baseline_of(month):
            raise ValueError(f"{where}의 month·baseline_month가 맞지 않는다")
        signals = check_signals(row.get("signals"))
        case_id = case_id_for(hs6, partner, month)
        if case_id in seen:
            raise ValueError(f"{where}: 같은 계열·월이 두 번 왔다")
        seen.add(case_id)
        if not _selected((hs6, partner), table, dataset, where):
            continue
        if not any(signals[code] == TRIGGERED for code in SIGNAL_CODES):
            continue
        scope = {"hs6": hs6, "partner": partner, "month": month, "baseline_month": baseline}
        cases.append({"case_id": case_id, **scope, "signals": signals, "snapshot_id": snapshot_id,
                      "policy_version": policy_version, "scope": dict(scope)})
    quality = []
    for index, row in enumerate(detection["data_quality"]):
        key = _series_key(row, f"detection.data_quality[{index}]")
        if _selected(key, table, dataset, f"detection.data_quality[{index}]"):
            quality.append(dict(row))
    cases.sort(key=lambda c: c["case_id"])
    return {"snapshot_id": snapshot_id, "dataset": dataset, "policy_version": policy_version, "cases": cases,
            "data_quality": quality}
