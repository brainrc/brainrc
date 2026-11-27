---
bump: patch
---
- Copy mode (#177, epic #120): where a symlink can't be made (Windows without Developer Mode or
  admin rights), `apply` copies each skill, agent, command, hooks dir and instructions file and
  records the copy in `copies.json`. `link_mode` in `brainrc.local.toml` (`auto`, `symlink`,
  `copy`) or `BRAINRC_LINK_MODE` sets it. `status` and `doctor` show a copy whose source changed as
  `UPDATE` and one edited by hand as `EDITED`, which `apply` never overwrites and `uninstall`
  keeps as a backup. macOS and Linux still link, byte for byte as before.
