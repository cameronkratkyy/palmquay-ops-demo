---
name: certs
description: Palmquay Properties certificate check (fictional demo, Phase 3e). Opens each contractor's insurance certificate PDF (vendors/<slug>/documents/coi.pdf), reads every field, and checks the typed copy (coi.md) against it. Writes one result per contractor, docs/certificates.md, and one audit row. Nothing is sent and no record is changed. Use for "/certs" or "check the certificates against the PDFs".
---
# /certs: read the certificate PDF, check the typed copy

**Why:** intake read a typed copy of each certificate. Typing makes mistakes (a transposed digit in a policy number), and the PDF from the insurer is what counts. So the AI reads the PDF itself.

1. **Read the rules first:** the certificate is the source. Where the PDF and the typed copy differ, a person fixes the typed record and re-runs intake. The AI never edits a record, never contacts the insurer or the contractor, and nothing is sent.
2. **Read each PDF:** `python -I -X utf8 tools/certs.py read vendors/<slug>/documents/coi.pdf`. It reads text PDFs only (no OCR). A scan, or a PDF whose fonts it can't map (browser- or Word-made files often embed subset fonts), comes back with no fields. That is not a pass: the contractor goes to a person.
3. **Check all 8 and log once:** `python -I -X utf8 tools/certs.py check`. It writes `documents/coi-check.json` per contractor (fields read, every difference, the next step), `docs/certificates.md` for a person to read, and exactly one row in `audit/documents-log.csv` (hash-chained). A second run is refused.
4. **Report:** how many certificates were read, how many match, and each difference as "X on the certificate, Y in the typed record," with who fixes it (the Facilities Manager, who owns contractor records).
5. **Verify the log:** `python -I -X utf8 tools/certs.py verify-log` must say OK.

No OCR, no network, nothing is sent.
