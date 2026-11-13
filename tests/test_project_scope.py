"""Project scope (#282): `apply` in a repo with brainrc.toml writes that repo's agent files, and
`status` shows the user scope and the project."""
import os
import shutil
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import PACK_TOML, TempRepoCase, brainrc, install_harnesses, make_pack, quiet  # noqa: E402

from brainrc import lock, project  # noqa: E402

TEAM_TOML = PACK_TOML.replace('name = "acme"', 'name = "team"').replace('prefix = "acme-"', 'prefix = "team-"') \
    .replace('requires_core = ">=1.0, <2"', 'requires_core = ">=0"')
FIXTURE_SKILLS = ["brainrc-aws", "brainrc-gatework", "brainrc-kubernetes", "brainrc-terraform",
                  "brainrc-ticket-github", "brainrc-ticket-jira", "brainrc-work", "spec-agent"]


def make_team_pack(root: Path) -> Path:
    """A pack with two skills and a rule, named team (prefix team-)."""
    make_pack(root, TEAM_TOML)
    for old in ("acme-deploy", "acme-context"):
        new = root / "skills" / old.replace("acme-", "team-")
        (root / "skills" / old).rename(new)
        skill = new / "SKILL.md"
        skill.write_text(skill.read_text().replace(old, new.name))
    (root / "agents/acme-reviewer.md").rename(root / "agents/team-reviewer.md")
    agent = root / "agents/team-reviewer.md"
    agent.write_text(agent.read_text().replace("acme-reviewer", "team-reviewer"))
    (root / "rules/50-acme.md").rename(root / "rules/50-team.md")
    (root / "rules/50-team.md").write_text("# Team\n\n- Team rule.\n")
    return root


def gatework_remote(tmp: Path) -> str:
    """A bare repo standing in for brainrc/gatework, tagged v1 and v2 (v2 adds brainrc-new). Returns its URL."""
    from test_brainrc import DEFAULT_PACK, git
    work = tmp / "gatework-work"
    shutil.copytree(DEFAULT_PACK, work, symlinks=True, ignore=shutil.ignore_patterns("__pycache__"))
    git("init", "-q", "-b", "main", cwd=work)
    git("add", "-A", cwd=work)
    git("commit", "-qm", "v1", cwd=work)
    git("tag", "v1", cwd=work)
    new = work / "skills/brainrc-new"
    new.mkdir()
    (new / "SKILL.md").write_text("---\nname: brainrc-new\ndescription: New in v2.\n---\nBody.\n")
    git("add", "-A", cwd=work)
    git("commit", "-qm", "v2", cwd=work)
    git("tag", "v2", cwd=work)
    git("clone", "-q", "--bare", str(work), str(tmp / "gatework.git"))
    return (tmp / "gatework.git").as_uri()


def use_git_gatework(repo: Path, url: str, ref: str = "v1") -> None:
    """Make core's default pack a git pack, as the shipped packs.toml does."""
    (repo / "packs.toml").write_text(f'[gatework]\ngit = "{url}"\nref = "{ref}"\n')


class ProjectCase(TempRepoCase):
    """A temp HOME with every harness installed, and a temp repo (with `.git`) as the current directory."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp()).resolve()
        self.old_home = os.environ["HOME"]
        os.environ["HOME"] = str(self.home)
        install_harnesses(self.home)
        self.proj = Path(tempfile.mkdtemp()).resolve() / "app"
        (self.proj / ".git").mkdir(parents=True)
        self.old_cwd = os.getcwd()
        os.chdir(self.proj)

    def tearDown(self):
        os.chdir(self.old_cwd)
        os.environ["HOME"] = self.old_home
        shutil.rmtree(self.home)
        shutil.rmtree(self.proj.parent)
        super().tearDown()

    def manifest(self, text: str = "") -> None:
        (self.proj / "brainrc.toml").write_text(text)

    def apply(self, code: int = 0) -> str:
        got, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(got, code, out)
        return out

    def status(self, code: int = 0) -> str:
        got, out = quiet(brainrc.cmd_sync, False)
        self.assertEqual(got, code, out)
        return out

    def skills(self) -> list[str]:
        d = self.proj / ".agents/skills"
        return sorted(p.name for p in d.iterdir()) if d.is_dir() else []

    def project_files(self) -> dict[str, bytes]:
        return {p.relative_to(self.proj).as_posix(): p.read_bytes() for p in sorted(self.proj.rglob("*"))
                if p.is_file() and ".git" not in p.relative_to(self.proj).parts}


class FindProjectTest(ProjectCase):
    def test_found_in_a_subdirectory_up_to_the_repo_root(self):
        self.manifest()
        sub = self.proj / "src/deep"
        sub.mkdir(parents=True)
        self.assertEqual(project.find_project(sub), self.proj)

    def test_not_found_above_the_repo_root(self):
        (self.proj.parent / "brainrc.toml").write_text("")
        self.assertIsNone(project.find_project(self.proj))

    def test_outside_a_repo_only_the_directory_itself(self):
        loose = self.proj.parent / "loose"
        (loose / "sub").mkdir(parents=True)
        (loose / "brainrc.toml").write_text("")
        self.assertEqual(project.find_project(loose), loose)
        self.assertIsNone(project.find_project(loose / "sub"))


class NoManifestTest(ProjectCase):
    def test_without_brainrc_toml_only_the_user_scope_runs(self):
        out = self.apply()
        self.assertNotIn("Project", out)
        self.assertEqual(self.project_files(), {})
        self.assertTrue((self.home / ".claude/skills/brainrc-work").is_symlink())


class ApplyTest(ProjectCase):
    def test_default_packs_are_on_and_both_scopes_apply(self):
        self.manifest()
        out = self.apply()
        self.assertIn(f"Project {self.proj} (brainrc.toml)", out)
        self.assertIn("CREATE    project   .agents/skills/brainrc-work/", out)
        self.assertEqual(self.skills(), FIXTURE_SKILLS)
        self.assertTrue((self.home / ".claude/skills/brainrc-work").is_symlink())  # user scope too
        work = self.proj / ".agents/skills/brainrc-work/SKILL.md"
        self.assertFalse(work.is_symlink())
        self.assertEqual(work.read_bytes(), (self.repo / "packs/gatework/skills/brainrc-work/SKILL.md").read_bytes())
        # A skill's linked directory is copied as files: roles/ -> ../../agents
        self.assertTrue((self.proj / ".agents/skills/brainrc-gatework/roles/brainrc-analyst.md").is_file())
        data = lock.read(self.proj / "brainrc.lock")
        self.assertEqual(data["scope"], "project")
        self.assertEqual(data["outputs"][".agents/skills/brainrc-work/SKILL.md"], lock.digest(work.read_bytes()))

    def test_second_apply_changes_nothing(self):
        self.manifest()
        self.apply()
        before = self.project_files()
        out = self.apply()
        self.assertIn("Project in sync.", out)
        self.assertEqual(self.project_files(), before)

    def test_status_shows_both_scopes_and_writes_nothing(self):
        self.manifest()
        out = self.status()
        self.assertIn("CREATE    claude", out)
        self.assertIn("CREATE    project   .agents/skills/brainrc-work/", out)
        self.assertIn("LOCK", out)
        self.assertEqual(self.project_files(), {"brainrc.toml": b""})
        self.apply()
        out = self.status()
        self.assertIn("Everything in sync.", out)
        self.assertIn("Project in sync.", out)

    def test_disabling_a_default_pack_prunes_its_files(self):
        self.manifest()
        self.apply()
        self.manifest("[packs.gatework]\nenabled = false\n")
        out = self.apply()
        self.assertIn("PRUNE     project   .agents/skills/brainrc-work/", out)
        self.assertEqual(self.skills(), [])
        self.assertFalse((self.proj / ".agents").exists())
        self.assertNotIn("outputs", lock.read(self.proj / "brainrc.lock"))
        self.assertTrue((self.home / ".claude/skills/brainrc-work").is_symlink())  # the user's own stays

    def test_exclude_leaves_an_item_out(self):
        self.manifest('exclude = ["gatework:skills/brainrc-aws", "skills/spec-*"]\n')
        self.apply()
        self.assertNotIn("brainrc-aws", self.skills())
        self.assertNotIn("spec-agent", self.skills())
        self.assertIn("brainrc-work", self.skills())

    def test_a_pack_in_the_repo_adds_skills_and_rules(self):
        make_team_pack(self.proj / "tools/team-pack")
        self.manifest('[packs.gatework]\nenabled = false\n\n[packs.team]\npath = "tools/team-pack"\n')
        self.apply()
        self.assertEqual(self.skills(), ["team-context", "team-deploy"])
        agents = (self.proj / "AGENTS.md").read_text()
        self.assertTrue(agents.startswith("<!-- brainrc:begin: generated from brainrc.toml (packs: team)."))
        self.assertIn("- Team rule.", agents)
        self.assertTrue(agents.endswith("<!-- brainrc:end -->\n"))
        block = project.BLOCK.search(agents)[0]
        self.assertEqual(lock.read(self.proj / "brainrc.lock")["blocks"], {"AGENTS.md": lock.digest(block.encode())})


class MachineLocalTest(ProjectCase):
    """Nothing machine-local reaches a project's files: they must match on every machine."""

    def test_local_config_does_not_change_the_project(self):
        self.manifest()
        self.apply()
        before = self.project_files()
        (self.repo / "packs.local.toml").write_text("[gatework]\nenabled = false\n")
        (self.repo / "brainrc.local.toml").write_text('profile = "minimal"\nexclude = ["skills/brainrc-work"]\n')
        (self.repo / "rules/99-mine.local.md").write_text("# Mine\n")
        out = self.apply()
        self.assertIn("Project in sync.", out)
        self.assertEqual(self.project_files(), before)
        self.assertFalse((self.home / ".claude/skills/brainrc-work").exists())  # the user scope did change


class OwnershipTest(ProjectCase):
    def test_a_file_brainrc_did_not_write_is_a_conflict(self):
        mine = self.proj / ".agents/skills/brainrc-work/SKILL.md"
        mine.parent.mkdir(parents=True)
        mine.write_text("my own\n")
        self.manifest()
        out = self.apply(code=1)
        self.assertIn("CONFLICT  project   .agents/skills/brainrc-work/", out)
        self.assertEqual(mine.read_text(), "my own\n")
        self.assertNotIn(".agents/skills/brainrc-work/SKILL.md", lock.read(self.proj / "brainrc.lock")["outputs"])
        self.assertIn("brainrc-aws", self.skills())  # the rest is written

    def test_nothing_is_written_through_a_linked_directory(self):
        outside = self.proj.parent / "outside"
        outside.mkdir()
        (self.proj / ".agents").symlink_to(outside)
        self.manifest()
        out = self.apply(code=1)
        self.assertIn("CONFLICT  project   .agents/skills/brainrc-work/", out)
        self.assertEqual(list(outside.iterdir()), [])

    def test_an_identical_file_is_adopted(self):
        mine = self.proj / ".agents/skills/brainrc-work/SKILL.md"
        mine.parent.mkdir(parents=True)
        shutil.copy(self.repo / "packs/gatework/skills/brainrc-work/SKILL.md", mine)
        self.manifest()
        out = self.apply()
        self.assertNotIn("brainrc-work/", out)
        self.assertIn(".agents/skills/brainrc-work/SKILL.md", lock.read(self.proj / "brainrc.lock")["outputs"])

    def test_an_owned_file_follows_its_source(self):
        self.manifest()
        self.apply()
        source = self.repo / "packs/gatework/skills/brainrc-work/SKILL.md"
        source.write_text(source.read_text() + "More.\n")
        out = self.apply()
        self.assertIn("UPDATE    project   .agents/skills/brainrc-work/", out)
        self.assertTrue((self.proj / ".agents/skills/brainrc-work/SKILL.md").read_text().endswith("More.\n"))

    def test_an_edited_file_that_is_no_longer_wanted_stays(self):
        self.manifest()
        self.apply()
        edited = self.proj / ".agents/skills/brainrc-aws/SKILL.md"
        edited.write_text("edited\n")
        self.manifest('exclude = ["skills/brainrc-aws"]\n')
        out = self.apply(code=1)
        self.assertIn("CONFLICT  project   .agents/skills/brainrc-aws/", out)
        self.assertEqual(edited.read_text(), "edited\n")


class AgentsBlockTest(ProjectCase):
    def setUp(self):
        super().setUp()
        make_team_pack(self.proj / "tools/team-pack")
        self.manifest('[packs.gatework]\nenabled = false\n\n[packs.team]\npath = "tools/team-pack"\n')

    def test_your_own_text_stays_around_the_block(self):
        (self.proj / "AGENTS.md").write_text("# My repo\n\nBuild with make.\n")
        self.apply()
        text = (self.proj / "AGENTS.md").read_text()
        self.assertTrue(text.startswith("# My repo\n\nBuild with make.\n\n<!-- brainrc:begin"))
        (self.proj / "AGENTS.md").write_text(text + "\n## After\n\nMore of mine.\n")
        (self.proj / "tools/team-pack/rules/50-team.md").write_text("# Team\n\n- Changed rule.\n")
        out = self.apply()
        self.assertIn("UPDATE    project   AGENTS.md", out)
        text = (self.proj / "AGENTS.md").read_text()
        self.assertIn("- Changed rule.", text)
        self.assertNotIn("- Team rule.", text)
        self.assertTrue(text.startswith("# My repo\n\nBuild with make.\n\n<!-- brainrc:begin"))
        self.assertTrue(text.endswith("<!-- brainrc:end -->\n\n## After\n\nMore of mine.\n"))

    def test_turning_the_pack_off_removes_only_the_block(self):
        (self.proj / "AGENTS.md").write_text("# My repo\n")
        self.apply()
        self.manifest('[packs.gatework]\nenabled = false\n')
        self.apply()
        self.assertEqual((self.proj / "AGENTS.md").read_text(), "# My repo\n")

    def test_a_file_that_was_only_the_block_is_removed(self):
        self.apply()
        self.manifest('[packs.gatework]\nenabled = false\n')
        self.apply()
        self.assertFalse((self.proj / "AGENTS.md").exists())


class GitPackProjectTest(ProjectCase):
    def setUp(self):
        super().setUp()
        from test_brainrc import git
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        work = make_team_pack(self.tmp / "work")
        git("init", "-q", "-b", "main", cwd=work)
        git("add", "-A", cwd=work)
        git("commit", "-qm", "v1", cwd=work)
        git("tag", "v1", cwd=work)
        git("clone", "-q", "--bare", str(work), str(self.tmp / "team.git"))
        self.url = (self.tmp / "team.git").as_uri()

    def tearDown(self):
        shutil.rmtree(self.tmp)
        super().tearDown()

    def test_status_does_not_fetch_and_apply_does(self):
        self.manifest(f'[packs.team]\ngit = "{self.url}"\nref = "v1"\n')
        out = self.status()
        self.assertIn(f"FETCH     team      {self.url} (v1)", out)
        self.assertFalse((self.settings_home / "project-packs").exists())
        self.apply()
        self.assertIn("team-deploy", self.skills())
        clones = list((self.settings_home / "project-packs").iterdir())
        self.assertEqual([c.name[:5] for c in clones], ["team-"])
        self.assertFalse((self.settings_home / "packs/team").exists())  # not the user scope's clone

    def test_a_project_pins_the_default_git_pack_to_another_ref(self):
        use_git_gatework(self.repo, gatework_remote(self.tmp), "v1")
        self.manifest('[packs.gatework]\nref = "v2"\n')
        self.apply()
        self.assertIn("brainrc-new", self.skills())  # the project's v2
        self.assertFalse((self.home / ".claude/skills/brainrc-new").exists())  # the user's v1
        self.assertTrue((self.home / ".claude/skills/brainrc-work").is_symlink())

    def test_a_failed_fetch_writes_nothing_in_the_project(self):
        self.manifest(f'[packs.team]\ngit = "{(self.tmp / "missing.git").as_uri()}"\n')
        out = self.apply(code=1)
        self.assertIn("Nothing written in the project", out)
        self.assertEqual(self.project_files(), {"brainrc.toml": self.project_files()["brainrc.toml"]})


class ManifestErrorTest(ProjectCase):
    def test_schema_errors_name_the_file_and_write_nothing(self):
        self.manifest('[packs.team]\npath = "../outside"\n')
        out = self.apply(code=1)
        self.assertIn("brainrc.toml: packs.team.path", out)
        self.assertIn("Nothing written in the project", out)
        self.assertTrue((self.home / ".claude/skills/brainrc-work").is_symlink())  # the user scope still applied
        self.assertFalse((self.proj / "brainrc.lock").exists())

    def test_a_new_pack_needs_an_origin(self):
        self.manifest('[packs.team]\nref = "v1"\n')
        out = self.apply(code=1)
        self.assertIn("packs.team: set `git` or `path` (team isn't a default pack)", out)

    def test_invalid_toml_names_the_line(self):
        self.manifest("[packs.team\n")
        out = self.apply(code=1)
        self.assertIn("brainrc.toml:1: invalid TOML", out)


class LockFormatTest(unittest.TestCase):
    def test_valid_fixture_locks_are_in_canonical_form(self):
        fixtures = Path(__file__).resolve().parent / "fixtures/lockfile/valid"
        for path in sorted(fixtures.glob("*.lock")):
            with self.subTest(path.name):
                text = path.read_text()
                self.assertEqual(lock.dumps(lock.loads(text)), text)

    def test_odd_keys_and_strings_are_quoted(self):
        data = {"version": 1, "brainrc": "1.0.0", "scope": "project",
                "outputs": {'a "b"/c.md': "sha256:" + "0" * 64, "x.md": "sha256:" + "1" * 64}}
        text = lock.dumps(data)
        self.assertIn('"a \\"b\\"/c.md" = ', text)
        self.assertEqual(tomllib.loads(text)["outputs"], data["outputs"])


if __name__ == "__main__":
    unittest.main()
