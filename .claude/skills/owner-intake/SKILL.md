---
name: owner-intake
description: Palmquay Properties new-owner intake (fictional demo, Phase 3g). Reads a new property owner's packet (owners/<slug>/) and the county record the coordinator saved, applies company/owner-rules.json, and writes intake.json with every problem, the document that shows it, and which of the three approval gates it blocks. Nothing is sent, signed, or entered in any software. Use for "/owner-intake <owner | all>" or "check the new owner's paperwork".
---
# /owner-intake: read the new owner's packet, find what's missing or doesn't match

**Why (the real office):** when a homeowner hires a manager, the manager can't collect rent or pay the owner until it knows who owns the home, who signed, where the owner's money goes, how the home is insured, and what the tenant already paid. Someone reads every page and compares names across documents. That's this step.

1. **Read the rules first:** `company/owner-rules.json` (codes, the five kinds of problem, the gates) and `company/owner-team.md` (who decides). Demo date 2026-11-05.
2. **Run it:** `python -I -X utf8 tools/owners.py intake <owner | all>`. For each owner it checks: every required document is there; the agreement's owner is the county record's owner, and every owner on the record signed; a W-9 (or, for a foreign owner, a referral to the Controller and the owner's tax adviser, never a form chosen by the AI); the bank account is in the owner's name; a landlord policy with $300,000 liability naming Palmquay Properties as additional insured; the association's lease rules; the lead-paint form for a home built before 1978; and, if a tenant lives there, the lease deposit against what came over.
3. **Say which kind each problem is:** not provided, provided but incomplete, two documents disagree, needs a professional's decision, or waiting on an outside approval. Quote the document for each one.
4. **The county record is one a person saved to the folder.** The AI compares names; it doesn't look anything up, and it never calls a title, a bank account, coverage, or a deposit "verified."
5. **Report** one line per owner: READY, HOLD, or BLOCKED, the codes, and each gate's state. Each owner adds one row to `audit/owners-log.csv` (hash-chained); a second run is refused.

Nothing is sent, signed, or entered in any software.
