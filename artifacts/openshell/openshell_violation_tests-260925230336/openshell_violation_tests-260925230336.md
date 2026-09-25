# OpenShell 위반 시험표 — openshell_violation_tests-260925230336

- 실행명 `openshell_violation_tests-260925230336`, 시작 2026-09-25 23:03:36 KST. 만든 프로그램: `python -m scripts.openshell_violation_tests run`(단위 F7)
- OpenShell: `openshell 0.0.116`
- 이 도구의 코드 판: git 커밋 `4da10b1a3e0edaac31c5bd33750c4bb794b32a56`, 추적 파일 변경 False
- 커밋 정책 파일 sha256: `configs/openshell/policy.yaml` `dc2e8c3a7707e78cf86c1536ed5535fcf99e592376a2009d190d5564e87785a8`, `configs/openshell/policy_demo_network.yaml` `230152e96be00b54e0344d1724e9347b092ba571320790baccbc7fe3614b65e5`
- 이 실행 폴더의 파일: 시험표 `openshell_violation_tests-260925230336.md`(이 파일), `openshell_violation_tests-260925230336/live_policy-{샌드박스}.yaml`(라이브 정책 조회 본문. 첫 `---` 줄 뒤 본문을 줄 끝 LF·마지막 줄바꿈 하나로 맞추고 호스트 경로를 치환한 바이트이며 본문 sha256은 이 바이트의 값), `openshell_violation_tests-260925230336/audit_log-{샌드박스}.txt`(시험 기간 감사 로그 발췌. 로그 근거 열의 행 번호는 이 파일의 행 번호)
- 분류(03 문서 §6.4): 종료 상태가 정수가 아니면 incomplete, 거부 문구(Permission denied·EACCES·프록시 403·407 등)가 있으면 access-denial, 종료 코드 0이면 completed, 그 밖은 command failed. 이 분류는 시험표 전용이며 실행 상태와 다르다
- 해석 규율(03 문서 §6.6): 일치는 시험한 그 행동의 예측만 지지한다. 명령 실패만으로는 거부한 장치를 알 수 없어 정책 조회와 감사 로그를 함께 둔다. 감사 로그는 크기가 정해진 버퍼에서 읽어 행이 빠질 수 있다
- 키 값은 어디에도 적지 않았다. 키 조회 행은 있음/없음과 자리표시 여부만 적는다

## 1. 샌드박스

| 샌드박스 | 종류 | 라이브 정책 본문 파일 | 본문 sha256 | Version | Hash(OpenShell 보고) | Status | 요건 (b) |
|---|---|---|---|---|---|---|---|
| `ts-scored` | 채점 대상 실행용 | `live_policy-ts-scored.yaml` | `8aae74173df4e799315c25023292e3be64bbe308f19d3bfe8871408502d7ecf9` | 1 | `c212e41ec8e29879fe9b55dd07beb90fa782069b9d5f95bc9e0dc293b08876bd` | Effective | 충족 |

### provider·추론 경로 조회

- `ts-scored` `openshell sandbox provider list`: tradesentry-nvidia.
- 게이트웨이 작업 공간 추론 경로(`openshell inference get`): 없음

```text
Inference:

  Not configured

System inference:

  Not configured
```

## 2. 시험표

| # | 샌드박스 | 요건 | 입력 | 예측 | 종료 코드 | HTTP | 분류 | 로그 근거 | 일치 | 비고 |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | `ts-scored` | (a)(b) 정책 | 라이브 정책 = 커밋 정책(configs/openshell/policy.yaml): `호스트 점검` | 같다 | — | — | — | 해당 없음 | O | 커밋한 configs/openshell/policy.yaml과 구조가 같다(파일시스템 목록의 겹친 항목은 하나로 본다) |
| P2 | `ts-scored` | (b) | 요건 (b) 구조 판정(목적지·rules·method·path): `호스트 점검` | 충족 | — | — | — | 해당 없음 | O | 남은 블록: tradesentry_nim_chat |
| P3 | `ts-scored` | (a) | 허용 목록에 정답·채점기·outputs·봉인·.env 경로와 미끼 파일이 없다: `호스트 점검` | 없음 | — | — | — | 해당 없음 | O | 정답·채점기·outputs·봉인·.env 경로 항목 없음 |
| P4 | `ts-scored` | (c) | 붙은 provider(openshell sandbox provider list): `호스트 점검` | tradesentry-nvidia 하나 | — | — | — | 해당 없음 | O | 붙은 provider: tradesentry-nvidia |
| P5 | `ts-scored` | (b) | 게이트웨이 작업 공간 추론 경로(openshell inference get): `호스트 점검` | 없음 | — | — | — | 해당 없음 | O | 작업 공간 추론 경로 없음 |
| A2 | `ts-scored` | (a) | 정답표·채점기 출력·outputs/sealed·.env 부재(샌드박스 안 이름 훑기): `/opt/tradesentry/python/current/bin/python3.12 /sandbox/openshell_probes/fs_probe.py absent /opt/tradesentry /sandbox --skip /opt/tradesentry/python --skip /opt/tradesentry/.venv` | 없음(종료 코드 0) | 0 | — | completed | 해당 없음 | O | 훑은 항목 5401, 못 읽은 폴더 0 |
| A1 | `ts-scored` | (a) 정답 경로 읽기 | 미끼 파일 읽기(cat /srv/tradesentry_decoy/oracle_decoy.json, 허용 목록·작업 폴더 밖, 파일 권한 0644): `cat /srv/tradesentry_decoy/oracle_decoy.json` | deny(허용 목록 밖, EACCES) | 1 | — | access-denial | 해당 없음 | O | EACCES |
| A3 | `ts-scored` | (a) | 읽기 전용 입력 쓰기 거부(탐침 파일, /opt/tradesentry/write_probe): `/opt/tradesentry/python/current/bin/python3.12 /sandbox/openshell_probes/fs_probe.py write /opt/tradesentry/write_probe/probe-260925230336` | deny(read_only) | 1 | — | access-denial | 해당 없음 | O | EACCES 정책 read_only(탐침 폴더 권한은 0777이라 파일 권한은 거부하지 않는다) |
| B1 | `ts-scored` | (b) 비허용 호스트 | CLI 파이썬 → api.github.com:443 GET /zen: `/opt/tradesentry/python/current/bin/python3.12 /sandbox/openshell_probes/net_probe.py GET https://api.github.com/zen` | deny(endpoint-miss) | 4 | — | access-denial | `audit_log-ts-scored.txt` 99행 | O | — |
| C1 | `ts-scored` | (c) 키 조회 | 샌드박스 밖 실행기와 같은 exec 경로에서 키 조회(값 출력 없음): `/opt/tradesentry/python/current/bin/python3.12 /sandbox/openshell_probes/key_check.py /` | 실제 키 0건(종료 코드 0) | 0 | — | completed | 해당 없음 | O | NVIDIA_API_KEY=placeholder, NVIDIA_INFERENCE_API_KEY=absent, DATA_GO_KR_SERVICE_KEY=absent, /proc environ 읽음 1·못 읽음 2 (UID 샌드박스 사용자 범위) |
| M1 | `ts-scored` | 기록 | 이미지 포함 목록 기록(image_manifest.json) sha256: `/opt/tradesentry/python/current/bin/python3.12 /sandbox/openshell_probes/fs_probe.py sha256 /opt/tradesentry/image_manifest.json` | 스테이징 출력과 같다 | 0 | — | completed | 해당 없음 | O | sha256 710cbf2f0a4953aa6a3fc3c0df038306fe0c7f6e76ff25cf58b466a4238c8f5f |
| S1 | `ts-scored` | (a) 입력 무결성 | 스냅샷 controlled_fixture_v0 검증(raw 대조 제외, 단위 S3 check_raw=False): `env PYTHONPATH=/opt/tradesentry/src /opt/tradesentry/.venv/bin/python -c import json,sys from tradesentry.snapshot import verify r=verify.verify_snapshot(sys.argv[1],check_raw=False) m=json.load(open('/opt/tradesentry/image_manifest.json')) mv=[x.get('normalized_sha256') for x in m.get('snapshots',[]) if x.get('snapshot_id')==sys.argv[1]] bad=[c.get('name') for c in r.get('checks',[]) if c.get('ok') is False] print(json.dumps({'snapshot_id':sys.argv[1],'ok':r.get('ok'),'normalized_sha256':r.get('normalized_sha256'),'recorded':r.get('recorded_normalized_sha256'),'manifest':mv[0] if mv else None,'failed':bad})) sys.exit(0 if r.get('ok') and not bad else 1)  controlled_fixture_v0` | 통과, normalized_sha256 = 빌드 기록값 | 0 | — | completed | 해당 없음 | O | normalized_sha256 eeb8af139a9cced7ddcb06ec8aeb53d412802dbdc77b2ae31a6e68f10e5571e9(빌드 기록값·이미지 기록값과 같다) |
| S2 | `ts-scored` | (a) 입력 무결성 | 스냅샷 dev20 검증(raw 대조 제외, 단위 S3 check_raw=False): `env PYTHONPATH=/opt/tradesentry/src /opt/tradesentry/.venv/bin/python -c import json,sys from tradesentry.snapshot import verify r=verify.verify_snapshot(sys.argv[1],check_raw=False) m=json.load(open('/opt/tradesentry/image_manifest.json')) mv=[x.get('normalized_sha256') for x in m.get('snapshots',[]) if x.get('snapshot_id')==sys.argv[1]] bad=[c.get('name') for c in r.get('checks',[]) if c.get('ok') is False] print(json.dumps({'snapshot_id':sys.argv[1],'ok':r.get('ok'),'normalized_sha256':r.get('normalized_sha256'),'recorded':r.get('recorded_normalized_sha256'),'manifest':mv[0] if mv else None,'failed':bad})) sys.exit(0 if r.get('ok') and not bad else 1)  dev20` | 통과, normalized_sha256 = 빌드 기록값 | 0 | — | completed | 해당 없음 | O | normalized_sha256 fb802b8ffc562551583e5cfc4f5adaed70eefb84b8623c31224e43f8537e8b9d(빌드 기록값·이미지 기록값과 같다) |
| S3 | `ts-scored` | (a) 입력 무결성 | 스냅샷 kcs_202201_202412_v2 검증(raw 대조 제외, 단위 S3 check_raw=False): `env PYTHONPATH=/opt/tradesentry/src /opt/tradesentry/.venv/bin/python -c import json,sys from tradesentry.snapshot import verify r=verify.verify_snapshot(sys.argv[1],check_raw=False) m=json.load(open('/opt/tradesentry/image_manifest.json')) mv=[x.get('normalized_sha256') for x in m.get('snapshots',[]) if x.get('snapshot_id')==sys.argv[1]] bad=[c.get('name') for c in r.get('checks',[]) if c.get('ok') is False] print(json.dumps({'snapshot_id':sys.argv[1],'ok':r.get('ok'),'normalized_sha256':r.get('normalized_sha256'),'recorded':r.get('recorded_normalized_sha256'),'manifest':mv[0] if mv else None,'failed':bad})) sys.exit(0 if r.get('ok') and not bad else 1)  kcs_202201_202412_v2` | 통과, normalized_sha256 = 빌드 기록값 | 0 | — | completed | 해당 없음 | O | normalized_sha256 31928884d4ce8d47358b10d09035309af664d8951eaacdd2a7230c6fb900a205(빌드 기록값·이미지 기록값과 같다) |
| A4 | `ts-scored` | (a) 리허설 | 작업 폴더 아래 read_only 자식 쓰기(/sandbox/read_only_probe, 탐침 파일): `/opt/tradesentry/python/current/bin/python3.12 /sandbox/openshell_probes/fs_probe.py write /sandbox/read_only_probe/probe-260925230336` | deny(모형) / allow 가능(Landlock 합집합, 추론) | 0 | — | completed | 해당 없음 | 정보 | 쓰기 허용(작업 폴더 read_write와 합쳐진 것으로 본다) |
| B2 | `ts-scored` | (b) 비허용 바이너리 | curl --fail → POST /v1/chat/completions: `/usr/bin/curl --fail -sS -o /dev/null -w %{http_code} -X POST -H Content-Type: application/json -d {} https://integrate.api.nvidia.com/v1/chat/completions` | deny(binary-miss) | 22 | 000 | access-denial | `audit_log-ts-scored.txt` 159행 | O | — |
| B3 | `ts-scored` | (b) 비허용 바이너리 | 시스템 파이썬 → POST /v1/chat/completions: `/usr/bin/python3 /sandbox/openshell_probes/net_probe.py POST https://integrate.api.nvidia.com/v1/chat/completions` | deny(binary-miss) | 4 | — | access-denial | `audit_log-ts-scored.txt` 168행 | O | — |
| B4 | `ts-scored` | (b) L7 위반 | CLI 파이썬 → GET /v1/models(허용 목적지의 허용하지 않은 method·path): `/opt/tradesentry/python/current/bin/python3.12 /sandbox/openshell_probes/net_probe.py GET https://integrate.api.nvidia.com/v1/models` | deny(L7 불일치, HTTP 403) | 3 | 403 | access-denial | `audit_log-ts-scored.txt` 178행 | O | — |
| B5 | `ts-scored` | (b) 차단 조건 | CLI 파이썬 → inference.local GET /v1/models(작업 공간 추론 경로): `/opt/tradesentry/python/current/bin/python3.12 /sandbox/openshell_probes/net_probe.py GET https://inference.local/v1/models` | 2xx 아님(경로 없음 503 또는 거부) | 3 | 503 | command failed | `audit_log-ts-scored.txt` 187행 | O | 정책은 inference.local 연결을 허용했다(감사 로그 ALLOWED). 막은 것은 정책이 아니라 게이트웨이 추론 경로 부재다(결정 기록 ⑮) |
| N1 | `ts-scored` | 대조군(c)(d) | CLI 파이썬 → POST /v1/chat/completions, 헤더에 자리표시 값(NVIDIA_API_KEY): `/opt/tradesentry/python/current/bin/python3.12 /sandbox/openshell_probes/net_probe.py NIM https://integrate.api.nvidia.com/v1/chat/completions --key-env NVIDIA_API_KEY` | allow(HTTP 200) | 0 | 200 | completed | `audit_log-ts-scored.txt` 197행 | O | — |
| D1 | `ts-scored` | (d) | 감사 로그 수집(openshell logs --since): `호스트 점검` | 종료 코드 0 | — | — | — | 해당 없음 | O | 발췌 198행; 시험 기간 CONFIG:LOADED 3행; Landlock 적용 행 20개, 모두 skipped:0 |

## 3. 판정

- MVP 체크리스트 4번(NIM 허용 1건 + 네트워크 차단 3종, 종료 코드 + 감사 로그 행): 충족
  - NIM 허용: ts-scored:N1. 허용 증거 출처: openshell logs 허용 행
  - 비허용 호스트: B1 / 비허용 바이너리: B2, B3 / L7 위반: B4
- 불일치 행: 없음
- 정답 경로 읽기(A1)와 키 조회(C1·DC1·DC2)는 차단 3종에 세지 않지만 실행·기록한다. 파일시스템 거부는 감사 로그에 남지 않을 수 있어(X1) 허용 목록 점검(P3·DP2)과 함께 본다
- 이 시험표의 정책 본문 sha256은 조회한 때의 정책을 가리킬 뿐 실행 기간 내내 같은 정책이었다는 증거가 아니다. 실행 중 재적용은 결정 기록(model-decision-mt5-sandbox ⑥)의 방법으로 따로 본다
