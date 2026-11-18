"""Retrieval eval for the Palmquay RAG assistant.

Plain English: we ask every question in eval_questions.json and check whether the file that holds
the answer comes back in the top results.
  recall@1 = share of questions where the right file is the very first result
  recall@3 = share where it's anywhere in the top 3 (what the answer step would get to read)
  MRR      = mean reciprocal rank: 1 if first, 1/2 if second, 1/3 if third, 0 if missing; averaged
Pass rule (set before the first run, 11/18): exact questions recall@3 >= 0.80. Paraphrase questions
are reported separately: they test meaning, which keyword search can't see (phase 2, embeddings).
Run: python -I -X utf8 rag/eval_retrieval.py
"""
import json, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rag import BM25, chunk_files, ask

ROOT = Path(__file__).resolve().parent.parent
qs = json.loads((ROOT / "rag" / "eval_questions.json").read_text(encoding="utf-8"))["questions"]
idx = BM25(chunk_files())
rows, times = [], []
for item in qs:
    hits, ms = ask(idx, item["q"], k=3)
    times.append(ms)
    files = [h["file"] for h in hits]
    rank = files.index(item["file"]) + 1 if item["file"] in files else 0
    rows.append((item, rank))
    print(f"{'OK  ' if rank else 'MISS'} rank {rank or '-'} | {item['kind']:10} | {item['q']}  -> {files[:3]}")


def score(kind):
    r = [rank for it, rank in rows if it["kind"] == kind]
    if not r:
        return None
    return {"n": len(r), "recall@1": round(sum(x == 1 for x in r) / len(r), 2),
            "recall@3": round(sum(x > 0 for x in r) / len(r), 2),
            "MRR": round(sum(1 / x for x in r if x) / len(r), 2)}


exact, para = score("exact"), score("paraphrase")
print(f"\nchunks indexed: {len(idx.chunks)} | questions: {len(rows)}")
print("exact:", exact)
print("paraphrase:", para)
print(f"latency per search: median {statistics.median(times)} ms, max {max(times)} ms")
ok = exact and exact["n"] >= 10 and exact["recall@3"] >= 0.80
print("RESULT:", "PASS" if ok else "FAIL", f"(exact recall@3 {exact['recall@3'] if exact else 0} vs 0.80 needed, n={exact['n'] if exact else 0})")
sys.exit(0 if ok else 1)
