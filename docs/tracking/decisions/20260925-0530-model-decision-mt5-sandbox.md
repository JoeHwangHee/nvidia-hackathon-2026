# MT5 샌드박스·정책·출력 방식의 결정(소유 트랙 M)

로드맵 MT5 두 번째 PR(샌드박스·런타임 스킬·OpenShell 정책·위반 시험, 단위 F3~F7)을 구현하며 소유 트랙(M)이 정한 것을 남긴다. 로드맵 MT5 행이 이 결정 기록에 남기라고 한 일곱 가지(봉인 입력 반입, 샌드박스 출력 방식과 경로별 내려받기, 정책 해시 규칙과 재적용 탐지, 평가 묶음 실행 기간 감사 로그 발췌, download 덮어쓰기 검증과 옮기는 절차, NemoClaw 시연 경로의 실행명 확보, 두 샌드박스의 정책 파일 구성)와 구현 중 정한 네 가지(이미지 정의 위치, 위반 시험 출력 이름, 키 변수 이름, 런타임 스킬 기본값)를 담는다. 이 작업에서는 `openshell`·`nemoclaw`·`docker`·NIM 명령을 돌리지 않았다. 실측이 필요한 곳은 `[미확인]`과 확인 명령(오케스트레이터가 돌린다)으로 적었다. 항목마다 [확정]·[잠정]을 붙였다.

용어

- OpenShell: 에이전트를 격리해 돌리는 NVIDIA 샌드박스 런타임. 정책 YAML로 파일·네트워크·프로세스를 통제하고 감사 로그(`openshell logs`)를 남긴다.
- NemoClaw: OpenShell 위에서 OpenClaw 에이전트를 돌리는 NVIDIA 참조 스택. 시연 샌드박스를 온보딩(처음 설정) 때 만든다.
- 채점 대상 실행 샌드박스: 정확도 지표를 내는 실행용. 개발 평가용(dev20·`real_dev`)과 공식 채점 대상 실행 전용(holdout40·`real_sealed`, `RB-1` 동결 뒤 새로 만든다) 두 가지다.
- 시연 샌드박스: NemoClaw 경로(운영자 → OpenClaw → 런타임 스킬 → CLI) 시연용. 정확도 지표에 쓰지 않는다.
- 정적 계층·동적 계층: 샌드박스를 만들 때 고정되는 정책 부분(`filesystem_policy`·`landlock`·`process`)과 실행 중 `openshell policy set`으로 다시 불러올 수 있는 부분(`network_policies`).
- 라이브 정책 조회: 실제 적용 중인 정책을 읽는 일(`openshell policy get <이름> --full`). 출력은 머리 항목(Version·Hash·Status 등), `---` 줄, 정책 본문 순서다(X1 실측).
- 방식 (나): 샌드박스는 호스트 `outputs/`를 열지 않고 샌드박스 작업 폴더에 쓰며, 샌드박스 밖 프로그램이 `openshell sandbox download`로 받는 방식(자료 계약 §10.3 "그 밖의 약속").
- 자리표시 값: provider(게이트웨이에 등록한 자격 증명 묶음)를 붙인 샌드박스의 키 변수에 들어가는 `openshell:resolve:env:<변수 이름>` 꼴 문자열. 정책 프록시가 요청 시점에 실제 키로 바꾼다(결정 기록 1556).
- 실행명: `{실행 이름}-{yymmddhhmmss}`(자료 계약 §10.3 N5). 실행 폴더 이름이다.

| 항목 | 내용 |
|---|---|
| 날짜 | 2026-09-25(금) 05:30(기록 시각). 관련 커밋: F4 `a63d94f`, F6 `884c729`, F5 `7dc5bfb`, F7 `0395bf6`, F3 `d1868e3`. 2회차(오케스트레이터 실측 반영, 2026-09-25(금) 06시대): F5 `99d3a71`, F4 `71e11cf`, F7 `3e05c6c`. 3회차(보안·NVIDIA·평가 방법론 검토 1 반영): F5 `05bf3cc`, F4 `4dff14e`, F7 `e33df9f`. 4회차(3회차 실측 반영): F7 `3ab8849` |
| 제목 | MT5 샌드박스·정책·출력 방식: 정책 파일 구성, 봉인 입력 반입, 출력 방식 (나)와 내려받기, download 검증 절차, 시연 실행명 확보, 정책 해시 규칙과 재적용 탐지, 감사 로그 발췌, 이미지 정의, 위반 시험 출력 이름, 키 변수 이름, 런타임 스킬 기본값, 샌드박스 안 스냅샷 검증, 라이브 정책의 OpenShell 추가 항목, 실측 사실, 추론 경로 격리, 내려받기 실패의 분모 |
| 결정 | ① [확정] 정책 파일은 둘이다. 채점 대상 실행 샌드박스 두 가지가 `configs/openshell/policy.yaml` 한 파일을 쓰고, 시연 샌드박스는 NemoClaw가 만든 정적 계층에 `configs/openshell/policy_demo_network.yaml`의 `network_policies`만 바꿔 넣는다 ② [잠정] 봉인 입력은 공식 채점 대상 실행 전용 이미지에 이미지 빌드로 굽는다(`/opt/tradesentry/sealed_input/{묶음}/`, 읽기 전용). upload는 쓰지 않는다 ③ [확정: 방식] [잠정: 이름 확보 시점] 샌드박스 출력은 방식 (나)다. 샌드박스 쪽 실행 폴더는 `/sandbox/outputs/{실행명}/`이고, 호스트 쪽은 같은 이름의 `outputs/{실행명}/`(봉인 묶음이면 `outputs/sealed/{실행명}/`)이다 ④ [확정: 실측] 내려받기는 늘 "확보한 빈 폴더 확인 → 같은 부모 아래 임시 폴더로 받기 → 검사 → 빈 폴더로 옮기기" 절차로 한다. download가 덮어쓰지 않는다는 보장에 기대지 않는다 ⑤ [잠정] NemoClaw 시연 경로의 실행명은 샌드박스 안 CLI가 확보하고, 호스트 받기 절차가 같은 이름의 호스트 폴더를 이미 있으면 실패하는 방식으로 만든 뒤에만 받는다 ⑥ [확정] 정책 해시 규칙(추출과 경로 치환 하나)과, 실행 중 재적용 탐지는 "묶음 앞뒤 라이브 정책 Version·Hash 대조 + 실행 기간 `CONFIG:LOADED` 재적용 행 0건"이다 ⑦ [잠정] 평가 묶음 실행 기간 감사 로그 발췌는 수집 스크립트 실행명 `openshell_audit_log-{시각}`의 실행 폴더에 `openshell_audit_log-{시각}.txt` 하나로 둔다 ⑧ [확정] 샌드박스 이미지 정의는 `configs/openshell/image/`(Dockerfile·포함 목록·CLI 실행기)와 스테이징 도구 `scripts/stage_sandbox_image.py`다 ⑨ [확정] 위반 시험 출력 이름(단위 F7 행에 적을 값) ⑩ [잠정] 키 변수 이름: CLI는 `NVIDIA_API_KEY`를 읽고, 시연 샌드박스에서는 실행기가 `NVIDIA_INFERENCE_API_KEY`의 자리표시 값만 그 이름으로 옮긴다 ⑪ [잠정] 런타임 스킬의 기본값: 운영자가 주지 않으면 스냅샷 `controlled_fixture_v0`, 정책 `dev-0.1`, 모드 `full`을 쓰고 기본값을 썼다고 알린다. `policy_v1`이 승인·동결되면 정책 기본값을 `policy_v1`로 바꾼다 ⑫ [확정] 샌드박스 안 스냅샷 확인은 CLI `snapshot-verify`(raw 대조가 늘 켜져 샌드박스 안에서는 종료 1이 설계대로다)가 아니라, 위반 시험의 이미지 기록 대조 행과 스냅샷 검증 행(단위 S3를 raw 대조 없이)으로 한다. raw 대조는 호스트 사전 점검의 `snapshot-verify`에서만 한다. 명령 표는 바꾸지 않는다 ⑬ [확정] OpenShell이 라이브 정책 `read_only` 끝에 스스로 더하는 `/var/log`를 커밋 정책에 명시하고, 구조 비교에서만 겹친 파일시스템 항목을 하나로 본다 ⑭ [사실] 2026-09-25(금) 실측 사실(아래 절) ⑮ [확정] 채점 대상 실행 샌드박스와 시연 샌드박스가 쓰는 게이트웨이 작업 공간에는 추론 경로(`inference.local`)를 두지 않는다. 시연은 X1처럼 추론 경로를 지우고 OpenClaw가 integrate를 직접 부르게 한다. 위반 시험과 평가 묶음 앞뒤로 `openshell inference get`을 적고 판정에 넣는다 ⑯ [잠정] 내려받기 실패(호스트 확보 실패·링크 거부·이름 충돌)는 그 사례 실행을 분모에 남는 실패로 기록하고, 재실행 규칙은 단위 E3을 따른다. 구현과 정확한 상태·원인 코드는 MT7이 정한다 |
| 이유와 근거 | 항목별 세부 절에 적었다 |
| 검토한 대안 | 항목별 세부 절에 적었다 |
| 결정 주체 | 소유 트랙(M). ③의 이름 확보 시점과 ⑦의 새 실행 이름은 오케스트레이터 확인이 필요하다(아래 "확인이 필요한 것") |
| 공용 약속 여부 | 자료 계약의 값·키·상태값·경로 표를 바꾸지 않았다. 다만 ③·⑤의 "샌드박스 안 CLI가 실행명을 정하고 호스트는 받을 때 확보한다"는 자료 계약 §10.3 N8의 "실행을 시작하기 전에 호스트 쪽 프로그램이 확보한다"와 순서가 다르다. N8 문구를 고치거나 CLI에 실행명을 넘기는 수단(새 옵션)을 두는 일은 공용 약속 변경이라 사용자 승인 대상이다. 승인 전에는 ③·⑤를 잠정으로 둔다 |
| 영향 | 파일: `configs/openshell/`(policy.yaml, policy_demo_network.yaml, provider_profile.yaml, image/), `scripts/openshell_common.py`, `scripts/openshell_violation_tests.py`, `scripts/openshell_probes/`, `scripts/stage_sandbox_image.py`, `skills/tradesentry/SKILL.md`, `tests/test_openshell_*.py`, `tests/test_sandbox_image.py`, `tests/test_runtime_skill.py`. 작업: MT7(샌드박스 밖 실행기와 내려받기 구현, ⑦ 수집 구현), AS2·AS3(`run-case`·`evaluate`의 샌드박스 안 실행), 평가 스킬 ② 공식 채점 단계(② 봉인 입력 반입), 단위 표 F5~F7 행(오케스트레이터가 ⑧·⑨ 값을 적는다), 스킬 사전 상태 열 |
| 관련 PR | MT5 두 번째 PR(브랜치 `model/MT5-sandbox`, 번호는 PR을 연 뒤 적는다) |

## 항목별 세부

### ① 두 샌드박스의 정책 파일 구성 [확정]

- 채점 대상 실행 샌드박스: `configs/openshell/policy.yaml` 한 파일. 개발 평가용과 공식 채점 대상 실행 전용이 같은 파일을 쓴다. 두 샌드박스의 차이는 정책이 아니라 이미지 내용(②의 봉인 입력)이다. 정적 계층은 만들 때 고정되므로 공식 채점 전용 샌드박스는 같은 파일로 새로 만든다(`openshell sandbox create ... --policy configs/openshell/policy.yaml`).
  - 요건(개발 플랜 §4.1·§4.4): (a) 앱·설정·스냅샷은 `/opt/tradesentry`에 `read_only`, 작업 폴더 `/sandbox`와 `read_write`(`/tmp`, `/dev/null`) 밖. 미끼 파일 `/srv/tradesentry_decoy/oracle_decoy.json`은 허용 목록 밖 (b) 목적지 `integrate.api.nvidia.com:443` 하나, `POST /v1/chat/completions` 한 경로, 실행 파일 `/opt/tradesentry/python/**`(이미지의 uv 관리 Python 3.12.13) (c) provider `tradesentry-nvidia`(프로필 `configs/openshell/provider_profile.yaml`, 자리표시 값 치환) (d)·(e) 위반 시험 스크립트(⑨).
- 시연 샌드박스: NemoClaw 온보딩이 만든 정적 계층을 그대로 두고, `network_policies`만 `configs/openshell/policy_demo_network.yaml`(X1 최종 4판의 `nvidia` 블록 하나)로 바꾼다. 적용 본문은 `python -m scripts.openshell_violation_tests compose-demo-policy --sandbox <이름> --out <저장소 밖 새 파일>`이 라이브 정책의 정적 계층을 글자 그대로 두고 만든다. 그 파일을 `openshell policy set <이름> --policy <그 파일> --wait`로 적용한다.
- 시연 샌드박스의 추론 경로(⑮): NemoClaw 온보딩은 게이트웨이 작업 공간 추론 경로를 만들고 OpenClaw가 `inference.local`로 부르게 한다. `inference.local`은 감독 프로세스가 샌드박스 네트워크 정책 밖에서 처리하므로, 이 경로가 있으면 네트워크 블록을 좁혀도 요건 (b)를 우회한다. 그래서 시연 준비에 X1 README 4단계를 넣는다: `openshell inference delete`로 경로를 지우고, OpenClaw 설정(`/sandbox/.openclaw/openclaw.json`의 `models.providers.inference`)의 `baseUrl`을 `https://integrate.api.nvidia.com/v1`로, `apiKey`를 샌드박스 환경변수 `NVIDIA_INFERENCE_API_KEY`의 자리표시 값으로 바꾼다. X1은 샌드박스 안 파이썬으로 고쳤고 명령은 기록이 없다 `[미확인]`. 대안 `nemoclaw <이름> config set --key models.providers.inference.baseUrl --value …`는 시험하지 않았다 `[미확인]`. 스킬 설치와 게이트웨이 재시작을 좁힌 정책 적용보다 먼저 한다(X1은 `openclaw_gateway_dialback`이 남은 판에서만 재시작했고, 좁힌 판 적용 뒤 재시작은 시험하지 않았다 `[미확인]`).
- 이유: 시연 샌드박스의 정적 계층(`/app`, `/sandbox/.openclaw`, `/run/nemoclaw/...` 등)은 NemoClaw 판이 정하고 실행 중 바꿀 수 없다(개발 플랜 §4.2). 그 정적 계층을 저장소에 커밋하면 NemoClaw 판에 묶이고, 다르게 적으면 적용이 거부되거나 틀린 증거가 된다. 네트워크 부분만 우리가 정하면 요건 (b)의 판단 대상(목적지·method·path·실행 파일)이 커밋 파일에 그대로 남는다. X1 4판이 이 구성으로 요건 (b)를 채웠다(`artifacts/openshell/violation_tests.md` §6) `[사실]`.
- 검토한 대안: (가) 한 파일을 두 종류에 모두 쓰기: 시연 샌드박스는 OpenClaw(node)가 추론을 부르므로 실행 파일 허용이 달라야 하고, 정적 계층이 NemoClaw 것이라 맞출 수 없다. (나) 공식 채점 전용 파일을 따로 두기: 개발 평가 때 시험한 정책과 공식 정책이 달라져 개발 평가 증거가 공식 실행을 뒷받침하지 못한다. 파일이 같으면 시험표의 본문 sha256(⑥)으로 같은 정책임을 보일 수 있다.

### ② 봉인 입력 반입 방식 [잠정]

- 방식: 공식 채점 대상 실행 전용 샌드박스의 이미지를 빌드할 때 봉인 입력을 굽는다. 위치는 `/opt/tradesentry/sealed_input/{묶음}/`(`{묶음}`은 `holdout40` 또는 `real_sealed`)다. `/opt/tradesentry`는 정책의 `read_only`이고 작업 폴더·`read_write` 밖이다. 정답표는 넣지 않는다.
- 빌드 맥락 만들기: 스테이징 도구(`scripts/stage_sandbox_image.py`)는 봉인 폴더 안 경로를 거부하므로 봉인 입력을 다루지 않는다. 봉인 입력 복사는 평가 스킬 ② 공식 채점 단계 안에서 샌드박스 밖 프로그램이 한다. 순서: 스테이징 도구로 저장소 밖 빈 폴더에 빌드 맥락을 만든다 → 봉인 해시 목록을 대조한다 → 해시 목록의 입력 항목만 `<빌드 맥락>/app/sealed_input/{묶음}/`에 복사하고 sha256을 다시 대조한다 → `openshell sandbox create --from <빌드 맥락>` → 빌드 맥락 폴더를 지운다. 각 단계는 봉인 사건으로 남긴다. 에이전트는 봉인 입력 파일을 열지 않는다(복사·해시 대조는 프로그램이 하고 에이전트는 종료 코드와 일치 여부만 받는다). 이 복사 프로그램은 아직 없다 `[미확인]`(MT7 또는 평가 스킬 ② 절차에서 만든다).
- 확인: 공식 채점 대상 실행 전용 샌드박스 최소 시험(개발 플랜 §4.4)의 쓰기 거부 행을 `python -m scripts.openshell_violation_tests run --scored <이름> --scored-kind official --ro-write-path /opt/tradesentry/sealed_input/<묶음>`으로 돌린다. 기대: 종료 코드 1, errno `EACCES`(정책 `read_only`) 또는 `EROFS`(읽기 전용 마운트).
- 리허설(비봉인 입력, 로드맵 MT5 ⑤): dev20 입력을 같은 방식으로 새 샌드박스에 넣는다. `stage_sandbox_image --add eval/dev/dev20/input/cases.json --add data/snapshots/dev20/snapshot_build.sqlite --add data/snapshots/dev20/snapshot_build.json`으로 `/opt/tradesentry/eval/dev/dev20/input/cases.json` 등에 굽고, 위반 시험을 `--ro-write-path /opt/tradesentry/eval/dev/dev20/input`과 dev20 정답표 파일 이름의 `--absent-name`으로 돌린다. 스테이징 도구는 `eval/dev/dev20/input/` 밖(정답표 `answers/` 포함)을 거부한다.
- 이유: 이미지에 구운 파일은 샌드박스 사용자가 덮을 수 없고, 정책 `read_only`로 쓰기도 막힌다. upload는 쓰기 가능한 위치(작업 폴더나 `/tmp`)에만 해 봤고(X1), 그곳은 쓰기 가능이라 "읽기 전용 입력"을 만족하지 않는다. upload는 Git 저장소 안에서 `.gitignore`를 따르거나 모두 무시 대상이면 거르지 않고 올려 제외 장치로 믿을 수 없다(자료 계약 §10.3 "upload 주의").
- 남는 위험: 이미지 층과 빌드 캐시에 봉인 입력이 남는다. 공식 채점 뒤 샌드박스와 이미지를 지우는지는 봉인 사건으로 기록한다(자료 계약 §10.3 N10). OpenShell이 빌드한 이미지를 어디에 두고 어떻게 지우는지는 `[미확인]`이다.
- 검토한 대안: (가) 호스트 폴더 마운트: OpenShell 0.0.116에서 마운트 수단을 확인하지 못했다 `[미확인]`. (나) upload 뒤 `chmod`: 샌드박스 사용자가 소유한 파일이면 다시 쓰기 가능하게 바꿀 수 있어 버렸다.

### ③ 샌드박스 출력 방식과 경로별 내려받기 [방식 확정, 이름 확보 시점 잠정]

- 방식 (나). 어떤 샌드박스도 호스트 `outputs/`를 허용 목록이나 작업 폴더에 넣지 않는다. CLI는 샌드박스 안에서 작업 폴더 `/sandbox`를 현재 폴더로 하여 불리고, 자기 실행 폴더 `/sandbox/outputs/{실행명}/`에 쓴다(CLI는 현재 폴더 기준 `outputs/`를 쓴다. `src/tradesentry/cli/dispatch.py`).
- 샌드박스 쪽 실행 폴더 이름: `{실행명}`과 같다. 실행명은 샌드박스 안 CLI가 명시적 KST 시각으로 확보한다(이미 있으면 실패하는 `os.mkdir`). 호스트 쪽 받는 곳은 같은 이름이다.
- 경로별 내려받기 주체와 시점

  | 경로 | 주체 | 시점 | 받는 곳 |
  |---|---|---|---|
  | 개발 묶음(dev20·`real_dev`) | 샌드박스 밖 실행기(로드맵 MT7의 평가 하네스, 프로그램) | 사례 실행 하나의 `openshell sandbox exec`가 끝난 직후(CLI가 NAT 파일 내보내기의 남은 쓰기를 기다린 뒤 종료한 때), 그 사례 실행 폴더마다 | `outputs/{실행명}/` |
  | 봉인 묶음(holdout40·`real_sealed`) | 같은 샌드박스 밖 실행기만. 에이전트는 봉인 실행 출력을 `exec`·`connect`·`download`로 열거나 받지 않는다 | 개발 묶음과 같다 | `outputs/sealed/{실행명}/`(임시 폴더도 `outputs/sealed/` 아래, ④) |
  | NemoClaw 시연 | 오케스트레이터가 부르는 호스트 받기 절차(⑤) | 시연 요청이 끝나고 스킬이 실행 폴더 위치(`/sandbox/outputs/{실행명}/`)를 알린 뒤 | `outputs/{실행명}/` |

- 받는 것: 그 실행 폴더 전체다. 사례 실행이면 보고서·실행 결과 기록·trace와 NAT 프로파일 파일 5개(`all_requests_profiler_traces.json`, `inference_optimization.json`, `standardized_data_all.csv`, `workflow_profiling_metrics.json`, `workflow_profiling_report.txt`. 2026-09-25(금) 05:00 오케스트레이터 실측: 실제 NIM으로 돌린 MT4 흐름이 실행 폴더에 만든다)가 든다. NAT가 정한 파일 이름을 N6 이름 규칙에 어떻게 맞추는지(N7 폴더에 그대로 두는지)는 단위 I13·E4(MT4·MT7)가 정한다 `[미확인]`. 받기 절차는 폴더를 통째로 옮기므로 어느 쪽으로 정해도 바뀌지 않는다.
- 받은 뒤 확인: 배치가 N6(`outputs/{실행명}/{도메인명}-{시각}.{확장자}`)·N7(`outputs/{실행명}/{도메인명}-{시각}/`)과 같고, 겹친 층(`outputs/{실행명}/{실행명}/`)이 없고, 심볼릭 링크가 없다. 사례 실행이면 NAT 파일 5개가 모두 있다(NAT 끝 이벤트가 빠지지 않았는지 보는 근거).
- 받은 뒤 샌드박스 쪽 폴더: 개발 묶음은 받은 뒤 지워도 된다. 봉인 묶음은 받기 전·지우기 전에도 같은 열람 금지를 받고, 지우는 시점은 정답 대조 채점 뒤다(N10).
- [잠정]인 까닭: 자료 계약 §10.3 N8은 "실행을 시작하기 전에 호스트 쪽 프로그램이 확보"한다고 적는다. 샌드박스 안 CLI에 호스트가 확보한 실행명을 넘기는 수단은 지금 없다(CLI 옵션은 자료 계약 §10 표에 있는 것뿐이다). 그래서 이 결정은 "샌드박스 안에서 확보 → 받을 때 호스트에서 같은 이름을 이미 있으면 실패하는 방식으로 확보"다. 호스트 확보가 실패하면(같은 이름이 이미 있음) 받지 않고 그 실행을 실패로 끝낸다. 샌드박스 실행의 실행명은 샌드박스 안 CLI만 만들므로 충돌은 호스트에서 같은 초에 같은 실행 이름을 쓴 다른 실행이 있을 때만 난다 `[추론]`. 이 순서를 받아들일지(N8 문구 보완), CLI에 실행명을 받는 수단을 새로 둘지는 사용자 결정이다.

### ④ download 덮어쓰기 검증과 옮기는 절차 [확정: 2026-09-25(금) 실측]

- 실측(OpenShell 0.0.116, 샌드박스 `ts-scored`, 오케스트레이터) `[사실]`
  - T-DL1 모양: `openshell sandbox download <샌드박스> /sandbox/outputs/<R> <A>`는 `<A>/<파일>`을 만든다. 폴더째가 아니라 **내용 복사**다(겹친 층 없음). 종료 코드 0.
  - T-DL2 덮어쓰기: 받는 곳에 같은 이름 파일이 있으면 **알리지 않고 덮어쓴다**(종료 코드 0, sha256이 바뀜). 그래서 download는 덮어쓰기 금지(N8)를 보장하지 않는다.
  - T-DL3 심볼릭 링크: 샌드박스 안 `link -> /etc/passwd`는 **링크 그대로** 받는다(샌드박스 쪽 대상을 따라가 받지 않는다). 호스트에서 그 링크를 따라가면 호스트 파일을 읽게 된다.
- 그래서 다음 절차로 받는다(샌드박스 밖 같은 프로그램이 확보와 받기를 모두 한다).
  1. 받는 곳 확인: `outputs/{실행명}/`(봉인이면 `outputs/sealed/{실행명}/`)이 방금 확보한 빈 폴더인지 본다. 비어 있지 않으면 받지 않고 실패로 끝낸다.
  2. 임시 폴더: 같은 부모(`outputs/` 또는 `outputs/sealed/`) 아래에 `tempfile.mkdtemp(prefix=".download-")`로 새 빈 폴더를 만든다. 점으로 시작해 실행 폴더 이름 규칙(`^[a-z][a-z0-9_]*-\d{12}$`)과 겹치지 않고, 끝나면 지운다. 봉인 묶음이면 이 폴더도 N10 금지를 받는다.
  3. 받기: `openshell sandbox download <샌드박스> /sandbox/outputs/<실행명> <임시 폴더>`.
  4. 검사: 임시 폴더 아래 모든 항목을 `os.lstat`으로 보고 심볼릭 링크(와 일반 파일·폴더가 아닌 것)가 하나라도 있으면 옮기지 않고 실패로 끝낸다(T-DL3). 링크를 따라가는 호출(`os.stat`, `open`, `shutil.copytree` 기본값)을 이 검사 전에 쓰지 않는다. 내용은 임시 폴더 바로 아래에 있어야 한다(T-DL1 내용 복사). `<임시 폴더>/<실행명>/` 한 겹만 있으면 모양이 바뀐 것이므로 실패로 끝내고 알린다.
  5. 옮기기: 내용의 최상위 항목마다 받는 곳에 같은 이름이 없는지 보고(`os.path.lexists`) `os.rename`으로 옮긴다. 같은 파일 시스템 안이라 복사가 아니다. 이미 있으면 멈추고 실패로 끝낸다.
  6. 임시 폴더를 지우고 ③의 "받은 뒤 확인"을 한다.
- 받는 곳에 직접 받지 않는 까닭은 T-DL2다. 확보한 빈 폴더에 곧바로 받아도 첫 받기는 안전하지만, 같은 폴더에 두 번 받으면 알리지 않고 덮으므로 늘 새 임시 폴더를 거친다. 셸로 옮길 때 `mv -n`은 같은 이름을 조용히 건너뛰므로, 옮긴 뒤 임시 폴더에 남은 항목이 있으면 충돌로 보고 실패로 끝낸다.

### ⑤ NemoClaw 시연 경로의 실행명 확보 주체와 방법 [잠정]

- 주체: 오케스트레이터가 부르는 호스트 받기 절차(샌드박스 밖 프로그램, ④와 같은 것).
- 방법: 스킬이 알린 샌드박스 쪽 실행 폴더 이름을 N5 형식(`^[a-z][a-z0-9_]*-\d{12}$`)으로 검사한다 → 호스트에서 `os.mkdir("outputs/<실행명>")`(`exist_ok` 없이)으로 확보한다 → `outputs/sealed/<실행명>`이 있으면 방금 만든 폴더를 지우고 실패로 끝낸다 → 확보에 실패하면 받지 않는다 → ④의 2~6. 시연 경로는 봉인 자료를 쓰지 않으므로 받는 곳은 늘 `outputs/`다.
- 이유: 로드맵 MT5 ⑥의 예시 그대로다. 시연 경로에서는 하네스 모델이 명령을 조립하므로 실행 전에 호스트가 이름을 넣을 길이 없다.

### ⑥ 정책 해시 규칙과 실행 중 재적용 탐지 [확정]

- 해시할 바이트(추출 규칙, `scripts/openshell_common.py`의 `split_policy_get`·`normalize_body`)
  1. `openshell policy get <이름> --full`의 표준 출력에서 ANSI 제어열을 지운다.
  2. 줄 끝을 LF로 맞추고(CRLF·CR → LF), 줄 끝 공백·탭을 지운 뒤 처음으로 `---`인 줄을 찾는다. 그 앞 줄들은 머리 항목(`Version`·`Hash`·`Status`·`Source`·`Config rev`)이다.
  3. 그 줄 뒤 전부가 본문이다. 줄마다 끝 공백·탭을 지우고, 앞뒤 빈 줄을 지우고, 마지막에 줄바꿈 하나를 둔다.
  4. 아래 경로 치환을 한 뒤 UTF-8 바이트다. 이 바이트가 커밋 사본 `live_policy-{샌드박스}.yaml` 파일 바이트이고, 시험표의 본문 sha256은 이 바이트의 sha256이다.
- 경로 치환 규칙(하나, `substitute_host_paths`): 호스트 경로만 바꾸고 샌드박스 안 경로(`/sandbox`, `/opt/tradesentry` 등)는 그대로 둔다. 긴 경로부터 봉인 폴더 → `$TRADESENTRY_SEALED_DIR`, 저장소 루트 → 루트 기준 상대경로(루트 자체는 `.`), 임시 폴더 → `$TMPDIR`, 홈 폴더 → `$HOME`. 적힌 경로와 실제 경로(`resolve`)를 모두 바꾼다. 그 뒤에도 macOS 로컬 경로 모양이 남으면 `<로컬 경로 가림>`으로 바꾸고 개수를 시험표에 적는다. X1의 라이브 정책 본문에는 호스트 경로가 없어 보통 바뀌는 곳이 없다 `[사실: X1 조회 기록]`.
- OpenShell이 보고하는 `Hash:`(`policy_hash`)는 우리 해시와 다른 값이다. 시험표에 따로 적는다. X1에서 이 값은 `CONFIG:LOADED`의 `policy_hash`와 같았다 `[사실]`.
- 재적용 탐지(X1 확인 뒤 정함): X1에서 `openshell policy set`마다 `CONFIG:DETECTED ... policy_changed:true` 다음에 `CONFIG:LOADED [INFO] Policy reloaded successfully [policy_hash:<64자리>]`가 남았고, 같은 내용을 다시 불러와도 남았으며, `Version`이 올라갔다(1 → 4) `[사실: artifacts/openshell/violation_tests.md §3]`. 그래서 평가 묶음마다:
  1. 묶음 시작 직전과 끝난 직후에 라이브 정책을 조회해 `Version`, `Hash`, 본문 sha256을 적는다.
  2. 묶음 실행 기간의 `openshell logs` 발췌(⑦)에서 `CONFIG:LOADED`이면서 `Policy reloaded`인 행을 센다.
  3. 판정: 앞뒤 `Version`·`Hash`가 같고 재적용 행이 0이면 "실행 기간 재적용 없음". `Version`이나 `Hash`가 다르면 재적용이 있었던 것이다(로그 버퍼와 관계없는 1차 근거). 발췌 첫 줄에 버퍼 경고가 있고 발췌의 첫 행이 묶음 시작보다 늦으면 로그 쪽 근거는 "불완전"으로 적는다.
  4. 위반 시험과 잇기: 묶음 시작 때의 `Version`·`Hash`·본문 sha256이 채점 요약에 적은 위반 시험표(`openshell_violation_tests-{시각}`)의 같은 샌드박스 행 값과 같아야 한다. 다르면 위반 시험 증거가 그 묶음을 덮지 않는다.
  5. 추론 경로(⑮): 묶음 시작 직전과 끝난 직후에 `openshell inference get`을 적고, 두 번 모두 작업 공간 추론 경로가 없어야 한다. 추론 경로는 정책 본문 밖이라 정책 해시에 들지 않는다(개발 플랜 §4.4).
- Landlock 적용 확인: `landlock.compatibility: best_effort`는 커널이 지원하지 않으면 파일시스템 통제를 알리지 않고 뺀다. 그래서 채점 대상 실행 샌드박스(우리 정책, 공식 채점 경로)는 위반 시험의 로그 수집 행과 평가 묶음 발췌(⑦)에서 Landlock 적용 행(`rules_applied`·`skipped`)이 있고 `skipped`가 모두 0이어야 한다. 시연 샌드박스는 이 조건을 판정에 넣지 않고 건수를 정보로 적는다. 정적 계층을 NemoClaw가 온보딩 때 고정하고, 정확도 지표에 쓰이지 않으며, Landlock 규칙은 허용 목록이라 없는 경로의 규칙을 건너뛰어도 접근이 넓어지지 않기 때문이다(오케스트레이터 판단, 2026-09-25(금), ⑭). 시연 정보 행 DL1이 라이브 정책 경로 가운데 샌드박스에 없는 것을 적어 `skipped`의 까닭을 남긴다(F7 `3ab8849`).
- 한계: 같은 이름으로 샌드박스를 지우고 다시 만들면 `Version`이 1로 돌아간다. 커밋한 증거도 Version 1이라 `Version`만으로는 다시 만든 샌드박스를 가리지 못한다. 샌드박스 고유 식별자나 만든 시각을 조회해 적을 수 있는지는 `[미확인]`이고 MT7에서 확인한다(`openshell sandbox list`·`get` 출력).
- 평가 스킬 ① 2단계의 "정책 적용 이벤트"는 ⑦의 발췌를 본다. 위반 시험 폴더의 발췌는 위반 시험 기간만 덮는다.

### ⑦ 평가 묶음 실행 기간 감사 로그 발췌의 위치와 이름 [잠정]

- 수집은 샌드박스 밖 프로그램(로드맵 MT7이 만든다)이 묶음이 끝난 뒤 한다. 실행 이름은 스크립트 이름 `openshell_audit_log`다(N5 "스크립트는 그 이름"). 시작 전에 자기 실행명을 확보한다(N8).
- 위치와 이름: 개발 묶음 `outputs/openshell_audit_log-{시각}/openshell_audit_log-{시각}.txt`, 봉인 묶음 `outputs/sealed/openshell_audit_log-{시각}/openshell_audit_log-{시각}.txt`. 파일 하나에 머리(묶음 실행명, 샌드박스 이름, 묶음 앞뒤 `Version`·`Hash`·본문 sha256, 묶음 앞뒤 `openshell inference get` 결과(⑮), 수집 명령, 재적용 행 수, Landlock 적용 행의 `skipped` 값, 버퍼 경고)와 발췌 행을 둔다. 호스트 경로 치환(⑥)을 거친다.
- 봉인 묶음 발췌는 금지 해제 조건 전에는 열지 않고 커밋하지 않는다. 그 전에 필요한 값(재적용 행 수, 거부 이벤트 수)은 수집 프로그램이 건수로만 표준 출력에 낸다(N10의 결정적 건수 추출).
- 오케스트레이터 확인이 필요한 것: 새 실행 이름 `openshell_audit_log`를 단위 표에 행으로 더할지(E 단위의 하위 출력으로 둘지).

### ⑧ 샌드박스 이미지 정의 [확정]

- 위치: `configs/openshell/image/`(Dockerfile, 포함 목록 `include.txt`, CLI 실행기 `tradesentry.sh`)와 스테이징 도구 `scripts/stage_sandbox_image.py`(단위 F5). 계획 경로 표에 없던 위치의 제안이다.
- 반입은 포함 목록과 `--add`로 명시한 경로뿐이다. 거부 규칙: `.env`류, `outputs/`, `artifacts/`, `spikes/`, `tests/`, `docs/`, `scripts/`, `eval/` 전부(예외는 `--add`로 준 `eval/dev/dev20/input/` 아래), 이름에 `oracle`·`answer`가 든 파일, 스냅샷은 `snapshot_build.sqlite`·`snapshot_build.json`만, 심볼릭 링크, 봉인 폴더 안 경로. 합성 시험자료는 `data/snapshots/controlled_fixture_v0/`의 두 빌드 파일만 들이고 생성 규칙 `fixture_spec.json`은 들이지 않는다(사례 이름표가 있다).
- 거부 규칙은 경로 조각을 casefold해서 비교하고, 적힌 철자가 디스크 철자(`os.listdir`)와 다르면 거부한다. macOS APFS처럼 대소문자를 구분하지 않는 파일 시스템에서 `--add .ENV`·`Eval/dev/dev20` 같은 별칭으로 우회되던 것을 막는다(MT5b 보안 검토 1, F5 `05bf3cc`). 하드 링크(링크 수 > 1)와 일반 파일이 아닌 것도 거부한다.
- 코드 판: 이미지 안에는 `.git`이 없으므로 스테이징 도구가 `image_manifest.json`의 `code_version`에 git 커밋과 추적 파일 변경 여부(`dirty`)를 적는다. 샌드박스 안 실행 결과의 `code_version`(자료 계약의 git 커밋 해시)은 이 값으로 채운다(MT7·AS2). `dirty`가 참인 이미지는 공식 실행에 쓰지 않는다. 위반 시험표 머리에도 도구의 코드 판을 적는다.
- 시연 샌드박스에는 이미지의 `/opt/tradesentry`를 묶음으로 꺼내 `/sandbox/tradesentry`로 올려 푼다(X1 방식). 가상환경은 옮길 수 없어 실행기가 관리 Python과 `PYTHONPATH`로 연다. 이 사본은 작업 폴더 안이라 쓰기 가능하다. 시연 경로는 정확도 지표에 쓰지 않으므로 받아들인다.

### ⑨ 위반 시험 출력 이름(단위 F7 행에 적을 값) [확정]

- 실행 폴더 `outputs/openshell_violation_tests-{시각}/`
  - 시험표 `openshell_violation_tests-{시각}.md`
  - N7 폴더 `openshell_violation_tests-{시각}/` 안에 샌드박스마다 `live_policy-{샌드박스 이름}.yaml`(⑥의 바이트)과 `audit_log-{샌드박스 이름}.txt`(시험 기간 발췌. 시험표 로그 근거 열의 행 번호는 이 파일의 행 번호)
- 샌드박스 이름은 파일 이름이 되므로 `^[a-z0-9][a-z0-9-]{0,62}$`만 받는다. 세 종류만 같은 이름의 `artifacts/openshell/openshell_violation_tests-{시각}/`로 증거 복사한다(N11).
- 행 구성(행 ID는 스크립트의 `scored_rows`·`demo_rows`가 정한다): 채점 대상 실행용(개발 평가)은 호스트 점검 5행(정책 대조, 요건 (b), 허용 목록, provider, 추론 경로), 파일 행 4개(부재 훑기, 미끼 읽기, 읽기 전용 쓰기, 작업 폴더 아래 `read_only` 자식 쓰기는 정보 행), 네트워크 행 5개(비허용 호스트, 비허용 바이너리 둘, L7, `inference.local`), 키 조회 1행, 대조군 NIM 1행, 이미지 기록 1행, 로그 수집 1행이다. 공식 채점 대상 실행 전용(`--scored-kind official`)은 개발 플랜 §4.4의 최소 시험 행(비허용 호스트, 부재 확인, 키 조회, 봉인 입력 쓰기 거부)에 호스트 점검·이미지 기록·로그 수집을 더한 것이다. 시연용은 호스트 점검 3행, 부재 훑기, 네트워크 행 4개(node 자손이 아닌 비허용 바이너리 둘, node가 띄운 비허용 호스트와 L7), 키 조회 2행(exec 세션, 하네스가 띄운 프로세스), 대조군 NIM 1행, 로그 수집 1행이다. MVP 체크리스트 4번은 NIM 허용 1건 이상과 네트워크 차단 3종(비허용 호스트·비허용 바이너리·L7)이 종료 코드와 감사 로그 행으로 모두 있을 때 충족이다.

### ⑩ 키 변수 이름 [잠정]

- CLI(MT4의 모델 설정 `configs/model/model.json`)는 `api_key_env`=`NVIDIA_API_KEY`를 읽는다. 채점 대상 실행 샌드박스는 provider `tradesentry-nvidia`가 그 이름으로 자리표시 값을 넣는다.
- 시연 샌드박스는 NemoClaw 온보딩이 만든 provider `nvidia-prod`가 `NVIDIA_INFERENCE_API_KEY`로만 넣는다. 그래서 실행기(`tradesentry.sh`)가 `NVIDIA_API_KEY`가 없고 `NVIDIA_INFERENCE_API_KEY`가 자리표시 값(`openshell:resolve:env:` 접두어)일 때에만 같은 값을 `NVIDIA_API_KEY`로 둔다. 실제 키 모양 값은 옮기지 않는다.
- 잠정인 까닭: 자리표시 값을 다른 변수 이름으로 옮겨 보내도 정책 프록시가 바꿔 주는지는 시험하지 않았다 `[추론: 치환은 헤더에 실린 자리표시 문자열로 한다(결정 기록 1556)]`. 확인 명령 T-DEMO3에서 확인한다. 안 되면 MT4 쪽 `api_key_env`를 샌드박스 종류에 따라 고르게 한다(MT4 문서가 "CLI(MT5)가 정한다"고 남겼다).

### ⑪ 런타임 스킬 기본값 [잠정]

- `skills/tradesentry/SKILL.md`는 운영자가 값을 주지 않으면 스냅샷 ID `controlled_fixture_v0`, 정책 버전 이름 `dev-0.1`, 모드 `full`을 쓰고, 기본값을 썼다고 답에 함께 적는다. 사례(`--case`)는 기본값이 없고 운영자에게 묻는다.
- 이유: 시연 MVP(개발 플랜 §5.1)의 첫 대상이 합성 사례 A/B/C(`controlled_fixture_v0`)이고, 지금 저장소에 있는 정책 수치는 개발용 `dev-0.1`뿐이다(`configs/policy_v1.json`은 승인 전). 모드 `full`은 전체 TradeSentry(조사자 + Critic + 수정 1회 + 검증기 차단)다.
- 바꾸는 때: `policy_v1`이 승인·동결되면(로드맵 DT4 ②) 정책 기본값을 `policy_v1`로 바꾸는 한 줄 수정을 같은 날 한다. `real_dev` 경보 시연 때는 운영자가 스냅샷 `kcs_202201_202412_v2`를 준다.
- 검토한 대안: 정책 기본값을 두지 않고 늘 묻기. 되묻기 왕복 없이 A/B/C를 시연하는 흐름을 위해 버렸다.
- 측정 편향 막기(MT5b 평가 검토 1): 스킬 호출 성공률(시연 요청 가운데 CLI 실행까지 이어진 비율)의 분자에 기본값으로 뜻하지 않은 대상을 실행한 요청도 들어갈 수 있다. 그래서 V1에서 ① 시연 요청 문구를 실행 전에 고정해 기록하고 ② 명시값 요청과 기본값 적용 요청의 성공률을 나눠 적고 ③ 분자는 스킬 답의 자기 보고 한 줄이 아니라 샌드박스 `/sandbox/outputs/{실행명}/`이나 exec 기록으로 센다.

### ⑫ 샌드박스 안 스냅샷 확인 [확정]

- 실측: 샌드박스 안 `tradesentry snapshot-verify --snapshot controlled_fixture_v0`가 종료 코드 1이었다. 실패 검사는 `peer_group_sources`(빌드 기록이 가리키는 `data/reference/peer_group_controlled_fixture_v0.csv`를 반입하지 않음)와 `raw_rebuild`("raw 대조 원천(manifest.json, raw/)이 없다")였다 `[사실]`.
- `peer_group_sources`: 스테이징 도구가 들이는 빌드 기록의 `peer_group_files`를 읽어 비교국 표를 sha256 대조 뒤 자동으로 들인다(F5 `99d3a71`). dev20을 `--add`하면 `peer_group_dev20.csv`가 같이 들어간다. 스테이징 결과를 호스트에서 흉내 내 돌려 보니(반입 폴더만 `PYTHONPATH`로 두고) 남는 실패는 `raw_rebuild` 하나였고 다시 계산한 `normalized_sha256`이 기록값과 같았다.
- `raw_rebuild`: raw 응답은 설계상 반입하지 않는다(⑧). CLI `snapshot-verify`는 raw 대조를 늘 켜고(단위 S3 `check_raw` 기본값 참), 끄는 CLI 옵션은 자료 계약 §10 명령 표에 없다. 명령 표를 바꾸지 않고 다음으로 나눈다.
  1. 호스트 사전 점검: 스테이징 전에 호스트에서 `tradesentry snapshot-verify --snapshot <id>`(raw 대조 포함)가 종료 코드 0이어야 한다.
  2. 이미지 기록: 스테이징 도구가 `image_manifest.json`에 반입 파일별 sha256과 스냅샷별 `normalized_sha256`·비교국 표를 적고, 위반 시험의 이미지 기록 행이 샌드박스 안 기록 sha256을 스테이징 출력(`manifest_sha256`)과 대조한다.
  3. 샌드박스 안 검증: 위반 시험의 스냅샷 검증 행(`--verify-snapshot <id>`, 기본 `controlled_fixture_v0`)이 샌드박스 안에서 단위 S3를 `check_raw=False`로 불러 raw 없이 도는 검사가 모두 통과하고 다시 계산한 `normalized_sha256`이 빌드 기록값, 그리고 이미지 기록(`image_manifest.json`의 `snapshots`, 이미지 기록 대조 행이 스테이징 출력과 이어 준 값)과 같은지 본다(3회차 F7 `e33df9f`). 이 탐침은 앱 코드를 고치지 않고 파이썬 한 줄로 단위 함수를 부른다.
- 그래서 샌드박스 안의 CLI `snapshot-verify`는 부르지 않는다. 부르면 `raw_rebuild` 하나 때문에 종료 코드 1이 나는 것이 설계대로다.
- 검토한 대안: (가) CLI에 raw 대조를 끄는 옵션 더하기: 자료 계약 §10 명령 표 변경이라 사용자 승인 대상이다 (나) raw를 반입하기: 반입 목록 원칙(원자료를 들이지 않는다)과 크기에 맞지 않는다.

### ⑬ 라이브 정책에 OpenShell이 더하는 항목 [확정]

- 실측: 라이브 정책(Version 2)의 `filesystem_policy.read_only` 끝에 커밋 정책에 없던 `/var/log`가 있어 위반 시험의 정책 대조 행이 불일치였다 `[사실]`. X1 시연 샌드박스의 라이브 정책에도 `/var/log`가 있었다. X1 OpenShell 단독 시험 샌드박스 조회 기록에는 없었다.
- 결정: 커밋 정책 `read_only` 끝에 `/var/log`를 이유 주석과 함께 적는다(F4 `71e11cf`). 그러면 라이브 본문과 커밋 정책이 같은 구조가 된다. 커밋한 증거(`artifacts/openshell/openshell_violation_tests-260925055407/`, 라이브 Version 1)에서 OpenShell은 이미 적힌 `/var/log`를 다시 더하지 않았다(`read_only`에 한 번) `[사실]`. 정책 대조 행이 파일시스템 목록의 똑같은 항목을 하나로 보고 비교하는 처리는 판이 바뀔 때를 위해 둔다. 겹친 항목은 허용 범위를 바꾸지 않는다.
- 해시 규칙(⑥)과의 관계: 본문 sha256은 라이브 본문 바이트 그대로이고 줄이거나 고치지 않는다. 겹침 처리는 구조 비교에만 쓴다.
- 검토한 대안: 비교에서 OpenShell 기본 항목 목록을 허용하기. 목록을 따로 관리해야 하고 커밋 정책만 읽는 사람에게 실제 허용 범위가 보이지 않아 버렸다.

### ⑭ 2026-09-25(금) 실측 사실 [사실]

- 커밋한 증거: `artifacts/openshell/openshell_violation_tests-260925055407/`(오케스트레이터 커밋 `c05f559`, 샌드박스 `ts-scored`, 코드는 F7 `3e05c6c`). MVP 체크리스트 4번 충족, 불일치 0. 감사 로그 발췌(`audit_log-ts-scored.txt`) 행 번호: 비허용 호스트 61행, 비허용 바이너리 curl 102행·시스템 파이썬 111행, L7 위반(`GET /v1/models` → 403) 121행, NIM 허용 142·143행(L4·L7 허용 행). 정책 대조 일치(라이브 Version 1, 본문 sha256 `8aae7417…`), 스냅샷 검증 행 일치(`normalized_sha256` `7453bf78…`), 이미지 기록 sha256 `20c83ea0…` = 스테이징 출력. `inference.local` 탐침은 503이었고, 130행 `NET:OPEN [INFO] ALLOWED inference.local:443`이 보이듯 정책은 막지 않았다. 막은 것은 추론 경로 부재다(⑮). Landlock 적용 행은 모두 `rules_applied:11 skipped:0`이다.
- 3회차 실측(오케스트레이터, 위반 시험 `openshell_violation_tests-260925061852`, 작업 폴더에만 있고 커밋하지 않음): 깨끗한 트리에서 다시 스테이징했다(`git_commit` `ac385c3`, `dirty=False`, `manifest_sha256` `c5fe1df9…`). 채점 대상 실행 샌드박스 `ts-scored`는 새로 만들었고, 시연 샌드박스는 `x1-demo`다.
  - 채점 대상 실행 샌드박스 행은 모두 일치했다(정책·요건 (b)·허용 목록·provider·추론 경로, 파일 행 4개, 네트워크 행 5개, 키 조회, 이미지 기록, 스냅샷 검증, NIM 허용, 로그 수집). Landlock 적용 행 17개가 모두 `skipped:0`이었다.
  - 시연 샌드박스 행: 요건 (b) 판정, 허용 목록, provider, 추론 경로 없음, 부재 훑기, 네트워크 행 5개(`inference.local` 포함), 키 조회 두 행이 모두 일치했다. 하네스가 띄운 프로세스의 키 조회는 `NO_REAL_KEY`였고, 조상 실행 파일은 `python3.13 < bash < node …`였다. NIM 허용 행도 일치했다.
  - 불일치는 시연 샌드박스의 로그 수집 행 하나였다. 시연 감사 로그에 `Landlock ruleset built [rules_applied:15 skipped:2]`(ro:10 rw:7, BestEffort)가 있었다. MVP 체크리스트 4번은 충족이었다. 이 불일치는 ⑥의 판단에 따라 정보로 바꿨다(4회차).
- 앞선 실행 `openshell_violation_tests-260925054457`(머리 `5b0c746`, 커밋하지 않음)은 ⑬을 낳은 실행이다(정책 대조 불일치 하나, 나머지 행은 위와 같은 판정). 미끼 읽기 EACCES, 읽기 전용 쓰기 EACCES, 부재 훑기 5,389항목에서 정답·채점기·outputs·봉인·.env 없음. 키 조회: `NVIDIA_API_KEY`는 자리표시 값, `NVIDIA_INFERENCE_API_KEY`·`DATA_GO_KR_SERVICE_KEY`는 없음. 이미지 기록 sha256이 스테이징 출력과 같음. 감사 로그 발췌 136행, 시험 기간 `CONFIG:LOADED` 0행. 유일한 불일치는 정책 대조 행(⑬)이었다.
- 작업 폴더 아래 `read_only` 자식(`/sandbox/read_only_probe`)은 쓰기가 허용됐다. Landlock이 작업 폴더 `read_write`와 합집합으로 판정한다는 예측대로다(T-RO1). 그래서 읽기 전용 입력은 작업 폴더 밖(`/opt/tradesentry`)에 두는 지금 배치를 유지한다.
- `openshell sandbox exec`의 기본 작업 폴더는 `/sandbox`다.
- OpenShell 0.0.116에는 `openshell provider profile list` 하위 명령이 없다. 프로필 가져오기(`openshell provider profile import -f ...`)는 "Imported 1 provider profile"로 끝났다.
- 게이트웨이 작업 공간·시스템 추론 경로는 모두 설정되지 않았다(X1 추론 경로가 남지 않았다).

### ⑮ 게이트웨이 작업 공간 추론 경로 격리 [확정]

- 문제: `inference.local`은 게이트웨이 작업 공간 추론 경로이고, 샌드박스 안 감독 프로세스가 네트워크 정책 밖에서 처리한다. 커밋한 증거의 감사 로그 130행 `ALLOWED inference.local:443`이 보이듯, 채점 대상 실행 정책은 `inference.local` 연결을 막지 않는다. `inference.local` 탐침이 503으로 끝난 까닭은 경로가 없어서다 `[사실]`. 경로를 되살리면 같은 작업 공간의 모든 샌드박스에 열린다(X1 README "되돌리기" 주의). 개발 플랜 §4.6이 격리 방법을 MT5에 넘겼다.
- 결정: 채점 대상 실행 샌드박스가 도는 게이트웨이(지금은 NemoClaw 게이트웨이 `nemoclaw` 하나)의 작업 공간에는 추론 경로를 두지 않는다. 시연 샌드박스도 같은 게이트웨이이므로 X1 4단계(`openshell inference delete`, OpenClaw의 integrate 직접 호출, ①)로 경로 없이 돈다. 샌드박스는 `--no-auto-providers`로 만들고 provider를 명시해 붙인다(채점 `tradesentry-nvidia`).
- 확인과 기록
  1. 위반 시험: 채점 대상 실행용의 추론 경로 조회 행·`inference.local` 탐침 행, 시연용의 추론 경로 조회 행(DP4)·node가 띄운 `inference.local` 탐침 행(DB5). 탐침 행은 2xx가 아니어야 일치이고, 비고에 "정책은 허용, 막은 것은 경로 부재"를 적는다.
  2. 평가 묶음: ⑥의 5와 ⑦ 머리에 묶음 앞뒤 `openshell inference get` 결과를 적는다.
  3. 경로가 필요한 다른 작업이 생기면(예: NemoClaw 기본 시연) 채점 대상 실행 전에 지우거나 별도 게이트웨이에서 한다. 별도 게이트웨이를 여는 방법은 `[미확인]`이다.
- 2026-09-25(금) 05:41 오케스트레이터 확인: 작업 공간·시스템 추론 모두 Not configured `[사실]`.
- 검토한 대안: 정책에서 `inference.local`을 막기. 이 경로는 네트워크 정책 밖에서 처리되어 정책으로 막을 수 없다고 본다 `[추론: 개발 플랜 §4.6]`.

### ⑯ 내려받기 실패와 분모 [잠정]

- 호스트 확보 실패(같은 이름이 이미 있음), 링크나 일반 파일이 아닌 항목 거부, 옮기기 충돌은 모두 "받지 않고 그 사례 실행을 실패로 끝낸다"(④·⑤). 평가 묶음에서 이 사례는 분모에 남는 실패로 기록하고 빠뜨리지 않는다(룰북 B5·B6). 실행 상태는 자료 계약의 실행 상태 값(`FAILED` 등) 가운데 하나를 쓴다. 인프라 실패인지 보이는 원인 분류 코드와 재실행 대상 여부는 단위 E3(인프라 실패 재실행 대상 목록) 규칙을 따른다. 정확한 코드 이름은 MT7이 자료 계약에서 고른다 `[미확인]`.
- 봉인 묶음은 한 번만 채점하는 규칙(룰북 B6)을 따른다. 내려받기 실패로 끝난 사례도 그대로 분모에 두고, 재실행은 E3이 인프라 실패로 분류한 경우에만 한다.
- 링크 거부로 실패하면 임시 폴더의 링크 항목만 `os.unlink`로 지우고(대상을 따라가지 않는다), 남은 임시 폴더는 이름을 바꿔 격리한 뒤 사건으로 기록한다. 증거 복사나 `shutil.copytree` 기본값처럼 링크를 따라가는 도구가 `outputs/` 아래 호스트 경로 링크를 읽지 않게 하기 위해서다(MT5b 보안 검토 권고 2). MT7이 프로그램으로 구현한다.
- 받기 전 윗단 링크(T-DL4): 받을 대상 `/sandbox/outputs/<실행명>` 자체가 링크일 때 download가 따라가는지, 어느 권한으로 읽는지는 `[미확인]`이다. 확인 전까지는 받기 전에 `openshell sandbox exec -n <이름> -- sh -c 'test -d /sandbox/outputs/<실행명> && ! test -L /sandbox/outputs/<실행명> && ! test -L /sandbox/outputs'`가 종료 코드 0일 때만 받는다.

### 넘길 곳

- MT7: ③·⑤ 호스트 쪽 실행명 확보와 내려받기(사용자 결정 뒤), ④ 절차의 프로그램 구현(링크 정리·격리 포함), ⑥의 4·5와 ⑦ 수집기, ⑯ 분모 처리, 샌드박스 고유 식별자 조회(⑥ 한계).
- MT4: NAT를 `[project].dependencies`로 lock에 넣고, 병합 뒤 이미지를 다시 빌드해 위반 시험을 다시 돈다(이미지 기록 값이 바뀐다).
- AS2: CLI 실행 파일(`/opt/tradesentry/.venv/bin/python`)로 NIM 허용이 되는지 실측(T-VENV). 위반 시험의 허용 행은 관리 Python 경로로만 보였다.
- V1: ⑪의 측정 편향 막기 세 가지.
- MT5 완료 전 남은 실측: 시연 샌드박스 행 전체(DP1~DP4·DA2·DB1~DB5·DC1·DN1·DD1), 하네스가 띄운 프로세스의 키 조회(DC2), dev20 리허설(dev20 입력 읽기 전용 쓰기 거부, 받은 뒤 N6 배치와 겹친 층 확인), T-DL4, T-DEMO1·T-DEMO3. 이 실측 전에는 MT5를 완료로 적지 않는다.

## 확인이 필요한 것(`[미확인]`)과 확인 명령

모두 오케스트레이터가 저장소 루트에서 돌린다. 키는 `spikes/x1/with_nvidia_key.py` 래퍼로만 자식 프로세스 환경에 넣고, 명령에는 변수 이름만 쓴다. 전체 순서와 기대 출력은 MT5 두 번째 PR 보고(`MT5b-1`)의 "오케스트레이터가 돌릴 명령"에 있다.

| 번호 | 확인할 것 | 명령(요지) | 판정 |
|---|---|---|---|
| T-DL1 (끝남: 내용 복사) | download가 폴더를 내용 복사하는지 폴더 복사하는지(겹친 층) | 샌드박스 안 `/sandbox/outputs/probe_dl-000000000000/a.txt`를 만들고 `openshell sandbox download <이름> /sandbox/outputs/probe_dl-000000000000 <저장소 밖 빈 폴더>` 뒤 `find <그 폴더>` | `<폴더>/a.txt`면 내용 복사, `<폴더>/probe_dl-000000000000/a.txt`면 폴더 복사. ④의 4에 적는다 |
| T-DL2 (끝남: 조용히 덮어씀) | 받는 곳의 같은 이름 파일을 덮는지 | 받는 곳에 내용이 다른 `a.txt`를 미리 두고 같은 download 뒤 sha256 비교 | 같으면 덮지 않음(또는 실패 종료 코드), 다르면 덮음. 어느 쪽이든 ④ 절차는 그대로다 |
| T-RO1 (끝남: 쓰기 허용) | 작업 폴더 아래 `read_only` 자식이 쓰기를 막는지(Landlock 합집합) | 위반 시험의 `read_only` 자식 쓰기 행(정보 행) | 정보 행. 쓰기 허용이면 읽기 전용 입력을 작업 폴더 밖에 두는 지금 배치를 유지한다 |
| T-DEMO1 | OpenClaw exec가 `/sandbox`에서 시작하는지 | 스킬이 `cd /sandbox && ...`로 부르므로 결과 무관. 스킬 실행 뒤 `/sandbox/outputs/`에 실행 폴더가 생겼는지 `openshell sandbox exec -n <시연> -- ls /sandbox/outputs` | 실행 폴더가 있다 |
| T-DEMO3 | ⑩ 자리표시 값을 옮겨 보내도 치환되는지 | 시연 샌드박스에서 스킬로 `run-case` 한 건(AS2 병합 뒤) | 종료 코드 0, 실행 결과 기록의 HTTP 200 |
| T-DL4 | 받을 대상 경로 자체가 링크일 때 download가 따라가는지(⑯) | 샌드박스 안 `ln -s /srv/tradesentry_decoy /sandbox/outputs/probe_link-000000000000` 뒤 `openshell sandbox download <이름> /sandbox/outputs/probe_link-000000000000 <저장소 밖 빈 폴더>`, `find <그 폴더>`. 미끼만 쓰고 실제 키가 있을 수 있는 경로는 쓰지 않는다 | 거부되거나 링크만 오면 안전. 미끼 내용(`oracle_decoy.json`)이 오면 막는 조건으로 올린다. 끝나면 샌드박스 쪽 링크를 지운다 |
| T-VENV | CLI 실행 파일 `/opt/tradesentry/.venv/bin/python`의 NIM 허용(정책은 `/opt/tradesentry/python/**`) | AS2 병합 뒤 채점 대상 실행 샌드박스에서 `run-case` 한 건, 감사 로그 허용 행의 실행 파일 경로 확인 | 허용 행이 있고 실행 파일이 `/opt/tradesentry/python/...`으로 풀려 있다 |
| T-SEAL1 | ② 공식 이미지에서 봉인 입력 쓰기 거부 | `--scored-kind official --ro-write-path /opt/tradesentry/sealed_input/<묶음>` | 쓰기 거부 행의 errno가 `EACCES` 또는 `EROFS` |
