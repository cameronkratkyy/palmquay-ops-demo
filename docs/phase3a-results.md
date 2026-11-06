# Phase 3a results (11/5/2026): buying for a furnishing project

*Fictional company, fictional project, fake data. Demo date 2026-11-05.*

## What ran, in order
1. **Rules first.** `company/rules.json` got a `projects` section (bed widths, clearance, walkway, owners, codes, the partner label); `CLAUDE.md` got section 10, which states every one of them.
2. **Test data.** `tools/make_project.py` wrote one project (`projects/unit-4b/`, 16 files): the request, the design partner's plan, 3 supplier catalogs, the first product picks, 3 quotes, the approved order (the baseline), a backorder notice, delivery tracking, a receipt, and 2 invoices, with one problem planted per activity.
3. **Answer key, locked.** `tests/answer-key-3a.json` was written by hand and its hash locked in `tests/LOCK.txt`, along with the approved order's hash, before any helper existed.
4. **Check first.** `tests/check_phase3a.py` was written before the helper. First run: **3 of 14 PASS**. Its own recomputation from the raw files already equaled the hand-written key, which shows the planted problems are really in the data.
5. **Dry run on a throwaway copy.** All 7 activities matched the key. It found 2 bugs in the check itself (a field name its exact-match rule forbade; the task table's header counted as a task) and 1 wording clash in the helper ("nothing paid" tripped the paid-search). All fixed before the real run; none loosened a check.
6. **Real run, once each, in order:** `/scope` → `/source` → `/quote` → `/approve` → `/change` → `/deliver` → `/match`. Each appended one row to `audit/procurement-log.csv`. A second run is refused.
7. **Blind review 01:** caught the planted miss (Keystone's invoice marked MATCH) on both counts, and found a gap in the written rule for a substitute's order date. The answer was right; the rule text was incomplete. Rule clarified.
8. **Blind review 02,** same unchanged files: 7 of 7 real outputs OK, planted miss caught.
9. **Final check and self-test** (below).

## What each activity caught
| Activity | Caught | Numbers |
|---|---|---|
| `/scope` | MISSING_MEASUREMENT, SCOPE_CONFLICT | Bedroom wall B blank; king needs 76 + 24 + 24 = 124 in on a 120 in wall; a queen (108 in) fits |
| `/source` | LATE_ITEM | Sofa GW-SOF-210 arrives 2026-12-17, 27 days after the install date; in-time alternative MH-SOF-118 ($1,520, 7 days) |
| `/quote` | HIDDEN_FREIGHT, QUOTE_EXPIRED | $185 delivery only in a footnote; Mangrove's quote ended 2026-11-01; total $4,898 → Facilities Manager approves; purchase request is a draft |
| `/approve` | TOO_WIDE, FINISH_MISMATCH, NEEDS_PERSON | Rug 98 in vs 96 in max; chrome vs brushed nickel; chair fabric not stated → a person decides; 5 of 5 clean products passed |
| `/change` | OVER_BUDGET | Backorder substitute +$410 → $5,308 vs $5,200 budget ($108 over); delivery 2026-11-09 instead of 11-13; baseline file unchanged (hash) |
| `/deliver` | DELIVERY_LATE, ADDRESS_MISMATCH | Bed frame 5 days after the install date; dresser addressed to Unit 4D; 2 tasks for the Facilities Manager due 2026-11-13; update drafted, not sent |
| `/match` | PRICE_MISMATCH, QTY_MISMATCH | Keystone billed 3 lamps at $139 vs an order of 2 at $129 (2 received): $872 billed vs $713 expected, $159 difference; held for Finance; nothing marked paid |

## Final counts
- `tests/check_phase3a.py`: **14 of 14 PASS** (Q0 lock, Q0b recompute = key, Q1–Q7 the activities, Q8 procurement log 9 rows with a verified chain, Q9 skills + rules, Q10 Phases 1 and 2, Q11 blind review, Q12 README).
- `--selftest`: **13 of 13** planted breaks caught, each by its own check.
- Phase 2: 8 of 8, self-test 23 of 23. Phase 1: 8 of 8, self-test 4 of 4 (one new break: the partner named without its label).
- The first full run was 13 of 14: Q10 caught that Phase 2's privacy scan didn't know the labeled-partner exception. Fixed in Phase 2's P6 (same narrow rule; every Phase 1 break must be caught).

## What people still do
Answer the one scope question, choose late-but-preferred vs. on-time, approve the purchase request, decide the unclear chair, approve or reject the change request, send the client update, and approve payment. The assistant does none of those.

## Not tested
How the dashboard and the 2-minute video present this (Phase 3b). Real supplier data, real prices, real email. Tax.
