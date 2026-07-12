"""Preprocess step (spec 6.2): make content SSG-independent, then emit config.

Content on disk stays logical (root-absolute + kb:// links, no injected dates).
The preprocessor copies docs/ into .build/, rewrites links to final URL paths,
injects git-derived date footers, expands the nav, and writes .build/mkdocs.yml.
Any SSG can then consume .build/ (D12/D14).
"""

from __future__ import annotations

import re
import shutil
from importlib import resources
from pathlib import Path

import yaml

from . import kb as kbmod
from . import links as linkmod
from . import nav as navmod
from .kb import load_yaml

FOOTER_SEP = "\n\n---\n\n"


def _rewrite_target(target: str, kb_name: str, suffix: str) -> str:
    if linkmod.is_anchor_only(target) or linkmod.is_external(target):
        return target
    kb_link = linkmod.parse_kb_link(target)
    if kb_link is not None:
        name, path = kb_link
        path_part, frag = linkmod.split_fragment(path)
        return linkmod.cross_kb_url(name, path_part, suffix) + frag
    path, frag = linkmod.split_fragment(target)
    if path.startswith("/") and path.endswith(".md"):
        return linkmod.source_path_to_url_path(path) + frag
    return target


def _rewrite_links(text: str, kb_name: str, suffix: str) -> str:
    def repl(m: re.Match) -> str:
        whole = m.group(0)
        target = m.group(1)
        new = _rewrite_target(target, kb_name, suffix)
        if new == target:
            return whole
        return whole.replace(target, new, 1)

    return linkmod._LINK_RE.sub(repl, text)


def _git_date(root: Path, rel_from_root: str) -> str | None:
    proc = kbmod.git(root, "log", "-1", "--format=%as", "--", rel_from_root)
    date = proc.stdout.strip()
    return date or None


def _is_shallow(root: Path) -> bool:
    proc = kbmod.git(root, "rev-parse", "--is-shallow-repository")
    return proc.stdout.strip() == "true"


def _domain_suffix(kb_yml: dict) -> str:
    url = str(kb_yml.get("url", ""))
    m = re.match(r"^https://kb-[a-z0-9-]+\.(.+?)/?$", url)
    return m.group(1) if m else "example.com"


def preprocess(root: Path) -> Path:
    """Produce .build/ (docs copy + mkdocs.yml). Returns the mkdocs.yml path."""
    kb_yml = load_yaml(root / "kb.yml")
    kb_name = kb_yml["name"]
    suffix = _domain_suffix(kb_yml)
    build = root / ".build"
    if build.exists():
        shutil.rmtree(build)
    docs_src = root / "docs"
    docs_dst = build / "docs"
    shutil.copytree(docs_src, docs_dst)

    # date footer: resolve shallow clones so dates aren't silently wrong
    dates_ok = True
    if _is_shallow(root):
        unshallow = kbmod.git(root, "fetch", "--unshallow")
        if unshallow.returncode != 0:
            dates_ok = False  # can't get true history — omit footers this build

    for md in docs_dst.rglob("*.md"):
        rel = md.relative_to(docs_dst).as_posix()
        text = md.read_text(encoding="utf-8")
        text = _rewrite_links(text, kb_name, suffix)
        if dates_ok:
            date = _git_date(root, f"docs/{rel}")
            if date:
                text = text.rstrip("\n") + FOOTER_SEP + f"*Last updated: {date} · from git history*\n"
        md.write_text(text, encoding="utf-8")

    # nav expansion + config generation
    nav = load_yaml(root / "nav.yml").get("nav")
    expanded = navmod.expand(nav, docs_dst)

    # site-base.yml carries a !!python/name: tag (mermaid superfences) that YAML
    # safe-load/dump cannot round-trip, so we keep it verbatim as text and append
    # the generated top-level keys as a separate safe-dumped block.
    base_text = resources.files("kbtool.data").joinpath("site-base.yml").read_text()
    generated = {
        "site_name": kb_yml.get("title", kb_name),
        "site_url": kb_yml.get("url", ""),
        "docs_dir": "docs",
        "site_dir": "site",
        "nav": expanded,
    }
    mkdocs_yml = build / "mkdocs.yml"
    mkdocs_yml.write_text(
        base_text.rstrip("\n") + "\n" + yaml.safe_dump(generated, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    _copy_redirects(root, build)
    return mkdocs_yml


def _copy_redirects(root: Path, build: Path) -> None:
    src = root / "docs" / "_redirects"
    if src.is_file():
        shutil.copy2(src, build / "docs" / "_redirects")
