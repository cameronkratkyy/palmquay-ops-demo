---
name: approve
description: Palmquay furnishing project (fictional demo): check each proposed product against its line in the design partner's plan (size, finish, fabric). Clear misses fail; anything the listing doesn't state goes to a person. Use for "/approve <project>" or "do these products fit the plan?".
argument-hint: <project>
---

# /approve: products against the plan

Operating policy is `CLAUDE.md` (section 10); every number comes from `company/rules.json` under `projects`. Demo date ("today") is **2026-11-05**; the order date is the request date.

## Steps
1. **Rules agree?** If a number in `CLAUDE.md` differs from `company/rules.json`, stop and say which. Don't pick one.
2. **Read the files yourself:** `projects/<project>/partner-plan.md` (max sizes, finish, fabric per line), `proposed.md`, and the catalogs. Note what you expect before running the helper.
3. **Run the helper** (it does the math and writes the files):
   ```
   python -I -X utf8 tools/project.py approve <project>
   ```
   It writes `out/approval.json` and `out/approval.md` (one row per line with the verdict and why) and appends exactly one row to `audit/procurement-log.csv`.
   - Exit 2 `UNREADABLE`: a file is missing or unreadable. Say which, and stop. Nothing was written.
   - Exit 3 `REFUSED`: this activity already ran (the log is append-only), or the log's hash chain is broken. Don't redo it and don't delete anything; tell the user.
4. **Compare** the helper's result with what you read in step 2. If you see a problem it didn't flag (or the reverse), stop and report it. Never hand-edit the outputs, the answer key, or the log.
5. **Report** in plain English: PASS, FAIL (TOO_WIDE, TOO_DEEP, FINISH_MISMATCH, FABRIC_MISMATCH, with the numbers), or NEEDS_PERSON (unclear: a named person decides). Never pass an unclear item.

Before Phase 3a is called done, the `compliance-checker` agent reviews every output blind (save its report under `reviews/procurement/`, then `python -I -X utf8 tools/project.py log-review <review>`).

## Limits
Never order, approve, sign, send, or pay. Never invent a measurement, price, date, or document. Fake data only.
