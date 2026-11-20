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
        self.assertIn("guard.deny[0]: set `match` (a command) or `tool`", text)
        self.assertIn("guard.deny[1]: set `match`", text)
        self.assertIn("guard.ask[0]: `match` can't be split", text)
        self.assertIn("guard.ask[1]: `tool` must start with mcp__", text)
        self.assertTrue(any("guard.ask[2]" in e and "reason" in e for e in errors), errors)
        self.assertTrue(any("guard.block" in w for w in warnings), warnings)
        self.assertEqual(guard.rules([src]), [])  # every one is malformed, so none is enforced

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
