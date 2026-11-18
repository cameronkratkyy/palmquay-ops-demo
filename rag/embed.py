"""Phase 2: semantic search (embeddings) and hybrid search for the Palmquay RAG assistant.

Plain English:
  Embeddings: a small AI model (all-MiniLM-L6-v2) turns each chunk and each question into a list of
  384 numbers that captures meaning. Two texts that mean the same thing land close together even when
  they share no words ("bug-control company" is near "Pest Solutions"). Closeness = cosine similarity.
  Hybrid search: keyword search (BM25) and meaning search each make a ranked list; reciprocal rank
  fusion (RRF) merges them: every chunk gets 1/(60 + its rank) from each list, summed. A chunk that
  ranks well on either list rises; one that ranks well on both rises most.
Runs locally on CPU with onnxruntime (no data leaves the PC). Model files live outside the repo:
  %LOCALAPPDATA%\\jarvis-tools\\models\\all-MiniLM-L6-v2 (override with RAG_MODEL_DIR).
Run (needs numpy, onnxruntime, tokenizers):
  <venv python> -I -X utf8 rag/embed.py "Which bug-control company lied on its paperwork?"
"""
import os, sys, time
from pathlib import Path
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rag import BM25, chunk_files, log_run

MODEL_DIR = Path(os.environ.get("RAG_MODEL_DIR", os.path.expandvars(r"%LOCALAPPDATA%\jarvis-tools\models\all-MiniLM-L6-v2")))


class Embedder:
    def __init__(self):
        self.tok = Tokenizer.from_file(str(MODEL_DIR / "tokenizer.json"))
        self.tok.enable_truncation(256)
        self.tok.enable_padding()
        self.sess = ort.InferenceSession(str(MODEL_DIR / "onnx" / "model.onnx"), providers=["CPUExecutionProvider"])
        self.inputs = {i.name for i in self.sess.get_inputs()}

    def encode(self, texts, batch=32):
        out = []
        for i in range(0, len(texts), batch):
            enc = self.tok.encode_batch(texts[i:i + batch])
            ids = np.array([e.ids for e in enc], dtype=np.int64)
            mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
            feed = {"input_ids": ids, "attention_mask": mask}
            if "token_type_ids" in self.inputs:
                feed["token_type_ids"] = np.zeros_like(ids)
            hidden = self.sess.run(None, feed)[0]                     # (batch, tokens, 384)
            m = mask[..., None].astype(np.float32)
            vec = (hidden * m).sum(1) / np.clip(m.sum(1), 1e-9, None)  # mean pooling over real tokens
            out.append(vec / np.linalg.norm(vec, axis=1, keepdims=True))  # unit length -> dot = cosine
        return np.vstack(out)


class Hybrid:
    def __init__(self):
        self.chunks = chunk_files()
        self.bm25 = BM25(self.chunks)
        self.emb = Embedder()
        t0 = time.perf_counter()
        self.vecs = self.emb.encode([c["text"] for c in self.chunks])
        self.index_ms = round((time.perf_counter() - t0) * 1000)

    def semantic(self, q, k):
        sims = self.vecs @ self.emb.encode([q])[0]
        order = np.argsort(-sims)[:k]
        return [dict(self.chunks[i], score=round(float(sims[i]), 3)) for i in order]

    def search(self, q, k=3, mode="hybrid", pool=20, rrf_k=60):
        if mode == "bm25":
            return self.bm25.search(q, k)
        if mode == "embed":
            return self.semantic(q, k)
        key = lambda c: (c["file"], c["line"])
        fused = {}
        for ranked in (self.bm25.search(q, pool), self.semantic(q, pool)):
            for r, c in enumerate(ranked, 1):
                fused.setdefault(key(c), [c, 0.0])[1] += 1 / (rrf_k + r)
        best = sorted(fused.values(), key=lambda x: -x[1])[:k]
        return [dict(c, score=round(s, 4)) for c, s in best]

    def ask(self, q, k=3, mode="hybrid"):
        t0 = time.perf_counter()
        hits = self.search(q, k, mode)
        ms = round((time.perf_counter() - t0) * 1000, 2)
        log_run({"when": time.strftime("%Y-%m-%d %H:%M:%S"), "question": q, "retriever": mode, "ms": ms,
                 "top": [f"{h['file']}:{h['line']}" for h in hits]})
        return hits, ms


if __name__ == "__main__":
    h = Hybrid()
    q = " ".join(sys.argv[1:]) or "Which bug-control company lied on its paperwork?"
    print(f"{len(h.chunks)} chunks embedded in {h.index_ms} ms")
    for mode in ("bm25", "embed", "hybrid"):
        hits, ms = h.ask(q, 3, mode)
        print(f"\n{mode} ({ms} ms):")
        for x in hits:
            print(f"  [{x['score']}] {x['file']}:{x['line']}  {x['text'][:120]}")
