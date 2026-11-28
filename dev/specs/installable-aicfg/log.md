# Log: installable-aicfg
- spec approved with option A (bundled). Prototype wheel: force-include works; the roles symlink becomes copies; hatchling `exclude` doesn't apply to force-include, so the code skips the copies instead.
- plan approved. T1 5 tests red; T2 installed mode; T3 pyproject + CI step (simulated in a venv); T4 real uv install: tokens differed (roles counted twice) → test red, fixed; relative pack paths found while documenting → test red, fixed; T5 docs, 0.3.22.
