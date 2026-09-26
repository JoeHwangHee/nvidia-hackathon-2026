"""holdout40 생성 스크립트(로드맵 DT6, 단위 V3). 봉인 폴더 안에만 둔다.

- 합성 세계(HS4 8504 아래 HS6 6개 x 합성 상대국 8개, 2022-01~2024-12)와 사례 40건의 사건·판정 근거 규칙을 이 파일에
  손으로 적고, 생성 규칙 JSON(명세 eval/scenarios/SCENARIO_SPEC.md §7.4 형식)을 만든다.
- 파일 내용은 저장소 생성 도구 eval/datagen/dev20.py의 `run`(생성 규칙 -> 파일 내용, 자체 검산, 임시 빌드·S3 검증)으로
  만든다. dev20.py의 generate·check·install 명령은 부르지 않는다(저장소 outputs/·data/snapshots/에 쓰기 때문).
- 기대 판정(signals, signal_status, review_status, unresolved_evidence, required_evidence)은 사례마다 손으로 고른 판정
  근거 규칙 키에서 명세 §5.1 규칙표로 적는다.
- 흔들림 seed는 gen/seed.json(nonce에서 유도)에서 읽는다.
- 계약 버전(schema_version)은 저장소 계약 커널 상수를 따른다. 2026-09-25(금) 계약 버전 2 재생성: 같은 seed·같은 생성
  규칙으로 다시 만들었고, 처음 만든 생성 규칙과 버전 표시 말고는 같다(--compare-rules로 대조).

사용(저장소 작업 폴더를 PYTHONPATH에 두고):
  python generate.py --dry                     # 생성·자체 검산만(파일을 쓰지 않는다)
  python generate.py --out <봉인 폴더>/holdout40  # 파일을 쓴다(이미 있는 파일은 덮지 않는다)
"""
import argparse
import json
import os
import sys
from pathlib import Path

from eval.datagen import dev20

HERE = Path(__file__).resolve().parent
DATASET = "holdout40"
SNAPSHOT_ID = "holdout40"
POLICY_VERSION = "policy_v1"
FIXED_TIME = "2026-09-25T09:30:00+09:00"
PERIOD = {"start": "202201", "end": "202412"}
HS4 = "8504"
HS6 = {"A": "850410", "B": "850421", "C": "850423", "D": "850433", "E": "850434", "F": "850440"}
PARTNERS = ["XR", "XS", "XT", "XU", "XV", "XW", "XY", "XZ"]
PEER_K = 4
PEER_SOURCE_YEAR = 2023

# 계열별 기본 월 값 {HS10 뒤 4자리: [금액 USD, 중량 kg]}. A·B는 여러 나라가 나눠 가진 품목, C~F는 한 나라가 큰 몫을 가진 품목.
SERIES = {
    "A": {
        "XR": {"1010": [2400, 160], "1090": [900, 300]},
        "XS": {"1010": [1800, 100], "3010": [1100, 220], "5000": [700, 35]},
        "XT": {"2010": [2600, 200], "2090": [650, 130]},
        "XU": {"1010": [1500, 60], "1090": [1200, 150]},
        "XV": {"3010": [3100, 310], "5000": [560, 28], "8000": [440, 110]},
        "XW": {"2010": [2200, 110], "2090": [800, 200], "3050": [240, 12]},
        "XY": {"1010": [1950, 130], "3010": [1050, 150]},
        "XZ": {"2010": [1400, 70], "8000": [1350, 450]},
    },
    "B": {
        "XR": {"1010": [7200, 400], "3010": [4800, 600]},
        "XS": {"2010": [3600, 200], "5010": [2000, 250]},
        "XT": {"1010": [2800, 140], "1090": [1200, 400]},
        "XU": {"2010": [2400, 120], "3010": [1200, 200]},
        "XV": {"1010": [1960, 140], "5010": [780, 130]},
        "XW": {"2010": [1100, 50], "3010": [660, 60], "8000": [440, 110]},
        "XY": {"1010": [1200, 60], "1090": [600, 150]},
        "XZ": {"3010": [900, 75], "5010": [500, 100]},
    },
    "C": {
        "XR": {"1010": [24000, 1600], "2010": [12000, 2000]},
        "XS": {"1010": [600, 40], "2010": [450, 50], "3010": [300, 60], "8000": [150, 75]},
        "XT": {"2010": [1100, 100], "5010": [700, 140]},
        "XU": {"1010": [900, 60], "3010": [500, 100]},
        "XV": {"3010": [858, 66], "5010": [442, 34]},
        "XW": {"2010": [800, 40], "8000": [600, 200]},
        "XY": {"1010": [750, 50], "5010": [450, 90]},
        "XZ": {"2010": [700, 50], "3010": [500, 100]},
    },
    "D": {
        "XR": {"1010": [640, 40], "3010": [360, 60]},
        "XS": {"2010": [18000, 1000], "5010": [9600, 1400]},
        "XT": {"1010": [1000, 50], "2010": [600, 60], "3010": [400, 80]},
        "XU": {"2010": [900, 60], "5010": [300, 50], "8000": [200, 25]},
        "XV": {"1010": [800, 50], "3010": [500, 100]},
        "XW": {"2010": [700, 35], "8000": [400, 100]},
        "XY": {"1010": [600, 40], "2010": [400, 50]},
        "XZ": {"3010": [1300, 100], "5010": [500, 125]},
    },
    "E": {
        "XR": {"2010": [800, 50], "3010": [400, 80]},
        "XS": {"2010": [900, 50], "8000": [300, 100]},
        "XT": {"1010": [21000, 1500], "3010": [9000, 1800]},
        "XU": {"1010": [1000, 80], "5010": [600, 150]},
        "XV": {"1010": [700, 50], "2010": [500, 50], "3010": [300, 75]},
        "XW": {"2010": [1500, 75], "5010": [500, 25]},
        "XY": {"1010": [750, 30], "3010": [450, 50], "5010": [300, 100]},
        "XZ": {"1010": [500, 40], "5010": [300, 60]},
    },
    "F": {
        "XR": {"1010": [900, 45], "5010": [600, 100]},
        "XS": {"3010": [1100, 100], "8000": [400, 160]},
        "XT": {"1010": [1200, 80], "3010": [800, 160]},
        "XU": {"2010": [16000, 800], "8000": [8000, 2000]},
        "XV": {"2010": [1000, 50], "5010": [500, 100]},
        "XW": {"1010": [800, 40], "8000": [500, 125]},
        "XY": {"2010": [600, 30], "3010": [400, 80]},
        "XZ": {"1010": [500, 25], "8000": [300, 75]},
    },
}
REST_OF_WORLD = {
    "A": {"1010": [3000, 200], "1090": [2000, 500], "2010": [2500, 150], "3010": [1500, 200]},
    "B": {"1010": [3000, 150], "2010": [2000, 100], "3010": [3000, 500]},
    "C": {"1010": [2000, 130], "2010": [1500, 250]},
    "D": {"2010": [2500, 150], "5010": [1500, 250]},
    "E": {"1010": [2500, 180], "3010": [1500, 300]},
    "F": {"2010": [2000, 100], "8000": [1500, 375]},
}

# 판정 근거 규칙표(명세 §5.1)
RULE_TABLE = {
    "unit_value": {
        "composition_explained": ("MONITOR", ["parent_child_match_V_and_Q", "weight_share_decomposition",
                                              "per_child_unit_value_stable", "comparability_ok"]),
        "unexplained": ("MAINTAIN", ["parent_child_match_V_and_Q", "weight_share_decomposition",
                                     "partner_comparison_done", "comparability_ok"]),
        "hold_missing": ("HOLD", ["missingness_listed", "failure_vs_not_collected_distinguished", "no_zero_fill"]),
        "hold_inconsistent": ("HOLD", ["parent_child_match_V_and_Q", "comparability_ok", "no_zero_fill"]),
        "rounding_unstable": ("HOLD", ["precision_sensitivity_shown"]),
    },
    "share": {
        "unexplained": ("MAINTAIN", ["country_and_world_change_shown", "partner_comparison_done",
                                     "comparability_ok"]),
        "hold_missing": ("HOLD", ["missingness_listed", "failure_vs_not_collected_distinguished", "no_zero_fill"]),
        "hold_inconsistent": ("HOLD", ["country_and_world_change_shown", "comparability_ok", "no_zero_fill"]),
    },
}


def shift(month, delta):
    index = int(month[:4]) * 12 + int(month[4:]) - 1 + delta
    return f"{index // 12}{index % 12 + 1:02d}"


def exact(m):
    return {"type": "exact", "month": m}


def children(m, values):
    return {"type": "children", "month": m, "values": values}


def parent(m, value):
    return {"type": "parent", "month": m, "value": value}


def scale(m, who, volume, price):
    return {"type": "scale", "month": m, "who": who, "volume": volume, "price": price}


def world(m, values):
    return {"type": "world", "month": m, "values": values}


def request(g, p, year, status):
    return {"type": "request", "endpoint": "nitemtrade", "hsSgn": HS6[g], "cntyCd": p, "strtYymm": f"{year}01",
            "status": status}


def others(target, exclude=()):
    return [p for p in PARTNERS if p != target and p not in exclude] + ["ROW"]


# 사례: (품목 묶음, 상대국, 비교월, 분류, 단가 규칙, 점유율 규칙, 사건, 메모)
CASES = [
    # ---- A(850410, 여러 나라가 나눔)
    ("A", "XR", "202402", 1, "composition_explained", None,
     [exact("202302"), children("202402", {"1010": [900, 60], "1090": [1500, 500]})],
     "하위 단가(15·3) 그대로, 싼 품목 중량 비중이 65%에서 89%로 늘어 부모 단가 약 -40%"),
    ("A", "XS", "202403", 8, None, "unexplained",
     [exact("202303"), exact("202403"), scale("202403", others("XS"), "0.35", "1")],
     "대상국 금액·단가는 그대로, 다른 상대국과 나머지 세계 물량이 65% 줄어 분모가 작아짐(점유율 상승)"),
    ("A", "XT", "202404", 2, "unexplained", None,
     [exact("202304"), children("202404", {"2010": [1430, 200], "2090": [714, 136]})],
     "비싼 하위품목 단가 -45%, 싼 품목 +5%. 구성효과를 빼도 약 -35% 남음"),
    ("A", "XU", "202405", 3, "unexplained", None,
     [exact("202305"), children("202405", {"1010": [2250, 60], "1090": [1560, 150]}),
      scale("202405", others("XU"), "1", "1.22")],
     "대상국 하위 단가 +50%·+30%. 같은 달 비교국과 나머지 세계 단가도 약 +22%(기준 아래)로 함께 오름"),
    ("A", "XV", "202406", 8, None, "unexplained",
     [exact("202306"), children("202406", {"3010": [8060, 806], "5000": [1456, 73], "8000": [1144, 286]})],
     "대상국 물량이 2.6배로 늘어(하위 단가 거의 그대로) 점유율 상승. 분모 완전"),
    ("A", "XW", "202407", 6, "hold_inconsistent", None,
     [children("202307", {"2010": [2200, 110], "2090": [800, 200], "3050": [240, 0]}),
      children("202407", {"2010": [3190, 110], "2090": [1160, 200], "3050": [348, 12]})],
     "기준월 하위품목 하나가 금액 240 USD·중량 0 kg이라 그 품목 단가 계산 불가 -> 분해 불가. 부모 단가 약 +40%"),
    ("A", "XY", "202408", 2, "unexplained", None,
     [exact("202308"), children("202408", {"1010": [2700, 120], "3010": [1617, 165]})],
     "하위 단가 +50%·+40%에 비중이 조금 옮음. 단가 약 +41% 대부분이 within"),
    # ---- B(850421, 큰 나라 하나 + 여러 나라)
    ("B", "XR", "202402", 8, None, "unexplained",
     [exact("202302"), exact("202402"), scale("202402", ["ROW"], "4.5", "1")],
     "대상국 금액은 그대로인데 수집하지 않은 나라들(나머지 세계) 수입이 4.5배로 늘어 분모가 커짐(점유율 하락)"),
    ("B", "XS", "202409", 8, None, "unexplained",
     [exact("202309"), children("202409", {"2010": [432, 24], "5010": [240, 30]})],
     "대상국 물량이 88% 줄어(하위 단가 그대로) 점유율 하락. 분모 완전"),
    ("B", "XT", "202410", 10, "composition_explained", "unexplained",
     [exact("202310"), children("202410", {"1010": [8400, 420], "1090": [1200, 400]})],
     "단가: 하위 단가(20·3) 그대로, 비싼 품목 물량이 3배로 늘어 부모 단가 약 +58%(구성효과). 점유율: 금액 2.4배로 상승"),
    ("B", "XU", "202411", 10, "hold_inconsistent", "unexplained",
     [exact("202311"), children("202411", {"2010": [9000, 400], "3090": [1000, 160]})],
     "단가: 비교월에 3010이 없고 3090이 그 달에만 나옴 -> HS10 집합이 달라 분해 불가(부모 단가 약 +59%). "
     "점유율: 금액이 크게 늘어 상승, 분모 완전"),
    ("B", "XV", "202405", 4, "hold_missing", None,
     [exact("202305"), children("202405", {"1010": [1120, 140], "5010": [390, 110]}),
      request("B", "XV", 2023, "FAILED")],
     "부모 HS6 단가 약 -40.5%. 기준월 연도의 대상국 HS10 조회 실패(REQUEST_FAILED) -> 분해 불가"),
    ("B", "XW", "202406", 1, "composition_explained", None,
     [exact("202306"), children("202406", {"2010": [440, 20], "3010": [440, 40], "8000": [1000, 250]})],
     "하위품목 셋의 단가(22·11·4) 그대로, 싼 품목 중량 비중이 50%에서 81%로 늘어 부모 단가 약 -39%"),
    ("B", "XY", "202407", 2, "unexplained", None,
     [exact("202307"), children("202407", {"1010": [1920, 60], "1090": [720, 150]})],
     "하위 단가 +60%·+20%, 비중 그대로. 단가 약 +47%가 모두 within"),
    # ---- C(850423, XR이 큰 몫)
    ("C", "XR", "202403", 7, None, "hold_inconsistent",
     [exact("202303"), exact("202403"), world("202403", {"1010": [20000, 1300], "2010": [11000, 1800]})],
     "비교월 전체국가 분모 31,000 USD가 대상국 금액 36,000 USD보다 작음(점유율 100% 초과). 대상국 금액·단가 그대로"),
    ("C", "XS", "202404", 1, "composition_explained", None,
     [exact("202304"),
      children("202404", {"1010": [1200, 80], "2010": [540, 60], "3010": [150, 30], "8000": [60, 30]})],
     "하위품목 넷의 단가(15·9·5·2) 그대로, 비싼 품목 쪽으로 비중이 옮아 부모 단가 약 +46%"),
    ("C", "XT", "202406", 3, "unexplained", None,
     [exact("202306"), children("202406", {"2010": [605, 110], "5010": [455, 130]}),
      scale("202406", others("XT"), "1", "0.8")],
     "대상국 하위 단가 -50%·-30%(부모 약 -41%). 같은 달 큰 공급국 포함 비교국 단가도 약 -20%로 함께 내림"),
    ("C", "XU", "202407", 5, "hold_inconsistent", None,
     [exact("202307"), children("202407", {"1010": [1305, 60], "3010": [725, 100]}), parent("202407", [2130, 160])],
     "비교월 부모 HS6 금액 2,130 USD와 HS10 하위 합 2,030 USD가 다름(금액 정확 일치 위반). 부모 단가 약 +52%"),
    ("C", "XV", "202408", 6, "rounding_unstable", None,
     [children("202308", {"3010": [104, 8], "5010": [52, 4]}), children("202408", {"3010": [140, 8], "5010": [71, 4]})],
     "기준월 156 USD·12 kg, 비교월 211 USD·12 kg(단가 약 +35.3%). 두 달 부모 중량을 ±0.5 kg 움직이면 구간 하한 약 "
     "+24.4%가 기준 30% 아래(반올림 불안정). 최소 기준은 넘음"),
    ("C", "XW", "202409", 2, "unexplained", None,
     [exact("202309"), children("202409", {"2010": [1120, 40], "8000": [540, 150]})],
     "비싼 하위품목 단가 +40%, 싼 품목 +20%, 비중도 비싼 쪽으로 옮음. within만 약 +34%"),
    ("C", "XY", "202410", 4, "hold_missing", None,
     [exact("202310"), children("202410", {"1010": [1050, 48], "5010": [648, 92]}),
      request("C", "XY", 2024, "NOT_COLLECTED")],
     "부모 HS6 단가 약 +41.5%. 비교월 연도의 대상국 HS10 조회가 수집되지 않음(NOT_COLLECTED) -> 분해 불가"),
    # ---- D(850433, XS가 큰 몫)
    ("D", "XS", "202304", 7, None, "hold_inconsistent",
     [exact("202204"), exact("202304"), world("202204", {"2010": [14000, 800], "5010": [8000, 1300]})],
     "기준월 전체국가 분모 22,000 USD가 대상국 금액 27,600 USD보다 작음(기준월 점유율 100% 초과). 비교월은 정상"),
    ("D", "XR", "202405", 9, "unexplained", None,
     [exact("202305"), children("202405", {"1010": [960, 40], "3010": [420, 56]})],
     "대상국의 이 HS6는 그 나라 8504 수입의 작은 부분이라 HS4 합계로 보면 단가 변화가 작아 보임(범위 함정). "
     "사례 범위(HS6)에서는 하위 단가 +50%·+25%로 약 +44%"),
    ("D", "XT", "202406", 1, "composition_explained", None,
     [exact("202306"), children("202406", {"1010": [300, 15], "2010": [600, 60], "3010": [1100, 220]})],
     "하위품목 셋의 단가(20·10·5) 그대로, 금액 합은 같고 싼 품목 쪽으로 비중이 옮아 부모 단가 약 -36%"),
    ("D", "XU", "202407", 6, "hold_inconsistent", None,
     [exact("202307"), children("202407", {"2010": [1260, 60], "5010": [420, 50], "8000": [160, 0]})],
     "비교월 하위품목 하나가 금액 160 USD·중량 0 kg -> 분해 불가. 부모 단가 약 +61%"),
    ("D", "XV", "202408", 5, "hold_inconsistent", None,
     [exact("202308")]
     + [children(f"2024{mm:02d}", {"1010": [800, 50], "3050": [500, 100]}) for mm in range(1, 13) if mm != 8]
     + [children("202408", {"1010": [1200, 52], "3050": [640, 98]})],
     "HSK 개정 흔적: 2024년 1월부터 하위 코드 3010이 사라지고 3050이 새로 나옴 -> 기준월과 비교월의 HS10 집합이 달라 "
     "분해 불가. 부모 단가 약 +41.5%"),
    ("D", "XW", "202409", 4, "hold_missing", None,
     [exact("202309"), children("202409", {"2010": [455, 35], "8000": [200, 100]}),
      request("D", "XW", 2024, "FAILED")],
     "부모 HS6 단가 약 -40.5%. 비교월 연도의 대상국 HS10 조회 실패(REQUEST_FAILED) -> 분해 불가"),
    ("D", "XZ", "202410", 2, "unexplained", None,
     [exact("202310"), children("202410", {"3010": [715, 100], "5010": [460, 125]})],
     "비싼 하위품목 단가 -45%, 싼 품목 -8%, 비중 그대로. 단가 약 -34.7%가 모두 within"),
    # ---- E(850434, XT가 큰 몫)
    ("E", "XT", "202402", 7, None, "hold_inconsistent",
     [exact("202302"), exact("202402"), world("202402", {"1010": [25000, 1800]})],
     "비교월 전체국가 분모에 하위 코드 하나(3010)가 빠져 25,000 USD로 대상국 금액 30,000 USD보다 작음"),
    ("E", "XS", "202403", 9, "composition_explained", None,
     [exact("202303"), children("202403", {"2010": [360, 20], "8000": [450, 150]})],
     "범위 함정: 이 나라 8504 합계로 보면 단가 변화가 작음. 사례 범위(HS6)에서는 하위 단가(18·3) 그대로, "
     "싼 품목 비중이 늘어 부모 단가 약 -40%"),
    ("E", "XU", "202405", 3, "unexplained", None,
     [exact("202305"), children("202405", {"1010": [560, 80], "5010": [390, 150]}),
      scale("202405", others("XU"), "1", "0.77")],
     "대상국 하위 단가 -44%·-35%(부모 약 -41%). 같은 달 비교국과 나머지 세계 단가도 약 -23%로 함께 내림"),
    ("E", "XV", "202406", 5, "hold_inconsistent", None,
     [exact("202306"), children("202406", {"1010": [1050, 50], "3010": [450, 75], "5090": [300, 20]})],
     "비교월에 2010이 없고 5090이 그 달에만 나옴 -> HS10 집합이 달라 분해 불가. 부모 단가 약 +45%"),
    ("E", "XW", "202407", 6, "rounding_unstable", None,
     [children("202307", {"2010": [180, 9], "5010": [60, 3]}), children("202407", {"2010": [117, 9], "5010": [39, 3]})],
     "기준월 240 USD·12 kg, 비교월 156 USD·12 kg(단가 -35%). 두 달 부모 중량을 ±0.5 kg 움직이면 구간 상한 약 "
     "-29.4%가 -30%보다 큼(반올림 불안정). 최소 기준은 넘음"),
    ("E", "XY", "202408", 1, "composition_explained", None,
     [exact("202308"), children("202408", {"1010": [250, 10], "3010": [450, 50], "5010": [600, 200]})],
     "하위품목 셋의 단가(25·9·3) 그대로, 가장 싼 품목 비중이 56%에서 77%로 늘어 부모 단가 -40%"),
    # ---- F(850440, XU가 큰 몫)
    ("F", "XU", "202403", 7, None, "hold_inconsistent",
     [exact("202303"), children("202403", {"2010": [20000, 1000], "8000": [10000, 2500]}),
      world("202403", {"2010": [18500, 950], "8000": [10500, 2600]})],
     "대상국 물량이 1.25배(단가 그대로)로 늘었는데 비교월 전체국가 분모 29,000 USD가 대상국 금액 30,000 USD보다 작음"),
    ("F", "XR", "202404", 1, "composition_explained", None,
     [exact("202304"), children("202404", {"1010": [1800, 90], "5010": [300, 50]})],
     "하위 단가(20·6) 그대로, 비싼 품목 비중이 31%에서 64%로 늘어 부모 단가 +45%"),
    ("F", "XS", "202405", 2, "unexplained", None,
     [exact("202305"), children("202405", {"3010": [1650, 100], "8000": [420, 150]})],
     "비싼 하위품목 단가 +50%, 싼 품목 +12%. 구성효과를 빼도 약 +40% 남음"),
    ("F", "XT", "202406", 3, "unexplained", None,
     [exact("202306"), children("202406", {"1010": [1740, 80], "3010": [1080, 160]}),
      scale("202406", others("XT"), "1", "1.22")],
     "대상국 하위 단가 +45%·+35%(부모 +41%). 같은 달 큰 공급국 포함 비교국 단가도 약 +22%로 함께 오름"),
    ("F", "XV", "202407", 4, "hold_missing", None,
     [exact("202307"), children("202407", {"2010": [1350, 50], "5010": [725, 100]}),
      request("F", "XV", 2023, "NOT_COLLECTED")],
     "부모 HS6 단가 약 +38%. 기준월 연도의 대상국 HS10 조회가 수집되지 않음(NOT_COLLECTED) -> 분해 불가"),
    ("F", "XW", "202408", 5, "hold_inconsistent", None,
     [exact("202308"), parent("202308", [1300, 150]), children("202408", {"1010": [1300, 40], "8000": [700, 125]})],
     "기준월 부모 HS6 중량 150 kg와 HS10 하위 합 165 kg의 차이가 허용오차(0.5 kg x 3)를 넘음. 부모 단가 약 +40%"),
]


def expected_for(rule_u, rule_s):
    signals, status, evidence = {}, {}, {}
    for family, key in (("unit_value", rule_u), ("share", rule_s)):
        if key is None:
            signals[family], status[family] = "NOT_TRIGGERED", "NOT_TRIGGERED"
        else:
            st, ev = RULE_TABLE[family][key]
            signals[family], status[family] = "TRIGGERED", st
            evidence[family] = list(ev)
    fired = [status[f] for f in ("unit_value", "share") if signals[f] == "TRIGGERED"]
    if "MAINTAIN" in fired:
        review = "MAINTAIN"
    elif "HOLD" in fired:
        review = "HOLD"
    else:
        review = "MONITOR"
    unresolved = "MAINTAIN" in fired and "HOLD" in fired
    required = next(iter(evidence.values())) if len(evidence) == 1 else {"unit_value": evidence["unit_value"],
                                                                         "share": evidence["share"]}
    return {"signals": signals, "signal_status": status, "review_status": review,
            "unresolved_evidence": unresolved, "required_evidence": required}


def build_rules():
    seed = json.loads((HERE / "seed.json").read_text(encoding="utf-8"))
    hs6 = [HS6[g] for g in sorted(HS6)]
    rules = {
        "schema_version": dev20.types.SCHEMA_VERSION, "dataset": DATASET, "snapshot_id": SNAPSHOT_ID, "policy_version": POLICY_VERSION,
        "fixed_time": FIXED_TIME,
        "world": {
            "period": dict(PERIOD), "hs4": HS4, "hs6": hs6, "partners": list(PARTNERS),
            "noise": {"seed": seed["noise_seed"], "quantity_permille": 15, "price_permille": 8},
            "series": {HS6[g]: SERIES[g] for g in sorted(HS6)},
            "rest_of_world": {HS6[g]: REST_OF_WORLD[g] for g in sorted(HS6)},
            "peer_k": PEER_K, "peer_source_year": PEER_SOURCE_YEAR,
        },
        "cases": [],
    }
    for g, p, month, klass, rule_u, rule_s, events, note in CASES:
        h = HS6[g]
        rules["cases"].append({
            "case_id": f"{h}-{p}-{month}", "hs6": h, "partner": p, "month": month, "scenario_class": klass,
            "events": events, "rule": {"unit_value": rule_u, "share": rule_s},
            "expected": expected_for(rule_u, rule_s), "note": note})
    return rules


def map_path(repo_path):
    """dev20.run이 돌려준 저장소 기준 경로 -> 봉인 묶음(holdout40/) 기준 경로."""
    bundle = f"eval/dev/{DATASET}/"
    snap = f"data/snapshots/{SNAPSHOT_ID}/"
    peer = f"data/reference/peer_group_{SNAPSHOT_ID}.csv"
    if repo_path.startswith(bundle):
        return repo_path[len(bundle):]
    if repo_path.startswith(snap):
        return "input/source/" + repo_path[len(snap):]
    if repo_path == peer:
        return f"input/source/peer_group_{SNAPSHOT_ID}.csv"
    raise ValueError("대응하지 않는 경로가 있다")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true")
    parser.add_argument("--out")
    parser.add_argument("--compare-rules", help="앞서 만든 generation_rules.json. schema_version 말고 같아야 한다")
    args = parser.parse_args(argv)
    rules = build_rules()
    if args.compare_rules:
        old = json.loads(Path(args.compare_rules).read_text(encoding="utf-8"))
        same = {k: v for k, v in old.items() if k != "schema_version"} == \
            {k: v for k, v in rules.items() if k != "schema_version"}
        print(json.dumps({"rules_equal_except_schema_version": same}))
        if not same:
            return 1
    result = dev20.run(rules)
    summary = result["summary"]
    print(json.dumps({"cases": summary["cases"], "requests": summary["requests"],
                      "self_check_extra_triggers": summary["self_check"]["extra_triggers"],
                      "files": summary["files"], "snapshot_verify_ok": summary["snapshot_verify_ok"]},
                     ensure_ascii=False))
    if args.dry:
        return 0
    out = Path(args.out)
    mapped = {map_path(k): v for k, v in result["files"].items()}
    if len(mapped) != len(result["files"]):
        raise ValueError("경로 대응이 겹친다")
    for rel, text in sorted(mapped.items()):
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as fh:
            fh.write(text.encode("utf-8"))
    print(json.dumps({"written": len(mapped)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
