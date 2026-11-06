"""Phase 3c acceptance check: controls copied from a real public-agency procurement packet (structure only, fake data).

Written 11/6/2026 before tools/controls.py or the /screen, /request, /closeout skills existed. It never imports the helper:
it recounts every result from the raw inputs its own way. Prints what it counted; exit 1 on any FAIL.

    python -I -X utf8 tests/check_phase3c.py               R0-R9
    python -I -X utf8 tests/check_phase3c.py --selftest    plant one break per check in a temp copy; each must FAIL its own check

Options: --root DIR (check a copy) · --copy (older checks are told they run on a copy) · --skip-old-phases (self-test speed)
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

HERE = os.path.dirname(os.path.abspath(__file__))
COPY = "--copy" in sys.argv
NO_OLD = "--skip-old-phases" in sys.argv
ROOT = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.dirname(HERE)
PROJ = "projects/unit-4b"
LOG, CHAIN = "audit/controls-log.csv", "audit/controls-log.chain.txt"
HEADER = "timestamp,actor,vendor,action,detail,result"
ACTIONS = {"screen": "onboarding-assistant", "approval_request": "procurement-assistant", "closeout": "procurement-assistant",
           "checker_review": "compliance-checker"}
SKILLS = ["screen", "request", "closeout"]
NEW_INPUTS = ["company/exclusion-list.md", f"{PROJ}/funding.md", f"{PROJ}/closeout/2026-11-12-gulfweave-completion.md"]
results = []


def rec(ok, name, counted):
    ok = bool(ok)
    results.append((ok, name))
    print(f"{'PASS' if ok else 'FAIL'} - {name} - {counted}")


def p(*a):
    return os.path.join(ROOT, *a)


def read(rel):
    f = p(*rel.split("/"))
    return open(f, encoding="utf-8").read() if os.path.exists(f) else ""


def jload(rel):
    t = read(rel)
    return json.loads(t) if t.strip() else None


def sha(rel):
    f = p(*rel.split("/"))
    return hashlib.sha256(open(f, "rb").read()).hexdigest() if os.path.exists(f) else "missing"


def fields(t):
    out = {}
    for line in t.splitlines():
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", line) or re.match(r"^([A-Z][A-Za-z ,()/'-]*?):[ \t]*(.*)$", line)
        if m and m.group(1) not in out:
            out[m.group(1)] = m.group(2).strip()
    return out


def table(t, first):
    lines = t.splitlines()
    for i, line in enumerate(lines):
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if line.startswith("|") and c and c[0] == first:
            out = []
            for row in lines[i + 2:]:
                if not row.startswith("|"):
                    break
                out.append(dict(zip(c, [x.strip() for x in row.strip().strip("|").split("|")])))
            return out
    return []


def money(s):
    return int(re.sub(r"[^\d]", "", s))


def day(s):
    return dt.date.fromisoformat(s.strip()[:10])


def norm_name(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


# ------------------------------------------------------------- the check's own recount -------------------------------------------------------------
def recount():
    rules = json.loads(read("company/rules.json"))
    c = rules["controls"]
    demo = day(rules["demo_date"])
    roles = {}
    for r in table(read("company/people.md"), "Role"):
        roles[re.sub(r"\s*\(.*?\)", "", r["Role"]).strip()] = r["Name"]
    active = {norm_name(r["Excluded party"]): r["Excluded party"] for r in table(read("company/exclusion-list.md"), "Excluded party")
              if day(r["Excluded from"]) <= demo <= day(r["Excluded until"])}
    out = {"screen": {"vendors": {}, "suppliers": {}}}
    for s in sorted(d for d in os.listdir(p("vendors")) if os.path.isdir(p("vendors", d))):
        docs = {k: fields(read(f"vendors/{s}/documents/{k}.md")) for k in ("w9", "coi", "license")}
        names = [docs["w9"].get("Legal name"), docs["coi"].get("Insured"), docs["license"].get("License holder")]
        codes, v = [], {}
        dt_ = read(f"vendors/{s}/{c['disclosure_file']}")
        rels = []
        if not dt_:
            codes.append("MISSING_DISCLOSURE")
        else:
            f = fields(dt_)
            names += [f.get("Firm"), f.get("Signed by")]
            paid = next((val for k, val in f.items() if k.startswith("No one was paid")), "")
            if not paid.startswith("Yes"):
                codes.append("PAID_SOLICITATION")
            rels = [r for r in table(dt_, "Person") if r.get("Person") and r["Person"] != "none"]
            names += [r["Person"] for r in rels]
            if rels:
                codes.append("CONFLICT_DISCLOSED")
        matched = sorted({active[norm_name(n)] for n in names if n and norm_name(n) in active})
        if matched:
            codes.append("EXCLUDED")
        result = "EXCLUDED" if "EXCLUDED" in codes else ("REVIEW" if codes else "CLEAR")
        v = {"result": result, "codes": sorted(codes)}
        if result != "CLEAR":
            v["reviewers"] = [c["exclusion_reviewer"] if result == "EXCLUDED" else c["disclosure_reviewer"]]
        if matched:
            v["matched"] = matched
            v["hold_followup"] = bool(glob.glob(p("vendors", s, "drafts", "*.md")))
        if rels:
            amount = money(fields(read(f"vendors/{s}/documents/request.md"))["Contract amount"])
            tier = next(t for t in rules["approval_tiers"] if t["max_amount"] is None or amount <= t["max_amount"])["approvers"]
            recused = sorted({role for r in rels for role, name in roles.items() if name in r["Relationship"] and role in tier})
            if recused:
                keep = [a for a in tier if a not in recused]
                for role in c["approval_order"]:
                    if len(keep) >= len(tier):
                        break
                    if role not in keep and role not in recused:
                        keep.append(role)
                v["recused"], v["approvers"] = recused, keep
        out["screen"]["vendors"][s] = v
    for r in table(read("company/approved-suppliers.md"), "Supplier"):
        out["screen"]["suppliers"][r["Supplier"]] = "EXCLUDED" if norm_name(r["Supplier"]) in active else "CLEAR"

    # approval request
    po_t = read(f"{PROJ}/approved/po-PQ-1042.md")
    po_lines = table(po_t, "SKU")
    total = money(fields(po_t)["Total"])
    ptype = next(t for t in c["procurement_types"] if t["max_amount"] is None or total <= t["max_amount"])
    fund = fields(read(f"{PROJ}/funding.md"))
    available = money(fund["Available"])
    plan = {r["Item"]: r for r in table(read(f"{PROJ}/partner-plan.md"), "Line")}
    approved_sup = {r["Supplier"] for r in table(read("company/approved-suppliers.md"), "Supplier") if r.get("Status") == "Approved"}
    catalog = []
    for f in sorted(glob.glob(p(*PROJ.split("/"), "catalogs", "*.md"))):
        t = open(f, encoding="utf-8").read()
        sup = fields(t)["Supplier"]
        catalog += [dict(r, supplier=sup) for r in table(t, "SKU")]
    src = jload(f"{PROJ}/out/source.json") or {}
    appr = jload(f"{PROJ}/out/approval.json") or {"FAIL": {}}
    proposed = {r["Line"]: r["SKU"] for r in table(read(f"{PROJ}/proposed.md"), "Line")}
    failed_skus = {proposed.get(ln): code for ln, code in appr.get("FAIL", {}).items()}

    def in_spec(item, row):
        pl = plan[item]
        ok = int(row["Width (in)"]) <= int(pl["Max width (in)"]) and int(row["Depth (in)"]) <= int(pl["Max depth (in)"])
        ok &= pl["Finish"] == "any" or row["Finish"] == pl["Finish"]
        ok &= pl["Fabric"] == "any" or row["Fabric"] == pl["Fabric"]
        return ok and row["supplier"] in approved_sup

    req = {"type": ptype["name"], "total": total, "budget_line": fund["Budget line"], "available": available,
           "left_after_order": available - total, "funds_short": total > available, "lines_checked": [], "flags": {}, "lowest": {}}
    if "line_min" in ptype:
        for line in po_lines:
            lt = int(line["Qty"]) * money(line["Unit price"])
            if lt <= ptype["line_min"]:
                continue
            req["lines_checked"].append(line["SKU"])
            options = [r for r in catalog if r["Item"] == line["Item"] and in_spec(line["Item"], r)]
            sups = {r["supplier"] for r in options}
            low = min(options, key=lambda r: money(r["Unit price"]))
            if len(sups) < ptype["min_suppliers"]:
                req["flags"][line["SKU"]] = "SINGLE_SOURCE"
            elif money(line["Unit price"]) > money(low["Unit price"]):
                req["flags"][line["SKU"]] = "LOWEST_NOT_SELECTED"
                reason = "LATE_ITEM" if low["SKU"] in src.get("late", {}) else failed_skus.get(low["SKU"])
                req["lowest"][line["SKU"]] = {"lowest_sku": low["SKU"], "lowest_price": money(low["Unit price"]),
                                              "selected_price": money(line["Unit price"]),
                                              "difference": money(line["Unit price"]) - money(low["Unit price"]), "reason_on_record": reason}
    elif ptype["max_amount"] is None:
        req["flags"]["ORDER"] = "FORMAL_BID_REQUIRED"
    req["lines_checked"].sort()
    req["needs_person"] = sorted(k for k, v in req["flags"].items()
                                 if v in ("SINGLE_SOURCE", "FORMAL_BID_REQUIRED") or not req["lowest"].get(k, {}).get("reason_on_record"))
    req["status"] = "FUNDS_SHORT" if req["funds_short"] else ("NEEDS_JUSTIFICATION" if req["needs_person"] else "READY_TO_CERTIFY")
    req["approvers"] = next(t for t in rules["approval_tiers"] if t["max_amount"] is None or total <= t["max_amount"])["approvers"]
    out["request"] = req

    # close-out
    crs = sorted(glob.glob(p(*PROJ.split("/"), "out", "change-request-*.json")))
    approved_delta, pending = 0, []
    for f in crs:
        md = open(f[:-5] + ".md", encoding="utf-8").read()
        cid = os.path.basename(f)[len("change-request-"):-5]
        if re.search(r"Approved by: _{3,}", md):
            pending.append(cid)
        else:
            approved_delta += json.load(open(f, encoding="utf-8"))["delta"]
    invs = {os.path.basename(f)[:-3]: fields(open(f, encoding="utf-8").read()) for f in sorted(glob.glob(p(*PROJ.split("/"), "invoices", "*.md")))}
    match = (jload(f"{PROJ}/out/match.json") or {}).get("invoices", {})
    invoiced = sum(money(v["Total due"]) for v in invs.values())
    held = sorted(k for k, v in match.items() if v.get("result") == "HOLD")
    received = {r["SKU"]: int(r["Qty received"]) for r in table(read(f"{PROJ}/received/receipt-2026-11-12.md"), "SKU")}
    full = [l["SKU"] for l in po_lines if received.get(l["SKU"], 0) >= int(l["Qty"])]
    open_lines = sorted(l["SKU"] for l in po_lines if l["SKU"] not in full)
    tasks = sorted(r["Task"] for r in table(read(f"{PROJ}/out/tasks.md"), "Task") if re.match(r"T\d+$", r.get("Task", "")))
    co = {"original": total, "approved_changes": approved_delta, "current": total + approved_delta, "invoiced": invoiced,
          "approved_for_payment": sum(money(v["Total due"]) for v in invs.values() if v.get("Payment status", "").startswith("approved")),
          "paid": sum(money(v["Total due"]) for v in invs.values() if v.get("Payment status") == "paid"),
          "held": sum(money(invs[k]["Total due"]) for k in held), "remaining": total + approved_delta - invoiced,
          "lines_received": len(full), "lines_total": len(po_lines), "open_lines": open_lines, "held_invoices": held,
          "pending_changes": pending, "open_tasks": tasks}
    notice = next(iter(sorted(glob.glob(p(*PROJ.split("/"), "closeout", "*.md")))), None)
    if notice:
        sup = fields(open(notice, encoding="utf-8").read())["Supplier"]
        nd = sorted(l["SKU"] for l in po_lines if l["Supplier"] == sup and l["SKU"] not in full)
        co["claim"] = {"supplier": sup, "result": "CLAIM_CONTRADICTED" if nd else "CLAIM_CONFIRMED", "not_delivered": nd}
    co["status"] = "NOT_READY" if (open_lines or held or pending or tasks) else "READY_TO_CLOSE"
    out["closeout"] = co
    return out


def subset_equal(got, want, path=""):
    """Every key in want must equal got's (the key's 'why' lines are notes, skipped). Returns a list of differences."""
    diffs = []
    if isinstance(want, dict):
        if not isinstance(got, dict):
            return [f"{path}: {got!r} is not an object"]
        for k, v in want.items():
            if k in ("why", "_note"):
                continue
            diffs += subset_equal(got.get(k), v, f"{path}.{k}")
    elif got != want:
        diffs.append(f"{path}: got {got!r}, want {want!r}")
    return diffs


# ------------------------------------------------------------- the checks -------------------------------------------------------------
def run_older():
    out = {}
    for tag, f in (("p1", "check_phase1.py"), ("p2", "check_phase2.py"), ("p3a", "check_phase3a.py"), ("p3b", "check_phase3b.py")):
        if not os.path.exists(p("tests", f)):
            out[tag] = (None, None, 99)
            continue
        cmd = [sys.executable, "-I", "-X", "utf8", p("tests", f)] + (["--root", ROOT] if f in ("check_phase3a.py", "check_phase3b.py") else []) \
            + (["--copy"] if COPY else [])
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT, timeout=900)
        m = re.findall(r"^RESULT: (\d+) of (\d+) checks PASS", r.stdout, re.M)
        out[tag] = (int(m[-1][0]), int(m[-1][1]), r.returncode) if m else (None, None, r.returncode)
    return out


def main():
    key = jload("tests/answer-key-3c.json") or {}
    lock = read("tests/LOCK.txt")
    locked = dict((ln.split()[1], ln.split()[0]) for ln in lock.splitlines() if len(ln.split()) > 1)
    frozen = [(ln.split()[0], ln.split()[1]) for ln in read("tests/frozen-3c.txt").splitlines() if ln and not ln.startswith("#")]
    older_ok = locked.get("answer-key.json") == sha("tests/answer-key.json") and locked.get("answer-key-3a.json") == sha("tests/answer-key-3a.json")
    rec(locked.get("answer-key-3c.json") == sha("tests/answer-key-3c.json") and locked.get("tests/frozen-3c.txt") == sha("tests/frozen-3c.txt")
        and older_ok and len(frozen) >= 80,
        "R0 answer key and frozen-record list unchanged since locked",
        f"key {sha('tests/answer-key-3c.json')[:12]} vs lock {locked.get('answer-key-3c.json', 'missing')[:12]}; frozen list "
        f"{sha('tests/frozen-3c.txt')[:12]} vs lock {locked.get('tests/frozen-3c.txt', 'missing')[:12]} ({len(frozen)} records); "
        f"older keys still match their locks: {older_ok}")
    try:
        mine = recount()
        # "certified" and "certificate_signed" describe what the helper writes (blank signature lines), not the inputs;
        # R2 and R3 check them on the output files. Fixed 11/6 after the first run, before the helper existed.
        inputs_only = json.loads(json.dumps(key))
        for sec, k in (("request", "certified"), ("closeout", "certificate_signed")):
            inputs_only.get(sec, {}).pop(k, None)
        diffs = subset_equal(mine, inputs_only)
    except Exception as e:
        mine, diffs = None, [f"recount crashed: {e!r}"]
    rec(not diffs and mine is not None, "R0b the check's own recount from the raw inputs equals the hand-written key",
        f"{len(diffs)} differences {diffs[:4]}")

    # R1 screen
    probs = []
    for s, want in key.get("screen", {}).get("vendors", {}).items():
        got = jload(f"vendors/{s}/screen.json")
        if got is None:
            probs.append(f"{s}: no screen.json")
            continue
        probs += subset_equal(got, want, s)
    sup = jload("controls/supplier-screen.json") or {}
    probs += subset_equal(sup.get("suppliers"), key.get("screen", {}).get("suppliers", {}), "suppliers")
    changed = [f for h, f in frozen if sha(f) != h]
    frozen_set = {f for _, f in frozen}
    added = sorted(os.path.relpath(x, ROOT).replace("\\", "/") for x in glob.glob(p(*PROJ.split("/"), "out", "**", "*"), recursive=True)
                   if os.path.isfile(x) and os.path.relpath(x, ROOT).replace("\\", "/") not in frozen_set)
    changed += [f"added {a}" for a in added]
    rec(not probs and not changed and frozen, "R1 /screen: 8 vendors + 3 suppliers = key; 0 Phase 1-3a records changed",
        f"{len(key.get('screen', {}).get('vendors', {}))} vendors + {len(key.get('screen', {}).get('suppliers', {}))} suppliers compared, "
        f"problems {probs[:4]}; frozen records {len(frozen)}, changed {len(changed)} {changed[:4]}")

    # R2 request
    got = jload(f"{PROJ}/controls/approval-request.json")
    md = read(f"{PROJ}/controls/approval-request.md")
    probs = subset_equal(got, key.get("request", {}), "request") if got is not None else ["no approval-request.json"]
    for need in [key.get("request", {}).get("budget_line", "?"), "Purpose", "Certification"] + list(key.get("request", {}).get("flags", {}).values()):
        if need not in md:
            probs.append(f"md missing '{need}'")
    if not re.search(r"Approved by: _{3,}", md):
        probs.append("certification not left blank")
    rec(got is not None and not probs, "R2 /request = key: type, funding, per-line competition, justifications, blank certification",
        f"{len((got or {}).get('flags', {}))} lines flagged; problems {probs[:4]}")

    # R3 close-out
    got = jload(f"{PROJ}/controls/contract-summary.json")
    cert = read(f"{PROJ}/controls/completion-certificate.md")
    replies = sorted(glob.glob(p(*PROJ.split("/"), "controls", "drafts", "reply-*.md")))
    probs = subset_equal(got, key.get("closeout", {}), "closeout") if got is not None else ["no contract-summary.json"]
    if len(re.findall(r"Signature: _{3,}", cert)) != 2 or "NOT READY" not in cert:
        probs.append("certificate: want 2 blank signatures and NOT READY")
    rt = open(replies[0], encoding="utf-8").read() if replies else ""
    nd = key.get("closeout", {}).get("claim", {}).get("not_delivered", [])
    if not rt or "not sent" not in rt.splitlines()[0].lower() or any(x not in rt for x in nd):
        probs.append("draft reply to the supplier missing, sendable, or missing an item")
    rec(got is not None and not probs, "R3 /closeout = key: running totals, open items, the false claim refused, certificate unsigned",
        f"{len((got or {}).get('open_lines', []))} open lines; {len(replies)} draft replies; problems {probs[:4]}")

    # R4 controls log
    raw = read(LOG)
    lines = raw.rstrip("\n").split("\n") if raw else []
    probs = [] if lines and lines[0] == HEADER else ["header missing or wrong"]
    links = read(CHAIN).split()
    h, good = hashlib.sha256(HEADER.encode()).hexdigest(), 0
    for i, line in enumerate(lines[1:]):
        h = hashlib.sha256((h + "\n" + line).encode("utf-8")).hexdigest()
        good += i < len(links) and links[i] == h
    n = max(len(lines) - 1, 0)
    if not (good == n == len(links)) or n == 0:
        probs.append(f"chain {good} of {n} rows verify, {len(links)} links")
    rows = list(csv.reader(io.StringIO(raw)))[1:] if raw else []
    counts, people = {}, 0
    for r in rows:
        if len(r) != 6 or r[3] not in ACTIONS or r[1] != ACTIONS[r[3]]:
            probs.append(f"bad row {r[:4]}")
            continue
        counts[r[3]] = counts.get(r[3], 0) + 1
        people += bool(re.search(r"(?<!not )\b(?:sent|signed|approved|paid|ordered)\b", r[5], re.I))
    missing = [a for a in ("screen", "approval_request", "closeout") if counts.get(a, 0) != 1]
    rec(not probs and not missing and people == 0, "R4 controls log: 1 row per action, right actors, chain verifies, 0 people-only actions",
        f"{n} rows; actions {counts}; not exactly once {missing}; people-only results {people}; problems {probs[:4]}")

    # R5 skills + rules text
    probs = []
    for s in SKILLS:
        t = read(f".claude/skills/{s}/SKILL.md")
        fm = t.split("---")[1] if t.startswith("---") else ""
        meta = dict(re.findall(r"^(\w[\w-]*):\s*(.*)$", fm, re.M))
        if meta.get("name") != s or not meta.get("description"):
            probs.append(f"{s}: front matter")
    rules = json.loads(read("company/rules.json")).get("controls", {})
    cm = read("CLAUDE.md")
    sec = cm.split("## 11.", 1)[1] if "## 11." in cm else ""
    pt = rules.get("procurement_types", [{}, {}])
    need = sorted(rules.get("issue_codes", {})) + rules.get("approval_order", []) + rules.get("screen_results", []) + [
        f"**${pt[0].get('max_amount', 0):,}**", f"**${pt[1].get('max_amount', 0):,}**", f"**${pt[1].get('line_min', 0):,}**",
        f"**{pt[1].get('min_suppliers')}**", "controls-log.csv", rules.get("disclosure_file", "?"), "exclusion-list.md"]
    absent = [x for x in need if x not in sec]
    rec(not probs and not absent and sec, "R5 3 skills with front matter; CLAUDE.md section 11 states every Phase 3c rule",
        f"{len(SKILLS) - len(probs)} of {len(SKILLS)} skills ok {probs}; {len(need) - len(absent)} of {len(need)} rules found; missing {absent}")

    # R6 older phases
    if NO_OLD:
        rec(True, "R6 Phases 1, 2, 3a, 3b still pass (skipped by --skip-old-phases in self-test copies)", "skipped")
    else:
        runs = run_older()
        want = {"p1": 8, "p2": 8, "p3a": 14, "p3b": 9}
        rec(all(runs[k][0] == runs[k][1] == want[k] and runs[k][2] == 0 for k in want),
            "R6 Phases 1, 2, 3a, 3b still pass (their scans read the new files)",
            "; ".join(f"{k}: {runs[k][0]} of {runs[k][1]} (want {want[k]}), exit {runs[k][2]}" for k in want))

    # R7 blind review
    revs = sorted(glob.glob(p("reviews", "controls", "*.md")))
    probs = [] if revs else ["no review saved"]
    if revs:
        t = open(revs[-1], encoding="utf-8").read()
        if not re.search(r"^Overall: PASS\b", t, re.M):
            probs.append("latest review is not 'Overall: PASS'")
        if not re.search(r"^Planted error caught: yes\b", t, re.M | re.I):
            probs.append("planted error not recorded as caught")
        man = dict(re.findall(r"^\|\s*`([^`]+)`\s*\|\s*([0-9a-f]{64})\s*\|", t, re.M))
        for f in (f"{PROJ}/controls/approval-request.json", f"{PROJ}/controls/contract-summary.json", "vendors/kestrelbay-air-heat/screen.json",
                  "vendors/gulfpine-pest/screen.json"):
            if man.get(f) != sha(f):
                probs.append(f"{f} not in the manifest or changed since")
    rec(not probs, "R7 blind review: planted error caught, real outputs PASS, nothing changed since",
        f"{len(revs)} reviews; latest {os.path.basename(revs[-1]) if revs else 'none'}; problems {probs}")

    # R8 README
    t = read("README.md")
    row = next((l for l in t.splitlines() if re.match(r"^\|\s*3c\s*\|", l)), "")
    pieces = ["`tools/controls.py`", "`tools/make_controls.py`", "`tests/check_phase3c.py`", "`audit/controls-log.csv`",
              "`company/exclusion-list.md`"] + [f"`/{s}` skill" for s in SKILLS]
    mapped = [x for x in pieces if any(l.startswith("| " + x) and l.rstrip().rstrip("|").split("|")[-1].strip().startswith("Designed and directed")
                                       for l in t.splitlines())]
    rec("Built" in row and len(mapped) == len(pieces), "R8 README: 3c built, every new piece mapped with a 'Designed and directed' line",
        f"3c row: '{row[:70]}'; {len(mapped)} of {len(pieces)} pieces mapped; missing {[x for x in pieces if x not in mapped]}")

    # R9 every new input is visibly fake
    files = NEW_INPUTS + sorted(os.path.relpath(f, ROOT).replace("\\", "/") for f in glob.glob(p("vendors", "*", "disclosures", "*.md")))
    # stricter after the first self-test (11/6): the standard line itself, not any "(fictional)" elsewhere in the file
    unmarked = [f for f in files if "Fake document made for a demo" not in read(f)]
    rec(len(files) >= 11 and not unmarked, "R9 every new input file is marked fake", f"{len(files)} files; unmarked {unmarked}")
    n = sum(ok for ok, _ in results)
    print(f"\nRESULT: {n} of {len(results)} checks PASS")
    return 0 if n == len(results) == 11 else 1


def _drop_flag(cp):
    fp = os.path.join(cp, *PROJ.split("/"), "controls", "approval-request.json")
    j = json.load(open(fp, encoding="utf-8"))
    if "GW-BED-Q" not in j.get("flags", {}):
        raise SystemExit("setup: GW-BED-Q flag not found")
    j["flags"].pop("GW-BED-Q")
    json.dump(j, open(fp, "w", encoding="utf-8"), indent=2)


def selftest():
    def sub(rel, old, new):
        def f(cp):
            fp = os.path.join(cp, *rel.split("/"))
            t = open(fp, encoding="utf-8").read()
            if old not in t:
                raise SystemExit(f"setup: '{old[:40]}' not in {rel}")
            open(fp, "w", encoding="utf-8").write(t.replace(old, new, 1))
        return f
    banned = "".join(["Cam", "eron"])
    breaks = [
        ("R0", "the answer key edited after locking", sub("tests/answer-key-3c.json", '"lowest_price": 1450', '"lowest_price": 1405')),
        ("R0b", "a catalog price changed under the key", sub(f"{PROJ}/catalogs/MH.md", "| MH-DR-60 | Dresser |", "| MH-DR-60 | Bureau |")),
        ("R1", "Kestrelbay's screen marked CLEAR", sub("vendors/kestrelbay-air-heat/screen.json", '"result": "REVIEW"', '"result": "CLEAR"')),
        ("R2", "a single-source line dropped from the request", _drop_flag),
        ("R3", "the remaining amount off by $100", sub(f"{PROJ}/controls/contract-summary.json", '"remaining": 3491', '"remaining": 3391')),
        ("R4", "a past controls-log row edited", sub(LOG, "onboarding-assistant", "onboarding-assistant ")),
        ("R5", "a skill's front matter broken", sub(".claude/skills/closeout/SKILL.md", "name: closeout", "name: close")),
        ("R6", "a personal name in a new file", sub(f"{PROJ}/funding.md", "# Funding record", f"# {banned} funding record")),
        ("R7", "the review's verdict changed", sub(None, None, None)),
        ("R8", "README's 3c row set back to Next", None),
        ("R9", "the fake label removed from the funding record", sub(f"{PROJ}/funding.md", "Fake document made for a demo", "Document")),
    ]
    caught = 0
    for target, what, plant in breaks:
        with tempfile.TemporaryDirectory() as tmp:
            cp = os.path.join(tmp, "Onboarding-Demo")
            shutil.copytree(ROOT, cp, ignore=shutil.ignore_patterns("__pycache__"))
            try:
                if target == "R7":
                    revs = sorted(glob.glob(os.path.join(cp, "reviews", "controls", "*.md")))
                    if not revs:
                        raise SystemExit("setup: no review to break")
                    t = open(revs[-1], encoding="utf-8").read()
                    open(revs[-1], "w", encoding="utf-8").write(t.replace("Overall: PASS", "Overall: FAIL"))
                elif target == "R8":
                    fp = os.path.join(cp, "README.md")
                    t = open(fp, encoding="utf-8").read()
                    t2 = re.sub(r"^(\|\s*3c\s*\|[^|]*\|)\s*Built[^|]*\|", r"\1 Next |", t, count=1, flags=re.M)
                    if t2 == t:
                        raise SystemExit("setup: 3c row not found")
                    open(fp, "w", encoding="utf-8").write(t2)
                else:
                    plant(cp)
            except SystemExit as e:
                print(f"SETUP FAIL - {target}: {e}")
                continue
            args = [sys.executable, "-I", "-X", "utf8", os.path.join(cp, "tests", "check_phase3c.py"), "--root", cp, "--copy"]
            if target != "R6":
                args.append("--skip-old-phases")
            r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1200)
            hit = any(l.startswith(f"FAIL - {target} ") for l in r.stdout.splitlines())
            caught += hit
            print(f"{'CAUGHT' if hit else 'MISSED'} - {target}: {what} (exit {r.returncode})")
    print(f"\nSELF-TEST: {caught} of {len(breaks)} planted breaks caught by the check they target")
    return 0 if caught == len(breaks) else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
