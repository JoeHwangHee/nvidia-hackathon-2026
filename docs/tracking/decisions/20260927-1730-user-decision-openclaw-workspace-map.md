# 사용자 결정: 디렉토리 구조는 옮기지 않고 README 3절에 OpenClaw 작업 공간 대응표를 더한다

사용자(팀장)가 2026-09-27(일) 17:2x 채팅으로 화면 캡처 한 장을 보여 주며 물었다. 캡처에는 교육 미션 강의(NVIDIA DLI "Securing Agents with NemoClaw and OpenShell")의 OpenClaw 작업 공간 그림과 폴더 배치 예시 화면이 있었다. 오케스트레이터가 세 선택지를 제시했고, 사용자는 "옮기지 않고 대응표만 추가"를 골랐다.

용어

- OpenClaw 작업 공간: OpenClaw 에이전트가 실행 문맥으로 읽는 파일 모음이다. 교육 과정 그림에는 `SOUL.md`·`AGENTS.md`·`TOOLS.md`·`USER.md`·`HEARTBEAT.md`·`skills/<name>/SKILL.md`·`memory/`가 있다. NemoClaw 시연 샌드박스에서는 `/sandbox/.openclaw/workspace/`이며, `nemoclaw <샌드박스> skill install <스킬 폴더>`가 스킬 폴더를 그 아래 `skills/<이름>/`에 넣는다(X1 기록 `artifacts/openshell/violation_tests.md`).
- 정적 계층: 샌드박스를 만들 때 고정되는 정책 부분(파일시스템 규칙 등)이다. 시연 샌드박스의 정적 계층은 NemoClaw 판이 정한다(결정 기록 `20260925-0530-model-decision-mt5-sandbox.md`).

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-27(일) 17:2x KST(채팅) |
| 요청 | "이 이미지대로 디렉토리 구조 변경가능해?" |
| 검토한 대안 | ① 그대로 두기(오케스트레이터 권장). ② 파일은 옮기지 않고 README 3절에 대응표만 더하기. ③ 그림대로 전면 개편(예: 런타임 스킬을 `nemoclaw/` 아래로, `configs/openshell/`을 `openshell/`로, `eval/`을 `evals/`로) |
| 결정 | ②. 파일은 옮기지 않는다. README 3절에 "OpenClaw 작업 공간과 이 저장소" 대응표를 더하고, English summary의 NemoClaw 항목에 한 구절을 더한다. 옛 경로에 안내용 빈 파일이나 링크를 남기는 방식은 쓰지 않는다(제출물이 가리키는 곳에 진짜 정책·스킬이 아닌 것이 보이게 된다) |
| 이유 | ① 제출물이 지금 경로를 가리킨다. 신청서 칸 3(Tech Stack)과 서비스 파일(`docs/submission/SUBMISSION_FORM.md`의 해당 절)에 `skills/<이름>/SKILL.md`, `skills/<이름>/<이름>-card.md`, `configs/openshell/policy.yaml`, `configs/nat/workflow.yml`, `eval/scorer/`, `artifacts/openshell/`이 적혀 있고, 제출물은 고칠 수 없다. ② 동결된 채점기 `eval/scorer/summary.py`가 요약에 `configs/openshell/policy.yaml` 경로와 sha256을 쓰고, 커밋된 위반 시험표·채점 요약도 경로와 지문을 기록했다. 이 층은 고치지 않는다. ③ 옮길 범위가 넓다. `configs/openshell/`을 적은 추적 파일만 53개이고, 스킬 3개 경로는 각각 23·32·21개 파일에 나온다. 마감(2026-09-28(월) 23:59) 하루 전이다. ④ 교육 과정 그림은 저장소 배치가 아니라 샌드박스 안 작업 공간이다. 이 저장소가 채운 자리는 스킬 하나이고, 나머지 자리(`SOUL.md`·`TOOLS.md`·`USER.md`·`HEARTBEAT.md`·`memory/`)는 이 프로젝트에서 만들거나 시험한 적이 없다. 저장소 맨 위 `AGENTS.md`는 Codex 안내문이라 이름이 겹친다 |
| 결정 주체 | 사용자(팀장). 실행은 오케스트레이터 |
| 공용 약속 여부 | 아니다. 자료 계약의 값·상태값·명령과 제출서 주장 문구는 바뀌지 않는다 |
| 영향 | `README.md` 3절(대응표와 설명 두 문장)과 English summary 한 구절, 이 결정 기록, 결정 색인, status |

## 대응표에 적은 것

- 스킬 자리: 런타임 스킬 `skills/tradesentry/SKILL.md`. 시연에서 OpenClaw 에이전트가 이 스킬을 읽고 샌드박스 안 CLI를 불렀다(자기채점 `1c` 행과 status의 MVP 완성 표 1번). 스킬 폴더를 작업 공간에 넣는 명령은 X1 기록에 있는 `nemoclaw <샌드박스> skill install <스킬 폴더>`로 적었다 `[사실: artifacts/openshell/violation_tests.md]`.
- 나머지 자리: "이 저장소에서 만들지 않았다"로만 적었다. NemoClaw가 시연 샌드박스의 이 파일들을 기본으로 어떻게 두는지는 확인하지 않았으므로 적지 않았다 `[미확인]`.
- `HEARTBEAT.md`: 고정 스냅샷을 쓰는 데모라 주기 작업이 없다고 적었다(README 1절 범위의 "실시간 수집 없음"과 같은 뜻).
- 작업 공간 밖: 시연 샌드박스는 네트워크 정책만 `configs/openshell/policy_demo_network.yaml`로 정하고, 정적 계층은 NemoClaw 판이 정하므로 커밋하지 않았다고 적었다 `[사실: 결정 기록 20260925-0530-model-decision-mt5-sandbox.md]`.

## 남은 것

- 구조 개편(③)이 다시 필요하면 대회가 끝난 뒤, 제출물이 가리키는 경로를 더 쓰지 않게 된 때 따로 정한다.
- 병합하면 공개 저장소에 바로 드러난다.
