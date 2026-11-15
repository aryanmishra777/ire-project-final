# build_report.py

## What it does
Builds the two-page final report PDF (`../Final Report - Aryan Mishra.pdf`) from the result files
and prints it with headless Microsoft Edge.

## Responsibility
Owns reading the numbers, formatting tables and filling the template. It doesn't hold any prose of
its own: the wording lives in `report/template.html` and the look in `report/style.css` (reused from
the mid-submission report so the two reports match). It doesn't run any experiment.

## How
1. Reads `results/comparisons.csv`, `interaction.csv`, `cost.csv`, `reproduction.csv`,
   `main_table.csv`, `failure_terms.csv` and `study/data/results/study_summary.md` plus
   `study_per_question.csv`.
2. Builds the HTML table rows and the sentence-level numbers (`[[placeholders]]` in the template).
   Significance is bolded from the BH-corrected p-values, never typed.
3. Embeds the three PNG figures as base64 and inlines the CSS, so `report/report.html` is one file.
4. Fails if any `[[placeholder]]` is left unfilled, then runs Edge with `--print-to-pdf`.
5. The repository and video links are visible placeholders in the template until real ones exist.

## Why
- **Every number comes from a result file.** The project rule is that no result is typed by hand, and
  a report built from the CSVs stays correct when the analysis is re-run.
- **HTML to PDF through Edge.** It matches the mid-submission report's fonts and layout, and needs no
  extra dependency (Edge ships with Windows). LaTeX or reportlab would look different.
- **Two A4 pages with fixed-size sections.** The reference report is two pages; overflow is hidden by
  the page CSS, so the PDF is checked by eye after any text change.
