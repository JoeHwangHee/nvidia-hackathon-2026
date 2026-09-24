"""단위 K4 정책 수치 읽기.

단위 ID: K4
도메인명: contract_policy_load
소유: D
입력: `configs/policy_v1.json`(승인 전에는 개발용 `configs/policy_dev.json`)
출력: 정책 객체
허용 import: 표준 라이브러리, tradesentry.contract

정책 수치는 코드에 박지 않고 이 단위로 읽는다(병렬 개발 규칙 §1.2, 자문 명세서 §4.10). 소비자는 단위 S2(승격 규칙),
판정 정책(P 묶음, 기준값), 지표 단위 X3·X4(허용오차)다.

파일과 정책 버전 이름
- `policy_v1` → `configs/policy_v1.json`(사용자 승인 뒤, 자료 계약 §10 계획 경로 표).
- `dev-<수>.<수>`(지금은 `dev-0.1`) → `configs/policy_dev.json`(결정 D2, 2026-09-24(목) 23:09 사용자 승인. 승인 전 실행용).
- 파일 안의 `policy_version`이 부른 이름과 같아야 한다.

파일 형식(자료 계약이 키 구조를 정하지 않아 이 단위가 정했다. 두 파일이 같은 형식을 쓴다)
    {
      "schema_version": 1,                                   # §1.2 JSON의 계약 버전 표시
      "policy_version": "dev-0.1",                           # §1.3
      "thresholds": {"unit_value": 30, "share": 10},        # 탐지 기준값. 단위는 §11.2(30%는 30, 10pp는 10)
      "min_amount": null,                                    # USD. null이면 적용하지 않는다
      "min_weight": null,                                    # kg. null이면 적용하지 않는다
      "tolerance": {"amount_usd": 0, "weight_rounding_kg": 0.5},       # §11.1: 금액 정확 일치, 중량 0.5kg×(행수+1)
      "confirmed_no_trade": null                             # 승격 규칙. null이면 승격하지 않는다
    }
- 밑줄(`_`)로 시작하는 최상위 키는 설명용이라 읽고 버린다. 그 밖의 키는 모두 있어야 하고(값은 null일 수 있다), 모르는 키는
  거부한다. 수는 int나 Decimal(파일의 소수는 Decimal로 읽는다)이고 0 이상이다. float는 받지 않는다.
- `thresholds.unit_value`는 단가 변화율 `r_U`의 기준(%, 30%는 `30`), `thresholds.share`는 점유율 변화 `d_s`의 기준
  (pp, 10pp는 `10`)이다. 비교는 절댓값 이상(`>=`)이다(oracle `dev-0.1 (임계 |r_U|>=30%, |d_s|>=10pp)`). 적용은 판정
  정책(M)이 한다. 이 모양(기준값을 수 하나로 둔다)은 판정 정책 작업(MT1)이 먼저 가정한 모양에 맞췄다(오케스트레이터 알림).
- 중량 허용오차는 `weight_rounding_kg × (대조한 하위 행 수 + 1)`이다(§11.1, 수집기 WEIGHT_ROUNDING_KG와 같은 뜻).
- 승격 규칙 `confirmed_no_trade`는 null이거나 {"rule": 규칙 이름}이다. 아는 규칙 이름은 하나다.
  `ingest_verify_candidates`: 수집기 `verify`가 `confirmed_no_trade_candidates`로 나열하는 행과 같은 규칙. 수입 흐름의
  HS6 자릿수 `UNRESOLVED_ZERO` 행 가운데, 같은 상대국·HS6·월의 `OBSERVED` HS6 행이 없고, 같은 상대국·월에 같은 HS4 아래
  다른 HS6의 `OBSERVED` 행(HS4 스캔 응답)이 있는 행을 `CONFIRMED_NO_TRADE`로 바꾼다. 적용은 단위 S2가 한다.
  모르는 규칙 이름은 거부한다(조용히 넘어가지 않는다). 실제 `policy_v1`의 규칙은 DT4 ② 제안과 사용자 승인으로 정한다.
"""
import json
import re
from decimal import Decimal
from pathlib import Path

from tradesentry.contract import types

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIGS_DIR = REPO_ROOT / "configs"
POLICY_V1_FILE = "policy_v1.json"
POLICY_DEV_FILE = "policy_dev.json"
POLICY_VERSION_RE = re.compile(r"policy_v[0-9]+|dev-[0-9]+\.[0-9]+")  # fullmatch로 쓴다
DEV_VERSION_RE = re.compile(r"dev-[0-9]+\.[0-9]+")
SIGNAL_METRICS = {"unit_value": "r_U", "share": "d_s"}  # 신호와 탐지 지표(§6.1). 기준값 단위는 그 지표의 단위(§11.2)
TOLERANCE_KEYS = ("amount_usd", "weight_rounding_kg")
PROMOTION_RULES = ("ingest_verify_candidates",)
POLICY_KEYS = ("schema_version", "policy_version", "thresholds", "min_amount", "min_weight", "tolerance",
               "confirmed_no_trade")


class PolicyError(ValueError):
    """정책 파일이 형식에 맞지 않거나 부른 버전과 다르다."""


def _number(value: object, where: str) -> int | Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, Decimal)):
        raise PolicyError(f"{where}: 수(int·Decimal)여야 한다(float는 받지 않는다)")
    if isinstance(value, Decimal) and not value.is_finite():
        raise PolicyError(f"{where}: 유한한 수여야 한다")
    if value < 0:
        raise PolicyError(f"{where}: 0 이상이어야 한다")
    return value


def _exact_keys(obj: object, keys: tuple[str, ...], where: str) -> dict:
    if not isinstance(obj, dict):
        raise PolicyError(f"{where}: 객체여야 한다")
    if set(obj) != set(keys):
        raise PolicyError(f"{where}: 키는 {', '.join(keys)}여야 한다")
    return obj


def parse_policy(document: object) -> dict:
    """정책 문서(파일 내용) → 검사한 정책 객체(키는 POLICY_KEYS 순서, `_` 키는 뺀다). 맞지 않으면 PolicyError."""
    if not isinstance(document, dict):
        raise PolicyError("정책 문서는 객체여야 한다")
    body = {k: v for k, v in document.items() if not (isinstance(k, str) and k.startswith("_"))}
    _exact_keys(body, POLICY_KEYS, "정책 문서")
    schema = body["schema_version"]
    if isinstance(schema, bool) or not isinstance(schema, int) or schema != types.SCHEMA_VERSION:
        raise PolicyError(f"schema_version: 정수 {types.SCHEMA_VERSION}이어야 한다")
    version = body["policy_version"]
    if not isinstance(version, str) or not POLICY_VERSION_RE.fullmatch(version):
        raise PolicyError("policy_version: policy_v<수> 또는 dev-<수>.<수> 형식이어야 한다")
    thresholds = _exact_keys(body["thresholds"], types.SIGNALS, "thresholds")
    parsed_thresholds = {signal: _number(thresholds[signal], f"thresholds.{signal}") for signal in types.SIGNALS}
    tolerance = _exact_keys(body["tolerance"], TOLERANCE_KEYS, "tolerance")
    promotion = body["confirmed_no_trade"]
    if promotion is not None:
        _exact_keys(promotion, ("rule",), "confirmed_no_trade")
        if promotion["rule"] not in PROMOTION_RULES:
            raise PolicyError(f"confirmed_no_trade.rule: 아는 규칙({', '.join(PROMOTION_RULES)})이 아니다")
        promotion = {"rule": promotion["rule"]}
    return {
        "schema_version": types.SCHEMA_VERSION,
        "policy_version": version,
        "thresholds": parsed_thresholds,
        "min_amount": None if body["min_amount"] is None else _number(body["min_amount"], "min_amount"),
        "min_weight": None if body["min_weight"] is None else _number(body["min_weight"], "min_weight"),
        "tolerance": {key: _number(tolerance[key], f"tolerance.{key}") for key in TOLERANCE_KEYS},
        "confirmed_no_trade": promotion,
    }


def policy_path(policy_version: str, *, configs_dir: Path | None = None) -> Path:
    """정책 버전 이름 → 정책 파일 경로. 경로 표에 없는 이름이면 PolicyError."""
    base = CONFIGS_DIR if configs_dir is None else Path(configs_dir)
    if policy_version == types.POLICY_V1:
        return base / POLICY_V1_FILE
    if isinstance(policy_version, str) and DEV_VERSION_RE.fullmatch(policy_version):
        return base / POLICY_DEV_FILE
    raise PolicyError(f"정책 파일이 정해지지 않은 정책 버전 이름이다: {policy_version!r}")


def load_policy(policy_version: str, *, configs_dir: Path | None = None) -> dict:
    """정책 버전 이름으로 정책 파일을 읽어 검사한 정책 객체를 돌려준다. 파일의 policy_version이 다르면 PolicyError."""
    path = policy_path(policy_version, configs_dir=configs_dir)
    try:
        document = json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)
    except FileNotFoundError as exc:
        raise PolicyError(f"정책 파일이 없다: configs/{path.name}") from exc
    except ValueError as exc:
        raise PolicyError(f"정책 파일이 JSON이 아니다: configs/{path.name}") from exc
    policy = parse_policy(document)
    if policy["policy_version"] != policy_version:
        raise PolicyError(f"configs/{path.name}의 policy_version이 {policy_version}이 아니다")
    return policy


def run(inp: object) -> object:
    """진입 함수. 정책 문서(`configs/policy_*.json` 내용) → 검사한 정책 객체."""
    return parse_policy(inp)
