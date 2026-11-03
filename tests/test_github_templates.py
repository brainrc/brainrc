"""CODEOWNERS, PR template, and issue forms exist with the expected content (AC1, AC5 to AC7, AC11)."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADVISORIES = "https://github.com/brainrc/brainrc/security/advisories/new"
FORMS = ["bug_report.yml", "feature_request.yml"]


def text(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


class GithubTemplatesTest(unittest.TestCase):
    def test_files_exist(self):
        for rel in (".github/CODEOWNERS", ".github/pull_request_template.md",
                    ".github/ISSUE_TEMPLATE/config.yml",
                    *(f".github/ISSUE_TEMPLATE/{f}" for f in FORMS)):
            self.assertTrue((ROOT / rel).is_file(), rel)

    def test_codeowners_owns_everything(self):
        lines = [ln.strip() for ln in text(".github/CODEOWNERS").splitlines()]
        rules = [ln for ln in lines if ln and not ln.startswith("#")]
        self.assertEqual(rules, ["* @bxker"])

    def test_config_disables_blank_issues_and_links_private_channel(self):
        config = text(".github/ISSUE_TEMPLATE/config.yml")
        self.assertRegex(config, r"(?m)^blank_issues_enabled: false$")
        self.assertIn("contact_links:", config)
        self.assertIn(f"url: {ADVISORIES}", config)

    def test_issue_forms_are_forms(self):
        for f in FORMS:
            body = text(f".github/ISSUE_TEMPLATE/{f}")
            self.assertRegex(body, r"(?m)^name: \S")
            self.assertRegex(body, r"(?m)^description: \S")
            self.assertRegex(body, r"(?m)^body:$")
            self.assertRegex(body, r"(?m)^\s+- type: (textarea|input|markdown|dropdown|checkboxes)$")
            self.assertRegex(body, r"(?m)^\s+id: \w+$")
            self.assertNotIn("\t", body)

    def test_pr_template_sections(self):
        pr = text(".github/pull_request_template.md")
        for want in ("Why", "What changed", "How to verify", "Closes #", "changelog.d/",
                     "python3 scripts/brainrc.py validate", "python3 -m unittest discover -s tests"):
            self.assertIn(want, pr)

    def test_no_personal_paths_or_emails(self):
        files = [".github/CODEOWNERS", ".github/pull_request_template.md",
                 ".github/ISSUE_TEMPLATE/config.yml", *(f".github/ISSUE_TEMPLATE/{f}" for f in FORMS)]
        for rel in files:
            body = text(rel)
            self.assertIsNone(re.search(r"[\w.+-]+@[\w-]+\.[\w.]+|/Users/|/home/", body), rel)


if __name__ == "__main__":
    unittest.main()
