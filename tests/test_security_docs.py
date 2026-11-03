"""SECURITY.md and GOVERNANCE.md state the guard model, reporting, and decision rules (AC1 to AC3, AC8)."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADVISORIES = "https://github.com/brainrc/brainrc/security/advisories/new"


def text(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


class SecurityDocsTest(unittest.TestCase):
    def test_files_exist(self):
        for rel in ("SECURITY.md", "GOVERNANCE.md"):
            self.assertTrue((ROOT / rel).is_file(), rel)

    def test_security_guard_model_and_links(self):
        body = text("SECURITY.md")
        self.assertIn("docs/guardrails.md", body)
        self.assertIn("seatbelt", body)
        self.assertIn("credentials", body)
        self.assertIn("Known gaps", body)

    def test_security_private_reporting(self):
        body = text("SECURITY.md")
        self.assertIn("Report a vulnerability", body)
        self.assertIn(ADVISORIES, body)
        self.assertRegex(body, r"(?i)public issue")

    def test_security_supported_versions_and_response(self):
        body = text("SECURITY.md")
        self.assertRegex(body, r"(?m)^#+ Supported versions")
        self.assertIn("latest release", body)
        self.assertIsNone(re.search(r"(?i)within\s+\d+\s+(hours?|days?|weeks?|business)", body))

    def test_governance(self):
        body = text("GOVERNANCE.md")
        self.assertIn("bxker", body)
        self.assertIn("maintainer", body)
        self.assertIn("squash", body.lower())
        self.assertIn("CI", body)
        self.assertIn("CONTRIBUTING.md", body)
        self.assertRegex(body, r"(?mi)^#+ .*become a maintainer")

    def test_no_personal_data(self):
        for rel in ("SECURITY.md", "GOVERNANCE.md"):
            body = text(rel)
            self.assertIsNone(re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", body), rel)
            self.assertNotIn("/Users/", body)
            self.assertNotIn("/home/", body)


if __name__ == "__main__":
    unittest.main()
