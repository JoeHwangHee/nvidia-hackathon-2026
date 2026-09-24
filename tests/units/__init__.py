"""단위 골든 시험(고정 입력과 기대 출력 한 쌍으로 단위 출력이 바뀌지 않았는지 보는 시험) 묶음.

배치: tests/units/{단위 ID}/에 test_golden.py와 골든 쌍(input.json, expected.json)을 둔다. 단위만의 시험이 더
필요하면 같은 폴더에 test_*.py로 더한다. 공통 규칙은 tests/units/golden.py다(docs/plan/UNITS.md §2).
폴더마다 __init__.py가 있어야 unittest discover가 그 폴더로 내려간다.
"""
