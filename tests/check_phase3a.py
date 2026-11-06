"""Phase 3a pass/fail check: the 7 buying activities for the fictional project unit-4b. Prints what it counted; exit 1 on any FAIL.

    python -I -X utf8 tests/check_phase3a.py             run the check
    python -I -X utf8 tests/check_phase3a.py --selftest  prove it can fail: one planted break per temp copy, each must FAIL its own check

Written before tools/project.py and the skills existed (11/5). It never imports the build: it parses the project files,
company/rules.json, and the locked answer key itself, and recomputes every activity its own way.
"""
import csv
import datetime as dt
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
COPY = "--copy" in sys.argv
NO_OLD = "--skip-old-phases" in sys.argv
ROOT = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.dirname(HERE)
PROJ = "projects/unit-4b"
OUT = PROJ + "/out"
LOG = "audit/procurement-log.csv"
CHAIN = "audit/procurement-log.chain.txt"
HEADER = "timestamp,actor,vendor,action,detail,result"
SKILLS = ["scope", "source", "quote", "approve", "change", "deliver", "match"]
ACTIONS = {"scope_brief": "procurement-assistant", "source_check": "procurement-assistant", "quote_compare": "procurement-assistant",
           "product_approval": "procurement-assistant", "change_request": "procurement-assistant",
           "delivery_exceptions": "procurement-assistant", "invoice_match": "procurement-assistant",
           "checker_review": "compliance-checker"}
PLANTED = "tests/checker-copies/unit-4b-match-copy.json"
NET_IMPORT = re.compile(r"^\s*(?:import|from)\s+(smtplib|socket|urllib|http|requests|ftplib|imaplib|poplib|aiohttp|httpx)\b", re.M)
results = []


def rec(ok, name, counted):
    results.append(bool(ok))
    print(f"{'PASS' if ok else 'FAIL'} - {name} - {counted}")


def path(*p):
    return os.path.join(ROOT, *[x for part in p for x in part.split("/")])


def read(rel):
    p = path(rel)
    return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def sha(rel):
    return hashlib.sha256(open(path(rel), "rb").read()).hexdigest() if os.path.exists(path(rel)) else None


def jload(rel):
    try:
        return json.load(open(path(rel), encoding="utf-8"))
    except (OSError, ValueError):
        return None


# ---------- my own parsers (not the build's) ----------
def fields(text):
    out = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Z][A-Za-z ,()/-]*?):[ \t]*(.*)$", line)
        if m and not line.startswith("|") and m.group(1) not in out:
            out[m.group(1).strip()] = m.group(2).strip()
    return out


def table(text, first):
    """Rows (dicts) of the first markdown table whose first header cell is `first`."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells and cells[0] == first:
            rows = []
            for r in lines[i + 2:]:
                if not r.startswith("|"):
                    break
                vals = [c.strip() for c in r.strip().strip("|").split("|")]
                rows.append(dict(zip(cells, vals + [""] * (len(cells) - len(vals)))))
            return rows
    return []


def usd(s):
    m = re.search(r"\$\s?([\d,]+)", s or "")
    return int(m.group(1).replace(",", "")) if m else None


def day(s):
    return dt.date.fromisoformat(s.strip())


def inches(s):
    m = re.match(r"\s*(\d+)\s*ft", s or "")
    return int(m.group(1)) * 12 if m else None


def rules():
    return json.load(open(path("company/rules.json"), encoding="utf-8"))


def tier(amount, r):
    for t in r["approval_tiers"]:
        if t["max_amount"] is None or amount <= t["max_amount"]:
            return t["approvers"]


def catalog():
    items = {}
    for p in sorted(glob.glob(path(PROJ, "catalogs", "*.md"))):
        text = open(p, encoding="utf-8").read()
        sup = fields(text).get("Supplier")
        for row in table(text, "SKU"):
            row["Supplier"] = sup
            items[row["SKU"]] = row
    return items


# ---------- recompute every activity from the inputs ----------
def recompute():
    r = rules()
    pr = r["projects"]
    req = fields(read(PROJ + "/request.md"))
    plan = {row["Line"]: row for row in table(read(PROJ + "/partner-plan.md"), "Line")}
    cat = catalog()
    start, install = day(req["Request date"]), day(req["Install by"])
    want = {}

    # 1 scope
    rooms = [x.strip() for x in req["Rooms"].split(",")]
    keys = [f"{room[0].upper()}{room[1:]} wall {w}" for room in rooms for w in ("A", "B")]
    missing = [k for k in keys if not req.get(k)]
    codes = ["MISSING_MEASUREMENT"] if missing else []
    bed = req.get("Bed size", "").lower()
    walls = [inches(req[k]) for k in keys if k.startswith("Bedroom") and req.get(k)]
    wall = min(walls) if walls else None
    need = pr["bed_widths_in"][bed] + 2 * pr["bed_side_clearance_in"]
    fits = [b for b, w in sorted(pr["bed_widths_in"].items(), key=lambda kv: kv[1]) if wall and w + 2 * pr["bed_side_clearance_in"] <= wall]
    if wall and need > wall:
        codes.append("SCOPE_CONFLICT")
    want["scope"] = {"status": "NEEDS_INFO" if codes else "READY", "codes": sorted(codes), "missing": missing,
                     "bed_requested": bed, "bed_needs_in": need, "wall_in": wall, "largest_bed_that_fits": fits[-1] if fits else None}

    # 2 source
    proposed = table(read(PROJ + "/proposed.md"), "Line")
    late, alt = {}, {}

    def meets(row, spec):
        ok = int(row["Width (in)"]) <= int(spec["Max width (in)"]) and int(row["Depth (in)"]) <= int(spec["Max depth (in)"])
        ok &= spec["Finish"] == "any" or row["Finish"] == spec["Finish"]
        ok &= spec["Fabric"] == "any" or row["Fabric"] == spec["Fabric"]
        return ok
    for p in proposed:
        it = cat[p["SKU"]]
        arrive = start + dt.timedelta(days=int(it["Lead time (days)"]))
        if arrive > install:
            late[p["SKU"]] = {"arrives": arrive.isoformat(), "days_late": (arrive - install).days}
            spec = plan[p["Line"]]
            options = [c for c in cat.values() if c["Item"] == it["Item"] and c["SKU"] != p["SKU"] and meets(c, spec)
                       and start + dt.timedelta(days=int(c["Lead time (days)"])) <= install]
            if options:
                alt[p["SKU"]] = min(options, key=lambda c: (usd(c["Unit price"]), c["SKU"]))["SKU"]
    want["source"] = {"items_checked": len(proposed), "late": late, "alternative": alt}

    # 3 quote
    quotes, total = {}, 0
    for qp in sorted(glob.glob(path(PROJ, "quotes", "*.md"))):
        text = open(qp, encoding="utf-8").read()
        f = fields(text)
        lines = table(text, "SKU")
        sub = sum(int(l["Qty"]) * usd(l["Unit price"]) for l in lines)
        qc = []
        if "Freight" in f:
            freight = usd(f["Freight"]) or 0
        else:
            notes = f.get("Notes", "")
            hidden = usd(notes) if any(w in notes.lower() for w in pr["hidden_freight_words"]) else None
            freight = hidden or 0
            if hidden:
                qc.append("HIDDEN_FREIGHT")
        if day(f["Valid until"]) < day(r["demo_date"]):
            qc.append("QUOTE_EXPIRED")
        quotes[f["Quote number"]] = {"subtotal": sub, "freight": freight, "total": sub + freight, "codes": sorted(qc)}
        total += sub + freight
    want["quote"] = {"quotes": quotes, "total": total, "approvers": tier(total, r)}

    # 4 approve
    verdict = {"PASS": [], "FAIL": {}, "NEEDS_PERSON": []}
    for p in proposed:
        it, spec = cat[p["SKU"]], plan[p["Line"]]
        fails = []
        if int(it["Width (in)"]) > int(spec["Max width (in)"]):
            fails.append("TOO_WIDE")
        if int(it["Depth (in)"]) > int(spec["Max depth (in)"]):
            fails.append("TOO_DEEP")
        if spec["Finish"] != "any" and it["Finish"] != spec["Finish"]:
            fails.append("FINISH_MISMATCH")
        unclear = spec["Fabric"] != "any" and it["Fabric"] == "not stated"
        if spec["Fabric"] != "any" and not unclear and it["Fabric"] != spec["Fabric"]:
            fails.append("FABRIC_MISMATCH")
        if fails:
            verdict["FAIL"][p["Line"]] = ",".join(fails)
        elif unclear:
            verdict["NEEDS_PERSON"].append(p["Line"])
        else:
            verdict["PASS"].append(p["Line"])
    want["approve"] = verdict

    # 5 change
    po_text = read(PROJ + "/approved/po-PQ-1042.md")
    po = fields(po_text)
    po_lines = {l["SKU"]: l for l in table(po_text, "SKU")}
    freight = {k[len("Freight "):]: usd(v) for k, v in po.items() if k.startswith("Freight ")}
    po_total = sum(int(l["Qty"]) * usd(l["Unit price"]) for l in po_lines.values()) + sum(freight.values())
    ev = fields(read(PROJ + "/events/2026-11-07-backorder.md"))
    old_sku = ev["SKU"]
    new_sku = ev["Proposed substitute"].split()[0]
    old_line, new_item = po_lines[old_sku], cat[new_sku]
    delta = (usd(new_item["Unit price"]) - usd(old_line["Unit price"])) * int(old_line["Qty"])
    new_total = po_total + delta
    budget = usd(po["Budget"])
    want["change"] = {"codes": ["OVER_BUDGET"] if new_total > budget else [], "old_sku": old_sku, "new_sku": new_sku, "delta": delta,
                      "new_total": new_total, "budget": budget, "over_by": max(new_total - budget, 0),
                      "old_date": old_line["Promised delivery"],
                      "new_date": (day(ev["Date"]) + dt.timedelta(days=int(new_item["Lead time (days)"]))).isoformat(),
                      "approvers": tier(new_total, r), "baseline_changed": False, "_po_total": po_total, "_po_stated": usd(po["Total"])}

    # 6 deliver
    tr_text = read(PROJ + "/deliveries/tracking-2026-11-12.md")
    as_of = day(fields(tr_text)["As of"])
    exc, late_days, covered = {}, {}, []
    for row in table(tr_text, "SKU"):
        if row["Status"] == pr["on_hold_status"]:
            covered.append(row["SKU"])
            continue
        codes6 = []
        if row["ETA"] and day(row["ETA"]) > install:
            codes6.append("DELIVERY_LATE")
            late_days[row["SKU"]] = (day(row["ETA"]) - install).days
        if row["Ship to"] != po["Ship to"]:
            codes6.append("ADDRESS_MISMATCH")
        if codes6:
            exc[row["SKU"]] = ",".join(codes6)
    want["deliver"] = {"exceptions": exc, "days_late": late_days, "covered_by_change": covered, "tasks": len(exc),
                       "task_owner": pr["exception_owner"], "task_due": (as_of + dt.timedelta(days=pr["task_due_days"])).isoformat()}

    # 7 match
    got = {row["SKU"]: int(row["Qty received"]) for row in table(read(PROJ + "/received/receipt-2026-11-12.md"), "SKU")}
    inv = {}
    for ip in sorted(glob.glob(path(PROJ, "invoices", "*.md"))):
        text = open(ip, encoding="utf-8").read()
        f = fields(text)
        sup = f["Supplier"]
        codes7, billed, expected = set(), 0, 0
        for l in table(text, "SKU"):
            q, u = int(l["Qty"]), usd(l["Unit price"])
            billed += q * u
            pl = po_lines.get(l["SKU"])
            if pl is None:
                codes7.add("QTY_MISMATCH")
                continue
            if u != usd(pl["Unit price"]):
                codes7.add("PRICE_MISMATCH")
            rq = got.get(l["SKU"], 0)
            if rq == 0:
                codes7.add("NOT_RECEIVED")
            if q > int(pl["Qty"]) or q > rq:
                codes7.add("QTY_MISMATCH")
            expected += min(q, int(pl["Qty"]), rq) * usd(pl["Unit price"])
        fb = usd(f.get("Freight", "")) or 0
        billed += fb
        expected += freight.get(sup, 0)
        if fb != freight.get(sup, 0):
            codes7.add("PRICE_MISMATCH")
        entry = {"result": "HOLD" if codes7 else "MATCH", "codes": sorted(codes7)}
        if codes7:
            entry.update({"billed": billed, "expected": expected, "difference": billed - expected})
        inv[f["Invoice number"]] = entry
    want["match"] = {"invoices": inv, "payment_approver": pr["payment_approver"]}
    return want


def strip(d):
    """The answer key without its notes ('why', '_note') and the recompute's private fields."""
    if isinstance(d, dict):
        return {k: strip(v) for k, v in d.items() if k not in ("why", "_note") and not k.startswith("_")}
    return d


def lock_line(name):
    for line in read("tests/LOCK.txt").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] == name:
            return parts[0]
    return None


# ---------- the checks ----------
def run():
    key = jload("tests/answer-key-3a.json") or {}
    q0 = lock_line("answer-key-3a.json") == sha("tests/answer-key-3a.json")
    rec(q0, "Q0 answer key unchanged since it was locked", f"lock {(lock_line('answer-key-3a.json') or 'missing')[:12]}..., now {(sha('tests/answer-key-3a.json') or 'missing')[:12]}...")
    try:
        want = recompute()
        err = ""
    except Exception as e:  # a broken input file is a FAIL, not a crash
        want, err = {}, repr(e)
    diff = [k for k in ("scope", "source", "quote", "approve", "change", "deliver", "match") if strip(want.get(k)) != strip(key.get(k))]
    po_ok = want.get("change", {}).get("_po_total") == want.get("change", {}).get("_po_stated")
    rec(not diff and not err and po_ok and want, "Q0b recomputed from the inputs = answer key (the data really has the planted problems)",
        f"7 activities recomputed; differ from key {diff}; PO total recomputed {want.get('change', {}).get('_po_total')} vs stated "
        f"{want.get('change', {}).get('_po_stated')}; error {err or 'none'}")

    def out_eq(n, label, rel, extra_ok=True, extra=""):
        got = jload(rel)
        ok = got is not None and strip(got) == strip(key.get(label)) and extra_ok
        rec(ok, n, f"{rel}: {'missing' if got is None else ('= key' if strip(got) == strip(key.get(label)) else 'differs: ' + json.dumps(strip(got))[:260])}{extra}")

    # Q1 scope
    b = jload(OUT + "/brief.json") or {}
    md = read(OUT + "/brief.md")
    req = fields(read(PROJ + "/request.md"))
    listed = [k for k in req if k in md]
    invented = (b.get("_measurements") or {}).get("Bedroom wall B") not in (None, "")
    out_eq("Q1 /scope: brief = key; every request field in brief.md; nothing invented", "scope", OUT + "/brief.json",
           len(listed) == len(req) and not invented and "_measurements" in b,
           f"; {len(listed)} of {len(req)} request fields in brief.md; invented measurement {invented}")
    # Q2 source
    out_eq("Q2 /source: late items and the in-time alternative = key", "source", OUT + "/source.json")
    # Q3 quote
    prd = read(OUT + "/purchase-request-draft.md")
    pr_ok = all(s in prd for s in ("DRAFT", "not an order", "$4,898", "Facilities Manager")) and "Approved by: ____" in prd
    out_eq("Q3 /quote: comparison = key; purchase request is a draft for a person", "quote", OUT + "/quotes.json", pr_ok,
           f"; draft has DRAFT / not an order / $4,898 / approver / blank sign-off: {pr_ok}")
    # Q4 approve
    a4 = jload(OUT + "/approval.json") or {}
    person_passed = set(a4.get("NEEDS_PERSON", [])) & set(a4.get("PASS", []))
    clean_failed = set(key.get("approve", {}).get("PASS", [])) & set(a4.get("FAIL", {}))
    out_eq("Q4 /approve: verdicts = key; unclear items go to a person; 0 clean items failed", "approve", OUT + "/approval.json",
           not person_passed and not clean_failed, f"; unclear passed {sorted(person_passed)}; clean failed {sorted(clean_failed)}")
    # Q5 change
    base_ok = lock_line("projects/unit-4b/approved/po-PQ-1042.md") == sha(PROJ + "/approved/po-PQ-1042.md")
    rows = log_rows()
    approved = [r for r in rows if len(r) == 6 and r[3] in ("baseline_update", "change_approved")]
    crmd = read(OUT + "/change-request-CR-001.md")
    out_eq("Q5 /change: change request = key; baseline unchanged; no approval taken by the AI", "change", OUT + "/change-request-CR-001.json",
           base_ok and not approved and "awaiting" in crmd.lower(),
           f"; baseline hash = lock {base_ok}; approval rows {len(approved)}; request says awaiting approval {'awaiting' in crmd.lower()}")
    # Q6 deliver
    tasks = [l for l in read(OUT + "/tasks.md").splitlines() if re.match(r"^\| T\d+ \|", l)]
    tasks_ok = len(tasks) == key.get("deliver", {}).get("tasks") and all("Facilities Manager" in t and "2026-11-13" in t for t in tasks)
    drafts = glob.glob(path(OUT, "drafts", "*.md"))
    draft_ok = len(drafts) == 1 and all("not sent" in open(d, encoding="utf-8").read().lower() for d in drafts)
    sent = [r for r in rows if len(r) == 6 and ("sent" in r[5].lower().replace("not sent", "") or "send" in r[3].lower())]
    out_eq("Q6 /deliver: exceptions = key; tasks have an owner and a date; update drafted, 0 sent", "deliver", OUT + "/deliveries.json",
           tasks_ok and draft_ok and not sent, f"; {len(tasks)} task rows ok {tasks_ok}; {len(drafts)} draft(s) marked not sent {draft_ok}; sent rows {len(sent)}")
    # Q7 match
    statuses = {os.path.basename(p): fields(open(p, encoding="utf-8").read()).get("Payment status")
                for p in glob.glob(path(PROJ, "invoices", "*.md"))}
    paid = [k for k, v in statuses.items() if v != "unpaid"]
    paid_rows = [r for r in rows if len(r) == 6 and re.search(r"\bpaid\b", r[5].lower().replace("unpaid", ""))]
    out_eq("Q7 /match: three-way match = key; 0 invoices marked paid by the AI", "match", OUT + "/match.json",
           not paid and not paid_rows and len(statuses) == 2, f"; payment status {statuses}; paid rows {len(paid_rows)}")

    # Q8 the procurement audit log
    probs = []
    raw = read(LOG)
    lines = raw.rstrip("\n").split("\n") if raw else []
    if not lines or lines[0] != HEADER:
        probs.append("header missing or wrong")
    links = read(CHAIN).split()
    h, good = hashlib.sha256(HEADER.encode()).hexdigest(), 0
    for i, line in enumerate(lines[1:]):
        h = hashlib.sha256((h + "\n" + line).encode("utf-8")).hexdigest()
        good += i < len(links) and links[i] == h
    n = len(lines) - 1 if lines else 0
    if not (good == n == len(links)):
        probs.append(f"chain {good} of {n} rows verify, {len(links)} links")
    counts = {}
    for r in rows:
        if len(r) != 6 or r[3] not in ACTIONS:
            probs.append(f"unknown row {r[:4]}")
            continue
        if r[1] != ACTIONS[r[3]]:
            probs.append(f"{r[3]} by {r[1]}")
        counts[r[3]] = counts.get(r[3], 0) + 1
    missing = [a for a in ACTIONS if counts.get(a, 0) < 1]
    doubles = [a for a, c in counts.items() if a != "checker_review" and c > 1]
    net = [os.path.basename(p) for p in glob.glob(path("tools", "*.py")) if NET_IMPORT.search(open(p, encoding="utf-8").read())]
    rec(not probs and not missing and not doubles and not net and n >= 8, "Q8 procurement log: 1 row per action, right actors, hash chain verifies",
        f"{n} rows; actions {counts}; missing {missing}; repeated {doubles}; network imports {net}; problems {probs[:4]}")

    # Q9 skills + CLAUDE.md section 10
    probs = []
    for s in SKILLS:
        t = read(f".claude/skills/{s}/SKILL.md")
        fm = t.split("---")[1] if t.startswith("---") and t.count("---") >= 2 else ""
        meta = dict(re.findall(r"^(\w[\w-]*):\s*(.*)$", fm, re.M))
        if meta.get("name") != s or not meta.get("description"):
            probs.append(f"{s}: front matter")
    cm = read("CLAUDE.md")
    pr = rules()["projects"]
    need = [f"**{pr['bed_side_clearance_in']} in**", f"**{pr['walkway_min_in']} in**", f"**{pr['task_due_days']} day**",
            pr["exception_owner"], pr["payment_approver"], "procurement-log.csv", "Drafts only", "## 10."]
    need += [f"{b} {w} in" for b, w in pr["bed_widths_in"].items()]
    need += sorted(pr["issue_codes"])
    absent = [x for x in need if x not in cm]
    rec(not probs and not absent, "Q9 7 skills with front matter; CLAUDE.md section 10 states every Phase 3a rule",
        f"{len(SKILLS) - len(probs)} of {len(SKILLS)} skills ok {probs}; {len(need) - len(absent)} of {len(need)} rules found; missing {absent}")

    # Q10 the older phases still pass
    if NO_OLD:
        rec(True, "Q10 Phases 1 and 2 still pass (skipped by --skip-old-phases in self-test copies)", "skipped")
    else:
        cmd = [sys.executable, "-I", "-X", "utf8", path("tests/check_phase2.py")] + (["--copy"] if COPY else [])
        r2 = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT, timeout=900)
        last = [l for l in r2.stdout.splitlines() if l.startswith("RESULT")]
        rec(r2.returncode == 0 and last and "8 of 8" in last[-1], "Q10 Phases 1 and 2 still pass (Phase 2's P6 reruns Phase 1 + its privacy scan)",
            f"check_phase2: {last[-1] if last else 'no result'}, exit {r2.returncode}")

    # Q11 the blind checker review
    probs = []
    revs = sorted(glob.glob(path("reviews", "procurement", "*.md")))
    pj = jload(PLANTED)
    if not pj or pj.get("invoices", {}).get("INV-KC-3307", {}).get("result") != "MATCH":
        probs.append("planted copy missing or not wrong")
    caught, real_ok, stale = False, 0, []
    real_outs = sorted(os.path.relpath(p, ROOT).replace("\\", "/") for p in glob.glob(path(OUT, "*.json")))
    if revs:
        rv = open(revs[-1], encoding="utf-8").read()
        man = {r["Reviewed file"].strip("`"): r["SHA-256 at review"] for r in table(rv, "Reviewed file")}
        stale = [p for p, hh in man.items() if sha(p) != hh]
        ver = {}
        for r in table(rv, "Target"):
            ver.setdefault(r["Target"].strip("`"), []).append(r)
        caught = any(r.get("Verdict", "").upper() == "FINDING" and "INV-KC-3307" in " ".join(r.values()) for r in ver.get(PLANTED, []))
        real_ok = sum(1 for p in real_outs if ver.get(p) and all(r.get("Verdict", "").upper() == "OK" for r in ver[p]))
        if [p for p in real_outs + [PLANTED] if p not in man]:
            probs.append("not every file is in the manifest")
    else:
        probs.append("no review in reviews/procurement/")
    rec(not probs and caught and real_ok == len(real_outs) == 7 and not stale,
        "Q11 blind checker review caught the planted miss and passed the real outputs",
        f"latest review {os.path.basename(revs[-1]) if revs else 'none'}; planted KC-as-MATCH caught {caught}; {real_ok} of {len(real_outs)} real outputs OK; "
        f"stale {stale}; problems {probs}")

    # Q12 README covers Phase 3a, no overclaims
    rd = read("README.md")
    pieces = ["`tools/make_project.py`", "`tools/project.py`", "`tests/check_phase3a.py`", "`audit/procurement-log.csv`",
              "`projects/unit-4b/`"] + [f"`/{s}` skill" for s in SKILLS]
    mapped = [p for p in pieces if any(l.startswith("| " + p) and "Designed and directed" in l for l in rd.splitlines())]
    status = re.search(r"^\| 3a \|.*Built", rd, re.M) is not None
    label = pr["partner_label"] in rd
    over = re.findall(r"(?i)\b(I coded|I wrote the code|I programmed)\b", rd)
    rec(len(mapped) == len(pieces) and status and label and not over, "Q12 README: Phase 3a status, every new piece mapped, partner label, no overclaims",
        f"{len(mapped)} of {len(pieces)} pieces mapped; status row {status}; label {label}; overclaims {over}")

    print(f"\nRESULT: {sum(results)} of {len(results)} checks PASS")
    return all(results)


def log_rows():
    raw = read(LOG)
    return list(csv.reader(raw.splitlines()[1:])) if raw else []


# ---------- self-test ----------
def selftest():
    breaks = [
        ("Q0", "the answer key edited after locking", "tests/answer-key-3a.json", '"over_by": 108', '"over_by": 100'),
        ("Q0b", "an input changed so the data no longer has its planted problem", "projects/unit-4b/invoices/INV-KC-3307.md", "| 3 | $139 | $417 |", "| 2 | $129 | $258 |"),
        ("Q1", "the brief marked READY", "projects/unit-4b/out/brief.json", '"NEEDS_INFO"', '"READY"'),
        ("Q2", "the late sofa dropped", "projects/unit-4b/out/source.json", '"days_late": 27', '"days_late": 0'),
        ("Q3", "a quote total changed", "projects/unit-4b/out/quotes.json", '"total": 4898', '"total": 4713'),
        ("Q4", "the unclear chair passed", "projects/unit-4b/out/approval.json", '"NEEDS_PERSON": [\n    "5"\n  ]', '"NEEDS_PERSON": []'),
        ("Q5", "the baseline edited before approval", "projects/unit-4b/approved/po-PQ-1042.md", "Total: $4,898", "Total: $5,308"),
        ("Q6", "a task row deleted", "projects/unit-4b/out/tasks.md", "| T2 |", "| X2 |"),
        ("Q7", "an invoice marked paid", "projects/unit-4b/invoices/INV-GW-5521.md", "Payment status: unpaid", "Payment status: paid"),
        ("Q8", "a past audit row edited", "audit/procurement-log.csv", "procurement-assistant", "procurement-assistant "),
        ("Q9", "a skill's front matter broken", ".claude/skills/match/SKILL.md", "name: match", "name: matcher"),
        ("Q11", "the planted copy marked OK in the review", None, None, None),
        ("Q12", "the README status row removed", "README.md", "| 3a |", "| 3x |"),
    ]
    ok_all = True
    for check, name, rel, old, new in breaks:
        tmp = tempfile.mkdtemp()
        cp = os.path.join(tmp, "Onboarding-Demo")
        shutil.copytree(ROOT, cp, ignore=shutil.ignore_patterns("__pycache__"))
        try:
            if rel is None:  # Q11: flip the planted copy's verdict in the latest review
                rv = sorted(glob.glob(os.path.join(cp, "reviews", "procurement", "*.md")))[-1]
                t = open(rv, encoding="utf-8").read()
                t2 = re.sub(r"(\| `?" + re.escape(PLANTED) + r"`? \| )FINDING", r"\1OK", t)
                planted_ok = t2 != t
                open(rv, "w", encoding="utf-8").write(t2)
            else:
                p = os.path.join(cp, *rel.split("/"))
                t = open(p, encoding="utf-8").read()
                planted_ok = old in t
                open(p, "w", encoding="utf-8").write(t.replace(old, new, 1))
            r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(cp, "tests", "check_phase3a.py"), "--root", cp, "--copy", "--skip-old-phases"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
            flagged = [l.split(" - ")[1].split(" ")[0] for l in r.stdout.splitlines() if l.startswith("FAIL - ")]
            ok = planted_ok and check in flagged and r.returncode == 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        ok_all &= ok
        print(f"{'PASS' if ok else 'FAIL'} - selftest: {name} makes {check} FAIL - planted {planted_ok}; flagged {flagged}")
    n = len(breaks)
    print(f"\nSELF-TEST: {'all' if ok_all else 'NOT all'} {n} planted breaks caught by their own check")
    return ok_all


if __name__ == "__main__":
    good = run()
    if "--selftest" in sys.argv:
        print("\nSelf-test (can the check fail?)")
        good = selftest() and good
    sys.exit(0 if good else 1)
