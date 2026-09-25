"""로드맵 MT7 리허설: 봉인 배치를 흉내 내어 단위 E2로 dev20(봉인 아님)을 돌리기 → 내려받기 → 실행 조건 입력 파일 배타 생성 →
채점기가 그 출력을 읽어 파일 세 개를 내기. 실제 outputs/sealed/·봉인 폴더·openshell·NIM에는 닿지 않는다.

- 위치: 임시 저장소 사본(커밋된 dev20 묶음과 스냅샷 원천으로 dev20 install을 한 번 돌린다). E2의 outputs/ 부모·해시 목록·봉인
  폴더 자리를 함수 인자로 임시 위치에 둔다(재대조 단계는 가짜 해시 목록으로 흉내 낸다).
- 사례 실행: 가짜 openshell(tests/units/F2/fake_openshell.py). dev20 20건 × 3모드 = 60회. 모델 응답은 없다(기록만 흉내).
- 채점기: python -m eval.scorer --run <run_dir>의 main을 in-process로 부른다. 채점기 파일은 고치지 않고, 채점기가 E2의 실행 이름을
  알아야 하는 상수 BATCH_DOMAINS만 시험 안에서 monkeypatch한다(D 트랙 PR이 더할 값 "sealed_evaluate": "evaluation_sealed_runner").
- 이름 충돌: 다른 부모(outputs/sealed/)에 첫 초의 이름을 미리 두어 N8대로 다음 초로 넘어가는지, 사례 실행 폴더가 묶음 폴더의
  형제(outputs/run_case-{시각}/)인지 본다.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

import harness_fixtures as hf
from eval.datagen import dev20
from eval.scorer import __main__ as scorer
from tradesentry.evaluation import sandbox_exec, sealed_runner

REPO = Path(__file__).resolve().parents[3]
FAKE = REPO / "tests" / "units" / "F2" / "fake_openshell.py"
DEV20_DIR = REPO / "eval" / "dev" / "dev20"
SNAPSHOT_DIR = REPO / "data" / "snapshots" / "dev20"
PEER_FILE = REPO / "data" / "reference" / "peer_group_dev20.csv"
COMMIT = "0123456789abcdef0123456789abcdef01234567"
DROP_ENV = ("NVIDIA_API_KEY", "NVIDIA_INFERENCE_API_KEY", "DATA_GO_KR_SERVICE_KEY", "TRADESENTRY_SEALED_DIR")
_SHARED: dict = {}


def _write_fake_sealed(root: Path) -> tuple[Path, Path]:
    """가짜 봉인 폴더(두 묶음 파일 넷)와 그 해시 목록. 내용은 자리표시다."""
    sealed = root / "sealed_fake"
    entries = []
    for name in ("holdout40/input/cases.json", "holdout40/answers/answers.json",
                 "real_sealed/sample-260926065820.json", "real_sealed/sample_seed.json"):
        path = sealed / name
        path.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps({"placeholder": name}).encode("utf-8")
        path.write_bytes(data)
        entries.append({"dataset": name.split("/")[0], "file_name": name,
                        "sha256": __import__("hashlib").sha256(data).hexdigest(),
                        "created_at": "2026-09-26T06:58:20+09:00", "created_by": "시험 생성 에이전트"})
    manifest = root / "manifest_fake.json"
    manifest.write_text(json.dumps({"schema_version": 2, "files": entries}), encoding="utf-8")
    return sealed, manifest


def setUpModule():
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
    cases_doc = json.loads((root / "eval" / "dev" / "dev20" / "input" / "cases.json").read_text(encoding="utf-8"))
    cases = [{k: c[k] for k in ("case_id", "hs6", "partner", "month")} for c in cases_doc["cases"]]
    # 가짜 openshell
    sandbox_root = root / "fake_sandbox"
    sandbox_root.mkdir()
    (sandbox_root / "host_secret.txt").write_text("not a secret", encoding="utf-8")
    bin_dir = root / "bin"
    bin_dir.mkdir()
    program = bin_dir / "openshell"
    program.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{FAKE}" "$@"\n', encoding="utf-8")
    program.chmod(0o755)
    versions = {"policy_version": cases_doc["policy_version"], "rulebook_version": "RB-1", "snapshot_id": "dev20",
                "grouping_version": "g0", "code_version": COMMIT}
    (root / "scenario.json").write_text(json.dumps({"manifest": {"code_version": {"git_commit": COMMIT, "dirty": False}},
                                                    "versions": versions, "dataset": "dev20", "cases": {}}),
                                        encoding="utf-8")
    env = {"PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}", "FAKE_OPENSHELL_ROOT": str(sandbox_root),
           "FAKE_OPENSHELL_SCENARIO": str(root / "scenario.json"), "FAKE_OPENSHELL_LOG": str(root / "openshell_log.jsonl"),
           "NVIDIA_API_KEY": "fake-placeholder", "TRADESENTRY_SEALED_DIR": str(root / "no_sealed")}
    sealed, manifest = _write_fake_sealed(root)
    outputs = root / "outputs"
    (outputs / "sealed" / "sealed_evaluate-260925100000").mkdir(parents=True)  # 다른 부모의 같은 이름(N8)
    settings = sealed_runner.Settings(dataset="dev20", sandbox="ts-rehearsal", snapshot_id="dev20",
                                      policy_version=cases_doc["policy_version"], outputs=outputs, repo_root=REPO,
                                      manifest=manifest, sealed_root=sealed)
    clock = hf.FakeClock()
    out, err = io.StringIO(), io.StringIO()
    with mock.patch.dict(os.environ, env), mock.patch.object(sandbox_exec, "code_version", lambda root=None: COMMIT):
        code = sealed_runner.run_sealed(settings, cases=cases, clock=clock, sleep=clock.sleep, out=out, err=err)
    _SHARED.update(root=root, cases=cases, code=code, out=out.getvalue(), err=err.getvalue())
    if code != 0:
        return
    run_line = [line for line in out.getvalue().splitlines() if line.startswith("outputs/")][0]
    run_dir = root / run_line
    environ = {k: v for k, v in os.environ.items() if k not in DROP_ENV}
    s_out, s_err = io.StringIO(), io.StringIO()
    with mock.patch.dict(scorer.BATCH_DOMAINS, {"sealed_evaluate": "evaluation_sealed_runner"}):
        s_code = scorer.main(["--run", str(run_dir)], repo_root=root, environ=environ, out=s_out, err=s_err)
    _SHARED.update(run_dir=run_dir, scorer_code=s_code, scorer_out=s_out.getvalue(), scorer_err=s_err.getvalue())


def tearDownModule():
    _SHARED.pop("tmp").cleanup()
    _SHARED.clear()


class RehearsalTest(unittest.TestCase):
    def test_e2_runs_dev20_with_recheck_and_no_name_collision(self):
        self.assertEqual(_SHARED["code"], 0, _SHARED["err"])
        lines = _SHARED["out"].splitlines()
        self.assertIn("목록 파일 4개, 일치 4개, 불일치 0개, 목록 밖 항목 0개 → 일치", lines[0])  # 재대조 단계 흉내
        self.assertEqual(lines[1], "계획 사례 20건")
        self.assertRegex(lines[2], r"^outputs/sealed_evaluate-\d{12}$")  # 봉인 아님: outputs/ 아래
        self.assertNotEqual(lines[2], "outputs/sealed_evaluate-260925100000")  # 다른 부모에 있던 이름은 건너뛰었다
        self.assertIn("실행 상태: COMPLETED 60, FAILED 0", _SHARED["out"])
        self.assertIn("모드별 사례 집합 일치: 참", _SHARED["out"])
        run_dir = _SHARED["run_dir"]
        stamp = run_dir.name.rsplit("-", 1)[1]
        self.assertEqual(sorted(p.name for p in run_dir.iterdir()),
                         [f"evaluation_sealed_runner-{stamp}.jsonl", f"run_conditions-{stamp}.json"])
        rows = hf.read_jsonl(run_dir / f"evaluation_sealed_runner-{stamp}.jsonl")
        self.assertEqual(len(rows), 60)
        self.assertEqual(len({row["run_id"] for row in rows}), 60)  # 사례 실행명 충돌 없음
        for row in rows:  # 사례 실행 폴더는 묶음 폴더의 형제(채점기가 <run_dir>의 부모에서 연다)
            self.assertTrue((run_dir.parent / row["run_id"]).is_dir())
            self.assertRegex(row["run_id"], r"^run_case-\d{12}$")
        doc = json.loads((run_dir / f"run_conditions-{stamp}.json").read_text(encoding="utf-8"), parse_float=Decimal)
        self.assertEqual((doc["dataset"], doc["planned_modes"], doc["order_seed"]),
                         ("dev20", ["checklist", "agent", "full"], "rb1-order-v1"))
        self.assertEqual(doc["planned_cases"], _SHARED["cases"])
        self.assertEqual(doc["sandbox"]["name"], "ts-rehearsal")
        self.assertNotIn("nat_profile_summary", doc)
        for case in _SHARED["cases"]:
            self.assertNotIn(case["case_id"], _SHARED["out"] + _SHARED["err"])

    def test_scorer_reads_e2_output_and_writes_three_files(self):
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
        self.assertIn(f"평가 묶음 실행 {_SHARED['run_dir'].name}", summary)
        self.assertIn("python -m tradesentry.evaluation.sealed_runner --dataset dev20 --sandbox ts-rehearsal "
                      "--snapshot dev20 --policy dev-0.1", summary)  # 재현 명령(룰북 B7)
        self.assertNotIn(str(_SHARED["root"]), summary)  # 로컬 절대경로가 없다(N13)


if __name__ == "__main__":
    unittest.main()
