"""Phase 3b acceptance check: the show-and-tell pieces (dashboard, one-page diagram, 2-minute video script, explainer).

Written 11/6/2026 before dashboard/build.py, tools/render.py, or any Phase 3b document existed. It never imports the
builder: it recounts every number from the records its own way and compares. Fake data only.

    python -I -X utf8 tests/check_phase3b.py               B1-B9, prints what it counted, exit 1 on any FAIL
    python -I -X utf8 tests/check_phase3b.py --selftest    plant one break per check in a temp copy; each must FAIL its own check

Options: --root DIR (check a copy) · --copy (the older checks are told they run on a copy)

How the dashboard proves its numbers (the contract the builder must meet):
- every number in a tile or table sits in <span data-k="key">; the key must be one this check recounts, with the same value;
- a quote from a record sits in an element with data-src="path" and must appear word for word in that file;
- a whole record shown as evidence sits in <pre data-file="path"> and must equal the file;
- identifiers with digits (SKUs, invoice, quote, order, task IDs, unit names) sit in <span class="id">;
- anything else with a digit inside a [data-audit] area is untagged, and fails.
"""
import csv
import datetime as dt
import glob
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
COPY = "--copy" in sys.argv
ROOT = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.dirname(HERE)
EXPIRY_WINDOW = 60  # the dashboard lists insurance and licenses that ended, or end within this many days of the demo date
SKILLS = ["intake", "chase", "route", "status", "scope", "source", "quote", "approve", "change", "deliver", "match",
          "screen", "request", "closeout"]  # Phase 3c added the last three (11/6)
TABS = ["overview", "onboarding", "buying", "checks", "audit", "map"]
ACT_OUT = {"scope_brief": "brief.json", "source_check": "source.json", "quote_compare": "quotes.json",
           "product_approval": "approval.json", "change_request": "change-request-CR-001.json",
           "delivery_exceptions": "deliveries.json", "invoice_match": "match.json"}
CTL_OUT = {"screen": "controls/supplier-screen.json", "approval_request": "projects/unit-4b/controls/approval-request.json",
           "closeout": "projects/unit-4b/controls/contract-summary.json"}  # Phase 3c (11/6): outputs outside Phase 3a's out/
EXC_OUT = {"packet_revision": "vendors/skyquay-lift-fire/revision.json", "freight_credit": "projects/unit-4b/exceptions/freight-credit.json"}  # Phase 3d (11/8)
BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
URL = re.compile(r"\bhttps?://|\bwww\.|//cdn|@import|\bfetch\(|XMLHttpRequest|WebSocket|\bsrc=[\"']//", re.I)
OVERCLAIM = [r"\bI (?:coded|programmed)\b", r"\bI wrote (?:the|all the|all of the|every line of) code\b", r"\bin production\b",
             r"\benterprise[- ]grade\b", r"\bat scale\b", r"\bself-improving\b", r"\bguarantee",
             r"\b(?:used|in use|deployed|running|live) (?:by|with|at) (?:real|actual)\b", r"\bsaves? (?:\S+ )?hours\b"]
NUMWORDS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen "
                                       "fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
STAMP = re.compile(r"\bT?\d{2}:\d{2}:\d{2}\b")
IDTOK = re.compile(r"\b(?=[\w-]*[A-Za-z])(?=[\w-]*\d)[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+\b|\b[A-Za-z]+\d+[A-Za-z0-9]*\b|\b\d+[A-Za-z]+\b")
NUM = re.compile(r"(?<![\w.])\$?\d[\d,]*(?:\.\d+)?")
ID_OK = re.compile(r"^(?:[A-Z]{1,5}-[A-Z0-9-]+|T\d+|[A-Z]\d+[a-z]?|Unit \w+|unit-\w+|Phase \w+)$")
results = []


def rec(ok, name, counted):
    ok = bool(ok)
    results.append((ok, name))
    print(f"{'PASS' if ok else 'FAIL'} - {name} - {counted}")


def p(*a):
    return os.path.join(ROOT, *a)


def read(*a):
    f = p(*a)
    return open(f, encoding="utf-8").read() if os.path.exists(f) else ""


def jload(*a):
    t = read(*a)
    return json.loads(t) if t else {}


def fields(t):
    """'| Field | Value |' rows and 'Key: value' lines -> dict (first wins)."""
    out = {}
    for line in t.splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", line) or re.match(r"^([A-Z][A-Za-z ,()/'-]*?):[ \t]*(.*)$", line)
        if m and m.group(1) not in out:
            out[m.group(1)] = m.group(2).strip()
    return out


def money(s):
    return int(re.sub(r"[^\d]", "", s))


def day(s):
    return dt.date.fromisoformat(s.strip()[:10])


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest() if os.path.exists(path) else "missing"


def norm(t):
    return re.sub(r"\s+", " ", t.replace("**", "").replace("\r", "")).strip()


# ------------------------------------------------------------------ HTML ------------------------------------------------------------------
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Node:
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent, self.kids = tag, attrs, parent, []


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, {k: (v or "") for k, v in attrs}, self.cur)
        self.cur.kids.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.kids.append(Node(tag, {k: (v or "") for k, v in attrs}, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, d):
        self.cur.kids.append(d)


def parse(html_text):
    t = Tree()
    t.feed(html_text)
    return t.root


def walk(n):
    yield n
    for k in n.kids:
        if isinstance(k, Node):
            yield from walk(k)


def text(n, skip=None):
    out = []
    for k in n.kids:
        if isinstance(k, str):
            out.append(k)
        elif not (skip and skip(k)) and k.tag not in ("script", "style"):
            out.append(text(k, skip))
    return "".join(out)


def raw_text(n):
    return "".join(k if isinstance(k, str) else raw_text(k) for k in n.kids)


def classes(n):
    return n.attrs.get("class", "").split()


def num_of(s):
    s = s.strip().replace("\u2212", "").lstrip("+-").replace("$", "").replace(",", "")
    return int(s) if re.fullmatch(r"\d+", s) else None


# ------------------------------------------------------------- recount -------------------------------------------------------------
def checks_run():
    """Run the three older checks once (B7 and the dashboard's Checks tab both use these numbers)."""
    out = {}
    for tag, f in (("p1", "check_phase1.py"), ("p2", "check_phase2.py"), ("p3a", "check_phase3a.py"), ("p3c", "check_phase3c.py"),
                   ("p3d", "check_phase3d.py")):
        cmd = [sys.executable, "-I", "-X", "utf8", p("tests", f)] + (["--root", ROOT] if f in ("check_phase3a.py", "check_phase3c.py", "check_phase3d.py") else []) \
            + (["--copy"] if COPY else []) + (["--skip-old-phases"] if f in ("check_phase3c.py", "check_phase3d.py") else [])
        if not os.path.exists(p("tests", f)):
            out[tag] = (None, None, 99, "missing")
            continue
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT, timeout=900)
        m = re.findall(r"^RESULT: (\d+) of (\d+) checks PASS", r.stdout, re.M)
        n, tot = (int(m[-1][0]), int(m[-1][1])) if m else (None, None)
        out[tag] = (n, tot, r.returncode, (r.stdout + r.stderr)[-300:])
    return out


def verify_chain(tool, cmd):
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", p("tools", tool), cmd], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", cwd=ROOT)
    m = re.search(r"(\d+) rows, (\d+) of (\d+) chain links verify -> OK", r.stdout)
    return (int(m.group(2)), int(m.group(1))) if m and r.returncode == 0 else (None, None)


def log_rows(name):
    t = read("audit", name)
    return list(csv.DictReader(io.StringIO(t))) if t else []


def recount(runs):
    E, info = {}, {}
    rules = jload("company", "rules.json")
    demo = day(rules["demo_date"])
    slugs = sorted(d for d in os.listdir(p("vendors")) if os.path.isdir(p("vendors", d)))
    key = jload("tests", "answer-key.json").get("vendors", {})
    intake = {s: jload("vendors", s, "intake.json") for s in slugs}
    info["slugs"], info["intake"] = slugs, intake
    info["key_agrees"] = set(slugs) == set(key) and all(intake[s].get("status") == key[s]["status"] and
                                                       sorted(intake[s].get("issues", [])) == sorted(key[s]["issues"]) for s in slugs)
    E["v.total"] = len([s for s in slugs if intake[s]])
    for st in ("READY", "HOLD", "BLOCKED"):
        E[f"v.{st}"] = sum(1 for s in slugs if intake[s].get("status") == st)
    tiers = rules["approval_tiers"]
    for s in slugs:
        amount = money(fields(read("vendors", s, "documents", "request.md"))["Contract amount"])
        tier = next(t for t in tiers if t["max_amount"] is None or amount <= t["max_amount"])
        E[f"v.{s}.amount"] = amount
        E[f"v.{s}.days"] = (demo - day(fields(read("vendors", s, "vendor.md"))["Submitted"])).days
        E[f"v.{s}.issues"] = len(intake[s].get("issues", []))
        E[f"v.{s}.approvers"] = len(tier["approvers"])
        if tier["approvers"] != intake[s].get("approvers"):
            info.setdefault("approver_mismatch", []).append(s)
    # insurance and licenses that ended or end soon (read from the documents themselves)
    expiry = set()
    for s in slugs:
        for doc, fld, tag in (("coi", "Policy end", "coi"), ("license", "Expires", "lic")):
            t = read("vendors", s, "documents", doc + ".md")
            if not t:
                continue
            d = (day(fields(t)[fld]) - demo).days
            if d < 0:
                E[f"x.{s}.{tag}.ago"] = -d
                expiry.add(f"{s}:{tag}")
            elif d <= EXPIRY_WINDOW:
                E[f"x.{s}.{tag}.left"] = d
                expiry.add(f"{s}:{tag}")
    info["expiry"] = expiry

    # the furnishing project
    proj = "unit-4b"
    out = lambda f: jload("projects", proj, "out", f)
    req = fields(read("projects", proj, "request.md"))
    po = fields(read("projects", proj, "approved", "po-PQ-1042.md"))
    brief, src, quotes, appr = out("brief.json"), out("source.json"), out("quotes.json"), out("approval.json")
    cr, dlv, mt = out("change-request-CR-001.json"), out("deliveries.json"), out("match.json")
    budget, committed = money(req["Budget"]), money(po["Total"])
    E.update({"p.budget": budget, "p.committed": committed, "p.headroom": budget - committed,
              "p.cr_delta": cr["delta"], "p.cr_total": cr["new_total"], "p.cr_over": cr["over_by"]})
    info["cr_math"] = committed + cr["delta"] == cr["new_total"] and cr["new_total"] - budget == cr["over_by"]
    notice = fields(read("projects", proj, "events", "2026-11-07-backorder.md"))
    E["p.backorder_late"] = (day(re.search(r"new ship date (\S+)", notice["Notice"]).group(1)) - day(req["Install by"])).days
    pr = rules["projects"]
    E["p.queen_needs"] = pr["bed_widths_in"]["queen"] + 2 * pr["bed_side_clearance_in"]
    E["p.king_needs"] = pr["bed_widths_in"][brief["bed_requested"]] + 2 * pr["bed_side_clearance_in"]
    E["p.wall"] = brief["wall_in"]
    E["p.sofa_late"] = next(iter(src["late"].values()))["days_late"]
    E["p.bed_late"] = next(iter(dlv["days_late"].values()))
    E["p.freight_hidden"] = sum(q["freight"] for q in quotes["quotes"].values() if "HIDDEN_FREIGHT" in q["codes"])
    E["p.exc"] = len(dlv["exceptions"])
    E["p.tasks"] = dlv["tasks"]
    held = {k: v for k, v in mt["invoices"].items() if v["result"] == "HOLD"}
    E["p.inv_hold"] = len(held)
    h = next(iter(held.values()))
    E.update({"p.inv_billed": h["billed"], "p.inv_expected": h["expected"], "p.inv_diff": h["difference"]})
    info["inv_due_ok"] = all(money(fields(read("projects", proj, "invoices", k + ".md"))["Total due"]) == v["billed"] for k, v in held.items())
    E["p.inv_match_total"] = sum(money(fields(read("projects", proj, "invoices", k + ".md"))["Total due"])
                                 for k, v in mt["invoices"].items() if v["result"] == "MATCH")

    # Phase 3c records (11/6): screens, the approval request, the running totals, the controls log
    ctl = rules.get("controls", {})
    screens = {s: jload("vendors", s, "screen.json") for s in slugs if os.path.exists(p("vendors", s, "screen.json"))}
    areq = jload("projects", proj, "controls", "approval-request.json") or None
    csum = jload("projects", proj, "controls", "contract-summary.json") or None
    info["screens"] = screens
    ctl_codes = [c for sc in screens.values() for c in sc.get("codes", [])] + list((areq or {}).get("flags", {}).values())
    if csum and csum.get("claim", {}).get("result") == "CLAIM_CONTRADICTED":
        ctl_codes.append("CLAIM_CONTRADICTED")
    if screens:
        for r in ("CLEAR", "REVIEW", "EXCLUDED"):
            E[f"sc.{r}"] = sum(1 for sc in screens.values() if sc.get("result") == r)
        sup = (jload("controls", "supplier-screen.json") or {}).get("suppliers", {})
        E["sc.suppliers"], E["sc.sup_excluded"] = len(sup), sum(1 for v in sup.values() if v == "EXCLUDED")
    po_lines = {}
    for line in read("projects", proj, "approved", "po-PQ-1042.md").splitlines():
        c_ = [x.strip() for x in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(c_) == 6 and re.match(r"^[A-Z]{2}-", c_[0]):
            po_lines[c_[0]] = {"item": c_[1], "supplier": c_[2], "qty": int(c_[3]), "unit": money(c_[4])}
    if areq:
        E["rq.available"] = areq["available"]
        cat = {}
        for f in glob.glob(p("projects", proj, "catalogs", "*.md")):
            for line in open(f, encoding="utf-8").read().splitlines():
                c_ = [x.strip() for x in line.strip().strip("|").split("|")]
                if line.startswith("|") and len(c_) == 8 and re.match(r"^[A-Z]{2}-", c_[0]):
                    cat[c_[0]] = money(c_[6])
        for line in read("projects", proj, "controls", "approval-request.md").splitlines():
            c_ = [x.strip() for x in line.strip().strip("|").split("|")]
            if line.startswith("|") and len(c_) == 8 and c_[0] in po_lines:
                sku, pl = c_[0], po_lines[c_[0]]
                E[f"rq.{sku}.line"] = pl["qty"] * pl["unit"]
                E[f"rq.{sku}.sources"] = len([x for x in c_[3].split(",") if x.strip()])
                E[f"rq.{sku}.lowest"] = cat[c_[4].split()[0]]
                E[f"rq.{sku}.selected"] = pl["unit"]
    if csum:
        for k_, v_ in (("original", "original"), ("approved_changes", "approved_changes"), ("current", "current"), ("invoiced", "invoiced"),
                       ("approved_for_payment", "approved_for_payment"), ("paid", "paid"), ("held", "held"), ("remaining", "remaining"),
                       ("received", "lines_received"), ("lines", "lines_total")):
            E[f"co.{k_}"] = csum[v_]

    # problems caught, by cause
    onb = [c for s in slugs for c in intake[s].get("issues", [])]
    per = {"scope": list(brief["codes"]), "source": ["LATE_ITEM"] * len(src["late"]),
           "quote": [c for q in quotes["quotes"].values() for c in q["codes"]],
           "approve": list(appr["FAIL"].values()) + ["NEEDS_PERSON"] * len(appr["NEEDS_PERSON"]),
           "change": list(cr["codes"]), "deliver": list(dlv["exceptions"].values()),
           "match": [c for v in mt["invoices"].values() for c in v["codes"]]}
    buy = [c for v in per.values() for c in v]
    E.update({"i.onb": len(onb), "i.buy": len(buy), "i.total": len(onb) + len(buy) + len(ctl_codes)})
    if screens or areq or csum:
        E["i.ctl"] = len(ctl_codes)
    for c, n in Counter(onb + buy + ctl_codes).items():
        E[f"ic.{c}"] = n
    for a, v in per.items():
        E[f"pa.{a}"] = len(v)

    # decisions waiting on people, by the written rules (dashboard/README.md)
    W = {}
    role = lambda s: re.sub(r"\s*\(.*?\)", "", s.split(",", 1)[1]).strip() if "," in s else re.sub(r"\s*\(.*?\)", "", s).strip()
    for s in slugs:
        for d in sorted(glob.glob(p("vendors", s, "drafts", "*-follow-up.md"))):
            if intake[s].get("status") in ("BLOCKED", "HOLD") and not screens.get(s, {}).get("hold_followup"):
                W[f"send_followup:{s}"] = role(fields(open(d, encoding="utf-8").read())["Reviewer and sender"])
        sc = screens.get(s, {})
        if os.path.exists(p("vendors", s, "packet.md")):
            W[f"sign_packet:{s}"] = sc["approvers"][0] if sc.get("recused") else intake[s]["approvers"][0]
        if sc.get("result") == "REVIEW":
            W[f"review_disclosure:{s}"] = ctl["disclosure_reviewer"]
        if sc.get("result") == "EXCLUDED":
            W[f"review_exclusion:{s}"] = ctl["exclusion_reviewer"]
    if brief.get("status") == "NEEDS_INFO":
        W[f"answer_scope:{proj}"] = role(req["Requested by"])
    for f in sorted(glob.glob(p("projects", proj, "out", "change-request-*.json"))):
        md = open(f[:-5] + ".md", encoding="utf-8").read()
        if re.search(r"Approved by: _{3,}", md):
            W["approve_change:" + os.path.basename(f)[len("change-request-"):-5]] = json.load(open(f, encoding="utf-8"))["approvers"][0]
    for f in sorted(glob.glob(p("projects", proj, "out", "drafts", "update-*.md"))):
        W["send_update:" + os.path.basename(f)[:-3]] = pr["update_reviewer"]
    for line in read("projects", proj, "out", "tasks.md").splitlines():
        m = re.match(r"^\|\s*(T\d+)\s*\|(?:[^|]*\|){4}\s*([^|]+?)\s*\|", line)
        if m:
            W["task:" + m.group(1)] = re.sub(r"\s*\(.*?\)", "", m.group(2)).strip()
    for k, v in mt["invoices"].items():
        W[("decide_invoice:" if v["result"] == "HOLD" else "approve_payment:") + k] = mt["payment_approver"]
    if areq:
        for sku in areq.get("needs_person", []):
            W[f"justify_line:{sku}"] = ctl["justification_writer"]
        if re.search(r"Approved by: _{3,}", read("projects", proj, "controls", "approval-request.md")):
            W["certify_request:PQ-1042"] = areq["approvers"][0]
    replies = sorted(glob.glob(p("projects", proj, "controls", "drafts", "reply-*.md")))
    for f in replies:
        if "not sent" in open(f, encoding="utf-8").read().splitlines()[0]:
            W["send_reply:" + os.path.basename(f)[:-3]] = ctl["closeout_verifier"]
    exr = rules.get("exceptions", {})
    credit_drafts = sorted(glob.glob(p("projects", proj, "exceptions", "credit-request-*.md")))
    for f in credit_drafts:
        if "not sent" in open(f, encoding="utf-8").read().splitlines()[0]:
            W["send_credit:" + os.path.basename(f)[:-3]] = exr["freight_credit"]["reviewer_and_sender"]
    # Phase 3d facts, recounted from the raw records (the e-signature export; the order vs. tracking), not from the helper's output
    for s in slugs:
        exps = sorted(glob.glob(p("vendors", s, "esign-status-*.md")))
        if exps and os.path.exists(p("vendors", s, "revision.json")):
            et = open(exps[-1], encoding="utf-8").read()
            sig = [c for c in ([x.strip() for x in l.strip().strip("|").split("|")] for l in et.splitlines()) if len(c) == 6 and c[0].isdigit()]
            ask = next(int(c[0]) for c in sig if c[3] == "change requested")
            E["ex.v1_signed"] = sum(1 for c in sig if c[3] == "signed" and int(c[0]) < ask)
    if os.path.exists(p("projects", proj, "exceptions", "freight-credit.json")):
        promised = {}
        for line in read("projects", proj, "approved", "po-PQ-1042.md").splitlines():
            c_ = [x.strip() for x in line.strip().strip("|").split("|")]
            if line.startswith("|") and len(c_) == 6 and re.match(r"^[A-Z]{2}-", c_[0]):
                promised[c_[0]] = (c_[2], c_[5])
        freight = {m.group(1): money(m.group(2)) for m in re.finditer(r"^Freight ([^:]+): (\$[\d,]+)", read("projects", proj, "approved", "po-PQ-1042.md"), re.M)}
        trk = sorted(glob.glob(p("projects", proj, "deliveries", "tracking-*.md")))[-1]
        late = []
        for line in open(trk, encoding="utf-8").read().splitlines():
            c_ = [x.strip() for x in line.strip().strip("|").split("|")]
            if line.startswith("|") and len(c_) == 5 and c_[0] in promised and c_[3] and c_[2] != pr["on_hold_status"]:
                d_ = (day(c_[3]) - day(promised[c_[0]][1])).days
                if d_ >= exr["freight_credit"]["days_past_promised"]:
                    late.append((d_, promised[c_[0]][0]))
        if late:
            E["ex.credit_days"] = max(d_ for d_, _ in late)
            E["ex.credit_freight"] = freight[late[0][1]]
    info["waiting"] = W
    E["w.total"] = len(W)
    E["w.onb"] = sum(1 for k in W if k.split(":")[0] in ("send_followup", "sign_packet", "review_disclosure", "review_exclusion"))
    E["w.buy"] = E["w.total"] - E["w.onb"]
    # 11/9 department hub: each owner's count of waiting decisions, recounted from the same records (every role in people.md + the requester, 0 if none)
    roles_all = set(W.values()) | {role(req["Requested by"])} | {
        re.sub(r"\s*\(.*?\)", "", r_).strip() for r_ in re.findall(r"^\|\s*([A-Z][^|]+?)\s*\|\s*[A-Z][a-z]+ [A-Z][a-z]+\s*\|", read("company", "people.md"), re.M)}
    for r_ in roles_all:
        E["w.role." + re.sub(r"[^a-z0-9]+", "-", r_.lower()).strip("-")] = sum(1 for v in W.values() if v == r_)

    # the older checks, live
    tags = [x for x in ("p1", "p2", "p3a", "p3c", "p3d") if runs[x][2] != 99]
    for tag in tags:
        n, tot = runs[tag][0], runs[tag][1]
        if n is not None:
            E[f"c.{tag}.pass"], E[f"c.{tag}.total"] = n, tot
    if all(runs[t][0] is not None for t in tags):
        E["c.pass"] = sum(runs[t][0] for t in tags)
        E["c.total"] = sum(runs[t][1] for t in tags)

    # audit logs + guardrails
    onb_rows, proc_rows = log_rows("audit-log.csv"), log_rows("procurement-log.csv")
    ctl_rows = log_rows("controls-log.csv") if os.path.exists(p("audit", "controls-log.csv")) else []
    exc_rows = log_rows("exceptions-log.csv") if os.path.exists(p("audit", "exceptions-log.csv")) else []
    info["rows"] = (onb_rows, proc_rows, ctl_rows, exc_rows)
    E.update({"a.onb": len(onb_rows), "a.proc": len(proc_rows), "a.rows": len(onb_rows) + len(proc_rows) + len(ctl_rows) + len(exc_rows)})
    if exc_rows:
        E["a.exc"] = len(exc_rows)
        le, _ = verify_chain("exceptions.py", "verify-log")
        if le is not None:
            E["a.exc_links"] = le
    if ctl_rows:
        E["a.ctl"] = len(ctl_rows)
        lc, _ = verify_chain("controls.py", "verify-log")
        if lc is not None:
            E["a.ctl_links"] = lc
    lo, _ = verify_chain("onboard.py", "verify-audit")
    lp, _ = verify_chain("project.py", "verify-log")
    if lo is not None:
        E["a.onb_links"] = lo
    if lp is not None:
        E["a.proc_links"] = lp
    E["a.reviews"] = sum(1 for r in onb_rows + proc_rows + ctl_rows + exc_rows if r["action"] == "checker_review")
    people = re.compile(r"^(?:send|sign|approve|pay|order|place)", re.I)
    did = re.compile(r"(?<!not )\b(?:sent|signed|approved|paid|ordered)\b", re.I)
    E["g.ai_people"] = sum(1 for r in onb_rows + proc_rows + ctl_rows + exc_rows if r["actor"].endswith("-assistant")
                           and (people.search(r["action"]) or did.search(r["result"])))
    drafts = [f for s in slugs for f in glob.glob(p("vendors", s, "drafts", "*.md"))
              if re.search(r"\|\s*Status\s*\|\s*DRAFT, not sent\s*\|", open(f, encoding="utf-8").read())]
    drafts += [f for f in glob.glob(p("projects", proj, "out", "drafts", "*.md")) + glob.glob(p("projects", proj, "controls", "drafts", "*.md"))
               + glob.glob(p("projects", proj, "exceptions", "credit-request-*.md"))
               if "not sent" in open(f, encoding="utf-8").read().splitlines()[0]]
    E["g.drafts"] = len(drafts)
    blank = 0
    for s in slugs:
        t = read("vendors", s, "packet.md")
        if "## Sign-offs" in t:
            for line in t.split("## Sign-offs", 1)[1].splitlines():
                c = [x.strip() for x in line.strip().strip("|").split("|")]
                if len(c) == 7 and c[0].isdigit() and not c[4] and not c[6]:
                    blank += 1
    for f in glob.glob(p("vendors", "*", "packet-v*.md")):  # a packet's newer version after a change during sign-off (Phase 3d)
        t = open(f, encoding="utf-8").read()
        for line in t.split("## Sign-offs", 1)[1].splitlines() if "## Sign-offs" in t else []:
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            if len(c) == 7 and c[0].isdigit() and not c[4] and not c[6]:
                blank += 1
    E["g.blank"] = blank
    E["g.blank_lines"] = sum(1 for f in glob.glob(p("projects", proj, "out", "*.md"))
                             if re.search(r"Approved by: _{3,}", open(f, encoding="utf-8").read()))

    extra = {"skills": len(glob.glob(p(".claude", "skills", "*", "SKILL.md"))),
             "people": len([l for l in read("company", "people.md").splitlines() if re.match(r"^\| [A-Z]", l) and "Role" not in l]),
             "suppliers": len([l for l in read("company", "approved-suppliers.md").splitlines() if "| Approved |" in l])}
    return E, info, extra


# ------------------------------------------------------------- tracing -------------------------------------------------------------
RECORD_GLOBS = ["company/*", "vendors/*/*.md", "vendors/*/*.json", "vendors/*/documents/*.md", "vendors/*/drafts/*.md",
                "projects/*/*.md", "projects/*/*/*.md", "projects/*/*/*.json", "projects/*/out/drafts/*.md", "audit/*.csv",
                "tests/answer-key*.json", "docs/phase2-results.md", "docs/phase3a-results.md", "reviews/*.md",
                "reviews/procurement/*.md", "CLAUDE.md"]


def strip_ids(t):
    t = DATE.sub(" ", t)
    t = STAMP.sub(" ", t)
    return IDTOK.sub(" ", t)


def nums(t):
    return {num_of(m) for m in NUM.findall(strip_ids(t))} - {None}


def trace_sets(E, extra, runs):
    blob = []
    for g in RECORD_GLOBS:
        for f in glob.glob(p(*g.split("/"))):
            if os.path.isfile(f):
                blob.append(open(f, encoding="utf-8", errors="replace").read())
    allt = "\n".join(blob)
    numbers = nums(allt) | set(E.values()) | set(extra.values())
    for n, tot, _, _ in runs.values():
        numbers |= {x for x in (n, tot) if x is not None}
    dates = set(DATE.findall(allt))
    ids = set(IDTOK.findall(DATE.sub(" ", allt + "\n" + read("README.md"))))
    return numbers, dates, ids


def trace(t, sets):
    numbers, dates, ids = sets
    words = [NUMWORDS[w.lower()] for w in re.findall(r"\b[A-Za-z]+\b", t) if w.lower() in NUMWORDS]
    found = nums(t) | set(words)
    bad_n = sorted(found - numbers)
    bad_d = sorted(set(DATE.findall(t)) - dates)
    bad_i = sorted({i for i in IDTOK.findall(DATE.sub(" ", t))} - ids)
    return found, bad_n, bad_d, bad_i


def overclaims(t):
    return [m.group(0) for pat in OVERCLAIM for m in re.finditer(pat, t, re.I)]


def pdf_pages(path):
    if not os.path.exists(path):
        return 0
    return len(re.findall(rb"/Type\s*/Page(?!s)", open(path, "rb").read()))


def png_width(path):
    if not os.path.exists(path):
        return 0
    b = open(path, "rb").read(32)
    return int.from_bytes(b[16:20], "big") if b.startswith(b"\x89PNG") else 0


def newer(a, b):
    return os.path.exists(a) and os.path.exists(b) and os.path.getmtime(a) >= os.path.getmtime(b) - 1


_BROWSER = []


def _renders(b):
    """True if this browser's headless mode returns a page (11/6: headless Edge returned nothing on the author's PC)."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as prof:
        r = subprocess.run([b, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={prof}", "--dump-dom",
                            "data:text/html,<p id=probe>ok</p>"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    return 'id="probe"' in r.stdout


def browser():
    """The first installed browser whose headless mode actually renders (checked once per run)."""
    if not _BROWSER:
        _BROWSER.append(next((b for b in BROWSERS if os.path.exists(b) and _renders(b)), None))
    return _BROWSER[0]


def dump(page, frag):
    b = browser()
    if not b or not os.path.exists(page):
        return ""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as prof:  # a browser can hold its temp profile a moment after exit
        r = subprocess.run([b, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={prof}",
                            "--virtual-time-budget=4000", "--dump-dom", "file:///" + page.replace("\\", "/") + frag],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    return r.stdout


# ------------------------------------------------------------- the checks -------------------------------------------------------------
def page_facts(html_text):
    root = parse(html_text)
    tags, ids, srcs, files, audit = [], [], [], [], []
    for n in walk(root):
        if "data-k" in n.attrs:
            tags.append((n.attrs["data-k"], text(n)))
        if "id" in classes(n):
            ids.append(text(n).strip())
        if "data-src" in n.attrs:
            srcs.append((n.attrs["data-src"], text(n)))
        if n.tag == "pre" and "data-file" in n.attrs:
            files.append((n.attrs["data-file"], raw_text(n)))
        elif "data-file" in n.attrs:  # added 11/6 after the first run (stricter, not looser): a file reference must name a real file and show exactly that path
            files.append(("ref:" + n.attrs["data-file"], text(n)))
        if "data-audit" in n.attrs:
            audit.append(n)
    skip = lambda k: ("data-k" in k.attrs or "data-src" in k.attrs or "data-file" in k.attrs or "id" in classes(k))
    untagged = []
    for a in audit:
        t = STAMP.sub(" ", DATE.sub(" ", text(a, skip)))
        untagged += re.findall(r"\S*\d\S*", t)
    return root, tags, ids, srcs, files, untagged


def b1(E, info, page):
    probs = []
    if not os.path.exists(page):
        rec(False, "B1 every dashboard number recounts from the records", "dashboard/index.html missing")
        return
    root, tags, ids, srcs, files, untagged = page_facts(open(page, encoding="utf-8").read())
    wrong = [(k, v, E.get(k)) for k, v in tags if k not in E or num_of(v) != E[k]]
    seen = {k for k, _ in tags}
    absent = sorted(set(E) - seen)
    bad_ids = [i for i in ids if not ID_OK.match(i)]
    bad_src = []
    for path, t in srcs:
        f = p(*path.split("/"))
        if not os.path.exists(f) or norm(t) not in norm(open(f, encoding="utf-8").read()):
            bad_src.append((path, t[:60]))
    bad_files = []
    for path, t in files:
        if path.startswith("ref:"):
            if not os.path.isfile(p(*path[4:].split("/"))) or t.strip() != path[4:]:
                bad_files.append(path)
            continue
        f = p(*path.split("/"))
        if not os.path.exists(f) or open(f, encoding="utf-8").read().replace("\r", "").strip() != t.replace("\r", "").strip():
            bad_files.append(path)
    folders = len(info["slugs"])
    rows_v = {n.attrs["data-v"]: n.attrs.get("data-status") for n in walk(root) if "data-v" in n.attrs}
    bad_v = [s for s in info["slugs"] if rows_v.get(s) != info["intake"][s].get("status")] + [s for s in rows_v if s not in info["slugs"]]
    w_page = {n.attrs["data-w"]: n.attrs.get("data-owner") for n in walk(root) if "data-w" in n.attrs}
    bad_w = sorted(set(w_page.items()) ^ set(info["waiting"].items()))
    x_page = {n.attrs["data-x"] for n in walk(root) if "data-x" in n.attrs}
    bad_x = sorted(x_page ^ info["expiry"])
    if not info["key_agrees"]:
        probs.append("intake.json disagrees with the locked answer key")
    if info.get("approver_mismatch"):
        probs.append(f"approvers differ from the tiers: {info['approver_mismatch']}")
    if not info["cr_math"] or not info["inv_due_ok"]:
        probs.append("project math in the records doesn't add up")
    ok = (len(tags) >= 60 and not wrong and not absent and not untagged and not bad_ids and not bad_src and not bad_files
          and folders == E["v.total"] == len(rows_v) and not bad_v and not bad_w and not bad_x and not probs)
    rec(ok, "B1 every dashboard number recounts from the records",
        f"{len(tags)} tagged numbers (want 60+), {len(tags) - len(wrong)} match, wrong {wrong[:4]}; recounted keys missing from the page "
        f"{len(absent)} {absent[:6]}; untagged digits in tiles/tables {len(untagged)} {untagged[:6]}; {len(ids)} ID spans, bad {bad_ids[:3]}; "
        f"{len(srcs)} quotes, {len(srcs) - len(bad_src)} found word for word {bad_src[:2]}; {len(files)} evidence panels, "
        f"{len(files) - len(bad_files)} equal their files {bad_files[:3]}; vendor folders {folders}, dashboard vendors {E['v.total']} "
        f"(tile) / {len(rows_v)} (rows), status wrong {bad_v}; waiting on people {len(w_page)} on the page vs {len(info['waiting'])} by the "
        f"rules, differ {bad_w[:4]}; expiring list {sorted(x_page)} vs {sorted(info['expiry'])}; {probs}")


def b2(E, info, page):
    probs = []
    onb_rows, proc_rows, ctl_rows, exc_rows = info["rows"]
    html_text = open(page, encoding="utf-8").read() if os.path.exists(page) else ""
    root = parse(html_text)
    data = next((raw_text(n) for n in walk(root) if n.tag == "script" and n.attrs.get("id") == "replay-data"), "")
    ev = json.loads(data) if data.strip() else []
    want = [("onb", r) for r in onb_rows] + [("proc", r) for r in proc_rows] + [("ctl", r) for r in ctl_rows] + [("exc", r) for r in exc_rows]
    if len(ev) != len(want):
        probs.append(f"{len(ev)} events vs {len(want)} log rows")
    per = {lg: [e for e in ev if e.get("log") == lg] for lg in ("onb", "proc", "ctl", "exc")}
    for lg, rows in (("onb", onb_rows), ("proc", proc_rows), ("ctl", ctl_rows), ("exc", exc_rows)):
        for i, r in enumerate(rows):
            e = per[lg][i] if i < len(per[lg]) else {}
            if [e.get(k) for k in ("t", "actor", "subject", "action", "result")] != [r["timestamp"], r["actor"], r["vendor"], r["action"], r["result"]]:
                probs.append(f"{lg} row {i + 1} differs")
                break
    if [e.get("t") for e in ev] != sorted(e.get("t") for e in ev):
        probs.append("events not in time order")
    # the check's own replay of the logs
    status = {s: "SUBMITTED" for s in info["slugs"]}
    for r in onb_rows:
        if r["action"] == "intake":
            status[r["vendor"]] = re.search(r"status (\w+)", r["detail"]).group(1)
    bad_status = [s for s in info["slugs"] if status[s] != info["intake"][s].get("status")]
    done = {r["action"] for r in proc_rows if r["action"] in ACT_OUT}
    missing_out = [a for a in done if not os.path.exists(p("projects", "unit-4b", "out", ACT_OUT[a]))]
    done_ctl = {r["action"] for r in ctl_rows if r["action"] in CTL_OUT}
    missing_out += [a for a in done_ctl if not os.path.exists(p(*CTL_OUT[a].split("/")))]
    done_exc = {r["action"] for r in exc_rows if r["action"] in EXC_OUT}
    missing_out += [a for a in done_exc if not os.path.exists(p(*EXC_OUT[a].split("/")))]
    want_acts = set(ACT_OUT) | done_ctl | done_exc
    qrow = next((r for r in proc_rows if r["action"] == "quote_compare"), {"detail": ""})
    crow = next((r for r in proc_rows if r["action"] == "change_request"), {"detail": ""})
    if f"total ${E['p.committed']:,}" not in qrow["detail"] or f"+${E['p.cr_delta']:,}" not in crow["detail"] or f"total ${E['p.cr_total']:,}" not in crow["detail"]:
        probs.append("log details disagree with the project files")
    # the page's own replay, rendered by a headless browser at the last event and at the start
    end_dom, start_dom = parse(dump(page, f"#replay={len(ev)}")), parse(dump(page, "#replay=0"))
    rv_end = {n.attrs["data-rv"]: n.attrs.get("data-status") for n in walk(end_dom) if "data-rv" in n.attrs}
    ra_end = {n.attrs["data-ra"] for n in walk(end_dom) if "data-ra" in n.attrs and n.attrs.get("data-done") == "1"}
    rv_0 = {n.attrs["data-rv"]: n.attrs.get("data-status") for n in walk(start_dom) if "data-rv" in n.attrs}
    ra_0 = {n.attrs["data-ra"] for n in walk(start_dom) if "data-ra" in n.attrs and n.attrs.get("data-done") == "1"}
    if rv_end != {s: info["intake"][s].get("status") for s in info["slugs"]} or ra_end != want_acts:
        probs.append(f"rendered replay end: vendors {rv_end}, activities {sorted(ra_end)}")
    if set(rv_0.values()) != {"SUBMITTED"} or len(rv_0) != len(info["slugs"]) or ra_0:
        probs.append(f"rendered replay start: vendors {rv_0}, activities {sorted(ra_0)}")
    table = [n for n in walk(root) if "data-log" in n.attrs and n.tag == "tr"]
    bad_t = 0
    for n in table:
        rows = {"onb": onb_rows, "proc": proc_rows, "ctl": ctl_rows, "exc": exc_rows}.get(n.attrs["data-log"], [])
        i = int(n.attrs.get("data-i", "0"))
        cells = [norm(text(c)) for c in n.kids if isinstance(c, Node) and c.tag == "td"]
        r = rows[i - 1] if 0 < i <= len(rows) else None
        if not r or cells[:5] != [norm(r["timestamp"]), r["actor"], r["vendor"], r["action"], norm(r["result"])]:
            bad_t += 1
    chains = (E.get("a.onb_links") == len(onb_rows) and E.get("a.proc_links") == len(proc_rows) and (not ctl_rows or E.get("a.ctl_links") == len(ctl_rows))
              and (not exc_rows or E.get("a.exc_links") == len(exc_rows)))
    ok = not probs and not bad_status and not missing_out and len(table) == len(want) and not bad_t and chains and len(ev) > 0
    rec(ok, "B2 replay: one event per audit row, and replaying them ends at the records",
        f"{len(ev)} events vs {len(onb_rows)} + {len(proc_rows)} + {len(ctl_rows)} + {len(exc_rows)} log rows; own replay: vendor statuses wrong {bad_status}, "
        f"{len(done) + len(done_ctl)} of {len(want_acts)} activities and controls with output files (missing {missing_out}); rendered at the end: {len(rv_end)} vendors, "
        f"{len(ra_end)} activities done; at the start: {len(rv_0)} vendors all SUBMITTED, {len(ra_0)} done; log table {len(table)} rows, "
        f"{bad_t} differ; chains {E.get('a.onb_links')} of {len(onb_rows)} + {E.get('a.proc_links')} of {len(proc_rows)} links; {probs[:3]}")


def tree_hashes():
    out = {}
    for dp, dns, fs in os.walk(ROOT):
        dns[:] = [d for d in dns if d != "__pycache__"]
        for f in fs:
            fp = os.path.join(dp, f)
            out[os.path.relpath(fp, ROOT)] = sha(fp)
    return out


def b3(E, page):
    probs = []
    shipped = open(page, encoding="utf-8").read() if os.path.exists(page) else ""
    ext = URL.findall(shipped)
    before = tree_hashes()
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [sys.executable, "-I", "-X", "utf8", p("dashboard", "build.py"), "--out", tmp] + (["--copy"] if COPY else [])
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT, timeout=900) \
            if os.path.exists(p("dashboard", "build.py")) else None
        fresh = open(os.path.join(tmp, "index.html"), encoding="utf-8").read() if os.path.exists(os.path.join(tmp, "index.html")) else ""
    after = tree_hashes()
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    if r is None or r.returncode != 0 or not fresh:
        probs.append(f"build failed: {(r.stdout + r.stderr)[-200:] if r else 'no dashboard/build.py'}")
    stale = []
    if fresh and shipped:
        a = {k: v for k, v in page_facts(shipped)[1]}
        b = {k: v for k, v in page_facts(fresh)[1]}
        stale = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    dom = parse(dump(page, "#tab=overview"))
    body = next((n for n in walk(dom) if n.tag == "body"), Node("body", {}, None))
    tabs = sorted(n.attrs["data-tab"] for n in walk(dom) if "data-tab" in n.attrs and n.tag == "section")
    ok = (shipped and not ext and not URL.findall(fresh) and not changed and not probs and not stale
          and body.attrs.get("data-rendered") == str(len(TABS)) and body.attrs.get("data-errors") == "0" and tabs == sorted(TABS))
    rec(ok, "B3 the page is offline, read-only, current, and renders",
        f"outside loads or web addresses {len(ext)} {ext[:3]}; files changed outside the build's own output by building {len(changed)} "
        f"{changed[:4]}; shipped page vs a fresh build: {len(stale)} tagged numbers differ {stale[:4]}; headless {os.path.basename(browser() or 'none')}: "
        f"tabs {tabs}, rendered {body.attrs.get('data-rendered')}, script errors {body.attrs.get('data-errors')}; {probs}")


def doc_text_html(path):
    return re.sub(r"\s+", " ", text(parse(open(path, encoding="utf-8").read()))) if os.path.exists(path) else ""


def b4(sets, page):
    src, png, pdf = p("docs", "diagram.html"), p("docs", "diagram.png"), p("docs", "diagram.pdf")
    t = doc_text_html(src)
    missing = [s for s in ["/" + k for k in SKILLS] + ["checker", "audit log", "approve"] if s.lower() not in t.lower()]
    found, bad_n, bad_d, bad_i = trace(t, sets)
    over = overclaims(t)
    w, pages = png_width(png), pdf_pages(pdf)
    frag = lambda h: (re.search(r"<!-- DIAGRAM START -->(.*?)<!-- DIAGRAM END -->", h, re.S) or [None, None])[1]
    dg = frag(open(src, encoding="utf-8").read()) if os.path.exists(src) else None
    dp = frag(open(page, encoding="utf-8").read()) if os.path.exists(page) else None
    ok = (t and not missing and not bad_n and not bad_d and not bad_i and not over and w >= 1200 and pages == 1
          and newer(png, src) and newer(pdf, src) and dg and dg == dp and not URL.findall(open(src, encoding="utf-8").read()))
    rec(ok, "B4 one-page diagram: every skill, the checker, the audit log, the people; numbers trace",
        f"missing {missing}; {len(found)} numbers, untraced {bad_n}; dates untraced {bad_d}; IDs untraced {bad_i}; overclaims {over}; "
        f"PNG {w} px wide (want 1200+), PDF {pages} page(s) (want 1); both rendered after the source: {newer(png, src)}, {newer(pdf, src)}; "
        f"dashboard Map tab shows the same diagram: {bool(dg) and dg == dp}")


# Length cap. Was 2:00 / 300 words; raised 11/8 when the author chose the longer, more-context script ("Keep 2:33"),
# then again the same day when he asked for full context in every scene ("it can be over 2 minutes that's fine").
# 11/9: raised from 3:30 / 450 words to 4:15 / 590 when he approved script v9.4 (D151: "D151 yes, load v9.4"; 574 words, 13 beats).
MAX_SECONDS, MAX_WORDS = 255, 590
# 11/9: the spoken credit line ("I designed the process... Claude Code wrote the code") was cut at his word ("just explain that we
# can save companies a lot of time"). The no-overclaim rule still holds: the script file must still say who built what, AND the
# dashboard itself (Map tab) must carry the credit, so a viewer who opens the live demo sees it. Both are checked below.
CREDIT = ("Designed and directed by the author", "Claude Code")


def b5(sets, page):
    t = read("docs", "video-script.md")
    rows = []
    for line in t.splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(c) == 3 and re.match(r"^\d:\d\d", c[0]):
            rows.append(c)
    say = " ".join(re.sub(r"[*_\"“”]", "", r[2]) for r in rows)
    words = re.findall(r"[A-Za-z0-9$][A-Za-z0-9$,.'’%/-]*", say)
    times = [[int(a) * 60 + int(b) for a, b in re.findall(r"(\d):(\d\d)", r[0])] for r in rows]
    flat = [x for tt in times for x in tt]
    labels = re.findall(r'data-tab-label="([^"]+)"', open(page, encoding="utf-8").read()) if os.path.exists(page) else []
    no_tab = [r[0] for r in rows if not any(f"**{l}**" in r[1] for l in labels)]
    paths = [x for r in rows for x in re.findall(r"`([^`]+)`", r[1]) if "/" in x or "." in x]
    bad_paths = [x for x in paths if not os.path.exists(p(*x.split("/")))]
    found, bad_n, bad_d, bad_i = trace(say, sets)
    over = overclaims(t)
    first_ok = bool(rows) and rows[0][0].startswith("0:00") and "**Overview**" in rows[0][1] and times[0][-1] <= 10
    page_text = open(page, encoding="utf-8").read() if os.path.exists(page) else ""
    credit_on_page = all(c in page_text for c in CREDIT)
    ok = (rows and len(words) <= MAX_WORDS and flat == sorted(flat) and flat and flat[-1] <= MAX_SECONDS and first_ok and not no_tab
          and not bad_paths and not bad_n and not bad_d and not bad_i and not over and re.search(r"\bdesign", t, re.I) and credit_on_page)
    rec(ok, f"B5 video script: {MAX_SECONDS // 60}:{MAX_SECONDS % 60:02d} or less, one window, starts on the finished dashboard, numbers trace, credit on the page",
        f"{len(rows)} beats; {len(words)} spoken words (want {MAX_WORDS} or fewer): {len(words) / 150 * 60:.0f} s at 150 a minute, "
        f"{len(words) / 177 * 60:.0f} s at 177; last beat ends {flat[-1] if flat else '?'} s; first beat on the Overview tab within 10 s: {first_ok}; "
        f"beats naming no dashboard tab {no_tab}; paths missing {bad_paths}; {len(found)} numbers, untraced {bad_n}; dates {bad_d}; IDs {bad_i}; "
        f"overclaims {over}; says 'designed': {bool(re.search(r'design', t, re.I))}; dashboard carries the credit {CREDIT}: {credit_on_page}")


def b6(sets):
    md, pdf = p("docs", "explainer.md"), p("docs", "explainer.pdf")
    t = read("docs", "explainer.md")
    missing = [s for s in ["/" + k for k in SKILLS] + ["rules", "people", "checker", "audit log", "answer key"] if s.lower() not in t.lower()]
    found, bad_n, bad_d, bad_i = trace(t, sets)
    over = overclaims(t)
    pages = pdf_pages(pdf)
    words = len(re.findall(r"[A-Za-z0-9$][\w$,.'’%/-]*", t))
    ok = (t and not missing and not bad_n and not bad_d and not bad_i and not over and pages == 1 and newer(pdf, md)
          and "designed and directed" in t.lower())
    rec(ok, "B6 one-page explainer: both halves, the 5 controls, numbers trace, no overclaims",
        f"{words} words; PDF {pages} page(s) (want 1), rendered after the source: {newer(pdf, md)}; missing {missing}; {len(found)} numbers, "
        f"untraced {bad_n}; dates {bad_d}; IDs {bad_i}; overclaims {over}; 'designed and directed': {'designed and directed' in t.lower()}")


def b7(runs):
    want = {"p1": 8, "p2": 8, "p3a": 14}
    if runs.get("p3c", (None, None, 99))[2] != 99:
        want["p3c"] = 11
    if runs.get("p3d", (None, None, 99))[2] != 99:
        want["p3d"] = 12
    got = {k: runs[k][:3] for k in want}
    ok = all(got[k][0] == got[k][1] == want[k] and got[k][2] == 0 for k in want)
    rec(ok, "B7 Phases 1, 2, 3a (and 3c, 3d, without their own older-phase steps) still pass (their scans read the new files)",
        "; ".join(f"{k}: {got[k][0]} of {got[k][1]} (want {want[k]}), exit {got[k][2]}" for k in want)
        + ("" if ok else " | " + " | ".join(runs[k][3].replace("\n", " ")[-160:] for k in want if runs[k][2] != 0)))


def b8():
    revs = sorted(glob.glob(p("reviews", "phase3b", "*.md")))
    need = ["docs/video-script.md", "docs/explainer.md", "docs/diagram.html", "dashboard/build.py"]
    probs = []
    if not revs:
        probs.append("no review saved")
    else:
        t = open(revs[-1], encoding="utf-8").read()
        if not re.search(r"^Overall: PASS\b", t, re.M):
            probs.append("latest review is not 'Overall: PASS'")
        man = dict(re.findall(r"^\|\s*`([^`]+)`\s*\|\s*([0-9a-f]{64})\s*\|", t, re.M))
        for f in need:
            if f not in man:
                probs.append(f"{f} not in the review's manifest")
            elif man[f] != sha(p(*f.split("/"))):
                probs.append(f"{f} changed after the review")
    rec(not probs, "B8 fresh-eyes review saved, PASS, and nothing changed since",
        f"{len(revs)} reviews; latest {os.path.basename(revs[-1]) if revs else 'none'}; {len(need)} files in the manifest checked; {probs}")


def b9():
    t = read("README.md")
    row = next((l for l in t.splitlines() if re.match(r"^\|\s*3b\s*\|", l)), "")
    need = ["`dashboard/build.py`", "`docs/diagram.png`", "`docs/video-script.md`", "`docs/explainer.md`", "`tools/render.py`", "`tests/check_phase3b.py`"]
    rows = {}
    for l in t.splitlines():
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if l.startswith("|") and len(c) == 5:
            rows[c[0]] = c
    missing = [n for n in need if not any(k.startswith(n) for k in rows)]
    weak = [n for n in need if any(k.startswith(n) for k in rows) and not next(v for k, v in rows.items() if k.startswith(n))[4].startswith("Designed and directed")]
    over = overclaims(t)
    ok = "Built" in row and not missing and not weak and not over
    rec(ok, "B9 README: 3b built, every new piece mapped with a 'Designed and directed' line",
        f"3b row: '{row[:80]}'; {len(need) - len(missing)} of {len(need)} pieces mapped, missing {missing}; resume lines not 'Designed and directed' {weak}; overclaims {over}")


def main():
    if not os.path.isdir(p("vendors")):
        print(f"FAIL - root {ROOT} has no vendors/ folder")
        return 1
    page = p("dashboard", "index.html")
    runs = checks_run()
    try:
        E, info, extra = recount(runs)
    except Exception as e:  # a record can't be read: every check fails rather than guessing
        for b in ("B1", "B2", "B3", "B4", "B5", "B6"):
            rec(False, f"{b} (records unreadable)", repr(e)[:200])
        b7(runs), b8(), b9()
        return finish()
    sets = trace_sets(E, extra, runs)
    for f, args in ((b1, (E, info, page)), (b2, (E, info, page)), (b3, (E, page)), (b4, (sets, page)), (b5, (sets, page)),
                    (b6, (sets,)), (b7, (runs,)), (b8, ()), (b9, ())):
        try:
            f(*args)
        except Exception as e:
            rec(False, f"{f.__name__.upper()} crashed", repr(e)[:300])
    return finish()


def finish():
    n = sum(1 for ok, _ in results if ok)
    print(f"\nRESULT: {n} of {len(results)} checks PASS")
    return 0 if n == len(results) and len(results) == 9 else 1


# ------------------------------------------------------------- self-test -------------------------------------------------------------
def selftest():
    def sub(rel, old, new, count=1):
        def f(cp):
            fp = os.path.join(cp, *rel.split("/"))
            t = open(fp, encoding="utf-8").read()
            if old not in t:
                raise SystemExit(f"self-test setup: '{old[:50]}' not found in {rel}")
            open(fp, "w", encoding="utf-8").write(t.replace(old, new, count))
        return f

    def retag(cp):  # B1: the Overview's vendor tile says 9 instead of 8
        fp = os.path.join(cp, "dashboard", "index.html")
        t = open(fp, encoding="utf-8").read()
        t2 = re.sub(r'(data-k="v\.total"[^>]*>)(\d+)', lambda m: m.group(1) + str(int(m.group(2)) + 1), t, count=1)
        if t2 == t:
            raise SystemExit("self-test setup: v.total tag not found")
        open(fp, "w", encoding="utf-8").write(t2)

    def drop_event(cp):  # B2: one audit row missing from the replay
        fp = os.path.join(cp, "dashboard", "index.html")
        t = open(fp, encoding="utf-8").read()
        m = re.search(r'(<script id="replay-data" type="application/json">)(.*?)(</script>)', t, re.S)
        ev = json.loads(m.group(2))[:-1]
        open(fp, "w", encoding="utf-8").write(t[:m.start(2)] + json.dumps(ev) + t[m.end(2):])

    def touch_later(rel):
        def f(cp):
            fp = os.path.join(cp, *rel.split("/"))
            open(fp, "a", encoding="utf-8").write("\n")
            later = os.path.getmtime(fp) + 120
            os.utime(fp, (later, later))
        return f

    banned = "".join(["Cam", "eron"])  # Phase 1's banned list, spelled so this file doesn't trip that scan
    breaks = [
        ("B1", "a dashboard tile off by one", retag),
        ("B2", "one audit row left out of the replay", drop_event),
        ("B3", "an outside font loaded by the page", sub("dashboard/index.html", "</head>", '<link rel="stylesheet" href="' + "".join(["https", "://", "fonts", ".", "googleapis", ".", "com"]) + '/css2">\n</head>')),
        ("B4", "the diagram edited after its PNG and PDF were made", touch_later("docs/diagram.html")),
        ("B5", "an invented number in the narration", _plant_narration),
        ("B6", "the explainer says 'I coded it'", sub("docs/explainer.md", "designed and directed", "coded", 99)),
        ("B7", "a personal name in a new file", sub("docs/explainer.md", "# ", f"# {banned} ")),
        ("B8", "the script changed after the review", sub("docs/video-script.md", "\n", "\n\n")),
        ("B9", "README's 3b row set back to Next", _readme_next),
    ]
    caught = 0
    for target, what, plant in breaks:
        with tempfile.TemporaryDirectory() as tmp:
            cp = os.path.join(tmp, "Onboarding-Demo")
            shutil.copytree(ROOT, cp, ignore=shutil.ignore_patterns("__pycache__"))
            try:
                plant(cp)
            except SystemExit as e:
                print(f"SETUP FAIL - {target}: {e}")
                continue
            r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(cp, "tests", "check_phase3b.py"), "--root", cp, "--copy"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
            hit = any(l.startswith(f"FAIL - {target} ") for l in r.stdout.splitlines())
            caught += hit
            print(f"{'CAUGHT' if hit else 'MISSED'} - {target}: {what} (exit {r.returncode})")
    print(f"\nSELF-TEST: {caught} of {len(breaks)} planted breaks caught by the check they target")
    return 0 if caught == len(breaks) else 1


def _plant_narration(cp):
    fp = os.path.join(cp, "docs", "video-script.md")
    t = open(fp, encoding="utf-8").read()
    lines = t.splitlines()
    for i, l in enumerate(lines):
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if l.startswith("|") and len(c) == 3 and re.match(r"^\d:\d\d", c[0]):
            lines[i] = l.rstrip().rstrip("|").rstrip() + " It saved the team 4,417 dollars. |"
            break
    else:
        raise SystemExit("no narration row")
    open(fp, "w", encoding="utf-8").write("\n".join(lines) + "\n")


def _readme_next(cp):
    fp = os.path.join(cp, "README.md")
    t = open(fp, encoding="utf-8").read()
    t2 = re.sub(r"^(\|\s*3b\s*\|[^|]*\|)\s*Built[^|]*\|", r"\1 Next |", t, count=1, flags=re.M)
    if t2 == t:
        raise SystemExit("3b row not found")
    open(fp, "w", encoding="utf-8").write(t2)


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
