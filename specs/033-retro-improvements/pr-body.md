Apply the first five spec-agent retros and release 0.3.1

## Why
Five spec-agent runs on this repo hit the same friction: small docs tickets got an extra gate, the Deliver gate made code changes look missing, parallel release PRs conflicted on `VERSION`, retro timings mixed agent time with waiting for the user, a message contradicting the docs got past review, and fallback mode ran silently.

## What changed
- **Sizing** (`sizing.md`): about 30 changed lines or fewer score at most `small` on the files signal. New self-contained example or doc files count about half. Other signals and the floors still apply.
- **Parallel releases** (`lifecycle.md`): intake lists other open PRs that change `VERSION` or `CHANGELOG.md` and recommends waiting. Deliver re-checks and renumbers if one merged.
- **Fallback** (`lifecycle.md`): intake says when it runs in fallback and how to install the agents.
- **Deliver gate** (`lifecycle.md`): a `Changes:` diff stat outside `specs/` comes before the spec artifacts.
- **Timing** (`state.md`, `SKILL.md`, `templates/retro.md`): gates record `presented_at` and `approved_at`, and retros report agent time and gate waits separately. Runs without the fields still resume.
- **Review** (`agents/code-reviewer.md`): user-facing text the diff adds must agree with the docs.
- `VERSION` 0.3.1.

Blast radius: spec-agent behaviour on its next run. No pack contract change. spec-agent costs about 430 more tokens when used, and the always-loaded total is unchanged.

## Acceptance criteria
- [x] AC1: sizing by changed lines
- [x] AC2: Deliver gate lists code first
- [x] AC3: open-PR VERSION check at intake and Deliver
- [x] AC4: gate timestamps and split retro timing
- [x] AC5: reviewer checks messages against docs
- [x] AC6: fallback named at intake
- [x] AC7: short edits, tests and `validate` pass, 0.3.1

## How to verify
```
python3 scripts/aicfg.py validate
python3 scripts/aicfg.py tokens | grep spec-agent
```

## Follow-ups
- none

Spec: `specs/033-retro-improvements/spec.md` · Plan: `specs/033-retro-improvements/plan.md`
Closes #33

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01RzrsSqZwVeoS9SKY8ubQ8N
