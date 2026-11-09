# Insurance certificates, read from the PDF (fictional company, sample records)

Until Phase 3e, intake read a typed copy of each contractor's certificate (`documents/coi.md`). Here the AI opens the certificate PDF itself (`documents/coi.pdf`), reads every field, and checks the typed copy against it. **The certificate is the source:** where they differ, a person fixes the typed record and re-runs intake. The AI changed no record, and nothing was sent.

| Contractor | Fields read from the PDF | Result |
|---|---|---|
| Bayvane Plumbing Inc. (`bayvane-plumbing`) | 12 | matches the typed record |
| Brightcurrent Electric Inc. (`brightcurrent-electric`) | 12 | matches the typed record |
| Clearsail Janitorial Services LLC (`clearsail-janitorial`) | 12 | matches the typed record |
| Fernhollow Grounds LLC (`fernhollow-grounds`) | 12 | differs: Policy number is DEMO-GL-0040 on the certificate but DEMO-GL-0004 in the typed record |
| Gulfpine Pest Solutions LLC (`gulfpine-pest`) | 12 | matches the typed record |
| Kestrelbay Air & Heat LLC (`kestrelbay-air-heat`) | 12 | matches the typed record |
| Saltmarsh Roofing Co. (`saltmarsh-roofing`) | 12 | matches the typed record |
| Skyquay Lift & Fire Inc. (`skyquay-lift-fire`) | 12 | matches the typed record |
