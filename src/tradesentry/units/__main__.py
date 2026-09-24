"""python -m tradesentry.units <단위 ID> --in <입력 파일> 진입점(개발 전용). 규칙은 runner.py에 있다."""
from tradesentry.units.runner import main

if __name__ == "__main__":
    raise SystemExit(main())
