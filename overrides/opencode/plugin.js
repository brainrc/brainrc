// brainrc guard plugin for OpenCode: runs the same Python guards as Claude Code's hooks
// (overrides/claude/hooks), packs' guard rules included, judged where the command runs (the bash
// tool's workdir, else the session's directory) so a pack's [scope] applies. MCP tools reach the
// guards under Claude Code's name for them, mcp__<server>__<tool>. OpenCode can't prompt
// from a plugin, so an "ask" blocks the call too (throwing is how a plugin refuses); the model gets
// the reason and should ask the user to run the command themselves. A pack's deny is a refusal.
import { spawnSync } from "node:child_process";
import { realpathSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

// brainrc links this file; resolve the link so the guards are found in a checkout or a package.
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

// OpenCode names an MCP tool <server>_<tool>, each part with anything but letters, digits, _ and -
// turned into _. The server's name can hold a _ itself, so it is matched against the servers OpenCode
// reports, the longest first; a tool of no known server is left alone.
const sanitize = (name) => name.replace(/[^a-zA-Z0-9_-]/g, "_");

function mcpName(tool, servers) {
  let best = null;
  for (const server of servers) {
    const prefix = sanitize(server) + "_";
    if (tool.length > prefix.length && tool.startsWith(prefix) && (!best || prefix.length > best[0].length)) {
      best = [prefix, server];
    }
  }
  return best ? `mcp__${best[1]}__${tool.slice(best[0].length)}` : null;
}

async function mcpServers(client) {
  try {
    const status = await client?.mcp?.status?.();
    return Object.keys(status?.data ?? {});
  } catch {
    return []; // no client or no answer: MCP tools go unguarded, as before
  }
}

// The strongest objection across the guards: the first deny, else the first ask, else null.
function objection(toolName, toolInput, cwd) {
  const payload = JSON.stringify({ tool_name: toolName, tool_input: toolInput, ...(cwd ? { cwd } : {}) });
  let ask = null;
  for (const guard of GUARDS) {
    const run = spawnSync("python3", [join(HOOKS, guard)], { input: payload, encoding: "utf8", timeout: 5000 });
    if (run.error || run.status !== 0 || !run.stdout.trim()) continue; // fail open, like a broken hook
    let decision;
    try {
      decision = JSON.parse(run.stdout).hookSpecificOutput;
    } catch {
      continue;
    }
    if (!decision || !["ask", "deny"].includes(decision.permissionDecision)) continue;
    const found = { decision: decision.permissionDecision, reason: decision.permissionDecisionReason };
    if (found.decision === "deny") return found;
    ask = ask ?? found;
  }
  return ask;
}

export const AiConfigGuard = async ({ directory, client } = {}) => ({
  "tool.execute.before": async (input, output) => {
    const args = output.args ?? {};
    let map = TOOLS[input.tool];
    if (!map) {
      // Asked each time, since servers can be added while OpenCode runs.
      const name = mcpName(input.tool, await mcpServers(client));
      if (!name) return;
      map = (a) => [name, a];
    }
    const cwd = typeof args.workdir === "string" && args.workdir
      ? resolve(directory ?? process.cwd(), args.workdir) : directory;
    const found = objection(...map(args), cwd);
    if (found?.decision === "deny") throw new Error(found.reason);
    if (found) {
      throw new Error(`${found.reason} OpenCode can't ask for approval, so this call is blocked; ` +
        "ask the user to run it themselves.");
    }
  },
});
