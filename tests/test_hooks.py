"""Tests for the Claude Code guard hooks (run as subprocesses, like the harness does)."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from support import rmtree, symlink

HOOKS = Path(__file__).resolve().parent.parent / "overrides" / "claude" / "hooks"


def run_hook(script: str, payload: dict) -> str | None:
    """Return the permission decision the hook emits, or None for no opinion."""
    out = subprocess.run(
        [sys.executable, str(HOOKS / script)],
        input=json.dumps(payload), capture_output=True, text=True, check=True,
    ).stdout.strip()
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else None


def bash(command: str) -> str | None:
    return run_hook("guard_outward.py", {"tool_name": "Bash", "tool_input": {"command": command}})


class GuardOutwardTest(unittest.TestCase):
    def test_asks_for_outward_and_destructive(self):
        for command in [
            "git push origin feature",
            "cd repo && git push -u origin 042-csv",
            "git push --force",
            "git reset --hard HEAD~1",
            "git clean -fdx",
            "git branch -D old",
            "gh pr create --draft --title x --body-file b.md",
            "gh pr merge 3 --squash",
            "gh issue comment 42 --body-file c.md",
            "gh issue close 42",
            "gh api repos/o/r/issues -f title=x",
            "gh api -X DELETE repos/o/r",
            "gh api --method=PATCH repos/o/r",
            "npm publish",
            "docker push img:1",
            "terraform apply",
            "rm -rf build",
            "rm -r -f build",
            "rm --recursive --force build",
            "sudo /bin/rm -fr /tmp/x",
            # Terraform family
            "terraform apply -auto-approve",
            "cd infra/dev && terraform destroy",
            "tofu apply tfplan",
            "terragrunt run-all apply --terragrunt-include-dir x",
            "terraform state rm aws_s3_bucket.logs",
            "terraform import aws_iam_role.r role",
            "terraform workspace delete old",
            # Kubernetes / GitOps
            "kubectl apply -f deploy.yaml",
            "kubectl --context prod delete pod api-0",
            "kubectl -n app rollout restart deploy/api",
            "kubectl scale deploy/api --replicas=0",
            "kubectl exec -it api-0 -- sh",
            "helm upgrade --install api ./chart -f values-prod.yaml",
            "helm --kube-context prod uninstall api",
            "argocd app sync payments",
            "flux reconcile kustomization apps",
            # AWS
            "aws s3 rm s3://bucket/key",
            "aws --profile prod ec2 terminate-instances --instance-ids i-1",
            "aws iam put-role-policy --role-name r --policy-name p --policy-document file://p.json",
            "aws lambda invoke --function-name f out.json",
            "aws secretsmanager get-secret-value --secret-id db",
            "aws ssm get-parameter --name /db/pass --with-decryption",
            # databases
            "migrate -path db/migrations -database $DATABASE_URL up",
            "goose -dir migrations postgres \"host=db.prod.internal\" up",
            "psql -h db.prod.internal -c 'DROP TABLE users'",
            # hosts
            "sudo reboot",
            # git global options before the subcommand
            "git -C ../other push origin main",
            "git -c user.name=x push",
            "git --no-pager -C repo reset --hard",
            # hidden inside wrappers
            "sh -c 'kubectl delete pod api-0'",
            "bash -lc \"terraform apply -auto-approve\"",
            "zsh --login -c 'helm uninstall api'",
            "eval kubectl delete ns app",
            "echo $(kubectl delete pod api-0)",
            "echo `gh api -X DELETE repos/o/r`",
            # operators without spaces
            "ls;kubectl delete pod api-0",
            "true&&helm upgrade api ./chart",
            # --dry-run=none is a real run
            "kubectl apply --dry-run=none -f deploy.yaml",
            # previously untested rules
            "gh workflow run deploy.yml",
            "gh secret set TOKEN",
            "gh release create v1.0.0",
            "gh repo delete o/r --yes",
            "argocd cluster rm prod",
            "sudo halt",
            "helm rollback api 3",
            "kubectl rollout undo deploy/api",
            "aws s3 sync ./site s3://bucket",
            "alembic upgrade head",
            "atlas migrate apply --url postgres://db.prod.internal/app",
            "gh api graphql -f query='mutation { addStar(input: {}) { clientMutationId } }'",
            "gh api graphql --input body.json",
        ]:
            with self.subTest(command=command):
                self.assertEqual(bash(command), "ask")

    def test_allows_safe_commands(self):
        for command in [
            "git status",
            "git log --oneline -5",
            "git commit -m 'Add flag'",
            "git diff main...HEAD",
            "gh issue view 42 --json title,body",
            "gh pr view 3",
            "gh api repos/o/r/issues",
            "gh api -X GET repos/o/r",
            "rm build/out.txt",
            "rm -r build",
            "python3 -m unittest -q",
            # read-only / offline infra work stays prompt-free
            "terraform fmt -check -recursive",
            "terraform init -backend=false && terraform validate",
            "terraform plan -lock=false -out=tfplan",
            "terraform plan -destroy -out=tfplan",
            "terraform show -json tfplan",
            "terragrunt plan --terragrunt-non-interactive",
            "kubectl --context kind-dev get pods -A",
            "kubectl -n app rollout status deploy/api",
            "kubectl apply --dry-run=client -f deploy.yaml",
            "kubectl create secret generic x --dry-run=client -o yaml",
            "kubectl --context dev diff -f deploy.yaml",
            "helm template api ./chart -f values.yaml",
            "helm lint ./chart",
            "helm upgrade api ./chart --dry-run",
            "argocd app diff payments",
            "flux get kustomizations",
            "aws sts get-caller-identity --profile dev",
            "aws --profile dev --region eu-west-1 ec2 describe-instances",
            "aws s3 ls s3://bucket",
            "aws ssm get-parameter --name /app/flag",
            "migrate -path db/migrations -database postgres://dev:dev@localhost:55432/app up",
            "psql -h localhost -p 55432 -c 'DROP TABLE t'",
            "psql -h db.prod.internal -c 'select 1'",
            # near misses for the rules above
            "git -C ../other status",
            "git -c core.pager=cat log -3",
            "sh -c 'kubectl get pods'",
            "bash -lc 'terraform validate'",
            "bash scripts/build.sh",
            "eval \"$(mise activate zsh)\"",
            "echo $(git rev-parse HEAD)",
            "ls;kubectl get pods",
            "kubectl apply --dry-run=server -f deploy.yaml",
            "terraform plan -out=apply.tfplan",
            "terraform plan -out apply.tfplan",
            "gh workflow list",
            "gh secret list",
            "gh release view v1.0.0",
            "argocd cluster list",
            "helm history api",
            "kubectl rollout history deploy/api",
            "aws s3 ls s3://bucket/site/",
            "alembic history",
            "gh api graphql -f query='query { viewer { login } }'",
        ]:
            with self.subTest(command=command):
                self.assertIsNone(bash(command))

    def test_asks_for_mcp_writes_only(self):
        def mcp(name: str) -> str | None:
            return run_hook("guard_outward.py", {"tool_name": name, "tool_input": {}})

        for name in [
            "mcp__github__create_pull_request",
            "mcp__plugin_ecc_github__merge_pull_request",
            "mcp__claude_ai_Slack__slack_send_message",
            "mcp__claude_ai_Atlassian__addCommentToJiraIssue",
            "mcp__claude_ai_Atlassian__transitionJiraIssue",
            "mcp__claude_ai_Atlassian__updateConfluencePage",
        ]:
            with self.subTest(name=name):
                self.assertEqual(mcp(name), "ask")
        for name in [
            "mcp__github__get_pull_request",
            "mcp__claude_ai_Atlassian__getTransitionsForJiraIssue",
            "mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql",
            "mcp__claude_ai_Slack__slack_read_thread",
            "mcp__plugin_ecc_memory__create_entities",
            "mcp__docs__search_documentation",
            "mcp__notaserver",
        ]:
            with self.subTest(name=name):
                self.assertIsNone(mcp(name))

    def test_ignores_other_tools_and_bad_input(self):
        self.assertIsNone(run_hook("guard_outward.py", {"tool_name": "Read", "tool_input": {}}))
        out = subprocess.run([sys.executable, str(HOOKS / "guard_outward.py")],
                             input="not json", capture_output=True, text=True)
        self.assertEqual((out.returncode, out.stdout), (0, ""))


# Fake credentials assembled at runtime so secret scanners don't flag this file.
FAKE_AWS = "AKIA" + "Q" * 16
FAKE_GH = "ghp_" + "a1" * 18
FAKE_PEM = "-----BEGIN " + "RSA PRIVATE KEY-----\nMIIE..."
FAKE_AWS_SECRET = "aws_secret_access_key = " + "wJalr" + "Q" * 35
FAKE_GITLAB = "glpat-" + "x" * 20
FAKE_JWT = "eyJ" + "a" * 12 + ".eyJ" + "b" * 12 + "." + "c" * 12


HOMELAB_HOOKS = HOOKS.parent.parent.parent / "examples" / "pack-homelab" / "overrides" / "claude" / "hooks"
HOMELAB_RISKY = ["qm destroy 105", "pct stop 200", "talosctl -n 10.0.0.2 upgrade --image x"]


def homelab(payload: dict | str) -> str | None:
    data = payload if isinstance(payload, str) else json.dumps(payload)
    out = subprocess.run(
        [sys.executable, str(HOMELAB_HOOKS / "guard_homelab.py")],
        input=data, capture_output=True, text=True, check=True,
    ).stdout.strip()
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else None


class HomelabGuardTest(unittest.TestCase):
    """The Proxmox and Talos rules live in examples/pack-homelab, not in core."""

    def test_core_no_longer_asks(self):
        for command in HOMELAB_RISKY:
            with self.subTest(command=command):
                self.assertIsNone(bash(command))

    def test_pack_asks_for_destructive(self):
        for command in HOMELAB_RISKY + [
            "qm migrate 105 node2",
            "pct rollback 200 snap1",
            "talosctl reset -n 10.0.0.2",
            "sh -c 'qm destroy 105'",
            "ls;pct shutdown 200",
        ]:
            with self.subTest(command=command):
                self.assertEqual(homelab({"tool_name": "Bash", "tool_input": {"command": command}}), "ask")

    def test_pack_allows_read_only(self):
        for command in ["qm list", "pct list", "talosctl -n 10.0.0.2 dashboard",
                        "talosctl -n 10.0.0.2 get members", "echo qm-destroy", "git status"]:
            with self.subTest(command=command):
                self.assertIsNone(homelab({"tool_name": "Bash", "tool_input": {"command": command}}))

    def test_pack_ignores_other_tools_and_bad_payloads(self):
        self.assertIsNone(homelab({"tool_name": "Read", "tool_input": {"command": "qm destroy 105"}}))
        self.assertIsNone(homelab("not json"))
        self.assertIsNone(homelab({"tool_name": "Bash"}))

    def test_pack_fragment_runs_hook_from_its_hooks_dir(self):
        fragment = json.loads((HOMELAB_HOOKS.parent / "settings.fragment.json").read_text())
        commands = [h["command"] for e in fragment["hooks"]["PreToolUse"] for h in e["hooks"]]
        self.assertEqual(len(commands), 1)
        self.assertIn("{{hooks_dir}}/guard_homelab.py", commands[0])


def write(path: str, content: str, tool: str = "Write") -> str | None:
    tool_input = {"file_path": path}
    if tool == "Write":
        tool_input["content"] = content
    elif tool == "Edit":
        tool_input.update(old_string="x", new_string=content)
    else:
        tool_input["edits"] = [{"old_string": "x", "new_string": content}]
    return run_hook("guard_secrets.py", {"tool_name": tool, "tool_input": tool_input})


class GuardSecretsTest(unittest.TestCase):
    def test_denies_secret_content(self):
        for tool in ("Write", "Edit", "MultiEdit"):
            for secret in (FAKE_AWS, FAKE_GH, FAKE_PEM, FAKE_AWS_SECRET, FAKE_GITLAB, FAKE_JWT):
                with self.subTest(tool=tool, secret=secret[:8]):
                    self.assertEqual(write("src/config.py", f"KEY = '{secret}'", tool), "deny")

    def test_denies_secret_file_writes_but_allows_examples(self):
        for path in ("app/.env", ".env.production", ".envrc", "home/.aws/credentials"):
            with self.subTest(path=path):
                self.assertEqual(write(path, "A=1"), "deny")
        for path in (".env.example", ".env.dist", "docs/credentials.md", "aws/config"):
            with self.subTest(path=path):
                self.assertIsNone(write(path, "API_KEY=changeme"))

    def test_asks_before_reading_secret_files(self):
        def read(path: str) -> str | None:
            return run_hook("guard_secrets.py", {"tool_name": "Read", "tool_input": {"file_path": path}})

        for path in ("/repo/.env", "/repo/.envrc", "/u/.aws/credentials", "/u/.netrc"):
            with self.subTest(path=path):
                self.assertEqual(read(path), "ask")
        for path in ("/repo/README.md", "/repo/.env.example", "/u/.aws/config"):
            with self.subTest(path=path):
                self.assertIsNone(read(path))

    def test_asks_before_grepping_secret_files(self):
        def grep(**tool_input: str) -> str | None:
            return run_hook("guard_secrets.py", {"tool_name": "Grep", "tool_input": {"pattern": "KEY", **tool_input}})

        self.assertEqual(grep(path="/repo/.env"), "ask")
        self.assertEqual(grep(glob=".env*"), "ask")
        self.assertEqual(grep(glob="**/.envrc"), "ask")
        self.assertIsNone(grep(path="/repo/src", glob="*.py"))
        self.assertIsNone(grep())

    def test_asks_before_bash_reads_of_secret_files(self):
        def sh(command: str) -> str | None:
            return run_hook("guard_secrets.py", {"tool_name": "Bash", "tool_input": {"command": command}})

        for command in ("cat .env", "grep TOKEN app/.env.local", "source .envrc",
                        "docker run --env-file=.env img", "cat ~/.aws/credentials", "head <.env"):
            with self.subTest(command=command):
                self.assertEqual(sh(command), "ask")
        for command in ("cat .env.example", "ls -la", "grep env README.md",
                        "cat ~/.aws/config", "echo credentials"):
            with self.subTest(command=command):
                self.assertIsNone(sh(command))

    def test_allows_normal_code(self):
        self.assertIsNone(write("src/app.py", "token = os.environ['GITHUB_TOKEN']\n"))
        self.assertIsNone(write("src/app.py", "aws_secret_access_key = os.environ['AWS_SECRET']\n"))

    def test_never_echoes_secret(self):
        out = subprocess.run(
            [sys.executable, str(HOOKS / "guard_secrets.py")],
            input=json.dumps({"tool_name": "Write",
                              "tool_input": {"file_path": "a.py", "content": FAKE_AWS}}),
            capture_output=True, text=True, check=True,
        ).stdout
        self.assertNotIn(FAKE_AWS, out)


if __name__ == "__main__":
    unittest.main()


PLUGIN = HOOKS.parent.parent / "opencode" / "plugin.js"
DRIVER = """
const [url, call] = process.argv.slice(-2);
const plugin = Object.values(await import(url))[0];
const hooks = await plugin({});
const [tool, args] = JSON.parse(call);
try {
  await hooks["tool.execute.before"]({ tool, sessionID: "s", callID: "c" }, { args });
  console.log("OK");
} catch (e) {
  console.log("BLOCKED " + e.message);
}
"""


@unittest.skipUnless(shutil.which("node"), "node is not installed")
class OpenCodePluginTest(unittest.TestCase):
    """overrides/opencode/plugin.js runs the same guards for OpenCode's tool calls."""

    def call(self, tool: str, args: dict) -> str:
        result = subprocess.run(["node", "--input-type=module", "-e", DRIVER, "--", PLUGIN.as_uri(),
                                 json.dumps([tool, args])], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def test_outward_command_is_blocked_with_the_reason(self):
        out = self.call("bash", {"command": "git push origin main"})
        self.assertTrue(out.startswith("BLOCKED"), out)
        self.assertIn("git push publishes commits", out)
        self.assertIn("ask the user to run it themselves", out)

    def test_safe_command_passes(self):
        self.assertEqual(self.call("bash", {"command": "git status"}), "OK")

    def test_secret_file_read_is_blocked(self):
        self.assertTrue(self.call("read", {"filePath": "/tmp/project/.env"}).startswith("BLOCKED"))

    def test_ordinary_read_passes(self):
        self.assertEqual(self.call("read", {"filePath": "/tmp/project/README.md"}), "OK")

    def test_writing_a_private_key_is_blocked(self):
        key = "-----BEGIN OPENSSH " + "PRIVATE KEY-----\nabc\n"
        self.assertTrue(self.call("write", {"filePath": "notes.txt", "content": key}).startswith("BLOCKED"))

    def test_unmapped_tools_pass(self):
        self.assertEqual(self.call("github_create_issue", {"title": "x"}), "OK")


CURSOR_GUARD = HOOKS.parent.parent / "cursor" / "hooks" / "guard.py"


def cursor(payload, guard: Path = CURSOR_GUARD) -> dict:
    """Run Cursor's guard adapter; it must always exit 0 with a JSON reply."""
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    result = subprocess.run([sys.executable, str(guard)], input=stdin, capture_output=True,
                            text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def shell(command: str) -> dict:
    return cursor({"hook_event_name": "beforeShellExecution", "command": command, "cwd": "/tmp/project"})


def read_file(path: str, content: str = "") -> dict:
    return cursor({"hook_event_name": "beforeReadFile", "file_path": path, "content": content})


class CursorGuardTest(unittest.TestCase):
    """overrides/cursor/hooks/guard.py runs the same guards for Cursor's blocking hooks."""

    def test_outward_command_is_denied_with_the_reason(self):
        reply = shell("git push origin main")
        self.assertEqual(reply["permission"], "deny")
        for key in ("user_message", "agent_message"):
            self.assertIn("git push publishes commits", reply[key])
            self.assertIn("ask the user to run it themselves", reply[key])

    def test_safe_command_is_allowed(self):
        self.assertEqual(shell("ls -la"), {"permission": "allow"})

    def test_bash_naming_a_secret_file_is_denied(self):
        self.assertEqual(shell("cat .env")["permission"], "deny")

    def test_secret_file_read_is_denied(self):
        self.assertEqual(read_file("/tmp/project/.env", "TOKEN=x")["permission"], "deny")

    def test_ordinary_read_is_allowed(self):
        self.assertEqual(read_file("/tmp/project/README.md", "# hi"), {"permission": "allow"})

    def test_bad_json_and_unknown_events_are_allowed(self):
        self.assertEqual(cursor("not json"), {"permission": "allow"})
        self.assertEqual(cursor({"hook_event_name": "afterFileEdit", "file_path": ".env"}),
                         {"permission": "allow"})

    def test_works_through_a_symlinked_hooks_dir(self):
        link_dir = Path(tempfile.mkdtemp()).resolve()
        try:
            symlink(link_dir / "ai-config", CURSOR_GUARD.parent)
            reply = cursor({"hook_event_name": "beforeShellExecution", "command": "git push"},
                           link_dir / "ai-config" / "guard.py")
            self.assertEqual(reply["permission"], "deny")
        finally:
            rmtree(link_dir)


REPO = HOOKS.parent.parent.parent
sys.path.insert(0, str(REPO))
import brainrc  # noqa: E402  (the package at the repo root)

RISKY = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "git push origin main"}}
SAFE = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": "ls"}}
CURSOR_RISKY = {"hook_event_name": "beforeShellExecution", "command": "git push origin main", "cwd": "/tmp/project"}


def fragment_commands(harness: str, hooks_dir: Path) -> list[str]:
    """Hook commands as apply writes them, pointing at hooks_dir."""
    rendered = brainrc.render_fragment(REPO / "overrides" / harness / "settings.fragment.json", str(hooks_dir))
    return [h["command"] for groups in rendered["hooks"].values() for g in groups
            for h in [g, *g.get("hooks", [])] if "command" in h]


def run_command(command: str, payload: dict) -> subprocess.CompletedProcess:
    """Run a hook command through the shell, as the harness does."""
    return subprocess.run(["sh", "-c", command], input=json.dumps(payload), capture_output=True, text=True)


class FailOpenTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()

    def tearDown(self):
        rmtree(self.tmp)

    def hooks_dir(self, harness: str) -> Path:
        """A link to the real hooks, as apply makes it."""
        d = self.tmp / harness
        symlink(d, REPO / "overrides" / harness / "hooks")
        return d

    def remove_target(self, link: Path) -> None:
        """The checkout moved or the package went away: the link now dangles."""
        link.unlink()
        symlink(link, self.tmp / "gone")

    def test_claude_commands_behave_like_the_guards_when_present(self):
        d = self.hooks_dir("claude")
        commands = fragment_commands("claude", d)
        self.assertEqual(len(commands), 2)
        for command, script in zip(commands, ["guard_outward.py", "guard_secrets.py"]):
            for payload in (RISKY, SAFE):
                direct = subprocess.run([sys.executable, str(d / script)], input=json.dumps(payload),
                                        capture_output=True, text=True)
                via = run_command(command, payload)
                self.assertEqual((via.returncode, via.stdout), (direct.returncode, direct.stdout), command)
        decision = json.loads(run_command(commands[0], RISKY).stdout)["hookSpecificOutput"]["permissionDecision"]
        self.assertEqual(decision, "ask")

    def test_claude_commands_pass_when_the_hooks_are_gone(self):
        d = self.hooks_dir("claude")
        commands = fragment_commands("claude", d)
        self.remove_target(d)
        for command in commands:
            result = run_command(command, RISKY)
            self.assertEqual((result.returncode, result.stdout), (0, ""), command)

    def test_cursor_commands_behave_like_the_guard_when_present(self):
        d = self.hooks_dir("cursor")
        for command in fragment_commands("cursor", d):
            result = run_command(command, CURSOR_RISKY)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["permission"], "deny")

    def test_cursor_commands_allow_when_the_hooks_are_gone(self):
        d = self.hooks_dir("cursor")
        commands = fragment_commands("cursor", d)
        self.remove_target(d)
        self.assertEqual(len(commands), 2)
        for command in commands:
            result = run_command(command, CURSOR_RISKY)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), {"permission": "allow"})

    def test_apply_replaces_old_form_hook_groups(self):
        old_command = 'python3 "$HOME/.claude/hooks/ai-config/guard_outward.py"'
        current = {"hooks": {"PreToolUse": [
            {"matcher": "Bash|mcp__.*", "hooks": [{"type": "command", "command": old_command, "timeout": 5}]}]}}
        wanted = brainrc.render_fragment(REPO / "overrides/claude/settings.fragment.json", "~/.claude/hooks/ai-config")
        merged = brainrc.merge_settings(current, wanted)
        self.assertEqual(merged["hooks"], wanted["hooks"])
        self.assertNotIn(old_command, json.dumps(merged))
