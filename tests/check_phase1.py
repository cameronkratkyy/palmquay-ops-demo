"""Phase 1 pass/fail check (C1-C7 of the brief). Prints what it counted; exit 1 on any FAIL.

    python -I -X utf8 tests/check_phase1.py            run the check
    python -I -X utf8 tests/check_phase1.py --lock     first time only: write tests/LOCK.txt (SHA-256 of the answer key)
    python -I -X utf8 tests/check_phase1.py --selftest  prove it can fail: plant 3 breaks in a temp copy, each must FAIL

C4 reads the documents themselves (never tools/make_vendors.py) and applies company/rules.json on its own,
then compares with tests/answer-key.json, which was written by hand.
"""
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# The author's machine keeps the demo at ~/Documents/Onboarding-Demo (computed, so no user name is stored here).
EXPECTED_ROOT = os.path.join(os.path.expanduser("~"), "Documents", "Onboarding-Demo")
# The author's private vault: its path lives in tests/private_paths.json, which stays on the author's machine
# (.gitignore), reversed like BANNED. Used only to prove the demo is NOT inside it. On the author's real copy the
# file is required (C1 fails without it); on other copies the vault part is reported as not checked.
_PRIVATE = os.path.join(HERE, "private_paths.json")
VAULT = json.load(open(_PRIVATE, encoding="utf-8"))["vault_reversed"][::-1] if os.path.exists(_PRIVATE) else None
# Words that must not appear anywhere in the demo, stored reversed so this file doesn't trip its own scan.
BANNED = [w[::-1] for w in ["noremac", "ytark", "notyalc", "cdls", "siuol .ts", "sroiretnikaes",
                            "setatseyktark", "liamg", "ssapmoc", "kaes", "-413"]]
# D58 (11/5, the author's decision: the partner company works with Palmquay on occasion): the partner's name
# is allowed only in a file that also contains company/rules.json projects.partner_label. Stored reversed, like BANNED.
PARTNER = "kaes"[::-1]
results = []


def rec(ok, name, counted):
    ok = bool(ok)
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} - {name} - {counted}")


def fields(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        m = re.match(r"\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", line)
        if m and m.group(1) not in ("Field", "---"):
            out[m.group(1)] = m.group(2)
    return out


def dollars(s):
    s = s.replace("$", "").replace(",", "").strip()
    return int(s) if s.isdigit() else None


def evaluate(root, rules):
    """Return {slug: {documents, issues, status, approvers}} computed from the documents only."""
    today = dt.date.fromisoformat(rules["demo_date"])
    win = rules["expiring_window_days"]
    mins = rules["insurance_minimums"]
    out = {}
    vroot = os.path.join(root, "vendors")
    for slug in sorted(os.listdir(vroot)):
        docs_dir = os.path.join(vroot, slug, "documents")
        docs = sorted(f[:-3] for f in os.listdir(docs_dir) if f.endswith(".md"))
        v = fields(os.path.join(vroot, slug, "vendor.md"))
        trade = v.get("Trade", "")
        d = {k: fields(os.path.join(docs_dir, k + ".md")) for k in docs}
        issues = []
        for need, code in (("w9", "MISSING_W9"), ("coi", "MISSING_COI"), ("request", "MISSING_REQUEST")):
            if need not in d:
                issues.append(code)
        licensed = trade in rules["required_documents"]["licensed_trades"]
        if licensed and "license" not in d:
            issues.append("MISSING_LICENSE")
        if "coi" in d:
            c = d["coi"]
            end = dt.date.fromisoformat(c["Policy end"])
            if end < today:
                issues.append("COI_EXPIRED")
            elif (end - today).days <= win:
                issues.append("COI_EXPIRING_30D")
            occ, agg = dollars(c["General liability per occurrence"]), dollars(c["General liability aggregate"])
            if occ is None or agg is None or occ < mins["gl_per_occurrence"] or agg < mins["gl_aggregate"]:
                issues.append("GL_BELOW_MIN")
            auto = dollars(c["Auto liability"])
            if auto is None or auto < mins["auto_liability"]:
                issues.append("AUTO_BELOW_MIN")
            if trade in mins["high_risk_trades"]:
                um = dollars(c.get("Umbrella", ""))
                if um is None or um < mins["umbrella_high_risk"]:
                    issues.append("UMBRELLA_MISSING")
            if not c.get("Workers' comp"):
                issues.append("WC_MISSING")
            if c.get("Additional insured", "").strip() != mins["additional_insured"]:
                issues.append("NO_ADDITIONAL_INSURED")
        if "license" in d:
            end = dt.date.fromisoformat(d["license"]["Expires"])
            if end < today:
                issues.append("LICENSE_EXPIRED")
            elif (end - today).days <= win:
                issues.append("LICENSE_EXPIRING_30D")
        names = {v.get("Legal name")}
        names |= {d[k].get(f) for k, f in (("w9", "Legal name"), ("coi", "Insured"), ("license", "License holder")) if k in d}
        if len(names) > 1:
            issues.append("NAME_MISMATCH")
        codes = rules["issue_codes"]
        status = "READY" if not issues else ("HOLD" if all(codes[i] == "HOLD" for i in issues) else "BLOCKED")
        amount = dollars(d["request"]["Contract amount"]) if "request" in d else None
        approvers = []
        for tier in rules["approval_tiers"]:
            if amount is not None and (tier["max_amount"] is None or amount <= tier["max_amount"]):
                approvers = tier["approvers"]
                break
        out[slug] = {"documents": docs, "issues": sorted(issues), "status": status, "approvers": approvers}
    return out


def run(root):
    results.clear()
    rules = json.load(open(os.path.join(root, "company", "rules.json"), encoding="utf-8"))
    key = json.load(open(os.path.join(root, "tests", "answer-key.json"), encoding="utf-8"))["vendors"]

    # C1 location
    parents, p = [], os.path.dirname(root)
    while True:
        if os.path.exists(os.path.join(p, "CLAUDE.md")):
            parents.append(p)
        if os.path.dirname(p) == p:
            break
        p = os.path.dirname(p)
    in_vault = VAULT is not None and os.path.normcase(os.path.abspath(root)).startswith(os.path.normcase(VAULT))
    is_real = os.path.normcase(root) == os.path.normcase(EXPECTED_ROOT)
    vault_note = ("vault path from the private file" if VAULT else
                  "MISSING private file (required on the real copy)" if is_real else
                  "vault path not configured on this copy: not checked")
    rec((not in_vault) and not parents and (is_real or "--copy" in sys.argv) and (VAULT is not None or not is_real),
        "C1 outside the vault, no CLAUDE.md above it",
        f"root {root}; inside vault {in_vault} ({vault_note}); CLAUDE.md in parents {parents}")

    # C2 rules file
    text = open(os.path.join(root, "CLAUDE.md"), encoding="utf-8").read()
    m = rules["insurance_minimums"]
    need = [rules["demo_date"], f"${m['gl_per_occurrence']:,}", f"${m['gl_aggregate']:,}", f"${m['auto_liability']:,}",
            f"${m['umbrella_high_risk']:,}", f"**{rules['expiring_window_days']} days**",
            f"${rules['approval_tiers'][0]['max_amount']:,}", f"${rules['approval_tiers'][1]['max_amount']:,}",
            f"**{rules['chase_deadline_days']} days**", "Drafts only", "audit/audit-log.csv", "Required documents", "Tone:",
            "roofing and elevator/fire", "Always list the approvers", m["additional_insured"]]
    need += sorted({r for t in rules["approval_tiers"] for r in t["approvers"]})  # every approver role
    need += sorted(rules["issue_codes"])  # every issue code, spelled exactly
    missing = [n for n in need if n not in text]
    rec(not missing, "C2 CLAUDE.md states every rule and matches rules.json", f"{len(need) - len(missing)} of {len(need)} found; missing {missing}")

    # C3 + C4 vendors
    got = evaluate(root, rules)
    with_record = sum(os.path.exists(os.path.join(root, "vendors", s, "vendor.md")) for s in got)
    docs_ok = sum(got[s]["documents"] == sorted(key[s]["documents"]) for s in key if s in got)
    rec(len(got) == 8 and with_record == 8 and docs_ok == 8 and set(got) == set(key),
        "C3 8 vendors, each with its record and exactly the key's documents",
        f"{len(got)} folders, {with_record} records, {docs_ok} of {len(key)} document sets match")
    match = [s for s in key if s in got and all(got[s][k] == (sorted(key[s][k]) if k == "issues" else key[s][k])
                                                 for k in ("issues", "status", "approvers"))]
    miss = {s: got.get(s) for s in key if s not in match}
    rec(len(match) == 8, "C4 recomputed from the documents = answer key", f"{len(match)} of 8 match; mismatches {miss}")
    covered = {i for s in key for i in key[s]["issues"]}
    want = {"COI_EXPIRED", "GL_BELOW_MIN", "MISSING_W9", "NO_ADDITIONAL_INSURED", "LICENSE_EXPIRING_30D", "NAME_MISMATCH"}
    small = [s for s in key if key[s]["status"] == "READY" and len(key[s]["approvers"]) == 1]
    large = [s for s in key if key[s]["status"] == "READY" and len(key[s]["approvers"]) == 4]
    rec(want <= covered and small and large, "C4b the key covers every planted problem + a clean small and a clean large job",
        f"{len(want & covered)} of {len(want)} problem types; clean small {small}; clean large {large}")

    # C5 lock
    lock = os.path.join(root, "tests", "LOCK.txt")
    digest = hashlib.sha256(open(os.path.join(root, "tests", "answer-key.json"), "rb").read()).hexdigest()
    locked = open(lock, encoding="utf-8").read().split()[0] if os.path.exists(lock) else None
    rec(locked == digest, "C5 answer key unchanged since it was locked", f"lock {locked[:12] if locked else 'missing'}..., now {digest[:12]}...")

    # C6 privacy + fake IDs
    hits, files = [], 0
    for dp, _, fs in os.walk(root):
        for fn in fs:
            if fn.endswith((".md", ".json", ".py", ".csv", ".txt", ".html")):
                files += 1
                low = open(os.path.join(dp, fn), encoding="utf-8", errors="replace").read().lower()
                label = (rules.get("projects", {}).get("partner_label") or "").lower()
                hits += [f"{fn}:{w}" for w in BANNED if w in low and not (w == PARTNER and label and label in low)]
    ids = [(k, val) for s in got for doc in ("w9", "coi", "license")
           if os.path.exists(os.path.join(root, "vendors", s, "documents", doc + ".md"))
           for k, val in fields(os.path.join(root, "vendors", s, "documents", doc + ".md")).items()
           if k in ("Taxpayer ID", "Policy number", "License number")]
    bad_ids = [i for i in ids if "XX" not in i[1] and "DEMO" not in i[1]]
    rec(not hits and not bad_ids and files > 0 and ids, "C6 no personal words; every ID is visibly fake",
        f"{files} files scanned for {len(BANNED)} words: {len(hits)} hits {hits}; {len(ids)} IDs, {len(bad_ids)} not marked fake")

    # C7 README teaching map
    rp = os.path.join(root, "README.md")
    rd = open(rp, encoding="utf-8").read() if os.path.exists(rp) else ""
    lines = rd.splitlines()
    start = next((i for i, l in enumerate(lines) if l.startswith("| Piece") and "Industry term" in l and "Resume line" in l), None)
    rows = []
    if start is not None:
        for l in lines[start + 2:]:
            if not l.startswith("| "):
                break
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            if len(cells) == 5 and all(cells):
                rows.append(cells[0])
    rec(len(rows) >= 8, "C7 README maps each piece (industry term + resume line)",
        f"{len(rows)} filled 5-column rows in the mapping table (want 8+): {rows}")

    print(f"\nRESULT: {sum(results)} of {len(results)} checks PASS")
    return all(results)


def selftest():
    breaks = [
        ("an expired license planted in the clean small job", "vendors/kestrelbay-air-heat/documents/license.md", "2027-08-31", "2026-10-01"),
        ("a personal word planted in a document", "vendors/skyquay-lift-fire/vendor.md", "Submitted (", "Submitted for " + "noremaC"[::-1] + " ("),
        ("the partner named without its label", "vendors/kestrelbay-air-heat/vendor.md", "Submitted (", "Submitted via " + "KAES"[::-1] + " ("),
        ("the answer key edited after locking", "tests/answer-key.json", '"why": "clean small job"', '"why": "clean"'),
    ]
    ok_all = True
    for name, rel, old, new in breaks:
        tmp = tempfile.mkdtemp()
        cp = os.path.join(tmp, "Onboarding-Demo")
        shutil.copytree(ROOT, cp)
        p = os.path.join(cp, rel)
        s = open(p, encoding="utf-8").read()
        assert old in s, f"selftest setup: '{old}' not in {rel}"
        open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))
        r = subprocess.run([sys.executable, "-I", "-X", "utf8", os.path.join(cp, "tests", "check_phase1.py"), "--copy"],
                           capture_output=True, text=True)
        failed = r.returncode != 0
        ok_all &= failed
        lines = [l for l in r.stdout.splitlines() if l.startswith("FAIL")]
        print(f"{'PASS' if failed else 'FAIL'} - selftest: {name} makes the check FAIL - flagged {[l.split(' - ')[1] for l in lines]}")
        shutil.rmtree(tmp, ignore_errors=True)
    return ok_all


if __name__ == "__main__":
    if "--lock" in sys.argv:
        k = os.path.join(ROOT, "tests", "answer-key.json")
        h = hashlib.sha256(open(k, "rb").read()).hexdigest()
        open(os.path.join(ROOT, "tests", "LOCK.txt"), "w", encoding="utf-8").write(
            f"{h}  answer-key.json  locked {dt.datetime.now():%Y-%m-%d %H:%M} before any Phase 2 run\n")
        print("locked", h[:12])
    elif "--selftest" in sys.argv:
        a = run(ROOT)
        print("\nSelf-test (can the check fail?)")
        b = selftest()
        sys.exit(0 if a and b else 1)
    else:
        sys.exit(0 if run(ROOT) else 1)
