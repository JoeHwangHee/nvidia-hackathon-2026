"""구성 단위 I9(프롬프트·모델 설정, configs/model/) 검사. 진입 함수가 없는 구성 단위라 골든 쌍 대신 이 시험으로 본다.

- model.json은 소수를 Decimal로 읽는다(float 없음). 키 값은 없고 키 환경변수의 이름만 있다.
- 한도는 개발 플랜 §6.6·자료 계약 §8.1의 조정값과 같다(도구 8회 = 기본 5 + 재조회 2 + 최종 검증 1, 수정 1회,
  모델 요청 10회, 300초, 누적 토큰 32,000, 5xx 재전송 요청당 3회). 바꾸려면 공용 약속 절차를 거친다.
- 프롬프트 파일이 있고, 금지 낱말(부정문으로도 쓰지 않음)·산문 숫자·증감 규칙과 JSON 초안 형식을 담는다. 금지 낱말은
  "금지 낱말:" 줄에만 나온다(프롬프트 파일 넷의 나머지 글이 그 낱말을 되풀이해 모델이 따라 쓰지 않게).
- 금지 낱말 목록은 검증기(단위 R3)의 금지 문구 목록과 항목마다 한 번씩 같다. 검증기가 아직 병합되지 않은 동안은 MT3
  브랜치 커밋 b5948c3의 목록(PINNED_*, 한국어 62개와 영문 앞부분 9개)과 맞추고, 병합되면 실제 목록과도 맞춘다(목록이
  바뀌면 이 시험이 실패해 프롬프트를 함께 고치게 한다).
"""
import json
import re
import unittest
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "configs" / "model"
PROMPT_FILES = ("investigator.txt", "critic.txt", "claims_template.txt", "claims_freeform.txt")

# 검증기 금지 문구 목록의 사본(MT3 브랜치 b5948c3 src/tradesentry/validator/validate.py의 FORBIDDEN_PHRASES·
# FORBIDDEN_LATIN). 검증기가 병합되면 아래 병합 뒤 시험이 실제 목록과 이 사본을 함께 맞춘다.
PINNED_PHRASES = (
    "부정 거래", "부정 수입", "부정 수출", "부정 행위", "부정 가능성", "부정 의혹", "부정 여부", "부정의 증거", "부정 소지",
    "부정 신고", "부정한 방법", "사기 거래", "사기 행위", "불법", "위법", "탈법", "편법", "탈세", "탈루", "밀수", "범죄",
    "혐의", "관세법 위반", "법 위반", "법률 위반", "관세 포탈", "관세 회피", "원산지 조작", "원산지를 조작", "원산지 세탁",
    "원산지 위장", "원산지 둔갑", "원산지 속임", "원산지 우회", "원산지 회피", "원산지를 바꿔", "원산지를 바꾼",
    "원산지 판정", "원산지 판단", "우회 수입", "우회 수출", "우회 환적", "환적", "제3국을 거쳐", "제3국 경유",
    "제3국을 경유", "저가 신고", "과소 신고", "허위 신고", "가격 조작", "개별 거래가격", "개별 거래의 가격", "덤핑",
    "통관 보류", "추징", "적발", "압수", "처벌", "고발", "정상 확정", "정상으로 확정", "정상 거래")
PINNED_LATIN = ("fraud", "illegal", "smuggl", "circumvent", "dumping", "evasion", "under-invoic", "transship",
                "misdeclar")


def load() -> dict:
    return json.loads((MODEL_DIR / "model.json").read_text(encoding="utf-8"), parse_float=Decimal)


def walk(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)
    else:
        yield value


def forbidden_line(text: str) -> tuple[list[str], str]:
    """프롬프트의 "금지 낱말:" 줄을 낱말 목록으로 나누고, 그 줄을 뺀 나머지 글을 돌려준다."""
    listed, rest = [], []
    for line in text.splitlines():
        if line.strip().startswith("금지 낱말:"):
            listed += [w.strip() for w in line.split(":", 1)[1].split(",") if w.strip()]
        else:
            rest.append(line)
    return listed, "\n".join(rest)


class ModelConfigTest(unittest.TestCase):
    def test_settings_shape_and_no_key_values(self):
        cfg = load()
        self.assertEqual(cfg["model"], "nvidia/nemotron-3-super-120b-a12b")
        self.assertTrue(cfg["endpoint"].startswith("https://integrate.api.nvidia.com/"))
        self.assertRegex(cfg["api_key_env"], r"^[A-Z][A-Z0-9_]*$")  # 변수 이름만 둔다
        self.assertFalse(any(isinstance(v, float) for v in walk(cfg)))
        self.assertIsInstance(cfg["request"]["temperature"], Decimal)
        self.assertIs(cfg["request"]["enable_thinking"], False)
        # model-0.2: 도구 없는 조사자 초안 요청에 response_format json_object(실측 뒤 켬, 결정 기록 ⑯)
        self.assertEqual((cfg["config_version"], cfg["request"]["structured_output"]), ("model-0.2", "json_object"))
        for value in walk(cfg):
            if isinstance(value, str):
                self.assertNotRegex(value, r"(?i)bearer|secret")

    def test_limits_match_the_documented_adjustable_values(self):
        cfg = load()
        limits = cfg["limits"]
        self.assertEqual(limits, {"model_requests": 10, "tokens": 32000, "wall_ms": 300000, "tool_attempts": 8,
                                  "basic_tool_attempts": 5, "investigator_comparisons": 2, "revision_stages": 1,
                                  "revision_requeries": 2, "final_verify": 1})
        self.assertEqual(limits["basic_tool_attempts"] + limits["revision_requeries"] + limits["final_verify"],
                         limits["tool_attempts"])
        self.assertEqual(cfg["retry"]["max_5xx_retries"], 3)
        self.assertEqual(cfg["timeouts"]["request_cap_ms"], 60000)
        self.assertLess(cfg["timeouts"]["end_reserve_ms"], limits["wall_ms"])

    def test_prompt_files_exist_and_carry_the_fixed_rules(self):
        cfg = load()
        texts = {name: (MODEL_DIR / file).read_text(encoding="utf-8") for name, file in cfg["prompts"].items()}
        self.assertEqual(set(texts), {"investigator", "claims_template", "claims_freeform", "critic"})
        for name, text in texts.items():
            with self.subTest(name=name):
                self.assertTrue(text.strip())
        for name in ("investigator", "critic"):
            self.assertIn("부정문으로도", texts[name])
            self.assertIn("JSON 객체 하나만", texts[name])
            self.assertIn("띄어쓰기를 바꾸거나 붙여 써도", texts[name])
        for phrase in ("같은 소수 자리나 더 거친 자리", "단위 없는 개수", "같은 방향"):
            self.assertIn(phrase, texts["investigator"])
        self.assertIn("도구를 부를 수 없다", texts["critic"])
        self.assertIn("metric_id", texts["claims_template"])
        self.assertIn("evidence_ids", texts["claims_freeform"])
        for status in ("MAINTAIN", "MONITOR", "HOLD", "NOT_TRIGGERED"):
            self.assertIn(status, texts["investigator"])
        self.assertIsNone(re.search(r"[A-Za-z0-9]{32,}", "".join(texts.values())))  # 키처럼 긴 토큰이 없다

    def test_prompts_list_the_pinned_validator_list_each_exactly_once(self):
        self.assertEqual((len(PINNED_PHRASES), len(set(PINNED_PHRASES)), len(PINNED_LATIN)), (62, 62, 9))
        expected = Counter(PINNED_PHRASES + PINNED_LATIN)
        for name in ("investigator.txt", "critic.txt"):
            listed, _ = forbidden_line((MODEL_DIR / name).read_text(encoding="utf-8"))
            self.assertEqual(Counter(listed), expected, name)  # 빠짐·더함·중복 없이 항목마다 한 번
        for name in PROMPT_FILES:  # 목록 줄 밖(네 파일 모두)에는 금지 낱말이 없다(영문은 대소문자 무시)
            _, rest = forbidden_line((MODEL_DIR / name).read_text(encoding="utf-8"))
            self.assertEqual([p for p in expected if p.lower() in rest.lower()], [], name)

    def test_prompts_cover_the_validator_forbidden_list_once_merged(self):
        from tradesentry.validator import validate

        phrases = getattr(validate, "FORBIDDEN_PHRASES", None)
        if phrases is None:
            self.skipTest("검증기(단위 R3, 로드맵 MT3)가 아직 병합되지 않아 금지 목록이 없다")
        latin = tuple(getattr(validate, "FORBIDDEN_LATIN", ()))
        self.assertEqual((tuple(phrases), latin), (PINNED_PHRASES, PINNED_LATIN))  # 바뀌면 사본과 프롬프트를 함께 고친다
        for name in ("investigator.txt", "critic.txt"):
            listed, _ = forbidden_line((MODEL_DIR / name).read_text(encoding="utf-8"))
            self.assertEqual(Counter(listed), Counter(tuple(phrases) + latin), name)


if __name__ == "__main__":
    unittest.main()
