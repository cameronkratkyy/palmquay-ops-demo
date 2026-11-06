---
name: intake
description: Palmquay Properties vendor intake (fictional demo). Reads one vendor's paperwork, applies company/rules.json, and records documents, issue codes, status (READY / HOLD / BLOCKED) and approvers in vendors/<slug>/intake.json, sets the vendor's Stage line, and adds one audit row. Use for "/intake <slug>", "/intake all", or "check this vendor's paperwork".
argument-hint: <vendor-slug | all>
---

# /intake: read the paperwork, find what's wrong

Operating policy is `CLAUDE.md`; every number comes from `company/rules.json`. Demo date ("today") is **2026-11-05**.

## Steps (one vendor at a time; for `all`, run them in folder order and skip any vendor that already has `intake.json`)

1. **Rules agree?** If a number in `CLAUDE.md` differs from `company/rules.json`, stop and say which. Don't pick one.
2. **Read the file yourself.** Read `vendors/<slug>/vendor.md` and every file in `vendors/<slug>/documents/`. Note which required documents are missing (W-9, certificate of insurance, work request, plus a state license for licensed trades). Don't guess what a missing document would say.
3. **Run the helper** (it does the date math, the dollar minimums, the name match and the approver tier):
   ```
   python -I -X utf8 tools/onboard.py intake <slug>
   ```
   It writes `vendors/<slug>/intake.json` with an evidence row for every rule it applied, sets the Stage line in `vendor.md` (the old value moves to a Stage history list), and appends exactly one audit row.
   - Exit 2 `UNREADABLE`: a document can't be read. Say which field, and stop for that vendor. Nothing was written.
   - Exit 3 `REFUSED`: intake already ran. Don't redo it and don't delete anything. Tell the user.
4. **Compare.** Check the helper's evidence against what you read in step 2. If you see a problem it didn't flag (or the reverse), stop and report it. Never hand-edit `intake.json`, the answer key, or the audit log.
5. **Report** one line per vendor: status, each issue in plain English, and the approvers for the contract amount's tier. Always list approvers, even for BLOCKED or HOLD ("who will approve once it's fixed").

## What the statuses mean (CLAUDE.md section 5)
- **READY**: every required document present and valid. Next: `/route`.
- **HOLD**: only "expires within 30 days" issues (COI_EXPIRING_30D, LICENSE_EXPIRING_30D). Next: `/chase` for renewal proof.
- **BLOCKED**: anything else. Next: `/chase`.

Before anything is called done, the `compliance-checker` agent reviews the results (see `/chase` step 7).

## Limits
Never approve, send, sign or pay. Never invent a document, number or date. Fake data only.
