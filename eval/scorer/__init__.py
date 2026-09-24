"""독립 채점기(샌드박스 밖에서 정답표와 대조해 채점하는 프로그램). tradesentry 패키지 전부(등록부·커널 포함)와 eval.datagen을 직접이든 간접이든 import하지 않는다. 계약 상수가 필요하면 이 안에 따로 적는다.
소유: D. 단위: C1~C4(docs/plan/UNITS.md).
이 파일은 아무것도 import하지 않는다. 하위 모듈을 import하면 그 패키지의 모든 import에 끼어드는 간접 import가 생긴다.
"""
