"""brainrc.local.toml's [extensions.<namespace>] (#144): this machine's settings for the pack that
owns the namespace, checked by its validator and rendered after every pack's."""
import contextlib
import io
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import REPO, TempRepoCase  # noqa: E402

from brainrc.cli import cmd_sync  # noqa: E402
from brainrc.config import ConfigError, check_config, machine_extensions, tilde  # noqa: E402
from brainrc.plugins import machine_findings, render_extensions  # noqa: E402
from brainrc.sources import Source, load_pack  # noqa: E402

ACME = REPO / "examples/pack-acme"


class MachineExtensionsTest(TempRepoCase):
    def setUp(self):
        super().setUp()
        shutil.copytree(ACME, self.repo / "packs/acme")
        self.srcs = [Source("core", self.repo), load_pack(self.repo / "packs/gatework", "gatework"),
                     load_pack(self.repo / "packs/acme", "acme")]

    def local(self, text: str):
        (self.repo / "brainrc.local.toml").write_text(text)

    def test_rendered_after_every_pack(self):
        self.local('profile = "full"\n\n[extensions.gatework]\ndeliver_checks = ["Load test signed off"]\n')
        text = render_extensions(self.srcs)
        self.assertIn("## This machine", text)
        self.assertIn('"Load test signed off"', text)
        self.assertGreater(text.index("## This machine"), text.index("Deploy plan reviewed by the owning team"))
        self.assertEqual(machine_findings(self.srcs), ([], []))
        self.assertEqual(check_config(), [])  # `extensions` is a known key

    def test_none_without_a_table(self):
        self.local('profile = "full"\n')
        self.assertNotIn("## This machine", render_extensions(self.srcs))

    def test_the_owning_pack_checks_it(self):
        self.local('[extensions.gatework]\nmodee = "inline"\n')
        errors, _ = machine_findings(self.srcs)
        self.assertTrue(any("brainrc.local.toml: unknown extension `modee`" in e for e in errors), errors)

    def test_a_namespace_no_pack_reads_warns(self):
        self.local('[extensions.gatewrok]\ndeliver_checks = ["x"]\n')
        self.assertEqual(machine_findings(self.srcs)[1],
                         [f"{tilde(self.repo / 'brainrc.local.toml')}: no enabled pack reads [extensions.gatewrok]"])

    def test_a_value_that_is_not_a_table_fails_with_its_line(self):
        self.local('profile = "full"\n[extensions]\ngatework = "inline"\n')
        with self.assertRaises(ConfigError) as e:
            machine_extensions()
        self.assertIn("brainrc.local.toml:3: `extensions.gatework` must be a table", str(e.exception))

    def test_a_date_renders_as_text(self):
        self.local('[extensions.gatework]\ndeliver_checks = [2026-01-01]\n')
        self.assertIn('"2026-01-01"', render_extensions(self.srcs))

    def test_an_older_namespace_is_read_with_a_warning(self):
        self.local('[extensions.spec-agent]\ndeliver_checks = ["Load test signed off"]\n')
        self.assertIn('"Load test signed off"', render_extensions(self.srcs))
        errors, warnings = machine_findings(self.srcs)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [f"{tilde(self.repo / 'brainrc.local.toml')}: [extensions.spec-agent] is "
                                    "deprecated; move it under [extensions.gatework] (read until 0.8.0)"])

    def test_doctor_names_the_file_to_fix(self):
        from brainrc.doctor import doctor_findings
        self.local('[extensions]\ngatework = "inline"\n')
        found = [f for f in doctor_findings() if "must be a table" in f[1]]
        self.assertTrue(found, doctor_findings())
        self.assertEqual(found[0][2], "fix [extensions] in the file named")

    def test_apply_stops_on_an_error_and_writes_nothing(self):
        self.local('[extensions.gatework]\nmodee = "inline"\n')
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cmd_sync(True)
        self.assertEqual(code, 1, buf.getvalue())
        self.assertIn("unknown extension `modee`", buf.getvalue())
        self.assertFalse((self.settings_home / "extensions.md").exists())


if __name__ == "__main__":
    unittest.main()
