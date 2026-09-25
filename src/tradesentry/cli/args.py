"""단위 F1 인자 검증.

단위 ID: F1
도메인명: cli_args
소유: M
입력: 문자열 인자
출력: 검증된 요청(모드 4개·스냅샷 ID·사례·정책 버전·실행명)
허용 import: 표준 라이브러리, tradesentry.contract

정본: docs/plan/UNITS.md §3.8. 시연 경로에서는 하네스 모델이 명령을 조립하므로 이 검증이 방어선이다(자문 명세서
docs/plan/SCAFFOLD_BRIEF.md §4.7). 여기서는 값의 형식만 본다. 그 값이 가리키는 스냅샷·정책·사례가 실제로 있는지는 명령을
잇는 조립체가 본다.

- 공통 옵션 셋(--snapshot, --policy, --mode)은 자료 계약 §10 CLI 행대로 다섯 명령이 모두 받는다. 명령마다 옵션의 역할
  (꼭 있어야 함, 없어도 됨, 받지만 쓰지 않음)은 표 COMMAND_OPTIONS 하나로 정한다. 쓰지 않는 옵션도 값 형식은 검사하고, 받은
  값은 요청에 그대로 남긴다. 도움말에는 "이 명령은 이 값을 쓰지 않는다"를 적는다. --case는 공통 옵션이 아니라 run-case만
  받는다. 표에 없는 옵션은 그 명령의 파서에 없으므로 인자 오류다. 명령을 잇는 작업(AS1~AS3)은 자기 명령의 행만 고친다.
- 형식(모두 ASCII 문자만, 값 전체가 맞아야 하고, 64자 이하)
  - 스냅샷 ID(--snapshot): 영문 소문자로 시작하고 영문 소문자·숫자·밑줄만 쓴다. 예: kcs_202201_202412_v2.
  - 정책 버전 이름(--policy): 영문 소문자로 시작하고 영문 소문자·숫자·밑줄을 쓴다. 하이픈은 조각 사이에만, 점은 숫자
    사이에만 둔다. 예: policy_v1, dev-0.1. 파일 경로도 파일 이름(예: policy_v1.json)도 아니다.
  - 모드(--mode): checklist, agent, full, freeform 가운데 하나(자료 계약 docs/rules/DATA_CONTRACT_V1.md §4.1).
  - 사례 인자(--case): 영문자·숫자로 시작하고 끝나며 그 사이에는 영문자·숫자·밑줄·하이픈만 쓴다. 예: 850450-XA-202412.
    문자 집합과 길이만 본다. run-case 배선(AS2)은 사례 식별자 {hs6}-{partner}-{month}만 받는다(합성 사례도 같은 꼴, 자문 명세서
    Q18). case_id의 문자열 형식은 자료 계약이 정하지 않았으므로(§4.5) 여기서도 정하지 않는다.
  - 실행명(--run-name, 다섯 명령의 선택 옵션): 자료 계약 §10.3 N5 형식 {실행 이름}-{yymmddhhmmss}이고, 실행 이름이 그 명령의
    실행 이름(명령 이름의 하이픈을 밑줄로 바꾼 것. 예: run-case → run_case)과 같아야 하며, 시각 12자리가 실제 날짜·시각이다.
    예: run_case-260925143015.
  - 경로 구분자, '..', 절대경로, '~'로 시작하는 값은 모두 거부한다. 위 형식이 이미 막지만 오류 문장을 따로 낸다.
- --run-name(사용자 결정 10(나), 결정 기록 20260925-0847-user-decision-morning-shared-promises.md): 샌드박스 밖 실행기(평가
  하네스)가 호스트 쪽 실행 폴더를 먼저 확보하고 그 이름을 샌드박스 안 CLI에 넘기는 수단이다. 옵션이 있으면 CLI는 그 이름의
  실행 폴더를 이미 있으면 실패하는 방식으로 만들고(명령 배선 F2), 없으면 지금처럼 CLI가 실행명을 확보한다. 옵션 역할 표
  COMMAND_OPTIONS 밖에서 다섯 명령에 똑같이 두는 선택 옵션이다(값 검사가 명령마다 다르므로 명령별 검사 함수를 쓴다).
- evaluate의 --mode는 선택 옵션이다(사용자 결정 12(가)). 주지 않으면 그 묶음의 정해진 모드 전부를 한 묶음으로 돌고, 주면 그
  모드 하나만(스모크용, 점수표로 합치지 않음) 돈다(명령 배선 F2).
- --conditions-extra(evaluate만의 선택 옵션, 조립 AS3. 결정 기록 model-decision-conditions-extra): 운영자가 아는 실행
  조건(라이브 정책 조회 본문 sha256, 대조한 시험표 실행 폴더 이름, 스킬 호출 성공률, 채점기·산문 패턴 목록 커밋, 사전 점검
  결과 등)을 담은 JSON 파일의 상대 경로다. 값 검사는 여기서 모양만 본다: 비어 있지 않고, 공백·제어 문자가 없으며(재현 명령에
  한 조각으로 적힌다), 절대 경로·드라이브 문자·'~'로 시작하지 않는다(로컬 절대경로는 실행 조건 입력 파일 N13 검사가 막으므로
  상대 경로만 받는다). 파일 내용의 검사는 명령 배선 F2와 단위 E1이 한다.
- --replay(run-case만의 선택 옵션, 조립 AS3. 결정 기록 model-decision-smoke-replay): 키 없는 스모크 재현의 재생 파일
  (eval/dev/smoke/{case_id}.json) 상대 경로다. 값 검사는 --conditions-extra와 같은 모양 검사다(상대 경로 한 조각). 파일 내용의
  검사와 재생은 명령 배선 F2(load_replay)와 단위 I8이 한다.
- 같은 옵션을 두 번 적으면 값이 같아도, --옵션=값 꼴이 섞여도 인자 오류다. argparse 기본 동작(마지막 값이 이김)은 쓰지 않는다.
- 옵션 줄임(예: --snap)은 받지 않는다. '@파일' 인자 펼치기(fromfile_prefix_chars)도 켜지 않는다.
- 오류 문장은 받은 값을 되풀이하지 않는다(자료 계약 §10.3 N13, 결정 기록 20260924-2356 ⑧). CLI 자신의 문장(형식 오류,
  옵션 반복)에는 값을 넣지 않는다. argparse가 만드는 문장은 _Parser.error 한 곳에서 redact로 고친다.
  - 모르는 인자는 옵션 이름 모양 조각(ASCII `--` 뒤 영문 소문자·하이픈, 32자 이하)만 남기고 나머지는 `<값 생략>`으로 바꾼다.
    `--이름=값`은 `--이름=<값 생략>`이다.
  - 선택지 밖 값(--mode, 명령 이름)과 받지 않는 명시 값(예: --help=값)은 `<값 생략>`으로 바꾼다.
  - 그래도 남은 경로 모양 조각(경로 구분자가 든 조각)은 `<경로 생략>`으로 가린다. argparse가 적는 옵션 별칭(-h/--help)은 둔다.
  - 제어 문자(줄바꿈·ESC 같은 유니코드 Cc·Cf와 줄·문단 구분자)는 `\\x..`·`\\u....` 표기로 적는다. 로그 줄 위조와 터미널
    제어열 주입을 막는다.
- 사용법·도움말·오류 문장은 write_text로 쓴다. 표준 출력·오류의 인코딩이 한국어를 못 쓰면 ASCII 역슬래시 표기로 바꿔 쓰고
  (UnicodeEncodeError로 호출 경로 기록이 나가지 않게), 흐름이 없거나 닫혔으면 조용히 넘어간다(argparse와 같은 동작).
- 오류와 도움말은 argparse 방식 그대로다. 인자 오류는 사용법과 오류 문장을 표준 오류에 쓰고 SystemExit(2)를 낸다. 도움말은
  표준 출력에 쓰고 SystemExit(0)을 낸다. --policy는 파일 경로가 아니라 버전 이름이다.
"""
import argparse
import dataclasses
import re
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime

# 계약 상수 사본: 자료 계약 docs/rules/DATA_CONTRACT_V1.md §4.1의 모드 4개.
# 조립 때 단위 K1(tradesentry.contract.types)에서 import하게 바꾼다(docs/plan/UNITS.md §6 조립 부산물 4).
MODES = ("checklist", "agent", "full", "freeform")

# 명령과 도움말(자료 계약 §10 계획 경로·명령 표). 명령의 실행 이름은 하이픈을 밑줄로 바꾼 것이다(§10.3 N5).
COMMANDS = {
    "snapshot-build": "raw 응답·manifest에서 파생 SQLite 스냅샷을 만든다(조립체 1)",
    "snapshot-verify": "스냅샷을 검증한다(조립체 1)",
    "detect": "동결 정책으로 경보 사례 목록을 만든다(조립체 2)",
    "run-case": "사례 1건을 조사한다(조립체 3)",
    "evaluate": "자료 묶음의 사례를 모드별로 실행하고 실행 쪽 키를 기록한다(조립체 4)",
}

# 옵션의 역할. REQUIRED: 꼭 있어야 하고 명령이 쓴다. OPTIONAL: 없어도 되고, 있으면 명령이 쓴다.
# UNUSED: 받지만 이 명령은 쓰지 않는다(값 형식은 검사하고 요청에 그대로 남긴다).
REQUIRED, OPTIONAL, UNUSED = "required", "optional", "unused"
UNUSED_NOTE = "이 명령은 이 값을 쓰지 않는다(값 형식만 검사한다)"

# 공통 옵션 셋. 계획 경로·명령 표(자료 계약 §10 CLI 행)의 "공통 옵션"이라 다섯 명령이 모두 받는다. 명령마다 쓰지 않는
# 공통 옵션을 받지 않게 좁히는 일은 그 표의 읽기를 바꾸는 일이라 사용자 확인 전에는 하지 않는다(오케스트레이터 결정,
# 병렬 개발 규칙 §4.3·§4.5).
COMMON_OPTIONS = ("snapshot", "policy", "mode")

# 명령 → {옵션: 역할}. 표에 없는 옵션(run-case 밖의 --case)은 그 명령이 받지 않는다.
# snapshot-verify는 평가 스킬 ② 사전 점검과 룰북 B3·B7이 --snapshot 하나로 부른다. evaluate는 룰북 B7의 재현 명령 형식
# (--snapshot, --policy, --mode와 나머지 인자)을 따른다. snapshot-build의 --policy는 승격 규칙에 쓸 정책이며, 없을 때의
# 뜻은 단위 S2(로드맵 DT1)가 정한다.
COMMAND_OPTIONS = {
    "snapshot-build": {"snapshot": REQUIRED, "policy": OPTIONAL, "mode": UNUSED},
    "snapshot-verify": {"snapshot": REQUIRED, "policy": UNUSED, "mode": UNUSED},
    "detect": {"snapshot": REQUIRED, "policy": REQUIRED, "mode": UNUSED},
    "run-case": {"snapshot": REQUIRED, "policy": REQUIRED, "mode": REQUIRED, "case": REQUIRED},
    "evaluate": {"snapshot": REQUIRED, "policy": REQUIRED, "mode": OPTIONAL},
}
# evaluate --mode OPTIONAL: 사용자 결정 12(가)(2026-09-25 08:47). 모드를 주지 않으면 묶음의 정해진 모드 전부를 돈다.

MAX_LENGTH = 64
SNAPSHOT_ID_RE = re.compile(r"[a-z][a-z0-9_]*")
POLICY_VERSION_RE = re.compile(r"[a-z][a-z0-9_]*(?:-[a-z0-9_]+|(?<=[0-9])\.[0-9]+)*")
CASE_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9_-]*[A-Za-z0-9])?")
RUN_NAME_RE = re.compile(r"[a-z][a-z0-9_]*-[0-9]{12}")  # 자료 계약 §10.3 N5 실행명(값 전체가 맞아야 한다)
STAMP_FORMAT = "%y%m%d%H%M%S"
PATH_HINT_RE = re.compile(r"[\\/]|\.\.|^~")  # 경로 구분자, '..', '~'로 시작
PATHISH_TOKEN_RE = re.compile(r"[^\s'\"(),\[\]]*[\\/][^\s'\"(),\[\]]*")  # 경로 구분자가 든 조각

# argparse 오류 문장 고치기(redact)
VALUE_OMITTED = "<값 생략>"
PATH_OMITTED = "<경로 생략>"
UNRECOGNIZED = "unrecognized arguments: "  # argparse(파이썬 3.12)가 모르는 인자를 알리는 문장의 앞부분
OPTION_NAME_RE = re.compile(r"--[a-z][a-z-]{0,29}")  # 모르는 인자 가운데 남길 옵션 이름 모양(전체 일치, 32자 이하)
ECHOED_VALUE_RE = re.compile(  # 받은 값을 파이썬 표현 문자열로 되풀이하는 argparse 문장 두 가지
    r"(invalid choice: |ignored explicit argument )('(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\")")
OPTION_ALIASES_RE = re.compile(r"-{1,2}[a-z][a-z-]*(?:/-{1,2}[a-z][a-z-]*)+:?")  # argparse가 적는 "-h/--help:" 꼴

SNAPSHOT_RULE = "스냅샷 ID는 영문 소문자로 시작하고 영문 소문자·숫자·밑줄만 쓰며 64자 이하다(예: kcs_202201_202412_v2)"
POLICY_RULE = ("정책 버전 이름은 영문 소문자로 시작하고 영문 소문자·숫자·밑줄을 쓰며, 하이픈은 조각 사이에만, 점은 숫자 "
               "사이에만 두고 64자 이하다(예: policy_v1, dev-0.1). 파일 경로나 파일 이름이 아니다")
RUN_NAME_RULE = ("실행명은 {실행 이름}-{yymmddhhmmss}이고(자료 계약 §10.3 N5), 실행 이름은 이 명령의 실행 이름(명령 이름의 "
                 "하이픈을 밑줄로 바꾼 것)이며, 시각 12자리는 실제 날짜·시각이다(예: run_case-260925143015)")
CASE_RULE = ("사례 인자는 영문자·숫자로 시작하고 끝나며 그 사이에는 영문자·숫자·밑줄·하이픈만 쓰고 64자 이하다"
             "(예: 850450-XA-202412. run-case는 사례 식별자 {hs6}-{partner}-{month}를 받는다)")


def _omit_unrecognized(token: str) -> str:
    name, equals, _ = token.partition("=")
    if OPTION_NAME_RE.fullmatch(name):
        return name + (f"={VALUE_OMITTED}" if equals else "")
    return VALUE_OMITTED


def _hide_path(match: re.Match[str]) -> str:
    token = match.group(0)
    return token if OPTION_ALIASES_RE.fullmatch(token) else PATH_OMITTED


def _escape_control(ch: str) -> str:
    if unicodedata.category(ch) in ("Cc", "Cf") or ch in "  ":
        code = ord(ch)
        return f"\\x{code:02x}" if code < 0x100 else f"\\u{code:04x}" if code < 0x10000 else f"\\U{code:08x}"
    return ch


def redact(message: str) -> str:
    """argparse 오류 문장이 받은 값을 되풀이하지 않게 고친다(자료 계약 §10.3 N13, 결정 기록 20260924-2356 ⑧).

    1) 선택지 밖 값·받지 않는 명시 값: 따옴표 안 값을 <값 생략>. 값을 먼저 지우므로 값 안의 글자가 아래 판정을 속이지 못한다
    2) 모르는 인자(문장이 그 문구로 시작할 때만): 옵션 이름 모양 조각만 남기고 나머지는 <값 생략>(--이름=값은
       --이름=<값 생략>)
    3) 그래도 남은 경로 구분자 든 조각: <경로 생략>(argparse가 적는 옵션 별칭 -h/--help는 둔다)
    4) 제어 문자: \\x..·\\u.... 표기
    """
    message = ECHOED_VALUE_RE.sub(lambda match: match.group(1) + VALUE_OMITTED, message)
    if message.startswith(UNRECOGNIZED):  # argparse는 이 문장을 늘 이 문구로 시작한다
        rest = message[len(UNRECOGNIZED):]
        message = UNRECOGNIZED + " ".join(_omit_unrecognized(token) for token in rest.split(" "))
    message = PATHISH_TOKEN_RE.sub(_hide_path, message)
    return "".join(_escape_control(ch) for ch in message)


def write_text(stream: object, text: str) -> None:
    """글을 흐름(표준 출력·오류)에 쓴다.

    흐름의 인코딩이 글자를 못 쓰면(UnicodeEncodeError) ASCII 역슬래시 표기로 바꿔 쓴다. 흐름이 없거나(AttributeError),
    파이프가 끊겼거나(OSError), 닫혔으면(ValueError) 조용히 넘어간다. argparse의 _print_message는 앞의 둘만 넘기지만,
    오류를 알리는 출력이 새 예외와 호출 경로 기록을 내지 않게 셋을 모두 넘긴다.
    """
    try:
        try:
            stream.write(text)
        except UnicodeEncodeError:
            stream.write(text.encode("ascii", "backslashreplace").decode("ascii"))
    except (AttributeError, OSError, ValueError):
        pass


def _checker(what: str, pattern: re.Pattern[str], rule: str):
    """argparse type 함수를 만든다. 오류는 값을 되풀이하지 않는 ArgumentTypeError로만 낸다."""

    def check(value: str) -> str:
        if PATH_HINT_RE.search(value):
            raise argparse.ArgumentTypeError(
                f"{what}에는 경로를 쓰지 않는다(경로 구분자, '..', 절대경로, '~'로 시작하는 값). {rule}")
        if len(value) > MAX_LENGTH or pattern.fullmatch(value) is None:
            raise argparse.ArgumentTypeError(f"{what} 형식이 아니다. {rule}")
        return value

    return check


check_snapshot_id = _checker("스냅샷 ID", SNAPSHOT_ID_RE, SNAPSHOT_RULE)
check_policy_version = _checker("정책 버전 이름", POLICY_VERSION_RE, POLICY_RULE)
check_case = _checker("사례 인자", CASE_RE, CASE_RULE)

def run_name_of(command: str) -> str:
    """명령의 실행 이름(자료 계약 §10.3 N5: 명령 이름의 하이픈을 밑줄로 바꾼 것)."""
    return command.replace("-", "_")


def check_run_name_for(command: str):
    """--run-name 검사 함수(argparse type)를 명령마다 만든다. 오류는 값을 되풀이하지 않는 ArgumentTypeError로만 낸다."""

    def check(value: str) -> str:
        if PATH_HINT_RE.search(value):
            raise argparse.ArgumentTypeError(
                f"실행명에는 경로를 쓰지 않는다(경로 구분자, '..', 절대경로, '~'로 시작하는 값). {RUN_NAME_RULE}")
        if len(value) > MAX_LENGTH or RUN_NAME_RE.fullmatch(value) is None:
            raise argparse.ArgumentTypeError(f"실행명 형식이 아니다. {RUN_NAME_RULE}")
        name, stamp = value.rsplit("-", 1)
        if name != run_name_of(command):
            raise argparse.ArgumentTypeError(f"실행명의 실행 이름이 이 명령의 실행 이름과 다르다. {RUN_NAME_RULE}")
        try:
            datetime.strptime(stamp, STAMP_FORMAT)
        except ValueError:
            raise argparse.ArgumentTypeError(f"실행명의 시각이 실제 날짜·시각이 아니다. {RUN_NAME_RULE}") from None
        return value

    return check


CONDITIONS_EXTRA_OPTION = "conditions-extra"  # evaluate만 받는 선택 옵션(COMMAND_OPTIONS 밖, --run-name과 같은 자리)
CONDITIONS_EXTRA_HELP = ("운영자가 아는 실행 조건(라이브 정책 조회 본문 sha256, 대조한 시험표 실행 폴더 이름, 스킬 호출 성공률, "
                         "채점기·산문 패턴 목록 커밋, 사전 점검 결과 등)을 담은 JSON 파일의 상대 경로. 실행 조건 입력 파일에 "
                         "합친다. 로컬 절대 경로는 받지 않는다(재현 명령에 그대로 적힌다)")
CONDITIONS_EXTRA_RULE = ("운영자 실행 조건 파일 경로는 비어 있지 않은 상대 경로이고, 공백·제어 문자가 없으며, 절대 경로·드라이브 "
                         "문자·'~'로 시작하지 않는다(로컬 절대 경로는 실행 조건 입력 파일 검사(N13)가 막는다)")
CONDITIONS_EXTRA_BAD_START_RE = re.compile(r"^(?:[\\/]|~|[A-Za-z]:[\\/])")


def _is_relative_path_piece(value: str) -> bool:
    """비어 있지 않고, 공백·제어 문자(유니코드 Cc·Cf·Zl·Zp)가 없고, `/`·`\\`·`~`·드라이브 문자로 시작하지 않는 상대 경로 한 조각."""
    return bool(value) and not any(ch.isspace() or unicodedata.category(ch) in ("Cc", "Cf", "Zl", "Zp") for ch in value) \
        and CONDITIONS_EXTRA_BAD_START_RE.match(value) is None


def check_conditions_extra(value: str) -> str:
    """--conditions-extra 값의 모양 검사(상대 경로 한 조각). 값은 오류 문장에 되풀이하지 않는다(N13)."""
    if not _is_relative_path_piece(value):
        raise argparse.ArgumentTypeError(CONDITIONS_EXTRA_RULE)
    return value


REPLAY_OPTION = "replay"  # run-case만 받는 선택 옵션(COMMAND_OPTIONS 밖, --run-name과 같은 자리). 키 없는 스모크 재현
REPLAY_HELP = ("기록된 모델 응답을 재생하는 재생 파일의 상대 경로(예: eval/dev/smoke/850450-XA-202412.json). 주면 NIM을 "
               "부르지 않고 기록된 응답을 차례로 내주며 요청 해시를 대조한다(키 없이 돈다). 재생 실행은 점수표 근거가 아니다. "
               "로컬 절대 경로·'~'는 받지 않는다")
REPLAY_RULE = ("재생 파일 경로는 비어 있지 않은 상대 경로이고, 공백·제어 문자가 없으며, 절대 경로·드라이브 문자·'~'로 "
               "시작하지 않는다(로컬 절대 경로는 출력에 남기지 않는다, N13)")


def check_replay(value: str) -> str:
    """--replay 값의 모양 검사(상대 경로 한 조각). 값은 오류 문장에 되풀이하지 않는다(N13)."""
    if not _is_relative_path_piece(value):
        raise argparse.ArgumentTypeError(REPLAY_RULE)
    return value


RUN_NAME_OPTION = "run-name"
RUN_NAME_HELP = ("호스트가 먼저 확보한 실행명(예: run_case-260925143015). 주면 그 이름의 실행 폴더 outputs/{실행명}/을 이미 "
                 "있으면 실패하는 방식으로 만들고, 주지 않으면 CLI가 실행명을 확보한다(사용자 결정 10)")

# 옵션 → argparse 인자 정의. dest는 옵션 이름 그대로다(요청의 필드 이름은 Request).
OPTIONS = {
    "snapshot": {"metavar": "SNAPSHOT_ID", "type": check_snapshot_id,
                 "help": "스냅샷 ID(예: kcs_202201_202412_v2, controlled_fixture_v0)"},
    "policy": {"metavar": "POLICY_VERSION", "type": check_policy_version,
               "help": "정책 버전 이름(예: policy_v1, dev-0.1). 파일 경로가 아니다"},
    "mode": {"choices": MODES, "help": "실행 모드. " + ", ".join(MODES) + " 가운데 하나"},
    "case": {"metavar": "CASE", "type": check_case,
             "help": "조사할 사례의 식별자 {hs6}-{partner}-{month}(예: 850450-XA-202412). 합성 사례도 같은 꼴이다"},
}


class _Parser(argparse.ArgumentParser):
    """오류 문장을 redact로 고치고, 사용법·도움말·오류 문장을 write_text로 쓰는 argparse.

    오류 처리(사용법 출력, SystemExit(2))와 도움말(SystemExit(0))은 argparse 그대로다. _print_message는 argparse가 모든
    출력에 쓰는 내부 메서드다(파이썬 판은 lock으로 3.12.13에 고정돼 있다).
    """

    def error(self, message: str):
        super().error(redact(message))

    def _print_message(self, message: str, file=None) -> None:
        if message:
            write_text(sys.stderr if file is None else file, message)


class _Once(argparse.Action):
    """같은 옵션을 두 번 적으면 값이 같아도 인자 오류로 끝낸다."""

    def __call__(self, parser, namespace, values, option_string=None):
        if getattr(namespace, self.dest, None) is not None:
            parser.error(f"{option_string} 옵션을 두 번 적었다. 옵션은 한 번만 적는다")
        setattr(namespace, self.dest, values)


@dataclass(frozen=True)
class Request:
    """단위 F1 검증을 거친 요청. 처리 함수(tradesentry.cli.dispatch.HANDLERS)는 이것만 받는다.

    필드 이름은 자료 계약의 키 이름(snapshot_id, policy_version, mode)을 따른다. 적지 않은 옵션은 None이다. 명령이 쓰지
    않는 공통 옵션(예: detect의 --mode)도 받은 값을 그대로 둔다. 쓸지 말지는 처리 함수가 COMMAND_OPTIONS대로 정한다.
    case는 --case 값 그대로이고 run-case만 받는다(뜻은 run-case 배선이 정한다). run_name은 --run-name 값 그대로다(없으면
    None. 다섯 명령이 받는다). conditions_extra는 --conditions-extra 값 그대로다(없으면 None. evaluate만 받는다). replay는
    --replay 값 그대로다(없으면 None. run-case만 받는다. 키 없는 스모크 재현).
    """

    command: str
    snapshot_id: str
    policy_version: str | None = None
    mode: str | None = None
    case: str | None = None
    run_name: str | None = None
    conditions_extra: str | None = None
    replay: str | None = None


def option_help(command: str, option: str) -> str:
    """명령의 옵션 도움말. 그 명령이 쓰지 않는 옵션이면 UNUSED_NOTE를 덧붙인다."""
    text = OPTIONS[option]["help"]
    return f"{text}. {UNUSED_NOTE}" if COMMAND_OPTIONS[command][option] == UNUSED else text


def build_parser() -> argparse.ArgumentParser:
    """tradesentry 명령의 인자 틀. 명령마다 COMMAND_OPTIONS의 옵션을 둔다. 도움말(-h, --help)은 종료 코드 0이다.

    옵션 줄임(예: --snap)은 받지 않는다(allow_abbrev=False). 시연 경로에서는 하네스 모델이 명령을 조립하므로 적힌 그대로의
    옵션 이름만 받는다.
    """
    parser = _Parser(
        prog="tradesentry",
        description="TradeSentry CLI(명령줄 실행 도구). 관세청 수입통계 경보를 조사해 담당자의 다음 업무를 제안한다. "
                    "부정·위법·원산지 판정이나 통관 조치가 아니다.",
        allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", metavar="<명령>", required=True)
    for name, help_text in COMMANDS.items():
        command = commands.add_parser(name, help=help_text, description=help_text, allow_abbrev=False)
        for option, role in COMMAND_OPTIONS[name].items():
            spec = dict(OPTIONS[option], help=option_help(name, option))
            command.add_argument(f"--{option}", dest=option, action=_Once, required=role == REQUIRED, **spec)
        command.add_argument(f"--{RUN_NAME_OPTION}", dest="run_name", action=_Once, metavar="RUN_NAME",
                             type=check_run_name_for(name), help=RUN_NAME_HELP)
        if name == "evaluate":
            command.add_argument(f"--{CONDITIONS_EXTRA_OPTION}", dest="conditions_extra", action=_Once,
                                 metavar="JSON_PATH", type=check_conditions_extra, help=CONDITIONS_EXTRA_HELP)
        if name == "run-case":
            command.add_argument(f"--{REPLAY_OPTION}", dest="replay", action=_Once, metavar="REPLAY_PATH",
                                 type=check_replay, help=REPLAY_HELP)
    return parser


def parse(argv: list[str] | None = None) -> Request:
    """인자를 검증해 요청을 돌려준다. argv가 None이면 sys.argv[1:]를 쓴다.

    인자 오류면 사용법과 오류 문장을 표준 오류에 쓰고 SystemExit(2), 도움말이면 SystemExit(0)을 낸다(argparse 방식).
    """
    namespace = build_parser().parse_args(argv)
    return Request(command=namespace.command, snapshot_id=namespace.snapshot,
                   policy_version=getattr(namespace, "policy", None), mode=getattr(namespace, "mode", None),
                   case=getattr(namespace, "case", None), run_name=getattr(namespace, "run_name", None),
                   conditions_extra=getattr(namespace, "conditions_extra", None),
                   replay=getattr(namespace, "replay", None))


def run(inp: object) -> object:
    """진입 함수. 입력은 문자열 인자 목록(명령 이름부터), 출력은 검증된 요청의 필드 사전이다."""
    if not isinstance(inp, list) or not all(isinstance(item, str) for item in inp):
        raise TypeError("단위 F1의 입력은 문자열 인자 목록이다")
    return dataclasses.asdict(parse(inp))
