# OpenShell Policy YAML 구조 레퍼런스

> **출처 (중요)**: 아래 스키마와 평가 규칙은 DLI 코스가 실제로 배포하는 정책 엔진 소스
> `https://nvdli.github.io/NemoClawDLI/nemoclaw/scripts/_openshell.js`
> 에서 추출했다. 구체적으로 `OPENSHELL_POLICY_HARDENED`(코스 주석: *"a 'shields up' policy read off the live launchable on 2026-06-17"*), `policyToYaml()`, `annotatePolicyYaml()`, 그리고 네트워크/파일시스템 평가 함수 `evalSandboxNetwork()` / `evalSandboxFs()`의 로직이다.
>
> **주의**: 코스 소스 주석이 직접 명시하듯 **"The live sandbox stays the source of truth."**
> 실제 작업 시에는 항상 `openshell policy get <agent> --full`로 라이브 정책을 먼저 읽고, 이 문서는 필드 해석용 레퍼런스로만 쓴다.
>
> **v1.1 (2026-09-23)**: 코스 JS 소스에 없는 두 가지를 **NVIDIA 공식 문서**(https://docs.nvidia.com/openshell/sandboxes/policies , https://docs.nvidia.com/openshell/sandboxes/inference-routing)에서 보강했다: ① `network_middlewares` 섹션과 credential rewrite 옵션(§2.1) ② 정적 vs 동적 계층 — filesystem/landlock/process는 생성 시 고정, network_policies/network_middlewares는 핫리로드(§2.1-1). "(v1.1 추가)"로 표시한 부분은 코스 소스가 아닌 공식 문서 기반이다.

---

## 1. 전체 스키마 한눈에

```yaml
version: 1

filesystem_policy:        # Landlock 규칙: 어떤 경로를 읽고 쓸 수 있나
  include_workdir: true   # 에이전트 작업 디렉토리(/sandbox)를 쓰기 가능으로
  read_only:              # 읽기 가능, 쓰기 불가 (쓰면 EACCES)
    - /usr
    - /lib
    - /proc
    - /dev/urandom
    - /app
    - /etc
    - /var/log
  read_write:             # 쓰기가 허용되는 유일한 경로들
    - /tmp
    - /dev/null
    - /sandbox/.openclaw
    - /sandbox/.nemoclaw
    - /home/linuxbrew

landlock:                 # 커널 수준 파일시스템 집행
  compatibility: best_effort   # 커널이 Landlock을 지원하는 범위에서 적용 (strict enforce 아님)

process:                  # 에이전트가 실행되는 비특권 신원
  run_as_user: sandbox
  run_as_group: sandbox

network_policies:         # egress는 DENY by default. 아래 named 블록이 각각 목적지 집합을 grant
  nvidia:
    endpoints:
      - host: integrate.api.nvidia.com
        port: 443
        rules:
          - allow: { method: POST, path: /v1/chat/completions }
          - allow: { method: POST, path: /v1/completions }
          - allow: { method: POST, path: /v1/embeddings }
          - allow: { method: GET,  path: /v1/models }
          - allow: { method: GET,  path: /v1/models/** }
      - host: inference-api.nvidia.com
        port: 443
        rules:
          - allow: { method: GET, path: /v1/models }
    binaries:
      - /usr/local/bin/openclaw

  managed_inference:
    endpoints:
      - host: inference.local
        port: 443
        rules:
          - allow: { method: GET,  path: /** }
          - allow: { method: POST, path: /** }
    binaries:
      - /usr/local/bin/openclaw
      - /usr/local/bin/node
      - /usr/bin/node
      - /usr/bin/curl
      - /usr/bin/python3

  clawhub:
    endpoints:
      - host: clawhub.ai
        port: 443
        rules:
          - allow: { method: GET,  path: /** }
          - allow: { method: POST, path: /** }
    binaries:
      - /usr/local/bin/openclaw
      - /usr/local/bin/node

  openclaw_docs:
    endpoints:
      - host: docs.openclaw.ai
        port: 443
        rules:
          - allow: { method: GET, path: /** }
    binaries:
      - /usr/local/bin/openclaw

  npm_registry:
    endpoints:
      - host: registry.npmjs.org
        port: 443
        rules:
          - allow: { method: GET, path: /** }
    binaries:
      - /usr/local/bin/openclaw
```

**baseline에서 의도적으로 빠져 있는 것** (코스 소스 주석 그대로):
- `github` 프리셋 (github.com, api.github.com)
- 메시징 프리셋 (telegram / discord / slack)

→ 이들이 **Hermes형 exfiltration 표면**이며, **명시적 온보딩 선택으로만** 부여된다. 해커톤 제출에서 이걸 안 켰다는 사실 자체가 설계 근거로 쓸 만하다.

---

## 2. 필드 레퍼런스

### 2.1 최상위

| 필드 | 타입 | 의미 |
|---|---|---|
| `version` | int | 정책 스키마 버전 (현재 `1`) |
| `filesystem_policy` | object | Landlock이 집행할 경로 규칙 |
| `landlock` | object | 커널 집행 모드 |
| `process` | object | 실행 신원 |
| `network_policies` | map<name, object> | 이름 붙은 egress grant 블록들 |
| `network_middlewares` | object | **(v1.1 추가, 공식 문서 기준)** 허용된 HTTP/WebSocket egress에 게이트웨이가 개입하는 계층. `request_body_credential_rewrite: true` / `websocket_credential_rewrite: true` 옵션으로 **provider credential을 게이트웨이가 주입** → 샌드박스는 API 키를 보지 못함. 코스 JS 소스의 baseline 정책에는 없으므로 라이브 정책에서 확인 |

### 2.1-1 정적 vs 동적 계층 (v1.1 추가 — 출처: https://docs.nvidia.com/openshell/sandboxes/policies)

> 공식 문서 원문: *"A policy has static sections `filesystem_policy`, `landlock`, and `process` that are locked at sandbox creation, and dynamic `network_policies` and `network_middlewares` sections that are hot-reloadable on a running sandbox."*

| 계층 | 섹션 | 변경 시점 | 함의 |
|---|---|---|---|
| **정적** | `filesystem_policy`, `landlock`, `process` | 샌드박스 생성 시 고정 | 바꾸려면 샌드박스 재생성. "작업별 임시 파일 권한 발급" 같은 설계는 **불가** |
| **동적** | `network_policies`, `network_middlewares` | 실행 중 핫리로드 (`openshell policy set`) | TTL 네트워크 리스, runaway 시 egress 즉시 차단, 레드팀 후 정책 패치 등 **런타임 제어는 여기서만** |
| **Inference** | (게이트웨이 설정) | 런타임 변경, 전파 약 5초 | 게이트웨이당 provider 1·model 1(단일 active backend). 모든 샌드박스가 같은 `inference.local` 백엔드를 봄 → **요청 단위 Nano/Ultra 라우팅은 앱 계층 게이트웨이에서** (출처: https://docs.nvidia.com/openshell/sandboxes/inference-routing) |

→ 아이디어 설계 시 함의: I-15(A2A 권한 리스)는 네트워크/credential만, I-10(라우터)는 OpenShell 핫리로드가 아닌 Secure Routing Gateway, N-A(서킷 브레이커)는 네트워크 정책 핫리로드로 구현. 상세는 `IDEA_EXPANSION_CHATGPT_REVIEW.md` §9-1.

### 2.2 `filesystem_policy`

| 필드 | 타입 | 의미 |
|---|---|---|
| `include_workdir` | bool | true면 `/sandbox` 작업 디렉토리를 쓰기 가능으로 취급 |
| `read_only` | string[] | 읽기 가능·쓰기 불가 경로 prefix. 쓰기 시도는 `EACCES` |
| `read_write` | string[] | **쓰기가 허용되는 유일한** 경로 prefix |

### 2.3 `landlock`

| 필드 | 값 | 의미 |
|---|---|---|
| `compatibility` | `best_effort` | 커널이 Landlock을 지원하는 곳에서 적용. **엄격 집행이 아니다.** compatibility mode / OverlayFS / 제한 이전에 열린 핸들은 별도로 고려해야 함 |

### 2.4 `process`

| 필드 | 값 | 의미 |
|---|---|---|
| `run_as_user` | `sandbox` | 비root(0 아닌 UID) |
| `run_as_group` | `sandbox` | 동일 |

`setuid`, `mount`, `ptrace` 같은 상승 프리미티브는 **이 파일이 아니라 seccomp 층에서** 차단된다.

### 2.5 `network_policies.<name>`

| 필드 | 타입 | 의미 |
|---|---|---|
| `endpoints` | array | 허용 목적지 목록 (L4 + 선택적 L7) |
| `binaries` | array<{path}> | **이 grant를 사용할 수 있는 실행 파일**. 이 블록의 핵심 |

### 2.6 `endpoints[]`

| 필드 | 타입 | 의미 |
|---|---|---|
| `host` | string | 호스트명. **와일드카드 가능** (`*`는 한 라벨, `**`는 라벨 경계를 넘음) |
| `port` | int | 단일 포트 |
| `ports` | int[] | 복수 포트 (`port`의 배열 대안) |
| `allowed_ips` | string[] | `host`가 비어 있을 때 IP 기반 매칭용 |
| `rules` | array<{allow:{method,path}}> | L7 제약. **없으면 L4 매칭만으로 통과** |

### 2.7 `rules[].allow`

| 필드 | 값 | 의미 |
|---|---|---|
| `method` | `GET`/`POST`/... 또는 `*` | HTTP 메서드. `*`는 전부 |
| `path` | 경로 glob 또는 `**` | 요청 경로. `**`는 전부 |

---

## 3. 평가(매칭) 규칙 — 이게 정확도의 핵심

### 3.1 네트워크 결정 순서

입력: `{ binary, host, port, method?, path?, ancestors? }`

1. **모든** named 정책 블록을 순회하며 두 조건을 각각 검사한다.
   - **엔드포인트 매칭**: `host` + `port`가 맞는가
   - **바이너리 매칭**: 요청 바이너리가 그 블록의 `binaries`에 있는가
2. 둘 다 만족하는 블록이 **하나도 없으면 → `deny`** (deny by default). 거부 이유에 endpoint-miss / binary-miss 진단이 담긴다.
3. 매칭된 블록이 있고 `method`/`path`가 주어졌다면, **이름 순 정렬 후 첫 블록**의 매칭 엔드포인트에서 L7 검사를 한다. L7 실패 → `deny`(matched 블록 이름과 함께).
4. 통과 → `allow` (matched 블록 이름 반환).

> 3번이 미묘하다: L7 검사는 **이름 알파벳 순 첫 매칭 블록 하나**만 적용된다. 그래서 같은 host:port를 여러 블록이 커버하면 **블록 이름이 결과를 바꿀 수 있다.** 정책을 쓸 때 host:port 중복 커버를 피하는 게 안전하다.

### 3.2 호스트 매칭

- `host`에 `*`가 없으면: 대소문자 무시 **완전 일치** + 포트 포함 여부
- `host`에 `*`가 있으면: glob 매칭 (구분자 `.`) + 포트 포함 여부
- `host`가 비어 있고 `allowed_ips`가 있으면: **포트만** 검사

### 3.3 바이너리 매칭 (해커톤 데모 포인트)

```
후보 집합 = [ 실행 파일 경로(exe path) ] + [ 모든 조상 프로세스 경로 ]
```

- `binaries[].path`에 `*`가 있으면 후보 집합에 대해 glob 매칭 (구분자 `/`)
- 없으면 exe path 완전 일치 **또는** 조상 목록 포함

**핵심**: `argv[0]` / cmdline은 **신뢰하지 않는다 (위조 가능).** exe 경로와 조상 추적으로만 신원을 해석한다. 문서 주석에 `claude spawns node` 예시가 있는 것처럼, 래퍼가 `node`를 띄우면 조상 추적으로 grant가 상속된다.

NemoClaw 문서에는 이에 더해 **trust-on-first-use(TOFU) 해시**로 바이너리 신원을 고정한다고 기술된다.

### 3.4 L7 매칭

- `rules`가 없으면 L4 매칭만으로 충분 (**즉, `rules` 생략은 해당 host:port 전체 개방**)
- `method`는 `*` 또는 대소문자 무시 일치
- `path`는 `**`이거나 glob 매칭 (구분자 `/`)

### 3.5 Glob 의미론

| 패턴 | 동작 |
|---|---|
| `*` | 구분자를 **넘지 않는** 한 세그먼트 (경로에서는 `/`, 호스트에서는 `.`) |
| `**` | 구분자를 **넘어** 전부 |

예: `path: /v1/models/**` → `/v1/models/a/b` 매칭. `path: /v1/*` → `/v1/models` 매칭되지만 `/v1/models/a`는 매칭 안 됨.

### 3.6 파일시스템 결정 순서

입력: `{ path, mode: "read" | "write" }`

1. `read_write` 중 `path`를 포함하는 prefix들을 찾아 **가장 긴 것** 선택
2. `read_only`에서도 동일하게 **가장 긴 것** 선택
3. 두 후보 중 **더 긴 prefix가 승리** (longest matching prefix wins)
4. 아무 prefix도 없으면: `include_workdir`이 true이고 `path`가 `/sandbox` 아래면 `allow`, 아니면 `deny`
5. 승자가 `read_write`면 `allow`. 승자가 `read_only`면 `read`는 `allow`, `write`는 `deny`

> **함의**: `read_only: [/etc]`와 `read_write: [/etc/myapp]`가 공존하면, `/etc/myapp/x`는 더 긴 prefix인 `read_write` 쪽이 이겨서 쓰기가 허용된다. 예외를 만들 때 이 규칙을 이용한다.

---

## 4. 스키마가 커버하지 **않는** 것 (반드시 알아야 함)

코스 소스 주석이 명시적으로 남긴 한계:

> *"The schema has no `tool_policy` or per-file read-only, so `SOUL.md` is guarded by DAC + chattr, not here."*

| 없는 것 | 대안 |
|---|---|
| 툴 단위 정책 (`tool_policy`) | OpenClaw 하네스 층에서 툴 인가·인자 검증 |
| 파일 단위 read-only | POSIX DAC 권한 + `chattr +i` (불변 플래그) + git 이력 |
| seccomp syscall 목록 | 별도 층. `ptrace`/`mount`/`setuid` 등이 여기서 차단되고 거부 시 `EPERM` |
| 런타임 파일/프로세스 권한 변경 | **불가** (정적 계층). 샌드박스 재생성만 가능. 런타임에 바꿀 수 있는 것은 `network_policies` / `network_middlewares` / inference backend뿐 (v1.1, §2.1-1) |
| 샌드박스 밖 credential 보관 | 이 YAML의 코스 baseline에는 없지만 공식 스키마의 `network_middlewares` + `request_body_credential_rewrite`로 가능 (v1.1) |
| 입력 콘텐츠 신뢰 판정 | NeMo Guardrails 등 애플리케이션 층 |
| 허용 채널 위 바이트의 의미 | 정책은 **목적지를 승인할 뿐 의미를 승인하지 않는다** |

---

## 5. 우리 프로젝트용 하드닝 템플릿

> 원칙: baseline에서 **빼는 방향**으로만 수정한다. 새 grant는 위협모델 근거와 함께 PR로.

```yaml
version: 1

filesystem_policy:
  include_workdir: true
  read_only:
    - /usr
    - /lib
    - /proc
    - /dev/urandom
    - /app
    - /etc
  # [변경] /var/log 제거: 로그 읽기는 우리 태스크에 불필요
  read_write:
    - /tmp
    - /dev/null
    - /sandbox/.openclaw
    - /sandbox/.nemoclaw
  # [변경] /home/linuxbrew 제거: brew 설치 경로 쓰기 불필요 (공급망 표면 축소)

landlock:
  compatibility: best_effort

process:
  run_as_user: sandbox
  run_as_group: sandbox

network_policies:
  # [유지·축소] 추론만. 모델 목록 조회가 필요 없으면 GET /v1/models도 제거
  nvidia:
    endpoints:
      - host: integrate.api.nvidia.com
        port: 443
        rules:
          - allow: { method: POST, path: /v1/chat/completions }
          - allow: { method: POST, path: /v1/embeddings }
    binaries:
      - /usr/local/bin/openclaw

  # [축소] managed_inference의 binaries에서 curl/python3 제거.
  # 이유: 범용 바이너리에 와일드카드 경로(/**)를 주면 임의 exfiltration 채널이 된다.
  managed_inference:
    endpoints:
      - host: inference.local
        port: 443
        rules:
          - allow: { method: POST, path: /v1/** }
    binaries:
      - /usr/local/bin/openclaw

  # [제거] clawhub / openclaw_docs / npm_registry
  # 이유: 런타임에 패키지·문서를 받아올 필요가 없다. 이미지 빌드 시점에 고정한다.

  # [부여 안 함] github, telegram, discord, slack
  # 이유: exfiltration 표면. 명시적 승인 없이는 켜지 않는다.
```

### 축소 시 체크 포인트
1. `rules`를 **생략하지 마라.** 생략하면 해당 host:port가 전체 개방된다.
2. `path: /**` + 범용 바이너리(`curl`, `python3`, `node`) 조합이 가장 위험하다. 둘 중 하나는 반드시 좁혀라.
3. 같은 host:port를 여러 블록이 커버하지 않게 하라 (L7 검사가 이름 순 첫 블록에만 적용됨).
4. `read_only`에 민감 경로가 포함되어 있지 않은지 확인하라. **읽을 수 있으면 출력 채널로 나갈 수 있다.**

---

## 6. 검증 절차 (제출 증거 만들기)

### 6.1 라이브 정책 읽기

```bash
openshell policy get <agent> --full
```

- 코스 헬퍼 `helpers.policyGet()`가 이 명령을 오퍼레이터 터미널로 실행하고 YAML 본문을 파싱한다.
- 반환 형태: `{ agent, command, raw, stderr, transcript, status, policy, parseError }`
- **`status`를 확인해 정책이 실제로 active인지 먼저 확인한다.**

### 6.2 예측 (브라우저, 네트워크 미접촉)

```js
helpers.evalSandboxNetwork(
  { binary: "/usr/bin/curl", host: "api.github.com", port: 443, method: "GET", path: "/user" },
  livePolicy
);
// → { action: "deny", reason: "endpoint api.github.com:443 not in policy 'nvidia'; ..." }

helpers.evalSandboxFs("/etc/passwd", "write", livePolicy);
// → "deny"
```

### 6.3 실측

```bash
openshell sandbox exec -n <agent> -- curl -sS -o /dev/null -w '%{http_code}' https://api.github.com/user
```

코스 헬퍼는 `helpers.sandboxExec(command, {agent})`로 동일 명령을 실행한다.

### 6.4 결과 분류 규칙 (코스 구현 그대로)

| 관측 | 분류 |
|---|---|
| 종료 상태가 정수가 아님 | **`incomplete`** — 완료 여부 미확인 |
| 출력에 `permission denied` / `operation not permitted` / `EACCES` / `EPERM` / `CONNECT tunnel failed ... 403·407` / `HTTP code 403·407 from proxy` / `proxy ... denied·forbidden` | **`access-denial evidence`** |
| 종료 코드 0 | **`completed`** |
| 그 외 | **`command failed`** |

### 6.5 증거 테이블 양식 (제출서에 그대로 첨부)

| # | 바이너리 | 목적지 | 메서드·경로 | 정책 예측 | 매칭 블록 | 실측 종료코드 | 실측 분류 | 일치 |
|---|---|---|---|---|---|---|---|---|
| 1 | `/usr/local/bin/openclaw` | integrate.api.nvidia.com:443 | POST /v1/chat/completions | allow | `nvidia` | 0 | completed | O |
| 2 | `/usr/bin/curl` | integrate.api.nvidia.com:443 | POST /v1/chat/completions | deny (binary-miss) | - | `[[ ]]` | access-denial | `[[ ]]` |
| 3 | `/usr/local/bin/openclaw` | api.github.com:443 | GET /user | deny (endpoint-miss) | - | `[[ ]]` | access-denial | `[[ ]]` |
| 4 | `/usr/local/bin/openclaw` | integrate.api.nvidia.com:443 | DELETE /v1/models | deny (L7-miss) | `nvidia` | `[[ ]]` | access-denial | `[[ ]]` |
| 5 | (fs) | `/etc/passwd` write | - | deny | - | `[[ ]]` | access-denial | `[[ ]]` |
| 6 | (fs) | `/tmp/probe` write | - | allow | `read_write:/tmp` | 0 | completed | O |

**2번과 1번의 대비가 데모의 핵심**이다. 동일 목적지·동일 요청인데 **바이너리 신원만 다르면 결과가 갈린다.**

### 6.6 해석 규율 (문서에 반드시 병기)

- 일치는 **테스트한 그 행동에 대한** 예측 지지일 뿐이며, 모든 정책 규칙을 증명하지 않는다.
- 불일치는 요청·활성 정책·응답 출처·평가기 가정을 다시 확인할 이유다.
- HTTP 에러는 프록시에서 올 수도, 대상 애플리케이션에서 올 수도 있다. **원인을 먼저 식별**하고 나서 귀속한다.
- 명령 실패만으로는 **어느 메커니즘이 거부했는지 식별되지 않는다.** 정책 또는 감사 증거가 필요하다.
- 오퍼레이터 토큰 평면은 체크포인트 **위**에 있고, egress 규칙은 그 축을 보지 못한다. 읽기 성공이 쓰기 권한을 증명하지 않는다.

---

## 7. 자주 틀리는 부분 정리

| 오해 | 실제 |
|---|---|
| `rules`를 비워두면 안전할 것 | `rules` 없으면 **L4 매칭만으로 통과** = host:port 전체 개방 |
| `landlock.compatibility: best_effort`면 강제 집행 | **아니다.** 커널이 지원하는 범위에서만 적용 |
| `read_only`면 유출 위험 없음 | 읽을 수 있으면 출력 채널로 나갈 수 있다. 허용된 명령이 출력한 비밀은 이미 채널에 도달했다 |
| `argv[0]`을 보고 바이너리를 판별 | 위조 가능하므로 **신뢰하지 않는다.** exe 경로 + 조상 추적 + TOFU 해시 |
| 블록 이름은 라벨일 뿐 | L7 검사가 **이름 순 첫 매칭 블록**에만 적용되므로 이름이 결과를 바꿀 수 있다 |
| `/sandbox`는 정책에 없으니 못 쓴다 | `include_workdir: true`면 `/sandbox` 아래는 기본 허용 (fallback 경로) |
| `setuid` 차단이 이 YAML에 있다 | seccomp 층 소관. 이 파일에는 없다 |
| `SOUL.md`를 이 정책으로 read-only 고정 가능 | 파일 단위 read-only가 스키마에 없다. DAC + `chattr`로 보호 |
