"""단위 S4(snapshot_fixture) 보조 시험: 합성 시험자료 controlled_fixture_v0.

setUpModule이 임시 폴더를 저장소 뿌리로 삼아(생성 규칙 파일만 복사) fixture.materialize로 정본 자리를 한 번 채운다. 저장소의
data/snapshots/·data/reference/·outputs/에는 쓰지 않는다. 시험 동안 단위 S2·S3·K3의 스냅샷 뿌리와 저장소 뿌리를 그
임시 폴더로 바꿔, snapshot_id만 주는 호출(자료 접근층·스냅샷 검증의 기본 경로)로 연다.

확인하는 것
- 커밋한 텍스트 원천(manifest.json, snapshot_hash.json, snapshot_build.json의 기록 키, 합성 비교국 표)이 다시 만든 것과
  바이트까지 같다(새 작업 폴더에서 materialize 한 번이면 같은 스냅샷이 된다).
- snapshot_id만으로 단위 S3(raw 대조 켬)이 통과하고 자료 접근층이 연다. CLI `tradesentry snapshot-verify
  --snapshot controlled_fixture_v0`도 종료 코드 0이다(--snapshot 값만 바꿔 교체되는 길).
- 관측 상태 5종이 수입 행에 각각 한 번 이상 있고, 빈칸마다 뜻한 상태가 나온다.
- 사례 A/B/C의 값이 oracle(eval/dev/oracle_ABC.json)의 입력과 같고, 지표 단위 X1~X3이 그 값에서 oracle 수치를 재현한다.
- 개발용 정책 dev-0.1 기준값으로 신호 발동(단위 P1)을 돌리면 사례 세 달만 발동한다.
- 합성 비교국 표가 단위 G1의 g0 규칙(같은 원천에 G1을 돌린 결과)과 바이트까지 같고, 사례의 비교국은 두 달 값이 있다.
- 다시 불러도 새로 쓰지 않고, 다른 파일이 있으면 덮지 않고 멈춘다.
- 생성 규칙·단위 파일·스냅샷에 기대 판정이나 시나리오 이름이 없다(정답과 입력의 분리).
"""
import contextlib
import io
import json
import re
import shutil
import sqlite3
import tempfile
import unittest
from datetime import datetime
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from unittest import mock

from tradesentry import ingest
from tradesentry.cli import dispatch
from tradesentry.contract import types
from tradesentry.contract.policy_load import load_policy
from tradesentry.dal import query
from tradesentry.grouping import g0
from tradesentry.metrics import decompose, share, unit_value
from tradesentry.policy import trigger
from tradesentry.snapshot import build, fixture, verify

REPO_ROOT = Path(__file__).resolve().parents[3]
ORACLE = REPO_ROOT / "eval" / "dev" / "oracle_ABC.json"
COMMITTED = REPO_ROOT / "data" / "snapshots" / fixture.SNAPSHOT_ID
COMMITTED_PEERS = REPO_ROOT / "data" / "reference" / fixture.PEER_GROUP_FILE
SID = fixture.SNAPSHOT_ID
ORACLE_CASE = {"A": "A-composition", "B": "B-residual", "C": "C-missing-hs10"}  # 이름표 → oracle case_id(시험에만 둔다)
FORBIDDEN = re.compile(r"\b(MAINTAIN|MONITOR|HOLD)\b|composition|residual|missing-hs10|모니터링|검토 유지|자료 보류|"
                       r"구성변화|잔존변화|자료누락")


def load_oracle() -> dict:
    return json.loads(ORACLE.read_text(encoding="utf-8"), parse_float=Decimal)


def make_root(base: Path) -> Path:
    """base를 저장소 뿌리로 보고 생성 규칙 파일만 정본 자리에 복사한다."""
    target = base / "data" / "snapshots" / SID
    target.mkdir(parents=True)
    shutil.copyfile(fixture.spec_path(), target / fixture.SPEC_FILE)
    return target


def quiet_materialize(root: Path, **kwargs) -> dict:
    with contextlib.redirect_stdout(io.StringIO()):
        return fixture.materialize(root, **kwargs)


_SHARED: dict = {}


def setUpModule():
    """모듈의 시험이 함께 쓰는 정본 자리를 한 번만 만든다(임시 폴더를 저장소 뿌리로 본다)."""
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    target = make_root(root)
    _SHARED.update(tmp=tmp, root=root, target=target, summary=quiet_materialize(root),
                   spec=fixture.load_spec(target / fixture.SPEC_FILE)[0])


def tearDownModule():
    _SHARED.pop("tmp").cleanup()
    _SHARED.clear()


class FixtureTestBase(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.root, self.target = _SHARED["root"], _SHARED["target"]
        self.summary, self.spec = _SHARED["summary"], _SHARED["spec"]
        self.cases = {case["label"]: case for case in self.spec["cases"]}
        snapshots = self.root / "data" / "snapshots"
        for module, name, value in ((build, "SNAPSHOTS_ROOT", snapshots), (build, "REPO_ROOT", self.root),
                                    (query, "SNAPSHOTS_ROOT", snapshots)):
            patcher = mock.patch.object(module, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def open(self) -> query.Snapshot:
        snap = query.open_snapshot(SID)  # snapshot_id만 준다(경로 없음)
        self.addCleanup(snap.close)
        return snap


class CommittedSourceTest(FixtureTestBase):
    def test_committed_text_sources_are_reproduced(self):
        for name in (fixture.SPEC_FILE, build.MANIFEST_FILE, build.HASH_FILE):
            self.assertEqual((self.target / name).read_bytes(), (COMMITTED / name).read_bytes(), name)
        self.assertEqual((self.root / "data" / "reference" / fixture.PEER_GROUP_FILE).read_bytes(),
                         COMMITTED_PEERS.read_bytes())
        committed = json.loads((COMMITTED / build.BUILD_RECORD).read_text(encoding="utf-8"))
        rebuilt = json.loads((self.target / build.BUILD_RECORD).read_text(encoding="utf-8"))
        for key in fixture.RECORD_KEYS + ("build_file",):
            self.assertEqual(rebuilt[key], committed[key], key)
        self.assertIsNone(committed["policy_version"])  # 승인된 정책이 아니라 생성 규칙의 승격(결정 기록 ⑦)
        self.assertEqual(committed["confirmed_no_trade_rule"], build.PROMOTION_RULE)

    def test_first_call_creates_every_canonical_file(self):
        shown = f"data/snapshots/{SID}"
        self.assertEqual(self.summary["created"], [
            f"{shown}/manifest.json", f"{shown}/snapshot_hash.json", f"data/reference/{fixture.PEER_GROUP_FILE}",
            f"{shown}/raw/*.xml(130)", f"{shown}/snapshot.sqlite", f"{shown}/snapshot_build.sqlite",
            f"{shown}/snapshot_build.json"])
        self.assertEqual(sorted(p.name for p in self.target.iterdir()),
                         sorted([fixture.SPEC_FILE, build.MANIFEST_FILE, build.HASH_FILE, build.RAW_DIR,
                                 build.COLLECTOR_DB, build.BUILD_FILE, build.BUILD_RECORD]))

    def test_manifest_is_the_collector_plan(self):
        manifest = json.loads((self.target / build.MANIFEST_FILE).read_text(encoding="utf-8"))
        self.assertEqual(manifest["requests"], ingest.build_manifest(manifest["config"]))
        self.assertEqual(manifest["config"], self.spec["collection_plan"])

    def test_collector_globals_are_restored(self):
        self.assertEqual(ingest.SNAP_DIR, Path(ingest.__file__).resolve().parents[2] / "data" / "snapshots")
        self.assertEqual(ingest.now_iso.__module__, ingest.__name__)
        self.assertEqual(ingest.now_iso.__name__, "now_iso")


class SwapBySnapshotIdTest(FixtureTestBase):
    def test_snapshot_verify_passes_with_raw_by_id_only(self):
        report = verify.run({"snapshot_id": SID})
        self.assertTrue(report["ok"], [c for c in report["checks"] if c["ok"] is False])
        checks = {c["name"]: c["ok"] for c in report["checks"]}
        for name in ("observation_matches_raw", "receipts_match_raw", "meta_matches_source", "raw_sha256",
                     "peer_group_sources", "normalized_sha256_record", "observation_rules", "coverage_hs10_children"):
            self.assertIs(checks[name], True, name)
        self.assertEqual(report["normalized_sha256"], self.summary["normalized_sha256"])

    def test_cli_snapshot_verify_takes_only_the_snapshot_option(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(dispatch, "OUTPUT_PARENT", Path(tmp)):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = dispatch.main(["snapshot-verify", "--snapshot", SID])  # 실스냅샷과 같은 명령, 값만 다르다
            self.assertEqual((code, err.getvalue()), (0, ""))
            [folder] = list(Path(tmp).iterdir())
            [report_file] = list(folder.iterdir())
            report = json.loads(report_file.read_text(encoding="utf-8"))
        self.assertIs(report["ok"], True)
        self.assertEqual(report["recorded_normalized_sha256"], self.summary["normalized_sha256"])

    def test_dal_opens_by_id_and_meta_is_the_contract_snapshot_object(self):
        obj = self.open().snapshot_object()
        self.assertEqual(set(obj), {"schema_version", *types.SNAPSHOT_KEYS})
        self.assertEqual((obj["schema_version"], obj["snapshot_id"], obj["source_kind"]), (1, SID, "controlled"))
        self.assertEqual(obj["normalized_sha256"], self.summary["normalized_sha256"])
        self.assertEqual(obj["collected_at"], self.spec["generated_at"])
        self.assertEqual(obj["source_url"], fixture.SOURCE_URL)  # 합성 자료는 생성 규칙의 저장소 상대경로(§2.3.1)
        self.assertEqual(obj["coverage_status"], "IN_PROGRESS")  # 수집기 기본값(v1은 값 집합을 정하지 않았다)
        self.assertEqual(obj["period"], {"start": "202201", "end": "202412"})
        self.assertEqual(obj["hs_version"], "HSK")

    def test_scope_is_three_hs6_ten_partners_thirty_six_months(self):
        scope = self.open().scope()
        self.assertEqual((len(scope["hs6"]), len(scope["partners"]), len(scope["months"])), (3, 10, 36))
        self.assertEqual(scope["other_partners"], [])
        for code in scope["partners"]:
            self.assertRegex(code, r"^[A-Z]{2}$")
        kcs = json.loads((REPO_ROOT / "data" / "reference" / "kcs_country_codes.json").read_text(encoding="utf-8"))
        assigned = {row[0] for row in kcs if isinstance(row, list) and row}
        self.assertFalse(set(scope["partners"]) & assigned)  # 어느 나라에도 배정되지 않은 합성 코드

    def test_out_of_scope_hs6_is_in_raw_but_not_queryable(self):
        snap = self.open()
        with self.assertRaises(query.ScopeError):
            snap.parent("850440", "XA", "202201")
        con = sqlite3.connect((self.target / build.BUILD_FILE).resolve().as_uri() + "?mode=ro", uri=True)
        self.addCleanup(con.close)
        found = con.execute("SELECT COUNT(*) FROM observation WHERE substr(hs_code, 1, 6) = '850440'").fetchone()[0]
        self.assertGreater(found, 0)  # 행 규칙 7: HS4 조회에는 오지만 분석 범위 밖


class ObservationStatusTest(FixtureTestBase):
    def test_all_five_statuses_appear_in_import_rows(self):
        counts = self.summary["import_observation_status"]
        self.assertEqual(set(counts), set(types.OBSERVATION_STATUSES))
        for status in types.OBSERVATION_STATUSES:
            self.assertGreaterEqual(counts[status], 1, status)

    def test_each_gap_reads_back_with_its_status(self):
        snap = self.open()
        self.assertEqual(snap.parent("850450", "XJ", "202205")["observation_status"], types.CONFIRMED_NO_TRADE)
        empty = snap.parent("850431", "XI", "202208")
        self.assertEqual((empty["observation_status"], empty["amount_usd"]), (types.UNRESOLVED_ZERO, None))
        self.assertEqual(empty["missingness"][0]["hs_code"], "8504")  # HS4 스캔이 빈 달(승격되지 않는다)
        zero = snap.parent("850431", "XH", "202210")
        self.assertEqual((zero["observation_status"], zero["amount_usd"], zero["net_weight_kg"]),
                         (types.OBSERVED, 0, 0))  # 수입 0이 명시된 달은 OBSERVED(값 0)
        self.assertEqual(snap.children("850432", "XC", "202201")["observation_status"], types.NOT_COLLECTED)
        failed = snap.children("850432", "XC", "202412")
        self.assertEqual((failed["observation_status"], failed["rows"]), (types.REQUEST_FAILED, []))


class OracleCaseTest(FixtureTestBase):
    def codes(self, hs6: str) -> dict[str, str]:
        hs10 = next(item["hs10"] for item in self.spec["hs6"] if item["code"] == hs6)
        return {"X1": hs10[0], "X2": hs10[1]}

    def test_spec_case_inputs_equal_oracle_inputs(self):
        oracle = load_oracle()
        self.assertEqual({c["case_id"] for c in oracle["cases"]}, set(ORACLE_CASE.values()))
        for label, case_id in ORACLE_CASE.items():
            want = next(c for c in oracle["cases"] if c["case_id"] == case_id)
            case, codes = self.cases[label], self.codes(self.cases[label]["hs6"])
            for side in ("baseline", "comparison"):
                self.assertEqual(case[side]["parent"], want[side]["parent"], f"{label} {side}")
                if isinstance(want[side].get("hs10"), str):
                    self.assertEqual(case[side]["hs10"], want[side]["hs10"])  # C: REQUEST_FAILED
                elif "hs10" in want[side]:
                    self.assertEqual(case[side]["hs10"], [{"code": codes[r["code"]], "V": r["V"], "Q": r["Q"]}
                                                          for r in want[side]["hs10"]], f"{label} {side}")
            share_want = want["expected"]["share"]
            self.assertEqual(case["world_usd"], {"baseline": share_want["V_world_0"],
                                                 "comparison": share_want["V_world_1"]})

    def test_case_values_read_back_through_dal(self):
        snap, oracle = self.open(), load_oracle()
        for label, case_id in ORACLE_CASE.items():
            want = next(c for c in oracle["cases"] if c["case_id"] == case_id)
            case, codes = self.cases[label], self.codes(self.cases[label]["hs6"])
            hs6, partner, base, month = case["hs6"], case["partner"], case["baseline_month"], case["month"]
            parents = snap.parent_series(hs6, partner, [base, month])
            self.assertEqual([(v["amount_usd"], v["net_weight_kg"], v["observation_status"]) for v in parents],
                             [(want[s]["parent"]["V"], want[s]["parent"]["Q"], types.OBSERVED)
                              for s in ("baseline", "comparison")])
            world = snap.world_series(hs6, [base, month])
            self.assertEqual([v["amount_usd"] for v in world],
                             [want["expected"]["share"]["V_world_0"], want["expected"]["share"]["V_world_1"]])
            for side, when in (("baseline", base), ("comparison", month)):
                kids = snap.children(hs6, partner, when)
                if isinstance(want[side].get("hs10"), list):
                    self.assertEqual([(r["hs10"], r["amount_usd"], r["net_weight_kg"]) for r in kids["rows"]],
                                     [(codes[r["code"]], r["V"], r["Q"]) for r in want[side]["hs10"]])
                elif isinstance(want[side].get("hs10"), str):
                    self.assertEqual((kids["observation_status"], kids["rows"]), (want[side]["hs10"], []))
                else:  # C의 기준월 HS10은 oracle에 없다. 합성 자료가 부모와 맞는 두 행을 둔다(MT3 요구)
                    self.assertEqual(kids["observation_status"], types.OBSERVED)
                    self.assertEqual(sum(r["amount_usd"] for r in kids["rows"]), want[side]["parent"]["V"])
                    self.assertEqual(sum(r["net_weight_kg"] for r in kids["rows"]), want[side]["parent"]["Q"])

    def test_metrics_units_reproduce_oracle_from_the_fixture(self):
        snap, oracle = self.open(), load_oracle()
        rounding = load_policy("dev-0.1")["tolerance"]["weight_rounding_kg"]
        for label, case_id in ORACLE_CASE.items():
            want = next(c for c in oracle["cases"] if c["case_id"] == case_id)["expected"]
            case = self.cases[label]
            hs6, partner, base, month = case["hs6"], case["partner"], case["baseline_month"], case["month"]
            target = {"snapshot_id": SID, "hs6": hs6, "partner": partner, "period": month, "baseline_period": base}
            parent, world, children = metric_rows(snap, hs6, partner, [base, month])
            outputs = [unit_value.run({**target, "parent": parent}),
                       share.run({**target, "parent": parent, "world": world}),
                       decompose.run({**target, "parent": parent, "children": children,
                                      "weight_rounding_kg": rounding})]
            found = {(m["inputs"]["metric"], m["inputs"]["partner"], m["inputs"]["period"]): m["value"]
                     for out in outputs for m in out["metrics"]}
            got = {"U0": found[("U", partner, base)], "U1": found[("U", partner, month)],
                   "r_U": found[("r_U", partner, month)], "within": found[("within_effect", partner, month)],
                   "mix": found[("mix_effect", partner, month)], "residual": found[("residual", partner, month)],
                   "V_country_0": found[("V", partner, base)], "V_country_1": found[("V", partner, month)],
                   "V_world_0": found[("V", "ALL", base)], "V_world_1": found[("V", "ALL", month)],
                   "s0_pp": found[("s", partner, base)], "s1_pp": found[("s", partner, month)],
                   "d_s_pp": found[("d_s", partner, month)]}
            expected = {**want["unit_value"], **{k: v for k, v in want["share"].items()
                                                 if k not in ("triggered", "threshold_pp")}}
            for key, value in expected.items():
                with self.subTest(case=case_id, field=key):
                    if value is None:
                        self.assertIsNone(got[key])  # C의 within·mix는 null 그대로
                    else:
                        self.assertEqual(Decimal(got[key]), Decimal(value) * (100 if key == "r_U" else 1))
            for out in outputs:
                for metric in out["metrics"]:
                    for evidence in metric["evidence_ids"]:
                        self.assertTrue(snap.resolve(evidence)["resolved"], evidence)


def metric_rows(snap: query.Snapshot, hs6: str, partner: str, months: list[str]) -> tuple[list, list, list]:
    """자료 접근층 출력을 지표 단위 입력(역할별 관측 행)으로 옮긴다(조립 AS1 어댑터가 할 일을 시험에서 따로 한다)."""
    parent = [{"month": v["month"], "hs_code": hs6, "observation_status": v["observation_status"],
               "amount_usd": v["amount_usd"], "net_weight_kg": v["net_weight_kg"], "evidence_ids": v["evidence_ids"]}
              for v in snap.parent_series(hs6, partner, months)]
    world = []
    for value in snap.world_series(hs6, months):
        for evidence in value["evidence_ids"]:
            row = snap.resolve(evidence)["row"]
            world.append({"month": row["month"], "hs_code": row["hs_code"], "partner_code": row["partner_code"],
                          "observation_status": row["observation_status"], "amount_usd": row["amount_usd"],
                          "net_weight_kg": row["net_weight_kg"], "evidence_ids": [evidence]})
    children = []
    for month in months:
        kids = snap.children(hs6, partner, month)
        if kids["rows"]:
            children += [{"month": month, "hs_code": r["hs10"], "observation_status": types.OBSERVED,
                          "amount_usd": r["amount_usd"], "net_weight_kg": r["net_weight_kg"],
                          "evidence_ids": [r["evidence_id"]]} for r in kids["rows"]]
        else:
            children += [{"month": month, "hs_code": e["hs_code"], "observation_status": e["observation_status"],
                          "amount_usd": None, "net_weight_kg": None, "evidence_ids": [e["evidence_id"]]}
                         for e in kids["missingness"]]
    return parent, world, children


class DetectionTest(FixtureTestBase):
    def test_only_the_three_case_months_trigger_under_dev_policy(self):
        snap = self.open()
        rows = []
        for hs6 in snap.hs6_codes:
            world = {v["month"]: v["amount_usd"] for v in snap.world_series(hs6)}
            for partner in snap.partners:
                series = {v["month"]: v for v in snap.parent_series(hs6, partner)}
                for month in snap.months[12:]:  # 전년동월 판정이 가능한 2023-01~2024-12
                    base = f"{int(month[:4]) - 1}{month[4:]}"
                    rows.append({"hs6": hs6, "partner": partner, "month": month, "baseline_month": base,
                                 **exact_changes(series[base], series[month], world[base], world[month])})
        self.assertEqual(len(rows), 3 * 10 * 24)
        detection = trigger.run({"policy": load_policy("dev-0.1"), "rows": rows})
        fired = {(f"{t['hs6']}-{t['partner']}-{t['month']}", signal) for t in detection["triggers"]
                 for signal, state in t["signals"].items() if state == "TRIGGERED"}
        self.assertEqual(fired, {(c["case_id"], "unit_value") for c in fixture.case_list(self.spec)})
        nulls = {(q["hs6"], q["partner"], q["month"]) for q in detection["data_quality"]}
        self.assertIn(("850450", "XJ", "202305"), nulls)  # 기준월이 무거래 확정(단가 없음)
        self.assertIn(("850431", "XI", "202308"), nulls)  # 기준월이 빈 달


def exact_changes(base: dict, current: dict, world_base: int, world_current: int) -> dict:
    """r_U(%)·d_s(pp)의 반올림 전 정확값(자료 계약 §11.1·§11.2·§3.4). 값이 없으면 None."""
    def value(v: dict) -> tuple[int | None, int | None]:
        if v["observation_status"] == types.CONFIRMED_NO_TRADE:
            return 0, 0
        if v["observation_status"] == types.OBSERVED:
            return v["amount_usd"], v["net_weight_kg"]
        return None, None

    (v0, q0), (v1, q1) = value(base), value(current)
    u0 = None if v0 is None or not q0 else Fraction(v0, q0)
    u1 = None if v1 is None or not q1 else Fraction(v1, q1)
    r_u = None if u0 is None or u1 is None or u0 == 0 else (u1 / u0 - 1) * 100
    d_s = None if v0 is None or v1 is None else (Fraction(v1, world_current) - Fraction(v0, world_base)) * 100
    return {"r_U": r_u, "d_s": d_s}


class PeerGroupTest(FixtureTestBase):
    def test_peer_table_equals_unit_g1_g0_rule_on_the_same_source(self):
        inp = g0.load_input(self.target, k=self.spec["peer_group"]["k"],
                            source_year=self.spec["peer_group"]["source_year"],
                            generated_at=self.spec["generated_at"])
        self.assertEqual(g0.run(inp).encode("utf-8"),
                         (self.root / "data" / "reference" / fixture.PEER_GROUP_FILE).read_bytes())

    def test_case_peers_have_both_case_months(self):
        snap = self.open()
        for case in self.spec["cases"]:
            peers = snap.peers(case["hs6"], case["partner"], "g0")
            self.assertEqual([p["peer_rank"] for p in peers], [1, 2, 3, 4, 5])
            for peer in peers:
                self.assertEqual((peer["source_version"], peer["baci_country_code"], peer["similarity"]),
                                 (SID, None, None))
                for value in snap.parent_series(case["hs6"], peer["peer_id"], [case["baseline_month"], case["month"]]):
                    self.assertEqual(value["observation_status"], types.OBSERVED)
                    self.assertGreater(value["amount_usd"], 0)


class MaterializeTest(FixtureTestBase):
    def test_second_call_writes_nothing(self):
        later = quiet_materialize(self.root, clock=lambda: datetime(2026, 9, 25, 3, 0, 0, tzinfo=types.KST))
        self.assertEqual(later["created"], [])
        self.assertEqual(later["normalized_sha256"], self.summary["normalized_sha256"])

    def test_refuses_to_overwrite_a_different_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = make_root(Path(tmp))
            (target / build.MANIFEST_FILE).write_bytes(b"{}\n")
            with self.assertRaises(fixture.FixtureError):
                quiet_materialize(Path(tmp))
            self.assertEqual((target / build.MANIFEST_FILE).read_bytes(), b"{}\n")
            self.assertEqual(sorted(p.name for p in target.iterdir()), [fixture.SPEC_FILE, build.MANIFEST_FILE])
            self.assertFalse((Path(tmp) / "data" / "reference").exists())

    def test_rejects_stale_collector_db_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = make_root(Path(tmp))
            sqlite3.connect(target / build.COLLECTOR_DB).close()  # 빈 SQLite(표 없음)
            with self.assertRaises(fixture.FixtureError):
                quiet_materialize(Path(tmp))
            self.assertEqual(sorted(p.name for p in target.iterdir()), [fixture.SPEC_FILE, build.COLLECTOR_DB])

    def test_rejects_stale_build_file_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = make_root(Path(tmp))
            con = sqlite3.connect(target / build.BUILD_FILE)
            con.execute("CREATE TABLE snapshot_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            con.close()
            with self.assertRaises(fixture.FixtureError):  # 표가 모자라 normalized_sha256이 다르다
                quiet_materialize(Path(tmp))
            self.assertEqual(sorted(p.name for p in target.iterdir()), [fixture.SPEC_FILE, build.BUILD_FILE])
            self.assertFalse((Path(tmp) / "data" / "reference").exists())


class InputAndSeparationTest(FixtureTestBase):
    def test_run_input_forms(self):
        with self.assertRaises(ValueError):
            fixture.run({"spec_file": "x", "spec": {}})
        bad = json.loads(json.dumps(self.spec))
        bad["collection_plan"]["partners"][0] = "x1"
        bad["partners"]["x1"] = bad["partners"].pop("XA")
        with self.assertRaises(fixture.FixtureError):
            fixture.run({"spec": bad})

    def test_no_expected_status_or_scenario_name_in_fixture_inputs(self):
        for path in (fixture.spec_path(), Path(fixture.__file__), COMMITTED / build.MANIFEST_FILE, COMMITTED_PEERS):
            self.assertIsNone(FORBIDDEN.search(path.read_text(encoding="utf-8")), path.name)
        con = sqlite3.connect((self.target / build.BUILD_FILE).resolve().as_uri() + "?mode=ro", uri=True)
        self.addCleanup(con.close)
        for table in build.HASH_TABLES:
            for row in con.execute(f'SELECT * FROM "{table}"'):
                for value in row:
                    if isinstance(value, str):
                        self.assertIsNone(FORBIDDEN.search(value), f"{table}: {value[:40]}")


if __name__ == "__main__":
    unittest.main()
