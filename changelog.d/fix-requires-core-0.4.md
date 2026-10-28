---
bump: patch
---
- The example pack accepts core 0.4 (`requires_core = ">=0.3, <0.5"`), and the pack examples in
  docs/tutorial.md and docs/packs.md pin `>=0.4, <0.5`. The 0.4.0 bump left them at `<0.4`, so
  `validate --pack examples/pack-acme` failed and a pack copied from the tutorial was rejected.
