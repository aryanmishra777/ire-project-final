# stats.py

## What it does
Paired significance testing for per-query metric differences: bootstrap confidence intervals,
a randomisation test, Benjamini–Hochberg correction, and the minimum detectable effect.

## Responsibility
Owns every statistical decision. Callers pass two aligned per-query arrays and get back one
dictionary. No other module computes a p-value.

## How
- `paired_bootstrap_ci()` resamples query indices 10,000 times (seeded) and takes the 2.5th and
  97.5th percentiles of the resampled mean difference.
- `randomization_p()` is a two-sided sign-flip test. Under the null, each query's difference is
  equally likely to be positive or negative. The p-value is (count of null means at least as
  extreme + 1) / (10,000 + 1).
- `benjamini_hochberg()` returns adjusted p-values (step-up procedure, kept monotone, capped at 1).
- `mde()` is (z for 0.975 + z for 0.8) × sd(diff) / sqrt(n): the smallest true effect detectable
  with 80% power at α = 0.05.
- `compare(a, b)` bundles these for b − a, with the win, loss and tie counts.

## Why
- **Paired, per query.** A query that's hard for one system is usually hard for all of them.
  Pairing removes that difficulty from the noise, which is why IR evaluation uses paired designs.
- **Randomisation over a t-test.** Smucker, Allan & Carterette (CIKM 2007) found it the most
  reliable test for IR metrics, which are bounded and skewed.
- **BH within each metric's family.** The grid makes eight rewrite-vs-raw comparisons per metric,
  and BH controls the false discovery rate without being as harsh as Bonferroni.
- **MDE reported with every comparison.** A non-significant result then reads as "no effect
  larger than X", which is a real finding, not just "nothing".
