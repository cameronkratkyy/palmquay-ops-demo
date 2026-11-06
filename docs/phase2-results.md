# Phase 2 results (11/5/2026)

*Fictional company, fake data. Demo date 2026-11-05.*

## What ran, in order
1. **Check first.** `tests/check_phase2.py` (P1–P7 plus P1b for `/status`) was written before any skill existed. First run: **1 of 8 PASS** (only P6; nothing else existed yet).
2. **Dry run of the helper** (`tools/onboard.py`) on a throwaway copy outside this folder, so the real audit log only holds real actions. It matched the key on 8 of 8 and refused a second intake and a packet for a BLOCKED vendor.
3. **Saltmarsh end to end:** `/intake` (COI_EXPIRED, BLOCKED) → `/chase` draft (lint 0 problems) → planted copy of that draft with a wrong deadline → compliance-checker review 01 (3 files; caught the planted deadline, 2 real files OK) → audit rows 1–3, hash chain verified.
4. **The other 7 vendors:** 7 intakes, 5 drafts (each linted and run through P2's rules before logging), 2 approval packets. `/route` on Bayvane (HOLD) was refused, as it should be. Saltmarsh wasn't run again, because intake refuses a second run and audit rows are append-only.
5. **Planted Gulfpine intake copy** (issues removed, status READY, name check skipping the certificate), then **compliance-checker review 02**: all 18 files (16 real + 2 planted), blind.
6. **Final check and self-test.**

## Counts (final run)
`python -I -X utf8 tests/check_phase2.py --selftest` → **8 of 8 checks PASS**; **self-test 23 of 23 planted breaks caught** by the check each one targets.

| Check | Result | What it counted |
|---|---|---|
| P1 `/intake` = locked key | PASS | 8 of 8 `intake.json` match the key (issues, status, approvers, documents); 8 of 8 Stage lines start with the status |
| P1b `/status` | PASS | 8 lines, 8 of 8 right (stage, status, blocker, days waiting) |
| P2 `/chase` | PASS | 6 of 6 drafts pass (vendor, item, why, deadline 2026-11-12, how to send, `.example` contact, no threats, no dates or dollar amounts outside the file); 0 drafts for READY vendors; **0 sends** |
| P3 `/route` | PASS | 2 of 2 packets (Kestrelbay: Facilities Manager; Skyquay: Facilities Manager > Procurement Lead > Legal > Finance); 0 packets for the 6 not READY; every sign-off cell blank |
| P4 compliance-checker | PASS | Tools exactly Read, Grep, Glob. Latest review: 18 files, 18 unchanged since review. 16 of 16 real files OK. Planted wrong deadline caught. Planted missed name mismatch caught |
| P5 audit log | PASS | 18 rows = 18 actions (8 intake + 6 chase drafts + 2 route packets + 2 checker reviews); hash chain 18 of 18 rows verify |
| P6 Phase 1 + privacy | PASS | Phase 1: 8 of 8, its self-test 3 of 3; 75 files scanned, 0 personal words, 0 web addresses other than `.example` |
| P7 README | PASS | 7 of 7 new pieces mapped with an industry term and a "designed and directed" resume line; 0 overclaims |

Statuses: **2 READY** (Kestrelbay, Skyquay), **1 HOLD** (Bayvane), **5 BLOCKED** (Saltmarsh, Brightcurrent, Fernhollow, Clearsail, Gulfpine). Same as the locked key.

## What the checker found
| Review | Files | Real files OK | Findings on planted copies | Findings on real files |
|---|---|---|---|---|
| `reviews/2026-11-05-01-saltmarsh.md` | 3 | 2 of 2 | 1: DRAFT_WRONG_DEADLINE (says 2026-11-19; rule gives 2026-11-12) | 0 |
| `reviews/2026-11-05-02-all-vendors.md` | 18 | 16 of 16 | 3: DRAFT_WRONG_DEADLINE; INTAKE_MISSED_NAME_MISMATCH (certificate says Gulfpine Pest Solutions LLC, the others say Gulfpine Pest Control Inc.); INTAKE_WRONG_STATUS (READY should be BLOCKED) | 0 |

The checker wasn't told which files were planted or what was wrong. It recomputed each Gulfpine result from the documents, not from the evidence inside the planted file, and so caught the name mismatch the planted intake had "missed."

## Not tested, and limits (plain)
- **The checker's tool limit wasn't enforced by the harness in this run.** Claude Code loads `.claude/agents/` when a session starts. The `compliance-checker` agent was created mid-session, so it couldn't be called by name. Both reviews ran as a general-purpose agent told to follow `compliance-checker.md` word for word and to use only Read, Grep, and Glob. P4 confirms the definition file lists exactly those three tools. It can't prove which tools the run used. In a new session the agent loads with the limit enforced; that wasn't tested.
- **The skills weren't invoked as slash commands.** This session followed each `SKILL.md` step by step. Typing `/intake` etc. in a fresh Claude Code session wasn't tried.
- **P4 reads the saved review; it can't run the AI checker itself.** The report was saved word for word by the onboarding assistant, with SHA-256 hashes of every reviewed file. P4 confirms the hashes still match, so the review covers the final files. Whether the saved text matches what the checker said rests on the recorder.
- **The checker was told not to open the answer key**, by instruction only.
- **The hash chain is tamper-evident, not tamper-proof.** Editing a past row breaks it (the self-test proves this). Someone who edits a row and also regenerates the whole chain wouldn't be caught. Nothing outside the folder anchors it.
- **Tone and "why it's required" are checked by rules, not by a person:** a list of threat words, required terms, and a "Why we need it:" line with at least 6 words, plus the checker's reading. No person has read the drafts yet.
- **"0 sends"** means no audit row marked sent, no draft marked sent, and no network import in `tools/` or `.claude/`. There's no email tool in this folder. It isn't a network monitor.
- **Narrow data.** 8 vendors with one planted problem each (or none), so there's no vendor with several problems. The unreadable-document path was tested once, on a scratch copy (exit 2, nothing written, audit log unchanged), not on the real data.
- **Days waiting is 2 for everyone.** Every vendor submitted 2026-11-03, and days are counted to the demo date.
- **Audit timestamps are the real clock.** Expiry math uses the fixed demo date.

## Files Phase 2 added or changed
- Added: `tests/check_phase2.py`, `tools/onboard.py`, `.claude/skills/{intake,chase,route,status}/SKILL.md`, `.claude/agents/compliance-checker.md`, `vendors/*/intake.json` (8), `vendors/*/drafts/2026-11-05-follow-up.md` (6), `vendors/{kestrelbay-air-heat,skyquay-lift-fire}/packet.md` (2), `tests/checker-copies/` (2 planted copies), `reviews/` (2 review records), `audit/audit-log.chain.txt`, this file.
- Changed: `vendors/*/vendor.md` (Stage line set; the old value kept in a new Stage history list), `audit/audit-log.csv` (rows appended only), `README.md` (status, mapping, run commands, change log).
- Not changed: `CLAUDE.md`, `company/*`, `tests/answer-key.json`, `tests/LOCK.txt`, `tests/check_phase1.py`, `tools/make_vendors.py`, every file in `vendors/*/documents/`. Phase 1's self-test plants a word after "Submitted (". That text now lives in the Stage history line, so the Phase 1 self-test still runs unchanged.
