"""kbtool check — the deploy-gate validator suite (spec 6.1).

Each validator appends Findings; `run_all` aggregates and the CLI exits non-zero
if any error-severity Finding exists. Warnings are printed but don't fail.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import deque
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

import jsonschema

from . import kb as kbmod
from . import links as linkmod
from . import nav as navmod
from .kb import KbError, load_yaml, parse_frontmatter

STATUS_ENUM = {"draft", "review", "published", "archived"}


@dataclass
class Finding:
    level: str  # "error" | "warning"
    message: str
    file: str = ""
    line: int = 0

    def format(self) -> str:
        loc = self.file + (f":{self.line}" if self.line else "") if self.file else ""
        prefix = "ERROR" if self.level == "error" else "warn"
        return f"[{prefix}] {loc + ': ' if loc else ''}{self.message}"


def _schema() -> dict:
    return json.loads(
        resources.files("kbtool.data").joinpath("frontmatter.schema.json").read_text()
    )


def _domain_suffix(kb_yml: dict) -> str:
    url = str(kb_yml.get("url", ""))
    m = re.match(r"^https://kb-[a-z0-9-]+\.(.+?)/?$", url)
    return m.group(1) if m else "example.com"


# --- individual validators -------------------------------------------------


def check_frontmatter(root: Path, vocab: dict) -> list[Finding]:
    out: list[Finding] = []
    schema = _schema()
    types = set(vocab.get("types") or [])
    tags = set(vocab.get("tags") or [])
    for md in kbmod.content_markdown_files(root):
        rel = md.relative_to(root).as_posix()
        text = md.read_text(encoding="utf-8")
        try:
            fm = parse_frontmatter(text)
        except KbError as e:
            out.append(Finding("error", str(e), rel))
            continue
        if kbmod.is_reserved(md):
            if fm.present:
                out.append(Finding("error", "reserved file must have no frontmatter", rel))
            continue
        if not fm.present:
            out.append(Finding("error", "missing frontmatter (type, title, description required)", rel))
            continue
        try:
            jsonschema.validate(fm.data, schema)
        except jsonschema.ValidationError as e:
            out.append(Finding("error", f"frontmatter schema: {e.message}", rel))
            continue
        if fm.data["type"] not in types:
            out.append(Finding("error", f"type '{fm.data['type']}' not in vocab.yml types", rel))
        for tag in fm.data.get("tags", []) or []:
            if tag not in tags:
                out.append(Finding("error", f"tag '{tag}' not in vocab.yml tags", rel))
    return out


def _is_public(rel_docs_path: str) -> bool:
    return rel_docs_path.startswith("public/")


def check_links(root: Path, kb_yml: dict) -> list[Finding]:
    out: list[Finding] = []
    docs = root / "docs"
    suffix = _domain_suffix(kb_yml)
    for md in kbmod.content_markdown_files(root):
        rel = md.relative_to(docs).as_posix()
        text = md.read_text(encoding="utf-8")
        for link in linkmod.find_links(text):
            target = link.target
            if linkmod.is_anchor_only(target) or linkmod.is_external(target):
                continue
            kb_link = linkmod.parse_kb_link(target)
            if kb_link is not None:
                # cross-KB: syntax already validated by the regex; not resolvable here
                continue
            if target.startswith("kb:"):
                out.append(Finding("error", f"malformed kb:// link: {target}", rel, link.line))
                continue
            path, _frag = linkmod.split_fragment(target)
            if not path:
                continue  # pure anchor after split
            if path.startswith("/"):
                tgt = docs / path.lstrip("/")
            else:
                tgt = (md.parent / path)
            try:
                tgt_rel = tgt.resolve().relative_to(docs.resolve()).as_posix()
            except ValueError:
                out.append(Finding("error", f"link escapes docs/: {target}", rel, link.line))
                continue
            if not tgt.exists():
                out.append(Finding("error", f"link target not found: {target}", rel, link.line))
                continue
            if _is_public(rel) and tgt_rel.endswith(".md") and not _is_public(tgt_rel):
                out.append(Finding(
                    "warning",
                    f"public page links to private page (broken for anonymous readers): {target}",
                    rel, link.line,
                ))
    return out


def check_index_reachability(root: Path) -> list[Finding]:
    """Every content .md must be reachable from docs/index.md via intra-KB links."""
    docs = root / "docs"
    index = docs / "index.md"
    if not index.is_file():
        return [Finding("error", "docs/index.md is missing", "docs/index.md")]
    all_md = {p.relative_to(docs).as_posix() for p in docs.rglob("*.md")}
    seen: set[str] = {"index.md"}
    queue: deque[str] = deque(["index.md"])
    while queue:
        cur = queue.popleft()
        cur_path = docs / cur
        text = cur_path.read_text(encoding="utf-8")
        for link in linkmod.find_links(text):
            target = link.target
            if linkmod.is_anchor_only(target) or linkmod.is_external(target):
                continue
            if linkmod.parse_kb_link(target) is not None or target.startswith("kb:"):
                continue
            path, _ = linkmod.split_fragment(target)
            if not path or not path.endswith(".md"):
                continue
            tgt = (docs / path.lstrip("/")) if path.startswith("/") else (cur_path.parent / path)
            try:
                rel = tgt.resolve().relative_to(docs.resolve()).as_posix()
            except ValueError:
                continue
            if rel in all_md and rel not in seen:
                seen.add(rel)
                queue.append(rel)
    orphans = sorted(all_md - seen)
    return [
        Finding("error", "orphan: not reachable from docs/index.md", o)
        for o in orphans
    ]


def check_log_append_only(root: Path) -> list[Finding]:
    log_rel = "docs/log.md"
    if not (root / log_rel).is_file():
        return []
    head = kbmod.git(root, "show", f"HEAD:{log_rel}")
    if head.returncode != 0:
        # no committed version yet (new file / no HEAD) — passes trivially
        return []
    current = (root / log_rel).read_text(encoding="utf-8")
    if current.rstrip() == head.stdout.rstrip():
        return []
    if current.rstrip().startswith(head.stdout.rstrip()):
        return []
    return [Finding(
        "error",
        "log.md is not append-only vs HEAD (mid-file edit?) — union merge is only safe for appends",
        log_rel,
    )]


def check_nav(root: Path) -> list[Finding]:
    out: list[Finding] = []
    docs = root / "docs"
    if not (root / "nav.yml").is_file():
        return [Finding("error", "nav.yml is missing", "nav.yml")]
    try:
        nav = load_yaml(root / "nav.yml").get("nav")
    except KbError as e:
        return [Finding("error", str(e), "nav.yml")]
    if not isinstance(nav, list):
        return [Finding("error", "nav.yml must have a top-level 'nav:' list", "nav.yml")]
    try:
        covered = navmod.covered_paths(nav, docs)
    except ValueError as e:
        return [Finding("error", str(e), "nav.yml")]
    all_md = {p.relative_to(docs).as_posix() for p in docs.rglob("*.md")}
    for missing in sorted(covered - all_md):
        out.append(Finding("error", f"nav references non-existent page: {missing}", "nav.yml"))
    for omitted in sorted(all_md - covered):
        out.append(Finding("error", f"page not in nav (add it or a covering glob): {omitted}", "nav.yml"))
    return out


def check_slug_triple(root: Path, kb_yml: dict) -> list[Finding]:
    out: list[Finding] = []
    name = kb_yml.get("name")
    url = kb_yml.get("url", "")
    if not name:
        return [Finding("error", "kb.yml missing 'name'", "kb.yml")]
    expected_url = f"https://kb-{name}."
    if not str(url).startswith(expected_url):
        out.append(Finding("error", f"kb.yml url must start with {expected_url}", "kb.yml"))
    wrangler = root / "wrangler.jsonc"
    if wrangler.is_file():
        txt = wrangler.read_text(encoding="utf-8")
        if f'"kb-{name}"' not in txt:
            out.append(Finding("error", f"wrangler.jsonc worker name must be kb-{name}", "wrangler.jsonc"))
        if f"kb-{name}." not in txt:
            out.append(Finding("error", f"wrangler.jsonc route must be kb-{name}.<domain>", "wrangler.jsonc"))
    return out


def check_boundary(root: Path) -> list[Finding]:
    out: list[Finding] = []
    manifest = root / "blueprint-checksums.json"
    if not manifest.is_file():
        return [Finding("error", "blueprint-checksums.json is missing", "blueprint-checksums.json")]
    data = json.loads(manifest.read_text(encoding="utf-8"))
    version = data.get("blueprint_version", "")
    for rel, expected in (data.get("checksums") or {}).items():
        f = root / rel
        if not f.is_file():
            out.append(Finding("error", f"blueprint-owned file missing: {rel}", rel))
            continue
        actual = hashlib.sha256(f.read_bytes()).hexdigest()
        if actual != expected:
            out.append(Finding("error", f"blueprint-owned file modified (checksum mismatch): {rel}", rel))
    for rel in data.get("marked_files") or []:
        f = root / rel
        if not f.is_file():
            out.append(Finding("error", f"blueprint-owned file missing: {rel}", rel))
            continue
        first = f.read_text(encoding="utf-8").splitlines()[:1]
        head = first[0] if first else ""
        if "MANAGED BY BLUEPRINT" not in head:
            out.append(Finding("error", f"missing managed marker on first line: {rel}", rel))
        elif version and version not in head:
            out.append(Finding("warning", f"managed marker version differs from manifest ({version}): {rel}", rel))
    return out


def check_markdown_lint(root: Path) -> list[Finding]:
    import shutil
    import subprocess

    if shutil.which("pymarkdown") is None:
        return [Finding("warning", "pymarkdown not on PATH — markdown lint skipped")]
    with resources.as_file(resources.files("kbtool.data").joinpath("pymarkdown.json")) as cfg:
        proc = subprocess.run(
            ["pymarkdown", "--config", str(cfg), "scan", str(root / "docs")],
            capture_output=True, text=True,
        )
    if proc.returncode == 0:
        return []
    out = []
    for line in (proc.stdout or "").splitlines():
        if line.strip():
            out.append(Finding("error", f"markdownlint: {line.strip()}"))
    if not out:
        out.append(Finding("error", f"markdownlint failed: {(proc.stderr or '').strip()[:200]}"))
    return out


# --- aggregate -------------------------------------------------------------


def check_secrets(root: Path, kb_yml: dict) -> list[Finding]:
    from . import secrets as secretsmod

    is_public = str(kb_yml.get("visibility", "private")) == "public"
    return [
        Finding(level, msg, rel, line)
        for (level, msg, rel, line) in secretsmod.scan(root, is_public)
    ]


def run_all(root: Path) -> list[Finding]:
    kb_yml = load_yaml(root / "kb.yml")
    vocab = load_yaml(root / "vocab.yml") if (root / "vocab.yml").is_file() else {}
    findings: list[Finding] = []
    findings += check_frontmatter(root, vocab)
    findings += check_links(root, kb_yml)
    findings += check_index_reachability(root)
    findings += check_log_append_only(root)
    findings += check_nav(root)
    findings += check_slug_triple(root, kb_yml)
    findings += check_boundary(root)
    findings += check_secrets(root, kb_yml)
    findings += check_markdown_lint(root)
    return findings
