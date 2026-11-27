"""Hook commands that run natively on Windows (#178): brainrc/hookcmd.py and each adapter's
`windows_hook`. Runs everywhere: the Windows form is switched on by patching
hookcmd.windows_hooks, and each command line runs through every shell this machine has (sh here;
cmd and PowerShell on Windows), so the same tests check the real thing on the Windows CI cell."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import home_env, restore_home, rmtree, saved_home  # noqa: E402
from test_brainrc import REPO, TempRepoCase, brainrc, install_harnesses, quiet  # noqa: E402

from brainrc import adapters, audit, hookcmd  # noqa: E402
from brainrc.config import ConfigError  # noqa: E402
from brainrc.plan import SettingsMerge  # noqa: E402
from brainrc.settings import merge_settings  # noqa: E402

HOOKED = ("antigravity", "claude", "codex", "copilot", "cursor", "devin", "gemini", "junie", "kiro")
RISKY = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git push origin main"}}
CURSOR_RISKY = {"hook_event_name": "beforeShellExecution", "command": "git push origin main", "cwd": "/tmp/project"}


def shells() -> list:
    """How a tool hands a command line to each shell here, as a function of the line: sh on
    macOS and Linux; on Windows cmd as Node runs a `shell: true` command (`cmd /d /s /c "<line>"`,
    passed verbatim), and PowerShell with the line as one argument."""
    if os.name != "nt":
        return [lambda line: ["sh", "-c", line]]
    found = [lambda line: f'cmd /d /s /c "{line}"']
    found += [lambda line, p=p: [p, "-NoProfile", "-Command", line] for p in ("powershell", "pwsh") if shutil.which(p)]
    return found


def windows(harness: str, hooks_dir: str) -> dict:
    """The hooks apply wants in harness's settings, in the Windows form."""
    m = SettingsMerge(harness, Path("unused.json"), [(REPO / "overrides" / harness / "settings.fragment.json", hooks_dir)])
    with mock.patch.object(hookcmd, "windows_hooks", return_value=True):
        return m.wanted()["hooks"]


def entries(hooks: dict) -> list[dict]:
    return [h for groups in hooks.values() for g in groups for h in ([*g["hooks"]] if "hooks" in g else [g])]


def runnable(entry: dict, harness: str) -> list[str]:
    """The Python source of the Windows form, whichever field the tool takes it in."""
    if harness == "claude":
        return [entry["args"][entry["args"].index("-c") + 1]]
    line = entry[{"codex": "commandWindows", "copilot": "powershell"}.get(harness, "command")]
    return [line.split(" -c ", 1)[1][1:-1]]


class WindowsHookFormTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        rmtree(self.tmp)

    def hooks_dir(self, harness: str) -> Path:
        """A copy of the real hooks beside Claude Code's, as the settings home's hooks copy is laid out."""
        root = self.tmp / "core"
        for name in {harness, "claude"}:
            if not (root / name / "hooks").exists():
                shutil.copytree(REPO / "overrides" / name / "hooks", root / name / "hooks")
        return root / harness / "hooks"

    def test_every_core_hook_has_a_windows_form_with_no_posix_shell(self):
        for harness in HOOKED:
            hooks = windows(harness, str(self.hooks_dir(harness)))
            for entry in entries(hooks):
                for source in runnable(entry, harness):
                    self.assertNotIn("[ ", source, harness)
                    self.assertFalse(hookcmd.UNSAFE & set(source) - {"'"}, (harness, source))

    def test_each_tool_takes_it_where_its_docs_say(self):
        d = str(self.hooks_dir("codex"))
        (claude,) = [e for e in entries(windows("claude", d)) if "guard_outward" in json.dumps(e)]
        self.assertEqual(claude["args"][-2], "-c")
        self.assertTrue(os.path.isabs(claude["command"]), claude)
        (codex,) = entries(windows("codex", d))
        self.assertTrue(codex["command"].startswith('f="'), codex)  # the POSIX line stays for macOS and Linux
        self.assertIn(" -c ", codex["commandWindows"])
        (copilot,) = entries(windows("copilot", d))
        self.assertIn(" -c ", copilot["powershell"])
        self.assertTrue(copilot["command"].startswith('f="'))  # written as Copilot's `bash`
        for harness in ("cursor", "junie", "gemini", "devin", "kiro", "antigravity"):
            for entry in entries(windows(harness, d)):
                self.assertIn(" -c ", entry["command"], harness)

    def run_line(self, source: str, payload: dict, cwd=None) -> list[subprocess.CompletedProcess]:
        line = hookcmd.line(sys.executable, hookcmd.FLAGS, source, None)
        return [subprocess.run(shell(line), input=json.dumps(payload), capture_output=True, text=True,
                               timeout=60, cwd=cwd) for shell in shells()]

    def test_codex_guard_denies_when_present_and_passes_when_gone(self):
        d = self.hooks_dir("codex")
        (source,) = runnable(entries(windows("codex", str(d)))[0], "codex")
        for result in self.run_line(source, RISKY):
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
        rmtree(d)
        for result in self.run_line(source, RISKY):
            self.assertEqual((result.returncode, result.stdout), (0, ""), result.stderr)

    def test_a_module_in_the_project_folder_is_not_imported(self):
        """The guard runs isolated (-I): `-c` alone would put the project folder first on sys.path."""
        d = self.hooks_dir("codex")
        project = self.tmp / "project"
        project.mkdir()
        (project / "json.py").write_text("raise SystemExit('planted json.py ran')\n")
        (entry,) = entries(windows("codex", str(d)))
        self.assertIn(" -I -c ", entry["commandWindows"])
        for result in self.run_line(runnable(entry, "codex")[0], RISKY, cwd=project):
            self.assertNotIn("planted", result.stderr)
            self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_cursor_and_antigravity_print_their_allow_when_the_guard_is_gone(self):
        for harness, allow in (("cursor", {"permission": "allow"}), ("antigravity", {"decision": "allow"})):
            d = self.hooks_dir(harness)
            sources = [s for e in entries(windows(harness, str(d))) for s in runnable(e, harness)]
            for result in self.run_line(sources[0], CURSOR_RISKY):
                self.assertEqual(result.returncode, 0, result.stderr)
            rmtree(d)
            for source in sources:
                for result in self.run_line(source, CURSOR_RISKY):
                    self.assertEqual((result.returncode, json.loads(result.stdout)), (0, allow), harness)

    def test_claude_exec_form_runs_without_a_shell(self):
        d = self.hooks_dir("claude")
        for entry in entries(windows("claude", str(d))):
            if "guard_outward" not in json.dumps(entry):
                continue
            result = subprocess.run([sys.executable, *entry["args"][-2:]], input=json.dumps(RISKY),
                                    capture_output=True, text=True, timeout=60)
            self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "ask")

    def test_the_program_is_quoted_only_when_it_must_be(self):
        with mock.patch.object(shutil, "which", return_value=None):
            self.assertTrue(hookcmd.line("C:/Python312/python.exe", [], "x", "cmd").startswith("C:/Python312/python.exe -c"))
            spaced = "C:/Program Files/Python312/python.exe"
            self.assertTrue(hookcmd.line(spaced, [], "x", "powershell").startswith(f'& "{spaced}" -c'))
            self.assertTrue(hookcmd.line(spaced, [], "x", "cmd").startswith(f'call "{spaced}" -c'))
            with self.assertRaisesRegex(ConfigError, "py launcher"):  # no quoting fits every shell
                hookcmd.line(spaced, [], "x", None)
            with self.assertRaisesRegex(ConfigError, "py launcher"):
                hookcmd.line("C:/Users/50%off/python.exe", [], "x", "cmd")
        with mock.patch.object(shutil, "which", side_effect=lambda n: "C:/Windows/py.exe" if n == "py" else None):
            self.assertEqual(hookcmd.line("C:/Windows/py.exe", ["-3"], "x", None), 'py -3 -c "x"')

    def test_python_skips_the_store_stub_and_an_old_python(self):
        hookcmd.python.cache_clear()
        self.addCleanup(hookcmd.python.cache_clear)
        where = {"py": "C:/Windows/py.exe", "python": "C:/Users/acme/AppData/Local/Microsoft/WindowsApps/python.exe"}
        with mock.patch.object(shutil, "which", side_effect=where.get), \
                mock.patch.object(hookcmd, "_usable", side_effect=lambda exe, args: False) as usable:
            self.assertEqual(hookcmd.python(), (sys.executable, []))  # py -3 is too old, python the stub
        self.assertEqual(usable.call_count, 2)
        self.assertFalse(hookcmd._usable(where["python"], []))
        self.assertTrue(hookcmd._usable(sys.executable, []))

    def test_a_payload_that_is_not_ascii_is_read_as_utf8(self):
        """-I ignores PYTHONUTF8, so -X utf8 makes the guard read stdin as UTF-8 on any code page."""
        d = self.hooks_dir("claude")
        (entry,) = [e for e in entries(windows("claude", str(d))) if "guard_outward" in json.dumps(e)]
        self.assertEqual(entry["args"][-5:-2], ["-X", "utf8", "-I"])
        payload = dict(RISKY, cwd="/tmp/Łódź")
        env = dict(os.environ, PYTHONIOENCODING="cp1252")  # ignored under -I, as it is on Windows
        result = subprocess.run([sys.executable, *entry["args"][-5:]], input=json.dumps(payload, ensure_ascii=False).encode(),
                                capture_output=True, timeout=60, env=env)
        self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "ask", result.stderr)

    def test_a_hook_under_home_is_written_home_relative(self):
        """As the POSIX line's $HOME: one lock gives every machine the same settings file."""
        (entry,) = entries(windows("codex", "~/.codex/hooks/brainrc"))
        self.assertIn("f=os.path.expanduser('~/.codex/hooks/brainrc/guard.py')", entry["commandWindows"])
        self.assertNotIn(os.path.expanduser("~").replace("\\", "/"), entry["commandWindows"])

    def test_a_path_a_shell_would_read_is_refused(self):
        with self.assertRaisesRegex(ConfigError, "hooks_dir in harnesses.local.toml"):
            hookcmd.native_path("C:/Users/50%off/.codex/hooks/brainrc/guard.py")

    def test_a_pack_command_in_another_form_is_left_alone(self):
        self.assertIsNone(hookcmd.parse('node "$HOME/.codex/hooks/brainrc-acme/check.js"'))
        path, fallback, only_if_present = hookcmd.parse('python3 "$HOME/.codex/hooks/brainrc-acme/guard_acme.py"')
        self.assertEqual((fallback, only_if_present), (None, False))

    def test_a_merge_recognises_its_own_windows_hooks(self):
        """A second apply replaces brainrc's Windows groups, not adds to them, for every format."""
        for harness in HOOKED:
            m = SettingsMerge(harness, Path("unused.json"),
                              [(REPO / "overrides" / harness / "settings.fragment.json", "~/.x/hooks/brainrc")])
            with mock.patch.object(hookcmd, "windows_hooks", return_value=True):
                once = merge_settings({}, m.wanted(), m.markers())
                twice = merge_settings(once, m.wanted(), m.markers())
            self.assertEqual(once, twice, harness)


class WindowsApplyTest(TempRepoCase):
    """apply, status and uninstall with the Windows form, end to end."""

    def setUp(self):
        super().setUp()
        self.home = Path(tempfile.mkdtemp()).resolve()
        self.old_home = saved_home()
        os.environ.update(home_env(self.home))
        install_harnesses(self.home)
        patcher = mock.patch.object(hookcmd, "windows_hooks", return_value=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        restore_home(self.old_home)
        rmtree(self.home)
        super().tearDown()

    def test_apply_is_in_sync_after_and_uninstall_removes_the_hooks(self):
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertEqual(quiet(brainrc.cmd_sync, False), (0, "Everything in sync.\n"))
        codex = json.loads((self.home / ".codex/hooks.json").read_text())
        (entry,) = codex["hooks"]["PreToolUse"][0]["hooks"]
        self.assertIn("/.codex/hooks/brainrc/guard.py", entry["commandWindows"])
        findings = [f for f in brainrc.doctor_findings() if "hook" in f[1] and f[0] == "FAIL"]
        self.assertEqual(findings, [])
        hooks = [(tool, e["name"]) for tool, found in audit.collect()["tools"].items() for e in found
                 if e["kind"] == "hook"]
        self.assertTrue(hooks)
        installed = {(tool, e["name"]) for tool, found in audit.collect()["tools"].items() for e in found
                     if e["kind"] == "hook" and e["installed"]}
        self.assertEqual([h for h in hooks if h not in installed], [])
        # cmd and PowerShell set no HOME: doctor reads the Windows line, not Codex's POSIX `command`.
        with mock.patch.dict(os.environ, {"HOME": "/nowhere"}):
            with mock.patch.object(os.path, "expanduser", lambda p: str(self.home) + p[1:] if p.startswith("~") else p):
                findings = [f for f in brainrc.doctor_findings() if "hook" in f[1] and f[0] == "FAIL"]
        self.assertEqual(findings, [])
        code, out = quiet(brainrc.uninstall.cmd_uninstall)
        self.assertEqual(code, 0, out)
        self.assertFalse((self.home / ".codex/hooks.json").exists())


if __name__ == "__main__":
    unittest.main()
