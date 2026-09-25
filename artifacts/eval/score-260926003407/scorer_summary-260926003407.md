# 평가 결과 요약 — evaluate-260925234445

채점기(eval/scorer)가 쓴 요약이다. 에이전트는 이 파일을 고쳐 쓰지 않는다(자료 계약 §10.3 N8). 등급 표기는 룰북 A5·B7을 따른다.

## 0. 실행 조건

- 룰북: RB-1, 동결 커밋 없음(RB-1 동결 전), 동결 뒤 변경 미기재(실행 조건 입력 파일에 없음)
- snapshot_id kcs_202201_202412_v2, 스냅샷 정규화 해시(normalized_sha256) 미기재(실행 조건 입력 파일에 없음), 대조 미기재(실행 조건 입력 파일에 없음)
- policy_version policy_v1, grouping_version g0(사유: 미기재(실행 조건 입력 파일에 없음))
- code_version 4da10b1a3e0edaac31c5bd33750c4bb794b32a56, 채점기 커밋 미기재(실행 조건 입력 파일에 없음), 산문 패턴 목록 커밋 미기재(실행 조건 입력 파일에 없음)(채점기가 계산한 패턴 목록 지문 sha256 9184cbe2695231a2b4388c1418c0fa116e9bdff07acfe634bd30a61448017595)
- 실행 기간(KST) 2026-09-25T23:44:45+09:00 ~ 2026-09-26T00:34:07+09:00, 동시성 1, 순서 seed dev-order-v1
- 한도(룰북 B2와 대조한 실행 설정): 도구 호출 시도 8, 재조사 1, 모델 요청 10, 사례당 wall time 300초, 누적 토큰 128000
- 샌드박스 이름 ts-scored, 커밋한 라이브 정책 조회 본문(정책 YAML) sha256 미기재(실행 조건 입력 파일에 없음), 대조한 시험표 실행 폴더 이름 미기재(실행 조건 입력 파일에 없음), `configs/openshell/policy.yaml` sha256 dc2e8c3a7707e78cf86c1536ed5535fcf99e592376a2009d190d5564e87785a8
- 봉인 해시 재대조 해당 없음(봉인 묶음 아님)
- 채점 전 확인(평가 스킬 ②): 1 예정 실행의 최종 상태 확정 참: 예정 실행 40건 가운데 줄 없는 조합 0건, 인프라 실패 재실행(룰북 B5) 대상 3건·재실행 3건(채점기 계산: 미실행 0건), 2 버전 키 일치 미기재(실행 조건 입력 파일에 없음), 5 모드별 사례 집합 일치 미기재(실행 조건 입력 파일에 없음)(채점기 계산: 참), 순서 seed·동시성 적용 참: 순서 seed dev-order-v1, 동시성 1, 속도 조절(모델 실행 사이 최소 60초, 분당 토큰 50000, HTTP 429 뒤 120초), 쉰 시간 합 1726초, 429 뒤 더 쉰 횟수 0, 동시성을 올렸다면 근거 결정 기록 미기재(실행 조건 입력 파일에 없음)
- 사전 점검 결과 미기재(실행 조건 입력 파일에 없음)
- 계약 버전 schema_version 2, 자료 묶음 real_dev, 평가 묶음 실행 evaluate-260925234445, 채점 실행 score-260926003407
- 채점기가 읽은 스냅샷 파일 data/snapshots/kcs_202201_202412_v2/snapshot_build.sqlite, 바이트 sha256 3a29db9227cc017771daf917ee5de907c7f46d6f41dc122782329d84faf12d7d
- 계획: 사례 20건 × 모드 freeform, full = 예정 실행 40건, 결과 줄 43줄
- 채점 대상 run_id 목록: run_case-260925234445, run_case-260925234545, run_case-260925234645, run_case-260925234804, run_case-260925234904, run_case-260925235016, run_case-260925235116, run_case-260925235216, run_case-260925235320, run_case-260925235423, run_case-260925235523, run_case-260925235706, run_case-260925235806, run_case-260925235906, run_case-260926000006, run_case-260926000118, run_case-260926000218, run_case-260926000345, run_case-260926000445, run_case-260926000626, run_case-260926000807, run_case-260926000948, run_case-260926001113, run_case-260926001213, run_case-260926001313, run_case-260926001413, run_case-260926001513, run_case-260926001613, run_case-260926001713, run_case-260926001816, run_case-260926001947, run_case-260926002047, run_case-260926002147, run_case-260926002327, run_case-260926002427, run_case-260926002534, run_case-260926002634, run_case-260926002734, run_case-260926002834, run_case-260926002934, run_case-260926003109, run_case-260926003239, run_case-260926003339
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
| freeform | 20 | 18 | FAILED 2, TIMEOUT 0, INVALID 0, BUDGET_EXCEEDED 0, 미실행 0 | 5/20 = 25.0% (11.2%~46.9%) | 4/93 = 4.3% | 5.2/5/9 | 0.1/0/1 | 0 / 1 / 0 | 4/20 = 20.0% (8.1%~41.6%) | 등급 D(개발 묶음 값, 대표 숫자 아님) |
| full | 20 | 17 | FAILED 0, TIMEOUT 0, INVALID 3, BUDGET_EXCEEDED 0, 미실행 0 | 3/20 = 15.0% (5.2%~36.0%) | 0/100 = 0.0% | 5.9/5/18 | 0/0/0 | 0 / 0 / 0 | 3/20 = 15.0% (5.2%~36.0%) | 등급 D(개발 묶음 값, 대표 숫자 아님) |

| 모드 | 자릿수만 다른 WRONG_VALUE(민감도) | 발동 신호별 주장 요건 미충족으로 생긴 INVALID | 인프라 실패 재실행(건수 / 재실행 전 기록으로 계산한 보고서 단위 오류율) |
|---|---|---|---|
| freeform | 0 | 집계하지 않음(원인 분류 코드 미정, 단위 L3) | 2 / 7/20 = 35.0% (18.1%~56.7%) |
| full | 0 | 집계하지 않음(원인 분류 코드 미정, 단위 L3) | 1 / 4/20 = 20.0% (8.1%~41.6%) |

- 차이 판정(1차, B4 비겹침 규칙): 구간이 겹쳐서 "차이를 확인하지 못했다"(차이가 없다는 뜻이 아님)
- 보조 분석(사전 등록): 짝 비교 둘 다 오류 1 / freeform만 오류 4 / full만 오류 2 / 둘 다 무오류 13, Newcombe 짝 차이 95% 구간(freeform − full) -14.2pp~+33.2pp, McNemar 정확 검정 p 0.688
- 결과 집합 분포(source=claim): freeform CORRECT 89, WRONG_VALUE 3, WRONG_DIRECTION 0, WRONG_UNIT 0, WRONG_REFERENT 1, UNSUPPORTED 0; full CORRECT 100, WRONG_VALUE 0, WRONG_DIRECTION 0, WRONG_UNIT 0, WRONG_REFERENT 0, UNSUPPORTED 0
- 결과 집합 분포(source=prose): freeform CORRECT 67, UNBACKED_PROSE 1; full CORRECT 112, UNBACKED_PROSE 0
- 극값·순위 표현 건수(참고, 채점 제외): freeform 0 / full 0
- 범위 밖: 숫자·증감이 없는 정성 서술과 극값·순위 말의 의미 정확성

## 4. 참고 지표

- 스킬 호출 성공률(NemoClaw 경로, 정확도 지표에는 영향을 주지 않는다): 미기재(실행 조건 입력 파일에 없음)
- 한국어 품질(참고, 자동 검사): freeform 한글 비율 83.6%, 금지 표현 0건, 필수 항목 누락 16건; full 한글 비율 91.4%, 금지 표현 0건, 필수 항목 누락 15건. 표본 점검: 미기재(실행 조건 입력 파일에 없음)
- NAT 프로파일 요약(참고): {"runs": 43, "runs_with_profile": 43, "profile_files_complete": 43, "runs_with_nat_trace": 43, "runs_workflow_end": 43, "by_mode": {"full": {"runs": 21, "runs_with_profile": 21, "execution_status": {"COMPLETED": 17, "FAILED": 1, "TIMEOUT": 0, "INVALID": 3, "BUDGET_EXCEEDED": 0}, "model_requests": {"median": 5, "min": 3, "max": 6}, "tokens": {"median": 43881, "min": 19691, "max": 84247}, "wall_ms": {"median": 20148, "min": 4460, "max": 34653}, "nat_llm_calls": {"median": 5, "min": 3, "max": 8}, "nat_llm_ms": {"median": 14459, "min": 4431, "max": 33702}, "nat_tokens": {"median": 44093, "min": 6619, "max": 84247}, "nat_tool_calls": {"median": 6, "min": 4, "max": 9}, "nat_workflow_ms": {"median": 20149, "min": 4460, "max": 46989}, "stage_spans": {"basic": 21, "critic": 19, "revision": 16, "final": 16, "other": 0}}, "freeform": {"runs": 22, "runs_with_profile": 22, "execution_status": {"COMPLETED": 18, "FAILED": 4, "TIMEOUT": 0, "INVALID": 0, "BUDGET_EXCEEDED": 0}, "model_requests": {"median": 4, "min": 3, "max": 6}, "tokens": {"median": 48130, "min": 31745, "max": 85677}, "wall_ms": {"median": 23261, "min": 11182, "max": 45999}, "nat_llm_calls": {"median": 6, "min": 3, "max": 10}, "nat_llm_ms": {"median": 18208, "min": 11133, "max": 74325}, "nat_tokens": {"median": 47366.5, "min": 15127, "max": 85677}, "nat_tool_calls": {"median": 6, "min": 4, "max": 9}, "nat_workflow_ms": {"median": 27481.5, "min": 11183, "max": 84396}, "stage_spans": {"basic": 22, "critic": 19, "revision": 18, "final": 15, "other": 0}}}}

## 5. 재현 명령

- 채점 대상 실행: tradesentry evaluate --snapshot kcs_202201_202412_v2 --policy policy_v1
- 정답 대조 채점: python -m eval.scorer --run outputs/evaluate-260925234445
- 스냅샷 검증: tradesentry snapshot-verify --snapshot kcs_202201_202412_v2
- 채점기 입력(보고서 원문) 위치: artifacts/eval/score-260926003407/{run_id}/(증거 복사 때 함께 복사. 봉인 묶음은 금지 해제 조건 뒤). 보고서 파일 바이트 sha256:
  - run_case-260925234445: dd576afa45be22251d03de88f4d01d64438e108d597b8730afdc5a3ed55079a3
  - run_case-260925234545: 166ad4fe2a38ed0b55ba4f8cfbe89d207fe2abbd9a5f90331fa2745aab26f255
  - run_case-260925234804: 9a3b92363a49428686e8d803bd67804fc87643a2e69339c8e34465b4ec2f024d
  - run_case-260925234904: c80a570196c857280a51dcd57bd236e9919a8f36c9d3255f68524b0dc1280aa3
  - run_case-260925235016: 2698349803c71f45df81569de07366b70fa3a78483858d152647ada87230e0ee
  - run_case-260925235116: 363360fdb5122221fb7fe68368b0864c1c76a2eea0c9f6970f41d61ae39a7d5e
  - run_case-260925235320: b200b386d6c93aa913b22f425108e9edb530b5183f7ad349d481386e5048d7ac
  - run_case-260925235423: 96542a07f06b728cbb79f801f9bfdea9a0e5c3d481424c5b4f5055fbc409e425
  - run_case-260925235523: a14382a269b2a00862b0082d371d4f0d9e2cbbfc3ec004bc5f985c4bffd0d26e
  - run_case-260925235706: 06a6f0f7b0b459daf71a303e4131d4c8a90de5bd152110eca4550c5ddfbc35cd
  - run_case-260925235806: 3feef5c0c998ca458552a41c56c4992fb2fc54bdd421951145be7a269c7a5ae0
  - run_case-260925235906: 410dfe4ac7880c62cda70482461baaf511ae00ac598501a3cc9fcb300d0f0bd5
  - run_case-260926000006: 4c2bf25a53ce8a2b329f45495b260ef4b84436181b3a3c7c84c1c121d8f4a5df
  - run_case-260926000218: 0fd2f3b22884343352210e8abdbd76009648d1991d8bf7f7268c86fb587d93b4
  - run_case-260926000345: 0d3895c732bd44ea7a959f8dda06ef4bc180f91503563378e404764a377fab80
  - run_case-260926000445: 200091b9f46dd9e4726f64765e296297c0fec957fb7ab2a0d81cc2ce01e08aba
  - run_case-260926000626: 69fe09fdfb20cb325a163ae03939e2d386c1b472b26cce9da11ea31c481ccfc9
  - run_case-260926001113: a2eb3b5302739240946aee408e7c882a925df56aaf10eb0cdd9f4bac755d9b07
  - run_case-260926001313: cb4e08874db8a11b9b68a6a3cbe03ab2d6bc7370b8d5e34c785a4c693c0ddedd
  - run_case-260926001413: 12caf66061814f216101326bafd95c8792f984f0c35dfe358a932a7222a56268
  - run_case-260926001513: 6a32269cfb575b7936c5f8caace6b4a2712be56823bc2096717bf5c013284374
  - run_case-260926001613: dc795616250d362806ef8d36cbbce9cd063224bd025d13f0c8db3b767ac42c07
  - run_case-260926001713: 4a94eb3fd24ee50b0fd101e3ab279f36867b8a121bdfc57e998274f9ecad906c
  - run_case-260926001947: f3565df3aa3b406338bf7b57072ac02c902025761da91a146eb1fcf34d0ca5d3
  - run_case-260926002047: 3865f72cc1a734208d5adc72d2bb578cbfe0c4336ad1f8f4aa92e6baa13a864f
  - run_case-260926002147: 0ebadcba354e235e0811a817347047742bf66a8acc858a3bca3ac9e2f08fc3a1
  - run_case-260926002327: 5bf818d656becca2a549bafecd7ff606348f4cb2a6bf6b6267afea5ace561682
  - run_case-260926002534: 037b6efbe1590f67cf9c5fbb654bfa6f9018c26f308de0ce8e8173c58acd4288
  - run_case-260926002634: 0d3fac5b10e795de1c9906f3e71f9a2038531de70fd412d72c2478192eb27c8a
  - run_case-260926002734: f2dd2ef38b8ebe3f68670e4d8162814c8f927321d3939156514cdb88098b814f
  - run_case-260926002834: 095f7457a19dc4cf671ef1ce72f65613bd78841b45f26e1288876ba228588f2a
  - run_case-260926002934: 756ba8d51aed7a8c79fb01163e003a6829d7637295ed23c9ffeead877dc21eae
  - run_case-260926003109: f93af2acef3ff244365484f70787d79c0c16737fe4c92764cca45ef445c20d09
  - run_case-260926003239: 597d8f8ff39d3ad58a83fc2ca1aefc63f21246fe89adfd7070013c678bed22f2
  - run_case-260926003339: 74a3b213b94355558f48f8f38511daecda0367c773b6eee2801ba7e5dec7fe14

## 6. 한계

- 봉인의 한계(룰북 B6): 봉인 폴더 위치는 비밀이 아니고, 같은 OS 사용자로 도는 에이전트의 열람을 기술적으로 막지 못하며, 해시는 변조를 드러낼 뿐 열람을 막지 않는다
- 산문 패턴의 한계(룰북 B3-2): 문장 단위로 주어를 맞추지 않아 우연히 맞는 표현을 놓치고, 배수 표현은 r_U claim만 뒷받침한다
- 표본 크기와 신뢰구간 폭: 사례 20건. 한 시계열에서 여러 경보가 뽑히면 독립 가정이 약해진다
- 숫자·증감이 없는 극값·순위 표현은 채점하지 않으므로 틀려도 잡히지 않는다
- 채점기 입력(보고서 원문)은 증거 복사 전까지 outputs/에만 있어 저장소만으로 재채점할 수 없다
- 승격 규칙(CONFIRMED_NO_TRADE)은 policy_v1 승인 전이라 채점기가 따로 적용하지 않고 스냅샷 표시를 썼다(F1 전 보완)
