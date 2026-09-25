# 평가 결과 요약 — evaluate-260926012023

채점기(eval/scorer)가 쓴 요약이다. 에이전트는 이 파일을 고쳐 쓰지 않는다(자료 계약 §10.3 N8). 등급 표기는 룰북 A5·B7을 따른다.

## 0. 실행 조건

- 룰북: RB-1, 동결 커밋 없음(RB-1 동결 전), 동결 뒤 변경 미기재(실행 조건 입력 파일에 없음)
- snapshot_id dev20, 스냅샷 정규화 해시(normalized_sha256) 미기재(실행 조건 입력 파일에 없음), 대조 미기재(실행 조건 입력 파일에 없음)
- policy_version policy_v1, grouping_version g0(사유: 미기재(실행 조건 입력 파일에 없음))
- code_version 905a2aa9fe99d09df2ee76512947eda6c6a7c983, 채점기 커밋 미기재(실행 조건 입력 파일에 없음), 산문 패턴 목록 커밋 미기재(실행 조건 입력 파일에 없음)(채점기가 계산한 패턴 목록 지문 sha256 9184cbe2695231a2b4388c1418c0fa116e9bdff07acfe634bd30a61448017595)
- 실행 기간(KST) 2026-09-26T01:20:23+09:00 ~ 2026-09-26T02:00:05+09:00, 동시성 1, 순서 seed dev-order-v1
- 한도(룰북 B2와 대조한 실행 설정): 도구 호출 시도 8, 재조사 1, 모델 요청 10, 사례당 wall time 300초, 누적 토큰 128000
- 샌드박스 이름 ts-scored, 커밋한 라이브 정책 조회 본문(정책 YAML) sha256 미기재(실행 조건 입력 파일에 없음), 대조한 시험표 실행 폴더 이름 미기재(실행 조건 입력 파일에 없음), `configs/openshell/policy.yaml` sha256 dc2e8c3a7707e78cf86c1536ed5535fcf99e592376a2009d190d5564e87785a8
- 봉인 해시 재대조 해당 없음(봉인 묶음 아님)
- 채점 전 확인(평가 스킬 ②): 1 예정 실행의 최종 상태 확정 참: 예정 실행 60건 가운데 줄 없는 조합 0건, 인프라 실패 재실행(룰북 B5) 대상 0건·재실행 0건(채점기 계산: 미실행 0건), 2 버전 키 일치 미기재(실행 조건 입력 파일에 없음), 5 모드별 사례 집합 일치 미기재(실행 조건 입력 파일에 없음)(채점기 계산: 참), 순서 seed·동시성 적용 참: 순서 seed dev-order-v1, 동시성 1, 속도 조절(모델 실행 사이 최소 60초, 분당 토큰 50000, HTTP 429 뒤 120초), 쉰 시간 합 1365초, 429 뒤 더 쉰 횟수 0, 동시성을 올렸다면 근거 결정 기록 미기재(실행 조건 입력 파일에 없음)
- 사전 점검 결과 미기재(실행 조건 입력 파일에 없음)
- 계약 버전 schema_version 2, 자료 묶음 dev20, 평가 묶음 실행 evaluate-260926012023, 채점 실행 score-260926020005
- 채점기가 읽은 스냅샷 파일 data/snapshots/dev20/snapshot_build.sqlite, 바이트 sha256 0eb13bc7bb5e7e993aa0f44c936f9c512c560b3082b0a49914aeba3987bab1cb
- 계획: 사례 20건 × 모드 checklist, agent, full = 예정 실행 60건, 결과 줄 60줄
- 채점 대상 run_id 목록: run_case-260926012023, run_case-260926012024, run_case-260926012103, run_case-260926012104, run_case-260926012105, run_case-260926012106, run_case-260926012124, run_case-260926012230, run_case-260926012233, run_case-260926012330, run_case-260926012430, run_case-260926012530, run_case-260926012630, run_case-260926012730, run_case-260926012822, run_case-260926012823, run_case-260926012830, run_case-260926012930, run_case-260926013030, run_case-260926013146, run_case-260926013214, run_case-260926013246, run_case-260926013346, run_case-260926013446, run_case-260926013546, run_case-260926013646, run_case-260926013746, run_case-260926013802, run_case-260926013846, run_case-260926013947, run_case-260926014019, run_case-260926014047, run_case-260926014147, run_case-260926014247, run_case-260926014347, run_case-260926014447, run_case-260926014505, run_case-260926014506, run_case-260926014547, run_case-260926014554, run_case-260926014647, run_case-260926014747, run_case-260926014757, run_case-260926014847, run_case-260926014905, run_case-260926014947, run_case-260926015047, run_case-260926015147, run_case-260926015247, run_case-260926015318, run_case-260926015347, run_case-260926015447, run_case-260926015547, run_case-260926015658, run_case-260926015659, run_case-260926015759, run_case-260926015803, run_case-260926015859, run_case-260926015922, run_case-260926015959
- 상태 변화 집계(모델 원초안 → Critic 뒤 → 검증 뒤): 집계하지 않음(trace 형식 미정, 단위 L1. F1 전 보완)

## 1. 대표 지표 — 실자료 사실 주장 오류율 (real_sealed)

- 해당 없음(이 채점 실행의 자료 묶음은 dev20다)

## 2. 보조 지표 — holdout40 (등급 C)

- 해당 없음(이 채점 실행의 자료 묶음은 dev20다)

## 3. 개발 묶음 값 — 대표 숫자 아님 (등급 D)

- dev20 비교군 3개:

| 비교군 | 근거 충족 처리정확도 x/N(Wilson 95%) | 불필요 보류율 | 잘못된 모니터링률 | 실행 실패 x/N | 도구 시도 중앙값(범위) | 토큰 중앙값(범위) | 시간(ms) 중앙값(범위) | 등급 |
|---|---|---|---|---|---|---|---|---|
| checklist | 19/20 = 95.0% (76.4%~99.1%) | 0/12 = 0.0% (0.0%~24.3%) | 0/17 = 0.0% (0.0%~18.4%) | 0/20(FAILED 0, TIMEOUT 0, INVALID 0, BUDGET_EXCEEDED 0, 미실행 0) | 5(4~5) | 0(0~0) | 14(12~20) | 등급 D |
| agent | 18/20 = 90.0% (69.9%~97.2%) | 0/12 = 0.0% (0.0%~24.3%) | 0/17 = 0.0% (0.0%~18.4%) | 1/20(FAILED 1, TIMEOUT 0, INVALID 0, BUDGET_EXCEEDED 0, 미실행 0) | 5(3~7) | 14966(5386~31412) | 14305.5(3048~65068) | 등급 D |
| full | 17/20 = 85.0% (64.0%~94.8%) | 0/12 = 0.0% (0.0%~24.3%) | 1/17 = 5.9% (1.0%~27.0%) | 1/20(FAILED 0, TIMEOUT 0, INVALID 1, BUDGET_EXCEEDED 0, 미실행 0) | 6(5~7) | 34888.5(20640~50429) | 22118.5(3387~75056) | 등급 D |

- 모든 사례를 보류했을 때의 점수: 8/20 = 40.0% (21.9%~61.3%)
- 미실행: checklist 0건, agent 0건, full 0건(분모 20에 실패로 포함)
- 인프라 실패 재실행 건수: checklist 0건, agent 0건, full 0건
- 보조 분석(사전 등록) checklist 대 agent: 둘 다 성공 18 / checklist만 성공 1 / agent만 성공 0 / 둘 다 실패 1, Newcombe 짝 차이 95% 구간(checklist − agent) -9.6pp~+22.5pp, McNemar 정확 검정 p 1.000
  - agent에서 좋아진 사례: 없음 / 나빠진 사례: 850431-XO-202410
- 보조 분석(사전 등록) checklist 대 full: 둘 다 성공 17 / checklist만 성공 2 / full만 성공 0 / 둘 다 실패 1, Newcombe 짝 차이 95% 구간(checklist − full) -5.6pp~+29.1pp, McNemar 정확 검정 p 0.500
  - full에서 좋아진 사례: 없음 / 나빠진 사례: 850432-XO-202404, 850432-XQ-202410
- 보조 분석(사전 등록) agent 대 full: 둘 다 성공 16 / agent만 성공 2 / full만 성공 1 / 둘 다 실패 1, Newcombe 짝 차이 95% 구간(agent − full) -14.3pp~+24.9pp, McNemar 정확 검정 p 1.000
  - full에서 좋아진 사례: 850431-XO-202410 / 나빠진 사례: 850432-XO-202404, 850432-XQ-202410
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
| MAINTAIN | 9 | 0 | 0 | 0 |
| MONITOR | 0 | 3 | 0 | 0 |
| HOLD | 0 | 0 | 7 | 1 |

- full

| 정답 \ 최종 | MAINTAIN | MONITOR | HOLD | 실행 실패 |
|---|---|---|---|---|
| MAINTAIN | 8 | 1 | 0 | 0 |
| MONITOR | 0 | 3 | 0 | 0 |
| HOLD | 0 | 0 | 7 | 1 |


## 4. 참고 지표

- 스킬 호출 성공률(NemoClaw 경로, 정확도 지표에는 영향을 주지 않는다): 미기재(실행 조건 입력 파일에 없음)
- 한국어 품질(참고, 자동 검사): checklist 한글 비율 87.7%, 금지 표현 0건, 필수 항목 누락 20건; agent 한글 비율 91.5%, 금지 표현 0건, 필수 항목 누락 19건; full 한글 비율 87.0%, 금지 표현 0건, 필수 항목 누락 16건. 표본 점검: 미기재(실행 조건 입력 파일에 없음)
- NAT 프로파일 요약(참고): {"runs": 60, "runs_with_profile": 60, "profile_files_complete": 60, "runs_with_nat_trace": 60, "runs_workflow_end": 60, "by_mode": {"checklist": {"runs": 20, "runs_with_profile": 20, "execution_status": {"COMPLETED": 20, "FAILED": 0, "TIMEOUT": 0, "INVALID": 0, "BUDGET_EXCEEDED": 0}, "model_requests": {"median": 0, "min": 0, "max": 0}, "tokens": {"median": 0, "min": 0, "max": 0}, "wall_ms": {"median": 14, "min": 12, "max": 20}, "nat_llm_calls": {"median": 0, "min": 0, "max": 0}, "nat_llm_ms": {"median": 0, "min": 0, "max": 0}, "nat_tokens": {"median": 0, "min": 0, "max": 0}, "nat_tool_calls": {"median": 5, "min": 4, "max": 5}, "nat_workflow_ms": {"median": 14, "min": 12, "max": 20}, "stage_spans": {"basic": 20, "critic": 0, "revision": 0, "final": 20, "other": 0}}, "agent": {"runs": 20, "runs_with_profile": 20, "execution_status": {"COMPLETED": 19, "FAILED": 1, "TIMEOUT": 0, "INVALID": 0, "BUDGET_EXCEEDED": 0}, "model_requests": {"median": 2, "min": 2, "max": 4}, "tokens": {"median": 15179, "min": 11627, "max": 31412}, "wall_ms": {"median": 13691, "min": 3048, "max": 51369}, "nat_llm_calls": {"median": 3, "min": 2, "max": 8}, "nat_llm_ms": {"median": 7880.5, "min": 3019, "max": 65048}, "nat_tokens": {"median": 14966, "min": 5386, "max": 31412}, "nat_tool_calls": {"median": 5, "min": 3, "max": 7}, "nat_workflow_ms": {"median": 14305.5, "min": 3048, "max": 65069}, "stage_spans": {"basic": 20, "critic": 0, "revision": 5, "final": 5, "other": 0}}, "full": {"runs": 20, "runs_with_profile": 20, "execution_status": {"COMPLETED": 19, "FAILED": 0, "TIMEOUT": 0, "INVALID": 1, "BUDGET_EXCEEDED": 0}, "model_requests": {"median": 5, "min": 3, "max": 6}, "tokens": {"median": 34900, "min": 20640, "max": 50429}, "wall_ms": {"median": 22080, "min": 3387, "max": 75056}, "nat_llm_calls": {"median": 6, "min": 3, "max": 11}, "nat_llm_ms": {"median": 10666.5, "min": 3363, "max": 50147}, "nat_tokens": {"median": 34888.5, "min": 20640, "max": 50429}, "nat_tool_calls": {"median": 6.5, "min": 5, "max": 9}, "nat_workflow_ms": {"median": 22118.5, "min": 3387, "max": 75056}, "stage_spans": {"basic": 20, "critic": 19, "revision": 15, "final": 15, "other": 0}}}}

## 5. 재현 명령

- 채점 대상 실행: tradesentry evaluate --snapshot dev20 --policy policy_v1
- 정답 대조 채점: python -m eval.scorer --run outputs/evaluate-260926012023
- 스냅샷 검증: tradesentry snapshot-verify --snapshot dev20
- 채점기 입력(보고서 원문) 위치: artifacts/eval/score-260926020005/{run_id}/(증거 복사 때 함께 복사. 봉인 묶음은 금지 해제 조건 뒤). 보고서 파일 바이트 sha256:
  - run_case-260926012023: 84e175513ce75ae89dcaa751b0a773b65e960fe17e4d7e64d9a020d7b0f0e2ae
  - run_case-260926012103: d405d41d499cc5d8079bfab8791da7a3b0e0854a60d6dc99e4bae7aecdd930c0
  - run_case-260926012104: f982781f95ecfe683810bf8befaf7cdea5a42c4322884fc210a4731b252b64e1
  - run_case-260926012105: 2c8e53a4a9d4b16918916013f2b92ab24626f338886d3347b2f6be221fbe2159
  - run_case-260926012106: f83738bb55309bbc7a341261484d9d927e91ce1dfc58692a60e84901918bbe67
  - run_case-260926012230: d280fb2cb5dca1f751650a3cf70643135db99e6fcdaa22ed714392bf0c94f749
  - run_case-260926012233: 2fce24651d83444cb24c4d99be13b9d8c95c676b593f99b5431a58b6bce6d3db
  - run_case-260926012330: 0f75b4103767043e01a5a616287e7e0274d6b45c641e12763bf33e256664fc0d
  - run_case-260926012430: cf1e02087b07255458729f3f744a5768b31033e3e31353718a9643ecef55128a
  - run_case-260926012530: 7ad45546ae86e60d092ae3074af252eeeecf969875763fe1804c92c6a8e64c2f
  - run_case-260926012630: d1e002fa8b2c8f982a712ff8507ece96eb11311958e42449ea9c6d2b81401026
  - run_case-260926012730: 24ff45a73429699280673bac4e37a834f3588c86b155664a8f22c9bc0cf030f5
  - run_case-260926012822: 2743559c2777354a16a10ca8c7423db7755b8d10c6423e73fe3142e558c48c0b
  - run_case-260926012823: 4a3555211d76b18b09f6b5cd5dccbec3863e7e05cefacd2cac0d60329a81ee02
  - run_case-260926012830: 154e630f8dc35d04244028e2a4047236a8190715ba58b46f7a62b55c89016827
  - run_case-260926012930: 40f4090e2db787db01533ea810adf36a5fdaa196ea067d9e8d410642b495d518
  - run_case-260926013030: 173a6e675f249eb6b603c2435ff19959afaf3db8968a9c83f9c7dd7bd85ef70b
  - run_case-260926013146: 42ca21be563a462e8378f8bdf25f72888fc89868edfd80d0b20066b71fb58c85
  - run_case-260926013214: 65d4c5fd19876bfd37f9366fae112af5443a8a2ba28cd2125d8eacaddda49543
  - run_case-260926013246: be25d752ab6afb451179affd2661dc79b12b6dd6cfbce0cc52acf25d934d3a53
  - run_case-260926013346: 7e9934ee42812c618e759655f405e68d58849627906f1bf4d24715a2d2c25d18
  - run_case-260926013446: d990c820319eb3f917f3e89b753ce9b7aaadb1f7503408755dd3b99e584c8efe
  - run_case-260926013546: 01bc9ce4a1a3639ec6ee65a9fdd3f88af309ca4fbd3ee6dd3596d0acfe870f18
  - run_case-260926013646: d102813e83da5bd41c4304aea475d321358e5067eb53257af6f242bec3d4d9f6
  - run_case-260926013746: db91b31c0f60f9301d30627499e132a900f8757959dedd2b2b5a24192d4f6d46
  - run_case-260926013802: e7a0fd4c10ad2250e76dc27e3de5c6179afaf2872b35620c993aa3e40c1935f5
  - run_case-260926013846: 5b24eb81ece1ab66d124ff425f74c5dd518349eb095699ad008fa534e67781bc
  - run_case-260926013947: f802df740806118fb653639376559f8f182cab58b35105f14969f8fd28b5d4f3
  - run_case-260926014019: 8ba314834d6505b0b79bb4109d7f72fccfde89e365ebf5bd4408ad796cb1a14c
  - run_case-260926014047: a0ee9869046a1cf6e4e280f884ee9db8a1df61546456f0e04ac35e62b2c1be7a
  - run_case-260926014147: 758c90b60594f1ebd7810b8a164e9b9b23a30f583d4fec201bb70c48aac699e4
  - run_case-260926014247: 243bd27bb7cc8d3368678954c78e09be0dc03934c4486b9933cea8cddd6b12c9
  - run_case-260926014347: 5ff0f8aa8d20c183fc6e5554c633842c3bd0b038429e1fd7061a7e4cd35b5d96
  - run_case-260926014447: 98cd603ca3e3392e25497eecf4d1df707c4954a6d92769cb8da484b02e63c396
  - run_case-260926014505: 3f16445be38188e69e23507ba1e5c2296ce30c24e1e497706e3af4bbad99124f
  - run_case-260926014506: 5a896d6553c0321d7ff8d7bffac5029f16ab08daa4b58cdb25b7bde867649ebe
  - run_case-260926014547: d94dd44d9557721f1f197c7a16bef6ee99907f590ecf11f80fad0c2ad14b31ed
  - run_case-260926014554: 41f6e7c642489553f85fae259f940ec69e0f361e1b965400c5e49b9e7e7fe590
  - run_case-260926014647: 4e2ad58420309578e4387c5d2271b901a1375b00b37bb9cb9de605406c863f1f
  - run_case-260926014747: 36183f10d2ec3518029c0b194661fd52c48f3abcf58fb4feca7b7451cd9cb18f
  - run_case-260926014757: 2eeabecc2813b730f204c020406d864826a25be915e95ce13f347029e14e551e
  - run_case-260926014847: 7c70ff5e71bd5399a363300884ef1f9411af07f8c50f074ac56f4e48b8b5ecad
  - run_case-260926014905: d4c581f0c41676acab1497b4dcf2ff39e7acbc80c74e3d8a73aa39d41d5aaa5a
  - run_case-260926014947: 7c92ac77c804deea5b4173fe1d749a8aa1fc1ef3eff681363ae6039cc6305d16
  - run_case-260926015047: 27fe30258d594c2cd740c9260955f1dd54b6013e732887de44ac3ed28a670a2c
  - run_case-260926015147: 29407a2677a86ad3b60efbdb64e38b6c2e5a682b8ee30ed7cb66bf247524d8bc
  - run_case-260926015247: 7c9c011dfdf6d9df6c81c317a39454756bf10fab5de341989e21bf12900c6534
  - run_case-260926015318: e337089eb3e05c0f3c41e5d3a8595ad12858845d44bba599e9c8d3e3344fbe50
  - run_case-260926015347: a3b72cdaa75ae8e34f7bd5cb33fb3e0f4c8c816af2dff16d1575ee798cf4ed65
  - run_case-260926015447: 39aa6de933112c376adf4ee7796959a5472c19e988017912607a6bf7c92fa6b0
  - run_case-260926015547: ab456fba09bee1d4a45d94a6bceb77db54bdcf0a886fb770d31dd24bc78c8b54
  - run_case-260926015658: 0c9ef3e7db32a2c89f78b63aca69c36c7edab66d51397795fd3618361c64846d
  - run_case-260926015659: 6d4673b91073d8d001490ff5d9078974f1d25bb372d154b23dc332a11f2e8de5
  - run_case-260926015759: b68a8b379459f69f8b27180949b9e0e9ac72115650dc443dbba00483ba77e9e0
  - run_case-260926015803: 29b257ebcddebc6d7197e1c5abeea882c963279e38d7325c1600c5f711b8482c
  - run_case-260926015859: 3416b80739bcfae753c1c063bce541dd6e110b3ddcad604e88415d52b1c5010a
  - run_case-260926015922: bb6656bb095d9038ea86828f6642090fb316ad41570f012e613dbc8160532e9c
  - run_case-260926015959: d2e47f9c988c412be67c738e4620268b5515cf84fa756aed0fcd6deb1361a526

## 6. 한계

- 봉인의 한계(룰북 B6): 봉인 폴더 위치는 비밀이 아니고, 같은 OS 사용자로 도는 에이전트의 열람을 기술적으로 막지 못하며, 해시는 변조를 드러낼 뿐 열람을 막지 않는다
- 산문 패턴의 한계(룰북 B3-2): 문장 단위로 주어를 맞추지 않아 우연히 맞는 표현을 놓치고, 배수 표현은 r_U claim만 뒷받침한다
- 표본 크기와 신뢰구간 폭: 사례 20건. 한 시계열에서 여러 경보가 뽑히면 독립 가정이 약해진다
- 숫자·증감이 없는 극값·순위 표현은 채점하지 않으므로 틀려도 잡히지 않는다
- 채점기 입력(보고서 원문)은 증거 복사 전까지 outputs/에만 있어 저장소만으로 재채점할 수 없다
- 승격 규칙(CONFIRMED_NO_TRADE)은 policy_v1 승인 전이라 채점기가 따로 적용하지 않고 스냅샷 표시를 썼다(F1 전 보완)
