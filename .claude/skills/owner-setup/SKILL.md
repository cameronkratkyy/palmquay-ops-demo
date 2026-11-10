---
name: owner-setup
description: Palmquay Properties setup sheet (fictional demo, Phase 3g). Drafts one sheet per new owner with every field a person types into the property management software (owner, tax form, where payouts go, property, agreement, any tenant and deposit), each with the record it came from, the open problems, and four blank sign-offs. Nothing is sent or entered in any software. Use for "/owner-setup <owner | all>" or "draft the setup sheets".
---
# /owner-setup: the draft setup sheet

**Why (the real office):** after the paperwork, someone types the owner and the property into the management software (for example AppFolio or Buildium; named as examples only). Retyping from eight documents is where wrong bank numbers and wrong owner names creep in. A sheet with each field and its source makes that entry a copy, and shows what isn't ready yet. A restricted draft record can be made earlier, with each function turned on as its gate clears.

1. **Run it:** `python -I -X utf8 tools/owners.py setup <owner | all>` after `/owner-intake` (and `/takeover` for a home with a tenant).
2. **Fields come from the records,** each with its source file. The bank account shows the last 4 digits only. "Owner payouts" stay held until the Trust Accountant confirms the account by calling the owner at a number Palmquay already had or confirmed separately (not only the one in the packet) and records how.
3. **A tenant's deposit is recorded now:** owed per the lease, received, and the difference; only "reconciled" waits. The sheet also lists what a person still reviews at takeover (amendments, ledger, paid-through date, arrears, notices, repairs).
4. **Four sign-offs, blank:** Management accepted (Broker of Record), Accounting approved (Trust Accountant), Leasing-ready or takeover complete (Property Manager), Entered in the software by a person (Owner Onboarding Coordinator, after the other three). For each gate the AI writes what it found: "Nothing blocking," "Blocked: CODE," or "On hold: CODE." It never signs.
5. One row per owner in `audit/owners-log.csv`; a second run is refused.

Nothing is sent, and nothing is entered in any software: the AI doesn't connect to any.
