# Log: aicfg-package
- intake: local ticket (owner chose it after #55). Baseline outputs captured in a fixed fake HOME before any change.
- spec: approved, package at the repo root. plan: approved.
- T1 split by script (deps scan, AST REPO rewrite); T2 tests/evals imports; the old-Python test caught a missing `import sys`. T3 before/after diff identical (600 lines). T4 docs, 0.3.20.
