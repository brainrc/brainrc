# Log: 204-point-urls-brainrc

## engine · intake · done
2026-10-27T18:43:34Z
**Did:** Branch 204-point-urls-brainrc from main; ticket fetched (MCP). Size small (4 docs + pyproject, ~15 lines, one open question), mode inline, domains none, offline only, delivery normal, auto.
**Evidence:** baseline `python3 -m unittest discover -s tests` → 438 OK; validate → OK.

## engine · Spec gate · auto-approved
2026-10-27T18:47:20Z (recorded late: spec written ~18:46, timestamp taken at write-up)
⛔ Spec gate: 204-point-urls-brainrc
Summary: 3 criteria (no old path outside specs/CHANGELOG; pyproject URLs; manifests regenerate unchanged). Two open questions, defaults taken (see spec.md).
Decide: the criteria and defaults.
Artifacts: specs/204-point-urls-brainrc/spec.md

## implementer (inline) · T1 · done
**Did:** Replaced the old path in 4 docs, added `[project.urls]`, wrote the fragment (reworded once: its first text named the old path and tripped AC1).
**Evidence:** grep → none; validate OK; tests 438 OK. **Changed files:** README.md, docs/install.md, docs/harness-packages.md, docs/roadmap.md, pyproject.toml, changelog.d/204-point-urls-brainrc.md. Commit 9af5a4c.

## code-reviewer (inline, shared context) · batch · done
**Findings:** none. Clone target `~/ai-config` and `ai-config@ai-config` intentionally unchanged (marketplace name is still ai-config until #208).

## verifier (inline) · verify · done
2026-10-27T18:47:04Z
**Evidence:** see verify.md; 3/3 criteria pass.

## engine · deliver · done
2026-10-28T01:16:33Z
Owner said "ship 204" (outside the stack gate, while #205 is blocked; counted as an intervention). Merged origin/main (v0.3.49) first: tests OK, validate OK, manifests unchanged, grep clean. Pushed 204-point-urls-brainrc, opened draft PR #229 against main. Ticket comment not posted (draft only). Deliver presented_at unset: no gate message was shown, the owner asked directly.
