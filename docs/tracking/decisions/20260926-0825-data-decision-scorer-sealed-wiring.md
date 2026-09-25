# 채점기의 봉인 파일 이름·봉인 묶음 실행 이름 배선

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-26(토) 08:25 무렵 |
| 제목 | 독립 채점기(`eval/scorer/__main__.py`)가 봉인 묶음을 채점할 때 읽을 파일 이름(`SEALED_FILES`)과 봉인 묶음 실행 이름 → 묶음 기록 도메인명(`BATCH_DOMAINS`)을 채운다. 룰북 `RB-1` 동결 전 확정 항목이다 |
| 결정 | ① `SEALED_FILES` = holdout40 정답표 `holdout40/answers/answers.json`, `real_sealed` 채점 표본 `real_sealed/sample-260926065820.json`(둘 다 봉인 폴더 기준 상대경로. 해시 목록 `eval/sealed_manifest.json`의 `file_name`과 글자까지 같고, 채점기는 해시 대조 뒤에만 읽는다. 자료 계약 §12.2) ② `BATCH_DOMAINS`에 봉인 묶음 실행 이름 `sealed_evaluate` → 묶음 기록 도메인명 `evaluation_sealed_runner`(단위 E2의 도메인명. 로드맵 MT7 `[미확인]`을 오케스트레이터가 정함, 구현은 브랜치 `model/MT7-sealed-runner`) ③ 시험: 두 이름이 해시 목록에 한 번씩 있고 상대경로·`..` 없음, 배선 값 고정 |
| 이유와 근거 | 채점기는 해시 목록에 있는 파일만 읽고(`read_sealed_file`), `real_sealed` 표본은 `{"cases": [case_id, ...]}` 모양이다(`check_sealed_sample`). 두 이름은 격리된 생성 에이전트의 해시 목록 보고에서 왔다(해시 등록 결정 기록 `20260926-0715-orchestrator-decision-sealed-hash-registration.md`) `[사실]`. 표본 파일 이름의 시각은 생성 시각이며 내용을 드러내지 않는다 |
| 결정 주체 | 소유 트랙(D). 실행 이름·도메인명은 오케스트레이터 결정(MT7) |
| 공용 약속 여부 | 아니다. 채점 규칙·자료 형식·명령은 그대로다. 자료 계약 §8·§10.3의 "MT7에서 F1 전에 정한다 `[미확인]`" 문장을 확정값으로 바꾸는 것은 문서 PR(사용자 확인)이 한다 |
| 영향 | 봉인 묶음 채점(F2)이 정답표·표본을 읽을 수 있다. 단위 E2 실행기는 같은 이름으로 묶음 기록을 써야 한다(`outputs/sealed/sealed_evaluate-{시각}/evaluation_sealed_runner-{시각}.jsonl`) |
| 관련 PR | 이 기록의 PR(브랜치 `data/DT8-sealed-wiring`), E2 실행기 PR(`model/MT7-sealed-runner`), 해시 등록 PR #79 |
