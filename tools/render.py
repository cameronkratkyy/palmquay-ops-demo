"""Render the Phase 3b pictures with the headless browser already on this PC (Edge, else Chrome). No install, no network.

    python -I -X utf8 tools/render.py              everything below
    python -I -X utf8 tools/render.py dashboard    dashboard/screenshot-<tab>.png, one per tab (plus the replay at its last row)
    python -I -X utf8 tools/render.py diagram      docs/diagram.png (2x, for LinkedIn Featured) + docs/diagram.pdf (1 page)
    python -I -X utf8 tools/render.py explainer    docs/explainer.html + docs/explainer.pdf, from docs/explainer.md

Each browser run gets its own throwaway profile, so it never touches an open browser or its sign-ins. Fake data only.
Prints what it made (size, pages, pixels); exit 1 if anything is missing.
"""
import html
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe"]
TABS = ["overview", "byhand", "onboarding", "owners", "buying", "checks", "audit", "map"]


def browser():
    b = next((x for x in BROWSERS if os.path.exists(x)), None)
    if not b:
        raise SystemExit("FAIL - no Edge or Chrome found")
    return b


def url(p, frag=""):
    return "file:///" + os.path.abspath(p).replace("\\", "/") + frag


def headless(args):
    with tempfile.TemporaryDirectory() as prof:
        subprocess.run([browser(), "--headless=new", "--disable-gpu", "--no-first-run", "--hide-scrollbars", f"--user-data-dir={prof}",
                        "--virtual-time-budget=4000"] + args, capture_output=True, timeout=180)


def png_size(p):
    b = open(p, "rb").read(32)
    return int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big")


def pdf_pages(p):
    return len(re.findall(rb"/Type\s*/Page(?!s)", open(p, "rb").read()))


def report(p):
    if not os.path.exists(p):
        print(f"FAIL - {os.path.relpath(p, ROOT)} not made")
        return False
    kb = os.path.getsize(p) // 1024
    extra = f"{png_size(p)[0]} x {png_size(p)[1]} px" if p.endswith(".png") else f"{pdf_pages(p)} page(s)" if p.endswith(".pdf") else ""
    print(f"made {os.path.relpath(p, ROOT)}: {kb} KB {extra}")
    return True


def dashboard():
    page = os.path.join(ROOT, "dashboard", "index.html")
    ok = True
    shots = [(t, f"#tab={t}") for t in TABS] + [("replay-end", "#replay=999")]
    for name, frag in shots:
        out = os.path.join(ROOT, "dashboard", f"screenshot-{name}.png")
        if os.path.exists(out):
            os.remove(out)
        headless([f"--screenshot={out}", "--window-size=1440,1600", "--force-device-scale-factor=1", url(page, frag)])
        ok &= report(out)
    return ok


def diagram():
    src = os.path.join(ROOT, "docs", "diagram.html")
    png, pdf = src[:-5] + ".png", src[:-5] + ".pdf"
    for f in (png, pdf):
        if os.path.exists(f):
            os.remove(f)
    headless([f"--screenshot={png}", "--window-size=1600,1000", "--force-device-scale-factor=2", url(src)])
    headless([f"--print-to-pdf={pdf}", "--no-pdf-header-footer", url(src)])
    return report(png) & report(pdf)


# ------------------------------------------------- a small Markdown reader for the explainer -------------------------------------------------
def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    return re.sub(r"(?<![*\w])\*([^*]+)\*(?![*\w])", r"<i>\1</i>", t)


def md_to_html(md):
    out, lines, i = [], md.replace("\r", "").split("\n"), 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = re.match(r"^(#{1,4}) (.*)$", line)
        if m:
            n = len(m.group(1))
            out.append(f"<h{n}>{inline(m.group(2))}</h{n}>")
            i += 1
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            body = [r for r in rows[2:]]
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in rows[0]) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in body) + "</tbody></table>")
        elif re.match(r"^(\d+\.|-) ", line):
            tag = "ol" if line[0].isdigit() else "ul"
            items = []
            while i < len(lines) and re.match(r"^(\d+\.|-) ", lines[i]):
                items.append(re.sub(r"^(\d+\.|-) ", "", lines[i]))
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
        elif line.startswith("> "):
            quote = []
            while i < len(lines) and lines[i].startswith("> "):
                quote.append(lines[i][2:])
                i += 1
            out.append(f"<blockquote>{inline(' '.join(quote))}</blockquote>")
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||> |\d+\. |- )", lines[i]):
                para.append(lines[i])
                i += 1
            out.append(f"<p>{inline(' '.join(para))}</p>")
    return "\n".join(out)


EXPLAINER_CSS = """
@page{size:Letter;margin:0.3in 0.42in}*{box-sizing:border-box}
body{font:8.5pt/1.28 "Segoe UI",system-ui,sans-serif;color:#0b0b0b;margin:0}
h1{font-size:15pt;margin:0 0 2px}h2{font-size:10pt;margin:6px 0 2px;color:#1d5a85;border-bottom:1px solid #e2e1dc;padding-bottom:1px}
h3{font-size:9.5pt;margin:6px 0 2px}p{margin:0 0 4px}ul,ol{margin:0 0 5px;padding-left:16px}li{margin:0 0 1px}
table{border-collapse:collapse;width:100%;margin:0 0 5px}th,td{border-bottom:1px solid #e2e1dc;padding:2px 5px;text-align:left;vertical-align:top}
th{font-size:8.2pt;color:#52514e;background:#f1f0ec}td:first-child{white-space:nowrap}code{font:8.4pt Consolas,monospace;background:#f1f0ec;padding:0 3px;border-radius:3px}
blockquote{margin:4px 0 6px;padding:5px 9px;border-left:3px solid #1d5a85;background:#f6f6f3}
"""


def explainer():
    md = os.path.join(ROOT, "docs", "explainer.md")
    if not os.path.exists(md):
        print("FAIL - docs/explainer.md not written yet")
        return False
    out_html, pdf = md[:-3] + ".html", md[:-3] + ".pdf"
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>How the Palmquay demo works</title>'
            f"<style>{EXPLAINER_CSS}</style></head><body>{md_to_html(open(md, encoding='utf-8').read())}</body></html>")
    open(out_html, "w", encoding="utf-8").write(page)
    if os.path.exists(pdf):
        os.remove(pdf)
    headless([f"--print-to-pdf={pdf}", "--no-pdf-header-footer", url(out_html)])
    return report(out_html) & report(pdf)


if __name__ == "__main__":
    what = sys.argv[1:] or ["dashboard", "diagram", "explainer"]
    ok = True
    for w in what:
        ok &= {"dashboard": dashboard, "diagram": diagram, "explainer": explainer}[w]()
    sys.exit(0 if ok else 1)
