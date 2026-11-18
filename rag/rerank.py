"""Phase 3: re-ranking. Hybrid search finds 20 candidates fast; a cross-encoder then reads the question and
each candidate together and re-orders them. Slower per item, much sharper.

Plain English: embeddings compare two summaries made separately (question alone, chunk alone). A cross-encoder
(ms-marco-MiniLM-L6-v2, trained on real search questions and the passages that answered them) reads both at once,
so it can see that "bug-control company" and "pest" and "lied" and "false certifications" belong together.
Runs locally on CPU with onnxruntime. Model lives outside the repo:
  %LOCALAPPDATA%\\jarvis-tools\\models\\ms-marco-MiniLM-L6-v2 (override with RAG_RERANK_DIR).
Run: <venv python> -I -X utf8 rag/rerank.py "Which bug-control company lied on its paperwork?"
"""
import os, sys
from pathlib import Path
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from embed import Hybrid

RERANK_DIR = Path(os.environ.get("RAG_RERANK_DIR", os.path.expandvars(r"%LOCALAPPDATA%\jarvis-tools\models\ms-marco-MiniLM-L6-v2")))


class Reranker:
    def __init__(self):
        self.tok = Tokenizer.from_file(str(RERANK_DIR / "tokenizer.json"))
        self.tok.enable_truncation(512)
        self.tok.enable_padding()
        self.sess = ort.InferenceSession(str(RERANK_DIR / "onnx" / "model.onnx"), providers=["CPUExecutionProvider"])
        self.inputs = {i.name for i in self.sess.get_inputs()}

    def score(self, question, texts):
        enc = self.tok.encode_batch([(question, t) for t in texts])      # each pair read together: [CLS] q [SEP] chunk [SEP]
        feed = {"input_ids": np.array([e.ids for e in enc], dtype=np.int64),
                "attention_mask": np.array([e.attention_mask for e in enc], dtype=np.int64)}
        if "token_type_ids" in self.inputs:
            feed["token_type_ids"] = np.array([e.type_ids for e in enc], dtype=np.int64)
        return self.sess.run(None, feed)[0][:, 0]                         # one relevance score per pair


class RerankedHybrid(Hybrid):
    def __init__(self):
        super().__init__()
        self.rr = Reranker()

    def search(self, q, k=3, mode="rerank", pool=20, rrf_k=60):
        if mode != "rerank":
            return super().search(q, k, mode, pool, rrf_k)
        cands = super().search(q, pool, "hybrid", pool, rrf_k)
        scores = self.rr.score(q, [c["text"] for c in cands])
        order = np.argsort(-scores)[:k]
        return [dict(cands[i], score=round(float(scores[i]), 3)) for i in order]


if __name__ == "__main__":
    h = RerankedHybrid()
    q = " ".join(sys.argv[1:]) or "Which bug-control company lied on its paperwork?"
    for mode in ("hybrid", "rerank"):
        hits, ms = h.ask(q, 3, mode)
        print(f"\n{mode} ({ms} ms):")
        for x in hits:
            print(f"  [{x['score']}] {x['file']}:{x['line']}  {x['text'][:110]}")
