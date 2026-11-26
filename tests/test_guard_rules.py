"""Declarative guard rules in pack.toml (#141): validate, the render apply writes, and its pruning."""
import json
import shutil
import unittest

from brainrc import guard
from brainrc.sources import Source, load_pack
from brainrc.validate import pack_toml_findings

from test_brainrc import REPO, TempRepoCase, install_harnesses, quiet
from support import home_env, restore_home, saved_home
import brainrc

ACME = REPO / "examples/pack-acme"


class GuardRulesTest(TempRepoCase):
    def pack(self, toml: str) -> Source:
        root = self.repo / "packs/acme"
        root.mkdir(parents=True, exist_ok=True)
        (root / "pack.toml").write_text('name = "acme"\nrequires_core = ">=0"\n' + toml)
        return load_pack(root, "acme")

    def test_the_acme_rules_render_with_the_packs_scope(self):
        rules = json.loads(guard.render([Source("core", self.repo), load_pack(ACME, "acme")]))["rules"]
        deny = next(r for r in rules if r["action"] == "deny")
        self.assertEqual(deny["match"], ["acme-deploy", "prod"])
        self.assertEqual(deny["pack"], "acme")
        self.assertIn("github.com/acme/*", deny["scope"]["remotes"])
        ask = next(r for r in rules if r["action"] == "ask")
        self.assertEqual(ask["tool"], "mcp__acme-jira__*transition*")
        self.assertIsNone(ask["match"])

    def test_a_rule_scope_replaces_the_packs(self):
        src = self.pack('[scope]\nremotes = ["github.com/acme/*"]\n[[guard.ask]]\nmatch = "acme-db drop"\n'
                        'reason = "drops a database"\nscope = { kube_contexts = ["acme-*"] }\n')
        self.assertEqual(guard.rules([src])[0]["scope"], {"kube_contexts": ["acme-*"]})

    def test_no_rules_render_nothing(self):
        self.assertIsNone(guard.render([Source("core", self.repo), self.pack("")]))

    def test_validate_names_each_bad_rule(self):
        src = self.pack('[[guard.deny]]\nreason = "neither"\n'
                        '[[guard.deny]]\nmatch = "x"\ntool = "mcp__a__b"\nreason = "both"\n'
                        '[[guard.ask]]\nmatch = "acme \'unclosed"\nreason = "bad quote"\n'
                        '[[guard.ask]]\ntool = "acme_delete"\nreason = "no mcp__"\n'
                        '[[guard.ask]]\nmatch = "acme-x"\n'
                        '[[guard.block]]\nmatch = "acme-x"\nreason = "unknown action"\n')
        errors, warnings = pack_toml_findings(src)
        text = "\n".join(errors)
        self.assertIn("guard.deny[0]: set `match` (a command), `tool`", text)
        self.assertIn("guard.deny[1]: set `match`", text)
        self.assertIn("guard.ask[0]: `match` can't be split", text)
        self.assertIn("guard.ask[1]: `tool` must be a string that starts with mcp__", text)
        self.assertTrue(any("guard.ask[2]" in e and "reason" in e for e in errors), errors)
        self.assertTrue(any("guard.block" in w for w in warnings), warnings)
        self.assertEqual(guard.rules([src]), [])  # every one is malformed, so none is enforced

    def test_a_match_that_is_not_a_string_fails_validate_and_never_crashes_a_render(self):
        src = self.pack('[[guard.deny]]\nmatch = ["acme-deploy", "prod"]\nreason = "r"\n'
                        '[[guard.deny]]\ntool = 3\nreason = "r"\n')
        errors, _ = pack_toml_findings(src)
        self.assertTrue(any("guard.deny[0]: `match` must be a string" in e for e in errors), errors)
        self.assertTrue(any("guard.deny[1]: `tool` must be a string" in e for e in errors), errors)
        self.assertIsNone(guard.render([src]))

    def test_a_path_or_a_wrapper_as_the_program_fails_validate(self):
        src = self.pack('[[guard.deny]]\nmatch = "./scripts/deploy.sh prod"\nreason = "r"\n'
                        '[[guard.deny]]\nmatch = "sudo reboot"\nreason = "r"\n')
        text = "\n".join(pack_toml_findings(src)[0])
        self.assertIn("guard.deny[0]: `match` must name the program alone (`deploy.sh`)", text)
        self.assertIn("guard.deny[1]: `match` starts with `sudo`", text)

    def test_the_wrappers_are_the_hooks(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("go", REPO / "overrides/claude/hooks/guard_outward.py")
        hook = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hook)
        self.assertEqual(set(hook.WRAPPERS), set(guard.WRAPPERS))

    def test_path_and_host_rules_compile_to_the_claude_sandbox(self):
        src = self.pack('[scope]\nremotes = ["github.com/acme/*"]\n'
                        '[[guard.deny]]\npath = "~/.acme/credentials"\nreason = "acme keys"\nscope = {}\n'
                        '[[guard.deny]]\nhost = "*.acme.example"\nreason = "acme internal"\nscope = {}\n'
                        '[[guard.deny]]\nmatch = "acme-deploy prod"\nreason = "prod"\n')
        self.assertEqual(pack_toml_findings(src), ([], []))
        self.assertEqual(guard.sandbox([Source("core", self.repo), src], "claude"), {
            "filesystem": {"denyRead": ["~/.acme/credentials"], "denyWrite": ["~/.acme/credentials"]},
            "network": {"deniedDomains": ["*.acme.example"]}})
        self.assertEqual(guard.sandbox([src], "cursor"), {})  # no sandbox there
        self.assertEqual([r["match"] for r in guard.rules([src])], [["acme-deploy", "prod"]])  # hooks skip them

    def test_bad_path_and_host_rules_fail_validate_and_compile_to_nothing(self):
        src = self.pack('[scope]\nremotes = ["github.com/acme/*"]\n'
                        '[[guard.ask]]\npath = "~/.acme"\nreason = "r"\nscope = {}\n'
                        '[[guard.deny]]\npath = "relative/dir"\nreason = "r"\nscope = {}\n'
                        '[[guard.deny]]\nhost = "https://acme.example/x"\nreason = "r"\nscope = {}\n'
                        '[[guard.deny]]\npath = "~/.acme"\nreason = "the pack\'s scope can\'t hold"\n')
        text = "\n".join(pack_toml_findings(src)[0])
        self.assertIn("guard.ask[0]: a `path` rule goes under [[guard.deny]]", text)
        self.assertIn("guard.deny[0]: `path` must be a string that starts with ~/ or /", text)
        self.assertIn("guard.deny[1]: `host` must be a domain name", text)
        self.assertIn("guard.deny[2]: a `path` rule compiles to sandbox settings", text)
        trailing = self.pack('[[guard.deny]]\nhost = """acme.example\n"""\nreason = "r"\n')
        self.assertTrue(any("`host` must be a domain" in e for e in pack_toml_findings(trailing)[0]))
        self.assertEqual(guard.sandbox([src], "claude"), {})

    def test_an_unscoped_pack_needs_no_scope_on_its_sandbox_rules(self):
        src = self.pack('[[guard.deny]]\nhost = "acme.example"\nreason = "r"\n')
        self.assertEqual(pack_toml_findings(src), ([], []))
        self.assertEqual(guard.sandbox([src], "claude"), {"network": {"deniedDomains": ["acme.example"]}})

    def test_good_rules_pass_validate(self):
        errors, warnings = pack_toml_findings(load_pack(ACME, "acme"))
        self.assertEqual((errors, warnings), ([], []))


class ApplyGuardRulesTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        self.old_home = saved_home()
        self.home = self.settings_home.parent / "home"
        self.home.mkdir()
        restore_home(home_env(self.home))
        install_harnesses(self.home)
        shutil.copytree(ACME, self.repo / "packs/acme")
        brainrc.permissions.ASSUME_YES = True

    def tearDown(self):
        brainrc.permissions.ASSUME_YES = False
        restore_home(self.old_home)
        super().tearDown()

    def test_apply_writes_the_rules_and_prunes_them_when_the_pack_goes(self):
        rules = self.settings_home / "guard-rules.json"
        (self.repo / "packs.local.toml").write_text('[acme]\npath = "packs/acme"\n')
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertIn("acme-deploy", rules.read_text())
        code, out = quiet(brainrc.cmd_sync, False)
        self.assertNotIn("guard-rules.json", out)  # in sync
        (self.repo / "packs.local.toml").write_text('[acme]\npath = "packs/acme"\nenabled = false\n')
        code, out = quiet(brainrc.cmd_sync, False)
        self.assertIn("PRUNE", out)
        self.assertIn("guard-rules.json", out)
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)
        self.assertFalse(rules.exists())


if __name__ == "__main__":
    unittest.main()
