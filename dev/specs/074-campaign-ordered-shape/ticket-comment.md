Shipped the ordered campaign shape. `/work --campaign` on an epic of dependent children builds them in dependency order, with Spec and Plan gates per child, one Deliver gate for the stack, and PRs opened one at a time as each predecessor merges.
Verify: `python3 -m unittest tests.test_evals.CampaignCheckTest -v`. No ordered campaign has run end to end yet. The sandbox epic `local:tickets/004-greeting-epic.md` (in `examples/sandbox`) is the first planned run.
PR: <PR_URL>
