"""KB repo discovery and shared file-format helpers."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml


class KbError(Exception):
    """A user-facing error (bad KB state), not a bug."""


def find_kb_root(start: Path | None = None) -> Path:
    """Walk up from `start` (or cwd) to the directory holding kb.yml."""
    cur = (start or Path.cwd()).resolve()
    for candidate in (cur, *cur.parents):
        if (candidate / "kb.yml").is_file():
            return candidate
    raise KbError("not inside a KB repo (no kb.yml found in this or any parent directory)")


@dataclass(frozen=True)
class Frontmatter:
    """Parsed leading YAML block of a Markdown file."""

    data: dict
    present: bool
    body_offset: int  # line index where the body starts (0-based)


def parse_frontmatter(text: str) -> Frontmatter:
    """Parse a leading `---\\n...\\n---` YAML block. Absent block → present=False.

    Kept dependency-free (no python-frontmatter) to stay lean.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return Frontmatter(data={}, present=False, body_offset=0)
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            block = "\n".join(lines[1:i])
            loaded = yaml.safe_load(block) if block.strip() else {}
            if not isinstance(loaded, dict):
                raise KbError("frontmatter is not a YAML mapping")
            return Frontmatter(data=loaded, present=True, body_offset=i + 1)
    raise KbError("frontmatter opening '---' has no closing '---'")


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        loaded = yaml.safe_load(fh)
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise KbError(f"{path.name} is not a YAML mapping")
    return loaded


def content_markdown_files(kb_root: Path) -> list[Path]:
    """All Markdown files under docs/, sorted for deterministic output."""
    return sorted((kb_root / "docs").rglob("*.md"))


def is_reserved(path: Path) -> bool:
    """OKF-reserved, frontmatter-free filenames: index.md and log.md (any dir)."""
    return path.name in ("index.md", "log.md")


def git(kb_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=kb_root,
        capture_output=True,
        text=True,
    )
