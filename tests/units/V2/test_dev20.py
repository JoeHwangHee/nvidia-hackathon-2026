"""단위 V2(datagen_dev20) 동작 시험: 커밋된 dev20 묶음의 재현·형식·분리, 설치 경로, 자체 검산의 음성 사례.

- 커밋된 생성 규칙(eval/dev/dev20/answers/generation_rules.json)으로 다시 만든 파일이 커밋된 파일(묶음, 스냅샷 폴더의
  텍스트 원천, data/reference/의 합성 비교국 표)과 바이트로 같고, 커밋된 빌드 기록의 기록 키가 다시 만든 빌드와 같다.
- 상대국은 관세청 국가코드 목록·국가 코드 대응표에 없는 합성 코드(ISO 3166-1 사용자 지정 범위)다.
- 입력 하위 경로(eval/dev/dev20/input/)에는 기대 상태·분류·생성 계열·정답표 키가 없다(채점 대상 실행 샌드박스가 읽는다).
- 커밋된 원천으로 수집기 SQLite를 재현해 단위 S2로 빌드하면 사례 목록에 적힌 normalized_sha256과 같고 단위 S3를 통과한다.
- install은 임시 저장소 사본에서 없는 것만 만들고, 다시 부르면 아무것도 쓰지 않으며, 자리에 다른 파일이 있으면 덮지 않고 멈춘다.
- 자체 검산은 사례 밖 경보, 기대 발동과 다른 자료, 탐지 기준에 너무 가까운 값, 판정 근거 규칙과 다른 자료, policy_v1
  제안 최소 기준 미달, 반올림 불안정 규칙 후보(U4)와 다른 판정을 잡는다.
- 생성 코드(eval/datagen/dev20.py)에는 사례 식별자가 없다(사례별 기대 상태는 정답 하위 경로의 생성 규칙에만 둔다).
음성 사례는 작은 골든 입력(tests/units/V2/input.json)을 고쳐 만든다. 네트워크·키 없이 돈다.
"""
import copy
import csv
import json
import shutil
import sqlite3
import tempfile
import unittest
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from unittest import mock

from eval.datagen import dev20
from eval.datagen import holdout40_check as v4
from tradesentry.contract.policy_load import load_policy
from tradesentry.dal import query

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DEV20 = ROOT / "eval" / "dev" / "dev20"
SNAPSHOT = ROOT / "data" / "snapshots" / "dev20"
PEER_FILE = ROOT / "data" / "reference" / "peer_group_dev20.csv"


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
        self.assertEqual(dev20.compare_committed(self.result, ROOT), [])

    def test_committed_build_record_names_reference_peer_file(self):
        record = json.loads((SNAPSHOT / "snapshot_build.json").read_text(encoding="utf-8"))
        self.assertEqual([entry["file_name"] for entry in record["peer_group_files"]], [PEER_FILE.name])
        cases = json.loads((DEV20 / "input" / "cases.json").read_text(encoding="utf-8"))
        self.assertEqual(record["normalized_sha256"], cases["snapshot_normalized_sha256"])

    def test_partners_are_unassigned_synthetic_codes(self):
        partners = self.rules["world"]["partners"]
        self.assertEqual(partners, ["XL", "XM", "XN", "XO", "XP", "XQ"])  # DT3의 XA~XJ와 겹치지 않고 XK는 쓰지 않는다
        kcs = json.loads((ROOT / "data" / "reference" / "kcs_country_codes.json").read_text(encoding="utf-8"))
        assigned = {row[0] for row in kcs if isinstance(row, list) and row}
        with open(ROOT / "data" / "reference" / "country_map.csv", encoding="utf-8", newline="") as fh:
            mapped = {row["cntyCd"] for row in csv.DictReader(fh)}
        self.assertTrue({"CN", "US"} <= assigned and {"CN", "US"} <= mapped)  # 목록을 제대로 읽었는지
        self.assertFalse(set(partners) & assigned)
        self.assertFalse(set(partners) & mapped)
        for case in self.rules["cases"]:
            self.assertIn(case["partner"], partners)

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
        # 입력 하위 경로와, 샌드박스에 함께 들어가는 스냅샷 쪽 텍스트(원천·빌드 기록)와 합성 비교국 표
        paths = [p for p in (DEV20 / "input").rglob("*") if p.is_file()]
        paths += [SNAPSHOT / name for name in ("manifest.json", "collection_log.json", "snapshot_hash.json",
                                               "snapshot_build.json")] + [PEER_FILE]
        for path in paths:
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


class CommittedRulesNegativeTest(unittest.TestCase):
    """커밋된 생성 규칙을 한 곳씩 고쳐, 판정 근거 규칙별 자료 불변식과 분류 3·9 검사가 각각 멈추는지 본다.

    규칙 키나 분류 번호를 자료와 맞지 않게 바꾸면(자료는 그대로) 그 규칙의 불변식만 어긋난다. 발동 여부는 그대로라
    앞 단계(기대 signals 대조)에서 멈추지 않는다."""

    def assert_refused(self, change, fragment: str) -> None:
        rules = committed_rules()
        change(rules)
        with self.assertRaises(ValueError) as caught:
            dev20.run(rules)
        self.assertIn(fragment, str(caught.exception))

    @staticmethod
    def case(rules: dict, scenario_class: int, **rule: str) -> dict:
        """그 분류에서 규칙 키가 rule과 같은 첫 사례(식별자 순)."""
        found = [c for c in rules["cases"] if c["scenario_class"] == scenario_class
                 and all(c["rule"][k] == v for k, v in rule.items())]
        return sorted(found, key=lambda c: c["case_id"])[0]

    def test_unit_unexplained_needs_decomposable_within(self):  # 분류 5(분해 불가) 자료를 설명 안 됨으로
        self.assert_refused(lambda r: self.case(r, 5)["rule"].update(unit_value="unexplained"),
                            "설명 안 됨 사례인데 within+잔차가 기준 미만")

    def test_unit_hold_inconsistent_needs_broken_decomposition(self):  # 분류 2(분해 성립) 자료를 불일치 보류로
        self.assert_refused(lambda r: self.case(r, 2)["rule"].update(unit_value="hold_inconsistent"),
                            "불일치 보류 사례인데 부모·하위 대조나 분해가 성립한다")

    def test_unit_hold_inconsistent_data_without_mismatch(self):  # 자료 변이: 분류 5의 부모 덮어쓰기를 뺀다
        def drop_parent(rules: dict) -> None:
            for case in rules["cases"]:
                case["events"] = [e for e in case["events"] if e["type"] != "parent"]
        self.assert_refused(drop_parent, "불일치 보류 사례인데 부모·하위 대조나 분해가 성립한다")

    def test_share_unexplained_needs_complete_denominator(self):  # 분류 7(분모 < 대상국) 자료를 설명 안 됨으로
        self.assert_refused(lambda r: self.case(r, 7)["rule"].update(share="unexplained"),
                            "점유율 설명 안 됨 사례인데 분모가 상대국 합보다 작거나")

    def test_share_hold_inconsistent_needs_short_denominator(self):  # 분류 8(분모 완전) 자료를 분모 불완전 보류로
        self.assert_refused(lambda r: self.case(r, 8)["rule"].update(share="hold_inconsistent"),
                            "분모 불완전 보류 사례인데 분모가 대상국 금액보다 작은 달이 없다")

    def test_class3_needs_peer_co_movement(self):  # 비교국이 평소 수준인 분류 2 자료를 분류 3으로
        self.assert_refused(lambda r: self.case(r, 2).update(scenario_class=3), "비교국 동반 변화")

    def test_class9_needs_small_hs4_change(self):  # 대상 HS6가 그 나라 HS4의 대부분인 분류 10 자료를 분류 9로
        self.assert_refused(lambda r: self.case(r, 10).update(scenario_class=9), "범위 함정이 아니다")


class InstallPathTest(unittest.TestCase):
    """install 명령과 같은 순서(원천 → 수집기 SQLite → 단위 S2 빌드 → 단위 S3)를 임시 폴더에서 돌린다."""

    def test_committed_source_builds_to_recorded_hash(self):
        cases = json.loads((DEV20 / "input" / "cases.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            collector = dev20.materialize_collector(SNAPSHOT, DEV20 / "input" / "source" / "raw", Path(tmp) / "dev20")
            con = sqlite3.connect(f"{(collector / 'snapshot.sqlite').as_uri()}?mode=ro", uri=True)
            try:
                stamps = {row[0] for row in con.execute("SELECT timestamp FROM collection_receipt")}
            finally:
                con.close()
            self.assertEqual(stamps, {"2026-09-25T00:00:00+09:00"})
            db = Path(tmp) / "build.sqlite"
            built = dev20.build_and_verify(collector, PEER_FILE, "dev20",
                                           load_policy(cases["policy_version"]), db)
            self.assertEqual(built["normalized_sha256"], cases["snapshot_normalized_sha256"])
            snapshot = query.open_snapshot("dev20", path=db)
            self.assertEqual(snapshot.world("850432", "202406")["amount_usd"], 5600)  # 분모가 대상국보다 작은 달
            self.assertEqual(snapshot.children("850431", "XP", "202412")["observation_status"], "REQUEST_FAILED")
            # 합성 비교국 표(g0 규칙): 대상국을 뺀 다섯 나라가 2023년 부모 HS6 수입금액 내림차순(같으면 코드순)이다
            peers = [p["peer_id"] for p in snapshot.peers("850450", "XN", "g0")]
            self.assertEqual(sorted(peers), ["XL", "XM", "XO", "XP", "XQ"])
            sums = {q: sum(snapshot.parent("850450", q, f"2023{m:02d}")["amount_usd"] for m in range(1, 13))
                    for q in peers}
            self.assertEqual(peers, sorted(peers, key=lambda q: (-sums[q], q)))

    def test_materialize_refuses_existing_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "dev20"
            target.mkdir()
            with self.assertRaises(FileExistsError):
                dev20.materialize_collector(SNAPSHOT, DEV20 / "input" / "source" / "raw", target)

    def test_install_into_repo_copy(self):
        """임시 저장소 사본(커밋 파일만)에 install: 처음엔 .gitignore 대상 셋을 만들고, 다시 부르면 0건, 다른 raw는 멈춘다."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(DEV20, root / "eval" / "dev" / "dev20")
            (root / "data" / "snapshots" / "dev20").mkdir(parents=True)
            for name in ("manifest.json", "collection_log.json", "snapshot_hash.json", "snapshot_build.json"):
                shutil.copyfile(SNAPSHOT / name, root / "data" / "snapshots" / "dev20" / name)
            (root / "data" / "reference").mkdir()
            shutil.copyfile(PEER_FILE, root / "data" / "reference" / PEER_FILE.name)
            first = dev20.install(root)
            self.assertTrue(first["ok"], first)
            self.assertEqual(first["created"], ["raw/*.xml(102)", "snapshot.sqlite", "snapshot_build.sqlite"])
            self.assertEqual(dev20.install(root)["created"], [])
            raw = sorted((root / "data" / "snapshots" / "dev20" / "raw").glob("*.xml"))[0]
            raw.write_bytes(raw.read_bytes() + b" ")
            third = dev20.install(root)
            self.assertFalse(third["ok"])
            self.assertEqual(third["different_in_place"], [f"raw/{raw.name}"])


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
        rules["cases"][0]["events"].append({"type": "scale", "month": "202407", "who": ["XN"], "volume": "1",
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

    def test_unit_case_below_proposed_minimum_is_refused(self):
        with mock.patch.object(dev20, "PROPOSED_MIN_AMOUNT", 2000):  # 골든 사례의 부모 금액(720·900 USD)보다 크게
            self.assert_refused(golden_rules(), "policy_v1 제안 최소 기준")

    def test_rounding_rule_must_match_case_rule(self):
        with mock.patch.object(dev20, "ROUNDING_KG", Fraction(40)):  # 구간이 넓어져 구성효과 사례가 불안정이 된다
            self.assert_refused(golden_rules(), "반올림 불안정 규칙 후보(U4)의 판정이 판정 근거 규칙과 다르다")

    def test_conflicting_events_are_refused(self):
        rules = golden_rules()
        rules["cases"][0]["events"].append({"type": "exact", "month": "202403"})
        self.assert_refused(rules, "사건이 이미 있다")

    def test_malformed_events_are_refused(self):
        for event in ({"type": "exact", "month": "202403", "extra": 1},
                      {"type": "scale", "month": "202407", "who": ["XN"], "volume": Decimal("0.5"), "price": "1"},
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
