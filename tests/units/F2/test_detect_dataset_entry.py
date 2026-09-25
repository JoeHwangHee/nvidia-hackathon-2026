"""조립 작업 AS1 세 번째 PR: 봉인용 탐지 입구 dispatch.detect_dataset_cases 시험.

- 자료는 detect 조립 시험(test_detect_command.py)과 같은 합성 스냅샷이다. 값은 모두 합성이고, 실자료 모양 시험은 수집기 메타의
  출처 종류만 real로 만든 것과 임시 파일의 합성 분할 기록(dispatch.REAL_SPLIT_FILES를 clear=True로 바꾼다)을 쓴다. 실제
  v1·v2 스냅샷과 저장소의 분할 기록 정본 파일로는 돌리지 않는다. real_sealed 묶음은 합성 자료로만 부른다.
- 입구의 출력 폴더는 저장소 밖 임시 폴더다. 거부 시험만 저장소 안에 이미 있는 폴더(src/tradesentry 등)를 여러 글자 경로로
  넘기고, 그때 파일이 생기지 않음을 본다. 저장소 안에 폴더를 새로 만들지 않는다.
"""
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tradesentry.cli import dispatch
from tradesentry.contract import policy_load
from tradesentry.dal import query
from tradesentry.metrics import share, unit_value
from tradesentry.policy import case_build, trigger

from . import detect_fixture as df
from .test_detect_command import (EXPECTED, MAIN_ID, SPLIT_DEV, SPLIT_SEALED, DetectCase, RealSnapshotCase,
                                  split_record, value_read_spies)

ROOT = Path(__file__).resolve().parents[3]
FILE_RE = re.compile(r"^policy_case_build-[0-9]{12}\.json$")  # 도메인명: docs/plan/UNITS.md §3.4 P2 행 글자 그대로


class EntryCase(RealSnapshotCase):
    """출력 폴더(저장소 밖 임시 폴더)와, 입구가 쓰면 안 되는 outputs 자리(dispatch.OUTPUT_PARENT)를 시험마다 새로 둔다."""

    def setUp(self):
        super().setUp()
        self.out = self.root / "sealed_like"
        self.out.mkdir()
        self.forbidden_outputs = self.root / "outputs_must_not_exist"
        patcher = mock.patch.object(dispatch, "OUTPUT_PARENT", self.forbidden_outputs)
        patcher.start()
        self.addCleanup(patcher.stop)

    def entry(self, dataset: str, out_dir=None, *, snapshot: str = MAIN_ID, policy: str = "dev-0.1") -> dict:
        """입구를 한 번 부른다. 표준 출력·표준 오류에 아무것도 쓰지 않고, outputs 자리를 만들지 않으며 실행명을 확보하지 않는다."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                mock.patch.object(dispatch, "reserve_run_dir", wraps=dispatch.reserve_run_dir) as reserve:
            try:
                return dispatch.detect_dataset_cases(snapshot, policy, dataset, self.out if out_dir is None else out_dir)
            finally:
                self.assertEqual((out.getvalue(), err.getvalue()), ("", ""))
                self.assertEqual(reserve.call_count, 0)
                self.assertFalse(os.path.lexists(self.forbidden_outputs))

    def written(self, returned: dict) -> bytes:
        """출력 폴더의 파일 하나(돌려받은 이름)를 읽는다. 로컬 절대경로가 들어 있지 않다(N13)."""
        self.assertEqual(set(returned), {"file_name", "code_version"})
        self.assertRegex(returned["file_name"], FILE_RE)
        self.assertEqual(returned["code_version"], dispatch.code_version())
        self.assertEqual(sorted(p.name for p in self.out.iterdir()), [returned["file_name"]])
        data = (self.out / returned["file_name"]).read_bytes()
        for local in (str(self.root), str(self.snapshots), str(ROOT)):
            self.assertNotIn(local.encode("utf-8"), data)
        return data


class RealDevEntryTest(EntryCase):
    """real_dev로 부르면 출력 바이트가 CLI detect의 출력 파일과 같다(같은 경로)."""

    def setUp(self):
        super().setUp()
        self.use_split(split_record())

    def test_real_dev_bytes_equal_the_cli_detect_output(self):
        code, out, err, run_dir = self.detect()
        self.assertEqual((code, err), (0, ""))
        [cli_file] = list(run_dir.iterdir())
        returned = self.entry("real_dev")
        data = self.written(returned)
        self.assertEqual(data, cli_file.read_bytes())
        result = json.loads(data)
        self.assertEqual(result["dataset"], "real_dev")
        self.assertEqual({c["partner"] for c in result["cases"]}, {"CN", "FI", "US"})  # 공허하지 않다


class RealSealedEntryTest(EntryCase):
    """real_sealed로 부르면(합성 자료) 분할 기록의 real_sealed 계열만 남긴 뒤 값을 읽는다. real_dev 계열의 관측 행은 읽지 않고,
    출력은 합성 기대 출력에서 real_sealed 계열 행만 고른 것과 같다."""

    def setUp(self):
        super().setUp()
        self.use_split(split_record())

    def test_output_is_the_real_sealed_cases(self):
        result = json.loads(self.written(self.entry("real_sealed")))
        sealed = set(SPLIT_SEALED)
        self.assertEqual(result, {
            "snapshot_id": MAIN_ID, "dataset": "real_sealed", "policy_version": "dev-0.1",
            "cases": [c for c in EXPECTED["cases"] if c["partner"] in sealed],
            "data_quality": [q for q in EXPECTED["data_quality"] if q["partner"] in sealed]})
        self.assertEqual({c["partner"] for c in result["cases"]}, {"DE", "JP", "TW"})  # 공허하지 않다

    def test_real_dev_rows_are_never_read(self):
        dev = set(SPLIT_DEV)
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
            returned = self.entry("real_sealed")
        self.assertEqual(events[0], "load_real_split")
        self.assertEqual(events.count("load_real_split"), 1)
        self.assertTrue(read_rows)
        self.assertEqual([p for p in read_params if dev & set(p)], [])
        self.assertEqual([r for r in read_rows if r.get("partner_code") in dev], [])
        self.assertEqual(sorted(c.args[2] for c in parent_series.call_args_list), SPLIT_SEALED)
        self.assertEqual(world_series.call_count, 1)
        self.assertEqual(sorted({c.args[0]["partner"] for c in x1.call_args_list}), SPLIT_SEALED)
        self.assertEqual(sorted({c.args[0]["partner"] for c in x2.call_args_list}), SPLIT_SEALED)
        self.assertEqual((x1.call_count, x2.call_count), (10, 10))
        [p1_call] = p1.call_args_list
        self.assertEqual(sorted({row["partner"] for row in p1_call.args[0]["rows"]}), SPLIT_SEALED)
        [p2_call] = p2.call_args_list
        given = p2_call.args[0]
        self.assertEqual((given["source_kind"], given["dataset"]), ("real", "real_sealed"))
        self.assertEqual(given["series_assignment"],
                         [{"hs6": df.HS6, "partner": p, "dataset": "real_dev" if p in dev else "real_sealed"}
                          for p in sorted(SPLIT_DEV + SPLIT_SEALED)])
        self.assertEqual(json.loads(self.written(returned))["dataset"], "real_sealed")


class TwoHs6SealedPairTest(DetectCase):
    """real_sealed 좁히기도 (hs6, partner) 쌍 단위다(합성 스냅샷 as1_detect_two_hs6)."""

    SPEC = df.TWO_HS6
    BUILD_POLICY = None
    SOURCE_KIND = "real"
    TWO_ID = df.TWO_HS6["config"]["snapshot_id"]
    DEV = [(df.HS6, "CN"), (df.SIBLING_HS6, "JP")]
    SEALED = [(df.HS6, "JP"), (df.SIBLING_HS6, "CN")]

    def setUp(self):
        super().setUp()
        record = {"snapshot_id": self.TWO_ID, "seed": 1, "ratio": {"real_dev": 1, "real_sealed": 1},
                  "method": "hs6_stratified_sha256_rank",
                  "real_dev": [{"hs6": h, "partner": p} for h, p in self.DEV],
                  "real_sealed": [{"hs6": h, "partner": p} for h, p in self.SEALED]}
        path = self.root / "real_split.json"
        path.write_text(json.dumps(record), encoding="utf-8")
        patcher = mock.patch.dict(dispatch.REAL_SPLIT_FILES, {self.TWO_ID: str(path)}, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.out = self.root / "sealed_like"
        self.out.mkdir()

    def test_real_sealed_narrowing_is_by_pair(self):
        dev = set(self.DEV)
        read_params: list[tuple] = []
        read_rows: list[dict] = []
        real_rows = query.Snapshot._rows

        def rows_spy(snap, where, params):
            found = real_rows(snap, where, params)
            read_params.append(tuple(params))
            read_rows.extend(found)
            return found

        with mock.patch.object(query.Snapshot, "_rows", autospec=True, side_effect=rows_spy), \
                mock.patch.object(query.Snapshot, "parent_series", autospec=True,
                                  side_effect=query.Snapshot.parent_series) as parent_series, \
                mock.patch.object(unit_value, "run", wraps=unit_value.run) as x1, \
                mock.patch.object(trigger, "run", wraps=trigger.run) as p1:
            returned = dispatch.detect_dataset_cases(self.TWO_ID, "dev-0.1", "real_sealed", self.out)
        self.assertEqual(sorted(c.args[1:3] for c in parent_series.call_args_list), sorted(self.SEALED))
        self.assertEqual([p for p in read_params if len(p) >= 2 and (p[1], p[0]) in dev], [])
        self.assertTrue(read_rows)
        self.assertEqual([r for r in read_rows if len(r["hs_code"]) >= 6
                          and (r["hs_code"][:6], r["partner_code"]) in dev], [])
        self.assertEqual(sorted({(c.args[0]["hs6"], c.args[0]["partner"]) for c in x1.call_args_list}),
                         sorted(self.SEALED))
        [p1_call] = p1.call_args_list
        self.assertEqual(sorted({(r["hs6"], r["partner"]) for r in p1_call.args[0]["rows"]}), sorted(self.SEALED))
        result = json.loads((self.out / returned["file_name"]).read_text(encoding="utf-8"))
        self.assertEqual(result["dataset"], "real_sealed")
        self.assertEqual(sorted((c["hs6"], c["partner"]) for c in result["cases"]), sorted(self.SEALED))


class EntryRefusalTest(EntryCase):
    """거부하는 경우는 관측 값을 읽지 않고 파일을 남기지 않는다. 묶음·출력 폴더 확인은 정책·스냅샷을 열기 전이다."""

    def setUp(self):
        super().setUp()
        self.use_split(split_record())

    def assert_refused(self, exc_type, *, dataset: str = "real_sealed", out_dir=None, opens: bool = False) -> None:
        spies = value_read_spies()
        with contextlib.ExitStack() as stack:
            mocks = {name: stack.enter_context(patcher) for name, patcher in spies.items()}
            loader = stack.enter_context(mock.patch.object(policy_load, "load_policy", wraps=policy_load.load_policy))
            opener = stack.enter_context(mock.patch.object(query, "open_snapshot", wraps=query.open_snapshot))
            with self.assertRaises(exc_type) as caught:
                self.entry(dataset, out_dir)
        self.assertEqual({name: m.call_count for name, m in mocks.items()}, dict.fromkeys(spies, 0))
        self.assertEqual((loader.call_count, opener.call_count), (int(opens), int(opens)))
        self.assertEqual(list(self.out.iterdir()), [])
        text = str(caught.exception)
        received = [dataset] if isinstance(dataset, str) and dataset and dataset not in dispatch.ENTRY_DATASETS else []
        for value in [MAIN_ID, str(self.root), str(ROOT)] + received:
            self.assertNotIn(value, text)  # 받은 값·로컬 절대경로를 넣지 않는다(N13)

    def test_unknown_dataset_is_refused_first(self):
        for dataset in ("dev20", "holdout40", "REAL_SEALED", "", None):
            with self.subTest(dataset):
                self.assert_refused(dispatch.DatasetEntryError, dataset=dataset)

    def test_out_dir_inside_the_repo_is_refused(self):
        """저장소 안 폴더는 경로 글자가 어떻든 거부한다(파일 정체성 비교). 저장소 안에 새 폴더를 만들지 않고 이미 있는 폴더를 쓴다."""
        inside = ROOT / "src" / "tradesentry"
        watched = (ROOT, inside, inside / "cli")
        before = [sorted(p.name for p in folder.iterdir()) for folder in watched]
        link = self.root / "link_into_repo"
        link.symlink_to(inside, target_is_directory=True)
        variants = {"저장소 뿌리": ROOT, "저장소 안 폴더": inside, "문자열": str(inside),
                    "상대경로": os.path.relpath(inside, os.getcwd()),
                    "..가 든 경로": str(ROOT / "src" / ".." / "src" / "tradesentry"),
                    "저장소로 가는 링크": link, "링크 아래 하위 폴더": link / "cli"}
        swapped = str(inside).swapcase()
        if os.path.exists(swapped):  # 대소문자를 구별하지 않는 파일 시스템(macOS 기본): 같은 폴더의 다른 글자 경로
            self.assertTrue(os.path.samefile(swapped, inside))
            variants["대소문자를 바꾼 경로"] = swapped
            variants["대소문자를 바꾼 뿌리"] = str(ROOT).swapcase()
        else:  # 대소문자를 구별하는 파일 시스템: 바꾼 경로는 다른(없는) 폴더다
            self.assertFalse(os.path.lexists(swapped))
        firmlink = "/System/Volumes/Data" + str(inside.resolve())
        if sys.platform == "darwin" and os.path.isdir(firmlink):  # macOS firmlink: 데이터 볼륨 쪽의 같은 폴더
            self.assertTrue(os.path.samefile(firmlink, inside))
            variants["firmlink 경로"] = firmlink
        for label, out_dir in variants.items():
            with self.subTest(label):
                self.assert_refused(dispatch.DatasetEntryError, out_dir=out_dir)
        self.assertEqual([sorted(p.name for p in folder.iterdir()) for folder in watched], before)  # 저장소에 파일이 없다

    def test_every_git_worktree_is_refused(self):
        """본 작업 폴더와 git이 아는 모든 worktree(`git worktree list --porcelain`) 안의 폴더를 거부한다."""
        listed = git_worktrees()
        self.assertIn(ROOT.resolve(), listed)
        for tree in listed:
            if tree.is_dir():
                with self.subTest(str(tree)):
                    self.assert_refused(dispatch.DatasetEntryError, out_dir=tree)

    def test_missing_or_non_folder_out_dir_is_refused(self):
        a_file = self.root / "a_file"
        a_file.write_text("x", encoding="utf-8")
        for label, out_dir in (("없는 폴더", self.root / "no_such"), ("파일", a_file), ("경로 아님", 3)):
            with self.subTest(label):
                self.assert_refused(dispatch.DatasetEntryError, out_dir=out_dir)
        self.assertFalse((self.root / "no_such").exists())  # 입구는 폴더를 만들지 않는다

    def test_controlled_snapshot_is_refused_before_values(self):
        with mock.patch.object(query.Snapshot, "source_kind", new_callable=mock.PropertyMock, return_value="controlled"), \
                mock.patch.object(dispatch, "load_real_split", wraps=dispatch.load_real_split) as split_loader:
            self.assert_refused(dispatch.DatasetEntryError, opens=True)
        self.assertEqual(split_loader.call_count, 0)

    def test_split_error_is_raised_before_values(self):
        self.use_split(None, raw="{not json")
        self.assert_refused(dispatch.SplitError, opens=True)
        self.use_split(split_record(dev=SPLIT_DEV[:-1]))
        self.assert_refused(dispatch.SplitError, opens=True)

    def test_policy_and_snapshot_errors_leave_no_file(self):
        with self.assertRaises(policy_load.PolicyError):
            self.entry("real_sealed", policy="no-such-policy")
        with self.assertRaises(query.SnapshotError):
            self.entry("real_sealed", snapshot="no_such_snapshot")
        self.assertEqual(list(self.out.iterdir()), [])

    def test_case_build_of_another_dataset_is_a_wiring_error(self):
        real = case_build.run

        def other_dataset(inp):
            return {**real(inp), "dataset": "real_dev"}

        with mock.patch.object(case_build, "run", side_effect=other_dataset):
            with self.assertRaises(dispatch.WiringError):
                self.entry("real_sealed")
        self.assertEqual(list(self.out.iterdir()), [])

    def test_existing_file_is_not_overwritten(self):
        fixed = dispatch.now_kst()
        with mock.patch.object(dispatch, "now_kst", return_value=fixed):
            first = self.entry("real_sealed")
            before = (self.out / first["file_name"]).read_bytes()
            with self.assertRaises(dispatch.DatasetEntryError):
                self.entry("real_sealed")
        self.assertEqual(sorted(p.name for p in self.out.iterdir()), [first["file_name"]])
        self.assertEqual((self.out / first["file_name"]).read_bytes(), before)

    def test_failed_write_leaves_no_partial_file(self):
        real_write_all = dispatch._write_all

        def broken(fd, payload):
            real_write_all(fd, payload[:10])
            raise OSError("disk full")

        with mock.patch.object(dispatch, "_write_all", side_effect=broken):
            with self.assertRaises(OSError):
                self.entry("real_sealed")
        self.assertEqual(list(self.out.iterdir()), [])

    def test_out_dir_swapped_after_the_check_is_refused(self):
        """확인한 뒤 탐지하는 동안 출력 폴더가 바뀌면(저장소로 가는 링크, 같은 이름의 다른 폴더) 쓰기 직전 재확인에서 거부한다."""
        inside = ROOT / "src" / "tradesentry"
        before = sorted(p.name for p in inside.iterdir())
        real_build = dispatch.build_case_list
        for label in ("저장소로 가는 링크", "같은 이름의 다른 폴더"):
            moved = self.root / f"moved-{len(label)}"

            def swap(snap, policy, dataset, label=label, moved=moved):
                result = real_build(snap, policy, dataset)
                self.out.rename(moved)
                if label == "저장소로 가는 링크":
                    self.out.symlink_to(inside, target_is_directory=True)
                else:
                    self.out.mkdir()
                return result

            with self.subTest(label), mock.patch.object(dispatch, "build_case_list", side_effect=swap):
                with self.assertRaises(dispatch.DatasetEntryError):
                    self.entry("real_sealed")
                self.assertEqual(list(moved.iterdir()), [])
                if self.out.is_symlink():
                    self.out.unlink()
                else:
                    self.assertEqual(list(self.out.iterdir()), [])
                    self.out.rmdir()
                moved.rename(self.out)
        self.assertEqual(sorted(p.name for p in inside.iterdir()), before)


def git_worktrees() -> set[Path]:
    """`git worktree list --porcelain`이 적는 작업 폴더(본 작업 폴더 포함)의 실제 경로."""
    listed = subprocess.run(["git", "-C", str(ROOT), "worktree", "list", "--porcelain"], capture_output=True, text=True,
                            check=True).stdout
    return {Path(line[len("worktree "):]).resolve() for line in listed.splitlines() if line.startswith("worktree ")}


class RepoRootsTest(unittest.TestCase):
    """저장소 뿌리: 이 작업 폴더, 본 작업 폴더, git이 아는 모든 worktree(공용 폴더 worktrees/*/gitdir)."""

    def test_roots_are_the_git_worktree_list(self):
        self.assertEqual({root.resolve() for root in dispatch._repo_roots()}, git_worktrees())

    def test_fake_layout_from_a_worktree_and_from_the_main_checkout(self):
        with tempfile.TemporaryDirectory() as name:
            base = Path(name).resolve()
            main_root, worktree, sibling = base / "main", base / "wt", base / "other"
            common = main_root / ".git"
            for tree in (worktree, sibling):
                gitdir = common / "worktrees" / tree.name
                gitdir.mkdir(parents=True)
                (gitdir / "commondir").write_text("../..\n", encoding="utf-8")
                (gitdir / "gitdir").write_text(f"{tree / '.git'}\n", encoding="utf-8")
                tree.mkdir()
                (tree / ".git").write_text(f"gitdir: {gitdir}\n", encoding="utf-8")
            with mock.patch.object(query, "REPO_ROOT", worktree):
                self.assertEqual(dispatch._repo_roots(), [worktree, main_root, sibling])
            with mock.patch.object(query, "REPO_ROOT", main_root):
                self.assertEqual(dispatch._repo_roots(), [main_root, sibling, worktree])
            (sibling / "deep").mkdir()
            with mock.patch.object(query, "REPO_ROOT", worktree):
                for refused in (main_root, sibling / "deep", worktree):
                    with self.subTest(str(refused)), self.assertRaises(dispatch.DatasetEntryError):
                        dispatch._entry_out_dir(refused)
                folder, identity = dispatch._entry_out_dir(base)  # 뿌리들의 부모는 저장소 밖이다
                self.assertEqual(folder, base)
                self.assertEqual(identity, (os.stat(base).st_dev, os.stat(base).st_ino))


if __name__ == "__main__":
    unittest.main()
