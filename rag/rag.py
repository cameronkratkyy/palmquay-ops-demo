"""Palmquay RAG assistant, retrieval step (phase 1: keyword search with BM25).

What this does, in plain English:
  1. Chunking: splits Palmquay's documents into small pieces (one table row or one paragraph each),
     and puts the document's title in front of every piece so a row like "| Coralline Haulage | ... |"
     still says which list it came from.
  2. Indexing: counts the words in every piece (BM25 needs word counts, piece lengths, and how rare
     each word is across all pieces).
  3. Retrieval: scores every piece against a question with BM25 (rare shared words count most,
     long pieces don't win just for being long) and returns the top k with a citation (file + line).
  4. Monitoring: logs how long each search took (milliseconds) to rag/runs.jsonl.

Run:  python -I -X utf8 rag/rag.py "Who approves work over $10,000?"
Stdlib only: no installs. Phase 2 adds embeddings (meaning search) and re-ranking.
"""
import json, math, re, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ["company/*.md", "docs/certificates.md", "docs/explainer.md", "controls/screen.md"]
STOP = set("a an and are as at be by did do does for from has have how i in is it its of on or our "
           "that the their this to was we what when where which who why will with you your".split())
K1, B = 1.5, 0.75  # standard BM25 settings: K1 = how fast repeat words stop adding score, B = length penalty


def words(text):
    return [w for w in re.findall(r"[a-z0-9$]+(?:[.,][0-9]+)*", text.lower()) if w not in STOP]


def chunk_files():
    chunks = []
    for pattern in SOURCES:
        for path in sorted(ROOT.glob(pattern)):
            lines = path.read_text(encoding="utf-8").splitlines()
            title = next((l.lstrip("# ").strip() for l in lines if l.startswith("#")), path.name)
            header, para, start = "", [], 0
            for i, line in enumerate(lines, 1):
                s = line.strip()
                if s.startswith("|") and not set(s) <= set("|-: "):
                    if not header:
                        header = s  # the table's column names travel with each row
                        continue
                    chunks.append({"file": path.relative_to(ROOT).as_posix(), "line": i,
                                   "text": f"{title} | {header} {s}"})
                elif s and not s.startswith("|"):
                    if not para:
                        start = i
                    para.append(s)
                    if s.startswith("#"):
                        header = ""
                if (not s or i == len(lines)) and para:
                    chunks.append({"file": path.relative_to(ROOT).as_posix(), "line": start,
                                   "text": f"{title} | {' '.join(para)}"})
                    para = []
    return chunks


class BM25:
    def __init__(self, chunks):
        self.chunks = chunks
        self.toks = [words(c["text"]) for c in chunks]
        self.avg = sum(map(len, self.toks)) / max(1, len(self.toks))
        df = {}
        for t in self.toks:
            for w in set(t):
                df[w] = df.get(w, 0) + 1
        n = len(self.toks)
        self.idf = {w: math.log(1 + (n - d + 0.5) / (d + 0.5)) for w, d in df.items()}

    def search(self, question, k=3):
        q = words(question)
        scores = []
        for i, t in enumerate(self.toks):
            tf, s = {}, 0.0
            for w in t:
                tf[w] = tf.get(w, 0) + 1
            for w in q:
                if w in tf:
                    f = tf[w]
                    s += self.idf[w] * f * (K1 + 1) / (f + K1 * (1 - B + B * len(t) / self.avg))
            scores.append((s, i))
        scores.sort(reverse=True)
        return [dict(self.chunks[i], score=round(s, 3)) for s, i in scores[:k] if s > 0]


def log_run(record):
    with open(ROOT / "rag" / "runs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def ask(index, question, k=3):
    t0 = time.perf_counter()
    hits = index.search(question, k)
    ms = round((time.perf_counter() - t0) * 1000, 2)
    log_run({"when": time.strftime("%Y-%m-%d %H:%M:%S"), "question": question, "retriever": "bm25",
             "ms": ms, "top": [f"{h['file']}:{h['line']}" for h in hits]})
    return hits, ms


if __name__ == "__main__":
    idx = BM25(chunk_files())
    hits, ms = ask(idx, " ".join(sys.argv[1:]) or "Who approves work over $10,000?")
    print(f"{len(idx.chunks)} chunks indexed; search took {ms} ms")
    for h in hits:
        print(f"[{h['score']}] {h['file']}:{h['line']}  {h['text'][:160]}")
