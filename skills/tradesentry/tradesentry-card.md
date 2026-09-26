# tradesentry 거버넌스 카드(skill card)

런타임 스킬 `tradesentry`(NemoClaw(OpenShell 위에서 에이전트를 돌리는 NVIDIA 참조 스택)의 OpenClaw 에이전트가 불러 OpenShell 샌드박스 안 TradeSentry CLI로 잇는 Agent Skills 형식의 작업 절차)의 거버넌스 카드(스킬이 무엇을 하고 무엇을 읽고 쓰는지 등 능력 범위를 밝히는 카드)다. NVIDIA 공식 스킬 `skill-card-generator`(기존 스킬 디렉터리에서 거버넌스 카드를 만드는 스킬)의 카드 형식을 따랐다: 절 제목과 순서는 생성기 템플릿 `references/skill-card.md.j2`, 항목 값의 규칙은 `references/style-guide.md`, 검토표는 생성기 SKILL.md의 작업 순서 5단계다. **생성기 형식을 따라 수동 작성** `[사실: 2026-09-26(토) 설치 명령(npx skills add NVIDIA/skills --skill skill-card-generator)이 작업 에이전트의 실행 권한 정책(신뢰하지 않는 코드 설치 차단)으로 거부돼 설치하지 못했고, 생성기의 SKILL.md·템플릿·스타일 가이드·예시 카드를 GitHub NVIDIA/skills 저장소(해당 폴더의 마지막 커밋 2a23a90, 2026-07-01)에서 읽어 같은 형식으로 손으로 채웠다. 생성기의 discover·render·validate 스크립트는 돌리지 않았다]`.

- 값은 `skills/tradesentry/SKILL.md` 본문에서 가져온 사실만 적었다. 없는 능력을 적지 않았고 결과 숫자는 적지 않는다.
- 절 제목은 생성기 템플릿의 영어 제목을 그대로 두고 괄호에 한국어 설명을 붙였다. 템플릿이 고정한 영어 문장은 그대로 두고 아래 줄에 한국어 설명을 달았다.
- 붉은 `VERIFY` 표시(생성기가 추론·기본값 항목에 붙이는 사람 확인 표시)는 소유자(사용자)가 확인한 뒤 지운다. 생성기 규칙상 표시가 남은 카드는 제출 전 검증에서 실패한다.
- 카드 파일 위치 `skills/tradesentry/tradesentry-card.md`는 생성기 SKILL.md "Examples"의 출력 형식(대상 스킬 폴더 안 `<스킬 이름>-card.md`)을 따랐다 `[사실: 생성기 SKILL.md Examples의 --out 인자]`. 경로의 정본은 `docs/rules/DATA_CONTRACT_V1.md` §10 계획 경로·명령 표다.

---

## Description(설명): <br>
운영자가 관세청 수입통계 경보 목록을 보거나 경보 사례 1건을 조사해 달라고 하면, OpenShell 샌드박스 안 TradeSentry CLI의 `detect`(경보 목록)나 `run-case`(사례 1건 조사)만 한 번 실행하고, CLI가 낸 표준 출력·보고서·종료 코드를 고치지 않고 그대로 전하는 TradeSentry 런타임 스킬이다. <br>

This skill is for demonstration purposes and not for production usage. <br>
(시연용이며 운영 배포용이 아니다. SKILL.md가 "시연 경로 전용"이라고 명시하고, 결과는 부정·위법·원산지 판정이나 실제 통관 조치가 아니다 `[사실: SKILL.md 머리말]`) <br>

## Third-Party Community Consideration(제3자 스킬 고지)
<span style="color:#d73a49">This skill is not owned or developed by NVIDIA. This skill has been developed and built to a third-party's requirements for this application and use case; see link to Non-NVIDIA [TradeSentry(저장소 JoeHwangHee/nvidia-hackathon-2026) Agent Card]().</span> <!-- VERIFY: 소유자는 이 저장소의 팀이며 NVIDIA가 아니다(추론 근거: 저장소 소유와 SKILL.md 작성 주체). 팀의 별도 에이전트 카드가 없어 링크가 비어 있다. 소유자 표기 문구와 링크(없으면 "없음")를 확인하고 이 표시를 지울 것 --> <br>
(이 스킬은 NVIDIA가 소유하거나 개발하지 않았다. TradeSentry 팀이 이 저장소의 용도에 맞춰 만들었다.) <br>

### License/Terms of Use(라이선스·이용 조건): <br>
<!-- VERIFY: license_identifier=null. 2026-09-26(토) 저장소에 LICENSE·NOTICE 파일이 없고 SKILL.md frontmatter에도 license 키가 없어 생성기 규칙대로 비웠다. 공개 저장소 방식 결정(로드맵 P2) 때 라이선스를 정하고 이 절을 채울 것 -->
(저장소에 LICENSE 파일이 없어 식별자를 비웠다. 정해지면 채운다 `[미확인]`) <br>

## Use Case(용도): <br>
NemoClaw 시연 샌드박스의 OpenClaw 에이전트가, 운영자(담당자)의 경보 목록 요청이나 경보 사례 1건 조사 요청을 받아 값 네 가지(`--snapshot` 스냅샷 ID, `--policy` 정책 버전 이름, `--mode` 모드, `--case` 사례 식별자)만 정하고 `/sandbox`에서 `tradesentry detect` 또는 `tradesentry run-case`를 한 번 실행한 뒤, 실행 결과 기록과 보고서의 값(`case_id`, `mode`, `execution_status`, `review_status_final`, `signal_status`, `unresolved_evidence`, 보고서의 `narrative`·`hypotheses`·`claims`)을 글자 그대로 운영자에게 옮길 때 쓴다. 정확도 지표를 내는 채점 대상 실행에는 쓰지 않는다. <br>

### Deployment Geography for Use(사용 지역): <br>
Global <br>
(문서에 지역 제한이 없어 생성기 기본값을 썼다. 다루는 자료는 대한민국 관세청 수입통계다 `[추론]`) <br>

## Requirements / Dependencies(요구 사항·의존성): <br>
**Requires API Key or External Credential:** [Yes] <br>
**Credential Type(s):** [API key] <br>  

Do not include secrets in prompts/logs/output; use least-privilege credentials; rotate keys as appropriate. See skill body for more details. <br>
(`run-case`의 모델 모드는 샌드박스 안 CLI가 NVIDIA 추론 엔드포인트(NIM)를 부르므로 NVIDIA API 키가 필요하다. 다만 이 스킬은 키 값을 다루지 않고 키를 변수 이름으로만 말하며, `.env`·환경변수 목록·자격 증명 파일·하네스 설정 폴더를 읽거나 출력하지 않는다. NVIDIA 추론 요청은 CLI만 하고 스킬은 `curl`·`wget`·파이썬 한 줄 등으로 외부에 요청하지 않는다 `[사실: SKILL.md "하지 않는 것"]`) <br>

## Known Risks and Mitigations(알려진 위험과 완화): <br>
Risk: Review before execution as proposals could introduce incorrect or misleading guidance into skills. <br>
Mitigation: Review and scan skill before deployment. <br>
(템플릿 고정 문구. 위험: 검토 없이 실행하면 잘못된 지침이 스킬에 들어갈 수 있다. 완화: 배포 전 스킬을 검토·검사한다.) <br>

## Reference(s)(참고 문서): <br>
- [개발 플랜 docs/plan/DEV_PLAN.md — §5.2 인터페이스 계약(정본)](../../docs/plan/DEV_PLAN.md) <br>
- [공용 자료 계약 docs/rules/DATA_CONTRACT_V1.md — §4.1 모드 4개, §10 계획 경로·명령 표](../../docs/rules/DATA_CONTRACT_V1.md) <br>
- [로드맵 docs/plan/ROADMAP.md — §3 체크리스트 1번(스킬 호출 성공률)](../../docs/plan/ROADMAP.md) <br>
- [스킬 사전 docs/eval/SKILL_DICTIONARY.md — §3.4 런타임 스킬](../../docs/eval/SKILL_DICTIONARY.md) <br>
- [평가 스킬 ② skills/tradesentry-eval/SKILL.md — 채점 대상 실행은 이 스킬이 맡는다](../tradesentry-eval/SKILL.md) <br>

## Skill Output(스킬 출력): <br>
**Output Type(s):** [Shell commands, Files] <br>
**Output Format:** [CLI 표준 출력·표준 오류·종료 코드를 그대로 전달. 읽는 결과 파일은 JSON(실행 결과 기록 `runlog_run_record-{시각}.json`, 보고서 `reports_render_ko-{시각}.json`)] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [CLI가 샌드박스 안 `/sandbox/outputs/{실행명}/`에 `{도메인명}-{시각}.{확장자}`로 쓴 파일 가운데 실행 결과 기록과 보고서(실행이 `COMPLETED`일 때만)만 읽고, trace(`runlog_trace-{시각}.jsonl`)와 NAT 폴더(`workflow_nat_wrap-{시각}`)는 열지 않는다. 값·숫자·상태값을 고치거나 다시 계산하거나 요약하면서 바꾸지 않고, 설명은 보고서 밖에 "스킬 설명"이라고 밝혀 한두 문장만 덧붙인다. 요청마다 CLI를 실제로 불렀는지(명령 이름)와 `run-case`의 `execution_status`를 답 끝에 한 줄로 남긴다(스킬 호출 성공률의 근거). 샌드박스 밖 `outputs/{실행명}/`으로의 내려받기는 이 스킬이 하지 않는다] <br>

## Skill Version(s)(스킬 버전): <br>
0.1.0 (source: pyproject.toml, 저장소 판) · 4f20bd6 (source: git SHA, `SKILL.md` 마지막 변경 커밋, committed 2026-09-25) <br>
(SKILL.md frontmatter에 version 키가 없고 CHANGELOG·git tag가 없어 생성기 규칙의 다음 출처를 썼다.) <br>

---

## 부록 A. 검토표(review table, 생성기 작업 순서 5단계)

생성기는 필드마다 신뢰도(`HIGH` 원문 그대로 / `INFERRED` 추론·분류 / `HUMAN-REQUIRED` 출처 없음)와 검토 필요 여부를 표로 남기라고 한다.

| Section(절) | Field(필드) | Confidence(신뢰도) | Review Needed(검토 필요) | Reasoning(이유) | Source Files(출처) |
|---|---|---|---|---|---|
| Description | `skill_name` | HIGH | No | frontmatter `name` | `skills/tradesentry/SKILL.md` |
| Description | `skill_kind` | HIGH | No | 생성기 기본값 `Agent` | 생성기 `references/style-guide.md` |
| Description | `description_sentence` | HIGH | No | frontmatter `description`의 두 문장("TradeSentry 런타임 스킬." + 다음 문장)을 한 문장으로 합침. 단어는 그대로 | `skills/tradesentry/SKILL.md` |
| Description | `usage_posture` | INFERRED | Yes | `demonstration`. SKILL.md "이 스킬은 시연 경로 전용이다", 채점 대상 실행에 쓰지 않음 | `skills/tradesentry/SKILL.md` |
| Third-Party Community Consideration | `owner` | INFERRED | Yes | `third_party`. 저장소 소유가 NVIDIA 조직이 아니고 팀 에이전트 카드가 없어 링크 비움 | `docs/eval/SKILL_DICTIONARY.md` §1 표 |
| License/Terms of Use | `license_identifier` | HUMAN-REQUIRED | Yes | `null`. LICENSE·NOTICE·frontmatter `license` 없음 | None |
| Use Case | `use_case` | INFERRED | Yes | SKILL.md "언제 쓰나"·"할 일" 1~4를 요약 | `skills/tradesentry/SKILL.md` |
| Deployment Geography | `deployment_geography` | INFERRED | Yes | 문서에 지역 제한 없음 → 기본값 `Global` | 생성기 `references/style-guide.md` |
| Requirements / Dependencies | `credential_requirements.requires_api_key_or_credential` | INFERRED | Yes | `yes`. CLI의 NVIDIA 추론 요청에 API 키가 필요(스타일 가이드의 "암묵적 인프라 자격 증명" 규칙). 스킬은 키 값을 다루지 않음 | `skills/tradesentry/SKILL.md` "하지 않는 것" |
| Requirements / Dependencies | `credential_requirements.credential_types` | INFERRED | Yes | `["API key"]`. 변수 이름은 적지 않음(생성기 규칙) | 같은 곳 |
| Reference(s) | `references` | HIGH | No | SKILL.md 본문이 가리키는 문서 | `skills/tradesentry/SKILL.md` |
| Skill Output | `output` | HIGH | No | SKILL.md "할 일" 2~7 원문 | `skills/tradesentry/SKILL.md` |
| Skill Version(s) | `skill_version` | INFERRED | Yes | frontmatter·CHANGELOG·tag 없음 → pyproject 판과 git SHA | `pyproject.toml`, git 이력 |
| (생략) | `evaluation` | — | — | 이 스킬 자체를 평가한 기록이 없어 생략(생성기 규칙: 근거 없으면 객체를 넣지 않음). 스킬 호출 성공률은 시연 지표이며 카드에 숫자를 적지 않는다 | None |
