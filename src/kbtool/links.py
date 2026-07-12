"""Link parsing and the source-path -> URL mapping (D12, spec 5.2).

Shared by the validator (targets exist) and the preprocessor (rewrite to what
the SSG consumes). Keeping one implementation prevents the two from drifting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Markdown inline links [text](target) and images ![alt](target). We match the
# target only; reference-style links are not used by our conventions.
_LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")

_KB_RE = re.compile(r"^kb://([a-z0-9][a-z0-9-]{0,30})/(.+)$")


@dataclass(frozen=True)
class Link:
    target: str
    line: int  # 1-based


def find_links(text: str) -> list[Link]:
    out: list[Link] = []
    for m in _LINK_RE.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        out.append(Link(target=m.group(1), line=line))
    return out


def is_external(target: str) -> bool:
    return bool(re.match(r"^[a-z][a-z0-9+.-]*://", target)) and not target.startswith("kb://")


def is_anchor_only(target: str) -> bool:
    return target.startswith("#")


def split_fragment(target: str) -> tuple[str, str]:
    """Return (path, '#frag' or '')."""
    if "#" in target:
        path, frag = target.split("#", 1)
        return path, "#" + frag
    return target, ""


def parse_kb_link(target: str) -> tuple[str, str] | None:
    """kb://<kb>/<path> -> (kb_name, path) or None if not a kb:// link."""
    m = _KB_RE.match(target)
    if not m:
        return None
    return m.group(1), m.group(2)


def source_path_to_url_path(src_path: str) -> str:
    """Map a docs-relative source path to its rendered URL path (directory URLs).

    `concepts/alpha.md`       -> `/concepts/alpha/`
    `concepts/index.md`       -> `/concepts/`
    `index.md`                -> `/`
    `assets/x/diagram.png`    -> `/assets/x/diagram.png`  (non-.md keep as-is)
    Accepts a leading slash; always returns a leading slash.
    """
    p = src_path.lstrip("/")
    if not p.endswith(".md"):
        return "/" + p
    stem = p[: -len(".md")]
    if stem == "index":
        return "/"
    if stem.endswith("/index"):
        return "/" + stem[: -len("index")]  # keep trailing slash
    return "/" + stem + "/"


def cross_kb_url(kb_name: str, path: str, domain_suffix: str) -> str:
    """kb://<kb>/<path>.md -> https://kb-<kb>.<suffix><url-path>."""
    url_path = source_path_to_url_path(path)
    return f"https://kb-{kb_name}.{domain_suffix}{url_path}"
