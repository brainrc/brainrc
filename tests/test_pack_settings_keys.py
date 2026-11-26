"""Packs own the permission entries their settings fragment adds (#142): tracked per settings file,
and removed, exactly those, when the pack is disabled or brainrc is uninstalled."""
import json
import unittest

import brainrc
from brainrc.settings import merge_settings, owned_permissions

from support import home_env, restore_home, saved_home
from test_brainrc import TempRepoCase, install_harnesses, quiet

ACME_PERMS = {"allow": ["Bash(acme-status:*)", "Bash(ls:*)"], "deny": ["Bash(acme-deploy prod:*)"]}


class MergePermissionsTest(unittest.TestCase):
    def test_adds_and_takes_out_only_what_it_owns(self):
        user = {"permissions": {"allow": ["Read", "Bash(ls:*)"], "defaultMode": "plan"}}
        frag = {"permissions": ACME_PERMS}
        merged = merge_settings(user, frag)
        self.assertEqual(merged["permissions"]["allow"], ["Read", "Bash(ls:*)", "Bash(acme-status:*)"])
        self.assertEqual(merged["permissions"]["deny"], ["Bash(acme-deploy prod:*)"])
        owned = owned_permissions(user, frag, {})
        self.assertEqual(owned, {"allow": ["Bash(acme-status:*)"], "deny": ["Bash(acme-deploy prod:*)"]})
        self.assertEqual(merge_settings(merged, frag, owned=owned), merged)  # idempotent
        self.assertEqual(merge_settings(merged, {}, owned=owned), user)  # the pack is gone

    def test_an_entry_it_owns_stays_owned_and_a_users_own_empty_list_stays(self):
        frag = {"permissions": {"allow": ["Bash(acme-status:*)"]}}
        once = merge_settings({}, frag)
        owned = owned_permissions({}, frag, {})
        self.assertEqual(owned_permissions(once, frag, owned), owned)
        self.assertEqual(merge_settings(once, {}, owned=owned), {})
        self.assertEqual(merge_settings({"permissions": {"allow": []}}, {}, owned=owned), {"permissions": {"allow": []}})

    def test_a_value_that_is_not_an_object_or_list_is_left_alone(self):
        frag = {"permissions": {"allow": ["Bash(x)"]}}
        self.assertEqual(merge_settings({"permissions": "odd"}, frag)["permissions"], "odd")
        self.assertEqual(merge_settings({"permissions": {"allow": "odd"}}, frag)["permissions"]["allow"], "odd")
        self.assertEqual(merge_settings({"permissions": "odd"}, {})["permissions"], "odd")


class WantedPermissionsTest(TempRepoCase):
    def test_a_string_where_a_list_belongs_is_skipped_not_split(self):
        from brainrc.plan import SettingsMerge
        frags = []
        for name, perms in (("a", {"allow": "Bash(x)"}), ("b", {"allow": ["Read"]})):
            f = self.repo / f"{name}.json"
            f.write_text(json.dumps({"permissions": perms}))
            frags.append((f, None))
        wanted = SettingsMerge("claude", self.repo / "settings.json", frags).wanted()
        self.assertEqual(wanted["permissions"]["allow"], ["Read"])


class DisablePackTest(TempRepoCase):
    """Done when: disabling a pack removes exactly the permissions it added."""

    def setUp(self):
        super().setUp()
        self.old_home = saved_home()
        self.home = self.settings_home.parent / "home"
        self.home.mkdir()
        restore_home(home_env(self.home))
        install_harnesses(self.home)
        brainrc.permissions.ASSUME_YES = True
        for name, perms in (("acme", ACME_PERMS), ("ops", {"allow": ["Bash(acme-status:*)"]})):
            pack = self.repo / "packs" / name
            (pack / "overrides/claude").mkdir(parents=True)
            (pack / "pack.toml").write_text(f'name = "{name}"\nrequires_core = ">=0"\n')
            (pack / "overrides/claude/settings.fragment.json").write_text(json.dumps({"permissions": perms}))
        self.settings = self.home / ".claude/settings.json"
        self.settings.write_text(json.dumps({"permissions": {"allow": ["Read", "Bash(ls:*)"]}, "model": "opus"}))

    def tearDown(self):
        brainrc.permissions.ASSUME_YES = False
        restore_home(self.old_home)
        super().tearDown()

    def enable(self, acme: bool = True, ops: bool = False) -> None:
        (self.repo / "packs.local.toml").write_text(
            f'[acme]\npath = "packs/acme"\nenabled = {str(acme).lower()}\n'
            f'[ops]\npath = "packs/ops"\nenabled = {str(ops).lower()}\n')
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)

    def perms(self) -> dict:
        return json.loads(self.settings.read_text()).get("permissions")

    def test_disabling_removes_exactly_what_it_added(self):
        self.enable()
        self.assertEqual(self.perms(), {"allow": ["Read", "Bash(ls:*)", "Bash(acme-status:*)"],
                                        "deny": ["Bash(acme-deploy prod:*)"]})
        code, out = quiet(brainrc.cmd_sync, False)
        self.assertIn("Everything in sync", out)
        self.enable(acme=False)
        self.assertEqual(self.perms(), {"allow": ["Read", "Bash(ls:*)"]})  # ls was the user's first
        self.assertEqual(json.loads(self.settings.read_text())["model"], "opus")
        self.assertFalse((self.settings_home / "settings-owned.json").exists())

    def test_an_entry_another_pack_still_wants_stays(self):
        self.enable(acme=True, ops=True)
        self.enable(acme=False, ops=True)
        self.assertEqual(self.perms(), {"allow": ["Read", "Bash(ls:*)", "Bash(acme-status:*)"]})
        self.enable(acme=False, ops=False)
        self.assertEqual(self.perms(), {"allow": ["Read", "Bash(ls:*)"]})

    def test_uninstall_takes_them_out_too(self):
        self.enable()
        code, out = quiet(brainrc.uninstall.cmd_uninstall)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.perms(), {"allow": ["Read", "Bash(ls:*)"]})


class SandboxTest(TempRepoCase):
    """#322: a pack's path and host guard rules land in Claude Code's sandbox lists, owned like
    permission entries: the user's own stay, and exactly the pack's go when it does."""

    def setUp(self):
        super().setUp()
        self.old_home = saved_home()
        self.home = self.settings_home.parent / "home"
        self.home.mkdir()
        restore_home(home_env(self.home))
        install_harnesses(self.home)
        brainrc.permissions.ASSUME_YES = True
        pack = self.repo / "packs/acme"
        pack.mkdir(parents=True)
        (pack / "pack.toml").write_text(
            'name = "acme"\nrequires_core = ">=0"\n'
            '[[guard.deny]]\npath = "~/.acme/credentials"\nreason = "acme keys"\n'
            '[[guard.deny]]\nhost = "*.acme.example"\nreason = "acme internal"\n')
        self.settings = self.home / ".claude/settings.json"
        self.settings.write_text(json.dumps({"sandbox": {"enabled": True, "filesystem": {"denyRead": ["~/.ssh"]}}}))

    def tearDown(self):
        brainrc.permissions.ASSUME_YES = False
        restore_home(self.old_home)
        super().tearDown()

    def enable(self, on: bool) -> None:
        (self.repo / "packs.local.toml").write_text(f'[acme]\npath = "packs/acme"\nenabled = {str(on).lower()}\n')
        code, out = quiet(brainrc.cmd_sync, True)
        self.assertEqual(code, 0, out)

    def box(self) -> dict:
        return json.loads(self.settings.read_text()).get("sandbox")

    def test_apply_adds_them_keeps_the_users_and_disabling_takes_them_out(self):
        self.enable(True)
        self.assertEqual(self.box(), {"enabled": True,
                                      "filesystem": {"denyRead": ["~/.ssh", "~/.acme/credentials"],
                                                     "denyWrite": ["~/.acme/credentials"]},
                                      "network": {"deniedDomains": ["*.acme.example"]}})
        code, out = quiet(brainrc.cmd_sync, False)
        self.assertIn("Everything in sync", out)
        self.enable(False)
        self.assertEqual(self.box(), {"enabled": True, "filesystem": {"denyRead": ["~/.ssh"]}})
        self.assertFalse((self.settings_home / "settings-owned.json").exists())

    def test_an_entry_the_user_had_first_stays_theirs(self):
        self.settings.write_text(json.dumps({"sandbox": {"network": {"deniedDomains": ["*.acme.example"]}}}))
        self.enable(True)
        self.enable(False)
        self.assertEqual(self.box(), {"network": {"deniedDomains": ["*.acme.example"]}})

    def test_uninstall_takes_them_out_too(self):
        self.enable(True)
        code, out = quiet(brainrc.uninstall.cmd_uninstall)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.box(), {"enabled": True, "filesystem": {"denyRead": ["~/.ssh"]}})

    def test_merge_leaves_a_sandbox_that_is_not_an_object_alone(self):
        frag = {"sandbox": {"network": {"deniedDomains": ["acme.example"]}}}
        self.assertEqual(merge_settings({"sandbox": "odd"}, frag)["sandbox"], "odd")
        self.assertEqual(merge_settings({"sandbox": {"network": "odd"}}, frag)["sandbox"]["network"], "odd")
        owned = owned_permissions({}, frag, {})
        self.assertEqual(owned, {"sandbox.network.deniedDomains": ["acme.example"]})
        self.assertEqual(merge_settings(merge_settings({}, frag), {}, owned=owned), {})


if __name__ == "__main__":
    unittest.main()
