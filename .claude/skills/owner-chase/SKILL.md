---
name: owner-chase
description: Palmquay Properties new-owner follow-ups (fictional demo, Phase 3g). For each owner whose intake isn't READY, drafts one short, specific email that asks for every missing or mismatched item, says why in plain words, and gives a 7-day deadline. The Owner Onboarding Coordinator reviews and sends each one; nothing is sent by the AI. Use for "/owner-chase <owner | all>" or "draft the owner follow-ups".
---
# /owner-chase: one follow-up per stuck owner

**Why (the real office):** most owner onboarding stalls on the owner: a second owner who hasn't signed, a tax form, the wrong bank account, an insurance change only their agent can make. One clear email listing everything at once beats three emails a week apart.

1. **Read** `owners/<slug>/intake.json`. READY owners get no email.
2. **Run it:** `python -I -X utf8 tools/owners.py chase <owner | all>`. One draft per owner in `owners/<slug>/drafts/`, addressed to the owner's `.example` address, from Talia Brooks (Owner Onboarding Coordinator).
3. **Each item says** what we need, what the documents show, and why we need it, in the owner's terms. A foreign owner is asked to choose the tax form with their own tax adviser; the AI never picks it. An owner on hold for an association is told nothing is missing, only that the association approves each lease.
4. **Deadline:** 7 days after the demo date (2026-11-12). Polite, specific, no threats, no legal language beyond naming the rule.
5. One row per owner in `audit/owners-log.csv`; a second run is refused.

Drafts only: nothing is sent. The coordinator reviews, edits if needed, and sends.
