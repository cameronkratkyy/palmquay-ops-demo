# The operations dashboard (fictional company, fake data)

One offline page that shows the whole demo on one screen: what's waiting on people, every vendor, the furnishing project, the checks, and the audit log. It's built from the records in this folder: every number in its tiles and tables comes from a record and is recounted by a test. The Map tab's diagram is drawn by hand (`docs/diagram.html`).

**Open it:** double-click `dashboard/index.html`. It's a file on this PC: no server, no internet, no sign-in.
**Rebuild it** after any record changes: `python -I -X utf8 dashboard/build.py` (about 5 seconds; it also runs the Phase 1, 2, 3a, and 3c checks live).
**Pictures:** `python -I -X utf8 tools/render.py dashboard` saves one screenshot per tab as `dashboard/screenshot-<tab>.png`.

## The tabs
| Tab | What it shows | Industry term |
|---|---|---|
| Overview | The tiles, every decision waiting on a person (with options and the AI's suggestion), and every problem caught, by cause | Control tower, exception queue, failure analysis |
| Onboarding | Each vendor's status, blocker, screen, approvers, and days waiting; insurance and licenses that ended or end soon; conflict-of-interest and exclusion screening; the record behind each vendor | Pipeline tracking, compliance monitoring, vendor due diligence |
| Buying | The furnishing project's budget, the seven buying steps and what each caught, deliveries, invoices, what people already decided, and the controls from a real procurement packet (approval request, running totals, close-out) | Procure-to-pay (P2P), FF&E procurement, contract close-out |
| Checks | The phase checks for Phases 1, 2, 3a, and 3c, run when the page was built (3c without its own older-phase step, so the page and the Phase 3b check never call each other); the checker's reviews; guardrail counts | Acceptance testing, maker-checker review |
| Audit log | A replay that rebuilds the board from the three logs (onboarding, procurement, controls) one row at a time, the hash chains, and every row | Audit trail, event replay |
| Map | The one-page diagram (`docs/diagram.html`) | System architecture |

## Rules: what counts as "waiting on people"
A decision is listed when its record shows a person hasn't acted yet:
1. A follow-up draft exists for a vendor that is blocked or on hold, and the vendor's screen doesn't hold it: the reviewer named in the draft sends it.
2. An approval packet exists: the first approver signs, or, if the screen recused that approver, the approver who replaces them.
3. The project brief still needs information: the person who made the request answers.
4. A change request's "Approved by" line is still blank: its approver decides.
5. A client update draft exists: the Facilities Manager sends it.
6. A follow-up task exists: its owner does it.
7. Every invoice after the three-way match: Finance decides (pay a match, or settle a held invoice).
8. A vendor's screen is REVIEW: Legal reviews the disclosure.
9. A vendor's screen is EXCLUDED: Legal reviews (its follow-up is held, so rule 1 doesn't list it).
10. Each order line the approval request says needs a person's justification: the Facilities Manager writes it.
11. The approval request's certification is blank: its first approver signs.
12. Each draft reply to a supplier in `projects/unit-4b/controls/drafts/`: the Facilities Manager sends it.

"Since" is the date on the record that created the decision: a draft's or packet's date; for the screening decisions, the disclosure's signing date or the exclusion list's "as of" date; for the justifications and the certification, the date the order was approved; for a reply to a supplier, the date of the supplier's notice. The AI's suggestion is only a suggestion; the named person decides.

## Rule: the expiry list
Insurance certificates and licenses that ended before the demo date, or end within 60 days after it. Dates come from the documents themselves, not from the intake record.

## How the numbers are proven
`tests/check_phase3b.py` never imports this builder. It recounts every fact its own way and compares:
- every number in a tile or table carries a tag (`data-k`) naming the fact, and must equal the recount;
- every quote names its file (`data-src`) and must appear in that file word for word;
- every record shown in full (`<pre data-file>`) must equal the file;
- any other digit in a tile or table fails the check.
It also proves the page is offline, that building it changes no other file, that the replay ends where the records are, and that the page renders in a headless browser with no script errors.
