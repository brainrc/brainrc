"""Pack naming rules (gh:294, docs/packs.md § Naming): each rejection with a near miss that passes."""
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import TempRepoCase, brainrc, quiet  # noqa: E402
from brainrc import naming  # noqa: E402
from brainrc.sources import Source  # noqa: E402
from support import rmtree

ROOT = Path(__file__).resolve().parent.parent


class NamingCase(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(rmtree, self.root)

    def errors(self, name="acme", prefix=None, pack_id=None):
        meta = {"name": name} | ({"id": pack_id} if pack_id is not None else {})
        return naming.check_pack_names(Source(name, self.root, prefix or f"{name}-", meta))

    def assert_refused(self, needle, **kw):
        errors = self.errors(**kw)
        self.assertTrue(any(needle in e for e in errors), f"{needle!r} not in {errors}")

    def assert_passes(self, **kw):
        self.assertEqual(self.errors(**kw), [])


class ReservedTest(NamingCase):
    """Rule 1: `brainrc-` and `brainrc/` are reserved for official packs."""

    def test_reserved_prefix_name_and_id_are_refused(self):
        self.assert_refused("reserved for official packs", name="tools", prefix="brainrc-")
        self.assert_refused("reserved for official packs", name="brainrc-tools", prefix="tools-")
        self.assert_refused("reserved for official packs", name="brainrc", prefix="tools-")
        self.assert_refused("reserved for official packs", name="extra", prefix="brainrc-", pack_id="brainrc/extra")

    def test_near_miss_passes(self):
        self.assert_passes(name="acme", prefix="acme-brainrc-")
        self.assert_passes(name="tools", prefix="jdoe-", pack_id="jdoe/brainrc-tools")

    def test_an_official_pack_may_use_them(self):
        self.assert_passes(name="terraform-aws", prefix="brainrc-", pack_id="brainrc/terraform-aws")


class OwnerPrefixTest(NamingCase):
    """Rule 2: a registry prefix starts with the owner's handle."""

    def test_prefix_without_the_owner_handle_is_refused(self):
        self.assert_refused("must start with the owner handle `jdoe-`", name="k8s", prefix="k8s-", pack_id="jdoe/k8s")
        self.assert_refused("owner handle", name="k8s", prefix="jdoex-", pack_id="jdoe/k8s")

    def test_near_miss_passes(self):
        self.assert_passes(name="k8s", prefix="jdoe-", pack_id="jdoe/k8s")
        self.assert_passes(name="k8s", prefix="jdoe-k8s-", pack_id="jdoe/k8s")

    def test_a_malformed_id_is_refused(self):
        for bad in ("jdoe", "jdoe/k8s/x", "JDoe/k8s", 7):
            with self.subTest(pack_id=bad):
                self.assert_refused("`id` must be `<owner>/<pack>`", name="k8s", prefix="jdoe-", pack_id=bad)


class VendorTest(NamingCase):
    """Rule 3: no vendor names without verification."""

    def test_vendor_names_are_refused(self):
        self.assert_refused("vendor name `aws`", name="aws-tools")
        self.assert_refused("vendor name `github`", name="sync", prefix="jdoe-", pack_id="jdoe/github-sync")
        self.assert_refused("vendor name `openai`", name="helpers", prefix="openai-")

    def test_near_miss_passes(self):
        self.assert_passes(name="awsome")
        self.assert_passes(name="sync", prefix="jdoe-", pack_id="jdoe/githubby-sync")

    def test_a_verified_vendor_may_use_its_own_name(self):
        with mock.patch.dict(naming.VERIFIED_VENDORS, {"hashicorp": frozenset({"hashicorp"})}):
            self.assert_passes(name="hashicorp", prefix="hashicorp-", pack_id="hashicorp/hashicorp")
            self.assert_refused("vendor name `hashicorp`", name="hashicorp", prefix="jdoe-hashicorp-",
                                pack_id="jdoe/hashicorp")


class LookalikeTest(NamingCase):
    """Rule 4: no names one or two edits from an official name."""

    def test_one_or_two_edits_from_brainrc_are_refused(self):
        for name in ("brainrx", "brianrc", "brain", "brainrcc", "brainrx-tools"):
            with self.subTest(name=name):
                self.assert_refused("edits from the official name `brainrc`", name=name)
        self.assert_refused("`brainrd` is one or two edits", name="go", prefix="brainrd-", pack_id="brainrd/go")

    def test_one_or_two_edits_from_an_official_id_are_refused(self):
        self.assert_refused("official pack `brainrc/go`", name="go", prefix="brainrd-", pack_id="brainrd/go")

    def test_near_miss_passes(self):
        for name in ("bran", "brainstorm", "acme"):
            with self.subTest(name=name):
                self.assert_passes(name=name)
        self.assert_passes(name="go", prefix="jdoe-", pack_id="jdoe/go")

    def test_edit_distance(self):
        self.assertEqual(naming.edits("brainrc", "brainrc"), 0)
        self.assertEqual(naming.edits("brianrc", "brainrc"), 1)  # a swap is one edit
        self.assertEqual(naming.edits("brain", "brainrc"), 2)
        self.assertEqual(naming.edits("bran", "brainrc"), 3)


class CharsetTest(NamingCase):
    """Rule 5: ASCII lowercase letters, digits and hyphens only."""

    def test_non_ascii_and_uppercase_names_are_refused(self):
        self.assert_refused("`name` must be ASCII", name="acmé", prefix="acme-")
        self.assert_refused("`prefix` must be ASCII", name="acme", prefix="acmé-")
        self.assert_refused("`prefix` must be ASCII", name="acme", prefix="Acme-")
        self.assert_refused("`prefix` must be ASCII", name="acme", prefix="acme_")

    def test_near_miss_passes(self):
        self.assert_passes(name="acme2", prefix="acme2-")

    def test_items_and_servers_are_checked(self):
        (self.root / "agents").mkdir()
        (self.root / "agents/acme-reviewér.md").write_text("---\nname: acme-reviewér\n---\n")
        (self.root / "agents/acme-reviewer2.md").write_text("---\nname: acme-reviewer2\n---\n")
        (self.root / "mcp").mkdir()
        (self.root / "mcp/servers.toml").write_text('[servers.acme_docs]\ncommand = "x"\n'
                                                    '[servers.acme-docs]\ncommand = "x"\n')
        errors = self.errors()
        self.assertEqual(len(errors), 2, errors)
        self.assertIn("acme:agents/acme-reviewér.md: name must be ASCII", errors[0])
        self.assertIn("server `acme_docs`", errors[1])


class PrefixLengthTest(NamingCase):
    """Rule 6: a prefix is 2 to 24 characters before its hyphen."""

    def test_too_short_or_long_is_refused(self):
        self.assert_refused("2 to 24 characters", name="acme", prefix="a-")
        self.assert_refused("2 to 24 characters", name="acme", prefix="a" * 25 + "-")

    def test_near_miss_passes(self):
        self.assert_passes(name="acme", prefix="ab-")
        self.assert_passes(name="acme", prefix="a" * 24 + "-")


class ValidateTest(TempRepoCase):
    """Rules 1 to 7 through `validate --pack`, and the shipped tree (core from a temp copy, so no local config)."""

    def setUp(self):
        super().setUp()
        self.pack = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(rmtree, self.pack)
        shutil.copytree(ROOT / "examples/pack-acme", self.pack, dirs_exist_ok=True)

    def validate(self):
        return quiet(brainrc.cmd_validate, str(self.pack))

    def test_examples_pass(self):
        for pack in ("pack-acme", "pack-homelab"):
            with self.subTest(pack=pack):
                code, out = quiet(brainrc.cmd_validate, str(ROOT / "examples" / pack))
                self.assertEqual(code, 0, out)

    def test_a_reserved_prefix_fails_validate(self):
        toml = self.pack / "pack.toml"
        toml.write_text(toml.read_text().replace('prefix = "acme-"', 'prefix = "brainrc-"'))
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("reserved for official packs", out)
        self.assertIn("pack skills must start with `brainrc-`", out)  # rule 7

    def test_docs_list_the_same_official_ids(self):
        text = (ROOT / "docs/packs.md").read_text()
        section = text.split("## Naming", 1)[1].split("\n## ", 1)[0]
        self.assertEqual(set(re.findall(r"^\| `(brainrc/[a-z0-9-]+)` \|", section, re.M)), naming.OFFICIAL_PACK_IDS)
        self.assertEqual(len(re.findall(r"^\d\. \*\*", section, re.M)), 7)


if __name__ == "__main__":
    unittest.main()
