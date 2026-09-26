"""담당자용 화면(UI2)의 순수 논리 패키지.

소유: M. 단위 표(docs/plan/UNITS.md)의 단위가 아니라 화면 단위 `app`(A2)에 딸린 화면 보조 패키지다.
이 패키지의 모듈(i18n·alerts·plain·records)은 streamlit을 import하지 않는다(시험 대상). streamlit은 하위 패키지
`screens/`와 진입 스크립트 `ui_app.py`에서만 import한다. 채점 경로(policy·workflow·validator·tools·metrics·reports·
evaluation, eval/scorer)는 읽기만 하고 고치지 않는다.
이 파일은 아무것도 import하지 않는다.
"""
