# OpenShell 위반 시험표 — X1

- 작성: 2026-09-24(목) 16:00 KST, 작업 X1(세로형 최소 통합 시험, 모델 트랙 M).
- 근거 태그: `[사실]` 직접 실측·확인, `[추론]` 근거가 있는 판단, `[DESIGN]` 팀 설계, `[미확인]` 확인하지 않음.
- 용어
  - OpenShell: 에이전트를 격리해 돌리는 NVIDIA 샌드박스 런타임. 게이트웨이(샌드박스의 바깥 요청을 받아 정책을 적용하고 전달하는 구성요소)와 샌드박스로 이뤄진다.
  - provider: 게이트웨이에 등록한 자격 증명 묶음. 샌드박스 안 프로세스는 자리표시 값(placeholder, 실제 키 대신 넣는 참조 문자열)만 보고, 게이트웨이가 나가는 요청에서 실제 키로 바꾼다.
  - L4·L7: L4는 목적지(host:port)와 실행 파일 수준 판정, L7은 HTTP 요청 수준(method·path) 판정이다.
  - Landlock: 리눅스 커널의 파일시스템 접근 제한 기능.
  - OCSF: OpenShell 감사 로그 행이 따르는 보안 이벤트 형식(Open Cybersecurity Schema Framework).
  - NemoClaw: OpenShell 위에서 에이전트를 돌리는 NVIDIA 참조 스택. OpenClaw는 그 기본 하네스(모델이 도구를 부르며 일하도록 감싸는 실행 틀)다.
  - NIM: NVIDIA 클라우드 추론 API. NAT: NVIDIA NeMo Agent Toolkit(실행 추적·평가 도구 모음).
  - colima: macOS에서 Docker용 리눅스 가상 머신을 띄우는 도구.
- 증거 파일(모두 `artifacts/openshell/logs/`)
  - `x1-os-test`(1단계, §1~§4)
    - 감사 로그 전체: `20260924-x1-os-test-openshell-logs.txt`(§1~§4의 "로그 N행"은 이 파일의 행 번호)
    - 명령·종료 코드·출력: `20260924-x1-os-test-transcript.txt`(§1~§4의 "[ID]"는 이 파일의 항목)
    - 라이브 정책 조회: `20260924-x1-os-test-policy.txt`, OpenShell 기본 정책: `20260924-x1-default-base-policy.txt`
    - NIM 1회 호출과 NAT 실행 추적 발췌: `20260924-x1-nim-run-excerpt.txt`
  - `x1-demo`(2단계 시연 샌드박스, §6)
    - 감사 로그: `20260924-x1-demo-openshell-logs.txt`(§6의 "demo 로그 N행"은 이 파일의 행 번호)
    - 명령·종료 코드·출력: `20260924-x1-demo-transcript.txt`(§6의 "[ID]"는 이 파일의 항목)
    - 라이브 정책·provider·추론 경로 조회: `20260924-x1-demo-policy.txt`
- 경로 표기: 개발 기계의 경로는 자리표시(`<colima Docker 소켓>`, `<OpenShell 설정 폴더>`, `<NemoClaw 설정 폴더>`, `<NemoClaw 게이트웨이 상태 폴더>`)로 적었다. 찾는 방법은 `spikes/x1/README.md`의 "자리표시" 절에 있다. 정책 조회·감사 로그·키 조회 결과에 나오는 `/usr/local/bin/…`, `/home/linuxbrew`, `/home/sandbox`, `/root`, `/sandbox/…` 같은 절대경로는 샌드박스(컨테이너) 안 경로다. 라이브 정책과 조회 결과를 그대로 옮긴 증거라 바꾸지 않았다

## 0. 요약

- 1단계(15:19~16:07): NemoClaw 설치기가 "NemoClaw license and third-party software notice" 수락을 요구해 멈췄다. 그동안 **OpenShell만 쓰는 시험 샌드박스 `x1-os-test`**에서 개발 플랜 §5.3의 `[미확인]` 항목을 실측했다(§1~§4). 이 샌드박스는 시연 샌드박스도 채점 대상 실행 샌드박스도 아니며, 그 행은 한 줄 경로의 증거가 아니다 `[DESIGN]`.
  - 결과: 키 주입 두 방식 모두 샌드박스 안에서 NIM(NVIDIA 클라우드 추론 API) 200을 받았고, 실제 키는 샌드박스 어디에도 없었다. 네트워크 위반 4종(비허용 호스트, 비허용 바이너리 2종, L7)은 종료 코드와 감사 로그 거부 행으로 막혔다. Landlock 미끼 파일 읽기는 `Permission denied`로 막혔고 로그 행은 없었다 `[사실]`.
- 2단계(17:16~17:58): 사용자 결정 (가)(오케스트레이터 전달)에 따라 고지를 수락하고 NemoClaw v0.0.124를 설치해 **시연 샌드박스 `x1-demo`**를 만들었다(§6).
  - 추론 경로를 지우고, OpenClaw가 `integrate.api.nvidia.com`을 헤더 자리표시 값으로 직접 부르게 하고, 기본 블록을 뺐다.
  - 처음 구성(추론 블록 바이너리 `openclaw`만)에서는 OpenClaw의 모델 호출이 binary-miss로 거부됐다. OpenClaw는 node 스크립트라 게이트웨이 프로세스의 실행 파일이 `/usr/local/bin/node`로 판정되기 때문이다(demo 로그 528~530행) `[사실]`.
  - 오케스트레이터 판단 정정에 따라 추론 블록에 `/usr/local/bin/node`를 더하고 경로는 `POST /v1/chat/completions` 하나로 두었다(3판).
  - **한 줄 경로 통과** `[사실]`: OpenClaw 요청 → `x1-probe` 스킬 → 샌드박스 안 CLI → NIM 1회(HTTP 200) → NAT 실행 추적(이벤트 4개) → 의도적 위반 1건 차단. 증거는 demo 로그 579~587행과 `20260924-x1-demo-nim-run-excerpt.txt`다. NemoClaw 래퍼는 턴 메타데이터의 `replayInvalid=true` 때문에 종료 코드 1을 냈다(OpenClaw 결과는 `status: ok`, `stopReason: stop`, 도구 2건 실패 0).
  - 3판에 남은 `openclaw_gateway_dialback`(자기 주소, `access: full`, rules 없음)을 뺀 **최종 4판**에서도 한 줄 경로가 통과했다(NIM 과부하 오류 2회 뒤 세 번째 요청, demo 로그 722~736행). 이 턴에서는 OpenClaw가 `exec`를 두 번 불러 CLI가 두 번 돌았다(각 실행은 NIM 1회). 위반 시험 4종도 4판에서 다시 막혔다.

## 1. 시험 환경 `[사실]`

| 항목 | 값 |
|---|---|
| 호스트 | macOS 26.5.1, Apple Silicon, colima `default`(CPU 4·메모리 8GiB, Docker 29.5.2, VM은 Ubuntu 24.04 aarch64) |
| OpenShell | 0.0.116. 공식 `install.sh`(Homebrew formula `openshell.rb`, sha256이 NemoClaw v0.0.124의 고정값과 같음)로 설치. 게이트웨이는 `brew services`로 뜨고 compute driver(샌드박스를 띄우는 실행 백엔드)는 `docker` |
| 샌드박스 이미지 | `ghcr.io/nvidia/openshell-community/sandboxes/base:latest` 위에 `spikes/x1/Dockerfile`(Python 3.12.13을 `/opt/x1/python`에, `nvidia-nat` 1.9.0, X1 CLI, 미끼 파일)을 얹었다. 생성 명령은 `openshell sandbox create --from spikes/x1 …` |
| 정책 | 1판 `spikes/x1/policy/x1-os-test.policy.yaml`(네트워크 블록 없음) → 2판·4판 `spikes/x1/policy/x1-os-test.nim.policy.yaml`(블록 `x1_nim_chat` 하나). 4판 라이브 정책 해시(OpenShell이 보고한 값) `3c8009005cf17ccd3e551590f59353f29b94fa72978d17808f50c41517d34eb2` |
| provider | `x1-nvidia`(사용자 프로필 `x1-nvidia-chat`, 샌드박스에 첨부), `x1-nvidia-route`(내장 유형 `nvidia`, `inference.local` 경로용, 첨부 안 함). 둘 다 `spikes/x1/with_nvidia_key.py`로 `--credential NVIDIA_API_KEY`(이름만)를 넘겨 만들었다 |
| 정리 | 시험 뒤 샌드박스·provider 2개·사용자 프로필·추론 경로를 지웠다(transcript 마지막 상태: 샌드박스 0, provider 0, 추론 경로 없음) |

## 2. 위반 시험표 — `x1-os-test`(OpenShell 단독 시험 샌드박스)

분류는 03 문서 §6.4를 따른다: 종료 상태가 정수가 아니면 `incomplete`, 거부 문구(`Permission denied`, 프록시 403 등)가 있으면 `access-denial`, 종료 코드 0이면 `completed`, 그 밖은 `command failed`. 예측은 03 문서 §3의 평가 규칙으로 계산했다.

| # | 요건 | 입력(실행 파일 → 목적지·method·path / 파일) | 예측 | 종료 코드 | HTTP | 분류 | 로그 근거 | 일치 |
|---|---|---|---|---|---|---|---|---|
| V0a | (b)(c) | `/opt/x1` python → `integrate.api.nvidia.com:443` `POST /v1/chat/completions`, provider는 첨부했지만 네트워크 블록 없음(1판) | deny(블록 없음) | 4 | CONNECT 403 | access-denial | 55행 `NET:OPEN [MED] DENIED … [reason:network connections not allowed by policy]`, [N0] | O |
| V0 | 대조군(c)(d) | 같은 요청, 2판(`x1_nim_chat`), 헤더에 자리표시 값 | allow(`x1_nim_chat`) | 0 | 200 | completed | 80·81행(L4·L7 허용), 297·298행(NAT 완전판), [N1]·[N3] | O |
| V1 | (b) 비허용 호스트 | `/opt/x1` python → `api.github.com:443` `GET /zen` | deny(endpoint-miss) | 4 | CONNECT 403 | access-denial | 106행 `[reason:endpoint api.github.com:443 is not allowed by any policy]` | O |
| V2 | (b) 비허용 바이너리 | `/usr/bin/curl --fail` → `integrate.api.nvidia.com:443` `POST /v1/chat/completions` | deny(binary-miss) | 22 | 403 | access-denial | 112행 `[reason:binary '/usr/bin/curl' not allowed in policy 'x1_nim_chat' (ancestors: [/opt/openshell/bin/openshell-sandbox] …)]` | O |
| V2b | (b) 비허용 바이너리 | `/usr/bin/python3`(실제 `/usr/bin/python3.12`) → 같은 요청 | deny(binary-miss) | 4 | CONNECT 403 | access-denial | 118행 | O |
| V3 | (b) L7 위반 | `/opt/x1` python → `integrate.api.nvidia.com:443` `GET /v1/models` | deny(L7 불일치) | 3 | 403(본문 `policy_denied`, `layer: l7`) | access-denial | 124행(L4 허용) + 131행 `HTTP:GET [MED] DENIED … [policy:x1_nim_chat engine:l7] [reason:L7_REQUEST deny …]` | O |
| V4 | (a) 정답 경로 읽기 | `cat /srv/x1-decoy/oracle_decoy.json`(미끼 파일, 이미지 빌드 때 허용 목록·`/sandbox` 밖에 둠, 파일 권한 0644) | deny(허용 목록 밖) | 1 | — | access-denial(`Permission denied`) | 로그 행 없음. 허용 목록에 `/srv`가 없음은 `20260924-x1-os-test-policy.txt` | O |
| V4b | (a) | `ls -la /srv/x1-decoy` | deny | 2 | — | access-denial | 로그 행 없음 | O |
| V5 | (c) 키 조회 | `key_check.py`(NIM 호출 전 [K1], 뒤 [K2]): 환경변수 전체·`.env` 파일·하네스 설정 경로 후보·`/proc/<pid>/environ` | 실제 키 0건 | 0 | — | completed | 해당 없음(네트워크 이벤트 아님). [K1]·[K2] 출력: `NVIDIA_API_KEY`는 자리표시 값, 실제 키 0건 | O |
| V6 | 조상 상속 | `/opt/x1` python이 띄운 `curl` → `POST /v1/chat/completions` | allow(조상 상속, 03 문서 §3.3) | 22 | 400 | command failed | 331·332행 `ALLOWED /usr/bin/curl(278) … [policy:x1_nim_chat]`. 400은 빈 본문에 대한 상류 응답으로 본다 `[추론]` | O |
| V6b | (b) + 조상 상속 | 같은 방식의 `curl` → `api.github.com:443` | deny(endpoint-miss) | 22 | 403 | access-denial | 338행 | O |
| V7 | (b) `inference.local` | `curl`·시스템 python → `inference.local:443` `GET /v1/models`, 정책에 `inference.local` 블록 없음 | deny(블록 없음, 03 문서 §3.1) | 0 | 200 | completed | 165·166·176·177행 `NET:OPEN [INFO] ALLOWED inference.local:443`(블록 이름·바이너리 없음) | **X** |
| V8 | (b) `inference.local` | 정책 3판에 `inference.local` 블록(`POST /v1/chat/completions`, `/opt/x1/python/**`)을 더한 뒤 `curl`·`/opt/x1` python → `GET /v1/models` | deny | 없음(응답 없이 멈춤, 수동 종료) | — | incomplete | 184행(3판 적재)과 205행(되돌림) 사이에 해당 행 없음. 되돌린 뒤 V7과 같은 동작 복귀([T5c], 213행) | 판정 불가 |

- V7 불일치의 뜻 `[사실]`: OpenShell 0.0.116에서 `inference.local`은 샌드박스 네트워크 정책과 따로 게이트웨이 라우터가 처리한다. 블록이 없어도 모든 바이너리가 쓸 수 있고, 라우터는 `openai_chat_completions, openai_completions, openai_responses, openai_embeddings, model_discovery`를 받는다(155행). 그래서 이 경로에는 요건 (b)의 "method·path 명시와 바이너리 제한"을 샌드박스 정책으로 걸 수 없었다. 블록을 두면 좁혀지는지는 V8이 멈춰 확인하지 못했다 `[미확인]`.
- 추론 경로는 작업 공간(workspace, 게이트웨이 안의 자원 범위) 단위다 `[사실]`: `openshell inference set`은 작업 공간 `default`에 경로를 만들었고(transcript [I3]), `x1-os-test`는 그 경로의 provider(`x1-nvidia-route`)를 첨부하지 않았는데도 V7에서 경로를 썼다. 따라서 같은 게이트웨이·같은 작업 공간에 추론 경로가 있으면 거기서 도는 모든 샌드박스(채점 대상 실행 샌드박스 포함)가 자기 정책과 관계없이 어떤 바이너리로든 NVIDIA 추론(위 5종)을 쓸 수 있다 `[추론]`. NemoClaw 온보딩은 이런 경로를 설정한다고 문서에 적혀 있다 `[사실: NemoClaw 저장소 docs/inference/how-inference-routing-works.mdx]`. 채점 대상 실행 샌드박스는 추론 경로가 없는 게이트웨이나 작업 공간에서 돌려야 요건 (b)를 정책으로 보일 수 있다 `[추론]`. 별도 `--workspace`가 경로를 격리하는지는 `[미확인]`이다(MT5·MT7 입력).
- 해석 규율(03 문서 §6.6): 일치는 시험한 그 행동에 대한 예측만 지지한다. V4의 거부 주체는 로그가 없어 정책 조회와 파일 권한으로 가렸다(파일 권한은 읽기를 허용했으므로 Landlock 거부로 본다 `[추론]`).

## 3. `openshell logs` 행 형식 `[사실]`

행 머리는 `[<유닉스 시각(초.밀리초)>] [<gateway|sandbox>] [<수준·출처>] [<대상>] ` 이다. 네트워크·정책 이벤트는 `[OCSF ] [ocsf]` 뒤에 이벤트 이름이 온다.

| 이벤트 | 형식(실측) | 행 |
|---|---|---|
| L4 거부 | `NET:OPEN [MED] DENIED <실행 파일 실제 경로>(<pid>) -> <host>:<port> [policy:- engine:opa] [reason:<사유>]` | 55·106·112·118·338 |
| L7 거부 | `HTTP:GET [MED] DENIED GET http://<host>:443<path> [policy:<블록> engine:l7] [reason:L7_REQUEST deny …]` | 131 |
| L4 허용 | `NET:OPEN [INFO] ALLOWED <실행 파일>(<pid>) -> <host>:<port> [policy:<블록> engine:opa]` | 80·124·297·331 |
| L7 허용 | `HTTP:POST [INFO] ALLOWED POST http://<host>:443<path> [policy:<블록> engine:l7]` | 81·298·332 |
| `inference.local` 허용 | `NET:OPEN [INFO] ALLOWED inference.local:443` 다음 줄 `[INFO ] [openshell_router] routing proxy inference request … endpoint=… method=… path=… protocols=…` | 154·155 |
| 정책 재적용 | `CONFIG:DETECTED [INFO] Settings poll: config change detected [old_revision:… new_revision:… policy_changed:true provider_env_changed:false]`, 이어서 `CONFIG:LOADED [INFO] Policy reloaded successfully [policy_hash:<64자리 16진수>] [hash:…]` | 69·72, 181·184, 205·208 |
| 생성 때 정책 | `CONFIG:LOADED [INFO] Acknowledged initial policy revision as loaded [version:1] [hash:…]` | 30 |
| Landlock | 생성 때 `CONFIG:PROBED … Landlock filesystem sandbox available [abi:v4 …]`, 명령마다 `CONFIG:APPLYING … [abi:V2 compat:BestEffort ro:6 rw:3]`·`CONFIG:BUILT … [rules_applied:9 skipped:0]` | 27, 28·29, 45·46 등 |
| 파일시스템 거부 | 행 없음(`--level debug`에서도 없음) | — |

- 거부 사유 문구는 03 문서의 예측 진단(endpoint-miss·binary-miss·L7 불일치)과 대응한다. binary-miss 행에는 조상 프로세스 목록과 명령줄이 함께 찍힌다 `[사실]`.
- `CONFIG:LOADED`는 `openshell policy set`으로 다시 불러올 때마다(3번) 남았다. 같은 내용을 다시 불러오면 revision은 바뀌고 `policy_hash`는 같았다(72행과 208행). `openshell policy get --full`의 `Hash:` 값과 같다 `[사실]`.

## 4. 개발 플랜 §5.3 `[미확인]` 항목의 확인 결과

| 항목 | 결과 | 근거 |
|---|---|---|
| Docker 안 Landlock 집행(요건 (a)) | **집행됨**(`x1-os-test`, colima VM 커널). 커널 ABI v4, 적용 V2 BestEffort. 미끼 파일 읽기 EACCES. 시연 샌드박스는 미실시 | V4·V4b, 27행 |
| 키 주입: 헤더에 키를 넣을 수 있는지 | **된다.** 자리표시 값을 `Authorization: Bearer` 헤더에 실으면 게이트웨이가 실제 키로 바꿨다(NIM 200). 프로필 선언은 `auth_style: bearer`, `header_name: authorization` | V0, [N1]·[N3], `spikes/x1/policy/x1-nvidia-chat.profile.yaml` |
| 키 주입: `inference.local` 전달 | **된다**(NIM 200). 단, 클러스터 추론 경로는 내장 유형 provider만 받고(사용자 프로필 유형은 거부), 정책 블록 없이 모든 바이너리에 열린다 | [I1]~[I3], [N2], V7 |
| `openshell logs` 거부·허용 행 형식, 파일시스템 거부 로그 | §3. 허용·거부 모두 L4·L7 행이 남는다. 파일시스템 거부는 남지 않는다 | §3 |
| 정책 재적용 때 `CONFIG:LOADED` | 재적용마다 남는다. 형식은 §3 | 72·184·208행 |
| 샌드박스 밖에서 `openshell sandbox exec -n <이름> -- <명령>` | 동작한다. CLI가 원격 명령의 종료 코드를 그대로 돌려준다(V1~V4b의 4·22·3·1·2). `--timeout` 옵션이 있다 | transcript 전체 |
| 저장소 파일·봉인 입력 반입 방식 | 관찰만: 이미지 빌드(`sandbox create --from <Dockerfile 폴더>`, `.dockerignore`가 Dockerfile도 걸러 내므로 `!Dockerfile` 필요), `sandbox upload <로컬> <샌드박스 경로>`(`/tmp`로 가능), `sandbox download`는 `/sandbox` 작업 폴더 아래만. 읽기 전용 반입·봉인 입력은 미실시(MT5 몫) | [S1], transcript [T1..T4b] 머리 |
| NAT 실행 추적 산출물 위치 | CLI의 `--runs-dir`(샌드박스 안 `/sandbox/x1-runs/<run_id>/`)에 `nat_trace.jsonl`·`app_trace.jsonl`을 쓰고 `sandbox download`로 `artifacts/runs/<run_id>/`에 받는다. NAT 1.9.0 파일 내보내기는 `stop()`에서 백그라운드 쓰기를 기다리지 않아 끝 이벤트가 빠졌고, CLI가 남은 작업을 기다리게 고쳐 4개 이벤트가 모두 남았다 | `20260924-x1-nim-run-excerpt.txt` |
| 하네스 자체의 추론 경로 | **확인(2단계)**: NemoClaw 기본은 OpenClaw 모델 provider `inference`가 `https://inference.local/v1`(더미 키, 길이 6)이고 게이트웨이 작업 공간 경로 `nvidia-prod`로 NIM에 간다. 시험 구성에서는 `https://integrate.api.nvidia.com/v1`과 헤더 자리표시 값으로 바꿨고, OpenClaw의 모델 호출이 200을 받았다(게이트웨이 로그 `[model-fetch] … status=200`). 게이트웨이 프로세스의 실행 파일은 `/usr/local/bin/node`다 | §6, demo transcript [C2]·[C3]·[A2] |
| 조상 프로세스 상속 | `x1-os-test`에서 **문서대로 동작**(V6·V6b). 시연 샌드박스에서도 **확인**: OpenClaw(node)가 띄운 CLI의 python(`/sandbox/x1opt/python/…/python3.12`)은 `nvidia` 블록 바이너리 목록에 없는데도 `[policy:nvidia]`로 허용됐다. node가 띄운 `curl`도 L4를 통과했다(DT3). 목적지·L7 제한은 그대로였다(CLI의 api.github.com 거부, DT3·DT4) | V6·V6b, §6 DA2·DT3·DT4 |
| 기본 블록 제거·축소 뒤 하네스 동작 | **돈다(3판·4판)**: 기본 블록 5개(`clawhub`·`openclaw_api`·`openclaw_docs`·`npm_registry`·`managed_inference`)를 빼고 추론 블록을 `POST /v1/chat/completions` 하나로 좁혀도 하네스가 돌았다. 4판에서는 `openclaw_gateway_dialback`까지 빼고 `nvidia` 블록 하나만 남겼는데도 돌았다. 단, 바이너리를 `openclaw`만 두면(2판) binary-miss로 거부돼 실제 실행 파일 `/usr/local/bin/node`를 넣어야 했다 | §6 DA1·DA2·DA4 |
| OpenClaw가 SKILL.md로 CLI를 부르는 방식 | **확인**: `nemoclaw x1-demo skill install spikes/x1/skill/x1-probe/`로 `/sandbox/.openclaw/workspace/skills/x1-probe`에 넣었다(ready). 요청 턴에서 OpenClaw가 `read`로 SKILL.md를 읽고 `exec`로 `/sandbox/x1opt/run_probe.sh`를 실행했다(도구 2건, 실패 0). CLI 결과 JSON을 고치지 않고 그대로 돌려줬다 | demo transcript [S1]·[A2] |
| 하네스가 띄운 프로세스의 키 조회 | **확인**: 하네스가 띄운 CLI 안에서(`--key-check`) 실제 키 0건. 이 프로세스에서는 `/proc/<pid>/environ` 16개를 읽을 수 있었다(하네스 게이트웨이 프로세스 포함 추정, 못 읽음 3). exec 세션에서는 하네스 environ을 읽을 수 없었다(읽음 1, 못 읽음 13) | §6 DH·DK1~DK3 |
| 같은 사용자 `/proc/<pid>/environ` 읽기 | 같은 exec 세션의 같은 사용자 프로세스는 읽혔다(3개). 감독 프로세스(root, pid 1)와 샌드박스 주 프로세스(pid 37, 사용자 sandbox)는 읽히지 않았다(2개). 실제 키는 0건 | [K2] |
| 미끼 파일 배치 | 이미지 빌드 때 `/srv/x1-decoy/`(모든 허용 prefix 밖, `/sandbox` 밖)에 두었다 | `spikes/x1/Dockerfile` |

## 5. 시연 샌드박스 첫 점검

2단계에서 실시했다. 결과는 §6에 있다.

## 6. 시연 샌드박스 `x1-demo` — 2단계(NemoClaw v0.0.124)

### 6.1 환경 `[사실]`

| 항목 | 값 |
|---|---|
| NemoClaw | v0.0.124(커밋 6f3cced). 고지 수락 기록 `<NemoClaw 설정 폴더>/usage-notice.json`(acceptedVersion `2026-04-01b`, 수락 시각 17:17:07 KST) |
| OpenClaw | 2026.7.1. `/usr/local/bin/openclaw` → `…/openclaw-runtime/node_modules/openclaw/openclaw.mjs`(첫 줄 `#!/usr/bin/env node`). 게이트웨이 프로세스 이름은 `openclaw-gateway`, 실행 파일은 `/usr/local/bin/node`(demo 로그 528행) |
| 게이트웨이 | NemoClaw가 1단계의 Homebrew 게이트웨이 서비스를 다시 구성했다: `gateway.env`를 다시 쓰고(포트 8080, 상태 `<NemoClaw 게이트웨이 상태 폴더>`), 같은 LaunchAgent로 띄운다. 활성 게이트웨이는 `nemoclaw`(127.0.0.1:8080). 17670 게이트웨이는 더 뜨지 않는다 |
| 온보딩 | `nemoclaw onboard --non-interactive --fresh --name x1-demo`, provider `build`, 모델 `nvidia/nemotron-3-super-120b-a12b`, 정책 등급 `restricted`, 정책 모드 `skip`, 웹 검색 없음. 키는 래퍼(`--export-as NVIDIA_INFERENCE_API_KEY`)로만 넘겼다. 종료 코드 0, 출력의 키 접두어 0건 |
| provider | `nvidia-prod`(유형 `nvidia` 내장 프로필, 헤더 bearer 방식, 자격 증명 키 이름 `NVIDIA_INFERENCE_API_KEY`). 샌드박스에 첨부됨. `providers_v2_enabled` 미설정 |
| 추론 경로 | 온보딩이 작업 공간 `default`에 `nvidia-prod` / `nvidia/nemotron-3-super-120b-a12b`를 설정했다. 시스템 경로는 없음. 17:23:36에 지웠다([D1]) |

### 6.2 첫 점검 결과

| 항목 | 결과 |
|---|---|
| 라이브 정책 조회 | 온보딩 직후 1판: hash `eae30384063fdb68f2703b77d8c3ca50097228eca4342780c276deee72442ab0`, 블록 7개(`clawhub`, `managed_inference`, `npm_registry`, `nvidia`, `openclaw_api`, `openclaw_docs`, `openclaw_gateway_dialback`). 축소 2판(추론 블록 바이너리 `openclaw`만): `4b11db0cf916a87718dd9cf3dd18d37a3411e5c82feff0d02226d549cbc02ccd`. 3판(`/usr/local/bin/node` 추가): `ea1461d49c8dea779e1e6dae6b47788a01fbd11eacd118b633feedfd8ab28495`. **최종 4판**(3판에서 `openclaw_gateway_dialback` 제거, 커밋한 `spikes/x1/policy/x1-demo-narrowed.policy.yaml`과 본문 같음): `721639afbd5972b5ea5b71a1a72979277245783a7d4b706b06b776c1856d3372`. 정적 계층은 네 판 모두 같다(`20260924-x1-demo-policy.txt`) |
| provider 설정 조회 | 6.1의 provider·추론 경로 행. 조회 결과에 자격 증명 값은 없다 |
| 남은 블록 목록(최종 4판) | `nvidia` 하나: `integrate.api.nvidia.com:443` `POST /v1/chat/completions` 하나, 바이너리 `/usr/local/bin/openclaw`·`/usr/local/bin/node`. 3판까지 남겼던 `openclaw_gateway_dialback`(`10.200.0.2:18789·18790`, `access: full`, `tls: skip`. 10.200.0.2는 샌드박스 자신의 veth 주소, 프록시는 10.200.0.1:3128)은 rules가 없는 블록이라 4판에서 뺐고, 빼도 한 줄 경로가 통과했다(DA4) |
| 요건 (b) 판정 | **충족(최종 4판)** `[사실: 4판 정책 본문, DA4, DT1'~DT4']`. 블록은 `nvidia` 하나이고, 외부 목적지는 NVIDIA 추론 엔드포인트 한 곳, L7은 `POST /v1/chat/completions` 하나다. `rules` 생략 블록과 범용 바이너리 + `/**` 조합이 없다. 범용 바이너리 node의 허용을 추론 요청 한 경로로 좁혔다(개발 플랜 §4.1 작성 원칙). 3판은 rules 없는 `openclaw_gateway_dialback`이 남아 있어 이 판정에 쓰지 않는다. 템플릿과 다른 점은 아래 행이다 |
| 하드닝 템플릿(03 문서 §5)과 다른 점 | ① 템플릿은 추론 블록 바이너리를 `openclaw`만 두라고 했지만, OpenClaw 2026.7.1의 `openclaw`는 `#!/usr/bin/env node` 스크립트라 실행 파일이 node로 판정된다. 그래서 추론 블록에 `/usr/local/bin/node`를 넣고 경로를 하나로 좁혔다. 그 결과 샌드박스 안의 **모든 node 프로세스와 그 자손**이 NIM 채팅 경로를 쓸 수 있고, provider의 자리표시 값이 모든 프로세스 환경에 있으므로 그 요청에는 키가 주입된다 `[추론]`. ② 템플릿의 `managed_inference`(`inference.local`)는 남기지 않고 뺐다(추론 경로도 삭제). ③ NemoClaw 기본 정책에만 있는 `openclaw_gateway_dialback`(자기 주소, `access: full`)도 4판에서 뺐다. ④ OpenClaw의 exec 도구가 띄우는 모든 프로세스가 node의 허가를 물려받는다(DT3에서 node가 띄운 `curl`이 L4를 통과). 그래서 모델이 조종하는 에이전트는 자기가 띄운 어떤 실행 파일로도 키가 주입되는 채팅 요청을 보낼 수 있고, 남는 제한은 method·path 규칙과 목적지뿐이다 `[추론]` |
| 하네스가 띄운 프로세스의 키 조회 | 실제 키 0건(DH·DH2). 하네스가 띄운 프로세스는 `/proc/<pid>/environ`을 14~16개 읽을 수 있었다. 그 안에는 하네스 게이트웨이 프로세스의 환경(`OPENCLAW_GATEWAY_TOKEN` 포함 추정)이 들어 있을 수 있다 `[추론]`. exec 세션 조회 4회도 0건(DK1~DK4) |

### 6.3 시험표 — `x1-demo`

| # | 입력 | 예측 | 종료 코드 | HTTP | 분류 | 로그 근거 | 일치 |
|---|---|---|---|---|---|---|---|
| DK1 | 요건 (c) 키 조회(`/usr/bin/python3 /tmp/x1-tools/key_check.py /`), 온보딩 직후·OpenClaw 요청 전 | 실제 키 0건 | 0 | — | completed | 해당 없음. demo transcript [K1]: 환경변수 이름은 `NVIDIA_INFERENCE_API_KEY`(자리표시 값)와 `OPENCLAW_GATEWAY_TOKEN`(샌드박스 안 OpenClaw 게이트웨이 토큰, NVIDIA 키 아님). `/proc` environ 읽음 1, 못 읽음 13 | O |
| DV7 | 추론 경로 삭제 뒤 `curl`·시스템 python → `inference.local` `GET /v1/models` | 실패 | curl 0(`--fail` 없음), python 3 | 503(`cluster inference is not configured`) | command failed | demo 로그 300행 `CONFIG:UPDATED … user_route_count:0`, 311·317행(L4 허용 뒤 라우터가 503) | O |
| DP1 | 축소 2판 적용 | 적재 | 0 | — | completed | demo 로그 328행 `CONFIG:DETECTED`, 333행 `CONFIG:LOADED [policy_hash:4b11db0c…]` | O |
| DK2 | 요건 (c) 키 조회, 설정 수정·2판·게이트웨이 재시작 뒤 | 실제 키 0건 | 0 | — | completed | demo transcript [K2] | O |
| DA1 | 2판에서 OpenClaw 요청 → 게이트웨이(node) → `POST /v1/chat/completions` | deny(binary-miss: 실행 파일 node ≠ `openclaw.mjs`) | 1 | —(CONNECT 거부) | access-denial | demo 로그 528~530행 `DENIED /usr/local/bin/node(5073) … binary '/usr/local/bin/node' not allowed in policy 'nvidia'`, 87·88·331·332행 `Resolved policy binary symlink … openclaw.mjs` | O |
| DP2 | 3판 적용(`/usr/local/bin/node` 추가) | 적재 | 0 | — | completed | demo 로그 563행 `CONFIG:LOADED [policy_hash:ea1461d4…]` | O |
| DK3 | 요건 (c) 키 조회, 3판 뒤·요청 전 | 실제 키 0건 | 0 | — | completed | demo transcript [K3] | O |
| DA2 | **한 줄 경로**: `nemoclaw x1-demo agent --agent main --json -m "…x1-probe…"` → OpenClaw → 스킬 → `run_probe.sh` → CLI → NIM 1회 → NAT → 의도적 위반 | OpenClaw·CLI의 NIM 요청 allow, 위반 deny | 래퍼 1(`replayInvalid=true`), CLI 0 | 200 | completed(래퍼 표시는 incomplete) | 579·581·586행 OpenClaw `ALLOWED … [policy:nvidia]`, 583·584행 CLI python ALLOWED(조상 상속), 585행 위반 `DENIED … api.github.com:443` | O |
| DH | 하네스가 띄운 CLI 안의 키 조회(`--key-check`, NIM 호출 전) | 실제 키 0건 | (CLI 0) | — | completed | CLI JSON `key_check`: `NO_REAL_KEY`, `proc_environ_readable 16`, `unreadable 3`, 실제 키 0 | O |
| DT1 | node의 자손이 아닌 `curl --fail` → `POST /v1/chat/completions` | deny(binary-miss) | 22 | 403 | access-denial | 624행 `DENIED /usr/bin/curl(19851) … not allowed in policy 'nvidia' (ancestors: [/opt/openshell/bin/openshell-sandbox] …)` | O |
| DT2 | node의 자손이 아닌 `/usr/bin/python3`(실제 3.13) → 같은 요청 | deny(binary-miss) | 4 | CONNECT 403 | access-denial | 633행 | O |
| DT3 | node가 띄운 `curl` → `GET /v1/models`(허용 목적지의 다른 경로) | L4 allow(조상 상속), L7 deny | 22 | 403 | access-denial | 642행 L4 `ALLOWED /usr/bin/curl(19923) … [policy:nvidia]`, 643행 `HTTP:GET [MED] DENIED … L7_REQUEST deny GET …/v1/models` | O |
| DT4 | node가 띄운 `curl` → `api.github.com:443` | deny(endpoint-miss) | 22 | CONNECT 403 | access-denial | 652행 `[reason:endpoint api.github.com:443 is not allowed by any policy]` | O |
| DP3 | 최종 4판 적용(`openclaw_gateway_dialback` 제거) | 적재 | 0 | — | completed | demo 로그 678행 `CONFIG:LOADED [policy_hash:721639af…]` | O |
| DK4 | 요건 (c) 키 조회, 4판 뒤·요청 전 | 실제 키 0건 | 0 | — | completed | demo transcript [K4] | O |
| DA3 | 4판에서 같은 요청(17:55:31, 17:55:56) | allow | 1, 1 | 200(SSE 안에 과부하 오류) | command failed | 694·695·712·713행 OpenClaw ALLOWED. 오류는 `FailoverError: The AI service is temporarily overloaded`(NIM 쪽 일시 오류, 정책 거부 아님) | O(정책 판정) |
| DA4 | **4판 한 줄 경로**(17:56:19 재요청) | OpenClaw·CLI의 NIM 요청 allow, 위반 deny | 래퍼 1(`replayInvalid=true`), CLI 0 | 200 | completed(래퍼 표시는 incomplete) | 722·727·735행 OpenClaw ALLOWED, 724·725·732·733행 CLI python ALLOWED(조상 상속), 726·734행 위반 DENIED. OpenClaw가 `exec`를 두 번 불러 CLI 실행 기록이 둘(`20260924T085624-x1-888ea4`, `20260924T085638-x1-b37f25`)이고 각각 NIM 1회 | O |
| DH2 | 4판 한 줄 경로의 CLI 안 키 조회 | 실제 키 0건 | (CLI 0) | — | completed | CLI JSON `key_check`: `NO_REAL_KEY`, `proc_environ_readable 14`, `unreadable 3` | O |
| DT1' | 4판에서 DT1 다시 | deny(binary-miss) | 22 | 403 | access-denial | 798행 | O |
| DT2' | 4판에서 DT2 다시 | deny(binary-miss) | 4 | CONNECT 403 | access-denial | 807행 | O |
| DT3' | 4판에서 DT3 다시 | L4 allow, L7 deny | 22 | 403 | access-denial | 816·817행 | O |
| DT4' | 4판에서 DT4 다시 | deny(endpoint-miss) | 22 | CONNECT 403 | access-denial | 826행 | O |

- DA2의 종료 코드: NemoClaw 래퍼는 OpenClaw 결과 메타데이터에 `replayInvalid: true`가 있으면 종료 코드 1을 낸다(NemoClaw 문서의 `agent` 명령 설명). OpenClaw 결과 자체는 `status: ok`, `summary: completed`, `stopReason: stop`, 도구 `read`·`exec` 2건 실패 0이고, 응답 본문은 CLI JSON 그대로다. `replayInvalid`의 원인은 `[미확인]`이다.
- 관찰: 17:47:58~17:48:01에 운영자 요청 없이 OpenClaw 턴 1건이 더 돌아 모델 호출 2회가 났다(demo 로그 613~616행, 게이트웨이 로그 `via gateway sender`). 원인 `[미확인]`. 하네스는 요청 밖에서도 키가 주입되는 추론을 쓸 수 있다.
- 관찰: 17:25:58 게이트웨이 재시작 뒤 `openshell sandbox exec` 여러 건이 `--timeout`을 넘겨 호스트에서 돌아오지 않았다. 멈춘 exec를 모두 끝내자 정상화됐다. 원인 `[미확인]`. 키 조회 스크립트가 일반 파일만 열도록 고쳤다(demo transcript [H1]).
- 현재 상태(17:58): `x1-demo`는 떠 있고 최종 4판 정책, 추론 경로 없음, `openclaw.json`은 직접 호출로 바뀐 상태다(원본 `/sandbox/.openclaw/openclaw.json.x1-backup`). `/sandbox/x1opt` 런타임과 `x1-probe` 스킬이 들어 있다. 되돌리는 명령은 `spikes/x1/README.md`에 있다.
