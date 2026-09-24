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

# 9. 증거 수집과 정리
openshell logs x1-os-test --since 30m -n 3000
openshell policy get x1-os-test --full
openshell sandbox download x1-os-test /sandbox/x1-runs artifacts/runs/
openshell sandbox delete x1-os-test
openshell provider delete x1-nvidia
openshell provider profile delete x1-nvidia-chat
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

# 3. 첫 점검과 요건 (c) 키 조회(OpenClaw 요청 전)
openshell policy get x1-demo --full
openshell provider list; openshell sandbox provider list x1-demo; openshell inference get
openshell sandbox upload x1-demo spikes/x1/key_check.py /tmp/x1-tools/
openshell sandbox exec -n x1-demo --timeout 240 -- /usr/bin/python3 /tmp/x1-tools/key_check.py /

# 4. 요건 (b) 구성: 추론 경로 삭제 -> OpenClaw가 NIM을 직접 부르게 설정 -> 축소 정책(최종 4판: nvidia 블록 하나)
openshell inference delete
#    /sandbox/.openclaw/openclaw.json의 models.providers.inference: baseUrl을 https://integrate.api.nvidia.com/v1로,
#    apiKey를 샌드박스 환경변수 NVIDIA_INFERENCE_API_KEY의 자리표시 값으로 바꾸고 .config-hash를 다시 계산한다
#    (샌드박스 안 python으로 수정, 자리표시 형식이 아니면 쓰지 않는다. 원본은 openclaw.json.x1-backup)
openshell policy set x1-demo --policy spikes/x1/policy/x1-demo-narrowed.policy.yaml --wait

# 5. CLI 런타임(호스트에서 만든 이미지 x1-probe:x1의 /opt/x1: Python 3.12 + nvidia-nat 1.9.0)과 스킬 넣기
docker create --name x1tmp x1-probe:x1 && docker cp x1tmp:/opt/x1 - | gzip -1 > x1opt.tar.gz && docker rm x1tmp
openshell sandbox upload x1-demo x1opt.tar.gz /tmp/x1-tools/
#    샌드박스 안에서 /sandbox/x1opt로 풀고, spikes/x1의 x1_probe.py·key_check.py·nat_workflow.yml을 app/에,
#    spikes/x1/demo/run_probe.sh를 /sandbox/x1opt/run_probe.sh에 둔다
nemoclaw x1-demo skill install spikes/x1/skill/x1-probe/
nemoclaw x1-demo gateway restart

# 6. 요청 전 키 조회를 한 번 더 한 뒤 한 줄 경로
openshell sandbox exec -n x1-demo --timeout 240 -- /usr/bin/python3 /tmp/x1-tools/key_check.py /
nemoclaw x1-demo agent --agent main --json --timeout 300 \
  -m "Run the X1 probe now: use the x1-probe skill with the one-line input 'Reply with exactly: X1 OK', then return the JSON line printed by the command exactly as it is."
openshell logs x1-demo --since <기간> -n 3000
#    커밋한 demo 로그(17:20:31~17:57:27, 37분)를 만든 수집 명령은 기록이 없다 [미확인]. 앞 판의 --since 10m은
#    그 로그를 만든 명령이 아니다. openshell logs는 크기가 정해진 버퍼에서 읽어 행이 빠질 수 있다(첫 줄 경고,
#    OpenShell v0.0.116 docs/observability/accessing-logs.mdx 38·60행). 완전한 기록은 샌드박스 안 /var/log/openshell.*.log다
openshell sandbox download x1-demo /sandbox/x1-runs artifacts/runs/
```

주의

- 게이트웨이 재시작 뒤 `openshell sandbox exec`가 `--timeout`을 넘겨 돌아오지 않은 일이 있었다. exec는 한 번에 하나씩, 호스트 쪽 감시 시간을 두고 돌린다.
- `nemoclaw … agent`는 OpenClaw 결과에 `replayInvalid: true`가 있으면 종료 코드 1을 낸다. 결과 JSON의 `status`와 `payloads`를 함께 본다.

되돌리기(시연 샌드박스를 NemoClaw 기본 상태로)

```bash
openshell policy set x1-demo --policy <온보딩 직후 정책: artifacts/openshell/logs/20260924-x1-demo-policy.txt 1절의 YAML 본문> --wait
openshell inference set --provider nvidia-prod --model nvidia/nemotron-3-super-120b-a12b
#    샌드박스 안에서 /sandbox/.openclaw/openclaw.json.x1-backup을 openclaw.json으로 되돌리고 .config-hash를 다시 계산한 뒤
nemoclaw x1-demo gateway restart
# 또는 샌드박스 삭제: nemoclaw x1-demo destroy
```
