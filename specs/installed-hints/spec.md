# Spec: hints name the command you actually run

Ticket: local · Size: small (~30 lines in doctor/config/cli, no new contract) · Status: draft

## Acceptance criteria
- **AC1** Installed (`aicfg/_core` present), every `doctor` fix hint and the usage text say
  `aicfg <command>`; from a checkout they say `python3 scripts/aicfg.py <command>` exactly as
  today (the checkout transcript is unchanged).
- **AC2** `plugin`'s hints stay `python3 scripts/aicfg.py plugin` (it only runs from a checkout).
- **AC3** A test covers both modes; README drops the "hints show the checkout command" caveat;
  CHANGELOG, VERSION 0.3.24.
