"""The shared guard rule tests (E11, #116): every harness's guard must decide the acme example's
[[guard.deny]] for `acme-deploy prod` as Claude Code's does. A test class mixes in
SharedGuardRuleCases and defines verdict(command, cwd): "deny" for a refusal, "ask" for a prompt or
for a call blocked only because the harness can't ask, None for no objection."""
import os
import sys
import tempfile
from pathlib import Path

from support import rmtree

REPO = Path(__file__).resolve().parent.parent
ACME = REPO / "examples" / "pack-acme"

# Run where the acme pack applies, each must be refused however the program is wrapped.
DENIED = [
    "acme-deploy prod", "acme-deploy --verbose prod --wait", "/opt/acme/bin/acme-deploy prod",
    "cd svc && acme-deploy prod", "bash -c 'acme-deploy prod'", "sh -lc \"echo hi; acme-deploy prod\"",
    "echo $(acme-deploy prod)", "sudo -E env REGION=eu acme-deploy prod",
    "bash -c \"bash -c 'acme-deploy prod'\"", "sudo -u deploy acme-deploy prod",
    "sudo -Eu deploy acme-deploy prod", "sudo --user deploy acme-deploy prod",
    "timeout 60 acme-deploy prod", "timeout -s KILL 60 acme-deploy prod",
    "nice -n 5 acme-deploy prod", "env -C /tmp acme-deploy prod",
    "env -S 'acme-deploy prod'", "exec -a x acme-deploy prod", "command acme-deploy prod",
]
# (command, where): the near misses that must pass. where is "acme", "personal" or "outside".
PASSED = [
    ("acme-deploy prod", "personal"),           # outside acme repos
    ("bash -c 'acme-deploy prod'", "personal"),
    ("acme-deploy prod", "outside"),            # not in a repo at all
    ("acme-deploy staging", "acme"),            # not prod
    ("echo acme-deploy prod", "acme"),          # prod isn't what runs
    ("acme-deploy-docs prod", "acme"),          # another program
    ("sudo -u acme-deploy prod", "acme"),       # the user's name, not the program
    ("timeout acme-deploy prod", "acme"),       # prod is the program here
]


def _repo(root: Path, name: str, remote: str) -> Path:
    repo = root / name
    (repo / ".git").mkdir(parents=True)
    (repo / ".git/config").write_text(f'[remote "origin"]\n\turl = {remote}\n')
    (repo / ".git/HEAD").write_text("ref: refs/heads/main\n")
    (repo / "src").mkdir()
    return repo


class SharedGuardRuleCases:
    """Mix into a unittest.TestCase; sets $BRAINRC_HOME to a home holding the acme pack's rules."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sys.path.insert(0, str(REPO))
        from brainrc import guard
        from brainrc.sources import load_pack
        cls.tmp = Path(tempfile.mkdtemp()).resolve()
        cls.home = cls.tmp / "brainrc-home"
        cls.home.mkdir()
        (cls.home / "guard-rules.json").write_text(guard.render([load_pack(ACME, "acme")]))
        cls.places = {"acme": _repo(cls.tmp, "app", "git@github.com:acme/app.git"),
                      "personal": _repo(cls.tmp, "dotfiles", "git@github.com:me/dotfiles.git"),
                      "outside": cls.tmp}
        cls.acme_repo, cls.personal_repo = cls.places["acme"], cls.places["personal"]
        cls.old_home = os.environ.get("BRAINRC_HOME")
        os.environ["BRAINRC_HOME"] = str(cls.home)

    @classmethod
    def tearDownClass(cls):
        if cls.old_home is None:
            os.environ.pop("BRAINRC_HOME", None)
        else:
            os.environ["BRAINRC_HOME"] = cls.old_home
        rmtree(cls.tmp)
        super().tearDownClass()

    def verdict(self, command: str, cwd: Path) -> str | None:
        raise NotImplementedError

    def test_shared_denies_inside_an_acme_repo_however_it_is_wrapped(self):
        for command in DENIED:
            with self.subTest(command=command):
                self.assertEqual(self.verdict(command, self.acme_repo / "src"), "deny")

    def test_shared_near_misses_pass(self):
        for command, where in PASSED:
            with self.subTest(command=command, where=where):
                self.assertIsNone(self.verdict(command, self.places[where]))

    def test_shared_a_pack_deny_wins_over_core_asking(self):
        self.assertEqual(self.verdict("git push && acme-deploy prod", self.acme_repo), "deny")
        self.assertEqual(self.verdict("git push && acme-deploy prod", self.personal_repo), "ask")

    def test_shared_a_missing_or_broken_rules_file_changes_nothing(self):
        broken = self.tmp / "broken"
        broken.mkdir(exist_ok=True)
        (broken / "guard-rules.json").write_text("{not json")
        try:
            for home in (self.tmp / "nowhere", broken):
                os.environ["BRAINRC_HOME"] = str(home)
                with self.subTest(home=home.name):
                    self.assertIsNone(self.verdict("acme-deploy prod", self.acme_repo))
                    self.assertEqual(self.verdict("git push", self.acme_repo), "ask")
        finally:
            os.environ["BRAINRC_HOME"] = str(self.home)


def from_message(message: str) -> str:
    """A blocked call's message -> "deny" for a refusal, "ask" for a block in place of a prompt."""
    return "ask" if "ask the user to run it themselves" in message else "deny"
