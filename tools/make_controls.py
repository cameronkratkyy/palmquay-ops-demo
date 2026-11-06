"""Phase 3c test data: the inputs for the controls borrowed from the author's real public-agency procurement packet
(structure only; every name, number, and document here is made up).

    python -I -X utf8 tools/make_controls.py      write the inputs below (refuses to overwrite an existing file)

Writes:
- vendors/<slug>/disclosures/conflict-of-interest.md for all 8 contractors (Kestrelbay discloses an owner related to its approver)
- company/exclusion-list.md (a stand-in for a government exclusion list; Gulfpine's insurance names a listed company)
- projects/unit-4b/funding.md (the budget line the order is charged to)
- projects/unit-4b/closeout/2026-11-12-gulfweave-completion.md (a supplier says everything was delivered; tracking says not)
Nothing here sends, signs, orders, or pays, and nothing opens a network connection.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAKE = "*Fake document made for a demo. Not a real company, person, signature, or record.*"

SIGNERS = {  # slug: (firm as on the W-9, signer, title)
    "bayvane-plumbing": ("Bayvane Plumbing Inc.", "Grant Holloway", "President"),
    "brightcurrent-electric": ("Brightcurrent Electric Inc.", "Lydia Chen", "Owner"),
    "clearsail-janitorial": ("Clearsail Janitorial Services LLC", "Nina Patel", "Managing Member"),
    "fernhollow-grounds": ("Fernhollow Grounds LLC", "Marco Delgado", "Owner"),
    "gulfpine-pest": ("Gulfpine Pest Control Inc.", "Derek Mills", "President"),
    "kestrelbay-air-heat": ("Kestrelbay Air & Heat LLC", "Tomas Ferreira", "Managing Member"),
    "saltmarsh-roofing": ("Saltmarsh Roofing Co.", "Owen Pratt", "President"),
    "skyquay-lift-fire": ("Skyquay Lift & Fire Inc.", "Alicia Romero", "Vice President"),
}
DISCLOSED = {"kestrelbay-air-heat": [("Ray Reyes", "Brother of Dana Reyes, Facilities Manager", "Owns 10% of the firm")]}


def write(rel, text):
    path = os.path.join(ROOT, *rel.split("/"))
    if os.path.exists(path):
        raise SystemExit(f"refused: {rel} already exists")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(text.strip() + "\n")
    return rel


def disclosure(slug):
    firm, signer, title = SIGNERS[slug]
    rel = DISCLOSED.get(slug, [])
    rows = "\n".join(f"| {p} | {r} | {i} |" for p, r, i in rel) or "| none | | |"
    return f"""# Conflict-of-interest disclosure (fictional)

{FAKE}

| Field | Value |
|---|---|
| Firm | {firm} |
| Signed by | {signer} |
| Title | {title} |
| Date signed | 2026-11-03 |
| No one was paid or promised anything to help win this work | Yes |
| No Palmquay employee, officer, or relative of one has an interest in this firm or this work | {"No (see below)" if rel else "Yes"} |

## Disclosed relationships
| Person | Relationship | Interest |
|---|---|---|
{rows}

By signing, the firm certifies the statements above are true and will update this form if anything changes.
"""


EXCLUSIONS = f"""# Exclusion list (fictional)

{FAKE} A made-up stand-in for a government exclusion list. A listed party can't be hired or paid while its exclusion is active.

As of: 2026-11-05

| Excluded party | Type | Excluded from | Excluded until | Reason |
|---|---|---|---|---|
| Gulfpine Pest Solutions LLC | Firm | 2026-03-16 | 2029-03-15 | Debarred: false certifications on an earlier contract |
| Coralline Haulage Co. | Firm | 2025-08-01 | 2028-07-31 | Debarred: unpaid wages on an earlier contract |
| Brenton Ashgrove | Individual | 2026-01-12 | 2027-01-11 | Suspended pending review |
"""

FUNDING = f"""# Funding record (fictional)

{FAKE}

Project: unit-4b
Budget line: FAC-TURN-2026
Description: Unit turnover furnishing, Bayfront Commons (fictional)
Approved amount: $5,200
Committed before this order: $0
Available: $5,200
Budget owner: Finance
"""

COMPLETION = f"""# Supplier completion notice (fictional)

{FAKE}

Supplier: Gulfweave Furnishings
Order: PQ-1042
Date: 2026-11-12
Signed by: Paula Vance, Delivery Manager (fictional)
Statement: All items on order PQ-1042 from Gulfweave Furnishings have been delivered and installed. We request sign-off on completion.
"""


def main():
    made = [write(f"vendors/{s}/disclosures/conflict-of-interest.md", disclosure(s)) for s in sorted(SIGNERS)]
    made.append(write("company/exclusion-list.md", EXCLUSIONS))
    made.append(write("projects/unit-4b/funding.md", FUNDING))
    made.append(write("projects/unit-4b/closeout/2026-11-12-gulfweave-completion.md", COMPLETION))
    print(f"wrote {len(made)} files:")
    for m in made:
        print("  " + m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
