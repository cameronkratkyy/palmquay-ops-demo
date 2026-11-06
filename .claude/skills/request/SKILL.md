---
name: request
description: Palmquay furnishing project (fictional demo): fill in the procurement approval request for an order: procurement type by dollar amount, purpose, funding line, per-line competition (quotes required by dollar size), justifications, and a blank certification for the approver. Never writes a justification a person owes and never signs. Use for "/request <project>" or "prepare the approval request".
argument-hint: <project>
---

# /request: the procurement approval request

Operating policy is `CLAUDE.md` (section 11); every number and code comes from `company/rules.json` under `controls`. This form is copied from a real public-agency procurement packet (structure only; all data is fake).

## Steps
1. **Rules agree?** If `CLAUDE.md` section 11 and `company/rules.json` disagree, stop and say which.
2. **Read the files yourself:** the approved order, `funding.md`, `request.md`, the design partner's plan, the supplier catalogs, `out/source.json`, and `out/approval.json`. Note what you expect first.
3. **Run the helper** (it does the dollar tiers, spec matching, and totals):
   ```
   python -I -X utf8 tools/controls.py request <project>
   ```
   It writes `controls/approval-request.json` and `controls/approval-request.md` (in the project folder; `out/` belongs to Phase 3a) and appends exactly one row to `audit/controls-log.csv`.
   - Exit 2 `UNREADABLE`: a file is missing or unreadable. Say which, and stop.
   - Exit 3 `REFUSED`: it already ran, or the log's hash chain is broken. Tell the user.
4. **Compare** with what you read. A LOWEST_NOT_SELECTED line gets a reason only if a record shows it; a SINGLE_SOURCE line always goes to the Facilities Manager. Never hand-edit the outputs.
5. **Report**: the procurement type and what it requires, the funding line and what's left, each flagged line, and which justifications a person still owes. The certification stays blank for the approver.

## Limits
Never order, approve, sign, send, or pay. Never write a justification a person owes. Never invent a price, supplier, or reason. Fake data only.
