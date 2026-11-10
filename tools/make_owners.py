"""Phase 3g sample records: 8 new property owners with their packets (fictional company, sample records).
Written 11/10/2026 with the answer key (tests/answer-key-3g.json) before tools/owners.py or any owner skill existed.
Ten problems are planted on purpose; one owner is clean (a control case: the check proves no false alarms).

    python -I -X utf8 tools/make_owners.py      write owners/<slug>/... (refuses to overwrite an existing file)

Every person, address, parcel, policy, bank, and tax ID here is made up. Emails use .example (a reserved domain that can't
receive mail); phones use 555-01xx. Full bank account numbers and tax IDs are never stored: only the last 4, masked.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABEL = "*Sample records for a demo. Not a real person, property, policy, bank account, or tax ID.*"
COUNTY_LABEL = ("*Sample record shaped like a county property appraiser's public listing. Saved to this folder by Talia Brooks, "
                "Owner Onboarding Coordinator, on {saved}. Not a real parcel; the AI compares it, it doesn't look anything up.*")

OWNERS = {
    "whitlock": {
        "owner": {"Owner name(s), as the owner wrote them": "Gregory Whitlock and Ana Whitlock", "Owner type": "Two individuals",
                  "Contact email": "g.whitlock@owner-mail.example", "Phone": "(555) 010-0201",
                  "Mailing address": "88 Juniper Ridge Rd, Asheville, NC 28801 (fictional)", "Mailing country": "United States",
                  "Property address": "2217 Saltwhistle Ln, Sarasota, FL 34232 (fictional)", "County": "Sarasota",
                  "Property type": "Single-family house", "Bedrooms / baths": "3 / 2", "Occupied": "No (vacant)",
                  "Association": "None", "Keys handed over": "2 door keys, 1 garage remote", "Utilities while vacant": "In the owners' name",
                  "Submitted": "2026-11-02"},
        "agreement": {"id": "PQ-MA-0201", "owners": "Gregory Whitlock; Ana Whitlock", "effective": "2026-11-15",
                      "sign": [("Gregory Whitlock", "Gregory Whitlock", "Owner", "2026-11-02"), ("Ana Whitlock", "Ana Whitlock", "Owner", "")]},
        "county": {"owners": "WHITLOCK GREGORY; WHITLOCK ANA", "parcel": "DEMO-0471-02-0019", "use": "Single family", "built": "1971",
                   "sale": "2014-05-20", "saved": "2026-11-04"},
        "w9": {"name": "Gregory Whitlock", "class": "Individual", "tin": "XXX-XX-0201 (sample)", "signed": "2026-11-02"},
        "ach": {"holder": "Gregory Whitlock; Ana Whitlock", "last4": "4471", "signed_by": "Gregory Whitlock", "signed": "2026-11-02"},
        "ins": {"type": "Landlord dwelling policy (DP-3)", "named": "Gregory Whitlock; Ana Whitlock", "limit": "$300,000",
                "ai": "Palmquay Properties", "interest": "None", "num": "DEMO-DP3-0201", "period": "2026-09-01 to 2027-09-01"},
    },
    "petrakis": {
        "owner": {"Owner name(s), as the owner wrote them": "Nadia Petrakis", "Owner type": "Individual",
                  "Contact email": "nadia.petrakis@owner-mail.example", "Phone": "(555) 010-0202",
                  "Mailing address": "51 Larchmont Ave, Columbus, OH 43214 (fictional)", "Mailing country": "United States",
                  "Property address": "4410 Kestrelwood Ct, Sarasota, FL 34238 (fictional)", "County": "Sarasota",
                  "Property type": "Single-family house", "Bedrooms / baths": "4 / 3", "Occupied": "No (vacant)",
                  "Association": "None", "Keys handed over": "3 door keys, 1 garage remote", "Utilities while vacant": "In the owner's name",
                  "Bought the home": "2026-10-16 (the owner's words)", "Submitted": "2026-11-03"},
        "agreement": {"id": "PQ-MA-0202", "owners": "Nadia Petrakis", "effective": "2026-11-15",
                      "sign": [("Nadia Petrakis", "Nadia Petrakis", "Owner", "2026-11-03")]},
        "county": {"owners": "HALVORSEN DALE", "parcel": "DEMO-0583-11-0042", "use": "Single family", "built": "1998",
                   "sale": "2018-02-09", "saved": "2026-11-04"},
        "w9": {"name": "Nadia Petrakis", "class": "Individual", "tin": "XXX-XX-0202 (sample)", "signed": "2026-11-03"},
        "ach": {"holder": "Nadia Petrakis", "last4": "1186", "signed_by": "Nadia Petrakis", "signed": "2026-11-03"},
        "ins": {"type": "Landlord dwelling policy (DP-3)", "named": "Nadia Petrakis", "limit": "$300,000",
                "ai": "Palmquay Properties", "interest": "None", "num": "DEMO-DP3-0202", "period": "2026-10-16 to 2027-10-16"},
    },
    "fontaine": {
        "owner": {"Owner name(s), as the owner wrote them": "Claire Fontaine", "Owner type": "Individual",
                  "Contact email": "claire.fontaine@owner-mail.example", "Phone": "(555) 010-0203",
                  "Mailing address": "540 Maple Crescent, Kingston, ON K7L 2B8 (fictional)", "Mailing country": "Canada",
                  "Property address": "915 Brinemoor Dr, Venice, FL 34285 (fictional)", "County": "Sarasota",
                  "Property type": "Single-family house", "Bedrooms / baths": "2 / 2", "Occupied": "No (vacant)",
                  "Association": "None", "Keys handed over": "2 door keys", "Utilities while vacant": "In the owner's name",
                  "Submitted": "2026-11-02"},
        "agreement": {"id": "PQ-MA-0203", "owners": "Claire Fontaine", "effective": "2026-11-15",
                      "sign": [("Claire Fontaine", "Claire Fontaine", "Owner", "2026-11-02")]},
        "county": {"owners": "FONTAINE CLAIRE", "parcel": "DEMO-0712-05-0007", "use": "Single family", "built": "1974",
                   "sale": "2021-01-12", "saved": "2026-11-04"},
        "lead": {"by": "Claire Fontaine", "known": "No known lead-based paint or hazards", "reports": "None available",
                 "pamphlet": "Palmquay gives each tenant the EPA pamphlet before the lease is signed", "signed": "2026-11-02"},
        "ach": {"holder": "Claire Fontaine", "last4": "3390", "signed_by": "Claire Fontaine", "signed": "2026-11-02"},
        "ins": {"type": "Landlord dwelling policy (DP-3)", "named": "Claire Fontaine", "limit": "$300,000",
                "ai": "Palmquay Properties", "interest": "None", "num": "DEMO-DP3-0203", "period": "2026-08-01 to 2027-08-01"},
    },
    "coralwick": {
        "owner": {"Owner name(s), as the owner wrote them": "Coralwick Rentals LLC (Derrick Ostrowski, manager)", "Owner type": "LLC",
                  "Contact email": "derrick@coralwick-rentals.example", "Phone": "(555) 010-0204",
                  "Mailing address": "7 Bramblecrest Ln, Lakewood Ranch, FL 34202 (fictional)", "Mailing country": "United States",
                  "Property address": "6032 Driftmark Way, Lakewood Ranch, FL 34202 (fictional)", "County": "Manatee",
                  "Property type": "Townhome", "Bedrooms / baths": "3 / 3", "Occupied": "No (vacant)",
                  "Association": "Driftmark Village HOA (fictional)", "Keys handed over": "2 door keys, 1 pool fob", "Utilities while vacant": "In the LLC's name",
                  "Submitted": "2026-11-01"},
        "agreement": {"id": "PQ-MA-0204", "owners": "Coralwick Rentals LLC", "effective": "2026-11-15",
                      "sign": [("Derrick Ostrowski", "Coralwick Rentals LLC", "Manager", "2026-11-01")]},
        "county": {"owners": "CORALWICK RENTALS LLC", "parcel": "DEMO-1690-30-0115", "use": "Townhouse", "built": "2016",
                   "sale": "2023-07-28", "saved": "2026-11-04"},
        "w9": {"name": "Coralwick Rentals LLC", "class": "LLC (taxed as a partnership)", "tin": "XX-XXX0204 (sample)", "signed": "2026-11-01"},
        "ach": {"holder": "Derrick Ostrowski", "last4": "7752", "signed_by": "Derrick Ostrowski", "signed": "2026-11-01"},
        "ins": {"type": "Landlord dwelling policy (DP-3)", "named": "Coralwick Rentals LLC", "limit": "$500,000",
                "ai": "Palmquay Properties", "interest": "None", "num": "DEMO-DP3-0204", "period": "2026-07-01 to 2027-07-01"},
        "assoc": {"name": "Driftmark Village HOA (fictional)", "approval": "Not required (the owner registers each tenant with the HOA office)",
                  "min": "6 months", "fee": "None", "dated": "2026-02-01"},
    },
    "haddad": {
        "owner": {"Owner name(s), as the owner wrote them": "Beverly Haddad", "Owner type": "Individual",
                  "Contact email": "bev.haddad@owner-mail.example", "Phone": "(555) 010-0205",
                  "Mailing address": "26 Osprey Point Dr, Venice, FL 34285 (fictional)", "Mailing country": "United States",
                  "Property address": "1340 Lanternfish Cir, Venice, FL 34293 (fictional)", "County": "Sarasota",
                  "Property type": "Single-family house", "Bedrooms / baths": "3 / 2", "Occupied": "Yes (tenant in place)",
                  "Current manager": "Tidewell Rentals (fictional), leaving 2026-11-14", "Association": "None",
                  "Keys handed over": "Coming from Tidewell Rentals", "Utilities while vacant": "Not vacant: the tenant pays electric and water",
                  "Submitted": "2026-11-02"},
        "agreement": {"id": "PQ-MA-0205", "owners": "Beverly Haddad", "effective": "2026-11-15",
                      "sign": [("Beverly Haddad", "Beverly Haddad", "Owner", "2026-11-02")]},
        "county": {"owners": "HADDAD BEVERLY", "parcel": "DEMO-0890-14-0031", "use": "Single family", "built": "1986",
                   "sale": "2011-09-30", "saved": "2026-11-04"},
        "w9": {"name": "Beverly Haddad", "class": "Individual", "tin": "XXX-XX-0205 (sample)", "signed": "2026-11-02"},
        "ach": {"holder": "Beverly Haddad", "last4": "5208", "signed_by": "Beverly Haddad", "signed": "2026-11-02"},
        "ins": {"type": "Homeowner policy (HO-3, owner-occupied)", "named": "Beverly Haddad", "limit": "$300,000",
                "ai": "Palmquay Properties", "interest": "None", "num": "DEMO-HO3-0205", "period": "2026-04-01 to 2027-04-01"},
        "lease": {"tenant": "Marco Ellison", "email": "marco.ellison@tenant-mail.example", "term": "2026-03-01 to 2027-02-28",
                  "rent": "$2,350", "deposit": "$2,400", "advance": "$0", "signed": "2026-02-20"},
        "transfer": {"from": "Tidewell Rentals (fictional), the outgoing manager", "from_email": "trust@tidewell-rentals.example",
                     "deposit": "$2,200", "advance": "$0", "interest": "$0 (non-interest-bearing account)", "on": "2026-11-03"},
    },
    "varma": {
        "owner": {"Owner name(s), as the owner wrote them": "Sunita Varma", "Owner type": "Individual",
                  "Contact email": "sunita.varma@owner-mail.example", "Phone": "(555) 010-0206",
                  "Mailing address": "1450 Wrenfield St, Chicago, IL 60614 (fictional)", "Mailing country": "United States",
                  "Property address": "Unit 304, 120 Heronmark Blvd, Sarasota, FL 34236 (fictional)", "County": "Sarasota",
                  "Property type": "Condo", "Bedrooms / baths": "2 / 2", "Occupied": "No (vacant)",
                  "Association": "Heronmark Towers Condominium Association (fictional)", "Keys handed over": "2 door keys, 1 garage fob, 1 mailbox key",
                  "Utilities while vacant": "In the owner's name", "Submitted": "2026-11-03"},
        "agreement": {"id": "PQ-MA-0206", "owners": "Sunita Varma", "effective": "2026-11-15",
                      "sign": [("Sunita Varma", "Sunita Varma", "Owner", "2026-11-03")]},
        "county": {"owners": "VARMA SUNITA", "parcel": "DEMO-2041-00-3040", "use": "Condominium", "built": "2008",
                   "sale": "2020-03-16", "saved": "2026-11-04"},
        "ach": {"holder": "Sunita Varma", "last4": "6634", "signed_by": "Sunita Varma", "signed": "2026-11-03"},
        "ins": {"type": "Landlord condo unit-owner policy (HO-6, rented to others)", "named": "Sunita Varma", "limit": "$300,000",
                "ai": "None", "interest": "Palmquay Properties", "num": "DEMO-HO6-0206", "period": "2026-05-01 to 2027-05-01"},
        "assoc": {"name": "Heronmark Towers Condominium Association (fictional)",
                  "approval": "Not required (the owner registers each tenant with the association office)", "min": "3 months", "fee": "None",
                  "dated": "2025-12-01"},
    },
    "brandt": {
        "owner": {"Owner name(s), as the owner wrote them": "James Brandt and Kelly Brandt", "Owner type": "Two individuals",
                  "Contact email": "brandt.family@owner-mail.example", "Phone": "(555) 010-0207",
                  "Mailing address": "300 Cypress Hollow Rd, Tampa, FL 33618 (fictional)", "Mailing country": "United States",
                  "Property address": "3906 Gullhaven Ter, Bradenton, FL 34209 (fictional)", "County": "Manatee",
                  "Property type": "Single-family house", "Bedrooms / baths": "3 / 2", "Occupied": "Yes (tenant in place)",
                  "Current manager": "None (the owners managed it themselves)", "Association": "None",
                  "Keys handed over": "2 door keys, 1 garage remote", "Utilities while vacant": "Not vacant: the tenant pays electric and water",
                  "Submitted": "2026-11-01"},
        "agreement": {"id": "PQ-MA-0207", "owners": "James Brandt; Kelly Brandt", "effective": "2026-11-15",
                      "sign": [("James Brandt", "James Brandt", "Owner", "2026-11-01"), ("Kelly Brandt", "Kelly Brandt", "Owner", "2026-11-01")]},
        "county": {"owners": "BRANDT JAMES; BRANDT KELLY", "parcel": "DEMO-3315-08-0270", "use": "Single family", "built": "2004",
                   "sale": "2017-04-21", "saved": "2026-11-04"},
        "w9": {"name": "James Brandt", "class": "Individual", "tin": "XXX-XX-0207 (sample)", "signed": "2026-11-01"},
        "ach": {"holder": "James Brandt; Kelly Brandt", "last4": "9015", "signed_by": "James Brandt", "signed": "2026-11-01"},
        "ins": {"type": "Landlord dwelling policy (DP-3)", "named": "James Brandt; Kelly Brandt", "limit": "$300,000",
                "ai": "Palmquay Properties", "interest": "None", "num": "DEMO-DP3-0207", "period": "2026-06-01 to 2027-06-01"},
        "lease": {"tenant": "Danielle Foster", "email": "danielle.foster@tenant-mail.example", "term": "2026-06-01 to 2027-05-31",
                  "rent": "$2,050", "deposit": "$2,100", "advance": "$0", "signed": "2026-05-18"},
        "transfer": {"from": "James Brandt and Kelly Brandt, the owners (they held the deposit themselves)", "from_email": "brandt.family@owner-mail.example",
                     "deposit": "$2,100", "advance": "$0", "interest": "$0 (non-interest-bearing account)", "on": "2026-11-04"},
    },
    "marsh": {
        "owner": {"Owner name(s), as the owner wrote them": "Helen Marsh", "Owner type": "Individual",
                  "Contact email": "helen.marsh@owner-mail.example", "Phone": "(555) 010-0208",
                  "Mailing address": "62 Palmetto Glen Ct, Sarasota, FL 34231 (fictional)", "Mailing country": "United States",
                  "Property address": "Unit 2B, 410 Seagrape Hollow Way, Bradenton, FL 34210 (fictional)", "County": "Manatee",
                  "Property type": "Condo", "Bedrooms / baths": "2 / 2", "Occupied": "No (vacant)",
                  "Association": "Seagrape Hollow Condominium Association (fictional)", "Keys handed over": "2 door keys, 1 gate fob, 1 mailbox key",
                  "Utilities while vacant": "In the owner's name", "Submitted": "2026-11-02"},
        "agreement": {"id": "PQ-MA-0208", "owners": "Helen Marsh", "effective": "2026-11-15",
                      "sign": [("Helen Marsh", "Helen Marsh", "Owner", "2026-11-02")]},
        "county": {"owners": "MARSH HELEN", "parcel": "DEMO-2208-02-0020", "use": "Condominium", "built": "2006",
                   "sale": "2016-10-05", "saved": "2026-11-04"},
        "w9": {"name": "Helen Marsh", "class": "Individual", "tin": "XXX-XX-0208 (sample)", "signed": "2026-11-02"},
        "ach": {"holder": "Helen Marsh", "last4": "2867", "signed_by": "Helen Marsh", "signed": "2026-11-02"},
        "ins": {"type": "Landlord condo unit-owner policy (HO-6, rented to others)", "named": "Helen Marsh", "limit": "$300,000",
                "ai": "Palmquay Properties", "interest": "None", "num": "DEMO-HO6-0208", "period": "2026-03-01 to 2027-03-01"},
        "assoc": {"name": "Seagrape Hollow Condominium Association (fictional)",
                  "approval": "Required before move-in (the association approves every lease and every tenant)",
                  "min": "7 months", "fee": "$100 per application", "due": "At least 20 days before move-in", "dated": "2026-03-01"},
    },
}


def table(rows):
    return "| Field | Value |\n|---|---|\n" + "".join(f"| {k} | {v} |\n" for k, v in rows)


def files(slug, o):
    out = {}
    out["owner.md"] = f"# Owner and property information form: {o['owner']['Owner name(s), as the owner wrote them']}\n\n{LABEL}\n\n" + table(o["owner"].items())
    a = o["agreement"]
    sig = "| Signer | Signing for | Capacity | Signed |\n|---|---|---|---|\n" + "".join(f"| {n} | {f} | {c} | {d} |\n" for n, f, c, d in a["sign"])
    sig += "| (blank) | Palmquay Properties | Broker of Record | |\n"
    out["documents/agreement.md"] = (
        f"# Residential management agreement {a['id']} (sample)\n\n{LABEL}\n\n"
        + table([("Agreement", a["id"]), ("Owner(s) named", a["owners"]), ("Property", o["owner"]["Property address"]),
                 ("Effective date", a["effective"]), ("Term", "12 months, renews monthly after that"),
                 ("Management fee", "9% of rent collected"), ("Owner reserve", "$500, kept in Palmquay's trust account for the owner's repairs"),
                 ("Insurance the owner keeps", "A landlord policy with at least $300,000 liability, naming Palmquay Properties as additional insured"),
                 ("Pages", "8 of 8 received")])
        + "\n## Signatures\n\n" + sig)
    c = o["county"]
    out["documents/county-record.md"] = (
        f"# County property record (sample): {o['owner']['Property address']}\n\n{COUNTY_LABEL.format(saved=c['saved'])}\n\n"
        + table([("Owner(s) of record", c["owners"]), ("Parcel ID", c["parcel"]), ("Site address", o["owner"]["Property address"]),
                 ("County", o["owner"]["County"]), ("Use", c["use"]), ("Year built", c["built"]), ("Last sale recorded", c["sale"])]))
    if "w9" in o:
        w = o["w9"]
        out["documents/w9.md"] = (f"# W-9: Request for Taxpayer Identification Number (sample)\n\n{LABEL}\n\n"
                                  + table([("Name", w["name"]), ("Tax classification", w["class"]), ("Taxpayer ID", w["tin"]), ("Signed", w["signed"])]))
    b = o["ach"]
    out["documents/ach.md"] = (
        f"# Owner payment (ACH direct deposit) authorization (sample)\n\n{LABEL}\n\n"
        + table([("Account holder name(s)", b["holder"]), ("Bank", "Gulfline Community Bank (sample)"), ("Routing number", "DEMO-ROUTING"),
                 ("Account number", f"XXXXXX{b['last4']} (sample; the full number is never stored here)"), ("Account type", "Checking"),
                 ("Supporting proof", f"Voided check showing the name(s): {b['holder']}"), ("Signed by", b["signed_by"]), ("Signed", b["signed"])]))
    i = o["ins"]
    out["documents/insurance.md"] = (
        f"# Insurance declarations page (sample)\n\n{LABEL}\n\n"
        + table([("Policy type", i["type"]), ("Insurer", "Seagrass Mutual (sample)"), ("Named insured", i["named"]),
                 ("Property", o["owner"]["Property address"]), ("Liability limit", i["limit"]), ("Additional insured", i["ai"]),
                 ("Additional interest", i["interest"]), ("Policy number", i["num"]), ("Policy period", i["period"])]))
    if "assoc" in o:
        s = o["assoc"]
        rows = [("Association", s["name"]), ("Lease approval by the association", s["approval"]), ("Minimum lease", s["min"]),
                ("Application fee", s["fee"])] + ([("Application due", s["due"])] if "due" in s else []) + [("Rules dated", s["dated"])]
        out["documents/association.md"] = f"# Association leasing rules, as sent by the owner (sample)\n\n{LABEL}\n\n" + table(rows)
    if "lead" in o:
        L = o["lead"]
        out["documents/lead-disclosure.md"] = (
            f"# Lead-based paint disclosure, owner's part (sample)\n\n{LABEL}\n\n"
            + table([("Signed by", L["by"]), ("Known lead-based paint or hazards", L["known"]), ("Reports or records", L["reports"]),
                     ("EPA pamphlet", L["pamphlet"]), ("Signed", L["signed"])]))
    if "lease" in o:
        L = o["lease"]
        out["tenant/lease.md"] = (f"# Lease summary, from the signed lease (sample)\n\n{LABEL}\n\n"
                                  + table([("Tenant", L["tenant"]), ("Tenant email", L["email"]), ("Lease term", L["term"]),
                                           ("Monthly rent", L["rent"]), ("Security deposit", L["deposit"]), ("Advance rent", L["advance"]),
                                           ("Signed", L["signed"])]))
        t = o["transfer"]
        out["tenant/deposit-transfer.md"] = (
            f"# Deposit transfer statement (sample)\n\n{LABEL}\n\n"
            + table([("From", t["from"]), ("From email", t["from_email"]), ("Tenant", L["tenant"]), ("Security deposit transferred", t["deposit"]),
                     ("Advance rent transferred", t["advance"]), ("Interest", t["interest"]), ("Transferred on", t["on"]),
                     ("Into", "Palmquay Tenant Deposit Trust Account, Gulfline Community Bank (sample)")]))
    return out


def main():
    made = 0
    for slug, o in OWNERS.items():
        for rel, body in files(slug, o).items():
            f = os.path.join(ROOT, "owners", slug, *rel.split("/"))
            if os.path.exists(f):
                print(f"refused: {os.path.relpath(f, ROOT)} already exists")
                return 3
            os.makedirs(os.path.dirname(f), exist_ok=True)
            with open(f, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(body)
            made += 1
    print(f"made {made} files for {len(OWNERS)} owners")
    return 0


if __name__ == "__main__":
    sys.exit(main())
