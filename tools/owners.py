"""Phase 3g helpers: bringing on a new property owner (fictional company, sample records).
Where a script is more reliable than reading by eye: name matching across documents, the year-built rule, deposit math, dates.
Nothing here signs, sends, moves money, enters anything in any software, or opens a network connection.

    python -I -X utf8 tools/owners.py intake <owner | all>     /owner-intake: read the packet + the saved county record; write intake.json
    python -I -X utf8 tools/owners.py takeover <owner | all>   /takeover: a tenant already lives there; compare the lease with the deposit transfer
    python -I -X utf8 tools/owners.py chase <owner | all>      /owner-chase: one follow-up draft per owner who isn't READY
    python -I -X utf8 tools/owners.py setup <owner | all>      /owner-setup: a draft setup sheet for the property management software
    python -I -X utf8 tools/owners.py status                   one line per owner (read-only)
    python -I -X utf8 tools/owners.py log-review <path>        log 1 row for a saved checker review
    python -I -X utf8 tools/owners.py verify-log               recompute the owners log's hash chain (read-only)

Each action writes its outputs and appends exactly one row per owner to audit/owners-log.csv; a second run is refused.
Exit codes: 0 ok, 2 a file is unreadable (stop), 3 refused (already done, or the log's chain is broken).
"""
import csv
import datetime as dt
import glob
import hashlib
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(ROOT, "company", "owner-rules.json"), encoding="utf-8"))
CODES = R["issue_codes"]
LOG = os.path.join(ROOT, "audit", "owners-log.csv")
CHAIN = os.path.join(ROOT, "audit", "owners-log.chain.txt")
HEADER = "timestamp,actor,owner,action,detail,result"
ACTOR = "owner-assistant"
DEMO = dt.date.fromisoformat(R["demo_date"])
DEADLINE = str(DEMO + dt.timedelta(days=R["chase_deadline_days"]))
GATES = ["accepted", "money", "leasing"]
LABEL = "*Sample records for a demo."


class Refused(Exception):
    pass


# ------------------------------------------------------------- reading -------------------------------------------------------------
def rel(*a):
    return "/".join(a)


def read(relpath):
    return open(os.path.join(ROOT, *relpath.split("/")), encoding="utf-8").read()


def exists(relpath):
    return os.path.exists(os.path.join(ROOT, *relpath.split("/")))


def table(relpath):
    """Field | Value rows of a record, in order."""
    out = {}
    if not exists(relpath):
        return out
    for line in read(relpath).splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", line)
        if m and m.group(1) not in ("Field", "---") and m.group(1) not in out:
            out[m.group(1)] = m.group(2)
    return out


def signatures(relpath):
    lines = read(relpath).splitlines()
    i = next(i for i, l in enumerate(lines) if l.startswith("| Signer |"))
    out = []
    for l in lines[i + 2:]:
        if not l.startswith("|"):
            break
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        out.append({"signer": c[0], "for": c[1], "capacity": c[2], "signed": c[3] if len(c) > 3 else ""})
    return out


def dollars(s):
    return int(re.sub(r"[^\d]", "", s.split("(")[0]))


def person_key(s):
    """'WHITLOCK GREGORY' and 'Gregory Whitlock' are the same person; word order and case don't matter."""
    return " ".join(sorted(w for w in re.findall(r"[a-z]+", s.lower()) if w != "and"))


def split_names(s):
    return [x.strip() for x in s.split(";") if x.strip()]


def team():
    out = {}
    lines = read("company/owner-team.md").splitlines()
    i = next(i for i, l in enumerate(lines) if l.startswith("| Role |"))
    for l in lines[i + 2:]:
        if not l.startswith("|"):
            break
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        out[c[0]] = {"name": c[1], "email": c[3]}
    return out


TEAM = team()


def who(role):
    return f"{TEAM[role]['name']}, {role}"


def packet(slug):
    base = rel("owners", slug)
    P = {"slug": slug, "base": base}
    for key, f in (("owner", "owner.md"), ("agreement", "documents/agreement.md"), ("county", "documents/county-record.md"),
                   ("w9", "documents/w9.md"), ("ach", "documents/ach.md"), ("insurance", "documents/insurance.md"),
                   ("association", "documents/association.md"), ("lead", "documents/lead-disclosure.md"),
                   ("lease", "tenant/lease.md"), ("transfer", "tenant/deposit-transfer.md")):
        P[key] = table(rel(base, f)) if exists(rel(base, f)) else None
        P[key + "_file"] = rel(base, f)
    for need in R["required_documents"]["every_owner"]:
        if not exists(rel(base, need)):
            P.setdefault("missing", []).append(need)
    return P


def slugs(arg):
    every = sorted(os.path.basename(os.path.dirname(d)) for d in glob.glob(os.path.join(ROOT, "owners", "*", "")))
    if arg == "all":
        return every
    if arg not in every:
        raise SystemExit(f"no owner folder named {arg}")
    return [arg]


# ------------------------------------------------------------- the log -------------------------------------------------------------
def chain_ok():
    if not os.path.exists(LOG):
        return True
    lines = open(LOG, encoding="utf-8").read().rstrip("\n").split("\n")
    links = open(CHAIN, encoding="utf-8").read().split() if os.path.exists(CHAIN) else []
    h = hashlib.sha256(HEADER.encode()).hexdigest()
    for i, line in enumerate(lines[1:]):
        h = hashlib.sha256((h + "\n" + line).encode("utf-8")).hexdigest()
        if i >= len(links) or links[i] != h:
            return False
    return len(links) == len(lines) - 1


def log(owner, action, detail, result):
    if not chain_ok():
        raise Refused("the owners log's hash chain is broken; nothing written")
    new = not os.path.exists(LOG)
    if new:
        open(LOG, "w", encoding="utf-8", newline="").write(HEADER + "\n")
        open(CHAIN, "w", encoding="utf-8", newline="").write("")
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerow([dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), ACTOR, owner, action, detail, result])
    line = buf.getvalue().rstrip("\n")
    links = open(CHAIN, encoding="utf-8").read().split()
    lines = open(LOG, encoding="utf-8").read().rstrip("\n").split("\n")
    h = links[-1] if links else hashlib.sha256(HEADER.encode()).hexdigest()
    assert len(lines) - 1 == len(links)
    h = hashlib.sha256((h + "\n" + line).encode("utf-8")).hexdigest()
    open(LOG, "a", encoding="utf-8", newline="").write(line + "\n")
    open(CHAIN, "a", encoding="utf-8", newline="").write(h + "\n")


def done(owner, action):
    if not os.path.exists(LOG):
        return False
    return any(r["owner"] == owner and r["action"] == action for r in csv.DictReader(io.StringIO(open(LOG, encoding="utf-8").read())))


def write_new(relpath, body):
    f = os.path.join(ROOT, *relpath.split("/"))
    if os.path.exists(f):
        raise Refused(f"{relpath} already exists; nothing overwritten")
    os.makedirs(os.path.dirname(f), exist_ok=True)
    open(f, "w", encoding="utf-8", newline="\n").write(body)


# ------------------------------------------------------------- /owner-intake -------------------------------------------------------------
def ev(file, field, says):
    return {"file": file, "field": field, "says": says}


def intake_one(slug):
    P = packet(slug)
    issues = []

    def add(code, *evidence):
        issues.append({"code": code, "meaning": CODES[code]["meaning"], "condition": CODES[code]["condition"],
                       "gates": CODES[code]["gates"], "fix": CODES[code]["fix"], "evidence": list(evidence)})

    for need in P.get("missing", []):
        add("MISSING_DOCUMENT", ev(rel(P["base"], need), "(not in the packet)", ""))
    agr, cty, own = P["agreement"] or {}, P["county"] or {}, P["owner"] or {}
    named = split_names(agr.get("Owner(s) named", ""))
    on_record = split_names(cty.get("Owner(s) of record", ""))
    rec_keys = {person_key(n) for n in on_record}
    if any(person_key(n) not in rec_keys for n in named):
        add("OWNER_NOT_ON_COUNTY_RECORD", ev(P["agreement_file"], "Owner(s) named", agr.get("Owner(s) named", "")),
            ev(P["county_file"], "Owner(s) of record", cty.get("Owner(s) of record", "")),
            ev(P["county_file"], "Last sale recorded", cty.get("Last sale recorded", "")))
    else:
        sig = signatures(P["agreement_file"])
        signed = {person_key(s["for"]) for s in sig if s["signed"]}
        unsigned = [n for n in on_record if person_key(n) not in signed]
        if unsigned:
            blank = [s for s in sig if not s["signed"] and person_key(s["for"]) in {person_key(n) for n in unsigned}]
            add("AGREEMENT_UNSIGNED_OWNER", ev(P["county_file"], "Owner(s) of record", cty.get("Owner(s) of record", "")),
                *[ev(P["agreement_file"], "Signatures", f"| {s['signer']} | {s['for']} | {s['capacity']} |") for s in blank])
    if P["w9"] is None:
        country = own.get("Mailing country", "")
        if country == "United States":
            add("MISSING_W9", ev(P["w9_file"], "(not in the packet)", ""))
        else:
            add("FOREIGN_TAX_REVIEW", ev(P["base"] + "/owner.md", "Mailing country", country), ev(P["w9_file"], "(not in the packet)", ""))
    ach = P["ach"] or {}
    holders = split_names(ach.get("Account holder name(s)", ""))
    if sorted(person_key(n) for n in holders) != sorted(person_key(n) for n in named):
        add("ACH_NAME_MISMATCH", ev(P["agreement_file"], "Owner(s) named", agr.get("Owner(s) named", "")),
            ev(P["ach_file"], "Account holder name(s)", ach.get("Account holder name(s)", "")))
    ins = P["insurance"] or {}
    if R["insurance"]["policy_type_must_include"].lower() not in ins.get("Policy type", "").lower():
        add("INSURANCE_NOT_LANDLORD", ev(P["insurance_file"], "Policy type", ins.get("Policy type", "")))
    if ins.get("Additional insured", "") != R["insurance"]["additional_insured"]:
        add("MANAGER_NOT_ADDITIONAL_INSURED", ev(P["insurance_file"], "Additional insured", ins.get("Additional insured", "")),
            ev(P["insurance_file"], "Additional interest", ins.get("Additional interest", "")))
    if dollars(ins.get("Liability limit", "$0")) < R["insurance"]["min_liability"]:
        add("INSURANCE_LIMIT_LOW", ev(P["insurance_file"], "Liability limit", ins.get("Liability limit", "")))
    if P["association"] is not None:
        if P["association"].get("Lease approval by the association", "").startswith("Required"):
            add("ASSOCIATION_APPROVAL", ev(P["association_file"], "Lease approval by the association", P["association"]["Lease approval by the association"]))
    elif own.get("Association", "None") != "None":
        add("MISSING_DOCUMENT", ev(P["association_file"], "(not in the packet)", ""))
    built = int(cty.get("Year built", "0") or 0)
    if built and built < R["lead_year"] and P["lead"] is None:
        add("LEAD_DISCLOSURE_MISSING", ev(P["county_file"], "Year built", cty.get("Year built", "")), ev(P["lead_file"], "(not in the packet)", ""))
    occupied = own.get("Occupied", "").startswith("Yes")
    if occupied:
        if P["lease"] is None or P["transfer"] is None:
            add("TENANT_RECORDS_MISSING", ev(P["lease_file"] if P["lease"] is None else P["transfer_file"], "(not in the packet)", ""))
        else:
            want, got = dollars(P["lease"]["Security deposit"]), dollars(P["transfer"]["Security deposit transferred"])
            if got != want:
                add("DEPOSIT_SHORT" if got < want else "DEPOSIT_OVER", ev(P["lease_file"], "Security deposit", P["lease"]["Security deposit"]),
                    ev(P["transfer_file"], "Security deposit transferred", P["transfer"]["Security deposit transferred"]))
    issues.sort(key=lambda i: i["code"])
    found = [i["code"] for i in issues]
    gates = {}
    for g in GATES:
        hit = [c for c in found if g in CODES[c]["gates"]]
        gates[g] = "ready" if not hit else ("hold" if all(c in R["hold_codes"] for c in hit) else "blocked")
    status = "READY" if not found else ("HOLD" if all(c in R["hold_codes"] for c in found) else "BLOCKED")
    provided = sorted(os.path.relpath(f, ROOT).replace("\\", "/") for f in glob.glob(os.path.join(ROOT, "owners", slug, "**", "*.md"), recursive=True)
                      if "/drafts/" not in f.replace("\\", "/") and not f.endswith("setup-sheet.md"))
    return {"owner": slug, "name": agr.get("Owner(s) named", ""), "property": own.get("Property address", ""), "county": own.get("County", ""),
            "property_type": own.get("Property type", ""), "occupied": occupied, "date": R["demo_date"], "status": status, "issues": issues,
            "gates": gates, "documents_read": provided,
            "note": "The county record is one the Owner Onboarding Coordinator saved to the folder; the AI compared names and didn't look anything up."}


def cmd_intake(arg):
    for s in slugs(arg):
        if done(s, "owner_intake"):
            raise Refused(f"intake already ran for {s}")
        j = intake_one(s)
        write_new(rel("owners", s, "intake.json"), json.dumps(j, indent=1) + "\n")
        codes = [i["code"] for i in j["issues"]]
        log(s, "owner_intake", f"owners/{s}/intake.json; {len(codes)} problem(s): {', '.join(codes) or 'none'}; gates "
            + ", ".join(f"{g} {j['gates'][g]}" for g in GATES), j["status"])
        print(f"{s}: {j['status']} {codes}")


def intake(slug):
    return json.loads(read(rel("owners", slug, "intake.json")))


# ------------------------------------------------------------- /takeover -------------------------------------------------------------
def first_names(name_field):
    return " and ".join(n.split()[0] for n in split_names(name_field)) if "LLC" not in name_field else name_field


def street(addr):
    return addr.split(",")[0] if not addr.startswith("Unit") else ", ".join(x.strip() for x in addr.split(",")[:2])


def cmd_takeover(arg):
    for s in slugs(arg):
        P = packet(s)
        if not (P["owner"] or {}).get("Occupied", "").startswith("Yes"):
            continue
        if done(s, "takeover"):
            raise Refused(f"takeover already ran for {s}")
        L, T_ = P["lease"], P["transfer"]
        want, got = dollars(L["Security deposit"]), dollars(T_["Security deposit transferred"])
        res = "MATCH" if want == got else ("DEPOSIT_SHORT" if got < want else "DEPOSIT_OVER")
        on = T_["Transferred on"]
        j = {"owner": s, "tenant": L["Tenant"], "lease_deposit": want, "transferred": got, "difference": want - got, "result": res,
             "received_on": on, "from": T_["From"], "lease": P["lease_file"], "transfer": P["transfer_file"],
             "tenant_letter": None, "letter_due": None, "outgoing_draft": None,
             "rule": "Fla. Stat. 83.49(7): on a change in the rental agent, the deposit and an accurate accounting move to the new agent."}
        prop = P["owner"]["Property address"]
        if res == "MATCH":
            due = str(dt.date.fromisoformat(on) + dt.timedelta(days=R["tenant_letter_days"]))
            path = rel("owners", s, "drafts", f"{R['demo_date']}-tenant-letter.md")
            pm = TEAM["Property Manager"]
            owners_ = " and ".join(split_names(P["agreement"]["Owner(s) named"]))
            write_new(path, f"""# Draft management-change letter to the tenant: {L['Tenant']}

{LABEL} DRAFT ONLY: the assistant never sends letters or email. {pm['name']} (Property Manager) reviews and sends it.*

| Field | Value |
|---|---|
| Status | DRAFT, not sent |
| To | {L['Tenant email']} |
| From | {pm['email']} |
| Reviewer and sender | {who('Property Manager')} |
| Subject | Your home at {street(prop)}: your new property manager, your deposit, and where to send notices |
| Send by | {P['agreement']['Effective date']} |
| Why send by | Management starts that day: the tenant needs who receives notices, how to pay rent, and how to ask for repairs from the first day |
| Due | {due} |
| Why the due date | The deposit notice: the deposit moved to Palmquay on {on}, and Fla. Stat. 83.49(2) asks for notice within {R['tenant_letter_days']} days after a change in where it is held, where the statute applies (not to landlords renting fewer than five units; counsel decides). Palmquay sends it for every takeover either way |
| Ready to send | No: counsel's Fla. Stat. 83.49(2)(d) wording goes in first |
| Drafted | {R['demo_date']} by {ACTOR} from owners/{s}/takeover.json |

## Message

Hello {L['Tenant'].split()[0]},

{owners_} have asked Palmquay Properties to manage your home at {street(prop)}, starting {P['agreement']['Effective date']}. Nothing in your lease changes: the same rent, the same dates, and the same rules.

## Where to send notices, rent, and repair requests

From {P['agreement']['Effective date']}, the person who receives notices for your landlord is {pm['name']}, Property Manager, Palmquay Properties, 1 Demo Plaza, Sarasota, FL 34236 (fictional). Pay rent through Palmquay's tenant portal; we'll email your sign-in link before your next rent is due. For repairs, use the portal or call (555) 010-0300.

## Your security deposit

Your {L['Security deposit']} security deposit moved to Palmquay on {on}. We hold it for you in a separate, non-interest-bearing account, so no interest is paid on it: the Palmquay Tenant Deposit Trust Account at Gulfline Community Bank (sample), 200 Demo Bay Rd, Sarasota, FL 34236 (fictional). It isn't mixed with the owners' money, and it stays yours under the lease.

If anything about your deposit, your rent, or your lease looks different from what you remember, please tell us.

[Not ready to send: insert the disclosure Fla. Stat. 83.49(2)(d) requires, from Palmquay's counsel-approved template, then deliver it in person, by mail, or by email under Fla. Stat. 83.505.]

{pm['name']}, Property Manager, Palmquay Properties (fictional)
""")
            j["tenant_letter"], j["letter_due"] = path, due
            out = f"MATCH; tenant letter drafted (due {due}), not sent"
        else:
            path = rel("owners", s, "drafts", f"{R['demo_date']}-deposit-outgoing-manager.md")
            ta = TEAM["Trust Accountant"]
            diff = abs(want - got)
            write_new(path, f"""# Draft email to the outgoing manager: {T_['From'].split(',')[0]}

{LABEL} DRAFT ONLY: the assistant never sends email. {ta['name']} (Trust Accountant) reviews and sends it.*

| Field | Value |
|---|---|
| Status | DRAFT, not sent |
| To | {T_['From email']} |
| From | {ta['email']} |
| Reviewer and sender | {who('Trust Accountant')} |
| Subject | {L['Tenant']}'s deposit: ${diff:,} difference |
| Issue codes | {res} |
| Deadline | {DEADLINE} |
| Drafted | {R['demo_date']} by {ACTOR} from owners/{s}/takeover.json |

## Message

Hello,

Thank you for sending the deposit for {L['Tenant']} at {street(prop)}. We received {T_['Security deposit transferred']} on {on}, against the {L['Security deposit']} security deposit shown in the lease we were given, so ${diff:,} remains unreconciled.

Please treat this email as our written receipt for the {T_['Security deposit transferred']} only; it isn't a receipt for the full deposit.

Florida law (Fla. Stat. 83.49(7)) asks that, when the rental agent changes, the deposit move to the new agent with an accurate accounting for each tenant. Could you send the complete accounting for this tenant's deposit, including any adjustments the tenant authorized, and the remaining amount if it's owed?

We've recorded the {T_['Security deposit transferred']} received and the ${diff:,} open; we won't mark the deposit reconciled until it's resolved. Please reply by **{DEADLINE}**.

{ta['name']}, Trust Accountant, Palmquay Properties (fictional)
""")
            j["outgoing_draft"] = path
            out = f"{res}; ${diff:,} open; outgoing-manager draft written, not sent; no tenant letter until it reconciles"
        write_new(rel("owners", s, "takeover.json"), json.dumps(j, indent=1) + "\n")
        log(s, "takeover", f"owners/{s}/takeover.json; lease {L['Security deposit']}, transferred {T_['Security deposit transferred']} on {on}; draft {path}", out)
        print(f"{s}: {out}")


# ------------------------------------------------------------- /owner-chase -------------------------------------------------------------
def ask(code, P, it):
    """One numbered item per problem: what we need, and why, in the owner's terms."""
    own, agr, cty = P["owner"], P["agreement"], P["county"]
    if code == "AGREEMENT_UNSIGNED_OWNER":
        who_ = [e["says"].split("|")[1].strip() for e in it["evidence"] if e["field"] == "Signatures"]
        both = "you both" if len(split_names(cty["Owner(s) of record"])) == 2 else "each of you"
        return (f"**{' and '.join(who_)}'s signature on the management agreement ({agr['Agreement']}).** The county record lists "
                f"{both} as owners ({cty['Owner(s) of record']}), and the agreement isn't signed by {' and '.join(w.split()[0] for w in who_)} yet.\n"
                "   **Why we need it:** Palmquay's policy is that every owner on the county record signs, or someone they've authorized in "
                "writing signs for them, so we know we're acting for everyone who owns the home.")
    if code == "OWNER_NOT_ON_COUNTY_RECORD":
        saved = re.search(r"on (\d{4}-\d{2}-\d{2})", read(P["county_file"])).group(1)
        return (f"**A copy of your recorded deed or your closing statement.** The county property record we saved on "
                f"{saved} still lists the owner as "
                f"{cty['Owner(s) of record']}, with the last sale recorded {cty['Last sale recorded']}. You told us you bought the home on "
                f"{own.get('Bought the home', '').split(' ')[0]}, so the county may not have caught up yet.\n"
                "   **Why we need it:** before Palmquay signs on, our broker confirms who owns the home.")
    if code == "FOREIGN_TAX_REVIEW":
        return ("**A US tax form, chosen with your tax adviser.** Your mailing address is in " + own["Mailing country"]
                + " and we don't have a tax form from you yet. Please ask your tax adviser which IRS form fits your situation (for example Form "
                "W-8BEN or W-8ECI, depending on how your rental income is treated) and send it to us.\n"
                "   **Why we need it:** US tax rules can require a property manager to withhold 30% of a foreign owner's gross rent for the IRS "
                f"unless the right documents and treatment are on file. Our Controller, {TEAM['Controller']['name']}, reviews it with your adviser; "
                "we don't choose the form or the treatment for you.")
    if code == "ACH_NAME_MISMATCH":
        return (f"**Bank details for an account in the name {agr['Owner(s) named']}, or the owner's written OK for this one.** The agreement "
                f"names {agr['Owner(s) named']} as the owner; the direct-deposit form is for an account in the name {P['ach']['Account holder name(s)']}.\n"
                "   **Why we need it:** the rent we collect belongs to the owner, so we pay it into the owner's account unless the owner "
                f"authorizes another in writing. Our Trust Accountant, {TEAM['Trust Accountant']['name']}, will call to confirm it at the number you gave us "
                "when we first spoke, not one sent with the bank form.")
    if code == "INSURANCE_NOT_LANDLORD":
        return (f"**Your agent's confirmation that the home is covered as a rental.** The declarations page you sent is a "
                f"{P['insurance']['Policy type'].split(' (')[0].lower()} ({P['insurance']['Policy type'].split('(')[1].rstrip(')')}). Please ask your "
                "agent whether it covers the home once a tenant lives there. If it doesn't, the agreement asks for a landlord (dwelling) policy with "
                f"at least ${R['insurance']['min_liability']:,} liability, naming Palmquay Properties as additional insured.\n"
                "   **Why we need it:** only your agent can confirm what your policy covers, and the management agreement asks for rental coverage.")
    if code == "MANAGER_NOT_ADDITIONAL_INSURED":
        return ("**Palmquay Properties named as additional insured.** Your policy lists Palmquay as additional interest, which sends us notices "
                "about the policy but doesn't extend its liability coverage to us. Please ask your agent to add Palmquay Properties as additional "
                "insured and send the updated declarations page or endorsement.\n"
                "   **Why we need it:** the management agreement asks for it, and your agent confirms the endorsement.")
    if code == "MISSING_W9":
        return ("**A signed W-9.** We don't have one from you yet.\n"
                "   **Why we need it:** each year we report the rent we collect for you to the IRS (Form 1099-MISC), and the W-9 gives us "
                "the name and taxpayer ID to use.")
    if code == "LEAD_DISCLOSURE_MISSING":
        return (f"**The owner's part of the lead-based paint disclosure.** The county record shows the home was built in {cty['Year built']}. "
                f"Federal rules require a lead-paint disclosure for homes built before {R['lead_year']}, given to each tenant before they sign a lease. "
                "Please fill in what you know (it's fine to say you know of none), sign it, and send any lead reports or records you have.\n"
                "   **Why we need it:** your part, any records, the EPA pamphlet, and the lease's lead warning go to each tenant before they sign; "
                "we can't sign a lease for the home without them.")
    if code == "DEPOSIT_SHORT":
        L, T_ = P["lease"], P["transfer"]
        diff = dollars(L["Security deposit"]) - dollars(T_["Security deposit transferred"])
        return (f"**Anything you know about {L['Tenant']}'s deposit.** The lease says {L['Security deposit']}; {T_['From'].split(',')[0].replace(' (fictional)', '')} sent us "
                f"{T_['Security deposit transferred']} on {T_['Transferred on']}. We're writing to them separately about the ${diff:,} difference. If you hold any of "
                "the deposit yourself, or agreed to a deduction with your tenant, please tell us.\n"
                "   **Why we need it:** Florida law has the old manager pass each tenant's deposit to the new one with an accounting, and we hold "
                "it for the tenant until the lease ends.")
    if code == "ASSOCIATION_APPROVAL":
        a = P["association"]
        return (f"**The association manager's contact, for their lease application.** Nothing is missing from your packet. "
                f"{a['Association'].replace(' (fictional)', '')}'s rules (dated {a['Rules dated']}) say the association approves every lease and "
                f"tenant before move-in, with an application {a['Application due'].lower()} and a fee of {a['Application fee']}.\n"
                "   **Why we ask:** so we can get the current application and build that time into the move-in date we give applicants.")
    return f"**{CODES[code]['meaning']}.**"


def cmd_chase(arg):
    co = TEAM["Owner Onboarding Coordinator"]
    for s in slugs(arg):
        j = intake(s)
        if j["status"] == "READY":
            continue
        if done(s, "owner_chase"):
            raise Refused(f"follow-up already drafted for {s}")
        P = packet(s)
        codes = [i["code"] for i in j["issues"]]
        n = len(codes)
        hold = j["status"] == "HOLD"
        items = "\n\n".join(f"{k}. " + ask(i["code"], P, i) for k, i in enumerate(j["issues"], 1))
        subj = ("Your association's lease approval: one step to plan for" if hold
                else f"{n} item{'s' if n > 1 else ''} before we start managing {street(j['property'])}")
        opener = (f"Thank you for choosing Palmquay to manage {street(j['property'])}. Your packet is complete; there's one step to plan for."
                  if hold else f"Thank you for choosing Palmquay to manage {street(j['property'])}. Before we can start, we need "
                  f"{['one thing', 'two things', 'three things', 'four things'][n - 1] if n <= 4 else f'{n} things'} from you.")
        path = rel("owners", s, "drafts", f"{R['demo_date']}-follow-up.md")
        write_new(path, f"""# Draft follow-up email: {j['name']}

{LABEL} DRAFT ONLY: the assistant never sends email. {co['name']} (Owner Onboarding Coordinator) reviews and sends it.*

| Field | Value |
|---|---|
| Status | DRAFT, not sent |
| To | {P['owner']['Contact email']} |
| From | {co['email']} |
| Reviewer and sender | {who('Owner Onboarding Coordinator')} |
| Subject | {subj} |
| Issue codes | {', '.join(codes)} |
| Deadline | {DEADLINE} |
| Drafted | {R['demo_date']} by {ACTOR} from owners/{s}/intake.json |

## Message

Hello {first_names(j['name']) if 'LLC' not in j['name'] else P['owner']['Owner name(s), as the owner wrote them'].split('(')[1].split(',')[0].split()[0]},

{opener}

## What we need

{items}

## Deadline and how to send it

Please send {'it' if n == 1 else 'these'} by **{DEADLINE}** (one week from today). Reply to this email with {'it' if n == 1 else 'them'} attached, or send {'it' if n == 1 else 'them'} to {co['email']}.

Thank you,
{co['name']}, Owner Onboarding Coordinator, Palmquay Properties (fictional)
""")
        log(s, "owner_chase", f"{path}; {', '.join(codes)}; deadline {DEADLINE}; reviewer {who('Owner Onboarding Coordinator')}", f"{j['status']}; follow-up drafted, not sent")
        print(f"{s}: drafted {path}")


# ------------------------------------------------------------- /owner-setup -------------------------------------------------------------
def cmd_setup(arg):
    gate = {g["id"]: g for g in R["gates"]}
    for s in slugs(arg):
        if done(s, "owner_setup"):
            raise Refused(f"setup sheet already drafted for {s}")
        j, P = intake(s), packet(s)
        own, agr, cty, ach = P["owner"], P["agreement"], P["county"], P["ach"]
        b = f"owners/{s}/"
        last4 = re.sub(r"[^\d]", "", ach["Account number"].split("(")[0])[-4:]
        tax = (f"W-9 on file, taxpayer ID {P['w9']['Taxpayer ID']}; a person reviews it" if P["w9"] else
               "Not found in the packet: the Controller and the owner's tax adviser decide the tax status, form, and withholding (FOREIGN_TAX_REVIEW)"
               if own["Mailing country"] != "United States" else "Not found in the packet (MISSING_W9)")
        rows = [("Owner", [("Owner name(s)", agr["Owner(s) named"], "documents/agreement.md"), ("Owner type", own["Owner type"], "owner.md"),
                           ("Email", own["Contact email"], "owner.md"), ("Phone", own["Phone"], "owner.md"),
                           ("Mailing address", own["Mailing address"], "owner.md"), ("Tax form", tax, "documents/w9.md"),
                           ("Owner payments to", f"Gulfline Community Bank (sample), checking ending {last4}, in the name(s) {ach['Account holder name(s)']}", "documents/ach.md"),
                           ("Owner payouts", f"Held until {TEAM['Trust Accountant']['name']} confirms the account by calling the owner at a number Palmquay already had or confirmed separately, and records how", "company/owner-rules.json")]),
                ("Property", [("Address", own["Property address"], "owner.md"), ("County", own["County"], "owner.md"),
                              ("Parcel ID", cty["Parcel ID"], "documents/county-record.md"), ("Type", own["Property type"], "owner.md"),
                              ("Year built", cty["Year built"], "documents/county-record.md"), ("Bedrooms / baths", own["Bedrooms / baths"], "owner.md"),
                              ("Association", own["Association"], "owner.md"), ("Keys", own["Keys handed over"], "owner.md")]),
                ("Agreement", [("Agreement", agr["Agreement"], "documents/agreement.md"), ("Effective date", agr["Effective date"], "documents/agreement.md"),
                               ("Management fee", agr["Management fee"], "documents/agreement.md"), ("Owner reserve", agr["Owner reserve"].split(",")[0], "documents/agreement.md")])]
        if j["occupied"] and P["lease"] and P["transfer"]:
            L, T_ = P["lease"], P["transfer"]
            want, got = dollars(L["Security deposit"]), dollars(T_["Security deposit transferred"])
            opening = (f"$0; reconciled once {TEAM['Trust Accountant']['name']} confirms the bank received it" if want == got
                       else f"${abs(want - got):,} open with {TEAM['Trust Accountant']['name']} ({'DEPOSIT_SHORT' if got < want else 'DEPOSIT_OVER'}); "
                       "both amounts are recorded now, and only 'reconciled' waits")
            rows.append(("Tenant already in place", [("Tenant", L["Tenant"], "tenant/lease.md"), ("Lease term", L["Lease term"], "tenant/lease.md"),
                                                     ("Monthly rent", L["Monthly rent"], "tenant/lease.md"), ("Deposit per the lease", L["Security deposit"], "tenant/lease.md"),
                                                     ("Deposit received", f"{T_['Security deposit transferred']} on {T_['Transferred on']}", "tenant/deposit-transfer.md"),
                                                     ("Difference", opening, "owners/" + s + "/takeover.json"),
                                                     ("A person also reviews", "The lease's amendments, the tenant ledger, the paid-through date, any arrears, notices, and open repairs (not in this sample packet)", "company/owner-rules.json")]))
        body = ""
        for title, rs in rows:
            body += f"\n## {title}\n\n| Field | Value | From |\n|---|---|---|\n" + "".join(
                f"| {a} | {v} | {src if '/' in src and src.startswith(('company', 'owners')) else b + src} |\n" for a, v, src in rs)
        open_items = "".join(f"- {i['code']}: {i['meaning']} ({', '.join(gate[g]['name'] for g in i['gates'])})\n" for i in j["issues"]) or "- None found by the AI\n"
        found = {g: ("Nothing blocking" if j["gates"][g] == "ready" else
                     ("On hold: " if j["gates"][g] == "hold" else "Blocked: ") + ", ".join(i["code"] for i in j["issues"] if g in i["gates"])) for g in GATES}
        signoffs = "".join(f"| {gate[g]['name']} | {who(gate[g]['role'])} | {found[g]} | | |\n" for g in GATES)
        signoffs += f"| {gate['entered']['name']} | {who(gate['entered']['role'])} | After the three above | | |\n"
        write_new(rel("owners", s, "setup-sheet.md"), f"""# Draft setup sheet: {j['name']}, {street(j['property'])}

{LABEL} DRAFT, not entered in any software. A person types it into Palmquay's property management software (for example AppFolio or Buildium, named as examples only) after the sign-offs below; a restricted draft record can be made earlier. The AI doesn't connect to any software.*
{body}
## Open items (from owners/{s}/intake.json)

{open_items}
Not on this sheet: {R['not_on_this_tab']}

## Sign-offs (blank: a person signs)

| Gate | Who signs | What the AI found | Signed by | Date |
|---|---|---|---|---|
{signoffs}""")
        log(s, "owner_setup", f"owners/{s}/setup-sheet.md; gates " + ", ".join(f"{g} {j['gates'][g]}" for g in GATES),
            f"DRAFTED; not entered in any software; 4 sign-offs blank")
        print(f"{s}: setup sheet drafted")


# ------------------------------------------------------------- read-only -------------------------------------------------------------
def cmd_status():
    for s in slugs("all"):
        f = os.path.join(ROOT, "owners", s, "intake.json")
        if not os.path.exists(f):
            print(f"{s}: not run")
            continue
        j = json.load(open(f, encoding="utf-8"))
        print(f"{s}: {j['status']} " + ", ".join(i["code"] for i in j["issues"]) + " | gates " + ", ".join(f"{g} {j['gates'][g]}" for g in GATES))


def cmd_log_review(path):
    t = read(path)
    m = re.search(r"^Overall: (PASS|FAIL)", t, re.M)
    log("all owners", "checker_review", f"{path}; recorded by {ACTOR}", f"overall {m.group(1) if m else 'not stated'}")
    print("logged")


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    try:
        c = argv[1]
        if c == "intake":
            cmd_intake(argv[2])
        elif c == "takeover":
            cmd_takeover(argv[2])
        elif c == "chase":
            cmd_chase(argv[2])
        elif c == "setup":
            cmd_setup(argv[2])
        elif c == "status":
            cmd_status()
        elif c == "log-review":
            cmd_log_review(argv[2])
        elif c == "verify-log":
            ok = chain_ok()
            print("chain verifies" if ok else "chain BROKEN")
            return 0 if ok else 3
        else:
            print(__doc__)
            return 1
    except Refused as e:
        print(f"refused: {e}")
        return 3
    except (OSError, KeyError, StopIteration) as e:
        print(f"unreadable: {e!r}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
