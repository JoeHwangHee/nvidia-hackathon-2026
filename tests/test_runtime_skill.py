"""단위 F3(런타임 스킬) 시험. skills/tradesentry/SKILL.md가 인터페이스 계약(docs/plan/DEV_PLAN.md §5.2)의 형식을 지키는지 본다.

- frontmatter의 name이 폴더 이름과 같고(소문자·숫자·하이픈, 64자 이하), description이 1024자 이하이며 영어 한 문장을 담는다.
- 셸 코드 블록은 `tradesentry detect`와 `tradesentry run-case`만 부르고, 옵션은 CLI(단위 F1)의 그 명령 옵션만 쓴다.
- 부르지 않는 명령(snapshot-build, snapshot-verify, evaluate)을 셸 코드 블록에 쓰지 않는다.
"""
import re
import unittest
from pathlib import Path

from tradesentry.cli import args

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "tradesentry" / "SKILL.md"


class RuntimeSkillTest(unittest.TestCase):
    def setUp(self):
        self.text = SKILL.read_text(encoding="utf-8")

    def frontmatter(self) -> dict[str, str]:
        match = re.match(r"---\n(.*?)\n---\n", self.text, re.S)
        self.assertIsNotNone(match)
        return dict(line.split(": ", 1) for line in match.group(1).splitlines())

    def test_frontmatter(self):
        meta = self.frontmatter()
        self.assertEqual(meta["name"], SKILL.parent.name)
        self.assertRegex(meta["name"], r"^[a-z0-9-]{1,64}$")
        self.assertLessEqual(len(meta["description"]), 1024)
        self.assertRegex(meta["description"], r"Use this skill [A-Za-z ,`\-.;]+\.$")

    def test_shell_blocks_call_only_detect_and_run_case(self):
        blocks = [block.strip() for block in re.findall(r"```bash\n(.*?)```", self.text, re.S)]
        self.assertEqual(len(blocks), 2)
        seen = set()
        for block in blocks:
            match = re.fullmatch(r"cd /sandbox && /sandbox/tradesentry/bin/tradesentry ([a-z-]+)((?: --[a-z]+ <[^>]+>)*)",
                                 block)
            self.assertIsNotNone(match, block)
            command = match.group(1)
            seen.add(command)
            options = re.findall(r"--([a-z]+)", match.group(2))
            required = [name for name, role in args.COMMAND_OPTIONS[command].items() if role == args.REQUIRED]
            self.assertEqual(sorted(options), sorted(required), command)
        self.assertEqual(seen, {"detect", "run-case"})
        for command in ("snapshot-build", "snapshot-verify", "evaluate"):
            self.assertNotIn(command, "".join(blocks))

    def test_modes_match_cli(self):
        for mode in args.MODES:
            self.assertIn(f"`{mode}`", self.text)


if __name__ == "__main__":
    unittest.main()
