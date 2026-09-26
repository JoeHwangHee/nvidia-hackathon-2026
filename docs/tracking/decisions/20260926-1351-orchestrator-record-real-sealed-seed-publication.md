# 기록: `real_sealed` 표본 추출 seed 공개(정답 대조 채점 뒤)

룰북 B6과 병렬 개발 규칙 §6.2·§6.3에 따라 `real_sealed`(실자료 봉인 묶음)의 표본 추출 seed 파일(nonce 포함. 경보가 40건을 넘을 때 채점 표본을 뽑는 고정 난수의 시작값)을 정답 대조 채점이 끝난 뒤 공개한다. 이 기록이 있어야 `real_sealed` 봉인 실행 출력과 그 채점기 출력의 금지 해제 조건(자료 계약 §10.3 N10)이 채워진다.

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-26(토) 13:51(기록 시각) |
| 채점 완료 | `real_sealed` 공식 실행 `outputs/sealed/sealed_evaluate-260926114518` → 채점기 실행 `outputs/score-260926135136`(종료 코드 0, 봉인 사건 "채점 완료"). `holdout40`은 `outputs/score-260926115824`(11:58:24) |
| seed 파일 | 해시 목록 `eval/sealed_manifest.json`의 `real_sealed/sample_seed.json`, sha256 `5732e950632547d5dbb3763dc16e5ceb0d8494b07bcc5daebbb9d9ba75842408`(결정 기록 `20260924-2340-dt4-real-split-and-sample-seed.md`에 같은 값이 policy_v1 수치 제안 전에 기록됨) |
| 표본 방법 | 결정 기록 `20260925-0845-user-decision-real-sealed-sampling-method.md`(사용자 결정 3)의 방법. 표본 생성은 격리 에이전트가 2026-09-26(토) 06:57~06:58에 했다(결정 기록 `20260926-0715-orchestrator-decision-sealed-hash-registration.md`: 경보 470건 → 표본 40건) |
| 결정 주체 | 오케스트레이터(기록). 공개 시점 규칙은 룰북 B6·병렬 개발 규칙 §6.2 `[사실]` |
| 공용 약속 여부 | 아니오(정해진 절차의 이행) |
| 원본 위치 | 봉인 원본 커밋 `eval/sealed/real_sealed/sample_seed.json`(사용자 결정 `20260926-1225-user-decision-r1-paths.md`) |

## seed 파일 내용(바이트 그대로) `[사실: 봉인 폴더에서 읽어 옮김, sha256 위와 같음]`

```json
{"dataset":"real_sealed","kind":"sample_seed","nonce":"30381cbbc220b0a33be26d72b0b68f7f494f1b8989bfe3e2452102943e56d667","schema_version":1,"seed":3083718519329212112}
```
