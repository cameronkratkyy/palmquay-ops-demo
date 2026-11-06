---
name: chase
description: Palmquay Properties follow-up drafts (fictional demo). For each BLOCKED or HOLD vendor, writes one polite draft email to vendors/<slug>/drafts/ saying what's missing or failing, why it's required, the 7-day deadline, and how to send it. Drafts only; nothing is sent. Use for "/chase <slug>", "/chase all", or "draft the follow-ups".
argument-hint: <vendor-slug | all>
---

# /chase: draft the follow-up (a person sends it)

Drafts only. The assistant has no email tool and never sends anything. Dana Reyes (Facilities Manager) reviews and sends every email (`CLAUDE.md` section 7).

## Steps (per vendor)

1. **Only BLOCKED or HOLD.** Read `vendors/<slug>/intake.json`. READY vendors have nothing to chase (use `/route`). No `intake.json`? Run `/intake` first.
2. **Get the facts** (don't retype them by eye):
   ```
   python -I -X utf8 tools/onboard.py facts <slug>
   ```
   It prints the vendor's `.example` contact, the sender, the deadline (demo date + `chase_deadline_days` = **2026-11-12**), the building and scope, and, for each issue, what intake found.
3. **Write the draft** to `vendors/<slug>/drafts/2026-11-05-follow-up.md` using the template below. One numbered item per issue code, no more, no fewer. Each item says what we need, what we found (the exact date, amount or names from step 2), and a **Why we need it:** line from the table below.
4. **Tone.** Short, polite, specific. No threats, no legal language, no "final notice". Don't ask for anything that isn't an issue code. Don't mention any date or dollar amount that isn't in the vendor's documents or the rules.
5. **Lint it** and fix until it reports 0 problems:
   ```
   python -I -X utf8 tools/onboard.py lint-draft vendors/<slug>/drafts/2026-11-05-follow-up.md
   ```
6. **Log it** (sets the Stage line and appends one audit row with result "drafted, not sent"):
   ```
   python -I -X utf8 tools/onboard.py log-draft vendors/<slug>/drafts/2026-11-05-follow-up.md
   ```
7. **Checker review before done.** Ask the `compliance-checker` agent to review the intake results, drafts and packets. It's read-only, so save its report word for word in `reviews/<date>-<nn>-<scope>.md` with the SHA-256 table from `tools/onboard.py manifest <files...>`. Then log it with `tools/onboard.py log-review <record>`. Any finding on a real file means fix it and review again. It isn't done until then.

## Why each item is required (from CLAUDE.md sections 2-4)
| Code | Why we need it |
|---|---|
| MISSING_W9 | Palmquay Properties requires a W-9 from every vendor; it confirms the legal name and taxpayer ID on file. |
| MISSING_COI | Every vendor needs a certificate of insurance on file before work is approved. |
| MISSING_LICENSE | Licensed trades (HVAC, roofing, electrical, plumbing, pest control, elevator/fire) need a current state license on file. |
| MISSING_REQUEST | Each job needs a work request (building, scope, amount) so the right people can approve it. |
| COI_EXPIRED | Our policy requires current insurance on file; an expired certificate stops the approval. |
| COI_EXPIRING_30D | A certificate that ends within 30 days puts the file on hold until we have the renewal. |
| LICENSE_EXPIRED | Our policy requires a current state license for this trade; an expired license stops the approval. |
| LICENSE_EXPIRING_30D | A license that ends within 30 days puts the file on hold until we have proof of renewal. |
| GL_BELOW_MIN | Our minimum for every vendor is $1,000,000 per occurrence and $2,000,000 aggregate. |
| AUTO_BELOW_MIN | Our minimum auto liability for every vendor is $1,000,000. |
| UMBRELLA_MISSING | Roofing and elevator/fire work need an umbrella policy of at least $5,000,000. |
| WC_MISSING | Every vendor needs workers' comp at statutory limits, or a valid exemption certificate. |
| NO_ADDITIONAL_INSURED | Our policy requires Palmquay Properties to be named as an additional insured. |
| NAME_MISMATCH | The legal name must match on the W-9, the certificate's Insured line and the license, so we know all three cover the same company. |

## Template (keep the headings and field names exactly)
```
# Draft follow-up email: <Legal name>

*Fake data for a demo. DRAFT ONLY: the assistant never sends email. Dana Reyes (Facilities Manager) reviews and sends it.*

| Field | Value |
|---|---|
| Status | DRAFT, not sent |
| To | <contact from facts> |
| From | dana.reyes@palmquay.example |
| Reviewer and sender | Dana Reyes, Facilities Manager |
| Subject | <short and specific, includes the deadline> |
| Issue codes | <codes from intake.json, comma separated> |
| Deadline | 2026-11-12 |
| Drafted | 2026-11-05 by onboarding-assistant from vendors/<slug>/intake.json |

## Message

Hello <Legal name> team,

<One sentence: thanks, and which job (building + scope).> <One sentence: what's left before we can move ahead.>

## What we need

1. **<What we need, in a few words.>** <What we found, with the exact date, amount or names.>
   **Why we need it:** <reason from the table above>

## Deadline and how to send it

Please send it by **2026-11-12** (one week from today). Reply to this email with the document attached (a PDF is fine), or send it to dana.reyes@palmquay.example. <If HOLD: say the file is on hold, not closed.>

If anything here looks wrong, just reply and we'll sort it out.

Thank you,
Dana Reyes
Facilities Manager, Palmquay Properties
dana.reyes@palmquay.example
```

## Limits
Never send, approve, sign or pay. Never invent a fact. Contacts are `.example` addresses, which can't receive mail. Fake data only.
