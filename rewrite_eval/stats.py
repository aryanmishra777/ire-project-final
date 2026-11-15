"""Paired significance testing for per-query metric differences.

Every comparison is paired by query: the same query is hard or easy for every system, so
pairing removes query difficulty as a source of variance.
- paired bootstrap over queries → 95% CI on the mean difference
- paired randomisation (sign-flip) test → p-value (Smucker et al., CIKM 2007)
- Benjamini–Hochberg across the family of comparisons
- minimum detectable effect for a paired design at the observed spread
"""
from __future__ import annotations

import numpy as np

from .config import ALPHA, N_BOOT, N_PERM, STATS_SEED

_Z = {0.05: 1.959964, 0.8: 0.841621}  # z_(1-α/2) for α=.05, z_power for 80% power


def paired_bootstrap_ci(diff: np.ndarray, n_boot: int = N_BOOT, alpha: float = ALPHA,
                        seed: int = STATS_SEED) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(diff), size=(n_boot, len(diff)))
    means = diff[idx].mean(axis=1)
    return float(np.quantile(means, alpha / 2)), float(np.quantile(means, 1 - alpha / 2))


def randomization_p(diff: np.ndarray, n_perm: int = N_PERM, seed: int = STATS_SEED) -> float:
    """Two-sided sign-flip test of H0: mean paired difference = 0."""
    rng = np.random.default_rng(seed + 1)
    observed = abs(diff.mean())
    signs = rng.choice([-1.0, 1.0], size=(n_perm, len(diff)))
    null = np.abs((signs * diff).mean(axis=1))
    return float((np.sum(null >= observed - 1e-12) + 1) / (n_perm + 1))


def benjamini_hochberg(pvals: list[float]) -> list[float]:
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    adj = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(adj, 1.0)
    return out.tolist()


def mde(diff: np.ndarray) -> float:
    """Smallest true mean difference detectable with 80% power at α=.05 (paired, normal approx)."""
    return float((_Z[0.05] + _Z[0.8]) * diff.std(ddof=1) / np.sqrt(len(diff)))


def compare(a: np.ndarray, b: np.ndarray) -> dict:
    """Stats for b − a (positive = b better)."""
    diff = np.asarray(b, float) - np.asarray(a, float)
    lo, hi = paired_bootstrap_ci(diff)
    return {"mean_a": float(np.mean(a)), "mean_b": float(np.mean(b)),
            "delta": float(diff.mean()), "ci_lo": lo, "ci_hi": hi,
            "p": randomization_p(diff), "mde": mde(diff), "n": int(len(diff)),
            "wins": int((diff > 0).sum()), "losses": int((diff < 0).sum()),
            "ties": int((diff == 0).sum())}
