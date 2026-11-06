# Blind review 06: the show-and-tell pieces after Phase 3c was added (11/6/2026)

*Fictional company, fake data. Saved word for word from the reviewer's report; scrubs are marked.*

| Field | Value |
|---|---|
| Reviewer | the author's registered `checker` agent, a fresh instance (tools: Read, Grep, Glob, WebFetch, WebSearch; no write or send tools) |
| How it ran | Told not to open earlier reviews, the results notes, the 3c answer key, or the discarded first run; to look at every screenshot; to mark as required only what is false, misleading, unrecordable, or a privacy leak. A new planted copy: "$120,000 job" changed to "$102,000 job" |
| Planted error caught | Yes (K9) |
| Result | FAIL: 2 checks with required fixes |

Overall: FAIL

## Required fixes and what was done
1. **K2:** "that limit was an instruction, not enforced" was true of the Phase 1-3a reviews, not the 3c review, which ran as an agent with no write tools. Done: the explainer and the Checks tab now say which.
2. **K8:** "Both chains verify" over three chains (now "All three"); the problems table repeated SINGLE_SOURCE's count on two rows (now one row per code with every place listed, so rows add up to the tiles); Kestrelbay's collapsed packet still names the recused approver (a note now says the packet predates the screen and who signs instead); the Gulfweave reply's "Since" date (now the notice's date, 2026-11-12, and the README's rule names each decision's date source); the dashboard README said three checks run at build (now four).
Optional fixes also done: "3 steps from a real packet" instead of "3 controls" in the diagram and explainer; the checks tile says Phase 3b's own check runs separately. Not changed: the labelled design-partner name (the author's decision D58; the GitHub session decides what goes public), the folder path in the Phase 1 check (on the GitHub scrub list, D60), and Clipchamp "already on this PC" (checked 11/6: Clipchamp 4.7 is installed).

## The report, word for word
VERDICT: FAIL (K2 and K8 have required fixes; K9 also fails but is outside the overall rule)

PASS - K1 - Every Say-column claim in docs/video-script.md traces. $120,000 and four blank sign-offs: skyquay packet.md "Contract amount | $120,000", "Over $50,000: 4 sign-offs". 27 days late, $108 over, $872 vs $713, "DRAFT, not sent", Dana sends: all match their records. Eight contractors: 8 vendor folders. The Say column is about 201 words.

FAIL - K2 - Required: explainer says the checker is "defined with read and search tools only. In these demo runs that limit was an instruction, not enforced." That matches reviews 1-4 ("general-purpose agent told to follow compliance-checker.md"). The 3c review reviews/controls/2026-11-06-01-controls.md used "the author's registered `checker` agent... tools: Read, Grep, Glob, WebFetch, WebSearch", a different definition, and the controls log credits it to "compliance-checker". The dashboard Checks lead repeats the same blanket claim. Everything else traced: 41 = 8+8+14+11; 0 of 31 rows; 20 waiting; 6 and 13 planted; PDF is one page. Optional: "3 controls from a real packet" is 3 skills covering 5 controls (brief, README), and "five controls" in the explainer means something else.

PASS - K3 - Every diagram.png number and label traces, third lane included: Ray Reyes is the brother of the only approver, the Gulfpine coi.md names "Gulfpine Pest Solutions LLC", 2 single-source lines, 27 days, GW-BED-Q and GW-CT-48 not on the receipt, 14 skills = 4+7+3, 31 rows. Optional: "3 controls" (as in K2).

PASS - K4 - Blue (AI does it) against amber (a person decides) is clear in all three lanes, and the line "AI leaves every signature blank" is stated.

PASS - K5 - Beats follow the tab and section order in index.html, and everything is in one window. The replay is 31 rows x 280 ms, about 8.7 s, inside the 13 s beat. Tight beats: 0:14-0:28 (about 7.2 s of words plus 3-5 actions), 0:48-1:14 (20.8 s of words plus 3-4 actions) and 1:26-1:37 (6.8 s plus 3 actions) land within about 1 s of their windows depending on how "point" is counted. Do the practice run with a timer.

PASS - K6 - "Designed", "Claude Code wrote the code", "hasn't run with real users" are all present. Nothing says the AI approves, sends or pays. The packet is described as "structure only". Optional: the "41 of 41 ... every phase" tile counts 3c's R6 line, which only prints "skipped", and leaves out Phase 3b's own check.

PASS - K7 - No real person, email (only .example) or Windows path in the script, explainer, diagram, dashboard or screenshots. Searches found nothing for "Brenton Ashgrove", "Coralline Haulage" or "Gulfpine Pest Solutions". The [scrubbed: the design partner's name] mention is covered under OTHER PROBLEMS.

FAIL - K8 - Required: (a) audit tab shows "Both chains verify" above three chains (18, 9, 4 rows). (b) The "Problems caught, by cause" table shows SINGLE_SOURCE "2" on two rows, so the Controls rows sum to 8 against the tile's 6. (c) The Kestrelbay packet in the collapsed record lists Dana Reyes as signer 1, while the page says she is recused and Marcus Hale signs. Nothing on the page explains that the packet predates the screen. (d) The Gulfweave reply row says "Since 2026-11-06" and sits before 11-07, but it answers a notice dated 2026-11-12. The dashboard README says "Since" is the record's date. (e) dashboard/README.md says the rebuild "runs the three phase checks live"; the Checks tab runs four. The 20 rows do match the README's 12 rules.

FAIL - K9 - tests/checker-copies/video-script-copy.md line 21 says "This $102,000 job" and the record says $120,000. Every other line is identical to docs/video-script.md.

OTHER PROBLEMS: README.md line 21 (and projects/unit-4b/partner-plan.md) names [scrubbed: the design partner's name] as the author's real business. It is labelled, and the 3a check Q12 requires the label, but K7 says no real company, so [scrubbed: the author's name] should confirm he wants it public. tests/check_phase1.py line 22 has EXPECTED_ROOT = [scrubbed: this PC's demo folder path]. It is not on any screen, but it names this PC's Windows user if the folder is shared. Script step 2 of "After you record" says Clipchamp is "already on this PC". That is unchecked, and the script's last section covers only the menu clicks, not this. The README mapping row for compliance-checker.md says the checker "caught both planted errors". That covers only reviews 1 and 2; the 3c review is a separate row.
