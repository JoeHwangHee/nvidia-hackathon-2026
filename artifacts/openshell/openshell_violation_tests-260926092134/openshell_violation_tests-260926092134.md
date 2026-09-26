# OpenShell 위반 시험표 — openshell_violation_tests-260926092134

- 실행명 `openshell_violation_tests-260926092134`, 시작 2026-09-26 09:21:34 KST. 만든 프로그램: `python -m scripts.openshell_violation_tests run`(단위 F7)
- OpenShell: `openshell 0.0.116`
- 이 도구의 코드 판: git 커밋 `c557540f743ffc77a996a2a227d68d0bbfa0f08e`, 추적 파일 변경 False
- 커밋 정책 파일 sha256: `configs/openshell/policy.yaml` `dc2e8c3a7707e78cf86c1536ed5535fcf99e592376a2009d190d5564e87785a8`, `configs/openshell/policy_demo_network.yaml` `230152e96be00b54e0344d1724e9347b092ba571320790baccbc7fe3614b65e5`
- 이 실행 폴더의 파일: 시험표 `openshell_violation_tests-260926092134.md`(이 파일), `openshell_violation_tests-260926092134/live_policy-{샌드박스}.yaml`(라이브 정책 조회 본문. 첫 `---` 줄 뒤 본문을 줄 끝 LF·마지막 줄바꿈 하나로 맞추고 호스트 경로를 치환한 바이트이며 본문 sha256은 이 바이트의 값), `openshell_violation_tests-260926092134/audit_log-{샌드박스}.txt`(시험 기간 감사 로그 발췌. 로그 근거 열의 행 번호는 이 파일의 행 번호)
- 분류(03 문서 §6.4): 종료 상태가 정수가 아니면 incomplete, 거부 문구(Permission denied·EACCES·프록시 403·407 등)가 있으면 access-denial, 종료 코드 0이면 completed, 그 밖은 command failed. 이 분류는 시험표 전용이며 실행 상태와 다르다
- 해석 규율(03 문서 §6.6): 일치는 시험한 그 행동의 예측만 지지한다. 명령 실패만으로는 거부한 장치를 알 수 없어 정책 조회와 감사 로그를 함께 둔다. 감사 로그는 크기가 정해진 버퍼에서 읽어 행이 빠질 수 있다
- 키 값은 어디에도 적지 않았다. 키 조회 행은 있음/없음과 자리표시 여부만 적는다

## 1. 샌드박스

| 샌드박스 | 종류 | 라이브 정책 본문 파일 | 본문 sha256 | Version | Hash(OpenShell 보고) | Status | 요건 (b) |
|---|---|---|---|---|---|---|---|
| `ts-official` | 공식 채점 대상 실행 전용 | `live_policy-ts-official.yaml` | `8aae74173df4e799315c25023292e3be64bbe308f19d3bfe8871408502d7ecf9` | 1 | `c212e41ec8e29879fe9b55dd07beb90fa782069b9d5f95bc9e0dc293b08876bd` | Effective | 충족 |

### provider·추론 경로 조회

- `ts-official` `openshell sandbox provider list`: tradesentry-nvidia.
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
| P1 | `ts-official` | (a)(b) 정책 | 라이브 정책 = 커밋 정책(configs/openshell/policy.yaml): `호스트 점검` | 같다 | — | — | — | 해당 없음 | O | 커밋한 configs/openshell/policy.yaml과 구조가 같다(파일시스템 목록의 겹친 항목은 하나로 본다) |
| P2 | `ts-official` | (b) | 요건 (b) 구조 판정(목적지·rules·method·path): `호스트 점검` | 충족 | — | — | — | 해당 없음 | O | 남은 블록: tradesentry_nim_chat |
| P3 | `ts-official` | (a) | 허용 목록에 정답·채점기·outputs·봉인·.env 경로와 미끼 파일이 없다: `호스트 점검` | 없음 | — | — | — | 해당 없음 | O | 정답·채점기·outputs·봉인·.env 경로 항목 없음 |
| P4 | `ts-official` | (c) | 붙은 provider(openshell sandbox provider list): `호스트 점검` | tradesentry-nvidia 하나 | — | — | — | 해당 없음 | O | 붙은 provider: tradesentry-nvidia |
| P5 | `ts-official` | (b) | 게이트웨이 작업 공간 추론 경로(openshell inference get): `호스트 점검` | 없음 | — | — | — | 해당 없음 | O | 작업 공간 추론 경로 없음 |
| A2 | `ts-official` | (a) | 정답표·채점기 출력·outputs/sealed·.env 부재(샌드박스 안 이름 훑기): `/opt/tradesentry/python/current/bin/python3.12 /sandbox/openshell_probes/fs_probe.py absent /opt/tradesentry /sandbox --skip /opt/tradesentry/python --skip /opt/tradesentry/.venv --name answers.json --name parent_series_ids.json --name generation_rules.json --name sample_seed.json` | 없음(종료 코드 0) | 0 | — | completed | 해당 없음 | O | 훑은 항목 5403, 못 읽은 폴더 0 |
| A3 | `ts-official` | (a) | 봉인 입력 쓰기 거부(탐침 파일, /opt/tradesentry/data/snapshots/holdout40): `/opt/tradesentry/python/current/bin/python3.12 /sandbox/openshell_probes/fs_probe.py write /opt/tradesentry/data/snapshots/holdout40/probe-260926092134` | deny(read_only) | 1 | — | access-denial | 해당 없음 | O | EACCES 권한 거부(정책 read_only 또는 파일 권한) |
| B1 | `ts-official` | (b) 비허용 호스트 | CLI 파이썬 → api.github.com:443 GET /zen: `/opt/tradesentry/python/current/bin/python3.12 /sandbox/openshell_probes/net_probe.py GET https://api.github.com/zen` | deny(endpoint-miss) | 4 | — | access-denial | `audit_log-ts-official.txt` 53행 | O | — |
| C1 | `ts-official` | (c) 키 조회 | 샌드박스 밖 실행기와 같은 exec 경로에서 키 조회(값 출력 없음): `/opt/tradesentry/python/current/bin/python3.12 /sandbox/openshell_probes/key_check.py /` | 실제 키 0건(종료 코드 0) | 0 | — | completed | 해당 없음 | O | NVIDIA_API_KEY=placeholder, NVIDIA_INFERENCE_API_KEY=absent, DATA_GO_KR_SERVICE_KEY=absent, /proc environ 읽음 1·못 읽음 2 (UID 샌드박스 사용자 범위) |
| M1 | `ts-official` | 기록 | 이미지 포함 목록 기록(image_manifest.json) sha256: `/opt/tradesentry/python/current/bin/python3.12 /sandbox/openshell_probes/fs_probe.py sha256 /opt/tradesentry/image_manifest.json` | 스테이징 출력과 같다 | 0 | — | completed | 해당 없음 | O | sha256 2ecddde2cd22c50b3945c9f0082cc58ce9cb14299af1f6523a3e7945769dc5c1 |
| S1 | `ts-official` | (a) 입력 무결성 | 스냅샷 holdout40 검증(raw 대조 제외, 단위 S3 check_raw=False): `env PYTHONPATH=/opt/tradesentry/src /opt/tradesentry/.venv/bin/python -c import json,sys from tradesentry.snapshot import verify r=verify.verify_snapshot(sys.argv[1],check_raw=False) m=json.load(open('/opt/tradesentry/image_manifest.json')) mv=[x.get('normalized_sha256') for x in m.get('snapshots',[]) if x.get('snapshot_id')==sys.argv[1]] bad=[c.get('name') for c in r.get('checks',[]) if c.get('ok') is False] print(json.dumps({'snapshot_id':sys.argv[1],'ok':r.get('ok'),'normalized_sha256':r.get('normalized_sha256'),'recorded':r.get('recorded_normalized_sha256'),'manifest':mv[0] if mv else None,'failed':bad})) sys.exit(0 if r.get('ok') and not bad else 1)  holdout40` | 통과, normalized_sha256 = 빌드 기록값 | 0 | — | completed | 해당 없음 | O | normalized_sha256 1df5f80112e38cef2878a990a51cea6595e7caff85ee7ab2daf2fdcaa951f93a(빌드 기록값·이미지 기록값과 같다) |
| S2 | `ts-official` | (a) 입력 무결성 | 스냅샷 kcs_202201_202412_v2 검증(raw 대조 제외, 단위 S3 check_raw=False): `env PYTHONPATH=/opt/tradesentry/src /opt/tradesentry/.venv/bin/python -c import json,sys from tradesentry.snapshot import verify r=verify.verify_snapshot(sys.argv[1],check_raw=False) m=json.load(open('/opt/tradesentry/image_manifest.json')) mv=[x.get('normalized_sha256') for x in m.get('snapshots',[]) if x.get('snapshot_id')==sys.argv[1]] bad=[c.get('name') for c in r.get('checks',[]) if c.get('ok') is False] print(json.dumps({'snapshot_id':sys.argv[1],'ok':r.get('ok'),'normalized_sha256':r.get('normalized_sha256'),'recorded':r.get('recorded_normalized_sha256'),'manifest':mv[0] if mv else None,'failed':bad})) sys.exit(0 if r.get('ok') and not bad else 1)  kcs_202201_202412_v2` | 통과, normalized_sha256 = 빌드 기록값 | 0 | — | completed | 해당 없음 | O | normalized_sha256 31928884d4ce8d47358b10d09035309af664d8951eaacdd2a7230c6fb900a205(빌드 기록값·이미지 기록값과 같다) |
| D1 | `ts-official` | (d) | 감사 로그 수집(openshell logs --since): `호스트 점검` | 종료 코드 0 | — | — | — | 해당 없음 | O | 발췌 86행; 시험 기간 CONFIG:LOADED 0행; Landlock 적용 행 11개, 모두 skipped:0 |

## 3. 판정

- MVP 체크리스트 4번(NIM 허용 1건 + 네트워크 차단 3종, 종료 코드 + 감사 로그 행): 해당 없음 (공식 채점용 샌드박스만 시험했다. 공식 최소 행에는 NIM 허용·L7 행이 없다)
  - NIM 허용: 없음. 허용 증거 출처: 없음
  - 비허용 호스트: 없음 / 비허용 바이너리: 없음 / L7 위반: 없음
- 불일치 행: 없음
- 공식 채점용 최소 행(비허용 호스트·부재 확인·키 조회·봉인 입력 쓰기 거부와 정책·기록 점검): 모두 일치
- 정답 경로 읽기(A1)와 키 조회(C1·DC1·DC2)는 차단 3종에 세지 않지만 실행·기록한다. 파일시스템 거부는 감사 로그에 남지 않을 수 있어(X1) 허용 목록 점검(P3·DP2)과 함께 본다
- 이 시험표의 정책 본문 sha256은 조회한 때의 정책을 가리킬 뿐 실행 기간 내내 같은 정책이었다는 증거가 아니다. 실행 중 재적용은 결정 기록(model-decision-mt5-sandbox ⑥)의 방법으로 따로 본다
