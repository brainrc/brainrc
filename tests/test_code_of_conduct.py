"""CODE_OF_CONDUCT.md is the Contributor Covenant 2.1 with a private report link (AC1, AC4, AC11)."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADVISORIES = "https://github.com/brainrc/brainrc/security/advisories/new"


def coc():
    return (ROOT / "CODE_OF_CONDUCT.md").read_text(encoding="utf-8")


class CodeOfConductTest(unittest.TestCase):
    def test_is_contributor_covenant_2_1(self):
        body = coc()
        self.assertIn("Contributor Covenant", body)
        self.assertIn("version 2.1", body)
        self.assertIn("https://www.contributor-covenant.org/version/2/1/code_of_conduct.html", body)

    def test_enforcement_contact_is_private_report_url(self):
        body = coc()
        self.assertIn(ADVISORIES, body)
        self.assertNotIn("[INSERT CONTACT METHOD]", body)

    def test_has_enforcement_guidelines(self):
        body = coc()
        for want in ("## Our Pledge", "## Enforcement Guidelines", "### 4. Permanent Ban", "## Attribution"):
            self.assertIn(want, body)

    def test_no_email_address(self):
        self.assertIsNone(re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", coc()))


if __name__ == "__main__":
    unittest.main()
