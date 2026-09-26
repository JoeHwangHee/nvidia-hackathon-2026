# tradesentry-eval 거버넌스 카드(skill card)

평가 스킬 ② `tradesentry-eval`(평가 룰북 Part B의 성능 평가를 사전 점검 → 실행 → 채점 → 결과 보고 순으로 수행하는 오케스트레이터용 Agent Skills 형식의 작업 절차)의 거버넌스 카드(스킬이 무엇을 하고 무엇을 읽고 쓰는지 등 능력 범위를 밝히는 카드)다. NVIDIA 공식 스킬 `skill-card-generator`(기존 스킬 디렉터리에서 거버넌스 카드를 만드는 스킬)의 카드 형식을 따랐다: 절 제목과 순서는 생성기 템플릿 `references/skill-card.md.j2`, 항목 값의 규칙은 `references/style-guide.md`, 검토표는 생성기 SKILL.md의 작업 순서 5단계다. **생성기 형식을 따라 수동 작성** `[사실: 2026-09-26(토) 설치 명령(npx skills add NVIDIA/skills --skill skill-card-generator)이 작업 에이전트의 실행 권한 정책(신뢰하지 않는 코드 설치 차단)으로 거부돼 설치하지 못했고, 생성기의 SKILL.md·템플릿·스타일 가이드·예시 카드를 GitHub NVIDIA/skills 저장소(해당 폴더의 마지막 커밋 2a23a90, 2026-07-01)에서 읽어 같은 형식으로 손으로 채웠다. 생성기의 discover·render·validate 스크립트는 돌리지 않았다]`.

- 값은 `skills/tradesentry-eval/SKILL.md` 본문에서 가져온 사실만 적었다. 이 카드에는 규칙과 절차만 담고, 봉인 자료(개발 중 보지 않도록 저장소 밖 봉인 폴더에 두는 평가 자료)의 경로 값·파일 이름·내용은 적지 않는다. 결과 숫자는 적지 않는다. `[사실: 아래 각 절의 태그가 근거 위치를 가리킨다]`
- 절 제목은 생성기 템플릿의 영어 제목을 그대로 두고 괄호에 한국어 설명을 붙였다. 템플릿이 고정한 영어 문장은 그대로 두고 아래 줄에 한국어 설명을 달았다. `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`
- 붉은 `VERIFY` 표시(생성기가 추론·기본값 항목에 붙이는 사람 확인 표시)는 소유자(사용자)가 확인한 뒤 지운다. 생성기 규칙상 표시가 남은 카드는 제출 전 검증에서 실패한다. `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`
- 카드 파일 위치 `skills/tradesentry-eval/tradesentry-eval-card.md`는 생성기 SKILL.md "Examples"의 출력 형식(대상 스킬 폴더 안 `<스킬 이름>-card.md`)을 따랐다 `[사실: 생성기 SKILL.md Examples의 --out 인자]`. 경로의 정본은 `docs/rules/DATA_CONTRACT_V1.md` §10 계획 경로·명령 표다.

---

## Description(설명): <br>
TradeSentry 평가 룰북 Part B(성능 평가)를 사전 점검 → 채점 대상 실행(OpenShell 샌드박스 안) → 정답 대조 채점(샌드박스 밖 독립 채점기) → 결과 보고 순으로 안전하게 수행하는 오케스트레이터용 지침이다. `[사실: skills/tradesentry-eval/SKILL.md frontmatter description]` <br>

This skill is for research and development only. <br>
(연구·개발 전용. 대회 제출용 성능 평가 절차이며, 이 스킬이 내는 어떤 숫자도 부정·위법·원산지 판정의 정확도가 아니다 `[추론: skills/tradesentry-eval/SKILL.md 머리말]`. 이 영어 문장은 템플릿 고정 문구 `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`이고, 세 이용 자세 가운데 이것을 고른 분류는 `[추론]`) <br>

## Third-Party Community Consideration(제3자 스킬 고지)
<span style="color:#d73a49">This skill is not owned or developed by NVIDIA. This skill has been developed and built to a third-party's requirements for this application and use case; see link to Non-NVIDIA [TradeSentry(저장소 JoeHwangHee/nvidia-hackathon-2026) Agent Card]().</span> <!-- VERIFY: 소유자는 이 저장소의 팀이며 NVIDIA가 아니다(추론 근거: 저장소 소유와 SKILL.md 작성 주체). 팀의 별도 에이전트 카드가 없어 링크가 비어 있다. 소유자 표기 문구와 링크(없으면 "없음")를 확인하고 이 표시를 지울 것 --> <br>
(이 스킬은 NVIDIA가 소유하거나 개발하지 않았다. TradeSentry 팀이 이 저장소의 용도에 맞춰 만들었다 `[추론: 저장소 소유 JoeHwangHee/nvidia-hackathon-2026(스킬 사전 §1 표)과 SKILL.md 작성 주체로 판단]`. 영어 고지 문장은 템플릿 고정 문구 `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`이며, 소유자 표기 문구와 카드 링크는 VERIFY 표시대로 `[미확인]`이다.) <br>

### License/Terms of Use(라이선스·이용 조건): <br>
<!-- VERIFY: license_identifier=null. 2026-09-26(토) 저장소에 LICENSE·NOTICE 파일이 없고 SKILL.md frontmatter에도 license 키가 없어 생성기 규칙대로 비웠다. 공개 저장소 방식 결정(로드맵 P2) 때 라이선스를 정하고 이 절을 채울 것 -->
(저장소에 LICENSE·NOTICE 파일과 SKILL.md frontmatter `license` 키가 없어 식별자를 비웠다 `[사실: 2026-09-26(토) 작업 기록 — worktree 루트 목록과 frontmatter 확인]`. 라이선스는 정해지면 채운다 `[미확인]`. 비우는 규칙은 `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`) <br>

## Use Case(용도): <br>
TradeSentry 팀의 오케스트레이터(개발자)가 dev20·`real_dev`(개발 묶음)와 `RB-1` 동결 뒤 holdout40·`real_sealed`(봉인 묶음)의 성능 평가를 할 때 쓴다. 구성요소·해시·동결 조건을 사전 점검한 뒤 OpenShell 샌드박스 안 TradeSentry CLI(`tradesentry run-case`·`evaluate`, 봉인 묶음은 샌드박스 밖 실행기 `python -m tradesentry.evaluation.sealed_runner`)로 채점 대상 실행을 돌리고, 샌드박스 밖 독립 채점기(`python -m eval.scorer --run <run_dir>`)로 정답 대조 채점을 한 번 하고, 룰북 B7 양식으로 결과를 보고한다. 구현 전이면 사전 점검에서 멈추고, 동결 조건이 하나라도 빠지면 봉인 채점을 거부한다. `[사실: skills/tradesentry-eval/SKILL.md "언제 쓰나"·"실행"·"채점"·머리말]` `[추론: 한두 문장으로 요약한 표현]` <br>

### Deployment Geography for Use(사용 지역): <br>
Global <br>
(문서에 지역 제한이 없어 생성기 기본값을 썼다. 평가 자료는 대한민국 관세청 수입통계 스냅샷과 그로부터 만든 합성 자료다 `[추론]`. 기본값 Global 규칙은 `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`) <br>

## Requirements / Dependencies(요구 사항·의존성): <br>
**Requires API Key or External Credential:** [Yes] <br>
**Credential Type(s):** [API key] <br>  

Do not include secrets in prompts/logs/output; use least-privilege credentials; rotate keys as appropriate. See skill body for more details. <br>
(채점 대상 실행의 모델 모드(`agent`·`full`·`freeform`)는 샌드박스 안 CLI가 NVIDIA 추론 엔드포인트(NIM)를 부르므로 NVIDIA API 키가 필요하다. 다만 이 스킬을 따르는 에이전트는 키 값을 읽거나 다루지 않는다: 키는 OpenShell 게이트웨이의 provider(등록한 자격 증명 묶음) 저장소에서 샌드박스 안 감독 프로세스의 정책 프록시가 요청 시점에 자리표시 값과 바꿔 넣고(credential placeholder rewrite), 채점기와 샌드박스 밖 실행기는 키 변수를 뺀 환경(`env -u NVIDIA_API_KEY -u DATA_GO_KR_SERVICE_KEY`)에서 돌며 `.env`를 읽지 않는다. 문서·기록·PR에는 변수 이름만 쓴다 `[사실: skills/tradesentry-eval/SKILL.md "실행"의 샌드박스, "채점", "금지"]`. 위 영어 문장은 템플릿 고정 문구 `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`이고, 필요 여부·종류의 분류(Yes/No, API key/None)는 스타일 가이드 규칙을 적용한 `[추론]`) <br>

## Known Risks and Mitigations(알려진 위험과 완화): <br>
Risk: Review before execution as proposals could introduce incorrect or misleading guidance into skills. <br>
Mitigation: Review and scan skill before deployment. <br>
(템플릿 고정 문구. 위험: 검토 없이 실행하면 잘못된 지침이 스킬에 들어갈 수 있다. 완화: 배포 전 스킬을 검토·검사한다. `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`) <br>

## Reference(s)(참고 문서): <br>
- [평가 룰북 docs/eval/RULEBOOK.md — Part B(B1~B7), A5](../../docs/eval/RULEBOOK.md) <br>
- [공용 자료 계약 docs/rules/DATA_CONTRACT_V1.md — §4, §7, §8, §9, §10, §12](../../docs/rules/DATA_CONTRACT_V1.md) <br>
- [병렬 개발 규칙 docs/rules/PARALLEL_DEV_RULES.md — §6 봉인 자료, §7 실자료 분할](../../docs/rules/PARALLEL_DEV_RULES.md) <br>
- [에이전트 운용 규칙 docs/rules/AGENT_OPS.md — §1.2, §1.4, §7](../../docs/rules/AGENT_OPS.md) <br>
- [개발 플랜 docs/plan/DEV_PLAN.md — §3.2, §4, §5.4, §9](../../docs/plan/DEV_PLAN.md) <br>
- [스킬 사전 docs/eval/SKILL_DICTIONARY.md — §3.3, §3.4](../../docs/eval/SKILL_DICTIONARY.md) <br>
- [로드맵 docs/plan/ROADMAP.md — MVP 합격 체크리스트](../../docs/plan/ROADMAP.md) <br>

(위 목록은 skills/tradesentry-eval/SKILL.md 본문이 가리키는 문서다 `[사실: skills/tradesentry-eval/SKILL.md]`. 각 문서의 절 표시는 SKILL.md가 가리키는 곳이다.) <br>

## Skill Output(스킬 출력): <br>
**Output Type(s):** [Shell commands, Files, Analysis] `[추론: 생성기 스타일 가이드의 분류 어휘로 분류]` `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]` <br>
**Output Format:** [JSONL(채점기 결과 `scorer_results-{시각}.jsonl`, `scorer_claims-{시각}.jsonl`)와 Markdown(결과 요약 `scorer_summary-{시각}.md`, 결정 기록)] `[사실: skills/tradesentry-eval/SKILL.md "채점"의 산출물 표]` <br>
**Output Parameters:** [1D] `[추론: 생성기 스타일 가이드의 분류 어휘로 분류]` `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]` <br>
**Other Properties Related to Output:** [채점 대상 실행의 도메인 출력은 실행 폴더 `outputs/{실행명}/`(봉인 묶음은 자료 계약 §10.3 N10이 정한 봉인 출력 자리)에 남고 커밋하지 않는다. 채점기는 자기 출력을 `outputs/score-{시각}/`에 쓰고, 그 `scorer_*` 파일과 재채점용 보고서 원문(`{run_id}/` 아래 허용 목록 파일)만 `artifacts/eval/score-{시각}/`로 증거 복사해 커밋한다. 실패·미실행·timeout·invalid도 분모에 남긴다. 봉인 묶음 출력과 그 채점기 출력은 금지 해제 조건(자료 계약 §10.3 N10) 전에는 열지 않고 커밋하지 않는다. 봉인 사건(해시 대조·반입·실행 시작·채점 시작·채점 완료 등)은 결정 기록에 날짜·주체·파일 수·해시 대조 결과로 남기고 봉인 자료 내용은 적지 않는다] `[사실: skills/tradesentry-eval/SKILL.md "이름과 출력 위치"·"채점"의 산출물 표·"보고와 커밋"]` <br>

## Skill Version(s)(스킬 버전): <br>
0.1.0 (source: pyproject.toml, 저장소 판) · c557540 (source: git SHA, `SKILL.md` 마지막 변경 커밋, committed 2026-09-26) `[사실: pyproject.toml의 version, git log -1 -- skills/tradesentry-eval/SKILL.md]` <br>
(SKILL.md frontmatter에 version 키가 없고 CHANGELOG·git tag가 없어 생성기 규칙의 다음 출처를 썼다. `[사실: skills/tradesentry-eval/SKILL.md frontmatter, worktree에 CHANGELOG·git tag 없음]`. 출처 우선순위는 `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]`) <br>

---

## 부록 A. 검토표(review table, 생성기 작업 순서 5단계)

생성기는 필드마다 신뢰도(`HIGH` 원문 그대로 / `INFERRED` 추론·분류 / `HUMAN-REQUIRED` 출처 없음)와 검토 필요 여부를 표로 남기라고 한다. `[사실: NVIDIA/skills skill-card-generator references/skill-card.md.j2·references/style-guide.md (커밋 2a23a90)]` 표의 Confidence는 이 저장소의 근거 태그에 이렇게 대응한다 `[DESIGN]`: `HIGH` = `[사실: Source Files 열의 파일]`, `INFERRED` = `[추론]`, `HUMAN-REQUIRED` = `[미확인]`.

| Section(절) | Field(필드) | Confidence(신뢰도) | Review Needed(검토 필요) | Reasoning(이유) | Source Files(출처) |
|---|---|---|---|---|---|
| Description | `skill_name` | HIGH | No | frontmatter `name` | `skills/tradesentry-eval/SKILL.md` |
| Description | `skill_kind` | HIGH | No | 생성기 기본값 `Agent` | 생성기 `references/style-guide.md` |
| Description | `description_sentence` | HIGH | No | frontmatter `description` 첫 문장 그대로 | `skills/tradesentry-eval/SKILL.md` |
| Description | `usage_posture` | INFERRED | Yes | `research_dev`. 대회 제출용 평가 절차. 운영 배포 없음(`CLAUDE.md` 프로젝트 개요) | `skills/tradesentry-eval/SKILL.md`, `CLAUDE.md` |
| Third-Party Community Consideration | `owner` | INFERRED | Yes | `third_party`. 저장소 소유가 NVIDIA 조직이 아니고 팀 에이전트 카드가 없어 링크 비움 | `docs/eval/SKILL_DICTIONARY.md` §1 표 |
| License/Terms of Use | `license_identifier` | HUMAN-REQUIRED | Yes | `null`. LICENSE·NOTICE·frontmatter `license` 없음 | None |
| Use Case | `use_case` | INFERRED | Yes | SKILL.md "언제 쓰나"·"실행"·"채점"을 요약 | `skills/tradesentry-eval/SKILL.md` |
| Deployment Geography | `deployment_geography` | INFERRED | Yes | 문서에 지역 제한 없음 → 기본값 `Global` | 생성기 `references/style-guide.md` |
| Requirements / Dependencies | `credential_requirements.requires_api_key_or_credential` | INFERRED | Yes | `yes`. 샌드박스 안 CLI의 NIM 호출에 NVIDIA API 키가 필요(스타일 가이드의 "암묵적 인프라 자격 증명" 규칙). 에이전트·채점기·실행기는 키 값을 다루지 않음 | `skills/tradesentry-eval/SKILL.md` "실행"의 샌드박스, "채점", "금지" |
| Requirements / Dependencies | `credential_requirements.credential_types` | INFERRED | Yes | `["API key"]`. 변수 이름은 적지 않음(생성기 규칙) | 같은 곳 |
| Reference(s) | `references` | HIGH | No | SKILL.md "줄여 부르는 문서" 표 | `skills/tradesentry-eval/SKILL.md` |
| Skill Output | `output` | HIGH | No | SKILL.md "이름과 출력 위치", "채점"의 산출물 표, "보고와 커밋" 원문 | `skills/tradesentry-eval/SKILL.md` |
| Skill Version(s) | `skill_version` | INFERRED | Yes | frontmatter·CHANGELOG·tag 없음 → pyproject 판과 git SHA | `pyproject.toml`, git 이력 |
| (생략) | `evaluation` | — | — | 이 스킬 자체를 평가한 기록이 없어 생략(생성기 규칙: 근거 없으면 객체를 넣지 않음). 이 스킬이 재는 TradeSentry 성능 숫자는 스킬 평가가 아니며 카드에 적지 않는다 | None |
