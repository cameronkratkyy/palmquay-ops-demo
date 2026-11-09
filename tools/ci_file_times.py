"""CI helper: set every tracked file's modified time to its last commit time.
A fresh clone gives every file the same checkout time, which says nothing about order. Checks such as "the PDF was rendered after its
source" then compare commit times: an output committed in the same commit as its source, or later, passes; one committed before a
newer source change fails, as it should.

    python -I -X utf8 tools/ci_file_times.py        (run from the repo root, after a full-history checkout)
"""
import os
import subprocess

out = subprocess.run(["git", "log", "--format=@%ct", "--name-only", "--no-renames"], capture_output=True, text=True, check=True).stdout
seen, t = set(), None
for line in out.splitlines():
    if line.startswith("@"):
        t = int(line[1:])
    elif line and line not in seen:
        seen.add(line)  # git log runs newest first, so the first time a path appears is its last commit
        if os.path.exists(line):
            os.utime(line, (t, t))
print(f"set {len(seen)} files to their last commit time")
