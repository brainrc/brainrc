---
bump: patch
---
- spec-agent: the wave-timing rule (set `finished_at` per handoff, write all four
  `metrics.waves` fields before landing or retry) moves into SKILL.md's Implement stage. In
  efficiency.md alone, a v0.3.30 run of sandbox ticket 003 left `task_minutes` and
  `wall_minutes` null.
