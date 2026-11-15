"""Run each participant's question through the literature-review tool twice:
'on' (the tool's LLM query understanding rewrites the question) and 'off' (bypassed: the raw
question goes straight to retrieval). Everything else is identical.

Run with the TOOL's own interpreter, since it imports the tool's code:
  "<tool>/venv/Scripts/python" study/run_tool.py --tool-dir "<tool>" --study-dir study/data \
      [--source crossref,arxiv] [--venues auto | --venues "ACL,EMNLP"]

Venues are chosen once per question (the tool's own select_venues) and shared by both runs, so
the rewrite stays the only difference between the conditions.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

TOP_N = 10


def _paper(r) -> dict:
    rec = r.record
    return {"id": rec.DOI or rec.id, "title": rec.title, "abstract": rec.abstract or "",
            "year": rec.issued or "", "venue": rec.container_title or "", "doi": rec.DOI or ""}


def run_question(pipeline_mod, models_mod, pipe, question: str) -> dict:
    """Both conditions for one question. Returns the rewrite and both top-10 lists."""
    structured_on, _, ranked_on = pipe.run_retrieval(question, limit=50, pdf_limit=0)
    bypass = models_mod.StructuredQuery(refined_query=question, keywords=[], focus_query=None)
    _, _, ranked_off = pipe.run_retrieval(question, limit=50, pdf_limit=0, structured=bypass)
    rewrite = structured_on.refined_query
    if structured_on.focus_query:
        rewrite += f" | {structured_on.focus_query}"
    return {"question": question, "rewrite": rewrite,
            "on": [_paper(r) for r in ranked_on[:TOP_N]],
            "off": [_paper(r) for r in ranked_off[:TOP_N]]}


def make_pipeline(pipeline_mod, config_mod, venue_mod, source: str, venues, question: str):
    """A fresh pipeline per question (venue choice is per question), venues enabled if asked."""
    pipe = pipeline_mod.LiteratureReviewPipeline(source=source, enrich=True, semantic=True,
                                                 tier=False, scihub=False)
    chosen = []
    if venues:
        cfg = SimpleNamespace(venues="__ask__" if venues == "auto" else venues, query=question,
                              interactive=False, provider="ollama", host=config_mod.OLLAMA_HOST,
                              api_key=config_mod.OLLAMA_API_KEY, model=config_mod.DEFAULT_MODEL)
        venue_mod.select_venues(pipe, cfg)
        chosen = [v["name"] for v in (pipe._venue_cfg or {}).get("venues", [])]
    return pipe, chosen


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tool-dir", required=True)
    ap.add_argument("--study-dir", default="study/data")
    ap.add_argument("--source", default="crossref,arxiv")
    ap.add_argument("--venues", default=None,
                    help='"auto" = the tool suggests venues per question; or a list "ACL,EMNLP"')
    ap.add_argument("--pids", default=None,
                    help="only these participants, e.g. P01,P04 (lets parallel workers split work)")
    args = ap.parse_args()
    only = set(args.pids.split(",")) if args.pids else None

    sys.path.insert(0, str(Path(args.tool_dir).resolve()))
    import config as config_mod
    import models as models_mod
    import pipeline as pipeline_mod
    import venue_flow as venue_mod

    # No PDF downloads in a study run: the full-text stage is skipped when this is falsy.
    pipeline_mod.enrich_with_full_text = None
    study = Path(args.study_dir)
    (study / "runs").mkdir(parents=True, exist_ok=True)
    with open(study / "questions.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        out = study / "runs" / f"{row['pid']}.json"
        if out.exists() or (only and row["pid"] not in only):
            continue  # resumable: one finished file per participant
        t0 = time.perf_counter()
        pipe, venues = make_pipeline(pipeline_mod, config_mod, venue_mod, args.source,
                                     args.venues, row["question"])
        result = {"pid": row["pid"], "source": args.source, "venues": venues,
                  "model": config_mod.DEFAULT_MODEL,
                  **run_question(pipeline_mod, models_mod, pipe, row["question"])}
        result["seconds"] = round(time.perf_counter() - t0)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{row['pid']}: {len(result['on'])} on / {len(result['off'])} off; "
              f"venues: {', '.join(venues) or 'none'}")


if __name__ == "__main__":
    main()
