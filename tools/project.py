"""Phase 3a helpers: the buying activities for a furnishing project, where a script is more reliable than reading by eye
(measurements, dates, totals, spec matches, three-way matches, file hashes) plus the append-only procurement log.
Fake data only. Nothing here sends, orders, approves, signs, or pays, and nothing opens a network connection.

    python -I -X utf8 tools/project.py scope <project>       /scope: request -> structured brief; missing and conflicting items
    python -I -X utf8 tools/project.py source <project>      /source: lead times vs. the install date; in-time alternatives
    python -I -X utf8 tools/project.py quote <project>       /quote: quotes -> one comparison table + a purchase request DRAFT
    python -I -X utf8 tools/project.py approve <project>     /approve: proposed products vs. the plan's spec; unclear -> a person
    python -I -X utf8 tools/project.py change <project>      /change: price a substitution; the baseline stays until approved
    python -I -X utf8 tools/project.py deliver <project>     /deliver: tracking vs. the order; tasks + a client update DRAFT
    python -I -X utf8 tools/project.py match <project>       /match: invoice vs. order vs. receipt; flags only, never pays
    python -I -X utf8 tools/project.py status <project>      one line per activity (read-only)
    python -I -X utf8 tools/project.py manifest <files...>   SHA-256 table for a checker review (read-only)
    python -I -X utf8 tools/project.py log-review <path>     log 1 row for a saved checker review
    python -I -X utf8 tools/project.py verify-log            recompute the procurement log's hash chain (read-only)

Each activity writes projects/<project>/out/ files and appends exactly one row to audit/procurement-log.csv.
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
PR = RULES["projects"]
TODAY = dt.date.fromisoformat(RULES["demo_date"])
LOG = os.path.join(ROOT, "audit", "procurement-log.csv")
CHAIN = os.path.join(ROOT, "audit", "procurement-log.chain.txt")
HEADER = "timestamp,actor,vendor,action,detail,result"
ME = "procurement-assistant"


class Refused(Exception):
    pass


class Unreadable(Exception):
    pass


# ------------------------------------------------------------- reading -------------------------------------------------------------
def pdir(project, *rest):
    p = os.path.join(ROOT, "projects", project, *rest)
    return p


def text(path):
    if not os.path.exists(path):
        raise Unreadable(f"{rel(path)} not found")
    return open(path, encoding="utf-8").read()


def rel(p):
    return os.path.relpath(os.path.abspath(p), ROOT).replace("\\", "/")


def kv(t):
    """'Key: value' lines (outside tables) -> dict; the first occurrence wins; empty values stay empty."""
    out = {}
    for line in t.splitlines():
        if line.startswith("|"):
            continue
        m = re.match(r"^([A-Z][A-Za-z ,()/-]*?):[ \t]*(.*)$", line)
        if m and m.group(1).strip() not in out:
            out[m.group(1).strip()] = m.group(2).strip()
    return out


def rows(t, first):
    lines = t.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        head = [c.strip() for c in line.strip().strip("|").split("|")]
        if head[0] != first:
            continue
        out = []
        for r in lines[i + 2:]:
            if not r.startswith("|"):
                break
            cells = [c.strip() for c in r.strip().strip("|").split("|")]
            out.append(dict(zip(head, cells + [""] * (len(head) - len(cells)))))
        return out
    return []


def dollars(s):
    m = re.search(r"\$\s?([\d,]+)", s or "")
    if not m:
        return None
    return int(m.group(1).replace(",", ""))


def money(n):
    return f"${n:,}"


def feet_to_in(s):
    m = re.match(r"\s*(\d+(?:\.\d+)?)\s*ft\s*$", s or "")
    if not m:
        return None
    return int(round(float(m.group(1)) * 12))


def date(s, what):
    try:
        return dt.date.fromisoformat(s.strip())
    except (ValueError, AttributeError):
        raise Unreadable(f"{what}: '{s}' is not a date")


def approvers(amount):
    for t in RULES["approval_tiers"]:
        if t["max_amount"] is None or amount <= t["max_amount"]:
            return t["approvers"]


def people():
    t = open(os.path.join(ROOT, "company", "people.md"), encoding="utf-8").read()
    return {r["Role"]: r["Name"] for r in rows(t, "Role")}


def load_catalog(project):
    items = {}
    for p in sorted(glob.glob(pdir(project, "catalogs", "*.md"))):
        t = text(p)
        sup = kv(t).get("Supplier")
        for r in rows(t, "SKU"):
            r["Supplier"] = sup
            items[r["SKU"]] = r
    if not items:
        raise Unreadable("no catalogs found")
    return items


def approved_suppliers():
    t = open(os.path.join(ROOT, "company", "approved-suppliers.md"), encoding="utf-8").read()
    return {r["Supplier"] for r in rows(t, "Supplier") if r.get("Status") == "Approved"}


def request(project):
    return kv(text(pdir(project, "request.md")))


def plan(project):
    return {r["Line"]: r for r in rows(text(pdir(project, "partner-plan.md")), "Line")}


def purchase_order(project):
    t = text(pdir(project, "approved", "po-PQ-1042.md"))
    f = kv(t)
    lines = {r["SKU"]: r for r in rows(t, "SKU")}
    freight = {k[len("Freight "):]: dollars(v) for k, v in f.items() if k.startswith("Freight ")}
    return f, lines, freight


# ------------------------------------------------------------- writing -------------------------------------------------------------
def now():
    return dt.datetime.now().isoformat(timespec="seconds")


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
    return any(r[3] == action for r in csv.reader(open(LOG, encoding="utf-8").read().splitlines()[1:]) if len(r) == 6)


def log(project, action, detail, result, actor=ME):
    good, n, _ = chain_ok()
    if not good:
        raise Refused("procurement log hash chain doesn't verify; not appending (run verify-log)")
    if not os.path.exists(LOG):
        with open(LOG, "w", encoding="utf-8", newline="") as f:
            f.write(HEADER + "\n")
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerow([now(), actor, project, action, detail, result])
    line = buf.getvalue().rstrip("\n")
    links = open(CHAIN, encoding="utf-8").read().split() if os.path.exists(CHAIN) else []
    prev = links[-1] if links else hashlib.sha256(HEADER.encode()).hexdigest()
    with open(LOG, "a", encoding="utf-8", newline="") as f:
        f.write(line + "\n")
    with open(CHAIN, "a", encoding="utf-8", newline="") as f:
        f.write(hashlib.sha256((prev + "\n" + line).encode("utf-8")).hexdigest() + "\n")
    print(f"log row {n + 1}: {line}")


def once(action):
    if logged(action):
        raise Refused(f"{action} already ran for this project (one row per action; the log is append-only)")


def write(project, name, content):
    p = pdir(project, "out", *name.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content if isinstance(content, str) else json.dumps(content, indent=2) + "\n")
    return rel(p)


# ------------------------------------------------------------- activities ----------------------------------------------------------
def scope(project):
    once("scope_brief")
    req = request(project)
    rooms = [r.strip() for r in req.get("Rooms", "").split(",") if r.strip()]
    if not rooms:
        raise Unreadable("request.md has no Rooms line")
    walls = [f"{r[0].upper()}{r[1:]} wall {w}" for r in rooms for w in ("A", "B")]
    meas = {k: (feet_to_in(req[k]) if req.get(k) else None) for k in walls}
    missing = [k for k in walls if meas[k] is None]
    codes = ["MISSING_MEASUREMENT"] if missing else []
    bed = req.get("Bed size", "").lower()
    clear = PR["bed_side_clearance_in"]
    bed_walls = [v for k, v in meas.items() if k.startswith("Bedroom") and v]
    wall = min(bed_walls) if bed_walls else None
    need = PR["bed_widths_in"][bed] + 2 * clear if bed in PR["bed_widths_in"] else None
    fits = [b for b, w in sorted(PR["bed_widths_in"].items(), key=lambda kv: kv[1]) if wall and w + 2 * clear <= wall]
    if need and wall and need > wall:
        codes.append("SCOPE_CONFLICT")
    out = {"status": "NEEDS_INFO" if codes else "READY", "codes": sorted(codes), "missing": missing, "bed_requested": bed,
           "bed_needs_in": need, "wall_in": wall, "largest_bed_that_fits": fits[-1] if fits else None, "_measurements": meas}
    j = write(project, "brief.json", out)
    lines = ["# Project brief: " + project + " (fictional)", "", f"Status: **{out['status']}**", "",
             "| Field | From the request | Note |", "|---|---|---|"]
    for k, v in req.items():
        note = "MISSING: ask once" if k in missing else ""
        if k == "Bed size" and "SCOPE_CONFLICT" in codes:
            note = (f"SCOPE_CONFLICT: a {bed} needs {need} in ({PR['bed_widths_in'][bed]} in + {clear} in each side); "
                    f"the shortest bedroom wall known is {wall} in; the largest bed that fits is a {out['largest_bed_that_fits']}")
        lines.append(f"| {k} | {v or '(blank)'} | {note} |")
    lines += ["", "## One question for the requester (draft; a person sends it)",
              f"Before we order, please send: {', '.join(missing) if missing else 'nothing'}"
              + (f"; and confirm a {out['largest_bed_that_fits']} bed instead of a {bed}." if 'SCOPE_CONFLICT' in codes else "."),
              "", "Nothing is ordered until a person approves this brief."]
    m = write(project, "brief.md", "\n".join(lines) + "\n")
    log(project, "scope_brief", f"{j}; {m}; codes {','.join(out['codes']) or 'none'}; missing {', '.join(missing) or 'none'}", out["status"])
    print(json.dumps({k: v for k, v in out.items() if not k.startswith('_')}))


def meets(item, spec):
    ok = int(item["Width (in)"]) <= int(spec["Max width (in)"]) and int(item["Depth (in)"]) <= int(spec["Max depth (in)"])
    ok = ok and (spec["Finish"] == "any" or item["Finish"] == spec["Finish"])
    ok = ok and (spec["Fabric"] == "any" or item["Fabric"] == spec["Fabric"])
    return ok


def source(project):
    once("source_check")
    req, spec, cat = request(project), plan(project), load_catalog(project)
    start, install = date(req.get("Request date"), "Request date"), date(req.get("Install by"), "Install by")
    ok_sup = approved_suppliers()
    proposed = rows(text(pdir(project, "proposed.md")), "Line")
    late, alt, table = {}, {}, []
    for p in proposed:
        it = cat.get(p["SKU"])
        if it is None:
            raise Unreadable(f"SKU {p['SKU']} is in no catalog")
        arrive = start + dt.timedelta(days=int(it["Lead time (days)"]))
        row = [p["Line"], p["SKU"], it["Item"], it["Supplier"], it["Lead time (days)"], arrive.isoformat(), "on time"]
        if arrive > install:
            late[p["SKU"]] = {"arrives": arrive.isoformat(), "days_late": (arrive - install).days}
            opts = [c for c in cat.values() if c["Item"] == it["Item"] and c["SKU"] != p["SKU"] and c["Supplier"] in ok_sup
                    and meets(c, spec[p["Line"]]) and start + dt.timedelta(days=int(c["Lead time (days)"])) <= install]
            if opts:
                best = min(opts, key=lambda c: (dollars(c["Unit price"]), c["SKU"]))
                alt[p["SKU"]] = best["SKU"]
            row[-1] = f"LATE_ITEM: {(arrive - install).days} days late" + (f"; in time: {alt.get(p['SKU'])}" if p["SKU"] in alt else "")
        table.append(row)
    out = {"items_checked": len(proposed), "late": late, "alternative": alt}
    j = write(project, "source.json", out)
    md = ["# Lead times vs. the install date (" + install.isoformat() + "), fictional", "",
          "| Line | SKU | Item | Supplier | Lead (days) | Arrives | Result |", "|---|---|---|---|---|---|---|"]
    md += ["| " + " | ".join(r) + " |" for r in table]
    md += ["", f"Rule: {PR['alternative_rule']}. A person picks between late-but-preferred and on-time."]
    m = write(project, "source.md", "\n".join(md) + "\n")
    log(project, "source_check", f"{j}; {m}; {len(proposed)} items; late {', '.join(late) or 'none'}", f"{len(late)} late")
    print(json.dumps(out))


def quote(project):
    once("quote_compare")
    quotes, total, md = {}, 0, ["# Quote comparison (fictional)", "",
                                "| Quote | Supplier | Subtotal | Freight | Total | Valid until | Flags |", "|---|---|---|---|---|---|---|"]
    ok_sup = approved_suppliers()
    lines_all = []
    for qp in sorted(glob.glob(pdir(project, "quotes", "*.md"))):
        t = text(qp)
        f = kv(t)
        ls = rows(t, "SKU")
        sub = 0
        for l in ls:
            q, u = int(l["Qty"]), dollars(l["Unit price"])
            if dollars(l["Line total"]) != q * u:
                raise Unreadable(f"{rel(qp)}: {l['SKU']} line total doesn't equal qty x price")
            sub += q * u
            lines_all.append((f["Quote number"], l["SKU"], l["Item"], q, u, f["Supplier"]))
        if dollars(f.get("Subtotal")) not in (None, sub):
            raise Unreadable(f"{rel(qp)}: stated subtotal {f.get('Subtotal')} doesn't match the lines ({money(sub)})")
        codes = []
        if "Freight" in f:
            freight = dollars(f["Freight"]) or 0
        else:
            notes = f.get("Notes", "")
            hidden = dollars(notes) if any(w in notes.lower() for w in PR["hidden_freight_words"]) else None
            freight = hidden or 0
            if hidden:
                codes.append("HIDDEN_FREIGHT")
        if date(f.get("Valid until"), "Valid until") < TODAY:
            codes.append("QUOTE_EXPIRED")
        if f["Supplier"] not in ok_sup:
            raise Refused(f"{f['Supplier']} is not an approved supplier")
        quotes[f["Quote number"]] = {"subtotal": sub, "freight": freight, "total": sub + freight, "codes": sorted(codes)}
        total += sub + freight
        md.append(f"| {f['Quote number']} | {f['Supplier']} | {money(sub)} | {money(freight)} | {money(sub + freight)} | {f['Valid until']} | "
                  + ("; ".join(codes) or "none") + " |")
    appr = approvers(total)
    out = {"quotes": quotes, "total": total, "approvers": appr}
    j = write(project, "quotes.json", out)
    md += ["", f"Grand total: **{money(total)}** (before tax; tax is handled by Finance)"]
    m = write(project, "quotes.md", "\n".join(md) + "\n")
    names = people()
    pr = ["# Purchase request DRAFT (fictional): not an order", "",
          "This is a draft for review. Nothing has been ordered. A person approves it and places the order.", "",
          "| Quote | SKU | Item | Qty | Unit price | Line total | Supplier |", "|---|---|---|---|---|---|---|"]
    pr += [f"| {q} | {s} | {i} | {n} | {money(u)} | {money(n * u)} | {sup} |" for q, s, i, n, u, sup in lines_all]
    pr += ["", "| Quote | Freight |", "|---|---|"] + [f"| {k} | {money(v['freight'])} |" for k, v in quotes.items()]
    pr += ["", f"Total: **{money(total)}**", "",
           "Before ordering, fix the flags: " + "; ".join(f"{k} {', '.join(v['codes'])}" for k, v in quotes.items() if v["codes"]), "",
           "Approvers (in order): " + " > ".join(f"{r} ({names.get(r, '?')})" for r in appr), "",
           "Approved by: ____________________   Date: __________"]
    d = write(project, "purchase-request-draft.md", "\n".join(pr) + "\n")
    log(project, "quote_compare", f"{j}; {m}; {d}; total {money(total)}; approvers {' > '.join(appr)}",
        "draft for review, not ordered")
    print(json.dumps(out))


def approve(project):
    once("product_approval")
    spec, cat = plan(project), load_catalog(project)
    proposed = rows(text(pdir(project, "proposed.md")), "Line")
    out = {"PASS": [], "FAIL": {}, "NEEDS_PERSON": []}
    md = ["# Product approval against the design plan (fictional)", "",
          "| Line | Item | SKU | Size (W x D in) | Finish | Fabric | Verdict | Why |", "|---|---|---|---|---|---|---|---|"]
    for p in proposed:
        it, s = cat[p["SKU"]], spec[p["Line"]]
        fails, why = [], []
        if int(it["Width (in)"]) > int(s["Max width (in)"]):
            fails.append("TOO_WIDE"); why.append(f"{it['Width (in)']} in wide vs {s['Max width (in)']} in max")
        if int(it["Depth (in)"]) > int(s["Max depth (in)"]):
            fails.append("TOO_DEEP"); why.append(f"{it['Depth (in)']} in deep vs {s['Max depth (in)']} in max")
        if s["Finish"] != "any" and it["Finish"] != s["Finish"]:
            fails.append("FINISH_MISMATCH"); why.append(f"{it['Finish']} vs {s['Finish']}")
        unclear = s["Fabric"] != "any" and it["Fabric"] == "not stated"
        if s["Fabric"] != "any" and not unclear and it["Fabric"] != s["Fabric"]:
            fails.append("FABRIC_MISMATCH"); why.append(f"{it['Fabric']} vs {s['Fabric']}")
        if fails:
            out["FAIL"][p["Line"]] = ",".join(fails); v = "FAIL"
        elif unclear:
            out["NEEDS_PERSON"].append(p["Line"]); v = "NEEDS_PERSON"; why.append(f"the listing doesn't state the fabric; the plan needs {s['Fabric']}")
        else:
            out["PASS"].append(p["Line"]); v = "PASS"
        md.append(f"| {p['Line']} | {s['Item']} | {p['SKU']} | {it['Width (in)']} x {it['Depth (in)']} | {it['Finish']} | {it['Fabric']} | {v} | "
                  + ("; ".join(why) or "meets the plan") + " |")
    md += ["", "NEEDS_PERSON items wait for a named person's decision, saved with their name. The assistant never passes an unclear item."]
    j = write(project, "approval.json", out)
    m = write(project, "approval.md", "\n".join(md) + "\n")
    log(project, "product_approval", f"{j}; {m}; pass {len(out['PASS'])}, fail {len(out['FAIL'])}, to a person {len(out['NEEDS_PERSON'])}",
        f"{len(out['FAIL'])} fail, {len(out['NEEDS_PERSON'])} to a person")
    print(json.dumps(out))


def change(project):
    once("change_request")
    f, lines, freight = purchase_order(project)
    po_path = pdir(project, "approved", "po-PQ-1042.md")
    before = hashlib.sha256(open(po_path, "rb").read()).hexdigest()
    po_total = sum(int(l["Qty"]) * dollars(l["Unit price"]) for l in lines.values()) + sum(freight.values())
    if po_total != dollars(f.get("Total")):
        raise Unreadable(f"the order's stated total {f.get('Total')} doesn't match its lines ({money(po_total)})")
    evs = sorted(glob.glob(pdir(project, "events", "*.md")))
    if not evs:
        raise Unreadable("no supplier notice in events/")
    ev = kv(text(evs[0]))
    old_sku, new_sku = ev["SKU"], ev["Proposed substitute"].split()[0]
    cat = load_catalog(project)
    old, new = lines[old_sku], cat[new_sku]
    qty = int(old["Qty"])
    delta = (dollars(new["Unit price"]) - dollars(old["Unit price"])) * qty
    new_total, budget = po_total + delta, dollars(f["Budget"])
    new_date = date(ev["Date"], "notice date") + dt.timedelta(days=int(new["Lead time (days)"]))
    appr = approvers(new_total)
    out = {"codes": ["OVER_BUDGET"] if new_total > budget else [], "old_sku": old_sku, "new_sku": new_sku, "delta": delta,
           "new_total": new_total, "budget": budget, "over_by": max(new_total - budget, 0), "old_date": old["Promised delivery"],
           "new_date": new_date.isoformat(), "approvers": appr, "baseline_changed": False,
           "_baseline_sha256_before": before}
    after = hashlib.sha256(open(po_path, "rb").read()).hexdigest()
    out["_baseline_sha256_after"] = after
    if after != before:
        raise Refused("the baseline changed during the change request; stopping")
    j = write(project, "change-request-CR-001.json", out)
    names = people()
    md = ["# Change request CR-001 (fictional): awaiting approval", "",
          f"Trigger: {ev['Supplier']} notice of {ev['Date']}: {old_sku} {ev['Notice']}.", "",
          "| | Approved baseline (PQ-1042) | Proposed change |", "|---|---|---|",
          f"| Item | {old['Item']} {old_sku} at {money(dollars(old['Unit price']))} | {new['Item']} {new_sku} at {money(dollars(new['Unit price']))} |",
          f"| Delivery | {old['Promised delivery']} | {new_date.isoformat()} |",
          f"| Project total | {money(po_total)} | {money(new_total)} ({'+' if delta >= 0 else ''}{money(delta)}) |",
          f"| Budget | {money(budget)} | {money(budget)} |", "",
          ("**OVER_BUDGET:** the change puts the project " + money(new_total - budget) + " over budget." if new_total > budget else "Within budget."),
          f"The substitute meets the plan's spec: {'yes' if meets(new, plan(project)[next(k for k, v in plan(project).items() if v['Item'] == new['Item'])]) else 'NO'}.", "",
          "Status: awaiting approval by " + " > ".join(f"{r} ({names.get(r, '?')})" for r in appr) + ".",
          "The approved baseline (approved/po-PQ-1042.md) stays exactly as it is until that approval is recorded. "
          f"Baseline SHA-256 before and after this request: {before[:16]}... = {after[:16]}...", "",
          "Approved by: ____________________   Date: __________"]
    m = write(project, "change-request-CR-001.md", "\n".join(md) + "\n")
    log(project, "change_request", f"{j}; {m}; {old_sku} -> {new_sku}; {'+' if delta >= 0 else ''}{money(delta)}; total {money(new_total)} vs budget {money(budget)}; "
        f"baseline unchanged", "awaiting approval")
    print(json.dumps({k: v for k, v in out.items() if not k.startswith('_')}))


def deliver(project):
    once("delivery_exceptions")
    req = request(project)
    install = date(req["Install by"], "Install by")
    f, lines, _ = purchase_order(project)
    trs = sorted(glob.glob(pdir(project, "deliveries", "tracking-*.md")))
    if not trs:
        raise Unreadable("no tracking file in deliveries/")
    t = text(trs[-1])
    as_of = date(kv(t)["As of"], "As of")
    exc, late, covered, tasks = {}, {}, [], []
    due = (as_of + dt.timedelta(days=PR["task_due_days"])).isoformat()
    for r in rows(t, "SKU"):
        if r["Status"] == PR["on_hold_status"]:
            covered.append(r["SKU"])
            continue
        codes, notes = [], []
        if r["ETA"] and date(r["ETA"], "ETA") > install:
            d = (date(r["ETA"], "ETA") - install).days
            codes.append("DELIVERY_LATE"); late[r["SKU"]] = d; notes.append(f"ETA {r['ETA']}, {d} days after the install date {install.isoformat()}")
        if r["Ship to"] != f["Ship to"]:
            codes.append("ADDRESS_MISMATCH"); notes.append(f"shipping to '{r['Ship to']}', the order says '{f['Ship to']}'")
        if codes:
            exc[r["SKU"]] = ",".join(codes)
            tasks.append((f"T{len(tasks) + 1}", r["SKU"], r["Supplier"], ", ".join(codes), "; ".join(notes)))
    out = {"exceptions": exc, "days_late": late, "covered_by_change": covered, "tasks": len(tasks),
           "task_owner": PR["exception_owner"], "task_due": due}
    j = write(project, "deliveries.json", out)
    names = people()
    owner = f"{PR['exception_owner']} ({names.get(PR['exception_owner'], '?')})"
    tm = ["# Follow-up tasks (fictional)", "", "| Task | SKU | Supplier | Exception | Detail | Owner | Due |", "|---|---|---|---|---|---|---|"]
    tm += [f"| {tid} | {sku} | {sup} | {codes} | {note} | {owner} | {due} |" for tid, sku, sup, codes, note in tasks]
    tm += ["", f"Covered by an open change request (not an exception here): {', '.join(covered) or 'none'}"]
    tk = write(project, "tasks.md", "\n".join(tm) + "\n")
    req_by = req.get("Requested by", "").split(",")[0]
    dm = [f"# Draft update to {req.get('Requested by')} ({req.get('Contact')}): not sent", "",
          f"Draft only. {owner} reviews and sends it; the assistant does not send email.", "",
          f"Hi {req_by.split()[0] if req_by else 'there'},", "",
          f"A quick update on Unit {req.get('Unit')}. As of {as_of.isoformat()}, most pieces are on track for {install.isoformat()}. Two need attention:"]
    dm += [f"- {sku}: {note}." for _, sku, _, _, note in tasks]
    dm += ["", "We're following up with both suppliers today and will confirm new dates by tomorrow.", "", "Thanks,", owner]
    d = write(project, f"drafts/update-{as_of.isoformat()}.md", "\n".join(dm) + "\n")
    log(project, "delivery_exceptions", f"{j}; {tk}; {d}; exceptions {', '.join(f'{k} {v}' for k, v in exc.items()) or 'none'}",
        f"{len(tasks)} tasks; update drafted, not sent")
    print(json.dumps(out))


def match(project):
    once("invoice_match")
    f, lines, freight = purchase_order(project)
    recs = sorted(glob.glob(pdir(project, "received", "receipt-*.md")))
    got = {r["SKU"]: int(r["Qty received"]) for p in recs for r in rows(text(p), "SKU")}
    inv, md = {}, ["# Three-way match: invoice vs. order PQ-1042 vs. receipt (fictional)", "",
                   "| Invoice | SKU | Billed | Ordered | Received | Flags |", "|---|---|---|---|---|---|"]
    for ip in sorted(glob.glob(pdir(project, "invoices", "*.md"))):
        t = text(ip)
        fi = kv(t)
        if fi.get("Payment status") != "unpaid":
            raise Refused(f"{rel(ip)} payment status is '{fi.get('Payment status')}'; the assistant only reviews unpaid invoices")
        sup = fi["Supplier"]
        codes, billed, expected = set(), 0, 0
        for l in rows(t, "SKU"):
            q, u = int(l["Qty"]), dollars(l["Unit price"])
            billed += q * u
            pl = lines.get(l["SKU"])
            if pl is None:
                codes.add("QTY_MISMATCH"); md.append(f"| {fi['Invoice number']} | {l['SKU']} | {q} x {money(u)} | not on the order | | QTY_MISMATCH |")
                continue
            line_codes = []
            if u != dollars(pl["Unit price"]):
                line_codes.append("PRICE_MISMATCH")
            rq = got.get(l["SKU"], 0)
            if rq == 0:
                line_codes.append("NOT_RECEIVED")
            if q > int(pl["Qty"]) or q > rq:
                line_codes.append("QTY_MISMATCH")
            codes.update(line_codes)
            expected += min(q, int(pl["Qty"]), rq) * dollars(pl["Unit price"])
            md.append(f"| {fi['Invoice number']} | {l['SKU']} | {q} x {money(u)} | {pl['Qty']} x {pl['Unit price']} | {rq} | {', '.join(line_codes) or 'ok'} |")
        fb = dollars(fi.get("Freight", "")) or 0
        billed += fb
        expected += freight.get(sup, 0)
        if fb != freight.get(sup, 0):
            codes.add("PRICE_MISMATCH")
        md.append(f"| {fi['Invoice number']} | freight | {money(fb)} | {money(freight.get(sup, 0))} | | {'ok' if fb == freight.get(sup, 0) else 'PRICE_MISMATCH'} |")
        e = {"result": "HOLD" if codes else "MATCH", "codes": sorted(codes)}
        if codes:
            e.update({"billed": billed, "expected": expected, "difference": billed - expected})
        inv[fi["Invoice number"]] = e
    names = people()
    out = {"invoices": inv, "payment_approver": PR["payment_approver"]}
    j = write(project, "match.json", out)
    md += ["", "| Invoice | Result | Billed | Should be | Difference |", "|---|---|---|---|---|"]
    md += [f"| {k} | {v['result']} | {money(v.get('billed', 0)) if 'billed' in v else 'as ordered'} | "
           f"{money(v['expected']) if 'expected' in v else ''} | {money(v['difference']) if 'difference' in v else ''} |" for k, v in inv.items()]
    md += ["", f"Payment is approved by {PR['payment_approver']} ({names.get(PR['payment_approver'], '?')}). "
           "The assistant flags differences and never marks an invoice paid."]
    m = write(project, "match.md", "\n".join(md) + "\n")
    log(project, "invoice_match", f"{j}; {m}; " + "; ".join(f"{k} {v['result']} {','.join(v['codes'])}".strip() for k, v in inv.items()),
        "flagged for Finance; payment status untouched")
    print(json.dumps(out))


# ------------------------------------------------------------- review + status ------------------------------------------------------
def manifest(paths):
    print("| Reviewed file | SHA-256 at review |\n|---|---|")
    for p in paths:
        a = os.path.join(ROOT, p) if not os.path.isabs(p) else p
        print(f"| `{rel(a)}` | {hashlib.sha256(open(a, 'rb').read()).hexdigest()} |")


def log_review(path):
    p = os.path.join(ROOT, path) if not os.path.isabs(path) else path
    t = text(p)
    found = sum(1 for r in rows(t, "Target") if r.get("Verdict", "").upper() == "FINDING")
    ok = sum(1 for r in rows(t, "Target") if r.get("Verdict", "").upper() == "OK")
    log("unit-4b", "checker_review", f"{rel(p)}; {ok} OK, {found} findings; recorded by {ME}", f"{found} findings", actor="compliance-checker")


def status(project):
    acts = [("scope_brief", "brief.json"), ("source_check", "source.json"), ("quote_compare", "quotes.json"),
            ("product_approval", "approval.json"), ("change_request", "change-request-CR-001.json"),
            ("delivery_exceptions", "deliveries.json"), ("invoice_match", "match.json")]
    print("| Activity | Done | Output |\n|---|---|---|")
    for a, f in acts:
        print(f"| {a} | {'yes' if logged(a) else 'no'} | {'out/' + f if os.path.exists(pdir(project, 'out', f)) else '-'} |")


def verify_log():
    good, n, ok = chain_ok()
    print(f"procurement log: {n} rows, {ok} of {n} chain links verify -> {'OK' if good else 'BROKEN'}")
    if not good:
        raise Refused("hash chain broken")


if __name__ == "__main__":
    acts = {"scope": scope, "source": source, "quote": quote, "approve": approve, "change": change, "deliver": deliver,
            "match": match, "status": status}
    a = sys.argv[1:]
    try:
        if a and a[0] in acts and len(a) == 2:
            acts[a[0]](a[1])
        elif a and a[0] == "manifest" and len(a) > 1:
            manifest(a[1:])
        elif a and a[0] == "log-review" and len(a) == 2:
            log_review(a[1])
        elif a == ["verify-log"]:
            verify_log()
        else:
            print(__doc__)
            sys.exit(1)
    except Unreadable as e:
        print(f"UNREADABLE - {e}. Stopping; nothing written.")
        sys.exit(2)
    except Refused as e:
        print(f"REFUSED - {e}")
        sys.exit(3)
