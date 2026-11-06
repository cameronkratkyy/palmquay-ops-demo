"""Make the 8 fake vendors and their documents (Phase 1 test fixtures). Fake data only.

    python -I -X utf8 tools/make_vendors.py

Rewrites vendors/<slug>/ from the table below. Each vendor has ONE planted problem (or none), and the
expected results live separately in tests/answer-key.json, written by hand. tests/check_phase1.py reads
the documents (not this table) and must reach the same results on its own.
"""
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAKE = "Fake document made for a demo. Not a real company, person, policy, license, or tax ID."

# slug, legal name, trade, amount, building, scope, requester, then overrides for the planted problem
VENDORS = [
    dict(slug="kestrelbay-air-heat", name="Kestrelbay Air & Heat LLC", trade="hvac", amount=8500,
         building="Harbor Walk Lofts", scope="Replace 2 rooftop condenser fan motors", requester="Dana Reyes"),
    dict(slug="saltmarsh-roofing", name="Saltmarsh Roofing Co.", trade="roofing", amount=42000,
         building="Bayfront Commons", scope="Re-coat 18,000 sq ft flat roof", requester="Dana Reyes",
         coi_end="2026-09-30"),                                   # planted: certificate expired
    dict(slug="brightcurrent-electric", name="Brightcurrent Electric Inc.", trade="electrical", amount=27500,
         building="Seminole Point Offices", scope="Panel upgrade + exit-light replacement, floors 1-3", requester="Dana Reyes",
         gl_occ=500000, gl_agg=1000000),                          # planted: liability below minimum
    dict(slug="fernhollow-grounds", name="Fernhollow Grounds LLC", trade="landscaping", amount=14200,
         building="Palm Row Apartments", scope="12-month grounds care contract", requester="Dana Reyes",
         no_w9=True),                                             # planted: W-9 missing
    dict(slug="clearsail-janitorial", name="Clearsail Janitorial Services LLC", trade="janitorial", amount=9800,
         building="Seminole Point Offices", scope="Nightly common-area cleaning, 3 months", requester="Dana Reyes",
         addl_insured="None listed"),                             # planted: no additional insured
    dict(slug="bayvane-plumbing", name="Bayvane Plumbing Inc.", trade="plumbing", amount=19750,
         building="Harbor Walk Lofts", scope="Replace 4 water heaters in units 2A-2D", requester="Dana Reyes",
         lic_end="2026-11-28"),                                   # planted: license expires in 23 days
    dict(slug="gulfpine-pest", name="Gulfpine Pest Control Inc.", trade="pest_control", amount=6400,
         building="Palm Row Apartments", scope="Quarterly pest treatment, 4 visits", requester="Dana Reyes",
         coi_insured="Gulfpine Pest Solutions LLC"),              # planted: name on certificate doesn't match
    dict(slug="skyquay-lift-fire", name="Skyquay Lift & Fire Inc.", trade="elevator_fire", amount=120000,
         building="Bayfront Commons", scope="Modernize 2 passenger elevators + fire-alarm tie-in", requester="Dana Reyes"),
]
HIGH_RISK = {"roofing", "elevator_fire"}
LICENSED = {"hvac", "roofing", "electrical", "plumbing", "pest_control", "elevator_fire"}
LICENSE_TYPE = {"hvac": "Air conditioning contractor", "roofing": "Roofing contractor", "electrical": "Electrical contractor",
                "plumbing": "Plumbing contractor", "pest_control": "Pest control operator", "elevator_fire": "Elevator + fire alarm contractor"}


def table(title, rows):
    out = [f"# {title}", "", f"*{FAKE}*", "", "| Field | Value |", "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in rows]
    return "\n".join(out) + "\n"


def money(n):
    return f"${n:,}"


def main():
    vdir = os.path.join(ROOT, "vendors")
    if os.path.isdir(vdir):
        shutil.rmtree(vdir)
    for i, v in enumerate(VENDORS, 1):
        d = os.path.join(vdir, v["slug"], "documents")
        os.makedirs(d)
        n = f"{i:02d}"
        contact = f"office@{v['slug']}.example"
        with open(os.path.join(vdir, v["slug"], "vendor.md"), "w", encoding="utf-8") as f:
            f.write(table(f"Vendor record: {v['name']}", [
                ("Legal name", v["name"]), ("Trade", v["trade"]), ("Contact email", contact),
                ("Phone", f"(555) 010-01{n}"), ("Stage", "Submitted (documents received, not yet reviewed)"),
                ("Submitted", "2026-11-03")]))
        with open(os.path.join(d, "request.md"), "w", encoding="utf-8") as f:
            f.write(table("Work request", [
                ("Vendor", v["name"]), ("Building", v["building"]), ("Scope", v["scope"]),
                ("Contract amount", money(v["amount"])), ("Requested by", v["requester"]), ("Target start", "2026-12-01")]))
        if not v.get("no_w9"):
            with open(os.path.join(d, "w9.md"), "w", encoding="utf-8") as f:
                f.write(table("W-9: Request for Taxpayer Identification Number (sample)", [
                    ("Legal name", v["name"]), ("Tax classification", "LLC" if v["name"].endswith("LLC") else "C corporation"),
                    ("Address", f"{100 + i} Demo Street, Sarasota, FL 34236 (fictional)"),
                    ("Taxpayer ID", f"XX-XXX{n}{n} (fake)"), ("Signed", "2026-10-28")]))
        with open(os.path.join(d, "coi.md"), "w", encoding="utf-8") as f:
            f.write(table("Certificate of liability insurance (sample)", [
                ("Insured", v.get("coi_insured", v["name"])), ("Certificate holder", "Palmquay Properties"),
                ("Additional insured", v.get("addl_insured", "Palmquay Properties")),
                ("Insurer", "Demo Mutual Insurance Co. (fictional)"), ("Policy number", f"DEMO-GL-00{n}"),
                ("General liability per occurrence", money(v.get("gl_occ", 1000000))),
                ("General liability aggregate", money(v.get("gl_agg", 2000000))),
                ("Auto liability", money(1000000)), ("Workers' comp", "Statutory"),
                ("Umbrella", money(5000000) if v["trade"] in HIGH_RISK else "None"),
                ("Policy start", "2025-10-01" if v.get("coi_end") else "2026-03-01"),
                ("Policy end", v.get("coi_end", "2027-03-01"))]))
        if v["trade"] in LICENSED:
            with open(os.path.join(d, "license.md"), "w", encoding="utf-8") as f:
                f.write(table("State contractor license (sample)", [
                    ("License holder", v["name"]), ("License type", LICENSE_TYPE[v["trade"]]),
                    ("License number", f"DEMO-LIC-00{n}"), ("Issued by", "State licensing board (simulated)"),
                    ("Status", "Active"), ("Expires", v.get("lic_end", "2027-08-31"))]))
    print(f"made {len(VENDORS)} vendors in {vdir}")


if __name__ == "__main__":
    main()
