"""Does re-ranking help? Same 20 questions as eval_compare.py, three modes side by side.
Pass rule (set before the first run, 11/18): rerank keeps exact recall@3 >= 0.90 AND paraphrase recall@3 is no
worse than hybrid's. It counts as a win only if paraphrase recall@1 or MRR goes up, or the known miss
("Which bug-control company lied on its paperwork?") gets fixed. Prints latency too: re-ranking costs time.
Run: <venv python> -I -X utf8 rag/eval_rerank.py
"""
import json, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from rerank import RerankedHybrid

ROOT = Path(__file__).resolve().parent.parent
qs = json.loads((ROOT / "rag" / "eval_questions.json").read_text(encoding="utf-8"))["questions"]
h = RerankedHybrid()
res, misses = {}, {}
for mode in ("bm25", "hybrid", "rerank"):
    ranks, times = {"exact": [], "paraphrase": []}, []
    for it in qs:
        hits, ms = h.ask(it["q"], 3, mode)
        times.append(ms)
        files = [x["file"] for x in hits]
        r = files.index(it["file"]) + 1 if it["file"] in files else 0
        ranks[it["kind"]].append(r)
        if not r:
            misses.setdefault(mode, []).append(it["q"])
    res[mode] = {k: {"recall@1": round(sum(x == 1 for x in v) / len(v), 2), "recall@3": round(sum(x > 0 for x in v) / len(v), 2),
                     "MRR": round(sum(1 / x for x in v if x) / len(v), 2)} for k, v in ranks.items()}
    res[mode]["median_ms"] = statistics.median(times)
    print(f"{mode:6}: exact {res[mode]['exact']} | paraphrase {res[mode]['paraphrase']} | median {res[mode]['median_ms']} ms")
for mode, qs_missed in misses.items():
    print(f"  {mode} missed: {qs_missed}")
R, H = res["rerank"], res["hybrid"]
ok = R["exact"]["recall@3"] >= 0.90 and R["paraphrase"]["recall@3"] >= H["paraphrase"]["recall@3"]
known = "Which bug-control company lied on its paperwork?"
win = (R["paraphrase"]["recall@1"] > H["paraphrase"]["recall@1"] or R["paraphrase"]["MRR"] > H["paraphrase"]["MRR"]
       or (known in misses.get("hybrid", []) and known not in misses.get("rerank", [])))
print("RESULT:", "PASS" if ok else "FAIL", "| win:", "yes" if win else "no",
      f"(rerank exact r@3 {R['exact']['recall@3']}, paraphrase r@3 {R['paraphrase']['recall@3']} vs hybrid {H['paraphrase']['recall@3']})")
(ROOT / "rag" / "eval_rerank_results.json").write_text(json.dumps({"results": res, "misses": misses, "pass": ok, "win": win}, indent=2), encoding="utf-8")
sys.exit(0 if ok else 1)
