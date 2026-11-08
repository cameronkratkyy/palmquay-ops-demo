# Approval packet, version 2: Skyquay Lift & Fire Inc.

*Sample data for a demo (fictional company). Built by the onboarding assistant from version 1 (`vendors/skyquay-lift-fire/packet.md`), the e-signature export (`vendors/skyquay-lift-fire/esign-status-2026-11-10.md`), and company/rules.json. Nothing is approved until the people below sign. The assistant never voids, sends, signs, approves, or pays.*

| Field | Value |
|---|---|
| Vendor | Skyquay Lift & Fire Inc. |
| Version | 2 (replaces version 1) |
| Building | Bayfront Commons |
| Scope | Modernize 2 passenger elevators + fire-alarm tie-in |
| Contract amount | $120,000 |
| Approval tier | Over $50,000: 4 sign-offs, in order |
| Status | RESTART: signing starts again with the first approver |
| Built | 2026-11-08T17:24:04 by onboarding-assistant |

## What changed
| What | Version 1 | Version 2 | Asked for by |
|---|---|---|---|
| contract terms | as in version 1 | Add a one-year warranty on parts and labor to the contract terms before I sign. | Priya Natarajan, Legal, 2026-11-10 |

A change to the contract terms is a material change under company/rules.json, so version 1's signatures don't carry over: version 1 becomes void once a person voids it in the e-signature tool, and signing restarts with the first approver.

## Version 1: where signing stood on 2026-11-10
| # | Role | Name | Version 1 | Now |
|---|---|---|---|---|
| 1 | Facilities Manager | Dana Reyes | signed 2026-11-06 | needs to sign again on version 2 |
| 2 | Procurement Lead | Marcus Hale | signed 2026-11-09 | needs to sign again on version 2 |
| 3 | Legal | Priya Natarajan | change requested | signs version 2 in order |
| 4 | Finance | Tom Becker | not reached | signs version 2 in order |

## Sign-offs (version 2, in this order; each person signs after the one above)

| # | Role | Name | Email | Decision | Date | Signature |
|---|---|---|---|---|---|---|
| 1 | Facilities Manager | Dana Reyes | dana.reyes@palmquay.example |  |  |  |
| 2 | Procurement Lead | Marcus Hale | marcus.hale@palmquay.example |  |  |  |
| 3 | Legal | Priya Natarajan | priya.natarajan@palmquay.example |  |  |  |
| 4 | Finance | Tom Becker | tom.becker@palmquay.example |  |  |  |

Decision, Date and Signature are left blank on purpose: a person fills them in.

## What a person does next
1. Dana Reyes, Facilities Manager, voids version 1 in the e-signature tool and sends version 2.
2. Signing starts again in order: Dana Reyes, Marcus Hale, Priya Natarajan, then Tom Becker.
