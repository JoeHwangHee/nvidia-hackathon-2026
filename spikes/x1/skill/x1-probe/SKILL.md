---
name: x1-probe
description: X1 통합 시험용 임시 스킬. 운영자가 "X1 probe"를 요청하면 이 샌드박스 안의 X1 최소 CLI를 한 번 실행해 NVIDIA NIM을 1회 호출하고 NAT 실행 추적 1건을 남긴 뒤, CLI가 출력한 JSON 한 줄을 고치지 않고 그대로 전한다. Use only when the operator explicitly asks to run the X1 probe; it runs one fixed CLI command and relays its JSON output verbatim.
---

# x1-probe

TradeSentry X1(세로형 최소 통합 시험)의 임시 스킬이다. 런타임 스킬 `tradesentry`가 아니며, 앱 코드에 섞지 않는다. NIM은 NVIDIA 클라우드 추론 API, NAT는 NVIDIA NeMo Agent Toolkit(실행 추적·평가 도구 모음)이다.

## 언제 쓰나

운영자가 "X1 probe를 돌려라", "run the X1 probe"처럼 이 시험을 명시적으로 요청할 때만 쓴다.

## 할 일

1. 운영자 요청에서 CLI에 넘길 한 줄 문장을 정한다. 운영자가 문장을 주지 않았으면 `Reply with exactly: X1 OK`를 쓴다.
2. 셸 도구로 아래 명령 하나만 실행한다. `<한 줄 문장>` 자리에만 값을 넣는다.

   ```bash
   /sandbox/x1opt/run_probe.sh "<한 줄 문장>"
   ```

   이 명령은 키 조회 → NIM 1회 호출과 NAT 추적 → 허용 목록 밖으로 보내는 의도적 요청 1건(차단 시험)을 차례로 한다.
3. 명령이 표준 출력에 낸 JSON 한 줄과 종료 코드를 그대로 전한다. `run_id`, `exit_code`, `http_status`, `content`, `run_dir`, `key_check`, `violation_probe` 값을 고치거나 다시 계산하지 않는다.

## 하지 않는 것

- 다른 옵션·파일 경로·URL·셸 조각을 명령에 붙이지 않는다.
- `curl`·`wget`·다른 프로그램으로 외부에 요청하지 않는다.
- `.env` 파일, 환경변수 목록, 자격 증명 파일을 읽거나 출력하지 않는다.
- CLI 결과를 요약하면서 숫자를 바꾸지 않는다.
