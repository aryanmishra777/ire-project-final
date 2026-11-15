"""Enforce the project's file rules (README, "Conventions") on every Python source file.

- at most 150 lines of code (non-blank lines outside docstrings; comments count)
- at most 170 lines including docstrings (non-blank)
- a companion .md next to each source file

Exit code 0 when everything passes, 1 otherwise.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".venv", "data", "results", "__pycache__", "build"}
MAX_CODE, MAX_TOTAL = 150, 170


def docstring_lines(tree: ast.AST) -> set[int]:
    """Line numbers covered by module, class and function docstrings."""
    lines: set[int] = set()
    nodes = [tree] + [n for n in ast.walk(tree)
                      if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    for node in nodes:
        body = getattr(node, "body", [])
        if body and isinstance(body[0], ast.Expr) and isinstance(
                getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
            lines.update(range(body[0].lineno, body[0].end_lineno + 1))
    return lines


def measure(path: Path) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8")
    doc = docstring_lines(ast.parse(text))
    nonblank = [i for i, ln in enumerate(text.splitlines(), start=1) if ln.strip()]
    code = [i for i in nonblank if i not in doc]
    return len(code), len(nonblank)


def main() -> int:
    failures = []
    for path in sorted(ROOT.rglob("*.py")):
        if SKIP_DIRS & set(path.relative_to(ROOT).parts):
            continue
        code, total = measure(path)
        rel = path.relative_to(ROOT).as_posix()
        problems = []
        if code > MAX_CODE:
            problems.append(f"{code} code lines > {MAX_CODE}")
        if total > MAX_TOTAL:
            problems.append(f"{total} lines with docstrings > {MAX_TOTAL}")
        if path.name != "__init__.py" and not path.with_suffix(".md").exists():
            problems.append("missing companion .md")
        status = "FAIL" if problems else "ok"
        print(f"{status:4}  {code:4} / {total:4}  {rel}  {'; '.join(problems)}")
        failures += problems
    print(f"\n{'FAILED' if failures else 'PASSED'}: {len(failures)} problem(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
