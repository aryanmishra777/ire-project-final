"""Command line: python -m rewrite_eval <step>

  prepare    download LitSearch, build the BM25 index and the dense embeddings
  rewrite    generate (or reuse cached) LLM rewrites for all queries and variants
  retrieve   run every retriever × variant cell and score it per query
  analyze    tables, significance tests, figures, cost frontier, failure analysis
  all        the four steps in order
"""
import argparse

from .config import LLM_PROVIDER, VARIANTS


def main() -> None:
    p = argparse.ArgumentParser(prog="rewrite_eval")
    p.add_argument("step", choices=["prepare", "rewrite", "retrieve", "analyze", "all"])
    p.add_argument("--provider", default=LLM_PROVIDER, choices=["groq", "ollama"])
    p.add_argument("--workers", type=int, default=4, help="concurrent LLM calls")
    p.add_argument("--limit", type=int, default=None,
                   help="only the first N queries (cross-checks and smoke tests)")
    p.add_argument("--tag", default=None, help="name for this run's result files")
    args = p.parse_args()
    tag = args.tag or ("main" if args.provider == LLM_PROVIDER and not args.limit
                       else f"{args.provider}_{args.limit or 'all'}")

    from .data import load_queries
    queries = load_queries()
    if args.limit:
        queries = queries.head(args.limit)

    if args.step in ("prepare", "all"):
        from .run import build_indexes
        build_indexes()
    if args.step in ("rewrite", "all"):
        from .rewrite import generate
        generate(list(zip(queries["qid"], queries["query"])),
                 [v for v in VARIANTS if v != "raw"], provider=args.provider,
                 workers=args.workers)
    if args.step in ("retrieve", "all"):
        from .run import run_cells
        run_cells(provider=args.provider, qids=list(queries["qid"]), tag=tag)
    if args.step in ("analyze", "all"):
        from .analyze import analyze
        analyze(tag)


if __name__ == "__main__":
    main()
