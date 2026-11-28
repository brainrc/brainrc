# Verify: mcp-sync

| Criterion | Evidence | Result |
|---|---|---|
| AC1 registry | `RegistryTest`: valid registry passes; both/neither of command and url, an `env` table, unknown key, bad env name, unknown harness, bad name each reported; `mcp` on a harness without an adapter fails. Core's registry stays commented out. | pass |
| AC2 packs | `PackServersTest`: prefix required, duplicate names reported, pack servers synced. | pass |
| AC3 merge | `AdapterTest` (claude, opencode, codex block round-trip through `tomllib`, escapes) and `McpSyncTest` (every harness written, secret value never written, foreign entries and keys kept, stale owned removed, user's same-name server kept and reported with exit 1, lost state adopts identical entries, Codex block removed back to the original text, harness filter, disabled harness cleared, doctor drift). | pass |
| AC4 real CLIs | Fake home, `apply` with a probe server: `claude mcp list` → Connected, probe saw `PROBE_SECRET`; `opencode mcp list` → connected, probe saw it; `codex mcp get probe` → stdio, `env: PROBE_SECRET=*****`. No secret in any file. A server added by `claude mcp add` afterwards is kept; removing the probe from the registry removes it from all three. Full suite 200 OK; validate core and pack OK; baseline transcript identical except the new help line. | pass |
| AC5 docs | README, formats (registry section, support row), packs, troubleshooting, roadmap, `mcp/servers.toml` header, CHANGELOG 0.3.27, VERSION. | pass |

Not verified: Codex actually launching the server (its CLI lists servers without connecting).
