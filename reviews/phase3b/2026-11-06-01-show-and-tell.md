# Blind review 01: Phase 3b show-and-tell pieces (11/6/2026)

*Fictional company, fake data. Saved word for word from the reviewer's report; two scrubs are marked.*

| Field | Value |
|---|---|
| Reviewer | the author's registered `checker` agent (tools: Read, Grep, Glob, WebFetch, WebSearch; no write or send tools) |
| How it ran | Given the brief and the files to review, plus `tests/checker-copies/video-script-copy.md` with one planted error ("27 days late" changed to "17 days late"), without being told which file was planted |
| Planted error caught | Yes (K9: "says 'The sofa would have arrived 17 days late'; source.md and phase3a-results.md say 27") |
| Result | FAIL: 3 required fixes |

Overall: FAIL

## Required fixes and what was done
1. **K6:** "a second AI that can only read" overclaimed. The review records say the tool limit was an instruction, not enforced. Done: reworded in the script, explainer, diagram, dashboard, and the README row; the explainer's "If they ask" table now says so.
2. **K7:** the Checks tab's collapsed Phase 1 output showed this PC's folder path, which names the Windows user. Done: the builder masks it ("<demo folder>"); 0 hits on the rebuilt page.
3. **K5:** the Buying beat pointed at the table, then the budget bar, which sits above it. Done: the cue now says to scroll back up on "$108 over budget."
Optional fixes also done: "palmquay" lowercase, the stray quote mark on the delivery row, a date note on the Overview, the full /intake list on the diagram, the planted copy's encoding.

## The report, word for word
VERDICT: FAIL (2 required fixes: K6 and K7; also a K5 ordering flaw). Real video-script.md is numerically correct. The checker copy is wrong in one number.

K1 PASS - Every Say claim traced. "fictional Sarasota", "eight contractors": 8 vendor folders and 8 intake rows. Saltmarsh "insurance expired, blocked": audit row 1, COI_EXPIRED, BLOCKED; COI ended 2026-09-30. Draft "not sent", Dana reviews and sends: audit row 2 "drafted, not sent", "reviewer and sender Dana Reyes"; people.md names her Facilities Manager. Checker "planted mistakes... flagged": reviews 01 and 02 (3 and 18 files, planted copies caught). Skyquay "$120,000, four people sign, in order, signatures blank": audit row 18 and the packet sign-off table. "sofa 27 days late": source.md "27 days late". Alternative MH-SOF-118 arrives in time. "then that sofa was backordered": backorder.md MH-SOF-118. "$108 over budget", "budget can't change until Dana signs": CR-001 ($5,308 vs $5,200); status "awaiting approval by Facilities Manager (Dana Reyes)". "$872 against $713, held for Finance, nothing marked paid": match.md. "seven steps, each with a planted problem": procurement log has 7 step rows, each with a flag. "hash-chained audit log, replays": Audit log tab with Play.

K2 PASS on facts. 27 rows (18+9); 8 vendors/6 problems; 7 steps/13 problems (2+1+2+3+1+2+2); 15 waiting (counted 15 rows); 30 of 30 (8+8+14). 11 skills (4+7); chair-fabric example matches approval.md; all skill descriptions match the records. "can only read" wording: see K6.

K3 PASS on numbers (8 vendors, 6/6, 13/13, 27 days, $185, 2 in, $108, 5 days, $872/$713, $120,000, 30 of 30, 4 approvers, 27 rows, 15 decisions). Image text matches diagram.html. Note: the /intake "Caught" list omits license-expiring and additional-insured; incomplete, not false. "can only read" wording: see K6.

K4 PASS - Two-colour key (blue "AI does it", amber "A person decides"). Every AI box is followed by an amber person box, with "The AI never sends email" and "leaves every signature blank".

K5 FAIL - Beat 0:58-1:28 says to point down the seven-steps table (/source, /change) and then to the budget bar. On the Buying tab the budget bar sits above the table (screenshot-buying.png). Recording in that order needs a scroll back up, and the spoken text covers the sofa before the budget anyway. Other beats name things that exist: tiles, Waiting table, Vendors table, "The record behind each vendor", "DRAFT, not sent", Checks tab checker table, Skyquay packet sign-off, "Invoices: three-way match" HOLD row, Play button. All are in one window. The checker table and the HOLD row need a scroll, which is fine.

K6 FAIL - "A second AI that can only read" is stated flatly in the script (0:36), the explainer (control 3), the diagram and the dashboard Checks tab. phase2-results.md says the tool limit "wasn't enforced by the harness in this run", and the reviews ran as a general-purpose agent told to use only Read/Grep/Glob. The definition file lists those 3 tools; enforcement was not tested. Say "defined to only read", and put the caveat in the explainer's "If they ask" table. Everything else passes: "designed and directed", "Claude Code wrote the code", "hasn't run with real users", no AI approving, sending, ordering or paying.

K7 FAIL - The Checks tab, collapsed "Phase 1: every line it printed", shows the real path [scrubbed: this PC's demo folder path] (line 1592). That is the author's Windows username on a page meant to be shared. It is collapsed in the script's path, but it ships. Strip or mask it in the build. Fictional labels are present on the dashboard stamp, the diagram, the explainer and the script. Only .example emails appear. I did not verify that "400 Palm Quay Way" in the PO record is not a real address; it is labelled fictional.

K8 PASS with small defects. Tiles equal the records: 8 vendors (2/1/5), 15 (8+7), $4,898/$5,200/$5,308, 19 (6+13), 30 of 30, 27 (18+9), 0 and 7 drafts/5 blanks (6 follow-ups plus 1 update; 1+4 sign-offs). Waiting table: 15 rows; "11 days" = 12-01 vs 11-20; $535 and $159 correct. Budget bar: 88.73% and 94.2% match 4,898 and 5,200 of ~5,520. Replay ends "Row 27 of 27", 6 drafts, 2 packets, 0 by the AI; hash chains 18 and 9 verify. Defects (optional): "palmquay" lowercase in Clearsail's row; a stray quote in the /deliver detail ("Unit 4D'"); the PO says "Approved on 2026-11-06" while the page treats 2026-11-05 as demo date, and the Overview Waiting table and the Buying tab "Deliveries as of 2026-11-12" use dates later than that. The page says "scripted events run to 2026-11-12".

K9 FAIL - tests/checker-copies/video-script-copy.md differs from the records in one place: beat 0:58-1:28 says "The sofa would have arrived 17 days late"; source.md and phase3a-results.md say 27. It also has encoding garbage in the Time column [garbled example omitted]. Everything else matches the real file. Whether the copy is an intentionally planted error is not stated in the files I read; if it was planted, it was correctly detectable.

Required fixes: 1. K6: change "can only read" to "defined to only read" (script beat 0:36, explainer control 3, diagram control 3, dashboard Checks lead) and add a line about the unenforced tool limit. 2. K7: mask the local path in the Phase 1 output shown on the Checks tab. 3. K5: reorder beat 0:58-1:28 (budget bar first, or move the on-screen cue), or scroll cue. Optional: fix "palmquay" case, the stray quote, the encoding in the copy file, and the date note on the PO.
