"""nav.yml parsing, glob expansion, and coverage (spec 6.2 step 4).

The KB writes a curated/hybrid nav; the preprocessor expands globs into an
explicit tree so the SSG's `omitted_files` check can stay fatal. Coverage
(every content page appears in the nav) is asserted by `kbtool check` too,
so the failure is caught before the build.
"""

from __future__ import annotations

import re
from pathlib import Path

from .kb import Frontmatter, parse_frontmatter


def glob_to_regex(pattern: str) -> re.Pattern:
    """Translate our nav glob DSL to a regex over docs-relative posix paths.

    `**` matches any characters including `/`; `*` matches within a segment.
    """
    out = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*" and i + 1 < len(pattern) and pattern[i + 1] == "*":
            out.append(".*")
            i += 2
        elif c == "*":
            out.append("[^/]*")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def _page_title(docs_dir: Path, rel: str) -> str:
    """Frontmatter title, else first H1, else the filename stem."""
    text = (docs_dir / rel).read_text(encoding="utf-8")
    fm: Frontmatter = parse_frontmatter(text)
    if fm.present and isinstance(fm.data.get("title"), str):
        return fm.data["title"]
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return Path(rel).stem


def _all_rel_md(docs_dir: Path) -> list[str]:
    return sorted(p.relative_to(docs_dir).as_posix() for p in docs_dir.rglob("*.md"))


def covered_paths(nav: list, docs_dir: Path) -> set[str]:
    """Docs-relative posix paths the nav references (explicit + glob matches)."""
    covered: set[str] = set()
    all_md = _all_rel_md(docs_dir)

    def walk(items: list) -> None:
        for item in items:
            if not isinstance(item, dict) or len(item) != 1:
                raise ValueError(f"nav entry must be a single-key mapping: {item!r}")
            (value,) = item.values()
            if isinstance(value, str):
                covered.add(value.lstrip("/"))
            elif isinstance(value, list):
                walk(value)
            elif isinstance(value, dict) and "glob" in value:
                rx = glob_to_regex(value["glob"].lstrip("/"))
                covered.update(p for p in all_md if rx.match(p))
            else:
                raise ValueError(f"unsupported nav value: {value!r}")

    walk(nav)
    return covered


def expand(nav: list, docs_dir: Path) -> list:
    """Return an explicit mkdocs nav: globs -> title-sorted lists of files."""

    def walk(items: list) -> list:
        result = []
        for item in items:
            (key,), (value,) = (item.keys(), item.values())
            if isinstance(value, str):
                result.append({key: value.lstrip("/")})
            elif isinstance(value, list):
                result.append({key: walk(value)})
            elif isinstance(value, dict) and "glob" in value:
                rx = glob_to_regex(value["glob"].lstrip("/"))
                matches = [p for p in _all_rel_md(docs_dir) if rx.match(p)]
                matches.sort(key=lambda rel: _page_title(docs_dir, rel).lower())
                result.append({key: [{_page_title(docs_dir, m): m} for m in matches]})
            else:
                raise ValueError(f"unsupported nav value: {value!r}")
        return result

    return walk(nav)
