# 사용자 결정: 저장소 라이선스 Apache License 2.0

저장소는 2026-09-26(토) 22:53부터 공개 상태이고(결정 기록 `docs/tracking/decisions/20260926-2253-user-decision-public-switch.md`), 라이선스는 그 기록과 2050 기록(`docs/tracking/decisions/20260926-2050-user-decision-public-repo-procedure-ops-plan.md` "남은 것" ②)에서 사용자 결정 대기로 남아 있었다. 이번 결정으로 닫는다.

용어

- 라이선스(license): 저작권자가 다른 사람에게 코드·문서를 쓰고 고치고 다시 배포할 권리를 어떤 조건으로 주는지 적은 조건. 저장소에 라이선스 파일이 없으면 공개돼 있어도 GitHub 안 열람·포크 말고는 권리를 주지 않는다.
- Apache License 2.0(SPDX(소프트웨어 라이선스 표준 식별자) `Apache-2.0`): 허용형(permissive, 고지만 지키면 상업적 이용·수정·재배포를 허용하는 방식) 오픈소스 라이선스. 기여자가 자기 기여에 걸린 특허의 사용 권리도 함께 주는 특허 조항이 있다.
- 거버넌스 카드: 공식 스킬 `skill-card-generator`가 스킬 디렉터리에서 만드는, 스킬의 능력 범위를 밝히는 카드(스킬 사전 3.5절, `docs/eval/SKILL_DICTIONARY.md`).

| 항목 | 내용 |
|---|---|
| 날짜 | 결정 2026-09-27(일) 02:1x(채팅 "라이선스는 권장대로할게". 권장안은 오케스트레이터가 앞서 제시한 Apache-2.0). 적용 2026-09-27(일) 02:2x~02:3x KST |
| 제목 | 이 저장소의 라이선스는 Apache License 2.0이다 |
| 결정 | ① 라이선스는 Apache License 2.0(`Apache-2.0`)이다. 전문은 저장소 루트 `LICENSE`다. ② 적용 범위는 이 프로젝트가 만든 코드와 문서다. ③ 저장소에 든 제3자 자료(관세청 API 조회 코드표·국가코드, 관세청 HS부호 자료와 품목표, BACI 발췌)는 Apache-2.0이 아니라 각 출처의 이용 조건을 따른다(README 7절 "출처와 이용 조건"). ④ `NOTICE` 파일은 두지 않는다 |
| 이유 | 허용형이면서 특허 조항이 있어 공개 저장소를 보는 사람에게 재사용·수정·재배포 권리를 분명히 준다. NVIDIA 공식 스킬 생태계(설치한 `skill-card-generator` 스크립트의 SPDX 표기가 `Apache-2.0`)와 맞는다 `[사실: 설치본 scripts/render_card.py 머리 주석]` `[추론: 생태계 정합]` |
| 결정 주체 | 사용자(2026-09-27(일) 02:1x). 적용은 문서 작업자(PR LIC1) |
| 공용 약속 여부 | 아니다. 자료 계약의 값·상태값·경로·명령은 바뀌지 않는다. 제출서 주장 문구도 바뀌지 않는다 |
| 영향 | `LICENSE`(새 파일), 거버넌스 카드 3개(License/Terms of Use 칸과 한국어 부록의 라이선스 부분), README(8절 저장소 구조, 11절 "라이선스", English summary), 스킬 사전 3.5절 실행 기록·형식·"남은 확인" ②와 1절 표 `skill-card-generator` 행, 개발 플랜 14.2절 "Agent Skills 배포" 행, 로드맵 P1·P2 행과 사용자 확인 목록, status, 제출 폼 최종본 "제출 절차"(6단계 라이선스 문장, 진행 줄), 결정 기록 색인 |
| 관련 PR | 이 기록을 담은 문서 PR(LIC1). 앞선 PR #107(결정 2050)·#111(결정 2253) |

## 한 일

- `LICENSE`: GitHub 라이선스 API(`gh api licenses/apache-2.0`, `spdx_id` `Apache-2.0`)의 `body`를 글자 그대로 넣었다. 부록(APPENDIX)의 자리표시 `[yyyy]`·`[name of copyright owner]`도 그대로 두었다 `[사실: 파일 대조]`.
- 거버넌스 카드 3개 재렌더(스킬 사전 3.5절 실행 기록 8~12행):
  - `scripts/discover_assets.py skills/<이름>`(3개, 종료 코드 0)의 Repo-root signals에 `license_identifier: Apache License  (from LICENSE)`가 잡혔다.
  - 지난 context JSON이 남아 있지 않아, 각 카드 생성기 부분의 값을 그대로 옮기고 `license_identifier: "Apache-2.0"`, `license_verify: false`(스타일 가이드: 식별자를 LICENSE 파일에서 가져왔을 때만 `false`) 두 값만 바꿔 다시 만들었다. 이용 자세 문장과 소유자 항목은 그대로다.
  - 임시 경로에 먼저 렌더해 옛 카드의 생성기 부분과 diff를 떴고, 세 카드 모두 차이는 `### License/Terms of Use: <br>` 아래 `Apache-2.0 <br>` 한 줄 추가뿐이었다.
  - 카드 경로로 렌더하고 한국어 부록을 다시 붙인 뒤 라이선스 부분만 고쳤다. `scripts/validate_submission.py`는 세 카드 모두 종료 코드 0이다.
- README 11절 "라이선스"(7절에 적힌 제3자 자료와 조건만 짧게 옮김), 8절 저장소 구조의 `LICENSE` 줄, English summary 한 줄을 더했다.
- 스킬 사전·개발 플랜·로드맵·status·제출 폼 최종본의 "라이선스 미정/사용자 결정 대기" 문장을 이 결정에 맞게 고쳤다. 지난 결정 기록(2050·2253)과 루트의 이전 기록은 고치지 않았다.

## 검사

모두 작업 worktree에서 2026-09-27(일) 02:3x에 돌렸다 `[사실: 실행 출력]`.

| 검사 | 결과 |
|---|---|
| 전체 시험(키·봉인 환경변수를 지운 환경, `uv run --locked python -m unittest discover -s tests`) | 1681개 OK(skipped=3), 종료 코드 0 |
| 생성기 검증 `scripts/validate_submission.py`(카드 3개) | 0, 0, 0 |
| 비밀값·로컬 경로 검사 `scripts/secret_scan.py`(스테이징 뒤 추적 파일 전체) | 1491개, 걸린 곳 0, 종료 코드 0 |
| 커밋 범위 검사(`origin/main..HEAD`의 추가 행) | 걸린 곳 0, 종료 코드 0 |
| 추가 행의 NVIDIA 키 접두어·서비스키 요청 파라미터·로컬 절대경로 모양 | 0건 |
| 안내 문서 점검(`CLAUDE.md`와 `AGENTS.md` 동일, 문서·절 참조 쌍) | 종료 코드 0 |
| `git status`에 생성기 설치본 사본(`.agents/`)과 실행 출력(`outputs/`)이 보이지 않음(`.gitignore` 대상) | 확인 |

## 남은 것

- `CLAUDE.md`·`AGENTS.md`의 문서 구조 트리에 `LICENSE` 줄을 더하는 일은 이 PR에 넣지 않았다. 사용자 확인을 받은 뒤 따로 더한다.
- `LICENSE` 부록의 자리표시는 Apache License 2.0 전문의 일부로 그대로 두었다. 파일 머리에 저작권 표기를 달지는 사용자가 원할 때 정한다.
- 이 문서 PR이 병합되면 공개 저장소에 바로 드러난다.
