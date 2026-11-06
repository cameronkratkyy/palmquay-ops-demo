---
name: match
description: Palmquay furnishing project (fictional demo): three-way match each supplier invoice against the approved order and what was received; flag price, quantity, and not-received differences for Finance. Never pays. Use for "/match <project>" or "check these invoices".
argument-hint: <project>
---

# /match: invoice vs. order vs. receipt

Operating policy is `CLAUDE.md` (section 10); every number comes from `company/rules.json` under `projects`. Demo date ("today") is **2026-11-05**; the order date is the request date.

## Steps
1. **Rules agree?** If a number in `CLAUDE.md` differs from `company/rules.json`, stop and say which. Don't pick one.
2. **Read the files yourself:** every file in `projects/<project>/invoices/`, the approved order, and `received/`. Note what you expect before running the helper.
3. **Run the helper** (it does the math and writes the files):
   ```
   python -I -X utf8 tools/project.py match <project>
   ```
   It writes `out/match.json` and `out/match.md` (per line: billed, ordered, received, flags; per invoice: result, billed, should be, difference) and appends exactly one row to `audit/procurement-log.csv`.
   - Exit 2 `UNREADABLE`: a file is missing or unreadable. Say which, and stop. Nothing was written.
   - Exit 3 `REFUSED`: this activity already ran (the log is append-only), or the log's hash chain is broken. Don't redo it and don't delete anything; tell the user.
4. **Compare** the helper's result with what you read in step 2. If you see a problem it didn't flag (or the reverse), stop and report it. Never hand-edit the outputs, the answer key, or the log.
5. **Report** in plain English: MATCH or HOLD per invoice, each flag (PRICE_MISMATCH, QTY_MISMATCH, NOT_RECEIVED), and the dollar difference. Finance approves payment; the assistant never marks anything paid.

Before Phase 3a is called done, the `compliance-checker` agent reviews every output blind (save its report under `reviews/procurement/`, then `python -I -X utf8 tools/project.py log-review <review>`).

## Limits
Never order, approve, sign, send, or pay. Never invent a measurement, price, date, or document. Fake data only.
