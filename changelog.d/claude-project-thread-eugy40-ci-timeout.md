---
bump: patch
---
- CI: the Windows `validate` jobs get 15 minutes instead of 10. Their tests take about 8 minutes,
  so a slow runner was hitting the limit and cancelling the job; other platforms keep 10.
