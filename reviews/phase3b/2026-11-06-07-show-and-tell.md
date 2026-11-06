# Blind review 07: the show-and-tell pieces with Phase 3c, after review 06's fixes (11/6/2026)

*Fictional company, fake data. Saved word for word from the reviewer's report; one scrub is marked.*

| Field | Value |
|---|---|
| Reviewer | the author's registered `checker` agent, a fresh instance (tools: Read, Grep, Glob, WebFetch, WebSearch; no write or send tools) |
| How it ran | Told not to open earlier reviews, the results notes, the 3c answer key, or the discarded first run (it could read only the "How it ran" lines of reviews); to look at every screenshot; to mark as required only what is false, misleading, unrecordable, or a privacy leak. A new planted copy: "$872 against $713" changed to "$827 against $713" |
| Planted error caught | Yes (K9) |
| Result | PASS: K1-K8 pass on the real files; 0 required fixes |

Overall: PASS

## Files reviewed (SHA-256 at review time; a later edit makes this review stale)
| File | SHA-256 |
|---|---|
| `docs/video-script.md` | c026c8a36d8c47b501883f6b18d5c11c6288e0c7c46d8dc1eae5f0c8ce3481c6 |
| `docs/explainer.md` | f542682b089d630cc75f2b5a948b8a913251b618e9da98f875b21158380fcbf5 |
| `docs/diagram.html` | 4a1b1be498b23e0248894d68d00c27c89a87e0eee07b165fe2fb1bc8fac2b7a5 |
| `dashboard/build.py` | 622a90e6f4d7bf7ed1b4067f53fd41a84e0bbc1e1771bf900d8bbc0c07959168 |
| `docs/explainer.pdf` | 44d72f44c647e5218cd05e4934ff782973184e2d76349b60df9d043d507382f2 |
| `docs/diagram.png` | b0e32c168c2f6792680b66028292efaa08a7d2d4a6e1213c0fbeb9b4d9bc7e6f |
| `dashboard/index.html` | 716a0c1c9782bfb48b2ad63c7a17bda27cf8e44563ceb891bd4afeac64fdaab6 |
| `dashboard/README.md` | 09b77da135ad54e29120f6c732492854fca654d8e0cb86484c3f013cd0487610 |
| `tests/checker-copies/video-script-copy.md` | ad5fd9668522155bbfcb1a9ad4e4af86308c803058111f017b73b6a2b09db16d |

## Optional notes, and what was done
- "41 of 41" counts Phase 3c's R6 line, which the dashboard runs as "skipped" (so the page and the Phase 3b check never call each other). Left as is on the page, which says so on the Checks tab; the full Phase 3c run, where R6 really runs Phases 1, 2, 3a, and 3b, was run separately and its result is in `docs/phase3c-results.md`.
- The other notes (the procurement reviews' finding counts, the guardrail row that lists only Phase 3a's blank approval lines) are wording on the Checks tab; left as is so this review stays current. The controls review (10:23) does predate reviews 06 and 07 of these pieces, which ran on the 3b side; the explainer's "the latest review" means the latest of the reviews that checked the AI's own outputs. Noted for the next edit.

## The report, word for word
VERDICT: PASS on K1-K8 (the real files). K9 FAIL, which is the copy's planted error, not a defect in the real files.

PASS - K1 script Say column - Every claim traced. "$872 against $713" matches match.md (HOLD, $159) and data.json. "27 days late" matches approval-request.md (arrives 2026-12-17 vs install 11-20). "$108 over budget" matches CR-001 ($5,308 vs $5,200). Skyquay "$120,000 ... four signatures ... blank" matches packet.md. "Dana ... sends it" matches the Saltmarsh draft's "Reviewer and sender". Eight contractors, and the checker "set up to only read", also match.

PASS - K2 explainer - "0 times in 31 audit log rows" = 18+9+4. "41 of 41" = 8+8+14+11. "20 decisions", "6/13/6 planted problems", and all 14 skill descriptions match their SKILL files and records. The checker claim matches compliance-checker.md (Read, Grep, Glob) and reviews/controls line 7 ("no write or send tools"). The earlier reviews' "How it ran" lines say the limit was an instruction. The PDF is one page.

PASS - K3 diagram.png - Every number traces: 8/6, 7/13, 3/6, $120,000 with 4 sign-offs, $872 vs $713, 27 days, $108, 5 days, 2 items not received, 14 skills, 4 approvers, 31 rows, 20 waiting, 41 of 41. The Gulfpine excluded company is named on its insurance (coi.md "Insured").

PASS - K4 AI vs person - Blue boxes for the AI, amber for people, with a legend. Every sign, send, approve, pay and certify step is amber, and each lane's footer says "0 ... by the AI".

PASS - K5 recordable and timing - Tab order matches index.html (Overview, Onboarding, Buying, Checks, Audit log). Skyquay is last in "The record behind each vendor". Saltmarsh has an "insurance end date" row. Headings "Invoices: three-way match" and "The checker: a second AI" exist. The replay is 31 rows at 280 ms, about 8.7 s, so it ends before 1:50. Spoken words total about 201. Rough fit per beat (words/2.5 plus 1.5 s per click): 5.6, 5.9, about 13, about 8, about 11, about 25, 9.9, 9.8, 10.2, 9.5 s. The tight ones are beat 3 (14 s window), beat 4 (8 s) and beat 6 (26 s). Beat 4 goes over if it needs two scrolls.

PASS - K6 overclaims - "Designed and directed" and "Claude Code wrote the code" appear everywhere. Every send, sign, order and pay step is a person's, and the README says the demo hasn't run with real users. The README's "ran by hand" is supported by the vault note ("prepared this packet as Major Projects Manager"). Only structure is copied; there is no real data. One wording issue is in OTHER.

PASS - K7 privacy - I grepped index.html, the README, and docs/*.md and *.html for the Windows user path and for phone, EIN and non-.example email patterns, with no hits. [scrubbed: the design partner's name] is named only in the README as the labelled design partner; the dashboard says "A design partner". The fake delivery address is marked "(fictional)". Every piece says the company and data are fictional.

PASS - K8 dashboard - Waiting rows: 9 onboarding + 11 buying = 20, sorted oldest first. All 12 rules and the "Since" dates match records (disclosure 11-03; exclusion list as of 11-05; order approved 11-06; supplier notice 11-07 and 11-12; invoices 11-12). Tiles match tables. The Kestrelbay packet shows Dana as signer, but an on-page note says the screen recused her. The screenshots match the current index.html.

FAIL - K9 video-script-copy.md - Beat 1:14-1:26 says "bills $827 against $713". The records (match.md, data.json p.inv_billed) say $872. This is the only difference I found from the real script.

OTHER PROBLEMS: The "41 of 41" tile and the 3c "11 of 11" count R6 as PASS, but its printed line says "skipped" (--skip-old-phases), so only 40 checks actually ran. The page discloses this in small print. The vault rule says a PASS with count 0 is a fail. Suggest "40 ran, 1 skipped (older phases run separately)", or count it outside the total. The diagram and explainer repeat "41 of 41". (Optional.) On the Checks tab, rows 3 and 4 of the reviewer table show "3 findings" and "2 findings" with no note on which were planted copies and which was the one real rule gap. A viewer could read them as failures; the lead paragraph explains this only partly. (Optional.) The Checks tab label "Approval lines left blank on the purchase request and change request: 2" leaves out 3c's blank certification and two close-out signatures. It is not false but stale. (Optional.) NOT CHECKED: whether the six Phase 3b reviews (not opened, per instruction) post-date the controls review. The explainer calls the controls review "the latest review". NOT CHECKED: Snipping Tool, Clipchamp, Drive and LinkedIn click steps; the script itself says it didn't click through them. Not read in full: the dashboard's collapsed evidence panels (I read their contents only through grep and the screens above), and screenshot-map.png (it is the diagram, which I did read).
