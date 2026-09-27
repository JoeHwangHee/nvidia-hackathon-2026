# HSGate 근거자료 및 설계 반영사항

> 기준일: 2026-09-23
> Claude 검토 + Codex 검토(HSGATE_DATA_VALIDITY.md) 교차 반영

---

## 1. 근거자료 링크

### 1.1 핵심 데이터
| 자료 | 링크 | 용도 | 비고 |
|---|---|---|---|
| CLIP 품목분류 국내사례 | https://unipass.customs.go.kr/clip/prlstclsfsrch/openULS0203042S.do | 검색 코퍼스, 평가 정답 | 조회 화면. 참조번호·결정세번·시행일자·검색어로 조회 |
| CLIP 목록 JSON | https://unipass.customs.go.kr/clip/prlstclsfsrch/retrieveDmstPrlstClsfCaseLst2.do | 수집 | Codex 제공, 미검증. 공식 공개 API가 아닌 화면 내부 엔드포인트로 보임 |
| CLIP 상세 JSON | https://unipass.customs.go.kr/clip/prlstclsfsrch/retrieveDmstPrlstClsfCaseDtl.do | 수집 | 위와 동일 |
| 관세청 HS부호 2026 | https://www.data.go.kr/data/15049722/fileData.do | 현행 세번 검증(V8) | 한글·영문 품목명, 성질·단위 코드 |
| HS부호 단위별 품목명 | https://www.data.go.kr/data/15130660/fileData.do | 호·소호 용어 사전, 마스킹 | 2·4·6·8·10단위 |
| 관세청 표준품명 | https://www.data.go.kr/data/15049721/fileData.do | V4 필수 속성 목록 | 표준품명, 필수규격, 규격값 |
| 관세율표 | https://www.data.go.kr/data/15051179/fileData.do | 데모 세액 차이 계산 | 품목번호별 관세율 |
| 관세청 법령해석 본문 API | https://www.data.go.kr/data/15140316/openapi.do | 보조 근거 | 공공누리 제1유형, 개발단계 자동승인 |

### 1.2 제도·법령
| 자료 | 링크 | 용도 |
|---|---|---|
| 품목분류 사전심사 제도 | https://www.customs.go.kr/cvnci/cm/cntnts/cntntsView.do?mi=3217&cntntsId=948 | 사례의 성격 이해 |
| 품목분류 확인방법 (CLIP) | https://unipass.customs.go.kr/clip/ctensrch/openULS0404009Q.do | 사전심사 효력·절차 |
| 관세법 제86조 | https://www.law.go.kr/법령/관세법/제86조 | 사전심사 효력 |
| 관세청 저작권 정책 | https://www.customs.go.kr/cvnci/cm/cntnts/cntntsView.do?mi=7612&cntntsId=2610 | 재배포·학습 이용 판단 |
| 관세청 공공데이터 제공신청 | https://www.customs.go.kr/kcs/cm/cntnts/cntntsView.do?mi=10062&cntntsId=2836 | 사례 전량 정식 요청 경로 |

### 1.3 비교 기준·경쟁
| 자료 | 링크 | 용도 |
|---|---|---|
| 관세청 빅데이터포털 국내 유사사례 | https://bigdata.customs.go.kr/web/anaySrvc/selectSmlrPrlstClsfCaseDmstList.do | Retriever 베이스라인 비교 |
| 관세청 빅데이터포털 국외 유사사례 | https://bigdata.customs.go.kr/web/anaySrvc/selectSmlrPrlstClsfCaseOvrsList.do | 동일 |
| 관세청 AI 품목분류 정확도 약 80% 보도 | https://www.taxwatch.co.kr/article/tax/2025/07/30/0002 | 발표 시 비교 기준 |
| 커스텀메이트 출시 보도 (2026-09) | https://wowtale.net/2026/09/21/265091/ | 경쟁 서비스, 차별화 근거 |

---

## 2. 데이터 사용 원칙

1. **CLIP은 RAG 검색 근거와 평가 정답으로만 사용한다. 파인튜닝하지 않는다.**
2. **원문 데이터는 저장소에 커밋하지 않는다.** 수집 스크립트와 사례 ID·URL·해시 매니페스트만 공개한다.
3. **수집은 정식 경로를 우선한다.** 공공데이터 제공신청(customsdata@korea.kr)을 해커톤 착수 즉시 보내고, 회신 전까지는 로컬 캐시를 최소화한다.
4. **실제 UNI-PASS와 실제 자격증명은 다루지 않는다.** Mock 게이트웨이만 사용한다.

---

## 3. 설계 반영사항

### 3.1 검증기 추가·수정
| ID | 내용 | 근거 |
|---|---|---|
| V4 수정 | 류별 필수 속성 목록을 표준품명 필수규격에서 자동 생성 | 표준품명 데이터 |
| **V8 신규** | 사례 유효성: 인용 사례 세번이 2026 HS부호에 존재하는지, 변경고시로 폐기되지 않았는지 확인 | HS 개정, 관세법 제87조 변경 |
| **V9 신규** | 근거 등급: 동일 물품 사례 / 유사 물품 사례 구분. 유사 사례만 있으면 확신도 하향 | 규격 불일치 시 고시 적용 곤란 판단례 |
| F7 신규 | V8 실패 시 해당 사례 제외 후 재검색 | V8 |

### 3.2 데이터 전처리
- `RRDC_NO`의 실제 고유성을 먼저 검증한다. 참조번호 재사용 이슈가 있으므로, 고유하지 않으면 `RRDC_NO + ENFR_DT` 복합키를 쓴다.
- 결정 세번 정규화: 공란, `HSK`, `ㅇ` 같은 표기 노이즈 제거. 복수 세번 사례는 평가에서 제외하거나 별도 집계.
- 입력 마스킹: `CMDT_DESC`에 포함된 호·소호 용어를 HS 품목명 사전으로 탐지해 마스킹한 뒤 인보이스 형식으로 변환.
- HS 버전 정리: 현행 체계에 없는 세번은 매핑하거나 평가에서 제외.

### 3.3 평가 분할
- **시간 기준 분할**: 과거 사례 = 검색 코퍼스, 최근 사례 = held-out.
- **그룹 분할**: 품명 첫 토큰 등으로 유사 품목을 묶어 같은 그룹이 코퍼스와 held-out에 동시에 들어가지 않게 한다 (품명 첫 토큰 중복 약 24%).
- 특정 류 편중을 확인하고 류별 결과를 따로 보고한다.

### 3.4 주장 수준
| 주장 | 가능 여부 |
|---|---|
| HS 6단위 top-1/top-3 정확도 | 헤드라인 지표로 사용 |
| HS 10단위 정확도 | 최근 사례·현행 세번 한정 보조 지표 |
| 근거 인용 정합성 | 규칙 판정 가능한 부분(V1, V2, V8)만 자동 지표화 |
| 루프 개선폭 | B3 대비로 제시 |
| 인젝션 차단률 | 자체 제작 fixture임을 명시하고 시스템 안전성 시험으로 제시 |
| 실제 신고 정확도, 비용 절감, 추징 감소 | **주장하지 않음** |
| 관세사 대체, 신고 자동 결정 | **주장하지 않음** |

### 3.5 포지셔닝
- 경쟁 서비스(사례 기반 후보 + 세번 존재 확인 + 관세사 확정)가 이미 존재함을 발표에서 먼저 인정한다.
- HSGate의 차별점은 세 가지로 한정한다.
  1. 실패 유형별로 행동을 바꾸는 자기수정 루프
  2. 사례의 유효성·동일성까지 따지는 근거 검증
  3. 인젝션에 강한 전송 게이트

---

## 4. 착수 첫날 확인 목록
- [ ] 공공데이터 제공신청 발송
- [ ] CLIP JSON 엔드포인트 응답 필드·페이징·호출 제한 확인
- [ ] 관세청 저작권 정책 원문 확인, 필요 시 담당자 문의
- [ ] 누적 건수·연도별 분포 재집계 (수치 간 불일치 여부 확인)
- [ ] `RRDC_NO` 고유성 검증
- [ ] 대상 류 확정 (사례 수 + 최근성 + 류 편중 기준)
- [ ] 법령해석 API 활용신청
