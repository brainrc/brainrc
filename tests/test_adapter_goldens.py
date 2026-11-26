"""Golden output per tool (#306): every file and link `apply` writes for each harness, in user and
project scope, byte for byte. Added before the tools moved onto brainrc/adapters/, so the move can
show it changed no output. tests/fixtures/adapter-golden/ holds one dump per scenario;
BRAINRC_REGOLDEN=1 rewrites them (then read the diff: every change there is a change users get)."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import home_env, readlink, restore_home, rmtree, saved_home  # noqa: E402
from test_brainrc import PACK_TOML, TempRepoCase, brainrc, install_harnesses, make_pack, quiet, set_core_version  # noqa: E402
from test_project_scope import make_team_pack  # noqa: E402

GOLDEN = Path(__file__).resolve().parent / "fixtures/adapter-golden"
# Rendered once for every tool and checked by their own tests: here only that they exist, so an
# edit to a core rule or to Gatework's stand-in doesn't churn every golden.
SHARED_RENDERS = {"{BRAINRC_HOME}/instructions.md", "{BRAINRC_HOME}/extensions.md"}

GUARD_RULES = '''
[[guard.deny]]
match = "acme-deploy prod"
reason = "deploys to production"

[[guard.ask]]
tool = "mcp__acme-jira__*transition*"
reason = "moves an Acme ticket"

[[guard.deny]]
path = "~/.acme/credentials"
reason = "holds the Acme deploy key"

[[guard.deny]]
host = "*.acme-internal.example"
reason = "internal hosts"
'''

SERVERS = '''
[servers.acme-docs]
command = "acme-docs-mcp"
args = ["--stdio"]
env_from = ["ACME_DOCS_TOKEN"]

[servers.acme-search]
url = "https://search.acme.example/mcp"

[servers.acme-claude-only]
command = "acme-only"
harnesses = ["claude"]
'''


def full_pack(root: Path) -> Path:
    """make_pack's acme pack, plus what every tool can take: a command, MCP servers, guard rules,
    and hooks or a plugin for each tool that runs them."""
    make_pack(root, PACK_TOML + GUARD_RULES)
    (root / "commands").mkdir()
    (root / "commands/acme-ship.md").write_text("---\ndescription: Ship it.\n---\nShip $ARGUMENTS.\n")
    (root / "mcp").mkdir()
    (root / "mcp/servers.toml").write_text(SERVERS)
    for tool, fragment in (("codex", {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
                                {"type": "command", "command": 'python3 "{{hooks_dir}}/guard_acme.py"'}]}]}}),
                           ("cursor", {"version": 1, "hooks": {"beforeShellExecution": [
                                {"command": 'python3 "{{hooks_dir}}/guard_acme.py"'}]}})):
        (root / "overrides" / tool / "hooks").mkdir(parents=True)
        (root / "overrides" / tool / "hooks/guard_acme.py").write_text("print()\n")
        (root / "overrides" / tool / "settings.fragment.json").write_text(json.dumps(fragment))
    (root / "overrides/opencode").mkdir(parents=True)
    (root / "overrides/opencode/plugin.js").write_text("export const AcmeGuard = async () => ({})\n")
    return root


@unittest.skipIf(os.name == "nt", "the goldens hold POSIX paths; the move they guard has no Windows-only code")
class AdapterGoldenTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp()).resolve()
        self.old_home = saved_home()
        os.environ.update(home_env(self.home))
        install_harnesses(self.home)
        self.pack = full_pack(Path(tempfile.mkdtemp()).resolve() / "acme-pack")
        set_core_version(self.repo, "1.2.3")
        (self.repo / "packs.local.toml").write_text(f"[acme]\npath = '{self.pack}'\n")
        self.old_cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self.old_cwd)
        restore_home(self.old_home)
        rmtree(self.home)
        rmtree(self.pack.parent)
        super().tearDown()

    def placeholders(self, text: str) -> str:
        for path, name in ((self.pack, "{PACK}"), (self.settings_home, "{BRAINRC_HOME}"),
                           (self.repo, "{REPO}"), (self.home, "{HOME}")):
            text = text.replace(str(path), name)
        return text

    def dump(self, roots: list[tuple[Path, str]], skip=lambda rel: False) -> str:
        """Every link (as its target) and file (as its text) under each root, paths as placeholders."""
        out = []
        for root, name in roots:
            for p in sorted(root.rglob("*")):
                rel = f"{name}/{p.relative_to(root).as_posix()}"
                if skip(rel) or "__pycache__" in p.parts:
                    continue
                if p.is_symlink():
                    out.append(f"LINK {rel} -> {self.placeholders(readlink(p))}")
                elif p.is_dir():
                    continue
                elif rel in SHARED_RENDERS:
                    out.append(f"FILE {rel} (rendered for every tool; not compared)")
                else:
                    out.append(f"FILE {rel}\n{self.placeholders(p.read_text())}".rstrip("\n"))
        return "\n".join(out) + "\n"

    def assert_golden(self, name: str, got: str) -> None:
        want = GOLDEN / f"{name}.txt"
        if os.environ.get("BRAINRC_REGOLDEN"):
            want.parent.mkdir(parents=True, exist_ok=True)
            want.write_text(got)
        self.assertEqual(got, want.read_text().replace("\r\n", "\n"))

    def apply(self) -> None:
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        code, out = quiet(brainrc.cmd_sync, False)
        self.assertEqual((code, out.strip()), (0, "Everything in sync."))

    def user_scope(self) -> str:
        return self.dump([(self.home, "{HOME}"), (self.settings_home, "{BRAINRC_HOME}")])

    def test_user_scope_for_every_enabled_tool(self):
        self.apply()
        self.assert_golden("user-scope", self.user_scope())

    def test_user_scope_with_gemini_cli_turned_on(self):
        (self.home / ".gemini").mkdir(exist_ok=True)
        (self.repo / "harnesses.local.toml").write_text("[gemini]\nenabled = true\n")
        self.apply()
        self.assert_golden("user-scope-gemini", self.user_scope())

    def test_turning_every_tool_off_takes_brainrc_back_out(self):
        self.apply()
        (self.repo / "harnesses.local.toml").write_text(
            "".join(f"[{n}]\nenabled = false\n\n" for n in brainrc.config.load_harnesses(include_disabled=True)))
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        # Backups carry a timestamp, so they are listed by name pattern only.
        self.assert_golden("user-scope-all-off", self.dump(
            [(self.home, "{HOME}"), (self.settings_home, "{BRAINRC_HOME}")],
            skip=lambda rel: ".bak-brainrc-" in rel))

    def test_project_scope_for_every_tool(self):
        proj = Path(tempfile.mkdtemp()).resolve() / "app"
        (proj / ".git").mkdir(parents=True)
        self.addCleanup(rmtree, proj.parent)
        make_team_pack(proj / "tools/team-pack")
        every = sorted(brainrc.config.load_harnesses(include_disabled=True))
        (proj / "brainrc.toml").write_text(f"harnesses = {json.dumps(every)}\n\n"
                                           '[packs.gatework]\nenabled = false\n\n'
                                           '[packs.team]\npath = "tools/team-pack"\n')
        os.chdir(proj)
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assert_golden("project-scope", self.dump(
            [(proj, "{PROJECT}")], skip=lambda rel: rel.startswith(("{PROJECT}/.git", "{PROJECT}/tools/"))))


if __name__ == "__main__":
    unittest.main()
