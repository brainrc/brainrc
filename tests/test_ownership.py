import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brainrc.config import OWNED_HOOK, OWNED_HOOK_MARKER


class OwnedHookTest(unittest.TestCase):
    def test_owned_by_either_dir_name(self):
        for cmd in (
            "python3 ~/.claude/hooks/brainrc/guard.py",
            "python3 ~/.claude/hooks/brainrc-acme/guard.py",
            "python3 ~/.claude/hooks/ai-config/guard.py",
            "python3 ~/.claude/hooks/ai-config-acme/guard.py",
            "python3 ~/.claude/hooks/ai-config-anything-else/x.py",  # legacy breadth
        ):
            with self.subTest(cmd=cmd):
                self.assertTrue(OWNED_HOOK.search(cmd))

    def test_near_misses_not_owned(self):
        for cmd in (
            "~/src/ai-config/run.sh",
            "/hooks/ai-configs/x",
            "/hooks/my-ai-config/x",
            "/hooks/brainrcx/x",
            "/hooks/my-brainrc/x",
            "~/src/brainrc/run.sh",
        ):
            with self.subTest(cmd=cmd):
                self.assertIsNone(OWNED_HOOK.search(cmd))

    def test_marker_names_new_dir(self):
        self.assertEqual(OWNED_HOOK_MARKER, "/hooks/brainrc/")
        self.assertTrue(OWNED_HOOK.search(OWNED_HOOK_MARKER))


if __name__ == "__main__":
    unittest.main()
