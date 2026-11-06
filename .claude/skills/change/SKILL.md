---
name: change
description: Palmquay furnishing project (fictional demo): price a supplier substitution against the approved baseline order (cost, budget, delivery date) and write a change request that waits for a person. The baseline file never changes before approval. Use for "/change <project>" or "what does this backorder do to the budget?".
argument-hint: <project>
---

# /change: price the change, hold the baseline

Operating policy is `CLAUDE.md` (section 10); every number comes from `company/rules.json` under `projects`. Demo date ("today") is **2026-11-05**; the order date is the request date.

## Steps
1. **Rules agree?** If a number in `CLAUDE.md` differs from `company/rules.json`, stop and say which. Don't pick one.
2. **Read the files yourself:** `projects/<project>/approved/po-PQ-1042.md` (the baseline), the supplier notice in `events/`, and the catalogs. Note what you expect before running the helper.
3. **Run the helper** (it does the math and writes the files):
   ```
   python -I -X utf8 tools/project.py change <project>
   ```
   It writes `out/change-request-CR-001.json` and `.md` (old vs. new item, date, total, budget, approvers, the baseline's hash before and after) and appends exactly one row to `audit/procurement-log.csv`.
   - Exit 2 `UNREADABLE`: a file is missing or unreadable. Say which, and stop. Nothing was written.
   - Exit 3 `REFUSED`: this activity already ran (the log is append-only), or the log's hash chain is broken. Don't redo it and don't delete anything; tell the user.
4. **Compare** the helper's result with what you read in step 2. If you see a problem it didn't flag (or the reverse), stop and report it. Never hand-edit the outputs, the answer key, or the log.
5. **Report** in plain English: the cost of the change, the new total vs. the budget (OVER_BUDGET if over), the new delivery date, and who must approve. Say plainly that the baseline is unchanged.

Before Phase 3a is called done, the `compliance-checker` agent reviews every output blind (save its report under `reviews/procurement/`, then `python -I -X utf8 tools/project.py log-review <review>`).

## Limits
Never order, approve, sign, send, or pay. Never invent a measurement, price, date, or document. Fake data only.
