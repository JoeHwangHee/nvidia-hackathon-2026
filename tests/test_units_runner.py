"""공통 실행기(src/tradesentry/units/runner.py) 시험: 실행명 확보(자료 계약 §10.3 N8), 출력 이름(N6), 덮어쓰기 금지, 종료 코드.

네트워크와 키 없이 돈다. 시계와 기다리기를 가짜로 바꿔 실제로 기다리지 않고, 출력은 임시 폴더에만 쓴다.
실행: uv run --locked python -m unittest discover -s tests -v (저장소 루트에서)
"""
import io
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest import mock

from tradesentry.units import registry, runner

KST = runner.KST
START = datetime(2026, 9, 25, 14, 30, 15, 250000, tzinfo=KST)  # 실행명 시각 260925143015


class FakeClock:
    """가짜 시계. sleep이 불리면 그만큼 시각을 옮긴다."""

    def __init__(self, start: datetime):
        self.t = start
        self.slept: list[float] = []

    def now(self) -> datetime:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.t += timedelta(seconds=seconds)


class TempOutputsMixin:
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.outputs = self.tmp / "outputs"

    def reserve(self, name: str = "x", clock: FakeClock | None = None, **kwargs):
        clock = clock or FakeClock(START)
        parent = kwargs.pop("parent", self.outputs)
        other = kwargs.pop("other", self.outputs / "sealed")
        return runner.reserve_run_dir(parent, other, name, clock=clock.now, sleep=clock.sleep, **kwargs)


class ReserveRunDirTest(TempOutputsMixin, unittest.TestCase):
    def test_creates_empty_run_dir_named_with_kst_stamp(self):
        clock = FakeClock(START)
        run_id, stamp, run_dir = self.reserve("metrics_unit_value", clock)
        self.assertEqual(stamp, "260925143015")
        self.assertEqual(run_id, "metrics_unit_value-260925143015")
        self.assertEqual(run_dir, self.outputs / run_id)
        self.assertEqual(list(run_dir.iterdir()), [])
        self.assertEqual(clock.slept, [])  # 첫 이름은 지금 초라 기다리지 않는다

    def test_stamp_is_kst_even_if_clock_is_utc(self):
        clock = FakeClock(START.astimezone(timezone.utc))
        _, stamp, _ = self.reserve("x", clock)
        self.assertEqual(stamp, "260925143015")

    def test_taken_name_moves_to_next_second_after_waiting_for_it(self):
        taken = self.outputs / "x-260925143015"
        taken.mkdir(parents=True)
        (taken / "keep.txt").write_text("앞선 실행", encoding="utf-8")
        clock = FakeClock(START)
        run_id, stamp, run_dir = self.reserve("x", clock)
        self.assertEqual(run_id, "x-260925143016")
        self.assertTrue(clock.slept)  # 다음 초가 될 때까지 기다렸다
        self.assertGreaterEqual(clock.now(), datetime(2026, 9, 25, 14, 30, 16, tzinfo=KST))
        self.assertEqual((taken / "keep.txt").read_text(encoding="utf-8"), "앞선 실행")  # 앞선 실행 폴더는 그대로다

    def test_same_name_in_other_parent_releases_new_dir_and_moves_on(self):
        other = self.outputs / "sealed" / "x-260925143015"
        other.mkdir(parents=True)
        run_id, _, _ = self.reserve("x")
        self.assertEqual(run_id, "x-260925143016")
        self.assertFalse((self.outputs / "x-260925143015").exists())  # 방금 만든 빈 폴더를 지웠다
        self.assertTrue(other.is_dir())  # 다른 부모 폴더 쪽은 건드리지 않는다

    def test_sealed_parent_checks_outputs_as_other_parent(self):
        sealed = self.outputs / "sealed"
        (self.outputs / "run_case-260925143015").mkdir(parents=True)
        run_id, _, run_dir = self.reserve("run_case", parent=sealed, other=self.outputs)
        self.assertEqual(run_id, "run_case-260925143016")
        self.assertEqual(run_dir.parent, sealed)
        self.assertFalse((sealed / "run_case-260925143015").exists())

    def test_gives_up_after_max_attempts(self):
        for sec in (15, 16, 17):
            (self.outputs / f"x-2609251430{sec}").mkdir(parents=True)
        with self.assertRaises(runner.RunNameError):
            self.reserve("x", max_attempts=3)
        self.assertEqual(sorted(p.name for p in self.outputs.iterdir()),
                         ["x-260925143015", "x-260925143016", "x-260925143017"])


class WriteOutputTest(TempOutputsMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.run_dir = self.outputs / "d-260925143015"
        self.run_dir.mkdir(parents=True)

    def test_json_keeps_decimal_digits(self):
        path = runner.write_output(self.run_dir, "d", "260925143015", "json", {"v": Decimal("1.10"), "n": None})
        self.assertEqual(path.name, "d-260925143015.json")
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"v": "1.10", "n": None})

    def test_jsonl_writes_one_line_per_item(self):
        path = runner.write_output(self.run_dir, "d", "260925143015", "jsonl", [{"a": 1}, {"a": 2}])
        self.assertEqual(path.read_text(encoding="utf-8").splitlines(), ['{"a": 1}', '{"a": 2}'])

    def test_text_and_binary(self):
        md = runner.write_output(self.run_dir, "d", "260925143015", "md", "# 요약\n")
        self.assertEqual(md.read_text(encoding="utf-8"), "# 요약\n")
        db = runner.write_output(self.run_dir, "d", "260925143015", "sqlite", b"SQLite format 3\x00")
        self.assertEqual(db.read_bytes(), b"SQLite format 3\x00")

    def test_value_must_match_extension(self):
        for ext, value in (("jsonl", {"a": 1}), ("md", b"x"), ("sqlite", "x"), ("json", {1, 2}), ("exe", "x")):
            with self.subTest(ext=ext), self.assertRaises(runner.OutputRuleError):
                runner.write_output(self.run_dir, "d", "260925143015", ext, value)

    def test_never_overwrites(self):
        existing = self.run_dir / "d-260925143015.json"
        existing.write_text("원래 내용", encoding="utf-8")
        with self.assertRaises(runner.OutputRuleError):
            runner.write_output(self.run_dir, "d", "260925143015", "json", {"new": True})
        self.assertEqual(existing.read_text(encoding="utf-8"), "원래 내용")


class RunUnitTest(TempOutputsMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.empty = self.tmp / "empty.json"
        self.empty.write_bytes(b"")

    def run_unit(self, unit_id: str, input_path: Path) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        clock = FakeClock(START)
        code = runner.run_unit(unit_id, input_path, outputs_root=self.outputs, clock=clock.now, sleep=clock.sleep,
                               out=out, err=err)
        text = out.getvalue() + err.getvalue()
        for local in (str(self.tmp), str(runner.REPO_ROOT), str(Path.home())):
            self.assertNotIn(local, text)  # 로컬 절대경로를 출력하지 않는다(N13)
        return code, out.getvalue(), err.getvalue()

    def test_unimplemented_runtime_unit_reserves_run_dir_then_fails(self):
        code, out, err = self.run_unit("X1", self.empty)
        self.assertEqual(code, runner.EXIT_NOT_IMPLEMENTED)
        run_dir = self.outputs / "metrics_unit_value-260925143015"
        self.assertTrue(run_dir.is_dir())
        self.assertEqual(list(run_dir.iterdir()), [])
        self.assertIn("실행명: metrics_unit_value-260925143015", out)
        self.assertIn("아직 구현되지 않았다", err)

    def test_unimplemented_eval_unit_reserves_run_dir_then_fails(self):
        code, _, _ = self.run_unit("C1", self.empty)
        self.assertEqual(code, runner.EXIT_NOT_IMPLEMENTED)
        self.assertTrue((self.outputs / "scorer_claims-260925143015").is_dir())

    def test_dev_null_is_no_input(self):
        seen = []
        with mock.patch.object(registry, "load_entry", return_value=lambda inp: seen.append(inp) or {"ok": True}):
            code, _, _ = self.run_unit("X1", Path("/dev/null"))
        self.assertEqual(code, runner.EXIT_OK)
        self.assertEqual(seen, [None])

    def test_success_writes_one_output_named_by_domain_and_stamp(self):
        source = self.tmp / "in.json"
        source.write_text('{"V": 1.50}', encoding="utf-8")
        with mock.patch.object(registry, "load_entry", return_value=lambda inp: {"echo": inp}):
            code, out, _ = self.run_unit("X1", source)
        self.assertEqual(code, runner.EXIT_OK)
        run_dir = self.outputs / "metrics_unit_value-260925143015"
        self.assertEqual([p.name for p in run_dir.iterdir()], ["metrics_unit_value-260925143015.json"])
        written = json.loads((run_dir / "metrics_unit_value-260925143015.json").read_text(encoding="utf-8"))
        self.assertEqual(written, {"echo": {"V": "1.50"}})  # 소수는 Decimal로 읽고 글자 그대로 쓴다
        self.assertIn("출력: outputs/metrics_unit_value-260925143015/metrics_unit_value-260925143015.json", out)

    def test_refusals_before_reservation_create_nothing(self):
        bad_json = self.tmp / "bad.json"
        bad_json.write_text("{", encoding="utf-8")
        cases = [("NOPE", self.empty), ("V3", self.empty), ("V6", self.empty), ("G3", self.empty),
                 ("S1", self.empty), ("K1", self.empty), ("X1", self.tmp / "missing.json"), ("X1", bad_json)]
        for unit_id, source in cases:
            with self.subTest(unit_id=unit_id, source=source.name):
                code, _, err = self.run_unit(unit_id, source)
                self.assertEqual(code, runner.EXIT_USAGE)
                self.assertTrue(err.startswith("오류:"))
                self.assertFalse(self.outputs.exists())

    def test_entry_load_error_does_not_print_local_paths(self):
        module_file = runner.REPO_ROOT / "src" / "tradesentry" / "metrics" / "unit_value.py"
        errors = [
            ImportError(f"cannot import name 'run' from 'tradesentry.metrics.unit_value' ({module_file})",
                        name="tradesentry.metrics.unit_value", path=str(module_file)),
            AttributeError(f"module loaded from {Path.home() / 'unit_value.py'} has no attribute 'run'"),
        ]
        for exc in errors:
            with self.subTest(error=type(exc).__name__):
                with mock.patch.object(registry, "load_entry", side_effect=exc):
                    code, _, err = self.run_unit("X1", self.empty)
                self.assertEqual(code, runner.EXIT_USAGE)
                self.assertIn(type(exc).__name__, err)
                self.assertIn("tradesentry.metrics.unit_value", err)  # 예외 이름과 모듈 이름만 적는다
                self.assertNotIn(str(runner.REPO_ROOT), err)
                self.assertNotIn(str(Path.home()), err)
                self.assertFalse(self.outputs.exists())

    def test_wrong_output_type_is_output_error(self):
        with mock.patch.object(registry, "load_entry", return_value=lambda inp: "문자열"):
            code, _, err = self.run_unit("E1", self.empty)  # E1은 jsonl이라 목록이어야 한다
        self.assertEqual(code, runner.EXIT_OUTPUT)
        self.assertIn("출력 규칙 위반", err)


class MainTest(unittest.TestCase):
    def test_main_uses_repo_outputs_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("", encoding="utf-8")
            empty = root / "empty.json"
            empty.write_bytes(b"")
            with mock.patch.object(runner, "REPO_ROOT", root), \
                    mock.patch("sys.stdout", new_callable=io.StringIO), \
                    mock.patch("sys.stderr", new_callable=io.StringIO):
                code = runner.main(["C4", "--in", str(empty)])
            self.assertEqual(code, runner.EXIT_NOT_IMPLEMENTED)
            made = [p.name for p in (root / "outputs").iterdir()]
            self.assertEqual(len(made), 1)
            self.assertRegex(made[0], r"^scorer_summary-\d{12}$")

    def test_input_option_is_required(self):
        with mock.patch("sys.stderr", new_callable=io.StringIO), self.assertRaises(SystemExit) as cm:
            runner.main(["X1"])
        self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
