---
name: auto-cron
description: "Auto-crystallized skill triggered by 8x cron calls (100% success across 2 sessions). Pattern: \"{\"action\":\"add\",\"job\":{\"name\":\"GO2SE-CronGuardian防...\""
metadata:
  openclaw:
    category: general
    aceforge:
      status: proposed
      proposed: 2026-03-29T12:25:21.249Z
      auto_generated: true
      candidate_occurrences: 8
      candidate_success_rate: 1
      first_seen: 2026-03-28T15:20:24.409Z
---

# auto-cron

## When to Use

Use this skill when you need to run: cron

## Detected Pattern

Arguments matching: {"action":"add","job":{"name":"GO2SE-CronGuardian防...

## Instructions

1. Execute the `cron` tool with arguments matching the pattern above
2. Expected success rate: 100%
3. First observed: 2026-03-28T15:20:24.409Z

## Anti-Patterns

- Do NOT use if arguments don't match the detected pattern
- Do NOT use if context has changed significantly
- Do NOT use if error rate is elevated since 2026-03-28T15:20:24.409Z