---
name: source
description: Palmquay furnishing project (fictional demo): check every proposed product's lead time against the install date, flag what can't arrive in time, and name the cheapest in-spec, in-time alternative from an approved supplier. Use for "/source <project>" or "what can't arrive in time?".
argument-hint: <project>
---

# /source: lead times vs. the install date

Operating policy is `CLAUDE.md` (section 10); every number comes from `company/rules.json` under `projects`. Demo date ("today") is **2026-11-05**; the order date is the request date.

## Steps
1. **Rules agree?** If a number in `CLAUDE.md` differs from `company/rules.json`, stop and say which. Don't pick one.
2. **Read the files yourself:** `projects/<project>/request.md` (request date, install date), `proposed.md`, `partner-plan.md`, every catalog, and `company/approved-suppliers.md`. Note what you expect before running the helper.
3. **Run the helper** (it does the math and writes the files):
   ```
   python -I -X utf8 tools/project.py source <project>
   ```
   It writes `out/source.json` and `out/source.md` (one row per item: lead time, arrival date, result) and appends exactly one row to `audit/procurement-log.csv`.
   - Exit 2 `UNREADABLE`: a file is missing or unreadable. Say which, and stop. Nothing was written.
   - Exit 3 `REFUSED`: this activity already ran (the log is append-only), or the log's hash chain is broken. Don't redo it and don't delete anything; tell the user.
4. **Compare** the helper's result with what you read in step 2. If you see a problem it didn't flag (or the reverse), stop and report it. Never hand-edit the outputs, the answer key, or the log.
5. **Report** in plain English: each late item with its arrival date and days late, and the in-time alternative. A person chooses between late-but-preferred and on-time.

Before Phase 3a is called done, the `compliance-checker` agent reviews every output blind (save its report under `reviews/procurement/`, then `python -I -X utf8 tools/project.py log-review <review>`).

## Limits
Never order, approve, sign, send, or pay. Never invent a measurement, price, date, or document. Fake data only.
