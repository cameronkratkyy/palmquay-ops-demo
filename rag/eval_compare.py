"""Compare keyword (bm25), meaning (embed), and hybrid retrieval on the same 20 questions.
Pass rule (set before this run, 11/18): hybrid keeps exact recall@3 >= 0.80 AND raises paraphrase
recall@3 above keyword search's 0.50. Prints recall@1, recall@3, MRR, and latency per mode.
Run: <venv python> -I -X utf8 rag/eval_compare.py
"""
import json, statistics, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed import Hybrid

ROOT = Path(__file__).resolve().parent.parent
qs = json.loads((ROOT / "rag" / "eval_questions.json").read_text(encoding="utf-8"))["questions"]
h = Hybrid()
print(f"chunks: {len(h.chunks)} | embedding the corpus took {h.index_ms} ms | questions: {len(qs)}")
res = {}
for mode in ("bm25", "embed", "hybrid"):
    ranks, times = {"exact": [], "paraphrase": []}, []
    for it in qs:
        hits, ms = h.ask(it["q"], 3, mode)
        times.append(ms)
        files = [x["file"] for x in hits]
        r = files.index(it["file"]) + 1 if it["file"] in files else 0
        ranks[it["kind"]].append(r)
        if it["kind"] == "paraphrase":
            print(f"  {mode:6} {'OK  ' if r else 'MISS'} {it['q']} -> {files[0] if files else '-'}")
    res[mode] = {k: {"recall@1": round(sum(x == 1 for x in v) / len(v), 2), "recall@3": round(sum(x > 0 for x in v) / len(v), 2),
                     "MRR": round(sum(1 / x for x in v if x) / len(v), 2)} for k, v in ranks.items()}
    res[mode]["median_ms"] = statistics.median(times)
    print(f"{mode:6}: exact {res[mode]['exact']} | paraphrase {res[mode]['paraphrase']} | median {res[mode]['median_ms']} ms")
ok = res["hybrid"]["exact"]["recall@3"] >= 0.80 and res["hybrid"]["paraphrase"]["recall@3"] > res["bm25"]["paraphrase"]["recall@3"]
print("RESULT:", "PASS" if ok else "FAIL", f"(hybrid exact {res['hybrid']['exact']['recall@3']}, hybrid paraphrase {res['hybrid']['paraphrase']['recall@3']} vs bm25 {res['bm25']['paraphrase']['recall@3']})")
(ROOT / "rag" / "eval_results.json").write_text(json.dumps(res, indent=2), encoding="utf-8")
sys.exit(0 if ok else 1)
