"""BM25 and dense retrievers over the LitSearch corpus, plus reciprocal rank fusion.

Both return, per query, the top-K corpus ids in rank order. Indexes and embeddings are built
once and cached under data/.
"""
from __future__ import annotations

import numpy as np

from .config import (DATA_DIR, DENSE_BATCH, DENSE_DOC_PREFIX, DENSE_MODEL,
                     DENSE_QUERY_PREFIX, RRF_K, TOP_K)

BM25_DIR = DATA_DIR / "bm25_index"


class BM25Retriever:
    """Lucene-style BM25 (k1=1.5, b=0.75) with English stemming and stopwords, via bm25s."""

    def __init__(self, corpus_ids: np.ndarray, texts: list[str] | None = None):
        import bm25s
        import Stemmer

        self._bm25s = bm25s
        self._stemmer = Stemmer.Stemmer("english")
        self.corpus_ids = corpus_ids
        if BM25_DIR.exists():
            self.index = bm25s.BM25.load(str(BM25_DIR))
        else:
            if texts is None:
                raise ValueError("no cached BM25 index; pass corpus texts to build one")
            tokens = bm25s.tokenize(texts, stopwords="en", stemmer=self._stemmer)
            self.index = bm25s.BM25()
            self.index.index(tokens)
            self.index.save(str(BM25_DIR))

    def search(self, queries: list[str], k: int = TOP_K) -> list[list[int]]:
        out = []
        for q in queries:  # one at a time: an all-stopword query must not sink the batch
            toks = self._bm25s.tokenize([q], stopwords="en", stemmer=self._stemmer,
                                        show_progress=False)
            if not toks.vocab:
                out.append([])
                continue
            idx, _ = self.index.retrieve(toks, k=k, show_progress=False)
            out.append([int(self.corpus_ids[i]) for i in idx[0]])
        return out


class DenseRetriever:
    """Exact cosine search over cached, L2-normalised embeddings (the corpus is small enough
    that approximate search is unnecessary)."""

    def __init__(self, corpus_ids: np.ndarray, texts: list[str] | None = None):
        import torch
        from sentence_transformers import SentenceTransformer

        self.corpus_ids = corpus_ids
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(DENSE_MODEL, device=device)
        path = DATA_DIR / f"emb_{DENSE_MODEL.replace('/', '__')}.npy"
        if path.exists():
            self.emb = np.load(path).astype(np.float32)
        else:
            if texts is None:
                raise ValueError("no cached embeddings; pass corpus texts to build them")
            self.emb = self.model.encode(
                [DENSE_DOC_PREFIX + t for t in texts], batch_size=DENSE_BATCH,
                normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=True,
            ).astype(np.float32)
            np.save(path, self.emb.astype(np.float16))

    def encode_queries(self, queries: list[str]) -> np.ndarray:
        return self.model.encode([DENSE_QUERY_PREFIX + q for q in queries],
                                 batch_size=DENSE_BATCH, normalize_embeddings=True,
                                 convert_to_numpy=True)

    def encode_docs(self, texts: list[str]) -> np.ndarray:
        return self.model.encode([DENSE_DOC_PREFIX + t for t in texts], batch_size=DENSE_BATCH,
                                 normalize_embeddings=True, convert_to_numpy=True)

    def search_vectors(self, vecs: np.ndarray, k: int = TOP_K) -> list[list[int]]:
        sims = vecs @ self.emb.T
        top = np.argpartition(-sims, k, axis=1)[:, :k]
        out = []
        for row, cand in zip(sims, top):
            order = cand[np.argsort(-row[cand])]
            out.append([int(self.corpus_ids[i]) for i in order])
        return out

    def search(self, queries: list[str], k: int = TOP_K) -> list[list[int]]:
        return self.search_vectors(self.encode_queries(queries), k)


def rrf(rankings: list[list[int]], k: int = TOP_K, c: int = RRF_K) -> list[int]:
    """Reciprocal rank fusion: score(d) = sum over lists of 1 / (c + rank)."""
    scores: dict[int, float] = {}
    for ranking in rankings:
        for r, doc in enumerate(ranking, start=1):
            scores[doc] = scores.get(doc, 0.0) + 1.0 / (c + r)
    return [d for d, _ in sorted(scores.items(), key=lambda x: -x[1])[:k]]
