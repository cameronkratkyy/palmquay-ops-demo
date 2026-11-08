# Blind review 08: the video script rewritten as a story (v3), 11/8/2026

*Fictional company, fake data. Summarized from the two reviewers' reports (no scrubs needed).*

| Field | Value |
|---|---|
| Reviewer | the author's registered `checker` agent, two fresh instances (tools: Read, Grep, Glob, WebFetch, WebSearch; no write or send tools) |
| How it ran | Round 1 graded S1-S7 from the brief against the records; told not to open reviews/ or the results notes. Copy b carried a planted error. Round 2 re-read the one changed beat (beat 3) and recounted the spoken words. |
| Planted error caught | Yes (S7: copy b, "$48,000 roof job" vs 42000 in vendors/saltmarsh-roofing/intake.json) |
| Result | Round 1: S1-S7 PASS (script); one note on beat 3 ("sends four papers" was loose: Fernhollow and Clearsail sent incomplete sets) applied. Round 2: beat 3 PASS, 274 spoken words, 0 required fixes; its optional 32-word beat 3 applied. |

Overall: PASS

## What it checked
- S1 every name, role, number, and fact matches the records (people.md, intake.json, packet.md, request.md, CR-001, match.md).
- S2 names the four approvers with their departments and the four papers.
- S3 the problem is clear in the first 10 seconds; Lena reads as the requester.
- S4 no overclaims: no "tamper-evident"; "marks it blocked" is a status; the checker claim is limited to planted errors.
- S5 300 spoken words or fewer; every tab, heading, row, and the Play button exists on the page. Timing risk noted: about 1:49 of speech plus clicks; needs one timed practice run.
- S6 no personal data. S7 planted error found.

## Manifest (SHA-256 of the files as they stand after the round 2 edit)
| File | SHA-256 |
|---|---|
| `docs/video-script.md` | a90f2be80f550a6acbb134e34d8f8d5256e0f09b23a92cbaa2776b421f070862 |
| `docs/explainer.md` | f542682b089d630cc75f2b5a948b8a913251b618e9da98f875b21158380fcbf5 |
| `docs/diagram.html` | 4a1b1be498b23e0248894d68d00c27c89a87e0eee07b165fe2fb1bc8fac2b7a5 |
| `dashboard/build.py` | 622a90e6f4d7bf7ed1b4067f53fd41a84e0bbc1e1771bf900d8bbc0c07959168 |
| `tests/checker-copies/video-script-v3-copy-a.md` | f24106a6c15b25255cda2b5db3f9a3797261dd7c2d9cc2eff9a2bd87a7099042 |
| `tests/checker-copies/video-script-v3-copy-b.md` | 5bae926a3c844cd1453acb5c76cb489fa0aaf6da3624b58c2fdf0d688af1783e |
