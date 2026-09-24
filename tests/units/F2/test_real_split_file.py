"""분할 기록 정본 파일 data/reference/real_split_kcs_202201_202412_v2.json 시험(조립 작업 AS1 두 번째 PR).

- 위치: 2026-09-25(금) 사용자 결정 8(결정 기록 20260925-0847-user-decision-morning-shared-promises.md). 실자료 분할 단위 V5의
  출력과 바이트가 같아야 한다.
- 이 파일은 공개 자료다. 분할 seed·방법·결과는 결정 기록 20260924-2340-dt4-real-split-and-sample-seed.md에 이미 커밋돼 있다.
- 공식 분할의 입력·출력(tests/units/V5/input.json·expected.json)은 V5 폴더 시험이 sha256으로 고정한다. 이 시험은 그 둘과
  정본 파일을 잇는다: 정본 파일 = 골든 기대 출력 = V5 run을 공통 실행기 형식으로 쓴 바이트. 셋 가운데 하나라도 바뀌면 실패한다.
  정본 파일을 다시 만드는 일은 재분할이 아니라 복사다. 골든 파일을 다시 만드는 일이 재분할이다(사용자 판단).
"""
import hashlib
import json
import unittest
from decimal import Decimal
from pathlib import Path

from eval.datagen import split

ROOT = Path(__file__).resolve().parents[3]
SPLIT_FILE = ROOT / "data" / "reference" / "real_split_kcs_202201_202412_v2.json"  # 사용자 결정 8의 글자 그대로
V5 = ROOT / "tests" / "units" / "V5"
OFFICIAL_SHA256 = "fe9797d2ef57f97fa2de5be6e8924b6615915d92bab0a20899f5e468407db2d0"  # DT4 결정 기록의 출력 파일 sha256


def runner_bytes(value: object) -> bytes:
    """공통 실행기(tradesentry.units.runner.write_output)가 json 출력을 쓰는 바이트 형식."""
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


class RealSplitFileTest(unittest.TestCase):
    def test_same_bytes_as_the_v5_golden_output(self):
        self.assertEqual(SPLIT_FILE.read_bytes(), (V5 / "expected.json").read_bytes())

    def test_sha256_is_the_official_split_output(self):
        self.assertEqual(hashlib.sha256(SPLIT_FILE.read_bytes()).hexdigest(), OFFICIAL_SHA256)

    def test_same_bytes_as_a_fresh_v5_run(self):
        inp = json.loads((V5 / "input.json").read_text(encoding="utf-8"), parse_float=Decimal)
        self.assertEqual(SPLIT_FILE.read_bytes(), runner_bytes(split.run(inp)))

    def test_shape(self):
        record = json.loads(SPLIT_FILE.read_text(encoding="utf-8"))
        self.assertEqual(list(record), ["snapshot_id", "seed", "ratio", "method", "real_dev", "real_sealed"])
        self.assertEqual(record["snapshot_id"], "kcs_202201_202412_v2")
        dev = {(item["hs6"], item["partner"]) for item in record["real_dev"]}
        sealed = {(item["hs6"], item["partner"]) for item in record["real_sealed"]}
        self.assertEqual((len(dev), len(sealed), len(dev & sealed)), (21, 43, 0))


if __name__ == "__main__":
    unittest.main()
