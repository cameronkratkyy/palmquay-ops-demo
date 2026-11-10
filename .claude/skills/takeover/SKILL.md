---
name: takeover
description: Palmquay Properties tenant takeover (fictional demo, Phase 3g). When a new owner's home already has a tenant, compares the lease's security deposit with what the previous holder transferred, writes takeover.json, and drafts either an email to the outgoing manager (a receipt for what came, and a request for the full accounting) or the management-change letter to the tenant. Nothing is sent and no money moves. Use for "/takeover <owner | all>" or "check the tenant's deposit".
---
# /takeover: a tenant already lives there

**Why (the real office):** Florida law (Fla. Stat. 83.49(7)) says that when the rental agent changes, the tenants' deposits move to the new agent "with an accurate accounting showing the amounts to be credited to each tenant account." If less comes over than the lease says, the new manager records what it got and finds the rest; it doesn't book the lease number as cash.

1. **Run it:** `python -I -X utf8 tools/owners.py takeover <owner | all>`. Only owners whose form says a tenant lives there are read.
2. **Deposit math:** the lease's security deposit against the transfer statement's. Equal is MATCH; less is DEPOSIT_SHORT; more is DEPOSIT_OVER. Both amounts are recorded now; only "reconciled" waits.
3. **If it matches:** draft the management-change letter for the Property Manager. It has two clocks: who receives notices for the landlord (Fla. Stat. 83.50), how to pay rent, and how to ask for repairs go out by the management start date; the deposit notice (where it's held, the depository's address, no interest) is due 30 days after the deposit moved (Fla. Stat. 83.49(2), where it applies; counsel decides, and Palmquay sends it either way). It's marked not ready to send until counsel's 83.49(2)(d) wording is in.
4. **If it doesn't:** draft an email for the Trust Accountant to the outgoing holder: a written receipt for the amount received only, and a request for the complete tenant accounting, any adjustments the tenant authorized, and the rest if it's owed. No tenant letter yet.
5. A ready leasing gate here means the packet review is done; the Property Manager signs only after the outside takeover review (amendments, ledger, paid-through date, arrears, notices, repairs).
6. One row per owner in `audit/owners-log.csv`; a second run is refused.

Nothing is sent, and no money moves: the Trust Accountant confirms what the bank actually received.
