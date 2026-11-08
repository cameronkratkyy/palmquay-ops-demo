---
name: credit
description: Palmquay furnishing project (fictional demo): compare the approved order's promised dates with the latest tracking, and for any item 7 days or more past its promised date, draft a polite request asking that supplier to credit 50% of its freight. Drafts only; the Facilities Manager reviews, may change the amount, and sends. Use for "/credit <project>" or "the bed frame is a week late, can we get shipping back?".
argument-hint: <project>
---

# /credit: a shipping credit for a late delivery

Operating policy is `CLAUDE.md` (section 12); every number comes from `company/rules.json` under `exceptions`.

## Steps
1. **Rules agree?** If `CLAUDE.md` section 12 and `company/rules.json` disagree, stop and say which.
2. **Read the files yourself:** the approved order (promised dates, freight by supplier), the latest tracking file, the install date, and the approved-supplier list. Note which items you expect to qualify.
3. **Run the helper** (it does the day counts and the credit math):
   ```
   python -I -X utf8 tools/exceptions.py credit <project>
   ```
   It writes `exceptions/freight-credit.json` and one `exceptions/credit-request-<supplier>-<date>.md` per supplier (not sent) in the project folder, and appends exactly one row to `audit/exceptions-log.csv`.
   - Exit 2 `UNREADABLE`: a file is missing or unreadable. Say which, and stop.
   - Exit 3 `REFUSED`: it already ran, or the log's chain is broken. Tell the user.
4. **Compare** with what you expected. The ask is an opening request, not something the supplier owes: keep it polite and specific, with no threats or legal language.
5. **Report**: each late item, days past its promised date, the supplier's freight, the credit asked, and who sends the draft.

## Limits
Never send, order, approve, or pay. Fake data only.
