# A stand-in for Gatework

The test suite's default pack: a few skills and agents with Gatework's names and placeholder
text, and a small validator plugin, so core's tests don't need the real Gatework
(brainrc/gatework). `copy_repo` in `tests/test_brainrc.py` installs it as `packs/gatework` in each
test's throwaway core and lists it in that core's `packs.toml`. Gatework's own content is tested
in its repo.
