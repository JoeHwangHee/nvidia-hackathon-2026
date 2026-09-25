# 실자료 v2 정본 빌드를 계약 버전 2로 다시 설치

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 12:31(기록 시각). 재설치는 같은 날 12:30에 했다 |
| 제목 | 계약 버전 v2(사용자 결정 `20260925-1205-user-decision-schema-v2.md`, 코드·자료 PR #46) 뒤 `kcs_202201_202412_v2` 정본 빌드(`snapshot_build.sqlite`·`snapshot_build.json`)를 새 계약으로 다시 만들어 설치 |
| 결정 | DT7 ② 결정 기록 `20260925-0920-data-decision-dt7-final-build.md` ①의 구동 순서 그대로 다시 설치한다: 실행명 확보 → `policy_v1` 읽기 → 단위 S2 빌드(비교국 표 `data/reference/peer_group_g0.csv`, 사용자 결정 11의 D10) → 단위 S3 검증(raw 대조 포함) → 단위 S2 `install_build`. 정본 자리의 파생 파일 두 개만 먼저 지웠다(`install_build`는 덮어쓰지 않는다). 동결 원자료는 읽기만 했다 |
| 결과 | 새 `normalized_sha256` `31928884d4ce8d47358b10d09035309af664d8951eaacdd2a7230c6fb900a205`(앞 값 `b439909a…4639`). 설치 전 S3 검증 `ok` 참, 검사 18개 모두 통과. 설치 뒤 `tradesentry snapshot-verify --snapshot kcs_202201_202412_v2` 종료 코드 0. 빌드 기록의 차이는 `schema_version`(1→2), `normalized_sha256`, `built_at`·`installed_from`·`installed_at`뿐이다(승격 행, 비교국 표 출처, raw 결합 해시, 행 수는 그대로) |
| 동결 파일 확인 | 재설치 전과 뒤의 sha256이 같다: `collection_http_attempts.jsonl`, `data-readiness.json`, `manifest.json`, `snapshot_hash.json`, `snapshot.sqlite`, raw 결합 해시 `afc76401431f02b4d8d5e848b197faaa197ce3dd037d66fd7ca719d7ce7bb017`(= `snapshot_hash.json`의 기록). 수집기의 `plan`·`collect`는 돌리지 않았다 |
| 교차 확인 | `tradesentry detect --snapshot kcs_202201_202412_v2 --policy policy_v1` 종료 코드 0, `dataset` real_dev, 사례 221건, 데이터 품질 154행 — DT7 ① 기록(`20260925-0925-data-decision-dt7-real-dev-mvp-selection.md`)과 같다 |
| 결정 주체 | 오케스트레이터(재설치 실행). 계약 버전 변경은 사용자 결정 |
| 공용 약속 여부 | 아니다. 사용자가 정한 계약 버전 변경을 정본 빌드에 적용한 것이다 |
| 영향 | 샌드박스 반입(재스테이징) 때 이 빌드를 굽는다. `real_sealed` 사례 목록(DT7 ③)과 봉인 해시 등록은 탐지·CLI 코드 동결 뒤 이 빌드로 한다 |
| 관련 PR | 이 기록의 PR(브랜치 `data/DT7-reinstall-v2`) |
