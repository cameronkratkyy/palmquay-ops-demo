"""Phase 3e: read each contractor's insurance certificate PDF and check the typed copy against it (fictional company, sample records).
Python's standard library only: it opens the PDF, inflates its compressed content streams, and reads the text operators in page order.
It reads text PDFs; it does not do OCR, so a scanned image would come back empty and be flagged for a person.
Nothing here sends, signs, changes a record, or opens a network connection.

    python -I -X utf8 tools/certs.py read <pdf> [--json]   the fields on one certificate ("Label: value" lines)
    python -I -X utf8 tools/certs.py check                  /certs: all 8 certificates vs their typed records; writes the results,
                                                            docs/certificates.md, and exactly one row in audit/documents-log.csv
    python -I -X utf8 tools/certs.py verify-log             recompute the documents log's hash chain (read-only)
Exit codes: 0 ok, 2 a file is unreadable, 3 refused (already done, or the log's chain is broken).
"""
import csv
import datetime as dt
import glob
import hashlib
import io
import json
import os
import re
import sys
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "audit", "documents-log.csv")
CHAIN = os.path.join(ROOT, "audit", "documents-log.chain.txt")
HEADER = "timestamp,actor,vendor,action,detail,result"


# ------------------------------------------------------------- reading a PDF -------------------------------------------------------------
def streams(b):
    """every content stream's bytes, inflated when it says /FlateDecode"""
    out = []
    # one object's dictionary right before its "stream" keyword (never reaching back past an earlier object's "endobj")
    for m in re.finditer(rb"\d+\s+\d+\s+obj\s*<<((?:(?!endobj).)*?)>>\s*stream\r?\n", b, re.S):
        d, start = m.group(1), m.end()
        if b"/Length1" in d or b"/Subtype" in d:  # embedded font files and images carry no page text
            continue
        length = re.search(rb"/Length\s+(\d+)(?!\s+\d+\s+R)", d)
        end = start + int(length.group(1)) if length else b.index(b"endstream", start)
        data = b[start:end]
        if b"/FlateDecode" in d:
            data = zlib.decompress(data)
        out.append(data)
    return out


def literal(s, i):
    """parse a PDF literal string starting after '(' at s[i]; returns (bytes, next index)"""
    out, depth = bytearray(), 1
    while i < len(s):
        c = s[i]
        if c == 0x5C:  # backslash
            n = s[i + 1]
            if 0x30 <= n <= 0x37:
                oct_ = re.match(rb"[0-7]{1,3}", s[i + 1:i + 4]).group(0)
                out.append(int(oct_, 8) & 0xFF)
                i += 1 + len(oct_)
                continue
            out += {ord("n"): b"\n", ord("r"): b"\r", ord("t"): b"\t", ord("b"): b"\b", ord("f"): b"\f"}.get(n, bytes([n]))
            i += 2
            continue
        if c == 0x28:
            depth += 1
        elif c == 0x29:
            depth -= 1
            if depth == 0:
                return bytes(out), i + 1
        out.append(c)
        i += 1
    raise ValueError("unterminated string")


def text_runs(content):
    """(x, y, text) for each string shown, tracking Td / TD / Tm / T* positions inside BT ... ET"""
    runs, x, y, lead, i, stack = [], 0.0, 0.0, 0.0, 0, []
    tok = re.compile(rb"\(|<[0-9A-Fa-f\s]*>|\[|\]|/[^\s/\[\]()<>]+|[-+]?\d*\.?\d+|[A-Za-z'\"*]+")
    while i < len(content):
        m = tok.search(content, i)
        if not m:
            break
        t, i = m.group(0), m.end()
        if t == b"(":
            sv, i = literal(content, i)
            stack.append(sv)
        elif t.startswith(b"<"):
            stack.append(bytes.fromhex(re.sub(rb"\s", b"", t[1:-1]).decode()))
        elif t == b"[":
            stack.append("[")
        elif t == b"]":
            parts = []
            while stack and stack[-1] != "[":
                v = stack.pop()
                if isinstance(v, bytes):
                    parts.append(v)
            if stack:
                stack.pop()
            stack.append(b"".join(reversed(parts)))
        elif re.match(rb"^[-+]?\d*\.?\d+$", t) or t.startswith(b"/"):
            stack.append(t)
        else:
            op = t
            if op == b"BT":
                x = y = 0.0
            elif op in (b"Td", b"TD") and len(stack) >= 2:
                x, y = x + float(stack[-2]), y + float(stack[-1])
                if op == b"TD":
                    lead = -float(stack[-1])
            elif op == b"Tm" and len(stack) >= 6:
                x, y = float(stack[-2]), float(stack[-1])
            elif op == b"TL" and stack:
                lead = float(stack[-1])
            elif op == b"T*":
                y -= lead
            elif op in (b"Tj", b"TJ", b"'", b'"') and stack and isinstance(stack[-1], bytes):
                if op in (b"'", b'"'):
                    y -= lead
                runs.append((x, y, stack[-1].decode("cp1252")))
            stack = []
    return runs


def lines(pdf_path):
    b = open(pdf_path, "rb").read()
    if not b.startswith(b"%PDF-"):
        raise ValueError(f"{pdf_path} is not a PDF")
    runs = [r for s in streams(b) for r in text_runs(s)]
    rows = {}
    for x, y, t in runs:
        rows.setdefault(round(y), []).append((x, t))
    return [" ".join(t for _, t in sorted(v)) for _, v in sorted(rows.items(), key=lambda kv: -kv[0])]


def read_fields(pdf_path):
    fields = {}
    for line in lines(pdf_path):
        m = re.match(r"^([A-Z][A-Za-z' ]{1,60}):\s+(.+)$", line.strip())
        if m and m.group(1) not in fields:
            fields[m.group(1)] = m.group(2).strip()
    return fields


# ------------------------------------------------------------- the log -------------------------------------------------------------
def chain_ok():
    if not os.path.exists(LOG):
        return True, 0, 0
    ls = open(LOG, encoding="utf-8", newline="").read().rstrip("\n").split("\n")
    if ls[0].rstrip("\r") != HEADER:
        return False, 0, 0
    links = open(CHAIN, encoding="utf-8").read().split() if os.path.exists(CHAIN) else []
    h, ok = hashlib.sha256(HEADER.encode()).hexdigest(), 0
    for i, line in enumerate(ls[1:]):
        h = hashlib.sha256((h + "\n" + line.rstrip("\r")).encode("utf-8")).hexdigest()
        ok += i < len(links) and links[i] == h
    n = len(ls) - 1
    return ok == n == len(links), n, ok


def append_row(vendor, action, detail, result):
    good, n, _ = chain_ok()
    if not good:
        raise SystemExit(3)
    new = not os.path.exists(LOG)
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerow([dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), "onboarding-assistant", vendor, action, detail, result])
    row = buf.getvalue().rstrip("\n")
    with open(LOG, "a", encoding="utf-8", newline="") as f:
        f.write((HEADER + "\n" if new else "") + row + "\n")
    links = open(CHAIN, encoding="utf-8").read().split() if os.path.exists(CHAIN) else []
    prev = links[-1] if links else hashlib.sha256(HEADER.encode()).hexdigest()
    with open(CHAIN, "a", encoding="utf-8", newline="\n") as f:
        f.write(hashlib.sha256((prev + "\n" + row).encode("utf-8")).hexdigest() + "\n")


# ------------------------------------------------------------- /certs -------------------------------------------------------------
def typed(md):
    return {m.group(1): m.group(2).strip() for m in re.finditer(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", open(md, encoding="utf-8").read(), re.M)
            if m.group(1) not in ("Field", "---")}


def check():
    if os.path.exists(LOG) and any(r["action"] == "certificate_check" for r in csv.DictReader(open(LOG, encoding="utf-8"))):
        print("refused: the certificates were already checked (one run, one log row)")
        raise SystemExit(3)
    results = []
    for pdf_path in sorted(glob.glob(os.path.join(ROOT, "vendors", "*", "documents", "coi.pdf"))):
        slug = pdf_path.split(os.sep)[-3]
        md = os.path.join(os.path.dirname(pdf_path), "coi.md")
        rec = typed(md)
        try:
            got = read_fields(pdf_path)
        except (ValueError, zlib.error, IndexError, UnicodeDecodeError) as e:  # e.g. a browser-made PDF with embedded subset fonts
            got = {}
            print(f"{slug}: could not read the PDF ({type(e).__name__}); sent to a person")
        if not got:
            diffs = [{"field": "(whole certificate)", "certificate": "no readable text (a scan, or fonts this reader can't map): needs a person", "record": "typed copy"}]
        else:
            diffs = [{"field": f, "certificate": got.get(f, "(not on the certificate)"), "record": v} for f, v in rec.items() if got.get(f) != v]
        out = {"vendor": slug, "pdf": f"vendors/{slug}/documents/coi.pdf", "record": f"vendors/{slug}/documents/coi.md",
               "fields_read": got, "differences": diffs, "result": "differs" if diffs else "match",
               "next_step": ("A person fixes the typed record to match the certificate, then re-runs intake." if diffs else "None."),
               "run": {"by": "onboarding-assistant", "tool": "tools/certs.py check", "at": dt.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}}
        json.dump(out, open(os.path.join(os.path.dirname(pdf_path), "coi-check.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        name = rec.get("Insured", slug)
        results.append((slug, name, len(got), diffs))
    lines_md = ["# Insurance certificates, read from the PDF (fictional company, sample records)", "",
                "Until Phase 3e, intake read a typed copy of each contractor's certificate (`documents/coi.md`). Here the AI opens the certificate "
                "PDF itself (`documents/coi.pdf`), reads every field, and checks the typed copy against it. **The certificate is the source:** "
                "where they differ, a person fixes the typed record and re-runs intake. The AI changed no record, and nothing was sent.", "",
                "| Contractor | Fields read from the PDF | Result |", "|---|---|---|"]
    for slug, name, n, diffs in results:
        res = ("matches the typed record" if not diffs else
               "differs: " + "; ".join(f"{d['field']} is {d['certificate']} on the certificate but {d['record']} in the typed record" for d in diffs))
        lines_md.append(f"| {name} (`{slug}`) | {n} | {res} |")
    open(os.path.join(ROOT, "docs", "certificates.md"), "w", encoding="utf-8", newline="\n").write("\n".join(lines_md) + "\n")
    nd = [r for r in results if r[3]]
    detail = (f"{len(results)} certificate PDFs read; {len(results) - len(nd)} match; {len(nd)} differ"
              + (" (" + "; ".join(f"{s}: {', '.join(d['field'] for d in diffs)}" for s, _, _, diffs in nd) + ")" if nd else ""))
    append_row("all", "certificate_check", detail, "DIFFERENCES_FOR_A_PERSON" if nd else "ALL_MATCH")
    print(detail)


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return
    if a[0] == "read":
        f = read_fields(a[1])
        print(json.dumps(f, ensure_ascii=False) if "--json" in a else "\n".join(f"{k}: {v}" for k, v in f.items()))
    elif a[0] == "check":
        check()
    elif a[0] == "verify-log":
        good, n, ok = chain_ok()
        print(f"documents log: {n} rows, {ok} links verify; {'OK' if good else 'BROKEN'}")
        raise SystemExit(0 if good else 3)
    else:
        raise SystemExit(f"unknown command {a[0]}")


if __name__ == "__main__":
    main()
