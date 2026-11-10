# Blind review 20: stale counts and "sample" wording (backlog #91), 11/10/2026

*Fictional company, sample records. Summarized from the reviewer's reports.*

| Field | Value |
|---|---|
| Reviewer | the author's registered `checker` agent, two fresh instances (read-only tools), two rounds |
| What changed | The explainer and the diagram said "20 decisions waiting on people" and "31 audit log rows"; the dashboard counts 21 and 34 (audit 18 + procurement 9 + controls 4 + exceptions 3, the build's own rule). Both now say 21 and 34, and check F5 compares those two numbers in the explainer and diagram with the dashboard's tags (stricter; still 6 checks, 85 in all). Visitor-facing wording that called the demo unreal replaced with "fictional" or "sample records" in the explainer, the dashboard README, and two check labels (Phase 1 C6, Phase 3c R9). The 13 record previews on the dashboard show each record's label line as "Sample records for a demo" / "Sample document made for a demo"; the record files and their hash locks are unchanged, and Phase 3b B1 maps exactly those two label starts on the file side before comparing, so every other character must still match |
| How it ran | Round 1 graded R1 counts recounted from the raw logs, R2 wording, R3 the new F5 code, R4 no record or check-logic change beyond the labels and F5, R5 new wording reads naturally. A planted-error test ran on a copy of the repository: the explainer set back to "20 decisions" made F5 FAIL (5 of 6); restored, F5 PASS, printing dashboard [21] / [34] and explainer and diagram ([21], [34]) |
| Round 1 | R1, R3, R4, R5 PASS (34 confirmed by hand: 18 + 9 + 4 + 3; the documents log's 1 row is outside the build's count, and its one action sends nothing). **FAIL** R2: the 13 record previews still showed the records' original label line |
| Applied after round 1 | The label-line mapping in `dashboard/build.py` (display) and in `tests/check_phase3b.py` B1 (its own copy of the two pairs, not imported from the build) |
| Round 2 | R2a 0 hits for the banned word anywhere in the built page, 13 label lines in sample wording; R2b the comparison is still strict (a preview that differs in any other character, or still shows the original label, fails); R2c record files still carry their original label lines; R2d no page text claims the previews are word for word ("Quotes are word for word" refers to quotes from step output files) |

Overall: PASS

Not changed (listed for the author): the dated build logs `docs/phase*-results.md` (history), the repository's own `CLAUDE.md`, the recorded video, and a code comment in `tests/check_orgchart.py` that still calls the previews "quoted word for word."

## Manifest (SHA-256)
| File | SHA-256 |
|---|---|
| `docs/video-script.md` | 6bcb5c79f08fbad8619d713eed43ef628e479f51b73187c8f7401ccbb79760ce |
| `docs/explainer.md` | adbb94a4769a3e76b6de75cca112583b6414dae9edf9ff3fe22ac2a1c7cded05 |
| `docs/diagram.html` | 9be5af58d99728cc678a7838b466cd1604394f9d9b42f725ddde676a574d6e16 |
| `dashboard/build.py` | ec360e23910cf15209de62d6aaf5544fd5a6bcfbda1f7a64d3769c9798c16adb |
| `README.md` | 9f9fe34c975aa4dde26bfc3259310a26171ff60b9f9ddc7ea04c233ce739955a |
| `dashboard/README.md` | 6c252112b027de0e12fad72efed714d2e7c53ee81f6d32bac6193f94a3fbf0b4 |
| `tests/check_phase1.py` | 68c725bbb24a9d1de3b69a99efc7e7f3e3b40c8bf495186bf3b022dd9a495d0e |
| `tests/check_phase3b.py` | 54beed53fd1be79f94490ac398dd3d0e3135847b1bac59cff5cf402790d3fcf8 |
| `tests/check_phase3c.py` | e254821835d7cff5b144038579e894cba53dec43860d3518fa70aac4f327929c |
| `tests/check_phase3f.py` | 4e6ba0b296dd7c39f4ee75463aca01991be681e00a3a4a918df6f23fb862bad7 |
| `tests/suite.json` | bfdbe14c0b6cf2e53ddaed29d9fdfe99da8d0dc1a25c33698b0ad6bb5d2503b3 |
| `.github/workflows/checks.yml` | 56d9c858e5c08e067f26e3b45796b3a204ba19bd516cfd4d9a3351e09bc4c693 |
