# Blind review 03: Phase 3b show-and-tell pieces, after review 02's fixes (11/6/2026)

*Fictional company, fake data. Saved word for word from the reviewer's report; one scrub is marked.*

| Field | Value |
|---|---|
| Reviewer | the author's registered `checker` agent, a fresh instance (tools: Read, Grep, Glob, WebFetch, WebSearch; no write or send tools) |
| How it ran | Told not to open this folder's earlier reviews and to look at every dashboard screenshot. A new planted copy: "four people sign" changed to "three people sign", without saying which file was planted |
| Planted error caught | Yes (K9: "so three people sign" where the records say four) |
| Result | FAIL: 5 required fixes |

Overall: FAIL

## Required fixes and what was done
1. **K5 timing:** about 263 words plus about 21 clicks didn't fit 2:00 at 150 words a minute. Done: the script is now 219 words and 20 counted clicks or scrolls, timed per beat (150 words a minute plus 1.5 s per action): 119.4 s. The replay now runs 27 rows at 280 ms (about 8 s).
2. **"People make every decision":** the AI does set statuses and pass/fail. Done: "People approve, send, sign, and pay."
3. **"The approved budget can't change":** what's frozen is the approved order (the baseline file), not the budget. Done in the script, the diagram's /change box, and the explainer.
4. **"Change a limit in one place":** the rules text restates every number. Done: "a check confirms the two agree" in the diagram and the explainer.
5. **Setup order and stopping:** Snipping Tool now opens after the other windows close, and a step says how to stop.
Optional fixes also done: the Checks tab explains the first buying review's real finding; the Buying tab says wall B is "still not recorded".

## The report, word for word
VERDICT: FAIL (K5 fails; K2, K3, K6 each have a wording problem that needs a fix; K1 passes on the real script, K9 fails)

K1 script Say column, FAIL (minor). Facts match the records: 8 contractors, Saltmarsh expired, "$120,000 job ... four people sign" (Approval tier 4, packet rows), 27 days, $108 over, $872 vs $713, Dana sends, Finance holds. Who-does-what is right. Two wording problems. (a) "People make every decision" (0:07) is stronger than the records: intake sets BLOCKED/READY/HOLD and /approve sets PASS/FAIL. Say "every approval." (b) "the approved budget can't change until Dana signs" (also the diagram and explainer): CR-001 shows Budget $5,200 in both columns. What stays frozen is the approved order, PQ-1042 ("approved baseline ... stays exactly as it is"). Say "approved order."

K2 explainer, FAIL (one claim). "One rules file ... plus one file for every number" is fine, but the diagram's "Change a limit in one place" is false. The demo's CLAUDE.md restates every number, and Phase 1 C2 checks 34 of 34 against rules.json. The explainer's "approved budget stays put" repeats issue (b). Other claims verified: 27 rows, 15 waiting (8+7), 30 of 30, "instruction, not enforced" (matches each review's "How it ran"), 4 self-tests throwaway copies. Phase 3b self-test is still marked pending in phase3b-results.md, and I couldn't run any scripts. The explainer PDF has /Count 1, so it is one page.

K3 diagram.png, FAIL (one claim). "Change a limit in one place" (see K2). Every number checked out: 8/6/6, 13/13, $185, 98 vs 96 in, 27 days, 5 days, $108, $872/$713, 4 approvers (people.md), 27 rows, 15 waiting, 11 skills.

K4 diagram AI vs person, PASS. Blue "AI does it" and orange "A person decides" boxes are labeled with named roles, and "The AI never sends email" and "leaves every signature blank" are stated.

K5 script recordable at the stated pace, FAIL. I counted the Say words at about 263 (under 300, OK). At 150 wpm that is 1:45 of speech, leaving about 15 s for roughly 21 clicks and scrolls, which is under 1 s each, not "a second or two." Per beat, the 0:50-1:02 beat has 25 words (10 s) plus 4 actions in a 12 s window. The 1:02-1:29 beat has about 63 words (25 s) plus 5 actions in 27 s. The 0:15-0:27 beat has 27 words (10.8 s) plus opening Saltmarsh, which is 7th of 8 collapsed sections, in 12 s. Realistic total is about 2:15-2:20. The Audit-log replay is 27 rows at 380 ms, about 10.3 s, against a 9 s window. Tab order is fine, since the budget bar sits above the seven steps table and "Invoices: three-way match" exists. Smaller issues: setup step 4 says close every other window, but step 5 then opens Snipping Tool, and stopping the recording needs Snipping Tool's bar, which is another app.

K6 overclaims, FAIL only for the "every decision" and "approved budget" wording above. Otherwise PASS. "Designed" and "Claude Code wrote the code" appear. Nothing claims real users, money or production, and the explainer says it "hasn't run with real users." Optional: the script and diagram say "set up to only read" without the caveat the explainer and dashboard give (the reviews were general-purpose agents told to use only Read, Grep and Glob).

K7 personal or real data, PASS. Greps of docs, dashboard and the script copy for the PC user name, [scrubbed: the cloud-sync folder name], Windows paths, [scrubbed: the design partner's name] and URLs found none. Only .example emails appear and addresses are marked fictional. Each piece says fictional. The explainer PDF text was not rendered (pdftoppm missing).

K8 dashboard, PASS on all 6 tabs plus the replay-end screenshot (all 7 viewed). Numbers, statuses and dates match the records, and the collapsed sections contain only fake records. Optional notes: (1) The Buying tab shows the scope question to Lena as "still open", yet PQ-1042, approved 11-06, already contains the queen bed. (2) The Checks tab shows procurement review results as "3 findings" and "2 findings" with no note that review 01 included 1 real finding, a rule-text gap that was fixed. That is honest but unexplained next to the "no findings on real files" rows.

K9 tests/checker-copies/video-script-copy.md, FAIL. Exactly one difference from the real script, in the 0:50-1:02 Say cell: "so three people sign" where the records say four (Approval tier 4: Dana Reyes, Marcus Hale, Priya Natarajan, Tom Becker). Everything else is identical, so it also has the "every decision" and "approved budget" and timing problems.

Required fixes: 1. Cut the Say words, or cut clicks, so a beat fits its window at 150 wpm plus about 1.5 s per action. Aim for about 220 words, and spread the time better. Re-time the replay to 9 s or stop it early. 2. Change "People make every decision" to "People make every approval." 3. Change "approved budget can't change" to "approved order can't change" in the script, diagram (/change box), explainer table and dashboard Map copy (index.html is rebuilt from the diagram), then re-render the PNG/PDF and rebuild. 4. Remove "Change a limit in one place" from the diagram, or say "limits live in rules.json and a check confirms the rules file matches." 5. Fix the setup step order (open Snipping Tool, then close other windows) and say how to stop the recording.

Optional: Add "told to" or the "instruction, not enforced" caveat to the script and diagram checker lines. Note the Phase 2 hash chain is tamper-evident, not tamper-proof. Explain the "3 findings" rows on the Checks tab.

Other: I couldn't run the check scripts or self-tests (no execution tool), so the 30 of 30 and the self-test counts are taken from the records and phase results docs, not re-run.
