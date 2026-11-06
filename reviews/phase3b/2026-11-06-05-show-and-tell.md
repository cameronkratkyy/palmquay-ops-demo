# Blind review 05: Phase 3b show-and-tell pieces, after review 04's fixes (11/6/2026)

*Fictional company, fake data. Saved word for word from the reviewer's report; one scrub is marked.*

| Field | Value |
|---|---|
| Reviewer | the author's registered `checker` agent, a fresh instance (tools: Read, Grep, Glob, WebFetch, WebSearch; no write or send tools) |
| How it ran | Told not to open this folder's earlier reviews or the results notes, to look at every screenshot, to also review README's Phase 3b rows and the dashboard README, and to mark as required only what is false, misleading, unrecordable, or a privacy leak. A new planted copy: "Eight contractors" changed to "Nine contractors", without saying which file was planted |
| Planted error caught | Yes (K9: "'Nine contractors sent paperwork.' The records have 8 vendor folders") |
| Result | PASS: K1-K8 pass on the real files; 0 required fixes |

Overall: PASS

## Files reviewed (SHA-256 at review time; a later edit makes this review stale)
| File | SHA-256 |
|---|---|
| `docs/video-script.md` | c026c8a36d8c47b501883f6b18d5c11c6288e0c7c46d8dc1eae5f0c8ce3481c6 |
| `docs/explainer.md` | f4876c5cb09e017f8c06382a349110bc5a62548a47ff7abf98d86ac135712f0c |
| `docs/diagram.html` | 04f046ecdbdd22ea2176bfa1747613ba959e356d15ffbece6fe115a9f36256e7 |
| `dashboard/build.py` | 79ec36a9a8a21430a740841ace86c59d0bd95eab1f449e49968240e69c3cf098 |
| `docs/explainer.pdf` | 70f4c068ac3f4cc23786942e8889313dc27139e8566d36158e09891cedc92294 |
| `docs/diagram.png` | 2687cf6531456022a99d44e5f270d43237155af47a76d71c9fddbd0eced9192d |
| `dashboard/index.html` | 3f2c5c2045c8c80913dabdd59ddca43b9a9ff75a6e3b76c1706c5b1ebc6d1812 |
| `dashboard/README.md` | d7af48cd322fd3316e02c3403b74d85e7fc58680d5cd9c8b25f0f8772293ac72 |
| `tests/checker-copies/video-script-copy.md` | 9b5095d048ef051493c7dc9ce0559f06689e54d4e358c1c57091e832347d5121 |

## Optional notes, and what was done
- README's 3a status row said "7 planted problems" where the other pieces say 13: reworded (README isn't one of the reviewed files above).
- Left as is, because changing a reviewed file re-opens the review: the Buying tab's present tense for two decisions already made on 2026-11-06; the diagram's "least privilege by design" without the "not enforced" caveat the other pieces carry; the Checks tab's "(the answers were right)"; the script's "the delivery" where the records say "receipt."

## The report, word for word
VERDICT: PASS (K1-K8 pass on the real files). K9 is a separate result: the copy has one wrong claim.

PASS - K1 Say column facts. I checked each claim against the dashboard and the records: "Eight contractors" matches the 8 vendor folders. "Saltmarsh... insurance expired" matches intake.json (COI end 2026-09-30, BLOCKED). "four signatures, in order, all blank" matches vendors/skyquay-lift-fire/packet.md. "27 days late" matches source.md. "$108 over budget" matches CR-001 ($5,308 against $5,200). "$872 against $713" matches match.md. Dana sends the follow-up, Dana signs the change, and Finance holds the invoice, all per people.md and the records. The checker "set up to only read" and "flagged the mistakes we planted" match the review files.

PASS - K2 Explainer. All 11 skills are described correctly. "0 times in 27 audit log rows" matches 18+9 rows. "30 of 30" matches 8+8+14. The 6 and 13 planted problems and the 15 waiting decisions match the dashboard counts. The checker caveat ("an instruction, not enforced") matches "How it ran" in all four reviews. Self-tests use throwaway copies: all four check scripts create temp copies.

PASS - K3 Diagram PNG. 8 vendors, 6/6, 13/13, $185, $872/$713, "A rug 2 in too wide" (98 vs 96), the bed 5 days late, 11 skills, 4 approvers, 27 rows and 15 decisions all trace to records.

PASS - K4 AI vs person. Blue "AI does it" boxes and amber "A person decides" boxes are keyed, and the amber gates are explicit: Facilities Manager, "1 to 4 people sign", "People decide".

PASS - K5 Recordable. The beats follow the tab order in index.html, and the heading names exist. Total spoken words are about 201 (80 s at 150 a minute). The replay runs 27 rows at 280 ms, about 7.6 s, matching "about 8 seconds". Per-beat word time plus clicks and scrolls (1.5 s each, pointing not counted) fits every window. Tightest beats: 0:14-0:28 uses about 11.7 to 13.2 of 14 s. 0:36-0:48 uses about 11.3 of 12 s. Both fit.

PASS - K6 Overclaims. "I designed... Claude Code wrote the code" appears. Nothing says real users, production, or real money. The AI never approves, sends, signs, orders, or pays. The checker's limit is stated as unenforced in the explainer, the Checks tab and README. No control or test is described as stronger than the records and check scripts show.

PASS - K7 Privacy. I grepped dashboard/index.html, dashboard/README.md, dashboard/data.json, docs/*.md, docs/*.html and README.md for this PC's Windows user name, the C:\Users path, the [scrubbed: cloud-sync folder] path, the owner's name, the [scrubbed: the design partner's name] vault wording, and [scrubbed: an email provider's name]. The only hit was README line 20, "[scrubbed: the design partner label, which README carries word for word]" That is labeled fictional and is not a leak. Emails are .example only. Collapsed sections hold only fake data, and every piece states it is fictional.

PASS - K8 Dashboard, all 7 screenshots plus the index.html text. The tile counts, the 15 waiting rows (8 onboarding + 7 buying), $302 left, days waiting 2, and 23 and 36 days all recompute. Tabs and screenshots agree. No broken or unreadable content.

FAIL (K9 only, not part of the overall verdict) - tests/checker-copies/video-script-copy.md. Its only difference from the real script is line 19: "Nine contractors sent paperwork." The records have 8 vendor folders and the dashboard says 8, so the claim is false. All other lines are identical to docs/video-script.md.

OTHER PROBLEMS (all optional, none required): README Status row 3a says "7 planted problems". The dashboard, diagram and explainer say 13, and the README's own table lists 13. Wording only. The Buying tab's steps table says "Dana Reyes... approves the purchase request" and "A person decides the unclear chair" in the present tense. The PO and the "Already decided" list show both were done on 2026-11-06. Mildly stale next to the waiting list. The diagram says "Set up to only read... least privilege by design" with no "not enforced" caveat. The explainer, Checks tab and README all have that caveat. The Checks tab says "(the answers were right)" about review 01's finding. Review 01 recorded a FINDING on CR-001's date. README says the rule text, not the answer, was wrong. It is consistent but could be misread. Every address shown, such as "400 Palm Quay Way, Sarasota FL", is labeled "(fictional)". It sits in collapsed records and is not a real person's address. The script says invoices are matched "to the order and the delivery". The records say "receipt". Wording only.
