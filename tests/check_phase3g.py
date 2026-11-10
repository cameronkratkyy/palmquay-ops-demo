"""Phase 3g check: bringing on a new property owner (fictional company, sample records).
Written 11/10/2026 before tools/owners.py or any owner skill existed; its first run had to fail.
It never imports the helper or the dashboard builder: it reads the owner packets and company/owner-rules.json and applies the
rules its own way, then compares with the locked answer key (tests/answer-key-3g.json) and with what the helper wrote.

    python -I -X utf8 tests/check_phase3g.py              G1-G9, prints what it counted; exit 1 on any FAIL
    python -I -X utf8 tests/check_phase3g.py --selftest   plants 6 breaks in a copy and proves each one is caught
    python -I -X utf8 tests/check_phase3g.py --facts      print the recounted facts for the New owners tab as JSON (Phase 3b B1 adds them)
Options: --root DIR (check a copy) · --copy (accepted for symmetry with the other checks; nothing here needs the author's machine)
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
ROOT = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.dirname(HERE)
HEADER = "timestamp,actor,owner,action,detail,result"
GATES = ["accepted", "money", "leasing"]
BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
SKILLS = ["owner-intake", "takeover", "owner-chase", "owner-setup"]
N_CHECKS = 9


# ------------------------------------------------------------- reading -------------------------------------------------------------
def fields(path):
    out = {}
    if not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", line.rstrip("\r\n"))
        if m and m.group(1) not in ("Field", "---") and m.group(1) not in out:
            out[m.group(1)] = m.group(2)
    return out


def rows_after(path, first):
    t = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    lines = t.splitlines()
    for i, l in enumerate(lines):
        c = [x.strip() for x in l.strip().strip("|").split("|")]
        if l.startswith("|") and c and c[0] == first:
            out = []
            for r in lines[i + 2:]:
                if not r.startswith("|"):
                    break
                out.append(dict(zip(c, [x.strip() for x in r.strip().strip("|").split("|")])))
            return out
    return []


def money(s):
    d = re.sub(r"[^\d]", "", (s or "").split("(")[0])
    return int(d) if d else None


def name_key(s):
    return frozenset(w for w in re.findall(r"[a-z]+", s.lower()) if w != "and")


def names(s):
    return [name_key(x) for x in s.split(";") if x.strip()]


# ------------------------------------------------------------- the check's own recount -------------------------------------------------------------
def evaluate(root):
    """Apply company/owner-rules.json to every owner packet, independently of tools/owners.py."""
    R = json.load(open(os.path.join(root, "company", "owner-rules.json"), encoding="utf-8"))
    codes = R["issue_codes"]
    out = {}
    for d in sorted(glob.glob(os.path.join(root, "owners", "*", ""))):
        slug = os.path.basename(os.path.dirname(d))
        f = lambda rel: os.path.join(d, *rel.split("/"))
        own, agr, cty = fields(f("owner.md")), fields(f("documents/agreement.md")), fields(f("documents/county-record.md"))
        ach, ins = fields(f("documents/ach.md")), fields(f("documents/insurance.md"))
        found = []
        for rel in R["required_documents"]["every_owner"]:
            if not os.path.exists(f(rel)):
                found.append("MISSING_DOCUMENT")
        a_names, c_names = names(agr.get("Owner(s) named", "")), names(cty.get("Owner(s) of record", ""))
        if any(n not in c_names for n in a_names):
            found.append("OWNER_NOT_ON_COUNTY_RECORD")
        else:
            signed = {name_key(r["Signing for"]) for r in rows_after(f("documents/agreement.md"), "Signer") if r.get("Signed", "").strip()}
            if any(n not in signed for n in c_names):
                found.append("AGREEMENT_UNSIGNED_OWNER")
        if not os.path.exists(f("documents/w9.md")):
            found.append("MISSING_W9" if own.get("Mailing country", "") == "United States" else "FOREIGN_TAX_REVIEW")
        if set(names(ach.get("Account holder name(s)", ""))) != set(a_names):
            found.append("ACH_NAME_MISMATCH")
        if R["insurance"]["policy_type_must_include"].lower() not in ins.get("Policy type", "").lower():
            found.append("INSURANCE_NOT_LANDLORD")
        if ins.get("Additional insured", "").strip() != R["insurance"]["additional_insured"]:
            found.append("MANAGER_NOT_ADDITIONAL_INSURED")
        if (money(ins.get("Liability limit")) or 0) < R["insurance"]["min_liability"]:
            found.append("INSURANCE_LIMIT_LOW")
        if os.path.exists(f("documents/association.md")):
            if fields(f("documents/association.md")).get("Lease approval by the association", "").startswith("Required"):
                found.append("ASSOCIATION_APPROVAL")
        elif own.get("Association", "None") != "None":
            found.append("MISSING_DOCUMENT")
        built = int(cty.get("Year built", "0") or 0)
        if built and built < R["lead_year"] and not os.path.exists(f("documents/lead-disclosure.md")):
            found.append("LEAD_DISCLOSURE_MISSING")
        tk = None
        if own.get("Occupied", "").startswith("Yes"):
            if not (os.path.exists(f("tenant/lease.md")) and os.path.exists(f("tenant/deposit-transfer.md"))):
                found.append("TENANT_RECORDS_MISSING")
            else:
                ls, tr = fields(f("tenant/lease.md")), fields(f("tenant/deposit-transfer.md"))
                want, got = money(ls["Security deposit"]), money(tr["Security deposit transferred"])
                res = "MATCH" if want == got else ("DEPOSIT_SHORT" if got < want else "DEPOSIT_OVER")
                if res != "MATCH":
                    found.append(res)
                on = tr["Transferred on"]
                tk = {"tenant": ls["Tenant"], "lease_deposit": want, "transferred": got, "difference": want - got, "result": res,
                      "received_on": on, "letter_due": str(dt.date.fromisoformat(on) + dt.timedelta(days=R["tenant_letter_days"])) if res == "MATCH" else None}
        found = sorted(found)
        gates = {}
        for g in GATES:
            hit = [c for c in found if g in codes[c]["gates"]]
            gates[g] = "ready" if not hit else ("hold" if all(c in R["hold_codes"] for c in hit) else "blocked")
        status = "READY" if not found else ("HOLD" if all(c in R["hold_codes"] for c in found) else "BLOCKED")
        out[slug] = {"status": status, "issues": found, "gates": gates, "takeover": tk, "owner": own, "agreement": agr, "county": cty,
                     "ach": ach, "insurance": ins, "names": agr.get("Owner(s) named", "")}
    return out, R


def team(root):
    t = {}
    for r in rows_after(os.path.join(root, "company", "owner-team.md"), "Role"):
        t[r["Role"]] = r["Name"]
    return t


def recount(root=None):
    """The facts the New owners tab shows, recounted from the raw records (keys start with 'o.')."""
    root = root or ROOT
    ev, R = evaluate(root)
    F = {"o.total": len(ev)}
    for s in ("READY", "HOLD", "BLOCKED"):
        F["o." + s] = sum(v["status"] == s for v in ev.values())
    all_codes = [c for v in ev.values() for c in v["issues"]]
    F["o.problems"] = len(all_codes)
    for cond in R["conditions"]:
        F["o.cond." + cond] = sum(R["issue_codes"][c]["condition"] == cond for c in all_codes)
    for c in sorted(set(all_codes)):
        F["o.ic." + c] = all_codes.count(c)
    for g in GATES:
        for st in ("ready", "hold", "blocked"):
            F[f"o.gate.{g}.{st}"] = sum(v["gates"][g] == st for v in ev.values())
    occ = {s: v["takeover"] for s, v in ev.items() if v["takeover"]}
    F["o.occupied"] = len(occ)
    for s, tk in occ.items():
        F[f"o.dep.{s}.lease"], F[f"o.dep.{s}.got"], F[f"o.dep.{s}.diff"] = tk["lease_deposit"], tk["transferred"], tk["difference"]
    # drafts on disk (each must be unsent; G4/G5 prove their content)
    fu = glob.glob(os.path.join(root, "owners", "*", "drafts", "*-follow-up.md"))
    og = glob.glob(os.path.join(root, "owners", "*", "drafts", "*-deposit-outgoing-manager.md"))
    tl = glob.glob(os.path.join(root, "owners", "*", "drafts", "*-tenant-letter.md"))
    F["o.followups"], F["o.outgoing"], F["o.letters"] = len(fu), len(og), len(tl)
    F["o.drafts"] = len(fu) + len(og) + len(tl)
    blank = 0
    for sh in glob.glob(os.path.join(root, "owners", "*", "setup-sheet.md")):
        for r in rows_after(sh, "Gate"):
            blank += not r.get("Signed by", "").strip() and not r.get("Date", "").strip()
    F["o.blank"] = blank
    # waiting on the new-owner team: each unsent draft (its sender), each gate ready or on hold (its person), each professional decision
    T = team(root)
    role_of_gate = {g["id"]: g["role"] for g in R["gates"]}
    wait = {}
    add = lambda role: wait.__setitem__(role, wait.get(role, 0) + 1)
    for path in fu:
        add("Owner Onboarding Coordinator")
    for path in og:
        add("Trust Accountant")
    for path in tl:
        add("Property Manager")
    for v in ev.values():
        for g in GATES:
            if v["gates"][g] in ("ready", "hold"):
                add(role_of_gate[g])
        for c in v["issues"]:
            if R["issue_codes"][c]["condition"] == "professional":
                add(R["issue_codes"][c]["fix"])
    F["o.wait.total"] = sum(wait.values())
    for role in T:
        F["o.wait." + re.sub(r"[^a-z0-9]+", "-", role.lower()).strip("-")] = wait.get(role, 0)
    rows = log_lines(root)
    F["o.rows"] = max(len(rows) - 1, 0)
    F["o.rule.deadline_days"] = R["chase_deadline_days"]
    F["o.rule.letter_days"] = R["tenant_letter_days"]
    F["o.rule.lead_year"] = R["lead_year"]
    F["o.rule.min_liability"] = R["insurance"]["min_liability"]
    F["o.rule.reserve"] = R["owner_reserve"]
    return F, ev, R


def log_lines(root):
    log = os.path.join(root, "audit", "owners-log.csv")
    return open(log, encoding="utf-8").read().rstrip("\n").split("\n") if os.path.exists(log) else []


# ------------------------------------------------------------- headless render -------------------------------------------------------------
_B = []


def browser():
    if not _B:
        pick = None
        for b in BROWSERS:
            if not os.path.exists(b):
                continue
            with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as prof:
                r = subprocess.run([b, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={prof}", "--dump-dom",
                                    "data:text/html,<p id=probe>ok</p>"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
            if 'id="probe"' in r.stdout:
                pick = b
                break
        _B.append(pick)
    return _B[0]


def dump(page, frag, width=None):
    b = browser()
    if not b or not os.path.exists(page):
        return ""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as prof:
        r = subprocess.run([b, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={prof}", "--virtual-time-budget=4000"]
                           + ([f"--window-size={width},900"] if width else []) + ["--dump-dom", "file:///" + page.replace("\\", "/") + frag],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    return r.stdout


# ------------------------------------------------------------- the checks -------------------------------------------------------------
def run(root):
    res = []
    p = lambda *a: os.path.join(root, *a)
    sha = lambda f: hashlib.sha256(open(f, "rb").read()).hexdigest()
    rec = lambda ok, name, detail: res.append((bool(ok), name, detail))
    key = json.load(open(p("tests", "answer-key-3g.json"), encoding="utf-8"))
    F, ev, R = recount(root)
    T = team(root)
    demo = dt.date.fromisoformat(R["demo_date"])
    deadline = str(demo + dt.timedelta(days=R["chase_deadline_days"]))

    # G1 inputs locked: every frozen record unchanged (earlier phases + the 8 owner packets), and the lock lines match
    frozen = [l.split(None, 1) for l in open(p("tests", "frozen-3g.txt"), encoding="utf-8") if re.match(r"^[0-9a-f]{64}\s", l)] if os.path.exists(p("tests", "frozen-3g.txt")) else []
    changed = [f.strip() for h, f in frozen if not os.path.exists(p(*f.strip().split("/"))) or sha(p(*f.strip().split("/"))) != h]
    lock = open(p("tests", "LOCK.txt"), encoding="utf-8").read()
    lock_ok = sha(p("tests", "answer-key-3g.json")) in lock and bool(frozen) and sha(p("tests", "frozen-3g.txt")) in lock
    packets = sum(f.strip().startswith("owners/") for _, f in frozen)
    rec(frozen and not changed and lock_ok and packets >= 50, "G1 inputs locked: earlier records and the owner packets unchanged, lock lines match",
        f"{len(frozen)} frozen files ({packets} in the owner packets), changed {changed[:5]}; lock lines match: {lock_ok}")

    # G2 the 8 packets: required files, every record labeled sample, .example emails, 555 phones, IDs and bank numbers masked
    probs = []
    for d in sorted(glob.glob(p("owners", "*", ""))):
        slug = os.path.basename(os.path.dirname(d))
        for f in glob.glob(os.path.join(d, "**", "*.md"), recursive=True):
            t = open(f, encoding="utf-8").read()
            rel = os.path.relpath(f, root).replace("\\", "/")
            if not re.search(r"^\*Sample (records|record)\b", t, re.M):
                probs.append(f"{rel}: no sample label")
            if re.search(r"\bfake\b", t, re.I):
                probs.append(f"{rel}: says fake")
            probs += [f"{rel}: email {e}" for e in re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", t) if not e.endswith(".example")]
            probs += [f"{rel}: phone {x}" for x in re.findall(r"\(\d{3}\) \d{3}-\d{4}", t) if not x.startswith("(555) 010-")]
            probs += [f"{rel}: long number {x}" for x in re.findall(r"(?<![\w-])\d{6,}(?![\w-])", t)]
            if "/documents/" in rel or "/tenant/" in rel or rel.endswith("owner.md"):
                for line in t.splitlines():
                    if re.search(r"\d+ (?:[A-Z][a-z]+ )+(?:Ln|Ct|Dr|Way|Cir|Blvd|Ter|Rd|Ave|St|Crescent)\b", line) and "(fictional)" not in line:
                        probs.append(f"{rel}: address not marked fictional")
        w9 = fields(os.path.join(d, "documents", "w9.md"))
        if w9 and not re.search(r"X{2,}", w9.get("Taxpayer ID", "")):
            probs.append(f"{slug}: tax ID not masked")
        if not re.match(r"^X{4,}\d{4}\b", fields(os.path.join(d, "documents", "ach.md")).get("Account number", "")):
            probs.append(f"{slug}: account number not masked to the last 4")
    n_own = len(glob.glob(p("owners", "*", "owner.md")))
    rec(n_own == 8 and not probs, "G2 8 owner packets: labeled sample, .example emails, 555 phones, addresses fictional, IDs and bank numbers masked",
        f"{n_own} owners; problems {len(probs)} {probs[:4]}")

    # G3 intake: this check's recount = the locked answer key = what /owner-intake wrote (status, every code, every gate)
    bad_key, bad_file, files_ = [], [], 0
    for s, want in key["owners"].items():
        got = ev.get(s)
        if not got or got["status"] != want["status"] or got["issues"] != sorted(want["issues"]) or got["gates"] != want["gates"]:
            bad_key.append(s)
        f = p("owners", s, "intake.json")
        if os.path.exists(f):
            files_ += 1
            try:
                j = json.load(open(f, encoding="utf-8"))
                codes_ = sorted(i["code"] for i in j.get("issues", []))
                ev_ok = all(i.get("evidence") and all(e.get("file") and e.get("says") is not None for e in i["evidence"]) for i in j.get("issues", []))
                if j.get("status") != want["status"] or codes_ != sorted(want["issues"]) or j.get("gates") != want["gates"] or not ev_ok:
                    bad_file.append(s)
            except (ValueError, KeyError, TypeError):
                bad_file.append(s + " (unreadable)")
    extra = sorted(set(ev) - set(key["owners"]))
    tot = key["totals"]
    rec(not bad_key and not extra and files_ == 8 and not bad_file and F["o.problems"] == tot["problems"]
        and (F["o.READY"], F["o.HOLD"], F["o.BLOCKED"]) == (tot["READY"], tot["HOLD"], tot["BLOCKED"]),
        "G3 intake: recount from the documents = answer key = intake files (status, codes, gates, evidence)",
        f"recount vs key differs {bad_key}, owners not in key {extra}; {files_} of 8 intake files, differ {bad_file}; "
        f"{F['o.problems']} problems; {F['o.READY']} ready / {F['o.HOLD']} on hold / {F['o.BLOCKED']} blocked")

    # G4 follow-ups: one unsent draft per owner that isn't READY, to the owner's .example address, naming every code, 7-day deadline
    probs, n = [], 0
    for s, v in ev.items():
        fs = glob.glob(p("owners", s, "drafts", "*-follow-up.md"))
        if v["status"] == "READY":
            if fs:
                probs.append(f"{s}: draft for a READY owner")
            continue
        if len(fs) != 1:
            probs.append(f"{s}: {len(fs)} follow-ups")
            continue
        n += 1
        t = open(fs[0], encoding="utf-8").read()
        fl = fields(fs[0])
        first = next((l for l in t.splitlines() if l.startswith("*")), "")
        listed = sorted(x.strip() for x in fl.get("Issue codes", "").split(","))
        items = re.findall(r"^\d+\. \*\*", t, re.M)
        if "DRAFT ONLY" not in first or "never sends" not in first or fl.get("Status") != "DRAFT, not sent":
            probs.append(f"{s}: not marked as an unsent draft")
        if fl.get("To") != v["owner"].get("Contact email") or not fl.get("To", "").endswith(".example"):
            probs.append(f"{s}: wrong address")
        if listed != v["issues"] or len(items) != len(v["issues"]):
            probs.append(f"{s}: codes {listed} / {len(items)} items vs {v['issues']}")
        if fl.get("Deadline") != deadline or deadline not in t.split("## Message", 1)[-1]:
            probs.append(f"{s}: deadline")
        if T.get("Owner Onboarding Coordinator", "?") not in fl.get("Reviewer and sender", ""):
            probs.append(f"{s}: wrong sender")
    want_n = sum(v["status"] != "READY" for v in ev.values())
    rec(n == want_n == len(key["follow_ups"]["owners"]) and not probs and key["follow_ups"]["deadline"] == deadline,
        "G4 follow-ups: one unsent draft per stuck owner, every problem named, 7-day deadline, none for the ready owner",
        f"{n} drafts for {want_n} stuck owners (key {len(key['follow_ups']['owners'])}); deadline {deadline}; problems {probs[:4]}")

    # G5 takeovers: deposit math recounted; the short one gets an outgoing-manager draft and no tenant letter; the matching one gets the letter, dated
    probs = []
    for s, want in key["takeovers"].items():
        tk = ev.get(s, {}).get("takeover")
        j = json.load(open(p("owners", s, "takeover.json"), encoding="utf-8")) if os.path.exists(p("owners", s, "takeover.json")) else {}
        for k_ in ("lease_deposit", "transferred", "difference", "result"):
            if not tk or tk[k_] != want[k_] or j.get(k_) != want[k_]:
                probs.append(f"{s}:{k_}")
        letters = glob.glob(p("owners", s, "drafts", "*-tenant-letter.md"))
        outs = glob.glob(p("owners", s, "drafts", "*-deposit-outgoing-manager.md"))
        # 11/10 dry run: the locked key leaves "outgoing_draft" out for brandt (no draft expected); a missing key means no draft
        if bool(letters) != want["tenant_letter"] or bool(outs) != want.get("outgoing_draft", False):
            probs.append(f"{s}: letter {len(letters)} / outgoing draft {len(outs)}")
        for f in letters:
            t, fl = open(f, encoding="utf-8").read(), fields(f)
            if fl.get("Status") != "DRAFT, not sent" or fl.get("Due") != want.get("letter_due") or f"${want['lease_deposit']:,}" not in t \
                    or T.get("Property Manager", "?") not in fl.get("Reviewer and sender", "") or not fl.get("To", "").endswith(".example"):
                probs.append(f"{s}: tenant letter")
        for f in outs:
            t, fl = open(f, encoding="utf-8").read(), fields(f)
            if fl.get("Status") != "DRAFT, not sent" or f"${want['difference']:,}" not in t or "83.49(7)" not in t \
                    or T.get("Trust Accountant", "?") not in fl.get("Reviewer and sender", "") or not fl.get("To", "").endswith(".example"):
                probs.append(f"{s}: outgoing-manager draft")
    rec(not probs and F["o.occupied"] == key["totals"]["occupied"],
        "G5 tenants in place: deposit math recounted; short deposit drafted to the outgoing manager; tenant letter only when it matches",
        f"{F['o.occupied']} occupied; " + "; ".join(f"{s} {w['lease_deposit']} vs {w['transferred']} = {w['difference']}" for s, w in key["takeovers"].items())
        + f"; problems {probs[:4]}")

    # G6 setup sheets: 8 drafts; key fields equal the records; bank last 4 only; 4 sign-offs blank; the AI's gate reading equals intake
    probs, sheets = [], 0
    word = {"ready": "Nothing blocking", "hold": "On hold", "blocked": "Blocked"}
    for s, v in ev.items():
        f = p("owners", s, "setup-sheet.md")
        if not os.path.exists(f):
            probs.append(f"{s}: no sheet")
            continue
        sheets += 1
        t = open(f, encoding="utf-8").read()
        allrows = {}
        for block in re.split(r"^## ", t, flags=re.M):
            for line in block.splitlines():
                c = [x.strip() for x in line.strip().strip("|").split("|")]
                if line.startswith("|") and len(c) == 3 and c[0] not in ("Field", "---"):
                    allrows.setdefault(c[0], c[1])
        last4 = re.sub(r"[^\d]", "", v["ach"].get("Account number", "").split("(")[0])[-4:]
        expect = {"Owner name(s)": v["names"], "Parcel ID": v["county"].get("Parcel ID"), "Year built": v["county"].get("Year built"),
                  "Address": v["owner"].get("Property address"), "Agreement": v["agreement"].get("Agreement")}
        wrong = [k_ for k_, x in expect.items() if allrows.get(k_) != x]
        if wrong:
            probs.append(f"{s}: fields {wrong}")
        if f"ending {last4}" not in allrows.get("Owner payments to", "") or re.search(r"X{4,}\d{4}", t):
            probs.append(f"{s}: bank not shown as last 4")
        if "not entered in any software" not in t.lower():
            probs.append(f"{s}: doesn't say it isn't entered")
        gate_rows = rows_after(f, "Gate")
        if len(gate_rows) != 4 or any(r.get("Signed by", "").strip() or r.get("Date", "").strip() for r in gate_rows):
            probs.append(f"{s}: sign-offs not 4 blank")
        for g, r in zip(GATES, gate_rows):
            if not r.get("What the AI found", "").startswith(word[v["gates"][g]]):
                probs.append(f"{s}: {g} reads {r.get('What the AI found', '')[:20]}")
        if v["takeover"] and f"${v['takeover']['transferred']:,}" not in allrows.get("Deposit received", ""):
            probs.append(f"{s}: deposit received")
    rec(sheets == 8 and not probs and F["o.blank"] == 32, "G6 setup sheets: 8 drafts, fields equal the records, bank last 4 only, every sign-off blank",
        f"{sheets} sheets; {F['o.blank']} blank sign-offs (want 32); problems {probs[:4]}")

    # G7 the owners log: one row per action, hash chain verifies, nothing sent, signed, paid, or entered by the AI
    lines = log_lines(root)
    links = open(p("audit", "owners-log.chain.txt"), encoding="utf-8").read().split() if os.path.exists(p("audit", "owners-log.chain.txt")) else []
    h, good = hashlib.sha256(HEADER.encode()).hexdigest(), 0
    for i, line in enumerate(lines[1:]):
        h = hashlib.sha256((h + "\n" + line.rstrip("\r")).encode("utf-8")).hexdigest()
        good += i < len(links) and links[i] == h
    rows = list(csv.DictReader(io.StringIO("\n".join(lines)))) if lines else []
    acts = [r["action"] for r in rows]
    claims = [r["result"] for r in rows if re.search(r"(?<!not )\b(sent|signed|paid|entered)\b", r["result"], re.I)]
    want_acts = {"owner_intake": 8, "takeover": F["o.occupied"], "owner_chase": F["o.followups"], "owner_setup": 8}
    off = {a: (acts.count(a), n_) for a, n_ in want_acts.items() if acts.count(a) != n_}
    rec(lines and lines[0] == HEADER and not off and good == len(lines) - 1 == len(links) and not claims,
        "G7 the owners log: one row per action, the hash chain verifies, 0 sent/signed/paid/entered by the AI",
        f"{len(rows)} rows; actions off {off}; chain {good} of {len(links)} links; claims {claims[:2]}")

    # G8 the New owners tab: one row per owner with its status; every o.* number equals this recount; renders at desktop and phone width
    page = p("dashboard", "index.html")
    html_ = open(page, encoding="utf-8").read() if os.path.exists(page) else ""
    sec = re.search(r'<section data-tab="owners"[^>]*>(.*?)</section>', html_, re.S)
    body = sec.group(1) if sec else ""
    rws = dict(re.findall(r'<tr data-owner-row="([a-z-]+)" data-status="([A-Z]+)"', body))
    bad_rows = sorted(s for s in set(rws) | set(ev) if rws.get(s) != ev.get(s, {}).get("status"))
    tags = re.findall(r'data-k="(o\.[^"]+)">([^<]*)<', html_)
    num = lambda x: int(re.sub(r"[^\d]", "", x)) if re.sub(r"[^\d]", "", x) else None
    wrong = sorted({k_ for k_, v_ in tags if k_ not in F or num(v_) != F[k_]})
    absent = sorted(set(F) - {k_ for k_, _ in tags})
    nav = bool(re.search(r'<button[^>]*data-for="owners"[^>]*>New owners</button>', html_))
    rendered = []
    for w in (1280, 390):
        dom = dump(os.path.abspath(page), "#tab=owners", w)
        shown = bool(re.search(r'<section data-tab="owners"[^>]*class="on"|<section[^>]*class="on"[^>]*data-tab="owners"', dom))
        errs = re.search(r'data-errors="(\d+)"', dom)
        rendered.append(shown and errs and errs.group(1) == "0")
    rec(sec and nav and len(rws) == 8 and not bad_rows and tags and not wrong and not absent and all(rendered),
        "G8 the New owners tab: a row per owner with its status, every number recounted, renders at desktop and phone width",
        f"tab {bool(sec)}, nav button {nav}; {len(rws)} owner rows, status wrong {bad_rows}; {len(tags)} o.* numbers, wrong {wrong[:4]}, "
        f"recounted but not shown {absent[:5]}; headless {os.path.basename(browser() or 'none')} shown at 1280 / 390 px: {rendered}")

    # G9 the skills, the README, and the suite: 4 skills that say nothing is sent; a 3g status row; pieces mapped; listed in suite.json and CI
    probs = []
    for sk in SKILLS:
        st = open(p(".claude", "skills", sk, "SKILL.md"), encoding="utf-8").read() if os.path.exists(p(".claude", "skills", sk, "SKILL.md")) else ""
        if not re.match(r"^---\r?\nname: " + re.escape(sk) + r"\r?\ndescription: .{40,}\r?\n---", st) or "nothing is sent" not in st.lower():
            probs.append(sk)
    rd = open(p("README.md"), encoding="utf-8").read()
    row = re.search(r"^\|\s*3g\s*\|.*\|\s*Built 11/10/2026", rd, re.M)
    pieces = ["`tools/owners.py`", "`tools/make_owners.py`", "`company/owner-rules.json`", "`tests/check_phase3g.py`", "`audit/owners-log.csv`"] + [f"`/{s}` skill" for s in SKILLS]
    mapped = [x for x in pieces if re.search(r"^\|\s*" + re.escape(x) + r".*Designed and directed", rd, re.M)]
    suite = json.load(open(p("tests", "suite.json"), encoding="utf-8")).get("checks", {})
    ci = open(p(".github", "workflows", "checks.yml"), encoding="utf-8").read() if os.path.exists(p(".github", "workflows", "checks.yml")) else ""
    rec(not probs and row and len(mapped) == len(pieces) and suite.get("check_phase3g.py") == N_CHECKS and "tests/check_phase3g.py" in ci,
        "G9 skills say nothing is sent; README 3g row and every piece mapped; listed in suite.json and CI",
        f"skills not right {probs}; status row {bool(row)}; {len(mapped)} of {len(pieces)} mapped; suite.json says {suite.get('check_phase3g.py')}; in CI {'tests/check_phase3g.py' in ci}")
    return res


def report(res):
    for ok, name, detail in res:
        print(("PASS" if ok else "FAIL"), "-", name, "-", detail)
    n = sum(ok for ok, _, _ in res)
    print(f"RESULT: {n} of {len(res)} checks PASS")
    return n == len(res)


def selftest():
    def edit(f, a, b):
        return ("text", f, a, b)
    breaks = [("G3", "an intake file that drops a planted problem", edit("owners/whitlock/intake.json", '"LEAD_DISCLOSURE_MISSING"', '"LEAD_DISCLOSURE_OK"')),
              ("G4", "a follow-up marked as sent", edit("owners/varma/drafts/2026-11-05-follow-up.md", "| Status | DRAFT, not sent |", "| Status | Sent 2026-11-05 |")),
              ("G5", "a takeover that calls the short deposit even", edit("owners/haddad/takeover.json", '"difference": 200', '"difference": 0')),
              ("G6", "a setup sheet with a sign-off filled in by the AI", edit("owners/brandt/setup-sheet.md", "| Management accepted | Gail Mercer, Broker of Record | Nothing blocking | |",
                                                                                "| Management accepted | Gail Mercer, Broker of Record | Nothing blocking | owner-assistant |")),
              ("G1", "an owner record edited after the lock", edit("owners/haddad/tenant/deposit-transfer.md", "| Security deposit transferred | $2,200 |", "| Security deposit transferred | $2,400 |")),
              ("G8", "a dashboard number off by one", edit("dashboard/index.html", 'data-k="o.total">8<', 'data-k="o.total">9<'))]
    caught = 0
    for code, what, (_, f, a, b) in breaks:
        tmp = tempfile.mkdtemp(prefix="p3g-")
        dst = os.path.join(tmp, "repo")
        shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        fp = os.path.join(dst, *f.split("/"))
        old = open(fp, encoding="utf-8").read() if os.path.exists(fp) else ""
        new = old.replace(a, b, 1)
        if os.path.exists(fp):
            open(fp, "w", encoding="utf-8", newline="").write(new)
        planted = new != old
        r = {n.split()[0]: ok for ok, n, _ in run(dst)}
        hit = planted and r.get(code) is False
        caught += hit
        print(f"self-test: {what} -> {code} {'caught' if hit else 'MISSED'}{'' if planted else ' (not planted: text not found)'}")
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"self-test: {caught} of {len(breaks)} breaks caught")
    return caught == len(breaks)


if __name__ == "__main__":
    if "--facts" in sys.argv:
        print(json.dumps(recount()[0], sort_keys=True))
        sys.exit(0)
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    sys.exit(0 if report(run(ROOT)) else 1)
