"""Core agents under `brainrc-` and their deprecated aliases (gh:295)."""
import shutil
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_brainrc import TempRepoCase, brainrc, make_pack, quiet  # noqa: E402
from brainrc import naming  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OLD = ("analyst", "architect", "code-reviewer", "doc-writer", "implementer", "infra-reviewer",
       "researcher", "security-reviewer", "test-writer", "verifier")


def meta(root, name):
    return brainrc.frontmatter(Path(root) / "packs/gatework/agents" / f"{name}.md")


class ShippedTreeTest(unittest.TestCase):
    def test_every_core_agent_is_prefixed_or_a_declared_alias(self):
        self.assertEqual(set(naming.AGENT_ALIASES), set(OLD))
        for f in (ROOT / "packs/gatework/agents").glob("*.md"):
            with self.subTest(agent=f.stem):
                self.assertTrue(f.stem.startswith("brainrc-") or f.stem in OLD)
                self.assertEqual(meta(ROOT, f.stem).get("name"), f.stem)

    def test_each_alias_runs_as_its_target(self):
        for n in OLD:
            with self.subTest(agent=n):
                new, alias = meta(ROOT, f"brainrc-{n}"), meta(ROOT, n)
                text = (ROOT / f"packs/gatework/agents/{n}.md").read_text()
                self.assertEqual((alias.get("tools"), alias.get("model")), (new.get("tools"), new.get("model")))
                self.assertTrue(alias["description"].startswith("Deprecated"), alias["description"])
                self.assertLessEqual(len(alias["description"]), 80, "always-loaded token budget")
                self.assertIn(f"`brainrc-{n}`", text)
                self.assertIn(naming.AGENT_ALIAS_REMOVED_IN, text)
                target = (ROOT / f"packs/gatework/agents/brainrc-{n}.md").read_text().split("\n---\n", 1)[1]
                self.assertTrue(text.endswith(target), "a subagent can't find another file, so it carries the instructions")

    def test_spec_agent_dispatches_the_new_names(self):
        text = (ROOT / "packs/gatework/skills/spec-agent/SKILL.md").read_text()
        for n in OLD:
            with self.subTest(agent=n):
                self.assertIn(f"[roles/brainrc-{n}.md](roles/brainrc-{n}.md)", text)
                self.assertNotIn(f"(roles/{n}.md)", text)


class AliasNearMissTest(TempRepoCase):
    def validate(self):
        return quiet(brainrc.cmd_validate)

    def test_unmodified_copy_validates(self):
        code, out = self.validate()
        self.assertEqual(code, 0, out)

    def test_missing_alias_fails(self):
        (self.repo / "packs/gatework/agents/verifier.md").unlink()
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("agents/verifier.md: deprecated alias for `brainrc-verifier` is missing", out)

    def test_alias_with_other_tools_fails(self):
        path = self.repo / "packs/gatework/agents/code-reviewer.md"
        path.write_text(path.read_text().replace("tools: Read, Grep, Glob, Bash", "tools: Read, Grep, Glob, Bash, Edit"))
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("alias `tools` must match `brainrc-code-reviewer`", out)

    def test_alias_without_its_removal_release_or_target_name_fails(self):
        path = self.repo / "packs/gatework/agents/analyst.md"
        path.write_text(path.read_text().replace(naming.AGENT_ALIAS_REMOVED_IN, "later")
                        .replace("`brainrc-analyst`", "the new agent"))
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("alias body must name the removal release", out)
        self.assertIn("alias body must name `brainrc-analyst`", out)

    def test_alias_whose_instructions_drift_from_its_target_fails(self):
        path = self.repo / "packs/gatework/agents/brainrc-verifier.md"
        path.write_text(path.read_text() + "\nOne more rule.\n")
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("agents/verifier.md: alias body must end with `brainrc-verifier`'s instructions", out)

    def test_alias_without_a_deprecated_description_fails(self):
        path = self.repo / "packs/gatework/agents/analyst.md"
        path.write_text(path.read_text().replace("description: Deprecated, use", "description: Use"))
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("alias `description` must start with `Deprecated`", out)

    def test_unprefixed_new_core_agent_fails_and_prefixed_passes(self):
        body = "---\nname: {0}\ndescription: A test agent.\n---\nBody.\n"
        (self.repo / "packs/gatework/agents/planner.md").write_text(body.format("planner"))
        code, out = self.validate()
        self.assertEqual(code, 1, out)
        self.assertIn("agents/planner.md: core agent names start with `brainrc-`", out)
        (self.repo / "packs/gatework/agents/planner.md").unlink()
        (self.repo / "packs/gatework/agents/brainrc-planner.md").write_text(body.format("brainrc-planner"))
        code, out = self.validate()
        self.assertEqual(code, 0, out)

    def test_a_pack_may_still_name_an_old_reviewer(self):
        pack = make_pack(self.repo.parent / f"{self.repo.name}-pack")
        toml = pack / "pack.toml"
        self.assertIn('reviewer = "brainrc-infra-reviewer"', toml.read_text())
        toml.write_text(toml.read_text().replace('"brainrc-infra-reviewer"', '"infra-reviewer"'))
        try:
            code, out = quiet(brainrc.cmd_validate, str(pack))
            self.assertNotIn("unknown reviewer", out)
        finally:
            shutil.rmtree(pack)


if __name__ == "__main__":
    unittest.main()
