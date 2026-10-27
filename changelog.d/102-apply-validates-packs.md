---
bump: patch
---
- `apply` and `status` run the checks `validate --pack` runs on each enabled pack before linking anything. A pack skill without the pack's prefix, or any other pack error, is printed and nothing is written. Before, `apply` linked it and exited 0 (gh:102).
