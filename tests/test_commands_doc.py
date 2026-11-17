"""docs/commands.md lists every visible command and each of its options, as the parser defines them."""
import argparse
import re
import unittest
from pathlib import Path

from brainrc import cli

REPO = Path(__file__).resolve().parent.parent
PAGE = REPO / "docs/commands.md"


def visible_commands() -> dict[str, argparse.ArgumentParser]:
    parser = cli._parser()
    sub = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    shown = {a.dest for a in sub._choices_actions if a.help != argparse.SUPPRESS}
    return {name: p for name, p in sub.choices.items() if name in shown}


def section(text: str, name: str) -> str | None:
    m = re.search(rf"(?ms)^## brainrc {re.escape(name)}\n(.*?)(?=^## |\Z)", text)
    return m.group(1) if m else None


class CommandsDocTest(unittest.TestCase):
    text = PAGE.read_text(encoding="utf-8")

    def test_every_command_has_a_section_with_its_options(self):
        for name, parser in visible_commands().items():
            with self.subTest(command=name):
                body = section(self.text, name)
                self.assertIsNotNone(body, f"docs/commands.md has no `## brainrc {name}` section")
                for action in parser._actions:
                    if isinstance(action, argparse._HelpAction):
                        continue
                    if action.option_strings:
                        for opt in action.option_strings:
                            self.assertIn(f"`{opt}", body, f"{name}: {opt} is not documented")
                    else:
                        self.assertIn(f"`{action.metavar or action.dest}", body,
                                      f"{name}: argument {action.metavar or action.dest} is not documented")

    def test_no_section_for_a_command_that_does_not_exist(self):
        documented = set(re.findall(r"(?m)^## brainrc ([a-z-]+)$", self.text))
        self.assertEqual(documented - set(visible_commands()), set())

    def test_hidden_commands_stay_out(self):
        for name in ("plugin", "capabilities", "release"):
            self.assertIsNone(section(self.text, name), name)


if __name__ == "__main__":
    unittest.main()
