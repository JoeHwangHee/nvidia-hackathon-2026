"""holdout40 봉인 직전 검사 1: 원천으로 수집기 SQLite를 재현하고 단위 S2로 빌드, 단위 S3로 검증(raw 대조 포함).

dev20과 같은 절차(명세 §7.3, eval/datagen/dev20.py install)를 저장소·봉인 폴더 밖 임시 폴더에서 한다. 통과하면 빌드
기록 사본을 묶음의 input/source/snapshot_build.json에 쓴다. 이미 있으면 쓰지 않고, 시각·설치 출처 키
(built_at·installed_from·installed_at·build_file)를 뺀 기록 키가 다시 빌드한 기록과 같은지만 본다(읽기 전용 재검사). 사례 목록의
snapshot_normalized_sha256과 빌드 결과가 같아야 한다.

사용(저장소 작업 폴더에서, PYTHONPATH에 저장소 작업 폴더):
  python build_check.py --bundle <holdout40 폴더> --tmp <임시 폴더>
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from eval.datagen import dev20
from tradesentry.contract import types
from tradesentry.contract.policy_load import load_policy
from tradesentry.snapshot import build as s2
from tradesentry.snapshot import verify as s3

SNAPSHOT_ID = "holdout40"


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--tmp", required=True)
    args = parser.parse_args(argv)
    bundle, tmp = Path(args.bundle), Path(args.tmp)
    src = bundle / "input" / "source"
    peer = src / f"peer_group_{SNAPSHOT_ID}.csv"
    cases = json.loads((bundle / "input" / "cases.json").read_text(encoding="utf-8"))
    policy = load_policy(cases["policy_version"])
    collector = dev20.materialize_collector(src, src / "raw", tmp / SNAPSHOT_ID)
    stamp = datetime.now(types.KST).strftime("%y%m%d%H%M%S")
    run_dir = tmp / "build"
    run_dir.mkdir()
    record = s2.build_snapshot(SNAPSHOT_ID, out_dir=run_dir, stamp=stamp, source_dir=collector, policy=policy,
                               peer_group_files=[peer])
    build_file = run_dir / f"{s2.DOMAIN}-{stamp}.sqlite"
    report = s3.verify_snapshot(SNAPSHOT_ID, build_file=build_file, source_dir=collector, check_raw=True,
                                peer_group_files=[peer])
    failed = [c["name"] for c in report["checks"] if c["ok"] is False]
    matches = record["normalized_sha256"] == cases.get("snapshot_normalized_sha256")
    summary = {"snapshot_verify_ok": bool(report["ok"]), "checks": len(report["checks"]), "failed_checks": failed,
               "normalized_sha256_matches_cases": matches,
               "recorded_matches": report.get("recorded_normalized_sha256") == record["normalized_sha256"],
               "confirmed_no_trade_rows": record["confirmed_no_trade_rows"],
               "policy_version": record["policy_version"], "row_counts": record["row_counts"]}
    ok = report["ok"] and matches and record["confirmed_no_trade_rows"] == 0 and summary["recorded_matches"]
    target = src / s2.BUILD_RECORD
    time_keys = ("built_at", "installed_from", "installed_at", "build_file")
    if ok and target.exists():
        recorded = json.loads(target.read_text(encoding="utf-8"))
        same = {k: v for k, v in recorded.items() if k not in time_keys} == \
            {k: v for k, v in record.items() if k not in time_keys}
        summary["existing_record_matches"] = same
        ok = ok and same
    elif ok:
        installed = {**record, "build_file": s2.BUILD_FILE, "installed_from": build_file.name,
                     "installed_at": datetime.now(types.KST).isoformat(timespec="seconds")}
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as fh:
            fh.write((json.dumps(installed, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    print(json.dumps({"ok": bool(ok), **summary}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
