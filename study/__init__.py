"""Human-study kit: forms, tool runner, pooling, analysis, illustrative data."""
import sys

if hasattr(sys.stdout, "reconfigure"):  # Windows consoles default to cp1252; results use Δ, ρ
    sys.stdout.reconfigure(encoding="utf-8")
