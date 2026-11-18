Templates for `brainrc new pack` (brainrc/newpack.py). Each file here is written into the new pack
at the same path, with `dot-` at the start of a name written as `.` and `{{key}}` replaced by the
pack's value (name, prefix, description, core_tag, facts). rule.md and facts.md are the bodies of
the pack's first rule and its facts skill; CLAUDE.md and GEMINI.md are written only for those
harnesses. Keep them short: the pack's README and AGENTS.md load into the context of whoever edits it.
