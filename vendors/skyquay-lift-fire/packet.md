# Approval packet: Skyquay Lift & Fire Inc.

*Fake data for a demo. Built by the onboarding assistant from the vendor's documents and company/rules.json. Nothing is approved until the people below sign. The assistant never approves, signs, or pays.*

| Field | Value |
|---|---|
| Vendor | Skyquay Lift & Fire Inc. |
| Trade | elevator_fire |
| Building | Bayfront Commons |
| Scope | Modernize 2 passenger elevators + fire-alarm tie-in |
| Contract amount | $120,000 |
| Requested by | Dana Reyes |
| Target start | 2026-12-01 |
| Intake status | READY (0 issues), checked against company/rules.json for 2026-11-05 |
| Approval tier | Over $50,000: 4 sign-offs, in order |
| Built | 2026-11-05T11:31:17 by onboarding-assistant |

## What intake checked

| Check | Source | Found | Rule | Result |
|---|---|---|---|---|
| W-9 on file | documents/w9.md | present | required from every vendor | ok |
| certificate of insurance on file | documents/coi.md | present | required from every vendor | ok |
| work request on file | documents/request.md | present | required from every vendor | ok |
| state license on file | documents/license.md | present | required for licensed trades (elevator_fire) | ok |
| insurance end date | documents/coi.md: Policy end | 2027-03-01 (116 days from 2026-11-05) | not before 2026-11-05; 30 days or fewer out = hold | ok |
| general liability | documents/coi.md | $1,000,000 / $2,000,000 | at least $1,000,000 per occurrence / $2,000,000 aggregate | ok |
| auto liability | documents/coi.md | $1,000,000 | at least $1,000,000 | ok |
| umbrella | documents/coi.md | $5,000,000 | at least $5,000,000 for elevator_fire (high-risk trade) | ok |
| workers' comp | documents/coi.md | Statutory | Statutory or a valid exemption certificate | ok |
| additional insured | documents/coi.md | Palmquay Properties | must name Palmquay Properties | ok |
| license end date | documents/license.md: Expires | 2027-08-31 (299 days from 2026-11-05) | not before 2026-11-05; 30 days or fewer out = hold | ok |
| legal name matches everywhere | vendor.md, w9.md, coi.md, license.md | vendor.md: Skyquay Lift & Fire Inc.; w9.md: Skyquay Lift & Fire Inc.; coi.md: Skyquay Lift & Fire Inc.; license.md: Skyquay Lift & Fire Inc. | same legal name on the vendor record, W-9, certificate and license | ok |

## Sign-offs (in this order; each person signs after the one above)

| # | Role | Name | Email | Decision | Date | Signature |
|---|---|---|---|---|---|---|
| 1 | Facilities Manager | Dana Reyes | dana.reyes@palmquay.example |  |  |  |
| 2 | Procurement Lead | Marcus Hale | marcus.hale@palmquay.example |  |  |  |
| 3 | Legal | Priya Natarajan | priya.natarajan@palmquay.example |  |  |  |
| 4 | Finance | Tom Becker | tom.becker@palmquay.example |  |  |  |

Decision, Date and Signature are left blank on purpose: a person fills them in. The next approver is notified by a person, not by the assistant.
