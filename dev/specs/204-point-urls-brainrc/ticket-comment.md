Draft PR: <PR_URL>

Install commands and issue links in README.md and docs/ now name `brainrc/brainrc`, and pyproject.toml has `[project.urls]`. The plugin manifests carry no repo URL, so regenerating them changes nothing. The grep from "Done when" finds nothing; validate and the test suite pass.
