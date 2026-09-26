"""real_sealed 채점 표본 추출(로드맵 DT7 ③). 표준 라이브러리만 쓴다.

방법 정본: docs/tracking/decisions/20260925-0845-user-decision-real-sealed-sampling-method.md ②
- N = 사례 목록 cases 항목 수. N <= 40이면 표본은 사례 전체.
- N > 40이면 사례마다 순위 값 = sha256(seed 파일 바이트 그대로 + b":" + case_id UTF-8)의 16진수 소문자 64자,
  (순위 값, case_id) 오름차순 정렬의 앞 40건.
표준 출력에는 건수·파일 이름·해시만 낸다. 사례 식별자·seed·nonce는 내지 않는다.
사용: python sample.py <real_sealed 폴더> <사례 목록 파일 이름> <code_version> <seed sha256 기대값>
"""
import datetime
import hashlib
import json
import os
import secrets
import sys

EXPECTED_SEED_SIZE = 168
SAMPLE_CAP = 40
KST = datetime.timezone(datetime.timedelta(hours=9))


def sha256_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main() -> int:
    folder, case_list_file, code_version, expected_seed_sha = sys.argv[1:5]
    seed_path = os.path.join(folder, "sample_seed.json")
    with open(seed_path, "rb") as f:
        seed_bytes = f.read()
    seed_sha = hashlib.sha256(seed_bytes).hexdigest()
    if seed_sha != expected_seed_sha or len(seed_bytes) != EXPECTED_SEED_SIZE:
        print("BLOCKED: seed file hash/size mismatch")
        return 2

    case_list_path = os.path.join(folder, case_list_file)
    case_list_sha = sha256_file(case_list_path)
    with open(case_list_path, "rb") as f:
        case_list = json.loads(f.read().decode("utf-8"))
    if case_list.get("dataset") != "real_sealed" or case_list.get("policy_version") != "policy_v1" \
            or case_list.get("snapshot_id") != "kcs_202201_202412_v2":
        print("BLOCKED: case list header mismatch")
        return 3
    case_ids = [c["case_id"] for c in case_list["cases"]]
    n = len(case_ids)
    if len(set(case_ids)) != n:
        print("BLOCKED: duplicate case_id in case list")
        return 4

    if n <= SAMPLE_CAP:
        sample = sorted(case_ids)
    else:
        ranked = sorted((hashlib.sha256(seed_bytes + b":" + cid.encode("utf-8")).hexdigest(), cid) for cid in case_ids)
        sample = [cid for _, cid in ranked[:SAMPLE_CAP]]

    now = datetime.datetime.now(KST)
    name = f"sample-{now.strftime('%y%m%d%H%M%S')}.json"
    payload = {
        "schema_version": 2,
        "dataset": "real_sealed",
        "snapshot_id": "kcs_202201_202412_v2",
        "policy_version": "policy_v1",
        "code_version": code_version,
        "case_list_file": case_list_file,
        "case_list_sha256": case_list_sha,
        "seed_file": "sample_seed.json",
        "seed_file_sha256": seed_sha,
        "method": "docs/tracking/decisions/20260925-0845-user-decision-real-sealed-sampling-method.md ②",
        "alert_count": n,
        "sample_size": len(sample),
        "nonce": secrets.token_hex(32),
        "cases": sample,
    }
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    fd = os.open(os.path.join(folder, name), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    print(f"alert_count={n}")
    print(f"sample_size={len(sample)}")
    print(f"over_cap={'yes' if n > SAMPLE_CAP else 'no'}")
    print(f"sample_file={name}")
    print(f"created_at={now.isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
