// ai-config guard plugin for OpenCode: runs the same Python guards as Claude Code's hooks
// (overrides/claude/hooks). OpenCode can't prompt from a plugin, so an "ask" blocks the call
// too; the model gets the reason and should ask the user to run the command themselves.
import { spawnSync } from "node:child_process";
import { realpathSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// aicfg links this file; resolve the link so the guards are found in a checkout or a package.
const HOOKS = join(dirname(realpathSync(fileURLToPath(import.meta.url))), "..", "claude", "hooks");
const GUARDS = ["guard_outward.py", "guard_secrets.py"];

// OpenCode tool -> the Claude tool name and arguments the guards read.
const TOOLS = {
  bash: (a) => ["Bash", { command: a.command ?? "" }],
  read: (a) => ["Read", { file_path: a.filePath ?? "" }],
  write: (a) => ["Write", { file_path: a.filePath ?? "", content: a.content ?? "" }],
  edit: (a) => ["Edit", { file_path: a.filePath ?? "", new_string: a.newString ?? "" }],
  grep: (a) => ["Grep", { path: a.path ?? "", glob: a.include ?? "" }],
};

function objection(toolName, toolInput) {
  const payload = JSON.stringify({ tool_name: toolName, tool_input: toolInput });
  for (const guard of GUARDS) {
    const run = spawnSync("python3", [join(HOOKS, guard)], { input: payload, encoding: "utf8", timeout: 5000 });
    if (run.error || run.status !== 0 || !run.stdout.trim()) continue; // fail open, like a broken hook
    let decision;
    try {
      decision = JSON.parse(run.stdout).hookSpecificOutput;
    } catch {
      continue;
    }
    if (decision && ["ask", "deny"].includes(decision.permissionDecision)) {
      return decision.permissionDecisionReason;
    }
  }
  return null;
}

export const AiConfigGuard = async () => ({
  "tool.execute.before": async (input, output) => {
    const map = TOOLS[input.tool];
    if (!map) return;
    const reason = objection(...map(output.args ?? {}));
    if (reason) {
      throw new Error(`${reason} OpenCode can't ask for approval, so this call is blocked; ` +
        "ask the user to run it themselves.");
    }
  },
});
