"""단위 V2(datagen_dev20) 동작 시험: 커밋된 dev20 묶음의 재현·형식·분리, 설치 경로, 자체 검산의 음성 사례.

- 커밋된 생성 규칙(eval/dev/dev20/answers/generation_rules.json)으로 다시 만든 파일이 커밋된 파일과 바이트로 같다.
- 입력 하위 경로(eval/dev/dev20/input/)에는 기대 상태·분류·생성 계열·정답표 키가 없다(채점 대상 실행 샌드박스가 읽는다).
- 커밋된 원천으로 수집기 SQLite를 재현해 단위 S2로 빌드하면 사례 목록에 적힌 normalized_sha256과 같고 단위 S3를 통과한다.
- 자체 검산은 사례 밖 경보, 기대 발동과 다른 자료, 탐지 기준에 너무 가까운 값, 판정 근거 규칙과 다른 자료를 잡는다.
- 생성 코드(eval/datagen/dev20.py)에는 사례 식별자가 없다(사례별 기대 상태는 정답 하위 경로의 생성 규칙에만 둔다).
음성 사례는 작은 골든 입력(tests/units/V2/input.json)을 고쳐 만든다. 네트워크·키 없이 돈다.
"""
import copy
import json
import sqlite3
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from eval.datagen import dev20
from eval.datagen import holdout40_check as v4
from tradesentry.contract.policy_load import load_policy
from tradesentry.dal import query

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DEV20 = ROOT / "eval" / "dev" / "dev20"


def committed_rules() -> dict:
    return json.loads((DEV20 / "answers" / "generation_rules.json").read_text(encoding="utf-8"))


def golden_rules() -> dict:
    return json.loads((HERE / "input.json").read_text(encoding="utf-8"), parse_float=Decimal)


class CommittedBundleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = committed_rules()
        cls.result = dev20.run(cls.rules)

    def test_regenerates_byte_for_byte(self):
        self.assertEqual(dev20.compare_committed(self.result["files"], DEV20), [])

    def test_v4_accepts_dev20_with_allocation(self):
        report = v4.check_files(DEV20 / "input" / "cases.json", DEV20 / "answers" / "answers.json",
                                DEV20 / "answers" / "parent_series_ids.json")
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["counts"]["by_class"], {str(k): n for k, n in v4.ALLOCATION["dev20"].items()})
        self.assertEqual(report["counts"]["cases"], 20)

    def test_self_check_finds_exactly_the_cases(self):
        checked = self.result["summary"]["self_check"]
        self.assertEqual((checked["cases"], checked["triggered_series_months"], checked["extra_triggers"]), (20, 20, 0))
        self.assertTrue(self.result["summary"]["snapshot_verify_ok"])

    def test_input_subpath_holds_no_answers(self):
        cases = json.loads((DEV20 / "input" / "cases.json").read_text(encoding="utf-8"))
        self.assertTrue(all(list(item) == list(v4.CASE_ITEM_KEYS) for item in cases["cases"]))
        self.assertEqual([c["case_id"] for c in cases["cases"]], sorted(c["case_id"] for c in cases["cases"]))
        banned = ("scenario_class", "required_evidence", "review_status", "signal_status", "parent_series_id",
                  "expected", "MAINTAIN", "MONITOR", "HOLD", "ps_")
        for path in (DEV20 / "input").rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                for word in banned:
                    self.assertNotIn(word, text, f"{path.relative_to(ROOT)}에 정답 쪽 글자 {word}")

    def test_answers_follow_hand_written_rules(self):
        answers = json.loads((DEV20 / "answers" / "answers.json").read_text(encoding="utf-8"))
        by_id = {c["case_id"]: c for c in self.rules["cases"]}
        self.assertEqual(set(by_id), {c["case_id"] for c in answers["cases"]})
        for entry in answers["cases"]:
            source = by_id[entry["case_id"]]
            for key in ("scenario_class", "rule", "expected", "note"):
                self.assertEqual(entry[key], source[key])
        ids = json.loads((DEV20 / "answers" / "parent_series_ids.json").read_text(encoding="utf-8"))
        self.assertEqual(ids["parent_series_ids"], sorted({c["parent_series_id"] for c in answers["cases"]}))
        self.assertEqual(len(ids["parent_series_ids"]), 20)

    def test_generator_code_holds_no_case_ids(self):
        code = (ROOT / "eval" / "datagen" / "dev20.py").read_text(encoding="utf-8")
        for case in self.rules["cases"]:
            self.assertNotIn(case["case_id"], code)

    def test_is_deterministic(self):
        self.assertEqual(dev20.run(committed_rules()), self.result)


class InstallPathTest(unittest.TestCase):
    """install 명령과 같은 순서(원천 → 수집기 SQLite → 단위 S2 빌드 → 단위 S3)를 임시 폴더에서 돌린다."""

    def test_committed_source_builds_to_recorded_hash(self):
        cases = json.loads((DEV20 / "input" / "cases.json").read_text(encoding="utf-8"))
        source = DEV20 / "input" / "source"
        with tempfile.TemporaryDirectory() as tmp:
            collector = dev20.materialize_collector(source, Path(tmp) / "dev20")
            con = sqlite3.connect(f"{(collector / 'snapshot.sqlite').as_uri()}?mode=ro", uri=True)
            try:
                stamps = {row[0] for row in con.execute("SELECT timestamp FROM collection_receipt")}
            finally:
                con.close()
            self.assertEqual(stamps, {"2026-09-25T00:00:00+09:00"})
            db = Path(tmp) / "build.sqlite"
            built = dev20.build_and_verify(collector, source / "peer_group_dev20_g0.csv", "dev20",
                                           load_policy(cases["policy_version"]), db)
            self.assertEqual(built["normalized_sha256"], cases["snapshot_normalized_sha256"])
            snapshot = query.open_snapshot("dev20", path=db)
            self.assertEqual(snapshot.world("850432", "202406")["amount_usd"], 5600)  # 분모가 대상국보다 작은 달
            self.assertEqual(snapshot.children("850431", "US", "202412")["observation_status"], "REQUEST_FAILED")
            # 합성 비교국 표(g0 규칙): 대상국을 뺀 다섯 나라가 2023년 부모 HS6 수입금액 내림차순(같으면 코드순)이다
            peers = [p["peer_id"] for p in snapshot.peers("850450", "DE", "g0")]
            self.assertEqual(sorted(peers), ["CN", "JP", "MY", "US", "VN"])
            sums = {q: sum(snapshot.parent("850450", q, f"2023{m:02d}")["amount_usd"] for m in range(1, 13))
                    for q in peers}
            self.assertEqual(peers, sorted(peers, key=lambda q: (-sums[q], q)))

    def test_materialize_refuses_existing_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "dev20"
            target.mkdir()
            with self.assertRaises(FileExistsError):
                dev20.materialize_collector(DEV20 / "input" / "source", target)


class SelfCheckNegativeTest(unittest.TestCase):
    """생성 규칙을 고쳐 자체 검산·규칙 검사가 멈추는지 본다(작은 골든 입력)."""

    def assert_refused(self, rules: dict, fragment: str) -> None:
        with self.assertRaises(ValueError) as caught:
            dev20.run(rules)
        self.assertIn(fragment, str(caught.exception))

    def test_golden_input_passes(self):
        self.assertEqual(dev20.run(golden_rules())["summary"]["self_check"]["extra_triggers"], 0)

    def test_trigger_outside_cases_is_refused(self):
        rules = golden_rules()
        rules["cases"][0]["events"].append({"type": "scale", "month": "202407", "who": ["DE"], "volume": "1",
                                            "price": "0.5"})
        self.assert_refused(rules, "사례 밖 경보")

    def test_expected_signals_must_match_data(self):
        rules = golden_rules()
        rules["cases"][0]["events"][1]["values"] = {"1000": [900, 75], "2000": [300, 75]}  # 변화 없음
        self.assert_refused(rules, "기대 signals와 다르다")

    def test_value_near_threshold_is_refused(self):
        rules = golden_rules()
        rules["cases"][0]["events"][1]["values"] = {"1000": [360, 30], "2000": [480, 120]}  # 단가 -30.0%
        self.assert_refused(rules, "탐지 기준에서")

    def test_composition_case_needs_fixed_child_prices(self):
        rules = golden_rules()
        rules["cases"][0]["events"][1]["values"] = {"1000": [150, 15], "2000": [540, 135]}  # 하위 단가가 바뀜
        self.assert_refused(rules, "구성효과 사례인데")

    def test_missing_case_needs_failed_or_uncollected_children(self):
        rules = golden_rules()
        rules["cases"][1]["events"].pop()  # 미수집 사건을 뺀다
        self.assert_refused(rules, "관측 누락 보류 사례인데")

    def test_conflicting_events_are_refused(self):
        rules = golden_rules()
        rules["cases"][0]["events"].append({"type": "exact", "month": "202403"})
        self.assert_refused(rules, "사건이 이미 있다")

    def test_malformed_events_are_refused(self):
        for event in ({"type": "exact", "month": "202403", "extra": 1},
                      {"type": "scale", "month": "202407", "who": ["DE"], "volume": Decimal("0.5"), "price": "1"},
                      {"type": "children", "month": "209901", "values": {"1000": [1, 1]}},
                      {"type": "children", "month": "202402", "values": {"1000": [0, 0]}}):
            rules = golden_rules()
            rules["cases"][0]["events"].append(event)
            with self.subTest(event=event), self.assertRaises(ValueError):
                dev20.run(rules)

    def test_answer_must_follow_rule_table(self):
        rules = golden_rules()
        rules["cases"][0]["expected"]["required_evidence"] = ["comparability_ok"]
        self.assert_refused(rules, "단위 V4 검사를 통과하지 못했다")

    def test_case_id_must_be_p2_form(self):
        rules = golden_rules()
        rules["cases"][0]["case_id"] = "A-composition"
        self.assert_refused(rules, "case_id는")

    def test_rules_input_is_not_changed(self):
        rules = golden_rules()
        before = copy.deepcopy(rules)
        dev20.run(rules)
        self.assertEqual(rules, before)


if __name__ == "__main__":
    unittest.main()
