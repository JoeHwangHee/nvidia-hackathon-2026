"""구성 단위 I9(프롬프트·모델 설정, configs/model/) 검사. 진입 함수가 없는 구성 단위라 골든 쌍 대신 이 시험으로 본다.

- model.json은 소수를 Decimal로 읽는다(float 없음). 키 값은 없고 키 환경변수의 이름만 있다.
- 한도는 개발 플랜 §6.6·자료 계약 §8.1의 조정값과 같다(도구 8회 = 기본 5 + 재조회 2 + 최종 검증 1, 수정 1회,
  모델 요청 10회, 300초, 누적 토큰 32,000, 5xx 재전송 요청당 3회). 바꾸려면 공용 약속 절차를 거친다.
- 프롬프트 파일이 있고, 금지 낱말(부정문으로도 쓰지 않음)·산문 숫자·증감 규칙과 JSON 초안 형식을 담는다. 금지 낱말은
  "금지 낱말:" 줄에만 나온다(나머지 지침 글이 그 낱말을 되풀이해 모델이 따라 쓰지 않게). 검증기(단위 R3)의 금지 목록이
  병합돼 있으면 두 프롬프트가 그 목록을 모두 담는지 본다(MT3 보고에서 넘어온 조건).
"""
import json
import re
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "configs" / "model"


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
            listed, rest = forbidden_line(texts[name])
            self.assertGreaterEqual(len(listed), 40)
            self.assertEqual([p for p in listed if p in rest], [], name)  # 금지 낱말은 목록 줄에만 있다
        for phrase in ("같은 소수 자리나 더 거친 자리", "단위 없는 개수", "같은 방향"):
            self.assertIn(phrase, texts["investigator"])
        self.assertIn("도구를 부를 수 없다", texts["critic"])
        self.assertIn("metric_id", texts["claims_template"])
        self.assertIn("evidence_ids", texts["claims_freeform"])
        for status in ("MAINTAIN", "MONITOR", "HOLD", "NOT_TRIGGERED"):
            self.assertIn(status, texts["investigator"])
        self.assertIsNone(re.search(r"[A-Za-z0-9]{32,}", "".join(texts.values())))  # 키처럼 긴 토큰이 없다

    def test_prompts_cover_the_validator_forbidden_list_once_merged(self):
        from tradesentry.validator import validate

        phrases = getattr(validate, "FORBIDDEN_PHRASES", None)
        if phrases is None:
            self.skipTest("검증기(단위 R3, 로드맵 MT3)가 아직 병합되지 않아 금지 목록이 없다")
        latin = getattr(validate, "FORBIDDEN_LATIN", ())
        cfg = load()
        for name in ("investigator", "critic"):
            text = (MODEL_DIR / cfg["prompts"][name]).read_text(encoding="utf-8")
            listed, _ = forbidden_line(text)
            joined = " ".join(listed)
            self.assertEqual([p for p in phrases if p not in listed], [], name)
            self.assertEqual([w for w in latin if w not in joined.lower()], [], name)


if __name__ == "__main__":
    unittest.main()
