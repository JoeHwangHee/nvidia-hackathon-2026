"""단위 L1(runlog_trace)의 골든 쌍 밖 규칙 시험: 덮어쓰기 금지, float·키 거부, Decimal 표기 보존, 이벤트·단계 검사."""
import tempfile
import unittest
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from tradesentry.runlog import trace

RUN_ID = "run_case-260925143015"
FIXED = datetime(2026, 9, 25, 14, 30, 15, tzinfo=trace.KST)


class TraceRuleTest(unittest.TestCase):
    def test_writer_creates_new_file_only_and_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = trace.trace_path(Path(tmp), "260925143015")
            self.assertEqual(path.name, "runlog_trace-260925143015.jsonl")
            writer = trace.TraceWriter(path, RUN_ID, clock=lambda: FIXED)
            writer.emit("tool_result", "basic", {"value": Decimal("20.30"), "n": 3})
            writer.emit("run_end", None, {"execution_status": "COMPLETED"})
            writer.close()
            text = path.read_text(encoding="utf-8")
            self.assertIn('"value":20.30', text)  # 끝자리 0 보존, 따옴표 없는 JSON 숫자
            records = trace.read_records(path)
            self.assertEqual([r["seq"] for r in records], [1, 2])
            self.assertEqual(records[0]["data"]["value"], Decimal("20.30"))
            self.assertEqual(records[0]["ts"], "2026-09-25T14:30:15+09:00")
            with self.assertRaises(FileExistsError):
                trace.TraceWriter(path, RUN_ID)

    def test_rejects_float_nan_and_key_like_fields(self):
        memory = trace.MemoryTrace(RUN_ID, clock=lambda: FIXED)
        with self.assertRaises(ValueError):
            memory.emit("run_start", None, {"x": 1.5})
        with self.assertRaises(ValueError):
            memory.emit("run_start", None, {"x": Decimal("NaN")})
        for key in ("Authorization", "api_key", "nested"):
            data = {"headers": {key: "v"}} if key != "nested" else {"a": [{"x-api-key": "v"}]}
            with self.subTest(key=key), self.assertRaises(ValueError):
                memory.emit("model_request", "basic", data)
        self.assertEqual(memory.records, [])

    def test_rejects_unknown_event_stage_and_bad_run_id(self):
        memory = trace.MemoryTrace(RUN_ID, clock=lambda: FIXED)
        with self.assertRaises(ValueError):
            memory.emit("model_thought", None, {})
        with self.assertRaises(ValueError):
            memory.emit("stage_start", "planning", {})
        with self.assertRaises(ValueError):
            trace.MemoryTrace("Run-1", clock=lambda: FIXED).emit("run_start", None, {})
        for ts in ("2026-09-25T05:30:15+00:00", "2026-09-25T14:30:15.120+09:00"):  # UTC, 초 단위 아님(§11.4)
            with self.subTest(ts=ts), self.assertRaises(ValueError):
                trace.run({"run_id": RUN_ID, "events": [{"ts": ts, "event": "run_start"}]})

    def test_canonical_hash_ignores_key_order_but_not_number_text(self):
        a = {"b": [1, {"y": Decimal("1.0"), "x": "가"}], "a": None}
        b = {"a": None, "b": [1, {"x": "가", "y": Decimal("1.0")}]}
        self.assertEqual(trace.canonical_sha256(a), trace.canonical_sha256(b))
        self.assertNotEqual(trace.canonical_sha256({"t": Decimal("1.0")}), trace.canonical_sha256({"t": Decimal("1")}))
        self.assertRegex(trace.canonical_sha256(a), r"^[0-9a-f]{64}$")

    def test_tee_passes_same_event_to_every_sink(self):
        first, second = trace.MemoryTrace(RUN_ID, lambda: FIXED), trace.MemoryTrace(RUN_ID, lambda: FIXED)
        trace.Tee(first, None, second, trace.NullSink()).emit("stage_start", "critic", {"stage": "critic"})
        self.assertEqual(first.records, second.records)
        self.assertEqual(first.records[0]["event"], "stage_start")


if __name__ == "__main__":
    unittest.main()
