# Blind review 04: Phase 3b show-and-tell pieces, after review 03's fixes (11/6/2026)

*Fictional company, fake data. Saved word for word from the reviewer's report; one scrub is marked.*

| Field | Value |
|---|---|
| Reviewer | the author's registered `checker` agent, a fresh instance (tools: Read, Grep, Glob, WebFetch, WebSearch; no write or send tools) |
| How it ran | Told not to open this folder's earlier reviews or the results notes, to look at every screenshot, and to mark as required only what is false, misleading, unrecordable, or a privacy leak. A new planted copy: "$872 against $713" changed to "$872 against $731", without saying which file was planted |
| Planted error caught | Yes (K9: "says '$872 against $731'. The records say $713") |
| Result | FAIL: 3 required fixes |

Overall: FAIL

## Required fixes and what was done
1. **K5 timing:** two beats overran once every click and scroll was counted. Done: the beats now follow the tab order (no going back to a tab), 200 words and 19 counted clicks or scrolls need 110.3 s, and each beat's window is its need plus at least half a second.
2. **"A test recounts every number":** the test recounts the numbers in tiles and tables; the Map tab's diagram is drawn by hand. Done: "every number in its tiles and tables" in the explainer, the diagram, the page header, and both READMEs.
3. **"Live" on the checks tile** next to "run at build": done, "three phases, run at build."
Optional fixes also done: the /deliver box now says a dresser went to the wrong unit; "least privilege by design"; "builds the approval packets"; "append-only by rule"; "puts the project $108 over budget."

## The report, word for word
VERDICT: FAIL (K5 fails; K6 and K8 each have required fixes; K9 is the planted error)

K1 PASS - Every figure and every actor in the Say column traces to the records. Checked: 27 days late (source.md), 4 signatures (rules.json and the packet), $108 over (CR-001), $872 against $713 (match.md), Dana sends the draft (draft header), 8 vendors. The Say column says "$108 over budget" as if the substitute is $108 over, but the project total is $108 over (cosmetic, optional).

K2 PASS - Claims trace: 8, 6, 13 and 15 (8+7); "0 times in 27 audit log rows" (audit-log.csv has no sent, signed or paid rows); 30 of 30 (8+8+14); checker "instruction, not enforced" (the "How it ran" lines); the rules file and numbers file are covered by check C2; the PDF is 1 page. Required: "A dashboard where a test recounts every number" overclaims. check_phase3b B1 recounts only tagged numbers in tiles and tables (its "untagged" scan runs only inside `data-audit` areas). The Map tab's numbers are untagged static text and are not recounted by B1. Optional: "builds the approvals" in the 30-second line could be misread as the AI approving.

K3 PASS - Diagram: 8/6/6, 13/13, $185, 98 vs 96 in, 27 days, $108, $872/$713, 4 approvers, 27 rows, 15 decisions and 11 skills all trace. The "recounts every number" claim on the diagram's "One screen" box has the same overclaim as K2. Optional: "A bed 5 days late; the wrong unit" reads as one bed in the wrong unit, but the dresser is the one shipping to Unit 4D. Optional: the "least privilege" label has no "not enforced" caveat, unlike the explainer and dashboard.

K4 PASS - Blue "AI does it" and amber "A person decides" boxes with a legend. "The AI never sends email" and "leaves every signature blank" sit in the amber boxes. A reader can tell who does what.

K5 FAIL - The order of the beats works in one window, and total time is about 112 of 120 s. Two beats overrun at 1.5 s per click or scroll. (a) 0:47-1:00 (13 s): 22 words is 8.8 s, plus tab, page scroll, open and inner scroll (4 actions, 6 s) is 14.8 s. Even with only 3 actions it is 13.3 s. (b) 0:26-0:35 (9 s): 20 words is 8 s, plus 1 scroll (1.5 s) is 9.5 s. The 0:07-0:13 beat is tight at 5.9 of 6 s. Optional: the beats go Onboarding, Checks, Onboarding, Buying, which backtracks against the tab order (Overview, Onboarding, Buying, Checks, Audit log).

K6 FAIL - Required: the "test recounts every number" overclaim (see K2, K3). Required: the Overview tile says "three phases, live" next to the label "Checks, run at build". The Checks tab text is a static paste from build time, so "live" overstates it. The rest holds: "designed", "Claude Code wrote the code", "hasn't run with real users", no "I coded" or "production", and the AI only suggests. Optional: the Audit tab's "append-only" is stronger than phase2-results ("tamper-evident, not tamper-proof").

K7 PASS - Emails are all .example. No phone numbers and no Windows paths in the pieces (grep, no matches). C1 shows `<demo folder>`. The address is marked "(fictional)". All pieces say they are fictional. The script's F11 step hides the address bar, which would otherwise show the path. [scrubbed: the design partner's name] appears only in partner-plan.md and rules.json, not on any shown piece. Clipchamp "already on this PC" is unverified; the script's closing section partly says so.

K8 FAIL - Required: the tile "live" contradiction (K6). Required: the Map tab's static numbers are not recounted by B1, which is why the "every number" claim is not true. Checked against the records: tiles, the 15 waiting rows, the 19 problems, the Onboarding vendor table (days waiting 2, approvers 1/2/4 match the tiers), the Buying budget bar ($4,898 / $5,200 / $5,308), invoices, the replay (27 rows, final states, 280 ms per row, about 7.6 s), and all 7 screenshots. All consistent. Optional: Checks-tab rows "3 findings" and "2 findings" for the procurement reviews don't say how many were on real files, unlike the onboarding rows ("0 on real files"). Optional: the sign-off table shows as raw pipe text in the packet `<pre>`, which is hard to read on video.

K9 FAIL - tests/checker-copies/video-script-copy.md differs from the real script in one place: the 1:27-1:39 beat says "$872 against $731". The records say $713 (match.md, quotes.md, match.json, dashboard). Otherwise identical.

Other: README.md line 80 says the 3b check "recounts every number on the page", the same overclaim as in K2. NOT CHECKED: the PDF's visual layout (the page count is 1). Playback of the video, and the Snipping Tool, Clipchamp, Drive and LinkedIn clicks.
