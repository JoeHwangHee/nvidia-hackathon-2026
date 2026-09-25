"""조립 점검(AS4) 시험: 단위 파일에 복사해 둔 계약 상수가 계약 커널(단위 K1, tradesentry.contract.types)과 같은지 본다.

정본: docs/plan/UNITS.md §6 조립 부산물 4(복사된 계약 상수는 K1에서 import하게 바꾼다. 채점기 사본은 예외), 조립 점검 결정
기록 docs/tracking/decisions/20260925-1240-orchestrator-decision-as4-assembly-check.md.

AS4는 MVP 시험 직전이라 사본을 import로 바꾸지 않고(동결 경로 P3·P5·R3과 트랙별 PR 규칙 때문에 후보로 남긴다) 이 시험으로
값이 같음을 고정한다. 사본을 K1 import로 바꾸는 PR은 이 시험이 통과하는 상태에서 바꾸고, 바꾼 뒤에도 통과해야 한다.
K1 값이 바뀌면(예: 계약 버전) 사본을 함께 고치지 않은 곳이 여기서 드러난다.

- 같은 종류·같은 순서까지 본다(순서가 뜻인 튜플이 있다: 판정 우선순위, 실행 결과 기록 키).
- 다른 모양으로 둔 사본(집합, 둘로 나눈 목록)은 K1 값에서 같은 모양을 만들어 비교한다. 모양이 다른 것 자체는 사본마다 쓰임
  (소속 검사)이 달라서이고, import로 바꿀 때 모양 변환을 함께 적어야 한다는 표시다.
- 채점기(eval/scorer/)의 사본은 보지 않는다. 채점기는 tradesentry를 import하지 않는 독립 구현이다(UNITS.md §2).
"""
import unittest

from tradesentry.cli import dispatch
from tradesentry.contract import types as k1
from tradesentry.grouping import g0
from tradesentry.metrics import rounding
from tradesentry.policy import case_aggregate, required_evidence, signal_decide
from tradesentry.reports import claims
from tradesentry.runlog import cause_codes, run_record, trace
from tradesentry.validator import validate
from tradesentry.workflow import investigator, orchestrate

GAPS = frozenset(k1.OBSERVATION_STATUSES) - {k1.OBSERVED, k1.CONFIRMED_NO_TRADE}  # 빠진 관측(계약 §3.4)

# (단위 ID와 이름, 사본, K1에서 만든 기대 값)
SAME = [
    # P5 필수 근거 규칙(동결 경로)
    ("P5 SIGNAL_CODES", required_evidence.SIGNAL_CODES, k1.SIGNALS),
    ("P5 SIGNAL_TRIGGERS", required_evidence.SIGNAL_TRIGGERS, k1.SIGNAL_TRIGGERS),
    ("P5 REVIEW_STATUSES", required_evidence.REVIEW_STATUSES, k1.REVIEW_STATUSES),
    ("P5 SIGNAL_STATUSES", required_evidence.SIGNAL_STATUSES, k1.SIGNAL_STATUSES),
    ("P5 OBSERVATION_STATUSES", required_evidence.OBSERVATION_STATUSES, k1.OBSERVATION_STATUSES),
    ("P5 ALL_PARTNER", required_evidence.ALL_PARTNER, k1.ALL_PARTNER),
    ("P5 SOURCE_KINDS", required_evidence.SOURCE_KINDS, k1.SOURCE_KINDS),
    ("P5 REAL_DATASETS", required_evidence.REAL_DATASETS, tuple(d for d in k1.DATASETS if d.startswith("real_"))),
    ("P5 DATA_STATUS_METRIC", required_evidence.DATA_STATUS_METRIC, k1.DATA_STATUS_METRIC),
    ("P5 CLAIM_METRICS + CLAIM_METRIC_PREFIXES",
     {f: required_evidence.CLAIM_METRICS[f] + required_evidence.CLAIM_METRIC_PREFIXES[f]
      for f in required_evidence.CLAIM_METRICS}, k1.SIGNAL_FAMILY_METRICS),
    # P3 신호별 판정·P4 사례 집계(동결 경로)
    ("P3 GAP_STATUSES(집합)", frozenset(signal_decide.GAP_STATUSES), GAPS),
    ("P4 PRIORITY", case_aggregate.PRIORITY, k1.CASE_STATUS_PRIORITY),
    # R1 typed claim 채우기
    ("R1 MODES", claims.MODES, k1.MODES),
    ("R1 CLAIM_FIELDS", claims.CLAIM_FIELDS, k1.CLAIM_FIELDS),
    ("R1 OBSERVATION_STATUSES", claims.OBSERVATION_STATUSES, k1.OBSERVATION_STATUSES),
    ("R1 UNIT_OF", claims.UNIT_OF, k1.METRIC_UNITS),
    ("R1 DIGITS_OF", claims.DIGITS_OF, k1.DISPLAY_DECIMALS),
    # R3 검증 규칙(동결 경로)
    ("R3 MODES", validate.MODES, k1.MODES),
    ("R3 CLAIM_FIELDS", validate.CLAIM_FIELDS, k1.CLAIM_FIELDS),
    ("R3 CLAIM_TYPES", validate.CLAIM_TYPES, k1.CLAIM_TYPES),
    ("R3 DIRECTIONS", validate.DIRECTIONS, k1.DIRECTIONS),
    ("R3 REVIEW_STATUSES", validate.REVIEW_STATUSES, k1.REVIEW_STATUSES),
    ("R3 SIGNAL_STATUSES", validate.SIGNAL_STATUSES, k1.SIGNAL_STATUSES),
    ("R3 SIGNAL_TRIGGERS", validate.SIGNAL_TRIGGERS, k1.SIGNAL_TRIGGERS),
    ("R3 SIGNALS", validate.SIGNALS, k1.SIGNALS),
    ("R3 OBSERVATION_STATUSES", validate.OBSERVATION_STATUSES, k1.OBSERVATION_STATUSES),
    ("R3 UNIT_OF", validate.UNIT_OF, k1.METRIC_UNITS),
    ("R3 DIGITS_OF", validate.DIGITS_OF, k1.DISPLAY_DECIMALS),
    ("R3 TOTAL_MONTH", validate.TOTAL_MONTH, k1.TOTAL_ROW_MONTH),
    ("R3 REPORT_REQUIRED + REPORT_OPTIONAL(집합)", frozenset(validate.REPORT_REQUIRED + validate.REPORT_OPTIONAL),
     frozenset(k1.REPORT_KEYS)),
    # L1~L3 실행 기록
    ("L1 KST", trace.KST, k1.KST),
    ("L2 RESULT_KEYS", run_record.RESULT_KEYS, k1.RUN_RECORD_KEYS),
    ("L2 SCORER_KEYS", run_record.SCORER_KEYS, k1.RUN_RECORD_SCORER_KEYS),
    ("L2 DATASETS", run_record.DATASETS, k1.DATASETS),
    ("L2 MODES", run_record.MODES, k1.MODES),
    ("L2 REVIEW_STATUSES", run_record.REVIEW_STATUSES, k1.REVIEW_STATUSES),
    ("L2 SIGNAL_STATUSES", run_record.SIGNAL_STATUSES, k1.SIGNAL_STATUSES),
    ("L2 SIGNAL_CODES", run_record.SIGNAL_CODES, k1.SIGNALS),
    ("L3 EXECUTION_STATUSES", cause_codes.EXECUTION_STATUSES, k1.EXECUTION_STATUSES),
    # X4 자릿수·반올림(DT2 결정 ⑪: K1이 생기기 전에 따로 적었다)
    ("X4 SCHEMA_VERSION", rounding.SCHEMA_VERSION, k1.SCHEMA_VERSION),
    ("X4 OBSERVATION_STATUSES(집합)", rounding.OBSERVATION_STATUSES, frozenset(k1.OBSERVATION_STATUSES)),
    ("X4 MISSING_STATUSES(집합)", rounding.MISSING_STATUSES, GAPS),
    ("X4 OBSERVED", rounding.OBSERVED, k1.OBSERVED),
    ("X4 CONFIRMED_NO_TRADE", rounding.CONFIRMED_NO_TRADE, k1.CONFIRMED_NO_TRADE),
    # I10 조사자·I12 흐름 조정
    ("I10 MODES", investigator.MODES, k1.MODES),
    ("I10 REVIEW_STATUSES", investigator.REVIEW_STATUSES, k1.REVIEW_STATUSES),
    ("I10 SIGNAL_STATUSES", investigator.SIGNAL_STATUSES, k1.SIGNAL_STATUSES),
    ("I10 SIGNAL_CODES", investigator.SIGNAL_CODES, k1.SIGNALS),
    ("I10 CLAIM_TYPES", investigator.CLAIM_TYPES, k1.CLAIM_TYPES),
    ("I10 CLAIM_FIELDS", investigator.CLAIM_FIELDS, k1.CLAIM_FIELDS),
    ("I12 MODES", orchestrate.MODES, k1.MODES),
    ("I12 CASE_KEYS", orchestrate.CASE_KEYS, k1.CASE_KEYS),
    # G1 g0 고정 목록(MT6 결정 ③: 열 목록 사본)
    ("G1 PEER_GROUP_KEYS", g0.PEER_GROUP_KEYS, k1.PEER_GROUP_KEYS),
    # F2 명령 배선(AS2 결정 기록: P3 머리 설명과 같은 값의 사본)
    ("F2 GAP_STATUSES", dispatch.GAP_STATUSES, signal_decide.GAP_STATUSES),
]


class ContractCopiesTest(unittest.TestCase):
    def test_every_copy_equals_the_kernel_value(self):
        for name, copy, expected in SAME:
            with self.subTest(copy=name):
                self.assertIs(type(copy), type(expected))
                self.assertEqual(copy, expected)

    def test_copy_list_is_not_empty_and_names_are_unique(self):
        names = [name for name, _, _ in SAME]
        self.assertEqual(len(names), len(set(names)))
        self.assertGreater(len(names), 50)


if __name__ == "__main__":
    unittest.main()
