## Description: <br>
TradeSentry 저장소를 평가 룰북 docs/eval/RULEBOOK.md의 Part A(팀 채점 규범 SCORING_GOLDEN_RULE.md를 TradeSentry 증거로 풀어 쓴 자기채점 규칙)로 채점하는 평가 스킬 ①이다. <br>

This skill is for research and development only. <br>

## Third-Party Community Consideration
<span style="color:#d73a49">This skill is not owned or developed by NVIDIA. This skill has been developed and built to a third-party's requirements for this application and use case; see link to Non-NVIDIA [TradeSentry (JoeHwangHee/nvidia-hackathon-2026) Agent Card](../../README.md).</span> <!-- VERIFY: third-party ownership inferred from the git remote (github.com/JoeHwangHee) and the SKILL.md author; the repo has no separate agent card, so the link points to the repo README. Confirm the owner label and link, then strip this marker. --> <br>

### License/Terms of Use: <br>
## Use Case: <br>
TradeSentry 팀의 에이전트가 룰북 Part A가 정한 세 회차(MVP 시험 뒤, `RB-1` 동결 뒤 결과 정리 때, 제출 전)와 자기채점·점수표 요청 때, 저장소에 이미 남은 산출물(커밋된 채점 결과, OpenShell 증거, 스킬, 채점기, 시험)을 읽어 규범 G1~G6 하드 게이트와 채점 지표 20개를 판정하고, 판정마다 근거 한 줄과 증거 경로를 붙인 결과 파일을 남길 때 쓴다. 채점 대상 실행과 정답 대조 채점은 하지 않는다. <br>

### Deployment Geography for Use: <br>
Global <br>

## Requirements / Dependencies: <br>
**Requires API Key or External Credential:** [Not Specified] <br>
**Credential Type(s):** [None identified] <br>  

Do not include secrets in prompts/logs/output; use least-privilege credentials; rotate keys as appropriate. See skill body for more details. <br>

## Known Risks and Mitigations: <br>
Risk: Review before execution as proposals could introduce incorrect or misleading guidance into skills. <br>
Mitigation: Review and scan skill before deployment. <br>

## Reference(s): <br>
- [평가 룰북 docs/eval/RULEBOOK.md — Part A(A1~A5)와 부록](../../docs/eval/RULEBOOK.md) <br>
- [팀 채점 규범 SCORING_GOLDEN_RULE.md — §2~§4, §7](../../SCORING_GOLDEN_RULE.md) <br>
- [공용 자료 계약 docs/rules/DATA_CONTRACT_V1.md — §10 계획 경로·명령 표](../../docs/rules/DATA_CONTRACT_V1.md) <br>
- [스킬 사전 docs/eval/SKILL_DICTIONARY.md — §1 상태 열, §2.1, §3.2, §3.4](../../docs/eval/SKILL_DICTIONARY.md) <br>
- [개발 플랜 docs/plan/DEV_PLAN.md — §1, §5.4](../../docs/plan/DEV_PLAN.md) <br>
- [로드맵 docs/plan/ROADMAP.md — MVP 합격 체크리스트](../../docs/plan/ROADMAP.md) <br>


## Skill Output: <br>
**Output Type(s):** [Files, Analysis] <br>
**Output Format:** [Markdown] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [회차마다 새 실행 폴더 `outputs/scorecard-{시각}/`를 배타 생성(이미 있으면 실패하는 방식)해 `scorecard-{시각}.md` 한 파일을 쓰고(덮어쓰기 금지), 비밀값·로컬 경로 검사를 통과한 그 파일만 같은 이름의 폴더 `artifacts/scorecard/scorecard-{시각}/`로 증거 복사해 커밋한다. 양식은 룰북 A3 "자기채점 결과 파일 양식"이고 점수는 0/1/3/5만 쓴다. 게이트 FAIL이 있으면 머리 정보·게이트·해소 조건만 남긴다] <br>

## Skill Version(s): <br>
0.1.0 (source: pyproject.toml); skill file last changed at 8adad56 (source: git SHA, committed 2026-09-25) <br>


---

## 한국어 요약과 근거(부록. 생성기 형식 밖)

위의 영어 절은 NVIDIA 공식 스킬 `skill-card-generator`(기존 스킬 디렉터리에서 거버넌스 카드(스킬의 능력 범위를 밝히는 카드)를 만드는 스킬)의 스크립트가 렌더한 출력 그대로다. 아래 부록은 스킬 사전(`docs/eval/SKILL_DICTIONARY.md`) §3.5가 카드에서 드러나야 한다고 정한 세 항목(읽는 입력·쓰는 출력, 외부 전송 여부, 금지 사항)과 생성 경위·검토표를 한국어로 적은 것이다. 생성기 절차(`scripts/validate_submission.py`)는 검토 표시가 남았는지만 검사하므로 이 부록은 검증 대상 문구에 걸리지 않는다 `[사실: 생성기 references/skill-card.md.j2·references/style-guide.md·scripts/validate_submission.py (메인 폴더 설치본, 2026-09-26(토))]`.

### 생성 경위 `[사실: 2026-09-26(토) 작업 기록 — 스킬 사전 §3.5 실행 기록 표]`

- 2026-09-26(토) 15:06 사용자가 메인 폴더에서 `npx skills add NVIDIA/skills --skill skill-card-generator`로 생성기를 설치했다(설치 위치 `.agents/skills/skill-card-generator/`, 커밋하지 않음).
- 같은 날 생성기 스크립트를 순서대로 실행했다: `scripts/discover_assets.py skills/tradesentry-scorecard`(15:09:54, 종료 코드 0) → 신호 요약과 `skills/tradesentry-scorecard/SKILL.md` 본문으로 context JSON 작성(`outputs/skill_cards-{시각}/`, 커밋하지 않음) → `scripts/render_card.py --context … --template references/skill-card.md.j2 --out skills/tradesentry-scorecard/tradesentry-scorecard-card.md`(15:12:10, 종료 코드 0) → `scripts/validate_submission.py skills/tradesentry-scorecard/tradesentry-scorecard-card.md`(15:12:10~11, 종료 코드 1: 소유자 항목의 붉은 VERIFY 표시 1건이 남아 있음. 아래 "남은 확인").
- 값은 `skills/tradesentry-scorecard/SKILL.md`의 frontmatter와 본문, discover 신호(pyproject 버전, git 원격·SHA, 저장소 루트의 LICENSE 부재)에서만 가져왔다. 없는 능력을 적지 않았고 결과 숫자를 적지 않았다.
- 이전 카드(같은 경로, 2026-09-26(토) 오전. 생성기를 설치하지 못해 형식만 따라 수동 작성)는 이 파일로 덮어썼다.

### 무엇을 하는가

- 평가 스킬 ①이다. 에이전트가 TradeSentry 저장소를 룰북(`docs/eval/RULEBOOK.md`) Part A(팀 채점 규범 `SCORING_GOLDEN_RULE.md`를 TradeSentry 증거로 풀어 쓴 자기채점 규칙)로 자기채점하고, 규범 G1~G6 하드 게이트와 채점 지표 20개(0/1/3/5만)·`2e` 표시·CAP 규칙·판정 밴드·가장 낮은 축 2개·컴포넌트 삭제 시험 답을 판정마다 근거 한 줄과 증거 경로를 붙여 결과 파일로 남긴다 `[사실: skills/tradesentry-scorecard/SKILL.md frontmatter description·머리말]`.
- 세 회차(2026-09-25(금) MVP 시험 뒤, `RB-1` 동결 뒤 결과 정리 때, 2026-09-28(월) 제출 전)와 자기채점·점수표 요청 때 쓴다. 성능 평가(평가 스킬 ②의 일)와 아이디어 고르기는 하지 않는다 `[사실: skills/tradesentry-scorecard/SKILL.md "언제 쓰나"]`.
- 자기채점 점수는 대회 점수가 아니다 `[사실: skills/tradesentry-scorecard/SKILL.md "정본과 이 스킬의 관계"]`.

### 읽는 입력·쓰는 출력

- 읽는 입력: 저장소 루트·룰북 버전·코드 버전(`git rev-parse HEAD`)·채점 시각·채점한 에이전트 이름(입력 표), 정본 문서(룰북 Part A·부록, 규범 §2~§4·§7, 자료 계약 §10, 스킬 사전 §1·§2.1·§3.4, 개발 플랜 §1·§5.4, 로드맵 MVP 체크리스트, 결정 기록), 증거 위치(`artifacts/eval/score-{시각}/`, `configs/openshell/policy.yaml`, `artifacts/openshell/openshell_violation_tests-{시각}/`, `configs/nat/workflow.yml`, 스킬 3개, `eval/scorer/`, `eval/dev/oracle_ABC.json`, `eval/dev/dev20/`, `eval/sealed_manifest.json`, README, `tests/`, `configs/policy_v1.json`) `[사실: skills/tradesentry-scorecard/SKILL.md "입력"·"읽는 문서"·"증거를 찾는 곳"]`.
- 쓰는 출력: 회차마다 새 실행 폴더 `outputs/scorecard-{시각}/`를 배타 생성해 `scorecard-{시각}.md` 한 파일(룰북 A3 양식, 한국어)을 쓰고, 비밀값·로컬 경로 검사를 통과한 그 파일만 `artifacts/scorecard/scorecard-{시각}/`로 증거 복사해 `git add <파일>`로 커밋한다. 앞선 회차의 폴더·파일은 고쳐 쓰지 않는다 `[사실: skills/tradesentry-scorecard/SKILL.md "출력"·"9단계. 저장과 커밋"]`.

### 외부 전송 여부

- 이 스킬은 채점 대상 실행을 돌리지 않고 정답 대조 채점도 새로 하지 않는다. 직접 돌리는 것은 규범 G4 확인용 시험·스모크·검사 명령과, 규범 G1 증거 확인용으로 `real_dev`의 run_dir에서 채점기를 다시 돌리는 일뿐이다 `[사실: skills/tradesentry-scorecard/SKILL.md "언제 쓰나"·"금지"]`. 그 두 종류의 명령은 네트워크·키 없이 돈다 `[추론: 저장소 시험 명령(CLAUDE.md)과 평가 스킬 ② "실행" 절의 채점기 조건]`.
- SKILL.md는 자격 증명이 필요하다거나 필요 없다고 명시하지 않고 키를 변수 이름으로만 언급하므로, 위 Requirements / Dependencies 절은 생성기 스타일 가이드의 정직한 기본값 "Not Specified"·"None identified"다 `[추론: 생성기 references/style-guide.md의 credential_requirements 분류 규칙]`.

### 금지 사항

- `.env`(키 파일)와 봉인 폴더(환경변수 `TRADESENTRY_SEALED_DIR`, 기본값 `~/.tradesentry/sealed/`)를 읽지 않는다. 키는 변수 이름(`NVIDIA_API_KEY`, `DATA_GO_KR_SERVICE_KEY`)으로만 말하고 키 값을 결과 파일·로그·보고에 쓰지 않는다 `[사실: skills/tradesentry-scorecard/SKILL.md "읽지 않는 것"·"금지"]`.
- 금지 해제 조건(자료 계약 §10.3 N10) 전의 봉인 묶음(`holdout40`, `real_sealed`) 출력(`outputs/sealed/` 아래, trace 포함)과 봉인 묶음을 채점한 채점기 출력 폴더를 읽지 않는다. `holdout40`·`real_sealed`에는 채점기를 돌리지 않는다 `[사실: skills/tradesentry-scorecard/SKILL.md "읽지 않는 것"·"금지"]`.
- 증거 없이 점수를 올리지 않고, 2점·4점 등 중간 값을 쓰지 않으며, 근거 한 줄을 비운 채 점수를 주지 않는다. 룰북과 규범을 고치지 않고 결과를 본 뒤 앵커 해석을 유리하게 바꾸지 않는다. 계획 경로·명령 표에 없는 경로를 짓지 않는다 `[사실: skills/tradesentry-scorecard/SKILL.md "금지"]`.

### 남은 확인 `[미확인]`

- 위 Third-Party Community Consideration 절의 붉은 VERIFY 표시(생성기가 추론·기본값 항목에 붙이는 사람 확인 표시) 1건: 소유자 표기 "TradeSentry (JoeHwangHee/nvidia-hackathon-2026)"와 링크(별도 에이전트 카드가 없어 저장소 README)를 소유자(사용자)가 확인하거나 고친 뒤, 붉은 span과 그 옆 주석을 지운다. 생성기 절차상 이 표시를 지우는 것은 사람 검토자의 일이며, 표시가 남은 동안 `scripts/validate_submission.py`는 종료 코드 1을 낸다 `[사실: 생성기 references/skill-card.md.j2·references/style-guide.md·scripts/validate_submission.py (메인 폴더 설치본, 2026-09-26(토))]`.
- License/Terms of Use 절이 비어 있다: 저장소에 LICENSE·NOTICE 파일과 SKILL.md frontmatter `license` 키가 없어 `license_identifier: null`로 두었고, 템플릿은 식별자가 없으면 이 절을 비워 렌더한다(표시도 붙지 않는다). 라이선스는 저장소 공개 방식 결정(로드맵 P2) 때 정하고 context JSON을 고쳐 다시 렌더한다 `[사실: discover 신호 Repo-root signals, 2026-09-26(토)]` `[사실: 생성기 references/skill-card.md.j2·references/style-guide.md·scripts/validate_submission.py (메인 폴더 설치본, 2026-09-26(토))]`.

### 검토표(review table, 생성기 스타일 가이드 "What goes in the review table")

생성기는 필드마다 신뢰도(`HIGH` 원문 그대로 / `INFERRED` 추론·분류 / `HUMAN-REQUIRED` 출처 없음)와 검토 필요 여부를 표로 남기라고 한다 `[사실: 생성기 references/skill-card.md.j2·references/style-guide.md·scripts/validate_submission.py (메인 폴더 설치본, 2026-09-26(토))]`. 이 저장소의 근거 태그와의 대응 `[DESIGN]`: `HIGH` = `[사실]`, `INFERRED` = `[추론]`, `HUMAN-REQUIRED` = `[미확인]`.

| Section(절) | Field(필드) | Confidence(신뢰도) | Review Needed(검토 필요) | Reasoning(이유) | Source Files(출처) |
|---|---|---|---|---|---|
| Description | `skill_name` | HIGH | No | frontmatter `name`을 title case로(`Tradesentry Scorecard`) | `skills/tradesentry-scorecard/SKILL.md` |
| Description | `skill_kind` | HIGH | No | 생성기 기본값 `Agent` | 생성기 `references/style-guide.md` |
| Description | `description_sentence` | HIGH | No | frontmatter `description` 첫 문장 그대로 | `skills/tradesentry-scorecard/SKILL.md` |
| Description | `usage_posture` | INFERRED | Yes | `research_dev`. 자기채점 절차이며 점수가 대회 점수가 아니라고 명시. 운영 배포 없음 | `skills/tradesentry-scorecard/SKILL.md`, `CLAUDE.md` 프로젝트 개요 |
| Third-Party Community Consideration | `owner` | INFERRED | Yes | `third_party`, `verify: true`. git 원격이 NVIDIA 조직 아님. 별도 에이전트 카드가 없어 `card_link`는 저장소 README 상대 경로 | discover 신호 `git.remote_url` |
| License/Terms of Use | `license_identifier` | HUMAN-REQUIRED | Yes | `null`, `license_verify: true`. LICENSE·NOTICE·frontmatter `license` 없음. 템플릿은 이 절을 비워 렌더함 | discover 신호 Repo-root signals |
| Use Case | `use_case` | INFERRED | Yes | "언제 쓰나"·"입력"·"증거를 찾는 곳"을 두 문장으로 요약 | `skills/tradesentry-scorecard/SKILL.md` |
| Deployment Geography | `deployment_geography` | INFERRED | Yes | 문서에 지역 제한 없음 → 기본값 `Global` | 생성기 `references/style-guide.md` |
| Requirements / Dependencies | `credential_requirements.requires_api_key_or_credential` | INFERRED | Yes | `not specified`. SKILL.md에 설치·인증 절이 없고 자격 증명이 필요·불필요하다는 명시도 없으며 키를 변수 이름으로만 언급(discover가 변수 이름 1개를 찾음) → 스타일 가이드의 "신호는 있으나 문서화 없음" 기본값. 이전 수동 카드의 `no`는 추론이어서 정직한 기본값으로 바꿈 | `skills/tradesentry-scorecard/SKILL.md` "읽지 않는 것"·"금지", 생성기 `references/style-guide.md` |
| Requirements / Dependencies | `credential_requirements.credential_types` | INFERRED | Yes | `[]`(상태 `not specified`와 짝). 템플릿은 `None identified`로 렌더 | 같은 곳 |
| Reference(s) | `references` | HIGH | No | "읽는 문서"의 문서 6개(저장소 상대 경로) | `skills/tradesentry-scorecard/SKILL.md` |
| Skill Output | `output` | HIGH | No | "출력"·"9단계. 저장과 커밋" 원문 | `skills/tradesentry-scorecard/SKILL.md` |
| Skill Version(s) | `skill_version` | INFERRED | Yes | frontmatter `version`·CHANGELOG·git tag 없음 → pyproject `0.1.0`과 SKILL.md 마지막 변경 커밋 SHA | `pyproject.toml`, `git log -1 -- skills/tradesentry-scorecard/SKILL.md` |
| (생략) | `evaluation` | — | — | 이 스킬 자체를 평가한 기록이 없어 생략 | None |
