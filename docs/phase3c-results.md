# Phase 3c results (11/6/2026): controls from a real procurement packet

*Fictional company, fictional project, fake data. The controls copy the structure of a real public-agency procurement approval packet the author prepared by hand; no name, number, or document from it is in the demo.*

## What was built
| Control | Skill | Inputs (new, fake) | Outputs |
|---|---|---|---|
| Conflict-of-interest disclosure + exclusion check | `/screen` | `vendors/*/disclosures/conflict-of-interest.md`, `company/exclusion-list.md` | `vendors/*/screen.json`, `controls/supplier-screen.json`, `controls/screen.md` |
| Approval request: procurement type by dollar size, purpose, funding line, quotes per line, certification | `/request` | `projects/unit-4b/funding.md` (+ the existing order, plan, catalogs) | `projects/unit-4b/controls/approval-request.json` and `.md` |
| Running totals + two-signature close-out | `/closeout` | `projects/unit-4b/closeout/2026-11-12-gulfweave-completion.md` (+ the existing invoices, receipt, tracking) | `projects/unit-4b/controls/contract-summary.*`, `completion-certificate.md`, `drafts/reply-gulfweave-2026-11-12.md` (not sent) |
Rules: `company/rules.json` (`controls`) and CLAUDE.md section 11. Log: `audit/controls-log.csv`, hash-chained.

## What each control caught
| Control | Caught | Numbers |
|---|---|---|
| `/screen` | CONFLICT_DISCLOSED | Kestrelbay's disclosure names an owner who is the brother of its only approver (the $8,500 tier): the Facilities Manager is recused, Legal reviews, the Procurement Lead signs |
| `/screen` | EXCLUDED | Gulfpine's insurance names Gulfpine Pest Solutions LLC, excluded 2026-03-16 to 2029-03-15: its follow-up is held for Legal. 6 contractors and 3 suppliers clear |
| `/request` | LOWEST_NOT_SELECTED | Sofa: $1,520 selected; the lowest in-spec price is $1,450 (GW-SOF-210), which the record shows arriving 27 days late, so the reason is on file |
| `/request` | SINGLE_SOURCE ×2 | Bed ($690, Gulfweave only) and dresser ($640, Mangrove only): the Facilities Manager writes the justification; the AI doesn't |
| `/request` | (no flag) | Standard purchase ($4,898, between $2,500 and $25,000); budget line FAC-TURN-2026, $302 left; certification blank |
| `/closeout` | CLAIM_CONTRADICTED | Gulfweave says everything was delivered; the receipt has neither its bed frame nor its coffee table. Invoiced $1,407 of $4,898, held $872, remaining $3,491; 3 of 8 lines received; NOT_READY; both certificate signatures blank |

## What ran, in order
1. **Inputs, rules, key, and lock first.** The fake inputs (11 files), the rules, and a hand-written answer key; then the key and the hashes of 94 Phase 1-3a records were locked in `tests/LOCK.txt` and `tests/frozen-3c.txt` before the helper existed.
2. **Check first.** `tests/check_phase3c.py` first run: **3 of 11**. Its own recount from the raw inputs matched the key on every result, so the planted problems are really in the data. One bug in the check, fixed before the helper existed: two fields the inputs can't decide (whether the signature lines were left blank) were compared in the recount; they're checked on the output files instead.
3. **Dry run on a throwaway copy:** every result matched the key; a second run was refused, as designed.
4. **First real run, discarded.** The approval request and close-out outputs went into `projects/unit-4b/out/`, which Phase 3a's checks own; Phase 3a's own Q6 and Q11 caught it minutes later. The run wasn't edited away: its 3-row log, hash chain, and 6 files are kept in `audit/discarded-3c-first-run/`. The outputs moved to `projects/unit-4b/controls/`, the 3c check gained a stricter rule (no new files in Phase 3a's `out/`), and all three steps re-ran once each with a fresh log.
5. **Blind review** (`reviews/controls/2026-11-06-01-controls.md`): every real output OK; the planted copy (the dresser's single-source flag removed) caught. Logged as the controls log's 4th row.
6. **The show-and-tell pieces updated:** the dashboard (a screening column and table, the controls section, the third log in the replay, 20 decisions waiting on people under 12 written rules), the diagram (a third lane), the explainer (3 more steps, still one page), README; the Phase 3b check extended to every new number, never loosened.

## Final counts
- `tests/check_phase3c.py`: **11 of 11** (R6 runs Phases 1, 2, 3a, 3b).
- Self-test: **11 of 11** planted breaks caught, each by its own check. The first self-test caught 9 of 11 and exposed two weak spots in the check itself: R2's planted edit never applied (the file spans several lines), and R9 accepted "(fictional)" anywhere in a file. R2's plant now edits the data; R9 now requires the standard fake-document line (stricter).
- The full run, with R6 really re-running Phases 1, 2, 3a, and 3b: **11 of 11**; those phases 8, 8, 14, and 9 of 9. (The dashboard runs the 3c check without R6, so the page and the Phase 3b check never call each other; the Checks tab says so.)
- The show-and-tell pieces after 3c: blind review 06 FAIL (2 required fixes: which reviews had the read-only limit as an instruction only; four dashboard consistency issues), fixed; review 07 **PASS**, planted error caught.

## What people still do
Legal: Kestrelbay's disclosure, Gulfpine's exclusion. Procurement Lead: sign Kestrelbay's packet. Facilities Manager: write 2 single-source justifications, sign the approval request, send the reply to Gulfweave, verify the close-out when everything has arrived.

## Not tested
A real exclusion list (the real one is a government database; this one is fake). A real disclosure form's legal wording. Installation (only delivery is in the records). How the new sections look in the video (the video script's story didn't change).
