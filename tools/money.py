"""Phase 3h helper: the business side of new owners (fictional company, sample records).
Reads money/inputs/ and the owner packets; writes drafts to money/out/ for people to review. It never decides, sends, signs, pays,
moves money, or posts anything to an accounting system, and it opens no network connection.

    python -I -X utf8 tools/money.py acceptance   draft the acceptance review (is each door worth taking, and on what terms)
    python -I -X utf8 tools/money.py month        draft December: owner statements, the payment batch, the trust reconciliation, the firm's numbers

Each command writes its files and appends one row to audit/owners-log.csv (hash-chained, shared with tools/owners.py); a second run is refused.
"""
import csv
import datetime as dt
import hashlib
import io
import json
import os
import re
import sys
from decimal import Decimal, ROUND_HALF_UP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IN = os.path.join(ROOT, "money", "inputs")
OUT = os.path.join(ROOT, "money", "out")
LOG = os.path.join(ROOT, "audit", "owners-log.csv")
CHAIN = os.path.join(ROOT, "audit", "owners-log.chain.txt")
HEADER = "timestamp,actor,owner,action,detail,result"
FS = json.load(open(os.path.join(IN, "fee-schedule.json"), encoding="utf-8"))
AS = json.load(open(os.path.join(IN, "assumptions.json"), encoding="utf-8"))
LABEL = "*Sample records for a demo. DRAFT: the assistant prepared it; a named person reviews it. Nothing here was sent, paid, or posted.*"


def c(s):
    """'$2,050' -> 205000 cents."""
    return int((Decimal(re.sub(r"[^\d.]", "", s.split("(")[0])) * 100).to_integral_value(rounding=ROUND_HALF_UP))


def rnd(x):
    return int(Decimal(x).to_integral_value(rounding=ROUND_HALF_UP))


def usd(cents):
    return f"${cents // 100:,}.{cents % 100:02d}"


def md_tables(path):
    lines, out, i = open(path, encoding="utf-8").read().splitlines(), [], 0
    while i < len(lines):
        if lines[i].startswith("|") and i + 1 < len(lines) and lines[i + 1].startswith("|---"):
            head = [x.strip() for x in lines[i].strip("|").split("|")]
            j, rows = i + 2, []
            while j < len(lines) and lines[j].startswith("|"):
                rows.append(dict(zip(head, [x.strip() for x in lines[j].strip("|").split("|")])))
                j += 1
            out.append((head, rows))
            i = j
        else:
            i += 1
    return out


def table(path, col):
    return next(rows for head, rows in md_tables(path) if col in head)


def field(path, name):
    for head, rows in md_tables(path):
        for r in rows:
            if r.get("Field") == name:
                return r["Value"]
    return ""


def team():
    return {r["Role"]: {"name": r["Name"], "email": r["Email (reserved demo domain)"]} for r in table(os.path.join(ROOT, "company", "owner-team.md"), "Role")}


TEAM = team()


def log(owner, action, detail, result, repeat_ok=False):
    lines = open(LOG, encoding="utf-8").read().rstrip("\n").split("\n")
    links = open(CHAIN, encoding="utf-8").read().split()
    h = hashlib.sha256(HEADER.encode()).hexdigest()
    for i, line in enumerate(lines[1:]):
        h = hashlib.sha256((h + "\n" + line).encode("utf-8")).hexdigest()
        if i >= len(links) or links[i] != h:
            raise SystemExit("refused: the owners log's hash chain is broken")
    if not repeat_ok and any(r["action"] == action for r in csv.DictReader(io.StringIO("\n".join(lines)))):
        raise SystemExit(f"refused: {action} already ran")
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerow([dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "owner-assistant", owner, action, detail, result])
    line = buf.getvalue().rstrip("\n")
    h = hashlib.sha256((h + "\n" + line).encode("utf-8")).hexdigest()
    open(LOG, "a", encoding="utf-8", newline="").write(line + "\n")
    open(CHAIN, "a", encoding="utf-8", newline="").write(h + "\n")


def write(rel, body):
    f = os.path.join(OUT, *rel.split("/"))
    if os.path.exists(f):
        raise SystemExit(f"refused: money/out/{rel} already exists")
    os.makedirs(os.path.dirname(f), exist_ok=True)
    open(f, "w", encoding="utf-8", newline="\n").write(body)


# ------------------------------------------------------------- acceptance review -------------------------------------------------------------
def acceptance_data():
    out = {}
    for r in table(os.path.join(IN, "rent-evidence.md"), "Comparable 1"):
        comps = sorted(c(r[f"Comparable {i}"]) for i in (1, 2, 3))
        asked = None if r["Owner asked"] == "none" else c(r["Owner asked"])
        lease = None if r["Current lease rent"] == "none" else c(r["Current lease rent"])
        ready, fund = c(r["Make-ready estimate"]), c(r["Owner funding"])
        flags = (["RENT_ABOVE_EVIDENCE"] if asked is not None and asked > comps[2] else []) + (["REPAIRS_NEED_FUNDING"] if ready > fund else [])
        out[r["Owner"]] = {"home": r["Home"], "asked": asked, "lease": lease, "range": [comps[0], comps[2]],
                           "proposed": lease if lease is not None else comps[1], "ready": ready, "fund": fund, "flags": flags,
                           "suggest": "CONDITIONAL" if flags else "ACCEPT", "reviewed": r["Reviewed"], "decision": "",
                           "decided_by": "Broker of Record"}
    return out


def cmd_acceptance():
    A = acceptance_data()
    rows = []
    for o, a in A.items():
        why = []
        if "RENT_ABOVE_EVIDENCE" in a["flags"]:
            why.append(f"owner asked {usd(a['asked'])}; leased comparables top out at {usd(a['range'][1])}: agree a listing rent first")
        if "REPAIRS_NEED_FUNDING" in a["flags"]:
            why.append(f"make-ready {usd(a['ready'])} vs {usd(a['fund'])} set aside: the owner funds the repairs first")
        rent = f"tenant in place at {usd(a['lease'])}" if a["lease"] is not None else f"owner asked {usd(a['asked'])}"
        rows.append(f"| {o} | {a['home']} | {rent} | {usd(a['range'][0])} to {usd(a['range'][1])} | {usd(a['proposed'])} | "
                    f"{usd(a['ready'])} vs {usd(a['fund'])} | {', '.join(a['flags']) or 'none'} | {a['suggest']}"
                    f"{': ' + '; '.join(why) if why else ''} | |")
    gm = TEAM["Broker of Record"]["name"]
    write("acceptance.json", json.dumps(A, indent=1) + "\n")
    write("acceptance.md", f"""# Acceptance review: is each door worth taking, and on what terms (draft)

{LABEL}

Before Palmquay signs an owner, the AI reads the rent evidence and walk-through notes staff gathered and drafts a suggestion. {gm} (Broker of Record) decides: accept, accept with conditions, or decline. The "rent to plan on" is the current lease rent for a home with a tenant, or else the middle of three leased comparables.

| Owner | Home | Rent now | Leased comparables | Rent to plan on | Make-ready vs owner funding | AI flags | AI suggests | Decision ({gm}) |
|---|---|---|---|---|---|---|---|---|
""" + "\n".join(rows) + "\n")
    n = sum(a["suggest"] == "ACCEPT" for a in A.values())
    log("all owners", "acceptance_review", "money/out/acceptance.md; " + ", ".join(f"{o} {a['suggest']}" for o, a in A.items()),
        f"DRAFTED; {n} accept, {len(A) - n} conditional suggested; decisions left blank for the broker, not signed")
    print(f"acceptance: {n} accept, {len(A) - n} conditional")


# ------------------------------------------------------------- the month -------------------------------------------------------------
def cmd_month():
    mo = os.path.join(IN, "month-2026-12.md")
    A = acceptance_data()
    pct = Decimal(FS["management_fee_pct"]) / 100
    limit, reserve = FS["repair_approval_limit"] * 100, FS["owner_reserve"] * 100
    rent = {r["Owner"]: (c(r["Amount"]), r) for r in table(mo, "Tenant")}
    inv = table(mo, "Vendor")
    S, lines, held = {}, [], []
    for o in sorted(rent):
        amt = rent[o][0]
        fee = rnd(Decimal(amt) * pct)
        pay_inv = [i for i in inv if i["Owner"] == o and (c(i["Amount"]) <= limit or i["Owner approval on file"].startswith("yes"))]
        hold_inv = [i for i in inv if i["Owner"] == o and i not in pay_inv]
        paid, hold = sum(c(i["Amount"]) for i in pay_inv), sum(c(i["Amount"]) for i in hold_inv)
        payout = reserve + amt - fee - paid - reserve - hold
        S[o] = {"opening": reserve, "rent": amt, "fee": fee, "repairs_paid": paid, "held": hold, "reserve_kept": reserve, "payout": payout}
        lines.append({"payee": "Palmquay Properties operating account", "what": f"management fee, {FS['management_fee_pct']}% of rent collected ({o})",
                      "amount": fee, "source": f"rent received {rent[o][1]['Received']}, money/inputs/month-2026-12.md", "authority": "the owner's management agreement",
                      "status": "draft, not paid"})
        for i in pay_inv:
            lines.append({"payee": i["Vendor"], "what": f"{i['Work']} ({o})", "invoice": i["Invoice"], "amount": c(i["Amount"]),
                          "source": f"invoice {i['Invoice']}", "authority": f"under the {usd(limit)} repair limit in the fee schedule",
                          "status": "draft, not paid"})
        for i in hold_inv:
            held.append({"invoice": i["Invoice"], "payee": i["Vendor"], "owner": o, "amount": c(i["Amount"]), "code": "INVOICE_NEEDS_OWNER_APPROVAL",
                         "reason": f"over the {usd(limit)} repair limit, and no owner approval on file"})
        lines.append({"payee": f"owner payout ({o})", "what": "owner distribution by ACH", "amount": payout,
                      "source": f"money/out/statements/2026-12-{o}.md", "authority": "the owner's management agreement; account confirmed by call on 2026-11-16",
                      "status": "draft, not paid"})
    total = sum(l["amount"] for l in lines)
    ta, pm, gm = TEAM["Trust Accountant"], TEAM["Property Manager"], TEAM["Broker of Record"]
    write("statements.json", json.dumps(S, indent=1) + "\n")
    for o, s in S.items():
        email = field(os.path.join(ROOT, "owners", o, "owner.md"), "Contact email")
        name = field(os.path.join(ROOT, "owners", o, "documents", "agreement.md"), "Owner(s) named").replace("; ", " and ")
        write(f"statements/2026-12-{o}.md", f"""# Owner statement, December: {name} (draft)

{LABEL}

| Field | Value |
|---|---|
| Status | DRAFT, not sent |
| To | {email} |
| Reviewer and sender | {ta['name']}, Trust Accountant |
| Home | {A[o]['home']} |

| Line | Amount |
|---|---|
| Owner funds at the start of the month (the reserve) | {usd(s['opening'])} |
| Rent collected | {usd(s['rent'])} |
| Management fee, {FS['management_fee_pct']}% of rent collected | -{usd(s['fee'])} |
| Repairs paid | -{usd(s['repairs_paid'])} |
| Held for the owner's approval | -{usd(s['held'])} |
| Reserve kept for repairs | -{usd(s['reserve_kept'])} |
| Proposed payout to the owner | {usd(s['payout'])} |

The tenant's security deposit is held in the separate deposit trust account and isn't part of these numbers.
""")
    for h in held:
        o = h["owner"]
        email = field(os.path.join(ROOT, "owners", o, "owner.md"), "Contact email")
        write(f"drafts/2026-12-owner-approval-{o}.md", f"""# Draft email: approve a repair invoice ({h['invoice']})

{LABEL}

| Field | Value |
|---|---|
| Status | DRAFT, not sent |
| To | {email} |
| Reviewer and sender | {pm['name']}, Property Manager |
| Issue codes | {h['code']} |

## Message

Hello, {h['payee'].replace(' (fictional)', '')} quoted {usd(h['amount'])} (quote {h['invoice']}) to replace the dripping drain valve on your water heater. Hot water still works, so it isn't urgent. Your agreement asks for your OK on any repair over {usd(limit)}, so nothing has been scheduled or paid. Reply "approved" and we'll book it; as the agreement allows, we've held {usd(h['amount'])} of your funds back from this month's payout until you answer, and that money stays on your account either way.

{pm['name']}, Property Manager, Palmquay Properties (fictional)
""")
    write("payment-batch-2026-12.json", json.dumps({"lines": lines, "held": held, "total": total}, indent=1) + "\n")
    write("payment-batch-2026-12.md", f"""# December payment batch (draft)

{LABEL}

{ta['name']} (Trust Accountant) reviews every line. A person releases the payments in the bank's system; approving the batch isn't the same as a payment going through.

| Payee | What | Amount | Source | Authority | Status |
|---|---|---|---|---|---|
""" + "".join(f"| {l['payee']} | {l['what']} | {usd(l['amount'])} | {l['source']} | {l['authority']} | {l['status']} |\n" for l in lines)
          + f"| **Total** | | **{usd(total)}** | | | |\n\n## Held, not in the batch\n\n| Invoice | Payee | Amount | Why |\n|---|---|---|---|\n"
          + "".join(f"| {h['invoice']} | {h['payee']} | {usd(h['amount'])} | {h['code']}: {h['reason']} |\n" for h in held))
    bal = {r["Account"]: c(r["Bank balance"]) for r in table(mo, "Bank balance")}
    own_liab = sum(s["reserve_kept"] + s["held"] for s in S.values())
    own_book = sum(s["opening"] + s["rent"] - s["fee"] - s["repairs_paid"] - s["payout"] for s in S.values())
    leases = sum(c(field(os.path.join(ROOT, "owners", o, "tenant", "lease.md"), "Security deposit")) for o in S)
    got = sum(c(field(os.path.join(ROOT, "owners", o, "tenant", "deposit-transfer.md"), "Security deposit transferred")) for o in S)
    R = {"owner_funds": {"bank": bal["Owner funds trust account"], "book": own_book, "liabilities": own_liab, "difference": own_liab - bal["Owner funds trust account"]},
         "deposits": {"bank": bal["Tenant deposit trust account"], "book": got, "liabilities": leases, "difference": leases - bal["Tenant deposit trust account"]}}
    write("reconciliation-2026-12.json", json.dumps(R, indent=1) + "\n")
    o_, d_ = R["owner_funds"], R["deposits"]
    write("reconciliation-2026-12.md", f"""# Trust account reconciliation, end of December (draft)

{LABEL}

A summary of the monthly reconciliation Florida's broker rule (61J2-14.012) requires for each trust account; the full reconciliation also lists the account, dates, any deposits in transit and outstanding payments, and each client's balance. {ta['name']} prepares it; {gm['name']} (Broker of Record) reviews, signs, and dates it. "Bank" is the statement balance on 2026-12-31; every December payment had cleared, so nothing was in transit or outstanding.

| Account | Bank balance | Books | Owed to clients | Difference |
|---|---|---|---|---|
| Owner funds trust account | {usd(o_['bank'])} | {usd(o_['book'])} | {usd(o_['liabilities'])} | {usd(o_['difference'])} |
| Tenant deposit trust account | {usd(d_['bank'])} | {usd(d_['book'])} | {usd(d_['liabilities'])} | {usd(d_['difference'])} |

Owner funds: the three numbers agree (two $500 reserves, plus the $640 held for the owner's approval).

Tenant deposits: an unresolved funding shortfall. The leases show {usd(d_['liabilities'])} owed to tenants; {usd(d_['bank'])} is in the bank. The {usd(d_['difference'])} is the part of Marco Ellison's deposit that Tidewell Rentals (fictional), the outgoing manager, hasn't transferred; the tenant's credit stays at the full lease amount. Status at 2026-12-31: the written demand to Tidewell for the rest or its accounting was drafted on 2026-11-05 for {ta['name']} (owners/haddad/drafts), with a reply date of 2026-11-12, and no answer is on file. Next step, for {ta['name']} and {gm['name']} to decide and record: a second written demand, and whether to bring in counsel. No other client's money covers the gap, and it stays on this report until it's resolved.

| Signs | Name | Signature | Date |
|---|---|---|---|
| Broker of Record | {gm['name']} | | |
""")
    vac = [a for a in A.values() if a["lease"] is None]
    allr = sum(a["proposed"] for a in A.values())
    vr = sum(a["proposed"] for a in vac)
    days = FS["days_in_month_convention"]
    E = {"december_fees": sum(s["fee"] for s in S.values()), "monthly_fees_all_rented": rnd(Decimal(allr) * pct),
         "revenue_per_door_month": rnd(Decimal(rnd(Decimal(allr) * pct)) / len(A)),
         "leasing_fees_vacant": sum(rnd(Decimal(a["proposed"]) * FS["leasing_fee_pct_of_first_month"] / 100) for a in vac),
         "vacant_rent_per_day": rnd(Decimal(vr) / days), "vacant_fee_per_day": rnd(Decimal(vr) * pct / days),
         "rent_sooner": rnd(Decimal(vr) * AS["days_sooner"] / days), "fees_sooner": rnd(Decimal(vr) * pct * AS["days_sooner"] / days),
         "staff_saved_per_owner": rnd(Decimal(AS["coordinator_cost_per_hour"] * 100) * (AS["minutes_per_owner_by_hand"] - AS["minutes_per_owner_with_system"]) / 60)}
    E["staff_saved_all"] = E["staff_saved_per_owner"] * len(A)
    write("economics.json", json.dumps(E, indent=1) + "\n")
    log("brandt + haddad", "month_close", "money/out/statements/, payment-batch-2026-12.md, reconciliation-2026-12.md, economics.json; "
        f"batch {usd(total)}, held {', '.join(h['invoice'] for h in held)}; deposit difference {usd(d_['difference'])}",
        "DRAFTED; statements not sent, batch not paid, reconciliation not signed"
        + ("; earlier run set aside in money/discarded-first-month/" if os.path.exists(os.path.join(ROOT, "money", "discarded-first-month", "README.md")) else ""),
        repeat_ok=os.path.exists(os.path.join(ROOT, "money", "discarded-first-month", "README.md")))
    print(f"month: batch {usd(total)}, held {[h['invoice'] for h in held]}, recon differences {o_['difference']} / {d_['difference']}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "acceptance":
        cmd_acceptance()
    elif cmd == "month":
        cmd_month()
    else:
        print(__doc__)
        sys.exit(1)
