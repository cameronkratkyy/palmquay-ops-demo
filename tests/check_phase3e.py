"""Phase 3e check: the AI reads the insurance certificate PDF itself (fictional company, sample records).
Written 11/9/2026 before tools/certs.py or the /certs skill existed; its first run had to fail.
Until now /intake read a typed copy of each certificate (documents/coi.md). Phase 3e gives it the PDF and checks the copy against it.

    python -I -X utf8 tests/check_phase3e.py              prints every check with what it counted; exit 1 on any FAIL
    python -I -X utf8 tests/check_phase3e.py --selftest   plants 4 breaks in a copy and proves each one is caught
"""
import csv
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Where a standard pdftotext may be: on PATH (the CI workflow puts one there), a Poppler unzipped under the user's Tools folder,
# or the copy Git for Windows ships. Built at run time, so no machine's folder names are written into this public file.
PDFTOTEXT_PLACES = sorted(glob.glob(os.path.join(os.path.expanduser("~"), "Tools", "poppler*", "**", "pdftotext.exe"), recursive=True)) + [
    os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Git", "mingw64", "bin", "pdftotext.exe")]
HEADER = "timestamp,actor,vendor,action,detail,result"


def run(root):
    res = []
    p = lambda *a: os.path.join(root, *a)
    sha = lambda f: hashlib.sha256(open(f, "rb").read()).hexdigest()
    rec = lambda ok, name, detail: res.append((bool(ok), name, detail))
    key = json.load(open(p("tests", "answer-key-3e.json"), encoding="utf-8"))
    slugs = sorted(key["certificates"])

    # E1 inputs locked: every frozen record unchanged, and the lock lines match
    frozen = [l.split(None, 1) for l in open(p("tests", "frozen-3e.txt"), encoding="utf-8") if re.match(r"^[0-9a-f]{64}\s", l)]
    changed = [f for h, f in frozen if not os.path.exists(p(*f.strip().split("/"))) or sha(p(*f.strip().split("/"))) != h]
    lock = open(p("tests", "LOCK.txt"), encoding="utf-8").read()
    lock_ok = sha(p("tests", "answer-key-3e.json")) in lock and sha(p("tests", "frozen-3e.txt")) in lock
    rec(frozen and not changed and lock_ok, "E1 inputs locked: frozen records unchanged, lock lines match",
        f"{len(frozen)} frozen files, changed {changed[:5]}; lock lines match: {lock_ok}")

    # E2 the 8 certificates are real PDFs, and a standard PDF tool (pdftotext, from Xpdf or Poppler) reads every answer-key value from them
    tool = shutil.which("pdftotext") or next((t for t in PDFTOTEXT_PLACES if os.path.exists(t)), None)
    bad_struct, missing_vals, found = [], [], 0
    for s in slugs:
        f = p("vendors", s, "documents", "coi.pdf")
        b = open(f, "rb").read() if os.path.exists(f) else b""
        if not (b.startswith(b"%PDF-") and b"xref" in b and b.rstrip().endswith(b"%%EOF") and b"/FlateDecode" in b):
            bad_struct.append(s)
        if tool and b:
            t = subprocess.run([tool, "-layout", f, "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
            for field, v in key["certificates"][s].items():
                if v in t:
                    found += 1
                else:
                    missing_vals.append(f"{s}:{field}")
    want = sum(len(c) for c in key["certificates"].values())
    rec(len(slugs) == 8 and not bad_struct and tool and found == want and not missing_vals,
        "E2 8 certificates are real compressed PDFs; a standard tool reads every value",
        f"{len(slugs)} PDFs, bad structure {bad_struct}; pdftotext: {tool or 'NOT FOUND'}; {found} of {want} values read, missing {missing_vals[:4]}")

    # E3 the reader (tools/certs.py read) pulls every field from each PDF, equal to the answer key
    wrong, got_n = [], 0
    reader = p("tools", "certs.py")
    for s in slugs:
        if not os.path.exists(reader):
            wrong.append("tools/certs.py missing")
            break
        r = subprocess.run([sys.executable, "-I", "-X", "utf8", reader, "read", p("vendors", s, "documents", "coi.pdf"), "--json"],
                           capture_output=True, text=True, encoding="utf-8")
        try:
            fields = json.loads(r.stdout)
        except ValueError:
            wrong.append(f"{s}: no JSON ({r.stderr.strip()[-80:]})")
            continue
        for field, v in key["certificates"][s].items():
            got_n += fields.get(field) == v
            if fields.get(field) != v:
                wrong.append(f"{s}:{field}={fields.get(field)!r}")
    rec(got_n == want and not wrong, "E3 the reader pulls every field from the PDF, equal to the answer key",
        f"{got_n} of {want} fields right; wrong {wrong[:4]}")

    # E4 the comparison: one result file per contractor, flags exactly the answer key's (no misses, no false alarms)
    miss, extra, files = [], [], 0
    for s in slugs:
        f = p("vendors", s, "documents", "coi-check.json")
        if not os.path.exists(f):
            miss.append(f"{s}: no coi-check.json")
            continue
        try:
            data = json.load(open(f, encoding="utf-8"))
        except ValueError:
            miss.append(f"{s}: coi-check.json is not valid JSON")
            continue
        files += 1
        got = {(x["field"], x["certificate"], x["record"]) for x in data.get("differences", [])}
        exp = {(x["field"], x["certificate"], x["record"]) for x in key["flags"][s]}
        miss += [f"{s}:{x[0]}" for x in exp - got]
        extra += [f"{s}:{x[0]}" for x in got - exp]
    nflags = sum(len(v) for v in key["flags"].values())
    rec(files == 8 and not miss and not extra and nflags == 1, "E4 the copy is checked against the PDF: every planted difference caught, no false alarms",
        f"{files} of 8 result files; answer key has {nflags} difference(s); missed {miss}; false alarms {extra}")

    # E5 the summary a person reads: 8 contractors, 7 match, 1 differs; the certificate wins; nothing sent or changed by the AI
    sm = p("docs", "certificates.md")
    t = open(sm, encoding="utf-8").read() if os.path.exists(sm) else ""
    rows = [l for l in t.splitlines() if l.startswith("|") and any(s in l for s in slugs)]
    ok_rows = sum("matches" in l for l in rows)
    diff_rows = [l for l in rows if "differs" in l]
    words = all(w in t.lower() for w in ("the certificate is the source", "a person", "nothing was sent"))
    rec(len(rows) == 8 and ok_rows == 7 and len(diff_rows) == 1 and "fernhollow" in diff_rows[0].lower() and words and "DEMO-GL-0040" in t,
        "E5 summary: 8 contractors, 7 match, 1 differs; the certificate is the source; a person fixes the record",
        f"{len(rows)} rows, {ok_rows} match, {len(diff_rows)} differ; says source/person/nothing sent: {words}")

    # E6 one audit row for the run, in its own hash-chained log
    log, chain = p("audit", "documents-log.csv"), p("audit", "documents-log.chain.txt")
    lines = open(log, encoding="utf-8").read().rstrip("\n").split("\n") if os.path.exists(log) else []
    links = open(chain, encoding="utf-8").read().split() if os.path.exists(chain) else []
    h, good = hashlib.sha256(HEADER.encode()).hexdigest(), 0
    for i, line in enumerate(lines[1:]):
        h = hashlib.sha256((h + "\n" + line.rstrip("\r")).encode("utf-8")).hexdigest()
        good += i < len(links) and links[i] == h
    acts = [r["action"] for r in csv.DictReader(io.StringIO("\n".join(lines)))] if lines else []
    rec(lines and lines[0] == HEADER and acts.count("certificate_check") == 1 and good == len(lines) - 1 == len(links),
        "E6 one audit row for the run; the log's hash chain verifies",
        f"{len(lines) - 1 if lines else 0} rows, certificate_check rows {acts.count('certificate_check')}; chain {good} of {len(links)} links")

    # E7 the skill: front matter, says what it reads, no OCR claim, nothing sent
    sk = p(".claude", "skills", "certs", "SKILL.md")
    st = open(sk, encoding="utf-8").read() if os.path.exists(sk) else ""
    fm = bool(re.match(r"^---\nname: certs\ndescription: .{40,}\n---", st))
    rec(fm and "coi.pdf" in st and "nothing is sent" in st.lower() and "no ocr" in st.lower(),
        "E7 the /certs skill: front matter; reads coi.pdf; says no OCR and nothing is sent", f"front matter {fm}; length {len(st)} chars")

    # E8 README: a 3e status row and every new piece mapped with a 'Designed and directed' line
    rd = open(p("README.md"), encoding="utf-8").read()
    row = re.search(r"^\|\s*3e\s*\|.*\|\s*Built 11/9/2026", rd, re.M)
    pieces = ["`tools/certs.py`", "`tools/make_certs.py`", "`/certs` skill", "`tests/check_phase3e.py`"]
    mapped = [x for x in pieces if re.search(r"^\|\s*" + re.escape(x) + r".*Designed and directed", rd, re.M)]
    rec(row and len(mapped) == len(pieces), "E8 README: 3e status row; every new piece mapped with a 'Designed and directed' line",
        f"status row {bool(row)}; {len(mapped)} of {len(pieces)} mapped")

    # E9 the dashboard shows it: one row per contractor on the Onboarding tab, 1 differs
    pg = open(p("dashboard", "index.html"), encoding="utf-8").read() if os.path.exists(p("dashboard", "index.html")) else ""
    sec = re.search(r'<h2>Insurance certificates, read from the PDF</h2>(.*?)</table>', pg, re.S)
    drows = re.findall(r"<tr data-cert=\"([a-z-]+)\" data-result=\"(match|differs)\"", sec.group(1)) if sec else []
    rec(len(drows) == 8 and sum(r == "differs" for _, r in drows) == 1, "E9 dashboard: the certificates section, 8 rows, 1 differs",
        f"section {bool(sec)}; {len(drows)} rows, {sum(r == 'differs' for _, r in drows)} differ")
    return res


def report(res):
    for ok, name, detail in res:
        print(("PASS" if ok else "FAIL"), "-", name, "-", detail)
    n = sum(ok for ok, _, _ in res)
    print(f"RESULT: {n} of {len(res)} checks PASS")
    return n == len(res)


def selftest():
    breaks = [("E3", "a reader that misreads one value", ("tools/certs.py", "return fields", "fields['Policy end'] = '2099-01-01'\n    return fields")),
              ("E4", "a missed difference", ("vendors/fernhollow-grounds/documents/coi-check.json", '"differences": [', '"differences": [], "x": [')),
              ("E5", "a summary that says all 8 match", ("docs/certificates.md", "differs", "matches")),
              ("E1", "an edited certificate PDF", ("vendors/kestrelbay-air-heat/documents/coi.pdf", b"/FlateDecode", b"/FlateDecode ")),
              ]
    caught = 0
    for code, what, (f, a, b) in breaks:
        tmp = tempfile.mkdtemp(prefix="p3e-")
        dst = os.path.join(tmp, "repo")
        shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        fp = os.path.join(dst, *f.split("/"))
        # read first, then write (opening for writing first empties the file, and a check would then "catch" an empty file instead)
        if isinstance(a, bytes):
            old = open(fp, "rb").read()
            new = old.replace(a, b, 1)
            open(fp, "wb").write(new)
        else:
            old = open(fp, encoding="utf-8").read()
            new = old.replace(a, b, 1)
            open(fp, "w", encoding="utf-8").write(new)
        planted = new != old and len(new) >= len(old) - 20
        res = {n.split()[0]: ok for ok, n, _ in run(dst)}
        hit = planted and res.get(code) is False
        caught += hit
        print(f"self-test: {what} -> {code} {'caught' if hit else 'MISSED'}")
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"self-test: {caught} of {len(breaks)} breaks caught")
    return caught == len(breaks)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    sys.exit(0 if report(run(ROOT)) else 1)
