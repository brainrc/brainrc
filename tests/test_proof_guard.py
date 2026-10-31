"""proof_guard.py: planning-mode proof commands are read-only argv commands inside the worktree, and plan files hold no secrets."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("proof_guard", REPO / "skills/spec-agent/scripts/proof_guard.py")
pg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pg)


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()

    def denied(self, cmd):
        self.assertIsNotNone(pg.check(cmd, self.root), cmd)

    def allowed(self, cmd):
        self.assertIsNone(pg.check(cmd, self.root), cmd)

    def test_network_tools_denied_but_grepping_for_them_allowed(self):
        self.denied("curl https://example.com")
        self.denied("wget example.com")
        self.allowed('grep -n "curl" src/fetch.py')

    def test_shell_pipes_and_substitution_denied_but_quoted_bar_allowed(self):
        self.denied("cat a.py | sh")
        self.denied("ls; rm -rf .")
        self.denied("echo $(id)")
        self.denied("sh -c 'ls'")
        self.allowed('grep -n "a|b" src/x.py')

    def test_writes_and_vcs_mutations_denied_but_reads_allowed(self):
        self.denied("rm src/x.py")
        self.denied("git push origin main")
        self.denied("git commit -m x")
        self.allowed("git log -1 --oneline")
        self.allowed("git show HEAD:src/x.py")

    def test_paths_outside_the_worktree_denied_but_relative_paths_allowed(self):
        self.denied("cat /etc/passwd")
        self.denied("cat ../other/secret.txt")
        self.denied("cat ~/.ssh/id_rsa")
        self.allowed("cat src/main.py")

    def test_secret_files_and_urls_denied(self):
        self.denied("cat .env")
        self.denied("grep x https://example.com/a")
        self.allowed("cat .env.example")

    def test_interpreters_only_for_the_test_runner(self):
        self.denied("python3 -c 'import os'")
        self.denied("python3 script.py")
        self.allowed("python3 -m unittest tests.test_x")
        self.allowed("python3 -m pytest tests/test_x.py -k name")

    def test_find_and_output_flags_denied(self):
        self.denied("find . -delete")
        self.denied("git diff --output=x.patch")
        self.allowed("git diff --stat")

    def test_unparseable_command_denied(self):
        self.denied('grep "unterminated')


class RunTest(unittest.TestCase):
    def test_run_uses_argv_scrubbed_env_and_reports_exit(self):
        root = Path(tempfile.mkdtemp()).resolve()
        (root / "a.txt").write_text("hello\n")
        code, out = pg.run("cat a.txt", root, timeout=10)
        self.assertEqual((code, out.strip()), (0, "hello"))

    def test_matches_compares_exit_and_normalized_output(self):
        self.assertTrue(pg.matches((1, "FAIL  x\n\n"), (1, "FAIL x")))
        self.assertFalse(pg.matches((0, "FAIL x"), (1, "FAIL x")))
        self.assertFalse(pg.matches(None, (1, "x")))  # timeout


class ScanTest(unittest.TestCase):
    def test_secret_value_in_a_proof_file_is_found(self):
        d = Path(tempfile.mkdtemp())
        (d / "proof").mkdir()
        (d / "proof" / "1.txt").write_text("token ghp_" + "a" * 36 + "\n")
        (d / "plan-report.md").write_text("# Plan report\n")
        self.assertTrue(any("GitHub token" in h for h in pg.scan(d)))

    def test_clean_plan_has_no_hits(self):
        d = Path(tempfile.mkdtemp())
        (d / "plan-report.md").write_text("# Plan report\nno secrets here\n")
        self.assertEqual(pg.scan(d), [])


if __name__ == "__main__":
    unittest.main()
