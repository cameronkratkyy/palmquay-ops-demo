"""Phase 3d helpers: two real-world exceptions (fictional company, sample records).
Where a script is more reliable than reading by eye: who signed before the change, the approval order, day counts, the credit math.
Nothing here voids, sends, signs, orders, approves, or pays, and nothing opens a network connection.

    python -I -X utf8 tools/exceptions.py revise <vendor>      /revise: a signer asked for a change mid-approval; build the next version
    python -I -X utf8 tools/exceptions.py credit <project>     /credit: items a week or more past their promised date; draft a shipping-credit request
    python -I -X utf8 tools/exceptions.py status               one line per exception step (read-only)
    python -I -X utf8 tools/exceptions.py log-review <path>    log 1 row for a saved checker review
    python -I -X utf8 tools/exceptions.py verify-log           recompute the exceptions log's hash chain (read-only)

Each action writes its outputs and appends exactly one row to audit/exceptions-log.csv; a second run is refused.
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
RULES = json.load(open(os.path.join(ROOT, "company", "rules.json"), encoding="utf-8"))
X = RULES["exceptions"]
LOG = os.path.join(ROOT, "audit", "exceptions-log.csv")
CHAIN = os.path.join(ROOT, "audit", "exceptions-log.chain.txt")
HEADER = "timestamp,actor,vendor,action,detail,result"


class Refused(Exception):
    pass


class Unreadable(Exception):
    pass


# ------------------------------------------------------------- reading -------------------------------------------------------------
def path(*a):
    return os.path.join(ROOT, *a)


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def text(p):
    if not os.path.exists(p):
        raise Unreadable(f"{rel(p)} not found")
    return open(p, encoding="utf-8").read()


def kv(t):
    out = {}
    for line in t.splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", line) or re.match(r"^([A-Z][A-Za-z ,()/'-]*?):[ \t]*(.*)$", line)
        if m and m.group(1) not in out:
            out[m.group(1)] = m.group(2).strip()
    return out


def rows(t, first):
    lines = t.splitlines()
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells and cells[0] == first:
            got = []
            for r in lines[i + 2:]:
                if not r.startswith("|"):
                    break
                got.append(dict(zip(cells, [c.strip() for c in r.strip().strip("|").split("|")])))
            return got
    return []


def dollars(s):
    return int(re.sub(r"[^\d]", "", s))


def usd(n):
    return f"${n:,}"


def usd_cents(c):
    return f"${c // 100:,}.{c % 100:02d}"


def day(s):
    return dt.date.fromisoformat(s.strip()[:10])


def people():
    return {re.sub(r"\s*\(.*?\)", "", r["Role"]).strip(): r for r in rows(text(path("company", "people.md")), "Role")}


def tier_for(amount):
    return next(t for t in RULES["approval_tiers"] if t["max_amount"] is None or amount <= t["max_amount"])["approvers"]


# ------------------------------------------------------------- the log -------------------------------------------------------------
def chain_ok():
    if not os.path.exists(LOG):
        return True, 0, 0
    lines = open(LOG, encoding="utf-8", newline="").read().rstrip("\n").split("\n")
    if lines[0].rstrip("\r") != HEADER:
        return False, 0, 0
    links = open(CHAIN, encoding="utf-8").read().split() if os.path.exists(CHAIN) else []
    h, ok = hashlib.sha256(HEADER.encode()).hexdigest(), 0
    for i, line in enumerate(lines[1:]):
        h = hashlib.sha256((h + "\n" + line.rstrip("\r")).encode("utf-8")).hexdigest()
        ok += i < len(links) and links[i] == h
    n = len(lines) - 1
    return ok == n == len(links), n, ok


def logged(action):
    if not os.path.exists(LOG):
        return False
    return any(r.get("action") == action for r in csv.DictReader(io.StringIO(open(LOG, encoding="utf-8").read())))


def once(action):
    good, _, _ = chain_ok()
    if not good:
        raise Refused("the exceptions log's hash chain doesn't verify")
    if logged(action):
        raise Refused(f"{action} already ran (the log is append-only)")


def log(actor, subject, action, detail, result):
    good, n, _ = chain_ok()
    if not good:
        raise Refused("the exceptions log's hash chain doesn't verify")
    if not os.path.exists(LOG):
        open(LOG, "w", encoding="utf-8", newline="").write(HEADER + "\n")
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerow([dt.datetime.now().isoformat(timespec="seconds"), actor, subject, action, detail, result])
    line = buf.getvalue().rstrip("\n")
    links = open(CHAIN, encoding="utf-8").read().split() if os.path.exists(CHAIN) else []
    prev = links[-1] if links else hashlib.sha256(HEADER.encode()).hexdigest()
    with open(LOG, "a", encoding="utf-8", newline="") as f:
        f.write(line + "\n")
    with open(CHAIN, "a", encoding="utf-8", newline="") as f:
        f.write(hashlib.sha256((prev + "\n" + line).encode("utf-8")).hexdigest() + "\n")
    print(f"log row {n + 1}: {line}")


def write(p, content):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.exists(p):
        raise Refused(f"{rel(p)} already exists (outputs are never overwritten)")
    if p.endswith(".json"):
        json.dump(content, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    else:
        open(p, "w", encoding="utf-8").write(content.strip() + "\n")


# ------------------------------------------------------------- /revise -------------------------------------------------------------
def revise(slug):
    once("packet_revision")
    vdir = path("vendors", slug)
    exports = sorted(glob.glob(os.path.join(vdir, "esign-status-*.md")))
    if not exports:
        raise Unreadable(f"vendors/{slug}/esign-status-*.md not found")
    ex_rel = rel(exports[-1])
    et = text(exports[-1])
    ef = kv(et)
    signers = rows(et, "#")
    asks = [r for r in signers if r["Status"] == "change requested"]
    if len(asks) != 1:
        raise Unreadable(f"{ex_rel}: want exactly 1 'change requested' row, found {len(asks)}")
    ask = asks[0]
    before = [r for r in signers if r["Status"] == "signed" and int(r["#"]) < int(ask["#"])]
    ctype = ef.get("Change type", "")
    if not ctype:
        raise Unreadable(f"{ex_rel}: no 'Change type' line")
    material = ctype in X["revision"]["material_changes"]
    v1_rel = ef["Packet"]
    v1 = kv(text(path(*v1_rel.split("/"))))
    amount = dollars(kv(text(path("vendors", slug, "documents", "request.md")))["Contract amount"])
    route = tier_for(amount)
    ppl = people()
    if not material:
        raise Refused(f"'{ctype}' isn't a material change under company/rules.json; a person corrects it in the e-signature tool")
    frm, to = int(ef["Version"]), int(ef["Version"]) + 1
    out = {"vendor": slug, "from_version": frm, "to_version": to, "change_type": ctype, "change": ask["Note"],
           "requested_by": ask["Role"], "requested_by_name": ask["Name"], "requested_on": ask["Date"], "material": material,
           "status": X["revision"]["status"], "signed_before": [r["Role"] for r in before],
           "signed_before_on": {r["Role"]: r["Date"] for r in before}, "route": route, "next": route[0],
           "sender": X["revision"]["sender"], "blank_signoffs": len(route),
           "sources": [v1_rel, ex_rel, "company/rules.json"], "packet": f"vendors/{slug}/packet-v{to}.md",
           "run": {"by": "onboarding-assistant", "at": dt.datetime.now().isoformat(timespec="seconds"), "tool": "tools/exceptions.py revise"}}
    sender = ppl[X["revision"]["sender"]]["Name"]
    names = [ppl[r]["Name"] for r in route]
    v1_rows = "\n".join(f"| {r['#']} | {r['Role']} | {r['Name']} | signed {r['Date']} | needs to sign again on version {to} |" for r in before)
    v1_rows += "\n" + "\n".join(f"| {r['#']} | {r['Role']} | {r['Name']} | {r['Status']} | signs version {to} in order |"
                                for r in signers if r not in before)
    signoff = "\n".join(f"| {i} | {r} | {ppl[r]['Name']} | {ppl[r]['Email (reserved demo domain)']} |  |  |  |" for i, r in enumerate(route, 1))
    md = f"""# Approval packet, version {to}: {v1.get('Vendor', slug)}

*Sample data for a demo (fictional company). Built by the onboarding assistant from version {frm} (`{v1_rel}`), the e-signature export (`{ex_rel}`), and company/rules.json. Nothing is approved until the people below sign. The assistant never voids, sends, signs, approves, or pays.*

| Field | Value |
|---|---|
| Vendor | {v1.get('Vendor', '')} |
| Version | {to} (replaces version {frm}) |
| Building | {v1.get('Building', '')} |
| Scope | {v1.get('Scope', '')} |
| Contract amount | {usd(amount)} |
| Approval tier | {v1.get('Approval tier', '')} |
| Status | {X['revision']['status']}: signing starts again with the first approver |
| Built | {out['run']['at']} by onboarding-assistant |

## What changed
| What | Version {frm} | Version {to} | Asked for by |
|---|---|---|---|
| {ctype} | as in version {frm} | {ask['Note']} | {ask['Name']}, {ask['Role']}, {ask['Date']} |

A change to the {ctype} is a material change under company/rules.json, so version {frm}'s signatures don't carry over: version {frm} becomes void once a person voids it in the e-signature tool, and signing restarts with the first approver.

## Version {frm}: where signing stood on {ef.get('Exported', '')}
| # | Role | Name | Version {frm} | Now |
|---|---|---|---|---|
{v1_rows}

## Sign-offs (version {to}, in this order; each person signs after the one above)

| # | Role | Name | Email | Decision | Date | Signature |
|---|---|---|---|---|---|---|
{signoff}

Decision, Date and Signature are left blank on purpose: a person fills them in.

## What a person does next
1. {sender}, {X['revision']['sender']}, voids version {frm} in the e-signature tool and sends version {to}.
2. Signing starts again in order: {', '.join(names[:-1])}, then {names[-1]}.
"""
    write(path("vendors", slug, f"packet-v{to}.md"), md)
    write(path("vendors", slug, "revision.json"), out)
    log("onboarding-assistant", slug, "packet_revision",
        f"vendors/{slug}/revision.json; vendors/{slug}/packet-v{to}.md; version {frm} -> {to}: {ctype} change asked by {ask['Role']} on {ask['Date']}; "
        f"{len(before)} earlier signatures don't carry over; route restarts with {route[0]}",
        f"{X['revision']['status']}; version {to} built, {len(route)} sign-offs blank, not sent")
    print(f"{slug}: version {frm} -> {to}, {ctype} ({ask['Role']}); {len(before)} earlier signers sign again; next {route[0]}")


# ------------------------------------------------------------- /credit -------------------------------------------------------------
def credit(project):
    once("freight_credit")
    pd = path("projects", project)
    po_rel = f"projects/{project}/approved/po-PQ-1042.md"
    po_t = text(path(*po_rel.split("/")))
    order = re.search(r"^# Purchase order (\S+)", po_t, re.M).group(1)
    lines = {r["SKU"]: r for r in rows(po_t, "SKU")}
    freight = {m.group(1): dollars(m.group(2)) for m in re.finditer(r"^Freight ([^:]+): (\$[\d,]+)", po_t, re.M)}
    trk = sorted(glob.glob(os.path.join(pd, "deliveries", "tracking-*.md")))
    if not trk:
        raise Unreadable(f"projects/{project}/deliveries/tracking-*.md not found")
    tt = text(trk[-1])
    as_of = kv(tt)["As of"]
    install = kv(text(os.path.join(pd, "request.md")))["Install by"]
    mail = {r["Supplier"]: r["Orders email"] for r in rows(text(path("company", "approved-suppliers.md")), "Supplier")}
    fc = X["freight_credit"]
    hold = RULES["projects"]["on_hold_status"]
    items = {}
    for r in rows(tt, "SKU"):
        if not r.get("ETA") or r["SKU"] not in lines or r["Status"] == hold:
            continue
        late = (day(r["ETA"]) - day(lines[r["SKU"]]["Promised delivery"])).days
        if late >= fc["days_past_promised"]:
            items[r["SKU"]] = {"supplier": r["Supplier"], "item": lines[r["SKU"]]["Item"], "promised": lines[r["SKU"]]["Promised delivery"],
                               "eta": r["ETA"], "days_past": late}
    ppl = people()
    rv = ppl[fc["reviewer_and_sender"]]["Name"]
    sups = {}
    for sku, it in items.items():
        s = sups.setdefault(it["supplier"], {"freight": freight[it["supplier"]], "skus": []})
        s["skus"].append(sku)
        s["credit_cents"] = freight[it["supplier"]] * 100 * fc["share_of_freight_percent"] // 100
        s["credit"] = usd_cents(s["credit_cents"])
        s["draft"] = f"projects/{project}/exceptions/credit-request-{it['supplier'].split()[0].lower()}-{as_of}.md"
    out = {"project": project, "order": order, "as_of": as_of, "tracking": rel(trk[-1]),
           "rule": {"days_past_promised": fc["days_past_promised"], "share_of_freight_percent": fc["share_of_freight_percent"]},
           "items": items, "suppliers": sups, "reviewer_and_sender": fc["reviewer_and_sender"], "status": fc["status"],
           "run": {"by": "procurement-assistant", "at": dt.datetime.now().isoformat(timespec="seconds"), "tool": "tools/exceptions.py credit"}}
    for name, s in sups.items():
        rows_ = "\n".join(f"| Late item | {sku}, {items[sku]['item']} |\n| Promised delivery | {items[sku]['promised']} |\n"
                          f"| Current ETA | {items[sku]['eta']} (tracking as of {as_of}) |\n| Days past the promised date | {items[sku]['days_past']} |"
                          for sku in s["skus"])
        plain = lambda it: " ".join(reversed([x.strip() for x in it.lower().split(",", 1)])) if "," in it else it.lower()  # "Bed frame, queen" -> "queen bed frame"
        what = " and ".join(f"the {plain(items[sku]['item'])} ({sku}) for {items[sku]['promised']}" for sku in s["skus"])
        now = " and ".join(f"{items[sku]['eta']}, {items[sku]['days_past']} days after that date" for sku in s["skus"])
        md = f"""# Draft to {name} (fictional): shipping credit request, not sent

Draft only. {rv}, {fc['reviewer_and_sender']}, reviews it, may change the amount, and sends it; the assistant does not send email. Sample data for a demo.

| Field | Value |
|---|---|
| To | {mail.get(name, '')} |
| Order | {order} |
{rows_}
| Freight on this order | {usd(s['freight'])} |
| Credit requested | {s['credit']} ({fc['share_of_freight_percent']}% of the freight) |

Subject: Order {order}: delivery delay and a shipping credit

Hello {name} team,

Our order {order} promised {what}. Tracking now shows {now}, and after our install date of {install}.

Because of the delay, we'd like to ask for a credit of {s['credit']}, which is {fc['share_of_freight_percent']}% of the {usd(s['freight'])} freight on this order. Could you confirm the new delivery date, and let us know whether you can apply the credit to your invoice for this order?

Thank you,
{rv}, {fc['reviewer_and_sender']}
Palmquay Properties (fictional)
"""
        write(path(*s["draft"].split("/")), md)
    write(os.path.join(pd, "exceptions", "freight-credit.json"), out)
    summary = "; ".join(f"{sku} ETA {it['eta']}, {it['days_past']} days past promised {it['promised']}" for sku, it in items.items())
    asks = "; ".join(f"{n} freight {usd(s['freight'])}, ask {fc['share_of_freight_percent']}% = {s['credit']}; draft {s['draft']}" for n, s in sups.items())
    log("procurement-assistant", project, "freight_credit", f"projects/{project}/exceptions/freight-credit.json; {summary or 'no item 7+ days late'}; {asks}",
        f"{fc['status']}; {len(sups)} credit request{'s' if len(sups) != 1 else ''} drafted, not sent")
    print(f"{project}: {len(items)} item(s) {fc['days_past_promised']}+ days past promised; {len(sups)} draft(s)")


# ------------------------------------------------------------- misc -------------------------------------------------------------
def status():
    print("| Step | Done | Output |\n|---|---|---|")
    for a, o in (("packet_revision", "vendors/*/revision.json"), ("freight_credit", "projects/unit-4b/exceptions/freight-credit.json")):
        print(f"| {a} | {'yes' if logged(a) else 'no'} | {o} |")


def log_review(p):
    t = text(path(*p.replace("\\", "/").split("/")))
    m = re.search(r"^Overall: (\w+)", t, re.M)
    log("compliance-checker", "skyquay-lift-fire + unit-4b", "checker_review", f"{p}; recorded by onboarding-assistant",
        f"overall {m.group(1) if m else 'not stated'}")


def verify_log():
    good, n, ok = chain_ok()
    print(f"exceptions log: {n} rows, {ok} of {n} chain links verify -> {'OK' if good else 'BROKEN'}")
    if not good:
        raise Refused("hash chain broken")


if __name__ == "__main__":
    a = sys.argv[1:]
    try:
        if len(a) == 2 and a[0] == "revise":
            revise(a[1])
        elif len(a) == 2 and a[0] == "credit":
            credit(a[1])
        elif a == ["status"]:
            status()
        elif len(a) == 2 and a[0] == "log-review":
            log_review(a[1])
        elif a == ["verify-log"]:
            verify_log()
        else:
            print(__doc__)
            sys.exit(1)
    except Unreadable as e:
        print(f"UNREADABLE: {e}")
        sys.exit(2)
    except Refused as e:
        print(f"REFUSED: {e}")
        sys.exit(3)
