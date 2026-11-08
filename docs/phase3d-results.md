# Phase 3d results: real-world exceptions (11/8/2026)

*Fictional company, sample records. Asked for by the author after reviewing the video script: the demo's problems should feel like real life, so a firm asking "what happens if...?" sees the system already thinking ahead.*

## How the two exceptions were picked
Two research assistants were asked the same question: the 3 to 5 most common exceptions in contractor approvals at property management companies and in furniture buying for apartment turnovers, how a good process handles each, and what an AI can safely do. Neither gave measured frequencies; both called a backorder followed by a pricier substitute realistic (so that scene stays), both said a material change mid-approval means the earlier signers sign again, and both said asking a supplier for part of the shipping back is a normal ask but not a standard entitlement or percentage. The author picked two to build and two for the video's closing line (tariff charges that weren't on the order, damaged deliveries), which the demo does not claim to handle.

## What was built
| Piece | What it does |
|---|---|
| `company/rules.json` `exceptions`, `CLAUDE.md` section 12 | The rules: which changes are material (scope, price, dates, contract terms, insurance); signing restarts from the first approver; a credit request when an item is 7 days or more past its promised date, asking for 50% of that supplier's freight |
| `vendors/skyquay-lift-fire/esign-status-2026-11-10.md` | The one new input: an e-signature export. Dana Reyes signed version 1 on 2026-11-06, Marcus Hale on 2026-11-09, then Priya Natarajan asked to add a one-year warranty |
| `tools/exceptions.py` + `/revise`, `/credit` | The helper and the two skills. Each step runs once, writes new files only, and appends one row to `audit/exceptions-log.csv` (hash-chained) |
| `vendors/skyquay-lift-fire/packet-v2.md`, `revision.json` | Version 2: the change word for word, both earlier signers marked to sign again, 4 sign-offs blank in tier order; version 1 untouched |
| `projects/unit-4b/exceptions/freight-credit.json`, `credit-request-gulfweave-2026-11-12.md` | The queen bed frame (GW-BED-Q) is 7 days past its promised 2026-11-18; the draft asks Gulfweave Furnishings for $92.50, half its $185 freight, for Dana Reyes to review and send |
| `dashboard/build.py` | Two new decisions waiting on Dana, the "A change during sign-off" and "Shipping credit for a late delivery" sections, the fourth log in the replay and hash-chain table, Phase 3d on the Checks tab |
| `tests/check_phase3b.py` | Extended, not loosened: recounts the new waiting rows, drafts, blank sign-offs, the fourth log, and the three new facts on the page |

## Test-first record
- Rules, CLAUDE.md section 12, the e-signature export, a hand-written answer key, and hashes of 154 earlier records were locked in `tests/LOCK.txt` before `tools/exceptions.py` existed.
- `tests/check_phase3d.py` was written next. First run: **4 of 12** (the lock, the recount against the key, the skipped older-phase step, and the sample label).
- A dry run on a throwaway copy matched the key; a second run was refused (append-only). Then the real run.
- The first dashboard check after the build found 3 untagged digits ("version 1", "version 2" in an options cell) and a stale "41 of 41 checks" in the diagram and explainer. Fixed by rewording, and the pictures were re-rendered to "53 of 53".

## Final results (11/8/2026)
- `tests/check_phase3d.py`: **12 of 12**, older phases included (Phase 1 8 of 8, Phase 2 8 of 8, 3a 14 of 14, 3b 9 of 9, 3c 11 of 11, org chart 8 of 8). Self-test: **12 of 12** planted breaks caught by the check they target.
- Blind review 01 (`reviews/exceptions/2026-11-08-01-exceptions.md`): caught the planted wrong promised date in a copy of the credit draft; real outputs PASS. Script review 15 (`reviews/phase3b/2026-11-08-15-script-v8.md`): two rounds, PASS; caught the planted "Dana and Tom signed".
- The exceptions log: 3 rows (the two steps and the review), 3 of 3 chain links verify.
- One wrinkle: D6 reads the dashboard, and the dashboard shows D6's result, so after a new log row the page needs two builds before it reads 12 of 12 (the first build checks the page it is replacing).

## Not done
- The one-page diagram (Map tab) doesn't show `/revise` and `/credit` yet; it is laid out to fill exactly one page.
- Nothing here was pushed to the public repo.
