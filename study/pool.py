"""Pool the two top-10 lists per participant into one blind, shuffled rating sheet.

Inputs  <study>/runs/<pid>.json          (from run_tool.py, or make_illustrative.py)
Outputs <study>/rating_sheets/<pid>.csv  what the participant sees: item, title, abstract, grade
        <study>/key.csv                  hidden: which condition ranked each item, and where
        <study>/fidelity_template.csv    Part B: question, rewrite, blank fidelity columns
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
from pathlib import Path


def paper_key(p: dict) -> str:
    """Same paper → same key. Normalised title first: one paper can carry different DOIs from
    different sources (journal vs arXiv), but a participant sees and rates it once."""
    title = re.sub(r"[^a-z0-9]", "", (p.get("title") or "").lower())
    return title or (p.get("doi") or "").lower().strip()


def pool_one(run: dict) -> tuple[list[dict], list[dict]]:
    """Return (sheet rows, key rows) for one participant."""
    merged: dict[str, dict] = {}
    for cond in ("on", "off"):
        for rank, p in enumerate(run[cond], start=1):
            k = paper_key(p)
            entry = merged.setdefault(k, {"paper": p, "rank_on": "", "rank_off": ""})
            if entry[f"rank_{cond}"] == "":  # a duplicate within one list keeps its best rank
                entry[f"rank_{cond}"] = rank
    entries = list(merged.values())
    # Seed from the pid so a sheet can be regenerated identically.
    seed = int(hashlib.sha1(run["pid"].encode()).hexdigest(), 16) % 2**32
    random.Random(seed).shuffle(entries)
    sheet, key = [], []
    for i, e in enumerate(entries, start=1):
        item = f"{run['pid']}-{i:02d}"
        p = e["paper"]
        sheet.append({"item": item, "title": p["title"], "abstract": p["abstract"],
                      "year": p.get("year", ""), "venue": p.get("venue", ""), "grade": ""})
        key.append({"pid": run["pid"], "item": item, "rank_on": e["rank_on"],
                    "rank_off": e["rank_off"]})
    return sheet, key


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def pool_study(study: Path) -> None:
    keys, fidelity = [], []
    for path in sorted((study / "runs").glob("*.json")):
        run = json.loads(path.read_text(encoding="utf-8"))
        sheet, key = pool_one(run)
        dest = study / "rating_sheets" / f"{run['pid']}.csv"
        if not dest.exists():  # never overwrite: a participant may have graded it in place
            _write(dest, sheet)
        keys += key
        fidelity.append({"pid": run["pid"], "question": run["question"],
                         "rewrite": run["rewrite"], "fidelity": "", "dropped_term": ""})
        print(f"{run['pid']}: {len(sheet)} papers to rate")
    _write(study / "key.csv", keys)
    _write(study / "fidelity_template.csv", fidelity)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--study-dir", default="study/data")
    pool_study(Path(ap.parse_args().study_dir))
