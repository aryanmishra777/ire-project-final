"""Fill the one-minute fidelity message (forms/fidelity_message.md) for every participant from
their run file, ready to paste into WhatsApp or email.

  python -m study.fidelity_messages [--study-dir study/data]

Output: <study>/fidelity_messages.md, one section per participant.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FORM = Path(__file__).resolve().parent / "forms" / "fidelity_message.md"


def template() -> str:
    """The message body: everything after the form's '---' separator."""
    return FORM.read_text(encoding="utf-8").split("---", 1)[1].strip()


def build(study: Path) -> Path:
    body = template()
    out = ["# Fidelity messages (one per participant)", "",
           "Send each participant only their own section. Record replies in "
           "`fidelity.csv` (columns `pid, question, rewrite, fidelity, dropped_term`).", ""]
    for path in sorted((study / "runs").glob("*.json")):
        run = json.loads(path.read_text(encoding="utf-8"))
        out += [f"## {run['pid']}", "",
                body.format(question=run["question"], rewrite=run["rewrite"]), ""]
    dest = study / "fidelity_messages.md"
    dest.write_text("\n".join(out), encoding="utf-8")
    return dest


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--study-dir", default="study/data")
    print(build(Path(ap.parse_args().study_dir)))
