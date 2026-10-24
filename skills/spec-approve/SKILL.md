---
name: spec-approve
description: Approve the pending spec-agent gate and continue
argument-hint: [optional notes]
disable-model-invocation: true
---

Using the `spec-agent` skill: approve the gate currently awaiting approval for the spec on
this branch. Record it in `state.json`, then continue the run. Notes to apply first, if any:
$ARGUMENTS

If no gate is pending, say so and do nothing. At deliver with `state.quiz` not `passed`, reply
"the Understand quiz comes first" and continue the quiz.

If `$ARGUMENTS` appears literally above, this tool didn't fill it in: use what the user typed
with this skill instead.
