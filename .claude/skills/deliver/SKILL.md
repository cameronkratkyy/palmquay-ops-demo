---
name: deliver
description: Palmquay furnishing project (fictional demo): compare delivery tracking with the approved order, flag late deliveries and wrong addresses, open a follow-up task for each, and draft an update to the requester for a person to send. Use for "/deliver <project>" or "what's late?".
argument-hint: <project>
---

# /deliver: delivery exceptions, tasks, and a draft update

Operating policy is `CLAUDE.md` (section 10); every number comes from `company/rules.json` under `projects`. Demo date ("today") is **2026-11-05**; the order date is the request date.

## Steps
1. **Rules agree?** If a number in `CLAUDE.md` differs from `company/rules.json`, stop and say which. Don't pick one.
2. **Read the files yourself:** the latest `projects/<project>/deliveries/tracking-*.md`, `request.md` (install date), and the approved order (ship-to). Note what you expect before running the helper.
3. **Run the helper** (it does the math and writes the files):
   ```
   python -I -X utf8 tools/project.py deliver <project>
   ```
   It writes `out/deliveries.json`, `out/tasks.md` (owner + due date per exception), and `out/drafts/update-<date>.md` (a draft; not sent) and appends exactly one row to `audit/procurement-log.csv`.
   - Exit 2 `UNREADABLE`: a file is missing or unreadable. Say which, and stop. Nothing was written.
   - Exit 3 `REFUSED`: this activity already ran (the log is append-only), or the log's hash chain is broken. Don't redo it and don't delete anything; tell the user.
4. **Compare** the helper's result with what you read in step 2. If you see a problem it didn't flag (or the reverse), stop and report it. Never hand-edit the outputs, the answer key, or the log.
5. **Report** in plain English: each exception (DELIVERY_LATE with days late, ADDRESS_MISMATCH with both addresses), each task's owner and due date, lines already covered by a change request, and that the update is a draft for a person to send.

Before Phase 3a is called done, the `compliance-checker` agent reviews every output blind (save its report under `reviews/procurement/`, then `python -I -X utf8 tools/project.py log-review <review>`).

## Limits
Never order, approve, sign, send, or pay. Never invent a measurement, price, date, or document. Fake data only.
