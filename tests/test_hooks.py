"""Tests for the Claude Code guard hooks (run as subprocesses, like the harness does)."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

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
            # homelab
            "qm destroy 105",
            "talosctl -n 10.0.0.2 upgrade --image x",
            "sudo reboot",
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
            "qm list",
            "talosctl -n 10.0.0.2 dashboard",
        ]:
            with self.subTest(command=command):
                self.assertIsNone(bash(command))

    def test_ignores_other_tools_and_bad_input(self):
        self.assertIsNone(run_hook("guard_outward.py", {"tool_name": "Read", "tool_input": {}}))
        out = subprocess.run([sys.executable, str(HOOKS / "guard_outward.py")],
                             input="not json", capture_output=True, text=True)
        self.assertEqual((out.returncode, out.stdout), (0, ""))


# Fake credentials assembled at runtime so secret scanners don't flag this file.
FAKE_AWS = "AKIA" + "Q" * 16
FAKE_GH = "ghp_" + "a1" * 18
FAKE_PEM = "-----BEGIN " + "RSA PRIVATE KEY-----\nMIIE..."


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
            for secret in (FAKE_AWS, FAKE_GH, FAKE_PEM):
                with self.subTest(tool=tool, secret=secret[:8]):
                    self.assertEqual(write("src/config.py", f"KEY = '{secret}'", tool), "deny")

    def test_denies_env_writes_but_allows_examples(self):
        self.assertEqual(write("app/.env", "A=1"), "deny")
        self.assertEqual(write(".env.production", "A=1"), "deny")
        self.assertIsNone(write(".env.example", "API_KEY=changeme"))

    def test_asks_before_reading_env(self):
        read = {"tool_name": "Read", "tool_input": {"file_path": "/repo/.env"}}
        self.assertEqual(run_hook("guard_secrets.py", read), "ask")
        read["tool_input"]["file_path"] = "/repo/README.md"
        self.assertIsNone(run_hook("guard_secrets.py", read))

    def test_allows_normal_code(self):
        self.assertIsNone(write("src/app.py", "token = os.environ['GITHUB_TOKEN']\n"))

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
