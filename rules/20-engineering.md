# Engineering

- Test-first for behavior changes: failing test, minimal code to green, then tidy.
- Stay in scope: no drive-by refactors, renames, or formatting of unrelated code.
- New dependencies need a stated reason and the user's approval.
- Never weaken, skip, or delete tests, or suppress lint/type errors, to make checks pass.
- Search before reading (`rg`, globs), read line ranges, and keep long command output out of
  context (save to a file, read the summary).
