# 평가 결과 요약 — evaluate-260925201452

채점기(eval/scorer)가 쓴 요약이다. 에이전트는 이 파일을 고쳐 쓰지 않는다(자료 계약 §10.3 N8). 등급 표기는 룰북 A5·B7을 따른다.

## 0. 실행 조건

- 룰북: RB-1, 동결 커밋 없음(RB-1 동결 전), 동결 뒤 변경 미기재(실행 조건 입력 파일에 없음)
- snapshot_id dev20, 스냅샷 정규화 해시(normalized_sha256) 미기재(실행 조건 입력 파일에 없음), 대조 미기재(실행 조건 입력 파일에 없음)
- policy_version policy_v1, grouping_version g0(사유: 미기재(실행 조건 입력 파일에 없음))
- code_version 3f1832af37906ffa79c2783563967ece86a56c5f, 채점기 커밋 미기재(실행 조건 입력 파일에 없음), 산문 패턴 목록 커밋 미기재(실행 조건 입력 파일에 없음)(채점기가 계산한 패턴 목록 지문 sha256 9184cbe2695231a2b4388c1418c0fa116e9bdff07acfe634bd30a61448017595)
- 실행 기간(KST) 2026-09-25T20:14:52+09:00 ~ 2026-09-25T21:22:45+09:00, 동시성 1, 순서 seed dev-order-v1
- 한도(룰북 B2와 대조한 실행 설정): 도구 호출 시도 8, 재조사 1, 모델 요청 10, 사례당 wall time 300초, 누적 토큰 128000
- 샌드박스 이름 ts-scored, 커밋한 라이브 정책 조회 본문(정책 YAML) sha256 미기재(실행 조건 입력 파일에 없음), 대조한 시험표 실행 폴더 이름 미기재(실행 조건 입력 파일에 없음), `configs/openshell/policy.yaml` sha256 dc2e8c3a7707e78cf86c1536ed5535fcf99e592376a2009d190d5564e87785a8
- 봉인 해시 재대조 해당 없음(봉인 묶음 아님)
- 채점 전 확인(평가 스킬 ②): 1 예정 실행의 최종 상태 확정 참: 예정 실행 60건 가운데 줄 없는 조합 0건, 인프라 실패 재실행(룰북 B5) 대상 10건·재실행 10건(채점기 계산: 미실행 0건), 2 버전 키 일치 미기재(실행 조건 입력 파일에 없음), 5 모드별 사례 집합 일치 미기재(실행 조건 입력 파일에 없음)(채점기 계산: 참), 순서 seed·동시성 적용 참: 순서 seed dev-order-v1, 동시성 1, 속도 조절(모델 실행 사이 최소 60초, 분당 토큰 50000, HTTP 429 뒤 120초), 쉰 시간 합 2266초, 429 뒤 더 쉰 횟수 9, 동시성을 올렸다면 근거 결정 기록 미기재(실행 조건 입력 파일에 없음)
- 사전 점검 결과 미기재(실행 조건 입력 파일에 없음)
- 계약 버전 schema_version 2, 자료 묶음 dev20, 평가 묶음 실행 evaluate-260925201452, 채점 실행 score-260925212245
- 채점기가 읽은 스냅샷 파일 data/snapshots/dev20/snapshot_build.sqlite, 바이트 sha256 0eb13bc7bb5e7e993aa0f44c936f9c512c560b3082b0a49914aeba3987bab1cb
- 계획: 사례 20건 × 모드 checklist, agent, full = 예정 실행 60건, 결과 줄 70줄
- 채점 대상 run_id 목록: run_case-260925201452, run_case-260925201454, run_case-260925201541, run_case-260925201542, run_case-260925201543, run_case-260925201544, run_case-260925201741, run_case-260925202036, run_case-260925202045, run_case-260925202136, run_case-260925202236, run_case-260925202336, run_case-260925202726, run_case-260925202826, run_case-260925202835, run_case-260925202836, run_case-260925202926, run_case-260925203026, run_case-260925203153, run_case-260925203439, run_case-260925203456, run_case-260925203539, run_case-260925203639, run_case-260925203739, run_case-260925203839, run_case-260925203939, run_case-260925204039, run_case-260925204115, run_case-260925204315, run_case-260925204415, run_case-260925204431, run_case-260925204515, run_case-260925204615, run_case-260925204715, run_case-260925204815, run_case-260925204915, run_case-260925204944, run_case-260925204945, run_case-260925205015, run_case-260925205022, run_case-260925205115, run_case-260925205215, run_case-260925205235, run_case-260925205315, run_case-260925205348, run_case-260925205415, run_case-260925205515, run_case-260925205814, run_case-260925205914, run_case-260925210035, run_case-260925210036, run_case-260925210154, run_case-260925210258, run_case-260925210410, run_case-260925210411, run_case-260925210525, run_case-260925210601, run_case-260925210801, run_case-260925210813, run_case-260925210901, run_case-260925211001, run_case-260925211237, run_case-260925211337, run_case-260925211437, run_case-260925211714, run_case-260925211814, run_case-260925211914, run_case-260925212014, run_case-260925212114, run_case-260925212214
- 상태 변화 집계(모델 원초안 → Critic 뒤 → 검증 뒤): 집계하지 않음(trace 형식 미정, 단위 L1. F1 전 보완)

## 1. 대표 지표 — 실자료 사실 주장 오류율 (real_sealed)

- 해당 없음(이 채점 실행의 자료 묶음은 dev20다)

## 2. 보조 지표 — holdout40 (등급 C)

- 해당 없음(이 채점 실행의 자료 묶음은 dev20다)

## 3. 개발 묶음 값 — 대표 숫자 아님 (등급 D)

- dev20 비교군 3개:

| 비교군 | 근거 충족 처리정확도 x/N(Wilson 95%) | 불필요 보류율 | 잘못된 모니터링률 | 실행 실패 x/N | 도구 시도 중앙값(범위) | 토큰 중앙값(범위) | 시간(ms) 중앙값(범위) | 등급 |
|---|---|---|---|---|---|---|---|---|
| checklist | 19/20 = 95.0% (76.4%~99.1%) | 0/12 = 0.0% (0.0%~24.3%) | 0/17 = 0.0% (0.0%~18.4%) | 0/20(FAILED 0, TIMEOUT 0, INVALID 0, BUDGET_EXCEEDED 0, 미실행 0) | 5(4~5) | 0(0~0) | 13.5(13~19) | 등급 D |
| agent | 18/20 = 90.0% (69.9%~97.2%) | 0/12 = 0.0% (0.0%~24.3%) | 0/17 = 0.0% (0.0%~18.4%) | 1/20(FAILED 0, TIMEOUT 0, INVALID 1, BUDGET_EXCEEDED 0, 미실행 0) | 5(4~7) | 21392.5(12424~31407) | 18390(6091~63528) | 등급 D |
| full | 11/20 = 55.0% (34.2%~74.2%) | 0/12 = 0.0% (0.0%~24.3%) | 2/17 = 11.8% (3.3%~34.3%) | 5/20(FAILED 3, TIMEOUT 0, INVALID 2, BUDGET_EXCEEDED 0, 미실행 0) | 6(2~8) | 30314(0~41828) | 29790.5(8198~86055) | 등급 D |

- 모든 사례를 보류했을 때의 점수: 8/20 = 40.0% (21.9%~61.3%)
- 미실행: checklist 0건, agent 0건, full 0건(분모 20에 실패로 포함)
- 인프라 실패 재실행 건수: checklist 0건, agent 2건, full 8건
- 보조 분석(사전 등록) checklist 대 agent: 둘 다 성공 18 / checklist만 성공 1 / agent만 성공 0 / 둘 다 실패 1, Newcombe 짝 차이 95% 구간(checklist − agent) -9.6pp~+22.5pp, McNemar 정확 검정 p 1.000
  - agent에서 좋아진 사례: 없음 / 나빠진 사례: 850450-XP-202411
- 보조 분석(사전 등록) checklist 대 full: 둘 다 성공 11 / checklist만 성공 8 / full만 성공 0 / 둘 다 실패 1, Newcombe 짝 차이 95% 구간(checklist − full) +16.9pp~+60.1pp, McNemar 정확 검정 p 0.008
  - full에서 좋아진 사례: 없음 / 나빠진 사례: 850431-XN-202408, 850431-XP-202412, 850431-XQ-202401, 850432-XM-202402, 850432-XP-202408, 850432-XQ-202410, 850450-XM-202405, 850490-XM-202403
- 보조 분석(사전 등록) agent 대 full: 둘 다 성공 10 / agent만 성공 8 / full만 성공 1 / 둘 다 실패 1, Newcombe 짝 차이 95% 구간(agent − full) +7.7pp~+56.8pp, McNemar 정확 검정 p 0.039
  - full에서 좋아진 사례: 850450-XP-202411 / 나빠진 사례: 850431-XN-202408, 850431-XP-202412, 850431-XQ-202401, 850432-XM-202402, 850432-XP-202408, 850432-XQ-202410, 850450-XM-202405, 850490-XM-202403
- 상태 변화(원초안 → Critic 뒤 → 검증 뒤): 집계하지 않음(trace 형식 미정, 단위 L1. F1 전 보완)

혼동행렬(행: 정답 사례 상태, 열: 최종 사례 상태와 실행 실패)

- checklist

| 정답 \ 최종 | MAINTAIN | MONITOR | HOLD | 실행 실패 |
|---|---|---|---|---|
| MAINTAIN | 9 | 0 | 0 | 0 |
| MONITOR | 0 | 3 | 0 | 0 |
| HOLD | 0 | 0 | 8 | 0 |

- agent

| 정답 \ 최종 | MAINTAIN | MONITOR | HOLD | 실행 실패 |
|---|---|---|---|---|
| MAINTAIN | 8 | 0 | 0 | 1 |
| MONITOR | 0 | 3 | 0 | 0 |
| HOLD | 0 | 0 | 8 | 0 |

- full

| 정답 \ 최종 | MAINTAIN | MONITOR | HOLD | 실행 실패 |
|---|---|---|---|---|
| MAINTAIN | 5 | 2 | 0 | 2 |
| MONITOR | 1 | 2 | 0 | 0 |
| HOLD | 0 | 0 | 5 | 3 |


## 4. 참고 지표

- 스킬 호출 성공률(NemoClaw 경로, 정확도 지표에는 영향을 주지 않는다): 미기재(실행 조건 입력 파일에 없음)
- 한국어 품질(참고, 자동 검사): checklist 한글 비율 87.7%, 금지 표현 0건, 필수 항목 누락 20건; agent 한글 비율 92.3%, 금지 표현 0건, 필수 항목 누락 16건; full 한글 비율 92.6%, 금지 표현 0건, 필수 항목 누락 13건. 표본 점검: 미기재(실행 조건 입력 파일에 없음)
- NAT 프로파일 요약(참고): {"runs": 70, "runs_with_profile": 70, "profile_files_complete": 70, "runs_with_nat_trace": 70, "runs_workflow_end": 70, "by_mode": {"checklist": {"runs": 20, "runs_with_profile": 20, "execution_status": {"COMPLETED": 20, "FAILED": 0, "TIMEOUT": 0, "INVALID": 0, "BUDGET_EXCEEDED": 0}, "model_requests": {"median": 0, "min": 0, "max": 0}, "tokens": {"median": 0, "min": 0, "max": 0}, "wall_ms": {"median": 13.5, "min": 13, "max": 19}, "nat_llm_calls": {"median": 0, "min": 0, "max": 0}, "nat_llm_ms": {"median": 0, "min": 0, "max": 0}, "nat_tokens": {"median": 0, "min": 0, "max": 0}, "nat_tool_calls": {"median": 5, "min": 4, "max": 5}, "nat_workflow_ms": {"median": 14, "min": 12, "max": 19}, "stage_spans": {"basic": 20, "critic": 0, "revision": 0, "final": 20, "other": 0}}, "agent": {"runs": 22, "runs_with_profile": 22, "execution_status": {"COMPLETED": 19, "FAILED": 2, "TIMEOUT": 0, "INVALID": 1, "BUDGET_EXCEEDED": 0}, "model_requests": {"median": 3, "min": 2, "max": 4}, "tokens": {"median": 22693, "min": 12424, "max": 31407}, "wall_ms": {"median": 17159, "min": 6091, "max": 63528}, "nat_llm_calls": {"median": 4, "min": 2, "max": 10}, "nat_llm_ms": {"median": 7689, "min": 3210, "max": 32471}, "nat_tokens": {"median": 21037, "min": 12424, "max": 31407}, "nat_tool_calls": {"median": 5, "min": 4, "max": 7}, "nat_workflow_ms": {"median": 19677, "min": 6091, "max": 77551}, "stage_spans": {"basic": 22, "critic": 0, "revision": 13, "final": 11, "other": 0}}, "full": {"runs": 28, "runs_with_profile": 28, "execution_status": {"COMPLETED": 15, "FAILED": 11, "TIMEOUT": 0, "INVALID": 2, "BUDGET_EXCEEDED": 0}, "model_requests": {"median": 4, "min": 3, "max": 7}, "tokens": {"median": 30810, "min": 16505, "max": 41828}, "wall_ms": {"median": 29077, "min": 8198, "max": 86055}, "nat_llm_calls": {"median": 6, "min": 4, "max": 15}, "nat_llm_ms": {"median": 8634, "min": 682, "max": 25463}, "nat_tokens": {"median": 30046.5, "min": 0, "max": 41828}, "nat_tool_calls": {"median": 6, "min": 2, "max": 8}, "nat_workflow_ms": {"median": 35756.5, "min": 8198, "max": 109433}, "stage_spans": {"basic": 28, "critic": 21, "revision": 19, "final": 14, "other": 0}}}}

## 5. 재현 명령

- 채점 대상 실행: tradesentry evaluate --snapshot dev20 --policy policy_v1
- 정답 대조 채점: python -m eval.scorer --run outputs/evaluate-260925201452
- 스냅샷 검증: tradesentry snapshot-verify --snapshot dev20
- 채점기 입력(보고서 원문) 위치: artifacts/eval/score-260925212245/{run_id}/(증거 복사 때 함께 복사. 봉인 묶음은 금지 해제 조건 뒤). 보고서 파일 바이트 sha256:
  - run_case-260925201452: f183caea53e34fdbb8901b538f714fa90abcf73eaa5a2ff0890c1d99dfb3d4ad
  - run_case-260925201541: f765d889cfdb07db898c7083a29c5bec02a3773508bf39f8662428c1b9be1cf0
  - run_case-260925201542: 4d45fad3f5b8172a4444921806ab123244c85b16870df739a3597da4e2e57fee
  - run_case-260925201543: d46d31aa887d38c02c42651d82c501a3fd83a8cec581adaa16c5c01bfdcc7c46
  - run_case-260925201544: b6d897684b1f4b64a8938504fa58d55c24c9b51b5d64745672697c5a576387a7
  - run_case-260925202036: 144995ac83123a182b489e9b633a049b9e5db134acff3ba45ac82e8e24f916c8
  - run_case-260925202045: fbaea8de907df5830843a50a4c89e4909c3355caf56b10f38fbc694b71331af1
  - run_case-260925202136: f433f8cb338db7d18af52c56058d9a507ec306d2e1a596fa6d9f972598440c9f
  - run_case-260925202236: a6237f33dcf9ffde4d72fe5a5783b00ade3426f7135047cbecbc4694ed70db51
  - run_case-260925202726: e1c817e7faf7906e6273910d71970886a16615715052717758dab0cf415c8139
  - run_case-260925202826: 993aac69ec3f7b993509e6fd238971ff31411ba715090b58ef7d8ff38e09bb5e
  - run_case-260925202835: 32ea243fb09c37522b538811f1af8a08d1769d487d99c9c4d8c853cd3f32fa35
  - run_case-260925202836: 166775bb40d6e19112042bea815ea8fecf0d5035570591db13d968a4859525ed
  - run_case-260925203026: 5061cc3f814eccac5ed0933d7812e0f13dbc93e84ba2f22857f63c72179729ed
  - run_case-260925203439: 12bc1b29cef1eb014ba4fd488d48ebed962f9fd30a943a8ad0e8843119971297
  - run_case-260925203456: e9406357f74cc7aa2d84642706170b81905376ca1022d133e3f51c719062e428
  - run_case-260925203539: b8662706ea4eed4367c5bfc766dae4e48f3e304fb64f603b68ad04a92299ea45
  - run_case-260925203639: 9f0ca8a92b535210208dd9a92cc6dc40ab3b3a473188cb4f50746ca3d64dad91
  - run_case-260925203739: 50df8f05962b05ccf538dce0bb9d945ec9359e7939849d2083ba7f0f741785ee
  - run_case-260925203839: 074aa7b352efc5ddb6ef3c28db65d6a527f51f2147b52d1c916a2a07887b6b9d
  - run_case-260925204115: 0e0df18b8b6aa667f3e83698d401f58175e70b2e151cfbcb4cbf0104549d0484
  - run_case-260925204315: 9b6e1e7e979495aa8113804ab99cd6403dec486593b1b8da2e811ca5401ce32b
  - run_case-260925204415: ed67c6f90a1b1a40cd51320d590b88360d23de4e035f5c607f595a41611a228a
  - run_case-260925204431: 40fae8f7a1778605aa19858186043d838d2e436200c0bca10e53df7476a015fc
  - run_case-260925204515: 478b58f6a1b78ebde759c7ca24a7644c822866637552a9cb431d94f09aaf5e68
  - run_case-260925204615: d570ce9bd5a46c8c701599459176a6c5199a0b05b7045442629736d7a4bdcb7b
  - run_case-260925204715: a7ae62011f51dc678aeca071ef2c152bc3ad7f376ffdce6f32fd07b9a5eb19ba
  - run_case-260925204815: 7bb2f39df2322ef6392a9a9d207fa1f9ef7070a6ce94323b3f77e16e684b4331
  - run_case-260925204944: c8cc5df52c5cc9d58c163477c691ba6c6de9a857c7cfa6c775e50cc20b46d47a
  - run_case-260925204945: e98ab74a667fd1d8d3392973482e526de02d8bed1c1516c0e14695f8540ebcee
  - run_case-260925205015: edf7cbc43312ac59d105cef3ef9e6f2fe68f7a6a4c61343970d6850d61da6003
  - run_case-260925205022: b8f7da8ce4a34801888c63077e01fcbb4c2b654c4f641e9fc2091baf8bf91be5
  - run_case-260925205115: 1cf6685170675deda203f57a2da08ccd48776040dbae8a1007c0ef9b61d378d2
  - run_case-260925205215: b788a016f5f9afad73f2612ed0c05ac95eff89291d8de1f890f9c0907b20edc4
  - run_case-260925205235: 3639b25829ceb4876c447f31c0adb77f383b1e171056e52be325e045207a2198
  - run_case-260925205315: e3243750f102762533a189169940ccdc86e763cc8218416710b95ba3bd35597a
  - run_case-260925205348: 0884fba5619313aeaa8bf3729b69847628637097b7e2f3244fc43707e05253b8
  - run_case-260925205814: 0ee898df013672fd8cec1eda728394f8bea6f5d0e95cf7a1e8193148758eafcc
  - run_case-260925210035: b3fe635b0f8a0ca56deb044c0ae4802fcabadf623d29cba5a867fe5a12bfa2c4
  - run_case-260925210154: 6acbf9f8dc10e3584693a42c0462220f6bfb1cd30eeb9714e2a898136a225320
  - run_case-260925210258: b70f911094641dd79bf7c961b7aebe0257d8cc0445f229d06c6417b133cc7c90
  - run_case-260925210410: df8418db298673b57a5d32c734a162a79d8f9587b90e5e21457679998502b5e1
  - run_case-260925210411: 586aadb38d9695b3e5597ae23269ee99ed1a1c21013160d4358f0f6dc5c2d6ef
  - run_case-260925210601: 8df7517e3a7735e3fe6a70ea0159da9c5cbb3743e7420f97a08020d93e4900d2
  - run_case-260925210801: 149061516b3e0e09660a7073f291bd5f2261b52e1dd8c09fd4a37e5b8edf3f6c
  - run_case-260925210813: 3ebbf9aea6a0622f7de1eb66ca5028502bf3e1f228da65d7db24902634666cf6
  - run_case-260925210901: 8117385b0048b3ce4ec88ce8c3b618e73f3732f596c23cee473eafc70a6db731
  - run_case-260925211237: f9fee7b50c6c5f29af6dc57145281fe6fe78841f4d4aa623a383d598bf11f160
  - run_case-260925211337: 2daa4514d83701a435289cdd6972b6239475962b7a782947c12f45b0308a67e3
  - run_case-260925211814: 042bd8db81f618cdd26340434b1cb2125a010d95d8c6d3527aa369f2e1d86a56
  - run_case-260925211914: 94fa79b6e443a1cc34bf1dc2cf4c4076d08ff48956067cb15d80759111731503
  - run_case-260925212014: 83cb68853d9b02f07aedc9dcaf6b0703dbc78b8424df22adb8147f080ae02c51
  - run_case-260925212114: d111687fed31997c9e465c62600da4dc292362a11b800030e99e7d7c89814982
  - run_case-260925212214: abc3a996763e95ceae7de705496858220dfc3c2e99863a15a55becb5d656b315

## 6. 한계

- 봉인의 한계(룰북 B6): 봉인 폴더 위치는 비밀이 아니고, 같은 OS 사용자로 도는 에이전트의 열람을 기술적으로 막지 못하며, 해시는 변조를 드러낼 뿐 열람을 막지 않는다
- 산문 패턴의 한계(룰북 B3-2): 문장 단위로 주어를 맞추지 않아 우연히 맞는 표현을 놓치고, 배수 표현은 r_U claim만 뒷받침한다
- 표본 크기와 신뢰구간 폭: 사례 20건. 한 시계열에서 여러 경보가 뽑히면 독립 가정이 약해진다
- 숫자·증감이 없는 극값·순위 표현은 채점하지 않으므로 틀려도 잡히지 않는다
- 채점기 입력(보고서 원문)은 증거 복사 전까지 outputs/에만 있어 저장소만으로 재채점할 수 없다
- 승격 규칙(CONFIRMED_NO_TRADE)은 policy_v1 승인 전이라 채점기가 따로 적용하지 않고 스냅샷 표시를 썼다(F1 전 보완)
