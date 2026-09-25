# 평가 결과 요약 — evaluate-260925212246

채점기(eval/scorer)가 쓴 요약이다. 에이전트는 이 파일을 고쳐 쓰지 않는다(자료 계약 §10.3 N8). 등급 표기는 룰북 A5·B7을 따른다.

## 0. 실행 조건

- 룰북: RB-1, 동결 커밋 없음(RB-1 동결 전), 동결 뒤 변경 미기재(실행 조건 입력 파일에 없음)
- snapshot_id kcs_202201_202412_v2, 스냅샷 정규화 해시(normalized_sha256) 미기재(실행 조건 입력 파일에 없음), 대조 미기재(실행 조건 입력 파일에 없음)
- policy_version policy_v1, grouping_version g0(사유: 미기재(실행 조건 입력 파일에 없음))
- code_version 3f1832af37906ffa79c2783563967ece86a56c5f, 채점기 커밋 미기재(실행 조건 입력 파일에 없음), 산문 패턴 목록 커밋 미기재(실행 조건 입력 파일에 없음)(채점기가 계산한 패턴 목록 지문 sha256 9184cbe2695231a2b4388c1418c0fa116e9bdff07acfe634bd30a61448017595)
- 실행 기간(KST) 2026-09-25T21:22:46+09:00 ~ 2026-09-25T22:11:48+09:00, 동시성 1, 순서 seed dev-order-v1
- 한도(룰북 B2와 대조한 실행 설정): 도구 호출 시도 8, 재조사 1, 모델 요청 10, 사례당 wall time 300초, 누적 토큰 128000
- 샌드박스 이름 ts-scored, 커밋한 라이브 정책 조회 본문(정책 YAML) sha256 미기재(실행 조건 입력 파일에 없음), 대조한 시험표 실행 폴더 이름 미기재(실행 조건 입력 파일에 없음), `configs/openshell/policy.yaml` sha256 dc2e8c3a7707e78cf86c1536ed5535fcf99e592376a2009d190d5564e87785a8
- 봉인 해시 재대조 해당 없음(봉인 묶음 아님)
- 채점 전 확인(평가 스킬 ②): 1 예정 실행의 최종 상태 확정 참: 예정 실행 40건 가운데 줄 없는 조합 0건, 인프라 실패 재실행(룰북 B5) 대상 3건·재실행 3건(채점기 계산: 미실행 0건), 2 버전 키 일치 미기재(실행 조건 입력 파일에 없음), 5 모드별 사례 집합 일치 미기재(실행 조건 입력 파일에 없음)(채점기 계산: 참), 순서 seed·동시성 적용 참: 순서 seed dev-order-v1, 동시성 1, 속도 조절(모델 실행 사이 최소 60초, 분당 토큰 50000, HTTP 429 뒤 120초), 쉰 시간 합 1352초, 429 뒤 더 쉰 횟수 0, 동시성을 올렸다면 근거 결정 기록 미기재(실행 조건 입력 파일에 없음)
- 사전 점검 결과 미기재(실행 조건 입력 파일에 없음)
- 계약 버전 schema_version 2, 자료 묶음 real_dev, 평가 묶음 실행 evaluate-260925212246, 채점 실행 score-260925221148
- 채점기가 읽은 스냅샷 파일 data/snapshots/kcs_202201_202412_v2/snapshot_build.sqlite, 바이트 sha256 3a29db9227cc017771daf917ee5de907c7f46d6f41dc122782329d84faf12d7d
- 계획: 사례 20건 × 모드 freeform, full = 예정 실행 40건, 결과 줄 43줄
- 채점 대상 run_id 목록: run_case-260925212246, run_case-260925212346, run_case-260925212446, run_case-260925212546, run_case-260925212647, run_case-260925212755, run_case-260925212935, run_case-260925213035, run_case-260925213135, run_case-260925213250, run_case-260925213352, run_case-260925213452, run_case-260925213552, run_case-260925213705, run_case-260925213807, run_case-260925213946, run_case-260925214049, run_case-260925214157, run_case-260925214304, run_case-260925214416, run_case-260925214526, run_case-260925214626, run_case-260925214749, run_case-260925214849, run_case-260925214949, run_case-260925215049, run_case-260925215149, run_case-260925215249, run_case-260925215349, run_case-260925215449, run_case-260925215549, run_case-260925215738, run_case-260925215838, run_case-260925215943, run_case-260925220043, run_case-260925220242, run_case-260925220342, run_case-260925220451, run_case-260925220559, run_case-260925220701, run_case-260925220827, run_case-260925220927, run_case-260925221056
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
| freeform | 20 | 18 | FAILED 2, TIMEOUT 0, INVALID 0, BUDGET_EXCEEDED 0, 미실행 0 | 7/20 = 35.0% (18.1%~56.7%) | 5/82 = 6.1% | 4.6/4.5/9 | 0.1/0/1 | 1 / 1 / 0 | 6/20 = 30.0% (14.5%~51.9%) | 등급 D(개발 묶음 값, 대표 숫자 아님) |
| full | 20 | 16 | FAILED 2, TIMEOUT 0, INVALID 2, BUDGET_EXCEEDED 0, 미실행 0 | 4/20 = 20.0% (8.1%~41.6%) | 0/120 = 0.0% | 7.5/6/34 | 0/0/0 | 0 / 0 / 0 | 4/20 = 20.0% (8.1%~41.6%) | 등급 D(개발 묶음 값, 대표 숫자 아님) |

| 모드 | 자릿수만 다른 WRONG_VALUE(민감도) | 발동 신호별 주장 요건 미충족으로 생긴 INVALID | 인프라 실패 재실행(건수 / 재실행 전 기록으로 계산한 보고서 단위 오류율) |
|---|---|---|---|
| freeform | 0 | 집계하지 않음(원인 분류 코드 미정, 단위 L3) | 2 / 8/20 = 40.0% (21.9%~61.3%) |
| full | 0 | 집계하지 않음(원인 분류 코드 미정, 단위 L3) | 1 / 5/20 = 25.0% (11.2%~46.9%) |

- 차이 판정(1차, B4 비겹침 규칙): 구간이 겹쳐서 "차이를 확인하지 못했다"(차이가 없다는 뜻이 아님)
- 보조 분석(사전 등록): 짝 비교 둘 다 오류 2 / freeform만 오류 5 / full만 오류 2 / 둘 다 무오류 11, Newcombe 짝 차이 95% 구간(freeform − full) -10.2pp~+38.1pp, McNemar 정확 검정 p 0.453
- 결과 집합 분포(source=claim): freeform CORRECT 77, WRONG_VALUE 3, WRONG_DIRECTION 0, WRONG_UNIT 0, WRONG_REFERENT 0, UNSUPPORTED 2; full CORRECT 120, WRONG_VALUE 0, WRONG_DIRECTION 0, WRONG_UNIT 0, WRONG_REFERENT 0, UNSUPPORTED 0
- 결과 집합 분포(source=prose): freeform CORRECT 74, UNBACKED_PROSE 2; full CORRECT 135, UNBACKED_PROSE 0
- 극값·순위 표현 건수(참고, 채점 제외): freeform 0 / full 0
- 범위 밖: 숫자·증감이 없는 정성 서술과 극값·순위 말의 의미 정확성

## 4. 참고 지표

- 스킬 호출 성공률(NemoClaw 경로, 정확도 지표에는 영향을 주지 않는다): 미기재(실행 조건 입력 파일에 없음)
- 한국어 품질(참고, 자동 검사): freeform 한글 비율 86.5%, 금지 표현 0건, 필수 항목 누락 13건; full 한글 비율 91.7%, 금지 표현 0건, 필수 항목 누락 14건. 표본 점검: 미기재(실행 조건 입력 파일에 없음)
- NAT 프로파일 요약(참고): {"runs": 43, "runs_with_profile": 43, "profile_files_complete": 43, "runs_with_nat_trace": 43, "runs_workflow_end": 43, "by_mode": {"full": {"runs": 21, "runs_with_profile": 21, "execution_status": {"COMPLETED": 16, "FAILED": 3, "TIMEOUT": 0, "INVALID": 2, "BUDGET_EXCEEDED": 0}, "model_requests": {"median": 5, "min": 3, "max": 6}, "tokens": {"median": 45400.5, "min": 23527, "max": 82466}, "wall_ms": {"median": 18993, "min": 4138, "max": 117293}, "nat_llm_calls": {"median": 5, "min": 3, "max": 14}, "nat_llm_ms": {"median": 13360, "min": 4089, "max": 66855}, "nat_tokens": {"median": 44709, "min": 12830, "max": 82466}, "nat_tool_calls": {"median": 7, "min": 4, "max": 9}, "nat_workflow_ms": {"median": 24957, "min": 4138, "max": 117294}, "stage_spans": {"basic": 21, "critic": 18, "revision": 15, "final": 13, "other": 0}}, "freeform": {"runs": 22, "runs_with_profile": 22, "execution_status": {"COMPLETED": 18, "FAILED": 4, "TIMEOUT": 0, "INVALID": 0, "BUDGET_EXCEEDED": 0}, "model_requests": {"median": 4, "min": 3, "max": 6}, "tokens": {"median": 44897.5, "min": 23051, "max": 83232}, "wall_ms": {"median": 25146.5, "min": 5697, "max": 108018}, "nat_llm_calls": {"median": 6.5, "min": 2, "max": 12}, "nat_llm_ms": {"median": 15503.5, "min": 3651, "max": 72936}, "nat_tokens": {"median": 38496.5, "min": 6788, "max": 83232}, "nat_tool_calls": {"median": 6, "min": 3, "max": 9}, "nat_workflow_ms": {"median": 28919.5, "min": 5697, "max": 108019}, "stage_spans": {"basic": 22, "critic": 17, "revision": 15, "final": 14, "other": 0}}}}

## 5. 재현 명령

- 채점 대상 실행: tradesentry evaluate --snapshot kcs_202201_202412_v2 --policy policy_v1
- 정답 대조 채점: python -m eval.scorer --run outputs/evaluate-260925212246
- 스냅샷 검증: tradesentry snapshot-verify --snapshot kcs_202201_202412_v2
- 채점기 입력(보고서 원문) 위치: artifacts/eval/score-260925221148/{run_id}/(증거 복사 때 함께 복사. 봉인 묶음은 금지 해제 조건 뒤). 보고서 파일 바이트 sha256:
  - run_case-260925212346: 08342123a81ed55d7ff6f04e9fb3c91cef471acd57d170ac07856b062030ea31
  - run_case-260925212446: 5e34b5958117a8119b6643769ae80fe8d28c1c8e800403296788a5397c27e2a7
  - run_case-260925212755: fcf7faad115dc28578c5f95be3ef6131869ffd9cf5eb9bc782acef8da997b656
  - run_case-260925212935: 6ce21e3f297e57fea491a6342f8826d6d80545b034c57762600029da89a61441
  - run_case-260925213135: 8e1feac82627869a16d7aa6cf004a7af5a46cd622cf561ac5b855782ab0a84b5
  - run_case-260925213250: 847b841ae50f3a2a95a38a451634a9e427b0e77ebf2dd79202fe359807f4caab
  - run_case-260925213352: e41addd6cf70b4e3f4c664deaeb921f4c00c596ed66193a0f63f4ef51afd0f17
  - run_case-260925213552: 8cd8a0572e35b8b50e81ba97e8078f9e2d1348c7753efe7b132389063b2636f3
  - run_case-260925213807: ec1988bfded5efab5af37979e7389da80827c49cb348e14181b9461473965324
  - run_case-260925213946: f1c94c4e549d1fd4db5c10feaae5611e69fb64ae8b31309fe95a6317a5626874
  - run_case-260925214049: 49042e17991cddb41fcc922bbf262630cb252b010dfc8396e5e552b2b25e74a1
  - run_case-260925214157: 20b75e77cf042f1f3216c455d9e6155c94e2e9009a877b17f36b64f3ddcbc004
  - run_case-260925214304: 7260877ea76ce1c0a074d95cbe32e11b0fb73d26a7237b28e497937c5d2d7c5b
  - run_case-260925214416: 1a6f879e797be89c2e76137cd7af12504d762ef9901a075b4391c1cd3181f629
  - run_case-260925214526: 257b9eaf7c91e93643c7db7dab5c2c44485c2073f06c8fa6628fbbc7521b2196
  - run_case-260925214626: 9a50671cb91cda20093b29444b29e6ee5fab2a5fb89f88935e2f1819f2cf33d6
  - run_case-260925214749: 87dd254f40dc40e5b40d98dcedb87617350d95f0c7c0d9d1af1ff88874a68b88
  - run_case-260925214849: 10a12071c1149e508466e1b1cbe0e7f479b7ed8e1a5efeb8188ad03f6454fe60
  - run_case-260925214949: 701f2de5285365ee4c7925b28a197f933cc672b81c661cec28b5106264e05d50
  - run_case-260925215049: bcb8b3b2e72829e3a9f004051bf1b0b611f3ad04578724d8c93e5798d3ea9359
  - run_case-260925215149: 69189fc86faffa80835176aef3d8b9e8f6fb008db8d9bb57344b87e3341e87e7
  - run_case-260925215249: f36b499330e9031d0c7f5450b9fee6d3d7d0837e3fda39316b8487855dc93840
  - run_case-260925215349: f8373517d5259c4353a6254ea816962a8f53d2a32cced51b7fd39141d8e90b2a
  - run_case-260925215449: 0575e005a7bd2e7d916609c6b96eaea1ea2214a451d4ef3bc647a99ebd9bb19c
  - run_case-260925215549: 65acb9bbbd124cb115b0459edb7e94f3e58c0979aad26035536a5d4f7a18bb27
  - run_case-260925215738: 666b953ecad9beca90865f57111081af7d8f56f9e18d9db0603cd28005609a0f
  - run_case-260925215838: a75cfef19bb81d77599b0b1d5245546f2479eeb808b8824c32a596c418a8277f
  - run_case-260925215943: 39c200633edff7865b6b90c84330993c0947c7483ccdd6917b175a80cbd3da0b
  - run_case-260925220043: 8a8bf69a5af62141c9780529e2329f3e095ead78ec5fa78ee42f34b9bc93533d
  - run_case-260925220242: 9244dd6732c39be8d6683d3cece30d676f901e6b7064a4a297643ab2b4491cd4
  - run_case-260925220342: 6c22e17d17f978f8e0034fafc3f99ebeb0d2c190611137c8b212c5796e4b5461
  - run_case-260925220827: 78bd4ea2cf148d6e87f98dd7eb46f5cb457495a3faa0c236914e26e94644d147
  - run_case-260925220927: 86b3b13943b554146286424d5379c89c5a5cd4afdd79fba3900802dfe261c4db
  - run_case-260925221056: d5b6641b9f72a69d87c0dc96bd7af19394feb0e4610fe50f21dc3c502bed4031

## 6. 한계

- 봉인의 한계(룰북 B6): 봉인 폴더 위치는 비밀이 아니고, 같은 OS 사용자로 도는 에이전트의 열람을 기술적으로 막지 못하며, 해시는 변조를 드러낼 뿐 열람을 막지 않는다
- 산문 패턴의 한계(룰북 B3-2): 문장 단위로 주어를 맞추지 않아 우연히 맞는 표현을 놓치고, 배수 표현은 r_U claim만 뒷받침한다
- 표본 크기와 신뢰구간 폭: 사례 20건. 한 시계열에서 여러 경보가 뽑히면 독립 가정이 약해진다
- 숫자·증감이 없는 극값·순위 표현은 채점하지 않으므로 틀려도 잡히지 않는다
- 채점기 입력(보고서 원문)은 증거 복사 전까지 outputs/에만 있어 저장소만으로 재채점할 수 없다
- 승격 규칙(CONFIRMED_NO_TRADE)은 policy_v1 승인 전이라 채점기가 따로 적용하지 않고 스냅샷 표시를 썼다(F1 전 보완)
