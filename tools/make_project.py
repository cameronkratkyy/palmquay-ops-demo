"""Phase 3a test data: one fictional furnishing project (Bayfront Commons, Unit 4B) with one planted problem per
buying activity. Fake data only: fictional companies, people, SKUs, prices, and addresses; emails use .example.

    python -I -X utf8 tools/make_project.py     writes projects/unit-4b/ and company/approved-suppliers.md (refuses to overwrite)

Planted on purpose (the locked answer key is tests/answer-key-3a.json):
  1 scope     bedroom wall B missing; a king bed requested for a 10 ft bedroom wall
  2 source    the proposed sofa (GW-SOF-210) takes 42 days against a 15-day window
  3 quote     Gulfweave's delivery charge sits in a footnote, not the line items; Mangrove's quote has expired
  4 approve   rug 2 in too wide; lamps in chrome where the plan says brushed nickel; chair fabric not stated
  5 change    the approved sofa is backordered; the substitute pushes the project over budget
  6 deliver   the bed frame arrives after the install date; the dresser is addressed to the wrong unit
  7 match     Keystone bills 3 lamps at $139 against an order for 2 at $129
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "projects", "unit-4b")
RULES = json.load(open(os.path.join(ROOT, "company", "rules.json"), encoding="utf-8"))
LABEL = RULES["projects"]["partner_label"]
ADDR = "Bayfront Commons, Unit 4B, 400 Palm Quay Way, Sarasota FL (fictional)"
GW, MH, KC = "Gulfweave Furnishings", "Mangrove Home Supply", "Keystone Coast Furniture"

FILES = {}
FILES["company/approved-suppliers.md"] = f"""# Palmquay Properties: approved furniture suppliers (fictional, demo only)

Only suppliers on this list can be quoted or ordered from. All three are fictional; emails use the reserved .example domain.

| Supplier | Code | Orders email | Status |
|---|---|---|---|
| {GW} | GW | orders@gulfweave.example | Approved |
| {MH} | MH | orders@mangrovehome.example | Approved |
| {KC} | KC | orders@keystonecoast.example | Approved |
"""

FILES["projects/unit-4b/request.md"] = f"""# Furnishing request (fictional)
Project: unit-4b
Building: Bayfront Commons (fictional)
Unit: 4B
Requested by: Lena Ortiz, Property Manager (fictional)
Contact: lena.ortiz@palmquay.example
Request date: 2026-11-05
Rooms: living room, bedroom
Budget: $5,200
Install by: 2026-11-20
Must have: pet-friendly performance fabric on upholstered pieces
Living room wall A: 14 ft
Living room wall B: 12 ft
Bedroom wall A: 10 ft
Bedroom wall B:
Bed size: king
Delivery address: {ADDR}
"""

FILES["projects/unit-4b/partner-plan.md"] = f"""# Furnishing plan from the design partner (fictional)
{LABEL}
Plan for: unit-4b
Bed size in plan: queen

| Line | Item | Qty | Max width (in) | Max depth (in) | Finish | Fabric |
|---|---|---|---|---|---|---|
| 1 | Sofa | 1 | 84 | 38 | any | pet-friendly performance |
| 2 | Area rug | 1 | 96 | 120 | any | any |
| 3 | Coffee table | 1 | 48 | 24 | oak | any |
| 4 | Floor lamp | 2 | 14 | 14 | brushed nickel | any |
| 5 | Accent chair | 1 | 32 | 34 | any | pet-friendly performance |
| 6 | Bed frame, queen | 1 | 64 | 86 | oak | any |
| 7 | Nightstand | 2 | 22 | 18 | oak | any |
| 8 | Dresser | 1 | 60 | 20 | oak | any |
"""

CAT_HEAD = "| SKU | Item | Width (in) | Depth (in) | Finish | Fabric | Unit price | Lead time (days) |\n|---|---|---|---|---|---|---|---|\n"
FILES["projects/unit-4b/catalogs/GW.md"] = f"# Catalog: {GW} (fictional)\nSupplier: {GW}\n\n" + CAT_HEAD + (
    "| GW-SOF-210 | Sofa | 82 | 37 | n/a | pet-friendly performance | $1,450 | 42 |\n"
    "| GW-SOF-205 | Sofa | 83 | 37 | n/a | pet-friendly performance | $1,930 | 2 |\n"
    "| GW-CT-48 | Coffee table | 48 | 24 | oak | n/a | $340 | 10 |\n"
    "| GW-BED-Q | Bed frame, queen | 64 | 86 | oak | n/a | $690 | 12 |\n"
    "| GW-NS-22 | Nightstand | 22 | 18 | oak | n/a | $175 | 12 |\n")
FILES["projects/unit-4b/catalogs/MH.md"] = f"# Catalog: {MH} (fictional)\nSupplier: {MH}\n\n" + CAT_HEAD + (
    "| MH-SOF-118 | Sofa | 83 | 36 | n/a | pet-friendly performance | $1,520 | 7 |\n"
    "| MH-CHR-32 | Accent chair | 32 | 33 | n/a | not stated | $460 | 7 |\n"
    "| MH-DR-60 | Dresser | 60 | 20 | oak | n/a | $640 | 9 |\n")
FILES["projects/unit-4b/catalogs/KC.md"] = f"# Catalog: {KC} (fictional)\nSupplier: {KC}\n\n" + CAT_HEAD + (
    "| KC-RUG-810 | Area rug | 98 | 120 | n/a | n/a | $420 | 5 |\n"
    "| KC-RUG-96 | Area rug | 96 | 120 | n/a | n/a | $395 | 5 |\n"
    "| KC-LMP-14 | Floor lamp | 14 | 14 | chrome | n/a | $119 | 4 |\n"
    "| KC-LMP-14N | Floor lamp | 14 | 14 | brushed nickel | n/a | $129 | 4 |\n")

FILES["projects/unit-4b/proposed.md"] = """# First product picks for the plan (fictional), before approval
Picked by: Palmquay facilities team (fictional)

| Line | SKU | Qty |
|---|---|---|
| 1 | GW-SOF-210 | 1 |
| 2 | KC-RUG-810 | 1 |
| 3 | GW-CT-48 | 1 |
| 4 | KC-LMP-14 | 2 |
| 5 | MH-CHR-32 | 1 |
| 6 | GW-BED-Q | 1 |
| 7 | GW-NS-22 | 2 |
| 8 | MH-DR-60 | 1 |
"""

Q_HEAD = "| SKU | Item | Qty | Unit price | Line total |\n|---|---|---|---|---|\n"
FILES["projects/unit-4b/quotes/Q-GW-1.md"] = (f"# Quote Q-GW-1 (fictional)\nSupplier: {GW}\nQuote number: Q-GW-1\nQuote date: 2026-11-05\n"
    f"Valid until: 2026-11-30\nShip to: {ADDR}\n\n" + Q_HEAD +
    "| GW-CT-48 | Coffee table | 1 | $340 | $340 |\n| GW-BED-Q | Bed frame, queen | 1 | $690 | $690 |\n| GW-NS-22 | Nightstand | 2 | $175 | $350 |\n\n"
    "Subtotal: $1,380\n\nNotes: Prices are for in-stock items. *Delivery and setup are billed at $185 per order and are not shown in the line items.\n")
FILES["projects/unit-4b/quotes/Q-MH-1.md"] = (f"# Quote Q-MH-1 (fictional)\nSupplier: {MH}\nQuote number: Q-MH-1\nQuote date: 2026-10-18\n"
    f"Valid until: 2026-11-01\nShip to: {ADDR}\n\n" + Q_HEAD +
    "| MH-SOF-118 | Sofa | 1 | $1,520 | $1,520 |\n| MH-CHR-32 | Accent chair | 1 | $460 | $460 |\n| MH-DR-60 | Dresser | 1 | $640 | $640 |\n\n"
    "Subtotal: $2,620\nFreight: $0\n\nNotes: Freight included.\n")
FILES["projects/unit-4b/quotes/Q-KC-1.md"] = (f"# Quote Q-KC-1 (fictional)\nSupplier: {KC}\nQuote number: Q-KC-1\nQuote date: 2026-11-05\n"
    f"Valid until: 2026-11-20\nShip to: {ADDR}\n\n" + Q_HEAD +
    "| KC-RUG-96 | Area rug | 1 | $395 | $395 |\n| KC-LMP-14N | Floor lamp | 2 | $129 | $258 |\n\n"
    "Subtotal: $653\nFreight: $60\n\nNotes: none.\n")

PO_HEAD = "| SKU | Item | Supplier | Qty | Unit price | Promised delivery |\n|---|---|---|---|---|---|\n"
FILES["projects/unit-4b/approved/po-PQ-1042.md"] = (
    "# Purchase order PQ-1042 (fictional): the approved baseline\nProject: unit-4b\n"
    "Approved by: Dana Reyes, Facilities Manager (fictional)\nApproved on: 2026-11-06\nBudget: $5,200\n"
    f"Ship to: {ADDR}\n\n" + PO_HEAD +
    f"| MH-SOF-118 | Sofa | {MH} | 1 | $1,520 | 2026-11-13 |\n"
    f"| KC-RUG-96 | Area rug | {KC} | 1 | $395 | 2026-11-11 |\n"
    f"| GW-CT-48 | Coffee table | {GW} | 1 | $340 | 2026-11-16 |\n"
    f"| KC-LMP-14N | Floor lamp | {KC} | 2 | $129 | 2026-11-10 |\n"
    f"| MH-CHR-32 | Accent chair | {MH} | 1 | $460 | 2026-11-13 |\n"
    f"| GW-BED-Q | Bed frame, queen | {GW} | 1 | $690 | 2026-11-18 |\n"
    f"| GW-NS-22 | Nightstand | {GW} | 2 | $175 | 2026-11-18 |\n"
    f"| MH-DR-60 | Dresser | {MH} | 1 | $640 | 2026-11-15 |\n\n"
    f"Freight {GW}: $185\nFreight {KC}: $60\nFreight {MH}: $0\nTotal: $4,898\n\n"
    "Notes: a person made the calls the assistant routed to them. The accent chair's fabric was confirmed as performance fabric "
    "by Dana Reyes on 2026-11-06. The rug and lamps were replaced with in-spec items. Mangrove refreshed its expired quote on "
    "2026-11-06 at the same prices.\n")

FILES["projects/unit-4b/events/2026-11-07-backorder.md"] = (
    f"# Supplier notice (fictional)\nDate: 2026-11-07\nSupplier: {MH}\nSKU: MH-SOF-118\n"
    f"Notice: backordered; new ship date 2026-12-01\nProposed substitute: GW-SOF-205 from {GW}\n")

TR_HEAD = "| SKU | Supplier | Status | ETA | Ship to |\n|---|---|---|---|---|\n"
FILES["projects/unit-4b/deliveries/tracking-2026-11-12.md"] = (
    "# Delivery tracking (fictional)\nAs of: 2026-11-12\n\n" + TR_HEAD +
    f"| KC-RUG-96 | {KC} | delivered | 2026-11-11 | {ADDR} |\n"
    f"| KC-LMP-14N | {KC} | delivered | 2026-11-10 | {ADDR} |\n"
    f"| GW-CT-48 | {GW} | in transit | 2026-11-16 | {ADDR} |\n"
    f"| GW-BED-Q | {GW} | delayed | 2026-11-25 | {ADDR} |\n"
    f"| GW-NS-22 | {GW} | delivered | 2026-11-12 | {ADDR} |\n"
    f"| MH-SOF-118 | {MH} | on hold (change request) |  | {ADDR} |\n"
    f"| MH-CHR-32 | {MH} | in transit | 2026-11-13 | {ADDR} |\n"
    f"| MH-DR-60 | {MH} | in transit | 2026-11-15 | {ADDR.replace('Unit 4B', 'Unit 4D')} |\n")

FILES["projects/unit-4b/received/receipt-2026-11-12.md"] = (
    "# Received at the unit (fictional)\nAs of: 2026-11-12\nSigned by: building staff (fictional)\n\n"
    "| SKU | Qty received |\n|---|---|\n| KC-RUG-96 | 1 |\n| KC-LMP-14N | 2 |\n| GW-NS-22 | 2 |\n")

INV_HEAD = "| SKU | Item | Qty | Unit price | Line total |\n|---|---|---|---|---|\n"
FILES["projects/unit-4b/invoices/INV-GW-5521.md"] = (
    f"# Invoice INV-GW-5521 (fictional)\nSupplier: {GW}\nInvoice number: INV-GW-5521\nInvoice date: 2026-11-12\n"
    "Purchase order: PQ-1042\nPayment status: unpaid\n\n" + INV_HEAD +
    "| GW-NS-22 | Nightstand | 2 | $175 | $350 |\n\nFreight: $185\nTotal due: $535\n")
FILES["projects/unit-4b/invoices/INV-KC-3307.md"] = (
    f"# Invoice INV-KC-3307 (fictional)\nSupplier: {KC}\nInvoice number: INV-KC-3307\nInvoice date: 2026-11-12\n"
    "Purchase order: PQ-1042\nPayment status: unpaid\n\n" + INV_HEAD +
    "| KC-RUG-96 | Area rug | 1 | $395 | $395 |\n| KC-LMP-14N | Floor lamp | 3 | $139 | $417 |\n\nFreight: $60\nTotal due: $872\n")


def main():
    if os.path.exists(P):
        print(f"REFUSED - {os.path.relpath(P, ROOT)} already exists; nothing written (delete it by hand to rebuild)")
        sys.exit(3)
    for rel, text in FILES.items():
        path = os.path.join(ROOT, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            print(f"REFUSED - {rel} exists")
            sys.exit(3)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print("wrote", rel)
    print(f"{len(FILES)} files written")


if __name__ == "__main__":
    main()
