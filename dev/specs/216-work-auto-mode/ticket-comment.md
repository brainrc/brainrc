`/work <ref> --auto` now runs spec-agent without gate stops and ends with a draft PR. An ordered campaign with `--auto` ends with stacked draft PRs. Only the flag turns it on, and every hard stop (guardrails conditions, size `large`, plan Callouts, CRITICAL/HIGH security findings, untrusted instructions, live targets) still stops with nothing pushed. Ticket comments stay drafts.
Verify: `python3 -m unittest -v tests.test_evals.AutoCaseTest tests.test_evals.AutoCampaignCaseTest`.
PR: <PR_URL>
