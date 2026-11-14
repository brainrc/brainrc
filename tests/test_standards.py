"""Standards-first project output (#286): .agents/skills/ and AGENTS.md for every tool, and a
tool's own files only where harnesses.toml says it can't read those. Golden trees in
tests/fixtures/project-golden/; BRAINRC_REGOLDEN=1 rewrites them (then read the diff)."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import rmtree  # noqa: E402
from test_project_scope import ProjectCase, make_team_pack  # noqa: E402

GOLDEN = Path(__file__).resolve().parent / "fixtures/project-golden"
TEAM = '[packs.gatework]\nenabled = false\n\n[packs.team]\npath = "tools/team-pack"\n'
TOOL_DIRS = (".claude", ".cursor", ".codex", ".opencode", ".gemini", ".agent")


class StandardsTest(ProjectCase):
    def setUp(self):
        super().setUp()
        make_team_pack(self.proj / "tools/team-pack")

    def generated(self) -> dict[str, bytes]:
        """What brainrc wrote: everything but the pack, the manifest and the lock (it names the version)."""
        return {k: v for k, v in self.project_files().items()
                if not k.startswith("tools/") and k not in ("brainrc.toml", "brainrc.lock")}

    def assert_golden(self, name: str) -> None:
        want = GOLDEN / name
        got = self.generated()
        if os.environ.get("BRAINRC_REGOLDEN"):
            rmtree(want, ignore_errors=True)
            for rel, data in got.items():
                (want / rel).parent.mkdir(parents=True, exist_ok=True)
                (want / rel).write_bytes(data)
        expected = {p.relative_to(want).as_posix(): p.read_bytes() for p in sorted(want.rglob("*")) if p.is_file()}
        self.assertEqual(sorted(got), sorted(expected))
        for rel in expected:  # Windows checks the goldens out with CRLF, so compare line ends as LF
            self.assertEqual(got[rel].replace(b"\r\n", b"\n"), expected[rel].replace(b"\r\n", b"\n"), rel)

    def test_default_writes_the_standard_files_and_claude_s_own(self):
        self.manifest(TEAM)
        self.apply()
        self.assert_golden("default")
        self.assertEqual(sorted(d for d in TOOL_DIRS if (self.proj / d).exists()), [".claude"])

    def test_tools_that_read_the_standard_get_nothing_else(self):
        self.manifest('harnesses = ["antigravity", "codex", "cursor", "opencode"]\n\n' + TEAM)
        self.apply()
        self.assert_golden("standard-only")
        self.assertEqual([d for d in TOOL_DIRS if (self.proj / d).exists()], [])
        self.assertFalse((self.proj / "CLAUDE.md").exists())

    def test_an_empty_list_means_the_standard_files_only(self):
        self.manifest('harnesses = []\n\n' + TEAM)
        self.apply()
        self.assert_golden("standard-only")

    def test_dropping_a_harness_takes_its_files_back_out(self):
        self.manifest(TEAM)
        (self.proj / "CLAUDE.md").write_text("# Mine\n")
        self.apply()
        self.assertTrue((self.proj / "CLAUDE.md").read_text().startswith("# Mine\n\n<!-- brainrc:begin"))
        self.manifest('harnesses = ["codex"]\n\n' + TEAM)
        out = self.apply()
        self.assertIn("PRUNE     project   .claude/skills/team-deploy/", out)
        self.assertFalse((self.proj / ".claude").exists())
        self.assertEqual((self.proj / "CLAUDE.md").read_text(), "# Mine\n")

    def test_machine_local_harness_settings_never_reach_the_repo(self):
        (self.repo / "harnesses.local.toml").write_text('[cursor]\nproject_skills = ".cursor/skills"\n')
        self.manifest(TEAM)
        out = self.apply()
        self.assertIn("`project_skills` is read from core's harnesses.toml only", out)
        self.assertFalse((self.proj / ".cursor").exists())
        self.assert_golden("default")

    def test_an_unknown_harness_is_an_error(self):
        self.manifest('harnesses = ["vim"]\n\n' + TEAM)
        out = self.apply(code=1)
        self.assertIn("harnesses: unknown harness `vim`", out)
        self.assertFalse((self.proj / ".agents").exists())

    def test_a_project_path_must_stay_in_the_repo(self):
        text = (self.repo / "harnesses.toml").read_text()
        self.manifest(TEAM)
        for bad in ("../elsewhere", ".agents/skills/", "./x", ".git/hooks", "a//b", "/abs", "~/x"):
            (self.repo / "harnesses.toml").write_text(text.replace('project_skills = ".claude/skills"',
                                                                   f'project_skills = "{bad}"'))
            self.assertIn("[claude] project_skills must be a path inside the repo", self.apply(code=1), bad)

    def test_a_claude_md_that_already_reads_agents_md_gets_no_block(self):
        self.manifest(TEAM)
        (self.proj / "CLAUDE.md").symlink_to("AGENTS.md")
        out = self.apply()
        self.assertNotIn("CONFLICT", out)
        self.assertTrue((self.proj / "CLAUDE.md").is_symlink())
        self.assertNotIn("@AGENTS.md", (self.proj / "AGENTS.md").read_text())
        (self.proj / "CLAUDE.md").unlink()
        (self.proj / "CLAUDE.md").write_text("# Mine\n\n@AGENTS.md\n")
        self.apply()
        self.assertEqual((self.proj / "CLAUDE.md").read_text(), "# Mine\n\n@AGENTS.md\n")

    def test_a_deeper_skills_directory_is_grouped_by_skill(self):
        text = (self.repo / "harnesses.toml").read_text()
        (self.repo / "harnesses.toml").write_text(text.replace('project_skills = ".claude/skills"',
                                                               'project_skills = ".github/copilot/skills"'))
        self.manifest(TEAM)
        out = self.apply()
        self.assertIn("CREATE    project   .github/copilot/skills/team-deploy/\n", out)
