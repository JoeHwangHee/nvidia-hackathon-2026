"""python -m tradesentry.cli <명령> 진입점. 설치 명령 tradesentry와 같다(tradesentry.cli.dispatch.main)."""
from tradesentry.cli.dispatch import main

if __name__ == "__main__":
    raise SystemExit(main())
