"""TradeSentry 앱 패키지.

관세청 수입통계 경보를 조사해 담당자의 다음 업무(MAINTAIN·MONITOR·HOLD)를 제안하는 에이전트의 런타임 코드다.
패키지 목록과 단위(혼자 실행하고 시험할 수 있게 파일 하나로 만든 가장 작은 구현 조각) 목록의 정본은
docs/rules/DATA_CONTRACT_V1.md §10·§10.3과 docs/plan/UNITS.md다.

이 파일은 아무것도 import하지 않는다. 어떤 단위를 import해도 이 파일이 먼저 실행되므로, 여기서 다른 모듈을
부르면 경계 시험(허용 import와 채점기 독립성을 import 문만 읽어 확인하는 시험)이 보는 간접 import가 생긴다.
"""
