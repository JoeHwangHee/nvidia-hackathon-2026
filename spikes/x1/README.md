# spikes/x1 — X1 임시 시험 코드

X1(구현 첫날의 세로형 최소 통합 시험)에서 쓴 임시 코드와 재현 절차다. 앱 코드가 아니며 S0(앱 뼈대) 결과에 섞지 않는다. 설치한 NAT 등의 판은 이 폴더 전용이고 앱 lock(패키지 버전 고정 파일)에 넣지 않는다.

- 결과와 증거: `artifacts/openshell/violation_tests.md`, `artifacts/openshell/logs/`
- 결정 기록: `docs/tracking/decisions/20260924-1556-x1-key-injection.md`
- 용어: OpenShell(에이전트를 격리해 돌리는 NVIDIA 샌드박스 런타임), 게이트웨이(OpenShell의 제어면, 곧 상태·정책·provider 설정을 보관하고 샌드박스에 내려보내는 부분. 샌드박스 밖 호스트에서 돈다), 감독 프로세스(supervisor, 샌드박스 컨테이너 안에서 root로 도는 `openshell-sandbox`. 정책 프록시로 바깥 요청을 검사하고, 게이트웨이에서 받은 자격 증명으로 요청 시점에 자리표시 값을 실제 키로 바꾼다. 근거는 OpenShell v0.0.116 `docs/about/how-it-works.mdx` 14·116행), provider(게이트웨이에 등록한 자격 증명 묶음), NAT(NVIDIA NeMo Agent Toolkit, 실행 추적·평가 도구 모음), NIM(NVIDIA 클라우드 추론 API), NemoClaw(OpenShell 위에서 에이전트를 돌리는 NVIDIA 참조 스택), OpenClaw(NemoClaw의 기본 하네스, 곧 모델이 도구를 부르며 일하도록 감싸는 실행 틀), colima(macOS에서 Docker용 리눅스 가상 머신을 띄우는 도구), 자리표시 값(placeholder, 실제 키 대신 샌드박스에 넣는 참조 문자열).

## 자리표시

개발 기계의 경로는 적지 않고 아래 자리표시로 적는다(`docs/standards.md` 문서 작성 규칙, `docs/rules/AGENT_OPS.md` §7.6). 실행할 때 각 값으로 바꾼다.

| 자리표시 | 찾는 방법 |
|---|---|
| `<colima Docker 소켓>` | `colima status` 출력의 `docker socket:` 값(`unix://`로 시작하는 전체 값) |
| `<OpenShell 설정 폴더>` | `XDG_CONFIG_HOME`(없으면 홈 폴더의 `.config`) 아래 `openshell` 폴더. Homebrew 게이트웨이 서비스 스크립트(`brew --prefix` 아래 `opt/openshell/libexec/openshell-gateway-homebrew-service`)가 `gateway.env`를 읽는 곳이다 |
| `<NemoClaw 설정 폴더>` | NemoClaw 저장소 문서 `docs/reference/host-files-and-state.mdx`(Host Files and State)가 적는 NemoClaw 호스트 상태 폴더. `usage-notice.json`·`sandboxes.json`이 있는 곳이다. 자격 증명 파일이 생길 수 있으므로 파일을 열지 않는다 |
| `<NemoClaw 게이트웨이 상태 폴더>` | NemoClaw가 `<OpenShell 설정 폴더>/gateway.env`의 `OPENSHELL_DB_URL`에 적는 게이트웨이 DB의 폴더. provider 자격 증명이 저장되므로 열지 않는다 |
| `<.env 경로>`, `<저장소 .env>` | 키가 든 본 저장소의 env 파일 경로. 이 파일은 래퍼(`with_nvidia_key.py`)만 읽는다 |
| `<1단계 게이트웨이 상태 폴더>` | 1단계 Homebrew 게이트웨이(`openshell`, 17670)가 쓰던 SQLite DB의 폴더. OpenShell 0.0.116 게이트웨이는 `OPENSHELL_DB_URL`이 없으면 `XDG_STATE_HOME` 아래 `openshell/gateway/`에 DB(`openshell.db`)를 두고, provider 자격 증명을 그 DB에 암호화해 둔다(키 암호화 키는 같은 폴더의 `credentials/` 아래) `[사실: OpenShell v0.0.116 docs/reference/gateway-config.mdx 19·392행]`. 1단계 `gateway.env`에는 `OPENSHELL_DB_URL`이 없었다(os-test transcript [G1]). 그때 Homebrew 서비스가 `XDG_STATE_HOME`을 어떻게 잡았는지는 `[미확인]`. provider 자격 증명이 있으므로 열지 않는다 |
| `<저장소 밖 임시 폴더>` | 저장소 밖에 만든 임시 폴더. 큰 묶음 파일(`x1opt.tar.gz`)을 저장소 안에 만들면 커밋될 수 있다 |
| `<NemoClaw CLI 폴더>` | NemoClaw 설치기가 CLI 심(shim, 실제 실행 파일로 이어 주는 작은 실행 파일)을 두는 폴더. 사용자 zsh 시작 설정 파일(`.zshrc`)의 NemoClaw PATH 블록에 적혀 있다 |

## 파일

| 파일 | 역할 |
|---|---|
| `with_nvidia_key.py` | 키 래퍼. env 파일에서 `NVIDIA_API_KEY` 한 줄만 읽어 자식 프로세스 환경에만 넣고, 자식 출력에서 키와 같은 문자열(과 앞·끝 조각)을 `***REDACTED***`로 가린다. 종료 코드를 그대로 돌려준다. `--export-as <이름>`으로 자식 환경의 변수 이름만 바꿀 수 있다 |
| `x1_probe.py` | 최소 CLI. 입력 한 줄로 NIM을 1회 호출하고 NAT 파일 내보내기로 실행 추적 1건(`nat_trace.jsonl`)과 앱 기록(`app_trace.jsonl`)을 남긴다. `--mode rewrite`(헤더 자리표시 값) 또는 `--mode inference-local`. `--api-key-env <이름>`(자리표시 값을 읽을 변수), `--key-check`(NIM 호출 전 이 프로세스에서 키 조회, 실제 키가 있으면 종료 코드 5), `--violation-probe <URL>`(호출 뒤 허용 목록 밖으로 의도적 요청 1건) |
| `nat_workflow.yml` | NAT 워크플로 설정 틀. CLI가 실행마다 채운 사본을 실행 폴더에 쓴다 |
| `key_check.py` | 요건 (c) 키 조회 시험. 값은 출력하지 않고 있음/없음·개수만 낸다. 실제 키 형식이 있으면 종료 코드 1. 일반 파일만 연다(FIFO·소켓에서 멈추지 않게) |
| `net_probe.py` | 위반 시험용 네트워크 탐침. 2xx가 아니면 0이 아닌 종료 코드 |
| `Dockerfile`, `.dockerignore` | 시험 샌드박스 이미지. 공동체 base 이미지 위에 Python 3.12(`/opt/x1/python`)와 `nvidia-nat==1.9.0`, CLI, 미끼 파일(`/srv/x1-decoy/`, 가짜 정답)을 넣는다 |
| `policy/x1-nvidia-chat.profile.yaml` | provider 프로필 초안. `integrate.api.nvidia.com:443` `POST /v1/chat/completions`, 키 자리는 `authorization` 헤더 bearer로 선언했다. 이 선언(`auth_style`·`header_name`)은 OpenShell 0.0.116에서 저장·검증되는 메타데이터이고, 치환은 CLI가 헤더에 실은 자리표시 값을 감독 프로세스의 정책 프록시가 바꿔서 일어난다(OpenShell v0.0.116 `docs/sandboxes/providers-v2.mdx` 216행) |
| `policy/x1-os-test.policy.yaml` | 시험 샌드박스 정책 1판(네트워크 블록 없음) |
| `policy/x1-os-test.nim.policy.yaml` | 2판. 정적 계층은 1판과 같고, 블록 `x1_nim_chat` 하나(`POST /v1/chat/completions`, `/opt/x1/python/**`)를 더했다 |
| `policy/x1-demo-narrowed.policy.yaml` | 시연 샌드박스 `x1-demo` 축소 정책(최종 4판). NemoClaw 기본 정책의 블록 7개 가운데 6개를 빼고 `nvidia` 블록 하나를 `POST /v1/chat/completions` 하나로 좁혔다. 바이너리는 `openclaw`와 실제 실행 파일 `/usr/local/bin/node` |
| `demo/run_probe.sh` | 시연 샌드박스용 CLI 실행기. `/sandbox/x1opt`의 Python 3.12와 NAT로 키 조회 → NIM 1회 → 의도적 위반 1건을 돌린다 |
| `skill/x1-probe/SKILL.md` | OpenClaw에 넣은 최소 스킬. `/sandbox/x1opt/run_probe.sh` 하나만 실행하고 결과 JSON을 그대로 전한다 |

## 재현 절차 — OpenShell 단독 시험 샌드박스(실행함)

저장소 루트에서 실행한다. `<.env 경로>`는 키가 든 본 저장소의 env 파일 경로다. 키 값은 어떤 명령에도 넣지 않는다.

```bash
# 0. 공식 스킬(개발 환경)
npx skills add NVIDIA/OpenShell --skill openshell-cli --skill generate-sandbox-policy --skill debug-inference --agent claude-code -y
npx skills add NVIDIA/skills --skill nemoclaw-user-guide --agent claude-code -y

# 1. colima와 OpenShell 0.0.116(설치 스크립트는 내려받아 읽은 뒤 실행)
colima start
curl -fsSL -o install.sh https://raw.githubusercontent.com/NVIDIA/OpenShell/main/install.sh
OPENSHELL_VERSION=v0.0.116 sh install.sh      # 게이트웨이 대기에서 종료 코드 1(compute driver 미설정)
# 주의: NemoClaw를 설치한 뒤(2단계 뒤)에는 아래 두 줄을 실행하지 않는다. NemoClaw가 다시 쓴 gateway.env(포트 8080,
#       <NemoClaw 게이트웨이 상태 폴더>)를 덮어써 시연 게이트웨이(nemoclaw)가 깨진다. NemoClaw 설치 전 기계에서만 쓴다.
#       덮어쓴 뒤 되살리는 방법은 [미확인](nemoclaw onboard가 다시 쓸 것으로 본다 [추론])
mkdir -p <OpenShell 설정 폴더>
printf 'OPENSHELL_DRIVERS=docker\nDOCKER_HOST=<colima Docker 소켓>\n' > <OpenShell 설정 폴더>/gateway.env
brew services restart nvidia/openshell/openshell
openshell status                                 # Connected, 0.0.116

# 2. 키 래퍼 동작 확인(무해한 명령만)
python3 spikes/x1/with_nvidia_key.py --env-file <.env 경로> -- true

# 3. provider(키는 이름으로만 넘긴다)
openshell provider profile import -f spikes/x1/policy/x1-nvidia-chat.profile.yaml
python3 spikes/x1/with_nvidia_key.py --env-file <.env 경로> -- \
  openshell provider create --name x1-nvidia --type x1-nvidia-chat --credential NVIDIA_API_KEY

# 4. 시험 샌드박스(이미지 빌드에 DOCKER_HOST 필요)
DOCKER_HOST=<colima Docker 소켓> openshell sandbox create --name x1-os-test \
  --from spikes/x1 --policy spikes/x1/policy/x1-os-test.policy.yaml \
  --provider x1-nvidia --no-auto-providers --detach

# 5. NIM 호출 전에 키 조회 시험(기대 종료 코드 0)
openshell sandbox exec -n x1-os-test -- /opt/x1/venv/bin/python /opt/x1/app/key_check.py

# 6. NIM 목적지를 여는 2판 정책을 실행 중에 다시 불러온다(CONFIG:LOADED 행이 남는다)
openshell policy set x1-os-test --policy spikes/x1/policy/x1-os-test.nim.policy.yaml --wait

# 7. NIM 1회 + NAT 추적 1건(기대 종료 코드 0, HTTP 200)
openshell sandbox exec -n x1-os-test -- /opt/x1/venv/bin/python /opt/x1/app/x1_probe.py \
  --input "Reply with exactly: X1 OK" --mode rewrite --runs-dir /sandbox/x1-runs

# 8. 위반 시험(모두 0이 아닌 종료 코드)
openshell sandbox upload x1-os-test spikes/x1/net_probe.py /tmp/x1-tools/
openshell sandbox exec -n x1-os-test -- /opt/x1/venv/bin/python /tmp/x1-tools/net_probe.py GET https://api.github.com/zen
openshell sandbox exec -n x1-os-test -- curl --fail -sS -o /dev/null -w "%{http_code}" -X POST \
  -H "Content-Type: application/json" -d "{}" https://integrate.api.nvidia.com/v1/chat/completions
openshell sandbox exec -n x1-os-test -- /opt/x1/venv/bin/python /tmp/x1-tools/net_probe.py GET https://integrate.api.nvidia.com/v1/models
openshell sandbox exec -n x1-os-test -- cat /srv/x1-decoy/oracle_decoy.json

# 9. 증거 수집과 정리. 1단계에서 이 정리를 실제로 했는지는 기록이 없다 [미확인](violation_tests.md §1 "정리" 행)
openshell logs x1-os-test --since 30m -n 3000      # 커밋한 os-test 로그를 만든 명령인지는 기록이 없다 [미확인]
openshell policy get x1-os-test --full
openshell sandbox download x1-os-test /sandbox/x1-runs artifacts/runs/
openshell sandbox delete x1-os-test
openshell provider delete x1-nvidia
openshell provider profile delete x1-nvidia-chat
#    아래 inference.local 비교를 했으면 그 provider와 추론 경로도 지운다
openshell provider delete x1-nvidia-route
openshell inference delete
```

`inference.local` 비교(채택하지 않음): 내장 유형 provider를 `--type nvidia`로 래퍼를 거쳐 만들고 `openshell inference set --provider <그 이름> --model nvidia/nemotron-3-super-120b-a12b` 뒤 `--mode inference-local`로 부른다. 끝나면 `openshell inference delete`.

## 재현 절차 — NemoClaw 시연 경로(2단계, 실행함)

NemoClaw 설치기는 라이선스·제3자 소프트웨어 고지 수락을 요구한다. 수락은 사용자가 결정한다(2026-09-24(목) 사용자 결정 (가), 오케스트레이터 전달). 결과는 `artifacts/openshell/violation_tests.md` §6에 있다.

```bash
# 1. 설치(부트스트랩 스크립트를 내려받아 읽은 뒤 판 고정). 키가 없으므로 온보딩 [3/8]에서 종료 코드 1이 정상
curl -fsSL -o nemoclaw.sh https://www.nvidia.com/nemoclaw.sh
#    실제 실행 형태는 artifacts/openshell/logs/20260924-x1-demo-transcript.txt [N1]
env -u NVIDIA_API_KEY -u NVIDIA_INFERENCE_API_KEY -u DATA_GO_KR_SERVICE_KEY DOCKER_HOST=<colima Docker 소켓> \
  NEMOCLAW_INSTALL_TAG=v0.0.124 NEMOCLAW_PROVIDER=build bash nemoclaw.sh --yes-i-accept-third-party-software

# 2. 온보딩(키는 래퍼로만, NemoClaw가 읽는 변수 이름으로 넘긴다)
python3 spikes/x1/with_nvidia_key.py --env-file <.env 경로> --export-as NVIDIA_INFERENCE_API_KEY -- \
  env DOCKER_HOST=<colima Docker 소켓> NEMOCLAW_PROVIDER=build \
  NEMOCLAW_MODEL=nvidia/nemotron-3-super-120b-a12b NEMOCLAW_POLICY_TIER=restricted NEMOCLAW_POLICY_MODE=skip \
  NEMOCLAW_WEB_SEARCH_PROVIDER=none NEMOCLAW_ACCEPT_THIRD_PARTY_SOFTWARE=1 \
  nemoclaw onboard --non-interactive --fresh --name x1-demo --yes-i-accept-third-party-software   # 실제 실행은 transcript [N3]

# 3. 첫 점검과 요건 (c) 키 조회(OpenClaw 요청 전). 17:21~17:22, transcript [C1]·[K1]
openshell policy get x1-demo --full
openshell provider list; openshell sandbox provider list x1-demo; openshell inference get
openshell sandbox upload x1-demo spikes/x1/key_check.py /tmp/x1-tools/
openshell sandbox exec -n x1-demo --timeout 240 -- /usr/bin/python3 /tmp/x1-tools/key_check.py /

# 4. 추론 경로 삭제와 OpenClaw 직접 호출 설정. 17:23~17:24, [D1]·[E1]
openshell inference delete
#    /sandbox/.openclaw/openclaw.json의 models.providers.inference: baseUrl을 https://integrate.api.nvidia.com/v1로,
#    apiKey를 샌드박스 환경변수 NVIDIA_INFERENCE_API_KEY의 자리표시 값으로 바꾸고 .config-hash를 다시 계산했다
#    (샌드박스 안 python으로 수정, 자리표시 형식이 아니면 쓰지 않음, 원본은 openclaw.json.x1-backup).
#    수정에 쓴 명령·스크립트는 기록 없음 [미확인]. 바뀐 값의 형태만 [E1]에 있다
#    대안(시험 안 함): nemoclaw x1-demo config set --key models.providers.inference.baseUrl --value https://integrate.api.nvidia.com/v1
#      NemoClaw v0.0.124 docs/reference/commands.mdx "config set" 절(1358~1378행). 이 명령으로 apiKey에 자리표시 값을 넣을 수
#      있는지와 OpenClaw 설정 해시를 다시 계산하는지는 [미확인]. 샌드박스 안에서 손으로 고친 값은 rebuild 뒤 남지 않을 수 있다
#      [추론: 같은 문서 2420행은 openclaw.json을 이미지가 만드는 상태로 적고, 샌드박스 안에서 고친 채널 설정은 rebuild 뒤 남지 않는다고 적는다]

# 5. 2판 정책(nvidia 블록 바이너리 openclaw만 + openclaw_gateway_dialback). 17:24:38, [P1]
#    2판 본문은 artifacts/openshell/logs/20260924-x1-demo-policy.txt 4절이다. 저장소의 x1-demo-narrowed.policy.yaml은 최종 4판이다
openshell policy set x1-demo --policy <2판 YAML: 20260924-x1-demo-policy.txt 4절 본문> --wait

# 6. CLI 런타임과 스킬 넣기, OpenClaw 게이트웨이 재시작(2판 상태에서 실행). 17:25, [U1]·[S1]·[R1]
#    x1-probe:x1 이미지(/opt/x1: Python 3.12.13 독립 실행형 + nvidia-nat 1.9.0, [U1])를 만든 명령은 기록 없음 [미확인]
#    아래 docker 줄도 transcript에는 없고 X1 구현 에이전트가 이 README에 적은 형태다. 묶음 파일은 저장소 밖에 만든다
docker create --name x1tmp x1-probe:x1 && docker cp x1tmp:/opt/x1 - | gzip -1 > <저장소 밖 임시 폴더>/x1opt.tar.gz && docker rm x1tmp
openshell sandbox upload x1-demo <저장소 밖 임시 폴더>/x1opt.tar.gz /tmp/x1-tools/
#    [U1]은 이 묶음과 앱 파일 5개를 올리고(모두 종료 코드 0) /sandbox/x1opt로 풀어 nat 1.9.0 import를 확인했다고만 적는다.
#    올린 파일 목록, 푼 명령, app/·run_probe.sh를 둔 명령은 기록 없음 [미확인]. 배치는 spikes/x1/demo/run_probe.sh가 기대하는 경로다:
#    /sandbox/x1opt/python/cpython-3.12.13-linux-aarch64-gnu/bin/python3.12, /sandbox/x1opt/venv/lib/python3.12/site-packages,
#    /sandbox/x1opt/app/x1_probe.py(와 key_check.py·nat_workflow.yml), /sandbox/x1opt/run_probe.sh
nemoclaw x1-demo skill install spikes/x1/skill/x1-probe/
nemoclaw x1-demo gateway restart

# 7. 2판에서 키 조회와 한 줄 경로 시도. 17:40, [K2]·[A1]. OpenClaw의 모델 호출이 binary-miss로 거부됐다(DA1)
openshell sandbox exec -n x1-demo --timeout 240 -- /usr/bin/python3 /tmp/x1-tools/key_check.py /
nemoclaw x1-demo agent --agent main --json --timeout 240 -m "<9와 같은 요청 문장>"

# 8. 3판 정책(2판 + nvidia 블록 바이너리 /usr/local/bin/node). 17:46:08, [P2]. 본문은 20260924-x1-demo-policy.txt 6절
#    그 전에 --api-key-env를 더한 x1_probe.py·run_probe.sh를 다시 올렸다. 올린 명령은 기록 없음 [미확인]
openshell policy set x1-demo --policy <3판 YAML: 20260924-x1-demo-policy.txt 6절 본문> --wait

# 9. 3판에서 키 조회와 한 줄 경로. 17:46, [K3]·[A2]. 통과했지만(DA2) 3판은 요건 (b)를 채우지 못한 구성이다
openshell sandbox exec -n x1-demo --timeout 240 -- /usr/bin/python3 /tmp/x1-tools/key_check.py /
nemoclaw x1-demo agent --agent main --json --timeout 300 \
  -m "Run the X1 probe now: use the x1-probe skill with the one-line input 'Reply with exactly: X1 OK', then return the JSON line printed by the command exactly as it is."

# 10. 위반 시험 DT1~DT4. 17:48, [T1..T4]. 명령 전체 형태는 기록 없음 [미확인]. 기록에 남은 조각은 다음과 같다
#    DT1: node의 자손이 아닌 curl -> POST https://integrate.api.nvidia.com/v1/chat/completions. demo 로그 624행의 조상
#         (openshell-sandbox)·명령줄 조각(/dev/null)과 출력(000, curl: (22) ... 403)으로 보아 1단계 8의 curl 줄과 같은 형태로 본다 [추론]
#    DT2: /usr/bin/python3 /tmp/x1-tools/net_probe.py로 POST https://integrate.api.nvidia.com/v1/chat/completions
#         (스크립트 경로는 demo 로그 633행 명령줄, method·URL은 [T1..T4] 출력 JSON)
openshell sandbox exec -n x1-demo -- /usr/bin/python3 /tmp/x1-tools/net_probe.py POST https://integrate.api.nvidia.com/v1/chat/completions   # DT2. 위 조각과 net_probe.py 사용법을 이은 형태 [추론]
#    DT3: node가 띄운 curl -> GET https://integrate.api.nvidia.com/v1/models, DT4: node가 띄운 curl -> api.github.com:443.
#         node가 curl을 띄운 방법은 기록 없음 [미확인]. 로그(642·643·652행)는 curl의 허용·거부만 보인다

# 11. 최종 4판(3판에서 openclaw_gateway_dialback 제거). 17:55:17, [P3]. 저장소의 x1-demo-narrowed.policy.yaml(7절 본문과 같음)
openshell policy set x1-demo --policy spikes/x1/policy/x1-demo-narrowed.policy.yaml --wait
openshell sandbox exec -n x1-demo --timeout 240 -- /usr/bin/python3 /tmp/x1-tools/key_check.py /
nemoclaw x1-demo agent --agent main --json --timeout 300 -m "<9와 같은 요청 문장>"
#    17:55:31·17:55:56 요청은 NIM 과부하 오류(DA3), 17:56:19 세 번째 요청이 통과했다(DA4, [A4-2]).
#    이어서 10과 같은 위반 시험을 다시 돌렸다(DT1'~DT4', 17:57. 명령 형태는 10과 같이 [미확인]).
#    4판 적용 뒤 nemoclaw x1-demo gateway restart는 시험하지 않았다. 재시작(17:25)은 openclaw_gateway_dialback이 남은 2판에서만 했다.
#    그 블록 없이 재시작이 건강 확인을 통과하는지는 [미확인]

# 12. 증거 수집
openshell logs x1-demo --since <기간> -n 3000
#    커밋한 demo 로그(17:20:31~17:57:27, 37분)를 만든 수집 명령은 기록이 없다 [미확인]. 앞 판의 --since 10m은
#    그 로그를 만든 명령이 아니다. openshell logs는 크기가 정해진 버퍼에서 읽어 행이 빠질 수 있다(첫 줄 경고,
#    OpenShell v0.0.116 docs/observability/accessing-logs.mdx 38·60행). 완전한 기록은 샌드박스 안 /var/log/openshell.*.log다
openshell policy get x1-demo --full
openshell sandbox download x1-demo /sandbox/x1-runs artifacts/runs/
```

주의

- OpenClaw 게이트웨이(샌드박스 안에서 OpenClaw를 띄우는 프로세스) 재시작(`nemoclaw x1-demo gateway restart`) 뒤 `openshell sandbox exec`가 `--timeout`을 넘겨 돌아오지 않은 일이 있었다. exec는 한 번에 하나씩, 호스트 쪽 감시 시간을 두고 돌린다.
- `nemoclaw … agent`는 OpenClaw 결과에 `replayInvalid: true`가 있으면 종료 코드 1을 낸다. 결과 JSON의 `status`와 `payloads`를 함께 본다.

되돌리기(시연 샌드박스)

되돌린 뒤(1판 정책과 추론 경로 복구)의 샌드박스는 요건 (b)를 채우지 않으므로 시연 증거로 쓰지 않는다.

```bash
# 0. 증거를 먼저 받는다
openshell sandbox download x1-demo /sandbox/x1-runs artifacts/runs/

# 1. X1이 넣은 것 지우기
nemoclaw x1-demo skill remove x1-probe
#    OpenClaw에서는 /sandbox/.openclaw/workspace/skills/x1-probe만 지운다(NemoClaw v0.0.124 docs/reference/commands.mdx 2687~2711행)
openshell sandbox exec -n x1-demo -- rm -rf /sandbox/x1opt /tmp/x1-tools /sandbox/x1-runs

# 2. 정책을 온보딩 직후 1판으로
openshell policy set x1-demo --policy <온보딩 직후 정책: artifacts/openshell/logs/20260924-x1-demo-policy.txt 1절의 YAML 본문> --wait

# 3. 추론 경로 되살리기
#    경고: 되살리면 같은 게이트웨이·작업 공간의 모든 샌드박스에 inference.local이 다시 열린다. 정책 블록이 없어도 어떤
#    실행 파일이든 쓸 수 있다(violation_tests.md V7, OpenShell v0.0.116 docs/sandboxes/inference-routing.mdx 328행).
#    NemoClaw 문서는 공유 NemoClaw 게이트웨이에서 openshell inference set을 직접 쓰지 말고 아래 명령을 쓰라고 한다. 이 명령은
#    OpenShell 경로, OpenClaw 설정의 provider 항목과 설정 해시, NemoClaw 등록부를 함께 맞춘다(같은 판 commands.mdx 3414·3435~3441행)
nemoclaw x1-demo inference set --provider nvidia-prod --model nvidia/nemotron-3-super-120b-a12b
#    앞 판에 적었던 openshell inference set --provider nvidia-prod --model nvidia/nemotron-3-super-120b-a12b는
#    NemoClaw 등록부 검사를 건너뛴다(같은 문서 3441행)

# 4. openclaw.json: 3의 명령은 OpenClaw 설정의 provider 항목과 선택 모델을 고친다(commands.mdx 3414행 "For OpenClaw, the patch
#    updates the OpenClaw config provider namespace and selected model"). 그래서 X1이 바꾼 baseUrl·apiKey도 3에서 다시
#    쓰일 것으로 본다 [추론]. 원본으로 확실히 돌리려면 샌드박스 안에서
#    /sandbox/.openclaw/openclaw.json.x1-backup을 openclaw.json으로 되돌리고 .config-hash를 다시 계산한 뒤 백업 파일을 지운다
#    (X1의 수정 명령이 기록에 없어 되돌리는 명령도 [미확인])
nemoclaw x1-demo gateway restart
# 또는 샌드박스를 지운다: nemoclaw x1-demo destroy(온보딩 때 만든 호스트 Docker 이미지도 지운다, commands.mdx 2013~2015행)
```

시연하지 않을 때는 샌드박스와 전달 프로세스를 멈춰 둔다.

```bash
nemoclaw x1-demo stop
#    컨테이너를 멈추고 그 샌드박스의 호스트 대시보드 전달(127.0.0.1:18789)을 멈추려 한다. 정책·자격 증명·작업 파일은 남고,
#    공유 호스트 게이트웨이(127.0.0.1:8080)는 계속 돈다(NemoClaw v0.0.124 docs/reference/commands.mdx 1529~1556행)
nemoclaw x1-demo start
#    다시 띄운다. start는 기록된 provider·모델로 https://inference.local에 추론 요청 1건을 보내 확인한다(같은 문서 1602행).
#    X1 구성은 추론 경로를 지웠으므로 이 확인은 실패해 0이 아닌 종료 코드를 낼 것으로 본다 [추론]
```

## MT4·MT5로 넘기는 것

X1 코드와 시험에서 드러난 한계다. 앱 코드는 MT4(조사 흐름·NIM 호출·NAT 감싸기)와 MT5(CLI·OpenShell 정책·NemoClaw 경로)에서 만든다.

- NAT(MT4)
  - LLM 구간 기록(LLM span, 모델 호출 하나를 시작·끝 이벤트로 남기는 기록)이 없다. X1 CLI는 NAT 함수 안에서 NIM을 `urllib`로 직접 불러, 실행 추적에는 `WORKFLOW_START`·`FUNCTION_START`·`FUNCTION_END`·`WORKFLOW_END` 네 이벤트만 남았다 `[사실: artifacts/openshell/logs/20260924-x1-demo-nim-run-excerpt.txt 4~7·35~38·46~49행]`. 그래서 NAT 프로파일러는 토큰 수와 모델 지연을 보지 못한다 `[추론]`. MT4는 NIM 호출이 LLM 구간 기록을 남기게 감싼다.
  - `WORKFLOW_END`가 파일에 남았는지는 이벤트 수로 확인하거나, 내보내기(exporter)의 `wait_for_tasks()`로 남은 쓰기를 기다려 확인한다. NAT 1.9.0의 `stop()`은 백그라운드 내보내기 작업을 기다리지 않는다 `[사실: NVIDIA/NeMo-Agent-Toolkit v1.9.0 packages/nvidia_nat_core/src/nat/observability/exporter/base_exporter.py 113~117·360~378행]`. X1 CLI는 이벤트 루프에 남은 작업 전체를 5초까지 기다리는 방법을 썼다(`x1_probe.py`의 `run_once`).
- 키 조회 시험 `key_check.py`의 조회 범위 한계(MT5)
  - `os.walk`에 `onerror`를 주지 않아, 목록을 읽지 못한 폴더가 조용히 빠진다. 목록을 읽지 못한 폴더를 따로 센다. 예: demo transcript [K1]에서 `/run/nemoclaw`는 파일 0개로 나왔는데, 폴더 목록을 읽지 못한 것으로 본다 `[추론]`.
  - 정책에 적힌 파일 경로(예: `read_only`의 `/run/nemoclaw/managed-startup-runtime.env`)는 폴더를 훑지 말고 직접 연다. 지금은 `.env` 찾기에서 `/run`을 빼고, 하네스 경로 후보는 폴더 목록으로만 훑는다.
  - 다른 프로세스의 environ에서도 `DATA_GO_KR_SERVICE_KEY=` 이름이 있는지 센다. 지금은 이 프로세스의 환경변수에서만 이름을 본다.
- 감사 로그(MT5): `openshell logs`는 크기가 정해진 버퍼라 행이 빠질 수 있다. 샌드박스 안 `/var/log/openshell.*.log`나 OCSF JSON 내보내기를 대조 출처로 검토한다(`artifacts/openshell/violation_tests.md` §3 "수집 한계").
- 한 줄 경로(MT5): 4판 턴은 SKILL.md를 다시 읽지 않았다. 새 세션으로 4판에서 스킬 읽기부터 다시 돌린다(`artifacts/openshell/violation_tests.md` §0).

## 개발 기계 되돌리기

X1이 개발 기계에 남긴 것과 되돌리는 방법이다. 명령은 공개 문서에서 확인한 것만 적고, 확인하지 못한 것은 `[미확인]`으로 둔다. 공개 문서는 태그를 지정해 읽은 OpenShell v0.0.116·NemoClaw v0.0.124 문서·소스와, 2026-09-24(목)에 웹에서 읽은 Homebrew 공식 manpage(명령 설명서, https://docs.brew.sh/Manpage)·Docker 공식 문서(https://docs.docker.com/reference/cli/docker/image/rm/)다. PR #19 수정 때 이 절의 명령은 Homebrew·Docker 명령 줄을 포함해 실행하지 않았다. 시연 샌드박스, NemoClaw 게이트웨이, provider `nvidia-prod` 가운데 하나라도 지우면 시연 경로가 돌지 않는다.

- 사용자 zsh 시작 설정 파일(`.zshrc`)의 NemoClaw PATH 블록
  - 모양: 빈 줄 하나 뒤에 `# NemoClaw PATH setup` 줄, `export PATH="<NemoClaw CLI 폴더>:$PATH"` 줄, `# end NemoClaw PATH setup` 줄이 온다 `[사실: NemoClaw v0.0.124 scripts/install.sh 2642~2691행]`.
  - 찾기: 두 표지 줄(`# NemoClaw PATH setup`, `# end NemoClaw PATH setup`)로 찾는다. 지우기: 두 표지 줄과 그 사이 줄을 편집기로 지운다.
  - `nemoclaw uninstall`의 CLI 제거 단계도 이 블록을 지운다 `[사실: 같은 판 src/lib/actions/uninstall/run-plan.ts 1861~1877·1993~2010행]`.
- NemoClaw v0.0.124(npm 전역 연결 CLI, 소스, 호스트 상태, 시연 샌드박스)
  - `nemoclaw uninstall [--yes] [--keep-openshell] [--delete-models] [--destroy-user-data] [--all-gateway-ports] [--gateway <name>]` `[사실: NemoClaw v0.0.124 docs/reference/commands.mdx 3716행]`.
  - 선택한 게이트웨이의 샌드박스(`x1-demo`)를 지우고, 형제 게이트웨이가 없으면 provider 등록과 NemoClaw가 관리하는 게이트웨이의 Docker 이미지도 지운다(같은 문서 3853행). 지우기 전에 등록된 샌드박스마다 호스트 쪽 스냅샷을 만든다(같은 판 docs/manage-sandboxes/uninstall-nemoclaw.mdx 20~24행). CLI는 `npm unlink -g nemoclaw`·`npm uninstall -g nemoclaw`로 지운다(run-plan.ts 1993~2002행).
  - `--keep-openshell`: OpenShell 실행 파일, NemoClaw가 관리하는 게이트웨이 서비스 파일, 로컬 게이트웨이 상태를 남기고 호스트 게이트웨이 프로세스를 멈추지 않는다(commands.mdx 3700행).
- OpenShell 0.0.116(Homebrew 로컬 tap(Homebrew가 공식(formula, 설치 단위)을 읽어 오는 저장소) `nvidia/openshell`의 `openshell`·`openshell-gateway`·`openshell-driver-vm`). 순서는 서비스 중지, 제거, tap 해제다 `[추론]`.
  - 서비스 중지: `brew services stop nvidia/openshell/openshell`. Homebrew 공식 manpage는 `brew services stop`을 "Stop the service formula immediately and unregister it from launching at login (or boot), unless --keep is specified"라고 적는다 `[사실: https://docs.brew.sh/Manpage]`. 공식 이름은 1단계 재현 절차 1의 `brew services restart` 줄과 같게 적었다. OpenShell 설치 문서는 중지도 Homebrew 서비스 명령으로 한다고만 적고, 예시는 `brew services list`·`brew services restart openshell`뿐이다 `[사실: OpenShell v0.0.116 docs/about/installation.mdx 51~56행]`. 멈추면 시연 경로가 돌지 않는다.
  - 제거: `brew uninstall nvidia/openshell/openshell`. NemoClaw uninstall은 macOS에서 OpenShell 실행 파일을 남기고, Homebrew가 이 공식을 확인하면 이 명령을 따로 안내한다 `[사실: NemoClaw v0.0.124 docs/manage-sandboxes/uninstall-nemoclaw.mdx 53~63행]`.
  - tap 해제: `brew untap nvidia/openshell`. Homebrew 공식 manpage는 `brew untap`을 "Remove a tapped formula repository"라고 적는다 `[사실: https://docs.brew.sh/Manpage]`. 같은 항목의 `--force` 설명("Uninstall all formulae and casks from this tap with --force before untapping")으로 보아 위 제거 뒤에 푼다 `[추론]`. OpenShell·NemoClaw 문서에는 이 명령이 없다. 이 로컬 tap은 설치 스크립트가 `brew tap-new --no-git`으로 만든다 `[사실: OpenShell v0.0.116 install.sh 668~673행]`.
  - CLI의 1단계 게이트웨이 등록 `openshell`(17670): `openshell gateway remove openshell`은 게이트웨이 서비스를 멈추지 않고 사용자 층 등록만 지운다 `[사실: OpenShell v0.0.116 docs/sandboxes/manage-gateways.mdx 85·148~151행]`. 지우기 전에 `openshell gateway list`로 층(`user`·`system`)을 본다.
- `gateway.env`와 LaunchAgent(로그인할 때 프로그램을 띄우는 macOS 설정) `homebrew.mxcl.openshell`
  - `gateway.env`: 1단계에서 `printf`로 썼고(os-test transcript [G1], 1단계 재현 절차 1), 2단계에서 NemoClaw가 다시 썼다(demo transcript [N2]). `nemoclaw uninstall`(기본 포트 8080, `--keep-openshell` 없이)이 NemoClaw 항목을 지우고 다른 항목은 남긴다 `[사실: commands.mdx 3740~3742행, run-plan.ts 1337~1371·3453~3469행]`. 1단계에 쓴 두 줄이 지금 파일에 남았는지는 `[미확인]`(파일을 열지 않는다).
  - LaunchAgent: Homebrew 서비스 파일이고 NemoClaw가 다시 썼다([N2]). NemoClaw uninstall은 macOS Homebrew 서비스를 남긴다(commands.mdx 3742행). `brew services stop`(위 OpenShell 항목)은 로그인 때 띄우는 등록을 푼다(manpage). 파일 자체를 지우는 명령은 `[미확인]`.
- Docker 이미지(openclaw-sandbox, openshell-community base, `x1-probe:x1`, `openshell/sandbox-from:1790231913`)
  - `nemoclaw gc --dry-run`으로 등록된 샌드박스와 연결되지 않은 `openshell/sandbox-from`·`nemoclaw-sandbox-local` 이미지를 먼저 본 뒤 `nemoclaw gc`로 지운다 `[사실: commands.mdx 3657~3668행]`. 1단계 이미지 `openshell/sandbox-from:1790231913`이 여기에 드는지는 `[미확인]`.
  - `nemoclaw x1-demo destroy`는 온보딩 때 만든 호스트 Docker 이미지를 지운다(같은 문서 2013~2015행).
  - `x1-probe:x1`과 공동체 base 이미지(`ghcr.io/nvidia/openshell-community/sandboxes/base:latest`): `docker image rm x1-probe:x1 ghcr.io/nvidia/openshell-community/sandboxes/base:latest`. Docker 공식 문서는 `docker image rm`을 "Remove one or more images"라고 적고, "You cannot remove an image of a running container unless you use the -f option"이라고 적는다 `[사실: https://docs.docker.com/reference/cli/docker/image/rm/]`. `nemoclaw gc`가 1단계 이미지 `openshell/sandbox-from:1790231913`을 지우지 않으면 같은 명령으로 지운다 `[추론]`.
- 게이트웨이(127.0.0.1:8080)와 호스트 전달 프로세스(127.0.0.1:18789)
  - 전달 프로세스: `nemoclaw x1-demo stop`이 컨테이너를 멈춘 뒤 그 샌드박스의 호스트 대시보드 전달을 멈추려 한다. 공유 호스트 게이트웨이는 계속 돈다 `[사실: commands.mdx 1529~1556행]`.
  - 게이트웨이: Homebrew 서비스다. 중지는 위 OpenShell 항목의 `brew services stop nvidia/openshell/openshell`이다(manpage). 멈추면 시연 경로가 돌지 않는다.

### 키 사본

키 사본의 위치와 키를 교체할 때 정리할 곳은 오래 가는 운영 문서인 `docs/operations.md`의 "키 사본 위치와 교체 때 정리할 곳" 절로 옮겼다. 어느 곳도 열지 않는다.
