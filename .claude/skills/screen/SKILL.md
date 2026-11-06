---
name: screen
description: Palmquay vendor onboarding (fictional demo): screen every contractor's conflict-of-interest disclosure and check every name in its documents, plus every approved supplier, against the exclusion list. Routes conflicts and exclusions to Legal; recuses a related approver. Never approves. Use for "/screen" or "screen the vendors".
argument-hint: (none: screens all contractors and suppliers)
---

# /screen: conflict-of-interest disclosures + exclusion check

Operating policy is `CLAUDE.md` (section 11); every number and code comes from `company/rules.json` under `controls`. Demo date ("today") is **2026-11-05**. This control is copied from a real public-agency procurement packet (structure only; all data is fake).

## Steps
1. **Rules agree?** If `CLAUDE.md` section 11 and `company/rules.json` disagree, stop and say which.
2. **Read the files yourself:** each `vendors/<vendor>/disclosures/conflict-of-interest.md`, the vendor's W-9, insurance certificate, and license, `company/exclusion-list.md`, and `company/approved-suppliers.md`. Note what you expect first.
3. **Run the helper** (it matches names and dates exactly and writes the files):
   ```
   python -I -X utf8 tools/controls.py screen
   ```
   It writes `vendors/<vendor>/screen.json` for each contractor, `controls/supplier-screen.json`, and `controls/screen.md`, and appends exactly one row to `audit/controls-log.csv`.
   - Exit 2 `UNREADABLE`: a file is missing or unreadable. Say which, and stop.
   - Exit 3 `REFUSED`: it already ran, or the log's hash chain is broken. Don't redo it or delete anything; tell the user.
4. **Compare** with what you read in step 2. If you see something it missed (or the reverse), stop and report it. Never hand-edit an output, the answer key, or the log, and never change a Phase 1-3a record (intake, packet, draft, Stage).
5. **Report** in plain English: CLEAR, REVIEW, or EXCLUDED per vendor with its codes; who reviews (Legal); any recused approver and who signs instead; any follow-up draft that must be held.

## Limits
Never approve, sign, send, or pay. Never decide a conflict yourself: Legal does. Never invent a name, relationship, or date. Fake data only.
