# fidelity_messages.py

## What it does
Writes one ready-to-send message per participant, asking only the fidelity question (Part B). It
fills `forms/fidelity_message.md` with that person's question and the tool's rewrite of it.

## Responsibility
Owns turning run files into participant messages. It doesn't record replies: those go into
`fidelity.csv`, which `analyze_study.py` reads.

## How
1. Reads the message template: the text after the `---` line in `forms/fidelity_message.md`.
2. For each `runs/<pid>.json`, fills `{question}` and `{rewrite}`. The rewrite is the tool's
   broad search phrase, plus its focused phrase when it made one.
3. Writes `<study>/fidelity_messages.md`, one section per participant.

## Why
- **Only Part B goes to participants.** They had no time for the 15-minute rating task. Fidelity
  ("does the rewrite still mean what you asked?") is the one judgment only the question's author
  can make. Relevance can be judged blind by the researcher instead, and the report says so.
- **Generated, not hand-written.** Each person sees exactly the rewrite the tool used. A
  hand-copied rewrite could pick up a typo, which would change what they're judging.
- **The template lives in `forms/`.** The wording can be edited as text without touching code.
