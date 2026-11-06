"""Phase 3c helpers: controls copied from a real public-agency procurement packet (structure only; fake data).
Where a script is more reliable than reading by eye: name matching, dates, dollar tiers, per-line competition, running totals.
Nothing here sends, signs, orders, approves, or pays, and nothing opens a network connection.

    python -I -X utf8 tools/controls.py screen                /screen: disclosures + exclusion list for all 8 contractors and the 3 suppliers
    python -I -X utf8 tools/controls.py request <project>     /request: the approval request form (type, purpose, funding, competition, certification)
    python -I -X utf8 tools/controls.py closeout <project>    /closeout: running totals, open items, the supplier's completion claim, the certificate
    python -I -X utf8 tools/controls.py status                one line per control (read-only)
    python -I -X utf8 tools/controls.py log-review <path>     log 1 row for a saved checker review
    python -I -X utf8 tools/controls.py verify-log            recompute the controls log's hash chain (read-only)

Each action writes its outputs and appends exactly one row to audit/controls-log.csv; a second run is refused.
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
C = RULES["controls"]
DEMO = dt.date.fromisoformat(RULES["demo_date"])
LOG = os.path.join(ROOT, "audit", "controls-log.csv")
CHAIN = os.path.join(ROOT, "audit", "controls-log.chain.txt")
HEADER = "timestamp,actor,vendor,action,detail,result"
FAKE = "*Fake data for a demo. Built by the assistant from the records named below. Nothing is approved, signed, sent, or paid by the assistant.*"


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


def day(s):
    return dt.date.fromisoformat(s.strip()[:10])


def key_name(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def people():
    return {re.sub(r"\s*\(.*?\)", "", r["Role"]).strip(): r["Name"] for r in rows(text(path("company", "people.md")), "Role")}


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
        raise Refused("the controls log's hash chain doesn't verify")
    if logged(action):
        raise Refused(f"{action} already ran (the log is append-only)")


def log(actor, subject, action, detail, result):
    good, n, _ = chain_ok()
    if not good:
        raise Refused("the controls log's hash chain doesn't verify")
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
    if p.endswith(".json"):
        json.dump(content, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    else:
        open(p, "w", encoding="utf-8").write(content.strip() + "\n")


# ------------------------------------------------------------- /screen -------------------------------------------------------------
def exclusions():
    t = text(path("company", "exclusion-list.md"))
    active, ended = {}, {}
    for r in rows(t, "Excluded party"):
        (active if day(r["Excluded from"]) <= DEMO <= day(r["Excluded until"]) else ended)[key_name(r["Excluded party"])] = r
    return active, kv(t).get("As of", "")


def screen():
    once("screen")
    active, as_of = exclusions()
    who = people()
    slugs = sorted(d for d in os.listdir(path("vendors")) if os.path.isdir(path("vendors", d)))
    summary = {}
    for s in slugs:
        docs = {k: kv(text(path("vendors", s, "documents", f"{k}.md"))) if os.path.exists(path("vendors", s, "documents", f"{k}.md")) else {}
                for k in ("w9", "coi", "license", "request")}
        names = [("W-9 legal name", docs["w9"].get("Legal name")), ("insurance insured", docs["coi"].get("Insured")),
                 ("license holder", docs["license"].get("License holder"))]
        codes, evidence, rels, dis = [], [], [], {}
        dpath = path("vendors", s, *C["disclosure_file"].split("/"))
        if not os.path.exists(dpath):
            codes.append("MISSING_DISCLOSURE")
            evidence.append({"check": "conflict-of-interest disclosure on file", "found": "missing", "result": "MISSING_DISCLOSURE"})
        else:
            dt_ = text(dpath)
            f = kv(dt_)
            paid = next((v for k, v in f.items() if k.startswith("No one was paid")), "")
            rels = [r for r in rows(dt_, "Person") if r.get("Person") and r["Person"] != "none"]
            dis = {"file": rel(dpath), "firm": f.get("Firm"), "signed_by": f.get("Signed by"), "date": f.get("Date signed"),
                   "paid_help_statement": paid, "relationships": rels}
            names += [("disclosure firm", f.get("Firm")), ("disclosure signer", f.get("Signed by"))] + [("disclosed person", r["Person"]) for r in rels]
            evidence.append({"check": "conflict-of-interest disclosure on file", "found": f"signed {f.get('Date signed')} by {f.get('Signed by')}", "result": "ok"})
            if not paid.startswith("Yes"):
                codes.append("PAID_SOLICITATION")
            evidence.append({"check": "no paid help to win the work", "found": paid or "blank", "result": "ok" if paid.startswith("Yes") else "PAID_SOLICITATION"})
            if rels:
                codes.append("CONFLICT_DISCLOSED")
            evidence.append({"check": "disclosed relationships", "found": "; ".join(f"{r['Person']}: {r['Relationship']} ({r['Interest']})" for r in rels) or "none",
                             "result": "CONFLICT_DISCLOSED" if rels else "ok"})
        matched = sorted({active[key_name(n)]["Excluded party"] for _, n in names if n and key_name(n) in active})
        for label, n in names:
            if n:
                hit = key_name(n) in active
                evidence.append({"check": f"exclusion list: {label}", "found": n, "result": "EXCLUDED" if hit else "not listed"})
        if matched:
            codes.append("EXCLUDED")
        result = "EXCLUDED" if "EXCLUDED" in codes else ("REVIEW" if codes else "CLEAR")
        out = {"vendor": s, "result": result, "codes": sorted(codes), "disclosure": dis, "names_checked": [n for _, n in names if n],
               "exclusion_list_as_of": as_of, "evidence": evidence}
        if result != "CLEAR":
            out["reviewers"] = [C["exclusion_reviewer"] if result == "EXCLUDED" else C["disclosure_reviewer"]]
        if matched:
            out["matched"] = matched
            out["hold_followup"] = bool(glob.glob(path("vendors", s, "drafts", "*.md")))
        if rels and docs["request"]:
            tier = tier_for(dollars(docs["request"]["Contract amount"]))
            recused = sorted({role for r in rels for role, name in who.items() if name in r["Relationship"] and role in tier})
            if recused:
                keep = [a for a in tier if a not in recused]
                for role in C["approval_order"]:
                    if len(keep) >= len(tier):
                        break
                    if role not in keep and role not in recused:
                        keep.append(role)
                out["recused"], out["approvers"] = recused, keep
        out["run"] = {"by": "onboarding-assistant", "at": dt.datetime.now().isoformat(timespec="seconds"), "rules": "company/rules.json (controls)",
                      "tool": "tools/controls.py screen"}
        write(path("vendors", s, "screen.json"), out)
        summary[s] = out
    sup = {}
    for r in rows(text(path("company", "approved-suppliers.md")), "Supplier"):
        sup[r["Supplier"]] = "EXCLUDED" if key_name(r["Supplier"]) in active else "CLEAR"
    write(path("controls", "supplier-screen.json"), {"suppliers": sup, "exclusion_list_as_of": as_of,
                                                     "checked": "every approved supplier's name against company/exclusion-list.md"})
    lines = ["# Screening results (fictional)", "", FAKE, "",
             f"Disclosures from `vendors/*/{C['disclosure_file']}`; names checked against `company/exclusion-list.md` (as of {as_of}).", "",
             "| Vendor | Result | Codes | What a person does |", "|---|---|---|---|"]
    for s, o in summary.items():
        todo = "nothing"
        if o["result"] == "EXCLUDED":
            todo = f"{o['reviewers'][0]} reviews; don't award; hold the follow-up draft" if o.get("hold_followup") else f"{o['reviewers'][0]} reviews; don't award"
        elif o["result"] == "REVIEW":
            todo = f"{o['reviewers'][0]} reviews the disclosure" + (f"; {', '.join(o['recused'])} recused, {', '.join(o['approvers'])} signs instead" if o.get("recused") else "")
        lines.append(f"| {s} | {o['result']} | {', '.join(o['codes']) or 'none'} | {todo} |")
    lines += ["", "| Supplier | Result |", "|---|---|"] + [f"| {k} | {v} |" for k, v in sup.items()]
    write(path("controls", "screen.md"), "\n".join(lines))
    counts = {r: sum(1 for o in summary.values() if o["result"] == r) for r in C["screen_results"]}
    flagged = "; ".join(f"{s} {o['result']} {','.join(o['codes'])}" for s, o in summary.items() if o["result"] != "CLEAR")
    log("onboarding-assistant", "all", "screen",
        f"vendors/*/screen.json; controls/supplier-screen.json; controls/screen.md; {len(summary)} contractors, {len(sup)} suppliers; {flagged or 'none flagged'}",
        ", ".join(f"{v} {k}" for k, v in counts.items()))


# ------------------------------------------------------------- /request -------------------------------------------------------------
def pdir(project, *a):
    return path("projects", project, *a)


def order(project):
    po = text(pdir(project, "approved", "po-PQ-1042.md"))
    return po, kv(po), rows(po, "SKU")


def request(project):
    once("approval_request")
    req_t = kv(text(pdir(project, "request.md")))
    po, pof, lines = order(project)
    total = dollars(pof["Total"])
    ptype = next(t for t in C["procurement_types"] if t["max_amount"] is None or total <= t["max_amount"])
    fund = kv(text(pdir(project, "funding.md")))
    available = dollars(fund["Available"])
    plan = {r["Item"]: r for r in rows(text(pdir(project, "partner-plan.md")), "Line")}
    approved = {r["Supplier"] for r in rows(text(path("company", "approved-suppliers.md")), "Supplier") if r.get("Status") == "Approved"}
    catalog = []
    for f in sorted(glob.glob(pdir(project, "catalogs", "*.md"))):
        t = text(f)
        catalog += [dict(r, supplier=kv(t)["Supplier"]) for r in rows(t, "SKU")]
    src = json.load(open(pdir(project, "out", "source.json"), encoding="utf-8"))
    appr = json.load(open(pdir(project, "out", "approval.json"), encoding="utf-8"))
    proposed = {r["Line"]: r["SKU"] for r in rows(text(pdir(project, "proposed.md")), "Line")}
    failed = {proposed.get(ln): c for ln, c in appr.get("FAIL", {}).items()}

    def fits(item, r):
        pl = plan[item]
        return (int(r["Width (in)"]) <= int(pl["Max width (in)"]) and int(r["Depth (in)"]) <= int(pl["Max depth (in)"])
                and pl["Finish"] in ("any", r["Finish"]) and pl["Fabric"] in ("any", r["Fabric"]) and r["supplier"] in approved)

    table_rows, flags, lowest, checked, why = [], {}, {}, [], {}
    for ln in lines:
        lt = int(ln["Qty"]) * dollars(ln["Unit price"])
        if "line_min" not in ptype or lt <= ptype["line_min"]:
            continue
        checked.append(ln["SKU"])
        opts = [r for r in catalog if r["Item"] == ln["Item"] and fits(ln["Item"], r)]
        sups = sorted({r["supplier"] for r in opts})
        low = min(opts, key=lambda r: dollars(r["Unit price"]))
        flag, note = "", ""
        if len(sups) < ptype["min_suppliers"]:
            flag, note = "SINGLE_SOURCE", f"Only {sups[0]} offers an in-spec {ln['Item'].lower()}. The {C['justification_writer']} writes why one source is acceptable."
        elif dollars(ln["Unit price"]) > dollars(low["Unit price"]):
            flag = "LOWEST_NOT_SELECTED"
            reason = "LATE_ITEM" if low["SKU"] in src.get("late", {}) else failed.get(low["SKU"])
            lowest[ln["SKU"]] = {"lowest_sku": low["SKU"], "lowest_price": dollars(low["Unit price"]), "selected_price": dollars(ln["Unit price"]),
                                 "difference": dollars(ln["Unit price"]) - dollars(low["Unit price"]), "reason_on_record": reason}
            if reason == "LATE_ITEM":
                late = src["late"][low["SKU"]]
                note = (f"On record: {low['SKU']} ({usd(dollars(low['Unit price']))}) would arrive {late['arrives']}, {late['days_late']} days after "
                        f"the install date (out/source.json). The {C['justification_writer']} confirms by signing.")
            elif reason:
                note = f"On record: {low['SKU']} failed product approval ({reason}, out/approval.json). The {C['justification_writer']} confirms by signing."
            else:
                note = f"No reason on record. The {C['justification_writer']} writes why the lowest price wasn't selected."
        if flag:
            flags[ln["SKU"]] = flag
            why[ln["SKU"]] = note
        table_rows.append(f"| {ln['SKU']} | {ln['Item']} | {usd(lt)} | {', '.join(sups)} | {low['SKU']} {low['Unit price']} | "
                          f"{ln['Unit price']} | {flag or 'ok'} | {note or 'competing prices; lowest selected'} |")
    if ptype["max_amount"] is None:
        flags["ORDER"] = "FORMAL_BID_REQUIRED"
        why["ORDER"] = "Above the Standard purchase limit: an advertised request for proposals with written scoring is required."
    needs = sorted(k for k, v in flags.items() if v in ("SINGLE_SOURCE", "FORMAL_BID_REQUIRED") or not lowest.get(k, {}).get("reason_on_record"))
    short = total > available
    status = "FUNDS_SHORT" if short else ("NEEDS_JUSTIFICATION" if needs else "READY_TO_CERTIFY")
    approvers = tier_for(total)
    who = people()
    out = {"project": project, "order": "PQ-1042", "type": ptype["name"], "total": total, "budget_line": fund["Budget line"], "available": available,
           "left_after_order": available - total, "funds_short": short, "lines_checked": sorted(checked), "flags": flags, "lowest": lowest,
           "needs_person": needs, "status": status, "approvers": approvers, "certified": False,
           "run": {"by": "procurement-assistant", "at": dt.datetime.now().isoformat(timespec="seconds"), "tool": "tools/controls.py request"}}
    write(pdir(project, "controls", "approval-request.json"), out)
    md = f"""# Procurement approval request: order PQ-1042, {project} (fictional)

{FAKE}

Order PQ-1042 was approved on {pof['Approved on']}, before this checklist was added. This form records what the checklist finds, for the file.

| Field | Value |
|---|---|
| Project | {req_t['Building']}, Unit {req_t['Unit']} |
| Order total | {usd(total)} |
| Procurement type | {ptype['name']}: {ptype['competition']} |
| Status | {status} |

## Purpose
Furnish the {' and '.join(x.strip() for x in req_t['Rooms'].split(','))} by {req_t['Install by']}, as requested by {req_t['Requested by']} on {req_t['Request date']}. Must have: {req_t['Must have']}.

## Funding
| Budget line | Approved | Committed before this order | Available | This order | Left |
|---|---|---|---|---|---|
| {fund['Budget line']} | {fund['Approved amount']} | {fund['Committed before this order']} | {usd(available)} | {usd(total)} | {usd(available - total)} |

## Competition (lines over {usd(ptype.get('line_min', 0))})
| SKU | Item | Line total | Suppliers with an in-spec price | Lowest in-spec | Selected | Flag | Justification |
|---|---|---|---|---|---|---|---|
""" + "\n".join(table_rows) + f"""

Still needs a person's written justification: {', '.join(needs) or 'none'}.

## Certification
The approver certifies that the information above and attached is true and complete, and that the suppliers were selected and prices set under Palmquay's purchasing rules.

Prepared by: procurement assistant (AI), from the records named above
Approvers (in order): {', '.join(f'{who.get(a, a)}, {a}' for a in approvers)}

Approved by: ____________________   Date: __________
"""
    write(pdir(project, "controls", "approval-request.md"), md)
    log("procurement-assistant", project, "approval_request",
        f"projects/{project}/controls/approval-request.json; projects/{project}/controls/approval-request.md; {ptype['name']} {usd(total)}; "
        f"budget line {fund['Budget line']}, left {usd(available - total)}; flags " + ", ".join(f"{k} {v}" for k, v in flags.items()),
        f"{status}; certification blank")


# ------------------------------------------------------------- /closeout -------------------------------------------------------------
def closeout(project):
    once("closeout")
    po, pof, lines = order(project)
    total = dollars(pof["Total"])
    approved_delta, pending = 0, []
    for f in sorted(glob.glob(pdir(project, "out", "change-request-*.json"))):
        cid = os.path.basename(f)[len("change-request-"):-5]
        if re.search(r"Approved by: _{3,}", text(f[:-5] + ".md")):
            pending.append(cid)
        else:
            approved_delta += json.load(open(f, encoding="utf-8"))["delta"]
    invs = {os.path.basename(f)[:-3]: kv(text(f)) for f in sorted(glob.glob(pdir(project, "invoices", "*.md")))}
    match = json.load(open(pdir(project, "out", "match.json"), encoding="utf-8"))["invoices"]
    held = sorted(k for k, v in match.items() if v["result"] == "HOLD")
    receipt = {r["SKU"]: int(r["Qty received"]) for r in rows(text(pdir(project, "received", "receipt-2026-11-12.md")), "SKU")}
    track_t = text(pdir(project, "deliveries", "tracking-2026-11-12.md"))
    track = {r["SKU"]: r for r in rows(track_t, "SKU")}
    full = [l["SKU"] for l in lines if receipt.get(l["SKU"], 0) >= int(l["Qty"])]
    open_lines = sorted(l["SKU"] for l in lines if l["SKU"] not in full)
    tasks = sorted(r["Task"] for r in rows(text(pdir(project, "out", "tasks.md")), "Task") if re.match(r"T\d+$", r.get("Task", "")))
    invoiced = sum(dollars(v["Total due"]) for v in invs.values())
    current = total + approved_delta
    out = {"project": project, "order": "PQ-1042", "original": total, "approved_changes": approved_delta, "current": current, "invoiced": invoiced,
           "approved_for_payment": sum(dollars(v["Total due"]) for v in invs.values() if v.get("Payment status", "").startswith("approved")),
           "paid": sum(dollars(v["Total due"]) for v in invs.values() if v.get("Payment status") == "paid"),
           "held": sum(dollars(invs[k]["Total due"]) for k in held), "remaining": current - invoiced,
           "lines_received": len(full), "lines_total": len(lines), "open_lines": open_lines, "held_invoices": held,
           "pending_changes": pending, "open_tasks": tasks}
    notices = sorted(glob.glob(pdir(project, "closeout", "*.md")))
    reply_rel = None
    if notices:
        nt = kv(text(notices[0]))
        sup = nt["Supplier"]
        nd = sorted(l["SKU"] for l in lines if l["Supplier"] == sup and l["SKU"] not in full)
        out["claim"] = {"supplier": sup, "notice": rel(notices[0]), "result": "CLAIM_CONTRADICTED" if nd else "CLAIM_CONFIRMED", "not_delivered": nd}
        if nd:
            items = "\n".join(f"- {s}: {track.get(s, {}).get('Status', 'no tracking')}, ETA {track.get(s, {}).get('ETA') or 'none'}; not on the "
                              f"receipt of {kv(text(pdir(project, 'received', 'receipt-2026-11-12.md')))['As of']}" for s in nd)
            reply_rel = f"projects/{project}/controls/drafts/reply-{key_name(sup).split()[0]}-{nt['Date']}.md"
            write(path(*reply_rel.split("/")), f"""# Draft reply to {sup} (fictional): not sent

Draft only. The {C['closeout_verifier']} reviews and sends it; the assistant does not send email.

Hello {sup} team,

Thank you for your completion notice of {nt['Date']} for order PQ-1042. We can't sign off on completion yet. Our records show these items haven't arrived:
{items}

Please send updated delivery dates. We'll sign the completion certificate once everything is received and checked.

Thank you,
{C['closeout_verifier']} ({people().get(C['closeout_verifier'], '')})
""")
    out["status"] = "NOT_READY" if (open_lines or held or pending or tasks) else "READY_TO_CLOSE"
    out["certificate_signed"] = False
    out["run"] = {"by": "procurement-assistant", "at": dt.datetime.now().isoformat(timespec="seconds"), "tool": "tools/controls.py closeout"}
    write(pdir(project, "controls", "contract-summary.json"), out)
    claim = out.get("claim", {})
    write(pdir(project, "controls", "contract-summary.md"), f"""# Running totals and close-out: order PQ-1042, {project} (fictional)

{FAKE}

| Original order | Approved changes | Current order | Invoiced to date | Approved for payment | Paid | Held | Remaining |
|---|---|---|---|---|---|---|---|
| {usd(total)} | {usd(approved_delta)} | {usd(current)} | {usd(invoiced)} | {usd(out['approved_for_payment'])} | {usd(out['paid'])} | {usd(out['held'])} | {usd(out['remaining'])} |

Lines received in full: {len(full)} of {len(lines)}. Open lines: {', '.join(open_lines) or 'none'}. Held invoices: {', '.join(held) or 'none'}. Pending changes: {', '.join(pending) or 'none'}. Open tasks: {', '.join(tasks) or 'none'}.

Supplier completion notice: {claim.get('supplier', 'none')}: {claim.get('result', 'n/a')}; not delivered: {', '.join(claim.get('not_delivered', [])) or 'none'}.{' Draft reply: `' + reply_rel + '` (not sent).' if reply_rel else ''}

Close-out status: {out['status']}.
""")
    reasons = f"{len(open_lines)} order lines open, {len(held)} invoice held, {len(pending)} change request pending, {len(tasks)} tasks open"
    write(pdir(project, "controls", "completion-certificate.md"), f"""# Completion certificate: order PQ-1042, {project} (fictional)

{FAKE}

Status: {'NOT READY' if out['status'] == 'NOT_READY' else 'READY'} to sign: {reasons}. Nobody signs until every item is received and checked.

## 1. The supplier certifies
Every item on the order from this supplier has been delivered and installed, and the work area is clean.

Signature: ____________________   Name: ____________________   Date: __________

## 2. The {C['closeout_verifier']} verifies
I checked the items against the order, the tracking, and the receipt, and the supplier's certification above is true.

Signature: ____________________   Name: ____________________   Date: __________
""")
    log("procurement-assistant", project, "closeout",
        f"projects/{project}/controls/contract-summary.json; projects/{project}/controls/contract-summary.md; projects/{project}/controls/completion-certificate.md"
        + (f"; {reply_rel}" if reply_rel else "") + f"; invoiced {usd(invoiced)} of {usd(current)}, remaining {usd(out['remaining'])}; "
        f"{claim.get('supplier', '')} {claim.get('result', '')} {','.join(claim.get('not_delivered', []))}",
        f"{out['status']}; certificate unsigned; reply drafted, not sent" if reply_rel else f"{out['status']}; certificate unsigned")


# ------------------------------------------------------------- misc -------------------------------------------------------------
def status():
    print("| Control | Done | Output |\n|---|---|---|")
    for a, o in (("screen", "vendors/*/screen.json"), ("approval_request", "projects/unit-4b/controls/approval-request.json"),
                 ("closeout", "projects/unit-4b/controls/contract-summary.json")):
        print(f"| {a} | {'yes' if logged(a) else 'no'} | {o} |")


def log_review(p):
    t = text(path(*p.replace("\\", "/").split("/")))
    m = re.search(r"^Overall: (\w+)", t, re.M)
    log("compliance-checker", "unit-4b + vendors", "checker_review", f"{p}; recorded by procurement-assistant",
        f"overall {m.group(1) if m else 'not stated'}")


def verify_log():
    good, n, ok = chain_ok()
    print(f"controls log: {n} rows, {ok} of {n} chain links verify -> {'OK' if good else 'BROKEN'}")
    if not good:
        raise Refused("hash chain broken")


if __name__ == "__main__":
    a = sys.argv[1:]
    try:
        if a == ["screen"]:
            screen()
        elif len(a) == 2 and a[0] == "request":
            request(a[1])
        elif len(a) == 2 and a[0] == "closeout":
            closeout(a[1])
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
