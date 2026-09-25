# 평가 결과 요약 — evaluate-260925230517

채점기(eval/scorer)가 쓴 요약이다. 에이전트는 이 파일을 고쳐 쓰지 않는다(자료 계약 §10.3 N8). 등급 표기는 룰북 A5·B7을 따른다.

## 0. 실행 조건

- 룰북: RB-1, 동결 커밋 없음(RB-1 동결 전), 동결 뒤 변경 미기재(실행 조건 입력 파일에 없음)
- snapshot_id dev20, 스냅샷 정규화 해시(normalized_sha256) 미기재(실행 조건 입력 파일에 없음), 대조 미기재(실행 조건 입력 파일에 없음)
- policy_version policy_v1, grouping_version g0(사유: 미기재(실행 조건 입력 파일에 없음))
- code_version 4da10b1a3e0edaac31c5bd33750c4bb794b32a56, 채점기 커밋 미기재(실행 조건 입력 파일에 없음), 산문 패턴 목록 커밋 미기재(실행 조건 입력 파일에 없음)(채점기가 계산한 패턴 목록 지문 sha256 9184cbe2695231a2b4388c1418c0fa116e9bdff07acfe634bd30a61448017595)
- 실행 기간(KST) 2026-09-25T23:05:17+09:00 ~ 2026-09-25T23:44:45+09:00, 동시성 1, 순서 seed dev-order-v1
- 한도(룰북 B2와 대조한 실행 설정): 도구 호출 시도 8, 재조사 1, 모델 요청 10, 사례당 wall time 300초, 누적 토큰 128000
- 샌드박스 이름 ts-scored, 커밋한 라이브 정책 조회 본문(정책 YAML) sha256 미기재(실행 조건 입력 파일에 없음), 대조한 시험표 실행 폴더 이름 미기재(실행 조건 입력 파일에 없음), `configs/openshell/policy.yaml` sha256 dc2e8c3a7707e78cf86c1536ed5535fcf99e592376a2009d190d5564e87785a8
- 봉인 해시 재대조 해당 없음(봉인 묶음 아님)
- 채점 전 확인(평가 스킬 ②): 1 예정 실행의 최종 상태 확정 참: 예정 실행 60건 가운데 줄 없는 조합 0건, 인프라 실패 재실행(룰북 B5) 대상 0건·재실행 0건(채점기 계산: 미실행 0건), 2 버전 키 일치 미기재(실행 조건 입력 파일에 없음), 5 모드별 사례 집합 일치 미기재(실행 조건 입력 파일에 없음)(채점기 계산: 참), 순서 seed·동시성 적용 참: 순서 seed dev-order-v1, 동시성 1, 속도 조절(모델 실행 사이 최소 60초, 분당 토큰 50000, HTTP 429 뒤 120초), 쉰 시간 합 1589초, 429 뒤 더 쉰 횟수 0, 동시성을 올렸다면 근거 결정 기록 미기재(실행 조건 입력 파일에 없음)
- 사전 점검 결과 미기재(실행 조건 입력 파일에 없음)
- 계약 버전 schema_version 2, 자료 묶음 dev20, 평가 묶음 실행 evaluate-260925230517, 채점 실행 score-260925234445
- 채점기가 읽은 스냅샷 파일 data/snapshots/dev20/snapshot_build.sqlite, 바이트 sha256 0eb13bc7bb5e7e993aa0f44c936f9c512c560b3082b0a49914aeba3987bab1cb
- 계획: 사례 20건 × 모드 checklist, agent, full = 예정 실행 60건, 결과 줄 60줄
- 채점 대상 run_id 목록: run_case-260925230517, run_case-260925230518, run_case-260925230547, run_case-260925230548, run_case-260925230549, run_case-260925230550, run_case-260925230618, run_case-260925230718, run_case-260925230731, run_case-260925230818, run_case-260925230918, run_case-260925231031, run_case-260925231131, run_case-260925231231, run_case-260925231242, run_case-260925231243, run_case-260925231331, run_case-260925231431, run_case-260925231531, run_case-260925231631, run_case-260925231645, run_case-260925231731, run_case-260925231831, run_case-260925231931, run_case-260925232031, run_case-260925232131, run_case-260925232231, run_case-260925232245, run_case-260925232331, run_case-260925232431, run_case-260925232441, run_case-260925232531, run_case-260925232631, run_case-260925232731, run_case-260925232831, run_case-260925232931, run_case-260925232957, run_case-260925232958, run_case-260925233031, run_case-260925233037, run_case-260925233131, run_case-260925233231, run_case-260925233243, run_case-260925233331, run_case-260925233336, run_case-260925233431, run_case-260925233531, run_case-260925233631, run_case-260925233731, run_case-260925233748, run_case-260925233831, run_case-260925233931, run_case-260925234031, run_case-260925234118, run_case-260925234131, run_case-260925234231, run_case-260925234258, run_case-260925234331, run_case-260925234343, run_case-260925234431
- 상태 변화 집계(모델 원초안 → Critic 뒤 → 검증 뒤): 집계하지 않음(trace 형식 미정, 단위 L1. F1 전 보완)

## 1. 대표 지표 — 실자료 사실 주장 오류율 (real_sealed)

- 해당 없음(이 채점 실행의 자료 묶음은 dev20다)

## 2. 보조 지표 — holdout40 (등급 C)

- 해당 없음(이 채점 실행의 자료 묶음은 dev20다)

## 3. 개발 묶음 값 — 대표 숫자 아님 (등급 D)

- dev20 비교군 3개:

| 비교군 | 근거 충족 처리정확도 x/N(Wilson 95%) | 불필요 보류율 | 잘못된 모니터링률 | 실행 실패 x/N | 도구 시도 중앙값(범위) | 토큰 중앙값(범위) | 시간(ms) 중앙값(범위) | 등급 |
|---|---|---|---|---|---|---|---|---|
| checklist | 19/20 = 95.0% (76.4%~99.1%) | 0/12 = 0.0% (0.0%~24.3%) | 0/17 = 0.0% (0.0%~18.4%) | 0/20(FAILED 0, TIMEOUT 0, INVALID 0, BUDGET_EXCEEDED 0, 미실행 0) | 5(4~5) | 0(0~0) | 14(13~18) | 등급 D |
| agent | 19/20 = 95.0% (76.4%~99.1%) | 0/12 = 0.0% (0.0%~24.3%) | 0/17 = 0.0% (0.0%~18.4%) | 0/20(FAILED 0, TIMEOUT 0, INVALID 0, BUDGET_EXCEEDED 0, 미실행 0) | 5(4~8) | 14682(12327~32555) | 10402.5(2859~33179) | 등급 D |
| full | 17/20 = 85.0% (64.0%~94.8%) | 0/12 = 0.0% (0.0%~24.3%) | 0/17 = 0.0% (0.0%~18.4%) | 2/20(FAILED 1, TIMEOUT 0, INVALID 1, BUDGET_EXCEEDED 0, 미실행 0) | 6(4~7) | 30572.5(17162~43873) | 23947.5(9032~72416) | 등급 D |

- 모든 사례를 보류했을 때의 점수: 8/20 = 40.0% (21.9%~61.3%)
- 미실행: checklist 0건, agent 0건, full 0건(분모 20에 실패로 포함)
- 인프라 실패 재실행 건수: checklist 0건, agent 0건, full 0건
- 보조 분석(사전 등록) checklist 대 agent: 둘 다 성공 19 / checklist만 성공 0 / agent만 성공 0 / 둘 다 실패 1, Newcombe 짝 차이 95% 구간(checklist − agent) -14.5pp~+14.5pp, McNemar 정확 검정 p 1.000
  - agent에서 좋아진 사례: 없음 / 나빠진 사례: 없음
- 보조 분석(사전 등록) checklist 대 full: 둘 다 성공 17 / checklist만 성공 2 / full만 성공 0 / 둘 다 실패 1, Newcombe 짝 차이 95% 구간(checklist − full) -5.6pp~+29.1pp, McNemar 정확 검정 p 0.500
  - full에서 좋아진 사례: 없음 / 나빠진 사례: 850431-XO-202410, 850450-XP-202411
- 보조 분석(사전 등록) agent 대 full: 둘 다 성공 17 / agent만 성공 2 / full만 성공 0 / 둘 다 실패 1, Newcombe 짝 차이 95% 구간(agent − full) -5.6pp~+29.1pp, McNemar 정확 검정 p 0.500
  - full에서 좋아진 사례: 없음 / 나빠진 사례: 850431-XO-202410, 850450-XP-202411
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
| HOLD | 0 | 0 | 8 | 0 |

- full

| 정답 \ 최종 | MAINTAIN | MONITOR | HOLD | 실행 실패 |
|---|---|---|---|---|
| MAINTAIN | 8 | 0 | 0 | 1 |
| MONITOR | 0 | 3 | 0 | 0 |
| HOLD | 0 | 0 | 7 | 1 |


## 4. 참고 지표

- 스킬 호출 성공률(NemoClaw 경로, 정확도 지표에는 영향을 주지 않는다): 미기재(실행 조건 입력 파일에 없음)
- 한국어 품질(참고, 자동 검사): checklist 한글 비율 87.7%, 금지 표현 0건, 필수 항목 누락 20건; agent 한글 비율 90.7%, 금지 표현 0건, 필수 항목 누락 16건; full 한글 비율 91.3%, 금지 표현 0건, 필수 항목 누락 15건. 표본 점검: 미기재(실행 조건 입력 파일에 없음)
- NAT 프로파일 요약(참고): {"runs": 60, "runs_with_profile": 60, "profile_files_complete": 60, "runs_with_nat_trace": 60, "runs_workflow_end": 60, "by_mode": {"checklist": {"runs": 20, "runs_with_profile": 20, "execution_status": {"COMPLETED": 20, "FAILED": 0, "TIMEOUT": 0, "INVALID": 0, "BUDGET_EXCEEDED": 0}, "model_requests": {"median": 0, "min": 0, "max": 0}, "tokens": {"median": 0, "min": 0, "max": 0}, "wall_ms": {"median": 14, "min": 13, "max": 18}, "nat_llm_calls": {"median": 0, "min": 0, "max": 0}, "nat_llm_ms": {"median": 0, "min": 0, "max": 0}, "nat_tokens": {"median": 0, "min": 0, "max": 0}, "nat_tool_calls": {"median": 5, "min": 4, "max": 5}, "nat_workflow_ms": {"median": 14, "min": 13, "max": 19}, "stage_spans": {"basic": 20, "critic": 0, "revision": 0, "final": 20, "other": 0}}, "agent": {"runs": 20, "runs_with_profile": 20, "execution_status": {"COMPLETED": 20, "FAILED": 0, "TIMEOUT": 0, "INVALID": 0, "BUDGET_EXCEEDED": 0}, "model_requests": {"median": 2, "min": 2, "max": 4}, "tokens": {"median": 14682, "min": 12327, "max": 32555}, "wall_ms": {"median": 10402.5, "min": 2859, "max": 33179}, "nat_llm_calls": {"median": 2.5, "min": 2, "max": 8}, "nat_llm_ms": {"median": 6084, "min": 2839, "max": 15114}, "nat_tokens": {"median": 14682, "min": 12327, "max": 32555}, "nat_tool_calls": {"median": 5, "min": 4, "max": 8}, "nat_workflow_ms": {"median": 10402.5, "min": 2860, "max": 33180}, "stage_spans": {"basic": 20, "critic": 0, "revision": 3, "final": 3, "other": 0}}, "full": {"runs": 20, "runs_with_profile": 20, "execution_status": {"COMPLETED": 18, "FAILED": 1, "TIMEOUT": 0, "INVALID": 1, "BUDGET_EXCEEDED": 0}, "model_requests": {"median": 4, "min": 3, "max": 7}, "tokens": {"median": 30572.5, "min": 17234, "max": 43873}, "wall_ms": {"median": 23947.5, "min": 9032, "max": 45529}, "nat_llm_calls": {"median": 6, "min": 3, "max": 9}, "nat_llm_ms": {"median": 12484, "min": 5871, "max": 67389}, "nat_tokens": {"median": 30572.5, "min": 17162, "max": 43873}, "nat_tool_calls": {"median": 6, "min": 4, "max": 9}, "nat_workflow_ms": {"median": 23948.5, "min": 9032, "max": 72417}, "stage_spans": {"basic": 20, "critic": 19, "revision": 13, "final": 12, "other": 0}}}}

## 5. 재현 명령

- 채점 대상 실행: tradesentry evaluate --snapshot dev20 --policy policy_v1
- 정답 대조 채점: python -m eval.scorer --run outputs/evaluate-260925230517
- 스냅샷 검증: tradesentry snapshot-verify --snapshot dev20
- 채점기 입력(보고서 원문) 위치: artifacts/eval/score-260925234445/{run_id}/(증거 복사 때 함께 복사. 봉인 묶음은 금지 해제 조건 뒤). 보고서 파일 바이트 sha256:
  - run_case-260925230517: 4caa615f8fe70db32eaf9a0c5a2f08106aa868ff768cd40521bbbf4f5edd2745
  - run_case-260925230518: d12034d472d62676cf29e831ec6869726c3939b9cb1454fb573ac1eaa61d4237
  - run_case-260925230547: 1dd74d263dd4ad89e723d193f80c2accdb52bb1469932ed8d09b65493d13055e
  - run_case-260925230548: 0d992d29ef397b0b97f19b5965a7fae4edb1a34a4576925e143391cb7feaf2e4
  - run_case-260925230549: bc53a44ccf4e6731c3b419860fd1c163b4dc0cdc9fb797997bd277ae26c266fe
  - run_case-260925230550: 171a7ebc2ab7cc5d621a292160a7e8864539d98d49b59d8bb6b362f4a657b7fd
  - run_case-260925230618: c7238a9762dd9d0e78b801ec12a3576a768ca1afb8bba2a4d71d32c49e3825b6
  - run_case-260925230718: 3b88002a98d323c05d7ed6a0f109a20a69627d03584e587086e27049afbdbcd3
  - run_case-260925230731: b629f55840401cc57ec63b3fb50ca42473c0ab61a6ddd108aa2c469dd2dfc118
  - run_case-260925230818: 49854550c042bbe5eca45d1dea0786ef66f4e0b6b2578a4de71bb90298bd293e
  - run_case-260925231031: 9ecacdd915eda80bc78a067fb582018e3eaad5936254e3eb5913d6575bad29ff
  - run_case-260925231231: c49d63ce83f8d12810adb486f070eb39e6a921036480b2543868771192a7f7fb
  - run_case-260925231242: 5f021d1ec7737609ad0c9cc1019a10e25bb1d306aeb7da4f84b692afa79ddb54
  - run_case-260925231243: fba48559c6f4a5fef99ceb5e700f038aefa222478b74df8a6c93ad4d01365cd4
  - run_case-260925231331: 5eef31cfb89ed9986e632739a659f7962c003e26858a36a89dbdded693814886
  - run_case-260925231431: abadb536e2b7d2aab7e66e049ca265bb33378dc6351f0ae82efb1f93bbf780ac
  - run_case-260925231531: 6bdc0bf64ff32cff0126257dab4214020dbd24ddadb942a0710f187dbef8170a
  - run_case-260925231631: c0ee6bef7c8a288c020004a3e7029a2d482debe91e8026c76b1762feaafebbb6
  - run_case-260925231645: f8c47c29deb44830a62da33c0f27b812c8eaebad11595722adf393dbe563d22c
  - run_case-260925231731: 332957bd24dfbdd49af98d8ed82ada44f1c6b09aa936ac5c7029b54510422ca2
  - run_case-260925231831: 257dc0ae7c0a0b00679351ac8a1d59ac88168a4045ef15feade4437fb6d69d71
  - run_case-260925231931: 04434a282821efe361c561bba3f2ee9d20e193e75b3d5b8ceda1ed8f68e6e43a
  - run_case-260925232031: 28e4186a6a9843a34a631672b16920dd0ed8b656e766dea54bca080a0e181e10
  - run_case-260925232131: 1c1e1744000b698c6c0f49158260c88777090eff030d6192062571449cab0b81
  - run_case-260925232231: c0622ef609b573cf53fe1963b280a59c058e997a2ad86f0210585ce0c21a4947
  - run_case-260925232245: 23b5429ad3506ddf9001467950966f62b4c8df780ce96e763b287efa34b7c1b2
  - run_case-260925232331: 620d0bde9b3d37050f8fec9502d3b5c0d267da5604d55ce6d1b6077a3dbd7495
  - run_case-260925232431: dc59a2401d238fb8b93785f6b2da3fab47832d2cbc375b45e9dc93dfced37488
  - run_case-260925232441: 8cad3d8b0867b4d82bb31d0710c68c6368552a47ed1a7b7fed69726bf2d37984
  - run_case-260925232531: ff3518c1c1208be26eccbf21cd8381d73635818c910c70a9ef0386b75e65fe5e
  - run_case-260925232631: 88831ddb803fab355cc22b7069b6fafb07977031edbbfcdf08424cd368f37e2b
  - run_case-260925232731: 8b4718d75df8028b5d6fba7ee5432497d9014272c24e643a29481c1e4412a5bc
  - run_case-260925232831: 7d1cbfd2f78a23b053376da461e7fcef73972832c2b8db5a706195485ad189e6
  - run_case-260925232931: c179a09609d191d789eabccbe6060f4467bdfb0697310f0c6ff217a6b8a07c38
  - run_case-260925232957: 4ef1ffbf0f95028168cc22cc9e9c6bdfe6778175027b194f6afd97298b16abae
  - run_case-260925232958: 5895d837958ad25f67844b50ca56a80ece67a0731e93253bc4d2fed9fbc54afc
  - run_case-260925233031: 2c258de42364a30abdca17574b0db16962ffe62a83ec76704ef19220bcdac523
  - run_case-260925233037: d8f2584e4d344859140bdff173c8272751959ceee7d9b3864051ebf6354c876d
  - run_case-260925233131: 6c6439f001e716bc478b2f7741c28866d74d50982c91c740a945e48a0b7f994d
  - run_case-260925233231: 2ca05526ab938fef9bedbfefa3345a4aa213f094ee67156af697950f67fd61ba
  - run_case-260925233243: 5e96449436ba1d4fa7d36358eef49d9e2b51e7eef9c628496b6f2528a5f89988
  - run_case-260925233331: 9529cb3e42a60ec286e4983bf311e29e4cefe254ec4c89a13cc56c2b5df7310a
  - run_case-260925233336: b7941af356a90751b4ed1d879ba33d5122b6ac15b86bfc58513ac7a7618ed028
  - run_case-260925233431: 14630e31370fd0d6049f6df9d2a3d3437561b41ebeab29ec6677dd8ef18eb4e2
  - run_case-260925233531: 42882ca049718b0286ce02ecdfce093de5235306e85ae731a76865fbf357f9ef
  - run_case-260925233631: cdff4108ee1bc2462fb1ede976a457c4458559bfe878eb12647a6ed2688e78c9
  - run_case-260925233731: b2e2d86b67a7ed811d643a2090f9680423a0a1abc768bcfdabe85ddcbb0577fd
  - run_case-260925233748: 9418b3660bf8c79a257a38be96f110c9ac8e09d868d0cefa6e09126b17f8e938
  - run_case-260925233831: 9abfb40689e99a53d0643a7fb1cc7663e948cb0ca98ccc28e24cb59b251421cf
  - run_case-260925233931: 320f68dbecc3fc2945ac500e5c0de44734947a3ba87e46c81b68705f52d850cf
  - run_case-260925234031: 185993b3822d81dd30f7b5ad144bb6562a9a41fe0baf4c619d12220babd35e2d
  - run_case-260925234118: be3177a6b13d27e87022b2a090da112f96f6073ff12c1616bc5062b207c81e94
  - run_case-260925234131: 5afc68a726613ffa525b4e0fae573b9e6897f93757c517f0ef701a8ba3cc84f0
  - run_case-260925234231: 394356e6c2f3c5e660a4d348fe9d40e0ca72d0e14d0d453e15d9424b904070a5
  - run_case-260925234258: 2bbab31fa59bdc0f5d4ac55e44e944029f2f8276250922c68758a8df1118fe41
  - run_case-260925234331: 0578f5db25afd702eb720d4dbca4e7ad3d10e705a09c6cc3d69f816c85681d22
  - run_case-260925234343: 3dc0da11214c2cfb84164082f707a0c783d854c8e8e445a9f6084e0c55db05f5
  - run_case-260925234431: 06bc11c1ec0713c049e3488200987fe59a1902fa0c863cafb7e0681a7e11d0fb

## 6. 한계

- 봉인의 한계(룰북 B6): 봉인 폴더 위치는 비밀이 아니고, 같은 OS 사용자로 도는 에이전트의 열람을 기술적으로 막지 못하며, 해시는 변조를 드러낼 뿐 열람을 막지 않는다
- 산문 패턴의 한계(룰북 B3-2): 문장 단위로 주어를 맞추지 않아 우연히 맞는 표현을 놓치고, 배수 표현은 r_U claim만 뒷받침한다
- 표본 크기와 신뢰구간 폭: 사례 20건. 한 시계열에서 여러 경보가 뽑히면 독립 가정이 약해진다
- 숫자·증감이 없는 극값·순위 표현은 채점하지 않으므로 틀려도 잡히지 않는다
- 채점기 입력(보고서 원문)은 증거 복사 전까지 outputs/에만 있어 저장소만으로 재채점할 수 없다
- 승격 규칙(CONFIRMED_NO_TRADE)은 policy_v1 승인 전이라 채점기가 따로 적용하지 않고 스냅샷 표시를 썼다(F1 전 보완)
