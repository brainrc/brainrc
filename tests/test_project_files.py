"""README links the new project files, states privacy, and the files stay clean (AC9 to AC12)."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEW_FILES = ["SECURITY.md", "GOVERNANCE.md", "CODE_OF_CONDUCT.md", ".github/CODEOWNERS",
             ".github/pull_request_template.md", ".github/ISSUE_TEMPLATE/bug_report.yml",
             ".github/ISSUE_TEMPLATE/feature_request.yml", ".github/ISSUE_TEMPLATE/config.yml"]
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
HOME_PATH = re.compile(r"/Users/|/home/")
NETWORK = re.compile(r"^\s*(?:import|from)\s+(?:urllib|http|socket|requests|ssl|ftplib|smtplib)\b", re.M)


def text(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def section(body, heading):
    m = re.search(rf"(?ms)^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", body)
    assert m, heading
    return m.group(1)


class ProjectFilesTest(unittest.TestCase):
    def test_readme_links_new_files(self):
        readme = text("README.md")
        for rel in ("SECURITY.md", "GOVERNANCE.md", "CODE_OF_CONDUCT.md"):
            self.assertIn(f"]({rel})", readme)

    def test_security_section_points_to_security_md(self):
        self.assertIn("](SECURITY.md)", section(text("README.md"), "Security"))

    def test_privacy_statement(self):
        privacy = section(text("README.md"), "Privacy")
        for want in ("no usage data", "`--ccusage`", "`git`"):
            self.assertIn(want, privacy)

    def test_no_network_imports(self):
        for top in ("brainrc", "scripts", "overrides"):
            for path in (ROOT / top).rglob("*"):
                if path.is_file() and (path.suffix == ".py" or "hooks" in path.parts):
                    try:
                        body = path.read_text(encoding="utf-8")
                    except UnicodeDecodeError:
                        continue
                    self.assertIsNone(NETWORK.search(body), str(path.relative_to(ROOT)))

    def test_new_files_have_no_personal_data(self):
        for rel in NEW_FILES:
            body = text(rel)
            self.assertIsNone(EMAIL.search(body), rel)
            self.assertIsNone(HOME_PATH.search(body), rel)


if __name__ == "__main__":
    unittest.main()
