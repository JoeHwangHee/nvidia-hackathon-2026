# 평가 결과 요약 — evaluate-260926020006

채점기(eval/scorer)가 쓴 요약이다. 에이전트는 이 파일을 고쳐 쓰지 않는다(자료 계약 §10.3 N8). 등급 표기는 룰북 A5·B7을 따른다.

## 0. 실행 조건

- 룰북: RB-1, 동결 커밋 없음(RB-1 동결 전), 동결 뒤 변경 미기재(실행 조건 입력 파일에 없음)
- snapshot_id kcs_202201_202412_v2, 스냅샷 정규화 해시(normalized_sha256) 미기재(실행 조건 입력 파일에 없음), 대조 미기재(실행 조건 입력 파일에 없음)
- policy_version policy_v1, grouping_version g0(사유: 미기재(실행 조건 입력 파일에 없음))
- code_version 905a2aa9fe99d09df2ee76512947eda6c6a7c983, 채점기 커밋 미기재(실행 조건 입력 파일에 없음), 산문 패턴 목록 커밋 미기재(실행 조건 입력 파일에 없음)(채점기가 계산한 패턴 목록 지문 sha256 9184cbe2695231a2b4388c1418c0fa116e9bdff07acfe634bd30a61448017595)
- 실행 기간(KST) 2026-09-26T02:00:06+09:00 ~ 2026-09-26T03:42:42+09:00, 동시성 1, 순서 seed dev-order-v1
- 한도(룰북 B2와 대조한 실행 설정): 도구 호출 시도 8, 재조사 1, 모델 요청 10, 사례당 wall time 300초, 누적 토큰 128000
- 샌드박스 이름 ts-scored, 커밋한 라이브 정책 조회 본문(정책 YAML) sha256 미기재(실행 조건 입력 파일에 없음), 대조한 시험표 실행 폴더 이름 미기재(실행 조건 입력 파일에 없음), `configs/openshell/policy.yaml` sha256 dc2e8c3a7707e78cf86c1536ed5535fcf99e592376a2009d190d5564e87785a8
- 봉인 해시 재대조 해당 없음(봉인 묶음 아님)
- 채점 전 확인(평가 스킬 ②): 1 예정 실행의 최종 상태 확정 참: 예정 실행 40건 가운데 줄 없는 조합 0건, 인프라 실패 재실행(룰북 B5) 대상 23건·재실행 23건(채점기 계산: 미실행 0건), 2 버전 키 일치 미기재(실행 조건 입력 파일에 없음), 5 모드별 사례 집합 일치 미기재(실행 조건 입력 파일에 없음)(채점기 계산: 참), 순서 seed·동시성 적용 참: 순서 seed dev-order-v1, 동시성 1, 속도 조절(모델 실행 사이 최소 60초, 분당 토큰 50000, HTTP 429 뒤 120초), 쉰 시간 합 3149초, 429 뒤 더 쉰 횟수 18, 동시성을 올렸다면 근거 결정 기록 미기재(실행 조건 입력 파일에 없음)
- 사전 점검 결과 미기재(실행 조건 입력 파일에 없음)
- 계약 버전 schema_version 2, 자료 묶음 real_dev, 평가 묶음 실행 evaluate-260926020006, 채점 실행 score-260926034242
- 채점기가 읽은 스냅샷 파일 data/snapshots/kcs_202201_202412_v2/snapshot_build.sqlite, 바이트 sha256 3a29db9227cc017771daf917ee5de907c7f46d6f41dc122782329d84faf12d7d
- 계획: 사례 20건 × 모드 freeform, full = 예정 실행 40건, 결과 줄 63줄
- 채점 대상 run_id 목록: run_case-260926020006, run_case-260926020109, run_case-260926020218, run_case-260926020332, run_case-260926020437, run_case-260926020619, run_case-260926020719, run_case-260926020819, run_case-260926020948, run_case-260926021048, run_case-260926021211, run_case-260926021311, run_case-260926021622, run_case-260926021915, run_case-260926022015, run_case-260926022327, run_case-260926022427, run_case-260926022527, run_case-260926022627, run_case-260926022727, run_case-260926022827, run_case-260926023105, run_case-260926023205, run_case-260926023441, run_case-260926023835, run_case-260926023935, run_case-260926024242, run_case-260926024342, run_case-260926024442, run_case-260926024756, run_case-260926024856, run_case-260926025156, run_case-260926025256, run_case-260926025356, run_case-260926025632, run_case-260926025925, run_case-260926030025, run_case-260926030125, run_case-260926030225, run_case-260926030523, run_case-260926030806, run_case-260926030906, run_case-260926031006, run_case-260926031243, run_case-260926031343, run_case-260926031443, run_case-260926031543, run_case-260926031837, run_case-260926031937, run_case-260926032230, run_case-260926032330, run_case-260926032624, run_case-260926032724, run_case-260926032824, run_case-260926032924, run_case-260926033109, run_case-260926033209, run_case-260926033503, run_case-260926033603, run_case-260926033703, run_case-260926033940, run_case-260926034040, run_case-260926034205
- real_dev 경보 목록(분모): 850432-PH-202302(850432·PH·202302), 850450-MY-202401(850450·MY·202401), 850431-MX-202404(850431·MX·202404), 850450-JP-202307(850450·JP·202307), 850432-CN-202301(850432·CN·202301), 850431-MX-202310(850431·MX·202310), 850431-CN-202405(850431·CN·202405), 850432-US-202303(850432·US·202303), 850431-MX-202305(850431·MX·202305), 850450-MY-202302(850450·MY·202302), 850432-PH-202411(850432·PH·202411), 850432-US-202409(850432·US·202409), 850432-CN-202304(850432·CN·202304), 850450-IN-202410(850450·IN·202410), 850490-ID-202306(850490·ID·202306), 850490-PH-202412(850490·PH·202412), 850490-FI-202402(850490·FI·202402), 850490-FI-202312(850490·FI·202312), 850431-PH-202302(850431·PH·202302), 850431-MX-202306(850431·MX·202306)
- 상태 변화 집계(모델 원초안 → Critic 뒤 → 검증 뒤): 집계하지 않음(trace 형식 미정, 단위 L1. F1 전 보완)

## 1. 대표 지표 — 실자료 사실 주장 오류율 (real_sealed)

- 해당 없음(이 채점 실행의 자료 묶음은 real_dev다)

## 2. 보조 지표 — holdout40 (등급 C)

- 해당 없음(이 채점 실행의 자료 묶음은 real_dev다)

## 3. 개발 묶음 값 — 대표 숫자 아님 (등급 D)

- real_dev freeform 대 full — "개발 묶음 값, 대표 숫자 아님"
- 사례 20건, 서로 다른 시계열 12개

| 모드 | 예정 실행 | COMPLETED | 실행 실패(상태별) | 보고서 단위 오류율(Wilson 95%) | 주장 단위 오류율(참고) | 보고서당 claim 수(평균/중앙값/최대) | 보고서당 UNBACKED_PROSE(평균/중앙값/최대) | UNBACKED_PROSE 필드별(narrative / hypotheses / claims[].text) | 민감도: hypotheses를 뺀 보고서 단위 오류율 | 등급 |
|---|---|---|---|---|---|---|---|---|---|---|
| freeform | 20 | 12 | FAILED 8, TIMEOUT 0, INVALID 0, BUDGET_EXCEEDED 0, 미실행 0 | 11/20 = 55.0% (34.2%~74.2%) | 4/82 = 4.9% | 6.8/6/14 | 0/0/0 | 0 / 0 / 0 | 11/20 = 55.0% (34.2%~74.2%) | 등급 D(개발 묶음 값, 대표 숫자 아님) |
| full | 20 | 9 | FAILED 11, TIMEOUT 0, INVALID 0, BUDGET_EXCEEDED 0, 미실행 0 | 11/20 = 55.0% (34.2%~74.2%) | 0/62 = 0.0% | 6.9/7/10 | 0/0/0 | 0 / 0 / 0 | 11/20 = 55.0% (34.2%~74.2%) | 등급 D(개발 묶음 값, 대표 숫자 아님) |

| 모드 | 자릿수만 다른 WRONG_VALUE(민감도) | 발동 신호별 주장 요건 미충족으로 생긴 INVALID | 인프라 실패 재실행(건수 / 재실행 전 기록으로 계산한 보고서 단위 오류율) |
|---|---|---|---|
| freeform | 0 | 집계하지 않음(원인 분류 코드 미정, 단위 L3) | 10 / 12/20 = 60.0% (38.7%~78.1%) |
| full | 0 | 집계하지 않음(원인 분류 코드 미정, 단위 L3) | 13 / 13/20 = 65.0% (43.3%~81.9%) |

- 차이 판정(1차, B4 비겹침 규칙): 구간이 겹쳐서 "차이를 확인하지 못했다"(차이가 없다는 뜻이 아님)
- 보조 분석(사전 등록): 짝 비교 둘 다 오류 6 / freeform만 오류 5 / full만 오류 5 / 둘 다 무오류 4, Newcombe 짝 차이 95% 구간(freeform − full) -28.4pp~+28.4pp, McNemar 정확 검정 p 1.000
- 결과 집합 분포(source=claim): freeform CORRECT 78, WRONG_VALUE 1, WRONG_DIRECTION 0, WRONG_UNIT 0, WRONG_REFERENT 3, UNSUPPORTED 0; full CORRECT 62, WRONG_VALUE 0, WRONG_DIRECTION 0, WRONG_UNIT 0, WRONG_REFERENT 0, UNSUPPORTED 0
- 결과 집합 분포(source=prose): freeform CORRECT 67, UNBACKED_PROSE 0; full CORRECT 71, UNBACKED_PROSE 0
- 극값·순위 표현 건수(참고, 채점 제외): freeform 0 / full 0
- 범위 밖: 숫자·증감이 없는 정성 서술과 극값·순위 말의 의미 정확성

## 4. 참고 지표

- 스킬 호출 성공률(NemoClaw 경로, 정확도 지표에는 영향을 주지 않는다): 미기재(실행 조건 입력 파일에 없음)
- 한국어 품질(참고, 자동 검사): freeform 한글 비율 87.2%, 금지 표현 0건, 필수 항목 누락 11건; full 한글 비율 90.6%, 금지 표현 0건, 필수 항목 누락 8건. 표본 점검: 미기재(실행 조건 입력 파일에 없음)
- NAT 프로파일 요약(참고): {"runs": 63, "runs_with_profile": 63, "profile_files_complete": 63, "runs_with_nat_trace": 63, "runs_workflow_end": 63, "by_mode": {"full": {"runs": 33, "runs_with_profile": 33, "execution_status": {"COMPLETED": 9, "FAILED": 24, "TIMEOUT": 0, "INVALID": 0, "BUDGET_EXCEEDED": 0}, "model_requests": {"median": 4, "min": 3, "max": 6}, "tokens": {"median": 39796, "min": 26378, "max": 85591}, "wall_ms": {"median": 43001, "min": 15472, "max": 84412}, "nat_llm_calls": {"median": 6, "min": 4, "max": 19}, "nat_llm_ms": {"median": 6481, "min": 723, "max": 28098}, "nat_tokens": {"median": 17846, "min": 0, "max": 85591}, "nat_tool_calls": {"median": 4, "min": 2, "max": 9}, "nat_workflow_ms": {"median": 42676, "min": 15472, "max": 156650}, "stage_spans": {"basic": 33, "critic": 14, "revision": 14, "final": 8, "other": 0}}, "freeform": {"runs": 30, "runs_with_profile": 30, "execution_status": {"COMPLETED": 12, "FAILED": 18, "TIMEOUT": 0, "INVALID": 0, "BUDGET_EXCEEDED": 0}, "model_requests": {"median": 4, "min": 3, "max": 6}, "tokens": {"median": 44555.5, "min": 23205, "max": 74178}, "wall_ms": {"median": 31048.5, "min": 18062, "max": 104852}, "nat_llm_calls": {"median": 5, "min": 3, "max": 15}, "nat_llm_ms": {"median": 5726.5, "min": 834, "max": 39197}, "nat_tokens": {"median": 15433, "min": 0, "max": 74178}, "nat_tool_calls": {"median": 4, "min": 2, "max": 8}, "nat_workflow_ms": {"median": 36145, "min": 18062, "max": 112717}, "stage_spans": {"basic": 30, "critic": 13, "revision": 13, "final": 10, "other": 0}}}}

## 5. 재현 명령

- 채점 대상 실행: tradesentry evaluate --snapshot kcs_202201_202412_v2 --policy policy_v1
- 정답 대조 채점: python -m eval.scorer --run outputs/evaluate-260926020006
- 스냅샷 검증: tradesentry snapshot-verify --snapshot kcs_202201_202412_v2
- 채점기 입력(보고서 원문) 위치: artifacts/eval/score-260926034242/{run_id}/(증거 복사 때 함께 복사. 봉인 묶음은 금지 해제 조건 뒤). 보고서 파일 바이트 sha256:
  - run_case-260926020006: 6ee6acd76ede1ee15e0074cf717fa38b22c7835b14f1b1b8c2bcc4565cf87aad
  - run_case-260926020109: b5f77dfef1587398b48674c47df6ccd06fda8cb238e3be6aeffc7493dc2e64ec
  - run_case-260926020218: af23db6c3a34ed257bd2f360a68d6d4dd0ce08e2cde1ce102f2b5e6909b88613
  - run_case-260926020332: 23941d52c7db1d9a2449dda64bfde22f1f61b4ef039be086640e8a4a877a9633
  - run_case-260926020437: 8667f67ef0df95b0fb38b10ddda0ea45b21ef6ab9a88d18ab5e8041349cbe16b
  - run_case-260926020619: 80982711ea75817904bff5f32b3dbdb0cf7ad3a0f07a25531efdd3085b362447
  - run_case-260926020719: 6b8b5166c5a67882edc0ead1df376759c99b24e0d4f9169ee0d3296cf4dd9699
  - run_case-260926020819: 51db16ab959f93291792c6b4aeec91a5e8a3a6156c167e6480468f8d65166ac7
  - run_case-260926020948: 3335cb6962c10b2d10cd884fcba07ba50a755a98aeb1aab508b1a6dc39f3d5eb
  - run_case-260926021048: 9dbf75e32c749543850fdb659d91c2997bf429b92730ab3c4f39f4ce7a55f6e9
  - run_case-260926021211: 3abab61db547a888d43ec65c097d85892ba9c2c29ecec9e83992847d5ea07865
  - run_case-260926022327: c3dfbf02288a893d40fa7e111ca67368a5dabaf2d6c9c71878f7f086c84880be
  - run_case-260926022727: 61828bc99583a9ee3259fbf1608515a43730f72acecb76030fc8b62d3feba0f8
  - run_case-260926023105: e6d2d916fb091e6d1b8e443c8cf0231992d75bf5cbf1f8bc34b10db857e55771
  - run_case-260926023835: 40ba36ee4797f7657383743253834ce9c16174b81271290caa428e8f9eb54e89
  - run_case-260926024756: 8f31c8eb57939a64e678a67bcc6da2b2cb54f71da27de2c56e5476652020149d
  - run_case-260926025156: bd73e20ff90ad6554c483a0db7d9cb724db513757fde762f8dc441137c42b12e
  - run_case-260926030806: d75dcf6fb12c3991d6c9b9114a8a3c4d890f0a2ee03f7546dbbf5005f9662847
  - run_case-260926032624: d282c9822b95e4ec6c8cab04003543781a49b7eda8ad24171dd1cd326899fc75
  - run_case-260926032924: 95d802f2c524b15a5f66edfd45d7aa27905c5e8c99ed3b27100a99a3f77181f3
  - run_case-260926034040: 26ef998350607975b6fbc634233553a0de46bec2a624549669d30d0d94892a91

## 6. 한계

- 봉인의 한계(룰북 B6): 봉인 폴더 위치는 비밀이 아니고, 같은 OS 사용자로 도는 에이전트의 열람을 기술적으로 막지 못하며, 해시는 변조를 드러낼 뿐 열람을 막지 않는다
- 산문 패턴의 한계(룰북 B3-2): 문장 단위로 주어를 맞추지 않아 우연히 맞는 표현을 놓치고, 배수 표현은 r_U claim만 뒷받침한다
- 표본 크기와 신뢰구간 폭: 사례 20건. 한 시계열에서 여러 경보가 뽑히면 독립 가정이 약해진다
- 숫자·증감이 없는 극값·순위 표현은 채점하지 않으므로 틀려도 잡히지 않는다
- 채점기 입력(보고서 원문)은 증거 복사 전까지 outputs/에만 있어 저장소만으로 재채점할 수 없다
- 승격 규칙(CONFIRMED_NO_TRADE)은 policy_v1 승인 전이라 채점기가 따로 적용하지 않고 스냅샷 표시를 썼다(F1 전 보완)
