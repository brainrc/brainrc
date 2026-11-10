"""The install docs and spec-agent use the brainrc plugin names (AC4 to AC6)."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ["README.md", "docs/install.md", "docs/troubleshooting.md", "docs/spec-agent.md",
        "docs/harness-packages.md", "skills/spec-agent/SKILL.md"]
OLD = re.compile(r"ai-config@ai-config|ai-config:<|/ai-config:work|plugins/local/ai-config|\"name\": \"ai-config\"")


def text(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def without_move_note(rel):
    """install.md minus its 'Moving from ai-config' section."""
    return re.sub(r"(?ms)^### Moving from ai-config\n.*?(?=^#{1,3} |\Z)", "", text(rel))


class PluginDocsTest(unittest.TestCase):
    def test_install_commands_use_new_names(self):
        install = text("docs/install.md")
        for want in ("/plugin install brainrc@brainrc", "codex plugin add brainrc@brainrc",
                     "~/.cursor/plugins/local/brainrc", "/brainrc:work", "brainrc:<name>"):
            self.assertIn(want, install)
        self.assertIn("/plugin install brainrc@brainrc", text("README.md"))

    def test_old_names_only_in_move_note_and_troubleshooting(self):
        for rel in DOCS:
            if rel == "docs/troubleshooting.md":
                continue
            body = without_move_note(rel) if rel == "docs/install.md" else text(rel)
            if rel == "skills/spec-agent/SKILL.md":
                body = body.replace("`ai-config:<role>`", "")
            self.assertIsNone(OLD.search(body), rel)

    def test_move_note(self):
        note = re.search(r"(?ms)^### Moving from ai-config\n(.*?)(?=^#{1,3} |\Z)", text("docs/install.md"))
        self.assertIsNotNone(note)
        for want in ("/plugin uninstall ai-config@ai-config", "/plugin marketplace remove ai-config",
                     "brainrc@brainrc", "brainrc:<name>", "doctor"):
            self.assertIn(want, note.group(1))

    def test_troubleshooting_points_at_doctor_warn(self):
        t = text("docs/troubleshooting.md")
        self.assertIn("brainrc@brainrc", t)
        self.assertIn("doctor", t)
        self.assertIn("Moving from ai-config", t)

    def test_spec_agent_role_lookup_order(self):
        s = text("skills/spec-agent/SKILL.md")
        self.assertLess(s.index("brainrc:<role>"), s.index("ai-config:<role>"))
