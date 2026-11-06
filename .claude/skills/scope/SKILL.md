---
name: scope
description: Palmquay furnishing project (fictional demo): turn the requester's furnishing request into a structured project brief, list missing measurements, and flag requirements that conflict with the room (a bed that doesn't fit). Use for "/scope <project>" or "build the brief for unit 4B".
argument-hint: <project>
---

# /scope: from request to project brief

Operating policy is `CLAUDE.md` (section 10); every number comes from `company/rules.json` under `projects`. Demo date ("today") is **2026-11-05**; the order date is the request date.

## Steps
1. **Rules agree?** If a number in `CLAUDE.md` differs from `company/rules.json`, stop and say which. Don't pick one.
2. **Read the files yourself:** `projects/<project>/request.md` (every line) and `partner-plan.md`. Note what you expect before running the helper.
3. **Run the helper** (it does the math and writes the files):
   ```
   python -I -X utf8 tools/project.py scope <project>
   ```
   It writes `out/brief.json` (with `_measurements` in inches) and `out/brief.md` (every request field, flags, and one question for the requester) and appends exactly one row to `audit/procurement-log.csv`.
   - Exit 2 `UNREADABLE`: a file is missing or unreadable. Say which, and stop. Nothing was written.
   - Exit 3 `REFUSED`: this activity already ran (the log is append-only), or the log's hash chain is broken. Don't redo it and don't delete anything; tell the user.
4. **Compare** the helper's result with what you read in step 2. If you see a problem it didn't flag (or the reverse), stop and report it. Never hand-edit the outputs, the answer key, or the log.
5. **Report** in plain English: status (READY or NEEDS_INFO), each missing measurement, each conflict with the numbers (bed width + 24 in each side vs. the wall), and the one question to send (a person sends it).

Before Phase 3a is called done, the `compliance-checker` agent reviews every output blind (save its report under `reviews/procurement/`, then `python -I -X utf8 tools/project.py log-review <review>`).

## Limits
Never order, approve, sign, send, or pay. Never invent a measurement, price, date, or document. Fake data only.
