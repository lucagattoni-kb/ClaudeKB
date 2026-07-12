"""build / serve / ci (spec 6.1, 6.2)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from .preprocess import preprocess


def _zensical(*args: str) -> int:
    exe = shutil.which("zensical")
    if exe is None:
        print("ERROR: zensical not found on PATH (is the KB env synced? `uv sync`)", file=sys.stderr)
        return 127
    return subprocess.run([exe, *args]).returncode


def build(root: Path) -> int:
    from .cli import run_check  # local import to avoid cycle

    rc = run_check(root)
    if rc != 0:
        return rc
    mkdocs_yml = preprocess(root)
    rc = _zensical("build", "-f", str(mkdocs_yml), "-s")
    if rc != 0:
        return rc
    # post-build assertions
    site = root / ".build" / "site"
    problems = []
    if not any(site.glob("search*.json")) and not (site / "search").exists():
        problems.append("search index not found in build output")
    src_redirects = root / "docs" / "_redirects"
    if src_redirects.is_file() and not (site / "_redirects").is_file():
        problems.append("_redirects present in source but missing from build output")
    for p in problems:
        print(f"ERROR: {p}", file=sys.stderr)
    return 1 if problems else 0


def serve(root: Path) -> int:
    mkdocs_yml = preprocess(root)
    return _zensical("serve", "-f", str(mkdocs_yml))
