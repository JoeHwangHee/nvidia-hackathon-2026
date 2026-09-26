# 평가 결과 요약 — sealed_evaluate-260926114518

채점기(eval/scorer)가 쓴 요약이다. 에이전트는 이 파일을 고쳐 쓰지 않는다(자료 계약 §10.3 N8). 등급 표기는 룰북 A5·B7을 따른다.

## 0. 실행 조건

- 룰북: RB-1, 동결 커밋 c557540f743ffc77a996a2a227d68d0bbfa0f08e, 동결 뒤 변경 동결 대상은 없음 — 실행 시작 시각에 git diff c557540f743ffc77a996a2a227d68d0bbfa0f08e HEAD -- docs/eval/RULEBOOK.md eval/scorer/ configs/policy_v1.json src/tradesentry/validator 0줄, 자료 계약 §11 동일. 동결 대상 밖 변경: run-case --sealed(code_version d35fe756a3065fbdbcc60110a91e8f912a5ffc74), 자료 계약 §10 CLI 행·경로 행. 채점 직전에 다시 확인한다
- snapshot_id kcs_202201_202412_v2, 스냅샷 정규화 해시(normalized_sha256) 미기재(실행 조건 입력 파일에 없음), 대조 미기재(실행 조건 입력 파일에 없음)
- policy_version policy_v1, grouping_version g0(사유: g0 대체 선언(2026-09-26(토) 08:10 사용자 결정, 결정 기록 20260926-0810-user-decision-rb1-g0-substitute-and-prose-ex2.md). real_dev와 같은 g0 고정 목록(대상국을 뺀 15개국 가운데 2023년 연간 수입금액 상위 5개국))
- code_version d35fe756a3065fbdbcc60110a91e8f912a5ffc74, 채점기 커밋 074a080, 산문 패턴 목록 커밋 074a080(채점기가 계산한 패턴 목록 지문 sha256 ce8f62765b3607127c24ed053b0e141bc47166275df58eacd7e191d6616eaec4)
- 실행 기간(KST) 2026-09-26T11:45:18+09:00 ~ 2026-09-26T13:51:27+09:00, 동시성 1, 순서 seed rb1-order-v1
- 한도(룰북 B2와 대조한 실행 설정): 도구 호출 시도 8, 재조사 1, 모델 요청 10, 사례당 wall time 300초, 누적 토큰 128000
- 샌드박스 이름 ts-official, 커밋한 라이브 정책 조회 본문(정책 YAML) sha256 8aae74173df4e799315c25023292e3be64bbe308f19d3bfe8871408502d7ecf9, 대조한 시험표 실행 폴더 이름 openshell_violation_tests-260926100925, `configs/openshell/policy.yaml` sha256 dc2e8c3a7707e78cf86c1536ed5535fcf99e592376a2009d190d5564e87785a8
- 봉인 해시 재대조 일치
- 봉인 묶음의 출처 점검(평가 스킬 ② 사전 점검 단계 4의 8번) ① 해시 목록 등록 커밋 dc9e76b(#79, 2026-09-26(토) 07:26)는 policy_v1 사용자 승인 기록(2026-09-25(금) 08:46)보다 뒤이고 동결 커밋 c557540의 조상이다. 등록 커밋→동결 커밋 사이 configs/policy_v1.json과 탐지 단위(unit_value·share·rounding·trigger·case_build·query·policy_load, CLI args.py) 변경 0줄. src/tradesentry/cli/dispatch.py 386줄 변경은 #87 평가 배선 분리이며 탐지 함수 _detect·build_case_list·detect_dataset_cases·detect_series의 AST 지문은 두 커밋에서 같다. 동결 커밋→code_version d35fe756a3065fbdbcc60110a91e8f912a5ffc74 사이의 dispatch.py 변경은 run-case의 --sealed 경로 추가(자료 묶음 표·real_sealed 계열 허용)이며 탐지 함수는 바꾸지 않았다. ② real_sealed 분할 기록(결정 기록 20260924-2340, 커밋 #21 2026-09-25(금) 00:20)은 policy_v1 수치 제안과 승인(2026-09-25(금) 08:46)보다 앞선다. ③ 표본 추출 seed 파일 sha256(5732e950…)이 결정 기록 20260924-2340과 해시 목록 real_sealed 항목에 같이 있다. 한계: 등록 뒤 정책·탐지 코드가 바뀌지 않았다는 것까지만 보인다(병렬 개발 규칙 §6.6·§6.7)
- 채점 전 확인(평가 스킬 ②): 1 예정 실행의 최종 상태 확정 참: 예정 실행 80건 가운데 줄 없는 조합 0건, 인프라 실패 재실행(룰북 B5) 대상 10건·재실행 10건(채점기 계산: 미실행 0건), 2 버전 키 일치 미기재(실행 조건 입력 파일에 없음), 5 모드별 사례 집합 일치 미기재(실행 조건 입력 파일에 없음)(채점기 계산: 참), 순서 seed·동시성 적용 참: 순서 seed rb1-order-v1, 동시성 1, 속도 조절(모델 실행 사이 최소 60초, 분당 토큰 50000, HTTP 429 뒤 120초), 쉰 시간 합 3588초, 429 뒤 더 쉰 횟수 11, 동시성을 올렸다면 근거 결정 기록 동시성 1(룰북 B5 그대로. 올리지 않음)
- 사전 점검 결과 평가 스킬 ② 사전 점검: 단계 3-3 채점기 자체 시험 203건 종료 0(2026-09-26(토) 08:32), 단계 4-3 스냅샷 kcs_202201_202412_v2 검증 ok(normalized_sha256 31928884d4ce8d47358b10d09035309af664d8951eaacdd2a7230c6fb900a205, snapshot_verify-260926083238), 단계 4-5 봉인 해시 목록 전체 대조 202/202(반입 도구 08:1x·08:3x). 단계 4-1·4-2·4-4·4-6·4-8은 동결 커밋 뒤 채움: 4-1 룰북 동결 커밋 c557540f743ffc77a996a2a227d68d0bbfa0f08e(PR #88 squash 2026-09-26(토) 09:20, 사용자 동결 확인 08:53) 뒤 docs/eval/RULEBOOK.md·eval/scorer/·configs/policy_v1.json·src/tradesentry/validator diff 0줄, 자료 계약 §11 자릿수 표 동일(실행 시작 시각 기준). 이 실행의 code_version은 d35fe756a3065fbdbcc60110a91e8f912a5ffc74 — 동결 뒤 run-case에 봉인 실행 경로 --sealed를 더한 수정 커밋(사용자 승인 2026-09-26(토) 09:55, 결정 기록 20260926-0945·20260926-0955). 첫 시작 outputs/sealed/sealed_evaluate-260926092509는 그 결함으로 무효(모델 호출 0, 봉인 내용 산출 0). 4-2 configs/policy_v1.json sha256 0804508a18ca8c848b41f3a90b8cc6f362e986becd76b607380f4786ee73a981 = 동결 커밋의 값(승인 기록 20260925-0846). 4-4 g0 대체 선언 결정 기록 20260926-0810 있음, 실행기 grouping_version g0. 4-6 holdout40_check 종료 코드 0(2026-09-26(토) 08:48, 건수만). 4-7 이 묶음의 유효한 공식 실행·채점 기록 없음(무효 첫 시작만, 채점 안 함). 4-8 아래 출처 점검. 4-9 E2 실행기(#87)와 부록 40 사용자 확인(08:53). 공식 채점 단계 4: 전용 샌드박스 ts-official(수정 커밋 d35fe756a3065fbdbcc60110a91e8f912a5ffc74 이미지, image manifest 359742d70383d0ca99758d985e40f45d150744fd217f216524fb647559c59d15) 공식 위반 시험 openshell_violation_tests-260926100925 모두 일치·불일치 0
- 계약 버전 schema_version 2, 자료 묶음 real_sealed, 평가 묶음 실행 sealed_evaluate-260926114518, 채점 실행 score-260926135136
- 채점기가 읽은 스냅샷 파일 data/snapshots/kcs_202201_202412_v2/snapshot_build.sqlite, 바이트 sha256 3a29db9227cc017771daf917ee5de907c7f46d6f41dc122782329d84faf12d7d
- 계획: 사례 40건 × 모드 freeform, full = 예정 실행 80건, 결과 줄 90줄
- 채점 대상 run_id 목록: run_case-260926114518, run_case-260926114618, run_case-260926114921, run_case-260926115021, run_case-260926115155, run_case-260926115308, run_case-260926115559, run_case-260926115659, run_case-260926115759, run_case-260926120138, run_case-260926120238, run_case-260926120412, run_case-260926120512, run_case-260926120612, run_case-260926120906, run_case-260926121041, run_case-260926121153, run_case-260926121344, run_case-260926121648, run_case-260926121748, run_case-260926121910, run_case-260926122010, run_case-260926122110, run_case-260926122224, run_case-260926122324, run_case-260926122424, run_case-260926122524, run_case-260926122643, run_case-260926122814, run_case-260926122921, run_case-260926123205, run_case-260926123305, run_case-260926123405, run_case-260926123727, run_case-260926123827, run_case-260926124210, run_case-260926124310, run_case-260926124410, run_case-260926124511, run_case-260926124611, run_case-260926124725, run_case-260926124919, run_case-260926125045, run_case-260926125145, run_case-260926125245, run_case-260926125346, run_case-260926125525, run_case-260926125625, run_case-260926125735, run_case-260926125918, run_case-260926130057, run_case-260926130214, run_case-260926130404, run_case-260926130504, run_case-260926130604, run_case-260926130708, run_case-260926130815, run_case-260926131051, run_case-260926131151, run_case-260926131251, run_case-260926131351, run_case-260926131451, run_case-260926131551, run_case-260926131716, run_case-260926131847, run_case-260926131947, run_case-260926132307, run_case-260926132410, run_case-260926132510, run_case-260926132646, run_case-260926132823, run_case-260926132923, run_case-260926133023, run_case-260926133134, run_case-260926133234, run_case-260926133408, run_case-260926133546, run_case-260926133656, run_case-260926133756, run_case-260926133856, run_case-260926134005, run_case-260926134106, run_case-260926134206, run_case-260926134306, run_case-260926134407, run_case-260926134507, run_case-260926134607, run_case-260926134843, run_case-260926134943, run_case-260926135049
- 상태 변화 집계(모델 원초안 → Critic 뒤 → 검증 뒤): 집계하지 않음(trace 형식 미정, 단위 L1. F1 전 보완)

## 1. 대표 지표 — 실자료 사실 주장 오류율 (real_sealed)

- A등급 주장 조건(B3-3): 미충족(조건 3)
- 사례 40건, 서로 다른 시계열 27개. 한 시계열에서 경보가 여러 건 뽑히면 Wilson 구간의 독립 가정이 약해진다

| 모드 | 예정 실행 | COMPLETED | 실행 실패(상태별) | 보고서 단위 오류율(Wilson 95%) | 주장 단위 오류율(참고) | 보고서당 claim 수(평균/중앙값/최대) | 보고서당 UNBACKED_PROSE(평균/중앙값/최대) | UNBACKED_PROSE 필드별(narrative / hypotheses / claims[].text) | 민감도: hypotheses를 뺀 보고서 단위 오류율 | 등급 |
|---|---|---|---|---|---|---|---|---|---|---|
| freeform | 40 | 36 | FAILED 2, TIMEOUT 0, INVALID 2, BUDGET_EXCEEDED 0, 미실행 0 | 11/40 = 27.5% (16.1%~42.8%) | 10/215 = 4.7% | 6.0/5/13 | 0/0/0 | 0 / 0 / 0 | 11/40 = 27.5% (16.1%~42.8%) | A등급 주장 보류(참고치) |
| full | 40 | 40 | FAILED 0, TIMEOUT 0, INVALID 0, BUDGET_EXCEEDED 0, 미실행 0 | 0/40 = 0.0% (0.0%~8.8%) | 0/264 = 0.0% | 6.6/5/27 | 0/0/0 | 0 / 0 / 0 | 0/40 = 0.0% (0.0%~8.8%) | A등급 주장 보류(참고치) |

| 모드 | 자릿수만 다른 WRONG_VALUE(민감도) | 발동 신호별 주장 요건 미충족으로 생긴 INVALID | 인프라 실패 재실행(건수 / 재실행 전 기록으로 계산한 보고서 단위 오류율) |
|---|---|---|---|
| freeform | 0 | 집계하지 않음(원인 분류 코드 미정, 단위 L3) | 6 / 14/40 = 35.0% (22.1%~50.5%) |
| full | 0 | 집계하지 않음(원인 분류 코드 미정, 단위 L3) | 4 / 4/40 = 10.0% (4.0%~23.1%) |

- 차이 판정(1차, B4 비겹침 규칙): 구간이 겹치지 않아 full의 보고서 단위 오류율이 "낮다"
- 보조 분석(사전 등록): 짝 비교 둘 다 오류 0 / freeform만 오류 11 / full만 오류 0 / 둘 다 무오류 29, Newcombe 짝 차이 95% 구간(freeform − full) +13.1pp~+42.8pp, McNemar 정확 검정 p 0.001
- 결과 집합 분포(source=claim): freeform CORRECT 205, WRONG_VALUE 7, WRONG_DIRECTION 0, WRONG_UNIT 0, WRONG_REFERENT 3, UNSUPPORTED 0; full CORRECT 264, WRONG_VALUE 0, WRONG_DIRECTION 0, WRONG_UNIT 0, WRONG_REFERENT 0, UNSUPPORTED 0
- 결과 집합 분포(source=prose): freeform CORRECT 167, UNBACKED_PROSE 0; full CORRECT 271, UNBACKED_PROSE 0
- 극값·순위 표현 건수(참고, 채점 제외): freeform 0 / full 0
- 범위 밖: 숫자·증감이 없는 정성 서술과 극값·순위 말의 의미 정확성

- 덧붙이기 전·뒤 보고서 단위 오류율(덧붙인 주장을 뺀 주장 집합으로 산문 뒷받침을 다시 판정. 실패·무효·미실행은 그대로 오류. 결정 기록 20260925-1856): freeform 전 13/40 → 뒤 11/40, full 전 1/40 → 뒤 0/40
- 덧붙인 주장 덕분에 뒷받침된 산문 표현 수: freeform 3, full 2
- 장치 발동 수(실행 추적 집계): 코드가 덧붙인 주장(최종 보고서에 남은 것) freeform 합계 126(보고서당 3(0~8)), full 합계 118(보고서당 3(0~7)); review_status 집계로 바뀐 최종 보고서(어느 단계든) freeform 1(2), full 0(1); 버린 초안 (나) 수정본 버림 / (가) 재조회 버림 freeform 0 / 1, full 3 / 1; HOLD 합의로 뺀 도구 지적 freeform 5, full 5

## 2. 보조 지표 — holdout40 (등급 C)

- 해당 없음(이 채점 실행의 자료 묶음은 real_sealed다)

## 3. 개발 묶음 값 — 대표 숫자 아님 (등급 D)

- 해당 없음(이 채점 실행의 자료 묶음은 real_sealed다)

## 4. 참고 지표

- 스킬 호출 성공률(NemoClaw 경로, 정확도 지표에는 영향을 주지 않는다): 5/7 — 시연 요청 7건 가운데 tradesentry 스킬 호출이 CLI 실행까지 이어진 5건(결정 기록 20260924-2315-user-decision-impl-plan-approval.md D5 규칙. 시연 2026-09-25(금)부터 26(토)까지. NemoClaw 래퍼의 replayInvalid 종료 코드 1은 실패로 세지 않음. 오케스트레이터 집계)
- 코드가 덧붙인 필수 근거 주장 수(2026-09-25(금) 18:09 사용자 결정, B2. 발동 신호 자기 계열 주장(2026-09-25(금) 22:22 사용자 결정 ②·⑦)과 자료 불일치 HOLD 초안의 중량 비중 0 주장(2026-09-26(토) 01:05 사용자 결정 ①·③)도 이 수에 든다. 최종 보고서에 남은 것, 완료 보고서당 중앙값(범위)): freeform 보고서당 3(0~8), 합계 126(필수 근거 109·자기 계열 0·중량 0 17), 완료 보고서 36건, full 보고서당 3(0~7), 합계 118(필수 근거 98·자기 계열 0·중량 0 20), 완료 보고서 40건
- 코드가 `review_status`를 집계 값으로 바꾼 보고서 수(2026-09-25(금) 22:22 사용자 결정 ①·⑦. 최종 보고서 기준, 괄호는 어느 단계든 바뀐 보고서 수): freeform 1(2), full 0(1)
- 덧붙이기 전 기준의 보고서 단위 오류율(덧붙인 필수 근거 주장을 빼고 같은 채점 규칙으로 다시 계산. 2026-09-25(금) 18:56 사용자 결정. 괄호는 덧붙이기 뒤): freeform 13/40 = 32.5% (20.1%~48.0%) (뒤 11/40), full 1/40 = 2.5% (0.4%~12.9%) (뒤 0/40)
- 덧붙인 필수 근거 주장 덕분에 뒷받침된 산문 표현 수(같은 결정, 모드별 합계): freeform 3, full 2
- 버린 초안 수(조사 흐름 수정, B2): (나) 수정본 버림 freeform 0, full 3; (가) 재조회 버림 freeform 1, full 1
- HOLD 합의 신호에 내지 않은 도구 지적 수(2026-09-25(금) 22:22 사용자 결정 ③): freeform 5, full 5
- 실행 추적 집계 범위: 사례 실행 폴더의 runlog_trace 파일(읽기만)에서 센다. 모드별 trace 있는 최종 실행 freeform 40/40건, full 40/40건. 없거나 읽을 수 없거나 모양이 다른 실행이 있는 모드는 여섯 값을 집계하지 않는다(사유: trace 없음·trace를 읽을 수 없음·trace 모양 다름)
- 한국어 품질(참고, 자동 검사): freeform 한글 비율 86.7%, 금지 표현 0건, 필수 항목 누락 30건; full 한글 비율 90.3%, 금지 표현 0건, 필수 항목 누락 38건. 표본 점검: 금지 해제 조건 뒤 결과표(로드맵 R1)에 적음
- NAT 프로파일 요약(참고): 금지 해제 조건 뒤 결과표(로드맵 R1)에 적음

## 5. 재현 명령

- 채점 대상 실행: python -m tradesentry.evaluation.sealed_runner --dataset real_sealed --sandbox ts-official --snapshot kcs_202201_202412_v2 --policy policy_v1 --conditions-extra outputs/operator_conditions-f2-real_sealed.json
- 정답 대조 채점: python -m eval.scorer --run outputs/sealed/sealed_evaluate-260926114518
- 스냅샷 검증: tradesentry snapshot-verify --snapshot kcs_202201_202412_v2
- 채점기 입력(보고서 원문) 위치: artifacts/eval/score-260926135136/{run_id}/(증거 복사 때 함께 복사. 봉인 묶음은 금지 해제 조건 뒤). 보고서 파일 바이트 sha256:
  - run_case-260926114518: 3ed70f4a920be91c907442fcb72cec808db0ca32474922ca3607cebaf9fe22c4
  - run_case-260926114921: 239b26d781ed58dde6df197ca0d16d9c5e9356a76bbd1d9658eb6d7a96aa6eb0
  - run_case-260926115021: 4333d85bd27c2555a5657f20b4495bdffcba0f7f3cc3c43b42f3c87fd205fb83
  - run_case-260926115155: 8d99d042c4f5fa553a79e6e3808a1fe43d73f2749d59667c9ee800ccb6f92f16
  - run_case-260926115559: b94dc45ad0ecd5de35f2bbc9333b2d2df927e2aa5b304de476c4660757a0416f
  - run_case-260926115659: 80e0f0d3c9abcb2155be0668fc24158a85839c11e24fdf6093d69d96f1376ce8
  - run_case-260926120138: cff2390ede8b283d6b85e1ab550c1fa54622a3f3a486d1e1cfe691177f28475d
  - run_case-260926120238: ce47b4f8ca6f35b744ca2ca3edbbae50f37ea97c7844f3dd12d1a13818f48109
  - run_case-260926120412: 7dde6fb4a61d3fd7e7884f89d035269756d1a2f1176ccd2d62de7912e274e3b0
  - run_case-260926120512: 01ec4a7ccbac565f6296a564c65021e751ff4e2de9de08666c12fcd181a5226c
  - run_case-260926120906: 420bf8d5b3d72b0d14a082d182098b907dd0f979497c48b6d9ffb66e60cb25db
  - run_case-260926121041: 097f5ca1394f6982d12338854331b0dccc3f5b219bd113d9646ab8c77fdf4127
  - run_case-260926121153: 866876a975560171230df367b10306f668352e8d2037df6d99e25bd64d8e7733
  - run_case-260926121648: 151a4685528ef500728379e6e0ebce2ddbe53ec7f01b279f651e4665037ac67f
  - run_case-260926121748: de6524584161bea69ec18821a7321cc11ecec098d7a626b82899216da75301e8
  - run_case-260926121910: 2233c858d386e03a28334569358967b9aa394f64275deca1604a5fed1bf27924
  - run_case-260926122010: d71098da5dcf8054e59b8042c86141667482fb8685376746455f78bd0bebef8c
  - run_case-260926122110: 6442c0a873dee677df569e0bfd5bd46ba3a40cf596499847ac9bf4e5882dc393
  - run_case-260926122224: 24b62358fba8307df9c22363edf52babae0083366cb185f3e6adc97ec5635fda
  - run_case-260926122324: 9f8d6c268a4c17ae3212df810c1da16d7969a3e960903113a53de28f40b4fbba
  - run_case-260926122424: aa89c24bba87633c17397e341bd1c1a0f3c68a55ba4224b7c253540f47a324a7
  - run_case-260926122524: c3d1c8d5ae7e168a5ca66fd32f30501befac2402b978cdde5e884514f06086bd
  - run_case-260926122643: 1a6ed86519168d6c695cb4814c9699d9bc31cb4055dd77e3f7c6c6922e5761a3
  - run_case-260926122814: 11f1ea054425bcb5b21e9b829fed7141c3b04a0a2345b98f7364d4e13bd5e835
  - run_case-260926123205: d193ef834acd800a19f493da113390fe47641c6c82c0914a81f5b3588183c319
  - run_case-260926123305: 97483068c4a6e4d9d39878eb5e0eb63d750694846bc0a3313871f641b92dfcc8
  - run_case-260926123727: 125d6e475ebfc418432e84da1b9b2e91665ce32ace856c8c1b0435f8b014c00e
  - run_case-260926124210: 15597476d9a1720ee800d4bbe7e7635e42ac7f89542a21601dde3aacd696fba0
  - run_case-260926124310: ebf0b3b9bf4794cb47b48366e2362b4b4cb59f48a410081e37eec92117f98fe6
  - run_case-260926124410: 6e8f33b0369c14a8a2b137c233dcb91117e7be98525e7be88264909adfbdb2e2
  - run_case-260926124511: 71507ec093ecd7e733964028638eafb3656b0fd621f869d10207163afe35d48c
  - run_case-260926124611: 7d83ad6ceb4e2331ecb091fe0f782a58da0b18f060cf7e7aeef75c5ff92fc7ac
  - run_case-260926124725: c3ee776eb17ca231522cfac243bbb08625b0817bd15a0d4e151d84c08a26004a
  - run_case-260926124919: 23275cab9d048390702f54636bac00bf33dfa5c4ebc0b37cd33dcb96fe7fc278
  - run_case-260926125045: bd12e05f646a63ad0a148759857aef28be4929792fa60fe89a1b32dfdef05390
  - run_case-260926125145: 82bf8c105b64d77abe0fa1a5c186dd65fa5c29db3b498fb2cc41ebcf8ceffbfe
  - run_case-260926125245: c1d7a96a7039b019be1da1fab0b12de17193460f42aa6afd67312dfbeb0d361c
  - run_case-260926125346: 0570639555436f17717aa2de6461c57b5946de3fd640e33ee03a89dedee325ad
  - run_case-260926125625: fe525f807fc2837927f7f56f03766b326830a657a4369d11b0fdae4ae889af06
  - run_case-260926125735: f2391df15becce5745a40d4856b12b4f7f2c1568ee90cc69d6d7bb06ce6d0bf9
  - run_case-260926125918: e793192b3ab2a5b108d80d2b8ca304645cbdf2ea0fa6c853cfe4c1835ee8cce7
  - run_case-260926130057: 52c43c4d0ce4a32b3846d4acd96193554fbb66594bd7668f8519f7c3fd0e313e
  - run_case-260926130214: b874e4ada4a1b7b0ac0ce165566fa1222201ea5bd581094ec331a6206dd2f7e3
  - run_case-260926130404: 7f62ad03d3341ff4ae1ee27eeee81ae13558bf7a72ffebd01d9e8c7adc61b68a
  - run_case-260926130504: 58a7c23fd38bd290fd81760274abc179b8aebce7540814c0fb0ea572130e8b71
  - run_case-260926130604: 2fee642163415258c284efd0b859318919a3e75d69d8b073c55a30ea53bbdcb0
  - run_case-260926130708: d9b302b0c707e4a8dfa7cd9bc15ef78ff6a95d505c8050abc2061fe455c4ad1f
  - run_case-260926131051: 26682f394709f16e15faca08abe8d7dc3d7294b2c4789eea931c9b344fa976b6
  - run_case-260926131151: 71d32721fbe1e285d7b88963dc5ed912478429d6036ca087efe748e15e5b4468
  - run_case-260926131251: d6503c7a12967b8bbc814a169cfa5dd6a8a7f9ea85faf350835999027ce872b1
  - run_case-260926131351: 94fdba279879c5ef579ddc7cc40124bdcab03be3a5a4b42e13cb119e6f114852
  - run_case-260926131451: 36576097daf1c3c7e82bc7f3a4766e8ddd74df45ed3f016b2a2cbe13057b19ce
  - run_case-260926131716: 8a4893553d5cc34750b15e81656d01646ecfe20737ab7e26d0f55cd3742c853d
  - run_case-260926131847: b035084884468a9bee28fa7ca83958613aa41dacc887279147c1ece4f24e1f65
  - run_case-260926132307: 3dd34f4f972bccc1ea5fa3a18828106f94c9304c28a51efe83f5b2f8f9382153
  - run_case-260926132410: 94160f2c10ea38411533da5c378fb0e7c6018e7ea3830a97f72c76c5b53c1d6a
  - run_case-260926132510: 39800e7edd9e389169daa97ce573984934916609bbb22424468725f4a17cc769
  - run_case-260926132646: ed7f8bf1ab6010f37a314f212ca2eb02351f5ea76485f985e160a458c731cafb
  - run_case-260926132823: e09ecd2d707fc775e38264cecaba5cc8ef378fc5f3584697e5066849e0b9439a
  - run_case-260926132923: 2c05ac3f50575af0b55c34a9388b092237fb9aae635fc4c3f0ba5d5952e37374
  - run_case-260926133023: 1742752c22afccf4ee09d220effe5aa1a70e21f65f839f30228aaeedbc8ea572
  - run_case-260926133134: 052ef9a09d0c2011e3a0a87a96e4056b3f9a5e63f2e2df8e19086b6abbc9224b
  - run_case-260926133234: acb10b94b0bde7211650dbc94cf99541f2a9cc0b31c8efae52982cbcd87f1fdb
  - run_case-260926133408: a7356e482cd71b02f2f4484dba3b33f01ce51ac869b367c2d9249497d1aad360
  - run_case-260926133546: 7771a2c9ae72db9919d96bb1ca390d40a42a459345a54f5c22158547bc5dc7a7
  - run_case-260926133656: a9bcc637b348841b7bff877fa936b13d466b6affa4cf9554c8ee3c3873cd5e8b
  - run_case-260926133756: 5934139461cd1c12d3d78f6421aee789e5e62a8515ae06d590da42de1fa37cf0
  - run_case-260926133856: 8f4f6d3e989aec665dafc20e1bfdd8dd46d1e02322fa918356bc1cef0ed05009
  - run_case-260926134005: 069df134a18efefb116d97dc5ef3b3f2718a5d955f55f9cd74a33ac382eebaf9
  - run_case-260926134106: 4c810d231a34eeb3510c1625cf8a35c15d0ba7c8880eda8af49f4910d45c1820
  - run_case-260926134206: 90a29d7e5f9ec6762a48b940a83028025d0bac27c91409bbf1bc278fddbebc7c
  - run_case-260926134306: f13f5079c233b7caf75659a027c39ef6e765038b98ef283056ab528fb28c4922
  - run_case-260926134507: 8348ff0cf94fc31e1090d7619a218bd1abbb947962a8d37ed9c27a5dc056ebed
  - run_case-260926134843: ba0b704b56eb7446e08bc5d4912ed70ee2023c4fb2911a584d16e9cc9d86f30a
  - run_case-260926134943: 265bf27cb9b3f72364713fa8d51dd290e56faebaa3759ce018332d931896dd99
  - run_case-260926135049: d211a4a5ac0348f552e4cd5a33d5bfa0214604a3414f6e7158fc7a9cc09785a9

## 6. 한계

- 봉인의 한계(룰북 B6): 봉인 폴더 위치는 비밀이 아니고, 같은 OS 사용자로 도는 에이전트의 열람을 기술적으로 막지 못하며, 해시는 변조를 드러낼 뿐 열람을 막지 않는다
- 산문 패턴의 한계(룰북 B3-2): 문장 단위로 주어를 맞추지 않아 우연히 맞는 표현을 놓치고, 배수 표현은 r_U claim만 뒷받침한다
- 표본 크기와 신뢰구간 폭: 사례 40건. 한 시계열에서 여러 경보가 뽑히면 독립 가정이 약해진다
- 숫자·증감이 없는 극값·순위 표현은 채점하지 않으므로 틀려도 잡히지 않는다
- 채점기 입력(보고서 원문)은 증거 복사 전까지 outputs/에만 있어 저장소만으로 재채점할 수 없다
- 승격 규칙(CONFIRMED_NO_TRADE)은 policy_v1 승인 전이라 채점기가 따로 적용하지 않고 스냅샷 표시를 썼다(F1 전 보완)
