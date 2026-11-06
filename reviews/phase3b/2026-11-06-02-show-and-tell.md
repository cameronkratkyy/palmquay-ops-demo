# Blind review 02: Phase 3b show-and-tell pieces, after review 01's fixes (11/6/2026)

*Fictional company, fake data. Saved word for word from the reviewer's report; two scrubs are marked.*

| Field | Value |
|---|---|
| Reviewer | the author's registered `checker` agent, a fresh instance (tools: Read, Grep, Glob, WebFetch, WebSearch; no write or send tools) |
| How it ran | Told a first review had found issues, and to judge the files as they are without assuming anything was fixed. A new planted copy: "$108 over budget" changed to "$180 over budget", without saying which file was planted |
| Planted error caught | Yes (K9: "'The substitute puts the project $180 over budget.' Records say $108") |
| Result | FAIL: 3 required fixes (one is the planted copy itself) |

Overall: FAIL

## Required fixes and what was done
1. **K1:** "Approved vendors can then supply a project" implied the onboarded contractors supply the furniture; the furniture suppliers are a separate approved list. Done: "The company also buys for projects, like furnishing an apartment, from its approved suppliers."
2. **K2, K3, K6:** "each check is proven able to fail" overclaimed (Phase 1 plants 4 breaks for 8 checks; Phase 3a 13 for 14). Done: the explainer and diagram now say self-tests plant breaks and the checks caught every one; the dashboard says "each check script also has a self-test."
3. **K9:** the planted copy, caught as intended.
Optional fixes also done: the opening beat re-timed (it ran about 15 s at 150 words a minute) and split into two Overview beats; every beat re-timed from its word count; a scroll cue on the Checks beat; "every dollar" now "every order and every payment"; the bed question now says the approved order has a queen bed.

## The report, word for word
VERDICT: FAIL (K1, K2, K3, K6, K9 fail on the real or copy files)

FAIL - K1 script Say column - Buying beat: "Approved vendors can then supply a project, like furnishing an apartment." The 8 onboarded contractors (roofing, plumbing and so on) don't supply furniture. company/approved-suppliers.md lists a separate set: Gulfweave, Mangrove, Keystone. The line implies the Skyquay and Kestrelbay kind of vendors supply the sofa. Every number checks out: 8 vendors; Saltmarsh COI expired (2026-09-30); $120,000, 4 signers; 27 days; $108 over; $872 vs $713; Dana sends the drafts; sign-offs blank.

FAIL - K2 explainer - "30 of 30 checks pass, and each check is proven able to fail" and "Each check is tested by planting a break." Phase 1's selftest plants 3 breaks (check_phase1.py line 5; phase3a-results says 4 of 4) against 8 checks. Phase 3a has 13 breaks for 14 checks. Other claims trace: 15 waiting (8+7), 6 and 13 planted problems, 0 AI actions in 27 rows, the checker limit "an instruction, not enforced" (matches the reviews' "How it ran" lines).

FAIL - K3 diagram - The "Tests first" box repeats "each check is proven able to fail." Same evidence as K2. Everything else traces: 11 skills, 4 approvers, 27 rows, $185, $108, $872/$713, 5 days, 2 in.

PASS - K4 - Blue "AI does it" against amber "A person decides" boxes. Each AI lane ends in a person box. The headline states "People approve, send, sign, and pay."

PASS - K5 - Every On-screen item exists, in page order: Overview "Waiting on people"; Onboarding Vendors table; "The record behind each vendor" (Saltmarsh "insurance end date" row, "DRAFT, not sent", Skyquay sign-off table); Checks checker table; Buying budget bar, seven-steps table and "Invoices: three-way match" HOLD row; Audit log Play. No other app is needed while recording. The replay runs about 10 s (27 rows at 380 ms). Pacing problem listed under optional fixes.

FAIL - K6 - The same "each check is proven able to fail" overclaim. The "Approved vendors" line also muddles who supplies what. "Designed and directed" and "Claude Code wrote the code" are present. Nothing claims real users, real money or production. The checker limit is disclosed as unenforced in the explainer and on the Checks tab. The script and diagram say only "set up to only read" (acceptable).

PASS - K7 - A grep of index.html for the Windows user, C:\, [scrubbed: the web-address prefix], real names and [scrubbed: the design partner's name] found nothing. The only addresses are .example and palmquay.example, including in the collapsed sections. [scrubbed: the Windows user name] matched only "video camera" in the script. Fictional labels appear in the script, explainer, diagram, and the dashboard header and tabs.

PASS (with a visual gap) - K8 - Recounted: tiles 8 vendors (2/1/5), 15 waiting, $4,898 / $5,200 / $5,308, 19 problems, 30 of 30 (8+8+14), 27 rows (18+9), 7 drafts, 5 blank sign-offs. Budget bar maths is right (88.73%, 7.43%, line at 94.2%). Seven-steps table matches procurement-log, CR-001 and the PO. Replay end matches Overview (6 drafts, 2 packets, 4 reviews, 0 AI actions). I saw only the Overview, Buying, Replay-end and diagram images. NOT CHECKED visually: screenshot-onboarding, -checks, -audit, -map.

FAIL - K9 copy - Row "0:58-1:28": "The substitute puts the project $180 over budget." Records say $108 (change-request-CR-001.md, procurement-log row 5). Every other line matches the real script, including the "Approved vendors" problem in K1.

Required fixes: 1. Reword the Buying opener, e.g. "Palmquay also buys furniture from approved suppliers for a project, like furnishing an apartment." The same fix goes in the copy. 2. Change "each check is proven able to fail" in the explainer (twice) and the diagram (HTML and PNG) to something true, such as "the checks are tested by planting breaks" or "most checks". 3. Fix $180 to $108 in tests/checker-copies/video-script-copy.md. That file is meant as a planted-error copy, so confirm it is supposed to be caught.

Optional fixes: Beat 1 is 37 words in 10 s (about 220 wpm). At the stated 150 wpm it runs about 15 s, and every later timestamp slips. Trim to about 25 words. Total spoken is about 262, which is under 300. The Checks-tab beat needs a scroll past the three result rows and the collapsed details. Say "scroll to 'The checker: a second AI'." Overview shows "What is bedroom wall B?" as still open, while PO-PQ-1042 was approved on 2026-11-06 with the queen bed. A viewer may ask. Explainer, script and diagram are not affected. "People approve every dollar" (script end) is loose. Finance approves payment, so "every payment" is safer.
