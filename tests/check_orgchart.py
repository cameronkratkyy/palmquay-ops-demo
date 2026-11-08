"""Org chart + wording check for the dashboard (written before the change, 11/8/2026).
Asked for: say "sample" not "fake" on the page; show who works at the company, with blank (no-face) profiles in different colors.
Run: python -I -X utf8 tests/check_orgchart.py   (reads dashboard/index.html; prints every count; exit 1 on any FAIL)"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
page = open(os.path.join(ROOT, "dashboard", "index.html"), encoding="utf-8").read()
people_md = open(os.path.join(ROOT, "company", "people.md"), encoding="utf-8").read()
request_md = open(os.path.join(ROOT, "projects", "unit-4b", "request.md"), encoding="utf-8").read()
fails = 0


def check(name, ok, detail):
    global fails
    fails += not ok
    print(("PASS" if ok else "FAIL"), "-", name, "|", detail)


def visible(html):
    # <pre> blocks are the sample records quoted word for word (other checks lock that text), so they're left out
    html = re.sub(r"<script.*?</script>|<style.*?</style>|<pre.*?</pre>", " ", html, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


# 1. wording: no "fake" anywhere a viewer can read; the header says fictional + sample
vis = visible(page)
fake_hits = re.findall(r".{0,40}\bfake\b.{0,40}", vis, re.I)
stamp = re.search(r'<div class="stamp">(.*?)</div>', page, re.S)
stamp_t = re.sub(r"<[^>]+>", "", stamp.group(1)) if stamp else ""
check("no 'fake' in text the dashboard writes (quoted records excluded)", not fake_hits, f"{len(fake_hits)} hits {fake_hits[:3]}")
check("header says fictional + sample records", bool(re.search(r"fictional", stamp_t, re.I) and re.search(r"sample records", stamp_t, re.I)),
      f"stamp: {stamp_t.strip()[:140]!r}")

# 2. org chart: every named person in the records, with title, blank profile, own color
names = re.findall(r"^\|\s*[^|]+\|\s*([A-Z][a-z]+ [A-Z][a-z]+)\s*\|", people_md, re.M)
req = re.search(r"Requested by:\s*([A-Z][a-z]+ [A-Z][a-z]+)", request_md)
want = names + ([req.group(1)] if req else [])
org = re.search(r'<div class="org"[^>]*data-org[^>]*>(.*?)<!-- ORG END -->', page, re.S)
org_html = org.group(1) if org else ""
# the builder puts a line break after every </div>, so allow whitespace before the end marker
cards = re.findall(r'<div class="person" data-person="([^"]+)" style="--pc:(#[0-9a-fA-F]{6})">(.*?)</div>\s*<!-- /person -->', org_html, re.S)
got = {n: (c, body) for n, c, body in cards}
missing = [n for n in want if n not in got]
check("org chart lists everyone in the records", len(want) >= 5 and not missing and len(cards) == len(want),
      f"want {len(want)} {want}; cards {len(cards)}; missing {missing}")
colors = [c.lower() for c, _ in got.values()]
check("each person has their own color", len(colors) == len(set(colors)) and len(colors) >= 5, f"{len(set(colors))} distinct of {len(colors)}: {colors}")
no_face = all("<svg" in b and "<img" not in b for _, b in got.values()) and "<img" not in org_html
check("blank profiles (an icon, no photos)", no_face and bool(got), f"{sum('<svg' in b for _, b in got.values())} icons, {org_html.count('<img')} images")
titled = [n for n, (_, b) in got.items() if re.search(r'class="title">[^<]{3,}<', b) and re.search(r'class="does">[^<]{8,}<', b)]
check("each card has a job title and what they decide", len(titled) == len(got) and got, f"{len(titled)} of {len(got)}")
on_overview = bool(re.search(r'<section data-tab="overview"[^>]*>\s*(?:<h2>[^<]*</h2>\s*)?(?:<p[^>]*>.*?</p>\s*)?<div class="org"', page, re.S))
check("org chart is at the top of the Overview tab", on_overview, f"found at top: {on_overview}")

# 3. the same color follows each person into the 'Waiting on people' table
rows = re.findall(r'<tr data-w="[^"]+" data-owner="[^"]*"><td class="nowrap">[^<]*</td>\s*<td>(.*?)</td>', page, re.S)
dots, wrong = 0, []
for cell in rows:
    m = re.search(r'<span class="dot" style="background:(#[0-9a-fA-F]{6})"></span>\s*([A-Z][a-z]+ [A-Z][a-z]+)', cell)
    if m:
        dots += 1
        if m.group(2) not in got or got[m.group(2)][0].lower() != m.group(1).lower():
            wrong.append(m.group(2))
check("waiting-table names carry the same color dot", rows and dots == len(rows) and not wrong, f"{dots} dots on {len(rows)} rows; wrong color {wrong}")

print(f"RESULT: {8 - fails} of 8 checks PASS")
sys.exit(1 if fails else 0)
