"""Phase 3d acceptance check: two real-world exceptions (fictional company, sample records).
  - a signer asks for a change after others signed, so the packet restarts from the first approver (/revise);
  - an item runs a week or more past its promised date, so a shipping-credit request is drafted for a person (/credit).

Written 11/8/2026 before tools/exceptions.py or the /revise and /credit skills existed. It never imports the helper:
it recounts every result from the raw records its own way. Prints what it counted; exit 1 on any FAIL.

    python -I -X utf8 tests/check_phase3d.py               D0-D10
    python -I -X utf8 tests/check_phase3d.py --selftest    plant one break per check in a temp copy; each must FAIL its own check

Options: --root DIR (check a copy) · --copy (older checks are told they run on a copy) · --skip-old-phases (D7 skipped; the
dashboard build and the Phase 3b check use it so the checks never call each other in a loop)
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
LOG, CHAIN = "audit/exceptions-log.csv", "audit/exceptions-log.chain.txt"
HEADER = "timestamp,actor,vendor,action,detail,result"
ACTIONS = {"packet_revision": "onboarding-assistant", "freight_credit": "procurement-assistant", "checker_review": "compliance-checker"}
SKILLS = ["revise", "credit"]
EXPECTED_NEW = ["vendors/skyquay-lift-fire/revision.json", "vendors/skyquay-lift-fire/packet-v2.md",
                f"{PROJ}/exceptions/freight-credit.json", f"{PROJ}/exceptions/credit-request-gulfweave-2026-11-12.md", LOG, CHAIN]
WATCHED = ["vendors", "projects", "audit", "company", "controls"]
HARSH = ["owe", "owed", "demand", "legal action", "lawyer", "lawsuit", "breach", "penalty", "failure to", "immediately", "must"]
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


def subset_equal(got, want, path=""):
    diffs = []
    if isinstance(want, dict):
        if not isinstance(got, dict):
            return [f"{path}: {got!r} is not an object"]
        for k, v in want.items():
            if k.startswith("_"):
                continue
            diffs += subset_equal(got.get(k), v, f"{path}.{k}")
    elif got != want:
        diffs.append(f"{path}: got {got!r}, want {want!r}")
    return diffs


# ------------------------------------------------------------- the check's own recount -------------------------------------------------------------
def recount():
    rules = json.loads(read("company/rules.json"))
    ex = rules["exceptions"]
    out = {}
    # /revise: the e-signature export(s)
    exports = sorted(glob.glob(p("vendors", "*", "esign-status-*.md")))
    if len(exports) != 1:
        raise ValueError(f"want 1 e-signature export, found {len(exports)}")
    f = exports[0]
    slug = os.path.basename(os.path.dirname(f))
    t = open(f, encoding="utf-8").read()
    fl = fields(t)
    rows = table(t, "#")
    ask = next(r for r in rows if r["Status"] == "change requested")
    signed = [r["Role"] for r in rows if r["Status"] == "signed" and int(r["#"]) < int(ask["#"])]
    ctype = fl["Change type"]
    material = ctype in ex["revision"]["material_changes"]
    amount = money(fields(read(f"vendors/{slug}/documents/request.md"))["Contract amount"])
    route = next(tt for tt in rules["approval_tiers"] if tt["max_amount"] is None or amount <= tt["max_amount"])["approvers"]
    out["revise"] = {"vendor": slug, "from_version": int(fl["Version"]), "to_version": int(fl["Version"]) + 1, "change_type": ctype,
                     "change": ask["Note"], "requested_by": ask["Role"], "requested_on": ask["Date"], "material": material,
                     "status": ex["revision"]["status"] if material else "CONTINUE", "signed_before": signed, "route": route,
                     "next": route[0] if material else route[int(ask["#"]) - 1], "sender": ex["revision"]["sender"],
                     "blank_signoffs": len(route) if material else len(route) - len(signed)}
    # /credit: the approved order vs. the latest tracking
    po = read(f"{PROJ}/approved/po-PQ-1042.md")
    lines = {r["SKU"]: r for r in table(po, "SKU")}
    freight = {m.group(1): money(m.group(2)) for m in re.finditer(r"^Freight ([^:]+): (\$[\d,]+)", po, re.M)}
    trk = sorted(glob.glob(p(*PROJ.split("/"), "deliveries", "tracking-*.md")))[-1]
    tt = open(trk, encoding="utf-8").read()
    hold = rules["projects"]["on_hold_status"]
    fc = ex["freight_credit"]
    items = {}
    for r in table(tt, "SKU"):
        if not r.get("ETA") or r["SKU"] not in lines or r["Status"] == hold:
            continue
        late = (day(r["ETA"]) - day(lines[r["SKU"]]["Promised delivery"])).days
        if late >= fc["days_past_promised"]:
            items[r["SKU"]] = {"supplier": r["Supplier"], "promised": lines[r["SKU"]]["Promised delivery"], "eta": r["ETA"], "days_past": late}
    sups = {}
    for sku, it in items.items():
        s = sups.setdefault(it["supplier"], {"freight": freight[it["supplier"]], "skus": []})
        s["skus"].append(sku)
        s["credit_cents"] = freight[it["supplier"]] * 100 * fc["share_of_freight_percent"] // 100
    out["credit"] = {"project": PROJ.split("/")[1], "as_of": fields(tt)["As of"], "items": items, "suppliers": sups,
                     "reviewer_and_sender": fc["reviewer_and_sender"], "status": fc["status"]}
    return out


def cents(c):
    return f"${c // 100:,}.{c % 100:02d}"


def run_older():
    out = {}
    for tag, f in (("p1", "check_phase1.py"), ("p2", "check_phase2.py"), ("p3a", "check_phase3a.py"), ("p3b", "check_phase3b.py"),
                   ("p3c", "check_phase3c.py"), ("org", "check_orgchart.py")):
        if not os.path.exists(p("tests", f)):
            out[tag] = (None, None, 99)
            continue
        cmd = [sys.executable, "-I", "-X", "utf8", p("tests", f)] + (["--root", ROOT] if f in ("check_phase3a.py", "check_phase3b.py", "check_phase3c.py") else []) \
            + (["--copy"] if COPY and f != "check_orgchart.py" else []) + (["--skip-old-phases"] if f == "check_phase3c.py" else [])
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT, timeout=1800)
        m = re.findall(r"^RESULT: (\d+) of (\d+) checks PASS", r.stdout, re.M)
        out[tag] = (int(m[-1][0]), int(m[-1][1]), r.returncode) if m else (None, None, r.returncode)
    return out


# ------------------------------------------------------------- the checks -------------------------------------------------------------
def main():
    key = jload("tests/answer-key-3d.json") or {}
    lock = read("tests/LOCK.txt")
    locked = dict((ln.split()[1], ln.split()[0]) for ln in lock.splitlines() if len(ln.split()) > 1)
    frozen = [(ln.split()[0], ln.split()[1]) for ln in read("tests/frozen-3d.txt").splitlines() if ln and not ln.startswith("#")]
    older = all(locked.get(k) == sha(f"tests/{k}") for k in ("answer-key.json", "answer-key-3a.json", "answer-key-3c.json"))
    rec(locked.get("answer-key-3d.json") == sha("tests/answer-key-3d.json") and locked.get("tests/frozen-3d.txt") == sha("tests/frozen-3d.txt")
        and older and len(frozen) >= 150,
        "D0 answer key and frozen-record list unchanged since locked",
        f"key {sha('tests/answer-key-3d.json')[:12]} vs lock {locked.get('answer-key-3d.json', 'missing')[:12]}; frozen list "
        f"{sha('tests/frozen-3d.txt')[:12]} vs lock {locked.get('tests/frozen-3d.txt', 'missing')[:12]} ({len(frozen)} records); older keys match: {older}")
    try:
        mine = recount()
        diffs = subset_equal(mine, key)
    except Exception as e:
        mine, diffs = None, [f"recount crashed: {e!r}"]
    rec(mine is not None and not diffs, "D0b the check's own recount from the raw records equals the hand-written key",
        f"{len(diffs)} differences {diffs[:4]}")
    rk, ck = key.get("revise", {}), key.get("credit", {})
    people = {re.sub(r"\s*\(.*?\)", "", r["Role"]).strip(): r["Name"] for r in table(read("company/people.md"), "Role")}

    # D1 /revise
    slug = rk.get("vendor", "?")
    got = jload(f"vendors/{slug}/revision.json")
    probs = subset_equal(got, rk) if got is not None else ["no revision.json"]
    v2 = read(f"vendors/{slug}/packet-v2.md")
    ex_files = sorted(glob.glob(p("vendors", slug, "esign-status-*.md")))
    export = open(ex_files[0], encoding="utf-8").read() if ex_files else ""
    export_rows = {r["Role"]: r for r in table(export, "#")}
    if not v2:
        probs.append("no packet-v2.md")
    else:
        for need in ["Version 2", "replaces version 1", rk.get("change", "?"), "Sample data for a demo", "void"]:
            if need.lower() not in v2.lower():
                probs.append(f"v2 missing '{need[:40]}'")
        for role in rk.get("signed_before", []):
            line = next((l for l in v2.splitlines() if people.get(role, "?") in l and export_rows.get(role, {}).get("Date", "?") in l), "")
            if "sign again" not in line.lower():
                probs.append(f"v2 doesn't say {role} ({people.get(role)}, signed {export_rows.get(role, {}).get('Date')}) must sign again")
        so = v2.split("## Sign-offs", 1)[1] if "## Sign-offs" in v2 else ""
        signoffs = [c for c in ([x.strip() for x in l.strip().strip("|").split("|")] for l in so.splitlines()) if len(c) == 7 and c[0].isdigit()]
        if [c[1] for c in signoffs] != rk.get("route"):
            probs.append(f"sign-off order {[c[1] for c in signoffs]}")
        if any(c[4] or c[5] or c[6] for c in signoffs):
            probs.append("a v2 sign-off is filled in")
    rec(got is not None and not probs, "D1 /revise = key: version 2 with the change word for word, earlier signers sign again, route restarts, sign-offs blank",
        f"{len(subset_equal(got, rk)) if got is not None else 'no'} key differences; problems {probs[:4]}")

    # D2 /credit
    got = jload(f"{PROJ}/exceptions/freight-credit.json")
    probs = subset_equal(got, ck) if got is not None else ["no freight-credit.json"]
    sup_mail = {r["Supplier"]: r["Orders email"] for r in table(read("company/approved-suppliers.md"), "Supplier")}
    drafts = sorted(glob.glob(p(*PROJ.split("/"), "exceptions", "credit-request-*.md")))
    if len(drafts) != len(ck.get("suppliers", {})):
        probs.append(f"{len(drafts)} drafts for {len(ck.get('suppliers', {}))} suppliers")
    harsh = []
    for name, s in ck.get("suppliers", {}).items():
        d = read(f"{PROJ}/exceptions/credit-request-{name.split()[0].lower()}-{ck.get('as_of')}.md")
        if not d:
            probs.append(f"no draft for {name}")
            continue
        if "not sent" not in d.splitlines()[0]:
            probs.append(f"{name}: first line doesn't say not sent")
        need = [sup_mail.get(name, "?"), "PQ-1042", f"${s['freight']:,}", cents(s["credit_cents"]),
                f"{json.loads(read('company/rules.json'))['exceptions']['freight_credit']['share_of_freight_percent']}%",
                people.get(ck.get("reviewer_and_sender"), "?")]
        for sku in s["skus"]:
            it = ck["items"][sku]
            need += [sku, it["promised"], it["eta"], str(it["days_past"])]
        probs += [f"{name}: missing '{x}'" for x in need if x not in d]
        body = d.lower()
        harsh += [w for w in HARSH if re.search(r"\b" + re.escape(w) + r"\b", body)]
    rec(got is not None and not probs and not harsh and drafts, "D2 /credit = key: one polite draft per supplier with the order, item, dates, freight, and ask; not sent",
        f"{len(drafts)} drafts; problems {probs[:4]}; harsh words {harsh}")

    # D3 exceptions log
    raw = read(LOG).replace("\r", "")
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
    counts, people_only = {}, 0
    outs = {"packet_revision": f"vendors/{slug}/revision.json", "freight_credit": f"{PROJ}/exceptions/freight-credit.json"}
    for r in rows:
        if len(r) != 6 or r[3] not in ACTIONS or r[1] != ACTIONS[r[3]]:
            probs.append(f"bad row {r[:4]}")
            continue
        counts[r[3]] = counts.get(r[3], 0) + 1
        if r[3] in outs and outs[r[3]] not in r[4]:
            probs.append(f"{r[3]} row doesn't name {outs[r[3]]}")
        people_only += bool(re.search(r"(?<!not )\b(?:sent|signed|approved|paid|ordered|voided)\b", r[5], re.I))
    missing = [a for a in outs if counts.get(a, 0) != 1]
    rec(not probs and not missing and people_only == 0, "D3 exceptions log: 1 row per action, right actors, chain verifies, 0 people-only results",
        f"{n} rows; actions {counts}; not exactly once {missing}; people-only results {people_only}; problems {probs[:4]}")

    # D4 only additions: every frozen record unchanged; the only new files in the record folders are the expected outputs
    changed = [f for hh, f in frozen if sha(f) != hh]
    frozen_set = {f for _, f in frozen}
    now = []
    for base in WATCHED:
        for dp, dns, fs in os.walk(p(base)):
            dns[:] = [d for d in dns if d != "__pycache__"]
            now += [os.path.relpath(os.path.join(dp, x), ROOT).replace("\\", "/") for x in fs]
    added = sorted(set(now) - frozen_set)
    extra = [a for a in added if a not in EXPECTED_NEW]
    absent = [e for e in EXPECTED_NEW if e not in added]
    rec(frozen and not changed and not extra and not absent, "D4 0 earlier records changed; the only new record files are the expected outputs",
        f"{len(frozen)} frozen, changed {len(changed)} {changed[:3]}; new {len(added)}, unexpected {extra[:3]}, expected but missing {absent[:3]}")

    # D5 skills + rules text
    probs = []
    for s in SKILLS:
        t = read(f".claude/skills/{s}/SKILL.md")
        fm = t.split("---")[1] if t.startswith("---") else ""
        meta = dict(re.findall(r"^(\w[\w-]*):\s*(.*)$", fm, re.M))
        if meta.get("name") != s or not meta.get("description"):
            probs.append(f"{s}: front matter")
    ex = json.loads(read("company/rules.json")).get("exceptions", {})
    cm = read("CLAUDE.md")
    sec = cm.split("## 12.", 1)[1] if "## 12." in cm else ""
    need = list(ex.get("revision", {}).get("material_changes", [])) + [
        f"**{ex.get('freight_credit', {}).get('days_past_promised')} days**", f"**{ex.get('freight_credit', {}).get('share_of_freight_percent')}%**",
        ex.get("revision", {}).get("status", "?"), ex.get("freight_credit", {}).get("status", "?"), ex.get("revision", {}).get("sender", "?"),
        "exceptions-log.csv", "/revise", "/credit"]
    absent = [x for x in need if x not in sec]
    rec(not probs and not absent and sec, "D5 2 skills with front matter; CLAUDE.md section 12 states every Phase 3d rule",
        f"{len(SKILLS) - len(probs)} of {len(SKILLS)} skills ok {probs}; {len(need) - len(absent)} of {len(need)} rules found; missing {absent}")

    # D6 the dashboard shows both
    page = read("dashboard/index.html")
    probs = []
    w = dict(re.findall(r'data-w="([^"]+)" data-owner="([^"]*)"', page))
    for name in ck.get("suppliers", {}):
        k_ = f"send_credit:credit-request-{name.split()[0].lower()}-{ck.get('as_of')}"
        if w.get(k_) != ck.get("reviewer_and_sender"):
            probs.append(f"no waiting row {k_} for {ck.get('reviewer_and_sender')}")
    srow = re.search(r'<tr data-w="sign_packet:' + re.escape(slug) + r'".*?</tr>', page, re.S)
    if not srow or "version 2" not in srow.group(0).lower():
        probs.append("Skyquay's waiting row doesn't ask about version 2")
    for f in (f"vendors/{slug}/packet-v2.md", f"{PROJ}/exceptions/credit-request-gulfweave-2026-11-12.md"):
        if f'data-src="{f}"' not in page:
            probs.append(f"no quote from {f}")
    ev = re.search(r'<script id="replay-data" type="application/json">(.*?)</script>', page, re.S)
    acts = re.search(r'<script id="replay-acts" type="application/json">(.*?)</script>', page, re.S)
    ev = json.loads(ev.group(1).replace("<\\/", "</")) if ev else []
    acts = [a["action"] for a in json.loads(acts.group(1).replace("<\\/", "</"))] if acts else []
    exc_ev = [e for e in ev if e.get("log") == "exc"]
    if len(exc_ev) != len(rows):
        probs.append(f"replay has {len(exc_ev)} exceptions events for {len(rows)} log rows")
    for a in ("packet_revision", "freight_credit"):
        if a not in acts:
            probs.append(f"replay board has no {a}")
    rec(page and not probs, "D6 the dashboard shows both: waiting rows, quotes from the new records, the replay",
        f"{len(w)} waiting rows; {len(exc_ev)} exceptions events in the replay; problems {probs[:4]}")

    # D7 older phases
    if NO_OLD:
        rec(True, "D7 Phases 1, 2, 3a, 3b, 3c and the org-chart check still pass (skipped by --skip-old-phases)", "skipped")
    else:
        runs = run_older()
        want = {"p1": 8, "p2": 8, "p3a": 14, "p3b": 9, "p3c": 11, "org": 8}
        rec(all(runs[k][0] == runs[k][1] == want[k] and runs[k][2] == 0 for k in want),
            "D7 Phases 1, 2, 3a, 3b, 3c and the org-chart check still pass (their scans read the new files)",
            "; ".join(f"{k}: {runs[k][0]} of {runs[k][1]} (want {want[k]}), exit {runs[k][2]}" for k in want))

    # D8 blind review
    revs = sorted(glob.glob(p("reviews", "exceptions", "*.md")))
    probs = [] if revs else ["no review saved"]
    if revs:
        t = open(revs[-1], encoding="utf-8").read()
        if not re.search(r"^Overall: PASS\b", t, re.M):
            probs.append("latest review is not 'Overall: PASS'")
        if not re.search(r"^Planted error caught: yes\b", t, re.M | re.I):
            probs.append("planted error not recorded as caught")
        man = dict(re.findall(r"^\|\s*`([^`]+)`\s*\|\s*([0-9a-f]{64})\s*\|", t, re.M))
        for f in EXPECTED_NEW[:4]:
            if man.get(f) != sha(f):
                probs.append(f"{f} not in the manifest or changed since")
    rec(not probs, "D8 blind review: planted error caught, real outputs PASS, nothing changed since",
        f"{len(revs)} reviews; latest {os.path.basename(revs[-1]) if revs else 'none'}; problems {probs}")

    # D9 README
    t = read("README.md")
    row = next((l for l in t.splitlines() if re.match(r"^\|\s*3d\s*\|", l)), "")
    pieces = ["`tools/exceptions.py`", "`tests/check_phase3d.py`", "`audit/exceptions-log.csv`"] + [f"`/{s}` skill" for s in SKILLS]
    mapped = [x for x in pieces if any(l.startswith("| " + x) and l.rstrip().rstrip("|").split("|")[-1].strip().startswith("Designed and directed")
                                       for l in t.splitlines())]
    rec("Built" in row and len(mapped) == len(pieces), "D9 README: 3d built, every new piece mapped with a 'Designed and directed' line",
        f"3d row: '{row[:70]}'; {len(mapped)} of {len(pieces)} pieces mapped; missing {[x for x in pieces if x not in mapped]}")

    # D10 every new input is visibly a sample
    files = sorted(os.path.relpath(f, ROOT).replace("\\", "/") for f in glob.glob(p("vendors", "*", "esign-status-*.md")))
    unmarked = [f for f in files if "Fake document made for a demo" not in read(f)]
    rec(files and not unmarked, "D10 every new input file is marked as a made-up sample", f"{len(files)} files; unmarked {unmarked}")

    n = sum(ok for ok, _ in results)
    print(f"\nRESULT: {n} of {len(results)} checks PASS")
    return 0 if n == len(results) == 12 else 1


# ------------------------------------------------------------- self-test -------------------------------------------------------------
def selftest():
    def sub(rel, old, new):
        def f(cp):
            fp = os.path.join(cp, *rel.split("/"))
            t = open(fp, encoding="utf-8").read()
            if old not in t:
                raise SystemExit(f"setup: '{old[:40]}' not in {rel}")
            open(fp, "w", encoding="utf-8", newline="").write(t.replace(old, new, 1))
        return f

    def suball(rel, old, new):
        def f(cp):
            fp = os.path.join(cp, *rel.split("/"))
            t_ = open(fp, encoding="utf-8").read()
            if old not in t_:
                raise SystemExit(f"setup: '{old[:40]}' not in {rel}")
            open(fp, "w", encoding="utf-8", newline="").write(t_.replace(old, new))
        return f

    def add(rel):
        def f(cp):
            open(os.path.join(cp, *rel.split("/")), "w", encoding="utf-8").write("stray\n")
        return f

    banned = "".join(["Cam", "eron"])
    draft = f"{PROJ}/exceptions/credit-request-gulfweave-2026-11-12.md"
    breaks = [
        ("D0", "the answer key edited after locking", sub("tests/answer-key-3d.json", '"credit_cents": 9250', '"credit_cents": 9200')),
        ("D0b", "the change type in the export changed under the key", sub("vendors/skyquay-lift-fire/esign-status-2026-11-10.md", "Change type: contract terms", "Change type: typo")),
        ("D1", "version 2 routed to Legal first", sub("vendors/skyquay-lift-fire/revision.json", '"next": "Facilities Manager"', '"next": "Legal"')),
        ("D2", "the credit asked for changed to $95.00 everywhere in the draft", suball(draft, "$92.50", "$95.00")),
        ("D3", "a past exceptions-log row edited", sub(LOG, "procurement-assistant", "procurement-assistant ")),
        ("D4", "a stray file added next to the outputs", add(f"{PROJ}/exceptions/notes.md")),
        ("D5", "a skill's front matter broken", sub(".claude/skills/credit/SKILL.md", "name: credit", "name: credits")),
        ("D6", "the shipping-credit row dropped from the dashboard", sub("dashboard/index.html", 'data-w="send_credit:', 'data-w="x_send_credit:')),
        ("D7", "a personal name in a new file", sub("vendors/skyquay-lift-fire/packet-v2.md", "# Approval packet", f"# {banned} approval packet")),
        ("D8", "the review's verdict changed", None),
        ("D9", "README's 3d row set back to Next", None),
        ("D10", "the sample label removed from the e-signature export", sub("vendors/skyquay-lift-fire/esign-status-2026-11-10.md", "Fake document made for a demo", "Document")),
    ]
    caught = 0
    for target, what, plant in breaks:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            cp = os.path.join(tmp, "Onboarding-Demo")
            shutil.copytree(ROOT, cp, ignore=shutil.ignore_patterns("__pycache__", ".git"))
            try:
                if target == "D8":
                    revs = sorted(glob.glob(os.path.join(cp, "reviews", "exceptions", "*.md")))
                    if not revs:
                        raise SystemExit("setup: no review to break")
                    t = open(revs[-1], encoding="utf-8").read()
                    open(revs[-1], "w", encoding="utf-8").write(t.replace("Overall: PASS", "Overall: FAIL"))
                elif target == "D9":
                    fp = os.path.join(cp, "README.md")
                    t = open(fp, encoding="utf-8").read()
                    t2 = re.sub(r"^(\|\s*3d\s*\|[^|]*\|)\s*Built[^|]*\|", r"\1 Next |", t, count=1, flags=re.M)
                    if t2 == t:
                        raise SystemExit("setup: 3d row not found")
                    open(fp, "w", encoding="utf-8").write(t2)
                else:
                    plant(cp)
            except SystemExit as e:
                print(f"SETUP FAIL - {target}: {e}")
                continue
            args = [sys.executable, "-I", "-X", "utf8", os.path.join(cp, "tests", "check_phase3d.py"), "--root", cp, "--copy"]
            if target != "D7":
                args.append("--skip-old-phases")
            r = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=3600)
            hit = any(l.startswith(f"FAIL - {target} ") for l in r.stdout.splitlines())
            caught += hit
            print(f"{'CAUGHT' if hit else 'MISSED'} - {target}: {what} (exit {r.returncode})")
    print(f"\nSELF-TEST: {caught} of {len(breaks)} planted breaks caught by the check they target")
    return 0 if caught == len(breaks) else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
