"""Phase 3h check: the business side of new owners (fictional company, sample records).
Written 11/10/2026 before tools/money.py existed; its first run had to fail. It never imports the helper or the builder.
It reads money/inputs/ and the owner packets, recounts every dollar its own way (in cents), and compares with the locked answer key
(tests/answer-key-3h.json), with what the helper wrote (money/out/), and with every number in the dashboard's money sections.

    python -I -X utf8 tests/check_phase3h.py              H1-H8, prints what it counted; exit 1 on any FAIL
    python -I -X utf8 tests/check_phase3h.py --selftest   plants 5 breaks in a copy and proves each one is caught
Options: --root DIR (check a copy) · --copy (accepted for symmetry; nothing here needs the author's machine)
"""
import csv
import glob
import hashlib
import html
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from decimal import Decimal, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = sys.argv[sys.argv.index("--root") + 1] if "--root" in sys.argv else os.path.dirname(HERE)
BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
N_CHECKS = 8


def cents(x):
    return int((Decimal(x) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def money(s):
    d = re.sub(r"[^\d.]", "", (s or "").split("(")[0])
    return cents(d) if d else None


def rows_after(path, first):
    lines = open(path, encoding="utf-8").read().splitlines() if os.path.exists(path) else []
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


def tables(path):
    """Every markdown table in a file, as lists of row dicts."""
    lines = open(path, encoding="utf-8").read().splitlines() if os.path.exists(path) else []
    out, i = [], 0
    while i < len(lines):
        if lines[i].startswith("|") and i + 1 < len(lines) and lines[i + 1].startswith("|---"):
            head = [x.strip() for x in lines[i].strip().strip("|").split("|")]
            rows, j = [], i + 2
            while j < len(lines) and lines[j].startswith("|"):
                rows.append(dict(zip(head, [x.strip() for x in lines[j].strip().strip("|").split("|")])))
                j += 1
            out.append((head, rows))
            i = j
        else:
            i += 1
    return out


def table_with(path, col):
    return next((rows for head, rows in tables(path) if col in head), [])


def recount(root=None):
    """Every number the money sections show, from the inputs only. Money in cents; other numbers as plain integers."""
    root = root or ROOT
    p = lambda *a: os.path.join(root, *a)
    fs = json.load(open(p("money", "inputs", "fee-schedule.json"), encoding="utf-8"))
    asm = json.load(open(p("money", "inputs", "assumptions.json"), encoding="utf-8"))
    ev = rows_after(p("money", "inputs", "rent-evidence.md"), "Owner")
    mo = p("money", "inputs", "month-2026-12.md")
    F, A = {}, {}
    pct = Decimal(fs["management_fee_pct"]) / 100
    for r in ev:
        o = r["Owner"]
        comps = sorted(money(r[f"Comparable {i}"]) for i in (1, 2, 3))
        lease = money(r["Current lease rent"]) if r["Current lease rent"] != "none" else None
        asked = money(r["Owner asked"]) if r["Owner asked"] != "none" else None
        ready, fund = money(r["Make-ready estimate"]), money(r["Owner funding"])
        flags = []
        if asked is not None and asked > comps[-1]:
            flags.append("RENT_ABOVE_EVIDENCE")
        if ready > fund:
            flags.append("REPAIRS_NEED_FUNDING")
        A[o] = {"range": [comps[0], comps[-1]], "proposed": lease if lease is not None else comps[1], "flags": flags,
                "suggest": "CONDITIONAL" if flags else "ACCEPT", "vacant": lease is None}
        F[f"b.acc.{o}.lo"], F[f"b.acc.{o}.hi"], F[f"b.acc.{o}.plan"] = comps[0], comps[-1], A[o]["proposed"]
        F[f"b.acc.{o}.ready"], F[f"b.acc.{o}.fund"] = ready, fund
        if asked is not None:
            F[f"b.acc.{o}.asked"] = asked
        if lease is not None:
            F[f"b.acc.{o}.lease"] = lease
    F["b.acc.accept"] = sum(a["suggest"] == "ACCEPT" for a in A.values())
    F["b.acc.conditional"] = sum(a["suggest"] == "CONDITIONAL" for a in A.values())
    # December: statements, batch, reconciliation
    rent = {r["Owner"]: money(r["Amount"]) for r in table_with(mo, "Tenant")}
    inv = table_with(mo, "Vendor")
    limit = cents(fs["repair_approval_limit"])
    reserve = cents(fs["owner_reserve"])
    S, held, batch = {}, {}, 0
    for o in sorted(rent):
        fee = int((Decimal(rent[o]) * pct).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        paid = sum(money(i["Amount"]) for i in inv if i["Owner"] == o and (money(i["Amount"]) <= limit or i["Owner approval on file"].lower().startswith("yes")))
        hold = sum(money(i["Amount"]) for i in inv if i["Owner"] == o and not (money(i["Amount"]) <= limit or i["Owner approval on file"].lower().startswith("yes")))
        for i in inv:
            if i["Owner"] == o and money(i["Amount"]) > limit and not i["Owner approval on file"].lower().startswith("yes"):
                held[i["Invoice"]] = "INVOICE_NEEDS_OWNER_APPROVAL"
        opening = reserve
        payout = opening + rent[o] - fee - paid - reserve - hold
        S[o] = {"opening": opening, "rent": rent[o], "fee": fee, "repairs_paid": paid, "held": hold, "reserve_kept": reserve, "payout": payout}
        for k_, v in S[o].items():
            F[f"b.st.{o}.{k_}"] = v
        batch += fee + paid + payout
    F["b.batch.total"] = batch
    for i in inv:
        F[f"b.batch.{i['Invoice']}"] = money(i["Amount"])
    bal = {r["Account"]: money(r["Bank balance"]) for r in table_with(mo, "Bank balance")}
    own_bank = bal.get("Owner funds trust account")
    dep_bank = bal.get("Tenant deposit trust account")
    own_liab = sum(s["reserve_kept"] + s["held"] for s in S.values())
    own_book = sum(s["opening"] + s["rent"] - s["fee"] - s["repairs_paid"] - s["payout"] for s in S.values())
    leases, got = 0, 0
    for o in S:
        leases += money(_field(p("owners", o, "tenant", "lease.md"), "Security deposit"))
        got += money(_field(p("owners", o, "tenant", "deposit-transfer.md"), "Security deposit transferred"))
    R = {"owner_funds": {"bank": own_bank, "book": own_book, "liabilities": own_liab, "difference": own_liab - own_bank},
         "deposits": {"bank": dep_bank, "book": got, "liabilities": leases, "difference": leases - dep_bank}}
    for acct, short in (("owner_funds", "own"), ("deposits", "dep")):
        for k_, v in R[acct].items():
            F[f"b.rec.{short}.{k_}"] = v
    # economics
    doors = len(A)
    vac = [a for a in A.values() if a["vacant"]]
    allrent = sum(a["proposed"] for a in A.values())
    monthly = int((Decimal(allrent) * pct).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    days = fs["days_in_month_convention"]
    vrent = sum(a["proposed"] for a in vac)
    q = lambda x: int(Decimal(x).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    E = {"december_fees": sum(s["fee"] for s in S.values()), "monthly_fees_all_rented": monthly,
         "revenue_per_door_month": q(Decimal(monthly) / doors),
         "leasing_fees_vacant": sum(q(Decimal(a["proposed"]) * fs["leasing_fee_pct_of_first_month"] / 100) for a in vac),
         "vacant_rent_per_day": q(Decimal(vrent) / days), "vacant_fee_per_day": q(Decimal(vrent) * pct / days),
         "rent_sooner": q(Decimal(vrent) * asm["days_sooner"] / days), "fees_sooner": q(Decimal(vrent) * pct * asm["days_sooner"] / days),
         "staff_saved_per_owner": q(Decimal(cents(asm["coordinator_cost_per_hour"])) * (asm["minutes_per_owner_by_hand"] - asm["minutes_per_owner_with_system"]) / 60)}
    E["staff_saved_all"] = E["staff_saved_per_owner"] * doors
    for k_, v in E.items():
        F["b.eco." + k_] = v
    F["b.eco.doors"], F["b.eco.vacant"] = doors, len(vac)
    F["b.rule.fee_pct"], F["b.rule.leasing_pct"] = fs["management_fee_pct"], fs["leasing_fee_pct_of_first_month"]
    F["b.rule.limit"], F["b.rule.reserve"], F["b.rule.days_month"] = limit, reserve, days
    F["b.as.cost_hour"], F["b.as.min_hand"], F["b.as.min_sys"], F["b.as.days"] = cents(asm["coordinator_cost_per_hour"]), asm["minutes_per_owner_by_hand"], asm["minutes_per_owner_with_system"], asm["days_sooner"]
    F["b.bench.rpu"], F["b.bench.margin"] = cents(asm["benchmark"]["revenue_per_unit_month"]), asm["benchmark"]["profit_margin_pct"]
    return F, {"acceptance": A, "statements": S, "held": held, "reconciliation": R, "economics": E, "batch_total": batch}


def _field(path, name):
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^\|\s*" + re.escape(name) + r"\s*\|\s*([^|]*?)\s*\|", line)
        if m:
            return m.group(1)
    return ""


def money_keys():
    """Keys whose values are money (in cents); the rest are plain counts, percents, minutes, or days."""
    return re.compile(r"^b\.(acc\.\w+\.(lo|hi|plan|ready|fund|asked|lease)|st\.|batch\.|rec\.|eco\.(?!doors$|vacant$)|rule\.(limit|reserve)$|as\.cost_hour$|bench\.rpu$)")


_B = []


def browser():
    if not _B:
        pick = None
        for b in BROWSERS:
            if os.path.exists(b):
                with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as prof:
                    r = subprocess.run([b, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={prof}", "--dump-dom",
                                        "data:text/html,<p id=probe>ok</p>"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
                if 'id="probe"' in r.stdout:
                    pick = b
                    break
        _B.append(pick)
    return _B[0]


def run(root):
    res = []
    p = lambda *a: os.path.join(root, *a)
    sha = lambda f: hashlib.sha256(open(f, "rb").read()).hexdigest()
    rec = lambda ok, name, detail: res.append((bool(ok), name, detail))
    key = json.load(open(p("tests", "answer-key-3h.json"), encoding="utf-8"))
    F, X = recount(root)
    out = lambda *a: p("money", "out", *a)
    jl = lambda f: json.load(open(f, encoding="utf-8")) if os.path.exists(f) else {}

    # H1 inputs locked
    frozen = [l.split(None, 1) for l in open(p("tests", "frozen-3h.txt"), encoding="utf-8") if re.match(r"^[0-9a-f]{64}\s", l)] if os.path.exists(p("tests", "frozen-3h.txt")) else []
    changed = [f.strip() for h, f in frozen if not os.path.exists(p(*f.strip().split("/"))) or sha(p(*f.strip().split("/"))) != h]
    lock = open(p("tests", "LOCK.txt"), encoding="utf-8").read()
    lock_ok = sha(p("tests", "answer-key-3h.json")) in lock and bool(frozen) and sha(p("tests", "frozen-3h.txt")) in lock
    rec(len(frozen) == 4 and not changed and lock_ok, "H1 inputs locked: the 4 money inputs unchanged, lock lines match",
        f"{len(frozen)} frozen inputs, changed {changed}; lock lines match: {lock_ok}")

    # H2 acceptance review: recount = key = what the helper wrote; every suggestion is a draft a person decides
    acc = jl(out("acceptance.json"))
    bad = [o for o, w in key["acceptance"].items() if X["acceptance"].get(o, {}).get("range") != w["range"] or X["acceptance"][o]["proposed"] != w["proposed"]
           or X["acceptance"][o]["flags"] != w["flags"] or X["acceptance"][o]["suggest"] != w["suggest"]]
    bad_out = [o for o, w in key["acceptance"].items() if acc.get(o, {}).get("range") != w["range"] or acc.get(o, {}).get("proposed") != w["proposed"]
               or acc.get(o, {}).get("flags") != w["flags"] or acc.get(o, {}).get("suggest") != w["suggest"] or acc.get(o, {}).get("decision") != ""]
    memo = open(out("acceptance.md"), encoding="utf-8").read() if os.path.exists(out("acceptance.md")) else ""
    rec(not bad and not bad_out and memo.startswith("# ") and "DRAFT" in memo and "Gail Mercer" in memo,
        "H2 acceptance review: rent range, rent to plan on, flags, and suggestion recounted; the decision is left blank for the broker",
        f"recount vs key differs {bad}; output differs {bad_out}; {F['b.acc.accept']} accept / {F['b.acc.conditional']} conditional suggested")

    # H3 December statements: every line recounted; drafts, not sent
    st = jl(out("statements.json"))
    bad = [o for o, w in key["statements"].items() if X["statements"].get(o) != w or st.get(o) != w]
    drafts = sorted(glob.glob(out("statements", "2026-12-*.md")))
    nd = [f for f in drafts if "| Status | DRAFT, not sent |" not in open(f, encoding="utf-8").read()]
    rec(not bad and len(drafts) == 2 and not nd,
        "H3 December owner statements: rent, fee, repairs, held, reserve, payout recounted; both are unsent drafts",
        f"differ {bad}; {len(drafts)} statement drafts, not marked unsent {nd}; payouts " + ", ".join(f"{o} {w['payout']}" for o, w in key["statements"].items()))

    # H4 payment batch: lines add up, the held invoice isn't in it, nothing marked paid, a person releases it
    pb = jl(out("payment-batch-2026-12.json"))
    lines = pb.get("lines", [])
    total = sum(l.get("amount", 0) for l in lines)
    held_ids = sorted(h.get("invoice") for h in pb.get("held", []))
    in_batch_held = [l for l in lines if l.get("invoice") in held_ids]
    no_src = [l for l in lines if not (l.get("source") and l.get("authority"))]
    paid = [l for l in lines if l.get("status") != "draft, not paid"]
    rec(total == key["batch_total"] == X["batch_total"] == pb.get("total") and held_ids == sorted(key["held_invoices"]) and not in_batch_held and not no_src and not paid,
        "H4 payment batch: lines add up, the held invoice is out, every line has its source and authority, nothing marked paid",
        f"{len(lines)} lines, total {total} (key {key['batch_total']}); held {held_ids}; missing source/authority {len(no_src)}; not 'draft, not paid' {len(paid)}")

    # H5 reconciliation: the owner-funds account balances; the deposit account shows its $200 difference, explained; the broker's sign-off blank
    rc = jl(out("reconciliation-2026-12.json"))
    rmd = open(out("reconciliation-2026-12.md"), encoding="utf-8").read() if os.path.exists(out("reconciliation-2026-12.md")) else ""
    ok_nums = X["reconciliation"] == key["reconciliation"] and {a: rc.get(a) for a in key["reconciliation"]} == key["reconciliation"]
    sign = re.search(r"\| Broker of Record \| Gail Mercer \|\s*\|\s*\|", rmd)
    rec(ok_nums and sign and "Tidewell" in rmd and "balanced" not in rmd.lower().split("deposit")[-1][:400],
        "H5 trust reconciliation: owner funds balance; the deposit account's difference is shown and explained; broker sign-off blank",
        f"numbers match key {ok_nums}; broker sign-off blank {bool(sign)}; deposit difference {X['reconciliation']['deposits']['difference']}")

    # H6 economics: every figure recounted; every assumption labeled as one
    eco = jl(out("economics.json"))
    bad = [k_ for k_, w in key["economics"].items() if X["economics"].get(k_) != w or eco.get(k_) != w]
    asm = json.load(open(p("money", "inputs", "assumptions.json"), encoding="utf-8"))
    labeled = all("Assumption" in asm[n] for n in ("coordinator_cost_note", "minutes_note", "days_sooner_note"))
    rec(not bad and labeled, "H6 firm economics: fees, revenue per door, leasing fees, cost of a slow day, staff time recounted; assumptions labeled",
        f"differ {bad}; assumptions labeled {labeled}; revenue per door {X['economics']['revenue_per_door_month']} cents a month")

    # H7 the dashboard's money sections: every data-b number equals the recount, no other digit, renders
    page = p("dashboard", "index.html")
    html_ = open(page, encoding="utf-8").read() if os.path.exists(page) else ""
    secs = re.findall(r'<div data-money[^>]*>(.*?)<!-- /money -->', html_, re.S)
    body = "".join(secs)
    tags = re.findall(r'data-b="(b\.[^"]+)">([^<]*)<', body)
    mk = money_keys()

    def parse(k_, v):
        if mk.match(k_):
            return money(v)
        d = re.sub(r"[^\d]", "", v)
        return int(d) if d else None
    wrong = sorted({k_ for k_, v in tags if k_ not in F or parse(k_, v) != F[k_]})
    absent = sorted(set(F) - {k_ for k_, _ in tags})
    rest = re.sub(r'<span[^>]*data-b="[^"]+">[^<]*</span>|<[^>]*data-src="[^"]*"[^>]*>[^<]*<|<code>.*?</code>|<pre.*?</pre>', " ", body, flags=re.S)
    rest = html.unescape(re.sub(r"<[^>]+>", " ", rest))  # icon codes like &#10003; are not visible digits
    rest = re.sub(r"\b\d{4}-\d{2}(-\d{2})?\b|\b[A-Z]{2,4}-\d{3,4}\b|\b(?:61J2-14\.012|83\.49\(\d\)(?:\([a-z]\))?|1099-MISC)\b", " ", rest)
    stray = re.findall(r"\S*\d\S*", rest)
    dom = ""
    b = browser()
    if b and os.path.exists(page):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as prof:
            dom = subprocess.run([b, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={prof}", "--virtual-time-budget=4000",
                                  "--dump-dom", "file:///" + os.path.abspath(page).replace("\\", "/") + "#tab=owners"],
                                 capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120).stdout
    shown = bool(re.search(r'<section data-tab="owners"[^>]*class="on"', dom)) and 'data-errors="0"' in dom and "data-money" in dom
    rec(len(secs) >= 4 and tags and not wrong and not absent and not stray and shown,
        "H7 the money sections on the New owners tab: every number recounted, no untagged digit, renders",
        f"{len(secs)} money sections, {len(tags)} numbers; wrong {wrong[:4]}; recounted but not shown {absent[:5]}; untagged digits {stray[:5]}; renders {shown}")

    # H8 README row and mapping; listed in suite.json and CI; the helper logged its two actions
    rd = open(p("README.md"), encoding="utf-8").read()
    row = re.search(r"^\|\s*3h\s*\|.*\|\s*Built 11/10/2026", rd, re.M)
    pieces = ["`tools/money.py`", "`money/inputs/`", "`tests/check_phase3h.py`"]
    mapped = [x for x in pieces if re.search(r"^\|\s*" + re.escape(x) + r".*Designed and directed", rd, re.M)]
    suite = json.load(open(p("tests", "suite.json"), encoding="utf-8")).get("checks", {})
    ci = open(p(".github", "workflows", "checks.yml"), encoding="utf-8").read()
    lg = open(p("audit", "owners-log.csv"), encoding="utf-8").read() if os.path.exists(p("audit", "owners-log.csv")) else ""
    acts = [r["action"] for r in csv.DictReader(io.StringIO(lg))] if lg else []
    rec(row and len(mapped) == len(pieces) and suite.get("check_phase3h.py") == N_CHECKS and "tests/check_phase3h.py" in ci
        and acts.count("acceptance_review") == 1 and acts.count("month_close") == 1 + len(glob.glob(p("money", "discarded-*", "README.md"))),
        "H8 README 3h row and pieces mapped; in suite.json and CI; one log row each for the review and the month",
        f"row {bool(row)}; mapped {len(mapped)} of {len(pieces)}; suite says {suite.get('check_phase3h.py')}; in CI {'tests/check_phase3h.py' in ci}; "
        f"log acceptance_review {acts.count('acceptance_review')}, month_close {acts.count('month_close')} (1 + {len(glob.glob(p('money', 'discarded-*', 'README.md')))} set-aside run)")
    return res


def report(res):
    for ok, name, detail in res:
        print(("PASS" if ok else "FAIL"), "-", name, "-", detail)
    n = sum(ok for ok, _, _ in res)
    print(f"RESULT: {n} of {len(res)} checks PASS")
    return n == len(res)


def selftest():
    breaks = [("H2", "a broker decision filled in by the AI", "money/out/acceptance.json", '"decision": ""', '"decision": "ACCEPT"'),
              ("H3", "a payout off by a dollar", "money/out/statements.json", '"payout": 168050', '"payout": 168150'),
              ("H4", "the held invoice slipped into the batch", "money/out/payment-batch-2026-12.json", '"lines": [', '"lines": [{"invoice": "MPC-0412", "amount": 0, "source": "x", "authority": "x", "status": "draft, not paid"}, '),
              ("H1", "a rent comparable edited after the lock", "money/inputs/rent-evidence.md", "| $2,250 |", "| $2,150 |"),
              ("H7", "a dashboard number changed", "dashboard/index.html", 'data-b="b.batch.total">$3,760.00<', 'data-b="b.batch.total">$3,761.00<')]
    caught = 0
    for code, what, f, a, b in breaks:
        tmp = tempfile.mkdtemp(prefix="p3h-")
        dst = os.path.join(tmp, "repo")
        shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        fp = os.path.join(dst, *f.split("/"))
        old = open(fp, encoding="utf-8").read() if os.path.exists(fp) else ""
        new = old.replace(a, b, 1)
        if os.path.exists(fp):
            open(fp, "w", encoding="utf-8", newline="").write(new)
        r = {n.split()[0]: ok for ok, n, _ in run(dst)}
        hit = new != old and r.get(code) is False
        caught += hit
        print(f"self-test: {what} -> {code} {'caught' if hit else 'MISSED'}{'' if new != old else ' (not planted)'}")
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"self-test: {caught} of {len(breaks)} breaks caught")
    return caught == len(breaks)


if __name__ == "__main__":
    if "--facts" in sys.argv:
        print(json.dumps(recount()[0], sort_keys=True))
        sys.exit(0)
    sys.exit(0 if (selftest() if "--selftest" in sys.argv else report(run(ROOT))) else 1)
