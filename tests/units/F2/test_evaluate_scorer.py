"""조립 작업 AS3 조립 시험: dev20으로 돈 평가 하네스 출력을 독립 채점기가 읽어 세 파일을 낸다(로드맵 AS3 완료 기준).

- 실제로 도는 것: 단위 F1 → F2 evaluate(호스트 백엔드) → 단위 E1 묶음 실행(dev20 사례 20건 × checklist·agent·full, 사용자
  결정 12(가)의 기본 모드 전부) → 사례마다 run-case와 같은 조립(run_case_in → investigate_case: 도구 I1~I5, 흐름 조정 I12,
  판정 정책 P3~P5, 보고서 R1·R2, 검증기 R3·R4, NAT 감싸기 I13, 실행 기록 L1~L3) → 단위 E4 → 실행 조건 입력 파일 → 채점기
  python -m eval.scorer --run <run_dir>의 main(저장소 뿌리를 임시 사본으로 준다) → scorer_results·scorer_claims·
  scorer_summary 세 파일.
- 바꾸는 것: 저장소 뿌리(임시 사본: 커밋된 dev20 묶음과 스냅샷 원천으로 dev20 install을 한 번 돌린다), 모델 전송 자리(모델
  모드는 HTTP 400을 곧바로 돌려주는 가짜. 재시도하지 않는 PROVIDER_HTTP_4XX로 FAILED가 된다), 백엔드(호스트). 실제 NIM·
  openshell은 부르지 않는다. 채점기는 in-process로 부르되 tradesentry를 import하는 쪽은 이 시험이다(채점기 코드는 그대로).
- 보는 것: 채점기 종료 코드 0과 세 파일, 결과 60줄, checklist 20건 COMPLETED와 보고서 파일 이름(reports_render_ko-{시각}.json),
  실행 조건 입력 파일 이름(run_conditions-{시각}.json), 사례 실행 폴더가 묶음 폴더의 형제, E4 runs_with_profile = 실행 수,
  평가 실행에서 세 포트(필수 조회 required_tools, 초안은 도구 없는 차례 drafts_only_without_tools, 규칙 참고값
  reference_status)가 켜졌는지(AS2 결정 기록 "AS3" 항목).
dev20 정답표는 채점기만 읽는다(이 시험은 파일을 복사만 하고 내용을 보지 않는다).
"""
import contextlib
import io
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import harness_fixtures as hf
from eval.datagen import dev20
from eval.scorer import __main__ as scorer
from tradesentry.cli import dispatch
from tradesentry.dal import query
from tradesentry.runlog import cause_codes
from tradesentry.workflow import orchestrate

from ..I7.fakes import NoNetworkMixin

REPO = Path(__file__).resolve().parents[3]
DEV20_DIR = REPO / "eval" / "dev" / "dev20"
SNAPSHOT_DIR = REPO / "data" / "snapshots" / "dev20"
PEER_FILE = REPO / "data" / "reference" / "peer_group_dev20.csv"
DROP_ENV = ("NVIDIA_API_KEY", "NVIDIA_INFERENCE_API_KEY", "DATA_GO_KR_SERVICE_KEY", "TRADESENTRY_SEALED_DIR")
_SHARED: dict = {}


class Http400Transport:
    """모델 요청마다 HTTP 400을 곧바로 돌려준다(네트워크 없음). 4xx는 재시도하지 않는다."""

    def __init__(self):
        self.sent = 0

    def send(self, payload, timeout_ms):
        self.sent += 1
        return {"http_status": 400, "body": b"", "error": None, "elapsed_ms": 5}


def setUpModule():
    """임시 저장소 사본에 dev20을 설치하고, evaluate(호스트 백엔드)를 한 번 돌린 뒤 채점기를 부른다."""
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    _SHARED["tmp"] = tmp
    shutil.copytree(DEV20_DIR, root / "eval" / "dev" / "dev20")
    (root / "data" / "snapshots" / "dev20").mkdir(parents=True)
    for name in ("manifest.json", "collection_log.json", "snapshot_hash.json", "snapshot_build.json"):
        shutil.copyfile(SNAPSHOT_DIR / name, root / "data" / "snapshots" / "dev20" / name)
    (root / "data" / "reference").mkdir()
    shutil.copyfile(PEER_FILE, root / "data" / "reference" / PEER_FILE.name)
    installed = dev20.install(root)
    if not installed["ok"]:
        raise AssertionError("dev20 install이 임시 사본에서 실패했다")
    transport = Http400Transport()
    seen_ports: list = []
    original = orchestrate.orchestrate

    def spy(ctx, ports, config, **kwargs):
        seen_ports.append((ctx.mode, ports))
        return original(ctx, ports, config, **kwargs)

    def refuse(*args, **kwargs):
        raise AssertionError("시험에서 네트워크 연결을 시도했다")

    out, err = io.StringIO(), io.StringIO()
    with mock.patch("socket.socket.connect", refuse), mock.patch("socket.create_connection", refuse), \
            mock.patch.object(query, "SNAPSHOTS_ROOT", root / "data" / "snapshots"), \
            mock.patch.object(dispatch, "OUTPUT_PARENT", root / "outputs"), \
            mock.patch.object(dispatch, "EVALUATE_BACKEND", dispatch.HOST_BACKEND), \
            mock.patch.dict(dispatch.EVALUATE_CASE_LISTS,
                            {"dev20": root / "eval" / "dev" / "dev20" / "input" / "cases.json"}), \
            mock.patch.object(dispatch, "run_case_transport", lambda config: transport), \
            mock.patch.object(orchestrate, "orchestrate", spy), \
            contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = dispatch.main(["evaluate", "--snapshot", "dev20", "--policy", "dev-0.1"])
    _SHARED.update(root=root, code=code, out=out.getvalue(), err=err.getvalue(), transport=transport,
                   ports=seen_ports)
    if code != 0:
        return
    batch_line = out.getvalue().splitlines()[0]
    batch_dir = root / Path(batch_line).parent
    environ = {k: v for k, v in os.environ.items() if k not in DROP_ENV}
    s_out, s_err = io.StringIO(), io.StringIO()
    s_code = scorer.main(["--run", str(batch_dir)], repo_root=root, environ=environ, out=s_out, err=s_err)
    _SHARED.update(batch_dir=batch_dir, scorer_code=s_code, scorer_out=s_out.getvalue(), scorer_err=s_err.getvalue())


def tearDownModule():
    _SHARED.pop("tmp").cleanup()
    _SHARED.clear()


class EvaluateToScorerTest(NoNetworkMixin, unittest.TestCase):
    def test_evaluate_writes_batch_and_conditions(self):
        self.assertEqual(_SHARED["code"], 0, _SHARED["err"])
        batch_line, conditions_line = _SHARED["out"].splitlines()
        self.assertRegex(batch_line, r"^outputs/evaluate-(\d{12})/evaluation_batch_run-\1\.jsonl$")
        self.assertRegex(conditions_line, r"^outputs/evaluate-(\d{12})/run_conditions-\1\.json$")  # 채점기 가정 이름
        lines = hf.read_jsonl(_SHARED["root"] / batch_line)
        self.assertEqual(len(lines), 60)
        self.assertTrue(all(hf.scorer_line_problems(line) == [] for line in lines))
        checklist = [line for line in lines if line["mode"] == "checklist"]
        model = [line for line in lines if line["mode"] != "checklist"]
        self.assertEqual({line["execution_status"] for line in checklist}, {"COMPLETED"})
        self.assertEqual({(line["execution_status"], line["errors"][0]["code"]) for line in model},
                         {("FAILED", cause_codes.PROVIDER_HTTP_4XX)})
        self.assertEqual(_SHARED["transport"].sent, 40)  # 모델 모드 40회, 재시도 없음
        self.assertEqual({line["code_version"] for line in lines}, {dispatch.code_version()})
        self.assertEqual({(line["dataset"], line["snapshot_id"], line["grouping_version"]) for line in lines},
                         {("dev20", "dev20", "g0")})

    def test_case_folders_are_siblings_with_the_scorer_file_names(self):
        root = _SHARED["root"]
        lines = hf.read_jsonl(root / _SHARED["out"].splitlines()[0])
        for line in lines:
            folder = root / "outputs" / line["run_id"]
            stamp = line["run_id"].rsplit("-", 1)[1]
            with self.subTest(run_id=line["run_id"]):
                self.assertTrue((folder / f"runlog_run_record-{stamp}.json").is_file())
                self.assertEqual((folder / f"reports_render_ko-{stamp}.json").is_file(),
                                 line["execution_status"] == "COMPLETED")  # 채점기 REPORT_DOMAIN과 같은 이름
                self.assertTrue((folder / f"workflow_nat_wrap-{stamp}").is_dir())

    def test_nat_summary_counts_every_run(self):
        import json
        from decimal import Decimal

        doc = json.loads((_SHARED["root"] / _SHARED["out"].splitlines()[1]).read_text(encoding="utf-8"),
                         parse_float=Decimal)
        summary = doc["nat_profile_summary"]
        self.assertEqual(summary["runs"], 60)
        self.assertEqual(summary["runs_with_profile"], 60)  # NAT 폴더 이름이 E4와 맞다(MT7 "AS3에 넘길 것" 5)
        self.assertEqual(summary["runs_with_nat_trace"], 60)
        self.assertEqual(doc["planned_modes"], ["checklist", "agent", "full"])
        self.assertEqual(len(doc["planned_cases"]), 20)

    def test_three_ports_are_on_in_the_evaluate_run(self):
        ports = _SHARED["ports"]
        self.assertEqual(len(ports), 60)
        for mode, port in ports:
            with self.subTest(mode=mode):
                self.assertIs(port.required_tools, dispatch.required_tools)
                self.assertIs(port.drafts_only_without_tools, True)
                self.assertIsNotNone(port.reference_status)

    def test_scorer_reads_the_batch_and_writes_three_files(self):
        self.assertEqual(_SHARED.get("scorer_code"), 0, _SHARED.get("scorer_err"))
        first = _SHARED["scorer_out"].splitlines()[0]
        self.assertRegex(first, r"^score-\d{12}$")
        stamp = first.split("-", 1)[1]
        folder = _SHARED["root"] / "outputs" / first
        self.assertEqual(sorted(p.name for p in folder.iterdir()),
                         [f"scorer_claims-{stamp}.jsonl", f"scorer_results-{stamp}.jsonl", f"scorer_summary-{stamp}.md"])
        results = hf.read_jsonl(folder / f"scorer_results-{stamp}.jsonl")
        self.assertEqual(len(results), 60)
        summary = (folder / f"scorer_summary-{stamp}.md").read_text(encoding="utf-8")
        self.assertIn(f"평가 묶음 실행 {_SHARED['batch_dir'].name}", summary)
        self.assertIn("tradesentry evaluate --snapshot dev20 --policy dev-0.1", summary)  # 재현 명령(룰북 B7)
        self.assertNotIn(str(_SHARED["root"]), summary)  # 로컬 절대경로가 없다(N13)


if __name__ == "__main__":
    unittest.main()
