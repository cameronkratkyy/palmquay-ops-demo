"""Palmquay operations dashboard: one offline page built from the records in this folder (fictional company, sample records).

    python -I -X utf8 dashboard/build.py              write dashboard/index.html + dashboard/data.json (runs the 3 older checks live, ~4 s)
    python -I -X utf8 dashboard/build.py --out DIR    write to DIR instead (the Phase 3b check uses this to prove the build is read-only)
    python -I -X utf8 dashboard/build.py --copy       tell the older checks they run on a copy

Read-only: it reads the records, runs the read-only checks and hash-chain verifiers, and writes only its own two files.
No server, no network: open dashboard/index.html by double-clicking it. Every number in a tile or table is tagged with
the fact it shows (data-k), every quote names its file (data-src), and tests/check_phase3b.py recounts each one its own way.
Rules for "Waiting on people" and the expiry list: dashboard/README.md.
"""
import csv
import datetime as dt
import glob
import html
import io
import json
import os
import re
import subprocess
import sys
import time

T0 = time.time()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else os.path.join(ROOT, "dashboard")
COPY = "--copy" in sys.argv
EXPIRY_WINDOW = 60
PROJECT = "unit-4b"
ACTS = [("scope_brief", "/scope", "Requirements and scope", "scope"), ("source_check", "/source", "Supplier lead times", "source"),
        ("quote_compare", "/quote", "Quotes and purchase request", "quote"), ("product_approval", "/approve", "Product approval", "approve"),
        ("change_request", "/change", "Budget and change control", "change"), ("delivery_exceptions", "/deliver", "Deliveries and exceptions", "deliver"),
        ("invoice_match", "/match", "Invoice three-way match", "match")]
MEANING = {
    "COI_EXPIRED": "Insurance certificate has expired", "GL_BELOW_MIN": "Liability coverage below the company minimum",
    "MISSING_W9": "Tax form missing", "NO_ADDITIONAL_INSURED": "Palmquay not named on the insurance",
    "LICENSE_EXPIRING_30D": "License about to expire: on hold until renewed", "NAME_MISMATCH": "Company name differs between documents",
    "MISSING_MEASUREMENT": "A wall length was left blank", "SCOPE_CONFLICT": "The requested bed doesn't fit the room",
    "LATE_ITEM": "Would arrive after the install date", "HIDDEN_FREIGHT": "Delivery charge only in a footnote",
    "QUOTE_EXPIRED": "Quote past its valid-until date", "TOO_WIDE": "Wider than the plan allows",
    "FINISH_MISMATCH": "Wrong finish for the plan", "NEEDS_PERSON": "Unclear, so sent to a person instead of guessed",
    "OVER_BUDGET": "The change puts the project over budget", "DELIVERY_LATE": "Delivery after the install date",
    "ADDRESS_MISMATCH": "Shipping to the wrong unit", "PRICE_MISMATCH": "Billed a higher price than ordered",
    "QTY_MISMATCH": "Billed more than was ordered and received",
    "CONFLICT_DISCLOSED": "A relative of an approver owns part of the vendor", "EXCLUDED": "A company on the exclusion list",
    "LOWEST_NOT_SELECTED": "The lowest in-spec price wasn't picked", "SINGLE_SOURCE": "Only one supplier offers it",
    "CLAIM_CONTRADICTED": "A supplier said all delivered; the receipt disagrees",
    "MISSING_DISCLOSURE": "No conflict-of-interest disclosure", "PAID_SOLICITATION": "Someone was paid to help win the work",
    "FORMAL_BID_REQUIRED": "Too large for quotes: needs a formal bid", "FUNDS_SHORT": "The budget line doesn't cover it"}
TABS = [("overview", "Overview"), ("onboarding", "Onboarding"), ("buying", "Buying"), ("checks", "Checks"),
        ("audit", "Audit log"), ("map", "Map")]

K = {}  # every tagged fact on the page: key -> value


# ------------------------------------------------------------- reading -------------------------------------------------------------
def path(*a):
    return os.path.join(ROOT, *a)


def read(*a):
    return open(path(*a), encoding="utf-8").read().replace("\r", "")


def jread(*a):
    return json.loads(read(*a))


def table_fields(t):
    out = {}
    for line in t.splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", line)
        if m and m.group(1) not in out:
            out[m.group(1)] = m.group(2)
    return out


def line_fields(t):
    out = {}
    for line in t.splitlines():
        m = re.match(r"^([A-Z][A-Za-z ,()/'-]*?):[ \t]*(.*)$", line)
        if m and m.group(1) not in out:
            out[m.group(1)] = m.group(2).strip()
    return out


def table_rows(t, first_header):
    lines = t.splitlines()
    for i, line in enumerate(lines):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells and cells[0] == first_header:
            rows = []
            for row in lines[i + 2:]:
                if not row.startswith("|"):
                    break
                rows.append(dict(zip(cells, [c.strip() for c in row.strip().strip("|").split("|")])))
            return rows
    return []


def dollars(s):
    return int(re.sub(r"[^\d]", "", s))


def day(s):
    return dt.date.fromisoformat(s.strip()[:10])


def norm(t):
    return re.sub(r"\s+", " ", t.replace("**", "")).strip()


def log_rows(name):
    return list(csv.DictReader(io.StringIO(read("audit", name))))


# ------------------------------------------------------------- markup helpers -------------------------------------------------------------
E = html.escape


def k(key, value, money=False):
    """A tagged number. The same key may appear more than once, always with the same value."""
    if key in K and K[key] != value:
        raise SystemExit(f"build error: {key} shown as {K[key]} and {value}")
    K[key] = value
    shown = f"${value:,}" if money else f"{value:,}"
    return f'<span class="n" data-k="{key}">{shown}</span>'


def q(rel, s, cls="src"):
    """A word-for-word quote from a record; the build stops if the text isn't in that file."""
    if norm(s) not in norm(read(*rel.split("/"))):
        raise SystemExit(f"build error: quote not found in {rel}: {s[:60]}")
    return f'<span class="{cls}" data-src="{rel}" title="Quoted from {rel}">{E(s)}</span>'


def code(c):
    return q("company/rules.json", c, "code")


def ident(s, plain=False):
    return f'<span class="id{" plain" if plain else ""}">{E(s)}</span>'


def pre(rel):
    return f'<pre data-file="{rel}">{E(read(*rel.split("/")).strip())}</pre>'


def chip(status, label=None):
    icon = {"READY": "&#10003;", "HOLD": "&#10074;&#10074;", "BLOCKED": "&#10005;", "SUBMITTED": "&#8226;", "PERSON": "?",
            "DONE": "&#10003;", "WAITING": "&#8230;", "LATE": "!", "OK": "&#10003;", "PASS": "&#10003;", "FAIL": "&#10005;"}.get(status, "&#8226;")
    return f'<span class="chip st-{status}"><i aria-hidden="true">{icon}</i>{E(label or status)}</span>'


def details(summary, body):
    return f"<details><summary>{summary}</summary>{body}</details>"


# ------------------------------------------------------------- load -------------------------------------------------------------
rules = jread("company", "rules.json")
DEMO = day(rules["demo_date"])
people = {}
for r in table_rows(read("company", "people.md"), "Role"):
    people[re.sub(r"\s*\(.*?\)", "", r["Role"]).strip()] = r["Name"]


def plain_item(s):
    """'Bed frame, queen' -> 'queen bed frame'."""
    return " ".join(reversed([x.strip() for x in s.lower().split(",", 1)])) if "," in s else s.lower()


def who(role):
    return f"{people[role]}, {role}" if role in people else role


slugs = sorted(d for d in os.listdir(path("vendors")) if os.path.isdir(path("vendors", d)))
V = {}
for s in slugs:
    v = {"slug": s, "intake": jread("vendors", s, "intake.json"), "rec": table_fields(read("vendors", s, "vendor.md")),
         "req": table_fields(read("vendors", s, "documents", "request.md")), "docs": {}}
    for doc in ("coi", "license"):
        if os.path.exists(path("vendors", s, "documents", doc + ".md")):
            v["docs"][doc] = table_fields(read("vendors", s, "documents", doc + ".md"))
    v["drafts"] = sorted(os.path.relpath(f, ROOT).replace("\\", "/") for f in glob.glob(path("vendors", s, "drafts", "*.md")))
    v["packet"] = f"vendors/{s}/packet.md" if os.path.exists(path("vendors", s, "packet.md")) else None
    V[s] = v

P = lambda *a: path("projects", PROJECT, *a)
pr_rules = rules["projects"]
req = line_fields(read("projects", PROJECT, "request.md"))
po_text = read("projects", PROJECT, "approved", "po-PQ-1042.md")
po = line_fields(po_text)
out = {f: jread("projects", PROJECT, "out", f) for f in ("brief.json", "source.json", "quotes.json", "approval.json",
                                                         "change-request-CR-001.json", "deliveries.json", "match.json")}
brief, src, quotes, appr = out["brief.json"], out["source.json"], out["quotes.json"], out["approval.json"]
cr, dlv, mt = out["change-request-CR-001.json"], out["deliveries.json"], out["match.json"]
notice_rel = "projects/unit-4b/events/2026-11-07-backorder.md"
notice = line_fields(read(*notice_rel.split("/")))
tracking = table_rows(read("projects", PROJECT, "deliveries", "tracking-2026-11-12.md"), "SKU")
tracking_asof = line_fields(read("projects", PROJECT, "deliveries", "tracking-2026-11-12.md"))["As of"]
invoices = {os.path.basename(f)[:-3]: line_fields(open(f, encoding="utf-8").read()) for f in glob.glob(P("invoices", "*.md"))}
tasks = [r for r in table_rows(read("projects", PROJECT, "out", "tasks.md"), "Task") if re.match(r"T\d+", r.get("Task", ""))]
onb_rows, proc_rows = log_rows("audit-log.csv"), log_rows("procurement-log.csv")
requester_name, requester_role = [x.strip() for x in re.sub(r"\s*\(.*?\)", "", req["Requested by"]).split(",", 1)]
unit = f"Unit {req['Unit']}"
ctl_rules = rules.get("controls", {})
screens = {s: jread("vendors", s, "screen.json") for s in slugs if os.path.exists(path("vendors", s, "screen.json"))}
sup_screen = jread("controls", "supplier-screen.json") if os.path.exists(path("controls", "supplier-screen.json")) else {"suppliers": {}}
areq = jread("projects", PROJECT, "controls", "approval-request.json") if os.path.exists(P("controls", "approval-request.json")) else None
csum = jread("projects", PROJECT, "controls", "contract-summary.json") if os.path.exists(P("controls", "contract-summary.json")) else None
ctl_rows = log_rows("controls-log.csv") if os.path.exists(path("audit", "controls-log.csv")) else []
reply_drafts = sorted(os.path.relpath(f, ROOT).replace("\\", "/") for f in glob.glob(P("controls", "drafts", "reply-*.md")))
ctl_day = {r["action"]: r["timestamp"][:10] for r in ctl_rows}
exclusion = {r["Excluded party"]: r for r in table_rows(read("company", "exclusion-list.md"), "Excluded party")} if os.path.exists(path("company", "exclusion-list.md")) else {}
exc_rules = rules.get("exceptions", {})
exc_rows = log_rows("exceptions-log.csv") if os.path.exists(path("audit", "exceptions-log.csv")) else []
revisions = {s: jread("vendors", s, "revision.json") for s in slugs if os.path.exists(path("vendors", s, "revision.json"))}
credit = jread("projects", PROJECT, "exceptions", "freight-credit.json") if os.path.exists(P("exceptions", "freight-credit.json")) else None
credit_drafts = sorted(os.path.relpath(f, ROOT).replace("\\", "/") for f in glob.glob(P("exceptions", "credit-request-*.md")))
catalog = {r["SKU"]: dict(r, supplier=line_fields(open(f, encoding="utf-8").read())["Supplier"]) for f in glob.glob(P("catalogs", "*.md")) for r in table_rows(open(f, encoding="utf-8").read(), "SKU")}


# ------------------------------------------------------------- live checks -------------------------------------------------------------
def run(args):
    r = subprocess.run([sys.executable, "-I", "-X", "utf8"] + args, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=ROOT, timeout=900)
    return r.returncode, r.stdout


def defang(s):
    """Check output may quote a web-address-like string it found; show it as text, never as an address (example: name[.]ai).
    It may also print this PC's folder path, which names the Windows user: masked, so the page can be shared."""
    s = s.replace(ROOT, "<demo folder>").replace(ROOT.replace("\\", "/"), "<demo folder>")
    s = re.sub(r"(?i)\b[a-z]:[\\/]+users[\\/]+[^\\/\s;,]+", "<user folder>", s)
    s = re.sub(r"(?i)(https?):/{2}", r"\1:[//]", s)
    s = re.sub(r"(?i)\bwww\.", "www[.]", s)
    return re.sub(r"(?i)([a-z0-9-])\.(com|net|org|io|gov|edu|us|ai|app|info|biz)\b", r"\1[.]\2", s)


CHECKS = {}
for tag, f, label in (("p1", "check_phase1.py", "Phase 1"), ("p2", "check_phase2.py", "Phase 2"), ("p3a", "check_phase3a.py", "Phase 3a"),
                      ("p3c", "check_phase3c.py", "Phase 3c"), ("p3d", "check_phase3d.py", "Phase 3d")):
    if not os.path.exists(path("tests", f)):
        continue
    t1 = time.time()
    rc, so = run([path("tests", f)] + (["--root", ROOT] if f in ("check_phase3a.py", "check_phase3c.py", "check_phase3d.py") else [])
                 + (["--copy"] if COPY else []) + (["--skip-old-phases"] if f in ("check_phase3c.py", "check_phase3d.py") else []))
    m = re.findall(r"^RESULT: (\d+) of (\d+) checks PASS", so, re.M)
    lines = [defang(l) for l in so.splitlines() if l.startswith(("PASS - ", "FAIL - "))]
    CHECKS[tag] = {"label": label, "file": f"tests/{f}", "rc": rc, "pass": int(m[-1][0]) if m else None,
                   "total": int(m[-1][1]) if m else None, "lines": lines, "secs": round(time.time() - t1, 1)}


def chain(tool, cmd):
    rc, so = run([path("tools", tool), cmd])
    m = re.search(r"(\d+) rows, (\d+) of (\d+) chain links verify -> OK", so)
    return (int(m.group(2)), so.strip()) if m and rc == 0 else (None, so.strip())


onb_links, onb_verify = chain("onboard.py", "verify-audit")
proc_links, proc_verify = chain("project.py", "verify-log")
ctl_links, ctl_verify = chain("controls.py", "verify-log") if ctl_rows else (0, "")
exc_links, exc_verify = chain("exceptions.py", "verify-log") if exc_rows else (0, "")


# ------------------------------------------------------------- facts -------------------------------------------------------------
def tier_of(amount):
    return next(t for t in rules["approval_tiers"] if t["max_amount"] is None or amount <= t["max_amount"])


onb_codes = [(c, s) for s in slugs for c in V[s]["intake"]["issues"]]
per_act = {"scope": [(c, "Bedroom") for c in brief["codes"]],
           "source": [("LATE_ITEM", sku) for sku in src["late"]],
           "quote": [(c, qid) for qid, qv in quotes["quotes"].items() for c in qv["codes"]],
           "approve": [(c, f"line {ln}") for ln, c in appr["FAIL"].items()] + [("NEEDS_PERSON", f"line {ln}") for ln in appr["NEEDS_PERSON"]],
           "change": [(c, "CR-001") for c in cr["codes"]],
           "deliver": [(c, sku) for sku, c in dlv["exceptions"].items()],
           "match": [(c, inv) for inv, iv in mt["invoices"].items() for c in iv["codes"]]}
buy_codes = [x for v in per_act.values() for x in v]
ctl_codes = [(c, s) for s, sc in screens.items() for c in sc.get("codes", [])]
ctl_codes += [(f, sku) for sku, f in (areq or {}).get("flags", {}).items()]
if csum and csum.get("claim", {}).get("result") == "CLAIM_CONTRADICTED":
    ctl_codes.append(("CLAIM_CONTRADICTED", csum["claim"]["supplier"]))
CTL_SKILL = {"CONFLICT_DISCLOSED": "/screen", "EXCLUDED": "/screen", "MISSING_DISCLOSURE": "/screen", "PAID_SOLICITATION": "/screen",
             "LOWEST_NOT_SELECTED": "/request", "SINGLE_SOURCE": "/request", "FORMAL_BID_REQUIRED": "/request", "FUNDS_SHORT": "/request",
             "CLAIM_CONTRADICTED": "/closeout"}
held = {i: v for i, v in mt["invoices"].items() if v["result"] == "HOLD"}
matched = {i: v for i, v in mt["invoices"].items() if v["result"] == "MATCH"}
hid, hv = next(iter(held.items()))
sofa_sku, sofa = next(iter(src["late"].items()))
bed_sku, bed_days = next(iter(dlv["days_late"].items()))
new_ship = re.search(r"new ship date (\S+)", notice["Notice"]).group(1)
queen_needs = pr_rules["bed_widths_in"]["queen"] + 2 * pr_rules["bed_side_clearance_in"]
bed_eta = next(r["ETA"] for r in tracking if r["SKU"] == bed_sku)
people_only = re.compile(r"^(?:send|sign|approve|pay|order|place)", re.I)
did = re.compile(r"(?<!not )\b(?:sent|signed|approved|paid|ordered)\b", re.I)
ai_people = sum(1 for r in onb_rows + proc_rows + ctl_rows + exc_rows if r["actor"].endswith("-assistant") and (people_only.search(r["action"]) or did.search(r["result"])))
unsent = [d for s in slugs for d in V[s]["drafts"] if "| Status | DRAFT, not sent |" in read(*d.split("/"))]
upd_drafts = sorted(os.path.relpath(f, ROOT).replace("\\", "/") for f in glob.glob(P("out", "drafts", "update-*.md")))
unsent += [d for d in upd_drafts + reply_drafts + credit_drafts if "not sent" in read(*d.split("/")).splitlines()[0]]
blank_signoffs = 0
for s in slugs:
    if V[s]["packet"]:
        for r in table_rows(read(*V[s]["packet"].split("/")), "#"):
            if r.get("#", "").isdigit() and not r.get("Decision") and not r.get("Signature"):
                blank_signoffs += 1
for s, rv in revisions.items():  # a newer packet version after a change during sign-off (Phase 3d): its own sign-off lines
    for r in table_rows(read(*rv["packet"].split("/")).split("## Sign-offs", 1)[1], "#"):
        if r.get("#", "").isdigit() and not r.get("Decision") and not r.get("Signature"):
            blank_signoffs += 1
blank_lines = [f for f in sorted(glob.glob(P("out", "*.md"))) if re.search(r"Approved by: _{3,}", open(f, encoding="utf-8").read())]
reviews = ([("onb", r) for r in onb_rows if r["action"] == "checker_review"] + [("proc", r) for r in proc_rows if r["action"] == "checker_review"]
           + [("ctl", r) for r in ctl_rows if r["action"] == "checker_review"] + [("exc", r) for r in exc_rows if r["action"] == "checker_review"])

# ------------------------------------------------------------- waiting on people -------------------------------------------------------------
W = []  # (since, key, owner_role, who, decision_html, options, suggestion_html, record)
for s in slugs:
    v, it = V[s], V[s]["intake"]
    name = it["legal_name"]
    for d in v["drafts"]:
        f = table_fields(read(*d.split("/")))
        if it["status"] in ("BLOCKED", "HOLD") and not screens.get(s, {}).get("hold_followup"):
            role = f["Reviewer and sender"].split(",", 1)[1].strip()
            asks = "; ".join(MEANING[c][0].lower() + MEANING[c][1:] for c in it["issues"])
            W.append((f["Drafted"][:10], f"send_followup:{s}", role, who(role),
                      f"Send the follow-up to {E(name)}? It asks them to fix: {E(asks)}. Reply due {f['Deadline']}.",
                      "Send as written · Edit, then send · Hold",
                      "Send as written: the checker's review of the drafts found " + q("audit/audit-log.csv", "no findings on real files") + ".", d))
    if v["packet"] and s in revisions:
        rv = revisions[s]
        role = rv["next"]
        v2 = rv["packet"]
        W.append((rv["requested_on"], f"sign_packet:{s}", role, who(role),
                  f"Sign {q(v2, 'version 2')} of the approval packet for {E(name)} ({k(f'v.{s}.amount', dollars(v['req']['Contract amount']), True)}, "
                  f"{k(f'v.{s}.approvers', len(rv['route']))} sign-offs in order, you first again)? {E(who(rv['requested_by']))} asked for a change after "
                  f"{k('ex.v1_signed', len(rv['signed_before']))} people signed {q(v2, 'version 1')}: " + q(v2, rv["change"]),
                  "Void the old version, send the new one, and sign it first · Ask Legal a question first",
                  "Send the new version: a change to the contract terms means the earlier signatures don't carry over.", v2))
    elif v["packet"]:
        pf = table_fields(read(*v["packet"].split("/")))
        sc = screens.get(s, {})
        role = sc["approvers"][0] if sc.get("recused") else it["approvers"][0]
        n = len(sc["approvers"]) if sc.get("recused") else len(it["approvers"])
        W.append((pf["Built"][:10], f"sign_packet:{s}", role, who(role),
                  f"Sign the approval packet for {E(name)} ({k(f'v.{s}.amount', dollars(v['req']['Contract amount']), True)}, "
                  f"{k(f'v.{s}.approvers', n)} sign-off{'s' if n > 1 else ''} in order, you first)?"
                  + (f" {E(who(sc['recused'][0]))} is recused: a disclosed relative owns part of the firm. Sign after Legal clears the disclosure." if sc.get("recused") else ""),
                  "Approve · Reject · Ask a question",
                  "Approve after Legal clears the disclosure." if sc.get("recused") else "Approve: intake found no issues against the rules.", v["packet"]))
    sc = screens.get(s, {})
    if sc.get("result") == "REVIEW":
        rel_ = sc["disclosure"]["relationships"][0]
        W.append((sc["disclosure"].get("date", ""), f"review_disclosure:{s}", sc["reviewers"][0], who(sc["reviewers"][0]),
                  f"Review {E(name)}'s conflict-of-interest disclosure: " + q(f"vendors/{s}/screen.json", rel_["Person"]) + ", "
                  + q(f"vendors/{s}/screen.json", rel_["Relationship"]) + ", " + q(f"vendors/{s}/screen.json", rel_["Interest"]) + ".",
                  "Clear it with the recusal · Require changes · End the onboarding",
                  "Clear it only with the recusal in place." if sc.get("recused") else "Decide before anyone signs.", f"vendors/{s}/screen.json"))
    if sc.get("result") == "EXCLUDED":
        hit = sc["matched"][0]
        W.append((sc.get("exclusion_list_as_of", ""), f"review_exclusion:{s}", sc["reviewers"][0], who(sc["reviewers"][0]),
                  f"{E(name)}'s paperwork names " + q("company/exclusion-list.md", hit) + f", excluded until {exclusion[hit]['Excluded until']}. "
                  + ("Its follow-up draft is on hold." if sc.get("hold_followup") else ""),
                  "End the onboarding · Ask the vendor to explain", "Don't send the follow-up as written; decide first whether to end the onboarding.",
                  f"vendors/{s}/screen.json"))
if brief["status"] == "NEEDS_INFO":
    W.append((req["Request date"], f"answer_scope:{PROJECT}", requester_role, f"{requester_name}, {requester_role}",
              f"What is bedroom wall B? It was left blank. The approved order has a queen bed, which needs {k('p.queen_needs', queen_needs)} in "
              f"on the shortest wall; wall A is {k('p.wall', brief['wall_in'])} in.",
              "Measure and reply", f"Measure before the bed frame arrives (now due {bed_eta}).", "projects/unit-4b/out/brief.md"))
for f in sorted(glob.glob(P("out", "change-request-*.json"))):
    crj = json.load(open(f, encoding="utf-8"))
    crid = os.path.basename(f)[len("change-request-"):-5]
    if re.search(r"Approved by: _{3,}", open(f[:-5] + ".md", encoding="utf-8").read()):
        role = crj["approvers"][0]
        late = (day(new_ship) - day(req["Install by"])).days
        W.append((notice["Date"], f"approve_change:{crid}", role, who(role),
                  f"Approve change request {ident(crid)}? The approved sofa is backordered to {new_ship}. The substitute arrives "
                  f"{crj['new_date']} for +{k('p.cr_delta', crj['delta'], True)}, a total of {k('p.cr_total', crj['new_total'], True)}.",
                  "Approve the substitute · Reject and wait · Ask for another option",
                  f"Approve: waiting misses the install date by {k('p.backorder_late', late)} days; the cost is "
                  f"{k('p.cr_over', crj['over_by'], True)} over budget.", f"projects/unit-4b/out/change-request-{crid}.md"))
for d in upd_drafts:
    W.append((tracking_asof, "send_update:" + os.path.basename(d)[:-3], pr_rules["update_reviewer"], who(pr_rules["update_reviewer"]),
              f"Send the delivery update to {requester_name}? The bed frame is {k('p.bed_late', bed_days)} days late and the dresser "
              f"is addressed to the wrong unit.", "Send as written · Edit, then send", "Send as written.", d))
for t in tasks:
    role = re.sub(r"\s*\(.*?\)", "", t["Owner"]).strip()
    what = {"DELIVERY_LATE": f"get a firm new date for the bed frame {ident(t['SKU'])} from {E(t['Supplier'])}",
            "ADDRESS_MISMATCH": f"correct the dresser's ship-to address with {E(t['Supplier'])} ({ident('Unit 4D')} to {ident(unit)})"}[t["Exception"]]
    W.append((tracking_asof, "task:" + t["Task"], role, who(role), f"Task {ident(t['Task'])}: {what}. Due {t['Due']}.",
              "Done · Escalate", "Call the supplier today.", "projects/unit-4b/out/tasks.md"))
for inv, iv in mt["invoices"].items():
    role = mt["payment_approver"]
    since = invoices[inv]["Invoice date"]
    if iv["result"] == "HOLD":
        W.append((since, f"decide_invoice:{inv}", role, who(role),
                  f"Invoice {ident(inv)} bills {k('p.inv_billed', iv['billed'], True)}; the order and the receipt support "
                  f"{k('p.inv_expected', iv['expected'], True)}. Pay as billed, or ask for a corrected invoice?",
                  "Pay as billed · Ask for a corrected invoice", f"Ask for a corrected invoice: it bills {k('p.inv_diff', iv['difference'], True)} too much.",
                  "projects/unit-4b/out/match.md"))
    else:
        W.append((since, f"approve_payment:{inv}", role, who(role),
                  f"Approve payment of invoice {ident(inv)} ({k('p.inv_match_total', dollars(invoices[inv]['Total due']), True)})? "
                  f"It matches the order and the receipt.", "Approve payment · Hold", "Approve payment.", "projects/unit-4b/out/match.md"))
if areq:
    jw = ctl_rules["justification_writer"]
    for sku in areq["needs_person"]:
        it_ = next(l for l in table_rows(po_text, "SKU") if l["SKU"] == sku)
        lt = int(it_["Qty"]) * dollars(it_["Unit price"])
        W.append((po["Approved on"], f"justify_line:{sku}", jw, who(jw),
                  f"Write the single-source justification for {ident(sku)} ({E(it_['Item'].lower())}, {k(f'rq.{sku}.line', lt, True)}): only "
                  f"{E(it_['Supplier'])} offers one that meets the plan.", "Write it · Find a second source",
                  "Write it: the catalogs show no second in-spec source.", "projects/unit-4b/controls/approval-request.md"))
    ap = areq["approvers"][0]
    W.append((po["Approved on"], "certify_request:PQ-1042", ap, who(ap),
              f"Sign the certification on the approval request for order {ident('PQ-1042')} ({E(areq['type'].lower())}, "
              f"{k('p.committed', areq['total'], True)}, budget line " + q("projects/unit-4b/controls/approval-request.md", areq["budget_line"]) + ")?",
              "Sign after the justifications · Hold", "Sign once both justifications are written.", "projects/unit-4b/controls/approval-request.md"))
if credit:
    fc_role = credit["reviewer_and_sender"]
    for d in credit_drafts:
        sup, sv = next((n_, s_) for n_, s_ in credit["suppliers"].items() if s_["draft"] == d)
        it_ = credit["items"][sv["skus"][0]]
        W.append((credit["as_of"], "send_credit:" + os.path.basename(d)[:-3], fc_role, who(fc_role),
                  f"Send the shipping-credit request to {E(sup)}? Its {E(plain_item(it_['item']))} {ident(sv['skus'][0])} is now "
                  f"{k('ex.credit_days', it_['days_past'])} days past its promised date; the draft asks for " + q(d, sv["credit"])
                  + f", half of its {k('ex.credit_freight', sv['freight'], True)} freight.",
                  "Send as written · Change the amount, then send · Don't ask", "Send it: it's a polite ask, and the supplier can say no.", d))
for d in reply_drafts:
    cv = ctl_rules["closeout_verifier"]
    nd = csum["claim"]["not_delivered"]
    W.append((os.path.basename(d)[-13:-3], "send_reply:" + os.path.basename(d)[:-3], cv, who(cv),
              f"Send the reply refusing {E(csum['claim']['supplier'])}'s completion notice? "
              + " and ".join(ident(x) for x in nd) + " aren't on the receipt.", "Send as written · Edit, then send", "Send as written.", d))
W.sort(key=lambda w: (w[0], w[1]))
w_onb = sum(1 for w in W if w[1].split(":")[0] in ("send_followup", "sign_packet", "review_disclosure", "review_exclusion"))


# ------------------------------------------------------------- page parts -------------------------------------------------------------
def tiles():
    t = []
    t.append(("Vendors", k("v.total", len(slugs)),
              f"{k('v.READY', sum(V[s]['intake']['status'] == 'READY' for s in slugs))} ready · "
              f"{k('v.HOLD', sum(V[s]['intake']['status'] == 'HOLD' for s in slugs))} on hold · "
              f"{k('v.BLOCKED', sum(V[s]['intake']['status'] == 'BLOCKED' for s in slugs))} blocked"))
    t.append(("Waiting on people", k("w.total", len(W)), f"{k('w.onb', w_onb)} onboarding · {k('w.buy', len(W) - w_onb)} buying"))
    t.append((f"{ident(unit, True)} spend vs budget", f"{k('p.committed', dollars(po['Total']), True)}",
              f"of {k('p.budget', dollars(req['Budget']), True)} · a pending change makes it {k('p.cr_total', cr['new_total'], True)}"))
    t.append(("Problems caught", k("i.total", len(onb_codes) + len(buy_codes) + len(ctl_codes)),
              f"{k('i.onb', len(onb_codes))} onboarding · {k('i.buy', len(buy_codes))} buying · {k('i.ctl', len(ctl_codes))} controls"))
    ok = all(CHECKS[c]["pass"] is not None for c in CHECKS)
    if ok:
        passed, total = sum(CHECKS[c]["pass"] for c in CHECKS), sum(CHECKS[c]["total"] for c in CHECKS)
        t.append(("Checks, run at build", f"{k('c.pass', passed)} of {k('c.total', total)}",
                  chip("PASS" if passed == total else "FAIL", "PASS" if passed == total else "FAIL") + " run at build; " + ident("Phase 3b", True) + "'s check runs separately"))
    else:
        t.append(("Checks, run at build", "not run", "a check printed no result"))
    t.append(("Audit log rows", k("a.rows", len(onb_rows) + len(proc_rows) + len(ctl_rows) + len(exc_rows)),
              f"{k('a.onb', len(onb_rows))} onboarding + {k('a.proc', len(proc_rows))} buying + {k('a.ctl', len(ctl_rows))} controls"
              + (f" + {k('a.exc', len(exc_rows))} exceptions" if exc_rows else "") + ", hash-chained"))
    t.append(("Sent, signed, or paid by the AI", k("g.ai_people", ai_people),
              f"{k('g.drafts', len(unsent))} drafts unsent · {k('g.blank', blank_signoffs)} sign-offs blank"))
    return '<div class="tiles" data-audit>' + "".join(
        f'<div class="tile"><div class="lab">{a}</div><div class="big">{b}</div><div class="small">{c}</div></div>' for a, b, c in t) + "</div>"


# Org chart (added 11/8 at the author's ask): who works at Palmquay. Names and what each person approves come from company/people.md and the
# furnishing request; job titles, departments, and colors are display choices. Blank profile icons only, never faces.
ORG_ORDER = ["Property Manager", "Facilities Manager", "Procurement Lead", "Legal", "Finance"]
ORG_TITLE = {"Property Manager": "Property Manager", "Facilities Manager": "Facilities Manager", "Procurement Lead": "Procurement Lead",
             "Legal": "Legal Counsel", "Finance": "Controller"}
ORG_DEPT = {"Property Manager": "Property management", "Facilities Manager": "Facilities", "Procurement Lead": "Procurement",
            "Legal": "Legal", "Finance": "Finance"}
ORG_COLORS = ["#1d6fa5", "#d9822b", "#2e8b57", "#7b4fb3", "#b83b5e"]
approves = {re.sub(r"\s*\(.*?\)", "", r["Role"]).strip(): r["Approves"] for r in table_rows(read("company", "people.md"), "Role")}
org_people = {**people, requester_role: requester_name}
ORG = [(role, org_people[role], ORG_COLORS[i]) for i, role in enumerate(ORG_ORDER) if role in org_people]
COLOR_OF = {name: color for _, name, color in ORG}
company_line = re.search(r"manages (\d+) ([a-z ]+?) in ([A-Za-z ]+? counties)", read("CLAUDE.md"))
ICON = ('<svg class="avatar" viewBox="0 0 40 40" aria-hidden="true"><circle cx="20" cy="20" r="20" fill="var(--pc)"/>'
        '<circle cx="20" cy="15" r="7" fill="#fff" fill-opacity=".92"/><path d="M7 35c2.5-7.5 7.5-10.5 13-10.5S30.5 27.5 33 35" fill="#fff" fill-opacity=".92"/></svg>')


def dot(name):
    return f'<span class="dot" style="background:{COLOR_OF[name]}"></span> ' if name in COLOR_OF else ""


# The department hub (11/9, at the author's ask after an "AI Agent One" reel: a company drawn as a hub, each department with its owner and its
# AI helpers). Each waiting decision maps to the skill whose output created it (from each skill's SKILL.md "It writes ..." line).
SKILL_OF = {"send_followup": "/chase", "sign_packet": "/route", "review_disclosure": "/screen", "review_exclusion": "/screen",
            "answer_scope": "/scope", "approve_change": "/change", "send_update": "/deliver", "task": "/deliver",
            "decide_invoice": "/match", "approve_payment": "/match", "justify_line": "/request", "certify_request": "/request",
            "send_reply": "/closeout", "send_credit": "/credit"}
role_slug = lambda r: re.sub(r"[^a-z0-9]+", "-", r.lower()).strip("-")


def hub_load():
    """per owner role: how many decisions wait on them, and which skills put them there (a changed packet counts as /revise)"""
    n, sk = {}, {}
    for since, key, role, person, decision, options, suggest, rec_ in W:
        n[role] = n.get(role, 0) + 1
        kind, what = key.split(":", 1)
        s = SKILL_OF[kind]
        if kind == "sign_packet" and os.path.exists(os.path.join(ROOT, "vendors", what, "packet-v2.md")):
            s = "/revise"
        sk.setdefault(role, set()).add(s)
    return n, sk


def org_chart():
    n_by, sk_by = hub_load()
    cards = []
    for role, name, color in ORG:
        does = (f"Asked for {E(unit)} to be furnished ({E(req['Budget'])} budget)" if role == requester_role
                else "Approves: " + E(approves.get(role, "")))
        uses = " ".join(f"<code>{s}</code>" for s in sorted(sk_by.get(role, ())))
        cards.append(f'<div class="person" data-person="{E(name)}" style="--pc:{color}">{ICON}<div class="pname">{E(name)}</div>'
                     f'<div class="title">{E(ORG_TITLE[role])}</div><div class="dept">{E(ORG_DEPT[role])}</div>'
                     f'<div class="does">{does}</div>'
                     f'<div class="uses">AI helpers: {uses or "none"}</div>'
                     f'<div class="wait">Waiting on {E(name.split()[0])}: {k("w.role." + role_slug(role), n_by.get(role, 0))}</div></div><!-- /person -->')
    where = (f"Manages {company_line.group(1)} {E(company_line.group(2))} in {E(company_line.group(3))}" if company_line else "")
    spokes = "".join(f'<line x1="50" y1="50" x2="{x}" y2="{y}"/>' for x, y in ((16.7, 14), (50, 14), (83.3, 14), (16.7, 86), (83.3, 86)))
    return ('<h2>Who works at Palmquay</h2><p class="lead">Palmquay Properties, a fictional property management company based in Sarasota, '
            f'Florida. {where}. Each department has one owner and the AI helpers whose work lands on them: '
            'the AI drafts and checks, and the person decides.</p>'
            '<div class="org" data-org data-hub><div class="people">' + "".join(cards)
            + '<div class="core"><b>Palmquay Properties</b><span>Contractor approvals and furniture buying</span>'
            f'<span>{k("w.total", len(W))} decisions waiting on people</span></div>'
            '<div class="helper ai">AI assistant: reads the papers and drafts the next step; never sends, signs, orders, or pays</div>'
            '<div class="helper chk">Checker AI: a second AI, told to only read, reviews the work</div>'
            f'<svg class="spokes" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">{spokes}</svg>'
            '</div></div><!-- ORG END -->')


def overview():
    rows = []
    for since, key, role, person, decision, options, suggest, rec_ in W:
        rows.append(f'<tr data-w="{key}" data-owner="{E(role)}"><td class="nowrap">{since}</td><td>{dot(person.split(",")[0])}{E(person)}</td><td>{decision}</td>'
                    f'<td class="muted">{E(options)}</td><td>{suggest}</td><td><code data-file="{rec_}">{E(rec_)}</code></td></tr>')
    waiting = ('<h2>Waiting on people</h2><p class="lead">Every decision the AI stopped for, oldest first. The AI suggests; the named person '
               'decides. Rules for what counts: <code>dashboard/README.md</code>. Onboarding runs as of the demo date '
               f'{rules["demo_date"]}; the furnishing project\'s scripted events run to {tracking_asof}.</p>'
               '<table data-audit><thead><tr><th>Since</th><th>Who decides</th><th>Decision</th><th>Options</th><th>AI suggests</th>'
               '<th>Record</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table>")
    by = Counter_codes()
    prow, grouped = [], {}
    for half, items, skill_of in (("Onboarding", onb_codes, lambda c, w: "/intake"), ("Buying", buy_codes, None),
                                  ("Controls", ctl_codes, lambda c, w: CTL_SKILL[c])):
        for c, where in items:
            sk = skill_of(c, where) if skill_of else next(a[1] for a in ACTS if any(c == x[0] and where == x[1] for x in per_act[a[3]]))
            place = E(V[where]["intake"]["legal_name"]) if where in V else E(where) if where in sup_screen["suppliers"] else (ident(where) if re.search(r"\d", where) and not where.startswith("line") else E(where))
            if where.startswith("line"):
                ln = where.split()[1]
                item = table_rows(read("projects", PROJECT, "out", "approval.md"), "Line")[int(ln) - 1]
                place = f"{E(item['Item'])} {ident(item['SKU'])}"
            g = grouped.setdefault((half, c), {"sk": sk, "places": []})
            g["places"].append(place)
    for (half, c), g in grouped.items():
        prow.append(f"<tr><td>{half}</td><td>{code(c)}</td><td>{E(MEANING[c])}</td><td><code>{g['sk']}</code></td><td>{', '.join(g['places'])}</td>"
                    f'<td class="num">{k("ic." + c, by[c])}</td></tr>')
    problems = ('<h2>Problems caught, by cause</h2><p class="lead">Each one was planted in the sample data on purpose, written into a locked answer '
                'key first, and caught by the step named here.</p><table data-audit><thead><tr><th>Half</th><th>Code</th><th>What it means</th>'
                '<th>Caught by</th><th>Where</th><th class="num">Count</th></tr></thead><tbody>' + "".join(prow) + "</tbody></table>")
    return org_chart() + waiting + problems


def Counter_codes():
    c = {}
    for x, _ in onb_codes + buy_codes + ctl_codes:
        c[x] = c.get(x, 0) + 1
    return c


def onboarding():
    rows = []
    for s in slugs:
        v, it = V[s], V[s]["intake"]
        sub = day(v["rec"]["Submitted"])
        st = it["status"]
        sc = screens.get(s, {})
        if sc.get("result") == "EXCLUDED":
            nxt = "Excluded company in its paperwork: Legal reviews; follow-up on hold"
        elif v["packet"] and sc.get("recused"):
            nxt = f"Packet on hold: Legal reviews a disclosure; {E(who(sc['approvers'][0]))} signs ({E(sc['recused'][0])} recused)"
        elif v["packet"] and s in revisions:
            nxt = (f"Change asked during sign-off: {q(revisions[s]['packet'], 'version 2')} built; signing restarts with "
                   f"{E(who(revisions[s]['next']))}")
        elif v["packet"]:
            nxt = f"Packet built; waiting on {E(who(it['approvers'][0]))}"
        elif v["drafts"]:
            nxt = f"Follow-up drafted; {E(who('Facilities Manager'))} reviews and sends"
        else:
            nxt = "Intake done"
        blockers = " ".join(code(c) for c in it["issues"]) or '<span class="muted">none</span>'
        rows.append(f'<tr data-v="{s}" data-status="{st}"><td><b>{E(it["legal_name"])}</b><div class="muted">{E({"elevator_fire": "elevator and fire", "hvac": "HVAC"}.get(it["trade"], it["trade"].replace("_", " ")))}</div></td>'
                    f'<td class="num">{k(f"v.{s}.amount", dollars(v["req"]["Contract amount"]), True)}</td><td>{chip(st)}</td><td>{blockers}</td>'
                    f'<td class="num">{k(f"v.{s}.issues", len(it["issues"]))}</td><td>{nxt}</td>'
                    f'<td>{scchip(sc.get("result")) if sc else "<span class=muted>not run</span>"}</td>'
                    f'<td class="num">{k(f"v.{s}.approvers", len(tier_of(dollars(v["req"]["Contract amount"]))["approvers"]))}</td>'
                    f'<td class="num">{k(f"v.{s}.days", (DEMO - sub).days)}</td></tr>')
    vt = ('<h2>Vendors</h2><p class="lead">Status as of the demo date ' + rules["demo_date"] + ', from each vendor\'s intake record. Days waiting '
          'count from the day the vendor submitted. A person approves every vendor; the AI builds the packet.</p>'
          '<table data-audit><thead><tr><th>Vendor</th><th class="num">Contract</th><th>Status</th><th>Blocker</th><th class="num">Issues</th>'
          '<th>Next step</th><th>Screen</th><th class="num">Approvers</th><th class="num">Days waiting</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table>")
    xr = []
    for s in slugs:
        for doc, fld, tag, label in (("coi", "Policy end", "coi", "insurance certificate"), ("license", "Expires", "lic", "state license")):
            if doc not in V[s]["docs"]:
                continue
            end = V[s]["docs"][doc][fld]
            d = (day(end) - DEMO).days
            if d < 0:
                when = f"ended {k(f'x.{s}.{tag}.ago', -d)} days before the demo date"
            elif d <= EXPIRY_WINDOW:
                when = f"ends {k(f'x.{s}.{tag}.left', d)} days after the demo date"
            else:
                continue
            xr.append(f'<tr data-x="{s}:{tag}"><td>{E(V[s]["intake"]["legal_name"])}</td><td>{label}</td><td>{end}</td><td>{when}</td>'
                      f'<td>{chip(V[s]["intake"]["status"])}</td></tr>')
    xt = ('<h2>Insurance and licenses: ended or ending soon</h2><p class="lead">Read from the documents themselves; anything ending within '
          'the window in <code>dashboard/README.md</code> is listed.</p><table data-audit><thead><tr><th>Vendor</th><th>Document</th>'
          '<th>End date</th><th>When</th><th>Vendor status</th></tr></thead><tbody>' + "".join(xr) + "</tbody></table>")
    ev = []
    for s in slugs:
        v, it = V[s], V[s]["intake"]
        rel = f"vendors/{s}/intake.json"
        er = "".join(f"<tr><td>{q(rel, e['check'])}</td><td>{q(rel, e['found'])}</td><td>{q(rel, e['rule'])}</td>"
                     f"<td>{chip('OK', 'ok') if e['result'] == 'ok' else (q(rel, e['result']) if e['result'] != 'n/a' else 'n/a')}</td></tr>"
                     for e in it["evidence"])
        body = (f'<p class="muted">What <code>/intake</code> checked, quoted from <code>{rel}</code>.</p><table><thead><tr><th>Check</th>'
                f'<th>Found</th><th>Rule</th><th>Result</th></tr></thead><tbody>{er}</tbody></table>')
        for d in v["drafts"]:
            body += f'<h4>Follow-up draft (not sent): <code>{d}</code></h4>{pre(d)}'
        if v["packet"]:
            note = ''
            if screens.get(s, {}).get('recused'):
                sc_ = screens[s]
                note = (f'<p class="lead">This packet was built before the screening step. The screen recused {E(who(sc_["recused"][0]))} '
                        f'(a disclosed relative owns part of the firm), so {E(who(sc_["approvers"][0]))} signs instead, after Legal reviews. '
                        f'The packet record itself is left as it was.</p>')
            body += f'<h4>Approval packet (sign-offs blank on purpose): <code>{v["packet"]}</code></h4>{note}{pre(v["packet"])}'
        if s in revisions:
            rv = revisions[s]
            body += (f'<h4>E-signature export (a person exported it): <code>{rv["sources"][1]}</code></h4>{pre(rv["sources"][1])}'
                     f'<h4>Approval packet, newest version (sign-offs blank on purpose): <code>{rv["packet"]}</code></h4>{pre(rv["packet"])}')
        parts = ["what intake checked"] + (["the follow-up draft"] if v["drafts"] else []) + (["the approval packet"] if v["packet"] else []) \
            + (["the change during sign-off"] if s in revisions else [])
        ev.append(details(f'{chip(it["status"])} <b>{E(it["legal_name"])}</b> <span class="muted">{", ".join(parts)}</span>', body))
    return vt + xt + screening() + revisions_section() + certificates_section() + "<h2>The record behind each vendor</h2>" + "".join(ev)


def certificates_section():
    """Phase 3e (11/9): each certificate PDF read by /certs and checked against the typed copy. No digits in the table (nothing to recount)."""
    checks = sorted(glob.glob(os.path.join(ROOT, "vendors", "*", "documents", "coi-check.json")))
    if not checks:
        return ""
    rows_ = []
    for f in checks:
        c = json.load(open(f, encoding="utf-8"))
        s = c["vendor"]
        if c["result"] == "match":
            res = chip("OK", "matches the typed record")
        else:
            res = chip("FAIL", "differs") + " " + "; ".join(
                f"{E(d['field'].lower())} on the certificate doesn't match the typed record" for d in c["differences"]) + "; the Facilities Manager fixes the record"
        rows_.append(f'<tr data-cert="{s}" data-result="{c["result"]}"><td>{E(V[s]["intake"]["legal_name"])}</td>'
                     f'<td><code data-file="{c["pdf"]}">{E(c["pdf"])}</code></td><td>{res}</td></tr>')
    return ('<h2>Insurance certificates, read from the PDF</h2><p class="lead">Until now intake read a typed copy of each certificate. '
            'Here the AI opens the certificate PDF itself, reads every field, and checks the typed copy against it. The certificate is the '
            'source: where they differ, a person fixes the record. The AI changes nothing and sends nothing. Summary: '
            '<code>docs/certificates.md</code>.</p><table data-audit><thead><tr><th>Vendor</th><th>Certificate PDF</th><th>Result</th></tr></thead>'
            '<tbody>' + "".join(rows_) + "</tbody></table>")


def revisions_section():
    if not revisions:
        return ""
    rows_ = []
    for s, rv in revisions.items():
        v2 = rv["packet"]
        before = ", ".join(f"{E(people.get(r, r))} ({rv['signed_before_on'][r]})" for r in rv["signed_before"])
        rows_.append(f'<tr><td>{E(V[s]["intake"]["legal_name"])}</td><td>{q(v2, rv["change"])}</td>'
                     f'<td>{E(who(rv["requested_by"]))}, {rv["requested_on"]}</td><td>{before}</td>'
                     f'<td>{q(v2, "version 2")}: {k(f"v.{s}.approvers", len(rv["route"]))} sign-offs, blank, in order</td>'
                     f'<td>{E(who(rv["sender"]))} voids {q(v2, "version 1")} and sends the new one; {E(who(rv["next"]))} signs first again</td></tr>')
    mcl = exc_rules["revision"]["material_changes"]
    mc = ", ".join(mcl[:-1]) + ", or " + mcl[-1]
    return ('<h2>A change during sign-off</h2><p class="lead">A signer can catch something after others have signed. A change to the '
            f'{E(mc)} means a new version: the old signatures don\'t carry over, and signing starts again from the first approver. '
            'The AI builds the new version and marks what changed; a person voids the old one and sends the new one. '
            f'The e-signature export runs to {max(rv["requested_on"] for rv in revisions.values())}.</p>'
            '<table data-audit><thead><tr><th>Vendor</th><th>Change asked</th><th>Asked by</th><th>Had signed the old version</th>'
            '<th>New version</th><th>Next</th></tr></thead><tbody>' + "".join(rows_) + "</tbody></table>")


def scchip(r):
    return {"CLEAR": chip("OK", "clear"), "REVIEW": chip("PERSON", "Legal reviews"), "EXCLUDED": chip("FAIL", "excluded")}.get(r, "")


def screening():
    if not screens:
        return ""
    rows_ = []
    for s in slugs:
        sc = screens.get(s)
        if not sc:
            continue
        rel_ = f"vendors/{s}/screen.json"
        d = sc.get("disclosure", {})
        rels = "; ".join(q(rel_, r["Person"]) + ": " + q(rel_, r["Relationship"]) for r in d.get("relationships", [])) or '<span class="muted">none</span>'
        hits = ", ".join(q(rel_, m) for m in sc.get("matched", [])) or '<span class="muted">none</span>'
        rows_.append(f'<tr><td>{E(V[s]["intake"]["legal_name"])}</td><td>{q(rel_, d.get("signed_by", ""))}, '
                     f'{d.get("date", "")}</td><td>{rels}</td><td>{hits}</td><td>{scchip(sc["result"])} {" ".join(code(c) for c in sc["codes"])}</td>'
                     f'<td>{E(", ".join(sc.get("reviewers", [])) or "nobody")}</td></tr>')
    sup = sup_screen.get("suppliers", {})
    n_ex = sum(1 for v in sup.values() if v == "EXCLUDED")
    counts = {r: sum(1 for sc in screens.values() if sc["result"] == r) for r in ("CLEAR", "REVIEW", "EXCLUDED")}
    return ('<h2>Screening: conflict-of-interest disclosures and the exclusion list</h2><p class="lead">Copied from a real public-agency '
            'procurement packet (structure only; every record here is a fictional sample). Every contractor signs a disclosure, and every name in its paperwork is '
            'checked against a fictional exclusion list. Legal decides; the AI only flags.</p><table data-audit><thead><tr><th>Vendor</th>'
            '<th>Disclosure signed</th><th>Disclosed relationships</th><th>Exclusion matches</th><th>Screen</th><th>Who reviews</th></tr></thead><tbody>'
            + "".join(rows_) + '</tbody></table><table data-audit><tbody>'
            f'<tr><td>Contractors clear / for review / excluded</td><td class="num">{k("sc.CLEAR", counts["CLEAR"])} / {k("sc.REVIEW", counts["REVIEW"])} / '
            f'{k("sc.EXCLUDED", counts["EXCLUDED"])}</td></tr><tr><td>Approved furniture suppliers checked against the list / excluded</td>'
            f'<td class="num">{k("sc.suppliers", len(sup))} / {k("sc.sup_excluded", n_ex)}</td></tr></tbody></table>')


def buying():
    budget, committed = dollars(req["Budget"]), dollars(po["Total"])
    scale = max(budget, cr["new_total"]) * 1.04
    pct = lambda x: f"{x / scale * 100:.2f}%"
    meter = (f'<div class="meter" role="img" aria-label="Committed {committed} of {budget}; pending change to {cr["new_total"]}">'
             f'<div class="seg committed" style="width:{pct(committed)}" title="Committed on the approved order"></div>'
             f'<div class="seg pending" style="left:{pct(committed)};width:{pct(cr["new_total"] - committed)}" title="Pending change request"></div>'
             f'<div class="budgetline" style="left:{pct(budget)}" title="Budget"></div></div>'
             '<div class="legend"><span><i class="sw committed"></i>Committed on the approved order</span>'
             '<span><i class="sw pending"></i>Pending change request</span><span><i class="sw line"></i>Budget</span></div>')
    head = (f'<h2>{E(req["Building"].replace(" (fictional)", ""))}, {ident(unit, True)}: furnishing project</h2>'
            f'<p class="lead">Requested by {E(requester_name)}, {E(requester_role)}, on {req["Request date"]}; install by {req["Install by"]}. '
            f'A design partner wrote the furnishing plan; Palmquay buys. Scripted events in this sample project run to {tracking_asof}.</p>'
            f'<div class="budget" data-audit><div class="bnums"><div><span class="lab">Committed</span> {k("p.committed", committed, True)}</div>'
            f'<div><span class="lab">Budget</span> {k("p.budget", budget, True)}</div><div><span class="lab">Left</span> {k("p.headroom", budget - committed, True)}</div>'
            f'<div><span class="lab">If change {ident("CR-001")} is approved</span> {k("p.cr_total", cr["new_total"], True)}, '
            f'{k("p.cr_over", cr["over_by"], True)} over</div></div>{meter}</div>')
    cr_md = "projects/unit-4b/out/change-request-CR-001.md"
    detail = {
        "scope": f"A king needs {k('p.king_needs', brief['bed_needs_in'])} in; the wall is {k('p.wall', brief['wall_in'])} in. "
                 + q("projects/unit-4b/out/brief.md", "Before we order, please send: Bedroom wall B; and confirm a queen bed instead of a king."),
        "source": f"Sofa {ident(sofa_sku)} would arrive {k('p.sofa_late', sofa['days_late'])} days late, so the step named the cheapest "
                  f"sofa that meets the plan and arrives in time: {ident(src['alternative'][sofa_sku])}.",
        "quote": f"A {k('p.freight_hidden', sum(qv['freight'] for qv in quotes['quotes'].values() if 'HIDDEN_FREIGHT' in qv['codes']), True)} "
                 f"delivery charge found only in a footnote. " + q("projects/unit-4b/out/purchase-request-draft.md",
                                                                   "Before ordering, fix the flags: Q-GW-1 HIDDEN_FREIGHT; Q-MH-1 QUOTE_EXPIRED"),
        "approve": q("projects/unit-4b/out/approval.md", "98 in wide vs 96 in max") + " · "
                   + q("projects/unit-4b/out/approval.md", "chrome vs brushed nickel") + " · "
                   + q("projects/unit-4b/out/approval.md", "the listing doesn't state the fabric; the plan needs pet-friendly performance"),
        "change": f"+{k('p.cr_delta', cr['delta'], True)} for the substitute; total {k('p.cr_total', cr['new_total'], True)}, "
                  f"{k('p.cr_over', cr['over_by'], True)} over. " + q(cr_md, f"{cr['old_sku']} backordered; new ship date {new_ship}"),
        "deliver": f"Bed frame {k('p.bed_late', bed_days)} days late; the dresser is shipping to "
                   + q("projects/unit-4b/out/tasks.md", "Unit 4D") + f", not {ident(unit, True)}. "
                   + f"{k('p.exc', len(dlv['exceptions']))} exceptions, {k('p.tasks', dlv['tasks'])} tasks opened.",
        "match": f"Billed {k('p.inv_billed', hv['billed'], True)}, should be {k('p.inv_expected', hv['expected'], True)}: "
                 f"{k('p.inv_diff', hv['difference'], True)} held for Finance. Lamps billed "
                 + q("projects/unit-4b/out/match.md", "3 x $139") + ", ordered " + q("projects/unit-4b/out/match.md", "2 x $129") + "."}
    decides = {"scope": f"{E(requester_name)} answers (wall B still not recorded)", "source": "A person picks late-but-preferred or on time",
               "quote": f"{E(who('Facilities Manager'))} approves the purchase request", "approve": "A person decides the unclear chair",
               "change": f"{E(who('Facilities Manager'))} approves or rejects (waiting)", "deliver": f"{E(who('Facilities Manager'))} sends the update (waiting)",
               "match": f"{E(who('Finance'))} approves payment (waiting)"}
    done = {r["action"]: r for r in proc_rows}
    ar = []
    for i, (act, skill, name, short) in enumerate(ACTS, 1):
        codes = " ".join(code(c) for c, _ in per_act[short])
        state = chip("DONE", "ran") if act in done else chip("WAITING", "not run")
        ar.append(f'<tr><td><code>{skill}</code><div class="muted">{name}</div></td><td>{state}</td><td>{codes}</td>'
                  f'<td class="num">{k("pa." + short, len(per_act[short]))}</td><td>{detail[short]}</td><td>{decides[short]}</td></tr>')
    acts = ('<h2>The seven buying steps</h2><p class="lead">Each ran once, in order, and caught the problem planted for it. Quotes are word for '
            'word from the step\'s output file.</p><table data-audit><thead><tr><th>Step</th><th>Ran</th><th>Caught</th><th class="num">Flags</th>'
            '<th>Detail</th><th>Who decides</th></tr></thead><tbody>' + "".join(ar) + "</tbody></table>")
    dr = []
    for r in tracking:
        exc = dlv["exceptions"].get(r["SKU"])
        flag = code(exc) if exc else (f"on hold for change request {ident('CR-001')}" if r["SKU"] in dlv["covered_by_change"] else '<span class="muted">none</span>')
        shipto = "matches the order" if r["Ship to"] == po["Ship to"] else "different unit from the order"
        dr.append(f'<tr><td>{ident(r["SKU"])}</td><td>{E(r["Supplier"])}</td><td>{E(r["Status"])}</td><td>{r["ETA"] or "none"}</td>'
                  f'<td>{shipto}</td><td>{flag}</td></tr>')
    deliveries = (f'<h2>Deliveries as of {tracking_asof}</h2><table data-audit><thead><tr><th>Item</th><th>Supplier</th><th>Status</th><th>ETA</th>'
                  '<th>Ship to</th><th>Exception</th></tr></thead><tbody>' + "".join(dr) + "</tbody></table>")
    if credit:
        fc = exc_rules["freight_credit"]
        cr_rows = []
        for sup, sv in credit["suppliers"].items():
            for sku in sv["skus"]:
                it_ = credit["items"][sku]
                cr_rows.append(f'<tr><td>{ident(sku)} {E(plain_item(it_["item"]))}</td><td>{E(sup)}</td><td>{it_["promised"]}</td><td>{it_["eta"]}</td>'
                               f'<td class="num">{k("ex.credit_days", it_["days_past"])}</td><td class="num">{k("ex.credit_freight", sv["freight"], True)}</td>'
                               f'<td class="num">{q(sv["draft"], sv["credit"])}</td><td>{chip("WAITING", "drafted, not sent")} '
                               f'{E(who(credit["reviewer_and_sender"]))} reviews and sends</td></tr>')
        deliveries += ('<h2>Shipping credit for a late delivery</h2><p class="lead">When tracking shows an item '
                       f'{fc["days_past_promised"]} days or more past the date the order promised, the AI drafts a polite request asking that supplier to '
                       f'credit {fc["share_of_freight_percent"]}% of its freight on the order. It\'s an opening ask, and the supplier can say no; '
                       f'{E(who(credit["reviewer_and_sender"]))}, may change the amount before sending it.</p>'
                       '<table data-audit><thead><tr><th>Item</th><th>Supplier</th><th>Promised</th><th>ETA</th><th class="num">Days past promised</th>'
                       '<th class="num">Supplier\'s freight</th><th class="num">Credit asked</th><th>Status</th></tr></thead><tbody>'
                       + "".join(cr_rows) + "</tbody></table>")
    ir = []
    for inv, iv in mt["invoices"].items():
        if iv["result"] == "HOLD":
            money_ = f'{k("p.inv_billed", iv["billed"], True)}</td><td class="num">{k("p.inv_expected", iv["expected"], True)}</td><td class="num">{k("p.inv_diff", iv["difference"], True)}'
            res = chip("HOLD", "HOLD") + " " + " ".join(code(c) for c in iv["codes"])
        else:
            money_ = f'{k("p.inv_match_total", dollars(invoices[inv]["Total due"]), True)}</td><td class="num"><span class="muted">same</span></td><td class="num"><span class="muted">none</span>'
            res = chip("OK", "MATCH")
        ir.append(f'<tr><td>{ident(inv)}</td><td>{E(invoices[inv]["Supplier"])}</td><td>{res}</td><td class="num">{money_}</td>'
                  f'<td>{E(invoices[inv]["Payment status"])}; {E(who(mt["payment_approver"]))} decides</td></tr>')
    inv_t = ('<h2>Invoices: three-way match</h2><p class="lead">Invoice vs. the approved order vs. what arrived. The AI flags differences '
             f'and never marks anything paid. On hold for Finance: {k("p.inv_hold", len(held))}.</p><table data-audit><thead><tr><th>Invoice</th><th>Supplier</th><th>Result</th>'
             '<th class="num">Billed</th><th class="num">Should be</th><th class="num">Difference</th><th>Payment</th></tr></thead><tbody>'
             + "".join(ir) + "</tbody></table>")
    po_rel = "projects/unit-4b/approved/po-PQ-1042.md"
    decided = ('<h2>Already decided by people (recorded)</h2><ul class="plain">'
               f'<li>{q(po_rel, "Approved by: " + po["Approved by"])}, {q(po_rel, "Approved on: " + po["Approved on"])}: '
               f'purchase order {ident("PQ-1042")}, the approved baseline.</li>'
               f'<li>{q(po_rel, po["Notes"])}</li></ul>')
    files = ["projects/unit-4b/request.md", "projects/unit-4b/out/brief.md", "projects/unit-4b/out/source.md", "projects/unit-4b/out/quotes.md",
             "projects/unit-4b/out/purchase-request-draft.md", "projects/unit-4b/out/approval.md", po_rel, notice_rel, cr_md,
             "projects/unit-4b/out/tasks.md"] + upd_drafts + credit_drafts + ["projects/unit-4b/out/match.md"]
    ev = "".join(details(f"<code>{f}</code>", pre(f)) for f in files)
    return head + acts + deliveries + inv_t + decided + controls_section() + "<h2>The records</h2>" + ev


def controls_section():
    if not areq or not csum:
        return ""
    md_rel = "projects/unit-4b/controls/approval-request.md"
    md_t = read(*md_rel.split("/"))
    rows_ = []
    for line in table_rows(md_t, "SKU"):
        sku = line["SKU"]
        po_l = next(l for l in table_rows(po_text, "SKU") if l["SKU"] == sku)
        lt = int(po_l["Qty"]) * dollars(po_l["Unit price"])
        sups = [x.strip() for x in line["Suppliers with an in-spec price"].split(",")]
        low_sku = line["Lowest in-spec"].split()[0]
        flag = areq["flags"].get(sku)
        rows_.append(f'<tr><td>{ident(sku)}</td><td>{E(po_l["Item"])}</td><td class="num">{k(f"rq.{sku}.line", lt, True)}</td>'
                     f'<td class="num">{k(f"rq.{sku}.sources", len(sups))}</td><td>{ident(low_sku)} {k(f"rq.{sku}.lowest", dollars(catalog[low_sku]["Unit price"]), True)}</td>'
                     f'<td class="num">{k(f"rq.{sku}.selected", dollars(po_l["Unit price"]), True)}</td><td>{code(flag) if flag else chip("OK", "ok")}</td>'
                     f'<td>{q(md_rel, line["Justification"])}</td></tr>')
    req_t = ('<h2>Controls from a real procurement packet</h2><p class="lead">The approval request, running totals, and close-out copy the '
             'structure of a real public-agency packet; every record here is a fictional sample. Order PQ-1042 was approved before this checklist was added, so the '
             'request records what the checklist finds, for the file.</p>'
             f'<table data-audit><tbody><tr><td>Procurement type</td><td>{q(md_rel, areq["type"])}</td></tr>'
             f'<tr><td>Order total</td><td>{k("p.committed", areq["total"], True)}</td></tr>'
             f'<tr><td>Budget line, available, left</td><td>{q(md_rel, areq["budget_line"])}: {k("rq.available", areq["available"], True)} available, '
             f'{k("p.headroom", areq["left_after_order"], True)} left</td></tr>'
             f'<tr><td>Status</td><td>{chip("PERSON", areq["status"].replace("_", " ").lower())}; certification blank for '
             f'{E(who(areq["approvers"][0]))}</td></tr></tbody></table>'
             '<table data-audit><thead><tr><th>Line</th><th>Item</th><th class="num">Line total</th><th class="num">Suppliers in spec</th>'
             '<th>Lowest in-spec</th><th class="num">Selected price</th><th>Flag</th><th>Justification</th></tr></thead><tbody>'
             + "".join(rows_) + "</tbody></table>")
    c = csum
    tot = ('<h3>Running totals for order PQ-1042</h3><table data-audit><thead><tr><th class="num">Original</th><th class="num">Approved changes</th>'
           '<th class="num">Current</th><th class="num">Invoiced</th><th class="num">Approved to pay</th><th class="num">Paid</th>'
           '<th class="num">Held</th><th class="num">Remaining</th></tr></thead><tbody><tr>'
           + "".join(f'<td class="num">{k("co." + key, c[key], True)}</td>' for key in ("original", "approved_changes", "current", "invoiced",
                                                                                  "approved_for_payment", "paid", "held", "remaining"))
           + "</tr></tbody></table>")
    claim = c.get("claim", {})
    close = ('<table data-audit><tbody>'
             f'<tr><td>Lines received in full</td><td>{k("co.received", c["lines_received"])} of {k("co.lines", c["lines_total"])}</td></tr>'
             f'<tr><td>Open lines</td><td>{" ".join(ident(x) for x in c["open_lines"])}</td></tr>'
             f'<tr><td>Held invoices, pending changes, open tasks</td><td>{" ".join(ident(x) for x in c["held_invoices"] + c["pending_changes"] + c["open_tasks"])}</td></tr>'
             f'<tr><td>{E(claim.get("supplier", "Supplier"))} says all delivered</td><td>{code(claim.get("result", "")) if claim.get("result") == "CLAIM_CONTRADICTED" else chip("OK", "confirmed")} '
             f'not on the receipt: {" ".join(ident(x) for x in claim.get("not_delivered", []))}</td></tr>'
             f'<tr><td>Close-out</td><td>{code(c["status"])}; completion certificate: both signatures blank</td></tr></tbody></table>')
    files = ["controls/screen.md", md_rel, "projects/unit-4b/controls/contract-summary.md", "projects/unit-4b/controls/completion-certificate.md"] + reply_drafts
    return req_t + tot + close + "".join(details(f"<code>{f}</code>", pre(f)) for f in files)


def checks():
    rows = []
    what = {"p1": "The fictional company, its rules, the vendors' planted problems, and the locked answer key",
            "p2": "Onboarding: intake, follow-up drafts, approval packets, the checker, the audit log",
            "p3a": "Buying: all seven steps against their locked answer key, the procurement log, the checker",
            "p3c": "Controls from the real packet against their locked answer key (its check of the older phases runs separately)",
            "p3d": "Real-world exceptions (a change during sign-off, a shipping credit) against their locked answer key (its check of the older phases runs separately)"}
    for c, v in CHECKS.items():
        res = (f'{k(f"c.{c}.pass", v["pass"])} of {k(f"c.{c}.total", v["total"])} ' + chip("PASS" if v["pass"] == v["total"] and v["rc"] == 0 else "FAIL",
               "PASS" if v["pass"] == v["total"] and v["rc"] == 0 else "FAIL")) if v["pass"] is not None else chip("FAIL", "no result")
        rows.append(f'<tr><td>{ident(v["label"], True)}</td><td>{E(what[c])}</td><td>{res}</td></tr>')
    t = ('<h2>Acceptance checks, run when this page was built</h2><p class="lead">Each check was written before the work it tests, recomputes '
         'every result its own way, and prints what it counted. A check that can\'t fail proves nothing, so each check script also has a self-test that plants '
         'breaks in a throwaway copy.</p><table data-audit><thead><tr><th>Phase</th><th>What it checks</th><th>Result</th></tr></thead><tbody>'
         + "".join(rows) + "</tbody></table>")
    t += "".join(details(f'{E(v["label"])}: every line it printed ({v["secs"]} s)', "<pre>" + E("\n".join(v["lines"])) + "</pre>") for v in CHECKS.values())
    cmds = "\n".join(f"python -I -X utf8 {v['file']}\npython -I -X utf8 {v['file']} --selftest" for v in CHECKS.values())
    t += details("Run them yourself (self-tests take longer)", f"<pre>{E(cmds)}</pre>")
    rr = []
    for lg, r in reviews:
        rel = {"onb": "audit/audit-log.csv", "proc": "audit/procurement-log.csv", "ctl": "audit/controls-log.csv", "exc": "audit/exceptions-log.csv"}[lg]
        rr.append(f'<tr><td>{E(r["timestamp"].replace("T", " "))}</td><td>{" ".join(ident(x) if re.search(r"\d", x) else E(x) for x in r["vendor"].split(" "))}</td><td>{q(rel, r["detail"])}</td><td>{q(rel, r["result"])}</td></tr>')
    t += ('<h2>The checker: a second AI, set up to only read</h2><p class="lead">It reviews the first AI\'s work blind, against the rules. Its definition gives it read and search tools only. In the Phase 1-3a reviews that limit was an instruction, not enforced; the Phase 3c review ran as a separate agent with no write tools. Each review records how it ran. The first buying review also found one real gap: a rule\'s wording didn\'t cover a substitute\'s order date (the answers were right); the rule was clarified and the second review ran on the same files. Each review '
          'mixed in a copy with a planted mistake to prove it was really reading. '
          f'Reviews logged: {k("a.reviews", len(reviews))}.</p>'
          '<table data-audit><thead><tr><th>When</th><th>Subject</th><th>What it reviewed</th><th>Result</th></tr></thead><tbody>' + "".join(rr) + "</tbody></table>")
    t += ('<h2>Guardrails, counted</h2><table data-audit><tbody>'
          f'<tr><td>Log rows where the AI sent, signed, approved, ordered, or paid</td><td class="num">{k("g.ai_people", ai_people)}</td></tr>'
          f'<tr><td>Drafts written and marked not sent (a person sends)</td><td class="num">{k("g.drafts", len(unsent))}</td></tr>'
          f'<tr><td>Packet sign-off lines left blank for a person</td><td class="num">{k("g.blank", blank_signoffs)}</td></tr>'
          f'<tr><td>Approval lines left blank on the purchase request and change request</td><td class="num">{k("g.blank_lines", len(blank_lines))}</td></tr>'
          '</tbody></table>')
    return t


def audit():
    ok = onb_links == len(onb_rows) and proc_links == len(proc_rows) and ctl_links == len(ctl_rows) and exc_links == len(exc_rows)
    head = ('<h2>Replay the run</h2><p class="lead">The page rebuilds the board from the audit log, one row at a time. Press play, or drag. '
            'The log is append-only by rule and hash-chained: editing any past row breaks every link after it.</p>'
            '<div class="replay"><div class="controls"><button id="play" type="button">&#9654; Play</button>'
            '<input id="step" type="range" min="0" value="0" aria-label="Replay step"><span id="steplabel" class="muted"></span></div>'
            '<div id="nowevent" class="nowevent"></div><div class="board"><div><h4>Vendors</h4><div id="rvendors" class="rgrid"></div></div>'
            '<div><h4>Buying steps, controls, and exceptions</h4><div id="racts" class="rgrid"></div></div></div><div id="rcount" class="muted"></div></div>')
    chain_t = ('<h2>Hash chains</h2><table data-audit><tbody>'
               f'<tr><td>Onboarding log</td><td class="num">{k("a.onb", len(onb_rows))} rows</td><td>{k("a.onb_links", onb_links) if onb_links is not None else "FAILED"} links verify</td></tr>'
               f'<tr><td>Procurement log</td><td class="num">{k("a.proc", len(proc_rows))} rows</td><td>{k("a.proc_links", proc_links) if proc_links is not None else "FAILED"} links verify</td></tr>'
               f'<tr><td>Controls log</td><td class="num">{k("a.ctl", len(ctl_rows))} rows</td><td>{k("a.ctl_links", ctl_links) if ctl_links is not None else "FAILED"} links verify</td></tr>'
               + (f'<tr><td>Exceptions log</td><td class="num">{k("a.exc", len(exc_rows))} rows</td><td>{k("a.exc_links", exc_links) if exc_links is not None else "FAILED"} links verify</td></tr>' if exc_rows else "")
               + f'</tbody></table><p>{chip("OK", ("All four" if exc_rows else "All three" if ctl_rows else "Both") + " chains verify") if ok else chip("FAIL", "A chain does not verify")}</p>')
    rows = []
    for lg, name, rs in (("onb", "audit/audit-log.csv", onb_rows), ("proc", "audit/procurement-log.csv", proc_rows),
                         ("ctl", "audit/controls-log.csv", ctl_rows), ("exc", "audit/exceptions-log.csv", exc_rows)):
        for i, r in enumerate(rs, 1):
            rows.append(f'<tr data-log="{lg}" data-i="{i}"><td class="nowrap">{E(r["timestamp"])}</td><td>{E(r["actor"])}</td><td>{E(r["vendor"])}</td>'
                        f'<td>{E(r["action"])}</td><td>{E(r["result"])}</td><td class="muted small">{E(r["detail"])}</td></tr>')
    table = ('<h2>Every row</h2><table class="log"><thead><tr><th>Time</th><th>Actor</th><th>Subject</th><th>Action</th><th>Result</th>'
             '<th>Detail</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table>")
    return head + chain_t + table


def diagram():
    f = path("docs", "diagram.html")
    if not os.path.exists(f):
        return "<p>The diagram isn't built yet (docs/diagram.html).</p>"
    m = re.search(r"<!-- DIAGRAM START -->.*?<!-- DIAGRAM END -->", open(f, encoding="utf-8").read(), re.S)
    return m.group(0) if m else "<p>docs/diagram.html has no diagram markers.</p>"


events = sorted([{"log": "onb", "i": i, "t": r["timestamp"], "actor": r["actor"], "subject": r["vendor"], "action": r["action"],
                  "detail": r["detail"], "result": r["result"]} for i, r in enumerate(onb_rows, 1)] +
                [{"log": "proc", "i": i, "t": r["timestamp"], "actor": r["actor"], "subject": r["vendor"], "action": r["action"],
                  "detail": r["detail"], "result": r["result"]} for i, r in enumerate(proc_rows, 1)] +
                [{"log": "ctl", "i": i, "t": r["timestamp"], "actor": r["actor"], "subject": r["vendor"], "action": r["action"],
                  "detail": r["detail"], "result": r["result"]} for i, r in enumerate(ctl_rows, 1)] +
                [{"log": "exc", "i": i, "t": r["timestamp"], "actor": r["actor"], "subject": r["vendor"], "action": r["action"],
                  "detail": r["detail"], "result": r["result"]} for i, r in enumerate(exc_rows, 1)], key=lambda e: e["t"])
rvendors = [{"slug": s, "name": V[s]["intake"]["legal_name"]} for s in slugs]
racts = [{"action": a, "skill": sk, "name": nm} for a, sk, nm, _ in ACTS]
if ctl_rows:
    racts += [{"action": "screen", "skill": "/screen", "name": "Disclosures + exclusion list"},
              {"action": "approval_request", "skill": "/request", "name": "Approval request"},
              {"action": "closeout", "skill": "/closeout", "name": "Running totals + close-out"}]
if exc_rows:
    racts += [{"action": "packet_revision", "skill": "/revise", "name": "A change during sign-off"},
              {"action": "freight_credit", "skill": "/credit", "name": "Shipping credit for a late delivery"}]

CSS = """
:root{--bg:#f4f4f1;--surface:#fcfcfb;--card:#fff;--ink:#0b0b0b;--ink2:#52514e;--line:#e2e1dc;--accent:#1d5a85;--good:#0ca30c;--warn:#fab219;--serious:#ec835a;--crit:#d03b3b;--soft:#f1f0ec}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 "Segoe UI",system-ui,sans-serif;color:var(--ink);background:var(--bg)}
header{background:var(--surface);border-bottom:1px solid var(--line);padding:16px 24px 0;position:sticky;top:0;z-index:5}
.top{display:flex;justify-content:space-between;align-items:baseline;gap:16px;flex-wrap:wrap}h1{font-size:19px;margin:0}
.stamp{font-size:12px;color:var(--ink2)}.org{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px;margin-bottom:6px}.people{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}.person{text-align:center;padding:10px 6px;border-radius:8px;border-top:4px solid var(--pc);background:var(--surface)}.avatar{width:52px;height:52px;display:block;margin:0 auto 6px}.pname{font-weight:600}.title{font-size:12.5px}.dept{font-size:11.5px;color:var(--ink2)}.does{font-size:11.5px;color:var(--ink2);margin-top:4px}.helpers{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px}.helper{font-size:12px;color:var(--ink2);border:1px dashed var(--line);border-radius:6px;padding:5px 9px}.org[data-hub] .people{position:relative;grid-template-columns:repeat(3,minmax(0,1fr));grid-template-areas:"a b c" "ai core chk" "d . e";gap:10px 56px}.org[data-hub] .person{position:relative;z-index:1;padding:6px 6px 7px}.org[data-hub] .title,.org[data-hub] .dept{display:inline}.org[data-hub] .dept::before{content:" · "}.org[data-hub] .person:nth-child(1){grid-area:a}.org[data-hub] .person:nth-child(2){grid-area:b}.org[data-hub] .person:nth-child(3){grid-area:c}.org[data-hub] .person:nth-child(4){grid-area:d}.org[data-hub] .person:nth-child(5){grid-area:e}.org[data-hub] .avatar{width:34px;height:34px;margin-bottom:2px}.org[data-hub] .core{grid-area:core;z-index:1;justify-self:center;align-self:center;display:flex;flex-direction:column;justify-content:center;gap:3px;width:128px;height:128px;padding:10px;border-radius:50%;background:var(--accent);color:#fff;text-align:center;font-size:11.5px;line-height:1.3}.org[data-hub] .core b{font-size:13px}.org[data-hub] .helper{z-index:1;align-self:center;background:var(--card);font-size:11.5px;max-width:240px}.org[data-hub] .ai{grid-area:ai;justify-self:end}.org[data-hub] .chk{grid-area:chk;justify-self:start}.spokes{position:absolute;inset:0;width:100%;height:100%;z-index:0;pointer-events:none}.spokes line{stroke:#9fb4c6;stroke-width:2;stroke-dasharray:5 5;vector-effect:non-scaling-stroke}.uses{font-size:11px;color:var(--ink2);margin-top:4px}.uses code{font-size:10.5px;padding:0 3px}.wait{font-size:11.5px;font-weight:600;margin-top:3px}@media (max-width:760px){.org[data-hub] .people{display:flex;flex-direction:column}.spokes{display:none}.org[data-hub] .core{width:auto;height:auto;border-radius:8px}}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:middle}.tiles{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));gap:10px;margin:12px 0 4px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:9px 11px}.tile .lab{font-size:12px;color:var(--ink2)}
.tile .big{font-size:23px;font-weight:600;line-height:1.25;font-variant-numeric:tabular-nums}.tile .small{font-size:11.5px;color:var(--ink2)}
nav{display:flex;gap:2px;margin-top:6px}nav button{border:0;background:none;padding:9px 14px;font:inherit;color:var(--ink2);border-bottom:2px solid transparent;cursor:pointer}
nav button[aria-selected=true]{color:var(--ink);border-bottom-color:var(--accent);font-weight:600}main{padding:6px 24px 48px;max-width:1500px}
section[data-tab]{display:none}section.on{display:block}h2{font-size:16px;margin:22px 0 4px}h4{margin:12px 0 6px;font-size:13px}
.lead{color:var(--ink2);margin:0 0 10px;max-width:980px}table{border-collapse:separate;border-spacing:0;width:100%;background:var(--card);border:1px solid var(--line);border-radius:8px;font-size:13px;margin-bottom:6px}
th,td{padding:7px 10px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}tr:last-child td{border-bottom:0}
th{font-size:12px;color:var(--ink2);font-weight:600;background:var(--soft)}.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.nowrap{white-space:nowrap}.muted{color:var(--ink2)}.small{font-size:11.5px}code,.code,.id{font:12px Consolas,"Cascadia Mono",monospace}
code,.code{background:var(--soft);padding:1px 4px;border-radius:4px}.id.plain{font:inherit}.code{display:inline-block;margin:1px 2px 1px 0}
.src{border-bottom:1px dotted #8a8983}.chip{display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:600;white-space:nowrap}
.chip i{font-style:normal;display:inline-grid;place-items:center;min-width:16px;height:16px;border-radius:8px;color:#fff;font-size:9px;padding:0 3px}
.st-READY i,.st-OK i,.st-PASS i,.st-DONE i{background:var(--good)}.st-HOLD i,.st-WAITING i{background:var(--warn);color:#0b0b0b}
.st-BLOCKED i,.st-FAIL i{background:var(--crit)}.st-PERSON i{background:var(--serious)}.st-SUBMITTED i{background:#8f8e88}
details{background:var(--card);border:1px solid var(--line);border-radius:8px;margin:6px 0;padding:6px 10px}summary{cursor:pointer;padding:2px 0}
pre{white-space:pre-wrap;font:12px/1.45 Consolas,"Cascadia Mono",monospace;background:#fbfbf9;border:1px solid var(--line);padding:10px;border-radius:6px;max-height:460px;overflow:auto}
.budget{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:8px 0}.bnums{display:flex;gap:28px;flex-wrap:wrap;font-size:15px;font-weight:600}
.bnums .lab{display:block;font-size:12px;font-weight:400;color:var(--ink2)}.meter{position:relative;height:16px;background:var(--soft);border-radius:4px;margin:12px 0 6px}
.seg{position:absolute;top:0;bottom:0}.seg.committed{left:0;background:var(--accent);border-radius:4px 0 0 4px}
.seg.pending{background:repeating-linear-gradient(45deg,#d9a03a 0 4px,#f5d58f 4px 8px);border-radius:0 4px 4px 0;border-left:2px solid var(--surface)}
.budgetline{position:absolute;top:-4px;bottom:-4px;width:2px;background:var(--ink)}.legend{display:flex;gap:18px;font-size:12px;color:var(--ink2)}
.sw{display:inline-block;width:12px;height:10px;margin-right:5px;vertical-align:-1px;border-radius:2px}.sw.committed{background:var(--accent)}
.sw.pending{background:repeating-linear-gradient(45deg,#d9a03a 0 3px,#f5d58f 3px 6px)}.sw.line{width:2px;background:var(--ink)}
ul.plain{padding-left:18px}.replay{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px}
.controls{display:flex;gap:12px;align-items:center}.controls input{flex:1}.controls button{font:inherit;padding:5px 14px;border:1px solid var(--line);border-radius:6px;background:var(--soft);cursor:pointer}
.nowevent{margin:10px 0;padding:8px 10px;background:var(--soft);border-radius:6px;min-height:38px;font-size:13px}
.board{display:grid;grid-template-columns:1fr 1fr;gap:18px}.rgrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}
.rc{border:1px solid var(--line);border-radius:6px;padding:6px 8px;font-size:12.5px;transition:background .3s}.rc.flash{background:#fff4d6}
.rc .badges{font-size:11px;color:var(--ink2)}table.log td{font-size:12px}
@media (max-width:1180px){.tiles{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}header{position:static}.board{grid-template-columns:1fr}}
"""

JS = """
(function(){
  var errs=0;window.addEventListener('error',function(){errs++;document.body.setAttribute('data-errors',String(errs));});
  var sections=[].slice.call(document.querySelectorAll('section[data-tab]')),buttons=[].slice.call(document.querySelectorAll('nav button'));
  function show(id){sections.forEach(function(s){s.classList.toggle('on',s.getAttribute('data-tab')===id);});
    buttons.forEach(function(b){b.setAttribute('aria-selected',b.getAttribute('data-for')===id?'true':'false');});}
  buttons.forEach(function(b){b.addEventListener('click',function(){show(b.getAttribute('data-for'));history.replaceState(null,'','#tab='+b.getAttribute('data-for'));});});
  var ev=JSON.parse(document.getElementById('replay-data').textContent),vs=JSON.parse(document.getElementById('replay-vendors').textContent),
      acts=JSON.parse(document.getElementById('replay-acts').textContent),slider=document.getElementById('step'),timer=null;
  slider.max=String(ev.length);
  function stateAt(n){var st={v:{},a:{},drafts:0,packets:0,reviews:0};
    vs.forEach(function(v){st.v[v.slug]={status:'SUBMITTED',draft:false,packet:false};});
    for(var i=0;i<n;i++){var e=ev[i];
      if(e.log==='onb'){var v=st.v[e.subject];
        if(e.action==='intake'){var m=/status (\\w+)/.exec(e.detail);if(v&&m)v.status=m[1];}
        else if(e.action==='chase_draft'){if(v)v.draft=true;st.drafts++;}
        else if(e.action==='route_packet'){if(v)v.packet=true;st.packets++;}
        else if(e.action==='checker_review'){st.reviews++;}}
      else{if(e.action==='checker_review')st.reviews++;else st.a[e.action]=e.result;}}
    return st;}
  var label={SUBMITTED:'SUBMITTED',READY:'READY',HOLD:'HOLD',BLOCKED:'BLOCKED'},icon={SUBMITTED:'\\u2022',READY:'\\u2713',HOLD:'\\u275a\\u275a',BLOCKED:'\\u2715'};
  function chip(s){return '<span class="chip st-'+s+'"><i aria-hidden="true">'+icon[s]+'</i>'+label[s]+'</span>';}
  function esc(t){return String(t).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  function render(n){var st=stateAt(n),last=n>0?ev[n-1]:null;
    document.getElementById('rvendors').innerHTML=vs.map(function(v){var s=st.v[v.slug],b=[];if(s.draft)b.push('follow-up drafted, not sent');if(s.packet)b.push('packet built, unsigned');
      return '<div class="rc'+(last&&last.subject===v.slug?' flash':'')+'" data-rv="'+v.slug+'" data-status="'+s.status+'"><div>'+esc(v.name)+'</div>'+chip(s.status)+'<div class="badges">'+b.join(' \\u00b7 ')+'</div></div>';}).join('');
    document.getElementById('racts').innerHTML=acts.map(function(a){var r=st.a[a.action];
      return '<div class="rc'+(last&&last.action===a.action?' flash':'')+'" data-ra="'+a.action+'" data-done="'+(r!==undefined?'1':'0')+'"><div><code>'+a.skill+'</code> '+esc(a.name)+'</div><div class="badges">'+(r!==undefined?esc(r):'not run yet')+'</div></div>';}).join('');
    document.getElementById('steplabel').textContent='Row '+n+' of '+ev.length;
    document.getElementById('nowevent').innerHTML=last?('<b>'+esc(last.t.replace('T',' '))+'</b> \\u00b7 '+esc(last.actor)+' \\u00b7 <code>'+esc(last.action)+'</code> \\u00b7 '+esc(last.subject)+' \\u2192 '+esc(last.result)):('Before the first row: '+vs.length+' vendors have sent paperwork; nothing has been reviewed yet.');
    document.getElementById('rcount').textContent='Follow-ups drafted: '+st.drafts+' \\u00b7 approval packets built: '+st.packets+' \\u00b7 checker reviews: '+st.reviews+' \\u00b7 sent, signed, ordered, or paid by the AI: 0';
    slider.value=String(n);document.getElementById('replay').setAttribute('data-rstep',String(n));}
  slider.addEventListener('input',function(){stop();render(parseInt(slider.value,10));});
  function stop(){if(timer){clearInterval(timer);timer=null;document.getElementById('play').innerHTML='\\u25b6 Play';}}
  document.getElementById('play').addEventListener('click',function(){if(timer){stop();return;}var n=parseInt(slider.value,10);if(n>=ev.length)n=0;render(n);
    this.innerHTML='\\u275a\\u275a Pause';timer=setInterval(function(){n++;render(n);if(n>=ev.length)stop();},280);});
  function fromHash(){var h=location.hash.replace('#','');var m=/(?:^|&)tab=(\\w+)/.exec(h),r=/(?:^|&)replay=(\\d+)/.exec(h);
    if(r){show('audit');render(Math.min(parseInt(r[1],10),ev.length));}else{show(m?m[1]:'overview');render(0);}}
  window.addEventListener('hashchange',fromHash);fromHash();
  document.body.setAttribute('data-rendered',String(sections.length));
})();
"""


def page():
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    head_tiles = tiles()
    secs = {"overview": overview(), "onboarding": onboarding(), "buying": buying(), "checks": checks(), "audit": audit(), "map": diagram()}
    nav = "".join(f'<button type="button" data-for="{t}" data-tab-label="{lab}" aria-selected="false">{lab}</button>' for t, lab in TABS)
    body = "".join(f'<section data-tab="{t}" id="tab-{t}"{" class=on" if t == "overview" else ""}>{secs[t]}</section>' for t, _ in TABS)
    body = body.replace('<div class="replay">', '<div class="replay" id="replay" data-rstep="0">')
    def data(i, obj):
        payload = json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")
        return f'<script id="{i}" type="application/json">{payload}</script>'
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Palmquay Properties: AI operations dashboard (fictional)</title>'
            f"<style>{CSS}</style></head>"
            '<body data-rendered="0" data-errors="0"><header><div class="top"><h1>Palmquay Properties &middot; AI operations dashboard</h1>'
            f'<div class="stamp">Fictional company with sample records. Built {stamp} from those records; '
            f'a test recounts every number in its tiles and tables. <a href="../video/">Watch the walkthrough</a></div></div>'
            f"{head_tiles}<nav>{nav}</nav></header><main>{body}</main>"
            + data("replay-data", events) + data("replay-vendors", rvendors) + data("replay-acts", racts)
            + f"<script>{JS}</script></body></html>")


def main():
    html_text = page()
    os.makedirs(OUT, exist_ok=True)
    html_text = html_text.replace("{SECS}", f"{time.time() - T0:.1f}")
    cut = html_text.index('<script id="replay-data"')  # line breaks between cells, so no two cells read as one word; never inside the scripts
    head_part, scripts = html_text[:cut], html_text[cut:]
    dg = re.search(r"<!-- DIAGRAM START -->.*?<!-- DIAGRAM END -->", head_part, re.S)  # the Map tab keeps the diagram byte for byte
    keep = dg.group(0) if dg else ""
    head_part = head_part.replace(keep, "\0DIAGRAM\0") if keep else head_part
    head_part = re.sub(r"(</t[dh]>|</tr>|</div>|</li>)", r"\1\n", head_part)
    html_text = (head_part.replace("\0DIAGRAM\0", keep) if keep else head_part) + scripts
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(html_text)
    json.dump({"built": dt.datetime.now().isoformat(timespec="seconds"), "facts": K,
               "waiting": [{"since": w[0], "key": w[1], "owner": w[2], "who": w[3], "record": w[7]} for w in W],
               "checks": {c: {kk: v[kk] for kk in ("label", "pass", "total", "rc")} for c, v in CHECKS.items()},
               "events": len(events)}, open(os.path.join(OUT, "data.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    fails = [c for c, v in CHECKS.items() if v["pass"] is None or v["pass"] != v["total"] or v["rc"] != 0]
    summary = ", ".join(f"{v['label']} {v['pass']} of {v['total']}" for v in CHECKS.values())
    print(f"{'PASS' if not fails and onb_links is not None and proc_links is not None else 'WARN'} - built {os.path.join(OUT, 'index.html')} "
          f"in {time.time() - T0:.1f} s: {len(K)} tagged facts, {len(W)} decisions waiting on people, {len(events)} replay events; "
          f"checks {summary}; chains {onb_links} + {proc_links} links")
    return 0


if __name__ == "__main__":
    sys.exit(main())
