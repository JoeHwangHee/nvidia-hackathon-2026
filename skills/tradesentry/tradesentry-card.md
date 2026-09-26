## Description: <br>
운영자가 관세청 수입통계 경보 목록을 보거나 경보 사례 1건을 조사해 달라고 하면, OpenShell 샌드박스 안 TradeSentry CLI의 `detect`(경보 목록)나 `run-case`(사례 1건 조사)만 한 번 실행하고, CLI가 낸 표준 출력·보고서·종료 코드를 고치지 않고 그대로 전한다. <br>

This skill is for demonstration purposes and not for production usage. <br>

## Third-Party Community Consideration
This skill is not owned or developed by NVIDIA. This skill has been developed and built to a third-party's requirements for this application and use case; see link to Non-NVIDIA [TradeSentry (JoeHwangHee/nvidia-hackathon-2026) Agent Card](../../README.md). <br>

### License/Terms of Use: <br>
Apache-2.0 <br>
## Use Case: <br>
NemoClaw 시연 샌드박스의 OpenClaw 에이전트가, 운영자(담당자)의 경보 목록 요청이나 경보 사례 1건 조사 요청을 받아 값 네 가지(`--snapshot`, `--policy`, `--mode`, `--case`)만 정하고 `/sandbox`에서 `tradesentry detect` 또는 `tradesentry run-case`를 한 번 실행한 뒤, 실행 결과 기록과 보고서의 값을 글자 그대로 운영자에게 옮길 때 쓴다. 정확도 지표를 내는 채점 대상 실행에는 쓰지 않는다. <br>

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
- [개발 플랜 docs/plan/DEV_PLAN.md — §5.2 인터페이스 계약(정본)](../../docs/plan/DEV_PLAN.md) <br>
- [공용 자료 계약 docs/rules/DATA_CONTRACT_V1.md — §4.1 모드 4개, §10 계획 경로·명령 표](../../docs/rules/DATA_CONTRACT_V1.md) <br>
- [로드맵 docs/plan/ROADMAP.md — §3 체크리스트 1번(스킬 호출 성공률)](../../docs/plan/ROADMAP.md) <br>
- [스킬 사전 docs/eval/SKILL_DICTIONARY.md — §3.4 런타임 스킬](../../docs/eval/SKILL_DICTIONARY.md) <br>
- [평가 스킬 ② skills/tradesentry-eval/SKILL.md — 채점 대상 실행은 이 스킬이 맡는다](../tradesentry-eval/SKILL.md) <br>


## Skill Output: <br>
**Output Type(s):** [Shell commands, Files] <br>
**Output Format:** [CLI 표준 출력·표준 오류·종료 코드를 그대로 전달. 읽는 결과 파일은 JSON(실행 결과 기록 `runlog_run_record-{시각}.json`, 보고서 `reports_render_ko-{시각}.json`)] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [CLI가 샌드박스 안 `/sandbox/outputs/{실행명}/`에 `{도메인명}-{시각}.{확장자}`로 쓴 파일 가운데 실행 결과 기록과 보고서(실행이 `COMPLETED`일 때만)만 읽고, trace(`runlog_trace-{시각}.jsonl`)와 NAT 폴더(`workflow_nat_wrap-{시각}`)는 열지 않는다. 값·숫자·상태값을 고치거나 다시 계산하거나 요약하면서 바꾸지 않고, 설명은 보고서 밖에 "스킬 설명"이라고 밝혀 한두 문장만 덧붙인다. 요청마다 CLI를 실제로 불렀는지(명령 이름)와 `run-case`의 `execution_status`를 답 끝에 한 줄로 남긴다. 샌드박스 밖 `outputs/{실행명}/`으로의 내려받기는 이 스킬이 하지 않는다] <br>

## Skill Version(s): <br>
0.1.0 (source: pyproject.toml); skill file last changed at 4f20bd6 (source: git SHA, committed 2026-09-25) <br>


---

## 한국어 요약과 근거(부록. 생성기 형식 밖)

위의 영어 절은 NVIDIA 공식 스킬 `skill-card-generator`(기존 스킬 디렉터리에서 거버넌스 카드(스킬의 능력 범위를 밝히는 카드)를 만드는 스킬)의 스크립트가 렌더한 출력 그대로다. 아래 부록은 스킬 사전(`docs/eval/SKILL_DICTIONARY.md`) §3.5가 카드에서 드러나야 한다고 정한 세 항목(읽는 입력·쓰는 출력, 외부 전송 여부, 금지 사항)과 생성 경위·검토표를 한국어로 적은 것이다. 생성기 절차(`scripts/validate_submission.py`)는 검토 표시가 남았는지만 검사하므로 이 부록은 검증 대상 문구에 걸리지 않는다 `[사실: 생성기 references/skill-card.md.j2·references/style-guide.md·scripts/validate_submission.py (메인 폴더 설치본, 2026-09-26(토))]`.

### 생성 경위 `[사실: 2026-09-26(토)·2026-09-27(일) 작업 기록 — 스킬 사전 §3.5 실행 기록 표]`

- 2026-09-26(토) 15:06 사용자가 메인 폴더에서 `npx skills add NVIDIA/skills --skill skill-card-generator`로 생성기를 설치했다(설치 위치 `.agents/skills/skill-card-generator/`, 커밋하지 않음).
- 같은 날 생성기 스크립트를 순서대로 실행했다: `scripts/discover_assets.py skills/tradesentry`(15:09:54, 종료 코드 0) → 신호 요약과 `skills/tradesentry/SKILL.md` 본문으로 context JSON 작성(`outputs/skill_cards-{시각}/`, 커밋하지 않음) → `scripts/render_card.py --context … --template references/skill-card.md.j2 --out skills/tradesentry/tradesentry-card.md`(15:12:10, 종료 코드 0) → `scripts/validate_submission.py skills/tradesentry/tradesentry-card.md`(15:12:10~11, 종료 코드 1: 소유자 항목의 붉은 VERIFY 표시 1건이 남아 있음. 아래 "남은 확인").
- 값은 `skills/tradesentry/SKILL.md`의 frontmatter와 본문, discover 신호(pyproject 버전, git 원격·SHA, 저장소 루트 LICENSE — 2026-09-26(토) 15:09 생성 때는 없었고 2026-09-27(일) 재렌더 때는 `license_identifier: Apache License  (from LICENSE)`)에서만 가져왔다. 없는 능력을 적지 않았고 결과 숫자를 적지 않았다.
- 이전 카드(같은 경로, 2026-09-26(토) 오전. 생성기를 설치하지 못해 형식만 따라 수동 작성)는 이 파일로 덮어썼다.
- 2026-09-27(일) 라이선스 결정(Apache License 2.0, 결정 기록 `docs/tracking/decisions/20260927-0215-user-decision-license-apache2.md`)에 따라 다시 렌더했다(생성기는 작업 worktree의 설치본 사본 `.agents/skills/skill-card-generator/`, 커밋하지 않음): `scripts/discover_assets.py skills/tradesentry`(02:26:58~59, 종료 코드 0) → 이 카드 생성기 부분의 값을 그대로 옮기고 `license_identifier: "Apache-2.0"`, `license_verify: false` 두 값만 바꾼 context JSON(`outputs/skill_cards-{시각}/`, 커밋하지 않음) → 임시 경로 렌더(02:27:35~36, 종료 코드 0)와 옛 생성기 부분의 diff는 License/Terms of Use 아래 `Apache-2.0 <br>` 한 줄 추가뿐 → `scripts/render_card.py --context … --template references/skill-card.md.j2 --out skills/tradesentry/tradesentry-card.md`(02:28:58, 종료 코드 0) → 이 부록을 다시 붙이고 라이선스 부분만 고침 → `scripts/validate_submission.py skills/tradesentry/tradesentry-card.md`(종료 코드 0. 시각은 스킬 사전 §3.5 실행 기록 표).

### 무엇을 하는가

- NemoClaw(OpenShell 위에서 에이전트를 돌리는 NVIDIA 참조 스택)의 OpenClaw 에이전트가 부르는 런타임 스킬이다. 운영자 요청 → OpenClaw 에이전트 → 이 스킬 → OpenShell(에이전트를 격리해 돌리는 샌드박스 런타임) 샌드박스 안 TradeSentry CLI(명령줄 실행 도구)로 이어진다 `[사실: skills/tradesentry/SKILL.md 머리말]`.
- 경보 목록 요청에는 `tradesentry detect`, 경보 사례 1건 조사 요청에는 `tradesentry run-case`를 한 번만 실행하고, 그 밖의 요청(스냅샷 만들기·검증, 평가·채점, 정답 확인, 설정 변경)은 할 수 없다고 답한다 `[사실: skills/tradesentry/SKILL.md "언제 쓰나"]`.
- 시연 경로 전용이며, 정확도 지표를 내는 채점 대상 실행에는 쓰지 않는다. 결과는 부정·위법·원산지 판정이나 실제 통관 조치가 아니다 `[사실: skills/tradesentry/SKILL.md 머리말]`.

### 읽는 입력·쓰는 출력

- 읽는 입력: 운영자 요청에서 정한 값 네 가지(`--snapshot` 스냅샷 ID, `--policy` 정책 버전 이름, `--mode` 모드, `--case` 사례 식별자)와, CLI 표준 출력에 적힌 경로 가운데 실행 결과 기록(`runlog_run_record-{시각}.json`)·보고서(`reports_render_ko-{시각}.json`. 실행이 `COMPLETED`일 때만) 두 파일만 `cat`으로 읽는다. trace(`runlog_trace-{시각}.jsonl`)·NAT 폴더(`workflow_nat_wrap-{시각}`)·표준 출력에 없는 파일은 열지 않는다 `[사실: skills/tradesentry/SKILL.md "할 일" 1·4]`.
- 쓰는 출력: 이 스킬은 파일을 쓰지 않는다. CLI가 `/sandbox/outputs/{실행명}/`에 쓴 결과의 위치와 종료 코드·표준 출력·표준 오류를 그대로 전하고, 실행 결과 기록과 보고서의 값(`case_id`, `mode`, `execution_status`, `review_status_final`, `signal_status`, `unresolved_evidence`, `narrative`, `hypotheses`, `claims`의 `text`)을 글자 그대로 옮긴다. 샌드박스 밖 `outputs/{실행명}/`으로의 내려받기는 하지 않는다 `[사실: skills/tradesentry/SKILL.md "할 일" 3·4·5]`.

### 외부 전송 여부

- 이 스킬 자체는 외부에 요청하지 않는다. `curl`·`wget`·파이썬 한 줄 등 다른 프로그램으로 외부에 요청하지 않고, NVIDIA 추론 엔드포인트(NIM) 요청은 샌드박스 안 CLI만 한다 `[사실: skills/tradesentry/SKILL.md "하지 않는 것"]`.
- 그래서 위 Requirements / Dependencies 절의 "API key"는 CLI의 추론 요청에 필요한 NVIDIA API 키를 뜻하며, 스킬은 키 값을 다루지 않고 키를 변수 이름으로만 말한다 `[사실: skills/tradesentry/SKILL.md "하지 않는 것"]` `[추론: 생성기 스타일 가이드의 "암묵적 인프라 자격 증명" 규칙을 적용한 분류]`.

### 금지 사항

- `.env` 파일, 환경변수 목록, 자격 증명 파일, 하네스 설정 폴더를 읽거나 출력하지 않는다 `[사실: skills/tradesentry/SKILL.md "하지 않는 것"]`.
- 정답표, 봉인 자료(개발 중 보지 않도록 저장소 밖에 둔 평가 자료), 채점기 출력을 찾거나 읽지 않고, 봉인 자료로 실행하거나 정답 대조 채점을 하지 않는다 `[사실: skills/tradesentry/SKILL.md "하지 않는 것"]`.
- `snapshot-build`·`snapshot-verify`·`evaluate`를 부르지 않고, 보고서와 CLI 출력의 숫자·상태값을 바꾸지 않는다. 종료 코드가 0이 아니면 그대로 전하고 멈추며 옵션을 바꿔 여러 번 부르지 않는다 `[사실: skills/tradesentry/SKILL.md "하지 않는 것"·"할 일" 6]`.

### 확인 결과와 남은 확인

- Third-Party Community Consideration 절의 소유자 표기 "TradeSentry (JoeHwangHee/nvidia-hackathon-2026)"와 링크(별도 에이전트 카드가 없어 저장소 README)는 소유자(사용자)가 2026-09-26(토) 15:34(채팅 "확인") 확인했다. 생성기 절차대로 확인 뒤 붉은 VERIFY 표시(span과 주석)를 지웠고, `scripts/validate_submission.py`는 종료 코드 0이다 `[사실: 사용자 확인 채팅 "확인", 검증 스크립트 실행]`.
- License/Terms of Use 절은 `Apache-2.0`이다: 2026-09-27(일) 사용자 결정(채팅 "라이선스는 권장대로할게", 결정 기록 `docs/tracking/decisions/20260927-0215-user-decision-license-apache2.md`)으로 저장소 루트에 Apache License 2.0 전문 `LICENSE`를 더했고, discover가 그 파일에서 식별자를 읽었으므로(`license_identifier: Apache License  (from LICENSE)`) 스타일 가이드대로 `license_verify: false`(붉은 VERIFY 표시 없음)로 다시 렌더했다. 값은 파일 첫 줄 발췌 대신 스타일 가이드가 요구하는 선택 목록식 짧은 이름(SPDX(소프트웨어 라이선스 표준 식별자) `Apache-2.0`, 파일 둘째 줄 "Version 2.0")으로 적었다. 이전(2026-09-26(토))에는 LICENSE·NOTICE 파일과 SKILL.md frontmatter `license` 키가 없어 `license_identifier: null`로 두어 이 절이 비어 있었다. 저장소에 든 제3자 자료는 Apache-2.0이 아니라 각 출처의 이용 조건을 따른다(README 7절) `[사실: discover 신호 Repo-root signals, 2026-09-27(일)]` `[사실: 생성기 references/skill-card.md.j2·references/style-guide.md "license_identifier"·"license_verify"]`.

### 검토표(review table, 생성기 스타일 가이드 "What goes in the review table")

생성기는 필드마다 신뢰도(`HIGH` 원문 그대로 / `INFERRED` 추론·분류 / `HUMAN-REQUIRED` 출처 없음)와 검토 필요 여부를 표로 남기라고 한다 `[사실: 생성기 references/skill-card.md.j2·references/style-guide.md·scripts/validate_submission.py (메인 폴더 설치본, 2026-09-26(토))]`. 이 저장소의 근거 태그와의 대응 `[DESIGN]`: `HIGH` = `[사실]`, `INFERRED` = `[추론]`, `HUMAN-REQUIRED` = `[미확인]`.

| Section(절) | Field(필드) | Confidence(신뢰도) | Review Needed(검토 필요) | Reasoning(이유) | Source Files(출처) |
|---|---|---|---|---|---|
| Description | `skill_name` | HIGH | No | frontmatter `name`을 생성기 규칙대로 title case로 바꿈(`Tradesentry`) | `skills/tradesentry/SKILL.md` |
| Description | `skill_kind` | HIGH | No | 생성기 기본값 `Agent` | 생성기 `references/style-guide.md` |
| Description | `description_sentence` | HIGH | No | frontmatter `description`의 둘째 문장(첫 문장 "TradeSentry 런타임 스킬."은 제목 구실)을 한 문장 그대로 | `skills/tradesentry/SKILL.md` |
| Description | `usage_posture` | INFERRED | Yes | `demonstration`. "이 스킬은 시연 경로 전용이다", 채점 대상 실행에 쓰지 않음 | `skills/tradesentry/SKILL.md` 머리말 |
| Third-Party Community Consideration | `owner` | INFERRED | Yes(2026-09-26(토) 15:34 확인 끝) | `third_party`. 처음 렌더 때 `verify: true`였고, 2026-09-26(토) 15:34 사용자 확인 뒤 붉은 `VERIFY` 표시를 지웠다. 2026-09-27(일) 재렌더 context는 `verify: false`다. git 원격 `github.com/JoeHwangHee/…`(NVIDIA 조직 아님). 별도 에이전트 카드가 없어 `card_link`는 저장소 README 상대 경로 | discover 신호 `git.remote_url` |
| License/Terms of Use | `license_identifier` | HIGH | No | `Apache-2.0`, `license_verify: false`. 저장소 루트 LICENSE 파일(Apache License 2.0 전문, 2026-09-27(일) 사용자 결정)에서 가져옴. discover는 첫 줄 `Apache License`를 식별자로 읽었고, 스타일 가이드의 선택 목록식 짧은 이름 규칙에 따라 SPDX 식별자로 적음(파일 둘째 줄 "Version 2.0"). 식별자를 LICENSE 파일에서 그대로 가져왔으므로 사람 확인 표시 없음 | `LICENSE`, discover 신호 Repo-root signals |
| Use Case | `use_case` | INFERRED | Yes | "언제 쓰나"·"할 일" 1~5를 두 문장으로 요약 | `skills/tradesentry/SKILL.md` |
| Deployment Geography | `deployment_geography` | INFERRED | Yes | 문서에 지역 제한 없음 → 기본값 `Global` | 생성기 `references/style-guide.md` |
| Requirements / Dependencies | `credential_requirements.requires_api_key_or_credential` | INFERRED | Yes | `yes`. CLI의 NVIDIA 추론 요청에 API 키가 필요("암묵적 인프라 자격 증명" 규칙). 스킬은 키 값을 다루지 않음. discover는 이 SKILL.md에서 키 변수 이름을 찾지 못함 | `skills/tradesentry/SKILL.md` "하지 않는 것" |
| Requirements / Dependencies | `credential_requirements.credential_types` | INFERRED | Yes | `["API key"]`(상태 `yes`와 짝). 변수 이름은 적지 않음 | 같은 곳 |
| Reference(s) | `references` | HIGH | No | SKILL.md 본문이 가리키는 문서 5개(저장소 상대 경로) | `skills/tradesentry/SKILL.md` |
| Skill Output | `output` | HIGH | No | "할 일" 2~7 원문. 분류 어휘(`Shell commands`, `Files`, `1D`)는 스타일 가이드 | `skills/tradesentry/SKILL.md` |
| Skill Version(s) | `skill_version` | INFERRED | Yes | frontmatter `version`·CHANGELOG·git tag 없음 → pyproject `0.1.0`과 SKILL.md 마지막 변경 커밋 SHA | `pyproject.toml`, `git log -1 -- skills/tradesentry/SKILL.md` |
| (생략) | `evaluation` | — | — | 이 스킬 자체를 평가한 기록이 없어 생략. discover가 든 `docs/eval/*`는 TradeSentry 성능 평가 문서이며 스킬 평가가 아님 | None |
