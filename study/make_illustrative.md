# make_illustrative.py

## What it does
Creates **illustrative, simulated** study data for 15 participants in `study/illustrative/`, then
runs the real pipeline on it (pooling, then analysis). That shows every step of the human study
working end to end while real data collection is pending.

## Responsibility
Owns the simulated data and its labelling. It must never produce anything that could pass for
real responses:
- an `ILLUSTRATIVE.txt` marker in the folder;
- a note inside every run file;
- placeholder paper titles ("Simulated paper 07 (P03)");
- the rewrite text "(simulated rewrite)";
- a red stamp on the figure (added by `analyze_study.py` because of the marker).

## How
1. **Questions**: 15 example questions written for the demo, spread across fields typical of
   IIIT-H research. They're plausible inputs, not anyone's real question.
2. **Runs**: for each participant, 24 placeholder papers get a hidden true grade (2/1/0 with
   weights 25/30/45). The "off" run ranks them by grade plus noise. The "on" run weights the grade
   by `1 + 0.3 × (fidelity − 3)`, so a rewrite that loses the meaning ranks worse.
3. **Pooling**: the real `pool.py` makes the blind sheets.
4. **Ratings**: each sheet is filled with the true grade. A 10% chance of a ±1 slip mimics
   rater noise.
5. **Fidelity**: preset 1–5 values. A dropped term is marked for ratings ≤ 2.
6. **Analysis**: the real `analyze_study.py`.

## Why
- **Run the real pipeline on fake inputs, rather than drawing fake charts.** The only simulated
  part is the input. Every downstream step is the code that will process the real pilot, so the
  demo also tests that code.
- **A fixed seed.** The illustrative numbers are identical every run, so the slides and the
  regenerated files never disagree.
- **A built-in fidelity–quality link.** It makes the right-hand panel of the figure show what the
  analysis is designed to detect. Because the effect was built into the simulation, it says
  nothing about the real world, which is why everything is stamped.
