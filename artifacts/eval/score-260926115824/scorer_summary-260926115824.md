# 평가 결과 요약 — sealed_evaluate-260926101039

채점기(eval/scorer)가 쓴 요약이다. 에이전트는 이 파일을 고쳐 쓰지 않는다(자료 계약 §10.3 N8). 등급 표기는 룰북 A5·B7을 따른다.

## 0. 실행 조건

- 룰북: RB-1, 동결 커밋 c557540f743ffc77a996a2a227d68d0bbfa0f08e, 동결 뒤 변경 동결 대상은 없음 — 실행 시작 시각에 git diff c557540f743ffc77a996a2a227d68d0bbfa0f08e HEAD -- docs/eval/RULEBOOK.md eval/scorer/ configs/policy_v1.json src/tradesentry/validator 0줄, 자료 계약 §11 동일. 동결 대상 밖 변경: run-case --sealed(code_version d35fe756a3065fbdbcc60110a91e8f912a5ffc74), 자료 계약 §10 CLI 행·경로 행. 채점 직전에 다시 확인한다
- snapshot_id holdout40, 스냅샷 정규화 해시(normalized_sha256) 미기재(실행 조건 입력 파일에 없음), 대조 미기재(실행 조건 입력 파일에 없음)
- policy_version policy_v1, grouping_version g0(사유: g0 대체 선언(2026-09-26(토) 08:10 사용자 결정, 결정 기록 20260926-0810-user-decision-rb1-g0-substitute-and-prose-ex2.md). 합성 묶음의 비교국 표는 합성 자료 안에서 만든 표)
- code_version d35fe756a3065fbdbcc60110a91e8f912a5ffc74, 채점기 커밋 074a080, 산문 패턴 목록 커밋 074a080(채점기가 계산한 패턴 목록 지문 sha256 ce8f62765b3607127c24ed053b0e141bc47166275df58eacd7e191d6616eaec4)
- 실행 기간(KST) 2026-09-26T10:10:39+09:00 ~ 2026-09-26T11:44:16+09:00, 동시성 1, 순서 seed rb1-order-v1
- 한도(룰북 B2와 대조한 실행 설정): 도구 호출 시도 8, 재조사 1, 모델 요청 10, 사례당 wall time 300초, 누적 토큰 128000
- 샌드박스 이름 ts-official, 커밋한 라이브 정책 조회 본문(정책 YAML) sha256 8aae74173df4e799315c25023292e3be64bbe308f19d3bfe8871408502d7ecf9, 대조한 시험표 실행 폴더 이름 openshell_violation_tests-260926100925, `configs/openshell/policy.yaml` sha256 dc2e8c3a7707e78cf86c1536ed5535fcf99e592376a2009d190d5564e87785a8
- 봉인 해시 재대조 일치
- 봉인 묶음의 출처 점검(평가 스킬 ② 사전 점검 단계 4의 8번) ① 해시 목록 등록 커밋 dc9e76b(#79, 2026-09-26(토) 07:26)는 policy_v1 사용자 승인 기록(2026-09-25(금) 08:46)보다 뒤이고 동결 커밋 c557540의 조상이다. 등록 커밋→동결 커밋 사이 configs/policy_v1.json과 탐지 단위(unit_value·share·rounding·trigger·case_build·query·policy_load, CLI args.py) 변경 0줄. src/tradesentry/cli/dispatch.py 386줄 변경은 #87 평가 배선 분리이며 탐지 함수 _detect·build_case_list·detect_dataset_cases·detect_series의 AST 지문은 두 커밋에서 같다. 동결 커밋→code_version d35fe756a3065fbdbcc60110a91e8f912a5ffc74 사이의 dispatch.py 변경은 run-case의 --sealed 경로 추가(자료 묶음 표·real_sealed 계열 허용)이며 탐지 함수는 바꾸지 않았다. ② real_sealed 분할 기록(결정 기록 20260924-2340, 커밋 #21 2026-09-25(금) 00:20)은 policy_v1 수치 제안과 승인(2026-09-25(금) 08:46)보다 앞선다. ③ 표본 추출 seed 파일 sha256(5732e950…)이 결정 기록 20260924-2340과 해시 목록 real_sealed 항목에 같이 있다. 한계: 등록 뒤 정책·탐지 코드가 바뀌지 않았다는 것까지만 보인다(병렬 개발 규칙 §6.6·§6.7)
- 채점 전 확인(평가 스킬 ②): 1 예정 실행의 최종 상태 확정 참: 예정 실행 120건 가운데 줄 없는 조합 0건, 인프라 실패 재실행(룰북 B5) 대상 4건·재실행 4건(채점기 계산: 미실행 0건), 2 버전 키 일치 미기재(실행 조건 입력 파일에 없음), 5 모드별 사례 집합 일치 미기재(실행 조건 입력 파일에 없음)(채점기 계산: 참), 순서 seed·동시성 적용 참: 순서 seed rb1-order-v1, 동시성 1, 속도 조절(모델 실행 사이 최소 60초, 분당 토큰 50000, HTTP 429 뒤 120초), 쉰 시간 합 3375초, 429 뒤 더 쉰 횟수 4, 동시성을 올렸다면 근거 결정 기록 동시성 1(룰북 B5 그대로. 올리지 않음)
- 사전 점검 결과 평가 스킬 ② 사전 점검: 단계 3-3 채점기 자체 시험 203건 종료 0(2026-09-26(토) 08:32), 단계 4-3 스냅샷 kcs_202201_202412_v2 검증 ok(normalized_sha256 31928884d4ce8d47358b10d09035309af664d8951eaacdd2a7230c6fb900a205, snapshot_verify-260926083238), 단계 4-5 봉인 해시 목록 전체 대조 202/202(반입 도구 08:1x·08:3x). 단계 4-1·4-2·4-4·4-6·4-8은 동결 커밋 뒤 채움: 4-1 룰북 동결 커밋 c557540f743ffc77a996a2a227d68d0bbfa0f08e(PR #88 squash 2026-09-26(토) 09:20, 사용자 동결 확인 08:53) 뒤 docs/eval/RULEBOOK.md·eval/scorer/·configs/policy_v1.json·src/tradesentry/validator diff 0줄, 자료 계약 §11 자릿수 표 동일(실행 시작 시각 기준). 이 실행의 code_version은 d35fe756a3065fbdbcc60110a91e8f912a5ffc74 — 동결 뒤 run-case에 봉인 실행 경로 --sealed를 더한 수정 커밋(사용자 승인 2026-09-26(토) 09:55, 결정 기록 20260926-0945·20260926-0955). 첫 시작 outputs/sealed/sealed_evaluate-260926092509는 그 결함으로 무효(모델 호출 0, 봉인 내용 산출 0). 4-2 configs/policy_v1.json sha256 0804508a18ca8c848b41f3a90b8cc6f362e986becd76b607380f4786ee73a981 = 동결 커밋의 값(승인 기록 20260925-0846). 4-4 g0 대체 선언 결정 기록 20260926-0810 있음, 실행기 grouping_version g0. 4-6 holdout40_check 종료 코드 0(2026-09-26(토) 08:48, 건수만). 4-7 이 묶음의 유효한 공식 실행·채점 기록 없음(무효 첫 시작만, 채점 안 함). 4-8 아래 출처 점검. 4-9 E2 실행기(#87)와 부록 40 사용자 확인(08:53). 공식 채점 단계 4: 전용 샌드박스 ts-official(수정 커밋 d35fe756a3065fbdbcc60110a91e8f912a5ffc74 이미지, image manifest 359742d70383d0ca99758d985e40f45d150744fd217f216524fb647559c59d15) 공식 위반 시험 openshell_violation_tests-260926100925 모두 일치·불일치 0
- 계약 버전 schema_version 2, 자료 묶음 holdout40, 평가 묶음 실행 sealed_evaluate-260926101039, 채점 실행 score-260926115824
- 채점기가 읽은 스냅샷 파일 data/snapshots/holdout40/snapshot_build.sqlite, 바이트 sha256 a714663f016b8824a9aa34bad366d2e3c46aac28c8a3a6e9f8947f4c7c97f396
- 계획: 사례 40건 × 모드 checklist, agent, full = 예정 실행 120건, 결과 줄 124줄
- 채점 대상 run_id 목록: run_case-260926101039, run_case-260926101040, run_case-260926101147, run_case-260926101206, run_case-260926101207, run_case-260926101247, run_case-260926101347, run_case-260926101447, run_case-260926101547, run_case-260926101605, run_case-260926101647, run_case-260926101747, run_case-260926101904, run_case-260926101905, run_case-260926101906, run_case-260926102104, run_case-260926102204, run_case-260926102222, run_case-260926102304, run_case-260926102404, run_case-260926102721, run_case-260926102821, run_case-260926102921, run_case-260926103021, run_case-260926103043, run_case-260926103044, run_case-260926103121, run_case-260926103221, run_case-260926103327, run_case-260926103527, run_case-260926103538, run_case-260926103627, run_case-260926103704, run_case-260926103727, run_case-260926103838, run_case-260926103938, run_case-260926104007, run_case-260926104008, run_case-260926104009, run_case-260926104042, run_case-260926104142, run_case-260926104242, run_case-260926104253, run_case-260926104254, run_case-260926104342, run_case-260926104442, run_case-260926104456, run_case-260926104542, run_case-260926104547, run_case-260926104548, run_case-260926104642, run_case-260926104654, run_case-260926104742, run_case-260926104842, run_case-260926104901, run_case-260926104945, run_case-260926105045, run_case-260926105211, run_case-260926105212, run_case-260926105213, run_case-260926105313, run_case-260926105323, run_case-260926105413, run_case-260926105538, run_case-260926105539, run_case-260926105540, run_case-260926105640, run_case-260926105740, run_case-260926105813, run_case-260926105814, run_case-260926105840, run_case-260926105940, run_case-260926110040, run_case-260926110140, run_case-260926110240, run_case-260926110340, run_case-260926110440, run_case-260926110451, run_case-260926110452, run_case-260926110540, run_case-260926110640, run_case-260926110658, run_case-260926110659, run_case-260926110700, run_case-260926110740, run_case-260926110840, run_case-260926110940, run_case-260926111054, run_case-260926111203, run_case-260926111439, run_case-260926111503, run_case-260926111504, run_case-260926111539, run_case-260926111639, run_case-260926111739, run_case-260926111839, run_case-260926111939, run_case-260926112039, run_case-260926112124, run_case-260926112139, run_case-260926112147, run_case-260926112239, run_case-260926112339, run_case-260926112439, run_case-260926112539, run_case-260926112639, run_case-260926112739, run_case-260926112839, run_case-260926112939, run_case-260926113054, run_case-260926113154, run_case-260926113214, run_case-260926113254, run_case-260926113354, run_case-260926113454, run_case-260926113554, run_case-260926113654, run_case-260926113754, run_case-260926113854, run_case-260926113954, run_case-260926114054, run_case-260926114154, run_case-260926114254, run_case-260926114354
- 상태 변화 집계(모델 원초안 → Critic 뒤 → 검증 뒤): 집계하지 않음(trace 형식 미정, 단위 L1. F1 전 보완)

## 1. 대표 지표 — 실자료 사실 주장 오류율 (real_sealed)

- 해당 없음(이 채점 실행의 자료 묶음은 holdout40다)

## 2. 보조 지표 — holdout40 (등급 C)

| 비교군 | 근거 충족 처리정확도 x/N(Wilson 95%) | 불필요 보류율 | 잘못된 모니터링률 | 실행 실패 x/N | 도구 시도 중앙값(범위) | 토큰 중앙값(범위) | 시간(ms) 중앙값(범위) | 등급 |
|---|---|---|---|---|---|---|---|---|
| checklist | 38/40 = 95.0% (83.5%~98.6%) | 0/24 = 0.0% (0.0%~13.8%) | 0/33 = 0.0% (0.0%~10.4%) | 0/40(FAILED 0, TIMEOUT 0, INVALID 0, BUDGET_EXCEEDED 0, 미실행 0) | 5(4~5) | 0(0~0) | 17(16~40) | 등급 C |
| agent | 38/40 = 95.0% (83.5%~98.6%) | 0/24 = 0.0% (0.0%~13.8%) | 0/33 = 0.0% (0.0%~10.4%) | 0/40(FAILED 0, TIMEOUT 0, INVALID 0, BUDGET_EXCEEDED 0, 미실행 0) | 5(4~7) | 15919.5(12188~34683) | 12293(2561~85074) | 등급 C |
| full | 35/40 = 87.5% (73.9%~94.5%) | 0/24 = 0.0% (0.0%~13.8%) | 2/33 = 6.1% (1.7%~19.6%) | 1/40(FAILED 0, TIMEOUT 0, INVALID 1, BUDGET_EXCEEDED 0, 미실행 0) | 6(4~7) | 35771.5(18184~62036) | 25381(6031~84515) | 등급 C |

- 모든 사례를 보류했을 때의 점수: 16/40 = 40.0% (26.3%~55.4%)
- 미실행: checklist 0건, agent 0건, full 0건(분모 40에 실패로 포함)
- 인프라 실패 재실행 건수: checklist 0건, agent 1건, full 3건
- 보조 분석(사전 등록) checklist 대 agent: 둘 다 성공 38 / checklist만 성공 0 / agent만 성공 0 / 둘 다 실패 2, Newcombe 짝 차이 95% 구간(checklist − agent) -7.9pp~+7.9pp, McNemar 정확 검정 p 1.000
  - agent에서 좋아진 사례: 없음 / 나빠진 사례: 없음
- 보조 분석(사전 등록) checklist 대 full: 둘 다 성공 35 / checklist만 성공 3 / full만 성공 0 / 둘 다 실패 2, Newcombe 짝 차이 95% 구간(checklist − full) -1.6pp~+19.3pp, McNemar 정확 검정 p 0.250
  - full에서 좋아진 사례: 없음 / 나빠진 사례: 850423-XT-202406, 850433-XU-202407, 850440-XS-202405
- 보조 분석(사전 등록) agent 대 full: 둘 다 성공 35 / agent만 성공 3 / full만 성공 0 / 둘 다 실패 2, Newcombe 짝 차이 95% 구간(agent − full) -1.6pp~+19.3pp, McNemar 정확 검정 p 0.250
  - full에서 좋아진 사례: 없음 / 나빠진 사례: 850423-XT-202406, 850433-XU-202407, 850440-XS-202405
- 상태 변화(원초안 → Critic 뒤 → 검증 뒤): 집계하지 않음(trace 형식 미정, 단위 L1. F1 전 보완)

혼동행렬(행: 정답 사례 상태, 열: 최종 사례 상태와 실행 실패)

- checklist

| 정답 \ 최종 | MAINTAIN | MONITOR | HOLD | 실행 실패 |
|---|---|---|---|---|
| MAINTAIN | 17 | 0 | 0 | 0 |
| MONITOR | 0 | 7 | 0 | 0 |
| HOLD | 0 | 0 | 16 | 0 |

- agent

| 정답 \ 최종 | MAINTAIN | MONITOR | HOLD | 실행 실패 |
|---|---|---|---|---|
| MAINTAIN | 17 | 0 | 0 | 0 |
| MONITOR | 0 | 7 | 0 | 0 |
| HOLD | 0 | 0 | 16 | 0 |

- full

| 정답 \ 최종 | MAINTAIN | MONITOR | HOLD | 실행 실패 |
|---|---|---|---|---|
| MAINTAIN | 15 | 2 | 0 | 0 |
| MONITOR | 0 | 7 | 0 | 0 |
| HOLD | 0 | 0 | 15 | 1 |


- 덧붙이기 전·뒤 보고서 단위 오류율(덧붙인 주장을 뺀 주장 집합으로 산문 뒷받침을 다시 판정. 실패·무효·미실행은 그대로 오류. 결정 기록 20260925-1856): checklist 전 0/40 → 뒤 0/40, agent 전 2/40 → 뒤 0/40, full 전 2/40 → 뒤 1/40
- 덧붙인 주장 덕분에 뒷받침된 산문 표현 수: checklist 0, agent 2, full 1
- 장치 발동 수(실행 추적 집계): 코드가 덧붙인 주장(최종 보고서에 남은 것) checklist 합계 46(보고서당 0(0~5)), agent 합계 121(보고서당 3(0~8)), full 합계 141(보고서당 4(0~10)); review_status 집계로 바뀐 최종 보고서(어느 단계든) checklist 0(0), agent 0(0), full 0(0); 버린 초안 (나) 수정본 버림 / (가) 재조회 버림 checklist 0 / 0, agent 0 / 0, full 2 / 1; HOLD 합의로 뺀 도구 지적 checklist 0, agent 2, full 4

## 3. 개발 묶음 값 — 대표 숫자 아님 (등급 D)

- 해당 없음(이 채점 실행의 자료 묶음은 holdout40다)

## 4. 참고 지표

- 스킬 호출 성공률(NemoClaw 경로, 정확도 지표에는 영향을 주지 않는다): 5/7 — 시연 요청 7건 가운데 tradesentry 스킬 호출이 CLI 실행까지 이어진 5건(결정 기록 20260924-2315-user-decision-impl-plan-approval.md D5 규칙. 시연 2026-09-25(금)부터 26(토)까지. NemoClaw 래퍼의 replayInvalid 종료 코드 1은 실패로 세지 않음. 오케스트레이터 집계)
- 코드가 덧붙인 필수 근거 주장 수(2026-09-25(금) 18:09 사용자 결정, B2. 발동 신호 자기 계열 주장(2026-09-25(금) 22:22 사용자 결정 ②·⑦)과 자료 불일치 HOLD 초안의 중량 비중 0 주장(2026-09-26(토) 01:05 사용자 결정 ①·③)도 이 수에 든다. 최종 보고서에 남은 것, 완료 보고서당 중앙값(범위)): checklist 보고서당 0(0~5), 합계 46(필수 근거 45·자기 계열 0·중량 0 1), 완료 보고서 40건, agent 보고서당 3(0~8), 합계 121(필수 근거 118·자기 계열 1·중량 0 2), 완료 보고서 40건, full 보고서당 4(0~10), 합계 141(필수 근거 139·자기 계열 1·중량 0 1), 완료 보고서 39건
- 코드가 `review_status`를 집계 값으로 바꾼 보고서 수(2026-09-25(금) 22:22 사용자 결정 ①·⑦. 최종 보고서 기준, 괄호는 어느 단계든 바뀐 보고서 수): checklist 0(0), agent 0(0), full 0(0)
- 덧붙이기 전 기준의 보고서 단위 오류율(덧붙인 필수 근거 주장을 빼고 같은 채점 규칙으로 다시 계산. 2026-09-25(금) 18:56 사용자 결정. 괄호는 덧붙이기 뒤): checklist 0/40 = 0.0% (0.0%~8.8%) (뒤 0/40), agent 2/40 = 5.0% (1.4%~16.5%) (뒤 0/40), full 2/40 = 5.0% (1.4%~16.5%) (뒤 1/40)
- 덧붙인 필수 근거 주장 덕분에 뒷받침된 산문 표현 수(같은 결정, 모드별 합계): checklist 0, agent 2, full 1
- 버린 초안 수(조사 흐름 수정, B2): (나) 수정본 버림 checklist 0, agent 0, full 2; (가) 재조회 버림 checklist 0, agent 0, full 1
- HOLD 합의 신호에 내지 않은 도구 지적 수(2026-09-25(금) 22:22 사용자 결정 ③): checklist 0, agent 2, full 4
- 실행 추적 집계 범위: 사례 실행 폴더의 runlog_trace 파일(읽기만)에서 센다. 모드별 trace 있는 최종 실행 checklist 40/40건, agent 40/40건, full 40/40건. 없거나 읽을 수 없거나 모양이 다른 실행이 있는 모드는 여섯 값을 집계하지 않는다(사유: trace 없음·trace를 읽을 수 없음·trace 모양 다름)
- 한국어 품질(참고, 자동 검사): checklist 한글 비율 87.9%, 금지 표현 0건, 필수 항목 누락 40건; agent 한글 비율 91.0%, 금지 표현 0건, 필수 항목 누락 33건; full 한글 비율 91.2%, 금지 표현 0건, 필수 항목 누락 36건. 표본 점검: 금지 해제 조건 뒤 결과표(로드맵 R1)에 적음
- NAT 프로파일 요약(참고): 금지 해제 조건 뒤 결과표(로드맵 R1)에 적음

## 5. 재현 명령

- 채점 대상 실행: python -m tradesentry.evaluation.sealed_runner --dataset holdout40 --sandbox ts-official --snapshot holdout40 --policy policy_v1 --conditions-extra outputs/operator_conditions-f2-holdout40.json
- 정답 대조 채점: python -m eval.scorer --run outputs/sealed/sealed_evaluate-260926101039
- 스냅샷 검증: tradesentry snapshot-verify --snapshot holdout40
- 채점기 입력(보고서 원문) 위치: artifacts/eval/score-260926115824/{run_id}/(증거 복사 때 함께 복사. 봉인 묶음은 금지 해제 조건 뒤). 보고서 파일 바이트 sha256:
  - run_case-260926101039: 67990a0202d6eadec2ccc5f48dd48d8920a521006dff125f882d7583bc67f460
  - run_case-260926101040: 6c44b362e19806bd9dcf0adaf433ccc8a0b263fed185e5454ac1078249de281a
  - run_case-260926101147: 918b759f76e3770af830c1de8245acdc766adb398e02117f44a0ac6162b75ddb
  - run_case-260926101206: af231a04f49054973d87a62a0dac33129d962c6a43016d880a1ccb5d26ba88af
  - run_case-260926101207: 7be28c07bb0d36dbb8a3e8ca9cd851731f5001d82634f83f89c141ab876d6c1f
  - run_case-260926101247: 57ea18da5a304f041a5105dd1edbcf47ea591b9672063294bba4650d28e56d9e
  - run_case-260926101347: ffe64ab043672e4ac1928f53006e3e029dfd3137778e53f2dcc1b73fc11ca513
  - run_case-260926101447: 270e8081cc444270f315d146ff5db9c2463389d3985afb53657daf323a051f14
  - run_case-260926101547: da81b821b460b58de82dd6af24408879502aa590df119a949015f6906c89e6b6
  - run_case-260926101605: b74b8aa7e05389061d581d53e4866b765e687bbf6e6717493b59a10ef554a92c
  - run_case-260926101647: 26d71aa4637b8f1c936833312d59c825d557cc78b6a092c1adeea32878286657
  - run_case-260926101904: 37594cde6d34a4de860d850180e18b9797d0beb2d08ad38f0d215431d6cee560
  - run_case-260926101905: c9c87daffbca119f175e90c7ae6411902a27f7ae19ebcb3a08f9c1aa2128f8e8
  - run_case-260926101906: e29d72dda5353b6661067c41bc29a83f4af9d2dbaed69a85649598ce633aec50
  - run_case-260926102104: 678abf4b283a4a7e80d0892187b6f63487307492ef327793e30d2c38ece3587b
  - run_case-260926102204: f233c82762e17b42dab967b233f87afa858eff363880380c4bc50c0a1043f8cb
  - run_case-260926102222: 4faa542ae0ecbc297a0f0b18ff6c01a2fc995055c1ccbc53fdb8668fc1961e1c
  - run_case-260926102304: b7b6b3ee4a15ca8e2a5ee343f11389f173e6d24a4a90340b8ba2405801378728
  - run_case-260926102721: f3ff3292e9b734044000f1cf2635022bde838761a8742e049031c1982e7261f3
  - run_case-260926102821: f3ab9a077821db3d57b5854335a479ff545efc163c6e357ea7688aa20c66ebcf
  - run_case-260926102921: f5303d50c908e15f4d5515d10fec5a57ff329fe47f095e6509b10e6e965716cf
  - run_case-260926103043: d8a471bf5f4a16b929fa922e9c90dfb2b9468242b5182f8c725d78c3b60b8553
  - run_case-260926103044: 509dc3d1d2183eb77b9db98f6e41e42fcf1e3c3c3c90bc4d467bdf185b9153ca
  - run_case-260926103121: 0704105d1540c5178d3630762b8b8656868bdb56f580a842d8a5fa3aa833b763
  - run_case-260926103327: 45fa4517094ebacb935d0e9f56777e9c1da7d5cca4b3fe7e6bc6e356d56445aa
  - run_case-260926103527: 4fb7cb01e9b6b86ef767f435cb530ec94196a3d7e6e6b1ebada1ebcc2b12a0a3
  - run_case-260926103538: 3be9a6abc6be03fb44e3570010aa74f8623f260a17a8737afaee2aafc30ce7e9
  - run_case-260926103627: f122d7266c4acd8e3ff48cc8f0da9e03c619847bfd3b02e5e5dabbb78e947a58
  - run_case-260926103704: 7c1e89841eb8381a324bbfc4ba505a3b7922a61e6ca84fb84b625d44c8e2bacf
  - run_case-260926103727: f5dd8914930c31180b66ee38ff4436ad1a562dc60717fb07c89d78024003b7e1
  - run_case-260926103838: 67ce4da0be7de1be54223a1cff52cc5b6e4b60b931b18e087b496838fecd1b8b
  - run_case-260926103938: 4bdfc246a462ec96b96b17492c6c715db0df9ecf3774ddf32f676231634e5438
  - run_case-260926104007: 695066d64ad66c35571ff0067d9bb14fa912c728d6a10eda84ebc7af36779a9d
  - run_case-260926104008: a1f13fbe33529b6955dc4957f5fa93efe86b0e1dedad56fae61349f980e98405
  - run_case-260926104009: e414cb29788b01ec6a5e7432e3268109190492563c53e45116df0571952ac108
  - run_case-260926104042: 3cce97aede83184f574dab81b72945762419055e00148c0e9e5688a3f728f611
  - run_case-260926104142: 807fec42776600ad021b30e3ef1d72bac2afa59829982f130ba999b5e5f55a15
  - run_case-260926104242: 01c1a6efaa5f30fad0fc191ee2e4368273969b34470d1e60ef9ac25fa8128273
  - run_case-260926104253: a98e99dd88a63a32f17d390ba2402ebf8b112656ae422942ba6218d78f64f00d
  - run_case-260926104254: 769c292096f80012fa64d28284478d209f218b9d5ba6139a13b2404424b1dfa7
  - run_case-260926104342: 0bc2966a2e1af2f2b5bc0907cc6f2b0ffbc7145e80e068c26af774fa06c3dfaa
  - run_case-260926104442: ae6ae9089e9190cc2844dfe73bc5bef467b23f2399b0a650c51b88dcdce1de89
  - run_case-260926104456: 51e915914837af08d7025908b72df4b9b9260fc33667cf00d2fc0f2cdb96f446
  - run_case-260926104542: ab974b70a4947457f8e4cd73858e4a272e7f20a0579e2b7611b93d9d70e18c1d
  - run_case-260926104547: 7077e8bd816d3267db82aa5b948df5abcde83b5f7deb6c9cfac37c880c0eeca6
  - run_case-260926104548: 9f95b213a33806be7705fcc5dbdcf152e3d4c2ba086198720b80f8bf9f4bd567
  - run_case-260926104642: c177ea783fcf3220a552e94c73306457c9f2e52422d8b9f2ecb6aa1a4d74dcca
  - run_case-260926104654: b83cbe1e8561926d285e1043d16191a464787eef3580c675ff2f4ef662b0966d
  - run_case-260926104742: 3e18fa40f6c317c8cf3209348b63a5b9c42824760cd9c7dfd1361924b93476c8
  - run_case-260926104842: 6fe33326c3c9acb9331686c9ff63c8996892021e5498da898d6252043bfc0530
  - run_case-260926104901: 75c2ea7e794fd794e6be40a292ab165941b9004aa9be3f71eaaaf3752d20fb0c
  - run_case-260926104945: 2eb51b66a7ce8f72cc95a9d48ff79e75df1202e4895fa2bd79c2839c1ac6b42a
  - run_case-260926105045: cc8b47ade51001dd2ab306026d9a1fa33f5bdcb2d669598f499867e2d28b235f
  - run_case-260926105211: da3ea3c735009275e0f800e97bedb9c0bda7749355b3b3a5818b41abffe65496
  - run_case-260926105212: a3e572ab0240f003c62a07093c71ee9f7dbb745f178f328bb18ebf4d77e82ec8
  - run_case-260926105213: ba9e93be7913cca1122b0486c3d69ce8b82723825685ef35b58b1b0be55bb614
  - run_case-260926105313: 1c3b16722d2a76f18e0ac0440c99253901c825aa7708fb48fc7672becae1ba63
  - run_case-260926105323: 05a4dd37db5afb152218b7f28ff4a63019fe73b0db8512188bfedfd8946448f1
  - run_case-260926105413: 8540939b9eb88735e2b8e7d66978428d008e5dd6daa68764cbbf8a3e7c3097fd
  - run_case-260926105538: 4859c15de4ee8efdc59f2626e3516afe00abbab1647bc8c8f5241ca33c5b8e2a
  - run_case-260926105539: 454a9f332a1e94f1fa736b4df33232cc01fbb52801a102b307df4b4866cb3316
  - run_case-260926105540: 99b71dc790f0ff092156d53a22065348fed333e659a8e75f615ea11d69ceeae3
  - run_case-260926105640: 79d50047edef59b899be806ee6e769c22a6f47455265ea129d193cd2507a8b39
  - run_case-260926105740: 8cf82ed74eb0c60001c93dab1418e571eed1f45d8dc74db7236840e3a9de63ed
  - run_case-260926105813: bc122e778efe65a0dbc850bf4d3dc7cc750b9f4dc00eaf872b1bda00f222d0ab
  - run_case-260926105814: 9980b84bfe94a74d462b1731ae0eec74e598a7ef1fc7792ce34370af42465258
  - run_case-260926105840: 9b399a14e432f9edfc14e178cf3f73c2eff65de2453797600e093898a7bb0de4
  - run_case-260926105940: bc76961a848e11d7b8f35efa46da1376d7eceee536532dc6d50cbd0851043ec6
  - run_case-260926110040: c123832e4322fa7c1e21ba77cf18f920907233893b976d3aa57ea64d29671c86
  - run_case-260926110140: 62849162b7a26ec8feb3f3f7d616c56079f84aa53e5f7a806fb3e170951424c9
  - run_case-260926110240: 75be6f6b9b54a599ecaf9047d975f6f6625b20f0a81ba587ea135f679e1cb3ac
  - run_case-260926110340: 622d8f0cd6df1c7eadf7941bb28e50653262182bdf2d8369f427d4dbd1adc1f5
  - run_case-260926110440: 1d9b58c52f1275d123cff61e5b21e68fb825a9738d02c7914bc79ff3a54e1dd5
  - run_case-260926110451: ae43a4351d29e2b61667f7f46fd1a191085e59a08eea84f519d2958d9934ec68
  - run_case-260926110452: 0bcdca1ce9240bd9c6688c11d281aa689025ad624878b2617573390e288c502f
  - run_case-260926110540: fb581df4c3b26b3eeea1550ed9b7ce820b6078b8c2437d3e5e328f95ef177a22
  - run_case-260926110640: ff9e94a10c18e4abf31dd2dcd5b0a2da46dab42852feac2b538e8846aba8fcc4
  - run_case-260926110658: e60f42eba16b66c8d1a1080850f49381d5a7b087793aea9b83a07c494f824197
  - run_case-260926110659: f31160331a3b68e951968ae47517dd1e78e81ed73d62adf3a7edd3ef4e991816
  - run_case-260926110700: b94b917987925266f966e13f43a68ffabee067d3e270af5fa55b72a472351b12
  - run_case-260926110740: 69bfcb53fda79a66dd6bd2286dcaa73b97603c0765e17ab536783ee1b0013489
  - run_case-260926110840: 70838bf80a14c2512dc3eba01bf1ce4b499b1d9f1d15d3384bdd71b3f54dcff6
  - run_case-260926110940: 2641594d57ac5cfdbe641b53262d147c8a3f8d6574da1a7283a83d53e2d06542
  - run_case-260926111054: 87ff0b83d47071c74111e19ba8ac9970204dd16d2eef3f318179699991701290
  - run_case-260926111439: 4c18446f623eaafe1817bbe6b8101e4fd29261ca439733b61ba4a9cbb9bb7b15
  - run_case-260926111503: 03ddadd790d9564c61aac43e07941016f31dded972c3b54d3c5b922822b0796e
  - run_case-260926111504: bc60207c5ee063768b3eb938e6e75582da3a4842f83d9fd21d24f9d74924ec2b
  - run_case-260926111539: 7ef0f08ecf53c91025137b93c2b2bfaa7740f4c2bc8c64c453c401f0c4e6e001
  - run_case-260926111639: 82a75aeb85a73f8a67a6721762d5664af4c81bd79aaf7f0aac3623c6a61069bc
  - run_case-260926111739: a7c69c09b7656cc3616f2b5cb32816587d76bd53e4169c002dd28b88697337b6
  - run_case-260926111839: a6e2cba1680540a79a5b6ba8992f985b6d0b35d388695ef4747ad058530bbcdb
  - run_case-260926111939: 3a6cd7a0fe565c6b7c3c671fe0b580ca6d70d83a56bddf619dd8f37a5c58c87b
  - run_case-260926112039: 3b722b36e1995de1ba2f4f4b31359be63a6021c1f7ed6b01755070881c37699b
  - run_case-260926112124: 468082e06eac74163af620d7732ef786b65bc9485f6f0b7e6e0d60c77f399bce
  - run_case-260926112139: 2b4b6036c05b9e83cedd3afa27f5b79743a8b7e10205e584be7d155274599484
  - run_case-260926112147: d456b846015c6f7b02a77c13d613037e807b824e7527c3e4c181fe025d76d2e5
  - run_case-260926112239: b41187f28d7fc4265a11ba6be4c5c06f35e4c1274b5cf731f4362eb0a9d8895c
  - run_case-260926112339: d1f8293b68f5b0b4dd2e2a4a8a94f5a24b0c3159419e401c832325abb7e6a988
  - run_case-260926112439: 1f165f778228eebaf9cc17e8c96cba620f04579c81ea6e3b7ca48abbe3916331
  - run_case-260926112539: 24732f48dea12df5e7f6e40d956229ebf44b24a600893be126908de181bfcaf9
  - run_case-260926112639: 663691c1333165f0ec920f98b159d61e94840ee4dc2fb7e0ae3817c921a3d365
  - run_case-260926112739: 337f381f96a729a5d9ffd10bf559206c1f5ecf35cb1faf2f8f89ae2a9562157d
  - run_case-260926112839: e4838a8e4b64f5028ab72f3f53995861754653150d12c00f7e27da743a5eaa0f
  - run_case-260926112939: abf8e10ff9b4b929747d0823118f22fcccdfc7a0f319a563a22ca671b5f08b33
  - run_case-260926113054: 0b0c16ea61b6a22b1d4c44977fa4c4b58c9c8cb2ed95be8b19764853f3820db0
  - run_case-260926113154: 5221c25b43e6523efd498066f962452121974eee99dd204ea860c86712da39ba
  - run_case-260926113214: 5625ca8ad830f9ead0e1b1af9fe530de5a9e8f5012f4520e5ed1ef18bd5720bf
  - run_case-260926113254: b2e371607ec84729307b71b5da51317ca8fb449158b929834bb81e0a7e65c763
  - run_case-260926113354: e7d957218a0335e0749b3730df54b492be17e02edb2a0a046940ea14852574af
  - run_case-260926113454: 999f6b3746d73f1f9afef488dac777cbd091cdac6bc5b3ee73f2fc5313a575e4
  - run_case-260926113554: a685f870ece14d8ef43643f44f112a1948a92bbdad27e9c40375f3d10fe57d6d
  - run_case-260926113654: b42a91caac3770651e839588d2dbb937c5a538f64968a2e1522636ff0a3348c4
  - run_case-260926113754: 7e01f68355fc9fd95550b461ec20093e25543ba352a9941fe36187be1ecb0fff
  - run_case-260926113854: 0fee5d32c144e86d180c2c4cd027bc093d4b71d49efb34fca9cc0960bec0c558
  - run_case-260926113954: 62b74932e3864036baae195a0dc71f6b3704e1ff3c58f1f9298199f35716abda
  - run_case-260926114054: 2a44f1b0ddde3991e73596c6fe9404c770e70e38d8451c3f649d5148d8eda845
  - run_case-260926114154: 9f4f07264755fc4cdd06768bd27c5084f798ba8cef408a430753225a84e14297
  - run_case-260926114254: 1de49c463ab9a121ad2c2275c0bdaa621589817d77581ce201c53d7ab96cf4be
  - run_case-260926114354: 83a4d18104ffdde4054ca40f4d0384d3a268ac3eb97a8ede14f796e558b31160

## 6. 한계

- 봉인의 한계(룰북 B6): 봉인 폴더 위치는 비밀이 아니고, 같은 OS 사용자로 도는 에이전트의 열람을 기술적으로 막지 못하며, 해시는 변조를 드러낼 뿐 열람을 막지 않는다
- 산문 패턴의 한계(룰북 B3-2): 문장 단위로 주어를 맞추지 않아 우연히 맞는 표현을 놓치고, 배수 표현은 r_U claim만 뒷받침한다
- 표본 크기와 신뢰구간 폭: 사례 40건. 한 시계열에서 여러 경보가 뽑히면 독립 가정이 약해진다
- 숫자·증감이 없는 극값·순위 표현은 채점하지 않으므로 틀려도 잡히지 않는다
- 채점기 입력(보고서 원문)은 증거 복사 전까지 outputs/에만 있어 저장소만으로 재채점할 수 없다
- 승격 규칙(CONFIRMED_NO_TRADE)은 policy_v1 승인 전이라 채점기가 따로 적용하지 않고 스냅샷 표시를 썼다(F1 전 보완)
