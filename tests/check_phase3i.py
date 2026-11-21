"""Phase 3i acceptance check: the dashboard's "Approve and watch it land" tab (working demo, sample records).

Written 11/20/2026 before the tab existed. It never imports dashboard/build.py: it reads the raw records itself, recounts
every value the tab shows, works out each problem's fingerprint its own way, and presses the tab's buttons in a headless
browser (Edge, else Chrome) on a throwaway copy of the page, with its own throwaway profile.

    python -I -X utf8 tests/check_phase3i.py              I1-I6, prints what it counted, exit 1 on any FAIL
    python -I -X utf8 tests/check_phase3i.py --selftest   plants one break per check in a temp copy; each must FAIL its own check
    python -I -X utf8 tests/check_phase3i.py --facts      print the recounted facts for the tab as JSON (Phase 3b B1 adds them)
Options: --root DIR (check a copy) · --copy (accepted for symmetry with the other checks; nothing here needs the author's machine)

The contract the page must meet (dashboard/README.md, "Rule: Approve and watch it land"):
- section[data-tab="approve"] holds one [data-ap-card] per problem, with data-fp (fingerprint), data-decider (name), data-since (date);
  inside: .ap-found, .ap-proof with two .ap-side panels (each names its file in [data-file] and quotes it in [data-src]),
  .ap-fix, and the buttons [data-ap-approve], [data-ap-reject], [data-ap-confirm] with a [data-ap-reason] box.
- [data-ap-panel] is the sample software screen: one [data-ap-rec] per card; each changed field is a [data-ap-field] with an
  .ap-before and an .ap-after value; the record carries data-state="landed" once approved.
- [data-ap-run], [data-ap-reset], [data-ap-runout] (data-found / data-new / data-decided / data-waiting), [data-ap-stuck] (one li per
  item waiting), [data-ap-msg]; the Audit log tab holds table[data-ap-log] with one tr[data-ap-row] per decision made on the page.
- Fingerprint: the first 16 hex characters of SHA-256 over the card id and each evidence line "file|field|value", joined by newlines.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.dirname(HERE)
BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
CARDS = ["owner-petrakis", "owner-haddad", "owner-coralwick", "vendor-fernhollow", "buy-keystone"]
# Real property-management and accounting products: the sample screen must not borrow a real product's name.
PRODUCTS = ["AppFolio", "Buildium", "Yardi", "Rent Manager", "Propertyware", "RealPage", "Entrata", "DoorLoop", "TenantCloud",
            "Rentvine", "ResMan", "MRI Software", "Hemlane", "Innago", "RentRedi", "Rentec", "Guesty", "Hostaway", "Turbotenant",
            "TurboTenant", "Avail.co", "Zillow Rental Manager", "QuickBooks", "Xero", "Sage Intacct", "DocuSign"]
BANNED_WORDS = [r"\bfake\b", r"\bmade[ -]up\b", r"\bdummy\b"]


# ------------------------------------------------------------- reading the records -------------------------------------------------------------
def fields(path):
    """'| Field | Value |' rows of a sample record, as a dict."""
    out = {}
    for line in open(path, encoding="utf-8").read().splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(c) == 2 and c[0] not in ("Field", "---"):
            out[c[0]] = c[1]
    return out


def table(path, first):
    """rows of a markdown table keyed by the first cell (e.g. a SKU)."""
    rows = {}
    for line in open(path, encoding="utf-8").read().splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if line.startswith("|") and c and c[0] == first:
            rows[first] = c
    return rows.get(first)


def usd(s):
    return int(re.sub(r"[^\d]", "", s))


def team(root):
    """name by role, from the two team files."""
    out = {}
    for f in ("people.md", "owner-team.md"):
        for line in open(os.path.join(root, "company", f), encoding="utf-8").read().splitlines():
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            if line.startswith("| ") and len(c) >= 2 and c[0] not in ("Role",) and not c[0].startswith("---"):
                out.setdefault(c[0], c[1])
    return out


def fingerprint(card, evidence):
    return hashlib.sha256("\n".join([card] + [f"{f}|{k}|{v}" for f, k, v in evidence]).encode("utf-8")).hexdigest()[:16]


def recount(root):
    """F: tagged facts (Phase 3b B1 adds these); C: what each card must show, from the raw records and the locked answer keys."""
    p = lambda *a: os.path.join(root, *a)
    j = lambda *a: json.load(open(p(*a), encoding="utf-8"))
    T = team(root)
    k3g, k3e, k3a = j("tests", "answer-key-3g.json"), j("tests", "answer-key-3e.json"), j("tests", "answer-key-3a.json")
    C = {}

    ag = fields(p("owners", "petrakis", "documents", "agreement.md"))
    cr = fields(p("owners", "petrakis", "documents", "county-record.md"))
    ow = fields(p("owners", "petrakis", "owner.md"))
    C["owner-petrakis"] = {
        "planted": "OWNER_NOT_ON_COUNTY_RECORD" in k3g["owners"]["petrakis"]["issues"],
        "evidence": [("owners/petrakis/documents/agreement.md", "Owner(s) named", ag["Owner(s) named"]),
                     ("owners/petrakis/documents/county-record.md", "Owner(s) of record", cr["Owner(s) of record"]),
                     ("owners/petrakis/documents/county-record.md", "Last sale recorded", cr["Last sale recorded"])],
        "sides": [[ag["Owner(s) named"]], [cr["Owner(s) of record"], cr["Last sale recorded"]]],
        "decider": T["Broker of Record"], "since": json.load(open(p("owners", "petrakis", "intake.json"), encoding="utf-8"))["date"],
        "lands": [("ap-after", "On hold")], "bought": ow["Bought the home"]}

    lease = fields(p("owners", "haddad", "tenant", "lease.md"))
    moved = fields(p("owners", "haddad", "tenant", "deposit-transfer.md"))
    d_lease, d_moved = usd(lease["Security deposit"]), usd(moved["Security deposit transferred"])
    C["owner-haddad"] = {
        "planted": "DEPOSIT_SHORT" in k3g["owners"]["haddad"]["issues"],
        "evidence": [("owners/haddad/tenant/lease.md", "Security deposit", lease["Security deposit"]),
                     ("owners/haddad/tenant/deposit-transfer.md", "Security deposit transferred", moved["Security deposit transferred"])],
        "sides": [[lease["Security deposit"]], [moved["Security deposit transferred"]]],
        "decider": T["Trust Accountant"], "since": json.load(open(p("owners", "haddad", "intake.json"), encoding="utf-8"))["date"],
        "lands": [("ap-before", f"${d_lease:,}"), ("ap-after", f"${d_moved:,}"), ("ap-after", f"${d_lease - d_moved:,}")]}

    ag2 = fields(p("owners", "coralwick", "documents", "agreement.md"))
    ach = fields(p("owners", "coralwick", "documents", "ach.md"))
    C["owner-coralwick"] = {
        "planted": "ACH_NAME_MISMATCH" in k3g["owners"]["coralwick"]["issues"],
        "evidence": [("owners/coralwick/documents/agreement.md", "Owner(s) named", ag2["Owner(s) named"]),
                     ("owners/coralwick/documents/ach.md", "Account holder name(s)", ach["Account holder name(s)"])],
        "sides": [[ag2["Owner(s) named"]], [ach["Account holder name(s)"]]],
        "decider": T["Trust Accountant"], "since": json.load(open(p("owners", "coralwick", "intake.json"), encoding="utf-8"))["date"],
        "lands": [("ap-before", "On"), ("ap-after", "Paused")]}

    typed = fields(p("vendors", "fernhollow-grounds", "documents", "coi.md"))["Policy number"]
    flag = next((f for f in k3e["flags"]["fernhollow-grounds"] if f["field"] == "Policy number"), {})
    cert = k3e["certificates"]["fernhollow-grounds"]["Policy number"]
    run_at = json.load(open(p("vendors", "fernhollow-grounds", "documents", "coi-check.json"), encoding="utf-8"))["run"]["at"][:10]
    C["vendor-fernhollow"] = {
        "planted": flag.get("certificate") == cert and flag.get("record") == typed and cert != typed,
        "evidence": [("vendors/fernhollow-grounds/documents/coi.pdf", "Policy number", cert),
                     ("vendors/fernhollow-grounds/documents/coi.md", "Policy number", typed)],
        "sides": [[cert], [typed]], "decider": T["Facilities Manager"], "since": run_at,
        "lands": [("ap-before", typed), ("ap-after", cert)]}

    inv = p("projects", "unit-4b", "invoices", "INV-KC-3307.md")
    po = p("projects", "unit-4b", "approved", "po-PQ-1042.md")
    rc = p("projects", "unit-4b", "received", "receipt-2026-11-12.md")
    li, lo, lr = table(inv, "KC-LMP-14N"), table(po, "KC-LMP-14N"), table(rc, "KC-LMP-14N")
    it = open(inv, encoding="utf-8").read()
    billed = usd(re.search(r"Total due: (\$[\d,]+)", it).group(1))
    rows = [l for l in it.splitlines() if l.startswith("| ") and not l.startswith("| SKU") and not l.startswith("|---")]
    freight = usd(re.search(r"Freight: (\$[\d,]+)", it).group(1))
    po_lines = {c[0]: c for c in ([x.strip() for x in l.strip().strip("|").split("|")] for l in open(po, encoding="utf-8") if l.startswith("| "))}
    expected = sum(int(po_lines[c[0]][3]) * usd(po_lines[c[0]][4]) for c in ([x.strip() for x in r.strip().strip("|").split("|")] for r in rows)) + freight
    q_b, pr_b, q_o, pr_o, q_r = int(li[2]), usd(li[3]), int(lo[3]), usd(lo[4]), int(lr[1])
    mk = k3a["match"]["invoices"]["INV-KC-3307"]
    C["buy-keystone"] = {
        "planted": mk["result"] == "HOLD" and set(mk["codes"]) == {"PRICE_MISMATCH", "QTY_MISMATCH"} and mk["expected"] == expected and mk["billed"] == billed,
        "evidence": [("projects/unit-4b/invoices/INV-KC-3307.md", "KC-LMP-14N", f"{q_b} x ${pr_b:,}"),
                     ("projects/unit-4b/approved/po-PQ-1042.md", "KC-LMP-14N", f"{q_o} x ${pr_o:,}"),
                     ("projects/unit-4b/received/receipt-2026-11-12.md", "KC-LMP-14N", str(q_r))],
        "sides": [[f"${billed:,}"], []], "decider": T["Finance (Controller)"],
        "since": re.search(r"Invoice date: (\d{4}-\d{2}-\d{2})", it).group(1),
        "lands": [("ap-before", f"${billed:,}"), ("ap-after", f"${expected:,}"), ("ap-after", f"${billed - expected:,}")]}

    for c in C.values():
        c["fp"] = None
    for cid in C:
        C[cid]["fp"] = fingerprint(cid, C[cid]["evidence"])
    F = {"ap.cards": len(C), "ap.haddad.lease": d_lease, "ap.haddad.moved": d_moved, "ap.haddad.short": d_lease - d_moved,
         "ap.kc.billed_qty": q_b, "ap.kc.billed_price": pr_b, "ap.kc.order_qty": q_o, "ap.kc.order_price": pr_o, "ap.kc.received": q_r,
         "ap.kc.billed": billed, "ap.kc.expected": expected, "ap.kc.diff": billed - expected}
    return F, C


# ------------------------------------------------------------- reading the page -------------------------------------------------------------
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Node:
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent, self.kids = tag, dict(attrs), parent, []


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.kids.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.kids.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, d):
        self.cur.kids.append(d)


def parse(t):
    tr = Tree()
    tr.feed(t)
    return tr.root


def walk(n):
    yield n
    for k in n.kids:
        if isinstance(k, Node):
            yield from walk(k)


def text(n):
    if isinstance(n, str):
        return n
    if n.tag in ("script", "style"):
        return ""
    return "".join(text(k) for k in n.kids)


def cls(n):
    return n.attrs.get("class", "").split()


def norm(t):
    return re.sub(r"\s+", " ", t.replace("**", "").replace("\r", "")).strip()


def find(n, pred):
    return [x for x in walk(n) if pred(x)]


def num(s):
    d = re.sub(r"[^\d]", "", s or "")
    return int(d) if d else None


# ------------------------------------------------------------- the browser run -------------------------------------------------------------
# Pressed on a copy of the page: reset, approve card 1, reject card 2 with no reason (must be refused), reject it with a reason,
# run the check again, then reload the page (same browser profile) and check that the decisions are still there, run again,
# and reset. Everything it sees goes into one JSON attribute on <body>.
DRIVER = r"""
<script>
(function(){
  var KEY='ap-check-phase', out={};
  function q(s,r){return (r||document).querySelector(s);} function qa(s,r){return [].slice.call((r||document).querySelectorAll(s));}
  function vis(e){return !!(e && e.getClientRects().length);}
  function card(id){return q('[data-ap-card="'+id+'"]');} function rec(id){return q('[data-ap-rec="'+id+'"]');}
  function snap(tag){var ro=q('[data-ap-runout]');
    out[tag]={pending:qa('[data-ap-card][data-state="pending"]').length, pendingShown:qa('[data-ap-card][data-state="pending"]').filter(vis).length,
      decided:qa('[data-ap-card]').filter(function(c){return c.getAttribute('data-state')!=='pending';}).length,
      stuck:qa('[data-ap-stuck] li').length, logRows:qa('table[data-ap-log] tr[data-ap-row]').length,
      landed:qa('[data-ap-rec][data-state="landed"]').map(function(r){return r.getAttribute('data-ap-rec');}),
      run:ro?{found:ro.getAttribute('data-found'),neu:ro.getAttribute('data-new'),decided:ro.getAttribute('data-decided'),waiting:ro.getAttribute('data-waiting'),text:ro.textContent}:null,
      msg:(q('[data-ap-msg]')||{}).textContent||''};}
  // the record's own fields as a person sees them (the status banner above them is meant to change, so it isn't compared)
  function showText(id){var r=rec(id);document.querySelector('nav button[data-for="approve"]').click();card(id).click();var t=r?q('.sw-fields',r):null;return t?t.innerText:'';}
  // for each changing field: [old value visible, new value visible]
  function fieldVis(id){showText(id);return qa('[data-ap-field]',rec(id)).filter(function(f){return q('.ap-before',f);}).map(function(f){return [vis(q('.ap-before',f)),vis(q('.ap-after',f))];});}
  try{
    var phase=sessionStorage.getItem(KEY);
    if(!phase){
      q('[data-ap-reset]').click(); snap('start');
      var ids=qa('[data-ap-card]').map(function(c){return c.getAttribute('data-ap-card');}); out.ids=ids;
      var a=ids[0], b=ids[1]; out.a=a; out.b=b;
      out.aBefore=showText(a); out.aVisBefore=fieldVis(a); q('[data-ap-approve]',card(a)).click(); out.aAfter=showText(a); out.aVisAfter=fieldVis(a); snap('approved');
      out.bBefore=showText(b); q('[data-ap-reject]',card(b)).click(); q('[data-ap-reason]',card(b)).value='';
      q('[data-ap-confirm]',card(b)).click(); snap('rejectNoReason');
      q('[data-ap-reason]',card(b)).value='Checked by phone: already settled'; q('[data-ap-confirm]',card(b)).click();
      out.bAfter=showText(b); snap('rejected');
      out.logText=qa('table[data-ap-log] tr[data-ap-row]').map(function(r){return r.textContent;});
      q('[data-ap-run]').click(); snap('run2');
      sessionStorage.setItem(KEY,'B'); sessionStorage.setItem(KEY+'-out',JSON.stringify(out)); location.reload(); return;
    }
    out=JSON.parse(sessionStorage.getItem(KEY+'-out')||'{}'); sessionStorage.removeItem(KEY);
    snap('reloaded'); out.aReload=showText(out.a); q('[data-ap-run]').click(); snap('run3');
    q('[data-ap-reset]').click(); out.aReset=showText(out.a); out.aVisReset=fieldVis(out.a); snap('reset');
  }catch(e){out.error=String(e&&e.stack||e);}
  document.body.setAttribute('data-ap-test',JSON.stringify(out));
})();
</script>
"""


def browser():
    return next((x for x in BROWSERS if os.path.exists(x)), None)


def drive(page_html):
    """Run the driver on a copy of the page; return (what it saw, the page's own script-error count)."""
    b = browser()
    if not b:
        return {"error": "no Edge or Chrome on this machine"}, None
    with tempfile.TemporaryDirectory() as tmp:
        f = os.path.join(tmp, "page.html")
        open(f, "w", encoding="utf-8").write(page_html.replace("</body>", DRIVER + "</body>", 1))
        prof = os.path.join(tmp, "profile")
        url = "file:///" + f.replace("\\", "/") + "#tab=approve"
        r = subprocess.run([b, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={prof}", "--virtual-time-budget=8000",
                            "--window-size=1440,1600", "--dump-dom", url], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    body = next((n for n in walk(parse(r.stdout)) if n.tag == "body"), None)
    if body is None:
        return {"error": "no page came back: " + (r.stderr or "")[-200:]}, None
    try:
        got = json.loads(body.attrs.get("data-ap-test") or "{}")
    except ValueError:
        got = {"error": "driver output unreadable"}
    return got, body.attrs.get("data-errors")


# ------------------------------------------------------------- the checks -------------------------------------------------------------
def run(root, page_path=None):
    res = []
    rec = lambda ok, name, detail: res.append((bool(ok), name, detail))
    page_path = page_path or os.path.join(root, "dashboard", "index.html")
    try:
        F, C = recount(root)
    except Exception as e:  # a record can't be read: every check fails rather than guessing
        for c in ("I1", "I2", "I3", "I4", "I5", "I6"):
            rec(False, f"{c} (records unreadable)", repr(e)[:200])
        return res
    html_text = open(page_path, encoding="utf-8").read() if os.path.exists(page_path) else ""
    dom = parse(html_text)
    sec = next((n for n in walk(dom) if n.tag == "section" and n.attrs.get("data-tab") == "approve"), None)
    audit = next((n for n in walk(dom) if n.tag == "section" and n.attrs.get("data-tab") == "audit"), None)
    nav = [n.attrs.get("data-for") for n in walk(dom) if n.tag == "button" and "data-for" in n.attrs]
    if sec is None:
        sec = Node("section", {}, None)
    cards = {n.attrs["data-ap-card"]: n for n in walk(sec) if "data-ap-card" in n.attrs}
    panel = next((n for n in walk(sec) if "data-ap-panel" in n.attrs), Node("div", {}, None))
    recs = {n.attrs["data-ap-rec"]: n for n in walk(panel) if "data-ap-rec" in n.attrs}

    # I1 the cards come from planted problems, and every value the tab shows recounts from the raw records
    tags = [(n.attrs["data-k"], text(n)) for n in walk(sec) if "data-k" in n.attrs]
    wrong = [(k, v, F.get(k)) for k, v in tags if k not in F or num(v) != F[k]]
    absent = sorted(set(F) - {k for k, _ in tags})
    srcs = [(n.attrs["data-src"], text(n)) for n in walk(sec) if "data-src" in n.attrs]
    bad_src = [(f, t[:40]) for f, t in srcs if not os.path.isfile(os.path.join(root, *f.split("/")))
               or norm(t) not in norm(open(os.path.join(root, *f.split("/")), encoding="utf-8").read())]
    unplanted = [c for c in CARDS if not C[c]["planted"]]
    ok = (list(cards) == CARDS and "approve" in nav and not wrong and not absent and len(tags) >= len(F) and not bad_src and srcs and not unplanted)
    rec(ok, "I1 5 cards, each a planted problem from a locked answer key; every value on the tab recounts from the records",
        f"tab in the nav {'approve' in nav}; cards {list(cards)} (want {CARDS}); planted in the answer keys {len(CARDS) - len(unplanted)} of "
        f"{len(CARDS)} {unplanted}; {len(tags)} tagged numbers, wrong {wrong[:4]}, recounted facts missing from the tab {absent[:6]}; "
        f"{len(srcs)} quotes, {len(srcs) - len(bad_src)} found word for word {bad_src[:3]}")

    # I2 each card: what was found, proof side by side (both sides name their file and quote it), the drafted fix, Approve, Reject + reason
    probs = {}
    for cid in CARDS:
        n = cards.get(cid)
        if n is None:
            probs[cid] = "missing"
            continue
        p_ = []
        found = [x for x in walk(n) if "ap-found" in cls(x) and norm(text(x))]
        fix = [x for x in walk(n) if "ap-fix" in cls(x) and norm(text(x))]
        sides = [x for x in walk(n) if "ap-side" in cls(x)]
        if not found:
            p_.append("no 'found' line")
        if not fix:
            p_.append("no drafted fix")
        if len(sides) != 2:
            p_.append(f"{len(sides)} proof sides")
        for i, s in enumerate(sides[:2]):
            refs = [x.attrs["data-file"] for x in walk(s) if "data-file" in x.attrs]
            quotes = [norm(text(x)) for x in walk(s) if "data-src" in x.attrs or "id" in cls(x) or "data-k" in x.attrs]
            if not refs or any(not os.path.isfile(os.path.join(root, *r.split("/"))) for r in refs):
                p_.append(f"side {i + 1} names no real file {refs}")
            want = C[cid]["sides"][i] if i < len(C[cid]["sides"]) else []
            miss = [w for w in want if not any(w in qq for qq in quotes)]
            if miss or not quotes:
                p_.append(f"side {i + 1} doesn't show {miss or 'any quoted value'}")
        btn = lambda a: [x for x in walk(n) if x.tag == "button" and a in x.attrs]
        if not btn("data-ap-approve") or not btn("data-ap-reject") or not btn("data-ap-confirm"):
            p_.append("Approve / Reject / Confirm button missing")
        if not [x for x in walk(n) if "data-ap-reason" in x.attrs and x.tag in ("textarea", "input")]:
            p_.append("no reason box")
        if n.attrs.get("data-decider") != C[cid]["decider"] or C[cid]["decider"] not in norm(text(n)):
            p_.append(f"decider {n.attrs.get('data-decider')} (want {C[cid]['decider']}, named on the card)")
        if n.attrs.get("data-since") != C[cid]["since"]:
            p_.append(f"since {n.attrs.get('data-since')} (want {C[cid]['since']})")
        if p_:
            probs[cid] = p_
    rec(not probs and len(cards) == len(CARDS), "I2 every card: found, proof side by side, drafted fix, Approve, Reject with a reason, the person who decides",
        f"{len(CARDS) - len(probs)} of {len(CARDS)} cards complete; deciders "
        f"{ {c: C[c]['decider'] for c in CARDS} }; problems {probs}")

    # I3 the sample software screen: labeled a sample, no real product's name, one record per card, before and after values recounted
    ptxt = norm(text(panel))
    sec_txt = norm(text(sec))
    named = [w for w in PRODUCTS if re.search(r"(?<![\w.])" + re.escape(w) + r"(?![\w])", sec_txt)]
    imgs = [x.tag for x in walk(sec) if x.tag in ("img", "image", "object", "embed", "iframe")]
    rprobs = {}
    for cid in CARDS:
        r = recs.get(cid)
        if r is None:
            rprobs[cid] = "no record"
            continue
        flds = [x for x in walk(r) if "data-ap-field" in x.attrs]
        changed = [x for x in flds if [y for y in walk(x) if "ap-before" in cls(y)] and [y for y in walk(x) if "ap-after" in cls(y)]]
        side_txt = {s: " ".join(norm(text(y)) for x in changed for y in walk(x) if s in cls(y)) for s in ("ap-before", "ap-after")}
        miss = [(s, v) for s, v in C[cid]["lands"] if v not in side_txt[s]]
        if not changed or miss or r.attrs.get("data-state") == "landed":
            rprobs[cid] = f"{len(changed)} changing fields; values not shown {miss}; starts landed {r.attrs.get('data-state') == 'landed'}"
    label_ok = "Sample property software" in ptxt and "sample screen" in ptxt.lower()
    rec(label_ok and not named and not imgs and not rprobs and len(recs) == len(CARDS),
        "I3 a sample software screen (labeled, no real product's name or logo): one record per card, before and after values recounted",
        f"labeled 'Sample property software' + 'sample screen': {label_ok}; real product names on the tab {named}; pictures {imgs}; "
        f"records {len(recs)} (want {len(CARDS)}); problems {rprobs}")

    # I4 fingerprints: the check's own SHA-256 of each card's evidence, all different
    fps = {c: cards[c].attrs.get("data-fp") for c in cards}
    fwrong = {c: (fps.get(c), C[c]["fp"]) for c in CARDS if fps.get(c) != C[c]["fp"]}
    rec(not fwrong and len(set(fps.values())) == len(CARDS), "I4 each problem's fingerprint = SHA-256 of its evidence (files, fields, values), all different",
        f"{len(CARDS) - len(fwrong)} of {len(CARDS)} match the check's own; distinct {len(set(fps.values()))}; wrong {fwrong}; "
        f"evidence lines {sum(len(C[c]['evidence']) for c in CARDS)}")

    # I5 a headless browser presses the buttons: approve, reject without and with a reason, run again, reload, reset
    got, errs = drive(html_text) if html_text else ({"error": "no page"}, None)
    s = lambda k: got.get(k) or {}
    n_ = len(CARDS)
    a, b = got.get("a"), got.get("b")
    land = C.get(a, {}).get("lands", [])
    after_vals = [v for side, v in land if side == "ap-after"]
    before_only = [v for side, v in land if side == "ap-before" and v not in after_vals]
    shows = lambda key, want: bool(got.get(key)) and all(pair == want for pair in got.get(key))  # every changing field: [old shown, new shown]
    steps = {
        "start: all waiting, nothing decided, nothing logged": s("start").get("pending") == n_ and s("start").get("stuck") == n_ and s("start").get("logRows") == 0 and not s("start").get("landed"),
        "approve: record lands, every changed field shows its new value and hides the old, 1 log row": s("approved").get("landed") == [a] and s("approved").get("logRows") == 1
            and shows("aVisBefore", [True, False]) and shows("aVisAfter", [False, True])
            and all(v in got.get("aAfter", "") for v in after_vals) and not any(v in got.get("aAfter", "") for v in before_only)
            and all(v in got.get("aBefore", "") for v in before_only),
        "reject with no reason: refused, nothing logged": s("rejectNoReason").get("decided") == 1 and s("rejectNoReason").get("logRows") == 1 and bool(s("rejectNoReason").get("msg", "").strip()),
        "reject with a reason: the record's fields stay as typed, reason logged": s("rejected").get("decided") == 2 and s("rejected").get("logRows") == 2
            and s("rejected").get("landed") == [a] and got.get("bAfter") == got.get("bBefore") and any("already settled" in t for t in got.get("logText", [])),
        "run again: 0 new, 2 already decided, 3 waiting": (s("run2").get("run") or {}).get("neu") == "0" and (s("run2").get("run") or {}).get("decided") == "2"
            and (s("run2").get("run") or {}).get("waiting") == str(n_ - 2) and s("run2").get("pendingShown") == n_ - 2 and s("run2").get("stuck") == n_ - 2,
        "reload: decisions kept, run again still 0 new": s("reloaded").get("decided") == 2 and s("reloaded").get("landed") == [a] and s("reloaded").get("logRows") == 2
            and (s("run3").get("run") or {}).get("neu") == "0" and (s("run3").get("run") or {}).get("decided") == "2",
        "reset: all 5 back, records as typed, log cleared": s("reset").get("pending") == n_ and s("reset").get("stuck") == n_ and s("reset").get("logRows") == 0
            and not s("reset").get("landed") and all(v in got.get("aReset", "") for v in before_only) and shows("aVisReset", [True, False]),
    }
    bad = [k for k, v in steps.items() if not v]
    rec(not bad and not got.get("error") and errs == "0", "I5 in a browser: approve lands, reject needs a reason, run again finds 0 new, decisions survive a reload, reset works",
        f"{len(steps) - len(bad)} of {len(steps)} steps pass; failed {bad}; script errors {errs}; approved {a}, rejected {b}; "
        f"run again said '{norm((s('run2').get('run') or {}).get('text', ''))}'; error {got.get('error', 'none')[:160] if got.get('error') else 'none'}")

    # I6 wording a stressed office manager reads: "working demo" + "sample records", never "fake" or "made up"
    tab_words = sec_txt + " " + (norm(text(next((n for n in walk(audit) if n.tag == "table" and "data-ap-log" in n.attrs), Node("x", {}, None)))) if audit else "")
    hits = [m.group(0) for pat in BANNED_WORDS for m in re.finditer(pat, tab_words, re.I)]
    has = {"working demo": "working demo" in sec_txt.lower(), "sample records": "sample records" in sec_txt.lower(),
           "audit log table": audit is not None and any(n.tag == "table" and "data-ap-log" in n.attrs for n in walk(audit))}
    rec(not hits and all(has.values()), "I6 plain wording: 'working demo' and 'sample records' on the tab, 0 'fake' / 'made up'; the audit log tab has the page's decision table",
        f"{len(tab_words.split())} words read; says {has}; banned words {hits[:4]}")
    return res


def report(res):
    for ok, name, detail in res:
        print(("PASS" if ok else "FAIL"), "-", name, "-", detail)
    n = sum(ok for ok, _, _ in res)
    print(f"RESULT: {n} of {len(res)} checks PASS")
    return n == len(res) and len(res) == 6


def selftest():
    """One planted break per check, each in a temp copy; each must make its own check FAIL."""
    page = os.path.join("dashboard", "index.html")
    breaks = [("I1", "a tagged number off by one (the invoice's should-be amount)", page, 'data-k="ap.kc.expected">$713<', 'data-k="ap.kc.expected">$714<'),
              ("I2", "a card that lost one side of its proof", page, 'class="ap-side"', 'class="ap-xside"'),
              ("I3", "a real product's name on the sample screen", page, "Sample property software", "AppFolio-style property software"),
              ("I4", "a fingerprint that doesn't match its evidence", page, 'data-fp="', 'data-fp="0'),
              ("I5", "a reject that no longer needs a reason", page, "if(!why){", "if(false){"),
              ("I5", "a reject that changes the record anyway", page, "d&&d.action==='approved'?'landed':'typed'", "d?'landed':'typed'"),
              ("I6", "the tab calls the records fake", page, "working demo with sample records", "working demo with fake records")]
    caught = 0
    for code, what, f, a, b in breaks:
        tmp = tempfile.mkdtemp(prefix="p3i-")
        dst = os.path.join(tmp, "repo")
        for d in ("company", "owners", "vendors", "projects", "tests", "dashboard"):
            shutil.copytree(os.path.join(ROOT, d), os.path.join(dst, d), ignore=shutil.ignore_patterns("__pycache__", "*.png"))
        fp = os.path.join(dst, *f.split("/"))
        old = open(fp, encoding="utf-8").read() if os.path.exists(fp) else ""
        new = old.replace(a, b, 1)
        planted = new != old
        open(fp, "w", encoding="utf-8", newline="").write(new)
        r = {n.split()[0]: ok for ok, n, _ in run(dst)}
        hit = planted and r.get(code) is False
        caught += hit
        print(f"self-test: {what} -> {code} {'caught' if hit else 'MISSED'}{'' if planted else ' (not planted: text not found)'}")
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"self-test: {caught} of {len(breaks)} breaks caught")
    return caught == len(breaks)


if __name__ == "__main__":
    if "--facts" in sys.argv:
        print(json.dumps(recount(ROOT)[0], sort_keys=True))
        sys.exit(0)
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    sys.exit(0 if report(run(ROOT)) else 1)
