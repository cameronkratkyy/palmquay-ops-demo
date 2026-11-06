"""Helpers the onboarding skills call where a script is more reliable than reading by eye: dates, dollar minimums,
approver order, file hashes, and the append-only audit log. Fake data only. Nothing here sends, approves, signs or pays,
and nothing here opens a network connection.

    python -I -X utf8 tools/onboard.py intake <slug>        /intake: read documents, apply company/rules.json, write intake.json, set Stage, log 1 row
    python -I -X utf8 tools/onboard.py facts <slug>         /chase: print the facts a follow-up email needs (read-only)
    python -I -X utf8 tools/onboard.py lint-draft <path>    /chase: check a draft against CLAUDE.md section 7 (read-only)
    python -I -X utf8 tools/onboard.py log-draft <path>     /chase: lint again, set Stage, log 1 row (chase_draft)
    python -I -X utf8 tools/onboard.py packet <slug>        /route: READY vendors only; write packet.md, set Stage, log 1 row
    python -I -X utf8 tools/onboard.py manifest <files...>  checker review: print the SHA-256 table the review record keeps (read-only)
    python -I -X utf8 tools/onboard.py log-review <path>    checker review: log 1 row for a saved review record
    python -I -X utf8 tools/onboard.py status               /status: one line per vendor (read-only)
    python -I -X utf8 tools/onboard.py verify-audit         recompute the audit log's hash chain (read-only)

Exit codes: 0 ok, 2 a document is unreadable (stop for that vendor), 3 refused (already done, not READY, lint failed).
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
TODAY = dt.date.fromisoformat(RULES["demo_date"])
DEADLINE = (TODAY + dt.timedelta(days=RULES["chase_deadline_days"])).isoformat()
AUDIT = os.path.join(ROOT, "audit", "audit-log.csv")
CHAIN = os.path.join(ROOT, "audit", "audit-log.chain.txt")
HEADER = "timestamp,actor,vendor,action,detail,result"
ME = "onboarding-assistant"
THREATS = re.compile(r"\b(legal action|lawsuits?|sue|suing|attorneys?|lawyers?|litigation|court|breach\w*|penalt\w*|liable|"
                     r"damages|terminat\w*|demand\w*|final notice|or else|consequences|failure to comply)\b", re.I)
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
MONEY = re.compile(r"\$\d[\d,]*")


class Refused(Exception):
    pass


class Unreadable(Exception):
    pass


# ------------------------------------------------------------- reading -------------------------------------------------------------
def fields(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        m = re.match(r"\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", line)
        if m and m.group(1) not in ("Field", "---"):
            out[m.group(1)] = m.group(2)
    return out


def usd(s):
    s = (s or "").replace("$", "").replace(",", "").strip()
    return int(s) if s.isdigit() else None


def money(n):
    return f"${n:,}"


def vdir(slug):
    p = os.path.join(ROOT, "vendors", slug)
    if not os.path.isfile(os.path.join(p, "vendor.md")):
        raise Refused(f"no vendor record at vendors/{slug}/vendor.md")
    return p


def load(slug):
    """(vendor record, {doc: fields}) for one vendor. Raises Unreadable if a present document lacks a field we need."""
    vd = vdir(slug)
    v = fields(os.path.join(vd, "vendor.md"))
    dd = os.path.join(vd, "documents")
    d = {f[:-3]: fields(os.path.join(dd, f)) for f in sorted(os.listdir(dd)) if f.endswith(".md")} if os.path.isdir(dd) else {}
    need = {"w9": ["Legal name"], "request": ["Contract amount", "Building", "Scope"],
            "coi": ["Insured", "Additional insured", "General liability per occurrence", "General liability aggregate",
                    "Auto liability", "Workers' comp", "Policy end"],
            "license": ["License holder", "Expires"]}
    for k in ("Legal name", "Trade", "Contact email", "Submitted"):
        if not v.get(k):
            raise Unreadable(f"vendor.md has no '{k}'")
    for doc, keys in need.items():
        for k in keys:
            if doc in d and not d[doc].get(k):
                raise Unreadable(f"{doc}.md has no '{k}'")
    try:
        if "coi" in d:
            dt.date.fromisoformat(d["coi"]["Policy end"])
        if "license" in d:
            dt.date.fromisoformat(d["license"]["Expires"])
    except ValueError as e:
        raise Unreadable(f"a date can't be read: {e}")
    if "request" in d and usd(d["request"]["Contract amount"]) is None:
        raise Unreadable(f"request.md amount '{d['request']['Contract amount']}' can't be read")
    return v, d


def tier(amount):
    for t in RULES["approval_tiers"]:
        if amount is not None and (t["max_amount"] is None or amount <= t["max_amount"]):
            return t
    return None


def tier_label(t):
    tiers = RULES["approval_tiers"]
    i = tiers.index(t)
    if t["max_amount"] is not None:
        return f"Up to {money(t['max_amount'])}"
    return f"Over {money(tiers[i - 1]['max_amount'])}"


def people():
    out = {}
    roles = {r for t in RULES["approval_tiers"] for r in t["approvers"]}
    for line in open(os.path.join(ROOT, "company", "people.md"), encoding="utf-8"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        for role in roles:
            if cells and (cells[0] == role or cells[0].startswith(role + " (")):
                out[role] = {"name": cells[1], "email": cells[3]}
    return out


def intake_json(slug):
    p = os.path.join(vdir(slug), "intake.json")
    if not os.path.exists(p):
        raise Refused(f"{slug} has no intake.json yet; run /intake first")
    return json.load(open(p, encoding="utf-8"))


def relpath(p):
    return os.path.relpath(os.path.abspath(p), ROOT).replace("\\", "/")


# ------------------------------------------------------------- writing -------------------------------------------------------------
def now():
    return dt.datetime.now().isoformat(timespec="seconds")


def chain_ok():
    """(ok, rows, links): recompute the hash chain over every row in the audit log."""
    raw = open(AUDIT, encoding="utf-8", newline="").read()
    lines = raw.rstrip("\n").split("\n")
    if lines[0].rstrip("\r") != HEADER:
        return False, 0, 0
    links = open(CHAIN, encoding="utf-8").read().split() if os.path.exists(CHAIN) else []
    h, ok = hashlib.sha256(HEADER.encode()).hexdigest(), 0
    for i, line in enumerate(lines[1:]):
        h = hashlib.sha256((h + "\n" + line.rstrip("\r")).encode("utf-8")).hexdigest()
        ok += i < len(links) and links[i] == h
    rows = len(lines) - 1
    return ok == rows == len(links), rows, ok


def audit(vendor, action, detail, result, actor=ME):
    """Append exactly one row (and its chain link). Never rewrites a past row; refuses if the chain is already broken."""
    good, rows, _ = chain_ok()
    if not good:
        raise Refused("audit log hash chain doesn't verify; not appending (run verify-audit)")
    ts = now()
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerow([ts, actor, vendor, action, detail, result])
    line = buf.getvalue().rstrip("\n")
    links = open(CHAIN, encoding="utf-8").read().split() if os.path.exists(CHAIN) else []
    prev = links[-1] if links else hashlib.sha256(HEADER.encode()).hexdigest()
    with open(AUDIT, "a", encoding="utf-8", newline="") as f:
        f.write(line + "\n")
    with open(CHAIN, "a", encoding="utf-8", newline="") as f:
        f.write(hashlib.sha256((prev + "\n" + line).encode("utf-8")).hexdigest() + "\n")
    print(f"audit row {rows + 1}: {line}")
    return ts


def set_stage(slug, value, when):
    """Replace the Stage line in vendor.md and keep the old value in a Stage history list (nothing is lost)."""
    p = os.path.join(vdir(slug), "vendor.md")
    text = open(p, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in text else "\n"
    m = re.search(r"^\| Stage \| (.*?) \|\s*$", text, re.M)
    if not m:
        raise Unreadable("vendor.md has no Stage line")
    old = m.group(1)
    text = text[:m.start(1)] + value + text[m.end(1):]
    if "## Stage history" not in text:
        submitted = fields(p).get("Submitted", "?")
        text = text.rstrip("\r\n") + f"{nl}{nl}## Stage history{nl}{nl}- {submitted}: {old}{nl}"
    text = text.rstrip("\r\n") + f"{nl}- {when}: {value}{nl}"
    open(p, "w", encoding="utf-8", newline="").write(text)


# ------------------------------------------------------------- /intake -------------------------------------------------------------
def intake(slug):
    vd = vdir(slug)
    out = os.path.join(vd, "intake.json")
    if os.path.exists(out):
        raise Refused(f"vendors/{slug}/intake.json already exists; not redone (audit rows are append-only)")
    v, d = load(slug)
    trade, mins = v["Trade"], RULES["insurance_minimums"]
    ev, issues = [], []

    def check(name, source, found, rule, code=None):
        ev.append({"check": name, "source": source, "found": found, "rule": rule, "result": code or "ok"})
        if code:
            issues.append(code)

    for doc, code, label in (("w9", "MISSING_W9", "W-9"), ("coi", "MISSING_COI", "certificate of insurance"),
                             ("request", "MISSING_REQUEST", "work request")):
        check(f"{label} on file", f"documents/{doc}.md", "present" if doc in d else "missing", "required from every vendor",
              None if doc in d else code)
    if trade in RULES["required_documents"]["licensed_trades"]:
        check("state license on file", "documents/license.md", "present" if "license" in d else "missing",
              f"required for licensed trades ({trade})", None if "license" in d else "MISSING_LICENSE")
    else:
        ev.append({"check": "state license on file", "source": "vendor.md: Trade", "found": trade,
                   "rule": "not required for this trade under company policy", "result": "n/a"})

    win = RULES["expiring_window_days"]

    def expiry(name, source, end, expired, expiring):
        days = (end - TODAY).days
        found = f"{end} ({-days} days ago)" if days < 0 else f"{end} ({days} days from {TODAY})"
        rule = f"not before {TODAY}; {win} days or fewer out = hold"
        check(name, source, found, rule, expired if days < 0 else expiring if days <= win else None)

    if "coi" in d:
        c = d["coi"]
        expiry("insurance end date", "documents/coi.md: Policy end", dt.date.fromisoformat(c["Policy end"]),
               "COI_EXPIRED", "COI_EXPIRING_30D")
        occ, agg = usd(c["General liability per occurrence"]), usd(c["General liability aggregate"])
        low = occ is None or agg is None or occ < mins["gl_per_occurrence"] or agg < mins["gl_aggregate"]
        check("general liability", "documents/coi.md", f"{c['General liability per occurrence']} / {c['General liability aggregate']}",
              f"at least {money(mins['gl_per_occurrence'])} per occurrence / {money(mins['gl_aggregate'])} aggregate",
              "GL_BELOW_MIN" if low else None)
        auto = usd(c["Auto liability"])
        check("auto liability", "documents/coi.md", c["Auto liability"], f"at least {money(mins['auto_liability'])}",
              "AUTO_BELOW_MIN" if auto is None or auto < mins["auto_liability"] else None)
        if trade in mins["high_risk_trades"]:
            um = usd(c.get("Umbrella"))
            check("umbrella", "documents/coi.md", c.get("Umbrella") or "missing",
                  f"at least {money(mins['umbrella_high_risk'])} for {trade} (high-risk trade)",
                  "UMBRELLA_MISSING" if um is None or um < mins["umbrella_high_risk"] else None)
        else:
            ev.append({"check": "umbrella", "source": "documents/coi.md", "found": c.get("Umbrella") or "missing",
                       "rule": f"not required for {trade}", "result": "n/a"})
        wc = c["Workers' comp"]
        check("workers' comp", "documents/coi.md", wc, mins["workers_comp"],
              None if wc.strip().lower() == "statutory" or "exempt" in wc.lower() else "WC_MISSING")
        ai = c["Additional insured"]
        check("additional insured", "documents/coi.md", ai, f"must name {mins['additional_insured']}",
              None if ai.strip() == mins["additional_insured"] else "NO_ADDITIONAL_INSURED")
    if "license" in d:
        expiry("license end date", "documents/license.md: Expires", dt.date.fromisoformat(d["license"]["Expires"]),
               "LICENSE_EXPIRED", "LICENSE_EXPIRING_30D")
    names = {"vendor.md": v["Legal name"]}
    for doc, key in (("w9", "Legal name"), ("coi", "Insured"), ("license", "License holder")):
        if doc in d:
            names[f"{doc}.md"] = d[doc][key]
    check("legal name matches everywhere", ", ".join(names), "; ".join(f"{k}: {n}" for k, n in names.items()),
          "same legal name on the vendor record, W-9, certificate and license",
          "NAME_MISMATCH" if len(set(names.values())) > 1 else None)

    issues = sorted(set(issues))
    codes = RULES["issue_codes"]
    status = "READY" if not issues else "HOLD" if all(codes[i] == "HOLD" for i in issues) else "BLOCKED"
    amount = usd(d["request"]["Contract amount"]) if "request" in d else None
    t = tier(amount)
    approvers = t["approvers"] if t else []
    ts = now()
    result = {
        "vendor": slug, "legal_name": v["Legal name"], "trade": trade, "demo_date": RULES["demo_date"],
        "documents": sorted(d), "issues": issues, "status": status, "approvers": approvers,
        "contract_amount": amount, "approval_tier": tier_label(t) if t else "unknown (no work request)",
        "evidence": ev, "run": {"by": ME, "at": ts, "rules": "company/rules.json", "tool": "tools/onboard.py intake"},
    }
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write("\n")
    nxt = "approval packet not built yet" if status == "READY" else "follow-up not drafted yet"
    set_stage(slug, f"{status}: intake done {ts[:10]}; {nxt}", ts[:10])
    audit(slug, "intake", f"vendors/{slug}/intake.json; status {status}; issues {' '.join(issues) or 'none'}; "
                          f"approvers {' > '.join(approvers)}", status)
    print(json.dumps({k: result[k] for k in ("vendor", "documents", "issues", "status", "approvers")}, indent=2))


# ------------------------------------------------------------- /chase --------------------------------------------------------------
def facts(slug):
    j = intake_json(slug)
    v, d = load(slug)
    if j["status"] == "READY":
        raise Refused(f"{slug} is READY; nothing to chase")
    fm = people()["Facilities Manager"]
    out = {"vendor": v["Legal name"], "to": v["Contact email"], "from": fm["email"], "reviewer_and_sender": f"{fm['name']}, Facilities Manager",
           "status": j["status"], "issue_codes": j["issues"], "deadline": DEADLINE,
           "deadline_rule": f"demo date {TODAY} + {RULES['chase_deadline_days']} days (rules.json chase_deadline_days)",
           "work": {k: d["request"][k] for k in ("Building", "Scope")} if "request" in d else "no work request on file",
           "problems": [e for e in j["evidence"] if e["result"] in j["issues"]]}
    print(json.dumps(out, indent=2, ensure_ascii=False))


def lint(path):
    """Problems with a draft (empty list = good). A guardrail, not the test: tests/check_phase2.py checks drafts on its own."""
    p = os.path.abspath(path)
    m = re.search(r"vendors[\\/]([^\\/]+)[\\/]drafts[\\/][^\\/]+\.md$", p)
    if not m:
        raise Refused("drafts live at vendors/<slug>/drafts/<name>.md")
    slug = m.group(1)
    j = intake_json(slug)
    v, d = load(slug)
    text = open(p, encoding="utf-8").read()
    f = fields(p)
    probs = []
    st = f.get("Status", "").lower()
    if "draft" not in st or "not sent" not in st:
        probs.append("Status must say 'DRAFT, not sent'")
    if f.get("To") != v["Contact email"] or not f.get("To", "").endswith(".example"):
        probs.append(f"To must be {v['Contact email']}")
    if f.get("Deadline") != DEADLINE:
        probs.append(f"Deadline must be {DEADLINE}")
    if sorted(x.strip() for x in f.get("Issue codes", "").split(",") if x.strip()) != j["issues"]:
        probs.append(f"Issue codes must be {', '.join(j['issues'])}")
    body = text.split("## Message", 1)[1] if "## Message" in text else ""
    if not body:
        probs.append("no '## Message' section")
    if DEADLINE not in body:
        probs.append("the message must state the deadline")
    if "reply" not in body.lower() or "@palmquay.example" not in body:
        probs.append("the message must say how to send it (reply, and a palmquay.example address)")
    if v["Legal name"] not in text:
        probs.append("name the vendor by its legal name")
    allowed = {TODAY.isoformat(), DEADLINE} | {x for doc in [v, *d.values()] for val in doc.values() for x in DATE.findall(val)}
    if set(DATE.findall(text)) - allowed:
        probs.append(f"dates not in the file: {sorted(set(DATE.findall(text)) - allowed)}")
    mins = RULES["insurance_minimums"]
    allowed_m = {money(mins[k]) for k in ("gl_per_occurrence", "gl_aggregate", "auto_liability", "umbrella_high_risk")}
    allowed_m |= {x for doc in d.values() for val in doc.values() for x in MONEY.findall(val)}
    if set(MONEY.findall(text)) - allowed_m:
        probs.append(f"dollar amounts not in the file: {sorted(set(MONEY.findall(text)) - allowed_m)}")
    if THREATS.search(text):
        probs.append(f"threat or legal wording: {sorted({t.lower() for t in THREATS.findall(text)})}")
    sec = re.search(r"^## What we need\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    items = re.split(r"^\d+\.\s", sec.group(1), flags=re.M)[1:] if sec else []
    if len(items) != len(j["issues"]):
        probs.append(f"'What we need' has {len(items)} items for {len(j['issues'])} issues")
    if sum("Why we need it:" in i for i in items) != len(items):
        probs.append("every item needs a 'Why we need it:' line")
    for e in j["evidence"]:
        if e["result"] in j["issues"]:
            for x in DATE.findall(e["found"]) + MONEY.findall(e["found"]):
                if x not in text:
                    probs.append(f"{e['result']}: the draft doesn't state what we found ({x})")
    return slug, f, probs


def lint_draft(path):
    _, _, probs = lint(path)
    for x in probs:
        print("PROBLEM -", x)
    print(f"{len(probs)} problems")
    if probs:
        raise Refused("draft needs fixing before it can be logged")


def log_draft(path):
    slug, f, probs = lint(path)
    if probs:
        raise Refused(f"lint found {len(probs)} problems: {probs}")
    rp = relpath(path)
    rows = list(csv.reader(open(AUDIT, encoding="utf-8")))[1:]
    if any(r[3] == "chase_draft" and r[4].split(";")[0].strip() == rp for r in rows):
        raise Refused(f"{rp} is already logged")
    j = intake_json(slug)
    ts = now()
    set_stage(slug, f"{j['status']}: follow-up drafted {ts[:10]} for Dana Reyes to review and send; reply due {DEADLINE}", ts[:10])
    audit(slug, "chase_draft", f"{rp}; to {f['To']}; items {' '.join(j['issues'])}; deadline {DEADLINE}; "
                               f"reviewer and sender Dana Reyes", "drafted, not sent")


# ------------------------------------------------------------- /route --------------------------------------------------------------
def packet(slug):
    j = intake_json(slug)
    if j["status"] != "READY":
        raise Refused(f"{slug} is {j['status']} ({', '.join(j['issues'])}); only READY vendors are routed")
    out = os.path.join(vdir(slug), "packet.md")
    if os.path.exists(out):
        raise Refused(f"vendors/{slug}/packet.md already exists")
    v, d = load(slug)
    r = d["request"]
    t = tier(usd(r["Contract amount"]))
    if t["approvers"] != j["approvers"]:
        raise Refused(f"approvers in intake.json {j['approvers']} differ from rules.json {t['approvers']}; stop and say so")
    ppl = people()
    ts = now()
    L = [f"# Approval packet: {v['Legal name']}", "",
         "*Fake data for a demo. Built by the onboarding assistant from the vendor's documents and company/rules.json. "
         "Nothing is approved until the people below sign. The assistant never approves, signs, or pays.*", "",
         "| Field | Value |", "|---|---|",
         f"| Vendor | {v['Legal name']} |", f"| Trade | {v['Trade']} |", f"| Building | {r['Building']} |",
         f"| Scope | {r['Scope']} |", f"| Contract amount | {r['Contract amount']} |",
         f"| Requested by | {r.get('Requested by', 'not stated')} |", f"| Target start | {r.get('Target start', 'not stated')} |",
         f"| Intake status | READY (0 issues), checked against company/rules.json for {RULES['demo_date']} |",
         f"| Approval tier | {tier_label(t)}: {len(t['approvers'])} sign-off{'s' if len(t['approvers']) > 1 else ''}, in order |",
         f"| Built | {ts} by {ME} |", "",
         "## What intake checked", "", "| Check | Source | Found | Rule | Result |", "|---|---|---|---|---|"]
    L += [f"| {e['check']} | {e['source']} | {e['found']} | {e['rule']} | {e['result']} |" for e in j["evidence"]]
    L += ["", "## Sign-offs (in this order; each person signs after the one above)", "",
          "| # | Role | Name | Email | Decision | Date | Signature |", "|---|---|---|---|---|---|---|"]
    L += [f"| {i} | {role} | {ppl[role]['name']} | {ppl[role]['email']} |  |  |  |" for i, role in enumerate(t["approvers"], 1)]
    L += ["", "Decision, Date and Signature are left blank on purpose: a person fills them in. "
              "The next approver is notified by a person, not by the assistant.", ""]
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))
    first = t["approvers"][0]
    set_stage(slug, f"READY: approval packet built {ts[:10]}; waiting on {first} ({ppl[first]['name']}), "
                    f"sign-off 1 of {len(t['approvers'])}", ts[:10])
    n = len(t["approvers"])
    audit(slug, "route_packet", f"vendors/{slug}/packet.md; {n} approver{'s' if n > 1 else ''}: {' > '.join(t['approvers'])}; "
                                f"amount {r['Contract amount']}", "packet built, awaiting sign-off")


# ---------------------------------------------------------- checker review ---------------------------------------------------------
def manifest(paths):
    print("| Reviewed file | SHA-256 at review |")
    print("|---|---|")
    for p in paths:
        print(f"| `{relpath(p)}` | {hashlib.sha256(open(p, 'rb').read()).hexdigest()} |")


def log_review(path):
    rp = relpath(path)
    text = open(path, encoding="utf-8").read()
    f = fields(path)
    vendor = f.get("Vendors", "")
    if not vendor:
        raise Refused("review record needs a 'Vendors' field (a slug or 'all')")
    head, files = text.split("## Checker report", 1) if "## Checker report" in text else (text, "")
    files = sum(1 for l in head.splitlines() if re.match(r"\| `[^`]+` \| [0-9a-f]{64} \|", l))
    verdicts = []
    for l in text.split("## Checker report", 1)[-1].splitlines():
        cells = [c.strip().strip("`").strip() for c in l.strip().strip("|").split("|")]
        if l.startswith("|") and len(cells) >= 4 and cells[1].upper() in ("OK", "FINDING"):
            verdicts.append(cells)
    oks = sum(c[1].upper() == "OK" for c in verdicts)
    finds = [c for c in verdicts if c[1].upper() == "FINDING"]
    planted = sum("checker-copies/" in c[0] for c in finds)
    if not files or not verdicts:
        raise Refused(f"review record has {files} manifest rows and {len(verdicts)} verdict rows; nothing to log")
    real = len(finds) - planted
    audit(vendor, "checker_review", f"{rp}; {files} files reviewed; {oks} OK; {len(finds)} finding{'' if len(finds) == 1 else 's'} "
                                    f"({planted} on planted copies, {real} on real files); recorded by {ME}",
          "no findings on real files" if real == 0 else f"{real} findings on real files: fix before done",
          actor="compliance-checker")


# ------------------------------------------------------------- /status -------------------------------------------------------------
def status():
    print(f"Vendor status as of {TODAY} (days waiting = days since the vendor submitted)\n")
    print("| Vendor | Stage | Status | Blocker | Days waiting |")
    print("|---|---|---|---|---|")
    for vd in sorted(glob.glob(os.path.join(ROOT, "vendors", "*", "vendor.md"))):
        slug = os.path.basename(os.path.dirname(vd))
        v = fields(vd)
        ip = os.path.join(os.path.dirname(vd), "intake.json")
        j = json.load(open(ip, encoding="utf-8")) if os.path.exists(ip) else None
        st = j["status"] if j else "NOT REVIEWED"
        blocker = (", ".join(j["issues"]) or "none") if j else "intake not run"
        days = (TODAY - dt.date.fromisoformat(v["Submitted"])).days
        print(f"| {slug} | {v.get('Stage', '?')} | {st} | {blocker} | {days} |")


def verify_audit():
    good, rows, ok = chain_ok()
    print(f"audit log: {rows} rows, {ok} of {rows} chain links verify -> {'OK' if good else 'BROKEN'}")
    if not good:
        raise Refused("hash chain broken")


if __name__ == "__main__":
    cmds = {"intake": intake, "facts": facts, "lint-draft": lint_draft, "log-draft": log_draft, "packet": packet,
            "log-review": log_review}
    a = sys.argv[1:]
    try:
        if a and a[0] in cmds and len(a) == 2:
            cmds[a[0]](a[1])
        elif a and a[0] == "manifest" and len(a) > 1:
            manifest(a[1:])
        elif a == ["status"]:
            status()
        elif a == ["verify-audit"]:
            verify_audit()
        else:
            print(__doc__)
            sys.exit(1)
    except Unreadable as e:
        print(f"UNREADABLE - {e}. Stopping for this vendor; nothing written.")
        sys.exit(2)
    except Refused as e:
        print(f"REFUSED - {e}")
        sys.exit(3)
