"""Docs that tell people which release to install pin the current major.minor, or a placeholder (#105)."""
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INSTALL_DOCS = ("README.md", "CONTRIBUTING.md", "docs/install.md", "docs/tutorial.md", "docs/troubleshooting.md")
# A concrete release someone would install or check out: `git checkout v0.3.29`, `...@v0.5.1`,
# `brainrc==0.5.1`, `--branch v0.5.1`. Placeholders such as `v<X.Y.Z>` don't match.
PIN = re.compile(r"(?:git checkout v|@v|brainrc==|--branch v)(\d+)\.(\d+)\.\d+")


def stale_pins(text: str, version: str) -> list[str]:
    """Each pin in text whose major.minor differs from version's, as `line N: <pin>`."""
    current = tuple(version.strip().split(".")[:2])
    return [f"line {n}: {m.group(0)}"
            for n, line in enumerate(text.splitlines(), 1)
            for m in PIN.finditer(line) if m.groups() != current]


class DocVersionTest(unittest.TestCase):
    def test_install_docs_pin_the_current_minor_or_a_placeholder(self):
        version = (REPO / "VERSION").read_text()
        for name in INSTALL_DOCS:
            path = REPO / name
            if path.is_file():
                with self.subTest(doc=name):
                    self.assertEqual(stale_pins(path.read_text(), version), [],
                                     f"{name} pins a release other than {version.strip()}; use v<X.Y.Z>")

    def test_a_stale_pin_is_found(self):
        text = "Stay on a release: `git checkout v0.3.29`.\npip install 'brainrc @ git+https://x@v0.5.1'\n"
        self.assertEqual(stale_pins(text, "0.5.8\n"), ["line 1: git checkout v0.3.29"])
        self.assertEqual(stale_pins("pip install brainrc==1.0.0", "0.5.8"), ["line 1: brainrc==1.0.0"])

    def test_placeholders_and_history_are_not_pins(self):
        text = "check out `git checkout v<X.Y.Z>`; `@v<X.Y.Z>`; removed in 0.5.0; shipped in 0.3.19\n"
        self.assertEqual(stale_pins(text, "0.5.8"), [])


if __name__ == "__main__":
    unittest.main()
