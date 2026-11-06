---
name: closeout
description: Palmquay furnishing project (fictional demo): keep running totals for an approved order (invoiced, approved, paid, held, remaining), list every open item, check a supplier's completion notice against tracking and the receipt, and prepare a two-signature completion certificate left blank. Refuses false completion claims with a draft reply. Never signs, sends, or pays. Use for "/closeout <project>" or "can we close this order?".
argument-hint: <project>
---

# /closeout: running totals + a two-signature close-out

Operating policy is `CLAUDE.md` (section 11); every code comes from `company/rules.json` under `controls`. Copied from a real public-agency procurement packet (structure only; all data is fake).

## Steps
1. **Rules agree?** If `CLAUDE.md` section 11 and `company/rules.json` disagree, stop and say which.
2. **Read the files yourself:** the approved order, change requests, invoices, `out/match.json`, the receipt, tracking, `out/tasks.md`, and any notice in `closeout/`. Note what you expect first.
3. **Run the helper** (it does the totals and the item-by-item check):
   ```
   python -I -X utf8 tools/controls.py closeout <project>
   ```
   It writes `controls/contract-summary.json`, `controls/contract-summary.md`, `controls/completion-certificate.md`, and, when a supplier's claim is contradicted, `controls/drafts/reply-<supplier>-<date>.md` (not sent), all in the project folder (`out/` belongs to Phase 3a). It appends exactly one row to `audit/controls-log.csv`.
   - Exit 2 `UNREADABLE`: a file is missing or unreadable. Say which, and stop.
   - Exit 3 `REFUSED`: it already ran, or the log's hash chain is broken. Tell the user.
4. **Compare** with what you read. Never hand-edit the outputs, and never mark an item received, an invoice paid, or the order closed.
5. **Report**: the running totals, every open item, whether the supplier's completion claim holds, and why the close-out is or isn't ready. Both certificate signatures stay blank; the Facilities Manager sends any reply.

## Limits
Never sign, send, approve, or pay. Never call an item delivered without a receipt. Fake data only.
