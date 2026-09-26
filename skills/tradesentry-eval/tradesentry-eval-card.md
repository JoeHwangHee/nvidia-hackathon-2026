## Description: <br>
TradeSentry 평가 룰북 Part B(성능 평가)를 사전 점검 → 채점 대상 실행(OpenShell 샌드박스 안) → 정답 대조 채점(샌드박스 밖 독립 채점기) → 결과 보고 순으로 안전하게 수행하는 오케스트레이터용 지침이다. <br>

This skill is for research and development only. <br>

## Third-Party Community Consideration
This skill is not owned or developed by NVIDIA. This skill has been developed and built to a third-party's requirements for this application and use case; see link to Non-NVIDIA [TradeSentry (JoeHwangHee/nvidia-hackathon-2026) Agent Card](../../README.md). <br>

### License/Terms of Use: <br>
## Use Case: <br>
오케스트레이터(작업을 배분·병합하고 사용자와 소통하는 주관 에이전트)가 TradeSentry의 성능 평가를 할 때 쓴다: 구성요소·동결 조건을 사전 점검하고, OpenShell 샌드박스 안에서 자료 묶음(`dev20`, `real_dev`, `holdout40`, `real_sealed`) × 모드(`checklist`, `agent`, `full`, `freeform`)의 채점 대상 실행을 돌리고, 샌드박스 밖 독립 채점기 `eval/scorer/`로 정답 대조 채점을 한 뒤 룰북 B7 양식으로 보고한다. 봉인 묶음은 `RB-1` 동결 조건이 모두 채워졌을 때만, 한 번만 채점한다. <br>

### Deployment Geography for Use: <br>
Global <br>

## Requirements / Dependencies: <br>
**Requires API Key or External Credential:** [Yes] <br>
**Credential Type(s):** [API key] <br>  

Do not include secrets in prompts/logs/output; use least-privilege credentials; rotate keys as appropriate. See skill body for more details. <br>

## Known Risks and Mitigations: <br>
Risk: Review before execution as proposals could introduce incorrect or misleading guidance into skills. <br>
Mitigation: Review and scan skill before deployment. <br>

## Reference(s): <br>
- [평가 룰북 docs/eval/RULEBOOK.md — Part B(B1~B7), A5](../../docs/eval/RULEBOOK.md) <br>
- [공용 자료 계약 docs/rules/DATA_CONTRACT_V1.md — §4, §7, §8, §9, §10, §12](../../docs/rules/DATA_CONTRACT_V1.md) <br>
- [병렬 개발 규칙 docs/rules/PARALLEL_DEV_RULES.md — §6 봉인 자료, §7 실자료 분할](../../docs/rules/PARALLEL_DEV_RULES.md) <br>
- [에이전트 운용 규칙 docs/rules/AGENT_OPS.md — §1.2, §1.4, §7](../../docs/rules/AGENT_OPS.md) <br>
- [개발 플랜 docs/plan/DEV_PLAN.md — §3.2, §4, §5.4, §9](../../docs/plan/DEV_PLAN.md) <br>
- [스킬 사전 docs/eval/SKILL_DICTIONARY.md — §3.3, §3.4](../../docs/eval/SKILL_DICTIONARY.md) <br>
- [로드맵 docs/plan/ROADMAP.md — MVP 합격 체크리스트](../../docs/plan/ROADMAP.md) <br>


## Skill Output: <br>
**Output Type(s):** [Shell commands, Files, Analysis] <br>
**Output Format:** [JSONL(채점기 결과 `scorer_results-{시각}.jsonl`, `scorer_claims-{시각}.jsonl`)와 Markdown(결과 요약 `scorer_summary-{시각}.md`, 결정 기록)] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [채점 대상 실행의 도메인 출력은 실행 폴더 `outputs/{실행명}/`(봉인 묶음은 자료 계약 §10.3 N10이 정한 봉인 출력 자리)에 남고 커밋하지 않는다. 채점기는 자기 출력을 `outputs/score-{시각}/`에 쓰고, 그 `scorer_*` 파일과 재채점용 보고서 원문(`{run_id}/` 아래 허용 목록 파일)만 `artifacts/eval/score-{시각}/`로 증거 복사해 커밋한다. 실패·미실행·timeout·invalid도 분모에 남긴다. 봉인 묶음 출력과 그 채점기 출력은 금지 해제 조건(자료 계약 §10.3 N10) 전에는 열지 않고 커밋하지 않는다. 봉인 사건은 결정 기록에 날짜·주체·파일 수·해시 대조 결과로 남기고 봉인 자료 내용은 적지 않는다] <br>

## Skill Version(s): <br>
0.1.0 (source: pyproject.toml); skill file last changed at 963ef0d (source: git SHA, committed 2026-09-26) <br>


---

## 한국어 요약과 근거(부록. 생성기 형식 밖)

위의 영어 절은 NVIDIA 공식 스킬 `skill-card-generator`(기존 스킬 디렉터리에서 거버넌스 카드(스킬의 능력 범위를 밝히는 카드)를 만드는 스킬)의 스크립트가 렌더한 출력 그대로다. 아래 부록은 스킬 사전(`docs/eval/SKILL_DICTIONARY.md`) §3.5가 카드에서 드러나야 한다고 정한 세 항목(읽는 입력·쓰는 출력, 외부 전송 여부, 금지 사항)과 생성 경위·검토표를 한국어로 적은 것이다. 생성기 절차(`scripts/validate_submission.py`)는 검토 표시가 남았는지만 검사하므로 이 부록은 검증 대상 문구에 걸리지 않는다 `[사실: 생성기 references/skill-card.md.j2·references/style-guide.md·scripts/validate_submission.py (메인 폴더 설치본, 2026-09-26(토))]`.

### 생성 경위 `[사실: 2026-09-26(토) 작업 기록 — 스킬 사전 §3.5 실행 기록 표]`

- 2026-09-26(토) 15:06 사용자가 메인 폴더에서 `npx skills add NVIDIA/skills --skill skill-card-generator`로 생성기를 설치했다(설치 위치 `.agents/skills/skill-card-generator/`, 커밋하지 않음).
- 같은 날 생성기 스크립트를 순서대로 실행했다: `scripts/discover_assets.py skills/tradesentry-eval`(15:09:54, 종료 코드 0) → 신호 요약과 `skills/tradesentry-eval/SKILL.md` 본문으로 context JSON 작성(`outputs/skill_cards-{시각}/`, 커밋하지 않음) → `scripts/render_card.py --context … --template references/skill-card.md.j2 --out skills/tradesentry-eval/tradesentry-eval-card.md`(15:12:10, 종료 코드 0) → `scripts/validate_submission.py skills/tradesentry-eval/tradesentry-eval-card.md`(15:12:10~11, 종료 코드 1: 소유자 항목의 붉은 VERIFY 표시 1건이 남아 있음. 아래 "남은 확인").
- 값은 `skills/tradesentry-eval/SKILL.md`의 frontmatter와 본문, discover 신호(pyproject 버전, git 원격·SHA, 저장소 루트의 LICENSE 부재)에서만 가져왔다. 없는 능력을 적지 않았고 결과 숫자를 적지 않았다.
- 이전 카드(같은 경로, 2026-09-26(토) 오전. 생성기를 설치하지 못해 형식만 따라 수동 작성)는 이 파일로 덮어썼다.

### 무엇을 하는가

- 평가 스킬 ②다. 평가 룰북(`docs/eval/RULEBOOK.md`) Part B의 TradeSentry 성능 평가를 사전 점검 → 채점 대상 실행(OpenShell 샌드박스 안 CLI) → 정답 대조 채점(샌드박스 밖 독립 채점기 `eval/scorer/`) → 결과 보고 순서로 수행하는 오케스트레이터용 지침이다. 순서를 건너뛰지 않는다 `[사실: skills/tradesentry-eval/SKILL.md 머리말·"두 가지 실행"]`.
- 자료 묶음 `dev20`·`real_dev`(개발), `holdout40`·`real_sealed`(봉인) × 모드 `checklist`·`agent`·`full`·`freeform`으로 돌리고, 봉인 묶음은 `RB-1`(룰북 첫 동결 버전) 동결 조건이 모두 채워졌을 때만 한 번 채점한다 `[사실: skills/tradesentry-eval/SKILL.md "언제 쓰나"·"채점" 산출물]`.
- 이 스킬이 내는 숫자는 부정·위법·원산지 판정의 정확도가 아니다 `[사실: skills/tradesentry-eval/SKILL.md 머리말]`.

### 읽는 입력·쓰는 출력

- 읽는 입력(샌드박스에 들이는 것): 읽기 전용 앱 코드·설정·스냅샷, `dev20`이면 `eval/dev/dev20/`의 입력 하위 경로, `holdout40`이면 봉인 입력. `real_sealed`는 봉인 파일을 하나도 넣지 않고 사례 식별자를 샌드박스 밖 실행기(단위 E2)가 인자로 한 건씩 넘긴다. 정답표(`eval/dev/oracle_ABC.json` 등)·채점기·봉인 폴더·`outputs/`·`artifacts/eval/`·`.env`는 어떤 샌드박스에도 들이지 않는다 `[사실: skills/tradesentry-eval/SKILL.md "실행" 샌드박스 표]`.
- 쓰는 출력: 채점 대상 실행의 도메인 출력은 `outputs/{실행명}/`(봉인 묶음은 자료 계약 §10.3 N10이 정한 봉인 출력 자리, 커밋 안 함). 채점기 출력은 `outputs/score-{시각}/`의 `scorer_results-{시각}.jsonl`·`scorer_claims-{시각}.jsonl`·`scorer_summary-{시각}.md`이고, 그 `scorer_*` 파일과 재채점용 보고서 원문(허용 목록 파일만)을 `artifacts/eval/score-{시각}/`로 증거 복사해 커밋한다. 봉인 사건은 결정 기록(`docs/tracking/decisions/`)에 남긴다 `[사실: skills/tradesentry-eval/SKILL.md "이름과 출력 위치"·"채점" 산출물·"보고와 커밋"]`.

### 외부 전송 여부

- 외부 전송은 샌드박스 안 CLI의 NVIDIA 추론 요청 한 경로만이다. 키는 샌드박스 프로그램에 자리표시 문자열만 두고 OpenShell 감독 프로세스의 정책 프록시가 나가는 요청에 넣는 방식(credential placeholder rewrite)으로 주입하며, 에이전트와 그 자식 프로세스가 읽을 수 있는 곳에 두지 않는다 `[사실: skills/tradesentry-eval/SKILL.md "실행" 샌드박스 절의 API 키 항목]`.
- 샌드박스 밖 실행기와 채점기는 키 변수를 뺀 환경(`env -u …`)에서 돌리고 `.env`를 읽지 않으며 둘 다 키가 필요 없다 `[사실: skills/tradesentry-eval/SKILL.md "실행" 샌드박스 절]`. 위 Requirements / Dependencies 절의 "API key"는 채점 대상 실행 쪽 CLI의 추론 요청에 필요한 NVIDIA API 키를 뜻한다 `[추론: 생성기 스타일 가이드의 "암묵적 인프라 자격 증명" 규칙을 적용한 분류]`.

### 금지 사항

- `.env`를 읽거나 출력하지 않고, 키 값을 어디에도 출력하지 않는다. 문서·기록·PR에는 변수 이름만 쓴다 `[사실: skills/tradesentry-eval/SKILL.md "금지"]`.
- 정답표와 채점기를 어떤 샌드박스에도 넣지 않고, 오케스트레이터는 정답표를 열지 않는다. 봉인 입력을 개발·시연용 샌드박스에 넣지 않으며 `real_sealed`의 사례 목록과 채점 표본은 어떤 샌드박스에도 넣지 않는다 `[사실: skills/tradesentry-eval/SKILL.md "금지"]`.
- 봉인 폴더(`TRADESENTRY_SEALED_DIR`, 기본값 밖의 위치를 받지 않음)에 쓰지 않고 파일 탐색기로 열지 않는다. 금지 해제 조건(자료 계약 §10.3 N10) 전에는 봉인 묶음 출력(자료 계약 §10.3 N10의 자리)·그 채점기 출력·trace를 열지 않고 커밋하지 않는다. `holdout40`과 `real_sealed`를 두 번 채점하지 않는다 `[사실: skills/tradesentry-eval/SKILL.md "금지"]`.
- 결과를 본 뒤 규칙·정책·프롬프트·검증기·채점기·산문 패턴 목록을 유리하게 고치지 않고, 실패·미실행 기록을 지우거나 덮어쓰지 않는다. 채점 대상 실행을 샌드박스 밖이나 NemoClaw 에이전트·런타임 `tradesentry` 스킬 경로로 돌리지 않는다 `[사실: skills/tradesentry-eval/SKILL.md "금지"]`.

### 확인 결과와 남은 확인

- Third-Party Community Consideration 절의 소유자 표기 "TradeSentry (JoeHwangHee/nvidia-hackathon-2026)"와 링크(별도 에이전트 카드가 없어 저장소 README)는 소유자(사용자)가 2026-09-26(토) 15:34(채팅 "확인") 확인했다. 생성기 절차대로 확인 뒤 붉은 VERIFY 표시(span과 주석)를 지웠고, `scripts/validate_submission.py`는 종료 코드 0이다 `[사실: 사용자 확인 채팅 "확인", 검증 스크립트 실행]`.
- License/Terms of Use 절이 비어 있다: 저장소에 LICENSE·NOTICE 파일과 SKILL.md frontmatter `license` 키가 없어 `license_identifier: null`로 두었고, 템플릿은 식별자가 없으면 이 절을 비워 렌더한다(표시도 붙지 않는다). 라이선스는 저장소 공개 방식 결정(로드맵 P2) 때 정하고 context JSON을 고쳐 다시 렌더한다 `[사실: discover 신호 Repo-root signals, 2026-09-26(토)]` `[사실: 생성기 references/skill-card.md.j2·references/style-guide.md·scripts/validate_submission.py (메인 폴더 설치본, 2026-09-26(토))]`.

### 검토표(review table, 생성기 스타일 가이드 "What goes in the review table")

생성기는 필드마다 신뢰도(`HIGH` 원문 그대로 / `INFERRED` 추론·분류 / `HUMAN-REQUIRED` 출처 없음)와 검토 필요 여부를 표로 남기라고 한다 `[사실: 생성기 references/skill-card.md.j2·references/style-guide.md·scripts/validate_submission.py (메인 폴더 설치본, 2026-09-26(토))]`. 이 저장소의 근거 태그와의 대응 `[DESIGN]`: `HIGH` = `[사실]`, `INFERRED` = `[추론]`, `HUMAN-REQUIRED` = `[미확인]`.

| Section(절) | Field(필드) | Confidence(신뢰도) | Review Needed(검토 필요) | Reasoning(이유) | Source Files(출처) |
|---|---|---|---|---|---|
| Description | `skill_name` | HIGH | No | frontmatter `name`을 title case로(`Tradesentry Eval`) | `skills/tradesentry-eval/SKILL.md` |
| Description | `skill_kind` | HIGH | No | 생성기 기본값 `Agent` | 생성기 `references/style-guide.md` |
| Description | `description_sentence` | HIGH | No | frontmatter `description` 첫 문장 그대로 | `skills/tradesentry-eval/SKILL.md` |
| Description | `usage_posture` | INFERRED | Yes | `research_dev`. 대회 제출용 평가 절차이며 운영 배포가 없음 | `skills/tradesentry-eval/SKILL.md`, `CLAUDE.md` 프로젝트 개요 |
| Third-Party Community Consideration | `owner` | INFERRED | Yes | `third_party`, `verify: true`. git 원격이 NVIDIA 조직 아님. 별도 에이전트 카드가 없어 `card_link`는 저장소 README 상대 경로 | discover 신호 `git.remote_url` |
| License/Terms of Use | `license_identifier` | HUMAN-REQUIRED | Yes | `null`, `license_verify: true`. LICENSE·NOTICE·frontmatter `license` 없음. 템플릿은 이 절을 비워 렌더함 | discover 신호 Repo-root signals |
| Use Case | `use_case` | INFERRED | Yes | "언제 쓰나"·"실행"·"채점"·"기본 정보" 실행자를 요약 | `skills/tradesentry-eval/SKILL.md` |
| Deployment Geography | `deployment_geography` | INFERRED | Yes | 문서에 지역 제한 없음 → 기본값 `Global` | 생성기 `references/style-guide.md` |
| Requirements / Dependencies | `credential_requirements.requires_api_key_or_credential` | INFERRED | Yes | `yes`. 샌드박스 안 CLI의 추론 요청에 NVIDIA API 키가 필요하고 SKILL.md가 키 주입 방식을 문서화함. discover도 이 SKILL.md에서 키 변수 이름 1개를 찾음. 실행기·채점기는 키 없이 돎 | `skills/tradesentry-eval/SKILL.md` "실행" 샌드박스 절 |
| Requirements / Dependencies | `credential_requirements.credential_types` | INFERRED | Yes | `["API key"]`(상태 `yes`와 짝). 변수 이름은 적지 않음 | 같은 곳 |
| Reference(s) | `references` | HIGH | No | "줄여 부르는 문서" 표의 문서 7개(저장소 상대 경로) | `skills/tradesentry-eval/SKILL.md` |
| Skill Output | `output` | HIGH | No | "이름과 출력 위치"·"채점" 산출물 표·"보고와 커밋" 원문 | `skills/tradesentry-eval/SKILL.md` |
| Skill Version(s) | `skill_version` | INFERRED | Yes | frontmatter `version`·CHANGELOG·git tag 없음 → pyproject `0.1.0`과 SKILL.md 마지막 변경 커밋 SHA | `pyproject.toml`, `git log -1 -- skills/tradesentry-eval/SKILL.md` |
| (생략) | `evaluation` | — | — | 이 스킬 자체를 평가한 기록이 없어 생략. 이 스킬이 재는 TradeSentry 성능 숫자는 스킬 평가가 아니며 카드에 적지 않음 | None |
