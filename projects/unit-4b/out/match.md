# Three-way match: invoice vs. order PQ-1042 vs. receipt (fictional)

| Invoice | SKU | Billed | Ordered | Received | Flags |
|---|---|---|---|---|---|
| INV-GW-5521 | GW-NS-22 | 2 x $175 | 2 x $175 | 2 | ok |
| INV-GW-5521 | freight | $185 | $185 | | ok |
| INV-KC-3307 | KC-RUG-96 | 1 x $395 | 1 x $395 | 1 | ok |
| INV-KC-3307 | KC-LMP-14N | 3 x $139 | 2 x $129 | 2 | PRICE_MISMATCH, QTY_MISMATCH |
| INV-KC-3307 | freight | $60 | $60 | | ok |

| Invoice | Result | Billed | Should be | Difference |
|---|---|---|---|---|
| INV-GW-5521 | MATCH | as ordered |  |  |
| INV-KC-3307 | HOLD | $872 | $713 | $159 |

Payment is approved by Finance (?). The assistant flags differences and never marks an invoice paid.
