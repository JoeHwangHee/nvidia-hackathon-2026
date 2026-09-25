"""조립 작업 AS1: tradesentry detect 조립 시험(명령 하나를 처음부터 끝까지 돌려 기대 출력과 비교한다). 대역 없이 실제 단위로
돈다. 다만 배선 계약 위반(종료 코드 4) 시험 셋은 단위 P2·K3 world_series·X1의 출력을 대역으로 일부러 어긋나게 한다. 네트워크와
키 없이 돈다.

- 실제로 도는 것: CLI 인자 검증(단위 F1) → 명령 배선(단위 F2의 detect) → 단위 K4 load_policy(저장소의
  configs/policy_dev.json, dev-0.1) → 단위 K3(정본 빌드를 읽기 전용으로 연다) → 어댑터 → 단위 X1·X2(X4) → 단위 P1 → 단위 P2
  → 출력 파일.
- 자료: tests/units/F2/detect_fixture.py가 수집기 코드와 단위 S2로 만든 합성 스냅샷(source_kind controlled). 실제 통계가
  아니다. 실자료 시험(real_dev 좁히기·분할 기록 거부)은 같은 본 스냅샷을 source_kind real로 만든 것(값은 합성, 출처 종류만
  real)과 임시 파일의 합성 분할 기록을 쓴다. 실자료 스냅샷 v1·v2로는 돌리지 않는다.
- 바꾸는 것은 위치 넷뿐이다: 스냅샷들의 뿌리(dal.query.SNAPSHOTS_ROOT), CLI 실행 폴더의 부모(dispatch.OUTPUT_PARENT, detect를
  부를 때마다 새 폴더), 최소 기준 시험의 정책 폴더(contract.policy_load.CONFIGS_DIR), 실자료 시험의 분할 기록 대응표
  (dispatch.REAL_SPLIT_FILES). 모두 임시 폴더다. 저장소의 data/·
  outputs/·configs/는 건드리지 않는다.
- 경계(DT2 결정 ②·AS1 항목, MT1 결정 ②): r_U 정확값 −29.96%(표시 −30.0)는 미발동, 정확히 −30%는 발동, d_s 정확값
  9.96pp(표시 10.0)는 미발동, 정확히 10pp는 발동이다. 단위 P1은 반올림 전 정확값(Fraction)을 받는다.
"""
import contextlib
import io
import json
import tempfile
import unittest
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from unittest import mock

from tradesentry.cli import dispatch
from tradesentry.contract import policy_load
from tradesentry.dal import query
from tradesentry.metrics import rounding, share, unit_value
from tradesentry.policy import case_build, trigger

from . import detect_fixture as df

ROOT = Path(__file__).resolve().parents[3]
T, N = "TRIGGERED", "NOT_TRIGGERED"
BASELINE = {"202401": "202301", "202402": "202302"}
MAIN_ID = df.MAIN["config"]["snapshot_id"]
GAP_ID = df.WORLD_GAP["config"]["snapshot_id"]
DETECT_FILE_DOMAIN = "policy_case_build"  # 출력 파일 도메인명: docs/plan/UNITS.md §3.4 P2 행 글자 그대로(코드 상수를 쓰지 않는다)
ORACLE_OF = {"CN": "A-composition", "JP": "B-residual", "DE": "C-missing-hs10"}  # 합성 계열 ↔ oracle 사례


def call(argv: list[str]) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = dispatch.main(argv)
    return code, out.getvalue(), err.getvalue()


def case(partner: str, month: str, unit_value_trigger: str, share_trigger: str, *, snapshot_id: str = MAIN_ID,
         policy_version: str = "dev-0.1") -> dict:
    """단위 P2의 사례 객체(자료 계약 §2.3.5의 8필드 + scope)."""
    scope = {"hs6": df.HS6, "partner": partner, "month": month, "baseline_month": BASELINE[month]}
    return {"case_id": f"{df.HS6}-{partner}-{month}", **scope,
            "signals": {"unit_value": unit_value_trigger, "share": share_trigger}, "snapshot_id": snapshot_id,
            "policy_version": policy_version, "scope": dict(scope)}


def quality(partner: str, month: str, signal: str, reason: str = "metric_null") -> dict:
    """단위 P1의 데이터 품질 목록 행."""
    return {"hs6": df.HS6, "partner": partner, "month": month, "baseline_month": BASELINE[month], "signal": signal,
            "reason": reason}


# 조립 시험의 기대 출력(본 스냅샷, dev-0.1). 계열 설계는 detect_fixture.py 머리말에 있다.
EXPECTED = {
    "snapshot_id": MAIN_ID, "dataset": None, "policy_version": "dev-0.1",
    "cases": [case("CN", "202401", T, N), case("DE", "202401", T, N), case("FI", "202402", N, T),
              case("JP", "202401", T, N), case("TW", "202402", N, T), case("US", "202402", T, N)],
    "data_quality": [quality("FI", "202402", "unit_value"),  # 무거래 확정 달: 단가 null(점유율은 0%로 계산됨)
                     quality("FR", "202401", "share"), quality("FR", "202401", "unit_value"),  # HS4 스캔 실패
                     quality("FR", "202402", "share"), quality("FR", "202402", "unit_value"),
                     quality("SE", "202402", "unit_value")],  # 기준월 중량 0
}

# 최소 기준이 있는 시험 정책(dev-9.8). 실제 정책이 아니다. 단가 신호에만 적용된다(MT1 결정 ③, 잠정 U2).
MIN_POLICY = {"_status": "시험용 정책(최소 기준 있음). 실제 정책이 아니다", "schema_version": 1,
              "policy_version": "dev-9.8", "thresholds": {"unit_value": 30, "share": 10}, "min_amount": 400,
              "min_weight": 8, "tolerance": {"amount_usd": 0, "weight_rounding_kg": 0.5}, "confirmed_no_trade": None}
EXPECTED_MIN = {
    "snapshot_id": MAIN_ID, "dataset": None, "policy_version": "dev-9.8",
    "cases": [case("FI", "202402", N, T, policy_version="dev-9.8"), case("TW", "202402", N, T, policy_version="dev-9.8")],
    "data_quality": [quality("CN", "202401", "unit_value", "below_min_amount"),  # 비교월 금액 360 < 400
                     quality("DE", "202401", "unit_value", "below_min_amount"),
                     quality("FI", "202402", "unit_value"),
                     quality("FR", "202401", "share"), quality("FR", "202401", "unit_value"),
                     quality("FR", "202402", "share"), quality("FR", "202402", "unit_value"),
                     quality("JP", "202401", "unit_value", "below_min_amount"),
                     quality("SE", "202402", "unit_value"),
                     quality("US", "202402", "unit_value", "below_min_weight")],  # 기준월 중량 7 < 8
}


class DetectCase(unittest.TestCase):
    """스냅샷은 시험 클래스마다 한 번 빌드한다. detect는 부를 때마다 새 실행 폴더 부모를 쓴다(같은 초 다툼으로 기다리지 않게)."""

    SPEC = df.MAIN
    BUILD_POLICY: dict | None = df.PROMOTION_POLICY
    SOURCE_KIND = "controlled"
    PEER_ROWS: list[dict] | None = None
    snapshots: Path

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        folder = tempfile.TemporaryDirectory()
        cls.addClassCleanup(folder.cleanup)
        cls.snapshots = df.install(Path(folder.name), cls.SPEC, source_kind=cls.SOURCE_KIND,
                                   build_policy=cls.BUILD_POLICY, peer_rows=cls.PEER_ROWS)

    def setUp(self):
        super().setUp()
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.count = 0
        patcher = mock.patch.object(query, "SNAPSHOTS_ROOT", self.snapshots)
        patcher.start()
        self.addCleanup(patcher.stop)

    def detect(self, *, snapshot: str | None = None, policy: str = "dev-0.1") -> tuple[int, str, str, Path]:
        """detect를 한 번 부르고 (종료 코드, 표준 출력, 표준 오류, 확보한 실행 폴더)를 돌려준다."""
        self.count += 1
        outputs = self.root / f"outputs{self.count}"
        argv = ["detect", "--snapshot", snapshot or self.SPEC["config"]["snapshot_id"], "--policy", policy]
        with mock.patch.object(dispatch, "OUTPUT_PARENT", outputs):
            code, out, err = call(argv)
        [run_dir] = list(outputs.iterdir())  # 실행명은 단위를 부르기 전에 하나만 확보한다(N8)
        self.assertRegex(run_dir.name, r"^detect-[0-9]{12}$")
        return code, out, err, run_dir

    def output(self, run_dir: Path, out: str) -> dict:
        """실행 폴더의 출력 파일 하나(policy_case_build-{시각}.json)를 읽는다. 표준 출력은 그 상대경로 한 줄이다."""
        stamp = run_dir.name.split("-", 1)[1]
        name = f"{DETECT_FILE_DOMAIN}-{stamp}.json"
        self.assertEqual(sorted(p.name for p in run_dir.iterdir()), [name])
        self.assertEqual(out, f"outputs/{run_dir.name}/{name}\n")
        text = (run_dir / name).read_text(encoding="utf-8")
        for local in (str(self.root), str(self.snapshots), str(self.snapshots.resolve()), str(ROOT)):
            self.assertNotIn(local, text)  # 로컬 절대경로를 쓰지 않는다(N13)
        return json.loads(text)


class DetectAssemblyTest(DetectCase):
    def test_detect_writes_the_expected_case_list(self):
        """조립 시험: 합성 스냅샷 전체를 detect로 돌려 단위 P2 출력을 기대 출력과 비교한다."""
        code, out, err, run_dir = self.detect()
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(self.output(run_dir, out), EXPECTED)

    def test_oracle_series_trigger_like_the_oracle(self):
        """oracle A·B·C의 부모 값을 가진 계열의 발동 여부가 oracle 기대(signals)와 같다."""
        oracle = json.loads((ROOT / "eval" / "dev" / "oracle_ABC.json").read_text(encoding="utf-8"))
        expected = {item["case_id"]: item["expected"]["signals"] for item in oracle["cases"]}
        code, out, err, run_dir = self.detect()
        self.assertEqual((code, err), (0, ""))
        found = {c["partner"]: c for c in self.output(run_dir, out)["cases"] if c["month"] == "202401"}
        for partner, oracle_id in ORACLE_OF.items():
            with self.subTest(partner=partner, oracle=oracle_id):
                self.assertEqual(found[partner]["signals"], expected[oracle_id])
        self.assertEqual(set(found), set(ORACLE_OF))  # 202401의 사례는 oracle 계열뿐이다(중립 계열은 사례가 아니다)

    def test_p1_gets_exact_values_not_display_values(self):
        """단위 P1 입력은 X1·X2의 반올림 전 정확값(Fraction)이다. 표시 값이었다면 VN·PH가 발동했을 경계다."""
        with mock.patch.object(trigger, "run", wraps=trigger.run) as p1:
            code, _, err, _ = self.detect()
        self.assertEqual((code, err), (0, ""))
        [p1_call] = p1.call_args_list
        rows = {(row["partner"], row["month"]): row for row in p1_call.args[0]["rows"]}
        self.assertEqual(len(rows), 20)  # 계열 10개 × 비교월 2개
        checks = ((("VN", "202402"), "r_U", Fraction(-2996, 100), Decimal("-30.0")),  # 정확 −29.96: 미발동
                  (("US", "202402"), "r_U", Fraction(-30), Decimal("-30.0")),  # 정확히 −30: 발동
                  (("PH", "202402"), "d_s", Fraction(996, 100), Decimal("10.0")),  # 정확 9.96: 미발동
                  (("TW", "202402"), "d_s", Fraction(10), Decimal("10.0")),  # 정확히 10: 발동(분모가 두 배면 5)
                  (("CN", "202401"), "d_s", Fraction(-4), Decimal("-4.0")),  # oracle A: 분모 중복 제거(두 배면 −2)
                  (("CN", "202401"), "r_U", Fraction(-40), Decimal("-40.0")),
                  (("FI", "202402"), "d_s", Fraction(-12), Decimal("-12.0")))  # 무거래 확정 달의 점유율 0%
        for key, symbol, exact, shown in checks:
            with self.subTest(series=key, metric=symbol):
                value = rows[key][symbol]
                self.assertIs(type(value), Fraction)
                self.assertEqual(value, exact)
                self.assertEqual(rounding.display(symbol, value), shown)
        for key, symbol in ((("FI", "202402"), "r_U"), (("SE", "202402"), "r_U"), (("FR", "202401"), "r_U"),
                            (("FR", "202401"), "d_s")):
            self.assertIsNone(rows[key][symbol])
        self.assertEqual((rows[("CN", "202401")]["amount_usd"], rows[("CN", "202401")]["net_weight_kg"]),
                         ({"month": 360, "baseline_month": 600}, {"month": 100, "baseline_month": 100}))
        self.assertNotIn("amount_usd", rows[("FR", "202401")])  # 부모 값이 없는 달은 옮기지 않는다(r_U가 null)

    def test_min_amount_and_min_weight_reach_p1(self):
        """정책의 min_amount·min_weight가 있으면 P1이 어댑터가 옮긴 부모 HS6 금액·중량으로 단가 신호를 거른다."""
        configs = self.root / "configs"
        configs.mkdir()
        (configs / policy_load.POLICY_DEV_FILE).write_text(json.dumps(MIN_POLICY, ensure_ascii=False), encoding="utf-8")
        with mock.patch.object(policy_load, "CONFIGS_DIR", configs):
            code, out, err, run_dir = self.detect(policy="dev-9.8")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(self.output(run_dir, out), EXPECTED_MIN)

    def test_assembly_units_are_called(self):
        """조립 점검 2단계(실행 커버리지): detect 한 번에 조립체 2의 단위(X1·X2·X4·P1·P2)와 K3·K4가 실제로 불린다."""
        spies = {
            "K4 load_policy": mock.patch.object(policy_load, "load_policy", wraps=policy_load.load_policy),
            "K3 open_snapshot": mock.patch.object(query, "open_snapshot", wraps=query.open_snapshot),
            "K3 parent_series": mock.patch.object(query.Snapshot, "parent_series", autospec=True,
                                                  side_effect=query.Snapshot.parent_series),
            "K3 world_series": mock.patch.object(query.Snapshot, "world_series", autospec=True,
                                                 side_effect=query.Snapshot.world_series),
            "K3 resolve": mock.patch.object(query.Snapshot, "resolve", autospec=True, side_effect=query.Snapshot.resolve),
            "X1 run": mock.patch.object(unit_value, "run", wraps=unit_value.run),
            "X1 exact_value": mock.patch.object(unit_value, "exact_value", wraps=unit_value.exact_value),
            "X2 run": mock.patch.object(share, "run", wraps=share.run),
            "X2 exact_value": mock.patch.object(share, "exact_value", wraps=share.exact_value),
            "X4 metric": mock.patch.object(rounding, "metric", wraps=rounding.metric),
            "P1 run": mock.patch.object(trigger, "run", wraps=trigger.run),
            "P2 run": mock.patch.object(case_build, "run", wraps=case_build.run),
        }
        with contextlib.ExitStack() as stack:
            mocks = {name: stack.enter_context(patcher) for name, patcher in spies.items()}
            code, _, err, _ = self.detect()
        self.assertEqual((code, err), (0, ""))
        # 계열 10개 × 비교월 2개 = 20번. K3는 계열마다 parent_series 한 번, HS6마다 world_series 한 번이고, ALL 행은
        # HS6·달(4달 × HS10 2개)마다 한 번만 근거 ID를 푼다. X4 metric은 X1이 3개, X2가 7개씩 만든다.
        self.assertEqual({name: m.call_count for name, m in mocks.items()},
                         {"K4 load_policy": 1, "K3 open_snapshot": 1, "K3 parent_series": 10, "K3 world_series": 1,
                          "K3 resolve": 8, "X1 run": 20, "X1 exact_value": 20, "X2 run": 20, "X2 exact_value": 20,
                          "X4 metric": 200, "P1 run": 1, "P2 run": 1})

    def test_case_build_output_shape_is_checked(self):
        """단위 P2 출력이 기대한 모양이 아니면 배선 계약 위반(4)이고 출력 파일을 쓰지 않는다."""
        with mock.patch.object(case_build, "run", return_value={"cases": []}):
            code, out, err, run_dir = self.detect()
        self.assertEqual((code, out), (dispatch.EXIT_WIRING, ""))
        self.assertIn("배선 계약 위반", err)
        self.assertEqual(list(run_dir.iterdir()), [])

    def test_world_rebuild_mismatch_is_a_wiring_error(self):
        """ALL 근거 행으로 다시 만든 HS10 행의 금액 합이 K3 world 값과 다르면 배선 계약 위반(4)이고 출력 파일을 쓰지 않는다.
        K3 world_series의 OBSERVED 금액만 두 배로 바꾸고 근거 ID·코드 목록은 그대로 둔다."""
        real_world_series = query.Snapshot.world_series  # 대역을 걸기 전의 진짜(대역 안에서 부른다)

        def doubled(snap, *args, **kwargs):
            values = real_world_series(snap, *args, **kwargs)
            return [{**v, "amount_usd": v["amount_usd"] * 2} if v["observation_status"] == "OBSERVED" else v
                    for v in values]

        with mock.patch.object(query.Snapshot, "world_series", autospec=True, side_effect=doubled) as world, \
                mock.patch.object(trigger, "run", wraps=trigger.run) as p1:
            code, out, err, run_dir = self.detect()
        self.assertGreater(world.call_count, 0)
        self.assertEqual((code, out), (dispatch.EXIT_WIRING, ""))
        self.assertIn("배선 계약 위반", err)
        self.assertIn("K3 world", err)
        self.assertEqual(p1.call_count, 0)  # 지표·판정 전에 멈춘다
        self.assertEqual(list(run_dir.iterdir()), [])

    def test_metric_symbol_must_appear_exactly_once(self):
        """지표 단위 출력에 P1에 넘길 기호(r_U)가 없거나 둘이면 배선 계약 위반(4)이고 출력 파일을 쓰지 않는다."""
        real_x1 = unit_value.run  # 대역을 걸기 전의 진짜(대역 안에서 부른다)

        def without_r_u(inp):
            output = real_x1(inp)
            return {**output, "metrics": [m for m in output["metrics"] if m["inputs"].get("metric") != "r_U"]}

        def twice_r_u(inp):
            output = real_x1(inp)
            return {**output, "metrics": output["metrics"] + [m for m in output["metrics"]
                                                             if m["inputs"].get("metric") == "r_U"]}

        for name, fake in (("missing", without_r_u), ("duplicated", twice_r_u)):
            with self.subTest(r_U=name):
                with mock.patch.object(unit_value, "run", side_effect=fake) as x1, \
                        mock.patch.object(trigger, "run", wraps=trigger.run) as p1:
                    code, out, err, run_dir = self.detect()
                self.assertGreater(x1.call_count, 0)
                self.assertEqual((code, out), (dispatch.EXIT_WIRING, ""))
                self.assertIn("배선 계약 위반", err)
                self.assertIn("r_U 지표가 하나가 아니다", err)
                self.assertEqual(p1.call_count, 0)
                self.assertEqual(list(run_dir.iterdir()), [])

    def test_policy_error_stops_before_the_snapshot(self):
        """정책을 읽지 못하면 스냅샷을 열지 않고 1로 끝난다. 오류 문장에는 받은 값을 넣지 않는다."""
        empty = self.root / "no_configs"
        empty.mkdir()
        with mock.patch.object(policy_load, "CONFIGS_DIR", empty), \
                mock.patch.object(query, "open_snapshot", wraps=query.open_snapshot) as opened:
            code, out, err, run_dir = self.detect()
        self.assertEqual((code, out), (dispatch.EXIT_FAILED, ""))
        self.assertIn("PolicyError", err)
        self.assertNotIn("dev-0.1", err)
        self.assertEqual(opened.call_count, 0)
        self.assertEqual(list(run_dir.iterdir()), [])  # 확보한 빈 실행 폴더만 남는다

    def test_missing_snapshot(self):
        code, out, err, run_dir = self.detect(snapshot="no_such_snapshot")
        self.assertEqual((code, out), (dispatch.EXIT_FAILED, ""))
        self.assertIn("SnapshotError", err)
        self.assertNotIn("no_such_snapshot", err)
        self.assertEqual(list(run_dir.iterdir()), [])


class WorldGapTest(DetectCase):
    """ALL 분모가 빠진 달(품목별 API 요청 실패)은 점유율 지표가 null이고 데이터 품질 목록에 남는다. 단가 신호는 그대로 돈다."""

    SPEC = df.WORLD_GAP
    BUILD_POLICY = None

    def test_missing_all_denominator_leaves_share_null(self):
        code, out, err, run_dir = self.detect()
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(self.output(run_dir, out), {
            "snapshot_id": GAP_ID, "dataset": None, "policy_version": "dev-0.1",
            "cases": [case("CN", "202401", T, N, snapshot_id=GAP_ID)],
            "data_quality": [quality("CN", "202401", "share"), quality("CN", "202402", "share")]})


class OtherPartnerTest(DetectCase):
    """비교국 표가 가리키는 계획 밖 국가(K3 scope의 other_partners)는 탐지 계열에 넣지 않는다. 계열은 수집 설정의 HS6 × 상대국."""

    SPEC = df.OTHER_PARTNER
    BUILD_POLICY = None
    PEER_ROWS = df.OTHER_PEER_ROWS

    def test_out_of_plan_peer_is_not_a_detection_series(self):
        with query.open_snapshot(df.OTHER_PARTNER["config"]["snapshot_id"]) as snap:
            # 시험이 공허하지 않다: 계획 밖 국가가 스냅샷에 있고, K3가 그 국가의 부모 값을 조회할 수 있다
            self.assertEqual(snap.scope()["other_partners"], [df.OTHER_PEER])
            self.assertEqual(len(snap.parent_series(df.HS6, df.OTHER_PEER)), len(snap.months))
        with mock.patch.object(trigger, "run", wraps=trigger.run) as p1:
            code, out, err, run_dir = self.detect()
        self.assertEqual((code, err), (0, ""))
        [p1_call] = p1.call_args_list
        self.assertEqual(sorted((row["partner"], row["month"]) for row in p1_call.args[0]["rows"]),
                         [("CN", "202401"), ("CN", "202402")])
        result = self.output(run_dir, out)
        self.assertEqual({c["partner"] for c in result["cases"]} | {q["partner"] for q in result["data_quality"]},
                         {"CN"})


VALUE_READS = ("_rows", "row", "parent_series", "parent", "world_series", "world", "children", "peers", "resolve")


def value_read_spies() -> dict:
    """K3로 관측 값을 읽는 메서드와 조립체 2 단위의 호출을 세는 감시(spy). 진짜를 부르면서 호출만 센다."""
    spies = {f"K3 {name}": mock.patch.object(query.Snapshot, name, autospec=True, side_effect=getattr(query.Snapshot, name))
             for name in VALUE_READS}
    spies.update({"X1 run": mock.patch.object(unit_value, "run", wraps=unit_value.run),
                  "X2 run": mock.patch.object(share, "run", wraps=share.run),
                  "P1 run": mock.patch.object(trigger, "run", wraps=trigger.run),
                  "P2 run": mock.patch.object(case_build, "run", wraps=case_build.run)})
    return spies


# 실자료 모양 시험의 합성 분할 기록(본 스냅샷의 계열 10개). real_sealed 쪽에 합성 기대 출력(EXPECTED)에서 사례를 내는
# JP·DE·TW를 두어 "real_sealed 계열 접근 0"이 공허하지 않게 한다. 값과 배정은 모두 합성이다.
SPLIT_DEV = ["CN", "FI", "FR", "US", "VN"]
SPLIT_SEALED = ["DE", "JP", "PH", "SE", "TW"]


def split_record(snapshot_id: str = MAIN_ID, dev: list[str] = SPLIT_DEV, sealed: list[str] = SPLIT_SEALED) -> dict:
    """단위 V5 출력 모양(키 여섯 개)의 합성 분할 기록."""
    return {"snapshot_id": snapshot_id, "seed": 1, "ratio": {"real_dev": 1, "real_sealed": 1},
            "method": "hs6_stratified_sha256_rank",
            "real_dev": [{"hs6": df.HS6, "partner": p} for p in dev],
            "real_sealed": [{"hs6": df.HS6, "partner": p} for p in sealed]}


class RealSnapshotCase(DetectCase):
    """본 스냅샷(202301~202402의 14개월, 비교월 쌍 2개, 계열 10개)을 source_kind real로 빌드한 것. 값은 합성이고 수집기 메타의
    출처 종류만 real이다. 분할 기록 대응표(dispatch.REAL_SPLIT_FILES)는 시험마다 임시 파일로 바꾼다."""

    SOURCE_KIND = "real"

    def use_split(self, record: object, *, raw: str | None = None) -> None:
        """이 스냅샷의 분할 기록을 임시 파일에 쓰고 대응표를 그 파일 하나로 바꾼다."""
        path = self.root / "real_split.json"
        path.write_text(raw if raw is not None else json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        patcher = mock.patch.dict(dispatch.REAL_SPLIT_FILES, {MAIN_ID: str(path)}, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def assert_not_vacuous(self) -> None:
        """좁히기나 거부가 없었다면 탐지할 비교월 쌍·계열이 있다(호출 0이 공허하지 않다)."""
        with query.open_snapshot(MAIN_ID) as snap:
            self.assertEqual(snap.source_kind, "real")
            pairs, series = dispatch.detect_pairs(snap.months), dispatch.detect_series(snap)
        self.assertEqual(pairs, [("202401", "202301"), ("202402", "202302")])
        self.assertEqual(len(series), 10)  # 계열 10 × 비교월 2 = P1 행 20

    def assert_refused_before_values(self, message: str) -> None:
        self.assert_not_vacuous()
        spies = value_read_spies()
        with contextlib.ExitStack() as stack:
            mocks = {name: stack.enter_context(patcher) for name, patcher in spies.items()}
            code, out, err, run_dir = self.detect()
        self.assertEqual((code, out), (dispatch.EXIT_FAILED, ""))
        self.assertEqual(err, message + "\n")
        self.assertNotIn(MAIN_ID, err)  # 받은 값을 되풀이하지 않는다
        self.assertNotIn(str(self.root), err)  # 로컬 절대경로를 쓰지 않는다(N13)
        self.assertEqual({name: m.call_count for name, m in mocks.items()}, dict.fromkeys(spies, 0))
        self.assertEqual(list(run_dir.iterdir()), [])  # 확보한 빈 실행 폴더만 남는다


class RealSplitRefusalTest(RealSnapshotCase):
    """분할 기록을 쓸 수 없는 실자료 스냅샷은 K3로 관측 값을 읽거나 지표를 계산하기 전에 거부하고 1로 끝난다(SplitError)."""

    def test_real_snapshot_without_a_split_file_is_refused(self):
        # 대응표는 저장소 값 그대로다(v2 하나). 이 스냅샷 ID는 대응표에 없다. v1 같은 다른 실자료 스냅샷도 이 길이다.
        self.assertNotIn(MAIN_ID, dispatch.REAL_SPLIT_FILES)
        self.assert_refused_before_values(dispatch.DETECT_SPLIT_REFUSAL)

    def test_missing_or_broken_split_file_is_refused(self):
        for label, raw in (("없는 파일", None), ("JSON 아님", "{not json"), ("목록", "[]")):
            with self.subTest(label):
                if raw is None:
                    patcher = mock.patch.dict(dispatch.REAL_SPLIT_FILES, {MAIN_ID: str(self.root / "no_such.json")})
                    patcher.start()
                    self.addCleanup(patcher.stop)
                else:
                    self.use_split(None, raw=raw)
                self.assert_refused_before_values(dispatch.DETECT_SPLIT_REFUSAL)

    def test_split_record_that_does_not_fit_the_snapshot_is_refused(self):
        good = split_record()
        bad = {
            "다른 스냅샷 ID": split_record(snapshot_id="kcs_202201_202412_v2"),
            "키 빠짐": {k: v for k, v in good.items() if k != "method"},
            "키 더함": {**good, "extra": 1},
            "키 순서": dict(reversed(list(good.items()))),
            "계열 빠짐": split_record(dev=SPLIT_DEV[:-1]),
            "계획 밖 계열": split_record(dev=SPLIT_DEV + ["GB"]),
            "두 묶음에 같은 계열": split_record(dev=SPLIT_DEV + ["JP"]),
            "한 묶음에 두 번": split_record(dev=SPLIT_DEV + ["CN"]),
            "real_dev 비어 있음": split_record(dev=[], sealed=SPLIT_DEV + SPLIT_SEALED),
            "ALL 계열": split_record(dev=SPLIT_DEV + ["ALL"]),
            "항목 키 더함": {**good, "real_dev": [dict(item, dataset="real_dev") for item in good["real_dev"]]},
        }
        for label, record in bad.items():
            with self.subTest(label):
                self.use_split(record)
                self.assert_refused_before_values(dispatch.DETECT_SPLIT_REFUSAL)


class UnknownSourceKindRefusalTest(RealSnapshotCase):
    """출처 종류가 허용 목록(controlled·real) 밖이면 값을 읽기 전에 거부한다(분할 기록이 있어도)."""

    def test_unknown_source_kind_is_refused_before_any_value_is_read(self):
        self.use_split(split_record())
        self.assert_not_vacuous()
        with mock.patch.object(query.Snapshot, "source_kind", new_callable=mock.PropertyMock, return_value="other"), \
                mock.patch.object(dispatch, "load_real_split", wraps=dispatch.load_real_split) as loader:
            spies = value_read_spies()
            with contextlib.ExitStack() as stack:
                mocks = {name: stack.enter_context(patcher) for name, patcher in spies.items()}
                code, out, err, run_dir = self.detect()
        self.assertEqual((code, out, err), (dispatch.EXIT_FAILED, "", dispatch.DETECT_REFUSAL + "\n"))
        self.assertEqual(loader.call_count, 0)
        self.assertEqual({name: m.call_count for name, m in mocks.items()}, dict.fromkeys(spies, 0))
        self.assertEqual(list(run_dir.iterdir()), [])


class RealDevNarrowingTest(RealSnapshotCase):
    """실자료 스냅샷은 분할 기록의 real_dev 계열만 남긴 뒤에 관측 값을 읽고 지표·신호 발동을 부른다. real_sealed 계열의 관측
    행은 읽지 않는다(병렬 개발 규칙 §7.2의 5). P2는 dataset=real_dev와 분할 기록 전체의 배정을 받는다."""

    def setUp(self):
        super().setUp()
        self.use_split(split_record())

    def test_sealed_series_would_trigger_without_narrowing(self):
        # 공허하지 않다: 같은 값의 합성 스냅샷(EXPECTED)에서 real_sealed 쪽 JP·DE·TW는 사례를, SE는 데이터 품질 행을 낸다
        self.assertTrue({"JP", "DE", "TW"} <= {c["partner"] for c in EXPECTED["cases"]})
        self.assertIn("SE", {q["partner"] for q in EXPECTED["data_quality"]})

    def test_output_is_the_real_dev_cases(self):
        code, out, err, run_dir = self.detect()
        self.assertEqual((code, err), (0, ""))
        dev = set(SPLIT_DEV)
        self.assertEqual(self.output(run_dir, out), {
            "snapshot_id": MAIN_ID, "dataset": "real_dev", "policy_version": "dev-0.1",
            "cases": [c for c in EXPECTED["cases"] if c["partner"] in dev],
            "data_quality": [q for q in EXPECTED["data_quality"] if q["partner"] in dev]})

    def test_real_sealed_rows_are_never_read(self):
        """좁히기가 관측 값을 읽기 전에 일어나고, real_sealed 상대국의 관측 행은 조회 조건에도 결과에도 나오지 않는다."""
        sealed = set(SPLIT_SEALED)
        events: list[str] = []
        read_params: list[tuple] = []
        read_rows: list[dict] = []
        real_rows, real_row = query.Snapshot._rows, query.Snapshot.row
        real_loader = dispatch.load_real_split

        def rows_spy(snap, where, params):
            events.append("K3 _rows")
            found = real_rows(snap, where, params)
            read_params.append(tuple(params))
            read_rows.extend(found)
            return found

        def row_spy(snap, table, rowid):
            found = real_row(snap, table, rowid)
            if found is not None:
                read_rows.append(found)
            return found

        def loader_spy(snap):
            events.append("load_real_split")
            return real_loader(snap)

        with mock.patch.object(query.Snapshot, "_rows", autospec=True, side_effect=rows_spy), \
                mock.patch.object(query.Snapshot, "row", autospec=True, side_effect=row_spy), \
                mock.patch.object(query.Snapshot, "parent_series", autospec=True,
                                  side_effect=query.Snapshot.parent_series) as parent_series, \
                mock.patch.object(query.Snapshot, "world_series", autospec=True,
                                  side_effect=query.Snapshot.world_series) as world_series, \
                mock.patch.object(dispatch, "load_real_split", side_effect=loader_spy), \
                mock.patch.object(unit_value, "run", wraps=unit_value.run) as x1, \
                mock.patch.object(share, "run", wraps=share.run) as x2, \
                mock.patch.object(trigger, "run", wraps=trigger.run) as p1, \
                mock.patch.object(case_build, "run", wraps=case_build.run) as p2:
            code, out, err, run_dir = self.detect()
        self.assertEqual((code, err), (0, ""))
        # 순서: 분할 기록을 먼저 읽고, 그 뒤에만 관측 행을 읽는다
        self.assertEqual(events[0], "load_real_split")
        self.assertEqual(events.count("load_real_split"), 1)
        self.assertGreater(len(events), 1)
        # 관측 행: 조회 조건과 돌려받은 행 어디에도 real_sealed 상대국이 없다(ALL 분모 행은 두 묶음이 함께 쓴다)
        self.assertTrue(read_rows)
        self.assertEqual([p for p in read_params if sealed & set(p)], [])
        self.assertEqual([r for r in read_rows if r.get("partner_code") in sealed], [])
        self.assertEqual(sorted(c.args[2] for c in parent_series.call_args_list), SPLIT_DEV)
        self.assertEqual(world_series.call_count, 1)
        # 지표·신호 발동: real_dev 계열만(계열 5 × 비교월 2 = 10번)
        self.assertEqual(sorted({c.args[0]["partner"] for c in x1.call_args_list}), SPLIT_DEV)
        self.assertEqual(sorted({c.args[0]["partner"] for c in x2.call_args_list}), SPLIT_DEV)
        self.assertEqual((x1.call_count, x2.call_count), (10, 10))
        [p1_call] = p1.call_args_list
        self.assertEqual(sorted({row["partner"] for row in p1_call.args[0]["rows"]}), SPLIT_DEV)
        # P2: dataset=real_dev와 분할 기록 전체(10개)의 배정
        [p2_call] = p2.call_args_list
        given = p2_call.args[0]
        self.assertEqual((given["source_kind"], given["dataset"]), ("real", "real_dev"))
        self.assertEqual(given["series_assignment"],
                         [{"hs6": df.HS6, "partner": p, "dataset": "real_dev" if p in SPLIT_DEV else "real_sealed"}
                          for p in sorted(SPLIT_DEV + SPLIT_SEALED)])
        self.assertEqual(self.output(run_dir, out)["dataset"], "real_dev")


if __name__ == "__main__":
    unittest.main()
