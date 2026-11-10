"""Phase 3f check: the dashboard's "By hand vs. system" tab (fictional company, sample records).

Written 11/9/2026 before the tab existed; its first run had to fail. The tab shows what the same work takes done by hand (every
email, check, lookup, retyped field, packet, supplier task, and sign-off) next to what a person still does with the system.
The COUNTS come from the sample records by a written rule per step. This check recounts each one from the raw records (the
locked answer keys, the documents, the plan, the quotes, the tracking, the invoices), never from the builder. The one exception
is "fields typed again," counted on the packets themselves: a field counts only when its value already exists word for word in
a source record (the work request, the vendor record, or the e-signature export).
The MINUTES are assumptions (dashboard/by-hand.json): this check proves they are labeled that way and never shown as a measurement.
It also proves one check count is used everywhere (tests/suite.json), and that the README's git-history line matches git.

    python -I -X utf8 tests/check_phase3f.py              F1-F6, prints what it counted; exit 1 on any FAIL
    python -I -X utf8 tests/check_phase3f.py --facts      print the recounted facts as JSON (Phase 3b's B1 adds them to its own)
    python -I -X utf8 tests/check_phase3f.py --selftest   plant one break per check in a temp copy; each must FAIL its own check

Options: --root DIR (check a copy) · --copy (the older checks are told they run on a copy)

The page contract (what dashboard/build.py must meet on this tab):
- the tab is <section data-tab="byhand">; each number in it is <span class="n" data-k="bh.KEY">, equal to this check's recount;
- one row per step (data-bh-step, in STEPS order) and per kind of touch (data-bh-type, in TYPES order);
- each kind of touch has <input data-min="TYPE" value="MINUTES"> and <td class="basis" data-basis="TYPE">, both equal to by-hand.json;
- the page's script recomputes every minute total from those inputs on load and marks the section data-bh-js="1".
"""
import glob
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
COPY = "--copy" in sys.argv
ROOT = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.dirname(HERE)
PROJ = "unit-4b"
N_CHECKS = 6
TYPES = ["write", "review", "check", "lookup", "typed", "form", "flag", "task", "sign"]
STEPS = ["intake", "certs", "screen", "chase", "route", "revise", "scope", "ask", "source", "quote", "approve", "request", "change",
         "deliver", "credit", "match", "closeout"]  # the order a real office works in (review round 1: the approval request comes before the order)
BUILD_RUNS = ["check_phase1.py", "check_phase2.py", "check_phase3a.py", "check_phase3c.py", "check_phase3d.py"]  # what dashboard/build.py re-runs
NUMWORDS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten".split())}
OVERCLAIM = [r"\bsav(?:e|es|ed|ing|ings)\b", r"\bguarantee", r"\bproven\b", r"\bROI\b", r"\bmeasured (?:result|savings|time|minutes)\b",
             r"\bfake\b", r"\bin production\b", r"\breal (?:client|customer)s?\b", r"\bcase study\b"]
BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
results = []


def rec(ok, name, counted):
    ok = bool(ok)
    results.append((ok, name))
    print(f"{'PASS' if ok else 'FAIL'} - {name} - {counted}")


def p(*a):
    return os.path.join(ROOT, *a)


def read(*a):
    f = p(*a)
    return open(f, encoding="utf-8").read().replace("\r", "") if os.path.exists(f) else ""


def jload(*a):
    t = read(*a)
    return json.loads(t) if t else {}


def kv(t):
    """'| Field | Value |' rows and 'Key: value' lines -> dict (first wins)."""
    out = {}
    for line in t.splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", line) or re.match(r"^([A-Z][A-Za-z ,()/'-]*?):[ \t]*(.*)$", line)
        if m and m.group(1) not in out:
            out[m.group(1)] = m.group(2).strip()
    return out


def rows(t, first):
    """The body rows (lists of cells) of the first Markdown table whose header starts with `first`."""
    lines = t.splitlines()
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells[0] == first:
            out = []
            for r in lines[i + 2:]:
                if not r.startswith("|"):
                    break
                out.append([c.strip() for c in r.strip().strip("|").split("|")])
            return out
    return []


def money(s):
    return int(re.sub(r"[^\d]", "", s))


def day(s):
    import datetime as dt
    return dt.date.fromisoformat(s.strip()[:10])


def rnd(x):
    return int(math.floor(x + 0.5))  # the page's script rounds the same way


def num(s):
    s = s.strip().replace(",", "").replace("$", "")
    return int(s) if re.fullmatch(r"\d+", s) else None


# ------------------------------------------------------------- recount -------------------------------------------------------------
def recount():
    """Every count on the tab, from the raw records. Returns (facts, detail) where detail keeps the per-step counters."""
    rules = jload("company", "rules.json")
    key = jload("tests", "answer-key.json")["vendors"]
    k3a, k3c, k3e = jload("tests", "answer-key-3a.json"), jload("tests", "answer-key-3c.json"), jload("tests", "answer-key-3e.json")
    slugs = sorted(d for d in os.listdir(p("vendors")) if os.path.isdir(p("vendors", d)))
    H = {s: Counter() for s in STEPS}  # by hand
    S = {s: Counter() for s in STEPS}  # with the system: what a person still does
    doc = lambda s, d: read("vendors", s, "documents", d + ".md")

    # Onboarding. 1 intake: per contractor, CLAUDE.md sections 2-4: the 3 required documents plus the license on file (a check even when
    # the trade needs none); 6 insurance rules (end date, general liability, auto, umbrella, workers' comp, additional insured) when a
    # certificate is on file; the license end date when a license is on file; the legal name on every page.
    for s in slugs:
        H["intake"]["check"] += len(rules["required_documents"]["all"]) + 1 + (6 if doc(s, "coi") else 0) + (1 if doc(s, "license") else 0) + 1
    S["intake"]["flag"] = sum(len(v["issues"]) for v in key.values())
    # 2 certs: every field on each certificate PDF compared with the typed record; each difference is fixed by a person either way
    for s in slugs:
        if os.path.exists(p("vendors", s, "documents", "coi.pdf")):
            H["certs"]["check"] += len(rows(doc(s, "coi"), "Field"))
    diffs = sum(len(v) for v in k3e["flags"].values())
    H["certs"]["typed"] = S["certs"]["typed"] = S["certs"]["flag"] = diffs
    # 3 screen: each disclosure statement the rules check (one per disclosure code), and each distinct name searched on the exclusion list
    # once (review round 1: a screener searches a name once, however many papers carry it)
    disc_codes = [c for c in rules["controls"]["issue_codes"] if re.search(r"DISCLOS|SOLICITATION", c)]
    names = set()
    for s in slugs:
        d = read("vendors", s, "disclosures", "conflict-of-interest.md")
        if d:
            H["screen"]["check"] += len(disc_codes)
        names |= {v for v in (kv(doc(s, "w9")).get("Legal name"), kv(doc(s, "coi")).get("Insured"), kv(doc(s, "license")).get("License holder"),
                              kv(d).get("Firm"), kv(d).get("Signed by")) if v}
        names |= {r[0] for r in rows(d, "Person") if r[0] and r[0].lower() != "none"}
    H["screen"]["lookup"] = len(names) + sum(1 for line in read("company", "approved-suppliers.md").splitlines() if "| Approved |" in line)
    S["screen"]["flag"] = sum(len(v["codes"]) for v in k3c["screen"]["vendors"].values())
    # 4 chase: one follow-up per blocked or held contractor (the locked key's statuses)
    stuck = [s for s, v in key.items() if v["status"] in ("BLOCKED", "HOLD")]
    H["chase"]["write"] = S["chase"]["review"] = len(stuck)
    # 5 route: one packet per ready contractor (the locked key), signed in order by its tier's approvers. Fields typed again are counted on
    # the packet itself: a header field counts only when its value already exists word for word in the contractor's work request or vendor
    # record; each signer's role, name, and email count 3 (they're copied from the approver list)
    tiers = rules["approval_tiers"]

    def signers(s):
        amount = money(kv(doc(s, "request"))["Contract amount"])
        return len(next(t for t in tiers if t["max_amount"] is None or amount <= t["max_amount"])["approvers"])

    def typed_on(form, s, extra_source=""):
        src = {r[1] for f in (doc(s, "request"), read("vendors", s, "vendor.md")) for r in rows(f, "Field") if len(r) > 1 and r[1]}
        t = read(*form.split("/"))
        head = sum(1 for r in rows(t, "Field") if len(r) > 1 and r[1] in src)
        changed = sum(1 for r in rows(t, "What") if len(r) > 2 and r[2] and r[2] in extra_source)  # a change copied from the e-signature export
        signed = [r for r in rows(t.split("## Sign-offs", 1)[1], "#") if r[0].isdigit()] if "## Sign-offs" in t else []
        return head + changed + 3 * len(signed)

    ready = [s for s, v in key.items() if v["status"] == "READY"]
    H["route"]["form"] = len(ready)
    H["route"]["typed"] = sum(typed_on(f"vendors/{s}/packet.md", s) for s in ready)
    H["route"]["sign"] = S["route"]["sign"] = sum(signers(s) for s in ready)
    # 6 revise: an e-signature export with a requested change: read its rows, build a new version (fields typed again counted on it, as in
    # step 5, plus the change copied word for word from the export), and every sign-off again
    for s in slugs:
        for f in sorted(glob.glob(p("vendors", s, "esign-status-*.md"))):
            export = open(f, encoding="utf-8").read()
            sig = [r for r in rows(export, "#") if r[0].isdigit()]
            if any(len(r) > 3 and r[3] == "change requested" for r in sig):
                newest = sorted(glob.glob(p("vendors", s, "packet-v*.md")))
                H["revise"]["check"] += len(sig)
                H["revise"]["form"] += 1
                H["revise"]["typed"] += typed_on(os.path.relpath(newest[-1], ROOT).replace("\\", "/"), s, export) if newest else 0
                H["revise"]["sign"] += len(sig)
                S["revise"]["sign"] += len(sig)

    # Buying. 7 ask: one quote request per quote on file; the system doesn't draft these, so a person writes them either way
    quotes = sorted(glob.glob(p("projects", PROJ, "quotes", "*.md")))
    H["ask"]["write"] = S["ask"]["write"] = len(quotes)
    # 8 scope: each wall length in the request, and whether the requested bed fits
    req = read("projects", PROJ, "request.md")
    H["scope"]["check"] = len(re.findall(r"^[A-Za-z ]+ wall [A-Z]:", req, re.M)) + (1 if re.search(r"^Bed size:", req, re.M) else 0)
    S["scope"]["flag"] = len(k3a["scope"]["codes"])
    # 9 source: each picked item's lead time looked up, and its arrival worked out against the install date
    picks = [r for r in rows(read("projects", PROJ, "proposed.md"), "Line") if r[0].isdigit()]
    H["source"]["lookup"] = H["source"]["check"] = len(picks)
    S["source"]["flag"] = len(k3a["source"]["late"])
    # 10 quote: every line total recomputed; per quote the subtotal, the notes (extra charges), the valid-until date; the purchase request
    qlines = sum(len([r for r in rows(open(f, encoding="utf-8").read(), "SKU") if r[0]]) for f in quotes)
    H["quote"]["check"] = qlines + 3 * len(quotes)
    H["quote"]["form"] = H["quote"]["sign"] = S["quote"]["sign"] = 1 if quotes else 0
    S["quote"]["flag"] = sum(len(q["codes"]) for q in k3a["quote"]["quotes"].values())
    # 11 approve: width and depth on every plan line, plus finish and fabric where the plan names one
    plan = [r for r in rows(read("projects", PROJ, "partner-plan.md"), "Line") if r[0].isdigit()]
    H["approve"]["check"] = sum(2 + (r[5].lower() != "any") + (r[6].lower() != "any") for r in plan)
    S["approve"]["flag"] = len(k3a["approve"]["FAIL"]) + len(k3a["approve"]["NEEDS_PERSON"])
    # 12 change: per backorder notice, the new total, the gap to the budget, the new delivery date; a change request; its approval
    notices = [f for f in glob.glob(p("projects", PROJ, "events", "*.md")) if "backordered" in open(f, encoding="utf-8").read()]
    H["change"]["check"] = 3 * len(notices)
    H["change"]["form"] = H["change"]["sign"] = S["change"]["sign"] = len(notices)
    S["change"]["flag"] = len(k3a["change"]["codes"])
    # 13 deliver: each tracked item looked up; its arrival against the install date and its address against the order; one task per
    # exception (not counting items on hold for a change); one update to the requester when there's any exception
    po = read("projects", PROJ, "approved", "po-PQ-1042.md")
    hold = rules["projects"]["on_hold_status"]
    trk = [r for r in rows(open(sorted(glob.glob(p("projects", PROJ, "deliveries", "tracking-*.md")))[-1], encoding="utf-8").read(), "SKU") if r[0]]
    install = day(kv(req)["Install by"])
    exc = [r for r in trk if r[2] != hold and ((r[3] and day(r[3]) > install) or r[4] != kv(po)["Ship to"])]
    H["deliver"]["lookup"], H["deliver"]["check"] = len(trk), 2 * len(trk)
    H["deliver"]["task"] = S["deliver"]["task"] = len(exc)
    H["deliver"]["write"] = S["deliver"]["review"] = 1 if exc else 0
    S["deliver"]["flag"] = len(k3a["deliver"]["exceptions"])
    # 14 credit: each tracked item against the date the order promised; per supplier with an item past the rule's days, the credit math and a request
    promised = {r[0]: (r[2], r[5]) for r in rows(po, "SKU") if r[0]}
    past = rules["exceptions"]["freight_credit"]["days_past_promised"]
    late = {promised[r[0]][0] for r in trk if r[0] in promised and r[3] and r[2] != hold and (day(r[3]) - day(promised[r[0]][1])).days >= past}
    H["credit"]["check"] = len(trk) + len(late)
    H["credit"]["write"] = S["credit"]["review"] = len(late)
    # 15 match: per invoice, the order and the receipt looked up and the freight checked; per line, price and quantity against the order and
    # quantity against the receipt; Finance decides each invoice
    invs = sorted(glob.glob(p("projects", PROJ, "invoices", "*.md")))
    ilines = sum(len([r for r in rows(open(f, encoding="utf-8").read(), "SKU") if r[0]]) for f in invs)
    H["match"]["lookup"] = 2 * len(invs)
    H["match"]["check"] = 3 * ilines + len(invs)
    H["match"]["sign"] = S["match"]["sign"] = len(invs)
    S["match"]["flag"] = sum(len(v["codes"]) for v in k3a["match"]["invoices"].values())
    # 16 request: every order line over the competition threshold priced in every approved catalog; the order total against the procurement
    # types and against the funds; the request itself; its certification
    line_min = next(t for t in rules["controls"]["procurement_types"] if t.get("line_min"))["line_min"]
    big = [r for r in rows(po, "SKU") if r[0] and int(r[3]) * money(r[4]) > line_min]
    H["request"]["lookup"] = len(big) * len(glob.glob(p("projects", PROJ, "catalogs", "*.md")))
    H["request"]["check"] = 1 + (1 if read("projects", PROJ, "funding.md") else 0)
    H["request"]["form"] = H["request"]["sign"] = S["request"]["sign"] = 1 if big else 0
    S["request"]["flag"] = len(k3c["request"]["flags"])
    # 17 closeout: each running total CLAUDE.md section 11 names; a supplier's completion notice against the receipt, line by line; the summary
    # and the certificate; a reply when the notice is wrong; the certificate's signatures
    claude = read("CLAUDE.md")
    m = re.search(r"running totals for the approved order: ([^.]+)\.", claude)
    n_totals = len(re.split(r",\s*", m.group(1))) if m else 0
    m2 = re.search(r"completion certificate has (\w+) signatures", claude)
    n_sig = NUMWORDS.get(m2.group(1), 0) if m2 else 0
    receipt = sorted(glob.glob(p("projects", PROJ, "received", "receipt-*.md")))
    got = {r[0] for r in rows(open(receipt[-1], encoding="utf-8").read(), "SKU") if r[0]} if receipt else set()
    for f in glob.glob(p("projects", PROJ, "closeout", "*.md")):
        mine = [r[0] for r in rows(po, "SKU") if r[0] and r[2] == kv(open(f, encoding="utf-8").read()).get("Supplier")]
        H["closeout"]["check"] += n_totals + len(mine)
        H["closeout"]["form"] += 2
        H["closeout"]["sign"] += n_sig
        S["closeout"]["sign"] += n_sig
        if any(x not in got for x in mine):
            H["closeout"]["write"] += 1
            S["closeout"]["review"] += 1
    S["closeout"]["flag"] = 1 if k3c["closeout"]["claim"]["result"] == "CLAIM_CONTRADICTED" else 0

    F = {}
    for st in STEPS:
        for t in TYPES:
            if H[st][t]:
                F[f"bh.s.{st}.{t}.h"] = H[st][t]
            if S[st][t]:
                F[f"bh.s.{st}.{t}.s"] = S[st][t]
        F[f"bh.s.{st}.h"], F[f"bh.s.{st}.s"] = sum(H[st].values()), sum(S[st].values())
    mins = {t["id"]: t["minutes"] for t in jload("dashboard", "by-hand.json").get("types", [])}
    for t in TYPES:
        h, s_ = sum(H[st][t] for st in STEPS), sum(S[st][t] for st in STEPS)
        F[f"bh.t.{t}.h"], F[f"bh.t.{t}.s"] = h, s_
        F[f"bh.m.{t}.h"], F[f"bh.m.{t}.s"] = rnd(h * mins.get(t, 0)), rnd(s_ * mins.get(t, 0))
    F["bh.same"] = sum(min(H[st][t], S[st][t]) for st in STEPS for t in TYPES)  # touches a person makes either way
    for side in ("h", "s"):
        F[f"bh.total.{side}"] = sum(F[f"bh.t.{t}.{side}"] for t in TYPES)
        F[f"bh.min.{side}"] = sum(F[f"bh.m.{t}.{side}"] for t in TYPES)
        F[f"bh.hours.{side}"] = rnd(F[f"bh.min.{side}"] / 60)
    F["bh.gone"], F["bh.new"] = F["bh.total.h"] - F["bh.same"], F["bh.total.s"] - F["bh.same"]
    suite = jload("tests", "suite.json").get("checks", {})
    F["c.suite"] = sum(suite.values())
    for f, n in suite.items():
        if f not in BUILD_RUNS:
            F["c.suite." + f[len("check_"):-3]] = n
    return F, {"H": H, "S": S, "mins": mins, "suite": suite}


# ------------------------------------------------------------- the page -------------------------------------------------------------
def section(page_html):
    m = re.search(r'<section data-tab="byhand"[^>]*>(.*?)</section>', page_html, re.S)
    return m.group(0) if m else ""


def tags(fragment, prefix=""):
    out = {}
    for k, v in re.findall(r'data-k="([^"]+)">([^<]*)<', fragment):
        if k.startswith(prefix):
            out.setdefault(k, []).append(v)
    return out


def visible(fragment):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", fragment, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t))).strip()


def attrs(tag_html):
    return dict(re.findall(r'([\w-]+)="([^"]*)"', tag_html))


_BROWSER = []


def browser():
    if not _BROWSER:
        found = None
        for b in BROWSERS:
            if os.path.exists(b):
                with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as prof:
                    r = subprocess.run([b, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={prof}", "--dump-dom",
                                        "data:text/html,<p id=probe>ok</p>"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
                if 'id="probe"' in r.stdout:
                    found = b
                    break
        _BROWSER.append(found)
    return _BROWSER[0]


def dump(page, frag):
    b = browser()
    if not b or not os.path.exists(page):
        return ""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as prof:
        r = subprocess.run([b, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={prof}", "--virtual-time-budget=4000",
                            "--dump-dom", "file:///" + page.replace("\\", "/") + frag], capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=120)
    return r.stdout


# ------------------------------------------------------------- the checks -------------------------------------------------------------
def f1(F, page_html):
    sec = section(page_html)
    got = tags(sec, "bh.")
    want = {k: v for k, v in F.items() if k.startswith("bh.")}
    twice = sorted(k for k, v in got.items() if len(set(v)) > 1)
    wrong = sorted((k, got[k][0], want[k]) for k in got if k in want and num(got[k][0]) != want[k])
    missing, extra = sorted(set(want) - set(got)), sorted(set(got) - set(want))
    steps = re.findall(r'data-bh-step="([^"]+)"', sec)
    types = re.findall(r'data-bh-type="([^"]+)"', sec)
    per = ", ".join(f"{t} {F.get(f'bh.t.{t}.h')}/{F.get(f'bh.t.{t}.s')}" for t in TYPES)
    ok = sec and len(got) >= 40 and not twice and not wrong and not missing and not extra and steps == STEPS and types == TYPES
    rec(ok, "F1 every count on the tab recounts from the raw records",
        f"{len(got)} tagged numbers on the tab, {len(want)} recounted; wrong {wrong[:4]}; missing {missing[:4]}; not recounted {extra[:4]}; "
        f"shown twice with different values {twice[:3]}; steps {len(steps)} (want {len(STEPS)}, in order: {steps == STEPS}); kinds of touch {len(types)} "
        f"(in order: {types == TYPES}); by hand {F.get('bh.total.h')} touches, with the system {F.get('bh.total.s')}; by kind (by hand/with): {per}")


def f2(F, page_html):
    sec = section(page_html)
    vis = visible(sec)
    model = jload("dashboard", "by-hand.json")
    mtypes = model.get("types", [])
    probs = []
    if [t.get("id") for t in mtypes] != TYPES:
        probs.append(f"model kinds {[t.get('id') for t in mtypes]}")
    if "not measured" not in model.get("status", ""):
        probs.append("model status doesn't say 'not measured'")
    bad_basis = [t.get("id") for t in mtypes if not (("not measured" in t.get("basis", "")) or t.get("basis", "").startswith("Source:"))]
    bad_min = [t.get("id") for t in mtypes if not isinstance(t.get("minutes"), (int, float)) or t.get("minutes") <= 0]
    inputs = {a.get("data-min"): a.get("value") for a in (attrs(x) for x in re.findall(r"<input[^>]*>", sec)) if a.get("data-min")}
    bad_in = [t["id"] for t in mtypes if t["id"] not in inputs or float(inputs[t["id"]]) != float(t["minutes"])]
    basis = dict(re.findall(r'<td class="basis" data-basis="(\w+)">([^<]*)</td>', sec))
    bad_cell = [t["id"] for t in mtypes if html.unescape(basis.get(t["id"], "")) != t.get("basis")]
    over = [m.group(0) for pat in OVERCLAIM for m in re.finditer(pat, vis, re.I)]
    lab = {"illustrative": "illustrative" in vis.lower(), "not measured": bool(re.search(r"not measure", vis, re.I)),
           "estimate": "estimate" in vis.lower()}
    ok = sec and not probs and not bad_basis and not bad_min and not bad_in and not bad_cell and not over and all(lab.values())
    rec(ok, "F2 labeled illustrative; every minute is an assumption with its basis, never a measurement",
        f"words on the tab {lab}; {len(mtypes)} kinds in dashboard/by-hand.json, basis missing or unlabeled {bad_basis}, minutes not > 0 {bad_min}; "
        f"{len(inputs)} minute inputs on the page, differ from the file {bad_in}; {len(basis)} basis cells, differ {bad_cell}; "
        f"overclaims {over[:4]}; {probs}")


def f3(F, page):
    dom = dump(page, "#tab=byhand")
    sec = section(dom)
    body = re.search(r"<body[^>]*>", dom)
    b = attrs(body.group(0)) if body else {}
    got = tags(sec, "bh.")
    want = {k: v for k, v in F.items() if k.startswith(("bh.m.", "bh.min.", "bh.hours."))}
    wrong = sorted((k, got.get(k), v) for k, v in want.items() if not got.get(k) or num(got[k][-1]) != v)
    js_on = 'data-bh-js="1"' in (re.search(r"<section[^>]*>", sec).group(0) if sec else "")
    shown = 'class="on"' in (re.search(r"<section[^>]*>", sec).group(0) if sec else "") or "class=on" in sec[:200]
    nav = bool(re.search(r'<button[^>]*data-for="byhand"', dom))
    ok = bool(dom) and sec and js_on and shown and nav and b.get("data-errors") == "0" and not wrong
    rec(ok, "F3 the tab renders, and the page's own math matches the recount",
        f"headless {os.path.basename(browser() or 'none')}: tab button {nav}, tab shown at #tab=byhand {shown}, script ran {js_on}, "
        f"script errors {b.get('data-errors')}; {len(want)} minute totals recomputed by the page, differ from the recount {wrong[:4]}; "
        f"by hand {F.get('bh.min.h')} min (about {F.get('bh.hours.h')} h), with the system {F.get('bh.min.s')} min (about {F.get('bh.hours.s')} h)")


def f4(F, page_html):
    slugs = sorted(d for d in os.listdir(p("vendors")) if os.path.isdir(p("vendors", d)))
    drafts = [f for s in slugs for f in glob.glob(p("vendors", s, "drafts", "*.md"))
              if re.search(r"\|\s*Status\s*\|\s*DRAFT, not sent\s*\|", open(f, encoding="utf-8").read())]
    drafts += [f for f in glob.glob(p("projects", PROJ, "out", "drafts", "*.md")) + glob.glob(p("projects", PROJ, "controls", "drafts", "*.md"))
               + glob.glob(p("projects", PROJ, "exceptions", "credit-request-*.md")) if "not sent" in open(f, encoding="utf-8").read().splitlines()[0]]
    key = jload("tests", "answer-key.json")["vendors"]
    k3a, k3c, k3e = jload("tests", "answer-key-3a.json"), jload("tests", "answer-key-3c.json"), jload("tests", "answer-key-3e.json")
    problems = (sum(len(v["issues"]) for v in key.values()) + len(k3a["scope"]["codes"]) + len(k3a["source"]["late"])
                + sum(len(q["codes"]) for q in k3a["quote"]["quotes"].values()) + len(k3a["approve"]["FAIL"]) + len(k3a["approve"]["NEEDS_PERSON"])
                + len(k3a["change"]["codes"]) + len(k3a["deliver"]["exceptions"]) + sum(len(v["codes"]) for v in k3a["match"]["invoices"].values())
                + sum(len(v["codes"]) for v in k3c["screen"]["vendors"].values()) + len(k3c["request"]["flags"])
                + (1 if k3c["closeout"]["claim"]["result"] == "CLAIM_CONTRADICTED" else 0))
    diffs = sum(len(v) for v in k3e["flags"].values())
    blank = 0
    for f in glob.glob(p("vendors", "*", "packet*.md")):
        t = open(f, encoding="utf-8").read()
        for line in t.split("## Sign-offs", 1)[1].splitlines() if "## Sign-offs" in t else []:
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(c) == 7 and c[0].isdigit() and not c[4] and not c[6]:
                blank += 1
    lines_ = sum(len(re.findall(r"^(?:Approved by|Signature): _{3,}", open(f, encoding="utf-8").read(), re.M))
                 for f in glob.glob(p("projects", PROJ, "**", "*.md"), recursive=True))
    invoices = len(glob.glob(p("projects", PROJ, "invoices", "*.md")))
    tasks = len(re.findall(r"^\|\s*T\d+\s*\|", read("projects", PROJ, "out", "tasks.md"), re.M))
    quotes = len(glob.glob(p("projects", PROJ, "quotes", "*.md")))
    page = tags(page_html)
    on_page = {k: num(page[k][0]) if k in page else None for k in ("g.drafts", "i.total")}
    checks = {"drafts a person reviews = unsent drafts on file": (F["bh.t.review.s"], len(drafts)),
              "the page's drafts tile agrees": (on_page["g.drafts"], len(drafts)),
              "flags a person reads = planted problems + certificate differences": (F["bh.t.flag.s"], problems + diffs),
              "the page's problems tile agrees": (on_page["i.total"], problems),
              "sign-offs with the system = blank sign-off lines on file + invoices": (F["bh.t.sign.s"], blank + lines_ + invoices),
              "sign-offs by hand = with the system": (F["bh.t.sign.h"], F["bh.t.sign.s"]),
              "supplier tasks = tasks on file, both ways": ((F["bh.t.task.h"], F["bh.t.task.s"]), (tasks, tasks)),
              "emails still written by a person = quote requests": (F["bh.t.write.s"], quotes),
              "fields typed with the system = certificate differences": (F["bh.t.typed.s"], diffs)}
    bad = [k for k, (a, b) in checks.items() if a != b]
    rec(not bad and drafts and problems, "F4 what's left for people matches the records and the rest of the dashboard",
        "; ".join(f"{k}: {a} vs {b}" for k, (a, b) in checks.items()) + f"; differ {bad}")


def f5(F, page_html):
    suite = jload("tests", "suite.json").get("checks", {})
    total = sum(suite.values())
    on_disk = sorted(os.path.basename(f) for f in glob.glob(p("tests", "check_*.py")))
    in_ci = sorted(set(re.findall(r"tests/(check_\w+\.py)", read(".github", "workflows", "checks.yml"))))
    real = {}
    for f in on_disk:
        if f == "check_phase3f.py":
            real[f] = N_CHECKS
        elif f == "check_phase3b.py":
            m = re.search(r"len\(results\) == (\d+)", read("tests", f))
            real[f] = int(m.group(1)) if m else None
        else:
            args = (["--root", ROOT] if f in ("check_phase3a.py", "check_phase3c.py", "check_phase3d.py") else []) \
                + (["--skip-old-phases"] if f in ("check_phase3c.py", "check_phase3d.py") else []) \
                + (["--copy"] if COPY and f in BUILD_RUNS else [])
            r = subprocess.run([sys.executable, "-I", "-X", "utf8", p("tests", f)] + args, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", cwd=ROOT, timeout=900)
            m = re.findall(r"^RESULT: (\d+) of (\d+) checks PASS", r.stdout, re.M)
            real[f] = int(m[-1][1]) if m else None
    off = {f: (suite.get(f), real.get(f)) for f in set(suite) | set(real) if suite.get(f) != real.get(f)}
    page = tags(page_html, "c.suite")
    page_off = {k: v for k, v in page.items() if num(v[0]) != F.get(k)}
    readme = [int(x) for x in re.findall(r"\b(\d+) pass/fail checks\b", read("README.md"))]
    docs = {f: re.findall(r"\b(\d+) of (\d+) checks\b", re.sub(r"<[^>]+>", " ", read(*f.split("/")))) for f in ("docs/explainer.md", "docs/diagram.html")}
    doc_off = {f: v for f, v in docs.items() if not v or any(int(a) != total or int(b) != total for a, b in v)}
    ok = (suite and on_disk == sorted(suite) == in_ci and not off and "c.suite" in page and not page_off
          and readme and all(x == total for x in readme) and not doc_off)
    rec(ok, "F5 one check count everywhere: the list, the scripts, CI, the dashboard, README, explainer, diagram",
        f"tests/suite.json lists {len(suite)} scripts, {total} checks; on disk {len(on_disk)}; run by CI {len(in_ci)}; differ from what each script "
        f"really runs {off}; dashboard c.suite tags {sorted(page)} differ {page_off}; README says {readme}; explainer and diagram say "
        f"{ {f: v for f, v in docs.items()} }, off {sorted(doc_off)}")


def f6():
    t = read("README.md")
    m = re.search(r"git history, which starts (\d+)/(\d+)/(\d{4}), has (\d+) commits on (\d+) days through commit ([0-9a-f]{7,40})", t)
    if not m:
        rec(False, "F6 the README's how-it-was-built line matches git", "no 'git history, which starts M/D/YYYY, has N commits on D days through commit HASH' line")
        return
    start = f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    n, d, h = int(m.group(4)), int(m.group(5)), m.group(6)
    git = lambda *a: subprocess.run(["git", "-C", ROOT] + list(a), capture_output=True, text=True, encoding="utf-8", errors="replace")
    c = git("rev-list", "--count", h)
    dates = git("log", "--format=%ad", "--date=short", h).stdout.split()
    real_n = int(c.stdout.strip()) if c.returncode == 0 and c.stdout.strip().isdigit() else None
    ok = real_n == n and len(set(dates)) == d and dates and min(dates) == start
    rec(ok, "F6 the README's how-it-was-built line matches git",
        f"README: starts {start}, {n} commits on {d} days through {h}; git: {real_n} commits on {len(set(dates))} days "
        f"({sorted(set(dates))}), first {min(dates) if dates else 'none'}{'' if c.returncode == 0 else '; git: ' + (c.stderr.strip()[:120])}")


def finish():
    n = sum(1 for ok, _ in results if ok)
    print(f"\nRESULT: {n} of {len(results)} checks PASS")
    return 0 if n == len(results) == N_CHECKS else 1


def main():
    if not os.path.isdir(p("vendors")):
        print(f"FAIL - root {ROOT} has no vendors/ folder")
        return 1
    page = p("dashboard", "index.html")
    page_html = open(page, encoding="utf-8").read() if os.path.exists(page) else ""
    try:
        F, _ = recount()
    except Exception as e:  # a record can't be read: every check fails rather than guessing
        for c in ("F1", "F2", "F3", "F4", "F5"):
            rec(False, f"{c} (records unreadable)", repr(e)[:200])
        f6()
        return finish()
    for f, args in ((f1, (F, page_html)), (f2, (F, page_html)), (f3, (F, page)), (f4, (F, page_html)), (f5, (F, page_html)), (f6, ())):
        try:
            f(*args)
        except Exception as e:
            rec(False, f"{f.__name__.upper()} crashed", repr(e)[:300])
    return finish()


# ------------------------------------------------------------- self-test -------------------------------------------------------------
def selftest():
    def sub(rel, old, new):
        def f(cp):
            fp = os.path.join(cp, *rel.split("/"))
            t = open(fp, encoding="utf-8").read()
            if old not in t:
                raise SystemExit(f"self-test setup: '{old[:50]}' not found in {rel}")
            open(fp, "w", encoding="utf-8").write(t.replace(old, new, 1))
        return f

    def retag(cp):  # F1: one step's count on the page is one too high
        fp = os.path.join(cp, "dashboard", "index.html")
        t = open(fp, encoding="utf-8").read()
        t2 = re.sub(r'(data-k="bh\.s\.intake\.check\.h">)(\d+)', lambda m: m.group(1) + str(int(m.group(2)) + 1), t, count=1)
        if t2 == t:
            raise SystemExit("self-test setup: bh.s.intake.check.h not found")
        open(fp, "w", encoding="utf-8").write(t2)

    def blank_basis(cp):  # F2: one kind of touch loses its "not measured" label
        fp = os.path.join(cp, "dashboard", "by-hand.json")
        m = json.load(open(fp, encoding="utf-8"))
        m["types"][2]["basis"] = "Typical time"
        json.dump(m, open(fp, "w", encoding="utf-8"), indent=1)

    def page_minutes(cp):  # F3: the page's minute input differs from the numbers it shows, so its own math disagrees
        fp = os.path.join(cp, "dashboard", "index.html")
        t = open(fp, encoding="utf-8").read()
        t2 = re.sub(r'(<input[^>]*data-min="check"[^>]*value=")([^"]+)(")', r"\g<1>3\g<3>", t, count=1)
        if t2 == t:
            raise SystemExit("self-test setup: the check minutes input not found")
        open(fp, "w", encoding="utf-8").write(t2)

    def extra_draft(cp):  # F4: one more unsent draft on file than the tab counts
        fp = os.path.join(cp, "projects", PROJ, "out", "drafts", "update-2026-11-13.md")
        open(fp, "w", encoding="utf-8").write("*Draft, not sent. Planted by the self-test.*\n")

    def readme_count(cp):  # F5: the README keeps an old check count
        fp = os.path.join(cp, "README.md")
        t = open(fp, encoding="utf-8").read()
        t2 = re.sub(r"\b\d+ pass/fail checks\b", "79 pass/fail checks", t, count=1)
        if t2 == t:
            raise SystemExit("self-test setup: README check count not found")
        open(fp, "w", encoding="utf-8").write(t2)

    def readme_commits(cp):  # F6: the README's commit count is off
        fp = os.path.join(cp, "README.md")
        t = open(fp, encoding="utf-8").read()
        t2 = re.sub(r"(git history, which starts \S+, has )(\d+)( commits)", lambda m: m.group(1) + str(int(m.group(2)) + 3) + m.group(3), t, count=1)
        if t2 == t:
            raise SystemExit("self-test setup: README git line not found")
        open(fp, "w", encoding="utf-8").write(t2)

    breaks = [("F1", "a step's count off by one on the page", retag), ("F2", "a minute value with no 'not measured' label", blank_basis),
              ("F3", "a minute input that disagrees with the totals shown", page_minutes), ("F4", "an unsent draft the tab doesn't count", extra_draft),
              ("F5", "the README keeps the old check count", readme_count), ("F6", "the README's commit count is off", readme_commits)]
    caught = 0
    for target, what, plant in breaks:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            cp = os.path.join(tmp, "Onboarding-Demo")
            shutil.copytree(ROOT, cp, ignore=shutil.ignore_patterns("__pycache__"))
            try:
                plant(cp)
            except SystemExit as e:
                print(f"SETUP FAIL - {target}: {e}")
                continue
            r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(cp, "tests", "check_phase3f.py"), "--root", cp, "--copy"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
            hit = any(line.startswith(f"FAIL - {target} ") for line in r.stdout.splitlines())
            caught += hit
            print(f"{'CAUGHT' if hit else 'MISSED'} - {target}: {what} (exit {r.returncode})")
    print(f"\nSELF-TEST: {caught} of {len(breaks)} planted breaks caught by the check they target")
    return 0 if caught == len(breaks) else 1


if __name__ == "__main__":
    if "--facts" in sys.argv:
        print(json.dumps(recount()[0], sort_keys=True))
        sys.exit(0)
    sys.exit(selftest() if "--selftest" in sys.argv else main())
