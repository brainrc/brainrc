import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brainrc.config import BACKUPS_KEPT
from brainrc.settings import replace_file


class BackupTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name).resolve()
        self.target = self.dir / "settings.json"
        self.target.write_text("{}")

    def names(self):
        return sorted(p.name for p in self.dir.glob("settings.json.bak-*"))

    def test_new_backup_uses_brainrc_name(self):
        replace_file(self.target, '{"a": 1}', "{}")
        names = self.names()
        self.assertEqual(len(names), 1)
        self.assertRegex(names[0], r"^settings\.json\.bak-brainrc-\d{8}T\d{6}Z$")

    def test_prune_spans_both_names_by_timestamp(self):
        # Interleaved names: prefix order and timestamp order disagree.
        old = [f"settings.json.bak-{p}-2026010{n}T000000Z" for n, p in enumerate(
            ["brainrc", "aicfg", "brainrc", "aicfg", "brainrc", "aicfg", "brainrc"])]
        for name in old:
            (self.dir / name).write_text("{}")
        replace_file(self.target, '{"a": 1}', "{}")
        names = self.names()
        self.assertEqual(len(names), BACKUPS_KEPT)
        # the newest seeded ones survive, the oldest are gone
        keep = old[len(old) - (BACKUPS_KEPT - 1):]
        for name in keep:
            self.assertIn(name, names)
        self.assertNotIn(old[0], names)
        self.assertNotIn(old[1], names)
        self.assertEqual(len([n for n in names if n not in old]), 1)  # the fresh backup

    def test_prune_leaves_files_that_only_look_like_backups(self):
        # Six real backups force pruning; the look-alikes and a symlinked backup must survive it.
        for n in range(6):
            (self.dir / f"settings.json.bak-aicfg-2026010{n}T000000Z").write_text("{}")
        lookalikes = ["settings.json.bak-aicfg-1", "settings.json.bak-brainrc-manual",
                      "settings.json.bak-aicfg-20260101T000000Z.keep"]
        for name in lookalikes:
            (self.dir / name).write_text("mine")
        elsewhere = self.dir / "elsewhere.json"
        elsewhere.write_text("mine")
        link = self.dir / "settings.json.bak-aicfg-20250101T000000Z"
        link.symlink_to(elsewhere)
        replace_file(self.target, '{"a": 1}', "{}")
        for name in lookalikes:
            self.assertTrue((self.dir / name).exists(), name)
        self.assertTrue(link.is_symlink())
        self.assertEqual(elsewhere.read_text(), "mine")

    def test_prune_ignores_mtime(self):
        import os
        a = self.dir / "settings.json.bak-aicfg-20260101T000000Z"
        a.write_text("{}")
        rest = []
        for n in range(2, BACKUPS_KEPT + 1):
            p = self.dir / f"settings.json.bak-brainrc-2026010{n}T000000Z"
            p.write_text("{}")
            rest.append(p)
        os.utime(a, (9999999999, 9999999999))  # newest mtime, oldest stamp
        replace_file(self.target, '{"a": 1}', "{}")
        self.assertFalse(a.exists())
        for p in rest:
            self.assertTrue(p.exists())


if __name__ == "__main__":
    unittest.main()
