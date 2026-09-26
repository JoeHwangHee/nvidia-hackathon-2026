# tradesentry-scorecard 거버넌스 카드(skill card)

평가 스킬 ① `tradesentry-scorecard`(TradeSentry 저장소를 평가 룰북 Part A로 자기채점하는 Agent Skills 형식의 작업 절차)의 거버넌스 카드(스킬이 무엇을 하고 무엇을 읽고 쓰는지 등 능력 범위를 밝히는 카드)다. NVIDIA 공식 스킬 `skill-card-generator`(기존 스킬 디렉터리에서 거버넌스 카드를 만드는 스킬)의 카드 형식을 따랐다: 절 제목과 순서는 생성기 템플릿 `references/skill-card.md.j2`, 항목 값의 규칙은 `references/style-guide.md`, 검토표는 생성기 SKILL.md의 작업 순서 5단계다. **생성기 형식을 따라 수동 작성** `[사실: 2026-09-26(토) 설치 명령(npx skills add NVIDIA/skills --skill skill-card-generator)이 작업 에이전트의 실행 권한 정책(신뢰하지 않는 코드 설치 차단)으로 거부돼 설치하지 못했고, 생성기의 SKILL.md·템플릿·스타일 가이드·예시 카드를 GitHub NVIDIA/skills 저장소(해당 폴더의 마지막 커밋 2a23a90, 2026-07-01)에서 읽어 같은 형식으로 손으로 채웠다. 생성기의 discover·render·validate 스크립트는 돌리지 않았다]`.

- 값은 `skills/tradesentry-scorecard/SKILL.md` 본문에서 가져온 사실만 적었다. 없는 능력을 적지 않았고 결과 숫자는 적지 않는다. `[사실: 아래 각 절의 태그가 근거 위치를 가리킨다]`
- 절 제목은 생성기 템플릿의 영어 제목을 그대로 두고 괄호에 한국어 설명을 붙였다. 템플릿이 고정한 영어 문장은 그대로 두고 아래 줄에 한국어 설명을 달았다. `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`
- 붉은 `VERIFY` 표시(생성기가 추론·기본값 항목에 붙이는 사람 확인 표시)는 소유자(사용자)가 확인한 뒤 지운다. 생성기 규칙상 표시가 남은 카드는 제출 전 검증에서 실패한다. `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`
- 카드 파일 위치 `skills/tradesentry-scorecard/tradesentry-scorecard-card.md`는 생성기 SKILL.md "Examples"의 출력 형식(대상 스킬 폴더 안 `<스킬 이름>-card.md`)을 따랐다 `[사실: 생성기 SKILL.md Examples의 --out 인자]`. 경로의 정본은 `docs/rules/DATA_CONTRACT_V1.md` §10 계획 경로·명령 표다.

---

## Description(설명): <br>
TradeSentry 저장소를 평가 룰북 `docs/eval/RULEBOOK.md`의 Part A(팀 채점 규범 `SCORING_GOLDEN_RULE.md`를 TradeSentry 증거로 풀어 쓴 자기채점 규칙)로 채점하는 평가 스킬 ①이다. `[사실: skills/tradesentry-scorecard/SKILL.md frontmatter description]` <br>

This skill is for research and development only. <br>
(연구·개발 전용. 팀이 자기 프로젝트를 채점하는 절차이며 자기채점 점수는 대회 점수가 아니다 `[추론: skills/tradesentry-scorecard/SKILL.md "정본과 이 스킬의 관계"·"금지"]`. 이 영어 문장은 템플릿 고정 문구 `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`이고, 세 이용 자세 가운데 이것을 고른 분류는 `[추론]`) <br>

## Third-Party Community Consideration(제3자 스킬 고지)
<span style="color:#d73a49">This skill is not owned or developed by NVIDIA. This skill has been developed and built to a third-party's requirements for this application and use case; see link to Non-NVIDIA [TradeSentry(저장소 JoeHwangHee/nvidia-hackathon-2026) Agent Card]().</span> <!-- VERIFY: 소유자는 이 저장소의 팀이며 NVIDIA가 아니다(추론 근거: 저장소 소유와 SKILL.md 작성 주체). 팀의 별도 에이전트 카드가 없어 링크가 비어 있다. 소유자 표기 문구와 링크(없으면 "없음")를 확인하고 이 표시를 지울 것 --> <br>
(이 스킬은 NVIDIA가 소유하거나 개발하지 않았다. TradeSentry 팀이 이 저장소의 용도에 맞춰 만들었다 `[추론: 저장소 소유 JoeHwangHee/nvidia-hackathon-2026(스킬 사전 §1 표)과 SKILL.md 작성 주체로 판단]`. 영어 고지 문장은 템플릿 고정 문구 `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`이며, 소유자 표기 문구와 카드 링크는 VERIFY 표시대로 `[미확인]`이다.) <br>

### License/Terms of Use(라이선스·이용 조건): <br>
<!-- VERIFY: license_identifier=null. 2026-09-26(토) 저장소에 LICENSE·NOTICE 파일이 없고 SKILL.md frontmatter에도 license 키가 없어 생성기 규칙대로 비웠다. 공개 저장소 방식 결정(로드맵 P2) 때 라이선스를 정하고 이 절을 채울 것 -->
(저장소에 LICENSE·NOTICE 파일과 SKILL.md frontmatter `license` 키가 없어 식별자를 비웠다 `[사실: 2026-09-26(토) 작업 기록 — worktree 루트 목록과 frontmatter 확인]`. 라이선스는 정해지면 채운다 `[미확인]`. 비우는 규칙은 `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`) <br>

## Use Case(용도): <br>
TradeSentry 팀의 오케스트레이터와 보조 에이전트(개발자)가 MVP 시험 뒤·룰북 `RB-1` 동결 뒤·제출 전의 세 회차에, 저장소의 커밋된 증거만 읽어 규범 G1~G6 하드 게이트, 채점 지표 20개(0/1/3/5)와 `2e` 표시, CAP·TIE 규칙과 판정 밴드, 컴포넌트 삭제 시험 답을 판정마다 근거 한 줄과 증거 경로를 붙여 결과 파일로 남길 때 쓴다. 성능 평가(채점 대상 실행·정답 대조 채점)는 하지 않는다. `[사실: skills/tradesentry-scorecard/SKILL.md "언제 쓰나"·"입력"·frontmatter description]` `[추론: 한두 문장으로 요약한 표현]` <br>

### Deployment Geography for Use(사용 지역): <br>
Global <br>
(문서에 지역 제한이 없어 생성기 기본값을 썼다. 채점 대상 자료는 대한민국 관세청 수입통계다 `[추론]`. 기본값 Global 규칙은 `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`) <br>

## Requirements / Dependencies(요구 사항·의존성): <br>
**Requires API Key or External Credential:** [No] <br>
**Credential Type(s):** [None] <br>  

Do not include secrets in prompts/logs/output; use least-privilege credentials; rotate keys as appropriate. See skill body for more details. <br>
(비밀값을 프롬프트·로그·출력에 넣지 않는다. 이 스킬은 `.env`와 봉인 폴더를 읽지 않고 키는 변수 이름(`NVIDIA_API_KEY`, `DATA_GO_KR_SERVICE_KEY`)으로만 말한다. 직접 돌리는 것은 규범 G4 확인용 시험·검사 명령과 `real_dev` 채점기 재계산뿐이며 둘은 키 없이 돈다 `[사실: skills/tradesentry-scorecard/SKILL.md "읽지 않는 것"·"금지"]`. 위 영어 문장은 템플릿 고정 문구 `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`이고, 필요 여부·종류의 분류(Yes/No, API key/None)는 스타일 가이드 규칙을 적용한 `[추론]`) <br>

## Known Risks and Mitigations(알려진 위험과 완화): <br>
Risk: Review before execution as proposals could introduce incorrect or misleading guidance into skills. <br>
Mitigation: Review and scan skill before deployment. <br>
(템플릿 고정 문구. 위험: 검토 없이 실행하면 잘못된 지침이 스킬에 들어갈 수 있다. 완화: 배포 전 스킬을 검토·검사한다. `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`) <br>

## Reference(s)(참고 문서): <br>
- [평가 룰북 docs/eval/RULEBOOK.md — Part A(A1~A5)와 부록](../../docs/eval/RULEBOOK.md) <br>
- [팀 채점 규범 SCORING_GOLDEN_RULE.md — §2~§4, §7](../../SCORING_GOLDEN_RULE.md) <br>
- [공용 자료 계약 docs/rules/DATA_CONTRACT_V1.md — §10 계획 경로·명령 표](../../docs/rules/DATA_CONTRACT_V1.md) <br>
- [스킬 사전 docs/eval/SKILL_DICTIONARY.md — §1 상태 열, §2.1, §3.2, §3.4](../../docs/eval/SKILL_DICTIONARY.md) <br>
- [개발 플랜 docs/plan/DEV_PLAN.md — §1, §5.4](../../docs/plan/DEV_PLAN.md) <br>
- [로드맵 docs/plan/ROADMAP.md — MVP 합격 체크리스트](../../docs/plan/ROADMAP.md) <br>

(위 목록은 skills/tradesentry-scorecard/SKILL.md 본문이 가리키는 문서다 `[사실: skills/tradesentry-scorecard/SKILL.md]`. 각 문서의 절 표시는 SKILL.md가 가리키는 곳이다.) <br>

## Skill Output(스킬 출력): <br>
**Output Type(s):** [Files, Analysis] `[추론: 생성기 스타일 가이드의 분류 어휘로 분류 `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`]` <br>
**Output Format:** [Markdown] `[사실: skills/tradesentry-scorecard/SKILL.md "출력"]` <br>
**Output Parameters:** [1D] `[추론: 생성기 스타일 가이드의 분류 어휘로 분류 `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`]` <br>
**Other Properties Related to Output:** [회차마다 새 실행 폴더 `outputs/scorecard-{시각}/`를 배타 생성(이미 있으면 실패하는 방식)해 `scorecard-{시각}.md` 한 파일을 쓰고(덮어쓰기 금지), 비밀값·로컬 경로 검사를 통과한 그 파일만 같은 이름의 폴더 `artifacts/scorecard/scorecard-{시각}/`로 증거 복사해 커밋한다. 양식은 룰북 A3 "자기채점 결과 파일 양식"이고 점수는 0/1/3/5만 쓴다. 게이트 FAIL이 있으면 머리 정보·게이트·해소 조건만 남긴다] `[사실: skills/tradesentry-scorecard/SKILL.md "출력"·"9단계. 저장과 커밋"]` <br>

## Skill Version(s)(스킬 버전): <br>
0.1.0 (source: pyproject.toml, 저장소 판) · 8adad56 (source: git SHA, `SKILL.md` 마지막 변경 커밋, committed 2026-09-25) `[사실: pyproject.toml의 version, git log -1 -- skills/tradesentry-scorecard/SKILL.md]` <br>
(SKILL.md frontmatter에 version 키가 없고 CHANGELOG·git tag가 없어 생성기 규칙의 다음 출처를 썼다. `[사실: skills/tradesentry-scorecard/SKILL.md frontmatter, worktree에 CHANGELOG·git tag 없음]`. 출처 우선순위는 `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`) <br>

---

## 부록 A. 검토표(review table, 생성기 작업 순서 5단계)

생성기는 필드마다 신뢰도(`HIGH` 원문 그대로 / `INFERRED` 추론·분류 / `HUMAN-REQUIRED` 출처 없음)와 검토 필요 여부를 표로 남기라고 한다. `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]` 표의 Confidence는 이 저장소의 근거 태그에 이렇게 대응한다 `[DESIGN]`: `HIGH` = `[사실: Source Files 열의 파일]`, `INFERRED` = `[추론]`, `HUMAN-REQUIRED` = `[미확인]`.

| Section(절) | Field(필드) | Confidence(신뢰도) | Review Needed(검토 필요) | Reasoning(이유) | Source Files(출처) |
|---|---|---|---|---|---|
| Description | `skill_name` | HIGH | No | frontmatter `name` | `skills/tradesentry-scorecard/SKILL.md` |
| Description | `skill_kind` | HIGH | No | 생성기 기본값 `Agent` | 생성기 `references/style-guide.md` |
| Description | `description_sentence` | HIGH | No | frontmatter `description` 첫 문장 그대로 | `skills/tradesentry-scorecard/SKILL.md` |
| Description | `usage_posture` | INFERRED | Yes | `research_dev`. 자기채점 절차이며 점수가 대회 점수가 아니라고 명시. 운영 배포 없음(`CLAUDE.md` 프로젝트 개요) | `skills/tradesentry-scorecard/SKILL.md`, `CLAUDE.md` |
| Third-Party Community Consideration | `owner` | INFERRED | Yes | `third_party`. 저장소 소유가 NVIDIA 조직이 아니고 팀 에이전트 카드가 없어 링크 비움 | `docs/eval/SKILL_DICTIONARY.md` §1 표 |
| License/Terms of Use | `license_identifier` | HUMAN-REQUIRED | Yes | `null`. LICENSE·NOTICE·frontmatter `license` 없음 | None |
| Use Case | `use_case` | INFERRED | Yes | SKILL.md "언제 쓰나"·"입력"·frontmatter를 한 문장으로 요약 | `skills/tradesentry-scorecard/SKILL.md` |
| Deployment Geography | `deployment_geography` | INFERRED | Yes | 문서에 지역 제한 없음 → 기본값 `Global` | 생성기 `references/style-guide.md` |
| Requirements / Dependencies | `credential_requirements.requires_api_key_or_credential` | INFERRED | Yes | `no`. `.env`를 읽지 않고 채점 대상 실행을 돌리지 않으며, 허용된 시험·검사·채점기 재계산은 키 없이 돈다 | `skills/tradesentry-scorecard/SKILL.md` "읽지 않는 것"·"금지", `skills/tradesentry-eval/SKILL.md` "채점" |
| Requirements / Dependencies | `credential_requirements.credential_types` | INFERRED | Yes | `["None"]`(상태 `no`와 짝) | 같은 곳 |
| Reference(s) | `references` | HIGH | No | SKILL.md "읽는 문서"에 적힌 문서 | `skills/tradesentry-scorecard/SKILL.md` |
| Skill Output | `output` | HIGH | No | SKILL.md "출력"·"9단계. 저장과 커밋" 원문 | `skills/tradesentry-scorecard/SKILL.md` |
| Skill Version(s) | `skill_version` | INFERRED | Yes | frontmatter·CHANGELOG·tag 없음 → pyproject 판과 git SHA | `pyproject.toml`, git 이력 |
| (생략) | `evaluation` | — | — | 이 스킬 자체를 평가한 기록이 없어 생략(생성기 규칙: 근거 없으면 객체를 넣지 않음) | None |
