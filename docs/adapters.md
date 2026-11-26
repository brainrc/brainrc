# Tool adapters

brainrc knows each AI tool through two things. [`harnesses.toml`](../harnesses.toml) says *where*
the tool reads each kind of content. An **adapter**, a small Python class in `brainrc/adapters/`,
says *what that content has to look like there*: how agents are written, where its settings file
keeps hooks, how it spells an MCP server, which guard rules its sandbox can take, and its name in
prose. A tool that reads everything the way Claude Code writes it needs an adapter with a name and
a label, and nothing else.

This page is for adding a tool. To change where a tool you already use reads its files, set its
paths in [`harnesses.local.toml`](configuration.md#harnesseslocaltoml) instead.

## What an adapter declares

| Attribute or method | What it says | Default |
|---|---|---|
| `name` | its `harnesses.toml` table | required |
| `label` | the tool's name in prose and in the [capability matrix](capabilities.md) | required |
| `paths` | its `harnesses.toml` table, for a tool core's file doesn't list | `{}` |
| `agents_format`, `render_agent(path)` | the agent format it reads; set `defines_agents_format = True` and write `render_agent` for a format of its own (OpenCode's) | `"claude"`: agents linked as written |
| `settings_format`, `hooks_view`, `hooks_put`, `hooks_problem` | where its settings file keeps hooks, mapped to and from Claude Code's shape; set `defines_settings_format = True` for a format of its own (Antigravity's) | `"claude"`: under `"hooks"` |
| `writes_mcp`, `mcp_key`, `mcp_entry(server)` | whether `apply` writes its MCP servers, the JSON key they sit under, and how one server is spelled | no MCP |
| `mcp_files(dest)` | other files that may hold its servers | its `mcp` path only |
| `mcp_text_change(text, servers)` | a config file that isn't JSON (Codex's TOML block) | the JSON merge |
| `sandbox` | guard rule kinds (`path`, `host`) to the settings lists its OS sandbox reads | none |

A harness table can borrow another adapter's format with `agents_format` or `settings_format`, so
a tool you define yourself in `harnesses.local.toml` can, for example, take OpenCode's agents.
A table with no adapter at all gets the defaults above.

## Shipping an adapter in core

1. Add `brainrc/adapters/<tool>.py` with the class, and list it in `BUILTIN` in
   `brainrc/adapters/__init__.py`, in `harnesses.toml`'s order.
2. Add the tool's table to `harnesses.toml`, with paths from the tool's current official docs.
   Mark a path you couldn't confirm in a comment, the way Antigravity's agents line is marked.
3. If the tool runs hooks, add `overrides/<tool>/` with its guard and `settings.fragment.json`, and
   its cases in `tests/test_hooks.py` (see [guardrails](guardrails.md)). If it can't block a tool
   call, say so in the matrix rather than claim guard parity.
4. Run `python3 scripts/brainrc.py capabilities --write`, update the hand-written table at the top
   of [capabilities](capabilities.md), and add a changelog fragment.

`tests/test_adapter_goldens.py` holds every file `apply` writes for each shipped tool. A change to
an existing tool's output fails it; `BRAINRC_REGOLDEN=1` rewrites the goldens, and the diff is the
change users get.

## An adapter from your own package

A tool brainrc doesn't ship can come from any Python package, with no change to core. Declare one
entry point in the `brainrc.adapters` group, named after the tool's table:

```toml
# pyproject.toml of your package
[project.entry-points."brainrc.adapters"]
acmetool = "acme_brainrc:AcmeTool"
```

```python
# acme_brainrc.py
from brainrc.adapters import Adapter


class AcmeTool(Adapter):
    name = "acmetool"
    label = "Acme Tool"
    paths = {"skills": "~/.acmetool/skills", "instructions": "~/.acmetool/AGENTS.md"}
```

Install the package into the same Python as brainrc (`pipx inject brainrc acme-brainrc`, or
`uv tool install brainrc --with acme-brainrc`). From then on `apply` treats `acmetool` like a
shipped tool: it is managed once `~/.acmetool` exists, `harnesses.local.toml` can move its paths
or set `enabled = false`, and `doctor` and `uninstall` know it. An entry point that can't load,
isn't an `Adapter`, or names itself differently stops `apply` with the package named. An entry
point that reuses a shipped tool's name is ignored; that tool keeps core's adapter.

An installed adapter runs as Python inside brainrc, so install only packages you trust, as you
would a pack with hooks.
