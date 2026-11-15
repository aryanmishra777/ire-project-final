"""Load LitSearch once from the Hugging Face hub and cache it locally as parquet.

Only titles and abstracts are indexed, as in LitSearch's main results (Table 3).
"""
import pandas as pd
from datasets import load_dataset

from .config import DATA_DIR, DATASET

QUERIES_PATH = DATA_DIR / "litsearch_queries.parquet"
CORPUS_PATH = DATA_DIR / "litsearch_corpus.parquet"


def _download() -> None:
    q = load_dataset(DATASET, "query", split="full").to_pandas()
    q.insert(0, "qid", [f"q{i:03d}" for i in range(len(q))])
    q["corpusids"] = q["corpusids"].apply(lambda ids: [int(x) for x in ids])
    q.to_parquet(QUERIES_PATH, index=False)

    c = load_dataset(DATASET, "corpus_clean", split="full",
                     columns=["corpusid", "title", "abstract"]).to_pandas()
    c["title"] = c["title"].fillna("").str.strip()
    c["abstract"] = c["abstract"].fillna("").str.strip()
    c.to_parquet(CORPUS_PATH, index=False)


def load_queries() -> pd.DataFrame:
    """597 queries: qid, query, corpusids (gold), specificity, quality, query_set."""
    if not QUERIES_PATH.exists():
        _download()
    return pd.read_parquet(QUERIES_PATH)


def load_corpus() -> pd.DataFrame:
    """64,183 papers: corpusid, title, abstract."""
    if not CORPUS_PATH.exists():
        _download()
    return pd.read_parquet(CORPUS_PATH)


def doc_texts(corpus: pd.DataFrame) -> list[str]:
    return [f"{t}. {a}".strip(". ") for t, a in zip(corpus["title"], corpus["abstract"])]
