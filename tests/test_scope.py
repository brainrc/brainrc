"""A pack's [scope] (#140): where it applies, and what that leaves out of a run elsewhere."""
import contextlib
import importlib.util
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from brainrc import scope
from brainrc.plugins import render_extensions
from brainrc.sources import Source, load_pack
from brainrc.validate import pack_toml_findings

from test_brainrc import REPO, TempRepoCase

ACME = REPO / "examples/pack-acme"


def fake_repo(root: Path, remote: str, branch: str = "main") -> Path:
    """A directory git would call a repo with one remote, written by hand (no git needed)."""
    (root / ".git").mkdir(parents=True)
    (root / ".git/config").write_text(
        '[core]\n\tbare = false\n[remote "origin"]\n\turl = %s\n\tfetch = +refs/heads/*:refs/remotes/origin/*\n'
        '[branch "main"]\n\tremote = origin\n' % remote)
    (root / ".git/HEAD").write_text(f"ref: refs/heads/{branch}\n")
    return root


class RemoteTest(unittest.TestCase):
    def test_ssh_and_https_normalize_alike(self):
        for url in ("git@github.com:acme/app.git", "https://github.com/acme/app", "https://me@github.com/acme/app.git",
                    "ssh://git@github.com:22/acme/app.git", "HTTPS://GitHub.com/Acme/App/"):
            with self.subTest(url=url):
                self.assertEqual(scope.normalize_remote(url), "github.com/acme/app")

    def test_a_local_path_stays_as_written(self):
        self.assertEqual(scope.normalize_remote("/srv/git/app"), "/srv/git/app")


class ContextTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_remotes_from_a_subdirectory(self):
        repo = fake_repo(self.tmp / "app", "git@github.com:acme/app.git")
        (repo / "src/deep").mkdir(parents=True)
        ctx = scope.Context(repo / "src/deep")
        self.assertIn("github.com/acme/app", ctx.values("remotes"))
        self.assertTrue(scope.applies({"remotes": ["github.com/acme/*"]}, ctx))
        self.assertFalse(scope.applies({"remotes": ["github.com/other/*"]}, ctx))

    def test_a_worktree_reads_the_shared_config(self):
        main = fake_repo(self.tmp / "main", "https://github.com/acme/app.git")
        wt_git = main / ".git/worktrees/wt"
        wt_git.mkdir(parents=True)
        (wt_git / "commondir").write_text("../..\n")
        (wt_git / "HEAD").write_text("ref: refs/heads/acme-42-fix\n")
        wt = self.tmp / "wt"
        wt.mkdir()
        (wt / ".git").write_text(f"gitdir: {wt_git}\n")
        ctx = scope.Context(wt)
        self.assertIn("github.com/acme/app", ctx.values("remotes"))
        self.assertEqual(ctx.values("tickets"), ["ACME-42"])

    def test_git_reads_url_in_any_case(self):
        repo = self.tmp / "app"
        (repo / ".git").mkdir(parents=True)
        (repo / ".git/config").write_text('[remote "origin"]\n\tURL = git@github.com:acme/app.git\n')
        self.assertIn("github.com/acme/app", scope.Context(repo).values("remotes"))

    def test_no_repo_matches_no_remote(self):
        self.assertEqual(scope.Context(self.tmp).values("remotes"), [])
        self.assertFalse(scope.applies({"remotes": ["*"]}, scope.Context(self.tmp)))

    def test_paths_match_the_directory_or_one_above_it(self):
        (self.tmp / "src/acme/app").mkdir(parents=True)
        ctx = scope.Context(self.tmp / "src/acme/app")
        self.assertTrue(scope.applies({"paths": [str(self.tmp / "src/acme")]}, ctx))
        self.assertTrue(scope.applies({"paths": [str(self.tmp / "src/ac*")]}, ctx))
        self.assertFalse(scope.applies({"paths": [str(self.tmp / "src/acme-other")]}, ctx))

    def test_kube_context_and_aws_profile(self):
        kube = self.tmp / "kubeconfig"
        kube.write_text("apiVersion: v1\ncurrent-context: \"acme-prod\"  # the live one\nkind: Config\n")
        env = {"KUBECONFIG": os.pathsep.join([str(self.tmp / "missing"), str(kube)]), "AWS_PROFILE": "acme-admin"}
        ctx = scope.Context(self.tmp, env=env)
        self.assertTrue(scope.applies({"kube_contexts": ["acme-*"]}, ctx))
        self.assertTrue(scope.applies({"aws_profiles": ["acme-*"]}, ctx))
        bare = scope.Context(self.tmp, env={"KUBECONFIG": str(self.tmp / "missing")})
        self.assertFalse(scope.applies({"kube_contexts": ["*"]}, bare))
        self.assertEqual(bare.values("aws_profiles"), ["default"])

    def test_tickets_from_the_branch_and_from_the_caller(self):
        repo = fake_repo(self.tmp / "app", "https://example.com/me/app", branch="feature/acme-7-login")
        self.assertEqual(scope.Context(repo).values("tickets"), ["ACME-7"])
        self.assertEqual(scope.Context(repo, ["ops-3"]).values("tickets"), ["OPS-3", "ACME-7"])
        self.assertTrue(scope.applies({"tickets": ["acme-*"]}, scope.Context(repo)))

    def test_any_key_is_enough_and_none_means_everywhere(self):
        ctx = scope.Context(self.tmp, env={"AWS_PROFILE": "acme"})
        self.assertTrue(scope.applies({"remotes": ["github.com/acme/*"], "aws_profiles": ["acme"]}, ctx))
        self.assertTrue(scope.applies(None, ctx))
        self.assertTrue(scope.applies({}, ctx))
        self.assertTrue(scope.applies({"remotes": []}, ctx))

    def test_a_key_is_read_only_when_asked_for(self):
        ctx = scope.Context(self.tmp, env={"KUBECONFIG": str(self.tmp / "missing")})
        scope.applies({"aws_profiles": ["x"]}, ctx)
        self.assertEqual(set(ctx._cache), {"aws_profiles"})

    def test_describe(self):
        self.assertEqual(scope.describe(None), "everywhere")
        self.assertEqual(scope.describe({"remotes": ["github.com/acme/*"], "tickets": ["ACME-*"]}),
                         "git remote github.com/acme/*, or ticket ACME-*")


def load_hook():
    spec = importlib.util.spec_from_file_location("guard_outward_under_test", REPO / "overrides/claude/hooks/guard_outward.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class HookParityTest(unittest.TestCase):
    """The guard hook carries its own copy of the evaluator: both must decide alike."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.hook = load_hook()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_same_keys_patterns_and_remote_form(self):
        self.assertEqual(self.hook.SCOPE_KEYS, scope.KEYS)
        for name in ("TICKET", "REMOTE_URL", "SECTION"):
            self.assertEqual(getattr(self.hook, name).pattern, getattr(scope, name).pattern, name)
            self.assertEqual(getattr(self.hook, name).flags, getattr(scope, name).flags, name)
        for url in ("git@github.com:acme/app.git", "ssh://git@h:22/a/b", "/srv/x", "https://u@h/a/b/"):
            self.assertEqual(self.hook.normalize_remote(url), scope.normalize_remote(url), url)

    def test_same_decisions(self):
        acme = fake_repo(self.tmp / "acme", "git@github.com:acme/app.git", branch="acme-5-fix")
        (acme / "sub").mkdir()
        personal = fake_repo(self.tmp / "mine", "https://github.com/me/x")
        kube = self.tmp / "kube"
        kube.write_text("current-context: acme-prod\n")
        scopes = [None, {}, {"remotes": ["github.com/acme/*"]}, {"remotes": ["git@github.com:acme/*"]},
                  {"paths": [str(self.tmp / "acme")]}, {"paths": [str(self.tmp / "ac*")]},
                  {"kube_contexts": ["acme-*"]}, {"aws_profiles": ["acme"]}, {"aws_profiles": ["default"]},
                  {"tickets": ["acme-*"]}, {"tickets": ["OPS-*"], "remotes": ["github.com/me/*"]}]
        envs = [{"KUBECONFIG": str(kube), "AWS_PROFILE": "acme"}, {"KUBECONFIG": str(self.tmp / "none")}]
        for env in envs:
            old = {k: os.environ.get(k) for k in ("KUBECONFIG", "AWS_PROFILE", "AWS_DEFAULT_PROFILE")}
            os.environ.pop("AWS_DEFAULT_PROFILE", None)
            os.environ.pop("AWS_PROFILE", None)
            os.environ.update(env)
            try:
                for cwd in (acme / "sub", personal, self.tmp):
                    for sc in scopes:
                        with self.subTest(env=env, cwd=cwd.name, scope=sc):
                            self.assertEqual(self.hook.scope_applies(sc, cwd, {}),
                                             scope.applies(sc, scope.Context(cwd, env=dict(os.environ))))
            finally:
                for k, v in old.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v


class ValidateScopeTest(TempRepoCase):
    def pack(self, toml: str) -> Source:
        root = self.repo / "packs/acme"
        root.mkdir(parents=True)
        (root / "pack.toml").write_text('name = "acme"\nrequires_core = ">=0"\n' + toml)
        return load_pack(root)

    def test_a_good_scope_passes(self):
        errors, warnings = pack_toml_findings(self.pack('[scope]\nremotes = ["github.com/acme/*"]\n'))
        self.assertEqual((errors, warnings), ([], []))

    def test_a_wrong_type_or_a_typo_fails_naming_the_known_key(self):
        errors, warnings = pack_toml_findings(self.pack('[scope]\nremotes = "github.com/acme/*"\nkube_context = ["x"]\n'))
        self.assertTrue(any("scope.remotes" in e for e in errors), errors)
        # ignored, a misspelt key would leave a scope that applies everywhere
        self.assertTrue(any("scope.kube_context" in e and "kube_contexts" in e for e in errors), errors)
        self.assertEqual(warnings, [])

    def test_a_typo_in_a_guard_rules_scope_fails_too(self):
        errors, _ = pack_toml_findings(self.pack('[[guard.deny]]\nmatch = "x"\nreason = "r"\nscope = { remote = ["a/*"] }\n'))
        self.assertTrue(any("guard.deny.0.scope.remote" in e and "remotes" in e for e in errors), errors)

    def test_an_empty_glob_fails(self):
        errors, _ = pack_toml_findings(self.pack('[scope]\npaths = [" "]\n'))
        self.assertTrue(any("empty glob" in e for e in errors), errors)


class ScopedExtensionsTest(TempRepoCase):
    """Done when: an acme pack's deliver checks don't show up in a personal-repo run."""

    def setUp(self):
        super().setUp()
        shutil.copytree(ACME, self.repo / "packs/acme")
        self.srcs = [Source("core", self.repo), load_pack(self.repo / "packs/gatework", "gatework"),
                     load_pack(self.repo / "packs/acme", "acme")]
        self.work = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        shutil.rmtree(self.work)
        super().tearDown()

    def test_a_personal_repo_run_leaves_out_acme(self):
        personal = fake_repo(self.work / "dotfiles", "git@github.com:me/dotfiles.git")
        text = render_extensions(self.srcs, scope.Context(personal))
        self.assertNotIn("Deploy plan reviewed by the owning team", text)
        self.assertNotIn("acme", text)

    def test_an_acme_repo_run_keeps_it(self):
        acme = fake_repo(self.work / "app", "git@github.com:acme/app.git")
        text = render_extensions(self.srcs, scope.Context(acme))
        self.assertIn("Deploy plan reviewed by the owning team", text)

    def test_an_acme_ticket_brings_it_in_outside_an_acme_repo(self):
        text = render_extensions(self.srcs, scope.Context(self.work, ["ACME-12"]))
        self.assertIn("Deploy plan reviewed by the owning team", text)

    def test_apply_renders_every_pack_and_says_where_acme_applies(self):
        text = render_extensions(self.srcs)
        self.assertIn("Deploy plan reviewed by the owning team", text)
        self.assertIn("## Scope", text)
        self.assertIn("- `acme`: git remote github.com/acme/*", text)

    def test_no_scope_section_without_a_scoped_pack(self):
        meta = dict(self.srcs[2].meta)
        meta.pop("scope")
        srcs = self.srcs[:2] + [Source("acme", self.srcs[2].root, "acme-", meta, "acme")]
        self.assertNotIn("## Scope", render_extensions(srcs))

    def test_pack_agents_are_listed_as_roles_with_their_files(self):
        """#143: a harness with no agents dir can still run acme-reviewer from its file."""
        acme = fake_repo(self.work / "app", "git@github.com:acme/app.git")
        for text in (render_extensions(self.srcs), render_extensions(self.srcs, scope.Context(acme))):
            self.assertIn("## Pack roles", text)
            self.assertIn("never replaces one", text)
            line = next(l for l in text.splitlines() if l.startswith("- `acme-reviewer` (acme): "))
            self.assertIn(f"File: `{(self.repo / 'packs/acme/agents/acme-reviewer.md').resolve()}`", line)
        self.assertNotIn("brainrc-code-reviewer", text.split("## Pack roles")[1])  # Gatework's own

    def test_the_scope_section_says_to_skip_a_skipped_packs_roles(self):
        self.assertIn("ticket connector and pack roles", render_extensions(self.srcs))

    def test_a_render_that_returns_no_text_is_a_config_error(self):
        from unittest import mock
        from brainrc import plugins
        mod = plugins.load(self.srcs[1])
        with mock.patch.object(mod, "render_extensions", return_value=None):
            with self.assertRaises(plugins.ConfigError) as e:
                render_extensions(self.srcs, scope.Context(self.work))
        self.assertIn("render_extensions returned NoneType", str(e.exception))

    def test_a_skipped_pack_brings_no_roles(self):
        personal = fake_repo(self.work / "dotfiles", "git@github.com:me/dotfiles.git")
        self.assertNotIn("## Pack roles", render_extensions(self.srcs, scope.Context(personal)))

    def test_an_excluded_agent_is_not_listed(self):
        (self.repo / "brainrc.local.toml").write_text('exclude = ["acme:agents/acme-reviewer.md"]\n')
        self.assertNotIn("acme-reviewer", render_extensions(self.srcs))

    def test_the_scope_command(self):
        (self.repo / "packs.local.toml").write_text('[acme]\npath = "packs/acme"\n')
        personal = fake_repo(self.work / "dotfiles", "git@github.com:me/dotfiles.git")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = scope.cmd_scope(str(personal))
        self.assertEqual(code, 0)
        self.assertIn("APPLIES  gatework  (no [scope])", buf.getvalue())
        self.assertIn("SKIPPED  acme  (needs git remote github.com/acme/*", buf.getvalue())
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            scope.cmd_scope(str(personal), ["acme-9"], as_json=True)
        rows = {r["pack"]: r for r in json.loads(buf.getvalue())["packs"]}
        self.assertTrue(rows["acme"]["applies"])
        self.assertEqual(rows["acme"]["why"], "ticket ACME-9 matches ACME-*")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            scope.cmd_scope(str(personal), extensions=True)
        self.assertNotIn("Deploy plan", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
