# Phase 3b results (11/6/2026): the show-and-tell pieces

*Fictional company, fictional project, fake data.*

## What was built
| Piece | File | What it's for |
|---|---|---|
| Dashboard | `dashboard/index.html` (built by `dashboard/build.py`) | One screen: decisions waiting on people, vendors, the project, checks, a replay of the audit log, the diagram. Double-click to open; no server, no internet |
| One-page diagram | `docs/diagram.png` (3200 x 1800) and `docs/diagram.pdf` (1 page), from `docs/diagram.html` | LinkedIn Featured and email |
| 2-minute video script | `docs/video-script.md` | Recorded in one window with Snipping Tool; setup and sharing steps included |
| Explainer | `docs/explainer.md` and `docs/explainer.pdf` (1 page) | What the author says in an interview: each step in plain English, then the industry term |
| Renderer | `tools/render.py` | Remakes every picture from its source with the browser already on the PC |
| Check | `tests/check_phase3b.py` | Written before the dashboard existed |

## What ran, in order
1. **Brief and check first.** The pass/fail (B1-B9) was locked before any code. First run: **1 of 9 PASS** (only B7, the older phases).
2. **Dashboard.** The first build passed B2 (replay) and B3 (offline, read-only, renders). B1 found 2 gaps: one fact not shown (invoices on hold) and table cells running together so a date read as part of a word. Both fixed in the builder; the check didn't change.
3. **Screenshot loop.** Every tab was screenshotted with headless Edge and looked at. Found and fixed: a line-break fix that broke the page's script (the check's B3 would have failed it: 0 tabs rendered), unit names in a code font, a vague quote on the lead-time row, "pest / control," and evidence panels that always said "draft, packet."
4. **Diagram** drafted at 16:10, then moved to 16:9 with larger type after the first render left the bottom quarter empty.
5. **Regression caught by the older checks:** Phase 2's web-address scan read the diagram's CSS class `dg-sw[.]ai` as a web domain ending in "ai". Renamed the class. The dashboard then kept re-quoting the old match from the check output it embeds, so the builder now shows quoted addresses as text (`name[.]ai`).
6. **One stricter rule added to the check** after its first run: a file reference on the page must name a real file and show exactly that path (it only adds a FAIL case; nothing got looser).
7. **Walkthrough.** All 9 video beats clicked through in a browser at full size and at 1366 x 768: every beat reachable in one window, 0 script errors, the replay plays all 27 rows.

8. **Five blind reviews** by a fresh reviewer each time (`reviews/phase3b/`), each with one planted error in a copy of the script. All 5 planted errors were caught. Reviews 01-04 failed with real findings, all fixed: "an AI that can only read" (the records say that limit was an instruction, not enforced); a folder path naming this PC's user in collapsed check output (now masked); "approved vendors supply the project" (the furniture suppliers are a separate list); "each check is proven able to fail" (true per script, not per check); "the approved budget can't change" (it's the approved order); "change a limit in one place" (the rules text restates the numbers, and a check confirms they agree); "a test recounts every number" (tiles and tables, not the hand-drawn diagram); and the script's timing, rewritten to 200 words in tab order with every click counted. **Review 05: PASS**, 0 required fixes.

9. **A slip of mine, repaired.** A one-line PowerShell replace with a wrongly nested list turned every capital "O" in this README into "n" (the checks still passed: none read those words). Repaired by script: every word with an "n" was matched against the spelling used in the other files; 23 capital O's restored, matching a count taken from the README as read at the start of the session (9 "One," 3 "Owner," 2 "LOCK," and 9 single words); 8 of 8 known lines verified before writing. All checks re-run after.

## Final counts
- `tests/check_phase3b.py`: **9 of 9 PASS** (B1 134 of 134 tagged numbers match, 0 untagged, 356 quotes found word for word, 35 evidence panels equal their files; B2 27 replay events = 18 + 9 log rows; B3 offline, read-only, renders 6 tabs with 0 script errors; B4-B6 the diagram, script, and explainer trace; B7 older phases; B8 review 05 PASS and current; B9 README).
- Self-test: **9 of 9** planted breaks caught, each by the check it targets (run after review 05 was saved, so the B8 break is real).
- Phase 1 8 of 8, Phase 2 8 of 8, Phase 3a 14 of 14 (run by the dashboard at build and by B7).
- Video script: 10 beats, 200 spoken words, 19 counted clicks or scrolls, 110 s needed at 150 words a minute plus 1.5 s per action, windows sized to end at 2:00.

## Update for Phase 3c (11/6, later)
Phase 3c added three steps from a real procurement packet, so the dashboard, diagram (a third lane), explainer (3 more steps, still one page), and README now cover them; this check was extended to every new number, the third log, and 14 skills (never loosened). Blind review 06 failed on two real issues (the read-only limit was only an instruction in the earlier reviews, not the 3c one; four dashboard consistency issues), fixed; review 07 passed with the planted error caught. Final: **9 of 9**. Details: `docs/phase3c-results.md`.

## What people still do
Record the video, watch it back, share the Drive link, add the diagram to LinkedIn Featured.

## Found along the way (not fixed here)
`projects/unit-4b/out/match.md` says "Payment is approved by Finance (?)": the Phase 3a helper looks up the name for "Finance" but `company/people.md` lists the role as "Finance (Controller)". The answer and the check are right; only the name is missing from that one line. Fixing it means re-running `/match`, which the helper refuses by design, so it waits for a decision. The video script never opens that file.

## Not tested
How the recorded video looks and sounds. The Snipping Tool, Clipchamp, Drive, and LinkedIn clicks (written from their usual menus, not clicked through). The PDFs were counted (1 page each) but not looked at as images. The trace check proves a spoken number appears somewhere in the records, not that it's the right one for that sentence. Small numbers are common in the records, so a wrong small number can trace by coincidence; the reviewer checks each claim against its record.

**Update 11/6 (chat 14.0):** the name lookup is fixed going forward in `tools/project.py` ("Finance" now finds Finance (Controller), Tom Becker). The existing `match.md` keeps its "(?)": it is one of the 94 frozen records in `tests/frozen-3c.txt`, and rewriting it would mean editing a locked baseline, so the fix applies to the next run, the way a posted record gets a forward correction. All 5 checks after the fix: 8/8, 8/8, 14/14, 9/9, 11/11. Not committed or pushed.
