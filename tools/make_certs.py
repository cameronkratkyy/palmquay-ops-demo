"""Phase 3e input maker (run once, before the reader existed; its outputs are then locked in tests/frozen-3e.txt).
Turns each contractor's typed insurance record (vendors/<slug>/documents/coi.md) into the certificate itself: a real one-page PDF
(compressed content stream, standard Helvetica, like most text PDFs), marked SAMPLE. Fictional company, insurer, and policies.
It does not copy any industry form's layout.

One difference is planted on purpose: Fernhollow's certificate shows policy number DEMO-GL-0040, while its typed record says DEMO-GL-0004
(a transposed digit, the kind of keying error a person makes). The certificate is the source of truth; the record is the copy.

    python -I -X utf8 tools/make_certs.py
"""
import glob
import os
import re
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLANT = {"fernhollow-grounds": {"Policy number": "DEMO-GL-0040"}}
FIELDS = ["Insured", "Certificate holder", "Additional insured", "Insurer", "Policy number", "General liability per occurrence",
          "General liability aggregate", "Auto liability", "Workers' comp", "Umbrella", "Policy start", "Policy end"]


def kv(t):
    return {m.group(1): m.group(2).strip() for m in re.finditer(r"^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$", t, re.M)}


def esc(s):
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").encode("cp1252")


def pdf(lines_out, path):
    """lines_out: [(font 'F1'|'F2', size, x, y, text)] plus boxes drawn in the content stream"""
    c = [b"0.85 0.85 0.85 RG 1 w 48 300 516 400 re S", b"0.93 0.93 0.93 RG 48 640 m 564 640 l S"]
    c.append(b"q 0.90 g BT /F2 64 Tf 0.766 0.643 -0.643 0.766 150 260 Tm (SAMPLE) Tj ET Q")
    for font, size, x, y, t in lines_out:
        c.append(b"BT /" + font.encode() + b" " + str(size).encode() + b" Tf " + f"{x} {y}".encode() + b" Td (" + esc(t) + b") Tj ET")
    stream = zlib.compress(b"\n".join(c))
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
            b"<< /Length " + str(len(stream)).encode() + b" /Filter /FlateDecode >>\nstream\n" + stream + b"\nendstream",
            b"<< /Title (Certificate of liability insurance, sample) /Producer (Palmquay demo, tools/make_certs.py) >>"]
    out, offs = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"), []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    x = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode() + b"".join(f"{o:010d} 00000 n \n".encode() for o in offs)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R /Info 7 0 R >>\nstartxref\n{x}\n%%EOF\n".encode()
    open(path, "wb").write(bytes(out))


def main():
    made = 0
    for md in sorted(glob.glob(os.path.join(ROOT, "vendors", "*", "documents", "coi.md"))):
        slug = md.split(os.sep)[-3]
        f = kv(open(md, encoding="utf-8").read())
        f.update(PLANT.get(slug, {}))
        lines = [("F2", 16, 56, 740, "CERTIFICATE OF LIABILITY INSURANCE"),
                 ("F1", 9, 56, 724, "Sample document for a demo. Fictional company, insurer, and policy; not proof of any real coverage."),
                 ("F1", 9, 56, 652, "This certificate is issued as a matter of information only and confers no rights upon the certificate holder.")]
        y = 616
        for name in FIELDS:
            lines.append(("F2", 10, 64, y, name + ":"))
            lines.append(("F1", 10, 250, y, f[name]))
            y -= 24
        lines.append(("F1", 8, 56, 286, "Issued by Demo Mutual Insurance Co. (fictional). Questions go to the insurer, not to Palmquay Properties."))
        pdf(lines, os.path.join(os.path.dirname(md), "coi.pdf"))
        made += 1
    print(f"made {made} certificate PDFs; planted: {PLANT}")


if __name__ == "__main__":
    main()
