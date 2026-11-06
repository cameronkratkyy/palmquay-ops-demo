---
name: status
description: Palmquay Properties onboarding status board (fictional demo). Prints one line per vendor with stage, status, blocker and days waiting. Read-only. Use for "/status", "where is everyone", or "who's blocked".
---

# /status: one line per vendor

Run:
```
python -I -X utf8 tools/onboard.py status
```

Show the table as printed, then add at most three short lines: how many are READY, HOLD and BLOCKED, and what the oldest wait is.

| Column | Where it comes from |
|---|---|
| Stage | the Stage line in `vendors/<slug>/vendor.md` (set by `/intake`, `/chase`, `/route`) |
| Status | `vendors/<slug>/intake.json` (`NOT REVIEWED` if intake hasn't run) |
| Blocker | the issue codes from `intake.json` (`none` if READY) |
| Days waiting | demo date (2026-11-05) minus the vendor's Submitted date |

Read-only: it writes nothing, so it adds no audit row (reading isn't an action under `CLAUDE.md` section 8). Fake data only.
