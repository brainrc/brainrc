# Team conventions

These apply to every repo the team owns.

## Git

- Branch from `main`; keep commits small.
- Write the why in the commit body.

```sh
# A comment in a code block is not a heading
git log --oneline
```

## Testing

- Run the unit tests before every push.

### Flaky tests

Quarantine a flaky test in its own PR, never in a feature PR.

## Review

Ask for review once CI is green.
