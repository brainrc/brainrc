Bad harness and pack config now prints `ERROR <file>:<line>: <what>` and exits 1 before anything is written, for syntax errors, `claude = false`, and wrongly typed keys like `enabled = "false"`. Unknown keys and harness tables only the local file defines print a `WARN` with file and line. `aicfg doctor | head` exits quietly.
Verify: `python3 -m unittest -v tests.test_aicfg.ConfigErrorTest tests.test_aicfg.ClosedStdoutTest`.
PR: <PR_URL>
