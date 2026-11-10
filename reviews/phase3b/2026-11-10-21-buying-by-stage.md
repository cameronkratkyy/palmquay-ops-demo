# Blind review 21: the Buying tab, by stage (D175), 11/10/2026

*Fictional company, sample records. Summarized from the reviewer's report.*

| Field | Value |
|---|---|
| Reviewer | the author's registered `checker` agent, a fresh instance (read-only tools), one round plus fixes |
| What changed | The owner asked for the Buying tab to show how a property management company actually buys, with the tools companies use for spending. Research first: Perplexity (134 sources) and three videos (an AppFolio work order sent to a vendor, Buildium requests, vendors, and bills, and Yardi's procure-to-pay). The tab now opens with "How Palmquay buys": five stages (Request, Approve, Order, Receive, Bill & pay), each with its record, where that record usually lives (example tools, named as examples only), the AI's part, who decides, and how many items wait on a person. Then a counts bar, one table of every open item by stage, a money line from the approved budget to the bill, the seven steps grouped by stage (change control on its own row, the order as a person's step), and an approval-limits box read from `company/rules.json`. Nothing was removed. Every new number is a tagged fact that Phase 3b B1 recounts from the records with its own code; no record file changed |
| How it ran | C1 every new number recounted by hand from the records; C2 no product is presented as connected; C3 real-industry accuracy against the research; C4 wording; C5 the brief's six parts with nothing dropped; C6 the recount code is independent of the build |
| Result | All six PASS. Recounted: stages 1 / 4 / 0 / 5 / 2 (12, matching "12 buying"), billed $535 + $872 = $1,407, held $872 − $713 = $159, policy numbers as in the rules file, the order a standard purchase in the Facilities Manager's tier, both invoices unpaid, budget line FAC-TURN-2026 owned by Finance |
| Applied after the review | "Waiting on approval" renamed "Waiting at the approval stage" (the stage holds two write-ups and a certification as well as an approval); "unpaid" now comes from the invoice records as a recounted number ("2 of 2 invoices unpaid"); the Order row says the purchase order "was approved by Dana Reyes, Facilities Manager" (the record shows who approved it, not who placed it); the strip says the suppliers in this sample project are fictional, next to the example tool names. B1 after the fixes: every tagged number matches |

Overall: PASS

Not changed (listed for the author): the page is wider than a phone screen on every tab (header tiles and tables), which predates this change; the recorded video still shows the earlier Buying tab.

## Manifest (SHA-256)
| File | SHA-256 |
|---|---|
| `docs/video-script.md` | 6bcb5c79f08fbad8619d713eed43ef628e479f51b73187c8f7401ccbb79760ce |
| `docs/explainer.md` | adbb94a4769a3e76b6de75cca112583b6414dae9edf9ff3fe22ac2a1c7cded05 |
| `docs/diagram.html` | 9be5af58d99728cc678a7838b466cd1604394f9d9b42f725ddde676a574d6e16 |
| `dashboard/build.py` | a26b8f99d9cd2c078c647c710bd54428ea5728e9f88da9bf82165a1e2ff6a002 |
| `README.md` | 9f9fe34c975aa4dde26bfc3259310a26171ff60b9f9ddc7ea04c233ce739955a |
| `dashboard/README.md` | 6c252112b027de0e12fad72efed714d2e7c53ee81f6d32bac6193f94a3fbf0b4 |
| `tests/check_phase3b.py` | 099e6bbffd0974af412b3446b2338835756504514a293772e732837c3976707f |
| `tests/check_phase3f.py` | 4e6ba0b296dd7c39f4ee75463aca01991be681e00a3a4a918df6f23fb862bad7 |
| `tests/suite.json` | bfdbe14c0b6cf2e53ddaed29d9fdfe99da8d0dc1a25c33698b0ad6bb5d2503b3 |
| `.github/workflows/checks.yml` | 56d9c858e5c08e067f26e3b45796b3a204ba19bd516cfd4d9a3351e09bc4c693 |
