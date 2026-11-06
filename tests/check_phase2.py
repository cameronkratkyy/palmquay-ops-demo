"""Phase 2 pass/fail check (P1-P7 of the Phase 2 brief). Prints what it counted; exit 1 on any FAIL.

    python -I -X utf8 tests/check_phase2.py             run the check
    python -I -X utf8 tests/check_phase2.py --selftest  prove it can fail: plant one break per temp copy, each must FAIL its own check

Written before the skills were built. It never imports tools/onboard.py (the build): it reads the vendor documents,
company/rules.json, company/people.md and the locked answer key itself. From Phase 1 it reuses only fields(),
dollars() and the personal-word list, so P6 runs the same scan as Phase 1 C6.

The checker test (P4) uses two planted copies in tests/checker-copies/:
  saltmarsh-roofing-draft-copy.md  the real Saltmarsh draft with one error planted (a wrong deadline)
  gulfpine-pest-intake-copy.json   Gulfpine's intake with the name mismatch removed (as if intake missed it)
The compliance-checker agent reviews them blind next to the real files; P4 reads its saved report.
"""
import csv
import datetime as dt
import glob
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
COPY = "--copy" in sys.argv
PLANTED_DRAFT = "tests/checker-copies/saltmarsh-roofing-draft-copy.md"
PLANTED_INTAKE = "tests/checker-copies/gulfpine-pest-intake-copy.json"
AGENT = ".claude/agents/compliance-checker.md"
SKILLS = ["intake", "chase", "route", "status"]
ACTORS = {"intake": "onboarding-assistant", "chase_draft": "onboarding-assistant",
          "route_packet": "onboarding-assistant", "checker_review": "compliance-checker"}
AUDIT_HEADER = "timestamp,actor,vendor,action,detail,result"
THREATS = re.compile(r"\b(legal action|lawsuits?|sue|suing|attorneys?|lawyers?|litigation|court|breach\w*|penalt\w*|liable|"
                     r"damages|terminat\w*|demand\w*|final notice|or else|consequences|failure to comply)\b", re.I)
NET_IMPORT = re.compile(r"^\s*(?:import|from)\s+(smtplib|socket|urllib|http|requests|ftplib|imaplib|poplib|aiohttp|httpx)\b", re.M)
OVERCLAIMS = re.compile(r"\b(coded (?:it|this|the \w+) myself|i coded|wrote (?:all )?the code myself|production[- ]ready|"
                        r"100% accurate|guarantee\w*|fully autonomous|zero errors|never makes mistakes|bulletproof|ai approves)\b", re.I)
TEXT_EXT = (".md", ".json", ".py", ".csv", ".txt", ".html")  # the same file types Phase 1 C6 scans
URL = re.compile(r"\bhttps?://([^/\s)\]>\"'`]+)", re.I)
WWW = re.compile(r"\bwww\.((?:[\w-]+\.)+[\w-]+)", re.I)
EMAIL = re.compile(r"[\w.+-]+@((?:[\w-]+\.)+[\w-]+)")
BARE = re.compile(r"\b((?:[a-z0-9-]+\.)+(?:com|net|org|io|gov|edu|us|ai|app|info|biz))\b", re.I)
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
MONEY = re.compile(r"\$\d[\d,]*")
results = []


def rec(ok, name, counted):
    ok = bool(ok)
    results.append((name.split()[0], ok))
    print(f"{'PASS' if ok else 'FAIL'} - {name} - {counted}")


def guarded(name, fn):
    """Run one check; a crash (missing file, bad JSON) counts as a FAIL, never as a pass."""
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        rec(False, name, f"could not run: {type(e).__name__}: {e}")


def load_phase1(root):
    spec = importlib.util.spec_from_file_location("check_phase1_for_p2", os.path.join(root, "tests", "check_phase1.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def read(p):
    return open(p, encoding="utf-8").read()


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def rel(root, p):
    return os.path.relpath(p, root).replace("\\", "/")


def table(text, first):
    """(header cells, rows) of the first markdown table whose first header cell is `first`. Backticks stripped."""
    lines = text.splitlines()
    for i, l in enumerate(lines):
        if not l.startswith("|"):
            continue
        cells = [c.strip() for c in l.strip().strip("|").split("|")]
        if cells and cells[0] == first:
            rows = []
            for r in lines[i + 2:]:
                if not r.startswith("|"):
                    break
                rows.append([c.strip().strip("`").strip() for c in r.strip().strip("|").split("|")])
            return cells, rows
    return None, []


def money(n):
    return f"${n:,}"


class Ctx:
    def __init__(self, root):
        self.root = root
        self.p1 = load_phase1(root)
        self.rules = json.load(open(os.path.join(root, "company", "rules.json"), encoding="utf-8"))
        self.key = json.load(open(os.path.join(root, "tests", "answer-key.json"), encoding="utf-8"))["vendors"]
        self.today = dt.date.fromisoformat(self.rules["demo_date"])
        self.deadline = (self.today + dt.timedelta(days=self.rules["chase_deadline_days"])).isoformat()

    def path(self, *parts):
        return os.path.join(self.root, *parts)

    def vendor(self, slug):
        vd = self.path("vendors", slug)
        v = self.p1.fields(os.path.join(vd, "vendor.md"))
        dd = os.path.join(vd, "documents")
        d = {f[:-3]: self.p1.fields(os.path.join(dd, f)) for f in sorted(os.listdir(dd)) if f.endswith(".md")}
        return v, d

    def tier(self, amount):
        for t in self.rules["approval_tiers"]:
            if t["max_amount"] is None or amount <= t["max_amount"]:
                return t["approvers"]
        return []

    def people(self):
        _, rows = table(read(self.path("company", "people.md")), "Role")
        out = {}
        for r in rows:
            for role in {x for t in self.rules["approval_tiers"] for x in t["approvers"]}:
                if r[0] == role or r[0].startswith(role + " ("):
                    out[role] = (r[1], r[3])
        return out

    def artifacts(self):
        a = {"intake": [], "chase_draft": [], "route_packet": [], "checker_review": []}
        for s in sorted(os.listdir(self.path("vendors"))):
            if os.path.exists(self.path("vendors", s, "intake.json")):
                a["intake"].append(f"vendors/{s}/intake.json")
            a["chase_draft"] += [rel(self.root, p) for p in sorted(glob.glob(self.path("vendors", s, "drafts", "*.md")))]
            if os.path.exists(self.path("vendors", s, "packet.md")):
                a["route_packet"].append(f"vendors/{s}/packet.md")
        a["checker_review"] = [rel(self.root, p) for p in sorted(glob.glob(self.path("reviews", "*.md")))]
        return a


# ---------- what a good draft must contain (written from CLAUDE.md sections 2-5 and 7, not from the build) ----------
def item_terms(code, v, d, rules):
    m, c, lic = rules["insurance_minimums"], d.get("coi", {}), d.get("license", {})
    names = sorted({x for x in (v.get("Legal name"), d.get("w9", {}).get("Legal name"), c.get("Insured"),
                                lic.get("License holder")) if x})
    return {
        "MISSING_W9": ["W-9"], "MISSING_COI": ["certificate of insurance"], "MISSING_LICENSE": ["license"],
        "MISSING_REQUEST": ["work request"],
        "COI_EXPIRED": ["certificate", c.get("Policy end", "?")], "COI_EXPIRING_30D": ["certificate", c.get("Policy end", "?")],
        "LICENSE_EXPIRED": ["license", lic.get("Expires", "?")], "LICENSE_EXPIRING_30D": ["license", lic.get("Expires", "?")],
        "GL_BELOW_MIN": ["general liability", c.get("General liability per occurrence", "?"), c.get("General liability aggregate", "?"),
                         money(m["gl_per_occurrence"]), money(m["gl_aggregate"])],
        "AUTO_BELOW_MIN": ["auto liability", c.get("Auto liability", "?"), money(m["auto_liability"])],
        "UMBRELLA_MISSING": ["umbrella", money(m["umbrella_high_risk"])],
        "WC_MISSING": ["workers' comp"],
        "NO_ADDITIONAL_INSURED": ["additional insured", m["additional_insured"]],
        "NAME_MISMATCH": names,
    }[code]


def check_draft(cx, slug, path):
    """Problems with one draft, as a list of strings (empty = good)."""
    probs, text = [], read(path)
    f = cx.p1.fields(path)
    v, d = cx.vendor(slug)
    issues = sorted(cx.key[slug]["issues"])
    status = f.get("Status", "").lower()
    if "draft" not in status or "not sent" not in status:
        probs.append(f"Status '{f.get('Status')}' is not 'DRAFT, not sent'")
    to = f.get("To", "")
    if to != v.get("Contact email") or not to.endswith(".example"):
        probs.append(f"To '{to}' is not the vendor's .example contact")
    if f.get("Deadline") != cx.deadline:
        probs.append(f"Deadline field '{f.get('Deadline')}' is not {cx.deadline}")
    codes = sorted(c.strip() for c in f.get("Issue codes", "").split(",") if c.strip())
    if codes != issues:
        probs.append(f"Issue codes {codes} are not the key's {issues}")
    if v.get("Legal name", "?") not in text:
        probs.append("does not name the vendor")
    body = text.split("## Message", 1)[1] if "## Message" in text else ""
    if cx.deadline not in body:
        probs.append(f"message body never states the deadline {cx.deadline}")
    if "reply" not in body.lower() or not re.search(r"[\w.]+@palmquay\.example", body):
        probs.append("message body doesn't say how to send it (reply + a palmquay.example address)")
    allowed_dates = {cx.today.isoformat(), cx.deadline} | {x for doc in [v, *d.values()] for val in doc.values()
                                                            for x in DATE.findall(val)}
    bad_dates = sorted(set(DATE.findall(text)) - allowed_dates)
    if bad_dates:
        probs.append(f"dates not in the file or the rules: {bad_dates}")
    for later in re.findall(r"\bby \**(\d{4}-\d{2}-\d{2})", text):
        if later != cx.deadline:
            probs.append(f"asks for something by {later}, not {cx.deadline}")
    m = cx.rules["insurance_minimums"]
    allowed_money = {money(m[k]) for k in ("gl_per_occurrence", "gl_aggregate", "auto_liability", "umbrella_high_risk")}
    allowed_money |= {x for doc in d.values() for val in doc.values() for x in MONEY.findall(val)}
    bad_money = sorted(set(MONEY.findall(text)) - allowed_money)
    if bad_money:
        probs.append(f"dollar amounts not in the file or the rules: {bad_money}")
    threats = sorted({t.lower() for t in THREATS.findall(text)})
    if threats:
        probs.append(f"threat or legal wording: {threats}")
    sec = re.search(r"^## What we need\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    blocks = re.split(r"^\d+\.\s", sec.group(1), flags=re.M)[1:] if sec else []
    if len(blocks) != len(issues):
        probs.append(f"{len(blocks)} items under 'What we need' for {len(issues)} issues")

    def why_ok(b):
        w = re.search(r"Why we need it:\**\s*(.*)", b, re.S)
        return bool(w) and len(w.group(1).split()) >= 6

    for code in issues:
        terms = item_terms(code, v, d, cx.rules)
        if not any(all(t.lower() in b.lower() for t in terms) and why_ok(b) for b in blocks):
            probs.append(f"{code}: no item naming {terms} with a 'Why we need it:' reason")
    return probs


def check_packet(cx, slug, path):
    probs, text = [], read(path)
    v, d = cx.vendor(slug)
    req = d["request"]
    amount = cx.p1.dollars(req["Contract amount"])
    want = cx.tier(amount)
    if want != cx.key[slug]["approvers"]:
        probs.append(f"rules.json tier {want} differs from the key {cx.key[slug]['approvers']}")
    for label, val in (("vendor name", v["Legal name"]), ("building", req["Building"]), ("scope", req["Scope"]),
                       ("amount", req["Contract amount"])):
        if val not in text:
            probs.append(f"{label} '{val}' missing")
    if "READY" not in cx.p1.fields(path).get("Intake status", ""):
        probs.append("Intake status field does not say READY")
    head, rows = table(text, "#")
    if not head or head[:2] != ["#", "Role"]:
        return probs + ["no sign-off table (| # | Role | ...)"]
    col = {h: i for i, h in enumerate(head)}
    roles = [r[col["Role"]] for r in rows]
    if roles != want:
        probs.append(f"approvers {roles}, rules.json says {want} in that order")
    ppl = cx.people()
    for r in rows:
        if r[col["Role"]] in ppl and r[col["Name"]] != ppl[r[col["Role"]]][0]:
            probs.append(f"{r[col['Role']]} is '{r[col['Name']]}', people.md says {ppl[r[col['Role']]][0]}")
        for blank in ("Decision", "Date", "Signature"):
            if blank not in col:
                probs.append(f"no {blank} column")
            elif not re.fullmatch(r"[_\s]*", r[col[blank]]):
                probs.append(f"{r[col['Role']]} {blank} is filled in: '{r[col[blank]]}'")
    return probs


# ------------------------------------------------------------- P1-P7 -------------------------------------------------------------
def p1(cx):
    good, stages, bad = 0, 0, {}
    for s, exp in cx.key.items():
        p = cx.path("vendors", s, "intake.json")
        if not os.path.exists(p):
            bad[s] = "no intake.json"
            continue
        j = json.load(open(p, encoding="utf-8"))
        diffs = [f"{k} {j.get(k)} vs key {exp[k]}" for k in ("issues", "documents")
                 if sorted(j.get(k) or []) != sorted(exp[k])]
        diffs += [f"{k} {j.get(k)} vs key {exp[k]}" for k in ("status", "approvers") if j.get(k) != exp[k]]
        if j.get("vendor") != s:
            diffs.append(f"vendor field {j.get('vendor')}")
        stage = cx.p1.fields(cx.path("vendors", s, "vendor.md")).get("Stage", "")
        if stage.startswith(exp["status"] + ":"):
            stages += 1
        else:
            diffs.append(f"Stage '{stage}' doesn't start with '{exp['status']}:'")
        if diffs:
            bad[s] = diffs
        else:
            good += 1
    rec(good == len(cx.key) == 8, "P1 /intake results = locked answer key (issues, status, approvers) + Stage filled",
        f"{good} of {len(cx.key)} intake.json match; {stages} of {len(cx.key)} Stage lines start with the status; mismatches {bad}")


def p1b(cx):
    helper = cx.path("tools", "onboard.py")
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", helper, "status"], capture_output=True, text=True, cwd=cx.root)
    head, rows = table(r.stdout, "Vendor")
    codes = set(cx.rules["issue_codes"])
    good, bad = 0, {}
    for s, exp in cx.key.items():
        row = next((x for x in rows if x[0] == s), None)
        if row is None or not head or len(row) != len(head):
            bad[s] = "no status line"
            continue
        c = dict(zip(head, row))
        v = cx.p1.fields(cx.path("vendors", s, "vendor.md"))
        days = (cx.today - dt.date.fromisoformat(v["Submitted"])).days
        diffs = []
        if c.get("Status") != exp["status"]:
            diffs.append(f"status {c.get('Status')}")
        if set(re.findall(r"[A-Z0-9_]+", c.get("Blocker", ""))) & codes != set(exp["issues"]):
            diffs.append(f"blocker {c.get('Blocker')}")
        if c.get("Stage") != v.get("Stage"):
            diffs.append("stage differs from vendor.md")
        if c.get("Days waiting") != str(days):
            diffs.append(f"days {c.get('Days waiting')} vs {days}")
        if diffs:
            bad[s] = diffs
        else:
            good += 1
    rec(r.returncode == 0 and good == 8 and len(rows) == 8, "P1b /status prints one correct line per vendor",
        f"exit {r.returncode}; {len(rows)} lines; {good} of 8 right (stage, status, blocker, days waiting); problems {bad} {r.stderr[-200:]}")


def p2(cx):
    need = [s for s in cx.key if cx.key[s]["status"] in ("BLOCKED", "HOLD")]
    good, extra, bad = 0, [], {}
    for s in cx.key:
        files = sorted(glob.glob(cx.path("vendors", s, "drafts", "*.md")))
        if s not in need:
            extra += [rel(cx.root, f) for f in files]
            continue
        if len(files) != 1:
            bad[s] = f"{len(files)} drafts (want exactly 1)"
            continue
        probs = check_draft(cx, s, files[0])
        if probs:
            bad[s] = probs
        else:
            good += 1
    rows = list(csv.reader(open(cx.path("audit", "audit-log.csv"), encoding="utf-8")))[1:]
    sent_rows = [r for r in rows if len(r) == 6 and ("send" in r[3].lower() or
                                                     ("sent" in r[5].lower() and "not sent" not in r[5].lower()))]
    net = [rel(cx.root, p) for base in ("tools", ".claude") for p in glob.glob(cx.path(base, "**", "*.py"), recursive=True)
           if NET_IMPORT.search(read(p))]
    sends = len(sent_rows) + len(net)
    rec(good == len(need) == 6 and not extra and sends == 0, "P2 /chase: 1 good draft per BLOCKED/HOLD vendor, 0 sends",
        f"{good} of {len(need)} drafts pass (vendor, item, why, deadline {cx.deadline}, how to send, .example contact, "
        f"no threats, no unsupported facts); {len(extra)} drafts for READY vendors {extra}; sends {sends} "
        f"(audit rows marked sent {len(sent_rows)}, network imports {net}); problems {bad}")


def p3(cx):
    ready = [s for s in cx.key if cx.key[s]["status"] == "READY"]
    good, wrong_place, bad, order = 0, [], {}, {}
    for s in cx.key:
        p = cx.path("vendors", s, "packet.md")
        if s not in ready:
            if os.path.exists(p):
                wrong_place.append(s)
            continue
        if not os.path.exists(p):
            bad[s] = "no packet.md"
            continue
        probs = check_packet(cx, s, p)
        _, rows = table(read(p), "#")
        order[s] = [r[1] for r in rows]
        if probs:
            bad[s] = probs
        else:
            good += 1
    rec(good == len(ready) == 2 and not wrong_place, "P3 /route: packet for each READY vendor, approvers in order, sign-offs blank",
        f"{good} of {len(ready)} packets pass; packets for vendors not READY {wrong_place}; approvers {order}; problems {bad}")


def p4(cx):
    probs = []
    # the agent is read-only by its own definition
    ap = cx.path(AGENT)
    text = read(ap) if os.path.exists(ap) else ""
    fm = text.split("---")[1] if text.startswith("---") and text.count("---") >= 2 else ""
    meta = dict(re.findall(r"^(\w[\w-]*):\s*(.*)$", fm, re.M))
    tools = sorted(t.strip() for t in meta.get("tools", "").split(",") if t.strip())
    if meta.get("name") != "compliance-checker" or tools != ["Glob", "Grep", "Read"]:
        probs.append(f"agent name {meta.get('name')}, tools {tools} (want exactly Glob, Grep, Read)")
    # the planted copies really are wrong, and wrong in exactly one way
    real_draft = sorted(glob.glob(cx.path("vendors", "saltmarsh-roofing", "drafts", "*.md")))
    pd, pi = cx.path(PLANTED_DRAFT), cx.path(PLANTED_INTAKE)
    if not (real_draft and os.path.exists(pd) and os.path.exists(pi)):
        probs.append("planted copies or the real Saltmarsh draft missing")
    else:
        rt, ptxt = read(real_draft[0]), read(pd)
        new_dates = sorted(set(DATE.findall(ptxt)) - set(DATE.findall(rt)))
        if len(new_dates) != 1 or rt.replace(cx.deadline, new_dates[0]) != ptxt:
            probs.append(f"planted draft is not the real draft with only the deadline changed (new dates {new_dates})")
        if not any("Deadline" in x for x in check_draft(cx, "saltmarsh-roofing", pd)):
            probs.append("planted draft's deadline error is not a real error by P2's rules")
        pj = json.load(open(pi, encoding="utf-8"))
        if pj.get("vendor") != "gulfpine-pest" or "NAME_MISMATCH" in pj.get("issues", []) \
                or "NAME_MISMATCH" not in cx.key["gulfpine-pest"]["issues"]:
            probs.append("planted Gulfpine intake does not miss the name mismatch")
    # the latest review covers every current file, still matches it byte for byte, and caught both plants
    reviews = cx.artifacts()["checker_review"]
    if not reviews:
        rec(False, "P4 read-only compliance-checker reviewed everything and caught both plants", f"no review in reviews/; {probs}")
        return
    rv = read(cx.path(reviews[-1]))
    _, man = table(rv, "Reviewed file")
    hashes = {r[0]: r[1] for r in man if len(r) >= 2}
    stale = [p for p, h in hashes.items() if not os.path.exists(cx.path(p)) or sha(cx.path(p)) != h]
    a = cx.artifacts()
    real = a["intake"] + a["chase_draft"] + a["route_packet"]
    want = real + [PLANTED_DRAFT, PLANTED_INTAKE]
    unlisted = [p for p in want if p not in hashes]
    head, vrows = table(rv, "Target")
    verdict = {}  # a file can have several finding rows
    for r in vrows:
        if head and len(r) == len(head) and r[1].upper() in ("OK", "FINDING"):
            verdict.setdefault(r[0], []).append(r)
    no_verdict = [p for p in want if p not in verdict]
    real_findings = [p for p in real if any(r[1].upper() != "OK" for r in verdict.get(p, []))]
    real_ok = [p for p in real if p in verdict and p not in real_findings]
    caught_deadline = any(r[1].upper() == "FINDING" and "DEADLINE" in (r[2] + r[3]).upper() and cx.deadline in r[3]
                          for r in verdict.get(PLANTED_DRAFT, []))
    caught_name = any(r[1].upper() == "FINDING" and "NAME_MISMATCH" in (r[2] + r[3]).upper()
                      for r in verdict.get(PLANTED_INTAKE, []))
    if stale or unlisted or no_verdict or real_findings or not caught_deadline or not caught_name:
        probs.append(f"stale {stale}; not in manifest {unlisted}; no verdict {no_verdict}; findings on real files {real_findings}")
    rec(not probs and caught_deadline and caught_name,
        "P4 read-only compliance-checker reviewed everything and caught both plants",
        f"agent tools {tools}; latest review {reviews[-1]}: {len(hashes)} files, {len(hashes) - len(stale)} unchanged since review; "
        f"{len(real_ok)} of {len(real)} real files marked OK by the checker; planted wrong deadline caught {caught_deadline}; "
        f"planted missed name mismatch caught {caught_name}; problems {probs}")


def p5(cx):
    raw = open(cx.path("audit", "audit-log.csv"), encoding="utf-8", newline="").read()
    lines = [l.rstrip("\r") for l in raw.split("\n")]
    if lines and lines[-1] == "":
        lines.pop()
    probs = []
    if not lines or lines[0] != AUDIT_HEADER:
        probs.append("header changed")
    data = lines[1:]
    rows = list(csv.reader(data))
    a = cx.artifacts()
    taken = sum(len(v) for v in a.values())
    seen = {k: [] for k in a}
    last = None
    for i, r in enumerate(rows, 1):
        if len(r) != 6 or not all(x.strip() for x in r):
            probs.append(f"row {i} doesn't have 6 filled fields")
            continue
        ts, actor, vendor, action, detail, _ = r
        try:
            t = dt.datetime.fromisoformat(ts)
            if last and t < last:
                probs.append(f"row {i} is earlier than the row above it")
            last = t
        except ValueError:
            probs.append(f"row {i} timestamp '{ts}'")
        if action not in ACTORS:
            probs.append(f"row {i} unknown action '{action}'")
            continue
        if actor != ACTORS[action]:
            probs.append(f"row {i} actor '{actor}' for {action}")
        if vendor not in cx.key and vendor != "all":
            probs.append(f"row {i} vendor '{vendor}'")
        seen[action].append(detail.split(";")[0].strip())
    for k in a:
        if sorted(seen[k]) != sorted(a[k]):
            probs.append(f"{k}: rows {sorted(seen[k])} vs files {sorted(a[k])}")
    cp = cx.path("audit", "audit-log.chain.txt")
    chain = open(cp, encoding="utf-8").read().split() if os.path.exists(cp) else []
    h, ok_links = hashlib.sha256(AUDIT_HEADER.encode()).hexdigest(), 0
    for i, line in enumerate(data):
        h = hashlib.sha256((h + "\n" + line).encode("utf-8")).hexdigest()
        if i < len(chain) and chain[i] == h:
            ok_links += 1
    if ok_links != len(data) or len(chain) != len(data):
        probs.append(f"hash chain: {ok_links} of {len(data)} rows verify, {len(chain)} links stored (a past row was edited?)")
    rec(not probs and len(rows) == taken and taken > 0, "P5 audit log: 1 row per action, append-only (hash chain)",
        f"{len(rows)} rows; {taken} actions taken ({len(a['intake'])} intake + {len(a['chase_draft'])} chase drafts + "
        f"{len(a['route_packet'])} route packets + {len(a['checker_review'])} checker reviews); "
        f"chain {ok_links} of {len(data)} rows verify; problems {probs}")


def p6(cx):
    cmd = [sys.executable, "-I", "-X", "utf8", cx.path("tests", "check_phase1.py"), "--selftest"] + (["--copy"] if COPY else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    m = re.search(r"RESULT: (\d+) of (\d+) checks PASS", r.stdout)
    st = len(re.findall(r"^PASS - selftest", r.stdout, re.M))
    n_breaks = len(re.findall(r"^(?:PASS|FAIL) - selftest", r.stdout, re.M))  # 4 since D58 (11/5); every one must be caught
    phase1_ok = r.returncode == 0 and m and m.group(1) == m.group(2) == "8" and st == n_breaks >= 4
    label = (json.load(open(cx.path("company", "rules.json"), encoding="utf-8")).get("projects", {}).get("partner_label") or "").lower()
    partner = getattr(cx.p1, "PARTNER", None)
    hits, webs, files = [], [], 0
    for dp, _, fs in os.walk(cx.root):
        for fn in fs:
            if fn.endswith(TEXT_EXT):
                files += 1
                t = open(os.path.join(dp, fn), encoding="utf-8", errors="replace").read()
                low = t.lower()
                hits += [f"{fn}:{w}" for w in cx.p1.BANNED if w in low and not (w == partner and label and label in low)]
                for rx in (URL, WWW, EMAIL, BARE):
                    webs += [f"{fn}:{host}" for host in rx.findall(t) if not host.lower().rstrip(".").endswith(".example")]
    rec(phase1_ok and not hits and not webs and files > 0, "P6 Phase 1 still 8 of 8; 0 personal words; 0 web addresses but .example",
        f"Phase 1: {m.group(0) if m else 'no result line'}, {st} of {n_breaks} self-test breaks caught, exit {r.returncode}; "
        f"{files} files scanned for {len(cx.p1.BANNED)} words: {len(hits)} hits {hits}; non-.example addresses {len(webs)} {webs[:5]}")


def p7(cx):
    rd = read(cx.path("README.md"))
    probs = []
    status_row = next((l for l in rd.splitlines() if l.startswith("| 2 |")), "")
    if "Built" not in status_row or "Next" in status_row:
        probs.append(f"status row for Phase 2: '{status_row[:90]}'")
    head, rows = table(rd, "Piece")
    rows = [r for r in rows if len(r) == 5 and all(r)] if head else []
    pieces = {"/intake": None, "/chase": None, "/route": None, "/status": None, "compliance-checker": None,
              "audit-log.csv": None, "check_phase2.py": None}
    for r in rows:
        for p in pieces:
            if p in r[0] and pieces[p] is None:
                pieces[p] = r
    missing = [p for p, r in pieces.items() if r is None]
    weak = [p for p, r in pieces.items() if r and (not re.search(r"designed|directed", r[4], re.I) or
                                                   re.search(r"\b(coded|programmed)\b", r[4], re.I))]
    if "header only" in rd:
        probs.append("audit row still says 'header only'")
    if "designed and directed" not in rd.lower():
        probs.append("no 'designed and directed' wording")
    over = sorted({m.group(0).lower() for m in OVERCLAIMS.finditer(rd)})
    if "check_phase2.py" not in rd.split("## Run the check", 1)[-1]:
        probs.append("Run the check section doesn't show check_phase2.py")
    rec(not probs and not missing and not weak and not over, "P7 README status + mapping cover the Phase 2 pieces, no overclaims",
        f"{len(pieces) - len(missing)} of {len(pieces)} new pieces mapped (term + resume line) {missing}; resume lines not "
        f"'designed/directed' {weak}; overclaims {over}; {len(rows)} mapping rows; problems {probs}")


def run(root):
    results.clear()
    cx = Ctx(root)
    for name, fn in (("P1", p1), ("P1b", p1b), ("P2", p2), ("P3", p3), ("P4", p4), ("P5", p5), ("P6", p6), ("P7", p7)):
        guarded(name, lambda fn=fn: fn(cx))
    print(f"\nRESULT: {sum(ok for _, ok in results)} of {len(results)} checks PASS")
    return all(ok for _, ok in results)


# ------------------------------------------------------------ self-test ------------------------------------------------------------
def sub(path, old, new):
    def f(cp):
        p = os.path.join(cp, path)
        s = read(p)
        assert old in s, f"'{old}' not in {path}"
        open(p, "w", encoding="utf-8", newline="").write(s.replace(old, new, 1))
    return f


def line_sub(path, contains, old, new):
    def f(cp):
        p = os.path.join(cp, path)
        lines = read(p).split("\n")
        i = next(i for i, l in enumerate(lines) if contains in l and old in l)
        lines[i] = lines[i].replace(old, new, 1)
        open(p, "w", encoding="utf-8", newline="").write("\n".join(lines))
    return f


def first_draft(cp, slug):
    return sorted(glob.glob(os.path.join(cp, "vendors", slug, "drafts", "*.md")))[0]


def draft_sub(slug, old, new):
    def f(cp):
        p = first_draft(cp, slug)
        sub(os.path.relpath(p, cp), old, new)(cp)
    return f


def json_edit(path, **changes):
    def f(cp):
        p = os.path.join(cp, path)
        j = json.load(open(p, encoding="utf-8"))
        j.update(changes)
        json.dump(j, open(p, "w", encoding="utf-8"), indent=2)
    return f


def swap_rows(path, a, b):
    def f(cp):
        p = os.path.join(cp, path)
        lines = read(p).split("\n")
        i = next(i for i, l in enumerate(lines) if a in l)
        j = next(i for i, l in enumerate(lines) if b in l)
        ci, cj = lines[i].split("|"), lines[j].split("|")
        ci[2:], cj[2:] = cj[2:], ci[2:]  # keep the # column, swap everything after it
        lines[i], lines[j] = "|".join(ci), "|".join(cj)
        open(p, "w", encoding="utf-8", newline="").write("\n".join(lines))
    return f


def drop_findings(name):
    """Turn every FINDING row about `name` in the latest review into OK (as if the checker missed it)."""
    def f(cp):
        p = sorted(glob.glob(os.path.join(cp, "reviews", "*.md")))[-1]
        lines = read(p).split("\n")
        hit = [i for i, l in enumerate(lines) if name in l and "FINDING" in l]
        assert hit, f"no FINDING row about {name}"
        for i in hit:
            lines[i] = lines[i].replace("FINDING", "OK")
        open(p, "w", encoding="utf-8", newline="").write("\n".join(lines))
    return f


def drop_last_audit_row(cp):
    for name in ("audit-log.csv", "audit-log.chain.txt"):
        p = os.path.join(cp, "audit", name)
        lines = read(p).rstrip("\n").split("\n")
        open(p, "w", encoding="utf-8", newline="").write("\n".join(lines[:-1]) + "\n")


def selftest():
    fake_mail = "".join(["office", "@", "clearsail-janitorial", ".", "com"])  # built in pieces so this file passes P6
    fake_site = "".join(["https", "://", "www", ".", "palmquay-demo", ".", "com"])
    personal = "noremaC"[::-1]  # reversed like Phase 1, so this file passes the scan
    late = "2026-11-19"
    breaks = [
        ("P1", "Bayvane's intake says BLOCKED instead of HOLD", json_edit("vendors/bayvane-plumbing/intake.json", status="BLOCKED")),
        ("P1", "Gulfpine's intake missed the name mismatch", json_edit("vendors/gulfpine-pest/intake.json", issues=[], status="READY")),
        ("P1", "a Stage line left at Submitted", line_sub("vendors/kestrelbay-air-heat/vendor.md", "| Stage |", "| Stage | ",
                                                         "| Stage | Submitted (not reviewed) was ")),
        ("P1b", "the /status helper is missing", lambda cp: os.remove(os.path.join(cp, "tools", "onboard.py"))),
        ("P2", "Saltmarsh's draft gives a wrong deadline", draft_sub("saltmarsh-roofing", "2026-11-12", late)),
        ("P2", "Clearsail's draft goes to a real-looking address", draft_sub("clearsail-janitorial",
                                                                             "office@clearsail-janitorial.example", fake_mail)),
        ("P2", "a legal threat added to Brightcurrent's draft", draft_sub("brightcurrent-electric", "## Deadline and how to send it",
                                                                          "If we don't hear back we will take legal action.\n\n"
                                                                          "## Deadline and how to send it")),
        ("P2", "a dollar amount that isn't in the file", draft_sub("bayvane-plumbing", "## Deadline and how to send it",
                                                                   "Coverage of $250,000 will also be needed.\n\n## Deadline and how to send it")),
        ("P2", "Fernhollow's draft deleted", lambda cp: os.remove(first_draft(cp, "fernhollow-grounds"))),
        ("P2", "a draft marked as sent", draft_sub("gulfpine-pest", "| Status | DRAFT, not sent |", "| Status | SENT 2026-11-05 |")),
        ("P3", "Skyquay's approvers out of order (Finance before Legal)",
         swap_rows("vendors/skyquay-lift-fire/packet.md", "| Legal |", "| Finance |")),
        ("P3", "a sign-off pre-filled in Kestrelbay's packet",
         line_sub("vendors/kestrelbay-air-heat/packet.md", "| Facilities Manager |", "|  |  |  |", "| Approved | 2026-11-05 | D. Reyes |")),
        ("P3", "a packet built for a BLOCKED vendor",
         lambda cp: shutil.copy(os.path.join(cp, "vendors", "kestrelbay-air-heat", "packet.md"),
                                os.path.join(cp, "vendors", "saltmarsh-roofing", "packet.md"))),
        ("P4", "the checker agent given the Write tool", sub(AGENT, "tools: Read, Grep, Glob", "tools: Read, Grep, Glob, Write")),
        ("P4", "the review lost the planted-deadline finding", drop_findings("saltmarsh-roofing-draft-copy")),
        ("P4", "a reviewed draft changed after the review", draft_sub("bayvane-plumbing", "Thank you,", "Thanks again,")),
        ("P5", "a past audit row edited", line_sub("audit/audit-log.csv", "saltmarsh-roofing/intake.json", "BLOCKED", "READY")),
        ("P5", "an audit row (and its chain link) removed", drop_last_audit_row),
        ("P6", "a personal word planted", sub("vendors/skyquay-lift-fire/vendor.md", "| Phone |", f"| Contact person | {personal} |\n| Phone |")),
        ("P6", "a real-looking web address planted", sub("README.md", "## Run the check", f"See {fake_site}\n\n## Run the check")),
        ("P6", "the Phase 1 answer key edited", sub("tests/answer-key.json", '"why": "clean small job"', '"why": "clean"')),
        ("P7", "README still says Phase 2 is Next", line_sub("README.md", "| 2 |", "Built", "Next")),
        ("P7", "README overclaims", sub("README.md", "## Run the check", "I coded it myself.\n\n## Run the check")),
    ]
    ok_all, caught = True, 0
    for want, name, mutate in breaks:
        tmp = tempfile.mkdtemp()
        cp = os.path.join(tmp, "Onboarding-Demo")
        shutil.copytree(ROOT, cp)
        try:
            mutate(cp)
        except Exception as e:  # noqa: BLE001
            print(f"FAIL - selftest setup for '{name}': {type(e).__name__}: {e}")
            ok_all = False
            shutil.rmtree(tmp, ignore_errors=True)
            continue
        r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(cp, "tests", "check_phase2.py"), "--copy"],
                           capture_output=True, text=True)
        failed = [l.split(" - ")[1].split()[0] for l in r.stdout.splitlines() if l.startswith("FAIL - ")]
        ok = r.returncode != 0 and want in failed
        ok_all &= ok
        caught += ok
        print(f"{'PASS' if ok else 'FAIL'} - selftest: {name} -> {want} must FAIL - flagged {failed}")
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"\nSELF-TEST: {caught} of {len(breaks)} planted breaks caught by the check they target")
    return ok_all


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        a = run(ROOT)
        print("\nSelf-test (can the check fail?)")
        b = selftest()
        sys.exit(0 if a and b else 1)
    sys.exit(0 if run(ROOT) else 1)
